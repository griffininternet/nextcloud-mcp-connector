---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 05
subsystem: infra
tags: [release, tag, github-actions, proof-lines, human-checkpoint, irreversible]

# Dependency graph
requires:
  - phase: 13
    plan: 01
    provides: "die sechs Versionsstellen auf 0.1.9 und den Changelog-Block, dessen Datumszeile dieser Plan gegen den Kalendertag des Tags gehalten hat"
  - phase: 13
    plan: 04
    provides: "die sechs grünen Gates auf dem 0.1.9-Kandidaten, den Archiv-Probelauf und die 47546 Bytes des lokal gebauten Pakets als Vergleichswert"
provides:
  - "der Branch main auf GitHub, gepusht bevor irgendein Tag existierte: dfee4f8..22471c1, danach 22471c1..685295d"
  - "die wörtliche Owner-Antwort freigeben vom 2026-08-25T18:27Z, samt dem Weg für Schritt 7 (angemeldete Store-Sitzung im Browser)"
  - "der Tag v0.1.9 lokal und remote auf 685295d, kein anderer Name, kein umgeschriebener Tag"
  - "der grüne Release-Lauf 32883904698, Job publish success in 1m40s: Multi-Arch-Image nach ghcr.io/street1983nk/mcp_connector:0.1.9 und das Store-Paket am GitHub-Release"
  - "das Release-Asset mcp_connector-0.1.9.tar.gz, 47264 Bytes, unter https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.9/mcp_connector-0.1.9.tar.gz"
  - "zwei datierte Proof-Zeilen in docs/store-submission.md: eine zum Push allein, eine zu Tag und Workflow; keine Zeile zu den Schritten 6 bis 8"
