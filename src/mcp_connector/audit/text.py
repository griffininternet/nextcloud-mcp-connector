"""The one cleaning rule for a name written by a stranger, on its way into a line.

Three places of this application print a value nobody here wrote: the registered name of a
client, on the way into a row (``audit/record.py``) and on the way into the stored form of one
(``audit/store.py``), and the identifier of a user chain (``exapp/audit_verify.py``), which is
named after an account. Each of them carried its own version of this rule until this module
existed, and that is what :func:`printable` ends.

**Why this module sits in ``audit/`` and not in ``exapp/ui/``.** ``exapp/ui/layout.py`` holds a
fourth version of the same rule, and ``audit/record.py:107-109`` says why it may not be
imported from there: ``exapp`` sits above this package, so an import upwards would be a
layering break. The other direction is allowed and already taken: ``exapp/audit_verify.py``
reads ``from ..audit.store import ...``. A leaf module down here can therefore serve all three
callers, while the fourth version above stays where it is and keeps that layer independent of
this one.

**Why the rule is ``str.isprintable`` and not a list of C0 plus DEL.** Two of the three
versions replaced only the C0 range and DEL, which lets a character of the category Cf pass. A
right-to-left override belongs to that category, and inside an output line it turns the reading
direction of everything after it round: a name can look like a different name without carrying
one different letter. ``str.isprintable`` is False for Cf as well, so naming the class instead
of listing characters is what closes R-18-06 of ``.planning/phases/18-audit-log-kern``. A list
is a claim about which characters are dangerous; the class is a claim about which characters can
be printed, and only the second one is a claim this project can keep.

**Why a character is replaced and not dropped.** A dropped line break melts the two parts of a
name into one word, so ``"Claude\\nAssistant"`` would be recorded as a name that nobody ever
registered. A space cannot melt anything, and a run of them collapses into one anyway.
"""

__all__ = ["printable"]


def printable(raw: str, *, limit: int) -> str:
    """``raw``, made safe to print on one line and cut to ``limit`` characters.

    Three steps in this order: every character :meth:`str.isprintable` refuses becomes a
    space, runs of whitespace collapse into one space, and the rest is cut. The result is
    always a string and never ``None``: whether "nothing left to print" means an empty column
    or no name at all is the question of the caller, and the two callers answer it differently.

    ``limit`` is keyword only and has no default on purpose. The two bounds of this project are
    :data:`~mcp_connector.audit.store.CLIENT_NAME_LIMIT` and
    ``exapp.audit_verify.CHAIN_LIMIT``, and which of them applies is not a decision of this
    module.

    **What this does not do.** It keeps a name from ending a line and starting another one, so
    no name can fake a line of an answer. Inside its line a name can still say anything at all,
    which is why every command that prints one also offers a machine readable shape a script
    can watch instead of a substring of the text.
    """
    replaced = "".join(character if character.isprintable() else " " for character in raw)
    return " ".join(replaced.split())[:limit]
