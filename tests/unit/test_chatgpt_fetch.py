"""Unit tests for the ChatGPT profile tool ``fetch``, all five id kinds and all failures.

``fetch`` is the one place in this server where a client supplied string decides which
resource is read, so the tests are written against that risk rather than against the happy
path. Every kind gets its own case, a wrong prefix has to be refused instead of guessed
(threat T-01-77), a ``url`` hit has to say out loud that it cannot be fetched instead of
inventing content (threat T-01-75), and a missing app has to produce the AppMissingError
sentence rather than a stack trace.

The Deck short form gets two tests of its own. One proves that the sweep finds a card whose
board and stack the search provider never reported, the other counts the HTTP calls: one
request per board and none per stack or per card, and the sweep stops at the board that
holds the card.
"""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from mcp import Client

from mcp_connector.errors import AppMissingError, ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.server import mcp
from mcp_connector.tools import chatgpt

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"
DAV_ROOT = f"{BASE}/remote.php/dav/"
FILES_ROOT = f"{BASE}/remote.php/dav/files/{USER}"
NOTES_API = f"{BASE}/index.php/apps/notes/api/v1/notes"
DECK_API = f"{BASE}/index.php/apps/deck/api/v1.0"
CALENDARS_ROOT = f"{BASE}/remote.php/dav/calendars/{USER}"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

NOTES_INSTALLED = {"api_version": ["0.2", "1.3"], "version": "6.0.1"}
DECK_INSTALLED = {"version": "1.18.3", "canCreateBoards": True, "apiVersions": ["1.0", "1.1"]}

FILE_PATH = "/Dokumente/Budget 2026.md"
FILE_CONTENT = "# Budget 2026\nStraßenbau: 1,2 Mio\n"

#: The stacks of the second board of ``deck_boards.json``, so the sweep has somewhere to
#: continue when the first board does not hold the card.
BOARD_5_STACKS: list[dict[str, Any]] = [
    {
        "id": 51,
        "title": "Ideen",
        "boardId": 5,
        "cards": [
            {
                "id": 501,
                "title": "Fähre buchen",
                "description": "Für den Betriebsausflug",
                "stackId": 51,
                "archived": False,
                "deletedAt": 0,
                "duedate": None,
            }
        ],
    }
]


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def envelope(data: Any) -> dict[str, Any]:
    return {"ocs": {"meta": {"status": "ok", "statuscode": 200, "message": "OK"}, "data": data}}


def capabilities_payload(
    *, notes: dict[str, Any] | None = None, deck: dict[str, Any] | None = None
) -> dict[str, Any]:
    section: dict[str, Any] = {"core": {}}
    if notes is not None:
        section["notes"] = notes
    if deck is not None:
        section["deck"] = deck
    return envelope({"capabilities": section})


def mock_capabilities(
    mock: respx.MockRouter,
    *,
    notes: dict[str, Any] | None = None,
    deck: dict[str, Any] | None = None,
) -> None:
    mock.get(CAPABILITIES_URL).mock(
        return_value=httpx.Response(200, json=capabilities_payload(notes=notes, deck=deck))
    )


def search_body(*, fileid: str = "4711", path: str = FILE_PATH, collection: bool = False) -> str:
    """One Multi-Status response of the fileid lookup, in the shape sabre sends it."""
    resourcetype = "<d:collection/>" if collection else ""
    href = f"/remote.php/dav/files/{USER}{path}".replace(" ", "%20")
    return f"""<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>{href}</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>{path.rsplit("/", 1)[-1]}</d:displayname>
        <d:getcontenttype>text/markdown</d:getcontenttype>
        <d:getcontentlength>27</d:getcontentlength>
        <d:resourcetype>{resourcetype}</d:resourcetype>
        <oc:fileid>{fileid}</oc:fileid>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""


EMPTY_MULTISTATUS = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"></d:multistatus>
"""


