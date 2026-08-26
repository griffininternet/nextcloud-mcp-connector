---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 01
subsystem: infra
tags: [release, versioning, changelog, appinfo, uv-lock, keep-a-changelog]

# Dependency graph
requires:
  - phase: 12-konsistenz-und-h-rtungs-nachzieher
    provides: "die zwei nutzersichtbaren Uebergaben fuer den Changelog: message_truncated auf der Eintragsebene von talk_browse (12-01) und die README-Provider-Korrektur spreed zu talk-conversations (12-04)"
  - phase: 11
    provides: "das Bump-Vorbild aus dem 0.1.8-Release (Commit 8392680 samt uv.lock-Zeile, 33cae32 fuer die drei README-Statuszeilen) und den 0.1.8-Eintrag zu preview_truncated als Wortlaut-Vorlage"
provides:
  - "Version 0.1.9 als dieselbe Zeichenkette an sechs Stellen: pyproject.toml, src/mcp_connector/__init__.py, appinfo/info.xml (version und image-tag), die drei README-Statuszeilen und die uv.lock-Selbstangabe"
  - "der 0.1.9-Kandidat fuer bootstrap_exapp.sh: app_version() liest appinfo/info.xml und baut daraus das Image-Tag, gegen das Plan 13-03 den CIMD-Weg nachmisst"
  - "Changelog-Block ## [0.1.9] - 2026-08-25 mit ### Changed (message_truncated als Formataenderung) und ### Fixed (talk-conversations als Doku-Korrektur)"
  - "zwei Link-Referenzen am Dateiende: [Unreleased] auf compare/v0.1.9...HEAD, [0.1.9] auf compare/v0.1.8...v0.1.9"
  - "kein Tag v0.1.9: die Tag-Liste ist nach diesem Plan unveraendert leer"
affects: [13-02-enterprise-fake-door, 13-03-cimd-nachmessung, 13-05-release-runbook]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Versions-Bump als reine Texteditierung, byte-exakt per Python rb/wb, ohne uv lock und ohne uv sync"
    - "Changelog-Formataenderungs-Eintrag nach dem preview_truncated-Vorbild: erst der Satz, dass ein Leser des alten Schluessels nachgezogen werden muss, dann die zwei Bedeutungen je Ebene"

key-files:
  created:
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-01-SUMMARY.md
  modified:
    - pyproject.toml
    - src/mcp_connector/__init__.py
    - appinfo/info.xml
    - uv.lock
    - README.md
    - README.de.md
    - README.fr.md
    - CHANGELOG.md

key-decisions:
  - "Die uv.lock-Zeile 472 wird mitgezogen, obwohl kein Gate und kein Runbook-Schritt sie haelt: Commit 8392680 hat sie beim 0.1.8-Bump ebenso geaendert, und eine Selbstangabe, die eine andere Version nennt als das Paket, ist eine Unwahrheit im Lockfile. Angefasst wurde sie per Texteditierung, nicht per uv lock, damit kein Dependency-Block sich bewegt."
  - "Die vier CRLF-Dateien (appinfo/info.xml, die drei READMEs) wurden per Python rb/wb ersetzt statt mit einem zeilenweisen Editor: ein LF-Rueckschreiber haette aus vier Ein-Zeilen-Diffs vier Massen-Diffs gemacht. Belegt durch git diff --numstat: 1 zu 1 je README, 2 zu 2 fuer info.xml."
  - "Der Changelog-Einleitungsabsatz nennt die Werkzeugzahl in Worten (twenty one) und nicht als Ziffer 21: das Werkzeugzahl-Gate in tests/contract/test_tool_surface.py liest README.md und docs/*.md, CHANGELOG.md liegt ausserhalb, aber eine Ziffer im Changelog waere eine zweite Stelle, die bei der naechsten Familie nachgezogen werden muesste."
  - "Commit-Typ release( fuer den Bump statt chore(: das Vorbild 8392680 des 0.1.8-Bumps traegt denselben Typ, und die Release-Historie dieses Repos bleibt damit an einem Wort erkennbar."
  - "Die Rubrik ### Added bleibt in diesem Plan leer und wird nicht angelegt: Plan 13-02 setzt den Enterprise-Eintrag dort in denselben Block, sobald der Text existiert. Keep-a-Changelog-Reihenfolge (Added vor Changed) bleibt damit ohne Umbau erreichbar."

