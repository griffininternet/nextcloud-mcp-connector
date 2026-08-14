"""Client check with the modern SDK (mcp 2.x) against a running Streamable HTTP server.

Usage::

    python tests/compat/modern_client_check.py http://127.0.0.1:8765/mcp

Exit code 0 when ``tools/list`` answered with at least one tool, 1 on any failure. The
script is a standalone process on purpose: it is the same command CI runs, and the
matrix test runs it twice around a server restart to prove there is no session to lose
(SRV-05, D-20).

The Basic credentials may be dummies. ``tools/list`` never touches Nextcloud, so this
check tests the transport and the protocol, not the account.
"""

import base64
import os
import sys

import anyio
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

DEFAULT_USER = "matrix-dummy-user"
DEFAULT_SECRET = "matrix-dummy-app-password"


def basic_header() -> str:
    """Basic credentials from the environment, with harmless defaults."""
    user = os.environ.get("NC_MCP_USER") or DEFAULT_USER
    secret = os.environ.get("NC_MCP_APP_PASSWORD") or DEFAULT_SECRET
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()


async def check(url: str) -> int:
    # Headers belong to the http client in mcp 2.x; streamable_http_client has no
    # headers argument any more.
    async with httpx2.AsyncClient(
        headers={"Authorization": basic_header()},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            result = await client.list_tools()

    count = len(result.tools)
    print(f"modern client: tools/list returned {count} tools")
    return 0 if count else 1


def describe(exc: BaseException) -> str:
    """Flatten an ExceptionGroup so the real cause is visible in CI output."""
    if isinstance(exc, BaseExceptionGroup):
        inner = "; ".join(describe(sub) for sub in exc.exceptions)
        return f"{type(exc).__name__}({inner})"
    return f"{type(exc).__name__}: {exc}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: modern_client_check.py <url>", file=sys.stderr)
        return 2
    try:
        return anyio.run(check, argv[1])
    except Exception as exc:
        print(f"modern client failed: {describe(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
