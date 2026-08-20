"""The one size limit on a request body, and the request that replays what it read.

``bounded_body`` exists because an announced ``Content-Length`` is the sender's claim about
the body and not the body (IN-01). Two handlers had a check on that claim and no check at
all on a request that makes none: the purge handler read whatever arrived into memory, and
the connections form parsed it and acted on it. Both call this function now, so this file is
where the limit itself is measured, on an ASGI ``receive`` of its own.

Measured below the test client on purpose: it reads a generator body into memory itself
before the application ever runs (``httpx.Request.read`` in ``starlette.testclient``), so a
counter placed up there says nothing about this code.
"""

import asyncio
from collections.abc import Iterator
from typing import Any

import pytest
from starlette.requests import Request

from mcp_connector.exapp.responses import (
    BodyTooLarge,
    BodyUnreadable,
    bounded_body,
    form_or_none,
    with_body,
)

LIMIT = 4096

#: One POST as ASGI hands it over, with the content type of an HTML form submission.
SCOPE: dict[str, Any] = {
    "type": "http",
    "http_version": "1.1",
    "method": "POST",
    "path": "/somewhere",
    "raw_path": b"/somewhere",
    "query_string": b"",
    "root_path": "",
    "scheme": "http",
    "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
    "client": ("127.0.0.1", 1234),
    "server": ("testserver", 80),
}


def sending(
    *chunks: bytes,
    counter: list[int] | None = None,
    scope: dict[str, Any] | None = None,
) -> Request:
    """A request whose body arrives in these chunks, counting what is asked for."""
    remaining: Iterator[bytes] = iter(chunks)

    async def receive() -> dict[str, Any]:
        try:
            chunk = next(remaining)
        except StopIteration:
            return {"type": "http.request", "body": b"", "more_body": False}
        if counter is not None:
            counter.append(len(chunk))
        return {"type": "http.request", "body": chunk, "more_body": True}

    return Request(SCOPE if scope is None else scope, receive)


def test_a_body_inside_the_limit_arrives_whole() -> None:
    raw = asyncio.run(bounded_body(sending(b"a=1", b"&b=2"), LIMIT))

    assert raw == b"a=1&b=2"


def test_a_body_of_exactly_the_limit_is_still_inside_it() -> None:
    """The edge is inclusive, so a limit of n means n bytes are allowed."""
    exact = b"a" * LIMIT

    raw = asyncio.run(bounded_body(sending(exact), LIMIT))

    assert raw == exact


def test_one_byte_over_the_limit_is_refused() -> None:
    with pytest.raises(BodyTooLarge):
        asyncio.run(bounded_body(sending(b"a" * (LIMIT + 1)), LIMIT))


def test_an_empty_body_is_an_empty_answer_and_not_a_refusal() -> None:
    assert asyncio.run(bounded_body(sending(), LIMIT)) == b""


def test_the_stream_is_not_read_past_the_limit() -> None:
    """The whole point: a sender with half a megabyte left gets no further than the limit."""
    asked: list[int] = []
    chunks = tuple(b"a" * 1024 for _ in range(512))

    with pytest.raises(BodyTooLarge):
        asyncio.run(bounded_body(sending(*chunks, counter=asked), LIMIT))

    assert sum(asked) <= LIMIT + 1024, "one chunk beyond the limit, and then it stops"


def test_a_stream_that_breaks_is_its_own_refusal() -> None:
    """A body nobody could read to the end is not a small body (fail closed)."""

    async def breaks() -> dict[str, Any]:
        raise RuntimeError("the connection went away")

    with pytest.raises(BodyUnreadable):
        asyncio.run(bounded_body(Request(SCOPE, breaks), LIMIT))


def test_the_refusals_carry_nothing_of_the_body() -> None:
    """The value is user input on a public route and belongs in no message (T-05-21)."""
    secret = b"action=pause&token=the-value-nobody-may-repeat"

    with pytest.raises(BodyTooLarge) as too_large:
        asyncio.run(bounded_body(sending(secret), len(secret) - 1))

    assert "the-value-nobody-may-repeat" not in str(too_large.value)


def test_a_replayed_body_parses_as_the_form_it_was() -> None:
    """``bounded_body`` has consumed the stream, so the parser gets it back as it was."""
    request = sending(b"action=pause&token=abc")
    raw = asyncio.run(bounded_body(request, LIMIT))

    form = asyncio.run(form_or_none(with_body(request, raw)))

    assert form is not None
    assert form["action"] == "pause"
    assert form["token"] == "abc"


def test_a_replayed_body_that_is_no_form_is_still_a_refusal_and_never_an_exception() -> None:
    """HI-02 holds through the replay: a parser failure is ``None``, not a traceback."""
    scope = {**SCOPE, "headers": [(b"content-type", b"multipart/form-data; boundary=the-line")]}
    request = sending(b"this is not a multipart body", scope=scope)
    raw = asyncio.run(bounded_body(request, LIMIT))

    assert asyncio.run(form_or_none(with_body(request, raw))) is None
