"""The boundaries of the client id metadata document fetch, every one with its negative.

No packet leaves this machine. The first half of the file needs no network at all and does
not even mock one, because the form of an identifier and the class of an address are pure
calls plus a resolver that is a parameter; the second half mocks the transport with
``respx`` and hands in a resolver, so the fetch is exercised end to end without a socket.

The address catalogue is the measurement of 06-RESEARCH.md, pattern 3, against the Python
3.13.13 of this project. Three of its rows exist to hold a specific mistake, and one test
below asserts the measurement itself so a future Python that changes one of those flags
fails here and not in production: 100.64.0.1 and 64:ff9b::7f00:1 are not ``is_private``,
and 224.0.0.1 is ``is_global``.
"""

import ast
import inspect
import ipaddress
import json
import logging
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.oauth import cimd

HOST = "metadata.attacker.example"
PORT = 443

#: The name and the address the fetch tests use. The name never resolves anywhere: every
#: test hands in the resolver, so what ``respx`` sees is the pinned literal.
NAME = "metadata.client.example"
PUBLIC_IP = "93.184.216.34"
PUBLIC_IPV6 = "2606:4700:4700::1111"
DOCUMENT_URL = f"https://{NAME}/c.json"
PINNED_URL = f"https://{PUBLIC_IP}/c.json"
PINNED_URL_V6 = f"https://[{PUBLIC_IPV6}]/c.json"


def document(**overrides: Any) -> dict[str, Any]:
    """The smallest document the rules admit for :data:`DOCUMENT_URL`, plus overrides."""
    return {
        "client_id": DOCUMENT_URL,
        "client_name": "A client that names itself",
        "redirect_uris": ["http://127.0.0.1/callback"],
    } | overrides


def sized_document(size: int) -> bytes:
    """An admissible document padded to exactly ``size`` bytes.

    The padding is one string property, so every character added to it adds exactly one
    byte to the encoded document and the size is the number it says it is.
    """
    body = document(padding="")
    raw = json.dumps(body, separators=(",", ":")).encode()
    body["padding"] = "x" * (size - len(raw))
    raw = json.dumps(body, separators=(",", ":")).encode()
    assert len(raw) == size, "the padding arithmetic of this helper is off"
    return raw


def answering(*addresses: str, calls: list[tuple[str, int]] | None = None) -> cimd.AddressLookup:
    """A resolver that answers with these literals, recording what it was asked."""

    async def resolve(host: str, port: int) -> list[str]:
        if calls is not None:
            calls.append((host, port))
        return list(addresses)

    return resolve


def failing(error: Exception) -> cimd.AddressLookup:
    """A resolver that cannot answer, which is the shape of a name that does not exist."""

    async def resolve(host: str, port: int) -> list[str]:
        raise error

    return resolve


# --- the form of a client identifier URL, before any packet ----------------------------


@pytest.mark.parametrize(
    "value",
    [
        "https://claude.ai/oauth/claude-code-client-metadata",
        "https://example.com/clients/metadata.json",
        "https://example.com/c.json?version=2",
        "https://example.com:8443/c.json",
        "  https://example.com/c.json  ",
    ],
)
def test_an_https_url_with_a_path_is_a_client_identifier(value: str) -> None:
    """A query is a SHOULD NOT of the draft and a port is a MAY, so neither is refused."""
    assert cimd.is_cimd_client_id(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "http://example.com/c.json",
        "https://example.com/",
        "https://example.com",
        "https://u:p@example.com/c.json",
        "https://example.com/c.json#x",
        "https://example.com/a/../c.json",
        "https://example.com/./c.json",
        "https://example.com/a/../../etc/c.json",
        "https:///c.json",
        "https://example.com:0/c.json",
        "https://example.com:99999/c.json",
        "cursor://anysphere.cursor-mcp/oauth/callback",
        "",
        "   ",
    ],
)
def test_everything_else_is_refused_without_a_packet(value: str) -> None:
    """Each of these is a target this process then never connects to (T-06-03).

    The refusal is stricter than the SDK's client side check on purpose: that one validates
    a URL its own operator configured, this one decides about an outbound request made on a
    stranger's behalf.
    """
    assert cimd.is_cimd_client_id(value) is False


