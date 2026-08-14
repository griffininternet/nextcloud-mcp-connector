"""Unit tests for the CalDAV client, with the four case time matrix as the centre piece.

CalDAV is where the competitors' bug reports live, and all of them are time bugs. The
matrix from 01-RESEARCH.md pitfall 4 is therefore mandatory and named as such below:

* case (a) an event in ``Europe/Berlin`` read through a UTC window
* case (b) a series across the DST boundary at the end of October
* case (c) an all day event
* case (d) a window that ends exactly on the event boundary

Around it sit the guards that keep a malformed request from ever reaching sabre: a naive
datetime, an end at or before the start, a calendar URI with a path separator, and a home
collection without a single VEVENT calendar.
"""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from lxml import etree

from mcp_connector.errors import ConflictError, ToolError
from mcp_connector.nextcloud.clients import caldav
from mcp_connector.nextcloud.clients import xml as davxml
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

CALENDAR_HOME = f"{BASE}/remote.php/dav/calendars/alice/"
PERSONAL = f"{CALENDAR_HOME}personal/"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

BERLIN = ZoneInfo("Europe/Berlin")


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


def calendars_response() -> httpx.Response:
    return httpx.Response(
        207,
        text=fixture("caldav_calendars_207.xml"),
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )


def report_response() -> httpx.Response:
    return httpx.Response(
        207,
        text=fixture("caldav_report_207.xml"),
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )


def empty_multistatus() -> httpx.Response:
    body = '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:"/>'
    return httpx.Response(207, text=body, headers={"Content-Type": "application/xml"})


# --------------------------------------------------------------------------------------
# to_caldav_utc
# --------------------------------------------------------------------------------------


def test_to_caldav_utc_returns_the_icalendar_utc_form() -> None:
    """``YYYYMMDDTHHMMSSZ``, not ISO 8601 with separators (pitfall 4, cause 1)."""
    assert caldav.to_caldav_utc(datetime(2026, 9, 15, 14, 0, tzinfo=BERLIN)) == "20260915T120000Z"
    assert caldav.to_caldav_utc(datetime(2026, 9, 1, 0, 0, tzinfo=UTC)) == "20260901T000000Z"


def test_to_caldav_utc_refuses_a_naive_datetime() -> None:
    """A naive datetime has no instant, and guessing one is how events move by hours."""
    with pytest.raises(ValueError, match="timezone aware"):
        caldav.to_caldav_utc(datetime(2026, 9, 15, 14, 0))


# --------------------------------------------------------------------------------------
# build_calendar_query
# --------------------------------------------------------------------------------------


def test_the_query_body_carries_one_expand_and_a_matching_time_range() -> None:
    """sabre needs both attributes on ``c:expand``; the filter must use the same window."""
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)

    body = caldav.build_calendar_query(start, end)
    root = etree.fromstring(body, parser=davxml.hardened_parser())

    expands = root.findall(f".//{{{davxml.CAL}}}expand")
    assert len(expands) == 1, "exactly one expand, otherwise sabre answers 400"
    assert expands[0].get("start") == "20260901T000000Z"
    assert expands[0].get("end") == "20260930T235959Z"

    ranges = root.findall(f".//{{{davxml.CAL}}}time-range")
    assert len(ranges) == 1
    assert ranges[0].get("start") == expands[0].get("start")
    assert ranges[0].get("end") == expands[0].get("end")

    assert root.tag == f"{{{davxml.CAL}}}calendar-query"
    comps = [element.get("name") for element in root.findall(f".//{{{davxml.CAL}}}comp-filter")]
    assert comps == ["VCALENDAR", "VEVENT"]


def test_the_query_body_is_built_with_lxml_and_not_from_a_string() -> None:
    """A summary or a URI must never be able to close a tag (threat T-01-45)."""
    source = Path(caldav.__file__).read_text(encoding="utf-8")
    assert "<c:" not in source, "no XML literal belongs into this module"
    assert "calendar-query" in source


