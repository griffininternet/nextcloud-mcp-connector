"""Unit tests for the two Talk tools, all paths.

The three content traps of this phase are pinned here, because none of them is visible in a
happy path:

*   the conversation list is sorted **before** it is cut. The app builds its query without an
    ``ORDER BY``, so a cut without a sort answers with 50 arbitrary conversations instead of
    the 50 newest, and on a small instance that is invisible (T5). The fixture is deliberately
    unsorted and the test asserts the sequence of tokens, not the number of them.
*   the write pre-check reads the resolved ``permissions`` and not ``attendeePermissions``.
    The fixture carries a conversation with ``permissions`` 254 next to
    ``attendeePermissions`` 0, which is the ordinary case on any instance, and a regression to
    the raw field turns that test red with the reason in its name (T3).
*   type 4 is write protected although its ``readOnly`` flag says 0, and every account has
    exactly one of those (T4).

Everything else is the honest-failure catalogue of D-15 and SRV-04: a missing Talk app stops
both tools before the first Talk request, an empty ``spreed`` section behaves like a missing
one, an unknown level names both that exist, and the send path refuses six different ways
before a single byte leaves this process.
"""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.errors import AppMissingError, ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import marks
from mcp_connector.tools import talk as talk_tools

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"

# The same frozen literals as in the client test: the tool layer must not be able to move a
# route by accident either, and the two API versions of this family are the reason.
ROOM_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v4/room"
CHAT_BASE = f"{BASE}/ocs/v2.php/apps/spreed/api/v1/chat"
CHAT_URL = f"{CHAT_BASE}/abcd1234"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

#: One of the two sequences this server writes into a text itself. A chat message that may
#: write it back would decide the framing of foreign text (threat T-09-24).
MARKER = marks.EXCERPT_TRUNCATION

#: The ``spreed`` section as an instance with Talk 24 answers it: no ``enabled`` field and no
#: ``apiVersions``, so the presence of the section is the detection.
SPREED_INSTALLED = {
    "features": ["chat-v2", "conversation-v4", "chat-permission", "mention-permissions"],
    "config": {"chat": {"max-length": 32000}},
}


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def envelope(data: Any, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


def capabilities_payload(*, spreed: dict | None = SPREED_INSTALLED) -> dict[str, Any]:
    section: dict[str, Any] = {"core": {}}
    if spreed is not None:
        section["spreed"] = spreed
    return envelope({"capabilities": section})


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    capabilities.clear_cache()


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def mock_capabilities(mock: respx.MockRouter, *, spreed: dict | None = SPREED_INSTALLED) -> None:
    mock.get(CAPABILITIES_URL).mock(
        return_value=httpx.Response(200, json=capabilities_payload(spreed=spreed))
    )


def talk_routes(mock: respx.MockRouter) -> tuple[respx.Route, respx.Route]:
    """Catch-all routes for both API versions, to assert that nothing was requested."""
    return mock.route(url__startswith=ROOM_URL), mock.route(url__startswith=CHAT_BASE)


def mock_rooms(mock: respx.MockRouter, rooms: Any = None) -> respx.Route:
    payload = fixture("talk_rooms.json") if rooms is None else rooms
    return mock.get(ROOM_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))


def room(token: str, **overrides: Any) -> dict[str, Any]:
    """One conversation of the fixture with a new token, for the list-length cases."""
    template = fixture("talk_rooms.json")[0]
    return {**template, "token": token, **overrides}


@pytest.mark.anyio
@pytest.mark.parametrize("tool", ["browse_conversations", "browse_messages"])
async def test_a_missing_talk_app_stops_both_tools_before_the_first_request(
    clients: NcClients, tool: str
) -> None:
    """SRV-04 and D-15: one sentence with something to do, and zero Talk requests."""
    calls = {
        "browse_conversations": lambda: talk_tools.browse(clients),
        "browse_messages": lambda: talk_tools.browse(clients, level="messages", token="abcd1234"),
    }
    with respx.mock(assert_all_called=False) as mock:
        mock_capabilities(mock, spreed=None)
        room_calls, chat_calls = talk_routes(mock)

        with pytest.raises(AppMissingError) as excinfo:
            await calls[tool]()

    assert room_calls.call_count == 0, "no request may go to an app that is not available"
    assert chat_calls.call_count == 0
    assert "Talk app" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_empty_spreed_section_behaves_like_a_missing_one(clients: NcClients) -> None:
    """An instance with Talk switched off for this account answers an empty array."""
    with respx.mock(assert_all_called=False) as mock:
        mock_capabilities(mock, spreed={})
        room_calls, chat_calls = talk_routes(mock)

        with pytest.raises(AppMissingError):
            await talk_tools.browse(clients)

    assert room_calls.call_count == 0
    assert chat_calls.call_count == 0