patterns-established:
  - "Sechs Versionsstellen in einem Commit, plus die Behauptung im Commit-Text, dass kein Tag existiert"
  - "Ein Vorab-Zaehlschritt vor jeder Ersetzung: die Anzahl der Treffer je Datei wird gegen eine erwartete Zahl geprueft und bricht bei Abweichung ab, statt blind zu ersetzen"

requirements-completed: []  # EXAPP-09 bleibt Pending: geteilt mit 13-02, 13-04, 13-05 und 13-06, und sein Wortlaut verlangt das Release im Store

# Metrics
duration: 12min
completed: 2026-08-25
---

# Phase 13 Plan 01: Version 0.1.9 und ihr Changelog-Block Summary

**Die Zeichenkette 0.1.9 steht an allen sechs Stellen, der Changelog-Block darueber nennt `message_truncated` als Formataenderung und `talk-conversations` als Doku-Korrektur, und `git tag --list v0.1.9` ist leer.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-25T16:57:00Z
- **Completed:** 2026-08-25T17:09:16Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Der 0.1.9-Kandidat existiert. `appinfo/info.xml` ist die Quelle, aus der `bootstrap_exapp.sh` per `app_version()` das Image-Tag baut, also kann Plan 13-03 ab jetzt gegen die Topologie messen, die auch veroeffentlicht wird.
- Die sechs Stellen tragen dieselbe Zeichenkette, und die Gleichheit ist nicht behauptet, sondern gehalten: `tests/unit/test_exapp_env_setup.py` vergleicht `<version>` mit `mcp_connector.__version__` und `<image-tag>` mit `<version>`, 152 Tests gruen.
- Der Changelog nennt genau die zwei Aenderungen, die Phase 12 als nutzersichtbar uebergeben hat, und keine der drei, die intern geblieben sind. `_ID_KIND`, `one_room` und `test_module_boundaries` kommen im Block nicht vor.
- Kein Dependency hat sich bewegt. Der Diff von `pyproject.toml` und `uv.lock` ist zusammen vier Zeilen, zwei davon Entfernungen, und enthaelt kein `dependencies`, kein `requires-dist` und keinen Paketnamen ausser `nextcloud-mcp-connector`.
- Die Grenze zum Tag wurde nicht ueberschritten. `git tag --list v0.1.9` ist leer, so wie D-01 es verlangt; der Tag entsteht in Plan 13-05 nach Owner-Freigabe.

## Task Commits

Each task was committed atomically:

1. **Task 1: Sechs Versionsstellen auf 0.1.9** - `da3673d` (release)
2. **Task 2: Changelog-Block 0.1.9 mit message_truncated als Formataenderung** - `65f33ed` (docs)

## Files Created/Modified

- `pyproject.toml` - Zeile 3, `version = "0.1.9"`. Ein-Zeilen-Diff, kein Dependency-Block angefasst
- `src/mcp_connector/__init__.py` - Zeile 7, `__version__ = "0.1.9"`. Die Referenz, gegen die das Manifest-Gate vergleicht
- `appinfo/info.xml` - Zeile 171 `<version>0.1.9</version>` und Zeile 245 `<image-tag>0.1.9</image-tag>`. `<summary>`, die drei `<description>`-Bloecke und `<environment-variables>` sind unberuehrt: ein leer gemachtes Element beantwortet den Store-Upload mit HTTP 500
- `uv.lock` - Zeile 472, die Selbstangabe des Pakets `nextcloud-mcp-connector`. Die sechste Stelle, ungegatet, per Texteditierung mitgezogen
- `README.md` - Zeile 27, `Version 0.1.9.` Die Zahl 21 in "All 21 tools" ist unberuehrt
- `README.de.md` - Zeile 29, `Version 0.1.9.` "Alle 21 Tools" unberuehrt, Umlaute der Statuszeile erhalten
- `README.fr.md` - Zeile 31, `Version 0.1.9.` "Les 21 outils" unberuehrt, Accents erhalten
- `CHANGELOG.md` - neuer Block `## [0.1.9] - 2026-08-25` ab Zeile 12, direkt ueber `## [0.1.8] - 2026-08-25` (jetzt Zeile 39); Einleitungsabsatz im Ton von 0.1.7, `### Changed` mit der Formataenderung, `### Fixed` mit der Doku-Korrektur; am Dateiende `[Unreleased]` auf `compare/v0.1.9...HEAD` umgeschrieben und `[0.1.9]` darunter ergaenzt

## Changelog-Datum (Uebergabe an Plan 13-05)

