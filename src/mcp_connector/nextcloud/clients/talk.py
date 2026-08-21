"""Talk client: two API versions of one app, reading plus one send path.

The Talk app addresses conversations on API version **v4** and the chat inside a conversation
on API version **v1**, both below ``/ocs/v2.php/apps/spreed/api/``. One family, one module:
the dividing line between the two versions is a property of the app and must never land on
the caller, exactly as with the two generations of Tables.

Both mandatory headers of D-18 are already set by :func:`ocs.ocs_get` and
:func:`ocs.ocs_post`, which is why this module deliberately has no header constant of its
own. Tables needs one because its row route belongs to a generation 1 path that is built
directly; every route here goes through the OCS helpers.

The trap of this family is the four read parameters. A read of this API writes into the
user's own account by default: it moves the read marker, acknowledges notifications and
bumps the online status. The values that keep a read a read therefore live in
:data:`READ_ONLY_PARAMS` below, as a constant and not as arguments.

Neither route carries ``#[OpenAPI(scope: SCOPE_IGNORE)]``, and both stand in the published
``openapi.json`` of the app. They are a promised API, not internal frontend plumbing, so
this module needs no replaceability warning of the kind a Mail integration would need.

:data:`MAX_MESSAGES` is enforced, not offered. One message may be 32.000 characters long, so
a window without an upper bound is megabytes in a single MCP answer, and the API's own
default of 100 is twice what this project is willing to hand over.

There is deliberately no edit, no remove, no scheduled-send, no summary, no pinning, no
reminder, no file and no re-sharing path in this module, and the parameter that would send a
message without notifying anybody is not spelled anywhere in this file either. The server
promise is that it can neither change nor remove nor quietly place a message, and the
cheapest way to keep a promise is to never write the code that could break it (threat
T-09-03). A unit test greps this file for every one of those paths.

There is no retry on the send, on any layer. A duplicated message is visible to third
parties in their chat and cannot be removed again by any tool of this server, because
removing one is forbidden by its own gate. One attempt, and the answer carries the id of the
new message so the model can read back instead of repeating (threat T-09-07).
"""

import re
from collections.abc import Mapping
from typing import Any

import httpx

from ...errors import ToolError
from ..credentials import Credentials
from . import ocs

#: API version 4, the conversation list. It sits below ``/ocs/v2.php`` and is therefore built
#: through :func:`ocs.ocs_url`, never by string concatenation with the base URL.
ROOM_PREFIX = "/apps/spreed/api/v4/room"

#: API version 1, the chat inside one conversation. The version differs from the one above
#: because the app versions its conversation API and its chat API separately, and mixing the
#: two yields a 404 out of the routing layer that reads like "conversation not found".
CHAT_PREFIX = "/apps/spreed/api/v1/chat"

#: Web route of one conversation, used for the ``url`` field a human clicks. Talk answers it
#: from ``index.php``, which is not optional on every instance and therefore part of it.
TALK_WEB_PREFIX = "/index.php/call"

#: Upper bound of one history window. The API caps at 200 and defaults to 100, and a single
#: message may carry 32.000 characters, so 50 is the number this project is willing to place
#: in one answer.
MAX_MESSAGES = 50

#: The four parameters that keep a read a read. Not arguments: an argument is something a
#: caller can get wrong, and getting one of these wrong writes into the user's own account.
#:
#: ``lookIntoFuture`` is mandatory in the API and has no default at all, so leaving it out is
#: an error from the framework layer rather than a safe fallback; 0 means "history" instead
#: of "long poll", which is also what keeps a call from blocking for up to 30 seconds.
#: ``setReadMarker`` defaults to 1 in Talk and would move the read marker of this account.
#: ``markNotificationsAsRead`` defaults to 1 and would acknowledge the notifications of a
#: conversation nobody has opened. ``noStatusUpdate`` defaults to 0, and 0 means the request
#: is allowed to bump the online status of the account.
#:
#: In spreed 24.0.4 none of the last three can actually fire with these values: the read
#: marker and the notification acknowledgement only happen on the ``lookIntoFuture=1``
#: branch, and the status bump additionally needs a Talk mobile user agent and a session.
#: That is not a reason to drop them. The code that skips them carries a comment calling
#: itself temporary ("until it can be fixed in Vue"), and this project promises the
#: property, not the version.
READ_ONLY_PARAMS: Mapping[str, int] = {
    "lookIntoFuture": 0,
    "setReadMarker": 0,
    "markNotificationsAsRead": 0,
    "noStatusUpdate": 1,
}

#: The continuation of a history window travels in a response header, not in the body. The
#: name is a constant so the one place that reads it is greppable.
LAST_GIVEN_HEADER = "X-Chat-Last-Given"

#: Talk addresses a conversation by a token, and the token is not free text: every route of
#: the app declares this pattern as its path requirement.
_TOKEN = re.compile(r"[a-z0-9]{4,30}")

_SHAPE_HINT = "Check that the Talk app is enabled and up to date on that instance."


def web_url(creds: Credentials, token: str) -> str:
    """The link a human can open. Always built from the configured base URL."""
    return f"{creds.base_url}{TALK_WEB_PREFIX}/{token}"


