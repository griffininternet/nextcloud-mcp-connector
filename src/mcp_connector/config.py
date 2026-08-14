"""Environment parsing (D-11) and base URL normalisation.

Only the stdio path is evaluated in this plan. ``NC_MCP_ALLOWED_HOSTS`` and
``NC_MCP_STATIC_BEARER`` are declared here so the names are fixed from day one, but plan
04 gives them behaviour: a half-read variable is worse than an unread one.
"""

import os
from collections.abc import Mapping
from urllib.parse import urlsplit

from .errors import ToolError
from .nextcloud.credentials import Credentials

ENV_URL = "NC_MCP_URL"
ENV_USER = "NC_MCP_USER"
ENV_APP_PASSWORD = "NC_MCP_APP_PASSWORD"

# Reserved names, evaluated in plan 04 (Streamable HTTP).
ENV_ALLOWED_HOSTS = "NC_MCP_ALLOWED_HOSTS"
ENV_STATIC_BEARER = "NC_MCP_STATIC_BEARER"

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


def load_stdio_credentials(env: Mapping[str, str] | None = None) -> Credentials:
    """Build credentials from the environment, naming any missing variable."""
    source = os.environ if env is None else env
    base_url = normalize_base_url(_required(source, ENV_URL))
    user = _required(source, ENV_USER)
    secret = _required(source, ENV_APP_PASSWORD)
    return Credentials(base_url=base_url, user=user, secret=secret)


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
