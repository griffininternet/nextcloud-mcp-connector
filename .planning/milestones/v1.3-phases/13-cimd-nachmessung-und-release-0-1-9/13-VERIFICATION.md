---
phase: 13-cimd-nachmessung-und-release-0-1-9
verified: 2026-08-25T21:15:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 13: CIMD-Nachmessung und Release 0.1.9 Verification Report

**Phase Goal:** Der CIMD-Weg ist nach den v1.1-Review-Fixes nicht mehr behauptet, sondern gegen
die laufende Topologie nachgemessen, und die Fassung aus Phase 12 liegt als Release 0.1.9 im
Nextcloud App Store, mit Proof-Zeilen für jeden Runbook-Schritt und einem Tag, der erst nach
ausdrücklicher Owner-Freigabe entstanden ist.

**Verified:** 2026-08-25T21:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CIMD-Weg live gegen den 0.1.9-Kandidaten nachgemessen (nicht nur behauptet) | VERIFIED | `docs/oauth-setup.md:318-343` trägt eine zweite, datierte Messung "Measured live on 2026-08-25 again ... against the 0.1.9 candidate", inklusive Image-Digest `sha256:1183f845...`, `client_id`-Nachweis, Abwesenheit von `POST /register`, Consent-Host, Token-200, echter Werkzeuginhalt und einer zweiten Gegenprobe mit `NC_MCP_OAUTH_CIMD=0`. Rohprotokoll in `13-MEASUREMENTS.md` (Topologie-Tabelle mit Digest, Rundlauf, Gegenprobe mit Socketzählung 0 vs. 5) |
| 2 | Version 0.1.9 an allen sechs Stellen als derselbe String | VERIFIED | grep bestätigt: `pyproject.toml:3`, `src/mcp_connector/__init__.py:7`, `appinfo/info.xml:189,263`, `README.md:27`, `README.de.md:29`, `README.fr.md:31`, `uv.lock:472` — alle `0.1.9` |
| 3 | Changelog-Block 0.1.9 nennt `message_truncated` als Formatänderung, README-Provider-Korrektur und Enterprise-Abschnitt | VERIFIED | `CHANGELOG.md:12-47`, Block `## [0.1.9] - 2026-08-25` mit `### Added` (Enterprise), `### Changed` (`message_truncated`), `### Fixed` (`talk-conversations`); Link-Referenzen `compare/v0.1.8...v0.1.9` und `compare/v0.1.9...HEAD` auf Zeile 480-481 |
| 4 | Alle Gates laufen lokal grün (inkl. Vokabular-Gate Phase-12-Reichweite) | VERIFIED | `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py tests/contract/test_tool_surface.py -q` lief in dieser Verifikation erneut, alle Tests grün (keine FAILED-Zeilen); Proof-Zeile 2026-08-25 18:13Z in `docs/store-submission.md:135` nennt alle sechs Kommandos mit Exit 0 |
| 5 | Branch gepusht, bevor irgendein Tag existiert | VERIFIED | Proof-Zeile 18:21Z (`docs/store-submission.md:136`): `origin/main`/`HEAD` beide `22471c1`, `git tag --list v0.1.9` leer zu diesem Zeitpunkt; erst danach folgt die Tag-Zeile |
| 6 | Tag v0.1.9 entsteht erst nach ausdrücklicher Owner-Freigabe | VERIFIED | `13-05-SUMMARY.md` Checkpoint-Tabelle: wörtliche Antwort `freigeben` um 2026-08-25T18:27Z über den Orchestrator; Tag wurde danach (18:30Z) gesetzt. `git tag --list v0.1.9` und `git rev-parse v0.1.9` in dieser Verifikation zeigen den Tag lokal vorhanden auf `685295d7d1e0ac227d6611d33fb3eb799351c800`, konsistent mit der SUMMARY |
| 7 | Signiert wurde das heruntergeladene Release-Asset, nicht das lokal gebaute | VERIFIED | Proof-Zeile 18:39Z (`docs/store-submission.md:138`): 47264 Bytes (Download) gegen 47546 Bytes (`dist/`), unterschiedliche sha256, `Verified OK` über das heruntergeladene Artefakt |
| 8 | Release 0.1.9 im Store gelistet, Runbook-Schritte 4-8 mit Proof-Zeilen | VERIFIED | Proof-Zeilen 18:30Z, 18:39Z, 18:40Z, 18:46Z, 18:41Z (x3) in `docs/store-submission.md:137-143`; Store-POST 201, Katalog-Endpoint nennt `0.1.9`, OCI-Index beide Plattformen, Tagliste zehn Tags inkl. `0.1.9` |
| 9 | Review-Warnings WR-01 bis WR-03 tatsächlich gefixt (nicht nur als "FIXED" behauptet) | VERIFIED | Commits `c564a6b`, `9ac0a3c`, `f3faefd` existieren in der Historie; Inhalt bestätigt: `docs/store-submission.md:135` nennt jetzt korrekt "the phase 12 measurement... the v1.2 baseline was 15612"; `CHANGELOG.md:24-27` nennt die korrigierte Cache-Begründung; `docs/contrib/enterprise-signals-issue.md` Kopf ist auf Metadaten reduziert, Go-Kriterium liegt in `.planning/.../enterprise-issue-go-kriterium.md` |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/store-submission.md` | Proof-Zeilen für Schritte 1-8, 0.1.9 | VERIFIED | 11 datierte Zeilen für 0.1.9 (18:13Z bis 18:46Z), alle Schritte 1-8 abgedeckt, keine Zeile läuft ihrem Ereignis voraus |
| `docs/oauth-setup.md` | Datierte, selbsttragende CIMD-Proof-Zeile ohne Nachbarverweis | VERIFIED | Zeilen 318-343, kein `.planning`-Pfad mehr in der Datei (`grep -n '\.planning'` leer) |
| `CHANGELOG.md` | 0.1.9-Block mit Enterprise/message_truncated/talk-conversations | VERIFIED | Block Zeile 12-47, korrekt referenziert |
| `appinfo/info.xml`, `pyproject.toml`, `__init__.py`, `README*.md`, `uv.lock` | Sechs Versionsstellen 0.1.9 | VERIFIED | Alle sechs Stellen bestätigt per grep |
| `.planning/phases/13.../13-MEASUREMENTS.md` | Rohprotokoll Topologie, Rundlauf, Gegenprobe | VERIFIED | 550+ Zeilen, Digest, Socketzählung 0 vs. 5, Konventionen (Credential-Kürzung) eingehalten |
| Git Tag `v0.1.9` | Existiert erst nach Freigabe, zeigt auf 685295d | VERIFIED | `git rev-parse v0.1.9` = `685295d7d1e0ac227d6611d33fb3eb799351c800` |
| `docs/contrib/enterprise-signals-issue.md` | Issue-Entwurf, nicht veröffentlicht, Go-Kriterium ausgelagert | VERIFIED | Datei vorhanden, Kopf reduziert nach WR-03-Fix, kein `gh issue create` in der Historie |
| `.planning/REQUIREMENTS.md` | EXAPP-08/09 Complete, keine Waisen | VERIFIED | Beide als Complete markiert, Mapping 6/6, "keine Waisen" |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `appinfo/info.xml` `<version>`/`<image-tag>` | `src/mcp_connector/__init__.py` `__version__` | Manifest-Gate `test_exapp_env_setup.py` | WIRED | Gate lief grün in dieser Verifikation, alle drei Stellen `0.1.9` |
| Tag `v0.1.9` | `appinfo/info.xml <version>` | Versions-Gleichheitsprüfung in `.github/workflows/release.yml`, Release-Lauf `32883904698` | WIRED | Lauf laut SUMMARY `success`, Job `publish` 1m40s; Tag und Version stimmen überein |
| `docs/oauth-setup.md` Proof-Zeile | keine Nachbardatei | Selbsttragende Aussage | WIRED | `grep -n '\.planning' docs/oauth-setup.md` liefert keinen Treffer |
| heruntergeladenes Asset | Signatur | `openssl dgst -sha512 -sign/-verify` über das Download-Artefakt | WIRED | Proof-Zeile 18:39Z nennt `Verified OK` über die 47264-Byte-Datei, nicht über `dist/` |
| Store-Katalog `apps.nextcloud.com` | GitHub Release Asset URL | AppAPI installiert von der URL, Store hält nur Metadaten | WIRED | Proof-Zeilen 18:40Z/18:46Z/18:41Z belegen 201, Katalogeintrag und Asset-Erreichbarkeit (302→200) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Manifest-/Vokabular-Gate grün | `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py tests/contract/test_tool_surface.py -q` | Alle Tests grün, keine Failures im Output | PASS |
| Sechs Versionsstellen konsistent | grep je Datei | Alle sechs Treffer `0.1.9` | PASS |
| Kein Em-Dash in geänderten Dateien | `grep -c '—'` über CHANGELOG.md, README*.md, docs/oauth-setup.md, docs/store-submission.md, appinfo/info.xml, enterprise-signals-issue.md | 0 überall | PASS |
| Review-Fix-Commits existieren real | `git cat-file -t c564a6b/9ac0a3c/f3faefd` | alle `commit` | PASS |
| Tag zeigt auf dokumentierten Commit | `git rev-parse v0.1.9` | `685295d7d1e0ac227d6611d33fb3eb799351c800`, deckt sich mit SUMMARY | PASS |

### Probe Execution

Kein dediziertes Probe-Skript (`scripts/*/tests/probe-*.sh`) für diese Phase gefunden oder deklariert. SKIPPED — kein konventionelles Probe-Muster in PLAN/SUMMARY referenziert; die Phase nutzt stattdessen Live-Messungen gegen die laufende Docker-Topologie, dokumentiert in `13-MEASUREMENTS.md` und den Proof-Zeilen, welche oben unter Observable Truths und Behavioral Spot-Checks geprüft wurden.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| EXAPP-08 | 13-03 | CIMD-Weg live nachgemessen gegen laufende Topologie mit Proof-Zeile | SATISFIED | `docs/oauth-setup.md:318-343`, `13-MEASUREMENTS.md` |
| EXAPP-09 | 13-01, 13-02, 13-04, 13-05, 13-06 | Release 0.1.9 im Store, alle Runbook-Schritte mit Proof-Zeilen, Tag nach Owner-Freigabe | SATISFIED | `docs/store-submission.md` Zeilen 133-143, Tag `v0.1.9`, `13-05-SUMMARY.md`, `13-06-SUMMARY.md` |

Keine Waisen: `.planning/REQUIREMENTS.md:57` bestätigt "Mapped to phases: 6 von 6 (Phase 12: 4, Phase 13: 2); keine Waisen, keine Dopplungen".

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.planning/ROADMAP.md` | 87 | Phase-Checkbox `[ ]` (statt `[x]`) im "v1.3 Pflege"-Abschnitt, obwohl Wave-Checkboxen, Progress-Tabelle (6/6, Complete) und STATE.md (`status: milestone-complete`) die Phase als abgeschlossen ausweisen | INFO | Rein kosmetische Inkonsistenz in der Roadmap-Übersichtszeile; beeinflusst nicht die tatsächliche Zielerreichung, da alle anderen Quellen (Progress-Tabelle, Wave-Checkboxen, STATE.md, REQUIREMENTS.md) konsistent "Complete" zeigen. Sollte beim nächsten Doku-Edit mitgezogen werden |

Keine TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER-Marker in den geänderten Dateien gefunden. Die drei Review-Warnungen WR-01 bis WR-03 sind über echte Commits gefixt, nicht nur im Review-Report als "FIXED" behauptet (siehe Truth 9). Die sieben Info-Punkte (IN-01 bis IN-07) aus `13-REVIEW.md` sind laut Review-Report nicht als Warnungen oder Blocker eingestuft und wurden nicht zwingend gefixt; sie betreffen kleinere Formulierungs- und Reihenfolgefragen, keine Zielverfehlung.

### Human Verification Required

Keine offenen Punkte. Alle sicherheits- und beweisrelevanten Schritte (Owner-Freigabe, Signaturprüfung, Store-Annahme) sind bereits durch den blockierenden Checkpoint in Plan 13-05 durchlaufen und mit Zeitstempel dokumentiert; die Verifikation konnte sie über Git-Historie, Dateiinhalt und Testlauf nachvollziehen, ohne dass eine subjektive oder visuelle Prüfung offen bleibt.

### Gaps Summary

Keine Gaps. Alle neun abgeleiteten Wahrheiten sind durch Codebase-Evidenz bestätigt (Versionsstellen, Changelog-Block, Live-Nachmessung des CIMD-Wegs mit Gegenprobe, Push-vor-Tag-Reihenfolge, Owner-Freigabe wörtlich protokolliert, Tag auf dokumentiertem Commit, Signatur über das heruntergeladene statt das lokal gebaute Artefakt, Store-Annahme mit 201 und Katalogeintrag, sowie real committete Fixes der drei Review-Warnungen). Der einzige gefundene Befund ist eine kosmetische Checkbox-Inkonsistenz in ROADMAP.md ohne Auswirkung auf die Zielerreichung.

---

_Verified: 2026-08-25T21:15:00Z_
_Verifier: Claude (gsd-verifier)_

## Nachtrag 2026-08-28 (Milestone v1.4, Phase 14, DOC-02)

`docs/contrib/enterprise-signals-issue.md` ist seit Commit `f9b3d2d` vom 2026-08-26 nicht
mehr im Repository. Die Commit-Botschaft lautet "docs: remove enterprise issue draft from
repo per owner decision (D-07: no issue, no internals in repo)".

Derselbe Commit `f9b3d2d` hat auch
`.planning/phases/13-cimd-nachmessung-und-release-0-1-9/enterprise-issue-go-kriterium.md`
entfernt, das Truth 9 (Zeile 34) als Ablageort des Go-Kriteriums nennt; auch diese
Nennung war am Prüfzeitpunkt richtig und bleibt unverändert.

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
