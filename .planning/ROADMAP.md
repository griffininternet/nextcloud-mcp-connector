# Roadmap: MCP Connector für Nextcloud

## Milestones

- **v1.0 MVP im Store**: Phasen 1-5 (shipped 2026-08-20, Release 0.1.2 live im Nextcloud App Store)
- **v1.1 Verwaltungs-Clients und Härtungs-Reste**: Phase 6 (shipped 2026-08-20; Phase 7 deferred, extern getaktet)
- **v1.2 Kuratierte Breite**: Phasen 8-11 (shipped 2026-08-25, Release 0.1.8 live im Store; Talk, Tables und Mail dazu, ohne das Sicherheitsversprechen oder die Schlankheit aufzugeben)
- **v1.3 Pflege und 0.1.9**: Phasen 12-13 (shipped 2026-08-26, Release 0.1.9 live im Store; Konsistenz- und Härtungs-Schulden abgeräumt, CIMD live nachgemessen, Enterprise-Fake-Door)
- **v1.4 Pflege und 0.1.10**: Phasen 14-15 (AKTIV seit 2026-08-28; gekürzter Enterprise-Text und Kontaktwechsel zu admin@infranode.dev als Release 0.1.10, Doku-Reste aus v1.3 abgeräumt)

## Phases

<details>
<summary>v1.0 MVP im Store (Phasen 1-5), SHIPPED 2026-08-20</summary>

- [x] Phase 1: Server-Kern (14/14 Pläne), completed 2026-08-14
- [x] Phase 2: ExApp-Shell (7/7 Pläne), completed 2026-08-15
- [x] Phase 3: OAuth 2.1 (9/9 Pläne), completed 2026-08-16
- [x] Phase 4: Per-User-Verwaltung und prepare_context (4/4 Pläne), completed 2026-08-17
- [x] Phase 5: Hardening und Store-Einreichung (16/16 Pläne inkl. Gap-Closure), completed 2026-08-20

Volle Phasendetails: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) (passed, 27/27 Requirements)

</details>

<details>
<summary>v1.1 Verwaltungs-Clients und Härtungs-Reste (Phase 6), SHIPPED 2026-08-20</summary>

- [x] Phase 6: Härtung, Eigennachweise und Conference-Reife (11/11 Pläne inkl. Gap-Closure), completed 2026-08-20
- [ ] Phase 7: Verwaltungs-Clients live verprobt, DEFERRED per Owner-Entscheid 2026-08-20 (extern getaktet: it@M-Antwort, Owner-Kontakte; CLIENT-01..03 als Future Requirements vorgemerkt, Protokoll in docs/client-setup.md bleibt einlösbar)

Volle Phasendetails: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
Audit: [milestones/v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md) (passed, 7/7 Requirements)

</details>

<details>
<summary>v1.2 Kuratierte Breite (Phasen 8-11), SHIPPED 2026-08-25</summary>

- [x] Phase 8: Erreichbarkeits-Spike und Tables (5/5 Pläne), completed 2026-08-21
- [x] Phase 9: Talk (5/5 Pläne), completed 2026-08-21
- [x] Phase 10: Mail strikt lesend und die Trifecta-Grenze (8/8 Pläne), completed 2026-08-24
- [x] Phase 11: Bündelung, Budget und Release 0.1.8 (10/10 Pläne; der Phasentitel "0.1.6" war überholt), completed 2026-08-25

Volle Phasendetails: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
Audit: [milestones/v1.2-MILESTONE-AUDIT.md](milestones/v1.2-MILESTONE-AUDIT.md) (passed, 17/17 Requirements)

</details>

<details>
<summary>v1.3 Pflege und 0.1.9 (Phasen 12-13), SHIPPED 2026-08-26</summary>

- [x] Phase 12: Konsistenz und Härtungs-Nachzieher (4/4 Pläne), completed 2026-08-25
- [x] Phase 13: CIMD-Nachmessung und Release 0.1.9 (6/6 Pläne, davon 2 mit Owner-Gate), completed 2026-08-25

Volle Phasendetails: [milestones/v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md)
Audit: [milestones/v1.3-MILESTONE-AUDIT.md](milestones/v1.3-MILESTONE-AUDIT.md) (passed, 6/6 Requirements)

</details>

### v1.4 Pflege und 0.1.10 (Phasen 14-15), AKTIV

- [x] **Phase 14: Doku-Reste und Gate-Entscheid** - Info-Findings aus 13-REVIEW und W-2 schließen, Reichweite des Vokabular-Gates gegenüber .planning entscheiden (completed 2026-08-27)
- [ ] **Phase 15: Release 0.1.10** - Gekürzten Enterprise-Text und Kontaktwechsel als Store-Release mit Standard-Runbook ausliefern

## Phase Details (v1.4)

