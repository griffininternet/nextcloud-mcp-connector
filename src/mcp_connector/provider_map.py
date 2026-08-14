"""Unified search entries to prefixed ids: the table and the parsing behind pitfall 10.

A unified search entry has **no** ``id`` field. ``CoreUnifiedSearchResultEntry`` carries
``title``, ``subline``, ``resourceUrl``, ``icon``, ``rounded`` and ``attributes``, and only
the files provider fills ``attributes`` with ``fileId`` and ``path``. The notes provider
ships the note id exclusively inside ``resourceUrl``, and the Deck provider is not called
``deck`` but ``search-deck-card-board`` and delivers only the ``cardId``, never board and
stack. Everything in this module follows from those four facts.

Two rules make the ids trustworthy instead of merely present:

**Never guess a kind.** A provider that is not in :data:`PROVIDER_KINDS` produces an id of
kind ``url``, and ``fetch`` answers that honestly with "open the url" instead of resolving
a Talk message as a note (threat T-01-69). The same applies inside a known provider: a
notes entry whose URL has no numeric last segment also becomes a ``url``, because a wrong
note id silently reads a different note.

**Never keep a foreign origin.** ``resourceUrl`` comes from an arbitrary installed app and
is only ever parsed, never fetched. Every URL this module returns is rebuilt from the
configured base URL, so a manipulated entry cannot point the user (or ChatGPT's citation
renderer) at another host (threat T-01-68).

The calendar provider is deliberately **not** in the table. Its entry URL addresses a day
view, not the DAV object name that ``event:<calendarUri>:<objectName>`` needs, so it would
be an id that no ``fetch`` can resolve. It stays in the ``url`` category until a real
instance shows a resolvable form.
"""

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from . import ids

#: Provider id as Nextcloud reports it at runtime, mapped to our resource kind. This is a
#: translation table, never a list of installed providers: that list is fetched per call.
PROVIDER_KINDS: Mapping[str, str] = {
    "files": "file",
    "notes": "note",
    # Verified against nextcloud/deck lib/Search/DeckProvider.php. "deck" is wrong.
    "search-deck-card-board": "card",
}

#: The honest rest category for everything the table does not cover.
UNKNOWN_KIND = "url"

#: Web route of a single file, used when an entry carries a fileId but no resourceUrl.
FILE_WEB_PREFIX = "/index.php/f"


def absolute_url(base_url: str, resource_url: Any) -> str:
    """Rebuild ``resource_url`` on the configured instance, or return an empty string.

    Path, query and fragment survive, the origin never does: ``#message_42`` matters for a
    Talk link, and ``http://evil.test`` must not reach the model.
    """
    if not isinstance(resource_url, str) or not resource_url.strip():
        return ""
    parts = urlsplit(resource_url.strip())
    path = parts.path
    if not path.startswith("/"):
        path = f"/{path}" if path else "/"
    return f"{base_url}{urlunsplit(('', '', path, parts.query, parts.fragment))}"


def extract_id(
    provider_id: str, entry: Mapping[str, Any], base_url: str
) -> tuple[str, str, bool] | None:
    """Return ``(kind, id, canonical)`` for one search entry, or ``None`` if it is unusable.

    ``canonical`` is false when the id cannot be handed to a read tool as it stands: the
    short card form needs a board sweep first, and a ``url`` id cannot be resolved at all.
    An entry without a usable ``resourceUrl`` and without a usable ``fileId`` carries
    nothing to build an id from and is skipped by the caller.
    """
    attributes = entry.get("attributes")
    # The psalm annotation in the server code says list<string>; the wire format is an
    # object, and an app that sets nothing sends an empty list. Both are normal.
    attributes = attributes if isinstance(attributes, dict) else {}
    url = absolute_url(base_url, entry.get("resourceUrl"))
    kind = PROVIDER_KINDS.get(provider_id, UNKNOWN_KIND)

    if kind == "file":
        file_id = _file_id(attributes, url)
        if file_id:
            return "file", ids.encode_file(file_id), True
    elif kind == "note":
        note_id = _last_numeric_segment(url)
        if note_id:
            return "note", ids.encode_note(note_id), True
    elif kind == "card":
        card_id = _last_numeric_segment(url)
        if card_id:
            # Short form on purpose: the provider knows no board and no stack, and an
            # invented one would address a card that does not exist.
            return "card", f"card{ids.SEPARATOR}{card_id}", False

    if not url:
        return None
    return UNKNOWN_KIND, ids.encode_url(url), False


def hit_url(base_url: str, kind: str, identifier: str, entry: Mapping[str, Any]) -> str:
    """The link a human can open: absolute, non-empty and always on this instance.

    OpenAI only renders a citation when ``url`` is a non-empty string, so a files hit
    without a ``resourceUrl`` still gets the canonical ``/f/<fileid>`` route.
    """
    url = absolute_url(base_url, entry.get("resourceUrl"))
    if url:
        return url
    if kind == "file":
        _, parts = ids.parse(identifier)
        return f"{base_url}{FILE_WEB_PREFIX}/{parts[0]}"
    # A url id carries its own absolute link, and no other kind reaches this line without
    # a resourceUrl, because extract_id would have skipped the entry.
    return identifier.partition(ids.SEPARATOR)[2] or base_url


def _file_id(attributes: Mapping[str, Any], url: str) -> str:
    """``attributes.fileId`` first, then the ``/f/<fileid>`` segment of the URL."""
    raw = attributes.get("fileId")
    candidate = str(raw).strip() if raw is not None else ""
    if candidate.isdigit():
        return candidate

    segments = [segment for segment in urlsplit(url).path.split("/") if segment]
    for index, segment in enumerate(segments[:-1]):
        if segment == "f" and segments[index + 1].isdigit():
            return segments[index + 1]
    return ""


def _last_numeric_segment(url: str) -> str:
    """Return the trailing numeric path segment of ``url``, or an empty string."""
    path = urlsplit(url).path.rstrip("/")
    if not path:
        return ""
    candidate = path.rsplit("/", 1)[-1]
    return candidate if candidate.isdigit() else ""
