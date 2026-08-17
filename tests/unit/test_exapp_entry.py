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

import asyncio
import base64
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest
from mcp.server.auth.provider import AccessToken
from mcp.shared.auth import OAuthClientInformationFull
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_connector import config, entry_exapp, entry_http
from mcp_connector.errors import ToolError
from mcp_connector.exapp.middleware import RequireAppApi
from mcp_connector.exapp.ui import connections as ui_connections
from mcp_connector.exapp.ui import strings
from mcp_connector.oauth import connections, crypto, store
from mcp_connector.oauth.metadata import PRM_SUFFIX, RESOURCE_SUFFIX, TOOL_SCOPE
from mcp_connector.oauth.verifier import OAUTH_STATE_ATTR, OAuthIdentity, StoreTokenVerifier

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

#: The registration behind the connection the end to end guard of this phase acts on, and
#: the bearer that connection was issued. Both are values of this file and of nothing else.
CONNECTED_CLIENT_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000001"
CONNECTED_TOKEN = "an-access-token-of-alice"

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

    A verifier that answers nothing about the identity behind a token, which is what the
    SDK protocol is: the boundary may let such a token through, and the credential layer
    then has nothing to act on. ``None`` instead of a verifier stays the fail-closed state.
    """

    def __init__(self, accepted: str | None = None) -> None:
        self._accepted = accepted
        self.seen: list[str] = []

    async def verify_token(self, token: str) -> AccessToken | None:
        self.seen.append(token)
        if self._accepted is not None and token == self._accepted:
            return AccessToken(token=token, client_id="test-client", scopes=[TOOL_SCOPE])
        return None


class StubSource(StubVerifier):
    """The verifier of this app: it also says whose connection a token is (plan 03-06)."""

    def __init__(self, accepted: str | None = None, identity: OAuthIdentity | None = None) -> None:
        super().__init__(accepted)
        self._identity = identity

    async def resolve_identity(self, access: AccessToken) -> OAuthIdentity | None:
        del access
        return self._identity


class StubSwitch:
    """The per account switch of the boundary, over a set of paused accounts (EXAPP-02).

    The shape ``entry_exapp`` hands in: one async call that takes a Nextcloud account and
    answers whether that account paused its MCP access. ``asked`` is what the tests of the
    check order assert on, because "was never asked" is the property that keeps an invalid
    token from learning whether an account exists.
    """

    def __init__(self, paused: set[str] | None = None, *, breaks: bool = False) -> None:
        self.paused = set(paused or ())
        self.breaks = breaks
        self.asked: list[str] = []

    async def __call__(self, nc_user: str) -> bool:
        self.asked.append(nc_user)
        if self.breaks:
            raise RuntimeError("the store of this deployment cannot be read")
        return nc_user in self.paused


def with_a_local_store(
    base: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, str], list[str]]:
    """An environment with a store in ``tmp_path`` and a data key that costs no network.

    The one thing a unit test cannot have is the OCS round trip that fetches the data key of
    this installation, and since the transport boundary reads the per account switch, every
    served request needs the store that holds it. The returned list counts the key fetches,
    which is how the tests below assert that opening the store is a once per process cost and
    not a Nextcloud round trip per MCP request (SC 5 of phase 3, D-47).
    """
    fetched: list[str] = []

    async def fake_key(env: object = None) -> bytes:
        del env
        fetched.append("key")
        return bytes(range(32))

    monkeypatch.setattr(store.crypto, "data_key", fake_key)
    return {**base, config.ENV_APP_PERSISTENT_STORAGE: str(tmp_path)}, fetched


def guarded_app(
    verifier: StubVerifier | None = None,
    switch: Callable[[str], Awaitable[bool]] | None = None,
) -> Starlette:
    """One route behind the real boundary, so a verifier and a switch can be handed in.

    The route answers with the identity the boundary deposited, when there is one: that is
    the hand over the credential layer of ``deps.py`` reads on every tool call.
    """

    async def served(request: Request) -> Response:
        identity = getattr(request.state, OAUTH_STATE_ATTR, None)
        return PlainTextResponse("served" if identity is None else f"served as {identity.nc_user}")

    app = Starlette(routes=[Route("/mcp", served, methods=["GET", "POST"])])
    for route in app.router.routes:
        if isinstance(route, Route):
            route.app = RequireAppApi(
                route.app, OAUTH_ENV, token_verifier=verifier, access_check=switch
            )
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


def test_initialize_with_a_valid_handshake_is_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resolved Nextcloud user is the AUTH-01 path and is not asked for a bearer.

    Since plan 04-01 this path reads the per account switch as well, so the application
    needs the store it reads it from: a local file and a data key that does not come over
    the network in a unit test. An account that never paused anything has no row there, and
    a request of that account is served exactly as it was before the switch existed.
    """
    env, _ = with_a_local_store(SERVED_ENV, tmp_path, monkeypatch)

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
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


