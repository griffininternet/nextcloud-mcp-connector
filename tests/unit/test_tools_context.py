"""Unit tests for ``prepare_context``, the bundling read (TOOL-08, D-52 to D-57).

The tool owns no data source of its own: it composes the unified search and the calendar
window, so the tests are written against the composition and never against a happy path.

Three of them are guards rather than checks. One proves that the search is asked **without**
a provider restriction, because a hardcoded provider list would lock out an installed
Findling and every future provider (D-53). One proves that a stalling calendar becomes a
named degradation while the finished search hits still arrive, because a global timeout
around the bundle would throw both away (pitfall 4 and 5). One proves that both sources
run at the same time, by making each fake wait for the other: a sequential implementation
deadlocks and the test fails on its own timeout.
"""

import asyncio
from datetime import timedelta
from typing import Any

import httpx
import pytest

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import calendar as calendar_tools
from mcp_connector.tools import context as context_tools
from mcp_connector.tools import search as search_tools

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def hit(
    identifier: str,
    title: str,
    provider: str,
    kind: str,
    **extra: Any,
) -> dict[str, Any]:
    """One unified search hit in the shape ``tools/search.py`` produces."""
    entry: dict[str, Any] = {
        "id": identifier,
        "title": title,
        "subline": "in Dokumente",
        "url": f"{BASE}/index.php/f/1",
        "provider": provider,
        "kind": kind,
    }
    entry.update(extra)
    return entry


FILE_HIT = hit("file:4711", "Budget 2026.md", "files", "file")
NOTE_HIT = hit("note:12", "Protokoll 2026-08-14", "notes", "note")
CARD_HIT = hit(
    "card:57", "Übergabe vorbereiten", "search-deck-card-board", "card", resolvable=False
)
TALK_HIT = hit(
    f"url:{BASE}/index.php/call/abc123#message_42",
    "Khaled",
    "spreed",
    "url",
    resolvable=False,
)


