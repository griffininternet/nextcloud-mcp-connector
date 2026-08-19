<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Phase 5: Hardening und Store-Einreichung, Pattern Map

**Gemappt:** 2026-08-19
**Dateien analysiert:** 25 (7 neu, 18 geändert)
**Analoge gefunden:** 24 / 25

Grundbefund der Recherche, der diese Karte prägt: Phase 5 ist überwiegend Wiederverwendung
an neuen Aufrufstellen und kaum Neubau (05-RESEARCH.md, "Key insight"). Für jede neue Datei
existiert ein Analog im Repo, das dieselbe Rolle in derselben Richtung schon erfüllt. Nur der
Negativ-Credential-Lasttest hat kein Vorbild.

Die drei Schnitte der Recherche sind hier als Gruppen geführt: (1) Ein-Klick-Tauglichkeit,
(2) Deinstallation, (3) Beweise und Doku.

---

## File Classification

### Schnitt 1: Ein-Klick-Tauglichkeit (BL-06)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `src/mcp_connector/exapp/admin_settings.py` (neu) | provider/registration | request-response (ausgehend OCS-POST) | `src/mcp_connector/exapp/settings_form.py` | exact |
| `src/mcp_connector/exapp/config_values.py` (neu) | service (Lesepfad) | request-response (ausgehend OCS-POST) | `src/mcp_connector/oauth/crypto.py` (`_read_key`, `_headers`, `_config_value`) | exact |
| `src/mcp_connector/config.py` (geändert) | config | transform (pure) | dieselbe Datei (`public_url`, `normalize_base_url`) | exact |
| `src/mcp_connector/oauth/registry.py` (geändert) | config/policy | transform (pure) | dieselbe Datei (`client_policy`, `_switch`, `_entries`) | exact |
| `src/mcp_connector/exapp/ui/strings.py` (geändert) | utility (Textkatalog) | keiner | dieselbe Datei (`SETTINGS_*`-Block) | exact |
| `src/mcp_connector/exapp/lifecycle.py` (geändert) | middleware/lifecycle | request-response (eingehend) | dieselbe Datei (`enabled`, `enabled=1`-Zweig) | exact |
| `appinfo/info.xml` (geändert) | config/manifest | keiner | dieselbe Datei | exact |

### Schnitt 2: Deinstallation (SC2)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `src/mcp_connector/exapp/occ.py` (neu) | provider/registration | request-response (ausgehend OCS-POST) | `src/mcp_connector/exapp/settings_form.py` | exact |
| `src/mcp_connector/exapp/purge.py` (neu) | route/handler + batch | request-response (eingehend) + batch (Widerrufsschleife) | `src/mcp_connector/exapp/lifecycle.py` (Guard, Factory) plus `oauth/provider.py::sweep_abandoned` (Schleife) | exact (zwei Analoge, je eine Hälfte) |
| `src/mcp_connector/oauth/store.py` (geändert) | model/repository | CRUD (SQLite) | dieselbe Datei (`authorizations_of_client`, `purge_expired`) | exact |
| `src/mcp_connector/oauth/crypto.py` (geändert) | service | request-response (ausgehend OCS-DELETE) | dieselbe Datei (`_write_key`) | exact |
| `src/mcp_connector/entry_exapp.py` (geändert) | config/wiring | keiner | dieselbe Datei (Route-Append-Block) | exact |
| `docs/uninstall.md` (neu) | doc/runbook | keiner | `docs/exapp-install.md` | exact |

### Schnitt 3: Beweise und Doku (SC3, SC4, EXAPP-04/05)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `tests/integration/test_permission_parity_share.py` (neu) | test (integration) | request-response über die volle Kette | `tests/integration/test_permission_fidelity_exapp.py` | exact |
| `tests/integration/test_credential_flood.py` (neu) | test (integration) | batch (parallele Requests) | keins (siehe "No Analog Found"); Teilvorbilder: `test_permission_fidelity_exapp.py` (Env-Fixture), `tests/unit/test_oauth_abuse.py` (Aufbau) | partial |
| `tests/unit/test_exapp_admin_settings.py` (neu) | test (unit) | request-response (respx) | `tests/unit/test_exapp_lifecycle.py` Zeilen 244-330 plus `tests/unit/test_oauth_crypto.py` Zeilen 37-40 | exact |
| `tests/unit/test_exapp_purge.py` (neu) | test (unit) | request-response (respx) + CRUD (tmp_path-SQLite) | `tests/unit/test_exapp_lifecycle.py` (Guard-Tests), `tests/unit/test_oauth_abuse.py` (Deployment-Fixture) | exact |
| `tests/unit/test_exapp_env_setup.py` (geändert) | test (unit, Manifest-Gate) | keiner | dieselbe Datei (Route-Gate Zeilen 637-668) | exact |
| `scripts/bootstrap_exapp.sh` (geändert) | script/fixture | file-I/O + occ-Aufrufe | dieselbe Datei (`ensure_files_home`, `ensure_calendar`) | exact |
| `docs/client-setup.md` (geändert) | doc | keiner | dieselbe Datei ("Claude.ai, step by step", "Cursor ...") | exact |
| `docs/faq.md` (neu) | doc | keiner | `docs/privacy.md` (Abschnitt "Deletion and user control") | role-match |
| `README.md` / `README.de.md` / `README.fr.md` (geändert) | doc (dreisprachig) | keiner | untereinander (gleiche Überschriftenfolge) | exact |
| `docs/oauth-setup.md` (geändert) | doc | keiner | dieselbe Datei (Abschnitte 1 und 2) | exact |
| `docs/store-submission.md` (geändert) | doc/runbook | keiner | dieselbe Datei | exact |
| `CHANGELOG.md` (geändert) | doc | keiner | dieselbe Datei (0.1.0-Block) | exact |

---

## Pattern Assignments

### `src/mcp_connector/exapp/admin_settings.py` (neu, provider/registration, request-response)

**Analog:** `src/mcp_connector/exapp/settings_form.py` (komplette Datei, 108 Zeilen)

Das ist ein Eins-zu-eins-Vorbild: gleiche OCS-Route, gleicher App-Kontext, gleiches
Fehlermodell. Der einzige Unterschied ist `section_type: "admin"`, eine zweite `FORM_ID`
und ein nicht leeres `fields`.

**Import- und Konstantenblock** (Zeilen 23-52):

```python
import logging
from collections.abc import Mapping
from typing import Any

import httpx

from .. import config
from ..nextcloud.clients.ocs import OCS_HEADERS
from ..nextcloud.credentials import appapi_auth_headers
from ..nextcloud.http import shared_client
from .ui import strings
from .ui.connections import CONNECTIONS_PATH

__all__ = ["form_scheme", "register_settings_form"]

#: The OCS route AppAPI exposes for Declarative Settings forms of an ExApp.
SETTINGS_PATH = "/ocs/v2.php/apps/app_api/api/v1/ui/settings"

#: The form id, stable across registrations: ``insertOrUpdate`` keys on (appid, formid), so
#: re-enabling the app updates the one entry instead of adding a second.
FORM_ID = "mcp_connector_settings"

FORM_PRIORITY = 10
SECTION_TYPE = "personal"
SECTION_ID = "security"

logger = logging.getLogger("mcp_connector.exapp.settings_form")
```

