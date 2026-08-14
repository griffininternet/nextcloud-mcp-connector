---
phase: 01-server-kern
plan: 11
subsystem: api
tags: [chatgpt, openai, pydantic, output-schema, ids, webdav-search, deck-sweep, respx]

# Dependency graph
requires:
  - phase: 01-10
    provides: unified_search, provider_map, hit_url, resolvable-Markierung
  - phase: 01-05
    provides: files.read mit Groessen-Cap, dav.parse_entries, dav.search_scope
  - phase: 01-07
    provides: caldav.get_event und die Event-Form mit id, summary, start, end
  - phase: 01-09
    provides: deck_client.get_boards, get_stacks, get_card, web_url
provides:
  - models.py mit SearchHit, SearchResults und FetchResult als Pydantic-Modelle
  - tools/chatgpt.py mit search (Delegation) und fetch (Routing ueber alle ID-Arten)
  - server/reg_chatgpt.py mit den zwei einzigen Tools MIT Output-Schema
  - dav.find_by_fileid und dav.build_fileid_body (fileid zurueck auf einen Pfad)
  - graceful ist generisch, ein Pydantic-Rueckgabetyp ueberlebt den Dekorator
affects: [01-14-tool-surface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Output-Schema genau dort, wo ein Client es liest (search und fetch), sonst nirgends"
    - "Ein zentraler ids-Codec entscheidet das Routing, unbekannte Praefixe werden abgelehnt"
    - "Sweep mit Cache, der genau einen Aufruf lang lebt (kein Modul-State, D-20)"
    - "WebDAV-SEARCH mit d:eq auf oc:fileid statt rekursivem PROPFIND"
    - "Grep-Test gegen eine unverifizierte Route, deshalb steht sie nirgends woertlich im Modul"

key-files:
  created:
    - src/mcp_connector/models.py
    - src/mcp_connector/tools/chatgpt.py
    - src/mcp_connector/server/reg_chatgpt.py
    - tests/unit/test_chatgpt_search.py
    - tests/unit/test_chatgpt_fetch.py
    - tests/integration/test_chatgpt_profile.py
  modified:
    - src/mcp_connector/server/__init__.py
    - src/mcp_connector/nextcloud/clients/dav.py
    - tests/contract/test_tool_surface.py
    - README.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "search und fetch laufen als einzige Tools OHNE structured_output=False: mcp 2.x erzeugt aus dem Pydantic-Rueckgabetyp structured_content und content gleichzeitig, genau die Doppelung, die OpenAI verlangt"
  - "graceful wird generisch (PEP 695), weil eine auf str festgenagelte Signatur genau die Annotation geloescht haette, aus der das SDK das Output-Schema baut"
  - "file:<fileid> wird per WebDAV-SEARCH mit d:eq auf oc:fileid in einen Pfad aufgeloest; gegen Nextcloud 34 live verifiziert, nicht angenommen"
  - "Die Deck-Kurzform wird per Sweep aufgeloest, ein Request pro Board, Abbruch beim Fund; die interne Route /apps/deck/cards/<id> (A4) wird nicht benutzt und steht deshalb nirgends woertlich im Modul"
  - "fetch antwortet auf eine url-ID mit einem ToolError, dessen Hinweis die URL traegt: ein Erfolgsergebnis ohne Inhalt ist die Form, die zum Erfinden einlaedt"
  - "fetch gibt fuer die Kurzform die kanonische lange Karten-ID zurueck, damit der naechste Aufruf ohne Sweep auskommt"
  - "Der Python-Parameter heisst resource_id, der Wire-Parameter id: der Wire-Name ist OpenAI-Vertrag, der Python-Name darf keinen Builtin verdecken (ruff A002)"
  - "Die Event-URL zeigt auf die Monatsansicht der Calendar-App; der Inhalt kommt aus CalDAV und braucht die App nicht, der Link schon"

patterns-established:
  - "Pydantic-Antwortmodelle nur fuer Clients, die sie lesen; alles andere bleibt kompakter JSON-String"
  - "Ein Grep-Test haelt eine bewusst nicht genutzte API-Route aus dem Modul heraus"
  - "Sweeps zaehlen ihre HTTP-Calls im Unit-Test, damit kein N+1 einschleicht"

requirements-completed: [TOOL-07]

# Metrics
duration: 74 min
completed: 2026-08-14
---

# Phase 01 Plan 11: ChatGPT-Kompatibilitaetsprofil Summary

**`search` und `fetch` mit exakt dem OpenAI-Schema: `search` delegiert an die Unified Search und liefert Zitat-faehige URLs, `fetch` loest praefixierte IDs auf Datei, Notiz, Karte und Termin auf und beantwortet nicht aufloesbare Treffer ehrlich statt falsch.**

## Performance

- **Duration:** 74 min (inklusive Unterbrechung durch einen API-Fehler und Wiederaufnahme)
- **Tasks:** 2 (beide TDD, RED und GREEN getrennt committet)
- **Files modified:** 11 (6 neu, 5 geaendert)

## Accomplishments

- `models.py` liefert `SearchHit`, `SearchResults` und `FetchResult` mit Annotationen auf dem Klassenkoerper; genau daran haengt, dass das SDK ueberhaupt ein Output-Schema baut statt still `repr()` zu verschicken.
- `search` ruft ausschliesslich `unified_search` auf und projiziert auf `id`, `title`, `url`, `text`. Kein zweiter Trefferweg, kein zweites ID-Schema. Der Unit-Test mockt nur die OCS-Routen der Unified Search, eine eigene Provider-Abfrage waere sofort als unmockter Request aufgefallen.
- Jeder Treffer traegt eine nicht leere, absolute URL auf der konfigurierten Instanz. Zwei Fallbacks (Titel auf die ID, URL auf die Instanz-Basis) verhindern, dass ein kuenftiger Provider die Zitate still abschaltet.
- `fetch` routet ueber `ids.parse` auf die vorhandenen Lesefunktionen: `files.read`, `notes.read`, den Deck-Client und `caldav.get_event`. Fuenf ID-Arten, jede mit eigenem Test.
- `dav.find_by_fileid` loest eine File-ID mit **einem** WebDAV-SEARCH (`d:eq` auf `oc:fileid`) zurueck auf den Pfad. Das war der offene Punkt des Plans: aus der Unified Search kommt nur die fileid, nicht der Pfad. Gegen die laufende Nextcloud 34 verifiziert, bevor eine Zeile Produktivcode entstand.
- Die Deck-Kurzform `card:<cardId>` wird per Sweep aufgeloest: ein Request fuer die Board-Liste, dann einen pro Board, Abbruch beim Fund. Der Test zaehlt die Calls und belegt, dass das zweite Board gar nicht mehr angefragt wird. Zurueck kommt die kanonische lange ID.
- Eine `url:`-ID wird nicht abgerufen, sondern beantwortet; der Hinweis traegt die URL zum Oeffnen. Kein einziger Request verlaesst den Prozess dabei (Unit-Test zaehlt auf einer Catch-all-Route).
- Grosse Dateien werden am selben Cap wie `files_read` geschnitten, die Kuerzung steht im `text` **und** in `metadata` samt Fortsetzungs-Offset.
- Der Contract-Test kennt jetzt die volle Oberflaeche: genau 15 Tools, und ein Output-Schema exakt bei `search` und `fetch`.

## Task Commits

1. **Task 1: Modelle und das Tool search (RED)** - `9c64907` (test)
2. **Task 1: Modelle und das Tool search (GREEN)** - `6b2c38d` (feat)
3. **Task 2: fetch mit Routing ueber alle ID-Arten (RED)** - `59eebc8` (test)
4. **Task 2: fetch mit Routing ueber alle ID-Arten (GREEN)** - `9f6d852` (feat)
5. **README-Abschnitt zum ChatGPT-Profil** - `74103e7` (docs)

## Files Created/Modified

- `src/mcp_connector/models.py` - `SearchHit`, `SearchResults`, `FetchResult`
- `src/mcp_connector/tools/chatgpt.py` - `search`, `fetch` und das Routing ueber alle fuenf ID-Arten
- `src/mcp_connector/server/reg_chatgpt.py` - die zwei Registrierungen mit Output-Schema
- `src/mcp_connector/server/__init__.py` - `graceful` generisch (PEP 695)
- `src/mcp_connector/nextcloud/clients/dav.py` - `build_fileid_body`, `find_by_fileid`
- `tests/unit/test_chatgpt_search.py` - 7 Faelle inklusive In-Memory-Aufruf mit Doppel-Payload
- `tests/unit/test_chatgpt_fetch.py` - 14 Faelle: fuenf ID-Arten, Sweep-Call-Zaehlung, Grep-Gate
- `tests/integration/test_chatgpt_profile.py` - 3 Live-Faelle: Datei- und Notiz-Rundlauf plus url-Grenze
- `tests/contract/test_tool_surface.py` - 15-Tools-Zaehlung, Output-Schema-Ausnahme, `fetch`-Parameter
- `README.md` - Abschnitt "ChatGPT connector profile"
- `.planning/REQUIREMENTS.md` - TOOL-07 auf Complete

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei wichtigsten:

- **Kein `structured_output=False` fuer diese zwei Tools.** Das ist die dokumentierte Ausnahme von der Schema-Diaet (D-14). Der Preis ist messbar: `tools/list` waechst von 9881 auf 10643 Bytes bei 15 statt 13 Tools, also gut 40 Prozent des Budgets bleiben frei.
- **`graceful` musste generisch werden.** Die alte Signatur `Callable[..., Awaitable[str]]` haette bei pyright nicht nur einen Fehler erzeugt, sondern konzeptionell die Return-Annotation ersetzt, aus der das SDK das Output-Schema ableitet. Ein Zeichen Aenderung mit direkter Wirkung auf den Vertrag.
- **Die File-ID-Aufloesung wurde erst verifiziert, dann gebaut.** Der Plan liess offen, wie aus `file:<fileid>` ein Pfad wird. Statt `attributes.path` durch die ID zu schleifen (was die ID aufblaehen und den OpenAI-Vertrag stoeren wuerde), loest ein WebDAV-SEARCH auf `oc:fileid` das Problem in einem Request. Vor der Implementierung gegen die laufende Nextcloud 34 geprueft, danach im Integrationstest festgenagelt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `graceful` auf einen generischen Rueckgabetyp umgestellt**
- **Found during:** Task 1
- **Issue:** `graceful` war als `Callable[..., Awaitable[str]] -> Callable[..., Awaitable[str]]` deklariert. Die zwei neuen Tools geben ein Pydantic-Modell zurueck; pyright haette den Dekorator abgelehnt, und die auf `str` festgenagelte Signatur ist genau die Annotation, aus der das SDK das Output-Schema baut.
- **Fix:** `def graceful[T](fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]` (PEP 695), Laufzeitverhalten unveraendert.
- **Files modified:** `src/mcp_connector/server/__init__.py`
- **Verification:** `uv run pyright` 0 Fehler; `search` und `fetch` haben ein Output-Schema, die anderen 13 Tools nicht.
- **Committed in:** `6b2c38d`

**2. [Rule 3 - Blocking] `dav.find_by_fileid` als neuer Lookup**
- **Found during:** Task 2
- **Issue:** `fetch("file:<fileid>")` braucht einen Pfad, und weder die ID noch die Unified-Search-Antwort traegt ihn bis in den `fetch`-Aufruf. Ohne Aufloesung waere die haeufigste ID-Art nicht abrufbar gewesen.
- **Fix:** `build_fileid_body` plus `find_by_fileid` in `dav.py`: ein WebDAV-SEARCH mit `d:eq` auf `oc:fileid`, Scope ist die eigene Home-Sammlung, Limit 1. Nicht numerische IDs werden vor dem Request abgelehnt.
- **Files modified:** `src/mcp_connector/nextcloud/clients/dav.py` (nicht in `files_modified` des Plans)
- **Verification:** Vorab per curl gegen die laufende Nextcloud 34 belegt (SEARCH liefert 207 mit dem passenden `d:href`), danach `test_a_file_id_is_resolved_to_a_path_and_read` und der Live-Rundlauf in `test_chatgpt_profile.py`.
- **Committed in:** `9f6d852`

**3. [Rule 2 - Missing Critical] Contract-Test auf die volle Oberflaeche erweitert**
- **Found during:** Task 2 (Acceptance Criterion "Contract-Test zaehlt 15")
- **Issue:** Der Plan listet `tests/contract/test_tool_surface.py` nicht unter `files_modified`, verlangt in den Acceptance Criteria aber genau die 15-Tools-Zaehlung und die Aussage, dass das Output-Schema exakt bei `search` und `fetch` steht.
- **Fix:** Drei neue Contract-Tests: vollstaendige Namensmenge plus `len == 15`, Output-Schema-Menge exakt `{search, fetch}`, und `fetch` mit Annotationen und dem Parameter `id`.
- **Files modified:** `tests/contract/test_tool_surface.py`
- **Verification:** `uv run pytest tests/contract -q` 15 passed
- **Committed in:** `59eebc8`

### Praezisierungen ohne Regelbedarf

- **Parametername im Python-Layer.** Der Plan schreibt `async def fetch(clients, id)`. `id` verdeckt einen Builtin, und ruff hat die Familie `A` aktiv. Der Wire-Parameter heisst wie verlangt `id` (mit einer einzigen, begruendeten `noqa: A002`-Zeile in der Registrierung), im Paket heisst der Wert `resource_id`.
- **Kanonische Karten-ID in der Antwort.** Bei der Kurzform gibt `fetch` die lange Form `card:<board>:<stack>:<card>` zurueck, damit der naechste Zugriff keinen Sweep mehr braucht. Der Plan legt das nicht fest.
- **Event-URL.** Der Plan verlangt eine oeffenbare URL, nennt aber keine Route. Genommen wird die Monatsansicht der Calendar-App (`/index.php/apps/calendar/dayGridMonth/<datum>`). Der Inhalt kommt aus CalDAV und braucht die App nicht; der Link braucht sie. Auf der Testinstanz ist die Calendar-App nicht installiert, deshalb ist dieser eine Link nicht live gegengeprueft (siehe "Issues Encountered").
- **Die interne Deck-Route steht nirgends woertlich im Modul.** Der Grep-Test aus den Acceptance Criteria prueft die reine Zeichenkette, also beschreibt der Modul-Docstring die Route, statt sie zu zitieren. Das ist Absicht und im Docstring vermerkt.
- **README-Abschnitt** ergaenzt, wie in den Vorgaengerplaenen ueblich; der Plan verlangt ihn nicht.

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing critical)
**Impact on plan:** Kein Scope Creep. Zwei Punkte waren Voraussetzung dafuer, dass der Plan ueberhaupt gebaut werden kann, der dritte setzt ein Acceptance Criterion um, das die Dateiliste nicht abgedeckt hat.

