---
phase: 16-release-0-1-11
plan: 01
subsystem: infra
tags: [release, versioning, changelog, appstore, exapp, crlf]

# Dependency graph
requires:
  - phase: 15-release-0-1-10
    provides: "Das Release 0.1.10 als signiertes Asset im Store, der Tag v0.1.10 als Bezugspunkt und das Vorgehen für die sechs Versionsstellen"
provides:
  - "Die Versionszeichenkette 0.1.11 an allen sechs Stellen (pyproject.toml, __init__.py, info.xml <version>, info.xml <image-tag>, die drei README-Statuszeilen, uv.lock)"
  - "Den Changelog-Block ## [0.1.11] - 2026-08-28 samt seiner Linkdefinition, an der Stelle des bisherigen [Unreleased]-Blocks"
  - "Einen 0.1.11-Kandidaten, den scripts/build_store_release.sh benennen und release.yml gegen einen Tag prüfen kann"
affects: [16-02 Gates und Archiv-Trockenlauf, 16-03 Branch-Push und Tag, EXAPP-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CRLF-Dateien byte-exakt per Python rb/wb patchen, zeilenweise mit Assertion auf den erwarteten Altzustand"
    - "Versionszählung immer verankert (^-Anker, grep -c auf Zeilenanfang), nie als Teilzeichenkette, weil v0.1.1 und v0.1.10 beide existieren"

key-files:
  created:
    - .planning/phases/16-release-0-1-11/16-01-SUMMARY.md
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
  - "Die Kopfzeile des Blocks trägt das Datum 2026-08-28; lokal (Europe/Berlin, 10:35) und in UTC (08:35Z) ist derselbe Kalendertag, der Tag kann also nicht auf einem früheren Tag entstehen"
  - "Die Aussage der beiden [Unreleased]-Punkte wurde übernommen und nicht neu erfunden; ergänzt wurde ein Satz zur geweiteten Teilen-Formulierung, gemessen gegen den veröffentlichten 0.1.10-Text (Aufzählung Ordner/Board/Tabelle) und nicht gegen den Zwischenstand aus b3267cd"
  - "Die zwei Punkte wurden beim Übergang in den Release-Block auf die Zeilenbreite der Nachbarblöcke umgebrochen; die Aussage blieb unverändert"
  - "Der Einleitungsabsatz wurde ersetzt: er sagte, die Änderungen warten auf das nächste Release, was in einem Release-Block falsch ist"

patterns-established:
  - "Ein wartender [Unreleased]-Block wird zum Release-Block umgewidmet, statt einen neuen Block daneben zu setzen; Abschnitt und Linkdefinition wandern gemeinsam"

requirements-completed: [EXAPP-11]

# Metrics
duration: 7min
completed: 2026-08-28
---

# Phase 16 Plan 01: Versionshub 0.1.11 und Changelog-Block Summary

**Die Zeichenkette 0.1.11 steht an allen sechs Versionsstellen, und aus dem wartenden [Unreleased]-Block ist der Release-Block `## [0.1.11] - 2026-08-28` samt seiner Linkdefinition geworden. Kein Tag existiert.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-08-28T08:29:00Z
- **Completed:** 2026-08-28T08:36:02Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Sechs Versionsstellen tragen dieselbe Zeichenkette 0.1.11, und in den sieben Dateien steht kein 0.1.10-Rest mehr
- Kein Zeilenenden-Massen-Diff: die CRLF-Zählungen sind vor und nach dem Patch 536, 551, 570 und 540, und `git diff --numstat` nennt je `1 1`, für `appinfo/info.xml` mit seinen zwei Stellen `2 2`
- Die Nutzlast dieses Releases ist unberührt geblieben: die drei gekürzten Trifecta-Absätze und `<author mail="admin@infranode.dev">` stehen Wort für Wort wie in `b3267cd`, `901b294` und `deafbf4`
- Der Changelog führt 12 Versionsabschnitte gegen 12 Linkdefinitionen, keine hängende Definition, kein `Unreleased` mehr in der Datei
- Das Manifest-, Beschreibungs-, Variablen- und Vokabular-Gate ist grün: `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` endet zweimal mit Exit 0

## Task Commits

1. **Task 1: Sechs Versionsstellen auf 0.1.11** - `289e4d6` (chore)
2. **Task 2: Aus dem [Unreleased]-Block wird der Changelog-Block 0.1.11** - `98f431c` (docs)

## Files Created/Modified

- `pyproject.toml` - Paketversion 0.1.11 (Zeile 3), kein Dependency-Block angefasst
- `src/mcp_connector/__init__.py` - `__version__ = "0.1.11"` (Zeile 7)
- `appinfo/info.xml` - `<version>` (183) und `<image-tag>` (258) auf 0.1.11, CRLF byte-exakt, ElementTree parst die Datei
- `uv.lock` - Selbsteintrag `version = "0.1.11"` (Zeile 472), als Texteditierung ohne Lock-Lauf
- `README.md`, `README.de.md`, `README.fr.md` - je die Statuszeile `Version 0.1.11.` (27, 29, 31), sonst keine Zeile
- `CHANGELOG.md` - der Block `## [0.1.11] - 2026-08-28` an der Stelle des bisherigen `[Unreleased]`-Blocks, plus die getauschte Linkdefinition am Dateiende

## Das Datum der Kopfzeile, für Plan 16-03

Die Kopfzeile lautet **`## [0.1.11] - 2026-08-28`**. Sie wurde am 2026-08-28 um 10:35 Europe/Berlin geschrieben, was in UTC 08:35Z desselben Tages ist: beide Uhren nennen denselben Kalendertag, anders als beim 0.1.10-Block, der lokal am 28. und in UTC noch am 27. geschrieben wurde. Ein Tag kann damit nicht an einem Tag entstehen, der früher ist als der, den der Block nennt. Entsteht der Tag an einem späteren Kalendertag, hebt Plan 16-03 diese eine Zeile vor dem Tag, weil ein Release-Notes-Datum im signierten Asset unveränderlich ist.

## Die Korrektur aus 901b294 fährt mit, ohne eigenen Eintrag

`901b294` hat nach dem Tag `v0.1.10` eine Behauptung im 0.1.10-Block korrigiert: der kurze Enterprise-Wortlaut sagt die Nichtexistenz nicht so deutlich wie der lange, er trägt sie in einem Wort, `planned`. Diese Korrektur steht als Prosa im Block der Vorversion und fährt mit dem 0.1.11-Asset zum ersten Mal in ein veröffentlichtes Artefakt. Sie hat **keinen** eigenen Changelog-Eintrag bekommen, weil ein Eintrag darüber ein Changelog-Eintrag über den Changelog wäre. Genau so ist die WR-02-Korrektur bei 0.1.10 behandelt worden. Der Changelog im Repository und der Changelog im signierten 0.1.10-Asset unterscheiden sich bis zum Upload von 0.1.11 um genau diese eine Stelle; das ist die bekannte und akzeptierte Drift-Klasse, kein Fehler.

## Decisions Made

- **Datum 2026-08-28** in der Kopfzeile, siehe Abschnitt oben.
- **Der Einleitungsabsatz wurde ersetzt statt übernommen.** Der alte Satz "wait for the next release" ist in einem Release-Block eine falsche Aussage. Der neue Absatz steht im Ton des 0.1.10-Blocks: kein Codewechsel, dieselben einundzwanzig Werkzeuge, jede Instanz behält ihr Verhalten, und der Store liest das Manifest zur Uploadzeit und zu keinem anderen Moment.
- **Die Teilen-Formulierung wurde gegen den veröffentlichten Stand gemessen.** Der Satz im Block sagt, die letzte der vier Aussagen sei jetzt eine allgemeine Wendung ("anywhere the account shares"), wo die längere Fassung Ordner, Board und Tabelle einzeln aufzählte. Das ist gegen `git show v0.1.10:appinfo/info.xml` wahr. Die Formulierung "nicht mehr ein geteilter Ordner", die die Nachweiszeile von 05:40Z benutzt, beschreibt den Zwischenstand aus `b3267cd` und wäre aus Sicht eines Store-Lesers falsch, weil dieser Zwischenstand nie veröffentlicht wurde.
- **Die zwei Punkte wurden umgebrochen.** Im `[Unreleased]`-Block standen sie als je eine sehr lange Zeile, die Nachbarblöcke brechen bei rund 95 Zeichen. Die Aussage ist unverändert.

## Deviations from Plan

Am Plan selbst: **None - plan executed exactly as written.** Keine Abweichung nach Regel 1 bis 4 an den acht Dateien, kein Auto-Fix, kein Paket installiert, kein Lock-Lauf, kein Tag.

Zwei Abweichungen vom mechanischen Abschluss-Protokoll, beide bewusst:

**1. EXAPP-11 wurde in REQUIREMENTS.md NICHT abgehakt.** Alle vier Pläne der Phase 16 tragen `requirements: [EXAPP-11]`, und die Anforderung verlangt wörtlich das Release "im Nextcloud App Store", samt Branch-Push, Owner-Freigabe, Tag und Signatur über das heruntergeladene Asset. Nach Plan 16-01 ist davon der erste Teil geschrieben und nichts veröffentlicht. Ein Haken hier wäre eine Behauptung über einen Zustand, den erst Plan 16-04 herstellt. Das Abhaken gehört an das Ende von 16-04.

**2. STATE.md wurde nach den SDK-Handlern von Hand nachgezogen.** `state.advance-plan` und `state.update-progress` fanden im Positionsblock kein maschinenlesbares Zählerpaar und schrieben nichts (`Cannot parse Current Plan or Total Plans`). `state.record-session` und `state.add-decision` schrieben, setzten dabei aber die Frontmatter-Felder `status` und `percent` auf Werte, die nicht stimmten, und die Entscheidungszeile enthielt einen Em-Dash. Beides ist von Hand korrigiert: `status: executing`, `percent: 25`, und der Em-Dash im neuen Eintrag ist durch einen Punkt ersetzt. Der eine verbliebene Em-Dash in STATE.md steht in einem Phase-09-Eintrag, ist vorbestehend und wurde nach der Regel zur Sichtweite nicht angefasst.

## Issues Encountered

Ein Akzeptanzkriterium ist zeitgebunden und war nach Task 1 nicht mehr in der geschriebenen Form prüfbar, ohne dass die Aussage dahinter falsch geworden wäre:

- **Kriterium aus Task 2:** `git diff v0.1.10..HEAD --numstat -- README.md README.de.md README.fr.md` soll keine Zeile ausgeben, als Beleg dafür, dass die drei READMEs keine Nutzlast tragen und der Block sie deshalb nicht nennen darf. Nach dem Commit von Task 1 nennt dieser Befehl je `1 1`, weil Task 1 selbst die drei Statuszeilen gehoben hat.
- **Gemessener Ersatz, gleiche Aussage:** gegen die Phasenbasis `3fb9941` (der Stand vor dem Bump) gibt derselbe Befehl keine Zeile aus, und `git diff v0.1.10..HEAD -U0` über die drei Dateien zeigt ausschließlich die drei Statuszeilen. Die Aussage des Blocks, dass die READMEs keine Nutzlast dieses Releases tragen, ist damit belegt. Der Block nennt keine der drei Dateien.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Runbook-Schritt 1 und 2 sind geschrieben. Plan 16-02 kann die Gates lokal fahren und den Archiv-Trockenlauf machen; `scripts/build_store_release.sh` liest die Version jetzt als 0.1.11 aus `appinfo/info.xml` und benennt das Archiv danach.
- Erwartung für die Budget-Messung in 16-02: die Werkzeugoberfläche wuchs von 0.1.9 auf 0.1.10 um genau ein Byte, weil die Versionszeichenkette im `serverInfo` des `tools/list`-Umschlags um ein Zeichen wuchs. Von `0.1.10` auf `0.1.11` wächst sie nicht, beide sind sechs Zeichen; 15712 Bytes gegen ein Budget von 18000 ist der erwartete Messwert.
- **Kein Tag existiert.** `git tag --list v0.1.11` ist leer, lokal und ungepusht. Der Tag entsteht in Plan 16-03 nach ausdrücklicher Owner-Freigabe, und der Branch-Push kommt davor.
- Nichts wurde in den Store geladen, und `release.yml` wurde nicht angestoßen.

## Self-Check: PASSED

- `.planning/phases/16-release-0-1-11/16-01-SUMMARY.md` existiert auf der Platte
- `289e4d6` und `98f431c` sind in `git log --oneline --all` vorhanden
- Alle 15 Akzeptanzkriterien aus Task 1 und alle 14 aus Task 2 wurden ausgeführt und geloggt; das eine zeitgebundene Kriterium ist oben unter "Issues Encountered" mit seinem gemessenen Ersatz dokumentiert
- Plan-Verifikation: sechs Stellen identisch, Gate zweimal Exit 0, `git diff --numstat 3fb9941..HEAD` nennt acht Dateien (`1 1` je Datei, `2 2` für `appinfo/info.xml`, `17 5` für `CHANGELOG.md`), `grep -c 'Unreleased' CHANGELOG.md` gibt 0, 12 gegen 12, `git tag --list v0.1.11` leer

---
*Phase: 16-release-0-1-11*
*Completed: 2026-08-28*
