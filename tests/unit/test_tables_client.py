"""Unit tests for the Tables client, all paths, asserted on the request that was built.

Two properties of this client are contract and not implementation detail, and neither of
them is visible in a parsed answer, which is why they are tested against the URL:

*   a rows URL always carries ``limit``. The parameter is nullable in the API, and leaving
    it out reads every row of the table, so the enforced limit is tested on the query
    string and not on the length of the result (pitfall 1).
*   the parser follows the generation. Generation 2 answers in an OCS envelope, generation 1
    answers with the bare list, and the two spellings of the node path differ per route:
    the columns route takes the singular ``table``, the row create route the plural
    ``tables``. Both URLs stand below as frozen literals, because mixing them up yields a
    404 out of the routing layer that reads like "table not found" (K3).

The rest is the usual catalogue: a 403 in the app's own error format, status **200** on the
create rather than the created-status a POST usually answers with, an empty table as
``no_data``, an empty table list, a non-numeric table id that produces zero requests, an
answer shape that does not fit, and the absence of an ``Origin`` header on the write.

The digits of the created-status appear nowhere in this file on purpose: the gate for this
plan greps for them, because a test that expects them is red against a correctly working
instance (pitfall 4).
"""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import tables as tables_client
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

# The frozen endpoint literals. They are the guard against swapping nodeType and
# nodeCollection: a route that changes spelling here has to be changed on purpose.
V2_BASE = f"{BASE}/ocs/v2.php/apps/tables/api/2"
TABLES_URL = f"{V2_BASE}/tables"
TABLE_URL = f"{V2_BASE}/tables/7"
COLUMNS_URL = f"{V2_BASE}/columns/table/7"
CREATE_ROW_URL = f"{V2_BASE}/tables/7/rows"
ROWS_URL = f"{BASE}/index.php/apps/tables/api/1/tables/7/rows/simple"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


CREATED_ROW = {
    "id": 4711,
    "tableId": 7,
    "createdBy": "alice",
    "createdAt": "2026-08-21 10:14:02",
    "lastEditBy": "alice",
    "lastEditAt": "2026-08-21 10:14:02",
    "data": [{"columnId": 11, "value": "Baulos 4 übergeben"}],
    "dataByAlias": [],
}


@pytest.mark.anyio
async def test_a_get_carries_both_mandatory_headers(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """D-18: Tables wants both headers even where there is no body to describe."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(TABLES_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("tables_tables.json")))
        )
        tables = await tables_client.get_tables(client, creds)

    request = route.calls[0].request
    assert request.headers["OCS-APIRequest"] == "true"
    assert request.headers["Content-Type"] == "application/json"
    assert [table["id"] for table in tables] == [7, 9]


@pytest.mark.anyio
async def test_the_rows_url_always_carries_a_limit(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The property a parsed answer never shows: without a limit this reads everything."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ROWS_URL).mock(
            return_value=httpx.Response(200, json=fixture("tables_rows_simple.json"))
        )
        rows = await tables_client.get_rows_simple(client, creds, 7, limit=25)

    assert "limit=25" in str(route.calls.last.request.url)
    assert route.calls.last.request.url.params["offset"] == "0"
    assert len(rows) == 4, "the title row plus three rows"


@pytest.mark.anyio
async def test_a_limit_above_the_maximum_is_capped_in_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ROWS_URL).mock(
            return_value=httpx.Response(200, json=fixture("tables_rows_simple.json"))
        )
        await tables_client.get_rows_simple(client, creds, 7, limit=5000)

    assert "limit=200" in str(route.calls.last.request.url)
    assert tables_client.MAX_ROWS == 200


@pytest.mark.anyio
async def test_a_limit_below_one_and_a_negative_offset_are_lifted(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """A zero limit would read nothing, a negative offset is a 400 at the app."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ROWS_URL).mock(
            return_value=httpx.Response(200, json=fixture("tables_rows_simple.json"))
        )
        await tables_client.get_rows_simple(client, creds, 7, limit=0, offset=-5)

    params = route.calls.last.request.url.params
    assert params["limit"] == "1"
    assert params["offset"] == "0"


@pytest.mark.anyio
async def test_the_columns_call_uses_the_singular_node_type(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Singular here, plural on the create route. The URL is the only place it shows (K3)."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(COLUMNS_URL).mock(
            return_value=httpx.Response(200, json=envelope(fixture("tables_columns.json")))
        )
        columns = await tables_client.get_columns(client, creds, 7)

    called = str(route.calls.last.request.url)
    assert called == COLUMNS_URL
    assert "columns/tables/" not in called
    assert [column["title"] for column in columns][:2] == ["Aufgabe", "Status"]


