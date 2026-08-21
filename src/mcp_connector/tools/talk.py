"""Talk tools: one browse tool with two levels, and one write behind an administrative switch.

**One tool, two levels.** ``talk_browse(level=...)`` walks the conversations of the account
and the history of one of them. Two separate tools would cost two slots in every client that
limits them and two schemas in every ``tools/list``, for navigation the model can express in
one enum value (D-06). The answer envelope is the same on both levels (``level``, ``count``,
``results``), so the model learns one shape instead of two.

**The limits are enforced, not offered.** This app paginates the conversation list not at all
and orders it not at all, and one message may be 32.000 characters long, so the order, the
filter and the three cuts are made here: :data:`MAX_CONVERSATIONS` conversations,
:data:`MAX_LIMIT` messages per window and :data:`MAX_MESSAGE_BYTES` bytes per message. Every
cut is named in the answer, never silent.

**Two things are explained before they can fail.** A missing or disabled Talk app stops both
tools at the capabilities check, before the first Talk request (SRV-04). And an account that
may not write into a conversation is refused here with a sentence and a next step, instead of
being walked into a 403 without a body; the check reads the conversation object and not the
account, and Talk's own permission middleware stays the authority. The pre-check is only the
better error message.

**The order of the checks in the write path is reversed against every other tool of this
server.** Everywhere else the app detection is the first line. In the send path the
administrative switch of TALK-04 is, before the app detection and before any client call,
because a switch that is read after the message went out has prevented nothing.

Deliberately absent: editing a message, removing one, clearing a history, sending one later,
summarising a conversation, pinning, reminding, attaching a file, sending one without
notifying anybody and setting the read marker. The client below has no code for any of it,
which is what makes the create-only annotation of ``talk_send`` honest rather than a promise
(threat T-09-03).
"""

import re
from typing import Any

from .. import config, paging
from ..errors import ToolError
from ..exapp.ui import strings
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import talk as talk_client
from ..nextcloud.credentials import Credentials
from . import marks

APP = "spreed"

#: The two navigation levels of ``talk_browse``, in the order a model walks them.
LEVELS = ("conversations", "messages")

#: TALK-02: a history read without an explicit limit reads this many messages and not the
#: window of 100 the API hands over when the parameter is left out.
DEFAULT_LIMIT = 20
MAX_LIMIT = 50

#: TALK-01. This one is a cut and not a page: the app offers no pagination for the
#: conversation list at all, so the answer names the cut together with the number of
#: conversations behind it instead of handing out a page handle nobody can follow.
MAX_CONVERSATIONS = 50

#: Upper bound of one message text, in **bytes**. TALK-02 says "byte cap" literally, and this
#: project budgets in bytes everywhere else too (``MAX_TOOL_BYTES``, ``BUDGET_BYTES``), so the
#: cut is measured on the UTF-8 encoding and not on characters. The number 800 is a setting
#: and not a measurement (A6): it makes 50 messages roughly 40 KB in the worst case, and it
#: stands at this one place so phase 11 can adjust it against ``prepare_context`` in one edit.
MAX_MESSAGE_BYTES = 800

#: The message types that belong in a history a model reads, as a positive list. TALK-02 asks
#: for "no system messages", and a negative list (``!= "system"``) would let the next new verb
#: of the app through by itself. ``comment`` is an ordinary message, ``object_shared`` is one
#: with a file beside it, ``voice-message`` is one whose text is the transcript placeholder,
#: and ``private_reply`` is one somebody addressed to this account alone. Everything else
#: stays out on purpose: ``system`` and ``command`` are the app talking about itself,
#: ``comment_deleted`` and ``reaction_deleted`` are the traces of something that is gone,
#: ``reaction`` is a single emoji per line, and ``record-audio`` and ``record-video`` are call
#: recordings whose text says nothing about the conversation.
#:
#: There is deliberately no ``include_system`` parameter to switch this off. It would cost
#: schema bytes on every ``tools/list`` for a use nobody has shown, and if one ever turns up
#: it is one line.
KEPT_TYPES = frozenset({"comment", "object_shared", "voice-message", "private_reply"})

