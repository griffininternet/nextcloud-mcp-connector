# Phase 1: Server-Kern - Research

**Researched:** 2026-08-14
**Domain:** MCP-Server (Python, offizielles SDK mcp 2.x) gegen Nextcloud-User-APIs (WebDAV/CalDAV/CardDAV/OCS/Notes-REST/Deck-REST)
**Confidence:** HIGH (SDK-Oberflaeche, Nextcloud-API-Details und #227 direkt gegen Quellcode bzw. offizielle Doku verifiziert), MEDIUM bei zwei Punkten (Deck-Card-Aufloesung per ID, Verhalten von `If-None-Match: *` in der realen Docker-Nextcloud)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**App-ID und Naming**
- **D-01:** App-ID: `mcp_connector`, Anzeigename "MCP Connector", Python-Package `mcp_connector`, Repo `nextcloud-mcp-connector` (GitHub street1983nk, public). Kein "nextcloud" in der App-ID (Store-Regel). Umbenennung ist nur bis zum CSR-PR billig; Freeze-Dokumentation in README festhalten.
- **D-02:** PyPI-Name: `nextcloud-mcp-connector` (der nackte Name `nextcloud-mcp-server` ist von der Community besetzt). CLI-Entry-Point: `nc-mcp` (stdio).

**Tool-Zuschnitt (15 Tools, Namensschema app_verb)**
- **D-03:** Dateien (4): `files_search`, `files_list`, `files_read`, `files_upload` (Upload nur neu, Konflikt = klare Ablehnung, kein Overwrite).
- **D-04:** Kalender (2): `calendar_list_events` (Zeitraum-Pflichtparameter, Timezone-explizit), `calendar_create_event`.
- **D-05:** Notes (3): `notes_search`, `notes_read`, `notes_create`.
- **D-06:** Deck (2): `deck_browse` (Boards/Stacks/Karten lesen, ein Tool mit Ebenen-Parameter statt drei), `deck_create_card`.
- **D-07:** Kontakte (1): `contacts_search` (lesend).
- **D-08:** Suche (1): `unified_search` (OCS Unified Search, provider-parallel, berechtigungstreu).
- **D-09:** ChatGPT-Profil (2): `search` und `fetch` mit exakt dem OpenAI-Kompatibilitaets-Schema (search: id/title/url; fetch: id/title/text/url/metadata). `search` delegiert an Unified Search, `fetch` loest IDs auf Datei/Notiz/Karte/Termin auf. ID-Format: praefixiert (`file:<fileid>`, `note:<id>`, `card:<boardId>:<cardId>`, `event:<calendar>:<uid>`), damit fetch eindeutig routen kann.
- **D-10:** prepare_context ist NICHT in Phase 1 (Phase 4), wird aber beim Tool-Registry-Design mitgedacht (Fan-out nutzt dieselben Client-Funktionen).

**Auth-Modell Phase 1**
- **D-11:** stdio: NC-Base-URL + Username + App-Passwort aus Env (NC_MCP_URL, NC_MCP_USER, NC_MCP_APP_PASSWORD).
- **D-12:** Streamable HTTP: Credential-Passthrough pro Request via Authorization-Header (Basic user:app-passwort). Zusaetzlich optionaler statischer Bearer fuer Single-User-Deployments (Env). KEIN Token-Store in Phase 1 (kommt mit OAuth in Phase 3). Kein Credential-Logging, niemals.
- **D-13:** Login Flow v2 ist Phase 3 (AUTH-02), nicht Phase 1.

**Antwort- und Fehlerformat**
- **D-14:** Kompakte JSON-Antworten mit stabilen Feldern; outputSchema nur wo Clients es nutzen (Schema-Diaet nach InfraNode-Playbook: keine Auto-Titles, kurze Descriptions nur im inputSchema). CI-Check fuer Token-Budget der tools/list-Antwort.
- **D-15:** Fehlerformat: message + hint (handlungsfaehig), 4xx-Fehler gehen ans Modell zur Selbstkorrektur, 5xx werden als degradierte Antwort gekapselt (Graceful-Degradation-Wrapper-Pattern aus InfraNode). Fehlende App (Notes/Deck nicht installiert): klarer Text "Notes app is not installed on this Nextcloud" + Hinweis.
- **D-16:** Annotationen pro Tool ehrlich: alle Lesetools readOnlyHint=true; Create-Tools readOnlyHint=false, destructiveHint=false, idempotentHint=false; openWorldHint=false (eigene Cloud). Permission-Level pro Tool in Doku-Tabelle (read / create-only).

**Nextcloud-Client-Schicht**
- **D-17:** httpx roh fuer ALLE APIs (WebDAV/CalDAV/CardDAV XML via lxml, icalendar fuer VEVENT, vobject fuer VCARD; Notes/Deck/OCS als JSON-REST). KEINE caldav-Library (sync), KEIN aiodav (verwaist). Ein AsyncClient pro Event-Loop (WeakKeyDictionary-Pattern aus InfraNode).
- **D-18:** OCS immer mit OCS-APIRequest: true + Accept: application/json. CalDAV-Edge-Cases (Timezone, Datumsbereich, stille Feld-Verluste) bekommen dedizierte Tests (Lehren aus Platzhirsch-Bugs #538/#544/#782).

**SDK und Transport**
- **D-19:** mcp>=2.0,<3 (GA seit 28.07.2026), Fallback-Pin >=1.29,<2 dokumentiert. Client-Matrix-Test: SDK 1.28+ UND 2.x gegen denselben Endpoint (Regressionstest der #227-Klasse).
- **D-20:** Kein In-Memory-Session-State in Tools; Pagination ueber server-generierte Handles als normale Tool-Argumente. Restart-Ueberlebens-Test als Success-Criterion-Beweis.

**Test-Umgebung**
- **D-21:** Lokale Test-Nextcloud: offizielles nextcloud:apache-Image per docker-compose im Repo (compose.test.yml), Apps notes/deck via occ im Init-Script; zweiter eingeschraenkter Testnutzer fuer Permission-Tests. uv + pytest + respx (gemockte httpx-Ebene) fuer Unit-Tests, In-Memory-MCP-Client (mcp 2.x Feature) fuer Tool-Contract-Tests, Integrationstests gegen die Docker-NC.

**Contribution-Fix (#227)**
- **D-22:** Minimaler PR an nextcloud/context_agent: stateless_http konfigurierbar machen bzw. auf False setzen (exakt wie im Issue diskutiert), mit Repro-Test. Kein Feature-Umbau, kein Scope darueber hinaus. Vor dem PR: CONTRIBUTING.md/CLA des Repos pruefen. Absender: GitHub street1983nk.

### Claude's Discretion

- Interne Modulstruktur (Anlehnung an InfraNode-Layout: server.py / tools.py / clients/ / schemas.py), Naming-Details, Logging-Aufbau, CI-Workflow-Details (GitHub Actions), Verzeichnis-Layout der Tests.

### Deferred Ideas (OUT OF SCOPE)

- prepare_context-Buendel-Tool: Phase 4 (TOOL-08)
- Login Flow v2 Browser-Onboarding: Phase 3 (AUTH-02)
- Tasks/VTODO, MCP-Prompts, Response-Format-Parameter: v1.x nach Launch (REQUIREMENTS v2)
- Talk/Tables/Mail, openDesk-Suite: v2/Phase-3-Meilenstein nach Oktober
- Gehostete Multi-Tenant-Instanz mit AVV (Behoerden-Paket): OPS-02, nach v1
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRV-01 | Streamable HTTP, bedient Session- und Stateless-Clients aus einem Endpoint | `mcp.streamable_http_app()` routet pro Request nach `MCP-Protocol-Version`, beide Aeren immer an, nichts zu konfigurieren (Abschnitt "SDK-Oberflaeche mcp 2.0.0", Pitfall 1) |
| SRV-02 | stdio-Betrieb, App-Passwort aus Env | `mcp.run()` ohne Argument = stdio; Auth existiert dort nicht, Credentials kommen aus Env (Abschnitt "Transport und Auth-Verdrahtung") |
| SRV-03 | Korrekte Annotationen + token-schlanke Schemas | `ToolAnnotations(read_only_hint=..., ...)` snake_case in Python, camelCase auf dem Draht; `structured_output=False` ist der Schema-Diaet-Hebel; Token-Budget-CI ueber In-Memory-Client (Abschnitte "Schema-Diaet", "Token-Budget-CI") |
| SRV-04 | Graceful Degradation bei fehlenden Apps | Eine OCS-Capabilities-Abfrage erkennt Notes und Deck verlaesslich (Abschnitt "Graceful Degradation") |
| SRV-05 | Kein Session-State, multi-worker-faehig | 2026er-Leg ist per Konstruktion sessionlos; `stateless_http` ist ein Legacy-only-Knopf; `RequestStateSecurity` nur relevant bei Multi-Round-Trip (Abschnitt "Statelessness") |
| TOOL-01 | Dateien suchen/listen/lesen/hochladen | WebDAV SEARCH (basicsearch), PROPFIND, GET, PUT mit `If-None-Match: *` (Abschnitt "Nextcloud-API-Referenz pro Tool") |
| TOOL-02 | Termine im Zeitraum lesen, Termin anlegen | CalDAV `calendar-query` REPORT mit `time-range` + serverseitigem `<c:expand>`, PUT einer ICS (Abschnitt "CalDAV", Pitfall 4) |
| TOOL-03 | Notizen suchen/lesen/anlegen | Notes REST v1 `/index.php/apps/notes/api/v1/notes`; ACHTUNG: kein Search-Endpoint, Suche laeuft ueber den Unified-Search-Provider `notes` |
| TOOL-04 | Deck-Boards/Karten lesen, Karte anlegen | Deck REST `/index.php/apps/deck/api/v1.0` (Boards, Stacks inkl. Cards, POST cards) |
| TOOL-05 | Kontakte suchen (lesend) | CardDAV `addressbook-query` REPORT mit `prop-filter`/`text-match` und `<c:limit><c:nresults>` |
| TOOL-06 | Berechtigungstreue Cloud-Suche | OCS `GET /ocs/v2.php/search/providers` + `/providers/{id}/search?term=` (Provider-Liste dynamisch, parallel) |
| TOOL-07 | ChatGPT-Profil `search`/`fetch` | Exaktes OpenAI-Schema verifiziert (search liefert `{"results":[...]}`, fetch ein Objekt); mcp 2.x erzeugt content+structured_content genau passend (Abschnitt "ChatGPT-Profil") |
| TOOL-09 | Nichts loeschen/ueberschreiben, Permission-Level dokumentiert | Create-only-Beweis: `If-None-Match: *` -> 412 bei existierender Datei (sabre/dav-Quellcode verifiziert); Negativ-Tests + Grep-Test gegen DELETE/MOVE/PROPPATCH |
| AUTH-01 | App-Passwort-Anbindung (Basic/Bearer, stdio + remote) | SDK-Auth-Layer akzeptiert nur `Bearer`; Basic-Passthrough muss ueber `ctx.headers` bzw. eigene ASGI-Middleware laufen (Abschnitt "Transport und Auth-Verdrahtung", Pitfall 2) |
| EXAPP-03 | App-ID in Woche 1 eingefroren | `mcp_connector` ist frei: nicht unter den 378 NC-34-Apps im Store, kein Eintrag in nextcloud/app-certificate-requests (838 Verzeichnisse geprueft); PyPI-Name `nextcloud-mcp-connector` frei |
| CONTRIB-01 | Fix-PR an context_agent#227 | Exakte Fundstelle, exakter Ein-Zeilen-Fix, DCO-Praxis und REUSE-Gate verifiziert (Abschnitt "Contribution-Fix #227") |
</phase_requirements>

## Summary

Die gute Nachricht zuerst: **mcp 2.0.0 loest SRV-01 und SRV-05 fast geschenkt**. Das SDK routet jeden HTTP-Request anhand des `MCP-Protocol-Version`-Headers und bedient die 2026-07-28-Aera (sessionlos, kein Handshake) und alle 2025er-Clients aus demselben `streamable_http_app()`. Es gibt keinen Aera-Schalter, keine Allowlist und keine Moeglichkeit, eine Aera abzuschalten. Der beruehmte `stateless_http`-Knopf, an dem context_agent#227 haengt, ist in v2 ausdruecklich **nur** ein Legacy-Knopf: der 2026er-Pfad liest ihn nie. Das heisst konkret: `stateless_http` unangetastet lassen (Default False), dann sind moderne Clients sessionlos und alte Clients sessionfaehig, und die #227-Fehlerklasse kann bei uns strukturell nicht auftreten. Der Preis dafuer ist Sticky Routing fuer Legacy-Clients bei mehr als einem Worker, nicht mehr.

Die schlechte Nachricht ist auf der Nextcloud-Seite und betrifft vier Stellen, die die bisherige Projekt-Research nicht auf dem Radar hatte. (1) Ein per `occ user:add` erzeugter Nutzer hat **keinen Kalender und kein Adressbuch**, weil beide erst beim ersten Login angelegt werden. Das Test-Setup muss `occ dav:create-calendar` und `occ dav:create-addressbook` explizit aufrufen, sonst liefern Kalender- und Kontakt-Tools in CI leere oder 404-Antworten und man sucht den Fehler im eigenen Code. (2) Die Notes-App hat **keinen Search-Endpoint**; `notes_search` muss den OCS-Unified-Search-Provider `notes` nutzen (der sucht serverseitig in Titel und Inhalt) und die Note-ID aus der `resourceUrl` parsen. (3) Unified-Search-Ergebnisse haben **kein `id`-Feld**; nur der Files-Provider liefert `attributes.fileId`. Alle anderen IDs muessen aus `resourceUrl` geparst werden, und Decks Provider-ID heisst `search-deck-card-board`, nicht `deck`, und liefert nur die `cardId` ohne Board und Stack. (4) WebDAV SEARCH sucht ausschliesslich in Properties (Dateiname, Mimetype, Groesse, Datum), niemals im Inhalt, und liefert ohne explizites `<d:limit>` maximal 100 Treffer.

Fuer den kritischen Sicherheitsversprechen-Teil (TOOL-09) gibt es eine harte, verifizierte Loesung: Nextclouds DAV-Layer ist sabre/dav, und sabre prueft `If-None-Match: *` in `checkPreconditions()` fuer **jede** Methode inklusive PUT. Ein Upload auf einen existierenden Pfad wird damit serverseitig mit 412 Precondition Failed abgelehnt, ohne Race zwischen Existenzpruefung und Schreiben. Das ist der Beweis fuer "kann konstruktionsbedingt nichts ueberschreiben", und er gehoert in einen Integrationstest.

**Primary recommendation:** Walking Skeleton = `files_read` (ein Tool) ueber stdio gegen eine per compose.test.yml gestartete `nextcloud:34-apache`, danach der HTTP-Entry mit Basic-Passthrough und der Client-Matrix-Test, danach die restlichen 14 Tools als vertikale Slices in der Reihenfolge WebDAV -> OCS/Notes/Deck (JSON, billig) -> CalDAV/CardDAV (XML, teuer) -> search/fetch (baut auf Unified Search + allen Readern auf). Der #227-PR ist ein unabhaengiger Ein-Zeilen-Fix und kann parallel in Wave 1 laufen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tool-Definition, Schemas, Annotationen | MCP-Server-Layer (`mcp_connector.server`) | - | Nur hier darf `mcp.*` importiert werden; Registry ist der einzige Ort, der Tool-Metadaten kennt |
| Tool-Logik (Parameter -> Nextcloud-Aufruf -> kompakte Antwort) | Tool-Funktionen (`mcp_connector.tools.*`) | - | Freistehende async Funktionen, ohne MCP-Import testbar; Voraussetzung fuer Unit-Tests mit respx |
| Credential-Beschaffung und -Bindung | Credential-Provider (`mcp_connector.nextcloud.credentials`) | Transport-Entry (stdio/HTTP) | Sicherheitsgrenze: Identitaet kommt aus Env (stdio) oder Request-Header (HTTP), NIE aus einem Tool-Parameter |
| HTTP-Transport zu Nextcloud, Pooling, Timeouts | Nextcloud-Client (`mcp_connector.nextcloud.http`) | - | Ein `httpx.AsyncClient` pro Event-Loop; Tools kennen keine URLs, keine Header |
| DAV-XML bauen und parsen | API-Clients (`nextcloud/clients/dav.py`, `caldav.py`, `carddav.py`) | lxml | XML gehoert nicht in Tool-Code; getestet mit fixierten Antwort-Fixtures |
| ICS/VCF-Serialisierung | icalendar, vobject | - | RFC-5545/6350 niemals per String-Bau; das ist der Ort der Platzhirsch-Bugs |
| Session-, Protokoll- und Aera-Handling | mcp-SDK | - | Nichts selbst bauen, nichts konfigurieren; jeder eigene Eingriff hier ist die #227-Falle |
| Auth-Erzwingung im HTTP-Modus | ASGI-Middleware bzw. `TokenVerifier` | Starlette-Host-App | SDK-Bearer-Layer und Basic-Passthrough schliessen sich gegenseitig aus, siehe Pitfall 2 |
| Fehler-Uebersetzung (HTTP-Status -> message+hint) | Graceful-Wrapper im Server-Layer | Tool-Funktionen | Einheitlich an einer Stelle, damit alle 15 Tools identisch degradieren |
| Test-Nextcloud-Bereitstellung | compose.test.yml + bootstrap.sh | GitHub Actions | Bootstrap ist idempotentes Shell-Skript, lokal und in CI identisch aufrufbar |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13 | Runtime | Projekt-Constraint; mcp 2.0.0 verlangt >=3.10 [VERIFIED: PyPI requires_python] |
| uv | 0.11.7 (lokal installiert) | venv, lock, run, Tool-Isolation | Projekt-Constraint (System-Python defekt); erlaubt `uv run --isolated --with "mcp==1.29.0"` fuer den Legacy-Client-Test |
| mcp[cli] | ==2.0.0, Constraint `>=2.0,<3` | MCP-Server, stdio + Streamable HTTP, In-Memory-Client | GA 2026-07-28; v1 offiziell Maintenance-Mode (nur Security-Fixes) [VERIFIED: PyPI + GitHub-Release-Notes v2.0.0] |
| httpx | 0.28.1 | Async-HTTP zu allen Nextcloud-APIs | Reifste Wahl, von respx unterstuetzt; DAV ist nur HTTP mit XML-Body [VERIFIED: PyPI] |
| lxml | 6.1.1 | DAV-XML bauen und parsen (SEARCH, PROPFIND, REPORT) | Einzige ernsthafte Option fuer namespaced XML mit Performance [VERIFIED: PyPI] |
| icalendar | 7.2.2 | VEVENT lesen/erzeugen (RFC 5545) | Korrekte VTIMEZONE-Behandlung, kein String-Bau [VERIFIED: PyPI] |
| vobject | 0.9.9 | vCard parsen (RFC 6350) | Standard fuer VCF-Lesen; seit 2024 stabil, kein Bewegungsbedarf [VERIFIED: PyPI] |
| pydantic | 2.13.4 | Tool-Argumentmodelle, `search`/`fetch`-Output-Modelle | Von mcp 2.0 erzwungen (>=2.12) [VERIFIED: PyPI requires_dist] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.x aktuell | Test-Runner | Alle Test-Ebenen |
| respx | 0.23.1 | httpx-Mocking | Unit-Tests der Tool-Funktionen; ACHTUNG: mockt `httpx`, nicht `httpx2` [VERIFIED: PyPI] |
| anyio (transitiv via mcp) | >=4.9 | async-Test-Plugin (`@pytest.mark.anyio` + `anyio_backend`-Fixture) | Genau das Muster der SDK-Doku; ersetzt pytest-asyncio, eine Abhaengigkeit weniger [CITED: py.sdk.modelcontextprotocol.io/get-started/testing] |
| ruff | aktuell | Lint + Format | Pflicht laut globaler Regel: `ruff check .` und `ruff format --check .` ueber das ganze Repo |
| inline-snapshot | optional | Snapshot-Assertions auf `CallToolResult` | Nur wenn die Contract-Tests sonst unleserlich werden; nicht notwendig |
| uvicorn (transitiv via mcp) | >=0.31.1 | ASGI-Server fuer den HTTP-Modus | `uvicorn mcp_connector.entry_http:app` |

### Bewusst NICHT in Phase 1

| Weggelassen | Grund |
|-------------|-------|
| nc_py_api | Braucht es erst fuer die ExApp-Shell in Phase 2 (AppAPI-Lifecycle, Declarative Settings). Phase 1 spricht ausschliesslich mit User-Credentials gegen `remote.php`/`ocs`/App-REST. Jetzt einbauen heisst FastAPI + niquests + caldav als toten Ballast mitschleppen. |
| FastAPI | mcp 2.0 hat keine FastAPI-Abhaengigkeit; `streamable_http_app()` ist eine Starlette-App, Starlette kommt transitiv mit. FastAPI kommt mit nc_py_api in Phase 2. |
| recurring-ical-events | Nicht noetig: sabre/dav expandiert Recurrences serverseitig via `<c:expand start end>` im calendar-query. Ein Problem weniger und deutlich weniger Code. [VERIFIED: sabre/dav lib/CalDAV/Plugin.php] |
| caldav / aiodav | D-17; caldav ist sync, aiodav verwaist. |
| PyJWT | Erst mit OAuth in Phase 3. Kommt ohnehin transitiv mit mcp. |
| tiktoken | Fuer den Token-Budget-Check reicht die serialisierte Byte-Groesse als deterministischer Proxy, siehe Abschnitt Token-Budget-CI. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx 0.28 fuer eigenen Code | httpx2 (kommt ohnehin als mcp-Dependency) | Waere eine HTTP-Stack-Abhaengigkeit weniger, aber httpx2 ist erst seit 2026-05-11 auf PyPI, respx unterstuetzt es nicht, und es verifiziert TLS gegen den OS-Trust-Store statt certifi. Fuer den eigenen Code bei httpx bleiben. |
| serverseitiges `<c:expand>` | recurring-ical-events clientseitig | Serverseitig ist weniger Code und liefert deterministisch UTC-Zeiten. Clientseitig nur, wenn ein Nextcloud-Bug in expand auftaucht (dann als dokumentierter Fallback). |
| anyio-Pytest-Plugin | pytest-asyncio 1.4.0 | Beide funktionieren. anyio ist schon da und die SDK-Doku benutzt es; pytest-asyncio waere eine Dev-Dependency ohne Zusatznutzen. |
| Basic-Passthrough via `ctx.headers` | Basic-Credentials in einen Bearer-Token kodieren | `ctx.headers` ist der dokumentierte Weg und braucht keine Client-seitige Sondervorbereitung. Bearer-Kodierung waere ein Eigenformat, das kein Client kennt. |

**Installation:**
```bash
uv init --python 3.13
uv add "mcp[cli]>=2.0,<3" "httpx>=0.28,<0.29" lxml icalendar vobject "pydantic>=2.12"
uv add --dev pytest respx ruff
```

**Version verification (durchgefuehrt 2026-08-14):**
```bash
curl -s https://pypi.org/pypi/mcp/json | jq -r .info.version        # 2.0.0, upload 2026-07-28T13:45:28
curl -s https://pypi.org/pypi/httpx/json | jq -r .info.version      # 0.28.1
curl -s https://pypi.org/pypi/lxml/json | jq -r .info.version       # 6.1.1
curl -s https://pypi.org/pypi/icalendar/json | jq -r .info.version  # 7.2.2
curl -s https://pypi.org/pypi/vobject/json | jq -r .info.version    # 0.9.9
curl -s https://pypi.org/pypi/respx/json | jq -r .info.version      # 0.23.1
curl -s https://pypi.org/pypi/pydantic/json | jq -r .info.version    # 2.13.4
```

mcp 2.0.0 `requires_dist` (relevant): `httpx2>=2.5.0`, `mcp-types==2.0.0`, `jsonschema>=4.20.0`, `opentelemetry-api>=1.28.0`, `pydantic>=2.12.0`, `pyjwt[crypto]>=2.10.1`, `sse-starlette>=3.0.0`, `starlette>=0.27`, `uvicorn>=0.31.1`, `pywin32>=311` (win32). Keine FastAPI-Abhaengigkeit. [VERIFIED: PyPI JSON]

## Package Legitimacy Audit

slopcheck 0.6.1 lief lokal am 2026-08-14 gegen PyPI. Der Installationsschritt am Ende brach ab (kein `pip` im PATH, nur uv), die Pruefung selbst lief vollstaendig durch.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| mcp | PyPI | 2.0.0 seit 2026-07-28, Projekt seit 2024 | sehr hoch | github.com/modelcontextprotocol/python-sdk | [OK] | Approved |
| mcp-types | PyPI | 2.0.0, lock-step mit mcp | via mcp | github.com/modelcontextprotocol/python-sdk | [OK] | Approved (transitiv, nicht direkt pinnen) |
| httpx | PyPI | 0.28.1 seit 2024-12-06 | sehr hoch | github.com/encode/httpx | [OK] | Approved |
| httpx2 | PyPI | erste Version 2026-05-11, 2.10.0 am 2026-08-09 | neu | github.com/pydantic/httpx2 | [SUS] | Transitiv behalten, NICHT direkt als Dependency aufnehmen |
| lxml | PyPI | 6.1.1 seit 2026-05-18 | sehr hoch | github.com/lxml/lxml | [OK] | Approved |
| icalendar | PyPI | 7.2.2 seit 2026-07-20 | hoch | github.com/collective/icalendar | [OK] | Approved |
| vobject | PyPI | 0.9.9 seit 2024-12-16 | hoch | github.com/py-vobject/vobject | [OK] | Approved |
| pydantic | PyPI | 2.13.4 seit 2026-05-06 | sehr hoch | github.com/pydantic/pydantic | [OK] | Approved |
| respx | PyPI | 0.23.1 seit 2026-04-08 | hoch | github.com/lundberg/respx | [OK] | Approved |
| pytest | PyPI | aktuell | sehr hoch | github.com/pytest-dev/pytest | [OK] | Approved |
| anyio | PyPI | >=4.9 | sehr hoch | github.com/agronholm/anyio | [OK] | Approved |
| ruff | PyPI | aktuell | sehr hoch | github.com/astral-sh/ruff | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** `httpx2`

Bewertung des SUS-Treffers: slopcheck begruendet ihn mit "Suspiciously close to 'httpx'. Could be a typosquat." Das ist bei diesem Namen ein erwartbares Signal. Gegenpruefung: `httpx2` wird auf PyPI unter `author_email: Tom Christie <tom@tomchristie.com>` (Autor von httpx) veroeffentlicht, Homepage und Source zeigen auf `github.com/pydantic/httpx2`, Classifier "Development Status :: 5 - Production/Stable" [VERIFIED: PyPI JSON]. Die SDK-Release-Notes zu v2.0.0b2 nennen den Wechsel explizit: "httpx is replaced by httpx2 (#2972) ... the next-generation httpx fork with SSE support built in" [CITED: github.com/modelcontextprotocol/python-sdk releases v2.0.0b2]. Das Paket ist damit legitim, aber jung. Konsequenz fuer den Plan: `httpx2` **nicht** in `pyproject.toml` aufnehmen (es kommt ueber mcp), und im Plan einen `checkpoint:human-verify` vor dem ersten `uv sync` setzen, bei dem der Owner die aufgeloeste Lock-Datei einmal durchsieht.

Zusaetzliche Beobachtung ohne Handlungsbedarf in Phase 1: httpx2 verifiziert TLS gegen den OS-Trust-Store (via `truststore`), nicht gegen certifi. Relevant, sobald ein Integrationstest gegen ein selbst signiertes Nextcloud-Zertifikat laeuft; im Docker-Setup nutzen wir HTTP, also kein Thema.

## SDK-Oberflaeche mcp 2.0.0 (exakt, gegen Quellcode verifiziert)

### Server und Tools

```python
from mcp.server import MCPServer          # FastMCP heisst in v2 MCPServer
from mcp.types import ToolAnnotations

mcp = MCPServer("MCP Connector", version="0.1.0", instructions="...")
```

`MCPServer.__init__` akzeptiert unter anderem `name`, `title`, `description`, `instructions`, `version`, `token_verifier`, `auth`, `log_level`, `debug`, `lifespan`, `middleware`, `request_state_security`, `subscriptions`. Transport-Argumente gehoeren **nicht** in den Konstruktor. [VERIFIED: src/mcp/server/mcpserver/server.py @ v2.0.0]

`@mcp.tool()` akzeptiert genau: `name`, `title`, `description`, `annotations`, `icons`, `meta`, `structured_output`. [VERIFIED: server.py Zeile 621ff]

`ToolAnnotations` hat in Python **snake_case**-Felder: `title`, `read_only_hint`, `destructive_hint`, `idempotent_hint`, `open_world_hint`. Auf dem Draht werden sie zu camelCase. [VERIFIED: src/mcp-types/mcp_types/_types.py Zeile 1365ff]

Input-Schema kommt aus Type-Hints, Optionalitaet aus Defaults, Descriptions und Constraints aus `Annotated[..., Field(...)]`, Enums aus `Literal[...]`. Ungueltige Argumente werden **vor** dem Funktionsaufruf abgelehnt und kommen als `is_error=True`-Result beim Modell an, das sich selbst korrigieren kann. [CITED: py.sdk.modelcontextprotocol.io/servers/tools]

### Schema-Diaet: der eine Hebel, der 56 Prozent spart

Das Output-Schema entsteht ausschliesslich aus der Return-Annotation. `@mcp.tool(structured_output=False)` schaltet es komplett ab: kein `output_schema`, kein Wrapping, keine Validierung, `structured_content=None`, `content` ist genau der zurueckgegebene String. [CITED: py.sdk.modelcontextprotocol.io/servers/structured-output]

Daraus folgt die Regel fuer dieses Projekt (deckt D-14 exakt ab):

- **13 Tools** (`files_*`, `calendar_*`, `notes_*`, `deck_*`, `contacts_search`, `unified_search`): `-> str` mit `structured_output=False`, Rueckgabe ist `json.dumps(payload, separators=(",", ":"), ensure_ascii=False)`. Kompaktes JSON mit stabilen Feldnamen, kein Output-Schema im `tools/list`.
- **2 Tools** (`search`, `fetch`): mit Pydantic-Return-Modell, also MIT Output-Schema, weil ChatGPT genau diese Struktur erwartet.

Zweiter Diaet-Hebel: Pydantic setzt in Input-Schemas automatisch `"title"`-Keys pro Property. Die sind reiner Ballast. Wenn das Budget knapp wird, ist ein `model_config = ConfigDict(json_schema_extra=...)`-Trick zu fragil; sauberer ist, die Beschreibungen kurz zu halten (eine Zeile, kein Fliesstext) und verschachtelte Modelle in Inputs zu vermeiden (flache Parameter statt `$defs`-Referenzen).

Dritte Falle, ausdruecklich dokumentiert: eine Klasse **ohne** Annotationen im Klassenkoerper als Return-Type fuehrt **still** zu `output_schema=None` und `repr()` als Text. Kein Fehler, keine Warnung, nutzloses Tool. Wenn wir Dataclasses fuer Antworten nutzen, muessen die Felder auf dem Klassenkoerper annotiert sein. [CITED: structured-output, "A class without type hints"]

### Fehlerbehandlung (deckt D-15)

| Wurf | Ergebnis | Wann bei uns |
|------|----------|--------------|
| beliebige Exception (`ValueError`, eigene `NextcloudToolError`) | `is_error=True`, Message im `content`, Modell liest und korrigiert | **Standardfall**: 400/403/404/409/412 von Nextcloud, fehlende App, ungueltiger Pfad, Konflikt beim Upload |
| `MCPError(code=..., message=...)` aus `mcp` | JSON-RPC-Fehler, **kein** Result, Modell sieht nichts, Host bekommt den Fehler | Nur wenn kein Modell-Retry helfen kann: fehlende Credentials im HTTP-Modus, Server nicht konfiguriert |

Entscheidungsfrage aus der Doku, wortwoertlich uebernehmen: "could a smarter model have avoided this? Yes -> ordinary exception. No -> `MCPError`." [CITED: py.sdk.modelcontextprotocol.io/servers/handling-errors]

Nie einen Fehlertext `return`-en: das haette `is_error=False` und sieht fuer das Modell wie ein Erfolg aus.

### Transport und Auth-Verdrahtung

```python
# stdio (SRV-02)
if __name__ == "__main__":
    mcp.run()                     # ohne Argument = stdio, blockierend

# HTTP (SRV-01), ASGI-App fuer uvicorn
app = mcp.streamable_http_app()   # Starlette-App, Endpoint /mcp
```

Wichtige, verifizierte Details:

1. **`transport_security` ist das Go-Live-Gate.** Ohne `transport_security=` akzeptiert die App nur Requests mit `Host: 127.0.0.1:<port>` / `localhost:<port>` / `[::1]:<port>` und antwortet auf alles andere mit **421 Misdirected Request**, bevor irgendetwas MCP-artiges passiert. Der Grund steht nur im Server-Log, der Client sieht einen generischen Transport-Fehler. Fuer Phase 1 heisst das: Env-Variable `NC_MCP_ALLOWED_HOSTS`, daraus `TransportSecuritySettings(allowed_hosts=[...])`, und hinter einem Reverse Proxy ehrlich `enable_dns_rebinding_protection=False`. Ein `host="0.0.0.0"` allowlistet **nichts**. [CITED: py.sdk.modelcontextprotocol.io/run/deploy]
2. **Gemountete Sub-Apps haben keinen Lifespan.** Wenn `streamable_http_app()` per `Mount` in eine eigene Starlette-App gehaengt wird (das passiert spaetestens in Phase 2), muss die Host-App im eigenen Lifespan `async with mcp.session_manager.run():` betreten, sonst schlaegt der erste Request mit `RuntimeError: Task group is not initialized` fehl. [CITED: run/asgi]
3. **`@mcp.custom_route()` ist NIE authentifiziert**, auch wenn der Rest des Servers es ist. Gut fuer `/health`, verboten fuer alles andere. [CITED: run/asgi]
4. **Der SDK-Auth-Layer akzeptiert ausschliesslich `Bearer`.** `BearerAuthBackend.authenticate()` gibt `None` zurueck, wenn der Authorization-Header nicht mit `bearer ` beginnt (case-insensitiv geprueft, dann `auth_header[7:]`). [VERIFIED: src/mcp/server/auth/middleware/bearer_auth.py @ v2.0.0] Der Basic-Passthrough aus D-12 laeuft also **nicht** durch `token_verifier`.
5. **`ctx.headers`** liefert im Handler die Request-Header (`Mapping[str, str] | None`, `None` bei stdio und In-Memory). Die Docstring warnt ausdruecklich: "Headers are client-supplied input - never treat one as an identity assertion." [VERIFIED: src/mcp/server/mcpserver/context.py Zeile 278ff]

Zu Punkt 5 die inhaltliche Einordnung, die im Plan stehen sollte: Wir behandeln den Header **nicht** als Identitaetsbehauptung. Wir leiten die darin enthaltenen Credentials unveraendert an Nextcloud weiter, und **Nextcloud** authentifiziert. Der Server behauptet nie selbst, wer der Nutzer ist. Damit ist der Passthrough architektonisch korrekt und deckt AUTH-01 ohne Token-Store.

Daraus folgt das Auth-Modell fuer Phase 1, drei Modi, per Env exklusiv gewaehlt:

| Modus | Auswahl | Mechanik | Konfiguriert `auth=`/`token_verifier=`? |
|-------|---------|----------|----------------------------------------|
| stdio | Entry-Point `nc-mcp` | Credentials aus `NC_MCP_URL` / `NC_MCP_USER` / `NC_MCP_APP_PASSWORD` | nein (stdio hat keine Header) |
| HTTP Passthrough (Default) | `NC_MCP_URL` gesetzt, `NC_MCP_STATIC_BEARER` leer | `ctx.headers["authorization"]` (Basic) wird 1:1 an Nextcloud weitergegeben; fehlt er, wirft das Tool `MCPError` mit Hinweis | **nein** |
| HTTP Static Bearer (Single-User) | `NC_MCP_STATIC_BEARER` gesetzt | `TokenVerifier` prueft konstanten Vergleich (`secrets.compare_digest`), Nextcloud-Credentials kommen aus Env wie bei stdio | ja, `auth=AuthSettings(...)` |

`token_verifier=` und `auth=` muessen immer zusammen gesetzt werden, sonst wirft `MCPServer(...)` einen `ValueError` schon vor dem ersten Request. [CITED: run/authorization]

### Statelessness und die #227-Fehlerklasse (SRV-01, SRV-05)

Das ist der wichtigste Absatz dieses Dokuments, weil er ein Success Criterion direkt beantwortet:

- Eine `streamable_http_app()` bedient **beide** Protokoll-Aeren. Routing pro Request nach `MCP-Protocol-Version`. Es gibt kein `legacy=`, keine Version-Allowlist, keinen Weg, eine Aera abzuschalten. [CITED: run/legacy-clients]
- Eine 2026-07-28-Verbindung ist **sessionlos per Konstruktion**. Kein `Mcp-Session-Id`, nichts fuer einen Load Balancer, an dem er kleben muesste.
- Eine Legacy-Verbindung (2025-11-25 und aelter, das ist der Default aller heutigen Clients inklusive SDK 1.28/1.29) bekommt eine Session, die als **in-process dict** lebt. Bei mehr als einem Worker braucht sie Sticky Routing, sonst 404 "Session not found".
- **`stateless_http=True` ist ein Legacy-only-Knopf.** Der 2026er-Pfad wird geroutet und beantwortet, *bevor* das Flag gelesen wird. Auf dem Legacy-Leg macht es Wegwerf-Sessions pro Request und kostet dafuer beide Server-zu-Client-Kanaele: jede server-initiierte Anfrage wirft `NoBackChannelError` als Top-Level-Fehler, Notifications werden still verworfen. [CITED: run/legacy-clients, run/deploy]

**Empfehlung: `stateless_http` nicht setzen (Default False).** Begruendung: Unsere Tools rufen nie in den Client zurueck (kein `ctx.elicit`, kein Sampling, kein `Resolve`), also waere `stateless_http=True` fachlich gratis. Aber es ist genau die Einstellung, an der context_agent#227 haengt, und der Nutzen (freies Load Balancing des Legacy-Legs) ist fuer eine Selfhoster-Installation mit einem Worker null. Multi-Worker ist Betriebssache und dann mit Sticky Sessions loesbar. Wenn spaeter doch Multi-Worker ohne Stickiness gebraucht wird, ist es ein Ein-Zeilen-Schalter, den ein Test abdeckt.

`RequestStateSecurity(keys=[...])` ist fuer uns **nicht** relevant, solange kein Tool `InputRequiredResult` oder `Resolve(...)` benutzt. Im Plan als Nicht-Ziel notieren, damit niemand es "sicherheitshalber" einbaut.

Der Restart-Ueberlebens-Test (Success Criterion 2) sieht damit so aus: moderner Client -> `list_tools`, Server-Prozess neu starten, derselbe Client-Code -> `list_tools` erneut, muss ohne Reconnect-Fehler durchlaufen, weil es keine Session gibt, die verloren gehen koennte.

### In-Memory-Client fuer Contract-Tests

```python
from mcp import Client

async with Client(mcp, raise_exceptions=True) as client:
    result = await client.list_tools()      # ListToolsResult, .tools ist list[Tool]
    tool = result.tools[0]
    tool.name, tool.title, tool.description, tool.input_schema, tool.annotations
    call = await client.call_tool("files_read", {"path": "/README.md"})
    call.content, call.structured_content, call.is_error
```

`Client(mcp)` ist aera-neutral. `Client(mcp, mode="legacy")` erzwingt den `initialize`-Handshake, und in diesem Modus **kein** `raise_exceptions=True` verwenden. [CITED: get-started/testing, client/]

Fuer den echten Client-Matrix-Test gegen ein **fremdes** SDK 1.x reicht der In-Memory-Client nicht (er ist v2-Code). Der Beweis fuer SRV-01 braucht einen echten 1.29-Client in einem getrennten Environment:

```bash
uv run --isolated --with "mcp>=1.29,<2" python tests/compat/legacy_client_check.py http://127.0.0.1:8765/mcp
```

Das Skript macht `initialize`, dann `tools/list`, dann einen `tools/call`, und faellt bei "Session terminated" mit Exit-Code 1 aus. Genau die #227-Reproduktion, nur als Regressionstest fuer uns.

Client mit eigenen Headern (fuer den Basic-Passthrough-Integrationstest):

```python
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

async with httpx2.AsyncClient(headers={"Authorization": f"Basic {b64}"},
                              timeout=httpx2.Timeout(30.0, read=300.0),
                              follow_redirects=True) as hc:
    transport = streamable_http_client("http://127.0.0.1:8765/mcp", http_client=hc)
    async with Client(transport) as client:
        ...
```

`streamable_http_client` nimmt **kein** `headers=` mehr, nur `url`, `http_client`, `terminate_on_close`. [CITED: client/transports]

## Nextcloud-API-Referenz pro Tool

Alle Pfade relativ zur Instanz-Basis-URL. Auth in Phase 1 immer HTTP Basic mit `user:app-passwort`.

### files_search (WebDAV SEARCH)

```
SEARCH /remote.php/dav/
Content-Type: text/xml
```

Der Endpoint ist die DAV-Wurzel, nicht der Files-Pfad: Nextclouds `FileSearchBackend::getArbiterPath()` gibt `''` zurueck. [VERIFIED: apps/dav/lib/Files/FileSearchBackend.php]

```xml
<?xml version="1.0" encoding="UTF-8"?>
<d:searchrequest xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:basicsearch>
    <d:select>
      <d:prop>
        <d:displayname/><d:getcontenttype/><d:getlastmodified/>
        <d:getcontentlength/><d:resourcetype/><oc:fileid/>
      </d:prop>
    </d:select>
    <d:from>
      <d:scope><d:href>/files/alice</d:href><d:depth>infinity</d:depth></d:scope>
    </d:from>
    <d:where>
      <d:like><d:prop><d:displayname/></d:prop><d:literal>%budget%</d:literal></d:like>
    </d:where>
    <d:orderby/>
    <d:limit><d:nresults>25</d:nresults></d:limit>
  </d:basicsearch>
</d:searchrequest>
```

Verifizierte Fakten:

- Operatoren: `d:eq`, `d:like`, `d:gt`, `d:lt`, `d:and`, `d:or`, `d:not`, `d:is-collection`. [CITED: docs.nextcloud.com WebDAV/search]
- Der Scope muss ein **Directory**-Node innerhalb des DAV-Baums sein, die Doku nennt `/files/$username[/unterordner]`. [VERIFIED: FileSearchBackend::isValidScope + Doku]
- Abfragbare Properties (queryable): `{DAV:}displayname`, `{DAV:}getcontenttype`, `{DAV:}getlastmodified`, `{DAV:}creationdate`, `{http://nextcloud.org/ns}upload_time`, `{oc}size`, `{oc}favorite`, `{oc}fileid`, `{oc}owner-id`. Nur-selektierbar: `resourcetype`, `getcontentlength`, `permissions`, `getetag`, `checksums`, `has-preview` und die Metadata-Properties. [VERIFIED: FileSearchBackend::getPropertyDefinitionsForScope]
- **Default-Limit ist 100**, wenn kein `<d:limit>` gesetzt ist. [VERIFIED: FileSearchBackend Zeile 359: `$maxResults = $limit->maxResults !== 0 ? (int)$limit->maxResults : 100`]
- **Maximal 100 Operatoren** pro Query, sonst `InvalidArgumentException`. Betrifft uns nicht bei einfachen Queries, aber kein Query-Baum aus Nutzer-Input generieren. [VERIFIED: `OPERATOR_LIMIT = 100`]
- **Kein Volltext.** SEARCH matcht Properties, nicht Inhalte. Das gehoert in die Tool-Description, sonst erwartet das Modell Inhaltstreffer. [CITED: Doku + Codepfad]
- Antwort: `207 Multi-Status` mit `d:multistatus`/`d:response`/`d:href` + `d:propstat`.

### files_list (PROPFIND)

```
PROPFIND /remote.php/dav/files/<uid>/<pfad>
Depth: 1
Content-Type: application/xml
```

```xml
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:getlastmodified/><d:getetag/><d:getcontenttype/><d:getcontentlength/>
    <d:resourcetype/><oc:fileid/><oc:size/><oc:permissions/>
  </d:prop>
</d:propfind>
```

`Depth: 1` = Ordner plus direkte Kinder (der Ordner selbst ist der erste `d:response`, den beim Mappen ueberspringen). `Depth: 0` = nur der Ordner. `oc:permissions` ist ein Rechte-String (R=shareable, W=writable, D=deletable, ...) und ist genau die Information, die `files_upload` vorab lesen kann, um "kein Schreibrecht" freundlich zu melden. [CITED: docs.nextcloud.com WebDAV/basic]

### files_read (GET)

```
GET /remote.php/dav/files/<uid>/<pfad>
```

Pflicht-Guards im Tool (Performance-Trap aus der Projekt-Research):
1. Vorab PROPFIND `Depth: 0` fuer `getcontentlength` und `getcontenttype`.
2. Groessen-Cap (Vorschlag 512 KiB Default, per Parameter bis maximal 2 MiB) und harte Ablehnung darueber mit Hinweis auf den Offset-Parameter.
3. Binaerdateien (Mimetype nicht `text/*`, nicht `application/json|xml|yaml|x-yaml`, nicht `+json|+xml`) mit klarem Text ablehnen, nicht base64 ausliefern.
4. Teil-Lesen via `Range: bytes=<offset>-<offset+limit-1>` (sabre/dav unterstuetzt Range auf Files) und `next_offset` im Antwort-JSON als Handle. Das ist die stateless Pagination aus D-20.

### files_upload (PUT, create-only)

```
PUT /remote.php/dav/files/<uid>/<pfad>
If-None-Match: *
Content-Type: <mimetype>
```

**Das ist der Beweis fuer TOOL-09.** sabre/dav ruft `checkPreconditions()` in `invokeMethod()` fuer **jede** Methode auf, also auch fuer PUT, und bei `If-None-Match: *` gilt: "The header can also contain `*`, in which case the request will only succeed if the entity does not exist at all", andernfalls `PreconditionFailed` (412). [VERIFIED: sabre-io/dav lib/DAV/Server.php Zeile 466 und 1348ff]

Fehler-Mapping fuer das Tool: 412 -> `"A file already exists at <path>. This server never overwrites files. Choose a different name."`, 403 -> Schreibrecht fehlt, 404 -> Elternordner existiert nicht (kein Auto-Mkcol, ausser man setzt bewusst `X-NC-WebDAV-AutoMkcol: 1`, was ich fuer Phase 1 **nicht** empfehle: Ordner anlegen ist ein zweiter Schreibvorgang, der nicht im Tool-Vertrag steht).

Optionale Header: `X-OC-MTime` (Zeitstempel), `OC-Checksum`. [CITED: docs.nextcloud.com WebDAV/basic]

Restrisiko (MEDIUM): Nextcloud haengt eigene Plugins in den PUT-Pfad. Dass `If-None-Match: *` in der realen Instanz zu 412 fuehrt, ist gegen sabre-Quellcode verifiziert, aber nicht gegen eine laufende Nextcloud 34. **Integrationstest ist Pflicht**, und wenn er fehlschlaegt, ist der Fallback ein PROPFIND-Existenzcheck vor dem PUT (mit dokumentiertem TOCTOU-Restrisiko).

### calendar_list_events (CalDAV REPORT calendar-query)

Kalender-Discovery:
```
PROPFIND /remote.php/dav/calendars/<uid>/
Depth: 1
```
Properties: `d:displayname`, `d:resourcetype`, `cs:getctag`, `c:supported-calendar-component-set` (Namespaces: `urn:ietf:params:xml:ns:caldav`, `http://calendarserver.org/ns/`). Nur Collections mit `VEVENT` im Component-Set beruecksichtigen, Subscriptions (`cs:subscribed`) ueberspringen.

Der Pfad ist `calendars/<uid>/<calendarUri>/`, ohne `users/`-Segment (CalendarRoot mit `principals/users` erbt `getName()` = `calendars`). [VERIFIED: apps/dav/lib/RootCollection.php + CalDAV/CalendarRoot.php]

Query:
```
REPORT /remote.php/dav/calendars/<uid>/<calendarUri>/
Depth: 1
Content-Type: application/xml
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
    <d:getetag/>
    <c:calendar-data>
      <c:expand start="20260901T000000Z" end="20260930T235959Z"/>
    </c:calendar-data>
  </d:prop>
  <c:filter>
    <c:comp-filter name="VCALENDAR">
      <c:comp-filter name="VEVENT">
        <c:time-range start="20260901T000000Z" end="20260930T235959Z"/>
      </c:comp-filter>
    </c:comp-filter>
  </c:filter>
</c:calendar-query>
```

Verifizierte Fakten, die den Kalender-Teil dramatisch vereinfachen:

- `<c:expand start end>` wird von sabre/dav unterstuetzt und expandiert Recurrences **serverseitig**. `start` und `end` sind Pflichtattribute, `end` muss groesser als `start` sein, sonst 400 `BadRequest`. [VERIFIED: sabre lib/CalDAV/Xml/Filter/CalendarData.php]
- Die Expansion nutzt die `calendar-timezone`-Property der Collection, und **defaultet auf UTC**, wenn die Property fehlt. Ergebnis sind absolute Zeiten, keine floating times. [VERIFIED: sabre lib/CalDAV/Plugin.php Zeile 426ff]
- Datums-Format in `time-range` und `expand`: iCalendar-UTC-Form `YYYYMMDDTHHMMSSZ`. **Kein ISO-8601 mit Bindestrichen und Doppelpunkten.** Das ist eine der drei haeufigsten CalDAV-Fehlerquellen.
- Ein `expand` verliert bewusst `RRULE`/`RECURRENCE-ID`-Struktur und liefert stattdessen Einzelinstanzen. Das ist fuer ein Lesetool genau richtig.

Tool-Vertrag daraus (deckt D-04, Timezone-explizit):
- Pflichtparameter `start` und `end` als ISO-8601-Strings **mit** Offset oder `Z` (z. B. `2026-09-01T00:00:00+02:00`), plus optionaler Parameter `timezone` (IANA-Name) fuer die Ausgabe-Darstellung.
- Intern nach UTC konvertieren, dann als `YYYYMMDDTHHMMSSZ` formatieren.
- Ganztaegige Termine (`DTSTART;VALUE=DATE`) als Datum ohne Uhrzeit ausgeben, niemals als Mitternacht mit Zeitzone. Eigenes Feld `all_day: true`.
- Antwortfelder stabil halten: `uid`, `summary`, `start`, `end`, `all_day`, `location`, `calendar`, `id` (Format `event:<calendarUri>:<objektname>`).

### calendar_create_event (CalDAV PUT)

```
PUT /remote.php/dav/calendars/<uid>/<calendarUri>/<neue-uuid>.ics
If-None-Match: *
Content-Type: text/calendar; charset=utf-8
```

ICS **immer** mit `icalendar` bauen, nie per String-Konkatenation. Mindestbestand: `BEGIN:VCALENDAR` mit `VERSION:2.0` und `PRODID`, ein `VEVENT` mit `UID` (selbst generiert, gleich dem Dateinamen-Stamm), `DTSTAMP`, `DTSTART`, `DTEND`, `SUMMARY`. Bei zonierten Zeiten muss ein passendes `VTIMEZONE` mit IANA-`TZID` im Kalender stehen; `icalendar` kann das aus einem `zoneinfo`-tzinfo erzeugen. Deprecated-Windows-TZIDs ("W. Europe Standard Time") sind ein bekannter Interop-Killer.

`If-None-Match: *` auch hier, damit ein zweiter Aufruf mit derselben UUID nicht ueberschreibt (macht das Tool ehrlich nicht-idempotent, passend zu `idempotent_hint=False`).

Rueckgabe: `id` im Format `event:<calendarUri>:<objektname>`, plus die vom Server bestaetigten Zeiten (nach dem PUT einmal per GET nachlesen ist die ehrliche Variante gegen "still verlorene Felder", der Platzhirsch-Bug #544).

### notes_search / notes_read / notes_create (Notes REST v1)

Basis: `/index.php/apps/notes/api/v1/notes`, Header `Accept: application/json`. [CITED: github.com/nextcloud/notes docs/api/v1.md]

| Operation | Request |
|-----------|---------|
| Liste | `GET /notes` mit `?exclude=content` (Datensparsamkeit), `?category=`, `?chunkSize=` + `?chunkCursor=` (Cursor kommt als Header `X-Notes-Chunk-Cursor`) |
| Einzelne Notiz | `GET /notes/{id}` |
| Anlegen | `POST /notes` mit Body `{"title": "...", "category": "...", "content": "..."}` |

Note-Felder: `id`, `etag`, `readonly`, `content`, `title`, `category`, `favorite`, `modified`. `title` wird serverseitig sanitisiert und bei Namenskollision numeriert; der zurueckgegebene Titel ist die Wahrheit und muss so ans Modell gehen. `507 Insufficient Storage` ist ein dokumentierter Fehlercode beim Anlegen.

**Kritisch: es gibt keinen Search-Endpoint.** Die Routen sind index/get/create/update/undo/autotitle/destroy/category/attachment/settings, kein Search. [VERIFIED: nextcloud/notes appinfo/routes.php] `notes_search` muss deshalb den Unified-Search-Provider nutzen:

```
GET /ocs/v2.php/search/providers/notes/search?term=<query>&limit=<n>
OCS-APIRequest: true
Accept: application/json
```

Der Provider hat die ID `notes`, sucht serverseitig ueber `NotesService::search()` in Titel **und** Inhalt, sortiert nach `modified` absteigend, und liefert `resourceUrl` = `.../index.php/apps/notes/note/{id}` (Route `notes.page.indexnote`) sowie `subline` = Excerpt. Es gibt **kein** `attributes`-Feld, die ID muss aus der URL geparst werden. [VERIFIED: nextcloud/notes lib/AppInfo/SearchProvider.php]

Empfohlenes Vorgehen fuer `notes_search`: Unified-Search fuer die Treffer, IDs aus `resourceUrl` extrahieren, Titel und Excerpt direkt aus dem Search-Entry nehmen (kein zweiter Roundtrip pro Treffer). Nur wenn `category` oder `modified` gebraucht werden, ein `GET /notes?exclude=content` als einzelner Zusatzaufruf und lokal joinen.

Fallback, wenn die Notes-App installiert ist, der Provider aber (aus welchem Grund auch immer) fehlt: `GET /notes?exclude=content` + clientseitiger Titel-Match. Als degradierter Pfad dokumentieren, nicht als Default.

### deck_browse / deck_create_card (Deck REST v1.0)

Basis: `/index.php/apps/deck/api/v1.0`. **Pflicht-Header laut Doku: `OCS-APIRequest: true` und `Content-Type: application/json`** fuer alle Requests (Attachment-Upload ausgenommen). [CITED: github.com/nextcloud/deck docs/API.md]

| Ebene | Request |
|-------|---------|
| Boards | `GET /boards` (optional `?details=true` fuer Labels/Stacks/Users) |
| Board-Details | `GET /boards/{boardId}` |
| Stacks inkl. Karten | `GET /boards/{boardId}/stacks` (Antwort enthaelt `cards`) |
| Karte | `GET /boards/{boardId}/stacks/{stackId}/cards/{cardId}` |
| Karte anlegen | `POST /boards/{boardId}/stacks/{stackId}/cards` mit `{"title": "...", "type": "plain", "order": 999, "description": "...", "duedate": "2026-09-01T10:00:00+00:00"}` |

Verifizierte Details:
- `title` maximal 255 Zeichen, sonst 400. `type` ist aktuell immer `"plain"`. Datumsformat ISO-8601. Fehlerformat ist **nicht** OCS-Envelope, sondern `{"status": 400, "message": "title must be provided"}` bzw. `{"status": 403, "message": "Permission denied"}`.
- API-Versionen 1.0 und 1.1 existieren; 1.1 ab Deck 1.3.0 (Attachment-Typen). Fuer unsere Operationen ist 1.0 ausreichend und breiter kompatibel.
- `deck_browse` mit `level`-Parameter (`boards` / `stacks` / `cards`) und optionalen `board_id` / `stack_id` deckt D-06 ab. Bei `level=cards` genuegt **ein** Request (`/boards/{id}/stacks`), weil Karten mitkommen. Kein N+1.

### contacts_search (CardDAV REPORT addressbook-query)

Adressbuch-Discovery:
```
PROPFIND /remote.php/dav/addressbooks/users/<uid>/
Depth: 1
```
Beachte das `users/`-Segment, das es bei Kalendern **nicht** gibt: der AddressBookRoot haengt unter der SimpleCollection `addressbooks` und heisst `users`. [VERIFIED: apps/dav/lib/RootCollection.php + CardDAV/AddressBookRoot.php]

Query:
```
REPORT /remote.php/dav/addressbooks/users/<uid>/<addressbookUri>/
Depth: 1
Content-Type: application/xml
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<c:addressbook-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag/>
    <c:address-data/>
  </d:prop>
  <c:filter test="anyof">
    <c:prop-filter name="FN">
      <c:text-match collation="i;unicode-casemap" match-type="contains">meier</c:text-match>
    </c:prop-filter>
    <c:prop-filter name="EMAIL">
      <c:text-match collation="i;unicode-casemap" match-type="contains">meier</c:text-match>
    </c:prop-filter>
  </c:filter>
  <c:limit><c:nresults>25</c:nresults></c:limit>
</c:addressbook-query>
```

Verifiziert: `test` akzeptiert `anyof` (Default) und `allof`, anderes gibt 400. `match-type` kennt `contains`, `starts-with`, `ends-with`, `equals`. `<c:limit><c:nresults>N</c:nresults></c:limit>` wird geparst. Nur **ein** `<c:filter>`-Element erlaubt. [VERIFIED: sabre lib/CardDAV/Xml/Request/AddressBookQueryReport.php]

VCF-Parsing mit `vobject`, ausgegeben werden `full_name` (FN), `emails`, `phones`, `organization`, `addressbook`, `uid`. Fehlende Properties sind der Normalfall, jeder Zugriff defensiv.

### unified_search (OCS)

```
GET /ocs/v2.php/search/providers
GET /ocs/v2.php/search/providers/{providerId}/search?term=<query>&limit=<n>&cursor=<c>
OCS-APIRequest: true
Accept: application/json
```

Verifiziert gegen `core/Controller/UnifiedSearchController.php` und `core/ResponseDefinitions.php`:

- Provider-Objekt: `id`, `appId`, `name`, `icon`, `order`, `isExternalProvider`, `triggers`, `filters` (Map Name -> Typ), `inAppSearch`.
- Ergebnis: `{ name, isPaginated, entries: [...], cursor }`.
- Entry: `thumbnailUrl`, `title`, `subline`, `resourceUrl`, `icon`, `rounded`, `attributes`. **`attributes` ist ein JSON-Objekt** (`addAttribute($key, $value)` schreibt in ein assoziatives Array), die psalm-Annotation `list<string>` im Server-Code ist irrefuehrend. [VERIFIED: lib/public/Search/SearchResultEntry.php jsonSerialize]
- **Es gibt kein `id`-Feld.** Nur der Files-Provider setzt `attributes.fileId` und `attributes.path`. [VERIFIED: apps/files/lib/Search/FilesSearchProvider.php]
- `limit` wird auf `unified-search.max-results-per-request` gedeckelt (Default laut Docblock 25) und auf mindestens 1 angehoben.
- **Ohne gueltigen Filter kommt 400** `"No valid filters provided"`. `term` muss also wirklich als Query-Parameter mitgehen; ein leerer `term` erzeugt einen Fehler, keine leere Liste. Das Tool muss leere Queries selbst abfangen.
- Der Files-Provider matcht `COMPARE_LIKE` auf `name`, also **Dateiname, nicht Inhalt**. Volltext gibt es nur mit einer zusaetzlich installierten Fulltextsearch-App. Diese Erwartung gehoert in die Tool-Description, sonst behauptet das Modell "nicht gefunden" fuer Inhalte, die existieren.
- Provider-Liste **immer zur Laufzeit abfragen**, niemals hardcoden. Sie haengt an installierten Apps. Fan-out ueber alle Provider parallel (`asyncio.gather` mit `return_exceptions=True`), pro Provider hartes Timeout, ausgefallene Provider explizit im Ergebnis als degradiert markieren.

### search / fetch (ChatGPT-Profil, TOOL-07)

Das Pflichtschema ist verifiziert, sowohl aus der OpenAI-Doku als auch aus dem offiziellen Cookbook-Referenzserver:

`search(query: str)` liefert ein Objekt mit dem Schluessel `results`, dessen Elemente `id`, `title`, `url` haben (das Cookbook liefert zusaetzlich `text` als Snippet, das ist erlaubt und nuetzlich):

```json
{"results": [{"id": "file:1234", "title": "Budget 2026.md", "text": "kurzer Auszug ...", "url": "https://cloud.example.com/f/1234"}]}
```

`fetch(id: str)` liefert ein Objekt mit `id`, `title`, `text`, `url`, `metadata`:

```json
{"id": "file:1234", "title": "Budget 2026.md", "text": "voller Inhalt ...", "url": "https://cloud.example.com/f/1234", "metadata": {"kind": "file", "path": "/Docs/Budget 2026.md"}}
```

Beide Strukturen muessen **doppelt** in der Antwort stehen: als `structuredContent` und als JSON-String im `content`-Array. [CITED: developers.openai.com/api/docs/mcp] Genau das erzeugt mcp 2.x automatisch, wenn die Tool-Funktion ein Pydantic-Modell (oder TypedDict/Dataclass mit Klassen-Annotationen) zurueckgibt: `structured_content` ist das Objekt Feld fuer Feld, `content` ist derselbe Wert als JSON-Text. [CITED: py.sdk.modelcontextprotocol.io/servers/structured-output] Also: **fuer diese zwei Tools `structured_output` NICHT abschalten.**

Parameternamen sind Teil des Vertrags: `search(query: str)` und `fetch(id: str)`, exakt so im OpenAI-Cookbook-Server. [VERIFIED: github.com/openai/openai-cookbook examples/deep_research_api/how_to_build_a_deep_research_mcp_server/main.py Zeilen 39-40, 109-110]

Weiterer Punkt aus der OpenAI-Doku: "ChatGPT creates citation metadata only when `url` is a non-empty string." Ein leerer `url` degradiert das Ergebnis zu normalem Tool-Output ohne Zitat. Also immer eine absolute, im Browser oeffnbare URL setzen.

**ID-Schema (verfeinert gegenueber D-09, mit Begruendung):**

| Kind | ID | Herkunft | Aufloesung in `fetch` |
|------|-----|----------|----------------------|
| Datei | `file:<fileid>` | `attributes.fileId` vom Files-Provider | `PROPFIND` per `oc:fileid`-Query bzw. `attributes.path` mitfuehren; einfacher und robuster: `resourceUrl` liefert `/f/<fileid>`, Inhalt via `GET /remote.php/dav/files/<uid>/<path>` mit dem aus `attributes.path` bekannten Pfad |
| Notiz | `note:<id>` | letztes Segment von `resourceUrl` | `GET /apps/notes/api/v1/notes/<id>` |
| Deck-Karte | `card:<boardId>:<stackId>:<cardId>` (kanonisch, lang) bzw. `card:<cardId>` (aus Unified Search) | `deck_browse` kennt alle drei; der Search-Provider liefert nur `cardId` | lange Form direkt per API; kurze Form ueber einen Sweep `GET /boards` + `GET /boards/{id}/stacks` mit Per-Request-Cache |
| Termin | `event:<calendarUri>:<objektname>` | aus dem `d:href` des REPORT-Ergebnisses | `GET /remote.php/dav/calendars/<uid>/<calendarUri>/<objektname>.ics` |

Zwei Abweichungen von D-09, die begruendet sind und im Plan als Praezisierung (keine Umentscheidung) laufen sollten:

1. Decks Unified-Search-Provider heisst `search-deck-card-board` und liefert `resourceUrl` = `/apps/deck/card/{cardId}` (Route `deck.page.redirectToCard`), also **nur** die cardId, kein boardId. Die in D-09 vorgesehene Form `card:<boardId>:<cardId>` ist aus Unified Search nicht herleitbar. [VERIFIED: nextcloud/deck lib/Search/DeckProvider.php + lib/Search/CardSearchResultEntry.php] Es gibt eine interne, nicht dokumentierte Route `GET /apps/deck/cards/{cardId}` (`card#read`), die als Fast Path taugt, aber nicht Teil der oeffentlichen API ist. Empfehlung: kanonische lange ID-Form, kurze Form akzeptieren, Aufloesung per Sweep, interne Route als optionaler Spike.
2. Termine per `UID` zu adressieren ist unzuverlaessig, weil der DAV-Objektname nicht zwingend `<UID>.ics` ist. Der `href`-Name ist eindeutig und direkt adressierbar.

## Graceful Degradation (SRV-04)

Ein einziger Aufruf entscheidet, welche optionalen Apps existieren:

```
GET /ocs/v2.php/cloud/capabilities
OCS-APIRequest: true
Accept: application/json
```

- Notes registriert `capabilities.notes = {api_version: ["0.2","1.0",...], version: "6.0.1"}`. [CITED: nextcloud/notes docs/api/README.md]
- Deck registriert `capabilities.deck = {version, canCreateBoards, apiVersions: ["1.0","1.1"]}`. [VERIFIED: nextcloud/deck lib/Capabilities.php]
- Kalender und Kontakte brauchen **keine** App: CalDAV und CardDAV sind im Core-`dav`-App. Die Calendar- und Contacts-Apps sind nur die Web-UI. Kalender-Tools funktionieren also auch ohne installierte Calendar-App, solange ein Kalender existiert (siehe Pitfall 3).
- `deck.canCreateBoards = false` ist die ehrliche Vorab-Antwort fuer `deck_create_card`, wenn der Nutzer keine Board-Rechte hat.

Umsetzungsempfehlung:
- Capabilities einmal pro Credential-Kontext mit kurzer TTL (60 s) cachen, **ohne** dass Korrektheit davon abhaengt (kein Session-State, D-20: der Cache ist reine Latenz-Optimierung und darf jederzeit leer sein).
- Bei fehlender App: Exception mit `message` + `hint`, Beispiel `"The Notes app is not installed on this Nextcloud."` / `"Ask an administrator to install the Notes app, or use files_search for note files under /Notes."`
- `tools/list` bleibt **statisch** ueber alle 15 Tools. Dynamisch filtern klingt eleganter, bricht aber die Token-Budget-Messbarkeit, macht das Listing credential-abhaengig (also nicht cachebar) und ueberrascht Clients, die Tool-Listen persistieren. Die klare Fehlermeldung ist der bessere Weg und genau das, was SRV-04 verlangt.

## Architecture Patterns

### System Architecture Diagram

```
MCP-Client (Claude Desktop / Claude Code / Cursor / ChatGPT / MCP Inspector)
   |                                     |
   | stdio (Subprozess)                  | Streamable HTTP POST /mcp
   |                                     | Authorization: Basic <user:app-pw>  (Passthrough)
   |                                     |   ODER Bearer <static>               (Single-User)
   v                                     v
+-- entry_stdio.py ------+   +-- entry_http.py -----------------------------+
| mcp.run()              |   | app = mcp.streamable_http_app(              |
| Credentials aus Env    |   |       transport_security=TransportSecurity  |
+-----------+------------+   |       ...)                                  |
            |                | + optional TokenVerifier (Bearer-Modus)     |
            |                +---------------------+-----------------------+
            |                                      |
            +----------------+---------------------+
                             v
              +-- server.py (MCP-Server-Layer) -----------------+
              | Registry: 15 @mcp.tool()-Wrapper                |
              |  - ToolAnnotations pro Tool (D-16)              |
              |  - structured_output=False bei 13 Tools         |
              |  - graceful(): Exception -> message+hint        |
              |  - resolve_credentials(ctx) einmal pro Call     |
              +----------------------+--------------------------+
                                     v
              +-- tools/ (freistehende async Funktionen) --------+
              | files.py calendar.py notes.py deck.py           |
              | contacts.py search.py chatgpt.py                |
              | Signatur: (clients: NcClients, ...) -> dict     |
              | Kein mcp-Import, kein Env-Zugriff               |
              +----------------------+--------------------------+
                                     v
              +-- nextcloud/ -----------------------------------+
              | credentials.py  Credentials (url, user, secret) |
              | http.py         AsyncClient pro Event-Loop      |
              | clients/dav.py      SEARCH / PROPFIND / GET/PUT |
              | clients/caldav.py   REPORT calendar-query + PUT |
              | clients/carddav.py  REPORT addressbook-query    |
              | clients/notes.py    JSON-REST v1                |
              | clients/deck.py     JSON-REST v1.0              |
              | clients/ocs.py      capabilities + search       |
              +----------------------+--------------------------+
                                     v
                     Nextcloud 34 (Docker, compose.test.yml)
                     remote.php/dav | ocs/v2.php | index.php/apps/*
                     ACLs greifen serverseitig, immer
```

Datenfluss eines Tool-Calls, drei Regeln, die den Rest bestimmen:
1. Die Identitaet fliesst genau einen Weg: Env (stdio) bzw. Request-Header (HTTP) -> `Credentials`-Objekt -> `NcClients` -> Nextcloud. Kein Tool-Parameter, keine globale Variable, kein Default-Admin.
2. `tools/` kennt nur `NcClients`. Damit laeuft identischer Tool-Code unter stdio, HTTP und (ab Phase 2) ExApp-Impersonation, ohne Aenderung.
3. `server.py` ist der einzige Ort mit `mcp`-Imports. Das haelt alle Tool-Funktionen mit respx unit-testbar und macht den Token-Budget-Check zu einer reinen Registry-Frage.

### Recommended Project Structure

```
nextcloud-mcp-connector/
├── pyproject.toml
├── uv.lock
├── README.md                        # inkl. App-ID-Freeze-Notiz (D-01) und Permission-Tabelle (TOOL-09)
├── LICENSE                          # AGPL-3.0-or-later (existiert)
├── compose.test.yml                 # nextcloud:34-apache, SQLite
├── scripts/
│   ├── bootstrap_test_nc.sh         # idempotent: Apps, User, Kalender, Adressbuch, App-Passwoerter
│   └── check_tool_budget.py         # CI-Gate fuer tools/list
├── src/mcp_connector/
│   ├── __init__.py
│   ├── server.py                    # Registry + Annotationen + graceful-Wrapper
│   ├── entry_stdio.py               # console_script nc-mcp
│   ├── entry_http.py                # ASGI app fuer uvicorn
│   ├── config.py                    # Env-Parsing, Modus-Auswahl, keine Secrets im Log
│   ├── errors.py                    # ToolError(message, hint), AppMissingError, ConflictError
│   ├── ids.py                       # file:/note:/card:/event: encode + parse (ein Ort!)
│   ├── models.py                    # SearchResults/SearchHit/FetchResult (nur ChatGPT-Profil)
│   ├── tools/
│   │   ├── files.py  calendar.py  notes.py  deck.py
│   │   ├── contacts.py  search.py  chatgpt.py
│   └── nextcloud/
│       ├── credentials.py  http.py  capabilities.py
│       └── clients/
│           ├── dav.py  caldav.py  carddav.py
│           ├── notes.py  deck.py  ocs.py
│           └── xml.py               # lxml-Builder + Namespace-Konstanten
└── tests/
    ├── conftest.py                  # anyio_backend, Credentials-Fixtures, respx-Router
    ├── fixtures/                    # echte Antwort-Bodies (207-XML, ICS, VCF, JSON)
    ├── unit/                        # Tool-Funktionen mit respx, alle Pfade
    ├── contract/                    # In-Memory Client: Namen, Annotationen, Schemas, Budget
    ├── integration/                 # gegen Docker-NC, per Marker + Env-Guard
    └── compat/legacy_client_check.py  # eigenes Env mit mcp 1.29
```

### Pattern 1: Credential-Provider als Parameter-Objekt

```python
# nextcloud/credentials.py
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Credentials:
    base_url: str      # ohne Trailing Slash
    user: str
    secret: str        # App-Passwort. __repr__ NIE ueberschreiben ohne Maskierung.

    def __repr__(self) -> str:                 # verhindert Leaks in Tracebacks
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, secret='***')"
```

**What:** Ein unveraenderliches Objekt, das jede Client-Methode als erstes Argument bekommt (oder das der `NcClients`-Container haelt).
**When to use:** Immer. Es ist die Naht, an der Phase 2 die AppAPI-Impersonation einhaengt, ohne Tool-Code anzufassen.
**Warum kein Modul-globaler Client:** Im HTTP-Passthrough-Modus wechseln die Credentials pro Request. Ein globaler Client waere ein Cross-User-Leak.

### Pattern 2: Ein httpx.AsyncClient pro Event-Loop, Auth pro Request

```python
# nextcloud/http.py
import asyncio, weakref, httpx

_clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, httpx.AsyncClient]" = weakref.WeakKeyDictionary()

def shared_client() -> httpx.AsyncClient:
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0, read=30.0),
            follow_redirects=False,          # Redirect wuerde den Auth-Header verlieren
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": "nextcloud-mcp-connector/0.1"},
        )
        _clients[loop] = client
    return client
```

**What:** Connection-Pooling ohne globalen State, der ueber Loops hinweg bricht. Auth wird pro Request mitgegeben (`auth=httpx.BasicAuth(c.user, c.secret)`), nicht am Client gesetzt.
**Warum `follow_redirects=False`:** Ein Cross-Host-Redirect wuerde den Authorization-Header an ein fremdes Ziel schicken oder verlieren (dokumentierte Fehlerklasse in der Projekt-Pitfalls-Research). Redirects stattdessen explizit als Konfigurationsfehler melden ("your Nextcloud URL redirects; use the final URL, including https and any subpath").
**Timeouts:** Ohne Timeout haengt ein Tool-Call bis zum Client-Timeout. 30 s Read ist grosszuegig fuer DAV-REPORTs auf grossen Kalendern.

### Pattern 3: Graceful-Wrapper an genau einer Stelle

```python
# server.py (Skizze)
import functools, json
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from .errors import ToolError

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATE_ONLY = ToolAnnotations(read_only_hint=False, destructive_hint=False,
                              idempotent_hint=False, open_world_hint=False)

def compact(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

def graceful(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:                 # message + hint, Modell kann reagieren
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
        except httpx.TimeoutException:
            raise ValueError("Nextcloud did not respond in time. Hint: retry with a smaller "
                             "time range or a narrower search scope.") from None
    return wrapper
```

**What:** Jede Tool-Registrierung geht durch `graceful`. Kein einzelner Tool-Wrapper darf eigene Fehlerformate erfinden.
**Warum `ValueError` und nicht `MCPError`:** siehe Fehlertabelle oben, das Modell soll die Chance zur Selbstkorrektur bekommen.
**Wichtig:** `from None` unterdrueckt die Exception-Chain. Das ist hier bewusst: ein httpx-Traceback kann URLs mit Credentials enthalten.

### Pattern 4: Stateless Pagination ueber Handles (D-20, SRV-05)

Jede Liste, die abgeschnitten wird, liefert im JSON ein opakes `next` mit allen Informationen, die den Folgeaufruf reproduzierbar machen, und das Tool nimmt es als normalen optionalen Parameter `cursor` wieder an:

```json
{"items": [...], "truncated": true, "next": "eyJvIjoyNSwicSI6ImJ1ZGdldCJ9"}
```

Inhalt des Handles: base64url von kompaktem JSON, zum Beispiel `{"o": 25, "q": "budget", "s": "/files/alice/Docs"}`. **Kein** Server-State, keine Signatur (es enthaelt keine Geheimnisse und keine Autoritaet, die Credentials kommen weiterhin aus dem Auth-Kanal). Beim Parsen defensiv sein: ungueltiger Cursor -> `ToolError` mit Hinweis, nie Crash.

Fuer OCS Unified Search ist der Cursor serverseitig vorgegeben (`cursor` im Ergebnis, `int|string|null`) und wird einfach durchgereicht.

### Pattern 5: ID-Codec an einem Ort

`ids.py` enthaelt `encode_file(fileid)`, `parse(id) -> (kind, parts)` und die zugehoerigen Tests. Jeder Tool-Code, der IDs bildet oder liest, geht darueber. Grund: `fetch` ist die einzige Stelle, an der ein falsch geformter Praefix zu stiller Fehlaufloesung fuehren kann (Karte statt Notiz), und ein zentraler Codec macht das per Property-Test pruefbar (`parse(encode(x)) == x` fuer alle vier Arten).

### Anti-Patterns to Avoid

- **`stateless_http=True` "weil modern".** In v2 betrifft es ausschliesslich das Legacy-Leg und kostet dort beide Rueckkanaele. Es ist genau der Fehler aus #227. Nicht setzen.
- **`tools/list` dynamisch nach installierten Apps filtern.** Macht das Listing credential-abhaengig, zerstoert die Cachebarkeit und die Token-Budget-Messung, und ueberrascht Clients mit persistierten Tool-Listen. Klare Fehlermeldung statt verstecktem Tool.
- **Nutzername als Tool-Parameter** (auch nicht "optional, fuer Admins"). Confused Deputy. Der Nutzer kommt aus dem Auth-Kanal, Punkt.
- **DAV-XML per f-String bauen.** Ein nicht escapter Suchbegriff mit `&` oder `<` erzeugt 400er, die nach "Nextcloud kaputt" aussehen. lxml baut und escapt.
- **ICS/VCF per String-Konkatenation.** Genau der Ursprung der Platzhirsch-Bugs #544/#782.
- **`follow_redirects=True` auf dem Nextcloud-Client.** Header-Leak beziehungsweise stiller Auth-Verlust.
- **Auth-Retry bei 401.** Fuettert Nextclouds Brute-Force-Schutz, der auf Quell-IP zaehlt, und verlangsamt danach **alle** Nutzer des Servers. Einmal fehlgeschlagen heisst: klarer Fehler ans Modell, kein zweiter Versuch.
- **Credentials im Log, auch nicht auf DEBUG.** `MCPServer(log_level=...)` konfiguriert den **Root**-Logger. Ein `log_level="DEBUG"` schaltet damit auch httpx-Logging an. Deshalb: Logger-Namen `mcp_connector.*`, httpx-Logger explizit auf WARNING, und `Credentials.__repr__` maskiert.
- **Ein Tool pro Deck-Ebene.** D-06 sagt bewusst ein Tool mit `level`-Parameter; drei Tools kosten Token-Budget und Client-Slots ohne Mehrwert.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP-Sessions, Protokoll-Aeren, `initialize` vs `server/discover` | Eigene Transport-Logik oder Aera-Weichen | `mcp.streamable_http_app()` unkonfiguriert | Das SDK routet pro Request; jeder eigene Eingriff ist die #227-Falle |
| Recurrence-Expansion (RRULE, EXDATE, DST) | Eigene Iteration oder recurring-ical-events | `<c:expand start end>` im calendar-query | sabre expandiert serverseitig, liefert absolute Zeiten, Default-Zone UTC |
| VTIMEZONE, DTSTART/DTEND, VALUE=DATE | ICS-Strings zusammenbauen | icalendar 7.x | RFC 5545 hat mehr Sonderfaelle als jedes Budget; hier sitzen die Wettbewerber-Bugs |
| vCard-Parsing (Multi-Value, Escaping, v3 vs v4) | Regex auf VCF | vobject | Gleiche Begruendung |
| XML-Namespaces, Escaping, Multistatus-Parsing | f-Strings und String-Suche | lxml (`etree.SubElement`, `xpath` mit Namespace-Map) | 400er durch nicht escapte Suchbegriffe sind sonst garantiert |
| Ueberschreib-Schutz beim Upload | Existenzcheck plus PUT (Race) | `If-None-Match: *` -> 412 vom Server | Atomar auf Serverseite, sabre prueft Preconditions fuer jede Methode |
| Volltextsuche ueber Dateien | Eigener Index, Embeddings, Grep-Schleife | OCS Unified Search (und Erwartung ehrlich dokumentieren) | Berechtigungstreu und ohne Infrastruktur; eigener Index driftet gegen ACLs |
| App-Erkennung | Try/Except um jeden Aufruf und Fehler raten | Ein `GET /ocs/v2.php/cloud/capabilities` | Liefert Notes- und Deck-Version plus `canCreateBoards` in einem Roundtrip |
| Test-Nextcloud | Manuelle Installationsanleitung im README | `compose.test.yml` + idempotentes `bootstrap_test_nc.sh` | Lokal und in CI derselbe Pfad; ohne das divergieren die Umgebungen sofort |
| Test-Doubles fuer den MCP-Layer | Handgeschriebene Fake-Clients | `Client(mcp)` (In-Memory-Transport) | Geht durch den echten Protokoll-Layer inklusive Schema-Validierung |
| Token-Zaehlung | tiktoken einbinden und ein Modell waehlen | Byte-Groesse der serialisierten `tools/list`-Antwort als Proxy | Deterministisch, dependency-frei, reicht fuer ein Budget-Gate voellig |

**Key insight:** In dieser Phase liegt der gesamte schwierige Teil in Formaten, die andere Leute seit 20 Jahren pflegen (iCalendar, vCard, WebDAV-XML) und in einem Protokoll, das sich gerade in zwei Aeren geteilt hat. Jede Zeile, die wir davon selbst schreiben, ist eine Zeile, die wir gegen Randfaelle testen muessen, die wir noch nicht kennen. Der Eigenanteil des Projekts ist die Kuration, die Antwortkompaktheit und die Ehrlichkeit der Fehlermeldungen, nicht die Formatarbeit.

## Common Pitfalls

### Pitfall 1: `stateless_http` beziehungsweise die #227-Fehlerklasse in die eigene Codebase holen

**What goes wrong:** Man liest "Spec 2026-07-28 ist stateless" und setzt `stateless_http=True`. Moderne Clients funktionieren, aber jeder Client mit SDK 1.28/1.29 (Claude Code, viele Agenten) bekommt nach `initialize` "Session terminated" beziehungsweise verliert jeden Rueckkanal.
**Why it happens:** Der Flag-Name legt nahe, er waehle die Protokoll-Aera. Tut er nicht. In v2 wird der Request nach `MCP-Protocol-Version` geroutet und der 2026er-Pfad kehrt zurueck, **bevor** `stateless_http` gelesen wird.
**How to avoid:** Flag nicht setzen. Beide Aeren sind ohnehin immer an. Multi-Worker mit Legacy-Clients ueber Sticky Sessions loesen.
**Warning signs:** "Session terminated" im Client-Log; `NoBackChannelError`; Verhalten unterscheidet sich zwischen erstem und zweitem Aufruf.
**Verification:** `tests/compat/legacy_client_check.py` in einem `uv run --isolated --with "mcp>=1.29,<2"`-Environment gegen den laufenden HTTP-Server, plus derselbe Ablauf mit dem 2.x-Client. Beides muss gruen sein. Das ist Success Criterion 2.

### Pitfall 2: Basic-Passthrough am SDK-Auth-Layer vorbei (oder mitten hinein)

**What goes wrong:** Zwei Varianten. (a) Man setzt `auth=AuthSettings(...)` + `token_verifier=...` und schickt dann Basic-Credentials: `BearerAuthBackend` gibt `None` zurueck, `RequireAuthMiddleware` antwortet 401, kein Tool laeuft, und das Log sagt nur "Authentication required". (b) Man liest den Header im Tool aus, konfiguriert aber `auth=` gar nicht und wundert sich, dass `get_access_token()` immer `None` ist.
**Why it happens:** Der SDK-Auth-Layer ist ausschliesslich fuer OAuth-Bearer gebaut (`auth_header.lower().startswith("bearer ")`), und `get_access_token()` haengt daran.
**How to avoid:** Zwei exklusive Modi, per Env gewaehlt (siehe Tabelle oben). Im Passthrough-Modus `auth=`/`token_verifier=` **nicht** setzen und `ctx.headers.get("authorization")` lesen. Im Static-Bearer-Modus beide setzen und den Nextcloud-Zugang aus Env nehmen. Beide Modi in einem Test abdecken, inklusive "kein Header vorhanden" -> `MCPError` mit brauchbarem Hinweis.
**Warning signs:** 401 ohne Eintrag im eigenen Log; `get_access_token()` ist `None` obwohl ein Token geschickt wurde; funktioniert per stdio, nicht per HTTP.

### Pitfall 3: Ein per occ erzeugter Nutzer hat keinen Kalender und kein Adressbuch

**What goes wrong:** `calendar_list_events` liefert leere Listen oder 404, `contacts_search` findet nichts, obwohl Nextcloud laeuft und die Credentials stimmen. Man sucht Stunden im eigenen CalDAV-XML.
**Why it happens:** Nextcloud legt den Default-Kalender (`personal`) und das Default-Adressbuch (`contacts`) im `UserEventsListener::firstLogin()` an, ausgeloest von `UserFirstTimeLoggedInEvent`. `occ user:add` feuert dieses Event nicht. [VERIFIED: apps/dav/lib/Listener/UserEventsListener.php Zeile 157ff, apps/dav/lib/CalDAV/CalDavBackend.php Zeile 119f, apps/dav/lib/CardDAV/CardDavBackend.php Zeile 40f]
**How to avoid:** Im Bootstrap explizit `occ dav:create-calendar <user> personal` und `occ dav:create-addressbook <user> contacts`. Das `name`-Argument wird direkt als **URI** verwendet, ist also deterministisch. [VERIFIED: apps/dav/lib/Command/CreateCalendar.php: `$caldav->createCalendar("principals/users/$user", $name, [])`] Verifizieren mit `occ dav:list-calendars <user>`.
**Zusaetzlich fuer das Tool selbst:** Wenn die Kalender-Discovery **null** VEVENT-Collections findet, ist die richtige Antwort nicht "keine Termine", sondern ein Fehler mit Hinweis: `"No calendar found for this account. Hint: open the Calendar app once in the web UI, or ask an admin to run occ dav:create-calendar."` Sonst behauptet das Modell wahrheitswidrig, der Nutzer habe keine Termine.
**Warning signs:** PROPFIND auf `calendars/<uid>/` liefert nur die eigene Collection ohne Kinder; `dav:list-calendars` ist leer.

### Pitfall 4: CalDAV-Zeitformate und Ganztages-Termine

**What goes wrong:** 400er, die wie ein Server-Bug aussehen; Termine, die um einen Tag verschoben sind; DST-Uebergaenge, an denen ein Termin doppelt oder gar nicht erscheint.
**Why it happens:** Drei unabhaengige Ursachen. (1) `time-range`/`expand` verlangen iCalendar-UTC (`20260901T000000Z`), nicht ISO-8601 mit Trennzeichen. (2) `<c:expand>` braucht **beide** Attribute und `end > start`, sonst wirft sabre `BadRequest`. (3) `DTSTART;VALUE=DATE` ist ein Datum ohne Zeitzone; wer es als Mitternacht interpretiert und in eine Zone konvertiert, verschiebt es.
**How to avoid:** Genau eine Konvertierungsfunktion `to_caldav_utc(dt)`, die auf naive Datetimes mit `ValueError` reagiert. Ganztages-Termine als `all_day: true` mit reinem Datum ausgeben. Testmatrix mit vier Faellen als Pflicht: (a) Termin in `Europe/Berlin`, gelesen mit UTC-Fenster, (b) wiederkehrender Termin ueber die DST-Grenze Ende Oktober, (c) Ganztages-Termin, (d) Fenster, das exakt auf der Termin-Grenze endet.
**Warning signs:** 400 mit `BadRequest` im DAV-Body; Termine mit Offset von genau 1 oder 2 Stunden; ein wiederkehrender Termin, der im Fenster fehlt.

### Pitfall 5: Erwartung "Suche findet Inhalte"

**What goes wrong:** Das Modell ruft `files_search` mit einem Satz aus dem Dokument auf, bekommt nichts, und schreibt dem Nutzer "die Datei existiert nicht".
**Why it happens:** WebDAV SEARCH matcht Properties (Name, Mimetype, Groesse, Datum). Der Files-Unified-Search-Provider matcht `LIKE` auf `name`. Volltext gibt es nur mit einer separat installierten Fulltextsearch-App. [VERIFIED: FileSearchBackend, FilesSearchProvider]
**How to avoid:** In beiden Tool-Descriptions **einen** Satz, der es klarstellt ("matches file and folder names, not file contents"). Bei null Treffern nicht nur `[]` liefern, sondern ein Feld `note: "matched on names only; contents are not indexed"`. Das ist ein Token gut investiert, weil es eine ganze Klasse falscher Modellaussagen verhindert.
**Warning signs:** Nutzer melden "findet meine Dokumente nicht", obwohl die Web-UI sie findet (die kann je nach Installation zusaetzliche Provider haben).

### Pitfall 6: 421 Misdirected Request nach dem ersten Deployment

**What goes wrong:** Lokal laeuft alles, hinter einem Hostnamen antwortet **jeder** Request mit 421, und der Client zeigt nur einen generischen Transport-Fehler.
**Why it happens:** `streamable_http_app()` armiert ohne `transport_security=` den DNS-Rebinding-Schutz mit einer Localhost-Allowlist. Die Pruefung laeuft vor allem MCP-Code, der Grund steht nur als eine Warnung im Server-Log. `host=`-Setzen allowlistet nichts. [CITED: run/deploy]
**How to avoid:** `NC_MCP_ALLOWED_HOSTS` als Env von Tag 1, daraus `TransportSecuritySettings(allowed_hosts=[...])`, und pro Hostname **zwei** Eintraege (`example.com` und `example.com:*`). Hinter einem Proxy, der den Host-Header kontrolliert, ehrlich `enable_dns_rebinding_protection=False`. Ein Integrationstest, der mit fremdem Host-Header 421 erwartet und mit erlaubtem Host 200, dokumentiert das Verhalten fuer Phase 2/3.
**Warning signs:** `curl` bekommt 421 mit Plaintext-Body "Invalid Host header"; im Log genau eine Warnung.

### Pitfall 7: stdout-Verschmutzung im stdio-Modus

**What goes wrong:** Der Client bricht mit JSON-Parse-Fehlern ab, obwohl der Server funktioniert.
**Why it happens:** Bei stdio **ist** stdout die Leitung. v2 haertet das deutlich (der Wire liegt auf privaten Deskriptoren, geflushter stdout-Output wird nach stderr umgeleitet), aber Output, der **vor** dem Serving-Start geflusht wird (Import-Zeit-Print, Wrapper-Skript-Echo), landet weiterhin auf der Leitung, ebenso ein `print()`, das erst beim Interpreter-Exit gedraint wird. [CITED: py.sdk.modelcontextprotocol.io/run]
**How to avoid:** Kein `print()` im Paket, ueberall `logging` (Handler flusht pro Record nach stderr). Kein Modul-Level-Code mit Ausgabe. `mcp.run()` unter `if __name__ == "__main__":`, weil alles, was den Server laedt, die Datei importiert. Ein Test, der `nc-mcp` als Subprozess startet, `initialize` schickt und prueft, dass die erste stdout-Zeile valides JSON-RPC ist.
**Warning signs:** Client meldet ungueltiges JSON; funktioniert unter `mcp dev`, nicht im echten Host.

### Pitfall 8: Brute-Force-Schutz macht den ganzen Server langsam

**What goes wrong:** Sporadische Latenzen bis 25 Sekunden, dann 429, und danach ist "der MCP-Server kaputt" fuer alle Nutzer.
**Why it happens:** Nextclouds Brute-Force-Schutz zaehlt pro Quell-IP. Ein Remote-MCP-Server ist eine IP fuer viele Nutzer. Ein abgelaufenes App-Passwort plus automatischer Retry reicht.
**How to avoid:** **Niemals** einen fehlgeschlagenen Auth-Versuch wiederholen. 401 wird zu einer klaren Meldung ("app password rejected; generate a new one in Nextcloud settings"), 429 zu einer eigenen Meldung mit Wartehinweis. Im Test-Setup den Schutz abschalten (`occ config:system:set auth.bruteforce.protection.enabled --value=false --type=boolean`), damit Negativ-Tests nicht die eigene CI drosseln. Fuer den Admin-Teil der Doku: `occ security:bruteforce:reset <ip>`.
**Warning signs:** Antwortzeiten kriechen Richtung 25 s; 429er; nach einem erfolgreichen Login ist alles wieder schnell.

### Pitfall 9: Deck-Fehlerformat und Pflicht-Header

**What goes wrong:** Deck-Requests kommen als HTML-Loginseite zurueck, oder Fehler lassen sich nicht parsen.
**Why it happens:** Deck verlangt `OCS-APIRequest: true` **und** `Content-Type: application/json` fuer alle API-Requests, antwortet aber **nicht** im OCS-Envelope, sondern mit `{"status": 4xx, "message": "..."}`. Wer einen `ocs.meta`-Parser darauf loslaesst, bekommt KeyErrors. [CITED: nextcloud/deck docs/API.md]
**How to avoid:** Getrennte Response-Handler: `parse_ocs()` fuer `/ocs/v2.php/*`, `parse_app_json()` fuer Notes und Deck. Der Deck-Client setzt beide Header immer, auch bei GET.

### Pitfall 10: Unified-Search-Ergebnisse ohne stabile ID

**What goes wrong:** `search`/`fetch` liefern IDs, die `fetch` nicht mehr aufloesen kann, oder ein Praefix zeigt auf den falschen Ressourcentyp.
**Why it happens:** `CoreUnifiedSearchResultEntry` hat kein `id`. Nur Files setzt `attributes.fileId`/`attributes.path`. Notes und Deck liefern die ID ausschliesslich in der `resourceUrl`, und Decks Provider heisst `search-deck-card-board` und gibt nur die `cardId`. [VERIFIED: ResponseDefinitions.php, FilesSearchProvider.php, notes SearchProvider.php, deck CardSearchResultEntry.php]
**How to avoid:** Ein zentraler `ids.py`-Codec plus eine Provider-zu-Kind-Mapping-Tabelle mit einer explizit unbekannten Kategorie: Provider, die wir nicht kennen, kommen in `search`-Ergebnisse mit einer ID vom Typ `url:<absolute-url>`, und `fetch` beantwortet die ehrlich mit "this result type cannot be fetched; open the url". Besser eine ehrliche Grenze als eine falsche Aufloesung. Property-Test: `parse(encode(x)) == x` fuer alle Arten.

## Code Examples

### Tool-Registrierung mit Annotationen und Schema-Diaet

```python
# src/mcp_connector/server.py
from typing import Annotated
from pydantic import Field
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations

from .tools import files as files_tools

mcp = MCPServer(
    "MCP Connector",
    version="0.1.0",
    instructions=(
        "Read and create content in the user's own Nextcloud. "
        "This server can never delete, overwrite or re-share anything."
    ),
)

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATE_ONLY = ToolAnnotations(read_only_hint=False, destructive_hint=False,
                              idempotent_hint=False, open_world_hint=False)


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_read(
    path: Annotated[str, Field(description="Path inside the user's files, e.g. /Docs/notes.md")],
    offset: Annotated[int, Field(ge=0, description="Byte offset for continued reads")] = 0,
    ctx: Context = None,
) -> str:
    """Read a text file from Nextcloud. Truncates large files and returns a next offset."""
    clients = await resolve_clients(ctx)
    return compact(await files_tools.read(clients, path=path, offset=offset))


@mcp.tool(annotations=CREATE_ONLY, structured_output=False)
@graceful
async def files_upload(
    path: Annotated[str, Field(description="Target path; must not exist yet")],
    content: Annotated[str, Field(description="UTF-8 text content")],
    ctx: Context = None,
) -> str:
    """Create a new text file. Fails if the target already exists; never overwrites."""
    clients = await resolve_clients(ctx)
    return compact(await files_tools.upload(clients, path=path, content=content))
```

Anmerkungen, die im Plan Zeit sparen: `structured_output=False` ist der Grund, warum diese beiden Tools kein `output_schema` in `tools/list` haben. `ctx: Context` ist im Input-Schema **nicht** sichtbar (die SDK-Injektion ist fuer das Modell unsichtbar). Die Docstring ist die Description, deshalb eine Zeile, praezise, mit dem wichtigsten Constraint darin.

### Create-only Upload

```python
# src/mcp_connector/nextcloud/clients/dav.py
import httpx
from ..credentials import Credentials
from ...errors import ToolError

async def put_new_file(client: httpx.AsyncClient, c: Credentials, path: str,
                       data: bytes, content_type: str) -> dict:
    url = f"{c.base_url}/remote.php/dav/files/{c.user}{quote_path(path)}"
    r = await client.put(
        url,
        content=data,
        headers={"If-None-Match": "*", "Content-Type": content_type},
        auth=httpx.BasicAuth(c.user, c.secret),
    )
    if r.status_code == 412:
        raise ToolError(
            message=f"A file already exists at {path}.",
            hint="This server never overwrites files. Pick a different name.",
        )
    if r.status_code == 403:
        raise ToolError(message=f"No permission to write to {path}.",
                        hint="Check the folder's share permissions in Nextcloud.")
    if r.status_code == 404:
        raise ToolError(message=f"The parent folder of {path} does not exist.",
                        hint="Create the folder in Nextcloud first, or use an existing path.")
    r.raise_for_status()
    return {"path": path, "etag": r.headers.get("etag"), "created": True}
```

Quelle des 412-Verhaltens: sabre/dav prueft `If-None-Match: *` in `checkPreconditions()`, aufgerufen aus `invokeMethod()` fuer jede HTTP-Methode. [VERIFIED: sabre-io/dav lib/DAV/Server.php Zeilen 466, 1348-1365]

### CalDAV-Query mit serverseitiger Expansion

```python
# src/mcp_connector/nextcloud/clients/caldav.py
from datetime import datetime, timezone
from lxml import etree

DAV = "DAV:"
CAL = "urn:ietf:params:xml:ns:caldav"
NS = {"d": DAV, "c": CAL}

def to_caldav_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def build_calendar_query(start: datetime, end: datetime) -> bytes:
    s, e = to_caldav_utc(start), to_caldav_utc(end)
    root = etree.Element(f"{{{CAL}}}calendar-query", nsmap={"d": DAV, "c": CAL})
    prop = etree.SubElement(root, f"{{{DAV}}}prop")
    etree.SubElement(prop, f"{{{DAV}}}getetag")
    cdata = etree.SubElement(prop, f"{{{CAL}}}calendar-data")
    etree.SubElement(cdata, f"{{{CAL}}}expand", start=s, end=e)
    filt = etree.SubElement(root, f"{{{CAL}}}filter")
    vcal = etree.SubElement(filt, f"{{{CAL}}}comp-filter", name="VCALENDAR")
    vev = etree.SubElement(vcal, f"{{{CAL}}}comp-filter", name="VEVENT")
    etree.SubElement(vev, f"{{{CAL}}}time-range", start=s, end=e)
    return etree.tostring(root, xml_declaration=True, encoding="utf-8")
```

`<c:expand>` verlangt beide Attribute und `end > start`, sonst 400. Die Expansion nutzt die `calendar-timezone`-Property und defaultet auf UTC. [VERIFIED: sabre lib/CalDAV/Xml/Filter/CalendarData.php, lib/CalDAV/Plugin.php]

### ChatGPT-Profil mit Output-Schema

```python
# src/mcp_connector/models.py
from pydantic import BaseModel

class SearchHit(BaseModel):
    id: str
    title: str
    url: str
    text: str = ""

class SearchResults(BaseModel):
    results: list[SearchHit]

class FetchResult(BaseModel):
    id: str
    title: str
    text: str
    url: str
    metadata: dict[str, str] | None = None
```

```python
# src/mcp_connector/server.py (Fortsetzung)
@mcp.tool(annotations=READ_ONLY)          # KEIN structured_output=False!
@graceful
async def search(query: str, ctx: Context = None) -> SearchResults:
    """Search the user's Nextcloud for files, notes, cards and events."""
    clients = await resolve_clients(ctx)
    return SearchResults(results=await chatgpt_tools.search(clients, query))


@mcp.tool(annotations=READ_ONLY)
@graceful
async def fetch(id: str, ctx: Context = None) -> FetchResult:
    """Fetch the full content of one search result by its id."""
    clients = await resolve_clients(ctx)
    return FetchResult(**await chatgpt_tools.fetch(clients, id))
```

Weil ein Pydantic-Modell zurueckkommt, erzeugt das SDK `structured_content` als Objekt Feld fuer Feld **und** `content` als JSON-Text desselben Objekts, genau die von OpenAI verlangte Doppelung. [CITED: py.sdk.modelcontextprotocol.io/servers/structured-output, developers.openai.com/api/docs/mcp]

### Contract-Test: Annotationen, Namen, Schema-Diaet

```python
# tests/contract/test_tool_contract.py
import pytest
from mcp import Client
from mcp_connector.server import mcp

EXPECTED = {
    "files_search", "files_list", "files_read", "files_upload",
    "calendar_list_events", "calendar_create_event",
    "notes_search", "notes_read", "notes_create",
    "deck_browse", "deck_create_card",
    "contacts_search", "unified_search", "search", "fetch",
}
CREATE_TOOLS = {"files_upload", "calendar_create_event", "notes_create", "deck_create_card"}
STRUCTURED = {"search", "fetch"}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_tool_surface():
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}

    assert set(tools) == EXPECTED, "tool set drifted from the curated 15"

    for name, tool in tools.items():
        a = tool.annotations
        assert a is not None, f"{name} has no annotations"
        assert a.open_world_hint is False
        if name in CREATE_TOOLS:
            assert a.read_only_hint is False
            assert a.destructive_hint is False        # das Sicherheitsversprechen
            assert a.idempotent_hint is False
        else:
            assert a.read_only_hint is True
        has_schema = getattr(tool, "output_schema", None) is not None
        assert has_schema == (name in STRUCTURED), f"{name}: unexpected output schema"
```

### Token-Budget-Gate

```python
# scripts/check_tool_budget.py
import asyncio, json, sys
from mcp import Client
from mcp_connector.server import mcp

BUDGET_BYTES = 24_000          # ~6k Tokens bei ~4 Bytes/Token

async def main() -> int:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()
    payload = result.model_dump(by_alias=True, exclude_none=True, mode="json")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    size = len(blob.encode("utf-8"))
    per_tool = sorted(
        ((len(json.dumps(t, separators=(",", ":"))), t["name"]) for t in payload["tools"]),
        reverse=True,
    )
    print(f"tools/list: {size} bytes, {len(payload['tools'])} tools, budget {BUDGET_BYTES}")
    for n, name in per_tool[:5]:
        print(f"  {name}: {n} bytes")
    if size > BUDGET_BYTES:
        print("FAIL: tools/list exceeds the token budget", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

Warum Bytes und nicht Tokens: es braucht keine Modellwahl, kein zusaetzliches Paket, ist deterministisch und reproduzierbar, und die Groessenordnung reicht fuer ein Gate voellig. Die Top-5-Ausgabe macht Regressionen sofort zuordenbar. Der Startwert 24.000 Bytes ist bewusst als Startwert markiert: erste Messung nach Fertigstellung aller 15 Tools durchfuehren und den Wert dann auf gemessen plus 15 Prozent Reserve festnageln, damit das Gate scharf ist statt dekorativ.

## Test-Umgebung: Docker-Nextcloud und CI

### compose.test.yml

```yaml
# compose.test.yml
services:
  nextcloud:
    image: nextcloud:34-apache          # 34.0.2 ist current stable (2026-08-12)
    ports: ["8080:80"]
    environment:
      SQLITE_DATABASE: nextcloud        # kein separater DB-Container
      NEXTCLOUD_ADMIN_USER: admin
      NEXTCLOUD_ADMIN_PASSWORD: admin-test-pw
      NEXTCLOUD_TRUSTED_DOMAINS: "localhost 127.0.0.1"
    healthcheck:
      test: ["CMD", "php", "-r", "exit(file_get_contents('http://localhost/status.php') ? 0 : 1);"]
      interval: 5s
      timeout: 5s
      retries: 40
```

Verifiziert: Auto-Konfiguration ueber `SQLITE_DATABASE` (die DB-Variablen defaulten auf SQLite), `NEXTCLOUD_ADMIN_USER`/`NEXTCLOUD_ADMIN_PASSWORD` (nur wirksam, wenn beide gesetzt sind), `NEXTCLOUD_TRUSTED_DOMAINS` als space-separierte Liste, `occ` immer als `www-data`. Tag `34-apache` existiert und ist vom 2026-08-12. [CITED: docker-library/docs nextcloud/content.md; VERIFIED: Docker Hub Tag-Liste]

### scripts/bootstrap_test_nc.sh (idempotent)

```bash
#!/usr/bin/env bash
set -euo pipefail
OCC="docker compose -f compose.test.yml exec -T --user www-data nextcloud php occ"

# 1) Optionale Apps installieren (Notes 6.0.1 und Deck 1.18.3 sind NC-34-kompatibel)
$OCC app:install notes || $OCC app:enable notes
$OCC app:install deck  || $OCC app:enable deck

# 2) Testnutzer: alice (voll), bob (eingeschraenkt, fuer Permission-Tests)
OC_PASS='alice-pw' $OCC user:add --password-from-env alice || true
OC_PASS='bob-pw'   $OCC user:add --password-from-env bob   || true

# 3) PFLICHT: Kalender + Adressbuch existieren erst nach dem ersten Login,
#    occ user:add feuert UserFirstTimeLoggedInEvent nicht.
$OCC dav:create-calendar    alice personal || true
$OCC dav:create-addressbook alice contacts || true
$OCC dav:create-calendar    bob   personal || true

# 4) Brute-Force-Schutz aus, damit Negativ-Tests die eigene CI nicht drosseln
$OCC config:system:set auth.bruteforce.protection.enabled --value=false --type=boolean

# 5) App-Passwoerter erzeugen; das Kommando gibt "app password:" und dann den Token aus
ALICE_PW="$(OC_PASS='alice-pw' $OCC user:auth-tokens:add alice --password-from-env --name mcp-test | tail -n1 | tr -d '\r')"
BOB_PW="$(OC_PASS='bob-pw'     $OCC user:auth-tokens:add bob   --password-from-env --name mcp-test | tail -n1 | tr -d '\r')"

cat > .env.test <<EOF
NC_MCP_URL=http://127.0.0.1:8080
NC_MCP_USER=alice
NC_MCP_APP_PASSWORD=${ALICE_PW}
NC_MCP_TEST_USER2=bob
NC_MCP_TEST_APP_PASSWORD2=${BOB_PW}
EOF

# 6) Verifikation
$OCC dav:list-calendars alice
$OCC app:list | grep -E "notes|deck"
```

Verifizierte Grundlagen: `user:auth-tokens:add` (Alias `user:add-app-password`) liest das Login-Passwort aus `NC_PASS`/`OC_PASS` bei `--password-from-env` und gibt `app password:` plus Token in der Folgezeile aus. [VERIFIED: core/Command/User/AuthTokens/Add.php] `dav:create-calendar <user> <name>` benutzt `name` direkt als Kalender-URI. [VERIFIED: apps/dav/lib/Command/CreateCalendar.php] Notes 6.0.1 (`>=33.0.0 <36.0.0`) und Deck 1.18.3 (`>=34.0.0 <35.0.0`) sind fuer NC 34 freigegeben. [VERIFIED: apps.nextcloud.com/api/v1/platform/34.0.0/apps.json]

Hinweis fuer den Plan: ohne `--password-from-env` erzeugt das Kommando ein App-Passwort **ohne** Login-Passwort und meldet "will therefore have limited capabilities". Fuer DAV/OCS/REST reicht das, aber weil es kostenlos ist, das Login-Passwort mitzugeben, tun wir es.

### GitHub Actions

```yaml
# .github/workflows/ci.yml (Skizze)
name: CI
on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest tests/unit tests/contract -q
      - run: uv run python scripts/check_tool_budget.py

  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v5
      - run: docker compose -f compose.test.yml up -d --wait
      - run: bash scripts/bootstrap_test_nc.sh
      - run: uv sync --frozen
      - run: set -a && . ./.env.test && set +a && uv run pytest tests/integration -q
      - name: HTTP server + client matrix (SRV-01)
        run: |
          set -a && . ./.env.test && set +a
          uv run uvicorn mcp_connector.entry_http:app --port 8765 &
          for i in $(seq 1 40); do curl -sf http://127.0.0.1:8765/health && break; sleep 0.5; done
          uv run python tests/compat/modern_client_check.py http://127.0.0.1:8765/mcp
          uv run --isolated --with "mcp>=1.29,<2" python tests/compat/legacy_client_check.py http://127.0.0.1:8765/mcp
      - if: failure()
        run: docker compose -f compose.test.yml logs --tail=200 nextcloud
```

Anmerkungen: `docker compose up -d --wait` respektiert den Healthcheck, deshalb braucht es kein `sleep`. Der `/health`-Endpoint kommt aus `@mcp.custom_route("/health", methods=["GET"])` und ist bewusst unauthentifiziert (das ist bei custom routes ohnehin so). `--isolated` sorgt dafuer, dass der Legacy-Check ein eigenes Environment mit mcp 1.x bekommt, ohne das Projekt-Lockfile zu beruehren. Windows-Entwicklungshost: Docker Desktop mit WSL2-Backend, identische Kommandos aus Git Bash.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact fuer Phase 1 |
|--------------|------------------|--------------|---------------------|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server import MCPServer` | mcp 2.0.0, 2026-07-28 | Jedes Codebeispiel und jeder Blogpost von vor August 2026 nennt `FastMCP`. Nicht kopieren. |
| Transport-Flags im Konstruktor | Transport-Flags in `run()` bzw. `streamable_http_app()` | mcp 2.0.0 | `MCPServer(port=...)` wirft `TypeError` |
| `mcp` nutzt `httpx` + `httpx-sse` | `mcp` nutzt `httpx2` | mcp 2.0.0b2 | Client-Transports brauchen `httpx2.AsyncClient`; unser eigener Code bleibt auf httpx |
| Transport + `ClientSession` + `initialize()` | ein `Client(target)` | mcp 2.0.0 | In-Memory-Tests sind drei Zeilen |
| `stateless_http` als Aera-Schalter verstanden | `stateless_http` ist ein Legacy-only-Knopf | mcp 2.0.0 | Loest SRV-05 ohne Zutun; entzieht #227 die Grundlage |
| Types aus `mcp.types` | eigenes Paket `mcp-types` (`mcp.types` bleibt permanenter Alias) | mcp 2.0.0 | Beide Importwege gehen; `mcp.types` ist kuerzer und stabil |
| `ctx.elicit()` fuer Rueckfragen | `Resolve(...)`-Dependency-Injection (aera-portabel) | mcp 2.0.0 | Fuer uns irrelevant (keine Rueckfragen), aber wichtig: nicht "vorsorglich" einbauen, sonst wird jedes Tool multi-round-trip und braucht `RequestStateSecurity` |
| MCP-Spec 2025-11-25 (Handshake, Sessions) | MCP-Spec 2026-07-28 (stateless, `server/discover`) | 2026-07-28 | Beide werden gleichzeitig bedient |

**Deprecated / veraltet:**
- SSE-Transport: seit Spec 2025-03-26 ueberholt, `mcp.sse_app()` existiert nur fuer Altclients. Nichts darauf bauen (deckt sich mit OPS-01 als v2-Option).
- mcp 1.x: Maintenance-Mode, nur Security-Fixes, lebt auf dem `v1.x`-Branch. Der dokumentierte Fallback-Pin `mcp>=1.28,<2` bleibt als Notausgang gueltig, ist aber kein Ziel.
- `auth_server_provider=`: von der offiziellen Doku fuer neue Server ausdruecklich abgeraten. Relevant erst in Phase 3.
- Tasks-Extension (SEP-2663): in 2.0.0 **nicht** enthalten, laut Release-Notes bewusst. Falls jemand danach fragt.

## Project Constraints (from CLAUDE.md)

| Constraint | Konsequenz fuer Phase 1 |
|------------|-------------------------|
| Timeline: v1 + Store-Einreichung vor der Nextcloud Conference September 2026, harte Deadline | Phase 1 hat keinen Puffer fuer Eigenbau. Jede "Don't Hand-Roll"-Zeile ist Terminschutz. |
| Tech stack: Python 3.13 + offizielles MCP-SDK, uv als Toolchain, Docker/WSL2 fuer Test-Nextcloud | Bestaetigt. Die CLAUDE.md nennt noch `mcp[cli] ~1.27`; das ist durch die Projekt-Research (STACK.md) und D-19 auf `>=2.0,<3` revidiert. **Der Plan sollte diesen Satz in CLAUDE.md mitkorrigieren**, sonst widersprechen sich die Dokumente. |
| Lizenz AGPL-3.0 | LICENSE existiert. Kein Code-Copy aus dem privaten infranode-api (nur Pattern-Nachbau). Fremde Snippets nur aus AGPL-/permissiv-kompatiblen Quellen; die hier zitierten SDK-Doku-Beispiele sind MIT. |
| Repo public auf GitHub street1983nk, NICHT Akara-GitLab | `street1983nk/nextcloud-mcp-connector` existiert noch **nicht** (HTTP 404). Anlegen ist eine Phase-1-Aufgabe und Voraussetzung fuer den CSR-PR und fuer den #227-Fork. |
| Solo-Betrieb, Wartungsaufwand pro Feature zaehlt | 15 Tools sind eine Obergrenze, kein Ziel. Kein Tool "weil es billig ist". |
| Code/README Englisch, Projektkommunikation Deutsch, keine Em-Dashes, echte Umlaute | Alle Tool-Namen, Descriptions, Fehlermeldungen, Docstrings und README auf Englisch. Planungsdokumente Deutsch. |
| Security: MCP darf nie mehr sehen als der angemeldete Nutzer; keine destruktiven Writes in v1 | Kein Admin-Credential im Code, auch nicht in Tests (Testtools laufen als alice/bob, nicht als admin). Kein DELETE/MOVE/PROPPATCH/Share-Aufruf, per Grep-Test abgesichert. |
| Nach jedem Edit committen und pushen (globale Regel) | Der Plan sollte Commit-Punkte pro Task vorsehen; Push braucht das noch anzulegende GitHub-Remote. |
| Commits ohne Claude-Attribution (`includeCoAuthoredBy=false`) | Gilt auch fuer den #227-PR. Dort zusaetzlich `Signed-off-by` (DCO), siehe unten. |
| Code-Bereinigung: Python ruff + vulture, `ruff check .` und `ruff format --check .` ueber das GANZE Repo | Beides ins CI, nicht nur lokal. `vulture` vor dem Phasenabschluss einmal laufen lassen. |
| Tests: alle Pfade (Happy, Fehler, Edge, Negativ, no_data) | Pro Tool mindestens: Erfolg, Nextcloud-4xx, Nextcloud-5xx, leeres Ergebnis, ungueltiger Parameter. Bei `files_upload` zusaetzlich der 412-Konfliktpfad. |
| Doku-Seite mitziehen nach API-/Verhaltensaenderung | In Phase 1 ist README die Doku; Tool-Tabelle mit Permission-Level (TOOL-09) und der App-ID-Freeze-Vermerk (D-01) gehoeren hinein. |

## Contribution-Fix #227 (CONTRIB-01)

Alles hier ist am 2026-08-14 direkt am Repository verifiziert.

**Status des Issues:** #227, offen, erstellt 2026-08-08, betitelt "MCP Server incompatible with MCP SDK >=1.28 clients: `stateless_http=True` causes immediate session termination". Maintainer `oleksandr-nc` hat am 2026-08-14 geantwortet: "Thank you for reporting this, we will take a look at this". Ein PR ist also willkommen und niemand arbeitet sichtbar daran. [VERIFIED: GitHub API]

**Fundstelle:** `ex_app/lib/main.py`, aktuell Zeile 40 in `main`:

```python
http_mcp_app = mcp.http_app("/", transport="http", stateless_http=True)
```

Kontext: die App nutzt **fastmcp 2.14.7** (`from fastmcp import FastMCP`), nicht das offizielle SDK-Server-API. Das ist wichtig fuer die PR-Formulierung: die Loesung ist nicht "auf mcp 2.x migrieren", sondern der von Nutzern verifizierte Ein-Zeilen-Wechsel im fastmcp-Aufruf. [VERIFIED: raw.githubusercontent.com nextcloud/context_agent main/ex_app/lib/main.py]

**Empfohlener minimaler Fix** (entspricht D-22, mit einem Zugestaendnis an Rueckwaertskompatibilitaet):

```python
# Session-capable by default; SDK >= 1.28 clients keep the session after initialize
# and fail with "Session terminated" when the transport is stateless. See #227.
_stateless = os.getenv("MCP_STATELESS_HTTP", "0").lower() in ("1", "true", "yes")
http_mcp_app = mcp.http_app("/", transport="http", stateless_http=_stateless)
```

Warum konfigurierbar statt hart `False`: es aendert das Default-Verhalten (behebt den Bug), nimmt aber niemandem etwas weg, der stateless bewusst braucht. Das ist die Variante mit der hoechsten Merge-Wahrscheinlichkeit bei minimalem Diff. Der PR-Text sollte den Kernsatz der SDK-Doku zitieren (Legacy-Session braucht Sticky Routing, `stateless_http` kostet beide Rueckkanaele) und auf die Umgebung aus dem Issue verweisen.

**Prozess-Fakten:**
- **Kein** `CONTRIBUTING.md` und **kein** CLA im Repo. Lizenz AGPL-3.0.
- **DCO ist gelebte Praxis:** alle direkten Commits der letzten Zeit tragen `Signed-off-by`. Also mit `git commit -s` arbeiten. [VERIFIED: GitHub Commits API]
- `.github/workflows/reuse.yml` prueft REUSE/SPDX-Compliance. Jede **neue** Datei braucht SPDX-Header (`SPDX-FileCopyrightText`, `SPDX-License-Identifier: AGPL-3.0-or-later`). Wenn der PR nur eine bestehende Datei aendert, ist nichts zu tun.
- `.github/workflows/integration_test.yml` faehrt eine schwere Matrix (server-versions master/stable33/stable32/stable31, llm2-App mit Modell-Cache). Erwarte lange CI-Laufzeiten und moeglicherweise flakige Jobs, die nichts mit dem Fix zu tun haben.
- Offene PRs zur Orientierung: #229 (chore), #226 (feat), #218 (feat), #215 (chore ci), #177 (dependabot: fastmcp 2.14.7 -> 3.2.0, offen seit 2026-06-04). Der Fix muss gegen fastmcp **2.14.7** funktionieren, also `stateless_http` als Keyword von `http_app` benutzen wie im Bestand.
- Ein Repro-Test im dortigen CI ist realistisch **nicht** machbar (er braeuchte einen zweiten Client mit mcp 1.28 gegen den laufenden ExApp-Container). Empfehlung: die Reproduktion als praezise Anleitung in den PR-Body schreiben (Kommandos plus erwartete Fehlermeldung) und den automatisierten Regressionstest bei **uns** halten (`tests/compat/legacy_client_check.py`). Das ist ehrlicher als ein Test, der im fremden CI nur Rauschen erzeugt.

**Reihenfolge:** GitHub-Repo anlegen -> Fork -> Branch `fix/stateless-http-session-compat` -> Ein-Zeilen-Aenderung plus Kommentar -> `git commit -s` -> PR mit Verweis auf #227 und Repro-Anleitung. Kein weiterer Scope.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Toolchain, venv, lock, isolierte Legacy-Client-Runs | ja | 0.11.7 (2026-04-15) | keiner (System-Python defekt) |
| Python 3.13 | Runtime | ja (3.13.1 im PATH) | 3.13.1 | uv verwaltet notfalls eine eigene Version |
| git | Repo | ja | 2.54.0.windows.1 | - |
| gh CLI | Repo anlegen, Fork und PR fuer #227 | ja, authentifiziert | 2.92.0 | Web-UI |
| Docker CLI | Test-Nextcloud | ja | 29.5.2 | - |
| **Docker Engine (Linux)** | Integrationstests lokal | **NEIN, laeuft nicht** | - | Unit- und Contract-Tests laufen ohne Docker; Integrationstests via Marker und Env-Guard ueberspringen und in CI (ubuntu-latest) ausfuehren |
| Node.js / npx | `mcp dev` (Inspector, optional) | ja | v22.21.0 | Inspector ist Komfort, kein Pflichtpfad |
| slopcheck | Package-Audit | ja (nach `uv tool install --force --reinstall slopcheck`) | 0.6.1 | - |
| Netzwerk zu PyPI, GitHub, apps.nextcloud.com, Docker Hub | Dependencies, App-Installation, Image-Pull | ja | - | - |

**Missing dependencies with no fallback:** keine.

**Missing dependencies with fallback:**
- Die Docker-Linux-Engine antwortet nicht (`npipe:////./pipe/dockerDesktopLinuxEngine` nicht vorhanden), Docker Desktop ist installiert, aber nicht gestartet. Konsequenz fuer den Plan: **jeder Task, der `docker compose` braucht, gehoert hinter einen `checkpoint:human-verify` "Docker Desktop gestartet?"**, und die Testsuite muss ohne Docker gruen durchlaufen. Praktisch heisst das: `tests/integration` mit `@pytest.mark.integration` markieren, in `conftest.py` per `pytest.skip` ueberspringen, wenn `NC_MCP_URL` fehlt oder die Instanz nicht antwortet, und in `pyproject.toml` `addopts = "-m 'not integration'"` als Default setzen, mit `-m integration` als expliziter Opt-in.

Zusaetzliche Umgebungsnotiz: Entwicklungshost ist Windows 11 mit Git Bash. Zeilenenden in Shell-Skripten muessen LF sein (`.gitattributes` mit `*.sh text eol=lf`), sonst scheitert `docker compose exec` mit `\r`-Artefakten. Das `tr -d '\r'` im Bootstrap-Skript ist genau dagegen.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Encoding / Injection | ja | DAV-XML nur ueber lxml bauen (Escaping automatisch); Pfade mit `urllib.parse.quote(path, safe="/")`; ICS/VCF ueber icalendar/vobject |
| V2 Authentication | ja | Keine eigene Authentifizierung. Credentials werden an Nextcloud durchgereicht, Nextcloud entscheidet. Kein Auth-Retry (Brute-Force-Schutz). Static-Bearer-Vergleich mit `secrets.compare_digest` |
| V3 Session Management | ja (indirekt) | Kein eigener Session-State; das SDK besitzt Sessions. Pagination ueber zustandslose Handles ohne Autoritaet |
| V4 Access Control | ja | Nutzeridentitaet ausschliesslich aus dem Auth-Kanal, nie aus Tool-Parametern. ACL-Durchsetzung serverseitig bei Nextcloud. Permission-Parity-Test mit dem eingeschraenkten Nutzer bob |
| V5 Validation / Sanitization | ja | Pydantic-Schemas als erste Verteidigungslinie (Constraints via `Field`); Pfad-Traversal-Guard (`..`, absolute Windows-Pfade, doppelte Slashes) vor jedem DAV-Pfadbau |
| V6 Cryptography | nein (Phase 1) | Kein eigener Krypto-Code. TLS macht httpx. Token-Signierung erst mit OAuth in Phase 3 |
| V7 Error Handling / Logging | ja | message+hint-Fehler ohne interne Details; niemals Credentials, URLs mit Credentials oder vollstaendige Tracebacks in Logs; `Credentials.__repr__` maskiert; httpx-Logger auf WARNING |
| V8 Data Protection | ja | Kein Persistieren von Credentials in Phase 1 (kein Token-Store, D-12). Datei-Inhalte werden nicht zwischengespeichert |
| V9 Communication | ja | HTTPS gegen produktive Nextcloud-Instanzen; `follow_redirects=False`, damit der Authorization-Header niemals an ein anderes Ziel geht; im HTTP-Modus `transport_security` explizit setzen |
| V10 Malicious Code / Supply Chain | ja | `uv.lock` committen, `uv sync --frozen` in CI, slopcheck-Audit dokumentiert, `httpx2` nicht direkt pinnen, kein `npx --yes` |
| V12 Files and Resources | ja | Kein DELETE/MOVE/COPY/PROPPATCH; PUT nur mit `If-None-Match: *`; Groessen-Cap beim Lesen; Binaerdateien abgelehnt |
| V13 API / Web Service | ja | OCS-Pflichtheader; Antwort-Envelopes getrennt geparst; harte Timeouts pro Aufruf |
| V14 Configuration | ja | Alle Secrets aus Env, nie aus Dateien im Repo; `.env.test` in `.gitignore`; keine Default-Credentials im Code |

### Known Threat Patterns for Python MCP Server + Nextcloud User APIs

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Confused Deputy: Tool-Parameter `user_id` erlaubt Fremdzugriff | Elevation of Privilege | Identitaet nur aus dem Auth-Kanal; kein Tool-Schema enthaelt einen Nutzer; Contract-Test prueft das ueber alle 15 Input-Schemas |
| Prompt Injection in gelesenen Inhalten laesst das Modell schreiben | Tampering | Nur zwei Schreibarten existieren (neu anlegen), beide nicht destruktiv; `destructive_hint=False` ist ehrlich, weil der Code nichts anderes kann |
| Pfad-Traversal ueber `../` in Tool-Parametern | Elevation of Privilege | Pfad-Normalisierung und Ablehnung von `..`; Nextcloud-seitig ist der DAV-Root ohnehin der User-Ordner, aber wir verlassen uns nicht darauf |
| XML-Injection ueber Suchbegriffe | Tampering | lxml baut und escapt; niemals f-Strings fuer XML |
| XXE / Billion Laughs beim Parsen von DAV-Antworten | Denial of Service | `etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)` fuer **alle** Parser; Antwortgroesse begrenzen |
| Credential-Leak ueber Logs oder Tracebacks | Information Disclosure | maskiertes `__repr__`, `raise ... from None` im Wrapper, httpx-Logger stumm, keine `print()` |
| Credential-Leak ueber Redirect | Information Disclosure | `follow_redirects=False`, Redirect als Konfigurationsfehler melden |
| DNS-Rebinding auf den lokalen MCP-Port | Spoofing | `transport_security` mit expliziter Host-Allowlist; Default schuetzt Localhost bereits |
| Brute-Force-Amplifikation gegen die Nextcloud-Instanz | Denial of Service | Kein Auth-Retry; 401/429 als Endzustand mit Hinweis |
| Unbegrenzte Antwortgroesse sprengt den Client-Kontext | Denial of Service | Groessen-Caps, `<d:limit>`/`nresults`/`limit`-Parameter ueberall, Truncation-Marker plus Handle |
| Supply-Chain: junge transitive Dependency (`httpx2`) | Tampering | Lockfile committen, `--frozen` in CI, dokumentierter Audit, Owner-Review des ersten Locks |
| SSRF ueber nutzergelieferte URLs | Spoofing | In Phase 1 existiert kein URL-holendes Tool. Diese Grenze im Plan explizit als Nicht-Ziel festhalten |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `If-None-Match: *` fuehrt in der realen Nextcloud 34 beim PUT zu 412, nicht nur laut sabre/dav-Quellcode | files_upload, Code Examples | Das Sicherheitsversprechen "kann nichts ueberschreiben" waere unbelegt. Mitigation: Integrationstest in Wave 1, Fallback PROPFIND-Existenzcheck mit dokumentiertem TOCTOU |
| A2 | Der Byte-Grenzwert 24.000 fuer `tools/list` entspricht grob 6k Tokens | Token-Budget-CI | Gate zu locker oder zu streng. Mitigation: Erstmessung nach Tool 15, dann Wert auf gemessen plus 15 Prozent fixieren |
| A3 | `Range`-Requests funktionieren auf Nextcloud-WebDAV-Dateien fuer das Teil-Lesen | files_read | Offset-Pagination faellt weg, dann nur Groessen-Cap plus Ablehnung. Klein, in Wave 1 verifizierbar |
| A4 | Die interne Route `GET /apps/deck/cards/{cardId}` ist mit App-Passwort ohne CSRF-Token erreichbar | fetch, Deck-ID-Aufloesung | Nur ein Fast Path; der Sweep ueber `/boards` + `/stacks` ist der verifizierte Weg und bleibt Default |
| A5 | Notes 6.x liefert weiterhin API v1 unter `/apps/notes/api/v1` (die Doku beschreibt v1.0 bis 1.4 bis Notes 4.9) | notes_* | Bei Bruch antwortet Capabilities mit einer anderen `api_version`; das Tool sollte die Liste pruefen und sonst klar meldem. Verifizierbar in Wave 1 |
| A6 | Der Unified-Search-Files-Provider setzt `attributes.fileId` und `attributes.path` in NC 34 genau so wie im master-Quellcode | search/fetch ID-Schema | ID-Ableitung faellt auf URL-Parsing zurueck (`/f/<fileid>`). Beide Wege im Parser vorsehen |
| A7 | `occ app:install notes` und `occ app:install deck` funktionieren im offiziellen Image ohne weitere Vorbereitung (Appstore-Zugriff, Schreibrechte auf custom_apps) | Bootstrap | Fallback: Apps als Volume vorab entpacken oder `app:enable` nach manuellem Download. In Wave 0 pruefen |
| A8 | Ein einzelner Worker genuegt fuer Phase 1, Sticky Sessions sind Betriebssache | Statelessness | Falls doch Multi-Worker gefordert wird, ist es ein Ein-Zeilen-Schalter plus Test, kein Umbau |

## Open Questions (RESOLVED)

1. **Deck-Karte per ID aufloesen: Sweep oder interne Route?**
   - Was wir wissen: Die oeffentliche API adressiert Karten nur als `boards/{b}/stacks/{s}/cards/{c}`. Der Unified-Search-Provider `search-deck-card-board` liefert nur `cardId`. Eine interne Route `GET /apps/deck/cards/{cardId}` existiert (`card#read`).
   - Was unklar ist: ob die interne Route mit App-Passwort ohne CSRF-Token nutzbar ist und ob sie stabil bleibt.
   - Empfehlung: kanonische ID-Form lang (`card:<boardId>:<stackId>:<cardId>`), Kurzform akzeptieren, Aufloesung per Sweep (`/boards` + `/boards/{id}/stacks`) mit Per-Request-Cache. Die interne Route als optionaler, hinter einem Feature-Flag versteckter Spike, wenn der Sweep zu langsam ist.

2. **Wie streng darf `files_read` sein?**
   - Was wir wissen: Unbegrenzte Reads sprengen den Client-Kontext (dokumentierte Performance-Trap).
   - Was unklar ist: Der richtige Default. 512 KiB sind grosszuegig fuer Markdown, knapp fuer eine CSV.
   - Empfehlung: 512 KiB Default, per Parameter bis 2 MiB, Truncation immer explizit im JSON markieren plus `next_offset`. Nach ersten realen Nutzungen anpassen; die Zahl ist eine Konfigurationskonstante, keine Architektur.

3. **Antwortsprache der Fehlermeldungen**
   - Was wir wissen: CLAUDE.md sagt Code und README Englisch.
   - Was unklar ist: Ob deutsche Behoerden-Nutzer deutsche Tool-Fehlertexte erwarten.
   - Empfehlung: Phase 1 komplett Englisch (das Modell uebersetzt fuer den Nutzer ohnehin). Lokalisierung waere ein Token-Kosten- und Wartungsthema und gehoert, wenn ueberhaupt, nach Phase 5.

4. **Wird der 24.000-Byte-Budget-Wert vor oder nach Tool 15 fixiert?**
   - Empfehlung: Das Gate von Anfang an im CI aktiv haben (damit es nicht vergessen wird), aber mit dem grosszuegigen Startwert. Ein eigener Task am Ende von Phase 1 misst und fixiert. Sonst ist das Gate entweder von Tag 1 rot oder am Ende bedeutungslos.

## Sources

### Primary (HIGH confidence)

**MCP Python SDK (offiziell)**
- https://py.sdk.modelcontextprotocol.io/llms-full.txt (vollstaendige v2-Doku, abgerufen 2026-08-14): Abschnitte `servers/tools`, `servers/structured-output`, `servers/handling-errors`, `handlers/context`, `run/`, `run/asgi`, `run/deploy`, `run/authorization`, `run/legacy-clients`, `get-started/testing`, `client/`, `client/transports`, `advanced/middleware`
- https://github.com/modelcontextprotocol/python-sdk/releases (v2.0.0, v2.0.0rc1, v2.0.0b2, v2.0.0b1, v1.29.0): GA-Datum, v1-Maintenance-Mode, `FastMCP` -> `MCPServer`, httpx2-Wechsel, fehlende Tasks-Extension
- Quellcode @ Tag v2.0.0: `src/mcp/server/mcpserver/server.py` (Konstruktor, `tool()`-Signatur), `src/mcp/server/mcpserver/context.py` (`headers`), `src/mcp/server/auth/middleware/bearer_auth.py` (nur Bearer), `src/mcp-types/mcp_types/_types.py` (`ToolAnnotations`)
- https://pypi.org/pypi/mcp/json und /mcp/2.0.0/json: Version 2.0.0, Upload 2026-07-28T13:45:28, requires_python >=3.10, requires_dist

**Nextcloud Server (Quellcode, Branch master)**
- `core/Controller/UnifiedSearchController.php`: OCS-Routen `/search/providers` und `/search/providers/{id}/search`, Limit-Deckelung, 400 bei fehlenden Filtern
- `core/ResponseDefinitions.php`: `CoreUnifiedSearchProvider`, `CoreUnifiedSearchResult`, `CoreUnifiedSearchResultEntry`
- `lib/public/Search/SearchResultEntry.php`: `attributes` serialisiert als Objekt
- `apps/files/lib/Search/FilesSearchProvider.php`: `attributes.fileId`/`path`, LIKE auf `name`, Filterliste
- `apps/dav/lib/Files/FileSearchBackend.php`: Arbiter-Pfad `''`, Scope-Validierung, Property-Definitionen, Default-Limit 100, OPERATOR_LIMIT 100
- `apps/dav/lib/RootCollection.php`, `CalDAV/CalendarRoot.php`, `CardDAV/AddressBookRoot.php`: URL-Segmente `calendars/<uid>` versus `addressbooks/users/<uid>`
- `apps/dav/lib/Listener/UserEventsListener.php` (firstLogin), `CalDAV/CalDavBackend.php` (PERSONAL_CALENDAR_URI), `CardDAV/CardDavBackend.php` (PERSONAL_ADDRESSBOOK_URI): Default-Kalender und -Adressbuch erst beim ersten Login
- `apps/dav/lib/Command/CreateCalendar.php`, `CreateAddressBook.php`: `name` wird als URI verwendet
- `core/Command/User/AuthTokens/Add.php`: `user:auth-tokens:add`, Alias `user:add-app-password`, `--password-from-env` liest NC_PASS/OC_PASS, Ausgabeformat

**sabre/dav (Nextclouds DAV-Engine, Branch master)**
- `lib/DAV/Server.php`: `checkPreconditions()` fuer jede Methode, `If-None-Match: *` -> PreconditionFailed
- `lib/CalDAV/Xml/Filter/CalendarData.php`: `<c:expand>` mit Pflichtattributen start/end
- `lib/CalDAV/Plugin.php`: Expansion nutzt `calendar-timezone`, Default UTC
- `lib/CalDAV/Xml/Request/CalendarQueryReport.php`: Pflicht-`filter`, nur ein Top-Level-comp-filter
- `lib/CardDAV/Xml/Request/AddressBookQueryReport.php`: `test` anyof/allof, `limit/nresults`, match-types

**Nextcloud-Doku und App-Doku**
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/search.html: SEARCH-Endpoint, basicsearch, Operatoren, Scope-Regel, Property-Tabelle
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/basic.html: URL-Format, PROPFIND-Properties, PUT/GET, X-OC-MTime, OC-Checksum
- https://github.com/nextcloud/notes/blob/main/docs/api/v1.md und docs/api/README.md: Endpoints, Note-Felder, Capabilities-Erkennung, chunkSize/chunkCursor
- https://github.com/nextcloud/notes/blob/main/appinfo/routes.php: kein Search-Endpoint
- https://github.com/nextcloud/notes/blob/main/lib/AppInfo/SearchProvider.php: Provider-ID `notes`, Suche in Titel und Inhalt, resourceUrl-Format
- https://github.com/nextcloud/deck/blob/main/docs/API.md: Basis-URL, Pflichtheader, Boards/Stacks/Cards, Fehlerformat, Titel-Limit
- https://github.com/nextcloud/deck/blob/main/lib/Capabilities.php: `deck`-Capabilities inkl. `canCreateBoards`
- https://github.com/nextcloud/deck/blob/main/lib/Search/DeckProvider.php und CardSearchResultEntry.php: Provider-ID `search-deck-card-board`, resourceUrl nur mit cardId
- https://github.com/nextcloud/deck/blob/main/appinfo/routes.php: interne Route `card#read` unter `/cards/{cardId}`
- https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json: Notes 6.0.1 (>=33 <36), Deck 1.18.3 (>=34 <35); 378 Apps, kein `mcp_connector`
- https://github.com/docker-library/docs/blob/master/nextcloud/content.md: Auto-Konfiguration, SQLITE_DATABASE, NEXTCLOUD_ADMIN_*, TRUSTED_DOMAINS, occ als www-data, Hook-Ordner
- Docker Hub Tag-Liste `library/nextcloud`: `34-apache` / `34.0.2-apache`, Stand 2026-08-12

**OpenAI (ChatGPT-Kompatibilitaet)**
- https://developers.openai.com/api/docs/mcp: Pflichttools `search`/`fetch`, exakte structuredContent- und content-Formen, Zitat-Bedingung "url must be a non-empty string"
- https://github.com/openai/openai-cookbook/blob/main/examples/deep_research_api/how_to_build_a_deep_research_mcp_server/main.py: verbatim `search(query: str)` -> `{"results": [...]}`, `fetch(id: str)` -> `{id,title,text,url,metadata}`

**context_agent (fuer CONTRIB-01)**
- GitHub API: Issue #227 (offen, 2026-08-08, Maintainer-Antwort 2026-08-14), offene PRs, Commit-Historie mit `Signed-off-by`
- `ex_app/lib/main.py` @ main: `mcp.http_app("/", transport="http", stateless_http=True)`, fastmcp-basiert
- `.github/workflows/reuse.yml`, `integration_test.yml`: REUSE-Gate, CI-Matrix

**Namens- und ID-Verfuegbarkeit**
- PyPI: `nextcloud-mcp-connector` 404 (frei), `nextcloud-mcp-server` 200 (belegt)
- GitHub API: `street1983nk/nextcloud-mcp-connector` 404 (noch nicht angelegt)
- nextcloud/app-certificate-requests: 838 Verzeichnisse, keines mit "mcp"; Code-Suche nach `mcp_connector` 0 Treffer

### Secondary (MEDIUM confidence)

- slopcheck 0.6.1 lokal gegen PyPI (12 Pakete): 11 OK, 1 SUS (`httpx2`), gegengeprueft ueber PyPI-Metadaten (Autor Tom Christie, github.com/pydantic/httpx2) und die SDK-Release-Notes
- Projekt-eigene Vorarbeit: `.planning/research/STACK.md`, `PITFALLS.md`, `ARCHITECTURE.md`, `FEATURES.md` (2026-08-14). Die SDK-Aussagen daraus sind hier gegen Primaerquellen nachverifiziert; die Nextcloud-API-Aussagen wurden praezisiert (Notes ohne Search, fehlende IDs in Unified Search, Kalender erst nach erstem Login).
- InfraNode-Messung "outputSchema = 56 Prozent des Token-Footprints bei 71 Tools" (eigene fruehere Messung, nicht in dieser Session reproduziert). Sie motiviert `structured_output=False`, die Wirkung wird durch das eigene Budget-Gate ohnehin gemessen.

### Tertiary (LOW confidence)

- Erreichbarkeit der internen Deck-Route `GET /apps/deck/cards/{cardId}` mit App-Passwort ohne CSRF-Token: aus Nextclouds allgemeinem CSRF-Verhalten bei Nicht-Session-Auth abgeleitet, nicht getestet (siehe A4 und Open Question 1)
- Nextcloud-`Range`-Unterstuetzung auf DAV-GET fuer Teil-Lesen: sabre unterstuetzt es generell, in NC 34 nicht verifiziert (A3)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Jede Version gegen PyPI geprueft, `requires_dist` von mcp 2.0.0 gelesen, der einzige SUS-Treffer nachrecherchiert und erklaert.
- SDK-Oberflaeche und Transport: HIGH. Nicht nur Doku, sondern Quellcode am Tag v2.0.0 (Konstruktor-Signatur, `tool()`-Parameter, `ToolAnnotations`-Felder, Bearer-Only-Backend, `ctx.headers`).
- Nextcloud-API-Details: HIGH fuer WebDAV, CalDAV, CardDAV, OCS Unified Search, Notes, Deck, occ-Kommandos (jeweils Quellcode oder offizielle App-Doku). MEDIUM nur fuer das Laufzeitverhalten von `If-None-Match: *` und `Range` in einer echten NC 34.
- ChatGPT-Profil: HIGH. Doku plus verbatim Referenzimplementierung von OpenAI.
- context_agent #227: HIGH. Issue, Zeile, Framework-Version, DCO-Praxis und CI-Gates direkt am Repo verifiziert.
- Test-Umgebung: MEDIUM-HIGH. Image-Tag, Env-Variablen und alle occ-Kommandos verifiziert; das Zusammenspiel als Ganzes ist erst gelaufen, wenn Docker Desktop laeuft (A7).
- Pitfalls: HIGH fuer die SDK- und Nextcloud-bezogenen (belegt), MEDIUM fuer die Betriebs-Pitfalls (Brute-Force, 421), die aus der Projekt-Research uebernommen und hier praezisiert wurden.

**Research date:** 2026-08-14
**Valid until:** 2026-09-14 fuer die Nextcloud-Seite (stabile APIs). **2026-08-28 fuer mcp 2.x**: die Version ist erst 17 Tage alt, ein 2.0.1 oder 2.1 kann Details verschieben. Vor dem Phasenabschluss `uv lock --upgrade-package mcp` pruefen und die Release-Notes lesen.
