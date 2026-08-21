"""Tables client: two API generations of one app, reading plus one create path.

The Tables app answers on two generations at the same time, and this project needs both.
Generation 2 lives under ``/ocs/v2.php/apps/tables/api/2`` and answers in an OCS envelope;
it knows the tables, the single table and the columns, and it is where a new row is posted.
Generation 1 lives under ``/index.php/apps/tables/api/1`` and answers with the bare object;
it is the only generation with a route that reads the rows of a table, verified against the
app's own ``openapi.json``. One family, one module: the dividing line between the two
generations is a property of the app, and it must not land on the caller.

Two headers are mandatory on **every** request, a plain GET included: ``OCS-APIRequest:
true`` and ``Content-Type: application/json`` (D-18). Without the first one Nextcloud
answers a browser login page with status 200, which is why the headers are one constant
here instead of an argument anyone could forget.

Two spellings in one app, and this is the trap of the family. The columns route takes the
singular word (``columns/table/{id}``), the row create route takes the plural one
(``tables/{id}/rows``). Mixing them up yields a 404 out of the routing layer that reads
exactly like "table not found" and sends the search for the cause in the wrong direction
(K3). Both spellings are named constants below, and the unit tests freeze the two URLs as
literals.

The row routes of generation 1 carry ``#[NoCSRFRequired]``, ``#[CORS]`` and explicitly
``#[OpenAPI(scope: SCOPE_DEFAULT)]``, and they stand in the published ``openapi.json`` of
the app (K10). They are a promised API, not an internal frontend route, which is why this
module needs no replaceability warning of the kind a Mail integration would need.

``limit`` is enforced, not offered. Both ``limit`` and ``offset`` are nullable in the API,
and leaving the limit out returns *every* row of the table: a table with 20.000 rows becomes
one MCP answer. :func:`get_rows_simple` therefore takes ``limit`` as a keyword without a
default, so forgetting it is an error at the developer, not a full table read at the user.

There is deliberately no update, no remove, no column, no schema and no share path in this
module. The server promise is that it can neither overwrite nor remove nor re-share
anything, and the cheapest way to keep a promise is to never write the code that could
break it (threat T-08-11).

There is no retry on the POST, on any layer. A duplicated row is data corruption that this
server cannot clean up, because removing a row is forbidden by its own gate. One attempt,
and the answer carries the id of the new row so the model can read back instead of
repeating (threat T-08-10).
"""

from collections.abc import Mapping
from typing import Any

import httpx

from ...errors import ToolError
from ..credentials import Credentials
from . import ocs

#: Generation 1, the only one with a route that reads the rows of a table. ``index.php`` is
#: not optional on every instance, so it is part of the prefix.
V1_PREFIX = "/index.php/apps/tables/api/1"

#: Generation 2. It sits below ``/ocs/v2.php`` and is therefore built through
#: :func:`ocs.ocs_url`, never by string concatenation with the base URL.
V2_PREFIX = "/apps/tables/api/2"

#: Web route of a single table, used for the ``url`` field a human clicks. The fragment is
#: part of the route: the Tables frontend is a single page application.
TABLES_WEB_PREFIX = "/index.php/apps/tables/#/table"

#: The singular spelling, and it belongs to the columns route only:
#: ``GET /api/2/columns/{nodeType}/{nodeId}`` with ``nodeType`` being ``table`` or ``view``.
NODE_TYPE_TABLE = "table"

#: The plural spelling, and it belongs to the row create route only:
#: ``POST /api/2/{nodeCollection}/{nodeId}/rows`` with ``nodeCollection`` being ``tables``
#: or ``views``. Swapping the two constants is a 404 from the routing layer (K3).
NODE_COLLECTION_TABLES = "tables"

#: Upper bound of one row read. Never build a rows URL without a limit: the parameter looks
#: optional and answers with the whole table when it is left out (pitfall 1).
MAX_ROWS = 200

#: The two mandatory headers of D-18, plus the ``Accept`` that keeps a proxy from
#: negotiating HTML. Copied per request, never mutated in place.
TABLES_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

_SHAPE_HINT = "Check that the Tables app is enabled and up to date on that instance."


def api_url(creds: Credentials, path: str = "") -> str:
    """Build a generation 1 Tables URL; ``path`` is empty or starts with a slash."""
    if path and not path.startswith("/"):
        raise ValueError(f"a Tables path must start with a slash (got {path!r})")
    return f"{creds.base_url}{V1_PREFIX}{path}"


def web_url(creds: Credentials, table_id: str | int) -> str:
    """The link a human can open. Always built from the configured base URL."""
    return f"{creds.base_url}{TABLES_WEB_PREFIX}/{table_id}"


async def get_tables(client: httpx.AsyncClient, creds: Credentials) -> list[dict[str, Any]]:
    """List the tables the user may see, own ones and shared ones alike.

    The answer is generous: it carries the views with their filters, the column order and
    the sort order of every table. None of that survives the projection in the tool layer.
    """
    response = await client.get(
        ocs.ocs_url(creds, f"{V2_PREFIX}/tables"),
        headers=dict(TABLES_HEADERS),
        auth=creds.auth(),
    )
    return _as_list(ocs.parse_ocs(response, what="the tables"), what="tables")


