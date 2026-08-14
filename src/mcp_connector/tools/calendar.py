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
from datetime import UTC, date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from ..errors import ToolError
from ..nextcloud import NcClients
from ..nextcloud.clients import caldav

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

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