@pytest.mark.parametrize(
    "end",
    [
        datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
        datetime(2026, 8, 31, 23, 0, tzinfo=UTC),
    ],
)
def test_an_end_at_or_before_the_start_is_refused(end: datetime) -> None:
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    with pytest.raises(ToolError) as excinfo:
        caldav.build_calendar_query(start, end)
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_end_at_or_before_the_start_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """sabre answers 400 BadRequest; the round trip is pure loss, so we refuse first."""
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(method="REPORT")
        with pytest.raises(ToolError):
            await caldav.query_events(client, creds, "personal", start, start)

    assert route.call_count == 0


# --------------------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_discovery_keeps_only_vevent_collections(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """VTODO only collections, subscriptions, the inbox and the home itself drop out."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(
            return_value=calendars_response()
        )
        calendars = await caldav.discover_calendars(client, creds)

    assert [entry.uri for entry in calendars] == ["personal", "projekt alpha"]
    assert [entry.display_name for entry in calendars] == ["Persönlich", "Projekt Alpha"]

    request = route.calls[0].request
    assert request.headers["Depth"] == "1"
    assert request.headers["Content-Type"] == "application/xml"

    body = etree.fromstring(request.content, parser=davxml.hardened_parser())
    asked = {str(element.tag) for element in body.iter() if isinstance(element.tag, str)}
    assert f"{{{davxml.CAL}}}supported-calendar-component-set" in asked
    assert f"{{{davxml.CS}}}getctag" in asked
    assert f"{{{davxml.DAV}}}displayname" in asked


