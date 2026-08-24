"""Unit tests for the one Mail tool, all three levels and every refusal.

The field values of the fixtures below are not invented. They come from the stage 2 protocol
of plan 10-01, which read them off a live Nextcloud 34 with Mail 5.11.1 and GreenMail behind
it: ``specialRole`` arrives as the string ``inbox`` and not as a number, ``previewText`` is
cut by the app itself at about 250 characters and is an empty string rather than ``null`` for
a mail without a text body, and a message list carries ``databaseId``, ``uid``, ``remoteId``
and ``messageId`` side by side, of which exactly one is the number this server may hand on.

The most expensive property of this family is a **refusal**, and it is the reason this file
has more rejection tests than happy paths. The parser of the Mail app drops a filter token it
does not know without a word: ``is:ungelesen`` was measured against the same six messages as
no filter at all and answered with all six. That is an answer which looks right and is wrong,
and a model cannot see the difference, so every one of those tokens ends here with a
``ToolError`` and a route call count of zero.
"""

import json
from typing import Any

import httpx
import pytest
import respx

from mcp_connector import paging
from mcp_connector.errors import AppMissingError, ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import mail as mail_tools
from mcp_connector.tools import marks

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

ACCOUNT_ID = 4
MAILBOX_ID = 7
MESSAGE_ID = 4711

CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"
NAVIGATION_URL = f"{BASE}/ocs/v2.php/core/navigation/apps"

# The frozen literals again, one layer up. The tool must not be able to move a route by
# accident either, and not one of them carries an ``api`` segment.
MAIL_PREFIX = f"{BASE}/ocs/v2.php/apps/mail"
ACCOUNTS_URL = f"{MAIL_PREFIX}/account/list"
MAILBOXES_URL = f"{MAIL_PREFIX}/ocs/mailboxes"
MESSAGES_URL = f"{MAILBOXES_URL}/{MAILBOX_ID}/messages"