def test_a_verified_bearer_leaves_its_identity_for_the_credential_layer() -> None:
    """The hand over of plan 03-06: the boundary resolves, the tool call reads (D-26)."""
    identity = OAuthIdentity(
        nc_user="alice", app_password="app-password", auth_id="auth-1", client_id="client-1"
    )
    source = StubSource(accepted="a-good-token", identity=identity)

    with TestClient(guarded_app(source)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-good-token"}
        )

    assert response.status_code == 200
    assert response.text == "served as alice"


def test_a_token_whose_connection_is_gone_stops_at_the_boundary() -> None:
    """Fail closed: a token this server cannot turn into an identity is not a valid one."""
    source = StubSource(accepted="a-good-token", identity=None)

    with TestClient(guarded_app(source)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-good-token"}
        )

    assert response.status_code == 401
    assert "resource_metadata=" in response.headers["www-authenticate"]


def test_the_mcp_route_is_guarded_with_the_verifier_of_this_deployment() -> None:
    """Plan 03-06 wires the real verifier, at the one place the boundary is built."""
    app = entry_exapp.build_exapp_app(OAUTH_ENV)

    guards = [
        route.app
        for route in app.router.routes
        if isinstance(route, Route) and route.path == entry_exapp.MCP_PATH
    ]

    assert len(guards) == 1
    guard = guards[0]
    assert isinstance(guard, RequireAppApi)
    assert isinstance(guard._token_verifier, StoreTokenVerifier)


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


# --- the per account switch of the same boundary (EXAPP-02, R1, D-49) --------------


def test_a_paused_account_is_refused_on_the_appapi_branch() -> None:
    """D-49: the switch blocks the app password way in, and the answer is R1, not a 401."""
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(switch=switch)) as client:
        response = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert response.status_code == 403
    assert json.loads(response.text)["error"] == "access_disabled"
    assert switch.asked == ["alice"]


def test_a_paused_account_is_refused_on_the_oauth_branch_as_well() -> None:
    """The other way in, same account, same answer: one decision for both (D-49)."""
    identity = OAuthIdentity(
        nc_user="alice", app_password="app-password", auth_id="auth-1", client_id="client-1"
    )
    source = StubSource(accepted="a-good-token", identity=identity)
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(source, switch)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-good-token"}
        )

    assert response.status_code == 403
    assert json.loads(response.text)["error"] == "access_disabled"
    assert switch.asked == ["alice"], "the identity of the token is what the switch is asked about"


def test_the_refusal_of_a_paused_account_is_the_wire_contract_of_the_ui_spec() -> None:
    """R1 word for word: 403, the named code, the sentence, no challenge, no-store.

    The missing ``WWW-Authenticate`` is the deliberate deviation from RFC 6750: there is no
    other scope and no other credential to come back with, and the header is what would pull
    an OAuth client into the whole discovery loop again for a decision its user made.
    """
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(switch=switch)) as client:
        response = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert response.status_code == 403
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"].startswith("application/json")
    assert "www-authenticate" not in {key.lower() for key in response.headers}
    body = json.loads(response.text)
    assert body == {
        "error": "access_disabled",
        "error_description": strings.ACCESS_DISABLED_DESCRIPTION,
    }
    assert strings.SETTINGS_PLACE in body["error_description"], "the sentence names the place"
    # T-03-66: the sentence states the rule, never a value out of the request.
    assert "alice" not in response.text
    assert APP_SECRET not in response.text


