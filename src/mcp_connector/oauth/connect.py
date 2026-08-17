"""The browser onboarding for clients that cannot speak OAuth (AUTH-02, D-36).

Three routes under ``/connect``: the invitation, the start of a sign in, and the waiting
screen that turns into the result. What the user gets at the end is one dedicated Nextcloud
app password, which they paste into their assistant app. What this server never gets, at any
point, is the password of that user: Nextcloud runs the sign in on its own pages, second
factor included, and there is no input on this whole route (T-03-30).

Built like :mod:`mcp_connector.exapp.lifecycle`, the one file of this repository that serves
several routes from one factory: the routes are handed out by :func:`connect_routes` and
attached by ``entry_exapp.build_exapp_app`` alone, so the standalone HTTP server and the
stdio server of phase 1 never grow a browser surface (D-23). The guards return a response
instead of raising, so no rejection can escape as a 500 and every end of this flow is a page
that names the next step.

Three properties are worth stating in one place, because the rest of the file is the
mechanics of them:

* **The flow id names a sign in, it does not authorise reading its result.** It is a
  ``secrets.token_urlsafe`` value and it travels in the URL of the waiting page, which is
  why every page here carries ``Referrer-Policy: no-referrer`` (the sign in link opens
  another origin), why the record expires after twenty minutes and why it is deleted the
  moment the flow ends (T-03-32). What decides whether the credential is *shown* is the
  Nextcloud account behind the browser: the flow id belongs to whoever started the flow,
  and that is not necessarily the person who signed in (CR-01).
* **The poll token is encrypted at rest**, bound to the flow id as additional authenticated
  data, so reading the store file does not hand anyone a running sign in (T-03-32).
* **The credential is never stored.** It is rendered into one answer and dropped. The store
  never sees it, no log line carries it, and the answer carries ``no-store`` (T-03-33). The
  connection is visible and revocable in Nextcloud under "Devices and sessions", which is
  where it belongs: it is the user's connection, not ours.
"""

import asyncio
import logging
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from .. import config
from ..errors import ToolError
from ..exapp.auth import appapi_user, is_user
from ..exapp.responses import NO_STORE, form_or_none
from ..exapp.ui import errors
from ..exapp.ui.connect import (
    ACTION_CANCEL,
    ACTION_FIELD,
    ACTION_START,
    CONNECT_PATH,
    FLOW_PARAM,
    WAIT_PATH,
    handoff_page,
    invitation_page,
    result_page,
    waiting_page,
)
from . import crypto, loginflow
from .store import STORE_FILENAME, OAuthStore
from .throttle import CLASS_CONNECT, CLASS_CONNECT_START, FLOW_LIMIT, Throttle, Throttled

__all__ = [
    "ACTION_CANCEL",
    "ACTION_FIELD",
    "ACTION_START",
    "CONNECT_CLIENT_ID",
    "CONNECT_PATH",
    "FLOW_ID_BYTES",
    "FLOW_PARAM",
    "ONBOARDING_CLIENT_NAME",
    "WAIT_PATH",
    "connect_routes",
]

#: The reserved client id every onboarding flow is booked under. The ``flows`` table points
#: at ``clients`` with a foreign key, because in the OAuth flow of plan 03-05 a flow always
#: belongs to a registered client. This route has no client at all: the user is here exactly
#: because their app cannot register itself. So it books its flows under one reserved row,
#: which is marked as not allowed and therefore refused by the enforcement point of AUTH-07:
#: it is a bookkeeping row, never a client that may ask for a token.
CONNECT_CLIENT_ID = "urn:mcp-connector:browser-onboarding"

#: What the reserved row says about itself when an administrator looks into the store.
_CONNECT_CLIENT_METADATA = '{"client_name":"Browser onboarding (AUTH-02), not a registration"}'

#: The name that reaches Nextcloud as the user agent of the start request and becomes the
#: entry in "Devices and sessions" (T-03-37). ``loginflow`` puts its fixed prefix in front.
ONBOARDING_CLIENT_NAME = "browser onboarding"

#: 32 bytes of entropy behind a flow id, which ``token_urlsafe`` renders as 43 characters.
FLOW_ID_BYTES = 32

logger = logging.getLogger("mcp_connector.oauth.connect")

#: How a caller hands in its own store, which is what the tests of this route do. In a
#: deployed process the factory opens one itself, on first use.
type StoreProvider = Callable[[], Awaitable[OAuthStore]]


