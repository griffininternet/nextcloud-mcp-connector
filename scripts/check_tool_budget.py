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

# Armed value, not a decorative one. A budget far above the measurement never fails and
# therefore never protects anything, which was the state until the end of phase 1.
#
#   Measurement 2026-08-14, all 15 curated tools registered: 10643 bytes
#   Budget      10643 + 15 percent = 12239, rounded up to the next 500 = 12500 bytes
#
#   Measurement 2026-08-21, all 18 curated tools registered: 12801 bytes
#   Budget      12801 + 15 percent = 14721, rounded up to the next 500 = 15000 bytes
#
#   Measurement 2026-08-21, all 20 curated tools registered: 14312 bytes
#   Budget      unchanged at 15000, because the measurement fits below it
#
# The older lines stay where they are: a regression is only attributable when the number it
# regressed from is still readable. The first 2026-08-21 line is the tables_browse and
# tables_create_row pair of phase 8 (751 and 780 bytes), which took the surface past the
# gate of phase 1 exactly as it was meant to. The second is the talk_browse and talk_send
# pair of phase 9 (861 and 648 bytes), and it raises nothing: a budget is lifted against a
# measurement that needs it, never out of habit, and this one leaves 688 bytes of headroom.
#
# The headroom is for wording, not for a new tool: at ~4 bytes per token the whole surface
# costs roughly 3.6k tokens in every single session of every client. A twenty-first tool or a
# description that grows into a paragraph is supposed to trip this gate, so the decision
# gets made on purpose instead of by accident. Raising the number is allowed, but only
# together with a new measurement line above, so a regression stays attributable.
BUDGET_BYTES = 15_000

# The second claim, and the one that actually reports a regression. A total with headroom
# says nothing about a single tool: today's outlier ``calendar_create_event`` sits at 1351
# bytes, so one new tool with a paragraph of prose fits under the total while being twice
# the size of everything around it. That is the change worth catching, and only a per tool
# ceiling catches it.
#
# The unit is the same as the one of the total, and it says bytes because it measures bytes
# (review finding IN-03). Until 2026-08-21 this one number was measured on characters while
# the total was measured on the UTF-8 encoding, so a tool with non-ASCII text in its
# description was undercounted against its own ceiling. Both are bytes now.
#
#   Measurement 2026-08-21, per tool on bytes for the first time: unchanged, biggest tool
#   ``calendar_create_event`` at 1351 bytes. Every description of this surface is ASCII, so
#   the two units happen to agree today; the point of the change is that they keep agreeing
#   when one of them is not ASCII any more.
MAX_TOOL_BYTES = 1400


async def main() -> int:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()

    payload = result.model_dump(by_alias=True, exclude_none=True, mode="json")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    size = len(blob.encode("utf-8"))
    per_tool = sorted(
        (
            (
                # ``.encode("utf-8")`` and not ``len`` of the string: the same unit as the
                # total above, so the two limits of this gate measure the same thing (IN-03).
                len(json.dumps(tool, separators=(",", ":"), ensure_ascii=False).encode("utf-8")),
                tool["name"],
            )
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

    too_big = [(name, tool_size) for tool_size, name in per_tool if tool_size > MAX_TOOL_BYTES]
    if too_big:
        for name, tool_size in too_big:
            print(
                f"FAIL: {name} is {tool_size} bytes, above the per tool ceiling "
                f"of {MAX_TOOL_BYTES}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
