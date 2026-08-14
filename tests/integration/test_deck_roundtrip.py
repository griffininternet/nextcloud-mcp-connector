"""Deck round trip against a real Nextcloud 34 with the Deck app (opt-in).

The unit tests pin the shapes; only a real instance answers the questions that matter
here: does Deck really accept the mandatory headers the way the documentation describes,
does ``GET /boards/{id}/stacks`` really carry the cards (the whole no-N+1 promise of
``deck_browse``), and is a card created seconds ago findable under the canonical long id.

Board and stack are test scaffolding, not connector features: the client cannot create
either of them on purpose (create-only, threat T-01-62), so the two ``POST`` calls below
are made directly with httpx and are clearly marked as setup.

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

import time
import uuid
from typing import Any

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.clients import deck as deck_client
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import deck as deck_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

BOARD_TITLE = "MCP-Test Board"
STACK_TITLE = "MCP-Test Stack"


def unique_title() -> str:
    return f"MCP-Test {time.strftime('%Y%m%d-%H%M%S')} {uuid.uuid4().hex[:8]}"


@pytest.fixture
def clients(live_env: dict[str, str | None]) -> NcClients:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")

    user = live_env["user"]
    assert user != "admin", "integration tests run as a normal user, never as admin"

    capabilities.clear_cache()
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(str(live_env["base_url"])),
            user=str(user),
            secret=str(live_env["secret"]),
        ),
    )


async def _post(clients: NcClients, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Test scaffolding only: the connector itself never creates boards or stacks."""
    response = await clients.client.post(
        deck_client.api_url(clients.creds, path),
        json=body,
        headers=dict(deck_client.DECK_HEADERS),
        auth=httpx.BasicAuth(clients.creds.user, clients.creds.secret),
    )
    if response.status_code >= 400:
        pytest.skip(f"this account may not prepare a deck board ({response.status_code})")
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


async def _board_and_stack(clients: NcClients) -> tuple[int, int]:
    """Return an existing writable board plus stack, creating them once if needed."""
    boards = await deck_client.get_boards(clients.client, clients.creds)
    board = next(
        (item for item in boards if item.get("title") == BOARD_TITLE and not item.get("archived")),
        None,
    )
    if board is None:
        board = await _post(clients, "/boards", {"title": BOARD_TITLE, "color": "0082c9"})

    board_id = int(board["id"])
    stacks = await deck_client.get_stacks(clients.client, clients.creds, board_id)
    stack = next((item for item in stacks if item.get("title") == STACK_TITLE), None)
    if stack is None:
        stack = await _post(
            clients, f"/boards/{board_id}/stacks", {"title": STACK_TITLE, "order": 1}
        )
    return board_id, int(stack["id"])


async def test_capabilities_report_the_installed_deck_app(clients: NcClients) -> None:
    caps = await capabilities.load(clients)

    assert caps.deck_available is True, "the bootstrap installs the Deck app"
    assert "1.0" in caps.deck_api_versions, (
        f"this client speaks Deck API 1.0 (got {caps.deck_api_versions})"
    )


async def test_a_new_card_is_findable_under_its_canonical_id(clients: NcClients) -> None:
    board_id, stack_id = await _board_and_stack(clients)
    title = unique_title()

    created = await deck_tools.create_card(
        clients,
        board_id=str(board_id),
        stack_id=str(stack_id),
        title=title,
        description="Grüße aus Hamburg, Straße 1",
    )
    assert created["id"] == f"card:{board_id}:{stack_id}:{created['id'].rsplit(':', 1)[-1]}"

    found = await deck_tools.browse(clients, level="cards", board_id=str(board_id), limit=100)
    ids = [card["id"] for card in found["results"]]
    assert created["id"] in ids, f"the new card must show up in the card level: {ids}"

    titles = {card["id"]: card["title"] for card in found["results"]}
    assert titles[created["id"]] == title


async def test_the_card_level_stays_one_request_against_a_real_instance(
    clients: NcClients,
) -> None:
    """The no-N+1 promise, measured where it counts: on a live board with real stacks."""
    board_id, _ = await _board_and_stack(clients)

    calls: list[str] = []
    original_send = clients.client.send

    async def counting_send(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        if "/apps/deck/api/" in request.url.path:
            calls.append(str(request.url))
        return await original_send(request, **kwargs)

    # The capabilities call is an OCS route and is deliberately not counted here.
    await capabilities.load(clients)
    clients.client.send = counting_send  # type: ignore[method-assign]
    try:
        await deck_tools.browse(clients, level="cards", board_id=str(board_id))
    finally:
        clients.client.send = original_send  # type: ignore[method-assign]

    assert len(calls) == 1, f"level=cards must cost exactly one Deck request, got {calls}"
    assert calls[0].endswith(f"/boards/{board_id}/stacks")


async def test_the_three_levels_answer_the_same_envelope(clients: NcClients) -> None:
    board_id, _ = await _board_and_stack(clients)

    boards = await deck_tools.browse(clients, level="boards")
    stacks = await deck_tools.browse(clients, level="stacks", board_id=str(board_id))
    cards = await deck_tools.browse(clients, level="cards", board_id=str(board_id))

    for answer, level in ((boards, "boards"), (stacks, "stacks"), (cards, "cards")):
        assert answer["level"] == level
        assert answer["count"] == len(answer["results"])

    assert board_id in [board["id"] for board in boards["results"]]


async def test_browsing_an_unknown_board_reports_it_instead_of_guessing(
    clients: NcClients,
) -> None:
    with pytest.raises(ToolError) as excinfo:
        await deck_tools.browse(clients, level="stacks", board_id="99999999")

    assert excinfo.value.hint
