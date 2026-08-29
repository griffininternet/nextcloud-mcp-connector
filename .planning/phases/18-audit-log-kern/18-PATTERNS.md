# Phase 18: Audit-Log Kern - Muster-Karte

**Kartiert:** 2026-08-29
**Untersuchte Dateien:** 26 (10 neu, 16 geändert)
**Analoga gefunden:** 25 / 26

Diese Karte beantwortet genau eine Frage: von welcher bestehenden Datei kopiert eine neue
Datei ihr Muster, und welche Zeilen genau. Sie erfindet nichts, was nicht schon im Code
steht. Wo es kein Analog gibt, steht das ausdrücklich da (Abschnitt "Kein Analog").

Die Dateiliste stammt aus `18-CONTEXT.md` (D-01 bis D-18) und aus dem Abschnitt
"Empfohlener Schnitt" von `18-RESEARCH.md` (Zeilen 1243-1268).

---

## Dateiklassifikation

### Neue Dateien

| Neue Datei | Rolle | Datenfluss | Nächstes Analog | Passung |
|------------|-------|------------|-----------------|---------|
| `src/mcp_connector/audit/__init__.py` | config/provider | Fabrik (kein Fluss) | `src/mcp_connector/oauth/store.py:82-128, 1409-1444` | exakt |
| `src/mcp_connector/audit/store.py` | model/persistence | CRUD + batch (Abräumen) | `src/mcp_connector/oauth/store.py` (ganz) | exakt |
| `src/mcp_connector/audit/record.py` | service | event-driven (ein Eintrag je Aufruf) | `src/mcp_connector/exapp/purge.py:245-256` + `src/mcp_connector/deps.py:230-246` | Rollen-Treffer |
| `src/mcp_connector/audit/allowlist.py` | config (konstante Daten) | kein Fluss | `src/mcp_connector/exapp/config_values.py:103-135` + `tests/contract/test_tool_surface.py:34-83` | Rollen-Treffer |
| `src/mcp_connector/exapp/<prüfkommando>.py` | route/handler | request-response | `src/mcp_connector/exapp/purge.py` (ganz) | exakt |
| `tests/unit/test_audit_store.py` | test (unit) | CRUD gegen echte Datei | `tests/unit/test_oauth_store.py:1-10, 43-44` | exakt |
| `tests/unit/test_audit_record.py` | test (unit) | event-driven | `tests/unit/test_oauth_credentials.py:96-136` (FakeContext) | Rollen-Treffer |
| `tests/unit/test_exapp_<prüfkommando>.py` | test (unit) | request-response | `tests/unit/test_exapp_purge.py:107-221` | exakt |
| `tests/contract/test_audit_surface.py` | test (contract gate) | Messung über alle Werkzeuge | `scripts/check_tool_budget.py:120-157` + `tests/contract/test_tool_surface.py:709-726` | exakt |
| `tests/integration/test_appapi_users_list.py` | test (integration) | request-response | `tests/integration/test_exapp_dav_matrix.py:31-38, 58, 82-93` + `tests/conftest.py:40-65` | Rollen-Treffer |

### Geänderte Dateien

| Geänderte Datei | Rolle | Was dazukommt | Muster in derselben Datei |
|-----------------|-------|---------------|---------------------------|
| `src/mcp_connector/server/__init__.py` | server/decorator | Marker + `finally`-Zweig in `graceful` | `:68-99` (der Dekorator selbst) |
| `src/mcp_connector/deps.py` | service | `resolve_caller(ctx) -> Caller` | `:230-246` (`_oauth_identity`) |
| `src/mcp_connector/oauth/verifier.py` | service | `client_name` in `claims` und in `OAuthIdentity` | `:82-90` (`AUTH_ID_CLAIM`), `:101-125` |
| `src/mcp_connector/exapp/middleware.py` | middleware | `AUDIT_STATE_ATTR` hinterlegen | `:214-235` (`_deposit`) |
| `src/mcp_connector/exapp/config_values.py` | config | ein Schlüssel in drei Aufzählungen | `:103-135` |
| `src/mcp_connector/exapp/admin_settings.py` | config/form | ein Feld, `"default": False` | `:147-153` (`allowlist_field`) |
| `src/mcp_connector/exapp/occ.py` | config/registration | `command_schemes()` als Liste | `:72-92`, `:95-131` |
| `src/mcp_connector/exapp/lifecycle.py` | lifecycle | vierter eigener `try`-Block | `:85-110` |
| `src/mcp_connector/entry_exapp.py` | composition root | Opener bauen, Route anhängen | `:85-103`, `:168-183` |
| `src/mcp_connector/config.py` | config | `ENV_AUDIT_*` plus Leser | `:47`, `:329-348` |
| `src/mcp_connector/errors.py` | model | `ToolError(..., reason=...)` | `:9-15` |
| `src/mcp_connector/nextcloud/clients/{ocs,dav,caldav,carddav}.py` | client | `reason=` an ~7 Statusabbildungen | `ocs.py:266-296` |
| `appinfo/info.xml` | manifest | der fünfte bewusst abwesende Pfad | `:260-285` |
| `tests/contract/test_no_destructive_calls.py` | gate | zweiter Eintrag in `FILES_WITH_OWN_SQL` | `:229-236`, `:397-409` |
| `tests/unit/test_exapp_purge.py` | test | Audit-Datei überlebt den Purge | `:107-154` (`Deployment`) |
| `tests/unit/test_exapp_lifecycle.py`, `test_exapp_config_values.py`, `test_exapp_admin_settings.py` | test | zweites Kommando, sechster/siebter Schlüssel | bestehende Gleichheits-Tests |

---

## Muster-Zuweisungen

### `src/mcp_connector/audit/store.py` (model/persistence, CRUD + batch)

**Analog:** `src/mcp_connector/oauth/store.py`. Die Datei ist 1568 Zeilen lang; unten
stehen nur die Stellen, die das neue Modul erbt.

**Importblock und Typalias** (`oauth/store.py:33-49`):

```python
import asyncio
import contextlib
import hashlib
import sqlite3
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import config
from . import crypto
from .crypto import decrypt, encrypt

#: What every method below hands to the worker thread: one function, one connection, one
#: result. Naming it keeps the three wrappers at the bottom readable and typed.
type Work[T] = Callable[[sqlite3.Connection], T]
```

Zu übernehmen: alles ausser den beiden `crypto`-Importen. D-06 legt keine Geheimnisse ab,
und §11 der Recherche verbietet den Datenschlüssel ausdrücklich (der Purge löscht ihn).

**Dateiname als benannte Konstante** (`oauth/store.py:82-83`):

```python
#: The one file in the persistent volume of this app.
STORE_FILENAME = "oauth.sqlite3"
```

Der Code sagt `oauth.sqlite3`, nicht `store.sqlite3`. Das neue Gegenstück heisst analog
`AUDIT_FILENAME = "audit.sqlite3"` und wird mit `config.persistent_storage(env) /
AUDIT_FILENAME` zusammengesetzt (siehe `oauth/store.py:1439`).

