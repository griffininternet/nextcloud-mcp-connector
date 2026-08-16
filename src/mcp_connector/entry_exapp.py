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
from .oauth import throttle
from .oauth.connect import connect_routes
from .oauth.consent import consent_routes
from .oauth.metadata import metadata_routes
from .oauth.provider import NextcloudOAuthProvider, auth_routes
from .oauth.registry import client_policy
from .oauth.store import store_opener
from .oauth.verifier import StoreTokenVerifier
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
    # One policy, one store and one provider for the whole application, built before the
    # transport boundary because the boundary needs the verifier that shares them: a
    # revocation has to be visible to the endpoint that issued the token and to the check
    # that lets it act, and two objects with two stores would be two answers to one
    # question.
    policy = client_policy(env)
    store = store_opener(env)
    provider = NextcloudOAuthProvider(env=env, policy=policy, store_provider=store)
    verifier = StoreTokenVerifier(store_provider=store, get_client=provider.get_client, env=env)
    # The last wire of the pair, and the one that makes "revoked" mean "now": the verifier
    # answers from a five second process cache, and a revocation, whether it comes from the
    # user through /revoke or from the reuse detection of the rotation, empties it in the
    # same process instead of waiting for the window to run out (SC 4, T-03-62).
    provider.on_revocation(verifier.invalidate)
    # One throttle for the whole application, so the five path classes are five counters
    # and not five objects with five ceilings (SC 5, D-37). It never reaches the MCP route:
    # a tool call arrives with a verified bearer and is answered from the process cache,
    # and rate limiting the actual work of this server would be our own denial of service.
    counters = throttle.Throttle()
    guarded = 0
    for route in app.router.routes:
        if isinstance(route, Route) and route.path == MCP_PATH:
            route.app = RequireAppApi(route.app, env, token_verifier=verifier)
            guarded += 1
    if guarded != 1:
        raise RuntimeError(
            f"the ExApp application has {guarded} guarded {MCP_PATH} routes instead of one; "
            "the MCP transport would be served without the AppAPI handshake"
        )
    # The lifecycle routes and the three discovery documents both come from a factory and
    # are attached here, never on the shared server object. A registration on the singleton
    # would make them appear in the standalone HTTP mode of phase 1 as well, and D-23 says
    # that mode stays as it was. The metadata routes replace the measurement probe of the
    # spike (D-29, AUTH-06) with the production path of AUTH-03; they live below
    # /.well-known/, they are public by contract, and they are what the 401 of the transport
    # boundary points a client at. The onboarding routes of AUTH-02 hang here for the same
    # reason twice over: they are the browser half of this deployment mode, and a page that
    # hands out a Nextcloud credential has no business appearing in the standalone HTTP
    # server of phase 1, which has no store, no data key and no AppAPI identity (D-23, D-36).
    #
    # The authorization server of plan 03-05 joins the same line: auth_routes builds the
    # endpoints of the SDK with create_auth_routes and our own provider, and consent_routes
    # adds the authorization endpoint in front of it plus the consent screen. The same rule
    # is why the provider is not passed to the MCPServer constructor as auth_server_provider:
    # that would attach these routes to the MCP application, where the standalone mode would
    # inherit them (03-RESEARCH.md, anti patterns).
    #
    # The policy read above is what the two places that answer to it read as well: the
    # discovery document stops advertising a registration endpoint when the switch is off,
    # and the routes stop containing one (AUTH-07, D-35). One store opener serves the
    # browser onboarding, the authorization server and the token verifier, so a deployment
    # fetches its data key once and every half writes to one file.
    for route in (
        *lifecycle_routes(env),
        *metadata_routes(env, dcr_enabled=policy.dcr_enabled),
        *connect_routes(env, store_provider=store, throttle=counters),
        *auth_routes(env, provider=provider, throttle=counters),
        *consent_routes(env, provider=provider, throttle=counters),
    ):
        app.router.routes.append(route)
    return app


def _warn_when_the_host_check_is_a_trap(env: Mapping[str, str] | None = None) -> None:
    """Name the 421 trap of a docker-install daemon without HaRP at startup (IN-04).

    Behind the PHP proxy the ``Host`` header is the container name, the rebinding
    protection stays armed without ``HP_SHARED_KEY``, and the default allowlist is
    localhost. The lifecycle routes sit before the transport check, so the installation
    turns green and every ``/mcp`` request afterwards dies as a 421 that surfaces as one
    log line. The warning is skipped when the operator already made a decision: an
    allowlist is set, the shared key selects the HaRP path, or the check is disabled.
    """
    source = os.environ if env is None else env
    if (source.get(config.ENV_HP_SHARED_KEY) or "").strip():
        return
    if (source.get(config.ENV_ALLOWED_HOSTS) or "").strip():
        return
    if not config.dns_rebinding_protection(env):
        return
    logger.warning(
        "%s is not set and %s is empty. Without HaRP the Host header of every proxied "
        "request is the container name, the Host check stays armed with the localhost "
        "default, and every /mcp request will answer 421. Set %s to the host name the "
        "proxy uses for this container (docs/exapp-install.md, pitfall 5).",
        config.ENV_HP_SHARED_KEY,
        config.ENV_ALLOWED_HOSTS,
        config.ENV_ALLOWED_HOSTS,
    )


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
        # The place the OAuth store writes to, checked before the first request and not on
        # the first authorization: a missing or read only volume answers every question
        # correctly until the container restarts and then has lost every connection
        # (pitfall 12, T-03-15). The data key is not fetched here; that needs a running
        # event loop and a reachable Nextcloud, and the store asks for it when it opens.
        config.persistent_storage()
        # The public URL is what the authorization server calls itself, and the SDK refuses
        # an issuer that is not https unless it is loopback. Building the application here
        # turns that refusal into the same named exit as a missing volume, instead of into
        # a traceback in a container log.
        app = build_exapp_app()
    except ToolError as exc:
        logger.error("%s %s", exc.message, exc.hint)
        raise SystemExit(2) from None

    if (os.environ.get(config.ENV_HP_SHARED_KEY) or "").strip():
        # HaRP with the FRP tunnel: the unix socket is the transport, frpc runs beside us.
        socket_path = os.environ.get(config.ENV_HP_EXAPP_SOCK) or DEFAULT_EXAPP_SOCK
        logger.info("MCP Connector is serving as an ExApp on %s", socket_path)
        uvicorn.run(app, uds=socket_path)
        return

    _warn_when_the_host_check_is_a_trap()

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
