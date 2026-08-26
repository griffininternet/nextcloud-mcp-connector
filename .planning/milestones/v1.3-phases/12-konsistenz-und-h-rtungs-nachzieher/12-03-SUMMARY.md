---
phase: 12-konsistenz-und-h-rtungs-nachzieher
plan: 03
subsystem: testing
tags: [pytest, provider-map, unified-search, vocabulary-gate, source-gate, ruff, pyright]

# Dependency graph
requires:
  - phase: 11-review-und-security
    provides: "die drei Nachzieher UF-1 bis UF-3 aus 11-SECURITY.md, das Quelltext-Gate aus T-11-29 als einmaliger Prüfschritt in 11-05-SUMMARY.md"
  - phase: 12-konsistenz-und-h-rtungs-nachzieher
    provides: "12-02 hat provider_map.py bereits angefasst (ids.encode_card_short, ids.parse in hit_url); dieser Plan ändert dort nur Kommentare"
provides:
  - "Verifikationskommentare für files und notes in PROVIDER_KINDS, beide am Release-Tag gelesen"
  - "Regressionstest für T-11-29: level=\"messages\" hat in tools/context.py keinen Aufrufer, mit Gegenprobe über eine geteilte Prüffunktion"
  - "Vokabular-Gate über drei READMEs, CHANGELOG.md und die übrigen docs/*.md, mit zwei benannten Ausnahmen und zwei Gegenproben"
  - "positive Behauptung über den Inhalt des Store-Archivs, aus scripts/build_store_release.sh gelesen"
