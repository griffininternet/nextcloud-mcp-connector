"""The one cleaning rule for a name written by a stranger, case by case.

Three modules print values nobody in this project wrote: the registered name of a client
(``audit/record.py``, ``audit/store.py``) and the identifier of a user chain, which carries an
account name (``exapp/audit_verify.py``). Until this file existed each of them carried its own
version of the rule with its own set of characters, which is exactly what R-18-06 of
``18-SECURITY.md`` names as the open point: two of the three let a format character such as the
right-to-left override through, and inside one output line that character turns the reading
direction round.

So the cases below are the rule itself, and the last two of them are the other half of the fix:
one rule that three modules do not use would leave the tree exactly as divided as before, so
both the call and the absence of a character loop of their own are asserted per module.
``printable`` is synchronous, so nothing here needs ``anyio``.
"""

import inspect

from mcp_connector.audit import record, store
from mcp_connector.audit.text import printable
from mcp_connector.exapp import audit_verify

#: The bound the cases are measured against. Neither of the two real bounds of the project,
#: on purpose: this module decides no bound, it takes one.
LIMIT = 80

#: RIGHT-TO-LEFT OVERRIDE, category Cf, written as its code point so this file stays readable
#: in every editor. ``isprintable()`` is False for it, which is why the rule of the module
#: under test catches it and a list of C0 plus DEL never did.
OVERRIDE = chr(0x202E)


def test_a_line_break_becomes_a_space_instead_of_disappearing() -> None:
    """The heart of the rule: a control character is replaced and never dropped.

    Dropping it would let ``"Claude\\nAssistant"`` become one word, so two parts of a name
    could be melted into a third name that was never registered.
    """
    assert printable("a\nb", limit=LIMIT) == "a b"


def test_a_direction_mark_does_not_survive_the_rule() -> None:
    """R-18-06: a format character inside a line turns the reading direction round."""
    cleaned = printable("a" + OVERRIDE + "b", limit=LIMIT)

    assert OVERRIDE not in cleaned, "a format character may not reach an output line"
    assert cleaned in {"ab", "a b"}, cleaned


def test_a_run_of_whitespace_collapses_into_one_space() -> None:
    """Tabs and spaces in any number are one space, so no name can align a column."""
    assert printable("a\t\t   b", limit=LIMIT) == "a b"


def test_the_result_carries_no_leading_or_trailing_space() -> None:
    """A name that begins with whitespace would otherwise indent the line it stands in."""
    assert printable("  x  ", limit=LIMIT) == "x"


def test_a_name_longer_than_the_limit_is_cut_to_it() -> None:
    """The bound is the caller's, and this asserts it is really applied and not advertised."""
    assert len(printable("x" * 200, limit=LIMIT)) == LIMIT


def test_a_name_of_nothing_but_control_characters_ends_as_the_empty_string() -> None:
    """Empty and not ``None``: what "nothing to print" means belongs to the callers.

    ``record._clamped_client_name`` turns it into ``None`` because a row has a column for
    that; ``audit_verify._printable`` prints it as it is because a finding needs a line.
    """
    assert printable("\x00\x7f", limit=LIMIT) == ""


def test_the_empty_string_stays_the_empty_string() -> None:
    """The ordinary answer for a client that registered without a name."""
    assert printable("", limit=LIMIT) == ""


def test_a_name_of_only_whitespace_ends_as_the_empty_string() -> None:
    """The neighbour of the case above, and the one a caller really sees more often."""
    assert printable("   \t ", limit=LIMIT) == ""


# --- the other half of R-18-06: the rule is used, and no second one stayed behind ---


def test_every_caller_of_the_rule_really_calls_it() -> None:
    """One rule beside three unchanged callers would be a fourth version and nothing else."""
    for module in (record, store, audit_verify):
        source = inspect.getsource(module)

        assert "printable(" in source, f"{module.__name__} does not call the one rule"


def test_no_caller_kept_a_character_loop_of_its_own() -> None:
    """A second set of characters anywhere in the tree is R-18-06 itself, not a copy of it.

    ``.isprintable()`` as a call on a character is what ``record.py`` used, and the pair of
    ``< " "`` and DEL is what the other two used. Neither may come back without this turning
    red, which is why the needles are the two spellings and not the word "clean".
    """
    leftovers = {
        record: (".isprintable()",),
        store: ('< " "', "\\x7f"),
        audit_verify: ('< " "', "\\x7f"),
    }

    for module, needles in leftovers.items():
        source = inspect.getsource(module)
        for needle in needles:
            assert needle not in source, f"{module.__name__} still carries {needle!r}"
