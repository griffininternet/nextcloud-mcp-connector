"""Contract test for the audit boundary: which parameter names may reach a log entry.

Two threats meet in this file. T-18-01 is a parameter value or a result body in the log, and
the answer to it is that ``audit/allowlist.py`` holds names alone, with the payload names on
a block list so none of them can quietly grow a value beside it one day. T-18-02 is a caller
that writes an invented parameter name into an entry, and the answer to it is that every name
of the allowlist has to exist in the schema of its own tool.

AUDIT-01 asks for the shape of ``scripts/check_tool_budget.py``: one measurement over all
registered tools, never a sample, failing as soon as a single tool crosses the boundary and
naming every finding rather than only the fact that there was one. Nothing here registers a
tool on the module singleton ``mcp``: ``tests/contract/test_tool_surface.py`` compares the
registry against a frozen literal, so a leftover test tool would turn that file red.

The proof that every tool carries the recording decorator belongs to the same file but not
yet: the marker is set in plan 18-06 and gets its case here with it.
"""

from typing import Any

import pytest
from mcp import Client

from mcp_connector.audit.allowlist import FORBIDDEN_PARAMS, PARAM_ALLOWLIST
from mcp_connector.server import mcp


def _argument_names(schema: dict[str, Any] | None) -> set[str]:
    """The names a caller can put into the arguments of a call, top level only.

    A nested model lives under ``$defs`` and its field names are never keys of the arguments
    mapping the recorder sees, so widening this to the nested pass of
    ``tests/contract/test_tool_surface.py`` would compare the allowlist against names that
    can never arrive as an argument.
    """
    properties = (schema or {}).get("properties")
    return set(properties) if isinstance(properties, dict) else set()


async def _measured_surface() -> dict[str, set[str]]:
    """Every registered tool with its argument names, taken over the wire like the gate."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = (await client.list_tools()).tools
    return {tool.name: _argument_names(tool.input_schema) for tool in tools}


@pytest.mark.anyio
async def test_every_registered_tool_has_an_allowlist_entry() -> None:
    """A tool the allowlist never heard of would be recorded by nobody's decision."""
    surface = await _measured_surface()

    findings = [
        f"{name} has no allowlist entry" for name in sorted(surface) if name not in PARAM_ALLOWLIST
    ]
    findings += [
        f"{name} has an allowlist entry but is not registered"
        for name in sorted(PARAM_ALLOWLIST)
        if name not in surface
    ]

    assert findings == [], (
        "the allowlist and the tool registry have to be the same set, or a new tool is "
        "recorded on an assumption nobody made: " + ", ".join(findings)
    )


@pytest.mark.anyio
async def test_no_allowlisted_name_is_absent_from_its_own_schema() -> None:
    """T-18-02: a name that no longer exists points the recorder at a parameter nobody sends."""
    surface = await _measured_surface()

    findings: list[str] = []
    for name in sorted(PARAM_ALLOWLIST):
        for parameter in sorted(PARAM_ALLOWLIST[name] - surface.get(name, set())):
            findings.append(f"{name}.{parameter}")

    assert findings == [], (
        "an allowlisted name that the tool does not take is a rule guarding nothing, and it "
        "stays wrong until somebody reads this list by hand: " + ", ".join(findings)
    )


def test_no_allowlisted_name_is_on_the_block_list() -> None:
    """T-18-01: the payload names carry content by their mere presence, so they stay out."""
    findings = [
        f"{name}.{parameter}"
        for name in sorted(PARAM_ALLOWLIST)
        for parameter in sorted(PARAM_ALLOWLIST[name] & FORBIDDEN_PARAMS)
    ]

    assert findings == [], (
        "recording that a body was handed along says nothing a reader did not already know "
        "from the tool name, and it is the place a value grows next to one day: "
        + ", ".join(findings)
    )


@pytest.mark.anyio
async def test_the_block_list_names_parameters_that_really_exist() -> None:
    """A block list that matches nothing blocks nothing, and nobody would notice."""
    surface = await _measured_surface()

    matched = sorted(
        f"{name}.{parameter}"
        for name in surface
        for parameter in sorted(surface[name] & FORBIDDEN_PARAMS)
    )

    assert matched != [], (
        "no name of FORBIDDEN_PARAMS occurs in the measured tool surface: the list would be "
        "decoration, and the case above would pass for the wrong reason"
    )
