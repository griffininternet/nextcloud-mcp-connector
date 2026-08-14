---
phase: 01-server-kern
plan: 01
subsystem: infra
tags: [uv, pytest, ruff, mcp, github-actions, supply-chain, tdd]

# Dependency graph
requires: []
provides:
  - "Reproduzierbare uv-Umgebung mit auditierten Pins (mcp[cli] 2.0.0, httpx 0.28.1, lxml, icalendar, vobject, pydantic) und committetem uv.lock"
  - "Console-Script-Vertrag nc-mcp = mcp_connector.entry_stdio:main (D-02)"
  - "Test-Harness: anyio_backend-Fixture, nc_env/live_env, Integration-Skip-Guard ohne Docker"
  - "RED-Contract-Test, der die erste Faehigkeit files_read exakt beschreibt (Ziel von Plan 01-02)"
  - "Token-Budget-Gate scripts/check_tool_budget.py mit BUDGET_BYTES = 24000, in CI verdrahtet (D-14)"
  - "CI-Workflow unit: uv sync --frozen, ruff check, ruff format --check, Unit+Contract, Budget-Gate"
  - "docs/dependency-audit.md als Supply-Chain-Nachweis (httpx2 nur transitiv)"
affects: [01-02-walking-skeleton, 01-14-tool-contract, alle Phase-1-Plaene, Phase 2 ExApp-Shell]

# Tech tracking
tech-stack:
  added:
    - "mcp[cli] 2.0.0 (>=2.0,<3), Fallback-Pin >=1.29,<2 dokumentiert"
    - "httpx 0.28.1, lxml 6.1.1, icalendar 7.2.2, vobject 0.9.9, pydantic 2.13.4"
    - "dev: pytest 9.1.1, respx 0.23.1, ruff 0.16.3 (anyio 4.14.2 transitiv als Async-Test-Plugin)"
    - "hatchling als Build-Backend, src-Layout"
  patterns:
    - "Schema-Diaet-Vertrag ab Tag 1 messbar: Byte-Budget der tools/list-Antwort statt tiktoken"
    - "Docker-freie Default-Suite: addopts -m 'not integration' plus Env-Guard in conftest"
    - "conftest.py importiert nie Projektmodule, damit RED-Tests die Collection nicht sprengen"
    - "Supply-Chain-Policy: junge transitive Pakete nie direkt pinnen, uv.lock committen, --frozen in CI"

key-files:
  created:
    - pyproject.toml
    - uv.lock
    - .gitattributes
    - .github/workflows/ci.yml
    - src/mcp_connector/__init__.py
    - scripts/check_tool_budget.py
    - tests/conftest.py
    - tests/contract/test_tool_surface.py
    - tests/unit/test_project_layout.py
    - docs/dependency-audit.md
  modified:
    - .gitignore

key-decisions:
  - "httpx2 bleibt ausschliesslich transitive Dependency von mcp und wird nie direkt gepinnt (slopcheck [SUS], Owner-Freigabe nach Verifikation)"
  - "Eigener Code nutzt httpx 0.28, weil respx httpx mockt und nicht httpx2"
  - "ruff schliesst .planning/ aus, weil ruff inzwischen Python-Bloecke in Markdown formatiert und Research-Dokumente wortgetreu bleiben muessen"
  - "mcp_connector als ruff-isort known-first-party, sonst landet es im Block des Fremdpakets mcp"
  - "CI-Workflow ist in dieser RED-Phase bewusst rot (Contract-Test und Budget-Gate brauchen mcp_connector.server aus Plan 01-02)"

patterns-established:
  - "TDD-Gate: Contract-Test beschreibt die Faehigkeit vor der Implementierung, Commit-Typ test(...) vor feat(...)"
  - "Jede neue Quelle bzw. Dependency wird im Audit-Dokument gefuehrt, inklusive uv-tree-Beleg"
  - "Marker-Disziplin: integration (braucht Docker-Nextcloud) und matrix (lokale Subprozesse) sind deklariert"

