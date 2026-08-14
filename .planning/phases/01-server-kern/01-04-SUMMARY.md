---
phase: 01-server-kern
plan: 04
subsystem: api
tags: [streamable-http, asgi, uvicorn, starlette, transport-security, basic-auth, bearer, stateless, client-matrix, tdd]

# Dependency graph
requires:
  - phase: 01-02
    provides: "MCPServer-Singleton mit reg_*-Autoload, deps.resolve_credentials(ctx) als Naht, config.normalize_base_url, Credentials mit maskiertem repr, ToolError/graceful"
  - phase: 01-03
    provides: "compose.test.yml, scripts/bootstrap_test_nc.sh und .env.test als Basis des CI-Integrationsjobs"
provides:
  - "src/mcp_connector/entry_http.py: ASGI-App fuer uvicorn, ein Endpoint POST /mcp fuer beide Protokoll-Aeren"
  - "TransportSecuritySettings aus NC_MCP_ALLOWED_HOSTS, inklusive Port-Wildcard pro Hostname und ehrlichem Opt-out hinter einem Proxy"
  - "Unauthentifizierter GET /health mit status und version, ohne Konfigurationsdetails"
  - "Drei exklusive Credential-Modi in deps.py: stdio (Env), HTTP-Basic-Passthrough, Static Bearer (secrets.compare_digest)"
  - "tests/compat/modern_client_check.py und legacy_client_check.py als eigenstaendige Exit-Code-Checks fuer CI und Test"
  - "tests/compat/test_client_matrix.py: SDK 2.x und SDK 1.29 gegen denselben Endpoint plus Restart-Ueberlebens-Beweis"
  - "CI-Integrationsjob mit Docker-Nextcloud plus Matrix-Schritten, Matrix-Marker zusaetzlich im Unit-Job"
affects: [01-05-files-search-list, 01-10-oauth-vorbereitung, 01-13-contribution-227, 01-14-tool-contract, 02-exapp-shell, 03-oauth]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modus-Auswahl als reine Funktion: select_mode(env, headers=...) ist ohne Server testbar, die Modi schliessen sich gegenseitig aus"
    - "Der Authorization-Header ist Material, keine Identitaetsbehauptung: Credentials gehen unveraendert an Nextcloud, Nextcloud authentifiziert"
    - "Auth-Verdrahtung ist eine Startentscheidung: auth= und token_verifier= sind Konstruktorargumente, ein Moduswechsel ist ein Neustart"
    - "Transport-Hardening kommt aus der Config, nicht aus dem SDK-Default: allowed_hosts explizit, sonst 421 ohne erkennbaren Grund"
    - "Externe SDK-Aeren werden als Subprozess mit eigenem Environment getestet, nie durch Imports im Testprozess"
    - "Testschichten sind per Marker getrennt: der Default-Lauf startet nichts, matrix startet Subprozesse, integration braucht Docker"

key-files:
  created:
    - src/mcp_connector/entry_http.py
    - tests/unit/test_http_modes.py
    - tests/unit/test_transport_security.py
    - tests/compat/modern_client_check.py
    - tests/compat/legacy_client_check.py
    - tests/compat/test_client_matrix.py
  modified:
    - src/mcp_connector/config.py
    - src/mcp_connector/deps.py
    - src/mcp_connector/server/__init__.py
    - .github/workflows/ci.yml
    - pyproject.toml
    - README.md

key-decisions:
  - "select_mode nimmt die Header als Keyword-Argument dazu: aus dem Environment allein laesst sich stdio nicht erkennen, denn ein stdio-Prozess hat konstruktionsbedingt keine Header"
  - "Die Auth-Verdrahtung entsteht beim Bau des MCPServer in server/__init__.py, weil auth= und token_verifier= Konstruktorargumente sind und das SDK ein halbes Paar mit ValueError ablehnt"
  - "Im Static-Bearer-Modus bleibt der Nextcloud-Zugang aus dem Env: der Bearer authentifiziert den Aufrufer dieses Servers, er waehlt keinen Nextcloud-Nutzer"
  - "Die Basis-URL kommt in jedem Modus aus NC_MCP_URL, nie aus dem Request: ein Client, der das Ziel waehlen koennte, koennte diesen Server samt Credentials auf einen fremden Host richten"
  - "Der Default-Testlauf deselektiert jetzt auch den matrix-Marker, damit 'uv run pytest' keinen Serverprozess startet"
  - "Der Legacy-Check laeuft mit --isolated --no-project: das zusaetzliche Flag haelt die Aufloesung von der mcp>=2-Pin des Projekts fern, ohne das geforderte --isolated --with zu ersetzen"
  - "AUTH-01 bleibt Pending: Basic-Passthrough und Static Bearer sind implementiert und unit-getestet, der Remote-Rundlauf mit echten App-Passwoertern gegen eine laufende Nextcloud fehlt noch"

