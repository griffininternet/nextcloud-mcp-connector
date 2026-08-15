# Phase 2: ExApp-Shell - Research

**Researched:** 2026-08-15
**Domain:** Nextcloud AppAPI ExApp (Lifecycle, Impersonation, HaRP/Proxy-Topologie) für einen MCP-Server
**Confidence:** HIGH (AppAPI-Kontrakt, Impersonation, Routen-/Zugriffsmodell, HaRP-Topologie: alles am Quellcode belegt), MEDIUM (empirisches Verhalten von DAV/Notes/Deck unter Impersonation, AIO-Detailablauf)

## Summary

Die drei Kernfragen der Phase sind beantwortbar und faktisch entschieden, bevor eine Zeile Code geschrieben wird.

**Erstens, D-24 (eigener Handshake statt nc_py_api):** Die AppAPI-Authentifizierung von Nextcloud zur ExApp besteht aus genau drei Headern und einem String-Vergleich. Die Referenzimplementierung (`nc_py_api._session.NcSessionApp.sign_check`) ist 17 Zeilen lang: `EX-APP-ID` muss der eigenen App-ID entsprechen, `AUTHORIZATION-APP-API` ist base64 von `userid:secret`, und `secret` muss gleich `APP_SECRET` aus der Umgebung sein. Der umgekehrte Weg (ExApp zu Nextcloud) setzt vier Header, davon drei konstant. Es gibt keine Signatur, keine Nonce, keinen Zeitstempel, kein Challenge-Response. Beide Deploy-Wege (HaRP-HAProxy und der PHP-Proxy) setzen exakt dieselben Header. **Empfehlung: selbst implementieren, nc_py_api nicht aufnehmen.** Der Aufwand liegt bei etwa 60 Zeilen inklusive Tests, die Alternative kostet FastAPI plus niquests plus Transitivballast in einem Projekt, das heute Starlette-only ist.

**Zweitens, AUTH-05 (Impersonation):** Impersonation ist kein Sonderweg für AppAPI-eigene Endpunkte, sondern im Nextcloud-Kern verankert. `OC::handleLogin()` ruft `tryAppAPILogin()` auf, das bei vorhandenem `AUTHORIZATION-APP-API`-Header `AppAPIService::validateExAppRequestToNC()` ausführt, und dieses setzt bei gültigem Secret per `IUserSession::setUser()` den aktiven Nutzer für den gesamten Request. Für WebDAV/CalDAV/CardDAV existiert zusätzlich ein eigener Sabre-Auth-Backend (`OCA\AppAPI\AppAPIAuthBackend` plus `OCA\AppAPI\DavPlugin`), der genau diesen Fall abdeckt. Der DAV-Spike startet damit nicht bei null, sondern muss eine dokumentierte Fähigkeit empirisch bestätigen. Jede Impersonation wird serverseitig in `data/exapp_impersonation.log` protokolliert.

**Drittens, AUTH-06 (Discovery unauthentifiziert von außen):** Go. ExApps deklarieren ihre extern erreichbaren Routen in `info.xml` mit einem `access_level` von `PUBLIC`, `USER` oder `ADMIN`. `PUBLIC` heißt wortwörtlich "public access without auth" und wird sowohl vom PHP-Proxy (`ExAppProxyController`, `#[PublicPage] #[NoCSRFRequired]`) als auch vom HaRP-Agenten ohne Nutzerkontext durchgelassen. In Nextcloud AIO leitet der mitgelieferte Caddy `/exapps/*` bereits ab Werk an HaRP weiter. Der AppAPI-Maintainer bestätigt öffentlich, dass genau der Anwendungsfall "MCP-Server als ExApp mit Streamable HTTP" über `https://<nc>/exapps/<appid>/...` durchstreamt. Die einzige echte Restlücke ist nicht die Erreichbarkeit, sondern der *kanonische Pfad* nach RFC 9728: `/.well-known/oauth-protected-resource/...` liegt auf der Domain-Wurzel und damit im Zuständigkeitsbereich von Nextcloud, nicht der ExApp. Der Spike muss deshalb den Weg über den `resource_metadata`-Parameter im `WWW-Authenticate`-Header (SEP-985-Priorität 1, im MCP-SDK 2.0 bereits so implementiert) belegen und die Reverse-Proxy-Regel als Fallback dokumentieren.

**Primary recommendation:** ExApp-Shell als vierten Betriebsmodus derselben Starlette-App bauen (drei `custom_route`-Handler plus eine Header-Prüfung, keine neue Dependency), extern über die HaRP-Route `/exapps/mcp_connector/mcp` erreichbar machen, in `info.xml` genau zwei eng gefasste Routen deklarieren (`^/mcp/?$` mit `USER` für Phase 2, `^/\.well-known/` mit `PUBLIC`), und die Identität ausschließlich aus `AUTHORIZATION-APP-API` ziehen.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**ExApp-Gerüst und Paketierung**

- **D-23:** Die ExApp ist ein dritter Betriebsmodus derselben Codebasis, kein neues Projekt: Die bestehende ASGI-App (entry_http.py, Starlette via mcp-SDK) wird um die AppAPI-Lifecycle-Endpunkte (/heartbeat, /init, /enabled) und die AppAPI-Auth-Prüfung erweitert. stdio und der eigenständige HTTP-Modus bleiben unverändert funktionsfähig (das Phase-1-Produkt bleibt nutzbar). [auto: empfohlene Option]
- **D-24:** Bevorzugt wird ein minimal selbst implementierter AppAPI-Kontrakt OHNE nc_py_api. Entscheidungsregel für den Researcher: Wenn die AppAPI-Handshake-/Signaturprüfung mit vertretbarem Aufwand (wenige, stabile Header-Checks laut offizieller AppAPI-Doku) selbst implementierbar ist, bleibt es dabei. Nur wenn die Prüfung nachweislich fragil oder undokumentiert ist, kommt nc_py_api als Dependency infrage; das wäre ein Package-Legitimacy-Gate (Owner) und bringt bekannten Ballast mit (01-RESEARCH.md Zeile 141: FastAPI + niquests + caldav). [auto]
- **D-25:** Container: eigenes schlankes Dockerfile (uv-basiert, non-root), kompatibel mit dem AppAPI Deploy Daemon (Docker-Socket-Variante) und HaRP. Image-Bau gehört in die CI, aber Registry-Publishing erst in Phase 5. [auto]

**Identitäts-Durchgriff (AUTH-05)**

- **D-26:** Eine einzige Client-Factory bleibt die Naht: NcClients/deps.resolve_clients bekommt einen vierten Credential-Modus "ExApp-Impersonation" (AppAPI-Headers mit Nutzerkontext). Tool-Code wird NICHT angefasst (das war das erklärte Design-Ziel aus Phase 1, 01-RESEARCH.md Zeile 701/760). [auto]
- **D-27:** Provider-Aufteilung je API-Familie ist explizit ERGEBNIS des DAV-Spikes, keine Vorab-Annahme: Wenn eine API-Familie (WebDAV/CalDAV/CardDAV) keine AppAPI-Impersonation kann, nutzt genau diese Familie weiterhin Nutzer-App-Passwörter, dokumentiert pro Familie. VERBOTEN bleibt ein admin-weites Shared-Token (Out of Scope seit PROJECT.md); stille Fallbacks sind verboten, jeder Modus-Wechsel ist im Log und in der Doku sichtbar. [auto]
- **D-28:** Permission-Parity-Beweis nutzt die zwei bestehenden Testkonten (alice, eingeschränkter Nutzer bob) aus Phase 1: bob sieht über MCP exakt das, was er in der Weboberfläche sieht, belegt über mindestens files/notes/unified_search (Muster aus tests/integration/test_permission_fidelity.py weiterverwenden). [auto]

**Spikes (Reihenfolge und Go/No-Go)**

- **D-29:** Der Discovery-Spike (AUTH-06) läuft ZUERST und als eigener früher Plan, weil er das Hauptrisiko ist und die OAuth-Topologie von Phase 3 entscheidet. Go-Kriterium: /.well-known/oauth-protected-resource (PRM, RFC 9728) und ein WWW-Authenticate-Header sind unauthentifiziert von AUSSEN erreichbar, auch über den AppAPI-Proxy-Pfad. No-Go-Fall: dokumentierte Fallback-Route (z.B. Route außerhalb des Proxys / eigene Subdomain / Admin-Reverse-Proxy-Regel) MUSS beschrieben und getestet sein, bevor Phase 3 startet. Ergebnis als eigenes Doc (docs/ oder .planning), nicht nur als SUMMARY-Absatz. [auto]
- **D-30:** Der DAV-Spike testet konkret: PROPFIND/REPORT/PUT unter AppAPI-Impersonation gegen die Test-NC; Ergebnisdoku enthält die Matrix API-Familie x Auth-Weg mit Beleg (HTTP-Status, Identität serverseitig verifiziert). [auto]

**Test-Infrastruktur**

- **D-31:** Primär compose-basiert: compose.test.yml wird um AppAPI + Deploy Daemon erweitert (oder ein zweites compose-File, wenn das Basis-Setup schlank bleiben soll, Entscheidung beim Planner). Nextcloud AIO ist der ZWEITE Smoke-Schritt (Success Criterion 1 nennt beide); wenn AIO lokal unverhältnismäßig ist, wird das als dokumentierter offener Punkt an Phase 5 übergeben statt still gestrichen. Loopback-Binding-Regel aus WR-06 gilt weiter (127.0.0.1). [auto]
- **D-32:** Alle Phase-1-Gates gelten unverändert (ruff verschärft, pyright 0 Fehler, vulture mit Whitelist, Token-Budget scharf, Testsuite grün ohne Docker; Integrationstests opt-in). [auto]

### Claude's Discretion

- Konkrete AppAPI-Header-Namen, Handshake-Details, interne Modulstruktur (z.B. exapp.py vs. server/exapp/), Testtiefe je Spike, compose-Layout.
- Reihenfolge der Pläne innerhalb der Phase, solange der Discovery-Spike früh liegt.

### Deferred Ideas (OUT OF SCOPE)

