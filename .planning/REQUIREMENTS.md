# Requirements: MCP Connector für Nextcloud

**Defined:** 2026-08-14
**Core Value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.

## v1 Requirements

### Server-Kern (SRV)

- [x] **SRV-01**: MCP-Client kann sich per Streamable HTTP verbinden (mcp>=2.0, bedient Session- und Stateless-Clients aus demselben Endpoint; Regressionstest gegen SDK>=1.28-Clients, Lehre aus context_agent#227)
- [x] **SRV-02**: Nutzer kann denselben Server lokal per stdio betreiben (Entry-Point ohne ExApp, App-Passwort aus Env)
- [x] **SRV-03**: Tools tragen korrekte Annotationen (readOnlyHint/destructiveHint/idempotentHint/openWorldHint) und token-schlanke Schemas (Schema-Diät-Pattern aus InfraNode)
- [x] **SRV-04**: Tool-Aufrufe gegen nicht installierte Nextcloud-Apps liefern klare Fehlertexte statt Crashes (Graceful Degradation)
- [x] **SRV-05**: Kein In-Memory-Session-State in Tools (Pagination über Handles), Server ist multi-worker-fähig

### Werkzeuge (TOOL)

- [x] **TOOL-01**: Nutzer kann Dateien suchen, Ordner listen, Dateien lesen und neue Dateien hochladen (WebDAV; kein Überschreiben, kein Löschen)
- [x] **TOOL-02**: Nutzer kann Termine in einem Zeitraum abfragen und neue Termine anlegen (CalDAV; Timezone-Edge-Cases getestet, Lehren aus Platzhirsch-Bugs #538/#544/#782)
- [x] **TOOL-03**: Nutzer kann Notizen suchen, lesen und anlegen (Notes-REST)
- [x] **TOOL-04**: Nutzer kann Deck-Boards und Karten lesen und neue Karten anlegen (Deck-REST)
- [x] **TOOL-05**: Nutzer kann Kontakte suchen (CardDAV, lesend)
- [x] **TOOL-06**: Nutzer kann berechtigungstreu über die ganze Cloud suchen (Unified Search OCS, provider-parallel)
- [x] **TOOL-07**: ChatGPT-Kompatibilitätsprofil: Tools `search` und `fetch` mit OpenAI-Schema (id/title/url bzw. id/title/text/url/metadata)
- [ ] **TOOL-08**: Gamechanger prepare_context: ein Aufruf bündelt relevante Dateien, Termine, Notizen und Karten zu einer Anfrage token-effizient (mit Kurz/Voll-Parameter)
- [x] **TOOL-09**: Kein Tool kann löschen, überschreiben oder Freigaben ändern; Permission-Level pro Tool ist dokumentiert und sichtbar

### Auth und Berechtigungen (AUTH)

- [x] **AUTH-01**: Nutzer kann sich mit App-Passwort verbinden (Bearer/Basic, für stdio und Remote)
- [ ] **AUTH-02**: Nutzer kann sich per Login Flow v2 onboarden (Browser-Login, Client sieht nie das echte Passwort)
- [ ] **AUTH-03**: MCP-Client verbindet per OAuth 2.1 nach MCP-Authorization-Spec: Protected Resource Metadata (RFC 9728), Dynamic Client Registration, PKCE S256, Token-Widerruf
- [ ] **AUTH-04**: Claude.ai-Connector und ChatGPT-Connector verbinden nachweislich plug-and-play gegen eine öffentliche Staging-Instanz (E2E-Erfolgskriterium)
- [x] **AUTH-05**: Jede Nextcloud-Anfrage läuft unter der Identität des angemeldeten Nutzers (ExApp-Impersonation bzw. Nutzer-Credentials); der Assistent sieht nie mehr als der Nutzer in der Weboberfläche
- [x] **AUTH-06**: Discovery-Endpunkte (well-known/PRM, WWW-Authenticate) sind unauthentifiziert erreichbar, auch durch den AppAPI-Proxy-Pfad (früher Spike, Hauptrisiko)
- [ ] **AUTH-07**: Admin kann steuern, welche OAuth-Clients sich verbinden dürfen: Client-Registry mit allowed-Flag als Enforcement-Punkt im AS-Design von Anfang an, Dynamic Client Registration global abschaltbar (Owner-Entscheid 14.08.2026; Admin-UI dafür darf in Phase 4 folgen)

### ExApp und Distribution (EXAPP)

- [x] **EXAPP-01**: Admin kann die App als ExApp über AppAPI installieren (Container-Backend, Heartbeat/Init/enabled_handler, Deploy Daemon; HaRP-Smoke-Test vor Einreichung)
- [ ] **EXAPP-02**: Nutzer kann in den Nextcloud-Settings den MCP-Zugriff aktivieren/deaktivieren, verbundene Clients einsehen und Tokens widerrufen (Per-User-Verwaltung, Declarative Settings)
- [x] **EXAPP-03**: App-ID ist in Woche 1 eingefroren (ohne "nextcloud" im Namen, Store-Regel; Zertifikat hängt an der ID)
- [ ] **EXAPP-04**: App ist im Nextcloud App Store eingereicht (Zertifikat via CSR-PR, Signatur, info.xml-Validierung, Datenweitergabe-Disclosure) vor der Nextcloud Conference September 2026
- [ ] **EXAPP-05**: Setup-Doku pro Client (Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI, MUCGPT) mit den bekannten Stolperstellen

### Flanke Nextcloud-Ökosystem (CONTRIB)

- [x] **CONTRIB-01**: Contribution-Fix an nextcloud/context_agent#227 (stateless_http=True bricht SDK>=1.28-Clients) als PR eingereicht *(PR: https://github.com/nextcloud/context_agent/pull/230, eingereicht 2026-08-15 mit Owner-Freigabe)*

## v2 Requirements

### Werkzeuge

- **TOOL-10**: Tasks (CalDAV VTODO, 2-3 Tools; beim Platzhirsch top-requested)
- **TOOL-11**: MCP-Prompts als Slash-Commands (2-4 kuratierte, orchestrieren prepare_context)
- **TOOL-12**: Response-Format-Parameter (kompakt/voll) für die großen Lesetools
- **TOOL-13**: Talk-, Tables-, Mail-Tools (kuratiert, nach nachgewiesener Nachfrage)
- **TOOL-14**: files_read_as_markdown, MarkItDown-artige Konvertierung (DOCX/PDF/XLSX zu Markdown) als optionales Extra `[markdown]`, damit die Basis-Installation schlank bleibt; reines Read-Tool, MIT-Lizenz AGPL-kompatibel; Parser-Angriffsfläche gehört in die Hardening-Betrachtung (Owner-Entscheidung 14.08.2026: v2, nicht v1)

### Betrieb

- **OPS-01**: SSE-Legacy-Fallback (nur bei nachgewiesenem Abnehmer-Bedarf)
- **OPS-02**: Gehostete Multi-Tenant-Remote-Instanz mit AVV (Behörden-Paket)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Tool-Flut (100+ Tools, volle CRUD-Spiegelung) | Sprengt Client-Limits (Cursor 40/80); Platzhirsch besetzt die Breite; Kuration ist unser Feature |
| Destruktive Operationen (Löschen, Überschreiben, Shares ändern, Mail senden) | Prompt-Injection-Risiko, Behörden-Blocker; "kann nichts zerstören" ist das Sicherheitsversprechen |
| Eigene semantische Suche / RAG-Index (Qdrant+Ollama) | Externe Infrastruktur, Index-Drift gegen Berechtigungen, Solo-Wartungslast; Unified Search reicht und ist berechtigungstreu |
| Eingebauter Agent/AI-Provider | Exakt der in context_agent#203 kritisierte Rucksack; wir bleiben MCP-only |
| Admin-weites Shared-Token für alle Nutzer | Bricht das Kernversprechen (Berechtigungs-Durchgriff); Per-User-Auth ab Tag 1 |
| Stateless-only-Transport als Abkürzung | Bricht heutige Clients (context_agent#227); stateless-ready ja, stateless-only nein |
| Schwergewichtige MCP-Resources als Datenkanal | Client-Support lückenhaft (ChatGPT/Cursor/Open WebUI tools-only); tools-first |
| openDesk-Suite (OpenProject, XWiki, Matrix, OX) | Phase 3 nach Oktober 2026, eigener Meilenstein |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SRV-01 | Phase 1 | Complete |
| SRV-02 | Phase 1 | Complete |
| SRV-03 | Phase 1 | Complete |
| SRV-04 | Phase 1 | Complete |
| SRV-05 | Phase 1 | Complete |
| TOOL-01 | Phase 1 | Complete |
| TOOL-02 | Phase 1 | Complete |
| TOOL-03 | Phase 1 | Complete |
| TOOL-04 | Phase 1 | Complete |
| TOOL-05 | Phase 1 | Complete |
| TOOL-06 | Phase 1 | Complete |
| TOOL-07 | Phase 1 | Complete |
| TOOL-09 | Phase 1 | Complete |
| AUTH-01 | Phase 1 | Complete |
| EXAPP-03 | Phase 1 | Complete |
| CONTRIB-01 | Phase 1 | Complete |
| EXAPP-01 | Phase 2 | Complete |
| AUTH-05 | Phase 2 | Complete |
| AUTH-06 | Phase 2 | Complete |
| AUTH-02 | Phase 3 | Pending |
| AUTH-03 | Phase 3 | Pending |
| AUTH-04 | Phase 3 | Pending |
| AUTH-07 | Phase 3 | Pending |
| EXAPP-02 | Phase 4 | Pending |
| TOOL-08 | Phase 4 | Pending |
| EXAPP-04 | Phase 5 | Pending |
| EXAPP-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0

---
*Requirements defined: 2026-08-14*
*Last updated: 2026-08-14 after roadmap creation (traceability filled)*
