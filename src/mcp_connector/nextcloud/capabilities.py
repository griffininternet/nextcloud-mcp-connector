"""Which optional apps this Nextcloud has, in one round trip (SRV-04).

``GET /ocs/v2.php/cloud/capabilities`` reports Notes and Deck including their API versions
and, for Deck, whether the user may create boards at all. That is one request instead of a
try-except around every tool call, and it is the difference between "the Notes app is not
installed on this Nextcloud" and a stack trace.

Only Notes and Deck are checked here, on purpose. Calendars and contacts need **no** app:
CalDAV and CardDAV live in the core ``dav`` app, and the Calendar and Contacts apps are
only their web interfaces. The honest check there is "does a collection exist" and it
belongs to plans 07 and 08, not into this module.

The cache is a pure latency optimisation and may be empty at any moment (D-20). Nothing in
this project becomes incorrect when it is cold, and it holds no session state: the key is
base URL plus user name, the value is a snapshot of public app metadata, and no credential
ever enters it. ``tools/list`` stays static regardless of what this module reports, because
a credential dependent tool list would break caching, the token budget gate and every
client that persists tool lists.
"""

import time
from dataclasses import dataclass
from typing import Any

from ..errors import AppMissingError
from . import NcClients
from .clients import ocs

__all__ = ["TTL_SECONDS", "Capabilities", "app_missing", "clear_cache", "load", "require_app"]

CAPABILITIES_PATH = "/cloud/capabilities"

#: Lifetime of a cache entry in seconds. Short enough that installing an app during a
#: session is noticed within a minute, long enough to save the round trip in a tool burst.
TTL_SECONDS = 60.0

_WHAT = "the Nextcloud capabilities"

#: message plus hint per optional app (D-15). The wording is part of the contract: it is
#: what the user reads, so it names the app and one thing to do instead.
_MISSING: dict[str, tuple[str, str]] = {
    "notes": (
        "The Notes app is not installed on this Nextcloud.",
        (
            "Ask an administrator to install the Notes app, or use files_search for note files "
            "under /Notes."
        ),
    ),
    "deck": (
        "The Deck app is not installed on this Nextcloud.",
        (
            "Ask an administrator to install the Deck app, or keep the task list in a note "
            "created with notes_create."
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class Capabilities:
    """The optional-app snapshot of one Nextcloud, as far as this project cares."""

    notes_available: bool = False
    notes_api_versions: tuple[str, ...] = ()
    deck_available: bool = False
    deck_api_versions: tuple[str, ...] = ()
    can_create_boards: bool = False

    def has(self, app: str) -> bool:
        """Whether ``app`` is installed. Unknown names are a programming error."""
        flags = {"notes": self.notes_available, "deck": self.deck_available}
        try:
            return flags[app]
        except KeyError:
            raise ValueError(f"{app!r} is not an optional app this server checks") from None


#: (base_url, user) -> (stored_at, capabilities). No secrets, no session state.
_cache: dict[tuple[str, str], tuple[float, Capabilities]] = {}


async def load(clients: NcClients) -> Capabilities:
    """Return the capabilities of this credential context, cached for ``TTL_SECONDS``."""
    key = (clients.creds.base_url, clients.creds.user)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached is not None and now - cached[0] < TTL_SECONDS:
        return cached[1]

    response = await ocs.ocs_get(clients.client, clients.creds, CAPABILITIES_PATH)
    result = parse(ocs.parse_ocs(response, what=_WHAT))
    _cache[key] = (now, result)
    return result


def clear_cache() -> None:
    """Drop every entry. Safe at any time, by construction (D-20)."""
    _cache.clear()


async def require_app(clients: NcClients, app: str) -> Capabilities:
    """Return the capabilities, or raise :class:`AppMissingError` if ``app`` is absent.

    Called first by every tool of an optional app, which is what keeps a missing app from
    producing a request that could only fail with an HTML page or a 404.
    """
    result = await load(clients)
    if not result.has(app):
        raise app_missing(app)
    return result


def app_missing(app: str) -> AppMissingError:
    """Build the error for a missing app: one sentence plus one thing the user can do."""
    message, hint = _MISSING[app]
    return AppMissingError(message=message, hint=hint)


def parse(data: Any) -> Capabilities:
    """Read the capabilities payload defensively; a missing key is a ``False``, not a crash."""
    section = data.get("capabilities") if isinstance(data, dict) else None
    section = section if isinstance(section, dict) else {}

    notes = section.get("notes")
    notes = notes if isinstance(notes, dict) else None
    deck = section.get("deck")
    deck = deck if isinstance(deck, dict) else None

    return Capabilities(
        notes_available=notes is not None,
        notes_api_versions=_versions(notes, "api_version"),
        deck_available=deck is not None,
        deck_api_versions=_versions(deck, "apiVersions"),
        can_create_boards=bool(deck.get("canCreateBoards")) if deck else False,
    )


def _versions(section: dict[str, Any] | None, key: str) -> tuple[str, ...]:
    """Accept a list, tolerate a single string, ignore anything else."""
    if not section:
        return ()
    raw = section.get(key)
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list):
        return tuple(str(item) for item in raw if isinstance(item, str | int | float))
    return ()