# --- the class of the address behind the name -------------------------------------------


@pytest.mark.parametrize(
    "literal",
    [
        "127.0.0.1",
        "::1",
        "10.0.0.5",
        "192.168.1.1",
        "169.254.169.254",
        "::ffff:127.0.0.1",
        "2002:7f00:1::1",
        "64:ff9b::7f00:1",
        "100.64.0.1",
        "224.0.0.1",
        "0.0.0.0",  # noqa: S104 - the unspecified address as a target, not a bind address
        "::",
    ],
)
def test_a_target_that_is_not_a_public_address_is_refused(literal: str) -> None:
    """The cloud metadata address, the loopback forms and the three measured gaps."""
    assert cimd.target_allowed(ipaddress.ip_address(literal)) is False


@pytest.mark.parametrize("literal", ["8.8.8.8", "2606:4700:4700::1111", "93.184.216.34"])
def test_a_public_address_is_the_only_kind_that_passes(literal: str) -> None:
    assert cimd.target_allowed(ipaddress.ip_address(literal)) is True


def test_the_three_measured_gaps_would_each_pass_a_single_flag_check() -> None:
    """Why the rule is a conjunction and not one flag, asserted rather than believed.

    If a future Python moves one of these flags, this test says so before somebody
    simplifies the conjunction on the strength of a docstring.
    """
    nat64 = ipaddress.ip_address("64:ff9b::7f00:1")
    cgnat = ipaddress.ip_address("100.64.0.1")
    multicast = ipaddress.ip_address("224.0.0.1")

    assert nat64.is_private is False, "is_private alone would let NAT64 through"
    assert nat64.is_global is True, "is_global alone would let NAT64 through"
    assert cgnat.is_private is False, "is_private alone would let CGNAT through"
    assert multicast.is_global is True, "is_global alone would let multicast through"

    for addr in (nat64, cgnat, multicast):
        assert cimd.target_allowed(addr) is False


# --- the resolution, with the resolver as a parameter -----------------------------------


@pytest.mark.anyio
async def test_a_name_on_public_addresses_only_answers_with_their_literals() -> None:
    result = await cimd.resolve_addresses(HOST, PORT, resolver=answering("8.8.8.8", "1.1.1.1"))

    assert result == ["8.8.8.8", "1.1.1.1"]


@pytest.mark.anyio
async def test_a_mixed_answer_discards_the_whole_name_and_never_picks_the_good_one() -> None:
    """T-06-02: picking the public address makes the rule switchable by a DNS answer."""
    result = await cimd.resolve_addresses(HOST, PORT, resolver=answering("8.8.8.8", "127.0.0.1"))

    assert result is None


@pytest.mark.anyio
async def test_the_order_of_a_mixed_answer_changes_nothing() -> None:
    """The refused address first is the same refusal, which is what "any" means."""
    result = await cimd.resolve_addresses(HOST, PORT, resolver=answering("127.0.0.1", "8.8.8.8"))

    assert result is None


@pytest.mark.anyio
async def test_an_empty_answer_is_a_refusal_and_not_an_empty_list() -> None:
    assert await cimd.resolve_addresses(HOST, PORT, resolver=answering()) is None


@pytest.mark.anyio
async def test_a_resolver_that_raises_is_the_same_refusal() -> None:
    """A name nobody could resolve is not a name that resolved to something allowed."""
    resolver = failing(OSError("Name or service not known"))

    assert await cimd.resolve_addresses(HOST, PORT, resolver=resolver) is None


@pytest.mark.anyio
async def test_an_answer_that_is_not_an_address_is_a_refusal() -> None:
    """Fail closed on a resolver this code cannot take apart, as everywhere else here."""
    resolver = answering("not-an-address")

    assert await cimd.resolve_addresses(HOST, PORT, resolver=resolver) is None


