"""Talk round trip against a real Nextcloud 34 with the Talk app (opt-in).

The unit tests of plan 09-01 and 09-03 pin the shapes and the outgoing request. This file
measures the one promise that cannot be proven that way: **a read leaves nothing behind**.
Success criterion 3 of this phase says it literally, and the unit layer can only hold that
the four parameters stand in our own URL. The consequence is what matters, so it is measured
here, live and on the same conversation: the read marker, both unread counters and the read
state other participants can see are compared before and after one history read. Those four
fields are the whole observable surface of the three side effects those parameters switch
off (T6, layer 2). There is no repair path either: removing a read marker means
``DELETE chat/{token}/read``, which the destructive gate of this project forbids, so the
property has to be measured rather than fixed afterwards.

Three more things only a running instance answers. A conversation nobody ever wrote into
answers with an empty history and not with a hint about a wrong base URL (T2 together with
T12, where the unread counter of that very conversation can be 1 while its history is
empty). A message really arrives and is really found again under its own wording, umlauts
included. And a token that stands in no conversation list of this account is refused by our
own sentence, without Nextcloud ever seeing it in a path: an unknown token on a single
conversation route counts as a brute force attempt against the address of this whole
container, which is one address for every user of the instance (T10).

The two test conversations are scaffolding, not connector features: a conversation is not
something this server can create (create-only, threat T-09-03), so ``scripts/
bootstrap_exapp.sh`` and ``scripts/bootstrap_test_nc.sh`` build them with ``occ`` and publish
their names in the connection file. A missing app, a missing conversation or a switched off
send therefore skips with the precondition named: an account without scaffolding says nothing
about the connector, and turning that into a red test would blame the wrong side.

The changelog conversation (type 4) is deliberately never a target here. Talk creates it for
every account, it is write protected whatever its ``readOnly`` flag says, and it is often the
only conversation of a fresh test account, which makes it the most plausible wrong pick of
all. The fixture below asserts that the writable conversation is not that one.

Run it against either topology::

    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a
    uv run pytest tests/integration/test_talk_roundtrip.py -m integration -q -rA

    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_talk_roundtrip.py -m integration -q -rA
"""

import os
import time
import uuid
import warnings
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from mcp_connector import config
from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.clients import talk as talk_client
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import talk as talk_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

#: The whole observable surface of the three side effects :data:`talk_client.READ_ONLY_PARAMS`
#: switches off. ``lastReadMessage`` is the read marker of this account, ``unreadMessages`` and
#: ``unreadMention`` are the two counters a notification acknowledgement would clear, and
#: ``lastCommonReadMessage`` is the read state every other participant of the conversation can
#: see, which is the one that makes a read visible to somebody else.
STATE_FIELDS = ("lastReadMessage", "unreadMessages", "unreadMention", "lastCommonReadMessage")


def unique_message() -> str:
    """One message text that no other run wrote, with umlauts a broken encoding would eat."""
    return f"Grüße aus Hamburg, Straße 1 ({time.strftime('%Y%m%d-%H%M%S')} {uuid.uuid4().hex[:8]})"


def measured(what: str) -> None:
    """Make a measurement visible in the test report of a passing run.

    A print stays hidden while the test is green, and a green run is exactly when these
    numbers are wanted: the eight values of the side effect measurement belong in the plan
    summary because phase 10 and phase 11 build on them.
    """
    warnings.warn(f"measured: {what}", stacklevel=2)


