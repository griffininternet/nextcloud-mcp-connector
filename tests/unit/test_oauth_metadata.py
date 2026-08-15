"""The three discovery documents of the production path (AUTH-03, D-38).

This file is the rewritten ``tests/unit/test_exapp_discovery.py``: the same fixture head and
the same four patterns (set equality on the field names, a forged ``Host``, a stray
``Authorization`` header, an empty well-known list in the standalone mode), with the spike
probe removed and the two authorization server paths added.

Every check builds its own Starlette app from ``metadata_routes``, which is the whole point
of the factory: the routes are never registered on the shared MCP server object, so the
stdio server and the standalone HTTP server of phase 1 stay exactly as they were (D-23).
Nothing here opens a socket.

Threats covered: T-03-02 (every document comes from configuration, never from the request),
T-03-03 (``no-store`` against the one hour cache of the PHP proxy and against the
``public, max-age=3600`` the SDK metadata handlers would set) and T-03-04 (set equality on
the field names instead of a subset, so a field added by an SDK upgrade cannot publish
configuration unnoticed).
"""

import base64
import json

from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config, entry_http
from mcp_connector.entry_exapp import build_exapp_app
from mcp_connector.exapp import responses
from mcp_connector.oauth import metadata

PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
APP_SECRET = "a8e934cd9e8d19e49db290ab1e529f4d9fed314388579d612eb01644beb7cacc"

PRM_PATH = "/.well-known/oauth-protected-resource/mcp"
OPENID_PATH = "/.well-known/openid-configuration"
AUTHORIZATION_SERVER_PATH = "/.well-known/oauth-authorization-server"
PROBE_PATH = "/.well-known/mcp-discovery-probe"

ENV = {
    config.ENV_PUBLIC_URL: PUBLIC_URL,
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: "0.1.0",
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}

#: What the authorization server document is allowed to contain, exactly. An SDK upgrade
#: that adds a field has to pass this list first (T-03-04).
AS_FIELDS = {
    "issuer",
    "authorization_endpoint",
    "token_endpoint",
    "registration_endpoint",
    "revocation_endpoint",
    "revocation_endpoint_auth_methods_supported",
    "scopes_supported",
    "response_types_supported",
    "grant_types_supported",
    "token_endpoint_auth_methods_supported",
    "code_challenge_methods_supported",
    "authorization_response_iss_parameter_supported",
}


def client(env: dict[str, str] | None = None, *, dcr_enabled: bool = True) -> TestClient:
    """A fresh app per call: one Starlette instance is one lifespan."""
    routes = metadata.metadata_routes(ENV if env is None else env, dcr_enabled=dcr_enabled)
    return TestClient(Starlette(routes=routes))


def stray_auth_headers() -> dict[str, str]:
    """The headers a client could smuggle in on a PUBLIC route. They must not matter."""
    token = base64.b64encode(f"attacker:{APP_SECRET}".encode()).decode()
    return {
        "Authorization": "Basic " + base64.b64encode(b"attacker:pw").decode(),
        "AUTHORIZATION-APP-API": token,
        "EX-APP-ID": "mcp_connector",
    }


# --- the protected resource metadata (RFC 9728) -----------------------------------


def test_the_protected_resource_metadata_answers_200_json_without_any_auth() -> None:
    """The document a client reaches through the resource_metadata pointer of the 401."""
    with client() as http:
        response = http.get(PRM_PATH)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_the_protected_resource_metadata_names_the_resource_and_one_server() -> None:
    """Claude reads only the first entry of authorization_servers, so there is one."""
    with client() as http:
        body = http.get(PRM_PATH).json()
    assert body["resource"] == f"{PUBLIC_URL}/mcp"
    assert body["authorization_servers"] == [PUBLIC_URL]
    assert body["bearer_methods_supported"] == ["header"]


def test_the_protected_resource_metadata_lists_exactly_the_one_tool_scope() -> None:
    """D-42: one scope for the whole tool surface, and offline_access is not part of it.

    The MCP specification says a server SHOULD NOT put offline_access into the PRM
    scopes_supported or into the WWW-Authenticate scope; it belongs into the authorization
    server document, where it describes the refresh grant.
    """
    with client() as http:
        response = http.get(PRM_PATH)
    assert response.json()["scopes_supported"] == ["nextcloud"]
    assert "offline_access" not in response.text


