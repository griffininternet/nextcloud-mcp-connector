"""Unit tests for the WebDAV SEARCH body, the SEARCH request and PROPFIND with Depth 1.

The two request builders of this module are the trust boundary between model generated
text and XML (threats T-01-30 and T-01-32), so the escaping test and the endpoint test are
as important here as the mapping of a real 207 answer.
"""

from pathlib import Path

import httpx
import pytest
import respx
from lxml import etree

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import dav, xml
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
SEARCH_URL = f"{BASE}/remote.php/dav/"
DOCS_URL = f"{BASE}/remote.php/dav/files/{USER}/Docs"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SEARCH_207 = (FIXTURES / "webdav_search_207.xml").read_text(encoding="utf-8")
PROPFIND_207 = (FIXTURES / "webdav_propfind_207.xml").read_text(encoding="utf-8")


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)


def _text_of(root: etree._Element, tag: str) -> str:
    element = root.find(f".//{{{xml.DAV}}}{tag}")
    assert element is not None, f"the body has no d:{tag}"
    return (element.text or "").strip()


def test_the_search_body_escapes_a_term_with_ampersand_and_angle_bracket() -> None:
    body = dav.build_search_body("/files/alice", "R&D <plan>", 25)

    assert b"&amp;" in body, "lxml escapes the ampersand, we never concatenate"
    assert b"&lt;plan&gt;" in body, "lxml escapes the angle brackets"
    root = etree.fromstring(body)
    assert _text_of(root, "literal") == "%R&D <plan>%", "the term arrives unchanged as text"


def test_the_search_body_sets_exactly_one_limit_with_nresults() -> None:
    root = etree.fromstring(dav.build_search_body("/files/alice", "budget", 25))

    limits = root.findall(f".//{{{xml.DAV}}}limit")
    assert len(limits) == 1, "without d:limit Nextcloud caps at 100 results"
    nresults = limits[0].find(f"{{{xml.DAV}}}nresults")
    assert nresults is not None, "d:limit without d:nresults is not a limit"
    assert (nresults.text or "") == "25"


def test_the_search_body_scopes_the_query_to_the_users_home() -> None:
    root = etree.fromstring(dav.build_search_body("/files/alice/Docs", "budget", 10))

    assert _text_of(root, "href") == "/files/alice/Docs"
    assert _text_of(root, "depth") == "infinity"
    assert root.find(f".//{{{xml.OC}}}fileid") is not None, "the fileid is selected"


def test_the_dav_module_never_builds_xml_from_a_string() -> None:
    """The one anti pattern this file exists to prevent (threat T-01-30)."""
    source = Path(dav.__file__).read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
    assert "<d:" not in code, "DAV bodies are built with lxml, never with a string"


@pytest.mark.parametrize("term", ["", "   "])
def test_an_empty_search_term_is_refused_before_the_request(term: str) -> None:
    with pytest.raises(ToolError) as excinfo:
        dav.build_search_body("/files/alice", term, 25)
    assert excinfo.value.hint


def test_a_limit_below_one_is_refused() -> None:
    with pytest.raises(ToolError):
        dav.build_search_body("/files/alice", "budget", 0)


def test_search_scope_is_the_home_or_one_folder_below_it(creds: Credentials) -> None:
    assert dav.search_scope(creds, "/") == "/files/alice"
    assert dav.search_scope(creds, "/Docs") == "/files/alice/Docs"
    assert dav.search_scope(creds, "Docs/") == "/files/alice/Docs"
    with pytest.raises(ToolError):
        dav.search_scope(creds, "/Docs/../../etc")


@pytest.mark.anyio
async def test_search_goes_to_the_dav_root_as_text_xml(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="SEARCH", url=SEARCH_URL).mock(
            return_value=httpx.Response(207, text=SEARCH_207)
        )
        await dav.search(client, creds, "/files/alice", "budget", 25)

    request = route.calls[0].request
    assert str(request.url) == SEARCH_URL, "the endpoint is the DAV root, not the files path"
    assert request.headers["content-type"] == "text/xml"
    assert request.headers["authorization"].startswith("Basic ")
    assert b"basicsearch" in request.content


