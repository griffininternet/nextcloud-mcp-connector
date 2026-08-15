# Phase 2: ExApp-Shell - Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 24 (11 neu, 13 geändert bzw. mechanisch angefasst)
**Analogs found:** 21 / 24

Grundregel dieser Phase: fast alles hat ein Vorbild im Repo. Nur `Dockerfile`, `start.sh` und
`appinfo/info.xml` sind Dateitypen, die es hier noch nie gab; für die gilt 02-RESEARCH.md
(Pattern 5, Routen-Deklaration) als Quelle, nicht ein erfundener Codebase-Analog.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächster Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `src/mcp_connector/exapp/__init__.py` | package | - | `src/mcp_connector/nextcloud/__init__.py` | exakt |
| `src/mcp_connector/exapp/auth.py` | middleware/utility | request-response (eingehend) | `src/mcp_connector/deps.py` (`StaticBearerVerifier`, `_credentials_from_basic`) | exakt |
| `src/mcp_connector/exapp/lifecycle.py` | route/controller | request-response | `src/mcp_connector/entry_http.py` (`/health` als `custom_route`) | exakt |
| `src/mcp_connector/exapp/status.py` | service (Client) | request-response (ausgehend, OCS) | `src/mcp_connector/nextcloud/clients/ocs.py` | exakt |
| `src/mcp_connector/entry_exapp.py` | config/entrypoint | Prozessstart | `src/mcp_connector/entry_stdio.py` + `entry_http.build_app` | exakt |
| `src/mcp_connector/config.py` (ERW) | config | - | sich selbst (`select_mode`, `static_bearer`, `_required`) | exakt |
| `src/mcp_connector/deps.py` (ERW) | service | - | sich selbst (`resolve_credentials`, dritter Zweig) | exakt |
| `src/mcp_connector/nextcloud/credentials.py` (ERW) | model | - | sich selbst (frozen dataclass, maskiertes `__repr__`) | exakt |
| `src/mcp_connector/nextcloud/clients/*.py` (20 Zeilen) | service | request-response | `clients/notes.py` Z. 70-99, `clients/ocs.py` Z. 64-81 | exakt |
| `appinfo/info.xml` | config (Manifest) | - | kein Analog | - |
| `Dockerfile` | config (Build) | - | kein Analog | - |
| `start.sh` | config (Startskript) | - | `scripts/bootstrap_test_nc.sh` (nur Shell-Konventionen) | partiell |
| `compose.exapp.yml` | config (Testumgebung) | - | `compose.test.yml` | exakt |
| `scripts/bootstrap_exapp.sh` | script | batch (occ) | `scripts/bootstrap_test_nc.sh` | exakt |
| `docs/spike-discovery.md` | doc | - | `docs/app-id-freeze.md` | exakt |
| `docs/spike-dav.md` | doc | - | `docs/app-id-freeze.md` | exakt |
| `docs/client-setup.md` (ERW, ExApp-Abschnitt) | doc | - | sich selbst (Abschnittsaufbau Z. 1-14, 98-173) | exakt |
| `tests/unit/test_exapp_auth.py` | test (unit) | - | `tests/unit/test_http_modes.py` | exakt |
| `tests/unit/test_exapp_lifecycle.py` | test (unit) | request-response | `tests/unit/test_transport_security.py` | exakt |
| `tests/unit/test_exapp_env_setup.py` | test (unit, Dateizusicherung) | file-I/O | `tests/unit/test_test_env_setup.py` | exakt |
| `tests/unit/test_appapi_credentials.py` | test (unit) | - | `tests/unit/test_credentials_http.py` | exakt |
| `tests/integration/test_permission_fidelity_exapp.py` | test (integration) | request-response | `tests/integration/test_permission_fidelity.py` | exakt |
| `tests/integration/test_exapp_dav_matrix.py` | test (integration) | request-response | `tests/integration/test_http_tool_call.py` | rollengleich |
| `.github/workflows/ci.yml` (ERW) | config (CI) | - | sich selbst (Job `unit` / `integration`) | exakt |
| `vulture_whitelist.py` (ERW) | config (Gate) | - | sich selbst | exakt |

## Pattern Assignments

### `src/mcp_connector/exapp/auth.py` (middleware/utility, request-response)

**Analog:** `src/mcp_connector/deps.py`

**Constant-time-Vergleich plus Kommentarhaltung** (`deps.py` Z. 82-106) - das ist wortwörtlich
das Muster, das `verify_appapi_headers` für `EX-APP-ID` und `APP_SECRET` kopiert:

```python
class StaticBearerVerifier:
    """Verify the single configured bearer token of a single-user deployment.

    ``secrets.compare_digest`` instead of ``==``: the comparison runs on attacker
    supplied input, and a short-circuiting comparison leaks the shared prefix over
    enough requests (threat T-01-24). The token is never logged and never echoed.

    The comparison runs on UTF-8 bytes, never on the strings themselves:
    ``compare_digest`` raises ``TypeError`` as soon as either side contains a
    non-ASCII character, and the caller-supplied side is hostile header input. A
    crash here would turn a malformed bearer into a 500 instead of a 401.
    """

    def __init__(self, token: str) -> None:
        self._token = token.encode("utf-8")
```

Übernehmen: `.encode("utf-8")` im Konstruktor, Vergleich nie auf `str`. Das schützt
`verify_appapi_headers` gegen den 500er, den ein Umlaut im Header sonst auslöst
(Test dazu: `test_http_modes.py` Z. 213-219).