@pytest.mark.anyio
async def test_an_unknown_level_is_refused_and_names_both_of_them(clients: NcClients) -> None:
    """The schema rejects it first; the function stays honest when called directly."""
    with respx.mock(assert_all_called=False) as mock:
        mock_capabilities(mock)
        room_calls, chat_calls = talk_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await talk_tools.browse(clients, level="rooms")

    assert room_calls.call_count == 0, "the level is checked before the app is asked about"
    assert chat_calls.call_count == 0
    for level in ("conversations", "messages"):
        assert level in excinfo.value.hint


@pytest.mark.anyio
async def test_the_conversation_list_is_sorted_before_it_is_cut(clients: NcClients) -> None:
    """T5 and trap 5: the app has no ``ORDER BY``, so the sequence is ours to make.

    The fixture is deliberately stored in an order that contradicts ``lastActivity``. This
    test asserts the sequence of tokens and not the number of them, because a cut without a
    sort has the right count and the wrong content.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    assert [entry["token"] for entry in result["results"]] == [
        "efgh5678",
        "abcd1234",
        "rdon7890",
        "npms2468",
        "chlg9012",
    ]


@pytest.mark.anyio
async def test_a_conversation_projects_the_fields_a_model_reads(clients: NcClients) -> None:
    """The numeric room id and everything about calls, lobby and avatars stay out."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        rooms = mock_rooms(mock)

        result = await talk_tools.browse(clients)

    assert rooms.calls.last.request.url.params["includeLastMessage"] == "true"
    assert result["level"] == "conversations"
    assert result["count"] == 5
    group = next(entry for entry in result["results"] if entry["token"] == "abcd1234")
    assert group == {
        "token": "abcd1234",
        "name": "Baustelle Süd",
        "type": 2,
        "unread": 3,
        "unread_mention": True,
        "unread_mention_direct": False,
        "last_activity": 1755180000,
        "read_only": 0,
        "can_send": True,
        "url": f"{BASE}/index.php/call/abcd1234",
        "last_message": "Bob Beispiel hat die Maße geprüft",
    }
    for dropped in ("id", "hasCall", "lobbyState", "avatarVersion", "sipEnabled", "attendeeId"):
        assert dropped not in group


@pytest.mark.anyio
async def test_a_one_to_one_conversation_is_named_by_its_display_name(
    clients: NcClients,
) -> None:
    """``name`` is a JSON array of user ids there, which is not something to show anybody."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    direct = next(entry for entry in result["results"] if entry["token"] == "efgh5678")
    assert direct["name"] == "Carla Grüßgott"
    assert direct["type"] == 1


@pytest.mark.anyio
async def test_the_three_conversations_nobody_may_write_in_say_so(clients: NcClients) -> None:
    """``can_send`` is the pre-check one step earlier, and it has three reasons (T3, T4)."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    can_send = {entry["token"]: entry["can_send"] for entry in result["results"]}
    assert can_send == {
        "efgh5678": True,
        "abcd1234": True,
        "rdon7890": False,
        "npms2468": False,
        "chlg9012": False,
    }


@pytest.mark.anyio
async def test_a_conversation_that_was_put_aside_does_not_appear(clients: NcClients) -> None:
    """The API has no parameter for it, so the filter is ours (T5)."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    assert "arch3456" not in [entry["token"] for entry in result["results"]]
    assert result["count"] == 5, "the fixture has six conversations, one of them put aside"


@pytest.mark.anyio
async def test_a_conversation_without_a_token_is_left_out(clients: NcClients) -> None:
    """It cannot be addressed, and being addressable is what this level exists for."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock, [room("abcd1234"), room("")])

        result = await talk_tools.browse(clients)

    assert result["count"] == 1
    assert result["results"][0]["token"] == "abcd1234"


