"""Which optional apps this Nextcloud has, in one round trip (SRV-04).

``GET /ocs/v2.php/cloud/capabilities`` reports Notes, Deck, Tables and Talk including their
API versions, for Deck whether the user may create boards at all, for Tables whether the app
is enabled and for Talk the chat length limit of the instance. That is one request instead of
a try-except around every tool call, and it is the difference between "the Notes app is not
installed on this Nextcloud" and a stack trace.

Only these four optional apps are checked here, on purpose. Calendars and contacts need
**no** app: CalDAV and CardDAV live in the core ``dav`` app, and the Calendar and Contacts
apps are only their web interfaces. The honest check there is "does a collection exist" and
it belongs to plans 07 and 08, not into this module.

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

__all__ = [
    "DEFAULT_CHAT_MAX_LENGTH",
    "TTL_SECONDS",
    "Capabilities",
    "app_missing",
    "clear_cache",
    "load",
    "require_app",
]

CAPABILITIES_PATH = "/cloud/capabilities"

#: Lifetime of a cache entry in seconds. Short enough that installing an app during a
#: session is noticed within a minute, long enough to save the round trip in a tool burst.
TTL_SECONDS = 60.0

_WHAT = "the Nextcloud capabilities"

#: Fallback for ``spreed.config.chat.max-length``. The number belongs to the instance and not
#: to us, so it is read from the capabilities and only defaulted here; the value matches
#: ``ChatManager::MAX_CHAT_LENGTH`` of Talk 24.
DEFAULT_CHAT_MAX_LENGTH = 32000

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
    "tables": (
        "The Tables app is not enabled on this Nextcloud.",
        (
            "Ask an administrator to enable the Tables app, or keep the list in a note "
            "created with notes_create."
        ),
    ),
    "spreed": (
        "The Talk app is not available on this Nextcloud.",
        "Ask an administrator to enable the Talk app for this account.",
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
    tables_available: bool = False
    tables_api_versions: tuple[str, ...] = ()
    spreed_available: bool = False
    spreed_features: tuple[str, ...] = ()
    spreed_chat_max_length: int = DEFAULT_CHAT_MAX_LENGTH

    def has(self, app: str) -> bool:
        """Whether ``app`` is installed. Unknown names are a programming error."""
        flags = {
            "notes": self.notes_available,
            "deck": self.deck_available,
            "tables": self.tables_available,
            # ``spreed`` and not ``talk``: the capabilities document names the section that
            # way, and the key of this mapping is the key of the answer.
            "spreed": self.spreed_available,
        }
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
    tables = section.get("tables")
    tables = tables if isinstance(tables, dict) else None
    # Talk behaves like Notes and Deck (presence of the section, no ``enabled`` field), with
    # one addition: an instance where Talk is switched off for this user answers an empty
    # array, so the section is only taken as proof when it carries something.
    spreed = section.get("spreed")
    spreed = spreed if isinstance(spreed, dict) and spreed else None

    return Capabilities(
        notes_available=notes is not None,
        notes_api_versions=_versions(notes, "api_version"),
        deck_available=deck is not None,
        deck_api_versions=_versions(deck, "apiVersions"),
        can_create_boards=bool(deck.get("canCreateBoards")) if deck else False,
        # The one place that differs from Notes and Deck: Tables publishes an explicit
        # ``enabled``, and an app that is installed but switched off is absent as far as this
        # server is concerned, so the flag is read from the field and not from the presence
        # of the section. No gate on ``version``: the API generations are what matter here.
        tables_available=bool(tables.get("enabled")) if tables else False,
        tables_api_versions=_versions(tables, "apiVersions"),
        spreed_available=spreed is not None,
        # No gate on a version number: ``features`` is what the app says about itself, and
        # it is the honest place to look up whether a parameter exists at all.
        spreed_features=_versions(spreed, "features"),
        spreed_chat_max_length=_chat_max_length(spreed),
    )


def _chat_max_length(section: dict[str, Any] | None) -> int:
    """Read ``config.chat.max-length``, falling back to the number Talk 24 ships with.

    The limit belongs to the instance, so reading it here keeps it from being maintained a
    second time in the tool layer. An unreadable or non-positive value is the fallback rather
    than an error: a wrong cap is a worse answer than a slightly generous one, and Talk
    refuses an over-long message itself.
    """
    if not section:
        return DEFAULT_CHAT_MAX_LENGTH
    config_section = section.get("config")
    config_section = config_section if isinstance(config_section, dict) else {}
    chat = config_section.get("chat")
    chat = chat if isinstance(chat, dict) else {}
    raw = chat.get("max-length")
    if isinstance(raw, bool) or not isinstance(raw, int | str):
        return DEFAULT_CHAT_MAX_LENGTH
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_CHAT_MAX_LENGTH
    return value if value > 0 else DEFAULT_CHAT_MAX_LENGTH


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
