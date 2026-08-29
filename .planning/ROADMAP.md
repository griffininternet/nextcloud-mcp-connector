# Roadmap: MCP Connector für Nextcloud

## Milestones

- **v1.0 MVP im Store**: Phasen 1-5 (shipped 2026-08-20, Release 0.1.2 live im Nextcloud App Store)
- **v1.1 Verwaltungs-Clients und Härtungs-Reste**: Phase 6 (shipped 2026-08-20; Phase 7 deferred, extern getaktet)
- **v1.2 Kuratierte Breite**: Phasen 8-11 (shipped 2026-08-25, Release 0.1.8 live im Store; Talk, Tables und Mail dazu, ohne das Sicherheitsversprechen oder die Schlankheit aufzugeben)
- **v1.3 Pflege und 0.1.9**: Phasen 12-13 (shipped 2026-08-26, Release 0.1.9 live im Store; Konsistenz- und Härtungs-Schulden abgeräumt, CIMD live nachgemessen, Enterprise-Fake-Door)
- **v1.4 Pflege und 0.1.10**: Phasen 14-15 (shipped 2026-08-28, Release 0.1.10 live im Store; gekürzter Enterprise-Text und Kontaktwechsel zu admin@infranode.dev, Doku-Reste aus v1.3 abgeräumt)
- **v1.5 Vorlauf openDesk**: Phasen 16-19 (AKTIV seit 2026-08-28; Release 0.1.11, zeitboxierter openDesk-Spike vor dem ISV-Call am 14.09., Audit-Log als erster Enterprise-Baustein)

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

<details>
<summary>v1.4 Pflege und 0.1.10 (Phasen 14-15), SHIPPED 2026-08-28</summary>

- [x] Phase 14: Doku-Reste und Gate-Entscheid (2/2 Pläne), completed 2026-08-28
- [x] Phase 15: Release 0.1.10 (4/4 Pläne, davon 2 mit Owner-Gate), completed 2026-08-28

Volle Phasendetails: [milestones/v1.4-ROADMAP.md](milestones/v1.4-ROADMAP.md)
Audit: [milestones/v1.4-MILESTONE-AUDIT.md](milestones/v1.4-MILESTONE-AUDIT.md) (passed, 4/4 Requirements)

</details>

### v1.5 Vorlauf openDesk (Phasen 16-19), AKTIV

- [x] **Phase 16: Release 0.1.11** - Den wartenden Textrest ausliefern und den `[Unreleased]`-Block leerräumen, bevor das Audit-Log ihn wieder füllt (4/4 Pläne, completed 2026-08-28, Release live im Store)
- [ ] **Phase 17: openDesk-Spike** - Installierbarkeit und Nutzeridentität gegen OpenProject messen statt argumentieren, plus die Fragenliste für den 14.09.
- [ ] **Phase 18: Audit-Log Kern** - Jeder Werkzeugaufruf hinterlässt einen prüfbaren Metadaten-Eintrag, der keine Inhalte trägt und den OAuth-Speicher nicht gefährdet
- [ ] **Phase 19: Audit-Log Bedienung und Textnachzug** - Administrator schaltet ein und liest über `occ`, und jede bestehende Aussage über Speicherung und Enterprise-Stand sagt danach die Wahrheit

**Stränge:** Phase 16 und Phase 17 hängen an nichts und können ab Tag 1 laufen. Phase 18 hängt ebenfalls an nichts (der Spike-Ausgang berührt das Audit-Log nicht). Die einzige echte Serialisierung des Meilensteins ist Phase 19: sie braucht das feststehende Satzschema aus Phase 18 und den geleerten `[Unreleased]`-Block aus Phase 16.

**Rahmenbedingung für alle vier Phasen:** Keines der beiden Features fasst die Werkzeugoberfläche an. 15712 von 18000 Bytes über 21 Werkzeuge bleiben stehen, kein Gate-Grenzwert wird angehoben.

## Phase Details (v1.5)

### Phase 16: Release 0.1.11

