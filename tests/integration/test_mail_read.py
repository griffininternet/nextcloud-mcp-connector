"""Reading mail, measured against a real instance: the three levels, the full text, the limits.

The unit layer of plans 10-02 to 10-06 pins shapes against invented answers. Success criteria
1 to 3 of this phase are statements about a **user** ("a user can read their mail"), and an
invented answer cannot carry one of those. This file therefore walks the tool paths
``mail_tools.browse`` and ``chatgpt.fetch`` rather than the client functions underneath them:
what a user gets is what the tool returns, and a client that answered correctly into a tool
that projected wrongly would still be a broken promise.

Four things are load bearing in here.

*   **What is measured and what is not claimed.** The rows below are field shapes and side
    effect freedom against Nextcloud 34.0.3, Mail 5.11.1 and GreenMail 2.1.12. They say
    nothing about another Mail release: ``specialRole`` is declared as ``int`` **or** ``str``
    in the app, and the value set of this instance is the one GreenMail can produce, which is
    an INBOX and nothing else.
*   **Why field values may be printed here.** Every address of this topology lives under
    ``example.test`` and every body was written by ``scripts/bootstrap_exapp.sh``, so nothing
    printed by this file is anybody's mail. That is the whole difference to the phase 8
    measurement, where a capped ``head`` was a security requirement because the accounts answer
    carried a real IMAP host. What has not changed is the rule underneath it: no header value
    is printed, ever, and :func:`test_no_measured_line_carries_the_app_secret` asserts that the
    protocol carries no ``APP_SECRET`` (T-08-01).
*   **The precondition, and it is a skip and not an assertion.** The six test mails of plan
    10-01 have to be delivered and the account synchronised. When a message is missing, the
    fixture skips with the bootstrap step named, because an account without scaffolding says
    nothing about the connector and a red test would blame the wrong side.
*   **The two account seam of this family is not the one Talk and Tables use.** bob has no
    mail account at all and ``account/list`` answers him 200 with ``[]``, so a test that took
    bob's empty list as the boundary would prove nothing about anybody's mailbox. The negative
    proof needs a mail account for alice and a refusal for bob on **alice's** real account id,
    mailbox id and message id (trap 15 of the phase research). Every one of those refusals is
    additionally asserted to be a refusal of the **instance** and not our own "you forgot the
    account id" sentence, because the two look the same in a test report and prove different
    things.

Run it against the running HaRP topology with GreenMail::

    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_mail_read.py -m integration -q

Add ``-s`` to see the measurement protocol: the number of accounts, the mailboxes with their
roles, the number of envelopes, the text length per test mail, the hit count per filter and
the seen state before and after the full text read. Those numbers are what the summary of plan
10-08 records.
"""

import os
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import mail as mail_client
from mcp_connector.nextcloud.credentials import MODE_APPAPI, Credentials
from mcp_connector.tools import chatgpt
from mcp_connector.tools import mail as mail_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

#: The bootstrap step every skip of this file names. A precondition that is not spelled out
#: turns into "the connector is broken" in somebody's head three weeks later.
BOOTSTRAP = "run bash scripts/bootstrap_exapp.sh against the running topology"

#: The six test mails of plan 10-01, by their subject, in the order the bootstrap delivers
#: them. The subjects are ASCII on purpose where a lookup depends on them: a mailbox that
#: re-encoded a subject would make a lookup fail for a reason that has nothing to do with what
#: is measured here.
TEXT_MAIL = "Gruesse aus Hamburg, die Masse stehen unten"
NEWSLETTER = "Newsletter August"
BIG_NEWSLETTER = "Grosser Newsletter August"
INVOICE = "Rechnung"
INVOICE_MAY = "Rechnung Mai"
ATTACHMENT_ONLY = "Nur ein Anhang"
FIXTURE_SUBJECTS = (
    TEXT_MAIL,
    NEWSLETTER,
    BIG_NEWSLETTER,
    INVOICE,
    INVOICE_MAY,
    ATTACHMENT_ONLY,
)

#: How many envelopes the bootstrap delivers. The plan says "at least five"; six is what is
#: there, and the fixture skips below that rather than measuring a half filled mailbox.
FIXTURE_COUNT = len(FIXTURE_SUBJECTS)

#: The shape ``fetch`` accepts, and the only id form an envelope of this family hands out.
MAIL_ID = re.compile(r"^mail:[0-9]+$")

