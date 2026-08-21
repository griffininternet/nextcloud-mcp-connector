# Phase 8: Erreichbarkeits-Spike und Tables, Recherche

**Recherchiert:** 2026-08-21
**Domäne:** Nextcloud Tables (API-Generationen 1 und 2) plus ein blockierender Erreichbarkeits-Spike für Nextcloud Mail unter AppAPI-Impersonation
**Konfidenz:** HIGH (Tables-Routen, Payloads und Statuscodes gegen die exakte Version gelesen, die auf der Testinstanz landet; Codebasis-Anknüpfungspunkte gelesen und Budget live gemessen; Mail-Routen und -Attribute gegen v5.11.1 gelesen, die Erreichbarkeit selbst ist genau die offene Messung dieser Phase)

> Diese Datei baut auf der Meilenstein-Kernrecherche in `.planning/research/` auf und
> wiederholt sie nicht. Sie enthält (a) die für die Planung fehlenden Codebasis-Anknüpfungspunkte,
> (b) die exakten Tables-Routen und Payload-Formen gegen Tables 2.2.2, (c) einen ausführbaren
> Messplan für den Mail-Spike, und (d) **elf Korrekturen** an der Kernrecherche, die die
> Planung direkt betreffen. Der Korrekturabschnitt ist der wichtigste Teil dieser Datei.

## Zusammenfassung

Die Tables-Familie ist mechanisch, aber nicht trivial: die Zeilen-Leseroute liegt in der
alten Generation (`/index.php/apps/tables/api/1/...`, `parse_app_json`), das Zeile-Anlegen in
der OCS-Generation (`/ocs/v2.php/apps/tables/api/2/...`, `parse_ocs`), und damit entsteht in
dieser Phase der **erste OCS-Schreibaufruf des Projekts** (`ocs.ocs_post`), nicht erst in
Phase 9 wie die Roadmap notiert. Beide v1-Zeilenrouten tragen `#[NoCSRFRequired]`, `#[CORS]`
und `#[OpenAPI(scope: SCOPE_DEFAULT)]`, sind also eine zugesagte API und kein
Frontend-Innenleben; das ist der entscheidende Unterschied zu Mail und der Grund, warum
Tables die risikoarme Familie ist.

Die grösste Falle der Phase ist keine Route, sondern ein Berechtigungsfeld: Nextcloud
serialisiert `onSharePermissions` für eine **eigene** Tabelle als
`{read:true, create:false, update:false, delete:false, manage:false}` und setzt
`isShared:false`. Ein Gate, das TABLES-02 wörtlich nimmt und auf `onSharePermissions.create`
prüft, würde also genau den Eigentümer aussperren, der serverseitig alles darf. Das ist
buchstäblich der `canCreateBoards`-Fehler aus Phase 1 in neuem Gewand, und die Codebasis hat
mit `deck._require_write_permission` schon die richtige Antwort dafür.

Der Mail-Spike ist billiger machbar als gedacht und braucht für die eigentliche Frage
(MAIL-04: trägt die AppAPI-Impersonation die internen Mail-Routen) **keinen echten
IMAP-Server**. Jede Antwort, die aus App-Code stammt (200, 403, 404 oder auch 500 mit
JSON-Körper), beweist, dass Controller und CSRF-Ausweg erreicht wurden; nur eine HTML-Loginseite
oder ein 3xx auf `/login` widerlegt es. Eine echte IMAP-Gegenprobe (GreenMail als vierter
Compose-Dienst) ist die Ausbaustufe, die zusätzlich die Feldformen für Phase 10 liefert.

**Primärempfehlung:** Plan 1 misst den Mail-Zugang gegen die schon laufende HaRP-Topologie mit
einem Konto ohne erreichbaren IMAP-Server (Stufe 1) und stuft nur bei einem uneindeutigen
Ergebnis auf GreenMail hoch (Stufe 2); Plan 2 und 3 bauen Tables nach dem Deck-Muster mit
`GET /ocs/v2.php/apps/tables/api/2/tables/{id}` als einzigem Metadatenaufruf (liefert
`rowsCount`, `isShared`, `onSharePermissions` und den Titel in einem Request, bedient damit
Kappungsmarkierung und Schreibrecht-Vorprüfung gleichzeitig) und `rows/simple` als
Standard-Zeilenform.

## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Research Support |
|----|------------------------------------|------------------|
| MAIL-04 | Mail-Zugang im AppAPI-Modus live bewiesen (accounts, mailboxes, messages, OCS-Volltext), SCOPE_IGNORE-Risiko im Code und in der Doku benannt | Messplan mit vier Wegen, erwarteten Statuscodes und Entscheidungskriterium (Abschnitt "Mail-Spike"); `SCOPE_IGNORE` an allen drei Controllern gegen v5.11.1 verifiziert; Vorbild `tests/integration/test_exapp_dav_matrix.py` plus `docs/spike-dav.md` |
| TABLES-01 | Tabellen, Spalten und Zeilen lesen, `limit`/`offset` (Default 25, Max 200), `rows/simple` als Default für Tabellen, `rowsCount`, benannte Truncation | Vollständige Routen-, Parameter- und Antwortformtabelle gegen Tables 2.2.2 verifiziert; `rows/simple`-Semantik aus `V1Api::getData` gelesen (erste Zeile sind die Titel, keine Row-Ids); `rowsCount` kommt aus dem Table-Objekt |
| TABLES-02 | Zeile mit Spaltentiteln statt Ids anlegen, unbekannte/mehrdeutige/fehlende Pflichttitel ablehnen, `onSharePermissions.create` vorab prüfen | `createRow`-Body-Form und Statuscode 200 verifiziert; `mandatory`-Feld je Spalte verifiziert; Korrektur K5 zur Eigentümer-Falle bei `onSharePermissions` mit der korrekten Prüfregel |

## Projekt-Constraints (aus CLAUDE.md und globalen Regeln)

Diese Direktiven haben dieselbe Autorität wie gesetzte Entscheidungen. Die Planung darf ihnen
nicht widersprechen.

- **Code und README auf Englisch**, Projektkommunikation auf Deutsch. Keine Em-Dashes, echte
  Umlaute in deutschen Texten.
- **Keine Emojis** ausser auf ausdrückliche Anfrage; Icons nur als SVG.
- **Security-Constraint aus PROJECT.md:** Der MCP darf nie mehr sehen als der angemeldete
  Nutzer; keine destruktiven Writes.
- **Tech-Stack-Constraint:** Python 3.13, `uv` als Toolchain (System-Python ist defekt, jedes
  Kommando läuft als `uv run ...`), offizielles MCP-SDK.
- **Code-Bereinigung ist Pflicht:** `ruff check .` und `ruff format --check .` über das ganze
  Repo, plus `vulture` (volle Konfidenz, annotierte Whitelist) vor jedem Push.
- **Nach jedem Edit committen** (ohne Rückfrage), keine Claude-Attribution in Commits,
  GitHub-Push auf `master` ist erlaubt (der Hook blockt nur GitLab).
- **Tests decken alle Pfade ab**, nicht nur den Happy Path: Fehler, Edge, Negativ, `no_data`.
- **Doku-Seite mitziehen:** nach einer API- oder Verhaltensänderung README (EN/DE/FR),
  `docs/` und Changelog nachziehen. Nutzerrelevante Änderungen gehören in den Changelog.
- **Vokabular-Gate:** das Wort "archiv" ist in öffentlichen Artefakten verboten. Tables hat
  archivierte Tabellen; die deutschen und französischen Texte müssen das ohne dieses Wort
  ausdrücken (etwa "zur Seite gelegte Tabellen"), im englischen Code bleibt `archived` als
  Feldname natürlich unberührt.
- **GSD-Workflow:** Datei-Änderungen nur innerhalb eines GSD-Kommandos.

Kein `.claude/skills/`- oder `.agents/skills/`-Verzeichnis vorhanden, also keine
projekteigenen Skill-Regeln zu berücksichtigen.

## Architektonische Verantwortungs-Zuordnung

| Fähigkeit | Primäre Schicht | Sekundäre Schicht | Begründung |
|-----------|-----------------|-------------------|------------|
| Endpunktwissen Tables (URL-Bau, Generationswahl, Parser) | `nextcloud/clients/tables.py` (neu) | `nextcloud/clients/ocs.py` (neuer `ocs_post`) | Eine Familie, ein Modul, auch wenn zwei API-Generationen darin liegen; die Trennlinie darf nicht beim Aufrufer landen |
| Erzwungenes `limit` auf Zeilen | Client | Tool (zweite Kappung) | Pitfall 7b: ein Weglassen liest die ganze Tabelle. Die Regel muss dort stehen, wo die URL entsteht |
| Titel-zu-Id-Abbildung, Pflichtspalten, Fehlersätze | `tools/tables.py` (neu) | Client (Pfad-Id-Wächter) | Fachlogik und Wortlaut gehören ins Tool, Wächter an die Naht zur URL |
| Schreibrecht-Vorprüfung | `tools/tables.py` | Nextcloud (`RequirePermission`-Middleware als letzte Instanz) | Muster 4 der Kernrecherche: das Objekt entscheidet, nicht das Konto |
| App-Erkennung `tables.enabled` | `nextcloud/capabilities.py` (geändert) | `tools/tables.py` (`require_app` als erste Zeile) | Ein gecachter Request statt eines 404 auf einer HTML-Seite |
| Schema, Annotationen, Enum-Level | `server/reg_tables.py` (neu) | `scripts/check_tool_budget.py` (Gate) | Registrierung ist eine eigene Datei je Familie, damit parallele Pläne keine gemeinsame Datei anfassen |
| Mail-Erreichbarkeitsbeweis | `tests/integration/test_exapp_mail_reach.py` (neu) | `docs/spike-mail.md` (neu) | Ein Spike ist eine Messung plus ihr Protokoll, kein Produktionscode |
| Nextcloud-seitige Voraussetzungen (Apps, Mail-Konto) | `scripts/bootstrap_exapp.sh` (geändert) | `compose.exapp.yml` (optional GreenMail) | Die Topologie ist Teil des Beweises und muss reproduzierbar sein |

## Standard Stack

### Kern

