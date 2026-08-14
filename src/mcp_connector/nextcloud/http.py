"""One ``httpx.AsyncClient`` per event loop, plus logging hardening.

Two deliberate settings:

* ``follow_redirects=False`` - a cross-host redirect would send the Authorization header
  to a foreign target or drop it silently. A redirecting base URL is a configuration
  error and is reported as one (threat T-01-08).
* No ``auth=`` on the client - authentication is passed per request, because the HTTP
  passthrough mode changes credentials per request.
"""

import asyncio
import logging
import sys
import weakref

import httpx

USER_AGENT = "nextcloud-mcp-connector/0.1"

_clients: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, httpx.AsyncClient] = (
    weakref.WeakKeyDictionary()
)


def shared_client() -> httpx.AsyncClient:
    """Return the client bound to the running event loop, creating it on first use."""
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0, read=30.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": USER_AGENT},
        )
        _clients[loop] = client
    return client


def configure_logging(level: int = logging.INFO) -> None:
    """Send package logs to stderr and keep httpx quiet. Idempotent.

    In stdio mode stdout *is* the wire, so every record goes to stderr. ``httpx`` and
    ``httpcore`` are pinned to WARNING because their INFO and DEBUG records contain
    request URLs, and a URL is one careless change away from containing credentials.
    """
    logger = logging.getLogger("mcp_connector")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)

    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
