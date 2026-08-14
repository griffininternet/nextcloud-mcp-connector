"""Registration of the calendar tools. The logic lives in :mod:`mcp_connector.tools.calendar`.

The parameter descriptions carry one example each. That is the cheapest fix for the most
expensive CalDAV mistake: a model that guesses the time format sends a window sabre answers
with 400, and neither the model nor the user learns why (pitfall 4).
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import calendar as calendar_tools
from . import READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def calendar_list_events(
    start: Annotated[
        str,
        Field(description="Window start, ISO 8601 with zone, e.g. 2026-09-01T00:00:00+02:00"),
    ],
    end: Annotated[str, Field(description="Window end, exclusive, same format as start")],
    calendar: Annotated[
        str | None, Field(description="One calendar by name or uri; default: all")
    ] = None,
    timezone: Annotated[
        str | None, Field(description="IANA zone for the output times, default UTC")
    ] = None,
    limit: Annotated[
        int, Field(ge=1, le=calendar_tools.MAX_LIMIT, description="Maximum number of events")
    ] = calendar_tools.DEFAULT_LIMIT,
    ctx: Context = None,
) -> str:
    """List calendar events in a time range (start and end are required, both with timezone)."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await calendar_tools.list_events(
            clients,
            start=start,
            end=end,
            calendar=calendar,
            timezone=timezone,
            limit=limit,
        )
    )
