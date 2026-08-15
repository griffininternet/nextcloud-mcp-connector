<!--
SPDX-FileCopyrightText: 2026 street1983nk
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Phase 3: OAuth 2.1 - Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 36 (22 neu, 11 geaendert, 1 geloescht, 2 optional)
**Analogs found:** 30 / 36 (davon 12 exakt, 18 Rollen-Treffer)

Diese Datei beantwortet genau eine Frage: **woher kopiert jede neue Datei ihr Muster.**
Sie ersetzt nicht 03-RESEARCH.md (was gebaut wird) und nicht 03-UI-SPEC.md (wie es
aussieht), sondern sagt dem Planer, welche existierende Datei der Executor daneben legt.

Grundregel dieses Repos, aus jedem gelesenen Modul ableitbar: **Routen kommen aus einer
Factory, die eine Umgebung als Parameter nimmt, werden von `entry_exapp.build_exapp_app`
und nirgends sonst angehaengt, und jede Antwort traegt `Cache-Control: no-store`.** Wer in
Phase 3 eine Route auf dem geteilten `mcp`-Objekt registriert, bricht D-23.

---

## File Classification

### Neue Module: `src/mcp_connector/oauth/`

| Neue Datei | Rolle | Data Flow | Naechstes Analog | Match |
|------------|-------|-----------|------------------|-------|
| `oauth/__init__.py` | package/barrel | - | `src/mcp_connector/exapp/__init__.py` | exakt |
| `oauth/metadata.py` | route factory / config document | request-response | `src/mcp_connector/exapp/discovery.py` | exakt (Vorgaenger derselben Route) |
| `oauth/consent.py` | route factory / HTML + Poll-Bruecke | request-response | `src/mcp_connector/exapp/lifecycle.py` | Rollen-Treffer (Factory + `_guard`) |
| `oauth/provider.py` | service / SDK-Protocol-Implementierung | request-response | `src/mcp_connector/deps.py` (`StaticBearerVerifier`, `build_auth`) | Rollen-Treffer |
| `oauth/verifier.py` | middleware / TokenVerifier + Prozess-Cache | request-response | `src/mcp_connector/deps.py:93-117` | exakt (dasselbe SDK-Protocol) |
| `oauth/registry.py` | service / Policy-Schalter | CRUD | `src/mcp_connector/config.py` (`select_mode`, `exapp_configured`) | Rollen-Treffer |
| `oauth/store.py` | model / Persistenz (SQLite, WAL) | CRUD | **kein Analog** (kein sqlite3 im Repo); Teilmuster aus `nextcloud/credentials.py` | partiell |
| `oauth/crypto.py` | utility / AESGCM + Schluesselbezug | transform | **kein Analog** (kein `cryptography`-Import im Repo); Teilmuster aus `exapp/auth.py` + `exapp/status.py` | partiell |
| `oauth/loginflow.py` | client / ausgehende Nextcloud-Calls | request-response | `src/mcp_connector/exapp/status.py` | exakt (ein Versuch, kein Retry, kein Secret im Log) |

### Neue Module: `src/mcp_connector/exapp/ui/` (UI-SPEC Component Inventory)

| Neue Datei | Rolle | Data Flow | Naechstes Analog | Match |
|------------|-------|-----------|------------------|-------|
| `exapp/ui/__init__.py` | package/barrel | - | `src/mcp_connector/exapp/__init__.py` | exakt |
| `exapp/ui/layout.py` | component / HTML-Shell + Header | transform | `exapp/discovery.py:94-106` (`_json`-Helfer) fuer die Header-Disziplin; HTML selbst ohne Analog | partiell |
| `exapp/ui/consent.py` | component / S1 bis S4 | request-response | `exapp/lifecycle.py:53-93` | Rollen-Treffer |
| `exapp/ui/errors.py` | component / E1 bis E7 aus einer Tabelle | transform | `nextcloud/clients/ocs.py:219-263` (`_status_error`) | exakt im Muster |
| `exapp/ui/strings.py` | config / alle Nutzertexte | - | `src/mcp_connector/errors.py` + die `_HINT`-Konstanten in `config.py:68-80`, `ocs.py:51-54`, `deps.py:57-61` | Rollen-Treffer |
| `exapp/ui/icons.py` | config / drei SVG-Konstanten | - | kein Analog (trivial, drei Modulkonstanten) | keiner noetig |

### Geaenderte Dateien

| Datei | Rolle | Aenderung | Analog fuer die Aenderung |
|-------|-------|-----------|---------------------------|
| `src/mcp_connector/exapp/middleware.py` | middleware | zweiter Zweig (Bearer) neben AppAPI | sich selbst (`RequireAppApi`, Zeilen 41-66) |
| `src/mcp_connector/entry_exapp.py` | composition root | AS-Routen einhaengen, Waechter-Zaehler erweitern | sich selbst (Zeilen 67-89) |
| `src/mcp_connector/config.py` | config | drei OAuth-Schalter, `APP_PERSISTENT_STORAGE`-Leser, `public_url`-Haertung | sich selbst (Zeilen 35-54, 173-213) |
| `src/mcp_connector/deps.py` | service | fuenfter Credential-Modus `oauth` | sich selbst (Zeilen 64-85, 142-180) |
| `appinfo/info.xml` | config/manifest | D-38: enge Well-known-Routen, neue AS-Routen | sich selbst (Zeilen 42-79) |
| `vulture_whitelist.py` | config | `ENV_APP_PERSISTENT_STORAGE` raus, Provider-Protocol-Methoden rein | sich selbst (Zeilen 31-62) |
| `deploy/Caddyfile` | config | zwei Rewrite-Regeln (Pitfall 2) | sich selbst (`route /exapps/*`) |
| `pyproject.toml` | config | `cryptography` transitiv -> direkt (Owner-Gate, A8) | `docs/dependency-audit.md` + `tests/unit/test_project_layout.py:22-36` |
| `tests/unit/test_exapp_env_setup.py` | test | Manifest-Gate auf die neuen Routen erweitern | sich selbst (Zeilen 93-136, 499-562) |
| `tests/unit/test_exapp_entry.py` | test | Waechter fuer die geschuetzte `/mcp`-Route | sich selbst (Zeilen 81-145) |
| `docs/spike-discovery.md` | doc | Open items abhaken, Proxy-Fallback-Regel festhalten | sich selbst (Zeilen 145-177) |

### Geloescht

