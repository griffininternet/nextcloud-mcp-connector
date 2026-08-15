"""The ExApp entry point and the boundary against the two phase 1 modes (D-23, D-27).

Nothing here starts a server: ``build_exapp_app`` is a pure function of its environment,
and every ``main`` case below exits before uvicorn is reached. Three regressions matter most
in this file. The standalone HTTP application of phase 1 must not grow a lifecycle route
or an AppAPI requirement just because the ExApp module exists, the MCP route of the
ExApp application must never answer a request that carries no valid handshake (CR-01):
before the wrapper existed, an ``initialize`` without a single AppAPI header was answered
with 200 and a fresh session id. And since plan 03-01 the route is declared PUBLIC, so HaRP
no longer decides who reaches it: an AppAPI context without a user id has to pass our own
bearer check or leave with a 401 that points at the metadata (pitfall 6, T-03-01).
"""

import base64

import pytest
from mcp.server.auth.provider import AccessToken
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_connector import config, entry_exapp, entry_http
from mcp_connector.errors import ToolError
from mcp_connector.exapp.middleware import RequireAppApi
from mcp_connector.oauth.metadata import PRM_SUFFIX, TOOL_SCOPE

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"

EXAPP_ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}
#: Behind HaRP the Host header is the one of the proxy, which is what the container sets
#: this to as well. Without it every request below would be answered with 421 instead.
SERVED_ENV = {**EXAPP_ENV, config.ENV_DISABLE_DNS_REBINDING: "1"}
#: The same environment with a configured public URL, so the pointer in the 401 can be
#: asserted as a whole string instead of as a fragment.
OAUTH_ENV = {**SERVED_ENV, config.ENV_PUBLIC_URL: PUBLIC_URL}

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


class StubVerifier:
    """The one method of the SDK ``TokenVerifier`` protocol, over one accepted token.

    Plan 03-06 puts the real verifier here. Until then the boundary is built with ``None``,
    which is the fail-closed state: no verifier means no valid bearer exists.
    """

    def __init__(self, accepted: str | None = None) -> None:
        self._accepted = accepted
        self.seen: list[str] = []

    async def verify_token(self, token: str) -> AccessToken | None:
        self.seen.append(token)
        if self._accepted is not None and token == self._accepted:
            return AccessToken(token=token, client_id="test-client", scopes=[TOOL_SCOPE])
        return None


def guarded_app(verifier: StubVerifier | None = None) -> Starlette:
    """One route behind the real boundary, so a verifier can be handed in.

    ``build_exapp_app`` builds the MCP transport behind the same wrapper but takes no
    verifier yet (plan 03-06 wires it). This little application drives the branches of the
    wrapper itself, including the one that hands a token to a verifier.
    """

    async def served(request: Request) -> Response:
        return PlainTextResponse("served")

    app = Starlette(routes=[Route("/mcp", served, methods=["GET", "POST"])])
    for route in app.router.routes:
        if isinstance(route, Route):
            route.app = RequireAppApi(route.app, OAUTH_ENV, token_verifier=verifier)
    return app


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
    # An invalid handshake says nothing at all, not even which scheme would work: the
    # caller behind those headers is a proxy, not an OAuth client (T-02-03).
    assert "www-authenticate" not in {key.lower() for key in response.headers}, name


def test_initialize_with_a_valid_handshake_is_served() -> None:
    """A resolved Nextcloud user is the AUTH-01 path and is not asked for a bearer."""
    with TestClient(entry_exapp.build_exapp_app(SERVED_ENV)) as client:
        response = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="alice")}
        )

    assert response.status_code == 200
    assert "protocolVersion" in response.text


# --- the second identity source of the same boundary (T-03-01, T-03-06) -----------


def test_an_empty_user_without_a_bearer_gets_the_discovery_401() -> None:
    """The 401 that starts the OAuth flow, out of /mcp itself and not out of HaRP.

    Until phase 2 the empty user id was the app context and passed on purpose (T-02-12);
    since /mcp is PUBLIC it is also what an anonymous caller produces, so the second check
    of this boundary decides here instead of at the credential layer.
    """
    with TestClient(entry_exapp.build_exapp_app(OAUTH_ENV)) as client:
        response = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="")}
        )

    assert response.status_code == 401
    assert response.content == b""
    assert response.headers["cache-control"] == "no-store"
    challenge = response.headers["www-authenticate"]
    assert challenge.startswith('Bearer error="invalid_token"')
    assert f'scope="{TOOL_SCOPE}"' in challenge
    assert f'resource_metadata="{PUBLIC_URL}{PRM_SUFFIX}"' in challenge
    assert "offline_access" not in challenge


