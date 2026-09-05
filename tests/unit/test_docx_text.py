"""Unit tests for safe DOCX extraction."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.credentials import Credentials
from mcp_connector.tools import docx_text

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
PATH = "/Docs/protocol.docx"
URL = f"{BASE}/remote.php/dav/files/{USER}/Docs/protocol.docx"


def _docx(document_xml: str) -> bytes:
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)
    return out.getvalue()


def _xml(body: str) -> str:
    return (
        '<?xml version="1.0"?>'
        "<w:document "
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )


def _stat(length: int) -> str:
    return f"""<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/alice/Docs/protocol.docx</d:href>
    <d:propstat>
      <d:prop>
        <d:getcontentlength>{length}</d:getcontentlength>
        <d:getcontenttype>{docx_text.DOCX_CONTENT_TYPE}</d:getcontenttype>
        <d:resourcetype/>
        <oc:fileid>42</oc:fileid>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>"""


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


def test_extracts_paragraphs_breaks_tabs_and_tables_in_order() -> None:
    data = _docx(
        _xml(
            "<w:p><w:r><w:t>Protocol title</w:t><w:tab/>"
            "<w:t>A</w:t></w:r></w:p>"
            "<w:tbl><w:tr>"
            "<w:tc><w:p><w:r><w:t>Morning</w:t></w:r></w:p></w:tc>"
            "<w:tc><w:p><w:r><w:t>2 drops</w:t></w:r></w:p></w:tc>"
            "</w:tr></w:tbl>"
            "<w:p><w:r><w:t>Line one</w:t><w:br/>"
            "<w:t>Line two</w:t></w:r></w:p>"
        )
    )
    assert docx_text.extract_docx(data) == (
        "Protocol title\tA\nMorning\t2 drops\nLine one\nLine two"
    )


def test_rejects_non_zip_and_missing_document_body() -> None:
    with pytest.raises(ToolError, match=r"valid \.docx"):
        docx_text.extract_docx(b"not a zip")
    out = BytesIO()
    with ZipFile(out, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
    with pytest.raises(ToolError, match="no Word document body"):
        docx_text.extract_docx(out.getvalue())


def test_rejects_excessive_uncompressed_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(docx_text, "MAX_UNCOMPRESSED_BYTES", 3)
    data = _docx(_xml("<w:p><w:r><w:t>text</w:t></w:r></w:p>"))
    with pytest.raises(ToolError, match="safe extraction limit"):
        docx_text.extract_docx(data)


@pytest.mark.anyio
async def test_tool_downloads_and_returns_extracted_text(clients: NcClients) -> None:
    data = _docx(_xml("<w:p><w:r><w:t>Aching joints protocol</w:t></w:r></w:p>"))
    with respx.mock(assert_all_called=True) as mock:
        mock.route(method="PROPFIND", url=URL).mock(
            return_value=httpx.Response(207, text=_stat(len(data)))
        )
        mock.route(method="GET", url=URL).mock(return_value=httpx.Response(200, content=data))
        result = await docx_text.extract(clients, PATH)

    assert result["content"] == "Aching joints protocol"
    assert result["format"] == "docx"
    assert result["truncated"] is False
    assert result["source_size"] == len(data)


@pytest.mark.anyio
async def test_extracted_text_paginates_by_utf8_bytes(clients: NcClients) -> None:
    data = _docx(_xml("<w:p><w:r><w:t>abcédef</w:t></w:r></w:p>"))
    with respx.mock as mock:
        mock.route(method="PROPFIND", url=URL).mock(
            return_value=httpx.Response(207, text=_stat(len(data)))
        )
        mock.route(method="GET", url=URL).mock(return_value=httpx.Response(200, content=data))
        first = await docx_text.extract(clients, PATH, max_bytes=4)

    assert first["content"] == "abc"
    assert first["next_offset"] == 3
    assert first["truncated"] is True


@pytest.mark.anyio
async def test_rejects_wrong_mimetype_before_get(clients: NcClients) -> None:
    body = _stat(10).replace(
        docx_text.DOCX_CONTENT_TYPE,
        "application/octet-stream",
    )
    with respx.mock as mock:
        mock.route(method="PROPFIND", url=URL).mock(return_value=httpx.Response(207, text=body))
        get = mock.route(method="GET", url=URL)
        with pytest.raises(ToolError, match="not a supported Word document"):
            await docx_text.extract(clients, PATH)
    assert not get.called
