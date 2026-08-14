"""Registration of the file tools. The logic lives in :mod:`mcp_connector.tools.files`.

No tool takes a user name: the identity comes from the auth channel through
``deps.resolve_clients`` only (threat T-01-12, confused deputy).
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import files as files_tools
from . import CREATE_ONLY, READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_search(
    query: Annotated[str, Field(description="Part of a file or folder name, e.g. budget")],
    folder: Annotated[str, Field(description="Folder to search in, e.g. /Docs")] = "/",
    limit: Annotated[
        int, Field(ge=1, le=files_tools.MAX_SEARCH_LIMIT, description="Maximum number of hits")
    ] = files_tools.DEFAULT_SEARCH_LIMIT,
    cursor: Annotated[str, Field(description="'next' value of the previous answer")] = "",
    ctx: Context | None = None,
) -> str:
    """Search files and folders by name (matches names, not file contents)."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await files_tools.search(
            clients, query=query, folder=folder, limit=limit, cursor=cursor or None
        )
    )


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_list(
    path: Annotated[str, Field(description="Folder path, e.g. /Docs")] = "/",
    limit: Annotated[
        int, Field(ge=1, le=files_tools.MAX_LIST_LIMIT, description="Maximum number of entries")
    ] = files_tools.DEFAULT_LIST_LIMIT,
    cursor: Annotated[str, Field(description="'next' value of the previous answer")] = "",
    ctx: Context | None = None,
) -> str:
    """List the direct children of a folder."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await files_tools.list_dir(clients, path=path, limit=limit, cursor=cursor or None)
    )


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_read(
    path: Annotated[str, Field(description="Path inside the user's files, e.g. /Docs/notes.md")],
    offset: Annotated[int, Field(ge=0, description="Byte offset for a continued read")] = 0,
    ctx: Context | None = None,
) -> str:
    """Read a text file from Nextcloud; large files come back truncated with a next offset."""
    clients = deps.resolve_clients(ctx)
    return compact(await files_tools.read(clients, path=path, offset=offset))


@mcp.tool(annotations=CREATE_ONLY, structured_output=False)
@graceful
async def files_upload(
    path: Annotated[str, Field(description="Target path; must not exist yet")],
    content: Annotated[str, Field(description="UTF-8 text content")],
    ctx: Context | None = None,
) -> str:
    """Create a new text file. Fails if the target already exists; never overwrites."""
    clients = deps.resolve_clients(ctx)
    return compact(await files_tools.upload(clients, path=path, content=content))
