"""The throttle of our own authorization paths, and the measure it really answers to.

**What is being protected, and it is not this process.** The finding of the phase research
that decides this module comes out of the HaRP source: HaRP asks Nextcloud who the caller
is for *every* request that carries an ``Authorization`` header, on public routes as well,
and it caches that answer for cookie sessions only (pitfall 5). Every such request is a
full Nextcloud PHP round trip that this application cannot switch off. The good half of the
same finding is that an unknown bearer produces no brute force entry in Nextcloud
(``Session::tryTokenLogin`` returns false without registering an attempt) and no HaRP
blacklist entry either, which means Nextcloud will not defend itself here. So the ceiling
is ours to set, and success criterion 5 is measured in Nextcloud round trips rather than in
our own response times.

**What is throttled and what is not.** The authorization paths of this application:
``/token``, ``/register``, ``/revoke``, ``/authorize`` with the consent screen behind it,
and the browser onboarding of AUTH-02, which is the one route on which an anonymous caller
can make this server start a Nextcloud login flow. The MCP route is deliberately not among
them: a tool call arrives with a verified bearer, is answered from the process cache of the
verifier, and rate limiting the actual work of this server would be a denial of service
with our own name on it (D-37).

**What is counted and what is stored.** Failed attempts only, per path class and per
source, in a fixed window. A successful answer clears the counter of its source, so an
ordinary user who mistypes something four times and then succeeds starts from zero again.
Nothing of a request is kept: the counter is keyed by the SHA-256 digest of the path class
and the source together, so the dictionary of this object contains digests, integers and
deadlines and nothing that could identify anybody (T-03-65).

**Why there are two limits.** The per source limit is the useful one and the forgeable one:
behind HaRP the peer address of every request is the proxy, so the source has to be taken
from ``X-Forwarded-For`` when it is there, and anybody who can send a request can write
that header. Splitting the counter that way is exactly what an attacker would do, which is
why the second limit exists: a ceiling per path class that no header can escape. Without it
a forged header would buy an unbounded number of Nextcloud round trips; without the first
limit a single flood behind one proxy would lock out every legitimate user of the instance.

The state is process local, has a hard ceiling on how many counters it keeps, and losing it
is harmless: a restart forgets who was attempting what, which costs one window of counting
and nothing else. Two workers count separately, which makes the effective limit twice the
number below, and that is a deliberate simplification: a shared counter would need a shared
store in the hot path of every authorization request, which is precisely what D-37 keeps
out of it.
"""

import hashlib
import logging
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..exapp.responses import json_response
from ..exapp.ui import errors

__all__ = [
    "CLASS_AUTHORIZE",
    "CLASS_CONNECT",
    "CLASS_REGISTER",
    "CLASS_REVOKE",
    "CLASS_TOKEN",
    "FAILURE_LIMIT",
    "PATH_CEILING",
    "SOURCE_LIMIT",
    "WINDOW",
    "Throttle",
    "Throttled",
    "source_of",
]

#: The five path classes of this application. Separate counters, because a person fighting
#: with the consent screen must not close the endpoint a working connector refreshes at.
CLASS_TOKEN = "token"  # noqa: S105 - the name of a path class, not a credential
CLASS_REGISTER = "register"
CLASS_REVOKE = "revoke"
CLASS_AUTHORIZE = "authorize"
CLASS_CONNECT = "connect"

#: How many failed attempts one source may make per path class before it has to wait. Ten
#: is generous for every legitimate shape of failure (a mistyped link, a stale tab, a
#: client that retries a rejected grant twice) and short work of a guessing loop.
FAILURE_LIMIT = 10

#: The ceiling of a whole path class, whatever a caller writes into a forwarded header.
#: Two hundred failures in five minutes is far above anything an instance produces by
#: accident and far below a load that a Nextcloud would feel.
PATH_CEILING = 200

#: The window both limits are counted in. Five minutes, the same order of magnitude as the
#: Nextcloud brute force window, so a caller that ran into this one is not surprised twice.
WINDOW = 300

#: How many counters this object keeps at once. Reached only by a caller that varies its
#: source, which is exactly the case the ceiling above already covers, so the reaction is
#: to drop what has run out and then, if that was not enough, to start over (T-03-65).
SOURCE_LIMIT = 4096

#: The counter of a whole path class, the one no request can influence. Not a source and
#: not a valid header value, so no caller can land in it by accident.
_WHOLE_CLASS = "\x00all"

#: What a throttled machine endpoint answers. ``temporarily_unavailable`` is the OAuth
#: error code for "this is not about your request, come back later"; a code that named the
#: throttle would tell a caller which of our defences they reached.
_ERROR = "temporarily_unavailable"

logger = logging.getLogger("mcp_connector.oauth.throttle")


@dataclass(slots=True)
class _Counter:
    """One window: how many failures were seen in it, and when it ends."""

    seen: int
    until: float


