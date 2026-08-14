"""The answer models of the ChatGPT profile, and the only output schemas this server ships.

Thirteen tools return a compact JSON string with ``structured_output=False`` and therefore
no output schema at all (schema diet, D-14). ``search`` and ``fetch`` are the documented
exception: OpenAI reads the payload twice, once as ``structuredContent`` and once as JSON
text inside ``content``, and mcp 2.x produces exactly that pair when a tool returns a
Pydantic model. Turning the structured output off for these two would cost the citations.

Every field is annotated on the class body, and that is load bearing rather than style. A
class **without** annotations silently yields ``output_schema=None`` and ships ``repr()``
as its text: no error, no warning, an unusable tool. It is the documented trap of the SDK
and the reason this module exists as a separate file instead of a few inline dicts.

Field names are a contract with OpenAI, not a matter of taste: ``search`` answers with
``results`` of ``id``/``title``/``url``/``text``, ``fetch`` with
``id``/``title``/``text``/``url``/``metadata``. Renaming one of them does not degrade the
answer, it removes it from ChatGPT.
"""

from pydantic import BaseModel

__all__ = ["FetchResult", "SearchHit", "SearchResults"]


class SearchHit(BaseModel):
    """One search result. ``url`` is never empty: ChatGPT cites nothing without it."""

    id: str
    title: str
    url: str
    text: str = ""


class SearchResults(BaseModel):
    """The envelope OpenAI expects: one key, one list, no metadata around it."""

    results: list[SearchHit]


class FetchResult(BaseModel):
    """The full content of one hit, plus the little that is worth knowing about it."""

    id: str
    title: str
    text: str
    url: str
    metadata: dict[str, str] | None = None
