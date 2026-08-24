"""Unit tests for the Mail client, all paths, asserted on the request that was built.

Two properties of this client are contract and not implementation detail, and neither of them
is visible in a parsed answer, which is why both are tested against the URL:

*   **every** message URL carries ``view=singleton``. Without it the app answers the threaded
    view, and a thread root is not a message: the two are indistinguishable in the payload, so
    a wrong window would read like mail and be something else.
*   **every** message URL carries an explicit ``limit``. The parameter looks optional and the
    app's own description claims an empty value returns all messages, while the controller
    computes ``min(100, max(1, $limit))``, so an omitted limit answers exactly one message.

The four endpoints stand below as frozen literals. They are the guard against confusing the
declared OCS routes with the internal ``/apps/mail/api/`` route set, which is the cheaper and
worse way to read the same data: a route that moves there has to be moved on purpose.

The rest is the usual catalogue: an account without a single mail account, the 500 with status
996 that means the user's own mail server rather than a Nextcloud problem (K6), the 206 that is
a success without a body (K7), a 404 whose wording stays with the app, an HTML login page, an
answer shape that does not fit, and an invented id that never reaches Nextcloud at all.
"""

import ast
import inspect
import io
import tokenize
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import mail as mail_client
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
MAILBOX_ID = 7
MESSAGE_ID = 4711

# The frozen endpoint literals. Not one of them carries an ``api`` segment: the declared OCS
# routes sit directly below ``/apps/mail/``, and the ``/apps/mail/api/`` spelling belongs to
# the internal route set this client deliberately does not use.
ACCOUNTS_URL = f"{BASE}/ocs/v2.php/apps/mail/account/list"
MAILBOXES_URL = f"{BASE}/ocs/v2.php/apps/mail/ocs/mailboxes"
MESSAGES_URL = f"{BASE}/ocs/v2.php/apps/mail/ocs/mailboxes/{MAILBOX_ID}/messages"
MESSAGE_URL = f"{BASE}/ocs/v2.php/apps/mail/message/{MESSAGE_ID}"


def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


#: The measured account answer: four fields and nothing else, in particular no IMAP host.
ACCOUNT = {"id": 4, "email": "alice@nc.test", "isDelegated": False, "aliases": []}

#: The measured mailbox answer. It carries ``id`` and ``databaseId`` at the same time, and
#: they are not the same thing: ``id`` is base64 of the IMAP name and belongs to the Mail
#: frontend, ``databaseId`` is the number every other route of this family expects.
MAILBOX = {
    "accountId": 4,
    "attributes": ["\\HasNoChildren"],
    "cacheBuster": "8f2c",
    "databaseId": MAILBOX_ID,
    "delimiter": ".",
    "displayName": "INBOX",
    "id": "SU5CT1g=",
    "mailboxes": [],
    "myAcls": None,
    "name": "INBOX",
    "shared": False,
    "specialRole": "inbox",
    "specialUse": ["inbox"],
    "syncInBackground": True,
    "unread": 6,
}

ENVELOPE = {
    "databaseId": MESSAGE_ID,
    "uid": 12,
    "mailboxId": MAILBOX_ID,
    "subject": "Maße geprüft und übergeben",
    "previewText": "Grüße aus der Werkstatt, die Maße stimmen.",
    "dateInt": 1755181000,
    "flags": {"seen": False, "flagged": False, "answered": False, "hasAttachments": False},
    "from": [{"label": "Bob Beispiel", "email": "bob@nc.test"}],
    "to": [{"label": "Alice Beispiel", "email": "alice@nc.test"}],
    "tags": {},
}

FULL_MESSAGE = {
    "id": MESSAGE_ID,
    "uid": 12,
    "subject": "Maße geprüft und übergeben",
    "body": "<p>Gr&uuml;&szlig;e aus der Werkstatt.</p>",
    "hasHtmlBody": False,
    "dateInt": 1755181000,
    "from": [{"label": "Bob Beispiel", "email": "bob@nc.test"}],
    "isSenderTrusted": False,
    "hasDkimSignature": False,
    "phishingDetails": {"warning": False, "checks": []},
    "smime": {"isSigned": False, "signatureIsValid": None, "isEncrypted": False},
}

#: What a 206 looks like: the same message, complete except for its body.
ENCRYPTED_MESSAGE = {key: value for key, value in FULL_MESSAGE.items() if key != "body"}

#: The measured failure of the two IMAP backed routes: HTTP 500 with this status in the
#: envelope, sent whenever the user's mail server cannot be reached or the mailbox was never
#: synchronised.
MAIL_SERVER_ERROR = 996


