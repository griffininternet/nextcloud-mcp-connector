# Stack Research

**Domain:** Nextcloud MCP-only ExApp, Milestone v1.2 "Kuratierte Breite" (Talk, Tables, Mail)
**Researched:** 2026-08-21
**Confidence:** HIGH für Endpunkte, Parameter und den Auth-/CSRF-Mechanismus (alle gegen den
Quelltext der jeweiligen App und gegen `nextcloud/server` stable32/33/34 gelesen).
MEDIUM für die Mail-Mindestversion und für die App-Erkennung von Mail (Route im Quelltext
verifiziert, aber noch nicht gegen eine laufende Instanz gemessen).

**Diese Datei ersetzt die v1.0-Stack-Recherche vom 2026-08-14.** Der dort entschiedene Stack
(Python 3.13, mcp>=2.0,<3, httpx, lxml, uv, AppAPI/HaRP) wird nicht angetastet und hier nicht
erneut begründet. Es geht ausschliesslich um die drei neuen Familien.

---

## Antwort in einem Satz

**Es kommt keine einzige neue Python-Abhängigkeit dazu.** Talk, Tables und Mail sind
durchgängig JSON über HTTP, alle drei laufen unter AppAPI-Impersonation ohne neuen Auth-Pfad
und ohne Scope-Deklaration, und die beiden Parser, die das Projekt schon hat
(`ocs.parse_ocs` für den OCS-Envelope, `ocs.parse_app_json` für nackte App-Routen), decken
jede der neun benötigten Antworten ab. Die einzige echte Erweiterung der Client-Schicht ist
ein `ocs_post` neben dem vorhandenen `ocs_get`.

---

## Recommended Stack

### Core Technologies

Unverändert. Keine Zeile in `[project.dependencies]` ändert sich.

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| httpx | >=0.28,<0.29 (schon drin) | Einziger HTTP-Client für Talk-OCS, Tables-OCS + Tables-v1, Mail-OCS + Mail-App-Routen | Alle drei Familien sind JSON über HTTP. Kein XML, kein DAV, kein IMAP. Der vorhandene `AppApiAuth` signiert jede dieser Requests unverändert (HIGH) |
| lxml | >=6.1,<7 (schon drin) | Nur ein Zweck neu: Text aus einem HTML-Mail-Body ziehen | Mail liefert `body` als sanitisiertes HTML, sobald die Nachricht einen HTML-Teil hat. `lxml.html.fromstring(...).text_content()` erledigt das mit einer Abhängigkeit, die längst im Lock steht, und verhindert damit genau den Dependency-Zukauf, den dieses Feld sonst provoziert (HIGH) |
| mcp[cli] | >=2.0,<3 (schon drin) | Tool-Registrierung der drei neuen Familien | Keine Änderung; die neuen Tools sind gewöhnliche freistehende Funktionen wie deck/notes (HIGH) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (keine) | - | - | - |

Bewusst leer. Die drei Kandidaten, die man in dieser Domäne reflexartig zieht, sind unten in
"What NOT to Use" mit Begründung abgelehnt.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| respx (schon im dev-group) | Contract-Tests je Endpunkt ohne Netz | Neun neue Endpunkte, jeder mit Happy/4xx/5xx/HTML-Login/no_data. Reicht für die gesamte Client-Schicht |
| Docker-Test-Nextcloud (`-m integration`) | Talk + Tables + Mail installieren und einmal wirklich messen | Talk und Tables sind per `occ app:install` reproduzierbar. Mail braucht einen IMAP-Server: **GreenMail** als zweiter Compose-Service ist der etablierte Weg (der Community-Server fährt genau das) |
| Bestehendes AST-Grep-Gate | Hält die Write-Grenze | Muss um die neuen Verben erweitert werden, siehe "Integration" unten |

---

## Die drei Familien im Detail

### 1. Talk (App-Id `spreed`): reines OCS, eine API-Generation je Zweck

Basis: `/ocs/v2.php/apps/spreed/api/...`, Envelope `ocs.meta` + `ocs.data`, also
`ocs.parse_ocs` unverändert.

| Zweck | Methode + Pfad | Wichtige Parameter |
|-------|----------------|--------------------|
| Konversationen lesen | `GET /ocs/v2.php/apps/spreed/api/v4/room` | `noStatusUpdate=1`, `includeStatus=false`, `includeLastMessage=true` (Default), `modifiedSince` |
| Eine Konversation | `GET /ocs/v2.php/apps/spreed/api/v4/room/{token}` | - |
| Nachrichten lesen | `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | **`lookIntoFuture=0` (Pflicht)**, `limit` (Default 100, Max 200), `lastKnownMessageId`, `includeLastKnown`, `setReadMarker=0`, `markNotificationsAsRead=0`, `noStatusUpdate=1` |
| Nachricht senden | `POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | `message`, optional `replyTo`, `silent`, `referenceId`. Antwort **201** |

**Die API-Version ist keine Verhandlungssache.** Die Routen sind in `ChatController` und
`RoomController` per `#[ApiRoute(... requirements: ['apiVersion' => '(v4)'])]` bzw. `'(v1)'`
fest verdrahtet. `v4` für Räume, `v1` für Chat, hart einsetzen, nichts aushandeln.

**Der wichtigste Befund für das Sicherheitsversprechen:** `lookIntoFuture=0` ist
konstruktionsbedingt nebenwirkungsfrei, und zwar an drei Stellen gleichzeitig, alle im
Quelltext von `ChatController::receiveMessages` nachlesbar:

