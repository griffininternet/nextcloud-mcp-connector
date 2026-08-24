"""Unit tests for the Talk client, all paths, asserted on the request that was built.

Two properties of this client are contract and not implementation detail, and neither of
them is visible in a parsed answer, which is why they are tested against the URL:

*   every history URL carries the four read parameters. A read of this API writes into the
    user's own account by default (read marker, notification acknowledgement, online
    status), so the safe values are asserted positively and one by one on the query string,
    ``lookIntoFuture=0`` additionally on its own because the API has no default for it at
    all (T6, T7).
*   the continuation of a window comes out of the ``X-Chat-Last-Given`` response header and
    never out of the returned messages. The app sets that header before it drops the
    messages this account may not see, so a window can be a 200 with an empty list and a
    usable header; deriving the next page from the ids would stop there (T8).

The two API versions of the family stand below as frozen literals: conversations are v4 and
the chat is v1, and mixing the two yields a 404 out of the routing layer that reads like
"conversation not found".

The second reading route of the chat, the context around one single message, is nailed down
in its own block at the bottom of this file, because every place it could be wrong is
invisible in a parsed answer as well:

*   the route hangs on the v1 chat URL and ends in ``/context``, frozen as a literal like the
    two above it;
*   ``limit`` is in the query string and none of the four read parameters is, which is the
    counter check to the reasoned omission in the client: that route does not accept them and
    takes its freedom from side effects out of its own construction;
*   an empty context is 304, and 304 is a success with an empty window here, not the redirect
    the shared parser would report;
*   neither a token outside the declared pattern nor a message id that is not a number
    produces a single request, and the call count says so;
*   one call is exactly one request, and a refusing status stays a refusal instead of turning
    into an empty window.

The rest is the usual catalogue: the created status on the send, which is a success here and
not an unexpected answer (T1), an empty conversation without messages that answers 304, an
instance without a single conversation, a token that never reaches Nextcloud, an answer shape
that does not fit, and the absence of an ``Origin`` header on the write.
"""

import inspect
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.clients import talk as talk_client
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
TOKEN = "abcd1234"

# The frozen endpoint literals. They are the guard against mixing up the two API versions of
# one app: a route that changes its version here has to be changed on purpose.
ROOM_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v4/room"
CHAT_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v1/chat/{TOKEN}"

# The id of the one message the context tests below ask for, and the third frozen literal:
# the context of a single message is a route of the chat API, so it is derived from CHAT_URL
# and a version change of it has to be a deliberate edit here.
MESSAGE_ID = "5103"
CONTEXT_URL = f"{CHAT_URL}/{MESSAGE_ID}/context"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


SENT_MESSAGE = {
    "id": 5105,
    "token": TOKEN,
    "actorType": "users",
    "actorId": "alice",
    "actorDisplayName": "Alice Beispiel",
    "timestamp": 1755181000,
    "message": "Maße geprüft und übergeben",
    "messageParameters": {},
    "messageType": "comment",
    "systemMessage": "",
    "expirationTimestamp": 0,
    "isReplyable": True,
    "markdown": True,
    "reactions": {},
    "referenceId": "",
}


@pytest.mark.anyio
async def test_the_history_url_carries_all_four_read_parameters(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The property a parsed answer never shows: a read of this API writes by default."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CHAT_URL).mock(
            return_value=httpx.Response(
                200,
                json=envelope(fixture("talk_messages.json")),
                headers={"X-Chat-Last-Given": "5100"},
            )
        )
        await talk_client.get_messages(client, creds, TOKEN, limit=20)

    called = str(route.calls.last.request.url)
    assert "lookIntoFuture=0" in called, "mandatory in the API and 0 means history (T7)"
    assert "setReadMarker=0" in called
    assert "markNotificationsAsRead=0" in called
    assert "noStatusUpdate=1" in called
    params = route.calls.last.request.url.params
    assert params["lookIntoFuture"] == "0"
    assert params["setReadMarker"] == "0"
    assert params["markNotificationsAsRead"] == "0"
    assert params["noStatusUpdate"] == "1"


@pytest.mark.anyio
async def test_a_message_limit_above_the_maximum_is_capped_in_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Fifty messages of 32.000 characters are already more than one answer should carry."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CHAT_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("talk_messages.json")))
        )
        await talk_client.get_messages(client, creds, TOKEN, limit=500)

    assert "limit=50" in str(route.calls.last.request.url)
    assert talk_client.MAX_MESSAGES == 50