#: The value set of ``special_role`` this instance can produce, pinned as an assertion rather
#: than left in a document (assumption A1). GreenMail creates an INBOX and nothing else, so
#: ``inbox`` is what is measurable here; the wider set the app declares is read out of its
#: source and stays in the docstring of ``mail_tools._special_role``, where it belongs.
MEASURED_SPECIAL_ROLES = {"inbox"}

#: The raw flag names of an envelope. None of them may appear as a field of a projected
#: envelope: ``unread`` and ``has_attachments`` are derived from two of them, and the other
#: nine are the internals of the Mail frontend.
RAW_FLAG_FIELDS = (
    "seen",
    "flagged",
    "answered",
    "deleted",
    "draft",
    "forwarded",
    "hasAttachments",
    "$mdnsent",
    "important",
    "flags",
)

#: The metadata keys a fetched mail always carries (plan 10-05). The conditional ones
#: (``encrypted``, ``phishing_warning``, ``phishing_checks``, ``mailbox``, ``date``,
#: ``truncated``) are deliberately not in here: a key that appears only when it has something
#: to say cannot be asserted as always present without turning an honest omission into a bug.
ALWAYS_METADATA = ("kind", "sender_trusted", "dkim", "signature")

#: A point in time before every test mail, as Unix seconds. 2001-09-09, chosen so the filter
#: has to compare against the integer column rather than a string that happens to sort right.
EARLY_SECONDS = 1000000000

#: The numeric tag id the bootstrap sets as the IMAP keyword ``$label1`` on one message.
#: ``tags:`` takes the id and not the label, which is a measurement of plan 10-01 that
#: corrected the phase research.
FIRST_TAG = "1"

#: The measurement protocol of one run. A module level memo and not a fixture, because the
#: last test of the file prints it as one block and asserts over all of it at once; a fixture
#: would either rebuild it per test or become a session fixture nobody can read.
_protocol: list[str] = []

#: Every refusal text this run produced, so the negative conditions can be held over all of
#: them in one place instead of being repeated at eleven call sites.
_refusals: list[tuple[str, str, str]] = []


def note(line: str) -> None:
    """Record one measured line. Printed by the protocol test, never a header value."""
    _protocol.append(line)


def refusal(where: str, error: ToolError) -> str:
    """Record one refusal and hold the four conditions every refusal of this run must meet.

    A refusal is an answer a model reads, so the conditions are about what it must **not** be:
    a stack trace hands out the internals of this server, a body that starts with ``<`` is the
    Nextcloud login page rather than an answer, and a text with ``/login`` in it is the same
    thing one indirection later. The fourth condition is positive and it is the one that costs
    a round trip when it is missing: a refusal without a next step is a dead end.
    """
    said = f"{error.message} {error.hint}"
    assert error.hint, f"{where}: a refusal without a next step is a dead end for the model"
    assert error.hint != error.message, f"{where}: the hint only repeats the message: {said!r}"
    assert "Traceback" not in said, f"{where}: the refusal carries a stack trace: {said!r}"
    assert not said.lstrip().startswith("<"), f"{where}: the refusal is markup: {said!r}"
    assert "<html" not in said.casefold(), f"{where}: the refusal is a page: {said!r}"
    assert "/login" not in said, f"{where}: the refusal points at a login page: {said!r}"
    _refusals.append((where, error.message, error.hint))
    return said


def _appapi_clients(exapp_env: dict[str, str], user: str) -> NcClients:
    """Build the impersonating clients for one user, ``APP_SECRET`` as the only credential.

    Mirrors ``deps._credentials_from_appapi``: the same base URL, the same fields, the same
    mode. No Basic scheme is built anywhere in this file and no ``NC_MCP_APP_PASSWORD`` is
    read as a credential source, so the identity can only come from ``AUTHORIZATION-APP-API``
    and a green row cannot be explained by a password that happened to sit in the environment.
    """
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=120.0),
        creds=Credentials(
            base_url=normalize_base_url(exapp_env["base_url"]),
            user=user,
            secret=exapp_env["app_secret"],
            mode=MODE_APPAPI,
            app_id=exapp_env["app_id"],
            app_version=exapp_env["app_version"],
            aa_version=exapp_env["aa_version"],
        ),
    )


@pytest.fixture
async def alice(exapp_env: dict[str, str]) -> AsyncIterator[NcClients]:
    """The account that owns the mail account of this topology."""
    clients = _appapi_clients(exapp_env, exapp_env["alice"])
    async with clients.client:
        yield clients