def search_answer(
    hits: list[dict[str, Any]],
    degraded: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    answer: dict[str, Any] = {
        "query": "budget",
        "count": len(hits),
        "results": hits,
        "note": search_tools.SEARCH_NOTE,
    }
    if degraded is not None:
        answer["degraded"] = degraded
    return answer


def event(summary: str, start: str) -> dict[str, Any]:
    return {
        "id": f"event:personal:{summary}.ics",
        "uid": summary,
        "summary": summary,
        "start": start,
        "end": start,
        "all_day": False,
        "calendar": "Persönlich",
    }


def calendar_answer(
    events: list[dict[str, Any]],
    degraded: list[dict[str, str]] | None = None,
    truncated: bool = False,
) -> dict[str, Any]:
    answer: dict[str, Any] = {
        "range": {"start": "", "end": "", "timezone": "UTC"},
        "count": len(events),
        "events": events,
    }
    if truncated:
        answer["truncated"] = True
    if degraded is not None:
        answer["degraded"] = degraded
    return answer


class FakeCall:
    """A stand in for one of the two composed tools that records how it was called."""

    def __init__(
        self,
        answer: dict[str, Any] | None = None,
        error: BaseException | None = None,
        hang: bool = False,
    ) -> None:
        self.answer = answer
        self.error = error
        self.hang = hang
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    async def __call__(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((args, kwargs))
        if self.hang:
            await asyncio.sleep(3600)
        if self.error is not None:
            raise self.error
        return self.answer if self.answer is not None else {}

    @property
    def kwargs(self) -> dict[str, Any]:
        assert self.calls, "the tool was never called"
        return self.calls[0][1]


def wire(
    monkeypatch: pytest.MonkeyPatch,
    search: FakeCall | None = None,
    calendar: FakeCall | None = None,
) -> tuple[FakeCall, FakeCall]:
    """Replace the two composed tools, so these tests never touch the network."""
    search = search if search is not None else FakeCall(search_answer([FILE_HIT]))
    calendar = calendar if calendar is not None else FakeCall(calendar_answer([]))
    monkeypatch.setattr(search_tools, "unified_search", search)
    monkeypatch.setattr(calendar_tools, "list_events", calendar)
    return search, calendar


@pytest.mark.anyio
async def test_one_call_bundles_hits_by_kind_and_the_window_of_the_next_seven_days(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bundle is grouped by ``kind`` and never by provider id (pitfall 9)."""
    search, calendar = wire(
        monkeypatch,
        search=FakeCall(search_answer([FILE_HIT, NOTE_HIT, CARD_HIT, TALK_HIT])),
        calendar=FakeCall(calendar_answer([event("Standup", "2026-08-18T09:00:00+00:00")])),
    )

    result = await context_tools.prepare_context(clients, query="budget")

    assert search.calls, "the search is asked in the same call"
    assert calendar.calls, "the calendar is asked in the same call"
    assert result["query"] == "budget"
    assert result["note"] == search_tools.SEARCH_NOTE, "one wording for one caveat"
    assert "degraded" not in result, "nothing failed, so the key costs no bytes"

    assert set(result["results"]) == {"file", "note", "card", "other"}
    assert [entry["id"] for entry in result["results"]["file"]] == ["file:4711"]
    assert [entry["id"] for entry in result["results"]["note"]] == ["note:12"]
    assert [entry["id"] for entry in result["results"]["card"]] == ["card:57"]
    assert [entry["id"] for entry in result["results"]["other"]] == [TALK_HIT["id"]]
    assert result["results"]["other"][0]["resolvable"] is False, "an url id resolves to nothing"
    assert result["results"]["card"][0]["resolvable"] is False, "the short card form needs a sweep"

    assert result["results"]["file"][0] == {
        "id": "file:4711",
        "title": "Budget 2026.md",
        "provider": "files",
        "kind": "file",
    }, "short carries the origin as fields and nothing else (D-54, D-57)"

    assert [item["summary"] for item in result["events"]] == ["Standup"]

    window = result["window"]
    start = calendar_tools.parse_instant(window["start"], field="start")
    end = calendar_tools.parse_instant(window["end"], field="end")
    assert (end - start).days == 7, "the window is now until now plus seven days"
    assert start.utcoffset() == timedelta(0), "the window starts in UTC"
    assert end.utcoffset() == timedelta(0), "the window ends in UTC"
    assert calendar.kwargs["start"] == window["start"], "the answer names the window it asked for"
    assert calendar.kwargs["end"] == window["end"]


@pytest.mark.anyio
async def test_the_search_is_asked_without_any_provider_restriction(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-53: a hardcoded provider list would lock out an installed Findling forever."""
    search, _calendar = wire(monkeypatch)

    await context_tools.prepare_context(clients, query="budget")

    args, kwargs = search.calls[0]
    assert kwargs.get("providers") is None, "no provider restriction reaches the unified search"
    assert "providers" not in kwargs, "the parameter is not passed at all"
    assert len(args) == 1, "only the clients travel positionally, never a provider list"
    assert kwargs["query"] == "budget"
    assert kwargs["limit"] == context_tools.SEARCH_LIMIT


@pytest.mark.anyio
async def test_both_sources_run_at_the_same_time(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each fake waits for the other: a sequential implementation cannot finish this."""
    search_started = asyncio.Event()
    calendar_started = asyncio.Event()

    async def fake_search(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        search_started.set()
        await asyncio.wait_for(calendar_started.wait(), timeout=5)
        return search_answer([FILE_HIT])

    async def fake_calendar(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calendar_started.set()
        await asyncio.wait_for(search_started.wait(), timeout=5)
        return calendar_answer([])

    monkeypatch.setattr(search_tools, "unified_search", fake_search)
    monkeypatch.setattr(calendar_tools, "list_events", fake_calendar)

    result = await asyncio.wait_for(
        context_tools.prepare_context(clients, query="budget"), timeout=10
    )

    assert [entry["id"] for entry in result["results"]["file"]] == ["file:4711"]


@pytest.mark.anyio
async def test_a_stalling_calendar_is_named_and_the_search_hits_still_arrive(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pitfall 4 and 5: the own, tighter cap degrades the calendar, not the whole bundle."""
    monkeypatch.setattr(context_tools, "CALENDAR_BUDGET", 0.05)
    _search, _calendar = wire(
        monkeypatch,
        search=FakeCall(search_answer([FILE_HIT, NOTE_HIT])),
        calendar=FakeCall(hang=True),
    )

    result = await asyncio.wait_for(
        context_tools.prepare_context(clients, query="budget"), timeout=10
    )

    assert [entry["id"] for entry in result["results"]["file"]] == ["file:4711"]
    assert [entry["id"] for entry in result["results"]["note"]] == ["note:12"]
    assert result["events"] == [], "no events, and the reason is spelled out"
    assert result["degraded"] == [
        {
            "source": "calendar",
            "reason": "The calendar did not answer within 0.05 seconds.",
        }
    ]


def test_the_calendar_cap_of_this_tool_is_tighter_than_the_standalone_one() -> None:
    """Pitfall 5: 20 seconds in one source would fill the whole bundle budget alone."""
    assert context_tools.CALENDAR_BUDGET == 10.0
    assert context_tools.CALENDAR_BUDGET < calendar_tools.PER_CALENDAR_TIMEOUT


@pytest.mark.anyio
async def test_a_failing_search_is_named_and_the_events_still_arrive(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror image: the calendar answer is never discarded because the search fell over."""
    wire(
        monkeypatch,
        search=FakeCall(error=httpx.ConnectError("no route")),
        calendar=FakeCall(calendar_answer([event("Standup", "2026-08-18T09:00:00+00:00")])),
    )

    result = await context_tools.prepare_context(clients, query="budget")

    assert [item["summary"] for item in result["events"]] == ["Standup"]
    assert result["results"] == {"file": [], "note": [], "card": [], "other": []}
    assert result["degraded"] == [
        {"source": "search", "reason": "The search could not be reached."}
    ]


@pytest.mark.anyio
async def test_the_degraded_entries_of_the_search_are_passed_through_unchanged(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-55: one form for one problem; the search already writes the right sentence."""
    entries = [{"provider": "files", "reason": "The provider could not be reached."}]
    wire(
        monkeypatch,
        search=FakeCall(search_answer([NOTE_HIT], degraded=entries)),
        calendar=FakeCall(calendar_answer([], degraded=[{"calendar": "Team", "reason": "boom"}])),
    )

    result = await context_tools.prepare_context(clients, query="budget")

    assert entries[0] in result["degraded"], "the provider entry arrives verbatim"
    assert {"calendar": "Team", "reason": "boom"} in result["degraded"], (
        "a partly degraded calendar is not silently complete either (SC 4)"
    )


@pytest.mark.anyio
async def test_a_bundle_without_any_source_is_an_error_and_never_an_empty_answer(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both sources gone means no data at all; an empty bundle would be read as "nothing"."""
    wire(
        monkeypatch,
        search=FakeCall(error=httpx.ConnectError("no route")),
        calendar=FakeCall(
            error=ToolError(message="None of the calendars could be read.", hint="x")
        ),
    )

    with pytest.raises(ToolError) as excinfo:
        await context_tools.prepare_context(clients, query="budget")

    assert "search" in excinfo.value.message.lower()
    assert "The search could not be reached." in excinfo.value.hint
    assert "None of the calendars could be read." in excinfo.value.hint


@pytest.mark.anyio
async def test_an_empty_bundle_is_a_valid_answer_with_empty_buckets(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """no_data: nothing matched is a result, not a failure."""
    wire(monkeypatch, search=FakeCall(search_answer([])), calendar=FakeCall(calendar_answer([])))

    result = await context_tools.prepare_context(clients, query="budget")

    assert result["results"] == {"file": [], "note": [], "card": [], "other": []}
    assert result["events"] == []
    assert "degraded" not in result


@pytest.mark.anyio
async def test_short_caps_every_bucket_and_says_that_it_capped(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-54: predictable tokens, and SC 4 forbids a silently shortened list."""
    many = [hit(f"file:{index}", f"Datei {index}", "files", "file") for index in range(9)]
    wire(monkeypatch, search=FakeCall(search_answer(many)))

    result = await context_tools.prepare_context(clients, query="budget")

    assert len(result["results"]["file"]) == context_tools.MAX_PER_BUCKET == 5
    assert [entry["id"] for entry in result["results"]["file"]] == [f"file:{i}" for i in range(5)]
    assert result["degraded"] == [
        {"source": "file", "reason": "Only the first 5 of 9 hits are listed."}
    ]


@pytest.mark.anyio
async def test_the_events_are_capped_at_ten_and_the_cap_is_asked_for_at_the_source(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The calendar caps itself; a truncated window is named instead of quietly shortened."""
    events = [event(f"Termin {index}", "2026-08-18T09:00:00+00:00") for index in range(12)]
    _search, calendar = wire(
        monkeypatch, calendar=FakeCall(calendar_answer(events, truncated=True))
    )

    result = await context_tools.prepare_context(clients, query="budget")

    assert calendar.kwargs["limit"] == context_tools.MAX_EVENTS == 10
    assert len(result["events"]) == 10
    assert {
        "source": "calendar",
        "reason": "Only the first 10 events of the window are listed.",
    } in result["degraded"]


@pytest.mark.anyio
async def test_an_unknown_detail_names_the_two_values_that_work(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wrong enum value is a caller error with a way out, never a silent fallback."""
    search, calendar = wire(monkeypatch)

    with pytest.raises(ToolError) as excinfo:
        await context_tools.prepare_context(clients, query="budget", detail="verbose")

    assert "short" in excinfo.value.hint, "the hint names the first value that works"
    assert "full" in excinfo.value.hint, "the hint names the second value that works"
    assert search.calls == [], "a bad parameter costs no search round trip"
    assert calendar.calls == [], "a bad parameter costs no calendar round trip"


@pytest.mark.anyio
async def test_an_empty_query_never_reaches_a_single_source(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty term would be a degraded search plus a meaningless calendar window."""
    search, calendar = wire(monkeypatch)

    with pytest.raises(ToolError) as excinfo:
        await context_tools.prepare_context(clients, query="   ")

    assert excinfo.value.hint
    assert search.calls == [], "the search is never asked for an empty term"
    assert calendar.calls == [], "and the window is never opened for one either"
