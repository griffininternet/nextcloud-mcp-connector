# Walking Skeleton, MCP Connector fuer Nextcloud

**Phase:** 1 (Server-Kern)
**Generated:** 2026-08-14

## Capability Proven End-to-End

Ein Entwickler startet `nc-mcp` per stdio mit App-Passwort aus der Umgebung und liest mit dem Tool `files_read` den Inhalt einer Textdatei aus seiner eigenen Nextcloud (Docker, `nextcloud:34-apache`).

Diese eine Faehigkeit durchlaeuft die komplette Vertikale: MCP-Client, stdio-Transport, Server-Registry mit Annotationen und Schema-Diaet, graceful-Fehlerwrapper, Credential-Aufloesung, HTTP-Pool, WebDAV-Client, gehaerteter XML-Parser, echte Nextcloud. Alle weiteren 14 Tools haengen sich ohne Architekturaenderung daran.

## Phase Goal (User Story)

**As a** Entwickler oder Selfhoster, **I want to** meinen MCP-Client lokal per stdio und remote per Streamable HTTP mit App-Passwort an meine Nextcloud anbinden, **so that** mein Assistent Dateien, Termine, Notizen, Deck-Karten und Kontakte berechtigungstreu nutzen kann, ohne etwas loeschen oder ueberschreiben zu koennen.

Hinweis: Die `**Goal:**`-Zeile in ROADMAP.md ist inhaltlich identisch, aber nicht im Drei-Slot-Format notiert. Die obige Formulierung ist eine treue Umschreibung ohne neue Inhalte.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| MCP-SDK | `mcp[cli]>=2.0,<3` (2.0.0, GA 2026-07-28), Import `from mcp.server import MCPServer` | v1 ist Maintenance-Mode; v2 bedient beide Protokoll-Aeren aus einem Endpoint, loest SRV-01 und SRV-05 ohne Eigenbau. `FastMCP` existiert in v2 nicht mehr. |
| Transport | stdio via `mcp.run()`, HTTP via `mcp.streamable_http_app()` mit `TransportSecuritySettings` | Zwei Entry-Points auf demselben Server-Objekt. `stateless_http` bleibt ungesetzt: in v2 ist es ein Legacy-only-Knopf und genau die Falle aus context_agent#227. |
| Nextcloud-Zugriff | httpx roh fuer alle APIs, lxml fuer DAV-XML, icalendar fuer ICS, vobject fuer VCF | D-17. Keine caldav-Library (sync), kein aiodav (verwaist). Formatarbeit an gepflegte Bibliotheken auslagern, Transport selbst halten. |
| Auth in Phase 1 | Drei exklusive Modi: stdio aus Env, HTTP-Basic-Passthrough via `ctx.headers`, optionaler statischer Bearer | D-11, D-12. Der SDK-Auth-Layer akzeptiert nur Bearer, deshalb laeuft Basic bewusst daneben. Nextcloud authentifiziert, der Server behauptet nie eine Identitaet. Kein Token-Store vor Phase 3. |
| Credential-Naht | `Credentials`-Parameterobjekt plus `resolve_credentials(ctx)` in `deps.py` | Hier haengt Phase 2 die AppAPI-Impersonation ein, ohne Tool-Code anzufassen. Kein modulglobaler Client, weil im Passthrough die Credentials pro Request wechseln. |
| Verzeichnislayout | `src/mcp_connector/` mit `server/` (nur hier `mcp`-Imports, Auto-Registrierung der `reg_*`-Module), `tools/` (freistehende async Funktionen), `nextcloud/clients/` | Tool-Funktionen bleiben ohne MCP-Import mit respx testbar. Ein Registrierungsmodul pro Tool-Bundle erlaubt parallele Plaene ohne Dateikonflikte. |
| Antwortformat | Kompaktes JSON per `structured_output=False` bei 13 Tools, Pydantic-Modelle nur bei `search` und `fetch` | D-14 plus die verifizierte Schema-Diaet: das Output-Schema ist der groesste Token-Posten. ChatGPT braucht die Doppelung aus structuredContent und content, deshalb dort Modelle. |
| Fehlerformat | `ToolError(message, hint)` wird im graceful-Wrapper zu einer gewoehnlichen Exception, `MCPError` nur bei fehlender Konfiguration | D-15 und die SDK-Regel: koennte ein besseres Modell den Fehler vermeiden? Dann Exception, sonst MCPError. `from None` verhindert Credential-Leaks in Tracebacks. |
| Schreibmodell | Nur Create-only: WebDAV-PUT und CalDAV-PUT immer mit `If-None-Match: *`, POST bei Notes und Deck | Das Sicherheitsversprechen ist konstruktiv, nicht per Konvention. sabre/dav prueft die Precondition serverseitig, also rennfrei. |
| Test-Umgebung | `compose.test.yml` mit `nextcloud:34-apache` plus idempotentes `scripts/bootstrap_test_nc.sh`, pytest mit `respx`, In-Memory-`Client(mcp)`, Marker `integration` und `matrix` | D-21. Default-Suite laeuft ohne Docker (`addopts = -m 'not integration'`), weil die Docker-Linux-Engine auf dem Entwicklungshost nicht laeuft. |
| Deployment-Ziel Phase 1 | Lokaler Prozess: `nc-mcp` (stdio) beziehungsweise `uv run uvicorn mcp_connector.entry_http:app` | ExApp-Container, AppAPI und Store-Paket sind Phase 2 und 5. In Phase 1 ist der dokumentierte lokale Vollstack-Lauf der Deployment-Nachweis. |
| App-Identitaet | App-ID `mcp_connector`, PyPI `nextcloud-mcp-connector`, CLI `nc-mcp`, Repo `street1983nk/nextcloud-mcp-connector` | D-01, D-02, EXAPP-03. Verfuegbarkeit gegen Store-API, app-certificate-requests und PyPI belegt. Umbenennung ist nur bis zum CSR-PR billig. |

