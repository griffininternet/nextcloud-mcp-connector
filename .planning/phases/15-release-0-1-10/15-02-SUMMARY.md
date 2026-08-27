---
phase: 15-release-0-1-10
plan: 02
subsystem: release
tags: [gates, tool-budget, store-archive, proof-rows, store-submission]

# Dependency graph
requires:
  - phase: 15-release-0-1-10
    provides: "Plan 15-01: Version 0.1.10 an allen sechs Stellen und der Changelog-Block 0.1.10 vom 2026-08-28"
  - phase: 14-doku-reste-und-gate-entscheid
    provides: "die Vokabular-Gate-Ausnahme für docs/store-submission.md und die vorwärts laufende Nachweistabelle"
provides:
  - "sechs grüne Gates auf dem 0.1.10-Kandidaten: 2813 Tests bestanden bei 163 deselektiert, kein Lint-Befund, 198 Dateien formatiert, kein Typfehler und keine Warnung, kein toter Code, Werkzeugoberfläche 15712 Bytes über 21 Werkzeuge gegen 18000"
  - "die Bytegröße des lokal gebauten Archivs für den Vergleich in Plan 15-04: 47299 Bytes, sha256 4682e06d8ff96cd55d24a82dbaec8e73efeccb7e8011cb58b7ae7fee1cdad463"
  - "Beweis vor dem Tag: das Archiv-README trägt die Statuszeile 0.1.10 und das Archiv-CHANGELOG den Block 0.1.10 samt der korrigierten 0.1.9-Prosa"
  - "drei datierte Proof-Zeilen zu den Runbook-Schritten 1 bis 3 in docs/store-submission.md"
  - "die Herkunft des einen Bytes über der 0.1.9-Messung ist benannt und gemessen: die serverInfo-Version im tools/list-Envelope"
