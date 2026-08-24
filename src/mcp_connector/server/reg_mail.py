"""Registration of the mail tool. The logic lives in :mod:`mcp_connector.tools.mail`.

``level`` is a ``Literal`` and therefore an enum in the input schema, not a free string: the
model sees the three valid values instead of guessing "inbox" or "folders" and paying a round
trip for the correction (D-06, D-14).

The tool is listed unconditionally, even on an instance without the Mail app. A credential
dependent ``tools/list`` is not cacheable, breaks the token budget gate and surprises clients
that persist tool lists; the honest answer to a missing app is the sentence the tool returns
(SRV-04).

Empty strings are the defaults instead of ``None``, so no ``anyOf`` of string and null reaches
the schema; the body below turns them back into ``None`` before the call.

One tool and no second one, which is the whole security statement of this family: there is no
send, no draft, no move, no flag and no delete here, and the full text of a single mail travels
through the existing ``fetch`` with ``mail:<databaseId>`` rather than through a tool of its own.
The full filter grammar stands in the docstring of the tool and in the README instead of in the
schema: every byte of a ``Field`` description is paid for in every ``tools/list`` of every
session, and a grammar is read once.
"""

from typing import Annotated, Literal

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import mail as mail_tools
from . import READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def mail_browse(
    level: Annotated[
        Literal["accounts", "mailboxes", "messages"],
        Field(description="What to list; mailboxes needs an account_id, messages a mailbox_id"),
    ] = "accounts",
    account_id: Annotated[str, Field(description="Account id from level=accounts")] = "",
    mailbox_id: Annotated[str, Field(description="Mailbox id from level=mailboxes")] = "",
    filter: Annotated[  # noqa: A002 - the name of the parameter in the Mail app
        str,
        Field(
            description=(
                "Only level=messages: type:value conditions, space separated; types is, not, "
                "from, subject, tags, start, end; start/end take Unix seconds"
            )
        ),
    ] = "",
    limit: Annotated[
        int, Field(ge=1, le=mail_tools.MAX_LIMIT, description="Maximum number of entries")
    ] = mail_tools.DEFAULT_LIMIT,
    cursor: Annotated[
        str,
        Field(description="Next page handle from a truncated messages answer; only that level"),
    ] = "",
    ctx: Context | None = None,
) -> str:
    """List the mail accounts of this user, the mailboxes of one, or the messages of one.

    Envelopes newest first; the full text of one is a fetch("mail:<id>") away. A filter value
    with a space or a colon has to be percent encoded (subject:Rechnung%20Mai). Reads only:
    never sends, drafts, moves, flags or deletes.
    """
    clients = deps.resolve_clients(ctx)
    return compact(
        await mail_tools.browse(
            clients,
            level=level,
            account_id=account_id or None,
            mailbox_id=mailbox_id or None,
            filter=filter or None,
            limit=limit,
            cursor=cursor or None,
        )
    )
