# Phase 3: OAuth 2.1 - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning
**Mode:** --auto (Claude hat je Grauzone die empfohlene Option gewaehlt; Leitplanke ist
die Owner-Vorgabe vom 15.08.: hoechste Sicherheit UND Zuverlaessigkeit fuer den
Auth-Prozess, vor Feature-Umfang und Komfort)

<domain>
## Phase Boundary

MCP-Clients verbinden plug-and-play per spec-konformem OAuth 2.1 (PRM nach RFC 9728,
Dynamic Client Registration, PKCE S256, Audience-Binding, Token-Widerruf), mit Login
Flow v2 als Fallback fuer Clients ohne OAuth. Requirements: AUTH-02, AUTH-03, AUTH-04
und NEU AUTH-07 (Admin-Client-Allowlist + DCR abschaltbar, Owner-Entscheid 14.08.).
Fuenf Success Criteria laut ROADMAP; UI hint = yes (Consent-/Login-Oberflaeche).

NICHT in dieser Phase: Admin-UI fuer die Allowlist (Phase 4 liefert die Oberflaeche,
Phase 3 liefert den Enforcement-Punkt), Datenfluss-Disclosure-Texte (Phase 6),
Store-Einreichung (Phase 5).

</domain>

<owner_directive>
## Owner-Vorgabe (15.08.2026, bindend fuer alle Plaene dieser Phase)

Hoechste Sicherheit und Zuverlaessigkeit haben Vorrang vor Feature-Umfang und Komfort.
Konkret: konservative Spec-Auslegung, fail-closed ueberall, kein implizites Vertrauen,
Negativ- und Missbrauchstests sind Akzeptanzkriterien (nicht nur Happy Path),
klare Fehlerpfade und sauberer Wiederanlauf ohne kaputte Sessions.

</owner_directive>

<decisions>
## Implementation Decisions

### AS-Architektur (wo der Authorization Server lebt)
- **D-33:** Ein minimaler eigener Authorization Server als Teil der ExApp (gleiche
  Codebasis, eigener Routen-Namespace: PRM unter /.well-known, dazu authorize/token/
  register/revoke). Die Nutzer-Authentifizierung delegiert der AS an Nextcloud per
  Login Flow v2; wir speichern und pruefen NIE selbst ein Nextcloud-Passwort.
  Die Nextcloud-oauth2-App wird NICHT verwendet (kein DCR, kein PKCE-Zwang, nicht
  OAuth-2.1-konform); kein externes IdP in v1. Researcher prueft zuerst, wie viel
  davon das MCP-Python-SDK (mcp.server.auth) fertig mitbringt, bevor etwas selbst
  gebaut wird. [auto: empfohlene Option]

### Token-Design und Speicherung
- **D-34:** Opake Zufalls-Tokens, keine JWTs in v1 (nichts, was ein Client falsch
  validieren kann; Widerruf wirkt sofort serverseitig, SC 4). Access-Token kurzlebig
  (Groessenordnung 1 h), Refresh-Token mit Rotation UND Reuse-Detection (bei
  Wiederverwendung wird die ganze Token-Familie widerrufen). Audience-Binding
  (RFC 8707 resource parameter) ist Pflicht, Tokens gelten nur fuer diese Resource.
  Je Authorization wird genau ein dediziertes Nextcloud-App-Passwort (via Login
  Flow v2) erzeugt und verschluesselt at rest abgelegt; Widerruf loescht Token UND
  App-Passwort. Ablageort und Verschluesselungsverfahren entscheidet der Researcher
  (Kandidaten: SQLite im ExApp-Volume mit Schluessel aus APP_SECRET-Ableitung);
  Klartext-Ablage ist verboten. [auto]

