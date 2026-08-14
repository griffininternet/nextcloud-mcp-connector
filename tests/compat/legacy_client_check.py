"""Client check with the legacy SDK (mcp 1.29) against the very same endpoint.

Usage::

    uv run --isolated --no-project --with "mcp>=1.29,<2" \
        python tests/compat/legacy_client_check.py http://127.0.0.1:8765/mcp

This file must stay importable under mcp 1.x, so it uses the 1.x client API
(``streamablehttp_client`` plus ``ClientSession`` plus an explicit ``initialize``) and
must never be imported by the pytest process, which runs mcp 2.x. The matrix test starts
it as a subprocess in its own environment.

What it reproduces: a legacy client performs the ``initialize`` handshake and then holds
a session. When a server is configured to throw that session away per request, the very
next call fails with "Session terminated" and every server-to-client channel is gone.
That is the failure class of nextcloud/context_agent#227, and running this check green
against our server is the regression test that we never acquired it (D-19, pitfall 1).

Exit code 0 when initialize and tools/list succeeded, 1 on any failure.
"""

import asyncio
import base64
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

DEFAULT_USER = "matrix-dummy-user"
DEFAULT_SECRET = "matrix-dummy-app-password"


def basic_header() -> str:
    user = os.environ.get("NC_MCP_USER") or DEFAULT_USER
    secret = os.environ.get("NC_MCP_APP_PASSWORD") or DEFAULT_SECRET
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()


async def check(url: str) -> int:
    headers = {"Authorization": basic_header()}
    async with (
        streamablehttp_client(url, headers=headers) as (read, write, _session_id),
        ClientSession(read, write) as session,
    ):
        init = await session.initialize()
        result = await session.list_tools()

    count = len(result.tools)
    print(
        f"legacy client: {init.serverInfo.name} answered initialize and "
        f"tools/list returned {count} tools"
    )
    return 0 if count else 1


def describe(exc: BaseException) -> str:
    """Flatten an ExceptionGroup so the real cause is visible in CI output."""
    if isinstance(exc, BaseExceptionGroup):
        inner = "; ".join(describe(sub) for sub in exc.exceptions)
        return f"{type(exc).__name__}({inner})"
    return f"{type(exc).__name__}: {exc}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: legacy_client_check.py <url>", file=sys.stderr)
        return 2
    try:
        return asyncio.run(check(argv[1]))
    except Exception as exc:
        print(f"legacy client failed: {describe(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
