"""The HTTP entry point: host allowlist, health endpoint and auth wiring (SRV-01).

Everything here runs in process against the ASGI app with Starlette's TestClient. No
uvicorn, no Docker, no Nextcloud: the client matrix test covers the real socket, this
file covers the decisions that are cheap to get wrong and expensive to debug in
production, above all the 421 of pitfall 6.
"""

import json

from starlette.testclient import TestClient

from mcp_connector import __version__, config, entry_http
from mcp_connector.server import mcp

MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "gsd-transport-check", "version": "0.0.0"},
    },
}


def post_mcp(app: object, host: str) -> int:
    """POST /mcp with an explicit Host header and return the status code.

    Every test builds its own app: the SDK session manager of one application object may
    be started exactly once, so a shared app would fail on the second lifespan instead of
    on the assertion.
    """
    with TestClient(app, base_url=f"http://{host}") as client:  # type: ignore[arg-type]
        response = client.post("/mcp", headers=MCP_HEADERS, content=json.dumps(INITIALIZE))
    return response.status_code


def test_health_answers_200_with_compact_json() -> None:
    with TestClient(entry_http.build_app({})) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == __version__


def test_health_leaks_no_configuration() -> None:
    """T-01-29: a public unauthenticated endpoint says that it lives, nothing else."""
    app = entry_http.build_app(
        {
            config.ENV_ALLOWED_HOSTS: "internal.example.com",
            config.ENV_URL: "https://cloud.internal.example.com",
            config.ENV_USER: "alice",
        }
    )
    with TestClient(app, base_url="http://internal.example.com") as client:
        body = client.get("/health").text

    assert "internal.example.com" not in body
    assert "alice" not in body
    assert set(json.loads(body)) == {"status", "version"}


def test_a_foreign_host_header_is_rejected_with_421() -> None:
    """Pitfall 6: the check runs before any MCP code, the client only sees a transport error."""
    assert post_mcp(entry_http.build_app({}), "evil.example") == 421


def test_an_allowed_host_is_served() -> None:
    app = entry_http.build_app({config.ENV_ALLOWED_HOSTS: "mcp.example.com"})
    assert post_mcp(app, "mcp.example.com") != 421


def test_an_allowed_host_is_served_with_a_port() -> None:
    """The Host header carries the port, so the allowlist must carry it too."""
    app = entry_http.build_app({config.ENV_ALLOWED_HOSTS: "mcp.example.com"})
    assert post_mcp(app, "mcp.example.com:8765") != 421


def test_localhost_is_the_default_allowlist() -> None:
    assert post_mcp(entry_http.build_app({}), "127.0.0.1:8765") != 421


def test_the_protection_can_be_disabled_for_a_reverse_proxy() -> None:
    app = entry_http.build_app({config.ENV_DISABLE_DNS_REBINDING: "true"})
    assert post_mcp(app, "behind-a-proxy.example") != 421


def test_the_app_is_importable_for_uvicorn() -> None:
    assert entry_http.app is not None


def test_passthrough_mode_configures_no_sdk_auth_layer() -> None:
    """Pitfall 2: with the bearer layer armed, every Basic request would 401 before a tool."""
    assert mcp.settings.auth is None


def test_static_bearer_mode_configures_both_halves() -> None:
    from mcp_connector import deps

    verifier, settings = deps.build_auth({config.ENV_STATIC_BEARER: "a-static-token"})
    assert verifier is not None
    assert settings is not None
