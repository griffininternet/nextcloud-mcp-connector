"""The permission promise proven over the whole ExApp chain (AUTH-05, D-28).

``tests/integration/test_permission_fidelity.py`` asks the same question this file asks:
does a tool refuse what a user does not own. The difference is where the credentials go and
where the identity is born. There the credentials reach our own client layer and the user id
is a field we set. Here the credentials are an ordinary Nextcloud app password that travels
to HaRP, and the identity is resolved by HaRP out of that password, injected as an AppAPI
header and only then trusted by the ExApp. The request runs the full path a real user runs:

    MCP client  ->  HaRP  ->  ExApp  ->  impersonation  ->  Nextcloud ACLs

Nothing in this file builds a Credentials object or an ``httpx.BasicAuth`` for Nextcloud. The
only credential is each user's app password in a Basic header on the transport client, the
same header ``tests/compat/modern_client_check.py`` uses. Everything past the header is the
deployed topology: HaRP, the reverse proxy, the ExApp container and Nextcloud's own
permission check. A green row therefore cannot be explained by our client layer; it can only
be explained by the chain resolving the right user and Nextcloud enforcing the right ACLs.

The order of the checks is deliberate, so an empty answer can never pass for a boundary:

1. Guard: alice and bob are really two different accounts.
2. ``tools/list`` over the chain answers the full tool surface for both, so the chain carries.
3. Positive control (files): alice creates a file and finds it again.
4. Leak (``files_search``): bob does not find alice's file.
5. Positive control (notes) plus leak (``notes_search``): alice finds her note, bob does not.
6. Positive control and leak (``unified_search``): alice finds her content, bob finds neither.
7. Direct access (``files_read``): bob, knowing the exact path, is refused, not served content.

The app id ``mcp_connector`` is frozen (docs/app-id-freeze.md), so the HaRP route
``/exapps/mcp_connector/mcp`` is a constant here rather than an interpolation.

Run it against the running HaRP topology::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_permission_fidelity_exapp.py -m integration -q
"""

import base64
import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

# The app id is frozen (docs/app-id-freeze.md); the HaRP route never changes, so it is a
# literal here. The env carries the same value in APP_ID and the fixture asserts they agree.
EXAPP_MCP_PATH = "/exapps/mcp_connector/mcp"

# A confidential line that only alice's file carries, kept ASCII so a leak assertion is exact
# (the same choice tests/integration/test_exapp_dav_matrix.py makes for its negative case).
SECRET_LINE = "Vertrauliche Notiz von alice, Strassenbudget."


def _basic(user: str, secret: str) -> str:
    """A Basic header, exactly what a client hands to HaRP; HaRP resolves the identity."""
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()


