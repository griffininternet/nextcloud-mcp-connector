---
phase: 01-server-kern
plan: 06
subsystem: api
tags: [ocs, nextcloud-notes, unified-search, graceful-degradation, respx, mcp]

# Dependency graph
requires:
  - phase: 01-02
    provides: httpx-Pool pro Event-Loop, Credentials, ToolError/AppMissingError, ids.py, Server-Layer mit READ_ONLY/CREATE_ONLY/graceful
  - phase: 01-03
    provides: compose.test.yml und bootstrap_test_nc.sh (Notes-App und Testnutzer)
  - phase: 01-04
    provides: entry_http mit Transport-Hardening, Credential-Passthrough pro Request
provides:
  - OCS-Grundschicht mit den beiden Pflichtheadern (D-18) und getrennten Parsern parse_ocs/parse_app_json
  - App-Erkennung fuer Notes und Deck ueber /cloud/capabilities mit 60-Sekunden-Cache
  - Graceful Degradation mit exaktem Fehlertext bei fehlender App (SRV-04, D-15)
  - notes_search, notes_read, notes_create (D-05, TOOL-03)
  - Live-Nachweis AUTH-01: echter Tool-Aufruf ueber HTTP mit App-Passwort gegen die Docker-Nextcloud
affects: [01-07-kalender, 01-08-kontakte, 01-09-deck, 01-10-unified-search, 01-11-chatgpt-profil, 01-14-tool-set]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Response-Parser: parse_ocs fuer /ocs/v2.php, parse_app_json fuer Notes und Deck (Pitfall 9)"
    - "Capabilities-Cache mit kurzer TTL pro (base_url, user), reine Latenz-Optimierung ohne Korrektheitsanspruch (D-20)"
    - "require_app vor dem ersten App-Request: eine fehlende App erzeugt null Requests"
    - "IDs aus resourceUrl parsen, unbrauchbare Treffer ueberspringen statt raten"
    - "Zurueckgegebene URLs immer aus der konfigurierten Basis-URL neu bauen (SSRF-Grenze)"

key-files:
  created:
    - src/mcp_connector/nextcloud/clients/ocs.py
    - src/mcp_connector/nextcloud/capabilities.py
    - src/mcp_connector/nextcloud/clients/notes.py
    - src/mcp_connector/tools/notes.py
    - src/mcp_connector/server/reg_notes.py
    - tests/fixtures/ocs_capabilities.json
    - tests/fixtures/ocs_search_notes.json
    - tests/unit/test_ocs_capabilities.py
    - tests/unit/test_notes_tools.py
    - tests/integration/test_notes_roundtrip.py
    - tests/integration/test_http_tool_call.py
  modified:
    - tests/contract/test_tool_surface.py
    - README.md

key-decisions:
  - "notes_search laeuft ueber den Unified-Search-Provider notes; die Notes-REST-API hat keine Search-Route, der Listen-Fallback bleibt dokumentiert und ist nicht der Default"
  - "Notiz-IDs kommen aus resourceUrl; ein Treffer ohne numerisches letztes Segment wird uebersprungen statt geraten (T-01-40)"
  - "Die zurueckgegebene url wird immer aus der konfigurierten Basis-URL gebaut, nie aus resourceUrl uebernommen (T-01-39)"
  - "Der Capabilities-Cache haelt 60 Sekunden pro (base_url, user) und enthaelt keine Credentials; ein leerer Cache aendert nie ein Ergebnis"
  - "Notes-REST-Aufrufe tragen zusaetzlich OCS-APIRequest: true, damit ein nicht authentifizierter Aufruf 401 statt einer HTML-Loginseite liefert"
  - "507 behaelt seine eigene Meldung (Speicher voll) und faellt nicht in den generischen 5xx-Zweig"
  - "notes_create meldet renamed=true, wenn der Server den Titel sanitisiert oder numeriert hat; der Servertitel ist die Wahrheit"
  - "notes_read akzeptiert note:12 und die nackte 12, lehnt aber jede fremde ID-Art ab"
  - "capabilities.py prueft nur Notes und Deck; Kalender und Kontakte brauchen keine App, dort ist die richtige Pruefung 'existiert eine Collection'"

