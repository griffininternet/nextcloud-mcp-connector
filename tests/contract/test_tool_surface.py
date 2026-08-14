"""Contract test for the tool surface exposed over MCP.

RED on purpose in plan 01-01: ``mcp_connector.server`` does not exist yet. Plan 01-02
delivers the walking skeleton (``files_read`` over stdio) and turns this file green.
The full check of all 15 curated tools follows in plan 01-14; here we pin exactly the
one capability the skeleton must provide.
"""

import pytest
from mcp import Client

from mcp_connector.server import mcp


@pytest.mark.anyio
async def test_files_read_is_exposed_with_honest_annotations() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "files_read" in tools, "the walking skeleton must expose files_read"

    tool = tools["files_read"]
    annotations = tool.annotations
    assert annotations is not None, "files_read has no annotations"
    assert annotations.read_only_hint is True, "files_read only reads"
    assert annotations.open_world_hint is False, "the tool talks to one known Nextcloud"
    assert tool.output_schema is None, (
        "files_read must run with structured_output=False (schema diet)"
    )


@pytest.mark.anyio
async def test_files_upload_is_annotated_as_create_only() -> None:
    """The only write tool of the phase must say out loud what it does and does not do."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "files_upload" in tools, "the create-only write path must be exposed"

    tool = tools["files_upload"]
    annotations = tool.annotations
    assert annotations is not None, "files_upload has no annotations"
    assert annotations.read_only_hint is False, "files_upload writes"
    assert annotations.destructive_hint is False, "it can only create, never replace"
    assert annotations.idempotent_hint is False, "a second call on the same path fails"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"
    assert "never overwrites" in (tool.description or ""), (
        "the constraint belongs in the description the model reads"
    )


@pytest.mark.anyio
async def test_the_three_notes_tools_are_listed_with_honest_annotations() -> None:
    """``tools/list`` stays static: Notes appears here even where the app is not installed."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ("notes_search", "notes_read", "notes_create"):
        assert name in tools, f"{name} is part of the curated set (D-05)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    for name in ("notes_search", "notes_read"):
        annotations = tools[name].annotations
        assert annotations is not None
        assert annotations.read_only_hint is True, f"{name} only reads"
        assert annotations.open_world_hint is False

    create = tools["notes_create"].annotations
    assert create is not None
    assert create.read_only_hint is False, "notes_create writes"
    assert create.destructive_hint is False, "it can only create, never replace or delete"
    assert create.idempotent_hint is False, "a second call creates a second note"
    assert create.open_world_hint is False


@pytest.mark.anyio
async def test_calendar_list_events_demands_a_window_with_a_timezone() -> None:
    """D-04: the window is not optional, and the model must see that in the schema."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "calendar_list_events" in tools, "the calendar read tool is part of the set"
    tool = tools["calendar_list_events"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "calendar_list_events only reads"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"

    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"start", "end"}
    assert "+02:00" in schema["properties"]["start"]["description"], (
        "the example value keeps the model from guessing the format"
    )
