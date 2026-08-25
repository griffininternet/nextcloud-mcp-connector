---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 04
subsystem: infra
tags: [release, gates, tool-budget, store-archive, proof-lines, structure-check]

# Dependency graph
requires:
  - phase: 13
    plan: 01
    provides: "die Version 0.1.9 an sechs Stellen und den Changelog-Block ab Zeile 12, gegen die die Proof-Zeilen zu den Runbook-Schritten 1 und 2 geschrieben wurden"
  - phase: 13
    plan: 02
    provides: "die Rubrik ### Added mit dem Enterprise-Eintrag und die vier Fake-Door-Fassungen, die als neuer Store-Text in der Proof-Zeile zu Schritt 2 stehen"
  - phase: 12
    provides: "die Vokabular-Gate-Reichweite ueber die drei READMEs, CHANGELOG.md und den Rest von docs/, mit docs/store-submission.md als einziger Ausnahme"
provides:
  - "sechs gruene Gates auf dem 0.1.9-Kandidaten: 2812 Tests bestanden bei 163 deselektiert, kein Lint-Befund, 199 Dateien formatiert, kein Typfehler, kein toter Code, Werkzeugoberflaeche 15711 Bytes ueber 21 Werkzeuge gegen 18000"
  - "ein geprueftes Store-Paket dist/mcp_connector-0.1.9.tar.gz, 47546 Bytes, sha256 4f2a05feba738536cc4a1ea26cc1c736e92048f959f6bc9064458d8ce8e2e318, nicht committet"
  - "drei datierte Proof-Zeilen in docs/store-submission.md zu den Runbook-Schritten 1 bis 3, jede mit dem Befehl, der sie geprueft hat"
  - "kein Tag v0.1.9: die Tag-Liste ist nach diesem Plan unveraendert leer"