**base64-Dekodierung mit `validate=True` und ohne Echo** (`deps.py` Z. 150-164):

```python
    try:
        decoded = base64.b64decode(payload.strip(), validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        # The offending value is never part of the message: it is credential material.
        raise MCPError(
            code=INVALID_REQUEST,
            message=f"The Basic credentials could not be decoded. {_BASIC_HINT}",
        ) from None

    user, separator, secret = decoded.partition(":")
    if not separator or not user or not secret:
        raise MCPError(...)
```

Unterschied zum ExApp-Fall, den der Plan explizit machen muss: `AUTHORIZATION-APP-API`
erlaubt einen **leeren** Nutzer (App-Kontext), also `if not separator: reject`, aber
`user == ""` ist kein Fehler beim Parsen. Verboten ist erst der Datenzugriff mit leerem
Nutzer (02-RESEARCH.md, Anti-Pattern "Impersonation ohne Nutzer"). Nach außen ist die
Antwort immer 401 ohne Detail, nie ein `MCPError` mit Hint: der eingehende Aufrufer ist
AppAPI, kein Modell.

**Import-Konvention** (`deps.py` Z. 22-37): Standardbibliothek, dann Dritt-Pakete, dann
relative Projekt-Imports (`from . import config`), `__all__` direkt darunter (Z. 39-45).

**Ausgehende Header als `httpx.Auth`** gehören ebenfalls in dieses Modul (02-RESEARCH.md
Pattern 3). Das `__repr__`-Verbot dazu steht im Analog `nextcloud/credentials.py` Z. 12-21
(siehe Shared Patterns).

---

### `src/mcp_connector/exapp/lifecycle.py` (route, request-response)

**Analog:** `src/mcp_connector/entry_http.py`

**custom_route-Muster inklusive der Begründung, warum das ohne Auth-Layer läuft**
(`entry_http.py` Z. 21-23 und Z. 47-54):

```python
* ``/health`` is a custom route, and custom routes are never authenticated, even when the
  rest of the server is. That is exactly right for a health probe and forbidden for
  anything else, so this module registers exactly one.
```

```python
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Liveness probe for deployments and for the client matrix test.

    Deliberately unauthenticated and deliberately dull: status and version, no
    configuration, no host names, no mode (threat T-01-29).
    """
    return JSONResponse({"status": "ok", "version": __version__})
```

Direkt übertragbar: `/heartbeat` ist derselbe Fall (ungeschützt, `{"status": "ok"}`, keine
Version, keine Konfiguration; 02-RESEARCH.md Pitfall 10 nennt T-01-29 analog).
`/init` und `/enabled` sind derselbe Dekorator, aber **mit** `require_appapi(request)` als
erster Zeile. Der Satz "so this module registers exactly one" in `entry_http.py` muss beim
Hinzufügen der drei Routen mitgepflegt werden, sonst lügt der Docstring.

**Imports** (`entry_http.py` Z. 31-40):

```python
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__, config
from .nextcloud.http import configure_logging
from .server import mcp
```

**Bau der App mit Env-Parameter statt Modul-Global** (`entry_http.py` Z. 57-67):

```python
def build_app(env: Mapping[str, str] | None = None) -> Starlette:
    """Build the ASGI application with the host allowlist of this deployment."""
    security = TransportSecuritySettings(
        allowed_hosts=config.allowed_hosts(env),
        enable_dns_rebinding_protection=config.dns_rebinding_protection(env),
    )
    return mcp.streamable_http_app(transport_security=security)


#: The application uvicorn imports. Built from the process environment at import time.
app = build_app()
```

`build_app(env)` ist der Grund, warum jeder Test seine eigene App bauen kann. Der ExApp-Modus
braucht dieselbe Signatur, sonst sind die Lifecycle-Tests nicht ohne Prozess testbar.
Achtung Host-Allowlist: hinter HaRP kommt der `Host` des Reverse-Proxys an, also gehört
`NC_MCP_ALLOWED_HOSTS` bzw. `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION` in die Deploy-Env des
Containers, sonst ist der erste Heartbeat ein 421 (dieselbe Falle wie Pitfall 6 aus Phase 1).

---

### `src/mcp_connector/exapp/status.py` (service, ausgehende OCS-Anfrage)

**Analog:** `src/mcp_connector/nextcloud/clients/ocs.py`

**Pflichtheader und URL-Bau** (`ocs.py` Z. 36-43 und Z. 57-61):

```python
#: OCS v2 lives under this prefix; v1 is not used anywhere in this project.
OCS_PREFIX = "/ocs/v2.php"

#: The two mandatory headers of D-18. Copied per request, never mutated in place.
OCS_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Accept": "application/json",
}


def ocs_url(creds: Credentials, path: str) -> str:
    """Build ``<base>/ocs/v2.php<path>``; ``path`` always starts with a slash."""
    if not path.startswith("/"):
        raise ValueError(f"an OCS path must start with a slash (got {path!r})")
    return f"{creds.base_url}{OCS_PREFIX}{path}"
```

Der Fortschritts-Push geht an `/apps/app_api/ex-app/status` unter genau diesem Präfix, mit
`OCS-APIRequest: true` (02-RESEARCH.md Lifecycle-Abschnitt) und `auth=creds.auth()` statt
`httpx.BasicAuth`.

**Auth pro Request, nie am Client** (`ocs.py` Z. 64-81):