**Der Block traegt das Datum 2026-08-25.** Das ist der Kalendertag des Schreibens. Entsteht der Tag `v0.1.9` an einem anderen Tag, muss Plan 13-05 die Zeile `## [0.1.9] - 2026-08-25` in `CHANGELOG.md` (Zeile 12) vor dem Tag auf den Tag des Tags korrigieren. Der 0.1.8-Block traegt dasselbe Datum, das ist kein Fehler: beide Releases fallen in denselben Kalendertag.

## Verification Results

| Prueffrage | Ergebnis |
|-----------|----------|
| `grep -c '^version = "0.1.9"' pyproject.toml` | 1 |
| `grep -c '^__version__ = "0.1.9"' src/mcp_connector/__init__.py` | 1 |
| `grep -o '<version>[^<]*' appinfo/info.xml` | `<version>0.1.9`, genau einer |
| `grep -o '<image-tag>[^<]*' appinfo/info.xml` | `<image-tag>0.1.9`, genau einer |
| `grep -n '^Version 0\.1\.9\.' README.md README.de.md README.fr.md` | drei Treffer, einer je Datei (27, 29, 31) |
| `grep -c '0\.1\.8' pyproject.toml src/mcp_connector/__init__.py` | 0 und 0 |
| `git diff --numstat uv.lock` | `1 1 uv.lock` |
| `git diff --numstat pyproject.toml` | `1 1 pyproject.toml` |
| `git diff -- pyproject.toml uv.lock` | vier Zeilen, alle `version = "0.1.8"` zu `version = "0.1.9"`; kein `dependencies`, kein `requires-dist`, kein Fremdpaketname |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, 152 Tests |
| `git tag --list v0.1.9` | leer |
| Blockreihenfolge `grep -n '^## \['` | `12: ## [0.1.9]` vor `39: ## [0.1.8] - 2026-08-25` |
| `message_truncated` | Zeile 23, also innerhalb des 0.1.9-Blocks (12 bis 38) |
| `talk_browse` | Zeile 22, im 0.1.9-Block |
| `talk-conversations` | einmal, in `### Fixed` |
| `compare/v0.1.9...HEAD` / `compare/v0.1.8...v0.1.9` | je genau einmal |
| `_ID_KIND` / `one_room` / `test_module_boundaries` in CHANGELOG.md | 0 / 0 / 0 |
| `grep -in 'archiv' CHANGELOG.md` | kein Treffer |
| Em-Dash und En-Dash in CHANGELOG.md | 0 und 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -k "vocabulary" -q` | Exit 0, 4 Tests |
| `git diff --stat 9f2baa1..HEAD` | genau die acht Dateien dieses Plans |
| Loeschungen in beiden Commits | keine |

## Decisions Made

- **Die uv.lock-Zeile wird mitgezogen.** Die Pattern-Map nennt sie als einzige Stelle ohne Analog und stellt die Frage ausdruecklich; der Plan hat sie entschieden. Angefasst wurde die Zeile per Texteditierung, kein `uv lock`, kein `uv sync`, kein `uv add`: ein Lock-Lauf haette Dependency-Zeilen bewegt und den Diff unpruefbar gemacht.
- **Byte-exakte Ersetzung mit Vorab-Zaehlung.** Vier der sieben Dateien liegen im CRLF (`appinfo/info.xml`, die drei READMEs), drei im LF. Ein Skript hat je Datei die Trefferzahl gegen eine erwartete Zahl geprueft und bei Abweichung abgebrochen, statt zu ersetzen. Die Vorab-Zaehlung hat auch die Nebenwirkungsfreiheit belegt: keine der sieben Dateien enthaelt `0.1.8` an einer Stelle, die nicht gemeint war.
- **Der Changelog nennt die Werkzeugzahl in Worten.** "the same twenty one tools" statt "21": eine Ziffer waere eine zweite Stelle, die bei der naechsten Werkzeugfamilie nachgezogen werden muss, und sie stuende ausserhalb des Halters, der genau das verhindert.
- **`### Added` bleibt aus.** Der Block hat heute nur `### Changed` und `### Fixed`. Plan 13-02 setzt den Enterprise-Eintrag als `### Added` darueber, in Keep-a-Changelog-Reihenfolge, ohne den bestehenden Text anzufassen.

## Deviations from Plan

Am Code und an den Artefakten des Plans: keine, der Plan lief woertlich wie geschrieben. Eine Abweichung betrifft die Zustandspflege danach.

