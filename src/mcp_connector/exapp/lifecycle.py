"""The three endpoints AppAPI calls: ``/heartbeat``, ``/init`` and ``/enabled``.

Deliberate deviation from the research sketch, which registered these with the custom
route decorator of the shared server object: they are handed out by a factory here and
attached by ``entry_exapp`` alone. A registration on the singleton would make
``/heartbeat``, ``/init`` and ``/enabled`` appear in the standalone HTTP server of phase 1
as soon as anything imports this module, and D-23 requires that stdio and that server stay
exactly as they were. The cost is one line in ``build_exapp_app``; the benefit is that the
two phase 1 modes cannot grow a lifecycle endpoint by accident.

Three rules that come straight from the AppAPI source:

* ``/heartbeat`` authenticates nothing. Non HaRP daemons send no headers at all, and a 401
  there makes the registration run into its ten minute timeout (pitfall 10). It answers
  ``{"status": "ok"}`` and nothing else, no version, no configuration (T-02-06).
* Every answer carries ``Cache-Control: no-store``. The PHP proxy caches JSON answers for
  3600 seconds whenever the answer does not say otherwise (pitfall 4, T-02-07).
* ``x-origin-ip`` means the request came through the PHP proxy, which does not protect
  these paths and attaches valid AppAPI headers itself. Such a request is answered with
  404 as defense in depth; the primary protection is the narrow route declaration in
  ``appinfo/info.xml`` (pitfall 2, T-02-04).
"""

import logging
from collections.abc import Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from . import status
from .auth import AppApiRejected, require_appapi

__all__ = ["lifecycle_routes"]

#: The only two values AppAPI ever sends as ``?enabled=``.
ENABLED_VALUES = ("0", "1")

#: Reported once, right after a successful ``/init``. There is nothing to do in between.
INIT_PROGRESS = 100

#: Set on the proxy path, never by HaRP and never by a client that reached us directly.
HEADER_ORIGIN_IP = "x-origin-ip"

#: On every answer of this module, including the failures (pitfall 4).
_NO_STORE = {"Cache-Control": "no-store"}

logger = logging.getLogger("mcp_connector.exapp.lifecycle")


def lifecycle_routes(env: Mapping[str, str] | None = None) -> list[Route]:
    """Build the three AppAPI routes against one environment.

    The environment is a parameter for the same reason ``entry_http.build_app`` takes one:
    it lets every test build its own application without touching the process environment.
    """

    async def heartbeat(request: Request) -> Response:
        """Liveness for the AppAPI registration. Unauthenticated by contract."""
        return _json({"status": "ok"})

    async def init(request: Request) -> Response:
        """Accept the install call, then report progress 100 out of band."""
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        try:
            await status.report_init_progress(INIT_PROGRESS, env=env)
        except Exception:
            # Nothing that happens on the way to Nextcloud may turn this into a 500:
            # AppAPI aborts the whole installation on a failing /init (pitfall 3).
            logger.error("the init progress push failed, the installation may stay below 100")
        return _json({})

    async def enabled(request: Request) -> Response:
        """Confirm the enable or disable call with an empty ``error`` field."""
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        value = request.query_params.get("enabled", "")
        if value not in ENABLED_VALUES:
            return _json({"error": "enabled must be 0 or 1"}, status_code=400)
        return _json({"error": ""})

    return [
        Route("/heartbeat", heartbeat, methods=["GET"]),
        Route("/init", init, methods=["POST"]),
        Route("/enabled", enabled, methods=["PUT"]),
    ]


def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    """Return the Nextcloud user id of this request, or the response that ends it.

    A response instead of an exception, so the handlers keep one straight control flow and
    no rejection can escape as a 500.
    """
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except AppApiRejected:
        # No detail, no WWW-Authenticate: the caller is a proxy, and every hint here would
        # only tell an attacker which of the checks rejected the request (T-02-03).
        return _json({}, status_code=401)


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    """One helper for every answer, so ``no-store`` cannot be forgotten on one branch."""
    return JSONResponse(payload, status_code=status_code, headers=_NO_STORE)


def _text(body: str, status_code: int) -> Response:
    return Response(body, status_code=status_code, media_type="text/plain", headers=_NO_STORE)