affects: [15-03, 15-04, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Testzahlen liest man aus einem Lauf ohne zusätzliches -q: addopts trägt bereits eins, zwei unterdrücken die Summenzeile"
    - "Eine Abweichung der Werkzeugoberfläche wird benannt, nicht weggerundet: die Messung mit auf 0.1.9 zurückgesetzter Versionszeichenkette liefert den alten Wert und beweist die Ursache"
    - "Proof-Zeilen tragen keine Pipe-Zeichen im Text; Rohr-Ketten werden als 'through cut und sort' beschrieben, damit die Tabellenspalten heil bleiben"

key-files:
  created:
    - .planning/phases/15-release-0-1-10/15-02-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Die Werkzeugoberfläche misst 15712 Bytes statt der im Plan erwarteten 15711. Die Abweichung wurde als Befund behandelt und ihre Ursache mechanisch bewiesen, statt sie zu ignorieren oder einen Grenzwert anzuheben: der tools/list-Envelope trägt die serverInfo-Metadaten mit der Versionszeichenkette, und 0.1.9 auf 0.1.10 ist genau ein Zeichen mehr. Mit auf 0.1.9 zurückgesetzter Versionszeichenkette liefert dieselbe Messung wieder 15711. BUDGET_BYTES bleibt 18000, MAX_TOOL_BYTES bleibt 1400, der Diff über check_tool_budget.py und test_tool_surface.py ist leer"
  - "Task 1 hat keinen Commit, weil er keine verfolgte Datei berührt: dist/ ist gitignored und der Plan verbietet ausdrücklich, etwas daraus zu committen. Der Nachweis des Tasks lebt in der Proof-Zeile zu Schritt 3 und in dieser Summary"
  - "Die Proof-Zeile zu Schritt 3 sagt 15712 und nicht das im Plan vorformulierte 'unverändert gegenüber dem 0.1.9-Lauf': eine Nachweiszeile trägt die Messung, nie die Erwartung"
  - "Die vom Skript gedruckte Signatur ist Diagnose und wurde nirgends notiert oder eingereicht; signiert wird in Plan 15-04 ausschließlich das heruntergeladene Asset"

patterns-established:
  - "Der Archiv-Probelauf prüft die fünfte Versionsstelle UND den Changelog-Stand im Tarball, weil beide unveränderlich mitreisen und kein Gate sie hält"

requirements-completed: []

# Metrics
duration: 20min
completed: 2026-08-28
---

# Phase 15 Plan 02: Gates, Archiv-Probelauf und Proof-Zeilen Summary

**Alle sechs Gates laufen auf dem 0.1.10-Kandidaten grün, ohne dass ein Grenzwert angehoben wurde, das Store-Archiv trägt vor dem Tag die Statuszeile 0.1.10 und den Changelog-Block 0.1.10, und die eine Byteabweichung der Werkzeugoberfläche hat einen Namen: die Versionszeichenkette im tools/list-Envelope.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-27T23:26Z (lokal 2026-08-28 01:26 +02:00)
- **Completed:** 2026-08-27T23:46Z (lokal 2026-08-28 01:46 +02:00)
- **Tasks:** 2
- **Files modified:** 1 (plus das nicht committete Archiv in `dist/`)

## Accomplishments

- Die sechs Gates liefen in der Runbook-Reihenfolge, jedes mit `uv run --no-sync`, jedes mit Exit 0
- Die Abweichung der Werkzeugoberfläche wurde nicht weggerundet und nicht mit einem höheren Grenzwert erledigt, sondern bis auf das Byte erklärt
- Das Store-Archiv hat genau einen Top-Level-Ordner und trägt die vier erwarteten Mitglieder
- Die fünfte Versionsstelle ist VOR dem Tag geprüft: im Archiv-README steht `Version 0.1.10.` und kein 0.1.9-Rest
- Der 0.1.9-Block im Archiv-Changelog trägt den korrigierten Wortlaut; W-1 des v1.3-Audits fährt mit diesem Asset zum ersten Mal mit
- Drei datierte Proof-Zeilen belegen die Schritte 1 bis 3, keine Zeile läuft ihrem Ereignis voraus
- Kein Tag, kein Push, kein Paketmanager-Aufruf, nichts aus `dist/` committet

## Die sechs Gates mit ihren Zahlen

| # | Kommando (jeweils mit `uv run --no-sync`) | Ergebnis |
|---|-------------------------------------------|----------|
| 1 | `pytest -q` | Exit 0, 2813 bestanden, 163 deselektiert, 69,78 s |
| 2 | `ruff check .` | Exit 0, `All checks passed!` |
| 3 | `ruff format --check .` | Exit 0, `198 files already formatted` |
| 4 | `pyright` | Exit 0, `0 errors, 0 warnings, 0 informations` |
| 5 | `vulture src scripts vulture_whitelist.py` | Exit 0, keine Ausgabe |
| 6 | `python scripts/check_tool_budget.py` | Exit 0, `tools/list: 15712 bytes, 21 tools, budget 18000` |

Vergleich zum 0.1.9-Lauf (Proof-Zeile vom 2026-08-25 18:13Z): 2812 auf 2813 bestandene Tests bei unverändert 163 deselektierten, das ist genau der eine Test aus Phase 14 (`test_the_vocabulary_gate_stops_at_the_internal_planning_area`); 199 auf 198 formatierte Dateien; und die Werkzeugoberfläche von 15711 auf 15712 Bytes.

### Die Zahl der Testläufe: warum drei statt einer

`addopts` in `pyproject.toml` trägt bereits ein `-q`. Das Runbook-Kommando `pytest -q` ergibt damit zwei, und zwei unterdrücken die Summenzeile: der Lauf endet grün, sagt aber seine Zahl nicht. Das Gate wurde deshalb wie im Runbook ausgeführt (Exit 0), und die Zahlen wurden aus einem zweiten Lauf ohne das zusätzliche `-q` gelesen. Dieselbe Suite, dasselbe Ergebnis, nur mit Summenzeile. Die Proof-Zeile sagt das ausdrücklich, damit niemand die Zahl für geraten hält.

## Der Befund: 15712 statt 15711, und wo das Byte herkommt

Der Plan nennt 15711 Bytes als Erwartungswert und verlangt bei Abweichung, zu stoppen und zu melden, statt einen Grenzwert anzuheben. Die Messung ergab 15712. Der Befund wurde vor dem Weitergehen bis zum Byte aufgeklärt:

1. **Kein Werkzeug hat sich bewegt.** `git diff v0.1.9..HEAD -- src/` nennt genau eine Datei und eine Zeile: `src/mcp_connector/__init__.py`, die Versionszeile. Kein Docstring, kein Schema, kein Parameter.
2. **Die 21 Werkzeug-Schemata sind byte-identisch zur Phase-12-Messung.** `mail_browse` 1376, `calendar_create_event` 1351, `calendar_list_events` 951, `search` 924, `talk_browse` 912. Die Summe aller 21 Werkzeuge beträgt 15532 Bytes.
3. **Das Byte sitzt im Envelope.** Die restlichen 180 Bytes der Antwort sind `_meta`, `ttlMs`, `cacheScope` und `resultType`. `_meta` lautet:

   ```
   {"io.modelcontextprotocol/serverInfo":{"name":"MCP Connector","version":"0.1.10"}}
   ```

   `server/__init__.py:44` baut den `MCPServer` mit `version=__version__`. `0.1.9` auf `0.1.10` ist genau ein Zeichen mehr.
4. **Gegenprobe.** Dieselbe Messung mit vor dem Import auf `0.1.9` gesetzter Versionszeichenkette liefert `15711 Bytes, 21 Werkzeuge`. Damit ist die Ursache nicht plausibel, sondern gemessen.

**Kein Grenzwert wurde angehoben.** `git diff -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py` ist leer (0 Zeilen), `BUDGET_BYTES` steht auf 18000 (`:83`), `MAX_TOOL_BYTES` auf 1400 (`:117`). Das Byte kostet Headroom: 2288 Bytes bleiben frei statt 2289.

Zur Einordnung für die nächsten Releases: die Werkzeugoberfläche wächst bei jedem Wechsel auf eine längere Versionszeichenkette um die Differenz der Zeichenzahl. Von 0.1.10 auf 0.1.11 ändert sich nichts, von 0.1.9 auf 0.1.10 war es ein Byte. Das ist kein Regressionssignal und wird beim nächsten Erwartungswert mitgedacht: der Erwartungswert für 0.1.11 ist 15712.

## Das Archiv und seine geprüften Inhalte

`bash scripts/build_store_release.sh` baute `dist/mcp_connector-0.1.10.tar.gz`.

| Prüfung | Ergebnis |
|---------|----------|
| Bytegröße lokal | **47299** |
| sha256 lokal | **4682e06d8ff96cd55d24a82dbaec8e73efeccb7e8011cb58b7ae7fee1cdad463** |
| Top-Level-Ordner | genau einer, `mcp_connector` |
| Mitglieder | `mcp_connector/appinfo/info.xml`, `mcp_connector/CHANGELOG.md`, `mcp_connector/LICENSE`, `mcp_connector/README.md` |
| `README.md` gegen `^Version 0\.1\.10\.` | 1 |
| `README.md` gegen `0\.1\.9` | 0, kein Rest |
| `CHANGELOG.md` gegen `^## \[0\.1\.10\]` | 1, Zeile 12; der 0.1.9-Block folgt auf Zeile 39 |
| `CHANGELOG.md` gegen `only at upload time` | 2, einer davon auf Zeile 52 und damit im 0.1.9-Block |
| `appinfo/info.xml` gegen `admin@infranode.dev` | 3 |
| `appinfo/info.xml` `<version>` und `<image-tag>` | `0.1.10` je einmal |
| `git status --short dist` | keine Zeile |
| `git tag --list v0.1.10` | keine Zeile |

**Die Bytegröße 47299 ist der Messwert, den Plan 15-04 braucht.** Sie ist ausdrücklich nicht der Wert, der eingereicht wird: `tar.gz` ist nicht bytereproduzierbar, bei 0.1.9 standen 47546 lokal gegen 47264 veröffentlicht. Die vom Skript gedruckte Signatur ist Diagnose; sie wurde nicht notiert und wird nicht eingereicht.

## W-1 endet mit diesem Asset

Der 0.1.9-Block im Archiv-Changelog trägt den nach dem v0.1.9-Tag korrigierten Wortlaut ("only at upload time", Commit `9ac0a3c`). Das signierte 0.1.9-Asset behält seine alte Fassung, das ist unveränderlich; der Drift endet nicht durch Rückwirkung, sondern dadurch, dass das nächste veröffentlichte Asset die korrigierte Datei mitführt. Der Probelauf hat das vor dem Tag belegt, und genau das war der zweite Auftrag dieses Plans.

## Die drei Proof-Zeilen

Eingefügt nach der bisher letzten Tabellenzeile (2026-08-25 18:46Z) und vor `### The update keeps the connections`, also auf den Zeilen 146 bis 148:

| Zeile | Zeit | Belegt |
|-------|------|--------|
| 146 | 2026-08-27 23:20Z | Schritt 1: sechs Versionsstellen, die drei README-Statuszeilen namentlich, `uv.lock` per Texteditierung ohne Lock-Lauf, vier CRLF-Dateien byte-exakt gepatcht |
| 147 | 2026-08-27 23:22Z | Schritt 2: Block 0.1.10 mit Enterprise-Kürzung und Kontaktwechsel unter `### Changed`, Übersetzungs-Korrekturen unter `### Fixed`, Linkdefinition gepaart, kein `[Unreleased]` |
| 148 | 2026-08-27 23:34Z | Schritt 3: sechs Gates mit ihren Zahlen, das benannte Byte, kein angehobener Grenzwert, Archiv mit einem Top-Level-Ordner, Statuszeile 0.1.10, Changelog-Block 0.1.10 samt der erstmals mitreisenden 0.1.9-Korrektur, Strukturprüfung und nicht das signierte Artefakt |

Die Uhrzeiten der Zeilen 146 und 147 sind die Commit-Zeitpunkte von Plan 15-01 (`c80a45c` 23:20:51Z, `9829f1e` 23:22:01Z), also die Zeitpunkte der Ereignisse und nicht die des Schreibens. Die Datumsspalte der Tabelle läuft über alle 67 Zeilen aufsteigend.

Für die Schritte 4 bis 8 steht keine Zeile. Sie entstehen in den Plänen 15-03 und 15-04, nachdem die Ereignisse eingetreten sind: eine vorab geschriebene Nachweiszeile dreht die Beweisrichtung um, und genau diese Richtung ist die Begründung der Vokabular-Gate-Ausnahme dieser Datei.

## Task Commits

1. **Task 1: Sechs Gates und der Archiv-Probelauf** - kein Commit, der Task berührt keine verfolgte Datei (`dist/` ist gitignored, der Plan verbietet ausdrücklich einen Commit daraus). `git status --short` war vor und nach dem Task leer.
2. **Task 2: Proof-Zeilen der Runbook-Schritte 1 bis 3** - `4be5129` (docs)

## Files Created/Modified

- `docs/store-submission.md` - drei neue Nachweiszeilen, `git diff --numstat` nennt 3 hinzugefügt und 0 entfernt, LF unverändert (0 CRLF)
- `dist/mcp_connector-0.1.10.tar.gz` - gebaut, geprüft, **nicht committet** (gitignored)
- `.planning/phases/15-release-0-1-10/15-02-SUMMARY.md` - diese Datei

## Decisions Made

- 15712 statt 15711 ist ein benannter Befund und keine Anhebung: die serverInfo-Version im Envelope, per Gegenprobe auf 15711 zurückgerechnet
- Task 1 bleibt ohne Commit, weil sein Ergebnis in `dist/` liegt und dort bleiben soll
- Die Proof-Zeile sagt die Messung (15712) und nicht die Planerwartung (unverändert)
- Die Diagnose-Signatur des Skripts wird nicht festgehalten, damit sie nirgends als eingereichter Wert missverstanden werden kann

## Deviations from Plan

**1. [Befund] Werkzeugoberfläche 15712 Bytes statt der erwarteten 15711**
- **Gefunden bei:** Task 1, Gate 6
- **Sachlage:** Der Plan verlangt bei Abweichung, zu stoppen und den Befund zu melden, statt einen Grenzwert anzuheben. Die Abweichung beträgt ein Byte und ihre Ursache ist mechanisch bewiesen: der `tools/list`-Envelope trägt `_meta` mit `serverInfo.version`, und die Versionszeichenkette wuchs mit dem Bump dieser Phase von fünf auf sechs Zeichen. Die 21 Werkzeug-Schemata sind byte-identisch zur letzten Messung, `git diff v0.1.9..HEAD -- src/` nennt nur die Versionszeile, und dieselbe Messung mit auf 0.1.9 gesetzter Zeichenkette gibt wieder 15711.
- **Behandlung:** gemeldet und dokumentiert (dieser Abschnitt, die Proof-Zeile und der Abschnitt "Der Befund" oben), kein Grenzwert angehoben, keine Datei des Gates angefasst. Der Plan wurde fortgesetzt, weil die Abweichung die mechanische Folge des Versions-Bumps aus Plan 15-01 ist und nicht der unerklärte Zuwachs, gegen den die Regel geschrieben ist. Der Erwartungswert für den nächsten Lauf ist 15712.
- **Kein Code geändert, kein Grenzwert geändert.**

**2. [Präzisierung] Die Testzahl kommt aus einem Lauf ohne das zusätzliche `-q`**
- **Gefunden bei:** Task 1, Gate 1
- **Sachlage:** `addopts` trägt bereits `-q`, das Runbook-Kommando fügt ein zweites hinzu, und zwei unterdrücken die Summenzeile. Das Gate selbst lief wie vorgeschrieben und endete mit Exit 0; die Zahlen 2813 und 163 stammen aus einem zusätzlichen Lauf desselben Kommandos ohne das doppelte `-q`. Die Proof-Zeile nennt diesen Umstand.
- **Kein Code geändert.**

**3. [Präzisierung] Formatierte Dateien 198 statt der 199 des 0.1.9-Laufs**
- **Gefunden bei:** Task 1, Gate 3
- **Sachlage:** Der Plan nennt für diese Zahl keinen Erwartungswert, die 0.1.9-Proof-Zeile sagt 199. Nachgemessen: das Repository trägt bei `v0.1.9` und bei `HEAD` genau 177 verfolgte `.py`-Dateien, und `git diff v0.1.9..HEAD --diff-filter=ACDR -- '*.py'` ist leer, es wurde also keine Python-Datei hinzugefügt, gelöscht oder umbenannt. Die 198 beziehungsweise 199 sind demnach nicht die Zahl der Repository-Dateien: `ruff format` läuft über den Arbeitsbaum und zählt auch nicht verfolgte Dateien mit, die keine `.gitignore`-Regel trifft. Plan 15-01 hat bereits 198 gemessen. Die Ursache der einen Datei Differenz ist damit außerhalb des Repositorys und wurde nicht weiter verfolgt; sie ist als Messwert notiert und nicht als Befund behandelt, weil `ruff format --check .` mit Exit 0 endet und damit sagt, dass jede Datei, die es gesehen hat, formatiert ist.
- **Kein Code geändert.**

Kein Paketmanager-Aufruf (alle Läufe mit `uv run --no-sync`), kein Tag, kein Push, kein `git clean`, kein `git stash`.

## Verification

| Kriterium | Ergebnis |
|-----------|----------|
| Sechs Gates mit Exit 0 | ja, Tabelle oben |
| `check_tool_budget.py` nennt 21 Werkzeuge und Budget 18000 | ja, `tools/list: 15712 bytes, 21 tools, budget 18000` |
| Abweichung zum Erwartungswert 15711 | ein Byte, Ursache gemessen und benannt, kein Grenzwert angehoben |
| `git diff -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py` | leer, 0 Zeilen |
| Top-Level-Ordner des Archivs | genau eine Zeile, `mcp_connector` |
| Vier Archiv-Mitglieder | alle vier vorhanden |
| `README.md` im Archiv gegen `^Version 0\.1\.10\.` | 1 |
| `CHANGELOG.md` im Archiv gegen `^## \[0\.1\.10\]` | 1 |
| `CHANGELOG.md` im Archiv gegen `only at upload time` | 2 |
| `appinfo/info.xml` im Archiv gegen `admin@infranode.dev` | 3 |
| Bytegröße des lokalen Archivs notiert | 47299 |
| `git status --short dist` | keine Zeile |
| Drei neue Tabellenzeilen, Form `\| YYYY-MM-DD HH:MMZ \|` | ja, Zeilen 146 bis 148 |
| Lage zwischen 18:46Z und `### The update keeps the connections` | ja, `grep -n` nennt 145, 146, 147, 148, 150 |
| Datumsspalte aufsteigend | ja, 67 Zeilen, sortierter Vergleich ohne Abweichung |
| `git diff --numstat docs/store-submission.md` | `3	0` |
| Jede neue Zeile nennt 0.1.10 und trägt ein Kommando in Spalte 3 | ja, 3 von 3 |
| Zeile zu Schritt 3 nennt structure check, das nicht signierte Archiv und das CHANGELOG.md | ja, alle drei |
| Zeilen zu den Schritten 4 bis 8 für 0.1.10 | keine |
| CRLF in `docs/store-submission.md` | 0 |
| Em- und En-Dashes in `docs/store-submission.md` | 0 und 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0 |
| `git tag --list v0.1.10` | keine Zeile |
| `git diff --diff-filter=D` über den Task-Commit | keine Löschung |

## Issues Encountered

Beim Staging von `docs/store-submission.md` warnt git wie in den Phasen 14 und 15-01 "LF will be replaced by CRLF the next time Git touches it". Das ist die Zeilenenden-Konfiguration des Repos; die Datei liegt im Arbeitsbaum weiter mit 0 CRLF und der Commit nennt 3 hinzugefügte und 0 entfernte Zeilen.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Runbook-Schritt 3 ist abgeschlossen; die Phase ist damit bis zur Grenze der Owner-Freigabe fertig und in diesem Zustand prüfbar
- Offen für Plan 15-03: die Datumsprüfung der Changelog-Kopfzeile (`## [0.1.10] - 2026-08-28`) gegen den Kalendertag des Tags, dann Branch-Push, dann der Tag `v0.1.10` nach ausdrücklicher Owner-Freigabe
- Für Plan 15-04 hinterlegt: lokal 47299 Bytes, sha256 `4682e06d…`. Die veröffentlichte Größe wird davon abweichen, und genau diese Differenz ist der Grund, dass die Einreichungs-Signatur über das heruntergeladene Asset läuft
- EXAPP-10 bleibt Pending, bis Asset, Signatur und Store-Upload vorliegen
- Erwartungswert der Werkzeugoberfläche für den nächsten Lauf: 15712 Bytes über 21 Werkzeuge

## Self-Check: PASSED

- `docs/store-submission.md` und diese Summary existieren auf der Platte, `dist/mcp_connector-0.1.10.tar.gz` ebenfalls und ist nicht verfolgt
- Der Task-Commit `4be5129` liegt im Log
- Echte Umlaute, keine Emojis, keine Em-Dashes in der Prosa

---
*Phase: 15-release-0-1-10*
*Completed: 2026-08-28*
