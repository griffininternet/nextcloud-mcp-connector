# Architecture Research

**Domain:** Nextcloud MCP-only ExApp (Remote MCP Server als External App)
**Researched:** 2026-08-14
**Confidence:** HIGH (AppAPI-Lifecycle, MCP-Auth-Spec, SDK-Faehigkeiten), MEDIUM (CalDAV/CardDAV ueber AppAPI-Auth, Consent-Bridge via AppAPI-Proxy)

## Standard Architecture

### System Overview

```
                    MCP-Clients (Claude.ai, Cursor, MUCGPT, Agenten)
                                     |
                        Streamable HTTP + Bearer Token
                                     |
+---------------------------------- v ------------------------------------+
|  ExApp-Container (ein ASGI-Prozess, FastAPI + FastMCP gemountet)        |
|                                                                          |
|  +--------------------+   +---------------------------+                 |
|  | ExApp-Shell        |   | Auth-Layer                |                 |
|  | /heartbeat /init   |   | /.well-known/oauth-       |                 |
|  | enabled_handler    |   |   protected-resource (PRM)|                 |
|  | AppAPIAuthMiddle-  |   | Embedded AS: /authorize   |                 |
|  |   ware (NC->ExApp) |   |   /token /register (DCR)  |                 |
|  | Declarative        |   | TokenVerifier (RS-Rolle)  |                 |
|  |   Settings-Handler |   | Login-Flow-v2-Fallback    |                 |
|  +---------+----------+   +-------------+-------------+                 |
|            |                            |                               |
|  +---------v----------------------------v-------------+                 |
|  | MCP-Server-Layer (FastMCP, stateless_http=True)    |                 |
|  | Tool-Registry (~15-20 Tools, Permission-Tiers)     |                 |
|  | Per-Request User-Context-Injection (contextvar)    |                 |
|  +--------------------------+--------------------------+                |
|                             |                                           |
|  +--------------------------v--------------------------+                |
|  | Nextcloud-Gateway (Credential-Provider-Interface)   |                |
|  | A: AppAPI-Impersonation (nc_py_api set_user)        |                |
|  | B: App-Passwort pro User (stdio / standalone)       |                |
|  +--------------------------+--------------------------+                |
|                             |                                           |
|  +----------+  Token-Store (SQLite/Postgres im Container,               |
|  | Storage  |  Hashes; Enable-Flags via preferences_ex in NC)           |
|  +----------+                                                           |
+-----------------------------|--------------------------------------------+
                              |  AA-VERSION, EX-APP-ID, EX-APP-VERSION,
                              |  AUTHORIZATION-APP-API (base64 userid:secret)
+---------------------------- v -------------------------------------------+
|  Nextcloud-Server                                                        |
|  AppAPI (Registrierung, Deploy Daemon: Docker-Socket-Proxy oder HaRP,    |
|          Heartbeat-Ueberwachung, Proxy-Route /apps/app_api/proxy/<id>/)  |
|  APIs: WebDAV (Files+SEARCH), CalDAV, CardDAV, Notes-REST, Deck-REST,    |
|        Unified Search OCS - alle laufen unter der Identitaet des Users,  |
|        ACLs greifen serverseitig                                         |
|  Personal Settings: Declarative-Settings-Formular der ExApp              |
+---------------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| ExApp-Shell | AppAPI-Lifecycle: `/heartbeat` (200 + `{"status":"ok"}`), `/init`, `enabled_handler`; validiert eingehende NC-Requests | `nc_py_api` `run_app` + FastAPI, `AppAPIAuthMiddleware` mit `disable_for` fuer die oeffentlichen MCP/OAuth-Routen |
| Settings-UI | Per-User-Schalter (MCP-Zugriff an/aus), Token-Liste, Widerruf in den NC-Personal-Settings | Declarative Settings (NC 29+) via `nc.ui`; Werte landen in `preferences_ex` |
| Auth-Layer (RS) | Bearer-Validierung, 401 mit `WWW-Authenticate: Bearer resource_metadata=...`, PRM-Dokument (RFC 9728), Audience-Check (RFC 8707) | `mcp` SDK: `FastMCP(token_verifier=..., auth=AuthSettings(issuer_url, resource_server_url, required_scopes))` |
| Auth-Layer (AS, embedded) | OAuth 2.1: `/authorize`, `/token`, PKCE, Refresh; Client-Registrierung: DCR (RFC 7591, von Claude.ai genutzt) + CIMD-faehig halten | Eigene Starlette-Routen im selben Prozess; opake Tokens, lokal verifizierbar (kein Introspection-Roundtrip) |
| Identity-Bridge | Bindet OAuth-Grant an eine NC-User-ID | Consent-Seite hinter `/apps/app_api/proxy/<appid>/` (NC-Session liefert User-ID via AppAPI-Header); Fallback: Login Flow v2 |
| MCP-Server-Layer | Tool-Registry, Schema-Diaet, Annotationen (`readOnlyHint`), Graceful Degradation | FastMCP `stateless_http=True`, `json_response=True`; Tool-Funktionen freistehend und testbar (InfraNode-Pattern) |
| Nextcloud-Gateway | Einheitliches Interface "gib mir NC-Clients fuer User X"; kapselt beide Credential-Modi | Provider A: `NextcloudApp.set_user(user_id)` (AppAPI-Impersonation); Provider B: `Nextcloud(auth=(user, app_password))` |
| API-Clients | WebDAV/SEARCH, CalDAV, CardDAV, Notes-REST, Deck-REST, OCS Unified Search | `nc_py_api` fuer Files/OCS; CalDAV/CardDAV notfalls direkt via httpx mit denselben Auth-Headern (siehe Anti-Pattern 5) |
| Token-Store | Access-/Refresh-Token-Hashes, Client-Registrierungen, Grants, Mapping Token -> NC-User-ID | SQLite (Volume im Container) fuer v1; Schema Postgres-faehig |

## Recommended Project Structure

```
src/nc_mcp/
├── server.py              # FastMCP-Factory: baut Server aus Registry + Auth-Config
├── tools/                 # Freistehende Tool-Funktionen, transport-agnostisch
│   ├── files.py           # WebDAV: suchen, lesen, hochladen
│   ├── calendar.py        # CalDAV: lesen, Termin anlegen
│   ├── notes.py           # Notes-REST: lesen, anlegen
│   ├── deck.py            # Deck-REST: lesen, Karte anlegen
│   ├── contacts.py        # CardDAV: lesen
│   ├── search.py          # Unified Search OCS (berechtigungstreu)
│   └── prepare_context.py # Buendel-Tool, orchestriert die anderen Clients
├── nextcloud/             # Gateway + API-Clients (kein MCP-Import hier!)
│   ├── gateway.py         # CredentialProvider-Protokoll + Client-Factory
│   ├── appapi.py          # Provider A: nc_py_api / set_user
│   ├── app_password.py    # Provider B: BasicAuth mit App-Passwort
│   └── clients/           # dav.py, caldav.py, carddav.py, notes.py, deck.py, ocs.py
├── auth/                  # Nur im HTTP-Modus aktiv
│   ├── verifier.py        # TokenVerifier-Implementierung (RS)
│   ├── authserver.py      # /authorize, /token, /register (AS)
│   ├── prm.py             # Protected Resource Metadata
│   ├── consent.py         # Consent-Seite (via AppAPI-Proxy, kennt NC-User)
│   ├── loginflow.py       # Login Flow v2 (Fallback / standalone)
│   └── store.py           # Token-/Client-/Grant-Persistenz
├── exapp/                 # Nur im ExApp-Modus aktiv
│   ├── lifecycle.py       # /heartbeat, /init, enabled_handler
│   └── settings.py        # Declarative Settings + preferences_ex
├── entry_http.py          # ASGI-App: ExApp-Shell + Auth + MCP mounten
└── entry_stdio.py         # stdio: Registry + Provider B aus Env-Vars
```

### Structure Rationale

- **tools/ importiert nie auth/ oder exapp/:** Tools erhalten den User-Kontext nur ueber das Gateway. Dadurch laeuft identischer Tool-Code unter stdio (Env-Credentials) und remote (Token-abgeleiteter User).
- **nextcloud/gateway.py ist die Sicherheitsgrenze:** Die User-ID kommt ausschliesslich aus dem validierten Token (HTTP) bzw. der Env-Config (stdio), niemals aus Tool-Parametern. Das ist der Ort, an dem der Berechtigungs-Durchgriff erzwungen wird.
- **entry_http.py vs entry_stdio.py:** Zwei duenne Einstiegspunkte, ein Kern. ExApp-Lifecycle und OAuth sind reine HTTP-Anbauten.

## Architectural Patterns

### Pattern 1: Token -> User-Context-Injection pro Request

**What:** Der `TokenVerifier` validiert den Bearer, laedt aus dem Token-Store die gebundene NC-User-ID und legt sie in einen contextvar/AccessToken. Jedes Tool holt sich seine NC-Clients ueber `gateway.for_current_user()`.
**When to use:** Immer im HTTP-Modus; Voraussetzung fuer `stateless_http=True` (kein Session-State, jede Replika kann jeden Request bedienen).
**Trade-offs:** Ein DB-Lookup pro Request (opake Tokens); dafuer sofortiger Widerruf moeglich (JWTs wuerden Widerruf verkomplizieren).

```python
class NcTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        rec = await store.lookup(hash(token))          # user_id, scopes, expiry, enabled-Flag
        if rec is None or rec.expired or not rec.user_enabled:
            return None
        return AccessToken(token=token, scopes=rec.scopes,
                           subject=rec.nc_user_id, ...)  # subject = einzige Quelle der User-ID
