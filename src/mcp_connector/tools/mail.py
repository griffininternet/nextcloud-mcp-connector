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
    "with truncated that it was cut."
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
    that its paging went in a circle (review finding IN-04).
    """
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Mail level.", hint=_LEVEL_HINT)
    if str(cursor or "").strip() and level != "messages":
        raise ToolError(
            message=f"level={level!r} has no next page, so a cursor cannot be applied here.",
            hint=_CURSOR_HINT,
        )
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
    return await _messages(clients, mailbox, capped, filter, cursor)


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
        oldest = min((_number(item.get("dateInt")) for item in raw), default=0)
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
            entry["truncated"] = True
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
    """One answer shape for all three levels, truncation named instead of silent."""
    kept = entries[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(entries) > len(kept):
        answer["truncated"] = True
    return answer