@pytest.fixture
async def bob(exapp_env: dict[str, str]) -> AsyncIterator[NcClients]:
    """The account that owns no mail account at all; see the module docstring, trap 15."""
    clients = _appapi_clients(exapp_env, exapp_env["bob"])
    async with clients.client:
        yield clients


@pytest.fixture
async def account_id(alice: NcClients) -> str:
    """The id of alice's mail account, or a skip that names the bootstrap step."""
    answer = await mail_tools.browse(alice, level="accounts")
    if not answer["results"]:
        pytest.skip(f"alice has no mail account; {BOOTSTRAP}")
    return str(answer["results"][0]["id"])


@pytest.fixture
async def mailbox_id(alice: NcClients, account_id: str) -> str:
    """The ``databaseId`` of alice's inbox, or a skip that names the bootstrap step."""
    answer = await mail_tools.browse(alice, level="mailboxes", account_id=account_id)
    inbox = next(
        (item for item in answer["results"] if item.get("special_role") == "inbox"),
        None,
    )
    if inbox is None:
        pytest.skip(f"alice's mail account has no inbox; {BOOTSTRAP}")
    return str(inbox["id"])


@pytest.fixture
async def envelopes(alice: NcClients, mailbox_id: str) -> list[dict[str, Any]]:
    """The projected envelopes of alice's inbox, or a skip that names the missing message."""
    answer = await mail_tools.browse(
        alice, level="messages", mailbox_id=mailbox_id, limit=mail_tools.MAX_LIMIT
    )
    subjects = {str(item["subject"]) for item in answer["results"]}
    missing = [wanted for wanted in FIXTURE_SUBJECTS if wanted not in subjects]
    if missing:
        pytest.skip(f"the test mails {missing} are not in alice's inbox; {BOOTSTRAP}")
    if answer["count"] < FIXTURE_COUNT:
        pytest.skip(f"alice's inbox holds {answer['count']} of {FIXTURE_COUNT} mails; {BOOTSTRAP}")
    return list(answer["results"])


def message_id(envelopes: list[dict[str, Any]], subject: str) -> str:
    """The numeric part of the id of one test mail, addressed by its subject."""
    entry = next(item for item in envelopes if str(item["subject"]) == subject)
    return str(entry["id"]).split(":", 1)[1]


async def seen_state(clients: NcClients, mailbox: str, message: str) -> bool:
    """``flags.seen`` of one message, read over the **envelope** route and not the full one.

    Reading the flag through ``fetch`` would measure the operation under test with the
    operation under test: a full message read is exactly what is supposed to leave the state
    alone, so the reading has to happen somewhere else. The envelope route carries the whole
    ``flags`` object and opens no IMAP session for a body, which makes it the cheap and the
    honest place to look.
    """
    raw = await mail_client.get_messages(
        clients.client, clients.creds, mailbox, limit=mail_tools.MAX_LIMIT
    )
    entry = next(item for item in raw if str(item.get("databaseId")) == message)
    flags = entry.get("flags")
    assert isinstance(flags, dict), f"the envelope of {message} carries no flags: {entry!r}"
    return bool(flags.get("seen"))


# --------------------------------------------------------------------------------------
# The three levels
# --------------------------------------------------------------------------------------


async def test_a_user_reads_the_mail_accounts_of_their_own_nextcloud(
    alice: NcClients, account_id: str
) -> None:
    """Level one: at least one account, with an id and an address, and no mail server in it.

    The absent host name is the half of this that is a promise rather than a projection: the
    mail infrastructure of a person is not something a model context needs, and the app does
    publish it on the internal listing route the phase 8 spike measured.
    """
    answer = await mail_tools.browse(alice, level="accounts")

    assert answer["level"] == "accounts"
    assert answer["count"] >= 1, f"alice has no mail account: {answer!r}"
    entry = next(item for item in answer["results"] if str(item["id"]) == account_id)
    assert "@" in str(entry["email"]), f"an account without an address: {entry!r}"
    printed = repr(answer)
    for forbidden in ("greenmail", "imap", "3143", "3025", "password"):
        assert forbidden not in printed.casefold(), (
            f"the accounts answer carries mail infrastructure ({forbidden}): {answer!r}"
        )
    note(f"accounts: {answer['count']} ({[item['email'] for item in answer['results']]})")


