---
phase: 16-release-0-1-11
plan: 03
subsystem: infra
tags: [release, tag, workflow, ghcr, proof-table, irreversible]

# Dependency graph
requires:
  - phase: 16-release-0-1-11
    provides: "Sechs grüne Gates auf dem 0.1.11-Kandidaten und die drei Proof-Zeilen der Runbook-Schritte 1 bis 3"
provides:
  - "Den Tag v0.1.11 auf 504de6c, lokal und auf der Gegenstelle"
  - "Den grünen Release-Lauf 33160063188 mit dem Multi-Arch-Image unter ghcr.io/street1983nk/mcp_connector:0.1.11"
  - "Das veröffentlichte Store-Asset mcp_connector-0.1.11.tar.gz mit 47046 Bytes und seiner Download-URL"
  - "Die Proof-Zeile der Runbook-Schritte 4 und 5 in docs/store-submission.md"
affects: [16-04 Signatur und Store-Einreichung, EXAPP-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Den Tagnamen vor dem Push über od -c Zeichen für Zeichen belegen, nicht über einen Teilstring-Treffer, wenn Nachbarversionen existieren"
    - "Den Tag mit der vollen Referenz refs/tags/<name> pushen, damit kein Branch gleichen Namens verwechselt werden kann"

key-files:
  created:
    - .planning/phases/16-release-0-1-11/16-03-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Task 1 und Task 2 waren beim Start dieses Ausführungslaufs bereits erledigt: der Push lag vor, die Owner-Freigabe lag vor. Beides wurde nachgeprüft statt wiederholt, weil ein zweiter Push nichts bewegt und eine zweite Nachfrage die Entscheidung nicht besser macht"
  - "Die Proof-Zeile entstand nach dem grünen Lauf und liegt damit zwangsläufig hinter dem Tag. Das ist Post-Tag-Drift in docs/store-submission.md und ohne Folge, weil diese Datei nicht im Asset mitreist"
  - "Der sha256 des heruntergeladenen Assets wurde für den Bericht gemessen, aber nirgends signiert und nirgends eingereicht: das ist Schritt 6 und gehört Plan 16-04"

patterns-established:
  - "Ein Release, dessen Proof-Zeile die Freigabe nicht auf die Minute kennt, sagt das statt eine Uhrzeit zu erfinden: die Aussage vor dem Tag ist prüfbar, eine erfundene Minute wäre es nicht"

requirements-completed: []
# EXAPP-11 bleibt Pending: es verlangt das Release im Nextcloud App Store, und der Upload ist
# Runbook-Schritt 7 in Plan 16-04. Dieser Plan liefert nur die Voraussetzung dafür.

# Metrics
duration: 9min
completed: 2026-08-28
---

# Phase 16 Plan 03: Tag v0.1.11 und Release-Workflow Summary

**Der Tag `v0.1.11` steht auf `504de6c`, der Lauf `33160063188` ist in jedem Schritt grün, das Multi-Arch-Image liegt unter `ghcr.io/street1983nk/mcp_connector:0.1.11` für `linux/amd64` und `linux/arm64`, und `mcp_connector-0.1.11.tar.gz` hängt mit 47046 Bytes am GitHub-Release. Nichts wurde umgeschrieben, nichts gelöscht, nichts hochgeladen.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-08-28T09:35:30Z
- **Completed:** 2026-08-28T09:44:30Z
- **Tasks:** 3 (zwei davon vorgefunden, einer ausgeführt)
- **Files modified:** 1

## Der Zustand vor dem Tag, nachgeprüft statt wiederholt

Task 1 war beim Start dieses Laufs bereits erledigt und wurde nicht ein zweites Mal
ausgeführt, sondern belegt:

| Prüfung | Erwartet | Gemessen |
|---------|----------|----------|
| `git log origin/main..HEAD --oneline \| wc -l` | 0 | 0 |
| `git status --short` | keine Zeile | keine Zeile |
| `HEAD` | 504de6c | `504de6cfb6c1b48d4e064919db217ea41448d2e1` |
| `git tag --list v0.1.11` | leer | leer |
| `git ls-remote --tags origin v0.1.11` | leer | leer |
| `gh run list --workflow release.yml --limit 5` | kein Lauf zu v0.1.11 | neuester Lauf `33142956284` zu `v0.1.10` |
| Kopfzeile des 0.1.11-Blocks | heutiger Kalendertag | `## [0.1.11] - 2026-08-28` in Zeile 12 |

Die Datumsfalle, die Plan 16-02 für diesen Plan hinterlassen hat, ist nicht eingetreten:
`date` gab `Fri Aug 28 11:35:59 2026` und `date -u` gab `Fri Aug 28 09:35:59 UTC 2026`. Beide
Kalendertage sind der 2026-08-28, also der Tag, den der Changelog-Block nennt. **Die Datumszeile
wurde nicht angefasst**, und `CHANGELOG.md` trägt in diesem Plan keine Änderung.

## Der Tagname, Zeichen für Zeichen

Die Warnung des Plans ist ernst, weil `v0.1.1` und `v0.1.10` beide existieren und ein
Teilstring-Treffer nichts beweist. Deshalb wurde der Name nach `git tag v0.1.11` und **vor** dem
Push über `od -c` gelesen:

```
0000000   v   0   .   1   .   1   1  \n
```

Acht Bytes, sieben davon der Name. Der Push lief mit der vollen Referenz
`git push origin refs/tags/v0.1.11`, damit kein Branch gleichen Namens in die Quere kommen kann,
und die Gegenstelle antwortete `* [new tag] v0.1.11 -> v0.1.11`.

| Zählung | Vorher | Nachher |
|---------|--------|---------|
| `git tag --list 'v0.1.*' \| wc -l` | 11 | **12** |
| `git tag --list \| wc -l` | 16 | 17 |
| `git tag --list \| grep -cx 'v0.1.11'` | 0 | 1 |

Die Gesamtzahl stieg um genau eins: **kein zweiter Tag ist nebenbei entstanden**, insbesondere
kein Milestone-Tag. `git ls-remote --tags origin v0.1.11` nennt
`504de6cfb6c1b48d4e064919db217ea41448d2e1`, denselben Commit wie lokal.

## Der Workflow-Lauf

| Feld | Wert |
|------|------|
| Run-Id | `33160063188` |
| Job | `publish` (ID 98812085768) |
| Ergebnis | `success` |
| Laufzeit | 1m51s |
| Zeitraum | 09:36:28Z bis 09:38:19Z |
| `gh run watch --exit-status` | Exit 0 |

Alle vierzehn Schritte des Jobs sind grün, darunter die drei, auf die es ankommt: die
Versions-Gleichheitsprüfung (`Decide dry run and version`, die bei Ungleichheit von Tag und
`<version>` mit Exit 1 abbräche), der Build für `linux/amd64` und `linux/arm64` mit Push nach
ghcr.io, und das Anhängen des Archivs an das Release. Zum Vergleich: der 0.1.10-Lauf
`33142956284` lief 1m48s. Die 1m51s liegen im selben Rahmen.

## Das Asset und seine Bytegröße

| Größe | Wert | sha256 |
|-------|------|--------|
| veröffentlicht | **47046 Bytes** | `e4b570c0cb9fa9ba44ce9a6bf40fb2518e99945d8c1676a7489293e86f2584b7` |
| lokal aus Plan 16-02 | 47349 Bytes | `df5a9ca97d08f9e21f0315b6b40802af9e837f1edee587107425e8cb29012364` |

**Die Differenz von 303 Bytes ist erwartet und wird nicht ausgeglichen.** `tar.gz` ist nicht
bytereproduzierbar, und dieselbe Messung steht in den Zeilen zu 0.1.2, 0.1.8, 0.1.9 und 0.1.10:
bei 0.1.10 standen 47299 lokal gegen 46973 veröffentlicht, bei verschiedenem sha256. Genau
deshalb signiert Schritt 6 das Heruntergeladene und nie `dist/`.

**Für Plan 16-04, damit dort nichts gesucht werden muss:**

- Download-URL: `https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.11/mcp_connector-0.1.11.tar.gz`
- Erwartete `Content-Length` nach dem 302: `47046`
- `isDraft` ist false, `publishedAt` ist `2026-08-28T09:38:09Z`

Das Asset wurde für diesen Bericht einmal in ein Temp-Verzeichnis geladen, um den sha256 zu
messen. **Es wurde nicht signiert und nicht eingereicht**, und weder `dist/` noch der Arbeitsbaum
wurden dabei berührt: `git status --short` blieb leer.

Eine Warnung für den späteren Leser des Releases: das `createdAt` der Release-Seite lautet
`2026-08-28T08:51:20Z` und ist das Commit-Datum des getaggten Commits, nicht der Moment der
Veröffentlichung. Der war 09:38:09Z, siebenundvierzig Minuten später.

## Das Image bei ghcr

Der Manifest-Abruf mit anonymem Pull-Token antwortet für `0.1.11` mit dem Content-Type
`application/vnd.oci.image.index.v1+json`, Digest
`sha256:42ed8cd2b625c3c9275c2e2d83f3ec458ef993d45ff7936d36c39fd2feb424e8`, und der Index trägt
vier Einträge:

| Digest (gekürzt) | Plattform |
|------------------|-----------|
| `sha256:a80bf9dde5b4` | linux/amd64 |
| `sha256:7256741f27f1` | linux/arm64 |
| `sha256:386fd5550b99` | attestation-manifest |
| `sha256:835e6dec97b0` | attestation-manifest |

Das ist dieselbe Form wie bei 0.1.9 und 0.1.10: zwei echte Architekturen plus zwei
Attestations-Einträge. Die Tagliste der Registry nennt jetzt zwölf Tags, `0.1.0` bis `0.1.11`,
keiner umgeschrieben, keiner entfernt.

Diese Messung ist **Vorabwissen für Schritt 8** und steht bewusst nur hier, nicht in der
Nachweistabelle: die Zeile zu Schritt 8 entsteht in Plan 16-04, nachdem der Schritt passiert ist.

## Die Proof-Zeile

`docs/store-submission.md` trägt eine neue Zeile mit dem Stempel `2026-08-28 09:38Z`, angehängt
hinter die 08:47Z-Zeile aus Plan 16-02 und vor die Überschrift
`### The update keeps the connections`. Sie deckt die zweite Hälfte von Schritt 4 und ganz
Schritt 5 ab, wie die 0.1.10-Zeile es tat, und nennt Run-Id, Job-Name, Laufzeit, Exit-Code,
Assetgröße, Commit-Hash des Tags, die Tagzahl von 11 auf 12 und den Freigabezeitpunkt.

| Prüfung | Erwartet | Gemessen |
|---------|----------|----------|
| `git diff --numstat docs/store-submission.md` | `1 0` | `1 0` |
| CRLF-Zählung der Datei | 0 | 0 |
| Zeilen zu den Schritten 6 bis 8 für 0.1.11 | 0 | 0 |
| Datumsspalte aufsteigend | ja | `sort -c` über 72 Stempel ohne Befund |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0 | Exit 0, 153 Tests |

## Task Commits

1. **Task 1: Branch pushen, Changelog-Datum prüfen, Abwesenheit des Tags belegen** - kein Commit, vorgefunden und nachgeprüft
2. **Task 2: Owner-Freigabe** - kein Commit, vorgefunden
3. **Task 3: Tag, Workflow, Proof-Zeile** - `843abe1` (docs)

## Files Created/Modified

- `docs/store-submission.md` - eine Proof-Zeile zu den Runbook-Schritten 4 und 5, angehängt an das Ende der Nachweistabelle

## Deviations from Plan

**None - plan executed exactly as written.** Kein Auto-Fix nach Regel 1 bis 4, kein Paket
installiert, kein Tag umgeschrieben, kein Asset gelöscht, kein Force-Push, nichts in den Store
hochgeladen. `CHANGELOG.md` blieb unberührt, weil sein Datum bereits stimmte.

## Issues Encountered

**Die Owner-Antwort liegt nicht wörtlich vor, sondern als Weitergabe.** Task 2 verlangt die
Antwort wörtlich (`freigeben` oder `warten`) samt Zeitpunkt. Der Checkpoint war beim Start dieses
Laufs bereits abgearbeitet: der Owner war ausdrücklich gefragt worden, ob der Tag `v0.1.11`
entstehen und der Release-Workflow starten soll, und hatte zugestimmt; als Weg für Schritt 7
wurde die angemeldete Store-Sitzung benannt. Diese Zustimmung erreichte den Ausführenden als
Weitergabe im Auftrag zu diesem Plan, nicht als wörtliches Zitat mit Uhrzeit. Der Zeitpunkt ist
deshalb nur nach oben scharf: **die Freigabe lag vor dem Tag-Push um 09:36:25Z.** Die Proof-Zeile
sagt genau das und erfindet keine Minute, weil die Aussage vor dem Tag prüfbar ist und eine
erfundene Uhrzeit es nicht wäre. Für das nächste Release ist die Lehre, die Antwort im Moment der
Freigabe wörtlich mit UTC-Stempel festzuhalten, statt sie später zu rekonstruieren.

**Post-Tag-Drift, diesmal bekannt und harmlos.** Der Commit `843abe1` mit der Proof-Zeile liegt
hinter dem Tag `v0.1.11`, und das ist unvermeidlich: der Plan verlangt ausdrücklich, die Zeile
erst nach dem grünen Lauf zu schreiben. Anders als bei den Drifts, die die 05:40Z- und
06:05Z-Zeilen für 0.1.10 festhalten mussten, hat dieser keine Folge für das veröffentlichte
Asset: das Archiv trägt nur `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE` und `README.md`, und
`docs/store-submission.md` reist nicht mit. Der Repository-Stand und das signierte Asset stimmen
in jeder Datei überein, die das Asset enthält.

## Known Stubs

Keine. Dieser Plan schreibt keinen Code und keinen Platzhalter.

## User Setup Required

Für Plan 16-04 wird der private Signierschlüssel gebraucht, der zum zusammengeführten
CSR-Zertifikat gehört (`~/.nextcloud/certificates/mcp_connector.key`), und die angemeldete
Store-Sitzung, die der Owner als Weg für Schritt 7 benannt hat.

## Next Phase Readiness

- Runbook-Schritte 4 und 5 sind abgeschlossen und belegt. Roadmap-Erfolgskriterium 3 ist erfüllt,
  ebenso die erste Hälfte von Erfolgskriterium 4: der Branch war auf GitHub, bevor irgendein Tag
  existierte, und der Tag entstand erst nach ausdrücklicher Freigabe.
- **Die irreversible Grenze der Phase ist überschritten.** Ab hier gilt ohne Ausnahme: kein
  `git tag -f`, kein Force-Push, kein `gh release delete-asset`. AppAPI installiert von der
  Asset-URL, nicht aus dem Store; ein gelöschtes Asset ist ein 404 für jede spätere Installation.
  Eine Korrektur kostet eine neue Patch-Version.
- Für Plan 16-04 stehen alle Zahlen bereit: die Download-URL, die erwarteten 47046 Bytes und der
  sha256 `e4b570c0…` des veröffentlichten Assets, gegen den lokalen `df5a9ca9…` bei 47349 Bytes.
  Signiert wird ausschließlich das heruntergeladene Asset.
- Offen bleiben die Schritte 6, 7 und 8: signieren, einreichen, verifizieren. Die Nachweistabelle
  trägt für sie noch keine Zeile, wie es sein soll.

## Self-Check: PASSED

- `.planning/phases/16-release-0-1-11/16-03-SUMMARY.md` existiert auf der Platte
- `843abe1` ist in `git log --oneline --all` vorhanden
- Alle 9 Akzeptanzkriterien aus Task 3 wurden ausgeführt und mit ihrer Ausgabe geloggt; die 7 aus
  Task 1 und die 5 aus Task 2 wurden am vorgefundenen Zustand nachgeprüft, keines umgedeutet
- Plan-Verifikation: `origin/main..HEAD` war vor dem Tag leer, Arbeitsbaum sauber, Changelog-Datum
  korrekt und unberührt, `git tag --list v0.1.11` genau ein Treffer und remote vorhanden, 12
  `v0.1.*`-Tags gegen 11 zuvor bei einem einzigen neuen Tag insgesamt, Lauf `33160063188`
  `success` bei Exit 0, Asset am Release, eine neue Proof-Zeile mit `1 0` im numstat, keine Zeile
  zu den Schritten 6 bis 8

---
*Phase: 16-release-0-1-11*
*Completed: 2026-08-28*
