"""The one JSON answer helper of this package, and the ``no-store`` every answer carries.

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

from typing import Any

from starlette.responses import JSONResponse

__all__ = ["NO_STORE", "json_response"]

#: On every answer of this package, success and rejection alike (pitfall 4, T-02-42).
NO_STORE = {"Cache-Control": "no-store"}


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
