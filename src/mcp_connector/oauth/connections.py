"""``/connections``: the page on which a user sees, ends and pauses their own connections.

One route, two verbs and a named action field, exactly as ``/connect`` handles its start
and its cancel: the list, the confirmation, the disconnect and the switch are one resource,
and every declared route is a line of external attack surface (D-38, T-04-36). The routes
are handed out by :func:`connections_routes` and attached by ``entry_exapp`` alone, so the
stdio server and the standalone HTTP server of phase 1 never grow a page that can end a
Nextcloud connection (D-23).

Four properties are the whole security of this module, and the rest of the file is their
mechanics:

* **The identity comes from HaRP and from nowhere else.** ``appapi_user`` reads the account
  out of the header AppAPI signs with ``APP_SECRET``, and a request without one arrives as
  the empty string, which :func:`is_user` never accepts. An empty identity is E8 on both
  verbs, before anything is read and long before anything is written (T-04-31).
* **Every state change is a POST with an anti forgery value.** The value is an HMAC under
  the data key of this installation, derived from the purpose of the form and the handle it
  is about, and it is compared in constant time. A row value is derived from the connection
  handle and the switch value from ``access:`` plus the account, so a value of one row
  cannot operate the switch and a value of one account cannot pause another (T-04-30). The
  purpose is what keeps the two forms of one connection apart, because an authorization
  carries the id of the flow it was born in and the consent form of that flow is about the
  very same string (ME-01).
* **Nothing here revokes anything itself.** The disconnect calls ``end_connection`` of the
  provider, the same sequence ``/revoke`` and the reuse detection of the rotation run,
  including the invalidation of the verifier cache. A second revocation path would be a
  second place to forget that cache in, and a revoked token would keep working for the five
  seconds of that window (T-03-62, T-04-35).
* **A refusal never tells anybody which check fired.** An unknown handle, a handle of
  another account, an already revoked one and a form without the anti forgery value are one
  answer: the list with the "Already disconnected" callout (T-04-31, the S8 contract).

Every answer is a page and never a redirect (CR-03): the answer of a form submission may
not be a redirect a browser checks against ``form-action 'self'``. The guards return a
response instead of raising, so no refusal escapes as a 500, and a store that cannot be
read is E7 with a reference in the log (fail closed, D-37). That promise now includes the
body itself: a form that cannot be parsed is answered by ``form_or_none`` with a page and
not by the framework with a traceback (HI-02).
"""

import json
import logging
import secrets
from collections.abc import Awaitable, Callable, Mapping

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..errors import ToolError
from ..exapp.auth import appapi_user, is_user
from ..exapp.responses import form_or_none
from ..exapp.ui import errors
from ..exapp.ui.connections import (
    ACTION_CONFIRM,
    ACTION_DISCONNECT,
    ACTION_FIELD,
    ACTION_KEEP,
    ACTION_PAUSE,
    ACTION_RESUME,
    AUTH_PARAM,
    CONFIRM_PARAM,
    CONNECTIONS_PATH,
    RESULT_DONE,
    RESULT_GONE,
    Connection,
    confirm_page,
    connections_page,
)
from .crypto import PURPOSE_DISCONNECT, PURPOSE_SWITCH
from .store import AuthorizationRow, OAuthStore
from .throttle import CLASS_CONNECTIONS, Throttle, Throttled

__all__ = ["SWITCH_HANDLE", "connections_routes"]

#: What the anti forgery value of the switch is derived from: this prefix plus the account,
#: under :data:`~mcp_connector.oauth.crypto.PURPOSE_SWITCH`. The account in the handle is
#: what keeps the value of one account from pausing another; the prefix predates the purpose
#: of ME-01 and stays because a handle that says what it is costs nothing (T-04-30).
SWITCH_HANDLE = "access:"

logger = logging.getLogger("mcp_connector.oauth.connections")

#: How a caller hands in its own store, the same shape ``oauth/connect.py`` uses.
type StoreProvider = Callable[[], Awaitable[OAuthStore]]

