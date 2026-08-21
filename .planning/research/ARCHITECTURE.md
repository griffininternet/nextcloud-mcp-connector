# Architecture Research

**Domain:** Erweiterung einer ausgelieferten MCP-only-ExApp um drei optionale App-Familien (Talk, Tables, Mail)
**Researched:** 2026-08-21
**Confidence:** HIGH für Talk und Tables (offizielle Talk-API-Doku, openapi.json der Tables-App, Quellcode gelesen), HIGH für die Codebasis-Integrationspunkte (gelesen, Budget live gemessen), MEDIUM für Mail (Routen und Controller-Attribute im Quellcode gelesen, aber kein öffentlicher API-Vertrag und Erreichbarkeit unter AppAPI-Impersonation nicht live belegt)

**Kernaussage in drei Sätzen.** Talk und Tables passen ohne neue Mechanik in die bestehende Architektur: sie sind Deck mit anderen Endpunkten, brauchen je ein Client-Modul, ein Tool-Modul, eine `reg_*`-Datei und zwei Zeilen in `capabilities.py`. Mail ist die einzige Familie, die echte Architekturentscheidungen erzwingt, weil sie keine Capabilities veröffentlicht und ihr Listing über eine interne, nicht als API zugesagte Route läuft. `prepare_context` wächst am billigsten gar nicht als neues Bein, sondern als zwei neue Einträge in `provider_map.PROVIDER_KINDS` plus zwei neue Buckets, weil der Fan-out die Suche schon heute ohne Provider-Einschränkung fragt und Talk- und Mail-Treffer damit bereits ankommen (heute als `url`, `resolvable: false`).

---

## Standard Architecture

### System Overview

Der Rahmen bleibt unverändert. Neu ist ausschliesslich, was mit `[NEU]` markiert ist.

```
                MCP-Clients (Claude, ChatGPT, Claude Code, MUCGPT, Agenten)
                                      |
                       Streamable HTTP + OAuth 2.1 / stdio
                                      |
+----------------------------------- v -----------------------------------------+
|  ExApp-Container                                                              |
|                                                                               |
|  exapp/middleware.py  ->  deps.resolve_clients(ctx)  ->  NcClients            |
|  (Auth-Grenze, unverändert)     (Credential-Naht, unverändert)                |
|                                      |                                        |
|  +---------------------------------- v -------------------------------------+ |
|  |  server/__init__.py: mcp, READ_ONLY, CREATE_ONLY, compact, graceful      | |
|  |  _load_registrations() importiert automatisch jedes reg_*.py             | |
|  +--+-----+-----+-----+-----+-----+-----+-----+------+------+------+--------+ |
|     |     |     |     |     |     |     |     |      |      |      |          |
|  reg_  reg_  reg_  reg_  reg_  reg_  reg_  reg_  reg_   reg_   reg_           |
|  files cal.  notes deck  cont. srch  ctx   chatgpt talk[NEU] tables[NEU] mail[NEU]
|     |     |     |     |     |     |     |     |      |      |      |          |
|  +--v-----v-----v-----v-----v-----v-----v-----v------v------v------v--------+ |
|  |  tools/  (freistehende, testbare Funktionen, kein SDK-Objekt im Body)    | |
|  |  files calendar notes deck contacts search context chatgpt marks         | |
|  |  + talk.py [NEU]  + tables.py [NEU]  + mail.py [NEU]                     | |
|  +--+--------------------+---------------------+------------------+---------+ |
|     |                    |                     |                  |           |
|     |            ids.py [GEÄNDERT]     provider_map.py [GEÄNDERT] paging.py   |
|     |            + message/row/mail    + 4 Provider-Kinds         (unverändert)
|     |                                                                         |
|  +--v---------------------------------------------------------------------+   |
|  |  nextcloud/capabilities.py [GEÄNDERT]                                  |   |
|  |  Kanal 1: GET /ocs/v2.php/cloud/capabilities  (spreed, tables)         |   |
|  |  Kanal 2: GET /ocs/v2.php/core/navigation/apps (mail) [NEU]            |   |
|  +--+---------------------------------------------------------------------+   |
|     |                                                                         |
|  +--v---------------------------------------------------------------------+   |
|  |  nextcloud/clients/  ocs  dav  caldav  carddav  notes  deck  xml       |   |
|  |  + talk.py [NEU]   + tables.py [NEU]   + mail.py [NEU]                 |   |
|  |  alle über ocs.parse_ocs bzw. ocs.parse_app_json, creds.auth() je Call |   |
|  +--+---------------------------------------------------------------------+   |
+-----|-------------------------------------------------------------------------+
      |
      v   Nextcloud (Impersonation via AUTHORIZATION-APP-API oder App-Passwort)
   /ocs/v2.php/apps/spreed/...   /ocs/v2.php/apps/tables/api/2/...
   /index.php/apps/tables/api/1/...   /index.php/apps/mail/api/...   /ocs/v2.php/apps/mail/message/...
```

### Component Responsibilities

| Komponente | Verantwortung | Für v1.2 |
|-----------|---------------|----------|
| `nextcloud/clients/*.py` | Eine API-Familie, URL-Bau, Pfad-ID-Wächter, Parser-Wahl (OCS-Envelope vs. App-JSON) | 3 neue Module |
| `nextcloud/capabilities.py` | App-Erkennung, 60-s-Cache, `require_app`, Fehlertext plus Hinweis | erweitert, plus ein zweiter Erkennungskanal |
| `tools/*.py` | Fachlogik, Antwort-Envelope, Kappung, Degradations-Wortlaut | 3 neue Module |
| `server/reg_*.py` | Schema (Annotated/Field), Annotationen, `compact`, `graceful` | 3 neue Dateien |
| `ids.py` | Ein Codec für jede adressierbare Ressource | 3 neue Kinds |
| `provider_map.py` | Unified-Search-Eintrag zu prefixierter ID, niemals raten | 4 neue Provider-Zeilen |
| `tools/chatgpt.py::fetch` | Die einzige Stelle, die eine ID zurück auf einen Leser routet | 2 bis 3 neue `case`-Zweige |
| `tools/context.py` | Bündel-Fan-out mit eigenem Budget pro Quelle | 2 neue Buckets, kein neues Bein |
| `scripts/check_tool_budget.py` | CI-Gate auf die Bytes von `tools/list` | Zahl steigt, Verfahren bleibt |

---

## Recommended Project Structure

Nur die Deltas. Alles andere bleibt, wo es liegt.

