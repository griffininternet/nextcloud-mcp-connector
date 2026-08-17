"""The JSON answer helper of this package, the ``no-store`` every answer carries, and the
one place a request body is turned into a form.

Until phase 3 three modules held their own copy of this constant, with the explicit reason
that ``exapp/discovery.py`` had to stay deletable in one piece: it was the measurement probe
of the discovery spike, written to be replaced rather than extended. Phase 3 replaced it
with ``oauth/metadata.py`` and deleted it, so the reason for the copies is gone and the
copies with it (03-PATTERNS.md, shared pattern 1). ``lifecycle.py``, ``middleware.py`` and
``oauth/metadata.py`` all answer through this module now.

The header is not cosmetics. ``createProxyResponse`` of the AppAPI PHP proxy calls
``cacheFor(3600)`` whenever an answer carries no ``Cache-Control`` and its content type is
exactly ``application/json`` (pitfall 4, T-02-42, T-03-03), and the metadata handlers of the
SDK set ``public, max-age=3600`` themselves. Either one would pin a discovery document with
a stale public URL, or a 401, for an hour.
"""

import logging
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import JSONResponse

__all__ = ["NO_STORE", "form_or_none", "json_response"]

#: On every answer of this package, success and rejection alike (pitfall 4, T-02-42).
NO_STORE = {"Cache-Control": "no-store"}

logger = logging.getLogger("mcp_connector.exapp.responses")


def json_response(
    payload: dict[str, Any],
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """One helper for every answer, so ``no-store`` cannot be forgotten on one branch.

    The extra headers are merged over the constant instead of replacing it (IN-06): with
    ``headers or dict(NO_STORE)`` a caller that passed a non-empty dict without
    ``Cache-Control`` silently lost ``no-store``, and the PHP proxy then cached the answer
    for 3600 seconds, which is exactly the pitfall the constant exists against. The merge
    order also lets a caller that sets ``Cache-Control`` itself win, because that is a
    decision and not an accident.
    """
    return JSONResponse(payload, status_code=status_code, headers={**NO_STORE, **(headers or {})})


async def form_or_none(request: Request) -> FormData | None:
    """The submitted form, or ``None`` when this body cannot be read as one (HI-02).

    ``Request.form()`` is not the total function every caller of it assumed. Starlette
    catches its own ``MultiPartException`` and turns it into a 400, but the parser it uses
    raises ``python_multipart.exceptions.MultipartParseError``, which is not covered by that
    and escaped into the framework: a bare ``text/plain`` 500 without ``no-store``, without
    the reference the error contract promises, and with a full traceback per request in the
    log. Every browser surface of this app said it answered a page instead, and every
    machine endpoint said it answered its own error shape.

    So the parse gets the shape everything else on these paths has: it returns a value or a
    refusal, never an exception, and the caller decides what its own refusal looks like. One
    helper rather than five copies, because the failure depends on the version of
    ``python-multipart`` and will come and go with updates.

    Nothing of the body reaches the log. It is user input on a public route, it may carry a
    credential on ``/token``, and the kind of the failure is the only thing worth recording.
    """
    try:
        return await request.form()
    except Exception:
        logger.warning("a submitted form could not be parsed")
        return None
