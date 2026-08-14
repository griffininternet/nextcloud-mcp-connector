"""Prefixed resource IDs, encoded and parsed in exactly one place.

``fetch`` is the only caller that has to route an ID back to a resource type, and a
malformed prefix there resolves a card as a note without any error. One codec plus a
roundtrip test makes that class of bug testable.

Formats::

    file:<fileid>
    note:<id>
    card:<boardId>:<stackId>:<cardId>      (short form card:<cardId> is accepted)
    event:<calendarUri>:<objectName>
    url:<absolute-url>                     (honest rest category, see pitfall 10)
"""

from .errors import ToolError

SEPARATOR = ":"

_HINT = (
    "Use an id exactly as returned by a search tool: file:<fileid>, note:<id>, "
    "card:<board>:<stack>:<card>, event:<calendar>:<object> or url:<absolute-url>."
)


def encode_file(fileid: str | int) -> str:
    return _join("file", str(fileid))


def encode_note(note_id: str | int) -> str:
    return _join("note", str(note_id))


def encode_card(board_id: str | int, stack_id: str | int, card_id: str | int) -> str:
    return _join("card", str(board_id), str(stack_id), str(card_id))


def encode_event(calendar_uri: str, object_name: str) -> str:
    return _join("event", calendar_uri, object_name)


def encode_url(url: str) -> str:
    """The rest category: everything we cannot address by a stable Nextcloud id."""
    value = (url or "").strip()
    if not value:
        raise ToolError(message="Cannot build an id from an empty url.", hint=_HINT)
    return f"url{SEPARATOR}{value}"


def parse(raw: str) -> tuple[str, tuple[str, ...]]:
    """Return ``(kind, parts)`` or raise :class:`ToolError` with a hint."""
    value = (raw or "").strip()
    kind, separator, rest = value.partition(SEPARATOR)
    if not separator or not kind or not rest:
        raise ToolError(message=f"{raw!r} is not a valid resource id.", hint=_HINT)

    if kind == "url":
        return "url", (rest,)
    if kind in ("file", "note"):
        parts = (rest,)
    elif kind == "card":
        parts = tuple(rest.split(SEPARATOR))
        if len(parts) not in (1, 3):
            raise ToolError(
                message=f"{raw!r} is not a valid card id.",
                hint=_HINT,
            )
    elif kind == "event":
        parts = tuple(rest.split(SEPARATOR, 1))
        if len(parts) != 2:
            raise ToolError(message=f"{raw!r} is not a valid event id.", hint=_HINT)
    else:
        raise ToolError(message=f"Unknown id type {kind!r}.", hint=_HINT)

    if any(not part.strip() for part in parts):
        raise ToolError(message=f"{raw!r} has an empty segment.", hint=_HINT)
    return kind, parts


def _join(kind: str, *parts: str) -> str:
    for part in parts:
        if not part or not part.strip():
            raise ToolError(message=f"Cannot build a {kind} id from an empty value.", hint=_HINT)
        if SEPARATOR in part:
            raise ToolError(
                message=f"A {kind} id segment must not contain {SEPARATOR!r} (got {part!r}).",
                hint="Report this as a bug: ids are built from Nextcloud values, not user input.",
            )
    return SEPARATOR.join((kind, *parts))