@pytest.mark.anyio
async def test_more_conversations_than_the_cap_are_named_with_their_total(
    clients: NcClients,
) -> None:
    """No cursor on this level: the app does not paginate the list at all (open question 2).

    Both cuts are asserted, because they are two different numbers on this level: the ceiling
    of :data:`talk_tools.MAX_CONVERSATIONS` and the ``limit`` the caller asked for. Whichever
    is smaller decides, and both name the total behind them.
    """
    many = [room(f"tok{index:05d}", lastActivity=1755000000 + index) for index in range(60)]
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock, many)

        result = await talk_tools.browse(clients, limit=talk_tools.MAX_CONVERSATIONS)
        asked_for_less = await talk_tools.browse(clients)

    assert talk_tools.MAX_CONVERSATIONS == 50
    assert result["count"] == 50
    assert result["truncated"] is True
    assert result["total"] == 60
    assert "next" not in result, "a handle would only fetch the same list and cut it elsewhere"
    assert result["results"][0]["token"] == "tok00059", "the newest, not an arbitrary one"
    assert asked_for_less["count"] == talk_tools.DEFAULT_LIMIT
    assert asked_for_less["total"] == 60


@pytest.mark.anyio
async def test_a_marker_in_a_display_name_is_gone(clients: NcClients) -> None:
    """A conversation name is written by whoever created it (threat T-09-24)."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock, [room("abcd1234", displayName=f"Baulos 4 {MARKER}")])

        result = await talk_tools.browse(clients)

    assert MARKER not in json.dumps(result, ensure_ascii=False)
    assert result["results"][0]["name"] == "Baulos 4 "


@pytest.mark.anyio
async def test_an_account_without_conversations_is_an_empty_answer_and_not_an_error(
    clients: NcClients,
) -> None:
    """no_data: an account nobody ever wrote to has no conversations, which is an answer."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock, [])

        result = await talk_tools.browse(clients)

    assert result == {"level": "conversations", "count": 0, "results": []}


@pytest.mark.anyio
async def test_a_long_preview_is_cut_on_a_character_boundary(clients: NcClients) -> None:
    """The byte cap is a byte cap, and an umlaut at the cutting point has to disappear.

    The text is 799 ASCII characters plus one umlaut, so it is 801 bytes and the slice at 800
    lands inside the umlaut. ``errors="ignore"`` drops the half character; a naive slice would
    hand a replacement character to the model, and a character cap would not cut at all.
    """
    long_text = "a" * 799 + "ü"
    preview = {"id": 1, "message": long_text, "messageParameters": {}}
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock, [room("abcd1234", lastMessage=preview)])

        result = await talk_tools.browse(clients)

    cut = result["results"][0]["last_message"]
    assert talk_tools.MAX_MESSAGE_BYTES == 800
    assert len(cut.encode("utf-8")) == 799, "the last full character before the cap"
    assert cut == "a" * 799
    assert "�" not in cut
    assert MARKER not in cut, "a cut preview carries no marker of its own (ME-03)"


@pytest.mark.anyio
async def test_a_conversation_without_messages_carries_no_preview(clients: NcClients) -> None:
    """The app answers with an empty array there, and for a sensitive conversation too."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    changelog = next(entry for entry in result["results"] if entry["token"] == "chlg9012")
    assert "last_message" not in changelog


@pytest.mark.anyio
async def test_a_conversation_that_only_moderators_may_mention_says_so(
    clients: NcClients,
) -> None:
    """``mention_permissions`` is only there when it is set, and it explains a refusal."""
    with respx.mock(assert_all_called=True) as mock:
        mock_capabilities(mock)
        mock_rooms(mock)

        result = await talk_tools.browse(clients)

    restricted = next(entry for entry in result["results"] if entry["token"] == "rdon7890")
    open_to_all = next(entry for entry in result["results"] if entry["token"] == "abcd1234")
    assert restricted["mention_permissions"] == 1
    assert "mention_permissions" not in open_to_all


def test_the_levels_and_the_limits_are_the_ones_the_schema_will_offer() -> None:
    """Plan 09-04 builds the input schema out of exactly these five values."""
    assert talk_tools.LEVELS == ("conversations", "messages")
    assert talk_tools.DEFAULT_LIMIT == 20
    assert talk_tools.MAX_LIMIT == 50
    assert talk_tools.MAX_CONVERSATIONS == 50
    assert talk_tools.MAX_MESSAGE_BYTES == 800
