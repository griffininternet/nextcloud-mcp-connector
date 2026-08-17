# Phase 4: Per-User-Verwaltung und prepare_context - Pattern Map

**Mapped:** 2026-08-17
**Files analyzed:** 16 neue/geänderte Dateien
**Analogs found:** 16 / 16 (keine Datei ohne Analog)

Grundlage: 04-CONTEXT.md (D-44 bis D-58), 04-RESEARCH.md (Pull-only-Befund, empfohlene
Struktur), 04-UI-SPEC.md (S5 bis S8, E8, R1, Schalter auf `/connections`). Alle Zeilennummern
gegen den Stand vom 2026-08-17 gelesen.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|-----------|-----------------|-------|
| `src/mcp_connector/exapp/ui/connections.py` (NEU) | View/Template (S5-S8) | request-response (Seiten-Render) | `src/mcp_connector/exapp/ui/connect.py` | exakt |
| Connections-Routen (NEU, Modulort = Planner-Entscheid, siehe Hinweis unten) | Route/Controller | request-response (GET Liste, POST Aktionsfeld) | `src/mcp_connector/oauth/consent.py` (Dispatch, HMAC, Identität) + `src/mcp_connector/oauth/connect.py` (Aktionsfeld, Store-Closure) | exakt |
| `src/mcp_connector/exapp/settings_form.py` (NEU) | Service (ausgehender OCS-Call) | request-response (fire-and-forget) | `src/mcp_connector/exapp/status.py` | exakt |
| `src/mcp_connector/tools/context.py` (NEU) | Tool-Logik | Fan-out/Aggregation mit Degradation | `src/mcp_connector/tools/search.py` (primär), `tools/calendar.py`, `tools/chatgpt.py` | exakt |
| `src/mcp_connector/server/reg_context.py` (NEU) | Tool-Registrierung | request-response | `src/mcp_connector/server/reg_search.py` | exakt |
| `src/mcp_connector/exapp/middleware.py` (MOD) | Middleware/Transportgrenze | request-response | sich selbst (Zweig-Struktur bleibt) | exakt |
| `src/mcp_connector/exapp/lifecycle.py` (MOD) | Lifecycle-Handler | request-response | eigener `/init`-Handler (Fire-and-forget-Modell) | exakt |
| `src/mcp_connector/oauth/store.py` (MOD) | Storage/Model | CRUD (SQLite, WAL) | eigene `authorizations`-Methoden + `_add_missing_columns` | exakt |
| `src/mcp_connector/oauth/provider.py` (MOD) | Service | CRUD (Widerrufssequenz) | eigene `_end_connection` (wird öffentlich) | exakt |
| `src/mcp_connector/exapp/ui/strings.py` (MOD) | Config/Textkatalog | statisch | sich selbst (eine Konstante je Satz, `__all__`) | exakt |
| `src/mcp_connector/exapp/ui/layout.py` (MOD) | UI-Primitive | statisch | eigene `detail_list`/`callout` (neues `row_list` daneben) | exakt |
| `src/mcp_connector/exapp/ui/errors.py` (MOD) | Config/Fehlertabelle | request-response | eigene `_PAGES`-Tabelle (E8 = neue Zeile) | exakt |
| `src/mcp_connector/entry_exapp.py` (MOD) | Wiring/Composition Root | - | eigene Factory-Anhäng-Schleife | exakt |
| `appinfo/info.xml` (MOD) | Config/Manifest | - | bestehender `^/connect/?$`-Eintrag | exakt |
| `tests/contract/test_tool_surface.py` (MOD) + README-Tabelle | Test (Contract) | - | eigene Einzeltool-Tests (z. B. `unified_search`, Zeile 232-255) | exakt |
| Neue Unit-/Guard-Tests (Schalter-Gate, Connections-Seite, context-Tool) | Test (Unit) | - | `tests/unit/test_exapp_entry.py` (Boundary), `tests/unit/test_oauth_consent.py` (Seiten) | rollengleich |

**Hinweis Modulort der Connections-Routen:** Die etablierte Zweiteilung ist Templates in
`exapp/ui/<name>.py`, Routen in `oauth/<name>.py` (Paare `exapp/ui/connect.py` +
`oauth/connect.py` und `exapp/ui/consent.py` + `oauth/consent.py`). Die Templates deklarieren
Pfad- und Feldkonstanten, das Routenmodul importiert sie (Einbahnstraße, Kommentar in
`exapp/ui/connect.py:25-28`). 04-RESEARCH.md skizziert alles in `exapp/ui/connections.py`;
CONTEXT stellt den Ort in Claudes Ermessen. Empfehlung dieses Mappings: die Zweiteilung
beibehalten (Routen z. B. in `oauth/connections.py`), weil beide Analoge sie tragen und die
Abhängigkeitsrichtung (oauth importiert exapp.ui, nie umgekehrt) sonst bricht.

---

## Pattern Assignments