- der Lesemarker wird nur unter `if ($lookIntoFuture && $setReadMarker === 1 && ...)`
  fortgeschrieben
- `markNotificationsAsRead` wird ausschliesslich an `waitForNewMessages` übergeben, also nur
  im Zukunfts-Zweig; der History-Zweig ruft `getHistory` ohne dieses Argument
- das Status-Update hängt an `if ($noStatusUpdate === 0 && $session instanceof Session)`,
  und eine Talk-Session hat nur, wer den Raum in einem Client betreten hat, nie ein reiner
  API-Aufruf

Trotzdem `setReadMarker=0`, `markNotificationsAsRead=0` und `noStatusUpdate=1` explizit
mitsenden: die Defaults sind `1`, `1`, `0`, und eine Talk-Version, die die Gates umbaut, darf
dieses Projekt nicht überraschen. Die Parameter sind hier die Dokumentation der Absicht.

**Fähigkeitserkennung:** `capabilities.spreed` existiert (`lib/Capabilities.php`, Rückgabe
`['spreed' => $capabilities]`). Nutzbar:

- `features` enthält `conversation-v4`, `chat-v2`, `chat-reference-id`, `silent-send`,
  `markdown-messages`, `unified-search`
- `config.chat.max-length` = `ChatManager::MAX_CHAT_LENGTH` = **32000**. Das ist die
  Längengrenze, die der lokale Guard vor dem Senden prüfen soll, analog zu Decks 255
- `config.conversations.can-create` ist das Gegenstück zu Decks `canCreateBoards`
- Sonderfall: ist Talk für den Nutzer administrativ deaktiviert, gibt
  `getCapabilities()` ein **leeres Array** zurück. `spreed` fehlt dann ganz, also greift
  dieselbe Prüfung wie bei Notes und Deck, ohne Extraweg

**Token-Guard:** Die Routen-Requirement ist `[a-z0-9]{4,30}`. Ein Token kommt immer von der
Gegenseite, geht in den Pfad und `httpx` normalisiert `..` nicht. Also derselbe lokale Guard
wie `deck._path_id`, nur mit diesem Muster.

**Versionslage:** spreed 22.x (NC 32), 23.x (NC 33), 24.x (NC 34). Alle drei tragen
`conversation-v4` und Chat v1; die Endpunkte sind in dieser Spanne stabil. Kein
Versions-Gate nötig, das Capability-Gate genügt.

**Sonstiges:** Der Chat-GET kann `304` antworten (keine neuen Nachrichten), was kein Fehler
ist und im Transport-Check nicht als Redirect enden darf. Der Antwortheader
`X-Nextcloud-Talk-Hash` signalisiert geänderte Capabilities; für uns nur ein Hinweis, den
60-Sekunden-Cache nicht zu verlängern.

### 2. Tables: gespaltene API, und die Spaltung liegt genau auf unserer Bruchkante

Das ist der Befund, der die Planung am stärksten betrifft:

> **Die Tables-v2-OCS-API kann Zeilen anlegen, aber nicht lesen.** In `appinfo/routes.php`
> steht unter `'ocs'` genau eine Zeilen-Route: `RowOCS#createRow`. Es gibt kein
> `GET /api/2/.../rows`. Zeilen lesen geht ausschliesslich über die v1-App-Route.

Daraus folgt zwingend ein gemischter Client:

| Zweck | Methode + Pfad | Parser |
|-------|----------------|--------|
| Tabellen auflisten | `GET /ocs/v2.php/apps/tables/api/2/tables` | `parse_ocs` |
| Eine Tabelle | `GET /ocs/v2.php/apps/tables/api/2/tables/{id}` | `parse_ocs` |
| Spalten | `GET /ocs/v2.php/apps/tables/api/2/columns/{nodeType}/{nodeId}` | `parse_ocs` |
| Views einer Tabelle | `GET /index.php/apps/tables/api/1/tables/{tableId}/views` | `parse_app_json` |
| **Zeilen lesen** | `GET /index.php/apps/tables/api/1/tables/{tableId}/rows?limit=&offset=` | `parse_app_json` |
| Zeilen einer View | `GET /index.php/apps/tables/api/1/views/{viewId}/rows?limit=&offset=` | `parse_app_json` |
| **Zeile anlegen** | `POST /ocs/v2.php/apps/tables/api/2/{tables\|views}/{nodeId}/rows` | `parse_ocs` |

Drei Fallen, alle im Quelltext belegt:

1. **`nodeType` wird zweimal unterschiedlich geschrieben.** Bei `columns` ist es die
   **Zahl** aus `Application`: `0` = Tabelle, `1` = View, Requirement `(\d+)`. Bei
   `createRow` ist es das **Wort** `tables` oder `views`, Requirement `(tables|views)`.
   Wer das verwechselt, bekommt einen 404 von der Routing-Schicht, nicht von der App.
2. **Der Body von `createRow` ist ein Objekt, keine Liste.** Korrekt ist
   `{"data": {"<columnId>": <value>, ...}}`; `RowOCSController::createRow` läuft
   `foreach ($data as $key => $value)` und castet den Schlüssel nach `int`. Die naheliegende
   Übernahme der v1-GET-Form (`[{"columnId": 1, "value": "x"}]`) endet in
   `Column with id 0 is not part of table` (nextcloud/tables#2237, die Doku war hier
   irreführend).
3. **`createRow` antwortet `200`, nicht `201`.** `DataResponse` ohne Statusargument. Ein
   Contract-Test, der auf 201 prüft, ist rot gegen eine korrekt arbeitende Instanz.