def envelope(data: Any, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    capabilities.clear_cache()


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def mock_mail_app(mock: respx.MockRouter, *, present: bool = True) -> None:
    """Both halves of the Mail detection: the capabilities and the navigation of the user.

    Mail publishes no capabilities section at all, so the second request is the answer, and it
    is the one that decides between "there" and "not there".
    """
    mock.get(CAPABILITIES_URL).mock(
        return_value=httpx.Response(200, json=envelope({"capabilities": {"core": {}}}))
    )
    entries: list[dict[str, Any]] = [{"id": "files", "app": "files", "type": "link"}]
    if present:
        entries.append({"id": "mail", "app": "mail", "type": "link"})
    mock.get(NAVIGATION_URL).mock(return_value=httpx.Response(200, json=envelope(entries)))


def mail_routes(mock: respx.MockRouter) -> respx.Route:
    """A catch-all over the whole Mail prefix, to assert that nothing was requested."""
    return mock.route(url__startswith=MAIL_PREFIX)


#: Two accounts as the app answers them: four fields, no account name and no IMAP host.
ACCOUNTS = [
    {"id": ACCOUNT_ID, "email": "alice@nc.test", "isDelegated": False, "aliases": []},
    {
        "id": 9,
        "email": "alice@behoerde.example",
        "isDelegated": True,
        "aliases": [{"id": 1, "email": "buero@behoerde.example", "name": "Büro"}],
    },
]


def mailbox(**overrides: Any) -> dict[str, Any]:
    """One mailbox with every field the app sends, so the projection provably throws away.

    ``id`` and ``databaseId`` stand here side by side on purpose: ``id`` is base64 of the IMAP
    name and belongs to the Mail frontend, ``databaseId`` is the number every other route of
    this family expects, and confusing the two is the most expensive mistake in this family
    (trap 10 of the phase research).
    """
    template: dict[str, Any] = {
        "accountId": ACCOUNT_ID,
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
    return {**template, **overrides}


#: Four mailboxes: three with a role and one that has none, which is the ``0`` branch.
MAILBOXES = [
    mailbox(),
    mailbox(databaseId=8, name="INBOX.Sent", displayName="INBOX.Sent", specialRole="sent"),
    mailbox(databaseId=9, name="INBOX.Drafts", displayName="INBOX.Drafts", specialRole="drafts"),
    mailbox(
        databaseId=10,
        name="INBOX.Projekte",
        displayName="INBOX.Projekte",
        specialRole=0,
        specialUse=[],
        unread=0,
    ),
]


def message(**overrides: Any) -> dict[str, Any]:
    """One envelope with the ballast the projection has to drop, including all four numbers."""
    template: dict[str, Any] = {
        "databaseId": MESSAGE_ID,
        "uid": 12,
        "remoteId": 12,
        "messageId": "<abc@nc.test>",
        "threadRootId": "<abc@nc.test>",
        "inReplyTo": None,
        "references": [],
        "mailboxId": MAILBOX_ID,
        "subject": "Maße geprüft und übergeben",
        "previewText": "Grüße aus der Werkstatt, die Maße stimmen.",
        "dateInt": 1755181000,
        "flags": {
            "seen": False,
            "flagged": False,
            "answered": False,
            "deleted": False,
            "draft": False,
            "forwarded": False,
            "hasAttachments": True,
            "important": False,
            "$junk": False,
            "$notjunk": True,
            "$mdnsent": False,
        },
        "from": [{"label": "Bob Beispiel", "email": "bob@nc.test"}],
        "to": [{"label": "Alice Beispiel", "email": "alice@nc.test"}],
        "cc": [],
        "bcc": [],
        "tags": {},
        "summary": "Eine von einem Modell erzeugte Zusammenfassung",
        "mentionsMe": False,
        "encrypted": False,
        "imipMessage": False,
        "avatar": None,
        "fetchAvatarFromClient": False,
        "attachments": [],
    }
    return {**template, **overrides}


async def browse_messages(
    clients: NcClients, mock: respx.MockRouter, payload: list[dict[str, Any]], **kwargs: Any
) -> tuple[dict[str, Any], respx.Route]:
    """The message level against one mocked window, for the many small assertions below."""
    mock_mail_app(mock)
    route = mock.get(MESSAGES_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
    answer = await mail_tools.browse(
        clients, level="messages", mailbox_id=str(MAILBOX_ID), **kwargs
    )
    return answer, route


# --- the level itself ------------------------------------------------------------------


@pytest.mark.anyio
async def test_an_unknown_level_is_refused_and_the_hint_names_all_three(
    clients: NcClients,
) -> None:
    """The schema rejects it first; the function stays honest when called directly."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(clients, level="folders")

    assert calls.call_count == 0
    for level in mail_tools.LEVELS:
        assert level in excinfo.value.hint


@pytest.mark.anyio
async def test_a_missing_mail_app_stops_the_tool_before_the_first_mail_request(
    clients: NcClients,
) -> None:
    """SRV-04: the sentence of ``_MISSING["mail"]``, and a Mail route count of zero."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock, present=False)
        calls = mail_routes(mock)

        with pytest.raises(AppMissingError) as excinfo:
            await mail_tools.browse(clients)

    assert calls.call_count == 0, "no request may go to an app that is not available"
    assert excinfo.value.message == "The Mail app is not available on this Nextcloud."
    assert excinfo.value.hint == "Ask an administrator to enable the Mail app for this account."


# --- level accounts --------------------------------------------------------------------


@pytest.mark.anyio
async def test_the_account_level_projects_both_accounts_and_carries_no_hostname(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(ACCOUNTS_URL).mock(return_value=httpx.Response(200, json=envelope(ACCOUNTS)))
        answer = await mail_tools.browse(clients, level="accounts")

    assert answer["level"] == "accounts"
    assert answer["count"] == 2
    assert answer["results"][0] == {"id": ACCOUNT_ID, "email": "alice@nc.test"}
    assert answer["results"][1] == {
        "id": 9,
        "email": "alice@behoerde.example",
        "delegated": True,
        "aliases": 1,
    }
    assert "imap" not in json.dumps(answer).casefold(), "mail infrastructure is not a tool answer"


@pytest.mark.anyio
async def test_an_empty_account_list_is_a_success_with_zero_accounts(clients: NcClients) -> None:
    """A user without a mail account is answered, not refused: the next step differs.

    "Set up an account in the Mail app" and "ask an administrator to enable the Mail app" are
    two different sentences, so the two cases must stay distinguishable in the answer.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(ACCOUNTS_URL).mock(return_value=httpx.Response(200, json=envelope([])))
        answer = await mail_tools.browse(clients, level="accounts")

    assert answer == {"level": "accounts", "count": 0, "results": []}


# --- level mailboxes -------------------------------------------------------------------


@pytest.mark.anyio
async def test_the_mailbox_level_without_an_account_id_refuses_instead_of_guessing_one(
    clients: NcClients,
) -> None:
    """A7: no default and no "first account". A guessed account looks right and is not."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(clients, level="mailboxes")

    assert calls.call_count == 0
    assert "account_id" in excinfo.value.message
    assert "level=accounts" in excinfo.value.hint


@pytest.mark.anyio
async def test_three_mailboxes_carry_a_special_role_and_the_fourth_carries_none(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(MAILBOXES)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    results = answer["results"]
    assert [entry.get("special_role") for entry in results] == ["inbox", "sent", "drafts", None]
    assert results[0] == {
        "id": MAILBOX_ID,
        "name": "INBOX",
        "unread": 6,
        "delimiter": ".",
        "special_role": "inbox",
    }


@pytest.mark.anyio
async def test_a_cut_mailbox_list_names_the_larger_limit_as_the_way_out(
    clients: NcClients,
) -> None:
    """The mailbox level hands out no cursor, so a cut below the ceiling has to say how to
    see the rest: raise the limit (review finding WR-03). A bare truncated flag on a level
    without a continuation reads like "cut, for good"."""
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(MAILBOXES)))
        answer = await mail_tools.browse(
            clients, level="mailboxes", account_id=str(ACCOUNT_ID), limit=2
        )

    assert answer["count"] == 2
    assert answer["truncated"] is True
    assert "next" not in answer, "this level hands out no cursor, and that stays true"
    assert "limit" in answer["note"]
    assert str(mail_tools.MAX_LIMIT) in answer["note"]


@pytest.mark.anyio
async def test_a_mailbox_list_cut_at_the_ceiling_says_the_rest_is_out_of_reach(
    clients: NcClients,
) -> None:
    """At the ceiling a larger limit is no way out any more, and inventing a cursor level
    is not this fix; the honest sentence is that the remaining entries are not reachable
    through this tool (review finding WR-03)."""
    crowd = [mailbox(databaseId=100 + n, name=f"INBOX.Ordner{n}") for n in range(60)]
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(crowd)))
        answer = await mail_tools.browse(
            clients, level="mailboxes", account_id=str(ACCOUNT_ID), limit=mail_tools.MAX_LIMIT
        )

    assert answer["count"] == mail_tools.MAX_LIMIT
    assert answer["truncated"] is True
    assert "next" not in answer
    assert "not reachable" in answer["note"]


@pytest.mark.anyio
async def test_a_mailbox_list_below_the_limit_carries_neither_truncation_nor_note(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(MAILBOXES)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert "truncated" not in answer
    assert "note" not in answer


@pytest.mark.anyio
async def test_the_number_zero_is_read_as_no_role_and_a_string_comes_through_lower_case(
    clients: NcClients,
) -> None:
    """The app declares ``specialRole`` as int **or** str; both spellings arrive here."""
    payload = [mailbox(specialRole=0), mailbox(databaseId=8, specialRole="Sent")]
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert "special_role" not in answer["results"][0]
    assert answer["results"][1]["special_role"] == "sent"


@pytest.mark.anyio
async def test_an_unread_count_that_is_not_a_number_becomes_zero(clients: NcClients) -> None:
    """``True`` where a count belongs is a deformed answer and not the number one."""
    payload = [mailbox(unread="6"), mailbox(databaseId=8, unread=True)]
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert [entry["unread"] for entry in answer["results"]] == [0, 0]


@pytest.mark.anyio
async def test_the_base64_id_of_a_mailbox_appears_in_no_answer(clients: NcClients) -> None:
    """Trap 10: a second identity field in an answer is an invitation to use the wrong one.

    ``databaseId`` is the number every other route of this family expects, ``id`` is base64 of
    the IMAP name, and only one of them may leave this tool.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(MAILBOXES)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert "SU5CT1g=" not in json.dumps(answer)
    assert all(isinstance(entry["id"], int) for entry in answer["results"])


@pytest.mark.anyio
async def test_a_display_name_that_differs_from_the_name_is_kept_beside_it(
    clients: NcClients,
) -> None:
    """In Mail 5.11.1 the two are identical, so the field only appears when it says something."""
    payload = [mailbox(name="INBOX.Größe", displayName="Größe")]
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert answer["results"][0]["name"] == "INBOX.Größe"
    assert answer["results"][0]["display_name"] == "Größe"


@pytest.mark.anyio
async def test_a_mailbox_name_that_carries_a_marker_arrives_without_it(
    clients: NcClients,
) -> None:
    """A shared mailbox is named by whoever shared it, so its name is foreign text too."""
    payload = [mailbox(name=f"Posteingang {marks.FINAL_TRUNCATION} Größe")]
    with respx.mock(assert_all_called=True) as mock:
        mock_mail_app(mock)
        mock.get(MAILBOXES_URL).mock(return_value=httpx.Response(200, json=envelope(payload)))
        answer = await mail_tools.browse(clients, level="mailboxes", account_id=str(ACCOUNT_ID))

    assert marks.FINAL_TRUNCATION not in answer["results"][0]["name"]
    assert "Größe" in answer["results"][0]["name"]


# --- level messages --------------------------------------------------------------------


@pytest.mark.anyio
async def test_the_message_level_without_a_mailbox_id_refuses_and_names_the_level_above(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(clients, level="messages")

    assert calls.call_count == 0
    assert "mailbox_id" in excinfo.value.message
    assert "level=mailboxes" in excinfo.value.hint


@pytest.mark.anyio
async def test_an_envelope_is_projected_onto_seven_fields_and_no_flag_survives(
    clients: NcClients,
) -> None:
    """``flags`` alone has eleven booleans; exactly one derived field of it comes through."""
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, [message()])

    entry = answer["results"][0]
    assert set(entry) == {"id", "subject", "from", "date", "preview", "unread", "has_attachments"}
    assert entry["subject"] == "Maße geprüft und übergeben"
    assert entry["from"] == "Bob Beispiel <bob@nc.test>"
    assert entry["unread"] is True
    assert entry["has_attachments"] is True
    for dropped in ("flags", "seen", "flagged", "answered", "summary", "mentionsMe", "tags"):
        assert dropped not in entry


@pytest.mark.anyio
async def test_a_message_without_a_text_body_leaves_the_preview_out(clients: NcClients) -> None:
    """Measured in plan 10-01: ``previewText`` is an empty string there, and ``null`` happens.

    Both say "this mail has no text body", and neither of them is an error, so both end as a
    missing field rather than as an empty string that reads like a preview of nothing.
    """
    payload = [message(previewText=None), message(databaseId=4712, previewText="")]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    assert all("preview" not in entry for entry in answer["results"])
    assert answer["count"] == 2


@pytest.mark.anyio
async def test_a_preview_over_the_byte_cap_is_cut_and_says_so_beside_the_text(
    clients: NcClients,
) -> None:
    """ME-03: the cut is a field next to the text and never a marker inside it."""
    payload = [message(previewText="ü" * mail_tools.MAX_PREVIEW_BYTES)]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    entry = answer["results"][0]
    assert entry["preview_truncated"] is True
    assert "truncated" not in entry, "the entry level flag is the preview one, never the page one"
    assert len(entry["preview"].encode("utf-8")) <= mail_tools.MAX_PREVIEW_BYTES
    for marker in (marks.FINAL_TRUNCATION, marks.EXCERPT_TRUNCATION):
        assert marker not in entry["preview"]
    assert "[" not in entry["preview"], "a cut preview carries no bracketed note of any kind"


@pytest.mark.anyio
async def test_a_cut_page_and_a_cut_preview_are_two_keys_with_two_meanings(
    clients: NcClients,
) -> None:
    """IN-01: the case that made one word for two cuts a problem, in one single answer.

    Both flags are set here at the same time and neither of them can be derived from the
    other: the **page** was cut, so there is a ``next`` to continue with, and the **preview**
    of one entry was cut at :data:`mail_tools.MAX_PREVIEW_BYTES`, which no cursor continues
    because the full text of a mail is one ``fetch`` away and not one page further. While both
    were called ``truncated``, a model reading the entry level flag as a page flag paged in a
    circle, and the hint of this family (``_CURSOR_HINT``) told it exactly that reading.
    """
    payload = [
        message(previewText="ü" * mail_tools.MAX_PREVIEW_BYTES),
        message(databaseId=4712, dateInt=1755180000, previewText="Kurz und vollständig."),
    ]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload, limit=2)

    assert answer["truncated"] is True, "the page was cut"
    assert paging.decode_cursor(answer["next"]) == {"o": 1755180000, "m": str(MAILBOX_ID)}
    assert "preview_truncated" not in answer, "the page flag is never the preview one"

    cut, whole = answer["results"]
    assert cut["preview_truncated"] is True, "the preview of the first entry was cut"
    assert "next" not in cut, "a cut preview has no continuation, the full text is a fetch away"
    assert "truncated" not in cut
    assert "preview_truncated" not in whole, "an uncut preview says nothing at all"


@pytest.mark.anyio
async def test_the_date_is_an_iso_timestamp_built_from_dateint(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, [message()])

    assert answer["results"][0]["date"] == "2025-08-14T14:16:40+00:00"


@pytest.mark.anyio
async def test_a_message_without_a_usable_date_keeps_the_field_out(clients: NcClients) -> None:
    """A number the standard library cannot turn into a moment is answered with nothing."""
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, [message(dateInt=0)])

    assert "date" not in answer["results"][0]


@pytest.mark.anyio
async def test_the_id_is_built_from_databaseid_and_from_none_of_the_other_numbers(
    clients: NcClients,
) -> None:
    """A message carries ``databaseId``, ``uid``, ``remoteId`` and ``messageId``, and only the
    first of them is the number ``fetch`` can resolve (trap 10)."""
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, [message()])

    assert answer["results"][0]["id"] == "mail:4711"
    assert "12" not in answer["results"][0]["id"], "uid is not the id of a message"
    assert "<abc@nc.test>" not in json.dumps(answer)


@pytest.mark.anyio
async def test_an_envelope_without_a_database_id_is_left_out_of_the_list(
    clients: NcClients,
) -> None:
    """Being addressable is what this level exists for, so an unaddressable entry drops out."""
    payload = [message(databaseId=None), message(databaseId=4712)]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    assert answer["count"] == 1
    assert answer["results"][0]["id"] == "mail:4712"


@pytest.mark.anyio
@pytest.mark.parametrize(("asked", "sent"), [(500, "50"), (0, "1"), (-5, "1"), (20, "20")])
async def test_the_window_is_capped_between_one_and_the_maximum(
    clients: NcClients, asked: int, sent: str
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        _, route = await browse_messages(clients, mock, [message()], limit=asked)

    assert route.calls.last.request.url.params["limit"] == sent


@pytest.mark.anyio
async def test_a_window_that_did_not_fill_up_carries_no_truncation(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(
            clients, mock, [message(), message(databaseId=4712)], limit=20
        )

    assert "truncated" not in answer
    assert "next" not in answer


# --- the filter grammar ----------------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.parametrize(
    "wanted",
    [
        "is:unread",
        "not:unread",
        "from:buchhaltung",
        "subject:Rechnung%20Mai",
        "tags:1",
        "start:1756000000",
        "end:1787575636",
        "is:unread from:buchhaltung subject:Rechnung",
    ],
)
async def test_every_allowed_filter_type_reaches_the_app_unchanged(
    clients: NcClients, wanted: str
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        _, route = await browse_messages(clients, mock, [message()], filter=wanted)

    assert route.calls.last.request.url.params["filter"] == wanted


@pytest.mark.anyio
async def test_a_misspelled_state_is_refused_with_the_states_that_work(
    clients: NcClients,
) -> None:
    """The measured case: ``is:ungelesen`` answered with all six messages, like no filter.

    That is the answer this whole positive list exists against, because a model reading it
    cannot tell it from a correctly filtered one.
    """
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter="is:ungelesen"
            )

    assert calls.call_count == 0
    assert "unread" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("wanted", "expected"),
    [
        ("foo:bar", "foo"),
        ("body:Rechnung", "body"),
        ("match:Rechnung", "match"),
        ("mentions:true", "mentions"),
    ],
)
async def test_an_unknown_filter_type_is_refused_and_the_hint_names_the_allowed_ones(
    clients: NcClients, wanted: str, expected: str
) -> None:
    """The full text search of the app is among them: it leaves the database and asks IMAP."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter=wanted
            )

    assert calls.call_count == 0
    assert expected in excinfo.value.message
    for allowed in mail_tools.FILTER_TYPES:
        assert allowed in excinfo.value.hint


@pytest.mark.anyio
async def test_a_token_without_a_colon_is_refused_instead_of_being_dropped(
    clients: NcClients,
) -> None:
    """The app splits on spaces, so ``subject:Rechnung Mai`` loses its second word in silence."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter="subject:Rechnung Mai"
            )

    assert calls.call_count == 0
    assert "colon" in excinfo.value.message
    assert "percent encoded" in excinfo.value.hint


@pytest.mark.anyio
async def test_a_filter_condition_without_a_value_is_refused(clients: NcClients) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter="subject:"
            )

    assert calls.call_count == 0
    assert "no value" in excinfo.value.message


@pytest.mark.anyio
@pytest.mark.parametrize(
    "wanted",
    ["start:2026-08-01", "start:2026-08-01T10:00:00Z", "end:2026-08-01", "start:gestern"],
)
async def test_an_iso_date_on_a_time_filter_is_refused_with_unix_seconds_in_the_hint(
    clients: NcClients, wanted: str
) -> None:
    """Measured: ``start:2026-08-01`` filtered all six messages away instead of failing.

    The app compares the value against the integer column ``sent_at``, and a timestamp with a
    time of day would be cut at its first colon on top of that.
    """
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter=wanted
            )

    assert calls.call_count == 0
    assert "Unix" in excinfo.value.hint
    assert "sent_at" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("wanted", ["is:is_important", "is:pi-important", "is:pi-other"])
async def test_the_undocumented_importance_filters_are_refused(
    clients: NcClients, wanted: str
) -> None:
    """This connector does not pass on a filter it cannot describe in one sentence."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError):
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), filter=wanted
            )

    assert calls.call_count == 0


