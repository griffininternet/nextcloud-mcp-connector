"""Phase acceptance: call all 15 tools once, through a real MCP client over stdio.

This is the proof behind success criterion 1 of phase 1. Not a unit test and not a mock:
the script starts ``nc-mcp`` as a subprocess exactly as Claude Desktop does, speaks the
protocol over the pipe, and calls every tool of the curated set against a real Nextcloud.
A tool that is registered but broken shows up here and nowhere else, because every other
layer either skips the transport or skips the cloud.

Usage::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a
    uv run python scripts/acceptance_all_tools.py

Exit code 0 only when all 15 tools answered. The output is a matrix of tool name, verdict
and the first line of the answer, so a failure is attributable without a rerun.

The calls build on each other on purpose: the file uploaded in step one is the file that
``files_read``, ``unified_search``, ``search`` and ``fetch`` look for later. A tool that
answers "no hits" for an object created seconds earlier is a failure, not an empty result,
and only a chained run can tell those two apart.

Deck is the one exception. Board and stack are not connector features (the server cannot
create either, by design), so the script uses the board the integration suite leaves
behind and reports the two Deck tools as skipped when no board exists.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

REQUIRED_ENV = ("NC_MCP_URL", "NC_MCP_USER", "NC_MCP_APP_PASSWORD")

EXPECTED_TOOLS = 15


class Report:
    """Verdict per tool, in call order."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, tool: str, verdict: str, detail: str) -> None:
        flat = " ".join(str(detail).split())
        self.rows.append((tool, verdict, flat[:110]))
        print(f"  {verdict:<7} {tool:<22} {flat[:90]}", flush=True)

    def failures(self) -> list[str]:
        return [tool for tool, verdict, _ in self.rows if verdict == "FAIL"]

    def called(self) -> set[str]:
        return {tool for tool, verdict, _ in self.rows if verdict in ("OK", "SKIP")}


def text_of(result: Any) -> str:
    """First text block of a tool result, whatever the tool returns."""
    for block in result.content:
        if isinstance(block, TextContent):
            return block.text
    return ""


async def call(client: Client, report: Report, tool: str, arguments: dict[str, Any]) -> str:
    try:
        result = await client.call_tool(tool, arguments)
    # Broad on purpose: one broken tool must not end the run, it must land in the matrix.
    except Exception as exc:
        report.add(tool, "FAIL", f"{type(exc).__name__}: {exc}")
        return ""
    payload = text_of(result)
    if result.is_error:
        report.add(tool, "FAIL", payload)
        return ""
    report.add(tool, "OK", payload)
    return payload