def test_an_invalid_bearer_of_a_paused_account_is_still_the_discovery_401() -> None:
    """The check order is the security here (pitfall 2): handshake, credential, switch.

    A 403 in front of the credential check would tell anyone who guesses an account name
    that the account exists and that it paused its access.
    """
    verifier = StubVerifier(accepted="a-good-token")
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(verifier, switch)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-stolen-token"}
        )

    assert response.status_code == 401
    assert "resource_metadata=" in response.headers["www-authenticate"]
    assert switch.asked == [], "an unauthenticated caller must not reach the switch at all"


def test_a_broken_handshake_of_a_paused_account_is_still_the_bare_401() -> None:
    """R3 is unchanged, and it stays first: no detail, no challenge, no switch (T-02-03)."""
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(switch=switch)) as client:
        response = client.get("/mcp", headers={"EX-APP-ID": APP_ID})

    assert response.status_code == 401
    assert response.content == b""
    assert "www-authenticate" not in {key.lower() for key in response.headers}
    assert switch.asked == []


def test_the_app_context_is_never_asked_for_a_switch() -> None:
    """Pitfall 10: an empty resolved identity has no switch, and the bearer already decided."""
    verifier = StubVerifier(accepted="a-good-token")
    switch = StubSwitch(paused={"alice"})

    with TestClient(guarded_app(verifier, switch)) as client:
        response = client.get(
            "/mcp", headers={**appapi_headers(user=""), "Authorization": "Bearer a-good-token"}
        )

    assert response.status_code == 200
    assert response.text == "served"
    assert switch.asked == []


def test_flipping_the_switch_takes_effect_on_the_very_next_request() -> None:
    """D-48 and D-46 in one run, on one application instance and one token.

    No cache may soften the pause, and switching back on restores the connection without a
    new sign in: the same credential is served again on the third request.
    """
    switch = StubSwitch()

    with TestClient(guarded_app(switch=switch)) as client:
        before = client.get("/mcp", headers=appapi_headers(user="alice"))
        switch.paused.add("alice")
        paused = client.get("/mcp", headers=appapi_headers(user="alice"))
        switch.paused.discard("alice")
        after = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert before.status_code == 200
    assert paused.status_code == 403
    assert after.status_code == 200
    assert switch.asked == ["alice", "alice", "alice"], "every request reads the switch again"


def test_the_switch_of_the_real_store_reaches_the_boundary(tmp_path: Path) -> None:
    """The end to end guard of this plan, with the store instead of a stub.

    A test that only checked the store round trip would stay green with no gate in the
    boundary at all, which is the whole of pitfall 1: the write is flipped behind the
    running application, and the very next request has to be the refusal.
    """
    subject = store.OAuthStore(tmp_path / store.STORE_FILENAME, bytes(range(32)))

    with TestClient(guarded_app(switch=subject.access_disabled)) as client:
        before = client.get("/mcp", headers=appapi_headers(user="alice"))
        asyncio.run(subject.set_access("alice", disabled=True))
        paused = client.get("/mcp", headers=appapi_headers(user="alice"))
        asyncio.run(subject.set_access("alice", disabled=False))
        after = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert before.status_code == 200
    assert paused.status_code == 403
    assert json.loads(paused.text)["error"] == "access_disabled"
    assert after.status_code == 200


