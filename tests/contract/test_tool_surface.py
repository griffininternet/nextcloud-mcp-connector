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
