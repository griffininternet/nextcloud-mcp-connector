# Project Research Summary

**Project:** MCP Connector für Nextcloud (MCP-only ExApp)
**Domain:** Nextcloud ExApp (Python), Remote-MCP-Server mit OAuth 2.1, App-Store-Distribution
**Researched:** 2026-08-14
**Confidence:** HIGH (Kernentscheidungen gegen offizielle Doku, PyPI und Live-GitHub-Daten verifiziert)

## Executive Summary

Das Produkt ist ein kuratierter, MCP-only Remote-Server als Nextcloud External App (ExApp): ~16-19 nicht-destruktive Tools über Files, Calendar, Notes, Deck, Contacts und Unified Search, per Klick aus dem Nextcloud App Store installierbar, mit Spec-konformem OAuth 2.1 und Per-User-Verwaltung in den Nextcloud-Settings. Die Wettbewerbsanalyse validiert exakt diese Positionierung: Der offizielle context_agent hat OAuth abgelehnt (#74 "not planned"), kann nicht skalieren und keine Per-User-Tokens; der Community-Platzhirsch (cbcoutinho, 110+ Tools) sprengt Client-Limits (Cursor deaktiviert ab 80 Tools) und hat keinen Store-Vertrieb. Die Lücke "MCP-only ExApp mit Spec-OAuth und Per-User-Kontrolle" ist offen nachgefragt (context_agent#105, #203) und von niemandem besetzt.

Empfohlener Ansatz: Python 3.13 + offizielles MCP-SDK, nc_py_api[app] für den AppAPI-Lifecycle, rohe httpx-Clients für alle Nextcloud-User-APIs (WebDAV/CalDAV/CardDAV/REST/OCS), ein eigener kleiner Authorization Server (4 Endpoints) im selben Prozess, opake Tokens mit Store-Lookup. Die zentrale Sicherheits-Invariante: Die NC-User-ID kommt ausschließlich aus dem validierten Token und fließt über eine einzige Gateway-Schicht in AppAPI-Impersonation oder App-Passwort-BasicAuth, nie aus Tool-Parametern, nie mit Admin-Rechten. Wichtige neue Faktenlage aus der Stack-Recherche: mcp 2.0.0 ist seit 28.07.2026 stabil (GA), die 1.x-Linie ist offiziell Maintenance-only. Die ursprüngliche Projektentscheidung "1.27 pinnen" ist damit überholt; Empfehlung ist mcp>=2.0,<3 mit dokumentiertem Fallback-Pin auf 1.29, da v2 beide Protokoll-Ären (2025er-Clients wie Claude.ai/Cursor und die stateless Spec 2026-07-28) aus demselben Endpoint bedient und damit auch die context_agent#227-Fehlerklasse konstruktiv löst.

Die zwei größten Risiken: (1) OAuth-Discovery-Fehler, die häufigste Ausfallklasse bei Custom-Connectoren; "funktioniert im Inspector, scheitert auf claude.ai" muss durch frühe E2E-Tests gegen eine öffentlich erreichbare Staging-Instanz ausgeschlossen werden. (2) Die harte September-Deadline gegen die Store-Zertifizierungs-Pipeline (CSR-PR, Signatur, Image-Publishing); CSR-Merges dauern aktuell 1-5 Tage, aber der CSR muss 3-4 Wochen vor der Konferenz raus und die App-ID (ohne "nextcloud" im Namen!) muss in Woche 1 eingefroren werden, weil das Zertifikat an die ID gebunden ist. Zwei technische Unbekannte mit MEDIUM-Confidence brauchen frühe Spikes: CalDAV/CardDAV mit AppAPI-Auth-Headern und die Consent-Bridge über die AppAPI-Proxy-Route.

## Key Findings

### Recommended Stack

Offizielles MCP-SDK statt FastMCP-Fork, nc_py_api als ExApp-Rahmen, httpx roh für alle Daten-APIs (der vom Platzhirsch validierte Weg), Parsing an Spezial-Libs delegiert. Der Authorization Server wird bewusst selbst gebaut (4 FastAPI-Routen + PyJWT), weil Nextclouds oauth2-App kein DCR und keine Scopes kann und Authlib für 4 maßgeschneiderte Endpoints zu schwer ist.

**Core technologies:**
- Python 3.13 + uv: Runtime und Toolchain (Projekt-Constraint)
- mcp[cli]>=2.0,<3: offizielles SDK, GA seit 28.07.2026; TokenVerifier, RFC-9728-PRM und 401-Discovery eingebaut; stateless HTTP nativ; Fallback-Pin >=1.29,<2 dokumentiert
- nc_py_api[app]>=0.30,<1: AppAPI-Handshake, Auth-Middleware, Declarative Settings (Per-User-UI), Impersonation
- FastAPI + Uvicorn: ASGI-Rahmen, MCP-App als Sub-App gemountet
- httpx + lxml + icalendar + recurring-ical-events + vobject: alle Nextcloud-User-APIs plus DAV/ICS/VCF-Parsing
- PyJWT[crypto]: selbst signierte Tokens (bereits transitive mcp-Dependency)
- Test: pytest + In-Memory `Client(mcp)`, lokale Wegwerf-NC via juliusknorr/nextcloud-docker-dev, CI mit offiziellem nextcloud-Image + manual-install

**Nicht verwenden:** FastMCP standalone (Fork, 4.x Beta), aiodav (verwaist), Docker Socket Proxy als Deploy-Ziel (deprecated, Entfernung NC 35, HaRP ist der Weg), Nextclouds oauth2-App als AS, sync-HTTP-Clients im async-Server.

### Expected Features

**Must have (table stakes):**
- Streamable HTTP als Primärtransport (Open WebUI ab 0.6.31 NUR Streamable HTTP), stateless-ready designt
- Auth-Fallback App-Passwort + Login Flow v2 (Selfhoster-Onboarding ohne OAuth, Pflicht für stdio)
- Kern-Lesetools für Files/Calendar/Notes/Deck/Contacts plus Unified Search OCS (berechtigungstreu)
- ChatGPT-Profil: exakt die zwei Pflichttools `search` und `fetch` mit Kompatibilitäts-Schema
- Tool-Annotationen (readOnlyHint etc.) + Schema-Diät (InfraNode-Playbook, outputSchema = 56% des Token-Footprints)
- Berechtigungs-Durchgriff (Assistent sieht nie mehr als der Nutzer), Graceful Degradation bei fehlenden Apps, Setup-Doku pro Client

**Should have (differentiators):**
- OAuth 2.1 nach MCP-Authorization-Spec (PRM, DCR, PKCE, Revocation): meistgefordert, von niemandem geliefert; Voraussetzung für Plug-and-play mit Claude.ai/ChatGPT
- Per-User-Verwaltung in den NC-Settings (an/aus, Clients einsehen, Tokens widerrufen)
- MCP-only ExApp per Klick aus dem App Store (die #203-Lücke)
- prepare_context als Bündel-Tool (spart 4-6 Roundtrips und Bestätigungsdialoge)
- Kuratiert schlank (~16-19 Tools) und konstruktionsbedingt nicht destruktiv (Behörden-Argument)

**Defer (v1.x/v2+):**
- Tasks (VTODO), MCP-Prompts, Response-Format-Parameter, SSE-Fallback (v1.x nach Nachfrage)
- Talk/Tables/Mail/Cookbook, openDesk-Suite; semantische Suche NIE selbst (Unified Search stattdessen)

**Anti-Features (bewusst nicht):** Tool-Flut, destruktive Operationen, eigener RAG-Index, Admin-weites Shared-Token, ausufernde Output-Schemas.

### Architecture Approach

Ein ASGI-Prozess mit klaren Schichten: ExApp-Shell (Lifecycle, Settings), Auth-Layer (RS via SDK-TokenVerifier + embedded AS mit 4 Routen + Consent-Bridge über AppAPI-Proxy), MCP-Server-Layer (Tool-Registry, stateless), Nextcloud-Gateway als Sicherheitsgrenze (CredentialProvider-Abstraktion: A = AppAPI-Impersonation im ExApp-Modus, B = App-Passwort für stdio/standalone), Token-Store (SQLite, Postgres-fähiges Schema). Zwei dünne Entry-Points (HTTP/stdio), ein Kern; tools/ importiert nie auth/ oder exapp/. Drei Deployment-Topologien aus einem Codebase: ExApp in-instance, standalone remote, lokal stdio.

**Major components:**
1. Nextcloud-Gateway: einzige Quelle des User-Kontexts (Token -> subject -> Clients), erzwingt Berechtigungs-Durchgriff
2. Auth-Layer: TokenVerifier (RS, vom SDK getragen) + eigener Mini-AS (/authorize, /token, /register, AS-Metadata) + Login-Flow-v2-Fallback
3. MCP-Server-Layer: ~16-19 freistehende, transport-agnostische Tool-Funktionen mit Permission-Tiers (Scopes nc:read/nc:write)
4. ExApp-Shell: /heartbeat, /init, enabled_handler, Declarative Settings (preferences_ex, Enable-Flag wirkt sofort im Verifier)
5. Token-Store: opake Token-Hashes, Client-Registrierungen, Grants, Widerruf

### Critical Pitfalls

1. **OAuth-Discovery-Kette bricht Claude.ai/ChatGPT silently:** Jedes fehlende Glied (PRM mit Pfad-Suffix, WWW-Authenticate-Pointer, DCR, PKCE-S256-Advertisement, Audience-Binding RFC 8707, 10s-Token-Timeout, Redirects) killt den Connect. Prävention: Discovery als eigenes Deliverable mit Curl-Checkliste, E2E-Test von öffentlichem Netz aus (claude.ai lehnt private IPs vor dem ersten Request ab).
2. **Session-State-Annahmen im Transport (context_agent#227-Klasse):** Kein Tool darf Session-State brauchen; Pagination über opake Handles, User-Kontext pro Request aus dem Token. Client-Matrix-Test (alte und neue SDK-Clients) einplanen; mcp 2.x entschärft das strukturell.
3. **ExApp-Deploy/Registrierung scheitert umgebungsspezifisch:** Heartbeat/init/enabled als allererster ExApp-Code, Test Deploy von Tag 1 grün halten, auf zwei Topologien testen (docker-compose + Nextcloud AIO).
4. **Zertifizierungs-Pipeline vs. September-Deadline:** CSR 3-4 Wochen vorher (Merge-Realität 1-5 Tage plus Rückfragen), App-ID ohne "nextcloud" in Woche 1 einfrieren (Zertifikat ist ID-gebunden), Multi-Arch-Image vor Store-Release pushen, Signing-Key wie Produktions-Secret behandeln.
5. **System-Credentials umgehen leise die Nutzerrechte:** Eine einzige Client-Factory, die eine User-Identität erzwingt; Permission-Parity-Test mit eingeschränktem Nutzer; exapp_impersonation.log als Audit-Argument dokumentieren.
6. **Brute-Force-Protection drosselt den ganzen Server (eine IP, viele User):** Nie Auth-Retries, Validierung cachen, 401/429 mit handlungsfähigen Meldungen, Admin-Runbook (occ security:bruteforce:reset, Allowlist).

## Implications for Roadmap

Basierend auf der Recherche empfohlene Phasenstruktur (folgt der verifizierten Build-Order aus ARCHITECTURE.md; jede Stufe ist unabhängig demo-fähig, das Auth-Neuland liegt hinter den verifizierten NC-Zugriffen):

### Phase 1: Kern ohne ExApp (Tools + Clients + stdio)
**Rationale:** Schnellste Feedback-Schleife; deckt die MEDIUM-Confidence-Unbekannten (DAV-Handling) früh auf; ein stdio-Server ist bereits ein nutzbares Produkt für Entwickler. App-ID und Name (ohne "nextcloud") werden HIER eingefroren, bevor irgendetwas daran hängt.
**Delivers:** httpx-Clients (WebDAV/CalDAV/CardDAV/Notes/Deck/OCS), ~14 Kern-Tools inkl. search/fetch, stdio-Entry mit App-Passwort gegen lokale Docker-NC, Schema-Diät + Annotationen von Anfang an, CI-Token-Budget-Check für tools/list.
**Addresses:** Kern-Lesetools, ChatGPT-Profil search/fetch, Annotationen, Graceful Degradation.
**Avoids:** Schema-Bloat (P3), WebDAV/CalDAV/OCS-Gotchas (Timezone/DST-Testmatrix, SEARCH-Template, OCS-Envelope), späte App-ID-Änderung (P8).

### Phase 2: Streamable HTTP + Stateless-Beweis
**Rationale:** Beweist das Stateless-Design, bevor Auth und ExApp obendrauf kommen; billiges Inkrement (Dummy-TokenVerifier mit statischem Token -> fixer User).
**Delivers:** entry_http mit gemounteter MCP-App, Restart-mid-conversation-Test, Client-Matrix-Test (alte + neue SDK-Clients).
**Uses:** mcp 2.x Streamable HTTP, FastAPI-Mounting.
**Implements:** MCP-Server-Layer + Pattern "Token -> User-Context-Injection" (noch mit Dummy).
**Avoids:** Session-State-Annahmen (P2, context_agent#227-Regressionstest).

### Phase 3: ExApp-Shell + AppAPI-Integration
**Rationale:** Lifecycle-Endpoints müssen vor jeder ExApp-Funktionalität stehen; der DAV-über-AppAPI-Spike (MEDIUM confidence) entscheidet, ob Provider A alle API-Familien trägt oder CalDAV/CardDAV bei Provider B bleiben.
**Delivers:** /heartbeat, /init (mit Progress), enabled_handler, Registrierung an Test-NC, Provider A (Impersonation) für Files verifiziert, DAV-Spike mit AppAPI-Headern, Test Deploy grün auf docker-compose + AIO.
**Uses:** nc_py_api[app], AppAPIAuthMiddleware, HaRP/manual-install.
**Implements:** ExApp-Shell, Credential-Provider-Abstraktion (Pattern 2).
**Avoids:** Deploy-/Registrierungs-Failures (P4), System-Credential-Bypass (P6, Client-Factory-Design hier festzurren).

### Phase 4: OAuth 2.1 (PRM + DCR + embedded AS + Consent-Bridge)
**Rationale:** Größter Neuland-Anteil und der Kern-Differenzierer; braucht die stabilen Phasen 1-3 als Basis. Enthält die zwei Haupt-Spikes: unauthentifizierte Discovery-Endpunkte durch den AppAPI-Proxy und Consent-Bridge via Proxy-Route (beide MEDIUM confidence).
**Delivers:** TokenVerifier (echt), 4 AS-Routen, PKCE, Refresh, Revocation, Consent-Seite, Login-Flow-v2-Fallback, Token-Store. Explizites Erfolgskriterium: Claude.ai-Connector UND ChatGPT-Connector verbinden Ende-zu-Ende gegen eine öffentliche Staging-Instanz.
**Uses:** mcp-SDK-Auth (TokenVerifier, AuthSettings, PRM automatisch), PyJWT bzw. opake Tokens mit Store-Lookup.
**Avoids:** OAuth-Discovery-Breakage (P1), Brute-Force-Throttling (P7, No-Retry-Policy + Validierungs-Cache hier einbauen).

### Phase 5: Per-User-Settings + prepare_context
**Rationale:** Settings-UI teilt den Token-Store mit OAuth (deshalb nach Phase 4); prepare_context baut komplett auf den fertigen Clients auf.
**Delivers:** Declarative-Settings-Seite (an/aus, Token-Liste, Widerruf, sofort wirksam), prepare_context mit parallelem Fan-out, Budget/Timeout pro Teilquelle und explizit markierten degradierten Quellen.
**Addresses:** Differenzierer Per-User-Verwaltung (#105) und prepare_context.
**Avoids:** Performance-Trap sequentielles Fan-out, silent partial results.

### Phase 6: Hardening + Store-Einreichung
**Rationale:** Zertifizierung hat eigene Durchlaufzeiten; der CSR-PR startet aber schon WÄHREND dieser Phase (braucht nur App-ID + Public Repo, nicht die fertige App).
**Delivers:** Permission-Parity-Test (eingeschränkter User: UI vs. MCP identisch), Negative-Credential-Loadtest, Verschlüsselung at rest, Create-only-Write-Tests, Uninstall-Cleanup, Multi-Arch-Image auf ghcr.io, info.xml XSD-validiert, Datenfluss-Disclosure-Text, signiertes Release, Install von Clean-Instanz, Client-Setup-Doku (Claude, ChatGPT, Cursor, Open WebUI, MUCGPT).
**Avoids:** Zertifizierungs-Lead-Time (P5), Store-Policy-Ablehnung (P8), Token-Storage/Write-Safety-Fehler.

### Phase Ordering Rationale

- Dependencies aus FEATURES.md: Token-Store vor OAuth und Per-User-UI; search/fetch vor prepare_context (beide brauchen Unified Search, search/fetch ist das kleinere testbare Inkrement); Annotationen von Anfang an (Nachrüsten heißt alle Approval-Flows neu testen).
- Das Auth-Neuland (Phase 4) liegt bewusst hinter verifizierten NC-Zugriffen; jede Phase davor ist unabhängig demo-fähig.
- Die September-Deadline erlaubt einen Scope-Schnitt nach Phase 4 (Fallback-Auth statt voller OAuth-Politur), ohne den Store-Eintrag zu gefährden; CSR-Start ist von der Fertigstellung entkoppelt.
- Frühe Spikes entschärfen die MEDIUM-Confidence-Stellen genau dort, wo sie günstig zu drehen sind (Phase 3: DAV-über-AppAPI; Phase 4: Discovery/Consent durch den Proxy).

### Research Flags

Phasen mit vermutlichem Research-Bedarf während der Planung:
- **Phase 3:** CalDAV/CardDAV mit AppAPI-Auth-Headern ist nicht explizit dokumentiert (MEDIUM); HaRP- vs. manual-install-Verhalten umgebungsspezifisch. Spike-Ergebnisse können die Provider-Aufteilung ändern.
- **Phase 4:** Consent-Bridge über die AppAPI-Proxy-Route ist abgeleitet, nicht E2E-verifiziert (MEDIUM); externe Erreichbarkeit des MCP-Endpoints (Reverse-Proxy-Route vs. Proxy-Durchgriff) ist das größte Topologie-Risiko; AS-Eigenbau gegen reale Claude.ai/ChatGPT-Connectoren validieren.
- **Phase 6:** Store-Review-Praxis für eine App, die per Design Nutzerdaten an KI-Clients gibt (Disclosure-Anforderungen), ggf. kurz nachrecherchieren.

Phasen mit Standard-Patterns (research-phase überspringbar):
- **Phase 1:** WebDAV/CalDAV/REST/OCS sind gut dokumentiert, der Roh-HTTP-Ansatz ist vom Platzhirsch praktisch validiert; InfraNode-Patterns (Schema-Diät, Graceful Degradation) liegen vor.
- **Phase 2:** SDK-Doku deckt Streamable HTTP + Mounting vollständig ab.
- **Phase 5:** Declarative Settings und preferences_ex sind offiziell dokumentiert; prepare_context ist reine Orchestrierung vorhandener Clients.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Gegen PyPI + offizielle Doku verifiziert; Restrisiko: mcp 2.0.0 ist erst 2,5 Wochen alt (Fallback-Pin 1.29 dokumentiert); NC-34-Support von nc_py_api vor Phase 1 verifizieren |
| Features | HIGH | Wettbewerber-Issues direkt verifiziert (context_agent #74/#105/#203/#227, Platzhirsch-Tracker); Client-Anforderungen aus Vendor-Doku (MEDIUM-Anteil) |
| Architecture | HIGH/MEDIUM | AppAPI-Lifecycle, MCP-Auth-Spec, SDK-Fähigkeiten HIGH; DAV-über-AppAPI und Consent-Bridge via Proxy MEDIUM (Spikes eingeplant) |
| Pitfalls | HIGH | Offizielle Docs, Live-GitHub-Daten (CSR-Durchlaufzeiten gemessen), eigene InfraNode-Messungen; einzelne NC-API-Edge-Cases MEDIUM (Community-Reports) |

**Overall confidence:** HIGH

### Gaps to Address

- **SDK-Versionskonflikt in den Research-Dateien:** STACK.md empfiehlt mcp>=2.0,<3 (GA verifiziert); FEATURES.md und PITFALLS.md wurden noch unter der Prämisse "1.27 pinnen / 2.0 ist Beta" geschrieben. Auflösung: mcp 2.x ist die Empfehlung (2.0 ist GA, nicht Beta; 1.x ist Maintenance-only); die Warnungen bleiben als Architektur-Anforderungen gültig (stateless-ready, Client-Matrix-Test alt+neu). Fallback-Pin >=1.29,<2 nur bei konkretem Blocker bis Mitte September.
- **CalDAV/CardDAV mit AppAPI-Headern:** Spike in Phase 3; Fallback ist Provider B (App-Passwort) für DAV-Familien.
- **Consent-Bridge + Discovery durch AppAPI-Proxy:** Spike früh in Phase 4; Fallback ist Login Flow v2 als Identity-Bridge plus dokumentierte Reverse-Proxy-Route für den MCP-Endpoint.
- **nc_py_api-Support für NC 34:** vor Phase 1 verifizieren (vermutlich nur Badge-Lag); min/max-version in info.xml danach festlegen.
- **AS-Eigenbau vs. reale Connectoren:** früher E2E-Test gegen Claude.ai und ChatGPT von öffentlichem Netz (in Phase 4 als Erfolgskriterium verankert).

## Sources

### Primary (HIGH confidence)
- PyPI (mcp, fastmcp, nc_py_api, caldav, httpx, pyjwt, icalendar u.a.): Versionen, GA-Status, requires_dist
- github.com/modelcontextprotocol/python-sdk (Releases) + py.sdk.modelcontextprotocol.io: v2-GA, v1-Maintenance, TokenVerifier/AuthSettings/PRM, stateless HTTP
- MCP Authorization Spec 2026-07-28: PRM MUST, DCR/CIMD, Audience-Validierung, Step-Up-Scopes
- Nextcloud-Doku: AppAPI (Auth-Header, Test Deploy, Deployment), ExApp-Troubleshooting, App-Store-Publishing-Regeln, Code Signing, WebDAV/SEARCH, Brute-Force-Protection
- github.com/nextcloud/app_api, HaRP, app-certificate-requests (CSR-Durchlaufzeiten Jul/Aug 2026 gemessen), nc_py_api-Doku und -Quellcode
- github.com/nextcloud/context_agent Issues #74, #105, #203, #227
- github.com/cbcoutinho/nextcloud-mcp-server (Feature-Umfang, Auth-Modi, Issue-Tracker)
- docs.openwebui.com (nur Streamable HTTP ab 0.6.31, OAuth 2.1 DCR)
- Interne InfraNode-Messungen: 71 Tools = ~27k Tokens, outputSchema = 56%, Schema-Diät -27%

### Secondary (MEDIUM confidence)
- Claude-Connector-Doku + Troubleshooting (support.claude.com, claude.com/docs): DCR-Pflicht, Curl-Checkliste, 10s-Token-Timeout, DNS/Private-IP-Ablehnung
- OpenAI-MCP-Doku (developers.openai.com, help.openai.com): Pflichttools search/fetch, Developer Mode, CIMD/DCR
- Cursor-Forum (40/80-Tool-Limits), MUCGPT 2.0 (München, 15.000+ Nutzer), Annotations-Verhalten in VS Code/Claude
- juliusknorr/nextcloud-docker-dev, Community-Reports zu Brute-Force bei API-Clients, Cal.com-CalDAV-Post-mortem

### Tertiary (LOW confidence)
- Community-OIDC-Provider-App (h2ck/oidc) als spätere Integrationsoption: bricht "per Klick installierbar", nur beobachten

---
*Research completed: 2026-08-14*
*Ready for roadmap: yes*