@pytest.mark.anyio
async def test_a_message_limit_below_one_is_lifted_in_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """A window of zero would read nothing and look like an empty conversation."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CHAT_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("talk_messages.json")))
        )
        await talk_client.get_messages(client, creds, TOKEN, limit=0)

    assert route.calls.last.request.url.params["limit"] == "1"


@pytest.mark.anyio
async def test_a_cursor_below_zero_becomes_zero_in_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """A negative cursor is a 400 at the app; the URL is built here and nowhere else."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CHAT_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("talk_messages.json")))
        )
        await talk_client.get_messages(client, creds, TOKEN, limit=20, last_known_message_id=-9)

    assert route.calls.last.request.url.params["lastKnownMessageId"] == "0"


@pytest.mark.anyio
async def test_an_empty_conversation_answers_304_and_is_an_empty_window(
    client: httpx.AsyncClient, creds: Credentials, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2: a fresh conversation is a success without a body, not a redirect.

    The shared parser turns every 3xx into "Nextcloud answered with a redirect, check the
    base URL", so this window has to be recognised before it gets there. The monkeypatch is
    the assertion: reaching ``parse_ocs`` at all would already be the bug.
    """

    def never(*args: object, **kwargs: object) -> object:
        raise AssertionError("a 304 must be answered before parse_ocs sees it")

    monkeypatch.setattr(ocs, "parse_ocs", never)
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CHAT_URL).mock(return_value=httpx.Response(304))
        messages, cursor = await talk_client.get_messages(client, creds, TOKEN, limit=20)

    assert messages == []
    assert cursor is None


@pytest.mark.anyio
async def test_an_empty_window_with_a_header_still_offers_a_next_page(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """T8: status 200 with no messages and a usable cursor is a real case, not a bug.

    The app sets ``X-Chat-Last-Given`` from the oldest comment it read and only afterwards
    drops the ones this account may not see or that have expired. A window whose messages
    are all invisible is therefore empty with a header, and stopping there would hide the
    older history behind it.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CHAT_URL).mock(
            return_value=httpx.Response(
                200, json=envelope([]), headers={"X-Chat-Last-Given": "4711"}
            )
        )
        messages, cursor = await talk_client.get_messages(client, creds, TOKEN, limit=20)

    assert messages == []
    assert cursor == 4711


@pytest.mark.anyio
async def test_a_full_window_returns_the_messages_and_the_cursor(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CHAT_URL).mock(
            return_value=httpx.Response(
                200,
                json=envelope(fixture("talk_messages.json")),
                headers={"X-Chat-Last-Given": "5100"},
            )
        )
        messages, cursor = await talk_client.get_messages(client, creds, TOKEN, limit=20)

    assert [message["id"] for message in messages] == [5104, 5103, 5102, 5101, 5100]
    assert cursor == 5100, "the id of the oldest message returned, out of the header"


@pytest.mark.anyio
@pytest.mark.parametrize("headers", [{}, {"X-Chat-Last-Given": "not a number"}])
async def test_a_missing_or_unreadable_cursor_header_offers_no_next_page(
    client: httpx.AsyncClient, creds: Credentials, headers: dict[str, str]
) -> None:
    """No header is the end of the history, and a header we cannot read is never guessed."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CHAT_URL).mock(
            return_value=httpx.Response(
                200, json=envelope(fixture("talk_messages.json")), headers=headers
            )
        )
        messages, cursor = await talk_client.get_messages(client, creds, TOKEN, limit=20)

    assert len(messages) == 5
    assert cursor is None


@pytest.mark.anyio
@pytest.mark.parametrize(("wanted", "sent"), [(True, "true"), (False, "false")])
async def test_the_conversation_list_never_asks_for_the_user_status(
    client: httpx.AsyncClient, creds: Credentials, wanted: bool, sent: str
) -> None:
    """The list carries one decision and two prohibitions, all three only visible in the URL."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ROOM_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("talk_rooms.json")))
        )
        rooms = await talk_client.get_rooms(client, creds, include_last_message=wanted)

    params = route.calls.last.request.url.params
    assert params["noStatusUpdate"] == "1"
    assert params["includeLastMessage"] == sent
    assert "includeStatus" not in params
    assert "modifiedSince" not in params
    assert [room["token"] for room in rooms][:2] == ["abcd1234", "efgh5678"]


