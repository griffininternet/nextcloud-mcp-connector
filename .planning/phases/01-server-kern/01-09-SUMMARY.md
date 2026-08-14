---
phase: 01-server-kern
plan: 09
subsystem: api
tags: [deck, httpx, respx, mcp, json-rest, graceful-degradation]

# Dependency graph
requires:
  - phase: 01-06
    provides: parse_app_json, capabilities.require_app, AppMissingError, ids.encode_card
provides:
  - Deck-REST-v1.0-Client mit Pflichtheadern und Deck-eigenem Fehlerformat
  - deck_browse als ein Tool mit Ebenen-Parameter (boards, stacks, cards)
  - deck_create_card als Create-only-Schreibpfad mit kanonischer langer Karten-Id
  - Ein-Request-Nachweis fuer die Kartenebene (Unit-Test und Integrationstest)
  - Vorab-Erklaerung bei fehlender Deck-App und fehlenden Board-Rechten
affects: [01-10-unified-search, 01-11-chatgpt-profil, 01-14-tool-surface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Tool mit Ebenen-Parameter statt eines Tools pro API-Ebene (D-06)"
    - "Literal-Typ im Registrierungsmodul erzeugt eine Enum-Beschraenkung im Input-Schema"
    - "Gleiche Antwort-Huelle fuer alle Ebenen: level, count, results, optional truncated"
    - "Lokale Guards vor dem Request: Titellaenge, ISO-Datum, numerische Pfad-Ids"

key-files:
  created:
    - src/mcp_connector/nextcloud/clients/deck.py
    - src/mcp_connector/tools/deck.py
    - src/mcp_connector/server/reg_deck.py
    - tests/fixtures/deck_boards.json
    - tests/fixtures/deck_stacks.json
    - tests/unit/test_deck_client.py
    - tests/unit/test_deck_tools.py
    - tests/integration/test_deck_roundtrip.py
  modified:
    - tests/contract/test_tool_surface.py
    - README.md

key-decisions:
  - "Deck-API-Version 1.0 statt 1.1: 1.1 bringt nur Attachment-Typen, 1.0 ist breiter kompatibel"
  - "canCreateBoards false beendet deck_create_card nicht sofort, sondern loest eine Pruefung der Board-Rechte aus; canCreateBoards regelt neue Boards, nicht Karten auf bestehenden Boards"
  - "Pfad-Ids muessen numerisch sein, sonst geht kein Request raus (T-01-63)"
  - "Archivierte und geloeschte Boards und Karten erscheinen nicht in browse; sie sind nicht adressierbarer Arbeitsvorrat"
  - "level ist ein Literal und damit eine Enum im Schema, keine freie Zeichenkette"

patterns-established:
  - "Ebenen-Navigation: ein Tool, ein Enum-Parameter, eine Antwort-Huelle"
  - "Ein-Request-Beweis als Test: respx zaehlt die Calls, der Integrationstest zaehlt sie live"
  - "Rechte-Vorabpruefung statt provoziertem 403, ohne dabei falsch negativ zu werden"

requirements-completed: [TOOL-04, SRV-04]

# Metrics
duration: 13 min
completed: 2026-08-14
---

# Phase 1 Plan 09: Deck-Vertikale Summary

**Deck-REST-v1.0-Client mit Pflichtheadern plus deck_browse (ein Tool, Enum-Ebenen, ein Request fuer alle Karten eines Boards) und create-only deck_create_card mit vorab erklaerten Rechtegrenzen**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-14T17:49:00Z
- **Completed:** 2026-08-14T18:02:00Z
- **Tasks:** 2 (beide TDD, RED und GREEN getrennt committet)
- **Files modified:** 10 (8 neu, 2 geaendert)

## Accomplishments

- **Deck-Client (D-18, Pitfall 9):** Jeder Request, auch ein GET, traegt `OCS-APIRequest: true` und `Content-Type: application/json`. Fehler werden ueber `parse_app_json` im Deck-Format `{"status": 4xx, "message": "..."}` gelesen, nie ueber den OCS-Envelope-Parser. Eine HTML-Loginseite wird als solche benannt statt als KeyError zu enden.
- **deck_browse (D-06):** Ein Tool mit `level` (`boards`, `stacks`, `cards`) statt drei Tools. `level="cards"` kostet genau einen HTTP-Request pro Board, weil `GET /boards/{id}/stacks` die Karten bereits mitliefert. Zwei Tests belegen das: einer gegen respx, einer gegen die echte Nextcloud 34.
- **deck_create_card:** Create-only. Es gibt in Client und Tool keinen PUT-, PATCH- oder DELETE-Pfad und keine Board- oder Stack-Anlage; ein Grep-Test haelt diese Grenze (T-01-62).
- **Graceful Degradation (SRV-04):** Fehlt die Deck-App, enden beide Tools an der Capabilities-Pruefung mit einem Satz plus Alternative und null Deck-Requests. Fehlen die Board-Rechte, wird das vorab erklaert, statt einen 403 zu provozieren.
- **Token-Budget:** `tools/list` liegt bei 8.277 Bytes fuer 12 Tools (Budget 24.000); `deck_browse` kostet 736 Bytes, `deck_create_card` 877 Bytes.

## Task Commits

1. **Task 1: Deck-Client mit Pflichtheadern und eigenem Fehlerformat**
   - `192d4db` (test) RED: 20 Faelle plus Fixtures
   - `b562855` (feat) GREEN: `clients/deck.py`
2. **Task 2: Tools deck_browse und deck_create_card**
   - `167e30e` (test) RED: 22 Tool-Faelle, 2 Contract-Faelle, 5 Integrationsfaelle
   - `8ad1ff0` (feat) GREEN: `tools/deck.py`, `server/reg_deck.py`
3. **Doku-Nachzug (Projektregel "Doku mitziehen"):** `8a941af` (docs) README-Abschnitt "Deck"

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/deck.py` - Deck REST v1.0: Boards, Board, Stacks inklusive Karten, eine Karte, Karte anlegen; Pflichtheader, lokale Guards, Deck-Fehlerformat
- `src/mcp_connector/tools/deck.py` - `browse()` mit Ebenen-Parameter und `create_card()`; Kartenabflachung ohne N+1, Rechte-Vorabpruefung, ID-Bildung ueber `ids.encode_card`
- `src/mcp_connector/server/reg_deck.py` - Registrierung: `deck_browse` (READ_ONLY), `deck_create_card` (CREATE_ONLY), `level` als `Literal`, beide `structured_output=False` und `@graceful`
- `tests/fixtures/deck_boards.json` - Zwei Boards, eines mit Schreibrecht, eines nur lesbar
- `tests/fixtures/deck_stacks.json` - Zwei Stacks mit drei Karten (eine ohne description, eine mit duedate, eine mit description null)
- `tests/unit/test_deck_client.py` - 20 Faelle: Header, Happy Path, Guards, 401, 403, 404, 429, HTML, Grep-Grenzen
- `tests/unit/test_deck_tools.py` - 22 Faelle: alle drei Ebenen, Ein-Request-Nachweis, fehlende Parameter, fehlende App, Rechtefaelle
- `tests/integration/test_deck_roundtrip.py` - 5 Faelle gegen Nextcloud 34: Capabilities, Karten-Roundtrip, Ein-Request-Nachweis live, gleiche Huelle auf allen Ebenen, unbekanntes Board
- `tests/contract/test_tool_surface.py` - Zwei neue Faelle: beide Deck-Tools mit ehrlichen Annotationen und Enum fuer `level`, plus Nachweis, dass es kein Tool pro Deck-Ebene gibt
- `README.md` - Abschnitt "Deck": Ebenen-Parameter, Ein-Request-Zusage, kanonische Karten-Id, Grenzen von `deck_create_card`

## Decisions Made

- **API-Version 1.0.** 1.1 gibt es seit Deck 1.3.0 und bringt nur Attachment-Typen. Fuer Boards, Stacks, Karten und das Anlegen einer Karte ist 1.0 funktional identisch und laeuft auf mehr Instanzen.
- **`Accept: application/json` als dritter Header.** Die Doku verlangt zwei Header; der dritte kostet nichts und verhindert, dass ein Proxy HTML aushandelt.
- **Antwort-Huelle fuer alle Ebenen gleich** (`level`, `count`, `results`, optional `truncated`). Das Modell lernt eine Form statt drei, und `truncated` macht das Abschneiden sichtbar statt still.
- **`can_edit` auf der Board-Ebene.** Das Modell sieht ohne Zusatzaufruf, auf welchem Board `deck_create_card` ueberhaupt Aussicht auf Erfolg hat.
- **Archivierte und geloeschte Objekte werden gefiltert.** Ein archiviertes Board ist kein Ziel fuer neue Karten, und eine geloeschte Karte ist kein Suchergebnis.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Numerische Pfad-Ids werden erzwungen**
- **Found during:** Task 1 (Deck-Client)
- **Issue:** `board_id`, `stack_id` und `card_id` stammen aus Modell-Eingaben und gehen unveraendert in den URL-Pfad. Der Plan verlangt keine Pruefung; das Bedrohungsregister verlangt in T-01-63 aber eine Mitigation gegen erratene und manipulierte Ids.
- **Fix:** `_path_id()` akzeptiert nur Ziffern und liefert sonst eine ToolError mit Hinweis, bevor ein Request entsteht.
- **Files modified:** `src/mcp_connector/nextcloud/clients/deck.py`
- **Verification:** `test_a_board_id_that_is_not_numeric_never_reaches_nextcloud` (respx zaehlt 0 Calls)
- **Committed in:** `b562855`

**2. [Rule 2 - Missing Critical] duedate wird vor dem Request als ISO-8601 geprueft**
- **Found during:** Task 1 (Deck-Client)
- **Issue:** Der Plan nennt "Datumsformat ISO-8601" als Vorgabe, aber keine Pruefung. Ein deutsches Datum wie `01.09.2026` haette einen 400 erzeugt, dessen Meldung dem Modell nicht sagt, welches Format erwartet wird.
- **Fix:** `check_duedate()` prueft mit `datetime.fromisoformat` und nennt im Hinweis ein gueltiges Beispiel.
- **Files modified:** `src/mcp_connector/nextcloud/clients/deck.py`
- **Verification:** `test_a_duedate_that_is_not_iso_8601_never_reaches_nextcloud`
- **Committed in:** `b562855`

**3. [Rule 1 - Bug] canCreateBoards allein wuerde deck_create_card falsch negativ machen**
- **Found during:** Task 2 (Tools)
- **Issue:** Der Plan verlangt, bei `canCreateBoards=false` vorab abzulehnen. Diese Capability regelt in Deck aber nur das Anlegen **neuer Boards** (Gruppenbeschraenkung der Instanz). Ein Nutzer mit `canCreateBoards=false` kann sehr wohl Schreibrechte auf einem geteilten Board haben. Die woertliche Umsetzung haette diesen legitimen Fall dauerhaft blockiert, ohne dass Nextcloud je widersprochen haette.
- **Fix:** Bei `canCreateBoards=false` prueft `_require_write_permission()` die Rechte des konkreten Boards (`PERMISSION_EDIT`) mit einem `GET /boards`. Nur ein wirklich nicht beschreibbares oder unbekanntes Board beendet den Aufruf, und zwar mit einer Meldung, die Board und Grund nennt. Die Plan-Zusage "erklaert das vorab, statt einen 403 zu provozieren" bleibt damit erfuellt, der Fehlalarm entfaellt.
- **Files modified:** `src/mcp_connector/tools/deck.py`
- **Verification:** `test_a_user_without_board_rights_is_told_before_the_post` (0 POSTs) und `test_a_restricted_user_may_still_write_to_a_board_that_grants_it`
- **Committed in:** `8ad1ff0`

**4. [Rule 2 - Missing Critical] Karten ohne Id oder ohne Stack werden uebersprungen**
- **Found during:** Task 2 (Tools)
- **Issue:** Eine Karte ohne `id` oder ohne zuordenbaren Stack liesse sich nicht wieder adressieren; eine geratene Id wuerde auf eine fremde Karte zeigen.
- **Fix:** Solche Eintraege werden ausgelassen statt geraten (dieselbe Linie wie bei `notes_search`).
- **Files modified:** `src/mcp_connector/tools/deck.py`
- **Verification:** `uv run pyright` (0 Fehler) plus die Kartenebenen-Tests
- **Committed in:** `8ad1ff0`

**5. [Rule 2 - Doku-Regel] README-Abschnitt "Deck" nachgezogen**
- **Found during:** Nach Task 2
- **Issue:** Projektregel "Doku mitziehen": Verhaltensaenderungen gehoeren in die Doku. Der Plan listet die README nicht in `files_modified`, die Tool-Tabelle nannte Deck aber nur in einer Zeile.
- **Fix:** Abschnitt mit Beispielantwort, Ein-Request-Zusage, Id-Format und den Grenzen von `deck_create_card`.
- **Files modified:** `README.md`
- **Verification:** `uv run ruff format --check .` gruen (Markdown-Codebloecke), Sichtpruefung
- **Committed in:** `8a941af`

---

**Total deviations:** 5 auto-fixed (3 fehlende kritische Funktionalitaet, 1 Korrektheitsfehler der Plan-Vorgabe, 1 Doku-Regel)
**Impact on plan:** Kein Scope-Zuwachs. Vier Abweichungen sind Guards und Filter innerhalb der geplanten Funktionen, eine korrigiert eine Plan-Vorgabe, die legitime Nutzung blockiert haette. Alle Plan-Akzeptanzkriterien bleiben erfuellt.

## Checkpoints

Der Plan ist `autonomous: true` und enthaelt keine Checkpoints. Es wurde keiner ausgeloest und keiner auto-genehmigt.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run pytest -q` (Default: unit, contract, compat) | 412 gruen, 41 deselektiert (integration, matrix) |
| `uv run pytest tests/unit/test_deck_client.py -q` | 20 gruen (Akzeptanz: mindestens 8) |
| `uv run pytest tests/unit/test_deck_tools.py -q` | 22 gruen (Akzeptanz: mindestens 8) |
| `uv run pytest -m integration -q` (Nextcloud 34, Deck 1.18.3) | 33 gruen, davon 5 neu |
| `uv run pytest -m matrix -q` | 8 gruen (SDK 1.29 und 2.x gegen denselben Endpoint) |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 8.277 von 24.000 Bytes, 12 Tools |
| `uv run pyright` | 0 Fehler, 0 Warnungen |
| `uv run vulture src scripts --min-confidence 80` | leer |
| `uv run ruff check .` / `ruff format --check .` | sauber, 72 Dateien formatiert |

**N+1-Beweis:** `test_browse_cards_needs_exactly_one_http_request` (respx: 1 Call auf `/boards/2/stacks`, 0 weitere Deck-Calls) und live `test_the_card_level_stays_one_request_against_a_real_instance` (gezaehlte Deck-Requests auf der echten Instanz: 1).

**Graceful Degradation:** `test_a_missing_deck_app_stops_both_tools_before_the_first_request` (drei Varianten, jeweils 0 Deck-Requests, Meldung "The Deck app is not installed on this Nextcloud.") und die beiden Rechte-Faelle aus Abweichung 3.

## Issues Encountered

- **pyright meldete `Unknown | Any | None` bei der Karten-Id-Bildung.** Ursache: `stack.get("id")` kann `None` sein. Behoben durch das explizite Ueberspringen solcher Karten (Abweichung 4), also ohne `type: ignore`.
- **Die Test-Nextcloud lief nicht mehr.** `docker compose -f compose.test.yml up -d --wait` gestartet, Volume und `.env.test` aus dem Bootstrap waren unveraendert gueltig, Deck 1.18.3 und Notes 6.0.1 weiterhin installiert.
- Sonst keine. Beide TDD-Zyklen liefen ohne Nachbesserung durch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Die vierte Vertikale steht; `fetch` (Plan 11) kann Karten ueber die kanonische lange Id `card:<board>:<stack>:<card>` direkt aufloesen, ohne Sweep.
- Fuer die kurze Id-Form `card:<cardId>` aus dem Unified-Search-Provider `search-deck-card-board` bleibt der Sweep `GET /boards` plus `GET /boards/{id}/stacks` der verifizierte Weg; `get_boards` und `get_stacks` liegen dafuer bereit, `get_card` fuer die lange Form.
- Offen fuer Plan 14: die Gesamtzahl der Tools (aktuell 12 von 15) und die Neufestlegung des Byte-Budgets auf "gemessen plus 15 Prozent".

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*

## Self-Check: PASSED

- Alle 8 als `created` gelisteten Dateien liegen auf der Platte (`[ -f ]` je Datei).
- Alle 5 Commit-Hashes sind in `git log --oneline --all` auffindbar (`192d4db`, `b562855`, `167e30e`, `8ad1ff0`, `8a941af`).
- Alle Akzeptanzkriterien beider Tasks wurden nach Abschluss erneut ausgefuehrt und sind gruen (siehe Verification).
