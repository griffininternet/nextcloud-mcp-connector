"""Stateless cursor handles for every truncated list (D-20, SRV-05).

A handle is base64url of compact JSON, and that is the whole mechanism. There is no server
side cursor table, no session and no expiry, so a restarted server continues a listing that
an older process handed out, which is exactly the property SRV-05 asks for.

The handle is deliberately **not signed**. It carries no secret and no authority: an offset
and the query it belongs to, nothing else. The credentials keep coming from the auth
channel on every single call, so a caller who edits a handle can only page through its own
data differently, never someone else's (threat T-01-33). Signing it would suggest a
guarantee that the auth channel already provides.

What a handle must never do is crash the server. Every input is treated as hostile text:
too long, not base64, not UTF-8, not JSON or not an object all end in a
:class:`~mcp_connector.errors.ToolError` with a way out.
"""

import base64
import binascii
import json
from typing import Any

from .errors import ToolError

#: A handle of this project stays far below 200 characters. The ceiling is a cheap guard
#: against a caller that pastes a whole document into the cursor parameter.
MAX_CURSOR_CHARS = 512

_HINT = (
    "Pass the value of the 'next' field from the previous answer unchanged, "
    "or leave cursor out to start from the beginning."
)


def encode_cursor(state: dict[str, Any]) -> str:
    """Turn the continuation state into one opaque, url safe token.

    ``sort_keys`` keeps the token stable for the same state, which makes the tests
    readable and the answers diffable.
    """
    blob = json.dumps(state, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    return base64.urlsafe_b64encode(blob.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Read a handle back, defensively. Never raises anything but :class:`ToolError`."""
    raw = (cursor or "").strip()
    if not raw:
        raise ToolError(message="The cursor is empty.", hint=_HINT)
    if len(raw) > MAX_CURSOR_CHARS:
        raise ToolError(
            message=f"The cursor is longer than {MAX_CURSOR_CHARS} characters.",
            hint=_HINT,
        )

    padded = raw + "=" * (-len(raw) % 4)
    try:
        blob = base64.b64decode(padded, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        raise ToolError(message="The cursor is not a valid handle.", hint=_HINT) from None

    try:
        state = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ToolError(message="The cursor does not decode to a handle.", hint=_HINT) from None

    if not isinstance(state, dict):
        raise ToolError(message="The cursor does not describe a position.", hint=_HINT)
    return state


def read_offset(state: dict[str, Any]) -> int:
    """Read the offset of a decoded handle, or raise if it is not a position."""
    offset = state.get("o")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ToolError(message="The cursor has no valid position.", hint=_HINT)
    return offset


def check_scope(state: dict[str, Any], key: str, expected: str, what: str) -> None:
    """Refuse a handle that belongs to a different query.

    Continuing a search for "budget" with the offset of a search for "invoice" would
    silently return the wrong page, and the model has no way to notice. Saying so is one
    round trip; guessing is a wrong answer.
    """
    if state.get(key) != expected:
        raise ToolError(
            message=f"This cursor belongs to a different {what}.",
            hint=f"Call the tool again without cursor to start a new {what}.",
        )
