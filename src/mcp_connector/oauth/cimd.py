"""The fetch of a client id metadata document, and the boundaries that hold around it.

This module is the first place in this project where a request chooses the target of an
outbound request of ours. Every other call goes to the configured Nextcloud, because the
base URL comes from ``NC_MCP_URL`` and never from a request (phase 01 decision, T-01-08).
A client identifier URL is different by design: the draft makes the identifier itself the
address of the document, so the value that arrives at ``/authorize`` decides where this
process connects to. That is the reason this file is a module of its own and not four
helpers inside the provider.

:func:`fetch_document_and_lifetime` is the one boundary this module offers outwards.
Everything else is a step of it that is public only so a test can hold that step on its own.
There used to be a second projection next to it, ``fetch_document``, for a caller with
nowhere to keep a freshness window; no caller of this app ever was that caller, because the
one that writes the row is the one that owns the deadline, and an export whose only reader is
the test suite is dead code that reads as a contract (audit finding W-8).

Four deliberate settings, each with the reason it exists:

* ``MAX_DOCUMENT_BYTES``, five kilobytes - the draft's own recommendation, and the limit is
  enforced by :func:`mcp_connector.exapp.responses.bounded_response`, not by a second
  counter here (T-06-04).
* ``FETCH_TIMEOUT_SECONDS = 5.0`` for connect and read - the fetch sits inside a browser
  request of the consent page, where the ten seconds of the reference implementation read
  as a hung page.
* ``CACHE_MIN_SECONDS`` and ``CACHE_MAX_SECONDS``, five minutes and one hour - the bounds
  the draft leaves to the authorization server, around the cache header of the answer.
* None of them is an environment switch. A switch on a limit is a limit an administrator can
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
import json
import logging
import socket
from collections.abc import Awaitable, Callable, Sequence
from typing import Any
from urllib.parse import urlsplit

import httpx

from mcp_connector.exapp.responses import BodyTooLarge, BodyUnreadable, bounded_response
from mcp_connector.nextcloud.http import USER_AGENT, NoCookieJar

__all__ = [
    "CACHE_MAX_SECONDS",
    "CACHE_MIN_SECONDS",
    "FETCH_TIMEOUT_SECONDS",
    "MAX_DOCUMENT_BYTES",
    "AddressLookup",
    "cache_lifetime",
    "fetch_document_and_lifetime",
    "is_cimd_client_id",
    "resolve_addresses",
    "target_allowed",
    "validate_document",
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

#: The floor and the ceiling of the window a fetched document may be reused in. The draft
#: says an authorization server "SHOULD respect HTTP cache headers" and "MAY define its own
#: upper and/or lower bounds" (section 6.6), and the reference implementation of the draft
#: runs five minutes by default with an hour as its cap. So these two are that MAY: a floor,
#: because a document that says "never cache me" would otherwise turn every authorization
#: request of that client into an outbound request, and a ceiling, because a client that
#: changes its return addresses has to be able to reach this server again the same day.
CACHE_MIN_SECONDS = 300
CACHE_MAX_SECONDS = 3600

#: The properties without which a document says nothing: which client it is, what to call it
#: on the consent page, and where it may be sent back to.
_REQUIRED = ("client_id", "client_name", "redirect_uris")

#: Authentication methods built on a symmetric secret. They are refusals because there is no
#: channel over which such a secret could ever have been agreed: nothing registered, so
#: nothing was ever handed out. A document that names one of them is either confused about
#: what it is or asking this server to accept an authentication it cannot check (T-06-12).
_FORBIDDEN_AUTH = frozenset({"client_secret_post", "client_secret_basic", "client_secret_jwt"})

logger = logging.getLogger("mcp_connector.oauth.cimd")

#: What :func:`resolve_addresses` asks: a name and a port in, the addresses the name stands
#: for out. It is a parameter and not a module call, so the two answer resolver of the
#: rebinding test is a value a test passes in rather than a patched library function
#: (the injection form of ``tests/unit/test_oauth_provider.py:91-107``).
type AddressLookup = Callable[[str, int], Awaitable[Sequence[str]]]


class _Refused(Exception):
    """One of the refusals of the fetch, raised inside this module and never outside it.

    The shape exists because the fetch has seven ways to say no and they all mean the same
    thing to the caller, so a chain of return values would either lose the distinction
    anyway or spread it over five levels of ``if``. It stays private and it stops at
    :func:`fetch_document_and_lifetime`, which turns it into ``None``: fail closed is a return
    value on a request path here and never an exception (D-37, shared pattern A of
    06-PATTERNS.md),
    because the callers are request handlers in four endpoints.
    """


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
    which is the reason the registry's own address check refuses the same three: user info
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


def cache_lifetime(cache_control: str | None) -> int:
    """How long this answer may be reused, in seconds, inside our own two bounds.

    One header and not three. ``Cache-Control: max-age`` is the one an origin actually sends
    for a static JSON document, and it is a duration, so it needs no clock. ``Expires`` is a
    date that would have to be compared against the ``Date`` of the same answer, and both of
    them come from the host the identifier named: a comparison of two attacker chosen
    timestamps decides nothing, and getting it wrong decides it in the attacker's favour. So
    ``Expires`` alone reads as no usable header and the floor applies, which is the safe end
    of the range.

    ``no-store`` and ``no-cache`` are respected as far as our own floor: they end up at
    :data:`CACHE_MIN_SECONDS` rather than at zero, because a row for this client has to exist
    for the foreign key of ``flows`` and ``authorizations`` either way (pitfall 3), so "do not
    keep this" cannot mean "keep nothing" here. It means "keep it for the shortest window this
    server has", and the draft's MAY is what allows that.

    Never raises and never logs: a malformed header is not a value worth a line in a file
    somebody else reads, and the floor is the answer to all of them.
    """
    if not cache_control:
        return CACHE_MIN_SECONDS
    seconds = CACHE_MIN_SECONDS
    for directive in cache_control.lower().split(","):
        token = directive.strip()
        if token in ("no-store", "no-cache"):
            return CACHE_MIN_SECONDS
        if token.startswith("max-age="):
            try:
                seconds = int(token.removeprefix("max-age=").strip())
            except ValueError:
                return CACHE_MIN_SECONDS
    return max(CACHE_MIN_SECONDS, min(seconds, CACHE_MAX_SECONDS))


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


async def _fetch_pinned(url: httpx.URL, ip: str) -> tuple[bytes, int]:
    """The document, fetched from this address with the original name in TLS and ``Host``.

    The second half of the pair is how long the answer may be reused, read from the cache
    header of this very answer: the header exists only here, and passing the response object
    out of this function so that a caller could read it would hand a caller an open stream
    whose body limit this function is responsible for.

    **Why the address and not the name** (T-06-07). The address is the one
    :func:`resolve_addresses` checked, and handing ``httpx`` the host name instead would let
    it resolve a second time: between the check and the connection there would be a window
    in which the name means something else, which is what a rebinding attack is. That window
    is the documented bypass class of 2026 and it closed four Python projects' SSRF checks
    (CVE-2026-55391 in datamodel-code-generator, plus mlflow issue 24179, crewAI issue 6520
    and Prefect pull request 21591). The rejected alternative is therefore literally
    ``client.get(url)`` with the original host name: it passes every negative test that uses
    a static name and none that uses a resolver answering twice.

    ``sni_hostname`` is what makes the pinning free of a second cost: ``httpcore`` 1.0.9
    hands it to the TLS handshake as ``server_hostname``
    (``httpcore/_async/connection.py:107,151``), so certificate validation stays on the real
    name. A hand written socket or a custom resolver hook is exactly what loses that.

    The client is built here and shared with nothing. The process wide client of
    ``nextcloud/http.py`` carries the pool, the timeouts and the purpose of the way to our
    own Nextcloud, and a fetch into a foreign trust domain shares no connection pool with a
    path that carries credentials (T-06-14). What it does copy from that module is the
    posture: ``follow_redirects=False``, the timeout style, ``NoCookieJar`` and the one
    ``USER_AGENT`` of this project. What it does not copy is the per loop cache: this is one
    fetch per call and no process state (D-20).

    Every refusal is a :class:`_Refused`, including a status that is not 200: a 3xx is a
    second target nobody checked, so not following a redirect and refusing it are the same
    decision (T-06-08).
    """
    literal = f"[{ip}]" if ":" in ip else ip
    pinned = url.copy_with(host=literal)
    name = url.raw_host.decode("ascii")
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(FETCH_TIMEOUT_SECONDS, connect=FETCH_TIMEOUT_SECONDS),
        follow_redirects=False,
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
        headers={"User-Agent": USER_AGENT},
        cookies=NoCookieJar(),
    ) as client:
        request = client.build_request(
            "GET",
            pinned,
            headers={"Host": url.netloc.decode("ascii"), "Accept": "application/json"},
            extensions={"sni_hostname": name},
        )
        try:
            response = await client.send(request, stream=True)
        except Exception as exc:
            # A timeout, a refused connection, a certificate that does not match the name.
            # The kind is logged, no value of the request is.
            logger.warning("a document could not be fetched: %s", type(exc).__name__)
            raise _Refused from exc
        try:
            if response.status_code != 200:
                logger.warning("a document was refused: status %s", response.status_code)
                raise _Refused
            raw = await bounded_response(response, MAX_DOCUMENT_BYTES)
            return raw, cache_lifetime(response.headers.get("cache-control"))
        except BodyTooLarge as exc:
            logger.warning("a document was refused: it is larger than the limit")
            raise _Refused from exc
        except BodyUnreadable as exc:
            logger.warning("a document was refused: its body could not be read")
            raise _Refused from exc
        finally:
            await response.aclose()


async def fetch_document_and_lifetime(
    client_id: str, *, resolver: AddressLookup = _system_addresses
) -> tuple[dict[str, Any], int] | None:
    """The document behind a client identifier URL and its window, or ``None``.

    The one boundary outwards. The window is what :func:`cache_lifetime` read from the
    answer, and it is handed out next to the document rather than applied here, because this
    module knows nothing about where a document is kept: the caller that writes the row is
    the caller that owns the deadline (``provider.py``, plan 06-05).

    The order is the one the diagram of 06-RESEARCH.md draws, and each step is where it is
    for a reason:

    1. the form of the identifier, because a refusal here costs no packet at all (T-06-03);
    2. the resolution, exactly once, and one refused address discards the whole name;
    3. the fetch, pinned to the first checked address;
    4. the document's own rules.

    **Exactly one resolution per call.** The checked address is the connected address, which
    is the whole content of the rebinding defence and the reason the literals travel from
    step 2 into step 3 instead of the name travelling into ``httpx``.

    **No negative cache.** The draft is literal about it: an authorization server "MUST NOT
    cache error responses" and "MUST NOT cache documents which are invalid or malformed". So
    a second call after a 500 or after a broken document really goes out again, and the
    throttling that a flood of unknown URL identifiers needs lives where throttling already
    lives: ``oauth/throttle.py`` limits ``CLASS_AUTHORIZE_START``, which is the route this
    fetch hangs from. Whether that class is enough or a ninth one is needed is a question
    for a measurement, and this plan does not invent one on a guess (T-06-10).

    The resolver travels on as a keyword so a test can hand in one that answers twice
    differently; no library function is patched anywhere.
    """
    identifier = (client_id or "").strip()
    if not is_cimd_client_id(identifier):
        return None
    try:
        url = httpx.URL(identifier)
        name = url.raw_host.decode("ascii")
        port = url.port or 443
    except Exception as exc:
        # The form check passed on ``urlsplit`` and this library disagrees about the same
        # string. Two libraries that do not agree about a target is a refusal, not a choice.
        logger.warning("a document target could not be taken apart: %s", type(exc).__name__)
        return None
    addresses = await resolve_addresses(name, port, resolver=resolver)
    if not addresses:
        return None
    try:
        raw, lifetime = await _fetch_pinned(url, addresses[0])
    except _Refused:
        return None
    document = validate_document(raw, identifier)
    return None if document is None else (document, lifetime)


def validate_document(raw: bytes, client_id: str) -> dict[str, Any] | None:
    """The document these bytes are, or ``None``. Never raises into a handler (D-37).

    The order below is the specification's order, and the four MUSTs are its four MUSTs:

    1. valid JSON, and an object rather than an array or a number;
    2. the required properties are present;
    3. the document's own ``client_id`` is the URL it was fetched from;
    4. the ``token_endpoint_auth_method`` is not one built on a shared symmetric secret.

    **Why step 3 compares byte for byte** (T-06-11). RFC 3986 section 6.2.1 calls this simple
    string comparison, and it is the same rule this project already applies to the ``issuer``
    of its own metadata document (``metadata.py``, where the configured value wins over the
    library's normalised one for exactly this reason). Normalising before comparing would
    hand an attacker the difference between the two spellings: a document served at one URL
    could then claim an identity that is a trailing slash, an escaped character or a default
    port away, and every later decision in this server keys off that identity.

    **What is deliberately not here.** No property of the document is interpreted, rendered
    or put into a URL by this function, and ``logo_uri`` in particular is not read at all.
    Fetching it would be a second outbound request into a domain nobody checked and a cross
    domain tracking channel for every consent page this server shows (draft section 6.7,
    T-06-13). The omission is written down so it is not later read as a gap.

    ``redirect_uris`` is checked for being a list and is **not** filtered here. The rule of
    D-35 is applied in ``provider.py`` through the registry's own address check, the same one
    the registration path applies, and a second filtering place would be a second truth about
    what this server accepts.

    What is logged is the step that refused, never a value of the document: it arrived from a
    foreign host over a connection a stranger's identifier chose.
    """
    try:
        document = json.loads(raw)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        logger.warning("a document was refused: it is not valid JSON")
        return None
    if not isinstance(document, dict):
        logger.warning("a document was refused: its top level is not an object")
        return None
    if any(key not in document for key in _REQUIRED):
        logger.warning("a document was refused: a required property is missing")
        return None
    if document["client_id"] != client_id:
        logger.warning("a document was refused: it names an identifier it was not fetched from")
        return None
    if document.get("token_endpoint_auth_method", "none") in _FORBIDDEN_AUTH:
        logger.warning("a document was refused: it asks for an authentication with a secret")
        return None
    if not isinstance(document.get("redirect_uris"), list):
        logger.warning("a document was refused: its return addresses are not a list")
        return None
    return document