async def test_a_user_reads_the_mailboxes_with_their_role_and_their_unread_count(
    alice: NcClients, account_id: str
) -> None:
    """Level two: an inbox with ``special_role`` and a numeric unread counter (MAIL-01).

    The value set of ``special_role`` is pinned here and not only in a document: the app
    declares the field as ``int`` **or** ``str``, and a release that started answering the
    number zero for an inbox would pass every unit test of this project and change what a user
    sees. What this instance can produce is the whole set that is asserted, and the docstring
    of :data:`MEASURED_SPECIAL_ROLES` says why that is not the whole set the app knows.
    """
    answer = await mail_tools.browse(alice, level="mailboxes", account_id=account_id)

    assert answer["level"] == "mailboxes"
    assert answer["count"] >= 1, f"the account has no mailbox: {answer!r}"
    roles = {str(item["special_role"]) for item in answer["results"] if item.get("special_role")}
    assert "inbox" in roles, f"no mailbox of this account is an inbox: {answer!r}"
    assert roles <= MEASURED_SPECIAL_ROLES, (
        f"this instance answered a special role outside the measured set: {roles!r}"
    )
    for item in answer["results"]:
        assert isinstance(item["unread"], int), (
            f"the unread counter of {item['name']!r} is not a number: {item!r}"
        )
        assert not isinstance(item["unread"], bool), (
            f"the unread counter of {item['name']!r} arrived as a flag: {item!r}"
        )
        assert item["unread"] >= 0, f"a negative unread counter: {item!r}"
    inbox = next(item for item in answer["results"] if item.get("special_role") == "inbox")
    rows = [(item["name"], item.get("special_role"), item["unread"]) for item in answer["results"]]
    note(f"mailboxes: {answer['count']} ({rows})")
    note(f"inbox unread before the full text reads: {inbox['unread']}")


async def test_a_user_reads_the_envelopes_with_subject_date_and_preview(
    envelopes: list[dict[str, Any]],
) -> None:
    """Level three: at least five envelopes, addressable, with a preview on at least one.

    The negative half is the one that costs something when it breaks: an envelope must carry
    no raw flag field. ``unread`` and ``has_attachments`` are derived from two of the eleven
    booleans the app sends, and passing the rest on would put nine fields per message into a
    model context for a question nobody asked.
    """
    assert len(envelopes) >= 5, f"fewer than five envelopes: {envelopes!r}"
    for entry in envelopes:
        assert MAIL_ID.fullmatch(str(entry["id"])), f"an id fetch cannot read: {entry!r}"
        assert str(entry["subject"]), f"an envelope without a subject: {entry!r}"
        assert str(entry["date"]).startswith("20"), f"an envelope without a date: {entry!r}"
        assert isinstance(entry["unread"], bool), f"unread is not a flag: {entry!r}"
        for field in RAW_FLAG_FIELDS:
            assert field not in entry, f"the envelope carries the raw flag {field!r}: {entry!r}"

    with_preview = [entry for entry in envelopes if entry.get("preview")]
    assert with_preview, f"not one envelope carries a preview: {envelopes!r}"
    lengths = {str(entry["subject"]): len(str(entry.get("preview", ""))) for entry in envelopes}
    note(f"envelopes: {len(envelopes)}, {len(with_preview)} of them with a preview")
    note(f"preview lengths in characters: {lengths}")


async def test_a_call_without_a_limit_reads_a_window_and_not_one_message(
    alice: NcClients, mailbox_id: str, envelopes: list[dict[str, Any]]
) -> None:
    """The trap of this family, measured where it would hurt (correction K3).

    ``min(100, max(1, null))`` is 1 in PHP 8, so a request without ``limit`` answers exactly
    one message and an inbox with six mails looks almost empty. The client takes ``limit`` as
    a keyword without a default for that reason, and this is the live proof that the default
    of the tool really arrives: more than one message, and never more than the window the tool
    promises.
    """
    answer = await mail_tools.browse(alice, level="messages", mailbox_id=mailbox_id)

    assert answer["count"] > 1, (
        f"a call without limit answered {answer['count']} messages; the app's null limit is 1 "
        f"and it reached the wire"
    )
    assert answer["count"] <= mail_tools.DEFAULT_LIMIT, (
        f"a call without limit answered more than DEFAULT_LIMIT: {answer['count']}"
    )
    assert answer["count"] == len(envelopes), (
        f"the default window and the explicit one disagree: {answer['count']} vs {len(envelopes)}"
    )
    note(
        f"window without limit: {answer['count']} messages "
        f"(DEFAULT_LIMIT={mail_tools.DEFAULT_LIMIT}, MAX_LIMIT={mail_tools.MAX_LIMIT})"
    )