```
src/mcp_connector/
├── nextcloud/
│   ├── capabilities.py            # GEÄNDERT: 3 Apps, 2 Erkennungskanäle
│   └── clients/
│       ├── talk.py                # NEU: spreed OCS v4 (Räume) + v1 (Chat)
│       ├── tables.py              # NEU: OCS api/2 (Tabellen, Spalten, Zeile anlegen)
│       │                          #      + App-Route api/1 (Zeilen lesen)
│       └── mail.py                # NEU: OCS message/{id} (lesen)
│                                  #      + App-Route api/accounts|mailboxes|messages (auflisten)
├── tools/
│   ├── talk.py                    # NEU: browse(level), send_message
│   ├── tables.py                  # NEU: browse(level), create_row
│   ├── mail.py                    # NEU: browse(level), read   (rein lesend)
│   └── context.py                 # GEÄNDERT: KIND_BUCKETS, EXCERPT_KINDS
├── server/
│   ├── reg_talk.py                # NEU
│   ├── reg_tables.py              # NEU
│   └── reg_mail.py                # NEU
├── ids.py                         # GEÄNDERT: message:, row:, mail:
└── provider_map.py                # GEÄNDERT: PROVIDER_KINDS + Fragment-Auswertung

tests/
├── contract/
│   ├── test_tool_surface.py       # GEÄNDERT: EXPECTED_TOOLS, CREATE_TOOLS, len(), README-Tabelle
│   ├── test_no_destructive_calls.py  # GEÄNDERT: neue FORBIDDEN-Nadeln
│   └── test_read_only_side_effects.py # NEU: Talk-Leseaufruf trägt setReadMarker=0
├── integration/
│   └── test_exapp_app_route_matrix.py # NEU (Spike): Talk/Tables/Mail unter Impersonation
└── unit/
    ├── test_talk_client.py, test_talk_tools.py         # NEU
    ├── test_tables_client.py, test_tables_tools.py     # NEU
    └── test_mail_client.py, test_mail_tools.py         # NEU

scripts/check_tool_budget.py       # GEÄNDERT: BUDGET_BYTES, plus Messzeile je Anhebung
README.md / README.de.md / README.fr.md   # GEÄNDERT: Tool-Tabelle, Toolzahl
appinfo/info.xml                   # GEÄNDERT: Store-Text nennt die Familien namentlich
docs/client-setup.md, docs/conference-demo.md  # GEÄNDERT: Toolzahl (Contract-Test prüft das)
```

### Structure Rationale

- **Ein Client-Modul pro API-Familie, nicht pro App.** Tables braucht zwei API-Generationen (OCS `api/2` schreibt, App-Route `api/1` liest Zeilen) und Mail braucht zwei Routenarten (OCS liest eine Nachricht, interne Route listet). Beides gehört in je *ein* Modul, weil die Trennlinie sonst mitten durch eine Familie läuft und der Aufrufer sie kennen müsste.
- **Drei `reg_*`-Dateien statt einer.** `server/__init__.py::_load_registrations` importiert jedes `reg_*`-Modul automatisch. Damit ist eine neue Familie eine neue Datei plus nichts, und drei parallel geplante Phasen ändern keine gemeinsame Datei.
- **Kein `tools/talk_messages.py` neben `tools/talk.py`.** Ein Modul pro Familie, `level`-Enum statt Tool pro Ebene, genau wie D-06 es für Deck entschieden hat.

---

## Neue vs. geänderte Komponenten (explizit)

### Neu

| Datei | Inhalt | Vorbild in der Codebasis |
|-------|--------|--------------------------|
| `nextcloud/clients/talk.py` | `get_rooms`, `get_messages`, `send_message`, `check_message`, `_path_token` | `clients/deck.py` |
| `nextcloud/clients/tables.py` | `get_tables`, `get_columns`, `get_rows`, `create_row`, `_path_id` | `clients/deck.py` |
| `nextcloud/clients/mail.py` | `get_accounts`, `get_mailboxes`, `get_messages`, `get_message` | `clients/notes.py` |
| `tools/talk.py` | `browse(level)`, `send_message` | `tools/deck.py` |
| `tools/tables.py` | `browse(level)`, `create_row` | `tools/deck.py` |
| `tools/mail.py` | `browse(level)`, `read` | `tools/notes.py` |
| `server/reg_talk.py`, `reg_tables.py`, `reg_mail.py` | Schemata und Annotationen | `server/reg_deck.py` |
| `tests/contract/test_read_only_side_effects.py` | Beweist, dass jeder Talk-Leseaufruf `setReadMarker=0` und `markNotificationsAsRead=0` trägt | neu, es gibt kein Vorbild |
| `tests/integration/test_exapp_app_route_matrix.py` | Spike: erreichen die drei Familien Nextcloud unter reiner AppAPI-Impersonation | `tests/integration/test_exapp_dav_matrix.py` |

### Geändert

| Datei | Änderung | Risiko |
|-------|----------|--------|
| `nextcloud/capabilities.py` | `Capabilities` bekommt Felder für `spreed`, `tables`, `mail`; `has()`-Flags-Dict; `_MISSING` drei Einträge; `parse()` liest `tables.enabled` als Bool statt Präsenz; zweiter Kanal `core/navigation/apps` für Mail | mittel: der Cache-Key bleibt `(base_url, user)`, ein zweiter Request pro Kaltstart |
| `ids.py` | `encode_message`, `encode_row`, `encode_mail`; `parse()` drei neue Kinds; `_HINT` wächst | niedrig, aber `_HINT` steht in Fehlermeldungen, nicht in `tools/list` |
| `provider_map.py` | `PROVIDER_KINDS` plus `talk-message`, `talk-message-current`, `mail`; `extract_id` braucht einen Talk-Zweig, der `attributes.conversation` plus Fragment `message_<id>` liest, weil der Pfad `/call/{token}` kein numerisches Endsegment hat | mittel: hier entsteht der Unterschied zwischen "auflösbar" und `url` |
| `tools/chatgpt.py::fetch` | `case "message"`, `case "mail"` (`row` nur, falls Tabellenzeilen adressierbar werden) | mittel: T-01-77 lebt hier, ein geratener Prefix liest die falsche Ressource |
| `tools/context.py` | `KIND_BUCKETS` von 3 auf 5; neue Konstante `EXCERPT_KINDS` | mittel, siehe eigener Abschnitt |
| `scripts/check_tool_budget.py` | `BUDGET_BYTES` plus je eine Messzeile pro Anhebung | niedrig, aber CI-blockierend |
| `tests/contract/test_tool_surface.py` | `EXPECTED_TOOLS`, `CREATE_TOOLS`, `len(tools) == 16`, README-Tabellenabgleich, `_counted_tools`-Prüfung über `docs/` | hoch in dem Sinn, dass es jede Familienphase rot macht, bis alles nachgezogen ist |
| `tests/contract/test_no_destructive_calls.py` | `FORBIDDEN` bekommt Nadeln für die Schreibrouten der drei Apps | niedrig |
| `README.md`, `README.de.md`, `README.fr.md` | Tool-Tabelle (der Contract-Test liest nur `README.md`, die Dreisprachigkeitsregel verlangt alle drei), Sätze "16 tools" in Zeile 19 und 30 | niedrig, mechanisch |
| `appinfo/info.xml` | Zeile 29 nennt "files, calendar, notes, deck and contacts"; Talk, Tables und Mail müssen dazu, damit der Store-Text nicht untertreibt | niedrig, aber Store-Release nötig |
| `docs/client-setup.md`, `docs/conference-demo.md` | nennen "16 tools"; der Contract-Test verlangt entweder die aktuelle Zahl oder einen Zeiger auf `tests/contract/test_tool_surface.py` | niedrig |

### Ausdrücklich unverändert

`deps.py`, `nextcloud/credentials.py`, `nextcloud/http.py`, `exapp/*`, `oauth/*`, `server/__init__.py` (`graceful`, `compact`, `READ_ONLY`, `CREATE_ONLY` tragen die neuen Tools unverändert), `paging.py` (der Codec ist generisch; Talk paginiert über `lastKnownMessageId` statt Offset, das ist ein anderer Schlüssel im gleichen Dict, kein neuer Mechanismus), `errors.py`, `tools/marks.py`.

---

## Integration Points

### 1. App-Erkennung: drei Apps, aber nur zwei über Capabilities

`capabilities.py` fragt heute `GET /ocs/v2.php/cloud/capabilities` und liest die Sektionen `notes` und `deck`, wobei Präsenz gleich installiert bedeutet. Für die drei neuen Familien ist das nur zweimal richtig.