| Datei | Grund |
|-------|-------|
| `src/mcp_connector/exapp/discovery.py` | Spike-Artefakt, laut eigenem Docstring "written to be replaced rather than extended"; die Probe-Route `/.well-known/mcp-discovery-probe` verschwindet mit ihr (offener Punkt aus `docs/spike-discovery.md`). `tests/unit/test_exapp_discovery.py` wird zu `tests/unit/test_oauth_metadata.py` umgebaut, nicht geloescht. |

### Neue Tests und Doku

| Neue Datei | Rolle | Data Flow | Naechstes Analog | Match |
|------------|-------|-----------|------------------|-------|
| `tests/unit/test_oauth_metadata.py` | test | request-response | `tests/unit/test_exapp_discovery.py` | exakt (Nachfolger derselben Route) |
| `tests/unit/test_oauth_provider.py` | test | request-response | `tests/unit/test_exapp_auth.py` | exakt |
| `tests/unit/test_oauth_store.py` | test | CRUD | `tests/unit/test_exapp_auth.py` (Leck-Tests) + `tests/unit/test_config.py` | Rollen-Treffer |
| `tests/unit/test_oauth_abuse.py` (D-40) | test | request-response | `tests/unit/test_exapp_auth.py:92-251` (Rejections + Leck-Gates) | exakt |
| `tests/unit/test_oauth_ui.py` | test | transform | `tests/unit/test_exapp_discovery.py:139-167` (Header-Gates) | Rollen-Treffer |
| `tests/unit/test_oauth_loginflow.py` | test | request-response | `tests/unit/test_credentials_http.py` / `test_ocs_capabilities.py` (httpx `MockTransport`) | Rollen-Treffer |
| `tests/integration/test_oauth_flow_exapp.py` | test | request-response | `tests/integration/test_permission_fidelity_exapp.py` | exakt |
| `docs/oauth-setup.md` | doc | - | `docs/exapp-install.md` (Topologie + Evidence + Pitfalls) | exakt |
| `scripts/spike_oauth_e2e.sh` (optional, D-39) | script | - | `scripts/spike_discovery.sh` | exakt |

---

## Pattern Assignments

### `oauth/metadata.py` (route factory, request-response)

**Analog:** `src/mcp_connector/exapp/discovery.py` (106 Zeilen, komplett gelesen). Dies ist
kein entferntes Analog, sondern der direkte Vorgaenger: dieselbe Route, derselbe Zweck,
in Phase 2 live vermessen. Die neue Datei ist die Produktivform davon.

**Importblock** (`discovery.py:34-42`) uebernehmen wie er ist:

```python
from collections.abc import Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .. import config
```

**Factory-Signatur mit Umgebung als Parameter** (`discovery.py:60-67`). Der Parameter ist
nicht Kosmetik: jeder Test baut damit seine eigene App, ohne `os.environ` anzufassen.

```python
def discovery_routes(env: Mapping[str, str] | None = None) -> list[Route]:
    """Build the two spike routes against one environment.
    ...
    The public URL is read from configuration on every request and never derived from the
    request, so a forged ``Host`` header cannot change the metadata (T-02-41).
    """
```

**Konfigurations-statt-Request-Muster** (`discovery.py:69-78`). Das ist der Anti-Pattern-
Punkt aus 03-RESEARCH.md ("Discovery-Dokumente aus dem Request ableiten") in Codeform:

```python
    async def protected_resource(request: Request) -> Response:
        """The RFC 9728 metadata document. Public by contract, configuration only."""
        base = config.public_url(env)
        return _json(
            {
                "resource": f"{base}{_RESOURCE_SUFFIX}",
                "authorization_servers": [],
                "bearer_methods_supported": ["header"],
            }
        )
```

`authorization_servers` bleibt in Phase 3 nicht leer, sondern traegt **genau einen**
Eintrag (Client-Verhalten Claude: nur der erste wird gelesen).

**Der Helfer, der `no-store` unvergesslich macht** (`discovery.py:94-106`), inklusive der
Merge-Reihenfolge, die schon einmal ein Bug war (IN-06):

```python
def _json(
    payload: dict[str, Any],
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """One helper for every answer, so ``no-store`` cannot be forgotten on one branch."""
    return JSONResponse(payload, status_code=status_code, headers={**_NO_STORE, **(headers or {})})
```

**Konsequenz fuer die drei neuen Pfade:** die Route-Liste am Ende der Factory
(`discovery.py:88-91`) waechst auf drei Eintraege
(`/.well-known/oauth-protected-resource/mcp`, `/.well-known/openid-configuration`,
`/.well-known/oauth-authorization-server`), und der `_NO_STORE`-Merge ueberschreibt das
`public, max-age=3600`, das die SDK-Metadaten-Handler setzen (Pitfall 4).

---

### `oauth/consent.py` und `exapp/ui/*` (route factory + HTML, request-response)

**Analog fuer die Routen-Haelfte:** `src/mcp_connector/exapp/lifecycle.py` (123 Zeilen).
Es ist die einzige Datei im Repo, die mehrere Routen mit einem gemeinsamen Guard und
gemeinsamen Antwort-Helfern ausliefert.

**Guard, der eine Response statt einer Exception zurueckgibt** (`lifecycle.py:96-114`).
Genau dieses Muster braucht `/authorize` und `/authorize/status`, damit ein abgelaufener
Flow eine Fehlerseite wird und nie ein 500:

```python
def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    """Return the Nextcloud user id of this request, or the response that ends it.

    A response instead of an exception, so the handlers keep one straight control flow and
    no rejection can escape as a 500.
    """
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        return _json({}, status_code=401)
```

**Aufrufmuster im Handler** (`lifecycle.py:64-76`), das der Executor eins zu eins auf die
Consent-Handler uebertraegt:

```python
    async def init(request: Request) -> Response:
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded
```

**Fehler duerfen den Hauptpfad nicht toeten** (`lifecycle.py:70-76`). Das ist die Vorlage
fuer den Widerruf (App-Passwort loeschen darf den Token-Widerruf nicht blockieren, D-37):

```python
        try:
            await status.report_init_progress(INIT_PROGRESS, env=env)
        except Exception:
            # Nothing that happens on the way to Nextcloud may turn this into a 500:
            # AppAPI aborts the whole installation on a failing /init (pitfall 3).
            logger.error("the init progress push failed, the installation may stay below 100")
        return _json({})
```

**Analog fuer `exapp/ui/errors.py`:** `src/mcp_connector/nextcloud/clients/ocs.py:219-263`.
Eine Funktion, eine Tabelle, ein Rueckgabetyp, jeder Zweig nennt Problem plus naechsten
Schritt. Das ist strukturell exakt die E1-bis-E7-Tabelle der UI-SPEC:

