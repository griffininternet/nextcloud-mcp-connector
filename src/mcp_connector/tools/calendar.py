"""Calendar tools: reading a window of events (D-04).

Three properties of this tool are contract, not implementation detail.

**The window is mandatory and carries a zone.** ``start`` and ``end`` are ISO 8601 strings
with an offset or ``Z``. A string without a zone is refused with the shape that works,
because guessing a zone is how an appointment moves by two hours (pitfall 4). The optional
``timezone`` parameter changes only how the answer is written, never which instants are
returned; the query always runs in UTC.

**All calendars are asked at once.** Without a ``calendar`` parameter the tool fans out over
every event calendar of the account. Each request has its own timeout, and a calendar that
fails is listed under ``degraded`` instead of quietly shrinking the result. A partial answer
that says it is partial is useful; one that does not is a lie the model will repeat.

**An account without a calendar is not an empty schedule.** The client turns that case into
an error with a way out, and this tool lets it through unchanged (pitfall 3).

Deliberately absent: a capabilities check. CalDAV is part of the core ``dav`` app, the
Calendar app is only its web interface, so requiring it would refuse to work on instances
where the tool works perfectly well. The honest precondition is "does a collection exist",
and that is what the discovery answers.

Timezone data comes from ``tzdata``: Windows has no system tz database, so ``zoneinfo``
finds nothing without it.
"""

import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from icalendar import Calendar as IcsCalendar
from icalendar import Event as IcsEvent
from icalendar import Timezone as IcsTimezone

from .. import ids
from ..errors import ToolError
from ..nextcloud import NcClients
from ..nextcloud.clients import caldav

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

#: Identifies this generator in every object it writes, as RFC 5545 asks for.
PRODID = "-//Nextcloud MCP Connector//nextcloud-mcp-connector 0.1//EN"

#: Wall clock budget for one calendar. A single slow collection must not hold the answer
#: hostage; it becomes a named degradation instead (threat T-01-50).
PER_CALENDAR_TIMEOUT = 20.0

_TIME_HINT = (
    "Use ISO 8601 with a zone, for example 2026-09-01T00:00:00+02:00 or 2026-09-01T00:00:00Z."
)

_ZONE_HINT = "Use an IANA name such as Europe/Berlin or UTC."