## Issues Encountered

- **Ausfuehrung wurde durch einen API-Fehler unterbrochen**, unmittelbar vor dem RED-Commit von Task 1. Der Arbeitsstand lag vollstaendig auf der Platte, die Wiederaufnahme hat ihn geprueft (RED bestaetigt), committet und normal weitergearbeitet. Keine Doppelarbeit, keine verlorenen Aenderungen.
- **Der RED-Commit von Task 1 ist der einzige Commit dieses Plans, bei dem `uv run pyright` einen Fehler meldet** ("chatgpt is unknown import symbol"), weil das Modul absichtlich noch fehlt. Das entspricht dem Vorgehen der Vorgaengerplaene (`d618164`, `088a677`: reine Testcommits ohne Stubs). Ab dem GREEN-Commit ist pyright durchgehend bei 0 Fehlern.
- **respx `assert_all_called`**: Der Test der langen Karten-ID registriert die `/boards`-Route absichtlich, ohne sie aufzurufen (das ist die Aussage: keine Sweep-Requests). Mit `assert_all_called=True` schlaegt respx darauf an; geloest mit `assert_all_called=False` plus Kommentar.
- **Die Calendar-App ist auf der Testinstanz nicht installiert** (das Bootstrap installiert nur Notes und Deck; CalDAV ist Core). Der Event-Rundlauf ist deshalb Unit-getestet, aber der erzeugte Calendar-Weblink ist nicht live gegen eine Instanz mit Calendar-App geprueft. Fuer 01-14 vorgemerkt.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run pytest -q` | 467 passed, 48 deselected |
| `uv run pytest -m integration -q` (Docker NC 34) | 40 passed, davon 3 neu |
| `uv run pytest tests/unit/test_chatgpt_search.py -q` | 7 passed (Plan verlangt mindestens 5) |
| `uv run pytest tests/unit/test_chatgpt_fetch.py -q` | 14 passed (alle fuenf ID-Arten, unbekanntes Praefix, fehlende App) |
| `uv run pytest tests/contract -q` | 15 passed, davon 3 neu |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 10643 Bytes, **15 Tools**, Budget 24000 |
| `uv run ruff check .` / `ruff format --check .` | sauber, 85 Dateien |
| `uv run pyright` | 0 errors |
| `uv run vulture src scripts --min-confidence 80` | leer |

**Schema-Beweis.** `tools/list` liefert ein `output_schema` ungleich `None` fuer genau zwei Namen, `search` und `fetch`; die uebrigen 13 haben `None` (`test_the_curated_set_is_complete_and_only_the_chatgpt_profile_has_a_schema`). Das Input-Schema von `search` hat genau die Property `query`, das von `fetch` genau `id`, beide required. Ein In-Memory-Aufruf von `search` liefert `structured_content` als Objekt **und** denselben Inhalt als JSON-Text im `content`-Array (`test_a_call_answers_with_structured_content_and_the_same_json_as_text`).

**Live-Beweis.** Datei anlegen, per `search` finden, deren ID per `fetch` aufloesen, Inhalt Byte fuer Byte vergleichen; danach dasselbe fuer eine Notiz. Beides gruen gegen `nextcloud:34-apache`. Die File-ID-Aufloesung per `oc:fileid` ist damit nicht angenommen, sondern belegt.

## Requirements

- **TOOL-07 auf Complete.** `search` und `fetch` tragen die verlangten Namen, Parameter und Feldnamen, liefern die von OpenAI verlangte Doppelung aus `structuredContent` und `content`, und der Rundlauf Suche-Treffer-Volltext ist live belegt.
- **SRV-03 bleibt Pending.** Annotationen und Schema-Diaet stimmen fuer alle 15 Tools und das Budget-Gate ist gruen, aber der Nachweis gehoert nach Plan 01-14: dort wird das Budget auf "gemessen plus 15 Prozent" festgezurrt und die Annotation jedes einzelnen Tools abgenommen.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Die Tool-Oberflaeche ist mit 15 Tools vollstaendig. Plan 01-14 kann direkt abnehmen: Budget auf gemessen plus 15 Prozent (aktuell 10643 Bytes), Annotationen aller Tools, TOOL-06-Negativbeweis mit zwei Konten und TOOL-09-Grep-Gate.
- Offene Punkte fuer 01-14: der Calendar-Weblink aus `fetch` gegen eine Instanz mit installierter Calendar-App, und die Frage aus 01-10, ob der Kalender-Provider dort eine aufloesbare `resourceUrl` liefert.
- Der Owner-Schritt aus 01-13 (PR an nextcloud/context_agent#227) ist von diesem Plan unberuehrt und weiterhin offen.

## Self-Check: PASSED

- Alle 6 als `created` gemeldeten Dateien liegen auf der Platte (`[ -f ]` je Datei).
- Alle 5 Commit-Hashes sind in `git log --oneline --all` auffindbar.
- Alle Acceptance Criteria beider Tasks nachgefahren und gruen, siehe Tabelle unter "Verification".
- Keine Stubs, keine Platzhalter, keine hardgecodeten Leerwerte im gelieferten Code.