**`limit`/`offset` statt Cursor.** Die v1-Zeilen-Routen nehmen `?limit=&offset=`, was
`paging.encode_cursor` direkt bedient. Kein Sonderfall.

**Kein `Origin`-Header senden.** Alle v1-Routen tragen `#[CORS]`. Die `CORSMiddleware` von
Nextcloud wird erst aktiv, wenn ein `Origin` im Request steht, und verlangt dann eine
Basic-Reauthentifizierung, die unter AppAPI-Impersonation nicht existiert. Ohne `Origin`
ist die Middleware ein No-op. Der bestehende Client sendet keinen, das muss so bleiben.

**Fähigkeitserkennung:** `capabilities.tables` existiert (`lib/Capabilities.php`) mit
`enabled`, `version`, `apiVersions`, `features`, `column_types`. Sauberes Gate:
`"1.0"` in `apiVersions` für den Lesepfad, `"2.0"` für den Create-Pfad. Beides ist in jeder
relevanten Version vorhanden (v0.9.11, v1.0.9, v2.1.1 und main melden alle
`["1.0","2.0","2.1"]`). `column_types` ist ausserdem das, was die Werte-Validierung vor dem
Create braucht, ohne dafür raten zu müssen.

**Versionslage, die eine Rolle spielt:** Tables 2.2.x verlangt NC >= 33, Tables 2.1.x
NC 33-34, Tables 1.0.x NC 30-32. Auf einer NC 32 läuft also Tables 1.0/0.9, auf 33/34 die
2.x-Linie. Die OCS-Create-Route existiert seit **Tables 0.8.0**, liegt damit unter allem, was
in der unterstützten NC-Spanne installierbar ist. Deshalb: **kein Versions-Gate, nur das
Capability-Gate.** Ein Gate auf `version` würde die 1.0-Linie auf NC 32 falsch aussperren.

### 3. Mail: die heikelste Familie, und die mit dem interessantesten Mechanismus

**Mail veröffentlicht keine Capability.** In `nextcloud/mail/lib` existiert keine
`Capabilities.php`, und `appinfo/info.xml` registriert keine. `/cloud/capabilities` kann Mail
also nicht erkennen. Das ist der einzige Punkt, an dem v1.2 ein neues Erkennungsmuster
braucht.

**Empfohlene Erkennung:** `GET /ocs/v2.php/core/navigation/apps`. Die Route liegt in
`core/Controller/NavigationController.php` als `#[ApiRoute(verb: 'GET', url:
'/navigation/apps', root: '/core')]` mit `#[NoAdminRequired]` und `#[NoCSRFRequired]`, ist
also nutzergebunden und nicht Admin-only, und ihr `OCSController`-Envelope passt in
`parse_ocs`. Sie liefert die Apps, die dieser Nutzer im Navigationsmenü hat, was exakt die
gewünschte Semantik ist ("für diesen Nutzer freigeschaltet"), inklusive `id: "mail"`. Als
zweites, bestätigendes Signal steht ohnehin schon etwas bereit: der Unified-Search-Provider
von Mail heisst `mail` (`lib/Search/Provider.php` gibt `Application::APP_ID` zurück), und
`ocs.list_search_providers` wird bereits pro Aufruf gelesen.

Empfehlung: eine `Capabilities`-Erweiterung mit einem zweiten Roundtrip auf
`/core/navigation/apps`, im gleichen 60-Sekunden-Cache, weil derselbe Aufruf auch Talk
(`spreed`) und Tables (`tables`) gegenprüft und damit alle drei Familien mit einer
Erkennungslogik bedient.

**Die Lese-Endpunkte:**

| Zweck | Methode + Pfad | Parser |
|-------|----------------|--------|
| Konten | `GET /index.php/apps/mail/api/accounts` | `parse_app_json` |
| Postfächer | `GET /index.php/apps/mail/api/mailboxes?accountId={id}` | `parse_app_json` |
| Nachrichtenliste | `GET /index.php/apps/mail/api/messages?mailboxId={id}&cursor=&limit=&filter=&view=` | `parse_app_json` |
| Eine Nachricht inkl. Body | `GET /ocs/v2.php/apps/mail/message/{id}` | `parse_ocs` |

**Der Mechanismus, der das überhaupt erlaubt, und warum er belastbar ist.** Mails interne
API-Controller sind gewöhnliche `Controller` (kein `OCSController`), und
`AccountsController::index`, `MailboxesController::index`, `MessagesController::index` und
`MessagesController::getBody` tragen **nur** `@NoAdminRequired`, **kein**
`@NoCSRFRequired`. Erreichbar sind sie trotzdem, wegen genau dieser Stelle in
`OC\AppFramework\Http\Request::passesCSRFCheck()`:

```php
if ($this->getHeader('OCS-APIRequest') !== '') {
    return true;
}
```

Der Header hebt die CSRF-Pflicht also für **jeden** Controller auf, nicht nur für
`OCSController`. Zusätzlich macht `cookieCheckRequired()` mit demselben Header den
Strict-Cookie-Check zum No-op. Verifiziert in `stable32`, `stable33`, `stable34` und `master`
mit identischem Code. Das ist übrigens auch die Erklärung, warum D-18 dieses Projekt seit
Phase 1 richtig trägt: der Header ist bei Notes und Deck nicht Kosmetik, sondern der
tragende Grund. Der Community-Server dokumentiert denselben Befund als gegen ein laufendes
Mail 5.x gemessen, was eine unabhängige Bestätigung ist.

