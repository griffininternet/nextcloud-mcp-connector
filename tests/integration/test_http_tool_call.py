"""AUTH-01: a real tool call over HTTP with a real app password (opt-in).

Everything else about the passthrough mode is unit tested, but one thing cannot be: that
the Basic credentials of an HTTP request actually reach Nextcloud and that Nextcloud
accepts them. That needs three real things at once, a uvicorn process, a Streamable HTTP
client and a running Nextcloud, and it is exactly what this file wires together.

The server subprocess is started **without** ``NC_MCP_USER`` and without
``NC_MCP_APP_PASSWORD``. If the round trip works anyway, the identity can only have come
from the request header, which is the whole claim of D-12.

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

import base64
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

REPO_ROOT = Path(__file__).resolve().parents[2]


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def basic(user: str, secret: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()


@pytest.fixture
def live(live_env: dict[str, str | None]) -> dict[str, str]:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")
    return {key: str(value) for key, value in live_env.items()}


@pytest.fixture
def server(live: dict[str, str]) -> Iterator[str]:
    """A uvicorn subprocess in passthrough mode, pointed at the test Nextcloud."""
    port = free_port()
    env = {key: value for key, value in os.environ.items()}
    # The point of the test: the process itself has no Nextcloud account.
    env.pop("NC_MCP_USER", None)
    env.pop("NC_MCP_APP_PASSWORD", None)
    env.pop("NC_MCP_STATIC_BEARER", None)
    env["NC_MCP_URL"] = live["base_url"]
    env["NC_MCP_ALLOWED_HOSTS"] = "127.0.0.1"

    process = subprocess.Popen(  # noqa: S603 - fixed command from our own package
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mcp_connector.entry_http:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    deadline = time.monotonic() + 60.0
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                process.kill()
                output = process.stdout.read() if process.stdout else ""
                pytest.fail(f"uvicorn exited early: {output[:2000]}")
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health", timeout=2.0).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        else:  # pragma: no cover - only on a hung server
            pytest.fail("the MCP server did not become healthy")
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:  # pragma: no cover
            process.kill()
            process.wait(timeout=30)


async def call_tool(url: str, authorization: str | None, name: str, arguments: dict) -> str:
    """Call one tool over Streamable HTTP and return the text of the answer."""
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx2.AsyncClient(
        headers=headers, timeout=httpx2.Timeout(30.0, read=120.0)
    ) as http:
        async with Client(streamable_http_client(url, http_client=http)) as client:
            result = await client.call_tool(name, arguments)
    texts = [block.text for block in result.content if getattr(block, "text", None)]
    joined = "\n".join(texts)
    if result.is_error:
        raise AssertionError(f"tool error: {joined}")
    return joined


def describe(exc: BaseException) -> str:
    """Flatten an ExceptionGroup: anyio wraps a JSON-RPC error into a TaskGroup failure."""
    if isinstance(exc, BaseExceptionGroup):
        return "; ".join(describe(sub) for sub in exc.exceptions)
    return f"{type(exc).__name__}: {exc}"


async def call_tool_error(url: str, authorization: str | None, name: str, arguments: dict) -> str:
    """Call a tool that is expected to fail and return the message the caller sees."""
    try:
        answer = await call_tool(url, authorization, name, arguments)
    except AssertionError as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001 - the transport error is the subject here
        return describe(exc)
    raise AssertionError(f"expected a failure, got: {answer}")


async def test_a_forwarded_app_password_creates_and_reads_a_note(
    server: str, live: dict[str, str]
) -> None:
    """AUTH-01: the account comes from the request, the data comes from Nextcloud."""
    title = f"MCP-HTTP {uuid.uuid4().hex[:8]}"
    content = f"# {title}\nGrüße über HTTP\n"
    header = basic(live["user"], live["secret"])

    created = json.loads(
        await call_tool(server, header, "notes_create", {"title": title, "content": content})
    )
    assert created["title"] == title
    assert created["id"].startswith("note:")

    read = json.loads(await call_tool(server, header, "notes_read", {"note_id": created["id"]}))
    assert read["content"] == content


async def test_a_wrong_app_password_is_rejected_without_a_retry(
    server: str, live: dict[str, str]
) -> None:
    message = await call_tool_error(
        server,
        basic(live["user"], "definitely-not-the-app-password"),
        "notes_search",
        {"query": "protokoll"},
    )
    assert "app password" in message.lower()


async def test_a_request_without_credentials_never_reaches_nextcloud(server: str) -> None:
    message = await call_tool_error(server, None, "notes_search", {"query": "protokoll"})
    assert "Basic credentials" in message
