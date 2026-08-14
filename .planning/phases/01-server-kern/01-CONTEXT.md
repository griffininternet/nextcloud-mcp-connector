# Phase 1: Server-Kern - Context

**Gathered:** 2026-08-14
**Status:** Ready for planning
**Mode note:** Erstellt im --auto-Modus; alle Entscheidungen sind die empfohlenen Optionen aus dem Grilling-Interview und der Projekt-Research, vom Owner pauschal freigegeben ("alles wie empfohlen").

<domain>
## Phase Boundary

Entwickler koennen den MCP-Server lokal (stdio) und remote (Streamable HTTP) mit App-Passwort gegen ihre Nextcloud nutzen, mit dem vollen kuratierten Tool-Set (15 Tools). App-ID wird eingefroren, der Fix-PR an nextcloud/context_agent#227 wird eingereicht. KEINE ExApp-Shell (Phase 2), KEIN OAuth (Phase 3), KEIN prepare_context (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### App-ID und Naming
- **D-01:** App-ID: `mcp_connector`, Anzeigename "MCP Connector", Python-Package `mcp_connector`, Repo `nextcloud-mcp-connector` (GitHub street1983nk, public). Kein "nextcloud" in der App-ID (Store-Regel). Umbenennung ist nur bis zum CSR-PR billig; Freeze-Dokumentation in README festhalten. [auto: empfohlene Option]
- **D-02:** PyPI-Name: `nextcloud-mcp-connector` (der nackte Name `nextcloud-mcp-server` ist von der Community besetzt). CLI-Entry-Point: `nc-mcp` (stdio). [auto]

### Tool-Zuschnitt (15 Tools, Namensschema app_verb)
- **D-03:** Dateien (4): `files_search`, `files_list`, `files_read`, `files_upload` (Upload nur neu, Konflikt = klare Ablehnung, kein Overwrite). [auto]
- **D-04:** Kalender (2): `calendar_list_events` (Zeitraum-Pflichtparameter, Timezone-explizit), `calendar_create_event`. [auto]
- **D-05:** Notes (3): `notes_search`, `notes_read`, `notes_create`. [auto]
- **D-06:** Deck (2): `deck_browse` (Boards/Stacks/Karten lesen, ein Tool mit Ebenen-Parameter statt drei), `deck_create_card`. [auto]
- **D-07:** Kontakte (1): `contacts_search` (lesend). [auto]
- **D-08:** Suche (1): `unified_search` (OCS Unified Search, provider-parallel, berechtigungstreu). [auto]
- **D-09:** ChatGPT-Profil (2): `search` und `fetch` mit exakt dem OpenAI-Kompatibilitaets-Schema (search: id/title/url; fetch: id/title/text/url/metadata). `search` delegiert an Unified Search, `fetch` loest IDs auf Datei/Notiz/Karte/Termin auf. ID-Format: praefixiert (`file:<fileid>`, `note:<id>`, `card:<boardId>:<cardId>`, `event:<calendar>:<uid>`), damit fetch eindeutig routen kann. [auto]
- prepare_context ist NICHT in Phase 1 (Phase 4), wird aber beim Tool-Registry-Design mitgedacht (Fan-out nutzt dieselben Client-Funktionen). (ehemals D-10, informational)

### Auth-Modell Phase 1
- **D-11:** stdio: NC-Base-URL + Username + App-Passwort aus Env (NC_MCP_URL, NC_MCP_USER, NC_MCP_APP_PASSWORD). [auto]
- **D-12:** Streamable HTTP: Credential-Passthrough pro Request via Authorization-Header (Basic user:app-passwort). Zusaetzlich optionaler statischer Bearer fuer Single-User-Deployments (Env). KEIN Token-Store in Phase 1 (kommt mit OAuth in Phase 3). Kein Credential-Logging, niemals. [auto]
- Login Flow v2 ist Phase 3 (AUTH-02), nicht Phase 1. (ehemals D-13, informational)