#: ``readOnly`` of a conversation that can be written in. Anything else is write protected.
READ_WRITE = 0

#: Conversation type 4, the automatically created "Talk updates" conversation. It is always
#: write protected regardless of its ``readOnly`` flag, and every account has exactly one of
#: them, often near the top of the list.
TYPE_CHANGELOG = 4

#: Bit 128 of the **resolved** ``permissions`` field of a conversation: the chat permission.
PERMISSIONS_CHAT = 128

_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."

#: The way out of every refusal that is about addressing: a missing token, a token nobody
#: knows and a handle of another conversation all end in the same next step. Named
#: ``_CONVERSATION_HINT`` and not ``_TOKEN_HINT`` because the linter of this repository reads
#: a string constant with ``TOKEN`` in its name as a hardcoded credential (S105), and a Talk
#: token is a conversation address rather than a secret.
_CONVERSATION_HINT = (
    "Call talk_browse with level=conversations first; it lists the token of every conversation "
    "of this account."
)

#: The way out of a cursor on a level that has none. One sentence and the next step, like every
#: other refusal of this family.
_CURSOR_HINT = (
    "Only level=messages hands out a cursor. Call talk_browse without cursor; the conversation "
    "list says with truncated and total that it was cut."
)

#: ``{placeholder}`` names of a message text. The values stand beside it in
#: ``messageParameters``, keyed by exactly this name.
_PLACEHOLDER = re.compile(r"\{([a-z0-9_-]+)\}", re.IGNORECASE)

#: Every collective mention this server refuses to send, and the syntax comes out of the
#: server rather than out of a guess. Nextcloud parses the mentions of a message in
#: ``OC\Comments\Comment::getMentions`` (nextcloud/server v34.0.0,
#: ``lib/private/Comments/Comment.php:216``), and the four collective types that regex can
#: answer with are ``group``, ``federated_group``, ``team`` and ``federated_team``; spreed then
#: turns each of them into a notification for every member (spreed v24.0.4,
#: ``lib/Chat/Notifier.php:525`` and ``:581``, reached from ``notifyMentionedUsers`` via
#: ``getMentionedGroupMembers`` and ``getMentionedTeamMembers``). ``guest/``, ``email/`` and
#: ``federated_user/`` are deliberately not in here: each of those addresses exactly one
#: person, which is what this tool is for.
#:
#: The quote is optional on both halves of the pattern. In the server regex the prefixed forms
#: only work quoted, because its unquoted alternative has no ``/`` in the character class, and
#: spreed skips the unquoted spelling as well (``lib/Chat/Parser/UserMention.php:138-145``).
#: Refusing it anyway is the same precaution that refuses ``@here``: a version in which the
#: other spelling works costs nothing here, and no legitimate address of one person is lost.
#:
#: Two boundaries keep real people sendable. The lookahead after the two words is what makes
#: ``@allan`` and ``@allison`` mentions of somebody, and the ``/`` after the four prefixes does
#: the same for ``@grouping`` and ``@teamster``.
_MENTION_COLLECTIVE = re.compile(
    r"@\"?(?:(?:all|here)\"?(?![\w-])|(?:federated_)?(?:group|team)/)",
    re.IGNORECASE,
)


