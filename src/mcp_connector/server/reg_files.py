"""Registration of the file tools. The logic lives in :mod:`mcp_connector.tools.files`.

No tool takes a user name: the identity comes from the auth channel through
``deps.resolve_clients`` only (threat T-01-12, confused deputy).
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import files as files_tools
from . import READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_read(
    path: Annotated[str, Field(description="Path inside the user's files, e.g. /Docs/notes.md")],
    offset: Annotated[int, Field(ge=0, description="Byte offset for a continued read")] = 0,
    ctx: Context = None,
) -> str:
    """Read a text file from Nextcloud; large files come back truncated with a next offset."""
    clients = deps.resolve_clients(ctx)
    return compact(await files_tools.read(clients, path=path, offset=offset))
