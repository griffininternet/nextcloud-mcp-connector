# Feature Research: v1.2 Talk, Tables, Mail

**Domain:** Kuratierte MCP-Tools fuer Nextcloud-Groupware (Chat, Tabellen, E-Mail) in einer bestehenden MCP-only-ExApp
**Researched:** 2026-08-21
**Confidence:** HIGH fuer die API-Lage (Quellcode und OpenAPI der drei Apps direkt geprueft), HIGH fuer den Wettbewerb (Tool-Listen direkt gelesen), MEDIUM fuer Nutzererwartung (Vendor-MCPs plus Wettbewerber als Proxy, keine eigenen Store-Rueckmeldungen)

> Die v1.0-Fassung dieser Datei (Gesamt-Feature-Landschaft des Produkts, 2026-08-14) steht in
> der Git-Historie unter Commit `29c5940`. Dieses Dokument betrachtet ausschliesslich die drei
> neuen Familien und die Aenderungen an `prepare_context` und am Budget-Gate.

## Ausgangslage in einem Satz

Alle drei Apps registrieren einen Unified-Search-Provider (`talk-message`, `talk-conversations`,
`mail`, `tables-search-tables`, verifiziert im Quellcode), also **liefert `unified_search` und damit
`prepare_context` heute schon Treffer aus Talk, Mail und Tables**, sobald die Apps installiert sind.
Die Luecke ist nicht die Suche, sondern **Navigation** (welche Konversationen, welche Tabellen,
welche Postfaecher gibt es), **Aufloesbarkeit** (Treffer sind derzeit `kind=url` und damit fuer
`fetch` toter Text) und **Zeilendaten** (Tabellen-Zeileninhalte werden von der Unified Search
ueberhaupt nicht indexiert). Das bestimmt den Schnitt unten.

## Feature Landscape

### Table Stakes (Users Expect These)

Fehlt eines davon, wirkt die Familie halb gebaut. Spalte "Familie" statt drei getrennter Tabellen,
weil die Roadmap ohnehin pro Familie schneidet.