**`body` kann HTML sein.** `IMAPMessage::getFullMessage()` setzt `body` auf
`getHtmlBody($id)`, sobald die Nachricht einen HTML-Teil hat (`hasHtmlBody: true`), sonst auf
den durch `parseMailBody` gelaufenen Klartext. Für ein Tool mit Byte-Budget heisst das:
HTML-Bodies müssen zu Text reduziert werden. Der Weg ohne neue Abhängigkeit ist
`lxml.html.fromstring(body).text_content()`. **Nicht** `lxml.html.clean` verwenden: das ist
seit lxml 5.2 in das separate Paket `lxml_html_clean` ausgezogen und wäre wieder ein Zukauf.

**Frische:** Die Nachrichtenliste liest den lokalen DB-Cache (`mailSearch->findMessages`),
nicht IMAP. Die Einzelnachricht dagegen geht live an IMAP. Die Liste kann also älter sein als
das Postfach. Das ist der Preis für strikt lesend und muss in der Tool-Beschreibung stehen,
statt mit `mailboxes#sync` "behoben" zu werden: dieser Aufruf ist ein Schreibvorgang gegen
den Cache und gehört nicht in diese Familie.

**Provisionierte Konten können scheitern, und zwar leise.** `ProvisioningMiddleware` läuft vor
jedem Mail-Controller und synchronisiert das IMAP-Passwort aus den Login-Credentials. Unter
Impersonation gibt es keine Login-Credentials, die Middleware fängt
`CredentialsUnavailableException|PasswordUnavailableException` und tut nichts. Folge: ein
provisioniertes Konto, dessen IMAP-Passwort dem Login-Passwort folgt, kann mit einem
IMAP-Fehler antworten, wenn das gespeicherte Passwort veraltet ist. Das ist eine Degradation
mit klarer Meldung ("Nextcloud Mail konnte sich nicht am IMAP-Server anmelden"), kein Bug
dieses Projekts und kein Blocker.

**Brute-Force-Schutz.** `messageApi#get` und `getRaw` tragen
`#[BruteForceProtection('mailGetMessage')]`. Wiederholte 404 aus der ExApp-IP können den
Throttler auslösen, und die trifft dann jeden Nutzer dieses Servers. Die bestehende Regel
"eine fehlgeschlagene Authentifizierung nie wiederholen" muss hier auf "einen 404 nie
wiederholen" erweitert werden.

**Die Suchbrücke funktioniert hier nicht.** Der Mail-Suchprovider baut seine `resourceUrl`
über `mail.deep_link.open` mit `$message->getMessageId()`, also der **RFC-Message-Id als
Zeichenkette**, nicht der numerischen Datenbank-Id, die `/ocs/v2.php/apps/mail/message/{id}`
braucht. Nach der Regel "never guess a kind" in `provider_map.py` bleiben Mail-Treffer damit
korrekt in der Kategorie `url`. Mail-Ids kommen ausschliesslich aus
`/api/messages?mailboxId=`.

---

## AppAPI: kein neuer Auth-Pfad, keine Scopes, keine info.xml-Änderung

Das ist die zweite Entlastung neben "keine neuen Abhängigkeiten".

- **API-Scopes gibt es nicht mehr.** AppAPI-Changelog 3.2.0 (2024-09-10): "ApiScopes are
  deprecated and removed. #373". Im aktuellen `lib/Service` existiert kein
  `ExAppApiScopeService` mehr, `occ app_api:scopes:list` wurde schon vorher entfernt. Ein
  impersonierter Request erreicht damit jede Route, die der Nutzer erreicht. Kein
  `<scopes>`-Element in `appinfo/info.xml`, keine Änderung an `--force-scopes`.
- **Der gemessene Fall A aus `docs/spike-dav.md` trägt weiter.** Alle drei neuen Familien
  laufen über dieselben Pfade, die dort bereits verifiziert sind: Talk und Tables-v2 sind
  OCS (Zeile "OCS" der Matrix, serverseitig über `cloud/user` bestätigt), Tables-v1 und die
  Mail-App-Routen sind gewöhnliche App-Routen über `OC::tryAppAPILogin` (Zeilen "Notes REST"
  und "Deck REST"). Es entsteht kein Provider-Split und kein App-Passwort-Rückfall.
- **`appinfo/info.xml` bleibt unangetastet.** Keine neue `<route>` (die Tools sind
  Werkzeuge hinter `/mcp`, keine HTTP-Oberfläche), keine neue
  `<environment-variable>`, keine Scopes. Das ist wichtig, weil jede Änderung dort das
  Variablen-Gate in `tests/unit/test_exapp_env_setup.py` und den Store-Upload berührt.
- **Talk-Bots sind ausdrücklich nicht der Weg.** AppAPI bringt einen
  `TalkBotsService` mitsamt Bot-Registrierung mit. Ein Talk-Bot handelt als eigene Identität
  mit eigenem Secret, nicht als der angemeldete Nutzer, und bricht damit genau das
  Kernversprechen ("der Assistent sieht niemals mehr als der angemeldete Nutzer"). Die
  Chat-OCS-API unter Impersonation ist der richtige Weg, der Bot-Pfad ist die falsche
  Abkürzung.

---

## Integration in die bestehende Client-Schicht

Was tatsächlich neu geschrieben wird, ist klein und liegt an vier Stellen:

