---
phase: 01-server-kern
plan: 10
subsystem: api
tags: [unified-search, ocs, asyncio, httpx, respx, graceful-degradation, ids]

# Dependency graph
requires:
  - phase: 01-06
    provides: ocs_get, parse_ocs, OCS-Pflichtheader, Fehler-Mapping
  - phase: 01-02
    provides: ids-Codec (encode_file, encode_note, encode_url, parse)
  - phase: 01-08
    provides: Fan-out-mit-degraded-Muster aus contacts_search
provides:
  - provider_map mit Provider-ID-zu-Kind-Tabelle und ID-Extraktion aus resourceUrl
  - ocs.list_search_providers und ocs.provider_search (Provider-Liste zur Laufzeit)
  - unified_search als paralleler Provider-Fan-out mit hartem Timeout pro Provider
  - degraded-Feld fuer ausgefallene, langsame und unbekannte Provider
  - resolvable-false-Markierung fuer Treffer ohne spaeter aufloesbare ID
affects: [01-11-chatgpt-profil, 01-14-tool-surface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Provider-Liste pro Aufruf frisch lesen, nie hardcoden und nie cachen"
    - "asyncio.gather(return_exceptions=True) plus asyncio.timeout pro Teilabfrage"
    - "Ehrliche Restkategorie url statt geratener Zuordnung (Pitfall 10)"
    - "Nicht aufloesbare IDs tragen resolvable: false, aufloesbare kosten kein Feld"
    - "Optionale Mengen-Parameter als kommaseparierter String (Schema-Diaet, kein anyOf)"

key-files:
  created:
    - src/mcp_connector/provider_map.py
    - src/mcp_connector/tools/search.py
    - src/mcp_connector/server/reg_search.py
    - tests/fixtures/ocs_providers.json
    - tests/fixtures/ocs_search_files.json
    - tests/unit/test_provider_map.py
    - tests/unit/test_unified_search.py
    - tests/integration/test_unified_search.py
  modified:
    - src/mcp_connector/nextcloud/clients/ocs.py
    - tests/contract/test_tool_surface.py
    - pyproject.toml
    - README.md

key-decisions:
  - "Der Kalender-Provider bleibt bewusst ausserhalb der Tabelle: seine resourceUrl adressiert eine Tagesansicht, nicht den DAV-Objektnamen, den event:<calendarUri>:<objectName> braucht; er faellt in die url-Kategorie, bis eine Instanz eine aufloesbare Form zeigt"
  - "Ein unbekannter Provider ergibt kind url und die ID url:<absolute-url>; auch ein bekannter Provider mit unbrauchbarer resourceUrl faellt dorthin, statt eine falsche Note-ID zu bilden"
  - "Deck bleibt bei der Kurzform card:<cardId> und wird als resolvable: false markiert, weil der Provider weder Board noch Stack liefert"
  - "Ein unbekannter Name im providers-Parameter ist eine Degradierung, kein Fehler: die anderen Provider haben echte Antworten, und eine leere Antwort ohne Grund wird als 'nichts gefunden' weitererzaehlt"
  - "Null Provider auf der Instanz ist dagegen ein Fehler mit Ausweg, weil eine leere Trefferliste dort eine Luege waere"
  - "limit gilt pro Provider und wird von Nextcloud erneut gedeckelt; Server-Cursor kommen unveraendert unter cursors zurueck"
  - "providers ist ein kommaseparierter String statt einer Liste, weil ein Listen-Parameter ein anyOf aus array und null im Input-Schema erzeugt"

patterns-established:
  - "Fan-out ueber eine zur Laufzeit gelesene Menge: erst Liste holen, dann parallel abfragen, Ausfaelle benennen"
  - "Ehrliche ID-Grenze: lieber url:<absolute-url> plus resolvable false als eine geratene Aufloesung"
  - "Timeout-Beweis im Unit-Test ueber einen async side_effect in respx plus monkeypatch der Timeout-Konstante"

requirements-completed: []

# Metrics
duration: 15 min
completed: 2026-08-14
---

# Phase 01 Plan 10: Unified Search Summary

**Cloudweite Suche ueber alle installierten Nextcloud-Suchprovider: Provider-Liste zur Laufzeit, paralleler Fan-out mit hartem Timeout pro Provider, normalisierte Treffer mit stabilen IDs und explizit benannten Degradierungen.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-14T18:04:30Z
- **Completed:** 2026-08-14T18:19:30Z
- **Tasks:** 2 (beide TDD, RED und GREEN getrennt committet)
- **Files modified:** 12 (8 neu, 4 geaendert)

## Accomplishments

- `provider_map.py` bildet Provider-IDs auf Kinds ab und holt die ID aus `attributes.fileId`, aus dem `/f/<fileid>`-Segment oder aus dem letzten Segment der `resourceUrl`; die verifizierte Deck-Provider-ID `search-deck-card-board` steht drin, `deck` bewusst nicht.
- Jede zurueckgegebene URL wird aus der konfigurierten Basis-URL neu gebaut, Pfad, Query und Fragment bleiben erhalten, die fremde Herkunft nie (T-01-68).
- `ocs.list_search_providers` und `ocs.provider_search` sprechen OCS mit den beiden Pflichtheadern; die Provider-ID geht URL-quotiert in den Pfad, weil sie vom Draht kommt.
- `unified_search` fragt alle Provider parallel ab (`asyncio.gather(return_exceptions=True)` plus `asyncio.timeout` pro Provider) und liefert `query`, `count`, `results`, `note` sowie optional `degraded`, `cursors` und `skipped`.
- Ausgefallene (500), zu langsame und unbekannte Provider erscheinen mit Namen und Grund unter `degraded`; ein stilles Teil-Ergebnis ist an keiner Stelle moeglich.
- Treffer, die spaeter nicht aufloesbar sind (Kurzform-Karten, url-Kategorie), tragen `resolvable: false`; aufloesbare Treffer kosten das Feld nicht.
- Live gegen die Docker-Nextcloud verifiziert: die Testinstanz meldet 9 Provider (`appstore`, `circles`, `comments`, `files`, `notes`, `search-deck-card-board`, `search-deck-comment`, `settings`, `systemtags`); die drei bekannten werden zugeordnet, die sechs uebrigen landen sauber in der url-Kategorie.

## Task Commits

1. **Task 1: Provider-Mapping und ID-Extraktion (RED)** - `d618164` (test)
2. **Task 1: Provider-Mapping und ID-Extraktion (GREEN)** - `bfbe3de` (feat)
3. **Task 2: unified_search mit parallelem Fan-out (RED)** - `088a677` (test)
4. **Task 2: unified_search mit parallelem Fan-out (GREEN)** - `a736484` (feat)
5. **README-Abschnitt zur cloudweiten Suche** - `c26df88` (docs)

## Files Created/Modified

- `src/mcp_connector/provider_map.py` - Provider-ID-zu-Kind-Tabelle, `extract_id`, `hit_url`, `absolute_url`
- `src/mcp_connector/tools/search.py` - `unified_search`: Fan-out, Normalisierung, degraded, note
- `src/mcp_connector/server/reg_search.py` - Registrierung mit READ_ONLY, `structured_output=False`, `@graceful`
- `src/mcp_connector/nextcloud/clients/ocs.py` - `SEARCH_PROVIDERS_PATH`, `list_search_providers`, `provider_search`
- `tests/fixtures/ocs_providers.json` - Provider-Liste inklusive eines unbekannten Providers (`spreed`)
- `tests/fixtures/ocs_search_files.json` - Files-Treffer mit `attributes` und einer ohne
- `tests/unit/test_provider_map.py` - 16 Faelle inklusive SSRF-Grenze und Skip-Fall
- `tests/unit/test_unified_search.py` - 14 Faelle inklusive 500-Provider, Timeout und Cursor
- `tests/integration/test_unified_search.py` - 4 Live-Faelle inklusive Degraded-Beweis
- `tests/contract/test_tool_surface.py` - `unified_search` in `tools/list`, Annotationen, Schema-Diaet
- `pyproject.toml` - pytest-Import-Modus `importlib`
- `README.md` - Abschnitt "Cloud wide search"

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die beiden wichtigsten:

- **Kalender-Provider nicht in der Tabelle.** Der Plan liess ihn ausdruecklich nur zu, wenn er zur Laufzeit auftritt und aufloesbar ist. Auf der Testinstanz taucht er nicht auf, und seine `resourceUrl` traegt keinen DAV-Objektnamen. Eine Zuordnung waere eine ID, die `fetch` nie aufloesen kann.
- **Unbekannte Provider-Namen degradieren, statt zu scheitern.** Ein Tippfehler im `providers`-Parameter erzeugt jetzt einen benannten `degraded`-Eintrag neben echten Treffern. Null Provider auf der Instanz bleibt dagegen ein Fehler mit Hinweis.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] pytest-Import-Modus auf importlib gestellt**
- **Found during:** Task 2 (Testlauf ueber die ganze Suite)
- **Issue:** Der Plan schreibt zwei Testdateien mit demselben Basisnamen vor (`tests/unit/test_unified_search.py` und `tests/integration/test_unified_search.py`). Im pytest-Standardmodus `prepend` bricht die Collection der ganzen Suite mit "import file mismatch" ab, weil der Testbaum keine Pakete hat.
- **Fix:** `--import-mode=importlib` in den `addopts` von `pyproject.toml`, mit Begruendungskommentar. Keine Umbenennung, damit die Plan-Dateinamen erhalten bleiben.
- **Files modified:** `pyproject.toml`
- **Verification:** `uv run pytest -q` sammelt und besteht alle 299 Tests; `uv run pytest -m integration -q` besteht alle 37.
- **Committed in:** `a736484`

