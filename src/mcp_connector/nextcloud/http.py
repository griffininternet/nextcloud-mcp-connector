"""One ``httpx.AsyncClient`` per event loop, plus logging hardening.

Three deliberate settings:

* ``follow_redirects=False`` - a cross-host redirect would send the Authorization header
  to a foreign target or drop it silently. A redirecting base URL is a configuration
  error and is reported as one (threat T-01-08).
* No ``auth=`` on the client - authentication is passed per request, because the HTTP
  passthrough mode changes credentials per request.
* ``cookies=NoCookieJar()`` - the client is shared by every request this process serves,
  and Nextcloud answers every one of them with a session cookie. A jar on a shared client
  is therefore a session shared between users, which is the one thing this server may
  never have (see :class:`NoCookieJar`).
"""

import asyncio
import http.cookiejar
import logging
import sys
import weakref

import httpx

USER_AGENT = "nextcloud-mcp-connector/0.1"


class NoCookieJar(http.cookiejar.CookieJar):
    """A cookie jar that stores nothing and sends nothing.

    **Why this class exists, measured against a running instance (plan 03-08).** The client
    above is shared by every request of the process, and ``httpx`` clients keep cookies by
    default. Nextcloud sets ``oc<instanceid>`` and ``oc_sessionPassphrase`` on *every*
    answer, including the WebDAV and OCS answers to a request that authenticated with an
    app password. The first user of a deployment therefore left a session cookie in this
    process, every later request of every other user carried it, and Nextcloud resolved the
    session before the credentials of the request: two users of one ExApp, one identity.
    The measured symptom was a WebDAV SEARCH whose scope was ``/files/bob`` and whose
    Nextcloud user was ``alice``, which the server answered with a 500 rather than a leak,
    and it is the same defect that would have handed one user another user's data on any
    path where the scope is not part of the request.

    The AppAPI mode never showed it, because there the identity travels in a header the
    proxy validates on every single request, so a stale session cookie changes nothing.
    That is why this only surfaced when a token became the identity (plan 03-06).

    Both directions are disabled on purpose. Not sending is what fixes the bug; not storing
    is what keeps a live session out of a long lived process, where it would be one more
    credential an exception or a heap dump could carry (T-01-08).

    The guard sits in the jar and not in an ``httpx.Cookies`` subclass, because
    ``httpx.AsyncClient`` rebuilds the ``Cookies`` wrapper around whatever it is given and
    a subclass of it would be silently dropped. A ``CookieJar`` is taken as it is, so this
    is the layer where the rule actually holds.
    """

    def set_cookie(self, cookie: http.cookiejar.Cookie) -> None:
        """Keep nothing. A shared client is not a browser and has no user to remember."""

    def add_cookie_header(self, request: object) -> None:
        """Send nothing. The credentials of a request are the only identity it carries."""


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
            cookies=NoCookieJar(),
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