class Throttle:
    """The counters of one process, asked before the work and told after it.

    Built once per application and shared by every authorization route, so the five path
    classes are five counters and not five objects with five ceilings.
    """

    def __init__(
        self,
        *,
        limit: int = FAILURE_LIMIT,
        ceiling: int = PATH_CEILING,
        window: int = WINDOW,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._limit = limit
        self._ceiling = ceiling
        self._window = window
        #: Monotonic: a window must not grow or shrink because somebody corrected the
        #: system clock, and nothing here is ever compared against a stored row.
        self._clock = clock if clock is not None else time.monotonic
        self._counters: dict[str, _Counter] = {}

    def __repr__(self) -> str:
        return (
            f"Throttle(limit={self._limit!r}, ceiling={self._ceiling!r}, window={self._window!r})"
        )

    def retry_after(self, path_class: str, source: str) -> int:
        """Seconds this caller has to wait, or ``0`` when it may go ahead.

        Never zero when a limit is reached: a page that promises an immediate retry invites
        exactly the request the throttle exists against, which is why the answer is rounded
        up and floored at one second.
        """
        now = self._clock()
        pairs = (
            (self._key(path_class, source), self._limit),
            (self._whole(path_class), self._ceiling),
        )
        for key, limit in pairs:
            counter = self._counters.get(key)
            if counter is None or counter.until <= now:
                continue
            if counter.seen >= limit:
                return max(1, math.ceil(counter.until - now))
        return 0

    def record_failure(self, path_class: str, source: str) -> None:
        """Count one refused attempt, for this source and for the path class as a whole."""
        now = self._clock()
        self._sweep(now)
        for key in (self._key(path_class, source), self._whole(path_class)):
            counter = self._counters.get(key)
            if counter is None or counter.until <= now:
                self._counters[key] = _Counter(seen=1, until=now + self._window)
            else:
                counter.seen += 1

    def forget(self, path_class: str, source: str) -> None:
        """Clear the counter of one source, because it just succeeded.

        The ceiling of the path class is deliberately not cleared: one success among a
        thousand failures is what a guessing loop looks like from the inside, and letting
        it reset the ceiling would hand an attacker the switch that turns the ceiling off.
        """
        self._counters.pop(self._key(path_class, source), None)

    def _key(self, path_class: str, source: str) -> str:
        """The digest one counter lives under. Never the source, never the path.

        SHA-256 of the two values with a separator between them: the separator is what
        keeps a source that ends in the name of a path class from colliding with another
        one, and the digest is what keeps this dictionary from being a record of who tried
        what (T-03-65).
        """
        return hashlib.sha256(f"{path_class}\x00{source}".encode()).hexdigest()

    def _whole(self, path_class: str) -> str:
        return self._key(path_class, _WHOLE_CLASS)

    def _sweep(self, now: float) -> None:
        """Keep the number of counters under the ceiling, in the simplest way that holds."""
        if len(self._counters) < SOURCE_LIMIT:
            return
        for key in [key for key, counter in self._counters.items() if counter.until <= now]:
            del self._counters[key]
        if len(self._counters) >= SOURCE_LIMIT:
            # Everything in here is younger than one window and nothing in it is worth more
            # than that window, so starting over is both correct and the rule that cannot
            # leak. It costs an ongoing flood one window of counting, and it is logged.
            logger.warning("the throttle reached its ceiling of counters and starts over")
            self._counters.clear()


class Throttled:
    """One route, with the counter asked before it and told after it.

    An ASGI wrapper and not a decorator on the handlers, for the reason
    :class:`~mcp_connector.oauth.provider.NoStore` is one: the endpoints of the
    authorization server belong to the SDK, and wrapping them leaves their bodies, their
    error shapes and their CORS handling exactly as they are.

    What counts as a failure is the status of the answer: anything from 400 upwards. That
    covers every refusal of every endpoint behind this wrapper without this module having
    to know a single one of them, and it counts nothing that worked, including the
    redirects of the authorization endpoint and the pages of the consent screen.
    """

    def __init__(
        self,
        app: ASGIApp,
        throttle: Throttle,
        path_class: str,
        *,
        machine: bool,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._app = app
        self._throttle = throttle
        self._path_class = path_class
        self._machine = machine
        self._env = env

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover - these routes are HTTP only
            await self._app(scope, receive, send)
            return

        source = source_of(Request(scope))
        wait = self._throttle.retry_after(self._path_class, source)
        if wait:
            await self._refuse(wait)(scope, receive, send)
            return

        status = 0

        async def watch(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        await self._app(scope, receive, watch)
        if status >= 400:
            self._throttle.record_failure(self._path_class, source)
        else:
            self._throttle.forget(self._path_class, source)

    def _refuse(self, wait: int) -> Response:
        """The 429, in the shape the caller of this path can read.

        The same number in the header and in the body, because the two are read by two
        different readers: an assistant app backs off on ``Retry-After``, and a person
        reads the sentence on the page. A page that said something else than its own header
        would make one of the two wrong.
        """
        if self._machine:
            return json_response(
                {
                    "error": _ERROR,
                    "error_description": f"too many failed attempts, retry in {wait} seconds",
                },
                status_code=429,
                headers={"Retry-After": str(wait)},
            )
        page, _reference = errors.error_page("E6", env=self._env, seconds=wait)
        return page


def source_of(request: Request) -> str:
    """Who is asking, as well as this topology can tell.

    Behind HaRP the peer of every request is the proxy, so the forwarded address is the
    only value that tells two callers apart at all. It is forgeable, and this function does
    not pretend otherwise: it is used to *split* a counter, never to authenticate anything,
    and the ceiling of the path class is what holds when somebody forges it. The first
    entry of the header is taken, because that is the original client in the convention of
    RFC 7239 and because a longer chain is the proxies, not the caller.
    """
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    peer = request.client.host if request.client else ""
    return forwarded or peer or ""