#: The one revocation of this deployment, handed in rather than imported: the page ends a
#: connection through ``provider.end_connection`` and never through the store (T-04-35).
type EndConnection = Callable[[str], Awaitable[bool]]

#: What a registration is called when its stored metadata cannot be read as a name. Empty
#: on purpose: ``layout.client_name`` turns it into the fallback wording, so a row of a
#: damaged registration is still a row a user can disconnect.
_NO_NAME = ""


def connections_routes(
    env: Mapping[str, str] | None = None,
    *,
    store_provider: StoreProvider,
    end_connection: EndConnection,
    throttle: Throttle | None = None,
) -> list[Route]:
    """The one route of the connections page, throttled as the emergency brake it is.

    A class of its own and a counter per account (HI-01). The page used to hang in
    ``CLASS_AUTHORIZE`` with the argument that only refusals have to be bounded here, which
    is true about the cost and wrong about the effect: what got bounded was not the attacker
    but the way to the switch. Two hundred anonymous requests, each with a different forged
    forwarded address, filled the ceiling of that whole class, and for the next five minutes
    the page answered E6 to everybody, its owner included, and every consent decision of the
    instance with it.

    Three properties hold it now. The class is this page and nothing else, so no other
    surface can close it and it can close no other surface. The counter is keyed by the
    account HaRP signed rather than by a header the caller writes, so one account's refusals
    never reach another account. And a request without an account is not counted at all: it
    is E8 before anything is read and costs nothing worth bounding.

    A refused request here is a page, so a throttled one is E6 with the same seconds in its
    header and in its text (T-04-37, D-37).
    """

    async def connections(request: Request) -> Response:
        """The list, and every action on it. One route, one identity check, one store."""
        user = appapi_user(request, env=env)
        if not user:
            # E8 before anything is read: an anonymous caller learns nothing at all about
            # this deployment, not even whether an account has connections (T-04-31).
            return _page(errors.error_page("E8", env=env))

        store = await _store_or_page(store_provider, env)
        if isinstance(store, Response):
            return store

        if request.method == "GET":
            return await _list(store, user, env)

        form = await form_or_none(request)
        if form is None:
            # A body this server cannot read is not a refusal of one of the guards below,
            # so it is the generic page with a reference in the log, and never the traceback
            # the framework used to answer with (HI-02).
            return _generic("a submitted form could not be parsed", env)
        return await _act(form, store, user, end_connection, env)

    def account(request: Request) -> str:
        """Who the counter of this request belongs to, or the empty string for nobody."""
        return appapi_user(request, env=env)

    route = Route(CONNECTIONS_PATH, connections, methods=["GET", "POST"])
    counters = throttle if throttle is not None else Throttle()
    route.app = Throttled(
        route.app, counters, CLASS_CONNECTIONS, machine=False, env=env, identity=account
    )
    return [route]


async def _act(
    form: FormData,
    store: OAuthStore,
    user: str,
    end_connection: EndConnection,
    env: Mapping[str, str] | None,
) -> Response:
    """Dispatch one submitted form, over a closed enumeration of five actions.

    Anything else is the list with a 400: not an error a user can act on differently, and
    not a page of its own, exactly as the onboarding answers a POST it does not understand.
    """
    action = str(form.get(ACTION_FIELD) or "")
    presented = str(form.get(CONFIRM_PARAM) or "")
    auth_id = str(form.get(AUTH_PARAM) or "")

    if action == ACTION_CONFIRM:
        return await _confirm(auth_id, store, user, env)
    if action == ACTION_DISCONNECT:
        return await _disconnect(auth_id, presented, store, user, end_connection, env)
    if action in (ACTION_PAUSE, ACTION_RESUME):
        return await _switch(action, presented, store, user, env)
    if action == ACTION_KEEP:
        # The safe button of the confirmation page. It changes nothing, so its answer is
        # the list the user came from, with the status of a page that worked.
        return await _list(store, user, env)
    return await _list(store, user, env, status_code=400)


