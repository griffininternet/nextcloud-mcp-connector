---
phase: 01-server-kern
plan: 05
subsystem: api
tags: [webdav, search, propfind, lxml, pagination, mcp, httpx, respx]

# Dependency graph
requires:
  - phase: 01-server-kern (Plan 02)
    provides: DAV-Client-Grundlage, gehaerteter XML-Parser, Credential-Objekt
  - phase: 01-server-kern (Plan 03)
    provides: files_read und files_upload, safe_path, ids.encode_file, NcClients
provides:
  - files_search (WebDAV SEARCH basicsearch) mit ehrlicher Erwartungssteuerung
  - files_list (PROPFIND Depth 1) ohne den Ordner selbst
  - paging.py, das zustandslose Cursor-Handle-Modul fuer alle Listen-Tools
  - dav.search, dav.propfind_children, dav.search_scope, dav.parse_entries
  - Zwei echte 207-Fixtures fuer SEARCH und PROPFIND Depth 1
affects: [01-09-deck, 01-10-unified-search, 01-11-chatgpt-search-fetch, 01-14-tool-surface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pattern 4 (Research): zustandslose Pagination ueber base64url-Handles, hier zum ersten Mal implementiert"
    - "Limit-Deckelung statt Ablehnung: eine unbrauchbare Zahl kostet keinen Roundtrip"
    - "Leere Felder werden aus der Antwort weggelassen, jeder Key wird in jedem Treffer bezahlt"

key-files:
  created:
    - src/mcp_connector/paging.py
    - tests/fixtures/webdav_search_207.xml
    - tests/fixtures/webdav_propfind_207.xml
    - tests/unit/test_paging.py
    - tests/unit/test_dav_search.py
    - tests/unit/test_files_search.py
    - tests/unit/test_files_list.py
    - tests/integration/test_files_browse.py
  modified:
    - src/mcp_connector/nextcloud/clients/dav.py
    - src/mcp_connector/tools/files.py
    - src/mcp_connector/server/reg_files.py
    - tests/contract/test_tool_surface.py
    - README.md

key-decisions:
  - "Cursor-Handles bleiben unsigniert: sie tragen kein Geheimnis und keine Autoritaet, die Credentials kommen weiterhin pro Aufruf aus dem Auth-Kanal"
  - "Ein Handle aus einer anderen Suche wird abgelehnt statt still auf die falsche Seite angewendet"
  - "files_search behaelt die Serverreihenfolge; nachsortieren wuerde bei Offset-Paging Treffer doppeln"
  - "files_list sortiert selbst (Ordner zuerst, dann Namen), weil die Seiten aus einer vollstaendigen Antwort geschnitten werden"
  - "propfind_children erkennt den Ordner selbst am Pfad statt an der Position und liefert ihn mit zurueck, damit ein Dateipfad ohne zweiten Request erklaert werden kann"
  - "Das note-Feld zur Namenssuche steht in JEDER Suchantwort, nicht nur bei null Treffern"

patterns-established:
  - "paging.encode_cursor / decode_cursor / read_offset / check_scope als einziger Ort fuer Fortsetzungs-Handles"
  - "dav.parse_entries verwirft jeden href ausserhalb des Home des Nutzers (auch aehnlich benannte Konten)"

requirements-completed: [TOOL-01, SRV-03, SRV-05]

# Metrics
duration: 16 min
completed: 2026-08-14
---

# Phase 1 Plan 05: Datei-Suche und Ordner-Listing Summary

**files_search (WebDAV basicsearch mit lxml-gebautem Body und explizitem d:limit) und files_list (PROPFIND Depth 1 ohne den Ordner selbst), beide mit zustandslosen base64url-Cursor-Handles, die prozessuebergreifend weiterlesen.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-08-14T17:34:00Z
- **Completed:** 2026-08-14T17:50:00Z
- **Tasks:** 2 (beide TDD, je RED und GREEN)
- **Files modified:** 13 (8 neu, 5 geaendert)

## Accomplishments

- Die vier Datei-Tools sind vollstaendig (D-03): suchen, listen, lesen, anlegen.
- `paging.py` liefert das Handle-Muster fuer alle spaeteren Listen-Tools (D-20, SRV-05), bewiesen prozessuebergreifend: PID 8064 gibt `eyJmIjoiLyIsIm8iOjIsInEiOiJtY3AtYnJvd3NlIn0` aus, PID 12036 liest damit korrekt weiter, ohne jeden Server-State.
- Pitfall 5 ist nicht nur dokumentiert, sondern gegen die echte Nextcloud 34 verifiziert: ein Wort, das nur im Dateiinhalt steht, liefert keinen Treffer, und jede Antwort sagt das mit `note: "matched on names only; contents are not indexed"`.
- XML-Injection ueber Suchbegriffe ist konstruktiv ausgeschlossen (T-01-30): der basicsearch-Body entsteht ausschliesslich per `etree.SubElement`, ein Grep-Test haelt jeden String-Aufbau aus `dav.py` heraus.
- Token-Budget bleibt weit im Rahmen: `tools/list` waechst auf 6662 Bytes bei 10 Tools (Budget 24000).

## Task Commits

1. **Task 1: Cursor-Handles und DAV-SEARCH-/PROPFIND-Schicht** - `b22e395` (test, RED), `511b285` (feat, GREEN)
2. **Task 2: Tools files_search und files_list** - `8914fdd` (test, RED), `89b4c90` (feat, GREEN)

**Dokumentation:** `648524a` (docs: README-Abschnitte zu Namenssuche und Handles)
**Plan metadata:** siehe letzter Commit dieses Plans (docs(01-05))

## Files Created/Modified

- `src/mcp_connector/paging.py` - Unsignierte base64url-Handles, defensives Dekodieren, `read_offset` und `check_scope`
- `src/mcp_connector/nextcloud/clients/dav.py` - `search_scope`, `build_search_body`, `search`, `propfind_children`, `parse_entries`, Property-Sets fuer Suche und Listing
- `src/mcp_connector/tools/files.py` - `search` und `list_dir` samt Limit-Deckelung, Paging und `_as_item`-Projektion
- `src/mcp_connector/server/reg_files.py` - Registrierung von `files_search` und `files_list` (READ_ONLY, `structured_output=False`)
- `tests/fixtures/webdav_search_207.xml` - Echte SEARCH-Antwort inklusive Sonderzeichen im Namen und 404-propstat
- `tests/fixtures/webdav_propfind_207.xml` - Echte Depth-1-Antwort, Ordner zuerst, drei Kinder
- `tests/unit/test_paging.py` - 13 Tests: Roundtrip, url-sicheres Alphabet, Sonderzeichen, sechs ungueltige Handles, Groessengrenze
- `tests/unit/test_dav_search.py` - Escaping, genau ein `d:limit`, DAV-Wurzel als Endpoint, Scope-Bau, Fixture-Mapping, fremdes Home, Depth-1-Verhalten
- `tests/unit/test_files_search.py` - Happy, leer, Scope, Limit-Deckelung, Cursor-Fortsetzung, letzte Seite, ungueltiger und fremder Cursor, 403, 5xx, Traversal
- `tests/unit/test_files_list.py` - Kinder ohne Ordner, Wurzel, leerer Ordner, Dateipfad, Paging ueber drei Seiten, 404, 403, 5xx, Traversal
- `tests/integration/test_files_browse.py` - Fund per Name, Miss per Inhalt, Handle-Fortsetzung, Dateipfad, unbekannter Ordner (5 Tests, gruen gegen Nextcloud 34)
- `tests/contract/test_tool_surface.py` - Vier `files_`-Tools, Annotationen, kein Output-Schema, "not file contents" in der Description
- `README.md` - Abschnitte "Files: what the search actually matches" und "Long lists: cursor handles instead of sessions"

## Decisions Made

- **Handle unsigniert.** Es enthaelt Offset, Suchbegriff und Ordner, sonst nichts. Eine Signatur wuerde eine Zusicherung suggerieren, die der Auth-Kanal ohnehin gibt; ein manipuliertes Handle kann nur die eigenen Daten anders blaettern (T-01-33).
- **Fremdes Handle wird abgelehnt.** `check_scope` vergleicht Suchbegriff und Ordner; sonst waere eine Fortsetzung mit falschem Kontext eine stille falsche Antwort.
- **Serverreihenfolge bei der Suche, Eigen-Sortierung beim Listing.** WebDAV SEARCH kennt `nresults`, aber keinen Offset: Folgeseiten entstehen durch groesseres Limit plus Slice, deshalb darf die Reihenfolge nicht nachtraeglich veraendert werden. Beim Listing kommt der ganze Ordner in einer Antwort, dort ist eine stabile Sortierung (Ordner zuerst, dann Name) die Voraussetzung fuer schnittfeste Seiten.
- **`propfind_children` gibt den Ordner selbst zurueck.** Depth 1 auf eine Datei antwortet mit genau dieser Datei; ohne das Zielobjekt saehe das wie ein leerer Ordner aus. So kostet die Erklaerung "das ist eine Datei, nimm files_read" keinen zweiten Request.
- **Ordner-Erkennung per Pfadvergleich statt per Position.** Der Plan sagt "ersten d:response ueberspringen"; der Pfadvergleich erfuellt dasselbe Kriterium und haengt nicht an einer Reihenfolge, die das Protokoll nicht zusichert.
- **`MAX_SEARCH_FETCH = 500`** deckelt den Trick "mehr holen und schneiden", damit Seite vierzig keinen unbegrenzten Request erzeugt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Zusaetzliche Testdatei tests/unit/test_dav_search.py**
- **Found during:** Task 1
- **Issue:** Der Plan listet fuer Task 1 nur `tests/unit/test_paging.py`, verlangt in den Acceptance Criteria aber Unit-Nachweise fuer Escaping, `d:limit`, den SEARCH-Endpoint und das Ueberspringen des Ordners. Diese Tests gehoeren nicht in ein Paging-Testmodul.
- **Fix:** Eigene Datei `tests/unit/test_dav_search.py` mit 16 Tests fuer die DAV-Schicht angelegt.
- **Files modified:** tests/unit/test_dav_search.py
- **Verification:** `uv run pytest tests/unit -q` gruen; alle fuenf Acceptance Criteria von Task 1 belegt.
- **Committed in:** b22e395 (RED), gruen mit 511b285

**2. [Rule 2 - Missing Critical] parse_entries verwirft hrefs ausserhalb des Home**
- **Found during:** Task 1
- **Issue:** Ein Praefixvergleich auf `/remote.php/dav/files/alice` trifft auch `/remote.php/dav/files/alicexyz`, also ein fremdes Konto. Der Plan verlangt das nicht ausdruecklich, es ist aber genau die Grenze aus T-01-32.
- **Fix:** `_home_path_of` verlangt nach dem Home-Praefix entweder Ende oder `/`; alles andere wird uebersprungen.
- **Files modified:** src/mcp_connector/nextcloud/clients/dav.py
- **Verification:** `test_search_drops_hrefs_outside_the_users_home`
- **Committed in:** 511b285

**3. [Rule 2 - Missing Critical] Ablehnung eines Handles aus einer fremden Suche**
- **Found during:** Task 2
- **Issue:** Der Plan beschreibt nur "dasselbe Handle setzt korrekt fort". Ein Handle mit `q: "invoice"`, angewendet auf eine Suche nach "budget", haette still die falsche Seite geliefert.
- **Fix:** `paging.check_scope` prueft Suchbegriff und Ordner beziehungsweise den Listing-Pfad und wirft sonst einen ToolError mit Hinweis.
- **Files modified:** src/mcp_connector/paging.py, src/mcp_connector/tools/files.py
- **Verification:** `test_a_cursor_from_another_query_is_refused`, `test_a_cursor_from_another_folder_is_refused`
- **Committed in:** 89b4c90

**4. [Konvention] README-Abschnitte ergaenzt**
- **Found during:** Nach Task 2
- **Issue:** Projektregel "Doku-Seite mitziehen": die Tool-Tabelle beschrieb `files_search` als Suche "by name and metadata", was mehr verspricht als das Tool kann.
- **Fix:** Tabellenzeilen korrigiert, zwei Abschnitte zu Namenssuche und Cursor-Handles ergaenzt.
- **Files modified:** README.md
- **Committed in:** 648524a

---

**Total deviations:** 4 (3 Rule 2, 1 Konvention)
**Impact on plan:** Kein Scope-Zuwachs an Funktionen. Drei Ergaenzungen schliessen Luecken, die der Plan implizit voraussetzt (Testnachweis, Kontogrenze, Cursor-Verwechslung), die vierte haelt die Doku ehrlich.

## Abweichung vom Plan-Wortlaut (bewusst)

- Plan: "erster d:response wird uebersprungen". Umgesetzt als Pfadvergleich (siehe Decisions). Das Acceptance Criterion "PROPFIND Depth 1 ueberspringt den Ordner selbst (Test gegen die Fixture)" ist erfuellt.
- Plan-Signatur: `search(clients, query, folder="/", limit=25, cursor=None)` und `list_dir(clients, path="/", limit=100, cursor=None)` wurden exakt so umgesetzt. Auf der MCP-Oberflaeche ist `cursor` ein `str` mit Default `""` statt `str | None`, weil ein Optional im Input-Schema ein `anyOf` erzeugt (Schema-Diaet, D-14); die Registrierung uebersetzt `""` nach `None`.

## Issues Encountered

- PROPFIND auf das Home des Nutzers geht an `.../files/alice/` mit Schraegstrich am Ende (Ergebnis von `files_url` mit Pfad `/`). Zwei Unit-Tests hatten die URL ohne Schraegstrich gemockt und liefen auf `AllMockedAssertionError`. Tests korrigiert, Produktionscode unveraendert; das reale Verhalten ist durch den Integrationstest `test_listing_the_root_folder_works`-Gegenstueck (`test_an_uploaded_file_is_found_by_name_and_listed`) gegen Nextcloud 34 gedeckt.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run pytest -q` | 368 passed, 36 deselected |
| `uv run pytest -m integration -q` (Docker NC 34) | 28 passed, davon 5 neu |
| `uv run python scripts/check_tool_budget.py` | 6662 Bytes, 10 Tools, Budget 24000, Exit 0 |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 66 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src scripts --min-confidence 80` | leer |
| `grep -v '^\s*#' dav.py \| grep '<d:'` | kein Treffer |
| Cursor-Handle prozessuebergreifend | PID 8064 erzeugt, PID 12036 liest weiter, korrekte Folgeseite |

## Known Stubs

Keine. Beide Tools sind vollstaendig verdrahtet und laufen gegen eine echte Nextcloud.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Die Datei-Vertikale ist komplett; `paging.py` steht als Muster fuer `deck_browse`, `unified_search` und die ChatGPT-Tools bereit.
- Offen laut Plan-Reihenfolge: 01-09 (Deck), 01-10 (Unified Search), 01-11 (search/fetch), 01-13, 01-14 (Tool-Surface-Gesamttest, Budget-Fixierung).
- TOOL-01, SRV-03 und SRV-05 sind auf Tool-Ebene belegt; der Gesamtnachweis ueber alle 15 Tools bleibt Plan 01-14.

## Requirements

- **TOOL-01: Complete.** Suchen, Listen, Lesen und Anlegen laufen gegen Nextcloud 34, ohne Ueberschreiben und ohne Loeschen.
- **SRV-05: Complete** (war es bereits, hier zum ersten Mal auf Tool-Ebene bewiesen: Handle aus Prozess A, Fortsetzung in Prozess B).
- **SRV-03: bleibt Pending.** Die zwei neuen Tools tragen korrekte Annotationen und kein Output-Schema (Contract-Test), aber SRV-03 ist eine Aussage ueber alle 15 Tools plus das fixierte Token-Budget; der Gesamtnachweis gehoert laut fruehem Phasen-Beschluss zu Plan 01-14. Diese Zurueckhaltung folgt derselben Linie wie bei TOOL-09 und AUTH-01.

## Self-Check: PASSED

- Alle acht neu angelegten Dateien liegen auf der Platte (`[ -f ]` je Pfad).
- Alle fuenf Commit-Hashes sind in `git log --oneline --all` auffindbar.
- Alle Acceptance Criteria beider Tasks nachgelaufen, alle Verification-Kommandos des Plans gruen (siehe Tabelle oben).

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