Für die Admin-Form ändern sich genau vier Werte: eine zweite `FORM_ID`
(z. B. `mcp_connector_admin`), `SECTION_TYPE = "admin"`, eine Admin-`SECTION_ID`
(`security` oder `additional`) und ein befülltes `fields`. `SETTINGS_PATH` bleibt identisch,
weil AppAPI beide Formulare über dieselbe Route annimmt.

**Schema-Bau als Funktion, nicht als Konstante** (Zeilen 55-77):

```python
def form_scheme(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Build the form scheme against one environment.

    A function and not a module level constant: both URLs in it come from the **public**
    URL of this deployment, which is configuration and not a compile time fact.
    """
    connections_url = f"{config.public_url(env)}{CONNECTIONS_PATH}"
    return {
        "id": FORM_ID,
        "priority": FORM_PRIORITY,
        "section_type": SECTION_TYPE,
        "section_id": SECTION_ID,
        "title": strings.SETTINGS_TITLE,
        "description": strings.SETTINGS_DESCRIPTION.format(connections_url=connections_url),
        "doc_url": connections_url,
        # Empty, and a list: core validation accepts an empty list and rejects a missing one.
        "fields": [],
    }
```

Die vier Felder der Admin-Form treten hier an die Stelle von `"fields": []`. Feld-Ids sind
die Config-Schlüssel (Recherche, Pattern 1), also `public_url`, `oauth_dcr`,
`oauth_allowlist_only`, `oauth_allowed_clients`, mit den Typen `url`, `checkbox`,
`checkbox`, `text`. Auflage aus der Recherche: **kein** Feld mit `"sensitive": true`.

**Registrierung: App-Kontext, ein Versuch, nie eine Ausnahme** (Zeilen 80-108):

```python
async def register_settings_form(*, env: Mapping[str, str] | None = None) -> None:
    """Put the signpost into Nextcloud's settings. Never raises, for any reason."""
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{SETTINGS_PATH}"
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
        response = await client.post(url, json={"formScheme": form_scheme(env)}, headers=headers)
    except httpx.HTTPError:
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the settings form registration to %s did not reach Nextcloud", url)
        return

    if response.status_code // 100 != 2:
        logger.error("the settings form registration to %s answered %s", url, response.status_code)
```

Der leere erste Parameter von `appapi_auth_headers("")` ist der App-Kontext: die ExApp redet
über sich selbst, nicht im Namen einer Person. Diesen Aufruf teilen `settings_form.py`,
`crypto.py::_headers` und (neu) `admin_settings.py` und `occ.py`.

---

### `src/mcp_connector/exapp/config_values.py` (neu, service, request-response)

**Analog:** `src/mcp_connector/oauth/crypto.py` (`EXAPP_CONFIG_PATH`, `_read_key`, `_headers`,
`_config_value`)

Der Lesepfad existiert vollständig und ist gegen ein laufendes AppAPI 34.0.0 gemessen. Neu
ist nur, dass mehrere Schlüssel auf einmal gelesen werden und dass ein fehlender Wert keine
Ausnahme, sondern ein Rückfall auf die Env ist.

**Route und Verb, mit der Begründung, warum es ein POST ist** (Zeilen 86-99):

```python
#: The AppAPI route that stores ExApp configuration.
EXAPP_CONFIG_PATH = "/ocs/v2.php/apps/app_api/api/v1/ex-app/config"

#: How the read is asked, measured against a running AppAPI 34.0.0 in plan 03-08. The
#: route table of that app declares three verbs on this resource and none of them is a
#: ``GET``: ``POST /ex-app/config`` writes, ``DELETE /ex-app/config`` removes, and the read
#: is ``POST /ex-app/config/get-values`` with a JSON body ``{"configKeys": [...]}``.
CONFIG_READ_SUFFIX = "/get-values"
CONFIG_READ_FIELD = "configKeys"
```

**Der Lesecall** (Zeilen 240-270):

```python
async def _read_key(settings: config.ExAppSettings) -> bytes | None:
    """Return the stored key, or ``None`` when Nextcloud says there is none yet."""
    url = f"{settings.base_url}{EXAPP_CONFIG_PATH}{CONFIG_READ_SUFFIX}"
    client = shared_client()
    try:
        response = await client.post(
            url, json={CONFIG_READ_FIELD: [CONFIG_KEY]}, headers=_headers(settings)
        )
    except httpx.HTTPError:
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the ExApp configuration at %s could not be read", url)
        raise ToolError(...) from None

    if response.status_code // 100 != 2:
        raise ToolError(...)

    raw = _config_value(_payload(response))
```

**Envelope-Parsing mit drei akzeptierten Formen, fail closed** (Zeilen 323-363, hier gekürzt
auf die Struktur, die wiederverwendet wird):

```python
def _config_value(payload: Any) -> str | None:
    """Pull our one value out of the OCS envelope, or refuse to guess."""
    if not isinstance(payload, dict):
        raise _unreadable()
    ocs = payload.get("ocs")
    if not isinstance(ocs, dict) or "data" not in ocs:
        raise _unreadable()

    data = ocs["data"]
    if isinstance(data, list):
        for entry in data:
            name = entry.get("configkey", entry.get("configKey"))   # AppAPI 34 answers lower case
            ...
            value = entry.get("configvalue", entry.get("configValue"))
            ...
    if isinstance(data, dict):
        ...
    raise _unreadable()
```

Der Kommentar dazu ist die Warnung, die der Planner mitnehmen muss: AppAPI 34.0.0 antwortet
mit den **Spaltennamen in Kleinschreibung** (`configkey`, `configvalue`), die camelCase-Form
ist der Schreibpfad. Ein neuer Mehrschlüssel-Leser muss beide Schreibweisen akzeptieren und
darf eine unlesbare Antwort niemals als "kein Wert" verbuchen.

**Unterschied zum Analog, den der Planner festlegen muss:** `crypto._read_key` scheitert hart,
weil ein erfundener Data Key jede Autorisierung unlesbar macht. Die Admin-Werte sind das
Gegenteil: eine unerreichbare Nextcloud darf die Installation nicht anhalten, sie muss auf die
Deploy-Env zurückfallen. Die Vorrangregel der Recherche ist
Admin-Wert > `NC_MCP_*`-Env > Code-Default.

**Header-Helfer, wörtlich übernehmbar** (`crypto.py` Zeilen 298-310):

```python
def _headers(settings: config.ExAppSettings) -> dict[str, str]:
    """The OCS headers plus the AppAPI identity, in the app context (empty user id)."""
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
    return headers
```