requirements-completed: []  # SRV-03 bleibt bewusst Pending, siehe Abschnitt "Requirements-Status"

# Metrics
duration: 24min
completed: 2026-08-14
---

# Phase 01 Plan 01: Projekt-Skelett, Toolchain und Test-Harness Summary

**uv-Toolchain mit auditierten Pins (mcp 2.0.0, kein direkter httpx2-Pin), Docker-freie pytest-Basis mit 7 gruenen Projekt-Invarianten, definiert roter files_read-Contract-Test und Byte-basiertes tools/list-Budget-Gate in CI.**

## Performance

- **Duration:** ~24 min (inklusive Wartezeit am blockierenden Package-Legitimacy-Gate)
- **Erster Task-Commit:** 2026-08-14T15:18:15Z
- **Letzter Task-Commit:** 2026-08-14T15:20:45Z
- **Tasks:** 3 von 3 (1 Checkpoint, 2 Auto-Tasks)
- **Files created/modified:** 11 (10 neu, 1 geaendert)

## Accomplishments

- Reproduzierbare Umgebung: `uv sync` loest 56 Pakete auf, `uv.lock` ist committet, CI installiert mit `--frozen`. `uv run python -c "import mcp, httpx, lxml, icalendar, vobject, pydantic"` laeuft mit Exit 0.
- Supply-Chain-Nachweis erbracht: `uv tree --depth 2` zeigt `httpx2 v2.10.0` ausschliesslich als Kind von `mcp[cli] v2.0.0`, nicht als Top-Level-Eintrag. Der Beleg steht in `docs/dependency-audit.md`, ein Unit-Test haelt die Policy maschinell fest.
- RED-Zustand ist definiert und aussagekraeftig: `uv run pytest tests/contract -q` endet mit Exit 2 und `ModuleNotFoundError: No module named 'mcp_connector.server'`. Der Test fordert genau `files_read` mit `read_only_hint=True`, `open_world_hint=False` und `output_schema is None`. Damit weiss Plan 01-02 ohne Rueckfrage, was zu liefern ist.
- Token-Budget-Gate ist nicht dekorativ: die Exit-Code-Logik wurde gegen die echte SDK-Oberflaeche verifiziert (Stub-Server mit einem Tool: 337 Bytes, Exit 0 unter Budget, Exit 1 bei `BUDGET_BYTES = 1`).
- Die Default-Suite laeuft ohne Docker: `addopts = "-m 'not integration' -q"` plus `pytest_collection_modifyitems`-Guard, der `-m integration` ohne `NC_MCP_URL` in Skips verwandelt statt in Fehler. Kein Test wartet auf einen Netzwerk-Timeout.

## Task Commits

1. **Task 1: Package-Legitimacy-Gate** - kein Commit (blockierender Checkpoint, Owner-Freigabe)
2. **Task 2: Toolchain, Dependency-Pins und CI-Grundgeruest** - `e2cd14e` (chore)
3. **Task 3: Test-Harness und RED-Contract-Test** - `e341b90` (test)
4. **Task 3: Token-Budget-Gate** - `c651c39` (feat)

_TDD-Gate-Sequenz: `test(01-01)` (RED) liegt vor `feat(01-01)`. Der GREEN-Gate-Commit fuer den Contract-Test gehoert bewusst zu Plan 01-02, der den Server-Layer liefert. Das ist der geplante Zustand dieses Plans, keine Luecke._

## Files Created/Modified