def connect_routes(
    env: Mapping[str, str] | None = None,
    *,
    store_provider: StoreProvider | None = None,
    throttle: Throttle | None = None,
) -> list[Route]:
    """Build the three onboarding routes against one environment.

    Throttled as browser paths, and in two classes rather than one: this is the surface on
    which an anonymous caller can make this server open a Nextcloud login flow, which is
    the anonymous flow creation T-03-35 handed to this plan (SC 5). The POST that opens one
    is counted on every request, because it answers 200 when it succeeds and a counter that
    only saw refusals bounded nothing at all on the one path it was built for (CR-02). The
    invitation and the waiting screen keep the refusal counter: they cost a poll, not a
    flow, and the waiting screen loads itself every three seconds by design. A refused
    request here is a page, so a throttled one is E6 with the same seconds in header and
    text.

    The store is opened once per application and not once per request, and the first open is
    also where :meth:`OAuthStore.purge_expired` runs: this project has no cron and no
    scheduler, so the sweep that removes what ran out hangs on the first use of the store
    (T-03-17). The cache lives in this closure and not in a module global, because a
    dictionary that outlives a request is one refactor away from being a session store
    (D-20), and because two applications in one process are a thing tests do.
    """
    opened: dict[str, OAuthStore] = {}
    lock = asyncio.Lock()

    async def store() -> OAuthStore:
        if store_provider is not None:
            return await store_provider()
        ready = opened.get("store")
        if ready is not None:
            return ready
        async with lock:
            ready = opened.get("store")
            if ready is None:
                # The key first: it is the one step that can fail with a named error, and it
                # fails before anything creates a directory.
                key = await crypto.data_key(env)
                ready = OAuthStore(config.persistent_storage(env) / STORE_FILENAME, key)
                await ready.purge_expired()
                opened["store"] = ready
            return ready

    async def invitation(request: Request) -> Response:
        """The page that explains the way and offers the one button that starts it."""
        return invitation_page(env=env)

    async def begin(request: Request) -> Response:
        """Start a sign in, or cancel a running one. The only state changing route here."""
        form = await form_or_none(request)
        if form is None:
            # A body no parser can read is the same case as an action this route does not
            # know, and it gets the same answer rather than a traceback (HI-02).
            return _with_status(invitation_page(env=env), 400)
        action = str(form.get(ACTION_FIELD) or "")
        if action == ACTION_CANCEL:
            return await _cancel(str(form.get(FLOW_PARAM) or ""), store, env)
        if action != ACTION_START:
            # Not an error a user can act on differently, and not one worth a page of its
            # own: the invitation is exactly the next step, with a status that says the
            # request was not one this route understands.
            return _with_status(invitation_page(env=env), 400)
        return await _start(store, env)

    async def wait(request: Request) -> Response:
        """One poll per load, and one of the four ends: waiting, result, expired, failed."""
        return await _wait(request, store, env)

    counters = throttle if throttle is not None else Throttle()
    invitation_route = Route(CONNECT_PATH, invitation, methods=["GET"])
    begin_route = Route(CONNECT_PATH, begin, methods=["POST"])
    wait_route = Route(WAIT_PATH, wait, methods=["GET"])

    for route in (invitation_route, wait_route):
        route.app = Throttled(route.app, counters, CLASS_CONNECT, machine=False, env=env)
    # The POST is the one request of this route that makes Nextcloud open a login flow, so
    # every one of them is counted and not only the refused ones (CR-02, SC 5). It has a
    # path class and a limit of its own for that: the pages behind it are loaded once every
    # three seconds by a waiting screen that is doing nothing wrong, and they must not run
    # into the ceiling of the requests that cost a round trip.
    begin_route.app = Throttled(
        begin_route.app,
        counters,
        CLASS_CONNECT_START,
        machine=False,
        env=env,
        count_all=True,
        limit=FLOW_LIMIT,
    )
    return [invitation_route, begin_route, wait_route]


async def _start(store: StoreProvider, env: Mapping[str, str] | None) -> Response:
    """Open a sign in at Nextcloud and remember it long enough to ask about it."""
    opened = await _store_or_page(store, env)
    if isinstance(opened, Response):
        return opened

    started = await loginflow.start_flow(ONBOARDING_CLIENT_NAME, env=env)
    if started is None:
        # loginflow logged what happened; nothing of the request is repeated here.
        return _generic("the login flow could not be started", env)

    flow_id = secrets.token_urlsafe(FLOW_ID_BYTES)
    try:
        await opened.save_client(
            CONNECT_CLIENT_ID, metadata_json=_CONNECT_CLIENT_METADATA, allowed=False
        )
        await opened.touch_client(CONNECT_CLIENT_ID)
        await opened.create_flow(
            flow_id,
            client_id=CONNECT_CLIENT_ID,
            # No redirect target, no code challenge, no scope and no resource: this route
            # issues no token and sends the user nowhere. The columns exist for the OAuth
            # flow of plan 03-05, and an empty value is the honest entry for this one.
            redirect_uri="",
            redirect_uri_explicit=False,
            code_challenge="",
            state=None,
            scopes="",
            resource="",
            poll_token=started.poll_token,
        )
    except Exception:
        logger.exception("the login flow could not be written to the store")
        return _generic("the flow record could not be written", env)

    return handoff_page(started.login_url, flow_id, env=env)


