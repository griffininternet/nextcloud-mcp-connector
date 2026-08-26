# Phase 13: CIMD-Nachmessung und Release 0.1.9 - Context

**Gathered:** 2026-08-25
**Status:** Ready for planning
**Source:** Owner-Anweisung 25.08. ("berücksichtige in der Planung unser ISV-Vorhaben") + NEXT.md-Übergaben aus Phase 12

<domain>
## Phase Boundary

Phase 13 liefert zwei Dinge: (1) den nachgemessenen CIMD-Beweis gegen die laufende
Topologie (E2E, client_id = https-URL, Proof-Zeile mit Datum/Befehl/Ergebnis) und
(2) Release 0.1.9 im Nextcloud App Store nach Runbook (Version an allen fünf
Stellen, Changelog 0.1.9, Gates lokal grün, Branch-Push VOR Tag, Tag v0.1.9 NUR
nach ausdrücklicher Owner-Freigabe, Signatur über das heruntergeladene Asset,
Proof-Zeilen für Runbook-Schritte 4-8 in docs/store-submission.md).

ZUSÄTZLICH per Owner-Anweisung 25.08.: Das ISV-Vorhaben (Nextcloud ISV Partner
Program, Call 14.09. mit Fabrice Mous, UG-Gründung als Träger, kommerzielle
Schiene Connector Enterprise) fließt in diese Phase ein, soweit es das Release
betrifft. Konkret die Fake-Door-Validierung 1 aus
C:/Users/Student/scripts/docs/specs/ideation-isv-monetarisierung-2026-08-25/validation-plan.md.

</domain>

<decisions>
## Implementation Decisions

### Release-Disziplin (aus ROADMAP/Phase-12-Übergaben, LOCKED)
- D-01: Tag v0.1.9 entsteht NUR nach ausdrücklicher Owner-Freigabe; Branch/main
  ist gepusht, BEVOR irgendein Tag existiert (Runbook Schritt 4).
- D-02: Changelog 0.1.9 nennt `message_truncated` ausdrücklich als
  Formatänderung und das README-Provider-Beispiel als Doku-Korrektur
  (Übergaben aus Phase 12).
- D-03: Signiert wird das HERUNTERGELADENE Release-Asset, nie das lokal gebaute
  (Runbook Schritt 6); jeder Runbook-Schritt 4-8 bekommt eine Proof-Zeile mit
  Datum, Befehl und Ergebnis in docs/store-submission.md.
- D-04: Gates bleiben auf der v1.2-Messung (BUDGET_BYTES 18000,
  MAX_TOOL_BYTES 1400, 21 Tools); Vokabular-Gate in der neuen
  Phase-12-Reichweite läuft lokal VOR dem Push.

### ISV-Vorhaben: Enterprise-Fake-Door fährt mit Release 0.1.9 mit (Owner 25.08., LOCKED)
- D-05: Ein Abschnitt "Enterprise" kommt in die Connector-READMEs (EN/DE/FR
  synchron, echte Umlaute/Accents, keine Em-Dashes): Audit-Log,
  Gruppen-Policies und SSO sind als kommerzielles Add-on GEPLANT (nichts davon
  existiert; ehrlich als Plan formulieren), Interessens-Kontakt
  k.cherif@outlook.de. KEIN Preis nennen. Quelle: validation-plan.md,
  Methode Fake-Door, Konzept-Brief concept-brief-1-connector-enterprise.md.
- D-06: Derselbe Enterprise-Hinweis kommt in die Store-Beschreibung
  (info.xml-Description EN/DE/FR; Regeln: kein Backtick, keine Tabelle).
  Er wird erst mit dem Release-Upload 0.1.9 sichtbar (Store liest das
  Manifest nur beim Release-Upload), deshalb gehört er in DIESE Phase.
- D-07: Das GitHub-Issue "Enterprise features: what would your org need
  before allowing MCP access?" (Fake-Door Schritt 2) wird als ENTWURF
  vorbereitet (Titel + Body als Datei im Repo-Doku-Bereich oder Messdokument),
  aber NICHT automatisch veröffentlicht; Veröffentlichung nur nach
  Owner-Freigabe (analog Tag-Regel; Owner sendet Outreach selbst).
- D-08: Kein Enterprise-Feature wird in dieser Phase GEBAUT (kein Audit-Log,
  keine Policies, kein SSO). Baustart frühestens nach ISV-Klarheit und
  Findling v1.1 (Anfang 2027). Diese Phase liefert nur die Fake-Door-Texte.

### Claude's Discretion
- Genaue Formulierung des Enterprise-Abschnitts (Ton wie bestehende READMEs,
  AIquila-artig kurz in der Store-Beschreibung).
- Platzierung des Enterprise-Abschnitts in den READMEs (sinnvoll nahe
  Grenzen/Support-Themen).
- Aufbau des CIMD-Messdokuments und Wahl des Messwegs, solange die
  Success-Criteria-Formulierung erfüllt ist (Proof-Zeile im Doku-/Messdokument,
  nicht in einer Zusammenfassung).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Release-Runbook und Store
- `docs/store-submission.md` — Runbook mit Schritten und bisherigen Proof-Zeilen
- `.planning/phases/12-konsistenz-und-h-rtungs-nachzieher/12-VERIFICATION.md` — was Phase 12 wirklich geliefert hat (Changelog-Stoff für 0.1.9)

### ISV-Vorhaben (Owner-Anweisung 25.08.)
- `C:/Users/Student/scripts/docs/specs/ideation-isv-monetarisierung-2026-08-25/validation-plan.md` — Fake-Door-Methode, Go/No-Go-Kriterien
- `C:/Users/Student/scripts/docs/specs/ideation-isv-monetarisierung-2026-08-25/concept-brief-1-connector-enterprise.md` — Schnitt Connector Enterprise (Audit/Policies/SSO)

### CIMD-Nachmessung
- `docs/oauth-setup.md` — bisherige CIMD-/OAuth-Beweisführung (v1.1)

</canonical_refs>

<specifics>
## Specific Ideas

- Enterprise-Abschnitt bewusst ohne Preis; Signale zählen (Go: >=5 qualifizierte
  Org-Signale in 6 Wochen oder 1 Ankerkunde).
- READMEs sind in dieser Phase ohnehin offen (Versions-Statuszeile 0.1.9 in
  EN/DE/FR), der Enterprise-Abschnitt fährt im selben Edit mit.
- info.xml-Description-Änderung fasst die Version NICHT an; der Versions-Bump
  ist eine separate Release-Aufgabe derselben Phase.

</specifics>

<deferred>
## Deferred Ideas

- Enterprise-Feature-BAU (Audit-Log, Policies, SSO): nach ISV-Klarheit +
  Findling v1.1, frühestens Anfang 2027.
- Fake-Doors 2 (Findling Pro) und 3 (Approved-Write-Suite): andere Repos/
  Projekte, nicht Teil dieser Phase.
- ISV-Call-Vorbereitung 14.09. (Dossier liegt auf dem Desktop): Owner-seitig,
  kein Phase-13-Artefakt.

</deferred>

---

*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Context gathered: 2026-08-25 via Owner-Anweisung + Phase-12-Übergaben*
