"""Unit tests for the calendar tools, all paths.

The time matrix itself lives in ``test_caldav_client.py``; what is pinned here is the
contract the model sees: a mandatory window with an explicit zone, a display zone that
only changes the representation, a fan out over all calendars that stays honest when one
of them fails, and an empty window that is an empty list and not an error.
"""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import calendar as calendar_tools

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

CALENDAR_HOME = f"{BASE}/remote.php/dav/calendars/alice/"
PERSONAL = f"{CALENDAR_HOME}personal/"
ALPHA = f"{CALENDAR_HOME}projekt%20alpha/"
CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

WINDOW = ("2026-09-01T00:00:00+02:00", "2026-11-01T00:00:00+01:00")


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def dav_response(body: str) -> httpx.Response:
    return httpx.Response(207, text=body, headers={"Content-Type": "application/xml"})


EMPTY = '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:"/>'


def mock_discovery(mock: respx.MockRouter) -> respx.Route:
    return mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(
        return_value=dav_response(fixture("caldav_calendars_207.xml"))
    )


def mock_calendars(
    mock: respx.MockRouter,
    *,
    personal: httpx.Response | None = None,
    alpha: httpx.Response | None = None,
) -> tuple[respx.Route, respx.Route]:
    mock_discovery(mock)
    personal_route = mock.route(method="REPORT", url=PERSONAL).mock(
        return_value=personal or dav_response(fixture("caldav_report_207.xml"))
    )
    alpha_route = mock.route(method="REPORT", url=ALPHA).mock(
        return_value=alpha or dav_response(EMPTY)
    )
    return personal_route, alpha_route


@pytest.mark.anyio
async def test_all_calendars_are_queried_and_the_events_are_merged(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        personal, alpha = mock_calendars(mock)
        result = await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert personal.call_count == 1
    assert alpha.call_count == 1, "without a calendar parameter every calendar is asked"

    assert result["count"] == 4
    assert [event["summary"] for event in result["events"]] == [
        "Projektbesprechung",
        "Standup",
        "Betriebsausflug",
        "Standup",
    ]
    assert result["range"]["start"] == WINDOW[0]
    assert result["range"]["end"] == WINDOW[1]
    assert result["range"]["timezone"] == "UTC"
    assert "degraded" not in result


@pytest.mark.anyio
async def test_the_output_times_are_absolute_and_carry_an_offset(clients: NcClients) -> None:
    """Even for a series: every instance is an absolute time, never a rule."""
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock)
        result = await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    standups = [event for event in result["events"] if event["summary"] == "Standup"]
    assert [event["start"] for event in standups] == [
        "2026-10-19T07:00:00+00:00",
        "2026-10-26T08:00:00+00:00",
    ]
    assert all(event["all_day"] is False for event in standups)


@pytest.mark.anyio
async def test_the_timezone_parameter_only_changes_the_representation(
    clients: NcClients,
) -> None:
    """Same instants, shown in Berlin: 09:00 local on both sides of the DST boundary."""
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock)
        result = await calendar_tools.list_events(
            clients, start=WINDOW[0], end=WINDOW[1], timezone="Europe/Berlin"
        )

    standups = [event for event in result["events"] if event["summary"] == "Standup"]
    assert [event["start"] for event in standups] == [
        "2026-10-19T09:00:00+02:00",
        "2026-10-26T09:00:00+01:00",
    ]
    assert result["range"]["timezone"] == "Europe/Berlin"