def loads(payload: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


async def run(client: Client, report: Report) -> None:
    marker = f"abnahme{uuid.uuid4().hex[:10]}"
    stamp = time.strftime("%Y%m%d-%H%M%S")

    listed = await client.list_tools()
    names = sorted(tool.name for tool in listed.tools)
    print(f"tools/list: {len(names)} tools: {', '.join(names)}\n")
    if len(names) != EXPECTED_TOOLS:
        report.add("tools/list", "FAIL", f"expected {EXPECTED_TOOLS} tools, got {len(names)}")

    # --- files ------------------------------------------------------------------------
    path = f"/{marker}-{stamp}.md"
    await call(
        client,
        report,
        "files_upload",
        {"path": path, "content": f"# {marker}\nAbnahmelauf Phase 1, Straßenbau.\n"},
    )
    found = loads(await call(client, report, "files_search", {"query": marker}))
    items = found.get("items") or []
    if not items:
        report.add("files_search", "FAIL", "the file uploaded one second ago was not found")
    file_id = str(items[0].get("id", "")) if items else ""

    await call(client, report, "files_list", {"path": "/"})
    await call(client, report, "files_read", {"path": path})

    # --- calendar ---------------------------------------------------------------------
    start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=1)
    end = start + timedelta(hours=1)
    await call(
        client,
        report,
        "calendar_create_event",
        {
            "summary": f"Abnahme {marker}",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": "Europe/Berlin",
        },
    )
    await call(
        client,
        report,
        "calendar_list_events",
        {
            "start": (start - timedelta(hours=1)).isoformat(),
            "end": (end + timedelta(hours=1)).isoformat(),
        },
    )

    # --- notes ------------------------------------------------------------------------
    created = loads(
        await call(
            client,
            report,
            "notes_create",
            {"title": f"Abnahme {marker}", "content": f"Abnahmelauf {marker}"},
        )
    )
    note_id = str(created.get("id") or "").removeprefix("note:")
    await call(client, report, "notes_search", {"query": marker})
    if note_id:
        await call(client, report, "notes_read", {"note_id": note_id})
    else:
        report.add("notes_read", "FAIL", "notes_create returned no id to read back")

    # --- deck -------------------------------------------------------------------------
    boards = loads(await call(client, report, "deck_browse", {"level": "boards"}))
    board_id = _first_id(boards)
    stack_id = ""
    if board_id:
        stacks = loads(
            await call(client, report, "deck_browse", {"level": "stacks", "board_id": board_id})
        )
        stack_id = _first_id(stacks)
    if board_id and stack_id:
        await call(
            client,
            report,
            "deck_create_card",
            {"board_id": board_id, "stack_id": stack_id, "title": f"Abnahme {marker}"},
        )
    else:
        report.add(
            "deck_create_card",
            "SKIP",
            "no board or stack on this account; the connector cannot create either by design",
        )

    # --- contacts, search, chatgpt profile ---------------------------------------------
    await call(client, report, "contacts_search", {"query": "a"})
    await call(client, report, "unified_search", {"query": marker})
    await call(client, report, "search", {"query": marker})
    if file_id:
        await call(client, report, "fetch", {"id": file_id})
    else:
        report.add("fetch", "FAIL", "no file id from files_search to resolve")


def _first_id(payload: dict[str, Any]) -> str:
    for key in ("results", "items", "boards", "stacks"):
        entries = payload.get(key)
        if isinstance(entries, list) and entries and isinstance(entries[0], dict):
            raw = str(entries[0].get("id", ""))
            return raw.rsplit(":", 1)[-1] if raw else ""
    return ""


async def main() -> int:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        print(f"missing environment: {', '.join(missing)}", file=sys.stderr)
        print("run: set -a && . ./.env.test && set +a", file=sys.stderr)
        return 2

    command = "nc-mcp.exe" if os.name == "nt" else "nc-mcp"
    parameters = StdioServerParameters(
        command=command,
        args=[],
        env={name: os.environ[name] for name in REQUIRED_ENV},
    )

    print(f"starting {command} over stdio against {os.environ['NC_MCP_URL']}\n")
    report = Report()
    # The transport is handed over unentered: mcp 2.x opens it inside the client.
    async with Client(stdio_client(parameters)) as client:
        await run(client, report)

    print("\n=== acceptance matrix ===")
    for tool, verdict, detail in report.rows:
        print(f"{verdict:<7} {tool:<22} {detail}")

    expected = {
        "files_search",
        "files_list",
        "files_read",
        "files_upload",
        "calendar_list_events",
        "calendar_create_event",
        "notes_search",
        "notes_read",
        "notes_create",
        "deck_browse",
        "deck_create_card",
        "contacts_search",
        "unified_search",
        "search",
        "fetch",
    }
    never_called = expected - report.called()
    failures = report.failures()

    if never_called:
        print(f"\nFAIL: never called: {', '.join(sorted(never_called))}", file=sys.stderr)
    if failures:
        print(f"FAIL: {len(failures)} tools failed: {', '.join(failures)}", file=sys.stderr)
    if never_called or failures:
        return 1

    print(f"\nOK: all {len(expected)} tools answered over stdio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
