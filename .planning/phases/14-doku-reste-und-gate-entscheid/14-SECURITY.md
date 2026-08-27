---
phase: 14
slug: doku-reste-und-gate-entscheid
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-28
---

# Phase 14 - Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register aus den `<threat_model>`-Blöcken von 14-01-PLAN.md und 14-02-PLAN.md
(register_authored_at_plan_time: true). Jede Mitigation wurde am 2026-08-28 direkt im
Repository nachgemessen, nicht aus den Summaries übernommen. Basis-Commit vor der Phase:
`31716bb`, geprüfter Stand: `34b8a69` (HEAD). T-14-SC ist in beiden Plänen identisch
deklariert und wird als ein Eintrag geführt.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Repo-Text zu Store-Text | appinfo/info.xml und CHANGELOG.md reisen im Store-Archiv; eine falsche Aussage wird mit dem nächsten Release veröffentlicht und ist im Asset unveränderlich | öffentliche Store-Texte |
| Übersetzung zu maßgeblicher Fassung | README.md ist maßgeblich; eine Korrektur in der Übersetzung darf die Bedeutung nicht verschieben | öffentliche Doku |
| Protokoll zu Leser | docs/store-submission.md und die abgelegte 13-VERIFICATION sind Beweisdokumente; ihre Aussagekraft hängt daran, dass sie nach dem Ereignis nicht mehr verändert werden | Proof-Zeilen, Verifikationsbefunde |
| Store-/Doku-Reichweite zu internem Planungsbereich | Das Vokabular-Gate schützt, was veröffentlicht wird; `.planning` liegt jenseits dieser Grenze, und die Grenze muss benannt und prüfbar sein | Gate-Reichweite |
| Repository zu Store-Archiv | `scripts/build_store_release.sh` entscheidet, was der Store bekommt; nur daran darf eine Ausnahme hängen, nicht an einer Zusicherung im Text | Archivmitglieder |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-14-01 | Tampering | README.fr.md, README.de.md | mitigate | Nur Wortersetzungen: `git show --numstat 75f1da2` nennt 2/2 (de) und 3/3 (fr); Greps auf `confidemment`, `MCP server` und englische Überschriften-Präpositionen leer, `réponse fausse mais assurée` 2x, Überschrift `# MCP Connector pour Nextcloud` auf Zeile 5 | closed |
| T-14-02 | Tampering | Enterprise-Abschnitt (Kürzung 55a5822) | mitigate | `git diff 31716bb..HEAD -U0 -- README.fr.md README.de.md` enthält 0 Treffer für `admin@infranode.dev`; die Nutzlast von Release 0.1.10 ist unangetastet | closed |
| T-14-03 | Repudiation | CHANGELOG.md | mitigate | `grep -n "Unreleased" CHANGELOG.md` leer; `[0.1.9]:`-Definition vorhanden (1x); Paarungsbeweis: diff der sortierten Versionsmengen aus `^\[..\]:` und `^## \[..\]` leer (10 gegen 10); `git show --numstat ef1cacf -- CHANGELOG.md` nennt 0/1 (nur die hängende Definition entfernt) | closed |
| T-14-04 | Tampering | appinfo/info.xml | mitigate | `git diff 31716bb..HEAD -U0 -- appinfo/info.xml` enthält ausschließlich die Kommentarzeilen des Ampersand-Blocks (2 entfernt, 3 hinzugefügt); `paypalme/KhaledCherifDev` 1x, `buy.stripe.com` 1x, keine `--`-Sequenz außerhalb der Begrenzer, `<version>0.1.9</version>` 1x unverändert; Manifest-Gate grün (153 passed) | closed |
| T-14-05 | Information Disclosure | Store-Texte (README.fr/de, CHANGELOG, info.xml) | accept | Alle vier Dateien sind bereits öffentlich; die Änderungen sind Wortkorrekturen ohne neue Information. Eintrag R-14-01 im Accepted Risks Log | closed |
| T-14-06 | Tampering | docs/store-submission.md, Proof-Zeilen | mitigate | `sort -c` über die Zeitstempel-Zeilen Exit 0; 64 Zeilen vor wie nach der Phase; sortierter Zeilenvergleich `git show 31716bb:docs/store-submission.md` gegen HEAD nennt genau eine geänderte Zeile, und das ist die 18:30Z-Zeile | closed |
| T-14-07 | Repudiation | 18:30Z-Zeile, Garantie "push before tag" | mitigate | Zeile 139 nennt `685295d` als "one commit after the `22471c1` that the row above certifies at 18:21Z"; `git rev-list --count 22471c1..685295d` gibt 1 (im Audit nachgemessen); `32883904698`, `47264` und `18:27Z` stehen weiter in der Zeile; `grep -c "row above"` gibt 4 | closed |
| T-14-08 | Tampering | abgelegte 13-VERIFICATION.md | mitigate | `git diff --numstat 31716bb..HEAD` nennt 42/0, also 0 entfernte Zeilen über die ganze Phase (die WR-02-Neutext-Korrektur `unabhaengig` zu `unabhängig` lag im Nachtrag selbst und saldiert sich im Phasen-Diff weg); Archivteil Zeile 1-103 byte-gleich zur Basis; Truth 9 (`^| 9 |`) byte-gleich; Nachtrag ab Zeile 105 mit `f9b3d2d` (Commit-Botschaft gegen `git log` geprüft), WR-01-Satz (2x `enterprise-issue-go-kriterium`) und WR-03-Satz (Drift `compare/v0.1.9...HEAD`) vorhanden | closed |
| T-14-09 | Tampering | Vokabular-Gate | mitigate | Docstring von `public_markdown_pages()` (tests/unit/test_exapp_env_setup.py:2022-2031) begründet die `.planning`-Ausnahme als SEC-03-Entscheidung; `git diff 31716bb..HEAD` der Testdatei nennt 31/0 und enthält 0 Treffer für `FORBIDDEN_VOCABULARY`, `PUBLIC_MARKDOWN`, `VOCABULARY_EXCEPTION`, `VERBATIM_ARCHIVE_TEXT`; `grep -c "FORBIDDEN_VOCABULARY = "` gibt 1 (eine Wortliste) | closed |
| T-14-10 | Elevation of Privilege | Gate-Reichweite | mitigate | `test_the_vocabulary_gate_stops_at_the_internal_planning_area` (Zeile 2132-2149) hält die Grenze mit beiden Assertions: keine Seite aus `public_markdown_pages()` unter `.planning`, kein Mitglied aus `archive_members()` mit Präfix `.planning/`; Lauf `-k internal_planning_area` 1 passed, Gesamtlauf 153 passed, Exit 0 | closed |
| T-14-11 | Information Disclosure | interne Planungsnotizen | accept | `.planning` ist per Owner-Entscheidung aus Phase 1 öffentlich (Repo-Sichtbarkeit option-a); der Verweis in docs/store-submission.md:13 ist als "internal note that may disappear" gekennzeichnet, der Pfad steht weiter dort. Eintrag R-14-02 im Accepted Risks Log | closed |
| T-14-SC | Tampering | Paketinstallation (Supply Chain) | mitigate | `git diff --stat 31716bb..HEAD -- pyproject.toml uv.lock requirements*.txt` ist leer; alle Prüfungen der Phase und dieses Audits liefen mit `uv run --no-sync`, also ohne Sync und ohne Auflösung | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-14-01 | T-14-05 | Die vier Store-Dateien sind bereits öffentlich; die Phase ändert nur Wortstellen und fügt keine neue Information hinzu. Restrisiko: keines über den Status quo hinaus | Plan 14-01 (Owner-Standard, Planungszeitpunkt) | 2026-08-28 |
| R-14-02 | T-14-11 | `.planning` ist seit Phase 1 per Owner-Entscheidung öffentlich (option-a). Der Verweis auf `.planning/phases/05-store-research.md` in der öffentlichen Doku bleibt bewusst stehen, ist aber als interne Notiz gekennzeichnet, die verschwinden darf; keine Aussage der Seite hängt an ihr (deckt auch Review-Befund IN-03 aus 14-REVIEW.md) | Plan 14-02 (Owner-Standard, Planungszeitpunkt) | 2026-08-28 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Keine. Weder 14-01-SUMMARY.md noch 14-02-SUMMARY.md enthält einen Abschnitt `## Threat Flags`
(per grep geprüft). Die im Review verbliebenen Info-Befunde IN-01 bis IN-04 aus 14-REVIEW.md
mappen auf bestehende Einträge oder sind keine neue Angriffsfläche:

- IN-01 (verschobene Zeilenzitate) und IN-04 (Em-Dashes im Archivbestand): Archivprinzip von
  T-14-08, kein neuer Angriffsvektor.
- IN-02 (neuer Gate-Test ohne Counter-Probe): betrifft die Robustheit der Mitigation von
  T-14-10, nicht ihre Existenz; der Test hat einen realen Fehlmodus über `archive_members()`
  und ist grün gelaufen. Als Härtungsvorschlag beim Review dokumentiert, kein offener Threat.
- IN-03 (interner Pfad in öffentlicher Doku): gedeckt durch R-14-02.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-28 | 12 | 12 | 0 | gsd-security-auditor (Claude) |

Prüfmethode: adversarial, jede Mitigation galt als abwesend, bis ein Grep- oder Git-Beleg am
richtigen Ort sie nachwies. Alle Diffs wurden gegen den Basis-Commit `31716bb` (Stand vor
Phase 14) gemessen, der Testlauf live ausgeführt (`uv run --no-sync pytest
tests/unit/test_exapp_env_setup.py`: 153 passed, Exit 0).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-28
