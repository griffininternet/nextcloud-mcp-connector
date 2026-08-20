"""The ChatGPT compatibility profile: ``search`` and ``fetch`` (D-09, TOOL-07).

Two functions, and both of them are deliberately thin.

**``search`` owns no search.** It calls :func:`mcp_connector.tools.search.unified_search`
and renames its fields. A second hit source here would mean two answers to the same
question, two id schemes and two places to fix pitfall 10, so the only logic in it is the
projection onto the four names OpenAI reads.

**Every hit keeps a link.** ChatGPT renders a citation only while ``url`` is a non-empty
string, so an empty one does not degrade a hit, it removes it from the answer the user
sees. The unified search already guarantees an absolute URL on the configured instance;
the fallbacks below exist so a future provider cannot quietly take the citations away.

**``fetch`` owns no reader.** It parses the id once, through the central codec, and then
calls the tool that already knows how to read that kind. Four properties of that routing
are load bearing:

* A prefix is never guessed. An unknown one is refused with the list of the valid ones,
  because resolving a Talk message as a note is worse than any error (threat T-01-77).
* A ``url`` id is answered, not fetched. This server never requests a URL that came out of
  a search entry; that is the SSRF door and it stays shut (threat T-01-75).
* The Deck short form is resolved by a sweep over the boards and their stacks, one request
  per board. Deck's internal single card route would be one request instead, but it is
  undocumented and unverified (assumption A4), so it is not used here at all. A unit test
  greps this file for it, which is why it is described rather than spelled out.
* The sweep cache lives inside one call and nowhere else (D-20). A module level cache would
  hand the board list of one user to the next request of another.

**No text of an answer carries a marker this server did not write.** ``text`` is one field
for every kind, so the truncation note of a cut file and the content of a note or a card
land in the same place a model reads. Every one of the four readers therefore filters the
marker sequences out of the foreign text (:mod:`mcp_connector.tools.marks`), and only the
file reader writes one back in, where a slice actually ended. The rule sits on all four and
not only on the one that appends, because a note that forges the sequence frames itself
exactly the same way (BL-09, ME-03).
"""

from typing import Any

from .. import ids, provider_map
from ..errors import ToolError
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import caldav
from ..nextcloud.clients import dav as dav_client
from ..nextcloud.clients import deck as deck_client
from . import deck as deck_tools
from . import files as files_tools
from . import marks
from . import notes as notes_tools
from . import search as search_tools

DEFAULT_LIMIT = search_tools.DEFAULT_LIMIT

#: Ceiling for the text of one fetched file. The cap is the one from ``files_read``, so a
#: fetched file and a read file cost the same context (threat T-01-79).
MAX_TEXT_BYTES = files_tools.DEFAULT_MAX_BYTES

#: Marked inside the text, not only in the metadata: a model that only reads ``text`` must
#: still be able to tell a complete document from the beginning of one. Defined in
#: :mod:`mcp_connector.tools.marks` together with the filter that keeps the sequence this
#: server's own (BL-09, ME-03), and re-exported here under its own name.
TRUNCATION_NOTE = marks.TRUNCATION_NOTE

#: Month view of the Calendar app. The event itself is read over CalDAV and needs no app;
#: this link needs the Calendar web interface, which is what a human opens.
CALENDAR_WEB_PREFIX = "/index.php/apps/calendar/dayGridMonth"

_UNFETCHABLE = "This search result cannot be fetched: it belongs to an app this server cannot read."


async def search(
    clients: NcClients,
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, str]]:
    """Search the whole Nextcloud and project the hits onto the OpenAI field names.

    An empty query is refused by the unified search itself, with the hint that explains
    what a usable term looks like. Catching it here as well would only duplicate a message
    that is already right.
    """
    answer = await search_tools.unified_search(clients, query=query, limit=limit)
    return [_as_hit(clients, hit) for hit in _entries(answer)]


def _entries(answer: dict[str, Any]) -> list[dict[str, Any]]:
    results = answer.get("results")
    return [hit for hit in results if isinstance(hit, dict)] if isinstance(results, list) else []