```python
async def ocs_get(
    client: httpx.AsyncClient,
    creds: Credentials,
    path: str,
    params: Mapping[str, Any] | None = None,
) -> httpx.Response:
    """GET an OCS endpoint with both mandatory headers and per request Basic auth.

    Authentication is passed per request and not on the client, because the HTTP
    passthrough mode changes credentials from call to call. Redirects are not followed:
    the client is built that way, and a redirecting base URL is a configuration error.
    """
    return await client.get(
        ocs_url(creds, path),
        params=dict(params) if params else None,
        headers=dict(OCS_HEADERS),
        auth=httpx.BasicAuth(creds.user, creds.secret),
    )
```

**Fehlerbehandlung** (`ocs.py` Z. 169-196, `_check_transport`): Redirect, 401, 429 und 5xx
bekommen je eine eigene `ToolError`-Meldung mit `hint`. Für `status.py` gilt die Phase-1-Regel
sinngemäß, aber mit einem Unterschied, den der Plan festhalten muss: ein fehlgeschlagener
Fortschritts-Push darf den `/init`-Handler nicht auf 500 laufen lassen (AppAPI würde die
Installation abbrechen). Loggen und weitermachen, kein Retry-Sturm.

---

### `src/mcp_connector/entry_exapp.py` (entrypoint)

**Analog:** `src/mcp_connector/entry_stdio.py` (vollständig, Z. 1-36)

```python
def main() -> None:
    """Validate the environment, then serve MCP over stdio until stdin closes."""
    configure_logging()
    try:
        load_stdio_credentials()
    except ToolError as exc:
        logger.error("%s %s", exc.message, exc.hint)
        raise SystemExit(2) from None

    logger.info("MCP Connector is serving over stdio")
    mcp.run()
```

Zu übernehmen: `configure_logging()` als erste Zeile, Konfigurationsfehler als eine lesbare
Zeile plus `SystemExit(2)`, `raise ... from None`, `logger = logging.getLogger("mcp_connector.entry_exapp")`
auf Modulebene (Z. 19), kein `print` (stdout-Regel gilt im Container zwar nicht als Wire, aber
die Projektregel bleibt einheitlich).

Der uvicorn-Start (uds vs. host/port, `HP_SHARED_KEY` als Weiche) hat kein Analog im Repo:
02-RESEARCH.md Pattern 4 ist die Vorlage. `subprocess`/`os.environ`-Zugriffe bitte gegen die
ruff-Regelgruppen S und A prüfen (siehe Shared Patterns, Gates).

---

### `src/mcp_connector/config.py` (ERWEITERT: vierter Modus)

**Analog:** sich selbst

**Die Modus-Tabelle im Modul-Docstring** (`config.py` Z. 6-17) ist der Ort, an dem der vierte
Modus dokumentiert werden MUSS, sonst ist die Datei innerlich widersprüchlich:

```python
===================  =========================================  ==================================
Mode                 Selected by                                Nextcloud credentials
===================  =========================================  ==================================
stdio                no transport headers exist at all          environment (D-11)
http_passthrough     headers present, no static bearer set      Basic credentials of the request
http_static_bearer   ``NC_MCP_STATIC_BEARER`` is set            environment, guarded by the bearer
===================  =========================================  ==================================
```

**`select_mode` als reine Funktion** (`config.py` Z. 91-112):

```python
def select_mode(
    env: Mapping[str, str] | None = None,
    *,
    headers: Mapping[str, str] | None = None,
) -> Mode:
    """Return the one credential mode that applies to this call.

    ``headers is None`` means the transport has none (stdio, in-memory client), and no
    environment variable can turn such a process into an HTTP mode.
    """
    source = os.environ if env is None else env
    if headers is None:
        return "stdio"
    if static_bearer(source):
        return "http_static_bearer"
    return "http_passthrough"


def static_bearer(env: Mapping[str, str] | None = None) -> str | None:
    """The configured static bearer, or ``None`` when the variable is unset or blank."""
    source = os.environ if env is None else env
    return (source.get(ENV_STATIC_BEARER) or "").strip() or None
```

Muster für den vierten Zweig: eine `exapp_configured(env)`-Funktion nach dem Vorbild von
`static_bearer` (leerer String zählt als nicht gesetzt), `Mode` um `"exapp"` erweitern, und
die Reihenfolge in `select_mode` bewusst setzen: ExApp gewinnt gegen Passthrough, aber
niemals gegen `headers is None`. Der bestehende Test `test_static_bearer_wins_over_headers_but_never_over_stdio`
(`test_http_modes.py` Z. 71-74) ist die Vorlage für den entsprechenden ExApp-Test.

**Env-Konstanten** (`config.py` Z. 27-34): jede Variable bekommt eine `ENV_*`-Konstante, mit
`# noqa: S105`-Kommentar wo der Name nach Secret aussieht:

```python
ENV_APP_PASSWORD = "NC_MCP_APP_PASSWORD"  # noqa: S105 - the env var name, not a secret
```

Für AppAPI kommen `APP_ID`, `APP_SECRET`, `APP_VERSION`, `AA_VERSION`, `APP_HOST`, `APP_PORT`,
`APP_PERSISTENT_STORAGE`, `HP_SHARED_KEY` dazu (Namen von AppAPI vorgegeben, also **ohne**
`NC_MCP_`-Präfix; das ist eine Abweichung, die im Docstring genannt gehört).

**Fehlermeldung bei fehlender Variable** (`config.py` Z. 153-164): `ToolError(message=..., hint=...)`,
Message nennt den Variablennamen, Hint sagt was zu tun ist.

---

### `src/mcp_connector/deps.py` (ERWEITERT: vierter Credential-Zweig)