@pytest.mark.anyio
async def test_the_account_list_is_handed_on_with_the_fields_the_app_sends(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ACCOUNTS_URL).mock(
            return_value=httpx.Response(200, json=envelope([ACCOUNT]))
        )
        accounts = await mail_client.get_accounts(client, creds)

    assert accounts == [ACCOUNT]
    assert str(route.calls.last.request.url) == ACCOUNTS_URL
    assert route.calls.last.request.headers["OCS-APIRequest"] == "true"


@pytest.mark.anyio
async def test_an_account_without_a_single_mail_account_is_a_success_with_zero_accounts(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Measured: 200 with ``[]``. The difference to "the Mail app is missing" is the next step.

    One says "set up an account in the Mail app", the other says "ask an administrator", so
    turning this into an error would answer the wrong question with confidence.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ACCOUNTS_URL).mock(return_value=httpx.Response(200, json=envelope([])))
        accounts = await mail_client.get_accounts(client, creds)

    assert accounts == []


@pytest.mark.anyio
async def test_the_mailbox_list_sends_the_account_and_nothing_else(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MAILBOXES_URL).mock(
            return_value=httpx.Response(200, json=envelope([MAILBOX]))
        )
        mailboxes = await mail_client.get_mailboxes(client, creds, 4)

    params = route.calls.last.request.url.params
    assert params["accountId"] == "4"
    assert list(params.keys()) == ["accountId"]
    assert mailboxes[0]["specialRole"] == "inbox", "a string, measured against GreenMail"
    assert mailboxes[0]["unread"] == 6


