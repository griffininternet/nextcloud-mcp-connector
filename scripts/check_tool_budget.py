"""CI gate for the size of the ``tools/list`` response.

Bytes instead of tokens on purpose: deterministic, no model choice, no extra package.
Exit code 1 when the budget is exceeded, plus the five biggest tools so a regression is
immediately attributable.
"""

import asyncio
import json
import sys

from mcp import Client

from mcp_connector.server import mcp

# Starting value, to be fixed at "measured plus 15 percent" in plan 01-14 once all 15
# tools exist. ~24 kB is roughly 6k tokens at ~4 bytes per token.
BUDGET_BYTES = 24_000


async def main() -> int:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()

    payload = result.model_dump(by_alias=True, exclude_none=True, mode="json")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    size = len(blob.encode("utf-8"))
    per_tool = sorted(
        (
            (len(json.dumps(tool, separators=(",", ":"), ensure_ascii=False)), tool["name"])
            for tool in payload["tools"]
        ),
        reverse=True,
    )

    print(f"tools/list: {size} bytes, {len(payload['tools'])} tools, budget {BUDGET_BYTES}")
    for tool_size, name in per_tool[:5]:
        print(f"  {name}: {tool_size} bytes")

    if size > BUDGET_BYTES:
        print("FAIL: tools/list exceeds the token budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