async def get_table(
    client: httpx.AsyncClient, creds: Credentials, table_id: str | int
) -> dict[str, Any]:
    """Read one table including its row count and the permissions of the caller.

    This single request answers two different questions at once (K11): ``rowsCount`` is what
    marks a truncated row read as truncated, and ``isShared`` together with
    ``onSharePermissions`` is the write permission pre-check, so creating a row does not
    have to fetch the whole table list first. ``title`` comes along for the wording of the
    answer.
    """
    table = _path_id(table_id, "table id")
    response = await client.get(
        ocs.ocs_url(creds, f"{V2_PREFIX}/tables/{table}"),
        headers=dict(TABLES_HEADERS),
        auth=creds.auth(),
    )
    return _as_dict(ocs.parse_ocs(response, what=f"the table {table}"), what="a table")


async def get_columns(
    client: httpx.AsyncClient, creds: Credentials, table_id: str | int
) -> list[dict[str, Any]]:
    """List the columns of a table, with the singular spelling of the node type (K3)."""
    table = _path_id(table_id, "table id")
    response = await client.get(
        ocs.ocs_url(creds, f"{V2_PREFIX}/columns/{NODE_TYPE_TABLE}/{table}"),
        headers=dict(TABLES_HEADERS),
        auth=creds.auth(),
    )
    payload = ocs.parse_ocs(response, what=f"the columns of table {table}")
    return _as_list(payload, what="columns")


async def get_rows_simple(
    client: httpx.AsyncClient,
    creds: Credentials,
    table_id: str | int,
    *,
    limit: int,
    offset: int = 0,
) -> list[list[Any]]:
    """Read rows in the compact form: the first list holds the column titles.

    ``limit`` is a keyword without a default on purpose. The parameter is nullable in the
    API, and an omitted limit reads the entire table, so a missing limit has to be an error
    at the developer rather than a full table read at the user (pitfall 1). The value is
    capped at :data:`MAX_ROWS` and lifted to at least one, and a negative offset becomes
    zero, because the URL is built here and nowhere else.

    This is generation 1: the answer is the bare list, so it goes through
    :func:`ocs.parse_app_json` and not through the envelope parser.
    """
    table = _path_id(table_id, "table id")
    capped = min(max(int(limit), 1), MAX_ROWS)
    response = await client.get(
        api_url(creds, f"/tables/{table}/rows/simple"),
        params={"limit": capped, "offset": max(int(offset), 0)},
        headers=dict(TABLES_HEADERS),
        auth=creds.auth(),
    )
    payload = ocs.parse_app_json(response, what=f"the rows of table {table}")
    return _as_rows(payload)


async def create_row(
    client: httpx.AsyncClient,
    creds: Credentials,
    table_id: str | int,
    *,
    data: Mapping[str, Any] | str,
) -> dict[str, Any]:
    """Create one row in an existing table and return the object Tables stored.

    The path takes the plural spelling (K3), and the answer is status **200**, not 201: the
    controller returns a plain data response, and the published schema lists 200 alone. A
    test that expects 201 is red against a correctly working instance.

    ``data`` maps column **ids** to values; the app casts every key with ``(int)``, so a
    column title never works here. A JSON string is accepted as well, because the controller
    decodes one, which lets a free-form tool parameter pass through unchanged (K4).

    There is no retry. If this call times out, that does not mean nothing was written, and
    a second attempt would duplicate a row that no tool of this server can remove again.
    """
    table = _path_id(table_id, "table id")
    response = await ocs.ocs_post(
        client,
        creds,
        f"{V2_PREFIX}/{NODE_COLLECTION_TABLES}/{table}/rows",
        {"data": data},
    )
    return _as_dict(ocs.parse_ocs(response, what="the new row"), what="a row")


def _path_id(value: str | int, what: str) -> str:
    """Ids are numeric in Tables; anything else is a bug or an attempt (threat T-08-06)."""
    text = str(value).strip()
    if not text.isdigit():
        raise ToolError(
            message=f"{value!r} is not a numeric {what}.",
            hint="Use an id from tables_browse; Tables addresses tables and columns by number.",
        )
    return text


def _as_list(payload: Any, what: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ToolError(
            message=f"Nextcloud answered with something that is not a list of {what}.",
            hint=_SHAPE_HINT,
        )
    return [item for item in payload if isinstance(item, dict)]


def _as_dict(payload: Any, what: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ToolError(
            message=f"Nextcloud answered with something that is not {what}.",
            hint=_SHAPE_HINT,
        )
    return payload


def _as_rows(payload: Any) -> list[list[Any]]:
    """Check the shape of the compact row form: a list of lists, titles first (K8).

    The first list carries the column titles, every list after it carries the values of one
    row in column order, and a missing value is an empty string. There are no row ids in
    this form, which is why a row read this way is not addressable later, and why
    ``limit=25`` answers with 26 lists rather than 25.
    """
    if not isinstance(payload, list):
        raise ToolError(
            message="Nextcloud answered with something that is not a list of rows.",
            hint=_SHAPE_HINT,
        )
    return [list(item) for item in payload if isinstance(item, list)]