@pytest.mark.anyio
async def test_a_server_error_on_the_mailbox_list_points_at_the_mail_account(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """K6: the everyday failure of this family is the user's own mail server, not Nextcloud.

    The shared transport check turns every status from 500 upwards into "this is a problem on
    the Nextcloud side, retry later or check its log", and that sends the user to a log they
    cannot read about a machine that is not at fault.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MAILBOXES_URL).mock(
            return_value=httpx.Response(
                500, json=envelope(None, MAIL_SERVER_ERROR, "Internal Server Error\n")
            )
        )
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_mailboxes(client, creds, 4)

    spoken = f"{excinfo.value.message} {excinfo.value.hint}"
    assert "Mail" in spoken
    assert "account" in spoken
    assert "Nextcloud side" not in spoken, "the Nextcloud log is the wrong next step here"


@pytest.mark.anyio
async def test_a_server_error_on_the_message_list_says_the_same_thing(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Both IMAP backed routes fail the same way, so both carry the same branch."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(
                500, json=envelope(None, MAIL_SERVER_ERROR, "Internal Server Error\n")
            )
        )
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10)

    spoken = f"{excinfo.value.message} {excinfo.value.hint}"
    assert "Mail" in spoken
    assert "Nextcloud side" not in spoken


@pytest.mark.anyio
async def test_every_message_url_carries_the_single_view_and_an_explicit_limit(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The two properties a parsed answer never shows, asserted one by one."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        messages = await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10)

    called = str(route.calls.last.request.url)
    assert "view=singleton" in called, "without it the app answers threads, not messages"
    assert "limit=10" in called, "an absent limit answers exactly one message (K3)"
    params = route.calls.last.request.url.params
    assert params["view"] == mail_client.VIEW
    assert params["limit"] == "10"
    assert [message["databaseId"] for message in messages] == [MESSAGE_ID]


@pytest.mark.anyio
async def test_a_message_limit_outside_the_window_is_corrected_in_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Fifty envelopes are already as much as one answer should carry; zero would read empty."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=500)
        assert route.calls.last.request.url.params["limit"] == "50"
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=0)
        assert route.calls.last.request.url.params["limit"] == "1"

    assert mail_client.MAX_MESSAGES == 50


@pytest.mark.anyio
@pytest.mark.parametrize("blank", ["", "   ", "\t\n"], ids=["empty", "spaces", "whitespace"])
async def test_a_filter_without_content_never_appears_in_the_url(
    client: httpx.AsyncClient, creds: Credentials, blank: str
) -> None:
    """The app turns an empty filter into ``null``, so leaving it out is the same, but shorter."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10, filter_string=blank)

    assert "filter" not in route.calls.last.request.url.params


@pytest.mark.anyio
async def test_a_filter_with_content_is_handed_on_unchanged(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        await mail_client.get_messages(
            client, creds, MAILBOX_ID, limit=10, filter_string="is:unread from:bob"
        )

    assert route.calls.last.request.url.params["filter"] == "is:unread from:bob"


@pytest.mark.anyio
async def test_a_cursor_travels_as_a_whole_number_and_never_below_zero(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The cursor is the ``dateInt`` of the oldest envelope of the page, compared strictly."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10, cursor=1755181000)
        assert route.calls.last.request.url.params["cursor"] == "1755181000"
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10, cursor=-9)
        assert route.calls.last.request.url.params["cursor"] == "0"
        await mail_client.get_messages(client, creds, MAILBOX_ID, limit=10)

    assert "cursor" not in route.calls.last.request.url.params, "no cursor means the first page"


@pytest.mark.anyio
async def test_the_message_path_uses_the_database_id_and_never_the_base64_one(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The most expensive confusion of this family, ruled out at the URL (falle 10).

    The mailbox answer carries ``id`` and ``databaseId`` side by side; ``id`` is base64 of the
    IMAP name, and a URL built from it answers a 404 that reads like "no such mailbox".
    """
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(MESSAGES_URL).mock(
            return_value=httpx.Response(200, json=envelope([ENVELOPE]))
        )
        await mail_client.get_messages(client, creds, MAILBOX["databaseId"], limit=10)

    called = str(route.calls.last.request.url)
    assert called.startswith(MESSAGES_URL)
    assert str(MAILBOX["id"]) not in called
    assert MAILBOX["id"] != MAILBOX["databaseId"], "the fixture would prove nothing otherwise"


@pytest.mark.anyio
async def test_a_full_message_comes_back_with_its_body_and_its_trust_signals(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MESSAGE_URL).mock(return_value=httpx.Response(200, json=envelope(FULL_MESSAGE)))
        message, body_missing = await mail_client.get_message(client, creds, MESSAGE_ID)

    assert body_missing is False
    assert message["body"] == FULL_MESSAGE["body"]
    assert message["isSenderTrusted"] is False
    assert "dkimValid" not in message, "absent means unchecked, and it is absent in practice"


@pytest.mark.anyio
async def test_an_undecryptable_message_is_a_success_without_a_body(
    client: httpx.AsyncClient, creds: Credentials, monkeypatch: pytest.MonkeyPatch
) -> None:
    """K7: 206 means found and complete except for the body, and that is not a failure.

    The shared parser accepts 100, 200 and 201 only, and OCS v2 writes the raw status into
    ``ocs.meta.statuscode``, so this answer has to be recognised before it gets there. The
    monkeypatch is the assertion: reaching ``parse_ocs`` at all would already be the bug.
    """

    def never(*args: object, **kwargs: object) -> object:
        raise AssertionError("a 206 must be answered before parse_ocs sees it")

    monkeypatch.setattr(ocs, "parse_ocs", never)
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MESSAGE_URL).mock(
            return_value=httpx.Response(
                mail_client.PARTIAL, json=envelope(ENCRYPTED_MESSAGE, mail_client.PARTIAL, "")
            )
        )
        message, body_missing = await mail_client.get_message(client, creds, MESSAGE_ID)

    assert body_missing is True
    assert "body" not in message
    assert message["subject"] == "Maße geprüft und übergeben"
    assert sorted(ocs._OK_STATUS) == [100, 200, 201], "206 stays local, it is not widened"


@pytest.mark.anyio
async def test_an_unknown_message_id_does_not_repeat_what_the_app_says(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Measured: ``data`` is the string "Account not found." and ``meta.message`` is empty.

    The shared status mapping reads ``meta.message``, so the app's sentence is dropped, and
    that is the wanted outcome here (threat T-10-08): repeating it would tell the caller
    something about an account that is not theirs.
    """
    payload = {
        "ocs": {
            "meta": {"status": "failure", "statuscode": 404, "message": ""},
            "data": "Account not found.",
        }
    }
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MESSAGE_URL).mock(return_value=httpx.Response(404, json=payload))
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_message(client, creds, MESSAGE_ID)

    spoken = f"{excinfo.value.message} {excinfo.value.hint}"
    assert "Account not found" not in spoken
    assert "did not find" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_html_login_page_explains_itself_instead_of_raising_a_keyerror(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The classic symptom of a missing OCS header, and the shared parser already names it."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ACCOUNTS_URL).mock(
            return_value=httpx.Response(
                200,
                text="<!DOCTYPE html><html><head><title>Login</title></head></html>",
                headers={"content-type": "text/html; charset=UTF-8"},
            )
        )
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_accounts(client, creds)

    assert "HTML" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_account_answer_that_is_not_a_list_is_reported_as_such(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(ACCOUNTS_URL).mock(
            return_value=httpx.Response(200, json=envelope({"unexpected": True}))
        )
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_accounts(client, creds)

    assert "not a list of mail accounts" in excinfo.value.message
    assert "Mail app" in excinfo.value.hint


@pytest.mark.anyio
async def test_a_full_message_that_is_not_an_object_is_reported_as_such(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """An unexpected shape is a sentence plus a next step, never a TypeError."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(MESSAGE_URL).mock(return_value=httpx.Response(200, json=envelope("a string")))
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_message(client, creds, MESSAGE_ID)

    assert "not a message" in excinfo.value.message
    assert "Mail app" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("invented", ["abc", "", "-1", "1 OR 1=1"])
async def test_a_mailbox_id_that_is_not_a_number_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, invented: str
) -> None:
    """The app offers nothing to lean on: it casts to 0 and answers 404 (threat T-10-06)."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_messages(client, creds, invented, limit=10)

    assert len(route.calls) == 0
    assert "mail_browse" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("invented", ["abc", "", "-1", "1 OR 1=1"])
async def test_a_message_id_that_is_not_a_number_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, invented: str
) -> None:
    """The most expensive call of this family, kept away from a value that is certainly wrong."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_message(client, creds, invented)

    assert len(route.calls) == 0
    assert "mail_browse" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("invented", ["abc", "", "-1", "1 OR 1=1"])
async def test_an_account_id_that_is_not_a_number_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials, invented: str
) -> None:
    """The third id of the family goes into a query rather than a path, and is guarded alike."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await mail_client.get_mailboxes(client, creds, invented)

    assert len(route.calls) == 0
    assert "mail_browse" in excinfo.value.hint


@pytest.mark.anyio
async def test_the_guard_refuses_before_any_other_argument_is_even_read(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Order of operations, and it is the reason the guard is worth anything.

    A guard that ran after the URL was assembled would still raise, but the request would
    already exist; here nothing is built, whatever else the caller passed in.
    """
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError):
            await mail_client.get_messages(
                client, creds, "übergabe", limit=999999, filter_string="is:unread", cursor=-5
            )

    assert len(route.calls) == 0


def test_the_code_part_of_the_module_builds_no_write_path() -> None:
    """The server promise of this family, kept by not writing the code (threat T-10-07).

    The grep runs over the **code part** of the module: docstrings blanked through
    ``ast.get_docstring`` and comments through ``tokenize``, every other string literal kept.
    That is the helper ``_code_lines`` of ``tests/contract/test_no_destructive_calls.py``, and
    it is needed here rather than a plain grep over the file text, because this module has to
    name the routes it does not build in order to explain why it does not build them.
    """
    for forbidden in (
        "ocs_post",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "client.request",
        "/message/send",
        "/api/messages",
        "/api/mailboxes",
        "/api/accounts",
        "/api/drafts",
        "/api/outbox",
        "/api/thread",
        "/api/tags",
        "/api/trustedsenders",
        "attachment",
    ):
        assert forbidden not in _module_code(), f"{forbidden} has no place in a read only client"


def test_the_module_head_carries_the_three_words_a_plain_grep_would_cost() -> None:
    """The counter proof that makes the helper above necessary rather than pedantic.

    Shortening the explanation to get a naive grep green would trade the one paragraph that
    says why the cheaper route set is not used for a green check mark.
    """
    source = Path(mail_client.__file__).read_text(encoding="utf-8")
    head = ast.get_docstring(ast.parse(source)) or ""

    assert "SCOPE_IGNORE" in head, "the search term this decision is found under"
    assert "/api/messages" in head, "the resource route that makes a prohibition unsayable"
    assert "attachment" in head, "what is deliberately absent is named, not implied"


def test_the_reader_takes_its_limit_as_a_keyword_without_a_default() -> None:
    """Constructive rather than documented: an omitted decision does not compile away."""
    limit = inspect.signature(mail_client.get_messages).parameters["limit"]
    assert limit.default is inspect.Parameter.empty
    assert limit.kind is inspect.Parameter.KEYWORD_ONLY


def _module_code() -> str:
    """The client module with its docstrings and comments blanked out.

    A copy of ``_code_lines`` from ``tests/contract/test_no_destructive_calls.py``, on purpose:
    a test that imports the gate's helper would pass whenever the helper stopped working.
    """
    path = Path(mail_client.__file__)
    source = path.read_text(encoding="utf-8")
    blanked = source.splitlines()

    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if ast.get_docstring(node, clean=False) is None:
            continue
        first = node.body[0]
        end = first.end_lineno or first.lineno
        for lineno in range(first.lineno, end + 1):
            blanked[lineno - 1] = ""

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        lineno, column = token.start
        blanked[lineno - 1] = blanked[lineno - 1][:column]

    return "\n".join(text for text in blanked if text.strip())