| App | Capabilities-Schlüssel | Form | Erkennung |
|-----|------------------------|------|-----------|
| Talk | `capabilities.spreed` | `features: [...]`, `config.chat.max-length`, `config.conversations.can-create` | Präsenz, wie Notes (HIGH, Talk-Doku) |
| Tables | `capabilities.tables` | `{enabled: bool, version, apiVersions: ["1.0","2.0","2.1"], features, isCirclesEnabled, column_types}` | **`enabled` auswerten, nicht Präsenz** (HIGH, `lib/Capabilities.php` gelesen) |
| Mail | keiner | Mail registriert keine `ICapability` | zweiter Kanal nötig (MEDIUM, Abwesenheitsbefund) |

**Empfehlung für Mail:** `GET /ocs/v2.php/core/navigation/apps` als zweiter Erkennungskanal. Das ist eine echte OCS-Route des Servers (`core/Controller/NavigationController.php`, `#[ApiRoute(verb: 'GET', url: '/navigation/apps', root: '/core')]`, `#[NoAdminRequired]`, liefert `list<CoreNavigationEntry>` mit `id`), sie ist nutzerbezogen und beantwortet damit genau die richtige Frage: nicht "ist die App auf dem Server", sondern "hat dieser Nutzer sie". Zwei Fallen: die Route kann `304 Not Modified` antworten (ETag), und sie listet nur Apps mit Navigationseintrag. Mail hat einen.

**Alternative, die man kennen sollte:** die Provider-Liste, die `tools/search.py` schon heute pro Aufruf über `ocs.list_search_providers` holt, enthält `mail`, wenn die App aktiv ist. Das ist kostenlos, aber es ist eine Liste über einen anderen Cache-Horizont (bewusst nicht gecacht) und würde die Capabilities-Semantik mit der Suchsemantik vermischen. Als Erkennung nur der zweite Wahlgang.

Konkret in `capabilities.py`:

```python
@dataclass(frozen=True, slots=True)
class Capabilities:
    notes_available: bool = False
    ...
    talk_available: bool = False
    talk_max_message_length: int = 0        # spreed.config.chat.max-length
    talk_can_create: bool = False           # spreed.config.conversations.can-create
    tables_available: bool = False           # tables.enabled, nicht Präsenz
    tables_api_versions: tuple[str, ...] = ()
    mail_available: bool = False             # aus core/navigation/apps
```

`load()` wird damit zu zwei Requests bei kaltem Cache. Das ist vertretbar, weil `require_app` ohnehin einmal pro Tool-Aufruf läuft und der 60-s-Cache beides zusammen hält. Wer den zweiten Request sparen will, holt ihn erst, wenn eine Mail-Frage gestellt wird (Lazy-Zweig im gleichen Cache-Eintrag). Das ist eine Umsetzungsentscheidung, keine Architekturentscheidung.

### 2. Client-Schicht: die Endpunkte, gemessen an dem, was wirklich existiert

**Talk** (Basis `ocs.ocs_url`, Parser `ocs.parse_ocs`, denn spreed antwortet im OCS-Envelope)

| Zweck | Methode und Pfad | Parameter, die Architektur sind |
|-------|------------------|--------------------------------|
| Konversationen | `GET /ocs/v2.php/apps/spreed/api/v4/room` | `noStatusUpdate=1` |
| Nachrichten | `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | `lookIntoFuture=0`, `limit<=200`, `lastKnownMessageId`, **`setReadMarker=0`**, **`markNotificationsAsRead=0`**, `noStatusUpdate=1` |
| Senden | `POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | `message` (max. 32000 Zeichen bzw. `config.chat.max-length`), optional `replyTo` |

Die beiden fett gesetzten Parameter sind der wichtigste Einzelbefund dieser Recherche. Ihre Vorgabewerte sind `1`: **ein naiver Leseaufruf setzt die Leseposition und quittiert Benachrichtigungen, also schreibt er.** Das AST-Grep-Gate sieht das nicht, weil es HTTP-Verben und Pfadfragmente prüft und dies ein GET auf einen Leseendpunkt ist. Deshalb der neue Contract-Test `test_read_only_side_effects.py`: er behauptet positiv, dass die Parameter im Query jedes Talk-Leseaufrufs stehen. Ein Denylist-Gate kann diese Klasse nicht fangen, eine Allowlist-Behauptung schon.

Zweiter Talk-Befund: der Raum-Token ist **nicht numerisch**. Er kommt aus `ISecureRandom` über Kleinbuchstaben plus Ziffern ohne `l`, `0` und `1` (`lib/Manager.php`). Der `_path_id`-Wächter von Deck und Notes (`text.isdigit()`) ist hier also falsch; es braucht `_path_token` mit einem Zeichensatz-Wächter (`^[a-z0-9]{4,64}$`), aus demselben Grund wie damals: der Wert geht in einen URL-Pfad (T-01-63).

**Tables** (zwei Generationen, mit Absicht)

| Zweck | Methode und Pfad | Parser |
|-------|------------------|--------|
| Tabellen | `GET /ocs/v2.php/apps/tables/api/2/tables` | `parse_ocs` |
| Spalten | `GET /ocs/v2.php/apps/tables/api/2/columns/{nodeType}/{nodeId}` | `parse_ocs` |
| **Zeilen lesen** | `GET /index.php/apps/tables/api/1/tables/{tableId}/rows?limit&offset` | `parse_app_json` |
| Zeile anlegen | `POST /ocs/v2.php/apps/tables/api/2/{tables\|views}/{nodeId}/rows`, Body `{"data": {"<columnId>": "<value>"}}` | `parse_ocs` |

Warum die Mischung: in der `openapi.json` der Tables-App gibt es unter `api/2` **keine** Route, die Zeilen einer Tabelle liest (nur `public/{token}/rows` für Freigabe-Links). Zeilenlesen existiert ausschliesslich in `api/1` als App-Route. Beide `api/1`-Controller-Methoden tragen `#[NoCSRFRequired]` und `#[CORS]`, sind also eine zugesagte API und nicht Frontend-Innenleben. Der Preis: `tables_browse(level="rows")` braucht zwei Requests, Spalten plus Zeilen, weil eine Zeile ihre Werte als `{columnId, value}` trägt und ohne Spaltentitel unlesbar ist. Das ist derselbe Handel, den `deck_browse(level="cards")` schon macht, nur umgekehrt: Deck spart den zweiten Request, Tables braucht ihn.

**Mail** (die eine Familie mit einer Architekturentscheidung)

| Zweck | Methode und Pfad | Charakter |
|-------|------------------|-----------|
| Konten | `GET /index.php/apps/mail/api/accounts` | intern, ohne CSRF-Attribut |
| Postfächer | `GET /index.php/apps/mail/api/mailboxes?accountId=N` | intern, `forceSync` bleibt `false` |
| Nachrichtenliste | `GET /index.php/apps/mail/api/messages?mailboxId=N&cursor=&limit=N` | intern, `limit` serverseitig auf 100 gekappt |
| **Eine Nachricht mit Inhalt** | `GET /ocs/v2.php/apps/mail/message/{id}` | OCS, typisierte Antwort `MailMessageApiResponse` |

Die Empfehlung ist die Zweiteilung selbst: **auflisten über die interne Route, den Inhalt über OCS lesen.** Der eine Aufruf, der wirklich fremde, von aussen geschriebene Prosa in den Kontext eines Modells hebt, läuft damit über die einzige Mail-Route, die die App selbst als API deklariert (`MessageApiController extends OCSController`). Die interne Route trägt nur Metadaten und ist damit die billigste Stelle, um bei einem Mail-Update zu brechen.