---

### `src/mcp_connector/config.py` (geändert, config, transform)

**Analog:** dieselbe Datei

**Was heute da ist** (Zeilen 226-229):

```python
def public_url(env: Mapping[str, str] | None = None) -> str:
    """Public base URL of this MCP server, used for the bearer discovery document."""
    source = os.environ if env is None else env
    return (source.get(ENV_PUBLIC_URL) or "").strip().rstrip("/") or DEFAULT_PUBLIC_URL
```

Die Funktion ist synchron und pur, der Admin-Wert kommt aber über HTTP. Der Planner muss also
entscheiden, wo der gelesene Wert lebt (Vorschlag: einmal beim `enabled=1`/Start gelesen und
in die aufrufende Schicht gegeben, nicht in `config.py` hineinasynchronisiert): jede
Signaturänderung an `public_url` trifft `settings_form.form_scheme`, `metadata.py`,
`consent.py` und die Form-Action jeder Seite.

**Validierungsmuster für den Admin-Wert** (Zeilen 121-147, `normalize_base_url`):

```python
def normalize_base_url(raw: str) -> str:
    """Strip whitespace and trailing slashes, keep a subpath, require http or https."""
    candidate = (raw or "").strip().rstrip("/")
    if not candidate:
        raise ToolError(message=f"{ENV_URL} is empty.", hint=_URL_HINT)

    parts = urlsplit(candidate)
    if parts.scheme not in ("http", "https"):
        raise ToolError(...)
    if not parts.netloc:
        raise ToolError(...)
    if parts.username or parts.password:
        # The value neither belongs in a URL nor in this message: base_url is logged with
        # its full value in exapp/status.py, so a password in there would end up in the log.
        raise ToolError(...)
    return candidate
```

Die Public URL wird zum `issuer` und zur `resource`, ist also der gefährlichste der vier
Admin-Werte (Security Domain, V5). `normalize_base_url` plus die Fragment-Regel aus
`registry.redirect_uri_allowed` (siehe unten) sind die vorhandenen Bausteine.

---

### `src/mcp_connector/oauth/registry.py` (geändert, config/policy, transform)

**Analog:** dieselbe Datei

**Der Schalterleser, den die drei AUTH-07-Werte teilen** (Zeilen 174-198):

```python
def _switch(env: Mapping[str, str] | None, name: str, *, default: bool) -> bool:
    """One switch, with a blank value counting as unset and a typo counting as nothing."""
    source = {} if env is None else env
    value = (source.get(name) or "").strip().lower()
    if not value:
        return default
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    logger.warning(
        "%s is set to a value that is neither on nor off, so it keeps its default (%s). "
        "The values this switch understands are %s and %s.",
        name, default, ", ".join(sorted(_TRUE_VALUES)), ", ".join(sorted(_FALSE_VALUES)),
    )
    return default
```

**Die Listenzerlegung** (Zeilen 201-214):

```python
def _entries(env: Mapping[str, str] | None, name: str) -> tuple[str, ...]:
    """Split, strip, drop the blanks, keep the first of a duplicate, keep the order."""
    source = {} if env is None else env
    raw = (source.get(name) or "").strip()
    entries: list[str] = []
    for item in raw.split(","):
        candidate = item.strip()
        if candidate and candidate not in entries:
            entries.append(candidate)
    return tuple(entries)
```

**Der Einbauort für den Admin-Vorrang** (Zeilen 129-135):

```python
def client_policy(env: Mapping[str, str] | None = None) -> ClientPolicy:
    """Read the three switches. The environment is a parameter, as everywhere here."""
    return ClientPolicy(
        dcr_enabled=_switch(env, ENV_DCR, default=True),
        allowlist_only=_switch(env, ENV_ALLOWLIST_ONLY, default=False),
        allowed=_entries(env, ENV_ALLOWED_CLIENTS),
    )
```

Ein Declarative-Settings-`checkbox` liefert einen booleschen Wert, nicht `"on"`/`"off"`.
`_switch` kennt heute nur Zeichenketten. Die Admin-Quelle braucht also entweder eine
Normalisierung auf dieselben `_TRUE_VALUES`/`_FALSE_VALUES` oder einen zweiten,
ausdrücklich benannten Zweig. Stiller Umgang mit einem unbekannten Wert ist hier verboten,
das ist die ganze Begründung des Log-Zweigs oben.

**Harte URL-Regel als Muster für die Public-URL-Prüfung** (Zeilen 138-171):

```python
def redirect_uri_allowed(value: str) -> bool:
    """Whether this address may be registered as a return target (D-35)."""
    parts = urlsplit((value or "").strip())
    if parts.scheme not in ("https", "http"):
        return False
    if parts.fragment:
        return False
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        return False
    if not host or parts.username or parts.password:
        return False
    if port is not None and not 0 < port <= 65535:
        return False
    if parts.scheme == "https":
        return True
    return host.lower() in LOOPBACK_HOSTS
```

---

### `src/mcp_connector/exapp/lifecycle.py` (geändert, lifecycle, request-response)

**Analog:** dieselbe Datei

**Der `enabled=1`-Zweig, an den die zwei neuen Registrierungen kommen** (Zeilen 75-96):

```python
    async def enabled(request: Request) -> Response:
        """Confirm the enable or disable call with an empty ``error`` field."""
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        value = request.query_params.get("enabled", "")
        if value not in ENABLED_VALUES:
            return json_response({"error": "enabled must be 0 or 1"}, status_code=400)

        if value == "1":
            try:
                await settings_form.register_settings_form(env=env)
            except Exception:
                # Same asymmetry as the init progress push: a non empty error field makes
                # AppAPI disable the app again at once, while a missing signpost costs
                # discoverability and this one line (pitfall 11).
                logger.error("the settings form registration failed, the signpost is missing")
        # enabled=0 registers nothing and unregisters nothing.
        return json_response({"error": ""})
```

Die Admin-Form und die occ-Kommando-Registrierung gehören in genau diesen Zweig, jede in
ihrem eigenen `try`, mit derselben Fehlertoleranz. Ein gefülltes `error`-Feld deaktiviert die
App sofort wieder (Recherche, "Registrierung gehört in denselben enabled=1-Zweig"). Abmelden
muss niemand: `unregisterExApp` räumt Settings-Forms und occ-Kommandos selbst weg.

---

### `src/mcp_connector/exapp/purge.py` (neu, route/handler + batch)

Zwei Analoge, weil die Datei zwei Hälften hat.

**Analog A für die Boundary:** `src/mcp_connector/exapp/lifecycle.py`

**Factory statt Registrierung am Singleton** (Zeilen 50-56 und 98-102):

```python
def lifecycle_routes(env: Mapping[str, str] | None = None) -> list[Route]:
    """Build the three AppAPI routes against one environment."""
    ...
    return [
        Route("/heartbeat", heartbeat, methods=["GET"]),
        Route("/init", init, methods=["POST"]),
        Route("/enabled", enabled, methods=["PUT"]),
    ]
```

