---
phase: 13-cimd-nachmessung-und-release-0-1-9
reviewed: 2026-08-25T18:58:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - CHANGELOG.md
  - README.de.md
  - README.fr.md
  - README.md
  - appinfo/info.xml
  - docs/contrib/enterprise-signals-issue.md
  - docs/oauth-setup.md
  - docs/store-submission.md
  - pyproject.toml
  - src/mcp_connector/__init__.py
  - uv.lock
findings:
  critical: 0
  warning: 3
  info: 7
  total: 10
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-08-25T18:58:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Narrative Findings (AI reviewer)

### Zusammenfassung

Geprüft wurden die elf Dateien des Release-und-Doku-Zyklus 0.1.9 gegen die Diff-Basis `dfee4f8`, mit den vorgegebenen Schwerpunkten. Die Kernpunkte halten:

- **Versions-Konsistenz:** Alle sechs Stellen tragen `0.1.9` und wurden einzeln verifiziert: `pyproject.toml:3`, `src/mcp_connector/__init__.py:7`, `appinfo/info.xml:189` (`<version>`), `appinfo/info.xml:263` (`<image-tag>`), die drei Statuszeilen `README.md:27`, `README.de.md:29`, `README.fr.md:31`, sowie `uv.lock:472`.
- **EN/DE/FR-Synchronität der Enterprise-Texte:** Alle sechs Fassungen (drei READMEs, drei info.xml-Descriptions) nennen dieselben drei Bausteine (Audit-Log, Gruppen-Policies, SSO), keinen Preis, den Kontakt k.cherif@outlook.de, und jede trägt den eigenen Ehrlichkeitssatz ("None of the three exists ... today" / "Keines der drei existiert heute ..." / "Aucun des trois n'existe aujourd'hui ...").
- **info.xml-XSD-Verträglichkeit:** Keine leeren Elemente (kein `<default>` in den Variablen), keine Backticks, Tabellen oder Bilder in den Descriptions, Elementreihenfolge unverändert, Summaries unter 128 Zeichen, keine `--`-Sequenzen in XML-Kommentaren.
- **Changelog-Korrektheit:** Der `message_truncated`-Umbau ist real und liegt nach v0.1.8 (Commit `066d8ec`, verifiziert in `src/mcp_connector/tools/talk.py:536` und `server/reg_talk.py:59`); `spreed` stand in allen drei READMEs von v0.1.8 (je 1 Treffer) und heißt jetzt `talk-conversations`; die Link-Referenzen `[0.1.9]` und `[Unreleased]` (Zeilen 479 bis 480) sind korrekt.
- **Keine Secrets:** Messprotokoll und Proof-Zeilen enthalten nur öffentliche Digests, Sha-Präfixe und den Pfad des Signaturschlüssels, keine Schlüsselwerte, Tokens oder Passwörter.
- **Keine Em-Dashes** (U+2014/U+2013) in allen elf Dateien; deutsche Texte mit echten Umlauten.

Gefunden wurden drei Warnungen (zwei Faktenfehler in Proof-Zeile bzw. Changelog, eine Strategie-Offenlegung im Issue-Entwurf) und sieben kleinere Punkte.

## Warnings

### WR-01: Proof-Zeile behauptet falsche Herkunft der Messzahl 15711

**File:** `docs/store-submission.md:135`
**Issue:** Die Step-3-Zeile sagt: "the tool surface measures 15711 bytes across 21 tools ... That is the same number the v1.2 measurement recorded, because this phase touched no tool and no docstring." Die v1.2-Messung hat aber 15612 Bytes festgehalten, nicht 15711: `.planning/MILESTONES.md:33` ("gerechnet aus 15612 gemessenen Bytes bei 21 Werkzeugen") und `CHANGELOG.md:114` (0.1.8: "15612 bytes across 21 tools"). Die 15711 stammen aus Phase 12 (Plan 12-01, `mail_browse`-Docstring, dokumentiert in `12-01-SUMMARY.md`: 15657 zu 15711). Die Kernaussage der Zeile (Phase 13 hat nichts angehoben) stimmt, aber die Herleitung ist falsch, und ein Leser, der die Proof-Zeile mit dem Changelog 0.1.8 vergleicht, findet einen Widerspruch in einem Dokument, dessen einziger Zweck belegbare Aussagen sind.
**Fix:** In der Zeile "the v1.2 measurement" durch die tatsächliche Referenz ersetzen, etwa:
```markdown
That is the same number the phase 12 measurement recorded (12-01, after the
mail_browse docstring change; the v1.2 baseline was 15612), because this phase
touched no tool and no docstring, and the budget was not raised to make it fit.
```

