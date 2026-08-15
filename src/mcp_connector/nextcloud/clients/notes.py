"""Notes REST v1 client: list, read and create, and nothing else.

The API lives at ``/index.php/apps/notes/api/v1`` and is an ordinary app route, not an OCS
route: the answer is the bare object and a failure is ``{"status": 4xx, "message": "..."}``,
which is why every response here goes through :func:`ocs.parse_app_json` and never through
the OCS envelope parser (pitfall 9).

``OCS-APIRequest: true`` goes out anyway, although the Notes documentation only asks for
``Accept: application/json``. It costs one header and it turns the browser login page that
an unauthenticated call would otherwise receive into a plain 401, which is the difference
between an actionable message and a parser guessing at HTML.

There is deliberately no update and no delete function. The server promise is that it
cannot overwrite or remove anything, and the cheapest way to keep a promise like that is to
never write the code that could break it (TOOL-09, threat T-01-41).
"""

from typing import Any

import httpx

from ...errors import ToolError
from ..credentials import Credentials
from . import ocs

#: Base path of the Notes REST API. The ``index.php`` is not optional on every instance.
NOTES_API_PREFIX = "/index.php/apps/notes/api/v1"

#: Web route of a single note, used for the ``url`` field of every answer.
NOTES_WEB_PREFIX = "/index.php/apps/notes/note"

#: The API generation this client speaks. Notes has published 1.0 up to 1.4 within it.
SUPPORTED_API_GENERATION = "1"

_HEADERS = {"OCS-APIRequest": "true", "Accept": "application/json"}


def api_url(creds: Credentials, path: str = "") -> str:
    """Build a Notes API URL; ``path`` is empty or starts with a slash."""
    if path and not path.startswith("/"):
        raise ValueError(f"a Notes path must start with a slash (got {path!r})")
    return f"{creds.base_url}{NOTES_API_PREFIX}{path}"


def web_url(creds: Credentials, note_id: str) -> str:
    """The link a human can open. Always built from the configured base URL."""
    return f"{creds.base_url}{NOTES_WEB_PREFIX}/{note_id}"


def check_api_version(versions: tuple[str, ...]) -> None:
    """Fail early when the instance no longer speaks the v1 API (assumption A5).

    An empty tuple is accepted: some Notes releases report no ``api_version`` at all, and
    refusing to work over a missing capability field would be a false negative.
    """
    if not versions:
        return
    if any(version.split(".", 1)[0] == SUPPORTED_API_GENERATION for version in versions):
        return
    listed = ", ".join(versions)
    raise ToolError(
        message=f"This Nextcloud offers the Notes API versions {listed}, not version 1.",
        hint=(
            "This server speaks the Notes API v1. Update the connector, or ask an "
            "administrator for a Notes version that still offers v1."
        ),
    )


async def get_note(client: httpx.AsyncClient, creds: Credentials, note_id: str) -> dict[str, Any]:
    """Read one note including its content."""
    response = await client.get(
        api_url(creds, f"/notes/{note_id}"),
        headers=dict(_HEADERS),
        auth=creds.auth(),
    )
    return _as_note(ocs.parse_app_json(response, what=f"the note {note_id}"))


async def create_note(
    client: httpx.AsyncClient,
    creds: Credentials,
    *,
    title: str,
    content: str,
    category: str | None = None,
) -> dict[str, Any]:
    """Create a note and return the object the server stored, titles included."""
    body: dict[str, Any] = {"title": title, "content": content}
    if category:
        body["category"] = category

    response = await client.post(
        api_url(creds, "/notes"),
        json=body,
        headers={**_HEADERS, "Content-Type": "application/json"},
        auth=creds.auth(),
    )
    return _as_note(ocs.parse_app_json(response, what="the new note"))


def _as_note(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ToolError(
            message="Nextcloud answered with something that is not a note.",
            hint="Check that the Notes app is enabled and up to date on that instance.",
        )
    return payload
