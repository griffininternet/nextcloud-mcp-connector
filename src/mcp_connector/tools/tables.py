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

import json
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

#: The example is part of the hint, because "invalid JSON" without a shape to copy costs a
#: round trip that a single object literal prevents.
_VALUES_HINT = (
    'Pass one JSON object of column titles and values, for example {"Task": "Call back", '
    '"Amount": 12.5}. Call tables_browse with level=columns for the titles and their types.'
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


async def create_row(clients: NcClients, table_id: str, values: str) -> dict[str, Any]:
    """Add one row to an existing table, addressed by column titles instead of ids.

    ``values`` is a **string** with one compact JSON object, not a mapping parameter. A
    ``dict`` parameter would pull ``additionalProperties`` or ``$defs`` into the input
    schema, and the tool surface of this server forbids ``$defs`` in several places on
    purpose; the precedent in this codebase is the comma string of
    ``unified_search.providers``. The Tables app accepts a JSON string for ``data`` as well
    (K4), so the string does not create a second shape on the way down either.

    Nothing is written before all four refusals have been passed: a missing write
    permission, an unknown title, an ambiguous title and a missing mandatory column. The
    order matters, because each of them is cheaper than the write it prevents.

    Cell values are not type checked here. The accepted shape per column ``type`` and
    ``subtype`` is not fully documented in the app, and a hand rolled validator would be a
    second truth that goes stale with every new column type. A 400 of the app is passed
    through with its own message instead. Verified shapes: a text column takes a JSON
    string, a number column takes a JSON number.

    There is no retry. A timeout does not mean that nothing was written, and no tool of this
    server can remove a duplicated row again, so the answer carries the id of the new row
    and the model can read back instead of repeating (T-08-10).
    """
    await capabilities.require_app(clients, APP)

    wanted = _parse_values(values)
    table = str(table_id or "").strip()

    info = await tables_client.get_table(clients.client, clients.creds, table)
    if not _may_create(info):
        raise ToolError(
            message=f"No permission to add a row to table {table} ({_text(info.get('title'))}).",
            hint=(
                "This table is shared with this account without a create permission. Ask its "
                "owner in Nextcloud for a write permission, or pick a table that tables_browse "
                "reports with can_create."
            ),
        )

    columns = await tables_client.get_columns(clients.client, clients.creds, table)
    data, written = _by_column_id(table, wanted, columns)

    row = await tables_client.create_row(clients.client, clients.creds, table, data=data)
    row_id = row.get("id")
    if row_id in (None, ""):
        raise ToolError(
            message="Nextcloud created the row but reported no id.",
            hint="Look for the row in the Tables app; it was probably created.",
        )

    return {
        "id": row_id,
        "table_id": table,
        "url": tables_client.web_url(clients.creds, table),
        "values_written": written,
    }


def _parse_values(values: str) -> dict[str, Any]:
    """Read the free form parameter, and answer a bad one with a shape to copy."""
    try:
        parsed = json.loads(values or "")
    except json.JSONDecodeError:
        # ``from None``: a decoder traceback would carry the raw parameter into the log and
        # tell the model nothing it can act on.
        raise ToolError(message="values is not valid JSON.", hint=_VALUES_HINT) from None

    if isinstance(parsed, list):
        raise ToolError(message="values must be a JSON object, not a list.", hint=_VALUES_HINT)
    if not isinstance(parsed, dict):
        raise ToolError(
            message="values must be a JSON object of column titles and values.",
            hint=_VALUES_HINT,
        )
    if not parsed:
        raise ToolError(
            message="values is an empty object, so there is nothing to write.",
            hint=_VALUES_HINT,
        )
    return parsed


def _by_column_id(
    table: str, wanted: dict[str, Any], columns: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve column titles against the columns of the instance, or refuse and say why.

    Titles are never guessed and never sent: the keys of the returned mapping are column
    **ids**, because the app casts every key with ``(int)`` and a title would silently become
    the column ``0`` (T-08-15). The comparison is normalised, so "Task" and "task " find the
    same column, and a title that matches two columns ends the call instead of picking one
    of them and writing into the wrong column.
    """
    by_title: dict[str, list[dict[str, Any]]] = {}
    for column in columns:
        by_title.setdefault(_normalise(column.get("title")), []).append(column)

    known = [_text(column.get("title") or "") for column in columns]
    titles_hint = f"Columns of this table: {', '.join(known) or 'none'}."

    ambiguous: list[str] = []
    unknown: list[str] = []
    data: dict[str, Any] = {}
    written: dict[str, Any] = {}
    for title, value in wanted.items():
        matches = by_title.get(_normalise(title), [])
        if not matches:
            unknown.append(str(title))
            continue
        if len(matches) > 1:
            found = ", ".join(str(column.get("id")) for column in matches)
            ambiguous.append(f"{str(title)!r} (column ids {found})")
            continue
        column = matches[0]
        data[str(column.get("id"))] = value
        written[_text(column.get("title") or title)] = value

    if ambiguous:
        raise ToolError(
            message=f"Table {table} has more than one column with the same title: "
            f"{'; '.join(ambiguous)}.",
            hint=(
                "Tables has no unique constraint on column titles, so this title cannot be "
                "resolved to one column. Rename one of them in the Tables app first; writing "
                "into either of the two would be a guess."
            ),
        )
    if unknown:
        missing_titles = ", ".join(repr(title) for title in unknown)
        raise ToolError(
            message=f"Table {table} has no column titled {missing_titles}.",
            hint=f"{titles_hint} The comparison ignores case and surrounding spaces.",
        )

    filled = {_normalise(title) for title in wanted}
    required = [
        _text(column.get("title") or "")
        for column in columns
        if column.get("mandatory") and _normalise(column.get("title")) not in filled
    ]
    if required:
        raise ToolError(
            message=f"Table {table} needs a value for {', '.join(repr(t) for t in required)}.",
            hint=(
                "These columns are mandatory in Tables, and a row without them is refused by "
                "the app. Add them to values and try again."
            ),
        )
    return data, written


def _normalise(title: Any) -> str:
    """One title as it is compared: trimmed and case folded, never as it is written."""
    return str(title or "").strip().casefold()


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