# --------------------------------------------------------------------------------------
# The full text
# --------------------------------------------------------------------------------------


async def test_the_full_text_of_an_html_mail_arrives_as_readable_text(
    alice: NcClients, envelopes: list[dict[str, Any]]
) -> None:
    """A newsletter of realistic size, read as prose and not as markup (MAIL-02, MAIL-03).

    The signals travel in ``metadata`` and every value there is a ``str``, because ``search``
    and ``fetch`` are the only two tools of this server **with** an output schema: a nested
    object would not be a richer answer but a change to the ChatGPT contract.
    """
    answer = await chatgpt.fetch(alice, f"mail:{message_id(envelopes, NEWSLETTER)}")
    text = str(answer["text"])

    assert answer["title"] == NEWSLETTER
    assert len(text) > 1000, f"the newsletter arrived almost empty: {text[:200]!r}"
    assert "\n\n" in text, "the conversion produced no paragraphs at all"
    assert "<" not in text, f"markup survived the conversion: {text[:400]!r}"
    assert ">" not in text, f"markup survived the conversion: {text[:400]!r}"
    for entity in ("&uuml;", "&szlig;", "&amp;", "&lt;", "&gt;", "&nbsp;"):
        assert entity not in text, f"the entity {entity} reached the model: {text[:400]!r}"
    assert "tracking" not in text, "the script element of the newsletter reached the model"

    metadata = answer["metadata"]
    for key in ALWAYS_METADATA:
        assert key in metadata, f"the trust signal {key!r} is missing: {metadata!r}"
    assert all(isinstance(value, str) for value in metadata.values()), (
        f"a metadata value is not a string: {metadata!r}"
    )
    assert "truncated" not in metadata, (
        f"a newsletter of this size was cut; the ceiling is {chatgpt.MAX_MAIL_BYTES} bytes"
    )
    note(
        f"full text {NEWSLETTER!r}: {len(text.encode('utf-8'))} bytes, metadata {sorted(metadata)}"
    )


async def test_the_full_text_of_a_plain_mail_arrives_with_real_umlauts(
    alice: NcClients, envelopes: list[dict[str, Any]]
) -> None:
    """The live proof of correction K2, and it is the correction this family exists on.

    The app runs **every** body through ``convertLinks``, which is ``htmlspecialchars`` plus
    HTMLPurifier, whatever ``hasHtmlBody`` says. A reader that trusted that flag would hand a
    model ``Gr&uuml;&szlig;e`` and a bare ``<a href=...>`` for every plain text mail it ever
    saw. The angle bracket the mail itself carries (``5 < 7``) is expected to survive as a
    character, because it is text the sender wrote and not markup the app added; the assertion
    below is therefore on ``<a `` and not on ``<``.
    """
    answer = await chatgpt.fetch(alice, f"mail:{message_id(envelopes, TEXT_MAIL)}")
    text = str(answer["text"])

    # The two the body of this test mail really carries ("Grüße", "Maße", "Straße", "Büro").
    # Asserting a character the fixture never wrote would fail for a reason that has nothing
    # to do with the conversion, which is the opposite of what this test is for.
    for umlaut in ("ü", "ß"):
        assert umlaut in text, f"the umlaut {umlaut!r} did not survive: {text!r}"
    for entity in ("&uuml;", "&szlig;", "&auml;", "&amp;"):
        assert entity not in text, f"the entity {entity} reached the model: {text!r}"
    assert "<a " not in text, f"a link element reached the model: {text!r}"
    assert "https://example.test/regal" in text, f"the link text was lost: {text!r}"
    assert "5 < 7" in text, f"the sender's own angle bracket was lost: {text!r}"
    note(f"full text {TEXT_MAIL!r}: {len(text.encode('utf-8'))} bytes, umlauts intact")