patterns-established:
  - "Pattern: jede optionale App wird vor dem ersten Request per require_app geprueft"
  - "Pattern: Fehlertexte nennen die App und eine Alternative, nie einen Stacktrace"
  - "Pattern: Integrationsnachweis pro Vertikale als eigener Roundtrip-Test mit Marker integration"

requirements-completed: [TOOL-03, SRV-04, AUTH-01]

# Metrics
duration: 27 min
completed: 2026-08-14
---

# Phase 1 Plan 06: OCS-Grundschicht und Notes-Vertikale Summary

**OCS-Client mit Pflichtheadern und getrennten Parsern, App-Erkennung mit 60-Sekunden-Cache und die drei Notes-Tools ueber den Unified-Search-Provider, inklusive live bewiesener Graceful Degradation und AUTH-01-Nachweis ueber HTTP**

## Performance

- **Duration:** 27 min
- **Started:** 2026-08-14T16:18:00Z
- **Completed:** 2026-08-14T16:45:00Z
- **Tasks:** 2 (TDD, je RED und GREEN)
- **Files modified:** 13 (11 neu, 2 geaendert)

## Accomplishments

- OCS-Grundschicht: `OCS-APIRequest: true` und `Accept: application/json` auf jedem Request (D-18), Basic-Auth pro Request, kein Redirect-Following, kein Auth-Retry
- Zwei getrennte Parser: `parse_ocs` fuer den OCS-Envelope, `parse_app_json` fuer Notes und Deck; eine HTML-Loginseite erzeugt einen erklaerenden Fehler statt eines KeyError (Pitfall 9)
- App-Erkennung ueber einen einzigen `/cloud/capabilities`-Roundtrip inklusive `canCreateBoards`, mit 60-Sekunden-TTL pro Credential-Kontext
- Drei Notes-Tools: `notes_search` (ein Request fuer alle Treffer, kein N+1), `notes_read`, `notes_create`; `tools/list` bleibt statisch
- Graceful Degradation gegen eine echte Nextcloud bewiesen: bei deaktivierter Notes-App antworten alle drei Tools mit "The Notes app is not installed on this Nextcloud." plus Hinweis, ohne einen einzigen Notes-Request
- AUTH-01 nachgewiesen: uvicorn-Subprozess ohne Nextcloud-Konto im Environment, Notiz per HTTP mit dem App-Passwort aus dem Request angelegt und wieder gelesen

## Task Commits

1. **Task 1: OCS-Client und App-Erkennung** - `809a205` (test, RED), `636ba33` (feat, GREEN)
2. **Task 2: Notes-Client und die drei Notes-Tools** - `01b9712` (test, RED), `e78db77` (feat, GREEN), `f09ba4c` (test, AUTH-01-Nachweis)
3. **Doku** - `5ab9bb7` (docs, README)

