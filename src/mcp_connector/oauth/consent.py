"""``/authorize`` and the consent screen behind it: the bridge into the Nextcloud sign in.

**Why this route exists at all.** The SDK serves ``/authorize`` on its own and answers a
refused request with JSON, which is the right answer for a machine and the wrong one for
the person standing in front of the browser this endpoint redirects. A blocked client, a
return address that does not match the registration and a registration that expired all
end here as a page that names what happened and what to do next (03-UI-SPEC.md, E1 to E5),
and everything the SDK does check stays where it is: this handler decides who gets in and
then hands the request to :class:`AuthorizationHandler` unchanged, so PKCE, the response
type, the exact redirect matching and the RFC error shapes are still the SDK's.

**Why a page and never a redirect for a bad return address.** A redirect to an address the
client did not register is the open redirect this whole check exists against (T-03-41). The
SDK refuses it too; the difference here is that the refusal is readable.

**Why the sign in link travels in the query.** The Login Flow v2 gives us the address of
its sign in page exactly once, in the answer to the authorization request, and the flow
record of the store has no column for it (the schema of plan 03-02 is shipped and a
migration is a bigger decision than this plan). So the redirect carries it, and the page
checks before it renders it that it points at the configured Nextcloud: a link on a page
that asks for trust is exactly the phishing step this surface exists against, and an
unchecked one would let anybody who can build a URL put their own page behind our button
(T-03-42). A link that fails the check is not shown; the sign in still finishes, because
the waiting state polls the flow either way.

**Why the sign in produces an authorization before anybody consented.** The poll answers
200 exactly once, and what it hands over is a Nextcloud app password that exists from that
moment on. It has to be stored right there or it is lost, so the row is written under the
id of its own flow, which is what connects the two without a column for it. Nothing can be
done with that row yet: no token exists without an authorization code, and plan 03-06
creates the code only when the user approves. The denial path of that plan revokes the app
password again, and that is the one piece of housekeeping this state owes.

The route is a factory like every other one of this project and is attached by
``entry_exapp`` alone (D-23). The guards return a response instead of raising, so no
refusal can escape as a 500 (the shape of ``exapp/lifecycle.py``).
"""

import logging
import time
from collections.abc import Mapping
from urllib.parse import urlsplit

from mcp.server.auth.handlers.authorize import AuthorizationHandler
from mcp.server.auth.routes import AUTHORIZATION_PATH
from mcp.shared.auth import InvalidRedirectUriError, OAuthClientInformationFull
from pydantic import AnyUrl, ValidationError
from starlette.datastructures import FormData, QueryParams
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .. import config
from ..errors import ToolError
from ..exapp.ui import errors
from ..exapp.ui.consent import (
    CONSENT_PATH,
    FLOW_PARAM,
    LOGIN_PARAM,
    STEP_PARAM,
    STEP_WAIT,
    consent_page,
    empty_page,
    handoff_page,
    waiting_page,
)
from . import loginflow
from .provider import NextcloudOAuthProvider
from .registry import redirect_uri_allowed
from .store import OAuthStore

__all__ = ["AUTHORIZATION_PATH", "CONSENT_PATH", "consent_routes"]

logger = logging.getLogger("mcp_connector.oauth.consent")


def consent_routes(
    env: Mapping[str, str] | None = None, *, provider: NextcloudOAuthProvider
) -> list[Route]:
    """The authorization endpoint of this app and the consent screen behind it."""
    handler = AuthorizationHandler(provider)

    async def authorize(request: Request) -> Response:
        """The front door: refuse readably, or let the SDK do its work."""
        params = request.query_params if request.method == "GET" else await request.form()
        refusal = await _refuse(params, provider, env)
        if refusal is not None:
            return refusal
        return await handler.handle(request)

    async def consent(request: Request) -> Response:
        """The consent surface: hand over, wait, decide.

        A POST is answered with the page a GET would answer and the status of a request
        this route does not understand yet. The decision itself is plan 03-06, and
        declaring the verb now keeps the manifest from changing twice.
        """
        rendered = await _screen(request.query_params, provider, env)
        if request.method == "POST":
            rendered.status_code = 400
        return rendered

    return [
        Route(AUTHORIZATION_PATH, authorize, methods=["GET", "POST"]),
        Route(CONSENT_PATH, consent, methods=["GET", "POST"]),
    ]