async def test_a_large_mail_is_cut_at_the_ceiling_and_says_so(
    alice: NcClients, envelopes: list[dict[str, Any]]
) -> None:
    """The 400 KB case: cut at :data:`chatgpt.MAX_MAIL_BYTES` and marked where it was cut.

    The marker is ``FINAL_TRUNCATION`` and not one of the other two, because both of those
    would be untrue here: one sends a model to ``files_read`` with an offset a message does not
    have, the other to ``fetch``, which is the very call that just did the cutting.
    """
    answer = await chatgpt.fetch(alice, f"mail:{message_id(envelopes, BIG_NEWSLETTER)}")
    text = str(answer["text"])
    metadata = answer["metadata"]

    assert metadata["truncated"] == "true", f"the large mail was not marked as cut: {metadata!r}"
    assert text.endswith(chatgpt.FINAL_TRUNCATION), f"the cut is not marked: {text[-200:]!r}"
    body = text[: -len(chatgpt.FINAL_TRUNCATION)]
    assert len(body.encode("utf-8")) <= chatgpt.MAX_MAIL_BYTES + 2, (
        f"the ceiling did not hold: {len(body.encode('utf-8'))} bytes"
    )
    assert text.count(chatgpt.FINAL_TRUNCATION) == 1, "the marker appears more than once"
    note(
        f"full text {BIG_NEWSLETTER!r}: {len(text.encode('utf-8'))} bytes, "
        f"cut at {chatgpt.MAX_MAIL_BYTES}, marker at the end"
    )


async def test_a_mail_without_a_text_body_is_refused_with_a_sentence(
    alice: NcClients, envelopes: list[dict[str, Any]]
) -> None:
    """The attachment-only mail: a refusal, not an empty success (threat T-10-34).

    A successful answer without content is the shape that invites a model to fill the gap
    itself, which is why the reader raises here instead of answering an empty string.
    """
    with pytest.raises(ToolError) as error:
        await chatgpt.fetch(alice, f"mail:{message_id(envelopes, ATTACHMENT_ONLY)}")

    said = refusal("fetch of the attachment-only mail", error.value)
    assert "attachment" in said.casefold(), f"the refusal does not name the reason: {said!r}"
    note(f"full text {ATTACHMENT_ONLY!r}: refused, {error.value.message!r}")


async def test_reading_a_mail_in_full_leaves_its_seen_state_alone(
    alice: NcClients, mailbox_id: str, envelopes: list[dict[str, Any]]
) -> None:
    """Success criterion "reading changes nothing", measured and not assumed.

    This is a property of the **version** and not of the protocol: ``MessageMapper`` reads with
    ``peek => true``, and nothing in the OCS request says so. A Mail release that dropped that
    flag would turn every read of this connector into a write on somebody's mailbox, and no
    unit test of ours could see it, because the parameter is not ours to send. That is exactly
    the kind of promise that belongs in a live measurement.

    Both numbers are read over the envelope route (see :func:`seen_state`), so the measurement
    itself opens no IMAP session for a body and cannot be the thing that changes the state.
    """
    target = message_id(envelopes, INVOICE)
    before = await seen_state(alice, mailbox_id, target)
    assert not before, (
        f"the message {target} was already read before this test; {BOOTSTRAP} on a fresh topology"
    )

    answer = await chatgpt.fetch(alice, f"mail:{target}")
    assert str(answer["text"]), "the read that is supposed to change nothing returned nothing"

    after = await seen_state(alice, mailbox_id, target)
    assert after == before, (
        f"reading the mail {target} in full set its seen flag: {before} -> {after}"
    )
    note(f"seen state of mail:{target} before the full text read: {before}")
    note(f"seen state of mail:{target} after the full text read: {after}")


# --------------------------------------------------------------------------------------
# The filter grammar
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        ("is:unread", 6),
        ("from:buchhaltung", 2),
        ("subject:Rechnung", 2),
        ("subject:Rechnung%20Mai", 1),
        (f"start:{EARLY_SECONDS}", 6),
        (f"tags:{FIRST_TAG}", 1),
    ],
)
async def test_a_documented_filter_really_filters(
    alice: NcClients,
    mailbox_id: str,
    envelopes: list[dict[str, Any]],
    condition: str,
    expected: int,
) -> None:
    """Each documented filter type against the six delivered mails, with its own hit count.

    ``subject:Rechnung%20Mai`` is the case that carries the grammar: the app splits the filter
    on spaces and every token at its first colon, so the percent encoding is not a nicety but
    the only spelling that filters on both words. ``tags:`` takes the numeric tag id and not
    the IMAP label, which is where plan 10-01 corrected the research.
    """
    answer = await mail_tools.browse(
        alice,
        level="messages",
        mailbox_id=mailbox_id,
        limit=mail_tools.MAX_LIMIT,
        filter=condition,
    )

    assert answer["count"] == expected, (
        f"the filter {condition!r} matched {answer['count']} of {len(envelopes)} messages, "
        f"expected {expected}"
    )
    note(f"filter {condition!r}: {answer['count']} of {len(envelopes)}")