async def _confirm(
    auth_id: str, store: OAuthStore, user: str, env: Mapping[str, str] | None
) -> Response:
    """S7 for a live connection of this account, and the S8 answer for everything else.

    The three cases an attacker can produce, an unknown handle, a handle of another account
    and one that was revoked, are answered by the same page as a resubmitted form: a page
    that told them apart would answer whether that connection exists (T-04-31).
    """
    row = await _owned(auth_id, store, user, env)
    if isinstance(row, Response):
        return row
    if row is None:
        return await _list(store, user, env, result=RESULT_GONE)
    return confirm_page(await _connection(row, store), env=env)


async def _disconnect(
    auth_id: str,
    presented: str,
    store: OAuthStore,
    user: str,
    end_connection: EndConnection,
    env: Mapping[str, str] | None,
) -> Response:
    """End one connection, through the one revocation path of this deployment.

    Ownership first and the anti forgery value second, and both refusals answer the same
    page: a refusal that named the reason would tell whoever tried which of the two halves
    they were missing (T-03-47, the rule of ``oauth/consent.py``).
    """
    row = await _owned(auth_id, store, user, env)
    if isinstance(row, Response):
        return row
    if row is None:
        return await _list(store, user, env, result=RESULT_GONE)

    if not _confirmed(store, auth_id, presented, purpose=PURPOSE_DISCONNECT):
        logger.warning("a disconnect arrived without the anti forgery value of its connection")
        return await _list(store, user, env, result=RESULT_GONE)

    # The name is read before the connection ends, because the callout names the app that
    # just lost access and the registration may be swept once nothing points at it.
    name = await _client_name(row.client_id, store)
    try:
        ended = await end_connection(auth_id)
    except Exception:
        logger.exception("a connection could not be ended")
        return _generic("the connection could not be ended", env)

    if not ended:
        return await _list(store, user, env, result=RESULT_GONE)
    return await _list(store, user, env, result=RESULT_DONE, result_client=name)


async def _switch(
    action: str, presented: str, store: OAuthStore, user: str, env: Mapping[str, str] | None
) -> Response:
    """Pause or resume the MCP access of the account behind this browser (SC 1).

    A named state and never a toggle, so a resubmitted or replayed form re-states a state
    instead of flipping it. The answer is the re-rendered list, where the pause callout
    appears or disappears: the proof of effect is the page itself.

    A form without the switch value changes nothing and answers the list unchanged. It is
    not the "Already disconnected" callout, because nothing was disconnected and a sentence
    about a connection would be a wrong sentence; the state above the callout is what the
    reader has to be able to trust, and it is the truth either way.
    """
    if not _confirmed(store, f"{SWITCH_HANDLE}{user}", presented, purpose=PURPOSE_SWITCH):
        logger.warning("a switch arrived without the anti forgery value of its account")
        return await _list(store, user, env)
    try:
        await store.set_access(user, disabled=action == ACTION_PAUSE)
    except Exception:
        logger.exception("the access switch of an account could not be written")
        return _generic("the access switch could not be written", env)
    return await _list(store, user, env)


async def _list(
    store: OAuthStore,
    user: str,
    env: Mapping[str, str] | None,
    *,
    result: str = "",
    result_client: str = "",
    status_code: int = 200,
) -> Response:
    """S5, S6 and S8: whatever this account looks like right now, read in one place.

    Every answer of this route ends here, including the refusals, so the page a user gets
    back is always the current state of their own account and never a stale copy of the
    form they submitted.
    """
    try:
        rows = await store.authorizations_of_user(user)
        paused = await store.access_disabled(user)
        connections = [await _connection(row, store) for row in rows]
    except Exception:
        logger.exception("the connections of an account could not be read")
        return _generic("the connections could not be read", env)

    return connections_page(
        connections,
        user=user,
        paused=paused,
        switch_token=store.form_token(f"{SWITCH_HANDLE}{user}", purpose=PURPOSE_SWITCH),
        result=result,
        result_client=result_client,
        status_code=status_code,
        env=env,
    )


