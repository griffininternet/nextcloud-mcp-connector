# Roadmap: MCP Connector für Nextcloud

## Milestones

- **v1.0 MVP im Store**: Phasen 1-5 (shipped 2026-08-20, Release 0.1.2 live im Nextcloud App Store)
- **v1.1 Verwaltungs-Clients und Härtungs-Reste**: Phase 6 (shipped 2026-08-20; Phase 7 deferred, extern getaktet)
- **v1.2 Kuratierte Breite**: Phasen 8-11 (aktiv; Talk, Tables und Mail dazu, ohne das Sicherheitsversprechen oder die Schlankheit aufzugeben)

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

### v1.2 Kuratierte Breite (Phasen 8-11)

- [x] **Phase 8: Erreichbarkeits-Spike und Tables** - Erst messen, ob Mail unter AppAPI-Impersonation überhaupt erreichbar ist, dann die risikoärmste Familie komplett bauen und damit die mechanische Checkliste einmal etablieren (completed 2026-08-21)
- [ ] **Phase 9: Talk** - Konversationen und Verlauf nachweislich nebenwirkungsfrei lesen, Nachricht senden als risikoarmer Create, Ausgangskanal per Admin-Schalter abschaltbar
- [ ] **Phase 10: Mail strikt lesend und die Trifecta-Grenze** - Konten, Postfächer, Envelopes und Volltext lesen ohne jeden Schreibpfad, App-Erkennung für alle drei Familien, Exfiltrationskette benannt statt beschwiegen
- [ ] **Phase 11: Bündelung, Budget und Release 0.1.4** - Talk- und Mail-Anteil in prepare_context, Suchtreffer auflösbar, Budget-Gate neu verankert, Fassung im Store

## Phase Details

### Phase 8: Erreichbarkeits-Spike und Tables

**Goal**: Die einzige offene Unbekannte des Meilensteins ist gemessen (erreicht der Connector Mail unter reiner AppAPI-Impersonation, oder nicht), und die Tables-Familie ist vollständig nutzbar: Tabellen, Spalten und Zeilen lesen, Zeile anlegen. Damit ist die mechanische Checkliste einer neuen Familie (Client-Modul, Tool-Modul mit `level`-Enum, `reg_*`-Registrierung, Capability-Feld, `EXPECTED_TOOLS`, `CREATE_TOOLS`, READMEs, Budget-Messzeile) einmal an der Familie ohne Zusatzrisiko durchlaufen.
**Depends on**: Phase 6 (v1.1 abgeschlossen, Release 0.1.3 live im Store)
**Requirements**: MAIL-04, TABLES-01, TABLES-02
**Reihenfolge innerhalb der Phase**: Der Mail-Erreichbarkeits-Spike läuft zuerst und blockierend. Ein negatives Ergebnis ändert den Schnitt von Phase 10 und 11 (MAIL-01..03, CTX-02, SEC-01, Tool-Zahl in TOOL-15) und muss vor deren Planung auf dem Tisch liegen, nicht danach.
**Success Criteria** (was wahr sein muss):

  1. Ein Integrationstest gegen eine echte Instanz zeigt, ob ein Assistent unter AppAPI-Impersonation die Mail-Listen-Routen (accounts, mailboxes, messages) und die OCS-Volltext-Route erreicht; scheitert einer der vier Wege, steht der Statuscode und die Antwortform (JSON, HTML, Loginseite) im Ergebnis, nicht die Vermutung.
  2. Das SCOPE_IGNORE-Risiko der internen Mail-Listen-Routen steht dort, wo es jemand liest: im Code an der Stelle, die diese Routen aufruft, und in der Doku als benannter Ersetzbarkeits-Hinweis.
  3. Nutzer kann seine Tabellen, deren Spalten und die Zeilen einer Tabelle über einen Aufruf lesen; jede Antwort ist gekappt (Default 25, Max 200 Zeilen), nennt `rowsCount` und markiert eine Kappung beim Namen, und ein Aufruf ohne gesetztes Limit liest nie die ganze Tabelle.
  4. Nutzer kann eine Zeile mit Spaltentiteln statt Spalten-Ids anlegen; ein unbekannter, mehrdeutiger oder fehlender Pflichttitel wird mit der Liste der gültigen Titel abgelehnt, bevor irgendetwas geschrieben wird.
  5. Ein Nutzer ohne Schreibrecht auf der Tabelle bekommt vorab einen Fehlersatz samt nächstem Schritt statt eines 403 aus der Nextcloud, und es existiert kein Pfad zum Ändern oder Löschen einer Zeile oder eines Schemas (Gate hält, Gegenprobe vorhanden).