def test_the_protected_resource_metadata_leaks_nothing_but_the_public_url() -> None:
    """T-03-04: no secret, no request host, no version, no configuration. Set equality."""
    with client() as http:
        response = http.get(PRM_PATH, headers={"Host": "attacker.example"})
    body = response.text
    assert set(json.loads(body)) == {
        "resource",
        "authorization_servers",
        "scopes_supported",
        "bearer_methods_supported",
        "resource_name",
    }
    assert APP_SECRET not in body
    assert "attacker.example" not in body
    assert "nc.test" not in body
    assert "0.1.0" not in body
    assert "testserver" not in body


def test_the_protected_resource_metadata_ignores_a_forged_host_header() -> None:
    """T-03-02: the URL is configuration, not a heuristic over the request."""
    with client() as http:
        forged = http.get(PRM_PATH, headers={"Host": "evil.example:9999"}).text
        plain = http.get(PRM_PATH).text
    assert forged == plain
    assert json.loads(plain)["resource"] == f"{PUBLIC_URL}/mcp"


def test_the_protected_resource_metadata_ignores_a_stray_authorization_header() -> None:
    """A PUBLIC route reads no credentials: a smuggled header changes nothing."""
    with client() as http:
        with_auth = http.get(PRM_PATH, headers=stray_auth_headers())
        without = http.get(PRM_PATH)
    assert with_auth.status_code == 200
    assert with_auth.text == without.text


def test_the_documents_fall_back_to_the_default_public_url_when_unset() -> None:
    """Without NC_MCP_PUBLIC_URL every document reads the documented default.

    The issuer is checked as an exact string on purpose: RFC 8414 compares it byte for
    byte, and a URL without a path picks up a trailing slash on the way through the URL
    type of the SDK models. A client that built its discovery URL from the configured
    value would discard a document whose issuer carries that extra slash.
    """
    env = {key: value for key, value in ENV.items() if key != config.ENV_PUBLIC_URL}
    with client(env) as http:
        prm = http.get(PRM_PATH).json()
        as_document = http.get(OPENID_PATH).json()
    assert prm["resource"] == f"{config.DEFAULT_PUBLIC_URL}/mcp"
    assert prm["authorization_servers"] == [config.DEFAULT_PUBLIC_URL]
    assert as_document["issuer"] == config.DEFAULT_PUBLIC_URL


def test_the_protected_resource_metadata_serves_no_other_verb() -> None:
    with client() as http:
        assert http.post(PRM_PATH).status_code == 405


# --- the authorization server metadata (RFC 8414 and OpenID Connect Discovery) ----


def test_both_authorization_server_paths_answer_the_same_document_byte_for_byte() -> None:
    """One document, two ways: the path appended variant a client finds on its own, and
    the target of the reverse proxy rule for the canonical root path (pitfall 2)."""
    with client() as http:
        appended = http.get(OPENID_PATH)
        canonical = http.get(AUTHORIZATION_SERVER_PATH)
    assert appended.status_code == canonical.status_code == 200
    assert appended.text == canonical.text


def test_the_authorization_server_document_names_the_four_endpoints() -> None:
    with client() as http:
        body = http.get(OPENID_PATH).json()
    assert body["issuer"] == PUBLIC_URL
    assert body["authorization_endpoint"] == f"{PUBLIC_URL}/authorize"
    assert body["token_endpoint"] == f"{PUBLIC_URL}/token"
    assert body["registration_endpoint"] == f"{PUBLIC_URL}/register"
    assert body["revocation_endpoint"] == f"{PUBLIC_URL}/revoke"


def test_the_authorization_server_document_carries_the_three_own_additions() -> None:
    """The three fields the SDK does not set: the public client method, the scope list
    and the RFC 9207 issuer parameter."""
    with client() as http:
        body = http.get(OPENID_PATH).json()
    assert "none" in body["token_endpoint_auth_methods_supported"]
    assert body["scopes_supported"] == ["nextcloud", "offline_access"]
    assert body["authorization_response_iss_parameter_supported"] is True
    assert body["code_challenge_methods_supported"] == ["S256"]


