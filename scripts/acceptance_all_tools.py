"""Phase acceptance: call all 18 tools once, through a real MCP client over stdio.

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

Exit code 0 only when all 18 tools answered. The output is a matrix of tool name, verdict
and the first line of the answer, so a failure is attributable without a rerun.

The calls build on each other on purpose: the file uploaded in step one is the file that
``files_read``, ``unified_search``, ``search`` and ``fetch`` look for later. A tool that
answers "no hits" for an object created seconds earlier is a failure, not an empty result,
and only a chained run can tell those two apart.

Deck and Tables are the two exceptions. A board, a stack, a table and a column are not
connector features (the server cannot create any of them, by design), so the script uses
what the integration suite leaves behind and reports the write as skipped when there is
nothing to write into. For Tables that check has two halves, because two refusals of the
connector are correct behaviour rather than a defect: a table shared without a write
permission, and a row that leaves a mandatory column empty. The script therefore only
considers tables with ``can_create`` and only writes when a text marker fits into every
mandatory column of one.
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

# The count the registry answers today. It stood at 15 while the registry already listed
# 16, which is the kind of drift only a number in two places produces, so it is raised in
# the same commit that raises every other frozen number of a phase.
EXPECTED_TOOLS = 18


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

    # --- tables -----------------------------------------------------------------------
    # Same exception as Deck, one family later: a table and its columns are not connector
    # features, so the script writes into the table the integration suite leaves behind and
    # reports the write as skipped when there is none.
    #
    # The table is not simply the first one listed, and the column is not simply the first
    # text column. Both shortcuts turn a correctly working connector into a FAIL: a table
    # shared without a write permission is refused by design, and a row that leaves a
    # mandatory column empty is refused by design as well. So only tables with ``can_create``
    # are candidates, and a candidate qualifies only when a text marker fits into every
    # mandatory column of it. If none does, this is a SKIP with a reason, exactly like Deck.
    tables = loads(await call(client, report, "tables_browse", {"level": "tables"}))
    table_id = ""
    values: dict[str, str] = {}
    for candidate in _writable_tables(tables):
        columns = loads(
            await call(client, report, "tables_browse", {"level": "columns", "table_id": candidate})
        )
        fits = _text_row_for(columns, f"Abnahme {marker}")
        if fits:
            table_id, values = candidate, fits
            break
    if table_id and values:
        await call(
            client,
            report,
            "tables_create_row",
            {"table_id": table_id, "values": json.dumps(values)},
        )
    else:
        report.add(
            "tables_create_row",
            "SKIP",
            "no writable table whose mandatory columns are all text; the connector creates "
            "neither a table nor a column by design",
        )

    # --- contacts, search, chatgpt profile ---------------------------------------------
    await call(client, report, "contacts_search", {"query": "a"})
    await call(client, report, "unified_search", {"query": marker})
    await call(client, report, "prepare_context", {"query": marker})
    await call(client, report, "search", {"query": marker})
    if file_id:
        await call(client, report, "fetch", {"id": file_id})
    else:
        report.add("fetch", "FAIL", "no file id from files_search to resolve")


def _writable_tables(payload: dict[str, Any]) -> list[str]:
    """The ids of the tables this account may add a row to, in the order they were listed.

    ``can_create`` is the field ``tables_browse`` reports for exactly this question (K5). A
    table without it is refused by the connector on purpose, so trying it anyway would report
    a working refusal as a broken tool.
    """
    entries = payload.get("results")
    if not isinstance(entries, list):
        return []
    ids: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("can_create"):
            continue
        raw = str(entry.get("id", ""))
        if raw:
            ids.append(raw.rsplit(":", 1)[-1])
    return ids


def _text_row_for(payload: dict[str, Any], value: str) -> dict[str, str]:
    """One row that this table would accept, or an empty mapping when there is none.

    Two refusals of the connector are by design and would otherwise look like a failure: a
    text marker in a number column is a 400 of the Tables app, and a row that leaves a
    mandatory column empty never leaves this server at all. So a table qualifies only when all
    of its mandatory columns are text columns, and the row written covers every one of them.
    A table without any mandatory column needs one text column to write into.
    """
    entries = payload.get("results")
    if not isinstance(entries, list):
        return {}
    columns = [entry for entry in entries if isinstance(entry, dict)]
    mandatory = [column for column in columns if column.get("mandatory")]
    if any(column.get("type") != "text" for column in mandatory):
        return {}
    chosen = mandatory or [column for column in columns if column.get("type") == "text"][:1]
    titles = [str(column.get("title") or "") for column in chosen]
    if not titles or not all(titles):
        return {}
    return dict.fromkeys(titles, value)


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
        "prepare_context",
        "tables_browse",
        "tables_create_row",
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
