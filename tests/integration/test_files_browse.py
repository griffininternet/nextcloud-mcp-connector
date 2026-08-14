"""Integration tests for finding and browsing files (opt-in, marker ``integration``).

The interesting test in here is the last one: it asserts that a word which exists only
*inside* a file produces no hit. That is not a bug report, it is the contract of WebDAV
SEARCH (pitfall 5), and pinning it here means a future change to full text search has to
be a deliberate decision instead of a surprise.

Run it with:
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
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.paging import decode_cursor
from mcp_connector.tools import files as files_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

#: A word that appears in no file name of a fresh Nextcloud and only inside our content.
CONTENT_ONLY_WORD = "zwiebelkuchenrezept"


@pytest.fixture
def clients(live_env: dict[str, str | None]) -> NcClients:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")

    user = live_env["user"]
    assert user != "admin", "integration tests run as a normal user, never as admin"

    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(str(live_env["base_url"])),
            user=str(user),
            secret=str(live_env["secret"]),
        ),
    )


def _unique_name() -> str:
    return f"mcp-browse-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


async def test_an_uploaded_file_is_found_by_name_and_listed(clients: NcClients) -> None:
    name = _unique_name()
    path = f"/{name}.md"
    await files_tools.upload(clients, path=path, content=f"# {name}\nInhalt mit Umlauten: Größe\n")

    found = await files_tools.search(clients, query=name)
    assert found["note"] == files_tools.SEARCH_NOTE
    assert [item["path"] for item in found["items"]] == [path]

    hit = found["items"][0]
    assert hit["kind"] == "file"
    assert hit["id"].startswith("file:"), "every hit carries a prefixed id for fetch"
    assert hit["size"] > 0

    listing = await files_tools.list_dir(clients, path="/")
    assert path in [item["path"] for item in listing["items"]]
    assert "/" not in [item["path"] for item in listing["items"]], "the folder is not its own child"


async def test_search_matches_names_only_and_not_file_contents(clients: NcClients) -> None:
    """Pitfall 5, verified against the real server instead of assumed."""
    name = _unique_name()
    await files_tools.upload(
        clients,
        path=f"/{name}.md",
        content=f"Dieses Dokument beschreibt ein {CONTENT_ONLY_WORD} in aller Ausfuehrlichkeit.\n",
    )

    by_name = await files_tools.search(clients, query=name)
    assert by_name["count"] >= 1, "the name is indexed"

    by_content = await files_tools.search(clients, query=CONTENT_ONLY_WORD)
    assert by_content["items"] == [], "WebDAV SEARCH matches names, never contents"
    assert by_content["note"] == files_tools.SEARCH_NOTE


async def test_a_truncated_listing_survives_a_restart_of_the_process(clients: NcClients) -> None:
    """SRV-05 on tool level: the handle is the whole state, nothing lives in this process."""
    name = _unique_name()
    for index in range(3):
        await files_tools.upload(clients, path=f"/{name}-{index}.md", content="x\n")

    first = await files_tools.search(clients, query=name, limit=1)
    assert first["truncated"] is True
    assert decode_cursor(first["next"])["o"] == 1

    second = await files_tools.search(clients, query=name, limit=1, cursor=first["next"])
    assert second["items"], "the handle continues the search without any server state"
    assert second["items"][0]["path"] != first["items"][0]["path"]


async def test_listing_a_file_explains_itself(clients: NcClients) -> None:
    name = _unique_name()
    path = f"/{name}.md"
    await files_tools.upload(clients, path=path, content="x\n")

    with pytest.raises(ToolError) as excinfo:
        await files_tools.list_dir(clients, path=path)

    assert "files_read" in excinfo.value.hint


async def test_listing_an_unknown_folder_reports_the_path(clients: NcClients) -> None:
    path = f"/{_unique_name()}-folder"
    with pytest.raises(ToolError) as excinfo:
        await files_tools.list_dir(clients, path=path)

    assert path in excinfo.value.message
