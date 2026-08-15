"""Console script ``nc-mcp-exapp``: the MCP server as a Nextcloud ExApp (EXAPP-01).

This is the fourth operating mode of the same code base (D-23). It serves the same MCP
endpoint as ``entry_http``, plus the three AppAPI lifecycle routes, and it takes its
identity exclusively from the deploy environment the AppAPI deploy daemon injects:

``APP_ID``, ``APP_SECRET``, ``APP_VERSION`` and ``NEXTCLOUD_URL`` are set when the
container starts, together with ``APP_HOST``/``APP_PORT`` for a plain deployment or
``HP_SHARED_KEY``/``HP_EXAPP_SOCK`` behind HaRP.

This process never needs a Nextcloud account of its own. It authenticates to Nextcloud
with ``APP_SECRET`` plus the user id AppAPI puts into the incoming header, so a second
credential channel in the environment is not a convenience but the silent fallback D-27
forbids: ``main`` refuses to start when one is configured.
"""

import logging
import os
from collections.abc import Mapping

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Route

from . import config
from .errors import ToolError
from .exapp.lifecycle import lifecycle_routes
from .exapp.middleware import RequireAppApi
from .nextcloud.http import configure_logging
from .server import mcp

__all__ = ["build_exapp_app", "main"]

#: The one route of this application that carries the MCP transport.
MCP_PATH = "/mcp"

#: The socket path HaRP itself defaults to when it starts an ExApp with the FRP tunnel.
DEFAULT_EXAPP_SOCK = "/tmp/exapp.sock"  # noqa: S108 - HaRP dictates this path, not we

#: Both would authenticate a caller of this server on their own, which the ExApp mode must
#: never allow: the identity comes from AUTHORIZATION-APP-API and from nowhere else.
CONFLICTING_VARIABLES = (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD)

logger = logging.getLogger("mcp_connector.entry_exapp")


def build_exapp_app(env: Mapping[str, str] | None = None) -> Starlette:
    """Build the MCP application of this deployment and attach the lifecycle routes.

    The MCP half is built exactly like ``entry_http.build_app``. Behind HaRP the ``Host``
    header is the one of the reverse proxy, so the container image sets
    ``NC_MCP_DISABLE_DNS_REBINDING_PROTECTION``; the allowlist stays configurable for
    deployments that terminate closer to the client (the 421 of pitfall 6 in phase 1).

    The three lifecycle routes are appended here and nowhere else. Registering them on the
    shared server object would add them to the standalone HTTP mode as well, and D-23 says
    that mode stays as it was.

    The MCP route is wrapped in :class:`~mcp_connector.exapp.middleware.RequireAppApi`
    here and only here, for the same reason: the standalone HTTP mode of phase 1 has no
    AppAPI identity and must not grow an authentication it cannot satisfy (D-23). Inside
    this mode the wrapper is not optional, so a missing wrap is an error and not a
    warning: it would leave the whole JSON-RPC preamble unauthenticated (CR-01).
    """
    security = TransportSecuritySettings(
        allowed_hosts=config.allowed_hosts(env),
        enable_dns_rebinding_protection=config.dns_rebinding_protection(env),
    )
    app = mcp.streamable_http_app(transport_security=security)
    guarded = 0
    for route in app.router.routes:
        if isinstance(route, Route) and route.path == MCP_PATH:
            route.app = RequireAppApi(route.app, env)
            guarded += 1
    if guarded != 1:
        raise RuntimeError(
            f"the ExApp application has {guarded} guarded {MCP_PATH} routes instead of one; "
            "the MCP transport would be served without the AppAPI handshake"
        )
    for route in lifecycle_routes(env):
        app.router.routes.append(route)
    return app


def main() -> None:
    """Validate the deploy environment, then serve until the container stops."""
    configure_logging()

    for name in CONFLICTING_VARIABLES:
        if (os.environ.get(name) or "").strip():
            logger.error(
                "%s is set in an ExApp process. The ExApp mode takes its identity from "
                "AUTHORIZATION-APP-API only; a second credential channel would be a silent "
                "fallback (D-27). Remove the variable from the deploy environment.",
                name,
            )
            raise SystemExit(2)

    try:
        config.exapp_settings()
    except ToolError as exc:
        logger.error("%s %s", exc.message, exc.hint)
        raise SystemExit(2) from None

    app = build_exapp_app()
    if (os.environ.get(config.ENV_HP_SHARED_KEY) or "").strip():
        # HaRP with the FRP tunnel: the unix socket is the transport, frpc runs beside us.
        socket_path = os.environ.get(config.ENV_HP_EXAPP_SOCK) or DEFAULT_EXAPP_SOCK
        logger.info("MCP Connector is serving as an ExApp on %s", socket_path)
        uvicorn.run(app, uds=socket_path)
        return

    host = os.environ.get(config.ENV_APP_HOST) or "127.0.0.1"
    try:
        port = int(os.environ[config.ENV_APP_PORT])
    except (KeyError, ValueError):
        logger.error(
            "%s is not set to a port number. The AppAPI deploy daemon sets it when it "
            "starts the container; start the process with it or set %s for a HaRP daemon.",
            config.ENV_APP_PORT,
            config.ENV_HP_SHARED_KEY,
        )
        raise SystemExit(2) from None

    logger.info("MCP Connector is serving as an ExApp on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
