"""Registration of the talk tools. The logic lives in :mod:`mcp_connector.tools.talk`.

``level`` is a ``Literal`` and therefore an enum in the input schema, not a free string: the
model sees the two valid values instead of guessing "chats" or "history" and paying a round
trip for the correction (D-06, D-14).

Both tools are listed unconditionally, even on an instance without the Talk app. A credential
dependent ``tools/list`` is not cacheable, breaks the token budget gate and surprises clients
that persist tool lists; the honest answer to a missing app is the sentence the tool returns
(SRV-04). The same holds for the administrative send switch of TALK-04: ``talk_send`` stays
listed when it is off, and the answer says who can turn it on.

Empty strings are the defaults instead of ``None``, so no ``anyOf`` of string and null reaches
the schema; the bodies below turn them back into ``None`` before the call.
"""

from typing import Annotated, Literal

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import talk as talk_tools
from . import CREATE_ONLY, READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def talk_browse(
    level: Annotated[
        Literal["conversations", "messages"],
        Field(description="What to list; messages needs a token"),
    ] = "conversations",
    token: Annotated[
        str, Field(description="Conversation token from level=conversations, e.g. gzu8sw3d")
    ] = "",
    limit: Annotated[
        int, Field(ge=1, le=talk_tools.MAX_LIMIT, description="Maximum entries")
    ] = talk_tools.DEFAULT_LIMIT,
    cursor: Annotated[
        str,
        Field(description="Next page handle from a truncated answer; only level=messages"),
    ] = "",
    ctx: Context | None = None,
) -> str:
    """List the conversations of this account, or the history of one.

    The messages level answers newest first; the next page runs further into the past."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await talk_tools.browse(
            clients,
            level=level,
            token=token or None,
            limit=limit,
            cursor=cursor or None,
        )
    )


@mcp.tool(annotations=CREATE_ONLY, structured_output=False)
@graceful
async def talk_send(
    token: Annotated[str, Field(description="Conversation token from talk_browse")],
    message: Annotated[str, Field(description="The text to post, plain text")],
    ctx: Context | None = None,
) -> str:
    """Send one message into a conversation; never edits or deletes one.

    A timeout does not mean nothing was sent. Read back with talk_browse(level=messages)
    instead of calling this twice."""
    clients = deps.resolve_clients(ctx)
    return compact(await talk_tools.send(clients, token=token, message=message))
