# Roadmap: MCP Connector für Nextcloud

## Overview

Der Weg führt vom sofort nutzbaren Kern zur Store-Distribution: Zuerst entsteht der komplette Tool-Kern mit stdio und Streamable HTTP (bereits ein nutzbares Produkt für Entwickler, App-ID wird hier eingefroren, Contribution-Fix als Flanke). Danach wird der Server zur ExApp mit sauberem Berechtigungs-Durchgriff, inklusive des Discovery-Spikes durch den AppAPI-Proxy als Go/No-Go für die OAuth-Topologie. Phase 3 liefert den Kern-Differenzierer OAuth 2.1 mit E2E-Beweis gegen Claude.ai und ChatGPT. Phase 4 ergänzt Per-User-Verwaltung und prepare_context. Phase 5 härtet und reicht im Store ein, vor der Nextcloud Conference September 2026 (der CSR-Prozess startet entkoppelt schon direkt nach dem App-ID-Freeze aus Phase 1).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Server-Kern** - Alle Kern-Tools, stdio und Streamable HTTP mit App-Passwort; App-ID-Freeze und context_agent-Fix (completed 2026-08-14)
- [x] **Phase 2: ExApp-Shell** - Installation über AppAPI, Berechtigungs-Durchgriff, Discovery- und DAV-Spikes
 (completed 2026-08-15)
- [x] **Phase 3: OAuth 2.1** - Spec-konformes OAuth mit E2E-Beweis gegen Claude.ai und ChatGPT, Login Flow v2 als Fallback (completed 2026-08-16)
- [x] **Phase 4: Per-User-Verwaltung und prepare_context** - Settings-UI mit Token-Kontrolle plus Bündel-Tool (completed 2026-08-17)
- [ ] **Phase 5: Hardening und Store-Einreichung** - Sicherheits-Tests, Signatur, Listing, Client-Doku vor der Conference

## Phase Details

### Phase 1: Server-Kern

**Goal**: Entwickler können den MCP-Server lokal (stdio) und remote (Streamable HTTP) mit App-Passwort gegen ihre Nextcloud nutzen, mit dem vollen kuratierten Tool-Set
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: SRV-01, SRV-02, SRV-03, SRV-04, SRV-05, TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06, TOOL-07, TOOL-09, AUTH-01, EXAPP-03, CONTRIB-01
**Success Criteria** (what must be TRUE):

  1. Entwickler startet den Server per stdio mit App-Passwort gegen eine lokale Docker-Nextcloud und kann Dateien suchen/listen/lesen/hochladen, Termine abfragen und anlegen, Notizen und Deck-Karten lesen und anlegen, Kontakte suchen und berechtigungstreu cloudweit suchen (inkl. search/fetch im ChatGPT-Schema)
  2. Ein MCP-Client verbindet per Streamable HTTP (Client-Matrix: SDK>=1.28 und 2.x aus demselben Endpoint) und eine laufende Konversation überlebt einen Server-Restart (Stateless-Beweis, kein Session-State in Tools)
  3. tools/list zeigt korrekte Annotationen, token-schlanke Schemas (CI-Token-Budget-Check besteht) und ein dokumentiertes, sichtbares Permission-Level pro Tool; kein Tool kann löschen, überschreiben oder Freigaben ändern
  4. Ein Tool-Aufruf gegen eine nicht installierte Nextcloud-App liefert einen klaren, handlungsfähigen Fehlertext statt eines Crashes
  5. Die App-ID (ohne "nextcloud" im Namen) ist in Woche 1 eingefroren und dokumentiert, und der Fix-PR an nextcloud/context_agent#227 ist eingereicht

**Plans**: 14 plans in 6 waves

Plans:
**Wave 1**

