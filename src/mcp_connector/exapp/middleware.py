"""The AppAPI handshake as a transport boundary, in front of the MCP route (CR-01).

``deps.resolve_credentials`` verifies the same handshake, and it stays where it is. The
difference is what each of the two protects. The check in the credential layer is a
handler control point: it runs when a tool asks for credentials, so everything the MCP
protocol does before that (``initialize``, ``tools/list``, session allocation) was served
to an unauthenticated caller. Measured, not assumed: without this module the ExApp
application answers 200 to an ``initialize`` that carries no AppAPI header at all.

So this is a second control, not a replacement. The handler check keeps a future tool that
forgets ``resolve_clients`` from reading data, this one keeps an unauthenticated caller
from reaching MCP code in the first place.

Two deliberate decisions:

* An empty user id passes here. ``AUTHORIZATION-APP-API`` with a valid secret and no user
  is the app context AppAPI uses for its own calls; refusing data access for that case is
  the job of ``deps._credentials_from_appapi`` and stays there (T-02-12).
* Every failure answers 401 with an empty body and ``Cache-Control: no-store``, exactly
  like the lifecycle routes. A broken deploy environment (``ToolError`` out of
  ``exapp_settings``) is answered the same way instead of turning into a 500: a boundary
  that cannot decide has to refuse, and ``entry_exapp.main`` already validates the
  environment at startup, so this branch is unreachable in a deployed process.
"""

from collections.abc import Mapping

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from ..errors import ToolError
from .auth import AppApiRejected, require_appapi

__all__ = ["RequireAppApi"]

#: Same header the lifecycle routes set, and for the same reason (pitfall 4).
_NO_STORE = {"Cache-Control": "no-store"}


class RequireAppApi:
    """Verify the AppAPI handshake before any MCP code runs."""

    def __init__(self, app: ASGIApp, env: Mapping[str, str] | None = None) -> None:
        self._app = app
        self._env = env

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Nothing else reaches this route in this deployment, and a lifespan or
            # websocket scope has no headers to verify. Passing it through keeps the
            # wrapper transparent for the startup of the session manager.
            await self._app(scope, receive, send)
            return

        try:
            require_appapi(Request(scope), env=self._env)
        except (AppApiRejected, ToolError):
            # No detail and no WWW-Authenticate: the caller behind these headers is a
            # proxy, and every hint would only say which of the checks rejected the
            # request (T-02-03).
            response = Response(status_code=401, headers=_NO_STORE)
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)