async def list_events(
    clients: NcClients,
    start: str,
    end: str,
    calendar: str | None = None,
    timezone: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Read every event instance between ``start`` and ``end`` across the user's calendars."""
    if limit < 1 or limit > MAX_LIMIT:
        raise ToolError(
            message=f"limit must be between 1 and {MAX_LIMIT} (got {limit}).",
            hint=f"Leave it out for the default of {DEFAULT_LIMIT} events.",
        )

    window_start = parse_instant(start, field="start")
    window_end = parse_instant(end, field="end")
    if window_end <= window_start:
        raise ToolError(
            message="end must be after start.",
            hint="Ask for a window such as one day, one week or one month.",
        )
    zone = resolve_zone(timezone)

    calendars = await caldav.discover_calendars(clients.client, clients.creds)
    selected = _select(calendars, calendar)

    results = await asyncio.gather(
        *(_query_one(clients, entry, window_start, window_end) for entry in selected),
        return_exceptions=True,
    )

    events: list[dict[str, Any]] = []
    degraded: list[dict[str, str]] = []
    for entry, outcome in zip(selected, results, strict=True):
        if isinstance(outcome, BaseException):
            degraded.append({"calendar": entry.display_name, "reason": _reason(outcome)})
            continue
        events.extend(outcome)

    if degraded and not events and len(degraded) == len(selected):
        # Every calendar failed. Reporting an empty schedule here would be the worst of
        # both worlds: no data and no error the caller could act on.
        raise ToolError(
            message="None of the calendars could be read.",
            hint="; ".join(item["reason"] for item in degraded),
        )

    events.sort(key=_sort_key)
    truncated = len(events) > limit
    events = events[:limit]

    result: dict[str, Any] = {
        "range": {"start": start, "end": end, "timezone": timezone or "UTC"},
        "count": len(events),
        "events": [_as_output(event, zone) for event in events],
    }
    if truncated:
        result["truncated"] = True
    if degraded:
        result["degraded"] = degraded
    return result


def parse_instant(value: str, field: str) -> datetime:
    """Parse one ISO 8601 boundary and insist on a zone (pitfall 4, cause 3)."""
    raw = (value or "").strip()
    try:
        parsed = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        raise ToolError(
            message=f"{field} is not a valid date and time ({value!r}).",
            hint=_TIME_HINT,
        ) from None

    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise ToolError(
            message=f"{field} has no timezone ({value!r}).",
            hint=_TIME_HINT,
        )
    return parsed


def resolve_zone(name: str | None) -> ZoneInfo | Any:
    """Return the display zone. UTC when none was asked for, an error when it is unknown."""
    if not name or not name.strip():
        return UTC
    try:
        return ZoneInfo(name.strip())
    except (ZoneInfoNotFoundError, ValueError):
        raise ToolError(
            message=f"{name!r} is not a known timezone.",
            hint=_ZONE_HINT,
        ) from None


def _select(calendars: list[caldav.CalendarRef], wanted: str | None) -> list[caldav.CalendarRef]:
    """Resolve the calendar parameter against the discovery, or fail with the real names.

    The parameter never reaches a URL unchecked; it selects from a list the server sent
    (threat T-01-51). Both the URI and the display name are accepted, because a model that
    has read one answer knows the display name.
    """
    if wanted is None or not wanted.strip():
        return calendars

    needle = wanted.strip().casefold()
    matches = [
        entry
        for entry in calendars
        if entry.uri.casefold() == needle or entry.display_name.casefold() == needle
    ]
    if matches:
        return matches

    available = ", ".join(sorted({entry.display_name for entry in calendars}))
    raise ToolError(
        message=f"This account has no calendar called {wanted!r}.",
        hint=f"Available calendars: {available}.",
    )


async def _query_one(
    clients: NcClients,
    entry: caldav.CalendarRef,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    async with asyncio.timeout(PER_CALENDAR_TIMEOUT):
        return await caldav.query_events(
            clients.client,
            clients.creds,
            entry.uri,
            start,
            end,
            calendar=entry.display_name,
        )


def _reason(exc: BaseException) -> str:
    """One sentence per failed calendar. Unknown failures are bugs and stay loud."""
    if isinstance(exc, ToolError):
        return exc.message
    if isinstance(exc, TimeoutError | httpx.TimeoutException):
        return f"The calendar did not answer within {PER_CALENDAR_TIMEOUT:.0f} seconds."
    if isinstance(exc, httpx.RequestError):
        return "The calendar could not be reached."
    raise exc


async def create_event(
    clients: NcClients,
    summary: str,
    start: str,
    end: str,
    calendar: str | None = None,
    location: str | None = None,
    description: str | None = None,
    all_day: bool = False,
    timezone: str | None = None,
) -> dict[str, Any]:
    """Create one new event and answer with the times the server confirmed.

    The object name is a fresh UUID and the write carries ``If-None-Match: *``, so this
    call can add an event but never replace one (TOOL-09, threat T-01-48). Afterwards the
    object is read back once: a server that silently drops a field is the documented bug
    class here, and only the read back exposes it.
    """
    title = (summary or "").strip()
    if not title:
        raise ToolError(
            message="An event needs a summary.",
            hint="Give a short title, for example 'Projektbesprechung'.",
        )

    zone = resolve_zone(timezone)
    if all_day:
        begin, finish = _all_day_window(start, end)
    else:
        begin, finish = _timed_window(start, end, zone if timezone else UTC)

    calendars = await caldav.discover_calendars(clients.client, clients.creds)
    target = _select(calendars, calendar)[0]

    object_name = f"{uuid.uuid4()}.ics"
    uid = object_name.removesuffix(".ics")
    ics = build_ics(
        uid=uid,
        summary=title,
        start=begin,
        end=finish,
        location=(location or "").strip() or None,
        description=(description or "").strip() or None,
        tzid=timezone if not all_day and timezone else None,
    )

    await caldav.put_event(clients.client, clients.creds, target.uri, object_name, ics)

    confirmed = await _read_back(clients, target, object_name)
    event = confirmed or {
        "id": ids.encode_event(target.uri, object_name),
        "uid": uid,
        "summary": title,
        "start": begin,
        "end": finish,
        "all_day": all_day,
        "location": location or "",
        "calendar": target.display_name,
    }

    result = _as_output(event, zone)
    result["created"] = True
    result["confirmed"] = confirmed is not None
    return result


async def _read_back(
    clients: NcClients, target: caldav.CalendarRef, object_name: str
) -> dict[str, Any] | None:
    """Read the created object once. A failure here does not undo the write.

    Reporting an error after a successful PUT would be the worst possible answer: the model
    would create the event a second time, and this server cannot delete the first one.
    """
    try:
        events = await caldav.get_event(
            clients.client,
            clients.creds,
            target.uri,
            object_name,
            calendar=target.display_name,
        )
    except ToolError:
        return None
    except (TimeoutError, httpx.TimeoutException, httpx.RequestError):
        return None
    return events[0] if events else None


def _all_day_window(start: str, end: str) -> tuple[date, date]:
    """Two pure dates, with the RFC 5545 exclusive end applied to a single day event."""
    begin = _parse_day(start, field="start")
    finish = _parse_day(end, field="end")
    if finish < begin:
        raise ToolError(
            message="end must not be before start.",
            hint="For an all day event give the last day or the day after it, e.g. 2026-10-25.",
        )
    if finish == begin:
        # RFC 5545 counts the end out, so start == end would be an event of zero length.
        finish = begin + timedelta(days=1)
    return begin, finish


def _timed_window(start: str, end: str, zone: Any) -> tuple[datetime, datetime]:
    """Two instants, expressed in the zone that will be written into the object."""
    begin = parse_instant(start, field="start")
    finish = parse_instant(end, field="end")
    if finish <= begin:
        raise ToolError(
            message="end must be after start.",
            hint="An event needs a duration; give an end after the start.",
        )
    return begin.astimezone(zone), finish.astimezone(zone)


def _parse_day(value: str, field: str) -> date:
    raw = (value or "").strip()
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise ToolError(
            message=f"{field} is not a date ({value!r}).",
            hint="An all day event takes a plain date, for example 2026-10-24.",
        ) from None


def build_ics(
    *,
    uid: str,
    summary: str,
    start: datetime | date,
    end: datetime | date,
    location: str | None = None,
    description: str | None = None,
    tzid: str | None = None,
) -> bytes:
    """Build one VCALENDAR with exactly one VEVENT, always through icalendar.

    Never by string concatenation: RFC 5545 escaping, line folding and the ``VALUE=DATE``
    form are exactly the places where a hand written generator breaks, and a summary that
    contains a line break would otherwise be able to open a second component
    (threat T-01-46).
    """
    calendar = IcsCalendar()
    calendar.add("prodid", PRODID)
    calendar.add("version", "2.0")

    if tzid is not None and isinstance(start, datetime) and start.tzinfo is not None:
        # An IANA TZID with a matching VTIMEZONE. A Windows identifier such as
        # "W. Europe Standard Time" is the classic interop killer and cannot appear here,
        # because the component is generated from the zoneinfo database itself.
        year = start.year
        component = IcsTimezone.from_tzinfo(
            start.tzinfo,
            tzid=tzid,
            first_date=date(year - 1, 1, 1),
            last_date=date(year + 5, 1, 1),
        )
        component.pop("COMMENT", None)
        calendar.add_component(component)

    event = IcsEvent()
    event.add("uid", uid)
    event.add("dtstamp", datetime.now(UTC))
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("summary", summary)
    if location:
        event.add("location", location)
    if description:
        event.add("description", description)
    calendar.add_component(event)

    return calendar.to_ical()


def _sort_key(event: dict[str, Any]) -> datetime:
    value = event["start"]
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min, tzinfo=UTC)


def _as_output(event: dict[str, Any], zone: Any) -> dict[str, Any]:
    """Project one event onto the stable answer shape, in the requested representation."""
    result: dict[str, Any] = {
        "id": event["id"],
        "uid": event["uid"],
        "summary": event["summary"],
        "start": _format(event["start"], zone),
        "end": _format(event["end"], zone),
        "all_day": event["all_day"],
        "calendar": event["calendar"],
    }
    if event.get("location"):
        # Omitted when empty: every key costs tokens in every event of every answer.
        result["location"] = event["location"]
    return result


def _format(value: datetime | date, zone: Any) -> str:
    """An instant in the display zone, or a pure date that never grows a time."""
    if isinstance(value, datetime):
        return value.astimezone(zone).isoformat()
    return value.isoformat()