- `pyproject.toml` - Projekt-Metadaten (PyPI-Name `nextcloud-mcp-connector`, D-02), Dependency-Pins ohne httpx2, Console-Script `nc-mcp`, pytest-Marker `integration`/`matrix`, ruff-Konfiguration inklusive `.planning`-Ausschluss und isort-first-party
- `uv.lock` - 56 aufgeloeste Pakete, Grundlage fuer `uv sync --frozen`
- `.gitattributes` - `*.sh`, `*.yml`, `*.yaml` mit `eol=lf` (Windows-Host, `docker compose exec` bricht sonst an `\r`)
- `.gitignore` - ergaenzt um `.env.test` (Secrets nie im Repo, V14) und `.ruff_cache/`
- `.github/workflows/ci.yml` - Job `unit`: checkout@v5, setup-uv@v5 mit Cache, `uv sync --frozen`, `ruff check .`, `ruff format --check .`, `pytest tests/unit tests/contract`, `python scripts/check_tool_budget.py`
- `src/mcp_connector/__init__.py` - `__version__ = "0.1.0"`, keine Seiteneffekte, kein `print` (stdout ist im stdio-Modus die Leitung)
- `docs/dependency-audit.md` - Audit-Tabelle (12 Pakete), Bewertung des httpx2-[SUS]-Treffers mit Gegenbelegen, `uv tree`-Ausgabe, Supply-Chain-Kontrollen
- `tests/conftest.py` - `anyio_backend` (asyncio), `nc_env`, `live_env`, Integration-Skip-Guard; importiert bewusst kein Projektmodul
- `tests/contract/test_tool_surface.py` - RED bis Plan 01-02: fordert `files_read` mit ehrlichen Annotationen und ohne Output-Schema
- `tests/unit/test_project_layout.py` - 7 gruene Invarianten (kein httpx2-Pin, httpx gepinnt, `not integration` in addopts, Marker deklariert, `nc-mcp`-Script, `requires-python >=3.13`, Paket-Version ohne Seiteneffekte)
- `scripts/check_tool_budget.py` - `BUDGET_BYTES = 24_000` als markierter Startwert, kompakte Serialisierung, Top-5-Tools, Exit 1 bei Ueberschreitung, kein tiktoken

## Decisions Made

- **httpx2 nur transitiv:** Der Owner hat das Gate nach unabhaengiger Pruefung freigegeben. Belege: `mcp` 2.0.0 `requires_dist` enthaelt `httpx2>=2.5.0`; `httpx2` hat Author `Tom Christie <tom@tomchristie.com>`, Maintainer `Pydantic Services Inc. <engineering@pydantic.dev>`, Repo `github.com/pydantic/httpx2` (echte pydantic-Org, 914 Stars, kein Fork, seit 2026-05-11); `encode/httpx` ist seit Maerz 2026 inaktiv, die Nachfolger-Story ist konsistent; unsere Direct-Dependency-Liste enthaelt `httpx2` nicht.
- **Eigener Code bleibt auf httpx:** respx mockt `httpx`, nicht `httpx2`. Ein Wechsel wuerde die gesamte Unit-Test-Strategie kosten.
- **CI ist in dieser Phase rot:** Der Workflow ruft Contract-Test und Budget-Gate auf, beide brauchen `mcp_connector.server`. Das ist der Sinn des RED-Gates. Erster gruener CI-Lauf mit Plan 01-02.
- **Kein tiktoken:** Bytes sind ein deterministischer, modellunabhaengiger Proxy. Der Startwert 24000 wird in Plan 01-14 auf "gemessen plus 15 Prozent" fixiert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff formatiert Python-Bloecke in Markdown und wollte 01-RESEARCH.md umschreiben**
- **Found during:** Task 2 (Verify-Schritt `ruff format --check .`)
- **Issue:** ruff 0.16 formatiert Code-Bloecke in Markdown-Dateien. `ruff format --check .` schlug an `.planning/phases/01-server-kern/01-RESEARCH.md` fehl und haette 20 Snippets im Research-Dokument umgeschrieben. Damit waere das Acceptance-Kriterium "ruff format --check endet mit Exit 0" nur durch Verfaelschung eines Planungsdokuments erreichbar gewesen.
- **Fix:** `exclude = [".planning"]` in `[tool.ruff]` mit Begruendungskommentar. Alles, was ausgeliefert wird (`src/`, `tests/`, `scripts/`, `docs/`), bleibt abgedeckt. Die globale Regel "ruff ueber das ganze Repo" bleibt fuer Code erfuellt.
- **Files modified:** pyproject.toml
- **Verification:** `uv run ruff check .` und `uv run ruff format --check .` beide Exit 0, 7 Dateien formatiert geprueft; `git diff` zeigt keine Aenderung an Planungsdokumenten.
- **Committed in:** e2cd14e

