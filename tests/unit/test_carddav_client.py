"""Unit tests for the CardDAV client: discovery, the query body and defensive vCard reading.

Three things decide whether this client is correct, and each of them has its own block
below.

* the **path**: address books live under ``addressbooks/users/<uid>/``, with a ``users/``
  segment that the calendar path does not have. Getting this wrong produces a 404 that
  looks exactly like "this account has no contacts".
* the **query body**: sabre accepts exactly one ``c:filter`` element, and it wants the
  search term inside a ``c:text-match``. A term with ``&`` or ``<`` must never be able to
  close a tag (threat T-01-53).
* the **vCard**: missing properties are the normal case, not the exception. A contact with
  nothing but ``FN`` has to survive the parser.
"""

from pathlib import Path

import httpx
import pytest
import respx
from lxml import etree

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import carddav
from mcp_connector.nextcloud.clients import xml as davxml
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

ADDRESSBOOK_HOME = f"{BASE}/remote.php/dav/addressbooks/users/alice/"
CONTACTS = f"{ADDRESSBOOK_HOME}contacts/"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


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


# --------------------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_discovery_asks_the_addressbook_home_under_the_users_segment(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """``addressbooks/users/<uid>/``: the CardDAV root has a segment CalDAV does not."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=addressbooks_response()
        )
        books = await carddav.discover_addressbooks(client, creds)

    request = route.calls[0].request
    assert "addressbooks/users/" in str(request.url)
    assert str(request.url) == ADDRESSBOOK_HOME
    assert request.headers["Depth"] == "1"
    assert request.headers["Content-Type"] == "application/xml"

    body = etree.fromstring(request.content, parser=davxml.hardened_parser())
    asked = {str(element.tag) for element in body.iter() if isinstance(element.tag, str)}
    assert f"{{{davxml.DAV}}}displayname" in asked
    assert f"{{{davxml.DAV}}}resourcetype" in asked

    assert [book.uri for book in books] == ["contacts", "team alpha"]
    assert [book.display_name for book in books] == ["Kontakte", "Team Alpha"]