@pytest.mark.parametrize(
    "authorization",
    ["Bearer whatever", "Bearer ", "bearer lower-case-scheme", "Basic YWxpY2U6cHc=", ""],
    ids=["a token", "an empty token", "a lower case scheme", "another scheme", "no header"],
)
def test_an_empty_user_is_refused_for_every_bearer_while_no_verifier_exists(
    authorization: str,
) -> None:
    """Fail-closed: without a verifier every bearer is invalid, never 200 and never 500."""
    headers = {**MCP_HEADERS, **appapi_headers(user="")}
    if authorization:
        headers["Authorization"] = authorization

    with TestClient(entry_exapp.build_exapp_app(OAUTH_ENV)) as client:
        response = client.post("/mcp", json=INITIALIZE, headers=headers)

    assert response.status_code == 401
    assert "resource_metadata=" in response.headers["www-authenticate"]


def test_the_401_of_the_bearer_boundary_never_repeats_the_token() -> None:
    """T-03-06: not in the body, not in a header, not in the challenge."""
    secret_token = "5f4dcc3b5aa765d61d8327deb882cf99"
    headers = {
        **MCP_HEADERS,
        **appapi_headers(user=""),
        "Authorization": f"Bearer {secret_token}",
    }

    with TestClient(entry_exapp.build_exapp_app(OAUTH_ENV)) as client:
        response = client.post("/mcp", json=INITIALIZE, headers=headers)

    assert response.status_code == 401
    assert secret_token not in response.text
    for key, value in response.headers.items():
        assert secret_token not in value, key


def test_a_verified_bearer_reaches_the_route_behind_the_boundary() -> None:
    """The other direction of the same branch, with the verifier plan 03-06 will hand in."""
    verifier = StubVerifier(accepted="a-good-token")

    with TestClient(guarded_app(verifier)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-good-token"}
        )

    assert response.status_code == 200
    assert response.text == "served"
    assert verifier.seen == ["a-good-token"]


def test_a_rejected_bearer_stops_at_the_boundary() -> None:
    verifier = StubVerifier(accepted="a-good-token")

    with TestClient(guarded_app(verifier)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-stolen-token"}
        )

    assert response.status_code == 401
    assert "resource_metadata=" in response.headers["www-authenticate"]
    assert verifier.seen == ["a-stolen-token"]


def test_a_resolved_user_is_never_asked_for_a_bearer() -> None:
    """Two identity sources, one branch each: no fallback from one to the other (D-27)."""
    verifier = StubVerifier(accepted="a-good-token")

    with TestClient(guarded_app(verifier)) as client:
        response = client.get(
            "/mcp",
            headers={**appapi_headers(user="alice"), "Authorization": "Bearer a-stolen-token"},
        )

    assert response.status_code == 200
    assert verifier.seen == [], "the AUTH-01 path read the Authorization header"


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


@pytest.mark.parametrize(
    ("env", "warned"),
    [
        ({}, True),
        ({config.ENV_HP_SHARED_KEY: "x" * 64}, False),
        ({config.ENV_ALLOWED_HOSTS: "harp.example"}, False),
        ({config.ENV_DISABLE_DNS_REBINDING: "1"}, False),
        ({config.ENV_HP_SHARED_KEY: "   ", config.ENV_ALLOWED_HOSTS: ""}, True),
    ],
    ids=[
        "neither key nor allowlist",
        "harp path selected",
        "allowlist set",
        "host check disabled",
        "blank values do not count as a decision",
    ],
)
def test_the_421_trap_of_a_daemon_without_harp_is_named_at_startup(
    caplog: pytest.LogCaptureFixture, env: dict[str, str], warned: bool
) -> None:
    """IN-04: without HaRP the Host header is the container name, the check stays armed
    with the localhost default, and every /mcp request dies as a 421 while the
    installation looks green. The warning names it once; an operator who set the
    allowlist, the shared key or the rebinding switch already decided."""
    with caplog.at_level("WARNING", logger="mcp_connector.entry_exapp"):
        entry_exapp._warn_when_the_host_check_is_a_trap(env)

    messages = [record.getMessage() for record in caplog.records]
    assert any(config.ENV_ALLOWED_HOSTS in message for message in messages) is warned, messages


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
