"""One bundle for one question: ``prepare_context`` (D-52 to D-57, TOOL-08).

This tool owns no data source. It composes the two fan-outs that already exist, and every
property that makes it trustworthy comes from that decision.

**Two ways, by the kind of question.** Content comes from the unified search, appointments
from the calendar with a computed window: "this week" is not a full text question, and a
bundle without the next appointments misses its purpose (D-52).

**The search is asked without a provider restriction.** Naming ``files,notes,deck`` here
would lock out an installed Findling and every future provider, and with it the one side
effect that carries D-53: the provider list is read at runtime, so a newly installed search
app is part of the bundle without a line of code here. Hits are grouped by their ``kind``
and never by the provider id, because the Deck provider is called
``search-deck-card-board`` and a grouping by name would silently never see a card.

**Each source has its own budget, the bundle has none.** A global ``asyncio.timeout``
around the ``gather`` would throw away the answer that was already finished, so every
source carries its own ceiling and a source that misses it becomes a named entry under
``degraded``. The wall clock of the whole call is therefore the maximum of the parts, not
their sum.

**A shortened answer says that it is shortened.** Buckets are capped for predictable
tokens (D-54), and every cap writes its own ``degraded`` entry: a list that is quietly five
entries long is the one outcome a model reports as "that is everything" (SC 4).

**Foreign text stays data (D-57).** A hit carries its origin as fields (``id``,
``provider``, ``kind``), never as prose, and an excerpt is a plain data field. Nothing in
this module frames a hit as an instruction or as a wish of the user. There is no content
filtering and no masking: masking is security theatre, the defence here is structure and
labelling.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from ..errors import ToolError
from ..nextcloud import NcClients
from . import calendar as calendar_tools
from . import chatgpt as chatgpt_tools
from . import marks
from . import search as search_tools

#: Hits requested from the search. Wider than any single bucket cap on purpose: the
#: grouping below can only distribute what it was given.
SEARCH_LIMIT = 25

#: "This week" without a schema field. The window is named in the answer, so the model
#: knows which days it is talking about (D-56: no budget parameter, no window parameter).
WINDOW_DAYS = 7

#: Own, tighter ceiling for the calendar leg. ``calendar.PER_CALENDAR_TIMEOUT`` is 20 s and
#: right for the standalone tool, but one stalling collection would fill the budget of the
#: whole bundle alone (pitfall 5). The cap belongs here; ``calendar.py`` stays untouched.
#:
#: Measured on the live topology on 2026-08-17 (plan 04-04, live proof 5, one MCP session
#: over client, proxy, HaRP, container and Nextcloud): ``detail="short"`` answered in
#: **0.84 s**, ``detail="full"`` with three excerpts in **0.99 s**, both with an empty
#: ``degraded`` list. That closes assumption A2 of 04-RESEARCH from the other side: the
#: healthy case is two orders of magnitude away from the thirty seconds a client grants, so
#: these budgets only ever bite when a source is actually stalling, which is what they are
#: for. Reproduce with the command in 04-04-MEASUREMENTS.md.
CALENDAR_BUDGET = 10.0

#: Token predictability over completeness (D-54): five hits per kind are enough for a model
#: to decide what to load, and the sixth costs every session that never needed it. Both caps
#: are named in ``degraded`` when they bite, so "five" is never mistaken for "all".
MAX_PER_BUCKET = 5
MAX_EVENTS = 10

#: The three kinds a read tool can resolve. Everything else is honest rest (pitfall 10).
KIND_BUCKETS = ("file", "note", "card")
OTHER_BUCKET = "other"
BUCKETS = (*KIND_BUCKETS, OTHER_BUCKET)

#: How much of a document reaches the answer in the full form. Three excerpts of two
#: kilobytes each are a paragraph of context per source, not a document dump: the model
#: decides from them whether it is worth calling ``fetch`` for the whole text (D-54).
MAX_EXCERPTS = 3
EXCERPT_MAX_BYTES = 2000

#: Own budget per excerpt, for the same reason the calendar has one: three reads that
#: cannot be finished must cost three sentences under ``degraded``, never the bundle.
EXCERPT_TIMEOUT = 5.0

#: Marked inside the text and not only beside it, exactly as ``chatgpt.fetch`` does it: a
#: model that only reads the excerpt must still be able to tell it from a whole document.
#: Defined in :mod:`mcp_connector.tools.marks` together with the filter that keeps the
#: sequence this server's own (BL-09, ME-03), and re-exported here under its own name.
EXCERPT_TRUNCATION = marks.EXCERPT_TRUNCATION

SHORT = "short"
FULL = "full"
DETAILS = (SHORT, FULL)

_DETAIL_HINT = f"Use detail={SHORT!r} for titles and ids, or detail={FULL!r} to add excerpts."

_QUERY_HINT = (
    "Give at least one word, for example 'budget'. Without a term the search has nothing "
    "to match and the window has nothing to be about."
)


async def prepare_context(clients: NcClients, query: str, detail: str = SHORT) -> dict[str, Any]:
    """Bundle the hits and the upcoming appointments for one question."""
    term = (query or "").strip()
    if not term:
        raise ToolError(message="The query is empty.", hint=_QUERY_HINT)

    mode = (detail or "").strip().lower() or SHORT
    if mode not in DETAILS:
        raise ToolError(message=f"{detail!r} is not a known detail level.", hint=_DETAIL_HINT)

    start, end = _window()
    search_out, calendar_out = await asyncio.gather(
        search_tools.unified_search(clients, query=term, limit=SEARCH_LIMIT),
        _events(clients, start, end),
        return_exceptions=True,
    )

    degraded: list[dict[str, str]] = []
    results = _bundle(_hits(search_out, degraded), degraded)
    events = _schedule(calendar_out, degraded)

    if isinstance(search_out, BaseException) and isinstance(calendar_out, BaseException):
        # Neither source answered. An empty bundle here would be read as "there is
        # nothing", which is the one statement this situation does not support.
        raise ToolError(
            message="Neither the search nor the calendar could be read.",
            hint="; ".join(item["reason"] for item in degraded),
        )

    if mode == FULL:
        await _excerpts(clients, results, degraded)

    result: dict[str, Any] = {
        "query": term,
        "window": {"start": start, "end": end},
        "events": events,
        "results": results,
    }
    if degraded:
        result["degraded"] = degraded
    result["note"] = search_tools.SEARCH_NOTE
    return result


def _window() -> tuple[str, str]:
    """Now until now plus a week, in UTC and in the form the calendar tool parses."""
    now = datetime.now(UTC).replace(microsecond=0)
    return now.isoformat(), (now + timedelta(days=WINDOW_DAYS)).isoformat()


async def _events(clients: NcClients, start: str, end: str) -> dict[str, Any]:
    """The calendar leg, under the ceiling of this tool instead of the one of that tool."""
    async with asyncio.timeout(CALENDAR_BUDGET):
        return await calendar_tools.list_events(clients, start=start, end=end, limit=MAX_EVENTS)


def _hits(
    outcome: dict[str, Any] | BaseException, degraded: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """The raw hits of the search leg, or nothing plus one sentence about why."""
    if isinstance(outcome, BaseException):
        degraded.append({"source": "search", "reason": _reason(outcome, "search", None)})
        return []

    # The search writes its own degraded entries and they arrive unchanged: one form for
    # one problem, and rewording them here would be a second answer to the same question.
    degraded.extend(_degraded_of(outcome))
    raw = outcome.get("results")
    return [hit for hit in raw if isinstance(hit, dict)] if isinstance(raw, list) else []


def _bundle(
    hits: list[dict[str, Any]], degraded: list[dict[str, str]]
) -> dict[str, list[dict[str, Any]]]:
    """Group by ``kind``, cap each group, and say out loud where the cap bit."""
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in BUCKETS}
    matched = dict.fromkeys(BUCKETS, 0)

    for hit in hits:
        kind = str(hit.get("kind") or "")
        bucket = kind if kind in KIND_BUCKETS else OTHER_BUCKET
        matched[bucket] += 1
        if len(grouped[bucket]) < MAX_PER_BUCKET:
            grouped[bucket].append(_short(hit, bucket))

    for name in BUCKETS:
        if matched[name] > MAX_PER_BUCKET:
            found = matched[name]
            degraded.append(
                {
                    "source": name,
                    "reason": f"Only the first {MAX_PER_BUCKET} of {found} hits are listed.",
                }
            )
    return grouped


def _short(hit: dict[str, Any], bucket: str) -> dict[str, Any]:
    """One hit as origin plus title: the four fields a follow up call needs (D-54, D-57)."""
    entry: dict[str, Any] = {
        "id": str(hit.get("id") or ""),
        "title": str(hit.get("title") or ""),
        "provider": str(hit.get("provider") or ""),
        "kind": str(hit.get("kind") or ""),
    }
    if bucket == OTHER_BUCKET or hit.get("resolvable") is False:
        # The honest half of pitfall 10: this id cannot be handed to a read tool as it is.
        entry["resolvable"] = False
    return entry


def _schedule(
    outcome: dict[str, Any] | BaseException, degraded: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """The events of the window, or nothing plus one sentence about why."""
    if isinstance(outcome, BaseException):
        degraded.append(
            {"source": "calendar", "reason": _reason(outcome, "calendar", CALENDAR_BUDGET)}
        )
        return []

    degraded.extend(_degraded_of(outcome))
    if outcome.get("truncated"):
        degraded.append(
            {
                "source": "calendar",
                "reason": f"Only the first {MAX_EVENTS} events of the window are listed.",
            }
        )
    raw = outcome.get("events")
    events = [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
    return events[:MAX_EVENTS]


async def _excerpts(
    clients: NcClients,
    results: dict[str, list[dict[str, Any]]],
    degraded: list[dict[str, str]],
) -> None:
    """Add a short excerpt to the first few resolvable hits, in place and in parallel.

    The order is the documented one: files first, then notes, then cards, and inside a kind
    the order the search returned. It is deliberately fixed rather than clever, because a
    ranking would be a second opinion about relevance next to the one Nextcloud already
    gave, and this tool has no more information than the search it just called.

    The content itself comes from ``chatgpt.fetch``: the id codec, the prefix discipline,
    the refusal to request a foreign url and the readers of the three kinds all live there
    and are tested there (threat T-01-75, T-01-77). A second routing here would be a second
    place to get exactly those decisions wrong. The excerpt is a data field and nothing
    else: no sentence of this module turns it into a request or an instruction (D-57).
    """
    targets = [
        hit for name in KIND_BUCKETS for hit in results[name] if hit.get("resolvable") is not False
    ][:MAX_EXCERPTS]

    outcomes = await asyncio.gather(
        *(_excerpt(clients, str(hit["id"])) for hit in targets), return_exceptions=True
    )
    for hit, outcome in zip(targets, outcomes, strict=True):
        if isinstance(outcome, BaseException):
            # The hit was found, and that stays true even when its content cannot be read.
            degraded.append(
                {
                    "source": str(hit["id"]),
                    "reason": _reason(outcome, "excerpt source", EXCERPT_TIMEOUT),
                }
            )
            continue
        hit["excerpt"] = outcome


async def _excerpt(clients: NcClients, identifier: str) -> str:
    """One excerpt, under its own ceiling, through the routing that already exists."""
    async with asyncio.timeout(EXCERPT_TIMEOUT):
        fetched = await chatgpt_tools.fetch(clients, identifier)
    return _capped(str(fetched.get("text") or ""))


def _capped(text: str) -> str:
    """Cut an excerpt to its byte ceiling and say inside the text that it was cut.

    Bytes and not characters, because the ceiling is about the payload and an umlaut is two
    bytes. ``errors="ignore"`` drops a character that the cut split in half, which is the
    right trade for a preview and would be the wrong one for a document.

    The document's own copy of either marker goes first (BL-09, ME-03). The marker stays in
    the text, which is what a model reading only the excerpt needs, but it can no longer
    come from the text: a shared file that writes the sequence itself would otherwise decide
    where the model believes the server excerpt ends, and that is the boundary D-57 rests
    on. Filtering happens before the measurement, so the ceiling applies to what is actually
    handed out.
    """
    body = marks.without_marks(text)
    encoded = body.encode("utf-8")
    if len(encoded) <= EXCERPT_MAX_BYTES:
        return body
    return f"{encoded[:EXCERPT_MAX_BYTES].decode('utf-8', errors='ignore')}\n\n{EXCERPT_TRUNCATION}"


def _degraded_of(answer: dict[str, Any]) -> list[dict[str, str]]:
    """The degraded entries of a composed answer, exactly as that tool wrote them (D-55)."""
    entries = answer.get("degraded")
    return (
        [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    )


def _reason(exc: BaseException, subject: str, budget: float | None) -> str:
    """One sentence per failed source: what happened, never who we are.

    The three cases are the ones from ``tools/search.py``, deliberately word for word.
    An unknown failure is a bug and stays loud instead of becoming a soothing sentence.
    """
    if isinstance(exc, ToolError):
        return exc.message
    if isinstance(exc, TimeoutError | httpx.TimeoutException):
        if budget is None:
            return f"The {subject} did not answer in time."
        return f"The {subject} did not answer within {budget:g} seconds."
    if isinstance(exc, httpx.RequestError):
        return f"The {subject} could not be reached."
    raise exc