**Plans**: 5 Pläne in 4 Wellen

Plans:
**Wave 1**

- [x] 08-01-PLAN.md: Mail-Erreichbarkeits-Spike (MAIL-04, blockierend): vier Wege messen, Protokoll, Topologie
- [x] 08-02-PLAN.md: Tables-Client über zwei API-Generationen, erste OCS-Schreibnaht, App-Erkennung

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-03-PLAN.md: Tables-Werkzeuge: browse mit drei Ebenen, Zeile mit Spaltentiteln anlegen

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-04-PLAN.md: Registrierung, Gates, Budget-Verankerung, READMEs EN/DE/FR und Changelog

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 08-05-PLAN.md: Integrationsnachweis gegen eine echte Instanz und Zwei-Konten-Negativbeweis

**UI hint**: nein (kein eigenes Frontend, reine Server- und Tool-Schicht)

### Phase 9: Talk

**Goal**: Nutzer kann seine Konversationen und deren Verlauf lesen, ohne dass dieses Lesen irgendetwas an seinem Zustand verändert, und er kann eine Nachricht senden, ohne dass ein Modell dabei die Adressierung erfinden oder eine gesperrte Konversation treffen kann. Der Administrator behält den Ausgangskanal in der Hand. In dieser Phase sitzen die querschneidenden Änderungen (nicht-numerische Pfad-Ids, neue Kinds, erster `ocs_post`), die Mail danach nur noch benutzt.
**Depends on**: Phase 8
**Requirements**: TALK-01, TALK-02, TALK-03, TALK-04
**Success Criteria** (was wahr sein muss):

  1. Nutzer kann seine Konversationen listen (Token, Name, Typ, Ungelesen- und Erwähnungs-Zähler, letzte Aktivität), archivierte bleiben draußen, die Liste ist auf 50 gekappt.
  2. Nutzer kann den Verlauf einer Konversation lesen (Default 20, Max 50, Byte-Kappe pro Nachricht, Paginierung über die letzte bekannte Nachrichten-Id), mit aufgelösten Platzhaltern und Mentions und ohne Systemnachrichten.
  3. Nach einem Lesevorgang ist nachweislich nichts am Nutzerzustand verändert: kein gesetzter Lesemarker, keine quittierte Benachrichtigung, kein gesetzter Online-Status, kein Long-Polling; ein positiv behauptender Test hält jeden dieser vier Parameter fest, nicht ein Denylist-Gate.
  4. Nutzer kann eine Nachricht in eine Konversation senden, adressiert ausschließlich mit einem Token aus dem Lesewerkzeug; eine schreibgeschützte Konversation, ein fehlendes Chat-Recht, `@all`/`@here` und ein zu langer Text werden vorab mit einem Satz samt nächstem Schritt abgelehnt, und es existiert kein Pfad zum Bearbeiten, Löschen oder stillen Senden.
  5. Administrator kann das Senden instanzweit abschalten; mit abgeschaltetem Schalter antwortet das Werkzeug mit einem Fehlersatz samt nächstem Schritt, gemessen über die ganze Kette: Settings-Form, Overlay-Lesepfad, Wirkung am Werkzeug.

**Plans**: 5 Pläne in 4 Wellen

Plans:
**Wave 1**

- [x] 09-01-PLAN.md: Talk-Client (v4-Räume, v1-Chat), 201 im OCS-Parser, 304 als leere Antwort, App-Erkennung spreed
- [ ] 09-02-PLAN.md: Sechster Admin-Wert: Formular, Overlay-Lesepfad, Manifest-Variable und der Weg in den Tool-Lesepfad

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 09-03-PLAN.md: Talk-Werkzeuge: browse mit zwei Ebenen, senden mit Vorprüfungen am Objekt und Schalter als erster Zeile

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 09-04-PLAN.md: Registrierung, Destruktiv-Gate für die verblosen Schreibwege, Budget, READMEs EN/DE/FR, Store-Beschreibung und Changelog

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 09-05-PLAN.md: Live-Messung der Nebenwirkungsfreiheit, Senden gegen eine echte Instanz und Zwei-Konten-Negativbeweis

**UI hint**: nein (der Admin-Schalter ist ein Declarative-Settings-Feld im Muster der bestehenden fünf Werte; Nextcloud rendert es, es entsteht kein eigenes Frontend)

### Phase 10: Mail strikt lesend und die Trifecta-Grenze