### Auto-fixed Issues

**1. [Rule 1 - Bug] EXAPP-09 wieder auf Pending zurueckgesetzt**

- **Found during:** Zustandspflege nach Task 2
- **Issue:** Die Frontmatter dieses Plans nennt `requirements: [EXAPP-09]`, und der Standardablauf hakt daraufhin die Anforderung in `.planning/REQUIREMENTS.md` ab (Checkbox Zeile 22 und Tabellenzeile 53 auf `Complete`). Der Wortlaut von EXAPP-09 lautet aber "Release 0.1.9 ist im Store", und dazu gehoeren Branch-Push, Tag nach Owner-Freigabe, Signatur ueber das heruntergeladene Asset und die Proof-Zeilen der Runbook-Schritte 4 bis 8. Nichts davon ist passiert, der Tag existiert bewusst nicht. Zusaetzlich beanspruchen vier weitere Plaene derselben Phase (13-02, 13-04, 13-05, 13-06) dieselbe Anforderung. Ein Haken haette in der Traceability-Tabelle behauptet, das Release sei ausgeliefert.
- **Fix:** `git checkout -- .planning/REQUIREMENTS.md`; die Datei ist byte-identisch zum Stand vor dem Abhaken, EXAPP-09 steht wieder auf `[ ]` und `Pending`. Das Abhaken gehoert in den letzten Plan der Kette (13-06 beziehungsweise 13-05 nach dem Store-Nachweis). Die Projekt-Praxis dafuer ist etabliert, siehe die Pending-Begruendungen von TOOL-09 und CLIENT-04 in STATE.md.
- **Files modified:** keine (die Ruecknahme stellt den Ausgangsstand her)
- **Verification:** `git diff --exit-code .planning/REQUIREMENTS.md` sauber; `grep -n 'EXAPP-09' .planning/REQUIREMENTS.md` zeigt `- [ ]` und `Pending`
- **Committed in:** nicht committet, weil es keine Aenderung gibt

---

**Total deviations:** 1 auto-fixed (1 Bug in der Zustandspflege)
**Impact on plan:** Keine Auswirkung auf die Artefakte. Die Korrektur verhindert eine unwahre Anforderungsangabe; kein Scope Creep.

## Issues Encountered

- Git warnt beim Stagen von `pyproject.toml`, `src/mcp_connector/__init__.py`, `uv.lock` und `CHANGELOG.md` mit "LF will be replaced by CRLF the next time Git touches it". Das ist die `core.autocrlf`-Einstellung dieses Arbeitsplatzes und keine Folge dieses Plans: die vier Dateien lagen vor dem Edit im LF und liegen danach im LF, `git diff --numstat` zeigt je einen Ein-Zeilen-Diff. Keine Aktion.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Fuer Plan 13-02:** `CHANGELOG.md` Zeile 12 bis 38 ist der 0.1.9-Block, `### Changed` beginnt auf Zeile 20. Der Enterprise-Eintrag gehoert als neue Rubrik `### Added` zwischen Einleitungsabsatz und `### Changed`. Die drei READMEs und die drei `<description>`-Bloecke in `appinfo/info.xml` sind unberuehrt und stehen dem Enterprise-Abschnitt vollstaendig offen; die Versionszeilen sind erledigt und muessen nicht ein zweites Mal angefasst werden.
- **Fuer Plan 13-03:** `appinfo/info.xml` nennt `<image-tag>0.1.9</image-tag>`, `bootstrap_exapp.sh` liest daraus das Tag. Der Kandidat, gegen den gemessen wird, ist damit baubar.
- **Fuer Plan 13-05:** das Changelog-Datum ist 2026-08-25 und muss vor dem Tag gegen den Kalendertag des Tags geprueft werden (Abschnitt oben). Runbook-Schritte 1 und 2 sind erledigt, Schritt 3 (die sechs Gates) hat dieser Plan bewusst nicht gefahren: nur die zwei Text-Gates liefen, der Vollauf gehoert vor den Push.
- **Kein Blocker.** Der Tag existiert nicht, die Grenze zum irreversiblen Teil des Runbooks ist unangetastet.

## Self-Check: PASSED

Alle acht geaenderten Dateien und die SUMMARY existieren auf der Platte, beide Task-Commits (`da3673d`, `65f33ed`) sind in `git log` auffindbar, und keiner der beiden Commits enthaelt eine Loeschung.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*
