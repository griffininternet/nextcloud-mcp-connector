"""Cloud wide search against a real Nextcloud 34 (opt-in, marker ``integration``).

A recorded fixture cannot answer the two questions that matter here: which providers a
real instance actually reports, and whether a freshly created file is findable through
them without any indexing step. Both are checked against the running container.

The degraded path gets a live proof too, without breaking the instance: a provider id that
does not exist has to come back as a named degradation next to real hits, never as an empty
answer.

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
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import files as files_tools
from mcp_connector.tools import search as search_tools

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


async def test_the_instance_reports_its_own_provider_list(clients: NcClients) -> None:
    """The list is instance specific; the only entry we may rely on is the core one."""
    providers = await ocs.list_search_providers(clients.client, clients.creds)

    ids = {str(provider.get("id")) for provider in providers}
    assert "files" in ids, f"a Nextcloud without the files provider is not one: {sorted(ids)}"


async def test_a_new_file_is_found_over_the_files_provider(clients: NcClients) -> None:
    """Upload, then find it cloud wide: no index run, no second tool, no degradation."""
    marker = f"mcpsuche{uuid.uuid4().hex[:8]}"
    path = f"/{marker}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    await files_tools.upload(clients, path=path, content="# Suchtest\nBudget und Straßenbau\n")

    result = await search_tools.unified_search(clients, query=marker)

    assert "degraded" not in result, f"no provider may fail here: {result.get('degraded')}"
    providers = {hit["provider"] for hit in result["results"]}
    assert "files" in providers, f"the uploaded file was not found: {result}"

    hit = next(hit for hit in result["results"] if hit["provider"] == "files")
    assert hit["kind"] == "file"
    assert hit["id"].startswith("file:")
    assert hit["url"].startswith(clients.creds.base_url)
    assert result["note"] == search_tools.SEARCH_NOTE


async def test_an_unknown_provider_id_comes_back_as_a_named_degradation(
    clients: NcClients,
) -> None:
    """The live degraded proof: a partial answer is always labelled as one."""
    result = await search_tools.unified_search(
        clients, query="budget", providers=["files", "ganz-sicher-nicht-installiert"]
    )

    assert result["degraded"] == [
        {
            "provider": "ganz-sicher-nicht-installiert",
            "reason": "This Nextcloud has no search provider with that id.",
        }
    ]


async def test_a_term_without_a_hit_returns_an_empty_list(clients: NcClients) -> None:
    """Zero hits are not an error, and the answer repeats the term that was searched."""
    term = f"kein-treffer-{uuid.uuid4().hex[:8]}"

    result = await search_tools.unified_search(clients, query=term)

    assert result["results"] == []
    assert result["count"] == 0
    assert result["query"] == term
