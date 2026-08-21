"""Tables tools: one browse tool with a level, and one create-only write (D-06, D-14).

**One tool, three levels.** ``tables_browse(level=...)`` walks the tables, the columns of a
table and its rows. Three separate tools would cost three slots in every client that limits
them and three schemas in every ``tools/list``, for navigation the model can express in one
enum value. The answer envelope is the same on every level (``level``, ``count``,
``results``), so the model learns one shape instead of three.

**The limit is enforced, not offered.** A row read without a limit returns *every* row of
the table, so a table with 20.000 rows would become one MCP answer (pitfall 1). The default
is :data:`DEFAULT_LIMIT` rows, the ceiling is :data:`MAX_LIMIT`, and a table that has more
rows than the window says so in the answer: ``rowsCount`` next to ``count`` and ``offset``,
plus ``truncated`` and a ``next`` handle. Truncation is named here, never silent.

**Two things are explained before they can fail.** A missing or disabled Tables app stops
both tools at the capabilities check, before the first Tables request (SRV-04). And a user
without a write permission on a shared table is refused by this tool with a sentence and a
next step, instead of being walked into a 403 out of Nextcloud's permission middleware. The
middleware stays the authority; the pre-check is only the better error message.

Deliberately absent: update, delete, creating columns or whole tables, importing a scheme
and every share path. The client below has no code for any of it, which is what makes the
create-only annotation of ``tables_create_row`` honest rather than a promise (T-08-11).
"""

from typing import Any

from .. import paging
from ..errors import ToolError
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import tables as tables_client
from . import marks

APP = "tables"

#: The three navigation levels of ``tables_browse``, in the order a model walks them.
LEVELS = ("tables", "columns", "rows")

#: TABLES-01: a row read without an explicit limit reads this many rows and not the table.
DEFAULT_LIMIT = 25
MAX_LIMIT = 200

_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."
_TABLE_HINT = "Call tables_browse with level=tables first; it lists the table ids."

#: Column fields that a model needs to interpret a value, and only those. Everything else
#: of a column object (uuid, technicalName, orderWeight, defaults, timestamps) is payload
#: nobody reads.
_COLUMN_LIMITS = (
    "selectionOptions",
    "textMaxLength",
    "numberMin",
    "numberMax",
    "numberDecimals",
    "datetimeDefault",
)


