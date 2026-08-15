"""ASGI entry point: the MCP server over Streamable HTTP (SRV-01, SRV-05).

Start it with::

    uv run uvicorn mcp_connector.entry_http:app --host 127.0.0.1 --port 8765

One endpoint, ``POST /mcp``, serves both protocol eras. The SDK routes each request by
its ``MCP-Protocol-Version`` header, so a 2026 client and a client on SDK 1.29 are served
from the same process without configuration, and nothing in this module tries to select
an era. That is not a convenience, it is the whole reason the class of failure behind
nextcloud/context_agent#227 cannot occur here, and ``tests/compat/test_client_matrix.py``
keeps it that way.

Two decisions worth the comment they cost:

* ``transport_security`` is the go-live gate. Without it the app answers **421
  Misdirected Request** to every Host header that is not localhost, the check runs before
  any MCP code, and the reason appears only as one line in the server log while the
  client sees a generic transport error. ``--host 0.0.0.0`` allowlists nothing: bind
  address and Host allowlist are unrelated. Hence ``NC_MCP_ALLOWED_HOSTS`` from day one.
* ``/health`` is a custom route, and custom routes are never authenticated, even when the
  rest of the server is. That is exactly right for a health probe and forbidden for
  anything else, so this module still registers exactly one. The AppAPI lifecycle routes
  of phase 2 are deliberately not registered here: ``entry_exapp.build_exapp_app``
  attaches them to its own application object, so this standalone mode stays exactly the
  server phase 1 shipped (D-23).

Not built here on purpose: mounting this app into a host application. A mounted sub-app
gets no lifespan of its own, so the host would have to enter ``mcp.session_manager.run()``
in its own lifespan or fail on the first request. The ExApp shell of phase 2 avoids that
question instead of answering it: it builds its own top level application and adds the
three lifecycle routes to it, without FastAPI and without a second framework layer
(D-24).
"""

from collections.abc import Mapping

from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__, config
from .nextcloud.http import configure_logging
from .server import mcp

__all__ = ["app", "build_app"]

configure_logging()


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Liveness probe for deployments and for the client matrix test.

    Deliberately unauthenticated and deliberately dull: status and version, no
    configuration, no host names, no mode (threat T-01-29).
    """
    return JSONResponse({"status": "ok", "version": __version__})


def build_app(env: Mapping[str, str] | None = None) -> Starlette:
    """Build the ASGI application with the host allowlist of this deployment."""
    security = TransportSecuritySettings(
        allowed_hosts=config.allowed_hosts(env),
        enable_dns_rebinding_protection=config.dns_rebinding_protection(env),
    )
    return mcp.streamable_http_app(transport_security=security)


#: The application uvicorn imports. Built from the process environment at import time.
app = build_app()
