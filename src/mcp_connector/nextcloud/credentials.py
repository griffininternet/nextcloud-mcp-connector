"""The credential object that every Nextcloud call receives as a parameter.

Immutable and masked: the secret must never show up in a traceback, a log record or a
``repr`` of some container that happens to hold it (threat T-01-07). It is a parameter
object, not module state, because the HTTP passthrough mode changes credentials per
request and a module-global client would be a cross-user leak.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    """Base URL without trailing slash, Nextcloud user id and app password."""

    base_url: str
    user: str
    secret: str

    def __repr__(self) -> str:
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, secret='***')"
