---
phase: 14-doku-reste-und-gate-entscheid
reviewed: 2026-08-27T22:51:53Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - README.fr.md
  - README.de.md
  - CHANGELOG.md
  - appinfo/info.xml
  - docs/store-submission.md
  - .planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md
  - tests/unit/test_exapp_env_setup.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-08-27T22:51:53Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Geprüft wurden die sieben Dateien der Doku-/Gate-Phase 14 gegen die git-Historie ab `c020c60`. Die Kernaussage vorab, weil sie den Prüfschwerpunkten entspricht: **keine Proof-Aussage wurde verfälscht.**

- Die Umsortierung der Proof-Zeilen in `docs/store-submission.md` ist rein positionell (Diff zeigt nur verschobene, inhaltlich identische Zeilen), und die Tabelle ist danach durchgehend chronologisch monoton.
- Die präzisierte 18:30Z-Zeile ist gegen die Historie verifiziert: `v0.1.9` zeigt auf `685295d`, dessen Parent ist `22471c1`, und `685295d` ist exakt ein Commit mit genau einer eingefügten Zeile in `docs/store-submission.md` ("docs(13-05): the proof line of the branch push, before any tag exists"). Die alte Formulierung ("the commit `main` already carried") war sachlich falsch, die neue ist belegt richtig.
- Der Nachtrag in der archivierten `13-VERIFICATION.md` ist rein additiv (Diff: nur angefügte Zeilen ab Zeile 103). Die zitierten Commits existieren und stimmen: `f9b3d2d` (2026-08-26, Commit-Botschaft wortgleich, löscht die Datei), `c564a6b`/`9ac0a3c`/`f3faefd` (alle `commit`). Die Zeilenverweise des Nachtrags (34, 48, 67) treffen die richtigen Stellen, und das IN-04-Zitat deckt sich mit `13-REVIEW.md:101-104`.
- `appinfo/info.xml` ist wohlgeformt (Parser-Check bestanden), keine `--`-Sequenz in Kommentaren, und der neu formulierte Ampersand-Kommentar korrigiert eine vorher falsche Behauptung (die paypal.me-Adresse trug nie ein Ampersand).
- Die drei Übersetzungsfixes sind korrekt und vollständig: kein `confidemment`, kein "for Nextcloud" mehr in `README.fr.md`, kein kleingeschriebenes "MCP server" mehr in `README.de.md`.
- Die entfernte `[Unreleased]`-Linkdefinition war tatsächlich hängend (kein `## [Unreleased]`-Abschnitt, keine automatisierte Abhängigkeit in tests/scripts/.github).
- Der neue Gate-Test läuft grün (alle 153 Tests des Moduls bestanden), das Vokabular-Gate greift, "archiv" kommt in keiner öffentlichen der geprüften Dateien vor, keine Em-Dashes im neuen Text, `pyproject.toml:56` bestätigt die im Docstring behauptete ruff-Ausnahme.

Drei Warnungen bleiben, alle in der Kategorie "die Phase wendet ihren eigenen Standard nicht vollständig an".

## Warnings

### WR-01: Nachtrag dokumentiert nur eine von zwei gelöschten Belegdateien

**File:** `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md:107-115`
**Issue:** Commit `f9b3d2d` hat nicht nur `docs/contrib/enterprise-signals-issue.md` entfernt, sondern auch `.planning/phases/13-cimd-nachmessung-und-release-0-1-9/enterprise-issue-go-kriterium.md` (git show f9b3d2d, drei Pfade). Truth 9 (Zeile 34) zitiert genau diese zweite Datei als Beleg: "Go-Kriterium liegt in `.planning/.../enterprise-issue-go-kriterium.md`". Der Nachtrag, dessen einziger Zweck die Dokumentation der Bericht-Repo-Drift ist (DOC-02, W-2), nennt nur die erste Datei. Ein Leser, der Truth 9 heute nachvollzieht, findet auch die zweite zitierte Datei nicht mehr, ohne dass der Nachtrag ihn darauf vorbereitet.
**Fix:** Einen Satz an den Nachtrag anfügen (nur anfügen, nicht umschreiben):
```markdown
Derselbe Commit `f9b3d2d` hat auch
`.planning/phases/13-cimd-nachmessung-und-release-0-1-9/enterprise-issue-go-kriterium.md`
entfernt, das Truth 9 (Zeile 34) als Ablageort des Go-Kriteriums nennt; auch diese
Nennung war am Prüfzeitpunkt richtig und bleibt unverändert.
```

### WR-02: ASCII-Ersatz "unabhaengig" statt "unabhängig" im neu geschriebenen Nachtrag

**File:** `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md:121`
**Issue:** "Alle drei sind in der Historie nachweisbar, unabhaengig davon, ..." verletzt die Projektregel (Umlaute immer, nie ae/oe/ue/ss, gilt auch in Markdown) und ist im selben Absatz inkonsistent: vier Zeilen darüber steht korrekt "hängt". Der Nachtrag ist Phase-14-Neutext, kein archivierter Bestand, und darf daher korrigiert werden.
**Fix:**
```markdown
Historie nachweisbar, unabhängig davon, ob die vierte Datei heute noch existiert.
```

### WR-03: Die Entfernung der [Unreleased]-Linkdefinition erzeugt selbst eine neue, unvermerkte Bericht-Repo-Drift

