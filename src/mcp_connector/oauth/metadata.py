"""The three discovery documents, served where a client can actually reach them (AUTH-03).

The SDK can build both documents and register both routes, but it registers them at the
canonical paths relative to the application root. Our application root sits behind a prefix
that HaRP strips: a client asks for ``/exapps/mcp_connector/.well-known/...`` and the
container sees ``/.well-known/...``, while the canonical RFC 9728 path of the resource
``https://cloud.example.com/exapps/mcp_connector/mcp`` is
``https://cloud.example.com/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp``,
on the domain root, where Nextcloud answers and not this app (measured: 404,
docs/spike-discovery.md). So the documents are built here and served at the paths that exist
below the stripped prefix (pitfall 1 and pitfall 2 of 03-RESEARCH.md).

The three ways a client looks for the metadata, in the order it tries them:

1. ``resource_metadata`` out of the ``WWW-Authenticate`` header of our own 401. Measured in
   phase 2 over both proxy paths, unchanged in both. This is the primary way and it needs
   nothing from an administrator. ``exapp/middleware.py`` builds that pointer from
   :data:`PRM_SUFFIX`, so the pointer and the route below cannot drift apart.
2. The canonical root paths, one path segment further up than Nextcloud's
   ``WellKnownController`` can match. They answer 404 unless the administrator adds the two
   reverse proxy rules of ``deploy/Caddyfile``; :data:`AS_METADATA_SUFFIX` exists as their
   rewrite target.
3. The path appended OpenID Connect variant, ``<public url>/.well-known/openid-configuration``.
   It survives a stripped prefix, so it is the one authorization server path that works
   without any administrator action, and :data:`OPENID_CONFIGURATION_SUFFIX` serves it.

Everything in these documents comes from :func:`mcp_connector.config.public_url`, never from
the incoming message: a forged host must not be able to point a client at another server
(T-03-02). The answers carry ``no-store`` through the shared helper, which also overrides
the ``public, max-age=3600`` the SDK metadata handlers would set (T-03-03).

Like ``exapp.lifecycle``, this is a factory. It is attached by ``build_exapp_app`` alone and
never registered on the shared MCP server object, so the stdio server and the standalone
HTTP server of phase 1 never grow a well-known route by accident (D-23).
"""

from collections.abc import Mapping
from typing import Any

from mcp.server.auth.routes import build_metadata
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.shared.auth import ProtectedResourceMetadata
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .. import config
from ..exapp.responses import json_response

__all__ = [
    "AS_METADATA_SUFFIX",
    "OPENID_CONFIGURATION_SUFFIX",
    "PRM_SUFFIX",
    "REFRESH_SCOPE",
    "REGISTERED_SCOPE",
    "RESOURCE_SUFFIX",
    "TOOL_SCOPE",
    "metadata_routes",
]

#: The resource these documents describe, relative to the public base URL. The value has to
#: match the URL the user types into the client character for character, trailing slash
#: included, or the connection fails before the first tool call (client behaviour of
#: Claude.ai and ChatGPT, 03-RESEARCH.md).
RESOURCE_SUFFIX = "/mcp"

#: The RFC 9728 document below our own prefix. Also the target of the pointer in every 401
#: of the transport boundary, which imports this constant instead of repeating it.
PRM_SUFFIX = "/.well-known/oauth-protected-resource/mcp"

#: Way 3 of the list above: OpenID Connect Discovery appends the well-known segment to the
#: issuer path, and a client finds this one without any administrator action.
OPENID_CONFIGURATION_SUFFIX = "/.well-known/openid-configuration"

#: Way 2 of the list above: RFC 8414 inserts the well-known segment between host and path,
#: which lands on the domain root. This path exists as the rewrite target of the reverse
#: proxy rule that maps the root path back onto this app.
AS_METADATA_SUFFIX = "/.well-known/oauth-authorization-server"

#: One scope for the whole curated tool surface (D-42). Read/write separation with step up
#: consent is phase 4 material; one scope is the reliable answer for v1.
TOOL_SCOPE = "nextcloud"

#: Named in the authorization server document only, because it describes the refresh grant.
#: The MCP specification says a server SHOULD NOT list it in the protected resource metadata
#: or in the WWW-Authenticate scope, and Claude appends it on its own when it sees it here.
REFRESH_SCOPE = "offline_access"

#: What every dynamic registration is recorded with, and the reason it is a constant: a
#: client compares what it may ask for against ``scopes_supported`` below, and the
#: authorization endpoint compares what it did ask for against the registration. Whoever
#: changes one of the two lists has to change the other in the same edit, or a client reads
#: an offer this server then refuses (the live run of AUTH-04 against ChatGPT).
REGISTERED_SCOPE = f"{TOOL_SCOPE} {REFRESH_SCOPE}"

