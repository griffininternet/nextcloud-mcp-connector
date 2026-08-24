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
#   Measurement 2026-08-21, same 20 tools, cursor description of tables_browse and
#               talk_browse says which level hands one out (review finding IN-04): 14358 bytes
#   Budget      unchanged at 15000, because the measurement fits below it
#
#   Measurement 2026-08-24, all 21 curated tools registered (mail_browse of phase 10): 15736
#               bytes
#   Budget      15736 + 15 percent = 18096, rounded up to the next 500 = 18500 bytes
#   Zwischenstand: this raise is an intermediate one, and it is marked as such on purpose.
#               TOOL-15 in phase 11 re-anchors the gate on the final measurement of that
#               phase, so nobody raises an already generous number a second time out of
#               habit (trap 14 of the phase 10 research).
#
# The older lines stay where they are: a regression is only attributable when the number it
# regressed from is still readable. The first 2026-08-21 line is the tables_browse and
# tables_create_row pair of phase 8 (751 and 780 bytes), which took the surface past the
# gate of phase 1 exactly as it was meant to. The second is the talk_browse and talk_send
# pair of phase 9 (861 and 648 bytes), and it raises nothing: a budget is lifted against a
# measurement that needs it, never out of habit. The third is 46 bytes of wording, spent
# because both tools now refuse a cursor on a level that has none and the schema is where a
# model reads which level that is; it left 642 bytes of headroom. The fourth is the single
# ``mail_browse`` of phase 10 at 1377 bytes, which is exactly the twenty-first tool the
# paragraph below was written for: it tripped the gate at 15000, and the gate did its job.
#
# The headroom is for wording, not for a new tool: at ~4 bytes per token the whole surface
# costs roughly 3.9k tokens in every single session of every client. A twenty-second tool or a
# description that grows into a paragraph is supposed to trip this gate, so the decision
# gets made on purpose instead of by accident. Raising the number is allowed, but only
# together with a new measurement line above, so a regression stays attributable.
BUDGET_BYTES = 18_500

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
#
#   Measurement 2026-08-24, biggest tool is ``mail_browse`` at 1377 bytes: unchanged, and
#   deliberately so. This ceiling is the real guard, so a tool that reaches it gets a shorter
#   description and never a higher limit (A5 of the phase 10 research). ``mail_browse`` was
#   1585 bytes when it was first written and it was cut, not exempted.
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
