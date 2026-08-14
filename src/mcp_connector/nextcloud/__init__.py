"""Nextcloud client layer: credentials, HTTP pool and one module per API family.

``NcClients`` is the single parameter object every tool function receives. It is the seam
where phase 2 hooks in the AppAPI impersonation without touching tool code.
"""

from dataclasses import dataclass

import httpx

from .credentials import Credentials

__all__ = ["Credentials", "NcClients"]


@dataclass(frozen=True, slots=True)
class NcClients:
    """The HTTP client of the current event loop plus the credentials of this call."""

    client: httpx.AsyncClient
    creds: Credentials