def stat_body(*, length: int, path: str = FILE_PATH, content_type: str = "text/markdown") -> str:
    href = f"/remote.php/dav/files/{USER}{path}".replace(" ", "%20")
    return f"""<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>{href}</d:href>
    <d:propstat>
      <d:prop>
        <d:getcontentlength>{length}</d:getcontentlength>
        <d:getcontenttype>{content_type}</d:getcontenttype>
        <d:getlastmodified>Thu, 14 Aug 2026 10:00:00 GMT</d:getlastmodified>
        <d:getetag>&quot;etag-1&quot;</d:getetag>
        <d:resourcetype/>
        <oc:fileid>4711</oc:fileid>
        <oc:permissions>RGDNVW</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    capabilities.clear_cache()


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def mock_file(mock: respx.MockRouter, *, content: str = FILE_CONTENT) -> None:
    body = content.encode("utf-8")
    mock.route(method="SEARCH", url=DAV_ROOT).mock(
        return_value=httpx.Response(207, text=search_body())
    )
    mock.route(method="PROPFIND", url=f"{FILES_ROOT}{FILE_PATH}").mock(
        return_value=httpx.Response(207, text=stat_body(length=len(body)))
    )
    mock.route(method="GET", url=f"{FILES_ROOT}{FILE_PATH}").mock(
        return_value=httpx.Response(200, content=body)
    )


@pytest.mark.anyio
async def test_a_file_id_is_resolved_to_a_path_and_read(clients: NcClients) -> None:
    """The search provider only reports a fileid, so the path is looked up, never guessed."""
    with respx.mock(assert_all_called=True) as mock:
        mock_file(mock)

        result = await chatgpt.fetch(clients, "file:4711")

    assert result["id"] == "file:4711"
    assert result["title"] == "Budget 2026.md"
    assert result["text"] == FILE_CONTENT
    assert result["url"] == f"{BASE}/index.php/f/4711"
    assert result["metadata"] == {
        "kind": "file",
        "path": FILE_PATH,
        "content_type": "text/markdown",
    }


@pytest.mark.anyio
async def test_a_long_file_is_cut_and_says_so_in_the_text_and_in_the_metadata(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The context window is the scarce resource here (threat T-01-79)."""
    monkeypatch.setattr(chatgpt, "MAX_TEXT_BYTES", 10)
    body = b"0123456789abcdefghij"

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="SEARCH", url=DAV_ROOT).mock(
            return_value=httpx.Response(207, text=search_body())
        )
        mock.route(method="PROPFIND", url=f"{FILES_ROOT}{FILE_PATH}").mock(
            return_value=httpx.Response(207, text=stat_body(length=len(body)))
        )
        slice_route = mock.route(method="GET", url=f"{FILES_ROOT}{FILE_PATH}").mock(
            return_value=httpx.Response(206, content=body[:10])
        )

        result = await chatgpt.fetch(clients, "file:4711")

    assert slice_route.calls[0].request.headers["Range"] == "bytes=0-9"
    assert result["text"].startswith("0123456789")
    assert "truncated" in result["text"].lower(), "a cut answer must say so inside the text"
    metadata = result["metadata"]
    assert metadata["truncated"] == "true"
    assert metadata["next_offset"] == "10"


@pytest.mark.anyio
async def test_a_file_id_that_belongs_to_no_file_is_an_error_with_a_way_out(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="SEARCH", url=DAV_ROOT).mock(
            return_value=httpx.Response(207, text=EMPTY_MULTISTATUS)
        )

        with pytest.raises(ToolError, match="4711") as excinfo:
            await chatgpt.fetch(clients, "file:4711")

    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_note_id_is_read_over_the_notes_rest_api(clients: NcClients) -> None:
    note = {
        "id": 12,
        "title": "Protokoll 2026-08-14",
        "content": "Anwesend: Anja, Khaled\nBudget beschlossen.",
        "category": "Sitzungen",
        "modified": 1755180000,
        "favorite": False,
    }
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock, notes=NOTES_INSTALLED)
        mock.get(f"{NOTES_API}/12").mock(return_value=httpx.Response(200, json=note))

        result = await chatgpt.fetch(clients, "note:12")

    assert result["id"] == "note:12"
    assert result["title"] == "Protokoll 2026-08-14"
    assert result["text"] == note["content"]
    assert result["url"] == f"{BASE}/index.php/apps/notes/note/12"
    assert result["metadata"]["kind"] == "note"
    assert result["metadata"]["category"] == "Sitzungen"


