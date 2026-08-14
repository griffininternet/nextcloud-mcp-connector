"""The ChatGPT compatibility profile: ``search`` and ``fetch`` (D-09, TOOL-07).

Two functions, and both of them are deliberately thin.

**``search`` owns no search.** It calls :func:`mcp_connector.tools.search.unified_search`
and renames its fields. A second hit source here would mean two answers to the same
question, two id schemes and two places to fix pitfall 10, so the only logic in it is the
projection onto the four names OpenAI reads.

**Every hit keeps a link.** ChatGPT renders a citation only while ``url`` is a non-empty
string, so an empty one does not degrade a hit, it removes it from the answer the user
sees. The unified search already guarantees an absolute URL on the configured instance;
the fallbacks below exist so a future provider cannot quietly take the citations away.
"""

from typing import Any

from ..nextcloud import NcClients
from . import search as search_tools

DEFAULT_LIMIT = search_tools.DEFAULT_LIMIT


async def search(
    clients: NcClients,
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, str]]:
    """Search the whole Nextcloud and project the hits onto the OpenAI field names.

    An empty query is refused by the unified search itself, with the hint that explains
    what a usable term looks like. Catching it here as well would only duplicate a message
    that is already right.
    """
    answer = await search_tools.unified_search(clients, query=query, limit=limit)
    return [_as_hit(clients, hit) for hit in _entries(answer)]


def _entries(answer: dict[str, Any]) -> list[dict[str, Any]]:
    results = answer.get("results")
    return [hit for hit in results if isinstance(hit, dict)] if isinstance(results, list) else []


def _as_hit(clients: NcClients, hit: dict[str, Any]) -> dict[str, str]:
    """One unified search hit as the four fields of the OpenAI contract.

    The two fallbacks are not cosmetic. A hit without a title is unreadable in a citation
    list, and the id at least names the resource; a hit without a url is not cited at all,
    and the instance root is still a page the user can open.
    """
    identifier = str(hit.get("id") or "")
    return {
        "id": identifier,
        "title": str(hit.get("title") or "") or identifier,
        "url": str(hit.get("url") or "") or clients.creds.base_url,
        "text": str(hit.get("subline") or ""),
    }
