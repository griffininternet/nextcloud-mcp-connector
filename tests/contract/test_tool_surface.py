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
async def test_the_four_file_tools_are_complete_and_read_first() -> None:
    """D-03: search, list, read and upload, and only the last one writes."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ("files_search", "files_list", "files_read", "files_upload"):
        assert name in tools, f"{name} is part of the curated file set (D-03)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    for name in ("files_search", "files_list"):
        annotations = tools[name].annotations
        assert annotations is not None
        assert annotations.read_only_hint is True, f"{name} only reads"
        assert annotations.open_world_hint is False


@pytest.mark.anyio
async def test_files_search_says_in_its_description_that_contents_are_not_matched() -> None:
    """Pitfall 5 belongs in the one sentence the model reads before it calls the tool."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    description = tools["files_search"].description or ""
    assert "not file contents" in description

    schema = tools["files_search"].input_schema
    assert set(schema.get("required", [])) >= {"query"}
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"


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


@pytest.mark.anyio
async def test_contacts_search_is_listed_as_a_pure_read() -> None:
    """D-07: the contacts vertical is read only, and the annotation has to say so."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "contacts_search" in tools, "the contacts read tool is part of the curated set"
    tool = tools["contacts_search"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "contacts_search only reads"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"

    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"query"}


@pytest.mark.anyio
async def test_the_two_deck_tools_are_listed_and_browse_takes_an_enum_level() -> None:
    """D-06: one browse tool with a level parameter, never one tool per Deck level."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ("deck_browse", "deck_create_card"):
        assert name in tools, f"{name} is part of the curated set (D-06)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    browse = tools["deck_browse"]
    annotations = browse.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "deck_browse only reads"
    assert annotations.open_world_hint is False

    schema = browse.input_schema
    assert schema["properties"]["level"]["enum"] == ["boards", "stacks", "cards"], (
        "the level is an enum in the schema, not a free string the model has to guess"
    )
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"

    create = tools["deck_create_card"].annotations
    assert create is not None
    assert create.read_only_hint is False, "deck_create_card writes"
    assert create.destructive_hint is False, "it can only create, never replace or delete"
    assert create.idempotent_hint is False, "a second call creates a second card"
    assert create.open_world_hint is False


@pytest.mark.anyio
async def test_there_is_no_tool_per_deck_level() -> None:
    """The anti-pattern D-06 rules out: three tools would cost slots without any gain."""
    async with Client(mcp, raise_exceptions=True) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    forbidden = {"deck_list_boards", "deck_list_stacks", "deck_list_cards", "deck_read_card"}
    assert not (names & forbidden), f"deck_browse covers these levels: {names & forbidden}"


@pytest.mark.anyio
async def test_unified_search_is_listed_as_a_pure_read_over_all_providers() -> None:
    """D-08 and TOOL-06: one cloud wide read, and the expectation management is in the text."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "unified_search" in tools, "the cloud wide search is part of the curated set"
    tool = tools["unified_search"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "unified_search only reads"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"

    assert "not file contents" in (tool.description or ""), (
        "pitfall 5 belongs in the sentence the model reads before it calls the tool"
    )

    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"query"}
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"
    assert schema["properties"]["providers"]["type"] == "string", (
        "an optional string beats an anyOf of list and null (schema diet)"
    )


@pytest.mark.anyio
async def test_search_is_a_read_tool_and_the_documented_exception_to_the_schema_diet() -> None:
    """D-14: an output schema exists exactly where a client reads it, and ChatGPT does."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "search" in tools, "the ChatGPT profile tool is named exactly search (TOOL-07)"
    tool = tools["search"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "search only reads"
    assert annotations.open_world_hint is False

    assert tool.output_schema is not None, "ChatGPT expects structured output from search"
    assert tools["unified_search"].output_schema is None, (
        "the exception stays an exception: the cloud wide search keeps the diet"
    )
    assert set(tool.input_schema.get("properties", {})) == {"query"}


@pytest.mark.anyio
async def test_calendar_create_event_is_annotated_as_create_only() -> None:
    """Not idempotent, and honestly so: If-None-Match refuses the second identical call."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "calendar_create_event" in tools, "the calendar write path must be exposed"
    tool = tools["calendar_create_event"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is False, "calendar_create_event writes"
    assert annotations.destructive_hint is False, "it can only create, never replace or delete"
    assert annotations.idempotent_hint is False, "a second call creates a second event"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"

    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"summary", "start", "end"}
