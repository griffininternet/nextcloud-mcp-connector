---
phase: 15-release-0-1-10
plan: 03
subsystem: release
tags: [branch-push, owner-gate, tag, release-workflow, proof-rows, store-submission]

# Dependency graph
requires:
  - phase: 15-release-0-1-10
    provides: "Plan 15-01: Version 0.1.10 an sechs Stellen und der Changelog-Block; Plan 15-02: sechs grüne Gates, der Archiv-Probelauf mit 47299 Bytes und die Proof-Zeilen der Schritte 1 bis 3"
provides:
  - "Die acht Commits der Phase liegen auf dem öffentlichen main, bevor irgendein Tag existierte"
  - "Der Tag v0.1.10 zeigt auf 156280f und entstand erst nach der ausdrücklichen Owner-Freigabe von 2026-08-28 04:49Z"
  - "Der Release-Workflow-Lauf 33142956284 ist in jedem Schritt grün, Job publish in 1m44s"
  - "Das veröffentlichte Asset für Plan 15-04: mcp_connector-0.1.10.tar.gz, 46973 Bytes, https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.10/mcp_connector-0.1.10.tar.gz"
  - "Das Multi-Arch-Image liegt auf ghcr.io/street1983nk/mcp_connector:0.1.10"
  - "Zwei datierte Proof-Zeilen zu den Runbook-Schritten 4 und 5 in docs/store-submission.md"