@pytest.fixture
def talk_env() -> dict[str, str]:
    """The connection values plus the two conversation names the bootstrap published.

    Two spellings of the same pair of values are accepted, and that is not convenience. The
    connection file of the app password instance names them ``NC_MCP_USER`` and
    ``NC_MCP_APP_PASSWORD`` (``.env.test``), the one of the HaRP topology names them
    ``NC_MCP_TEST_USER`` and ``NC_MCP_TEST_APP_PASSWORD`` (``.env.exapp``), and the Talk
    scaffolding of this plan stands on both. A fixture that knew only one spelling would skip
    against the topology this plan measures on, and a green run that measured nothing is the
    one outcome this file must not produce.
    """
    base_url = (os.environ.get("NC_MCP_URL") or "").strip()
    user = (os.environ.get("NC_MCP_USER") or os.environ.get("NC_MCP_TEST_USER") or "").strip()
    secret = (
        os.environ.get("NC_MCP_APP_PASSWORD") or os.environ.get("NC_MCP_TEST_APP_PASSWORD") or ""
    ).strip()
    room = (os.environ.get("NC_MCP_TEST_TALK_ROOM") or "").strip()
    locked = (os.environ.get("NC_MCP_TEST_TALK_READONLY_ROOM") or "").strip()

    wanted = (
        ("NC_MCP_URL", base_url),
        ("NC_MCP_USER or NC_MCP_TEST_USER", user),
        ("NC_MCP_APP_PASSWORD or NC_MCP_TEST_APP_PASSWORD", secret),
        ("NC_MCP_TEST_TALK_ROOM", room),
        ("NC_MCP_TEST_TALK_READONLY_ROOM", locked),
    )
    missing = [name for name, value in wanted if not value]
    if missing:
        pytest.skip(
            "no Talk scaffolding configured (missing: "
            f"{', '.join(missing)}); run scripts/bootstrap_exapp.sh or "
            "scripts/bootstrap_test_nc.sh first"
        )
    assert user != "admin", "integration tests run as a normal user, never as admin"
    return {
        "base_url": base_url,
        "user": user,
        "secret": secret,
        "room": room,
        "locked_room": locked,
    }


@pytest.fixture
async def clients(talk_env: dict[str, str]) -> AsyncIterator[NcClients]:
    capabilities.clear_cache()
    nc_clients = NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(talk_env["base_url"]),
            user=talk_env["user"],
            secret=talk_env["secret"],
        ),
    )
    async with nc_clients.client:
        yield nc_clients


async def _spreed_section(clients: NcClients) -> dict[str, Any]:
    """The raw ``spreed`` section of ``/cloud/capabilities``: a read of the test, not of a tool.

    :class:`~mcp_connector.nextcloud.capabilities.Capabilities` keeps only what a tool needs,
    and the version of the app is not one of those things. It is a measurement this phase owes
    its summary, because Talk publishes roughly monthly and the research this plan was built
    on read the source at tag v24.0.4, so the number is read here and marked as scaffolding.
    """
    response = await ocs.ocs_get(clients.client, clients.creds, capabilities.CAPABILITIES_PATH)
    payload = ocs.parse_ocs(response, what="the capabilities of this Nextcloud")
    section = payload.get("capabilities") if isinstance(payload, dict) else None
    spreed = section.get("spreed") if isinstance(section, dict) else None
    return spreed if isinstance(spreed, dict) else {}


async def _rooms(clients: NcClients) -> list[dict[str, Any]]:
    """The unprojected conversation list of this account.

    The projection of ``talk_browse`` deliberately drops the four fields of
    :data:`STATE_FIELDS`, so the measurement reads the raw answer. The read under measurement
    is the one that goes through the tool, and that difference is the whole point: the
    property has to hold for what the connector promises, not for a request this test built.
    """
    return await talk_client.get_rooms(clients.client, clients.creds, include_last_message=False)


async def _named_room(clients: NcClients, name: str) -> dict[str, Any]:
    """The scaffolding conversation with this display name, or a skip that names it."""
    for room in await _rooms(clients):
        if str(room.get("displayName") or "") == name:
            return room
    pytest.skip(
        f"the conversation {name!r} does not exist for this account; "
        "run the bootstrap script of this topology first"
    )