@pytest.mark.anyio
async def test_discovery_drops_the_generated_addressbooks(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Verified against a running Nextcloud 34, not assumed.

    Every account that has ever authenticated owns ``z-server-generated--system`` (the
    directory of all accounts) and ``z-app-generated--contactsinteraction--recent``. Both
    are address books to sabre. Keeping them would put the account directory of the whole
    instance into a name search and would make "this account has no address book"
    unreachable on any real server.
    """
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=addressbooks_response()
        )
        books = await carddav.discover_addressbooks(client, creds)

    uris = {book.uri for book in books}
    assert uris == {"contacts", "team alpha"}
    assert not any(uri.startswith(carddav.GENERATED_PREFIXES) for uri in uris)


@pytest.mark.anyio
async def test_an_account_with_only_generated_addressbooks_counts_as_having_none(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The live shape of a user created by ``occ user:add`` who then authenticated once."""
    body = (
        '<?xml version="1.0"?>'
        '<d:multistatus xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">'
        "<d:response>"
        "<d:href>/remote.php/dav/addressbooks/users/alice/z-server-generated--system/</d:href>"
        "<d:propstat><d:prop><d:resourcetype><d:collection/><card:addressbook/>"
        "</d:resourcetype></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat>"
        "</d:response></d:multistatus>"
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=httpx.Response(207, text=body)
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.discover_addressbooks(client, creds)

    assert "dav:create-addressbook" in excinfo.value.hint


@pytest.mark.anyio
async def test_discovery_unquotes_the_uri_and_quotes_it_again_for_the_url(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """``team%20alpha`` is one URI with a space, and it stays one path segment."""
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=addressbooks_response()
        )
        books = await carddav.discover_addressbooks(client, creds)

    assert books[1].uri == "team alpha"
    assert carddav.addressbook_url(creds, books[1].uri) == f"{ADDRESSBOOK_HOME}team%20alpha/"


@pytest.mark.anyio
async def test_an_account_without_an_addressbook_names_the_occ_command(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Pitfall 3: ``occ user:add`` creates no address book, so "no book" is not "no hits"."""
    body = (
        '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">'
        "<d:response><d:href>/remote.php/dav/addressbooks/users/alice/</d:href>"
        "<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>"
        "<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>"
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=httpx.Response(207, text=body)
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.discover_addressbooks(client, creds)

    assert "no address book" in excinfo.value.message.lower()
    assert "dav:create-addressbook" in excinfo.value.hint


@pytest.mark.anyio
async def test_a_rejected_app_password_during_discovery_is_not_retried(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="PROPFIND", url=ADDRESSBOOK_HOME).mock(
            return_value=httpx.Response(401, text="unauthorized")
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.discover_addressbooks(client, creds)

    assert route.call_count == 1, "a repeated auth failure slows the whole instance down"
    assert "app password" in excinfo.value.message.lower()


# --------------------------------------------------------------------------------------
# The query body
# --------------------------------------------------------------------------------------


def test_the_query_body_carries_one_filter_two_prop_filters_and_a_limit() -> None:
    """Verified against sabre: only one ``c:filter`` is allowed, ``test`` must be anyof."""
    body = carddav.build_addressbook_query("meier", 25)
    root = etree.fromstring(body, parser=davxml.hardened_parser())

    assert root.tag == f"{{{davxml.CARD}}}addressbook-query"

    filters = root.findall(f"{{{davxml.CARD}}}filter")
    assert len(filters) == 1, "sabre rejects a second filter element with 400"
    assert filters[0].get("test") == "anyof"

    prop_filters = filters[0].findall(f"{{{davxml.CARD}}}prop-filter")
    assert [element.get("name") for element in prop_filters] == ["FN", "EMAIL"]
    for prop_filter in prop_filters:
        match = prop_filter.find(f"{{{davxml.CARD}}}text-match")
        assert match is not None
        assert match.get("match-type") == "contains"
        assert match.get("collation") == "i;unicode-casemap"
        assert match.text == "meier"

    limits = root.findall(f"{{{davxml.CARD}}}limit")
    assert len(limits) == 1
    nresults = limits[0].find(f"{{{davxml.CARD}}}nresults")
    assert nresults is not None
    assert nresults.text == "25"

    prop = root.find(f"{{{davxml.DAV}}}prop")
    assert prop is not None
    asked = {str(element.tag) for element in prop}
    assert f"{{{davxml.CARD}}}address-data" in asked


def test_a_search_term_with_ampersand_and_angle_bracket_is_escaped() -> None:
    """Threat T-01-53: the term is text, and text can never open or close a tag."""
    term = 'Meier & <Söhne> "AG"'
    body = carddav.build_addressbook_query(term, 10)

    assert b"&amp;" in body
    assert b"&lt;" in body
    assert b"<S\xc3\xb6hne>" not in body, "the angle brackets of the term must not survive raw"

    root = etree.fromstring(body, parser=davxml.hardened_parser())
    matches = root.findall(f".//{{{davxml.CARD}}}text-match")
    assert len(matches) == 2
    assert {match.text for match in matches} == {term}, "escaping is reversible, not lossy"


def test_the_query_body_is_built_with_lxml_and_not_from_a_string() -> None:
    source = Path(carddav.__file__).read_text(encoding="utf-8")
    assert "<c:" not in source, "no XML literal belongs into this module"
    assert "addressbook-query" in source


def test_an_empty_search_term_is_refused_before_a_body_is_built() -> None:
    for term in ("", "   "):
        with pytest.raises(ToolError) as excinfo:
            carddav.build_addressbook_query(term, 25)
        assert excinfo.value.hint


@pytest.mark.anyio
async def test_an_empty_search_term_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(method="REPORT")
        with pytest.raises(ToolError):
            await carddav.query_contacts(client, creds, "contacts", "  ", 25)

    assert route.call_count == 0


# --------------------------------------------------------------------------------------
# vCard parsing
# --------------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_the_report_yields_the_stable_contact_shape(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        contacts = await carddav.query_contacts(
            client, creds, "contacts", "meier", 25, addressbook="Kontakte"
        )

    assert route.calls[0].request.headers["Depth"] == "1"
    assert route.calls[0].request.headers["Content-Type"] == "application/xml"

    maria = next(item for item in contacts if item["uid"] == "maria-meier-uid")
    assert maria["full_name"] == "Maria Meier"
    assert maria["emails"] == ["maria.meier@beispiel.de", "m.meier@example.org"]
    assert maria["phones"] == ["+49 40 1234567", "+49 170 7654321"]
    assert maria["organization"] == "Beispiel GmbH, Vertrieb"
    assert maria["addressbook"] == "Kontakte"
    assert set(maria) == {
        "full_name",
        "emails",
        "phones",
        "organization",
        "addressbook",
        "uid",
    }, "no raw vCard and no etag leak into the contact shape"


@pytest.mark.anyio
async def test_a_contact_without_email_phone_and_organization_never_crashes(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Missing properties are the normal case in a real address book."""
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=report_response())
        contacts = await carddav.query_contacts(client, creds, "contacts", "name", 25)

    minimal = next(item for item in contacts if item["full_name"] == "Nur Name")
    assert minimal["emails"] == []
    assert minimal["phones"] == []
    assert minimal["organization"] == ""
    assert minimal["uid"] == ""
    assert minimal["addressbook"] == "contacts", "without a display name the uri is the label"


def test_umlauts_and_an_ampersand_survive_the_vcard_parser() -> None:
    contacts = carddav.parse_contacts(
        fixture("carddav_report_207.xml").encode("utf-8"), addressbook="Kontakte"
    )

    juergen = next(item for item in contacts if item["uid"] == "juergen-schroeder-uid")
    assert juergen["full_name"] == "Jürgen Schröder"
    assert juergen["organization"] == "Meier & Söhne"
    assert juergen["emails"] == ["j.schroeder@meier-soehne.de"]
    assert juergen["phones"] == []


def test_a_damaged_vcard_is_reported_and_not_guessed_at() -> None:
    """A vCard nobody can read is an error with a hint, never a half parsed contact."""
    body = (
        '<?xml version="1.0"?>'
        '<d:multistatus xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">'
        "<d:response><d:href>/remote.php/dav/addressbooks/users/alice/contacts/x.vcf</d:href>"
        "<d:propstat><d:prop><card:address-data>NOT A VCARD AT ALL</card:address-data></d:prop>"
        "<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>"
    )
    with pytest.raises(ToolError) as excinfo:
        carddav.parse_contacts(body, addressbook="Kontakte")

    assert excinfo.value.hint


def test_the_module_parses_vcards_with_vobject_and_never_with_a_regex() -> None:
    """D-17 as a grep: RFC 6350 is not a job for a hand written pattern."""
    source = Path(carddav.__file__).read_text(encoding="utf-8")
    assert "vobject" in source
    assert "import re" not in source
    assert "re.compile" not in source


# --------------------------------------------------------------------------------------
# Guards and status handling
# --------------------------------------------------------------------------------------


def test_the_module_has_no_write_path_at_all() -> None:
    """T-01-57: contacts are read only in this phase, and that is greppable."""
    source = Path(carddav.__file__).read_text(encoding="utf-8")
    for method in ("PUT", "DELETE", "MOVE", "PROPPATCH"):
        assert method not in source, f"{method} has no place in a read only client"
    for call in (".put(", ".delete(", ".patch("):
        assert call not in source, f"{call} is a write and this module never writes"


@pytest.mark.parametrize("uri", ["../calendars", "contacts/sub", "", "  ", "with\nnewline", ".."])
def test_an_addressbook_uri_that_could_leave_the_collection_is_refused(
    creds: Credentials, uri: str
) -> None:
    """Threat T-01-59: the URI is one path segment, never a path."""
    with pytest.raises(ToolError):
        carddav.addressbook_url(creds, uri)


@pytest.mark.anyio
async def test_an_unknown_addressbook_is_reported_as_not_found(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=f"{ADDRESSBOOK_HOME}weg/").mock(
            return_value=httpx.Response(404, text="not found")
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.query_contacts(client, creds, "weg", "meier", 25)

    assert "weg" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_server_error_during_the_query_is_reported_with_its_status(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=CONTACTS).mock(
            return_value=httpx.Response(503, text="service unavailable")
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.query_contacts(client, creds, "contacts", "meier", 25)

    assert "503" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_redirect_is_never_followed(client: httpx.AsyncClient, creds: Credentials) -> None:
    """A redirect would carry the Authorization header to a foreign host (T-01-08)."""
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=CONTACTS).mock(
            return_value=httpx.Response(302, headers={"Location": "http://evil.test/"})
        )
        with pytest.raises(ToolError) as excinfo:
            await carddav.query_contacts(client, creds, "contacts", "meier", 25)

    assert "redirect" in excinfo.value.message.lower()


@pytest.mark.anyio
async def test_an_addressbook_without_a_hit_is_an_empty_list(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="REPORT", url=CONTACTS).mock(return_value=empty_multistatus())
        contacts = await carddav.query_contacts(client, creds, "contacts", "niemand", 25)

    assert contacts == []