Warum die interne Route überhaupt erreichbar ist, sauber belegt: `messages#index` trägt `@NoAdminRequired`, aber **kein** `NoCSRFRequired`. `SecurityMiddleware::isInvalidCSRFRequired` ruft dann `Request::passesCSRFCheck()`, und das gibt `true` zurück, sobald der Header `OCS-APIRequest` gesetzt ist (`lib/private/AppFramework/Http/Request.php`, Zeile 436), während `cookieCheckRequired()` ohne Session-Cookie ohnehin `false` liefert. Dieses Projekt schickt `OCS-APIRequest: true` per D-18 auf jedem Request, auch auf reinen App-Routen. Der Weg ist also offen, aber er ist **neu für dieses Projekt**: Notes, Deck und Tables-`api/1` tragen alle `#[NoCSRFRequired]`, Mail ist die erste Familie, die auf diesem Pfad läuft. Genau deshalb der Spike vor der ersten Zeile Mail-Tool-Code.

Drei Mail-Wächter, die in die Architektur gehören und nicht in einen Review-Kommentar:

1. **`/message/send` existiert im OCS-Bestand von Mail** (`#[ApiRoute(verb: 'POST', url: '/message/send')]` auf demselben Controller wie `get`). Der Pfad muss als Nadel in `FORBIDDEN` von `test_no_destructive_calls.py`, sonst ist "kein Senden" eine Behauptung über heute.
2. `mailboxes#markAllAsRead` (`/api/mailboxes/{id}/read`), `mailboxes#clearMailbox` (`/api/mailboxes/{id}/clear`) und `messages#setFlags` sind ebenfalls Nadeln. Keine davon ist `DELETE`, das Gate sieht sie also nicht von allein.
3. `AccountsController::index` gibt `mailAccount->jsonSerialize()` durch, und darin stehen IMAP- und SMTP-Hostnamen und Kontonamen. Das Tool projiziert auf `accountId`, `emailAddress`, `name` und gibt die Rohantwort niemals weiter. Das ist dasselbe Projektionsmuster, das `tools/deck.py::_boards` schon anwendet, hier aber mit einem Datenschutzgrund statt eines Tokengrunds.

### 3. Tool-Schicht und Registry

Drei `reg_*`-Dateien, sechs Tools. Die Formen folgen `reg_deck.py`, weil dessen Entscheidungen (Level-Enum, leerer String statt `None` im Schema, `MAX_LIMIT` aus dem Tool-Modul) genau die Schema-Diät sind, die dieser Meilenstein für die neuen Tools verlangt.

| Tool | Annotation | Parameter | Besonderheit |
|------|-----------|-----------|--------------|
| `talk_browse` | READ_ONLY | `level` (`conversations\|messages`), `conversation`, `limit`, `cursor` | Cursor trägt `lastKnownMessageId` plus Token, `paging.check_scope` gegen Token-Verwechslung |
| `talk_send_message` | CREATE_ONLY | `conversation`, `message`, `reply_to` | Vorprüfung `readOnly` des Raums aus der Raumliste, genau wie `deck._require_write_permission`; Längenprüfung gegen `config.chat.max-length` |
| `tables_browse` | READ_ONLY | `level` (`tables\|columns\|rows`), `table_id`, `limit`, `cursor` | `rows` sind zwei Requests, Spaltentitel werden in die Zeile eingesetzt |
| `tables_create_row` | CREATE_ONLY | `table_id`, `values` | `values` ist ein **JSON-String**, kein Dict, siehe Muster 3 |
| `mail_browse` | READ_ONLY | `level` (`accounts\|mailboxes\|messages`), `account_id`, `mailbox_id`, `limit`, `cursor` | drei Ebenen, weil `mailboxes` ohne `accountId` nicht antwortet |
| `mail_read` | READ_ONLY | `message_id` | der einzige Aufruf, der einen Mail-Body holt; über OCS |

Damit sind es 22 Tools und sechs Schreibpfade werden vier plus zwei, also `CREATE_TOOLS` = `{files_upload, calendar_create_event, notes_create, deck_create_card, talk_send_message, tables_create_row}`. Mail bleibt vollständig aus `CREATE_TOOLS` heraus, und das ist der Punkt der Familie.

### 4. IDs, provider_map und fetch

Neue Kinds in `ids.py`:

```
message:<token>:<messageId>     # Talk-Nachricht, Token ist [a-z0-9], kollidiert nicht mit ":"
row:<tableId>:<rowId>           # Tabellenzeile (nur falls adressierbar gebraucht)
mail:<messageId>                # Mail-Nachricht, numerische Mail-DB-ID
```

In `provider_map.PROVIDER_KINDS` kommen vier Zeilen dazu, und zwei davon brauchen mehr als die Tabelle:

| Provider-ID (live verifiziert im Quellcode) | Kind | Woraus die ID entsteht |
|---------------------------------------------|------|------------------------|
| `talk-message` | `message` | `attributes.conversation` (Token) plus Fragment `#message_<id>` |
| `talk-message-current` | `message` | dito |
| `mail` | `mail` | letztes numerisches Pfadsegment von `/index.php/apps/mail/open/{messageId}` |
| `talk-conversations` | bleibt `url` | eine Konversation ist kein Dokument |
| `tables-search-tables` | bleibt `url` | der Link trägt die ID im **Fragment** (`#/table/{id}`), nicht im Pfad |

Zwei Dinge daran sind wichtig. Erstens: der Modul-Docstring von `provider_map.py` nennt heute schon `#message_42` als Beispiel dafür, warum `absolute_url` das Fragment erhält und die Herkunft verwirft. Diese Vorarbeit zahlt jetzt ein, `extract_id` braucht nur einen Talk-Zweig, der Fragment und `attributes` liest. Zweitens: `_last_numeric_segment` liest ausschliesslich `urlsplit(url).path`. Für Mail passt das exakt, für Talk und Tables passt es nicht, und der ehrliche Ausgang ist bei Tables `url` mit `resolvable: false` statt einer geratenen Tabellen-ID.

In `chatgpt.fetch` kommen `case "message"` und `case "mail"` dazu. Beide sind so dünn wie `_fetch_note`: `require_app`, ein Client-Aufruf, `marks.without_marks` über den fremden Text, Projektion auf `{id, title, text, url, metadata}`. Für `message` heisst "eine Nachricht lesen" praktisch: die Nachricht plus einen kleinen Kontext um sie herum, was mit `lastKnownMessageId` und `limit` gut geht, aber eine Designentscheidung ist, die in der Phase getroffen und im Docstring begründet werden muss.

---

## prepare_context: Wachstum ohne Vertragsbruch

Der Vertrag von `tools/context.py` besteht aus vier Zusagen: eigenes Budget pro Quelle statt eines globalen Timeouts, jede Kappung schreibt einen `degraded`-Eintrag, Wanduhr gleich Maximum der Teile statt Summe, fremder Text bleibt Datenfeld. Alle vier bleiben erhalten, wenn man den billigen Weg nimmt.

**Empfohlen: kein neues Bein, zwei neue Buckets.**

```python
KIND_BUCKETS = ("file", "note", "card", "message", "mail")   # war 3, wird 5
EXCERPT_KINDS = ("file", "note", "card")                      # NEU, bewusst nicht 5
```