@pytest.mark.anyio
async def test_an_account_without_a_single_conversation_is_not_an_error(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ROOM_URL).mock(return_value=httpx.Response(200, json=envelope([])))
        rooms = await talk_client.get_rooms(client, creds, include_last_message=True)

    assert rooms == []


@pytest.mark.anyio
async def test_sending_a_message_is_answered_with_the_created_status(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """T1: the send route documents the created status as its only success.

    OCS v2 writes the raw HTTP status into ``ocs.meta.statuscode`` as well, so this answer
    passes through the shared parser only because the success set carries it. Read as an
    unexpected status it would invite the model to send the message a second time.
    """
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(CHAT_URL).mock(
            return_value=httpx.Response(201, json=envelope(SENT_MESSAGE, 201, "Created"))
        )
        sent = await talk_client.send_message(
            client, creds, TOKEN, message="Maße geprüft und übergeben"
        )

    assert sent["id"] == 5105
    assert str(route.calls.last.request.url) == CHAT_URL


@pytest.mark.anyio
async def test_the_send_request_sends_json_and_never_an_origin_header(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """With an Origin present Nextcloud demands a basic reauthentication (threat T-08-09)."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(CHAT_URL).mock(
            return_value=httpx.Response(201, json=envelope(SENT_MESSAGE, 201, "Created"))
        )
        await talk_client.send_message(client, creds, TOKEN, message="Grüße an die Truppe")

    request = route.calls.last.request
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["OCS-APIRequest"] == "true"
    assert "origin" not in {key.lower() for key in request.headers}
    assert json.loads(request.content) == {"message": "Grüße an die Truppe"}


@pytest.mark.anyio
async def test_a_403_on_the_send_route_becomes_a_sentence_with_a_next_step(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The app refuses a conversation without chat permission, and it says so without a body."""
    with respx.mock(assert_all_called=True) as mock:
        mock.post(CHAT_URL).mock(
            return_value=httpx.Response(403, headers={"content-type": "text/html"}, text="")
        )
        with pytest.raises(ToolError) as excinfo:
            await talk_client.send_message(client, creds, TOKEN, message="Grüße")

    assert "No permission" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_history_answer_that_is_not_a_list_is_reported_as_such(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """An unexpected shape is a sentence plus a next step, never a TypeError."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CHAT_URL).mock(
            return_value=httpx.Response(200, json=envelope({"unexpected": True}))
        )
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_messages(client, creds, TOKEN, limit=20)

    assert "not a list of messages" in excinfo.value.message
    assert "Talk app" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("token", ["ABC", "abc", "ab-cd", "a" * 31])
async def test_a_token_outside_the_declared_pattern_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, token: str
) -> None:
    """Tokens go into the path, and an invented one is not just a 404 (threats T-09-02, T10).

    An unknown token on a single-conversation route registers a brute force attempt against
    the address of this container, which is one address for every user of the instance. So
    the guard has to refuse before anything goes out, which is what the call count asserts.
    """
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_messages(client, creds, token, limit=20)

    assert len(route.calls) == 0
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_token_outside_the_pattern_is_refused_on_the_send_path_as_well(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Both paths of the family go through the same guard, and nothing is posted."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await talk_client.send_message(client, creds, "Übergabe", message="Grüße")

    assert len(route.calls) == 0
    assert "talk_browse" in excinfo.value.hint


def test_the_web_link_is_always_built_from_the_configured_base_url() -> None:
    """SSRF boundary: the link a human opens never comes out of an answer (threat T-09-04)."""
    creds = Credentials(BASE, USER, SECRET)
    assert talk_client.web_url(creds, TOKEN) == f"{BASE}/index.php/call/{TOKEN}"
    assert talk_client.web_url(creds, TOKEN).startswith(creds.base_url)


def test_the_module_has_no_edit_remove_or_scheduled_send_path() -> None:
    """The server promise of this family, kept by not writing the code (threat T-09-03).

    ``PUT`` is not a forbidden verb in this project, so editing a message would be caught by
    no verb check at all. The list below is therefore a positive statement about the three
    path forms this module builds, and the last entry keeps the word for a message that
    notifies nobody out of the file so a gate can keep it out of the tool layer too.
    """
    source = Path(talk_client.__file__).read_text(encoding="utf-8")
    for forbidden in (
        ".put(",
        ".patch(",
        ".delete(",
        "/schedule",
        "/summarize",
        "/reminder",
        "/pin",
        "/attachment",
        "/share",
        "/read",
        "silent",
    ):
        assert forbidden not in source, f"{forbidden} has no place in a read plus send client"


def test_the_readers_take_their_limits_as_keywords_without_a_default() -> None:
    """Constructive rather than documented: an omitted decision does not compile away."""
    limit = inspect.signature(talk_client.get_messages).parameters["limit"]
    assert limit.default is inspect.Parameter.empty
    assert limit.kind is inspect.Parameter.KEYWORD_ONLY

    preview = inspect.signature(talk_client.get_rooms).parameters["include_last_message"]
    assert preview.default is inspect.Parameter.empty
    assert preview.kind is inspect.Parameter.KEYWORD_ONLY


def test_the_four_read_parameters_are_exactly_these_four_values() -> None:
    """The constant is the mitigation of T-09-01, so its content is part of the contract."""
    assert dict(talk_client.READ_ONLY_PARAMS) == {
        "lookIntoFuture": 0,
        "setReadMarker": 0,
        "markNotificationsAsRead": 0,
        "noStatusUpdate": 1,
    }


def message(message_id: int, text: str) -> dict[str, Any]:
    """One message of a context answer, reduced to the fields these tests read."""
    return {
        "id": message_id,
        "token": TOKEN,
        "actorType": "users",
        "actorId": "alice",
        "actorDisplayName": "Alice Beispiel",
        "timestamp": 1755180000 + message_id,
        "message": text,
        "messageType": "comment",
        "systemMessage": "",
    }


CONTEXT_WINDOW = [
    message(5102, "Vorher: Maße noch offen"),
    message(int(MESSAGE_ID), "Die gesuchte Nachricht, Größe geprüft"),
    message(5104, "Danach: übernommen"),
]


@pytest.mark.anyio
async def test_the_context_window_carries_the_wanted_message_itself(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The reason this route exists at all: ``includeLastKnown`` is true in the app.

    Reading history below ``messageId + 1`` with a window of one would answer the highest id
    under that bound, so a deleted or filtered target would silently become a neighbour. The
    window comes back in the order of the answer, because picking the right entry is the
    caller's job and reordering here would take that decision away.
    """
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(200, json=envelope(CONTEXT_WINDOW))
        )
        messages = await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert [entry["id"] for entry in messages] == [5102, 5103, 5104]
    assert int(MESSAGE_ID) in [entry["id"] for entry in messages]
    assert str(route.calls.last.request.url).startswith(CONTEXT_URL)


@pytest.mark.anyio
async def test_an_empty_context_answers_304_and_that_is_a_success_not_a_redirect(
    client: httpx.AsyncClient, creds: Credentials, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The unspectacular case with its own test: 304 without a body is an empty window.

    The shared parser turns every 3xx into "Nextcloud answered with a redirect, check the
    base URL", which would send the reader of a vanished message after a configuration
    problem that does not exist. The monkeypatch is the assertion: reaching ``parse_ocs`` at
    all would already be the bug.
    """

    def never(*args: object, **kwargs: object) -> object:
        raise AssertionError("a 304 must be answered before parse_ocs sees it")

    monkeypatch.setattr(ocs, "parse_ocs", never)
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CONTEXT_URL).mock(return_value=httpx.Response(304))
        messages = await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert messages == []


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [{"unexpected": True}, "a sentence instead of a window"])
async def test_a_context_answer_of_the_wrong_shape_is_refused_with_a_sentence(
    client: httpx.AsyncClient, creds: Credentials, payload: object
) -> None:
    """An unexpected shape is one sentence plus a next step, never a TypeError.

    Both forms would otherwise be read as "no messages", and an empty window is exactly the
    answer that invites a model to fill the gap itself.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CONTEXT_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert "not a list of messages" in excinfo.value.message
    assert "Talk app" in excinfo.value.hint


@pytest.mark.anyio
async def test_an_entry_that_is_not_a_message_is_dropped_and_never_invented(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The shared shape helper of this module drops entries it cannot read, as everywhere.

    A window whose only entry is unreadable therefore comes back empty, and that is the
    honest half of it: the caller in ``tools/chatgpt.py`` filters on the id it asked for and
    refuses when it is missing, so an empty window never reaches a model as a message.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(200, json=envelope(["not a message", CONTEXT_WINDOW[1]]))
        )
        messages = await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert [entry["id"] for entry in messages] == [int(MESSAGE_ID)]


@pytest.mark.anyio
@pytest.mark.parametrize("token", ["ABC", "abc", "ab cd", "../../etc", ""])
async def test_a_context_token_outside_the_pattern_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, token: str
) -> None:
    """Tokens go into the path, and an invented one is not just a 404 (threat T-11-08).

    The count is the assertion: an unknown token on a single-conversation route registers a
    brute force attempt against the address of this container, which is one address for
    every user of the instance, so the guard has to refuse before anything goes out.
    """
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_message_context(client, creds, token, MESSAGE_ID, limit=1)

    assert route.call_count == 0
    assert excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("message_id", ["abc", "-1", "", "4711abc", "٤٧"])
async def test_a_context_message_id_that_is_not_a_number_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, message_id: str
) -> None:
    """The second path segment gets the same treatment as the first one.

    The last case is an Arabic-Indic pair of digits: ``str.isdigit`` would accept it, and it
    would reach an app that declares this segment as an integer.
    """
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_message_context(client, creds, TOKEN, message_id, limit=1)

    assert route.call_count == 0
    assert "message id" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_the_context_url_carries_the_limit_and_none_of_the_read_parameters(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The counter check to the reasoned omission in the client (threat T-11-07).

    This route does not accept the four read parameters at all, and its freedom from side
    effects comes from its own construction: timeout 0, ``markNotificationsAsRead: false``
    and no read marker at all, verified in the source of spreed 24.0.4. Sending one of them
    anyway would be an argument the app answers with a 400.
    """
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(200, json=envelope(CONTEXT_WINDOW))
        )
        await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    params = route.calls.last.request.url.params
    assert params["limit"] == "1"
    assert "noStatusUpdate" not in params
    assert "lookIntoFuture" not in params
    assert "setReadMarker" not in params
    assert "markNotificationsAsRead" not in params
    assert "lastKnownMessageId" not in params


@pytest.mark.anyio
@pytest.mark.parametrize(("wanted", "sent"), [(999, "50"), (0, "1")])
async def test_a_context_limit_is_capped_and_lifted_in_the_url(
    client: httpx.AsyncClient, creds: Credentials, wanted: int, sent: str
) -> None:
    """One message may carry 32.000 characters, so the window is capped here, not asked for."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(200, json=envelope(CONTEXT_WINDOW))
        )
        await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=wanted)

    assert route.calls.last.request.url.params["limit"] == sent
    assert talk_client.MAX_MESSAGES == 50


@pytest.mark.anyio
async def test_one_context_call_is_exactly_one_request(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The guard against a second read: no follow up window, no loop (threat T-11-10)."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(200, json=envelope(CONTEXT_WINDOW))
        )
        await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert route.call_count == 1


@pytest.mark.anyio
async def test_a_403_on_the_context_route_stays_a_refusal_and_never_an_empty_window(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """A conversation without chat permission is a sentence of the shared parser (T-11-11).

    Read as an empty window it would say "that message does not exist", which is a different
    and untrue statement about somebody else's conversation.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CONTEXT_URL).mock(
            return_value=httpx.Response(403, headers={"content-type": "text/html"}, text="")
        )
        with pytest.raises(ToolError) as excinfo:
            await talk_client.get_message_context(client, creds, TOKEN, MESSAGE_ID, limit=1)

    assert "No permission" in excinfo.value.message
    assert excinfo.value.hint


def test_the_context_reader_takes_its_limit_as_a_keyword_without_a_default() -> None:
    """Same rule as the two readers above: an omitted decision does not compile away."""
    limit = inspect.signature(talk_client.get_message_context).parameters["limit"]
    assert limit.default is inspect.Parameter.empty
    assert limit.kind is inspect.Parameter.KEYWORD_ONLY