patterns-established:
  - "Fehlerklasse statt Fehlertext: fehlende oder falsche Transport-Credentials werden MCPError (kein Modell koennte das korrigieren), Nextcloud-Fehler bleiben gewoehnliche Tool-Fehler"
  - "Kein Fehlertext wiederholt jemals den Authorization-Header, auch nicht gekuerzt; ein parametrisierter Test haelt das fest"
  - "Jeder Test baut seine eigene ASGI-App: der Session-Manager einer App-Instanz darf genau einmal laufen"

requirements-completed: [SRV-01, SRV-05]

# Metrics
duration: 20 min
completed: 2026-08-14
---

# Phase 1 Plan 04: Streamable HTTP mit Credential-Passthrough Summary

**Ein Endpoint fuer beide MCP-Aeren: entry_http.py als uvicorn-App mit Host-Allowlist und /health, drei exklusive Credential-Modi (stdio, Basic-Passthrough, Static Bearer mit compare_digest) und ein Matrix-Test, der SDK 1.29 und SDK 2.x gegen dieselbe URL fuehrt und den Serverneustart ueberlebt.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-14T16:05:00Z
- **Completed:** 2026-08-14T16:25:00Z
- **Tasks:** 3 (davon 2 nach TDD)
- **Files modified:** 12 (6 neu, 6 geaendert)

## Accomplishments

- Streamable HTTP ist deploybar: `uv run uvicorn mcp_connector.entry_http:app --host 127.0.0.1 --port 8765`, MCP auf `POST /mcp`, Liveness auf `GET /health`.
- SRV-01 ist bewiesen, nicht behauptet: ein Client mit mcp 2.0.0 und ein Client mit mcp 1.29.0 (eigenes Environment) bekommen aus demselben Endpoint ihre Tool-Liste, ohne "Session terminated".
- SRV-05 ist bewiesen: der Matrix-Test toetet den uvicorn-Prozess, startet ihn neu und laesst denselben Client-Code erneut laufen; die Antwort ist Byte fuer Byte dieselbe.
- Drei Credential-Modi, die sich gegenseitig ausschliessen, mit 32 Unit-Tests fuer Happy Path, Fehlerpfade und Leck-Freiheit.
- Der 421-Fall aus Pitfall 6 ist zweimal abgesichert: in-process gegen die ASGI-App und ueber einen echten Socket gegen den laufenden Server.
- CI kennt jetzt drei Schichten: Unit plus Contract plus Matrix ohne Docker, und einen Integrationsjob mit Test-Nextcloud und Matrix-Block.

## Task Commits

1. **Task 1: Drei exklusive Auth-Modi in config.py und deps.py** (TDD)
   - `00074da` test: failing tests for the three credential modes
   - `30f8b32` feat: implement the three exclusive credential modes
2. **Task 2: ASGI-Entry-Point mit Transport-Security und /health** (TDD)
   - `15d2235` test: failing tests for the HTTP entry point
   - `c01140c` feat: add the ASGI entry point with transport security and health
3. **Task 3: Client-Matrix, Restart-Beweis und CI-Verdrahtung**
   - `74bce60` test: prove the client matrix and the restart survival
   - `6500a14` docs: document the HTTP mode, the host allowlist and the test layers

## Files Created/Modified