**Zahlen als benannte Konstanten mit Begründungszeile** (`oauth/store.py:85-97`):

```python
# --- lifetimes ---------------------------------------------------------------------
# Every number of seconds this phase uses is one of the names below. A literal at a call
# site is a value nobody finds again when a client turns out to need a different one.

#: An authorization code is a hand over between two requests of the same browser, so it is
#: short by an order of magnitude compared to everything else here.
AUTH_CODE_TTL = 60
```

Genau diese Form für `RETENTION_DAYS = 180`, `SIZE_LIMIT_BYTES`, `SWEEP_EVERY`,
`SWEEP_USER_CHECK_EVERY` und die Schwelle aus D-12.

**Schema als Modulkonstante mit `IF NOT EXISTS`** (`oauth/store.py:158-165, 208, 236`):

```python
SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  client_id TEXT PRIMARY KEY,
  client_secret_hash TEXT,
  metadata_json TEXT NOT NULL,
  allowed INTEGER NOT NULL DEFAULT 1,
  registered_at INTEGER NOT NULL,
  last_used_at INTEGER,
...
CREATE INDEX IF NOT EXISTS authorizations_nc_user ON authorizations(nc_user);
...
CREATE INDEX IF NOT EXISTS refresh_family ON refresh_tokens(family_id);
"""
```

Die Spaltenkommentare im SQL sind Hausstil (`:166-178`) und tragen die Begründung, nicht
nur die Bedeutung. Der Schemaentwurf aus `18-RESEARCH.md:494-515` passt genau in diese
Form.

**Digest** (`oauth/store.py:251-258`):

```python
def token_hash(token: str) -> str:
    """The one form a token takes on disk. SHA-256 hex, never the token itself.

    No salt and no key stretching on purpose: these are 256 bit random values, not
    passwords, so there is nothing to brute force and a per row salt would only make the
    lookup by token impossible.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
```

Der Kettenhash folgt derselben Form (`hashlib.sha256`, Standardbibliothek, kein Schlüssel),
gibt aber nach `18-RESEARCH.md:544-549` `.digest()` statt `.hexdigest()` zurück.

**Objekt statt Modulzustand, mit Schema-Flag am Objekt** (`oauth/store.py:394-411`):

```python
class OAuthStore:
    """The persistence of the phase, bound to one file and one data key.

    Every method opens its own connection inside a worker thread and closes it again. That
    costs a fraction of a millisecond per call and buys the property this server needs
    most: no connection, no cursor and no transaction is shared between two requests, so
    two workers on the same volume behave exactly like two threads in one worker.
    """

    def __init__(self, path: Path, key: bytes) -> None:
        self._path = path
        self._key = key
        # False until this object has opened the file once (LO-02). See :meth:`_call` for
        # what it is worth and what it deliberately does not promise.
        self._schema_ready = False

    def __repr__(self) -> str:
        return f"OAuthStore(path={self._path!r}, key='***')"
```

`AuditStore.__init__` nimmt nur den Pfad: es gibt keinen Schlüssel und keinen zu maskieren.

**Die drei Hüllen** (`oauth/store.py:1344-1354`):

```python
    async def _read[T](self, work: Work[T]) -> T:
        """A statement without a transaction of its own, in a worker thread."""
        return await asyncio.to_thread(self._call, work, False)

    async def _write[T](self, work: Work[T]) -> T:
        """Statements that are committed together when ``work`` returns, or not at all."""
        return await asyncio.to_thread(self._call, work, True)

    async def _transaction[T](self, work: Work[T]) -> T:
        """``work`` runs its own ``BEGIN IMMEDIATE`` and its own ``COMMIT``."""
        return await asyncio.to_thread(self._call, work, False)
```

Das Anhängen an die Kette (Lesen des letzten Hashes plus `INSERT`) nimmt `_transaction`,
weil es seine eigene Transaktion aufmacht (Falle 5 der Recherche).

**Der Ausführungsrumpf mit `BEGIN IMMEDIATE` und best-effort-Rollback**
(`oauth/store.py:1389-1406`):

```python
        conn = _connect(self._path, schema=not self._schema_ready or not self._path.exists())
        self._schema_ready = True
        try:
            if commit:
                conn.execute("BEGIN IMMEDIATE")
            result = work(conn)
            if commit:
                conn.execute("COMMIT")
            return result
        except BaseException:
            if commit:
                # Suppressed and not handled: the error of ``work`` is the one that
                # matters, and it is on its way up.
                with contextlib.suppress(sqlite3.Error):
                    conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
```

Die Zeile `not self._schema_ready or not self._path.exists()` ist load bearing und wird
mitkopiert: ein entferntes Volume bei laufendem Prozess ergäbe sonst "no such table" bis
zum Neustart (Begründung im Docstring `:1373-1387`).

**Verbindung und Pragmas** (`oauth/store.py:1447-1466`):

```python
def _connect(path: Path, *, schema: bool = True) -> sqlite3.Connection:
    """One connection with the three pragmas, and the schema when the caller asks for it.

    ``isolation_level=None`` turns off the implicit transaction handling of the standard
    library, which is what makes an explicit ``BEGIN IMMEDIATE`` mean what it says.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, timeout=_BUSY_TIMEOUT_SECONDS)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    if schema:
        conn.executescript(SCHEMA)
        _add_missing_columns(conn)
    return conn
```

Zwei Abweichungen, beide gemessen belegt in `18-RESEARCH.md:879-892`:
`PRAGMA auto_vacuum = INCREMENTAL` muss **vor** `executescript(SCHEMA)` stehen (Falle 4),
und `foreign_keys = ON` kann entfallen, wenn das Audit-Schema keine Fremdschlüssel hat.

**Timeout-Konstanten** (`oauth/store.py:1530-1533`):

```python
#: How long the loser of a lock waits for the winner. Long enough for a transaction that
#: writes two rows, short enough that a wedged process answers instead of hanging.
_BUSY_TIMEOUT_MS = 5000
_BUSY_TIMEOUT_SECONDS = _BUSY_TIMEOUT_MS / 1000
```

**Spaltenmigration** (`oauth/store.py:1469-1499`), das Muster für spätere Erweiterungen:

```python
    columns = {row[1] for row in conn.execute("PRAGMA table_info(auth_codes)")}
    if "redirect_uri_explicit" not in columns:
        conn.execute(
            "ALTER TABLE auth_codes ADD COLUMN redirect_uri_explicit INTEGER NOT NULL DEFAULT 1"
        )
```

D-16 nimmt genau diesem Muster die Arbeit ab: die Spalte `actor` steht von Anfang an im
Schema, damit später keine Migration nötig wird.

**Das opportunistische Abräumen** (`oauth/store.py:1546-1551`):

