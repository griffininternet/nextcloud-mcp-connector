"""Notes round trip against a real Nextcloud 34 with the Notes app (opt-in).

The unit tests pin the shapes; only a real instance answers the two questions that matter
here: does the unified search provider ``notes`` exist and find a note that was created
seconds earlier, and is the title the server reports back really the truth (it sanitises
and numbers titles, so a second note with the same title comes back renamed).

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

import time
import uuid

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import notes as notes_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


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


async def test_capabilities_report_the_installed_notes_app(clients: NcClients) -> None:
    caps = await capabilities.load(clients)

    assert caps.notes_available is True, "the bootstrap installs the Notes app"
    assert any(version.startswith("1.") for version in caps.notes_api_versions), (
        f"assumption A5: Notes still speaks the v1 API (got {caps.notes_api_versions})"
    )


async def test_create_search_and_read_are_one_round_trip(clients: NcClients) -> None:
    title = unique_title()
    content = f"# {title}\nGrüße aus Hamburg, Straße 1\n"

    created = await notes_tools.create(clients, title=title, content=content, category="MCP")
    assert created["title"] == title
    assert created["id"].startswith("note:")

    found = await notes_tools.search(clients, query=title.split()[-1])
    ids = [hit["id"] for hit in found["results"]]
    assert created["id"] in ids, f"the note must be findable via the notes search provider: {found}"

    read = await notes_tools.read(clients, note_id=created["id"])
    assert read["id"] == created["id"]
    assert read["content"] == content
    assert read["title"] == created["title"]
    assert read["category"] == "MCP"


async def test_the_server_title_wins_over_the_requested_one(clients: NcClients) -> None:
    """Notes numbers a colliding title; whatever it answers is what the model must see."""
    title = unique_title()
    first = await notes_tools.create(clients, title=title, content="erste Notiz\n")
    second = await notes_tools.create(clients, title=title, content="zweite Notiz\n")

    assert first["id"] != second["id"]
    read_second = await notes_tools.read(clients, note_id=second["id"])
    assert read_second["title"] == second["title"], (
        "the title returned by create must be the one stored on the server"
    )


async def test_reading_an_unknown_note_reports_not_found(clients: NcClients) -> None:
    with pytest.raises(ToolError) as excinfo:
        await notes_tools.read(clients, note_id="note:99999999")

    assert excinfo.value.hint
