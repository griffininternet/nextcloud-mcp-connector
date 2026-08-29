"""Does this Nextcloud account still exist? One question, one call, and an unsymmetric answer.

D-12 says a user who is removed in Nextcloud takes the whole chain of that user with him, and
the sweep of D-11 is what notices it. This module is the half of that sentence which asks
Nextcloud, and it is written around one property: **the uncertainty always falls towards
keeping.** A chain that is kept for another month costs storage. A chain that falls because a
list was short costs the record of everything that account ever did.

**The way, and that it costs nothing new.** AppAPI exposes the user list of the instance
itself, reachable with the four headers of an ExApp in the app context (empty user id), the
same outgoing shape ``exapp/occ.py`` and ``exapp/config_values.py`` already use. No
impersonation, no ``provisioning_api``, no new permission and no new route. Verified against
``nextcloud/app_api`` v34.0.3, the same tag those two modules verified their own paths
against, in three places:

*   ``appinfo/routes.php:72`` registers ``OCSApi#getNCUsersList`` as
    ``GET /api/v1/users`` under the ``ocs`` group, so it answers under ``/ocs/v2.php``.
*   ``lib/Controller/OCSApiController.php:81-86`` carries ``#[AppAPIAuth]`` and
    ``#[PublicPage]``: the app secret in the header is the whole authentication, and no
    session of a person is involved.
*   ``lib/Service/ExAppService.php:199-203`` answers with the uid of every user
    ``IUserManager::searchDisplayName('')`` finds, without a limit.

**What it costs.** The endpoint answers with the whole list and never with a yes or a no about
one account: on an instance with ten thousand accounts one answer is ten thousand identifiers.
So this function is called **once per sweep and never once per user**. The caller collects
every account it has a question about and holds all of them against one list. Putting this
function into a loop turns one call into one call per silent chain.

**The return value is the rule of this file.** ``None`` means "unknown, so every account
exists", and it is the answer to a network error, to any status other than 200, to a body that
is not readable as a list, **and to an empty list**. An empty list is always a fault and never
an instance without users: this log cannot hold an entry if nobody ever called a tool, so a
store with a silent chain in it is a store on an instance that has users. Only a list with at
least one identifier in it becomes a ``frozenset``.

The reason for that asymmetry is the most dangerous assumption of this phase (A1,
18-RESEARCH.md §7): it is unmeasured whether ``searchDisplayName('')`` answers completely on
an LDAP or a directory backend, and whether a disabled account is in it. A missing identifier
in this list drops a whole chain under D-12. So a doubt is never a deletion.

**What never reaches a log line here.** No value of the answer and no header: the four headers
carry the app secret, and base64 is an encoding and not a protection. A failure is worth its
status or the name of its exception type, and nothing else (T-18-10).
"""

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from .. import config
from ..errors import ToolError
from ..nextcloud.clients.ocs import OCS_HEADERS
from ..nextcloud.credentials import appapi_auth_headers
from ..nextcloud.http import shared_client

__all__ = ["USERS_PATH", "existing_users"]

#: The OCS route AppAPI exposes for the user list of the instance. ``/ocs/v2.php`` because
#: this project speaks v2 everywhere, although the route is registered for both.
USERS_PATH = "/ocs/v2.php/apps/app_api/api/v1/users"

logger = logging.getLogger("mcp_connector.audit.accounts")


def _identifiers(payload: Any) -> frozenset[str] | None:
    """The uids out of the OCS envelope, or ``None`` when the answer cannot be read.

    Three refusals, and each of them is a decision to keep rather than to delete: a body that
    is not the OCS envelope, a ``data`` that is not a JSON list, and a list that yields no
    identifier at all. The last one covers both an empty list and a list of things that are
    not names, because both mean the same for the caller: this answer names nobody, so it may
    not be used to say that somebody is gone.

    A shape other than a list is refused on purpose rather than guessed at. ``array_map`` over
    the result of ``searchDisplayName`` keeps the keys of its input, so a backend whose keys
    are not a sequence would arrive as a JSON object; reading that as a list would mean
    deciding, in the one direction that cannot be taken back, what an unmeasured shape means.
    """
    if not isinstance(payload, dict):
        return None
    ocs = payload.get("ocs")
    if not isinstance(ocs, dict) or "data" not in ocs:
        return None
    data = ocs["data"]
    if not isinstance(data, list):
        return None
    names = frozenset(item for item in data if isinstance(item, str) and item)
    return names or None


async def existing_users(env: Mapping[str, str] | None = None) -> frozenset[str] | None:
    """Every account this instance has, or ``None`` for "unknown, so keep everything".

    Never raises, for any answer and any failure: the caller is the sweep inside a tool call,
    and the account check of D-12 may not cost that call anything (D-13).

    ``None`` on every failure and on an empty list, a ``frozenset`` only for a list with at
    least one identifier in it. The module docstring says why that asymmetry is the whole
    point of this file, and the caller in ``audit/record.py`` is written to it: with ``None``
    it drops no chain at all, even for an account that has been silent for a year.
    """
    try:
        settings = config.exapp_settings(env)
    except ToolError:
        # A missing deploy variable is a startup problem and is reported there. Here it is
        # one more reason not to know, which is one more reason to keep.
        logger.info("no account check on this sweep: the deploy environment is incomplete")
        return None

    url = f"{settings.base_url}{USERS_PATH}"
    headers = dict(OCS_HEADERS)
    headers.update(
        appapi_auth_headers(
            "",
            app_id=settings.app_id,
            app_version=settings.app_version,
            aa_version=settings.aa_version,
            app_secret=settings.app_secret,
        )
    )

    try:
        response = await shared_client().get(url, headers=headers)
    except httpx.HTTPError as exc:
        # The type of the failure and never the request: the headers carry the app secret.
        logger.warning("the account list was not read: %s", type(exc).__name__)
        return None

    if response.status_code != httpx.codes.OK:
        logger.warning("the account list was not read: Nextcloud answered %s", response.status_code)
        return None

    try:
        payload = response.json()
    except ValueError:
        logger.warning("the account list was not read: the answer was not JSON")
        return None

    names = _identifiers(payload)
    if names is None:
        # Not "there are no users": an unreadable or empty answer is never an empty instance,
        # because a log with a silent chain in it belongs to an instance that has users.
        logger.warning("the account list named nobody, so no chain is treated as orphaned")
    return names