@pytest.mark.anyio
async def test_discovery_unquotes_the_uri_from_the_href(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """``projekt%20alpha`` is a URI with a space, and the URL builder quotes it again."""
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(return_value=calendars_response())
        calendars = await caldav.discover_calendars(client, creds)

    alpha = calendars[1]
    assert alpha.uri == "projekt alpha"
    assert caldav.calendar_url(creds, alpha.uri) == f"{CALENDAR_HOME}projekt%20alpha/"


@pytest.mark.anyio
async def test_an_account_without_a_calendar_names_the_occ_command(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Pitfall 3: a user created with ``occ user:add`` has no calendar at all.

    The honest answer is an error with a way out, never an empty list that the model
    would report as "you have no appointments".
    """
    body = (
        '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">'
        "<d:response><d:href>/remote.php/dav/calendars/alice/</d:href>"
        "<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>"
        "<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>"
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(
            return_value=httpx.Response(207, text=body)
        )
        with pytest.raises(ToolError) as excinfo:
            await caldav.discover_calendars(client, creds)

    assert "no calendar" in excinfo.value.message.lower()
    assert "dav:create-calendar" in excinfo.value.hint


@pytest.mark.anyio
async def test_a_rejected_app_password_during_discovery_is_not_retried(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="PROPFIND", url=CALENDAR_HOME).mock(
            return_value=httpx.Response(401, text="unauthorized")
        )
        with pytest.raises(ToolError) as excinfo:
            await caldav.discover_calendars(client, creds)

    assert route.call_count == 1, "a repeated auth failure slows the whole instance down"
    assert "app password" in excinfo.value.message.lower()


# --------------------------------------------------------------------------------------
# The four case time matrix (01-RESEARCH.md, pitfall 4)
# --------------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_matrix_a_a_berlin_event_read_through_a_utc_window(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Case (a): 14:00 in Berlin is 12:00 UTC, and it stays that instant."""
    start = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 16, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(return_value=report_response())
        events = await caldav.query_events(client, creds, "personal", start, end)

    meeting = next(event for event in events if event["uid"] == "berlin-meeting-uid")
    assert meeting["start"] == datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    assert meeting["end"] == datetime(2026, 9, 15, 13, 0, tzinfo=UTC)
    assert meeting["start"].astimezone(BERLIN).hour == 14
    assert meeting["all_day"] is False
    assert meeting["summary"] == "Projektbesprechung"
    assert meeting["location"] == "Hamburg, Straße 1"


@pytest.mark.anyio
async def test_matrix_b_a_series_across_the_dst_boundary_keeps_its_local_time(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Case (b): 09:00 Berlin is 07:00Z before and 08:00Z after the change of clocks."""
    start = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(return_value=report_response())
        events = await caldav.query_events(client, creds, "personal", start, end)

    standups = [event for event in events if event["uid"] == "weekly-standup-uid"]
    assert len(standups) == 2, "the server expands the series, we only read the instances"

    assert [event["start"] for event in standups] == [
        datetime(2026, 10, 19, 7, 0, tzinfo=UTC),
        datetime(2026, 10, 26, 8, 0, tzinfo=UTC),
    ]
    assert {event["start"].astimezone(BERLIN).hour for event in standups} == {9}
    assert {event["start"].astimezone(BERLIN).utcoffset() for event in standups} == {
        timedelta(hours=2),
        timedelta(hours=1),
    }


@pytest.mark.anyio
async def test_matrix_c_an_all_day_event_stays_a_date(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Case (c): ``VALUE=DATE`` has no time and no zone; midnight would shift it."""
    start = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(return_value=report_response())
        events = await caldav.query_events(client, creds, "personal", start, end)

    outing = next(event for event in events if event["uid"] == "betriebsausflug-uid")
    assert outing["all_day"] is True
    assert outing["start"] == date(2026, 10, 24)
    assert outing["end"] == date(2026, 10, 25)
    assert not isinstance(outing["start"], datetime)


@pytest.mark.anyio
async def test_matrix_d_a_window_that_ends_on_the_event_start_is_sent_unchanged(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Case (d): ``time-range`` is half open, and we do not fudge the boundary."""
    start = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)  # exactly the start of the Berlin meeting

    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="REPORT", url=PERSONAL).mock(return_value=empty_multistatus())
        events = await caldav.query_events(client, creds, "personal", start, end)

    assert events == []
    body = etree.fromstring(route.calls[0].request.content, parser=davxml.hardened_parser())
    time_range = body.find(f".//{{{davxml.CAL}}}time-range")
    assert time_range is not None
    assert time_range.get("end") == "20260915T120000Z", "no second added, no second removed"


# --------------------------------------------------------------------------------------
# ICS parsing
# --------------------------------------------------------------------------------------


def test_parsing_an_all_day_ics_yields_a_pure_date() -> None:
    events = caldav.parse_ics(
        fixture("event_allday.ics"), calendar_uri="personal", object_name="allday.ics"
    )

    assert len(events) == 1
    assert events[0]["all_day"] is True
    assert events[0]["start"] == date(2026, 10, 24)
    assert events[0]["end"] == date(2026, 10, 25)
    assert events[0]["id"] == "event:personal:allday.ics"


def test_parsing_a_series_never_expands_it_in_this_process() -> None:
    """The RRULE fixture must stay one event: sabre expands, this module does not."""
    events = caldav.parse_ics(
        fixture("event_berlin_dst.ics"),
        calendar_uri="personal",
        object_name="weekly-standup.ics",
    )

    assert len(events) == 1, "a client side expansion would produce three instances here"
    assert events[0]["start"] == datetime(2026, 10, 19, 7, 0, tzinfo=UTC)
    assert events[0]["start"].astimezone(BERLIN).hour == 9


def test_the_module_does_not_iterate_recurrences_itself() -> None:
    """D-17 as a grep: no recurring-ical-events, no hand rolled recurrence walk."""
    source = Path(caldav.__file__).read_text(encoding="utf-8").lower()
    assert "recurring_ical_events" not in source
    assert "recurring-ical-events" not in source
    assert "rrulestr" not in source, "dateutil expansion would duplicate the server's work"
    assert "dateutil" not in source
    for access in ('get("rrule")', "get('rrule')", '["rrule"]', "['rrule']"):
        assert access not in source, f"the module reads {access}, so it interprets recurrences"


@pytest.mark.anyio
async def test_the_object_name_comes_from_the_href_and_not_from_the_uid(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The UID is content, the object name is the address. Only one of them addresses."""
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(return_value=report_response())
        events = await caldav.query_events(client, creds, "personal", start, end)

    meeting = next(event for event in events if event["uid"] == "berlin-meeting-uid")
    assert meeting["id"] == "event:personal:berlin-meeting.ics"


# --------------------------------------------------------------------------------------
# Guards and status handling
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("uri", ["../contacts", "personal/sub", "", "  ", "with\nnewline"])
def test_a_calendar_uri_that_could_leave_the_collection_is_refused(
    creds: Credentials, uri: str
) -> None:
    """Threat T-01-51: the URI is a single path segment, never a path."""
    with pytest.raises(ToolError):
        caldav.calendar_url(creds, uri)


@pytest.mark.anyio
async def test_an_unknown_calendar_is_reported_as_not_found(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 30, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=f"{CALENDAR_HOME}weg/").mock(
            return_value=httpx.Response(404, text="not found")
        )
        with pytest.raises(ToolError) as excinfo:
            await caldav.query_events(client, creds, "weg", start, end)

    assert "weg" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_server_error_during_the_query_is_reported_with_its_status(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 30, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(
            return_value=httpx.Response(503, text="service unavailable")
        )
        with pytest.raises(ToolError) as excinfo:
            await caldav.query_events(client, creds, "personal", start, end)

    assert "503" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_redirect_is_never_followed(client: httpx.AsyncClient, creds: Credentials) -> None:
    """A redirect would carry the Authorization header to a foreign host (T-01-08)."""
    start = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 30, 0, 0, tzinfo=UTC)

    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=PERSONAL).mock(
            return_value=httpx.Response(302, headers={"Location": "http://evil.test/"})
        )
        with pytest.raises(ToolError) as excinfo:
            await caldav.query_events(client, creds, "personal", start, end)

    assert "redirect" in excinfo.value.message.lower()


# --------------------------------------------------------------------------------------
# Write path (task 3 fills the tool layer; the client contract is pinned here)
# --------------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_put_event_sends_if_none_match_star(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.put(f"{PERSONAL}new-event.ics").mock(
            return_value=httpx.Response(201, headers={"ETag": '"abc"'})
        )
        result = await caldav.put_event(
            client, creds, "personal", "new-event.ics", b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"
        )

    request = route.calls[0].request
    assert request.headers["If-None-Match"] == "*"
    assert request.headers["Content-Type"] == "text/calendar; charset=utf-8"
    assert result["created"] is True


@pytest.mark.anyio
async def test_put_event_reports_an_existing_object_as_a_conflict(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.put(f"{PERSONAL}new-event.ics").mock(return_value=httpx.Response(412, text="exists"))
        with pytest.raises(ConflictError):
            await caldav.put_event(client, creds, "personal", "new-event.ics", b"x")


@pytest.mark.anyio
async def test_put_event_treats_a_replacing_answer_as_a_broken_promise(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """204 means the precondition was ignored and something was overwritten. Say so."""
    with respx.mock(assert_all_called=True) as mock:
        mock.put(f"{PERSONAL}new-event.ics").mock(return_value=httpx.Response(204))
        with pytest.raises(ToolError) as excinfo:
            await caldav.put_event(client, creds, "personal", "new-event.ics", b"x")

    assert "replaced" in excinfo.value.message.lower()


@pytest.mark.anyio
async def test_get_event_reads_the_stored_object_back(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(f"{PERSONAL}betriebsausflug.ics").mock(
            return_value=httpx.Response(
                200,
                text=fixture("event_allday.ics"),
                headers={"Content-Type": "text/calendar; charset=utf-8"},
            )
        )
        events = await caldav.get_event(client, creds, "personal", "betriebsausflug.ics")

    assert events[0]["all_day"] is True
    assert events[0]["id"] == "event:personal:betriebsausflug.ics"