@pytest.mark.anyio
async def test_an_empty_host_never_reaches_the_resolver() -> None:
    calls: list[tuple[str, int]] = []

    resolver = answering("8.8.8.8", calls=calls)

    assert await cimd.resolve_addresses("", PORT, resolver=resolver) is None
    assert calls == []


@pytest.mark.anyio
async def test_the_name_is_resolved_exactly_once() -> None:
    """The literals are what the fetch pins to, so a second resolution has no reason.

    Plan 06-02 turns this into the rebinding test with a resolver that answers twice
    differently; the count is the half of that claim which holds without a transport.
    """
    calls: list[tuple[str, int]] = []

    await cimd.resolve_addresses(HOST, PORT, resolver=answering("8.8.8.8", calls=calls))

    assert calls == [(HOST, PORT)]


@pytest.mark.anyio
async def test_a_refusal_records_its_kind_and_no_value_of_the_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-06-05: what is logged is the kind of the refusal, never the target."""
    caplog.set_level(logging.WARNING, logger="mcp_connector.oauth.cimd")

    await cimd.resolve_addresses(HOST, PORT, resolver=answering("8.8.8.8", "169.254.169.254"))

    assert caplog.records, "a refusal that leaves no trace at all is not the goal either"
    for record in caplog.records:
        assert HOST not in record.getMessage()
        assert "169.254.169.254" not in record.getMessage()


@pytest.mark.anyio
async def test_the_default_resolver_is_wired_and_answers_into_the_same_rule() -> None:
    """Without a resolver argument the name goes through this host's own resolver.

    ``localhost`` is the one name that resolves without a packet leaving the machine, and
    its answer is refused, which proves both halves at once: the default is reached, and
    what it returns is judged by :func:`target_allowed` and not waved through.
    """
    assert await cimd.resolve_addresses("localhost", PORT) is None


# --- the pinned fetch: where the request goes, and what stops it ------------------------


@pytest.mark.anyio
@respx.mock
async def test_the_request_goes_to_the_checked_address_with_the_original_name_in_tls() -> None:
    """T-06-07: the checked address is the connected address, and TLS keeps the real name.

    All three assertions on the sent request belong together. The address in the URL is
    what closes the rebinding window; the ``Host`` header is what makes a virtual host
    answer for the right site; and ``sni_hostname`` is what keeps the handshake and the
    certificate check on the name, so the pinning costs no certificate validation.
    """
    body = document()
    route = respx.get(PINNED_URL).mock(return_value=httpx.Response(200, json=body))

    result = await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP))

    assert result == body
    sent = route.calls.last.request
    assert sent.url.host == PUBLIC_IP
    assert sent.headers["host"] == NAME
    assert sent.extensions["sni_hostname"] == NAME
    assert sent.headers["accept"] == "application/json"


@pytest.mark.anyio
@respx.mock
async def test_an_ipv6_address_is_pinned_in_brackets_and_the_name_still_travels() -> None:
    """The bracket form is the one thing about v6 a URL cannot get wrong twice."""
    route = respx.get(PINNED_URL_V6).mock(return_value=httpx.Response(200, json=document()))

    result = await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IPV6))

    assert result is not None
    sent = route.calls.last.request
    assert sent.url.host == PUBLIC_IPV6
    assert sent.headers["host"] == NAME
    assert sent.extensions["sni_hostname"] == NAME


@pytest.mark.anyio
@respx.mock
async def test_one_fetch_resolves_the_name_exactly_once() -> None:
    """The half of the rebinding claim that a counter can state on its own."""
    calls: list[tuple[str, int]] = []
    respx.get(PINNED_URL).mock(return_value=httpx.Response(200, json=document()))

    await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP, calls=calls))

    assert calls == [(NAME, PORT)]


@pytest.mark.anyio
async def test_a_redirect_is_a_refusal_and_its_target_is_never_asked() -> None:
    """T-06-08: a 3xx is a second target nobody checked, so it is not a detour but a no."""
    with respx.mock(assert_all_called=False) as mock:
        first = mock.get(PINNED_URL).mock(
            return_value=httpx.Response(302, headers={"Location": "http://127.0.0.1/c.json"})
        )
        second = mock.get("http://127.0.0.1/c.json")

        result = await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP))

    assert result is None
    assert first.called is True
    assert second.called is False, "the redirect target was fetched, which is the whole hole"


@pytest.mark.anyio
@respx.mock
async def test_a_document_of_exactly_the_limit_is_still_a_document() -> None:
    """The boundary is inclusive, and the number in the assertion is the draft's own."""
    respx.get(PINNED_URL).mock(
        return_value=httpx.Response(200, content=sized_document(cimd.MAX_DOCUMENT_BYTES))
    )

    result = await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP))

    assert result is not None
    assert result["client_name"] == "A client that names itself"