#: What a user sees in the consent dialog of the client. A fixed name, no version and no
#: host: the document is public and says nothing about the installation (T-03-04).
RESOURCE_NAME = "Nextcloud MCP Connector"

#: Added to the two methods the SDK lists. Claude.ai and ChatGPT both register as public
#: clients, which have no client secret to present at the token endpoint.
PUBLIC_CLIENT_AUTH_METHOD = "none"


def metadata_routes(
    env: Mapping[str, str] | None = None, *, dcr_enabled: bool = True
) -> list[Route]:
    """Build the three discovery routes against one environment.

    The environment is a parameter for the same reason ``lifecycle_routes`` takes one: it
    lets every test build its own application without touching the process environment. The
    public URL is read from configuration on every call and never derived from the incoming
    message, so a forged host cannot change a document (T-03-02).

    ``dcr_enabled`` is the switch plan 03-05 hands in from the registry policy (AUTH-07).
    When dynamic client registration is off, the document stops advertising an endpoint that
    would refuse every call. The default keeps this plan free of a policy it does not have
    yet, and matches the delivery state of D-35 (registration on).
    """

    async def protected_resource(request: Request) -> Response:
        """The RFC 9728 document. Public by contract, configuration only."""
        return json_response(_protected_resource_document(env))

    async def authorization_server(request: Request) -> Response:
        """The RFC 8414 document, served at both reachable paths, byte for byte the same."""
        return json_response(_authorization_server_document(env, dcr_enabled=dcr_enabled))

    return [
        Route(PRM_SUFFIX, protected_resource, methods=["GET"]),
        Route(OPENID_CONFIGURATION_SUFFIX, authorization_server, methods=["GET"]),
        Route(AS_METADATA_SUFFIX, authorization_server, methods=["GET"]),
    ]


def _protected_resource_document(env: Mapping[str, str] | None) -> dict[str, Any]:
    """Build the RFC 9728 document out of the configured public URL alone.

    ``model_validate`` with plain strings instead of the constructor with ``AnyHttpUrl``
    objects: the model preserves an empty URL path (``url_preserve_empty_path``), while an
    ``AnyHttpUrl`` built outside the model has already appended a trailing slash to a path
    less URL. The resource value has to survive as it was configured.

    ``exclude_none`` keeps the optional fields of the model out of the answer instead of
    publishing them as ``null``, which is what RFC 9728 asks for and what keeps the set of
    field names small enough for the leak test to be exact.
    """
    base = config.public_url(env)
    document = ProtectedResourceMetadata.model_validate(
        {
            "resource": f"{base}{RESOURCE_SUFFIX}",
            "authorization_servers": [base],
            "scopes_supported": [TOOL_SCOPE],
            "resource_name": RESOURCE_NAME,
        }
    )
    return document.model_dump(mode="json", exclude_none=True)


def _authorization_server_document(
    env: Mapping[str, str] | None, *, dcr_enabled: bool
) -> dict[str, Any]:
    """Build the RFC 8414 document from the SDK, then add the three fields it does not set.

    The four endpoints it names are built in plan 03-05. A discovery document describes the
    addresses of an authorization server, not their implementation state, and a client reads
    it before it ever calls one of them.
    """
    base = config.public_url(env)
    metadata = build_metadata(
        AnyHttpUrl(base),
        None,
        ClientRegistrationOptions(
            enabled=dcr_enabled,
            valid_scopes=[TOOL_SCOPE, REFRESH_SCOPE],
            default_scopes=[TOOL_SCOPE],
        ),
        RevocationOptions(enabled=True),
    )
    # The SDK lists client_secret_post and client_secret_basic. Claude.ai and ChatGPT both
    # arrive as public clients, and a public client authenticates with none of the two
    # (client behaviour, 03-RESEARCH.md).
    metadata.token_endpoint_auth_methods_supported = [
        *(metadata.token_endpoint_auth_methods_supported or []),
        PUBLIC_CLIENT_AUTH_METHOD,
    ]
    # Spelled out rather than inherited from the registration options, because the two lists
    # answer different questions: what a client may register for, and what this server
    # offers (D-42 plus the refresh grant).
    metadata.scopes_supported = [TOOL_SCOPE, REFRESH_SCOPE]
    # RFC 9207: the authorization response carries the issuer, which is what lets a client
    # notice a mix-up attack between two authorization servers it talks to.
    metadata.authorization_response_iss_parameter_supported = True

    document = metadata.model_dump(mode="json", exclude_none=True)
    # RFC 8414 compares the issuer byte for byte against the value the discovery URL was
    # built from. ``AnyHttpUrl`` appends a trailing slash to a path less URL, so a connector
    # deployed on its own host would advertise an issuer that no client accepts. The
    # configured value wins; every endpoint above is built from it with the slash stripped.
    document["issuer"] = base
    return document