**Die Doppelsicherung, wörtlich das Muster für den Purge-Handler** (Zeilen 105-127):

```python
def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    """Return the Nextcloud user id of this request, or the response that ends it."""
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        # No detail, no WWW-Authenticate: the caller is a proxy, and every hint here would
        # only tell an attacker which of the checks rejected the request (T-02-03).
        return json_response({}, status_code=401)


def _text(body: str, status_code: int) -> Response:
    return Response(body, status_code=status_code, media_type="text/plain", headers=NO_STORE)
```

`HEADER_ORIGIN_IP = "x-origin-ip"` (Zeile 45). Die zweite Hälfte der Kontrolle ist eine
Nicht-Aktion: der Handler bekommt **keinen** Eintrag in `appinfo/info.xml`, genau wie
`/heartbeat`, `/init` und `/enabled` (T-02-20, Pitfall 13 der Recherche).

**Analog B für die Widerrufsschleife:** `src/mcp_connector/oauth/provider.py::sweep_abandoned`
(Zeilen 971-992) und `_hand_back` (Zeilen 929-953):

```python
        swept = 0
        for row in rows:
            try:
                password = await store.app_password(row.auth_id)
            except Exception:
                logger.error("the app password of an abandoned sign in could not be read back")
                password = None
            if password and await loginflow.revoke_app_password(
                row.nc_user, password, env=self._env
            ):
                swept += 1
            else:
                logger.warning("an abandoned sign in was dropped without handing its password back")
            await store.delete_authorization(row.auth_id)
        return swept
```

Drei Eigenschaften daraus gelten auch für den Purge: die Zeile geht auch dann, wenn der
Widerruf scheiterte; jeder Fehlschlag ist eine Logzeile ohne Wert; gezählt wird, nicht
protokolliert (Security Domain, V7: "Anzahl, nicht Werte").

**Der Widerruf selbst, fertig vorhanden** (`oauth/loginflow.py` Zeilen 239-274):

```python
async def revoke_app_password(
    login_name: str, app_password: str, *, env: Mapping[str, str] | None = None
) -> bool:
    """Remove one app password again, authenticated with exactly that app password."""
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{APP_PASSWORD_PATH}"
    client = shared_client()

    try:
        response = await client.request(
            "DELETE",
            url,
            headers=dict(OCS_HEADERS),
            auth=httpx.BasicAuth(login_name, app_password),
            timeout=REVOKE_TIMEOUT,
        )
    except httpx.HTTPError:
        logger.error("the app password deletion at %s did not reach Nextcloud", url)
        return False

    if response.status_code in (200, 401):
        return True

    logger.error("the app password deletion at %s answered %s", url, response.status_code)
    return False
```

`APP_PASSWORD_PATH = "/ocs/v2.php/core/apppassword"` (Zeile 72), `REVOKE_TIMEOUT = 5.0`
(Zeile 92). 401 gilt als Erfolg, weil es "existiert nicht mehr" bedeutet.

**Reihenfolge im Handler, aus Pattern 4 der Recherche:** App-Passwörter widerrufen, dann
Store-Zeilen löschen, dann den Data Key entfernen. Wer den Key zuerst löscht, kann die
Passwörter nicht mehr entschlüsseln.

---

### `src/mcp_connector/exapp/occ.py` (neu, provider/registration, request-response)

**Analog:** `src/mcp_connector/exapp/settings_form.py::register_settings_form` (Zeilen 80-108,
oben vollständig zitiert)

Identische Form: URL aus `config.exapp_settings(env).base_url`, `OCS_HEADERS` plus
`appapi_auth_headers("")`, `shared_client()`, ein `await client.post(...)`, ein `try` gegen
`httpx.HTTPError`, eine Statusprüfung mit `// 100 != 2`, nie eine Ausnahme nach draußen.
Es ändern sich nur Pfad und Body:

```python
# Aus 05-RESEARCH.md, "occ-Kommando registrieren" (verifiziert gegen app_api v34.0.3,
# appinfo/routes.php OccCommand#registerCommand und lib/Service/ExAppOccService.php):
#
# POST {base}/ocs/v2.php/apps/app_api/api/v1/occ_command
# json = {
#   "name": "mcp_connector:purge",
#   "description": "Revoke every MCP connection of this instance and delete all stored data.",
#   "hidden": 0,
#   "arguments": [],
#   "options": [{"name": "force", "mode": "none", "description": "Do not ask."}],
#   "usages": ["mcp_connector:purge --force"],
#   "execute_handler": "purge",      # eine Route auf UNS, absichtlich NICHT in <routes>
# }
```

---

### `src/mcp_connector/oauth/store.py` (geändert, model/repository, CRUD)

**Analog:** dieselbe Datei

**Lesemethode mit optionalem Limit, exakt die Form, die der Purge braucht** (Zeilen 647-680):

```python
    async def authorizations_of_client(
        self, client_id: str, limit: int | None = None
    ) -> list[AuthorizationRow]:
        """The connections booked under one client, oldest first (WR-04).

        ``limit`` is optional since BL-01, and the default is deliberately "all of them".
        A capped read in front of a cascading delete is not a bound on the work, it is a
        bound on how many credentials are handed back before the rest is destroyed.

        ``None`` travels as ``LIMIT -1``, which is SQLite's own spelling of "no upper bound".
        The statement therefore stays one constant string with one placeholder, and no branch
        of this method builds SQL out of a value.
        """
        capped = _NO_LIMIT if limit is None else limit

        def work(conn: sqlite3.Connection) -> list[AuthorizationRow]:
            rows = conn.execute(
                "SELECT auth_id, client_id, nc_user, scopes, resource, created_at, "
                "revoked_at, cleanup_at FROM authorizations WHERE client_id = ? "
                "ORDER BY created_at LIMIT ?",
                (client_id, capped),
            ).fetchall()
            return [_authorization_row(row) for row in rows]

        return await self._read(work)
```

Eine `all_authorizations()` für den Purge kopiert das ohne die `WHERE`-Klausel und ohne
Limit. Der Purge muss **alle** Zeilen sehen, auch die mit `revoked_at IS NOT NULL`:
`authorizations_of_user` (Zeilen 697-706) filtert `revoked_at IS NULL` und ist damit die
falsche Vorlage. `abandoned_authorizations` filtert ebenfalls und ist genauso ungeeignet
(vom Kommentar in `provider.end_connection`, Zeilen 762-766, ausdrücklich benannt).

**Löschmuster im Schreibpfad** (Zeilen 1137-1154):

```python
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            conn.execute(
                "DELETE FROM clients WHERE last_used_at IS NULL AND registered_at < ? ...",
                (moment - UNUSED_CLIENT_TTL,),
            )
            ...

        await self._write(work)
```