**Goal**: Die im `[Unreleased]`-Block wartenden Textänderungen sind als Release 0.1.11 im Nextcloud App Store, und der Block ist danach leer
**Depends on**: Nichts (Phase 15 abgeschlossen; der Stand ist heute release-fertig)
**Requirements**: EXAPP-11
**Success Criteria** (was wahr sein muss):

  1. Wer die App im Nextcloud App Store aufruft, sieht die Fassung 0.1.11 mit dem gekürzten Trifecta-Absatz samt Teilen-Formulierung und mit admin@infranode.dev als Autorenkontakt im Manifest
  2. Die Zeichenkette 0.1.11 steht an allen sechs Versionsstellen (pyproject, `__init__`, info.xml version und image-tag, drei README-Statuszeilen, uv.lock), der Changelog trägt einen Block 0.1.11 mit seiner Linkdefinition, und der `[Unreleased]`-Block ist danach leer
  3. Der Branch liegt auf dem öffentlichen `main`, bevor ein Tag existiert; der Tag `v0.1.11` entsteht erst nach der wörtlichen Owner-Freigabe
  4. Die Signatur ist über das heruntergeladene Asset gerechnet und verifiziert, nicht über das lokal gebaute, und `docs/store-submission.md` trägt für jeden Runbook-Schritt eine datierte Proof-Zeile
  5. Alle Gates laufen auf dem Kandidaten grün, ohne dass ein Grenzwert angehoben wurde; die Werkzeugoberfläche bleibt bei 21 Werkzeugen

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 16-01-PLAN.md , Versions-Bump auf 0.1.11 an sechs Stellen, und aus dem [Unreleased]-Block wird der Changelog-Block 0.1.11 samt getauschter Linkdefinition

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 16-02-PLAN.md , sechs Gates lokal grün ohne Anhebung, Archiv-Probelauf mit Nutzlast-Zählung, Proof-Zeilen der Runbook-Schritte 1 bis 3

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 16-03-PLAN.md , Branch-Push vor dem Tag, blockierende Owner-Freigabe, Tag v0.1.11 und grüner Release-Workflow, Proof-Zeile der Schritte 4 und 5

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 16-04-PLAN.md , Signatur über das heruntergeladene Asset, Store-Einreichung mit 201, die fünf Nachweise aus Schritt 8 in einer Proof-Zeile

### Phase 17: openDesk-Spike

**Goal**: Die openDesk-Frage ist vor dem ISV-Call gemessen und schriftlich belegt, ohne dass eine Zeile Produktionscode entsteht
**Depends on**: Nichts (Strang S, parallel zu 16 und 18); intern gilt: OD-01 vor OD-02, weil Installierbarkeit über jeder API-Frage steht
**Requirements**: OD-01, OD-02, OD-03
**Success Criteria** (was wahr sein muss):

  1. Ein Leser des Spike-Berichts erfährt zuerst, ob und auf welchem Weg diese ExApp in einer openDesk-Umgebung installierbar ist: je eine Antwort zum abgeschalteten App Store, zur fehlenden AppAPI auf Kubernetes und zur auf Nextcloud 33.0.7 gepinnten Zielumgebung gegenüber unseren auf 34.0.3 erbrachten Ein-Klick-Nachweisen, jede mit Quelle oder ausdrücklich als offene ISV-Call-Frage markiert
  2. Weg 0 (über `integration_openproject`) und Weg 1 (eigener OAuth-Autorisierungscode je Nutzer) stehen im selben Bericht mit Messwerten nebeneinander, mindestens zu PKCE-Unterstützung, Token-Lebensdauer und Erneuerung ohne Browsersitzung, dazu die Antwort, ob die SSRF-Grenze aus v1.1 eine Nachbarkomponente unter internem Dienstnamen durchlässt
  3. Welcher Weg trägt, steht im Bericht als Folge dieser Messungen da und nicht als Argument; ein Weg, der nicht gemessen werden konnte, steht als "ungemessen" da und nicht als "verworfen"
  4. Eine Fragenliste für den 14.09. liegt vor und enthält das ZenDiS-Aufnahmeverfahren, den Installationsweg in openDesk, die AGPL-Konsequenz für die Enterprise-Positionierung und die Folge der in openDesk abgeschalteten Apps Talk und Kontakte für zwei unserer bestehenden Werkzeugfamilien
  5. Der ausgelieferte Produktionsbaum ist nach der Phase unverändert: kein neues Werkzeug, kein neuer Client im Paket, Werkzeugoberfläche und Budget-Gate stehen still