**2. [Rule 2 - Missing Critical] resolvable-Markierung an jedem Treffer**
- **Found during:** Task 2 (Umsetzung der Must-Have-Wahrheit "jeder Treffer traegt eine aufloesbare ID oder ist ehrlich markiert")
- **Issue:** Der Plan nennt die Trefferfelder `id, title, subline, url, provider, kind`. Damit waere eine Kurzform-Karten-ID und eine url-ID vom Modell nicht von einer aufloesbaren Datei-ID zu unterscheiden, und genau das ist Pitfall 10.
- **Fix:** Zusaetzliches Feld `resolvable: false`, nur dort, wo die ID nicht direkt an ein Lese-Tool gehen kann. Aufloesbare Treffer bleiben unveraendert kompakt.
- **Files modified:** `src/mcp_connector/tools/search.py`, `tests/unit/test_unified_search.py`
- **Verification:** `test_a_hit_that_cannot_be_resolved_later_says_so`
- **Committed in:** `a736484`

**3. [Rule 2 - Missing Critical] Fehler statt leerer Liste bei null Providern**
- **Found during:** Task 2
- **Issue:** Meldet eine Instanz gar keinen Suchprovider, waere `results: []` eine Antwort, die das Modell als "nichts gefunden" weitergibt.
- **Fix:** `ToolError` mit Hinweis auf die Administration; unbekannte angefragte Provider bleiben dagegen eine Degradierung.
- **Files modified:** `src/mcp_connector/tools/search.py`
- **Verification:** `test_an_instance_without_any_provider_is_an_error_with_a_way_out`
- **Committed in:** `a736484`

