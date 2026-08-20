"""Contract test for the tool surface exposed over MCP.

RED on purpose in plan 01-01: ``mcp_connector.server`` does not exist yet. Plan 01-02
delivers the walking skeleton (``files_read`` over stdio) and turns this file green.
Plan 01-14 closes the phase and widens the file to the full surface: the section
"the whole surface at once" below checks all tools in one pass instead of one
vertical at a time, so a new tool, a wrong annotation, a stray output schema or a
user parameter cannot slip in between two plans.

The sixteenth tool, ``prepare_context``, arrived in plan 04-02 and had to be entered here
on purpose: the frozen literal below refused it until then, which is exactly the job of
this file (D-58).
"""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from mcp import Client

from mcp_connector.server import mcp

README = Path(__file__).resolve().parents[2] / "README.md"
DOCS = Path(__file__).resolve().parents[2] / "docs"

# The curated set (D-03 to D-09). A set comparison, not a subset check: a sixteenth tool
# fails this file just as loudly as a missing one. Counter proof for the reviewer: adding
# ``@mcp.tool`` for a ``files_delete`` anywhere under ``server/reg_*.py`` turns
# ``test_the_curated_set_is_complete_and_only_the_chatgpt_profile_has_a_schema`` and
# ``test_every_tool_carries_honest_annotations`` red, because both compare against this
# frozen literal and never against ``len(tools)`` alone.
EXPECTED_TOOLS = {
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
    "search",
    "fetch",
}

# The four write paths. Everything else in EXPECTED_TOOLS only reads (D-16).
CREATE_TOOLS = {"files_upload", "calendar_create_event", "notes_create", "deck_create_card"}

# The documented exception to the schema diet: ChatGPT reads structured content (D-14).
STRUCTURED_TOOLS = {"search", "fetch"}

# A parameter that names a user turns this server into a confused deputy: the credentials
# come from the auth channel, so a tool that also accepts a user name would let the model
# ask for someone else's data (T-01-95).
FORBIDDEN_PROPERTIES = {"user", "username", "uid", "userid", "owner"}


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
async def test_prepare_context_is_listed_as_a_bundling_read() -> None:
    """TOOL-08 and D-58: two parameters, no output schema, and an honest warning.

    The description carries the D-57 sentence for the same reason the unverified client
    callout exists in the consent page: the bundle lifts text other people wrote into the
    context of an assistant, and the client deserves to know that before it calls.
    """
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert "prepare_context" in tools, "the bundling read is part of the curated set"
    tool = tools["prepare_context"]

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "prepare_context only reads"
    assert annotations.open_world_hint is False
    assert tool.output_schema is None, "structured_output=False (schema diet)"

    assert "third parties" in (tool.description or ""), (
        "D-57: the client is told that the bundle can contain content written by others"
    )

    schema = tool.input_schema
    assert set(schema.get("required", [])) >= {"query"}
    assert set(schema.get("properties", {})) == {"query", "detail"}, (
        "two parameters and no more: every field is paid for in every session (D-56)"
    )
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"
    assert schema["properties"]["detail"]["type"] == "string", (
        "a string beats a literal enum, which would push an anyOf into the schema (D-14)"
    )
    for value in ("short", "full"):
        assert value in schema["properties"]["detail"]["description"], (
            "the two values that work belong in the sentence the model reads"
        )


@pytest.mark.anyio
async def test_the_curated_set_is_complete_and_only_the_chatgpt_profile_has_a_schema() -> None:
    """The whole surface in one assertion: 16 tools, and the diet holds for 14 of them."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == EXPECTED_TOOLS
    assert len(tools) == 16, "the curated set is 16 tools, no more and no fewer"

    with_schema = {name for name, tool in tools.items() if tool.output_schema is not None}
    assert with_schema == STRUCTURED_TOOLS, (
        "an output schema exists exactly where a client reads it (D-14)"
    )


@pytest.mark.anyio
async def test_fetch_is_a_read_tool_with_the_openai_parameter_name() -> None:
    """TOOL-07: the parameter is called ``id``, and a connector that renames it breaks."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    tool = tools["fetch"]
    annotations = tool.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "fetch only reads"
    assert annotations.open_world_hint is False

    assert set(tool.input_schema.get("properties", {})) == {"id"}
    assert set(tool.input_schema.get("required", [])) == {"id"}


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


# ---------------------------------------------------------------------------
# The whole surface at once (plan 01-14, phase acceptance)
#
# The tests above pin one vertical each, which is the right granularity while a
# vertical is being built. These four walk the complete registry instead, so the
# checks hold for a tool nobody thought about when this file was written.
# ---------------------------------------------------------------------------


