"""The ExApp entry point and the boundary against the two phase 1 modes (D-23, D-27).

Nothing here starts a server: ``build_exapp_app`` is a pure function of its environment,
and every ``main`` case below exits before uvicorn is reached. Two regressions matter most
in this file. The standalone HTTP application of phase 1 must not grow a lifecycle route
or an AppAPI requirement just because the ExApp module exists, and the MCP route of the
ExApp application must never answer a request that carries no valid handshake (CR-01):
before the wrapper existed, an ``initialize`` without a single AppAPI header was answered
with 200 and a fresh session id.
"""

import base64

import pytest
from starlette.testclient import TestClient

from mcp_connector import config, entry_exapp, entry_http
from mcp_connector.errors import ToolError

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"

EXAPP_ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}
#: Behind HaRP the Host header is the one of the proxy, which is what the container sets
#: this to as well. Without it every request below would be answered with 421 instead.
SERVED_ENV = {**EXAPP_ENV, config.ENV_DISABLE_DNS_REBINDING: "1"}

LIFECYCLE_PATHS = {"/heartbeat", "/init", "/enabled"}

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}
MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def paths(app: object) -> set[str]:
    return {getattr(route, "path", "") for route in app.router.routes}  # type: ignore[attr-defined]


def appapi_headers(user: str = "alice", secret: str = APP_SECRET) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token,
    }


# --- the application -------------------------------------------------------------


def test_the_exapp_app_carries_the_three_lifecycle_routes() -> None:
    assert paths(entry_exapp.build_exapp_app(EXAPP_ENV)) >= LIFECYCLE_PATHS


def test_the_standalone_http_app_has_no_lifecycle_route() -> None:
    """D-23: phase 1 stays exactly as it was, whoever imported the ExApp package."""
    assert not LIFECYCLE_PATHS & paths(entry_http.build_app({}))


def test_the_exapp_app_still_serves_mcp() -> None:
    assert "/mcp" in paths(entry_exapp.build_exapp_app(EXAPP_ENV))


# --- the transport boundary (CR-01) ----------------------------------------------


@pytest.mark.parametrize(
    ("name", "headers"),
    [
        ("nothing at all", {}),
        ("only the app id", {"EX-APP-ID": APP_ID}),
        ("a wrong secret", appapi_headers(secret="not-the-secret")),
        ("a foreign app id", {**appapi_headers(), "EX-APP-ID": "other_app"}),
        ("a bearer instead", {"Authorization": "Bearer whatever"}),
    ],
)
def test_initialize_without_a_valid_handshake_is_rejected(
    name: str, headers: dict[str, str]
) -> None:
    """CR-01: the JSON-RPC preamble used to be served to anyone who reached the socket.

    Not a session, not a serverInfo, not a tool list: the request never reaches MCP code.
    """
    with TestClient(entry_exapp.build_exapp_app(SERVED_ENV)) as client:
        response = client.post("/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **headers})

    assert response.status_code == 401, name
    assert response.content == b"", name
    assert "mcp-session-id" not in {key.lower() for key in response.headers}, name
    assert response.headers["cache-control"] == "no-store", name


@pytest.mark.parametrize("user", ["alice", ""])
def test_initialize_with_a_valid_handshake_is_served(user: str) -> None:
    """The empty user id is the app context and passes the boundary on purpose (T-02-12).

    Refusing it belongs to the credential layer, which is where the data access is.
    """
    with TestClient(entry_exapp.build_exapp_app(SERVED_ENV)) as client:
        response = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user=user)}
        )

    assert response.status_code == 200
    assert "protocolVersion" in response.text


def test_a_duplicated_route_wrap_is_a_build_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The counter probe: a silently unwrapped MCP route is the whole finding CR-01."""
    original = entry_exapp.MCP_PATH
    monkeypatch.setattr(entry_exapp, "MCP_PATH", "/not-a-route")

    with pytest.raises(RuntimeError, match="without the AppAPI handshake"):
        entry_exapp.build_exapp_app(EXAPP_ENV)

    assert original == "/mcp"


def test_the_standalone_http_app_serves_mcp_without_any_appapi_header() -> None:
    """D-23: phase 1 has no AppAPI identity, so it must not grow a handshake it cannot
    satisfy. This is the regression guard for the fix of CR-01."""
    with TestClient(entry_http.build_app({config.ENV_DISABLE_DNS_REBINDING: "1"})) as client:
        response = client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)

    assert response.status_code == 200
    assert "protocolVersion" in response.text


# --- the other direction of the mode switch (WR-03) -------------------------------


def test_ambient_appapi_variables_stop_the_standalone_http_app() -> None:
    """WR-03: APP_ID and APP_SECRET are the two mode switches without an NC_MCP_ prefix,
    and they are common names. A base image or a CI variable that sets them used to flip
    a phase 1 server into the ExApp credential mode without touching its configuration,
    which locks out every user of a passthrough deployment."""
    env = {config.ENV_APP_ID: "some-github-app", config.ENV_APP_SECRET: "some-other-thing"}
    assert config.select_mode(env, headers={}) == "exapp", "the counter probe stopped working"

    with pytest.raises(ToolError) as excinfo:
        entry_http.build_app(env)

    assert config.ENV_APP_SECRET in excinfo.value.message
    assert "nc-mcp-exapp" in excinfo.value.hint


@pytest.mark.parametrize(
    "env",
    [
        {},
        {config.ENV_APP_ID: "mcp_connector"},
        {config.ENV_APP_SECRET: "app-secret-test"},
        {config.ENV_APP_ID: "mcp_connector", config.ENV_APP_SECRET: "   "},
    ],
    ids=["nothing set", "only the id", "only the secret", "a blank secret"],
)
def test_the_guard_leaves_every_other_http_deployment_alone(env: dict[str, str]) -> None:
    """A blank value is a typo in a compose file, not a request to change the mode, and
    one of the two variables alone never selected the ExApp mode either."""
    assert "/mcp" in paths(entry_http.build_app(env))


# --- the startup validation ------------------------------------------------------


@pytest.mark.parametrize("conflicting", [config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD])
def test_a_second_credential_channel_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, conflicting: str
) -> None:
    """T-02-08: an ExApp process with a second way to authenticate is a misconfiguration."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(config.ENV_STATIC_BEARER, raising=False)
    monkeypatch.delenv(config.ENV_APP_PASSWORD, raising=False)
    monkeypatch.setenv(conflicting, "something")

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


def test_a_missing_deploy_variable_stops_the_start(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*EXAPP_ENV, config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(config.ENV_APP_ID, "mcp_connector")

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


@pytest.mark.parametrize("port", [None, "", "not-a-number"])
def test_a_missing_or_broken_port_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, port: str | None
) -> None:
    """A ValueError traceback out of int() would tell an administrator nothing."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    for name in (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD, config.ENV_HP_SHARED_KEY):
        monkeypatch.delenv(name, raising=False)
    if port is None:
        monkeypatch.delenv(config.ENV_APP_PORT, raising=False)
    else:
        monkeypatch.setenv(config.ENV_APP_PORT, port)

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2