def test_the_authorization_server_document_carries_no_other_field() -> None:
    """T-03-04: set equality, so an SDK upgrade cannot publish a new field unreviewed."""
    with client() as http:
        response = http.get(OPENID_PATH, headers={"Host": "attacker.example"})
    body = response.text
    assert set(json.loads(body)) == AS_FIELDS
    assert APP_SECRET not in body
    assert "attacker.example" not in body
    assert "nc.test" not in body
    assert "testserver" not in body


def test_no_field_of_any_document_is_null() -> None:
    """exclude_none: a document with null fields is harder to read for a client than one
    that omits what it does not offer, and RFC 8414 asks for omission."""
    with client() as http:
        for path in (PRM_PATH, OPENID_PATH, AUTHORIZATION_SERVER_PATH):
            body = http.get(path).json()
            assert None not in body.values(), path


def test_a_disabled_registration_removes_the_endpoint_from_the_document() -> None:
    """Plan 03-05 hands the DCR switch of the registry policy in here (AUTH-07). The
    document then stops advertising an endpoint that would refuse every call."""
    with client(dcr_enabled=False) as http:
        body = http.get(OPENID_PATH).json()
    assert "registration_endpoint" not in body
    assert body["token_endpoint"] == f"{PUBLIC_URL}/token"


def test_the_authorization_server_document_ignores_a_stray_authorization_header() -> None:
    with client() as http:
        with_auth = http.get(AUTHORIZATION_SERVER_PATH, headers=stray_auth_headers())
        without = http.get(AUTHORIZATION_SERVER_PATH)
    assert with_auth.status_code == 200
    assert with_auth.text == without.text


# --- cache control ---------------------------------------------------------------


def test_all_three_documents_carry_no_store() -> None:
    """T-03-03: createProxyResponse caches JSON for 3600 s unless Cache-Control is set,
    and the metadata handlers of the SDK would answer public, max-age=3600."""
    with client() as http:
        for path in (PRM_PATH, OPENID_PATH, AUTHORIZATION_SERVER_PATH):
            cache_control = http.get(path).headers["cache-control"]
            assert cache_control == "no-store", path


def test_extra_headers_never_cost_the_no_store() -> None:
    """IN-06: the helper promised that no-store cannot be forgotten, but a caller passing
    a non-empty header dict without Cache-Control used to replace the constant and the
    PHP proxy then cached the answer for an hour. Merging keeps the promise."""
    response = responses.json_response({}, headers={"WWW-Authenticate": "Bearer"})
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_caller_that_sets_cache_control_itself_wins() -> None:
    """The merge order is deliberate: an explicit Cache-Control is a decision, not an
    accident, and the default must not overrule it silently."""
    response = responses.json_response({}, headers={"Cache-Control": "no-store, max-age=0"})
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_no_headers_at_all_still_answer_no_store() -> None:
    response = responses.json_response({})
    assert response.headers["cache-control"] == "no-store"


# --- wiring ----------------------------------------------------------------------


def test_build_exapp_app_registers_exactly_the_three_well_known_routes() -> None:
    app = build_exapp_app(ENV)
    well_known = sorted(
        path
        for path in (getattr(route, "path", "") for route in app.router.routes)
        if "well-known" in path
    )
    assert well_known == sorted([PRM_PATH, OPENID_PATH, AUTHORIZATION_SERVER_PATH])


def test_the_spike_probe_route_is_gone() -> None:
    """The measurement probe of phase 2 was written to be replaced, not extended, and the
    401 of the discovery flow comes out of /mcp itself from this plan on."""
    with client() as http:
        assert http.get(PROBE_PATH).status_code == 404
    assert PROBE_PATH not in {
        getattr(route, "path", "") for route in build_exapp_app(ENV).router.routes
    }


def test_the_standalone_http_app_knows_none_of_the_routes() -> None:
    """D-23: phase 1 modes must not grow a .well-known route. Empty list, not a subset."""
    app = entry_http.build_app({config.ENV_URL: "http://nc.test"})
    well_known = [
        path
        for path in (getattr(route, "path", "") for route in app.router.routes)
        if "well-known" in path
    ]
    assert well_known == []