**Analog:** sich selbst, Z. 57-79 - hier hängt der neue Zweig ein, und mehr wird nicht angefasst:

```python
def resolve_credentials(ctx: Any) -> Credentials:
    headers = getattr(ctx, "headers", None) if ctx is not None else None
    mode = config.select_mode(headers=headers)

    if mode == "http_passthrough":
        # headers is not None in this mode, select_mode guarantees it.
        return _credentials_from_basic(headers or {})

    # stdio and static bearer both take the Nextcloud account from the environment: the
    # bearer authenticates the caller of this server, it does not select a Nextcloud user.
    return load_stdio_credentials()


def resolve_clients(ctx: Any) -> NcClients:
    """Bundle the event loop client with the credentials of this call."""
    return NcClients(client=shared_client(), creds=resolve_credentials(ctx))
```

Der ExApp-Zweig liest ausschließlich `AUTHORIZATION-APP-API` aus `ctx.headers` und ignoriert
`Authorization` vollständig (02-RESEARCH.md Anti-Pattern "Basic-Header und AppAPI-Header
gleichzeitig akzeptieren"). Der Signatur-Guard-Test `test_no_tool_parameter_can_set_the_user`
(`test_credentials_http.py` Z. 124-129) muss weiter grün bleiben: `resolve_credentials(ctx)`
behält genau einen Parameter.

Modul-Docstring Z. 10-16 nennt die drei Regeln (kein Caching, kein Auth-Retry, kein Logging
des Headers). Diese Liste gilt unverändert für den ExApp-Modus und sollte dort um einen Satz
ergänzt werden, nicht dupliziert.

---

### `src/mcp_connector/nextcloud/credentials.py` (ERWEITERT: `mode` + `auth()`)

**Analog:** sich selbst, Z. 12-21 (vollständig):

```python
@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    """Base URL without trailing slash, Nextcloud user id and app password."""

    base_url: str
    user: str
    secret: str

    def __repr__(self) -> str:
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, secret='***')"
```

Neue Felder bekommen Defaults, damit die 40+ bestehenden Konstruktoraufrufe (Tests inklusive)
unverändert bleiben: `mode: str = "basic"`, `app_id: str = ""`, `app_version: str = ""`,
`aa_version: str = ""`. `frozen=True, slots=True, repr=False` bleibt. `__repr__` nimmt `mode`
mit auf, aber niemals `secret`. Die Tests dazu existieren schon
(`test_credentials_http.py` Z. 23-47) und decken den neuen Modus ohne Umbau mit ab, sobald
sie parametrisiert werden.

---

### `src/mcp_connector/nextcloud/clients/*.py` (20 mechanische Zeilen)

**Analog:** `clients/notes.py` Z. 70-99 (repräsentativ für alle sechs Module):

```python
async def get_note(client: httpx.AsyncClient, creds: Credentials, note_id: str) -> dict[str, Any]:
    """Read one note including its content."""
    response = await client.get(
        api_url(creds, f"/notes/{note_id}"),
        headers=dict(_HEADERS),
        auth=httpx.BasicAuth(creds.user, creds.secret),
    )
    return _as_note(ocs.parse_app_json(response, what=f"the note {note_id}"))
```

Änderung ist exakt eine Zeile pro Aufrufstelle: `auth=httpx.BasicAuth(creds.user, creds.secret)`
wird `auth=creds.auth()`. Verteilung (per grep, Stand heute):
`dav.py` 6 (Z. 130, 177, 336, 372, 400, 477), `deck.py` 5 (Z. 90, 103, 120, 140, 173),
`caldav.py` 4 (Z. 180, 288, 322, 350), `carddav.py` 2 (Z. 183, 277), `notes.py` 2 (Z. 75, 97),
`ocs.py` 1 (Z. 80).

Nicht anfassen: `_HEADERS` mit `OCS-APIRequest: true` (`notes.py` Z. 35) bleibt in allen
JSON-Clients stehen, sonst greift die CSRF-Prüfung unter Impersonation
(02-RESEARCH.md Pitfall 12). Wenn `httpx` in einer Datei danach nicht mehr importiert wird,
meldet ruff das (F401); dann Import entfernen, aber die Typ-Annotation `httpx.AsyncClient`
hält den Import in aller Regel am Leben.

---

### `compose.exapp.yml` (config, Testumgebung)

**Analog:** `compose.test.yml` (vollständig, Z. 1-39)

**Kopfkommentar mit den vier Kommandos** (Z. 1-13) ist Pflichtteil des Musters:

```yaml
# Local throwaway Nextcloud for the integration tests (D-21).
#
#   docker compose -f compose.test.yml up -d --wait   # start and wait for healthy
#   bash scripts/bootstrap_test_nc.sh                 # apps, users, calendars, .env.test
#   docker compose -f compose.test.yml down           # stop, keep the data volume
#   docker compose -f compose.test.yml down -v        # stop and throw the data away
```

**Loopback-Bindung mit Begründung** (Z. 18-22) - WR-06, gilt für Caddy genauso:

```yaml
    ports:
      # Loopback only (WR-06): with the default admin password and the bruteforce guard
      # disabled at bootstrap, a 0.0.0.0 binding would expose a trivially ownable
      # instance to the developer's or runner's LAN.
      - "127.0.0.1:${NC_TEST_PORT:-8080}:80"
```

**Healthcheck, damit `--wait` funktioniert** (Z. 28-34):

```yaml
    healthcheck:
      # status.php answers as soon as the web server is up. That is not the same as
      # "installed", so the bootstrap script polls `occ status` before it does any work.
      test: ["CMD", "php", "-r", "exit(file_get_contents('http://localhost/status.php') ? 0 : 1);"]
      interval: 5s
      timeout: 5s
      retries: 40
```

Neu dazu (02-RESEARCH.md, Compose-Skizze): `caddy` mit `/exapps/*` zu `appapi-harp`,
`appapi-harp` mit `HP_SHARED_KEY`/`NC_INSTANCE_URL`/Docker-Socket. HaRP-Ports 8780/8782
werden **nicht** veröffentlicht (Caddy erreicht sie im Compose-Netz), damit die WR-06-Regel
nicht aufgeweicht wird. D-31 lässt dem Planner die Wahl zwischen Erweiterung und zweitem
File; bei zweitem File müssen die Dateizusicherungen in `test_test_env_setup.py` mitwachsen.

---

### `scripts/bootstrap_exapp.sh` (script, occ-Batch)

**Analog:** `scripts/bootstrap_test_nc.sh` (vollständig)

**Kopf, Idempotenz-Versprechen und occ-Wrapper** (Z. 1-40):

```bash
#!/usr/bin/env bash
# Bootstrap the local test Nextcloud from compose.test.yml.
# ...
# Idempotent by design: every step checks first and skips what already exists, so a second
# run is a no-op apart from a fresh app password in .env.test.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE_FILE="${COMPOSE_FILE:-compose.test.yml}"
SERVICE="nextcloud"
OCC="docker compose -f ${COMPOSE_FILE} exec -T --user www-data ${SERVICE} php occ"

occ() {
  # Intentionally unquoted: OCC is a command line, not a single word.
  # shellcheck disable=SC2086
  $OCC "$@"
}
```

**Ensure-Funktion mit Fehlerausgabe erst im Fehlerfall** (Z. 57-71) - Vorlage für
`ensure_daemon`, `ensure_exapp`:

```bash
ensure_app() {
  local app="$1" output
  if output="$(occ app:install "$app" 2>&1)"; then
    echo "app ${app}: installed"
    return 0
  fi
  if output="$(occ app:enable "$app" 2>&1)"; then
    echo "app ${app}: enabled"
    return 0
  fi
  echo "ERROR: could not install or enable ${app}:" >&2
  echo "${output}" >&2
  echo "See the FALLBACK block at the end of this script." >&2
  return 1
}
```

**Verifikationsblock am Ende** (Z. 164-174): erst `occ`-Ausgabe zeigen, dann per `grep`
scharf prüfen und mit `exit 1` scheitern. Für ExApp: `occ app_api:app:list` plus
`occ app_api:daemon:list` (02-RESEARCH.md, occ-Rezept).

**FALLBACK-Kommentarblock** (Z. 180-201): der Analog dokumentiert den Offline-Fall am
Dateiende statt in einem separaten Dokument. Für Phase 2 gehört dorthin der Fall
"`occ app:install app_api` ohne App-Store-Zugang" (02-RESEARCH.md Pitfall 9) und die
Re-Registrierungs-Falle mit festem `"secret"` im `--json-info` (Pitfall 11).

Zwei harte Konventionen aus dem Analog: LF-Zeilenenden (siehe Shared Patterns) und
Passwörter per `-e OC_PASS=` in den Container statt per Host-Export (Z. 35-40).

---

### `docs/spike-discovery.md` und `docs/spike-dav.md` (doc)

**Analog:** `docs/app-id-freeze.md`

**Kopf mit Status und Geltungsbereich** (Z. 1-4):

```markdown
# App ID Freeze

**Status:** frozen
**Decision date:** 2026-08-14
**Scope:** every public identifier of this project (Nextcloud app id, display name, ...)
```

**Entscheidung als Tabelle, danach nummerierte Begründung, danach Belege mit verbatim
kopiertem Kommando und Ausgabe** (Z. 6-40):

```markdown
## Decision

| Identifier | Frozen value |
|------------|--------------|
| Nextcloud app id | `mcp_connector` |

## Rationale

1. **No "nextcloud" inside the app id.** ...

## Availability evidence

All checks were executed on **2026-08-14** from the development host.

### 1. PyPI distribution name is free

```
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/nextcloud-mcp-connector/json
404
```
```

Genau dieser Aufbau erfüllt D-29 und D-30: Matrix (Pfad x Auth-Zustand x Statuscode bzw.
API-Familie x Auth-Weg), Beleg als kopiertes `curl -i`-Ergebnis mit Datum, und ein
Abschnitt "Consequence for phase 3" bzw. "Provider split per API family" mit der
Fallback-Route im Klartext. Kein SUMMARY-Absatz, sondern ein eigenständiges Dokument
(D-29 verlangt das ausdrücklich).

---

### `tests/unit/test_exapp_auth.py` (test, unit)

**Analog:** `tests/unit/test_http_modes.py`

**Fake-Kontext statt Server** (Z. 29-38):

```python
class FakeContext:
    """Stand-in for the SDK context: ``headers`` is ``None`` on stdio and in-memory."""

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers


def basic(user: str = USER, secret: str = SECRET) -> str:
    raw = f"{user}:{secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()
```

Für ExApp: `appapi_headers(user="alice", secret=SECRET)` als Helfer, der die drei Header
baut. Abschnittstrennung per Kommentarbanner (`# --- mode selection ----`, Z. 50).

**Der Kein-Echo-Test und der Kein-Log-Test** (Z. 146-172) sind eins zu eins zu übernehmen,
mit `AUTHORIZATION-APP-API` statt `authorization`:

```python
@pytest.mark.parametrize("header", [...])
def test_no_error_message_ever_repeats_the_header(env_credentials: None, header: str) -> None:
    """T-01-21: the header is material, not text we are allowed to quote back."""
    try:
        deps.resolve_credentials(FakeContext(headers={"authorization": header}))
    except deps.MCPError as exc:
        text = f"{exc.message} {exc}"
        assert header not in text


def test_resolution_writes_nothing_to_the_log(
    env_credentials: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        deps.resolve_credentials(FakeContext(headers={"authorization": basic()}))
    assert SECRET not in caplog.text
    assert caplog.text.strip() == ""
```

**Der Quelltext-Gate gegen `==`** (Z. 231-234) gehört auch über `verify_appapi_headers`:

```python
def test_the_verifier_compares_in_constant_time() -> None:
    """T-01-24: a plain ``==`` would leak the token length by length of comparison."""
    source = inspect.getsource(deps.StaticBearerVerifier)
    assert "compare_digest" in source
```

Alle Pfade testen (globale Regel + Phase-1-Praxis): fehlende Header, leerer Header, falsche
App-Id, kaputtes base64, fehlender Doppelpunkt, falsches Secret, Umlaut im Header, leerer
Nutzer (= App-Kontext, kein Fehler beim Parsen, aber kein Datenzugriff).

---

### `tests/unit/test_exapp_lifecycle.py` (test, unit)

**Analog:** `tests/unit/test_transport_security.py`

**In-Process gegen die ASGI-App, jede Prüfung baut ihre eigene App** (Z. 32-52):

```python
def post_mcp(app: object, host: str) -> int:
    """POST /mcp with an explicit Host header and return the status code.

    Every test builds its own app: the SDK session manager of one application object may
    be started exactly once, so a shared app would fail on the second lifespan instead of
    on the assertion.
    """
    with TestClient(app, base_url=f"http://{host}") as client:  # type: ignore[arg-type]
        response = client.post("/mcp", headers=MCP_HEADERS, content=json.dumps(INITIALIZE))
    return response.status_code


def test_health_answers_200_with_compact_json() -> None:
    with TestClient(entry_http.build_app({})) as client:
        response = client.get("/health")

    assert response.status_code == 200
```

**Leak-Test für unauthentifizierte Endpunkte** (Z. 54-68) - direkt auf `/heartbeat` münzen:

```python
def test_health_leaks_no_configuration() -> None:
    """T-01-29: a public unauthenticated endpoint says that it lives, nothing else."""
    ...
    assert set(json.loads(body)) == {"status", "version"}
```

Zusätzlich für Phase 2, ohne Analog, aber aus dem Research abgeleitet: `/heartbeat` antwortet
200 **mit und ohne** AppAPI-Header (Pitfall 10), `/init` und `/enabled` antworten 401 ohne
gültige Header, `/enabled` liefert `{"error": ""}` (sonst deaktiviert AppAPI sofort wieder),
und `enabled` akzeptiert als Query-Wert strikt `0` oder `1`.

---

### `tests/unit/test_exapp_env_setup.py` (test, Dateizusicherungen ohne Docker)

**Analog:** `tests/unit/test_test_env_setup.py` (vollständig, Z. 1-79)

```python
"""Guards for the local test Nextcloud (compose.test.yml plus bootstrap script).

These checks are pure file assertions, so the default suite keeps running without Docker.
"""

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.test.yml"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_test_nc.sh"


@pytest.mark.parametrize("path", [COMPOSE, BOOTSTRAP])
def test_no_crlf_in_files_the_container_reads(path: Path) -> None:
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; docker compose exec fails on the CR"
    )


def test_compose_binds_the_test_instance_to_loopback_only() -> None:
    """WR-06: throwaway credentials are only defensible while nothing but localhost can
    reach the instance; a bare host port would publish it on every interface."""
    text = COMPOSE.read_text(encoding="utf-8")
    assert '"127.0.0.1:${NC_TEST_PORT:-8080}:80"' in text
```

Das ist der Weg, `Dockerfile`, `start.sh`, `compose.exapp.yml` und `appinfo/info.xml` zu
prüfen, ohne dass die Standard-Suite Docker braucht (D-32: grün ohne Docker). Konkrete
Kandidaten aus dem Research: CRLF-Verbot für `start.sh` und `bootstrap_exapp.sh`,
`HEALTHCHECK` im Dockerfile, `USER` (non-root), `ENTRYPOINT ["/start.sh", ...]`, frpc-SHA256
im Dockerfile, und in `info.xml` KEINE Route mit `<url>.*</url>` plus `PUBLIC`
(02-RESEARCH.md Anti-Pattern 1) sowie kein `401` in `bruteforce_protection` der MCP-Route.

---

### `tests/integration/test_permission_fidelity_exapp.py` (test, integration)

**Analog:** `tests/integration/test_permission_fidelity.py` (D-28 nennt es namentlich)

**Client-Fabrik und Zwei-Konten-Fixtures** (Z. 50-85):

```python
def _clients(base_url: str, user: str, secret: str) -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(base_url),
            user=user,
            secret=secret,
        ),
    )


@pytest.fixture
async def bob(live_env: dict[str, str | None]) -> AsyncIterator[NcClients]:
    """The second account. He owns nothing of alice's and shares nothing with her."""
    base_url = live_env["base_url"]
    user = os.environ.get("NC_MCP_TEST_USER2")
    secret = os.environ.get("NC_MCP_TEST_APP_PASSWORD2")
    if not base_url or not user or not secret:
        pytest.skip("no second test user configured (NC_MCP_TEST_USER2)")
```

Für die ExApp-Variante ändert sich genau eine Stelle: `Credentials(..., mode="appapi",
secret=APP_SECRET, user="bob", app_id=..., app_version=...)`. Der Rest der Datei bleibt.

**Der Positiv-Kontroll-Test zuerst** (Z. 100-117) - ohne ihn beweist ein leeres Ergebnis
nichts:

```python
async def test_the_two_accounts_are_really_two_different_accounts(
    alice: NcClients, bob: NcClients
) -> None:
    """Guard against a false pass: if both fixtures were alice, every test below is empty."""
    assert alice.creds.user != bob.creds.user
```

**Die vier Lecktests** (Z. 120-164) decken files_search, unified_search, chatgpt-search und
den direkten `files_read` auf bekanntem Pfad ab. D-28 verlangt mindestens files/notes/
unified_search; die Notes-Ergänzung ist der einzige echte Zuwachs.

**Marker- und Ausführungsmuster** (Z. 25-29, 47):

```python
pytestmark = [pytest.mark.integration, pytest.mark.anyio]
```

---

### `tests/integration/test_exapp_dav_matrix.py` (test, integration, DAV-Spike)

**Analog:** `tests/integration/test_http_tool_call.py`

**Freier Port plus Subprozess mit bewusst leerer Umgebung** (Z. 42-80):

```python
def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture
def server(live: dict[str, str]) -> Iterator[str]:
    """A uvicorn subprocess in passthrough mode, pointed at the test Nextcloud."""
    port = free_port()
    env = dict(os.environ.items())
    # The point of the test: the process itself has no Nextcloud account.
    env.pop("NC_MCP_USER", None)
    env.pop("NC_MCP_APP_PASSWORD", None)
    process = subprocess.Popen(  # noqa: S603 - fixed command from our own package
        [sys.executable, "-m", "uvicorn", "mcp_connector.entry_http:app", ...]
    )
```

Für den DAV-Spike ist dasselbe Prinzip zu nutzen: der Prozess bekommt **kein** App-Passwort,
nur `APP_SECRET`. Wenn PROPFIND/REPORT/PUT trotzdem funktionieren, kann die Identität nur aus
`AUTHORIZATION-APP-API` gekommen sein. Serverseitiger Identitätsbeleg per
`GET /ocs/v2.php/cloud/user` (muss `bob` liefern) plus Negativtest auf `/remote.php/dav/files/alice/`,
wie in 02-RESEARCH.md, Abschnitt DAV-Spike, gefordert.

---

### `.github/workflows/ci.yml` (ERWEITERT)

**Analog:** sich selbst

**Job `unit`, Gate-Reihenfolge** (Z. 8-40) - neue Schritte reihen sich hier ein, sie ersetzen
nichts:

```yaml
      - name: Lint
        run: uv run ruff check .
      - name: Format check
        run: uv run ruff format --check .
      - name: Type check
        run: uv run pyright
      - name: Dead code check
        run: uv run vulture src scripts vulture_whitelist.py
      - name: Unit and contract tests
        run: uv run pytest tests/unit tests/contract
      - name: Tool budget gate
        run: uv run python scripts/check_tool_budget.py
```

**Job `integration`, Compose-Start mit `--wait` und Log-Dump bei Fehlschlag** (Z. 42-74):

```yaml
      - name: Start the test Nextcloud
        # --wait honours the healthcheck in compose.test.yml, so no sleep is needed.
        run: docker compose -f compose.test.yml up -d --wait
      - name: Bootstrap apps, users, calendar and address book
        run: bash scripts/bootstrap_test_nc.sh
      ...
      - name: Nextcloud logs on failure
        if: failure()
        run: docker compose -f compose.test.yml logs --tail=200
```

Neu (D-25): ein `docker buildx build` des ExApp-Images im Job `unit` oder als eigener Job,
**ohne** Push (Registry-Publishing erst Phase 5). Der Log-Dump-Schritt bekommt bei einem
ExApp-Job zusätzlich die HaRP- und ExApp-Container-Logs.

---

## Shared Patterns

### Modul-Docstring erklärt das Warum, nicht das Was
**Quelle:** `src/mcp_connector/deps.py` Z. 1-20, `entry_http.py` Z. 1-29
**Gilt für:** jede neue Python-Datei dieser Phase

```python
"""Credential resolution per tool call: the one channel the identity may come from.

Three rules that follow from D-12 and pitfall 8, all of them load bearing:

* no caching of credentials anywhere, they live for the duration of one call
* no auth retry, because Nextcloud counts failures per source IP and a remote MCP
  server is one IP for many users
* no logging of the header, not even on DEBUG, not even truncated (threat T-01-21)
"""
```

Der Stil ist projektweit durchgehalten: Entscheidungs-Ids (D-xx), Threat-Ids (T-01-xx) und
Pitfall-Nummern stehen im Docstring, nicht nur im Planungsordner. Phase 2 verweist analog auf
D-23 bis D-32 und auf die Pitfalls aus 02-RESEARCH.md.

### Secrets: maskieren, nie loggen, konstant vergleichen
**Quelle:** `nextcloud/credentials.py` Z. 20-21, `deps.py` Z. 95-106, `nextcloud/http.py` Z. 41-57
**Gilt für:** `exapp/auth.py`, `exapp/status.py`, `credentials.py`, alle zugehörigen Tests

```python
    def __repr__(self) -> str:
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, secret='***')"
```

```python
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
```

`AppApiAuth` hält das base64-Token privat (`self._headers`) und erbt kein `__repr__`, das es
zeigen würde. Das Token enthält `APP_SECRET` im Klartext, base64 ist Kodierung, kein Schutz.

### Fehler tragen `message` plus `hint`
**Quelle:** `src/mcp_connector/errors.py` (via `clients/ocs.py` Z. 169-196 und Z. 217-261)
**Gilt für:** alle Service- und Client-Dateien

```python
    if status == 401:
        raise ToolError(
            message="Nextcloud rejected the app password.",
            hint=(
                "Generate a new app password in Nextcloud under Settings, Security, "
                "Devices and sessions, then restart the MCP server."
            ),
        )
```

Ausnahme im ExApp-Modus: eingehende Requests von AppAPI bekommen 401 **ohne** Detail und ohne
Hint. `message`/`hint` richtet sich an Menschen und Modelle, nicht an einen Proxy.

### HTTP-Härtung, die nicht dupliziert wird
**Quelle:** `nextcloud/http.py` Z. 26-38

```python
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0, read=30.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": "nextcloud-mcp-connector/0.1"},
        )
```

`follow_redirects=False` bleibt im ExApp-Modus zwingend: ein Redirect würde die vier
AppAPI-Header an ein fremdes Ziel schicken. Kein zweiter Client, kein `auth=` am Client.

### Dateien, die ein Container liest, haben LF
**Quelle:** `tests/unit/test_test_env_setup.py` Z. 33-37, `.gitattributes`
**Gilt für:** `start.sh`, `scripts/bootstrap_exapp.sh`, `Dockerfile`, `compose.exapp.yml`

```python
@pytest.mark.parametrize("path", [COMPOSE, BOOTSTRAP])
def test_no_crlf_in_files_the_container_reads(path: Path) -> None:
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; docker compose exec fails on the CR"
    )
```

Auf diesem Windows-Host ist das kein theoretisches Risiko. Vor dem Anlegen neuer Shell-Dateien
`.gitattributes` prüfen und den Test um die neuen Pfade erweitern.

### Gates unverändert (D-32)
**Quelle:** `pyproject.toml` Z. 46-81, `vulture_whitelist.py` Z. 1-12, `.github/workflows/ci.yml`

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "S", "SIM", "C4", "RUF", "PT", "ASYNC", "RET", "A", "ISC"]
ignore = ["ISC001"]
```

Praktische Folgen für Phase 2: `S` erzwingt begründete `# noqa: S105`/`S603`-Kommentare bei
Env-Namen und `subprocess`-Aufrufen; `line-length = 100`; `known-first-party = ["mcp_connector"]`;
pyright `standard` über `src`, `scripts`, `tests`. Jeder neue Name, den vulture nicht sieht
(z.B. die drei Lifecycle-Handler, registriert per Dekorator), braucht einen Eintrag mit
Ein-Zeilen-Begründung nach dem Muster von `vulture_whitelist.py` Z. 31-37:

