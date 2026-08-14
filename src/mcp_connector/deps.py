"""Credential resolution per tool call: the one channel the identity may come from.

Why a request header is allowed to carry credentials here, although the SDK docstring
warns "never treat one as an identity assertion": we do not. This server never decides
who the caller is, and it never grants anything based on the header. It forwards the
Basic credentials unchanged to the configured Nextcloud, and Nextcloud authenticates
them. That is the whole difference between a passthrough and a confused deputy
(threat T-01-23), and it is why no tool has a user parameter (threat T-01-12).

Three rules that follow from D-12 and pitfall 8, all of them load bearing:

* no caching of credentials anywhere, they live for the duration of one call
* no auth retry, because Nextcloud counts failures per source IP and a remote MCP
  server is one IP for many users
* no logging of the header, not even on DEBUG, not even truncated (threat T-01-21)

The static bearer mode is the only mode that configures the SDK auth layer, and it
configures ``auth=`` and ``token_verifier=`` together, because the SDK raises
``ValueError`` in the constructor when only one of them is set (pitfall 2).
"""

import base64
import binascii
import secrets
from collections.abc import Mapping
from typing import Any

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_REQUEST

from . import config
from .config import load_stdio_credentials
from .nextcloud import NcClients
from .nextcloud.credentials import Credentials
from .nextcloud.http import shared_client

__all__ = [
    "MCPError",
    "StaticBearerVerifier",
    "build_auth",
    "resolve_clients",
    "resolve_credentials",
]

#: Client id reported for the single deployment identity of the static bearer mode.
STATIC_BEARER_CLIENT_ID = "nc-mcp-static-bearer"

_BASIC_HINT = (
    "Send an Authorization header with Basic credentials: base64 of "
    "'<nextcloud-user>:<app-password>'. Create the app password in Nextcloud under "
    "Settings, Security, Devices and sessions."
)


def resolve_credentials(ctx: Any) -> Credentials:
    """Return the credentials for this call, from the one source this mode allows.

    Raises ``MCPError`` in the HTTP passthrough mode when the request carries no usable
    Basic credentials. That is deliberate and matches the SDK guidance: a smarter model
    could not have avoided a missing Authorization header, so the failure belongs to the
    host, not into the model's context as a correctable tool error.
    """
    headers = getattr(ctx, "headers", None) if ctx is not None else None
    mode = config.select_mode(headers=headers)

    if mode == "http_passthrough":
        # headers is not None in this mode, select_mode guarantees it.
        return _credentials_from_basic(headers or {})

    # stdio and static bearer both take the Nextcloud account from the environment: the
    # bearer authenticates the caller of this server, it does not select a Nextcloud user.
    return load_stdio_credentials()


def resolve_clients(ctx: Any) -> NcClients:
    """Bundle the event loop client with the credentials of this call."""
    return NcClients(client=shared_client(), creds=resolve_credentials(ctx))


class StaticBearerVerifier:
    """Verify the single configured bearer token of a single-user deployment.

    ``secrets.compare_digest`` instead of ``==``: the comparison runs on attacker
    supplied input, and a short-circuiting comparison leaks the shared prefix over
    enough requests (threat T-01-24). The token is never logged and never echoed.

    The comparison runs on UTF-8 bytes, never on the strings themselves:
    ``compare_digest`` raises ``TypeError`` as soon as either side contains a
    non-ASCII character, and the caller-supplied side is hostile header input. A
    crash here would turn a malformed bearer into a 500 instead of a 401.
    """

    def __init__(self, token: str) -> None:
        self._token = token.encode("utf-8")

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token or not secrets.compare_digest(token.encode("utf-8"), self._token):
            return None
        return AccessToken(
            token=token,
            client_id=STATIC_BEARER_CLIENT_ID,
            scopes=[],
            subject=STATIC_BEARER_CLIENT_ID,
        )


def build_auth(
    env: Mapping[str, str] | None = None,
) -> tuple[StaticBearerVerifier | None, AuthSettings | None]:
    """Return the SDK auth wiring for the configured mode.

    ``(None, None)`` in the passthrough mode: the SDK bearer layer only understands
    ``Bearer`` and would answer 401 to every Basic request before a tool ever runs
    (pitfall 2). Both values set in the static bearer mode, never one of them.
    """
    token = config.static_bearer(env)
    if token is None:
        return None, None

    base = config.public_url(env)
    settings = AuthSettings(
        issuer_url=base,  # type: ignore[arg-type] - pydantic coerces the string
        resource_server_url=base,  # type: ignore[arg-type]
        required_scopes=[],
    )
    return StaticBearerVerifier(token), settings


def _credentials_from_basic(headers: Mapping[str, str]) -> Credentials:
    """Decode Basic credentials from the request, or fail with an actionable message."""
    raw = headers.get("authorization") or headers.get("Authorization")
    if not raw:
        raise MCPError(
            code=INVALID_REQUEST,
            message=f"This server needs Basic credentials per request. {_BASIC_HINT}",
        )

    scheme, _, payload = raw.partition(" ")
    if scheme.lower() != "basic":
        raise MCPError(
            code=INVALID_REQUEST,
            message=(
                "This server expects Basic credentials, not another authorization scheme. "
                f"{_BASIC_HINT}"
            ),
        )

    try:
        decoded = base64.b64decode(payload.strip(), validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        # The offending value is never part of the message: it is credential material.
        raise MCPError(
            code=INVALID_REQUEST,
            message=f"The Basic credentials could not be decoded. {_BASIC_HINT}",
        ) from None

    user, separator, secret = decoded.partition(":")
    if not separator or not user or not secret:
        raise MCPError(
            code=INVALID_REQUEST,
            message=f"The Basic credentials are not in the form user:app-password. {_BASIC_HINT}",
        )

    # The base URL stays a deployment decision. A client that could pick the target
    # instance could aim this server, and the credentials, at a host of its choosing.
    return Credentials(base_url=config.load_base_url(), user=user, secret=secret)