```

### Pattern 2: Credential-Provider-Abstraktion (Impersonation vs App-Passwort)

**What:** Ein Protokoll `CredentialProvider.get_clients(user_id) -> NcClients`. Provider A nutzt die AppAPI-Authentifizierung: ExApp signiert Requests mit `AUTHORIZATION-APP-API` (base64 `userid:secret`), Nextcloud fuehrt den Call als dieser User aus, ACLs greifen serverseitig, Impersonation wird von AppAPI auditiert. Provider B nutzt pro User ein App-Passwort (Login Flow v2) mit BasicAuth.
**When to use:** A im ExApp-Deployment (kein Passwort-Handling, sauberes Audit-Log). B fuer stdio und fuer die standalone-Remote-Topologie ohne AppAPI.
**Trade-offs:** A koppelt an AppAPI-Version und funktioniert nur in registrierten ExApps; B erfordert verschluesselte Speicherung von App-Passwoertern (im ExApp-Modus vermeiden).

### Pattern 3: Colocated AS+RS mit NC-Session als Identity-Bridge

**What:** AS und RS leben im selben Prozess. Die `/authorize`-Consent-Seite wird ueber die AppAPI-Proxy-Route (`/apps/app_api/proxy/<appid>/...`) ausgeliefert: Der Browser des Users ist dort in Nextcloud eingeloggt, AppAPI reicht die Session-User-ID in den Auth-Headern an die ExApp durch. Consent-Klick bindet den Authorization Code an genau diese User-ID.
**When to use:** ExApp-Modus. Fuer standalone-Remote ersetzt Login Flow v2 die Bridge (Browser-Login, App-Passwort als Identitaetsnachweis, dann eigenes Token ausstellen; genau das Muster des Community-Servers).
**Trade-offs:** Eleganteste UX (kein Passwort, kein zweiter Login wenn NC-Session existiert); Abhaengigkeit vom Proxy-Routing muss frueh im lokalen NC-Setup verifiziert werden (Confidence MEDIUM, siehe Sources).

### Pattern 4: Permission-Tiers als Tool-Annotationen + Scope-Mapping

**What:** Jedes Tool deklariert Tier `read` oder `write_lowrisk` (MCP-Annotationen `readOnlyHint`/`destructiveHint=false` + eigenes Metadatum). Scopes `nc:read` und `nc:write` bilden die Tiers ab; der RS antwortet bei fehlendem Scope mit 403 `insufficient_scope` + `scope="nc:write"` (Step-Up-Flow der Spec 2026-07-28). Destruktive Ops existieren im Code schlicht nicht.
**When to use:** Von Anfang an; nachtraegliches Tiering ist teuer.
**Trade-offs:** Zwei Scopes reichen fuer v1; feingranularere Scopes (pro App) erst wenn Clients Step-Up sauber koennen.

## Data Flow

### Onboarding-Flow (einmalig pro Client)

```
MCP-Client -> POST /mcp (ohne Token)
    ExApp -> 401 + WWW-Authenticate: Bearer resource_metadata=".../.well-known/oauth-protected-resource", scope="nc:read"
