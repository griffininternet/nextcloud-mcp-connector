---
phase: 14-doku-reste-und-gate-entscheid
plan: 02
subsystem: docs
tags: [store-submission, proof-table, verification-addendum, vocabulary-gate, sec-03]

# Dependency graph
requires:
  - phase: 13-cimd-nachmessung-und-release-0-1-9
    provides: "13-REVIEW.md mit IN-01, IN-02, IN-04 und IN-07; die Proof-Zeilen von 0.1.9; die Commits 22471c1 und 685295d"
  - phase: 13-cimd-nachmessung-und-release-0-1-9
    provides: "13-VERIFICATION.md als Archivstand mit den drei Fundstellen der entfernten Datei"
provides:
  - "docs/store-submission.md mit chronologisch sortierter Nachweistabelle (64 Zeilen, sort -c Exit 0)"
  - "der Rückverweis der 18:30Z-Zeile deckt den getaggten Commit 685295d als eine Änderung hinter 22471c1"
  - "der .planning-Verweis in docs/store-submission.md ist als interne Notiz gekennzeichnet, die verschwinden darf"
  - "13-VERIFICATION.md mit datiertem Nachtrag zu f9b3d2d, 30 hinzugefügte und 0 entfernte Zeilen"
  - "SEC-03-Entscheid: .planning bleibt außerhalb der Gate-Reichweite, begründet im Docstring und gehalten von test_the_vocabulary_gate_stops_at_the_internal_planning_area"
