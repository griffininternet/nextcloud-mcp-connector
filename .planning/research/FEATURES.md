# Feature Research

**Domain:** Nextcloud MCP-Server / MCP-only ExApp (Remote-MCP-Anbindung fuer KI-Assistenten)
**Researched:** 2026-08-14
**Confidence:** HIGH (Wettbewerber und Issues direkt verifiziert), MEDIUM (Client-Anforderungen aus Vendor-Doku plus Sekundaerquellen)

## Feature Landscape

### Table Stakes (Users Expect These)

Fehlt eines davon, wirkt das Produkt kaputt oder ist mit den Ziel-Clients schlicht nicht nutzbar.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Streamable-HTTP-Transport mit echtem Session-Handling | Standard-Transport aller Remote-Clients (Claude.ai, ChatGPT, Cursor, Open WebUI nativ ab v0.6.31 NUR Streamable HTTP). context_agent#227 zeigt: stateless_http=True mit SDK >= 1.28 terminiert Sessions sofort ("McpError: Session terminated") | MEDIUM | Sessionfaehig ausliefern, Architektur trotzdem stateless-ready halten (kein Session-State in Tools, Pagination ueber Handles). SSE nur als Legacy-Fallback erwaegen, nicht als Primaertransport |
| Auth-Fallback: App-Passwort (Bearer/Basic) + Login Flow v2 | Beide Wettbewerber koennen das; Entwickler und Selfhoster (Zielgruppe v1) erwarten einen Weg ohne OAuth-Setup. Login Flow v2 ist beim Community-Platzhirsch der empfohlene Multi-User-Pfad | MEDIUM | Login Flow v2 = Browser-Onboarding ohne manuelles App-Passwort-Kopieren. Muss auch fuer stdio-Betrieb funktionieren |
| Kern-Lesetools pro App (Files, Calendar, Notes, Deck, Contacts) | Das ist der Produktkern; ohne Lesen von Dateien/Terminen/Notizen gibt es keinen Use Case. Beim Platzhirsch waren Deck (#75), Tasks (#73), Contacts (#103) die meist-gewuenschten App-Integrationen | MEDIUM | WebDAV/CalDAV-Fallen real: Wettbewerber-Bugs bei Datumsbereichen (#538), Timezone-Handling (#782), stillschweigend ignorierten Feldern (#544). Testabdeckung fuer Edge Cases einplanen |
| Berechtigungs-Durchgriff (Assistent sieht nie mehr als der Nutzer) | Kernversprechen jeder Multi-User-Integration; context_agent#74 nennt Least-Privilege explizit als Enterprise-Anforderung | MEDIUM | Erzwungen durch Auth-Design: jede Anfrage laeuft mit Nutzer-Credentials gegen Nextcloud-APIs, nie mit Admin-Token. Unified Search OCS ist berechtigungstreu |
| ChatGPT-Kompatibilitaetsprofil: Tools `search` und `fetch` | OpenAI verlangt fuer Connectoren (ausserhalb Developer Mode, inkl. Deep Research) exakt zwei Tools namens `search` und `fetch` mit definiertem Kompatibilitaets-Schema (id/title/url bzw. id/title/text/url/metadata) | MEDIUM | `search` = Unified Search OCS ueber Provider, `fetch` = Datei/Notiz/Karte per ID laden. Ohne diese beiden Namen ist "plug-and-play mit ChatGPT" falsch |
| Korrekte Tool-Annotationen (readOnlyHint, destructiveHint, idempotentHint, openWorldHint) | ChatGPT-App-Submission verlangt Annotationen; VS Code/Claude nutzen readOnlyHint fuer "always allow" ohne Bestaetigungsdialog. Reduziert Approval-Fatigue massiv | LOW | InfraNode-Patterns vorhanden. Alle v1-Tools sind readOnly oder non-destruktiv, das laesst sich ehrlich annotieren |
| Token-schlanke Schemas und Antworten | Tool-Schemas fressen Kontext: Cursor warnt ab 40 Tools, deaktiviert ab 80; InfraNode-Messung: outputSchema = 56% des Footprints | LOW | Schema-Diaet-Playbook aus InfraNode wiederverwenden (-27% Tokens). Kurze Descriptions, keine ausufernden Output-Schemas |
| Graceful Degradation bei fehlenden Apps | Notes/Deck/Contacts sind optionale Nextcloud-Apps; Tool-Aufrufe gegen nicht installierte Apps duerfen nicht kryptisch crashen | MEDIUM | Bei tools/list idealerweise nur Tools installierter Apps anbieten oder klare Fehlertexte ("Notes app not installed"). InfraNode-Graceful-Degradation-Wrapper vorhanden |
| Setup-Doku pro Client | Nutzer scheitern real am Verbinden (Latenode/Foren voll davon: Developer Mode, Connector-Re-Enable pro Chat, HTTPS-Pflicht) | LOW | Je eine kurze Anleitung: Claude.ai/Desktop, ChatGPT (Developer Mode + Connector), Cursor, Open WebUI, MUCGPT 2.0. Mit Screenshots der Stolperstellen |

### Differentiators (Competitive Advantage)

Kein Wettbewerber hat diese Kombination; sie deckt sich mit den offen nachgefragten, unerfuellten Issues.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| MCP-Authorization-Spec-OAuth 2.1 (Protected Resource Metadata, Dynamic Client Registration, PKCE, Revocation) | Meistgefordert und von niemandem geliefert: context_agent#74 ("not planned"), Platzhirsch hat OAuth-direkt sogar deprecated. Claude.ai-Connectoren setzen DCR voraus (kein manuelles Client-ID-Feld); Open WebUI unterstuetzt OAuth 2.1 DCR nativ; OpenAI empfiehlt CIMD/DCR | HIGH | Groesster Einzelposten: eigener Authorization-Server-Layer im ExApp (Nextclouds oauth2-App kann kein DCR). Discovery-Endpunkte (/.well-known/oauth-protected-resource, WWW-Authenticate mit resource_metadata) muessen unauthentifiziert durch den AppAPI-Proxy erreichbar sein, das ist die technische Hauptrisiko-Stelle |
| Per-User-Verwaltung in den Nextcloud-Settings | context_agent#105 fordert genau das (offen, keine Antwort); context_agent-Doku gibt zu: "MCP services that require different access tokens for each user are not currently supported". Platzhirsch hat keine NC-UI | MEDIUM | Settings-Seite: Zugriff an/aus, verbundene Clients einsehen, Tokens widerrufen. Braucht Token-Store, den OAuth ohnehin benoetigt |
| MCP-only ExApp per Klick aus dem App Store | context_agent#203 fordert exakt das (geschlossen mit Doku-PR statt Umsetzung): MCP ohne AI-Provider-Zwang und ohne context_agent-Dependency-Rucksack. Store-Distribution schlaegt Docker-Compose-Anleitung bei der Zielgruppe Selfhoster/Behoerde | HIGH | AppAPI/Deploy Daemon, Signatur, Zertifikat, Store-Review. Harte Deadline September einpreisen |
| prepare_context (Kontext-Buendelung in einem Call) | Entspricht Anthropic-Guidance "wenige, konsolidierte Workflow-Tools statt API-Spiegelung": ein Aufruf liefert relevante Dateien+Termine+Notizen+Karten token-effizient. Spart dem Client 4-6 Roundtrips und dem Nutzer 4-6 Bestaetigungsdialoge | MEDIUM | Baut komplett auf den Per-App-Clients und Unified Search auf; kein eigener Index noetig. Antwortformat-Parameter (kurz/voll) einbauen |
| Kuratiert schlank: ~15-20 Tools als Feature | Cursor: Warnung ab 40, Abschaltung ab 80 Tools ueber ALLE Server hinweg; GitHub-MCP allein hat 30+. Ein 18-Tool-Server bleibt neben anderen Servern nutzbar, ein 110-Tool-Server nicht | LOW | Aktiv vermarkten ("passt neben deine anderen MCP-Server"). Belegt die bewusste Gegenposition zum Platzhirsch |
| Sicherheits-Design: konstruktionsbedingt nicht destruktiv | context_agent exponiert Datei-Loeschen, Sharing-Aenderung, Mail-Versand via MCP; das ist fuer Behoerden ein No-Go ohne Confirmation-Infrastruktur. "Kann nichts zerstoeren" ist pruefbar und kommunizierbar | LOW | Kein Delete, kein Overwrite (Upload nur neue Dateien oder explizite Konflikt-Ablehnung), keine Share-Aenderung. Permission-Level pro Tool sichtbar dokumentieren |
| MCP-Prompts als Slash-Commands | Claude Desktop/Claude Code zeigen Prompts als Slash-Commands; fast kein Nextcloud-Wettbewerber nutzt das. Billiger UX-Gewinn ("/summarize-my-week") | LOW | 2-4 kuratierte Prompts, die prepare_context orchestrieren. Nur Bonus, viele Clients ignorieren Prompts |
| Remote-Skalierbarkeit (Multi-Worker-faehig) | context_agent-Doku: "It is currently not possible to scale this app". Fuer Behoerden-Deployments (openDesk, MUCGPT mit 15.000+ Nutzern in Muenchen) ist das ein Ausschlusskriterium | MEDIUM | Kein In-Memory-Session-State, Token-Store extern (NC-DB via AppAPI oder SQLite pro Instanz vermeiden). Folgt aus der stateless-ready-Architekturentscheidung |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Tool-Flut (100+ Tools, volle CRUD-Spiegelung aller Apps) | "Mehr Apps = mehr Nutzen"; beim Platzhirsch die haeufigste Issue-Kategorie | Sprengt Client-Limits (Cursor 40/80), Token-Kosten pro Turn, Modell-Verwirrung bei aehnlichen Tools; Platzhirsch besetzt die Breite bereits | Kuratierte 15-20 Tools + prepare_context; neue Apps nur nach nachgewiesener Nachfrage (v2: Tasks, Talk, Tables, Mail) |
| Destruktive Operationen (Loeschen, Ueberschreiben, Shares aendern, Mail senden) | "Vollstaendiger Agent" wirkt maechtiger; context_agent bietet es | Prompt-Injection-Risiko bei Remote-Content, Approval-Fatigue, Behoerden-Blocker; OpenAI warnt selbst, dass Write-Actions trotz readOnly-Markierung passieren koennen (boese Server) | Nicht-destruktive Writes (neu anlegen, hochladen ohne Overwrite); Loeschen bleibt bewusst in der Nextcloud-UI |
| Eigene semantische Suche / RAG-Index (Qdrant + Ollama) | Platzhirsch hat es (experimentell), klingt nach Differenzierer | Externe Infrastruktur (Vektor-DB + Embedding-Service), Index-Drift gegen Berechtigungen, Wartungslast fuer Solo-Dev; Platzhirsch besetzt das Feld | Unified Search OCS: berechtigungstreu, provider-parallel, null Zusatzinfrastruktur; das Modell beim Client uebernimmt das Ranking |
| Eingebauter Agent/AI-Provider (context_agent-Modell) | "Alles in einer App" | Exakt der in #203 kritisierte Dependency-Rucksack; erzwingt AI-Provider-Konfiguration, obwohl das Modell beim MCP-Client sitzt | MCP-only bleiben: Daten liefern, Intelligenz beim Client lassen |
| Stateless-only-HTTP als Abkuerzung | Einfacher zu deployen, wirkt "modern" (Spec 2026-07-28) | context_agent#227: SDK >= 1.28-Clients brechen mit "Session terminated"; SDKs fuer die neue Stateless-Spec sind Beta | Sessionfaehig mit mcp ~1.27 ausliefern, Tools stateless designen, Upgrade-Pfad offen halten |
| Schwergewichtige MCP-Resources als primaerer Datenkanal | Spec-Purismus ("Files sind doch Resources") | Client-Support fuer Resources ist lueckenhaft (ChatGPT, Cursor, Open WebUI weitgehend tools-only); Daten waeren fuer die Mehrheit unsichtbar | Tools-first; Resources hoechstens minimal als Bonus fuer Claude Desktop |
| Admin-weites Shared-Token fuer alle Nutzer | Schnellster Multi-User-Hack (so macht es context_agent heute) | Bricht das Kernversprechen (Nutzer sieht mehr als erlaubt), context_agent#105 belegt den Schmerz | Per-User-Auth von Tag 1: OAuth oder Login Flow v2 pro Nutzer |
| Ausufernde Output-Schemas pro Tool | "Structured Output ist Best Practice" | InfraNode-Messung: outputSchema = 56% des Token-Footprints bei 71 Tools | Output-Schemas nur wo Clients sie wirklich nutzen; kompakte Text/JSON-Antworten mit stabilen Feldern |

## Feature Dependencies

```
OAuth 2.1 (PRM + DCR + Revocation)
    └──requires──> Token-Store (ExApp-persistent)
    └──requires──> Unauthentifizierte Discovery-Endpunkte durch AppAPI-Proxy
    └──requires──> ExApp-Grundgeruest (AppAPI, Deploy Daemon)

Per-User-Verwaltung (NC-Settings-UI)
    └──requires──> Token-Store (derselbe wie OAuth)
    └──requires──> ExApp-Grundgeruest

prepare_context
    └──requires──> Per-App-Clients (WebDAV, CalDAV, Notes-REST, Deck-REST, CardDAV)
    └──requires──> Unified Search (OCS)

search/fetch (ChatGPT-Profil)
    └──requires──> Unified Search (OCS)
    └──requires──> Datei-/Notiz-/Karten-Lesen per ID (fetch-Aufloesung)

Tool-Annotationen ──enhances──> Approval-UX (VS Code/Claude "always allow", ChatGPT-Submission)
Login Flow v2 ──enhances──> stdio-Betrieb + Selfhoster-Onboarding ohne OAuth
Remote-Skalierbarkeit ──requires──> kein In-Memory-State (Architekturentscheidung, kein Feature-Nachruesten)

Eigene semantische Suche ──conflicts──> Solo-Wartbarkeit + Berechtigungs-Durchgriff
Stateless-only-Transport ──conflicts──> SDK-1.27-Clients + ChatGPT/Claude heute
```

### Dependency Notes

- **OAuth requires Discovery durch den AppAPI-Proxy:** Claude.ai probiert bei Connect DCR und liest Protected Resource Metadata aus WWW-Authenticate/well-known. Wenn der AppAPI-Proxy-Pfad (`/index.php/apps/app_api/proxy/<app>/...`) diese Endpunkte nicht sauber unauthentifiziert durchreicht, scheitert der gesamte Plug-and-play-Anspruch. Frueh im Projekt verifizieren (Spike), nicht am Ende.
- **Per-User-UI und OAuth teilen den Token-Store:** Reihenfolge im Roadmap: Token-Store vor beiden Features.
- **search/fetch vor prepare_context bauen:** beide brauchen Unified Search; search/fetch ist das kleinere, testbare Inkrement und schaltet ChatGPT frei.
- **Annotationen von Anfang an:** nachtraeglich annotieren heisst alle Client-Approval-Flows erneut testen.

## MVP Definition

### Launch With (v1)

Der geplante Scope (~15-20 Tools ueber Files/Calendar/Notes/Deck/Contacts/Unified Search + prepare_context) wird durch die Evidenz VALIDIERT: Cursor-Limits (40/80), Anthropic-Guidance (wenige Workflow-Tools), Platzhirsch-Nachfrage (Deck/Contacts top-requested), OpenAI-Pflichttools. Eine Ergaenzung wird empfohlen (search/fetch explizit einplanen, zaehlt in die 15-20 hinein).

- [ ] Streamable HTTP mit Sessions (mcp ~1.27), stateless-ready designt: sonst laufen die Ziel-Clients nicht
- [ ] App-Passwort-Bearer + Login Flow v2: Entwickler/Selfhoster-Onboarding ab Tag 1, unabhaengig vom OAuth-Fortschritt
- [ ] OAuth 2.1 nach MCP-Authorization-Spec (PRM, DCR, PKCE, Revocation): der Kern-Differenzierer, ohne den Claude.ai/ChatGPT nicht plug-and-play sind
- [ ] Kuratierte Tools (~16-19 inkl. search/fetch): Files (Suche, Lesen, Ordner listen, Upload), Calendar (Termine im Zeitraum, Termin anlegen), Notes (Suchen, Lesen, Anlegen), Deck (Boards/Karten lesen, Karte anlegen), Contacts (Suchen), `search` + `fetch` (ChatGPT-Profil), `prepare_context`
- [ ] Tool-Annotationen + Schema-Diaet: Client-Approval-UX und Token-Budget
- [ ] Per-User-Verwaltung in NC-Settings (mind. an/aus + Token-Widerruf): Differenzierer #2, technisch mit OAuth-Token-Store verzahnt
- [ ] ExApp + App-Store-Einreichung: Distribution IST das Produktversprechen
- [ ] Graceful Degradation fuer fehlende Apps + Setup-Doku pro Client (Claude, ChatGPT, Cursor, Open WebUI, MUCGPT)

### Add After Validation (v1.x)

- [ ] Tasks (CalDAV VTODO, 2-3 Tools): beim Platzhirsch #73 top-requested, technisch billig auf dem vorhandenen CalDAV-Client; Trigger: erste Nutzer-Nachfrage
- [ ] MCP-Prompts (Slash-Commands, 2-4 Stueck): Trigger: Claude-Desktop-Nutzeranteil sichtbar
- [ ] Response-Format-Parameter (kompakt/voll) fuer die grossen Lesetools: Trigger: Token-Feedback aus realer Nutzung
- [ ] SSE-Legacy-Fallback: nur falls ein relevanter Abnehmer (z.B. aeltere ChatGPT-Konfiguration) es nachweislich braucht

### Future Consideration (v2+)

- [ ] Talk, Tables, Mail, Cookbook, News: Breite hat der Platzhirsch; erst nach Product-Market-Fit und nur kuratiert
- [ ] openDesk-Suite (OpenProject, XWiki, Matrix): Phase 3, eigener Meilenstein
- [ ] Upgrade auf Stateless-Spec 2026-07-28: wenn SDKs stabil und Ziel-Clients migriert sind
- [ ] Elicitation/Confirmation-Flows fuer riskantere Writes: erst wenn destruktive Ops ueberhaupt erwogen werden (aktuell bewusst nie)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Streamable HTTP + Sessions | HIGH | LOW | P1 |
| Kern-Lesetools (5 Apps + Unified Search) | HIGH | MEDIUM | P1 |
| search/fetch ChatGPT-Profil | HIGH | LOW | P1 |
| App-Passwort + Login Flow v2 | HIGH | MEDIUM | P1 |
| OAuth 2.1 (PRM/DCR) | HIGH | HIGH | P1 |
| ExApp + Store-Einreichung | HIGH | HIGH | P1 |
| prepare_context | HIGH | MEDIUM | P1 |
| Annotationen + Schema-Diaet | MEDIUM | LOW | P1 |
| Per-User-Settings-UI | HIGH | MEDIUM | P1 (minimal), Ausbau P2 |
| Graceful Degradation fehlende Apps | MEDIUM | LOW | P1 |
| Client-Setup-Doku | MEDIUM | LOW | P1 |
| Tasks (VTODO) | MEDIUM | LOW | P2 |
| MCP-Prompts | LOW | LOW | P2 |
| Remote-Skalierung Multi-Worker | MEDIUM | MEDIUM | P2 (Architektur P1, Betrieb P2) |
| Weitere Apps (Talk/Tables/Mail) | MEDIUM | HIGH | P3 |

## Competitor Feature Analysis

| Feature | nextcloud/context_agent (offiziell) | cbcoutinho/nextcloud-mcp-server (Platzhirsch) | Our Approach |
|---------|-------------------------------------|-----------------------------------------------|--------------|
| Distribution | ExApp, aber MCP nur als Nebenprodukt eines Agenten mit AI-Provider-Zwang | Standalone (Docker/Helm/K8s), kein App Store | MCP-only ExApp per Klick aus dem Store (Luecke aus #203) |
| Auth | Nur statisches App-Passwort als Bearer; OAuth "not planned" (#74) | App-Passwort, BasicAuth-Passthrough, Login Flow v2; OAuth-direkt deprecated | Spec-OAuth 2.1 (PRM+DCR) plus App-Passwort/Login Flow v2 als Fallback |
| Per-User | Nicht unterstuetzt (Doku + #105 offen) | Login Flow v2 pro Client, aber keine NC-UI zur Verwaltung | Verwaltung in den Nextcloud-Settings (aktivieren, einsehen, widerrufen) |
| Tool-Umfang | Alle Agent-Tools ueber ~15 Kategorien inkl. destruktiver Ops (Loeschen, Shares, Mail senden) | 110+ Tools ueber 10-12 Apps, volle CRUD | ~16-19 kuratierte Tools, nicht destruktiv, annotiert |
| Transport/Skalierung | Streamable HTTP, aber stateless_http=True bricht SDK>=1.28-Clients (#227); "not possible to scale" laut Doku | Streamable HTTP + stdio, unabhaengig deploybar | Streamable HTTP mit Sessions + stdio; stateless-ready, multi-worker-faehig |
| Suche | DuckDuckGo/eigene Suchtools | Experimentelle Vektor-Suche (Qdrant+Ollama) + App-Tools | Unified Search OCS (berechtigungstreu, ohne Zusatzinfrastruktur) + prepare_context |
| ChatGPT-Kompatibilitaet | Blockiert durch fehlendes OAuth (#74 wurde exakt dafuer geoeffnet) | Kein search/fetch-Profil dokumentiert, kein Spec-OAuth | search/fetch-Pflichttools + OAuth = beide OpenAI-Huerden adressiert |

## Sources

- https://github.com/nextcloud/context_agent (README) und https://docs.nextcloud.com/server/latest/admin_manual/ai/app_context_agent.html (MCP-Sektion: Bearer-App-Passwort, "not possible to scale", keine Per-User-Tokens, Tool-Kollisions-Warnung) [HIGH]
- https://github.com/nextcloud/context_agent/issues/74 (OAuth 2.1 + PKCE gefordert, Label "not planned", Enterprise-Least-Privilege-Motivation) [HIGH]
- https://github.com/nextcloud/context_agent/issues/105 (Per-User-MCP in User-Settings, offen, keine Maintainer-Antwort) [HIGH]
- https://github.com/nextcloud/context_agent/issues/203 (dedizierte MCP-only ExApp gefordert; geschlossen via Doku-PR, nicht gebaut) [HIGH]
- https://github.com/nextcloud/context_agent/issues/227 (stateless_http=True bricht MCP-SDK >= 1.28: "Session terminated"; Fix-Vorschlag stateless_http=False) [HIGH]
- https://github.com/cbcoutinho/nextcloud-mcp-server (110+ Tools, 10-12 Apps, Login Flow v2, OAuth-direkt deprecated, Qdrant+Ollama-Suche experimentell) und Issue-Tracker (Deck #75, Tasks #73, Contacts #103 top-requested; CalDAV-Bugs #538/#544/#782) [HIGH]
- https://support.claude.com/en/articles/11175166 und https://claude.com/docs/connectors/building/authentication (Claude-Connectoren: Streamable HTTP, OAuth mit DCR/CIMD, kein manuelles Client-ID-Feld) [MEDIUM]
- https://developers.openai.com/api/docs/mcp und https://help.openai.com/en/articles/12584461 (ChatGPT: Pflichttools search+fetch mit Kompatibilitaets-Schema, OAuth CIMD/DCR empfohlen, Developer Mode fuer volle Toolsets, Write-Confirmation) [MEDIUM-HIGH]
- https://forum.cursor.com/t/regarding-the-quantity-limit-of-mcp-tools/153432 u.a. (Cursor: 40-Tool-Warnung, 80-Tool-Abschaltung ueber alle Server) [MEDIUM]
- https://docs.openwebui.com/features/extensibility/mcp/ (Open WebUI ab v0.6.31: nativ NUR Streamable HTTP; Auth None/Bearer/OAuth 2.1 DCR/Static) [HIGH]
- https://stadt.muenchen.de/news/mucgpt-neue-version.html und https://github.com/it-at-m/mucgpt (MUCGPT 2.0: MCP-Anbindungen, teilbare Assistenten, 15.000+ Nutzer) [MEDIUM]
- https://sunpeak.ai/blogs/testing-mcp-tool-annotations/ und https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/ (Annotationen fuer ChatGPT-Submission, readOnlyHint-Approval-Verhalten in VS Code/Claude) [MEDIUM]
- Interne Referenz: InfraNode-MCP-Messung (71 Tools = ~27k Tokens, outputSchema = 56% Footprint, Schema-Diaet -27%) [HIGH, eigene Messung]

---
*Feature research for: Nextcloud MCP-only ExApp*
*Researched: 2026-08-14*
