"""Environment parsing (D-11, D-12), base URL normalisation and mode selection.

Three credential modes exist and they are mutually exclusive, because a server that can
fall back from one identity source to another has no identity source at all:

===================  =========================================  ==================================
Mode                 Selected by                                Nextcloud credentials
===================  =========================================  ==================================
stdio                no transport headers exist at all          environment (D-11)
http_passthrough     headers present, no static bearer set      Basic credentials of the request
http_static_bearer   ``NC_MCP_STATIC_BEARER`` is set            environment, guarded by the bearer
===================  =========================================  ==================================

``select_mode`` is a pure function of the environment plus the request headers, so every
branch is testable without a server. The remaining helpers here feed the transport
hardening of ``entry_http`` (allowed hosts, DNS rebinding protection).
"""

import os
from collections.abc import Mapping
from typing import Literal
from urllib.parse import urlsplit

from .errors import ToolError
from .nextcloud.credentials import Credentials

ENV_URL = "NC_MCP_URL"
ENV_USER = "NC_MCP_USER"
ENV_APP_PASSWORD = "NC_MCP_APP_PASSWORD"

ENV_ALLOWED_HOSTS = "NC_MCP_ALLOWED_HOSTS"
ENV_STATIC_BEARER = "NC_MCP_STATIC_BEARER"
ENV_DISABLE_DNS_REBINDING = "NC_MCP_DISABLE_DNS_REBINDING_PROTECTION"
ENV_PUBLIC_URL = "NC_MCP_PUBLIC_URL"

Mode = Literal["stdio", "http_passthrough", "http_static_bearer"]

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
    if static_bearer(source):
        return "http_static_bearer"
    return "http_passthrough"


def static_bearer(env: Mapping[str, str] | None = None) -> str | None:
    """The configured static bearer, or ``None`` when the variable is unset or blank."""
    source = os.environ if env is None else env
    return (source.get(ENV_STATIC_BEARER) or "").strip() or None


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
