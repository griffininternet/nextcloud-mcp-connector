"""Tables round trip against a real Nextcloud 34 with the Tables app (opt-in).

The unit tests pin the shapes; only a real instance answers the questions that matter
here: does Tables really accept the two mandatory headers on a plain GET the way the
documentation describes, does ``POST /api/2/tables/{id}/rows`` really answer with 200 and
not 201 (pitfall 4), does ``GET /api/2/tables/{id}`` really carry ``rowsCount`` and
``onSharePermissions`` when a single table exists (assumption A6), and do value shapes
beyond text and number pass through without a conversion of our own (assumption A2). The
last one is the reason the test table carries a selection and a datetime column: they make
the open assumption visible instead of hiding it, and a refusal of the app is a measurement
for phase 10, never a reason to build a type converter into the client.

Table and columns are test scaffolding, not connector features: the client cannot create
either of them on purpose (create-only, threat T-08-11), so the ``POST`` calls below are
made directly with httpx and are clearly marked as setup. They are idempotent, because a
tenth run must not leave ten test tables behind (threat T-08-30).

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a
    uv run pytest tests/integration/test_tables_roundtrip.py -m integration -q
"""

import json
import time
import uuid
import warnings
from typing import Any

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.clients import tables as tables_client
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import tables as tables_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

# Real umlauts in the title, because a title travels through the OCS envelope, through the
# projection and back into an assertion, and a broken encoding anywhere on that way is a
# bug this suite should see rather than avoid.
TABLE_TITLE = "MCP-Test Übergaben Straßenbau"

TASK_COLUMN = "Aufgabe"
SIZE_COLUMN = "Größe in m²"
STATUS_COLUMN = "Status"
DUE_COLUMN = "Fällig am"

# The two shapes verified in the unit tests: a text column takes a JSON string, a number
# column takes a JSON number.
SIZE_VALUE = 12.5
# The two shapes assumption A2 is about. A model writes the label it read and an ISO date,
# so that is what is measured here; whether Tables wants an option id or another date
# format is exactly the open question.
STATUS_VALUE = "offen"
DUE_VALUE = "2026-08-21"

STATUS_OPTIONS = json.dumps([{"id": 0, "label": "offen"}, {"id": 1, "label": "erledigt"}])


def unique_task() -> str:
    """One task text that no other run wrote, with umlauts a broken encoding would eat."""
    return f"Grüße aus Hamburg, Straße 1 ({time.strftime('%Y%m%d-%H%M%S')} {uuid.uuid4().hex[:8]})"


def measured(what: str) -> None:
    """Make a measurement visible in the test report of a passing run.

    A print stays hidden while the test is green, and a green run is exactly when these
    numbers are wanted: the answer to assumption A2 belongs in the plan summary whether the
    instance accepted the value or refused it.
    """
    warnings.warn(f"measured: {what}", stacklevel=2)


@pytest.fixture
def clients(live_env: dict[str, str | None]) -> NcClients:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")

    user = live_env["user"]
    assert user != "admin", "integration tests run as a normal user, never as admin"

    capabilities.clear_cache()
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(str(live_env["base_url"])),
            user=str(user),
            secret=str(live_env["secret"]),
        ),
    )


