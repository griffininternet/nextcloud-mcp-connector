"""Mail tools: one browse tool with three levels, and not one path that writes.

**One tool, three levels.** ``mail_browse(level=...)`` walks the mail accounts of the signed
in user, the mailboxes of one account and the message envelopes of one mailbox. Three
separate tools would cost three slots in every client that limits them and three schemas in
every ``tools/list``, for navigation the model can express in one enum value (D-06). The
answer envelope is the same on all three levels (``level``, ``count``, ``results``), so the
model learns one shape instead of three.

**The limits are enforced, not offered.** The window is :data:`DEFAULT_LIMIT` by default and
:data:`MAX_LIMIT` at most, a preview is cut at :data:`MAX_PREVIEW_BYTES` bytes, and every cut
is named in the answer instead of happening quietly. One sentence of this paragraph belongs
to this family alone: a ``limit`` that is not sent at all answers with exactly **one**
message in this app and not with all of them, which is why the client below takes it as a
keyword without a default and why nothing here can build a window-less URL.

**Two things are explained before they can fail.** A missing or disabled Mail app stops this
tool at the app detection, before the first Mail request (SRV-04). And a filter with an
unknown type is refused here instead of being dropped in silence by the app: its parser
returns ``false`` for a token it does not know and nobody reads that answer, so a typo comes
back as the **unfiltered** list, which is an answer that looks right and is wrong, and a
model has no way to see it.

**Deliberately absent:** sending, drafting, moving, flagging, deleting, downloading an
attachment, writing a tag, trusting a sender, and the full text filter ``body:``. The client
below has no code for any of it, which is what makes the read-only annotation of this family
honest rather than a promise. The full text of a single mail travels through the existing
``fetch`` with ``mail:<databaseId>`` and never through a second tool of its own (owner
decision).
"""

import re
from datetime import UTC, datetime
from typing import Any

from .. import ids, paging
from ..errors import ToolError
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import mail as mail_client
from . import marks

APP = "mail"

#: The three navigation levels of ``mail_browse``, in the order a model walks them.
LEVELS = ("accounts", "mailboxes", "messages")

#: MAIL-01: a mailbox read without an explicit limit reads this many envelopes. The ceiling is
#: the ceiling of the client one layer down, so no window of this tool can ask for more than
#: the app is willing to hand over anyway.
DEFAULT_LIMIT = 20
MAX_LIMIT = 50

#: Upper bound of one preview text, in **bytes**, measured on the UTF-8 encoding like every
#: other budget of this project. The number is a setting and not a measurement: plan 10-01
#: measured that the app cuts ``previewText`` itself at about 250 characters (the two
#: newsletters of 25 KB and 229 KB of text both arrived with exactly 251), so an ordinary
#: German preview of that length passes untouched and this cap is the guard against a Mail
#: version that stops cutting. It stands at this one place so phase 11 can weigh it against
#: ``prepare_context`` in a single edit.
MAX_PREVIEW_BYTES = 400

#: The key of the scope this family paginates in. A page handle belongs to one mailbox, and
#: :func:`paging.check_scope` refuses one from another; ``o`` beside it is the position, which
#: is a Unix timestamp here rather than an index.
_SCOPE = "m"

#: The id kind of a mail, in the spelling ``fetch`` expects. Plan 10-05 is the one that adds
#: ``ids.encode_mail`` and teaches ``ids.parse`` this kind; until then the prefix is built
#: from the separator of that module rather than from a second copy of the colon.
_ID_KIND = "mail"

_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."

#: The way out of a missing account number. No default and no "first account": a guessed
#: account is the kind of answer that looks right, and this family reads somebody's mail.
_ACCOUNT_HINT = (
    "Call mail_browse with level=accounts first; it lists the id of every mail account of "
    "this user."
)