### DCR-Policy und Client-Allowlist (AUTH-07)
- **D-35:** DCR ist im Auslieferungszustand AN (SC 1 und 2 verlangen plug-and-play
  fuer Claude.ai und ChatGPT), ABER: Client-Registry mit allowed-Flag ab dem ersten
  Commit, Enforcement bei JEDER Token-Ausgabe und jedem authorize (nicht nur bei der
  Registrierung); globaler Schalter, der DCR komplett abschaltet; Allowlist-Modus
  (nur gelistete Client-IDs/Redirect-URIs), in v1 per Config/occ/Env schaltbar,
  Admin-UI folgt in Phase 4. Redirect-URIs matchen exakt (kein Prefix-Match),
  https ist Pflicht mit der spec-ueblichen localhost-Ausnahme fuer native Clients.
  Registrierungen unbenutzter Clients verfallen (Aufraeumen, kein unbegrenztes
  Wachstum der Registry). [auto]

### Login Flow v2 Fallback (AUTH-02)
- **D-36:** Clients ohne OAuth onboarden ueber den Login Flow v2 der Nextcloud
  selbst (poll-Endpunkt-Muster): Wir zeigen dem Nutzer den Browser-Link, Nextcloud
  fuehrt den Login samt 2FA, das Ergebnis ist ein App-Passwort, das der Nutzer als
  Bearer nutzt (bestehender AUTH-01-Pfad bleibt unveraendert). Der Client und wir
  sehen NIE das echte Passwort; einen eigenen Passwort-Prompt gibt es unter keinen
  Umstaenden. [auto]

### Robustheit und Drosselung (SC 5)
- **D-37:** Token-Validierung laeuft gegen den eigenen Store (kein Nextcloud-
  Roundtrip pro MCP-Request); ein kurzlebiger Validierungs-Cache haelt auch das
  eigene Backend aus dem heissen Pfad. KEINE automatischen Auth-Retries gegen
  Nextcloud (Brute-Force-Guard-Schonung, Lehre aus Phase 1/Pitfall 8). 401 traegt
  immer den korrekten WWW-Authenticate-Header mit resource_metadata-Pointer
  (Spike-Ergebnis: Prioritaet 1, SEP-985), 429 traegt Retry-After. Fail-closed:
  Wenn Store oder Cache nicht erreichbar sind, wird abgelehnt, nie durchgewunken. [auto]

### Discovery- und Routing-Haertung
- **D-38:** Das akzeptierte Restrisiko AR-02-06 aus 02-SECURITY.md wird in dieser
  Phase geschlossen: die Manifest-Route ^/\.well-known/ wird auf exakt die
  benoetigten Pfade eng gefasst; die neuen AS-Routen werden einzeln und minimal
  deklariert (authorize als Browser-Route PUBLIC, token/register/revoke mit eigenen
  Kontrollen und ohne Nutzer-Session). Die Spike-Topologie gilt: resource_metadata-
  Pointer im WWW-Authenticate zuerst, Reverse-Proxy-Fallback-Regel aus
  docs/spike-discovery.md dokumentiert halten. [auto]

### Staging-Instanz und E2E-Beweis (SC 1 und 2)
- **D-39:** Der plug-and-play-Beweis mit Claude.ai- und ChatGPT-Connector braucht
  eine OEFFENTLICH erreichbare Staging-Instanz (Domain + TLS). Das ist eine
  OWNER-ACTION (Domain/Server bereitstellen; Vorschlag: Subdomain auf vorhandener
  Infrastruktur mit Caddy). Alle uebrigen Plaene laufen vorher lokal gegen die
  compose-Topologien; der E2E-Beweis ist ein eigener SPAETER Plan mit
  Owner-Checkpoint und blockiert den Rest der Phase nicht. [auto]

### Testtiefe (Owner-Vorgabe)
- **D-40:** Missbrauchstests sind Akzeptanzkriterien der Plaene, mindestens:
  Refresh-Token-Replay nach Rotation (Familie stirbt), widerrufener Client bekommt
  401 mit korrektem WWW-Authenticate und kann sich sauber neu verbinden (SC 4),
  falsche/abweichende redirect_uri wird abgelehnt, PKCE-Downgrade (fehlendes oder
  plain challenge) wird abgelehnt, Audience-Mismatch wird abgelehnt, bei DCR=aus
  scheitert die Registrierung mit benennender Meldung, Allowlist-Modus blockt
  nicht gelistete Clients an authorize UND token. [auto]