affects: [13-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die irreversible Grenze wird in zwei Hälften belegt: eine Proof-Zeile für den Push, bevor der Tag zur Entscheidung steht, und eine zweite für Tag und Workflow, erst nach dem grünen Lauf. Endet die Phase am Checkpoint mit warten, ist der Push trotzdem belegt und nicht unaufgezeichnet"
    - "Der Tag wird auf den Commit gesetzt, den origin/main schon trägt: git rev-parse --short v0.1.9 und git rev-parse --short origin/main sind vor dem Tag-Push dieselbe Zahl"

key-files:
  created:
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-05-SUMMARY.md
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/deferred-items.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Die Proof-Zeile zu Schritt 4 wurde in zwei Zeilen geteilt: eine für den Push vor dem Checkpoint, eine für Tag und Workflow danach. Der Plan sah eine gebündelte Zeile in Task 3 vor. Grund: zwischen Push und Tag liegt ein blockierender menschlicher Checkpoint, und bei der Antwort warten hätte der Push gar keine Zeile bekommen. Beide Zeilen behaupten nur Eingetretenes, die erste sagt ausdrücklich, dass sie die erste Hälfte ist und dass die Zeile zu Tag und Workflow erst nach dem grünen Lauf entsteht."
  - "Das Changelog-Datum blieb unangetastet: ## [0.1.9] - 2026-08-25 traf den Kalendertag des Tags in UTC (Messung 18:20Z, Tag 18:27Z). Task 1 hat deshalb keinen eigenen Commit, weil er keine Datei geändert hat."
  - "Der Tag zeigt auf 685295d und nicht auf den späteren Doku-Commit 3131a96. Die Proof-Zeile zu Tag und Workflow entsteht konstruktionsbedingt nach dem Lauf, kann also nicht im getaggten Stand liegen. Das Release-Paket enthält appinfo/info.xml, CHANGELOG.md, LICENSE und README.md; keine dieser vier Dateien wurde nach dem Tag angefasst."
  - "Die Node-20-Abkündigung des Workflow-Laufs wurde nicht gefixt, sondern in deferred-items.md protokolliert. Sie ist vorbestehend (auch beim 0.1.8-Lauf vorhanden), betrifft fünf fremde Actions und hätte eine Änderung an release.yml mitten in eine laufende Veröffentlichung gebracht."

patterns-established:
  - "Die Owner-Freigabe wird wörtlich und mit Zeitpunkt aufgenommen, samt dem Weg, den sie für den nächsten Plan freigibt; sie kommt über den Orchestrator und nicht aus einem Kommando"

requirements-completed: []  # EXAPP-09 bleibt Pending: sein Wortlaut verlangt das Release im Store, und der Store-Upload ist Schritt 7 in Plan 13-06

# Metrics
duration: 13min
completed: 2026-08-25
---

# Phase 13 Plan 05: Push, Owner-Freigabe, Tag v0.1.9 und der grüne Workflow Summary

**Der Branch war auf GitHub, bevor irgendein Tag existierte, die Owner-Antwort lautete um 18:27Z wörtlich `freigeben`, der Tag `v0.1.9` entstand danach auf demselben Commit `685295d`, den `origin/main` schon trug, und der Release-Lauf `32883904698` ist in jedem Schritt grün: das Multi-Arch-Image liegt unter `ghcr.io/street1983nk/mcp_connector:0.1.9`, und `mcp_connector-0.1.9.tar.gz` mit 47264 Bytes hängt am GitHub-Release.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-25T18:20:00Z
- **Completed:** 2026-08-25T18:33:00Z
- **Tasks:** 3 (einer davon der blockierende Checkpoint)
- **Files modified:** 1 versioniert (`docs/store-submission.md`), plus zwei Planungsdateien

## Accomplishments

- **Der Push kam zuerst, und das ist der Kern dieses Plans.** 18 Commits der Phase lagen ungepusht, genau die Lage, in der das 0.1.8-Release 42 ungepushte Commits fand. Nach `git push origin main` (`dfee4f8..22471c1`) gab `git log origin/main..HEAD --oneline | wc -l` die Zahl 0, und `git tag --list v0.1.9` war weiterhin leer: der Zustand, in dem ein Tag überhaupt erst zur Entscheidung stehen darf.
- **Das Changelog-Datum stimmte ohne Eingriff.** `## [0.1.9] - 2026-08-25` in Zeile 12 gegen den Kalendertag in UTC gehalten: die Messung lief um 18:20Z, der Tag entstand um 18:27Z, beides am 2026-08-25. Keine Zeile geändert, also kein Commit für Task 1.
- **Der Checkpoint hat gehalten.** Zwischen Push und Tag lag ein echter Halt: die Rückgabe nannte den Stand, die fünf Prüfschritte und die zwei Entscheidungen, und kein Kommando hat die Antwort ersetzt. `git tag --list v0.1.9` war zum Zeitpunkt der Rückgabe leer, lokal und remote.
- **Der Tag trägt genau den Namen, den das Manifest verlangt.** `<version>` und `<image-tag>` in `appinfo/info.xml` nennen `0.1.9`, der Tag heißt `v0.1.9`, und die Gleichheitsprüfung in `release.yml` ließ ihn passieren statt mit Exit 1 abzubrechen. Kein Milestone-Tag wurde gesetzt.
- **Der Workflow ist in jedem Schritt grün.** `gh run watch 32883904698 --exit-status` endete mit Exit 0, `conclusion` ist `success`, Job `publish` von 18:28:00Z bis 18:29:40Z, also 1m40s. Alle 15 Schritte mit Haken, darunter Login nach ghcr.io, der Multi-Arch-Build für `linux/amd64` und `linux/arm64` mit `push: true`, der Bau des Store-Pakets und das Anhängen an das Release.
- **Zwei Proof-Zeilen, keine dritte.** Zeile 136 belegt den Push allein, Zeile 137 Tag und Workflow. `grep -c '0\.1\.9' docs/store-submission.md` gibt 5: die drei Zeilen aus 13-04 zu den Schritten 1 bis 3 und diese zwei. Keine Zeile behauptet etwas zu den Schritten 6 bis 8.

## Der Checkpoint (Task 2)

| Frage | Antwort |
|-------|---------|
| Zeitpunkt der Antwort | 2026-08-25T18:27Z, unmittelbar vor dem Tag |
| Antwort, wörtlich | `freigeben` |
| Weg für Schritt 7 in Plan 13-06 | angemeldete Store-Sitzung im Browser, wie bei 0.1.1 bis 0.1.8 |
| Weg der Antwort | über den Orchestrator an den Executor weitergegeben, nicht aus einem Kommando abgeleitet |
| Zustand bei der Rückgabe des Checkpoints | `origin/main` und `HEAD` beide `685295d`, Arbeitsbaum sauber, `git tag --list v0.1.9` und `git ls-remote --tags origin v0.1.9` beide leer, kein Release-Lauf zu `v0.1.9` |

Die Antwort trug beide verlangten Teile: die Freigabe und den Weg. Damit war Task 3 startbar und Plan 13-06 hat seinen Weg für den Store-Upload.

## Task Commits

1. **Task 1: Branch pushen, Datum prüfen, Abwesenheit des Tags belegen** - kein Commit an Code oder Changelog (das Datum stimmte), aber ein Doku-Commit `685295d` mit der Proof-Zeile zum Push, selbst gepusht (`22471c1..685295d`)
2. **Task 2: Owner-Freigabe** - kein Commit; ein Halt, dessen Ergebnis dieses Kapitel und die Zeile 137 tragen
3. **Task 3: Tag, Workflow, Proof-Zeile der Schritte 4 und 5** - Tag `v0.1.9` auf `685295d` (kein Commit-Objekt), dann `3131a96` mit der Proof-Zeile zu Tag und Workflow, gepusht (`685295d..3131a96`)

## Die Übergabe an Plan 13-06

| Wert | Inhalt |
|------|--------|
| Tag | `v0.1.9`, remote `685295d7d1e0ac227d6611d33fb3eb799351c800` |
| Run-Id | `32883904698`, `conclusion: success`, Job `publish` 1m40s |
| Asset | `mcp_connector-0.1.9.tar.gz`, 47264 Bytes |
| Download-URL | `https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.9/mcp_connector-0.1.9.tar.gz` |
| Image | `ghcr.io/street1983nk/mcp_connector:0.1.9`, Multi-Arch, im Lauf gebaut und gepusht |
| Vergleichswert aus 13-04 | lokal gebaut 47546 Bytes, sha256 `4f2a05feba738536cc4a1ea26cc1c736e92048f959f6bc9064458d8ce8e2e318` |
| Weg für Schritt 7 | angemeldete Store-Sitzung im Browser (Owner-Entscheid) |

Die Differenz 47264 gegen 47546 Bytes ist der erwartete Befund und kein Fehler: `tar.gz` ist nicht bytereproduzierbar, bei 0.1.8 standen 45546 gegen 45710. Signiert wird ausschließlich das heruntergeladene Asset, nie `dist/`.

## Files Created/Modified

- `docs/store-submission.md` - zwei neue Tabellenzeilen. Zeile 136 (`18:21Z`) belegt den Push: 18 Commits auf dem öffentlichen `main`, `origin/main` und `HEAD` derselbe Commit, sauberer Baum, `v0.1.9` lokal und remote abwesend, und der Satz, warum der Push zuerst kommt (die Store-Beschreibung verlinkt `blob/main/...`, die Screenshots laden von `raw.githubusercontent.com/.../main/...`). Zeile 137 (`18:30Z`) belegt Tag und Workflow: Tag auf `685295d`, Run-Id, Job-Name, Laufzeit, Image-Referenz, Asset-Name und Bytezahl, die Freigabe um 18:27Z, und die Feststellung, dass kein Tag umgeschrieben und kein Asset gelöscht wurde
- `.planning/phases/13-cimd-nachmessung-und-release-0-1-9/deferred-items.md` - neu, ein Eintrag: die Node-20-Abkündigung der fünf Workflow-Actions, ausdrücklich nicht gefixt

## Verification Results

| Prüffrage | Ergebnis |
|-----------|----------|
| `git log origin/main..HEAD --oneline \| wc -l` nach dem Branch-Push | 0 |
| `git status --short` | leer, vor und nach jedem Commit |
| Kopfzeile des 0.1.9-Blocks gegen den heutigen Kalendertag (UTC) | `## [0.1.9] - 2026-08-25` in Zeile 12, Messung 18:20Z, Tag 18:27Z, kein Eingriff nötig |
| `git tag --list v0.1.9` vor dem Checkpoint | leer |
| `git ls-remote --tags origin v0.1.9` vor dem Checkpoint | leer |
| `gh run list --workflow release.yml --limit 5` vor dem Tag | kein Lauf zu `v0.1.9`, jüngster `32803041518` für `v0.1.8` |
| `git tag --list v0.1.9` nach Task 3 | `v0.1.9`, genau eine Zeile |
| `git rev-parse --short v0.1.9` gegen `origin/main` vor dem Tag-Push | beide `685295d` |
| `git ls-remote --tags origin v0.1.9` | `685295d7d1e0ac227d6611d33fb3eb799351c800 refs/tags/v0.1.9` |
| `gh run watch 32883904698 --exit-status` | Exit 0, alle 15 Schritte mit Haken |
| `gh run view 32883904698 --json conclusion --jq .conclusion` | `success` |
| Job und Laufzeit | `publish`, `success`, 18:28:00Z bis 18:29:40Z, 1m40s |
| `gh release view v0.1.9 --json assets --jq '.assets[].name'` gegen `^mcp_connector-0.1.9.tar.gz$` | 1 |
| Asset-Größe laut Release-API | 47264 Bytes |
| Zeilen zu den Schritten 6 bis 8 für 0.1.9 | keine; `grep -c '0\.1\.9' docs/store-submission.md` gibt 5, alle zu den Schritten 1 bis 5 |
| `git diff --numstat docs/store-submission.md` vor jedem der zwei Commits | `1 0` und `1 0` |
| Em-Dash und En-Dash in `docs/store-submission.md` | 0 und 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, nach jeder der zwei Doku-Änderungen gelaufen |
| Löschungen in den Commits | keine, `git diff --diff-filter=D` bei beiden leer |
| Milestone-Tag gesetzt | keiner; `v0.1.9` ist der einzige neue Tag |

## Decisions Made

- **Zwei Proof-Zeilen statt einer.** Der Plan bündelte die Schritte 4 und 5 in einer Zeile in Task 3. Zwischen den beiden Hälften von Schritt 4 liegt aber ein blockierender Checkpoint, dessen mögliche Antwort `warten` die Phase beendet hätte. Eine gebündelte Zeile wäre in diesem Fall nie geschrieben worden, und der Push, der stattgefunden hat, wäre unbelegt geblieben. Die erste Zeile behauptet deshalb ausdrücklich nur die erste Hälfte und nennt, was noch fehlt; die zweite entstand erst nach dem grünen Lauf. Die Beweisrichtung bleibt in beiden Fällen gewahrt: keine Zeile stand vor ihrem Ereignis.
- **Kein Eingriff am Changelog.** Das Datum stimmte. Ein Commit, der eine Datei anfasst, um zu zeigen, dass sie richtig ist, wäre eine Behauptung ohne Änderung.
- **Der Tag zeigt nicht auf den letzten Commit von main.** `v0.1.9` steht auf `685295d`, `main` steht danach auf `3131a96`. Das ist unvermeidlich und harmlos: die Zeile zu Tag und Workflow kann erst nach dem Lauf entstehen. Von den vier Dateien im Paket (`appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`) wurde nach dem Tag keine angefasst.
- **Node-20-Abkündigung nicht angefasst.** Die Annotation des Laufs nennt fünf fremde Actions, die GitHub bereits auf Node 24 zwingt. Der Lauf ist grün, das Release unberührt. Ein Fix an `release.yml` mitten in einer laufenden Veröffentlichung wäre genau die Änderung, die ein Release-Runbook verbietet; der Befund steht in `deferred-items.md`, samt dem Hinweis, dass die Abkündigungsregel ein Issue und eine datierte Erinnerung verlangt.

## Deviations from Plan

### Auto-fixed Issues

Keine. Keine der Regeln 1 bis 3 wurde ausgelöst, kein Blocker.

### Scope-Erweiterung an den Artefakten

**1. [Rule 2 - Belegbarkeit] Eine zweite Proof-Zeile, geschrieben vor dem Checkpoint**
- **Found during:** Task 1, vor der Rückgabe des Checkpoints
- **Issue:** Der Plan legte die einzige Proof-Zeile zu Schritt 4 in Task 3, also hinter den Checkpoint. Bei der Antwort `warten` wäre der bereits ausgeführte Push ohne jede Zeile in der Nachweistabelle geblieben, obwohl er stattgefunden hat: eine Lücke genau in der Kategorie, gegen die T-13-25 und T-13-26 gerichtet sind.
- **Fix:** Eine eigene Zeile für die erste Hälfte von Schritt 4, ausdrücklich als solche benannt, mit dem Satz, dass die Zeile zu Tag und Workflow erst nach dem grünen Lauf entsteht. Die Zeile aus Task 3 deckt danach die zweite Hälfte und Schritt 5 ab und nennt die Freigabe.
- **Files modified:** `docs/store-submission.md`
- **Commit:** `685295d` (die erste Zeile), `3131a96` (die zweite)

**Total deviations:** 1 (Scope-Erweiterung, keine Auto-Fix-Regel)
**Impact on plan:** Ein zusätzlicher Doku-Commit vor dem Checkpoint. Alle Akzeptanzkriterien von Task 1 und Task 3 sind erfüllt; die Nachweistabelle trägt eine Zeile mehr als geplant und keine zu den Schritten 6 bis 8.

## Known Stubs

Keine. Dieser Plan hat keine Zeile Code angefasst; die einzige geänderte versionierte Datei ist Dokumentation und beschreibt ausschließlich Ereignisse, die eingetreten sind.

## Threat Flags

Keine neue Sicherheitsoberfläche. Der Plan hat keinen Endpunkt, keinen Auth-Pfad und kein Schema angefasst. Die drei Vertrauensgrenzen des Threat Models wurden alle gehalten: der Tag entstand nur nach der Freigabe (T-13-22), er heißt wörtlich `v0.1.9` (T-13-23), kein Asset wurde gelöscht und kein Tag umgeschrieben (T-13-24).

## Issues Encountered

- Git warnt beim Stagen von `docs/store-submission.md` mit "LF will be replaced by CRLF the next time Git touches it". Das ist `text=auto` aus `.gitattributes` mit der Windows-Einstellung dieses Arbeitsplatzes, dieselbe Meldung wie in 13-04, und keine Folge dieses Plans: `git diff --numstat` zeigt beide Male `1 0`. Keine Aktion.
- Der Workflow-Lauf trägt die Annotation "Node.js 20 is deprecated" für fünf fremde Actions. Vorbestehend, grün, ausdrücklich nicht gefixt, protokolliert in `deferred-items.md`.

## User Setup Required

Für Plan 13-06 (Schritt 7): eine angemeldete Store-Sitzung im Browser auf `https://apps.nextcloud.com`, wie der Owner sie am Checkpoint benannt hat. Das Signieren (Schritt 6) braucht den privaten Signaturschlüssel zum zusammengeführten Zertifikat; er ist bewusst kein Repository-Secret.

## Next Phase Readiness

- **Für Plan 13-06:** alle Werte stehen in der Übergabetabelle oben. Das Asset ist da, der Tag ist da, das Image ist da. Signiert wird das heruntergeladene Asset, und die Differenz 47264 gegen 47546 Bytes ist der Beleg, warum.
- **Erfolgskriterium 3 der Roadmap ist erfüllt:** der Branch war gepusht, bevor irgendein Tag existierte, und der Tag entstand erst nach ausdrücklicher Owner-Freigabe.
- **Kein Blocker.** Offen bleiben die Runbook-Schritte 6 bis 8: signieren, einreichen, nachprüfen.
- **Eine Grenze, die stehen bleiben muss:** das Asset unter der Download-URL darf nie gelöscht und der Tag nie umgeschrieben werden, weil AppAPI von dieser URL installiert und nicht aus dem Store.

## Self-Check: PASSED

`docs/store-submission.md`, diese SUMMARY und `deferred-items.md` liegen auf der Platte. Die Commits `685295d` und `3131a96` sind in `git log` auffindbar und beide auf `origin/main`, keiner enthält eine Löschung. Der Tag `v0.1.9` existiert lokal und remote auf `685295d`, der Lauf `32883904698` steht auf `success`, und das Release trägt `mcp_connector-0.1.9.tar.gz`.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*