| Datei | Änderung | Umfang |
|-------|----------|--------|
| `nextcloud/clients/ocs.py` | **`ocs_post` ergänzen.** Heute existiert nur `ocs_get`. Talk-Senden und Tables-Create sind die ersten OCS-Schreibaufrufe des Projekts. Braucht `OCS_HEADERS` plus `Content-Type: application/json` | klein, aber tragend |
| `nextcloud/clients/talk.py` (neu) | Reines OCS über `ocs_get`/`ocs_post` + `parse_ocs`. Lokale Guards: Token-Muster `[a-z0-9]{4,30}`, Nachrichtenlänge gegen `config.chat.max-length` | mittel |
| `nextcloud/clients/tables.py` (neu) | Gemischt: `ocs_get`/`ocs_post` + `parse_ocs` für v2, `client.get` mit `DECK_HEADERS`-Muster + `parse_app_json` für v1. Guards: numerische Ids, `nodeCollection` als geschlossene Menge, Werte gegen `column_types` | mittel |
| `nextcloud/clients/mail.py` (neu) | Gemischt: App-Routen + `parse_app_json` für Listen, OCS + `parse_ocs` für die Einzelnachricht. Dazu die HTML-nach-Text-Reduktion über `lxml` | mittel |
| `nextcloud/capabilities.py` | Drei Felder für `spreed` (features, `config.chat.max-length`, `config.conversations.can-create`), zwei für `tables` (`apiVersions`, `column_types`), plus ein zweiter Roundtrip auf `/core/navigation/apps` für `mail_available`. `_MISSING` um drei Einträge erweitern | mittel |
| `provider_map.py` | `talk-conversations`, `talk-message`, `talk-message-current`, `tables-search-tables`, `mail` als bekannte Provider-Ids. **Mail bleibt `url`** (Message-Id ist nicht die Datenbank-Id, siehe oben), Talk-Konversationen sind über `spreed.Page.showCall` auflösbar (`/apps/spreed/call/{token}`) | klein |
| AST-Grep-Gate | Die neuen erlaubten Schreibpfade sind genau zwei: `POST` auf `.../spreed/api/v1/chat/{token}` und `POST` auf `.../tables/api/2/{tables\|views}/{id}/rows`. Alles andere (`PUT`, `DELETE`, `PATCH`, jeder Mail-Schreibpfad, `mailboxes#sync`, `message/send`) muss weiter unmöglich sein | klein, kritisch |

**Schema-Diät ist hier keine Optimierung, sondern Voraussetzung.** Die drei Rohobjekte sind
die grössten, die dieses Projekt bisher angefasst hat:

- ein Talk-Raum aus `api/v4/room` hat über 50 Felder, davon fast alles Call-, Lobby-,
  SIP-, Recording- und Federation-Zustand, den ein Assistent nie braucht
- eine Tables-Zeile trägt pro Zelle ein Objekt `{columnId, value}` plus Metadaten
- eine Mail-Nachricht trägt `phishingDetails`, `smime`, `dkimValid`, `scheduling`,
  `attachments`, `inlineAttachments`, `unsubscribeUrl`, `itineraries` und den Body

Ohne aggressive Projektion in der Client-Schicht (nicht erst im Tool) sprengt jede der drei
Familien allein das Budget. Das ist der Grund, aus dem das Budget-Gate angehoben werden muss
**und** die Diät gleichzeitig strenger wird: 11268 von 12500 Bytes sind heute belegt, sechs
bis acht neue Tools kommen dazu.

**Prompt-Injection-Fläche wächst deutlich.** Talk-Nachrichten und Mail-Bodies sind
fremdgeschriebener Freitext von aussen (eine Mail kommt von einem beliebigen Absender im
Internet, eine Talk-Nachricht von jedem Teilnehmer). Der bestehende Marker-Filter aus
`tools/marks.py` muss auf jeden dieser Texte laufen, bevor der Server seine eigenen Marker
schreibt, sonst entscheidet der Absender einer Mail über die Rahmung. Das ist keine neue
Abhängigkeit, aber eine neue Pflicht-Aufrufstelle.

---

## Installation

```bash
# Nichts. Das ist der Punkt.
uv sync
```

`pyproject.toml` bleibt unverändert. Kein `uv add`, kein Lock-Update, kein Eintrag in
`docs/dependency-audit.md`, kein neues Lizenz-Thema und keine neue Angriffsfläche im
Container-Image.

Für die Integrationsstufe kommt ein Compose-Service dazu (kein Python-Paket):