`_write` läuft in `BEGIN IMMEDIATE` bis `COMMIT` (Zeilen 1170-1203), ein Rumpf ist also
atomar. Der Schema-Block (Zeilen 144-219) zeigt, dass `flows`, `authorizations`,
`auth_codes`, `refresh_tokens` und `access_tokens` an `clients` bzw. `authorizations`
kaskadieren; `user_access` hängt an nichts und muss beim Purge einzeln geleert werden.

---

### `src/mcp_connector/oauth/crypto.py` (geändert, service, request-response)

**Analog:** dieselbe Datei, `_write_key` (Zeilen 273-295)

```python
async def _write_key(settings: config.ExAppSettings, value: str) -> None:
    """Store a freshly created key as a sensitive value. One attempt, no retry."""
    url = f"{settings.base_url}{EXAPP_CONFIG_PATH}"
    client = shared_client()
    try:
        response = await client.post(
            url,
            json={"configKey": CONFIG_KEY, "configValue": value, "sensitive": 1},
            headers=_headers(settings),
        )
    except httpx.HTTPError:
        # Neither the key nor a header value appears in this line.
        logger.error("the ExApp configuration at %s could not be written", url)
        raise ToolError(...) from None

    if response.status_code // 100 != 2:
        raise ToolError(...)
```

Das Löschen ist derselbe Aufruf mit `DELETE` auf `EXAPP_CONFIG_PATH` (der Kommentar in
Zeilen 90-98 nennt alle drei Verben dieser Ressource). Das Verb reist über
`client.request("DELETE", url, ...)`, wie es `loginflow.revoke_app_password` vormacht.

---

### `src/mcp_connector/entry_exapp.py` (geändert, wiring)

**Analog:** dieselbe Datei, Zeilen 150-164:

```python
    for route in (
        *lifecycle_routes(env),
        *metadata_routes(env, dcr_enabled=policy.dcr_enabled),
        *connect_routes(env, store_provider=store, throttle=counters),
        *connections_routes(
            env,
            store_provider=store,
            end_connection=provider.end_connection,
            throttle=counters,
        ),
        *auth_routes(env, provider=provider, throttle=counters),
        *consent_routes(env, provider=provider, throttle=counters),
    ):
        app.router.routes.append(route)
    return app
```

Die Purge-Route kommt in genau diese Aufzählung, mit `store_provider=store`, weil sie den
einen Store dieser Anwendung braucht. Der Kommentar direkt darüber (Zeilen 124-149) ist die
Begründung, die jeder neue Eintrag erbt: nichts davon darf am geteilten MCP-Serverobjekt
hängen, sonst wächst dem Standalone-HTTP-Modus aus Phase 1 ein Endpunkt zu (D-23).

Die `--force`-Pflicht des occ-Kommandos wird auf der AppAPI-Seite deklariert (`options` im
`occ.py`-Body), der Handler muss sie zusätzlich selbst prüfen: was AppAPI übergibt, ist
Eingabe.

---

### `tests/integration/test_permission_parity_share.py` (neu, test)

**Analog:** `tests/integration/test_permission_fidelity_exapp.py` (276 Zeilen, komplettes
Vorbild)

**Die Regel, die dieser Test nicht brechen darf** (Zeilen 12-17 des Analogs):

```
Nothing in this file builds a Credentials object or an ``httpx.BasicAuth`` for Nextcloud. The
only credential is each user's app password in a Basic header on the transport client, the
same header ``tests/compat/modern_client_check.py`` uses. Everything past the header is the
deployed topology: HaRP, the reverse proxy, the ExApp container and Nextcloud's own
permission check.
```

Das ist wörtlich das Warnzeichen aus Pitfall 6 der Recherche.

**Sitzungshelfer und Basic-Header** (Zeilen 58-84):

```python
EXAPP_MCP_PATH = "/exapps/mcp_connector/mcp"


def _basic(user: str, secret: str) -> str:
    """A Basic header, exactly what a client hands to HaRP; HaRP resolves the identity."""
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()


@asynccontextmanager
async def _mcp_session(base: str, user: str, secret: str) -> AsyncIterator[Client]:
    url = base.rstrip("/") + EXAPP_MCP_PATH
    async with httpx2.AsyncClient(
        headers={"Authorization": _basic(user, secret)},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            yield client
```

**Env-Fixture mit Skip statt Fehler** (Zeilen 101-126):

```python
@pytest.fixture
def chain_env() -> dict[str, str]:
    required = {
        "base": "NC_MCP_URL",
        "app_id": "APP_ID",
        "alice": "NC_MCP_TEST_USER",
        "alice_pw": "NC_MCP_TEST_APP_PASSWORD",
        "bob": "NC_MCP_TEST_USER2",
        "bob_pw": "NC_MCP_TEST_APP_PASSWORD2",
    }
    values = {key: (os.environ.get(name) or "").strip() for key, name in required.items()}
    missing = sorted(required[key] for key, value in values.items() if not value)
    if missing:
        pytest.skip(f"no ExApp topology configured (missing: {', '.join(missing)})")
    assert values["app_id"] == "mcp_connector", ...
    assert values["alice"] != "admin", "the chain test runs as normal users, never as admin"
    return values
```

**Payload-Dekodierung und Marker-Fixture** (Zeilen 87-98 und 129-154):

```python
def _payload(result: Any) -> dict[str, Any]:
    """Decode the compact JSON a tool answers with (structured_output=False)."""
    assert not result.is_error, f"the tool call ended in an error: {_texts(result)!r}"
    texts = _texts(result)
    assert texts, f"the tool answered without any text content: {result!r}"
    data = json.loads(texts[0])
    assert isinstance(data, dict), f"the tool did not answer with an object: {data!r}"
    return data


@pytest.fixture
async def alices_content(chain_env: dict[str, str]) -> dict[str, str]:
    marker = f"nurfueralice{uuid.uuid4().hex[:10]}"
    file_path = f"/{marker}.md"
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        uploaded = _payload(await c.call_tool("files_upload", {...}))
        assert uploaded.get("path") == file_path, f"alice's upload did not land: {uploaded!r}"
```

**Positivkontrolle vor jedem Leak-Test** (Zeilen 19-28 und die Testreihenfolge im Analog).
Die vier neuen Aussagen von SC3 hängen sich an genau dieses Muster: bob findet die read-only
geteilte Datei (positiv), bob findet die ungeteilte nicht (existiert schon), bob liest die
geteilte, bob kann **nicht** in den read-only geteilten Ordner hochladen. Der letzte Fall
kopiert die Refusal-Assertion aus Zeilen 257-277:

```python
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        try:
            result = await c.call_tool("files_read", {"path": file_path})
        except Exception as exc:  # a raised protocol error is also a refusal, not content
            message = str(exc)
        else:
            assert result.is_error, f"bob read alice's file over the chain: {_texts(result)!r}"
            message = " ".join(_texts(result))
    assert SECRET_LINE not in message, "the refusal carried the content of alice's file"
```

---