def test_a_store_that_cannot_answer_the_switch_refuses_instead_of_letting_through(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Fail closed (the D-37 analogy): a store outage is not a decision of the user.

    So it is neither a pass through nor a claim that the account paused its access. It is a
    503 that says nothing else, plus one log line for the administrator.
    """
    switch = StubSwitch(breaks=True)

    with (
        caplog.at_level("ERROR", logger="mcp_connector.exapp.middleware"),
        TestClient(guarded_app(switch=switch)) as client,
    ):
        response = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert response.status_code == 503
    assert response.content == b""
    assert response.headers["cache-control"] == "no-store"
    assert "access_disabled" not in response.text
    assert caplog.records, "a store that cannot be read has to say so once"


def test_a_boundary_without_a_switch_serves_exactly_as_before() -> None:
    """The default of the new parameter is the behaviour of phase 3, unchanged."""
    with TestClient(guarded_app()) as client:
        response = client.get("/mcp", headers=appapi_headers(user="alice"))

    assert response.status_code == 200
    assert response.text == "served"


def test_the_mcp_route_is_guarded_with_the_switch_of_this_deployment() -> None:
    """The wiring: the store that holds the tokens is the store that holds the switch."""
    app = entry_exapp.build_exapp_app(OAUTH_ENV)

    guards = [
        route.app
        for route in app.router.routes
        if isinstance(route, Route) and route.path == entry_exapp.MCP_PATH
    ]

    assert len(guards) == 1
    guard = guards[0]
    assert isinstance(guard, RequireAppApi)
    assert guard._access_check is not None, "the boundary was built without the switch"


def test_the_switch_costs_no_nextcloud_round_trip_per_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC 5 of phase 3, which this phase may not worsen: one round trip per MCP call.

    The switch is a local read, and the one network call the store needs at all, the data key
    of this installation, is paid once per process by the opener both halves share. Three
    served requests therefore fetch it once, and nothing else of the switch leaves the
    container.
    """
    env, fetched = with_a_local_store(SERVED_ENV, tmp_path, monkeypatch)

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
        for _ in range(3):
            response = client.post(
                "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="alice")}
            )
            assert response.status_code == 200

    assert fetched == ["key"], "the store was opened per request instead of per process"


def test_a_paused_account_is_refused_by_the_wired_application(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole chain of this plan in one test: store, wiring, boundary, R1.

    The switch is flipped in the file the running application reads, behind its back and
    between two requests, which is what "the flip takes effect on the next request" means
    (D-48). Nothing is disconnected by it, and turning it back on serves the same caller
    again without a new sign in (D-46).
    """
    env, _ = with_a_local_store(SERVED_ENV, tmp_path, monkeypatch)
    subject = store.OAuthStore(tmp_path / store.STORE_FILENAME, bytes(range(32)))

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
        before = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="alice")}
        )
        asyncio.run(subject.set_access("alice", disabled=True))
        paused = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="alice")}
        )
        other = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="bob")}
        )
        asyncio.run(subject.set_access("alice", disabled=False))
        after = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="alice")}
        )

    assert before.status_code == 200
    assert paused.status_code == 403
    assert json.loads(paused.text) == {
        "error": "access_disabled",
        "error_description": strings.ACCESS_DISABLED_DESCRIPTION,
    }
    assert "www-authenticate" not in {key.lower() for key in paused.headers}
    assert paused.headers["cache-control"] == "no-store"
    assert other.status_code == 200, "the switch of one account is not the switch of another"
    assert after.status_code == 200


def test_the_switch_is_decided_at_the_boundary_and_nowhere_else() -> None:
    """One source for one sentence: no tool may carry a second copy of this decision."""
    tools = Path("src/mcp_connector/tools").glob("*.py")
    offenders = [path.name for path in tools if "access_disabled" in path.read_text("utf-8")]

    assert offenders == []


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


def test_a_missing_persistent_volume_stops_the_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-03-15: a store without a volume loses every authorization on the next restart,
    and it does so silently in production, weeks after the install looked green."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    for name in (
        config.ENV_STATIC_BEARER,
        config.ENV_APP_PASSWORD,
        config.ENV_APP_PERSISTENT_STORAGE,
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


def test_the_missing_volume_names_itself_in_the_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    for name in (
        config.ENV_STATIC_BEARER,
        config.ENV_APP_PASSWORD,
        config.ENV_APP_PERSISTENT_STORAGE,
    ):
        monkeypatch.delenv(name, raising=False)

    with caplog.at_level("ERROR", logger="mcp_connector.entry_exapp"), pytest.raises(SystemExit):
        entry_exapp.main()

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert config.ENV_APP_PERSISTENT_STORAGE in messages
    assert APP_SECRET not in messages


@pytest.mark.parametrize("port", [None, "", "not-a-number"])
def test_a_missing_or_broken_port_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, port: str | None
) -> None:
    """A ValueError traceback out of int() would tell an administrator nothing."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv(config.ENV_APP_PERSISTENT_STORAGE, str(tmp_path))
    for name in (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD, config.ENV_HP_SHARED_KEY):
        monkeypatch.delenv(name, raising=False)
    if port is None:
        monkeypatch.delenv(config.ENV_APP_PORT, raising=False)
    else:
        monkeypatch.setenv(config.ENV_APP_PORT, port)

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


def test_a_missing_public_url_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """WR-09: the one value an installation has to set, and the one whose absence is silent.

    A missing volume loses connections on the next restart and an unusable issuer refuses to
    build; both already stop the start. A missing public URL did neither: the container came
    up, answered every discovery document, and named `http://127.0.0.1:8765` as the issuer,
    the audience of every token and the target of the consent redirect. Every browser was
    then sent to its own machine, and nothing in the log said why.
    """
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv(config.ENV_APP_PERSISTENT_STORAGE, str(tmp_path))
    for name in (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD, config.ENV_PUBLIC_URL):
        monkeypatch.delenv(name, raising=False)

    with (
        caplog.at_level("ERROR", logger="mcp_connector.entry_exapp"),
        pytest.raises(SystemExit) as excinfo,
    ):
        entry_exapp.main()

    assert excinfo.value.code == 2
    messages = [record.getMessage() for record in caplog.records]
    assert any(config.ENV_PUBLIC_URL in message for message in messages), messages
    assert any(config.DEFAULT_PUBLIC_URL in message for message in messages), messages


def test_a_blank_public_url_counts_as_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A quoted empty value in a compose file is a typo, not a decision to use the default.

    The exit code alone would not prove anything here, because a later check refuses the
    start as well; what is asserted is that this value is the one named in the log.
    """
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv(config.ENV_APP_PERSISTENT_STORAGE, str(tmp_path))
    monkeypatch.setenv(config.ENV_PUBLIC_URL, "   ")
    for name in (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD):
        monkeypatch.delenv(name, raising=False)

    with (
        caplog.at_level("ERROR", logger="mcp_connector.entry_exapp"),
        pytest.raises(SystemExit) as excinfo,
    ):
        entry_exapp.main()

    assert excinfo.value.code == 2
    messages = [record.getMessage() for record in caplog.records]
    assert any(config.ENV_PUBLIC_URL in message for message in messages), messages


# --- the end to end guard of phase 4: the hand on the switch, and the refusal ------


def a_connected_account(
    tmp_path: Path, *, nc_user: str = "alice", token: str = CONNECTED_TOKEN
) -> store.OAuthStore:
    """One registered client and one live OAuth connection of that account, in the store.

    Written straight into the file the application opens, because what this guard is about
    happens after the connection exists: everything from the sign in to the consent has its
    own tests, and repeating the whole dance here would test those again instead of this.
    """
    subject = store.OAuthStore(tmp_path / store.STORE_FILENAME, bytes(range(32)))
    registration = OAuthClientInformationFull.model_validate(
        {
            "client_id": CONNECTED_CLIENT_ID,
            "client_name": "Claude",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "scope": TOOL_SCOPE,
        }
    ).model_dump_json(exclude={"client_secret"})
    asyncio.run(subject.save_client(CONNECTED_CLIENT_ID, metadata_json=registration, allowed=True))
    asyncio.run(subject.touch_client(CONNECTED_CLIENT_ID))
    asyncio.run(
        subject.create_authorization(
            f"authorization-of-{nc_user}",
            client_id=CONNECTED_CLIENT_ID,
            nc_user=nc_user,
            app_password="aaaaa-bbbbb-ccccc-ddddd-eeeee",
            scopes=TOOL_SCOPE,
            resource=f"{PUBLIC_URL}{RESOURCE_SUFFIX}",
        )
    )
    asyncio.run(
        subject.create_access_token(
            token,
            auth_id=f"authorization-of-{nc_user}",
            family_id=f"family-of-{nc_user}",
            scopes=TOOL_SCOPE,
            resource=f"{PUBLIC_URL}{RESOURCE_SUFFIX}",
        )
    )
    return subject


def switch_form(subject: store.OAuthStore, action: str, nc_user: str = "alice") -> dict[str, str]:
    """The form the page renders for that account, with the anti forgery value it carries."""
    return {
        ui_connections.ACTION_FIELD: action,
        ui_connections.CONFIRM_PARAM: subject.form_token(
            f"{connections.SWITCH_HANDLE}{nc_user}", purpose=crypto.PURPOSE_SWITCH
        ),
    }


def bearer_call(client: TestClient, token: str) -> Any:
    """One MCP request of a connected client: the OAuth branch of the boundary."""
    return client.post(
        "/mcp",
        json=INITIALIZE,
        headers={**MCP_HEADERS, **appapi_headers(user=""), "Authorization": f"Bearer {token}"},
    )


def test_the_switch_on_the_page_refuses_the_very_next_call_of_that_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The end to end guard of this phase (SC 1): a hand on the switch, and the refusal.

    Everything is the wired application: the user posts the pause form of ``/connections``
    under their own AppAPI identity, and the very next MCP call of their assistant, with a
    token that has not changed, is R1. A test that only checked the store round trip would
    stay green with no gate in the boundary at all, which is exactly pitfall 1.
    """
    env, _ = with_a_local_store(OAUTH_ENV, tmp_path, monkeypatch)
    subject = a_connected_account(tmp_path)

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
        before = bearer_call(client, CONNECTED_TOKEN)
        paused = client.post(
            ui_connections.CONNECTIONS_PATH,
            data=switch_form(subject, ui_connections.ACTION_PAUSE),
            headers=appapi_headers(user="alice"),
        )
        refused = bearer_call(client, CONNECTED_TOKEN)
        resumed = client.post(
            ui_connections.CONNECTIONS_PATH,
            data=switch_form(subject, ui_connections.ACTION_RESUME),
            headers=appapi_headers(user="alice"),
        )
        after = bearer_call(client, CONNECTED_TOKEN)

    assert before.status_code == 200, "the connection works before anything is switched"
    assert paused.status_code == 200
    assert strings.CONNECTIONS_PAUSED_TITLE in paused.text, "the page shows what it just did"
    assert refused.status_code == 403
    assert json.loads(refused.text) == {
        "error": "access_disabled",
        "error_description": strings.ACCESS_DISABLED_DESCRIPTION,
    }
    assert "www-authenticate" not in {key.lower() for key in refused.headers}
    assert refused.headers["cache-control"] == "no-store"
    assert resumed.status_code == 200
    assert strings.CONNECTIONS_PAUSED_TITLE not in resumed.text
    assert after.status_code == 200, "turning it back on needs no new sign in (D-46)"


def test_the_switch_of_one_account_leaves_the_other_accounts_serving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The negative probe of the same chain: a pause is one account's decision, not a mode."""
    env, _ = with_a_local_store(OAUTH_ENV, tmp_path, monkeypatch)
    subject = a_connected_account(tmp_path)

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
        client.post(
            ui_connections.CONNECTIONS_PATH,
            data=switch_form(subject, ui_connections.ACTION_PAUSE),
            headers=appapi_headers(user="alice"),
        )
        other = client.post(
            "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, **appapi_headers(user="bob")}
        )

    assert other.status_code == 200


def test_the_page_of_this_deployment_is_wired_to_the_store_of_this_deployment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One store, one truth: the page lists the connection the token verifier knows about."""
    env, _ = with_a_local_store(OAUTH_ENV, tmp_path, monkeypatch)
    a_connected_account(tmp_path)

    with TestClient(entry_exapp.build_exapp_app(env)) as client:
        listed = client.get(ui_connections.CONNECTIONS_PATH, headers=appapi_headers(user="alice"))

    assert listed.status_code == 200
    assert "Claude" in listed.text
    assert ui_connections.CONNECTIONS_PATH in paths(entry_exapp.build_exapp_app(env))