def _properties(schema: dict[str, Any]) -> list[tuple[str, Any]]:
    """Every property name in a JSON schema, including nested ones and ``$defs``.

    A shallow pass over ``properties`` would miss exactly the case worth catching: a
    parameter that arrives as a nested model and therefore lives under ``$defs``.
    """
    found: list[tuple[str, Any]] = []
    stack: list[Any] = [schema]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("properties", "$defs", "definitions") and isinstance(value, dict):
                    found.extend(value.items())
                stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
    return found


@pytest.mark.anyio
async def test_every_tool_carries_honest_annotations() -> None:
    """D-16 over the whole registry: four create-only tools, twelve pure reads."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == EXPECTED_TOOLS, "the curated set is frozen (D-03 to D-09)"
    assert CREATE_TOOLS < EXPECTED_TOOLS, "every write tool must be part of the curated set"

    for name, tool in sorted(tools.items()):
        annotations = tool.annotations
        assert annotations is not None, f"{name} has no annotations"
        assert annotations.open_world_hint is False, (
            f"{name} talks to one known Nextcloud, never to the open web"
        )
        if name in CREATE_TOOLS:
            assert annotations.read_only_hint is False, f"{name} writes and must say so"
            assert annotations.destructive_hint is False, (
                f"{name} can only create, never replace or delete"
            )
            assert annotations.idempotent_hint is False, (
                f"a second {name} call is a second object, not a no-op"
            )
        else:
            assert annotations.read_only_hint is True, f"{name} only reads"


@pytest.mark.anyio
async def test_every_tool_has_a_non_empty_description_and_only_two_have_an_output_schema() -> None:
    """The description is what the model reads before it decides; empty is not an option."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name, tool in sorted(tools.items()):
        description = (tool.description or "").strip()
        assert description, f"{name} has no description"
        assert len(description) >= 20, f"{name} has a description too short to be useful"

    with_schema = {name for name, tool in tools.items() if tool.output_schema is not None}
    assert with_schema == STRUCTURED_TOOLS, (
        "an output schema exists exactly at search and fetch, nowhere else (D-14)"
    )


@pytest.mark.anyio
async def test_no_input_schema_accepts_a_user_parameter() -> None:
    """T-01-95: the caller is the auth channel, never a tool argument."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == EXPECTED_TOOLS, "the confused deputy check must cover all 16 schemas"

    findings: list[str] = []
    for name, tool in sorted(tools.items()):
        schema = tool.input_schema or {}
        for property_name, _definition in _properties(schema):
            if property_name.lower() in FORBIDDEN_PROPERTIES:
                findings.append(f"{name}.{property_name}")

    assert findings == [], (
        "a tool that takes a user name lets the model act as someone else: " + ", ".join(findings)
    )


@pytest.mark.anyio
async def test_the_readme_permission_table_matches_the_live_registry() -> None:
    """D-16: the documented permission level is generated from the same truth, or it lies."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    documented: dict[str, str] = {}
    for line in README.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[1] not in ("read", "create-only"):
            continue
        documented[cells[0].strip("`")] = cells[1]

    assert set(documented) == set(tools), (
        "the README tool table and the registry must list the same names"
    )
    for name, level in sorted(documented.items()):
        expected = "create-only" if name in CREATE_TOOLS else "read"
        assert level == expected, f"README calls {name} {level}, the registry says {expected}"


def test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from() -> None:
    """IN-04: a page may record a run with an old count, it may not leave it unexplained.

    Two kinds of number live in ``docs/``. A statement about the product ("all 16 tools")
    has to be the number this registry answers. A dated evidence line ("connected, 15 tools
    listed") is a record of a run and stays as it was recorded, and a reader who counts both
    holds one of them for wrong unless the page says which is which. So a page that names a
    count other than the current one has to point at the file that holds the truth, and that
    pointer is this one: the number lives in a test, never in a document.
    """
    holder = "tests/contract/test_tool_surface.py"
    current = len(EXPECTED_TOOLS)
    unexplained: list[str] = []

    for page in [*sorted(DOCS.glob("*.md")), README]:
        text = page.read_text(encoding="utf-8")
        explained = holder in text
        for number, line in _counted_tools(text):
            if number != current and not explained:
                unexplained.append(f"{page.name}: {line.strip()}")

    assert unexplained == [], (
        "a page naming a tool count other than "
        f"{current} has to point at {holder}: " + "; ".join(unexplained)
    )


def _counted_tools(text: str) -> Iterator[tuple[int, str]]:
    """Every place a page names a number of tools, with the line it stands in."""
    counts = re.compile(r"tools=(\d+)|(\d+)\s+tools\b")
    for line in text.splitlines():
        for match in counts.finditer(line):
            yield int(match.group(1) or match.group(2)), line