@pytest.mark.anyio
@respx.mock
async def test_one_byte_over_the_limit_is_a_refusal() -> None:
    """T-06-09: 5121 bytes, and the read stops inside the chunk loop of bounded_response."""
    respx.get(PINNED_URL).mock(
        return_value=httpx.Response(200, content=sized_document(cimd.MAX_DOCUMENT_BYTES + 1))
    )

    assert await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP)) is None


@pytest.mark.anyio
@respx.mock
async def test_a_target_that_never_answers_is_a_refusal_and_not_an_exception() -> None:
    """A timeout is the failure this fetch has to survive silently: it sits in a page."""
    respx.get(PINNED_URL).mock(side_effect=httpx.ReadTimeout("the target did not answer"))

    assert await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP)) is None


@pytest.mark.anyio
@respx.mock
async def test_a_transport_error_is_the_same_refusal() -> None:
    """A refused connection, a broken certificate: one shape of no for all of them."""
    respx.get(PINNED_URL).mock(side_effect=httpx.ConnectError("connection refused"))

    assert await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP)) is None


@pytest.mark.parametrize("status", [302, 400, 401, 403, 404, 500, 503])
@pytest.mark.anyio
@respx.mock
async def test_no_answer_but_200_produces_a_document_and_none_of_them_raises(status: int) -> None:
    """D-37: ``fetch_document`` answers ``None`` on every one of these, never an exception."""
    respx.get(PINNED_URL).mock(return_value=httpx.Response(status, json=document()))

    assert await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP)) is None


@pytest.mark.anyio
async def test_a_client_id_that_is_not_https_costs_no_packet_and_no_resolution() -> None:
    """The first check of the chain is the one that is free (T-06-03)."""
    calls: list[tuple[str, int]] = []

    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PINNED_URL)

        result = await cimd.fetch_document(
            "http://example.com/c.json", resolver=answering(PUBLIC_IP, calls=calls)
        )

    assert result is None
    assert route.called is False
    assert calls == []


# --- the document's own rules ------------------------------------------------------------