async def test_the_narrowing_filters_do_not_answer_the_unfiltered_list(
    alice: NcClients, mailbox_id: str, envelopes: list[dict[str, Any]]
) -> None:
    """The control the parametrised run above cannot give on its own.

    ``is:unread`` and ``start:`` legitimately match every one of the six messages, so their
    hit count alone cannot tell a working filter from a silently dropped one. The three
    narrowing conditions can, and that is what makes the whole set proof rather than
    coincidence: a parser that dropped what it did not understand would answer six every time.
    """
    baseline = len(envelopes)
    counts: dict[str, int] = {}
    for condition in ("from:buchhaltung", "subject:Rechnung%20Mai", f"tags:{FIRST_TAG}"):
        answer = await mail_tools.browse(
            alice,
            level="messages",
            mailbox_id=mailbox_id,
            limit=mail_tools.MAX_LIMIT,
            filter=condition,
        )
        counts[condition] = int(answer["count"])

    assert all(count < baseline for count in counts.values()), (
        f"a narrowing filter answered the unfiltered list of {baseline}: {counts!r}"
    )
    note(f"narrowing filters against a baseline of {baseline}: {counts}")


@pytest.mark.parametrize(
    ("condition", "why"),
    [
        ("is:ungelesen", "a typo the app would drop in silence, answering the unfiltered list"),
        ("subject:", "an empty value the app would apply to the empty string"),
        ("start:2026-08-01", "an ISO date compared against the integer column sent_at"),
    ],
)
async def test_a_filter_the_app_would_swallow_is_refused_here(
    alice: NcClients, mailbox_id: str, condition: str, why: str
) -> None:
    """The three refusals that replace a right looking answer with a sentence (trap 3).

    Every one of them was measured against this instance in plan 10-01 and none of them
    produces an error in the app: ``is:ungelesen`` answered all six messages, ``start:`` with
    an ISO date answered none of them, and neither said why. A model cannot tell either answer
    from a correct one, so the refusal has to happen here, before the request.
    """
    with pytest.raises(ToolError) as error:
        await mail_tools.browse(
            alice,
            level="messages",
            mailbox_id=mailbox_id,
            limit=mail_tools.MAX_LIMIT,
            filter=condition,
        )

    said = refusal(f"filter {condition!r}", error.value)
    assert condition.split(":")[0] in said or condition.split(":")[-1] in said, (
        f"the refusal of {condition!r} names neither the type nor the value: {said!r}"
    )
    note(f"filter {condition!r}: refused ({why})")


# --------------------------------------------------------------------------------------
# The two account boundary, on the seam this family really has (trap 15)
# --------------------------------------------------------------------------------------


async def test_the_second_account_owns_no_mail_account_and_that_is_a_success(
    bob: NcClients, exapp_env: dict[str, str]
) -> None:
    """The precondition of the boundary below, and the reason it needs its own shape.

    Zero accounts is a **success** with zero results and explicitly not the statement "the Mail
    app is missing": one of them is answered by setting up an account, the other by asking an
    administrator, and a test that confused the two would pass while proving nothing.
    """
    assert exapp_env["alice"] != exapp_env["bob"], (
        "the negative proof needs two accounts; NC_MCP_TEST_USER2 points at the same user"
    )
    answer = await mail_tools.browse(bob, level="accounts")

    assert answer["count"] == 0, f"bob unexpectedly owns a mail account: {answer!r}"
    assert answer["results"] == []
    note(f"bob's own accounts: {answer['count']} (a success, not an error)")