### Claude's Discretion
- Interne Modulstruktur des AS, Schema des Token-Stores, exakte Lebensdauern
  (innerhalb "kurz"), Wortlaut der Consent-Seite (ui-phase darf im plan-chain
  triggern, UI hint = yes), Reihenfolge der Plaene, solange der E2E-Beweis hinten
  liegt und die Haertung (D-38) frueh kommt.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt-Planung
- .planning/ROADMAP.md (Phase 3, 5 Success Criteria, UI hint yes)
- .planning/REQUIREMENTS.md (AUTH-02/03/04 und NEU AUTH-07; Out of Scope beachten)
- .planning/phases/02-exapp-shell/02-CONTEXT.md (D-23 bis D-32 gelten weiter)
- .planning/phases/01-server-kern/01-CONTEXT.md (D-01 bis D-22 gelten weiter)

### Spike- und Security-Ergebnisse (Grundlage dieser Phase)
- docs/spike-discovery.md (Topologie-Entscheid: resource_metadata-Pointer Prio 1,
  Reverse-Proxy-Fallback, Streaming-Befund, "Open items for phase 3")
- .planning/phases/02-exapp-shell/02-SECURITY.md (AR-02-06 MUSS hier geschlossen
  werden; Trust Boundaries der ExApp-Kette)
- docs/spike-dav.md (Provider-Entscheid Fall A)
- docs/client-setup.md (bestehende Auth-Wege, die unveraendert bleiben)

### Code-Anker
- src/mcp_connector/exapp/discovery.py (PRM-Route, wird vom Spike- zum Produktivpfad)
- src/mcp_connector/exapp/auth.py und middleware.py (Transport-Grenze, bleibt)
- src/mcp_connector/deps.py und nextcloud/credentials.py (Credential-Naht, D-26)
- appinfo/info.xml (Routen-Deklaration, D-38 aendert sie)

### Externe Spezifikationen
- MCP Authorization Spec (modelcontextprotocol.io, Version 2025-06-18 oder neuer)
- RFC 9728 (Protected Resource Metadata), RFC 8707 (Resource Indicators),
  RFC 7636 (PKCE), OAuth 2.1 Draft (draft-ietf-oauth-v2-1)
- Nextcloud Login Flow v2 (docs.nextcloud.com, client APIs)

</canonical_refs>

<code_context>
## Wiederverwendbare Bausteine

- Die PRM-Route und der WWW-Authenticate-Pointer existieren als Spike-Code in
  exapp/discovery.py und sind live verifiziert (Phase 2); Phase 3 macht daraus den
  Produktivpfad und entfernt die Probe-Route (docs/spike-discovery.md, Open items).
- Die Credential-Naht (ein Resolver, vier Modi) nimmt OAuth als fuenften Modus auf,
  ohne Tool-Code anzufassen (D-26-Muster).
- Testmuster: Lecktests/Negativtests aus tests/integration/test_permission_fidelity*
  und die Waechter-Test-Kultur aus tests/unit/test_exapp_env_setup.py.
- Gates unveraendert (D-32): ruff/pyright/vulture/pytest/Tool-Budget vor jedem Commit.

</code_context>

<deferred>
## Noted for Later

- Admin-UI fuer Client-Allowlist und DCR-Schalter: Phase 4 (Enforcement-Punkt
  entsteht in Phase 3, D-35).
- Datenfluss-Disclosure-Text: Phase 6 (Owner-Entscheid 14.08., Punkt 3).
- Findling-Synergie (README-Cross-Link, Content-Hit-Fidelity-Test): BACKLOG.md
  BL-01..03, Trigger Findling v1.0.
- AIO-Smoke, WR-12 socat-Loop, cosign: Phase 5 (Uebergaben aus Phase 2).

</deferred>