def _as_hit(clients: NcClients, hit: dict[str, Any]) -> dict[str, str]:
    """One unified search hit as the four fields of the OpenAI contract.

    The two fallbacks are not cosmetic. A hit without a title is unreadable in a citation
    list, and the id at least names the resource; a hit without a url is not cited at all,
    and the instance root is still a page the user can open.
    """
    identifier = str(hit.get("id") or "")
    return {
        "id": identifier,
        "title": str(hit.get("title") or "") or identifier,
        "url": str(hit.get("url") or "") or clients.creds.base_url,
        "text": str(hit.get("subline") or ""),
    }


async def fetch(
    clients: NcClients, resource_id: str, *, max_bytes: int | None = None
) -> dict[str, Any]:
    """Read one search result in full and answer in the OpenAI fetch shape.

    The parameter is called ``resource_id`` inside the package and ``id`` on the wire: the
    wire name is the OpenAI contract, the Python name is not allowed to shadow a builtin.

    ``max_bytes`` exists for Python callers and is not on the wire: the registered tool has
    two parameters and keeps them (schema diet), so the ChatGPT contract is unchanged. It
    is how ``prepare_context`` reads a file for a two kilobyte excerpt without pulling the
    whole slice ceiling over the wire first (LO-06). ``None`` is the ceiling this tool
    always used, so every existing caller reads exactly what it read before. Only the file
    reader slices; for the other three kinds a document is one call and the limit has
    nothing to apply to.
    """
    kind, parts = ids.parse(resource_id)
    match kind:
        case "file":
            return await _fetch_file(clients, parts[0], max_bytes)
        case "note":
            return await _fetch_note(clients, parts[0])
        case "card":
            return await _fetch_card(clients, parts)
        case "event":
            return await _fetch_event(clients, parts[0], parts[1])
        case _:
            raise ToolError(
                message=_UNFETCHABLE,
                hint=f"Open the url in a browser to read it: {parts[0]}",
            )


async def _fetch_file(
    clients: NcClients, fileid: str, max_bytes: int | None = None
) -> dict[str, Any]:
    """Turn a file id back into a path, then read that path with the ordinary reader.

    ``MAX_TEXT_BYTES`` is read here and not bound as a default in the signature, so the
    ceiling stays one module level constant that a caller can lower and a test can lower
    for the whole module.
    """
    entry = await dav_client.find_by_fileid(clients.client, clients.creds, fileid)
    if entry is None:
        raise ToolError(
            message=f"This account has no file with the id {fileid}.",
            hint=(
                "Run search again and use the id from the fresh answer: a file id stops "
                "resolving once the file is deleted or the share is gone."
            ),
        )

    path = str(entry["path"])
    limit = MAX_TEXT_BYTES if max_bytes is None else max_bytes
    answer = await files_tools.read(clients, path=path, max_bytes=limit)

    # The document's own copy of either marker goes before this server writes one of its
    # own (BL-09, ME-03): a complete file that carries the note would claim to be cut, and
    # a cut one could point the model at an offset its author chose.
    text = marks.without_marks(str(answer["content"]))
    metadata = {"kind": "file", "path": path}
    if answer["content_type"]:
        metadata["content_type"] = str(answer["content_type"])
    if answer["truncated"]:
        offset = int(answer["next_offset"])
        text = f"{text}\n\n{TRUNCATION_NOTE.format(offset=offset)}"
        metadata["truncated"] = "true"
        metadata["next_offset"] = str(offset)

    return {
        "id": ids.encode_file(fileid),
        "title": path.rsplit("/", 1)[-1] or path,
        "text": text,
        "url": f"{clients.creds.base_url}{provider_map.FILE_WEB_PREFIX}/{fileid}",
        "metadata": metadata,
    }


async def _fetch_note(clients: NcClients, note_id: str) -> dict[str, Any]:
    """Read one note. The reader checks the Notes app itself, so a missing app is named."""
    note = await notes_tools.read(clients, note_id)

    metadata = {"kind": "note"}
    if note.get("category"):
        metadata["category"] = str(note["category"])
    if note.get("modified"):
        metadata["modified"] = str(note["modified"])

    return {
        "id": str(note["id"]),
        "title": str(note["title"]),
        "text": marks.without_marks(str(note["content"])),
        "url": str(note["url"]),
        "metadata": metadata,
    }