| Baustein | Version | Zweck | Warum Standard |
|----------|---------|-------|----------------|
| `httpx` | 0.28.x (bereits im Projekt) | Einziger HTTP-Client für alle Tables-Aufrufe | Beide Generationen sind JSON über HTTP; kein XML, kein DAV |
| `mcp[cli]` | >=2.0,<3 (bereits) | Tool-Registrierung | `reg_tables.py` folgt `reg_deck.py` eins zu eins |
| `pytest` + `respx` | bereits im Dev-Group | Unit-Tests mit gemocktem httpx | Vorbild `tests/unit/test_deck_client.py` |
| Nextcloud Tables | **2.2.2** (2026-08-19) | Zieldomäne | Aktuellste Store-Fassung, `nc >=33.0.0 <36.0.0`, läuft auf der Testinstanz NC 34.0.3 [VERIFIED: apps.nextcloud.com/api/v1/platform/34.0.0/apps.json] |
| Nextcloud Mail | **5.11.1** (2026-08-20) | Spike-Ziel | `nc >=32.0.0 <36.0.0`, `php >=8.1.0 <8.6.0` [VERIFIED: apps.nextcloud.com API] |

**Keine neue Python-Abhängigkeit.** `pyproject.toml` und `uv.lock` bleiben in dieser Phase
unangetastet. `lxml` wird erst in Phase 10 für HTML-Mail-Bodies gebraucht und ist ohnehin
schon Dependency.

### Unterstützend (nur Testinfrastruktur, optional)

| Baustein | Version | Zweck | Wann nötig |
|----------|---------|-------|------------|
| `greenmail/standalone` (Docker-Image) | 2.1.12 (2026-08-05) | Echter IMAP/SMTP-Server für die Mail-Spike-Ausbaustufe | Nur wenn Stufe 1 des Spikes kein eindeutiges Ergebnis liefert oder wenn Phase 10 die Feldformen vorab braucht [VERIFIED: hub.docker.com/v2/repositories/greenmail/standalone/tags] |