async def _cancel(flow_id: str, store: StoreProvider, env: Mapping[str, str] | None) -> Response:
    """Drop a running sign in and go back to the start. Idempotent by construction."""
    opened = await _store_or_page(store, env)
    if isinstance(opened, Response):
        return opened
    if flow_id:
        await opened.delete_flow(flow_id)
    # A redirect and not a rendered page: the next reload of the browser must not repeat the
    # POST that just changed something.
    return RedirectResponse(CONNECT_PATH, status_code=303, headers=dict(NO_STORE))


async def _wait(request: Request, store: StoreProvider, env: Mapping[str, str] | None) -> Response:
    """The waiting screen: one poll, then one of the four ends of this flow.

    The result end of it is the one page of this project that writes a credential into a
    document, and since CR-01 it is also the one that asks who is reading. The flow id is
    not an answer to that question: it belongs to whoever started the flow, and an attacker
    who starts a flow, sends the victim nothing but Nextcloud's own sign in link and then
    loads this page would read the victim's app password off their own screen. So the
    credential is only rendered to the Nextcloud account that just signed in, and every
    other case hands the credential back to Nextcloud instead of showing it (D-34).
    """
    opened = await _store_or_page(store, env)
    if isinstance(opened, Response):
        return opened

    flow_id = request.query_params.get(FLOW_PARAM) or ""
    if not flow_id:
        return _page(errors.error_page("E3", env=env))

    # Loaded without the deadline, so that "ran out of time" and "never existed" can be told
    # apart here. Nextcloud cannot tell them apart: it answers 404 for both (pitfall 7).
    try:
        # ``load_flow`` decrypts the poll token of the row, and a data key that changed or
        # a damaged blob make that a refusal. Unguarded it reached Starlette as a bare 500,
        # while the docstring of this module said no rejection escapes as one (WR-06).
        row = await opened.load_flow(flow_id, now=0)
    except Exception:
        logger.exception("a flow record could not be read back")
        return _generic("the flow record could not be read", env)
    if row is None:
        return _page(errors.error_page("E3", env=env))
    if row.expires_at <= _now():
        await opened.delete_flow(flow_id)
        return _page(errors.error_page("E4", env=env))

    result = await loginflow.poll_once(row.poll_token, env=env)
    if result.outcome == loginflow.POLL_PENDING:
        return waiting_page(flow_id, env=env)
    if result.outcome != loginflow.POLL_DONE or result.credentials is None:
        return _generic("the login flow poll failed", env)

    credentials = result.credentials
    if not is_user(appapi_user(request, env=env), credentials.login_name):
        # Not the browser of the account that signed in, so the credential is not shown to
        # it. It exists at Nextcloud from the moment of the poll, and nobody will ever use
        # it now, so it goes back the same way a failed write hands it back (pitfall 13).
        logger.warning("a finished sign in was not handed to the account that signed in")
        await loginflow.revoke_app_password(
            credentials.login_name, credentials.app_password, env=env
        )
        await opened.delete_flow(flow_id)
        return _page(errors.error_page("E3", env=env))

    try:
        # Deleted before the credential is rendered, not after: the 200 of a poll arrives
        # exactly once, so a record that survives the answer would leave the next load
        # waiting for a result that can never come again.
        await opened.delete_flow(flow_id)
    except Exception:
        logger.exception("the finished flow record could not be removed")
        # The credential exists in Nextcloud at this point and would stay there unused, so
        # it is handed back instead of being left behind (pitfall 13, D-34).
        await loginflow.revoke_app_password(
            credentials.login_name, credentials.app_password, env=env
        )
        return _generic("the finished flow record could not be removed", env)

    return result_page(credentials.login_name, credentials.app_password, env=env)


async def _store_or_page(
    store: StoreProvider, env: Mapping[str, str] | None
) -> OAuthStore | Response:
    """The store, or the page that ends the request. Never an exception into the framework.

    Fail closed (D-37): a deploy environment that is not complete, a volume that is not
    writable and a data key that cannot be fetched are all the same answer to the user, and
    all of them are an administrator's problem rather than theirs.
    """
    try:
        return await store()
    except ToolError as exc:
        logger.error("the onboarding has no store: %s %s", exc.message, exc.hint)
        return _generic("the store could not be opened", env)
    except Exception:
        logger.exception("the onboarding could not open its store")
        return _generic("the store could not be opened", env)


def _generic(what: str, env: Mapping[str, str] | None = None) -> Response:
    """The generic page plus the one log line that carries its reference (T-03-24).

    The reference is the only thing that connects a user report with a log entry, and it is
    written here, at the one place the page is built, so it cannot be the reference of
    another answer.
    """
    response, reference = errors.error_page("E7", env=env)
    logger.error("%s (reference %s)", what, reference)
    return response


def _page(built: tuple[Response, str]) -> Response:
    """Take the response of an error page whose reference nobody has to log."""
    response, _ = built
    return response


def _with_status(response: Response, status_code: int) -> Response:
    """The same page, answered with a different status. Used once, for a request we ignore."""
    response.status_code = status_code
    return response


def _now() -> int:
    """Whole seconds, in one place, so a deadline is compared against one clock."""
    return int(time.time())