### `scripts/bootstrap_exapp.sh` (geändert, script/fixture)

**Analog:** dieselbe Datei

**Idempotente Fixture-Funktion mit occ, plus Nachweis statt Annahme** (Zeilen 281-306):

```bash
ensure_calendar() {
  local uid="$1" name="$2" attempt
  # The create races the DAV app warming up right after the install, and a create that
  # failed transiently must not pass as "already there".
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    occ dav:create-calendar "$uid" "$name" >/dev/null 2>&1 || true
    if occ dav:list-calendars "$uid" 2>/dev/null | grep "$name" >/dev/null; then
      echo "calendar ${uid}/${name}: present (attempt ${attempt})"
      return 0
    fi
    sleep 5
  done
  echo "ERROR: calendar ${uid}/${name} did not appear within 60s." >&2
  return 1
}
```

**Dateien im Home anlegen, ohne einen ersten Login zu haben** (Zeilen 323-334):

```bash
ensure_files_home() {
  local uid="$1"
  dc exec -T --user www-data "${SERVICE}" sh -c \
    "mkdir -p 'data/${uid}/files' && printf 'Initialised by scripts/bootstrap_exapp.sh.\n' \
      > 'data/${uid}/files/Readme.md'"
  if occ files:scan "$uid" >/dev/null 2>&1; then
    echo "files home ${uid}: initialised"
  else
    echo "files home ${uid}: scan failed" >&2
    return 1
  fi
}
```

Der Kommentar darüber (Zeilen 308-322) ist die Warnung, die für die neue Share-Fixture
genauso gilt: `occ user:add` feuert kein erstes Login, also existiert nichts von dem, was ein
echter Login anlegt, und eine leere Datei-Heimat lässt WebDAV-SEARCH mit 500 statt leer
antworten.

**Aufrufreihenfolge im Hauptteil** (Zeilen 648-659) und **Env-Ausgabe** (Zeilen 696-716):

```bash
ensure_user alice "${ALICE_PASSWORD}"
ensure_user bob "${BOB_PASSWORD}"
ensure_calendar alice personal
...
ensure_files_home alice
ensure_files_home bob

umask 077
cat >"${ENV_FILE}" <<EOF
NC_MCP_URL=${BASE_URL}
NC_MCP_TEST_USER=alice
NC_MCP_TEST_APP_PASSWORD=${ALICE_APP_PASSWORD}
NC_MCP_TEST_USER2=bob
NC_MCP_TEST_APP_PASSWORD2=${BOB_APP_PASSWORD}
...
EOF
```

Die neue Fixture (alice teilt einen Ordner read-only mit bob, ein zweiter bleibt ungeteilt)
gehört als `ensure_readonly_share` zwischen `ensure_files_home` und den App-Passwort-Block,
und ihre Pfade gehören als zwei neue Variablen in denselben Heredoc, damit der Test sie über
`os.environ` findet und ohne Topologie skippt.

---

### `tests/unit/test_exapp_admin_settings.py` und `tests/unit/test_exapp_purge.py` (neu, test)

**Analog A:** `tests/unit/test_exapp_lifecycle.py`

**Env-Konstanten und respx-Ziel** (Zeilen 27-42):

```python
APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
BASE_URL = "http://nc.test"
PUBLIC_URL = "https://cloud.example.test/exapps/mcp_connector"

ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
    config.ENV_PUBLIC_URL: PUBLIC_URL,
}

SETTINGS_URL = f"{BASE_URL}/ocs/v2.php/apps/app_api/api/v1/ui/settings"
```

**Ein Schema Feld für Feld auf dem Draht prüfen** (Zeilen 244-263):

```python
@pytest.mark.anyio
@respx.mock
async def test_the_registered_form_is_the_scheme_of_the_ui_spec() -> None:
    """The schema table of 04-UI-SPEC, asserted key by key on the wire."""
    route = respx.post(SETTINGS_URL).mock(
        return_value=httpx.Response(200, json={"ocs": {"meta": {"status": "ok"}}})
    )

    await settings_form.register_settings_form(env=ENV)

    assert route.called
    scheme = json.loads(route.calls.last.request.content)["formScheme"]
    assert scheme["id"] == "mcp_connector_settings"
    assert scheme["section_type"] == "personal"
    assert scheme["doc_url"] == f"{PUBLIC_URL}/connections"
```

Für die Admin-Form ist die Entsprechung: `section_type == "admin"`, die vier Feld-Ids in der
Reihenfolge des Schemas, und ein Negativ-Gate `"sensitive" not in request.content` (die
Falle der Recherche, ICrypto-Blob).

**App-Kontext-Assertion** (Zeilen 303-317):

```python
    sent = route.calls.last.request
    expected = base64.b64encode(f":{APP_SECRET}".encode()).decode()
    assert sent.headers["AUTHORIZATION-APP-API"] == expected
    assert sent.headers["EX-APP-ID"] == APP_ID
    assert sent.headers["OCS-APIRequest"] == "true"
```

**Fehlertoleranz des `enabled=1`-Zweigs** (Zeilen 224-241):

```python
def test_enabled_answers_200_when_the_registration_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pitfall 11: a 500 out of /enabled makes AppAPI disable the app again at once."""

    async def boom(*, env: object = None) -> None:
        raise httpx.ConnectError("nextcloud is not reachable")

    monkeypatch.setattr(settings_form, "register_settings_form", boom)
    with client() as http:
        response = http.put("/enabled?enabled=1", headers=appapi_headers())
    assert response.status_code == 200
    assert response.json() == {"error": ""}
    assert response.headers["cache-control"] == "no-store"
```

**Analog B für den Lesepfad:** `tests/unit/test_oauth_crypto.py` (Zeilen 36-40):

```python
CONFIG_URL = f"{BASE_URL}{crypto.EXAPP_CONFIG_PATH}"
#: The read is its own route and its own verb (measured against AppAPI 34.0.0 in plan
#: 03-08): a POST to /get-values with a JSON body, not a GET with a query parameter.
READ_URL = f"{CONFIG_URL}{crypto.CONFIG_READ_SUFFIX}"
```

und die Antwortformen als Helfer (`ocs_body`, `stored`), die dieselbe Datei über
`respx.post(READ_URL).mock(...)` an rund fünfzehn Stellen benutzt.

**Analog C für die Purge-Tests:** `tests/unit/test_oauth_abuse.py`, `Deployment`-Fixture
(Zeilen 126-183) plus die Store-Aussaat `_seed_connection` (Zeile 911). Der Store ist dort
eine SQLite-Datei in `tmp_path`, jede Nextcloud-Antwort kommt aus respx, und die
Abschnittsmarken (`# --- D-40 case 1: ...`) sind die Form, in der ein Kriterienkatalog im
Testcode geführt wird. Für den Purge sind das die Aussagen aus dem Runbook: jedes
App-Passwort widerrufen, jede Tabelle leer, Data Key weg, Reihenfolge eingehalten, Handler
über den PHP-Proxy nicht erreichbar.