GreenMail-Eckdaten [CITED: greenmail-mail-test.github.io/greenmail/#deploy_docker]: Testports
IMAP 3143, IMAPS 3993, SMTP 3025, SMTPS 3465, POP3 3110, API 8080. Konfiguration über
`GREENMAIL_OPTS`, Default
`-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 -Dgreenmail.auth.disabled`,
Nutzer über `-Dgreenmail.users=user1:pwd@domain,user2:pwd`, Erweiterung ohne Überschreiben
über `GREENMAIL_ADDITIONAL_OPTS` (ab 2.1.9).

### Alternativen, geprüft und verworfen

| Statt | Möglich wäre | Abwägung |
|-------|--------------|----------|
| `GET /api/2/tables` plus `GET /api/2/tables/{id}` | `GET /ocs/v2.php/apps/tables/api/2/init` | `init` liefert "Tables and views incl. shares" als ein `Index`-Objekt, also deutlich mehr Payload als gebraucht. Für ein Byte-Budget ist der schmale Aufruf richtig [VERIFIED: openapi.json, Pfad `/api/2/init`] |
| `rows/simple` als Default | Immer `rows` plus `columns` | `rows` liefert Row-Ids und typisierte Werte, kostet aber den Spaltenaufruf und mehr Bytes. Empfehlung: `simple` als Default (TABLES-01), `rows` nicht in Phase 8 bauen, solange keine adressierbare Zeile gebraucht wird |
| Eigene Titel-Abbildung über den Spaltenaufruf | `dataByAlias` aus der Zeilenantwort | `dataByAlias` ist ein leeres Dictionary, solange keine Aliase konfiguriert sind (`Row2::$dataByAlias = []`, wird nur von aussen gesetzt). Als Abkürzung unbrauchbar, [ASSUMED] für den konkreten Laufzeitwert |
| GreenMail | docker-mailserver, eigenes Dovecot-Image | Schwergewichtig, mehr Konfiguration, kein Gewinn für vier Messzeilen |
| Kein Versions-Gate, nur Capability-Gate | Gate auf `tables.version` | Ein Versions-Gate würde die 1.0-Linie auf NC 32 falsch aussperren; `apiVersions` enthält in jeder relevanten Fassung `1.0` und `2.0` |

## Package Legitimacy Audit

**Nicht anwendbar in dieser Phase: es wird kein externes Paket installiert.** `pyproject.toml`
und `uv.lock` bleiben unverändert, es gibt kein `uv add`, kein `npm install`, kein `pip install`.

Die zwei externen Artefakte, die dazukommen, sind keine Sprachpakete, sondern Nextcloud-Apps
und ein Docker-Image; sie sind über ihre offiziellen Quellen verifiziert:

| Artefakt | Quelle | Verifikation | Disposition |
|----------|--------|--------------|-------------|
| Nextcloud-App `tables` 2.2.2 | apps.nextcloud.com (offizieller Store) | Store-API-Abfrage: Plattform-Spec `>=33.0.0 <36.0.0`, veröffentlicht 2026-08-19; Quellcode auf github.com/nextcloud/tables Tag `v2.2.2` gelesen | Freigegeben |
| Nextcloud-App `mail` 5.11.1 | apps.nextcloud.com (offizieller Store) | Store-API-Abfrage: `>=32.0.0 <36.0.0`, veröffentlicht 2026-08-20; Quellcode Tag `v5.11.1` gelesen | Freigegeben |
| Docker-Image `greenmail/standalone:2.1.12` | Docker Hub, Projekt GreenMail | Tag-Liste der Registry (59 Tags, 2.1.12 vom 2026-08-05) plus offizielle Projektdoku für Ports und Optionen | Freigegeben, optional |

`occ app:install` funktioniert auf der laufenden Testinstanz: ein Aufruf gegen
`https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json` aus dem Container heraus
antwortet mit 200 [VERIFIED: `docker exec nc-mcp-exapp-nc curl ...`].

## Korrekturen an der Meilenstein-Kernrecherche

Diese elf Punkte sind gegen die exakten Versionen geprüft, die auf der Testinstanz landen. Sie
widersprechen an einigen Stellen `.planning/research/*`. Wo sie widersprechen, gilt diese
Datei, weil hier der Tag-genaue Quellcode gelesen wurde.

**K1. Der Mail-OCS-Pfad hat kein `api`-Segment.** `PITFALLS.md` nennt vier Routen unter
`/ocs/v2.php/apps/mail/api/message/...`. In `appinfo/routes.php` von v5.11.1 stehen im
`ocs`-Block genau drei Einträge: `/message/{id}`, `/message/{id}/raw`,
`/message/{id}/attachment/{attachmentId}`. Die korrekte URL ist also
**`GET /ocs/v2.php/apps/mail/message/{id}`**, wie `ARCHITECTURE.md` und `STACK.md` sagen.
Der Spike muss den `/api/`-Pfad nicht messen; wer ihn misst, bekommt einen 404 aus der
Routing-Schicht und hält Mail für unerreichbar. [VERIFIED: nextcloud/mail v5.11.1
appinfo/routes.php]

**K2. `/message/send` steht nicht in `routes.php`, sondern als Attribut am Controller.**
`MessageApiController::send` trägt `#[ApiRoute(verb: 'POST', url: '/message/send')]`. Die Route
existiert also, sie ist nur nicht im `ocs`-Block sichtbar. Für das AST-Gate in Phase 10 heisst
das: die Nadel muss `message/send` sein, nicht ein Pfad aus `routes.php`. [VERIFIED:
nextcloud/mail v5.11.1 lib/Controller/MessageApiController.php]

**K3. `nodeType` beim Spaltenaufruf ist ein Wort im Singular, keine Zahl.** `STACK.md` sagt,
bei `columns` sei `nodeType` "die Zahl aus `Application`: 0 = Tabelle, 1 = View, Requirement
`(\d+)`". Das gilt für `favorites`, nicht für `columns`. Die Route
`['name' => 'ApiColumns#index', 'url' => '/api/2/columns/{nodeType}/{nodeId}']` hat **kein**
`requirements`-Element, und der Controller ist mit `@param 'table'|'view' $nodeType`
dokumentiert. Richtig ist also
`GET /ocs/v2.php/apps/tables/api/2/columns/table/{tableId}`. Beim Zeile-Anlegen heisst der
Pfadteil dagegen `nodeCollection` und ist der **Plural** `tables` oder `views`
(`requirements` `(tables|views)`). Zwei Schreibweisen in einer App, und ein Verwechseln
ergibt einen 404 aus der Routing-Schicht. [VERIFIED: nextcloud/tables v2.2.2
appinfo/routes.php, lib/Controller/ApiColumnsController.php, lib/Controller/RowOCSController.php]

**K4. `createRow` akzeptiert `data` auch als JSON-String.** Das Body-Schema ist
`{"data": oneOf[string, object]}`, und der Controller macht `if (is_string($data)) { $data =
json_decode($data, true); }`. Muster 3 der Kernrecherche (Freiform-Feld als String im
Tool-Schema) passt damit ohne Umbau bis in den HTTP-Body durch; das Tool kann den geparsten
Dict senden oder den String durchreichen. Die Schlüssel werden mit `(int)$key` gecastet, es
sind also immer Spalten-**Ids**, niemals Titel. [VERIFIED: openapi.json, RowOCSController]

**K5. `onSharePermissions` ist bei einer eigenen Tabelle nicht "keine Rechte", sondern nur
`read`.** `TableService::setIsSharedState` setzt für eine Tabelle, deren `ownership` der
aufrufende Nutzer ist, `isShared = false` und
`onSharePermissions = new Permissions(read: true)`. Das `Permissions`-Modell hat für alle
anderen Felder den Default `false` und serialisiert genau fünf Felder. Serverseitig darf der
Eigentümer trotzdem alles: `PermissionsService::checkPermission` ruft zuerst `basisCheck`, und
das gibt `true` zurück, sobald `userIsElementOwner` zutrifft.
**Die korrekte Vorprüfung für `tables_create_row` lautet also:** erlaubt, wenn
`isShared == false` (eigene Tabelle) **oder** `onSharePermissions.create == true` **oder**
`onSharePermissions.manage == true`; abgelehnt nur im Rest. Ein wörtliches
`if not onSharePermissions.create: refuse` würde jeden Nutzer auf seiner eigenen Tabelle
abweisen, und ein Test, der nur mit einer eigenen Tabelle arbeitet, wäre rot, ohne dass die
Ursache am Feldnamen sichtbar ist. Das ist derselbe Fall wie `canCreateBoards` in Phase 1
(siehe `tools/deck.py::_require_write_permission`), und die Begründung gehört genauso in einen
Docstring. [VERIFIED: nextcloud/tables v2.2.2 lib/Service/TableService.php,
lib/Model/Permissions.php, lib/Service/PermissionsService.php]

**K6. Bei Mail führt ein fehlendes `limit` nicht zu "alles", sondern zu genau einer
Nachricht.** `MessagesController::index` rechnet `$limit = min(100, max(1, $limit))`; mit
`null` ergibt `max(1, null)` in PHP 8 den Wert 1. Die Kernrecherche notiert "serverseitig auf
100 gekappt", was nur die Obergrenze ist. Für den Spike ist das relevant, weil eine
Ein-Element-Antwort kein Fehler ist. [VERIFIED: nextcloud/mail v5.11.1
lib/Controller/MessagesController.php]

**K7. `/api/mailboxes` antwortet mit einem Objekt, nicht mit einer Liste, und berührt immer
IMAP.** Die Antwort ist `{id, email, mailboxes: [...], delimiter}`. `MailManager::getMailboxes`
ruft **unbedingt** `mailboxSync->sync(...)`, und dieser Sync steigt nur dann früh aus, wenn der
letzte Sync jünger als 7200 Sekunden ist. Ohne erreichbaren IMAP-Server endet der Aufruf in
einer `ServiceException`, die `#[TrapError]` in eine JSON-Antwort verwandelt. Für den Spike ist
das kein Problem, sondern ein Messwert (siehe Entscheidungskriterium unten). [VERIFIED:
nextcloud/mail v5.11.1 lib/Controller/MailboxesController.php, lib/Service/MailManager.php,
lib/IMAP/MailboxSync.php]

**K8. `rows/simple` hat keine Zeilen-Ids.** `V1Api::getData` baut eine Liste von Listen: die
erste Liste sind die Spaltentitel, danach je Zeile die Werte in Spaltenreihenfolge, fehlende
Werte als leerer String. Kein `id`, kein `createdBy`, keine Typinformation. Zwei Folgen:
`limit=25` liefert **26** Listen (Titelzeile plus Zeilen), und eine über `rows/simple` gelesene
Zeile ist später nicht adressierbar. Deshalb braucht Phase 8 **keinen** neuen
`row:`-Id-Typ in `ids.py`, und `ids.py` bleibt unangetastet. [VERIFIED: nextcloud/tables v2.2.2
lib/Api/V1Api.php]

**K9. Der erste `ocs_post` entsteht in Phase 8, nicht in Phase 9.** Die Roadmap schreibt
Phase 9 zu, dass dort "der erste `ocs_post`" liegt. `tables_create_row` postet aber nach
`/ocs/v2.php/apps/tables/api/2/{nodeCollection}/{nodeId}/rows`, und `clients/ocs.py` kennt
heute nur `ocs_get`. Die Naht `ocs.ocs_post` (beide Pflichtheader, `Content-Type:
application/json`, `auth=creds.auth()` pro Aufruf, keine Redirect-Folge, kein `Origin`-Header)
gehört damit in diese Phase. Phase 9 benutzt sie dann nur.

**K10. Die Tables-v1-Zeilenrouten sind eine zugesagte API, nicht internes Frontend.**
`indexTableRows` und `indexTableRowsSimple` tragen `#[NoAdminRequired]`, `#[NoCSRFRequired]`,
`#[CORS]`, `#[RequirePermission(READ)]` und ausdrücklich `#[OpenAPI(scope:
OpenAPI::SCOPE_DEFAULT)]`. Sie stehen in der `openapi.json` der App. Das ist der genaue
Gegensatz zu Mails `#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]` und der Grund, warum bei Tables
kein Ersetzbarkeits-Hinweis nötig ist und bei Mail schon. [VERIFIED: nextcloud/tables v2.2.2
lib/Controller/Api1Controller.php]

**K11. `GET /api/2/tables/{id}` existiert und ist der günstigste Metadatenaufruf.** Die
Einzeltabellenroute liegt in der OCS-Generation, läuft über `TableService::find` mit
Enhancement und liefert daher `rowsCount`, `columnsCount`, `isShared`, `onSharePermissions`,
`title`, `ownership`, `archived` und `favorite` in einem Request. Damit sind die
Kappungsmarkierung von TABLES-01 und die Schreibrecht-Vorprüfung von TABLES-02 aus derselben
Antwort bedient, und `tables_create_row` braucht anders als `deck_create_card` nicht die ganze
Tabellenliste zu holen. [VERIFIED: openapi.json, lib/Controller/ApiTablesController.php]

## Architekturmuster

### Systemarchitektur, Datenfluss dieser Phase

```
MCP-Client (Claude, Cursor, Agent)
        |
        |  tools/call: tables_browse | tables_create_row
        v
server/reg_tables.py   [NEU]        Schema, Literal-Enum level, READ_ONLY / CREATE_ONLY
        |  compact(), graceful()
        v
deps.resolve_clients(ctx)           Credential-Naht, unverändert (appapi | basic | bearer)
        |
        v
tools/tables.py        [NEU]
        |
        +--> capabilities.require_app(clients, "tables")   [Cache 60 s]
        |        |
        |        +--> GET /ocs/v2.php/cloud/capabilities  -> tables.enabled auswerten (nicht Präsenz)
        |
        +-- level=tables ---> clients.tables.get_tables()
        |                        GET /ocs/v2.php/apps/tables/api/2/tables        parse_ocs
        |                        -> Projektion (id, title, rowsCount, columnsCount, isShared, ...)
        |
        +-- level=columns --> clients.tables.get_columns(table_id)
        |                        GET .../api/2/columns/table/{tableId}           parse_ocs
        |                        -> Projektion (id, title, type, subtype, mandatory, Grenzen)
        |
        +-- level=rows -----> clients.tables.get_table(table_id)   [rowsCount, Titel]
        |                     clients.tables.get_rows_simple(table_id, limit, offset)
        |                        GET /index.php/apps/tables/api/1/tables/{id}/rows/simple
        |                            ?limit=<immer gesetzt>&offset=            parse_app_json
        |                        -> Titelzeile abtrennen, Zeilen als Objekte, truncated + rowsCount
        |
        +-- create_row -----> clients.tables.get_table(table_id)   [Rechte-Vorprüfung, K5]
                              clients.tables.get_columns(table_id) [Titel -> Id, mandatory]
                              clients.tables.create_row(...)
                                 POST /ocs/v2.php/apps/tables/api/2/tables/{id}/rows
                                 Body {"data": {"<columnId>": <value>}}          parse_ocs (200!)
                                 -> {id, table_id, url, values_written}

Getrennter, blockierender Zweig (Plan 1, kein Produktionscode):

tests/integration/test_exapp_mail_reach.py  [NEU]
        |  Credentials(mode="appapi", secret=APP_SECRET)   kein App-Passwort im Prozess
        v
Nextcloud direkt (nicht über die ExApp, wie test_exapp_dav_matrix.py)
        |
        +--> GET /index.php/apps/mail/api/accounts
        +--> GET /index.php/apps/mail/api/mailboxes?accountId=N
        +--> GET /index.php/apps/mail/api/messages?mailboxId=N&limit=5
        +--> GET /ocs/v2.php/apps/mail/message/{id}
        |
        v
Protokoll: Statuscode + Content-Type + erste Zeichen des Körpers je Weg
        -> docs/spike-mail.md, Entscheidung für Phase 10
```

### Empfohlene Projektstruktur, nur die Deltas

```
src/mcp_connector/
├── nextcloud/
│   ├── capabilities.py              # GEÄNDERT: tables_available (enabled!), tables_api_versions, _MISSING-Eintrag
│   └── clients/
│       ├── ocs.py                   # GEÄNDERT: ocs_post (erster OCS-Schreibaufruf des Projekts)
│       └── tables.py                # NEU: api/2 (Tabellen, Spalten, Zeile anlegen) + api/1 (Zeilen lesen)
├── tools/
│   └── tables.py                    # NEU: browse(level), create_row
└── server/
    └── reg_tables.py                # NEU

tests/
├── contract/
│   ├── test_tool_surface.py         # GEÄNDERT: EXPECTED_TOOLS +2, CREATE_TOOLS +1, len == 18, Enum-Prüfung, README-Tabelle
│   └── test_no_destructive_calls.py # GEÄNDERT: FORBIDDEN-Nadeln für die Tables-Schreibrouten
├── integration/
│   ├── test_exapp_mail_reach.py     # NEU (Spike, blockierend)
│   └── test_tables_roundtrip.py     # NEU (Vorbild test_deck_roundtrip.py)
└── unit/
    ├── test_tables_client.py        # NEU (respx)
    └── test_tables_tools.py         # NEU

scripts/
├── bootstrap_exapp.sh               # GEÄNDERT: ensure_app tables, ensure_app mail, optional Mail-Konto
├── check_tool_budget.py             # GEÄNDERT: BUDGET_BYTES plus neue Messzeile
└── acceptance_all_tools.py          # GEÄNDERT: EXPECTED_TOOLS 15 -> 18 (Altlast aus dem v1.1-Audit)

docs/spike-mail.md                   # NEU (Vorbild docs/spike-dav.md)
README.md / README.de.md / README.fr.md   # GEÄNDERT: Tool-Tabelle, Toolzahl
CHANGELOG.md                         # GEÄNDERT: nutzerrelevante Änderung
compose.exapp.yml                    # OPTIONAL: greenmail-Dienst (nur Spike-Stufe 2)
```

`appinfo/info.xml` bleibt in dieser Phase unverändert: der Store-Text nennt die Familien
namentlich, aber die Fassung geht erst in Phase 11 (EXAPP-07) in den Store, und ein Store-Text,
der Talk und Mail schon nennt, wäre bis dahin unwahr. Die Aufnahme von "tables" in den
Store-Text ist damit eine Phase-11-Zeile. Der Contract-Test prüft `info.xml` nicht.

### Muster 1: Ein Browse-Tool mit `level`-Enum

**Was:** `tables_browse(level="tables"|"columns"|"rows")` statt drei Tools.
**Wann:** immer bei einer Hierarchie (D-06, für Deck entschieden).
**Wie in dieser Codebasis:** `Literal[...]` im Registrierungsmodul erzeugt das `enum` im
Input-Schema; das Tool prüft `level not in LEVELS` und antwortet mit `_LEVEL_HINT`. Der
Contract-Test prüft die Enum-Werte wörtlich, siehe `test_the_two_deck_tools_are_listed_and_browse_takes_an_enum_level`.

```python
# tools/tables.py, Muster aus tools/deck.py
LEVELS = ("tables", "columns", "rows")
DEFAULT_LIMIT = 25          # TABLES-01
MAX_LIMIT = 200             # TABLES-01

if level not in LEVELS:
    raise ToolError(message=f"{level!r} is not a Tables level.", hint=_LEVEL_HINT)
capped = min(max(limit, 1), MAX_LIMIT)
await capabilities.require_app(clients, APP)
```

### Muster 2: `require_app` als erste Zeile

Unverändert übernehmen. `tools/list` bleibt statisch (SRV-04), auch auf einer Instanz ohne
Tables. Neu ist nur, dass `capabilities.parse` für Tables **`enabled` auswertet und nicht die
Präsenz der Sektion**.

### Muster 3: Freiform-Feld als String, nicht als Dict

`tables_create_row(values: str)` mit kompaktem JSON. Ein `dict`-Parameter zieht
`additionalProperties` oder `$defs` ins Schema, und `test_tool_surface.py` verbietet `$defs`
an mehreren Stellen wörtlich. Präzedenzfall in der Codebasis: `unified_search.providers` ist
ein Komma-String. Durch K4 passt der String bis in den HTTP-Body, ohne dass eine zweite Form
entsteht.

Der Parsefehler muss ein Satz mit Beispiel sein, kein `JSONDecodeError`:

```python
try:
    parsed = json.loads(values)
except json.JSONDecodeError:
    raise ToolError(
        message="values is not valid JSON.",
        hint='Pass an object of column titles and values, for example {"Task": "Call back", "Done": false}.',
    ) from None
if not isinstance(parsed, dict):
    raise ToolError(message="values must be a JSON object, not a list.", hint=...)
```

### Muster 4: Der Schreibpfad prüft die Berechtigung des Objekts

Vorbild `tools/deck.py::_require_write_permission`. Für Tables mit der Korrektur K5:

```python
def _may_create(table: dict[str, Any]) -> bool:
    """Own tables report only ``read`` in onSharePermissions, yet the owner may write.

    ``TableService::setIsSharedState`` sets ``Permissions(read: true)`` for a table the caller
    owns, and Nextcloud's own check short circuits on ownership before it ever looks at that
    object. Reading ``create`` alone would refuse every user on their own table.
    """
    permissions = table.get("onSharePermissions")
    permissions = permissions if isinstance(permissions, dict) else {}
    if not table.get("isShared"):
        return True
    return bool(permissions.get("create") or permissions.get("manage"))
```

### Muster 5: Positive Behauptung, wo ein Denylist-Gate blind ist

Für Tables ist die blinde Stelle nicht ein schreibender Vorgabeparameter wie bei Talk, sondern
das **fehlende** `limit`. Ein Test, der nur die geparste Antwort prüft, sieht es nicht. Der
Test muss die gebaute URL prüfen:

```python
# tests/unit/test_tables_client.py
route = respx.get(url__regex=r".*/api/1/tables/7/rows/simple.*").mock(...)
await tables.get_rows_simple(client, creds, 7, limit=25, offset=0)
assert "limit=25" in str(route.calls.last.request.url)
```

Zusätzlich, wie in der Kernrecherche vorgeschlagen: ein eingefrorenes Literal über die
Pfad-Konstanten des neuen Clients, damit eine Route, die niemand verboten hat, nicht
unbemerkt dazukommt.

### Muster 6: Projektion statt Durchreichen

`GET /api/2/tables` liefert je Tabelle unter anderem `views` (ganze View-Objekte mit Filtern
und Sortierungen), `columnOrder`, `sort`, `createdBy`, `lastEditBy`, `ownerDisplayName`. Das ist
Payload, den niemand liest. Projektion (Vorbild `tools/deck.py::_boards`):

- `level=tables`: `id`, `title`, `rowsCount`, `columnsCount`, `isShared`, `can_create` (aus K5), plus `emoji` nur wenn gesetzt; archivierte Tabellen filtern (wie Deck `archived`/`deletedAt`)
- `level=columns`: `id`, `title`, `type`, `subtype`, `mandatory`, plus die interpretationsnötigen Grenzen je Typ (`selectionOptions`, `textMaxLength`, `numberMin`, `numberMax`, `numberDecimals`, `datetimeDefault`)
- `level=rows`: die Titelzeile wird zu Schlüsseln, nicht wiederholt; Antwort trägt `rowsCount`, `count`, `offset`, `truncated`

### Anti-Muster in dieser Phase

- **Ein Tool pro Ebene** (`tables_list_tables`, `tables_list_rows`, ...): der Contract-Test hat für Deck schon eine Verbotsliste; Tables braucht dieselbe (`tables_list_tables`, `tables_list_columns`, `tables_list_rows`, `tables_read_row`).
- **Zeilen ohne `limit` lesen:** liest die ganze Tabelle. `limit` gehört in den Client, nicht ins Tool.
- **`nodeType` und `nodeCollection` verwechseln:** Singular ohne s beim Spaltenaufruf, Plural mit s beim Anlegen (K3).
- **Auf 201 testen:** `createRow` antwortet 200 (`DataResponse` ohne Statusargument, openapi listet nur 200).
- **Einen `Origin`-Header senden:** alle v1-Routen tragen `#[CORS]`; mit `Origin` verlangt Nextclouds CORS-Middleware eine Basic-Reauthentifizierung, die unter Impersonation nicht existiert. Der bestehende Client sendet keinen, das muss so bleiben.
- **Retry auf dem POST:** eine doppelte Zeile ist Datenkorruption, die dieser Server nicht aufräumen kann (DELETE ist per Gate verboten). Ein Versuch, die Antwort trägt die neue Zeilen-Id, und die Tool-Beschreibung sagt, dass ein Timeout nicht bedeutet, dass nichts geschrieben wurde.
- **Die Rohantwort der Tabellenliste durchreichen:** siehe Muster 6.

## Tables-API-Referenz (verifiziert gegen Tables 2.2.2)

### Routen

| Zweck | Methode und Pfad | Parser | Bemerkung |
|-------|------------------|--------|-----------|
| Tabellen listen | `GET /ocs/v2.php/apps/tables/api/2/tables` | `parse_ocs` | keine Query-Parameter; Antwort ist eine Liste von `Table` |
| Eine Tabelle | `GET /ocs/v2.php/apps/tables/api/2/tables/{id}` | `parse_ocs` | liefert `rowsCount`, `isShared`, `onSharePermissions`, `title` (K11) |
| Spalten | `GET /ocs/v2.php/apps/tables/api/2/columns/table/{tableId}` | `parse_ocs` | `nodeType` ist `table` oder `view`, Singular (K3) |
| Zeilen, kompakt | `GET /index.php/apps/tables/api/1/tables/{tableId}/rows/simple?limit=&offset=` | `parse_app_json` | erste Liste sind die Titel, keine Row-Ids (K8) |
| Zeilen, vollständig | `GET /index.php/apps/tables/api/1/tables/{tableId}/rows?limit=&offset=` | `parse_app_json` | Liste von `Row` mit `data: [{columnId, value}]` |
| Zeile anlegen | `POST /ocs/v2.php/apps/tables/api/2/tables/{tableId}/rows` | `parse_ocs` | `nodeCollection` ist `tables` oder `views`, Plural (K3); Antwort 200 |

Es gibt unter `api/2` **keine** Route, die Zeilen einer Tabelle liest; die einzige lesende
Zeilen-Route dort ist `public/{token}/rows` für Freigabelinks. [VERIFIED: openapi.json,
vollständige Pfadliste geprüft]

### Wichtige Antwortfelder

`Table` (Pflichtfelder laut `openapi.json`): `id`, `title`, `emoji`, `ownership`,
`ownerDisplayName`, `createdBy`, `createdAt`, `lastEditBy`, `lastEditAt`, `archived`,
`favorite`, `isShared`, `onSharePermissions` (nullable, `{read, create, update, delete,
manage}`), `hasShares`, `rowsCount`, `description`, `views`, `columnsCount`, `columnOrder`,
`sort`.

`Column`: `id`, `uuid`, `title`, `technicalName`, `tableId`, `type`, `subtype`, **`mandatory`**,
`description`, `orderWeight`, plus typabhängige Felder (`numberDefault`, `numberMin`,
`numberMax`, `numberDecimals`, `numberPrefix`, `numberSuffix`, `textDefault`,
`textAllowedPattern`, `textMaxLength`, `textUnique`, `selectionOptions`, `selectionDefault`,
`datetimeDefault`, `usergroup*`, `showUserStatus`, `viewColumnInformation`, `customSettings`).
`mandatory` ist die Grundlage für die Pflichttitel-Prüfung aus TABLES-02.

`Row`: `id`, `tableId`, `createdBy`, `createdAt`, `lastEditBy`, `lastEditAt`, `data`,
`dataByAlias`. `data` ist in Wahrheit eine **Liste** von `{columnId, value}` (das
`openapi.json` beschreibt es fälschlich als Objekt); `dataByAlias` ist leer, solange keine
Aliase konfiguriert sind.

`capabilities.tables`: `{enabled, version, apiVersions, features, isCirclesEnabled,
column_types}`. Gate: `enabled` auswerten, `"1.0"` und `"2.0"` in `apiVersions` erwarten. Kein
Gate auf `version`.

### Titel-zu-Id-Abbildung (TABLES-02)

Ablauf im Tool, bevor irgendetwas geschrieben wird:

1. `values` als JSON-Objekt parsen (Muster 3), Schlüssel sind Spaltentitel.
2. Spalten holen, Abbildung Titel zu Id bauen. **Vergleich normalisiert** (getrimmt, casefold), damit "Task" und "task " denselben Treffer finden.
3. **Mehrdeutig:** derselbe normalisierte Titel kommt bei mehreren Spalten vor. Ablehnen und die betroffenen Titel plus Ids nennen. Tables erlaubt doppelte Spaltentitel, deswegen ist das ein realer Fall und kein theoretischer.
4. **Unbekannt:** ein Schlüssel hat keine Spalte. Ablehnen mit der Liste der gültigen Titel.
5. **Fehlende Pflichtspalte:** eine Spalte mit `mandatory: true` fehlt in `values`. Ablehnen mit ihrem Titel.
6. Erst danach `POST`, mit `{"data": {"<columnId>": value}}`.

Die Werteform je `type`/`subtype` ist die wahrscheinlichste Ursache für einen 400 und in der
App nicht vollständig dokumentiert. Empfehlung: **keine clientseitige Typvalidierung bauen**,
sondern den 400 der App mit ihrer eigenen Meldung durchreichen (`_status_error` hängt
"Nextcloud says: ..." an) und die zwei Formen, die im Test verifiziert wurden, in der
Tool-Beschreibung nennen. Ein selbstgebauter Typvalidator wäre eine zweite Wahrheit, die bei
jedem neuen `column_type` veraltet. [ASSUMED für die Wertformen jenseits von `text` und
`number`, siehe Assumptions Log A2]

## Mail-Spike: Messplan (MAIL-04)

### Was gemessen wird und warum genau das

Die offene Frage ist **nicht**, ob Mail funktioniert, sondern ob eine impersonierte Anfrage
Mails Controller überhaupt **erreicht**. Der Mechanismus ist im Serverquellcode belegt
(`Request::passesCSRFCheck()` gibt `true` zurück, sobald der Header `OCS-APIRequest` gesetzt
ist, und dieses Projekt sendet ihn per D-18 auf jedem Request), aber Mail ist die erste Familie,
deren Listen-Routen **kein** `#[NoCSRFRequired]` tragen. Alle drei Controller tragen
`#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]` auf Klassenebene und `@NoAdminRequired` als
Docblock-Annotation an `index`. [VERIFIED: nextcloud/mail v5.11.1 lib/Controller/{Accounts,Mailboxes,Messages}Controller.php]

### Entscheidungskriterium, vorab festlegen

| Beobachtung | Bedeutung |
|-------------|-----------|
| JSON-Körper mit einem beliebigen Status (200, 206, 401, 403, 404, 500) | **Erreicht.** Nur App-Code produziert diese Körper; die CSRF- und Impersonations-Kette hat gehalten |
| HTML-Körper (`content-type: text/html` oder Körper beginnt mit `<`) | **Nicht erreicht.** Das ist die Loginseite, die `ocs._json_payload` schon heute namentlich benennt |
| 3xx mit `Location`, die `/login` enthält | **Nicht erreicht**, Authentifizierung ist gescheitert (nicht die Basis-URL, siehe Pitfall 9 der Kernrecherche) |
| 3xx auf etwas anderes | Topologie- oder Basis-URL-Problem, Messung wiederholen |

Damit ist das Ergebnis auch dann eindeutig, wenn kein IMAP-Server erreichbar ist, und genau
das macht Stufe 1 möglich.

### Stufe 1 (empfohlener Start, kein IMAP nötig)

Voraussetzungen: `occ app:install mail`, ein Mail-Konto für den Testnutzer, das auf einen
nicht existierenden IMAP-Host zeigt. Das geht, weil `occ mail:account:create-imap` die
Verbindung **nicht** prüft, sondern das Konto nur speichert. [VERIFIED: nextcloud/mail v5.11.1
lib/Command/CreateImapAccount.php]

```bash
docker compose -p nc-mcp-exapp -f compose.exapp.yml exec -T -u www-data nextcloud \
  php occ mail:account:create-imap alice "Alice Spike" alice@example.test \
  imap.invalid 143 none alice s3cret-imap-pw \
  smtp.invalid 25 none alice s3cret-imap-pw password
```

Erwartete Messwerte (Prognose, die der Test bestätigen oder widerlegen soll):

| Weg | Erwartung ohne IMAP | Begründung |
|-----|---------------------|------------|
| `GET /index.php/apps/mail/api/accounts` | 200, JSON-Liste mit einem Konto | `AccountsController::index` liest nur die Datenbank und serialisiert das Konto |
| `GET /index.php/apps/mail/api/mailboxes?accountId=N` | 500 mit JSON (oder 200 mit leerer Liste, falls Horde den Fehler schluckt) | `getMailboxes` erzwingt einen Sync gegen IMAP (K7); `#[TrapError]` macht daraus JSON |
| `GET /index.php/apps/mail/api/messages?mailboxId=0&limit=5` | 403 mit JSON `[]` | kein Postfach vorhanden, `DoesNotExistException` wird zu 403 |
| `GET /ocs/v2.php/apps/mail/message/999999` | 404 im OCS-Envelope, Text "Account not found." | `messageApi#get` findet die Nachricht nicht |

Alle vier Erwartungen sind "erreicht" nach dem Kriterium oben. Der Test darf deshalb **nicht**
auf Statuscode 200 prüfen, sondern muss Statuscode, `content-type` und die ersten Zeichen des
Körpers je Weg protokollieren und nur die HTML- und Login-Redirect-Fälle als Fehlschlag
werten.

**Vorsicht Brute-Force:** `messageApi#get` trägt `#[BruteForceProtection('mailGetMessage')]`,
und Nextcloud zählt pro Quell-IP; für eine ExApp ist das eine IP für alle Nutzer. Der Spike
darf genau **einen** 404-Versuch machen, nie eine Schleife. Auf der lokalen Topologie ist der
Schutz zwar per Bootstrap abgeschaltet (`DISABLE_BRUTEFORCE=1`), aber die Regel gehört in den
Test, nicht in die Topologie, weil sie in Phase 10 in Produktionscode wandert.

### Stufe 2 (nur bei uneindeutigem Ergebnis oder als Vorarbeit für Phase 10)

GreenMail als vierter Dienst in `compose.exapp.yml`, danach ein echtes Konto, ein
eingeliefertes Testmail und `occ mail:account:sync <id> -f`. Erst dann liefern alle vier Wege
200 mit echten Feldern, und die Envelope- und Volltextformen für Phase 10 sind gemessen statt
angenommen.

```yaml
  greenmail:
    image: greenmail/standalone:2.1.12
    environment:
      GREENMAIL_OPTS: >-
        -Dgreenmail.setup.test.all
        -Dgreenmail.hostname=0.0.0.0
        -Dgreenmail.auth.disabled
        -Dgreenmail.users=alice:alice-imap-pw@example.test
    networks: [nc-mcp-exapp-net]
```

Konto dann gegen `greenmail` Port 3143, `imapSslMode` `none`. Einliefern eines Testmails über
SMTP 3025 (drei Zeilen `smtplib` in einem Setup-Schritt) oder über die GreenMail-API auf 8080.
Danach `occ mail:account:sync`, weil die Nachrichtenliste den lokalen Cache liest und nicht
IMAP (Kernrecherche, Frische-Absatz).

### Wo das SCOPE_IGNORE-Risiko dokumentiert wird (Erfolgskriterium 2)

In Phase 8 existiert **kein Produktionscode**, der Mail-Routen aufruft; das Client-Modul kommt
erst in Phase 10. "Im Code an der Stelle, die diese Routen aufruft" ist in dieser Phase also
das Spike-Testmodul. Empfehlung:

1. Modul-Docstring von `tests/integration/test_exapp_mail_reach.py`: die vier Wege, welcher davon `SCOPE_IGNORE` ist, und der Satz, dass die Listen-Routen ersetzbar bleiben müssen.
2. Eine benannte Konstante je interne Route, damit die Zeichenketten an einer Stelle stehen und Phase 10 sie übernehmen kann.
3. `docs/spike-mail.md` nach dem Vorbild `docs/spike-dav.md`: Messtabelle mit Datum, Versionen (NC 34.0.3, AppAPI 34.0.0, Mail 5.11.1), Statuscodes, Antwortformen, Entscheidung, und der ausdrückliche Ersetzbarkeits-Hinweis (Discovery über den Suchprovider `mail` plus OCS-Volltext ist der Ausweg, wenn eine Mail-Version die internen Routen bricht).
4. Ein Satz im Plan, der die Wiederholung dieses Hinweises im künftigen `clients/mail.py` an Phase 10 übergibt.

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Titelzeile plus Werte zu Zeilen zusammensetzen | Eigene Spalten-Join-Logik über `data: [{columnId, value}]` | `rows/simple`, dessen erste Zeile die Titel sind | Ein Request weniger, keine Reihenfolgeannahme, die App macht die Zuordnung |
| Berechtigungslogik für Zeilen-Anlegen | Eigene Rechteauswertung aus Shares | `isShared` plus `onSharePermissions` lesen (K5), letzte Instanz bleibt Nextclouds `RequirePermission` | Die Middleware ist die Wahrheit; unser Check ist nur die bessere Fehlermeldung |
| Statuscodes auf Sätze abbilden | Neue Fehlerbehandlung im Tables-Client | `ocs.parse_ocs` und `ocs.parse_app_json` plus `_status_error` | Eine Stelle für alle Familien; Mail bringt in Phase 10 zwei neue Fälle dazu (206, 404-als-Auth) |
| Cursor-Handles | Eigene Offset-Kodierung | `paging.encode_cursor` / `decode_cursor` / `read_offset` / `check_scope` | Der Codec ist generisch und stateless; `check_scope` verhindert, dass ein Handle einer anderen Tabelle angewendet wird |
| Wertformate je Spaltentyp validieren | Eigener Typvalidator aus `column_types` | Den 400 der App mit ihrer Meldung durchreichen | Zweite Wahrheit, die bei jedem neuen Spaltentyp veraltet |
| IMAP sprechen | `imaplib`, `imapclient` | Nichts davon; Mail-Routen über HTTP, IMAP nur als Testdienst | Würde die Mail-App und ihre Berechtigungen umgehen |
| Truncation markieren | Eigenes Feldschema | `_envelope`-Muster aus `tools/deck.py` plus `rowsCount` | Ein Antwortformat über alle Familien |

## Häufige Fallen in dieser Phase

### Falle 1: `limit` weglassen liest die ganze Tabelle

**Was schiefgeht:** `limit` und `offset` sind `nullable: true`; ohne `limit` liefert
`findAllByTable` alle Zeilen. Eine Tabelle mit 20.000 Zeilen wird eine MCP-Antwort.
**Warum:** Der Parameter sieht optional aus, und der Test mit drei Zeilen fällt nie auf.
**Vermeidung:** `limit` im Client erzwingen (nicht im Tool), Kappung markieren, und den Test
gegen die **URL** schreiben, nicht gegen das Ergebnis.
**Frühwarnzeichen:** eine Zeilen-URL im Log ohne `limit=`.

### Falle 2: Der Eigentümer wird auf seiner eigenen Tabelle abgewiesen

Siehe K5. **Frühwarnzeichen:** der erste Integrationstest von `tables_create_row` scheitert mit
dem eigenen Fehlersatz, obwohl der Nutzer die Tabelle selbst angelegt hat. Wer dann das Gate
lockert statt die Regel zu korrigieren, verliert die Vorprüfung ganz.

### Falle 3: `nodeType` gegen `nodeCollection`

Siehe K3. Ein 404 aus der Routing-Schicht sieht wie "Tabelle nicht gefunden" aus und führt zur
falschen Fehlersuche. **Vermeidung:** zwei benannte Konstanten im Client, deren Kommentar den
Unterschied nennt, plus ein eingefrorenes URL-Literal im Test.

### Falle 4: Auf 201 prüfen

`createRow` antwortet 200. Ein Test auf 201 ist rot gegen eine korrekt arbeitende Instanz.

### Falle 5: Doppelte Zeile durch Retry

Kein Retry auf dem POST, auf keiner Schicht. Die Antwort trägt die neue Zeilen-Id, damit das
Modell nachlesen statt wiederholen kann. Der Satz "ein Timeout bedeutet nicht, dass nichts
geschrieben wurde" gehört in die Tool-Beschreibung. Aufräumen ist unmöglich: DELETE ist per
Gate verboten.

### Falle 6: Das Budget-Gate wird zur Dekoration

Aktuelle Messung: **11268 Bytes, 16 Tools, Gate 12500** [VERIFIED: `uv run python
scripts/check_tool_budget.py`, heute gelaufen]. Freiraum: 1232 Bytes. Die Schätzung der
Kernrecherche für die zwei neuen Tools ist 790 plus 520, also rund 1310 Bytes. **Das Gate
reisst in dieser Phase.** Es muss in demselben Commit angehoben werden, der die Tools bringt,
mit einer neuen datierten Messzeile im Skriptkommentar, wie die Regel dort es verlangt.
Empfehlung: Messung plus 15 Prozent, aufgerundet auf die nächsten 500 (das ist die Formel, die
TOOL-15 für den Meilenstein-Endstand festschreibt, und das Vorgehen des bestehenden Eintrags),
**plus** die zweite Behauptung, die die Aggregatzahl nicht hat: kein einzelnes Tool über 1400
Bytes. Der heutige Ausreisser `calendar_create_event` liegt mit 1351 knapp darunter, ein neues
Tool mit Absatzbeschreibung fällt darüber, und genau das ist die Regression, die eine
Gesamtzahl mit Luft nie meldet.

### Falle 7: Die eingefrorenen Testliterale werden nicht vollständig nachgezogen

`tests/contract/test_tool_surface.py` prüft an **fünf** Stellen gegen feste Zahlen und Mengen
(`EXPECTED_TOOLS`, `CREATE_TOOLS`, `len(tools) == 16`, README-Tabelle, Toolzahlen in `docs/`).
Vollständige Liste im Abschnitt "Mechanische Checkliste". Ein vergessener Punkt macht die Phase
rot, aber an einer Stelle, die nichts mit Tables zu tun hat.

### Falle 8: Der Spike wird auf 200 statt auf "App-Code hat geantwortet" geprüft

Siehe Entscheidungskriterium. Ein Spike, der ohne IMAP-Server auf 200 prüft, meldet "Mail
unerreichbar" und kippt damit fälschlich den Schnitt der Phasen 10 und 11.

## Mechanische Checkliste (exakte Anknüpfungspunkte)

Diese Liste ist der Grund, warum Tables vor Talk und Mail liegt: sie einmal an der risikolosen
Familie durchzuspielen macht die beiden schwierigen Phasen kürzer.

### Produktionscode

| Datei | Änderung |
|-------|----------|
| `src/mcp_connector/nextcloud/clients/tables.py` | NEU. Vorbild `clients/deck.py`: Modul-Docstring mit den Pflichtheadern (D-18), `SUPPORTED_*`-Konstanten je Generation, `api_url`-Helfer je Generation, `web_url`, `_path_id` (numerisch, `isdigit`), erzwungenes `limit` |
| `src/mcp_connector/nextcloud/clients/ocs.py` | `ocs_post` dazu (K9): beide Pflichtheader plus `Content-Type: application/json`, `auth=creds.auth()` pro Aufruf, kein `Origin`, keine Redirect-Folge |
| `src/mcp_connector/nextcloud/capabilities.py` | `Capabilities`: `tables_available` (aus `tables.enabled`, **nicht** Präsenz), `tables_api_versions`; `has()`-Dictionary um `"tables"` erweitern; `_MISSING["tables"]` mit einem Satz plus einer Sache, die der Nutzer tun kann; `parse()` entsprechend |
| `src/mcp_connector/tools/tables.py` | NEU. `LEVELS`, `DEFAULT_LIMIT = 25`, `MAX_LIMIT = 200`, `browse`, `create_row`, `_envelope`, `_may_create` (K5), Titel-zu-Id-Abbildung |
| `src/mcp_connector/server/reg_tables.py` | NEU. Vorbild `reg_deck.py`: `Literal["tables","columns","rows"]`, leere Strings statt `None`, `structured_output=False`, `READ_ONLY` / `CREATE_ONLY`, `@graceful`, `compact(...)` |
| `src/mcp_connector/ids.py` | **Unverändert** (K8: keine adressierbare Zeile in dieser Phase) |
| `src/mcp_connector/provider_map.py` | **Unverändert.** `tables-search-tables` trägt die Id im URL-Fragment, nicht im Pfad; der ehrliche Ausgang bleibt `kind=url`, `resolvable: false` (TOOL-16, Phase 11) |
| `src/mcp_connector/tools/context.py` | **Unverändert** (Phase 11) |

### Tests

| Datei | Änderung |
|-------|----------|
| `tests/contract/test_tool_surface.py` | `EXPECTED_TOOLS` plus `tables_browse`, `tables_create_row`; `CREATE_TOOLS` plus `tables_create_row`; `len(tools) == 16` auf 18; ein neuer Test für das Level-Enum und die Abwesenheit von `$defs`; eine Verbotsliste `tables_list_tables`/`tables_list_columns`/`tables_list_rows`/`tables_read_row` analog `test_there_is_no_tool_per_deck_level`. Achtung: der Docstring von `test_the_curated_set_is_complete_...` nennt die Zahl ebenfalls, und `test_no_input_schema_accepts_a_user_parameter` hat sie in einer Assertion-Meldung |
| `tests/contract/test_no_destructive_calls.py` | `FORBIDDEN`-Nadeln für die Tables-Schreibrouten, die **kein** verbotenes Verb brauchen: `apps/tables/api/1/rows` (Einzelzeile lesen, ändern, löschen), `apps/tables/api/1/columns`, `tables/scheme` (Import), `/transfer`, sowie die Share-Route (`{nodeCollection}/{nodeId}/share`). Dazu je eine Gegenprobe, wie die drei bestehenden Ausnahmen sie haben |
| `tests/unit/test_tables_client.py` | NEU, `respx`. Muss enthalten: URL trägt immer `limit`; `nodeType` Singular und `nodeCollection` Plural als eingefrorene Literale; `parse_app_json` gegen `{"message": ...}` mit 403; `createRow` mit Status 200; leere Tabelle (`no_data`); nicht numerische `table_id` wird vor dem Request abgelehnt |
| `tests/unit/test_tables_tools.py` | NEU. Level-Validierung, Kappung (Default 25, Max 200, `truncated`, `rowsCount`), Titel unbekannt, Titel mehrdeutig, Pflichttitel fehlt, `values` kein JSON, `values` eine Liste, eigene Tabelle darf schreiben (K5), fremde Tabelle ohne `create` wird abgelehnt |
| `tests/integration/test_tables_roundtrip.py` | NEU, Marker `integration`. Vorbild `test_deck_roundtrip.py`: Tabelle und Spalten als Setup anlegen (die Tools können das nicht, also direkte POSTs mit denselben Credentials, wie `_ensure_board_with_stack` es macht), dann Zeile über das Tool anlegen und über `browse(level="rows")` zurücklesen |
| `tests/integration/test_exapp_mail_reach.py` | NEU, Marker `integration`. Vorbild `test_exapp_dav_matrix.py` inklusive **beider Kontrollprüfungen** (kein App-Passwort und kein statischer Bearer im Prozess, falsches `APP_SECRET` wird abgewiesen); ohne sie beweist eine grüne Matrix nichts |
| `tests/unit/test_ocs_capabilities.py` | Um `tables.enabled` erweitern, inklusive des Falls `enabled: false` bei vorhandener Sektion |
| `tests/fixtures/` | Neue Fixtures: `tables_tables.json`, `tables_columns.json`, `tables_rows_simple.json` (Vorbild `deck_boards.json`) |

### Skripte, Doku, Topologie

| Datei | Änderung |
|-------|----------|
| `scripts/check_tool_budget.py` | `BUDGET_BYTES` anheben, neue datierte Messzeile im Kommentarblock, optional die Pro-Tool-Behauptung (max. 1400 Bytes) |
| `scripts/acceptance_all_tools.py` | `EXPECTED_TOOLS = 15` auf 18. Das ist die im v1.1-Audit notierte Altlast (Modul-Docstring und Zeile 16 nennen die Zahl ebenfalls); `docs/conference-demo.md` beschreibt die Fehlermeldung dieses Skripts wörtlich |
| `scripts/bootstrap_exapp.sh` | `ensure_app tables` und `ensure_app mail` neben den bestehenden `ensure_app notes` / `ensure_app deck` (Zeilen 849 und 850); für den Spike zusätzlich das Mail-Konto anlegen (idempotent, wie der Rest des Skripts) |
| `scripts/bootstrap_test_nc.sh` | `ensure_app tables` (Zeilen 159 und 160), damit die App-Passwort-Integrationsschicht Tables ebenfalls sieht |
| `README.md` | Tool-Tabelle um zwei Zeilen (`| \`tables_browse\` | read | ... |`, `| \`tables_create_row\` | create-only | ... |`); die Sätze "The 16 tools" in Zeile 19 und "All 16 tools" in Zeile 30 |
| `README.de.md`, `README.fr.md` | Dieselben zwei Tabellenzeilen und Zahlen (Zeilen 21 und 32 bzw. 21 und 34). Dreisprachigkeitsregel, und das Vokabular-Gate gilt für die deutschen und französischen Texte |
| `docs/client-setup.md` | "16 tools" an drei Stellen (Zeilen 11, 74, 431). Achtung: Zeile 431 ist ein **datierter Messwert** eines Laufs; nach der Regel im Contract-Test darf er bleiben, wenn die Seite auf `tests/contract/test_tool_surface.py` zeigt |
| `docs/conference-demo.md` | `tools=16` (Zeile 140) und die Beispielmeldung des Acceptance-Skripts (Zeile 271) |
| `CHANGELOG.md` | Nutzerrelevante Änderung: Tables lesen und Zeile anlegen |
| `docs/spike-mail.md` | NEU, Vorbild `docs/spike-dav.md` |
| `compose.exapp.yml` | Nur für Spike-Stufe 2: GreenMail-Dienst |
| `appinfo/info.xml` | **Unverändert in dieser Phase** (Store-Text erst in Phase 11, EXAPP-07) |

Die Regel des Contract-Tests für Toolzahlen in `docs/` ist wörtlich: eine Seite, die eine
andere Zahl als die aktuelle nennt, muss auf `tests/contract/test_tool_surface.py` zeigen.
Datierte Messwerte alter Läufe dürfen also stehenbleiben, wenn dieser Zeiger auf der Seite
steht.

## Codebeispiele

### Client: erzwungenes `limit`, zwei Generationen, ein Modul

```python
# src/mcp_connector/nextcloud/clients/tables.py  (Skizze, Muster aus clients/deck.py)

#: Row reads live in generation 1 only: generation 2 has no route that reads the rows of a
#: table (verified against the app's own openapi.json). Row creation lives in generation 2.
V1_PREFIX = "/index.php/apps/tables/api/1"
V2_PREFIX = "/apps/tables/api/2"          # below /ocs/v2.php, built through ocs.ocs_url

#: Two spellings in one app: the columns route takes the singular word, the row create route
#: takes the plural one. Mixing them up yields a 404 from the routing layer, not from the app.
NODE_TYPE_TABLE = "table"                 # GET /api/2/columns/{nodeType}/{nodeId}
NODE_COLLECTION_TABLES = "tables"         # POST /api/2/{nodeCollection}/{nodeId}/rows

#: Never build a rows URL without it: limit and offset are nullable in the API, and leaving
#: the limit out returns every row of the table.
MAX_ROWS = 200


async def get_rows_simple(
    client: httpx.AsyncClient,
    creds: Credentials,
    table_id: str | int,
    *,
    limit: int,
    offset: int = 0,
) -> list[list[Any]]:
    """Read rows in the compact form: the first list holds the column titles.

    ``limit`` is a keyword without a default on purpose (pitfall 7b).
    """
    table = _path_id(table_id, "table id")
    capped = min(max(int(limit), 1), MAX_ROWS)
    response = await client.get(
        f"{creds.base_url}{V1_PREFIX}/tables/{table}/rows/simple",
        params={"limit": capped, "offset": max(int(offset), 0)},
        headers=dict(TABLES_HEADERS),
        auth=creds.auth(),
    )
    payload = ocs.parse_app_json(response, what=f"the rows of table {table}")
    return _as_rows(payload)
```

### OCS-Schreibnaht

```python
# src/mcp_connector/nextcloud/clients/ocs.py  (neu, neben ocs_get)

async def ocs_post(
    client: httpx.AsyncClient,
    creds: Credentials,
    path: str,
    json_body: Mapping[str, Any],
) -> httpx.Response:
    """POST to an OCS endpoint. The first write this project makes over OCS.

    Same rules as ``ocs_get``: both mandatory headers, authentication per request, redirects
    are never followed. No ``Origin`` header, ever: with one present Nextcloud's CORS
    middleware demands a basic reauthentication that does not exist under impersonation.
    """
    return await client.post(
        ocs_url(creds, path),
        json=dict(json_body),
        headers={**OCS_HEADERS, "Content-Type": "application/json"},
        auth=creds.auth(),
    )
```

### Spike: eine Messzeile statt einer Vermutung

```python
# tests/integration/test_exapp_mail_reach.py  (Skizze)

async def _probe(clients: NcClients, method: str, url: str) -> dict[str, str]:
    """One measured way. Records what came back instead of asserting a status code.

    A JSON body with any status proves the controller was reached; an HTML body or a redirect
    to /login proves it was not. That distinction is the whole point of MAIL-04, and it is
    the reason this helper does not assert 200: the listing routes touch IMAP, and an IMAP
    error is still app code answering.
    """
    response = await clients.client.request(
        method, url, headers=dict(ocs.OCS_HEADERS), auth=clients.creds.auth()
    )
    body = response.text.lstrip()
    return {
        "status": str(response.status_code),
        "content_type": response.headers.get("content-type", ""),
        "shape": "html" if body.startswith("<") else "json" if body[:1] in "[{" else "other",
        "location": response.headers.get("location", ""),
        "head": body[:120],
    }
```

Der Beweis besteht dann aus einem `assert` je Weg auf `shape == "json"` plus einer
Protokollausgabe, die wörtlich in `docs/spike-mail.md` wandert.

## Stand der Technik

| Alt | Aktuell | Seit | Bedeutung |
|-----|---------|------|-----------|
| Tables 1.0.x (NC 30-32) | Tables **2.2.2** (NC 33 bis 35) | 2026-08-19 | Auf NC 34 läuft die 2.x-Linie; die Route `nodeType` ist dort ein Wort, keine Zahl (K3) |
| Mail 5.10.x | Mail **5.11.1** (NC 32 bis 35) | 2026-08-20 | Drei OCS-Routen in `routes.php` plus `message/send` als Attribut (K1, K2) |
| AppAPI mit API-Scopes | AppAPI ohne Scopes | 3.2.0 (2024-09-10) | Kein `<scopes>`-Element, kein `--force-scopes`, `appinfo/info.xml` bleibt unberührt |
| `#[OpenAPI]` unbekannt | `SCOPE_DEFAULT` gegen `SCOPE_IGNORE` als Vertragsaussage | seit NC 28 verbreitet | Tables v1-Zeilen sind zugesagt (K10), Mails Listen sind es nicht |

**Veraltet oder irreführend:**
- Die Aussage der Tables-Wiki-Doku zum Row-Create-Format (Liste von `{columnId, value}`) ist falsch; korrekt ist ein Objekt oder ein JSON-String (nextcloud/tables#2237, K4).
- `openapi.json` beschreibt `Row.data` als Objekt; tatsächlich ist es eine Liste.
- `openapi.json` beschreibt die Antwort von `rows/simple` als `array of string`; tatsächlich ist es eine Liste von Listen (K8).

## Security Domain

`security_enforcement` ist in `.planning/config.json` nicht gesetzt, gilt damit als aktiv.

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Betroffen | Standardkontrolle in dieser Phase |
|----------------|-----------|-----------------------------------|
| V2 Authentication | nein (unverändert) | Die vier Credential-Modi bestehen; diese Phase führt keinen neuen Auth-Pfad ein (AppAPI ohne Scopes) |
| V3 Session Management | nein | Kein Zustand zwischen zwei Aufrufen; `paging`-Handles tragen keine Autorität |
| V4 Access Control | **ja** | Vorprüfung auf dem Objekt (K5), letzte Instanz ist Nextclouds `RequirePermission`; kein Update-, Delete- oder Schema-Pfad im Client; AST-Gate mit neuen Nadeln plus Gegenprobe |
| V5 Input Validation | **ja** | `_path_id` numerisch für jede Pfad-Id (T-01-63); `limit` gekappt im Client; `values` als JSON geparst und auf ein Objekt geprüft; Spaltentitel gegen die Serverliste geprüft, niemals geraten |
| V6 Cryptography | nein | Nichts Neues; kein Geheimnis in dieser Phase |
| V7 Error Handling und Logging | **ja** | Jeder Fehler ist ein Satz plus nächster Schritt aus `_status_error`; niemals Stacktrace, niemals HTML-Loginseite; die Rohantwort der App wird nie durchgereicht |
| V13 API und Web Service | **ja** | Kein `Origin`-Header; Redirects werden nicht gefolgt; alle URLs aus der konfigurierten Basis-URL gebaut (SSRF-Grenze) |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standard-Gegenmassnahme |
|--------|--------|-------------------------|
| Modellgesteuerte Pfad-Id (`table_id` aus einer Halluzination) | Spoofing, Information Disclosure | `_path_id`-Wächter, Ids nur aus `tables_browse`, Ablehnung vor dem Request |
| Doppelte Zeile durch Client-Retry | Tampering | Kein Retry auf dem POST, neue Zeilen-Id in der Antwort, Hinweis in der Tool-Beschreibung |
| Zugriff auf eine fremde Tabelle | Elevation of Privilege | Impersonation trägt die Nextcloud-ACL; der Zwei-Konten-Negativbeweis wird für Tables erweitert (`test_permission_fidelity_exapp.py`, Kernrecherche Security-Tabelle) |
| Ungekappte Zeilenmenge | Denial of Service (Kontextfenster und Nextcloud) | `limit` im Client erzwungen, Kappung markiert |
| Brute-Force-Sperre der ExApp-IP durch Id-Raten | Denial of Service | Im Spike genau ein 404-Versuch; die Regel "eine fehlgeschlagene Authentifizierung nie wiederholen" wird auf "einen 404 nie wiederholen" erweitert (Produktionscode dazu erst in Phase 10) |
| Fremder Text aus Tabellenzellen im Modellkontext | Tampering (Prompt Injection) | Zellwerte sind fremder Text: `marks.without_marks` auf jedes neue Freitextfeld, und Tabellenzeilen bekommen in Phase 11 bewusst **keinen** Auszug in `prepare_context` |
| Kontodaten der Mail-App im Modellkontext (Spike) | Information Disclosure | Der Spike protokolliert Statuscode, Content-Type und maximal 120 Zeichen des Körpers, nie die ganze Kontoantwort (sie enthält IMAP- und SMTP-Hostnamen) |

## Environment Availability

Gemessen am 2026-08-21 auf dem Entwicklungsrechner.

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Ausweg |
|--------------|---------------|-----------|---------|--------|
| Docker Engine | Integrationstests, Spike | ja | 29.5.2 (linux) | keiner nötig |
| HaRP-Topologie `nc-mcp-exapp` | Spike unter AppAPI-Impersonation | ja, läuft (NC 34.0.3, HaRP release, Registry, Caddy) | Container seit 26 h up und healthy | `docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait` plus `scripts/bootstrap_exapp.sh` |
| `.env.exapp` | Fixture `exapp_env` | ja, 32 Zeilen, enthält `APP_ID`, `APP_SECRET`, `APP_VERSION`, `NC_MCP_TEST_USER`, `NC_MCP_TEST_USER2`, `NC_MCP_TEST_APP_PASSWORD` | vom 2026-08-20 | Bootstrap neu laufen lassen |
| App `app_api` | Impersonation | ja | 34.0.0 | keiner |
| App `tables` | TABLES-01, TABLES-02 | **nein** | soll 2.2.2 | `occ app:install tables`, Store aus dem Container erreichbar (200 verifiziert) |
| App `mail` | MAIL-04 | **nein** | soll 5.11.1 | `occ app:install mail` |
| Mail-Konto für den Testnutzer | MAIL-04 Wege 2 bis 4 | nein | - | `occ mail:account:create-imap ...`, prüft die Verbindung nicht |
| IMAP-Server | Spike-Stufe 2, Feldformen für Phase 10 | nein | - | GreenMail 2.1.12 als Compose-Dienst; für Stufe 1 nicht nötig |
| App `spreed` | erst Phase 9 | nein | 24.0.4 verfügbar für NC 34 | ausserhalb dieser Phase |
| ExApp-Image im Registry | **nicht nötig für diese Phase** | vorhanden, aber Tag 0.1.2 | Repo steht auf 0.1.3 | Der Spike spricht Nextcloud direkt an, nicht die ExApp (wie `test_exapp_dav_matrix.py`); kein Rebuild nötig |
| `uv` | jedes Python-Kommando | ja | im Projekt etabliert | keiner (System-Python ist defekt) |

**Fehlende Abhängigkeiten ohne Ausweg:** keine.
**Fehlende Abhängigkeiten mit Ausweg:** `tables` und `mail` per `occ app:install` (idempotent
über `ensure_app` im Bootstrap-Skript); IMAP-Server nur für die optionale Spike-Stufe 2.

*Runtime State Inventory: entfällt. Diese Phase ist kein Rename, Refactor oder Migration; der
Zustand, der ausserhalb von git liegt (installierte Nextcloud-Apps, Mail-Konto), ist oben in
der Environment-Tabelle erfasst und wird im Bootstrap-Skript reproduzierbar gemacht.*

*Validation Architecture: entfällt, `workflow.nyquist_validation` ist in
`.planning/config.json` ausdrücklich `false`.*

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---------|-----------|---------------------|
| A1 | Die Prognosetabelle für Spike-Stufe 1 (200 / 500 / 403 / 404) trifft zu | Mail-Spike | Gering: der Test protokolliert, was kommt, und wertet nur HTML und Login-Redirect als Fehlschlag. Eine abweichende Zahl ist ein Messergebnis, kein Testfehler |
| A2 | Die Wertformate der Spaltentypen jenseits von `text` und `number` (Auswahl, Datum, Nutzergruppe) passen ohne clientseitige Umformung in den `data`-Body | Titel-zu-Id-Abbildung | Mittel: ein 400 der App mit ihrer eigenen Meldung; deshalb ausdrücklich keine Eigenvalidierung. Der Integrationstest sollte mindestens einen Auswahl- und einen Datumswert enthalten, damit die Lücke sichtbar wird |
| A3 | `dataByAlias` ist in der v1-Zeilenantwort leer, solange keine Aliase konfiguriert sind | Alternativen | Gering: die Abkürzung wird nicht benutzt; wäre sie doch gefüllt, wäre das nur ein späterer Optimierungspfad |
| A4 | Die geschätzten Schema-Grössen (790 plus 520 Bytes) treffen ungefähr zu | Falle 6 | Gering: die Anhebung erfolgt gegen eine **Messung**, nicht gegen die Schätzung. Die Schätzung dient nur der Vorhersage, dass das Gate reisst |
| A5 | `occ app:install tables` und `occ app:install mail` laufen auf der Testinstanz durch | Environment | Gering: der Store ist aus dem Container erreichbar (200 verifiziert) und der Bootstrap hat für `notes` und `deck` denselben Weg; Fallback (Handinstallation in `custom_apps`) ist in beiden Bootstrap-Skripten schon dokumentiert |
| A6 | Die 200-Antwort von `GET /api/2/tables/{id}` enthält `rowsCount` und `onSharePermissions` auch dann, wenn nur eine Tabelle existiert | Muster 4, K11 | Gering: `show()` ruft `TableService::find` mit aktivem Enhancement; im Integrationstest sofort sichtbar |

## Offene Fragen (RESOLVED)

Alle vier Fragen sind mit der Planung von Phase 8 entschieden; die jeweilige Empfehlung wurde unverändert in die Pläne übernommen (1: Plan 08-01 Task 3, 2: Plan 08-04, 3 und 4: Plan 08-03).

1. **RESOLVED: Welchen Weg nimmt der Spike: Stufe 1 oder direkt Stufe 2?**
   - Was wir wissen: Stufe 1 beantwortet MAIL-04 vollständig und braucht keinen neuen Compose-Dienst; Stufe 2 liefert zusätzlich die Feldformen, die Phase 10 sonst annehmen muss.
   - Was unklar ist: ob die Owner-Zeit für den zusätzlichen Dienst jetzt oder in Phase 10 besser investiert ist.
   - Empfehlung: Stufe 1 im ersten Plan, Stufe 2 als benannter, ausgeklammerter Folgeschritt im Plan von Phase 10. Wenn Stufe 1 auch nur einen Weg uneindeutig lässt, wird Stufe 2 in Phase 8 nachgezogen, weil MAIL-04 blockierend ist.

2. **RESOLVED: Wie hoch genau landet das Budget-Gate?**
   - Was wir wissen: Messung heute 11268 bei Gate 12500; die Phase fügt rund 1310 Bytes hinzu; TOOL-15 schreibt für den Endstand "Messung plus 15 Prozent, aufgerundet auf die nächsten 500" fest.
   - Was unklar ist: ob die Zwischenanhebung in Phase 8 derselben Formel folgt (etwa 14500) oder knapper auf die nächsten 500 über der Messung geht (etwa 13000).
   - Empfehlung: derselben Formel folgen wie der bestehende Eintrag im Skript, **und** die Pro-Tool-Behauptung (max. 1400 Bytes) dazunehmen; sie ist der Teil, der eine Regression wirklich meldet.

3. **RESOLVED: Bekommt `tables_browse` schon einen `cursor`?**
   - Was wir wissen: `paging` bedient `limit`/`offset` direkt, und die v1-Route nimmt beide.
   - Was unklar ist: ob ein Cursor-Parameter die rund 130 Byte Schema in jeder Sitzung wert ist, wenn `offset` in der Antwort ohnehin genannt wird.
   - Empfehlung: Cursor ja, weil ein `next`-Handle das etablierte Antwortmuster dieses Servers ist und `check_scope` eine Verwechslung zweier Tabellen verhindert. Alternative wäre ein offener `offset`-Parameter, der die Scope-Prüfung verliert.

4. **RESOLVED: Sind doppelte Spaltentitel in Tables wirklich möglich?**
   - Was wir wissen: Es gibt keine Unique-Bedingung auf `title` in der Spaltenverwaltung, und `textUnique` betrifft Zellwerte, nicht Titel.
   - Was unklar ist: ob die Oberfläche es verhindert.
   - Empfehlung: den Mehrdeutigkeitsfall trotzdem behandeln (TABLES-02 verlangt ihn wörtlich) und ihn im Unit-Test mit einer konstruierten Spaltenliste abdecken, nicht am Server.

## Quellen

### Primär (HIGH)

- Eigene Codebasis, gelesen am 2026-08-21: `nextcloud/clients/{ocs,deck}.py`, `nextcloud/capabilities.py`, `tools/deck.py`, `server/{__init__,reg_deck}.py`, `paging.py`, `ids.py`, `tests/conftest.py`, `tests/contract/{test_tool_surface,test_no_destructive_calls}.py`, `tests/integration/test_exapp_dav_matrix.py`, `scripts/{check_tool_budget,acceptance_all_tools}.py`, `scripts/bootstrap_{exapp,test_nc}.sh`, `pyproject.toml`, `README*.md`, `docs/*`, `.planning/config.json`
- Live gemessen: `uv run python scripts/check_tool_budget.py` (11268 Bytes, 16 Tools, Gate 12500); `docker ps` (HaRP-Topologie läuft); `docker exec nc-mcp-exapp-nc php occ app:list` (weder `tables` noch `mail` noch `spreed` installiert); Store-Erreichbarkeit aus dem Container (HTTP 200)
- nextcloud/tables, Tag **v2.2.2**: `appinfo/routes.php`, `lib/Controller/{Api1Controller,ApiColumnsController,ApiTablesController,RowOCSController}.php`, `lib/Api/V1Api.php`, `lib/Db/{Table,Row2}.php`, `lib/Model/Permissions.php`, `lib/Service/{TableService,RowService,PermissionsService}.php`
- nextcloud/tables `openapi.json` (main): vollständige Pfadliste, Parameter, Body- und Antwortschemata, Komponenten `Table`, `Column`, `Row`, `Capabilities`, `View`
- nextcloud/mail, Tag **v5.11.1**: `appinfo/{routes.php,info.xml}`, `lib/Controller/{MessageApiController,AccountsController,MailboxesController,MessagesController}.php`, `lib/Service/MailManager.php`, `lib/IMAP/MailboxSync.php`, `lib/Command/CreateImapAccount.php`
- Nextcloud App Store API, `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json`: `tables` 2.2.2 (`>=33.0.0 <36.0.0`, 2026-08-19), `mail` 5.11.1 (`>=32.0.0 <36.0.0`, 2026-08-20), `spreed` 24.0.4 (`>=34.0.0 <35.0.0`)
- GreenMail-Projektdoku, Abschnitt Docker: Testports, `GREENMAIL_OPTS`, `-Dgreenmail.users`, `-Dgreenmail.setup.test.all`
- Docker Hub Registry-API: `greenmail/standalone` 2.1.12 vom 2026-08-05

### Sekundär (MEDIUM)

- `.planning/research/{SUMMARY,ARCHITECTURE,STACK,PITFALLS,FEATURES}.md` (2026-08-21): Meilenstein-Kernrecherche, Grundlage dieser Datei; an elf Stellen durch die Tag-genaue Quellcode-Lesung korrigiert
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`: gesetzte Entscheidungen und Requirement-Wortlaut
- nextcloud/tables Issue #2237: Verwirrung um das Row-Create-Format, auch bei Menschen

### Tertiär (LOW)

- keine. Alle Einzelaussagen dieser Datei sind entweder gegen Quellcode oder gegen eine
  laufende Instanz geprüft oder im Assumptions Log als Annahme markiert.

## Metadaten

**Konfidenz je Bereich:**
- Tables-Routen, Parameter, Payloads, Statuscodes: HIGH (Tag v2.2.2 plus `openapi.json` gelesen, Version gegen den Store abgeglichen)
- Tables-Berechtigungssemantik (K5): HIGH (drei zusammenhängende Quelldateien gelesen: `TableService`, `Permissions`, `PermissionsService`)
- Codebasis-Anknüpfungspunkte und mechanische Checkliste: HIGH (Dateien gelesen, Budget live gemessen, Zeilennummern geprüft)
- Mail-Routen und Controller-Attribute: HIGH (Tag v5.11.1 gelesen; korrigiert einen Pfadfehler der Kernrecherche)
- Erreichbarkeit von Mail unter Impersonation: **offen, das ist der Messgegenstand.** Der Mechanismus ist HIGH belegt, die Messung in dieser Topologie fehlt genau deswegen
- Wertformate der Spaltentypen beim Anlegen: MEDIUM (Assumption A2, absichtlich nicht clientseitig validiert)

**Recherchedatum:** 2026-08-21
**Gültig bis:** 2026-09-20 (30 Tage; Tables und Mail veröffentlichen aber im Wochenrhythmus, deshalb die Versionen vor dem ersten Integrationstest gegen `occ app:list` gegenprüfen)
</content>
</invoke>
