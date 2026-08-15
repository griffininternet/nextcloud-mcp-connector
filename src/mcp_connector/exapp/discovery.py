"""The measurement probe of the discovery spike (D-29, AUTH-06), nothing more.

This module exists to answer one question that phase 3 depends on: can an OAuth capable
client reach the discovery metadata of this ExApp from the outside, unauthenticated, and
over which proxy path. It is not the phase 3 implementation, and it is written to be
replaced rather than extended.

Two routes, both below ``/.well-known/`` so the single ``^/\\.well-known/`` PUBLIC route in
``appinfo/info.xml`` already covers them and no manifest change is needed for the spike:

* ``GET /.well-known/oauth-protected-resource/mcp`` answers 200 with an RFC 9728 shaped
  document. It carries only the configured public URL and the method list, and nothing that
  comes from the request: no host header, no version, no configuration, and above all no
  secret (T-02-40, T-02-41). The real Protected Resource Metadata, with a live authorization
  server, is built in phase 3 (AUTH-03) from the ``AuthSettings`` of the SDK; this route is
  measured now and replaced then.
* ``GET /.well-known/mcp-discovery-probe`` answers 401 with a
  ``WWW-Authenticate: Bearer resource_metadata="<url>"`` header. It measures whether both
  proxy paths hand a 401 and that header to the client unchanged. The realistic test would be
  a 401 out of ``/mcp`` itself, but ``/mcp`` carries ``access_level`` USER in phase 2 on
  purpose (defense in depth, and HaRP resolves the user from an app password for us), so HaRP
  answers there before we do. The switch of ``/mcp`` to PUBLIC belongs with the own token
  verifier in phase 3. That limitation is recorded in ``docs/spike-discovery.md`` (T-02-45).

The probe reads no data and holds no state. Its 401 body is empty, its 200 body is a fixed
document derived from configuration alone. The whole module is deliberately public: an
unauthenticated caller is the point of the measurement (T-02-44).

Like ``entry_exapp``, this is attached by ``build_exapp_app`` alone and never registered on
the shared MCP server object, so the stdio server and the standalone HTTP server of phase 1
never grow a ``.well-known`` route by accident (D-23).
"""

from collections.abc import Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .. import config

__all__ = ["discovery_routes"]

#: The resource this metadata describes, relative to the public base URL of the server.
_RESOURCE_SUFFIX = "/mcp"

#: The canonical RFC 9728 metadata path of this ExApp, below its own prefix. The client is
#: pointed here through the WWW-Authenticate header (SEP-985 priority 1), which is what the
#: probe measures: does the pointer survive both proxy paths unchanged.
_METADATA_SUFFIX = "/.well-known/oauth-protected-resource/mcp"

#: On every answer of this module, including the 401. The PHP proxy caches JSON for 3600
#: seconds unless the answer says otherwise (pitfall 4, T-02-42). Defined locally, the same
#: three line constant that lifecycle.py and middleware.py each keep, so this spike module
#: stays self contained and can be deleted in one piece in phase 3.
_NO_STORE = {"Cache-Control": "no-store"}


def discovery_routes(env: Mapping[str, str] | None = None) -> list[Route]:
    """Build the two spike routes against one environment.

    The environment is a parameter for the same reason ``lifecycle_routes`` takes one: it
    lets every test build its own application without touching the process environment. The
    public URL is read from configuration on every request and never derived from the
    request, so a forged ``Host`` header cannot change the metadata (T-02-41).
    """

    async def protected_resource(request: Request) -> Response:
        """The RFC 9728 metadata document. Public by contract, configuration only."""
        base = config.public_url(env)
        return _json(
            {
                "resource": f"{base}{_RESOURCE_SUFFIX}",
                "authorization_servers": [],
                "bearer_methods_supported": ["header"],
            }
        )

    async def probe(request: Request) -> Response:
        """A 401 that points at the metadata, to measure header pass through."""
        base = config.public_url(env)
        metadata_url = f"{base}{_METADATA_SUFFIX}"
        headers = dict(_NO_STORE)
        headers["WWW-Authenticate"] = f'Bearer resource_metadata="{metadata_url}"'
        return _json({}, status_code=401, headers=headers)

    return [
        Route(_METADATA_SUFFIX, protected_resource, methods=["GET"]),
        Route("/.well-known/mcp-discovery-probe", probe, methods=["GET"]),
    ]


def _json(
    payload: dict[str, Any],
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """One helper for every answer, so ``no-store`` cannot be forgotten on one branch.

    The extra headers are merged over the constant instead of replacing it (IN-06): with
    ``headers or dict(_NO_STORE)`` a caller that passed a non-empty dict without
    ``Cache-Control`` silently lost ``no-store``, and the PHP proxy then cached the
    answer for 3600 seconds, which is exactly the pitfall the constant exists against.
    """
    return JSONResponse(payload, status_code=status_code, headers={**_NO_STORE, **(headers or {})})