async def _post(clients: NcClients, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Test scaffolding only: the connector itself never creates tables or columns.

    A status of 400 or above is a skip and not a failure: an account that may not prepare a
    table says nothing about the connector, and turning that into a red test would blame
    the wrong side. ``httpx.BasicAuth`` is written out here on purpose, so the setup is
    visibly not going through the credential seam the measurements use.
    """
    response = await clients.client.post(
        ocs.ocs_url(clients.creds, path),
        json=body,
        headers=dict(tables_client.TABLES_HEADERS),
        auth=httpx.BasicAuth(clients.creds.user, clients.creds.secret),
    )
    if response.status_code >= 400:
        pytest.skip(f"this account may not prepare a tables table ({response.status_code})")
    payload = ocs.parse_ocs(response, what="the prepared table or column")
    assert isinstance(payload, dict), f"the setup call did not answer with an object: {payload!r}"
    return payload


async def _table_with_columns(clients: NcClients) -> str:
    """Return the test table, creating it and its four columns once if they are missing.

    The four columns are deliberate. A mandatory text column exercises the refusal of
    ``create_row`` for a missing mandatory value, a number column is the second verified
    value shape, and the selection plus the datetime column are the two shapes of
    assumption A2.

    The ``subtype`` of the text column is load bearing and it is not optional, although the
    published ``openapi.json`` of the app says it is (and offers ``progress`` and ``stars``
    as the only values, which belong to a number column). ``ColumnsHelper::
    getColumnBusinessObject`` resolves ``ucfirst(type) . ucfirst(subtype) . 'Business'``,
    and ``TextBusiness`` does not exist: only ``TextLineBusiness``, ``TextLongBusiness``,
    ``TextLinkBusiness`` and ``TextRichBusiness`` do. A text column created without a
    subtype therefore turns every read and every write of that whole table into a 500,
    measured against Tables 2.2.2 on 2026-08-21. This is a property of the scaffolding
    route, not of the connector: ``number``, ``selection`` and ``datetime`` all have a
    business class without a subtype.
    """
    tables = await tables_client.get_tables(clients.client, clients.creds)
    table = next(
        (item for item in tables if item.get("title") == TABLE_TITLE and not item.get("archived")),
        None,
    )
    if table is None:
        table = await _post(
            clients,
            f"{tables_client.V2_PREFIX}/tables",
            {"title": TABLE_TITLE, "template": "custom"},
        )

    table_id = str(table["id"])
    node = int(table_id)
    columns = await tables_client.get_columns(clients.client, clients.creds, table_id)
    titles = {str(column.get("title")) for column in columns}

    wanted: tuple[tuple[str, str, dict[str, Any]], ...] = (
        (TASK_COLUMN, "text", {"mandatory": True, "subtype": "line", "textMaxLength": 255}),
        (SIZE_COLUMN, "number", {"numberDecimals": 1}),
        (STATUS_COLUMN, "selection", {"selectionOptions": STATUS_OPTIONS}),
        (DUE_COLUMN, "datetime", {}),
    )
    for title, kind, extra in wanted:
        if title in titles:
            continue
        await _post(
            clients,
            f"{tables_client.V2_PREFIX}/columns/{kind}",
            {"baseNodeId": node, "baseNodeType": "table", "title": title, **extra},
        )
    return table_id


async def _create_measuring_the_value_shapes(
    clients: NcClients, table_id: str, task: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write one row through the tool, narrowing down which value shapes the app accepts.

    The first attempt is the one a model would make: the label of a selection option and an
    ISO date next to the two verified shapes. If the app refuses it, the two candidates are
    tried one at a time, so the answer to assumption A2 names the column instead of the
    request. Every outcome is reported, and the fall back to text plus number keeps the
    round trip assertion of the caller meaningful either way.
    """
    base = {TASK_COLUMN: task, SIZE_COLUMN: SIZE_VALUE}
    attempts: tuple[tuple[str, dict[str, Any]], ...] = (
        (
            "text, number, selection and datetime",
            {**base, STATUS_COLUMN: STATUS_VALUE, DUE_COLUMN: DUE_VALUE},
        ),
        ("text, number and a selection label", {**base, STATUS_COLUMN: STATUS_VALUE}),
        ("text, number and an ISO date", {**base, DUE_COLUMN: DUE_VALUE}),
        ("text and number", base),
    )
    for what, values in attempts:
        try:
            created = await tables_tools.create_row(
                clients, table_id=table_id, values=json.dumps(values, ensure_ascii=False)
            )
        except ToolError as error:
            measured(f"A2: writing {what} was refused: {error.message} ({error.hint})")
            continue
        measured(f"A2: writing {what} answered with row id {created['id']}")
        return created, values

    pytest.fail("not even a text and a number could be written into the test table")


async def _row_with_task(clients: NcClients, table_id: str, task: str) -> dict[str, Any] | None:
    """Walk the rows of the table page by page and return the one carrying this task.

    Paging instead of one wide read, because the table survives every run: the cursor is
    the only way a later run still finds its own row, and it proves the live handle carries
    the table scope.
    """
    cursor: str | None = None
    for _ in range(50):
        page = await tables_tools.browse(
            clients, level="rows", table_id=table_id, limit=tables_tools.MAX_LIMIT, cursor=cursor
        )
        for row in page["results"]:
            if row.get(TASK_COLUMN) == task:
                return row
        cursor = page.get("next")
        if not cursor:
            return None
    return None


async def test_capabilities_report_the_installed_tables_app(clients: NcClients) -> None:
    caps = await capabilities.load(clients)

    assert caps.tables_available is True, "the bootstrap installs the Tables app"
    assert "1.0" in caps.tables_api_versions, (
        f"the row read of this client lives in generation 1 (got {caps.tables_api_versions})"
    )
    assert "2.0" in caps.tables_api_versions, (
        f"the create route lives in generation 2 (got {caps.tables_api_versions})"
    )
    measured(f"capabilities.tables apiVersions: {list(caps.tables_api_versions)}")


async def test_a_new_row_is_readable_back_under_its_column_titles(clients: NcClients) -> None:
    """The round trip: a row written by title is found again with the same titles as keys."""
    table_id = await _table_with_columns(clients)
    task = unique_task()

    created, values = await _create_measuring_the_value_shapes(clients, table_id, task)

    assert created["id"], f"Tables created a row without an id: {created!r}"
    assert created["table_id"] == table_id
    assert created["url"].endswith(f"/table/{table_id}")
    assert created["values_written"][TASK_COLUMN] == task

    row = await _row_with_task(clients, table_id, task)
    assert row is not None, f"the new row is not in the row level of table {table_id}"
    assert "Grüße aus Hamburg, Straße 1" in row[TASK_COLUMN], (
        f"the umlauts did not survive the round trip: {row!r}"
    )
    assert SIZE_COLUMN in row, f"the row does not carry the number column: {row!r}"
    for title in values:
        assert title in row, f"a written column is missing from the read back row: {row!r}"


async def test_the_live_row_url_carries_a_limit(clients: NcClients) -> None:
    """The property a parsed answer cannot show: the request itself was capped.

    A rows URL without ``limit`` reads the whole table (pitfall 1), so the assertion has to
    happen on the outgoing request and not on the number of results.
    """
    table_id = await _table_with_columns(clients)

    calls: list[httpx.URL] = []
    original_send = clients.client.send

    async def counting_send(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        if request.url.path.endswith("/rows/simple"):
            calls.append(request.url)
        return await original_send(request, **kwargs)

    # The capabilities call is an OCS route and is deliberately outside the capture.
    await capabilities.load(clients)
    clients.client.send = counting_send  # type: ignore[method-assign]
    try:
        await tables_tools.browse(clients, level="rows", table_id=table_id)
        await tables_tools.browse(clients, level="rows", table_id=table_id, limit=5000)
    finally:
        clients.client.send = original_send  # type: ignore[method-assign]

    assert len(calls) == 2, f"each row read must issue exactly one rows/simple request: {calls}"
    for url in calls:
        assert "limit" in url.params, f"a live rows URL carries no limit: {url}"
    assert calls[0].params["limit"] == str(tables_tools.DEFAULT_LIMIT)
    assert calls[1].params["limit"] == str(tables_client.MAX_ROWS)
    measured(f"live rows URLs: {[str(url.copy_with(scheme='', host='')) for url in calls]}")


async def test_the_table_level_reports_a_row_count_and_the_owner_may_write(
    clients: NcClients,
) -> None:
    """Assumption A6 and correction K5, both against the running instance.

    The single table call is asked directly for the two fields the tool layer depends on,
    because a projection that quietly filled in a default would hide a missing field. And
    ``can_create`` has to be true for a table this account owns, although the share object
    of an own table reports ``read`` alone.
    """
    table_id = await _table_with_columns(clients)

    info = await tables_client.get_table(clients.client, clients.creds, table_id)
    assert "rowsCount" in info, f"the single table call carries no rowsCount: {sorted(info)}"
    assert "onSharePermissions" in info, (
        f"the single table call carries no onSharePermissions: {sorted(info)}"
    )
    measured(
        f"GET api/2/tables/{table_id}: rowsCount={info.get('rowsCount')!r} "
        f"isShared={info.get('isShared')!r} onSharePermissions={info.get('onSharePermissions')!r}"
    )

    answer = await tables_tools.browse(clients, level="tables")
    entry = next((item for item in answer["results"] if item["title"] == TABLE_TITLE), None)
    assert entry is not None, f"the test table is missing from the table level: {answer!r}"
    assert isinstance(entry["rowsCount"], int), f"rowsCount is not a number: {entry!r}"
    assert entry["can_create"] is True, f"the owner may add a row to their own table: {entry!r}"


async def test_browsing_an_unknown_table_reports_it_instead_of_guessing(
    clients: NcClients,
) -> None:
    with pytest.raises(ToolError) as excinfo:
        await tables_tools.browse(clients, level="rows", table_id="99999999")

    assert excinfo.value.hint
    measured(f"unknown table: {excinfo.value.message} ({excinfo.value.hint})")