@pytest.mark.anyio
async def test_search_maps_a_real_207_answer(client: httpx.AsyncClient, creds: Credentials) -> None:
    with respx.mock as mock:
        mock.route(method="SEARCH", url=SEARCH_URL).mock(
            return_value=httpx.Response(207, text=SEARCH_207)
        )
        hits = await dav.search(client, creds, "/files/alice", "budget", 25)

    assert [hit["path"] for hit in hits] == [
        "/Docs/budget-2026.md",
        "/Budget Ablage",
        "/Docs/Jahres budget & Anhang.md",
        "/budget.txt",
    ]

    first = hits[0]
    assert first["name"] == "budget-2026.md"
    assert first["content_type"] == "text/markdown"
    assert first["size"] == 2048
    assert first["last_modified"] == "Thu, 14 Aug 2026 10:00:00 GMT"
    assert first["fileid"] == "4711"
    assert first["is_collection"] is False

    folder = hits[1]
    assert folder["is_collection"] is True, "d:collection makes it a folder"
    assert folder["size"] == 15360, "a folder reports oc:size, never getcontentlength"

    assert hits[3]["fileid"] == "", "a 404 propstat contributes nothing, not an empty guess"


@pytest.mark.anyio
async def test_search_drops_hrefs_outside_the_users_home(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    foreign = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/alicexyz/budget.md</d:href>
    <d:propstat><d:prop><oc:fileid>1</oc:fileid></d:prop>
    <d:status>HTTP/1.1 200 OK</d:status></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/alice/budget.md</d:href>
    <d:propstat><d:prop><oc:fileid>2</oc:fileid></d:prop>
    <d:status>HTTP/1.1 200 OK</d:status></d:propstat>
  </d:response>
</d:multistatus>
"""
    with respx.mock as mock:
        mock.route(method="SEARCH", url=SEARCH_URL).mock(
            return_value=httpx.Response(207, text=foreign)
        )
        hits = await dav.search(client, creds, "/files/alice", "budget", 25)

    assert [hit["fileid"] for hit in hits] == ["2"], "a similar user name is not this user"


@pytest.mark.anyio
async def test_search_reports_a_server_error_without_leaking_the_body(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock as mock:
        mock.route(method="SEARCH", url=SEARCH_URL).mock(
            return_value=httpx.Response(500, text="<html>stack trace</html>")
        )
        with pytest.raises(ToolError) as excinfo:
            await dav.search(client, creds, "/files/alice", "budget", 25)

    assert "500" in excinfo.value.message
    assert "stack trace" not in excinfo.value.message


@pytest.mark.anyio
async def test_propfind_children_skips_the_folder_itself(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.route(method="PROPFIND", url=DOCS_URL).mock(
            return_value=httpx.Response(207, text=PROPFIND_207)
        )
        itself, children = await dav.propfind_children(client, creds, "/Docs")

    request = route.calls[0].request
    assert request.headers["depth"] == "1"
    assert b"permissions" in request.content, "oc:permissions is part of the property set"
    assert b"size" in request.content

    assert itself["path"] == "/Docs"
    assert itself["is_collection"] is True
    assert [child["path"] for child in children] == [
        "/Docs/notes.md",
        "/Docs/Grüße & Co.txt",
        "/Docs/Bilder",
    ]
    assert "/Docs" not in [child["path"] for child in children]


@pytest.mark.anyio
async def test_propfind_children_of_a_file_reports_the_file_as_target(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Depth 1 on a file answers with the file alone; the tool layer turns that into a hint."""
    body = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/alice/Docs/notes.md</d:href>
    <d:propstat><d:prop>
      <d:displayname>notes.md</d:displayname>
      <d:getcontentlength>10</d:getcontentlength>
      <d:resourcetype/>
      <oc:fileid>11</oc:fileid>
    </d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat>
  </d:response>
</d:multistatus>
"""
    with respx.mock as mock:
        mock.route(method="PROPFIND", url=f"{BASE}/remote.php/dav/files/{USER}/Docs/notes.md").mock(
            return_value=httpx.Response(207, text=body)
        )
        itself, children = await dav.propfind_children(client, creds, "/Docs/notes.md")

    assert itself["is_collection"] is False
    assert children == []


@pytest.mark.anyio
async def test_propfind_children_of_a_missing_folder_reports_the_path(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    with respx.mock as mock:
        mock.route(method="PROPFIND", url=f"{BASE}/remote.php/dav/files/{USER}/Nope").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(ToolError) as excinfo:
            await dav.propfind_children(client, creds, "/Nope")

    assert "/Nope" in excinfo.value.message
    assert "not found" in excinfo.value.message.lower()


@pytest.mark.anyio
async def test_propfind_children_without_the_target_is_an_error(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    empty = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:"></d:multistatus>
"""
    with respx.mock as mock:
        mock.route(method="PROPFIND", url=DOCS_URL).mock(
            return_value=httpx.Response(207, text=empty)
        )
        with pytest.raises(ToolError) as excinfo:
            await dav.propfind_children(client, creds, "/Docs")

    assert excinfo.value.hint