- `src/mcp_connector/entry_http.py` (neu) - ASGI-App, TransportSecuritySettings aus der Config, unauthentifizierter `/health`, `build_app(env)` als testbare Fabrik. Enthaelt bewusst kein Aera-Flag und keine Mount-Konstruktion.
- `src/mcp_connector/config.py` - `select_mode`, `static_bearer`, `allowed_hosts` (Port-Wildcard pro Name), `dns_rebinding_protection`, `public_url`, `load_base_url`.
- `src/mcp_connector/deps.py` - Modus-Verzweigung in `resolve_credentials`, Basic-Dekodierung ohne Header-Echo, `StaticBearerVerifier` mit `secrets.compare_digest`, `build_auth` als Paar-Fabrik.
- `src/mcp_connector/server/__init__.py` - baut den MCPServer mit dem Auth-Paar aus `deps.build_auth()`; Docstring auf "einziger Ort, der Tools registriert" korrigiert.
- `tests/unit/test_http_modes.py` (neu) - 32 Faelle: Modusauswahl, Dekodierung, alle Fehlerpfade, Leck-Freiheit, Allowlist-Parsing.
- `tests/unit/test_transport_security.py` (neu) - 10 Faelle: /health, 421 fuer fremden Host, Erfolg fuer erlaubten Host mit und ohne Port, Proxy-Opt-out, Auth-Layer bleibt im Passthrough unbewaffnet.
- `tests/compat/modern_client_check.py` (neu) - mcp-2.x-Client, `httpx2.AsyncClient` traegt den Basic-Header, Exit 0/1.
- `tests/compat/legacy_client_check.py` (neu) - mcp-1.x-API (`streamablehttp_client` plus `ClientSession.initialize`), laeuft nur im isolierten Environment, Exit 0/1.
- `tests/compat/test_client_matrix.py` (neu) - startet uvicorn auf einem freien Port, /health-Polling, moderner Check, Legacy-Check, Restart-Beweis, 421 ueber echten Socket.
- `.github/workflows/ci.yml` - Matrix-Schritt im Unit-Job, neuer Integrationsjob mit `docker compose up -d --wait`, Bootstrap, `-m integration`, Matrix-Block und Logs bei Fehlschlag.
- `pyproject.toml` - `addopts` deselektiert jetzt auch `matrix`, Marker-Beschreibung praezisiert.
- `README.md` - HTTP-Modus mit Startkommando, /health, Host-Allowlist-Erklaerung, korrigierte und erweiterte Env-Tabelle, Testschichten.

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die beiden folgenreichsten:

- **Der Header ist Material, keine Identitaet.** Die SDK-Docstring warnt ausdruecklich davor, einen Header als Identitaetsbehauptung zu behandeln. Genau das passiert hier nicht: der Server entscheidet nie, wer der Aufrufer ist, er reicht die Basic-Credentials unveraendert an die konfigurierte Nextcloud weiter und laesst Nextcloud authentifizieren. Die Begruendung steht als Kommentar in `deps.py`, weil sie sonst beim naechsten Refactoring verloren geht.
- **Die Modus-Wahl ist eine Startentscheidung.** `auth=` und `token_verifier=` sind Konstruktorargumente des MCPServer, also faellt die Entscheidung beim Prozessstart und nicht pro Request. Das ist keine Einschraenkung, sondern die Eigenschaft, die den Passthrough vom Bearer-Layer sauber trennt (Pitfall 2).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] select_mode braucht die Header, nicht nur das Environment**
- **Found during:** Task 1
- **Issue:** Der Plan spezifiziert `select_mode(env) -> Literal["stdio", "http_passthrough", "http_static_bearer"]`. Aus dem Environment allein ist "stdio" nicht ableitbar: derselbe Env-Satz gilt fuer stdio und fuer den Static-Bearer-Modus, unterschieden werden sie dadurch, dass ein stdio-Prozess keine Transport-Header hat.
- **Fix:** `select_mode(env=None, *, headers=None)`. `headers is None` heisst stdio, und kein Env-Wert kann einen solchen Prozess in einen HTTP-Modus kippen. Die Funktion bleibt rein und ohne Server testbar.
- **Files modified:** src/mcp_connector/config.py
- **Verification:** `tests/unit/test_http_modes.py::test_static_bearer_wins_over_headers_but_never_over_stdio`
- **Committed in:** `30f8b32`

**2. [Rule 3 - Blocking] server/__init__.py musste angefasst werden (nicht in files_modified des Plans)**
- **Found during:** Task 2
- **Issue:** `auth=` und `token_verifier=` sind Konstruktorargumente von `MCPServer`; das Server-Objekt ist ein Modul-Singleton, das beim Import entsteht. Von `entry_http` aus laesst sich der Auth-Layer nicht mehr nachtraeglich bewaffnen, und das SDK wirft `ValueError`, wenn nur eine Haelfte gesetzt ist.
- **Fix:** `server/__init__.py` baut den Server mit `deps.build_auth()`, das `(None, None)` liefert, solange kein Static Bearer konfiguriert ist. Der Docstring wurde von "einziger Ort, der mcp importiert" auf "einziger Ort, der Tools registriert" korrigiert, weil `deps.py` jetzt `MCPError` und die Auth-Typen braucht.
- **Files modified:** src/mcp_connector/server/__init__.py
- **Verification:** `tests/unit/test_transport_security.py::test_passthrough_mode_configures_no_sdk_auth_layer`, `uv run pytest -q` gruen
- **Committed in:** `c01140c`

