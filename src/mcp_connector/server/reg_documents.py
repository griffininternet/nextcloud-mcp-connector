"""Registration for read-only document text extraction."""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import docx_text
from . import READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_extract_text(
    path: Annotated[str, Field(description="Path of a .docx file inside the user's files")],
    offset: Annotated[
        int,
        Field(ge=0, description="Extracted UTF-8 byte offset for a continued read"),
    ] = 0,
    ctx: Context | None = None,
) -> str:
    """Extract text from a Word .docx file; large results return a next offset."""
    clients = deps.resolve_clients(ctx)
    return compact(await docx_text.extract(clients, path=path, offset=offset))
