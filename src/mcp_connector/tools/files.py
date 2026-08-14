"""File tools: reading text files and creating new ones.

Three guards protect the model's context window and the user's data (threat T-01-13):
the path guard runs before any request, the mimetype check refuses binary content instead
of shipping base64, and the size cap turns a large file into a marked slice with a
``next_offset`` instead of a multi-megabyte answer.

``upload`` is the only write in this package, and it can only create. Everything that
could turn it into a replace is refused before the request or by Nextcloud itself.
"""

import re

from ..errors import ToolError
from ..nextcloud import NcClients
from ..nextcloud.clients import dav

DEFAULT_MAX_BYTES = 512 * 1024
HARD_MAX_BYTES = 2 * 1024 * 1024

_TEXT_TYPES = frozenset(
    {
        "application/json",
        "application/xml",
        "application/yaml",
        "application/x-yaml",
        "application/javascript",
        "application/sql",
    }
)
_TEXT_SUFFIXES = ("+json", "+xml", "+yaml")

_SLICE_HINT = (
    "Read the file in slices: pass offset and max_bytes (at most "
    f"{HARD_MAX_BYTES} bytes) and continue at the next_offset from each answer."
)

DEFAULT_CONTENT_TYPE = "text/markdown"

# type/subtype with the token characters of RFC 9110. No parameters, no whitespace, and
# above all no control characters that could split the request header.
_CONTENT_TYPE_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]+/[A-Za-z0-9!#$%&'*+.^_`|~-]+$")

_FILE_TARGET_HINT = (
    "Give the full path of the new file, for example /Docs/meeting-notes.md. "
    "This tool writes files; it does not create folders."
)


async def read(
    clients: NcClients,
    path: str,
    offset: int = 0,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict:
    """Read a text file and return stable fields: path, content, size, content_type.

    ``truncated`` is true when the answer stops before the end of the file; only then is
    ``next_offset`` present, so the caller never has to guess whether it saw everything.
    """
    if offset < 0:
        raise ToolError(
            message=f"offset must not be negative (got {offset}).",
            hint="Start at offset 0 and follow the next_offset from each answer.",
        )
    if max_bytes < 1 or max_bytes > HARD_MAX_BYTES:
        raise ToolError(
            message=f"max_bytes must be between 1 and {HARD_MAX_BYTES} bytes (got {max_bytes}).",
            hint=_SLICE_HINT,
        )

    target = dav.safe_path(path)
    info = await dav.stat(clients.client, clients.creds, target)

    if info["is_collection"]:
        raise ToolError(
            message=f"{target} is a folder, not a file.",
            hint="Use files_list to see what is inside a folder.",
        )

    content_type = info["content_type"] or "application/octet-stream"
    if not _is_text(content_type):
        raise ToolError(
            message=f"{target} is {content_type} and not text.",
            hint="This tool returns text only. Share a link to the file instead.",
        )

    size = info["size"]
    if offset > 0 and offset >= size:
        raise ToolError(
            message=f"offset {offset} is at or past the end of {target} ({size} bytes).",
            hint="Read from a smaller offset, or stop: the file has no more content.",
        )
    if offset == 0 and size > HARD_MAX_BYTES:
        raise ToolError(
            message=(
                f"{target} is {size} bytes and too large to read in one call "
                f"(limit {HARD_MAX_BYTES} bytes)."
            ),
            hint=_SLICE_HINT,
        )

    remaining = size - offset
    if offset > 0 or remaining > max_bytes:
        data = await dav.get_range(
            clients.client,
            clients.creds,
            target,
            offset=offset,
            limit=min(max_bytes, remaining),
        )
    else:
        data = await dav.get_range(clients.client, clients.creds, target)

    content, used = _decode(data, target)
    result: dict = {
        "path": target,
        "content": content,
        "size": size,
        "content_type": content_type,
        "truncated": offset + used < size,
    }
    if result["truncated"]:
        result["next_offset"] = offset + used
    return result


async def upload(
    clients: NcClients,
    path: str,
    content: str,
    content_type: str = DEFAULT_CONTENT_TYPE,
) -> dict:
    """Create a new text file and return path, etag and ``created``.

    There is no overwrite mode and no force flag, by design (D-03, TOOL-09). If something
    already exists at the target, Nextcloud refuses the request and the caller gets a
    conflict it can act on: pick another name.
    """
    if (path or "").strip().endswith("/"):
        raise ToolError(
            message=f"{path!r} names a folder, not a file.",
            hint=_FILE_TARGET_HINT,
        )

    target = dav.safe_path(path)
    if target == "/":
        raise ToolError(
            message="The upload target is the root folder, not a file.",
            hint=_FILE_TARGET_HINT,
        )

    if not _CONTENT_TYPE_RE.match(content_type or ""):
        raise ToolError(
            message=f"{content_type!r} is not a plain mimetype.",
            hint=f"Use a bare type/subtype such as {DEFAULT_CONTENT_TYPE} or text/plain.",
        )

    try:
        data = content.encode("utf-8")
    except UnicodeEncodeError:
        raise ToolError(
            message="The content is not valid UTF-8 text.",
            hint="Send plain text; this tool does not upload binary content.",
        ) from None

    return await dav.put_new_file(clients.client, clients.creds, target, data, content_type)


def _is_text(content_type: str) -> bool:
    base = content_type.split(";", 1)[0].strip().lower()
    return (
        base.startswith("text/")
        or base in _TEXT_TYPES
        or any(base.endswith(suffix) for suffix in _TEXT_SUFFIXES)
    )


def _decode(data: bytes, path: str) -> tuple[str, int]:
    """Decode UTF-8, tolerating a multi byte character cut by the range boundary."""
    try:
        return data.decode("utf-8"), len(data)
    except UnicodeDecodeError as exc:
        tail_cut = exc.start > 0 and exc.start >= len(data) - 3
        if tail_cut:
            try:
                return data[: exc.start].decode("utf-8"), exc.start
            except UnicodeDecodeError:
                pass
        raise ToolError(
            message=f"{path} is not valid UTF-8 text.",
            hint="Nextcloud reports this file as text, but its bytes are not UTF-8.",
        ) from None