async def get_rooms(
    client: httpx.AsyncClient,
    creds: Credentials,
    *,
    include_last_message: bool,
) -> list[dict[str, Any]]:
    """List the conversations this account is part of, newest activity **not** first.

    The answer carries 59 mandatory fields per conversation and no order at all: the query
    behind it has no ``ORDER BY``, so the sequence is whatever the database hands back.
    Sorting and capping therefore belong to the caller, and capping without sorting first
    would be an untruth nobody can see: "the 50 newest" would be 50 arbitrary ones.

    ``include_last_message`` is a keyword without a default so the caller makes the decision
    visibly. The preview of the last message is the largest single item of this answer: a
    conversation list wants it, a send pre-check does not need it at all.

    ``includeStatus``, ``modifiedSince`` and ``threadId`` are never set. The user status is
    payload without use here, and the modified-since form is a delta list, which is not the
    model this project answers in.
    """
    response = await ocs.ocs_get(
        client,
        creds,
        ROOM_PREFIX,
        params={"noStatusUpdate": 1, "includeLastMessage": include_last_message},
    )
    payload = ocs.parse_ocs(response, what="the Talk conversations")
    return _as_list(payload, what="conversations")


async def get_messages(
    client: httpx.AsyncClient,
    creds: Credentials,
    token: str,
    *,
    limit: int,
    last_known_message_id: int = 0,
) -> tuple[list[dict[str, Any]], int | None]:
    """Read one window of history, newest first, plus the id to continue with.

    Two things about the answer are not obvious and both are load bearing.

    A conversation without messages, and a window past the oldest message, answer **304**
    with no body. That is a success and not a redirect, so it is handled here: the shared
    parser turns every 3xx into "Nextcloud answered with a redirect, check the base URL",
    which would send the reader of a fresh conversation after a configuration problem that
    does not exist. The check stays local because 304 has a meaning on this one route only;
    a second special case in the shared parser would cost more than this line does.

    The continuation id comes out of the ``X-Chat-Last-Given`` header and never out of the
    returned messages. The app sets that header from the oldest comment it read and only
    afterwards drops the ones this account may not see or that have expired, so a window can
    be a 200 with an empty list and a usable header. Deriving the next page from the message
    ids would stop there and hide the older history behind it without saying so.

    ``limit`` is a keyword without a default, capped at :data:`MAX_MESSAGES` and lifted to at
    least one, and a negative cursor becomes zero, because the URL is built here and nowhere
    else.
    """
    conversation = _path_token(token)
    capped = min(max(int(limit), 1), MAX_MESSAGES)
    response = await ocs.ocs_get(
        client,
        creds,
        f"{CHAT_PREFIX}/{conversation}",
        params={
            **READ_ONLY_PARAMS,
            "limit": capped,
            "lastKnownMessageId": max(int(last_known_message_id), 0),
        },
    )
    if response.status_code == httpx.codes.NOT_MODIFIED:
        return [], None
    payload = ocs.parse_ocs(response, what=f"the messages of conversation {conversation}")
    return _as_list(payload, what="messages"), _last_given(response)


async def send_message(
    client: httpx.AsyncClient,
    creds: Credentials,
    token: str,
    *,
    message: str,
) -> dict[str, Any]:
    """Post one message into an existing conversation and return the message Talk stored.

    The success status here is **201**, not 200: the controller documents 201 as its only
    success and the published schema lists nothing else for it. In OCS v2 that number also
    reaches ``ocs.meta.statuscode``, which is why :data:`ocs._OK_STATUS` carries it.

    The body has exactly one key. The schema of this route also knows ``actorDisplayName``,
    ``referenceId``, ``replyTo``, ``replyToToken``, ``threadTitle`` and ``threadId``, and none
    of them is ever set: a display name chosen by a caller is an identity claim, and the
    others belong to a threading model this project does not answer in.

    There is no retry. If this call times out, that does not mean nothing was posted, and a
    second attempt would place a message twice in somebody else's chat, where no tool of this
    server can remove it again.
    """
    conversation = _path_token(token)
    response = await ocs.ocs_post(
        client,
        creds,
        f"{CHAT_PREFIX}/{conversation}",
        {"message": message},
    )
    return _as_dict(ocs.parse_ocs(response, what="the sent message"), what="a message")


def _path_token(value: str) -> str:
    """Tokens go into the path; anything but the declared pattern never leaves this process.

    Every Talk route declares ``[a-z0-9]{4,30}`` as its path requirement, so this guard is as
    sharp as the numeric one of Tables, only with a different alphabet (threat T-09-02). It
    matters more than a shape check: an unknown token on a single-conversation route
    registers a brute force attempt against the address of this container, which is one
    address for every user of the instance.
    """
    text = str(value).strip()
    if not _TOKEN.fullmatch(text):
        raise ToolError(
            message=f"{value!r} is not a Talk conversation token.",
            hint=(
                "Use a token exactly as talk_browse reports it; a Talk token is 4 to 30 "
                "lower case letters and digits."
            ),
        )
    return text


def _last_given(response: httpx.Response) -> int | None:
    """The cursor of the next, older page, or ``None`` when there is no older page.

    A missing header is the end of the history, and a header that is not a number is an
    instance or a proxy this project does not argue with: both mean "do not offer a next
    page", which is the honest answer and never a guessed one.
    """
    raw = response.headers.get(LAST_GIVEN_HEADER)
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return None


def _as_list(payload: Any, what: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ToolError(
            message=f"Nextcloud answered with something that is not a list of {what}.",
            hint=_SHAPE_HINT,
        )
    return [item for item in payload if isinstance(item, dict)]


def _as_dict(payload: Any, what: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ToolError(
            message=f"Nextcloud answered with something that is not {what}.",
            hint=_SHAPE_HINT,
        )
    return payload