@pytest.mark.anyio
@pytest.mark.parametrize("level", ["accounts", "mailboxes"])
async def test_a_filter_on_a_level_that_reads_no_messages_is_refused_not_ignored(
    clients: NcClients, level: str
) -> None:
    """An ignored parameter answers as if it had been applied, which is the same wrong answer."""
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level=level, account_id=str(ACCOUNT_ID), filter="is:unread"
            )

    assert calls.call_count == 0
    assert "level=messages" in excinfo.value.hint


@pytest.mark.anyio
@pytest.mark.parametrize("wanted", ["", "   ", None])
async def test_an_empty_filter_never_appears_in_the_url(
    clients: NcClients, wanted: str | None
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        _, route = await browse_messages(clients, mock, [message()], filter=wanted)

    assert "filter" not in route.calls.last.request.url.params


# --- the cursor ------------------------------------------------------------------------


@pytest.mark.anyio
async def test_a_full_window_hands_out_a_handle_with_the_oldest_date_of_the_page(
    clients: NcClients,
) -> None:
    payload = [message(), message(databaseId=4712, dateInt=1755180000)]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload, limit=2)

    assert answer["truncated"] is True
    assert paging.decode_cursor(answer["next"]) == {"o": 1755180000, "m": str(MAILBOX_ID)}


