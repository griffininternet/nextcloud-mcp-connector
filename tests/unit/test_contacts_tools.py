"""Unit tests for ``contacts_search``: fan out, honest degradation and a compact answer.

The client tests pin the wire format. These tests pin the promises the tool makes to the
model: every address book is asked, a failing one is named instead of silently dropped, an
empty search term costs no request, and the answer carries the stable fields only, never
the raw vCard.
"""

from pathlib import Path

import httpx
import pytest
import respx
from lxml import etree

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import xml as davxml
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import contacts as contacts_tools

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

HOME = f"{BASE}/remote.php/dav/addressbooks/users/alice/"
CONTACTS = f"{HOME}contacts/"
TEAM = f"{HOME}team%20alpha/"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def addressbooks_response() -> httpx.Response:
    return httpx.Response(
        207,
        text=fixture("carddav_addressbooks_207.xml"),
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )


def report_response() -> httpx.Response:
    return httpx.Response(
        207,
        text=fixture("carddav_report_207.xml"),
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )


def empty_multistatus() -> httpx.Response:
    body = '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:"/>'
    return httpx.Response(207, text=body, headers={"Content-Type": "application/xml"})


@pytest.mark.anyio
async def test_every_addressbook_is_asked_and_the_hits_are_merged(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        first = mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        second = mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        result = await contacts_tools.search(clients, "meier")

    assert first.call_count == 1
    assert second.call_count == 1, "a hit can live in any address book of the account"

    assert result["query"] == "meier"
    assert result["count"] == 3
    assert "degraded" not in result

    maria = next(item for item in result["contacts"] if item["uid"] == "maria-meier-uid")
    assert maria["full_name"] == "Maria Meier"
    assert maria["emails"] == ["maria.meier@beispiel.de", "m.meier@example.org"]
    assert maria["phones"] == ["+49 40 1234567", "+49 170 7654321"]
    assert maria["organization"] == "Beispiel GmbH, Vertrieb"
    assert maria["addressbook"] == "Kontakte", "the display name, not the uri"


@pytest.mark.anyio
async def test_a_contact_without_optional_fields_stays_small(clients: NcClients) -> None:
    """Schema diet: an empty list or an empty string is not worth a key in every answer."""
    with respx.mock(assert_all_called=False) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        result = await contacts_tools.search(clients, "name")

    minimal = next(item for item in result["contacts"] if item["full_name"] == "Nur Name")
    assert set(minimal) == {"full_name", "addressbook"}


@pytest.mark.anyio
async def test_the_answer_never_carries_the_raw_vcard(clients: NcClients) -> None:
    """T-01-56 and the token budget: only the stable fields leave this tool."""
    with respx.mock(assert_all_called=False) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        result = await contacts_tools.search(clients, "meier")

    blob = repr(result)
    assert "BEGIN:VCARD" not in blob
    assert "VERSION:3.0" not in blob
    allowed = {"full_name", "emails", "phones", "organization", "addressbook", "uid"}
    for contact in result["contacts"]:
        assert set(contact) <= allowed


@pytest.mark.anyio
async def test_an_empty_search_term_is_refused_without_a_single_request(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        propfind = mock.route(method="PROPFIND")
        report = mock.route(method="REPORT")

        with pytest.raises(ToolError) as excinfo:
            await contacts_tools.search(clients, "   ")

    assert propfind.call_count == 0
    assert report.call_count == 0
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_limit_above_the_maximum_is_reduced_to_the_maximum(clients: NcClients) -> None:
    """The cap travels to the server as ``c:nresults``, so a huge book stays a small answer."""
    with respx.mock(assert_all_called=False) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        route = mock.route(method="REPORT", url=CONTACTS).mock(return_value=empty_multistatus())
        mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        await contacts_tools.search(clients, "meier", limit=100_000)

    body = etree.fromstring(route.calls[0].request.content, parser=davxml.hardened_parser())
    nresults = body.find(f".//{{{davxml.CARD}}}nresults")
    assert nresults is not None
    assert nresults.text == str(contacts_tools.MAX_LIMIT)


@pytest.mark.anyio
async def test_a_failing_addressbook_is_named_and_the_other_hits_still_arrive(
    clients: NcClients,
) -> None:
    """A partial answer that says it is partial is useful; one that does not is a lie."""
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        mock.route(method="REPORT", url=TEAM).mock(
            return_value=httpx.Response(503, text="service unavailable")
        )

        result = await contacts_tools.search(clients, "meier")

    assert result["count"] == 3, "the healthy address book still answers"
    assert result["degraded"] == [
        {"addressbook": "Team Alpha", "reason": result["degraded"][0]["reason"]}
    ]
    assert "503" in result["degraded"][0]["reason"]


@pytest.mark.anyio
async def test_a_search_without_a_hit_is_an_empty_list_and_not_an_error(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=empty_multistatus())
        mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        result = await contacts_tools.search(clients, "niemand")

    assert result["contacts"] == []
    assert result["count"] == 0
    assert result["query"] == "niemand"
    assert "degraded" not in result


@pytest.mark.anyio
async def test_every_addressbook_failing_is_an_error_and_not_an_empty_result(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=httpx.Response(503, text="no"))
        mock.route(method="REPORT", url=TEAM).mock(return_value=httpx.Response(503, text="no"))

        with pytest.raises(ToolError) as excinfo:
            await contacts_tools.search(clients, "meier")

    assert "none of the address books could be read" in excinfo.value.message.lower()
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_account_without_an_addressbook_gets_the_solution_hint(
    clients: NcClients,
) -> None:
    """bob in the test instance: no address book at all, and the tool says what to do."""
    body = (
        '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">'
        "<d:response><d:href>/remote.php/dav/addressbooks/users/alice/</d:href>"
        "<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>"
        "<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>"
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=httpx.Response(207, text=body))

        with pytest.raises(ToolError) as excinfo:
            await contacts_tools.search(clients, "meier")

    assert "no address book" in excinfo.value.message.lower()
    assert "dav:create-addressbook" in excinfo.value.hint


@pytest.mark.anyio
async def test_more_hits_than_the_limit_are_cut_and_the_cut_is_reported(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.route(method="PROPFIND", url=HOME).mock(return_value=addressbooks_response())
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        mock.route(method="REPORT", url=TEAM).mock(return_value=empty_multistatus())

        result = await contacts_tools.search(clients, "meier", limit=2)

    assert result["count"] == 2
    assert result["truncated"] is True


def test_the_tool_module_has_no_write_path(clients: NcClients) -> None:
    """D-07: contacts are read only, and that stays greppable in the tool layer too."""
    source = Path(contacts_tools.__file__).read_text(encoding="utf-8")
    for call in (".put(", ".delete(", ".patch("):
        assert call not in source