#: The way out of a missing mailbox number, one level deeper and with the same reasoning.
_MAILBOX_HINT = (
    "Call mail_browse with level=mailboxes and that account_id first; it lists the id of "
    "every mailbox of the account."
)

#: The way out of a cursor on a level that has none. One sentence and the next step, like
#: every other refusal of this family.
_CURSOR_HINT = (
    "Only level=messages hands out a cursor. Call mail_browse without cursor; the answer says "
    "with truncated that the page was cut (a cut preview of a single entry is a different key, "
    "preview_truncated)."
)

#: The filter types this connector passes on, as a **positive** list. Three things are decided
#: here, and each of them costs an answer if it is decided the other way round.
#:
#: (a) The parser of the app drops an unknown type **in silence**: ``parseFilterToken``
#: returns ``false`` and nobody reads that answer, so ``is:ungelesen`` comes back as the
#: **unfiltered** list rather than as an error, measured on a live instance in plan 10-01 (six
#: of six messages, exactly like no filter at all). A model cannot tell that answer from a
#: correct one, which is why this is a positive list and not a negative one: a negative list
#: would let the next new verb of the app through by itself.
#:
#: (b) ``body:`` exists in the app and is missing here on purpose. It is the one filter that
#: leaves the database and searches over IMAP, so it costs one round trip to the mail server
#: of the user per call. The reason stands here so the omission is not repaired later as an
#: oversight.
#:
#: (c) Two properties of the app's parser are part of the documented grammar, because a caller
#: cannot guess them: the filter is split on **spaces**, and each token is split at the
#: **first** colon with everything after the second part falling away. A value that contains a
#: space or a colon therefore has to be percent encoded: ``subject:Rechnung%20Mai`` is the
#: only spelling that filters on both words, and ``subject:Rechnung Mai`` filters on
#: ``Rechnung`` and drops ``Mai`` without saying so (measured, plan 10-01).
#:
#: ``tags:`` takes the **numeric tag id** and not the IMAP label. That is a measurement of
#: plan 10-01 which corrects the research: ``tags:1`` matched one message and ``tags:$label1``
#: matched none.
FILTER_TYPES = frozenset({"is", "not", "from", "subject", "tags", "start", "end"})

#: The two types whose value is a flag name, and the values they take. ``unread`` and ``read``
#: are measured (plan 10-01: six hits and zero hits on the same six messages); ``starred``,
#: ``answered`` and ``important`` are read out of the parser of the app. The three special
#: forms of the importance classification (``is_important``, ``pi-important``, ``pi-other``)
#: are deliberately absent: they are undocumented internals of that classification, and this
#: connector does not pass on a filter it cannot describe in one sentence.
_FLAG_TYPES = frozenset({"is", "not"})
FLAG_VALUES = frozenset({"unread", "read", "starred", "answered", "important"})

#: The two types whose value is a point in time, and the shape that value has to have.
#: ``str.isdigit`` would accept a superscript two and an Arabic-Indic digit as well, and both
#: would reach the app as text it compares against an integer column.
_TIMESTAMP_TYPES = frozenset({"start", "end"})
_DIGITS = re.compile(r"[0-9]+")

_FILTER_HINT = (
    "Write every condition as type:value and separate them with spaces, using one of: "
    f"{', '.join(sorted(FILTER_TYPES))}. A value that contains a space or a colon has to be "
    "percent encoded (subject:Rechnung%20Mai), because the Mail app splits the filter on "
    "spaces and every token at its first colon."
)

_SECONDS_HINT = (
    "start: and end: are compared against the integer column sent_at, so they take Unix "
    "seconds and nothing else (start:1756000000). An ISO date is compared as text there: it "
    "filters everything away instead of failing, and a timestamp with a time of day would be "
    "cut at its first colon on top of that."
)

_FLAG_HINT = f"is: and not: take one of: {', '.join(sorted(FLAG_VALUES))}."