```python
def _status_error(status: int, detail: str, what: str) -> ToolError:
    """One place that turns a Nextcloud status into a sentence the model can act on."""
    suffix = f" Nextcloud says: {detail}" if detail else ""
    if status == 400:
        return ToolError(
            message=f"Nextcloud rejected the request for {what} as invalid.{suffix}",
            hint="Correct the arguments and call the tool again.",
        )
    ...
```

**Analog fuer `exapp/ui/strings.py`:** die `_HINT`-Konstanten des Projekts, jeweils oben im
Modul, ein Name pro Text (`deps.py:57-61`, `ocs.py:51-54`, `config.py:68-80`,
`ids.py:20-23`). Beispiel `deps.py:57-61`:

```python
_BASIC_HINT = (
    "Send an Authorization header with Basic credentials: base64 of "
    "'<nextcloud-user>:<app-password>'. Create the app password in Nextcloud under "
    "Settings, Security, Devices and sessions."
)
```

**Ohne Analog:** HTML-Rendering. Im ganzen Repo gibt es keinen `HTMLResponse` und kein
`text/html` ausserhalb einer Testfixture (`tests/unit/test_ocs_capabilities.py:128`, die
die Nextcloud-Loginseite simuliert). `exapp/ui/layout.py` ist damit die erste HTML-Datei
des Projekts; verbindlich ist dafuer allein 03-UI-SPEC.md. Zu uebernehmen ist nur die
Header-Disziplin des `_json`-Helfers: **eine** Funktion baut jede Seite, damit CSP, Nonce,
`X-Frame-Options` und `no-store` genau eine Quelle haben.

---

### `oauth/provider.py` und `oauth/verifier.py` (service, request-response)

**Analog:** `src/mcp_connector/deps.py`. `StaticBearerVerifier` ist die bereits existierende
Implementierung desselben SDK-Protocols, das `oauth/verifier.py` ersetzt.

**Verifier-Muster** (`deps.py:93-117`), inklusive der beiden Begruendungen, die in Phase 3
unveraendert gelten:

```python
class StaticBearerVerifier:
    """Verify the single configured bearer token of a single-user deployment.

    ``secrets.compare_digest`` instead of ``==``: the comparison runs on attacker
    supplied input, and a short-circuiting comparison leaks the shared prefix over
    enough requests (threat T-01-24). The token is never logged and never echoed.

    The comparison runs on UTF-8 bytes, never on the strings themselves ...
    """

    def __init__(self, token: str) -> None:
        self._token = token.encode("utf-8")

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token or not secrets.compare_digest(token.encode("utf-8"), self._token):
            return None
        return AccessToken(
            token=token,
            client_id=STATIC_BEARER_CLIENT_ID,
            scopes=[],
            subject=STATIC_BEARER_CLIENT_ID,
        )
```

Fuer Phase 3 wird daraus ein Lookup gegen `oauth/store.py` plus Prozess-Cache; die drei
Eigenschaften bleiben: `None` statt Exception bei Misserfolg, `compare_digest` auf Bytes,
Token nie im Log. **Zusaetzlich** (SDK-Luecke, Pitfall 3): `AccessToken.resource` gegen die
eigene Resource pruefen und bei `None` ablehnen.

**SDK-Verdrahtung an einer Stelle** (`deps.py:120-139`). Diese Funktion ist der Ort, an dem
`build_auth` um den OAuth-Modus waechst, und sie enthaelt bereits die Warnung, warum die
beiden SDK-Werte nur zusammen gesetzt werden:

```python
def build_auth(
    env: Mapping[str, str] | None = None,
) -> tuple[StaticBearerVerifier | None, AuthSettings | None]:
    """Return the SDK auth wiring for the configured mode.

    ``(None, None)`` in the passthrough mode: the SDK bearer layer only understands
    ``Bearer`` and would answer 401 to every Basic request before a tool ever runs
    (pitfall 2). Both values set in the static bearer mode, never one of them.
    """
```

**Refusal-Muster fuer den Provider** (`exapp/auth.py:35-42`): eine Exception ohne Nachricht,
weil jede Nachricht dem Angreifer sagt, welche Pruefung gefeuert hat. Der Provider braucht
dasselbe fuer `get_client` (Pitfall 9: gesperrt, abgelaufen und unbekannt sind alle `None`):

```python
class AppApiRejected(Exception):
    """This request is not a valid AppAPI request.

    Carries no message on purpose. Every rejection answers 401 with an empty body ...
    """
```

---

### `oauth/loginflow.py` (client, request-response)

**Analog:** `src/mcp_connector/exapp/status.py` (64 Zeilen, komplett gelesen). Das ist der
einzige ausgehende Nextcloud-Call des ExApp-Pakets und traegt die vollstaendige Fehler-
politik, die D-37 verlangt.

**Ganzes Muster** (`status.py:34-64`):

```python
async def report_init_progress(
    progress: int = 100, *, env: Mapping[str, str] | None = None
) -> None:
    """Tell Nextcloud how far the initialisation got. Never raises for a transport error."""
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{STATUS_PATH}"
    headers = dict(OCS_HEADERS)
    headers.update(
        appapi_auth_headers(
            "",
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
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the init progress push to %s did not reach Nextcloud", url)
        return

    if response.status_code // 100 != 2:
        logger.error("the init progress push to %s answered %s", url, response.status_code)
```

Vier Dinge davon sind fuer `loginflow.py` bindend:

1. **Basis-URL aus `config.exapp_settings(env).base_url`**, nie aus der Antwort. Das ist
   genau Pitfall 7c (der `poll.endpoint` ist eine oeffentliche absolute URL, die der
   Container nicht aufloesen kann).
2. **`shared_client()` aus `nextcloud/http.py`**, kein eigener Client. Der hat bereits
   `follow_redirects=False` und Timeouts (`http.py:26-38`).
3. **Ein Versuch, kein Retry**, und der Fehler wird geloggt, nicht geworfen (D-37).
4. **Kein Wert aus dem Request im Logsatz**, weil die Header das Secret tragen.

**Fuer die OCS-Header und das Widerrufs-Delete** zusaetzlich `nextcloud/clients/ocs.py:40-43`:

```python
OCS_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Accept": "application/json",
}
```

