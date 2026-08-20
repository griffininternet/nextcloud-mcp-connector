"""The two boundaries of the document fetch that hold without a network.

Nothing here goes to the net, and this file does not even mock one: the three functions
under test are pure calls plus one resolver that is a parameter, so the negative catalogue
of AUTH-09 runs as fast as a lint. That is the point of splitting them out of the fetch
(plan 06-01): a refusal that needs no packet is a refusal that stands before the first one.

The address catalogue is the measurement of 06-RESEARCH.md, pattern 3, against the Python
3.13.13 of this project. Three of its rows exist to hold a specific mistake, and one test
below asserts the measurement itself so a future Python that changes one of those flags
fails here and not in production: 100.64.0.1 and 64:ff9b::7f00:1 are not ``is_private``,
and 224.0.0.1 is ``is_global``.
"""

import ast
import inspect
import ipaddress
import logging

import pytest

from mcp_connector.oauth import cimd

HOST = "metadata.attacker.example"
PORT = 443


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