Die Begründung steht schon im Docstring des Moduls: die Suche wird **ohne Provider-Einschränkung** gefragt, damit eine neu installierte Such-App ohne Codezeile im Bündel ankommt. Genau das ist bei Talk und Mail heute der Fall. `talk-message` und `mail` liefern bereits Treffer in dieses Bündel, sie landen nur im `other`-Bucket mit `resolvable: false`. Zwei Zeilen in `provider_map` und zwei Bucket-Namen machen sie zu benannten, auflösbaren Treffern. Kein `asyncio.gather`-Bein, kein neues Budget, kein neuer Degradations-Grund, keine zusätzliche Nextcloud-Runde.

**Die Antwortgrösse wächst dabei kaum, und das ist rechenbar.** Die Obergrenze der Trefferzahl ist `SEARCH_LIMIT = 25`, nicht `MAX_PER_BUCKET * len(BUCKETS)`. Heute können maximal 20 der 25 Treffer gezeigt werden (4 Buckets à 5), künftig maximal 25 (6 Buckets à 5). Mehr Buckets verteilen also um, sie blasen nicht auf. Der Zuwachs ist auf fünf zusätzliche Trefferzeilen begrenzt, jede rund 120 Byte kompakt, also unter 700 Byte im schlechtesten Fall.

**`EXCERPT_KINDS` ist die eigentliche Entscheidung.** `_excerpts` zieht heute die ersten drei auflösbaren Treffer über `KIND_BUCKETS` in der dokumentierten Reihenfolge und liest je bis 2 KB Inhalt. Würde man die Liste einfach auf fünf Kinds erweitern, könnte ein Mail-Body zum Auszug werden, und ein Mail-Body ist der am leichtesten von aussen beschreibbare Text im ganzen System: jeder Fremde kann eine Mail an die Nutzerin senden und damit Text in ihren Assistenzkontext legen. D-57 sagt, fremder Text bleibt Datenfeld, und das gilt weiter. Aber die Angriffsfläche wächst um eine Klasse, in der die Autorenschaft nicht einmal mehr eine Nextcloud-Berechtigung voraussetzt. Empfehlung: `EXCERPT_KINDS` bleibt `("file", "note", "card")`, Talk und Mail erscheinen im Bündel mit Titel, Herkunft und ID, aber ohne Auszug, und ein Satz im Docstring sagt, warum. Wer den Auszug will, ruft `fetch` und trifft damit eine bewusste Entscheidung.

**Die verworfene Alternative, mit Preis.** Ein drittes und viertes `gather`-Bein (etwa "ungelesene Talk-Konversationen" und "die letzten Mails im Posteingang") wäre technisch vertragskonform: eigenes Budget, eigener `degraded`-Name, Wanduhr bleibt das Maximum. Es kostet aber zwei bis drei zusätzliche Nextcloud-Runden **in jedem** `prepare_context`-Aufruf, auch in denen, in denen niemand nach einer Nachricht gefragt hat, und es verwandelt ein Bündel für eine Frage in ein Dashboard. Es gibt genau einen Grund, es später doch zu tun: "ungelesen" ist keine Volltextfrage und über die Suche nicht ausdrückbar. Das gehört in den Backlog, nicht in v1.2.

---

## Budget-Gate: Rechnung und Landeplatz

**Ist-Messung, heute gelaufen** (`uv run python scripts/check_tool_budget.py`): **11268 Bytes, 16 Tools, Budget 12500.** Der Envelope ohne Tools sind 174 Bytes.

Gemessene Grössen je Tool, sortiert, mit Parameterzahl:

| Bytes | Params | Tool |
|------:|:------:|------|
| 1351 | 8 | calendar_create_event |
| 951 | 5 | calendar_list_events |
| 924 | 1 | search (mit outputSchema) |
| 877 | 5 | deck_create_card |
| 761 | 1 | fetch (mit outputSchema) |
| 736 | 4 | deck_browse |
| 703 | 4 | files_search |
| 678 | 3 | unified_search |
| 644 | 3 | notes_create |
| 625 | 2 | prepare_context |
| 538 | 3 | files_list |
| 501 | 2 | files_upload, files_read |
| 487 | 2 | contacts_search |
| 478 | 2 | notes_search |
| 339 | 1 | notes_read |

Daraus ein belastbares Kostenmodell für die Planung: **rund 250 Byte Sockel plus rund 125 Byte je dokumentierter Parameter**, ohne `outputSchema`. Gegenprobe: 1 Param 375 gegen gemessen 339, 2 Params 500 gegen 478 bis 501, 4 Params 750 gegen 703 bis 736, 5 Params 875 gegen 877. Ein Enum kostet etwas mehr als ein freier String, eine ausführliche Beschreibung erklärt den Ausreisser `calendar_create_event`.

Schätzung für v1.2:

| Neues Tool | Params | Schätzung |
|-----------|:------:|----------:|
| talk_browse | 4 (1 Enum) | 780 |
| talk_send_message | 3 | 660 |
| tables_browse | 4 (1 Enum) | 790 |
| tables_create_row | 2 | 520 |
| mail_browse | 5 (1 Enum) | 900 |
| mail_read | 1 | 360 |
| **Summe** | | **4010** |

**Erwartete Endmessung: 11268 + 4010 = rund 15300 Bytes bei 22 Tools.** Planungszuschlag für Wortlaut nach Review: 15300 bis 15800. In Tokens gerechnet, bei den ~4 Byte pro Token, die der Skriptkommentar ansetzt: von rund 2,8k auf rund 3,8k Tokens in jeder Sitzung jedes Clients, also plus etwa 36 Prozent. Das ist der Preis der Breite, und er sollte in der Meilenstein-Doku stehen, weil "kuratiert schlank" ein Verkaufsargument ist. Cursors Grenze von 80 Tools bleibt mit 22 unkritisch.

**Wo die Anhebung landet.** Der Skriptkommentar hält die Regel fest: anheben ist erlaubt, aber nur mit einer neuen Messzeile darüber, damit eine Regression zuschreibbar bleibt. Zwei Fragen dazu.

*Wann?* Nicht in einer Vorphase auf Vorrat. Das Gate ist ein CI-Gate, und schon die erste Familie überschreitet 12500. Also **eine Anhebung pro Familienphase, jeweils in demselben Commit, der die Tools bringt, mit frischer Messzeile.** Beispielhafter Verlauf: nach Tables 12578 gegen Gate 13000, nach Talk 14018 gegen 14500, nach Mail 15278 gegen 16000. So ist die Zahl nie geraten, und niemand muss am Ende eine provisorische Zahl zurücknehmen.

*Wie hoch?* Die alte Formel war Messung plus 15 Prozent, aufgerundet auf 500. Bei 15300 sind 15 Prozent aber 2300 Byte, und das sind rund drei ganze Tools Spielraum, also ein entwaffnetes Gate. Empfehlung: **Messung plus 5 Prozent, aufgerundet auf die nächsten 500** (16000 bei 15300), und zusätzlich eine zweite Behauptung im Skript, die die aggregierte Zahl nicht hat: **kein einzelnes Tool über 1400 Bytes.** Der heutige Ausreisser (`calendar_create_event`, 1351) liegt knapp darunter, ein neues Tool mit acht Parametern und Absatzbeschreibung fällt darüber, und genau das ist die Regression, die eine Gesamtzahl mit 2300 Byte Luft nie melden würde.

*Optionaler Rabatt, falls es eng wird:* eine Diätrunde über `calendar_create_event` (1351) und `calendar_list_events` (951) holt erfahrungsgemäss 200 bis 300 Byte, ohne ein Feature anzufassen. Das wäre der ehrlichere Hebel als ein grösseres Budget.