```python
def _purge_expired_rows(conn: sqlite3.Connection, moment: int) -> None:
    """Drop what has run out. Opportunistic, so this project needs no cron (T-03-17)."""
    conn.execute("DELETE FROM flows WHERE expires_at <= ?", (moment,))
    conn.execute("DELETE FROM auth_codes WHERE expires_at <= ?", (moment,))
```

Das ist dasselbe Prinzip wie D-11, nur ohne Bündelungsintervall. Der Audit-Lauf hängt
zusätzlich an `seq % SWEEP_EVERY == 0` und löscht in Stapeln (WAL-Grund,
`18-RESEARCH.md:899-909`).

**Leeren, ohne die Datei zu opfern** (`oauth/store.py:1306-1340`), das Vorbild für die
Formulierung, warum ein `DELETE FROM` hier erlaubt ist:

```python
    async def wipe_all(self) -> None:
        """Empty every table of the schema in one transaction. The file stays (05-06).
        ...
        One statement per table rather than a loop over a tuple of names, and children
        before parents even though the cascades would do it anyway. The explicit order
        keeps working if a foreign key is ever dropped, and the literal ``DELETE FROM``
        keeps these statements inside the narrow, counter proved exemption the destructive
        gate grants this one file (``tests/contract/test_no_destructive_calls.py``).
        """
```

---

### `src/mcp_connector/audit/__init__.py` (config/provider, Fabrik)

**Analog:** `src/mcp_connector/oauth/store.py:1409-1444`.

**Opener als Closure, kein Modulglobal** (`oauth/store.py:1409-1444`):

```python
def store_opener(env: Mapping[str, str] | None = None) -> Callable[[], Awaitable["OAuthStore"]]:
    """One store per application, opened at its first use and swept when it opens.
    ...
    The cache lives in this closure and not in a module global, for the reason D-20 gives:
    a dictionary that outlives a request is one refactor away from being a session store.
    Two applications in one process, which is what every test builds, get one store each
    unless the caller passes the same opener to both.
    """
    opened: dict[str, OAuthStore] = {}
    lock = asyncio.Lock()

    async def open_once() -> OAuthStore:
        ready = opened.get("store")
        if ready is not None:
            return ready
        async with lock:
            ready = opened.get("store")
            if ready is None:
                # The key first: it is the one step that can fail with a named error, and
                # it fails before anything creates a directory.
                key = await crypto.data_key(env)
                ready = OAuthStore(config.persistent_storage(env) / STORE_FILENAME, key)
                await ready.purge_expired()
                opened["store"] = ready
            return ready

    return open_once
```

`audit_opener(env)` kopiert die Form eins zu eins, ohne den Schlüsselschritt. Beachte:
`opened: dict[...]` steht **innerhalb** der Funktion und ist deshalb kein Modulzustand im
Sinne des Gates (siehe Abschnitt "Berührte Gates").

**Typalias für den Provider** (`exapp/purge.py:129-130`):

```python
#: How a caller hands in its own store, the same shape ``oauth/connections.py`` uses.
type StoreProvider = Callable[[], Awaitable[OAuthStore]]
```

---

### `src/mcp_connector/audit/record.py` (service, event-driven)

Kein exaktes Analog: es gibt heute keinen Erfassungspfad. Das Muster setzt sich aus drei
bestehenden Stellen zusammen.

**Wie eine Funktion aus dem Kontext liest, ohne je zu werfen** (`deps.py:230-246`):

```python
def _oauth_identity(ctx: Any) -> OAuthIdentity | None:
    """The identity the transport boundary left for this request, or ``None``.

    Defensive on the way in and never on the way out: a context without a request, a
    request without state and a state without our value are one answer, and that answer is
    a refusal in the caller. The alternative, guessing an identity from anything else in
    the request, is the confused deputy this whole layer exists against (T-01-12).
    """
    try:
        request = getattr(ctx.request_context, "request", None)
    except (AttributeError, ValueError):
        return None
    state = getattr(request, "state", None)
    if state is None:
        return None
    identity = getattr(state, OAUTH_STATE_ATTR, None)
    return identity if isinstance(identity, OAuthIdentity) else None
```

Das ist die Vorlage für `resolve_caller(ctx)` **und** für das Lesen des Rekorders unter
`AUDIT_STATE_ATTR`. Wichtig: `resolve_credentials` selbst darf der Erfassungspfad nicht
nehmen, weil es das Nextcloud-Passwort zurückgibt (`deps.py:222-227`) und bei fehlendem
Kontext `MCPError` wirft (`deps.py:203-212`), was D-13 verbietet.

**Fehlertoleranz mit Typ statt Meldung im Log** (`exapp/purge.py:245-256`):

```python
async def _empty(store: OAuthStore) -> bool:
    """Empty every table, or report that it did not happen. Never raises.

    A failure here does not invalidate the revocations above, and it must not hide them:
    the answer of the handler carries both facts as their own field.
    """
    try:
        await store.wipe_all()
    except Exception as exc:
        logger.error("the tables of this deployment were not emptied: %s", type(exc).__name__)
        return False
    return True
```

Und dieselbe Regel eine Zeile weiter oben, `exapp/purge.py:157-160`:

```python
        except Exception as exc:
            # The type only, never the message: a store error can carry a path.
            logger.error("the purge found no readable store: %s", type(exc).__name__)
```

Das ist D-13 wörtlich: fail-open, eine Zeile ins Nextcloud-Log, nie eine Meldung, die
einen Pfad tragen könnte.

**Klammerung des fremdbestimmten Client-Namens** (`exapp/ui/layout.py:506-522`):

```python
def client_name(raw: str) -> str:
    """Make an attacker supplied client name safe to show, before it is escaped.

    Escaping alone keeps the markup intact but not the page: a name of two hundred
    characters with line breaks in it can imitate a second paragraph of page copy inside
    the card. So control characters go, runs of whitespace collapse into one blank, and
    the result is cut to :data:`CLIENT_NAME_LIMIT` characters.
    """
    printable = "".join(character for character in (raw or "") if character.isprintable())
    collapsed = " ".join(printable.split())
    if not collapsed:
        return strings.CLIENT_NAME_FALLBACK
    if len(collapsed) > CLIENT_NAME_LIMIT:
        return collapsed[: CLIENT_NAME_LIMIT - len(_TRUNCATION_MARK)] + _TRUNCATION_MARK
    return collapsed
```

Diese drei Zeilen werden im Audit-Modul nachgebaut, **nicht importiert**: `exapp/ui` liegt
über `audit/`, und der Import wäre eine Schichtverletzung (Falle 8 der Recherche). Eigene
Längenkonstante, eigener Name.

**Kanonisierung** (`server/__init__.py:63-65`):

```python
def compact(payload: object) -> str:
    """Serialise a tool answer without a single wasted byte (schema diet, D-14)."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
```

