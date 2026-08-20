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

import httpx
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Message

__all__ = [
    "NO_STORE",
    "BodyTooLarge",
    "BodyUnreadable",
    "bounded_body",
    "bounded_response",
    "form_or_none",
    "json_response",
    "with_body",
]

#: On every answer of this package, success and rejection alike (pitfall 4, T-02-42).
NO_STORE = {"Cache-Control": "no-store"}

logger = logging.getLogger("mcp_connector.exapp.responses")


class BodyTooLarge(Exception):
    """More body arrived than the caller of :func:`bounded_body` is willing to read."""


class BodyUnreadable(Exception):
    """The body could not be read to its end, so there is nothing to decide on."""


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


async def bounded_body(request: Request, max_bytes: int) -> bytes:
    """The body, read no further than ``max_bytes``.

    The one place a size limit on a request body is implemented, because an announced
    ``Content-Length`` is the sender's claim about the body and not the body (IN-01). A
    request with ``Transfer-Encoding: chunked`` announces nothing at all, so a handler that
    reads the header and then calls ``request.body()`` or ``request.form()`` has no limit
    left on the one shape that carries no number. Both places that had such a check had that
    hole: the purge handler and the connections form.

    Raises :class:`BodyTooLarge` and :class:`BodyUnreadable` rather than answering, because
    the two callers answer differently and neither answer belongs in this module. Nothing of
    the body is ever logged here, for the reason :func:`form_or_none` gives.

    The stream is left where it stopped rather than drained: draining it is the read this
    function exists to avoid.
    """
    chunks: list[bytes] = []
    seen = 0
    try:
        async for chunk in request.stream():
            seen += len(chunk)
            if seen > max_bytes:
                raise BodyTooLarge
            chunks.append(chunk)
    except BodyTooLarge:
        raise
    except Exception as exc:
        raise BodyUnreadable from exc
    return b"".join(chunks)


async def bounded_response(response: httpx.Response, max_bytes: int) -> bytes:
    """The body of an answer this process asked for, read no further than ``max_bytes``.

    The twin of :func:`bounded_body` on the response side, and it lives in this module for
    the reason the module docstring gives: this is the one place a size limit is
    implemented, and two size limits in two modules are exactly the copy this module once
    removed. Its caller is the outbound fetch of a client id metadata document
    (``oauth/cimd.py``, plan 06-02), where the body belongs to a foreign server and is
    therefore attacker input arriving in the other direction. That module imports this
    function and builds no limit of its own.

    The rejected alternative is ``response.text`` and a check on ``len`` afterwards: by
    then the memory is already spent, which is the same defect as trusting an announced
    ``Content-Length`` (IN-01). A host that answers a hundred megabytes to a request for a
    five kilobyte document costs nothing here, because the counter stops the read inside
    the chunk loop rather than after it.

    Raises :class:`BodyTooLarge` and :class:`BodyUnreadable` like its twin, because the
    caller answers in its own shape and that answer does not belong in this module.
    Nothing of the body is ever logged here.
    """
    chunks: list[bytes] = []
    seen = 0
    try:
        async for chunk in response.aiter_bytes():
            seen += len(chunk)
            if seen > max_bytes:
                raise BodyTooLarge
            chunks.append(chunk)
    except BodyTooLarge:
        raise
    except Exception as exc:
        raise BodyUnreadable from exc
    return b"".join(chunks)


def with_body(request: Request, raw: bytes) -> Request:
    """The same request with a body already in hand, for a parser that wants to stream it.

    :func:`bounded_body` has consumed the stream by the time a caller knows the body is
    small enough to parse, and ``Request.form()`` wants to read one. So it gets a request
    over the same scope whose stream is these bytes and nothing more. The scope carries the
    identity, the headers and the content type, so the parser sees exactly what it saw
    before; what it cannot do any more is read further than the limit allowed.
    """

    async def replay() -> Message:
        return {"type": "http.request", "body": raw, "more_body": False}

    return Request(request.scope, replay)


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
