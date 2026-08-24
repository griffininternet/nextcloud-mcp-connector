"""HTML to text for a model context, because a mail body is always HTML.

Even a plain text mail arrives as HTML: the Mail app runs the body through ``convertLinks``,
and that is ``htmlspecialchars`` plus HTMLPurifier (correction K2 of the phase research). A
reader that trusted ``hasHtmlBody`` would hand ``Gr&uuml;&szlig;e`` and ``<a href=...>`` to a
model for every text mail it ever sees. This module turns that into text a model can read.

**What it costs and where the actual decision is.** ``lxml`` buys the hard half: a forgiving
HTML parser for the broken markup of real mail in whatever character set it arrived in. The
paragraph policy is the own half, and it is different in every library that offers one and
right in none of them, because it is a decision about foreign prose and not about markup.
That is why there is no new dependency here: ``lxml`` has been in ``pyproject.toml`` since
phase 1 for the DAV bodies, and writing the paragraph policy is not duplicated work.

**What this is not.** It is not a sanitizer and not a renderer. It produces text for a model
and never anything that goes into a browser, so nothing here escapes, rewrites or repairs
markup for display. ``lxml_html_clean`` (the successor of ``lxml.html.clean`` since lxml 5)
is not needed and is deliberately not installed, so that nobody reaches for it here.

**The honest limit.** The paragraph policy is an approximation. A table becomes lines, a
layout built from nested tables becomes flat while it does so, and a mail that carries its
structure in styles alone loses that structure entirely. No rule over free text can get that
right for every mail, and the alternative, guessing harder, would be a second opinion about
foreign content that this package deliberately does not have.

Every requirement below was measured against this working tree with lxml 6.1.1 (see
``10-RESEARCH.md``, section "HTML zu Text"); the comments name the measurement, because they
are numbers from a run and not preferences.
"""

import re
from typing import cast

from lxml import etree
from lxml.html import HtmlMixin, HTMLParser, document_fromstring

#: Removed with their whole subtree before any text is taken. HTMLPurifier in the Mail app
#: already drops scripts and lifts style blocks out, but this function must not rely on that:
#: it is handed foreign text, and the defence belongs where the text is processed (T-10-17).
#: ``noscript`` and ``template`` ride along, because they cost nothing here and their content
#: is markup for a browser that never runs, so it is not part of what the sender wrote.
_DROPPED_TAGS = ("script", "style", "noscript", "template")

#: Where a line ends. Measured without this step, ``text_content()`` alone turned
#: ``<p>Hallo &amp; tschüss</p><div>Zeile2<br>Zeile3</div>`` into the single word chain
#: ``Hallo & tschüssZeile2Zeile3``, which is what a model would have had to read.
_BLOCK_TAGS = frozenset(
    {
        "p",
        "div",
        "li",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "table",
    }
)

#: The one break that has no content of its own, so it gets a newline after it and not around
#: it: two newlines for a single ``<br>`` would turn every soft wrap into a paragraph.
_VOID_BLOCK_TAG = "br"

#: More than one empty line says nothing a reader or a model can use, and mail HTML produces
#: long runs of them from spacer rows and nested wrappers.
_BLANK_RUN = re.compile(r"\n{3,}")


def to_text(html: str) -> str:
    """The readable text of an HTML fragment, entities resolved and blocks on their own lines.

    Takes a string and returns a string, and never raises: everything that arrives here was
    written by a stranger, and an empty body is an ordinary case (a mail with attachments
    only; with HTTP 206 the body is missing by design). A crash in the full text path would
    be the most expensive possible answer to a perfectly normal mail (T-10-15).

    It does not truncate. The byte cap belongs to the call site, where the cut can be marked
    as one (:mod:`mcp_connector.tools.marks`); a helper that cut silently would produce text
    that claims to be whole.
    """
    # Measured: ``document_fromstring("")`` and ``("   ")`` both raise
    # ``ParserError("Document is empty")``, so the empty case is decided before the parser
    # sees it rather than caught behind it.
    if not html or not html.strip():
        return ""

    try:
        # Measured: parsing the UTF-8 bytes with an explicit encoding gives character for
        # character the same result as parsing the string, and additionally survives the two
        # forms that make the string path fail or lie: an XML declaration (``ValueError:
        # Unicode strings with encoding declaration are not supported``) and a ``<meta
        # charset>`` that contradicts the text we already hold decoded.
        # ``no_network=True``: measured, libxml2's HTML parser resolved no external entity
        # and expanded no entity bomb even without it, but the option costs nothing and this
        # function is handed foreign HTML (T-10-13, T-10-14).
        parser = HTMLParser(no_network=True, encoding="utf-8")
        root = document_fromstring(html.encode("utf-8"), parser=parser)
    except (etree.ParserError, etree.XMLSyntaxError, ValueError):
        return ""

    # ``drop_tree`` keeps the tail text of the removed element, which ``parent.remove(el)``
    # would eat: the words after a style block belong to the sender. It lives on lxml's
    # ``HtmlMixin``, which the type stubs of ``document_fromstring`` do not carry, hence the
    # cast; the parser above builds html elements, so it is a cast and not a conversion.
    for element in list(root.iter(*_DROPPED_TAGS)):
        cast(HtmlMixin, element).drop_tree()

    for element in root.iter():
        tag = element.tag
        if not isinstance(tag, str):
            # Comments and processing instructions carry a callable tag. Their text stays out
            # of ``text_content()`` anyway; their tail is the sender's and stays in.
            continue
        if tag == _VOID_BLOCK_TAG:
            element.tail = "\n" + (element.tail or "")
        elif tag in _BLOCK_TAGS:
            element.text = "\n" + (element.text or "")
            element.tail = "\n" + (element.tail or "")

    # Measured leftover: an internal DTD subset leaves the two characters ``]>`` in the text.
    # That is named here and not scrubbed away: a second cleaning rule over foreign text would
    # be a second truth about what the sender wrote, and this function has exactly one.
    return _tidied(str(cast(HtmlMixin, root).text_content()))


def _tidied(text: str) -> str:
    """Line ends trimmed, runs of empty lines cut to one, the whole thing stripped."""
    lines = "\n".join(line.strip() for line in text.splitlines())
    return _BLANK_RUN.sub("\n\n", lines).strip()
