"""The outgoing half of the install handshake: the init progress push.

``POST /init`` answering 200 is not enough. AppAPI only sets the progress to 100 by
itself when the call fails with 404 or 501, so an implemented ``/init`` that stays quiet
leaves the app at "initialising, 0 percent" forever and ``/enabled`` is never called
(pitfall 3). The ExApp reports the progress itself, over the same OCS route every other
part of this project uses.

One attempt, no retry, and a failure never propagates: a 500 out of ``/init`` aborts the
whole installation, while a missed progress push leaves one visible error line and an
installation an administrator can finish by hand. That asymmetry is the entire error
policy of this module.
"""

import logging
from collections.abc import Mapping

import httpx

from .. import config
from ..nextcloud.clients.ocs import OCS_HEADERS
from ..nextcloud.credentials import appapi_auth_headers
from ..nextcloud.http import shared_client

__all__ = ["report_init_progress"]

#: The OCS route AppAPI exposes for the install progress. Exempt from the "app must be
#: enabled" check while the installation runs.
STATUS_PATH = "/ocs/v2.php/apps/app_api/ex-app/status"

logger = logging.getLogger("mcp_connector.exapp.status")


async def report_init_progress(
    progress: int = 100, *, env: Mapping[str, str] | None = None
) -> None:
    """Tell Nextcloud how far the initialisation got. Never raises for a transport error.

    The call runs in the app context, so the user id in the outgoing token is empty: this
    is the ExApp reporting about itself, not a request on behalf of a person.
    """
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{STATUS_PATH}"
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

    client = shared_client()
    try:
        response = await client.put(url, json={"progress": progress}, headers=headers)
    except httpx.HTTPError:
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the init progress push to %s did not reach Nextcloud", url)
        return

    if response.status_code // 100 != 2:
        logger.error("the init progress push to %s answered %s", url, response.status_code)