**File:** `CHANGELOG.md:479` (entfernte Zeile), betrifft `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md:28` und `docs/store-submission.md:137`
**Issue:** Die Entfernung selbst ist richtig (der Link war hängend, nichts Automatisiertes hängt daran). Aber zwei archivierte Belege zitieren den Link als vorhanden: 13-VERIFICATION Truth 3 (Zeile 28: "Link-Referenzen `compare/v0.1.8...v0.1.9` und `compare/v0.1.9...HEAD` auf Zeile 480-481") und die Proof-Zeile 18:14Z in `docs/store-submission.md:137` (`grep -n 'compare/v0.1.9' CHANGELOG.md` nennt Zeile 479, ein grep, das heute leer ausgeht, weil `compare/v0.1.9` in `compare/v0.1.8...v0.1.9` nicht als Substring vorkommt). Genau für diese Klasse von Drift stellt dieselbe Phase im Nachtrag den Standard auf: die alte Aussage bleibt stehen, ein datierter Vermerk erklärt die Abweichung. Für die Drift, die die Phase selbst erzeugt hat, fehlt dieser Vermerk.
**Fix:** Einen datierten Satz an den bestehenden Nachtrag in 13-VERIFICATION anfügen, z. B.:
```markdown
Ebenfalls seit Phase 14: die hängende Linkdefinition `[Unreleased]` wurde aus
`CHANGELOG.md` entfernt, sodass die Zeile-28-Evidenz (`compare/v0.1.9...HEAD`) und der
grep der 18:14Z-Proof-Zeile in `docs/store-submission.md` heute nicht mehr greifen;
beide waren am 2026-08-25 richtig.
```

## Info

### IN-01: Zeilenzitate der 13-VERIFICATION auf store-submission.md sind durch die Umsortierung teilweise verschoben

**File:** `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md:33`
**Issue:** "Proof-Zeilen 18:30Z, 18:39Z, 18:40Z, 18:46Z, 18:41Z (x3) in `docs/store-submission.md:137-143`" trifft nach den +2 Kopfzeilen und der Umsortierung heute die Zeilen 139-145. Das Zitat `:135` in Truth 9 und Truth 4 stimmt zufällig weiter (die 18:13Z-Zeile rückte zwei Positionen nach vorn und zwei Zeilen nach hinten). Archivbestand, war am Prüfzeitpunkt richtig.
**Fix:** Kann im selben Nachtrag-Satz wie WR-03 miterledigt werden ("Zeilenzitate auf docs/store-submission.md haben sich um zwei verschoben"); keine Umschreibung des Berichts.

### IN-02: Neuer Gate-Test ohne Counter-Probe, erste Hälfte kann strukturell nicht feuern

**File:** `tests/unit/test_exapp_env_setup.py:2132-2149`
**Issue:** `test_the_vocabulary_gate_stops_at_the_internal_planning_area` ist kein Tautologie-Fall: die erste Schleife wird rot, sobald jemand `public_markdown_pages()` auf `.planning` ausweitet (das ist ihr erklärter Zweck), und die zweite Schleife hat mit `archive_members()` einen realen Fehlmodus (Build-Skript kopiert eine .planning-Datei). Aber die Datei-Konvention verlangt für jedes Gate eine Counter-Probe ("a gate that was never seen failing is not a gate", Zeile 165-167), und dieser Test hat keine: beim heutigen Aufbau der Funktion kann `".planning" in page.parts` nie wahr werden, der Test wurde also nie feuern gesehen.
**Fix:** Kleine Counter-Probe ergänzen, z. B. die Schleifenbedingung gegen einen konstruierten Pfad prüfen: `assert ".planning" in (ROOT / ".planning" / "x.md").parts`, oder die Prüfung in eine Hilfsfunktion ziehen, die ein Probe-Test mit `[ROOT / ".planning" / "x.md"]` füttert.

### IN-03: Öffentliches Doc verweist weiterhin auf internen .planning-Pfad

**File:** `docs/store-submission.md:12`
**Issue:** Der Verweis auf `.planning/phases/05-store-research.md` bleibt in einem veröffentlichten Doc stehen. Die Neuformulierung entschärft das bewusst ("an internal note that may disappear: ... no claim on this page leans on that note"), und die Datei existiert derzeit noch. Kein Handlungsbedarf; nur festgehalten, dass die Nennung eines internen Pfads in der öffentlichen Doku eine bewusste Entscheidung dieser Phase ist.
**Fix:** Keiner nötig; alternativ den Pfad ganz streichen, da die Seite ihn erklärtermaßen nicht braucht.

### IN-04: Em-Dashes im archivierten Teil der 13-VERIFICATION

**File:** `.planning/milestones/v1.3-phases/13-cimd-nachmessung-und-release-0-1-9/13-VERIFICATION.md:18,27,67,73`
**Issue:** Vier Em-Dashes im Bestand vom 2026-08-25 verletzen die Projektregel, liegen aber vor dem Phase-14-Diff (der Nachtrag selbst ist sauber). Nach dem Archiv-Prinzip der Phase dürfen sie nicht nachträglich umgeschrieben werden.
**Fix:** Keine Aktion; als bekannter Bestand akzeptieren.

---

_Reviewed: 2026-08-27T22:51:53Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