MCP-Client -> GET PRM -> authorization_servers: [ExApp-eigener AS]
MCP-Client -> AS-Metadata (RFC 8414) -> DCR /register (Claude.ai) oder CIMD
MCP-Client -> Browser: /authorize (PKCE + resource-Parameter)
    Browser -> Nextcloud-Login (Session) -> AppAPI-Proxy -> Consent-Seite (kennt NC-User-ID aus AppAPI-Header)
    User bestaetigt -> Code -> /token -> Access-Token (an NC-User-ID gebunden, Audience = MCP-URL)
```

### Request-Flow (jeder Tool-Call)

```
Bearer-Request -> TokenVerifier (Store-Lookup: User-ID, Scopes, Enable-Flag)
    -> Scope-Check (Tier des Tools)
    -> gateway.for_current_user() -> Provider A: set_user(user_id)
    -> NC-API-Call mit AA-VERSION/EX-APP-ID/EX-APP-VERSION/AUTHORIZATION-APP-API
    -> Nextcloud fuehrt als User aus, ACLs greifen serverseitig
    -> Antwort -> Schema-Diaet/Trunkierung -> MCP-Response
```

### Key Data Flows

1. **Sicherheits-Invariante:** Die NC-User-ID fliesst genau einen Weg: validiertes Token -> AccessToken.subject -> Gateway -> AppAPI-Header. Kein Tool-Parameter, keine Env-Variable, kein Default-Admin. AppAPIs App-Level-Zugriff (Scopes wurden in neueren AppAPI-Versionen entfernt, Zugriff ist app-weit mit Audit-Log) wird nie ohne konkreten User-Kontext fuer Datenzugriffe benutzt.
2. **Settings-Flow:** User toggelt in den NC-Personal-Settings (Declarative Settings) -> Wert in `preferences_ex` -> TokenVerifier prueft das Flag bei jedem Request -> Aus-Schalten wirkt sofort, ohne Token-Ablauf abzuwarten.
3. **Lifecycle-Flow:** `occ app_api:app:register` / Store-Install -> Deploy Daemon zieht Image und startet Container -> AppAPI pollt `/heartbeat` (Timeout 600 s) -> `/init` (Setup, Settings-Formular registrieren) -> `enabled_handler` (Achtung: dort ist kein User-Kontext verfuegbar).

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Selfhoster, 1 Instanz | Ein Container via Deploy Daemon, SQLite-Token-Store, fertig |
| Behoerde, 1k-10k User | Gleicher Container; Engpass ist die Nextcloud selbst (DAV-Latenz), nicht der MCP; httpx-Connection-Pooling, Timeouts, Parallelisierung in prepare_context |
| Extern/Multi-Replika | Topologie "standalone remote": stateless_http + json_response, Token-Store auf Postgres, N Replikas hinter LB; kein Session-State by Design |

### Scaling Priorities

1. **First bottleneck:** NC-API-Roundtrips (v. a. WebDAV SEARCH und prepare_context-Faecher). Fix: paralleles Fan-out mit Budget/Timeout pro Teilquelle, harte Antwort-Trunkierung.
2. **Second bottleneck:** Token-Store-Lookups. Fix: In-Prozess-Cache mit kurzer TTL, Invalidation beim Widerruf.

### Deployment-Topologien (alle aus demselben Codebase)

| Topologie | Transport | Auth | Credential-Provider |
|-----------|-----------|------|---------------------|
| ExApp in-instance (Store) | Streamable HTTP, erreichbar via Docker-Socket-Proxy-Daemon oder HaRP (NC 32+, FRP-Tunnel; MCP-Endpoint braucht externe Erreichbarkeit fuer Remote-Clients!) | OAuth 2.1 (embedded AS) | A: AppAPI-Impersonation |
| Standalone remote | Streamable HTTP, eigene Domain | OAuth 2.1 + Login Flow v2 als Identity-Bridge | B: App-Passwoerter (verschluesselt) |
| Lokal (Entwickler) | stdio | keine (Spec: Credentials aus Env) | B: `NEXTCLOUD_URL`/`USERNAME`/`APP_PASSWORD` |

Wichtig fuer die ExApp-Topologie: Der OAuth-/MCP-Endpoint muss fuer externe Clients (Claude.ai) oeffentlich erreichbar sein. Zwei Wege: (a) Reverse-Proxy-Route des Admins direkt auf den ExApp-Port, (b) Durchgriff ueber die AppAPI-Proxy-Route. Weg (b) fuer den MCP-Endpoint ist unerprobt (Auth-Header-Konflikte moeglich); Weg (a) als Default dokumentieren. Frueh testen, das ist das groesste Topologie-Risiko.

## Anti-Patterns

### Anti-Pattern 1: App-Level-Zugriff fuer Datenabrufe

**What people do:** ExApp ruft NC-APIs ohne User-Kontext oder als Admin auf und filtert "spaeter".
**Why it's wrong:** Bricht die Kern-Invariante (MCP sieht mehr als der User); clientseitiges Filtern ist nicht verlaesslich.
**Do this instead:** Jeder Datenzugriff laeuft als der Token-gebundene User (set_user / App-Passwort). Serverseitige ACLs sind die einzige Wahrheitsquelle. Unified Search OCS ist bereits berechtigungstreu.

### Anti-Pattern 2: User-ID als Tool- oder Header-Parameter

**What people do:** Tools akzeptieren `user_id`, oder der HTTP-Layer liest eine User-ID aus Client-Headern.
**Why it's wrong:** Confused-Deputy: Jeder mit gueltigem Token koennte fremde Identitaeten anfordern.
**Do this instead:** User-ID ausschliesslich aus dem validierten Token ableiten (Pattern 1).

### Anti-Pattern 3: Nextclouds eingebaute oauth2-App als MCP-AS

**What people do:** Versuchen, MCP-Clients direkt gegen NCs OAuth2-App zu autorisieren.
**Why it's wrong:** Keine Dynamic Client Registration, keine Scopes (Token = Vollzugriff), nicht MCP-spec-tauglich; genau daran scheitert das Oekosystem seit context_agent#74.
**Do this instead:** Embedded AS in der ExApp, NC nur als Identity-Quelle (Session via Proxy oder Login Flow v2).

### Anti-Pattern 4: Session-State im MCP-Layer

**What people do:** Login-Zustand, Cursor-Pagination oder Caches an die MCP-Session haengen.
**Why it's wrong:** Verhindert stateless Streamable HTTP und Multi-Replika; kollidiert mit Spec-2026-07-28-Richtung.
**Do this instead:** Pagination ueber opake Handles im Response, alles Persistente in den Store.

### Anti-Pattern 5: nc_py_api als Alleskoenner annehmen

**What people do:** Davon ausgehen, dass nc_py_api CalDAV/CardDAV/Deck vollstaendig mit AppAPI-Auth abdeckt.
**Why it's wrong:** Files/OCS sind solide abgedeckt; Calendar laeuft ueber das caldav-Extra, CardDAV/Deck sind duenn oder fehlen. Unverifiziert, ob jede DAV-Route AppAPI-Header akzeptiert (Confidence MEDIUM).
**Do this instead:** Eigene schlanke httpx-Clients pro API-Familie, die die AppAPI-Header (bzw. BasicAuth im Provider B) selbst setzen; nc_py_api nur fuer Lifecycle, Settings, preferences_ex und Files. Spike in Phase 1: ein CalDAV-REPORT mit AppAPI-Headern gegen die Test-NC.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Nextcloud AppAPI | Registrierung via info.xml (`external-app`), Deploy Daemon, Heartbeat | API-Scopes wurden entfernt (app-weiter Zugriff + Audit); HaRP ist der neue Weg ab NC 32, Docker-Socket-Proxy weiter verbreitet; beide unterstuetzen |
| Nextcloud DAV/REST/OCS | httpx-Clients mit AppAPI-Headern oder BasicAuth | OCS immer `OCS-APIRequest: true` + `Accept: application/json` |
| MCP-Clients | Streamable HTTP + OAuth 2.1 nach Spec 2026-07-28 | PRM ist MUST; DCR fuer Claude.ai-Kompatibilitaet implementieren (in der Spec deprecated zugunsten CIMD, aber real noetig); Audience-Validierung MUST |
| App Store | Signiertes Release, Image auf Registry | Deploy Daemon zieht das Image; Multi-Arch-Build einplanen |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| tools/ <-> nextcloud/ | Direkte Funktionsaufrufe ueber Gateway-Interface | tools/ kennt keine Credentials, nur Clients |
| auth/ <-> tools/ | Nur via contextvar (AccessToken.subject) | Keine direkten Imports; stdio laedt auth/ gar nicht |
| exapp/ <-> auth/ | Enable-Flag in preferences_ex, gelesen vom Verifier | Settings-Widerruf wirkt sofort |
| entry_http vs entry_stdio | Beide bauen dieselbe Registry aus server.py | Einziger Unterschied: Transport + Credential-Provider |

## Suggested Build Order

1. **Kern zuerst, ohne ExApp:** nextcloud/clients + tools/ + stdio-Entry mit App-Passwort gegen lokale Docker-NC. Schnellste Feedback-Schleife, deckt Anti-Pattern 5 frueh auf.
2. **Streamable HTTP stateless:** entry_http mit Dummy-TokenVerifier (statisches Token -> fixer User). Beweist Stateless-Design.
3. **ExApp-Shell:** Lifecycle-Endpoints, Registrierung an Test-NC, Provider A (AppAPI-Impersonation) fuer Files verifizieren, dann DAV-Spike.
4. **OAuth-Layer:** PRM + Verifier + embedded AS + Consent-Bridge (Proxy-Route) + Login-Flow-v2-Fallback. Groesster Neuland-Anteil, braucht die Phasen 1-3 als stabile Basis.
5. **Settings-UI + Token-Verwaltung:** Declarative Settings, Widerruf, Enable-Flag.
6. **prepare_context + Packaging/Store:** Buendel-Tool auf fertigen Clients; Signatur, Listing, HaRP-/Socket-Proxy-Doku.

Begruendung der Reihenfolge: Jede Stufe ist unabhaengig demo-faehig (stdio-Server ist schon ein nutzbares Produkt fuer Entwickler); das Auth-Neuland liegt hinter den verifizierten NC-Zugriffen; die harte September-Deadline erlaubt Scope-Schnitt nach Stufe 4 (Fallback-Auth statt voller OAuth-Politur), ohne den Store-Eintrag zu gefaehrden.

## Sources

- MCP Authorization Spec 2026-07-28 (modelcontextprotocol.io/specification/latest/basic/authorization): RS-Rolle, PRM MUST, DCR deprecated aber erhalten, CIMD SHOULD, Audience-Validierung MUST, Step-Up-Scopes. Confidence HIGH.
- AppAPI-Doku (nextcloud.github.io/app_api/tech_details/Authentication.html): Header AA-VERSION, EX-APP-ID, EX-APP-VERSION, AUTHORIZATION-APP-API = base64 `userid:secret`. Confidence HIGH.
- AppAPI-Changelog (github.com/nextcloud/app_api/blob/main/CHANGELOG.md): API-Scopes entfernt; Impersonation-Audit-Logging. Confidence HIGH.
- HaRP (github.com/nextcloud/HaRP): Deploy-Proxy ab NC 32, FRP-Tunnel, `/heartbeat` muss 200 + `{"status":"ok"}` liefern, 600-s-Timeout. Confidence HIGH.
- nc_py_api-Doku (cloud-py-api.github.io/nc_py_api/NextcloudApp.html): `set_user`, `AppAPIAuthMiddleware` (mit `disable_for`), `enabled_handler` ohne User-Kontext, Declarative Settings ab NC 29, `preferences_ex`. Confidence HIGH.
- MCP Python SDK (py.sdk.modelcontextprotocol.io/run/authorization/): `TokenVerifier`, `AuthSettings(issuer_url, resource_server_url, required_scopes)`, PRM-Endpoint + 401/WWW-Authenticate automatisch, `stateless_http=True`. Confidence HIGH.
- cbcoutinho/nextcloud-mcp-server (github.com): Multi-User via "OAuth am MCP-Layer + Login Flow v2 holt App-Passwort" bestaetigt das Bridge-Muster fuer die standalone-Topologie. Confidence HIGH (fuer das Muster).
- Consent-Bridge via AppAPI-Proxy-Route (User-ID aus Session-Headern): abgeleitet aus ExApp-UI-Mechanik, nicht per Ende-zu-Ende-Beispiel verifiziert. Confidence MEDIUM, Spike in Build-Stufe 4 einplanen.
- CalDAV/CardDAV mit AppAPI-Auth-Headern: nicht explizit dokumentiert. Confidence MEDIUM, Spike in Build-Stufe 3.

---
*Architecture research for: Nextcloud MCP-only ExApp*
*Researched: 2026-08-14*