**Plan metadata:** siehe letzter `docs(01-06)`-Commit

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/ocs.py` - OCS-URL-Bau, Pflichtheader, `parse_ocs`, `parse_app_json`, zentrales Status-Mapping
- `src/mcp_connector/nextcloud/capabilities.py` - `Capabilities`, `load`, `require_app`, `app_missing`, `clear_cache`, TTL-Cache
- `src/mcp_connector/nextcloud/clients/notes.py` - Notes REST v1: `list_notes`, `get_note`, `create_note`, `check_api_version` (A5), kein Update, kein Delete
- `src/mcp_connector/tools/notes.py` - `search`, `read`, `create` inklusive ID-Parsing aus `resourceUrl` und dokumentiertem Fallback
- `src/mcp_connector/server/reg_notes.py` - Registrierung der drei Tools mit READ_ONLY bzw. CREATE_ONLY, `structured_output=False`, `@graceful`
- `tests/fixtures/ocs_capabilities.json` - Capabilities-Antwort einer Nextcloud 34 mit Notes und Deck
- `tests/fixtures/ocs_search_notes.json` - Unified-Search-Antwort des Notes-Providers
- `tests/unit/test_ocs_capabilities.py` - 18 Faelle: Header, Fixture, fehlende Schluessel, HTML, 401, 5xx, Redirect, TTL, Cache-Key, Fehlertexte
- `tests/unit/test_notes_tools.py` - 17 Faelle: Happy, leer, leerer Term, kaputte resourceUrl, fremder Host, 404, 507, App fehlt (3x), API-Version, 5xx, Titel-Wahrheit
- `tests/integration/test_notes_roundtrip.py` - Anlegen, Suchen, Lesen und Titel-Kollision gegen die Docker-Nextcloud
- `tests/integration/test_http_tool_call.py` - AUTH-01: echter Tool-Aufruf ueber Streamable HTTP mit App-Passwort
- `tests/contract/test_tool_surface.py` - erweitert um die Annotationen der drei Notes-Tools
- `README.md` - `notes_search` korrekt beschrieben, Abschnitt zu optionalen Apps

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei wichtigsten:

- Die Suche laeuft ueber `/ocs/v2.php/search/providers/notes/search`, weil die Notes-REST-API keine Search-Route hat. Titel und Excerpt kommen aus dem Search-Entry, also ein Request statt einem pro Treffer.
- Ein Treffer ohne verwertbare `resourceUrl` wird uebersprungen. Eine geratene ID wuerde eine andere Notiz aufloesen, und das ist schlimmer als ein fehlender Treffer.
- `tools/list` bleibt statisch. Die ehrliche Fehlermeldung ersetzt das dynamische Ausblenden von Tools; das haelt das Listing cachebar und die Token-Budget-Messung gueltig.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 507 verschwand im generischen 5xx-Zweig**
- **Found during:** Task 2 (Notes-Tools)
- **Issue:** `_check_transport` behandelte jeden Status ab 500 als Serverfehler, also auch 507. Beim Anlegen einer Notiz auf einem vollen Konto haette das Modell "Serverfehler, spaeter erneut versuchen" gelesen statt "Speicher voll, Quota freigeben".
- **Fix:** 507 ist im Transport-Zweig ausgenommen und laeuft in das Status-Mapping, das die eigene Meldung samt Quota-Hinweis erzeugt.
- **Files modified:** src/mcp_connector/nextcloud/clients/ocs.py
- **Verification:** `test_create_reports_a_full_nextcloud_with_its_own_message` gruen
- **Committed in:** `e78db77`

**2. [Rule 2 - Missing Critical] Contract-Test fuer die drei Notes-Tools**
- **Found during:** Task 2
- **Issue:** Das Akzeptanzkriterium verlangt den Nachweis der Annotationen in `tools/list`, die Dateiliste des Plans nennt `tests/contract/test_tool_surface.py` aber nicht.
- **Fix:** Contract-Test ergaenzt: Namen vorhanden, `read_only_hint` bei den Lesetools, `read_only_hint=False` plus `destructive_hint=False` plus `idempotent_hint=False` bei `notes_create`, `output_schema is None` bei allen dreien.
- **Files modified:** tests/contract/test_tool_surface.py
- **Verification:** `uv run pytest tests/contract -q` gruen
- **Committed in:** `01b9712` (RED) und danach gruen mit `e78db77`

**3. [Rule 2 - Missing Critical] AUTH-01-Nachweis ueber HTTP**
- **Found during:** Nach Task 2, ausdruecklich vom Orchestrator angefragt (offener Punkt aus 01-04)
- **Issue:** Basic-Passthrough und Static Bearer waren nur unit-getestet; der Rundlauf mit echtem App-Passwort gegen eine laufende Nextcloud fehlte.
- **Fix:** `tests/integration/test_http_tool_call.py` startet uvicorn ohne `NC_MCP_USER` und ohne `NC_MCP_APP_PASSWORD`, legt per `notes_create` eine Notiz an und liest sie zurueck; dazu ein falsches App-Passwort und ein Request ohne Header.
- **Files modified:** tests/integration/test_http_tool_call.py
- **Verification:** drei Tests gruen gegen die Docker-Nextcloud
- **Committed in:** `f09ba4c`

**4. [Rule 1 - Bug] README beschrieb notes_search falsch**
- **Found during:** Doku-Durchsicht am Ende
- **Issue:** Die Tool-Tabelle sagte "Find notes by title and category". Die Suche laeuft ueber den Provider und matcht Titel und Inhalt, nicht die Kategorie.
- **Fix:** Zeile korrigiert, Abschnitt "Optional apps" ergaenzt.
- **Files modified:** README.md
- **Committed in:** `5ab9bb7`

---

**Total deviations:** 4 auto-fixed (2 Bugs, 2 fehlende kritische Nachweise)
**Impact on plan:** Kein Scope-Zuwachs ueber den Plan hinaus. Der AUTH-01-Nachweis war vom Orchestrator freigegeben und schliesst einen offenen Punkt aus 01-04.

## Issues Encountered

- **Nextcloud meldet eine deaktivierte App verzoegert.** Nach `occ app:disable notes` lieferte `/cloud/capabilities` weiterhin `notes`, und die Suche auf den bereits entfernten Provider antwortete mit 500 statt 404. Ursache ist der App-Cache der Nextcloud selbst (die occ-CLI teilt ihn nicht mit den Webprozessen), nicht unser 60-Sekunden-Cache. Erst ein Container-Neustart machte die Aenderung sichtbar, danach war der Pfad exakt wie erwartet. Fuer kuenftige Degradations-Tests gilt: App deaktivieren, Container neu starten, dann pruefen.
- **respx-Guard-Routen und `assert_all_called=True` vertragen sich nicht.** Eine Route, die absichtlich nie feuert (der Nachweis "kein Notes-Request"), laesst den Kontextmanager scheitern. Diese Tests laufen mit `assert_all_called=False` und pruefen die Call-Counts explizit.

## User Setup Required

None - no external service configuration required. Die Integrationstests brauchen die lokale Docker-Nextcloud (`compose.test.yml` plus `scripts/bootstrap_test_nc.sh`), die seit 01-03 existiert.

## Next Phase Readiness

- Die OCS-Schicht steht fuer Plan 01-09 (Deck, gleiches Fehlerformat, `canCreateBoards` schon vorhanden) und Plan 01-10 (Unified Search, `ocs_get` plus `parse_ocs` sind wiederverwendbar).
- `capabilities.require_app` ist der Einstiegspunkt fuer jede weitere optionale App. Fuer Kalender und Kontakte gilt er ausdruecklich nicht; dort ist die Pruefung "existiert eine Collection" (Plan 01-07 und 01-08).
- Annahme A5 bestaetigt: die Test-Nextcloud 34.0.2 meldet Notes 6.0.1 mit `api_version` `["0.2", "1.3", "1.4"]`, die v1-Linie lebt.
- Offen bleibt der Token-Budget-Fixwert (Plan 01-14): `tools/list` liegt aktuell bei 2626 Bytes fuer 5 Tools, Budget 24000.

## Self-Check: PASSED

- Alle 11 in `key-files.created` genannten Dateien existieren auf der Platte
- Alle 6 Commit-Hashes sind in `git log` auffindbar
- `uv run pytest -q` gruen (204 Tests, ohne Docker), `uv run pytest -m integration -q` gruen (11 Tests gegen Nextcloud 34.0.2)
- `uv run ruff check .` und `uv run ruff format --check .` sauber
- `uv run python scripts/check_tool_budget.py` Exit-Code 0

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