async def browse(
    clients: NcClients,
    level: str = "tables",
    table_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Walk the user's Tables: the tables, the columns of one table, or its rows."""
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Tables level.", hint=_LEVEL_HINT)
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "tables":
        return _envelope(level, await _tables(clients), capped)

    table = str(table_id or "").strip()
    if not table:
        raise ToolError(message=f"level={level!r} needs a table_id.", hint=_TABLE_HINT)

    if level == "columns":
        columns = await tables_client.get_columns(clients.client, clients.creds, table)
        return _envelope(level, [_column(column) for column in columns], capped)

    return await _rows(clients, table, capped, cursor)


async def _tables(clients: NcClients) -> list[dict[str, Any]]:
    """Table ids and sizes, plus whether the user may add a row at all."""
    tables = await tables_client.get_tables(clients.client, clients.creds)
    return [_table(table) for table in tables if not table.get("archived")]


def _table(table: dict[str, Any]) -> dict[str, Any]:
    """Project one table onto the fields a model reads, and drop the rest.

    ``GET /api/2/tables`` answers with the views of every table including their filters and
    sort orders, plus ``columnOrder``, ``sort``, ``ownerDisplayName``, ``createdBy`` and
    ``lastEditBy``. None of that survives here: every key is paid for in every answer.
    """
    entry: dict[str, Any] = {
        "id": table.get("id"),
        "title": _text(table.get("title") or ""),
        "rowsCount": table.get("rowsCount"),
        "columnsCount": table.get("columnsCount"),
        "isShared": bool(table.get("isShared")),
        "can_create": _may_create(table),
    }
    if table.get("emoji"):
        entry["emoji"] = table["emoji"]
    return entry


def _column(column: dict[str, Any]) -> dict[str, Any]:
    """Project one column: what it is called, what it is, and what a value must respect."""
    entry: dict[str, Any] = {
        "id": column.get("id"),
        "title": _text(column.get("title") or ""),
        "type": str(column.get("type") or ""),
        "mandatory": bool(column.get("mandatory")),
    }
    if column.get("subtype"):
        entry["subtype"] = str(column["subtype"])
    for key in _COLUMN_LIMITS:
        value = column.get(key)
        if value is None or value == "" or value == []:
            continue
        entry[key] = value
    return entry


async def _rows(clients: NcClients, table: str, limit: int, cursor: str | None) -> dict[str, Any]:
    """Read one window of rows and say how much of the table it is.

    The table itself is read first, for two answers out of one request (K11): ``rowsCount``
    is what turns "there is more" into an observation instead of a guess, and ``title`` is
    what the answer calls the table.
    """
    info = await tables_client.get_table(clients.client, clients.creds, table)

    offset = 0
    if cursor:
        state = paging.decode_cursor(cursor)
        # A handle of another table would silently answer with the wrong page, and the model
        # has no way to notice. Saying so costs one round trip; guessing is a wrong answer.
        paging.check_scope(state, "t", table, "table")
        offset = paging.read_offset(state)

    payload = await tables_client.get_rows_simple(
        clients.client, clients.creds, table, limit=limit, offset=offset
    )
    titles = [_text(cell) for cell in payload[0]] if payload else []
    results = [_row(titles, values) for values in payload[1:]]

    answer: dict[str, Any] = {
        "level": "rows",
        "table": _text(info.get("title") or ""),
        "count": len(results),
        "results": results,
        "rowsCount": _row_count(info, offset + len(results)),
        "offset": offset,
    }
    if answer["rowsCount"] > offset + len(results):
        answer["truncated"] = True
        answer["next"] = paging.encode_cursor({"o": offset + len(results), "t": table})
    return answer


def _row(titles: list[str], values: list[Any]) -> dict[str, Any]:
    """Zip the title row of the compact form onto one row of values.

    The first list of ``rows/simple`` carries the column titles (K8), so it becomes the keys
    of every row object and is never repeated as a row of its own. A row that is shorter than
    the title row keeps empty strings, which is the same "missing value" the app sends.
    """
    row: dict[str, Any] = {}
    for index, title in enumerate(titles):
        value = values[index] if index < len(values) else ""
        row[title] = _text(value) if isinstance(value, str) else value
    return row


def _row_count(info: dict[str, Any], fallback: int) -> int:
    """The row count of the table, or what was read so far if the app reported nothing."""
    count = info.get("rowsCount")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return fallback
    return count


def _may_create(table: dict[str, Any]) -> bool:
    """Whether this account may add a row to this table (K5).

    The naive read of this question is wrong on the most common case of all. Tables reports
    the permissions of a *share* in ``onSharePermissions``, and ``TableService::
    setIsSharedState`` sets ``Permissions(read: true)`` together with ``isShared = false``
    for a table the caller owns, while Nextcloud's own ``PermissionsService::
    checkPermission`` short circuits on ``userIsElementOwner`` long before it looks at that
    object. A literal ``if not onSharePermissions.create: refuse`` would therefore refuse
    every user on their own table. That is the same trap as ``canCreateBoards`` in phase 1:
    a field that answers a different question than the one being asked.

    So ownership decides first, and only a share really is asked for a create permission.
    ``manage`` counts as well, because a share that may manage the table may write rows.
    """
    permissions = table.get("onSharePermissions")
    permissions = permissions if isinstance(permissions, dict) else {}
    if not table.get("isShared"):
        return True
    return bool(permissions.get("create") or permissions.get("manage"))


def _text(value: Any) -> str:
    """Foreign text on its way into the model context, with our own markers removed.

    Cell values and titles are written by whoever may write to the table, so they are the
    place where a document could otherwise claim to be this server talking (T-08-14).
    """
    return marks.without_marks(str(value))


def _envelope(level: str, results: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for all three levels, truncation named instead of silent."""
    kept = results[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(results) > len(kept):
        answer["truncated"] = True
    return answer