@pytest.mark.anyio
async def test_one_deformed_date_does_not_suppress_the_handle_of_a_full_window(
    clients: NcClients,
) -> None:
    """A single envelope without a usable ``dateInt`` must not swallow the continuation.

    ``_number`` reads a missing, boolean or non integer date as 0, and a minimum over all
    envelopes would let that one zero suppress ``next`` on a full page: truncated without a
    way to continue, and the rest of the mailbox silently unreachable (review finding
    WR-02). The cursor has to be the oldest *valid* timestamp of the page instead.
    """
    payload = [
        message(),
        message(databaseId=4712, dateInt=1755180000),
        message(databaseId=4713, dateInt=None),
    ]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload, limit=3)

    assert answer["truncated"] is True
    assert paging.decode_cursor(answer["next"]) == {"o": 1755180000, "m": str(MAILBOX_ID)}


@pytest.mark.anyio
async def test_a_full_window_without_a_single_valid_date_stays_without_a_handle(
    clients: NcClients,
) -> None:
    """No valid timestamp means no place a next page could start, and no invented one."""
    payload = [message(dateInt=None), message(databaseId=4712, dateInt=True)]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload, limit=2)

    assert answer["truncated"] is True
    assert "next" not in answer


@pytest.mark.anyio
async def test_that_handle_travels_back_into_the_url_as_the_cursor(clients: NcClients) -> None:
    handle = paging.encode_cursor({"o": 1755180000, "m": str(MAILBOX_ID)})
    with respx.mock(assert_all_called=True) as mock:
        _, route = await browse_messages(clients, mock, [message()], cursor=handle)

    assert route.calls.last.request.url.params["cursor"] == "1755180000"