### Connections-Routen (Route 13, GET Liste / POST Aktionsfeld)

**Analog:** `src/mcp_connector/oauth/consent.py` und `src/mcp_connector/oauth/connect.py`

**Route-Factory + Anhängen nur durch entry_exapp** (`oauth/consent.py:128-195`, gekürzt):
```python
def consent_routes(
    env: Mapping[str, str] | None = None,
    *,
    provider: NextcloudOAuthProvider,
    throttle: Throttle | None = None,
) -> list[Route]:
    ...
    counters = throttle if throttle is not None else Throttle()
    authorize_route = Route(AUTHORIZATION_PATH, authorize, methods=["GET", "POST"])
    screen_routes = [
        Route(CONSENT_PATH, consent, methods=["GET"]),
        Route(DECIDE_PATH, decide, methods=["POST"]),
    ]
    for route in screen_routes:
        route.app = Throttled(route.app, counters, CLASS_AUTHORIZE, machine=False, env=env)
    return [authorize_route, *screen_routes]
```
`connections_routes(...)` folgt exakt dieser Form: Factory nimmt `env`, Store/Callbacks und
`throttle`, gibt `list[Route]` zurück, wird ausschließlich in `entry_exapp.build_exapp_app`
angehängt (D-23). Browser-Throttle-Klasse wie `CLASS_AUTHORIZE` (refusal-gezählt), keine
eigene Start-Klasse nötig: die Seite öffnet keinen Login-Flow.

**POST mit Aktionsfeld statt mehrerer Routen** (`oauth/connect.py:152-163`):
```python
async def begin(request: Request) -> Response:
    """Start a sign in, or cancel a running one. The only state changing route here."""
    form = await request.form()
    action = str(form.get(ACTION_FIELD) or "")
    if action == ACTION_CANCEL:
        return await _cancel(str(form.get(FLOW_PARAM) or ""), store, env)
    if action != ACTION_START:
        return _with_status(invitation_page(env=env), 400)
    return await _start(store, env)
```
Für `/connections`: geschlossene Enumeration `confirm | disconnect | pause | resume`
(UI-SPEC), unbekannte Aktion = Liste mit Status 400, exakt wie oben.

**Identität aus dem HaRP-Header, nie aus der Anfrage** (`exapp/auth.py:92-124`):
```python
def appapi_user(request: Request, *, env: Mapping[str, str] | None = None) -> str:
    """The Nextcloud account this request runs as, or an empty string when there is none."""
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        return ""

def is_user(received: str, expected: str) -> bool:
    """Whether these two Nextcloud user ids are the same account. Empty is never a match."""
    return bool(received) and bool(expected) and _same(received, expected)
```
Leere Identität auf `/connections` = E8 (403). Ownership je Zeile:
`is_user(appapi_user(request, env=env), row.nc_user)`, das Muster steht wörtlich in
`oauth/consent.py:417-423` (die drei Fälle fremd/unbekannt/weg antworten identisch, S8).