### Praezisierungen ohne Regelbedarf

- `extract_id` bekommt die Basis-URL als dritten Parameter (der Plan nennt `extract_id(provider_id, entry)`), weil die url-Kategorie eine absolute URL braucht. Die Rueckgabe bleibt die geplante `(kind, id, canonical)`. Ergaenzend gibt es `hit_url` und `absolute_url`.
- Der `providers`-Parameter akzeptiert im Tool-Layer einen kommaseparierten String (Schema-Diaet) und in Python zusaetzlich eine Sequenz.

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing critical)
**Impact on plan:** Kein Scope Creep. Der Import-Modus war Voraussetzung fuer einen gruenen Gesamtlauf, die beiden anderen Punkte setzen Must-Have-Wahrheiten des Plans um, die die Feldliste nicht abgedeckt hat.

## Issues Encountered

- **respx zaehlt einen abgebrochenen Request nicht als Call.** Der Timeout-Test lief mit `assert_all_called=True` rot, weil die abgebrochene Antwort nie zurueckkommt. Geloest mit `assert_all_called=False` plus Kommentar; das Verhalten ist genau das, was der Test belegt.
- **pyright im Standard-Modus** meldete das Entpacken von `tuple | None` in den Tests. Geloest mit einem kleinen Test-Helfer `resolved(...)`, der den Skip-Fall in eine klare Assertion verwandelt, statt die Typpruefung zu lockern.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run pytest -q` | 299 passed |
| `uv run pytest -m integration -q` (Docker NC 34) | 37 passed, davon 4 neu |
| `uv run pytest tests/unit/test_provider_map.py -q` | 16 passed (Plan verlangt mindestens 6) |
| `uv run pytest tests/unit/test_unified_search.py -q` | 14 passed (Plan verlangt mindestens 8) |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 8956 Bytes, 13 Tools, Budget 24000 |
| `uv run ruff check .` / `ruff format --check .` | sauber, 78 Dateien formatiert |
| `uv run pyright` | 0 errors |
| `uv run vulture src scripts --min-confidence 80` | leer |
| Keine hardgecodete Provider-Liste | `grep` in `tools/search.py` trifft nur eine Docstring-Zeile |

Degraded-Beweis, dreifach: ein 500-Provider (Unit), ein Provider jenseits des Timeouts (Unit, `monkeypatch` auf 0.05 s plus async `side_effect`), ein unbekannter Provider-Name gegen die laufende Nextcloud (Integration).

## Requirements

- **SRV-05** war bereits vor diesem Plan Complete und bleibt es: `unified_search` haelt keinen Session-State, cached nichts und reicht Server-Cursor unveraendert durch.
- **TOOL-06 bleibt Pending.** Der provider-parallele Fan-out ist live belegt, die Berechtigungstreue selbst aber nur architektonisch (jeder Request traegt das App-Passwort des Nutzers, kein eigener Index, kein Cache, kein Nutzer-Parameter). Es fehlt der Negativbeweis mit zwei Konten, dass Nutzer B eine Datei von Nutzer A nicht findet. Der gehoert in den Tool-Surface-Plan 01-14, der bereits zwei Testkonten nutzt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-11 (ChatGPT-Profil, `search` und `fetch`) kann direkt auf `unified_search` und `provider_map` aufsetzen: die ID-Kategorien inklusive der ehrlichen url-Grenze stehen, jede URL ist absolut und oeffenbar (Voraussetzung fuer die Zitat-Metadaten).
- Offene Punkte fuer 01-14: TOOL-06-Negativbeweis mit zwei Konten, und die Frage, ob die Kalender-Provider-ID auf einer Instanz mit installierter Calendar-App eine aufloesbare `resourceUrl` liefert.

## Self-Check: PASSED

- Alle 8 als `created` gemeldeten Dateien liegen auf der Platte (`[ -f ]` je Datei).
- Alle 5 Commit-Hashes sind in `git log --oneline --all` auffindbar.
- Alle Acceptance Criteria beider Tasks nachgefahren und gruen, siehe Tabelle unter "Verification".

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