async def _state(clients: NcClients, token: str) -> dict[str, Any]:
    """The four fields of :data:`STATE_FIELDS` for one conversation, read fresh."""
    for room in await _rooms(clients):
        if str(room.get("token") or "").strip() == token:
            return {field: room.get(field) for field in STATE_FIELDS}
    pytest.fail(f"the conversation {token} vanished from the list between two reads")


@pytest.fixture
async def writable(clients: NcClients, talk_env: dict[str, str]) -> dict[str, Any]:
    """The writable test conversation, with the changelog trap explicitly ruled out.

    The assertion is a guard and not a formality: type 4 is write protected whatever its
    ``readOnly`` flag says, it exists for every account, and picking it would turn every
    refusal below into a measurement of the wrong object.
    """
    room = await _named_room(clients, talk_env["room"])
    assert room.get("type") != talk_tools.TYPE_CHANGELOG, (
        f"the writable test conversation is the changelog conversation: {room.get('token')}"
    )
    assert talk_tools._may_send(room)[0], (
        f"the bootstrap conversation {talk_env['room']!r} is not writable for this account: "
        f"readOnly={room.get('readOnly')!r} permissions={room.get('permissions')!r}"
    )
    return room


@pytest.fixture
async def write_protected(clients: NcClients, talk_env: dict[str, str]) -> dict[str, Any]:
    """The write protected test conversation, the object the negative case is measured on."""
    room = await _named_room(clients, talk_env["locked_room"])
    if talk_tools._number(room.get("readOnly")) == talk_tools.READ_WRITE:
        pytest.skip(
            f"the conversation {talk_env['locked_room']!r} is not write protected on this "
            "instance; the bootstrap sets it with occ talk:room:update --readonly 1"
        )
    return room


def _sending_is_switched_on() -> bool:
    """Establish the state of the administrative switch instead of assuming it.

    A value once stored in Nextcloud survives every rebuild of the container, so a Talk switch
    somebody turned off would make a later run red without a visible reason. The send tests
    below therefore skip with the reason named rather than fail.
    """
    return config.talk_send_enabled()


async def test_capabilities_report_the_installed_spreed_app(clients: NcClients) -> None:
    """The app the whole family needs, and the version the summary of this phase owes."""
    caps = await capabilities.load(clients)
    if not caps.spreed_available:
        pytest.skip(
            "the Talk app is not installed or not enabled for this account; "
            "the bootstrap installs it with ensure_app spreed"
        )

    assert caps.spreed_chat_max_length > 0, (
        f"the instance reports no usable chat length: {caps.spreed_chat_max_length!r}"
    )
    assert caps.spreed_features, "an installed Talk app publishes a feature list"

    spreed = await _spreed_section(clients)
    measured(
        f"spreed version {spreed.get('version')!r}, {len(caps.spreed_features)} features, "
        f"chat max-length {caps.spreed_chat_max_length}"
    )
    measured(f"spreed features (first ten): {list(caps.spreed_features)[:10]}")


async def test_the_admin_switch_is_established_and_not_assumed() -> None:
    """Both ends of the TALK-04 switch, plus the value this topology really carries.

    Two assertions, because the reading itself has to be live: an explicit ``0`` closes the
    channel and an unset value leaves it open, which is the shipped state. The value of this
    topology is a measurement and not an expectation, for the reason
    :func:`_sending_is_switched_on` spells out.
    """
    assert config.talk_send_enabled({config.ENV_TALK_SEND: "0"}) is False
    assert config.talk_send_enabled({}) is True, "the shipped state of this switch is on"

    measured(
        f"admin switch talk_send on this topology: {_sending_is_switched_on()} "
        f"({config.ENV_TALK_SEND}={os.environ.get(config.ENV_TALK_SEND)!r})"
    )


