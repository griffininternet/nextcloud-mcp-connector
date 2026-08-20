# Requirements: MCP Connector für Nextcloud — Milestone v1.1

**Defined:** 2026-08-20
**Core Value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Milestone:** v1.1 "Verwaltungs-Clients und Härtungs-Reste" — bewusst klein, Deadline Nextcloud Conference September 2026.

## v1.1 Requirements

### Verwaltungs-Clients (CLIENT)

- [ ] **CLIENT-01**: MUCGPT verbindet sich live nach dem Protokoll in docs/client-setup.md (drei Checks in Ausfallreihenfolge plus Berechtigungs-Gegenprobe); die Messdatei ersetzt den Lücken-Absatz, BL-12 wird geschlossen. *Externer Blocker: it@M-Antwort (Mail gesendet 20.08.); die Identitätsfrage (Service-Konto vs. Per-User) wird beim Termin gestellt und entscheidet über einen künftigen Token-Exchange.*
- [ ] **CLIENT-02**: F13 verbindet sich live gegen den Connector; Messdatei neben den anderen Client-Nachweisen, docs/client-setup.md erhält eine belegte F13-Sektion. *Laut Outreach-Dossier MCP-fähig; Zugang läuft über Owner-Kontakt.*
- [ ] **CLIENT-03**: BaerGPT verbindet sich live gegen den Connector; Messdatei und belegte Doku-Sektion wie bei CLIENT-02. *Laut Outreach-Dossier MCP-fähig; Zugang läuft über Owner-Kontakt.*
- [ ] **CLIENT-04**: Cursor verbindet sich live nach der Teilregistrierung (Commit a80af0a): DCR mit Cursors Drei-URI-Body wird 201, Autorisierung und Tool-Aufruf laufen durch (BL-04-Rest, F1 aus dem v1.0-Audit).
- [ ] **CLIENT-05**: Die Loopback-Portfrage ist beantwortet: gemessen, ob ein Client mit wechselndem 127.0.0.1-Port (Kandidat: Claude Code) am exakten Redirect-Matching scheitert; falls ja, Entscheid über die RFC-8252-7.3-Ausnahme (beliebiger Port auf Loopback) dokumentiert und umgesetzt oder als akzeptiertes Risiko festgehalten.

### Auth-Härtung (AUTH)

- [ ] **AUTH-08**: Ein Client, der sich per Client ID Metadata Document ausweist (CIMD, DCR-Nachfolger der MCP-Spec; Kandidat: Claude Code), kann sich verbinden; die DCR-Kontrollen gelten unverändert (Redirect-URI-Prüfung, Allowlist-Modus AUTH-07 greift, ein abgeschaltetes DCR ist über CIMD nicht umgehbar) (BL-05).
- [x] **AUTH-09**: Der CIMD-Dokumentabruf ist als Outbound-Request SSRF-geprüft und fail-closed: keine privaten/link-lokalen Ziele, nur https, Größen- und Zeitlimit, kontrolliertes Caching; Negativtests belegen jede Grenze.

### Store und Installation (EXAPP)

- [x] **EXAPP-06**: NC-34.0.3-UI-Smoke: auf einer auf 34.0.3 aktualisierten Instanz ist nachgewiesen, ob die Store-UI den Install-/Remove-Knopf für ExApps zeigt (Upstream-Fix app_api#971/server#61709); bei Erfolg werden docs/exapp-install.md und der Store-Text auf die wörtlich wahre Ein-Klick-Story angepasst.

### Conference (CONF)

- [ ] **CONF-01**: Demo-Material für die Nextcloud Conference September 2026 steht: eine reproduzierbare Demo-Strecke (Verbindung, Tool-Aufrufe, Per-User-Verwaltung, Widerruf) gegen eine laufende Instanz, mit Drehbuch.
- [ ] **CONF-02**: Ein Lightning-Talk-Entwurf (Folien plus Sprechzettel) liegt vor; ob eingereicht wird, entscheidet der Owner.

## Future Requirements

Vorgemerkt, nicht in v1.1:

- v1.2 "Kuratierte Breite": Talk-, Tables- und Mail-Tools, prepare_context-Ausbau (Q4 2026, nach Store-Feedback)
- v2.0 "openDesk/Behörden": OpenProject, XWiki, Matrix, OX, Gruppen-Policies, Audit-Log, ZenDiS-Kontakt
- Token Exchange für MUCGPT-Per-User-Identität (nur falls die it@M-Antwort Per-User-Treue fordert; Ergebnis von CLIENT-01)
- Findling-Synergie BL-01..03 (Cross-Links, Content-Hit-Fidelity-Test; nach Findling v1.0)
- BL-13-Reste (IN-01..06 Advisory-Befunde), soweit nicht von AUTH-08/09 mit erledigt
- Prototype-Fund-Antrag (Frist 1.10. bis 30.11.2026; Querschnitt, kein Code-Requirement)

## Out of Scope

| Feature | Reasoning |
|---------|-----------|
| Private-use URI-Schemes als Redirect (cursor://...) | D-35 steht: ein Desktop-Scheme gehört niemandem exklusiv, jede andere App kann es abfangen; Cursor kommt über die Teilregistrierung herein |
| Tool-Breite (Talk/Tables/Mail) | v1.2; v1.1 bleibt bewusst klein wegen Conference-Deadline |
| Destruktive Operationen | Unverändertes v1-Sicherheitsversprechen |
| Eigener LLM/RAG-Index | Unverändert: das Modell sitzt beim Client |
| MUCGPT-Fork oder angepasste Connector-Version | Verifiziert unnötig: MUCGPT ist voller MCP-Client, der Engpass ist das Auth-Modell, nicht das Protokoll |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLIENT-01 | Phase 7 | Pending |
| CLIENT-02 | Phase 7 | Pending |
| CLIENT-03 | Phase 7 | Pending |
| CLIENT-04 | Phase 6 | Pending |
| CLIENT-05 | Phase 6 | Pending |
| AUTH-08 | Phase 6 | Pending |
| AUTH-09 | Phase 6 | Complete |
| EXAPP-06 | Phase 6 | Complete |
| CONF-01 | Phase 6 | Pending |
| CONF-02 | Phase 6 | Pending |

**Coverage:** 10/10 v1.1-Requirements auf genau eine Phase abgebildet, keine Waisen, keine Dubletten.

---
*Requirements defined: 2026-08-20*
*Last updated: 2026-08-20 (Roadmap v1.1: Phasen 6-7 zugeordnet)*
