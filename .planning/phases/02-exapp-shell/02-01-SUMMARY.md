---
phase: 02-exapp-shell
plan: 01
subsystem: auth
tags: [appapi, exapp, starlette, uvicorn, ocs, nextcloud, lifecycle]

# Dependency graph
requires:
  - phase: 01-server-kern
    provides: config.select_mode, deps.StaticBearerVerifier (constant-time-Muster), entry_http.build_app, nextcloud.http.shared_client, clients/ocs.OCS_HEADERS
provides:
  - "verify_appapi_headers: drei AppAPI-Header zu einer Nextcloud-Nutzer-Id, constant-time, ohne Echo"
  - "require_appapi: derselbe Check fuer einen Starlette-Request, ohne Modulzustand"
  - "lifecycle_routes(env): /heartbeat, /init und /enabled als Starlette-Routen aus einer Fabrik"
  - "report_init_progress: Fortschritts-Push an /ocs/v2.php/apps/app_api/ex-app/status"
  - "appapi_auth_headers: die vier ausgehenden AppAPI-Header als reine Funktion"
  - "config.exapp_configured, config.exapp_settings, ExAppSettings mit maskiertem repr"
  - "entry_exapp.build_exapp_app und nc-mcp-exapp als vierter Betriebsmodus"
affects: [02-02 vierter Credential-Modus, 02-03 Container und Manifest, 02-04 HaRP-Testtopologie, 03 OAuth Discovery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Routen-Fabrik statt Dekorator-Registrierung am Singleton (Modus-Trennung erzwingbar)"
    - "Guard gibt Nutzer-Id ODER fertige Response zurueck, kein Kontrollfluss ueber Exceptions nach aussen"
    - "Eine _json-Hilfsfunktion setzt Cache-Control: no-store auf jeder Antwort, auch auf Fehlern"

key-files:
  created:
    - src/mcp_connector/exapp/__init__.py
    - src/mcp_connector/exapp/auth.py
    - src/mcp_connector/exapp/lifecycle.py
    - src/mcp_connector/exapp/status.py
    - src/mcp_connector/entry_exapp.py
    - tests/unit/test_exapp_auth.py
    - tests/unit/test_exapp_lifecycle.py
    - tests/unit/test_exapp_entry.py
  modified:
    - src/mcp_connector/config.py
    - src/mcp_connector/entry_http.py
    - src/mcp_connector/nextcloud/credentials.py
    - pyproject.toml
    - vulture_whitelist.py
    - tests/unit/test_config.py
    - tests/unit/test_http_modes.py

key-decisions:
  - "Lifecycle-Routen kommen aus einer Fabrik und werden nur von entry_exapp angehaengt, nicht per Dekorator am geteilten Serverobjekt registriert (D-23)"
  - "exapp gewinnt in select_mode gegen den statischen Bearer, aber nie gegen stdio; ein Prozess mit beiden Kanaelen wird beim Start mit Exit-Code 2 abgelehnt (D-27)"
  - "Die AppAPI-Variablen behalten ihre Namen ohne NC_MCP_-Praefix, weil der Deploy-Daemon sie vorgibt"
  - "/init antwortet auch bei gescheitertem Fortschritts-Push 200 (Pitfall 3)"
  - "x-origin-ip beendet /init und /enabled mit 404 (Pitfall 2, T-02-04)"
  - "EXAPP-01 und AUTH-05 bleiben Pending: dieser Plan belegt den Kontrakt in-process, nicht die Installation"

patterns-established:
  - "Fabrik-Pattern fuer Routen: jede Pruefung baut ihre eigene App, kein geteilter Zustand zwischen Tests"
  - "AppApiRejected traegt keinen Wert und keine Meldung; nach aussen immer 401 ohne Detail"
  - "Env als Parameter durch die ganze Kette (lifecycle_routes, require_appapi, report_init_progress), damit nichts os.environ braucht"

requirements-completed: []

# Metrics
duration: 30 min
completed: 2026-08-15
---

# Phase 2 Plan 01: AppAPI-Handshake, Lifecycle-Endpunkte und ExApp-Entrypoint Summary

**Der komplette AppAPI-Lebenszyklus selbst implementiert: drei Header per compare_digest zu einer Nutzer-Id, /heartbeat ungeschuetzt, /init mit OCS-Fortschritts-Push, /enabled mit leerem error-Feld, plus ein eigener Entry-Point, der Phase 1 nachweislich unberuehrt laesst.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-08-15T05:45:00Z
- **Completed:** 2026-08-15T06:15:00Z
- **Tasks:** 3 (davon 2 im TDD-Zyklus, also 5 Code-Commits)
- **Files modified:** 15 (8 neu, 7 geaendert), 1197 Zeilen hinzu, 0 Zeilen geloescht

## Accomplishments

- `exapp/auth.py`: `verify_appapi_headers` prueft die drei Header in der Reihenfolge aus 02-RESEARCH.md Pattern 1, vergleicht App-Id und Secret per `secrets.compare_digest` auf UTF-8-Bytes und laesst weder den empfangenen Wert noch das Secret in Exception oder Logrecord erscheinen. Ein Umlaut im Header endet als 401, nie als 500.
- `exapp/lifecycle.py`: die drei Endpunkte als `Route`-Objekte aus `lifecycle_routes(env)`. `/heartbeat` prueft bewusst nichts, `/init` und `/enabled` laufen durch `_guard`, jede Antwort traegt `Cache-Control: no-store`.
- `exapp/status.py`: ein einziger `PUT` auf `/ocs/v2.php/apps/app_api/ex-app/status` mit den vier ausgehenden Headern und leerer Nutzer-Id; jeder Fehler bleibt eine Logzeile und wird nie zur Ausnahme.
- `config.py`: vierter Modus `exapp` inklusive Docstring-Tabelle, `exapp_configured`, `exapp_settings` und `ExAppSettings` mit maskiertem `__repr__`.
- `entry_exapp.py`: `build_exapp_app` haengt die Lifecycle-Routen an die MCP-App, `main` lehnt einen zweiten Credential-Kanal und einen fehlenden Port mit lesbarer Zeile plus Exit-Code 2 ab, danach uvicorn per Unix-Socket (HaRP) oder Host und Port.
- 73 neue Testfaelle ohne Docker, ohne Netz und ohne Serverprozess; die Suite waechst von 489 auf 562 gruene Tests.

## Task Commits

1. **Task 1: Vierter Modus in config.py und die AppAPI-Header-Pruefung** - `16efc8a` (test, RED) und `3701262` (feat, GREEN)
2. **Task 2: Die drei Lifecycle-Endpunkte und der Fortschritts-Push** - `56d206e` (test, RED) und `7207fd2` (feat, GREEN)
3. **Task 3: Entry-Point der ExApp und Abgrenzung gegen den HTTP-Modus** - `99ec25b` (feat)

Kein REFACTOR-Commit: beide GREEN-Staende waren bereits die Zielform, ein leerer Refactor-Commit haette nichts belegt.

## Files Created/Modified

- `src/mcp_connector/exapp/__init__.py` - Paket-Docstring mit D-23 und D-24, keine Re-Exports, keine Nebenwirkungen beim Import
- `src/mcp_connector/exapp/auth.py` - `AppApiRejected`, `verify_appapi_headers`, `require_appapi`, `_same` (constant-time)
- `src/mcp_connector/exapp/lifecycle.py` - `lifecycle_routes`, die drei Handler, `_guard`, `_json`, `_text`
- `src/mcp_connector/exapp/status.py` - `report_init_progress`, `STATUS_PATH`
- `src/mcp_connector/entry_exapp.py` - `build_exapp_app`, `main`, Startvalidierung, uds/TCP-Weiche
- `src/mcp_connector/config.py` - zehn AppAPI-ENV-Konstanten, `Mode` um `exapp` erweitert, `exapp_configured`, `exapp_settings`, `ExAppSettings`, `_required_exapp`
- `src/mcp_connector/nextcloud/credentials.py` - `appapi_auth_headers` (vier Header, neues dict pro Aufruf)
- `src/mcp_connector/entry_http.py` - Docstring korrigiert: weiterhin genau eine Custom-Route, keine Lifecycle-Routen hier, kein FastAPI-Runner in Phase 2
- `pyproject.toml` - Console-Script `nc-mcp-exapp`
- `vulture_whitelist.py` - `ENV_APP_PERSISTENT_STORAGE` mit Begruendung
- `tests/unit/test_exapp_auth.py` - 26 Faelle: Happy Paths, alle Ablehnungen, Kein-Echo, Kein-Log, Quelltext-Gate, ausgehende Header
- `tests/unit/test_exapp_lifecycle.py` - 23 Faelle gegen die drei Routen per TestClient
- `tests/unit/test_exapp_entry.py` - 9 Faelle: Routen-Abgrenzung gegen entry_http und die drei Abbruchpfade von `main`
- `tests/unit/test_config.py` - ExApp-Abschnitt: `exapp_configured`, `exapp_settings`, Fehlerform, maskiertes repr
- `tests/unit/test_http_modes.py` - Praezedenz des vierten Modus (gegen Bearer, nie gegen stdio)

## Decisions Made

- **Routen-Fabrik statt Registrierung am Singleton.** 02-RESEARCH.md Pattern 2 skizzierte `@mcp.custom_route`. Das haette `/heartbeat`, `/init` und `/enabled` auch im eigenstaendigen HTTP-Modus erscheinen lassen, sobald irgendein Import das Modul beruehrt. D-23 verlangt das Gegenteil, also liefert `lifecycle_routes(env)` die Routen und `entry_exapp` haengt sie an. Nebeneffekt: Annahme A4 aus dem Research (custom_route kann PUT und POST) ist gegenstandslos.
- **`env` als Parameter durch die ganze Kette.** `require_appapi(request, *, env=None)` und `report_init_progress(progress, *, env=None)` nehmen das Environment entgegen, damit `lifecycle_routes(env)` es durchreichen kann. Ohne diesen Parameter waeren die Lifecycle-Tests nur ueber `os.environ`-Monkeypatching moeglich gewesen, was der Plan ausdruecklich nicht wollte.
- **Doppelter Schutz um den Fortschritts-Push.** `report_init_progress` faengt `httpx.HTTPError` selbst ab; zusaetzlich umschliesst der `/init`-Handler den Aufruf. Der Plan verlangt beides implizit: der Test ersetzt die Funktion durch eine, die wirft, und erwartet trotzdem 200.
- **EXAPP-01 und AUTH-05 bleiben Pending.** Beide Requirements stehen im Plan-Frontmatter, sind aber durch diesen Plan nicht belegbar: EXAPP-01 braucht Dockerfile, `info.xml` und eine laufende Nextcloud (02-03 bis 02-05), AUTH-05 den vierten Credential-Modus samt Permission-Parity (02-02, 02-05). Das folgt der Phase-1-Praxis (AUTH-01 blieb bis zum Live-Beweis Pending).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `env`-Parameter fuer `require_appapi` und `report_init_progress`**
- **Found during:** Task 1 und Task 2
- **Issue:** Der Plan gibt `require_appapi(request) -> str` und `report_init_progress(progress: int = 100)` vor, verlangt aber gleichzeitig `lifecycle_routes(env)` mit einem festen Test-Env. Ohne einen Weg, `env` weiterzureichen, waeren die Lifecycle-Tests auf `os.environ` angewiesen gewesen.
- **Fix:** Beide Funktionen bekamen einen optionalen Keyword-Parameter `env: Mapping[str, str] | None = None`, der auf `os.environ` zurueckfaellt. Kein Modulzustand, kein Caching.
- **Files modified:** src/mcp_connector/exapp/auth.py, src/mcp_connector/exapp/status.py, src/mcp_connector/exapp/lifecycle.py
- **Verification:** `uv run pytest tests/unit/test_exapp_lifecycle.py` (23 Faelle) laeuft ohne jede Aenderung an `os.environ`.
- **Committed in:** `3701262` und `7207fd2`

**2. [Rule 2 - Missing Critical] Regressionstestdatei `tests/unit/test_exapp_entry.py`**
- **Found during:** Task 3
- **Issue:** Die Modus-Trennung (D-23) und die Startvalidierung (D-27, T-02-08) standen nur als CLI-Akzeptanzkriterien im Plan, also in keinem Testlauf. Eine spaetere Aenderung an `entry_http` oder `entry_exapp` haette beides still brechen koennen.
- **Fix:** Neue Unit-Testdatei mit neun Faellen: die ExApp-App traegt die drei Routen und `/mcp`, die Phase-1-App traegt keine davon, und `main` endet mit Exit-Code 2 bei `NC_MCP_STATIC_BEARER`, bei `NC_MCP_APP_PASSWORD`, bei fehlender Deploy-Variable und bei fehlendem oder unbrauchbarem `APP_PORT`.
- **Files modified:** tests/unit/test_exapp_entry.py (neu, nicht in `files_modified` des Plans)
- **Verification:** `uv run pytest tests/unit/test_exapp_entry.py` -> 9 passed; kein Serverprozess wird gestartet.
- **Committed in:** `99ec25b`

**3. [Rule 3 - Blocking] Akzeptanzkriterium `uv run nc-mcp-exapp` durch `python -m` ersetzt**
- **Found during:** Task 3
- **Issue:** Die Aenderung an `project.scripts` loest bei `uv run` eine Neuinstallation des Projekts aus. Diese scheitert auf diesem Host mit `os error 32`, weil zwei laufende `nc-mcp.exe`-Prozesse des Owners (PID 3524 und 23956) die Datei `.venv/Scripts/nc-mcp.exe` sperren. Fremde Prozesse zu beenden ist nicht Aufgabe dieses Plans.
- **Fix:** Alle weiteren Kommandos laufen mit `uv run --no-sync`; das Akzeptanzkriterium wurde als `NC_MCP_STATIC_BEARER=x ... uv run --no-sync python -m mcp_connector.entry_exapp` nachgewiesen (identischer Einstiegspunkt, `main()` ueber `__main__`). Ergebnis: Exit-Code 2 plus die Logzeile, die `NC_MCP_STATIC_BEARER` beim Namen nennt.
- **Files modified:** keine (nur Ausfuehrungsweg)
- **Verification:** siehe Verification-Log unten, Punkt 4.
- **Committed in:** nicht anwendbar

**4. [Rule 1 - Bug] Em-Dash in STATE.md ersetzt**
- **Found during:** Abschluss
- **Issue:** Die Zeile `Current focus:` trennte Phase und Name mit einem Em-Dash (U+2014), das die globale Projektregel verbietet.
- **Fix:** Ersetzt durch `Phase 2, ExApp-Shell`. Eine Pruefung auf U+2014 und U+2013 laeuft jetzt beim Schreiben der Datei mit.
- **Files modified:** .planning/STATE.md
- **Verification:** Zaehlung von U+2014 und U+2013 in STATE.md -> 0
- **Committed in:** Docs-Commit dieses Plans

### Abweichungen ohne Rule-Zuordnung (Plan-Text gegen Realitaet)

- **Ausgangsstand der Testsuite:** Der Plan nennt 476 gruene Tests als Ausgangswert, tatsaechlich waren es 489 (Stand `abbfd0f`). Nach diesem Plan: 562.
- **vulture-Gate zeitversetzt:** `uv run vulture` meldete nach Task 1 und Task 2 Namen, deren Aufrufer erst in der jeweils naechsten Aufgabe entstehen (`ENV_APP_HOST`, `ENV_APP_PORT`, `ENV_HP_SHARED_KEY`, `ENV_HP_EXAPP_SOCK`, `appapi_auth_headers`). Der Plan sieht das Gate deshalb erst in Task 3 vor ("erst vulture laufen lassen, dann nur die tatsaechlich gemeldeten Namen eintragen"). Vorratseintraege in der Whitelist wurden bewusst vermieden; am Ende des Plans ist das Gate leer, eingetragen wurde genau ein Name (`ENV_APP_PERSISTENT_STORAGE`).
- **`# noqa: S105` bei `HP_SHARED_KEY` entfernt:** ruff meldet die Regel dort nicht, und ein unbenutztes `noqa` faellt unter RUF100. Die Begruendung steht jetzt als normaler Kommentar.

---

**Total deviations:** 4 auto-fixed (1 Bug, 1 Missing Critical, 2 Blocking) plus 3 dokumentierte Textabweichungen.
**Impact on plan:** Kein Scope-Zuwachs. Zwei Signaturen tragen einen optionalen Parameter mehr, eine Testdatei kam hinzu, ein Akzeptanzkriterium wurde ueber denselben Code-Pfad statt ueber den Console-Script-Wrapper nachgewiesen.

## Checkpoints

Der Plan enthaelt keine Checkpoints. Im AUTO_MODE waren keine auto-approve-Entscheidungen noetig; es kam auch kein Package-Legitimacy-Fall auf, weil dieser Plan D-24 folgt und keine neue Laufzeit-Dependency aufnimmt (`uv sync` unveraendert, `pyproject.toml` nur um einen Console-Script-Eintrag ergaenzt).

## Verification Log

1. `uv run --no-sync pytest` -> **562 passed, 54 deselected** (ohne Docker, ohne Nextcloud, ohne Serverprozess)
2. `uv run --no-sync ruff check .` -> All checks passed; `uv run --no-sync ruff format --check .` -> 98 files already formatted
3. `uv run --no-sync pyright` -> **0 errors, 0 warnings, 0 informations**; `uv run --no-sync vulture src scripts vulture_whitelist.py` -> leer
4. Gegenprobe Modus-Trennung: `build_exapp_app(...)` -> `['/enabled', '/heartbeat', '/init', '/mcp']`; `entry_http.build_app({})` -> `['/health', '/mcp']`
5. Gegenprobe Fallback-Verbot: `NC_MCP_STATIC_BEARER=x ... python -m mcp_connector.entry_exapp` -> Exit-Code 2, Logzeile nennt `NC_MCP_STATIC_BEARER`
6. `uv run --no-sync python scripts/check_tool_budget.py` -> Exit-Code 0 (10642 Bytes, 15 Tools, Budget 12500; Tool-Oberflaeche unveraendert)
7. Task-Akzeptanzkriterien einzeln: `grep -c "compare_digest" exapp/auth.py` -> 3; `grep -v '^\s*#' exapp/auth.py | grep -c "logger\|logging"` -> 0; `grep -v '^\s*#' exapp/lifecycle.py | grep -c "no-store"` -> 3; `... | grep -c "custom_route"` -> 0; `grep -v '^\s*#' exapp/status.py | grep -c "ex-app/status"` -> 1; `grep -c "nc-mcp-exapp" pyproject.toml` -> 1; `select_mode(..., headers={})` -> `exapp`, `headers=None` -> `stdio`

## Threat Model Coverage

| Threat ID | Umsetzung | Beleg |
|-----------|-----------|-------|
| T-02-01 | `compare_digest` fuer App-Id und Secret, base64 mit `validate=True`, Ablehnung ohne Detail | `test_a_wrong_secret_is_rejected`, `test_the_verifier_compares_in_constant_time` |
| T-02-02 | Kein `==`, kein Teilvergleich, Vergleich auf UTF-8-Bytes | Quelltext-Gate im Test (kein `==` im Verifier) |
| T-02-03 | `AppApiRejected` ohne Wert, kein f-String mit Headerinhalt, `ExAppSettings.__repr__` maskiert | `test_no_rejection_ever_repeats_the_header`, `test_verification_writes_nothing_to_the_log`, `test_the_settings_repr_masks_the_app_secret` |
| T-02-04 | `x-origin-ip`-Guard beendet `/init` und `/enabled` mit 404 | `test_a_request_through_the_php_proxy_is_not_served` |
| T-02-05 | `/heartbeat` prueft nichts und antwortet immer 200 | drei Heartbeat-Tests (ohne Header, mit gueltigen, mit falschem Secret) |
| T-02-06 | Antwort ist als Menge genau `{"status"}` | `test_heartbeat_leaks_no_configuration` |
| T-02-07 | `Cache-Control: no-store` zentral in `_json`/`_text` | `test_every_answer_carries_no_store` (6 Faelle inkl. 400, 401, 404) |
| T-02-08 | `main` lehnt `NC_MCP_STATIC_BEARER` und `NC_MCP_APP_PASSWORD` mit Exit-Code 2 ab | `test_a_second_credential_channel_stops_the_start` |
| T-02-09 | transfer: `follow_redirects=False` bleibt in `nextcloud/http.py`, Basis-URL kommt aus der Deploy-Umgebung | `status.report_init_progress` nutzt `shared_client()` und `settings.base_url` |

## Known Stubs

Keine. Jede Funktion dieses Plans hat ihren produktiven Aufrufer: `verify_appapi_headers` <- `require_appapi` <- `_guard` <- `/init` und `/enabled`; `appapi_auth_headers` <- `report_init_progress`; `lifecycle_routes` <- `build_exapp_app`.

Bewusst noch nicht verdrahtet, laut Plan Sache von 02-02: `deps.resolve_credentials` kennt den Modus `exapp` noch nicht und faellt fuer ihn auf `load_stdio_credentials` zurueck. Das ist kein stiller Fallback: ein ExApp-Prozess hat kein `NC_MCP_APP_PASSWORD` (`main` verbietet es sogar), also endet dieser Weg heute in einem benannten `ToolError` statt in einer falschen Identitaet.

## Issues Encountered

- **Gesperrte `.venv/Scripts/nc-mcp.exe`:** siehe Abweichung 3. Geloest durch `uv run --no-sync`; die laufenden Prozesse des Owners wurden nicht angefasst. Folge fuer die naechsten Plaene: wer den Console-Script `nc-mcp-exapp` tatsaechlich installiert braucht, muss die beiden `nc-mcp.exe`-Prozesse vorher beenden und einmal `uv sync` laufen lassen.

## User Setup Required

Keine. Dieser Plan braucht weder Docker noch eine laufende Nextcloud, und er nimmt keine neue Dependency auf.

## Next Phase Readiness

- **Bereit fuer 02-02:** `appapi_auth_headers` liegt bereits in `nextcloud/credentials.py`, genau dort, wo die `httpx.Auth`-Implementierung und `Credentials.auth()` entstehen sollen. `config.exapp_settings` liefert die vier Werte, die der vierte Credential-Modus braucht.
- **Bereit fuer 02-03:** `entry_exapp.main` erwartet `APP_HOST`/`APP_PORT` bzw. `HP_SHARED_KEY`/`HP_EXAPP_SOCK` genau so, wie der Deploy-Daemon sie setzt; der Startbefehl fuer `ENTRYPOINT` heisst `nc-mcp-exapp`. `ENV_APP_PERSISTENT_STORAGE` ist deklariert, aber noch nicht ausgewertet.
- **Offener Punkt:** Der Console-Script-Eintrag ist in `pyproject.toml`, aber auf diesem Host noch nicht ins `.venv` installiert (gesperrte Datei). Vor dem Container-Bau irrelevant, fuer einen lokalen `manual-install`-Dev-Loop relevant.
- **Requirements:** EXAPP-01 und AUTH-05 bleiben bewusst Pending, siehe Decisions.

## Self-Check: PASSED

- Alle acht neu angelegten Dateien liegen auf der Platte (`[ -f ]` je Datei geprueft).
- Alle fuenf Task-Commits sind in `git log` auffindbar: `16efc8a`, `3701262`, `56d206e`, `7207fd2`, `99ec25b`.
- Alle Akzeptanzkriterien der drei Aufgaben und alle fuenf Punkte des Plan-Verification-Blocks wurden ausgefuehrt, siehe Verification Log.
- Kein Commit dieses Plans loescht eine Datei (`git diff --stat abbfd0f..HEAD` -> 1197 Zeilen hinzu, 0 Dateien geloescht).

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
