"""Environment parsing (D-11, D-12), base URL normalisation and mode selection.

Four credential modes exist and they are mutually exclusive, because a server that can
fall back from one identity source to another has no identity source at all:

===================  =========================================  ==================================
Mode                 Selected by                                Nextcloud credentials
===================  =========================================  ==================================
stdio                no transport headers exist at all          environment (D-11)
exapp                ``APP_ID`` and ``APP_SECRET`` are set      the user id in the AppAPI header
http_passthrough     headers present, no static bearer set      Basic credentials of the request
http_static_bearer   ``NC_MCP_STATIC_BEARER`` is set            environment, guarded by the bearer
===================  =========================================  ==================================

The AppAPI variables are the one group here without the ``NC_MCP_`` prefix: ``APP_ID``,
``APP_SECRET``, ``APP_VERSION``, ``AA_VERSION``, ``APP_HOST``, ``APP_PORT``,
``APP_PERSISTENT_STORAGE``, ``HP_SHARED_KEY``, ``HP_EXAPP_SOCK`` and ``NEXTCLOUD_URL``
are dictated by the AppAPI deploy daemon, which injects them into the container. Renaming
them here would mean renaming them in a component we do not own.

``select_mode`` is a pure function of the environment plus the request headers, so every
branch is testable without a server. The remaining helpers here feed the transport
hardening of ``entry_http`` (allowed hosts, DNS rebinding protection).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from .errors import ToolError
from .nextcloud.credentials import Credentials

ENV_URL = "NC_MCP_URL"
ENV_USER = "NC_MCP_USER"
ENV_APP_PASSWORD = "NC_MCP_APP_PASSWORD"  # noqa: S105 - the env var name, not a secret

ENV_ALLOWED_HOSTS = "NC_MCP_ALLOWED_HOSTS"
ENV_STATIC_BEARER = "NC_MCP_STATIC_BEARER"
ENV_DISABLE_DNS_REBINDING = "NC_MCP_DISABLE_DNS_REBINDING_PROTECTION"
ENV_PUBLIC_URL = "NC_MCP_PUBLIC_URL"

# The AppAPI deploy environment. The names come from AppAPI, see the module docstring.
ENV_APP_ID = "APP_ID"
ENV_APP_SECRET = "APP_SECRET"  # noqa: S105 - the env var name, not a secret
ENV_APP_VERSION = "APP_VERSION"
ENV_AA_VERSION = "AA_VERSION"
ENV_APP_HOST = "APP_HOST"
ENV_APP_PORT = "APP_PORT"
ENV_APP_PERSISTENT_STORAGE = "APP_PERSISTENT_STORAGE"
ENV_HP_SHARED_KEY = "HP_SHARED_KEY"  # the env var name, not a secret
ENV_HP_EXAPP_SOCK = "HP_EXAPP_SOCK"
ENV_NEXTCLOUD_URL = "NEXTCLOUD_URL"

Mode = Literal["stdio", "exapp", "http_passthrough", "http_static_bearer"]

#: Used as issuer and resource server URL in the static bearer mode. It is only ever a
#: self-reference for the RFC 9728 discovery document, never a place we send secrets to.
DEFAULT_PUBLIC_URL = "http://127.0.0.1:8765"

#: What the SDK allows when no allowlist is configured. Spelled out instead of relying on
#: the SDK default, because a silent default is what produces a 421 nobody can explain.
LOCALHOST_NAMES = ("127.0.0.1", "localhost", "[::1]")

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

REDIRECT_HINT = "Your Nextcloud URL redirects; use the final URL, including https and any subpath."

_URL_HINT = (
    f"Set {ENV_URL} to the full base URL of your Nextcloud, for example "
    "https://cloud.example.com or https://example.com/nextcloud."
)

_EXAPP_HINT = (
    f"{ENV_APP_ID}, {ENV_APP_SECRET}, {ENV_APP_VERSION} and {ENV_NEXTCLOUD_URL} are set by the "
    "AppAPI deploy daemon when it starts the container. A missing one means the process was "
    "started by hand: register the ExApp with 'occ app_api:app:register' and take the values "
    "from that registration."
)


@dataclass(frozen=True, slots=True, repr=False)
class ExAppSettings:
    """The AppAPI identity of this process: who we are and where Nextcloud lives.

    Masked like :class:`~mcp_connector.nextcloud.credentials.Credentials`: ``app_secret``
    is a bearer equivalent secret whose disclosure allows impersonating every user of the
    instance, so it never appears in a traceback or in the repr of a container (T-02-03).
    """

    app_id: str
    app_secret: str
    app_version: str
    aa_version: str
    base_url: str

    def __repr__(self) -> str:
        return (
            f"ExAppSettings(app_id={self.app_id!r}, app_version={self.app_version!r}, "
            f"aa_version={self.aa_version!r}, base_url={self.base_url!r}, app_secret='***')"
        )


def normalize_base_url(raw: str) -> str:
    """Strip whitespace and trailing slashes, keep a subpath, require http or https."""
    candidate = (raw or "").strip().rstrip("/")
    if not candidate:
        raise ToolError(message=f"{ENV_URL} is empty.", hint=_URL_HINT)

    parts = urlsplit(candidate)
    if parts.scheme not in ("http", "https"):
        raise ToolError(
            message=f"{ENV_URL} must start with http:// or https:// (got {candidate!r}).",
            hint=_URL_HINT,
        )
    if not parts.netloc:
        raise ToolError(
            message=f"{ENV_URL} has no host ({candidate!r}).",
            hint=_URL_HINT,
        )
    return candidate


def load_base_url(env: Mapping[str, str] | None = None) -> str:
    """The configured Nextcloud instance. Needed in every mode, including passthrough."""
    source = os.environ if env is None else env
    return normalize_base_url(_required(source, ENV_URL))


def load_stdio_credentials(env: Mapping[str, str] | None = None) -> Credentials:
    """Build credentials from the environment, naming any missing variable."""
    source = os.environ if env is None else env
    base_url = load_base_url(source)
    user = _required(source, ENV_USER)
    secret = _required(source, ENV_APP_PASSWORD)
    return Credentials(base_url=base_url, user=user, secret=secret)


def select_mode(
    env: Mapping[str, str] | None = None,
    *,
    headers: Mapping[str, str] | None = None,
) -> Mode:
    """Return the one credential mode that applies to this call.

    ``headers is None`` means the transport has none (stdio, in-memory client), and no
    environment variable can turn such a process into an HTTP mode.
    """
    source = os.environ if env is None else env
    if headers is None:
        return "stdio"
    # The ExApp mode wins over the static bearer on purpose: a process deployed by AppAPI
    # has APP_SECRET from the deploy environment, so a process that carries both is a
    # misconfiguration. entry_exapp rejects that combination at startup with exit code 2
    # instead of resolving it silently per request (D-27, no silent fallbacks).
    if exapp_configured(source):
        return "exapp"
    if static_bearer(source):
        return "http_static_bearer"
    return "http_passthrough"


def static_bearer(env: Mapping[str, str] | None = None) -> str | None:
    """The configured static bearer, or ``None`` when the variable is unset or blank."""
    source = os.environ if env is None else env
    return (source.get(ENV_STATIC_BEARER) or "").strip() or None


def exapp_configured(env: Mapping[str, str] | None = None) -> bool:
    """True when this process was deployed as an ExApp, by the same rule as the bearer.

    A blank value counts as unset: an empty ``APP_SECRET`` in a compose file is a typo,
    not a request to authenticate everyone.
    """
    source = os.environ if env is None else env
    app_id = (source.get(ENV_APP_ID) or "").strip()
    app_secret = (source.get(ENV_APP_SECRET) or "").strip()
    return bool(app_id) and bool(app_secret)


def exapp_settings(env: Mapping[str, str] | None = None) -> ExAppSettings:
    """Read the AppAPI deploy environment, naming any variable that is missing.

    ``AA_VERSION`` is the one optional value: HaRP writes a hard coded placeholder into
    that header anyway, and nothing in this project evaluates it (pitfall 8).
    """
    source = os.environ if env is None else env
    raw_url = (source.get(ENV_NEXTCLOUD_URL) or "").strip() or (source.get(ENV_URL) or "").strip()
    if not raw_url:
        raise ToolError(message=f"{ENV_NEXTCLOUD_URL} is not set.", hint=_EXAPP_HINT)
    return ExAppSettings(
        app_id=_required_exapp(source, ENV_APP_ID),
        app_secret=_required_exapp(source, ENV_APP_SECRET),
        app_version=_required_exapp(source, ENV_APP_VERSION),
        aa_version=(source.get(ENV_AA_VERSION) or "").strip(),
        base_url=normalize_base_url(raw_url),
    )


def public_url(env: Mapping[str, str] | None = None) -> str:
    """Public base URL of this MCP server, used for the bearer discovery document."""
    source = os.environ if env is None else env
    return (source.get(ENV_PUBLIC_URL) or "").strip().rstrip("/") or DEFAULT_PUBLIC_URL


def allowed_hosts(env: Mapping[str, str] | None = None) -> list[str]:
    """Parse ``NC_MCP_ALLOWED_HOSTS`` into an allowlist for the transport layer.

    Two entries per bare hostname (``example.com`` and ``example.com:*``), because the
    Host header carries the port whenever the client was given one, and an allowlist that
    only knows the bare name answers 421 to every real request (pitfall 6). An entry that
    already carries a port or a wildcard is taken verbatim: the operator meant it.
    """
    source = os.environ if env is None else env
    raw = (source.get(ENV_ALLOWED_HOSTS) or "").strip()
    names = [item.strip() for item in raw.split(",") if item.strip()] or list(LOCALHOST_NAMES)

    hosts: list[str] = []
    for name in names:
        for candidate in (name,) if _has_port(name) else (name, f"{name}:*"):
            if candidate not in hosts:
                hosts.append(candidate)
    return hosts


def dns_rebinding_protection(env: Mapping[str, str] | None = None) -> bool:
    """Whether the Host header check stays armed. Off only behind a trusted proxy."""
    source = os.environ if env is None else env
    value = (source.get(ENV_DISABLE_DNS_REBINDING) or "").strip().lower()
    return value not in _TRUE_VALUES


def _has_port(name: str) -> bool:
    """True for ``example.com:8765`` and ``[::1]:*``, false for ``[::1]``."""
    return ":" in name.rsplit("]", 1)[-1]


def _required_exapp(source: Mapping[str, str], name: str) -> str:
    """Like :func:`_required`, but with the hint an ExApp operator can act on."""
    value = (source.get(name) or "").strip()
    if not value:
        raise ToolError(message=f"{name} is not set.", hint=_EXAPP_HINT)
    return value


def _required(source: Mapping[str, str], name: str) -> str:
    value = (source.get(name) or "").strip()
    if not value:
        raise ToolError(
            message=f"{name} is not set.",
            hint=(
                f"Set {ENV_URL}, {ENV_USER} and {ENV_APP_PASSWORD} in the environment of the "
                "MCP server. Create the app password in Nextcloud under "
                "Settings, Security, Devices and sessions."
            ),
        )
    return value