async def test_the_second_account_reaches_neither_mailbox_nor_message_nor_full_text(
    bob: NcClients,
    account_id: str,
    mailbox_id: str,
    envelopes: list[dict[str, Any]],
) -> None:
    """The boundary, with alice's **real** ids and three separate ways in.

    The ids are the real ones rather than invented, which is what makes this a measurement of
    the instance instead of a measurement of our own shape guards. And every refusal is
    asserted to be a refusal of the instance: our own "you forgot the account id" and "you
    forgot the mailbox id" sentences would look identical in a test report and would prove
    nothing at all about anybody's mailbox (trap 15).
    """
    target = message_id(envelopes, TEXT_MAIL)
    subject = TEXT_MAIL
    preview = str(next(item for item in envelopes if item["subject"] == subject).get("preview", ""))

    with pytest.raises(ToolError) as mailbox_error:
        await mail_tools.browse(bob, level="mailboxes", account_id=account_id)
    with pytest.raises(ToolError) as message_error:
        await mail_tools.browse(
            bob, level="messages", mailbox_id=mailbox_id, limit=mail_tools.MAX_LIMIT
        )
    with pytest.raises(ToolError) as fetch_error:
        await chatgpt.fetch(bob, f"mail:{target}")

    for where, error in (
        (f"bob on alice's account {account_id}", mailbox_error.value),
        (f"bob on alice's mailbox {mailbox_id}", message_error.value),
        (f"bob on alice's mail {target}", fetch_error.value),
    ):
        said = refusal(where, error)
        assert error.hint != mail_tools._ACCOUNT_HINT, (
            f"{where}: this is our own missing-account-id refusal and says nothing about the "
            f"boundary: {said!r}"
        )
        assert error.hint != mail_tools._MAILBOX_HINT, (
            f"{where}: this is our own missing-mailbox-id refusal: {said!r}"
        )
        assert "no mail account" not in said.casefold(), (
            f"{where}: the refusal is about bob's missing account and not about the boundary: "
            f"{said!r}"
        )
        assert subject not in said, f"{where}: the refusal carried alice's subject: {said!r}"
        if preview:
            assert preview[:40] not in said, f"{where}: the refusal carried alice's text"
        note(f"bob refused at {where}: {error.message!r}")


# --------------------------------------------------------------------------------------
# The protocol, and the two conditions held over the whole run
# --------------------------------------------------------------------------------------


async def test_every_refusal_of_this_run_is_a_sentence_with_a_next_step() -> None:
    """The negative conditions of the whole file, in one place and over every refusal.

    :func:`refusal` already holds them at each call site; this test is what makes the set
    itself visible and what fails when a future change stops routing refusals through that
    helper. A run that produced no refusal at all is a run in which the boundary tests were
    skipped, so an empty list is a skip and not a pass.
    """
    if not _refusals:
        pytest.skip("no refusal was measured in this run; the boundary tests did not run")

    for where, message, hint in _refusals:
        said = f"{message} {hint}"
        assert "Traceback" not in said, f"{where}: stack trace"
        assert not said.lstrip().startswith("<"), f"{where}: markup"
        assert "/login" not in said, f"{where}: login page"
        assert hint.strip(), f"{where}: no next step"
    print(f"\n{len(_refusals)} refusals, each a sentence with a next step:")
    for where, message, hint in _refusals:
        print(f"  {where}: {message} | {hint[:70]}")


async def test_no_measured_line_carries_the_app_secret(exapp_env: dict[str, str]) -> None:
    """T-08-01, held over the protocol this file prints rather than promised in a comment.

    Field values of these mails may be printed, because every address lives under
    ``example.test`` and every body was written by the bootstrap. A header value may not, and
    ``APP_SECRET`` is the one that would matter: it is the whole credential of this topology.
    """
    if not _protocol:
        pytest.skip("nothing was measured in this run")

    blob = "\n".join(_protocol) + "\n".join(f"{a}{b}{c}" for a, b, c in _refusals)
    secret = exapp_env["app_secret"]
    assert secret, "the fixture handed out an empty APP_SECRET"
    assert secret not in blob, "the measurement protocol carries the app secret"
    assert "AUTHORIZATION-APP-API" not in blob, "the protocol carries an auth header name"
    assert os.environ.get("NC_MCP_TEST_APP_PASSWORD", "\0") not in blob, (
        "the protocol carries an app password"
    )


async def test_the_measurement_protocol_of_this_run(
    alice: NcClients, account_id: str, mailbox_id: str
) -> None:
    """Print what was measured. Run the file with ``-s`` to see it.

    The inbox counter is read once more at the end on purpose: it is the number that would
    have moved if any read of this run had been a write, and it is the last line of the
    protocol for exactly that reason.
    """
    answer = await mail_tools.browse(alice, level="mailboxes", account_id=account_id)
    inbox = next(item for item in answer["results"] if str(item["id"]) == mailbox_id)
    note(f"inbox unread after the whole run: {inbox['unread']}")

    print("\n--- mail read, measured ---")
    for line in _protocol:
        print(f"  {line}")
    assert _protocol, "nothing was measured"