async def test_the_conversation_level_lists_both_test_conversations_with_their_write_state(
    clients: NcClients, talk_env: dict[str, str]
) -> None:
    """Positive control: without it, every refusal below could be an empty answer instead.

    The two conversations are found through the tool and not through the client, and their
    ``can_send`` is compared against what the scaffolding built, so the honesty of that field
    is measured on a real object rather than on a fixture.
    """
    answer = await talk_tools.browse(clients, level="conversations", limit=talk_tools.MAX_LIMIT)

    by_name = {str(entry["name"]): entry for entry in answer["results"]}
    open_entry = by_name.get(talk_env["room"])
    locked_entry = by_name.get(talk_env["locked_room"])
    if open_entry is None or locked_entry is None:
        pytest.skip(
            "the two bootstrap conversations are not in the list of this account "
            f"(found: {sorted(by_name)}); run the bootstrap script of this topology first"
        )

    assert open_entry["can_send"] is True, f"the writable conversation refuses a send: {open_entry}"
    assert open_entry["read_only"] == talk_tools.READ_WRITE
    assert locked_entry["can_send"] is False, (
        f"the write protected conversation accepts a send: {locked_entry}"
    )
    assert locked_entry["read_only"] != talk_tools.READ_WRITE
    assert "ü" in open_entry["name"], (
        f"the umlauts of the writable conversation name did not survive: {open_entry}"
    )
    assert "ß" in locked_entry["name"], (
        f"the umlauts of the write protected conversation name did not survive: {locked_entry}"
    )
    measured(
        f"conversations: count={answer['count']} "
        f"open={open_entry['token']} type={open_entry['type']} unread={open_entry['unread']} "
        f"locked={locked_entry['token']} read_only={locked_entry['read_only']}"
    )


async def test_reading_the_history_changes_nothing_about_the_account(
    clients: NcClients, writable: dict[str, Any]
) -> None:
    """The property TALK-02 promises, measured instead of asserted about our own URL.

    The unit test of plan 09-01 holds that the four parameters stand in the request. This one
    holds the consequence: the read marker, both unread counters and the read state other
    participants can see are the same before and after. Those four fields are the whole
    observable surface of the three side effects those parameters switch off, and
    ``unreadMessages`` together with ``unreadMention`` is at the same time the counter probe
    that no notification was acknowledged, as far as the conversation list makes that visible.

    The read in the middle runs through :mod:`mcp_connector.tools.talk` and not through the
    client, because the promised property belongs to the tool a model calls.

    The conversation is filled first when it is empty, and that is what makes this a
    measurement rather than a formality: ``setReadMarker`` can only move a marker that has
    somewhere to move to, so a read over an empty window would come back unchanged whatever
    the parameters said. On an instance with a switched off send the fill step is skipped and
    the measurement is the weaker one, which the measured line then says.
    """
    token = str(writable["token"])
    filled = await talk_tools.browse(clients, level="messages", token=token, limit=20)
    if filled["count"] == 0 and _sending_is_switched_on():
        await talk_tools.send(clients, token=token, message=unique_message())

    before = await _state(clients, token)
    answer = await talk_tools.browse(clients, level="messages", token=token, limit=20)
    after = await _state(clients, token)

    assert before["lastReadMessage"] == after["lastReadMessage"], (
        f"reading moved the read marker (lastReadMessage): "
        f"{before['lastReadMessage']!r} -> {after['lastReadMessage']!r}"
    )
    assert before["unreadMessages"] == after["unreadMessages"], (
        f"reading changed the unread counter (unreadMessages): "
        f"{before['unreadMessages']!r} -> {after['unreadMessages']!r}"
    )
    assert before["unreadMention"] == after["unreadMention"], (
        f"reading acknowledged a mention (unreadMention): "
        f"{before['unreadMention']!r} -> {after['unreadMention']!r}"
    )
    assert before["lastCommonReadMessage"] == after["lastCommonReadMessage"], (
        f"reading changed the read state other people can see (lastCommonReadMessage): "
        f"{before['lastCommonReadMessage']!r} -> {after['lastCommonReadMessage']!r}"
    )

    assert answer["count"] >= 1 or not _sending_is_switched_on(), (
        "the measurement ran over an empty window although sending is on; "
        "the fill step above did not take effect"
    )
    measured(
        f"side effect free read of {token} (messages in the window: {answer['count']}): "
        + ", ".join(f"{field} {before[field]!r} -> {after[field]!r}" for field in STATE_FIELDS)
    )