```python
# --- Framework entry points -----------------------------------------------------------
# health: registered with @mcp.custom_route and checked by tests/unit/test_transport_
#   security.py and the client matrix, which waits for it before every run.
health
_.verify_token
```

### Integrationstests bleiben opt-in und ohne Docker übersprungen
**Quelle:** `tests/conftest.py` Z. 39-54, `pyproject.toml` Z. 40-44

```python
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests when no test Nextcloud is configured."""
    if os.environ.get("NC_MCP_URL"):
        return
```

Neue ExApp-Integrationstests brauchen zusätzlich eine eigene Skip-Bedingung (kein
`APP_SECRET` bzw. keine registrierte ExApp). Muster dafür ist die `bob`-Fixture in
`test_permission_fidelity.py` Z. 73-85 mit `pytest.skip("...")` und einer Meldung, die die
fehlende Variable beim Namen nennt.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `appinfo/info.xml` | config (Manifest) | - | Das Repo hat noch kein XML-Manifest. Vorlage ist 02-RESEARCH.md, Abschnitt "Routen-Deklaration" (vollständiges `<external-app>`-Beispiel mit den zwei engen Routen) plus `docs/app-id-freeze.md` für die eingefrorenen Werte (`mcp_connector`, "MCP Connector", AGPL-3.0-or-later). Referenz-ExApp: `nextcloud/context_agent/appinfo/info.xml`. |
| `Dockerfile` | config (Build) | - | Kein Container-Build im Repo. Vorlage ist 02-RESEARCH.md Pattern 5 (uv-Installer, non-root, `curl`, frpc 0.61.1 mit SHA256, `HEALTHCHECK`, `ENTRYPOINT ["/start.sh", ...]`, kein fester Port). Projektregel: uv als Installer, Python 3.13. |
| `start.sh` | config (Startskript) | - | Wird laut Research **wortwörtlich** aus HaRP `exapps_dev/` übernommen (AGPL-3.0, SPDX-Header setzen), nicht nachgebaut. Aus dem Repo gilt nur die LF-Regel und der Kopfkommentar-Stil von `scripts/bootstrap_test_nc.sh`. |

## Metadata

**Analog search scope:** `src/mcp_connector/**`, `tests/{unit,contract,integration,compat}/**`,
`scripts/`, `docs/`, `.github/workflows/`, Repo-Wurzel (`compose.test.yml`, `pyproject.toml`,
`vulture_whitelist.py`)
**Files scanned:** 21 gelesen, 39 Python-Module und 26 Testdateien indiziert
**Pattern extraction date:** 2026-08-15