Dieselbe Serialisierung, aber im Audit-Modul selbst geschrieben: ein Import von `server`
in `audit` wäre ein Ringschluss, weil `server` den Rekorder aufruft
(`18-RESEARCH.md:530-533`).

---

### `src/mcp_connector/audit/allowlist.py` (config, konstante Daten)

**Analog:** `src/mcp_connector/exapp/config_values.py:103-135` für die Form der benannten
Aufzählung, `tests/contract/test_tool_surface.py:79-83` für die Sperrliste.

**Benannte Aufzählung mit Begründung, warum die Reihenfolge so ist**
(`exapp/config_values.py:103-117`):

```python
#: The six keys, in the order the form declares its fields. They are the field ids of the
#: admin form and the configuration keys at the same time (see the module docstring).
CONFIG_KEYS: tuple[str, ...] = (
    PUBLIC_URL_KEY,
    "oauth_dcr",
    ...
)
```

**Sperrliste** (`tests/contract/test_tool_surface.py:79-83`):

```python
# A parameter that names a user turns this server into a confused deputy: the credentials
# come from the auth channel, so a tool that also accepts a user name would let the model
# ask for someone else's data (T-01-95).
FORBIDDEN_PROPERTIES = {"user", "username", "uid", "userid", "owner"}
```

**Namenszwang aus dem Gate:** Die Erlaubnisliste muss `PARAM_ALLOWLIST` heissen, in
Grossbuchstaben. `tests/contract/test_no_destructive_calls.py:635` nimmt genau
`target.id.isupper()` als Ausnahme vom Verbot des Modulzustands; ein
`_param_allowlist: dict[...]` auf Modulebene macht dieses Gate rot.

---

### `src/mcp_connector/exapp/<prüfkommando>.py` (route/handler, request-response)