async def _refuse(
    params: QueryParams | FormData,
    provider: NextcloudOAuthProvider,
    env: Mapping[str, str] | None,
) -> Response | None:
    """The page this request ends on, or ``None`` when it may go to the SDK handler."""
    client_id = str(params.get("client_id") or "")
    if not client_id:
        # Not an authorization request at all: a link somebody kept, a stale tab, or the
        # "Start over" of the timeout page. The empty state says so in a sentence.
        return empty_page(env=env)

    client = await provider.get_client(client_id)
    if client is None:
        return _no_client_page(client_id, provider, env)

    raw = params.get("redirect_uri")
    try:
        requested = AnyUrl(str(raw)) if raw else None
        address = client.validate_redirect_uri(requested)
    except (InvalidRedirectUriError, ValidationError, ValueError):
        return _page(errors.error_page("E5", env=env, client=_name(client)))
    if not redirect_uri_allowed(str(address)):
        # A registration from before this rule, or one written another way. The address is
        # checked where it is used and not only where it was accepted (T-03-41).
        return _page(errors.error_page("E5", env=env, client=_name(client)))
    return None


def _no_client_page(
    client_id: str, provider: NextcloudOAuthProvider, env: Mapping[str, str] | None
) -> Response:
    """Which of the three pages a refused client gets, decided without asking the store.

    ``get_client`` answers ``None`` for unknown, blocked, unlisted and expired alike, and
    that is deliberate: an answer that separates them is an information service for whoever
    is guessing client ids (T-03-47). The page is therefore chosen from the policy, which
    is the administrator's own configuration and tells the caller nothing about any client:

    * with the allowlist mode on, the next step is an administrator (E1),
    * with registration switched off, the next step is an administrator too, and the page
      names the reason a registration would fail (E2),
    * otherwise the honest reading is that the registration is gone or was never made, and
      the next step is the app that asked (E3).
    """
    policy = provider.policy
    if policy.allowlist_only and not policy.listed(client_id):
        return _page(errors.error_page("E1", env=env, client=client_id))
    if not policy.dcr_enabled:
        return _page(errors.error_page("E2", env=env, client=client_id))
    return _page(errors.error_page("E3", env=env, client=client_id))


async def _screen(
    params: QueryParams,
    provider: NextcloudOAuthProvider,
    env: Mapping[str, str] | None,
) -> Response:
    """One of the four states of the consent surface, in the order they can happen."""
    flow_id = params.get(FLOW_PARAM) or ""
    if not flow_id:
        return _page(errors.error_page("E3", env=env))

    store = await _store_or_page(provider, env)
    if isinstance(store, Response):
        return store

    # Loaded without the deadline, so that "ran out of time" and "never existed" can be
    # told apart here. Nextcloud cannot tell them apart: it answers 404 for both.
    row = await store.load_flow(flow_id, now=0)
    if row is None:
        return _page(errors.error_page("E3", env=env))
    if row.expires_at <= _now():
        await store.delete_flow(flow_id)
        return _page(errors.error_page("E4", env=env))

    client = await provider.get_client(row.client_id)
    if client is None:
        # The enforcement point again, on the way to the decision: a client that was
        # blocked while its user was signing in must not reach the screen that grants
        # anything (T-03-40, pitfall 9).
        return _no_client_page(row.client_id, provider, env)

    signed_in = await store.load_authorization(flow_id)
    if signed_in is not None:
        return _decision(client, signed_in.nc_user, row.redirect_uri, provider, env)

    if params.get(STEP_PARAM) != STEP_WAIT:
        link = _sign_in_link(params.get(LOGIN_PARAM) or "", env)
        if link:
            return handoff_page(_name(client), link, flow_id, env=env)
        # No usable link, so the honest page is the one that keeps asking: the sign in may
        # already be running in another window.
        return waiting_page(flow_id, env=env)

    result = await loginflow.poll_once(row.poll_token, env=env)
    if result.outcome == loginflow.POLL_PENDING:
        return waiting_page(flow_id, env=env)
    if result.outcome != loginflow.POLL_DONE or result.credentials is None:
        return _generic("the login flow poll failed", env)

    credentials = result.credentials
    try:
        # Written under the id of its own flow, which is what connects the two without a
        # column for it. It has to happen now: the 200 of a poll arrives exactly once.
        await store.create_authorization(
            flow_id,
            client_id=row.client_id,
            nc_user=credentials.login_name,
            app_password=credentials.app_password,
            scopes=row.scopes,
            resource=row.resource,
        )
    except Exception:
        logger.exception("the finished sign in could not be written to the store")
        # The app password exists at Nextcloud from now on and nobody will ever use it, so
        # it is handed back instead of left behind (pitfall 13, D-34).
        await loginflow.revoke_app_password(
            credentials.login_name, credentials.app_password, env=env
        )
        return _generic("the finished sign in could not be written to the store", env)

    return _decision(client, credentials.login_name, row.redirect_uri, provider, env)