```yaml
# compose.test.yml, nur für -m integration
greenmail:
  image: greenmail/standalone:latest
  environment:
    GREENMAIL_OPTS: "-Dgreenmail.setup.test.all -Dgreenmail.users=alice:alice@example.org"
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Tables-Zeilen über v1 (`/index.php/apps/tables/api/1/.../rows`) | Auf eine v2-Leseroute warten | Sobald Tables eine `GET /api/2/.../rows` bekommt. Bis dahin gibt es keine Alternative, v2 hat sie nicht |
| Tables-Spalten über v2 (`/api/2/columns/{nodeType}/{nodeId}`) | v1 `/api/1/tables/{id}/scheme` | Wenn sich die v2-Spalten-Route auf einer Instanz zickig zeigt. Der Community-Server nutzt für das Schema bewusst v1, mit dem Kommentar, die v2-Scheme-Route habe im Test Probleme gemacht. Also: v2-`columns` als Standard, v1-`scheme` als dokumentierter Ausweichpfad |
| Mail-Einzelnachricht über OCS (`/ocs/v2.php/apps/mail/message/{id}`) | `/index.php/apps/mail/api/messages/{id}/body` | Nur falls die OCS-Route auf einer Zielinstanz fehlt (ältere Mail-Version). Beide liefern über `getFullMessage()` die identische Struktur; die OCS-Variante hat den Envelope, den psalm-typisierten Vertrag und den Brute-Force-Schutz, also ist sie der Standard |
| Mail-App-Erkennung über `/core/navigation/apps` | Probe-Request auf `/api/accounts` und 404/HTML als "nicht installiert" deuten | Wenn sich zeigt, dass eine Instanz Mails Navigationseintrag ausblendet. Der Probe-Weg ist unschöner (er unterscheidet "nicht installiert" nicht sauber von "kaputt"), aber er funktioniert überall |
| `lxml.html.text_content()` für HTML-Mails | Nur `hasHtmlBody: true` melden und den Body weglassen | Wenn die Diät zeigt, dass HTML-Mails auch nach der Text-Reduktion das Budget reissen. Ein ehrliches "diese Nachricht hat einen HTML-Body, hier sind Betreff, Absender und Datum" ist besser als ein abgeschnittenes Markup-Fragment |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `html2text`, `beautifulsoup4`, `markdownify` | Wären ein Zukauf für exakt einen Zweck, den `lxml` schon kann. `lxml` steht als direkte Abhängigkeit im `pyproject.toml` und ist über die DAV-Pfade ohnehin geladen | `lxml.html.fromstring(...).text_content()` |
| `lxml.html.clean` | Seit lxml 5.2 in das eigene Paket `lxml_html_clean` ausgezogen. Der Import sieht kostenlos aus und ist es nicht | `text_content()`; Mail sanitisiert serverseitig bereits |
| `imapclient`, `imaplib`, eigene IMAP-Anbindung | Würde die Mail-App umgehen, also auch ihre Berechtigungen, ihre Verschlüsselung der Kontodaten und die Impersonation. Bricht das Kernversprechen sofort | Mails HTTP-API unter Impersonation |
| `email` / `email.parser` auf `message/{id}/raw` | Rohes RFC-2822 selbst zu parsen holt MIME, Encodings und S/MIME ins eigene Projekt. `getFullMessage()` liefert das bereits geparst und sanitisiert | `GET /ocs/v2.php/apps/mail/message/{id}` |
| `nc_py_api` | In v1.0 bewusst nicht genommen, daran ändert v1.2 nichts. Alles, was hier gebraucht wird, sind neun HTTP-Aufrufe | httpx + die vorhandene Client-Schicht |
| Talk `lookIntoFuture=1` | Long-Poll bis 60 Sekunden, blockiert den Tool-Aufruf, und es ist der einzige Zweig, in dem Lesemarker und Benachrichtigungen tatsächlich geschrieben werden | `lookIntoFuture=0` |
| Talk-Bot-API / AppAPI `TalkBotsService` | Der Bot handelt als eigene Identität, nicht als der Nutzer. Bricht "sieht nie mehr als der Nutzer" | Chat-OCS unter Impersonation |
| Mail `POST /ocs/v2.php/apps/mail/message/send`, `/api/outbox`, `setFlags`, `setTag`, `move`, `snooze`, `DELETE /api/messages/{id}` | Milestone-Entscheid: Mail ist strikt lesend. Diese Routen existieren und sind unter Impersonation erreichbar, deshalb muss das Gate sie aktiv ausschliessen, nicht die Unwissenheit | nichts; nicht implementieren |
| Mail `mailboxes#sync` | Schreibt in den Cache und stösst IMAP-Verkehr an. "Strikt lesend" heisst, die Cache-Frische auszuhalten und zu benennen | Staleness in der Tool-Beschreibung dokumentieren |
| Mail OCS-Anhangsroute `/message/{id}/attachment/{id}` | Über Mail-Versionen unzuverlässig, antwortet auf manchen Instanzen mit HTTP 200 und leerem Nicht-JSON-Body (cbcoutinho GH #989). Anhänge sind in v1.2 ohnehin ausserhalb des Lesescopes | Anhänge nur als Metadaten (Name, MIME, Grösse) auflisten |
| `Origin`-Header auf Tables-v1 | `#[CORS]` aktiviert die `CORSMiddleware`, die dann eine Basic-Reauthentifizierung verlangt, die unter Impersonation nicht existiert | keinen `Origin` senden (Status quo) |
| Versions-Gate auf `capabilities.tables.version` | Sperrt die 1.0-Linie auf NC 32 falsch aus, obwohl sie `apiVersions` 1.0/2.0/2.1 kann | Gate auf `apiVersions` |

---

## Stack Patterns by Variant

**Wenn eine Familie fehlt (der Normalfall):**
- `capabilities.require_app("spreed" | "tables" | "mail")` vor dem ersten Request, exakt das
  Notes-/Deck-Muster
- `tools/list` bleibt statisch. Eine credential-abhängige Tool-Liste würde Caching,
  Budget-Gate und jeden Client zerschiessen, der Tool-Listen persistiert. Die Familie ist
  gelistet und antwortet mit einer Erklärung, sie verschwindet nicht
- `prepare_context` lässt die fehlende Familie weg und sagt es, statt zu scheitern

**Wenn die Familie da ist, der Nutzer aber nicht darf:**
- Talk: `config.conversations.can-create` und die 403 aus `RequirePermission(CHAT)` /
  `RequireReadWriteConversation`
- Tables: die 403 aus `RequirePermission(PERMISSION_CREATE)`. Der Read-Only-Fall ist normal
  (geteilte Tabelle ohne Create-Recht) und muss als Erklärung ankommen, nicht als Fehler
- Mail: `403` aus `DoesNotExistException` beim Zugriff auf ein fremdes Postfach

**stdio- und Passthrough-Modus:**
- Identisch. Die drei Familien sprechen ausschliesslich über `Credentials.auth()`, also
  wechselt zwischen App-Passwort und Impersonation nur das `httpx.Auth`-Objekt. Kein
  Sonderfall, kein zweiter Codepfad. Im Basic-Modus gilt derselbe `OCS-APIRequest`-Header,
  aus demselben Grund

---

## Version Compatibility

| Komponente | Kompatibel mit | Notizen |
|------------|----------------|---------|
| Talk (`spreed`) 22.x / 23.x / 24.x | NC 32 / 33 / 34 | Alle mit `conversation-v4` und Chat v1. Endpunkte in dieser Spanne stabil |
| Talk Chat-API `v1`, Room-API `v4` | fest, nicht verhandelbar | Routen-Requirements `(v1)` bzw. `(v4)` im Quelltext |
| Tables 1.0.x | NC 30-32 | Der Weg auf NC 32; meldet `apiVersions` 1.0/2.0/2.1 |
| Tables 2.1.x / 2.2.x | NC 33-34 / NC 33-35 | Der Weg auf NC 33 und 34 |
| Tables OCS-`createRow` | seit Tables 0.8.0 | Liegt unter allem, was in der NC-32-bis-34-Spanne installierbar ist |
| Mail 5.10.x / 5.11.x / 5.12.x | NC 32-35 | Ein Versions-Gate ist hier nicht empfohlen, weil Mail keine Capability meldet. Statt zu gaten: `/core/navigation/apps` prüfen und auf 404/HTML degradieren |
| `Request::passesCSRFCheck()` mit `OCS-APIRequest` | NC 32, 33, 34, master | In allen vier Zweigen identischer Code. Der Mechanismus, der Mails interne Routen und Decks/Tables' App-Routen überhaupt erreichbar macht |
| AppAPI ohne API-Scopes | seit AppAPI 3.2.0 (2024-09-10) | Scopes entfernt, kein `<scopes>` in `info.xml` nötig |
| `pyproject.toml` | unverändert | Keine neue Abhängigkeit, kein Lock-Update |

---

## Offene Punkte, ehrlich benannt

1. **Nichts davon ist gegen eine laufende Instanz gemessen.** Alles oben ist aus dem
   Quelltext der jeweiligen App am aktuellen Zweig gelesen, plus die unabhängige
   Bestätigung des Community-Servers für den Mail-CSRF-Mechanismus. Der saubere Abschluss
   ist ein kurzer Spike im Stil von `docs/spike-dav.md`: eine Zeile je Familie, Endpunkt,
   Auth-Pfad, gemessener Status, serverseitig verifizierte Identität. Neun Requests, ein
   Nachmittag, und danach ist die Tabelle oben Messung statt Lektüre.
2. **Mail-Mindestversion (MEDIUM).** Wann genau die OCS-`messageApi`-Routen eingeführt
   wurden, liess sich nicht sauber datieren: das Feature geht auf nextcloud/mail#9703
   (Juni 2024) zurück, der Changelog nennt es nicht, und Mail veröffentlicht keine
   Capability, an der man es ablesen könnte. Empfehlung, die diese Lücke schliesst, ohne sie
   zu verstecken: nicht auf eine Version gaten, sondern die Route probieren und bei 404
   oder HTML mit einer Erklärung degradieren.
3. **`/core/navigation/apps` als Erkennungsweg (MEDIUM).** Route, Attribute und Semantik
   sind im Quelltext verifiziert, die Antwortform aber nicht gegen eine Instanz geprüft. Ein
   Randfall bleibt offen: eine Instanz, die Mails Navigationseintrag ausblendet, würde als
   "Mail fehlt" gelesen. Gegenprobe über den `mail`-Suchprovider ist der billige Ausweg,
   weil die Provider-Liste ohnehin gelesen wird.
4. **Talk-Nachrichtentext-Fidelity.** Talk liefert `message` mit Platzhaltern
   (`{actor}`, `{file}`) und die Auflösung in `messageParameters`. Ein Tool, das nur
   `message` weiterreicht, zeigt bei Dateifreigaben wörtlich `{file}`. Wie weit die
   Substitution gehen soll, ist eine Feature-Entscheidung, nicht eine Stack-Entscheidung,
   gehört aber in die Phasenplanung.
5. **Tables-Zellwert-Formate je `column_types`.** `column_types` liefert die Liste
   (`text-line`, `text-rich`, `selection-multi`, `datetime`, `usergroup`, ...), aber nicht
   die erwartete Wertform pro Typ beim Create. Das ist die eine Stelle, an der die
   Zeilen-Create-Phase eigene Recherche braucht, und ein `usergroup`- oder
   `selection-multi`-Wert ist der wahrscheinlichste Ort für einen 400.

---

## Sources

- https://raw.githubusercontent.com/nextcloud/server/stable32/lib/private/AppFramework/Http/Request.php sowie stable33, stable34 und master, `passesCSRFCheck()` und `cookieCheckRequired()` — der `OCS-APIRequest`-Mechanismus, in vier Zweigen identisch (HIGH)
- https://raw.githubusercontent.com/nextcloud/server/master/lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php — `isInvalidCSRFRequired()`, `isValidOCSRequest()` (HIGH)
- https://raw.githubusercontent.com/nextcloud/server/stable34/core/Controller/NavigationController.php — `/core/navigation/apps`, `NoAdminRequired` + `NoCSRFRequired` (HIGH)
- https://nextcloud-talk.readthedocs.io/en/latest/conversation/ und /chat/ — Room v4, Chat v1, Parameter und Statuscodes (HIGH)
- https://raw.githubusercontent.com/nextcloud/spreed/main/lib/Controller/ChatController.php — `receiveMessages` und `sendMessage`, Defaults, `apiVersion`-Requirements, die drei Nebenwirkungs-Gates (HIGH)
- https://raw.githubusercontent.com/nextcloud/spreed/main/lib/Controller/RoomController.php — `getRooms`, `getSingleRoom`, `(v4)` (HIGH)
- https://raw.githubusercontent.com/nextcloud/spreed/main/lib/Capabilities.php — Schlüssel `spreed`, `FEATURES`, `config.chat.max-length`, `config.conversations.can-create`, leeres Array bei deaktiviertem Talk (HIGH)
- https://raw.githubusercontent.com/nextcloud/spreed/main/lib/Chat/ChatManager.php — `MAX_CHAT_LENGTH = 32000` (HIGH)
- https://raw.githubusercontent.com/nextcloud/spreed/main/lib/Search/{ConversationSearch,MessageSearch,CurrentMessageSearch}.php — Provider-Ids `talk-conversations`, `talk-message`, `talk-message-current`, `spreed.Page.showCall` (HIGH)
- https://raw.githubusercontent.com/nextcloud/tables/main/appinfo/routes.php — die vollständige Routenliste, insbesondere: unter `'ocs'` existiert nur `RowOCS#createRow` und keine Zeilen-Leseroute (HIGH)
- https://raw.githubusercontent.com/nextcloud/tables/main/lib/Controller/RowOCSController.php — Body-Form `{"data": {columnId: value}}`, Antwort 200, `RequirePermission(CREATE)` (HIGH)
- https://raw.githubusercontent.com/nextcloud/tables/main/lib/Controller/Api1Controller.php — `indexTableRows`/`indexViewRows`/`indexTableRowsSimple` mit `limit`/`offset`, `NoCSRFRequired` + `CORS` auf allen v1-Routen (HIGH)
- https://raw.githubusercontent.com/nextcloud/tables/main/lib/Capabilities.php sowie die Tags v0.9.11, v1.0.9, v2.1.1 — `apiVersions` ["1.0","2.0","2.1"] in allen, `column_types` (HIGH)
- https://raw.githubusercontent.com/nextcloud/tables/main/lib/AppInfo/Application.php — `NODE_TYPE_TABLE = 0`, `NODE_TYPE_VIEW = 1`, Permission-Konstanten (HIGH)
- https://github.com/nextcloud/tables/blob/main/CHANGELOG.md — "Enh(API): Add OCS API to create rows #1161" unter 0.8.0 (HIGH)
- https://github.com/nextcloud/tables/issues/2237 — der Objekt-statt-Liste-Fehler beim Create und die irreführende Doku (MEDIUM)
- https://raw.githubusercontent.com/nextcloud/mail/main/appinfo/routes.php — `'ocs'`-Block mit `messageApi#{get,getRaw,getAttachment}`, `'resources'`-Block mit accounts/mailboxes/messages (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/Controller/MessageApiController.php — `OCSController`, `ApiRoute`, `BruteForceProtection`, 200/206-Semantik (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/Controller/{Messages,Accounts,Mailboxes}Controller.php — gewöhnliche `Controller` **ohne** `@NoCSRFRequired` auf den Index-Methoden, `limit` auf 100 gedeckelt, Cursor-Paginierung, Lesen aus dem DB-Cache (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/Model/IMAPMessage.php — `getFullMessage()`: `body` ist HTML bei `hasHtmlMessage`, sonst Klartext (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/ResponseDefinitions.php — `MailIMAPFullMessage` / `MailMessageApiResponse`, die Feldflut für die Schema-Diät (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/Http/Middleware/ProvisioningMiddleware.php — Passwortsync ist ein No-op ohne Login-Credentials (HIGH)
- https://raw.githubusercontent.com/nextcloud/mail/main/lib/Search/Provider.php — Provider-Id `mail`, `resourceUrl` über `mail.deep_link.open` mit der RFC-Message-Id (HIGH)
- `gh api repos/nextcloud/mail/contents/lib` plus `appinfo/info.xml` — keine `Capabilities.php`, keine Capability-Registrierung (HIGH)
- https://raw.githubusercontent.com/nextcloud/app_api/main/CHANGELOG.md — "ApiScopes are deprecated and removed. #373" unter 3.2.0 (2024-09-10); `lib/Service` ohne Scope-Service (HIGH)
- Versionsmatrix aus `appinfo/info.xml` der Zweige spreed/stable32|33|34 (22.0.17, 23.0.10, 24.0.4), tables main + Tags, mail main/stable5.11/stable5.10 (HIGH)
- https://github.com/cbcoutinho/nextcloud-mcp-server, `nextcloud_mcp_server/client/{mail,tables,talk}.py` — unabhängige Bestätigung gegen ein laufendes Mail 5.x für den `OCS-APIRequest`-CSRF-Ausweg, für die Talk-Versionen v4/v1 und für den Tables-v1-Zeilenpfad; ausserdem die gemessenen Warnungen zur v2-Scheme-Route und zur OCS-Anhangsroute (MEDIUM)
- `docs/spike-dav.md` (dieses Repo) — Fall A, alle Familien unter Impersonation, serverseitig verifizierte Identität (HIGH)

---
*Stack research for: Nextcloud MCP-only ExApp, Milestone v1.2 (Talk, Tables, Mail)*
*Researched: 2026-08-21*