async def _owned(
    auth_id: str, store: OAuthStore, user: str, env: Mapping[str, str] | None
) -> AuthorizationRow | Response | None:
    """The live connection of this account behind this handle, or ``None``, or a page.

    ``None`` is the answer for all three of unknown, revoked and belonging to somebody
    else, which is what makes the caller unable to tell them apart even by accident.
    """
    if not auth_id:
        return None
    try:
        row = await store.load_authorization(auth_id)
    except Exception:
        logger.exception("a connection could not be read back")
        return _generic("the connection could not be read", env)
    if row is None or row.revoked_at is not None or not is_user(user, row.nc_user):
        return None
    return row


async def _connection(row: AuthorizationRow, store: OAuthStore) -> Connection:
    """One store row as the page shows it, with the anti forgery value of exactly that row."""
    return Connection(
        auth_id=row.auth_id,
        client_name=await _client_name(row.client_id, store),
        client_id=row.client_id,
        created_at=row.created_at,
        token=store.form_token(row.auth_id, purpose=PURPOSE_DISCONNECT),
    )


async def _client_name(client_id: str, store: OAuthStore) -> str:
    """What the registration behind a connection calls itself, or an empty string.

    Attacker input twice over: the value comes from a dynamic client registration, and it
    is read out of stored JSON. A registration that cannot be read is not an error of this
    page, so it becomes the fallback wording of ``layout.client_name`` instead of a refusal
    the user cannot act on (T-04-34).
    """
    try:
        row = await store.load_client(client_id)
    except Exception:
        logger.error("the registration of a listed connection could not be read")
        return _NO_NAME
    if row is None:
        return _NO_NAME
    try:
        metadata = json.loads(row.metadata_json)
    except (TypeError, ValueError):
        logger.error("the registration of a listed connection is not readable JSON")
        return _NO_NAME
    name = metadata.get("client_name") if isinstance(metadata, dict) else None
    return str(name) if isinstance(name, str) else _NO_NAME


def _confirmed(store: OAuthStore, handle: str, presented: str, *, purpose: str) -> bool:
    """Whether this form came from a page this server rendered for this handle and purpose.

    ``compare_digest`` on bytes and not ``==``: the value arrives from a request, and a
    comparison that stops at the first different character leaks its prefix over enough
    attempts (the rule of ``exapp/auth.py`` and of the consent decision).

    ``purpose`` is what keeps the value of the consent form of a connection from ending that
    connection: both forms are about the same id (ME-01).
    """
    expected = store.form_token(handle, purpose=purpose)
    return bool(presented) and secrets.compare_digest(
        expected.encode("utf-8"), presented.encode("utf-8")
    )


async def _store_or_page(
    store: StoreProvider, env: Mapping[str, str] | None
) -> OAuthStore | Response:
    """The store, or the page that ends the request. Never an exception into the framework.

    Fail closed (D-37): an incomplete deploy environment, a volume that is not writable and
    a data key that cannot be fetched are one answer to the user, and all three are an
    administrator's problem rather than theirs.
    """
    try:
        return await store()
    except ToolError as exc:
        logger.error("the connections page has no store: %s %s", exc.message, exc.hint)
        return _generic("the store could not be opened", env)
    except Exception:
        logger.exception("the connections page could not open its store")
        return _generic("the store could not be opened", env)


def _generic(what: str, env: Mapping[str, str] | None) -> Response:
    """The generic page plus the one log line that carries its reference (T-03-24)."""
    response, reference = errors.error_page("E7", env=env)
    logger.error("%s (reference %s)", what, reference)
    return response


def _page(built: tuple[Response, str]) -> Response:
    """Take the response of an error page whose reference nobody has to log."""
    response, _ = built
    return response