@pytest.mark.anyio
async def test_an_all_day_event_is_a_date_without_a_time(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock)
        result = await calendar_tools.list_events(
            clients, start=WINDOW[0], end=WINDOW[1], timezone="Europe/Berlin"
        )

    outing = next(event for event in result["events"] if event["summary"] == "Betriebsausflug")
    assert outing["all_day"] is True
    assert outing["start"] == "2026-10-24"
    assert outing["end"] == "2026-10-25"
    assert "T" not in outing["start"], "a date must never grow a time or an offset"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-09-01T00:00:00", "2026-09-30T00:00:00+02:00"),
        ("2026-09-01T00:00:00+02:00", "2026-09-30T00:00:00"),
        ("2026-09-01", "2026-09-30"),
    ],
)
async def test_a_time_without_a_zone_is_refused_before_any_request(
    clients: NcClients, start: str, end: str
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        everything = mock.route()
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(clients, start=start, end=end)

    assert everything.call_count == 0
    assert "timezone" in f"{excinfo.value.message} {excinfo.value.hint}".lower()
    assert "+02:00" in excinfo.value.hint, "the hint shows the accepted shape"


@pytest.mark.anyio
async def test_an_unparsable_time_is_refused_with_the_expected_format(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        everything = mock.route()
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(clients, start="next monday", end=WINDOW[1])

    assert everything.call_count == 0
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_end_before_the_start_is_refused_before_any_request(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        everything = mock.route()
        with pytest.raises(ToolError):
            await calendar_tools.list_events(clients, start=WINDOW[1], end=WINDOW[0])

    assert everything.call_count == 0


@pytest.mark.anyio
async def test_an_unknown_timezone_name_is_refused_before_any_request(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        everything = mock.route()
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(
                clients, start=WINDOW[0], end=WINDOW[1], timezone="Europe/Hamburg"
            )

    assert everything.call_count == 0
    assert "Europe/Berlin" in excinfo.value.hint, "the hint shows a valid IANA name"


@pytest.mark.anyio
async def test_one_broken_calendar_is_named_and_the_others_still_answer(
    clients: NcClients,
) -> None:
    """Graceful degradation, D-15: a partial answer must say that it is partial."""
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock, alpha=httpx.Response(503, text="service unavailable"))
        result = await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert result["count"] == 4, "the healthy calendar still delivers"
    assert len(result["degraded"]) == 1
    assert result["degraded"][0]["calendar"] == "Projekt Alpha"
    assert "503" in result["degraded"][0]["reason"]


@pytest.mark.anyio
async def test_a_window_without_events_is_an_empty_list_and_not_an_error(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock, personal=dav_response(EMPTY))
        result = await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert result["events"] == []
    assert result["count"] == 0
    assert result["range"]["start"] == WINDOW[0]
    assert "degraded" not in result


@pytest.mark.anyio
async def test_a_named_calendar_is_the_only_one_that_is_asked(clients: NcClients) -> None:
    with respx.mock(assert_all_called=False) as mock:
        personal, alpha = mock_calendars(mock)
        result = await calendar_tools.list_events(
            clients, start=WINDOW[0], end=WINDOW[1], calendar="Persönlich"
        )

    assert personal.call_count == 1
    assert alpha.call_count == 0
    assert {event["calendar"] for event in result["events"]} == {"Persönlich"}


@pytest.mark.anyio
async def test_the_calendar_parameter_also_accepts_the_uri(clients: NcClients) -> None:
    with respx.mock(assert_all_called=False) as mock:
        personal, alpha = mock_calendars(mock)
        await calendar_tools.list_events(
            clients, start=WINDOW[0], end=WINDOW[1], calendar="personal"
        )

    assert personal.call_count == 1
    assert alpha.call_count == 0


@pytest.mark.anyio
async def test_an_unknown_calendar_name_lists_the_ones_that_exist(clients: NcClients) -> None:
    """The name is validated against the discovery, never pasted into a path (T-01-51)."""
    with respx.mock(assert_all_called=False) as mock:
        mock_discovery(mock)
        report = mock.route(method="REPORT")
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(
                clients, start=WINDOW[0], end=WINDOW[1], calendar="../contacts"
            )

    assert report.call_count == 0
    assert "Persönlich" in excinfo.value.hint


@pytest.mark.anyio
async def test_an_account_without_a_calendar_says_so_instead_of_reporting_no_events(
    clients: NcClients,
) -> None:
    """Pitfall 3 through the tool: an empty account is not an empty schedule."""
    body = (
        '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">'
        "<d:response><d:href>/remote.php/dav/calendars/alice/</d:href>"
        "<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>"
        "<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>"
    )
    with respx.mock(assert_all_called=False) as mock:
        mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(return_value=dav_response(body))
        report = mock.route(method="REPORT")
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert report.call_count == 0
    assert "dav:create-calendar" in excinfo.value.hint


@pytest.mark.anyio
async def test_the_calendar_tools_never_ask_for_the_optional_app_capabilities(
    clients: NcClients,
) -> None:
    """CalDAV is core dav: requiring the Calendar app would be a wrong precondition."""
    with respx.mock(assert_all_called=False) as mock:
        capabilities = mock.get(CAPABILITIES_URL)
        mock_calendars(mock)
        await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert capabilities.call_count == 0


@pytest.mark.anyio
async def test_the_limit_caps_the_answer_and_marks_it(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_calendars(mock)
        result = await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1], limit=2)

    assert result["count"] == 2
    assert result["truncated"] is True
    assert len(result["events"]) == 2


@pytest.mark.anyio
async def test_an_impossible_limit_is_refused(clients: NcClients) -> None:
    with respx.mock(assert_all_called=False) as mock:
        everything = mock.route()
        with pytest.raises(ToolError):
            await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1], limit=0)

    assert everything.call_count == 0


@pytest.mark.anyio
async def test_every_calendar_failing_is_an_error_and_not_an_empty_schedule(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock_calendars(
            mock,
            personal=httpx.Response(500, text="boom"),
            alpha=httpx.Response(500, text="boom"),
        )
        with pytest.raises(ToolError) as excinfo:
            await calendar_tools.list_events(clients, start=WINDOW[0], end=WINDOW[1])

    assert "500" in f"{excinfo.value.message} {excinfo.value.hint}"


def test_the_window_is_converted_to_caldav_utc_once(clients: NcClients) -> None:
    """The parser is strict and the conversion has exactly one implementation."""
    parsed = calendar_tools.parse_instant("2026-09-01T00:00:00+02:00", field="start")
    assert parsed == datetime(2026, 8, 31, 22, 0, tzinfo=UTC)