- MarkItDown-Konvertierung (TOOL-14, v2, Owner-Entscheidung 14.08.).
- "Accounts"-Systemadressbuch als opt-in Parameter (Produkt-/Datenschutzentscheidung, aus 01-08).
- 11 Info-Findings aus 01-REVIEW.md + UF-01..UF-05 aus 01-SECURITY.md (nicht-blockierende Qualitäts-/Prozesspunkte; Kandidaten für Hardening in Phase 5).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXAPP-01 | Admin kann die App als ExApp über AppAPI installieren (Container-Backend, Heartbeat/Init/enabled_handler, Deploy Daemon; HaRP-Smoke-Test vor Einreichung) | Lifecycle-Kontrakt exakt belegt (Abschnitt "AppAPI-Kontrakt"), Dockerfile-Anforderungen inkl. frpc/start.sh belegt, occ-Kommandos für unattended Setup belegt, Env-Variablen der Deploy-Phase aus `DockerActions::buildDeployEnvs` |
| AUTH-05 | Jede Nextcloud-Anfrage läuft unter der Identität des angemeldeten Nutzers | `OC::tryAppAPILogin` plus `AppAPIService::finalizeRequestToNC` (setUser) plus `AppAPIAuthBackend`/`DavPlugin` für Sabre; Impersonations-Matrix und Auth-Naht (`Credentials.auth()`) im Abschnitt "Pattern 3" |
| AUTH-06 | Discovery-Endpunkte unauthentifiziert erreichbar, auch durch den AppAPI-Proxy-Pfad | `ExAppRouteAccessLevel::PUBLIC = 0`, `passesExAppProxyRouteAccessLevelCheck`, HaRP-Agent `AccessLevel.PUBLIC`-Zweig, AIO-Caddy `/exapps/*`; Restrisiko RFC-9728-Wurzelpfad im Abschnitt "Discovery-Spike" |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Externe Erreichbarkeit des MCP-Endpunkts | HaRP (HAProxy vor Nextcloud) | Admin-Reverse-Proxy | HaRP terminiert `/exapps/*` und routet am PHP-Prozess vorbei; Streaming bleibt erhalten (Maintainer-Aussage app_api#825) |
| Zugriffsentscheidung public/user/admin je Route | AppAPI (Routen-Registry) | HaRP-Agent bzw. ExAppProxyController | `access_level` wird zentral in Nextcloud gehalten und an HaRP repliziert; die ExApp trifft diese Entscheidung nicht |
| Auflösung "welcher Nextcloud-Nutzer" | Nextcloud (Session/App-Passwort) | HaRP `/harp/user-info` | Nur Nextcloud kennt Sessions und App-Passwörter; HaRP fragt zurück und liefert der ExApp das Ergebnis als `AUTHORIZATION-APP-API` |
| Identitätsnachweis ExApp zu Nextcloud | ExApp (4 Header) | - | Shared Secret aus `APP_SECRET`, Nutzer-Id im selben Header |
| Berechtigungsdurchsetzung (ACLs) | Nextcloud-Kern | - | Nach `setUser()` greifen alle serverseitigen Prüfungen unverändert; die ExApp filtert nichts nach |
| ExApp-Lifecycle (heartbeat/init/enabled) | ExApp (HTTP-Handler) | AppAPI (Aufrufer, Timeouts) | Kontrakt ist fest, die ExApp ist reiner Responder |
| Container-Deployment und Volume | Deploy Daemon (HaRP/Docker) | - | Image-Pull, Env-Injection, Persistent Volume `nc_app_<appid>_data` |
| Brute-Force-Schutz auf ExApp-Routen | HaRP bzw. Nextcloud-Throttler | ExApp (eigene Limits) | Pro Route konfigurierbar über `bruteforce_protection`; die Doku weist die Restverantwortung explizit der ExApp zu |
| TLS-Terminierung | Admin-Reverse-Proxy | HaRP (optionales HTTPS-Frontend) | Die ExApp spricht intern HTTP bzw. Unix-Socket |

## Standard Stack

### Core

Diese Phase führt **keine neue Laufzeit-Abhängigkeit** ein. Alles Nötige ist bereits im Projekt.

| Library | Version (installiert) | Purpose | Why Standard |
|---------|----------------------|---------|--------------|
| mcp | 2.0.x | `MCPServer.custom_route` für `/heartbeat`, `/init`, `/enabled`; `streamable_http_app()` als Basis-ASGI-App | Bereits Phase-1-Kern; `custom_route` ist der dokumentierte Weg für nicht-MCP-Routen und läuft bewusst ohne Auth-Layer [VERIFIED: src/mcp_connector/entry_http.py, `/health` nutzt es bereits] |
| starlette (transitiv) | via mcp | Request/Response, Routing | Kommt mit dem SDK, kein FastAPI nötig |
| httpx | 0.28.1 | Ausgehende Calls zu Nextcloud inkl. neuem `httpx.Auth`-Subclass für AppAPI-Header | `httpx.Auth` ist die vorgesehene Erweiterungsstelle; die 20 Aufrufstellen ändern sich mechanisch von `httpx.BasicAuth(...)` auf `creds.auth()` [VERIFIED: grep über src/mcp_connector/nextcloud/clients] |
| uvicorn (transitiv) | >=0.31 | Server im Container, inkl. Unix-Socket-Modus für HaRP/FRP | `uvicorn.run(..., uds=...)` ist Standard; nc_py_api macht nichts anderes [VERIFIED: nc_py_api/ex_app/uvicorn_fastapi.py] |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| frpc (FRP-Client-Binary) | 0.61.1 | Tunnel Unix-Socket zu HaRP, wenn `HP_SHARED_KEY` gesetzt ist | Nur im Container-Image; kein Python-Paket, sondern ein Binary aus dem offiziellen FRP-Release mit SHA256-Prüfung [CITED: github.com/nextcloud/HaRP README, Abschnitt "Adapting ExApps to use HaRP"] |
| `start.sh` aus HaRP `exapps_dev/` | main | Erzeugt `frpc.toml`, startet frpc, dann `exec "$@"` | Wortwörtlich übernehmen statt nachbauen; HaRP-Doku verlangt genau das |
| Caddy (Test-Setup) | 2.x Image | Reverse-Proxy vor der Test-Nextcloud, routet `/exapps/*` zu HaRP | Bildet die AIO-Topologie 1:1 nach, ohne die es keinen HaRP-Test gibt |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Eigener 60-Zeilen-Handshake | `nc_py_api[app]` | Bringt FastAPI, niquests, pydantic-settings und einen eigenen Session-Layer mit; das Projekt ist heute Starlette-only. Der einzige echte Mehrwert (Declarative Settings) wird erst in Phase 4 gebraucht und ist eine reine OCS-Registrierung, ebenfalls selbst machbar. **Nicht nehmen** (D-24 bestätigt). |
| HaRP-Route `/exapps/<appid>/mcp` | PHP-Proxy `/apps/app_api/proxy/<appid>/mcp` | Der PHP-Proxy läuft durch den PHP-Prozess, puffert potenziell (`ProxyResponse` streamt zwar via `fpassthru`, aber die gesamte Nextcloud-Response-Pipeline hängt dran), erlaubt nur GET/POST/PUT/DELETE und tauscht bei DSP-Daemons den `Authorization`-Header gegen `X-Original-Authorization`. Als Zweitpfad testen, nicht als Default dokumentieren. |
| Container-Deploy für den Dev-Loop | `manual-install`-Daemon plus lokaler uvicorn | Für die Entwicklung klar besser (kein Image-Rebuild pro Iteration), für den Abnahmetest ungeeignet. Beides einrichten. |
| Eigenes `/init` | Kein `/init` (404) | AppAPI setzt bei 404/501 den Init-Fortschritt automatisch auf 100. Funktioniert, verlässt sich aber auf Exception-Codes im Guzzle-Pfad. Sauberer: `/init` implementieren, 200 antworten und sofort `progress=100` per OCS melden. |

**Installation:** keine. `uv sync` unverändert.

**Version verification (durchgeführt 2026-08-15):**
- AppAPI stabil für NC 34: Tags `v34.0.3` (zuletzt), `main` trägt `35.0.0-dev.1`. AppAPI folgt seit v34 der Nextcloud-Hauptversion, die alte 3.x-Zählung ist Geschichte. [VERIFIED: `gh api repos/nextcloud/app_api/tags`, `appinfo/info.xml`]
- AppAPI ist **nicht** im Server-Tarball enthalten (`nextcloud/server/apps` führt es nicht), muss also im Test per `occ app:install app_api` aus dem App Store geholt werden (Internetzugang nötig). [VERIFIED: `gh api repos/nextcloud/server/contents/apps`]

## Package Legitimacy Audit

Diese Phase installiert **keine** neuen Python-Pakete. Der Legitimacy-Gate ist damit gegenstandslos, wird hier aber für die eine Alternative dokumentiert, die der Planner sonst versehentlich aufnehmen könnte.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| nc_py_api | PyPI | seit 2023 | etabliert (offizielles Nextcloud-nahes Projekt, cloud-py-api) | github.com/cloud-py-api/nc_py_api | nicht ausgeführt (Paket wird nicht aufgenommen) | ABGELEHNT per D-24, Beleg siehe "Antwort auf D-24" |
| frpc (Binary, kein Paket) | GitHub Release fatedier/frp v0.61.1 | seit 2017 | sehr hoch | github.com/fatedier/frp | n/a (kein Registry-Paket) | Aufgenommen mit SHA256-Pin aus der HaRP-Doku |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Wenn der Planner entgegen D-24 doch nc_py_api aufnehmen will, ist das ein Owner-Gate plus `checkpoint:human-verify`, nicht eine Executor-Entscheidung.

## Der AppAPI-Kontrakt, konkret und aktuell (Stand NC 34 / AppAPI 34.x)

### Eingehend: Nextcloud (oder HaRP) ruft die ExApp

Header, die auf jedem Request von AppAPI an die ExApp stehen:

| Header | Wert | Quelle |
|--------|------|--------|
| `AA-VERSION` | AppAPI-Version, z.B. `34.0.3`; HaRP setzt hart `32` | `AppAPICommonService::buildAppAPIAuthHeaders`, `haproxy.cfg.template` |
| `EX-APP-ID` | die App-ID, hier `mcp_connector` | dito |
| `EX-APP-VERSION` | Version aus der ExApp-Registrierung | dito |
| `AUTHORIZATION-APP-API` | `base64(userid + ":" + app_secret)`; `userid` ist leer bei anonymen bzw. systeminternen Aufrufen | dito |
| `AA-REQUEST-ID` | Request-Id von Nextcloud, `CLI` bei occ-Aufrufen; nur PHP-Pfad, HaRP setzt ihn nicht | `buildAppAPIAuthHeaders` |
| `harp-shared-key`, `ex-app-host`, `ex-app-port` | nur wenn der Daemon HaRP ist, und nur auf dem PHP-zu-HaRP-Hop | `buildAppAPIAuthHeaders` |
| `x-origin-ip` | nur der PHP-Proxy setzt ihn (Client-IP für Rate-Limiting) | `ExAppProxyController::buildHeadersWithExclude` |

Die Prüfung in der ExApp ist genau das (Referenz `nc_py_api._session.NcSessionApp.sign_check`):

1. `EX-APP-ID`, `EX-APP-VERSION`, `AUTHORIZATION-APP-API` müssen alle drei vorhanden und nicht leer sein.
2. `EX-APP-ID` muss der eigenen App-ID entsprechen.
3. `base64decode(AUTHORIZATION-APP-API)` in `username` und `app_secret` zerlegen (`split(":", maxsplit=1)`).
4. `app_secret` muss `APP_SECRET` aus der Umgebung entsprechen.
5. Rückgabewert ist `username`, also der zu imitierende Nutzer (leer = kein Nutzerkontext).

`AA-VERSION` wird von nc_py_api **nicht** geprüft. Das ist konsistent damit, dass HaRP dort hart `32` hineinschreibt.

**Wichtig:** `/heartbeat` darf keine Auth verlangen. Die Doku sagt das explizit, und nc_py_api nimmt `heartbeat` zwangsweise aus der Middleware heraus. Gleichzeitig *sendet* AppAPI bei HaRP-Daemons sehr wohl Auth-Header an `/heartbeat` (`heartbeatExApp` merged `buildAppAPIAuthHeaders` hinein, wenn `deployConfig['harp']` gesetzt ist). Der Handler muss also beides vertragen: mit und ohne Header.

### Ausgehend: die ExApp ruft Nextcloud

Vier Header, drei davon konstant pro Prozess:

```
AA-VERSION: <AA_VERSION aus der Umgebung>
EX-APP-ID: <APP_ID>
EX-APP-VERSION: <APP_VERSION>
AUTHORIZATION-APP-API: base64("<nextcloud-user-id>:<APP_SECRET>")
```

Nextcloud validiert in `AppAPIService::validateExAppRequestToNC()`: ExApp existiert, ist enabled, Secret stimmt, Nutzer existiert. Danach `finalizeRequestToNC()` mit `IUserSession::setUser($activeUser)` plus `session->set('app_api', true)` (letzteres hebt CORS-Prüfung und Zwei-Faktor auf) und einem Eintrag in `data/exapp_impersonation.log`. Bei leerer Nutzer-Id: `setUser(null)`, also App-Kontext ohne Nutzer.

Aufgerufen wird das an zwei Stellen:

- **Kern-Login-Pfad:** `OC::handleLogin()` ruft `OC::tryAppAPILogin($request)` auf. Damit greift Impersonation grundsätzlich für alle Requests, die durch den normalen Login-Pfad laufen (`index.php`-App-Routen, `ocs/v2.php`). [VERIFIED: nextcloud/server `lib/OC.php`]
- **AppFramework-Middleware:** `AppAPIAuthMiddleware` prüft zusätzlich, aber **nur** wenn die Ziel-Methode das Attribut `#[AppAPIAuth]` trägt. Das haben ausschließlich AppAPI-eigene Controller. Diese Middleware ist also *nicht* der Weg, über den Notes oder Deck erreichbar werden.
- **Sabre/DAV:** `DavPlugin::beforeMethod` (Priorität 8, also vor der Sabre-Auth) ruft `validateExAppRequestToNC($request, isDav: true)` und setzt `Auth::DAV_AUTHENTICATED`; `AppAPIAuthBackend::check()` akzeptiert dann, wenn Session-`user_id` und Header-Nutzer übereinstimmen. Registriert wird das über `SabrePluginAuthInitEvent` und `SabrePluginAddEvent`, also für den `remote.php/dav`-Server, unter dem Files, CalDAV und CardDAV gemeinsam hängen.

### Lifecycle

| Schritt | Methode | Erwartung | Timeout |
|---------|---------|-----------|---------|
| 0 | Docker `HEALTHCHECK` | Container gesund | 15 min |
| 1 | `GET /heartbeat` | HTTP 200 | 10 min (60*10 Versuche im Sekundentakt); Test-Deploy-App: 1 min |
| 2 | `POST /init` | HTTP 200, danach Fortschritt bis 100 per OCS; bei 404 oder 501 setzt AppAPI selbst 100 | init_timeout default 40 min (`occ config:app:set app_api init_timeout`) |
| 3 | `PUT /enabled?enabled=1` bzw. `=0` | HTTP 200, JSON ohne nicht-leeres `error`-Feld | 60 s im Code (die Doku nennt 30 s) |

Fortschritt melden: `PUT /ocs/v2.php/apps/app_api/ex-app/status` mit `{"progress": <int>}`, mit den vier ausgehenden Headern und `OCS-APIRequest: true`.
Enabled-Zustand abfragen: `GET /ocs/v2.php/apps/app_api/ex-app/state`.

Beide Endpunkte sind explizit von der "ExApp muss enabled sein"-Prüfung ausgenommen, solange die Installation läuft (`isExemptFromEnabledCheck`).

### Routen-Deklaration (seit AppAPI 3.0.0 verpflichtend für den Proxy)

```xml
<external-app>
    <docker-install>
        <registry>ghcr.io</registry>
        <image>street1983nk/nextcloud-mcp-connector</image>
        <image-tag>0.2.0</image-tag>
    </docker-install>
    <routes>
        <route>
            <url>^/mcp/?$</url>
            <verb>GET,POST,DELETE</verb>
            <access_level>USER</access_level>
            <headers_to_exclude>[]</headers_to_exclude>
        </route>
        <route>
            <url>^/\.well-known/</url>
            <verb>GET</verb>
            <access_level>PUBLIC</access_level>
            <headers_to_exclude>[]</headers_to_exclude>
        </route>
    </routes>
</external-app>
```

Feldsemantik (aus `ExAppRouteHelper` und der Doku):

- `url`: Regex, wird gegen den Pfad **inklusive führendem Slash und ohne** `/exapps/<appid>` bzw. `/apps/app_api/proxy/<appid>` gematcht. Der PHP-Proxy hat noch einen "bare path"-Fallback für Altbestand (context_agent schreibt `mcp` ohne Slash), der laut Quellcode-TODO verschwinden soll. Kanonisch ist `^/pfad$`.
- `verb`: Kommaliste; Match ist `str_contains(strtolower(verb), strtolower(method))`. Achtung, das ist ein Substring-Vergleich: `GET` matcht innerhalb von `GET,POST`, aber auch die Methode `GET` gegen einen Eintrag `TARGET`. Praktisch unkritisch, aber kein exakter Vergleich.
- `access_level`: `PUBLIC` (0), `USER` (1), `ADMIN` (2). Als String oder als Zahl erlaubt.
- `headers_to_exclude`: JSON-Array-String, z.B. `["cookie"]`. `authorization-app-api`, `x-origin-ip` und `content-length` werden immer entfernt bzw. neu gesetzt.
- `bruteforce_protection`: JSON-Array-String von HTTP-Statuscodes, die den Throttler triggern.

Erster Treffer nach Pfad **und** Verb gewinnt, danach entscheidet dessen `access_level` allein. Kein Treffer bedeutet 404.

## Architecture Patterns

### System Architecture Diagram

```
                      MCP-Client (Claude.ai / Cursor / MUCGPT)
                                   |
                                   | HTTPS, Streamable HTTP
                                   v
                   Admin-Reverse-Proxy (nginx/Caddy/Apache/AIO-Caddy)
                       |                                   |
     /exapps/*  -------+                                   +------- alles andere
        |                                                             |
        v                                                             v
   HaRP (HAProxy + SPOE-Agent, Port 8780)                     Nextcloud (PHP)
        |   1. Pfad -> appid + target_path                     |  /apps/app_api/proxy/<appid>/<pfad>
        |   2. Route-Regex + access_level prüfen              |     (Zweitweg, PublicPage-Controller)
        |      PUBLIC -> durch; USER -> /harp/user-info -------+---> Session/App-Passwort auflösen
        |   3. Header setzen:                                  |
        |      EX-APP-ID / EX-APP-VERSION / AA-VERSION         |     requestToExApp2 setzt dieselben
        |      AUTHORIZATION-APP-API = b64(user:secret)        |     Header und hängt x-origin-ip an
        |   4. Pfadpräfix strippen                            |
        v                                                      v
   +---------------------------------------------------------------------------+
   |  ExApp-Container (ein uvicorn-Prozess, Starlette-App aus dem MCP-SDK)      |
   |                                                                           |
   |  /heartbeat  /init  /enabled     <- custom_route, ohne MCP-Auth-Layer     |
   |  /mcp                            <- streamable_http_app (Phase-1-Kern)    |
   |  /.well-known/...                <- PRM (Phase 3), heute nur Spike-Stub   |
   |                                                                           |
   |  exapp/auth.py: 3 Header prüfen -> nextcloud_user_id                     |
   |             |                                                             |
   |             v                                                             |
   |  deps.resolve_clients(ctx) -> NcClients(client, Credentials(mode=EXAPP))  |
   |             |                                                             |
   |  tools/ unverändert (kennt nur NcClients)                                |
   +---------------------------------------------------------------------------+
                                   |
                                   | httpx, 4 AppAPI-Header statt BasicAuth
                                   v
                     Nextcloud: remote.php/dav | ocs/v2.php | index.php/apps/*
                     OC::tryAppAPILogin -> setUser(user) -> ACLs greifen serverseitig
                     Protokoll: data/exapp_impersonation.log
```

Drei Dinge, die dieses Bild festlegt:

1. Es gibt genau **zwei** externe Eingangswege in die ExApp (HaRP `/exapps/...`, PHP-Proxy `/apps/app_api/proxy/...`) und beide liefern dieselben vier Header. Die App muss die Wege nicht unterscheiden, außer für die Absicherung der Lifecycle-Endpunkte (siehe Pitfall 4).
2. Der Pfadpräfix ist in beiden Fällen entfernt, bevor die App den Request sieht. Die App kann ihre eigene öffentliche URL **nicht** aus dem Request ableiten. Sie braucht `NC_MCP_PUBLIC_URL` (existiert bereits in `config.py`) als Konfiguration.
3. Die Identität kommt aus genau einem Header. Damit bleibt die Phase-1-Invariante ("die Identität fließt genau einen Weg, kein Tool-Parameter") unverändert gültig.

### Recommended Project Structure

```
src/mcp_connector/
├── entry_http.py           # unverändert nutzbar; ExApp-Routen kommen über exapp/ dazu
├── entry_exapp.py          # NEU: ASGI-App + uvicorn-Start (uds vs. host/port)
├── config.py               # ERWEITERT: exapp_config() liest APP_ID/APP_SECRET/... ; select_mode kennt "exapp"
├── deps.py                 # ERWEITERT: vierter Zweig in resolve_credentials
├── exapp/                  # NEU, komplett neuer Code, kein Tool-Code berührt
│   ├── __init__.py
│   ├── auth.py             # verify_appapi_headers() -> user_id ; AppApiAuth(httpx.Auth)
│   ├── lifecycle.py        # /heartbeat, /init, /enabled als custom_route
│   └── status.py           # PUT /ocs/v2.php/apps/app_api/ex-app/status (Init-Fortschritt)
└── nextcloud/
    ├── credentials.py      # ERWEITERT: Credentials.auth() -> httpx.Auth
    └── clients/*.py        # 20 Zeilen mechanisch: httpx.BasicAuth(...) -> creds.auth()

appinfo/info.xml            # NEU: ExApp-Metadaten inkl. <routes>
Dockerfile                  # NEU: uv-basiert, non-root, frpc, start.sh
start.sh                    # NEU: 1:1 aus HaRP exapps_dev/
compose.exapp.yml           # NEU: nextcloud + caddy + harp (D-31)
scripts/bootstrap_exapp.sh  # NEU: occ app:install app_api, daemon:register, app:register
```

### Pattern 1: AppAPI-Handshake, selbst implementiert

**What:** Eine Funktion, die aus den drei Headern eine Nextcloud-Nutzer-Id macht oder scheitert.
**When to use:** In einer Starlette-Middleware bzw. am Anfang jedes ExApp-Requests.

```python
# exapp/auth.py
import base64
import binascii
import secrets

class AppApiRejected(Exception):
    """Kein gültiger AppAPI-Request. Antwort ist immer 401, nie ein Detail."""

def verify_appapi_headers(headers, app_id: str, app_secret: str) -> str:
    """Return the Nextcloud user id this request runs as ("" = app context, no user).

    Spiegelt nc_py_api._session.NcSessionApp.sign_check, mit zwei Verschärfungen:
    constant-time Secret-Vergleich (Projektregel aus deps.StaticBearerVerifier) und
    keinerlei Echo des empfangenen Wertes in Logs oder Fehlertexten.
    """
    ex_app_id = headers.get("ex-app-id", "")
    ex_app_version = headers.get("ex-app-version", "")
    raw_auth = headers.get("authorization-app-api", "")
    if not ex_app_id or not ex_app_version or not raw_auth:
        raise AppApiRejected
    if not secrets.compare_digest(ex_app_id.encode("utf-8"), app_id.encode("utf-8")):
        raise AppApiRejected
    try:
        decoded = base64.b64decode(raw_auth, validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise AppApiRejected from None
    user, separator, secret = decoded.partition(":")
    if not separator:
        raise AppApiRejected
    if not secrets.compare_digest(secret.encode("utf-8"), app_secret.encode("utf-8")):
        raise AppApiRejected
    return user
```

Referenz (identische Semantik, ohne constant-time):

```python
# nc_py_api/_session.py, sign_check()  [VERIFIED: raw.githubusercontent.com/cloud-py-api/nc_py_api/main/nc_py_api/_session.py]
headers = {"EX-APP-ID": ..., "EX-APP-VERSION": ..., "AUTHORIZATION-APP-API": ...}
empty_headers = [k for k, v in headers.items() if not v]
if empty_headers: raise ValueError(...)
if headers["EX-APP-ID"] != self.cfg.app_name: raise ValueError(...)
username, app_secret = get_username_secret_from_headers(headers)
if app_secret != self.cfg.app_secret: raise ValueError(...)
return username
```

### Pattern 2: Lifecycle-Endpunkte als `custom_route`

**What:** Drei Handler auf der bestehenden MCP-Starlette-App, analog zu `/health`.
**Why:** `custom_route` ist bewusst außerhalb des SDK-Auth-Layers (steht schon so im Docstring von `entry_http.py`). Genau das braucht `/heartbeat`.

```python
@mcp.custom_route("/heartbeat", methods=["GET"])
async def heartbeat(request: Request) -> JSONResponse:
    # Ohne Auth, per Doku-Vorgabe. AppAPI sendet bei HaRP-Daemons trotzdem Header mit;
    # die werden hier absichtlich ignoriert.
    return JSONResponse({"status": "ok"})

@mcp.custom_route("/init", methods=["POST"])
async def init(request: Request) -> JSONResponse:
    require_appapi(request)          # 401 ohne gültige Header
    await report_init_progress(100)  # PUT /ocs/v2.php/apps/app_api/ex-app/status
    return JSONResponse({})

@mcp.custom_route("/enabled", methods=["PUT"])
async def enabled(request: Request) -> JSONResponse:
    require_appapi(request)
    # enabled=1|0 als Query-Parameter. Kein Nutzerkontext an dieser Stelle.
    return JSONResponse({"error": ""})
```

`/enabled` muss `{"error": ""}` oder ein JSON ohne nicht-leeres `error` liefern, sonst deaktiviert AppAPI die App sofort wieder (`enableExApp` prüft `json_decode($body)['error']`).

### Pattern 3: Der vierte Credential-Modus als `httpx.Auth`

**What:** `Credentials` bekommt eine Methode, die das passende `httpx.Auth`-Objekt liefert. Der Tool-Code bleibt unberührt, die Client-Module ändern sich nur an der Zeile, an der heute `httpx.BasicAuth` steht.

```python
# nextcloud/credentials.py
@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    base_url: str
    user: str
    secret: str          # App-Passwort ODER APP_SECRET, je nach mode
    mode: str = "basic"  # "basic" | "appapi"
    app_id: str = ""
    app_version: str = ""
    aa_version: str = ""

    def auth(self) -> httpx.Auth:
        if self.mode == "appapi":
            return AppApiAuth(self)
        return httpx.BasicAuth(self.user, self.secret)

    def __repr__(self) -> str:
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, mode={self.mode!r}, secret='***')"


class AppApiAuth(httpx.Auth):
    """Setzt die vier AppAPI-Header pro Request. Kein Retry, kein State."""

    def __init__(self, creds: Credentials) -> None:
        token = base64.b64encode(f"{creds.user}:{creds.secret}".encode()).decode()
        self._headers = {
            "AA-VERSION": creds.aa_version,
            "EX-APP-ID": creds.app_id,
            "EX-APP-VERSION": creds.app_version,
            "AUTHORIZATION-APP-API": token,
        }

    def auth_flow(self, request: httpx.Request):
        request.headers.update(self._headers)
        yield request
```

**Aufrufstellen:** `auth=httpx.BasicAuth(creds.user, creds.secret)` wird zu `auth=creds.auth()`. Betroffen sind 20 Stellen in `clients/{dav,caldav,carddav,notes,deck,ocs}.py` (Stand heute, per grep). Keine Logikänderung, kein Tool-Code, kein Test-Contract.

**Warnung:** `repr` maskiert weiterhin; `AppApiAuth` darf keinen `__repr__` erben, der das Token zeigt. Das Base64-Token enthält das Shared Secret im Klartext.

### Pattern 4: Start ohne nc_py_api

```python
# entry_exapp.py
def main() -> None:
    if os.environ.get("HP_SHARED_KEY"):
        # HaRP mit FRP-Tunnel: der Socket ist der Transport, frpc läuft im selben Container.
        uvicorn.run(app, uds=os.environ.get("HP_EXAPP_SOCK", "/tmp/exapp.sock"))
    else:
        uvicorn.run(app, host=os.environ.get("APP_HOST", "127.0.0.1"), port=int(os.environ["APP_PORT"]))
```

Das ist zeilengleich mit `nc_py_api.ex_app.run_app` [VERIFIED: nc_py_api/ex_app/uvicorn_fastapi.py]. `APP_HOST` ist bei Docker-Netzen ungleich `host` der Wert `0.0.0.0`, bei `net=host` `127.0.0.1` (`AppAPICommonService::buildExAppHost`).

### Pattern 5: Dockerfile

Anforderungen aus der HaRP-Doku, wortwörtlich:

1. `start.sh` aus `exapps_dev/` des HaRP-Repos kopieren, `ENTRYPOINT ["/start.sh", <startbefehl>]`.
2. `curl` im Image haben.
3. frpc 0.61.1 mit SHA256-Verifikation installieren (amd64 `bff260b6...`, arm64 `af6366f2...`; Alpine 3.21 alternativ `apk add frp`).
4. `HEALTHCHECK` setzen. AppAPI wertet ihn aus; ein Container ohne Healthcheck gilt als gesund.

Kein Label, kein fester Port: der Port kommt zur Laufzeit als `APP_PORT`. `EXPOSE` ist damit informativ. Multi-Arch (amd64 + arm64) baut die CI; Publishing erst Phase 5 (D-25).

### Anti-Patterns to Avoid

- **`<url>.*</url>` mit `access_level` PUBLIC.** Der PHP-Proxy schützt `/heartbeat`, `/init`, `/enabled` **nicht** und hängt selbst gültige AppAPI-Header an. Eine `.*`-Route macht damit `PUT /apps/app_api/proxy/mcp_connector/enabled?enabled=0` für jeden aus dem Internet erreichbar. HaRP blockt diese drei Pfade explizit ("Only requests from AppAPI allowed to the internal endpoints"), der PHP-Proxy nicht. Immer eng deklarieren.
- **`bruteforce_protection` mit `401` auf der MCP-Route.** Der OAuth-Discovery-Flow *beginnt* per Spezifikation mit einem 401. Ein 401-Trigger sperrt damit legitime Erstverbindungen aus.
- **Die eigene öffentliche URL aus dem Request ableiten.** Präfix ist gestrippt, `Host` ist der des Reverse-Proxys, `X-Forwarded-Prefix` gibt es nicht. Konfiguration statt Heuristik.
- **Basic-Header und AppAPI-Header gleichzeitig akzeptieren.** Der Client kann im ExApp-Modus einen `Authorization`-Header mitschicken (HaRP reicht ihn durch). Im ExApp-Modus zählt ausschließlich `AUTHORIZATION-APP-API`. Alles andere ist der stille Fallback, den D-27 verbietet.
- **`nc_py_api` "nur für den Handshake" aufnehmen.** Es zieht FastAPI und niquests mit; das Projekt hat heute weder das eine noch das andere.
- **Impersonation ohne Nutzer.** Ein leerer Nutzer in `AUTHORIZATION-APP-API` bedeutet App-Kontext ohne Nutzer. Für Datenzugriffe ist das zu verbieten, nicht zu tolerieren (Kernversprechen des Projekts).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Nutzer aus Session/App-Passwort auflösen | Eigene Session-Prüfung gegen Nextcloud | `access_level=USER` in `info.xml` deklarieren | HaRP fragt `/harp/user-info` selbst ab (inkl. App-Passwort und Basic Auth) und liefert das Ergebnis als `AUTHORIZATION-APP-API`; ein Nachbau wäre ein zweiter Auth-Pfad |
| Zugriffsschutz auf ExApp-Routen | Eigene Middleware mit Allowlist | `access_level` je Route | Die Entscheidung fällt vor der ExApp, spart einen kompletten Request-Roundtrip und ist admin-sichtbar |
| Brute-Force-Schutz auf öffentlichen Routen | Eigener Zähler | `bruteforce_protection` je Route | Nutzt den Nextcloud-Throttler bzw. HaRPs Blacklist inkl. IP-Ermittlung hinter Reverse-Proxies |
| FRP-Tunnel-Konfiguration | Eigenes Startskript | `start.sh` aus HaRP `exapps_dev/` | Die Datei ist der veröffentlichte Vertrag, inkl. TLS-Zertifikatspfaden, die AppAPI zur Installationszeit in den Container legt |
| Zertifikate für Self-Signed-Nextcloud im Container | Eigene CA-Bundle-Logik | AppAPI `docker_exapp_install_certificates` | HaRP/AppAPI installieren System-Zertifikate beim Deploy in den Container |
| Init-Fortschritt | Eigener Statusspeicher | `PUT /ocs/v2.php/apps/app_api/ex-app/status` | Der Admin sieht den Fortschritt in der ExApp-Verwaltung; ohne diesen Call bleibt die App auf 0 stehen |
| Persistente Daten | Eigenes Volume-Handling | `APP_PERSISTENT_STORAGE` | AppAPI legt `nc_app_<appid>_data` an und mountet es; Updates behalten es |

**Key insight:** AppAPI ist kein dünner Reverse-Proxy, sondern ein Policy-Layer mit Registry. Alles, was mit "wer darf diese Route aufrufen" zu tun hat, gehört in `info.xml`, nicht in Python. Die ExApp bleibt dadurch ein reiner Responder, und der Admin sieht die Policy an einer Stelle.

## Common Pitfalls

### Pitfall 1: Der kanonische RFC-9728-Pfad liegt außerhalb der ExApp
**What goes wrong:** Für die Resource `https://cloud.example.com/exapps/mcp_connector/mcp` lautet die kanonische Metadaten-URL `https://cloud.example.com/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp`. Dieser Pfad liegt auf der Domain-Wurzel und wird von Nextcloud beantwortet, nicht von HaRP. Ergebnis: 404 vom falschen Zuständigen.
**Why it happens:** RFC 9728 §3.1 schiebt `/.well-known/oauth-protected-resource` zwischen Host und Pfad, statt es an den Pfad anzuhängen. Das MCP-SDK registriert seine Route genau so (`build_resource_metadata_url`), aber innerhalb der eigenen App, wo sie hinter dem gestrippten Präfix landet.
**How to avoid:** Drei Wege, in dieser Reihenfolge testen: (a) `WWW-Authenticate: Bearer resource_metadata="https://cloud.example.com/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"` - das ist Priorität 1 in `build_protected_resource_metadata_discovery_urls` des SDK-Clients (SEP-985) und damit spezifikationskonform; (b) Reverse-Proxy-Regel des Admins, die den Wurzelpfad auf die ExApp mappt (dokumentierte Zusatzkonfiguration); (c) eigene Subdomain bzw. der eigenständige HTTP-Modus aus Phase 1.
**Warning signs:** Client meldet "could not discover authorization server", obwohl `/mcp` einen 401 mit korrektem Header liefert.

### Pitfall 2: `x-origin-ip` verrät den Weg, aber nur den PHP-Weg
**What goes wrong:** Man will Lifecycle-Endpunkte gegen externe Aufrufe absichern und sucht ein Unterscheidungsmerkmal.
**Why it happens:** Nur `ExAppProxyController::buildHeadersWithExclude` setzt `x-origin-ip` (und entfernt vorher einen mitgeschickten). HaRP setzt ihn nicht.
**How to avoid:** Primärschutz ist die enge Routen-Deklaration (kein Treffer bedeutet 404). `x-origin-ip` nur als Defense-in-Depth verwenden: liegt der Header an, kam der Request durch den PHP-Proxy, und dann darf `/enabled` nicht bedient werden.
**Warning signs:** `/enabled` lässt sich von außen aufrufen, sobald man versuchsweise eine breite Route deklariert.

### Pitfall 3: `POST /init` mit 200 und ohne Fortschrittsmeldung
**What goes wrong:** Die App bleibt dauerhaft bei "Initialisierung 0 Prozent", `/enabled` wird nie gerufen.
**Why it happens:** `dispatchExAppInitInternal` setzt Fortschritt 100 nur, wenn der Aufruf mit Statuscode 404 oder 501 eine Exception wirft. Ein 200 ohne nachfolgenden Status-Push lässt die App hängen.
**How to avoid:** Entweder `/init` gar nicht implementieren (Starlette antwortet 404, AppAPI setzt selbst 100), oder 200 antworten und sofort `progress=100` per OCS melden. Empfehlung: Zweites, weil es zugleich den ausgehenden AppAPI-Auth-Pfad beim Deploy verifiziert.
**Warning signs:** `occ app_api:app:list` zeigt die App als registriert, aber nicht enabled; `occ app_api:app:register` hängt bis zum init_timeout.

### Pitfall 4: Der PHP-Proxy cached JSON-Antworten eine Stunde
**What goes wrong:** Discovery-Antworten oder MCP-Antworten werden vom Browser bzw. Client eine Stunde lang gecacht.
**Why it happens:** `createProxyResponse` ruft `cacheFor(3600)`, wenn kein `Cache-Control` gesetzt ist und der Content-Type **exakt** `application/json` ist. Ein `application/json; charset=utf-8` fällt aus der Ausnahme heraus und wird gecacht.
**How to avoid:** Auf allen ExApp-Antworten explizit `Cache-Control: no-store` setzen. Das schaltet die Proxy-Cache-Logik ab.
**Warning signs:** Geänderte Metadaten schlagen erst nach einer Stunde durch; ein widerrufenes Token wirkt scheinbar nicht.

### Pitfall 5: Der `Authorization`-Header überlebt den DSP-Weg nicht unverändert
**What goes wrong:** Ein Bearer-Token kommt in der ExApp nicht an.
**Why it happens:** `AppAPIService::swapAuthorizationHeader` verschiebt `Authorization` nach `X-Original-Authorization`, sobald der Deploy-Daemon HAProxy-Basic-Auth verwendet (Docker Socket Proxy mit `haproxy_password`). Das ist explizit dokumentiert ("This is required for AppAPI Docker Socket Proxy, as the Basic Auth is already in use by HaProxy").
**How to avoid:** Für Phase 2 irrelevant, wenn die Identität ausschließlich aus `AUTHORIZATION-APP-API` kommt. Für Phase 3 (Bearer) muss der Reader beide Header kennen. DSP ist ohnehin deprecated (Entfernung in NC 35), HaRP ist der Zielpfad.
**Warning signs:** Funktioniert mit HaRP, scheitert mit DSP.

### Pitfall 6: HaRP fragt bei jedem Request mit `Authorization` bei Nextcloud nach
**What goes wrong:** Latenz pro MCP-Call steigt, und ein 5xx aus `/harp/user-info` führt zu 401 statt zum Durchreichen.
**Why it happens:** `_exapps_msg` ruft `nc_get_user` immer, wenn ein Cookie **oder** ein `authorization`-Header anliegt. Die Session-Cache (`HP_SESSION_LIFETIME`, Default 3 s) greift nur für Cookies. Ein 4xx aus Nextcloud liefert `None` (dann entscheidet weiter `access_level`), ein 5xx wirft und wird zu 401.
**How to avoid:** Auf einer `PUBLIC`-Route keinen `Authorization`-Header senden, wenn er nicht gebraucht wird. Für Phase 3 einplanen: eigene Bearer-Tokens werden von Nextcloud als 4xx abgewiesen (unschädlich, kostet aber pro Request einen Roundtrip). Das ist ein Argument dafür, in Phase 3 die MCP-Route auf `PUBLIC` zu stellen und selbst zu authentifizieren.
**Warning signs:** Unter Last steigende Latenzen; sporadische 401 ohne Eintrag im ExApp-Log.

### Pitfall 7: Netz-Dreieck und `nextcloud_url`
**What goes wrong:** Registrierung schlägt beim Heartbeat fehl, obwohl der Container läuft.
**Why it happens:** Drei Richtungen müssen funktionieren: Nextcloud erreicht den Daemon, der Daemon erreicht Nextcloud, die ExApp erreicht Nextcloud. Bei HaRP kommt eine vierte dazu: Nextcloud erreicht die ExApp über `<nextcloud_url>/exapps/<appid>` - also über die **öffentliche** URL und damit über den Reverse-Proxy (`DockerActions::resolveExAppUrl`). Ohne `/exapps/`-Regel im Proxy scheitert bereits der Heartbeat. Zusätzlich ersetzt AppAPI bei fehlendem `nextcloud_url` in der Daemon-Konfiguration `https` durch `http`.
**How to avoid:** Im Testaufbau zwingend einen Reverse-Proxy vor Nextcloud stellen, der `/exapps/*` an HaRP gibt (genau das macht AIO ab Werk in seinem Caddyfile). `nextcloud_url` bei `app_api:daemon:register` explizit setzen.
**Warning signs:** "heartbeat check failed. Make sure that Nextcloud instance and ExApp can reach it other." im Log.

### Pitfall 8: `AA-VERSION` als Kompatibilitätssignal missverstehen
**What goes wrong:** Man baut eine Versionsprüfung auf `AA-VERSION` und blockt HaRP-Requests.
**Why it happens:** HaRP setzt hart `AA-VERSION: 32` mit dem Kommentar "temporary, remove it after we update all ExApps", während der PHP-Pfad die echte AppAPI-Version schickt. nc_py_api prüft den Header gar nicht.
**How to avoid:** `AA-VERSION` nur loggen, nie auswerten.

### Pitfall 9: AppAPI ist nicht im Server-Image
**What goes wrong:** `occ app:enable app_api` scheitert im CI mit "app not found".
**Why it happens:** AppAPI ist eine App-Store-App, kein Bestandteil des Server-Tarballs.
**How to avoid:** `occ app:install app_api` (braucht Netz) oder das Release-Tarball vorab in den Container legen. Im CI als eigener, cachebarer Schritt führen.

### Pitfall 10: `/heartbeat` mit Auth abgesichert
**What goes wrong:** Die Registrierung läuft 10 Minuten und schlägt dann fehl.
**Why it happens:** Bei Nicht-HaRP-Daemons kommt der Heartbeat **ohne** AppAPI-Header. Wer dort eine Prüfung einbaut, antwortet 401, und AppAPI wartet bis zum Timeout.
**How to avoid:** `/heartbeat` bleibt ungeschützt und antwortet ausschließlich `{"status":"ok"}` mit 200. Kein Versionsstring, keine Konfiguration (T-01-29 aus Phase 1 gilt analog).

### Pitfall 11: Re-Registrierung invalidiert das Secret
**What goes wrong:** Nach `app_api:app:unregister` plus `register` liefert die ExApp plötzlich 401 auf alle eingehenden Requests, oder Nextcloud weist alle ausgehenden ab.
**Why it happens:** `APP_SECRET` wird bei der Registrierung neu erzeugt und als Container-Env gesetzt. Ein weiterlaufender alter Prozess (typisch im `manual-install`-Dev-Loop) hält das alte Secret.
**How to avoid:** Im Dev-Loop nach jeder Re-Registrierung den lokalen Prozess neu starten; Secret im `manual_install`-JSON fest vorgeben (`"secret": "..."`), dann ist es stabil.
**Warning signs:** `Invalid signature for ExApp` im Nextcloud-Log; vergleiche app_api#934 (Talk-Bot verliert Secret nach ExApp-Neustart).

### Pitfall 12: CSRF bei App-REST unter Impersonation
**What goes wrong:** Theoretisch könnte `SecurityMiddleware` einen `CrossSiteRequestForgeryException` werfen, weil Impersonation den Nutzer per `setUser()` einloggt, ohne Token-Auth-Kontext.
**Why it happens:** `passesCSRFCheck()` verlangt entweder `OCS-APIRequest`, einen `requesttoken` oder einen Controller mit `#[NoCSRFRequired]`.
**How to avoid:** Bereits erledigt. Phase 1 schickt auf allen JSON-Clients `OCS-APIRequest: true` (`notes.py`, `deck.py`, `ocs.py`). Diesen Header beim Umbau nicht entfernen. Für DAV ist die Frage gegenstandslos (Sabre, kein AppFramework).

## Code Examples

### Enge Routen-Deklaration und ihre Wirkung

```
Client: GET https://cloud.example.com/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
HaRP:   target_path = "/.well-known/oauth-protected-resource/mcp"
        Route ^/\.well-known/ trifft, access_level PUBLIC -> durchgelassen, kein nc_user nötig
        Header gesetzt: EX-APP-ID, EX-APP-VERSION, AA-VERSION, AUTHORIZATION-APP-API = b64(":<secret>")
ExApp:  user_id == ""  -> App-Kontext, kein Datenzugriff erlaubt, nur Metadaten ausliefern
```

```
Client: POST https://cloud.example.com/exapps/mcp_connector/mcp   (Basic <alice:app-passwort>)
HaRP:   Route ^/mcp/?$ trifft, access_level USER
        nc_get_user -> GET /index.php/apps/app_api/harp/user-info (mit harp-shared-key)
        -> user_id "alice", access_level 1
        AUTHORIZATION-APP-API = b64("alice:<secret>")
ExApp:  verify_appapi_headers -> "alice"
        Credentials(mode="appapi", user="alice", secret=APP_SECRET)
        -> PROPFIND /remote.php/dav/files/alice/  mit den 4 Headern
Nextcloud: DavPlugin -> validateExAppRequestToNC -> setUser(alice) -> ACLs von alice greifen
```

### occ-Rezept für den unattended Testaufbau (HaRP)

```bash
# 1. AppAPI installieren (App Store, braucht Netz)
occ app:install app_api

# 2. HaRP-Daemon registrieren (Beispiel aus RegisterDaemon::addUsage)
occ app_api:daemon:register \
  harp_proxy_docker "Harp Proxy (Docker)" docker-install http \
  "appapi-harp:8780" "http://caddy" \
  --net nextcloud --harp \
  --harp_frp_address "appapi-harp:8782" \
  --harp_shared_key "$HP_SHARED_KEY" \
  --set-default

# 3a. ExApp aus lokaler info.xml registrieren (Container-Deploy)
occ app_api:app:register mcp_connector harp_proxy_docker \
  --info-xml /var/www/html/appinfo-mcp/info.xml --force-scopes

# 3b. Oder Dev-Loop ohne Container: manual-install mit festem Secret
occ app_api:daemon:register manual_install "Manual Install" manual-install http null "http://caddy"
occ app_api:app:register mcp_connector manual_install --json-info \
  '{"id":"mcp_connector","name":"MCP Connector","daemon_config_name":"manual_install","version":"0.2.0","secret":"dev-secret","port":9100,"routes":[{"url":"^/mcp/?$","verb":"GET,POST,DELETE","access_level":"USER"},{"url":"^/\\.well-known/","verb":"GET","access_level":"PUBLIC"}]}' \
  --force-scopes --wait-finish

# 4. Zustand prüfen
occ app_api:app:list
occ app_api:daemon:list
```

`--json-info` ist der Weg, der ohne App-Archiv auskommt; die Routen müssen dort typisiert stehen (`access_level` als String oder Zahl, Listen als echte JSON-Arrays), während sie in `info.xml` als JSON-String im Element stehen (`<bruteforce_protection>[401]</bruteforce_protection>`).

### Docker-Compose-Skizze für den HaRP-Test (D-31)

```yaml
services:
  caddy:            # spiegelt die AIO-Topologie: /exapps/* -> HaRP, Rest -> Nextcloud
    image: caddy:2
    ports: ["127.0.0.1:8080:80"]      # WR-06: Loopback
  nextcloud:
    image: nextcloud:34-apache        # wie compose.test.yml, SQLite
  appapi-harp:
    image: ghcr.io/nextcloud/nextcloud-appapi-harp:release
    environment:
      HP_SHARED_KEY: "${HP_SHARED_KEY}"
      NC_INSTANCE_URL: "http://caddy"
      HP_TRUSTED_PROXY_IPS: "172.16.0.0/12"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./.harp-certs:/certs
```

Caddyfile-Kern (aus dem AIO-Original abgeleitet):

```
:80 {
    route /exapps/* { reverse_proxy appapi-harp:8780 { transport http { read_timeout 1800s } } }
    route { reverse_proxy nextcloud:80 }
}
```

## Der Discovery-Spike (AUTH-06): Go-Kriterien und Belege

**Vorbefund: Go.** Was bereits ohne Test feststeht:

| Frage | Antwort | Beleg |
|-------|---------|-------|
| Kann eine ExApp unauthentifizierte Routen haben? | Ja, `access_level` `PUBLIC` = "public access without auth" | `ExAppRouteAccessLevel::PUBLIC = 0`; Doku `tech_details/api/routes` |
| Lässt der PHP-Proxy anonyme Requests zu? | Ja, Controller ist `#[PublicPage] #[NoAdminRequired] #[NoCSRFRequired]`, `passesExAppProxyRouteAccessLevelCheck` gibt bei PUBLIC bedingungslos true | `ExAppProxyController` |
| Lässt HaRP anonyme Requests zu? | Ja, `if route.access_level == AccessLevel.PUBLIC: route_allowed = True` vor jeder Nutzerprüfung | `haproxy_agent.py`, `_exapps_msg` |
| Ist der HaRP-Pfad von außen erreichbar? | Ja, `<nc>/exapps/<appid>/...`, in AIO ab Werk verdrahtet | HaRP-README; all-in-one `Containers/apache/Caddyfile`: `route /exapps/* { reverse_proxy {$HARP_HOST}:8780 }` |
| Überlebt Streamable HTTP den Weg? | Ja für HaRP, laut Maintainer | app_api#825, oleksandr-nc, 2026-04-10: "The request and response bodies stream straight through HAProxy to your ExApp and back. So everything should work." |
| Kommt `WWW-Authenticate` beim Client an? | Ja, der Proxy filtert nur `aa-version`, `ex-app-id`, `authorization-app-api`, `ex-app-version`, `aa-request-id` aus der Antwort | `ExAppProxyController::createProxyResponse` |

**Was der Spike trotzdem messen muss:**

1. `curl -i https://<test-nc>/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp` ohne Cookie und ohne Auth: erwartet 200 mit JSON.
2. `curl -i https://<test-nc>/exapps/mcp_connector/mcp` ohne Auth: erwartet 401 mit `WWW-Authenticate: Bearer resource_metadata="..."` (mit `access_level=PUBLIC` auf der Route; bei `USER` antwortet bereits HaRP mit 403/401, was für Phase 3 zu früh wäre).
3. Dasselbe über `https://<test-nc>/apps/app_api/proxy/mcp_connector/...` (Zweitweg, PHP).
4. Der kanonische Wurzelpfad `https://<test-nc>/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp`: erwartet 404 von Nextcloud. **Dieses Ergebnis ist der eigentliche Spike-Befund** und entscheidet, ob Phase 3 auf den `resource_metadata`-Zeiger setzt oder eine Reverse-Proxy-Regel dokumentieren muss.
5. Streaming-Nachweis: eine MCP-Session (SSE-Antwort auf GET, chunked POST) über den HaRP-Pfad mit dem echten SDK-Client.

**Dokumentationsziel (D-29):** `docs/spike-discovery.md` mit der Matrix Pfad x Auth-Zustand x Statuscode, dem 404-Befund zum Wurzelpfad und der empfohlenen Topologie für Phase 3, inklusive der Fallback-Reverse-Proxy-Regel im Klartext.

**Wichtiger Nebenbefund für die Reihenfolge:** In Phase 2 ist `access_level=USER` auf `/mcp` die bessere Wahl (Defense in Depth, und HaRP löst für uns den Nutzer aus einem App-Passwort auf, was die Permission-Parity-Kette ohne OAuth vollständig macht). Der Wechsel auf `PUBLIC` gehört in Phase 3, zusammen mit dem eigenen Token-Verifier. Der Discovery-Spike darf `PUBLIC` temporär auf einer separaten `.well-known`-Route testen, ohne `/mcp` zu öffnen.

## Der DAV-Spike (D-30): erwartete Matrix

Impersonation ist für alle drei Familien im Code vorgesehen. Der Spike bestätigt oder widerlegt.

| API-Familie | Endpunkt | Mechanismus in Nextcloud | Erwartung | Spike-Nachweis |
|-------------|----------|--------------------------|-----------|----------------|
| WebDAV Files | `/remote.php/dav/files/<user>/` | `DavPlugin` + `AppAPIAuthBackend` | funktioniert | PROPFIND Depth 1, SEARCH, PUT mit `If-None-Match: *` |
| CalDAV | `/remote.php/dav/calendars/<user>/` | derselbe Sabre-Server, dieselben Plugins | funktioniert | REPORT `calendar-query` mit `<c:expand>` |
| CardDAV | `/remote.php/dav/addressbooks/users/<user>/` | dito | funktioniert | REPORT `addressbook-query` |
| OCS (capabilities, Unified Search) | `/ocs/v2.php/...` | `OC::tryAppAPILogin` in `handleLogin` | funktioniert | `GET /ocs/v2.php/cloud/user` muss `alice` liefern, nicht 401 |
| Notes REST | `/index.php/apps/notes/api/v1/notes` | dito | funktioniert | GET Liste, POST neue Notiz |
| Deck REST | `/index.php/apps/deck/api/v1.0/boards` | dito | funktioniert | GET Boards, POST Karte |

**Identität serverseitig verifizieren** (D-30 verlangt Beleg, nicht nur Statuscode): `GET /ocs/v2.php/cloud/user` mit denselben Headern muss `ocs.data.id == "bob"` liefern, und `data/exapp_impersonation.log` muss den Eintrag zeigen. Zusätzlich der Negativtest: ein Zugriff auf `/remote.php/dav/files/alice/` mit Bob-Kontext muss 403/404 liefern, nicht 200.

**Wenn eine Familie scheitert:** genau diese Familie fällt auf App-Passwörter zurück (D-27), dokumentiert pro Familie, mit sichtbarem Log-Eintrag beim Moduswechsel und ohne stillen Fallback. Der Rückfall ist dann eine bewusste Konfiguration, kein Laufzeitverhalten.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Docker Socket Proxy als empfohlener Deploy-Daemon | HaRP (HAProxy + SPOE-Agent + FRP) | Empfohlen ab NC 32, DSP deprecated in AppAPI 34.0.0, Entfernung geplant für NC 35 | Nichts DSP-Spezifisches bauen; DSP nur noch als Kompatibilitätspfad testen |
| API-Scopes in `info.xml` (`<scopes>`) | Entfernt, Zugriff ist app-weit mit Impersonations-Audit-Log | AppAPI 3.2.0 (#373) | `--force-scopes` bleibt als No-Op-Flag in Beispielen, `<scopes>` nicht mehr pflegen |
| ExApp-Routen implizit erlaubt | `<routes>` in `info.xml` verpflichtend, sobald der Proxy genutzt wird | AppAPI 3.0.0 (#327) | Ohne Deklaration antwortet der Proxy 404, ohne Fehlermeldung an den Client |
| AppAPI-Versionierung 3.x | AppAPI folgt der Nextcloud-Hauptversion (34.x für NC 34) | ab v34 | Versionsangaben in Doku und Blogposts vor 2025 sind irreführend |
| ExApp lauscht auf TCP `APP_HOST:APP_PORT` | Bei HaRP: Unix-Socket `/tmp/exapp.sock` plus frpc-Tunnel | NC 32 | Der Startcode muss beide Fälle können; `HP_SHARED_KEY` ist das Unterscheidungsmerkmal |
| `<system>true</system>`, `exAppRequestWithUserInit` | entfernt bzw. deprecated | AppAPI 3.0.0 (#323) | Ältere ExApp-Beispiele im Netz sind teilweise nicht mehr lauffähig |

**Deprecated/veraltet:**
- Die offizielle Doku unter `nextcloud.github.io/app_api` hinkt dem Code hinterher: `CreationOfDeployDaemon` empfiehlt weiterhin DSP und kennt die `--harp*`-Optionen von `app_api:daemon:register` nicht. Im Zweifel gilt der Quellcode und das CHANGELOG.
- Das alte Doku-Zitat "heartbeat timeout 90 Sekunden" stimmt nicht mehr; der Code nutzt 10 Minuten (600 Versuche im Sekundentakt), bzw. 1 Minute für die Test-Deploy-App.

## Antwort auf die Entscheidungsregel D-24

**Ergebnis: selbst implementieren, kein nc_py_api.**

| Kriterium aus D-24 | Befund | Beleg |
|--------------------|--------|-------|
| "wenige, stabile Header-Checks" | Genau drei Header, ein Gleichheitsvergleich, ein base64-Split. Seit AppAPI 2.x unverändert. | `nc_py_api._session.sign_check`, `AppAPICommonService::buildAppAPIAuthHeaders`, `haproxy.cfg.template` |
| "laut offizieller AppAPI-Doku" | Dokumentiert unter `tech_details/Authentication`, zusätzlich im Quellcode beider Seiten nachvollziehbar | nextcloud.github.io/app_api/tech_details/Authentication.html |
| "nachweislich fragil oder undokumentiert" | Nein. Kein Zeitstempel, keine Nonce, keine Signatur, keine Kanonisierung. Die einzige Subtilität ist, dass `AA-VERSION` nicht geprüft wird und `/heartbeat` ungeschützt bleiben muss. | HaRP setzt `AA-VERSION: 32` hart, nc_py_api prüft ihn nicht |
| Kosten der Alternative | nc_py_api zieht FastAPI, niquests und einen eigenen Session-Layer; das Projekt ist Starlette-only und httpx-only | 01-RESEARCH.md Zeile 141, `context_agent/pyproject.toml` als Gegenbeispiel |
| Aufwand der Eigenimplementierung | ca. 60 Zeilen: Header-Prüfung (25), `httpx.Auth` (20), Start-Wrapper (10), Init-Status-Push (15) | Patterns 1, 3, 4 in diesem Dokument |

Der einzige Teil von nc_py_api, der später echten Mehrwert hätte, sind die Declarative Settings für EXAPP-02 in Phase 4. Auch das ist eine OCS-Registrierung im `enabled`-Handler und kann dann neu bewertet werden, ohne Phase 2 zu belasten.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Impersonation funktioniert empirisch für Notes-REST und Deck-REST (Code-Pfad über `OC::tryAppAPILogin` belegt, aber nicht gegen eine laufende Instanz getestet) | DAV-Spike-Matrix | Diese Familien brauchen den App-Passwort-Fallback nach D-27; Provider-Aufteilung wird komplexer |
| A2 | `Cache-Control: no-store` auf allen ExApp-Antworten unterbindet die 3600-Sekunden-Cache-Logik des PHP-Proxys vollständig | Pitfall 4 | Antworten könnten trotzdem gecacht werden; Discovery-Änderungen schlagen verzögert durch |
| A3 | Streaming über den PHP-Proxy (`/apps/app_api/proxy/...`) funktioniert ebenfalls; der Maintainer bestätigt nur den HaRP-Pfad | Alternatives Considered | Der PHP-Proxy taugt nur als Fallback für nicht-streamende Aufrufe; die Doku muss HaRP als Voraussetzung nennen |
| A4 | `mcp.custom_route` unterstützt `PUT` und `POST` genauso wie das bereits genutzte `GET` | Pattern 2 | Lifecycle-Routen müssten als separate Starlette-Routen auf der gebauten App registriert werden (kleiner Umbau, kein Blocker) |
| A5 | Der Nextcloud-Testcontainer erreicht seine eigene öffentliche URL über den Caddy-Service im selben Compose-Netz | Compose-Skizze | Heartbeat schlägt fehl; es braucht zusätzlich `extra_hosts` oder `trusted_proxies`-Konfiguration |
| A6 | AIO benötigt für den Smoke-Test nur das Aktivieren des optionalen HaRP-Containers, keine weitere Handarbeit | Test-Infrastruktur | Der AIO-Schritt wird größer als geplant und wandert nach D-31 als offener Punkt in Phase 5 |
| A7 | `access_level=USER` plus Basic-App-Passwort ergibt über HaRP eine vollständige Identitätskette ohne OAuth | Discovery-Spike, Nebenbefund | Der Permission-Parity-Beweis in Phase 2 braucht einen anderen Träger (z.B. Nextcloud-Session-Cookie im Test) |

## Open Questions

1. **Wird `/mcp` in Phase 2 auf `USER` oder `PUBLIC` gesetzt?**
   - Was wir wissen: `USER` gibt zusätzlichen Schutz und liefert die Nutzeridentität frei Haus; `PUBLIC` ist für den OAuth-Flow ab Phase 3 zwingend, weil sonst HaRP vor unserem 401 antwortet.
   - Was unklar ist: ob der Discovery-Spike `PUBLIC` auf `/mcp` braucht, um den 401-mit-`WWW-Authenticate` realistisch zu testen.
   - Empfehlung: `/mcp` auf `USER` belassen, den Spike auf einer separaten Route (`^/spike/mcp$`, `PUBLIC`) fahren und den Wechsel als Phase-3-Aufgabe dokumentieren.

2. **Sollen `/heartbeat`, `/init`, `/enabled` zusätzlich per `x-origin-ip` abgesichert werden?**
   - Was wir wissen: Die enge Routendeklaration reicht, HaRP blockt sie ohnehin.
   - Was unklar ist: ob der Aufwand die zusätzliche Verzweigung wert ist.
   - Empfehlung: ja, drei Zeilen, weil eine spätere Routen-Erweiterung sonst still zur Lücke wird.

3. **Wie wird das ExApp-Archiv für den App Store aufgebaut (info.xml plus l10n)?**
   - Was wir wissen: ExApps liefern `appinfo/`, `l10n/`, optional `img/`, `css/`, `js/`; kein PHP.
   - Was unklar ist: ob der App-Store-Validator das `<routes>`-Element im aktuellen Schema akzeptiert.
   - Empfehlung: Phase 5 (EXAPP-04), aber `info.xml` schon in Phase 2 vollständig und schema-nah schreiben, damit der CSR-PR #1160 nicht nachträglich Änderungen braucht.

4. **Wie verhält sich `nc_get_user` bei einem Bearer-Token, das Nextcloud nicht kennt?**
   - Was wir wissen: 4xx wird zu `None` (Request läuft auf `PUBLIC`-Routen weiter), 5xx wird zu 401.
   - Was unklar ist: ob Nextcloud für unbekannte Bearer-Tokens sicher 401 (also 4xx) liefert und nicht 500.
   - Empfehlung: im Discovery-Spike mitmessen, weil davon die Phase-3-Topologie abhängt.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker Engine | compose-Testumgebung, Deploy Daemon | ja | 29.5.2 (Docker Desktop) | - |
| Docker Compose | compose.exapp.yml | ja | v5.1.4 | - |
| uv | Build und Tests | ja | 0.11.7 | - |
| Python | Toolchain | ja | 3.13.1 (global defekt laut Projektregel, uv ist der Weg) | uv-verwaltetes Python |
| curl | Spike-Messungen, Container-Build | ja | 8.19.0 | - |
| Netzzugang zu apps.nextcloud.com | `occ app:install app_api` | ja (angenommen, Recherche lief online) | - | AppAPI-Release-Tarball vorab in den Container legen |
| Netzzugang zu ghcr.io | HaRP-Image, später eigenes Image | ja (angenommen) | - | Image lokal bauen |
| Nextcloud AIO | zweiter Smoke-Test (D-31) | nicht geprüft | - | Als dokumentierter offener Punkt an Phase 5 übergeben, falls lokal unverhältnismäßig |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** AIO (siehe D-31 und Open Question).

Hinweis zur Windows-/Docker-Desktop-Umgebung: HaRP mountet `/var/run/docker.sock`. Unter Docker Desktop funktioniert das aus einem Linux-Container heraus, der Socket-Pfad im Compose-File bleibt `/var/run/docker.sock`. Die Loopback-Bindung nach WR-06 gilt für alle veröffentlichten Ports (`127.0.0.1:8080:80`), auch für HaRPs 8780/8782, die im Test gar nicht veröffentlicht werden müssen, weil Caddy sie im Compose-Netz erreicht.

## Security Domain

### Neue Trust Boundaries dieser Phase

| Boundary | Wer spricht | Kontrolle |
|----------|-------------|-----------|
| Internet zu HaRP | beliebiger Client | Routen-Regex plus `access_level`, IP-Blacklist (`HP_BLACKLIST_COUNT`), Pfad-Traversal-Filter |
| HaRP zu ExApp | HAProxy | setzt die vier Header selbst, überschreibt Client-Werte; `harp-shared-key` schützt den AppAPI-signierten Sonderpfad |
| Nextcloud-PHP-Proxy zu ExApp | AppAPI | entfernt `authorization-app-api` und `x-origin-ip` aus dem Client-Request, setzt eigene |
| ExApp zu Nextcloud | unser Code | `APP_SECRET` plus Nutzer-Id; jeder Aufruf landet im Impersonations-Log |
| Deploy Daemon zu Container | AppAPI/HaRP | Docker-Socket, Env-Injection inklusive `APP_SECRET` |

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | Shared-Secret-Vergleich constant-time (`secrets.compare_digest`), kein Retry, kein Echo des Wertes |
| V3 Session Management | teilweise | Die ExApp hält keine Session; die Nutzeridentität gilt genau für einen Request (Phase-1-Invariante bleibt) |
| V4 Access Control | ja | `access_level` je Route in `info.xml`; Datenzugriff nur mit nicht-leerer Nutzer-Id; ACLs bleiben serverseitig |
| V5 Input Validation | ja | base64-Dekodierung mit `validate=True`, Längen- und Trennzeichenprüfung; Query-Parameter `enabled` streng auf 0/1 |
| V6 Cryptography | ja | Kein eigenes Krypto. base64 ist Kodierung, kein Schutz; das Secret ist ein Bearer-äquivalentes Geheimnis |
| V7 Error Handling / Logging | ja | 401 ohne Detail nach außen; `AA-REQUEST-ID` als Korrelations-Id loggen; niemals `AUTHORIZATION-APP-API` oder `APP_SECRET` loggen (auch nicht gekürzt) |
| V9 Communications | ja | Intern HTTP bzw. Unix-Socket ist akzeptiert (HaRP terminiert TLS); ausgehend `follow_redirects=False` bleibt (Header-Leak-Schutz aus Phase 1) |
| V14 Configuration | ja | Container non-root, keine Secrets im Image, `APP_SECRET` nur aus der Umgebung |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Gefälschter `AUTHORIZATION-APP-API` von außen | Spoofing | Beide Proxy-Wege entfernen bzw. überschreiben den Header aus dem Client-Request; zusätzlich Secret-Vergleich in der ExApp |
| Lifecycle-Endpunkt von außen aufrufbar (`enabled=0` als DoS) | Denial of Service, Tampering | Enge Routendeklaration (kein Treffer bedeutet 404), plus `x-origin-ip`-Guard |
| Timing-Angriff auf das Shared Secret | Information Disclosure | `secrets.compare_digest` statt `==` (Phase-1-Muster aus `StaticBearerVerifier`, T-01-24) |
| Secret-Leak über Logs oder Tracebacks | Information Disclosure | `Credentials.__repr__` maskiert; `AppApiAuth` hält das Token privat; httpx/httpcore bleiben auf WARNING |
| Confused Deputy: Client wählt den Nutzer | Elevation of Privilege | Nutzer kommt ausschließlich aus dem Header, den der Proxy setzt; kein Tool-Parameter (T-01-12 bleibt gültig) |
| Cache-Vergiftung über den PHP-Proxy (3600 s) | Tampering | `Cache-Control: no-store` auf allen Antworten |
| Brute Force auf öffentliche Routen | Denial of Service | `bruteforce_protection` je Route, aber ohne 401 auf der MCP-Route |
| Path Traversal über den Proxy | Tampering | Beide Proxies filtern `..`-Segmente; die ExApp validiert Pfade ohnehin (`safe_path`, T-01-09) |

Neu zu ergänzen in `01-SECURITY.md` bzw. dessen Phase-2-Fortschreibung: die fünf Boundaries oben und die Feststellung, dass `APP_SECRET` ein instanzweites Geheimnis ist, dessen Kompromittierung Impersonation **jedes** Nutzers erlaubt. Es gehört damit in dieselbe Schutzklasse wie ein Admin-Token, auch wenn es kein Shared-Admin-Token im Sinne des Out-of-Scope-Eintrags ist (es erlaubt keinen Zugriff ohne Nutzerkontext, aber Zugriff als beliebiger Nutzer).

## Project Constraints (from CLAUDE.md)

| Direktive | Konsequenz für Phase 2 |
|-----------|--------------------------|
| Python 3.13, uv als Toolchain, System-Python defekt | Alle Kommandos über `uv run`; das Container-Image nutzt uv als Installer |
| mcp>=2.0,<3, offizielles SDK, kein FastMCP | Lifecycle-Routen über `mcp.custom_route`, nicht über eine zweite Framework-Schicht |
| httpx roh statt DAV-Libraries | Der neue Credential-Modus ist ein `httpx.Auth`, nicht ein zweiter Client-Stack |
| Kein admin-weites Shared-Token | `APP_SECRET` wird nie ohne Nutzerkontext für Datenzugriffe benutzt; leerer Nutzer bedeutet Ablehnung |
| Keine destruktiven Operationen | Unverändert; die ExApp-Shell fügt keine Tools hinzu |
| AGPL-3.0, Repo public auf street1983nk | `start.sh` aus HaRP ist AGPL-3.0, Übernahme mit SPDX-Header ist kompatibel; frpc ist Apache-2.0 und wird nur als Binary installiert |
| Code und README Englisch, Projektkommunikation Deutsch | RESEARCH/Pläne deutsch, Code und Docstrings englisch |
| Keine Em-Dashes, echte Umlaute, keine Emojis | Gilt für alle Artefakte dieser Phase |
| Conventional Commits `typ(02-xx):`, keine Co-Authored-By-Trailer | Unverändert aus Phase 1 |
| GSD-Workflow: keine direkten Repo-Edits außerhalb eines GSD-Kommandos | Executoren arbeiten nur im Plan-Kontext, Push macht der Orchestrator |
| Gates (D-32): ruff verschärft, pyright 0 Fehler, vulture mit Whitelist, Token-Budget, Testsuite ohne Docker grün | Neue Module brauchen Unit-Tests ohne Docker; die 20 mechanischen Client-Änderungen dürfen die Contract-Tests nicht berühren |

## Sources

### Primary (HIGH confidence)

Quellcode, jeweils Stand `main` am 2026-08-15, abgerufen über raw.githubusercontent.com bzw. die GitHub-API:

- `nextcloud/app_api` `lib/Controller/ExAppProxyController.php` - Proxy-Routing, `access_level`-Prüfung, Header-Ausschluss, Cache-Logik, Bruteforce
- `nextcloud/app_api` `lib/Db/ExApp.php` - `enum ExAppRouteAccessLevel: PUBLIC=0, USER=1, ADMIN=2`
- `nextcloud/app_api` `lib/Service/AppAPICommonService.php` - `buildAppAPIAuthHeaders`, `buildExAppHost`
- `nextcloud/app_api` `lib/Service/AppAPIService.php` - `requestToExApp2`, `prepareRequestToExApp2`, `swapAuthorizationHeader`, `validateExAppRequestToNC`, `finalizeRequestToNC`, `heartbeatExApp`, `dispatchExAppInitInternal`, `enableExApp`, `disableExApp`, `getExAppUrl`
- `nextcloud/app_api` `lib/Service/ExAppRouteHelper.php` - Routen-Normalisierung und erlaubte Feldwerte
- `nextcloud/app_api` `lib/Service/HarpService.php` - HaRP-Registry, `harp-shared-key`, `getHarpExApp`
- `nextcloud/app_api` `lib/DavPlugin.php`, `lib/AppAPIAuthBackend.php`, `lib/Listener/SabrePluginAuthInitListener.php` - DAV-Impersonation
- `nextcloud/app_api` `lib/Middleware/AppAPIAuthMiddleware.php` - greift nur bei `#[AppAPIAuth]`
- `nextcloud/app_api` `lib/DeployActions/DockerActions.php` - `buildDeployEnvs`, `resolveExAppUrl`, Healthcheck-Behandlung
- `nextcloud/app_api` `lib/Command/Daemon/RegisterDaemon.php` - alle `--harp*`-Optionen und Usage-Beispiele
- `nextcloud/app_api` `appinfo/routes.php`, `appinfo/info.xml`, `CHANGELOG.md` - Proxy-Pfade, HaRP-Callbacks, Versionsstand 34.x/35.0.0-dev
- `nextcloud/HaRP` `haproxy_agent.py` (SPOE-Agent: `_exapps_msg`, `nc_get_user`, Access-Level-Logik), `haproxy.cfg.template` (Header-Injection, Statuscodes), `README.md` (Deployment, Reverse-Proxy-Beispiele, ExApp-Anpassung, Env-Variablen)
- `nextcloud/server` `lib/OC.php` (`handleLogin`, `tryAppAPILogin`), `lib/private/AppFramework/Http/Request.php` (`passesCSRFCheck`), `lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php`
- `nextcloud/all-in-one` `php/containers.json` (HaRP-Container), `Containers/apache/Caddyfile` (`route /exapps/*`)
- `nextcloud/context_agent` `appinfo/info.xml`, `Dockerfile`, `start.sh`, `ex_app/lib/main.py`, `ex_app/lib/mcp_server.py`, `pyproject.toml` - der nächstliegende Referenz-ExApp (offizieller MCP-Server als ExApp)
- `cloud-py-api/nc_py_api` `nc_py_api/_session.py` (`sign_check`, `_add_auth`, `AppConfig`), `nc_py_api/_misc.py` (`get_username_secret_from_headers`), `nc_py_api/ex_app/integration_fastapi.py`, `nc_py_api/ex_app/uvicorn_fastapi.py`
- Lokal installiertes MCP-SDK: `.venv/Lib/site-packages/mcp/server/auth/routes.py` (`build_resource_metadata_url`), `mcp/client/auth/utils.py` (SEP-985-Reihenfolge), `mcp/server/auth/middleware/bearer_auth.py` (`resource_metadata` im `WWW-Authenticate`), `mcp/server/auth/settings.py`

Offizielle Dokumentation:

- nextcloud.github.io/app_api/tech_details/Authentication.html - Header und Validierungsreihenfolge
- nextcloud.github.io/app_api/notes_for_developers/ExAppLifecycle.html - heartbeat/init/enabled, Timeouts, Cookies
- nextcloud.github.io/app_api/notes_for_developers/ExAppOverview.html - Ordnerstruktur, `<external-app>`, Persistent Storage, Makefile-Konventionen
- nextcloud.github.io/app_api/tech_details/api/routes.html - Routen-Deklaration und Feldsemantik
- nextcloud.github.io/app_api/tech_details/Deployment.html - Deploy-Env-Variablen, Installationsablauf, manual-install
- nextcloud.github.io/app_api/ManagingExternalApplications.html - occ-Kommandos

### Secondary (MEDIUM confidence)

- github.com/nextcloud/app_api/issues/825 - Maintainer-Aussage zu Streamable HTTP über HaRP (2026-04-10, geschlossen)
- github.com/nextcloud/app_api/issues/934 - Secret-Verlust nach ExApp-Neustart (Kontext für Pitfall 11)
- github.com/nextcloud/app_api/pull/874 und Backports - "fix: proxy route leading slash" als Hintergrund der Regex-Kanonisierung
- `nextcloud/notes` `lib/Controller/NotesController.php`, `nextcloud/deck` `lib/Controller/BoardApiController.php` - Attributlage für die CSRF-Betrachtung

### Tertiary (LOW confidence)

- Keine. Alle Aussagen dieses Dokuments sind entweder Quellcode-belegt oder als Annahme in der Assumptions-Tabelle markiert.

## Metadata

**Confidence breakdown:**
- AppAPI-Kontrakt (Header, Lifecycle, Routen): HIGH - beidseitiger Quellcode plus Doku plus zwei Referenzimplementierungen
- Impersonation (AUTH-05): HIGH für den Mechanismus (Kern-Login-Hook plus Sabre-Backend), MEDIUM für die empirische Abdeckung je API-Familie
- Discovery-Topologie (AUTH-06): HIGH für die Erreichbarkeit `PUBLIC`-deklarierter Routen, MEDIUM für die Client-Akzeptanz eines nicht-kanonischen PRM-Pfades
- Deploy und Test-Infrastruktur: HIGH für die occ-Kommandos und die AIO-Topologie, MEDIUM für den konkreten Compose-Aufbau (nicht ausgeführt)
- Dockerfile-Anforderungen: HIGH - HaRP-README plus context_agent als lauffähiges Beispiel

**Research date:** 2026-08-15
**Valid until:** 2026-09-15 (AppAPI bewegt sich mit jeder Nextcloud-Hauptversion; vor Phase 5 erneut gegen den dann aktuellen `main` prüfen, besonders die DSP-Entfernung in NC 35)
