"""The discovery spike routes, in process and without Nextcloud (D-29, AUTH-06).

Every check builds its own Starlette app from ``discovery_routes``, which is the whole
point of the factory: the routes are never registered on the shared MCP server object, so
the stdio server and the standalone HTTP server of phase 1 stay exactly as they were
(D-23). Nothing here opens a socket.

Threats covered: T-02-40 (the public metadata route leaks no internal detail), T-02-41
(the resource URL comes from configuration, never from the request), T-02-42 (``no-store``
against the one hour cache of the PHP proxy) and T-02-44 (the probe reads no data and only
answers with a header).
"""

import base64
import json

from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config, entry_http
from mcp_connector.entry_exapp import build_exapp_app
from mcp_connector.exapp import discovery

PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
APP_SECRET = "a8e934cd9e8d19e49db290ab1e529f4d9fed314388579d612eb01644beb7cacc"

METADATA_PATH = "/.well-known/oauth-protected-resource/mcp"
PROBE_PATH = "/.well-known/mcp-discovery-probe"

ENV = {
    config.ENV_PUBLIC_URL: PUBLIC_URL,
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: "0.1.0",
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}


def client() -> TestClient:
    """A fresh app per call: one Starlette instance is one lifespan."""
    return TestClient(Starlette(routes=discovery.discovery_routes(ENV)))


def stray_auth_headers() -> dict[str, str]:
    """The headers a client could smuggle in on a PUBLIC route. They must not matter."""
    token = base64.b64encode(f"attacker:{APP_SECRET}".encode()).decode()
    return {
        "Authorization": "Basic " + base64.b64encode(b"attacker:pw").decode(),
        "AUTHORIZATION-APP-API": token,
        "EX-APP-ID": "mcp_connector",
    }


# --- the metadata route ----------------------------------------------------------


def test_metadata_answers_200_json_without_any_auth() -> None:
    """The whole point of the spike: reachable, unauthenticated, from the outside."""
    with client() as http:
        response = http.get(METADATA_PATH)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_metadata_carries_resource_and_bearer_methods_from_configuration() -> None:
    with client() as http:
        body = http.get(METADATA_PATH).json()
    assert body["resource"] == f"{PUBLIC_URL}/mcp"
    assert body["bearer_methods_supported"] == ["header"]


def test_metadata_leaks_nothing_but_the_public_url_and_the_method_list() -> None:
    """T-02-40: no secret, no request host, no version, no configuration. Set equality."""
    with client() as http:
        response = http.get(METADATA_PATH, headers={"Host": "attacker.example"})
    body = response.text
    assert set(json.loads(body)) == {
        "resource",
        "authorization_servers",
        "bearer_methods_supported",
    }
    assert APP_SECRET not in body
    assert "attacker.example" not in body
    assert "nc.test" not in body
    assert "0.1.0" not in body
    assert "testserver" not in body


def test_metadata_resource_ignores_a_forged_host_header() -> None:
    """T-02-41: the URL is configuration, not a heuristic over the request."""
    with client() as http:
        forged = http.get(METADATA_PATH, headers={"Host": "evil.example:9999"}).json()
        plain = http.get(METADATA_PATH).json()
    assert forged["resource"] == plain["resource"] == f"{PUBLIC_URL}/mcp"


def test_metadata_ignores_a_stray_authorization_header() -> None:
    """A PUBLIC route reads no credentials: a smuggled header changes nothing."""
    with client() as http:
        with_auth = http.get(METADATA_PATH, headers=stray_auth_headers())
        without = http.get(METADATA_PATH)
    assert with_auth.status_code == 200
    assert with_auth.json() == without.json()


def test_metadata_falls_back_to_the_default_public_url_when_unset() -> None:
    """Without NC_MCP_PUBLIC_URL the resource is the documented default, never the request.

    This is the exact case of the live measurement: the deployed container has no
    NC_MCP_PUBLIC_URL, so the resource reads the default host. The spike measures
    reachability and header pass through, not the value of this field (see the doc).
    """
    env = {key: value for key, value in ENV.items() if key != config.ENV_PUBLIC_URL}
    with TestClient(Starlette(routes=discovery.discovery_routes(env))) as http:
        body = http.get(METADATA_PATH).json()
    assert body["resource"] == f"{config.DEFAULT_PUBLIC_URL}/mcp"
    assert "testserver" not in json.dumps(body)


# --- the probe route -------------------------------------------------------------


def test_probe_answers_401_with_a_www_authenticate_pointer() -> None:
    with client() as http:
        response = http.get(PROBE_PATH)
    assert response.status_code == 401
    header = response.headers["www-authenticate"]
    assert header == f'Bearer resource_metadata="{PUBLIC_URL}{METADATA_PATH}"'


def test_probe_body_is_empty_and_carries_no_secret() -> None:
    with client() as http:
        response = http.get(PROBE_PATH, headers=stray_auth_headers())
    assert response.json() == {}
    assert APP_SECRET not in response.text


# --- cache control ---------------------------------------------------------------


def test_both_routes_carry_no_store() -> None:
    """T-02-42: createProxyResponse caches JSON for 3600 s unless Cache-Control is set."""
    with client() as http:
        assert http.get(METADATA_PATH).headers["cache-control"] == "no-store"
        assert http.get(PROBE_PATH).headers["cache-control"] == "no-store"


# --- wiring ----------------------------------------------------------------------


def test_build_exapp_app_registers_both_well_known_routes() -> None:
    app = build_exapp_app(ENV)
    paths = {getattr(route, "path", "") for route in app.router.routes}
    assert METADATA_PATH in paths
    assert PROBE_PATH in paths


def test_the_standalone_http_app_knows_neither_route() -> None:
    """D-23: phase 1 modes must not grow a .well-known route. Empty list, not a subset."""
    app = entry_http.build_app({config.ENV_URL: "http://nc.test"})
    well_known = [
        path
        for path in (getattr(route, "path", "") for route in app.router.routes)
        if "well-known" in path
    ]
    assert well_known == []