async def _fetch_card(clients: NcClients, parts: tuple[str, ...]) -> dict[str, Any]:
    """Read one Deck card, from the canonical triple or from the short search form."""
    await capabilities.require_app(clients, deck_tools.APP)

    if len(parts) == 3:
        board, stack, card_id = parts
        card = await deck_client.get_card(clients.client, clients.creds, board, stack, card_id)
        stack = str(card.get("stackId") or stack)
    else:
        board, stack, card = await _resolve_card(clients, parts[0])

    identifier = str(card.get("id") or (parts[2] if len(parts) == 3 else parts[0]))
    metadata = {"kind": "card", "board": board, "stack": stack}
    if card.get("duedate"):
        metadata["duedate"] = str(card["duedate"])

    return {
        "id": ids.encode_card(board, stack, identifier),
        "title": str(card.get("title") or ""),
        "text": marks.without_marks(str(card.get("description") or "")),
        "url": deck_client.web_url(clients.creds, identifier),
        "metadata": metadata,
    }


async def _resolve_card(clients: NcClients, card_id: str) -> tuple[str, str, dict[str, Any]]:
    """Find board and stack of a card the search provider reported by its id alone.

    One request for the board list plus one per board, and the walk stops at the board that
    holds the card. ``GET /boards/{id}/stacks`` already contains the cards, so there is no
    request per stack and none per card.

    ``seen`` lives for exactly this call. It is not a cache in the sense of D-20 and must
    never become one: board titles and card contents are user data.
    """
    seen: dict[str, list[dict[str, Any]]] = {}
    for board in await deck_client.get_boards(clients.client, clients.creds):
        board_id = str(board.get("id") or "")
        if not board_id or board_id in seen:
            continue
        seen[board_id] = await deck_client.get_stacks(clients.client, clients.creds, board_id)
        for stack in seen[board_id]:
            cards = stack.get("cards")
            for card in cards if isinstance(cards, list) else []:
                if isinstance(card, dict) and str(card.get("id")) == card_id:
                    owning = str(card.get("stackId") or stack.get("id") or "")
                    return board_id, owning, card

    raise ToolError(
        message=f"No card with the id {card_id} is on any board of this account.",
        hint=(
            "Call deck_browse with level=cards to get a full card id of the form "
            "card:<board>:<stack>:<card>."
        ),
    )


async def _fetch_event(clients: NcClients, calendar_uri: str, object_name: str) -> dict[str, Any]:
    """Read one calendar object and render it as the few lines that describe an event."""
    events = await caldav.get_event(clients.client, clients.creds, calendar_uri, object_name)
    if not events:
        raise ToolError(
            message=f"The calendar object {object_name} holds no event.",
            hint="Call calendar_list_events for the window you are interested in.",
        )

    event = events[0]
    start = _instant(event["start"])
    end = _instant(event["end"])

    lines = [
        str(event["summary"]),
        f"Start: {start}",
        f"End: {end}",
        f"All day: {'yes' if event['all_day'] else 'no'}",
        f"Calendar: {event['calendar']}",
    ]
    metadata = {"kind": "event", "calendar": calendar_uri, "start": start, "end": end}
    if event.get("location"):
        lines.append(f"Location: {event['location']}")
        metadata["location"] = str(event["location"])
    if event.get("uid"):
        metadata["uid"] = str(event["uid"])
    if len(events) > 1:
        # One object, several instances: the series was not expanded for a direct GET.
        metadata["instances"] = str(len(events))

    return {
        "id": ids.encode_event(calendar_uri, object_name),
        "title": str(event["summary"]),
        "text": marks.without_marks("\n".join(lines)),
        "url": f"{clients.creds.base_url}{CALENDAR_WEB_PREFIX}/{start[:10]}",
        "metadata": metadata,
    }


def _instant(value: Any) -> str:
    """An ISO 8601 string for a datetime and for a pure all day date alike."""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
