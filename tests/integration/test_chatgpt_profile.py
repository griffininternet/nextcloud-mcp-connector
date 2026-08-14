"""The ChatGPT profile against a real Nextcloud 34 (opt-in, marker ``integration``).

Recorded fixtures cannot answer the one question this file exists for: does an id that
``search`` produced still resolve when ``fetch`` gets it back. Both round trips are walked
end to end, for a file and for a note, and the content that comes out is compared with the
content that went in.

The file case additionally proves the piece no mock can prove: a Nextcloud file id can be
turned back into a path with a single WebDAV SEARCH, because ``oc:fileid`` really is a
queryable property on this server generation.

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
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import chatgpt
from mcp_connector.tools import files as files_tools
from mcp_connector.tools import notes as notes_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


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


async def test_a_file_is_found_by_search_and_read_back_by_fetch(clients: NcClients) -> None:
    """The full ChatGPT round trip: upload, search, fetch, compare."""
    marker = f"mcpprofil{uuid.uuid4().hex[:8]}"
    path = f"/{marker}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    content = f"# {marker}\nBudget und Straßenbau, Größe 3 Mio.\n"
    await files_tools.upload(clients, path=path, content=content)

    results = await chatgpt.search(clients, query=marker)

    hit = next((item for item in results if item["id"].startswith("file:")), None)
    assert hit is not None, f"the uploaded file did not come back as a file hit: {results}"
    assert hit["url"], "a hit without a url produces no citation in ChatGPT"

    fetched = await chatgpt.fetch(clients, hit["id"])

    assert fetched["id"] == hit["id"]
    assert fetched["text"] == content, "fetch must return what was uploaded, byte for byte"
    assert fetched["metadata"] is not None
    assert fetched["metadata"]["kind"] == "file"
    assert fetched["metadata"]["path"] == path
    assert fetched["url"].startswith(clients.creds.base_url)


async def test_a_note_is_found_by_search_and_read_back_by_fetch(clients: NcClients) -> None:
    """The same round trip over a second provider and a second reader."""
    marker = f"mcpnotiz{uuid.uuid4().hex[:8]}"
    content = f"Protokoll {marker}\nAnwesend: Anja, Khaled. Beschluss: Straßenbau.\n"
    created = await notes_tools.create(clients, title=marker, content=content)

    results = await chatgpt.search(clients, query=marker)

    hit = next((item for item in results if item["id"] == created["id"]), None)
    assert hit is not None, f"the new note did not come back from search: {results}"
    assert hit["url"], "a hit without a url produces no citation in ChatGPT"

    fetched = await chatgpt.fetch(clients, hit["id"])

    assert fetched["id"] == created["id"]
    assert content.strip() in fetched["text"]
    assert fetched["metadata"] is not None
    assert fetched["metadata"]["kind"] == "note"


async def test_an_id_of_a_kind_that_cannot_be_fetched_says_so(clients: NcClients) -> None:
    """The honest boundary holds against the real instance too, without any request."""
    with pytest.raises(ToolError, match="cannot be fetched"):
        await chatgpt.fetch(clients, f"url:{clients.creds.base_url}/index.php/apps/dashboard")