def _decision(
    client: OAuthClientInformationFull,
    user: str,
    redirect_uri: str,
    provider: NextcloudOAuthProvider,
    env: Mapping[str, str] | None,
) -> Response:
    """The consent screen, with the warning that belongs to a self registered client.

    The warning is the answer to "who says this app is what it says it is". In v1 every
    client in the registry got there by registering itself, so the honest condition is
    membership of the administrator's list, and the shipped state (an empty list) shows the
    warning for every one of them (03-UI-SPEC.md, S3, T-03-42).
    """
    addresses = [str(uri) for uri in client.redirect_uris or []]
    return consent_page(
        _name(client),
        client.client_id,
        redirect_uri,
        user,
        unverified=not provider.policy.listed(client.client_id, addresses),
        env=env,
    )


def _sign_in_link(candidate: str, env: Mapping[str, str] | None) -> str:
    """The Nextcloud sign in address, or an empty string when it is not one.

    Two checks, and both are about the same question: does this address belong to the
    Nextcloud this app is deployed against. The scheme is checked because a link is
    clicked, and the host because the value travelled through the browser and anybody can
    write a URL. The two accepted hosts are the configured Nextcloud and the configured
    public address of this app, which in every supported topology are the same domain: the
    ExApp lives under it, and Nextcloud builds its sign in address from ``overwrite.cli.url``.
    """
    if not candidate:
        return ""
    parts = urlsplit(candidate)
    if parts.scheme not in ("https", "http") or not parts.netloc:
        return ""
    known = {
        urlsplit(config.public_url(env)).netloc,
        urlsplit(_nextcloud_base(env)).netloc,
    }
    if parts.netloc not in known - {""}:
        logger.warning("a sign in link of a foreign host was not rendered")
        return ""
    return candidate


def _nextcloud_base(env: Mapping[str, str] | None) -> str:
    """The configured Nextcloud, or an empty string when this process has none."""
    try:
        return config.exapp_settings(env).base_url
    except ToolError:
        return ""


async def _store_or_page(
    provider: NextcloudOAuthProvider, env: Mapping[str, str] | None
) -> OAuthStore | Response:
    """The store, or the page that ends the request. Never an exception into the framework.

    Fail closed (D-37): an incomplete deploy environment, a volume that is not writable and
    a data key that cannot be fetched are one answer to the user, and all three are an
    administrator's problem rather than theirs.
    """
    try:
        return await provider.store()
    except ToolError as exc:
        logger.error("the consent screen has no store: %s %s", exc.message, exc.hint)
        return _generic("the store could not be opened", env)
    except Exception:
        logger.exception("the consent screen could not open its store")
        return _generic("the store could not be opened", env)


def _name(client: OAuthClientInformationFull) -> str:
    """The name a registration gave itself, cleaned and cut where it is rendered."""
    return client.client_name or ""


def _generic(what: str, env: Mapping[str, str] | None) -> Response:
    """The generic page plus the one log line that carries its reference (T-03-24)."""
    response, reference = errors.error_page("E7", env=env)
    logger.error("%s (reference %s)", what, reference)
    return response


def _page(built: tuple[Response, str]) -> Response:
    """Take the response of an error page whose reference nobody has to log."""
    response, _ = built
    return response


def _now() -> int:
    """Whole seconds, in one place, so a deadline is compared against one clock."""
    return int(time.time())
