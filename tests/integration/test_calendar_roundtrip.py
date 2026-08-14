"""Calendar round trip against a real Nextcloud 34 with CalDAV (opt-in).

The unit tests pin the shapes against recorded fixtures. Only a real sabre answers the
questions that actually decide whether the calendar tools are correct: does the server
expand a series the way we assume, does it keep the instant of a Berlin event across the
change of clocks, is ``time-range`` really half open, and does ``If-None-Match: *`` really
refuse the second write.

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

import uuid

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ConflictError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import caldav
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import calendar as calendar_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def token() -> str:
    """A marker that makes one test run's events findable among all others."""
    return f"MCP-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def clients(live_env: dict[str, str | None]) -> NcClients:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")

    user = live_env["user"]
    assert user != "admin", "integration tests run as a normal user, never as admin"

    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(str(live_env["base_url"])),
            user=str(user),
            secret=str(live_env["secret"]),
        ),
    )


async def test_the_bootstrap_calendar_is_discovered(clients: NcClients) -> None:
    """``occ dav:create-calendar alice personal`` uses the name directly as the URI."""
    calendars = await caldav.discover_calendars(clients.client, clients.creds)

    assert calendars, "the bootstrap creates a calendar; pitfall 3 says it does not exist by login"
    assert "personal" in {entry.uri for entry in calendars}


async def test_a_berlin_event_is_found_again_through_a_utc_window(
    clients: NcClients,
) -> None:
    marker = token()
    created = await calendar_tools.create_event(
        clients,
        summary=f"{marker} Projektbesprechung",
        start="2026-09-15T14:00:00+02:00",
        end="2026-09-15T15:00:00+02:00",
        location="Hamburg, Straße 1",
        timezone="Europe/Berlin",
    )

    assert created["created"] is True
    assert created["confirmed"] is True, "the server confirmed the times by read back"
    assert created["start"] == "2026-09-15T14:00:00+02:00"

    found = await calendar_tools.list_events(
        clients, start="2026-09-15T00:00:00Z", end="2026-09-16T00:00:00Z"
    )
    event = next(item for item in found["events"] if item["id"] == created["id"])

    assert event["start"] == "2026-09-15T12:00:00+00:00", "14:00 in Berlin is 12:00 UTC"
    assert event["end"] == "2026-09-15T13:00:00+00:00"
    assert event["all_day"] is False
    assert event["location"] == "Hamburg, Straße 1"


async def test_two_events_around_the_dst_boundary_keep_their_local_time(
    clients: NcClients,
) -> None:
    """The proof against the real server: 09:00 Berlin is 07:00Z, then 08:00Z."""
    marker = token()
    before = await calendar_tools.create_event(
        clients,
        summary=f"{marker} Standup CEST",
        start="2026-10-19T09:00:00+02:00",
        end="2026-10-19T09:15:00+02:00",
        timezone="Europe/Berlin",
    )
    after = await calendar_tools.create_event(
        clients,
        summary=f"{marker} Standup CET",
        start="2026-10-26T09:00:00+01:00",
        end="2026-10-26T09:15:00+01:00",
        timezone="Europe/Berlin",
    )

    found = await calendar_tools.list_events(
        clients, start="2026-10-01T00:00:00Z", end="2026-11-01T00:00:00Z"
    )
    by_id = {item["id"]: item for item in found["events"]}

    assert by_id[before["id"]]["start"] == "2026-10-19T07:00:00+00:00"
    assert by_id[after["id"]]["start"] == "2026-10-26T08:00:00+00:00"

    shown = await calendar_tools.list_events(
        clients,
        start="2026-10-01T00:00:00Z",
        end="2026-11-01T00:00:00Z",
        timezone="Europe/Berlin",
    )
    local = {item["id"]: item for item in shown["events"]}
    assert local[before["id"]]["start"] == "2026-10-19T09:00:00+02:00"
    assert local[after["id"]]["start"] == "2026-10-26T09:00:00+01:00"


async def test_an_all_day_event_stays_a_date_on_the_server(clients: NcClients) -> None:
    marker = token()
    created = await calendar_tools.create_event(
        clients,
        summary=f"{marker} Betriebsausflug",
        start="2026-10-24",
        end="2026-10-24",
        all_day=True,
    )

    assert created["all_day"] is True
    assert created["start"] == "2026-10-24"
    assert created["end"] == "2026-10-25", "RFC 5545 counts the end of an all day event out"

    found = await calendar_tools.list_events(
        clients,
        start="2026-10-20T00:00:00Z",
        end="2026-10-30T00:00:00Z",
        timezone="Europe/Berlin",
    )
    event = next(item for item in found["events"] if item["id"] == created["id"])

    assert event["all_day"] is True
    assert event["start"] == "2026-10-24", "not a midnight, and not the day before"
    assert "T" not in event["start"]


async def test_a_window_that_ends_on_the_event_start_excludes_it(clients: NcClients) -> None:
    """Matrix case (d) against sabre: ``time-range`` is half open, on the server too."""
    marker = token()
    created = await calendar_tools.create_event(
        clients,
        summary=f"{marker} Grenzfall",
        start="2026-09-20T10:00:00Z",
        end="2026-09-20T11:00:00Z",
    )

    excluded = await calendar_tools.list_events(
        clients, start="2026-09-20T09:00:00Z", end="2026-09-20T10:00:00Z"
    )
    assert created["id"] not in {item["id"] for item in excluded["events"]}

    included = await calendar_tools.list_events(
        clients, start="2026-09-20T09:00:00Z", end="2026-09-20T10:00:01Z"
    )
    assert created["id"] in {item["id"] for item in included["events"]}


async def test_the_same_calendar_object_cannot_be_written_twice(clients: NcClients) -> None:
    """The write promise (TOOL-09) against the real precondition handling of sabre."""
    object_name = f"{uuid.uuid4()}.ics"
    ics = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//test//EN\r\n"
        "BEGIN:VEVENT\r\nUID:" + object_name[:-4] + "\r\nDTSTAMP:20260901T101500Z\r\n"
        "DTSTART:20260921T100000Z\r\nDTEND:20260921T110000Z\r\n"
        "SUMMARY:Kein Ueberschreiben\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    ).encode("utf-8")

    first = await caldav.put_event(clients.client, clients.creds, "personal", object_name, ics)
    assert first["created"] is True

    with pytest.raises(ConflictError):
        await caldav.put_event(clients.client, clients.creds, "personal", object_name, ics)


async def test_an_empty_window_is_an_empty_list(clients: NcClients) -> None:
    result = await calendar_tools.list_events(
        clients, start="2019-01-01T00:00:00Z", end="2019-01-02T00:00:00Z"
    )

    assert result["events"] == []
    assert result["count"] == 0
    assert "degraded" not in result