affects: [13-release-und-store, changelog-0.1.9, provider-map-erweiterungen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Quelltext-Gate mit Text als Parameter statt read_text im Prüfkörper, damit die Gegenprobe dieselbe Funktion speist"
    - "Anker einer Nicht-leer-Behauptung darf nicht die Zeile sein, die die Gegenprobe manipuliert"
    - "Ausnahme eines Gates wird an eine positive, aus dem Build-Skript gelesene Eigenschaft gebunden statt an Prosa"

key-files:
  created: []
  modified:
    - src/mcp_connector/provider_map.py
    - tests/unit/test_tools_context.py
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Die Wortliste FORBIDDEN_VOCABULARY bleibt in tests/unit/test_exapp_env_setup.py und das Gate wächst um sie herum: zwei Stellen mit demselben Wort wären zwei Wahrheiten (der Fehler, den dieses Projekt als IN-03 benannt und behoben hat), und ein Umzug hätte an einem grünen Sicherheits-Gate gebaut. Der Preis ist thematische Unschärfe im Dateinamen."
  - "LICENSE ist die zweite, benannte Ausnahme des Vokabular-Gates: der AGPL-3.0-Volltext trägt das Wort in LICENSE:653 in einem eigenen Satz über einen Quell-Link. Fremdtext im Store-Archiv, eine Bearbeitung würde einen Lizenztext verfälschen."
  - "Die Nicht-leer-Behauptung des Quelltext-Gates ankert auf level=\"accounts\" und nicht auf level=\"mailboxes\": die Gegenprobe ersetzt genau die mailboxes-Zeile, ein überschriebener Anker hätte das Gate aus dem falschen Grund rot werden lassen."
  - "Das Vokabular-Gate prüft ausschließlich Markdown plus Manifest; Skripte bleiben draußen, weil ARCHIVE dort ein Variablenname und tar das Werkzeug ist."

patterns-established:
  - "Geteilte Prüffunktion: _message_level_calls(text) und vocabulary_findings(text, name) nehmen den Text als Parameter, das Gate liest die echte Datei, die Gegenprobe füttert einen konstruierten String"
  - "Jeder Fund nennt Datei und Zeilennummer, damit ein Verstoß eine Einzeilenkorrektur ist"
  - "Gegenproben, die eine echte Datei manipulieren, schreiben und lesen sie als Bytes (write_bytes) und nicht als Text, sonst dreht der Python-Roundtrip die Zeilenenden"

requirements-completed: [SEC-02]

# Metrics
duration: 21min
completed: 2026-08-25
---

# Phase 12 Plan 03: Konsistenz und Härtungs-Nachzieher Summary

**Die drei Nachzieher aus 11-SECURITY.md sind von Prüfschritten zu Belegen geworden: PROVIDER_KINDS trägt für jeden der sechs Einträge Repository, Datei und Klasse, das Quelltext-Gate zu T-11-29 läuft als Regressionstest mit Gegenprobe, und die Vokabular-Regel reicht jetzt so weit wie ihre Formulierung, mit zwei begründeten Ausnahmen.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-08-25T13:02:00Z
- **Completed:** 2026-08-25T13:23:00Z
- **Tasks:** 3
- **Files modified:** 3 (234 Zeilen, ausschließlich Zugänge, keine Löschung)

## Accomplishments

- Keine Zuordnung in `PROVIDER_KINDS` steht mehr ohne ihren Beleg, und beide neuen Belege erklären die abweichende Ableitung im eigenen Modul (Doppelspur bei `files`, Attributlosigkeit bei `notes`).
- `level="messages"` hat in `tools/context.py` von jetzt an einen Wächter statt einer Protokollzeile: der Lauf gegen eine manipulierte Quelle meldet den Fund mit Zeilennummer 365 und war damit rot gesehen.
- Die Vokabular-Regel deckt die drei READMEs, `CHANGELOG.md` und die übrigen `docs/*.md` ab, und ihre Ausnahme hängt an einer aus `scripts/build_store_release.sh` gelesenen Eigenschaft statt an einer Zusicherung im Prosatext.
- Die Wortliste steht weiter an genau einer Stelle im ganzen Testbaum, geprüft über alle `tests/**/*.py`.

## Task Commits

Each task was committed atomically:

1. **Task 1: SEC-02(a): die zwei fehlenden Verifikationskommentare** - `2407c1e` (docs)
2. **Task 2: SEC-02(b): Regressionstest zu T-11-29 mit Gegenprobe** - `397026f` (test)
3. **Task 3: SEC-02(c): Vokabular-Gate mit begründeter Ausnahme** - `381900f` (test)

## Fremder Quelltext: welche Zeile an welchem Ref bestätigt wurde

Der offene Punkt der Recherche (Secondary confidence: `Application.php` war nur auf `main` gelesen) ist geschlossen. Erste Handlung dieses Plans war der Lesezugriff am Tag:

| Datei | Ref | Zeile, bestätigt | Ergebnis |
|-------|-----|------------------|----------|
| `nextcloud/notes` `lib/AppInfo/Application.php` | Tag `v6.0.2` | 28 | `public const APP_ID = 'notes';` — am Tag bestätigt, nicht auf `main` |
| `nextcloud/notes` `lib/AppInfo/SearchProvider.php` | Tag `v6.0.2` | 22, 37-39 | in der Recherche am Tag gelesen (`class SearchProvider implements IProvider`, `getId()` liefert `Application::APP_ID`) |
| `nextcloud/server` `apps/files/lib/Search/FilesSearchProvider.php` | Tag `v34.0.0` | 49-51 plus `search()` | in der Recherche am Tag gelesen (`getId()` liefert `'files'`, `addAttribute('fileId', ...)`, `addAttribute('path', ...)`) |

Damit nennt jeder der beiden neuen Kommentare einen Release-Tag und keine wandernde Referenz, und die Konstante, die die Recherche nur auf `main` gesehen hatte, ist am Tag gelesen. Der Abruf lief über `raw.githubusercontent.com`, rein lesend, ohne Paketinstallation (T-12-SC bleibt eingehalten: `pyproject.toml` und `uv.lock` sind unberührt).

## Files Created/Modified

- `src/mcp_connector/provider_map.py` — zwei Kommentarblöcke über `"files"` und `"notes"`, im Format der vier vorhandenen Einträge. `PROVIDER_KINDS` selbst ist unverändert: dieselben sechs Ids, dieselben Zuordnungen.
- `tests/unit/test_tools_context.py` — `MESSAGE_LEVEL_CALL`, `_message_level_calls(text)`, das Gate `test_no_line_of_this_module_asks_mail_for_level_messages` und die Gegenprobe `test_the_message_level_gate_notices_the_call_and_leaves_the_prose_alone`. Der Verhaltenstest zu T-11-29 ist unverändert.
- `tests/unit/test_exapp_env_setup.py` — `PUBLIC_MARKDOWN`, `VOCABULARY_EXCEPTION`, `VERBATIM_ARCHIVE_TEXT`, `STORE_RELEASE_SCRIPT`, `ARCHIVE_MEMBER`, die Funktionen `vocabulary_findings`, `public_markdown_pages`, `archive_members` und vier Tests. Die bestehende Manifest-Anwendung, der engere Halter je Sprachvariante und die Manifest-Gegenprobe sind unverändert.

## Decisions Made

- **Ort der Wortliste: unverändert, das Gate wächst um sie herum.** `FORBIDDEN_VOCABULARY` bleibt in `tests/unit/test_exapp_env_setup.py`, und die neue Markdown-Prüfung entsteht in derselben Datei. Zwei Stellen mit demselben Wort wären zwei Wahrheiten, genau der Fehler, den dieses Projekt als IN-03 benannt und behoben hat; ein Umzug in eine neue Datei hätte am heute grünen Manifest-Gate gebaut, ohne die Regel zu verbessern. Der Preis ist ein Dateiname, der thematisch weiter ist als sein Inhalt, und der ist billiger als eine zweite Wahrheit oder ein Umbau an einem grünen Sicherheits-Gate. Die Begründung steht im Abschnittskommentar der Datei, nicht nur hier.
- **Zwei Ausnahmen statt einer.** `docs/store-submission.md` wie geplant (interne Release-Doku, zwei datierte Proof-Zeilen 124 und 125, fremder Nextcloud-Klassenname in 281). Dazu `LICENSE`, siehe Deviations.
- **Anker der Nicht-leer-Behauptung.** Der Quelltext-Gate-Anker ist `level="accounts"`, nicht `level="mailboxes"`, siehe Deviations.
- **Reichweite bewusst auf Markdown plus Manifest begrenzt.** `scripts/*.sh` bleibt draußen: dort ist `ARCHIVE` ein Variablenname und `tar` das Werkzeug, das das Paket baut. Eine Prüfung darauf hätte das Gate an einer Stelle rot gemacht, an der die Regel nie gemeint war.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LICENSE trägt das verbotene Wort: zweite benannte Ausnahme statt rotem Gate**

- **Found during:** Task 3 (SEC-02c)
- **Issue:** Der Plan und die Recherche halten fest: "Der Inhalt des Store-Archivs, gelesen in `scripts/build_store_release.sh:42-46`: `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`. Alle vier sind sauber." Das ist für drei der vier richtig. `LICENSE` trägt das Wort in Zeile 653, im AGPL-3.0-Satz "interface could display a \"Source\" link that leads users to an archive". Die geforderte positive Behauptung ("jede dieser Dateien ist sauber") wäre bei Einführung **rot** gewesen. Die Zählung der Recherche (`grep -ric "archiv"`) hatte nur Markdown-Dateien betrachtet, `LICENSE` war nicht in der Liste.
- **Fix:** `VERBATIM_ARCHIVE_TEXT = ("LICENSE",)` als zweite, namentlich benannte und im Docstring begründete Ausnahme. Die Begründung ist schärfer als die der Release-Doku: es ist kein Text dieses Projekts, und eine Bearbeitung des Lizenztextes zur Erfüllung einer Hausregel würde die Lizenz verfälschen. Dieselbe Klasse von Argument wie beim fremden Nextcloud-Klassennamen in `store-submission.md:281`, nur unverhandelbar.
- **Files modified:** `tests/unit/test_exapp_env_setup.py`
- **Verification:** `test_the_store_archive_carries_no_exempt_page` grün; `grep -in "archiv" LICENSE` zeigt genau die eine Zeile 653; die Gegenprobe über ein manipuliertes `README.md` macht denselben Test trotzdem rot, die Ausnahme deckt also nur `LICENSE` und nicht die Prüfung selbst.
- **Committed in:** `381900f` (Task-3-Commit)

**2. [Rule 1 - Bug] Der Gegenprobenlauf machte das Quelltext-Gate aus dem falschen Grund rot**

- **Found during:** Task 2 (SEC-02b)
- **Issue:** Erste Bauform nach Plan-Vorschlag: die Nicht-leer-Behauptung ankerte auf `mail_tools` **und** `level="mailboxes"`. Die vorgeschriebene Gegenprobe ersetzt aber genau `level="mailboxes"` durch `level="messages"`. Der Lauf schlug damit an der Anker-Behauptung fehl ("and the level this module does ask for has to be in it") und nie an der Nadel. Das Gate war rot, aber der Beweis war keiner: die eigentliche Prüfung war nicht gezeigt.
- **Fix:** Anker auf `level="accounts"` umgestellt, also auf eine Zeile, die die Manipulation nicht anfasst. Ein Kommentar im Test hält den Grund fest, damit die nächste Änderung ihn nicht wieder verliert.
- **Files modified:** `tests/unit/test_tools_context.py`
- **Verification:** Zweiter Gegenprobenlauf: `AssertionError: the message level of mail has no caller here / assert [(365, '                    level="messages",')] == []`. Die Nadel spricht, mit Zeilennummer.
- **Committed in:** `397026f` (Task-2-Commit)

**3. [Rule 3 - Blocking] Gegenproben auf echten Dateien schreiben Bytes, nicht Text**

- **Found during:** Task 2, wieder relevant in Task 3
- **Issue:** Der Gegenprobenlauf des Plans schreibt `src/mcp_connector/tools/context.py` per `write_text` zurück. Auf diesem Windows-Host dreht der Roundtrip `read_text`/`write_text` die Zeilenenden, und `git status` zeigte die Datei danach als geändert, obwohl `git diff` leer war. Das Gegenteil der Zusage "der Baum ist danach sauber".
- **Fix:** `git checkout -- src/mcp_connector/tools/context.py` für die eine Datei (kein `git clean`, kein blanket reset), und die README-Gegenprobe in Task 3 von Anfang an auf `read_bytes`/`write_bytes` umgestellt. Als Muster in `patterns-established` festgehalten.
- **Files modified:** keine (Werkzeugbedienung, nicht Repo-Inhalt)
- **Verification:** `git diff --exit-code -- src/mcp_connector/tools/context.py README.md README.de.md README.fr.md CHANGELOG.md docs/store-submission.md` ist sauber, `git status --short` nach jedem Task nur mit der jeweils bearbeiteten Datei.
- **Committed in:** nicht committet (keine Inhaltsänderung)

---

**Total deviations:** 3 auto-fixed (2 Bugs, 1 Blocking)
**Impact on plan:** Beide Bug-Fixes betreffen die Beweiskraft der Gates, also genau das, worum es in diesem Plan geht: eine Ausnahme, die bei Einführung rot gewesen wäre, und eine Gegenprobe, die das falsche Assert getroffen hätte. Kein Scope Creep, keine neue Datei, keine Paketinstallation.

## Issues Encountered

- Der offene Punkt der Recherche zu `Application::APP_ID` war in einem Zug lösbar: der Netzzugriff auf `raw.githubusercontent.com` am Tag `v6.0.2` funktionierte, also nennt der Kommentar den Tag statt nur die am Tag gelesene `SearchProvider.php`. Der Ausweichpfad des Plans wurde nicht gebraucht.
- `ruff format` wollte eine Zeile der neuen f-String-Verkettung anders setzen; einmal `ruff format` auf die Datei angewendet, danach `--check` grün.

## Verification Results

| Prüfung | Ergebnis |
|---------|----------|
| `uv run --no-sync pytest -q` | grün (voller Baum, nach jedem Task) |
| `uv run --no-sync pytest tests/contract -q` | grün |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 197 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | exit 0 |
| Vollständigkeits-Skript über `PROVIDER_KINDS` | "every provider entry carries its proof" |
| Gegenprobe manipulierte `context.py` | rot mit `(365, 'level="messages",')`, Baum danach sauber |
| Gegenprobe manipuliertes `README.md` | rot in **beiden** neuen Gates, `README.md:533` genannt, Baum danach sauber |
| Wortlisten-Eindeutigkeit über `tests/**/*.py` | genau eine Definition |
| `git diff --name-only 6eff36d..HEAD -- docs/store-submission.md pyproject.toml uv.lock appinfo/info.xml CHANGELOG.md scripts/check_tool_budget.py` | leer |

## Known Stubs

Keine. Dieser Plan fügt Kommentare und Prüfungen hinzu und keine Code-Pfade mit Datenquelle.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Für Phase 13 wichtig:** `CHANGELOG.md` steht ab jetzt unter dem Vokabular-Gate. Der 0.1.9-Block entsteht dort, also unter dieser Regel und nicht nachträglich geprüft. Wer den Block schreibt, bekommt einen roten Testlauf mit Datei und Zeilennummer statt eines Fundes im Store-Text.
- Wächst das Store-Archiv um eine Datei, prüft `test_the_store_archive_carries_no_exempt_page` sie automatisch mit, weil die Liste aus `scripts/build_store_release.sh` gelesen wird. Eine neue verbatim übernommene Fremddatei müsste bewusst in `VERBATIM_ARCHIVE_TEXT` benannt werden.
- Kommt ein siebter Provider in `PROVIDER_KINDS`, verlangt das Vollständigkeits-Skript aus diesem Plan (in `12-03-PLAN.md` als Verifikationsschritt, nicht als Test im Baum) einen Kommentar mit Repository, Datei und Klasse. Das ist die einzige Stelle, an der die Vollständigkeit noch von einem Plan-Verifikationsschritt und nicht von der Suite gehalten wird; ein Halter im Baum wäre der nächste billige Schritt, ist aber in SEC-02 nicht gefordert.
- Keine Blocker für Plan 12-04.

## Self-Check: PASSED

Alle drei geänderten Dateien existieren, die SUMMARY existiert, und alle drei Task-Commits (`2407c1e`, `397026f`, `381900f`) sind in `git log` auffindbar.

---
*Phase: 12-konsistenz-und-h-rtungs-nachzieher*
*Completed: 2026-08-25*