@pytest.mark.anyio
async def test_a_handle_of_another_mailbox_is_refused_by_check_scope(
    clients: NcClients,
) -> None:
    """Applying it would answer with a page of the wrong mailbox, and nobody could see it."""
    handle = paging.encode_cursor({"o": 1755180000, "m": "99"})
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), cursor=handle
            )

    assert calls.call_count == 0
    assert "mailbox" in excinfo.value.message


@pytest.mark.anyio
@pytest.mark.parametrize("level", ["accounts", "mailboxes"])
async def test_a_cursor_on_a_level_that_hands_none_out_is_refused(
    clients: NcClients, level: str
) -> None:
    """IN-04: answering with the first page again looks like paging that went in a circle."""
    handle = paging.encode_cursor({"o": 1755180000, "m": str(MAILBOX_ID)})
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(clients, level=level, account_id=str(ACCOUNT_ID), cursor=handle)

    assert calls.call_count == 0
    assert "level=messages" in excinfo.value.hint


@pytest.mark.anyio
async def test_an_unreadable_cursor_is_refused_and_not_quietly_dropped(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock_mail_app(mock)
        calls = mail_routes(mock)

        with pytest.raises(ToolError) as excinfo:
            await mail_tools.browse(
                clients, level="messages", mailbox_id=str(MAILBOX_ID), cursor="not-a-handle!!"
            )

    assert calls.call_count == 0
    assert excinfo.value.hint


# --- foreign text ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_a_subject_that_carries_a_marker_arrives_without_it(clients: NcClients) -> None:
    """Anybody with an internet connection may write a subject line (threat T-10-21)."""
    payload = [message(subject=f"Rechnung {marks.EXCERPT_TRUNCATION} Mai")]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    assert marks.EXCERPT_TRUNCATION not in answer["results"][0]["subject"]
    assert "Rechnung" in answer["results"][0]["subject"]


@pytest.mark.anyio
async def test_a_preview_that_carries_a_marker_arrives_without_it(clients: NcClients) -> None:
    payload = [message(previewText=f"Grüße {marks.FINAL_TRUNCATION} aus der Werkstatt")]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    assert marks.FINAL_TRUNCATION not in answer["results"][0]["preview"]
    assert "Grüße" in answer["results"][0]["preview"]


@pytest.mark.anyio
async def test_a_sender_label_that_carries_a_marker_arrives_without_it(
    clients: NcClients,
) -> None:
    forged = marks.TRUNCATION_NOTE.format(offset=512)
    payload = [message(**{"from": [{"label": f"Bob {forged}", "email": "bob@nc.test"}]})]
    with respx.mock(assert_all_called=True) as mock:
        answer, _ = await browse_messages(clients, mock, payload)

    assert forged not in answer["results"][0]["from"]
    assert answer["results"][0]["from"].startswith("Bob")