Fuer `DELETE /ocs/v2.php/core/apppassword` gilt laut 03-RESEARCH.md Code-Beispiel 3: 200 und
401 sind **beide** Erfolg. Das ist eine bewusste Abweichung von `ocs.py:179-186`, wo 401 ein
`ToolError` ist, und gehoert als Kommentar in den Code, sonst sieht es nach Schlamperei aus.

---

### `oauth/registry.py` (service, CRUD)

**Analog:** `src/mcp_connector/config.py`. Die drei Schalter aus 03-RESEARCH.md
(`NC_MCP_OAUTH_DCR`, `NC_MCP_OAUTH_ALLOWLIST_ONLY`, `NC_MCP_OAUTH_ALLOWED_CLIENTS`) folgen
exakt dem dort etablierten Muster.

**Konstantenblock** (`config.py:35-54`): jeder Env-Name ist eine Modulkonstante, nie ein
Stringliteral am Verwendungsort.

```python
ENV_ALLOWED_HOSTS = "NC_MCP_ALLOWED_HOSTS"
ENV_STATIC_BEARER = "NC_MCP_STATIC_BEARER"
ENV_DISABLE_DNS_REBINDING = "NC_MCP_DISABLE_DNS_REBINDING_PROTECTION"
ENV_PUBLIC_URL = "NC_MCP_PUBLIC_URL"
```

**Leerer Wert gilt als nicht gesetzt** (`config.py:179-188`), samt Begruendung, die fuer
einen Sicherheitsschalter noch staerker gilt:

```python
def exapp_configured(env: Mapping[str, str] | None = None) -> bool:
    """True when this process was deployed as an ExApp, by the same rule as the bearer.

    A blank value counts as unset: an empty ``APP_SECRET`` in a compose file is a typo,
    not a request to authenticate everyone.
    """
    source = os.environ if env is None else env
    app_id = (source.get(ENV_APP_ID) or "").strip()
    app_secret = (source.get(ENV_APP_SECRET) or "").strip()
    return bool(app_id) and bool(app_secret)
```

**Boolean-Schalter** (`config.py:66` und `236-240`), fuer `NC_MCP_OAUTH_DCR` zu spiegeln,
mit umgekehrter Default-Richtung (DCR ist an, bis jemand es abschaltet):

```python
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

def dns_rebinding_protection(env: Mapping[str, str] | None = None) -> bool:
    """Whether the Host header check stays armed. Off only behind a trusted proxy."""
    source = os.environ if env is None else env
    value = (source.get(ENV_DISABLE_DNS_REBINDING) or "").strip().lower()
    return value not in _TRUE_VALUES
```

**Kommagetrennte Liste parsen** (`config.py:216-233`, `allowed_hosts`) ist die Vorlage fuer
`NC_MCP_OAUTH_ALLOWED_CLIENTS`: trennen, strippen, Leereintraege verwerfen, Duplikate
unterdruecken, dokumentierter Default statt stillem SDK-Default.

---

### `oauth/store.py` (model/persistence, CRUD)

**Kein Analog.** Im Repo existiert kein `sqlite3`, kein `to_thread` und keine Datei, die
etwas ueber einen Prozessneustart hinweg schreibt. Der Planer nimmt das Schema aus
03-RESEARCH.md ("Token-Store: Schema-Vorschlag") und Code-Beispiel 4 (atomare Einloesung
mit `BEGIN IMMEDIATE`).

Uebernehmbar sind trotzdem drei Muster aus dem Repo:

**Maskierter, unveraenderlicher Datensatz** (`nextcloud/credentials.py:23-61`). Jede
Store-Zeile, die ein Geheimnis traegt, ist so zu bauen:

```python
@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    base_url: str
    user: str
    secret: str
    mode: str = MODE_BASIC
    ...

    def __repr__(self) -> str:
        return (
            f"Credentials(base_url={self.base_url!r}, user={self.user!r}, "
            f"mode={self.mode!r}, secret='***')"
        )
```

**Kein Default-Zweig bei einer Modus-Entscheidung** (`credentials.py:43-55`). Direkt
uebertragbar auf `refresh_tokens.state` (`active` / `used` / `revoked`): ein unbekannter
Zustand wirft, statt still als `active` durchzugehen.

```python
    def auth(self) -> httpx.Auth:
        """Return the ``httpx.Auth`` of this mode, one fresh object per call.

        No default branch and no fallback: an unknown mode raises instead of quietly
        authenticating with Basic (D-27).
        """
        if self.mode == MODE_APPAPI:
            return AppApiAuth(self)
        if self.mode == MODE_BASIC:
            return httpx.BasicAuth(self.user, self.secret)
        raise ValueError(f"unknown credential mode {self.mode!r}, expected one of {MODES}")
```

**Fail-closed beim Start mit benanntem Fehler** (`config.py:248-253`). Fuer den Store-Pfad
aus `APP_PERSISTENT_STORAGE` (Pitfall 12) und den fehlenden Schluessel (Pitfall 11) ist das
die Vorlage; `entry_exapp.main:134-138` zeigt, wie daraus ein `SystemExit(2)` wird.

```python
def _required_exapp(source: Mapping[str, str], name: str) -> str:
    """Like :func:`_required`, but with the hint an ExApp operator can act on."""
    value = (source.get(name) or "").strip()
    if not value:
        raise ToolError(message=f"{name} is not set.", hint=_EXAPP_HINT)
    return value
```

---

### `oauth/crypto.py` (utility, transform)

**Kein Analog fuer die Krypto selbst.** `cryptography` wird im Repo nirgends importiert
(nur transitiv im Lock), `hashlib` ebenso wenig. Verbindlich sind 03-RESEARCH.md
(AESGCM mit `aad=auth_id`, D-43) und die Alternatives-Tabelle dort.

**Uebernehmbar ist die Geheimnis-Hygiene aus `exapp/auth.py`** (116 Zeilen, komplett
gelesen), Zeilen 114-116 und der Modul-Docstring:

```python
def _same(received: str, expected: str) -> bool:
    """Constant time comparison on UTF-8 bytes, never on the strings themselves."""
    return secrets.compare_digest(received.encode("utf-8"), expected.encode("utf-8"))
```

und (`auth.py:60-64`) das Muster, wie ein kaputter Wert behandelt wird, ohne ihn zu zitieren:

```python
    try:
        decoded = base64.b64decode(raw_auth, validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        # The offending value is credential material and stays out of the exception.
        raise AppApiRejected from None
```