async def test_an_empty_history_is_an_empty_answer_and_not_a_hint_about_the_base_url(
    clients: NcClients, write_protected: dict[str, Any]
) -> None:
    """Trap 2 together with T12, and it is the most likely first run of all.

    The write protected conversation is never written into, so its history holds nothing but
    system messages, which the positive list of message types drops. The answer is therefore
    ``count: 0``, and the unread counter of that very conversation can stand at one at the same
    time, because Talk counts a conversation nobody opened as unread whether it holds anything
    or not. Neither of the two is an error, and neither of them may arrive as the sentence
    about a wrong base URL that a 3xx would produce.
    """
    token = str(write_protected["token"])
    try:
        answer = await talk_tools.browse(clients, level="messages", token=token, limit=20)
    except ToolError as error:
        pytest.fail(
            f"an empty history came back as an error: {error.message} ({error.hint}); "
            f"the base URL sentence is {config.REDIRECT_HINT!r}"
        )

    assert answer["count"] == 0, f"the write protected conversation holds messages: {answer!r}"
    assert answer["results"] == []
    assert answer["token"] == token
    measured(
        f"empty history of {token}: count={answer['count']} "
        f"next={'yes' if answer.get('next') else 'no'} "
        f"unreadMessages={write_protected.get('unreadMessages')!r}"
    )