**Plans**: 9 plans
Plans:
**Wave 1**

- [x] 17-01-PLAN.md , OD-01 aus Quellen ohne Docker, Bericht angelegt mit Kopf, vorab festgelegten Entscheidungskriterien und Abschnitt 1

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 17-02-PLAN.md , Stufe A Teil 1: Spike-Topologie mit Nextcloud 33.0.7 gepinnt und auf Loopback, S0 gemessen, SSRF-Grenze gegen internen Dienstnamen gemessen (D-06)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 17-03-PLAN.md , Stufe A Teil 2: OpenProject 17.7.2, die vier Oberflächenschritte per Owner-Gate, Grundzustand für den Zwei-Konten-Negativbeweis

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 17-04-PLAN.md , Weg 1 vollständig gemessen: PKCE mit Gegenprobe ohne code_challenge, expires_in, Refresh ohne Browsersitzung, Zwei-Konten-Negativbeweis

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 17-05-PLAN.md , Weg 0 eingerichtet (Zwei-Wege-OAuth2 per Owner-Gate), S1, S2, Capability-Befund und Egress-Kontrollmessung

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 17-06-PLAN.md , Weg 0 gemessen: S3 Zwei-Konten-Negativbeweis, S4 Erneuerung nach künstlichem Ablauf mit Gegenprobe, S6 Byte-Kosten und API-Form

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 17-07-PLAN.md , Stufe B mit Keycloak 26.7.0 und user_oidc 8.11.0, S5a bis S5c mit Log-Zeile als Messwert (ungemessen ausdrücklich zulässig), Entwurf zu user_oidc#925 nur bei geglückter Repro

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 17-08-PLAN.md , OD-03: Fragenliste für den 14.09. im Bericht und im Dossier, zwei unversendete Entwürfe der Rückkanäle, Owner-Gate

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 17-09-PLAN.md , Bericht abgeschlossen (welcher Weg trägt, was ungemessen blieb, Ränder, Reproduktion), Geheimnisgriff, Produktionsbaum-Nachweis und Abräumen der Messumgebung

*Die Wellen sind seriell, weil alle Pläne dieselbe Berichtsdatei füllen und dieselbe eine Messumgebung benutzen; der Schnitt zwischen Welle 2 und 3 sowie vor Welle 7 folgt dem Stufenschnitt der Recherche (Stufe A vollständig protokolliert, bevor Keycloak dazukommt).*

### Phase 18: Audit-Log Kern

**Goal**: Jeder Werkzeugaufruf hinterlässt einen prüfbaren Eintrag, der weder Parameterwerte noch Ergebnisinhalte trägt und den OAuth-Speicher nicht schreibunfähig machen kann
**Depends on**: Nichts (Strang A, parallel zu 16 und 17; unabhängig vom Spike-Ausgang, trägt den Meilenstein auch allein)
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03
**Success Criteria** (was wahr sein muss):

  1. Nach einem Werkzeugaufruf steht ein Eintrag mit Nutzer, Werkzeugname, Zeitpunkt, aufrufendem Client und Ergebnisstatus in der Ablage; ein abgelehnter Aufruf steht mit seinem Grund darin, und kein Werkzeug der 21 kann an dieser Erfassung vorbei
  2. In keinem Eintrag steht ein Parameterwert oder ein Ergebnisinhalt; eine Erlaubnisliste je Werkzeug nennt die zulässigen Parameternamen, und ein Vertragstest nach dem Muster des Budget-Gates schlägt fehl, sobald ein Werkzeug diese Grenze überschreitet
  3. Ein Prüfkommando bestätigt die ungebrochene Hash-Kette über alle Einträge oder benennt die erste gebrochene Stelle; eine nachträglich veränderte Zeile wird von diesem Kommando gefunden
  4. Das Log liegt in einer eigenen Ablage neben dem OAuth-Speicher, hat eine Obergrenze und eine Aufbewahrungsfrist, die mindestens 180 Tage erreichen kann; bei vollem Volume bleiben Token-Rotation und neue Verbindungen funktionsfähig
  5. `occ mcp_connector:purge` und die Deinstallation lassen das Audit-Log stehen, während alles andere verschwindet; Verbindung trennen und Pausieren lassen die Einträge ebenfalls stehen, und gelöscht wird nur durch die abgelaufene Aufbewahrungsfrist oder die Löschung des Nutzers in Nextcloud (D-v1.5-01)

