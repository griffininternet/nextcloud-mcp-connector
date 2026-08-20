"""The one size limit on a request body, its twin on the response side, and the request
that replays what it read.

``bounded_body`` exists because an announced ``Content-Length`` is the sender's claim about
the body and not the body (IN-01). Two handlers had a check on that claim and no check at
all on a request that makes none: the purge handler read whatever arrived into memory, and
the connections form parsed it and acted on it. Both call this function now, so this file is
where the limit itself is measured, on an ASGI ``receive`` of its own.

``bounded_response`` is the same limit for an answer this process asked for (plan 06-01, the
document fetch of AUTH-09, T-06-04). It is measured the same way, on a stream of its own:
nothing here opens a socket, and the counter sits in the stream so the test can say how much
of it was consumed before the refusal.

Measured below the test client on purpose: it reads a generator body into memory itself
before the application ever runs (``httpx.Request.read`` in ``starlette.testclient``), so a
counter placed up there says nothing about this code.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from starlette.requests import Request

from mcp_connector.exapp.responses import (
    BodyTooLarge,
    BodyUnreadable,
    bounded_body,
    bounded_response,
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


# --- the same limit on an answer we asked for ------------------------------------------

DOCUMENT_LIMIT = 5120


class Answering(httpx.AsyncByteStream):
    """A response body that arrives in these chunks and counts what was taken from it."""

    def __init__(self, *chunks: bytes, taken: list[int] | None = None, breaks: bool = False):
        self._chunks = chunks
        self._taken = taken
        self._breaks = breaks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        if self._breaks:
            raise RuntimeError("the connection went away")
        for chunk in self._chunks:
            if self._taken is not None:
                self._taken.append(len(chunk))
            yield chunk


def answering(
    *chunks: bytes, taken: list[int] | None = None, breaks: bool = False
) -> httpx.Response:
    """A streaming 200 whose body is these chunks, with no socket anywhere near it."""
    return httpx.Response(200, stream=Answering(*chunks, taken=taken, breaks=breaks))


def test_a_document_inside_the_limit_arrives_whole_and_byte_equal() -> None:
    payload = b'{"client_id":"https://claude.ai/oauth/claude-code-client-metadata"}'

    raw = asyncio.run(bounded_response(answering(payload[:20], payload[20:]), DOCUMENT_LIMIT))

    assert raw == payload


def test_a_document_of_exactly_the_limit_is_still_inside_it() -> None:
    """The edge is inclusive here too, so 5120 bytes are a document and not a refusal."""
    exact = b"a" * DOCUMENT_LIMIT

    raw = asyncio.run(bounded_response(answering(exact), DOCUMENT_LIMIT))

    assert raw == exact


def test_one_byte_over_the_limit_is_refused_on_the_response_side_as_well() -> None:
    with pytest.raises(BodyTooLarge):
        asyncio.run(bounded_response(answering(b"a" * (DOCUMENT_LIMIT + 1)), DOCUMENT_LIMIT))


def test_an_empty_document_is_an_empty_answer_and_not_a_refusal() -> None:
    """Empty is a decision for the caller to make, not a read that failed."""
    assert asyncio.run(bounded_response(answering(), DOCUMENT_LIMIT)) == b""


def test_the_answer_is_not_read_past_the_limit() -> None:
    """The whole point (T-06-04): a host with megabytes left gets no further than the limit.

    The chunk after the one that crosses the limit exists in the stream and is never taken,
    which is what "the refusal comes before the full read" means. A check on the finished
    body would consume all 512 kilobytes first and only then say no.
    """
    taken: list[int] = []
    chunks = tuple(b"a" * 1024 for _ in range(512))

    with pytest.raises(BodyTooLarge):
        asyncio.run(bounded_response(answering(*chunks, taken=taken), DOCUMENT_LIMIT))

    assert sum(taken) <= DOCUMENT_LIMIT + 1024, "one chunk beyond the limit, and then it stops"
    assert len(taken) < len(chunks), "the stream had more to give and was not asked for it"


def test_an_answer_that_breaks_mid_stream_is_its_own_refusal() -> None:
    """A document nobody could read to the end is not a small document (fail closed)."""
    with pytest.raises(BodyUnreadable):
        asyncio.run(bounded_response(answering(b"{", breaks=True), DOCUMENT_LIMIT))


def test_a_broken_answer_never_arrives_as_its_original_exception() -> None:
    """The caller of the fetch handles two refusals, not every error httpx can raise."""
    with pytest.raises(BodyUnreadable) as refusal:
        asyncio.run(bounded_response(answering(breaks=True), DOCUMENT_LIMIT))

    assert isinstance(refusal.value.__cause__, RuntimeError)


def test_the_refusals_of_an_answer_carry_nothing_of_the_document() -> None:
    """A foreign document is attacker input and belongs in no message (T-06-05)."""
    document = b'{"client_name":"the-value-nobody-may-repeat"}'

    with pytest.raises(BodyTooLarge) as too_large:
        asyncio.run(bounded_response(answering(document), len(document) - 1))

    assert "the-value-nobody-may-repeat" not in str(too_large.value)