#: Claude Code's real client id metadata document, fetched in this session on 2026-08-20 from
#: https://claude.ai/oauth/claude-code-client-metadata. It is here because it is the candidate
#: client of AUTH-08: a rule that refuses this document refuses the client this phase exists
#: for. Note that both return addresses are port less, which is what plan 06-03's port rule
#: is about.
CLAUDE_CODE_DOCUMENT = {
    "client_id": "https://claude.ai/oauth/claude-code-client-metadata",
    "client_name": "Claude Code",
    "client_uri": "https://claude.ai",
    "redirect_uris": ["http://localhost/callback", "http://127.0.0.1/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
}


def encoded(**overrides: Any) -> bytes:
    """The minimal document with these overrides, as the bytes a fetch would return."""
    return json.dumps(document(**overrides)).encode()


def without(key: str) -> bytes:
    """The minimal document with one property taken out again."""
    return json.dumps({k: v for k, v in document().items() if k != key}).encode()


def test_the_real_claude_code_document_passes_every_rule() -> None:
    """The candidate client of AUTH-08, measured and not imagined."""
    raw = json.dumps(CLAUDE_CODE_DOCUMENT).encode()

    result = cimd.validate_document(raw, str(CLAUDE_CODE_DOCUMENT["client_id"]))

    assert result == CLAUDE_CODE_DOCUMENT


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        (b"{not json at all", "a body that is not JSON"),
        (b"", "an empty body"),
        (b"\xff\xfe{}", "a body that is not even text"),
        (b'["a", "list"]', "a JSON array instead of an object"),
        (b'"a string"', "a JSON string instead of an object"),
        (b"7", "a JSON number instead of an object"),
        (without("client_id"), "no client_id"),
        (without("client_name"), "no client_name"),
        (without("redirect_uris"), "no redirect_uris"),
        (encoded(redirect_uris="http://127.0.0.1/callback"), "redirect_uris as a string"),
        (encoded(redirect_uris={"one": "http://127.0.0.1/cb"}), "redirect_uris as an object"),
        (encoded(client_id=f"{DOCUMENT_URL}/"), "a client_id one trailing slash away"),
        (encoded(client_id=DOCUMENT_URL.upper()), "a client_id in another case"),
        (encoded(client_id="https://other.example/c.json"), "somebody else's client_id"),
        (encoded(token_endpoint_auth_method="client_secret_basic"), "basic secret auth"),
        (encoded(token_endpoint_auth_method="client_secret_post"), "posted secret auth"),
        (encoded(token_endpoint_auth_method="client_secret_jwt"), "a secret signed JWT"),
    ],
)
def test_a_document_that_breaks_one_rule_is_refused(raw: bytes, why: str) -> None:
    """Each row is a rule that would be a claim without it (success criterion 2)."""
    assert cimd.validate_document(raw, DOCUMENT_URL) is None, why


@pytest.mark.parametrize("method", [None, "none", "private_key_jwt"])
def test_an_authentication_without_a_shared_secret_is_admissible(method: str | None) -> None:
    """A missing property means ``none``, and ``none`` is what a public client uses."""
    raw = (
        without("token_endpoint_auth_method")
        if method is None
        else encoded(token_endpoint_auth_method=method)
    )

    assert cimd.validate_document(raw, DOCUMENT_URL) is not None


@pytest.mark.anyio
@respx.mock
async def test_a_fetched_document_that_names_another_identifier_is_refused() -> None:
    """T-06-11 through the whole chain: the transport worked and the answer still is no."""
    respx.get(PINNED_URL).mock(
        return_value=httpx.Response(200, json=document(client_id="https://other.example/c.json"))
    )

    assert await cimd.fetch_document(DOCUMENT_URL, resolver=answering(PUBLIC_IP)) is None


# --- the boundaries of the module itself ------------------------------------------------


def test_no_log_call_of_this_module_takes_a_value_of_the_request() -> None:
    """The rule of provider.py:308-312, checked instead of promised.

    A log line is the easiest way for a foreign URL to reach a file somebody else reads,
    and the message texts alone cannot be trusted to stay value free while the module
    grows.
    """
    forbidden = {"value", "client_id", "host", "answer", "answers", "parsed", "literals"}
    tree = ast.parse(inspect.getsource(cimd))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if not isinstance(function, ast.Attribute):
            continue
        if not (isinstance(function.value, ast.Name) and function.value.id == "logger"):
            continue
        for argument in node.args:
            for inner in ast.walk(argument):
                assert not (isinstance(inner, ast.Name) and inner.id in forbidden), (
                    f"logger.{function.attr} takes {getattr(inner, 'id', '')}, "
                    "which is a value of the request"
                )


def test_the_two_limits_are_module_constants_without_a_switch() -> None:
    """T-06-06: a limit an administrator can weaken by accident is not a limit."""
    assert cimd.MAX_DOCUMENT_BYTES == 5120
    assert cimd.FETCH_TIMEOUT_SECONDS == 5.0
    assert "os.environ" not in inspect.getsource(cimd)


def test_the_size_limit_of_the_fetch_is_the_one_the_project_already_has() -> None:
    """06-02 imports the twin of ``bounded_body`` instead of counting bytes here (T-06-04)."""
    from mcp_connector.exapp.responses import bounded_response

    assert inspect.iscoroutinefunction(bounded_response)
