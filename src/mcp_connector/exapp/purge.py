"""The handler behind ``occ mcp_connector:purge``: end every connection of this instance.

Success criterion 2 of this phase says an uninstall removes all data, tokens included. The
measurement says the opposite happens on its own: the Remove button of Nextcloud 34 calls
``disableExApp()`` for an ExApp, so the container stops and nothing else does. The volume
with the encrypted app passwords stays, ``ExAppService::unregisterExApp()`` does not delete
the ExApp configuration this app keeps its data key in, and the Nextcloud app passwords in
``oc_authtoken`` are touched by no AppAPI path at all. Measured on this machine two days
after the last run: 85 clients, 84 authorizations, 83 refresh tokens, all still there, and
84 app passwords still valid. Without this module the criterion is not reachable.

Three decisions, each with its source, because each of them is one somebody will want to
undo.

**Why there is no route in the manifest.** The occ command reaches this handler over
AppAPI's ``PublicFunctions``, the same internal path ``/heartbeat``, ``/init`` and
``/enabled`` arrive on, so it needs no declaration to work. Declaring one would publish an
instance wide deletion to the internet, because the PHP proxy attaches valid AppAPI headers
itself and protects none of these paths (T-02-20, pitfall 13 of 05-RESEARCH.md). The big
comment in ``appinfo/info.xml`` names this path as the fourth deliberately absent one, and
:func:`purge_routes` therefore runs the same double check ``exapp/lifecycle.py`` runs:
``x-origin-ip`` means the PHP proxy and is answered with 404, then ``require_appapi``.

**Why the order is not negotiable.** The data key lives in Nextcloud's ExApp configuration,
the encrypted app passwords live in the volume, and one is useless without the other.
Revoking a Nextcloud app password means authenticating with that very password, so it has
to be decrypted first. Whoever deletes the key first, or empties the tables first, has
destroyed the only knowledge of which credential belongs to which connection, and every one
of them stays valid in Nextcloud with no record left that it exists (pattern 4 of
05-RESEARCH.md). Hand back, then empty, then delete the key.

**Why nothing is cleaned up on the ``enabled=0`` hook.** That hook looks like the natural
place, because the Remove button fires exactly it. It also fires on every update
(``lib/Command/ExApp/Update.php``) and on every ordinary disable, so cleaning up there
would delete every connection of every user whenever an administrator updates the app. The
disable branch of ``exapp/lifecycle.py`` stays empty, and a test in
``tests/unit/test_exapp_purge.py`` keeps it that way (T-05-28).
"""

import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..errors import ToolError
from ..oauth import crypto, loginflow
from ..oauth.store import AuthorizationRow, OAuthStore
from .auth import AppApiRejected, require_appapi
from .responses import NO_STORE, json_response

__all__ = ["FORCE_OPTION", "PURGE_PATH", "purge_routes"]

#: The path of the one route of this module, and the name the occ command registration
#: hands to AppAPI as its ``execute_handler`` (``exapp/occ.py`` derives that from this
#: constant, so the two cannot drift apart). It appears in no ``<route>`` of the manifest,
#: on purpose; see the module docstring.
PURGE_PATH = "/purge"

#: The one option of the command. Declared on the AppAPI side in ``exapp/occ.py`` and
#: checked here as well, because what AppAPI hands over is input: an instance wide deletion
#: does not run because a declaration somewhere else says a flag is required.
FORCE_OPTION = "force"

#: Set on the proxy path, never by HaRP and never on the internal AppAPI path. The same
#: header ``exapp/lifecycle.py`` refuses, spelled a second time rather than imported: that
#: module imports ``exapp/occ.py``, which imports this one, so an import back would close a
#: cycle. A test holds the two spellings equal.
HEADER_ORIGIN_IP = "x-origin-ip"

#: The largest body this handler reads before deciding it is not an occ invocation. The
#: real one is a handful of option names; anything above this is not AppAPI and is not
#: parsed (the rule of ``oauth/connections.py``, MAX_FORM_BYTES).
MAX_BODY_BYTES = 4096

#: The words that mean "no" when a flag arrives with a value. Everything else, including a
#: flag that arrives with no value at all, counts as set: a Symfony option in mode ``none``
#: is presence and nothing more.
FALSE_WORDS = frozenset({"0", "false", "no", "off", "none", "nein"})

FORCE_HINT = (
    "Nothing was changed. This command ends every MCP connection of this instance and "
    f"cannot be undone, so it only runs with --{FORCE_OPTION}."
)

STORE_HINT = (
    "Nothing was changed: the data of this app could not be opened, so no credential "
    "could be handed back to Nextcloud. Check that the app is enabled and that its volume "
    "is readable, then run the command again before removing the app."
)

logger = logging.getLogger("mcp_connector.exapp.purge")