@pytest.mark.anyio
async def test_creating_a_row_uses_the_plural_and_is_answered_with_200(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The app answers a plain data response here, so the success status is 200."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(CREATE_ROW_URL).mock(
            return_value=httpx.Response(200, json=envelope(CREATED_ROW))
        )
        created = await tables_client.create_row(
            client, creds, 7, data={"11": "Baulos 4 übergeben"}
        )

    assert created["id"] == 4711
    assert str(route.calls.last.request.url) == CREATE_ROW_URL
    assert json.loads(route.calls.last.request.content) == {"data": {"11": "Baulos 4 übergeben"}}


@pytest.mark.anyio
async def test_the_create_request_sends_json_and_never_an_origin_header(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """With an Origin present Nextcloud demands a basic reauthentication (threat T-08-09)."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(CREATE_ROW_URL).mock(
            return_value=httpx.Response(200, json=envelope(CREATED_ROW))
        )
        await tables_client.create_row(client, creds, 7, data={"11": "Maße geprüft"})

    request = route.calls.last.request
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["OCS-APIRequest"] == "true"
    assert "origin" not in {key.lower() for key in request.headers}


@pytest.mark.anyio
async def test_a_403_on_the_rows_route_becomes_a_sentence_with_a_next_step(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Generation 1 answers with the bare object, so parse_app_json reads the message."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ROWS_URL).mock(
            return_value=httpx.Response(403, json={"message": "No read permission for table 7"})
        )
        with pytest.raises(ToolError) as excinfo:
            await tables_client.get_rows_simple(client, creds, 7, limit=25)

    assert "No read permission for table 7" in excinfo.value.message
    assert "permission" in excinfo.value.hint.lower()


@pytest.mark.anyio
async def test_a_table_with_no_rows_is_no_data_and_not_an_error(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Only the title row comes back; that is an empty table, not a broken answer."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ROWS_URL).mock(
            return_value=httpx.Response(200, json=[["Aufgabe", "Status", "Fällig am"]])
        )
        rows = await tables_client.get_rows_simple(client, creds, 7, limit=25)

    assert rows == [["Aufgabe", "Status", "Fällig am"]]
    assert len(rows) - 1 == 0, "the title row plus zero rows"


@pytest.mark.anyio
async def test_an_instance_without_a_single_table_is_not_an_error(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(TABLES_URL).mock(return_value=httpx.Response(200, json=envelope([])))
        tables = await tables_client.get_tables(client, creds)

    assert tables == []


@pytest.mark.anyio
async def test_a_table_id_that_is_not_numeric_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Ids go into the path; anything but digits is a bug or an attempt (threat T-08-06)."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await tables_client.get_rows_simple(client, creds, "7/../../tables", limit=25)

    assert len(route.calls) == 0
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_table_read_that_answers_with_a_list_is_reported_as_such(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """An unexpected shape is a sentence plus a next step, never a TypeError."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(TABLE_URL).mock(return_value=httpx.Response(200, json=envelope([])))
        with pytest.raises(ToolError) as excinfo:
            await tables_client.get_table(client, creds, 7)

    assert "not a table" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_table_list_that_is_not_a_list_is_reported_as_such(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(TABLES_URL).mock(
            return_value=httpx.Response(200, json=envelope({"unexpected": True}))
        )
        with pytest.raises(ToolError) as excinfo:
            await tables_client.get_tables(client, creds)

    assert excinfo.value.hint


def test_the_web_link_is_always_built_from_the_configured_base_url() -> None:
    """SSRF boundary: the link a human opens never comes out of an answer (T-08-08)."""
    creds = Credentials(BASE, USER, SECRET)
    assert tables_client.web_url(creds, 7) == f"{BASE}/index.php/apps/tables/#/table/7"
    assert tables_client.web_url(creds, 7).startswith(creds.base_url)


def test_the_module_has_no_update_remove_or_share_path() -> None:
    """The server promise of this family, kept by not writing the code (threat T-08-11)."""
    source = Path(tables_client.__file__).read_text(encoding="utf-8")
    for forbidden in (".put(", ".patch(", "/share", "/transfer", "/scheme"):
        assert forbidden not in source, f"{forbidden} has no place in a read plus create client"


def test_the_rows_reader_takes_its_limit_as_a_keyword_without_a_default() -> None:
    """Constructive rather than documented: an omitted limit does not compile away."""
    import inspect

    parameter = inspect.signature(tables_client.get_rows_simple).parameters["limit"]
    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