### WR-02: Changelog-0.1.9-Begründung widerspricht dem eigenen 0.1.5-Eintrag

**File:** `CHANGELOG.md:24-26`
**Issue:** Der Added-Eintrag von 0.1.9 schließt mit: "the description travels with this release because the store reads the manifest at upload time, which is what made the corrections of 0.1.5 and 0.1.6 invisible." Das ist doppelt schief: (1) Die Korrekturen von 0.1.5 und 0.1.6 wurden nicht unsichtbar, sie sind die heutige Store-Seite; unsichtbar war die 0.1.5-Änderung nur für Minuten. (2) Der 0.1.5-Eintrag derselben Datei (Zeilen 170 bis 176) benennt als Ursache ausdrücklich die Store-Caches ("the store serves the app page, the catalogue and the search index from caches that refresh minutes apart"), nicht das Manifest-Lesen beim Upload. Zwei Erklärungen desselben Vorfalls in einer Datei, von denen eine falsch ist, in einem Release-Dokument, dessen Korrektheit Prüfschwerpunkt war.
**Fix:** Den Halbsatz auf die tatsächlich gemeinte Aussage kürzen:
```markdown
the description travels with this release because the store reads the manifest
only at upload time, so a corrected text in the repository reaches nobody until
the next release; 0.1.5 and 0.1.6 were both releases for exactly that reason.
```

### WR-03: Internes Go-Kriterium des Fake-Door-Tests liegt im öffentlichen Repo

**File:** `docs/contrib/enterprise-signals-issue.md:1-14`
**Issue:** Der HTML-Kommentar am Dateikopf trägt die interne Versuchsanordnung in das öffentliche Repository: "Kind: fake door", das exakte Go-Kriterium ("at least five qualified organisation signals, each from an organisation with more than 100 users, within six weeks ... Anything short of that is a no-go and the add-on stays unbuilt") und den Hinweis "Not published ... owner decision (D-07)". Der Issue-Body selbst ist ehrlich (er sagt, dass nichts implementiert ist), aber die Schwelle, an der die Antworten gemessen werden, ist damit für genau die Zielgruppe lesbar, die sie messen soll, bevor der Owner über die Veröffentlichung entschieden hat. Das kontaminiert das Messergebnis des Experiments und legt Geschäftsstrategie offen, ohne dass es dafür einen Grund im Repo gibt.
**Fix:** Den Kommentarkopf auf die technischen Metadaten reduzieren (Ziel-Repo, Titel, "Not published, owner decision D-07") und Go-Kriterium samt Fake-Door-Einordnung in die private Planung verschieben (z. B. `.planning/`-Phase oder BACKLOG-Eintrag), bevor jemand die Datei zitiert.

## Info

### IN-01: Proof-Zeilen nicht chronologisch sortiert

**File:** `docs/store-submission.md:133-143`
**Issue:** Die Zeile 18:13Z (Step 3) steht nach den beiden 18:14Z-Zeilen, und die 18:46Z-Zeile (Katalog-Listing) steht vor den drei 18:41Z-Zeilen. In einer Tabelle, deren Beweiskraft auf der Reihenfolge beruht ("push before tag"), sollte die Zeilenfolge den Zeitstempeln folgen.
**Fix:** Zeilen 135 vor 133/134 bzw. 140 hinter 143 einsortieren, oder eine Notiz ergänzen, dass die Reihenfolge den Runbook-Schritten und nicht der Uhr folgt.

### IN-02: Tag-Commit 685295d ist nicht der Commit, den die 18:21Z-Zeile zertifiziert