affects: [15-release-0-1-10, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Proof-Zeilen sortieren statt umschreiben: stabile Sortierung des Tabellenblocks nach Zeitstempel, danach sortierter Zeilenvergleich gegen git show HEAD: als Beweis, dass keine Aussage verfälscht wurde"
    - "Archivstände korrigieren durch Anfügen: git diff --numstat muss 0 entfernte Zeilen nennen, die belegende Zeile wird byte-gleich gegen git show HEAD: geprüft"
    - "Gate-Ausnahmen an eine prüfbare Eigenschaft binden statt an Prosa: der Docstring begründet, ein Test hält die Grenze"
    - "CRLF-Testdatei (tests/unit/test_exapp_env_setup.py) byte-exakt per Python rb/wb patchen, damit kein Massen-Diff aus Zeilenenden entsteht"

key-files:
  created:
    - .planning/phases/14-doku-reste-und-gate-entscheid/14-02-SUMMARY.md
  modified:
    - docs/store-submission.md
    - .planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "SEC-03 wird über den zweiten zugelassenen Weg entschieden: .planning bleibt außerhalb der Reichweite des Vokabular-Gates, als dokumentierte Ausnahme im Docstring von public_markdown_pages(). Die Reichweite wird nicht ausgeweitet, und in .planning wird nichts bereinigt"
  - "Die Ausnahme hängt nicht am Kommentar, sondern an zwei prüfbaren Eigenschaften: keine gedeckte Seite liegt unter .planning, und kein Mitglied des Store-Archivs beginnt mit .planning/"
  - "Die Messzahl (144 Treffer in 35 Dateien) steht in dieser SUMMARY und ausdrücklich nicht im Docstring: eine Zahl im Kommentar veraltet still"
  - "IN-01 wird durch Sortieren gelöst und nicht durch die im Review angebotene Notiz 'die Reihenfolge folgt den Runbook-Schritten': eine Tabelle, deren Beweiskraft an der Reihenfolge hängt, soll die Reihenfolge tragen und nicht erklären"
  - "IN-02 präzisiert genau einen Rückverweis; keine Zahl, kein Zeitstempel und kein Run-Name der Zeile wurde angetastet"
  - "DOC-02 wird als Nachtrag gelöst und nicht als Korrektur: der Befund war am 2026-08-25 richtig, und ein später an die Welt angepasster Verifikationsbericht ist kein Bericht mehr"
  - "IN-07 wird durch Kennzeichnung gelöst und nicht durch Entfernen des Pfades: der Pfad ist heute korrekt, und die Selbsttragfähigkeit liegt darin, dass jede Tabellenzeile ihren eigenen Befehl oder ihre eigene URL trägt"

patterns-established:
  - "Reordering-Beweis: eine reine Zeilenbewegung ist belegt, wenn der sortierte Zeilenvergleich vor und nach der Änderung 0 Unterschiede zeigt; erst die anschließende Textänderung darf genau eine Zeile nennen"

requirements-completed: [DOC-02, SEC-03]

# Metrics
duration: 6min
completed: 2026-08-28
---

# Phase 14 Plan 02: Doku-Reste und Gate-Entscheid Summary

**Die Nachweistabelle von docs/store-submission.md läuft jetzt in der Uhrzeit vorwärts (vier Zeilenbewegungen, sortierter Vergleich: 0 verfälschte Zeilen), der Rückverweis der 18:30Z-Zeile deckt den getaggten Commit 685295d als nachgemessen eine Änderung hinter 22471c1, der Archivstand von Phase 13 trägt einen datierten Nachtrag statt einer Umschreibung, und die Reichweite des Vokabular-Gates gegenüber .planning ist entschieden, begründet und von einem Test gehalten.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-08-27T22:34:54Z
- **Completed:** 2026-08-27T22:40:14Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Die 64 Proof-Zeilen mit Zeitstempel sind chronologisch: `sort -c` endet mit Exit 0, und der sortierte Zeilenvergleich gegen den Stand vor der Sortierung nennt 0 Unterschiede, also wurde ausschließlich verschoben
- Genau eine Zeile ist danach präzisiert worden, die 18:30Z-Zeile; der sortierte Vergleich gegen `cf64cdf` nennt jetzt genau diese eine Zeile und keine andere
- Die vier `row above`-Rückverweise wurden nach der Sortierung einzeln nachgelesen und treffen weiter die Zeile, die sie meinen (Tabelle unten)
- Der `.planning`-Verweis im Scope-Absatz ist als interne Notiz gekennzeichnet, die verschwinden darf, samt dem Grund, warum keine Aussage der Seite an ihr hängt; der Pfad steht weiter dort
- Der Archivstand `13-VERIFICATION.md` trägt einen Nachtrag mit 30 hinzugefügten und 0 entfernten Zeilen; Truth 9 ist byte-gleich zum Stand vor der Änderung
- SEC-03 ist entschieden, im Docstring von `public_markdown_pages()` begründet und von einem neuen Test gehalten; die Wortliste liegt weiter an einer einzigen Stelle (`grep -c "FORBIDDEN_VOCABULARY = "` gibt 1)
- Der Testlauf der Datei geht von 152 auf 153 bestandene Tests, `ruff check .` und `ruff format --check .` über das ganze Repo enden mit Exit 0 (198 Dateien formatiert)

## Task 1: die vier Zeilenbewegungen

Der Tabellenblock läuft von Zeile 80 bis Zeile 143 und ist zusammenhängend (64 Zeilen). Sortiert wurde stabil nach dem Zeitstempel, deshalb behalten gleiche Zeitstempel ihre bisherige Reihenfolge zueinander. Die sechs `2026-08-19`-Zeilen ohne Uhrzeit tragen keinen Zeitstempel und stehen unverändert an ihrer Stelle.

| # | Zeile (Stand vorher) | Inhalt | Bewegung |
|---|----------------------|--------|----------|
| 1 | 97 (08:28Z) und 98 (08:30Z) | Screenshot-URLs, Manifest-Validierung 0.1.2 | gemeinsam und in dieser Reihenfolge vor Zeile 91 (08:33Z) |
| 2 | 128 (03:01Z) | Katalog-Listing 0.1.8 | hinter Zeile 132 (02:59Z), damit letzte Zeile des 0.1.8-Blocks |
| 3 | 135 (18:13Z) | sechs Gates 0.1.9 | vor Zeile 133 (18:14Z, Schritt 1) |
| 4 | 140 (18:46Z) | Katalog-Listing 0.1.9 | hinter Zeile 143 (18:41Z, Tagliste), damit letzte Zeile des 0.1.9-Blocks |

**Ergebnis des sortierten Vergleichs.** Nach der reinen Sortierung, vor der Textänderung:

```
diff <(git show HEAD:docs/store-submission.md | grep '^| 2026-' | sort) \
     <(grep '^| 2026-' docs/store-submission.md | sort) | grep -c '^[<>]'
0
```

Null Unterschiede heißt: jede der 64 Zeilen ist Zeichen für Zeichen dieselbe, nur an anderer Stelle. Erst danach wurde die 18:30Z-Zeile geändert, und derselbe Vergleich nennt seitdem 2 Zeilen (eine entfernte, eine hinzugefügte), beide mit dem Präfix `| 2026-08-25 18:30Z |`. Genau eine geänderte Zeile, wie es das Akzeptanzkriterium verlangt. `git show HEAD:... | grep -c '^| 2026-'` und `grep -c '^| 2026-'` geben beide 64: keine Zeile wurde gelöscht, keine hinzugefügt.

### Die vier geprüften "row above"-Stellen

Nach der Sortierung einzeln nachgelesen, nicht angenommen. `grep -c "row above"` gibt 4.

| Zeile (jetzt) | Zeitstempel | Der Verweis | Die gemeinte Zeile | Trifft? |
|---------------|-------------|-------------|--------------------|---------|
| 124 | 2026-08-24 22:39Z | "the 31909 against 32168 bytes of the 2026-08-20 row above" | die datiert genannte 08:34Z-Zeile, die genau diese zwei Zahlen trägt und weiter oberhalb steht | ja, der Verweis ist datiert und nicht positionell |
| 127 | 2026-08-25 02:58Z | "the download URL and the signature of the row above" | 126, 02:55Z, Download 45546 Bytes plus `Verified OK` | ja, direkt darüber |
| 137 | 2026-08-25 18:30Z | "the `22471c1` that the row above certifies at 18:21Z" | 136, 18:21Z, `origin/main` und `HEAD` gleich `22471c1` | ja, direkt darüber |
| 139 | 2026-08-25 18:40Z | "the download URL of the row above" | 138, 18:39Z, Download 47264 Bytes plus `Verified OK` | ja, direkt darüber |

Die Bewegung 2 zog die 03:01Z-Zeile aus der Lücke zwischen 127 und der 02:58Z-Asset-Zeile heraus, was den Rückverweis von 127 auf 126 unberührt lässt. Bewegung 3 verschob nur Zeilen oberhalb von 136, Bewegung 4 nur Zeilen unterhalb von 139.

## Task 1: alter und neuer Wortlaut des Rückverweises

**Nachgemessene Grundlage, im Lauf und nicht aus dem Review abgeschrieben:**

```
git rev-list --count 22471c1..685295d   ->  1
git log --oneline -1 685295d            ->  685295d docs(13-05): the proof line of the branch push, before any tag exists
git log --oneline -1 22471c1            ->  22471c1 docs(13-04): complete the local gates and proof lines plan
```

**Vorher (zwei Stellen derselben Zeile):**

```
The tag `v0.1.9` exists locally and on the remote and points at `685295d`, the commit
`main` already carried, so nothing was tagged that the public branch does not serve.
...
The tag came into being only after an explicit owner release at 18:27Z, and the commits of
this phase were on the public `main` before it existed, which the row above records at 18:21Z.
```

**Nachher:**

```
The tag `v0.1.9` exists locally and on the remote and points at `685295d`, one commit after
the `22471c1` that the row above certifies at 18:21Z: `685295d` is that proof line itself,
and it was published by the `git push origin main` of this step before the tag was created,
so nothing was tagged that the public branch does not serve.
...
The tag came into being only after an explicit owner release at 18:27Z, and every commit of
this phase was on the public `main` before it existed.
```

Der zweite Satz gibt den Rückverweis ab, weil er jetzt im ersten steht; `grep -c "row above"` bleibt deshalb bei 4. Die Garantie "push before tag" steht weiter und stützt sich auf die Kommandospalte derselben Zeile (`git push origin main`, dann `git tag v0.1.9`). Aus der Zeile wurde keine Zahl, kein Zeitstempel und kein Run-Name genommen: `32883904698`, `47264` und `18:27Z` sind je einmal weiter vorhanden.

## Task 1: der gekennzeichnete Verweis (IN-07)

Vorher (Zeile 11 bis 12):

```
was checked with, and the store side facts are verified against the store source, see
`.planning/phases/05-store-research.md`.
```

Nachher (Zeile 11 bis 14):

```
was checked with, and the store side facts are verified against the store source. The
research those facts came out of is kept in `.planning/phases/05-store-research.md`, an
internal note that may disappear: every row of the proof table below carries its own
command or its own URL, so no claim on this page leans on that note.
```

Der Pfad steht weiter dort, weil er heute korrekt ist. Was sich ändert, ist der Status: er ist eine interne Notiz und keine Beweisstütze mehr.

## Task 2: der Wortlaut des Nachtrags

Angefügt am Dateiende von `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md`, ab Zeile 105. Nichts oberhalb wurde angefasst.

```
## Nachtrag 2026-08-28 (Milestone v1.4, Phase 14, DOC-02)

`docs/contrib/enterprise-signals-issue.md` ist seit Commit `f9b3d2d` vom 2026-08-26 nicht
mehr im Repository. Die Commit-Botschaft lautet "docs: remove enterprise issue draft from
repo per owner decision (D-07: no issue, no internals in repo)".

Drei Stellen dieses Berichts nennen die Datei als vorhanden: Zeile 34 (Truth 9), Zeile 48
(Artefakt-Tabelle) und Zeile 67 (Em-Dash-Prüfung). Alle drei waren am Prüfzeitpunkt
`2026-08-25T21:15:00Z` richtig und bleiben unverändert. Ein Verifikationsbericht, der
später an die Welt angepasst wird, ist kein Bericht mehr, sondern eine Behauptung über
einen Zustand, den niemand mehr nachprüfen kann.

Was Truth 9 belegt, hängt nicht an dieser Datei. Die drei WR-Fixes sind die Commits
`c564a6b` (WR-01, Herkunft der 15711 Bytes in der Step-3-Proof-Zeile), `9ac0a3c` (WR-02,
Changelog-Begründung an den 0.1.5-Cache-Befund angeglichen) und `f3faefd` (WR-03,
Go-Kriterium aus dem öffentlichen Issue-Entwurf herausgenommen). Alle drei sind in der
Historie nachweisbar, unabhängig davon, ob die vierte Datei heute noch existiert.

Der Befund IN-04 aus `13-REVIEW.md` (die SSO-Aufzählung des Entwurfs ließ den Schluss
"and a way to withdraw them" weg, den `README.md` trägt) ist mit derselben Entfernung
gegenstandslos: die Datei, deren Aufzählung abwich, gibt es nicht mehr. Beleg:
`git ls-files docs/contrib/` nennt nur noch `docs/contrib/227-pr-body.md`,
`test -f docs/contrib/enterprise-signals-issue.md` ist falsch, und
`git log --diff-filter=D -- docs/contrib/enterprise-signals-issue.md` nennt `f9b3d2d` als
den Commit, der den Pfad entfernt hat.

Geschrieben in Phase 14 des Milestones v1.4 unter der Anforderung DOC-02. Auslöser ist
Tech-Debt-Punkt W-2 aus `.planning/milestones/v1.3-MILESTONE-AUDIT.md`, der genau diese
Abweichung zwischen Bericht und heutigem Repository-Stand festgehalten hat.
```

Die drei Commit-Kennungen und die Entfernungs-Kennung sind im Lauf nachgeprüft und nicht abgeschrieben: `git log --oneline -1 f9b3d2d` nennt "docs: remove enterprise issue draft from repo per owner decision (D-07: no issue, no internals in repo)", `git log -1 --format='%ad' --date=short f9b3d2d` gibt 2026-08-26, und `git log --oneline --diff-filter=D -- docs/contrib/enterprise-signals-issue.md` nennt denselben Commit als den, der den Pfad entfernt hat. Über die Owner-Entscheidung selbst steht im Nachtrag kein Urteil, und über zukünftige Releases steht nichts.

## Task 3: die SEC-03-Entscheidung im Klartext

**Gewählt: der zweite der beiden von SEC-03 zugelassenen Wege. `.planning` bleibt außerhalb der Reichweite des Vokabular-Gates und ist als dokumentierte Ausnahme im Docstring von `public_markdown_pages()` begründet. Die Reichweite wird nicht ausgeweitet, und in `.planning` wird nichts bereinigt.**

**Begründung.** Die Regel adressiert, was der Store und ein Leser der Dokumentation dieses Repositories bekommt: die drei READMEs, den Changelog, alles unter `docs/` und die Manifest-Texte. `.planning` liegt auf der anderen Seite dieser Grenze. Der Bereich ist interner Planungsbereich, reist in keinem Store-Archiv mit, und die abgelegten Milestone- und Phasenstände tragen das Wort in einem technischen `tar`-Kontext als datierten Messbefund. Eine Bereinigung dieser Dateien würde ein Protokoll verfälschen, statt einen Text zu verbessern. Dieselbe Grenze ist im Werkzeugkasten schon gezogen: `pyproject.toml` schließt `.planning` aus der ruff-Reichweite aus, mit derselben Begründung (Planungsdokumente müssen wortgetreu bleiben).

**Messung als Grundlage, Stand 2026-08-28.** `grep -ri "archiv" --include="*.md" .planning` nennt heute 160 Zeilentreffer in 37 Dateien. Davon entfallen 16 Treffer in 2 Dateien auf die Planungsdokumente dieser Phase selbst (`14-01-PLAN.md` und `14-02-PLAN.md`), die zum Zeitpunkt der Planungsmessung noch nicht auf der Platte lagen. Ohne sie sind es genau **144 Treffer in 35 Dateien**, also die Zahl, die der Plan nennt. Sämtliche 144 liegen in abgelegten Milestone- und Phasenständen. Die Zahl steht hier und ausdrücklich nicht im Docstring: eine Zahl im Kommentar veraltet still.

**Wie die Ausnahme gehalten wird.** Nicht durch den Kommentar, sondern durch zwei prüfbare Eigenschaften, in derselben Bauweise, in der `VOCABULARY_EXCEPTION` an `test_the_store_archive_carries_no_exempt_page` hängt:

1. Keine Seite aus `public_markdown_pages()` liegt unter `.planning` (`".planning" not in page.parts`). Verschiebt jemand die Grenze, wird der Lauf rot, statt die Entscheidung stillschweigend zu ändern.
2. Kein Mitglied aus `archive_members()` beginnt mit `.planning/`. Der Store bekommt nichts aus dem internen Bereich, und genau das rechtfertigt die Ausnahme. Die Liste kommt aus `scripts/build_store_release.sh` und nicht aus dem Gedächtnis.

Der Docstring des neuen Tests sagt, was ein rotes Ergebnis bedeutet: die Grenze hat sich bewegt, also ist die Entscheidung offen neu zu treffen und nicht die Grenze zurückzuschieben.

**Nicht angefasst:** `FORBIDDEN_VOCABULARY` (weiter genau eine Wortliste, `grep -c "FORBIDDEN_VOCABULARY = "` gibt 1), `PUBLIC_MARKDOWN`, `VOCABULARY_EXCEPTION`, `VERBATIM_ARCHIVE_TEXT` und die drei bestehenden Reichweiten-Tests. Der Diff der Testdatei besteht aus zwei rein anfügenden Hunks (`@@ -2020,0 +2021,11 @@` und `@@ -2120,0 +2132,20 @@`), also 31 hinzugefügte und 0 entfernte Zeilen; `git diff -U0` enthält für jeden der sechs Schutzobjekte 0 Treffer mit `+` oder `-`.

## Task Commits

1. **Task 1: Nachweistabelle chronologisch und der Rückverweis der Tag-Zeile präzise** - `a61fb1e` (docs)
2. **Task 2: Datierter Nachtrag im Archivstand der 13-VERIFICATION** - `b565178` (docs)
3. **Task 3: Reichweite des Vokabular-Gates entscheiden, begründen und prüfbar machen** - `5dc360a` (test)

## Files Created/Modified

- `docs/store-submission.md` - vier Zeilenbewegungen, eine präzisierte 18:30Z-Zeile, der `.planning`-Verweis als interne Notiz gekennzeichnet (10 hinzugefügte, 8 entfernte Zeilen; die 5 gegen 5 der reinen Sortierung sind darin die minimale Darstellung der Bewegung)
- `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md` - Nachtrag ab Zeile 105, 30 hinzugefügte und 0 entfernte Zeilen
- `tests/unit/test_exapp_env_setup.py` - `.planning`-Absatz im Docstring von `public_markdown_pages()`, neuer Test `test_the_vocabulary_gate_stops_at_the_internal_planning_area`, 31 hinzugefügte und 0 entfernte Zeilen

## Decisions Made

- SEC-03 über den zweiten Weg: `.planning` bleibt außerhalb der Reichweite, als dokumentierte Ausnahme im Docstring, Begründung und Messung oben
- Die Ausnahme hängt an zwei prüfbaren Eigenschaften und nicht am Kommentar; die Wortliste bleibt an ihrer einzigen Stelle
- IN-01 durch Sortieren gelöst, nicht durch die im Review angebotene Notiz über die Runbook-Reihenfolge
- DOC-02 als Nachtrag, nicht als Korrektur: der Befund war zum Prüfzeitpunkt richtig
- IN-07 durch Kennzeichnung, nicht durch Entfernen des Pfades

## Deviations from Plan

None - plan executed exactly as written.

Eine Zahl im Plan brauchte eine Erklärung, keine Änderung: der Plan nennt als Messgrundlage 144 Treffer in 35 Dateien, der Lauf am 2026-08-28 findet 160 in 37. Die Differenz sind exakt die 16 Treffer in den beiden Planungsdokumenten dieser Phase selbst (`14-01-PLAN.md`, `14-02-PLAN.md`), die bei der Planungsmessung noch nicht existierten. Ohne sie stimmt die Zahl des Plans auf den Treffer. Da die Zahl laut Plan nicht in den Kommentar geschrieben wird, hat das keine Auswirkung auf den Code; beide Zahlen sind oben genannt.

Kein Versions-Bump, kein Tag, keine Paketinstallation: `grep -c '^version = "0.1.9"' pyproject.toml` gibt 1, `<version>` in `appinfo/info.xml` nennt 0.1.9, `git tag --list v0.1.10` ist leer, und alle Läufe liefen mit `uv run --no-sync` (T-14-SC erfüllt).

## Verification

| Kriterium | Ergebnis |
|-----------|----------|
| `grep -oE '^\| 2026-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}Z' docs/store-submission.md \| sort -c` | keine Meldung, Exit 0 |
| Zeilenzahl der Tabelle vorher/nachher | 64 gegen 64 |
| Sortierter Vergleich nach reiner Sortierung | 0 Unterschiede, also keine verfälschte Aussage |
| Sortierter Vergleich nach der Textänderung | 2 Zeilen (eine entfernte, eine hinzugefügte), beide `\| 2026-08-25 18:30Z \|` |
| 18:30Z-Zeile enthält `685295d`, `22471c1`, `32883904698`, `47264`, `18:27Z` | je 1 |
| `grep -c "row above" docs/store-submission.md` | 4, jeder Treffer einzeln nachgelesen (Tabelle oben) |
| `grep -n "—\|–" docs/store-submission.md` | keine Zeile (rc=1) |
| `git rev-list --count 22471c1..685295d` | 1 |
| `git diff --numstat` der 13-VERIFICATION | `30 0`, also 0 entfernte Zeilen |
| Truth 9 (`^\| 9 \|`) | 1 Treffer, `diff` gegen `git show HEAD:` leer, also byte-gleich |
| `grep -c "^## Nachtrag 2026-08-28"` / `f9b3d2d` / `2026-08-26` | 1 / 2 / 1 |
| Em- und En-Dashes in der 13-VERIFICATION | 4 Treffer, alle in Zeile 18, 27, 67 und 73, also oberhalb des Nachtrags ab Zeile 105 |
| `grep -c "def test_the_vocabulary_gate_stops_at_the_internal_planning_area"` | 1 |
| `grep -c "FORBIDDEN_VOCABULARY = "` | 1 |
| `git diff -U0` der Testdatei gegen die sechs Schutzobjekte | je 0 Treffer, zwei rein anfügende Hunks |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | 153 passed, Exit 0 (vorher 152) |
| `uv run --no-sync pytest ... -k internal_planning_area` | 1 passed |
| `uv run --no-sync ruff check .` / `ruff format --check .` | All checks passed / 198 files already formatted, je Exit 0 |
| `git status --short .planning` | leer (Task 2 ist committet, sonst ist dort nichts geändert) |
| `git diff --diff-filter=D` je Commit | keine Löschung einer verfolgten Datei |
| Version und Tag | 0.1.9 unverändert, `v0.1.10` existiert nicht |

## Issues Encountered

- `tests/unit/test_exapp_env_setup.py` liegt mit CRLF (2199 Zeilen vorher). Der Patch lief byte-exakt per Python `rb`/`wb`, deshalb nennt der Diff nur die 31 tatsächlich hinzugefügten Zeilen und keinen Massen-Diff aus Zeilenenden.
- Git warnt beim Stagen von `docs/store-submission.md` und der `13-VERIFICATION.md` mit "LF will be replaced by CRLF the next time Git touches it". Das ist `text=auto` aus `.gitattributes` in Verbindung mit der Windows-Einstellung dieses Arbeitsplatzes und keine Folge dieser Änderung: beide Dateien liegen im Working Copy mit LF, vor und nach der Änderung, und die Commits nennen nur die tatsächlich berührten Zeilen. Keine Aktion.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DOC-01, DOC-02 und SEC-03 sind geschlossen; Phase 14 hat damit alle drei Doku- und Gate-Anforderungen erfüllt
- Für Phase 15 (EXAPP-10) bleibt offen: der Versions-Bump auf 0.1.10 an allen sechs Stellen, der Changelog-Block `[0.1.10]` samt Linkdefinition (Regel aus 14-01), der Branch-Push vor dem Tag, der Tag `v0.1.10` nur nach ausdrücklicher Owner-Freigabe und die Signatur über das heruntergeladene Asset
- Neue Proof-Zeilen von Phase 15 gehören ans Ende der Tabelle und sind damit von sich aus chronologisch; der Reordering-Beweis oben ist die Prüfung, falls doch einmal eine Zeile dazwischen muss
- `docs/store-submission.md` bleibt die einzige Datei mit einer Vokabular-Gate-Ausnahme, und ihre Begründung ist jetzt an zwei Stellen gedeckt: die Datei reist nicht im Store-Archiv, und `.planning` liegt per Entscheid außerhalb der Reichweite

## Self-Check: PASSED

- Alle drei geänderten Dateien existieren auf der Platte
- Alle drei Task-Commits liegen im Log: `a61fb1e`, `b565178`, `5dc360a`
- Echte Umlaute durchgehend, kein ASCII-Ersatz; keine Em- oder En-Dashes in dieser Datei außer den zitierten Grep-Mustern der Prüftabelle, also den Suchmustern selbst und keiner Prosa

---
*Phase: 14-doku-reste-und-gate-entscheid*
*Completed: 2026-08-28*