## Stack Touched in Phase 1

- [ ] Projekt-Scaffold (uv, pyproject mit Pins, ruff, pytest mit Markern, CI-Workflow) -> Plan 01
- [ ] Routing beziehungsweise Transport: stdio-Entry und HTTP-Endpoint `/mcp` plus `/health` -> Plan 02 und Plan 04
- [ ] Echter Lesezugriff auf die Datenquelle (WebDAV GET plus PROPFIND gegen Nextcloud) -> Plan 02
- [ ] Echter Schreibzugriff (WebDAV PUT mit Create-only-Schutz, belegt durch 412) -> Plan 03
- [ ] Interaktion aus einem echten Client (MCP-Client ruft Tools ueber stdio und HTTP auf) -> Plan 02, Plan 04, Abnahme in Plan 14
- [ ] Vollstack-Lauf dokumentiert: `docker compose -f compose.test.yml up -d --wait`, `bash scripts/bootstrap_test_nc.sh`, `uv run pytest -q`, `-m integration`, `-m matrix` -> Plan 03 und Plan 14

## Out of Scope (Deferred to Later Slices)

Explizit nicht Teil des Skeletons und nicht Teil von Phase 1:

- ExApp-Shell, AppAPI-Lifecycle, HaRP, `nc_py_api`, FastAPI (Phase 2, EXAPP-01)
- Impersonation ueber AppAPI und der Discovery-Spike durch den AppAPI-Proxy (Phase 2, AUTH-05, AUTH-06)
- OAuth 2.1, Protected Resource Metadata, Dynamic Client Registration, PKCE, Token-Widerruf, Login Flow v2 (Phase 3, AUTH-02 bis AUTH-04)
- Token-Store und jede Form von Credential-Persistenz (Phase 3)
- Per-User-Settings-UI in Nextcloud und Declarative Settings (Phase 4, EXAPP-02)
- `prepare_context` als Buendel-Tool (Phase 4, TOOL-08); die Client-Funktionen sind aber so geschnitten, dass der Fan-out sie wiederverwenden kann
- Store-Einreichung, CSR-PR, Signatur, Multi-Arch-Image (Phase 5, EXAPP-04)
- Setup-Doku fuer ChatGPT, Cursor, Open WebUI und MUCGPT gegen die echten Clients (Phase 5, EXAPP-05); Phase 1 dokumentiert nur die selbst verprobten Wege
- Tasks beziehungsweise VTODO, MCP-Prompts, Response-Format-Parameter, Talk, Tables, Mail (v1.x und v2)
- Loeschen, Ueberschreiben, Verschieben, Freigaben aendern: dauerhaft ausgeschlossen, nicht aufgeschoben
- Eigener Suchindex, RAG, Embeddings: dauerhaft ausgeschlossen (Unified Search ist berechtigungstreu)
- Dynamisches Filtern von `tools/list` nach installierten Apps: bewusst verworfen (bricht Cachebarkeit und Budget-Messung)

## Subsequent Slice Plan

Jede spaetere Phase legt eine vertikale Scheibe auf dieses Skelett, ohne seine Architekturentscheidungen zu aendern:

- Phase 1 (dieses Skelett, 14 Plaene): `files_read` per stdio, dann Create-only-Upload mit Test-Nextcloud, dann HTTP-Transport mit Client-Matrix, dann die restlichen Tools als Scheiben (Dateien, Notes, Deck, Kalender, Kontakte, Unified Search, ChatGPT-Profil), plus App-ID-Freeze und der context_agent-Fix als Flanken
- Phase 2: Admin installiert dieselbe Codebasis als ExApp; jede Anfrage laeuft unter der Identitaet des angemeldeten Nutzers (die Credential-Naht in `deps.py` bekommt eine dritte Quelle)
- Phase 3: MCP-Client verbindet plug-and-play per OAuth 2.1; der `token_verifier`-Pfad ersetzt den statischen Bearer, der Passthrough bleibt als Fallback
- Phase 4: Nutzer verwaltet Zugriff und Tokens in den Nextcloud-Settings, und `prepare_context` buendelt die vorhandenen Lesefunktionen per Fan-out
- Phase 5: Haertung, Signatur und Store-Einreichung vor der Nextcloud Conference September 2026, plus Setup-Doku pro Ziel-Client
