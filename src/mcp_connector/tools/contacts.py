"""Contacts tool: searching the user's own address books over CardDAV (D-07, TOOL-05).

Three properties of this tool are contract, not implementation detail.

**It only reads.** There is no create, no update and no delete path for contacts in this
phase, neither here nor in the client below it (threat T-01-57). A contact is other
people's data, and the first write we add will be the one that needs a real confirmation
story.

**All address books are asked at once.** A person can live in the private book, in a
shared team book or in both. Each request has its own timeout, and a book that fails is
listed under ``degraded`` instead of quietly shrinking the result (threat T-01-58).

**An account without an address book is not an empty result.** The client turns that case
into an error with a way out, and this tool lets it through unchanged: a user created with
``occ user:add`` has no address book at all, and "no book" answered as "no contacts" is
the kind of lie a model repeats with confidence (pitfall 3).

Deliberately absent: a capabilities check. CardDAV is part of the core ``dav`` app and the
Contacts app is only its web interface, so requiring the app would refuse to work on
instances where the tool works perfectly well. The honest precondition is "does a
collection exist", and the discovery answers exactly that.

Also deliberately absent: the raw vCard. The answer carries ``full_name``, ``emails``,
``phones``, ``organization``, ``addressbook`` and ``uid``, and empty fields are left out
entirely, because every key is paid for in every hit of every answer.
"""

import asyncio
from typing import Any

import httpx

from ..errors import ToolError
from ..nextcloud import NcClients
from ..nextcloud.clients import carddav

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

#: Wall clock budget for one address book. A single slow collection must not hold the
#: answer hostage; it becomes a named degradation instead.
PER_ADDRESSBOOK_TIMEOUT = 20.0

#: Fields that are only reported when they carry something.
_OPTIONAL = ("emails", "phones", "organization", "uid")

_TERM_HINT = "Give at least one word, for example a last name or a part of a mail address."


async def search(clients: NcClients, query: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """Search every address book of the user by name and mail address."""
    term = (query or "").strip()
    if not term:
        raise ToolError(message="The search term is empty.", hint=_TERM_HINT)

    # A limit outside the range is capped instead of refused: the model asked a legitimate
    # question with an unhelpful number, and an error would only cost a second round trip.
    capped = min(max(limit, 1), MAX_LIMIT)

    books = await carddav.discover_addressbooks(clients.client, clients.creds)

    results = await asyncio.gather(
        *(_query_one(clients, book, term, capped) for book in books),
        return_exceptions=True,
    )

    contacts: list[dict[str, Any]] = []
    degraded: list[dict[str, str]] = []
    for book, outcome in zip(books, results, strict=True):
        if isinstance(outcome, BaseException):
            degraded.append({"addressbook": book.display_name, "reason": _reason(outcome)})
            continue
        contacts.extend(outcome)

    if degraded and not contacts and len(degraded) == len(books):
        # Every book failed. Reporting an empty result here would be the worst of both
        # worlds: no data and no error the caller could act on.
        raise ToolError(
            message="None of the address books could be read.",
            hint="; ".join(item["reason"] for item in degraded),
        )

    contacts.sort(key=_sort_key)
    truncated = len(contacts) > capped
    contacts = contacts[:capped]

    result: dict[str, Any] = {
        "query": term,
        "count": len(contacts),
        "contacts": [_as_output(contact) for contact in contacts],
    }
    if truncated:
        result["truncated"] = True
    if degraded:
        result["degraded"] = degraded
    return result


async def _query_one(
    clients: NcClients,
    book: carddav.AddressBookRef,
    term: str,
    limit: int,
) -> list[dict[str, Any]]:
    async with asyncio.timeout(PER_ADDRESSBOOK_TIMEOUT):
        return await carddav.query_contacts(
            clients.client,
            clients.creds,
            book.uri,
            term,
            limit,
            addressbook=book.display_name,
        )


def _reason(exc: BaseException) -> str:
    """One sentence per failed address book. Unknown failures are bugs and stay loud."""
    if isinstance(exc, ToolError):
        return exc.message
    if isinstance(exc, TimeoutError | httpx.TimeoutException):
        return f"The address book did not answer within {PER_ADDRESSBOOK_TIMEOUT:.0f} seconds."
    if isinstance(exc, httpx.RequestError):
        return "The address book could not be reached."
    raise exc


def _sort_key(contact: dict[str, Any]) -> tuple[str, str]:
    return (contact.get("full_name", "").casefold(), contact.get("addressbook", ""))


def _as_output(contact: dict[str, Any]) -> dict[str, Any]:
    """Project one contact onto the stable answer shape, without the empty fields."""
    result: dict[str, Any] = {
        "full_name": contact.get("full_name", ""),
        "addressbook": contact.get("addressbook", ""),
    }
    for field in _OPTIONAL:
        value = contact.get(field)
        if value:
            result[field] = value
    return result