**2. [Rule 3 - Blocking] isort gruppierte mcp_connector mit dem Fremdpaket mcp**
- **Found during:** Task 3 (`ruff check .`, Regel I001)
- **Issue:** Weil das Projekt editierbar installiert ist, hielt ruff `mcp_connector` fuer Third-Party und forderte, `from mcp import Client` und `from mcp_connector.server import mcp` in einen Block zu ziehen. Das haette die Trennung Fremdcode/eigener Code in jeder Datei aufgehoben.
- **Fix:** `[tool.ruff.lint.isort] known-first-party = ["mcp_connector"]`.
- **Files modified:** pyproject.toml
- **Verification:** `uv run ruff check .` Exit 0 bei unveraenderter Importstruktur.
- **Committed in:** e341b90

**3. [Rule 2 - Missing Critical] Zusatz-Invarianten im Unit-Test**
- **Found during:** Task 3
- **Issue:** Der Plan forderte vier Pruefungen. Zwei Invarianten fehlten, die spaeter teuer werden: dass `httpx` ueberhaupt direkt gepinnt ist (sonst koennte jemand still auf `httpx2` wechseln und respx verlieren) und dass die Marker `integration`/`matrix` deklariert sind (sonst warnt pytest und der Docker-Guard verliert seine Grundlage). Zusaetzlich eine Pruefung, dass der Paket-Import ohne Seiteneffekte die Version liefert.
- **Fix:** 7 Tests statt 4, alle gruen.
- **Files modified:** tests/unit/test_project_layout.py
- **Verification:** `uv run pytest tests/unit -q` Exit 0, 7 passed.
- **Committed in:** e341b90

**4. [Rule 1 - Bug] Em-Dashes in STATE.md entfernt**
- **Found during:** State-Update (`gsd-sdk query state.add-decision`)
- **Issue:** Der SDK-Formatter fuegt Entscheidungen mit Em-Dash-Trenner ein. Em-Dashes sind projektweit verboten.
- **Fix:** Alle ` — ` und ` – ` in STATE.md durch `: ` ersetzt (betrifft auch zwei vorher bestehende Zeilen).
- **Files modified:** .planning/STATE.md
- **Verification:** Zaehlung der Em-Dash-Zeichen in STATE.md ergibt 0.
- **Committed in:** SUMMARY-Commit

---

**Total deviations:** 4 auto-fixed (2 blocking, 1 missing critical, 1 bug)
**Impact on plan:** Alle vier Fixes waren fuer Korrektheit oder Regelkonformitaet notwendig. Kein Scope-Creep, keine zusaetzliche Dependency, keine Architekturaenderung.

## Requirements-Status

Der Plan fuehrt `requirements: [SRV-03]`. SRV-03 verlangt Tools mit korrekten Annotationen und token-schlanken Schemas. Dieser Plan liefert den **Vertrag und das Messwerkzeug** dafuer (Contract-Test, Budget-Gate, Schema-Diaet-Regel), aber noch **kein einziges Tool**: `mcp_connector.server` existiert absichtlich nicht. SRV-03 bleibt daher in `REQUIREMENTS.md` auf `Pending` und wird abgehakt, sobald Plan 01-02 den Contract-Test gruen macht (voller 15-Tool-Nachweis in Plan 01-14). `requirements-completed` ist deshalb bewusst leer, statt eine nicht erbrachte Faehigkeit zu behaupten.

## Authentication Gates

Keine. Der einzige Checkpoint war das Package-Legitimacy-Gate (Task 1), kein Auth-Gate.

## Checkpoint-Verlauf