**File:** `docs/store-submission.md:137`
**Issue:** Die 18:30Z-Zeile sagt, der Tag zeige auf "685295d, the commit `main` already carried ... which the row above records at 18:21Z". Die 18:21Z-Zeile zertifiziert aber `22471c1`; `685295d` ist ein Commit später (die Proof-Zeile selbst) und wurde erst durch das `git push origin main` derselben 18:30Z-Zeile öffentlich. Die Garantie "push before tag" hält (der Push steht in der Kommandospalte vor dem Tag), aber der Rückverweis auf die 18:21Z-Zeile deckt den getaggten Commit nicht ab.
**Fix:** Formulierung präzisieren: "points at 685295d, one commit after the 22471c1 of the row above (the proof line itself), pushed by the `git push origin main` of this step before the tag was created."

### IN-03: Veralteter Ampersand-Kommentar bei den Donation-Buttons

**File:** `appinfo/info.xml:229-231`
**Issue:** Der Kommentar sagt "The ampersand of the PayPal address is written as an entity because this is XML", aber die aktuelle URL `https://www.paypal.com/paypalme/KhaledCherifDev` enthält seit dem 0.1.8-Umbau auf paypal.me gar keinen Ampersand mehr. Der Kommentar beschreibt einen Zustand, den es nicht mehr gibt.
**Fix:** Die zwei Kommentarzeilen entfernen oder auf "a bare ampersand here would be a parse error" verallgemeinern.

### IN-04: SSO-Aufzählung des Issue-Entwurfs weicht vom README ab

**File:** `docs/contrib/enterprise-signals-issue.md:31-32`
**Issue:** Der Entwurf zitiert die drei README-Bausteine, lässt beim SSO-Punkt aber den Schluss "and a way to withdraw them" weg, den `README.md:527` trägt. Wer README und Issue nebeneinander liest, sieht zwei verschiedene Zusagen desselben geplanten Features.
**Fix:** "... the tokens that were handed out and a way to withdraw them." ergänzen.

### IN-05: Übersetzungsschwächen in DE- und FR-README

**File:** `README.de.md:7`, `README.de.md:22`, `README.fr.md:5`, `README.fr.md:274`, `README.fr.md:528`
**Issue:** Drei Kleinigkeiten in den nachgezogenen Fassungen: (1) `README.de.md:7` und `:22` schreiben "MCP server" klein, während `info.xml` (DE-Summary) "MCP Server" schreibt; im deutschen Satz ist die Großschreibung richtig. (2) Die FR-Hauptüberschrift `README.fr.md:5` lautet "MCP Connector for Nextcloud" mit englischem "for", während die DE-Fassung "für" übersetzt. (3) "confidemment" (`README.fr.md:274` und `:528`) ist kein französisches Wort; gemeint ist etwa "avec assurance" oder "de façon assurée".
**Fix:** "MCP Server" in DE, "MCP Connector pour Nextcloud" und "une réponse fausse mais assurée" (oder gleichwertig) in FR.

### IN-06: [Unreleased]-Linkdefinition ohne zugehörigen Abschnitt

**File:** `CHANGELOG.md:479`
**Issue:** Die Linkdefinition `[Unreleased]: .../compare/v0.1.9...HEAD` wurde korrekt auf v0.1.9 nachgezogen, aber die Datei enthält keinen Abschnitt `## [Unreleased]`, der sie referenziert. Keep a Changelog 1.1.0, auf das sich der Kopf der Datei beruft, sieht den Abschnitt vor; so ist es eine hängende Definition, die nichts rendert.
**Fix:** Entweder einen leeren `## [Unreleased]`-Abschnitt führen oder die Definition weglassen, bis es ungeröllte Änderungen gibt.

### IN-07: Verbleibender .planning-Verweis widerspricht der neuen Proof-Regel

**File:** `docs/store-submission.md:12`
**Issue:** Die Phase hat in `docs/oauth-setup.md` die Verweise auf Planungsnotizen mit der Begründung entfernt, "the notes of a release are removed once the release is out, and a proof that leans on them stops being a proof". `docs/store-submission.md:12` verweist weiterhin auf `.planning/phases/05-store-research.md`. Die Datei existiert heute und ist committet, aber der Verweis fällt unter genau die Regel, die die Phase selbst formuliert hat.
**Fix:** Die store-seitigen Fakten wie in oauth-setup.md inline benennen oder den Verweis als "internal note, may disappear" markieren.

---

_Reviewed: 2026-08-25T18:58:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
