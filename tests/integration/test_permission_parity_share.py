"""Permission parity in both directions, over the whole ExApp chain (AUTH-05, TOOL-09).

``tests/integration/test_permission_fidelity_exapp.py`` proves one half of the promise: bob
does not see what alice has. Success criterion 3 of phase 5 asks for the other half as well,
and that half cannot be measured with two accounts that share nothing: what a restricted user
*may* see, and where Nextcloud stops him even though our tool would happily continue.

The trap this file avoids is the one 05-RESEARCH.md names as pitfall 6: comparing the MCP view
with a "web view" built from the same calls and the same credentials is a test that is always
green, because our tools already speak WebDAV and OCS, the very interfaces the web interface
uses. So the asymmetry lives in the data, not in the comparison. ``ensure_readonly_share`` in
``scripts/bootstrap_exapp.sh`` creates it:

*   a folder of alice, shared with bob with ``permissions=1`` (read, nothing else), with one
    marked file in it, and
*   a second marked file of alice that is never shared with anybody.

Five statements follow, each of them measurable and none of them a tautology:

1. bob finds the shared file over ``files_search`` and over ``unified_search``.
2. bob finds the private file over neither, while alice finds it in the same run.
3. bob reads the shared file and gets its content marker back.
4. bob cannot upload into the read-only folder, although ``files_upload`` is create-only and
   would try; the same call into his own home succeeds, so the refusal is Nextcloud's.
5. Create-only holds over the chain: alice's second upload onto the same path is refused.

Nothing in this file builds a credential object of our own client layer and nothing builds an
authentication helper of the HTTP library, for the same reason the analog states in its own
header: the only credential is each user's app password in a Basic header on the transport
client. HaRP resolves the identity out of it, the ExApp impersonates that identity and
Nextcloud decides. A test that built the reference side itself would prove nothing about the
deployed chain, and a grep gate over this file keeps both spellings out of it.

The app id ``mcp_connector`` is frozen (docs/app-id-freeze.md), so the HaRP route
``/exapps/mcp_connector/mcp`` is a constant here rather than an interpolation.

Run it against the running HaRP topology::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_permission_parity_share.py -m integration -q
"""

import base64
import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import PurePosixPath
from typing import Any

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

# The app id is frozen (docs/app-id-freeze.md); the HaRP route never changes, so it is a
# literal here. The env carries the same value in APP_ID and the fixture asserts they agree.
EXAPP_MCP_PATH = "/exapps/mcp_connector/mcp"


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


async def _refusal(client: Client, tool: str, arguments: dict[str, Any]) -> str:
    """Call a tool that must not succeed and return the refusal as text.

    A raised protocol error and an error result are the same answer for this file: the call
    did not go through. A success is the one outcome that is never acceptable, so it fails
    here rather than in each caller.
    """
    try:
        result = await client.call_tool(tool, arguments)
    except Exception as exc:  # a raised protocol error is also a refusal, not a success
        return str(exc)
    assert result.is_error, f"{tool} succeeded where it had to be refused: {_texts(result)!r}"
    return " ".join(_texts(result))