**Der Schluesselbezug** (`POST /ocs/v2.php/apps/app_api/api/v1/ex-app/config` mit
`sensitive=1`) ist ein ausgehender OCS-Call und folgt damit exakt `exapp/status.py`
(siehe `oauth/loginflow.py` oben): `OCS_HEADERS` plus `appapi_auth_headers("")` im
App-Kontext, `shared_client()`, ein Versuch. Unterschied: hier ist ein Fehlschlag
**nicht** verzeihbar. Ohne Schluessel wird der Start abgebrochen (Pitfall 11), Muster
`entry_exapp.main:134-138`.

---

### `exapp/middleware.py` (middleware, request-response) - GEAENDERT

**Analog:** die Datei selbst (66 Zeilen). Pattern 4 aus 03-RESEARCH.md ("Zwei
Identitaetsquellen an einer Transportgrenze") wird genau hier eingebaut. Der bestehende
Rahmen bleibt, es kommt ein Zweig dazu.

**Bestehender Rahmen** (`middleware.py:41-66`):

```python
class RequireAppApi:
    """Verify the AppAPI handshake before any MCP code runs."""

    def __init__(self, app: ASGIApp, env: Mapping[str, str] | None = None) -> None:
        self._app = app
        self._env = env

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        try:
            require_appapi(Request(scope), env=self._env)
        except (AppApiRejected, ToolError):
            response = Response(status_code=401, headers=_NO_STORE)
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)
```

Zwei Punkte, die die Aenderung nicht kaputt machen darf:

- Der Nicht-HTTP-Zweig (Zeilen 49-54) bleibt, sonst startet der Session-Manager nicht.
- Der Rueckgabewert von `require_appapi` wird heute verworfen. Ab Phase 3 entscheidet er:
  **nicht leerer Nutzer** -> bestehender AUTH-01-Pfad, kein Bearer wird gelesen;
  **leerer Nutzer** -> Bearer gegen den Verifier, sonst 401 mit `WWW-Authenticate`.
  Der 401 dieses Zweiges braucht anders als heute einen Header; die Formatvorlage steht in
  03-RESEARCH.md Code-Beispiel 2 und in `discovery.py:80-86`:

```python
        headers = dict(_NO_STORE)
        headers["WWW-Authenticate"] = f'Bearer resource_metadata="{metadata_url}"'
```

---

### `entry_exapp.py` (composition root) - GEAENDERT

**Analog:** die Datei selbst (`build_exapp_app`, Zeilen 49-89).

**Waechter, den Pitfall 6 verlangt** (Zeilen 72-81). Er zaehlt heute die geschuetzten
`/mcp`-Routen und wirft bei allem ausser genau einer. Die Manifest-Umstellung auf PUBLIC
und der neue Wrapper gehoeren in denselben Task, und dieser Zaehler ist der Beweis:

```python
    guarded = 0
    for route in app.router.routes:
        if isinstance(route, Route) and route.path == MCP_PATH:
            route.app = RequireAppApi(route.app, env)
            guarded += 1
    if guarded != 1:
        raise RuntimeError(
            f"the ExApp application has {guarded} guarded {MCP_PATH} routes instead of one; "
            "the MCP transport would be served without the AppAPI handshake"
        )
```

**Anhaengen der Factory-Routen** (Zeilen 87-88). Hier kommen die AS-Routen dazu, und
nirgends sonst:

```python
    for route in (*lifecycle_routes(env), *discovery_routes(env)):
        app.router.routes.append(route)
    return app
```

**Anti-Pattern aus 03-RESEARCH.md, das hier greifbar wird:** `auth_server_provider=` am
`MCPServer`-Konstruktor haengt die AS-Routen an die MCP-App. Diese Schleife ist der Grund,
warum das nicht passt: die AS-Routen kommen aus `create_auth_routes` und werden wie
`lifecycle_routes` angehaengt, der Verifier separat gesetzt.

---

### `appinfo/info.xml` (manifest) - GEAENDERT (D-38)

**Analog:** die Datei selbst, Zeilen 42-79. Der Kommentarblock ueber den Routen ist Teil des
Musters, nicht Dekoration: er benennt je Regel die Bedrohung.

```xml
		<routes>
			<route>
				<url>^/mcp/?$</url>
				<verb>GET,POST,DELETE</verb>
				<access_level>USER</access_level>
				<headers_to_exclude>["AUTHORIZATION-APP-API","EX-APP-ID","EX-APP-VERSION","AA-VERSION","X-ORIGIN-IP"]</headers_to_exclude>
			</route>
			<route>
				<url>^/\.well-known/</url>
				<verb>GET</verb>
				<access_level>PUBLIC</access_level>
				<headers_to_exclude>["AUTHORIZATION-APP-API","EX-APP-ID","EX-APP-VERSION","AA-VERSION","X-ORIGIN-IP"]</headers_to_exclude>
			</route>
		</routes>
```

Vier Regeln, die aus der bestehenden Datei folgen und fuer jede neue Route gelten:

1. `headers_to_exclude` traegt **immer** alle fuenf Namen (WR-01, IN-01).
2. `access_level` von `/mcp` wechselt auf PUBLIC (Spike Open item), `authorize` ist PUBLIC,
   `token`/`register`/`revoke` sind PUBLIC ohne Nutzer-Session (D-38).
3. Kein `bruteforce_protection` auf 401, der Kommentar dazu steht bereits Zeilen 56-58.
4. Jede Well-known-Route wird voll verankert (`^...$`, Pitfall 14), weil HaRP mit
   `re.match` prueft und ein Muster ohne `$` auch Praefixe trifft.

---

### `deps.py` (service) - GEAENDERT: der fuenfte Credential-Modus

**Analog:** die Datei selbst, Zeilen 64-85. Die Naht ist bereits da, der neue Modus haengt
sich in dieselbe Verzweigung. Kein Tool-Code wird angefasst (D-26).

```python
def resolve_credentials(ctx: Any) -> Credentials:
    """Return the credentials for this call, from the one source this mode allows."""
    headers = getattr(ctx, "headers", None) if ctx is not None else None
    mode = config.select_mode(headers=headers)

    if mode == "exapp":
        return _credentials_from_appapi(headers or {})

    if mode == "http_passthrough":
        return _credentials_from_basic(headers or {})

    return load_stdio_credentials()
```

**Vorlage fuer `_credentials_from_oauth`:** `_credentials_from_appapi` (Zeilen 142-180).
Zwei Absagen und kein dritter Pfad; Basis-URL aus der Konfiguration, nie aus dem Request:

```python
    # The base URL is the one AppAPI deployed us against, never a value from the request.
    return Credentials(
        base_url=settings.base_url,
        user=user,
        secret=settings.app_secret,
        mode="appapi",
        ...
    )
```

Der OAuth-Modus baut daraus `Credentials(base_url=settings.base_url, user=nc_user,
secret=<entschluesseltes App-Passwort>, mode=MODE_BASIC)`, denn gegenueber Nextcloud ist ein
App-Passwort Basic-Auth. `credentials.py:18-20` (`MODE_BASIC`, `MODE_APPAPI`, `MODES`)
bleibt damit unveraendert; ein dritter `MODE_*`-Eintrag waere falsch.

**Der Docstring von `deps.py:20-25` ist eine Warnung, die Phase 3 aktiv aendert:**

```python
In the ExApp mode the identity comes from ``AUTHORIZATION-APP-API`` and from nowhere
else. An ``Authorization`` header that arrives with the same request is not read ...
```

Dieser Absatz muss mitgeaendert werden, sonst beschreibt er das Gegenteil des neuen
Verhaltens. Die neue Formulierung folgt Pattern 4: der Bearer wird **nur** gelesen, wenn
der AppAPI-Nutzer leer ist, und es gibt weiterhin keinen Fallback in beide Richtungen (D-27).

---

## Test Patterns

### `tests/unit/test_oauth_metadata.py`

**Analog:** `tests/unit/test_exapp_discovery.py` (188 Zeilen, komplett gelesen). Diese Datei
wird umgebaut, nicht neu erfunden.

**Fixture-Kopf mit einer Env-Konstante** (Zeilen 24-42):

```python
PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
APP_SECRET = "a8e934cd9e8d19e49db290ab1e529f4d9fed314388579d612eb01644beb7cacc"

ENV = {
    config.ENV_PUBLIC_URL: PUBLIC_URL,
    config.ENV_APP_ID: "mcp_connector",
    ...
}

def client() -> TestClient:
    """A fresh app per call: one Starlette instance is one lifespan."""
    return TestClient(Starlette(routes=discovery.discovery_routes(ENV)))
```

**Mengengleichheit statt Teilmenge** (Zeilen 73-88). Das ist das schaerfste Muster im Repo
und gehoert auf jedes ausgelieferte Metadaten-Dokument:

```python
def test_metadata_leaks_nothing_but_the_public_url_and_the_method_list() -> None:
    """T-02-40: no secret, no request host, no version, no configuration. Set equality."""
    with client() as http:
        response = http.get(METADATA_PATH, headers={"Host": "attacker.example"})
    body = response.text
    assert set(json.loads(body)) == {
        "resource",
        "authorization_servers",
        "bearer_methods_supported",
    }
    assert APP_SECRET not in body
    assert "attacker.example" not in body
```

**Gefaelschter Host aendert nichts** (Zeilen 90-95) und **fremder Authorization-Header
aendert nichts** (Zeilen 45-52 plus 98-104) sind beide direkt zu uebernehmen.

**Verdrahtungstest gegen die Phase-1-Modi** (Zeilen 180-188). Er muss die neuen AS-Routen
mitpruefen, sonst waechst der Standalone-HTTP-Server heimlich einen `/token`-Endpunkt:

```python
def test_the_standalone_http_app_knows_neither_route() -> None:
    """D-23: phase 1 modes must not grow a .well-known route. Empty list, not a subset."""
    app = entry_http.build_app({config.ENV_URL: "http://nc.test"})
    well_known = [...]
    assert well_known == []
```

### `tests/unit/test_oauth_abuse.py` (die D-40-Missbrauchstests)

**Analog:** `tests/unit/test_exapp_auth.py:92-251`. Drei Bausteine:

**Parametrisierte Ablehnungen** statt einzelner Testfunktionen (Zeilen 94-141), eine Zeile
pro Missbrauchsfall.

**Der Echo-Test** (Zeilen 216-233), auf Refresh-Token und Authorization-Code zu spiegeln:

```python
def test_no_rejection_ever_repeats_the_header(raw: str) -> None:
    """T-02-03: the header is credential material, not text we may quote back."""
    ...
    except auth.AppApiRejected as exc:
        text = f"{exc} {exc.args!r}"
        assert raw not in text
```

**Der caplog-Leck-Test** (Zeilen 236-243). Fuer Phase 3 die wichtigste Einzelzeile im ganzen
Repo, weil der Store Token, App-Passwoerter und den Datenschluessel anfasst:

```python
def test_verification_writes_nothing_to_the_log(caplog: pytest.LogCaptureFixture) -> None:
    """T-02-03: not on DEBUG, not truncated, not the successful case either."""
    with caplog.at_level(logging.DEBUG):
        ...
    assert APP_SECRET not in caplog.text
    assert caplog.text.strip() == ""
```

**Das Quelltext-Gate** (Zeilen 246-250). Es prueft eine Eigenschaft, die kein Verhaltenstest
sieht, und ist die Vorlage fuer "der Store schreibt nie einen Klartext-Token":

```python
def test_the_verifier_compares_in_constant_time() -> None:
    """T-02-02: a plain == leaks the shared prefix of the secret over enough requests."""
    source = inspect.getsource(auth)
    assert source.count("compare_digest") >= 2, "app id and secret are both compared"
    assert " == " not in source.split("def verify_appapi_headers", 1)[1].split("def ", 1)[0]
```

### `tests/unit/test_exapp_env_setup.py` (Waechter-Kultur) - GEAENDERT

**Analog:** die Datei selbst. Das Manifest-Gate ist eine Funktion ueber einen geparsten
Baum, keine Kette von Asserts, damit ein Gegenprobe-Test ein absichtlich kaputtes Manifest
durchschicken kann (Zeilen 93-136):

```python
def manifest_problems(root: etree._Element) -> list[str]:
    """Return every reason this manifest must not be shipped, empty list when it is fine.

    A function instead of a row of asserts, because a gate that was never seen failing is
    not a gate.
    """
    problems: list[str] = []
    ...
    routes = root.findall(".//route")
    if len(routes) != 2:
        problems.append(f"{len(routes)} routes declared, this phase opens exactly two")

    for route in routes:
        url = (route.findtext("url") or "").strip()
        ...
        if url in WIDE_URLS:
            problems.append(f"route {url!r} matches everything")
        for header in PROXY_OWNED_HEADERS:
            if f'"{header}"' not in excluded:
                problems.append(f"route {url!r} does not have {header} stripped by the proxy")
        if access_level == "PUBLIC" and not url.startswith("^/"):
            problems.append(f"public route {url!r} is not anchored at a path")
```

**Gegenprobe** (Zeilen 518-531): das Gate bekommt eine kaputte Route und muss feuern.

Aenderungen, die Phase 3 hier zwingend braucht:

- `test_the_manifest_declares_exactly_the_two_routes_of_this_phase` (Zeile 499) und die
  Zaehlung `!= 2` in `manifest_problems` wachsen auf die neue Routenliste.
- Neue Pruefung aus Pitfall 14: jede PUBLIC-Well-known-Route ist **voll** verankert
  (`url.endswith("$")`), plus verbotene Nachbarn
  (`/.well-known/oauth-protected-resource/mcpx`, `/.well-known/`, Doppel-Slash).
- Neue Pruefung: die Manifest-Routen und die tatsaechlich registrierten Starlette-Pfade aus
  `build_exapp_app(ENV)` stimmen ueberein (Mengengleichheit, kein Subset).

### `tests/integration/test_oauth_flow_exapp.py`

**Analog:** `tests/integration/test_permission_fidelity_exapp.py` (276 Zeilen; Kopf gelesen).
Zu uebernehmen sind Marker, Ausfuehrungsanleitung im Docstring und die Prueforder.

```python
pytestmark = [pytest.mark.integration, pytest.mark.anyio]

# The app id is frozen (docs/app-id-freeze.md); the HaRP route never changes, so it is a
# literal here.
EXAPP_MCP_PATH = "/exapps/mcp_connector/mcp"
```

Skip-Muster ohne Topologie: `tests/conftest.py:39-68` (`exapp_env`-Fixture) mit benannter
fehlender Variable, plus `pytest_collection_modifyitems` (Zeilen 71-86). Damit bleibt die
Standard-Suite ohne Docker gruen (D-32).

### `docs/oauth-setup.md`

**Analog:** `docs/exapp-install.md` (340 Zeilen). Uebernommen wird die Gliederung, nicht der
Inhalt: `## Topology`, `## Install`, `## Evidence` (nummerierte, nachvollziehbare Beweise
mit echten Kommandos und Antworten), `## Known pitfalls`, `## Security notes for
production`, `## Related` mit relativen Links. `docs/spike-discovery.md` liefert zusaetzlich
das Muster fuer den Messmatrix-Abschnitt, den die Discovery-Topologie-Tabelle aus
03-RESEARCH.md fuellt.

---

## Shared Patterns

### 1. `Cache-Control: no-store` auf jeder Antwort

**Quelle:** `exapp/discovery.py:57` und `:94-106`, `exapp/lifecycle.py:48` und `:117-119`,
`exapp/middleware.py:38`.
**Anwenden auf:** jede neue Route dieser Phase, HTML wie JSON, Erfolg wie Fehler.

```python
#: On every answer of this module, including the 401. The PHP proxy caches JSON for 3600
#: seconds unless the answer says otherwise (pitfall 4, T-02-42).
_NO_STORE = {"Cache-Control": "no-store"}
```

Drei Module halten heute jeweils ihre eigene Kopie dieser Konstante, mit der ausdruecklichen
Begruendung, dass `discovery.py` in einem Stueck loeschbar bleiben soll. Phase 3 loescht
`discovery.py`; damit faellt die Begruendung fuer die Vervielfachung weg. Der Planer sollte
**eine** Quelle daraus machen (Kandidat: `exapp/ui/layout.py` fuer HTML, ein gemeinsamer
Helfer fuer JSON), sonst haelt Phase 3 fuenf Kopien statt drei.

Zusaetzlich in Phase 3: die SDK-Metadaten-Handler setzen `public, max-age=3600`, die
DCR-Antwort setzt gar nichts (Pitfall 4). Eine ASGI-Middleware ueber allen AS-Routen
ueberschreibt beides. Vorlage fuer eine ASGI-Middleware, die selbst antwortet:
`exapp/middleware.py:48-66`.

### 2. Konfiguration statt Request

**Quelle:** `exapp/discovery.py:60-78`, `deps.py:217-220`, `config.py:210-213`.
**Anwenden auf:** `oauth/metadata.py`, `oauth/consent.py`, `oauth/loginflow.py`, jede
Stelle, die eine oeffentliche URL oder eine Nextcloud-Basis braucht.

```python
    # The base URL stays a deployment decision. A client that could pick the target
    # instance could aim this server, and the credentials, at a host of its choosing.
    return Credentials(base_url=config.load_base_url(), user=user, secret=secret)
```

Der Test dazu existiert bereits (`test_exapp_discovery.py:90-95`) und ist zu kopieren.

### 3. Ablehnung ohne Hinweis, Fehler ohne Echo

**Quelle:** `exapp/auth.py:35-42` (Exception ohne Nachricht), `exapp/auth.py:60-64`
(kaputter Wert wird nicht zitiert), `exapp/middleware.py:58-63`, `exapp/lifecycle.py:106-114`.
**Anwenden auf:** Provider, Verifier, Store, alle AS-Routen.

Fuer die UI gilt dieselbe Regel in anderer Sprache, UI-SPEC Copy-Regeln: kein OAuth-
Fehlercode, kein Parametername, kein Token-Fragment im Seitentext. `{ref}` in E7 ist die
projektuebliche Aufloesung: eine Zufalls-ID, die nur mit einer Logzeile korreliert.

### 4. Kein Retry gegen Nextcloud

**Quelle:** `exapp/status.py:34-64`, `nextcloud/credentials.py:64-75` (`AppApiAuth` hat
bewusst keinen Retry-Zweig), `nextcloud/http.py:1-10` (`follow_redirects=False`),
`deps.py:10-16`.
**Anwenden auf:** `oauth/loginflow.py` (Init, Poll, App-Passwort loeschen), Schluesselbezug
in `oauth/crypto.py`.

```python
    Stateless by construction: the headers are built once in the constructor and the flow
    yields exactly once. There is no retry branch, because a retry would replay an
    impersonation blindly against an instance that already refused it, and Nextcloud
    counts authentication failures per source IP for every user of this server.
```

### 5. Factory-Routen, angehaengt an genau einer Stelle

**Quelle:** `exapp/lifecycle.py:1-22` (Docstring erklaert die Entscheidung),
`exapp/discovery.py:29-31`, `entry_exapp.py:82-88`, `exapp/__init__.py:1-15`.
**Anwenden auf:** `oauth/metadata.py`, `oauth/consent.py` und die Routen aus
`create_auth_routes`.

```python
Importing this package has no side effects: no route registration, no environment read,
no client creation.
```

Der Testbeweis dazu ist `test_exapp_discovery.py:180-188` (leere Liste, kein Subset).

### 6. Maskierte Container und keine Secrets in Logs

**Quelle:** `config.py:83-102` (`ExAppSettings.__repr__`), `nextcloud/credentials.py:57-61`
und `:92-93`, `nextcloud/http.py:41-57` (`httpx`/`httpcore` auf WARNING, weil ihre Records
URLs enthalten).
**Anwenden auf:** jede Store-Zeile, den Provider-State, die Policy-Objekte.

```python
    def __repr__(self) -> str:
        return (
            f"ExAppSettings(app_id={self.app_id!r}, app_version={self.app_version!r}, "
            f"aa_version={self.aa_version!r}, base_url={self.base_url!r}, app_secret='***')"
        )
```

### 7. Fail-closed beim Start, benannter Fehler, Exit 2

**Quelle:** `entry_exapp.py:120-160`, `config.py:248-267`, `errors.py:9-15`.
**Anwenden auf:** fehlender Datenschluessel (Pitfall 11), fehlendes oder nicht schreibbares
`APP_PERSISTENT_STORAGE` (Pitfall 12), widerspruechliche OAuth-Schalter.

```python
    try:
        config.exapp_settings()
    except ToolError as exc:
        logger.error("%s %s", exc.message, exc.hint)
        raise SystemExit(2) from None
```

Und das Muster fuer eine Variable, die es in diesem Modus nicht geben darf
(`entry_exapp.py:42-44` plus `:124-132`) ist die Vorlage, falls DCR-Schalter und
Allowlist-Modus je in einen unmoeglichen Zustand geraten koennen.

### 8. Shell-Muster fuer Skripte und den Bootstrap

**Quelle:** `scripts/bootstrap_exapp.sh:103-117` (`occ_stdin` / `occ_pw`: jedes Secret geht
durch stdin, nie durch argv), `:251-259` (`require_hex64`), `:119-134` (kein `grep -q` auf
einer Pipe).
**Anwenden auf:** jeden Bootstrap-Schritt, der den neuen 32-Byte-Schluessel setzt oder
Allowlist-Eintraege schreibt.

```bash
require_hex64() {
  local name="$1" value="$2" origin="$3"
  if ! printf '%s' "$value" | grep -Eq '^[0-9a-f]{64}$'; then
    echo "ERROR: ${name} in ${origin} is not 64 lower case hex characters." >&2
    ...
```

Die zugehoerigen Waechter-Tests stehen in `tests/unit/test_exapp_env_setup.py:760-800`
(kein Secret im Prozesslisting, Secrets durch stdin, kein `grep -q` auf einer Pipe) und
gelten unveraendert weiter.

---

## No Analog Found

| Datei | Rolle | Data Flow | Grund |
|-------|-------|-----------|-------|
| `oauth/store.py` | model | CRUD | Kein `sqlite3`, kein `to_thread`, keine persistente Datei im Repo. Quelle: 03-RESEARCH.md "Token-Store: Schema-Vorschlag" plus Code-Beispiel 4 (`BEGIN IMMEDIATE`). Uebernommen werden nur die Datensatz- und Fail-closed-Muster oben. |
| `oauth/crypto.py` | utility | transform | Kein `cryptography`- und kein `hashlib`-Import im Repo. Quelle: 03-RESEARCH.md (AESGCM mit `aad=auth_id`, D-43) und die Alternatives-Tabelle. |
| `exapp/ui/layout.py` | component | transform | Kein HTML im Repo (`HTMLResponse` und `text/html` kommen nur in einer Testfixture vor, `tests/unit/test_ocs_capabilities.py:128`). Quelle: 03-UI-SPEC.md, verbindlich fuer CSP, Nonce, Farben, Typografie, Fokus. |
| `exapp/ui/icons.py` | config | - | Drei Modulkonstanten, kein Muster noetig. |
| `oauth/provider.py` (SDK-Verdrahtung) | service | request-response | Fuer `create_auth_routes` und `OAuthAuthorizationServerProvider` gibt es im Repo kein Vorbild. Referenz ist der installierte Quelltext: `.venv/Lib/site-packages/mcp/server/auth/provider.py:137-310` (elf async-Methoden) und `.venv/Lib/site-packages/mcp/server/auth/routes.py:67`, `:152`, `:220`. Das Verifier-Teilstueck hat mit `deps.StaticBearerVerifier` sehr wohl ein Analog. |
| Refresh-Rotation, Reuse-Detection | service | CRUD | Kein Vorbild im Repo, kein Vorbild im SDK (Docstring sagt nur "SHOULD rotate"). Quelle: 03-RESEARCH.md Pitfall 10 und Code-Beispiel 4, D-41 (Gnadenfenster). |

---

## Metadata

**Analog search scope:** `src/mcp_connector/**`, `tests/unit/**`, `tests/integration/**`,
`appinfo/`, `scripts/`, `docs/`, `deploy/`, `vulture_whitelist.py`, plus der installierte
SDK-Quelltext unter `.venv/Lib/site-packages/mcp/server/auth/` (nur Signaturen, zur
Abgrenzung "was ist schon da").

**Files fully read:** `CLAUDE.md`, `src/mcp_connector/config.py`, `deps.py`, `errors.py`,
`entry_exapp.py`, `exapp/__init__.py`, `exapp/auth.py`, `exapp/discovery.py`,
`exapp/lifecycle.py`, `exapp/middleware.py`, `exapp/status.py`, `nextcloud/credentials.py`,
`nextcloud/http.py`, `nextcloud/clients/ocs.py`, `appinfo/info.xml`, `deploy/Caddyfile`,
`vulture_whitelist.py`, `tests/conftest.py`, `tests/unit/test_exapp_discovery.py`; gezielt
gelesen: `tests/unit/test_exapp_auth.py` (213-251), `tests/unit/test_exapp_env_setup.py`
(1-140, 490-568), `tests/integration/test_permission_fidelity_exapp.py` (1-75),
`scripts/bootstrap_exapp.sh` (90-134, 251-273), `src/mcp_connector/ids.py` (1-40),
`docs/spike-discovery.md` (1-12, 145-177).

**Read-only:** Es wurde ausschliesslich diese Datei geschrieben. Kein Quellcode angefasst,
kein Python ausgefuehrt, nichts committet.

**Pattern extraction date:** 2026-08-15