---

## Architectural Patterns

### Muster 1: Ein Browse-Tool mit `level`-Enum je Familie

**Was:** Navigation innerhalb einer App ist ein Enum-Wert, kein Tool pro Ebene.
**Wann:** immer, wenn eine App eine Hierarchie hat (Talk: Konversation zu Nachricht, Tables: Tabelle zu Spalte zu Zeile, Mail: Konto zu Postfach zu Nachricht).
**Handel:** ein Schema statt drei, dafür ein Tool, dessen Pflichtparameter von `level` abhängen. Das kostet einen Rundlauf, wenn das Modell `board_id` vergisst, und `tools/deck.py` löst das mit einem Fehlertext, der den nächsten Aufruf nennt.

```python
if level not in LEVELS:
    raise ToolError(message=f"{level!r} is not a Talk level.", hint=_LEVEL_HINT)
capped = min(max(limit, 1), MAX_LIMIT)
await capabilities.require_app(clients, APP)
```

### Muster 2: `require_app` als erste Zeile, nicht als Except-Zweig

**Was:** jedes Tool einer optionalen App fragt zuerst die Capabilities, dann die App.
**Wann:** alle sechs neuen Tools.
**Handel:** ein gecachter Request gegen eine Fehlermeldung, die "die Talk-App ist auf dieser Nextcloud nicht installiert" sagt statt eines 404 auf einer HTML-Loginseite. `tools/list` bleibt dabei statisch, das ist SRV-04 und ändert sich nicht.

### Muster 3: Ein Freiform-Feld ist ein String, kein Dict

**Was:** `tables_create_row(values: str)` mit kompaktem JSON als Wert, nicht `values: dict[str, str]`.
**Warum:** ein Dict-Parameter zieht `additionalProperties` oder ein `$defs` ins Input-Schema, und der Contract-Test verbietet `$defs` ausdrücklich an mehreren Stellen. Es gibt dafür schon einen Präzedenzfall in der Codebasis: `unified_search.providers` ist ein Komma-String statt einer Liste, und `test_tool_surface.py` behauptet das wörtlich ("an optional string beats an anyOf of list and null").
**Handel:** das Tool muss den String parsen und einen Parsefehler in einen Satz mit Beispiel verwandeln. Das ist eine Funktion mit drei Zeilen gegen rund 200 Byte Schema in jeder Sitzung.

### Muster 4: Der Schreibpfad prüft die Berechtigung des Objekts, nicht die des Kontos

**Was:** `talk_send_message` liest `readOnly` des Raums aus der Raumliste, bevor es sendet, statt in einen 403 zu laufen.
**Vorbild:** `tools/deck.py::_require_write_permission`, wo `canCreateBoards` bewusst nicht als Antwort auf "darf ich eine Karte anlegen" genommen wird.
**Handel:** ein Request mehr im Schreibpfad, dafür eine Fehlermeldung, die den Raum benennt und sagt, was zu tun ist.

### Muster 5: Positive Behauptung, wo ein Denylist-Gate blind ist

**Was:** ein Contract-Test, der behauptet, dass jeder Talk-Leseaufruf `setReadMarker=0` und `markNotificationsAsRead=0` trägt, und dass die URL-Konstanten der drei neuen Clients gleich einem eingefrorenen Literal sind.
**Warum:** `test_no_destructive_calls.py` sucht Verben und Pfadfragmente. Ein GET mit einem schreibenden Vorgabeparameter ist damit unsichtbar. Ein eingefrorenes Literal über die gebauten URLs fängt zusätzlich die Route, die niemand verboten hat, weil niemand an sie gedacht hat.

---

## Data Flow

### Talk-Lesepfad

```
talk_browse(level="messages", conversation="a1b2c3d4", limit=25, cursor=...)
   -> deps.resolve_clients(ctx)                     [unverändert]
   -> capabilities.require_app(clients, "talk")     [Cache 60 s, sonst 1 bis 2 Requests]
   -> paging.decode_cursor -> lastKnownMessageId, check_scope gegen Token
   -> clients/talk.get_messages(token, lookIntoFuture=0, setReadMarker=0,
                                markNotificationsAsRead=0, noStatusUpdate=1)
   -> ocs.parse_ocs
   -> tools/talk._envelope(level, results, limit) + "next" wenn gekappt
   -> compact() -> graceful() -> MCP
```

### Mail-Lesepfad, zweigeteilt

```
mail_browse(level="messages", mailbox_id="7")
   -> GET /index.php/apps/mail/api/messages?mailboxId=7&limit=25    [intern, Metadaten]
   -> Projektion auf id, subject, from, date, hasAttachments

mail_read(message_id="4711")
   -> GET /ocs/v2.php/apps/mail/message/4711                        [OCS, Inhalt]
   -> marks.without_marks(body)                                     [D-57 bleibt]
```

### prepare_context nach der Änderung

```
prepare_context(query, detail)
   |
   +-- unified_search(limit=25)  [ein Bein, unverändert, ohne Provider-Filter]
   |      -> provider_map.extract_id je Eintrag
   |         files -> file | notes -> note | deck -> card
   |         talk-message(-current) -> message  [NEU]
   |         mail -> mail                       [NEU]
   |         Rest -> url, resolvable: false
   |      -> _bundle: 6 Buckets à MAX_PER_BUCKET, Kappung schreibt degraded
   |
   +-- _events(CALENDAR_BUDGET=10 s)  [ein Bein, unverändert]
   |
   +-- _excerpts nur über EXCERPT_KINDS = (file, note, card)  [NEU begrenzt]
          -> chatgpt.fetch(max_bytes=EXCERPT_READ_BYTES), eigenes 5-s-Budget je Auszug
```

Kein neues Bein, kein neues Budget, kein neuer `degraded`-Grund. Der einzige Vertragstext, der sich ändert, ist der Docstring: er muss sagen, dass Nachrichten und Mails im Bündel erscheinen, aber keinen Auszug bekommen, und warum.

---

## Kosten und Skalierung

Nicht Nutzerzahlen sind hier die Achse, sondern Runden pro Aufruf, Bytes pro Sitzung und Wartungslast pro Familie.

| Achse | heute | nach v1.2 | Was zuerst bricht |
|-------|-------|-----------|-------------------|
| `tools/list` | 11268 B, 16 Tools | ~15300 B, 22 Tools | Client-Tool-Limits sind unkritisch; die Tokens pro Sitzung sind die reale Kosten |
| Runden je Leseaufruf | 1 bis 2 (plus Capabilities kalt) | Talk 1, Tables `rows` 2, Mail `messages` 1, `mail_read` 1 | Tables `rows` ist der einzige neue Zweirunden-Pfad |
| Capabilities kalt | 1 Request | 2 Requests (Capabilities plus Navigation) | nur beim ersten Aufruf je 60-s-Fenster und Nutzer |
| `prepare_context` | 2 Beine, Wanduhr ~1 s gemessen | 2 Beine, unverändert | nichts, wenn kein Bein dazukommt |
| Wartung | 5 Familien | 8 Familien | Solo-Betrieb: Mail ist die einzige, die bei einem Nextcloud-Update ohne Vorwarnung brechen kann |

---

## Anti-Patterns

### Ein Tool pro Ebene oder pro Postfach