@pytest.mark.anyio
async def test_a_note_id_without_the_notes_app_gets_the_app_missing_sentence(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)

        with pytest.raises(AppMissingError, match="Notes app is not installed"):
            await chatgpt.fetch(clients, "note:12")


@pytest.mark.anyio
async def test_the_long_card_form_is_read_directly(clients: NcClients) -> None:
    card = {
        "id": 102,
        "title": "Fixtures schreiben",
        "description": "Mit echten Deck-Antworten",
        "stackId": 11,
        "duedate": "2026-09-01T10:00:00+00:00",
    }
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock, deck=DECK_INSTALLED)
        boards = mock.get(f"{DECK_API}/boards")
        mock.get(f"{DECK_API}/boards/2/stacks/11/cards/102").mock(
            return_value=httpx.Response(200, json=card)
        )

        result = await chatgpt.fetch(clients, "card:2:11:102")

    assert boards.call_count == 0, "a canonical id needs no sweep at all"
    assert result["id"] == "card:2:11:102"
    assert result["title"] == "Fixtures schreiben"
    assert result["text"] == "Mit echten Deck-Antworten"
    assert result["url"] == f"{BASE}/index.php/apps/deck/card/102"
    assert result["metadata"]["kind"] == "card"
    assert result["metadata"]["board"] == "2"
    assert result["metadata"]["stack"] == "11"
    assert result["metadata"]["duedate"] == "2026-09-01T10:00:00+00:00"


@pytest.mark.anyio
async def test_the_short_card_form_is_resolved_by_a_sweep_without_an_n_plus_one(
    clients: NcClients,
) -> None:
    """One request per board, none per stack, and the sweep stops where the card is."""
    with respx.mock(assert_all_called=False) as mock:
        mock_capabilities(mock, deck=DECK_INSTALLED)
        boards = mock.get(f"{DECK_API}/boards").mock(
            return_value=httpx.Response(200, json=fixture("deck_boards.json"))
        )
        stacks_2 = mock.get(f"{DECK_API}/boards/2/stacks").mock(
            return_value=httpx.Response(200, json=fixture("deck_stacks.json"))
        )
        stacks_5 = mock.get(f"{DECK_API}/boards/5/stacks").mock(
            return_value=httpx.Response(200, json=BOARD_5_STACKS)
        )
        cards = mock.get(url__startswith=f"{DECK_API}/boards/2/stacks/11/cards")

        result = await chatgpt.fetch(clients, "card:102")

    assert boards.call_count == 1, "the board list is fetched once"
    assert stacks_2.call_count == 1, "one request per board, and it already carries the cards"
    assert stacks_5.call_count == 0, "the sweep stops at the board that holds the card"
    assert cards.call_count == 0, "no request per card, the stacks answer already has them"

    assert result["id"] == "card:2:11:102", "the answer reports the canonical long id"
    assert result["title"] == "Fixtures schreiben"
    assert result["metadata"]["board"] == "2"
    assert result["metadata"]["stack"] == "11"


