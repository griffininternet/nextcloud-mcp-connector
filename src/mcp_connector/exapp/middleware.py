"""The transport boundary in front of the MCP route: two identity sources (CR-01, T-03-01).

``deps.resolve_credentials`` verifies the same handshake, and it stays where it is. The
difference is what each of the two protects. The check in the credential layer is a
handler control point: it runs when a tool asks for credentials, so everything the MCP
protocol does before that (``initialize``, ``tools/list``, session allocation) was served
to an unauthenticated caller. Measured, not assumed: without this module the ExApp
application answers 200 to an ``initialize`` that carries no AppAPI header at all.

So this is a second control, not a replacement. The handler check keeps a future tool that
forgets ``resolve_clients`` from reading data, this one keeps an unauthenticated caller
from reaching MCP code in the first place.

Since plan 03-01 the ``/mcp`` route is declared PUBLIC in ``appinfo/info.xml``, because the
401 that starts the OAuth discovery flow has to come from this application and not from
HaRP. HaRP still signs every request with ``AUTHORIZATION-APP-API``, but the user id in it
is empty whenever the caller sent no Nextcloud credential. That gives this boundary two
branches instead of one (03-RESEARCH.md, pattern 4):

* valid handshake with a user id: the AUTH-01 path, unchanged. The ``Authorization`` header
  is not read at all, so an OAuth token can never be mistaken for that user's credential
  and a Nextcloud credential can never stand in for a missing token (D-27, no fallback in
  either direction).
* valid handshake without a user id: our own OAuth path. The bearer goes to the token
  verifier, and anything but a verified token ends the request with a 401 that carries the
  ``WWW-Authenticate`` challenge with the ``resource_metadata`` pointer.
* invalid handshake: 401 with an empty body and no hint, exactly as before (T-02-03).

The verifier is a parameter and it is still ``None`` in this plan: plan 03-06 builds the
real one on top of the token store. ``None`` is not an open door but the strictest state
this boundary has, and it is the meaning of fail-closed here: while no verifier exists, no
bearer is valid, and every anonymous caller gets the discovery 401 (T-03-01).

Every rejection carries ``Cache-Control: no-store``, like every other answer of this
package, and none of them repeats the received token in body or header (T-03-06).
"""

from collections.abc import Mapping

from mcp.server.auth.provider import TokenVerifier
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .. import config
from ..errors import ToolError
from ..oauth.metadata import PRM_SUFFIX, TOOL_SCOPE
from .auth import AppApiRejected, require_appapi
from .responses import NO_STORE

__all__ = ["RequireAppApi"]

#: The scheme prefix of a bearer credential, compared case insensitively (RFC 9110 §11.1).
_BEARER_PREFIX = "bearer "

#: The challenge of the 401, minus the pointer, which is the only part that depends on the
#: deployment. Built from constants alone so no part of a request can reach a client
#: through it (T-03-06). ``scope`` names the one tool scope and never ``offline_access``,
#: which the MCP specification keeps out of both the challenge and the resource metadata.
_CHALLENGE = (
    'Bearer error="invalid_token", '
    'error_description="Authentication required", '
    f'scope="{TOOL_SCOPE}", '
    'resource_metadata="{metadata_url}"'
)


class RequireAppApi:
    """Verify the AppAPI handshake, then the bearer, before any MCP code runs."""

    def __init__(
        self,
        app: ASGIApp,
        env: Mapping[str, str] | None = None,
        *,
        token_verifier: TokenVerifier | None = None,
    ) -> None:
        self._app = app
        self._env = env
        self._token_verifier = token_verifier

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Nothing else reaches this route in this deployment, and a lifespan or
            # websocket scope has no headers to verify. Passing it through keeps the
            # wrapper transparent for the startup of the session manager.
            await self._app(scope, receive, send)
            return

        request = Request(scope)
        try:
            user = require_appapi(request, env=self._env)
        except (AppApiRejected, ToolError):
            # No detail and no WWW-Authenticate: the caller behind these headers is a
            # proxy, and every hint would only say which of the checks rejected the
            # request (T-02-03).
            response = Response(status_code=401, headers=NO_STORE)
            await response(scope, receive, send)
            return

        if not user and not await self._bearer_is_valid(request):
            response = Response(status_code=401, headers=self._unauthorized_headers())
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)

    async def _bearer_is_valid(self, request: Request) -> bool:
        """Whether this request carries a token the configured verifier accepts.

        False whenever anything is missing: no verifier, no header, a different scheme, an
        empty token, or a verifier that answered ``None``. The verifier never sees a value
        that is not a bearer credential, and the token is never written anywhere.
        """
        if self._token_verifier is None:
            return False
        header = request.headers.get("authorization") or ""
        if header[: len(_BEARER_PREFIX)].lower() != _BEARER_PREFIX:
            return False
        token = header[len(_BEARER_PREFIX) :].strip()
        if not token:
            return False
        return await self._token_verifier.verify_token(token) is not None

    def _unauthorized_headers(self) -> dict[str, str]:
        """The 401 headers of the OAuth branch: no-store plus the discovery pointer.

        The pointer is built from the configured public URL and the one path constant of
        ``oauth.metadata``, so the address in the challenge and the route that answers it
        cannot drift apart, and a forged host cannot aim a client somewhere else (T-03-02).
        """
        metadata_url = f"{config.public_url(self._env)}{PRM_SUFFIX}"
        return {**NO_STORE, "WWW-Authenticate": _CHALLENGE.format(metadata_url=metadata_url)}
