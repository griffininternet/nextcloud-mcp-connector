"""Unit tests for the hardened XML layer (threat T-01-11).

Nextcloud answers with 207 Multi-Status bodies. Parsing untrusted XML with a default
parser is how XXE and billion-laughs enter a Python process.
"""

import pytest
from lxml import etree

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import xml

MULTISTATUS = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/alice/Docs/notes.md</d:href>
    <d:propstat>
      <d:prop>
        <d:getcontentlength>1234</d:getcontentlength>
        <d:getcontenttype>text/markdown</d:getcontenttype>
        <d:getetag>&quot;abc&quot;</d:getetag>
        <d:resourcetype/>
        <oc:fileid>4711</oc:fileid>
        <oc:permissions>RGDNVW</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
    <d:propstat>
      <d:prop><d:quota-used-bytes/></d:prop>
      <d:status>HTTP/1.1 404 Not Found</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/alice/Docs/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""

XXE_PROBE = """<?xml version="1.0"?>
<!DOCTYPE multistatus [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/remote.php/dav/files/alice/&xxe;</d:href>
  </d:response>
</d:multistatus>
"""

BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<d:multistatus xmlns:d="DAV:"><d:response><d:href>&lol3;</d:href></d:response></d:multistatus>
"""


def test_hardened_parser_settings() -> None:
    """lxml does not expose the flags as attributes, so pin them at the source level.

    The behaviour is asserted separately by the entity and billion-laughs probes below.
    """
    import inspect

    parser = xml.hardened_parser()
    assert isinstance(parser, etree.XMLParser)

    source = inspect.getsource(xml.hardened_parser)
    for setting in ("resolve_entities=False", "no_network=True", "huge_tree=False"):
        assert setting in source, f"hardened_parser must keep {setting}"


def test_hardened_parser_does_not_expand_entities() -> None:
    """Behavioural proof for resolve_entities=False on a body with a defined entity."""
    body = (
        '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY greet "hello">]>'
        '<d:multistatus xmlns:d="DAV:"><d:response><d:href>&greet;</d:href>'
        "</d:response></d:multistatus>"
    )
    with pytest.raises(ToolError):
        xml.parse_multistatus(body)


def test_namespace_constants() -> None:
    assert xml.DAV == "DAV:"
    assert xml.OC == "http://owncloud.org/ns"
    assert xml.NC == "http://nextcloud.org/ns"
    assert xml.CAL == "urn:ietf:params:xml:ns:caldav"
    assert xml.CARD == "urn:ietf:params:xml:ns:carddav"
    assert xml.CS == "http://calendarserver.org/ns/"
    assert xml.NSMAP["d"] == xml.DAV


def test_parse_multistatus_returns_href_and_props() -> None:
    entries = xml.parse_multistatus(MULTISTATUS)
    assert [href for href, _ in entries] == [
        "/remote.php/dav/files/alice/Docs/notes.md",
        "/remote.php/dav/files/alice/Docs/",
    ]
    props = entries[0][1]
    assert props[f"{{{xml.DAV}}}getcontentlength"] == "1234"
    assert props[f"{{{xml.DAV}}}getcontenttype"] == "text/markdown"
    assert props[f"{{{xml.OC}}}fileid"] == "4711"
    assert props[f"{{{xml.DAV}}}getetag"] == '"abc"'


def test_parse_multistatus_skips_propstats_that_are_not_ok() -> None:
    props = xml.parse_multistatus(MULTISTATUS)[0][1]
    assert f"{{{xml.DAV}}}quota-used-bytes" not in props


def test_parse_multistatus_marks_collections() -> None:
    props = xml.parse_multistatus(MULTISTATUS)[1][1]
    assert props[f"{{{xml.DAV}}}resourcetype"] == f"{{{xml.DAV}}}collection"


def test_parse_multistatus_accepts_bytes() -> None:
    assert xml.parse_multistatus(MULTISTATUS.encode("utf-8"))


def test_entity_declaration_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        xml.parse_multistatus(XXE_PROBE)
    assert excinfo.value.hint
    assert "/etc/passwd" not in excinfo.value.message


def test_billion_laughs_is_rejected() -> None:
    with pytest.raises(ToolError):
        xml.parse_multistatus(BILLION_LAUGHS)


def test_malformed_xml_raises_toolerror_not_a_parser_error() -> None:
    with pytest.raises(ToolError):
        xml.parse_multistatus("<d:multistatus xmlns:d='DAV:'><d:response>")


def test_wrong_root_element_is_rejected() -> None:
    with pytest.raises(ToolError):
        xml.parse_multistatus("<html><body>Login</body></html>")
