"""Registration of the contacts tool. The logic lives in :mod:`mcp_connector.tools.contacts`.

One tool, one sentence, two parameters. The description says "name or email address"
because that is exactly what the server side filter matches: a model that searches for a
phone number here would get an empty answer and no explanation.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import contacts as contacts_tools
from . import READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def contacts_search(
    query: Annotated[str, Field(description="Part of a name or of a mail address, e.g. meier")],
    limit: Annotated[
        int, Field(ge=1, le=contacts_tools.MAX_LIMIT, description="Maximum number of contacts")
    ] = contacts_tools.DEFAULT_LIMIT,
    ctx: Context = None,
) -> str:
    """Search the user's contacts by name or email address."""
    clients = deps.resolve_clients(ctx)
    return compact(await contacts_tools.search(clients, query=query, limit=limit))
