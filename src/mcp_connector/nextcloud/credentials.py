"""The credential object that every Nextcloud call receives as a parameter.

Immutable and masked: the secret must never show up in a traceback, a log record or a
``repr`` of some container that happens to hold it (threat T-01-07). It is a parameter
object, not module state, because the HTTP passthrough mode changes credentials per
request and a module-global client would be a cross-user leak.
"""

import base64
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    """Base URL without trailing slash, Nextcloud user id and app password."""

    base_url: str
    user: str
    secret: str

    def __repr__(self) -> str:
        return f"Credentials(base_url={self.base_url!r}, user={self.user!r}, secret='***')"


def appapi_auth_headers(
    user: str,
    *,
    app_id: str,
    app_version: str,
    aa_version: str,
    app_secret: str,
) -> dict[str, str]:
    """Build the four headers an ExApp sends to Nextcloud, one fresh dict per call.

    ``AUTHORIZATION-APP-API`` is base64 of ``"<user>:<app_secret>"``. base64 is an
    encoding and not a protection, so the result is exactly as sensitive as the secret
    itself: it is never written to a log record and never put into an error message
    (T-02-03). An empty ``user`` is the app context without a user, which is what the
    init progress push uses.

    This lives next to :class:`Credentials` and not in the ``exapp`` package because the
    ``nextcloud`` package must not import from ``exapp``: the fourth credential mode of
    plan 02-02 grows right here, one layer below the ExApp shell.
    """
    token = base64.b64encode(f"{user}:{app_secret}".encode()).decode()
    return {
        "AA-VERSION": aa_version,
        "EX-APP-ID": app_id,
        "EX-APP-VERSION": app_version,
        "AUTHORIZATION-APP-API": token,
    }
