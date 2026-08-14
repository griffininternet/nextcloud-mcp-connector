# Roadmap: MCP Connector für Nextcloud

## Overview

Der Weg führt vom sofort nutzbaren Kern zur Store-Distribution: Zuerst entsteht der komplette Tool-Kern mit stdio und Streamable HTTP (bereits ein nutzbares Produkt für Entwickler, App-ID wird hier eingefroren, Contribution-Fix als Flanke). Danach wird der Server zur ExApp mit sauberem Berechtigungs-Durchgriff, inklusive des Discovery-Spikes durch den AppAPI-Proxy als Go/No-Go für die OAuth-Topologie. Phase 3 liefert den Kern-Differenzierer OAuth 2.1 mit E2E-Beweis gegen Claude.ai und ChatGPT. Phase 4 ergänzt Per-User-Verwaltung und prepare_context. Phase 5 härtet und reicht im Store ein, vor der Nextcloud Conference September 2026 (der CSR-Prozess startet entkoppelt schon direkt nach dem App-ID-Freeze aus Phase 1).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Server-Kern** - Alle Kern-Tools, stdio und Streamable HTTP mit App-Passwort; App-ID-Freeze und context_agent-Fix
- [ ] **Phase 2: ExApp-Shell** - Installation über AppAPI, Berechtigungs-Durchgriff, Discovery- und DAV-Spikes
- [ ] **Phase 3: OAuth 2.1** - Spec-konformes OAuth mit E2E-Beweis gegen Claude.ai und ChatGPT, Login Flow v2 als Fallback
- [ ] **Phase 4: Per-User-Verwaltung und prepare_context** - Settings-UI mit Token-Kontrolle plus Bündel-Tool
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

- [ ] 01-02-PLAN.md - Walking Skeleton: files_read per stdio (Wave 2)
- [ ] 01-12-PLAN.md - App-ID-Freeze, README mit Permission-Tabelle, GitHub-Repo (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md - Test-Nextcloud per compose plus files_upload create-only (Wave 3)
- [ ] 01-04-PLAN.md - Streamable HTTP, Basic-Passthrough, Client-Matrix und Restart-Beweis (Wave 3)
- [ ] 01-06-PLAN.md - OCS-Schicht, Graceful Degradation und Notes-Tools (Wave 3)
- [ ] 01-07-PLAN.md - Kalender-Tools mit serverseitiger Expansion (Wave 3)
- [ ] 01-08-PLAN.md - Kontakte-Suche ueber CardDAV (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-05-PLAN.md - files_search und files_list mit zustandsloser Pagination (Wave 4)
- [ ] 01-09-PLAN.md - Deck-Tools: deck_browse und deck_create_card (Wave 4)
- [ ] 01-10-PLAN.md - unified_search mit parallelem Provider-Fan-out (Wave 4)
- [ ] 01-13-PLAN.md - Contribution-PR an nextcloud/context_agent#227 (Wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 01-11-PLAN.md - ChatGPT-Profil: search und fetch (Wave 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 01-14-PLAN.md - Phasenabschluss: Schreibgrenzen-Beweis, Budget-Gate, Doku, Abnahme (Wave 6)

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

**Plans**: TBD

### Phase 3: OAuth 2.1

**Goal**: MCP-Clients verbinden plug-and-play per spec-konformem OAuth 2.1, mit Login Flow v2 als Fallback für Clients ohne OAuth
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):

  1. Der Claude.ai-Connector verbindet plug-and-play gegen eine öffentlich erreichbare Staging-Instanz: URL eintragen, Browser-Login mit Consent, Tools nutzbar, ohne manuelle Client-Konfiguration
  2. Der ChatGPT-Connector verbindet ebenso Ende-zu-Ende gegen dieselbe Staging-Instanz (PRM, Dynamic Client Registration, PKCE S256, Audience-Binding komplett)
  3. Nutzer ohne OAuth-fähigen Client onboarden sich per Login Flow v2 im Browser; der Client sieht nie das echte Passwort
  4. Token-Widerruf wirkt sofort: Ein widerrufener Client erhält 401 mit korrektem WWW-Authenticate-Header und kann sich sauber neu verbinden
  5. Wiederholte fehlgeschlagene Auth-Versuche drosseln die Nextcloud-Instanz nicht (keine Auth-Retries, Validierungs-Cache, handlungsfähige 401/429-Meldungen)

**Plans**: TBD
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

**Plans**: TBD
**UI hint**: yes

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

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Server-Kern | 1/14 | In Progress|  |
| 2. ExApp-Shell | 0/TBD | Not started | - |
| 3. OAuth 2.1 | 0/TBD | Not started | - |
| 4. Per-User-Verwaltung und prepare_context | 0/TBD | Not started | - |
| 5. Hardening und Store-Einreichung | 0/TBD | Not started | - |

## Coverage

Alle 26 v1-Requirements sind genau einer Phase zugeordnet (siehe Traceability in REQUIREMENTS.md).

| Phase | Requirements |
|-------|--------------|
| 1 | SRV-01..05, TOOL-01..07, TOOL-09, AUTH-01, EXAPP-03, CONTRIB-01 (16) |
| 2 | EXAPP-01, AUTH-05, AUTH-06 (3) |
| 3 | AUTH-02, AUTH-03, AUTH-04 (3) |
| 4 | EXAPP-02, TOOL-08 (2) |
| 5 | EXAPP-04, EXAPP-05 (2) |

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp)*