**Analog:** `src/mcp_connector/exapp/purge.py`, ganze Datei, ausdrücklich als Vorbild
benannt in `18-CONTEXT.md` (Claude's Discretion, dritter Punkt).

**Pfadkonstante mit dem Grund für ihre Abwesenheit im Manifest** (`purge.py:57-66`):

```python
#: The path of the one route of this module, and the name the occ command registration
#: hands to AppAPI as its ``execute_handler`` (``exapp/occ.py`` derives that from this
#: constant, so the two cannot drift apart). It appears in no ``<route>`` of the manifest,
#: on purpose; see the module docstring.
PURGE_PATH = "/purge"
```

**Fabrik statt Registrierung am Serverobjekt** (`purge.py:133-144, 212`):

```python
def purge_routes(
    env: Mapping[str, str] | None = None, *, store_provider: StoreProvider
) -> list[Route]:
    """The one route of the purge, handed out rather than registered on the server object.

    A factory for the reason D-23 gives and ``exapp/lifecycle.py`` states: a registration on
    the shared MCP server object would make this path appear in the standalone HTTP mode of
    phase 1 as soon as anything imports this module, and that mode has no AppAPI identity to
    check it against.
    """

    async def purge(request: Request) -> Response:
        ...

    return [Route(PURGE_PATH, purge, methods=["POST"])]
```

**Die Doppelprüfung, Pflicht laut Sicherheitsdomäne V4** (`purge.py:259-272`):

```python
def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    """Return the Nextcloud user id of this request, or the response that ends it.

    Verbatim the guard of ``exapp/lifecycle.py``, including the reason for both halves: a
    response instead of an exception so no rejection escapes as a 500, and no detail in the
    rejection so nothing tells a caller which of the checks refused it (T-02-03).
    """
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        return json_response({}, status_code=401)
```

Dazu die Konstante und ihre Begründung, warum sie zweimal geschrieben ist
(`purge.py:78-82`):

```python
#: Set on the proxy path, never by HaRP and never on the internal AppAPI path. The same
#: header ``exapp/lifecycle.py`` refuses, spelled a second time rather than imported: that
#: module imports ``exapp/occ.py``, which imports this one, so an import back would close a
#: cycle. A test holds the two spellings equal.
HEADER_ORIGIN_IP = "x-origin-ip"
```

**Textantwort statt JSON** (`purge.py:411-412`), und genau die Form, die das Prüfkommando
nach `18-RESEARCH.md:736-745` braucht (immer 200, Urteil im Rumpf):

```python
def _text(body: str, status_code: int) -> Response:
    return Response(body, status_code=status_code, media_type="text/plain", headers=NO_STORE)
```

**Optionen aus dem occ-Umschlag lesen, falls das Kommando welche bekommt**
(`purge.py:296-317`) samt der Messung, die die Form belegt (`purge.py:68-76`):

```python
#: The envelope AppAPI wraps an occ invocation in ...
#: So the body of a real invocation is ``{"occ": {"arguments": null, "options": {"force":
#: true}}}`` and the flag is one level below the top.
OCC_ENVELOPE = "occ"
```

**Begrenztes Lesen des Rumpfs** (`purge.py:390-408`), unverändert zu übernehmen, wenn das
Prüfkommando Optionen hat:

```python
    announced = request.headers.get("content-length", "")
    if announced.isdigit() and int(announced) > MAX_BODY_BYTES:
        logger.warning("a purge call announced a body this handler does not read")
        return None
    try:
        raw = await bounded_body(request, MAX_BODY_BYTES)
    except BodyTooLarge:
        ...
```

**Modul-Docstring als Ort der Begründungen** (`purge.py:1-38`): drei Überschriften
("Why there is no route in the manifest", "Why the order is not negotiable", "Why nothing
is cleaned up on the ``enabled=0`` hook"). Die Grenzbeschreibung aus D-v1.5-02
(`18-RESEARCH.md:589-597`) und die `--rm-data`-Formulierung (`:1142-1148`) gehören in
genau dieses Format.

---

### `tests/unit/test_audit_store.py` (test, CRUD gegen echte Datei)

**Analog:** `tests/unit/test_oauth_store.py`.

**Docstring, der sagt, warum eine echte Datei und kein Mock** (`test_oauth_store.py:1-10`):

```python
"""The persistence of the phase: every row that survives a restart, and what it costs.

Threats covered here: T-03-10 (the store file leaves the volume), T-03-11 (a plaintext
token in the database), T-03-13 (two winners of one refresh rotation) and T-03-17 (tables
that grow without a bound).

Every check runs against a real SQLite file in ``tmp_path``, because the guarantees under
test are the guarantees of the file: atomicity across threads, and content that is useless
to whoever steals it.
"""
```

**Die Öffnungshilfe** (`test_oauth_store.py:43-44`):

```python
def open_store(tmp_path: Path, key: bytes = KEY) -> store.OAuthStore:
    return store.OAuthStore(tmp_path / store.STORE_FILENAME, key)
```

**Der Manipulationstest** (Erfolgskriterium 3, `18-CONTEXT.md` Specific Ideas) hat sein
Vorbild im Zählen an der Ablage vorbei, `tests/unit/test_exapp_purge.py:143-153`:

```python
    def counts(self) -> dict[str, int]:
        """The row count of every table, read out of the file behind the store's back."""
        conn = sqlite3.connect(self.path)
        try:
            found: dict[str, int] = {}
            for table in TABLES:
                statement = "SELECT COUNT(*) FROM " + table  # noqa: S608 - a literal name
                found[table] = conn.execute(statement).fetchone()[0]
            return found
        finally:
            conn.close()
```

Derselbe Zugriff, nur mit `UPDATE` statt `SELECT`, ist der Angreifer aus
`18-RESEARCH.md:1200-1213`. Die drei Fälle (verändert, gelöscht, echter Grabstein) gehören
zusammen in diese Datei.

Asynchrone Tests laufen über `@pytest.mark.anyio` mit der `anyio_backend`-Fixture aus
`tests/conftest.py:13-16`; `pytest-asyncio` ist keine Abhängigkeit dieses Projekts.

---

### `tests/unit/test_audit_record.py` (test, event-driven)

**Analog:** `tests/unit/test_oauth_credentials.py:96-136`. Das ist der einzige Ort im
Repository, der einen Werkzeugkontext fälscht, und er ist genau der, den der Rekorder
liest.

```python
class FakeRequestContext:
    """What the SDK hands a tool: the request of the message, and nothing else of ours."""

    def __init__(self, request: Request) -> None:
        self.request = request


class FakeContext:
    """The context object of a tool call, in the two shapes ``deps`` reads it in."""

    def __init__(
        self,
        headers: Mapping[str, str] | None = None,
        identity: OAuthIdentity | None = None,
    ) -> None:
        self.headers = headers
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/mcp",
                "query_string": b"",
                "headers": [
                    (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
                ],
            }
        )
        if identity is not None:
            setattr(request.state, OAUTH_STATE_ATTR, identity)
        self.request_context = FakeRequestContext(request)
```

Zu erweitern um ein `params`-Feld an `FakeRequestContext`, weil der Rekorder
`ctx.request_context.params["arguments"].keys()` liest (`18-RESEARCH.md:238-256`), und um
ein zweites `setattr` für `AUDIT_STATE_ATTR`.

**Der Doppelgänger, der immer wirft** (fail-open-Test, D-13), hat sein Vorbild in der
Spionage-Fixture `tests/unit/test_exapp_purge.py:164-184`:

```python
@pytest.fixture
def destructive(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """A spy on the two destructive steps, so "it did not run" is an assertion.
    ...
    """
    seen: list[str] = []

    async def empty(store: OAuthStore) -> bool:
        seen.append("empty")
        return True

    monkeypatch.setattr(purge, "_empty", empty)
```

---

### `tests/unit/test_exapp_<prüfkommando>.py` (test, request-response)

**Analog:** `tests/unit/test_exapp_purge.py`.

**Die Deployment-Hülle** (`:107-118`):

```python
class Deployment:
    """One process of this application with its own store file and the purge route on it."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "oauth.sqlite3"
        self.store = OAuthStore(self.path, KEY)
        self.client = TestClient(
            Starlette(routes=purge.purge_routes(ENV, store_provider=self._open))
        )

    async def _open(self) -> OAuthStore:
        return self.store
```

**Die AppAPI-Kopfzeilen** (`:97-104`):

```python
def appapi_headers(user: str = "", secret: str = APP_SECRET) -> dict[str, str]:
    """What AppAPI puts on an internal call. The user is empty: this is the app context."""
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token,
    }
```

**Der Aufruf, wie AppAPI ihn liefert** (`:187-202`):

```python
def call(
    deployment: Deployment,
    *,
    force: bool = True,
    body: object | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """One occ invocation, as AppAPI delivers it: a POST with the options in the body.

    ``Any`` for the reason ``tests/unit/test_oauth_abuse.py`` gives: the test client of
    Starlette answers with the response type of ``httpx2``, the fork the MCP SDK brings, and
    the outgoing calls of this app use ``httpx``. Naming either type here is a false claim.
    """
```

**Der Threat-Katalog im Docstring** (`:1-27`) ist das Format, in dem die Kriterien dieser
Phase aufgelistet werden.

Der Fall "der Pfad steht in keiner `<url>` des Manifests" ist in dieser Datei schon
vorhanden (`MANIFEST` auf `:94`, geprüft mit `lxml.etree` und `hardened_parser`), und der
neue Pfad braucht denselben Fall (`18-RESEARCH.md:715-717`).

---

### `tests/contract/test_audit_surface.py` (test, Gate)

**Analog:** `scripts/check_tool_budget.py` für die Messung über alle Werkzeuge,
`tests/contract/test_tool_surface.py:709-726` für die Gate-Form innerhalb von pytest.

**Eine Messung über alle, keine Stichprobe** (`check_tool_budget.py:120-142`):

```python
async def main() -> int:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()

    payload = result.model_dump(by_alias=True, exclude_none=True, mode="json")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    size = len(blob.encode("utf-8"))
    per_tool = sorted(
        (
            (
                len(json.dumps(tool, separators=(",", ":"), ensure_ascii=False).encode("utf-8")),
                tool["name"],
            )
            for tool in payload["tools"]
        ),
        reverse=True,
    )
```

**Der Fehlschlag benennt jeden Treffer, nicht nur die Tatsache**
(`check_tool_budget.py:148-156`):

```python
    too_big = [(name, tool_size) for tool_size, name in per_tool if tool_size > MAX_TOOL_BYTES]
    if too_big:
        for name, tool_size in too_big:
            print(
                f"FAIL: {name} is {tool_size} bytes, above the per tool ceiling "
                f"of {MAX_TOOL_BYTES}",
                file=sys.stderr,
            )
        return 1
```

**Dieselbe Behauptung als pytest-Gate mit gesammelten Befunden**
(`test_tool_surface.py:709-726`):

```python
@pytest.mark.anyio
async def test_no_input_schema_accepts_a_user_parameter() -> None:
    """T-01-95: the caller is the auth channel, never a tool argument."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == EXPECTED_TOOLS, "the confused deputy check must cover all 21 schemas"

    findings: list[str] = []
    for name, tool in sorted(tools.items()):
        schema = tool.input_schema or {}
        for property_name, _definition in _properties(schema):
            if property_name.lower() in FORBIDDEN_PROPERTIES:
                findings.append(f"{name}.{property_name}")

    assert findings == [], (
        "a tool that takes a user name lets the model act as someone else: " + ", ".join(findings)
    )
```

Genau diese Form für die drei Behauptungen aus `18-RESEARCH.md:419-433`:
Vollständigkeit, keine Erfindungen, keine Verräter.

**Der Dekorator-Nachweis** braucht `.fn` und damit `mcp._tool_manager.list_tools()` statt
des `Client`. Das ist erlaubt: `tests/contract/test_module_boundaries.py` läuft nur über
`src/mcp_connector` (`:34-37`, `SRC = ... / "src" / "mcp_connector"`) und sieht `tests/`
gar nicht.

**Achtung Gegenprobe:** `test_tool_surface.py:508-515` vergleicht die Werkzeugmenge gegen
ein eingefrorenes Literal und `len(tools) == 21`. Ein Testwerkzeug, das am Modulsingleton
`mcp` hängen bleibt, macht diese Datei rot (Falle 9). Der Gegenbeweis wird ohne
Registrierung geführt.

---

### `tests/integration/test_appapi_users_list.py` (test, request-response, Marker `integration`)

**Analog:** `tests/integration/test_exapp_dav_matrix.py`.

**Marker und Laufanweisung im Docstring** (`:31-38`, `:58`):

```python
Run it against the running HaRP topology::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_exapp_dav_matrix.py -m integration -q
"""
...
pytestmark = [pytest.mark.integration, pytest.mark.anyio]
```

**Die Fixture, die sich ohne `.env.exapp` selbst überspringt** (`tests/conftest.py:40-65`):

```python
def exapp_env() -> dict[str, str]:
    """The AppAPI deploy identity that ``scripts/bootstrap_exapp.sh`` writes into ``.env.exapp``.
    ...
    When one of the required values is missing the caller skips with the variable named, the
    same shape ``test_permission_fidelity.py`` uses.
    """
    required = {
        "base_url": "NC_MCP_URL",
        "app_id": "APP_ID",
        "app_secret": "APP_SECRET",
        ...
    }
```

Dieser Test misst A1 aus dem Annahmenverzeichnis (`18-RESEARCH.md:1535`), die einzige
Annahme mit hohem Risiko: gibt `GET /ocs/v2.php/apps/app_api/api/v1/users` wirklich jedes
Konto zurück.

---

## Geänderte Dateien: was genau dazukommt

### `src/mcp_connector/server/__init__.py`

Der heutige Dekorator, unverändert zitiert (`:82-99`):

```python
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
        except httpx.TimeoutException:
            raise ValueError(
                "Nextcloud did not respond in time. Hint: retry with a smaller range or a "
                "narrower scope."
            ) from None
        except httpx.RequestError:
            raise ValueError(
                "Could not reach Nextcloud. Hint: check the configured Nextcloud URL and "
                "that the server is online."
            ) from None

    return wrapper
```

Dazu: `wrapper.__mcp_audited__ = True` vor dem `return`, ein `finally`-Zweig, und je einer
der drei bestehenden `except`-Zweige setzt `outcome`/`reason`. Die Zielform steht in
`18-RESEARCH.md:1412-1434`. Der Docstring des Dekorators (`:69-80`) bleibt und bekommt den
Erfassungsabsatz dazu; `from None` ist load bearing und wird nicht angefasst.

### `src/mcp_connector/exapp/middleware.py`

Die Naht, an der der Rekorder hinterlegt wird (`:229-235`):

```python
        if not isinstance(self._token_verifier, IdentitySource):
            return True
        identity = await self._token_verifier.resolve_identity(access)
        if identity is None:
            return False
        setattr(request.state, OAUTH_STATE_ATTR, identity)
        return True
```

Die Namenskonstante liegt bei ihrem Leser (`oauth/verifier.py:88-90`):

```python
#: The name the transport boundary deposits the resolved identity under, and the name
#: ``deps.py`` reads. One constant, so the two sides cannot drift apart.
OAUTH_STATE_ATTR = "oauth_identity"
```

`AUDIT_STATE_ATTR` gehört nach demselben Muster in `audit/__init__.py`, dorthin, wo der
Leser sitzt.

### `src/mcp_connector/oauth/verifier.py`

Das Feld, dem `client_name` folgt (`:82-86`):

```python
#: Where the id of the authorization travels inside the SDK token model. The model has no
#: field for it, and ``claims`` is what it offers for exactly this (RFC 7662 style claims).
#: The value is an internal id, never a secret: it is the flow id of a consent that already
#: happened, and by itself it grants nothing.
AUTH_ID_CLAIM = "auth_id"
```

Und die Datenklasse, die ein Feld dazubekommt (`:101-125`), samt maskiertem `__repr__`, in
dem der neue Name mitgeführt wird:

```python
@dataclass(frozen=True, slots=True, repr=False)
class OAuthIdentity:
    nc_user: str
    app_password: str
    auth_id: str
    client_id: str
    revoked: bool = False

    def __repr__(self) -> str:
        return (
            f"OAuthIdentity(nc_user={self.nc_user!r}, auth_id={self.auth_id!r}, "
            f"client_id={self.client_id!r}, revoked={self.revoked!r}, app_password='***')"
        )
```

### `src/mcp_connector/exapp/config_values.py` und `admin_settings.py` (Schalter, D-14)

Drei Einträge, an drei Stellen, in dieser Reihenfolge
(`config_values.py:110-117`, `:121-128`, `:133-135`):

```python
CONFIG_KEYS: tuple[str, ...] = (
    PUBLIC_URL_KEY,
    "oauth_dcr",
    ...
    "talk_send",
)

KEY_TO_ENV: Mapping[str, str] = {
    PUBLIC_URL_KEY: config.ENV_PUBLIC_URL,
    ...
    "talk_send": config.ENV_TALK_SEND,
}

SWITCH_KEYS: frozenset[str] = frozenset(
    {"oauth_dcr", "oauth_cimd", "oauth_allowlist_only", "talk_send"}
)
```

Das Formularfeld mit dem ab Werk ausgeschalteten Zustand
(`admin_settings.py:147-153`), das genaue Vorbild für den Audit-Schalter:

```python
            {
                "id": allowlist_field,
                "title": strings.ADMIN_FIELD_ALLOWLIST_LABEL,
                "description": strings.ADMIN_FIELD_ALLOWLIST_DESCRIPTION,
                "type": "checkbox",
                "default": False,
            },
```

Der Kommentar über `"default"` ist Pflicht: jedes andere Feld begründet seinen
Auslieferungszustand (`:131-133`, `:140-146`, `:166-171`).

Der Leser im Code, in der Richtung "ab Werk aus" also mit positiver Liste
(`oauth/registry.py:284-308`, nicht `config.talk_send_enabled`, das die
Gegenrichtung fährt und dies ausdrücklich sagt, `config.py:336-345`):

```python
def _switch(env: Mapping[str, str] | None, name: str, *, default: bool) -> bool:
    """One switch, with a blank value counting as unset and a typo counting as nothing.

    A value this function does not know keeps the default and says so in the log.
    """
    source = {} if env is None else env
    value = (source.get(name) or "").strip().lower()
    if not value:
        return default
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    logger.warning(...)
    return default
```

Und die Umgebungsvariable nach dem Namensmuster von `config.py:47`
(`ENV_TALK_SEND = "NC_MCP_TALK_SEND"`).

### `src/mcp_connector/exapp/occ.py` und `lifecycle.py` (zweites Kommando)

`command_scheme()` (`occ.py:72-92`) wird zu `command_schemes() -> list[dict[str, Any]]`,
weil `OccCommandController::registerCommand` genau ein Kommando je `POST` nimmt
(`18-RESEARCH.md:701-703`). Der Docstring erklärt heute schon, warum es eine Funktion und
keine Modulkonstante ist:

```python
def command_scheme() -> dict[str, Any]:
    """The one command this app registers.

    A function rather than a module level constant so the shape has one place a test reads
    and the registration cannot be asserted against a copy of itself.
    """
```

Die Registrierungsschleife bekommt einen `try` je Kommando, nach genau dem Vorbild der
drei unabhängigen Registrierungen (`lifecycle.py:93-110`):

```python
            try:
                await admin_settings.register_admin_form(env=env)
            except Exception:
                # Its own try block, and not a second statement in the one above: the two
                # forms are independent, so a failure of one may not cost the other.
                logger.error("the admin form registration failed, the admin settings are missing")
            try:
                await occ.register_occ_commands(env=env)
            except Exception:
                logger.error("the occ command registration failed, the purge command is missing")
```

Der App-Kontext des ausgehenden Aufrufs bleibt wie er ist (`occ.py:109-119`): leere
Nutzer-Id, OCS-Kopfzeilen plus `appapi_auth_headers`.

Die Ableitung des Handlers aus der Route (`occ.py:55-57`) wird für den zweiten Pfad
wiederholt:

```python
#: The route on us AppAPI calls when the command runs, without the leading slash: one
#: derivation from the route itself, so the two cannot say different things.
OCC_HANDLER = PURGE_PATH.removeprefix("/")
```

### `src/mcp_connector/entry_exapp.py`

Der Opener wird gebaut, wo der OAuth-Opener gebaut wird (`:90-93`):

```python
    policy = client_policy(env)
    store = store_opener(env)
    provider = NextcloudOAuthProvider(env=env, policy=policy, store_provider=store)
```

Und die Route wird in derselben Aufzählung angehängt (`:168-182`):

```python
    for route in (
        *lifecycle_routes(env),
        *metadata_routes(env, dcr_enabled=policy.dcr_enabled, cimd_enabled=policy.cimd_enabled),
        *connect_routes(env, store_provider=store, throttle=counters),
        ...
        *purge_routes(env, store_provider=store),
    ):
        app.router.routes.append(route)
    return app
```

Der lange Kommentarblock darüber (`:129-167`) nennt für jede Route den Grund, warum sie
hier und nicht am Serverobjekt hängt. Der fünfte Absatz gehört dazugeschrieben.

### `src/mcp_connector/errors.py`

Die Klasse, die ein Schlüsselwortargument bekommt (`:9-15`):

```python
class ToolError(Exception):
    """A failure a caller can act on: what went wrong plus what to do about it."""

    def __init__(self, message: str, hint: str) -> None:
        super().__init__(f"{message} Hint: {hint}")
        self.message = message
        self.hint = hint
```

`reason: str = REASON_UNSPECIFIED` als reines Schlüsselwortargument mit Vorgabewert, damit
die rund 223 unberührten Wurfstellen unverändert bleiben (D-17).

### `src/mcp_connector/nextcloud/clients/ocs.py` und die drei DAV-Geschwister

Die eine Stelle, die die halbe Oberfläche abdeckt (`ocs.py:266-291`):

```python
def _status_error(status: int, detail: str, what: str) -> ToolError:
    """One place that turns a Nextcloud status into a sentence the model can act on."""
    suffix = f" Nextcloud says: {detail}" if detail else ""
    ...
    if status == 403:
        return ToolError(
            message=f"No permission for {what}.{suffix}",
            hint="Ask the owner in Nextcloud for the missing permission.",
        )
    if status in (404, 998):
        return ToolError(
            message=f"Nextcloud did not find {what}.{suffix}",
            hint="Search for it first; the id or the name is unknown to this instance.",
        )
```

Hier kommt `reason=REASON_PERMISSION_DENIED` beziehungsweise `reason=REASON_UNKNOWN_ID`
dazu, und nur hier. Die Gegenstücke stehen in `dav.py:505-556` und `:567-601`,
`caldav.py:445-479` und `:488-523`, `carddav.py:375-404` (Fundstellen aus
`18-RESEARCH.md:649-655`, in dieser Kartierung nicht einzeln nachgelesen).

**Was nie ins Log darf:** `exc.message` und `exc.hint`. Die Zeile
`f"No permission for {what}"` zeigt, warum: `what` ist ein Pfad oder ein Kalendername.

---

## Gemeinsame Muster

### SQLite-Klempnerei
**Quelle:** `src/mcp_connector/oauth/store.py:1344-1466`
**Gilt für:** `audit/store.py`
Drei Hüllen über `asyncio.to_thread`, eine frische Verbindung je Aufruf,
`isolation_level=None`, `BEGIN IMMEDIATE` am Anfang, best-effort-`ROLLBACK`,
`conn.close()` im `finally`, Schema-Flag am Objekt plus `path.exists()`.

### Fehlermodell "nie werfen, eine Zeile ins Log, nur der Typ"
**Quelle:** `src/mcp_connector/exapp/purge.py:157-159, 245-256`;
`src/mcp_connector/exapp/occ.py:95-131`; `src/mcp_connector/exapp/config_values.py:190-199`
**Gilt für:** `audit/record.py`, das Prüfkommando, die zweite occ-Registrierung
Ein Versuch, kein Wiederholen, eine Logzeile, nie ein Wert aus dem Vorgang, nie eine
Ausnahme nach oben. Begründung im Projekt: Fallstrick 11 (ein nicht leeres `error`-Feld
schaltet die App sofort wieder ab) und D-13.

### Kein Wert im Log
**Quelle:** `src/mcp_connector/exapp/purge.py:359-369`;
`src/mcp_connector/exapp/config_values.py:416-423`
**Gilt für:** jede neue Logzeile dieser Phase

```python
def _rejected(key: str, why: str) -> None:
    """Name the field and the reason, never the value: it came in over HTTP (T-05-03)."""
```

### Identität aus `request.state`, defensiv gelesen
**Quelle:** `src/mcp_connector/deps.py:230-246`; `src/mcp_connector/exapp/middleware.py:234`
**Gilt für:** `deps.resolve_caller`, `audit/record.py`

### Doppelprüfung vor jedem occ-Handler
**Quelle:** `src/mcp_connector/exapp/purge.py:259-272`
**Gilt für:** das Prüfkommando. Pflicht, nicht Kür (Sicherheitsdomäne V4).

### Keine neue Route im Manifest, nur der Kommentar
**Quelle:** `appinfo/info.xml:260-285`
**Gilt für:** den Pfad des Prüfkommandos

```xml
		<!--
		  - Exactly thirteen routes, and they are the whole external attack surface of this app.
		  ...
		  - The fourth deliberately absent path is /purge, added in plan 05-06, and for it
		  - this is not defense in depth but the control itself.
		  ...
		  - path appears in no <url> below.
```

Der Satz "Exactly thirteen routes" bleibt wahr: es kommt keine `<url>` dazu, nur ein
fünfter Absatz über einen fünften abwesenden Pfad.

### Konfigurationswert mit Vorgabe im Code
**Quelle:** `src/mcp_connector/exapp/config_values.py:103-135, 396-413`;
`src/mcp_connector/exapp/admin_settings.py:147-153`; `src/mcp_connector/config.py:47, 329-348`
**Gilt für:** den Schalter aus D-14
Die Kette ist Admin-Wert, dann `NC_MCP_*`, dann Vorgabe im Code. Ein 401 beim ersten Start
ergibt `{}` und damit die Vorgabe, und die ist "aus": die fail-closed-Richtung
(`config_values.py:215-239`).

### Verzeichnis der Ablage
**Quelle:** `src/mcp_connector/config.py:240-283`
**Gilt für:** `audit/__init__.py`
`config.persistent_storage(env)` wirft im ExApp-Betrieb, wenn das Volume fehlt, und wird
von `entry_exapp.main` schon beim Start gerufen. Die Audit-Datei liegt daneben, nicht
darunter (D-01, D-18).

---

## Berührte Gates

### 1. `FILES_WITH_OWN_SQL` in `tests/contract/test_no_destructive_calls.py`

Heute (`:229-236`):

```python
# The one file where the word DELETE is not an HTTP verb. TOOL-09 is a promise about what
# this server does to data in Nextcloud, and the OAuth store is our own SQLite file: it
# has to drop an expired authorization code and a registration nobody ever used, or it
# grows without a bound (T-03-17). The exemption is deliberately narrow, two exact SQL
# forms in one file, so an HTTP DELETE written in the same module is still reported, and
# ``.delete(`` above is never exempt anywhere.
FILES_WITH_OWN_SQL = frozenset({"oauth/store.py"})
SQL_DELETE_FORMS = ("DELETE FROM ", "ON DELETE CASCADE")
```

Die Prüfung selbst (`:356-358`):

```python
def _is_own_sql(relative: str, text: str) -> bool:
    """True for a statement against our own store file, false for anything else."""
    return relative in FILES_WITH_OWN_SQL and any(form in text for form in SQL_DELETE_FORMS)
```

`audit/store.py` braucht `DELETE FROM` für Frist, Obergrenze und Nutzerbereinigung und
gehört deshalb in diese Menge, mit einer **eigenen Begründungszeile** nach dem Muster der
drei bestehenden Ausnahmen (`:229-234`, `:238-245`, `:251-260`). Der Gegenbeweis-Test
(`:397-409`) trägt den zweiten Eintrag ohne Änderung, weil er über die Menge schleift:

```python
    for relative in FILES_WITH_OWN_SQL | FILES_WITH_OWN_APP_PASSWORD | FILES_WITH_OWN_CONFIG:
        assert (SRC / relative).is_file(), f"{relative} is exempt but does not exist"
```

### 2. Die Grossschreibungsregel für Modulzustand, dieselbe Datei

Der Gate (`:615-643`), die entscheidende Zeile ist `:635`:

```python
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if (relative, target.id) in ALLOWED_MODULE_STATE:
                    continue
                if target.id.isupper():  # module constants are configuration, not state
                    continue
                if target.id.startswith("__") and target.id.endswith("__"):
                    continue  # __all__ is the export list of a module, not runtime state
                findings.append(f"{relative}:{node.lineno}: module level mutable {target.id}")
```

Erkannt werden `ast.Dict`, `ast.List`, `ast.Set`, die drei Comprehensions und die Aufrufe
aus `_MUTABLE_FACTORIES` (`:277-284`: `dict`, `list`, `set`, `defaultdict`,
`WeakKeyDictionary`, `WeakValueDictionary`).

**Zwei Folgen für diese Phase:**
- `PARAM_ALLOWLIST` muss in Grossbuchstaben stehen. `_param_allowlist` oder
  `param_allowlist` auf Modulebene ist ein Fehlschlag.
- Die Ausnahmenliste bleibt bei zwei Einträgen (`:272-275`, geprüft in `:656-661`):

```python
    assert len(ALLOWED_MODULE_STATE) == 2, (
        "the exceptions are counted, not only described: a third cache is a decision, and a "
        "decision has to be made in a review and not in a diff (D-20, T-08-23)"
    )
```

Das Audit-Modul darf also keinen dritten Cache anmelden. Der Opener löst das, indem sein
`opened`-Wörterbuch in einer Closure liegt und nicht auf Modulebene
(`oauth/store.py:1421-1426`).

### 3. `tests/contract/test_tool_surface.py` bleibt unberührt

Diese Phase fügt kein Werkzeug hinzu. Das eingefrorene Literal (`:40-62`) und
`len(tools) == 21` (`:515`) bleiben, solange kein Test dauerhaft etwas an `mcp` registriert.
Der Byte-Gate-Nachweis läuft über `scripts/check_tool_budget.py` vor und nach der Änderung;
erwartet 15712 vor und 15712 nach (`18-RESEARCH.md:1056-1084`), Grenzwert `BUDGET_BYTES =
18_000` (`check_tool_budget.py:83`) wird nicht angefasst.

### 4. `tests/unit/test_project_layout.py`

Kein neues Paket, keine neue Abhängigkeit (`:22-46`). Diese Phase kommt mit `sqlite3`,
`hashlib`, `json`, `time` und `asyncio` aus.

---

## Kein Analog

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `src/mcp_connector/audit/record.py` (nur die Kettenlogik im Dekorator) | service | event-driven | Es gibt heute keinen Erfassungspfad und keinen Test für `graceful` (geprüft: `graceful` kommt in `tests/` nur in einem Docstring von `test_ocs_capabilities.py:1` vor). Rahmen, Kontextlesen, Fehlermodell und Klammerung haben je ein Analog (oben zugewiesen); die Verkettung der Teile ist neu und folgt `18-RESEARCH.md:1412-1434`. |

Alles andere hat ein Analog im Repository.

---

## Metadaten

**Suchbereich:** `src/mcp_connector/` (alle Unterpakete), `tests/unit/`,
`tests/contract/`, `tests/integration/`, `scripts/`, `appinfo/`
**Gelesene Analog-Dateien:** 24 (davon 4 gezielt in Ausschnitten, weil sie über 400 Zeilen
haben: `oauth/store.py`, `tests/contract/test_tool_surface.py`,
`tests/contract/test_no_destructive_calls.py`, `tests/unit/test_exapp_purge.py`)
**Projektvorgaben gelesen:** `CLAUDE.md` im Repository-Wurzelverzeichnis vorhanden;
`.claude/skills/` und `.agents/skills/` existieren nicht
**Kartierungsdatum:** 2026-08-29
