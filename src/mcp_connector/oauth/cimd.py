"""The two boundaries of a client id metadata document fetch that need no network at all:
the form of the identifier, and the class of the address it resolves to.

This module is the first place in this project where a request chooses the target of an
outbound request of ours. Every other call goes to the configured Nextcloud, because the
base URL comes from ``NC_MCP_URL`` and never from a request (phase 01 decision, T-01-08).
A client identifier URL is different by design: the draft makes the identifier itself the
address of the document, so the value that arrives at ``/authorize`` decides where this
process connects to. That is the reason this file is a module of its own and not three
helpers inside the provider.

Three deliberate settings, each with the reason it exists:

* ``MAX_DOCUMENT_BYTES``, five kilobytes - the draft's own recommendation, and the limit is
  enforced by :func:`mcp_connector.exapp.responses.bounded_response`, not by a second
  counter here (T-06-04).
* ``FETCH_TIMEOUT_SECONDS = 5.0`` for connect and read - the fetch sits inside a browser
  request of the consent page, where the ten seconds of the reference implementation read
  as a hung page.
* Neither is an environment switch. A switch on a limit is a limit an administrator can
  weaken by accident, and an accident is what this whole file exists against (open
  question 5 of the research, T-06-06).

Fail closed is a return value here and never an exception (D-37): all three functions
answer with ``False`` or ``None``, because their callers are request handlers and an
exception out of one of them would be a new failure shape in four endpoints. What is logged
is the kind of a refusal and never a value of the request (the rule of
``provider.py:308-312``), because the identifier is a foreign URL and the host it names is
an attacker's choice.
"""

import asyncio
import ipaddress
import logging
import socket
from collections.abc import Awaitable, Callable, Sequence
from urllib.parse import urlsplit

__all__ = [
    "FETCH_TIMEOUT_SECONDS",
    "MAX_DOCUMENT_BYTES",
    "AddressLookup",
    "is_cimd_client_id",
    "resolve_addresses",
    "target_allowed",
]

#: "The recommended maximum response size for client metadata documents is 5 kilobytes"
#: (draft-ietf-oauth-client-id-metadata-document-00, section 6.6), quoted rather than
#: rounded. The read stops inside the chunk loop of ``bounded_response``, so a host that
#: answers a hundred megabytes costs this process five kilobytes of memory.
MAX_DOCUMENT_BYTES = 5120

#: Connect and read alike. The reference implementation uses ten seconds, and this project
#: already runs ``connect=5.0`` in ``nextcloud/http.py``; a fetch that hangs here hangs the
#: consent page of a user who is waiting for a browser to answer.
FETCH_TIMEOUT_SECONDS = 5.0

logger = logging.getLogger("mcp_connector.oauth.cimd")

#: What :func:`resolve_addresses` asks: a name and a port in, the addresses the name stands
#: for out. It is a parameter and not a module call, so the two answer resolver of the
#: rebinding test is a value a test passes in rather than a patched library function
#: (the injection form of ``tests/unit/test_oauth_provider.py:91-107``).
type AddressLookup = Callable[[str, int], Awaitable[Sequence[str]]]


def is_cimd_client_id(value: str) -> bool:
    """Whether this string is a client identifier URL the draft admits, before any request.

    The draft is quoted rather than paraphrased: "Client identifier URLs MUST have an
    'https' scheme, MUST contain a path component, MUST NOT contain single-dot or
    double-dot path segments, MUST NOT contain a fragment component and MUST NOT contain a
    username or password." A query string is a SHOULD NOT and a port is a MAY, so both are
    tolerated here and neither is invented as a refusal we could not defend.

    **Why this is stricter than the SDK's own check.** ``is_valid_client_metadata_url`` in
    ``mcp/client/auth/utils.py`` asks two questions, https and a path that is not the root.
    That is enough for a client validating a URL it configured itself, and not enough for a
    server deciding whether to make an outbound request on a stranger's behalf: here the
    string is the target, and every refusal below is a target this process then never
    connects to. The refusal costs no packet, which is what makes it the first check of the
    chain and not the last (T-06-03).

    Three of the refusals are ways to smuggle a target past a reader rather than mistakes,
    which is the reason ``registry.redirect_uri_allowed`` refuses the same three: user info
    renders as the host in more than one client, a fragment is where a value hides from a
    server log, and a dot segment lets one document URL stand for another path entirely.

    The value is never logged. It is the input of a public route and a host of an
    attacker's choosing, and the caller has the string anyway.
    """
    parts = urlsplit((value or "").strip())
    if parts.scheme != "https":
        return False
    if parts.fragment or parts.username or parts.password:
        return False
    path = parts.path
    if not path or path == "/":
        return False
    if any(segment in (".", "..") for segment in path.split("/")):
        return False
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        # A malformed host or port. An address this library cannot take apart is not one
        # this server and a remote host would agree about either.
        return False
    if not host:
        return False
    return port is None or 0 < port <= 65535