@pytest.mark.anyio
async def test_the_sweep_continues_to_the_next_board_and_reports_an_unknown_card(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock, deck=DECK_INSTALLED)
        mock.get(f"{DECK_API}/boards").mock(
            return_value=httpx.Response(200, json=fixture("deck_boards.json"))
        )
        mock.get(f"{DECK_API}/boards/2/stacks").mock(
            return_value=httpx.Response(200, json=fixture("deck_stacks.json"))
        )
        stacks_5 = mock.get(f"{DECK_API}/boards/5/stacks").mock(
            return_value=httpx.Response(200, json=BOARD_5_STACKS)
        )

        with pytest.raises(ToolError, match="999") as excinfo:
            await chatgpt.fetch(clients, "card:999")

    assert stacks_5.call_count == 1, "every board is swept before the card is declared unknown"
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_event_id_is_read_from_caldav(clients: NcClients) -> None:
    ics = (FIXTURES / "event_allday.ics").read_text(encoding="utf-8")
    with respx.mock(assert_all_called=True) as mock:
        mock.get(f"{CALENDARS_ROOT}/personal/allday.ics").mock(
            return_value=httpx.Response(200, text=ics)
        )

        result = await chatgpt.fetch(clients, "event:personal:allday.ics")

    assert result["id"] == "event:personal:allday.ics"
    assert result["title"] == "Betriebsausflug"
    assert "2026-10-24" in result["text"]
    assert "Hamburg" in result["text"]
    assert result["url"].startswith(BASE)
    assert result["metadata"]["kind"] == "event"
    assert result["metadata"]["calendar"] == "personal"
    assert result["metadata"]["start"] == "2026-10-24"


@pytest.mark.anyio
async def test_a_url_id_is_answered_honestly_instead_of_being_fetched(
    clients: NcClients,
) -> None:
    """Never fetch a url from a search entry: that is the SSRF door (threat T-01-75)."""
    target = f"{BASE}/index.php/call/abc123#message_42"
    with respx.mock(assert_all_called=False) as mock:
        any_request = mock.route()

        with pytest.raises(ToolError, match="cannot be fetched") as excinfo:
            await chatgpt.fetch(clients, f"url:{target}")

    assert any_request.call_count == 0, "not a single request may leave for a url id"
    assert target in excinfo.value.hint, "the hint hands the user the link to open"


@pytest.mark.anyio
async def test_an_unknown_prefix_is_refused_and_names_the_valid_ones(
    clients: NcClients,
) -> None:
    """Guessing a kind is how a Talk message gets read as a note (threat T-01-77)."""
    with respx.mock(assert_all_called=False) as mock:
        any_request = mock.route()

        with pytest.raises(ToolError, match="Unknown id type") as excinfo:
            await chatgpt.fetch(clients, "talk:42")

    assert any_request.call_count == 0
    for prefix in ("file:", "note:", "card:", "event:"):
        assert prefix in excinfo.value.hint


@pytest.mark.anyio
async def test_an_empty_id_is_refused(clients: NcClients) -> None:
    with respx.mock(assert_all_called=False) as mock:
        any_request = mock.route()

        with pytest.raises(ToolError, match="not a valid resource id"):
            await chatgpt.fetch(clients, "   ")

    assert any_request.call_count == 0


def test_the_internal_deck_card_route_is_not_used() -> None:
    """A4 is unverified, so the sweep stays the only way (acceptance criterion of the plan)."""
    source = Path(chatgpt.__file__).read_text(encoding="utf-8")

    assert "/apps/deck/cards/" not in source


@pytest.mark.anyio
async def test_the_registered_tool_carries_an_output_schema_and_only_an_id() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "fetch" in tools, "the ChatGPT profile needs a tool named exactly fetch"
    tool = tools["fetch"]

    assert tool.output_schema is not None, "ChatGPT expects structured output here"
    assert set(tool.output_schema.get("properties", {})) == {
        "id",
        "title",
        "text",
        "url",
        "metadata",
    }

    schema = tool.input_schema
    assert set(schema.get("properties", {})) == {"id"}, "the parameter name is contract"
    assert set(schema.get("required", [])) == {"id"}

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True