#: The way out of a filter on a level that reads no messages. Refused rather than ignored, for
#: the same reason as the cursor: an ignored parameter answers as if it had been applied.
_FILTER_LEVEL_HINT = (
    "Only level=messages takes a filter. Call mail_browse with level=messages and a "
    "mailbox_id, or leave filter out."
)


async def browse(
    clients: NcClients,
    level: str = "accounts",
    account_id: str | None = None,
    mailbox_id: str | None = None,
    filter: str | None = None,  # noqa: A002 - the name of the parameter in the Mail app
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Walk the user's Mail: the accounts, the mailboxes of one, or the envelopes of one.

    The order of the checks is the point of this function, and it is the order of every other
    browse tool of this server: the level, then a cursor on a level that hands none out, then
    the limit, then the app detection, and the mandatory id only inside the branch that needs
    it. The cheapest mistake a caller can make costs no request at all, and the app detection
    stands before the first Mail request rather than after it (SRV-04).

    A ``cursor`` on the account or the mailbox level is refused rather than ignored. Only the
    message level hands one out, so a handle on either of the other two is either a handle of
    that level or one somebody invented; answering it with the first page again would look
    like a page that happens to repeat the previous one, and a model has no way to notice
    that its paging went in a circle (review finding IN-04). A ``filter`` on one of those two
    levels is refused for the same reason and in the same place: neither of them reads
    messages, so applying it is impossible and ignoring it answers as if it had been applied.

    The whole filter is checked against :data:`FILTER_TYPES` **before** the app detection,
    which puts the most valuable refusal of this family at zero requests. The app would take a
    filter with a typo, drop the token it does not understand and answer with the unfiltered
    list, and that answer is more expensive than any error.
    """
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Mail level.", hint=_LEVEL_HINT)
    if str(cursor or "").strip() and level != "messages":
        raise ToolError(
            message=f"level={level!r} has no next page, so a cursor cannot be applied here.",
            hint=_CURSOR_HINT,
        )
    if str(filter or "").strip() and level != "messages":
        raise ToolError(
            message=f"level={level!r} reads no messages, so a filter cannot be applied here.",
            hint=_FILTER_LEVEL_HINT,
        )
    wanted = _checked_filter(filter)
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "accounts":
        return _envelope(level, await _accounts(clients), capped)

    if level == "mailboxes":
        account = str(account_id or "").strip()
        if not account:
            raise ToolError(message=f"level={level!r} needs an account_id.", hint=_ACCOUNT_HINT)
        return _envelope(level, await _mailboxes(clients, account), capped)

    mailbox = str(mailbox_id or "").strip()
    if not mailbox:
        raise ToolError(message=f"level={level!r} needs a mailbox_id.", hint=_MAILBOX_HINT)
    return await _messages(clients, mailbox, capped, wanted, cursor)


def _checked_filter(raw: str | None) -> str | None:
    """The filter string, checked token by token, or ``None`` for "no filter at all".

    Empty and whitespace only are a filter nobody asked for and become ``None``; the client
    then leaves the parameter out of the URL entirely, which is what the app makes of an empty
    string anyway, one round trip earlier and with a shorter URL.

    Five refusals, and every one of them replaces a right looking answer with a sentence:

    *   whitespace that is not the space character. The app splits its filter on **spaces
        alone**, so ``is:unread\\tfrom:chef`` reaches it as **one** token whose value is no
        known flag; the parser drops that token without a word and answers with the
        unfiltered list, exactly the silent wrong answer this gate exists against (review
        finding WR-01). ``str.split()`` here would read the same string as two valid tokens
        and wave it through, which is why this check comes first and refuses every character
        ``str.isspace`` accepts except the space itself, a tab and a no-break space included.
    *   a token without a colon. The app drops it silently, so ``unread`` alone filters
        nothing and reads like ``is:unread``.
    *   a type outside :data:`FILTER_TYPES`. The message names the type that was refused and
        the hint names the ones that work, because "invalid filter" without a list costs a
        round trip a single sentence prevents.
    *   an empty value. ``subject:`` reaches the app as a filter on the empty string.
    *   an ISO value on ``start:`` or ``end:``. Those two are compared against the integer
        column ``sent_at``, so ``start:2026-08-01`` filtered **all six** messages of the test
        instance away rather than filtering nothing (measured, plan 10-01), and
        ``start:2026-08-01T10:00:00Z`` would additionally be cut at its first colon. A filter
        that quietly removes everything is the worse answer of the two.

    After the whitespace refusal only spaces are left, so ``str.split()`` and the space split
    of the app see the **same** tokens: what passes this loop is what the app parses, token
    for token, and a value with whitespace in it has to be percent encoded either way.
    """
    wanted = str(raw or "").strip()
    if not wanted:
        return None

    if any(ch.isspace() and ch != " " for ch in wanted):
        raise ToolError(
            message="The filter contains whitespace the Mail app does not split on.",
            hint=_FILTER_HINT,
        )

    for token in wanted.split():
        kind, separator, value = token.partition(":")
        if not separator:
            raise ToolError(
                message=f"{token!r} is not a filter condition: it carries no colon.",
                hint=_FILTER_HINT,
            )
        if kind not in FILTER_TYPES:
            raise ToolError(
                message=f"{kind!r} is not a filter type this connector passes on.",
                hint=_FILTER_HINT,
            )
        if not value:
            raise ToolError(
                message=f"The filter condition {token!r} has no value.", hint=_FILTER_HINT
            )
        if kind in _TIMESTAMP_TYPES and not _DIGITS.fullmatch(value):
            raise ToolError(
                message=f"{value!r} is not a Unix timestamp, so {kind}: cannot use it.",
                hint=_SECONDS_HINT,
            )
        if kind in _FLAG_TYPES and value not in FLAG_VALUES:
            raise ToolError(
                message=f"{value!r} is not a message state this connector filters on.",
                hint=_FLAG_HINT,
            )
    return wanted


async def _accounts(clients: NcClients) -> list[dict[str, Any]]:
    """The mail accounts of this user, projected onto what a next call needs.

    An empty list is a success with zero accounts and explicitly not the same statement as a
    missing Mail app: one of them is answered by setting up an account in Mail, the other by
    asking an administrator, and the two next steps must stay distinguishable in the answer.

    This answer carries no IMAP host and no server name, because the app publishes none on
    this route and because the mail infrastructure of a person does not belong in a model
    context.
    """
    raw = await mail_client.get_accounts(clients.client, clients.creds)
    return [_account(item) for item in raw]


def _account(raw: dict[str, Any]) -> dict[str, Any]:
    """One account: the number the next level needs, the address, and two hints.

    ``delegated`` appears only when it is true, because "this is an ordinary account" is the
    normal case and costs nothing to say by omission. ``aliases`` arrives as a **count** and
    never as a list: an alias is a second address of the same account and not a navigation
    target, so the list would be payload for a fact one number carries.
    """
    entry: dict[str, Any] = {
        "id": _number(raw.get("id")),
        "email": _text(raw.get("email") or ""),
    }
    if raw.get("isDelegated"):
        entry["delegated"] = True
    aliases = raw.get("aliases")
    if isinstance(aliases, list) and aliases:
        entry["aliases"] = len(aliases)
    return entry


async def _mailboxes(clients: NcClients, account: str) -> list[dict[str, Any]]:
    """The mailboxes of one account, with the two fields that make them interpretable.

    ``account_id`` is mandatory and there is deliberately no default for it: the first account
    of the list is not the account somebody meant, and taking it would produce a right looking
    answer about the wrong mailbox (A7). It is the same decision the Talk family made for its
    conversation token and the Tables family for its table id.
    """
    raw = await mail_client.get_mailboxes(clients.client, clients.creds, account)
    return [_mailbox(item) for item in raw]


def _mailbox(raw: dict[str, Any]) -> dict[str, Any]:
    """One mailbox: the numeric id, the name, the role, the unread count and the delimiter.

    The base64 field ``id`` of the app is **not** passed on, and the reason is the same one
    the Talk family gives for the numeric room id: a second identity field in an answer is an
    invitation to use the wrong one, and ``databaseId`` is the number every other route of
    this family expects. Confusing the two is the most expensive mistake in this family, so
    only one of them exists here at all.

    ``display_name`` appears only when it differs from ``name``. In Mail 5.11.1 the two are
    identical, so repeating it would be one more line per mailbox that says nothing.

    Left out by name: ``specialUse`` (the full list ``special_role`` takes its first entry
    from), ``attributes``, ``myAcls``, ``shared``, ``syncInBackground``, ``cacheBuster`` and
    the nested ``mailboxes``, which are the internals of the Mail frontend.
    """
    name = _text(raw.get("name") or "")
    entry: dict[str, Any] = {
        "id": _number(raw.get("databaseId")),
        "name": name,
        "unread": _number(raw.get("unread")),
        "delimiter": _text(raw.get("delimiter") or ""),
    }
    role = _special_role(raw.get("specialRole"))
    if role:
        entry["special_role"] = role
    display = _text(raw.get("displayName") or "")
    if display and display != name:
        entry["display_name"] = display
    return entry


def _special_role(value: Any) -> str:
    """The IMAP special use of a mailbox as a lower case word, or an empty string.

    This one field needs a reader of its own rather than :func:`_number` or :func:`_text`,
    because the app declares it as ``int`` **or** ``str``: it is built from
    ``getSpecialUseParsed()[0] ?? 0``, so it is either the first special use or the number
    zero. Zero means "no role at all" and becomes a missing field rather than a role called
    ``0``; any other number is a deformed answer and is read the same way.

    The measured value set is ``inbox``, ``sent``, ``drafts``, ``trash``, ``junk``,
    ``archive`` and ``flagged``; plan 10-01 measured ``inbox`` as a ``str`` on a live
    instance, and the number zero is the branch read out of the source, because the test
    instance has an inbox and nothing else. Both have to work.
    """
    if isinstance(value, str):
        return value.strip().casefold()
    return ""


async def _messages(
    clients: NcClients,
    mailbox: str,
    limit: int,
    filter_string: str | None,
    cursor: str | None,
) -> dict[str, Any]:
    """One window of message envelopes of one mailbox, newest first.

    The handle is read before anything goes out, because it is the cheapest refusal of the
    two: a handle of another mailbox ends the call without a single Mail request. The
    continuation is the ``dateInt`` of the **oldest** message of the current page, which fits
    into :func:`paging.read_offset` unchanged, because that guard accepts any non negative
    integer and a Unix timestamp is one.

    The order is the order of the app, newest first, and there is no sort parameter at all.

    Two honest limits of this level, and neither of them is repaired here.

    The cursor of the app filters ``sent_at <`` **strictly**. Two mails that carry the same
    second across a page boundary therefore mean that the second one falls out, for good. The
    project made the same decision for the half open calendar window ("the time window is
    never corrected"), and for the same reason: a correction of our own (ask for one second
    more and de-duplicate here) would be a second truth about the order of the app, and two
    callers with the same window would see different lists depending on which of the two
    truths answered them.

    The app applies two filters by itself, whatever the ``filter`` parameter says: inside a
    flagged mailbox only flagged messages, and outside the trash no deleted ones. A window of
    this level is therefore the app's idea of that mailbox and not the raw IMAP folder.
    """
    position: int | None = None
    if cursor:
        state = paging.decode_cursor(cursor)
        # A handle of another mailbox would silently answer with a page of the wrong mailbox,
        # and the model has no way to notice. Saying so costs one round trip; guessing is a
        # wrong answer about somebody's mail.
        paging.check_scope(state, _SCOPE, mailbox, "mailbox")
        position = paging.read_offset(state)

    raw = await mail_client.get_messages(
        clients.client,
        clients.creds,
        mailbox,
        limit=limit,
        filter_string=filter_string,
        cursor=position,
    )
    entries = [_message(item) for item in raw if _number(item.get("databaseId")) > 0]

    answer: dict[str, Any] = {
        "level": "messages",
        "mailbox_id": mailbox,
        "count": len(entries),
        "results": entries,
    }
    if len(raw) >= limit:
        answer["truncated"] = True
        # The continuation is the oldest *valid* timestamp of the page. A single envelope
        # with a missing or deformed ``dateInt`` reads as 0 through ``_number``, and taking
        # the minimum over it would silently suppress the cursor: the answer would say
        # "truncated" without a ``next``, and the rest of the mailbox would be unreachable
        # (review finding WR-02). An envelope without a date falls out of the app's strict
        # ``sent_at <`` cursor anyway, so it has no say in where the next page begins.
        oldest = min(
            (stamp for item in raw if (stamp := _number(item.get("dateInt"))) > 0), default=0
        )
        if oldest > 0:
            answer["next"] = paging.encode_cursor({"o": oldest, _SCOPE: mailbox})
    return answer


def _message(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one envelope: who wrote what, when, and whether it was read.

    Left out by name, and the list is longer than the one that stays: the ten remaining
    booleans of ``flags`` beside the one ``unread`` is derived from, the five threading
    fields (``threadRootId``, ``inReplyTo``, ``references``, ``messageId`` and the thread
    flags), ``avatar``, ``fetchAvatarFromClient``, ``remoteId``, ``uid``, ``attachments`` and
    ``mentionsMe``. ``summary`` is left out with a reason of its own: it can be generated by
    a model, and a second opinion about foreign text beside that text is not something this
    server passes on as if it were the text.

    ``id`` is built from ``databaseId`` and from nothing else. A message carries ``uid``,
    ``remoteId``, ``messageId`` and, in the full message, ``id`` as well, and all four of them
    are the wrong number for ``fetch``. An envelope without a usable ``databaseId`` is left
    out of the list entirely, the same way the Talk family drops a conversation without a
    token: being addressable is what this level exists for.

    A missing preview is not an error. Plan 10-01 measured that a mail without a text body
    arrives with an empty ``previewText`` rather than without the field, and both say the same
    thing, so both end as a missing ``preview`` here instead of as an empty string that reads
    like a preview of nothing.
    """
    flags = raw.get("flags")
    flags = flags if isinstance(flags, dict) else {}

    entry: dict[str, Any] = {
        "id": f"{_ID_KIND}{ids.SEPARATOR}{_number(raw.get('databaseId'))}",
        "subject": _text(raw.get("subject") or ""),
        "from": _sender(raw.get("from")),
        "unread": not flags.get("seen"),
    }
    when = _date(raw.get("dateInt"))
    if when:
        entry["date"] = when
    preview, cut = _capped(_text(raw.get("previewText") or ""))
    if preview:
        entry["preview"] = preview
        if cut:
            # ``preview_truncated`` and not ``truncated``, and the difference is the whole
            # point: one level up, ``truncated`` means "this page was cut and there may be a
            # next", and :data:`_CURSOR_HINT` tells a model exactly that sentence. The same
            # word down here meant "this preview was cut at MAX_PREVIEW_BYTES", which is a
            # second meaning a model cannot resolve, because both readings are plausible in
            # the same answer: a cut page whose first entry carries a cut preview sets both
            # keys at once (review finding IN-01).
            entry["preview_truncated"] = True
    if flags.get("hasAttachments"):
        entry["has_attachments"] = True
    return entry


def _sender(raw: Any) -> str:
    """The first sender of an envelope as ``label <email>``, or as much of it as there is.

    The list has one entry in practice and the app allows several; the first is the sender and
    the rest is the shape of the field, not a second author. Both halves are foreign text: a
    label is what the sender chose to be called, which is why they go through :func:`_text`
    before anything else happens to them.
    """
    if not isinstance(raw, list) or not raw:
        return ""
    first = raw[0]
    if not isinstance(first, dict):
        return ""
    label = _text(first.get("label") or "").strip()
    email = _text(first.get("email") or "").strip()
    if label and email and label != email:
        return f"{label} <{email}>"
    return email or label


def _date(value: Any) -> str:
    """``dateInt`` as an ISO timestamp in UTC, or an empty string if there is no usable one.

    Unlike the Talk family, which passes its Unix numbers through, a mail date is read by a
    person as often as by a program, and one envelope carries exactly one of them, so the
    twenty five bytes per message buy a value nobody has to convert. A number the standard
    library cannot turn into a moment is answered with nothing rather than with a guess.
    """
    seconds = _number(value)
    if seconds <= 0:
        return ""
    try:
        return datetime.fromtimestamp(seconds, tz=UTC).isoformat()
    except (OSError, OverflowError, ValueError):
        return ""


def _capped(text: str) -> tuple[str, bool]:
    """One text at :data:`MAX_PREVIEW_BYTES`, and whether it had to be cut.

    The cut is measured on the UTF-8 encoding, because a byte is what an answer actually
    costs. Slicing the encoded form can land in the middle of a multi byte character, so the
    decode drops what it cannot read: an umlaut at the cutting point disappears instead of
    arriving as a broken character.

    A cut preview carries **no** marker inside the text. A preview is a fragment by
    definition, the full text is one ``fetch`` away, and a marker inside foreign text is an
    attack path (ME-03) for which a mail is the cheapest place of all: anybody may write one,
    without standing in anybody's address book. The truncation is a field beside the text.
    """
    blob = text.encode("utf-8")
    if len(blob) <= MAX_PREVIEW_BYTES:
        return text, False
    return blob[:MAX_PREVIEW_BYTES].decode("utf-8", errors="ignore"), True


def _text(value: Any) -> str:
    """Foreign text on its way into the model context, with our own markers removed.

    A subject, a preview and the label of a sender are written by whoever sent the mail, and
    that is anybody with an internet connection. Mail is therefore the family where this
    filter matters most: without it a stranger could write one of this server's own markers
    into a subject and decide how the text around it is framed (threat T-10-21).
    """
    return marks.without_marks(str(value))


def _number(value: Any) -> int:
    """A counter or an id of the app as a number, and 0 for anything that is not one.

    ``bool`` is excluded on purpose: it is an ``int`` in Python, and a ``True`` that arrives
    where a count belongs is a deformed answer and not the number one.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _envelope(level: str, entries: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for the account and the mailbox level, truncation named with a way out.

    Neither of these two levels hands out a cursor, and a bare ``truncated: true`` on a level
    without one reads like "cut, and there is no continuation" (review finding WR-03). The
    cut happens here in the projection, after the app already delivered the complete list, so
    the answer says what a caller can still do: raise the limit while there is room, and when
    :data:`MAX_LIMIT` is already reached, say honestly that the rest is out of reach for this
    tool rather than leaving the model to page in a circle.
    """
    kept = entries[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(entries) > len(kept):
        answer["truncated"] = True
        if len(kept) < MAX_LIMIT:
            answer["note"] = (
                f"{len(kept)} of {len(entries)} {level} shown; this level hands out no "
                f"cursor, so call mail_browse again with a larger limit (at most "
                f"{MAX_LIMIT}) to see more"
            )
        else:
            answer["note"] = (
                f"{len(kept)} of {len(entries)} {level} shown; this level hands out no "
                f"cursor and {MAX_LIMIT} is its ceiling, so the entries beyond it are not "
                "reachable through this tool"
            )
    return answer