- [x] 01-01-PLAN.md - Scaffold, Toolchain, CI und roter Contract-Test (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md - Walking Skeleton: files_read per stdio (Wave 2)
- [x] 01-12-PLAN.md - App-ID-Freeze, README mit Permission-Tabelle, GitHub-Repo (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md - Test-Nextcloud per compose plus files_upload create-only (Wave 3)
- [x] 01-04-PLAN.md - Streamable HTTP, Basic-Passthrough, Client-Matrix und Restart-Beweis (Wave 3)
- [x] 01-06-PLAN.md - OCS-Schicht, Graceful Degradation und Notes-Tools (Wave 3)
- [x] 01-07-PLAN.md - Kalender-Tools mit serverseitiger Expansion (Wave 3)
- [x] 01-08-PLAN.md - Kontakte-Suche ueber CardDAV (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-05-PLAN.md - files_search und files_list mit zustandsloser Pagination (Wave 4)
- [x] 01-09-PLAN.md - Deck-Tools: deck_browse und deck_create_card (Wave 4)
- [x] 01-10-PLAN.md - unified_search mit parallelem Provider-Fan-out (Wave 4)
- [x] 01-13-PLAN.md - Contribution-PR an nextcloud/context_agent#227 (Wave 4) *(PR eingereicht: nextcloud/context_agent PR 230, 2026-08-15)*

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-11-PLAN.md - ChatGPT-Profil: search und fetch (Wave 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 01-14-PLAN.md - Phasenabschluss: Schreibgrenzen-Beweis, Budget-Gate, Doku, Abnahme (Wave 6)

### Phase 2: ExApp-Shell

**Goal**: Admins können die App als ExApp über AppAPI installieren, jede Anfrage läuft unter der Identität des angemeldeten Nutzers, und die OAuth-Topologie ist per Spike entschieden
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: EXAPP-01, AUTH-05, AUTH-06
**Success Criteria** (what must be TRUE):

  1. Admin installiert die App als ExApp über AppAPI (Heartbeat/Init/enabled_handler funktionieren, Test Deploy grün auf docker-compose und Nextcloud AIO)
  2. Ein eingeschränkter Testnutzer sieht über MCP exakt das, was er auch in der Weboberfläche sieht, nicht mehr (Impersonation bzw. Nutzer-Credentials über eine einzige Client-Factory, Permission-Parity stichprobenhaft belegt)
  3. Discovery-Endpunkte (well-known/PRM, WWW-Authenticate) sind unauthentifiziert von außen erreichbar, auch über den AppAPI-Proxy-Pfad; das Spike-Ergebnis inkl. Fallback-Route ist dokumentiert, bevor Phase 3 startet
  4. Der DAV-über-AppAPI-Spike ist entschieden: Die Provider-Aufteilung (Impersonation vs. App-Passwort je API-Familie) ist getestet und dokumentiert

**Plans**: 7 plans in 5 waves

Plans:
**Wave 1**

- [x] 02-01-PLAN.md - AppAPI-Handshake, Lifecycle-Endpunkte und ExApp-Entrypoint (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md - Vierter Credential-Modus bis in die 20 Client-Aufrufstellen (Wave 2)
- [x] 02-03-PLAN.md - Container-Image, Startskript und ExApp-Manifest mit zwei engen Routen (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-04-PLAN.md - Testtopologie mit Reverse-Proxy und HaRP plus Installation über AppAPI (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-05-PLAN.md - Discovery-Spike AUTH-06 mit Messmatrix und Phase-3-Empfehlung (Wave 4)
- [x] 02-06-PLAN.md - DAV-Spike D-30: Impersonations-Matrix je API-Familie (Wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02-07-PLAN.md - Permission-Parity über die volle Kette, Doku, AIO-Entscheidung, Abnahme (Wave 5)

### Phase 3: OAuth 2.1

**Goal**: MCP-Clients verbinden plug-and-play per spec-konformem OAuth 2.1, mit Login Flow v2 als Fallback für Clients ohne OAuth
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: AUTH-02, AUTH-03, AUTH-04, AUTH-07
**Success Criteria** (what must be TRUE):

  1. Der Claude.ai-Connector verbindet plug-and-play gegen eine öffentlich erreichbare Staging-Instanz: URL eintragen, Browser-Login mit Consent, Tools nutzbar, ohne manuelle Client-Konfiguration
  2. Der ChatGPT-Connector verbindet ebenso Ende-zu-Ende gegen dieselbe Staging-Instanz (PRM, Dynamic Client Registration, PKCE S256, Audience-Binding komplett)
  3. Nutzer ohne OAuth-fähigen Client onboarden sich per Login Flow v2 im Browser; der Client sieht nie das echte Passwort
  4. Token-Widerruf wirkt sofort: Ein widerrufener Client erhält 401 mit korrektem WWW-Authenticate-Header und kann sich sauber neu verbinden
  5. Wiederholte fehlgeschlagene Auth-Versuche drosseln die Nextcloud-Instanz nicht (keine Auth-Retries, Validierungs-Cache, handlungsfähige 401/429-Meldungen)

**Plans**: 9 plans in 8 waves

Plans:
**Wave 1**

- [x] 03-01-PLAN.md - Discovery-Produktivpfad, Routen-Haertung D-38 und PUBLIC-Umstellung mit Bearer-Grenze (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md - Verschluesselter Token-Store, der Neustarts ueberlebt (Wave 2)
- [x] 03-03-PLAN.md - UI-Bausteine nach 03-UI-SPEC: Shell, Komponenten, Texte, sieben Fehlerseiten (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-04-PLAN.md - Login Flow v2 und Onboarding ohne OAuth (AUTH-02) (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-05-PLAN.md - Client-Registry, DCR-Policy, AS-Routen und Consent-Bruecke (Wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-06-PLAN.md - Zustimmung, Code-Tausch, Token-Verifier und fuenfter Credential-Modus (Wave 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 03-07-PLAN.md - Rotation, Widerruf, Drosselung und die D-40-Missbrauchsmatrix (Wave 6)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 03-08-PLAN.md - Integrationsbeweis gegen die laufende Topologie und docs/oauth-setup.md (Wave 7)

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 03-09-PLAN.md - Staging-E2E mit Claude.ai und ChatGPT (AUTH-04, Owner-Action) (Wave 8)

**UI hint**: yes

### Phase 4: Per-User-Verwaltung und prepare_context

**Goal**: Nutzer kontrollieren den MCP-Zugriff selbst in den Nextcloud-Settings, und ein einziger prepare_context-Aufruf bündelt den relevanten Cloud-Kontext token-effizient
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: EXAPP-02, TOOL-08
**Success Criteria** (what must be TRUE):

  1. Nutzer aktiviert/deaktiviert den MCP-Zugriff in den Nextcloud-Settings; Deaktivierung wirkt sofort (der nächste Tool-Aufruf des verbundenen Clients schlägt mit klarer Meldung fehl)
  2. Nutzer sieht in den Settings seine verbundenen Clients und widerruft einzelne Tokens, ohne andere Clients zu beeinflussen
  3. Ein prepare_context-Aufruf liefert relevante Dateien, Termine, Notizen und Deck-Karten zu einer Anfrage gebündelt in einer token-effizienten Antwort, mit Kurz/Voll-Parameter und parallelem Fan-out
  4. Fällt eine Teilquelle aus oder überschreitet ihr Budget/Timeout, ist sie im prepare_context-Ergebnis explizit als degradiert markiert (keine stillen Teil-Ergebnisse)

**Plans**: 4 plans in 3 waves
**UI hint**: yes

Plans:
**Wave 1**

- [x] 04-01-PLAN.md - Schalter im Store und R1 an der Transportgrenze (Wave 1)
- [x] 04-02-PLAN.md - prepare_context: Fan-out, Kurz/Voll, degraded, Tool-Oberfläche in einem Zug (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-03-PLAN.md - Connections-Seite: Liste, Widerruf je Zeile, Schalter, Route 13, E2E-Wächter (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-04-PLAN.md - Settings-Wegweiser (Link-only-Form) und Live-Abnahme mit SC-5-Messung (Wave 3)

### Phase 5: Hardening und Store-Einreichung

**Goal**: Die App ist gehärtet, signiert und vor der Nextcloud Conference September 2026 im Nextcloud App Store eingereicht, mit Setup-Doku für alle Ziel-Clients
**Mode:** mvp
**Depends on**: Phase 4 (CSR-PR startet entkoppelt bereits nach dem App-ID-Freeze aus Phase 1, spätestens 3-4 Wochen vor der Conference)
**Requirements**: EXAPP-04, EXAPP-05
**Success Criteria** (what must be TRUE):

  1. Die App ist im Nextcloud App Store eingereicht (Zertifikat via CSR-PR, signiertes Release, XSD-valide info.xml, Datenweitergabe-Disclosure, Multi-Arch-Image auf ghcr.io) vor der Nextcloud Conference September 2026
  2. Ein Admin installiert die App per Klick auf einer sauberen Nextcloud-Instanz aus dem Store-Paket; Deinstallation räumt alle Daten (inkl. Tokens) auf
  3. Der Permission-Parity-Test besteht: Ein eingeschränkter Nutzer sieht via MCP nichts, was die Weboberfläche ihm nicht zeigt; Create-only-Write-Tests und Negative-Credential-Loadtest sind grün
  4. Für Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI und MUCGPT existiert je eine Setup-Doku mit den bekannten Stolperstellen, jeweils gegen den echten Client verprobt

**Plans**: 10 plans in 5 waves

Plans:
**Wave 1**

- [x] 05-01-PLAN.md - Admin-Werte lesen und Admin-Settings-Form registrieren (BL-06, Teil 1) (Wave 1)
- [x] 05-03-PLAN.md - Permission-Parity mit Read-only-Share plus Create-only ueber die Kette (SC 3) (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md - Schalter-Durchsetzung dort, wo eine Autorisierung entsteht (BL-10) (Wave 2)
- [x] 05-04-PLAN.md - Admin-Werte wirken, Setup-Zustand statt Startabbruch (BL-06, Teil 2) (Wave 2)
- [x] 05-05-PLAN.md - Negativ-Credential-Lasttest und Admin-Sicherheitsdoku (SC 3) (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-06-PLAN.md - Purge-Kommando, Store-Wipe, Data-Key-Loeschung, privacy.md-Korrektur (SC 2) (Wave 3)
- [x] 05-07-PLAN.md - Client-Doku Open WebUI und MUCGPT (EXAPP-05, SC 4) (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 05-08-PLAN.md - Install- und Deinstallations-Beweis auf frischer Instanz plus Runbook (SC 2) (Wave 4)
- [x] 05-09-PLAN.md - FAQ dreisprachig, Store-Beschreibung, README-Status, Manifest-Textgates (Wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 05-10-PLAN.md - Release 0.1.1 und Store-Pflege mit Live-Nachweis (EXAPP-04) (Wave 5)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Server-Kern | 14/14 | Complete    | 2026-08-14 |
| 2. ExApp-Shell | 7/7 | Complete    | 2026-08-15 |
| 3. OAuth 2.1 | 8/9 | In Progress|  |
| 4. Per-User-Verwaltung und prepare_context | 4/4 | Complete   | 2026-08-17 |
| 5. Hardening und Store-Einreichung | 9/10 | In Progress|  |

## Coverage

Alle 26 v1-Requirements sind genau einer Phase zugeordnet (siehe Traceability in REQUIREMENTS.md).

| Phase | Requirements |
|-------|--------------|
| 1 | SRV-01..05, TOOL-01..07, TOOL-09, AUTH-01, EXAPP-03, CONTRIB-01 (16) |
| 2 | EXAPP-01, AUTH-05, AUTH-06 (3) |
| 3 | AUTH-02, AUTH-03, AUTH-04, AUTH-07 (4) |
| 4 | EXAPP-02, TOOL-08 (2) |
| 5 | EXAPP-04, EXAPP-05 (2) |

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp)*