- **Task 1 (checkpoint:human-verify, gate="blocking-human"):** trotz aktivem Auto-Mode **nicht** auto-approved. Package-Legitimacy-Gates sind von der Auto-Approval-Regel ausgenommen, weil hier eine Supply-Chain-Entscheidung ansteht ([SUS]-Befund fuer httpx2). Der Owner hat die Pruefschritte durchlaufen und explizit freigegeben ("approved"). Erst danach lief die erste Installation via uv. Die vom Owner gelieferten Belege stehen unter "Decisions Made" und in `docs/dependency-audit.md`.

## Issues Encountered

Keine ungeplanten Probleme. Der rote Contract-Test und der rote CI-Workflow sind der geplante Zustand.

## Known Stubs

Keine Stubs im Sinne von vorgetaeuschter Funktionalitaet. Bewusst noch nicht existierende Ziele, die der RED-Zustand benennt:

| Ziel | Referenziert von | Faellig in |
|------|------------------|-----------|
| `mcp_connector.server` (Objekt `mcp`) | tests/contract/test_tool_surface.py, scripts/check_tool_budget.py | Plan 01-02 |
| `mcp_connector.entry_stdio:main` (Console-Script `nc-mcp`) | pyproject.toml `[project.scripts]` | Plan 01-02 |

## User Setup Required

Keine. Kein externer Service, keine Env-Variable fuer diesen Plan. `.env.test` entsteht erst mit dem Docker-Bootstrap und ist bereits ignoriert.

## Next Phase Readiness

- Bereit fuer Plan 01-02 (Walking Skeleton): `uv sync` laeuft, das Test-Harness steht, und der rote Contract-Test benennt die zu liefernde Faehigkeit exakt (`files_read`, `read_only_hint=True`, `open_world_hint=False`, kein Output-Schema, also `structured_output=False`).
- Plan 01-02 muss zusaetzlich `mcp_connector/entry_stdio.py` mit `main()` liefern, sonst bleibt das Console-Script `nc-mcp` ein leeres Versprechen.
- Offen fuer spaeter (keine Blocker dieses Plans): Docker-Desktop-Linux-Engine laeuft auf dem Host nicht, Integrationstests bleiben bis dahin CI-Sache; das GitHub-Remote `street1983nk/nextcloud-mcp-connector` existiert noch nicht, es gibt also noch keinen CI-Lauf und keinen Push.
- `BUDGET_BYTES` ist ein Startwert und muss in Plan 01-14 auf "gemessen plus 15 Prozent" fixiert werden, sonst ist das Gate dekorativ.

## Self-Check

Dateien (alle mit `[ -f ]` geprueft): pyproject.toml FOUND, uv.lock FOUND, .gitattributes FOUND, .github/workflows/ci.yml FOUND, src/mcp_connector/__init__.py FOUND, scripts/check_tool_budget.py FOUND, tests/conftest.py FOUND, tests/contract/test_tool_surface.py FOUND, tests/unit/test_project_layout.py FOUND, docs/dependency-audit.md FOUND.

Commits: e2cd14e FOUND, e341b90 FOUND, c651c39 FOUND.

Plan-Verifikation:
1. `uv sync` Exit 0, `uv run ruff check .` Exit 0, `uv run ruff format --check .` Exit 0 - PASS
2. `uv run pytest tests/unit -q` Exit 0 (7 passed), `uv run pytest tests/contract -q` Exit 2 mit `mcp_connector.server` in der Ausgabe - PASS
3. `docs/dependency-audit.md` enthaelt die `uv tree`-Ausgabe mit `httpx2 v2.10.0` unter `mcp[cli] v2.0.0` - PASS
4. Kein `print(` in `src/`, `.env.test` in `.gitignore`, keine Credentials in pyproject/CI - PASS
5. Budget-Gate: Exit 0 unter Budget, Exit 1 bei Ueberschreitung (gegen Stub-Server verifiziert) - PASS

## Self-Check: PASSED

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
