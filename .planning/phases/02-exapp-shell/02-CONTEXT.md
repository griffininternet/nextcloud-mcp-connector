# Phase 2: ExApp-Shell - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning
**Mode:** --auto (alle Grauzonen automatisch mit der empfohlenen Option aufgelöst, einmaliger Durchgang; Audit-Trail in 02-DISCUSSION-LOG.md)

<domain>
## Phase Boundary

Die App wird als ExApp über AppAPI installierbar (Heartbeat/Init/enabled_handler, Deploy Daemon), jede Nextcloud-Anfrage läuft unter der Identität des angemeldeten Nutzers (AUTH-05, Permission-Parity belegt), und die zwei Spikes sind entschieden und dokumentiert, BEVOR Phase 3 startet: (1) Discovery-Endpunkte unauthentifiziert durch den AppAPI-Proxy (AUTH-06, Go/No-Go für die OAuth-Topologie), (2) DAV-über-AppAPI (Provider-Aufteilung Impersonation vs. App-Passwort je API-Familie).

NICHT in dieser Phase: OAuth selbst (Phase 3), Settings-UI/Token-Verwaltung (Phase 4), Store-Einreichung (Phase 5; CSR-PR #1160 läuft bereits separat).

</domain>

<decisions>
## Implementation Decisions

### ExApp-Gerüst und Paketierung
- **D-23:** Die ExApp ist ein dritter Betriebsmodus derselben Codebasis, kein neues Projekt: Die bestehende ASGI-App (entry_http.py, Starlette via mcp-SDK) wird um die AppAPI-Lifecycle-Endpunkte (/heartbeat, /init, /enabled) und die AppAPI-Auth-Prüfung erweitert. stdio und der eigenständige HTTP-Modus bleiben unverändert funktionsfähig (das Phase-1-Produkt bleibt nutzbar). [auto: empfohlene Option]
- **D-24:** Bevorzugt wird ein minimal selbst implementierter AppAPI-Kontrakt OHNE nc_py_api. Entscheidungsregel für den Researcher: Wenn die AppAPI-Handshake-/Signaturprüfung mit vertretbarem Aufwand (wenige, stabile Header-Checks laut offizieller AppAPI-Doku) selbst implementierbar ist, bleibt es dabei. Nur wenn die Prüfung nachweislich fragil oder undokumentiert ist, kommt nc_py_api als Dependency infrage; das wäre ein Package-Legitimacy-Gate (Owner) und bringt bekannten Ballast mit (01-RESEARCH.md Zeile 141: FastAPI + niquests + caldav). [auto]
- **D-25:** Container: eigenes schlankes Dockerfile (uv-basiert, non-root), kompatibel mit dem AppAPI Deploy Daemon (Docker-Socket-Variante) und HaRP. Image-Bau gehört in die CI, aber Registry-Publishing erst in Phase 5. [auto]

### Identitäts-Durchgriff (AUTH-05)
- **D-26:** Eine einzige Client-Factory bleibt die Naht: NcClients/deps.resolve_clients bekommt einen vierten Credential-Modus "ExApp-Impersonation" (AppAPI-Headers mit Nutzerkontext). Tool-Code wird NICHT angefasst (das war das erklärte Design-Ziel aus Phase 1, 01-RESEARCH.md Zeile 701/760). [auto]
- **D-27:** Provider-Aufteilung je API-Familie ist explizit ERGEBNIS des DAV-Spikes, keine Vorab-Annahme: Wenn eine API-Familie (WebDAV/CalDAV/CardDAV) keine AppAPI-Impersonation kann, nutzt genau diese Familie weiterhin Nutzer-App-Passwörter, dokumentiert pro Familie. VERBOTEN bleibt ein admin-weites Shared-Token (Out of Scope seit PROJECT.md); stille Fallbacks sind verboten, jeder Modus-Wechsel ist im Log und in der Doku sichtbar. [auto]
- **D-28:** Permission-Parity-Beweis nutzt die zwei bestehenden Testkonten (alice, eingeschränkter Nutzer bob) aus Phase 1: bob sieht über MCP exakt das, was er in der Weboberfläche sieht, belegt über mindestens files/notes/unified_search (Muster aus tests/integration/test_permission_fidelity.py weiterverwenden). [auto]

### Spikes (Reihenfolge und Go/No-Go)
- **D-29:** Der Discovery-Spike (AUTH-06) läuft ZUERST und als eigener früher Plan, weil er das Hauptrisiko ist und die OAuth-Topologie von Phase 3 entscheidet. Go-Kriterium: /.well-known/oauth-protected-resource (PRM, RFC 9728) und ein WWW-Authenticate-Header sind unauthentifiziert von AUSSEN erreichbar, auch über den AppAPI-Proxy-Pfad. No-Go-Fall: dokumentierte Fallback-Route (z.B. Route außerhalb des Proxys / eigene Subdomain / Admin-Reverse-Proxy-Regel) MUSS beschrieben und getestet sein, bevor Phase 3 startet. Ergebnis als eigenes Doc (docs/ oder .planning), nicht nur als SUMMARY-Absatz. [auto]
- **D-30:** Der DAV-Spike testet konkret: PROPFIND/REPORT/PUT unter AppAPI-Impersonation gegen die Test-NC; Ergebnisdoku enthält die Matrix API-Familie x Auth-Weg mit Beleg (HTTP-Status, Identität serverseitig verifiziert). [auto]

### Test-Infrastruktur
- **D-31:** Primär compose-basiert: compose.test.yml wird um AppAPI + Deploy Daemon erweitert (oder ein zweites compose-File, wenn das Basis-Setup schlank bleiben soll, Entscheidung beim Planner). Nextcloud AIO ist der ZWEITE Smoke-Schritt (Success Criterion 1 nennt beide); wenn AIO lokal unverhältnismäßig ist, wird das als dokumentierter offener Punkt an Phase 5 übergeben statt still gestrichen. Loopback-Binding-Regel aus WR-06 gilt weiter (127.0.0.1). [auto]
- **D-32:** Alle Phase-1-Gates gelten unverändert (ruff verschärft, pyright 0 Fehler, vulture mit Whitelist, Token-Budget scharf, Testsuite grün ohne Docker; Integrationstests opt-in). [auto]

### Claude's Discretion
- Konkrete AppAPI-Header-Namen, Handshake-Details, interne Modulstruktur (z.B. exapp.py vs. server/exapp/), Testtiefe je Spike, compose-Layout.
- Reihenfolge der Pläne innerhalb der Phase, solange der Discovery-Spike früh liegt.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt-Planung
- .planning/ROADMAP.md (Phase-2-Ziel, 4 Success Criteria, Requirements EXAPP-01/AUTH-05/AUTH-06)
- .planning/REQUIREMENTS.md (v1-Requirements, Out of Scope: kein Shared-Admin-Token, keine destruktiven Tools)
- .planning/PROJECT.md (Key Decisions, Constraints)
- .planning/phases/01-server-kern/01-CONTEXT.md (D-01 bis D-22, gelten weiter)
- .planning/phases/01-server-kern/01-RESEARCH.md (nc_py_api-Abwägung Zeile ~141, NcClients-Naht Zeile ~701/760)
- .planning/phases/01-server-kern/01-SECURITY.md (Trust Boundaries + 102 Threat-Dispositionen; neue Boundaries dieser Phase: AppAPI-Proxy zu ExApp, Deploy Daemon zu Container)
- .planning/research/ARCHITECTURE.md, STACK.md, PITFALLS.md, FEATURES.md, SUMMARY.md (Projekt-Research 2026-08-14)

### Implementierung (Phase-1-Stand, öffentliches Repo street1983nk/nextcloud-mcp-connector)
- src/mcp_connector/deps.py (drei Credential-Modi; hier hängt der vierte Modus ein)
- src/mcp_connector/entry_http.py (ASGI-App, TransportSecuritySettings, /health)
- src/mcp_connector/nextcloud/ (Client-Schicht; DAV-Spike-Gegenstand)
- tests/integration/test_permission_fidelity.py (Permission-Parity-Muster mit alice/bob)
- docs/client-setup.md (bestehende Betriebsmodi, bleibt gültig)
- docs/app-id-freeze.md (App-ID mcp_connector, eingefroren)

### Externe Referenzen (im Research zu verifizieren, Stand beachten)
- AppAPI-Dokumentation (github.com/nextcloud/app_api bzw. docs.nextcloud.com, ExApp-Lifecycle, Auth-Header, Deploy Daemon, HaRP)
- MCP Authorization Spec (Protected Resource Metadata RFC 9728, WWW-Authenticate) für die Discovery-Anforderungen des Spikes
- nextcloud/app-certificate-requests PR #1160 (laufender CSR, App-ID-Bindung)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- NcClients + deps.resolve_clients: die designierte Naht für Impersonation (Tool-Code bleibt unberührt).
- entry_http.py: laufende ASGI-App mit Host-Allowlist, /health, stateless Transport; ExApp-Endpunkte docken hier an.
- compose.test.yml + scripts/bootstrap_test_nc.sh: Test-NC mit alice/bob, Apps, Kalender, Adressbuch; Erweiterungspunkt für AppAPI/Deploy-Daemon.
- capabilities.require_app: App-Erkennung mit TTL (Gotcha: occ-Deaktivierung erst nach NC-Neustart sichtbar).
- Gates: ruff (S/SIM/C4/RUF/PT/ASYNC/RET/A/ISC), pyright standard, vulture full+Whitelist, Token-Budget 12500, AST-Gate gegen destruktive Aufrufe.

### Established Patterns
- Optionale MCP-String-Parameter als `str = ""` (Schema-Diät, kein anyOf).
- ctx-Parameter als `Context | None = None`.
- lxml SubElement mit attrib=, XXE/DTD-gehärteter Parser (xml.py), kein Duplizieren des Schutzes.
- Fehler: message + hint; 4xx ans Modell, 5xx als degradierte Antwort; kein Credential-Logging, `raise ... from None`.
- Conventional Commits `typ(02-xx):`, keine Co-Authored-By-Trailer, keine Em-Dashes, echte Umlaute.
- Executoren pushen nicht; Orchestrator pusht gesammelt nach Spot-Check.

</code_context>

<deferred>
## Deferred Ideas

- MarkItDown-Konvertierung (TOOL-14, v2, Owner-Entscheidung 14.08.).
- "Accounts"-Systemadressbuch als opt-in Parameter (Produkt-/Datenschutzentscheidung, aus 01-08).
- 11 Info-Findings aus 01-REVIEW.md + UF-01..UF-05 aus 01-SECURITY.md (nicht-blockierende Qualitäts-/Prozesspunkte; Kandidaten für Hardening in Phase 5).

</deferred>