**Was Leute tun:** `talk_list_conversations`, `talk_read_messages`, `mail_list_accounts`, `mail_list_mailboxes`, `mail_list_messages`.
**Warum falsch:** fünf Schemata für Navigation, die ein Enum-Wert ausdrückt, rund 3000 zusätzliche Bytes in jeder Sitzung, und genau die Tool-Flut, gegen die dieses Projekt positioniert ist. `test_tool_surface.py` hat für Deck schon eine explizite Verbotsliste (`deck_list_boards` und Geschwister); die neuen Familien brauchen dieselbe.
**Stattdessen:** ein `*_browse` mit `level`, plus höchstens ein zweites Tool für den Sonderfall, der wirklich anders ist (`mail_read`, weil der Body über eine andere Route kommt).

### Den Talk-Leseendpunkt mit Vorgabewerten aufrufen

**Was Leute tun:** `GET /chat/{token}?limit=50` und fertig.
**Warum falsch:** `setReadMarker` und `markNotificationsAsRead` haben den Vorgabewert 1. Der Aufruf setzt damit die Leseposition der Nutzerin und quittiert ihre Benachrichtigungen. Ein Assistent, der ein Postfach "nur anschaut", hat danach 40 ungelesene Nachrichten als gelesen markiert, und niemand hat je eine Schreiboperation angefordert. Das AST-Grep-Gate sieht davon nichts.
**Stattdessen:** beide Parameter explizit auf 0, `lookIntoFuture=0`, `noStatusUpdate=1`, und ein Contract-Test, der das positiv behauptet.

### `forceSync=true` beim Postfach-Listing

**Was Leute tun:** frische Daten wollen und `forceSync` setzen.
**Warum falsch:** das löst eine IMAP-Synchronisation aus, also einen serverseitigen Vorgang mit unbestimmter Dauer, angestossen von einem Tool, das "lesen" heisst. Ein Modell, das es dreimal probiert, hat drei Synchronisationen bestellt.
**Stattdessen:** Vorgabewert `false` lassen und im Antworttext sagen, dass die Liste den Stand der letzten Synchronisation zeigt. Das ist genau die Erwartungssteuerung, die `search.SEARCH_NOTE` für die Volltextsuche schon macht.

### Die Rohantwort einer App durchreichen

**Was Leute tun:** `return compact(await mail_client.get_accounts(...))`.
**Warum falsch:** `AccountsController::index` serialisiert das Konto samt IMAP- und SMTP-Hostnamen und Kontonamen. Das gehört nicht in einen Modellkontext, und es kostet Tokens für Felder, die niemand liest.
**Stattdessen:** projizieren, wie `tools/deck.py::_boards` und `chatgpt._as_hit` es tun: die drei bis fünf Felder, die ein Folgeaufruf braucht.

### Eine Tabellen-ID aus dem Suchergebnis raten

**Was Leute tun:** aus dem Provider `tables-search-tables` eine `row:`- oder `table:`-ID bauen.
**Warum falsch:** der Link der App trägt die ID im **Fragment** (`#/table/{id}`), nicht im Pfad. `_last_numeric_segment` findet dort nichts, und eine geratene ID adressiert eine andere Tabelle. Das ist derselbe Fehler, den `provider_map` beim Kalender-Provider bewusst nicht macht.
**Stattdessen:** `url` mit `resolvable: false`, und ein Satz im Docstring, warum.

---

## Build Order

Vier Phasen, plus eine kleine vorgeschaltete. Die Reihenfolge folgt zwei Regeln: Risiko zuerst messen, Mechanik zuerst dort einführen, wo sie am wenigsten kostet.

### Phase 0: Erreichbarkeits-Spike (klein, blockierend)

**Was:** eine Integrationsdatei `tests/integration/test_exapp_app_route_matrix.py` nach dem Muster von `test_exapp_dav_matrix.py`, drei Zeilen: ein Talk-Raumlisting, ein Tables-Zeilenlesen, ein Mail-Postfachlisting, alle drei unter reiner AppAPI-Impersonation mit `mode="appapi"` und ohne App-Passwort im Prozess, plus die beiden Kontrollen, die die vorhandene Datei schon hat.
**Warum zuerst:** die vorhandene Matrix beweist Impersonation für `remote.php`, `ocs/v2.php` und `index.php/apps/...`, aber Notes, Deck und Tables-`api/1` tragen alle `#[NoCSRFRequired]`. Mail ist die erste Familie, deren Listing auf dem CSRF-Pfad "der `OCS-APIRequest`-Header genügt" läuft. Der Pfad ist im Serverquellcode belegt, aber nicht in dieser Topologie mit HaRP und AppAPI davor gemessen.
**Was der Spike entscheidet:** wenn Mail unter Impersonation nicht erreichbar ist, fällt Mail aus dem Meilenstein und der Roadmap fehlt eine Phase, statt dass die letzte Phase scheitert. Das ist der billigste Zeitpunkt für diese Nachricht.

### Phase 1: Tables

**Warum zuerst:** die kleinste Neuheit. Numerische IDs, `parse_app_json` und `parse_ocs` beide vorhanden, Browse-plus-Create genau wie Deck, kein Eingriff in `ids.py`, `provider_map.py`, `chatgpt.fetch` oder `context.py`. Damit wird die lange, halbmechanische Checkliste "was berührt eine neue Familie" (Capabilities-Feld, `_MISSING`-Text, `EXPECTED_TOOLS`, `CREATE_TOOLS`, `len(tools)`, README-Tabelle in drei Sprachen, `info.xml`, Toolzahl in `docs/`, Budget-Messzeile) einmal an der risikolosen Familie durchgespielt und für die beiden schwierigen dokumentiert.
**Neue Mechanik, die hier trotzdem entsteht:** `tables.enabled` als Bool statt Präsenz in `capabilities.parse`, zwei API-Generationen in einem Client-Modul, der JSON-String-Parameter aus Muster 3, und die erste Budget-Anhebung mit Messzeile.

### Phase 2: Talk

**Warum an zweiter Stelle:** hier sitzen die querschneidenden Änderungen. Nicht-numerische Pfad-IDs (neuer Wächter), drei neue Kinds in `ids.py`, der erste neue Eintrag in `provider_map.PROVIDER_KINDS` mit Fragment-Auswertung, der erste neue `case` in `chatgpt.fetch`, und der Lese-mit-Schreibwirkung-Befund mit seinem neuen Contract-Test. Nach dieser Phase sind alle Nähte geweitet, die Mail dann nur noch benutzt.
**Abhängigkeit nach vorn:** `provider_map` und `fetch` müssen hier so gebaut werden, dass ein weiteres Kind eine Zeile ist. Wenn Talk hier hart in `extract_id` verdrahtet wird, zahlt Phase 3 dafür.

### Phase 3: Mail

**Warum zuletzt:** die einzige Familie ohne Capabilities (braucht den zweiten Erkennungskanal), die einzige mit einem internen Listing ohne API-Zusage, die sensibelste inhaltlich, die mit dem `/message/send` im eigenen OCS-Bestand, und die, die am meisten von den in Phase 2 geweiteten Nähten profitiert. Ausserdem die einzige, deren Erreichbarkeit erst Phase 0 klärt.
**Enthält:** `core/navigation/apps` als zweiter Kanal, die Zweiteilung Listing-intern gegen Inhalt-über-OCS, drei bis vier neue `FORBIDDEN`-Nadeln, die Projektion der Kontoantwort.

### Phase 4: prepare_context, Budget-Endstand und Aussenwirkung