**Goal**: Nutzer kann seine Mail lesen, und zwar nur lesen: Konten, Postfächer, Envelopes, Volltext, Filter. Gleichzeitig verschwinden alle drei neuen Familien sauber, wenn ihre App auf der Instanz fehlt, und die Kette, die durch Mail-Lesen plus Talk-Senden erst entsteht, ist benannt statt beschwiegen.
**Depends on**: Phase 9 (Naht-Erweiterungen und `talk_send`-Schalter stehen), Ergebnis des Spikes aus Phase 8
**Requirements**: MAIL-01, MAIL-02, MAIL-03, SRV-06, SEC-01
**Success Criteria** (was wahr sein muss):

  1. Nutzer kann seine Mail-Konten, Postfächer (mit `specialRole` und Ungelesen-Zähler) und Nachrichten-Envelopes lesen (Vorschautext statt Body, Default 20, Max 50).
  2. Nutzer kann eine einzelne Mail im Volltext über das bestehende `fetch` mit `mail:<databaseId>` lesen: HTML kommt als Text an, die Byte-Kappe ist markiert, und Nextclouds Vertrauens-Signale (Absender vertraut, Phishing-Hinweise, DKIM) kommen als Datenfelder mit, statt gefiltert zu werden.
  3. Nutzer kann die Nachrichtenliste filtern (`is:unread`, `from:`, `subject:`, `start:`, `tags:`), und die Grammatik steht so dokumentiert, wie sie getestet ist.
  4. Es existiert kein Weg, über diese App eine Mail zu senden, als Entwurf anzulegen, zu verschieben, zu markieren oder zu löschen: das erweiterte Gate hält das fest, mit Gegenprobe, obwohl die Mail-App selbst eine Sende-Route anbietet.
  5. Ein Werkzeug gegen eine nicht installierte App antwortet in allen drei Familien mit einem Fehlersatz samt konkretem nächstem Schritt, nie mit Stacktrace oder Loginseite; für Talk und Tables über den bestehenden Capabilities-Weg, für Mail über den zweiten Erkennungskanal, gecacht wie bisher.
  6. Wer die Doku oder die Store-Beschreibung (EN/DE/FR) liest, findet die Exfiltrationskette benannt (fremder Mail-Inhalt als Daten, Talk-Senden als Ausgangskanal), den Admin-Schalter als Gegenmaßnahme und den Satz, dass Mail strikt lesend ist.

**Plans**: TBD
**UI hint**: nein (kein eigenes Frontend; Doku- und Store-Texte sind Textarbeit)

### Phase 11: Bündelung, Budget und Release 0.1.4

**Goal**: Die neuen Familien kommen dort an, wo ein Assistent sie im Alltag trifft: im Ein-Aufruf-Bündel `prepare_context` und als auflösbarer Suchtreffer. Das Budget-Gate wird auf die neue Messung verankert statt einmalig angehoben, und die Fassung, die all das trägt, liegt im Store.
**Depends on**: Phase 10 (beide neuen Kinds existieren und sind auflösbar)
**Requirements**: CTX-01, CTX-02, TOOL-15, TOOL-16, EXAPP-07
**Success Criteria** (was wahr sein muss):

  1. `prepare_context` liefert in einem Aufruf zusätzlich einen Talk-Digest (maximal 3 Konversationen mit Erwähnung oder Ungelesenem, Vorschau hart auf ~200 Zeichen gekappt) und Mail-Ungelesen-Zähler pro Konto und Inbox (nur Zahlen, keine Betreffs), jeweils mit eigenem Zeit-Budget und eigenem `degraded`-Eintrag.
  2. Das gemessene Timeout- und Degradations-Verhalten der bestehenden Quellen ist unverändert, und die Request-Kosten der Mail-Zähler sind gemessen und aufgeschrieben statt geschätzt.
  3. Ein Talk- oder Tables-Treffer aus der Suche ist auflösbar: `fetch` liefert Inhalt statt `kind=url`; Mail-Treffer bleiben ehrlich `kind=url` mit benanntem Grund.
  4. `tools/list` bleibt unter einem neu gemessenen und aufgeschriebenen Budget (Messung plus 15 Prozent, aufgerundet), alle fünf neuen Werkzeuge sind schema-diätet, die Annotationen sagen die Wahrheit (drei lesend, zwei anlegend), und Werkzeugzahl 21 steht identisch in Registry, README-Tabelle in drei Sprachen und Contract-Tests.
  5. Release 0.1.4 ist im Store: Version an allen vier Stellen, Changelog-Block, Store-Texte und READMEs EN/DE/FR nachgezogen, alle Gates grün, Runbook-Schritte mit Proof-Zeilen, Tag erst nach Owner-Freigabe.

**Plans**: TBD
**UI hint**: nein (kein eigenes Frontend)

## Requirement Coverage v1.2