---

### `tests/unit/test_exapp_env_setup.py` (geändert, Manifest-Gate)

**Analog:** dieselbe Datei

**Das Gate, das die Routenzahl einfriert** (Zeilen 637-668):

```python
def test_the_manifest_declares_exactly_the_thirteen_routes_of_this_phase(
    manifest_root: etree._Element,
) -> None:
    routes = [
        ((route.findtext("url") or "").strip(), (route.findtext("access_level") or "").strip())
        for route in manifest_root.findall(".//route")
    ]
    assert routes == [
        ("^/mcp/?$", "PUBLIC"),
        ("^/\\.well-known/oauth-protected-resource/mcp$", "PUBLIC"),
        ...
        ("^/connections/?$", "PUBLIC"),
    ]
```

Dieses Gate ist in Phase 5 das Sicherheitsnetz für Pitfall 13: es bleibt bei dreizehn, weil
der Purge-Handler keine Route bekommt. Ein Plan, der es auf vierzehn hebt, hat den Fehler
gemacht, den die Recherche benennt. Die Datei führt außerdem `INFO_XML` (Zeile 43) und einen
gehärteten Parser (`hardened_parser`), also ist sie auch der Ort für ein neues Gate auf die
Store-Beschreibung (keine Backticks, keine Tabelle, Absätze durch Leerzeilen) und für die
`<default>`-Regel aus Pitfall 3 (befüllt oder gar nicht da).

Ein zweiter Grund, diese Datei anzufassen: sie prüft in
`test_the_bootstrap_registration_declares_the_same_thirteen_routes` (Zeile 920), dass
`scripts/bootstrap_exapp.sh` dieselben Routen registriert. Wer am Manifest oder am
Bootstrap dreht, dreht an beiden.

---

### `docs/uninstall.md` (neu) und `docs/client-setup.md` (geändert)

**Analog für das Runbook:** `docs/exapp-install.md` (362 Zeilen)

Die Gliederung, die der Planner übernehmen sollte, weil sie in diesem Repo etabliert ist:

```
# ExApp installation
## Topology
## Install
## Evidence
### 1. The app is registered and enabled
### 2. The container the daemon started is healthy
...
## Development loop
## Known pitfalls
## Security notes for production
## Related
```

Der Abschnitt `## Evidence` mit durchnummerierten, kopierbaren Prüfungen ist genau die Form,
die SC2 braucht: Zeile A (UI-Weg, was bleibt zurück) und Zeile B (occ-Weg, nichts bleibt
zurück). Die Gegenproben stehen fertig in der Recherche, Abschnitt "Code Examples".

**Analog für die zwei Client-Kapitel:** `docs/client-setup.md`, die vorhandenen Abschnitte
`### Claude.ai, step by step` (Zeile 316), `### ChatGPT, step by step` (Zeile 341) und
`### Cursor and other clients with a cursor:// style callback` (Zeile 359). Open WebUI folgt
der Form der ersten zwei (Schritt für Schritt plus die eine Stolperstelle aus Pitfall 10),
MUCGPT eher der Form von Cursor, weil dort eine Einschränkung erklärt wird und keine
Erfolgsanleitung. Zwei Aussagen in der Datei sind veraltet und müssen mit: "The full client
matrix ... follows in a later phase" und die Zahlen "15 tools" bzw. "twelve routes" in
`docs/exapp-install.md`, während das Manifest dreizehn Routen führt.

---

### `docs/faq.md` (neu) und die drei READMEs

**Analog:** `docs/privacy.md`, Abschnitt `## Deletion and user control` (Zeilen 82-92):

```markdown
## Deletion and user control

- A user pauses or resumes their own access, and disconnects any connected
  assistant, on the connector's own `/connections` page. Disconnecting hands the
  app password back to Nextcloud, so the entry also disappears from the user's
  Devices and sessions in Nextcloud.
- A user can revoke access from the Nextcloud side at any time, under Settings,
  Security, Devices and sessions.
- Uninstalling the app removes its container and its database, and with it every
  token and encrypted app password it held.
```

Die dritte Zeile ist nach dieser Phase **falsch** und die FAQ darf sie nicht zitieren, sie
muss sie ersetzen: das UI-Remove entfernt weder Volume noch Data Key noch die
App-Passwörter. `docs/privacy.md` ist damit selbst ein Kandidat für eine Korrektur im
gleichen Plan wie die FAQ, sonst stehen zwei Wahrheiten im Repo.

**Analog für die dreisprachige Pflege:** `README.md`, `README.de.md`, `README.fr.md` haben
identische Überschriftenfolge (`## Status`, `### OAuth 2.1`, `## Quickstart`, ...). Ein neuer
`## FAQ` muss an derselben Position in allen drei Dateien erscheinen, mit echten Umlauten in
`.de` und Accents in `.fr`. `## Status` sagt in allen drei "phase 1 (server core)" und ist
seit vier Phasen falsch.

**Store-Text:** `appinfo/info.xml` Zeilen 13-30 zeigen die vorhandene dreisprachige
`<description>` in CDATA. Zwei Regeln aus der Recherche gelten für jede Ergänzung dort:
Absätze durch **Leerzeilen** trennen (die Instanz rendert mit `breaks: false`, die vier
heutigen Sätze sind dort ein Klumpen), und keine Backticks, keine Tabellen, keine Bilder,
weil `dompurify` sie in der Instanzansicht entfernt.

---

## Shared Patterns

### 1. Ausgehender Nextcloud-Aufruf im App-Kontext

**Quelle:** `src/mcp_connector/exapp/settings_form.py` Zeilen 86-108, `src/mcp_connector/oauth/crypto.py` Zeilen 298-310
**Gilt für:** `exapp/admin_settings.py`, `exapp/config_values.py`, `exapp/occ.py`, den Data-Key-Löschpfad in `oauth/crypto.py`

```python
settings = config.exapp_settings(env)
url = f"{settings.base_url}{SOME_OCS_PATH}"
headers = dict(OCS_HEADERS)
headers.update(
    appapi_auth_headers(
        "",                      # empty user id: the app speaks about itself
        app_id=settings.app_id,
        app_version=settings.app_version,
        aa_version=settings.aa_version,
        app_secret=settings.app_secret,
    )
)
client = shared_client()          # refuses redirects, carries this project's timeouts
try:
    response = await client.post(url, json=..., headers=headers)
except httpx.HTTPError:
    logger.error("... %s did not reach Nextcloud", url)   # never a value of the request
    return
if response.status_code // 100 != 2:
    logger.error("... %s answered %s", url, response.status_code)
```

Vier Regeln, die dieses Muster trägt (aus dem Modulkopf von `oauth/loginflow.py`, Zeilen
10-18): Ziel immer aus der konfigurierten Base-URL und nie aus einer Antwort; Client immer
`shared_client()`; ein Versuch, keine Retry-Schleife (D-37); kein Wert eines Requests in
einer Logzeile.