@pytest.fixture
def chain_env() -> dict[str, str]:
    """The values ``scripts/bootstrap_exapp.sh`` writes into ``.env.exapp`` for this proof.

    The first six are the ones the analog needs: the reverse proxy front where the HaRP path
    lives, the frozen app id and one app password per user. The last four are the third data
    layer of plan 05-03, and without them this file has nothing to measure, so it skips with
    the missing names instead of asserting against paths that do not exist.
    """
    required = {
        "base": "NC_MCP_URL",
        "app_id": "APP_ID",
        "alice": "NC_MCP_TEST_USER",
        "alice_pw": "NC_MCP_TEST_APP_PASSWORD",
        "bob": "NC_MCP_TEST_USER2",
        "bob_pw": "NC_MCP_TEST_APP_PASSWORD2",
        "shared_dir": "NC_MCP_TEST_SHARED_DIR",
        "shared_file": "NC_MCP_TEST_SHARED_FILE",
        "private_file": "NC_MCP_TEST_PRIVATE_FILE",
        "marker": "NC_MCP_TEST_SHARED_MARKER",
    }
    values = {key: (os.environ.get(name) or "").strip() for key, name in required.items()}
    missing = sorted(required[key] for key, value in values.items() if not value)
    if missing:
        pytest.skip(f"no ExApp topology configured (missing: {', '.join(missing)})")
    # The three paths arrive relative to the root of the user and get their leading slash
    # here, which is the spelling the tools take. The bootstrap writes them that way because
    # Git Bash rewrites an exported value that starts with a slash into a Windows path when it
    # starts a native process: `/mcp-share-x/f.md` reached pytest as
    # `C:/Program Files/Git/mcp-share-x/f.md` and every assertion below measured the MSYS
    # installation directory instead of Nextcloud (measured on this host, plan 05-03).
    for key in ("shared_dir", "shared_file", "private_file"):
        assert not values[key].startswith("/"), (
            f"{required[key]} carries a leading slash; on Windows that value is rewritten "
            "before pytest sees it, so the connection file writes it relative to the root"
        )
        values[key] = "/" + values[key]
    assert values["app_id"] == "mcp_connector", (
        f"the app id is frozen as mcp_connector but APP_ID is {values['app_id']!r}"
    )
    assert values["alice"] != values["bob"], (
        "the parity proof needs two accounts; NC_MCP_TEST_USER2 points at the same user"
    )
    assert values["shared_file"].startswith(values["shared_dir"] + "/"), (
        "the shared file is not inside the shared folder, so statement 4 would prove nothing"
    )
    assert not values["private_file"].startswith(values["shared_dir"] + "/"), (
        "the private file lies inside the shared folder; bob is allowed to see it then"
    )
    # The private file carries its own unique token in its name and in its content, the same
    # way the shared one does. Deriving it here keeps the fixture at four variables.
    values["private_marker"] = PurePosixPath(values["private_file"]).stem
    assert values["private_marker"] not in values["marker"], (
        "both markers share a prefix; a leak assertion could then pass on the wrong object"
    )
    return values


async def test_bob_finds_the_shared_file_over_both_search_paths(
    chain_env: dict[str, str],
) -> None:
    """Statement 1: the rights of a share reach into both read paths of the connector.

    This is the positive half nobody can fake with two unrelated accounts: bob owns nothing
    here, the folder is alice's, and Nextcloud is the only reason he sees anything at all.
    Both paths are measured, because ``files_search`` is a WebDAV SEARCH in bob's own home
    (where the share is mounted) and ``unified_search`` is the provider fan-out over OCS.
    """
    marker = chain_env["marker"]
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        by_dav = _payload(await c.call_tool("files_search", {"query": marker}))
        by_ocs = _payload(await c.call_tool("unified_search", {"query": marker}))

    paths = {item["path"] for item in by_dav["items"]}
    assert chain_env["shared_file"] in paths, (
        f"bob does not find the file shared with him over files_search: {by_dav!r}"
    )
    assert by_ocs["count"] >= 1, f"the shared file is invisible to bob's unified search: {by_ocs!r}"
    assert any(marker in json.dumps(entry) for entry in by_ocs["results"]), (
        f"unified search answered without the shared marker: {by_ocs!r}"
    )


