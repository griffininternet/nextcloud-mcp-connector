<!--
Prepared pull request body for nextcloud/context_agent#227.

Target repo:  nextcloud/context_agent
Head branch:  street1983nk:fix/stateless-http-session-compat
Commit:       def1425 (single functional change, Signed-off-by / DCO)
Title:        fix(mcp): make stateless_http configurable and session-capable by default
PR URL:       https://github.com/nextcloud/context_agent/pull/230
Submitted:    2026-08-15

Everything below this comment is the PR body as it will be rendered on GitHub.
-->

## Problem

Clients built on the MCP Python SDK `>= 1.28` (Claude Code, Hermes Agent, Cursor and other
Streamable HTTP clients) cannot stay connected to the context_agent MCP server. The
`initialize` call succeeds and the tools are discovered, but the next request fails:

```
McpError: Session terminated
MCP server 'Nextcloud' failed initial connection after 3 attempts, parking
```

## Cause

`ex_app/lib/main.py` mounts the MCP app with a stateless transport:

```python
http_mcp_app = mcp.http_app("/", transport="http", stateless_http=True)
```

With fastmcp 2.14.7 that flag makes the session manager build a throwaway transport per
request and call `terminate()` once the request is answered
(`StreamableHTTPSessionManager._handle_stateless_request`). Every POST becomes an
independent transaction, so a client that keeps the `ClientSession` it created during
`initialize` is talking to a session that no longer exists.

The same setting also costs both server to client channels on that leg: server initiated
requests raise `NoBackChannelError` and notifications are dropped silently.

## Fix

One functional change, no other scope:

```python
# Session-capable by default: SDK >= 1.28 clients keep the session after initialize
# and fail with "Session terminated" when the transport is stateless. See #227.
_stateless_http = os.getenv("MCP_STATELESS_HTTP", "0").lower() in ("1", "true", "yes")
http_mcp_app = mcp.http_app("/", transport="http", stateless_http=_stateless_http)
```

`os` is already imported in that module, so the diff stays at one file and four lines.
The call keeps the existing fastmcp 2.14.7 `http_app` signature, so this is independent of
the pending fastmcp 3.x bump in #177.

## Backwards compatibility

The default flips from stateless to session-capable, which is what fixes the bug. Nobody
loses the old behaviour: a deployment that deliberately wants a stateless transport, for
example to spread the legacy leg over several workers without sticky routing, sets
`MCP_STATELESS_HTTP=1` and gets exactly what it has today. Session-capable transports keep
their session state in process, so a multi worker deployment that does not set the variable
needs sticky routing.

## Reproduction

The failure only shows with a client on the 1.x SDK line, because a `mcp >= 2` client using
the 2026-07-28 protocol era is sessionless by construction and never reaches the code path
that reads `stateless_http`. That asymmetry is why the server looks healthy in some setups.

1. Run context_agent (2.8.0 or current `main`) on a Nextcloud instance and note the
   Streamable HTTP endpoint URL your MCP client is configured with.

2. Save this as `legacy_client_check.py`:

   ```python
   import asyncio
   import sys

   from mcp import ClientSession
   from mcp.client.streamable_http import streamablehttp_client


   async def check(url: str) -> int:
       headers = {"Authorization": "<the same auth header your MCP client sends>"}
       async with (
           streamablehttp_client(url, headers=headers) as (read, write, _session_id),
           ClientSession(read, write) as session,
       ):
           await session.initialize()
           result = await session.list_tools()
       print(f"tools/list returned {len(result.tools)} tools")
       return 0


   sys.exit(asyncio.run(check(sys.argv[1])))
   ```

3. Run it against the endpoint with the legacy SDK pinned into an isolated environment:

   ```bash
   uv run --isolated --no-project --with "mcp>=1.29,<2" \
       python legacy_client_check.py https://<nextcloud>/<mcp-endpoint>
   ```

Before the fix: `initialize` returns, then `tools/list` raises `McpError: Session terminated`
and the script exits non zero.

After the fix (or with `MCP_STATELESS_HTTP` unset on a patched deployment): the script prints
the number of tools and exits 0. Setting `MCP_STATELESS_HTTP=1` reproduces the old failure,
which is a convenient way to confirm that the switch really is the cause.

## Where the automated regression test lives

Automating this inside this repository would need a second client environment on the 1.x SDK
line talking to a running ExApp container, on top of an already heavy server version matrix
(master, stable33, stable32, stable31 plus the llm2 app). That would add a lot of CI weight
and flakiness for one flag, so the check is automated in our project instead, and it is the
source of the reproduction above:

- Repository: https://github.com/street1983nk/nextcloud-mcp-connector
- `tests/compat/legacy_client_check.py` performs `initialize` plus `tools/list` under
  `mcp>=1.29,<2` in its own environment and exits 1 on "Session terminated".
- `tests/compat/test_client_matrix.py` runs that legacy client and a `mcp>=2,<3` client
  against the same endpoint, so a stateless transport regression fails the build.

Happy to switch this to a plain `stateless_http=False` without the environment variable if
you prefer the smaller surface.

Fixes #227
