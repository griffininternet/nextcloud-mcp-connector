"""Unit tests for the stateless cursor handles (D-20, SRV-05).

The handle is the whole pagination state, so two properties matter: it survives a
roundtrip unchanged, and anything that is not a handle produces an error the model can
act on instead of a traceback (threat T-01-33).
"""

import base64
import json

import pytest

from mcp_connector.errors import ToolError
from mcp_connector.paging import MAX_CURSOR_CHARS, decode_cursor, encode_cursor


def test_roundtrip_returns_exactly_the_state() -> None:
    state = {"o": 25, "q": "budget"}
    assert decode_cursor(encode_cursor(state)) == state


def test_handle_is_url_safe_and_carries_no_padding() -> None:
    handle = encode_cursor({"o": 25, "q": "budget", "s": "/files/alice/Docs"})
    assert "=" not in handle, "padding would need escaping in a query string"
    assert "+" not in handle, "url safe alphabet only"
    assert "/" not in handle, "url safe alphabet only"


def test_special_characters_survive_the_roundtrip() -> None:
    state = {"o": 50, "q": "Jahres bericht & Anhang <ü>", "f": "/Docs/Größe"}
    assert decode_cursor(encode_cursor(state)) == state


def test_the_handle_is_readable_and_therefore_carries_no_secret() -> None:
    """It is deliberately not signed, so the test pins what may be inside it."""
    handle = encode_cursor({"o": 25, "q": "budget"})
    padded = handle + "=" * (-len(handle) % 4)
    assert json.loads(base64.urlsafe_b64decode(padded)) == {"o": 25, "q": "budget"}


@pytest.mark.parametrize(
    "cursor",
    [
        "nicht-base64",
        "",
        "   ",
        "!!!!",
        "***",
        base64.urlsafe_b64encode(b"[1,2,3]").decode().rstrip("="),
        base64.urlsafe_b64encode(b"not json at all").decode().rstrip("="),
        base64.urlsafe_b64encode("nur text".encode("utf-16")).decode().rstrip("="),
    ],
)
def test_an_invalid_handle_raises_a_toolerror_instead_of_crashing(cursor: str) -> None:
    with pytest.raises(ToolError) as excinfo:
        decode_cursor(cursor)
    assert excinfo.value.hint, "every cursor error tells the caller how to continue"


def test_an_oversized_handle_is_refused_before_decoding() -> None:
    with pytest.raises(ToolError) as excinfo:
        decode_cursor("A" * (MAX_CURSOR_CHARS + 1))
    assert str(MAX_CURSOR_CHARS) in excinfo.value.message