async def browse(
    clients: NcClients,
    level: str = "conversations",
    token: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Walk the user's Talk: the conversations of the account, or the history of one of them.

    A ``cursor`` on the conversation level is refused rather than ignored, and it is refused
    here, before the capabilities request, so the cheapest mistake costs no request at all.
    Only the message level hands one out, so a handle on this level is either a handle of the
    other level or one somebody invented; answering it with the first page again would look
    like a page that happens to be identical to the previous one, and a model has no way to
    notice that its paging went in a circle (review finding IN-04).
    """
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Talk level.", hint=_LEVEL_HINT)
    if str(cursor or "").strip() and level != "messages":
        raise ToolError(
            message=f"level={level!r} has no next page, so a cursor cannot be applied here.",
            hint=_CURSOR_HINT,
        )
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "conversations":
        return await _conversations(clients, capped)

    conversation = str(token or "").strip()
    if not conversation:
        raise ToolError(message=f"level={level!r} needs a token.", hint=_CONVERSATION_HINT)
    return await _messages(clients, conversation, capped, cursor)


async def send(clients: NcClients, token: str, message: str) -> dict[str, Any]:
    """Send one message into a conversation this account is part of. Never edits or removes.

    The order of this function is the reverse of every other tool of this server, and the
    first line is what reverses it: the administrative switch of TALK-04 is read before the
    app is looked up and before any client call, because a switch that is read after the
    message went out has prevented nothing (threat T-09-20).

    Six refusals follow, and each of them is cheaper than the write it prevents.

    The length comes from the instance (``config.chat.max-length``) with the number Talk 24
    ships as the fallback, so the limit is not maintained a second time here.

    A collective mention is refused, and not only the two that mean everybody. ``@all`` is the
    one that works everywhere: Talk turns it into a notification of every participant of the
    conversation, which makes one tool call a message to everybody. ``@"group/<id>"``,
    ``@"team/<id>"`` and their two federated spellings are the same amplifier one size smaller,
    one notification per member of a whole group or team, so they are refused with it (threat
    T-09-23; the six spellings and their source in spreed 24 and in the Nextcloud comment
    parser stand at :data:`_MENTION_COLLECTIVE`). ``@here`` is ordinary text in spreed 24 and is
    refused as a precaution against a version in which it is not. The two boundaries of that
    pattern matter, because a plain containment test would refuse ``@allan``, ``@allison`` and
    ``@grouping`` as well, and those are legitimate mentions of real people; so is
    ``@"federated_user/alice@cloud.example"``, which addresses exactly one person and passes.

    A missing token is refused before that lookup, the same way :func:`browse` refuses one, so
    the cheapest mistake a caller can make costs no request at all. It also closes a second
    door: an empty string is what a conversation without a token of its own would match in the
    list, and matching it there is worse than not asking.

    The token has to stand in the conversation list of this account, so the pre-check goes
    through ``talk_client.get_rooms`` (in :func:`_room`) and never through the single
    conversation route: an unknown token there is a counted brute force attempt against the
    address of this whole container, which is one address for every user of the instance.

    Then the conversation object decides whether this account may write into it at all, by the
    three rules of :func:`_may_send`.

    There is no retry. If this call times out, that does not mean nothing was posted, and a
    second attempt would place a message twice in somebody else's chat, where no tool of this
    server can remove it again. The answer carries the id and the name of the conversation so
    the model can read back instead of repeating (threat T-09-25).
    """
    if not config.talk_send_enabled():
        raise ToolError(
            message="Sending Talk messages is switched off for this Nextcloud.",
            hint=(
                f"This account cannot change it: an administrator switches it on under "
                f"{strings.ADMIN_SETTINGS_PLACE}, and the change takes effect after this app "
                "is disabled and enabled again. Reading conversations and their history with "
                "talk_browse is unaffected."
            ),
        )

    caps = await capabilities.require_app(clients, APP)

    text = str(message or "")
    allowed = caps.spreed_chat_max_length or capabilities.DEFAULT_CHAT_MAX_LENGTH
    if len(text) > allowed:
        raise ToolError(
            message=(
                f"The message is {len(text)} characters long, and this Nextcloud accepts "
                f"{allowed} per message."
            ),
            hint="Shorten the message, or split it into several messages and send them one by one.",
        )
    if _MENTION_COLLECTIVE.search(text):
        raise ToolError(
            message=(
                "A message that mentions everybody or a whole group at once is not sent "
                "through this connector."
            ),
            hint=(
                'Talk turns @all, @"group/<id>" and @"team/<id>" into a notification for every '
                "participant or member at once, and in many conversations only moderators may "
                "do that at all (mention_permissions in talk_browse). Mention the people you "
                "mean one by one instead; a mention of a single account, a guest or a federated "
                "user is sent."
            ),
        )

    conversation = str(token or "").strip()
    if not conversation:
        raise ToolError(
            message="Sending needs the token of a conversation.", hint=_CONVERSATION_HINT
        )
    room = await _room(clients, conversation, include_last_message=False)
    name = _text(room.get("displayName") or "")
    allowed_here, why = _may_send(room)
    if not allowed_here:
        raise _refusal(why, conversation, name)

    sent = await talk_client.send_message(clients.client, clients.creds, conversation, message=text)
    message_id = sent.get("id")
    if message_id in (None, ""):
        raise ToolError(
            message="Nextcloud accepted the message but reported no id.",
            hint=(
                f"Look for it in the conversation {name!r}, it was probably sent; reading the "
                "history back with talk_browse is cheaper than sending it twice."
            ),
        )

    return {
        "sent": True,
        "id": message_id,
        "token": conversation,
        "conversation": name,
        "timestamp": _number(sent.get("timestamp")),
        "url": talk_client.web_url(clients.creds, conversation),
    }


def _refusal(why: str, token: str, name: str) -> ToolError:
    """One sentence per reason of :func:`_may_send`, each with its own next step."""
    if why == "read-only":
        return ToolError(
            message=f"The conversation {name!r} ({token}) is read only.",
            hint=(
                "A moderator of that conversation can lift the read only state in Talk. "
                "Conversations this account may write in are the ones talk_browse reports "
                "with can_send true."
            ),
        )
    if why == "changelog":
        return ToolError(
            message=(
                f"{name!r} ({token}) is the changelog conversation of this account, and Talk "
                "keeps it read only."
            ),
            hint=(
                "It is created automatically for every account and carries the release notes "
                "of Talk, so nothing can be sent into it. Pick one of the other conversations "
                "talk_browse reports with can_send true."
            ),
        )
    return ToolError(
        message=f"This account has no chat permission in {name!r} ({token}).",
        hint=(
            "The chat permission of this conversation was taken away for this account; a "
            "moderator can grant it again in Talk. Conversations this account may write in are "
            "the ones talk_browse reports with can_send true."
        ),
    )


async def _conversations(clients: NcClients, limit: int) -> dict[str, Any]:
    """The conversations of this account, newest activity first, put-aside ones left out.

    The order of the three steps is the whole point of this function. ``getRoomsForUser``
    builds its query without an ``ORDER BY``, so the sequence the app hands back is a database
    matter, and a cut after 50 without sorting first would not answer with the 50 newest
    conversations but with 50 arbitrary ones. On a test instance with three conversations that
    is invisible; on a real one with eighty it is a wrong answer nobody can see. So: sort,
    then filter, then cut.

    The filter runs here because the API has no parameter for it. ``isArchived`` is a field of
    the answer, exactly as ``archived`` is in Deck and in Tables.

    A conversation without a token is left out as well. It cannot be addressed, and being
    addressable is what this level exists for.
    """
    rooms = await talk_client.get_rooms(clients.client, clients.creds, include_last_message=True)
    ordered = sorted(rooms, key=lambda room: _number(room.get("lastActivity")), reverse=True)
    entries = [
        _conversation(clients.creds, room)
        for room in ordered
        if not room.get("isArchived") and str(room.get("token") or "").strip()
    ]
    # No cursor on this level, and that is a decision rather than an omission. The app does
    # not paginate this list, so a handle could only fetch the whole list again and cut it
    # somewhere else, which is a round trip for a different slice of the same read. The cut
    # plus the total number behind it says the same thing honestly and costs one number.
    #
    # A handle that arrives here anyway is refused in :func:`browse` and never silently
    # dropped (IN-04): this function is only reached without one.
    answer = _envelope("conversations", entries, min(limit, MAX_CONVERSATIONS))
    if answer.get("truncated"):
        answer["total"] = len(entries)
    return answer


def _conversation(creds: Credentials, room: dict[str, Any]) -> dict[str, Any]:
    """Project one conversation onto the fields a model reads, and drop the other fifty.

    ``GET /api/v4/room`` answers with 59 mandatory fields per conversation: everything about
    calls, the lobby, signaling, SIP, breakout rooms, avatars, recording and live
    transcription. None of that survives here, and neither does the numeric room ``id``: it
    addresses none of the three routes this family builds, and a second identity field in an
    answer is an invitation to use the wrong one.

    ``name`` comes from ``displayName`` and never from ``name``. For a one to one conversation
    ``name`` is a JSON array of user ids, which is not something to show to anybody.

    ``unread`` is the counter of the app and not an exact number of messages. A conversation
    nobody ever opened reports 1 even when it is empty, because the web interface wants a dot
    on it, and the history of that same conversation then answers with nothing at all. The
    number is passed through and said to be the app's counter; correcting it would invent a
    second truth about somebody else's number.

    ``last_activity`` stays the Unix number the app sent, like ``modified`` in
    :mod:`mcp_connector.tools.notes`. An ISO string would have to invent a zone and costs
    around 700 bytes in one full answer.
    """
    token = str(room.get("token") or "").strip()
    entry: dict[str, Any] = {
        "token": token,
        "name": _text(room.get("displayName") or ""),
        "type": _number(room.get("type")),
        "unread": _number(room.get("unreadMessages")),
        "unread_mention": bool(room.get("unreadMention")),
        "unread_mention_direct": bool(room.get("unreadMentionDirect")),
        "last_activity": _number(room.get("lastActivity")),
        "read_only": _number(room.get("readOnly")),
        "can_send": _may_send(room)[0],
        "url": talk_client.web_url(creds, token),
    }
    preview = _preview(room.get("lastMessage"))
    if preview:
        entry["last_message"] = preview
    if _number(room.get("mentionPermissions")):
        entry["mention_permissions"] = _number(room["mentionPermissions"])
    return entry


def _preview(raw: Any) -> str:
    """The last message of a conversation as one line, or an empty string.

    The app answers with an empty array instead of an object for a conversation without
    messages, and it drops the preview server side for a conversation somebody marked
    sensitive. Both arrive here as "nothing to show", which is why the shape is checked rather
    than the emptiness.

    A cut preview carries no marker of its own. A preview is a fragment by definition, and the
    full text is one call away on the message level.
    """
    if not isinstance(raw, dict):
        return ""
    text, _ = _capped(_resolve(raw.get("message"), raw.get("messageParameters")))
    return text


async def _messages(
    clients: NcClients, token: str, limit: int, cursor: str | None
) -> dict[str, Any]:
    """One window of the history of one conversation, newest message first.

    The handle is read before anything goes out, because it is the cheapest refusal of the
    two: a handle of another conversation ends the call without a single Talk request.

    The conversation itself is read after that, for two answers out of one request. It turns
    a token a model invented into our own sentence instead of a request against a Talk path,
    and it is where the display name of the envelope comes from, so a wrong pick is visible
    without a second tool call.

    ``truncated`` and ``next`` come from the continuation id of the client and never from the
    number of messages in this answer. The app takes that id from the oldest message it read
    and only afterwards drops the ones this account may not see or that have expired, and the
    positive list of message types does the same thing a second time. A window with nothing in
    it and a continuation behind it is therefore a regular case and not the end of the
    history: reading the end out of an empty window would hide the older history without
    saying so.

    The order stays the order of the app, newest first. Turning it around would produce an
    answer whose sequence contradicts the meaning of ``next``, which walks backwards into the
    past.
    """
    last_known = 0
    if cursor:
        state = paging.decode_cursor(cursor)
        # A handle of another conversation would silently answer with a page of the wrong
        # chat, and the model has no way to notice. Saying so costs one round trip; guessing
        # is a wrong answer about somebody's conversation.
        paging.check_scope(state, "c", token, "conversation")
        last_known = paging.read_offset(state)

    room = await _room(clients, token, include_last_message=False)
    raw, last_given = await talk_client.get_messages(
        clients.client, clients.creds, token, limit=limit, last_known_message_id=last_known
    )
    kept = [_message(item) for item in raw if _is_kept(item)]

    answer: dict[str, Any] = {
        "level": "messages",
        "token": token,
        "conversation": _text(room.get("displayName") or ""),
        "count": len(kept),
        "results": kept,
    }
    if last_given is not None:
        answer["truncated"] = True
        answer["next"] = paging.encode_cursor({"o": last_given, "c": token})
    return answer


def _is_kept(raw: dict[str, Any]) -> bool:
    """Whether this message belongs in a history a model reads (:data:`KEPT_TYPES`)."""
    return str(raw.get("messageType") or "") in KEPT_TYPES


def _message(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one message: who wrote what, when, and whether this is all of it.

    Left out by name: ``reactions`` (a mandatory field on every single message, bytes without
    use here), ``parent`` (which can carry a whole second message), ``markdown``,
    ``isReplyable``, ``referenceId``, ``threadId``, ``isThread``, ``threadTitle``,
    ``threadReplies``, ``metaData``, ``reactionsSelf`` and ``expirationTimestamp``.

    The truncation is a field beside the text and never a marker inside it. A marker inside
    foreign text is an attack path (ME-03), and a chat message is the cheapest place for it of
    all, because every participant of a conversation may write one.
    """
    text, cut = _capped(_resolve(raw.get("message"), raw.get("messageParameters")))
    entry: dict[str, Any] = {
        "id": raw.get("id"),
        "timestamp": _number(raw.get("timestamp")),
        "actor": _text(raw.get("actorDisplayName") or ""),
        "message": text,
    }
    if cut:
        entry["truncated"] = True
    if raw.get("lastEditTimestamp"):
        entry["edited"] = True
    return entry


def _resolve(message: Any, parameters: Any) -> str:
    """Put the values of ``messageParameters`` into the ``{placeholder}`` text of a message.

    Talk sends the text with placeholders and the values beside it, already resolved into
    display names for guests, groups, teams and federated accounts. Reading that answer is
    therefore the cheap way round; parsing the ``@"user id"`` syntax of the raw text a second
    time would be a second truth about foreign identities.

    A mention keeps its ``@`` so it still reads as one, and a mention is recognised by its
    ``mention-id`` or by the name of its placeholder, never by ``type`` alone: the author of a
    message arrives as ``{actor}`` with type ``user`` as well, and prefixing that one would
    make every message look as if it mentioned its own author.

    An unknown placeholder, and one whose entry carries no name, stays in the text exactly as
    it came. Nothing is guessed here.

    The result is foreign text and goes through :func:`marks.without_marks` before anything
    else happens to it.
    """
    params = parameters if isinstance(parameters, dict) else {}

    def replace(match: re.Match[str]) -> str:
        entry = params.get(match.group(1))
        if not isinstance(entry, dict):
            return match.group(0)
        name = str(entry.get("name") or "").strip()
        if not name:
            return match.group(0)
        return f"@{name}" if _is_mention(match.group(1), entry) else name

    return marks.without_marks(_PLACEHOLDER.sub(replace, str(message or "")))


def _is_mention(key: str, entry: dict[str, Any]) -> bool:
    """Whether this parameter is a mention of somebody rather than a plain value."""
    if entry.get("mention-id"):
        return True
    if str(entry.get("type") or "") == "call":
        return True
    return key.casefold().startswith("mention")


def _capped(text: str) -> tuple[str, bool]:
    """One text at :data:`MAX_MESSAGE_BYTES`, and whether it had to be cut.

    The cut is measured on the UTF-8 encoding, because TALK-02 asks for a byte cap and because
    a byte is what an answer actually costs. Slicing the encoded form can land in the middle of
    a multi byte character, so the decode drops what it cannot read: an umlaut at the cutting
    point disappears instead of arriving as a broken character.
    """
    blob = text.encode("utf-8")
    if len(blob) <= MAX_MESSAGE_BYTES:
        return text, False
    return blob[:MAX_MESSAGE_BYTES].decode("utf-8", errors="ignore"), True


async def _room(clients: NcClients, token: str, *, include_last_message: bool) -> dict[str, Any]:
    """The conversation with this token out of this account's own list, or a refusal.

    Never ``GET /room/{token}`` with a token that came out of a model. That route answers an
    unknown token with a counted brute force attempt against the address of this container,
    which is one address for every user of the instance, so a model that invents tokens would
    slow Talk down for everybody and end in a 429 (threat T-09-21). The list costs the same
    single request, carries no token in its path and is the account's own data.

    A token that is not in the list therefore becomes our own sentence, and Nextcloud never
    sees it in a path at all.
    """
    rooms = await talk_client.get_rooms(
        clients.client, clients.creds, include_last_message=include_last_message
    )
    for room in rooms:
        if str(room.get("token") or "").strip() == token:
            return room
    raise ToolError(
        message=f"The token {token!r} is not in the conversation list of this account.",
        hint=_CONVERSATION_HINT,
    )


# The trap of this family, and the third instance of the same class in this project after
# ``canCreateBoards`` in phase 1 and ``onSharePermissions`` in phase 8. The field that looks
# like the answer is ``attendeePermissions``: it carries the *raw* value of the participant
# and is 0 for practically every ordinary account, because Talk resolves the permissions
# through a fallback chain (attendee, then conversation, then instance) and grants a moderator
# everything. Reading it would refuse almost everybody in almost every conversation, and the
# failure would look like a permission problem instead of a field name. The resolved result is
# ``permissions``, and that is the field Talk's own middleware checks, so that is the field
# below. It is named here and not in the docstring because a test of this plan greps the
# module for the wrong name outside of comments.
def _may_send(room: dict[str, Any]) -> tuple[bool, str]:
    """Whether this account may send into this conversation, and why not if it may not.

    Three refusals, and each one has a reason of its own.

    ``readOnly`` other than :data:`READ_WRITE` is a conversation somebody switched to read
    only. Type :data:`TYPE_CHANGELOG` is the "Talk updates" conversation, which
    ``checkReadOnlyState`` refuses regardless of that flag, and it stands in the list of every
    account, which makes it a plausible pick for a model that was told to send something. And
    a resolved permission set without :data:`PERMISSIONS_CHAT` is an account whose chat
    permission was taken away in that one conversation, which is the case the comment above
    this function is about.

    Type 6, the note to self, is writable and must not be locked away with the others.

    Talk's own middleware stays the authority. This answer is only the better error message,
    and ``can_send`` in the conversation list is the same answer one step earlier.
    """
    if _number(room.get("readOnly")) != READ_WRITE:
        return False, "read-only"
    if _number(room.get("type")) == TYPE_CHANGELOG:
        return False, "changelog"
    if not _number(room.get("permissions")) & PERMISSIONS_CHAT:
        return False, "no-chat-permission"
    return True, ""


def _text(value: Any) -> str:
    """Foreign text on its way into the model context, with our own markers removed.

    A message text and a display name are written by whoever may write into the conversation,
    so they are the place where a chat could otherwise claim to be this server talking
    (threat T-09-24).
    """
    return marks.without_marks(str(value))


def _number(value: Any) -> int:
    """A counter or a flag of the app as a number, and 0 for anything that is not one.

    ``bool`` is excluded on purpose: it is an ``int`` in Python, and a ``True`` that arrives
    where a count belongs is a deformed answer and not the number one.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _envelope(level: str, entries: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for both levels, truncation named instead of silent."""
    kept = entries[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(entries) > len(kept):
        answer["truncated"] = True
    return answer
