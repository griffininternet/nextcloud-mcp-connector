---
phase: 15-release-0-1-10
plan: 01
subsystem: release
tags: [version-bump, changelog, info.xml, uv.lock, store-release]

# Dependency graph
requires:
  - phase: 14-doku-reste-und-gate-entscheid
    provides: "CHANGELOG.md ohne hängende Linkdefinition plus die Paarungsregel für Phase 15; die korrigierten Übersetzungen in README.fr.md und README.de.md"
  - phase: 13-cimd-nachmessung-und-release-0-1-9
    provides: "Commit 55a5822 (gekürzter Enterprise-Abschnitt und Kontaktwechsel zu admin@infranode.dev) als Nutzlast dieses Releases"
provides:
  - "Version 0.1.10 als dieselbe Zeichenkette an allen sechs Stellen"
  - "Changelog-Block 0.1.10 mit Kopfzeile 2026-08-28, Rubriken Changed und Fixed"
  - "Linkdefinition [0.1.10] auf compare/v0.1.9...v0.1.10, gepaart mit ihrem Abschnitt"
  - "Tarball-Name und Tag-Name des Kandidaten stehen fest: 0.1.10 beziehungsweise v0.1.10"
affects: [15-02, 15-03, 15-04, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CRLF-Dateien (README.md, README.de.md, README.fr.md, appinfo/info.xml) byte-exakt per Python rb/wb patchen; das Skript prüft die Trefferzahl vor und die CRLF-Zahl nach dem Schreiben und bricht bei Abweichung ab"
    - "uv.lock-Versionszeile per Texteditierung heben, nie per uv lock oder uv sync; alle Prüfläufe mit uv run --no-sync"
    - "Changelog-Block und Linkdefinition entstehen im selben Commit, Mengengleichheit als Nachweis"

key-files:
  created:
    - .planning/phases/15-release-0-1-10/15-01-SUMMARY.md
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
  - "Die Kopfzeile des 0.1.10-Blocks trägt 2026-08-28, den lokalen Kalendertag des Schreibens (Europe/Berlin); in UTC war es beim Commit noch 2026-08-27T23:22Z. Plan 15-03 prüft das Datum vor dem Tag gegen den Kalendertag des Tags und korrigiert es, falls der Tag an einem anderen Tag entsteht"
  - "EXAPP-10 bleibt Pending und wird von diesem Plan NICHT abgehakt: die Anforderung verlangt 'Release 0.1.10 ist im Store', und dieser Plan erzeugt weder Tag noch Asset noch Upload. Alle vier Pläne der Phase tragen EXAPP-10, abgehakt wird sie am Ende von Plan 15-04"
  - "Die WR-02-Korrektur am 0.1.9-Block bekommt keinen eigenen Changelog-Eintrag; sie fährt als Prosa im Vorversions-Block mit dem 0.1.10-Asset zum ersten Mal mit und schließt damit W-1 des v1.3-Audits"
  - "appinfo/info.xml wurde ausschließlich an <version> und <image-tag> angefasst; der gekürzte Enterprise-Text, die Summaries, die Descriptions und die environment-variables blieben unberührt, weil ein leer gemachtes Element den Store-Upload mit HTTP 500 beendet"

patterns-established:
  - "Versions-Bump als reine Zeichenkettenersetzung: git diff --numstat nennt für jede Datei gleich viele hinzugefügte wie entfernte Zeilen, appinfo/info.xml als einzige Datei mit zwei Stellen also 2 gegen 2"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-08-28
---

# Phase 15 Plan 01: Versions-Bump auf 0.1.10 und Changelog-Block Summary

**Die Zeichenkette 0.1.10 steht an allen sechs Versionsstellen, und der Changelog-Block 0.1.10 vom 2026-08-28 nennt die Enterprise-Kürzung samt Kontaktwechsel zu admin@infranode.dev als nutzersichtbare Änderung und die Übersetzungs-Korrekturen als Doku-Korrektur, ohne dass ein Tag entstanden ist.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-27T23:15Z (lokal 2026-08-28 01:15 +02:00)
- **Completed:** 2026-08-27T23:22Z (lokal 2026-08-28 01:22 +02:00)
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Sechs Versionsstellen tragen dieselbe Zeichenkette 0.1.10, und in den sieben berührten Dateien gibt es keinen 0.1.9-Rest mehr
- Kein Zeilenenden-Massen-Diff: die vier CRLF-Dateien wurden byte-exakt gepatcht, ihre CRLF-Zahlen (536, 551, 570, 540) sind vor und nach dem Schreiben identisch
- uv.lock ist als sechste Stelle mitgezogen, ohne dass eine Dependency-Zeile sich bewegt hat; kein uv lock, kein uv sync, kein Paket installiert
- Der Changelog-Block 0.1.10 steht über dem 0.1.9-Block, trägt genau zwei Rubriken und ist mit genau einer Linkdefinition gepaart
- Kein Tag v0.1.10 existiert; das Manifest-Gate ist nach beiden Tasks grün

## Das Datum der Kopfzeile, für Plan 15-03

Die Kopfzeile lautet wörtlich:

```
## [0.1.10] - 2026-08-28
```

Das ist der lokale Kalendertag des Schreibens (Europe/Berlin, 2026-08-28 01:20). In UTC war zum Zeitpunkt beider Commits noch der 2026-08-27 (23:20:51Z und 23:22:01Z), die Commit-Zeitstempel im Log tragen entsprechend `2026-08-28T01:20:51+02:00` und `2026-08-28T01:22:01+02:00`. Wer das Datum in UTC nachrechnet, findet also einen Tag Differenz, ohne dass ein Fehler vorliegt.

**Auftrag an Plan 15-03:** vor dem Tag den Kalendertag prüfen. Entsteht der Tag v0.1.10 an einem anderen Kalendertag als dem 2026-08-28, muss diese eine Zeile auf den Tag-Tag gehoben werden, denn ein Release-Notes-Datum, das nicht der Tag-Tag ist, ist im veröffentlichten Asset unveränderlich falsch.

## Die sechs Versionsstellen und ihr Nachweis

| Stelle | Datei und Zeile | Nachweis |
|--------|-----------------|----------|
| Paketversion | `pyproject.toml:3` | `grep -c '^version = "0.1.10"'` gibt 1 |
| Laufzeit-Version | `src/mcp_connector/__init__.py:7` | `grep -c '^__version__ = "0.1.10"'` gibt 1 |
| Manifest-Version | `appinfo/info.xml:183` | `grep -o '<version>[^<]*'` gibt genau `<version>0.1.10` |
| Image-Tag | `appinfo/info.xml:258` | `grep -o '<image-tag>[^<]*'` gibt genau `<image-tag>0.1.10` |
| Statuszeilen der drei READMEs | `README.md:27`, `README.de.md:29`, `README.fr.md:31` | `grep -n '^Version 0\.1\.10\.'` gibt drei Treffer, einen je Datei |
| Lock-Version | `uv.lock:472` | `grep -n 'version = "0.1.10"' uv.lock` nennt Zeile 472 |

`grep -rn '0\.1\.9'` über alle sieben Dateien bleibt leer (rc=1). Die drei Zahlen 21 in "All 21 tools", "Alle 21 Tools" und "Les 21 outils" sind unangetastet: in dieser Phase wurde kein Werkzeug angefasst.

## Der Changelog-Block im Überblick

- Einleitungsabsatz in Prosa: kein Codewechsel, dieselben einundzwanzig Werkzeuge, geändert hat sich Text, und Text ist die Art Änderung, die nur ein Release zu den Lesern trägt
- `### Changed`: der Enterprise-Abschnitt in Store-Beschreibung und allen drei READMEs ist auf wenige Sätze gekürzt, die Kontaktadresse ist von `k.cherif@outlook.de` auf `admin@infranode.dev` gewechselt, keines der drei Vorhaben (Audit-Log, Gruppen-Policies, SSO über den Identitätsanbieter der Organisation) existiert in dieser Version in irgendeiner Einstellung, und die Begründung nennt die Uploadzeit samt 0.1.5, 0.1.6 und 0.1.9 in derselben Sache wie der 0.1.9-Block nach seiner Korrektur
- `### Fixed`: die französische Hauptüberschrift ist Französisch, das Scheinwort ist an beiden Fundstellen in README.fr.md ersetzt, README.de.md schreibt den Produktbegriff wie die deutsche Store-Summary; ausdrücklich als Wortkorrektur in den Lesefassungen ohne Verhaltensänderung benannt
- Keine weitere Rubrik, kein `## [Unreleased]`, keine `[Unreleased]`-Definition
- Am Dateiende genau eine neue Zeile, direkt über `[0.1.9]:`

```
[0.1.10]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.9...v0.1.10
```

## Was bewusst NICHT im Block steht

Fünf Änderungen der Phase 14 sind intern geblieben und namentlich ausgeschlossen: der Entscheid über die Reichweite des Vokabular-Gates und der Test dazu, der neu formulierte Ampersand-Kommentar in `appinfo/info.xml`, die Sortierung der Nachweistabelle im Runbook samt datiertem Nachtrag, und die Anhebung der GitHub-Actions auf ihre node24-Majors.

Ebenfalls nicht als Eintrag: die WR-02-Korrektur am 0.1.9-Block (Commit `9ac0a3c`). Sie ist Begründungsprosa im Block der Vorversion, und ein Eintrag darüber wäre ein Changelog-Eintrag über den Changelog.

## W-1 aus dem v1.3-Audit ist mit diesem Block auf dem Weg ins Asset

Der Tech-Debt-Punkt W-1 aus `.planning/milestones/v1.3-MILESTONE-AUDIT.md` lautet: "CHANGELOG.md-Drift zwischen signiertem 0.1.9-Asset und Repo (WR-02-Korrektur 9ac0a3c nach dem Tag; nur Begründungsprosa, fährt mit dem nächsten Release mit)".

Das nächste Release ist 0.1.10, und dieser Plan hat seinen Changelog geschrieben. Der 0.1.9-Block liegt damit in der korrigierten Fassung in derselben Datei, die im 0.1.10-Tarball mitreist; das signierte 0.1.9-Asset behält seine alte Fassung, das ist unveränderlich und war nie anders zu haben. **W-1 ist mit dem Upload von 0.1.10 geschlossen, ohne einen eigenen Changelog-Eintrag bekommen zu haben.** Plan 15-04 kann den Punkt beim Abschluss als erledigt vermerken.

## Task Commits

1. **Task 1: Sechs Versionsstellen auf 0.1.10** - `c80a45c` (chore)
2. **Task 2: Changelog-Block 0.1.10 mit Enterprise-Kürzung und Kontaktwechsel** - `9829f1e` (docs)

## Files Created/Modified

- `pyproject.toml` - Paketversion 0.1.10
- `src/mcp_connector/__init__.py` - `__version__` 0.1.10
- `appinfo/info.xml` - `<version>` und `<image-tag>` 0.1.10, sonst nichts
- `uv.lock` - Versionszeile des eigenen Pakets, per Texteditierung
- `README.md`, `README.de.md`, `README.fr.md` - je die Statuszeile des Abschnitts Status
- `CHANGELOG.md` - Block `## [0.1.10] - 2026-08-28` plus Linkdefinition `[0.1.10]:`
- `.planning/phases/15-release-0-1-10/15-01-SUMMARY.md` - diese Datei

## Decisions Made

- Kopfzeilendatum 2026-08-28 (lokaler Kalendertag), mit dem Prüfauftrag an Plan 15-03 oben
- EXAPP-10 bleibt Pending, weil die Anforderung den Store nennt und dieser Plan weder Tag noch Upload erzeugt
- Die WR-02-Korrektur bleibt ohne eigenen Eintrag, ihre Veröffentlichung wird stattdessen hier belegt

## Deviations from Plan

Keine inhaltliche Abweichung. Zwei Präzisierungen zu Formulierungen im Plan, beide ohne Auswirkung auf das Ergebnis:

**1. Akzeptanzkriterium "1 1 je Datei" trifft für appinfo/info.xml nicht zu**
- **Gefunden bei:** Task 1, Prüfung von `git diff --numstat`
- **Sachlage:** Der Plan zählt selbst sieben Zeilen mit 0.1.9 in sieben Dateien und benennt zwei davon in `appinfo/info.xml` (`<version>` und `<image-tag>`). Damit kann diese eine Datei nicht `1	1` liefern, sie liefert zwangsläufig `2	2`. Das Kriterium ist als "gleich viele hinzugefügte wie entfernte Zeilen, keine Zeilenenden-Umschreibung" gelesen und in dieser Lesart erfüllt: `1	1` für die sechs übrigen Dateien, `2	2` für `appinfo/info.xml`.
- **Kein Code geändert.**

**2. Akzeptanzkriterium zum Dependency-freien Diff präzisiert auf geänderte Zeilen**
- **Gefunden bei:** Task 1, Prüfung von `git diff -- pyproject.toml uv.lock`
- **Sachlage:** Der Standard-Diff mit drei Zeilen Kontext zeigt ` dependencies = [` aus `uv.lock:474`, weil diese Zeile zwei Zeilen unter der geänderten liegt. Das ist eine Kontextzeile, keine Änderung. Nachgeprüft mit `git diff -U0`, das ausschließlich die tatsächlich geänderten Zeilen zeigt: dort stehen genau die vier Zeilen `-version = "0.1.9"` und `+version = "0.1.10"` je Datei, und der Grep nach `dependencies` oder `requires-dist` bleibt leer (rc=1).
- **Kein Code geändert.**

Kein Paketmanager-Aufruf, kein Tag, kein Push: `git tag --list v0.1.10` ist nach beiden Tasks leer, alle Prüfläufe liefen mit `uv run --no-sync`.

## Verification

| Kriterium | Ergebnis |
|-----------|----------|
| Sechs Versionsstellen auf 0.1.10 | alle sechs, Nachweistabelle oben |
| `grep -rn '0\.1\.9'` über die sieben Dateien | keine Zeile (rc=1) |
| `git diff --numstat HEAD~2 HEAD` | `1	1` je Datei, `2	2` für appinfo/info.xml, `28	0` für CHANGELOG.md |
| CRLF-Zahlen vor und nach dem Patchen | 536 / 551 / 570 / 540, unverändert |
| `git diff -U0 -- pyproject.toml uv.lock`, Grep auf `dependencies` und `requires-dist` | keine Zeile (rc=1) |
| `git diff -- appinfo/info.xml`, Grep auf `<summary`, `<description`, `Enterprise`, `admin@infranode.dev`, `<default` | keine Zeile (rc=1) |
| `xml.etree.ElementTree.parse("appinfo/info.xml")` | parst ohne Fehler |
| Reihenfolge der Blöcke | Zeile 12 `## [0.1.10] - 2026-08-28`, Zeile 39 `## [0.1.9] - 2026-08-25` |
| `admin@infranode.dev` im Changelog | 1 Treffer, Zeile 22, also oberhalb des 0.1.9-Blocks |
| Rubriken im 0.1.10-Block | genau `### Changed` und `### Fixed` |
| Verbotene Begriffe im Block (`Unreleased`, Runbook-Dateiname, `node24`, Gate-Konstante, `WR-02`) | keine Zeile (rc=1) |
| `grep -c 'Unreleased' CHANGELOG.md` | 0 |
| `grep -c 'compare/v0.1.9...v0.1.10' CHANGELOG.md` | 1 |
| Abschnitte gegen Linkdefinitionen | 11 gegen 11, `diff` der sortierten Versionsmengen leer |
| Vokabular-Gate-Wort in CHANGELOG.md | keine Zeile (rc=1) |
| `grep -c '—' CHANGELOG.md` | 0 |
| CRLF in CHANGELOG.md | 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, nach Task 1 und nach Task 2 |
| `uv run --no-sync ruff check .` / `ruff format --check .` | All checks passed / 198 files already formatted |
| `git tag --list v0.1.10` | keine Zeile |
| `git diff --diff-filter=D` je Commit | keine Löschung einer verfolgten Datei |

## Issues Encountered

Beim Staging der drei LF-Dateien warnt git "LF will be replaced by CRLF the next time Git touches it". Das ist die vorhandene Zeilenenden-Konfiguration des Repos und keine Folge dieser Änderung: die Commits nennen für jede dieser Dateien genau eine hinzugefügte und eine entfernte Zeile. Dieselbe Warnung stand schon in Phase 14.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Der 0.1.10-Kandidat ist benannt: `scripts/build_store_release.sh` liest `appinfo/info.xml` und benennt den Tarball nach 0.1.10, `release.yml` akzeptiert den Tag v0.1.10
- Offen in dieser Phase: Plan 15-02, dann Plan 15-03 mit der Datumsprüfung der Changelog-Kopfzeile und dem Tag nach ausdrücklicher Owner-Freigabe, dann Plan 15-04
- EXAPP-10 bleibt Pending, bis Asset, Signatur und Store-Upload vorliegen
- W-1 aus dem v1.3-Audit ist mit dem Upload von 0.1.10 geschlossen

## Self-Check: PASSED

- Alle acht geänderten Dateien und diese Summary existieren auf der Platte
- Beide Task-Commits liegen im Log: `c80a45c`, `9829f1e`
- Echte Umlaute, keine Emojis; der einzige Treffer für Em- und En-Dashes ist das zitierte Grep-Muster in der Prüftabelle, also das Suchmuster selbst und keine Prosa

---
*Phase: 15-release-0-1-10*
*Completed: 2026-08-28*