**3. [Rule 2 - Missing Critical] NC_MCP_PUBLIC_URL ergaenzt**
- **Found during:** Task 1
- **Issue:** `AuthSettings` verlangt `issuer_url` und `resource_server_url`. Ohne konfigurierbare Selbstreferenz haette der Static-Bearer-Modus eine hartkodierte URL im Discovery-Dokument.
- **Fix:** `NC_MCP_PUBLIC_URL` mit Default `http://127.0.0.1:8765`, dokumentiert in der README-Env-Tabelle.
- **Files modified:** src/mcp_connector/config.py, src/mcp_connector/deps.py, README.md
- **Verification:** `tests/unit/test_http_modes.py::test_build_auth_configures_both_in_static_bearer_mode`
- **Committed in:** `30f8b32`, `6500a14`

**4. [Rule 2 - Missing Critical] Default-Testlauf deselektiert den matrix-Marker**
- **Found during:** Task 3
- **Issue:** Akzeptanzkriterium "uv run pytest -q startet keinen Server" war mit `addopts = "-m 'not integration' -q"` nicht erfuellbar: der Marker existierte seit Plan 02, wurde aber im Default-Lauf mitgenommen.
- **Fix:** `addopts = "-m 'not integration and not matrix' -q"`. Ein `-m` auf der Kommandozeile ueberschreibt das weiterhin, deshalb funktioniert `uv run pytest -m matrix -q` unveraendert.
- **Files modified:** pyproject.toml, README.md, .github/workflows/ci.yml (Matrix-Schritt im Unit-Job, damit die Schicht nicht aus der CI faellt)
- **Verification:** `uv run pytest -q` (168 Tests, kein Subprozess), `uv run pytest -m matrix -q` (8 Tests)
- **Committed in:** `74bce60`

**5. [Rule 1 - Bug] README beschrieb NC_MCP_ALLOWED_HOSTS falsch**
- **Found during:** Task 3
- **Issue:** Die Env-Tabelle nannte die Variable "Comma separated allow list of Nextcloud hosts the server may talk to". Das ist das Gegenteil der Wahrheit: es ist die Allowlist der `Host`-Header eingehender Requests. Wer das so liest, traegt seine Nextcloud-Domain ein und bekommt auf jeden Request 421.
- **Fix:** Beschreibung korrigiert, HTTP-Abschnitt um Startkommando, `/health`, die 421-Erklaerung und den Hinweis "--host 0.0.0.0 allowlistet niemanden" erweitert.
- **Files modified:** README.md
- **Verification:** Manuelle Gegenprobe gegen `config.allowed_hosts` und `tests/unit/test_transport_security.py`
- **Committed in:** `6500a14`

**6. [Rule 3 - Blocking] Jeder Transport-Test baut seine eigene ASGI-App**
- **Found during:** Task 2
- **Issue:** Zwei Tests scheiterten mit `RuntimeError: StreamableHTTPSessionManager .run() can only be called once per instance`, weil sie dieselbe App-Instanz nacheinander durch einen TestClient-Lifespan schickten.
- **Fix:** `entry_http.build_app(env)` pro Test statt geteiltem `entry_http.app`; als Kommentar im Testmodul festgehalten.
- **Files modified:** tests/unit/test_transport_security.py
- **Verification:** `uv run pytest tests/unit/test_transport_security.py -q` (10 Tests gruen)
- **Committed in:** `c01140c`

**7. [Rule 2 - Missing Critical] --no-project beim Legacy-Check, ExceptionGroup wird aufgeloest**
- **Found during:** Task 3
- **Issue:** (a) `uv run --isolated --with "mcp>=1.29,<2"` muss ohne `--no-project` die mcp>=2-Pin des Projekts mit aufloesen; das ist unnoetiges Risiko fuer den Regressionstest. (b) Beide Check-Skripte meldeten Fehler als nacktes `ExceptionGroup: unhandled errors in a TaskGroup`, was in CI wertlos ist.
- **Fix:** (a) `--no-project` ergaenzt, `--isolated --with` bleibt wie gefordert Teil der Kommandozeile. (b) `describe()` flacht ExceptionGroups ab: aus dem Rauschen wird `ExceptionGroup(ConnectError: All connection attempts failed)`.
- **Files modified:** tests/compat/test_client_matrix.py, tests/compat/modern_client_check.py, tests/compat/legacy_client_check.py, .github/workflows/ci.yml
- **Verification:** Beide Skripte gegen einen toten Port: Exit 1 mit lesbarer Ursache; gegen den laufenden Server: Exit 0
- **Committed in:** `74bce60`

---