### Phase 14: Doku-Reste und Gate-Entscheid
**Goal**: Die dokumentarischen Reste aus v1.3 sind abgeräumt und die Reichweite des Vokabular-Gates gegenüber .planning ist entschieden statt offen
**Depends on**: Nichts (Phase 13 abgeschlossen; erste Phase von v1.4)
**Requirements**: DOC-01, DOC-02, SEC-03
**Success Criteria** (was wahr sein muss):
  1. Der französische Enterprise-/README-Wortlaut ist echtes Französisch: kein "confidemment" und kein englisches "for" in einer FR-Überschrift, geprüft gegen den Stand nach der Kürzung vom 27.08. (Reste können auch anderswo in README.fr.md liegen)
  2. CHANGELOG.md trägt keine hängende [Unreleased]-Linkdefinition mehr (entfernt oder wieder referenziert) und der veraltete Ampersand-Kommentar in appinfo/info.xml ist korrigiert oder entfernt
  3. Die Proof-Zeilen in docs/store-submission.md sind chronologisch sortiert und die 18:21Z-Zeile verweist auf den getaggten Commit zurück, ohne dass eine bestehende Proof-Aussage verfälscht wurde
  4. Die abgelegte 13-VERIFICATION unter .planning/milestones/v1.3-phases/ trägt eine datierte Nachtrags-Notiz, die den Entfernungs-Commit f9b3d2d zur ehemaligen Datei docs/contrib/enterprise-signals-issue.md nennt; der ursprüngliche Verifikationsbefund bleibt unverändert (er war zum Prüfzeitpunkt korrekt)
  5. Die Gate-Reichweite ist einheitlich entschieden: entweder prüft das Vokabular-Gate zusätzlich .planning/**/*.md (Treffer dort bereinigt oder als begründete Ausnahme gelistet) oder .planning steht als dokumentierte Ausnahme im Gate-Docstring; der gewählte Weg steht als Kommentar am Gate und die Entscheidung im Plan-/Summary-Text
**Plans**: 2 plans
Plans:
- [x] 14-01-PLAN.md , Sprachreste IN-05, hängende Linkdefinition IN-06 und veralteter Ampersand-Kommentar IN-03 (DOC-01a bis DOC-01c)
- [x] 14-02-PLAN.md , Proof-Zeilen chronologisch samt Rückverweis IN-01/IN-02/IN-07 (DOC-01d), datierter Nachtrag in der abgelegten 13-VERIFICATION (DOC-02) und entschiedene Gate-Reichweite (SEC-03)

### Phase 15: Release 0.1.10
**Goal**: Der gekürzte Enterprise-Text mit dem Kontaktwechsel zu admin@infranode.dev ist als Release 0.1.10 im Store, und die Doku-Fixes aus Phase 14 fahren im Asset mit
**Depends on**: Phase 14 (die Doku-Fixes müssen vor dem Tag im Branch liegen, damit sie ins Store-Asset fahren)
**Requirements**: EXAPP-10
**Success Criteria** (was wahr sein muss):
  1. Die Zeichenkette 0.1.10 steht an allen sechs Versionsstellen (pyproject, __init__, info.xml version + image-tag, drei README-Statuszeilen, uv.lock)
  2. Der Changelog-Block 0.1.10 nennt den gekürzten Enterprise-Abschnitt und den Kontaktwechsel zu admin@infranode.dev als nutzersichtbare Änderung; damit fährt auch die WR-02-Korrektur aus dem Repo-Changelog mit ins Asset und der Changelog-Drift W-1 ist erledigt
  3. Alle Gates laufen lokal grün auf dem Release-Kandidaten, ohne Anhebung (18000/1400 bei 21 Tools)
  4. Der Branch ist auf GitHub, bevor ein Tag existiert; der Tag v0.1.10 entsteht NUR nach ausdrücklicher Owner-Freigabe; die Signatur läuft über das heruntergeladene Asset, nicht über das lokal gebaute
  5. Release 0.1.10 ist im Store gelistet und die Runbook-Schritte tragen datierte Proof-Zeilen in docs/store-submission.md
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Server-Kern | v1.0 | 14/14 | Complete | 2026-08-14 |
| 2. ExApp-Shell | v1.0 | 7/7 | Complete | 2026-08-15 |
| 3. OAuth 2.1 | v1.0 | 9/9 | Complete | 2026-08-16 |
| 4. Per-User-Verwaltung und prepare_context | v1.0 | 4/4 | Complete | 2026-08-17 |
| 5. Hardening und Store-Einreichung | v1.0 | 16/16 | Complete | 2026-08-20 |
| 6. Härtung, Eigennachweise und Conference-Reife | v1.1 | 11/11 | Complete | 2026-08-20 |
| 7. Verwaltungs-Clients live verprobt | v1.1 | 0/0 | Deferred (extern getaktet) | - |
| 8. Erreichbarkeits-Spike und Tables | v1.2 | 5/5 | Complete | 2026-08-21 |
| 9. Talk | v1.2 | 5/5 | Complete | 2026-08-21 |
| 10. Mail strikt lesend und die Trifecta-Grenze | v1.2 | 8/8 | Complete | 2026-08-24 |
| 11. Bündelung, Budget und Release 0.1.8 | v1.2 | 10/10 | Complete | 2026-08-25 |
| 12. Konsistenz und Härtungs-Nachzieher | v1.3 | 4/4 | Complete | 2026-08-25 |
| 13. CIMD-Nachmessung und Release 0.1.9 | v1.3 | 6/6 | Complete | 2026-08-25 |
| 14. Doku-Reste und Gate-Entscheid | v1.4 | 2/2 | Complete    | 2026-08-27 |
| 15. Release 0.1.10 | v1.4 | 0/TBD | Not started | - |

## Next

`/gsd:plan-phase 14`: Phase 14 (Doku-Reste und Gate-Entscheid) planen

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp); v1.0 abgeschlossen: 2026-08-20; v1.1 abgeschlossen: 2026-08-20 (Phase 7 deferred); v1.2 abgeschlossen: 2026-08-25 (Release 0.1.8 live); v1.3 abgeschlossen: 2026-08-26 (Release 0.1.9 live, CIMD nachgemessen, Enterprise-Fake-Door); v1.4 aufgesetzt: 2026-08-28 (Phasen 14-15: Doku-Reste, Gate-Entscheid, Release 0.1.10)*
