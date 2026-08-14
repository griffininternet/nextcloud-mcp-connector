"""Unit tests for the ID codec.

The codec is the only place that builds or reads prefixed IDs. A wrong prefix would
make ``fetch`` resolve a card as a note (silently), so the roundtrip property is
pinned here for all five kinds.
"""

import pytest

from mcp_connector import ids
from mcp_connector.errors import ToolError


def test_roundtrip_for_all_five_kinds() -> None:
    cases = [
        (ids.encode_file("12345"), ("file", ("12345",))),
        (ids.encode_note("42"), ("note", ("42",))),
        (ids.encode_card("7", "13", "99"), ("card", ("7", "13", "99"))),
        (ids.encode_event("personal", "abcd-1234.ics"), ("event", ("personal", "abcd-1234.ics"))),
        (
            ids.encode_url("https://nc.test/index.php/apps/notes/note/42"),
            ("url", ("https://nc.test/index.php/apps/notes/note/42",)),
        ),
    ]
    for encoded, expected in cases:
        assert ids.parse(encoded) == expected


def test_encoded_prefixes_are_stable() -> None:
    assert ids.encode_file("1") == "file:1"
    assert ids.encode_note("1") == "note:1"
    assert ids.encode_card("1", "2", "3") == "card:1:2:3"
    assert ids.encode_event("personal", "x.ics") == "event:personal:x.ics"
    assert ids.encode_url("https://nc.test/x") == "url:https://nc.test/x"


def test_short_card_form_is_accepted() -> None:
    """Unified search only returns a cardId, without board and stack."""
    assert ids.parse("card:99") == ("card", ("99",))


def test_url_keeps_colons_and_slashes() -> None:
    kind, parts = ids.parse("url:https://nc.test:8443/index.php/apps/deck/#/board/1")
    assert kind == "url"
    assert parts == ("https://nc.test:8443/index.php/apps/deck/#/board/1",)


@pytest.mark.parametrize(
    "raw",
    [
        "garbage",
        "",
        ":",
        "file:",
        "unknown:1",
        "note:",
        "card:",
        "card:1:2",
        "card:1:2:3:4",
        "event:personal",
        "url:",
    ],
)
def test_invalid_ids_raise_toolerror_with_hint(raw: str) -> None:
    with pytest.raises(ToolError) as excinfo:
        ids.parse(raw)
    assert excinfo.value.hint, "every rejection must carry an actionable hint"


def test_encode_rejects_empty_parts() -> None:
    for call in (
        lambda: ids.encode_file(""),
        lambda: ids.encode_note(""),
        lambda: ids.encode_card("1", "", "3"),
        lambda: ids.encode_event("", "x.ics"),
        lambda: ids.encode_url(""),
    ):
        with pytest.raises(ToolError):
            call()


def test_encode_rejects_separator_inside_a_part() -> None:
    """A colon inside an id would make ``parse`` ambiguous."""
    with pytest.raises(ToolError):
        ids.encode_note("4:2")
    with pytest.raises(ToolError):
        ids.encode_event("per:sonal", "x.ics")