**Total deviations:** 7 auto-fixed (3 blocking, 3 missing critical, 1 bug)
**Impact on plan:** Kein Scope-Zuwachs. Fuenf der sieben Abweichungen sind Anpassungen an harte SDK-Eigenschaften (Konstruktor-Auth, Session-Manager-Lebenszyklus, AuthSettings-Pflichtfelder), eine erfuellt ein Akzeptanzkriterium des Plans, eine korrigiert eine irrefuehrende Doku-Zeile aus Plan 01-01.

## Issues Encountered

- **AUTH-01 bleibt Pending.** Der Passthrough ist implementiert und auf Unit-Ebene vollstaendig getestet, aber kein Test fuehrt bisher einen echten Tool-Aufruf ueber HTTP mit einem echten App-Passwort gegen eine laufende Nextcloud. `tools/list` loest bewusst keine Nextcloud-Anfrage aus, deshalb beweist auch der Matrix-Test den Rundlauf nicht. Der fehlende Nachweis ist ein integration-markierter Test (uvicorn mit `.env.test`, moderner Client mit echtem Basic-Header, `files_read` auf eine bekannte Datei) und gehoert in den naechsten Plan, der ohnehin gegen die Docker-Nextcloud laeuft.
- **Restrisiko Multi-Worker.** Legacy-Clients bekommen weiterhin eine In-Process-Session. Bei mehr als einem uvicorn-Worker brauchen sie Sticky Routing. Das ist bewusst so (Pitfall 1: der Gegenschalter kostet beide Rueckkanaele) und in der README als Betriebssache noch nicht erwaehnt; ein Satz dazu gehoert in die Deployment-Doku spaetestens zu Phase 5.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans. Zwei Ergaenzungen zur Registerlage:

| Threat ID | Status nach diesem Plan |
|-----------|-------------------------|
| T-01-21 | Mitigiert: kein Logging in `deps.py`, ein parametrisierter Test verbietet Header-Echo in Fehlermeldungen, `/health` gibt nur status und version |
| T-01-22 | Mitigiert: `TransportSecuritySettings` aus der Config, 421 in-process und ueber echten Socket belegt |
| T-01-23 | Mitigiert: keine Identitaetsableitung aus dem Header, Begruendung als Kommentar im Code, Basis-URL nie aus dem Request |
| T-01-24 | Mitigiert: `secrets.compare_digest`, Grep-Test haelt es fest |
| T-01-29 | Mitigiert: `/health` liefert genau zwei Felder, Test prueft die Schluesselmenge |

## User Setup Required

None - keine externe Dienstkonfiguration noetig. Fuer den HTTP-Betrieb sind `NC_MCP_URL` und `NC_MCP_ALLOWED_HOSTS` zu setzen, beides in der README dokumentiert.

## Next Phase Readiness

- Der Remote-Transport steht: die folgenden Tool-Plaene (01-05 bis 01-09) brauchen an der Transportschicht nichts mehr zu aendern, ihre Tools laufen unveraendert unter stdio und HTTP.
- Plan 01-13 (Fix-PR an context_agent#227) kann sich auf `tests/compat/legacy_client_check.py` als fertige Reproduktion stuetzen.
- Offen fuer den naechsten Plan mit Docker: der integration-markierte AUTH-01-Rundlauf ueber HTTP mit echtem App-Passwort.
- Phase 2 (ExApp-Shell) erbt die Naht: `deps.resolve_credentials(ctx)` ist der einzige Ort, an dem die AppAPI-Impersonation als vierter Modus eingehaengt wird, ohne Tool-Code anzufassen. Der Lifespan-Fallstrick gemounteter Sub-Apps ist in `entry_http.py` als Kommentar hinterlegt.

## Self-Check: PASSED

- Alle sechs neu angelegten Dateien existieren auf der Platte (`[ -f ]` gegen die key-files-Liste).
- Alle sechs Commit-Hashes sind in `git log` auffindbar.
- Plan-Verifikation: `uv run pytest -q` (168 Tests) gruen ohne Docker, `uv run pytest -m matrix -q` (8 Tests) gruen inklusive Restart-Fall, `uv run ruff check .` und `uv run ruff format --check .` sauber.
- Grep-Gegenprobe: `grep -v '^\s*#' src/mcp_connector/entry_http.py | grep -c stateless_http` ergibt 0, und im gesamten `src/` kommt der Begriff nicht vor.
- `.github/workflows/ci.yml` enthaelt den Integrationsjob mit `docker compose -f compose.test.yml up -d --wait` und beide Matrix-Checks.

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
