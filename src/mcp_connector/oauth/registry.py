"""The admin switches of AUTH-07, read once into one object every check asks.

**Why a policy object and not a condition.** The trap of this requirement has a number in
the research (pitfall 9): whoever checks the allowlist at ``/register`` only has built a
door that locks after the visitor is inside. A client that was blocked afterwards keeps
authorizing and keeps refreshing until its token expires on its own. D-35 therefore names
four places where the same question is asked, and this module is the answer all four share:

1. ``register_client`` refuses a registration that the switch forbids (this plan),
2. ``get_client`` refuses a blocked, unlisted or expired client, which covers ``/authorize``,
   ``/token`` and ``/revoke`` alike because all three load their client through it (this plan),
3. ``exchange_authorization_code`` and ``exchange_refresh_token`` refuse a client that was
   blocked in the middle of a running flow (plan 03-06 and 03-07),
4. ``verify_token`` refuses an access token that was issued before the block (plan 03-06).

**Why ``cimd_enabled`` is derived and not only read.** The fourth switch decides whether a
client may identify itself with the URL of its own metadata document instead of registering
(CIMD, plan 06-05). It is a switch of its own because the MCP specification 2026-07-28 makes
that the preferred way and dynamic registration the legacy one, so an administrator whose
network forbids outbound requests must be able to close the new way without losing the old
one. But it is derived with ``and`` from the registration switch, because the owner
directive of this phase is that a disabled dynamic registration must not be circumventable
through CIMD: whoever switches registration off meant "no clients that sign themselves up",
not "no RFC 7591 clients". Both ways therefore pass the same four enforcement points, and
the CIMD way cannot outlive the switch that closed the other one.

**Why the allowlist mode with an empty list closes everything.** An administrator who
switches the mode on and forgets the list did not mean "allow everyone"; they meant to
close the door and have not named an exception yet. Fail closed is the owner directive of
this phase, and this is the one place where it is a single line of code.

**Why an entry may be a redirect URI.** A dynamically registered client gets a random id
from the SDK, which an administrator cannot know in advance. The address the client is sent
back to is the stable, published property of a connector (Claude.ai and ChatGPT each have
exactly one), so a list of allowed redirect URIs is the form an administrator can actually
write down before the first client ever connects.

The shape follows ``config.py``, down to the reasons: every variable name is a module
constant, a blank value counts as unset because an empty value in a compose file is a typo,
and a comma separated list is split, stripped and deduplicated instead of trusting a
default nobody wrote down.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit

from .store import IDLE_CLIENT_TTL, UNUSED_CLIENT_TTL

__all__ = [
    "ENV_ALLOWED_CLIENTS",
    "ENV_ALLOWLIST_ONLY",
    "ENV_CIMD",
    "ENV_DCR",
    "IDLE_REGISTRATION_TTL",
    "LOOPBACK_HOSTS",
    "UNUSED_REGISTRATION_TTL",
    "ClientPolicy",
    "client_policy",
    "loopback_match",
    "redirect_uri_allowed",
]

#: Dynamic client registration, globally. On in the shipped state, because success criteria
#: 1 and 2 are about connecting Claude.ai and ChatGPT without an administrator (D-35).
ENV_DCR = "NC_MCP_OAUTH_DCR"

#: Only explicitly listed clients may authorize. Off in the shipped state.
ENV_ALLOWLIST_ONLY = "NC_MCP_OAUTH_ALLOWLIST_ONLY"

#: The list itself: client ids or redirect URIs, separated by commas.
ENV_ALLOWED_CLIENTS = "NC_MCP_OAUTH_ALLOWED_CLIENTS"

#: Client id metadata documents, the way a client identifies itself by the URL of its own
#: published document instead of registering. On in the shipped state, because the MCP
#: specification 2026-07-28 makes this the preferred way and dynamic registration the legacy
#: one. Switching it off does not switch registration off; switching registration off does
#: switch this off, which is the fail closed direction of the owner directive.
ENV_CIMD = "NC_MCP_OAUTH_CIMD"

#: The values of ``config.py``, in both directions. The negative list exists because
#: ``NC_MCP_OAUTH_DCR`` is the first switch of this project whose default is on: the other
#: ones only had to recognise the value that arms them.
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})

#: The addresses the OAuth 2.1 security guidance exempts from the https rule, because a
#: native client on a desktop has no certificate for its own callback (D-35). ``urlsplit``
#: reports the IPv6 host without its brackets, so the set carries the unbracketed form.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

#: The two windows a registration lives in. The numbers belong to the store, which is what
#: sweeps with them; they are named here as well so the enforcement point and the sweep
#: cannot drift apart and so plan 03-07 does not invent a second twenty four hours.
UNUSED_REGISTRATION_TTL = UNUSED_CLIENT_TTL
IDLE_REGISTRATION_TTL = IDLE_CLIENT_TTL

logger = logging.getLogger("mcp_connector.oauth.registry")


@dataclass(frozen=True, slots=True, repr=False)
class ClientPolicy:
    """What an administrator decided, as one immutable value the whole phase reads.

    Immutable for the same reason the credential objects of phase 1 are: a policy that a
    request handler could change is a policy that one bug turns off for every later
    request. It is built once per application from the deploy environment.

    The repr counts the entries instead of naming them. Which assistants an institution
    connects is customer data, and a policy object ends up in a log record the moment
    somebody adds a debug line to a handler (T-02-03, the masking rule of this project).
    """

    dcr_enabled: bool
    allowlist_only: bool
    allowed: tuple[str, ...]
    cimd_enabled: bool

    def __repr__(self) -> str:
        return (
            f"ClientPolicy(dcr_enabled={self.dcr_enabled!r}, "
            f"allowlist_only={self.allowlist_only!r}, allowed={len(self.allowed)} entries, "
            f"cimd_enabled={self.cimd_enabled!r})"
        )

    def listed(self, client_id: str, redirect_uris: Sequence[str] = ()) -> bool:
        """Whether an administrator named this client, by id or by return address.

        Asked separately from :meth:`allows` because the consent screen needs this
        question and not the other one: a client that registered itself and is on no list
        is shown as unverified even while the allowlist mode is off, which is the shipped
        state (03-UI-SPEC.md, S3, T-03-42).
        """
        if client_id and client_id in self.allowed:
            return True
        return any(uri in self.allowed for uri in redirect_uris)

    def allows(self, client_id: str, redirect_uris: Sequence[str] = ()) -> bool:
        """Whether this client may pass the enforcement point at all.

        Without the allowlist mode this is true for everyone, which is what makes the
        shipped state plug and play. With the mode on it is the membership question, and
        an empty list therefore refuses everything.
        """
        if not self.allowlist_only:
            return True
        return self.listed(client_id, redirect_uris)


def client_policy(env: Mapping[str, str] | None = None) -> ClientPolicy:
    """Read the switches. The environment is a parameter, as everywhere here.

    Three of the four are read, the fourth is derived. ``cimd_enabled`` is the CIMD switch
    **and** the registration switch, because the locked decision of this phase reads "a
    disabled dynamic registration must not be circumventable through CIMD". An
    administrator who closed the door for clients that sign themselves up closed it for
    both spellings of that, and the explicit ``on`` of the newer switch does not reopen it.
    The other direction stays open: CIMD alone can be switched off, for instance on an
    instance whose network forbids the outbound request the document fetch needs.

    ``_switch`` does the parsing for all of them, unchanged. It already knows the switch
    whose default is on, the blank value that counts as unset and the typo that keeps the
    default and says so; a second parser would be a second truth.
    """
    dcr = _switch(env, ENV_DCR, default=True)
    return ClientPolicy(
        dcr_enabled=dcr,
        allowlist_only=_switch(env, ENV_ALLOWLIST_ONLY, default=False),
        allowed=_entries(env, ENV_ALLOWED_CLIENTS),
        cimd_enabled=_switch(env, ENV_CIMD, default=True) and dcr,
    )


def redirect_uri_allowed(value: str) -> bool:
    """Whether this address may be registered as a return target (D-35).

    The SDK compares a redirect URI of a request against the registered ones exactly, so
    this function is about what may be registered in the first place, and it is the check
    the SDK does not bring: https, with the loopback exception the specification grants
    native clients, and nothing else.

    Three refusals are worth naming, because each of them is a way to smuggle a target
    past a reader rather than a mistake: a URL with credentials in it renders as the host
    of its user info part in more than one client, a fragment is forbidden for a redirect
    URI by RFC 6749 and is where a token would be hidden from a server log, and a host
    like ``127.0.0.1.evil.example`` reads as loopback to a human and resolves to whatever
    its owner wants.
    """
    parts = urlsplit((value or "").strip())
    if parts.scheme not in ("https", "http"):
        return False
    if parts.fragment:
        return False
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        # A malformed host or port. An address this library cannot take apart is not one
        # a browser and this server would agree about either.
        return False
    if not host or parts.username or parts.password:
        return False
    if port is not None and not 0 < port <= 65535:
        return False
    if parts.scheme == "https":
        return True
    return host.lower() in LOOPBACK_HOSTS


def loopback_match(requested: str, registered: Sequence[str]) -> str | None:
    """The registered address this loopback request matches, port aside (RFC 8252 7.3).

    The specification's word is MUST, not MAY: "The authorization server MUST allow any
    port to be specified at the time of the request for loopback IP redirect URIs, to
    accommodate clients that obtain an available ephemeral port from the operating system at
    the time of the request." A native client takes whatever port the operating system hands
    it, so a server that compares the port refuses the client over a property the client
    cannot control.

    Measured reason this exists: Claude Code publishes ``http://localhost/callback`` and
    ``http://127.0.0.1/callback`` in its client id metadata document, both without a port,
    and arrives with ``http://localhost:3118/callback``.

    Every relaxation is named, and there is exactly one:

    * **Only the port is free.** Scheme, host, path and query are compared exactly, the host
      case insensitively as in :func:`redirect_uri_allowed`. A host change is not a port
      change: ``localhost`` against ``127.0.0.1`` stays a refusal, because the two names
      resolve through different mechanisms and a client that publishes both can send either.
    * **Only loopback is this function's business.** A request whose host is not in
      :data:`LOOPBACK_HOSTS` gets ``None``, and the exact comparison of the SDK stands. That
      set is the consistent one because D-35 already lets those three hosts be registered;
      section 7.3 names only the IP literals and section 8.3 advises against the name, but
      the client this rule exists for sends the name, so a literal reading would leave it
      out.
    * **A fragment, user info or an address this library cannot take apart is a refusal**,
      on both sides of the comparison, with the same ``try/except ValueError`` around
      ``hostname`` and ``port`` as the neighbour above. The scheme is compared and not
      restricted: which schemes may be registered at all is D-35's question, asked in
      :func:`redirect_uri_allowed`, and this function does not become a second gate for it.

    Nothing of the checked value is logged, and nothing is written: the anti pattern here is
    to put the requested address into the client's ``redirect_uris`` on a match. That turns
    a comparison into a registration, grows the row on every run, and hands whoever holds a
    loopback port a permanent entry.
    """
    asked = urlsplit((requested or "").strip())
    host = _comparable_host(asked)
    if host is None or host not in LOOPBACK_HOSTS:
        return None
    for candidate in registered:
        known = urlsplit((candidate or "").strip())
        known_host = _comparable_host(known)
        if known_host is None or known_host != host:
            continue
        exact = (known.scheme, known.path, known.query)
        if exact == (asked.scheme, asked.path, asked.query):
            return candidate
    return None


def _comparable_host(parts: SplitResult) -> str | None:
    """The lower case host of an address that may be compared at all, or ``None``.

    One helper for both sides of :func:`loopback_match`, so that a refusal cannot be
    forgotten on the registered side: an entry written with user info or a fragment is
    refused there for the same reason it is refused for a request.
    """
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        # A malformed host or port, the reading of ``redirect_uri_allowed``: an address this
        # library cannot take apart is not one a browser and this server would agree about.
        return None
    if not host or parts.fragment or parts.username or parts.password:
        return None
    if port is not None and not 0 < port <= 65535:
        return None
    return host.lower()


def _switch(env: Mapping[str, str] | None, name: str, *, default: bool) -> bool:
    """One switch, with a blank value counting as unset and a typo counting as nothing.

    A value this function does not know keeps the default and says so in the log. Both
    other readings are worse: guessing "on" would arm a switch nobody armed, and guessing
    "off" would disable dynamic registration on a typo, which is the outage an
    administrator would look for everywhere except in a misspelled variable.
    """
    source = {} if env is None else env
    value = (source.get(name) or "").strip().lower()
    if not value:
        return default
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    logger.warning(
        "%s is set to a value that is neither on nor off, so it keeps its default (%s). "
        "The values this switch understands are %s and %s.",
        name,
        default,
        ", ".join(sorted(_TRUE_VALUES)),
        ", ".join(sorted(_FALSE_VALUES)),
    )
    return default


def _entries(env: Mapping[str, str] | None, name: str) -> tuple[str, ...]:
    """Split, strip, drop the blanks, keep the first of a duplicate, keep the order.

    Order preserving instead of a set, so the repr count and any later admin view show the
    list the administrator wrote rather than a hash order (the rule of ``allowed_hosts``).
    """
    source = {} if env is None else env
    raw = (source.get(name) or "").strip()
    entries: list[str] = []
    for item in raw.split(","):
        candidate = item.strip()
        if candidate and candidate not in entries:
            entries.append(candidate)
    return tuple(entries)