### Antwort- und Fehlerformat
- **D-14:** Kompakte JSON-Antworten mit stabilen Feldern; outputSchema nur wo Clients es nutzen (Schema-Diaet nach InfraNode-Playbook: keine Auto-Titles, kurze Descriptions nur im inputSchema). CI-Check fuer Token-Budget der tools/list-Antwort. [auto]
- **D-15:** Fehlerformat: message + hint (handlungsfaehig), 4xx-Fehler gehen ans Modell zur Selbstkorrektur, 5xx werden als degradierte Antwort gekapselt (Graceful-Degradation-Wrapper-Pattern aus InfraNode). Fehlende App (Notes/Deck nicht installiert): klarer Text "Notes app is not installed on this Nextcloud" + Hinweis. [auto]
- **D-16:** Annotationen pro Tool ehrlich: alle Lesetools readOnlyHint=true; Create-Tools readOnlyHint=false, destructiveHint=false, idempotentHint=false; openWorldHint=false (eigene Cloud). Permission-Level pro Tool in Doku-Tabelle (read / create-only). [auto]

### Nextcloud-Client-Schicht
- **D-17:** httpx roh fuer ALLE APIs (WebDAV/CalDAV/CardDAV XML via lxml, icalendar fuer VEVENT, vobject fuer VCARD; Notes/Deck/OCS als JSON-REST). KEINE caldav-Library (sync), KEIN aiodav (verwaist). Ein AsyncClient pro Event-Loop (WeakKeyDictionary-Pattern aus InfraNode). [auto]
- **D-18:** OCS immer mit OCS-APIRequest: true + Accept: application/json. CalDAV-Edge-Cases (Timezone, Datumsbereich, stille Feld-Verluste) bekommen dedizierte Tests (Lehren aus Platzhirsch-Bugs #538/#544/#782). [auto]

### SDK und Transport
- **D-19:** mcp>=2.0,<3 (GA seit 28.07.2026), Fallback-Pin >=1.29,<2 dokumentiert. Client-Matrix-Test: SDK 1.28+ UND 2.x gegen denselben Endpoint (Regressionstest der #227-Klasse). [auto]
- **D-20:** Kein In-Memory-Session-State in Tools; Pagination ueber server-generierte Handles als normale Tool-Argumente. Restart-Ueberlebens-Test als Success-Criterion-Beweis. [auto]

### Test-Umgebung
- **D-21:** Lokale Test-Nextcloud: offizielles nextcloud:apache-Image per docker-compose im Repo (compose.test.yml), Apps notes/deck via occ im Init-Script; zweiter eingeschraenkter Testnutzer fuer Permission-Tests. uv + pytest + respx (gemockte httpx-Ebene) fuer Unit-Tests, In-Memory-MCP-Client (mcp 2.x Feature) fuer Tool-Contract-Tests, Integrationstests gegen die Docker-NC. [auto]

### Contribution-Fix (#227)
- **D-22:** Minimaler PR an nextcloud/context_agent: stateless_http konfigurierbar machen bzw. auf False setzen (exakt wie im Issue diskutiert), mit Repro-Test. Kein Feature-Umbau, kein Scope darueber hinaus. Vor dem PR: CONTRIBUTING.md/CLA des Repos pruefen. Absender: GitHub street1983nk. [auto]

### Claude's Discretion
- Interne Modulstruktur (Anlehnung an InfraNode-Layout: server.py / tools.py / clients/ / schemas.py), Naming-Details, Logging-Aufbau, CI-Workflow-Details (GitHub Actions), Verzeichnis-Layout der Tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt-Planung
- `.planning/PROJECT.md` - Produktdefinition, Key Decisions (SDK-Revision auf mcp 2.x), Constraints
- `.planning/REQUIREMENTS.md` - 26 v1-Requirements, Phase-1-Zuordnung (16 Reqs)
- `.planning/ROADMAP.md` - Phase-1-Ziel und 5 Success Criteria

### Research (alle 2026-08-14, frisch)
- `.planning/research/STACK.md` - Stack-Empfehlungen mit Versionen (mcp 2.x GA, nc_py_api, httpx-roh-Entscheidung, Test-Setup)
- `.planning/research/FEATURES.md` - Tool-Landschaft, ChatGPT-search/fetch-Pflichtschema, Anti-Features, Wettbewerbsmatrix
- `.planning/research/ARCHITECTURE.md` - Drei-Schichten-Architektur, Build-Order, Topologien, markierte Spikes
- `.planning/research/PITFALLS.md` - 8 kritische Pitfalls mit Phasen-Mapping (CalDAV-TZ, Brute-Force, Store-Zertifizierung)
- `.planning/research/SUMMARY.md` - Synthese und Phasen-Vorschlag

### Wiederverwendbare Patterns (externes Repo, nur lesen)
- `C:\Users\Student\infranode-api\src\infranode\mcp\server.py` - Tool-Registrierung, Annotationen (_annotations), Schema-Diaet (_slim_schema), Graceful-Wrapper (_graceful), Instructions-Stamping
- `C:\Users\Student\infranode-api\src\infranode\mcp\tools.py` - freistehende testbare async Tool-Funktionen
- `C:\Users\Student\infranode-api\src\infranode\mcp\client.py` - Event-Loop-gebundener httpx-Pool, strukturierte Fehler (message+hint)
- ACHTUNG Lizenz: infranode-api ist privat; Patterns als Vorbild nachbauen, Code neu schreiben (dieses Repo ist AGPL-3.0 public)

### Externe Referenzen
- nextcloud/context_agent#227 (github.com) - stateless_http-Bug, Grundlage des Contribution-Fix
- cbcoutinho/nextcloud-mcp-server Issues #538/#544/#782 (github.com) - CalDAV/WebDAV-Edge-Case-Katalog fuer unsere Tests
- OpenAI MCP-Doku (developers.openai.com/api/docs/mcp) - Pflichtschema fuer search/fetch

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Greenfield-Repo, noch kein Code. Wiederverwendung erfolgt als Pattern-Nachbau aus InfraNode-MCP (siehe canonical_refs), nicht als Code-Copy (Lizenzgrenze privat->AGPL).

### Established Patterns
- InfraNode-MCP-Patterns sind produktionserprobt (live auf mcp.infranode.dev): Schema-Diaet -27% Tokens gemessen, Graceful Degradation, Tool-Annotationen, Registry-Listing-Playbook (.planning/MCP-LAUNCH-KIT.md im InfraNode-Repo).

### Integration Points
- Phase 2 haengt die ExApp-Shell VOR diesen Server (AppAPI-Middleware, Impersonation); die Client-Factory muss deshalb ab Tag 1 eine austauschbare Credential-Quelle haben (Env / Header-Passthrough / spaeter Token-Store), ein Parameter-Objekt statt globaler Config.

</code_context>

<specifics>
## Specific Ideas

- Kuration ist Feature: 15 Tools, aktiv vermarktet als "passt neben deine anderen MCP-Server" (Cursor-Limits 40/80).
- Sicherheitsversprechen woertlich: "Der Server kann konstruktionsbedingt nichts loeschen oder ueberschreiben." Muss nach Phase 1 wahr und testbar sein (Create-only-Write-Tests).
- Der Owner will Gamechanger-Qualitaet: lieber 15 exzellente, schnelle, token-schlanke Tools als Feature-Buffet.

</specifics>

<deferred>
## Deferred Ideas

- prepare_context-Buendel-Tool: Phase 4 (TOOL-08)
- Login Flow v2 Browser-Onboarding: Phase 3 (AUTH-02)
- Tasks/VTODO, MCP-Prompts, Response-Format-Parameter: v1.x nach Launch (REQUIREMENTS v2)
- Talk/Tables/Mail, openDesk-Suite: v2/Phase-3-Meilenstein nach Oktober
- Gehostete Multi-Tenant-Instanz mit AVV (Behoerden-Paket): OPS-02, nach v1

</deferred>

---

*Phase: 1-Server-Kern*
*Context gathered: 2026-08-14*