async def test_bob_finds_neither_the_private_file_nor_its_content(
    chain_env: dict[str, str],
) -> None:
    """Statement 2: the leak half, with the existence of the object proven in the same run.

    Alice's find is the positive control that matters here: an empty answer for bob only
    means "no permission" once somebody has shown that the object is there and indexed. The
    two searches use the unique token of the private file, so a hit could not be anything
    else.
    """
    marker = chain_env["private_marker"]
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        owner_view = _payload(await c.call_tool("files_search", {"query": marker}))
    owner_paths = {item["path"] for item in owner_view["items"]}
    assert chain_env["private_file"] in owner_paths, (
        f"alice does not even find her own private file: {owner_view!r}"
    )

    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        by_dav = _payload(await c.call_tool("files_search", {"query": marker}))
        by_ocs = _payload(await c.call_tool("unified_search", {"query": marker}))
        # Positive control on bob's side too: the same two calls do answer for him when the
        # object is one he may see, so the two empty results above are a boundary and not a
        # broken search.
        shared = _payload(await c.call_tool("files_search", {"query": chain_env["marker"]}))

    assert by_dav["items"] == [], f"bob sees a file that was never shared with him: {by_dav!r}"
    assert by_dav["count"] == 0
    assert by_ocs["results"] == [], f"a provider leaked alice's private file to bob: {by_ocs!r}"
    assert shared["count"] >= 1, "bob's file search answers nothing at all, so it proves nothing"


async def test_bob_reads_the_shared_file_and_gets_its_marker(chain_env: dict[str, str]) -> None:
    """Statement 3: read permission carries through to the content, not only to the listing.

    A file that is findable but unreadable would be a parity failure in the other direction:
    Nextcloud grants the read, so the connector has to deliver it.
    """
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        result = _payload(await c.call_tool("files_read", {"path": chain_env["shared_file"]}))

    assert result["path"] == chain_env["shared_file"]
    assert chain_env["marker"] in result["content"], (
        f"bob's read of the shared file carries no content marker: {result!r}"
    )


async def test_bob_cannot_write_into_the_read_only_share(chain_env: dict[str, str]) -> None:
    """Statement 4: the create-only tool stops at a boundary Nextcloud draws, not we.

    ``files_upload`` never asks whether it may write; it sends the PUT and reports what comes
    back. Into the read-only share that is a refusal, into bob's own home the same call is a
    created file. The second half is the positive control: without it a broken tool, a wrong
    path or an unreachable chain would look exactly like an enforced permission.
    """
    denied = f"{chain_env['shared_dir']}/bob-tried-{uuid.uuid4().hex[:8]}.md"
    allowed = f"/bob-own-{uuid.uuid4().hex[:8]}.md"
    async with _mcp_session(chain_env["base"], chain_env["bob"], chain_env["bob_pw"]) as c:
        message = await _refusal(c, "files_upload", {"path": denied, "content": "attempt\n"})
        own = _payload(await c.call_tool("files_upload", {"path": allowed, "content": "mine\n"}))

    assert own.get("created") is True, f"bob cannot write into his own home either: {own!r}"
    assert own.get("path") == allowed
    assert chain_env["marker"] not in message, "the refusal carried the marker of alice's file"
    assert message.strip(), "the refusal carried no reason at all"


async def test_create_only_holds_over_the_full_chain(chain_env: dict[str, str]) -> None:
    """Statement 5: the no-overwrite promise (TOOL-09, D-03) measured through the chain.

    The unit tests pin ``If-None-Match: *`` in our own client, and plan 02-06 measured the
    412 under impersonation. What is measured here is the promise as a user meets it: the
    first upload is a created file, the second onto the same path is refused with a reason
    the caller can act on. Nothing is deleted afterwards, because no tool of this server can
    delete anything.
    """
    path = f"/mcp-create-only-{uuid.uuid4().hex[:8]}.md"
    async with _mcp_session(chain_env["base"], chain_env["alice"], chain_env["alice_pw"]) as c:
        first = _payload(await c.call_tool("files_upload", {"path": path, "content": "first\n"}))
        message = await _refusal(c, "files_upload", {"path": path, "content": "second\n"})
        after = _payload(await c.call_tool("files_read", {"path": path}))

    assert first.get("created") is True, f"the first upload did not create the file: {first!r}"
    assert "already exists" in message, f"the refusal names no reason: {message!r}"
    assert "different name" in message, f"the refusal offers no way forward: {message!r}"
    assert after["content"] == "first\n", "the refused second upload changed the file anyway"