affects: [13-05-release-runbook, 13-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die sechs Gates in der Runbook-Reihenfolge mit uv run --no-sync, also ohne Sync und ohne Auflaesung: kein Paketstand bewegt sich zwischen Messung und Push"
    - "Archiv-Probelauf als Strukturpruefung mit drei Fragen: genau ein Top-Level-Ordner, die Mitgliederliste, und die README-Statuszeile aus dem Paket selbst gelesen statt aus dem Arbeitsbaum"

key-files:
  created:
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-04-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Die Proof-Zeile zu Schritt 3 nennt weder eine Signatur noch eine Bytezahl des lokal gebauten Pakets. Die 47546 Bytes stehen in dieser SUMMARY, damit Plan 13-06 die Differenz zum veroeffentlichten Asset belegen kann, aber nicht in der Nachweistabelle: dort waere eine Bytezahl neben dem Wort Signatur genau die Verwechslung, die T-13-17 beschreibt."
  - "Die Zahl der bestandenen Tests wurde mit einem zweiten Lauf ohne das zusaetzliche -q ermittelt. addopts traegt bereits -q, das Runbook-Kommando ergibt also -qq, und -qq unterdrueckt die Summenzeile. Der Gate-Lauf selbst blieb woertlich der aus dem Runbook; der zweite Lauf diente nur der Zahl."
  - "Task 1 hat keinen Commit, weil er nichts an einer versionierten Datei aendert: dist/ ist per .gitignore:17 ausgeschlossen, und ein leerer Commit haette eine Aenderung behauptet, die es nicht gibt. Die Messwerte des Tasks reisen in der Proof-Zeile von Task 2 und in dieser SUMMARY."
  - "Die Werkzeugoberflaeche traf den Erwartungswert 15711 Bytes exakt. Damit war der Befund-Fall aus dem Plan (stoppen statt Grenzwerte anheben) nicht zu betreten; BUDGET_BYTES bleibt 18000 und MAX_TOOL_BYTES bleibt 1400."

patterns-established:
  - "Drei Proof-Zeilen in einem Commit, je eine pro Runbook-Schritt, und die Behauptung im Commit-Text, dass keine Zeile fuer die Schritte 4 bis 8 geschrieben wurde"

requirements-completed: []  # EXAPP-09 bleibt Pending: geteilt mit 13-01, 13-02, 13-05 und 13-06, und sein Wortlaut verlangt das Release im Store

# Metrics
duration: 12min
completed: 2026-08-25
---

# Phase 13 Plan 04: Die sechs Gates und die Proof-Zeilen der Schritte 1 bis 3 Summary

**Alle sechs Gates laufen auf dem 0.1.9-Kandidaten gruen, das Werkzeugoberflaechen-Mass steht unveraendert bei 15711 Bytes ueber 21 Werkzeuge gegen 18000, das Store-Paket hat genau einen Top-Level-Ordner und traegt die Statuszeile 0.1.9, und drei datierte Proof-Zeilen belegen die Runbook-Schritte 1 bis 3, ohne dass ein Tag existiert.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-25T18:07:00Z
- **Completed:** 2026-08-25T18:19:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Die sechs Gates laufen in der Runbook-Reihenfolge und mit dem Praefix `uv run --no-sync` durch, jeder mit Exit 0. Damit ist der Zustand, der gepusht werden soll, gemessen und nicht angenommen.
- Das Werkzeugoberflaechen-Mass hat sich nicht bewegt: 15711 Bytes, genau der Erwartungswert des Plans. Der Befund-Fall (Abweichung meldet man, statt das Budget anzuheben) musste nicht betreten werden, weil Phase 12 kein Werkzeug und keinen Docstring angefasst hat.
- Pitfall 7 ist geschlossen. Die Statuszeile `Version 0.1.9.` steht nicht nur im Arbeitsbaum, sondern im gebauten Paket selbst, aus ihm heraus gelesen. Bei 0.1.8 lag der Fix hinter dem Tag, und weil ein Release-Asset unveraenderlich ist, sagt jenes Paket bis heute 0.1.7.
- Die Nachweistabelle hat drei neue Zeilen und keine vierte. Die Schritte 4 bis 8 bleiben leer, weil sie noch nicht passiert sind: eine vorab geschriebene Zeile wuerde die Beweisrichtung umdrehen, und genau diese Richtung ist der Grund fuer die Vokabular-Gate-Ausnahme dieser Datei.
- Die Grenze zum irreversiblen Teil des Runbooks ist unangetastet. `git tag --list v0.1.9` ist leer, es lief kein Push, und aus `dist/` ist nichts committet.

## Task Commits

1. **Task 1: Die sechs Gates und der Archiv-Probelauf** - kein Commit, siehe unten. Der Task aendert keine versionierte Datei: sein Ergebnis ist eine Messung, sein Artefakt liegt unter `dist/` und ist per `.gitignore:17` ausgeschlossen
2. **Task 2: Proof-Zeilen der Runbook-Schritte 1 bis 3** - `bf4cc06` (docs), 3 Zeilen hinzugefuegt, 0 entfernt

## Die Gate-Zahlen (Uebergabe an Plan 13-05 und 13-06)

| Gate | Kommando | Ergebnis |
|------|----------|----------|
| 1 | `uv run --no-sync pytest -q` | Exit 0, 2812 bestanden, 163 deselektiert, 67 s |
| 2 | `uv run --no-sync ruff check .` | Exit 0, `All checks passed!` |
| 3 | `uv run --no-sync ruff format --check .` | Exit 0, 199 Dateien bereits formatiert |
| 4 | `uv run --no-sync pyright` | Exit 0, `0 errors, 0 warnings, 0 informations` |
| 5 | `uv run --no-sync vulture src scripts vulture_whitelist.py` | Exit 0, keine Ausgabe |
| 6 | `uv run --no-sync python scripts/check_tool_budget.py` | Exit 0, `tools/list: 15711 bytes, 21 tools, budget 18000` |

Vergleich zur letzten Messung (0.1.8, Proof-Zeile vom 2026-08-24 22:36Z): 2766 auf 2812 bestandene Tests bei unveraendert 163 deselektierten, 197 auf 199 formatierte Dateien, und die Werkzeugoberflaeche von 15657 auf 15711 Bytes. Die 54 Bytes sind die Docstring-Aenderung an `talk_browse` aus Phase 12 und kein neues Werkzeug: die Zahl 21 ist unveraendert.

Die groessten Werkzeuge im Mass: `mail_browse` 1376, `calendar_create_event` 1351, `calendar_list_events` 951, `search` 924, `talk_browse` 912 Bytes. Der grenznaechste Wert ist `mail_browse` mit 1376 gegen `MAX_TOOL_BYTES` 1400.

## Das lokal gebaute Paket (Uebergabe an Plan 13-06)

- **Pfad:** `dist/mcp_connector-0.1.9.tar.gz`, nicht committet
- **Groesse:** 47546 Bytes
- **sha256:** `4f2a05feba738536cc4a1ea26cc1c736e92048f959f6bc9064458d8ce8e2e318`
- **Mitglieder:** `mcp_connector/`, `mcp_connector/appinfo/`, `mcp_connector/appinfo/info.xml`, `mcp_connector/CHANGELOG.md`, `mcp_connector/LICENSE`, `mcp_connector/README.md`

Diese beiden Werte sind Diagnose und kein eingereichter Wert. Plan 13-06 laedt das Asset des Releases herunter, vergleicht Groesse und sha256 gegen diese Zeilen und signiert ausschliesslich das Heruntergeladene: `tar.gz` ist nicht bytereproduzierbar, bei 0.1.8 standen 45710 Bytes lokal gegen 45546 veroeffentlicht bei verschiedenen sha256. Die vom Build-Skript ausgegebene Signatur ueber das lokale Paket wurde nicht notiert und wird nicht eingereicht.

## Files Created/Modified

- `docs/store-submission.md` - drei neue Tabellenzeilen 133 bis 135, direkt nach der letzten 0.1.8-Zeile (132) und vor `### The update keeps the connections` (jetzt 137). Zeile 133 belegt Schritt 1 (sechs Versionsstellen, die drei README-Statuszeilen ausdruecklich genannt, `uv.lock` als sechste Stelle per Texteditierung), Zeile 134 Schritt 2 (`message_truncated` als Formataenderung, `talk-conversations` als Doku-Korrektur, Enterprise als neuer Store-Text, die zwei Link-Referenzen), Zeile 135 Schritt 3 (die sechs Gate-Zahlen, ein Top-Level-Ordner, die Statuszeile im Paket, und der Satz, dass der Lauf eine Strukturpruefung ist und das lokal gebaute Paket nicht das signierte Artefakt)

## Verification Results

| Prueffrage | Ergebnis |
|-----------|----------|
| Sechs Gates in Runbook-Reihenfolge, je Exit 0 | ja, Zahlen in der Tabelle oben |
| `check_tool_budget.py` nennt 21 Werkzeuge und Budget 18000 | ja, `tools/list: 15711 bytes, 21 tools, budget 18000` |
| Abweichung der Werkzeugoberflaeche zum Erwartungswert 15711 | keine, Treffer auf das Byte |
| `tar -tzf dist/mcp_connector-0.1.9.tar.gz \| cut -d/ -f1 \| sort -u` | genau eine Zeile, `mcp_connector` |
| `tar -xzOf dist/mcp_connector-0.1.9.tar.gz mcp_connector/README.md \| grep -c '^Version 0\.1\.9\.'` | 1 |
| `git status --short dist` | leer |
| `git check-ignore -v dist/mcp_connector-0.1.9.tar.gz` | `.gitignore:17:dist/` |
| Drei neue Zeilen mit Datum der Form `\| YYYY-MM-DD HH:MMZ \|` | ja, 133, 134, 135 |
| Reihenfolge: neue Zeilen zwischen 0.1.8-Zeile und `### The update keeps the connections` | 132 (0.1.8), 133 bis 135 (neu), 137 (Ueberschrift) |
| `0.1.9` je neue Zeile, Kommando in der dritten Spalte | ja in allen drei; `grep -c '0\.1\.9' docs/store-submission.md` gibt 3, also traegt keine aeltere Zeile die Zahl |
| Die Zeile zu Schritt 3 nennt structure check und das nicht signierte lokale Paket | ja, wortgleich mit dem Formvorbild der 0.1.8-Zeile |
| Zeile zu einem der Schritte 4 bis 8 fuer 0.1.9 | keine, `grep -n 'Step [45678]'` leer |
| Em-Dash und En-Dash in `docs/store-submission.md` | 0 und 0 |
| `git diff --numstat docs/store-submission.md` vor dem Commit | `3 0` |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, 152 Tests, Vokabular-Gate eingeschlossen |
| `git tag --list v0.1.9` | leer, nach Task 1 und nach Task 2 |
| Loeschungen im Commit | keine, `git diff --diff-filter=D` leer |
| Arbeitsbaum nach dem Commit | sauber |

## Decisions Made

- **Keine Bytezahl und keine Signatur in der Proof-Zeile.** Die 47546 Bytes und der sha256 stehen in dieser SUMMARY, weil Plan 13-06 sie fuer die Differenz braucht. In der Nachweistabelle waeren sie die Verwechslungsgefahr, die T-13-17 beschreibt: eine Bytezahl neben dem Wort Signatur liest sich wie ein eingereichter Wert.
- **Die Testzahl kam aus einem zweiten Lauf.** `addopts` in `pyproject.toml` traegt bereits `-q`, das Runbook-Kommando ergibt also `-qq`, und damit unterdrueckt pytest die Summenzeile. Der Gate-Lauf blieb woertlich der aus dem Runbook (Exit 0); die Zahl 2812 bei 163 deselektierten kam aus `uv run --no-sync pytest` ohne das zweite `-q`. Das ist derselbe Testumfang, nur eine Zeile mehr Ausgabe.
- **Task 1 ohne Commit.** Der Task erzeugt eine Messung und ein Paket unter `dist/`. Beides ist bewusst nicht versioniert, also gibt es nichts zu committen; ein leerer Commit haette eine Aenderung behauptet. Die Messwerte sind in der Proof-Zeile von Task 2 und hier festgehalten, also nicht verloren.
- **Grenzwerte unangetastet.** `BUDGET_BYTES` bleibt 18000, `MAX_TOOL_BYTES` bleibt 1400, wie D-04 es verlangt. Es gab keinen Anlass, sie anzufassen, und der Plan haette bei einer Abweichung ohnehin den Befund verlangt und nicht die Anhebung.

## Deviations from Plan

Keine an den Artefakten. Der Plan lief wie geschrieben: zwei Tasks, ein Commit, keine Auto-Fix-Regel wurde ausgeloest, kein Blocker, kein Checkpoint.

Eine Beobachtung ohne Aenderung: das Runbook-Kommando `uv run --no-sync pytest -q` kann seine eigenen Zahlen nicht nennen, weil `addopts` bereits `-q` traegt und `-qq` die Summenzeile unterdrueckt. Der Gate-Lauf ist davon unberuehrt (Exit 0 ist der Gate-Wert), nur die Proof-Zeile braucht die Zahl, und die kam aus einem zweiten Lauf desselben Umfangs. Das Runbook wurde nicht geaendert: das gehoert in einen Plan, der das Runbook anfasst, und nicht in einen, der es ausfuehrt.

**Total deviations:** 0
**Impact on plan:** keiner

## Known Stubs

Keine. Dieser Plan hat keine Zeile Code angefasst; die einzige geaenderte Datei ist Dokumentation, und sie beschreibt ausschliesslich Ereignisse, die eingetreten sind.

## Issues Encountered

- Git warnt beim Stagen von `docs/store-submission.md` mit "LF will be replaced by CRLF the next time Git touches it". Das ist `text=auto` aus `.gitattributes` mit der Windows-Einstellung dieses Arbeitsplatzes und keine Folge dieses Plans: die Datei lag vorher im LF und liegt danach im LF, `git diff --numstat` zeigt `3 0`. Keine Aktion.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Fuer Plan 13-05 (Push und Tag):** die Runbook-Schritte 1 bis 3 sind belegt, der Kandidat ist gemessen. Offen bleibt vor dem Tag genau eine Pruefung aus 13-01: das Changelog-Datum `## [0.1.9] - 2026-08-25` in `CHANGELOG.md` Zeile 12 muss gegen den Kalendertag des Tags gehalten werden. Der Tag selbst entsteht erst nach ausdruecklicher Owner-Freigabe (D-01), und der Branch-Push kommt davor, weil die URLs im Manifest sonst auf einen Stand zeigen, den es oeffentlich nicht gibt.
- **Fuer Plan 13-06 (Signatur und Store-Upload):** die Vergleichswerte stehen oben. Signiert wird ausschliesslich das heruntergeladene Asset, und die Differenz zu 47546 Bytes und `4f2a05fe…` ist der Beleg dafuer, warum.
- **Kein Blocker.** Kein Tag, kein Push, kein Upload, nichts aus `dist/` committet.

## Self-Check: PASSED

`docs/store-submission.md` und diese SUMMARY liegen auf der Platte, der Task-Commit `bf4cc06` ist in `git log` auffindbar, und er enthaelt keine Loeschung. Das gebaute Paket `dist/mcp_connector-0.1.9.tar.gz` existiert mit 47546 Bytes und ist per `.gitignore:17` ausgeschlossen.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*
