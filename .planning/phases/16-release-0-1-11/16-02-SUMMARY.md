---
phase: 16-release-0-1-11
plan: 02
subsystem: infra
tags: [release, gates, tool-budget, store-package, proof-table]

# Dependency graph
requires:
  - phase: 16-release-0-1-11
    provides: "Die Versionszeichenkette 0.1.11 an allen sechs Stellen und den Changelog-Block ## [0.1.11] - 2026-08-28"
provides:
  - "Sechs lokal grüne Gates auf dem 0.1.11-Kandidaten, ohne Anhebung eines Grenzwerts"
  - "Die Bytegröße des lokal gebauten Store-Pakets, 47349, als Bezugswert für die Differenz zum veröffentlichten Asset in Plan 16-04"
  - "Die Proof-Zeilen der Runbook-Schritte 1 bis 3 in docs/store-submission.md"
affects: [16-03 Branch-Push und Tag, 16-04 Signatur über das heruntergeladene Asset, EXAPP-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Testzahlen aus einem Lauf ohne zusätzliches -q lesen, weil addopts bereits eines trägt und zwei davon die Summenzeile unterdrücken"
    - "Die Nutzlast eines Textreleases im gebauten Paket zählen, nicht im Arbeitsbaum: vier Zählungen gegen 1 und gegen 0, sonst ließe sich ein Release bauen, das seinen eigenen Grund nicht enthält"

key-files:
  created:
    - .planning/phases/16-release-0-1-11/16-02-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Task 1 hat keinen eigenen Commit, weil er keine versionierte Datei berührt: dist/ ist gitignored, und die Messungen sind in den Proof-Zeilen aus Task 2 festgehalten"
  - "Die Proof-Zeile zu Schritt 2 nennt v0.1.10..3fb9941 als den Befehl, der die Nutzlast-Aussage über die drei READMEs wirklich belegt, statt der Form aus dem 16-01-SUMMARY, die nach dem Versionshub nicht mehr leer ist"

patterns-established:
  - "Bei einem Versionssprung gleicher Länge ist die Byte-Gleichheit der Werkzeugoberfläche selbst der Nachweis: die Proof-Zeile nennt den Grund, statt die Zahl nur zu wiederholen"

requirements-completed: []

# Metrics
duration: 11min
completed: 2026-08-28
---

# Phase 16 Plan 02: Gates und Paket-Probelauf Summary

**Alle sechs Gates laufen lokal grün, die Werkzeugoberfläche misst exakt die erwarteten 15712 Bytes über 21 Werkzeuge gegen ein Budget von 18000 ohne jede Bewegung, und das gebaute Store-Paket trägt Statuszeile, Manifest-Nutzlast und Changelog-Block des Kandidaten. Kein Tag existiert.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-28T08:38:00Z
- **Completed:** 2026-08-28T08:49:08Z
- **Tasks:** 2
- **Files modified:** 1

## Die gemessenen Gate-Zahlen

| Gate | Ergebnis | Exit |
|------|----------|------|
| `pytest -q` | 2813 bestanden, 163 deselektiert, 87,47 s | 0 |
| `ruff check .` | All checks passed | 0 |
| `ruff format --check .` | 198 Dateien bereits formatiert | 0 |
| `pyright` | 0 errors, 0 warnings, 0 informations | 0 |
| `vulture src scripts vulture_whitelist.py` | keine Ausgabe, kein toter Code | 0 |
| `python scripts/check_tool_budget.py` | 15712 Bytes, 21 Werkzeuge, Budget 18000 | 0 |

Jedes Kommando lief mit dem Präfix `uv run --no-sync`, in genau der Reihenfolge des Runbooks.
Die Testzahl stammt aus einem zweiten Lauf ohne das zusätzliche `-q`, weil `addopts` bereits
eines trägt und zwei davon die Summenzeile unterdrücken.

**Die Werkzeugoberfläche hat sich nicht um ein Byte bewegt.** 15712 ist exakt der Wert des
0.1.10-Laufs. Das ist der erwartete Befund und kein Zufall: die Versionszeichenkette reist im
`serverInfo` des `tools/list`-Umschlags mit, und `0.1.10` wie `0.1.11` sind sechs Zeichen lang.
Beim Sprung von `0.1.9` auf `0.1.10` wuchs sie um ein Zeichen, deshalb wuchs damals die
Messung um genau ein Byte. Die größten Schemata sind unverändert `mail_browse` mit 1376 und
`talk_browse` mit 912 Bytes.

**Kein Grenzwert wurde angehoben.** `BUDGET_BYTES` steht auf 18000 (Zeile 83),
`MAX_TOOL_BYTES` auf 1400 (Zeile 117), und
`git diff -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py` ist leer.

## Der Paket-Probelauf, eine Strukturprüfung

`bash scripts/build_store_release.sh` baute `dist/mcp_connector-0.1.11.tar.gz` mit **47349
Bytes**. Diese Zahl ist der Bezugswert, gegen den Plan 16-04 die Differenz zum
veröffentlichten Asset belegt; bei 0.1.10 standen 47299 Bytes lokal gegen 46973
veröffentlicht, bei verschiedenem sha256. Die vom Skript ausgegebene Signatur ist Diagnose und
wurde nirgends notiert und nirgends eingereicht.

| Prüfung | Erwartet | Gemessen |
|---------|----------|----------|
| Top-Level-Ordner | genau `mcp_connector` | genau `mcp_connector` |
| Mitglieder | `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md` | alle vier, sonst nichts |
| `README.md` gegen `^Version 0\.1\.11\.` | 1 | 1 |
| `info.xml` gegen `author mail="admin@infranode.dev"` | 1 | 1 |
| `info.xml` gegen `k.cherif@outlook.de` | 0 | 0 |
| `info.xml` gegen `An assistant also reads text that strangers wrote` | 1 | 1 |
| `info.xml` gegen `would be a chain` | 0 | 0 |
| `CHANGELOG.md` gegen `^## \[0\.1\.11\]` | 1 | 1 |
| `CHANGELOG.md` gegen `Unreleased` | 0 | 0 |

Die vier Zählungen über das Manifest sind der Punkt des Probelaufs: sie belegen, dass die vier
Zeilen, für die dieses Release überhaupt existiert, tatsächlich im Kandidaten liegen. Kein Gate
hält sie, und ein Asset ist unveränderlich.

`git status --short dist` gibt keine Zeile aus, `git tag --list v0.1.11` ebenfalls nicht.

## Die drei Proof-Zeilen

`docs/store-submission.md` trägt drei neue Zeilen, 08:44Z, 08:45Z und 08:47Z, zwischen der
bisher letzten Zeile von 06:05Z und der Überschrift `### The update keeps the connections`.
`git diff --numstat` nennt 3 hinzugefügte und 0 entfernte Zeilen, keine bestehende Zeile wurde
bewegt. Die Datumsspalte aller 77 Tabellenzeilen ist von der ersten bis zur letzten aufsteigend.
Die Datei bleibt LF, im Arbeitsbaum wie im Index: die CRLF-Zählung ist 0 an beiden Orten.

Für die Schritte 4 bis 8 steht keine Zeile in der Datei. Sie entstehen in den Plänen 16-03 und
16-04, nachdem ihre Ereignisse eingetreten sind.

## Task Commits

1. **Task 1: Sechs Gates und Paket-Probelauf** - kein Commit, siehe unten
2. **Task 2: Proof-Zeilen der Runbook-Schritte 1 bis 3** - `8a2b123` (docs)

Task 1 hat keine versionierte Datei berührt. Er misst, und `dist/` ist gitignored; sein Ergebnis
ist in der Proof-Zeile von 08:47Z festgehalten, die Task 2 committet hat. Ein leerer Commit
hätte nur behauptet, dass etwas geschah.

## Files Created/Modified

- `docs/store-submission.md` - drei Proof-Zeilen zu den Runbook-Schritten 1, 2 und 3, angehängt an das Ende der Nachweistabelle

## Deviations from Plan

**None - plan executed exactly as written.** Kein Auto-Fix nach Regel 1 bis 4, kein Paket
installiert, kein Grenzwert angehoben, kein Tag erzeugt, nichts gepusht, nichts hochgeladen.

## Issues Encountered

Eine Diskrepanz, klein und ohne Folge für den Kandidaten, aber sie gehört benannt:

**Das 16-01-SUMMARY nennt unter "Issues Encountered" einen Ersatzbefehl, der die Aussage nicht
trägt.** Dort steht, gegen die Phasenbasis `3fb9941` gebe
`git diff --numstat 3fb9941..HEAD -- README.md README.de.md README.fr.md` keine Zeile aus, als
Beleg dafür, dass die drei READMEs keine Nutzlast dieses Releases tragen. Gemessen gibt dieser
Befehl je `1 1` aus, denn `3fb9941` ist der Stand vor dem Versionshub, und der Hub hat die drei
Statuszeilen gehoben. Leer ist stattdessen `git diff --numstat v0.1.10..3fb9941` über dieselben
drei Dateien: zwischen dem Tag und dem Phasenstart hat sich in den READMEs keine Zeile bewegt.

Die Aussage des Changelog-Blocks bleibt damit richtig und ist jetzt sauber belegt: sowohl über
den leeren Bereich `v0.1.10..3fb9941` als auch über `git diff v0.1.10..HEAD -U0`, das über die
drei Dateien genau drei geänderte Zeilen zeigt, je eine Statuszeile. Beide Formen stehen in der
Proof-Zeile zu Schritt 2, die falsche Form steht nirgends.

Sonst keine Abweichung: die Testzahl 2813 bestanden bei 163 deselektierten und die
Byte-Erwartung 15712 aus dem 16-01-SUMMARY sind beide exakt eingetroffen, und die 198
formatierten Dateien entsprechen dem 0.1.10-Lauf.

## Known Stubs

Keine. Dieser Plan schreibt keinen Code und keinen Platzhalter.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Runbook-Schritt 3 ist abgeschlossen und belegt. Roadmap-Erfolgskriterium 5 ist erfüllt: alle
  Gates lokal grün auf dem Kandidaten, bei 18000 und 1400 über 21 Werkzeuge, ohne Anhebung.
- **Kein Tag existiert**, weder lokal noch auf der Gegenstelle, und nichts wurde gepusht. Die
  drei Wave-1-Commits und der eine Commit dieses Plans liegen unveröffentlicht auf `main`.
- Für Plan 16-03: die Kopfzeile des Changelog-Blocks nennt `2026-08-28`, und dieser Plan lief am
  2026-08-28 in UTC wie in Europe/Berlin. Entsteht der Tag an einem späteren Kalendertag, ist
  diese eine Zeile vor dem Tag zu heben.
- Für Plan 16-04: das lokal gebaute Paket hat **47349 Bytes**. Das veröffentlichte Asset wird
  eine andere Größe und einen anderen sha256 haben, `tar.gz` ist nicht bytereproduzierbar.
  Signiert wird ausschließlich das heruntergeladene Asset.

## Self-Check: PASSED

- `.planning/phases/16-release-0-1-11/16-02-SUMMARY.md` existiert auf der Platte
- `8a2b123` ist in `git log --oneline --all` vorhanden
- Alle 13 Akzeptanzkriterien aus Task 1 und alle 11 aus Task 2 wurden ausgeführt und mit ihrer
  Ausgabe geloggt; keines blieb ungeprüft, keines wurde umgedeutet
- Plan-Verifikation: sechs Gates Exit 0, 15712 über 21 gegen 18000, leerer Diff über die beiden
  Gate-Dateien, ein Top-Level-Ordner, vier Manifest-Zählungen wie erwartet, drei Proof-Zeilen
  mit `3 0` im numstat, CRLF-Zählung 0, `git status --short dist` leer, `git tag --list v0.1.11` leer

---
*Phase: 16-release-0-1-11*
*Completed: 2026-08-28*