async def test_the_live_history_url_carries_the_four_read_only_parameters(
    clients: NcClients, writable: dict[str, Any]
) -> None:
    """The counter probe of the measurement above: the request really was built that way.

    A parsed answer cannot show which parameters went out, and the side effect measurement
    alone would also stay green if the instance simply ignored them. Both halves together are
    the proof: our values leave the process, and nothing moves on the account.
    """
    token = str(writable["token"])
    calls: list[httpx.URL] = []
    original_send = clients.client.send

    async def counting_send(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        if talk_client.CHAT_PREFIX in request.url.path:
            calls.append(request.url)
        return await original_send(request, **kwargs)

    # The capabilities call is an OCS route of its own and deliberately outside the capture.
    await capabilities.load(clients)
    clients.client.send = counting_send  # type: ignore[method-assign]
    try:
        await talk_tools.browse(clients, level="messages", token=token, limit=20)
    finally:
        clients.client.send = original_send  # type: ignore[method-assign]

    assert len(calls) == 1, f"one history read must issue exactly one chat request: {calls}"
    url = calls[0]
    for name, value in talk_client.READ_ONLY_PARAMS.items():
        assert url.params.get(name) == str(value), (
            f"the live history URL carries {name}={url.params.get(name)!r} instead of {value}"
        )
    assert url.params["limit"] == "20"
    measured(f"live history URL: {url.copy_with(scheme='', host='', port=None)}")


async def test_a_sent_message_is_found_again_in_the_history_of_the_same_conversation(
    clients: NcClients, writable: dict[str, Any]
) -> None:
    """The round trip: a message written through the tool comes back under its own wording."""
    if not _sending_is_switched_on():
        pytest.skip(
            f"sending is switched off on this topology ({config.ENV_TALK_SEND}=0); "
            "the refusal of that state is covered by tests/unit/test_talk_tools.py"
        )

    token = str(writable["token"])
    text = unique_message()
    sent = await talk_tools.send(clients, token=token, message=text)

    assert sent["sent"] is True
    assert sent["id"], f"Talk accepted the message without an id: {sent!r}"
    assert sent["token"] == token
    assert sent["conversation"] == str(writable["displayName"])
    assert sent["url"].endswith(f"/call/{token}")

    answer = await talk_tools.browse(
        clients, level="messages", token=token, limit=talk_tools.MAX_LIMIT
    )
    found = next((item for item in answer["results"] if item["message"] == text), None)
    assert found is not None, (
        f"the sent message is not in the history of {token}: "
        f"{[item['message'] for item in answer['results']]}"
    )
    assert "Grüße aus Hamburg, Straße 1" in found["message"], (
        f"the umlauts did not survive the round trip: {found!r}"
    )
    assert found["id"] == sent["id"]
    measured(f"sent message {sent['id']} into {token} and read it back: {found['message']!r}")


async def test_a_send_into_the_write_protected_conversation_is_refused_with_a_next_step(
    clients: NcClients, write_protected: dict[str, Any]
) -> None:
    """The negative case of TALK-03 on a real object, and it leaves nothing behind.

    The message count of the same conversation is read before and after, because a refusal
    that still posted would be worse than a silent failure: no tool of this server can remove
    a message again.
    """
    if not _sending_is_switched_on():
        pytest.skip(f"sending is switched off on this topology ({config.ENV_TALK_SEND}=0)")

    token = str(write_protected["token"])
    before = await talk_tools.browse(
        clients, level="messages", token=token, limit=talk_tools.MAX_LIMIT
    )

    with pytest.raises(ToolError) as excinfo:
        await talk_tools.send(clients, token=token, message=unique_message())

    assert excinfo.value.hint, "a refusal without a next step is a dead end for the model"
    assert token in excinfo.value.message, (
        f"the refusal does not name the conversation it is about: {excinfo.value.message!r}"
    )
    assert "can_send" in excinfo.value.hint, (
        f"the next step does not point back at the read tool: {excinfo.value.hint!r}"
    )

    after = await talk_tools.browse(
        clients, level="messages", token=token, limit=talk_tools.MAX_LIMIT
    )
    assert after["count"] == before["count"], (
        f"the refused send still changed the history of {token}: {after!r}"
    )
    measured(f"read only refusal: {excinfo.value.message} ({excinfo.value.hint})")


async def test_a_token_that_is_not_in_the_list_never_reaches_nextcloud_in_a_path(
    clients: NcClients,
) -> None:
    """T10: the refusal is our own sentence and not a 404 of the app.

    An unknown token on a single conversation route registers a counted brute force attempt
    against the address of this container, and that address is the same one for every user of
    the instance. So the assertion is not only that the call is refused, but that the invented
    token appears in no outgoing request at all, neither in a path nor in a query. The guard
    belongs in the code and not in the topology: the bootstrap switches the counter off on
    this test instance, which is exactly why a passing test here has to prove the code.
    """
    invented = f"mcpnosuch{uuid.uuid4().hex[:8]}"
    seen: list[str] = []
    original_send = clients.client.send

    async def counting_send(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        seen.append(str(request.url))
        return await original_send(request, **kwargs)

    clients.client.send = counting_send  # type: ignore[method-assign]
    try:
        with pytest.raises(ToolError) as excinfo:
            await talk_tools.browse(clients, level="messages", token=invented, limit=5)
    finally:
        clients.client.send = original_send  # type: ignore[method-assign]

    assert excinfo.value.hint, "a refusal without a next step is a dead end for the model"
    assert invented in excinfo.value.message, (
        f"the refusal does not name the token it rejected: {excinfo.value.message!r}"
    )
    assert not any(invented in url for url in seen), (
        f"the invented token reached Nextcloud in a request: {seen}"
    )
    assert any(talk_client.ROOM_PREFIX in url for url in seen), (
        f"the refusal was made without looking at the account's own list: {seen}"
    )
    measured(f"unknown token refused after {len(seen)} request(s): {excinfo.value.message}")