### 2. Boundary-Guard für einen Endpunkt, den nur der Daemon aufrufen darf

**Quelle:** `src/mcp_connector/exapp/lifecycle.py` Zeilen 105-127
**Gilt für:** `exapp/purge.py`

```python
if HEADER_ORIGIN_IP in request.headers:      # "x-origin-ip" == the PHP proxy
    return _text("Not Found", status_code=404)
try:
    return require_appapi(request, env=env)
except (AppApiRejected, ToolError):
    return json_response({}, status_code=401)
```

Plus die Nicht-Aktion: kein `<route>`-Eintrag in `appinfo/info.xml`. Der Kommentar dort
(Zeilen 58-67) ist die Begründung und muss um den Purge-Handler ergänzt werden, weil dieser
Kommentar der einzige Ort ist, an dem die undeklarierten Pfade überhaupt auftauchen.

### 3. Fehlermodell der Registrierungen im `enabled=1`-Zweig

**Quelle:** `src/mcp_connector/exapp/lifecycle.py` Zeilen 85-96
**Gilt für:** jede neue Registrierung (Admin-Form, occ-Kommando)

Ein `try`/`except Exception` pro Registrierung, eine Logzeile, `{"error": ""}` als Antwort.
Ein gefülltes `error` deaktiviert die App sofort wieder.

### 4. Aufräumen mit Widerruf: Reihenfolge und Bestehenlassen der Löschung

**Quelle:** `src/mcp_connector/oauth/provider.py` Zeilen 929-953 und 971-992
**Gilt für:** `exapp/purge.py`, `oauth/store.py`

Erst Notiz/Lesen, dann Widerruf, dann Löschen. Die Zeile geht auch bei gescheitertem
Widerruf, weil ein Ciphertext ohne Nutzungsrecht schlimmer ist als ein verlorener Datensatz
(D-34). Gezählt wird, nicht protokolliert.

### 5. Maskierung und Nichtwiederholung von Werten

**Quelle:** `src/mcp_connector/config.py` Zeilen 114-118 (`ExAppSettings.__repr__`),
`src/mcp_connector/oauth/registry.py` Zeilen 99-103 (`ClientPolicy.__repr__`),
`src/mcp_connector/oauth/crypto.py` Zeilen 112-120 (`DecryptionRejected`)
**Gilt für:** jedes neue Dataclass-Objekt und jede neue Logzeile der Phase

```python
    def __repr__(self) -> str:
        return (
            f"ClientPolicy(dcr_enabled={self.dcr_enabled!r}, "
            f"allowlist_only={self.allowlist_only!r}, allowed={len(self.allowed)} entries)"
        )
```

Der Purge-Log nennt Anzahlen, nie Konten, nie Client-Namen, nie ein Passwortfragment.
`tests/unit/test_oauth_abuse.py` führt dafür zwei fertige Gates:
`test_no_rejection_ever_repeats_the_value_it_received` (Zeile 828) und
`test_no_rejection_writes_a_received_value_to_the_log` (Zeile 838), beide auf DEBUG-Level.

### 6. Env als Parameter, überall

**Quelle:** `src/mcp_connector/exapp/lifecycle.py` Zeilen 50-55, `src/mcp_connector/config.py` durchgehend
**Gilt für:** jede neue Funktion der Phase

`env: Mapping[str, str] | None = None`, aufgelöst als `os.environ if env is None else env`.
Das ist der Grund, warum jeder Unit-Test seine eigene Anwendung bauen kann, ohne die
Prozessumgebung anzufassen.

### 7. Testmarker und Skip-statt-Fehler

**Quelle:** `tests/conftest.py` Zeilen 71-86, `tests/integration/test_permission_fidelity_exapp.py` Zeilen 54 und 110-121
**Gilt für:** beide neuen Integrationstests

```python
pytestmark = [pytest.mark.integration, pytest.mark.anyio]
...
if missing:
    pytest.skip(f"no ExApp topology configured (missing: {', '.join(missing)})")
```

Ohne `NC_MCP_URL` skippt die Suite, statt rot zu werden. `addopts` deselektiert den
`integration`-Marker ohnehin.

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `tests/integration/test_credential_flood.py` | test (integration) | batch, parallel | Im Repo existiert kein Lasttest. Es gibt keinen `asyncio.gather`-Lauf über N HTTP-Requests, keine Messung gegen ein Container-Access-Log und keinen Test, dessen Ergebnis eine Zahl für die Doku ist statt einer Zusicherung. Der Planner nimmt hier den Vorschlag aus 05-RESEARCH.md, "Negativ-Credential-Lasttest" (zwei getrennte Läufe: ungültiger Bearer, ungültiges Basic; Messgröße Nextcloud-Requests pro Angreifer-Request; `occ security:bruteforce:attempts` und `... reset <ip>` als Rahmen). Übernehmbar sind nur die Ränder: die `chain_env`-Fixture und `_basic()` aus `test_permission_fidelity_exapp.py` und die Abschnittsgliederung von `tests/unit/test_oauth_abuse.py`. |

Teilweise ohne Vorbild, aber mit tragfähigem Rahmen:

- `docs/faq.md`: kein FAQ-Dokument existiert. `docs/privacy.md` liefert Substanz und Ton,
  nicht die Form. Achtung, es liefert außerdem einen Satz, der nach dieser Phase falsch ist.
- Die vier Feldtypen der Admin-Form: das Repo hat noch nie ein Declarative-Settings-Feld
  ausgeliefert (`fields` ist heute bewusst leer). Die Typenliste ist in der Recherche
  verifiziert (`text`, `password`, `email`, `tel`, `url`, `number`, `checkbox`,
  `multi-checkbox`, `radio`, `select`, `multi-select`, kein Button).

---

## Metadata

**Durchsuchter Bereich:** `src/mcp_connector/**`, `tests/**`, `docs/**`, `scripts/**`,
`appinfo/`, Repo-Wurzel
**Gelesene Analog-Dateien:** 14 (`exapp/settings_form.py`, `exapp/lifecycle.py`,
`oauth/crypto.py`, `config.py`, `oauth/registry.py`, `oauth/loginflow.py`,
`oauth/connections.py` (Auszug), `oauth/provider.py` (Auszug), `oauth/store.py` (Auszug),
`entry_exapp.py`, `appinfo/info.xml`, `tests/integration/test_permission_fidelity_exapp.py`,
`tests/conftest.py`, `tests/unit/test_exapp_lifecycle.py` (Auszug)), plus gezielte
Struktur-Greps in `tests/unit/test_exapp_env_setup.py`, `tests/unit/test_oauth_abuse.py`,
`tests/unit/test_oauth_crypto.py`, `scripts/bootstrap_exapp.sh`, `exapp/ui/strings.py` und
allen betroffenen `docs/`-Dateien
**Pattern-Extraktion:** 2026-08-19
