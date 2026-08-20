"""The markers this server writes into a text, and the filter that keeps them its own.

Two answers of this package carry a sentence about themselves inside the text a document
fills: ``chatgpt.fetch`` says that a file was cut and where to continue, and the excerpt of
``context.prepare_context`` says that it is a preview of a longer document. Both are in
band signalling, and that is a deliberate trade: a model that reads only ``text`` has to be
able to tell a whole document from the beginning of one, and the ChatGPT contract has no
field for it.

**What the trade costs without this module (ME-03).** A document that other people may
write into can contain the same character sequence. Then a model sees "the server excerpt
ends here, what follows is not the document any more", and the framing of foreign text is
decided by whoever wrote that text, which is exactly the boundary D-57 rests on. The
mirror image works too: a document can claim to be complete where the server cut it.

**What this module does.** Every marker sequence is removed from foreign text before the
server writes its own. After that, a marker in an answer came from this server, because the
one other way in has been closed. Whitespace around the removed sequence stays as it was:
rewriting foreign text further is not the job of a filter, and a filter that reflows text
would be a second opinion about content this package deliberately does not have.

**The honest limit.** Only the exact sequences below are removed. A document can still
write something that reads like a marker, and no filter over free text can prevent that.
The clean answer is BL-09's schema variant, a separate field a document cannot produce; it
was deliberately not chosen (owner decision 2026-08-20), because it changes the response of
``prepare_context`` and touches the ChatGPT contract of ``fetch``, in which the marker sits
in the text on purpose. This module is the interim step: the response schema of both tools
stays exactly as it was.

Both constants live here rather than in the two modules that use them, because a second
copy of a sequence is a second chance for the filter to miss one of them. The two modules
re-export them under their established names.
"""

import re

#: Marked inside the text and not only beside it: a model that only reads the excerpt must
#: still be able to tell it from a whole document.
EXCERPT_TRUNCATION = "[excerpt truncated; call fetch with this id for the full text]"

#: The same idea one level down, for a file that was read as a slice. The offset is part of
#: the sentence, because it is what a caller needs to continue.
TRUNCATION_NOTE = "[truncated here; call files_read with offset {offset} to continue]"

_HEAD, _TAIL = TRUNCATION_NOTE.split("{offset}")

#: One pattern per marker. The note is matched by its shape and not by one value: a forged
#: copy carries whatever offset its author chose, so a filter that only knew the number this
#: server would have written would remove none of them.
_PATTERNS = (
    re.compile(re.escape(EXCERPT_TRUNCATION)),
    re.compile(re.escape(_HEAD) + r"\d+" + re.escape(_TAIL)),
)


def without_marks(text: str) -> str:
    """Foreign text with every marker sequence of this server removed.

    Called on the way in, before anything is appended, so the two are never confused: what
    the document wrote is gone by the time the server decides whether to mark a cut.
    """
    for pattern in _PATTERNS:
        text = pattern.sub("", text)
    return text