**Anti-Forgery-HMAC über den Handle** (`oauth/consent.py:529-539` + `oauth/store.py:362-369`):
```python
def _confirmed(store: OAuthStore, flow_id: str, presented: str) -> bool:
    expected = store.form_token(flow_id)
    return bool(presented) and secrets.compare_digest(
        expected.encode("utf-8"), presented.encode("utf-8")
    )
```
```python
# oauth/store.py:362 - deriviert aus dem Installations-Datenschlüssel, nichts wird gespeichert
def form_token(self, flow_id: str) -> str:
    return crypto.form_token(self._key, flow_id)
```
Für die Connections-Formulare: `store.form_token(auth_id)` (Disconnect) bzw.
`store.form_token(nc_user)` oder ein fester Seiten-Handle (Pause/Resume); nie ein eigenes
CSRF-System bauen (Don't Hand-Roll, T-03-50). Bei fehlendem/falschem Wert: dieselbe Antwort
wie "already disconnected" (kein Orakel, `consent.py:398-403` als Vorbild inkl. Log-Warnung).

**Fail-closed Store-Zugriff, nie 500 ins Framework** (`oauth/connect.py:313-329`):
```python
async def _store_or_page(
    store: StoreProvider, env: Mapping[str, str] | None
) -> OAuthStore | Response:
    try:
        return await store()
    except ToolError as exc:
        logger.error("the onboarding has no store: %s %s", exc.message, exc.hint)
        return _generic("the store could not be opened", env)
    except Exception:
        logger.exception("the onboarding could not open its store")
        return _generic("the store could not be opened", env)
```
Plus `_generic`/`_page`-Helfer (`oauth/connect.py:332-347`): E7 mit Referenz, eine Log-Zeile.
E8 kommt als neue Tabellenzeile dazu (siehe errors.py unten).

**Antwort auf die POST ist eine Seite, kein Redirect** (CR-03): `oauth/consent.py:478-480`
begründet es (`form-action 'self'` vs. Redirect nach Form-Submission). S8 rendert die volle
Liste mit Ergebnis-Callout, Status 200. Das `303`-Muster von `oauth/connect.py:240` ist hier
NICHT das Vorbild (UI-SPEC legt die Seiten-Antwort fest, die Resubmit-Zeile "Already
disconnected" existiert genau deshalb).

**Widerruf je Zeile = geteilter Pfad, nie Store direkt** (`oauth/provider.py:739-758`):
```python
async def _end_connection(
    self, store: OAuthStore, *, auth_id: str, family_id: str, now: int
) -> None:
    """Three writes and one call, in this order and never another..."""
    await store.revoke_family(family_id, now=now)
    await store.revoke_authorization(auth_id, now=now)
    await store.note_cleanup(auth_id, now=now)
    self._held.clear()
    self._invalidate()
```
Der Plan hebt das als öffentliches `end_connection(auth_id)` an die Oberfläche
(Pattern 5 der Recherche). Wächter-Signal aus Pitfall 3: ein Import von
`store.revoke_authorization` in einem UI-/Routen-Modul ist der Fehler.
`self._invalidate()` ist der Verifier-Cache (verdrahtet in `entry_exapp.py:92`:
`provider.on_revocation(verifier.invalidate)`); ohne ihn lebt ein widerrufener Token bis zu
5 s weiter (T-03-62).

---

### `src/mcp_connector/exapp/ui/connections.py` (View, S5-S8)

**Analog:** `src/mcp_connector/exapp/ui/connect.py` (Seitenbau) + `exapp/ui/layout.py` (Primitive)

**Pfad- und Feldkonstanten beim Template, Routen importieren sie** (`exapp/ui/connect.py:54-70`):
```python
CONNECT_PATH = "/connect"
WAIT_PATH = "/connect/wait"
FLOW_PARAM = "flow"
ACTION_FIELD = "action"
ACTION_START = "start"
ACTION_CANCEL = "cancel"
```
Für die neue Datei: `CONNECTIONS_PATH = "/connections"`, `ACTION_FIELD`,
`ACTION_CONFIRM/DISCONNECT/PAUSE/RESUME`, `AUTH_PARAM` (Handle als Hidden Field),
`CONFIRM_PARAM` (HMAC), alle in `__all__`.

**Seitenbau ausschließlich über layout.page** (`exapp/ui/connect.py:88-101`):
```python
def invitation_page(*, env: Mapping[str, str] | None = None) -> Response:
    return layout.page(
        strings.CONNECT_TITLE,
        [
            layout.paragraph(strings.CONNECT_BODY.format(host=_host(env))),
            layout.form(
                CONNECT_PATH,
                [layout.button_primary(strings.SIGNIN_CTA, name=ACTION_FIELD, value=ACTION_START)],
                env=env,
            ),
        ],
        env=env,
    )
```
`layout.page` (layout.py:198-282) setzt die fünf Pflicht-Header zentral (`no-store` inkl.,
Pitfall 8), `focus_heading=True` existiert für S7 (layout.py:210, 237-241, wie die
Consent-Seite). Callouts über `layout.callout("warning"|"success", title, body)`
(layout.py:314-327), Detail-Liste S7 über `layout.detail_list` (layout.py:302-311,
Werte monospace, nie gekürzt). Formulare über `layout.form(path, buttons, hidden={...})`
(layout.py:358-387, POST default, Hidden-Felder escaped, `app_path`-Prefix aus der
konfigurierten Public-URL, nie aus dem Request).

**Client-Name ist Angreifer-Input:** vor dem Escapen durch `layout.client_name(raw)`
(layout.py:446, Steuerzeichen raus, Whitespace kollabiert, 80 Zeichen); genau so nutzt es
`exapp/ui/errors.py:110`. Gilt für jeden App-Namen in Zeile, S7-Titel und S8-Callout.

**Host in Texten:** `_host(env)`-Helfer wie `exapp/ui/connect.py:188-191`
(`urlsplit(config.public_url(env)).netloc`), nie der Host-Header (T-03-02).

---

### `src/mcp_connector/exapp/middleware.py` (Schalter-Gate R1)

**Analog:** die eigene Zweigstruktur; das Gate ist ein Einschub, kein Umbau.

**Wo R1 einzuhängen ist** (`exapp/middleware.py:97-113`, Ist-Zustand):
```python
        request = Request(scope)
        try:
            user = require_appapi(request, env=self._env)          # 1. Handshake
        except (AppApiRejected, ToolError):
            response = Response(status_code=401, headers=NO_STORE)  # R3
            await response(scope, receive, send)
            return

        if not user and not await self._bearer_is_valid(request):   # 2. Credential
            response = Response(status_code=401, headers=self._unauthorized_headers())  # R2
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)
        # 3. HIER, vor dem Durchreichen: Schalter-Check (R1), beide Zweige
```
Die aufgelöste Identität des OAuth-Zwiegs liegt nach `_deposit` in
`request.state.<OAUTH_STATE_ATTR>` (middleware.py:136-157, `setattr(request.state,
OAUTH_STATE_ATTR, identity)`); der AUTH-01-Zweig hat `user` direkt. Reihenfolge ist
Sicherheit (Pitfall 2): erst Handshake, dann Credential, dann Schalter; leere Identität
(App-Kontext) wird nie geprüft (Pitfall 10). R1-Antwort: 403, konstanter JSON-Body aus
`strings.py`, `headers=NO_STORE`, KEIN `WWW-Authenticate` (UI-SPEC R1). Der Store-Zugriff
kommt als Konstruktor-Parameter herein, wie `token_verifier` heute
(middleware.py:78-87), verdrahtet nur in `entry_exapp` (siehe unten). Der Read ist
`store.access_disabled(nc_user)`, lokales SQLite, kein Cache (D-47/D-48).

---

### `src/mcp_connector/oauth/store.py` (user_access-Tabelle + User-Query)

**Analog:** die eigenen `authorizations`-Methoden und das Schema-/Migrationsmuster.

**Schema-Erweiterung im SCHEMA-String** (Muster `oauth/store.py:136-204`; neue Tabelle laut
Recherche-Code-Beispiel 4):
```sql
CREATE TABLE IF NOT EXISTS user_access (
  nc_user TEXT PRIMARY KEY,
  disabled_at INTEGER NOT NULL
);
-- kein Eintrag = Zugriff an (D-50 kostenlos); resume = DELETE der Zeile
```
`CREATE TABLE IF NOT EXISTS` im `SCHEMA`-Literal ist die Migration für neue Tabellen
(`_connect` führt es bei jedem Open aus, store.py:1136-1149). `_add_missing_columns`
(store.py:1152-1170) ist nur für neue Spalten bestehender Tabellen nötig, hier also nicht.
Falls `authorizations_of_user` einen Index will: `CREATE INDEX IF NOT EXISTS ... ON
authorizations(nc_user)` in den SCHEMA-String, wie `refresh_family` (store.py:192).

**Write-Methode, exakt die Form von `revoke_authorization`** (store.py:598-608):
```python
async def revoke_authorization(self, auth_id: str, *, now: int | None = None) -> None:
    """Mark the connection as gone. Idempotent: the first revocation time stands."""
    moment = _moment(now)

    def work(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE authorizations SET revoked_at = ? WHERE auth_id = ? AND revoked_at IS NULL",
            (moment, auth_id),
        )

    await self._write(work)
```
`set_access(nc_user, disabled)` schreibt via `INSERT ... ON CONFLICT` bzw. `DELETE`
(Upsert-Vorbild: `save_client`, store.py:385-397). `_write` läuft in `BEGIN IMMEDIATE`
(store.py:1054-1095), `_read` ohne Transaktion; jede Methode öffnet ihre eigene Connection
im Thread (store.py:342-349, Multi-Worker-Regel SRV-05).

**Read-Methode, exakt die Form von `load_authorization`** (store.py:542-562):
```python
async def load_authorization(self, auth_id: str) -> AuthorizationRow | None:
    def work(conn: sqlite3.Connection) -> AuthorizationRow | None:
        row = conn.execute(
            "SELECT auth_id, client_id, nc_user, scopes, resource, created_at, revoked_at, "
            "cleanup_at FROM authorizations WHERE auth_id = ?",
            (auth_id,),
        ).fetchone()
        if row is None:
            return None
        return AuthorizationRow(...)
    return await self._read(work)
```
`access_disabled(nc_user) -> bool` (SELECT 1) und
`authorizations_of_user(nc_user) -> list[AuthorizationRow]` (WHERE nc_user = ? AND
revoked_at IS NULL ORDER BY created_at DESC, S5 "newest first") folgen dieser Form; Rückgabe
als frozen dataclass wie `AuthorizationRow`.

---

### `src/mcp_connector/exapp/settings_form.py` (Link-only-Form-Registrierung)

**Analog:** `src/mcp_connector/exapp/status.py` (komplett, 34-65)

**Der ganze OCS-Call inkl. Fehlermodell** (`exapp/status.py:34-65`):
```python
async def report_init_progress(
    progress: int = 100, *, env: Mapping[str, str] | None = None
) -> None:
    """... Never raises for a transport error."""
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{STATUS_PATH}"
    headers = dict(OCS_HEADERS)
    headers.update(
        appapi_auth_headers(
            "",                              # App-Kontext: leerer User
            app_id=settings.app_id,
            app_version=settings.app_version,
            aa_version=settings.aa_version,
            app_secret=settings.app_secret,
        )
    )
    client = shared_client()
    try:
        response = await client.put(url, json={"progress": progress}, headers=headers)
    except httpx.HTTPError:
        logger.error("the init progress push to %s did not reach Nextcloud", url)
        return
    if response.status_code // 100 != 2:
        logger.error("the init progress push to %s answered %s", url, response.status_code)
```
Für die Settings-Form: gleicher Header-Bau (`appapi_auth_headers` in
`nextcloud/credentials.py:96-122`, base64 `"<user>:<app_secret>"`, nie loggen), gleicher
`shared_client()`, aber `client.post(url, json={"formScheme": FORM_SCHEME}, headers=...)`
gegen `/ocs/v2.php/apps/app_api/api/v1/ui/settings` (gemessen 200, Messprotokoll
04-RESEARCH.md). FORM_SCHEME mit `fields: []`, `doc_url` aus `config.public_url(env)` +
`/connections` (nie der interne Hostname), Titel/Beschreibung aus `strings.py`
(`SETTINGS_TITLE`, `SETTINGS_DESCRIPTION` mit `{connections_url}`-Platzhalter).

---

### `src/mcp_connector/exapp/lifecycle.py` (Registrierung bei /enabled)

**Analog:** der eigene `/init`-Handler (Fire-and-forget) und der `/enabled`-Handler.

**Das Fehlermodell, wörtlich zu übernehmen** (`exapp/lifecycle.py:61-84`):
```python
    async def init(request: Request) -> Response:
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded
        try:
            await status.report_init_progress(INIT_PROGRESS, env=env)
        except Exception:
            # Nothing that happens on the way to Nextcloud may turn this into a 500:
            logger.error("the init progress push failed, the installation may stay below 100")
        return json_response({})

    async def enabled(request: Request) -> Response:
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded
        value = request.query_params.get("enabled", "")
        if value not in ENABLED_VALUES:
            return json_response({"error": "enabled must be 0 or 1"}, status_code=400)
        return json_response({"error": ""})
```
Bei `value == "1"`: `settings_form.register_settings_form(env=env)` im selben
try/except-Modell wie `init` (Pitfall 11: nie 500 aus `/enabled`, ein Log-Eintrag reicht).
Kein Entregistrieren bei `0` (AppAPI blendet deaktivierte Apps selbst aus).

---

### `src/mcp_connector/tools/context.py` (prepare_context)

**Analog:** `src/mcp_connector/tools/search.py` (Fan-out + degraded), `tools/calendar.py`
(Zeitfenster), `tools/chatgpt.py` (Id-Routing für Voll-Auszüge)

**Fan-out mit Timeout je Teilquelle, nie global** (`tools/search.py:89-106`):
```python
    outcomes = await asyncio.gather(
        *(_ask(clients, provider_id, term, capped) for provider_id in selected),
        return_exceptions=True,
    )
    for provider_id, outcome in zip(selected, outcomes, strict=True):
        if isinstance(outcome, BaseException):
            degraded.append({"provider": provider_id, "reason": _reason(outcome)})
            continue
        ...
```
```python
# tools/search.py:162-164 - der Timeout sitzt um den Einzel-Call, nicht um das Bündel
async def _ask(clients: NcClients, provider_id: str, term: str, limit: int) -> dict[str, Any]:
    async with asyncio.timeout(PER_PROVIDER_TIMEOUT):
        return await ocs.provider_search(clients.client, clients.creds, provider_id, term, limit)
```
prepare_context startet parallel: (a) `search_tools.unified_search(clients, query=query,
limit=...)` OHNE `providers`-Einschränkung (D-53, sonst stirbt die Findling-Synergie) und
(b) `calendar.list_events(clients, start, end)` in einem eigenen, ENGEREN
`asyncio.timeout(10)` um den Aufruf (Pitfall 5: `PER_CALENDAR_TIMEOUT = 20.0` in
calendar.py:52 bleibt unverändert, der Cap gehört in context.py). Kein globales
`asyncio.timeout` um `gather` (Pitfall 4).

**Die degraded-Form ist wörtlich zu übernehmen** (`tools/search.py:203-211`):
```python
def _reason(exc: BaseException) -> str:
    """One sentence per failed provider: what happened, never who we are."""
    if isinstance(exc, ToolError):
        return exc.message
    if isinstance(exc, TimeoutError | httpx.TimeoutException):
        return f"The provider did not answer within {PER_PROVIDER_TIMEOUT:g} seconds."
    if isinstance(exc, httpx.RequestError):
        return "The provider could not be reached."
    raise exc
```
Einträge als `{"provider"|"source"|"calendar": name, "reason": satz}` (D-55; die Suche
liefert ihre eigenen `degraded`-Einträge mit, calendar.py:101 nutzt `{"calendar": ...,
"reason": ...}`). Ein gescheiterter Kalender wird `{"source": "calendar", "reason": ...}`.

**Bündeln nach kind, nie nach Provider-Id** (`provider_map.py:37-42`):
```python
PROVIDER_KINDS: Mapping[str, str] = {
    "files": "file",
    "notes": "note",
    # Verified against nextcloud/deck lib/Search/DeckProvider.php. "deck" is wrong.
    "search-deck-card-board": "card",
}
```
Die Treffer von `unified_search` tragen bereits `kind` und `resolvable: False` für
Nicht-Auflösbares (search.py:186-199); context.py bündelt danach (Pitfall 9).

**Voll-Auszüge über das fetch-Routing, keinen eigenen Reader** (`tools/chatgpt.py:97-117`):
```python
async def fetch(clients: NcClients, resource_id: str) -> dict[str, Any]:
    kind, parts = ids.parse(resource_id)
    match kind:
        case "file":
            return await _fetch_file(clients, parts[0])
        case "note":
            return await _fetch_note(clients, parts[0])
        case "card":
            return await _fetch_card(clients, parts)
        case "event":
            return await _fetch_event(clients, parts[0], parts[1])
        case _:
            raise ToolError(message=_UNFETCHABLE, hint=...)
```
Byte-Cap-Vorbild: `MAX_TEXT_BYTES = files_tools.DEFAULT_MAX_BYTES` (chatgpt.py:47-48) und
die Trunkierungs-Notiz IM Text (chatgpt.py:52, 139-143). Für D-54: Top-K auflösbare
Treffer, je max. 2000 Bytes, je 5 s eigener Timeout; ein gescheiterter Auszug wird
degraded-Eintrag, der Treffer bleibt in Kurzform. Für D-57: jeder Treffer trägt Quelle + Id
als Strukturfelder (wie search.py-Hits: `id`, `title`, `provider`, `kind`), Auszüge sind
reine Datenfelder ohne Anweisungs-Rahmung; Guard-Test dazu siehe Tests unten.

**Fehler-/Hint-Konvention:** `ToolError(message=..., hint=...)` mit `_HINT`-Konstanten,
wie search.py:49-54 und calendar.py:54-58. Antwort-`note` wiederverwenden:
`search_tools.SEARCH_NOTE` (search.py:47), keine zweite Formulierung desselben Vorbehalts.

---

### `src/mcp_connector/server/reg_context.py` (Registrierung, Schema-Diät)

**Analog:** `src/mcp_connector/server/reg_search.py` (komplett, 18-36)

```python
@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def unified_search(
    query: Annotated[str, Field(description="Words to search for, e.g. budget 2026")],
    limit: Annotated[
        int, Field(ge=1, le=search_tools.MAX_LIMIT, description="Maximum hits per provider")
    ] = search_tools.DEFAULT_LIMIT,
    providers: Annotated[
        str, Field(description="Comma separated provider ids, e.g. files,notes; empty means all")
    ] = "",
    ctx: Context | None = None,
) -> str:
    """Search the whole Nextcloud across all installed search providers (matches names and metadata, not file contents)."""  # noqa: E501
    clients = deps.resolve_clients(ctx)
    return compact(await search_tools.unified_search(...))
```
Für `prepare_context`: exakt zwei Parameter (`query: str`, `detail: str` mit
`Field(description=...)`; Enum "short"/"full" als String, kein Literal-anyOf: reg_search.py
Docstring erklärt, warum Strings statt Listen/Enums, Schema-Diät D-14). `READ_ONLY`,
`structured_output=False`, `compact(...)`-Serialisierung, `graceful`-Wrapper, alles aus
`server/__init__.py:34-97`. Die Datei registriert sich selbst über den `reg_*`-Autoimport
(`server/__init__.py:100-112`), keine Änderung an `server/__init__.py` nötig.
Die Description muss die D-57-Warnung tragen (Inhalte Dritter möglich) UND unter dem
Token-Budget bleiben: `uv run --no-sync python scripts/check_tool_budget.py`
(Stand 2026-08-17: 10642 von 12500 Bytes, 1858 frei).

---

### `tests/contract/test_tool_surface.py` + README (D-58, in EINEM Zug)

**Analog:** die eigene Datei; vier Berührpunkte, alle exakt lokalisiert.

1. **`EXPECTED_TOOLS`** (Zeile 27-43): `"prepare_context"` eintragen, das eingefrorene
   Literal wächst von 15 auf 16 Namen.
2. **Zähl-Assertions**: Zeile 265 (`len(tools) == 15`) und die Kommentare "15 tools"
   (Zeile 260, 410) bewusst mitziehen.
3. **Eigener Oberflächen-Test** im Stil von `test_unified_search_is_listed_as_a_pure_read...`
   (Zeile 232-255):
```python
    tool = tools["unified_search"]
    annotations = tool.annotations
    assert annotations.read_only_hint is True, "unified_search only reads"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"
    assert "not file contents" in (tool.description or "")
    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"query"}
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"
```
   Für prepare_context zusätzlich: Property-Set == {"query", "detail"}, und die
   D-57-Warnung in der Description asserten.
4. **README-Tabelle**: der Test Zeile 425-444 parst Zeilen der Form
   ``| `name` | read |``; eine Zeile ``| `prepare_context` | read |`` in die bestehende
   Tabelle, sonst rot. `CREATE_TOOLS` (Zeile 46) bleibt unverändert (read-only-Tool).

---

### `src/mcp_connector/exapp/ui/errors.py` (E8)

**Analog:** die eigene `_PAGES`-Tabelle (Zeile 65-81):
```python
_PAGES: dict[str, _ErrorPage] = {
    "E1": _ErrorPage(403, strings.ERROR_ALLOWLIST_TITLE, strings.ERROR_ALLOWLIST_BODY),
    ...
    "E6": _ErrorPage(429, strings.ERROR_THROTTLED_TITLE, strings.ERROR_THROTTLED_BODY),
    GENERIC: _ErrorPage(500, strings.ERROR_GENERIC_TITLE, strings.ERROR_GENERIC_BODY),
}
```
E8 = `_ErrorPage(403, strings.ERROR_SIGN_IN_TITLE, strings.ERROR_SIGN_IN_BODY)` (Body mit
`{host}`-Platzhalter; `error_page` formatiert heute `client/seconds/ref`, der `host`-Fill
muss dazu, kleinste Änderung an `error_page` Zeile 109-113 oder Fill beim Aufrufer).
Keine neue Mechanik, eine Zeile plus Konstanten.

### `src/mcp_connector/exapp/ui/strings.py` (neue Konstanten)

**Analog:** die eigene Datei. Regeln aus dem Docstring (Zeile 1-27): eine Konstante je Satz,
alle in `__all__` (alphabetisch), Platzhalter als `str.format`-Namen, kein Literal in einer
Template-Funktion. Neue Platzhalter dieser Phase: `date`, `connections_url` (UI-SPEC).
Die komplette Konstantenliste steht wörtlich im UI-SPEC ("New string constants"), inklusive
der vier `SWITCH_*`, `SETTINGS_TITLE/DESCRIPTION`, `SETTINGS_PLACE`,
`ACCESS_DISABLED_DESCRIPTION` (R1-Body) und der Wiederverwendungen (`CONNECT_TITLE`,
`CONSENT_DETAIL_APP_NAME` strings.py:211, `CONSENT_DETAIL_CLIENT_ID` strings.py:215,
`CONSENT_IDENTITY`, `WORDMARK`, `FOOTER_PASSWORD_PROMPT`, `CLIENT_NAME_FALLBACK`).

### `src/mcp_connector/exapp/ui/layout.py` (row_list + 3 CSS-Regeln)

**Analog:** `detail_list` (Zeile 302-311) als Form-Vorbild der neuen Primitive:
```python
def detail_list(items: Sequence[tuple[str, str]]) -> str:
    rows = "".join(
        f'<dt>{_escape(term)}</dt><dd class="mono">{_escape(value)}</dd>' for term, value in items
    )
    return f"<dl>{rows}</dl>"
```
`row_list(rows)` baut `<ul class="rows">` mit `<li class="row">` (Titel Body/600,
Sekundärzeilen muted/mono, ein Aktions-Fragment), escaped am einen Punkt (`_escape`,
Zeile 529). Stylesheet: exakt die drei Regeln aus dem UI-SPEC Component Inventory
(`ul.rows`, `li.row`, `.row-title`), keine neue Farbe/Größe/Abstufung. `page()` bleibt
unverändert (UI-SPEC: kein neuer Parameter nötig).

### `src/mcp_connector/entry_exapp.py` (Verdrahtung)

**Analog:** die eigenen zwei Stellen.

**Gate-Parameter an der Wrap-Stelle** (Zeile 99-107):
```python
    for route in app.router.routes:
        if isinstance(route, Route) and route.path == MCP_PATH:
            route.app = RequireAppApi(route.app, env, token_verifier=verifier)
            guarded += 1
    if guarded != 1:
        raise RuntimeError(...)
```
Hier bekommt `RequireAppApi` zusätzlich den Store-Zugriff (denselben `store`-Opener von
Zeile 85, `store = store_opener(env)`), damit Schalter und Tokens aus EINER Datei kommen.

**Routen-Anhängen** (Zeile 131-138): `connections_routes(env, store_provider=store,
end_connection=provider.end_connection, throttle=counters)` in dieselbe Tupel-Schleife.
`lifecycle_routes(env)` braucht ggf. keinen neuen Parameter (settings_form liest env selbst).

### `appinfo/info.xml` (Route 13)

**Analog:** der `^/connect/?$`-Eintrag (Zeile 181-186):
```xml
<route>
    <url>^/connect/?$</url>
    <verb>GET,POST</verb>
    <access_level>PUBLIC</access_level>
    <headers_to_exclude>["AUTHORIZATION-APP-API","EX-APP-ID","EX-APP-VERSION","AA-VERSION","X-ORIGIN-IP"]</headers_to_exclude>
</route>
```
Neue Route: `^/connections/?$`, `GET,POST`, PUBLIC, identisches `headers_to_exclude`.
Pflicht seit AR-02-06: Begründungskommentar im Manifest-Kommentarblock (Zeile 43-148 ist das
Vorbild; der PUBLIC-Grund ist der gemessene CR-01-Absatz von `/authorize/decide`,
Zeile 119-144). Der Kommentar "Exactly twelve routes" (Zeile 43) muss auf dreizehn wandern.

---

## Shared Patterns

### Faktorei + Anhängen nur in entry_exapp (D-23)
**Quelle:** `exapp/lifecycle.py:50`, `oauth/connect.py:103`, `oauth/consent.py:128`,
`entry_exapp.py:131-138`. Gilt für: connections_routes. Kein Decorator auf dem
Server-Singleton, sonst erben stdio/HTTP-Modus die Route.

### Guards geben Responses zurück, nie Exceptions ins Framework
**Quelle:** `oauth/connect.py:313-329` (`_store_or_page`), `exapp/lifecycle.py:93-111`
(`_guard`), `oauth/consent.py:585-620`. Gilt für: alle Connections-Handler. Fail closed =
E7 mit Referenz + eine Log-Zeile (`_generic`, `oauth/connect.py:332-341`).

### Ablehnung nennt die Regel, nie einen Wert aus der Anfrage (T-03-66, T-03-47)
**Quelle:** `oauth/consent.py:398-403` und `417-423` (identische Antwort für
fremd/unbekannt/weg), `exapp/middleware.py:100-104` (kein Detail bei kaputtem Handshake).
Gilt für: S8-Fälle, E8, R1.

### NO_STORE auf jeder Antwort
**Quelle:** `exapp/responses.NO_STORE`, genutzt in `middleware.py:104`, `layout._headers`
(alle Seiten), `lifecycle.py`. Gilt für: R1 explizit (`headers=NO_STORE`), Connections-Seiten
implizit über `layout.page` (Pitfall 8: der PHP-Proxy cacht 3600 s).

### degraded-Liste mit Name und Grund (D-55)
**Quelle:** `tools/search.py:99` + `_reason` 203-211, `tools/calendar.py:101`. Gilt für:
prepare_context. Keine neue Form für dasselbe Problem.

### Tool-Registrierung: READ_ONLY + graceful + compact + Schema-Diät
**Quelle:** `server/__init__.py:52-97`, `server/reg_search.py:18-36`. Gilt für: reg_context.
Budget-Gate: `scripts/check_tool_budget.py` vor jedem Commit.

### Wächter-Tests, die ohne den Fix rot sind
**Quelle (Boundary):** `tests/unit/test_exapp_entry.py:158-346`, baut die App per
`build_exapp_app`, wickelt Routen selbst in `RequireAppApi` mit Test-Verifier (Zeile 125)
und prüft jede Kombination einzeln (u. a. `test_a_verified_bearer_leaves_its_identity...`,
`test_a_token_whose_connection_is_gone_stops_at_the_boundary`). Erweiterung dieser Phase:
die vier Kombinationen User/OAuth x an/aus, plus der End-to-End-Wächter (Schalter auf der
Seite umlegen, nächster tools/call ist R1 mit 403 ohne WWW-Authenticate; ein Test, der nur
den Store-Roundtrip prüft, wäre ohne die Sperre grün und damit keiner).
**Quelle (Seiten):** `tests/unit/test_oauth_consent.py:1-80` (Setup: `TestClient` gegen
`build_exapp_app`, respx für Nextcloud, SQLite in `tmp_path`, ENV-Dict mit
`config.ENV_PUBLIC_URL` etc.) und die Testnamen 163-520 als Stil-Vorbild (ein Satz je Test,
Happy/Fehler/Edge/no_data). Für D-57: Guard-Test, der einen Treffertext mit
Anweisungs-Injection durch prepare_context schickt und assertet, dass er unverändert als
Datenfeld ankommt und keine Struktur/Felder verschiebt.

### Identität und Ownership
**Quelle:** `exapp/auth.py:92-124` (`appapi_user` kollabiert jede Ablehnung in "",
`is_user` mit `compare_digest`, leer matcht nie). Gilt für: E8-Gate, Zeilen-Ownership,
Schalter-POST.

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|-----------|-------|
| keine | - | - | Jede Datei der Phase hat ein direktes Analog im Repo. Der einzige inhaltliche Neubau ohne 1:1-Vorbild ist der formScheme-Payload der Declarative-Settings-Registrierung; dafür steht der gemessene Payload wörtlich in 04-RESEARCH.md (Messprotokoll + Code-Beispiel 1), der Transport-Code hat mit `exapp/status.py` ein exaktes Analog. |

## Metadata

**Analog search scope:** `src/mcp_connector/**` (61 Dateien), `tests/contract/`,
`tests/unit/` (Auswahl), `appinfo/info.xml`
**Files scanned:** 61 Quellcode-Dateien gelistet; 20 gezielt gelesen (kleine komplett,
`store.py`/`provider.py` per Grep-Ortung und Ausschnitt)
**Pattern extraction date:** 2026-08-17
