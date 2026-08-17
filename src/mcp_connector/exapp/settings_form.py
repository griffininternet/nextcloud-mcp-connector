"""The signpost in Nextcloud's own settings: one link only Declarative Settings form.

The contract of this module is measured, not assumed (04-RESEARCH.md, Messprotokoll
2026-08-17 against app_api v34.0.3): the registration is
``POST /ocs/v2.php/apps/app_api/api/v1/ui/settings`` in the app context, ``insertOrUpdate``
makes it idempotent, AppAPI hands out the forms of *enabled* apps only, so disabling hides
the entry by itself, and ``ExAppService::unregisterExApp`` removes it on uninstall. There
is nothing to unregister on our side and no fourteenth route: when a user changes a
declarative value, **no call reaches the ExApp**.

That last measurement is the reason ``fields`` is empty. A checkbox rendered by Nextcloud
would store its value in ``preferences_ex``, and the bearer boundary would only learn about
it by asking Nextcloud on every request (forbidden by D-47) or by polling (forbidden by
D-48). A visible switch that the boundary does not enforce is worse than no switch, so the
form carries a title, a description and one link, and the switch itself lives on
``/connections`` where flipping it is a local write this app reads on the very next request.

The error model is the one of :mod:`mcp_connector.exapp.status`: one attempt, no retry, and
a failure never propagates. A failed registration costs the signpost and one log line; a
500 out of ``/enabled`` makes AppAPI disable the app again immediately (pitfall 11).
"""

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from .. import config
from ..nextcloud.clients.ocs import OCS_HEADERS
from ..nextcloud.credentials import appapi_auth_headers
from ..nextcloud.http import shared_client
from .ui import strings
from .ui.connections import CONNECTIONS_PATH

__all__ = ["form_scheme", "register_settings_form"]

#: The OCS route AppAPI exposes for Declarative Settings forms of an ExApp.
SETTINGS_PATH = "/ocs/v2.php/apps/app_api/api/v1/ui/settings"

#: The form id, stable across registrations: ``insertOrUpdate`` keys on (appid, formid), so
#: re-enabling the app updates the one entry instead of adding a second.
FORM_ID = "mcp_connector_settings"

#: Where the entry sits, per the schema table of 04-UI-SPEC.md. ``personal`` because
#: EXAPP-02 is per user by definition, ``security`` because that is where the user already
#: manages devices and sessions (measured addressable for an ExApp form).
FORM_PRIORITY = 10
SECTION_TYPE = "personal"
SECTION_ID = "security"

logger = logging.getLogger("mcp_connector.exapp.settings_form")


def form_scheme(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Build the form scheme against one environment.

    A function and not a module level constant: both URLs in it come from the **public**
    URL of this deployment, which is configuration and not a compile time fact. An internal
    host name here would be a dead link for every reader of the settings page and a small
    leak about the deployment on top (T-04-40).
    """
    connections_url = f"{config.public_url(env)}{CONNECTIONS_PATH}"
    return {
        "id": FORM_ID,
        "priority": FORM_PRIORITY,
        "section_type": SECTION_TYPE,
        "section_id": SECTION_ID,
        "title": strings.SETTINGS_TITLE,
        # The doc_url renders as a small help icon, and a help icon is easy to miss, so the
        # address is spelled out as text as well.
        "description": strings.SETTINGS_DESCRIPTION.format(connections_url=connections_url),
        "doc_url": connections_url,
        # Empty, and a list: core validation accepts an empty list and rejects a missing
        # one. See the module docstring for why it stays empty (pitfall 1).
        "fields": [],
    }


async def register_settings_form(*, env: Mapping[str, str] | None = None) -> None:
    """Put the signpost into Nextcloud's settings. Never raises, for any reason.

    The call runs in the app context, so the user id in the outgoing token is empty: this
    is the ExApp registering something about itself, not a request on behalf of a person.
    """
    settings = config.exapp_settings(env)
    url = f"{settings.base_url}{SETTINGS_PATH}"
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
        response = await client.post(url, json={"formScheme": form_scheme(env)}, headers=headers)
    except httpx.HTTPError:
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the settings form registration to %s did not reach Nextcloud", url)
        return

    if response.status_code // 100 != 2:
        logger.error("the settings form registration to %s answered %s", url, response.status_code)
