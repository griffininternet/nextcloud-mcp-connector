"""Notes tools: search, read and create (D-05).

The search does not use the Notes REST API, because it has no search route at all: the
routes are index, get, create, update, undo, autotitle, destroy, category, attachment and
settings. The server side search lives in the unified search provider ``notes``, which
matches title **and** content, sorts by modification date and answers in one request. Title
and excerpt come straight out of that answer, so a search over twenty hits stays one round
trip instead of twenty one.

    GET /ocs/v2.php/search/providers/notes/search?term=...&limit=...

Documented fallback, deliberately not the default: if the Notes app is installed but the
provider is missing, ``GET /notes?exclude=content`` plus a client side title match would
still find something. That path matches titles only, so it is a degraded answer and would
have to be marked as one; :func:`mcp_connector.nextcloud.clients.notes.list_notes` is the
piece it would need.

Two details keep the ids honest. The unified search entry has no ``id`` field, so the note
id is parsed out of ``resourceUrl``, and an entry whose URL does not end in a numeric note
segment is skipped rather than guessed at: a wrong id resolves to a different note, which
is worse than one missing hit (threat T-01-40). And ``resourceUrl`` is only ever parsed,
never fetched; the returned link is rebuilt from the configured base URL, so a manipulated
entry cannot point this server or its user at a foreign host (threat T-01-39).
"""

from typing import Any
from urllib.parse import urlsplit

from .. import ids
from ..errors import ToolError
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import notes as notes_client
from ..nextcloud.clients import ocs

APP = "notes"

#: The unified search provider id of the Notes app.
SEARCH_PROVIDER_PATH = "/search/providers/notes/search"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

_ID_HINT = "Use an id from notes_search, for example note:12."


async def search(clients: NcClients, query: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """Search notes by title and content and return compact hits."""
    await _ready(clients)

    term = (query or "").strip()
    if not term:
        raise ToolError(
            message="The search term is empty.",
            hint="Give at least one word; Nextcloud rejects a search without a term.",
        )
    if limit < 1 or limit > MAX_LIMIT:
        raise ToolError(
            message=f"limit must be between 1 and {MAX_LIMIT} (got {limit}).",
            hint=f"Leave it out for the default of {DEFAULT_LIMIT} hits.",
        )

    response = await ocs.ocs_get(
        clients.client,
        clients.creds,
        SEARCH_PROVIDER_PATH,
        params={"term": term, "limit": limit},
    )
    data = ocs.parse_ocs(response, what="the note search")
    entries = data.get("entries") if isinstance(data, dict) else None
    entries = entries if isinstance(entries, list) else []

    results: list[dict[str, str]] = []
    skipped = 0
    for entry in entries:
        if not isinstance(entry, dict):
            skipped += 1
            continue
        note_id = _note_id_from_resource_url(entry.get("resourceUrl"))
        if note_id is None:
            skipped += 1
            continue
        results.append(
            {
                "id": ids.encode_note(note_id),
                "title": str(entry.get("title") or ""),
                "excerpt": str(entry.get("subline") or ""),
                "url": notes_client.web_url(clients.creds, note_id),
            }
        )

    result: dict[str, Any] = {"count": len(results), "results": results}
    if skipped:
        # Named, not swallowed: the model should be able to say "some hits were unusable"
        # instead of silently reporting fewer notes than the user can see in the web UI.
        result["skipped"] = skipped
    return result


async def read(clients: NcClients, note_id: str) -> dict[str, Any]:
    """Read one note including its full content."""
    await _ready(clients)
    raw = _plain_note_id(note_id)

    note = await notes_client.get_note(clients.client, clients.creds, raw)
    stored_id = str(note.get("id", raw))
    return {
        "id": ids.encode_note(stored_id),
        "title": str(note.get("title") or ""),
        "content": str(note.get("content") or ""),
        "category": str(note.get("category") or ""),
        "modified": note.get("modified"),
        "favorite": bool(note.get("favorite")),
        "url": notes_client.web_url(clients.creds, stored_id),
    }


async def create(
    clients: NcClients, title: str, content: str, category: str | None = None
) -> dict[str, Any]:
    """Create a note and report what the server actually stored.

    Notes sanitises titles and numbers a collision, so the answer can carry a different
    title than the one that was asked for. That title is the truth and goes back
    unchanged; ``renamed`` marks the case so the model can mention it instead of telling
    the user about a note that does not exist under that name.
    """
    await _ready(clients)

    wanted = (title or "").strip()
    if not wanted:
        raise ToolError(
            message="A note needs a title.",
            hint="Give a short title, for example 'Protokoll 2026-08-14'.",
        )

    note = await notes_client.create_note(
        clients.client,
        clients.creds,
        title=wanted,
        content=content or "",
        category=(category or "").strip() or None,
    )

    stored_id = str(note.get("id", ""))
    if not stored_id:
        raise ToolError(
            message="Nextcloud created the note but reported no id.",
            hint="Look for the note in the Notes app; it was probably created.",
        )
    stored_title = str(note.get("title") or "")
    result: dict[str, Any] = {
        "id": ids.encode_note(stored_id),
        "title": stored_title,
        "category": str(note.get("category") or ""),
        "modified": note.get("modified"),
        "url": notes_client.web_url(clients.creds, stored_id),
    }
    if stored_title != wanted:
        result["renamed"] = True
    return result


async def _ready(clients: NcClients) -> None:
    """Refuse before the first Notes request when the app or its API is not there."""
    caps = await capabilities.require_app(clients, APP)
    notes_client.check_api_version(caps.notes_api_versions)


def _plain_note_id(raw: str) -> str:
    """Accept ``note:12`` and a bare ``12``; refuse an id of any other kind."""
    value = (raw or "").strip()
    if value.isdigit():
        return value

    kind, parts = ids.parse(value)
    if kind != "note":
        raise ToolError(
            message=f"{raw!r} is not a note id (it is a {kind} id).",
            hint=_ID_HINT,
        )
    note_id = parts[0]
    if not note_id.isdigit():
        raise ToolError(message=f"{raw!r} has no numeric note id.", hint=_ID_HINT)
    return note_id


def _note_id_from_resource_url(resource_url: Any) -> str | None:
    """Return the numeric note id of ``.../apps/notes/note/12``, or ``None``."""
    if not isinstance(resource_url, str) or not resource_url.strip():
        return None
    path = urlsplit(resource_url.strip()).path.rstrip("/")
    if not path:
        return None
    candidate = path.rsplit("/", 1)[-1]
    return candidate if candidate.isdigit() else None