| Requirement | Phase |
|-------------|-------|
| MAIL-04 | 8 |
| TABLES-01 | 8 |
| TABLES-02 | 8 |
| TALK-01 | 9 |
| TALK-02 | 9 |
| TALK-03 | 9 |
| TALK-04 | 9 |
| MAIL-01 | 10 |
| MAIL-02 | 10 |
| MAIL-03 | 10 |
| SRV-06 | 10 |
| SEC-01 | 10 |
| CTX-01 | 11 |
| CTX-02 | 11 |
| TOOL-15 | 11 |
| TOOL-16 | 11 |
| EXAPP-07 | 11 |

17 von 17 v1.2-Requirements abgedeckt, jedes genau einmal, keine Waisen.

## Phasenschnitt: Begründung

- **Reihenfolge folgt Risiko, nicht Attraktivität.** Die lethal-trifecta-Frage ist per Owner-Entscheid vom 2026-08-21 entschieden (`talk_send` kommt, hinter einem neuen Admin-Schalter, TALK-04) und wird nicht wieder aufgemacht. Die einzige verbleibende Unbekannte ist die Mail-Erreichbarkeit unter AppAPI-Impersonation, deshalb steht sie als blockierender erster Schritt in Phase 8.
- **Kein eigener Spike-Phasen-Kopf.** Bei Granularität coarse wäre eine Phase für eine einzige Messung Ballast; der Spike ist der erste, blockierende Plan von Phase 8, und Tables hängt nicht an ihm. Die Erkenntnis fällt damit genauso früh, ohne eine Phase, die einen Satz liefert.
- **Tables vor Talk**, obwohl Talk die attraktivere Familie ist: numerische Ids, beide Parser vorhanden, kein Eingriff in `ids.py`, `provider_map`, `fetch` oder `context.py`. Die Checkliste einmal risikolos zu lernen macht die beiden schwierigen Phasen kürzer.
- **SRV-06 liegt in Phase 10**, nicht in Phase 8: die Aussage lautet "alle drei Familien degradieren sauber", und nachweisbar ist sie erst, wenn alle drei Familien Werkzeuge haben. Mail bringt dabei den zweiten Erkennungskanal, weil Mail keinen Capabilities-Eintrag veröffentlicht.
- **SEC-01 liegt in Phase 10**, nicht am Ende: die Phase, die die Kette erst schließt (Mail-Lesen neben Talk-Senden), liefert auch ihre Benennung und ihren Verweis auf den Schalter. Eine Sicherheitsaussage, die eine Phase später nachgezogen wird, ist in der Zwischenzeit unwahr.
- **`prepare_context` und `provider_map` bewusst als letzte Phase**, nicht als Anhängsel jeder Familienphase: die Bucket-Entscheidung (welche Kinds bekommen einen Auszug) muss beide neuen Kinds gleichzeitig sehen, um konsistent zu sein, und das Budget-Gate wird sinnvoll erst verankert, wenn alle fünf Werkzeuge stehen.

## Research-Flags für die Phasenplanung

- **Phase 8**: Zellwert-Formate je `column_types` beim Zeile-Anlegen sind nicht vollständig dokumentiert (wahrscheinlichste Quelle für einen 400); kurze Recherche innerhalb der Phase einplanen. Mail-Erreichbarkeit ist MEDIUM-Konfidenz, nur aus Quellcode gelesen, nie in dieser Topologie gemessen.
- **Phase 9**: HIGH-Konfidenz aus offizieller Doku plus Quellcode, kein Extra-Research erwartet.
- **Phase 10**: Mail-Mindestversion für die OCS-Routen ist nicht sauber datierbar; Empfehlung ist, nicht auf eine Version zu gaten, sondern bei 404 oder HTML degradiert zu antworten. Die Antwortform des Navigations-Erkennungswegs ist nie gegen eine laufende Instanz geprüft; Gegenprobe über die Unified-Search-Provider-Liste ist der billige Ausweg.
- **Phase 11**: Standardmuster, kein Extra-Research erwartet.

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
| 8. Erreichbarkeits-Spike und Tables | v1.2 | 5/5 | Complete    | 2026-08-21 |
| 9. Talk | v1.2 | 1/5 | In Progress | - |
| 10. Mail strikt lesend und die Trifecta-Grenze | v1.2 | 0/? | Not started | - |
| 11. Bündelung, Budget und Release 0.1.4 | v1.2 | 0/? | Not started | - |

## Next

`/gsd:execute-phase 8`

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp); v1.0 abgeschlossen: 2026-08-20; v1.1 abgeschlossen: 2026-08-20 (Phase 7 deferred); v1.2 Phasen 8-11 ergänzt: 2026-08-21*
</content>
</invoke>