**Plans**: TBD

### Phase 19: Audit-Log Bedienung und Textnachzug

**Goal**: Ein Administrator schaltet das Log ein und liest es über `occ`, und jede bestehende Aussage über Speicherung, Purge und den Enterprise-Stand sagt danach die Wahrheit
**Depends on**: Phase 18 (Satzschema und Speicher müssen feststehen, bevor etwas gelesen und beschrieben wird) und Phase 16 (der `[Unreleased]`-Block muss geleert sein, sonst führe 0.1.11 Text über ein Modul mit, das es zum Auslieferungszeitpunkt nicht gibt)
**Requirements**: AUDIT-04, AUDIT-05, AUDIT-06
**Success Criteria** (was wahr sein muss):

  1. Ein Administrator liest und exportiert das Log über ein `occ`-Kommando; das Manifest deklariert dafür keine neue Route, und die von außen erreichbare Angriffsfläche der App ist unverändert
  2. Ab Werk ist das Log aus; ein Administrator schaltet es in den Admin-Einstellungen ein, und die Beschriftung sagt, was das Log leistet, was es nicht leistet, und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann (D-v1.5-04, D-v1.5-02)
  3. Die Admin-Einstellung bietet keine Stufe an, die Parameterwerte oder Ergebnisinhalte protokolliert; `keys` ist der einzige einschaltbare Inhaltsumfang, `full` existiert nirgends in der Oberfläche
  4. `docs/privacy.md` und `docs/uninstall.md` sagen in ihrem eigenen Text, dass das Audit-Log Purge und Deinstallation übersteht und die Aufbewahrungsfrist der einzige automatische Löscher ist; das v1.0-Erfolgskriterium "eine Deinstallation entfernt alle Daten" ist entsprechend umgeschrieben statt stillschweigend falsch
  5. Der Enterprise-Absatz nennt das Audit-Log in allen drei Sprachen nicht länger als geplant, ein Gate hält die Wörter revisionssicher, AI-Act-konform, DSGVO-konform und SIEM-zertifiziert draußen, und alle Textänderungen dieser Phase warten im `[Unreleased]`-Block: kein Tag, kein Store-Upload, die Auslieferung ist EXAPP-12 und ausdrücklich nicht Teil dieses Meilensteins (D-v1.5-03)

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
| 14. Doku-Reste und Gate-Entscheid | v1.4 | 2/2 | Complete | 2026-08-27 |
| 15. Release 0.1.10 | v1.4 | 4/4 | Complete | 2026-08-28 |
| 16. Release 0.1.11 | v1.5 | 4/4 | Complete | 2026-08-28 |
| 17. openDesk-Spike | v1.5 | 8/9 | In Progress|  |
| 18. Audit-Log Kern | v1.5 | 0/? | Not started | - |
| 19. Audit-Log Bedienung und Textnachzug | v1.5 | 0/? | Not started | - |

## Next

`/gsd:execute-phase 17`: Phase 17 (openDesk-Spike) ausführen, neun Pläne in neun seriellen Wellen, drei davon mit Owner-Gate. Phase 18 (Audit-Log Kern) kann parallel dazu geplant werden.

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp); v1.0 abgeschlossen: 2026-08-20; v1.1 abgeschlossen: 2026-08-20 (Phase 7 deferred); v1.2 abgeschlossen: 2026-08-25 (Release 0.1.8 live); v1.3 abgeschlossen: 2026-08-26 (Release 0.1.9 live, CIMD nachgemessen, Enterprise-Fake-Door); v1.4 abgeschlossen: 2026-08-28 (Release 0.1.10 live); v1.5 aufgesetzt: 2026-08-28 (Phasen 16-19: Release 0.1.11, openDesk-Spike, Audit-Log in zwei Phasen); Phase 17 geplant: 2026-08-28 (9 Pläne, 9 Wellen)*
