"""Credential resolution per tool call: the one channel the identity may come from.

The signature already takes the MCP context although only the environment path exists in
this plan. Plan 04 adds the HTTP header modes here, and no tool code changes for it.

There is deliberately no user parameter anywhere: a tool argument that selects the user
would be a confused deputy (threat T-01-12).
"""

from typing import Any

from .config import load_stdio_credentials
from .nextcloud import NcClients
from .nextcloud.credentials import Credentials
from .nextcloud.http import shared_client


def resolve_credentials(ctx: Any) -> Credentials:
    """Return the credentials for this call.

    ``ctx`` is unused in stdio mode (there are no headers) and is accepted so the HTTP
    passthrough and static bearer modes of plan 04 fit in without touching tool code.
    """
    return load_stdio_credentials()


def resolve_clients(ctx: Any) -> NcClients:
    """Bundle the event loop client with the credentials of this call."""
    return NcClients(client=shared_client(), creds=resolve_credentials(ctx))