def target_allowed(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Whether an outbound request of ours may go to this address. Fail closed.

    **One flag is not enough, and this is measured and not assumed** (06-RESEARCH.md,
    pattern 3, against the Python 3.13.13 of this project). Three addresses in that
    measurement are the reason this is a conjunction of seven questions:

    * ``100.64.0.1`` (carrier grade NAT) is **not** ``is_private``. ``is_global`` is False
      for it, and that is the only flag that holds it.
    * ``64:ff9b::7f00:1`` (NAT64 embedding 127.0.0.1) is **not** ``is_private`` either, and
      ``is_global`` is **True** for it. Only ``is_reserved`` holds it.
    * ``224.0.0.1`` (multicast) is ``is_global`` **True**. Only ``is_multicast`` holds it.

    So neither ``is_private`` alone nor ``is_global`` alone is a boundary, and anybody who
    later simplifies this to one flag reopens one of the three. The v4 mapped form is
    unpacked first: ``::ffff:127.0.0.1`` already reads as private in this version, and
    unpacking makes the intent readable and covers a version where it does not.

    Nothing is logged here. The address is a value of the request by way of a resolver, and
    the caller records the kind of its refusal.
    """
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped
    if not addr.is_global:
        return False
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


async def _system_addresses(host: str, port: int) -> list[str]:
    """The default resolver: what this host's own resolver says, TCP records only.

    ``SOCK_STREAM`` narrows the answer to the records a connection could use, which is what
    keeps one name from producing the same address three times over three socket types.

    The call goes through the running event loop rather than through ``anyio.getaddrinfo``,
    which is the same ``loop.getaddrinfo`` underneath on the asyncio backend this project
    runs on. The reason is the dependency policy of ``docs/dependency-audit.md``: a package
    this code imports directly is declared directly, and ``anyio`` is in the lock as a
    transitive dependency of the SDK. Importing it here would either break that policy or
    require a direct dependency, an audit entry and an owner sign off for a call the
    standard library already offers.
    """
    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return [str(record[4][0]) for record in records]


async def resolve_addresses(
    host: str, port: int, *, resolver: AddressLookup = _system_addresses
) -> list[str] | None:
    """Every address this name stands for, or ``None`` if any one of them is refused.

    **Why one bad address discards the whole name** (T-06-02). A function that picked the
    good address out of a mixed answer would turn the rule into something a DNS answer can
    switch off: a name that resolves to ``8.8.8.8`` and to ``127.0.0.1`` would be fetched
    from the public address today and from the loopback one as soon as the order of the
    answer changes, and both times the check would have said yes. So a mixed answer is a
    refusal, and the negative test of that is the one that separates this from the
    implementations the 2026 CVEs were written about.

    Empty answers and a resolver that raises are the same refusal, for the reason D-37
    gives everywhere else here: a name nobody could resolve is not a name that resolved to
    something safe.

    The returned literals are what the fetch of plan 06-02 pins its connection to. They are
    the addresses that were checked, never the name again: resolving a second time inside
    ``httpx`` is exactly the window between check and use that pinning closes.

    The resolver is a parameter with a default rather than a module level call, so a test
    can hand in a resolver that answers twice differently without patching a library.
    """
    if not host:
        return None
    try:
        answers = await resolver(host, port)
    except Exception as exc:
        # A name that cannot be resolved is not a name that resolved to something allowed.
        # The kind of the failure is logged, no value of the request is.
        logger.warning("a document target did not resolve: %s", type(exc).__name__)
        return None
    if not answers:
        logger.warning("a document target resolved to no address at all")
        return None
    literals: list[str] = []
    for answer in answers:
        try:
            parsed = ipaddress.ip_address(str(answer))
        except ValueError:
            logger.warning("a resolver answered something that is not an address")
            return None
        if not target_allowed(parsed):
            # Not "take the good one": see the docstring. One refused address ends the
            # whole name, and the message says that much and nothing about the target.
            logger.warning("a document target was refused: an address of it is not public")
            return None
        literals.append(str(parsed))
    return literals
