"""The registration of the occ commands of this app with Nextcloud.

Two of them since plan 18-08: ``mcp_connector:purge`` ends every connection of this
instance, and ``mcp_connector:audit:verify`` checks the chain of the audit log. They are
registered one by one, because ``OccCommandController::registerCommand`` takes exactly one
command per ``POST`` (app_api v34.0.3), and each of them gets its own ``try`` for the reason
``exapp/lifecycle.py`` gives its second form registration: they are independent, so a
failure of one may not cost the other.

Built like :mod:`mcp_connector.exapp.settings_form` and
:mod:`mcp_connector.exapp.admin_settings`, which are the one to one model for the transport,
the app context and the error model: one attempt, no retry, one log line on failure, never
an exception out of this module. The reason for that tolerance is pitfall 11 of phase 2: the
registration happens in the ``enabled=1`` branch, and a non empty ``error`` field there
makes AppAPI disable the app again at once.

Two things differ from the two forms, and they are the whole content of this module: the
path (``POST /ocs/v2.php/apps/app_api/api/v1/occ_command``, verified against app_api 34.0.3,
``appinfo/routes.php`` ``OccCommand#registerCommand`` and
``lib/Service/ExAppOccService.php``) and the body, which describes a Symfony command
Nextcloud then builds and offers in ``occ list``.

Nobody has to unregister anything: ``ExAppService::unregisterExApp`` calls
``unregisterExAppOccCommands($appId)`` itself, the same way it removes the settings forms.
And ``disableExApp`` removes nothing, which is why the disable branch of
``exapp/lifecycle.py`` stays empty.

Every ``execute_handler`` is derived from the path constant of its handler module rather
than written a second time. A registration whose handler name drifts away from the route is
a command that exists, is documented, and answers 404 on the one day somebody needs it.
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
from .audit_verify import AUDIT_VERIFY_PATH, JSON_OPTION
from .purge import FORCE_OPTION, PURGE_PATH

__all__ = [
    "OCC_AUDIT_COMMAND_NAME",
    "OCC_AUDIT_HANDLER",
    "OCC_AUDIT_JSON_DESCRIPTION",
    "OCC_COMMAND_NAME",
    "OCC_COMMAND_PATH",
    "OCC_FORCE_DESCRIPTION",
    "OCC_HANDLER",
    "command_schemes",
    "register_occ_commands",
]

#: The OCS route AppAPI exposes for the occ commands of an ExApp.
OCC_COMMAND_PATH = "/ocs/v2.php/apps/app_api/api/v1/occ_command"

#: What an administrator types. The app id as the namespace, which is what every ExApp
#: command of an app shares and what makes it findable in ``occ list``.
OCC_COMMAND_NAME = "mcp_connector:purge"

#: The route on us AppAPI calls when the command runs, without the leading slash: one
#: derivation from the route itself, so the two cannot say different things.
OCC_HANDLER = PURGE_PATH.removeprefix("/")

OCC_DESCRIPTION = (
    "End every MCP connection of this instance: hand every Nextcloud app password this app "
    "created back to Nextcloud, empty its database and delete its encryption key. Run this "
    "before removing the app, because removing the app does not do it."
)

OCC_FORCE_DESCRIPTION = (
    "Required. This cannot be undone: every connected assistant has to be authorized again."
)

#: What an administrator types for the check of AUDIT-02. The namespace has two levels on
#: purpose: AUDIT-04 adds a second command in phase 19 that reads entries out and hands them
#: over, and ``mcp_connector:audit:`` carries both of them, so the day that command arrives
#: costs no renaming and no second invention of a name.
OCC_AUDIT_COMMAND_NAME = "mcp_connector:audit:verify"

#: The route on us AppAPI calls when the check runs, derived exactly like :data:`OCC_HANDLER`.
OCC_AUDIT_HANDLER = AUDIT_VERIFY_PATH.removeprefix("/")

OCC_AUDIT_DESCRIPTION = (
    "Check every entry of the audit log against the chain it belongs to and report either "
    "that no break was found or the first place a chain is broken."
)

OCC_AUDIT_JSON_DESCRIPTION = (
    "Answer with the same result as JSON, for a script that watches this instead of the "
    "exit code, which is always 0."
)

logger = logging.getLogger("mcp_connector.exapp.occ")


def command_schemes() -> list[dict[str, Any]]:
    """The commands this app registers, one entry per ``POST``.

    A list and not one object, because ``OccCommandController::registerCommand`` takes
    exactly one command per request (signature verified against app_api v34.0.3), so two
    commands are two registrations and never one body with two names in it.

    A function rather than a module level constant so the shapes have one place a test reads
    and the registration cannot be asserted against a copy of itself. Nothing in them comes
    from configuration: unlike the two settings forms these bodies carry no URL, because a
    command is invoked on the command line and not followed in a browser.
    """
    return [
        {
            "name": OCC_COMMAND_NAME,
            "description": OCC_DESCRIPTION,
            # Visible in ``occ list``: an administrator who has to find this command on the
            # day of an uninstall should not have to know it exists (05-RESEARCH.md,
            # pattern 3).
            "hidden": 0,
            "arguments": [],
            # Mode ``none`` is a flag without a value, so ``--force`` is presence and nothing
            # else. The handler checks it again, because what AppAPI hands over is input.
            "options": [
                {"name": FORCE_OPTION, "mode": "none", "description": OCC_FORCE_DESCRIPTION}
            ],
            "usages": [f"{OCC_COMMAND_NAME} --{FORCE_OPTION}"],
            "execute_handler": OCC_HANDLER,
        },
        {
            "name": OCC_AUDIT_COMMAND_NAME,
            "description": OCC_AUDIT_DESCRIPTION,
            "hidden": 0,
            "arguments": [],
            # The same mode as the option above, and for once the handler reads it for a
            # shape and not for a permission: with it the answer arrives as JSON.
            "options": [
                {"name": JSON_OPTION, "mode": "none", "description": OCC_AUDIT_JSON_DESCRIPTION}
            ],
            # Both ways round, because the plain one is the one an administrator types and
            # the other is the one a monitoring script needs to find.
            "usages": [OCC_AUDIT_COMMAND_NAME, f"{OCC_AUDIT_COMMAND_NAME} --{JSON_OPTION}"],
            "execute_handler": OCC_AUDIT_HANDLER,
        },
    ]


async def register_occ_commands(*, env: Mapping[str, str] | None = None) -> None:
    """Register every command of this app with Nextcloud. Never raises, for any reason.

    The call runs in the app context, so the user id in the outgoing token is empty: this is
    the ExApp registering something about itself and not a request on behalf of a person.

    One ``try`` per command, and that is the same reason ``exapp/lifecycle.py`` gives for
    putting the admin form registration in a block of its own: the commands are independent
    of each other, so a Nextcloud that refuses one of them must not cost the other. Every
    failure names the command it happened to, because "the registration failed" over two
    commands is a line that sends an administrator to the wrong one.
    """
    try:
        settings = config.exapp_settings(env)
    except ToolError:
        # A missing deploy variable is a startup problem and is reported there. Raising here
        # would travel into the enable handler, which must answer with an empty error field.
        logger.error("no occ command was registered: the deploy environment is incomplete")
        return

    url = f"{settings.base_url}{OCC_COMMAND_PATH}"
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
    for scheme in command_schemes():
        try:
            response = await client.post(url, json=scheme, headers=headers)
        except httpx.HTTPError:
            # No value from the request is repeated here: the headers carry the app secret.
            # The name of the command is not a value of the request, it is a constant of this
            # module, so it can be named and has to be.
            logger.error(
                "the registration of %s to %s did not reach Nextcloud", scheme["name"], url
            )
            continue

        if response.status_code // 100 != 2:
            logger.error(
                "the registration of %s to %s answered %s",
                scheme["name"],
                url,
                response.status_code,
            )