**Warum getrennt und am Ende:** `KIND_BUCKETS` und `EXCERPT_KINDS` sind erst sinnvoll zu entscheiden, wenn beide neuen Kinds existieren und `fetch` sie auflösen kann. Hier landet auch die Endmessung des Budgets, die Tightening-Entscheidung (plus 5 Prozent statt 15, plus Pro-Tool-Deckel), die Toolzahl in README in drei Sprachen, der Store-Text in `appinfo/info.xml` und die Toolzahlen in `docs/`, die der Contract-Test prüft.

### Warum nicht Talk zuerst

Talk ist die attraktivere Familie und die mit der besten Dokumentation, und man könnte argumentieren, dass die querschneidenden Änderungen zuerst gehören. Dagegen spricht: die Familienphase besteht zu einem guten Teil aus mechanischer Nacharbeit an fünf eingefrorenen Testliteralen, drei READMEs, einer `info.xml` und mehreren Dokumentseiten. Diese Choreografie einmal an der Familie zu lernen, die sonst nichts Neues verlangt, macht die beiden schwierigen Phasen kürzer. Wer Talk zuerst baut, lernt beides gleichzeitig.

---

## Offene Punkte, die live zu prüfen sind

| Frage | Status | Prüfweg |
|-------|--------|---------|
| Erreicht Mails internes Listing Nextcloud unter AppAPI-Impersonation | offen, MEDIUM | Phase-0-Spike gegen die Docker-Topologie |
| Exakter OCS-Pfad von `messageApi#get` | MEDIUM (`/ocs/v2.php/apps/mail/message/{id}` erwartet) | ein `curl` gegen die Testinstanz |
| Veröffentlicht Mail wirklich keine Capabilities | MEDIUM (Abwesenheitsbefund aus `lib/AppInfo/Application.php`) | `cloud/capabilities` einmal abrufen und nach `mail` greppen |
| Antwortet `core/navigation/apps` in dieser Topologie mit 200 oder 304 | offen | Spike, gleicher Lauf |
| Trägt ein Talk-Nachrichtentreffer `attributes.conversation` auch in der installierten Talk-Version | HIGH im Quellcode, ungeprüft live | ein `unified_search`-Lauf gegen die Testinstanz mit einem Talk-Treffer |
| Welche Talk- und Tables-Versionen laufen auf der Testinstanz | offen | `cloud/capabilities`, `spreed.features` und `tables.apiVersions` |
| Ist `rows/simple` (Titelzeile plus Werte) die billigere Zeilenform als `rows` plus Spalten | offen | beide einmal messen, Bytes und Runden vergleichen |

---

## Sources

**Codebasis, gelesen am 2026-08-21 (HIGH):** `src/mcp_connector/nextcloud/capabilities.py`, `nextcloud/clients/{ocs,deck,notes}.py`, `nextcloud/__init__.py`, `tools/{deck,notes,search,chatgpt,context}.py`, `server/__init__.py`, `server/reg_{deck,notes}.py`, `ids.py`, `provider_map.py`, `paging.py`, `deps.py`, `scripts/check_tool_budget.py`, `tests/contract/test_tool_surface.py`, `tests/contract/test_no_destructive_calls.py`, `tests/integration/test_exapp_dav_matrix.py`. Budget live gemessen mit `uv run python scripts/check_tool_budget.py` sowie einer Pro-Tool-Messung: 11268 Bytes, 16 Tools.

**Nextcloud Talk (HIGH):**
- [Conversations management, Talk API](https://nextcloud-talk.readthedocs.io/en/stable/conversation/) - `GET /ocs/v2.php/apps/spreed/api/v4/room`, Parameter, Antwortfelder
- [Chat management, Talk API](https://nextcloud-talk.readthedocs.io/en/stable/chat/) - `GET`/`POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}`, Vorgabewerte von `setReadMarker` und `markNotificationsAsRead`, Grenze 32000 Zeichen
- [Capabilities, Talk API](https://nextcloud-talk.readthedocs.io/en/stable/capabilities/) - Schlüssel `spreed`, `config.chat.max-length`
- Quellcode: `nextcloud/spreed` `lib/Search/{ConversationSearch,MessageSearch,CurrentMessageSearch}.php` (Provider-IDs `talk-conversations`, `talk-message`, `talk-message-current`; Eintrag mit `token`, `_fragment` `message_<id>`, `attributes.conversation`), `lib/Manager.php` (Token-Zeichensatz)

**Nextcloud Tables (HIGH):**
- [openapi.json der Tables-App](https://raw.githubusercontent.com/nextcloud/tables/main/openapi.json) - 47 Pfade, `api/1`- und `api/2`-Generationen, Body-Schema von `create-row`, Abwesenheit einer Zeilenleseroute unter `api/2`
- Quellcode: `lib/Capabilities.php` (`enabled`, `apiVersions`, `column_types`), `lib/Controller/Api1Controller.php` (`#[NoCSRFRequired]`, `#[CORS]`), `lib/AppInfo/Application.php` (`registerSearchProvider`, `registerCapability`), `lib/Search/SearchTablesProvider.php` (Provider-ID, Link mit ID im Fragment)
- [Tables API Wiki](https://github.com/nextcloud/tables/wiki/API) - Capabilities-Abruf per curl, `column_types` seit 0.5.0 (MEDIUM)

**Nextcloud Mail (MEDIUM bis HIGH je Zeile):**
- Quellcode: `appinfo/routes.php` (drei OCS-Routen plus `resources`-Block; kein Listing über OCS), `lib/Controller/MessageApiController.php` (`extends OCSController`, `get`, `getRaw`, `getAttachment`, `#[ApiRoute(verb: 'POST', url: '/message/send')]`), `lib/Controller/MessagesController.php` (`index(int $mailboxId, ...)`, `limit` auf 100 gekappt, kein `NoCSRFRequired`), `lib/Controller/MailboxesController.php` (`index(int $accountId, bool $forceSync = false)`), `lib/Controller/AccountsController.php` (`index` serialisiert die Kontokonfiguration), `lib/Search/{Provider,FilteringProvider}.php` (Provider-ID `mail`, Link `mail.deep_link.open`), `lib/AppInfo/Application.php` (keine `registerCapability`)
- [OCS API to send a message, nextcloud/mail#9450](https://github.com/nextcloud/mail/issues/9450) und [nextcloud/mail#3746](https://github.com/nextcloud/mail/issues/3746) - Belege dafür, dass `/api/messages` die Frontend-Route ist und die OCS-Fläche jung und klein ist

**Nextcloud Server (HIGH, Quellcode gelesen):**
- `lib/private/AppFramework/Http/Request.php` - `passesCSRFCheck()` gibt `true` bei gesetztem `OCS-APIRequest`-Header (Zeile 436), `cookieCheckRequired()` (Zeile 459)
- `lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php` - `isInvalidCSRFRequired()`, OCS-Ausnahme
- `core/Controller/NavigationController.php` - `#[ApiRoute(verb: 'GET', url: '/navigation/apps', root: '/core')]`, `#[NoAdminRequired]`, `list<CoreNavigationEntry>`, möglicher 304
- `nextcloud/notes` `lib/Controller/NotesApiController.php` und `nextcloud/deck` `lib/Controller/BoardApiController.php` - beide `#[NoCSRFRequired]` plus `#[CORS]`, womit Mail als Ausnahme belegt ist
- [OCS APIs overview, Developer Manual](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/OCS/ocs-api-overview.html) - Capabilities-Endpunkt; die App-Liste ist dort ausdrücklich **nicht** dokumentiert, weshalb `core/navigation/apps` als MEDIUM gilt, bis sie einmal live geantwortet hat

---
*Architecture research für: v1.2 Kuratierte Breite (Talk, Tables, Mail)*
*Researched: 2026-08-21*