#: How a caller hands in its own store, the same shape ``oauth/connections.py`` uses.
type StoreProvider = Callable[[], Awaitable[OAuthStore]]


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
        """Revoke, empty, delete the key. In that order, and only with ``force``."""
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        if not await _forced(request):
            logger.info("a purge without the force option changed nothing")
            return json_response({"purged": False, "hint": FORCE_HINT})

        try:
            store = await store_provider()
            rows = await store.all_authorizations()
        except Exception as exc:
            # The type only, never the message: a store error can carry a path.
            logger.error("the purge found no readable store: %s", type(exc).__name__)
            return json_response({"purged": False, "hint": STORE_HINT})

        revoked, failures = await _hand_back_every(store, rows, env)
        cleared = await _empty(store)
        # Last, and only now. Every ciphertext this key opens is gone at this point, and
        # until this line every one of them still had to be decryptable.
        key_deleted = await crypto.delete_key(env)

        logger.info(
            "the purge ended %s connections, handed back %s app passwords, failed on %s, "
            "cleared the tables: %s, deleted the data key: %s",
            len(rows),
            revoked,
            failures,
            cleared,
            key_deleted,
        )
        return json_response(
            {
                "purged": True,
                "connections": len(rows),
                "revoked": revoked,
                "revoke_failures": failures,
                "tables_cleared": cleared,
                "key_deleted": key_deleted,
            }
        )

    return [Route(PURGE_PATH, purge, methods=["POST"])]


async def _hand_back_every(
    store: OAuthStore, rows: list[AuthorizationRow], env: Mapping[str, str] | None
) -> tuple[int, int]:
    """Give every Nextcloud app password back, one attempt each. Returns (done, failed).

    Three properties of ``provider.sweep_abandoned``, which this loop is built after, hold
    here as well and all three are the difference between a purge and a hang: one attempt
    per credential with the five second timeout of ``loginflow.REVOKE_TIMEOUT`` and no
    retry, a failure that is counted instead of raised, and a loop that keeps going
    (T-05-31). Nothing of a row is logged: the count is the report, the account is not
    (security domain V7, T-05-29).
    """
    revoked = 0
    failures = 0
    for row in rows:
        try:
            password = await store.app_password(row.auth_id)
        except Exception:
            logger.error("the app password of a connection could not be read back")
            password = None

        if password and await loginflow.revoke_app_password(row.nc_user, password, env=env):
            revoked += 1
        else:
            # loginflow already logged what happened, without a value of the exchange.
            failures += 1
            logger.warning("a connection was purged without handing its app password back")
    return revoked, failures


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


async def _forced(request: Request) -> bool:
    """Whether this invocation carries the ``force`` flag, in any shape AppAPI may send it.

    The exact wire shape of an occ option is assumption A5: the interface is verified from
    the source of app_api 34.0.3, but no run against HaRP has confirmed it yet. So the check
    accepts every plausible spelling instead of one guessed one, and refuses everything else.
    Both directions matter. A purge that silently does nothing because the flag arrived as a
    list rather than a mapping would send an administrator into an uninstall believing the
    credentials are gone, and a purge that runs without the flag is an instance wide deletion
    nobody asked for.
    """
    params = request.query_params
    if FORCE_OPTION in params and _is_set(params[FORCE_OPTION]):
        return True
    return _forced_in(await _payload(request))


def _forced_in(payload: Any) -> bool:
    """The flag in a JSON body: at the top level, in a mapping of options, or in a list."""
    if not isinstance(payload, dict):
        return False
    if FORCE_OPTION in payload:
        return _is_set(payload[FORCE_OPTION])

    options = payload.get("options")
    if isinstance(options, dict):
        return FORCE_OPTION in options and _is_set(options[FORCE_OPTION])
    if isinstance(options, list | tuple):
        return any(
            isinstance(item, str) and item.strip().lstrip("-") == FORCE_OPTION for item in options
        )
    return False


def _is_set(value: object) -> bool:
    """Whether this value means the flag is set. Only a spelled out no is a no."""
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in FALSE_WORDS
    return False


async def _payload(request: Request) -> Any:
    """The JSON body, or ``None`` when there is none this handler is willing to read.

    Bounded and never logged. The body arrives on the internal AppAPI path, so it is not
    attacker input in the ordinary sense, and it is still the input of a destructive action:
    an announced length above :data:`MAX_BODY_BYTES` is not an occ invocation and is not
    parsed at all.
    """
    announced = request.headers.get("content-length", "")
    if announced.isdigit() and int(announced) > MAX_BODY_BYTES:
        logger.warning("a purge call announced a body this handler does not read")
        return None
    try:
        raw = await request.body()
    except Exception:
        logger.warning("the body of a purge call could not be read")
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        logger.warning("the body of a purge call is not JSON")
        return None


def _text(body: str, status_code: int) -> Response:
    return Response(body, status_code=status_code, media_type="text/plain", headers=NO_STORE)