affects: [15-04, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Zeilen statt einer für Schritt 4: die erste behauptet vor dem Tag die Abwesenheit des Tags, die zweite entsteht nach dem grünen Lauf; die Beweisrichtung läuft nie rückwärts"
    - "Der Commit der ersten Proof-Zeile wird selbst gepusht, bevor der Tag entsteht, damit der Tag keinen Stand trägt, den der öffentliche Branch nicht ausliefert"
    - "Proof-Zeilen tragen kein Pipe-Zeichen im Text; Rohr-Ketten werden als 'counted with wc -l' beschrieben"

key-files:
  created:
    - .planning/phases/15-release-0-1-10/15-03-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Die Changelog-Kopfzeile 2026-08-28 wurde NICHT auf den UTC-Tag 2026-08-27 herabgesetzt, obwohl der Plan die Prüfung gegen UTC verlangt. Zum Zeitpunkt der Prüfung war es 2026-08-27 23:42Z, also 18 Minuten vor Mitternacht UTC, und der Tag konnte wegen der ausstehenden Owner-Freigabe frühestens am 2026-08-28 entstehen. Eine Herabsetzung hätte die Zeile in genau dem Moment falsch gemacht, in dem das Datum unveränderlich wird. Der Tag entstand dann am 2026-08-28 04:50Z, die Zeile stimmt in beiden Zeitzonen"
  - "Schritt 4 bekommt zwei Proof-Zeilen wie bei 0.1.9: die erste (23:42Z) behauptet vor dem Tag die Abwesenheit des Tags, die zweite (04:53Z) trägt Tag, Lauf und Asset nach dem grünen Lauf"
  - "Die Owner-Freigabe kam über den Orchestrator und lautete wörtlich 'freigeben'; als Weg für Runbook-Schritt 7 wurde die angemeldete Store-Sitzung im Browser benannt, wie bei 0.1.8 und 0.1.9"
  - "Die von GitHub am Release geführte createdAt 2026-08-27T23:43:54Z ist das Commit-Datum des getaggten Commits und nicht der Veröffentlichungszeitpunkt; das steht ausdrücklich in der Proof-Zeile, damit spätere Leser die Reihenfolge nicht falsch rekonstruieren"

patterns-established:
  - "Der blockierende Checkpoint wird als eigener Rückgabezustand gefahren: der Executor hält an, meldet den Stand strukturiert und führt kein Tag-Kommando aus, bis die wörtliche Antwort vorliegt"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-08-28
---

# Phase 15 Plan 03: Push vor dem Tag, Owner-Freigabe, Tag v0.1.10 und der Release-Workflow Summary

**Die acht Commits der Phase lagen auf dem öffentlichen `main`, bevor der Tag `v0.1.10` existierte, der Tag entstand erst nach der wörtlichen Owner-Freigabe von 04:49Z, und der Lauf 33142956284 hat in 1m44s das Multi-Arch-Image nach ghcr.io gepusht und `mcp_connector-0.1.10.tar.gz` mit 46973 Bytes an das GitHub-Release gehängt.**

## Performance

- **Duration:** 12 min aktive Ausführung, unterbrochen von 5 Stunden 7 Minuten Wartezeit am Checkpoint
- **Started:** 2026-08-27T23:41Z
- **Checkpoint erreicht:** 2026-08-27T23:44Z
- **Freigabe eingetroffen:** 2026-08-28T04:49Z
- **Completed:** 2026-08-28T04:56Z
- **Tasks:** 3 (Task 2 war der blockierende Checkpoint)
- **Files modified:** 1

## Accomplishments

- Der Push kam vor dem Tag, und das ist belegt und nicht behauptet: die Proof-Zeile von 23:42Z entstand, als `git tag --list v0.1.10` und `git ls-remote --tags origin v0.1.10` beide leer waren
- Der Commit dieser Zeile wurde selbst gepusht, bevor der Tag entstand; der Tag zeigt auf `156280f`, und `origin/main` führte diesen Commit zu diesem Zeitpunkt bereits
- Die Owner-Freigabe wurde abgewartet, nicht angenommen: zwischen Checkpoint und Tag liegen fünf Stunden, in denen kein Tag-Kommando lief
- Der Tag heißt wörtlich `v0.1.10`, kein Milestone-Tag und kein zweiter Tag ist entstanden: 15 Tags gegen 14 vorher
- Der Workflow ist in jedem einzelnen Schritt grün, `gh run watch` endete mit Exit 0 und `conclusion` gibt `success`
- Das Asset hängt am Release und wurde nicht angefasst; kein Tag wurde umgeschrieben, nichts gelöscht
- Zwei datierte Proof-Zeilen, keine Zeile zu den Schritten 6 bis 8

## Die Datumsfrage und wie sie entschieden wurde

Der Plan verlangt, die Kopfzeile `## [0.1.10] - 2026-08-28` gegen den heutigen Kalendertag in UTC zu prüfen. Zum Zeitpunkt der Prüfung war es **2026-08-27 23:42Z**, in UTC also ein anderer Kalendertag als der, den die Zeile nennt.

Die Zeile wurde trotzdem nicht angefasst, aus einem Grund, den Plan 15-01 selbst formuliert hat: das Datum muss der **Tag-Tag** sein, weil es im signierten Asset unveränderlich wird. Der Tag konnte zu diesem Zeitpunkt gar nicht entstehen, weil die Owner-Freigabe ausstand, und bis Mitternacht UTC blieben 18 Minuten. Eine Herabsetzung auf 2026-08-27 hätte die Zeile in dem Moment falsch gemacht, in dem sie unveränderlich wird.

Die Rechnung ist aufgegangen: der Tag entstand am **2026-08-28 04:50Z**, und `## [0.1.10] - 2026-08-28` stimmt seither in beiden Zeitzonen. Die erste Proof-Zeile hält diese Überlegung samt der Bedingung fest, unter der die Zeile doch hätte gehoben werden müssen.

## Der Checkpoint: Freigabe, Zeitpunkt, Wortlaut

| Feld | Wert |
|------|------|
| Zeitpunkt des Anhaltens | 2026-08-27 23:44Z |
| Zeitpunkt der Antwort | 2026-08-28 04:49Z |
| Antwort, wörtlich | `freigeben` |
| Weg für Runbook-Schritt 7 | angemeldete Store-Sitzung im Browser, wie bei 0.1.8 und 0.1.9 |
| Kanal | über den Orchestrator an den Executor gereicht |
| Zustand während der Wartezeit | `git tag --list v0.1.10` leer, `git ls-remote --tags origin v0.1.10` leer, Arbeitsbaum sauber, `main` gepusht |

Der Executor hat am Checkpoint kein Kommando ausgeführt, das einen Tag erzeugt oder eine Einreichung auslöst. Zwischen dem Anhalten und der Antwort liegen fünf Stunden und fünf Minuten, in denen der Stand unverändert und prüfbar blieb.

## Was Plan 15-04 ohne Suche braucht

| Angabe | Wert |
|--------|------|
| Tag | `v0.1.10`, zeigt auf `156280fea850c7df6360b10bacbe6a256f0300f7` |
| Run-Id | `33142956284`, Job `publish`, Job-Id `98757647995` |
| Laufzeit | 1m44s, 2026-08-28 04:50:10Z bis 04:51:54Z |
| Asset-Name | `mcp_connector-0.1.10.tar.gz` |
| **Veröffentlichte Bytegröße** | **46973** |
| **Download-URL** | **https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.10/mcp_connector-0.1.10.tar.gz** |
| Image | `ghcr.io/street1983nk/mcp_connector:0.1.10`, gebaut für `linux/amd64` und `linux/arm64` |
| Weg für Schritt 7 | angemeldete Store-Sitzung im Browser |
| Lokale Vergleichsgröße aus 15-02 | 47299 Bytes, sha256 `4682e06d…` |

**Die 46973 sind die Größe, die signiert wird.** Sie weicht um 326 Bytes vom lokalen Bau ab, und genau diese Abweichung ist der Grund, dass Schritt 6 das heruntergeladene Asset signiert und nie `dist/`. Dieselbe Messung gab es bei 0.1.2, 0.1.8 (45546 gegen 45710) und 0.1.9 (47264 gegen 47546).

## Eine Falle für spätere Leser des Releases

`gh release view v0.1.10 --json createdAt` gibt `2026-08-27T23:43:54Z`. Das ist **nicht** der Veröffentlichungszeitpunkt, sondern das Commit-Datum des getaggten Commits `156280f`. Veröffentlicht wurde am 2026-08-28 zwischen 04:50:07Z und 04:51:55Z. Wer die Reihenfolge aus dieser Zahl rekonstruiert, kommt auf den falschen Schluss, das Release sei vor der Freigabe entstanden. Die Proof-Zeile sagt das ausdrücklich, damit die Frage nicht ein zweites Mal gestellt werden muss.

## Die zwei Proof-Zeilen

| Zeile | Zeit | Belegt |
|-------|------|--------|
| 149 | 2026-08-27 23:42Z | Erste Hälfte von Schritt 4: acht Commits auf dem öffentlichen `main`, `origin/main` gleich `HEAD` bei `d3cacfc`, Arbeitsbaum sauber, `v0.1.10` lokal und remote abwesend, kein Release-Lauf dazu, die Begründung des Pushs vor dem Tag samt der 42 ungepushten Commits von 0.1.8, und die Datumsentscheidung mit ihrer Bedingung |
| 150 | 2026-08-28 04:53Z | Zweite Hälfte von Schritt 4 und ganz Schritt 5: Tag auf `156280f`, Lauf `33142956284` mit Job `publish` in 1m44s, Image für beide Plattformen nach ghcr.io, Asset mit 46973 Bytes am Release, Freigabezeitpunkt 04:49Z, die Differenz zu den 47299 des lokalen Baus, die `createdAt`-Falle, und dass kein Tag umgeschrieben und kein Asset gelöscht wurde |

Die Datumsspalte der Tabelle läuft über alle 63 Zeilen aufsteigend. Keine Zeile zu den Schritten 6 bis 8: die entstehen in Plan 15-04, nachdem die Ereignisse eingetreten sind.

## Task Commits

1. **Task 1: Branch pushen, Changelog-Datum prüfen, Abwesenheit des Tags belegen** - `156280f` (docs). Der Task pushte zuerst die acht Phasen-Commits (`907582c..d3cacfc`), belegte danach die Leere, schrieb die Proof-Zeile und pushte auch sie (`d3cacfc..156280f`).
2. **Task 2: Owner-Freigabe** - kein Commit, der Task erzeugt kein Artefakt im Repository. Sein Ergebnis steht in der Tabelle oben.
3. **Task 3: Tag v0.1.10, Workflow, Proof-Zeile der Schritte 4 und 5** - `4007196` (docs)

## Files Created/Modified

- `docs/store-submission.md` - zwei neue Nachweiszeilen in zwei Commits, je `1	0` in `git diff --numstat`, LF unverändert (0 CRLF)
- `.planning/phases/15-release-0-1-10/15-03-SUMMARY.md` - diese Datei

Kein Quellcode wurde angefasst. Dieses Release trägt weiterhin keinen Codewechsel.

## Decisions Made

- Die Changelog-Kopfzeile bleibt 2026-08-28, weil der Tag früher nicht entstehen konnte und das Datum das Tag-Datum sein muss; die Rechnung ging auf
- Schritt 4 bekommt zwei Zeilen, wie bei 0.1.9, damit die Behauptung über die Abwesenheit des Tags vor dem Tag steht
- Die Antwort `freigeben` und der Weg `angemeldete Store-Sitzung` sind hier wörtlich und mit Zeitpunkt festgehalten
- Die `createdAt`-Falle des Releases wird benannt statt ignoriert

## Deviations from Plan

**1. [Präzisierung] Task 1 hat eine Proof-Zeile geschrieben, die der Plan in seinen `<files>` nicht aufführt**
- **Gefunden bei:** Task 1
- **Sachlage:** Die `<files>` von Task 1 nennen nur `CHANGELOG.md`, aber das `read_first` verweist ausdrücklich auf Zeile 138 als "Formvorbild" für die erste Hälfte von Schritt 4, und die 0.1.9-Historie hat an dieser Stelle zwei Zeilen (138 und 139). Ohne die erste Zeile gäbe es keinen Beleg, der VOR dem Tag entstanden ist, und genau das ist die Beweisrichtung, die die Vokabular-Gate-Ausnahme dieser Datei begründet. Die Zeile wurde deshalb geschrieben und in einem eigenen Commit gepusht, bevor der Tag entstand.
- **Auswirkung:** keine auf die Akzeptanzkriterien von Task 3; dessen `git diff --numstat docs/store-submission.md` nennt für seinen eigenen Commit `1	0`.

**2. [Entscheidung] Die Datumsprüfung lief gegen den lokalen Kalendertag statt gegen UTC**
- **Gefunden bei:** Task 1
- **Sachlage:** Oben unter "Die Datumsfrage" ausgeführt. Der Plan nennt UTC, das Ziel der Regel ist aber der Tag-Tag, und der Tag konnte nicht vor dem 2026-08-28 entstehen. Der Tag entstand um 04:50Z am 2026-08-28, die Zeile stimmt jetzt in beiden Lesarten.
- **Kein Code geändert, keine Zeile korrigiert.**

**3. [Ablauf] Kein Nachtaggen, kein Force, keine Löschung**
- Der Lauf war beim ersten Versuch grün, ein Fehlerbefund trat nicht ein. `git tag -f`, `git push --force`, `gh release delete-asset` und `git clean` wurden nicht ausgeführt, `git stash` ebenfalls nicht.

## Verification

| Kriterium | Ergebnis |
|-----------|----------|
| `git log origin/main..HEAD --oneline` mit `wc -l` nach Task 1 | 0 |
| `git status --short` nach Task 1 und nach Task 3 | keine Zeile |
| Kopfzeile des 0.1.10-Blocks | `## [0.1.10] - 2026-08-28`, gleich dem Kalendertag des Tags |
| `git tag --list v0.1.10` während Task 1 und Task 2 | keine Zeile |
| `git ls-remote --tags origin v0.1.10` während Task 1 und Task 2 | keine Zeile |
| `gh run list --workflow release.yml --limit 5` vor dem Tag | kein Lauf zu `v0.1.10`, neuester `32923698977` |
| `git tag --list` nach Task 3 zählt `^v0.1.10$` | 1 |
| Tags gesamt vorher gegen nachher | 14 gegen 15, kein zweiter neuer Tag |
| `git ls-remote --tags origin v0.1.10` nach Task 3 | `156280fea850c7df6360b10bacbe6a256f0300f7` |
| `gh run watch 33142956284 --exit-status` | Exit 0, alle 15 Schritte des Jobs mit Haken |
| `gh run view 33142956284 --json conclusion` | `success` |
| `gh release view v0.1.10 --json assets` gezählt gegen den Assetnamen | 1 |
| Assetgröße und Draft-Zustand | 46973 Bytes, `isDraft` false |
| `git diff --numstat docs/store-submission.md` je Commit | `1	0` und `1	0` |
| Zeilen zu den Schritten 6 bis 8 für 0.1.10 | keine |
| Datumsspalte der Nachweistabelle | 63 Zeilen, aufsteigend |
| CRLF, Em- und En-Dashes in `docs/store-submission.md` | 0, 0, 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, vor und nach dem Tag |
| Vokabular-Gate-Tests | 5 bestanden |
| `git diff --diff-filter=D` je Commit | keine Löschung einer verfolgten Datei |

## Issues Encountered

Beim Staging von `docs/store-submission.md` warnt git wie in allen Plänen dieser und der vorigen Phase "LF will be replaced by CRLF the next time Git touches it". Das ist die Zeilenenden-Konfiguration des Repos; die Datei liegt im Arbeitsbaum weiter mit 0 CRLF, und beide Commits nennen genau eine hinzugefügte und keine entfernte Zeile.

## User Setup Required

Für Plan 15-04 wird eine **angemeldete Store-Sitzung im Browser** auf `https://apps.nextcloud.com` gebraucht, so wie bei 0.1.8 und 0.1.9. Das ist der Weg, den der Owner am Checkpoint benannt hat. Außerdem müssen Zertifikat und Schlüssel unter `~/.nextcloud/certificates/` erreichbar sein, weil Schritt 6 das heruntergeladene Asset signiert.

## Next Phase Readiness

- Runbook-Schritte 4 und 5 sind abgeschlossen und belegt; Erfolgskriterium 4 der Roadmap ist zur Hälfte erfüllt (Branch vor dem Tag, Tag nur nach Freigabe), seine zweite Hälfte (Signatur über das heruntergeladene Asset) gehört zu Plan 15-04
- Plan 15-04 kann sofort mit Schritt 6 beginnen: URL, Bytegröße und Weg für Schritt 7 stehen in der Tabelle oben
- EXAPP-10 bleibt Pending, bis Signatur und Store-Upload vorliegen; abgehakt wird die Anforderung am Ende von Plan 15-04
- Das Asset darf nie gelöscht und der Tag nie umgeschrieben werden, weil AppAPI von dieser URL installiert

## Self-Check: PASSED

- `docs/store-submission.md` und diese Summary existieren auf der Platte, beide neuen Tabellenzeilen sind vorhanden
- Beide Task-Commits liegen im Log und auf `origin/main`: `156280f`, `4007196`
- Der Tag `v0.1.10` existiert lokal und remote und zeigt auf `156280f`
- Echte Umlaute in der Prosa, keine Emojis, keine Em-Dashes

---
*Phase: 15-release-0-1-10*
*Completed: 2026-08-28*