| Familie | Feature | Why Expected | Complexity | Notes |
|---------|---------|--------------|------------|-------|
| Talk | Konversationen listen (Token, Name, Typ, Ungelesen-Zaehler, letzte Aktivitaet) | Ohne Liste kein Token, ohne Token kein Lesen und kein Senden. Beide Wettbewerber haben es (`nc_talk_*`, `list_talk_conversations`) | LOW | Genau ein Request: `GET /ocs/v2.php/apps/spreed/api/v4/room` liefert `token`, `displayName`, `type`, `unreadMessages`, `unreadMention`, `unreadMentionDirect`, `lastActivity`, `lastMessage`, `readOnly`, `permissions`, `isArchived`. `noStatusUpdate=1` mitschicken, sonst setzt das Lesen den Online-Status des Nutzers |
| Talk | Nachrichten einer Konversation lesen (Verlauf, nicht Polling) | Kernnutzen "worum ging es in dem Raum" | MEDIUM | `GET /chat/{token}` mit `lookIntoFuture=0`, `limit` (Default 100, Max 200), `lastKnownMessageId` als Offset. **Zwingend `setReadMarker=0`** (Default 1!) und `markNotificationsAsRead=0` (Default 1, nur mit Capability `chat-keep-notifications`), sonst ist ein Lesetool ein Schreibtool |
| Talk | Systemnachrichten und Platzhalter aufloesen | Rohantwort ist fuer ein Modell unlesbar: `message` enthaelt `{actor}`, `{mention-user1}` usw., die Werte stehen in `messageParameters`; `systemMessage` markiert Beitritte, Anrufe, Datei-Shares | MEDIUM | Platzhalter durch `@Name` ersetzen, Systemnachrichten per Default weglassen (spart Tokens und Rauschen), pro Nachricht harte Byte-Kappe (eine Nachricht darf 32.000 Zeichen haben) |
| Talk | Nachricht senden | Der eine Write, den diese Familie ueberhaupt sinnvoll macht ("sag Team X, dass...") | LOW-MEDIUM | `POST /chat/{token}` mit `message` (max 32.000 Zeichen). Vorher pruefen: `readOnly == 0` und Permission-Bit `128` ("can post chat message"), analog zum `can_edit` bei Deck. `replyTo` nur aus derselben Konversation erlaubt |
| Tables | Tabellen listen | Ohne Tabellen-Id kein Zugriff auf Spalten und Zeilen | LOW | `GET /ocs/v2.php/apps/tables/api/2/tables`. Antwort traegt `rowsCount`, `columnsCount`, `archived`, `favorite`, `isShared` und `onSharePermissions{read,create,update,delete,manage}`: letzteres ist das `can_edit`-Analogon fuer den Create |
| Tables | Spalten einer Tabelle lesen | Ohne Spaltenkenntnis ist eine Zeile nicht interpretierbar und nicht anlegbar | LOW | `GET /api/2/columns/{nodeType}/{nodeId}`. Rohantwort ist token-fett (ueber 30 Felder pro Spalte); projizieren auf `id`, `title`, `type`, `subtype`, `mandatory` und bei `selection` die Optionen |
| Tables | Zeilen lesen mit Paginierung | Der eigentliche Inhalt; die Unified Search indexiert Zeilen **nicht**, dieses Tool ist der einzige Weg | MEDIUM | Nur in API v1 vorhanden: `GET /index.php/apps/tables/api/1/tables/{tableId}/rows?limit&offset` (bzw. `/views/{viewId}/rows`). v2 hat **kein** Row-Read, nur Row-Create. v1 ist trotzdem dokumentiert (`OpenAPI SCOPE_DEFAULT`, `NoCSRFRequired`), also kein Internal-Route-Risiko wie bei Mail |
| Tables | Zeile anlegen | Der risikoarme Write dieser Familie ("trag das in die Urlaubsliste ein") | MEDIUM | `POST /ocs/v2.php/apps/tables/api/2/{nodeCollection}/{nodeId}/rows` mit `data` als Map `{"<columnId>": value}` (Controller castet die Keys nach int). Permission `create` wird serverseitig per Middleware erzwungen, also 403 statt stiller Nicht-Wirkung |
| Mail | Konten und Postfaecher listen | Ohne `mailboxId` gibt es keine Nachrichtenliste; ein Nutzer hat oft mehrere Konten | MEDIUM | Nur ueber die **internen** Routen `GET /index.php/apps/mail/api/accounts` und `GET /api/mailboxes?accountId=`. Mailbox-JSON traegt `databaseId`, `name`, `specialRole` (Inbox-Erkennung) und `unread` |
| Mail | Nachrichten eines Postfachs listen (Envelopes) | "Was liegt im Postfach" ist die Grundfrage der Familie | MEDIUM | `GET /api/messages?mailboxId=&limit=&cursor=&filter=`; `limit` wird serverseitig auf 100 geklemmt. Envelope liefert `databaseId`, `subject`, `from`, `dateInt`, `flags.seen`, `previewText`, teils `summary`: token-guenstig ohne Body |
| Mail | Eine Nachricht im Volltext lesen | Ohne Body ist die Familie nutzlos; genau das kann das offizielle context_agent **nicht** (es kann nur senden) | MEDIUM | `GET /ocs/v2.php/apps/mail/api/message/{id}` ist offizielle OCS-API (dokumentiert, `BruteForceProtection`). Achtung: `body` ist **HTML**, wenn die Mail HTML hat; IMAP-Roundtrip pro Aufruf, also eigenes Timeout-Budget wie beim Kalender |
| alle drei | App-Erkennung mit Graceful Degradation | Notes/Deck-Muster ist etabliert (SRV-04); ein Tool gegen eine fehlende App darf keinen Stacktrace und keine HTML-Loginseite produzieren | LOW (Talk, Tables) / MEDIUM (Mail) | Talk: Capability-Key `spreed`. Tables: Key `tables` mit `enabled`, `apiVersions`, `column_types`. **Mail hat keinen Capabilities-Eintrag** (keine `lib/Capabilities.php` im Repo): Erkennung ueber `GET /ocs/v2.php/core/navigation/apps` (nutzerbezogen, `NoAdminRequired`) und cachebar wie das bestehende Capabilities-Modul |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Mail strikt lesend, waehrend beide Wettbewerber senden | Google hat mit dem offiziellen Gmail-MCP genau diese Linie zum Standard gemacht: 9 Tools, Scopes `gmail.readonly` und `gmail.compose`, **kein Senden**, nur Entwurf. Unsere Position ist die konservativere Variante derselben Industrie-Norm, kein Feature-Rueckstand | LOW (Weglassen kostet nichts, es kostet nur Disziplin) | Nextcloud Mail **bietet** OCS-Senden an (`POST /apps/mail/api/message/send`, `UserRateLimit 5/100s`). Genau deshalb ist das Nicht-Anbieten eine bewusste, pruefbare Aussage (AST-Grep-Gate: kein Client-Code fuer diese Route) |
| Vertrauens-Signale aus Nextcloud mitliefern statt filtern | Die OCS-Message-Antwort enthaelt `isSenderTrusted`, `phishingDetails`, `hasDkimSignature`, `dkimValid`, `smime`. Diese als Datenfelder durchzureichen passt exakt zu D-57 ("fremder Text bleibt Daten") und ist etwas, das kein anderer Nextcloud-MCP tut | LOW | Kein eigenes Urteil bauen, nur Nextclouds Urteil weitergeben. Kostet ein paar Felder und macht Mail-Inhalte fuer das Modell als "fremd" erkennbar |
| Read ohne Nebenwirkung als messbare Eigenschaft | Talk-Lesen setzt per Default Leseeintrag und Online-Status und quittiert Benachrichtigungen. Ein Tool, das `setReadMarker=0`, `markNotificationsAsRead=0`, `noStatusUpdate=1`, `lookIntoFuture=0` setzt und das in einem Test festnagelt, ist ehrlich `readOnlyHint=true`. Der Wettbewerber hat dafuer sogar ein eigenes Schreib-Tool (`mark as read`) | LOW | Direkter Beleg fuer das Sicherheitsversprechen und eine Zeile Store-Text: "Lesen aendert in deiner Nextcloud nichts, auch nicht den Gelesen-Status" |
| Zeile anlegen mit Spaltentiteln statt Spalten-Ids | Der API-Weg verlangt `{"<columnId>": value}`. Modelle raten Ids und schreiben dann in die falsche Spalte (Issue nextcloud/tables#2237 zeigt, dass sogar Menschen das Format nicht finden). Titel annehmen, serverseitig auf Ids abbilden, bei unbekanntem oder mehrdeutigem Titel mit der Liste der gueltigen Titel ablehnen | MEDIUM (ein zusaetzlicher Columns-Request pro Create) | Gleiches Muster wie `deck_create_card`: ablehnen, was die API ablehnen wuerde, mit einem Hinweis, der den naechsten Aufruf richtig macht. Pflichtspalten (`mandatory`) vorab pruefen |
| Kompaktformat fuer Zeilen | `GET /api/1/tables/{id}/rows/simple` liefert erste Zeile Spaltentitel, danach reine Wertelisten. Gegenueber `data: [{columnId, value}, ...]` pro Zelle spart das grob die Haelfte der Antwort-Bytes | LOW | Als Default fuer den Rows-Level nutzen, `rows/simple` gibt es allerdings nur fuer Tabellen, nicht fuer Views |
| Talk-Digest in `prepare_context` aus **einem** Request | Die Konversationsliste traegt `unreadMessages`, `unreadMention`, `unreadMentionDirect` und `lastMessage` schon mit. "Wer hat mich erwaehnt und was liegt ungelesen" kostet also null zusaetzliche Roundtrips ueber die Liste hinaus, die das Talk-Tool sowieso braucht | LOW | Das ist der guenstigste Kontextgewinn des ganzen Meilensteins: eine Handvoll Zeilen Antwort fuer die Frage, die Nutzer morgens wirklich haben |
| Ein Browse-Tool pro Familie statt CRUD-Spiegelung | 5 neue Tools gegen 24 beim Community-Platzhirsch fuer dieselben drei Apps (Talk 6, Tables 5, Mail 13) und 24+ beim offiziellen context_agent (Tables allein 13, davon `delete_table` und `delete_column`) | LOW | Setzt das etablierte `deck_browse(level=...)`-Muster fort: eine Antwort-Huelle (`level`, `count`, `results`, `truncated`) pro Familie, ein Enum statt drei Tool-Slots |
| Konversation ausschliesslich per Token adressieren | context_agent loest Konversationen ueber `display_name` auf (`{conv.display_name: conv}[name]`). Zwei Raeume mit gleichem Namen, und die Nachricht geht in den falschen; ausserdem laesst sich ein Anzeigename aus fremdem Inhalt vorschlagen | LOW | Token kommt aus `talk_browse`, nie aus Text. Gleiche Disziplin wie bei Deck-Ids |

### Anti-Features (Commonly Requested, Often Problematic)

Explizit nicht bauen. Jede Zeile ist eine Absage an etwas, das mindestens ein Wettbewerber anbietet.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Mail senden** | Beide Wettbewerber haben es (`nc_mail_send_message`, context_agent `send_email`), Nextcloud bietet die OCS-Route an | Irreversibel, nach aussen wirksam, und im Verbund mit Mail-Lesen die klassische toedliche Kombination (private Daten + fremder Inhalt + Ausgangskanal). Google zieht beim eigenen Gmail-MCP genau hier die Grenze | Gar nicht. Falls spaeter Druck entsteht: `create draft` (interne Route `/api/drafts`), nie Senden |
| **Mail-Entwurf anlegen** | Wirkt harmlos und ist der Gmail-MCP-Kompromiss | In v1.2 nicht: es waere der erste Write in der sensibelsten Familie, laeuft nur ueber interne, ungetypte Routen und verwaessert die Aussage "Mail ist strikt lesend" | Vertagen bis Store-Feedback es verlangt; dann als eigener, klein geschnittener Requirement |
| **Mail-Flags, Tags, Verschieben, Loeschen, Als-gelesen-markieren** | Der Platzhirsch hat 6 solche Tools; "Assistent raeumt Postfach auf" klingt gut | Alles Zustandsaenderungen in fremden Systemen (IMAP), teils destruktiv (`delete_message`), und jede einzelne bricht die Aussage der Familie | Aufraeumen bleibt in der Mail-App. Das Modell darf lesen und zusammenfassen |
| **Mail-Anhaenge herunterladen** | "Lies mir die Rechnung im Anhang vor" | Binaerdaten in der Tool-Antwort (der Platzhirsch kappt bei 5 MB inline), Base64 sprengt jedes Token-Budget, plus Malware-Flaeche | Anhang-Metadaten (Name, Groesse, Typ) im Read ausgeben, Download-Link auf die Instanz. Datei-Anhaenge, die in Nextcloud liegen, kann `files_*` lesen |
| **Talk-Nachricht loeschen oder bearbeiten** | Talk erlaubt es (6 h Loeschfenster, 24 h Editierfenster) | Destruktiv beziehungsweise Geschichtsfaelschung in einem geteilten Raum; kollidiert frontal mit dem Versprechen | Nicht anbieten. Korrektur ist eine neue Nachricht |
| **Talk-Konversation anlegen** (context_agent kann `create_public_conversation`) | "Assistent eroeffnet Projektraum" | Erzeugt einen **oeffentlichen** Raum als Nebenwirkung eines Chatbefehls, laedt potenziell Gaeste ein, ist praktisch nicht rueckholbar ohne Loeschen (das wir nicht haben) | Raum in Talk anlegen, dann per `talk_browse` finden |
| **Reaktionen setzen, Teilnehmerlisten, Avatare, Anrufe, Umfragen, Threads** | Vollstaendigkeitsreflex; context_agent hat drei Reaktions-Tools | Jedes Tool kostet Budget-Bytes in jeder Session; Teilnehmerlisten sind zusaetzlich eine Personendaten-Ausleitung ohne konkreten Nutzen; Threads sind capability-abhaengig und noch in Bewegung | Weglassen. Threads erst, wenn ein Abnehmer sie nachweislich braucht |
| **`lookIntoFuture=1` (Long Polling auf neue Nachrichten)** | "Assistent hoert im Raum mit" | Blockiert bis 30 s (Max 60) pro Aufruf, laeuft in jedes Client-Timeout, erzeugt Dauerlast pro Session und ist mit stateless Tools nicht sinnvoll | Immer `lookIntoFuture=0`. Aktualitaet kommt vom naechsten Aufruf, Digest kommt aus der Konversationsliste |
| **Eigene Suchtools pro Familie (`talk_search`, `mail_search`, `tables_search`)** | Wirkt wie eine Luecke | Redundant: `unified_search` und `prepare_context` deckt Talk-Nachrichten, Talk-Konversationen, Mail-Nachrichten und Tabellen-/View-Namen schon ab, berechtigungstreu und provider-parallel. Mail parst den Suchbegriff sogar mit seiner eigenen Filtergrammatik (`is:unread from:alice subject:invoice`) | Drei Tool-Slots gespart. Statt neuer Suchtools die Provider-Zuordnung verbessern (siehe Dependencies) |
| **Tabellen-Schema aendern (Tabelle/Spalte anlegen, aendern, loeschen), Import, Shares** | context_agent hat genau das, inklusive `delete_table` und `delete_column` | Destruktiv im Wortsinn: eine geloeschte Spalte nimmt die Daten aller Zeilen mit. Import und Shares aendern Struktur beziehungsweise Berechtigungen | Nur `tables_browse` und `tables_create_row`. Struktur bleibt Menschenarbeit in der Tables-UI |
| **Zeile aktualisieren oder loeschen** | "Status auf fertig setzen" ist der haeufigste Wunsch nach Create | Update ist Ueberschreiben (Datenverlust ohne Historie), Delete ist destruktiv. Beides faellt unter das v1-Versprechen | Neue Zeile anlegen, Korrektur in der UI. Falls Update je kommt: eigener Meilenstein mit Confirmation-Flow |
| **Tabellen-Zeilen als CSV/Excel-Dump ohne Kappe** | "Gib mir die ganze Tabelle" | Tabellen mit 10.000 Zeilen sprengen jedes Kontextfenster; MCP-Antworten mit sechsstelligen Token-Zahlen sind ein dokumentiertes Feldproblem | `limit`/`offset` mit hartem Maximum, `truncated: true` benennen, `rowsCount` mitliefern, damit das Modell die Groesse kennt, bevor es liest |
| **Talk-Volltext-Verlauf ohne Kappe ("lies alles seit Januar")** | Zusammenfassungs-Wunsch | 200 Nachrichten mal bis 32.000 Zeichen ist ein Antwort-Groessen-Unfall; `limit` Default 100 ist fuer LLM-Nutzung zu hoch | Eigener Default deutlich unter dem API-Default (Vorschlag 20, Max 50), Byte-Kappe pro Nachricht, Paginierung ueber `lastKnownMessageId` |
| **`GET /chat/{token}/mentions` als "meine Erwaehnungen"** | Der Name legt es nahe | Der Endpunkt liefert **Autocomplete-Vorschlaege** fuer das Erwaehnen von Personen, nicht Erwaehnungen des Nutzers. Wer das verwechselt, baut ein Feature, das etwas anderes tut als sein Name sagt | Erwaehnungen kommen aus `unreadMention` und `unreadMentionDirect` der Konversationsliste |
| **Talk-Nachricht mit `@all` senden** | Bequem fuer Ankuendigungen | Ein Aufruf benachrichtigt alle Teilnehmer; im Zusammenspiel mit Prompt-Injection aus einer gelesenen Mail ist das ein Massen-Benachrichtigungshebel | `@all` und `@here` im Nachrichtentext ablehnen mit Hinweis "in Talk senden". Einzelne Erwaehnungen bleiben erlaubt |
| **`silent=true` als Default beim Senden** | "Stoert niemanden" | Eine Nachricht, die niemand mitbekommt, ist die schlechtere Ueberraschung: der Nutzer glaubt, er habe informiert | Normal senden. Kein `silent`-Parameter im Schema (Schema-Diaet) |
| **Semantische Suche / Vektorindex fuer Mail und Talk** | Der Platzhirsch hat es (Qdrant + Ollama, inklusive Mail) | Fremde Infrastruktur, Index-Drift gegen Berechtigungen, und ein Mail-Vektorindex ist eine Kopie der sensibelsten Daten neben der Nextcloud | Unified Search plus Mail-Filtergrammatik. Bleibt bei der v1.0-Entscheidung |
| **Credential-dependenter `tools/list`** ("Talk-Tools nur zeigen, wenn Talk da ist") | Wirkt sauber und spart Budget-Bytes | Bricht Caching, das Budget-Gate und Clients, die Tool-Listen persistieren; die etablierte Antwort ist der ehrliche Fehlersatz zur Laufzeit (SRV-04) | Statische Liste, `require_app`-Fehler mit einem konkreten naechsten Schritt |

## Vorgeschlagener Tool-Schnitt

Konkrete Formen, damit die Roadmap Phasen schneiden kann. Fuenf neue Tools, keine sechs.

| Tool | Annotation | Form | Familie |
|------|-----------|------|---------|
| `talk_browse` | READ_ONLY | `level="conversations"\|"messages"`, `token`, `limit`, `before_id` | Talk |
| `talk_send` | CREATE_ONLY | `token`, `message`, `reply_to?` | Talk |
| `tables_browse` | READ_ONLY | `level="tables"\|"columns"\|"rows"`, `table_id`, `view_id?`, `limit`, `offset` | Tables |
| `tables_create_row` | CREATE_ONLY | `table_id`, `values` (Objekt Spaltentitel zu Wert) | Tables |
| `mail_browse` | READ_ONLY | `level="accounts"\|"mailboxes"\|"messages"`, `account_id`, `mailbox_id`, `filter?`, `limit` | Mail |
| (kein neues Tool) | READ_ONLY | `fetch` um Praefix `mail:<databaseId>` erweitern | Mail |

Der letzte Punkt ist der wichtigste Sparposten: **Mail-Volltext braucht kein eigenes Tool.** `fetch`
loest heute `file:`, `note:`, `card:` und `url:` auf; `mail:<databaseId>` einzuhaengen kostet null
Budget-Bytes, nutzt die offizielle OCS-Route und faellt automatisch in die bestehende Byte-Kappe
plus Truncation-Markierung. Dieselbe Ueberlegung gilt fuer eine einzelne Talk-Nachricht: nicht
noetig, `talk_browse(level="messages")` deckt es ab.

**Budget-Rechnung** (aktuell 16 Tools, 11.268 von 12.500 Bytes, Schnitt 704 Bytes pro Tool): fuenf
Tools mit Enums und mehreren Parametern liegen erfahrungsgemaess bei 700 bis 900 Bytes, also grob
+4.000 Bytes auf etwa 15.300. Nach der bestehenden Regel (Messung plus 15 Prozent, aufgerundet auf
die naechsten 500) landet das Gate bei **17.500 bis 18.000 Bytes** mit einer neuen Messzeile im
Skript. Bei 21 Tools bleibt Abstand zur Cursor-Warnschwelle (40) und weit zur Abschaltgrenze (80).

## Feature Dependencies

```
talk_browse(level="conversations")
    └──requires──> Capability-Gate "spreed" (Capabilities-Modul, vorhanden)
    └──enables───> talk_browse(level="messages")   (Token)
    └──enables───> talk_send                        (Token + readOnly/Permission-Bit 128)
    └──enables───> prepare_context Talk-Digest      (dieselbe eine Antwort, keine Zusatzkosten)

tables_browse(level="tables")
    └──requires──> Capability-Gate "tables" (enabled, apiVersions, column_types)
    └──enables───> tables_browse(level="columns"|"rows")
    └──enables───> tables_create_row  (Spaltentitel zu columnId, onSharePermissions.create)

tables_create_row
    └──requires──> Columns-Read (Titel-Aufloesung, mandatory-Pruefung, selection-Optionen)

mail_browse(level="accounts")
    └──requires──> App-Erkennung ohne Capabilities:  GET /ocs/v2.php/core/navigation/apps
    └──requires──> Interne Routen erreichbar (OCS-APIRequest-Header umgeht CSRF; in AppAPI-Modus zu beweisen)
    └──enables───> mail_browse(level="mailboxes") ──> mail_browse(level="messages") ──> fetch("mail:<id>")

fetch  ──erweitert um──> mail:<databaseId>  (offizielle OCS-Route, HTML zu Text, Byte-Kappe)

unified_search / prepare_context ──deckt schon ab──> Talk-Nachrichten, Talk-Konversationen,
                                                     Mail-Nachrichten, Tabellen- und View-Namen
provider_map ──blockiert heute──> Aufloesbarkeit dieser Treffer (kind=url)

prepare_context Talk-Digest ──requires──> Talk-Konversationsliste (Client aus talk_browse)
prepare_context Mail-Ungelesen ──requires──> mail_browse-Client (accounts + mailboxes, 1+N Requests)

talk_send ──konfliktiert mit──> mail_browse + fetch("mail:...") in derselben Session
                                (private Daten + fremder Inhalt + Ausgangskanal)
```

### Dependency Notes

- **`provider_map` ist der billigste Hebel des Meilensteins.** `talk-message`-Treffer tragen bereits
  die Attribute `conversation` (Token), `messageId`, `threadId`, `actorType`, `actorId`, `timestamp`.
  Damit ist ein Talk-Treffer sauber adressierbar, ohne eine Id aus einer URL zu raten. Fuer
  `tables-search-tables` steckt die Id im **Fragment** (`.../apps/tables/#/table/7`), nicht im Pfad:
  die bestehende `_last_numeric_segment`-Logik findet sie nicht, das ist eine kleine, bewusste
  Ergaenzung. Fuer `mail` steht in der URL die **RFC-Message-Id** (`mail.deep_link.open`), nicht die
  numerische `databaseId`, die die OCS-Route braucht: Mail-Treffer bleiben also ehrlich `kind=url`,
  solange niemand die Deep-Link-Aufloesung beweist. Nicht versprechen, was nicht gemessen ist.
- **Mail haengt an internen Routen, Tables nicht.** Die Mail-Listen-Controller sind
  `#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`, koennen sich also zwischen Releases aendern; der
  Zugang funktioniert, weil `Request::passesCSRFCheck()` bei gesetztem Header `OCS-APIRequest`
  vorzeitig `true` liefert (im Server-Quellcode verifiziert). Die Tables-v1-Routen sind dagegen
  `SCOPE_DEFAULT` und `NoCSRFRequired`, also dokumentierte API. Konsequenz fuer die Roadmap: Mail
  braucht Integrationstests gegen eine echte Instanz (und den Beweis im **AppAPI-Modus**, nicht nur
  mit App-Passwort), Tables nicht.
- **Zwei Familien haben ein Permissions-Analogon zu Deck.** Talk: `readOnly` plus Bit `128`. Tables:
  `onSharePermissions.create`. Beides vor dem Write pruefen und mit der Liste der schreibbaren Ziele
  ablehnen, statt den Nutzer in ein 403 laufen zu lassen.
- **`prepare_context` bekommt keinen neuen Datenzugriff, sondern zwei bestehende Clients.** Reihenfolge
  in der Roadmap: Talk-Tools vor Talk-Digest, Mail-Tools vor Mail-Ungelesen. Der Digest ist ein
  Aufsatz, keine eigene Phase.

## MVP Definition

### Launch With (v1.2)

- [ ] `talk_browse` (zwei Level) mit nebenwirkungsfreiem Lesen: `setReadMarker=0`,
      `markNotificationsAsRead=0`, `noStatusUpdate=1`, `lookIntoFuture=0`, archivierte Konversationen
      heraus, Systemnachrichten per Default heraus, Platzhalter aufgeloest
- [ ] `talk_send` mit Vorpruefung (`readOnly`, Permission-Bit 128), `@all`/`@here`-Ablehnung,
      Laengenkappe 32.000 Zeichen, kein `silent`, kein Delete- oder Edit-Pfad im Client
- [ ] `tables_browse` (drei Level) mit projizierten Spalten, `rows/simple` als Default-Format,
      `limit`/`offset` und benannter Truncation
- [ ] `tables_create_row` mit Spaltentiteln statt Ids, Pflichtspalten-Pruefung und
      `onSharePermissions.create`-Vorpruefung
- [ ] `mail_browse` (drei Level), strikt lesend, mit `previewText` statt Body in der Liste
- [ ] `fetch` um `mail:<databaseId>` erweitert: offizielle OCS-Route, HTML zu Text, Byte-Kappe,
      Truncation-Marker, Vertrauens-Signale (`isSenderTrusted`, `phishingDetails`, DKIM) als Datenfelder
- [ ] App-Erkennung fuer alle drei Familien, Mail ueber `core/navigation/apps`, mit je einem
      Fehlersatz plus konkretem naechsten Schritt
- [ ] `prepare_context`: Talk-Digest (Konversationen mit `unreadMention`/`unreadMentionDirect` oder
      ungelesenen Nachrichten, Kappe 3, `lastMessage`-Vorschau hart gekappt), eigenes Zeit-Budget,
      eigener `degraded`-Eintrag
- [ ] Budget-Gate angehoben mit neuer Messzeile, Schema-Diaet fuer alle fuenf Tools, Annotationen
      ehrlich (drei READ_ONLY, zwei CREATE_ONLY)
- [ ] Sicherheitsdoku: ein Abschnitt, der Mail-und-Talk-Inhalte als fremde Daten benennt und die
      Kombination Lesen plus Senden ausdruecklich adressiert

### Add After Validation (v1.x)

- [ ] `prepare_context` Mail-Ungelesen (nur Zaehler, keine Betreffs): Trigger, wenn `mail_browse`
      stabil ist und die 1+N-Requests gemessen sind
- [ ] `provider_map`-Eintraege fuer `talk-message` (Attribute) und `tables-search-tables` (Fragment):
      Trigger, sobald an einer echten Instanz gemessen; hebt Treffer aus `kind=url`
- [ ] Mail-Filtergrammatik als eigener Parameter dokumentieren (`is:unread`, `from:`, `subject:`,
      `start:`, `tags:`): Trigger, wenn Nutzer nach Filtern fragen
- [ ] Talk-Thread-Unterstuetzung (capability-gated): Trigger, wenn ein Abnehmer Threads nutzt
- [ ] Mail-Entwuerfe (`create draft`, nie Senden): Trigger, wenn Store-Feedback es verlangt; Vorbild
      ist der offizielle Gmail-MCP

### Future Consideration (v2+)

- [ ] Schreibende Mail-Operationen jeder Art: nur mit Elicitation/Confirmation-Infrastruktur, also
      frueestens wenn destruktive Ops ueberhaupt konzeptionell erlaubt werden
- [ ] Zeilen-Update mit Confirmation, Tabellen-Schema-Operationen: eigener Meilenstein, nicht hier
- [ ] Talk-Reaktionen, Umfragen, Teilnehmerverwaltung: Breite, die der Platzhirsch besetzt
- [ ] openDesk-Nachbarn (OX-Mail, Matrix) statt Nextcloud-Mail/Talk: Phase 3

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `talk_browse` (Konversationen + Nachrichten) | HIGH | MEDIUM | P1 |
| `talk_send` | HIGH | LOW | P1 |
| `tables_browse` (Tabellen, Spalten, Zeilen) | HIGH | MEDIUM | P1 |
| `tables_create_row` (Titel statt Ids) | MEDIUM | MEDIUM | P1 |
| `mail_browse` (Konten, Postfaecher, Envelopes) | HIGH | MEDIUM-HIGH | P1 |
| `fetch`-Erweiterung `mail:<id>` | HIGH | MEDIUM | P1 |
| App-Erkennung, Mail ueber `navigation/apps` | MEDIUM | LOW-MEDIUM | P1 |
| `prepare_context` Talk-Digest | HIGH | LOW | P1 |
| Budget-Gate plus Schema-Diaet | MEDIUM | LOW | P1 |
| Nebenwirkungsfreies Talk-Lesen als Test festgenagelt | HIGH | LOW | P1 |
| Vertrauens-Signale in der Mail-Antwort | MEDIUM | LOW | P2 |
| `provider_map` fuer `talk-message` und Tables-Fragment | MEDIUM | LOW | P2 |
| `prepare_context` Mail-Ungelesen (nur Zaehler) | MEDIUM | MEDIUM | P2 |
| Mail-Filtergrammatik dokumentiert und getestet | MEDIUM | LOW | P2 |
| Talk-Threads | LOW | MEDIUM | P3 |
| Mail-Entwuerfe | LOW | MEDIUM | P3 |

## Competitor Feature Analysis

| Aspekt | nextcloud/context_agent (offiziell) | cbcoutinho/nextcloud-mcp-server (332 Sterne, aktiv) | Offizielle Vendor-MCPs (Referenzpunkt) | Unser Ansatz |
|--------|-------------------------------------|-----------------------------------------------------|----------------------------------------|--------------|
| Talk | `list_talk_conversations`, `create_public_conversation`, `send_message_to_conversation` (per **Anzeigename**), `list_messages_in_conversation`, `add_reaction`, `remove_reaction`, `list_reactions` | 6 Tools: Konversationen listen, lesen, posten, als gelesen markieren, Teilnehmer listen | Slack-MCP (offiziell): 14 bis 15 Tools, Suche/Lesen/Threads getrennt, plus Senden und Draft | 2 Tools: `talk_browse` (Level-Enum) plus `talk_send`, Adressierung nur per Token, kein Reaktions-, Raum- oder Markieren-Pfad |
| Tables | 13 Tools inklusive `delete_table`, `delete_column`, `update_row`, `delete_row`; `create_row(data: str)` als JSON-String | 5 Tools: listen, Schema, lesen, `insert_row`, `update_row`, `delete_row` | (kein Vendor-Pendant) | 2 Tools: `tables_browse` (Level-Enum) plus `tables_create_row` mit Spaltentiteln; kein Update, kein Delete, keine Schema-Aenderung |
| Mail | 4 Tools, davon **`send_email`**, aber **kein** Volltext-Lesen | 13 Tools inklusive `send_message`, `set_flags`, `move_message`, `delete_message`, Tags, Anhaenge | Gmail-MCP (Google, Developer Preview): 9 Tools, Scopes `gmail.readonly` plus `gmail.compose`, **kein Senden**, nur `create_draft` | 1 Tool plus `fetch`-Praefix, strikt lesend: listen und lesen, sonst nichts. Naeher an Googles Linie als beide Nextcloud-Wettbewerber |
| Summe fuer diese drei Familien | 24+ Tools, destruktiv und nach aussen wirksam | 24 Tools, destruktiv und nach aussen wirksam | Gmail 9, Slack 14 bis 15 pro **einer** Familie | **5 neue Tools**, 21 gesamt, zwei nicht-destruktive Writes |
| Lesen mit Nebenwirkung | Nicht adressiert | Eigenes `mark as read`-Tool, Leseeintrag beim Lesen nicht dokumentiert | Slack liest ueber eigene Scopes | Lesen setzt weder Leseeintrag noch Online-Status noch quittiert Benachrichtigungen, per Test festgenagelt |
| Internal-API-Risiko Mail | nutzt py-nextcloud-Bibliothek ueber dieselben internen Routen | benannt und per GreenMail-Integrationstest abgesichert (vorbildlich dokumentiert) | (entfaellt) | Gleiche Lage, gleiche Antwort: Integrationstest plus AppAPI-Modus-Beweis, Risiko im Requirement benannt |

## Response-Groessen-Leitplanken (fuer die Phasenplanung)

Der Meilenstein steht und faellt mit Antwort-Groessen, nicht mit Endpunkten. Konkrete Werte als
Ausgangspunkt, alle in der bestehenden `degraded`/`truncated`-Sprache benannt:

| Antwort | API-Default | Vorschlag | Begruendung |
|---------|-------------|-----------|-------------|
| Talk-Nachrichten pro Aufruf | `limit=100`, Max 200 | Default 20, Max 50 | Eine Nachricht darf 32.000 Zeichen haben |
| Talk-Nachrichtentext | unbegrenzt | Byte-Kappe pro Nachricht plus Marker | gleiche Mechanik wie `EXCERPT_MAX_BYTES` |
| Talk-Konversationen | alle | Max 50, archivierte heraus | Instanzen mit dreistelligen Raumzahlen |
| Tables-Zeilen | `limit`/`offset` frei | Default 25, Max 200, `rowsCount` mitliefern | Tabellen sind unbegrenzt gross |
| Mail-Envelopes | serverseitig auf 100 geklemmt | Default 20, Max 50, `previewText` gekappt | Envelope-Objekt ist feldreich |
| Mail-Volltext | ganzer HTML-Body | bestehende `fetch`-Byte-Kappe, HTML zu Text | HTML-Mails sind Vielfache des Textinhalts |
| `prepare_context` Talk-Digest | (neu) | Max 3 Eintraege, nur Konversationen mit Erwaehnung oder Ungelesenem, `lastMessage`-Vorschau ~200 Zeichen | grob 400 bis 600 Bytes, damit bleibt das Buendel vorhersagbar |
| `prepare_context` Mail | (neu, P2) | nur Zaehler, keine Betreffs | rund 100 Bytes, kein Inhalt aus fremder Hand im Standardbuendel |

## Sources

- nextcloud/spreed `docs/chat.md` und `docs/conversation.md` sowie `nextcloud-talk.readthedocs.io`
  (Endpunkte, Parameter-Defaults `setReadMarker=1`, `markNotificationsAsRead=1`, `limit=100/200`,
  32.000-Zeichen-Grenze, Statuscodes 403/412/413/429, Room-Felder `unreadMention`,
  `unreadMentionDirect`, `lastMessage`, `isArchived`) [HIGH]
- nextcloud/spreed `docs/constants.md` (Konversationstypen inklusive 6 = Note to self, `readOnly`,
  Permission-Bit 128 "can post chat message and share items") [HIGH]
- nextcloud/spreed `lib/Capabilities.php` (Feature-Flags `chat-keep-notifications`, `chat-permission`,
  `note-to-self`, `archived-conversations-v2`, `markdown-messages`, `sensitive-conversations`) [HIGH]
- nextcloud/spreed `lib/Search/MessageSearch.php`, `lib/Search/ConversationSearch.php`
  (Provider-Ids `talk-message`, `talk-conversations`; Attribute `conversation`, `messageId`,
  `threadId`, `actorType`, `actorId`, `timestamp`) [HIGH]
- nextcloud/tables `openapi.json` (v1 hat Row-Read mit `limit`/`offset` und `rows/simple`, v2 hat nur
  Row-Create; `Row.data` als `columnId`/`value`; `Table.onSharePermissions`, `rowsCount`,
  `columnsCount`, `archived`) [HIGH]
- nextcloud/tables `lib/Controller/RowOCSController.php` (Create-Format `{"<columnId>": value}`,
  `RequirePermission(PERMISSION_CREATE)`), `lib/Controller/Api1Controller.php`
  (`NoCSRFRequired`, `CORS`, `OpenAPI SCOPE_DEFAULT`, also dokumentierte API),
  `lib/Capabilities.php` (`tables.enabled`, `apiVersions`, `column_types`),
  `lib/Search/SearchTablesProvider.php` (Provider-Id `tables-search-tables`, Id im URL-Fragment) [HIGH]
- github.com/nextcloud/tables/issues/2237 (Row-Create-Format war selbst fuer Menschen schwer zu
  finden: Begruendung fuer Spaltentitel statt Ids) [MEDIUM]
- nextcloud/mail `appinfo/routes.php` (OCS-Oberflaeche umfasst nur `message/{id}`, `message/{id}/raw`,
  `message/{id}/attachment/{attachmentId}`; alles andere sind interne `/api/...`-Routen),
  `lib/Controller/MessageApiController.php` (`POST /message/send` mit `UserRateLimit 5/100s`;
  `get()` liefert Volltext plus `isSenderTrusted`, `phishingDetails`, DKIM, S/MIME),
  `lib/Controller/MessagesController.php` und `MailboxesController.php`
  (`#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`, `index(mailboxId, cursor, filter, limit)`,
  `limit` auf 100 geklemmt), `lib/Db/Message.php` und `lib/Db/Mailbox.php` (`databaseId`,
  `previewText`, `summary`, `flags`, `unread`, `specialRole`), `lib/Model/IMAPMessage.php`
  (`body` ist HTML, wenn HTML-Teil vorhanden), `lib/Search/Provider.php` (Provider-Id `mail`,
  Suchbegriff wird als Mail-Filtergrammatik geparst, Deep-Link traegt die RFC-Message-Id) [HIGH]
- nextcloud/mail hat **keine** `lib/Capabilities.php` (404 im Repo), daher Erkennung ueber
  nextcloud/server `core/Controller/NavigationController.php`
  (`ApiRoute GET /core/navigation/apps`, `NoAdminRequired`) [HIGH]
- nextcloud/server `lib/private/AppFramework/Http/Request.php`, `passesCSRFCheck()`
  (Header `OCS-APIRequest` gesetzt bedeutet CSRF-Pruefung bestanden: der Zugang zu den internen
  Mail-Routen mit App-Passwort) [HIGH]
- cbcoutinho/nextcloud-mcp-server README plus `docs/mail.md`, `docs/table.md` (110+ Tools; Talk 6,
  Tables 5, Mail 13; Mail-Filtergrammatik; eigene Notiz, dass die internen Mail-Routen
  `SCOPE_IGNORE` sind und per Integrationstest abgesichert werden) [HIGH]
- nextcloud/context_agent `ex_app/lib/all_tools/{talk,tables,mail}.py` (Talk 7 Tools inklusive
  `create_public_conversation` und Adressierung per Anzeigename; Tables 13 Tools inklusive
  `delete_table`, `delete_column`, `update_row`, `delete_row`; Mail 4 Tools inklusive `send_email`,
  ohne Volltext-Lesen) [HIGH]
- developers.google.com Gmail-MCP-Konfiguration (offizieller Gmail-MCP: 9 Tools, Scopes
  `gmail.readonly` plus `gmail.compose`, kann **nicht** senden, nur `create_draft`) [HIGH]
- docs.slack.dev Slack-MCP-Server (14 bis 15 Tools fuer eine Familie, Trennung Suche/Lesen/Thread,
  Senden und Draft getrennt, Scope pro Tool) [MEDIUM-HIGH]
- Wiz "Model Context Protocol Security" und modelcontextprotocol-Discussion 2211
  (toedliche Kombination aus privaten Daten, fremdem Inhalt und Ausgangskanal; Antwortgroessen
  jenseits der Kontextfenster als dokumentiertes Feldproblem) [MEDIUM]
- Interne Referenz: `scripts/check_tool_budget.py` (16 Tools, 11.268 von 12.500 Bytes, Regel
  Messung plus 15 Prozent auf die naechsten 500), `src/mcp_connector/tools/deck.py` (Browse-Level-
  Muster), `src/mcp_connector/tools/context.py` (Kappen, `degraded`, Budget pro Quelle),
  `src/mcp_connector/provider_map.py` (Kind-Zuordnung und `resolvable=false`) [HIGH, eigener Code]

---
*Feature research for: v1.2 Talk, Tables, Mail in einer kuratierten Nextcloud-MCP-ExApp*
*Researched: 2026-08-21*
</content>
</invoke>
