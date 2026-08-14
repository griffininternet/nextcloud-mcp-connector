"""The negative proof of the permission promise, with two real accounts (TOOL-06).

Every other test in this suite asks whether a tool finds what the user owns. This file
asks the opposite and much more important question: does a tool refuse what the user does
**not** own. A server that answers the first question perfectly and the second one wrongly
is not a connector, it is a data leak.

The proof needs two accounts, because a single account can never demonstrate a boundary.
``scripts/bootstrap_test_nc.sh`` creates both: alice with a calendar and an address book,
bob as the restricted second account. Neither shares anything with the other, so every
path from bob to alice's file has to come back empty.

Four paths are checked, because they reach Nextcloud through four different APIs and each
one could leak on its own:

*   ``files_search``  -> WebDAV SEARCH
*   ``unified_search`` -> OCS unified search, fanned out over all providers
*   ``search``         -> the ChatGPT profile on top of unified search
*   ``files_read``     -> a direct WebDAV GET on the known path

The last one matters most: it is the case where the attacker already knows the path, so
nothing but Nextcloud's own permission check stands between bob and the file. If that
check ever stopped working, an empty search result would still look reassuring.

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

import os
import uuid
from collections.abc import AsyncIterator

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import chatgpt as chatgpt_tools
from mcp_connector.tools import files as files_tools
from mcp_connector.tools import search as search_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def _clients(base_url: str, user: str, secret: str) -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(base_url),
            user=user,
            secret=secret,
        ),
    )


@pytest.fixture
async def alice(live_env: dict[str, str | None]) -> AsyncIterator[NcClients]:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")
    assert live_env["user"] != "admin", "integration tests run as a normal user, never as admin"

    clients = _clients(str(live_env["base_url"]), str(live_env["user"]), str(live_env["secret"]))
    async with clients.client:
        yield clients


@pytest.fixture
async def bob(live_env: dict[str, str | None]) -> AsyncIterator[NcClients]:
    """The second account. He owns nothing of alice's and shares nothing with her."""
    base_url = live_env["base_url"]
    user = os.environ.get("NC_MCP_TEST_USER2")
    secret = os.environ.get("NC_MCP_TEST_APP_PASSWORD2")
    if not base_url or not user or not secret:
        pytest.skip("no second test user configured (NC_MCP_TEST_USER2)")

    clients = _clients(str(base_url), user, secret)
    async with clients.client:
        yield clients


@pytest.fixture
async def alices_private_file(alice: NcClients) -> dict[str, str]:
    """One file in alice's home, with a marker no other object in the instance carries."""
    marker = f"nurfueralice{uuid.uuid4().hex[:10]}"
    path = f"/{marker}.md"
    await files_tools.upload(
        alice,
        path=path,
        content=f"# {marker}\nVertrauliche Notiz von alice, Straßenbau-Budget.\n",
    )
    return {"marker": marker, "path": path}


async def test_the_two_accounts_are_really_two_different_accounts(
    alice: NcClients, bob: NcClients
) -> None:
    """Guard against a false pass: if both fixtures were alice, every test below is empty."""
    assert alice.creds.user != bob.creds.user, (
        "the negative proof needs two accounts; NC_MCP_TEST_USER2 points at the same user"
    )
    assert alice.creds.secret != bob.creds.secret


async def test_alice_finds_her_own_file(
    alice: NcClients, alices_private_file: dict[str, str]
) -> None:
    """The positive control. Without it, an empty answer for bob proves nothing."""
    result = await files_tools.search(alice, query=alices_private_file["marker"])

    paths = {item["path"] for item in result["items"]}
    assert alices_private_file["path"] in paths, f"alice cannot find her own file: {result}"


async def test_bob_does_not_find_alices_file_over_the_file_search(
    bob: NcClients, alices_private_file: dict[str, str]
) -> None:
    """WebDAV SEARCH runs in bob's own home collection, never in the instance."""
    result = await files_tools.search(bob, query=alices_private_file["marker"])

    assert result["items"] == [], f"bob sees a file that is not his: {result}"
    assert result["count"] == 0


async def test_bob_does_not_find_alices_file_over_the_unified_search(
    bob: NcClients, alices_private_file: dict[str, str]
) -> None:
    """The provider fan-out is the widest read path of this server, and it stays honest."""
    result = await search_tools.unified_search(bob, query=alices_private_file["marker"])

    assert result["results"] == [], f"a provider leaked alice's file to bob: {result}"
    assert result["count"] == 0


async def test_bob_does_not_find_alices_file_over_the_chatgpt_profile(
    bob: NcClients, alices_private_file: dict[str, str]
) -> None:
    """``search`` is a rename of unified search, so it must not widen the permission scope."""
    hits = await chatgpt_tools.search(bob, alices_private_file["marker"])

    assert hits == [], f"the ChatGPT profile leaked alice's file to bob: {hits}"


async def test_bob_cannot_read_alices_file_even_knowing_the_exact_path(
    bob: NcClients, alices_private_file: dict[str, str]
) -> None:
    """The case where search hygiene does not help: the path is already known.

    Every request carries bob's own credentials, so Nextcloud resolves the path inside
    bob's home. The file simply is not there, and the tool says so instead of reaching
    into another home directory.
    """
    with pytest.raises(ToolError) as excinfo:
        await files_tools.read(bob, path=alices_private_file["path"])

    message = f"{excinfo.value.message} {excinfo.value.hint}"
    assert "Vertrauliche" not in message, "an error must never carry the content of a file"
    assert "Straßenbau" not in message, "an error must never carry the content of a file"