@asynccontextmanager
async def _mcp_session(base: str, user: str, secret: str) -> AsyncIterator[Client]:
    """An MCP session over Streamable HTTP against the ExApp, authenticated as one user.

    The Basic header lives on the httpx client (mcp 2.x has no headers argument on the
    transport), so every request of the session carries this user's app password to HaRP.
    """
    url = base.rstrip("/") + EXAPP_MCP_PATH
    async with httpx2.AsyncClient(
        headers={"Authorization": _basic(user, secret)},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            yield client


def _payload(result: Any) -> dict[str, Any]:
    """Decode the compact JSON a tool answers with (structured_output=False)."""
    assert not result.is_error, f"the tool call ended in an error: {_texts(result)!r}"
    texts = _texts(result)
    assert texts, f"the tool answered without any text content: {result!r}"
    data = json.loads(texts[0])
    assert isinstance(data, dict), f"the tool did not answer with an object: {data!r}"
    return data


def _texts(result: Any) -> list[str]:
    return [c.text for c in result.content if getattr(c, "text", None) is not None]


@pytest.fixture
def chain_env() -> dict[str, str]:
    """The values scripts/bootstrap_exapp.sh writes into .env.exapp for the full chain test.

    ``NC_MCP_URL`` is the reverse proxy front where the HaRP path lives; the two app passwords
    are what each user hands to HaRP. When one is missing the test skips with the variable
    named, the shape the rest of the integration suite uses, so the default run stays green
    without the topology.
    """
    required = {
        "base": "NC_MCP_URL",
        "app_id": "APP_ID",
        "alice": "NC_MCP_TEST_USER",
        "alice_pw": "NC_MCP_TEST_APP_PASSWORD",
        "bob": "NC_MCP_TEST_USER2",
        "bob_pw": "NC_MCP_TEST_APP_PASSWORD2",
    }
    values = {key: (os.environ.get(name) or "").strip() for key, name in required.items()}
    missing = sorted(required[key] for key, value in values.items() if not value)
    if missing:
        pytest.skip(f"no ExApp topology configured (missing: {', '.join(missing)})")
    assert values["app_id"] == "mcp_connector", (
        f"the app id is frozen as mcp_connector but APP_ID is {values['app_id']!r}"
    )
    assert values["alice"] != "admin", "the chain test runs as normal users, never as admin"
    return values


@pytest.fixture
async def alices_content(chain_env: dict[str, str]) -> dict[str, str]:
    """One file and one note, created by alice over the full chain, each with a unique marker.

    The creates are themselves part of the proof: they run as impersonated alice through HaRP,
    so a later find by alice and a later miss by bob both speak about objects the chain made.
    """
    marker = f"nurfueralice{uuid.uuid4().hex[:10]}"
    file_path = f"/{marker}.md"
    note_title = f"alicenote{uuid.uuid4().hex[:10]}"
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        uploaded = _payload(
            await c.call_tool(
                "files_upload",
                {"path": file_path, "content": f"# {marker}\n{SECRET_LINE}\n"},
            )
        )
        assert uploaded.get("path") == file_path, f"alice's upload did not land: {uploaded!r}"
        note = _payload(
            await c.call_tool(
                "notes_create",
                {"title": note_title, "content": "created over the ExApp chain as alice"},
            )
        )
        assert note.get("id"), f"alice's note was not created: {note!r}"
    return {"marker": marker, "file_path": file_path, "note_title": note_title}


async def test_alice_and_bob_are_two_different_accounts(chain_env: dict[str, str]) -> None:
    """Guard against a false pass: two identical accounts make every leak test below empty."""
    assert chain_env["alice"] != chain_env["bob"], (
        "the negative proof needs two accounts; NC_MCP_TEST_USER2 points at the same user"
    )
    assert chain_env["alice_pw"] != chain_env["bob_pw"], (
        "both accounts carry the same app password; the chain would resolve the same identity"
    )


async def test_the_chain_carries_the_full_tool_surface_for_both(chain_env: dict[str, str]) -> None:
    """tools/list over HaRP, the ExApp and back, answers the full surface for alice and bob.

    Without this, an empty leak result could mean a broken chain rather than an enforced
    boundary. Both accounts reach the same tool count, so the chain is live for each of them.
    """
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        alice_tools = {tool.name for tool in (await c.list_tools()).tools}
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        bob_tools = {tool.name for tool in (await c.list_tools()).tools}

    assert alice_tools == bob_tools, "the two accounts see different tools over the chain"
    assert "files_search" in alice_tools
    assert "unified_search" in alice_tools
    assert len(alice_tools) >= 14, f"the chain served a short tool list: {sorted(alice_tools)}"


async def test_alice_finds_her_own_file_over_the_chain(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Positive control (files): without it, an empty answer for bob would prove nothing."""
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        result = _payload(await c.call_tool("files_search", {"query": alices_content["marker"]}))

    paths = {item["path"] for item in result["items"]}
    assert alices_content["file_path"] in paths, f"alice cannot find her own file: {result!r}"


async def test_bob_does_not_find_alices_file_over_the_chain(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Leak test (files_search): bob's WebDAV SEARCH runs in bob's home, never in alice's."""
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        result = _payload(await c.call_tool("files_search", {"query": alices_content["marker"]}))

    assert result["items"] == [], f"bob sees a file that is not his over the chain: {result!r}"
    assert result["count"] == 0


async def test_alice_finds_her_own_note_over_the_chain(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Positive control (notes): the note provider answers for the account that owns it."""
    title = alices_content["note_title"]
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        result = _payload(await c.call_tool("notes_search", {"query": title}))

    titles = {entry.get("title") for entry in result["results"]}
    assert title in titles, f"alice cannot find her own note: {result!r}"


async def test_bob_does_not_find_alices_note_over_the_chain(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Leak test (notes_search): the note provider must not answer across accounts."""
    title = alices_content["note_title"]
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        result = _payload(await c.call_tool("notes_search", {"query": title}))

    assert result["results"] == [], f"bob sees a note that is not his over the chain: {result!r}"
    assert result["count"] == 0


async def test_alice_finds_her_content_over_unified_search(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Positive control (unified_search): the widest read path answers for the owner."""
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        by_file = _payload(await c.call_tool("unified_search", {"query": alices_content["marker"]}))

    assert by_file["count"] >= 1, f"alice's own content is invisible to unified search: {by_file!r}"


async def test_bob_finds_neither_over_unified_search(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Leak test (unified_search): the provider fan-out is the widest path and stays honest.

    Both of alice's markers are queried, so a leak from any single provider would show up.
    """
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        by_file = _payload(await c.call_tool("unified_search", {"query": alices_content["marker"]}))
        by_note = _payload(
            await c.call_tool("unified_search", {"query": alices_content["note_title"]})
        )

    assert by_file["results"] == [], f"a provider leaked alice's file to bob: {by_file!r}"
    assert by_note["results"] == [], f"a provider leaked alice's note to bob: {by_note!r}"


async def test_bob_cannot_read_alices_file_even_knowing_the_exact_path(
    chain_env: dict[str, str], alices_content: dict[str, str]
) -> None:
    """Direct access: the case where search hygiene does not help, the path is already known.

    Every request of bob's session carries bob's app password, so the chain resolves bob and
    Nextcloud resolves the path inside bob's home, where the file is not. The tool refuses
    instead of reaching into another home, and the refusal never carries the file content.
    """
    file_path = alices_content["file_path"]
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        try:
            result = await c.call_tool("files_read", {"path": file_path})
        except Exception as exc:  # a raised protocol error is also a refusal, not content
            message = str(exc)
        else:
            assert result.is_error, f"bob read alice's file over the chain: {_texts(result)!r}"
            message = " ".join(_texts(result))
    assert SECRET_LINE not in message, "the refusal carried the content of alice's file"
    assert "Vertrauliche" not in message, "the refusal carried the content of alice's file"
