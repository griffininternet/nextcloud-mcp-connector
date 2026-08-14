"""File tools. This plan delivers the read side of the walking skeleton.

Three guards protect the model's context window and the user's data (threat T-01-13):
the path guard runs before any request, the mimetype check refuses binary content instead
of shipping base64, and the size cap turns a large file into a marked slice with a
``next_offset`` instead of a multi-megabyte answer.
"""

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
