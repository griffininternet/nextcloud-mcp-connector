"""WebDAV client, read side only: PROPFIND with Depth 0 and GET with an optional Range.

This module intentionally implements no write and no destructive request. The create-only
upload (PUT with ``If-None-Match: *``) arrives in plan 03, and a grep test in the contract
suite keeps every other HTTP method out of this file (TOOL-09).

Status handling follows two rules from the research: never repeat a failed
authentication (Nextcloud counts failures per source IP and slows down every user of the
server afterwards), and never let a redirect pass silently (the auth header would go to a
foreign host or vanish).
"""

from urllib.parse import quote

import httpx
from lxml import etree

from ... import config
from ...errors import ToolError
from ..credentials import Credentials
from . import xml

DAV_FILES_PREFIX = "/remote.php/dav/files/"

_STAT_PROPS = (
    f"{{{xml.DAV}}}getcontentlength",
    f"{{{xml.DAV}}}getcontenttype",
    f"{{{xml.DAV}}}getlastmodified",
    f"{{{xml.DAV}}}getetag",
    f"{{{xml.DAV}}}resourcetype",
    f"{{{xml.OC}}}fileid",
    f"{{{xml.OC}}}permissions",
)

_PATH_HINT = (
    "Use an absolute path inside the user's own files, for example /Docs/notes.md. "
    "Parent references and backslashes are not accepted."
)


def safe_path(path: str) -> str:
    """Return a normalised absolute path or raise (threat T-01-09, path traversal).

    Runs before any request is built, so an unsafe path never reaches Nextcloud.
    """
    raw = (path or "").strip()
    if not raw:
        raise ToolError(message="No path was given.", hint=_PATH_HINT)
    if "\\" in raw:
        raise ToolError(
            message=f"The path {raw!r} contains a backslash.",
            hint=_PATH_HINT,
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in raw):
        raise ToolError(
            message="The path contains a control character.",
            hint=_PATH_HINT,
        )

    segments: list[str] = []
    for segment in raw.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            raise ToolError(
                message=f"The path {raw!r} points outside the user's files.",
                hint=_PATH_HINT,
            )
        segments.append(segment)
    return "/" + "/".join(segments)


def files_url(creds: Credentials, path: str) -> str:
    """Build the WebDAV URL of a file in the user's own home."""
    user = quote(creds.user, safe="")
    return f"{creds.base_url}{DAV_FILES_PREFIX}{user}{quote(safe_path(path), safe='/')}"


def _stat_body() -> bytes:
    """Build the PROPFIND body with lxml; never with an f-string (threat T-01-11)."""
    root = etree.Element(
        f"{{{xml.DAV}}}propfind",
        nsmap={"d": xml.DAV, "oc": xml.OC, "nc": xml.NC},
    )
    prop = etree.SubElement(root, f"{{{xml.DAV}}}prop")
    for name in _STAT_PROPS:
        etree.SubElement(prop, name)
    return etree.tostring(root, xml_declaration=True, encoding="utf-8")


async def stat(client: httpx.AsyncClient, creds: Credentials, path: str) -> dict:
    """Read the metadata of one entry: size, mimetype, etag, fileid, permissions."""
    target = safe_path(path)
    response = await client.request(
        "PROPFIND",
        files_url(creds, target),
        headers={"Depth": "0", "Content-Type": "application/xml"},
        content=_stat_body(),
        auth=httpx.BasicAuth(creds.user, creds.secret),
    )
    _check(response, target)

    entries = xml.parse_multistatus(response.content)
    if not entries:
        raise ToolError(
            message=f"Nextcloud returned no properties for {target}.",
            hint="Check the path in the Nextcloud web interface and try again.",
        )
    props = entries[0][1]
    resourcetype = props.get(f"{{{xml.DAV}}}resourcetype", "")
    return {
        "path": target,
        "size": int(props.get(f"{{{xml.DAV}}}getcontentlength") or 0),
        "content_type": props.get(f"{{{xml.DAV}}}getcontenttype", ""),
        "last_modified": props.get(f"{{{xml.DAV}}}getlastmodified", ""),
        "etag": props.get(f"{{{xml.DAV}}}getetag", ""),
        "fileid": props.get(f"{{{xml.OC}}}fileid", ""),
        "permissions": props.get(f"{{{xml.OC}}}permissions", ""),
        "is_collection": f"{{{xml.DAV}}}collection" in resourcetype,
    }


async def get_range(
    client: httpx.AsyncClient,
    creds: Credentials,
    path: str,
    offset: int = 0,
    limit: int | None = None,
) -> bytes:
    """GET a file, optionally only the byte window ``[offset, offset+limit)``."""
    target = safe_path(path)
    headers: dict[str, str] = {}
    if offset > 0 or limit is not None:
        end = "" if limit is None else str(offset + limit - 1)
        headers["Range"] = f"bytes={offset}-{end}"

    response = await client.get(
        files_url(creds, target),
        headers=headers,
        auth=httpx.BasicAuth(creds.user, creds.secret),
    )
    _check(response, target)
    return response.content


def _check(response: httpx.Response, path: str) -> None:
    """Translate a Nextcloud status into message plus hint. No retry, ever."""
    status = response.status_code
    if status in (200, 206, 207):
        return
    if 300 <= status < 400:
        raise ToolError(
            message=f"Nextcloud answered the request for {path} with a redirect ({status}).",
            hint=config.REDIRECT_HINT,
        )
    if status == 401:
        raise ToolError(
            message="Nextcloud rejected the app password.",
            hint=(
                "Generate a new app password in Nextcloud under Settings, Security, "
                "Devices and sessions, then restart the MCP server."
            ),
        )
    if status == 403:
        raise ToolError(
            message=f"No permission to read {path}.",
            hint="Ask the owner of the share for read permission in Nextcloud.",
        )
    if status == 404:
        raise ToolError(
            message=f"File not found: {path}.",
            hint="List the parent folder first to get the exact spelling of the path.",
        )
    if status == 416:
        raise ToolError(
            message=f"The requested byte range of {path} is not available.",
            hint="Read the file again from offset 0 and follow next_offset.",
        )
    if status == 429:
        raise ToolError(
            message="Nextcloud is rate limiting this server.",
            hint="Wait about a minute before the next call; do not repeat it immediately.",
        )
    if status >= 500:
        raise ToolError(
            message=f"Nextcloud reported a server error ({status}) for {path}.",
            hint="This is a problem on the Nextcloud side. Retry later or check its log.",
        )
    raise ToolError(
        message=f"Nextcloud answered with an unexpected status {status} for {path}.",
        hint="Retry once; if it persists, check the Nextcloud log for that request.",
    )
