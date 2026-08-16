"""The way from an authorization request to the Nextcloud sign in and back to a decision.

This is the surface where a person, not a program, decides something: they see who is
asking, they sign in on Nextcloud's own pages, and they come back to a screen that names
the app, its return address and what it would be allowed to do.

Threats covered here: T-03-40 (a blocked client that keeps authorizing), T-03-41 (a return
address that does not belong to the registration), T-03-42 (a self registered client with a
name that imitates a trusted one), T-03-46 (a token without an audience) and T-03-47 (an
error page that tells the caller which check fired).

Every Nextcloud answer comes from respx and the store is a SQLite file in ``tmp_path``: no
container, no network, no Nextcloud.
"""

import asyncio
import base64
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
import respx
from mcp.shared.auth import OAuthClientInformationFull
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config
from mcp_connector.entry_exapp import build_exapp_app
from mcp_connector.exapp.ui import consent as ui_consent
from mcp_connector.exapp.ui import strings
from mcp_connector.oauth import consent, loginflow, registry
from mcp_connector.oauth import provider as provider_module
from mcp_connector.oauth.store import AUTH_CODE_TTL, FLOW_TTL, OAuthStore, token_hash

BASE_URL = "http://nc.test"
PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
HOST = "cloud.example.com"
PREFIX = "/exapps/mcp_connector"
RESOURCE = f"{PUBLIC_URL}/mcp"

CLIENT_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000001"
CLIENT_NAME = "Claude"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"
CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
STATE = "state-of-the-client"

LOGIN_URL = "https://cloud.example.com/index.php/login/v2/flow/abc123"
POLL_TOKEN = "poll-token-of-this-flow"
LOGIN_NAME = "alice"
APP_PASSWORD = "aaaaa-bbbbb-ccccc-ddddd-eeeee"

#: A key that is not secret, because it never leaves this file.
KEY = bytes(range(32))

ENV = {
    config.ENV_PUBLIC_URL: PUBLIC_URL,
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: "app-secret-test",
    config.ENV_APP_VERSION: "0.1.0",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
}

INIT_URL = f"{BASE_URL}{loginflow.INIT_PATH}"
POLL_URL = f"{BASE_URL}{loginflow.POLL_PATH}"
REVOKE_URL = f"{BASE_URL}{loginflow.APP_PASSWORD_PATH}"


def start_body() -> dict[str, object]:
    return {"poll": {"token": POLL_TOKEN, "endpoint": f"{BASE_URL}/x"}, "login": LOGIN_URL}


def poll_body() -> dict[str, str]:
    return {"server": BASE_URL, "loginName": LOGIN_NAME, "appPassword": APP_PASSWORD}


@pytest.fixture
def store(tmp_path: Path) -> OAuthStore:
    return OAuthStore(tmp_path / "oauth.sqlite3", KEY)


def make(store: OAuthStore, **env: str) -> provider_module.NextcloudOAuthProvider:
    async def provide() -> OAuthStore:
        return store

    return provider_module.NextcloudOAuthProvider(
        env=ENV | env, policy=registry.client_policy(ENV | env), store_provider=provide
    )


def application(provider: provider_module.NextcloudOAuthProvider, **env: str) -> Starlette:
    return Starlette(
        routes=[
            *provider_module.auth_routes(ENV | env, provider=provider),
            *consent.consent_routes(ENV | env, provider=provider),
        ]
    )


def register(provider: provider_module.NextcloudOAuthProvider, **fields: object) -> None:
    payload: dict[str, object] = {
        "client_id": CLIENT_ID,
        "client_name": CLIENT_NAME,
        "redirect_uris": [REDIRECT],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": "nextcloud",
    }
    payload.update(fields)
    asyncio.run(provider.register_client(OAuthClientInformationFull.model_validate(payload)))


def authorize_query(**overrides: str) -> dict[str, str]:
    query = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "code_challenge": CHALLENGE,
        "code_challenge_method": "S256",
        "redirect_uri": REDIRECT,
        "state": STATE,
        "scope": "nextcloud",
        "resource": RESOURCE,
    }
    query.update(overrides)
    return {key: value for key, value in query.items() if value}


def start(client: TestClient, **overrides: str) -> Any:
    """The authorization request itself, without following the redirect.

    The return type stays loose on purpose: the test client of Starlette answers with the
    response model of the httpx fork the SDK brings, which is a different class than the
    one this project imports (docs/dependency-audit.md).
    """
    return client.get("/authorize", params=authorize_query(**overrides), follow_redirects=False)


def flow_of(response: Any) -> str:
    location = response.headers["location"]
    match = re.search(r"flow=([A-Za-z0-9_-]+)", location)
    assert match is not None, location
    return match.group(1)


def consent_url(flow_id: str, *, step: str = "") -> str:
    query = f"{ui_consent.FLOW_PARAM}={flow_id}"
    if step:
        query += f"&{ui_consent.STEP_PARAM}={step}"
    return f"{ui_consent.CONSENT_PATH}?{query}"


# --- the authorization request -----------------------------------------------------------


def test_the_request_opens_a_flow_and_sends_the_browser_to_our_own_page(
    store: OAuthStore,
) -> None:
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))

    with respx.mock:
        init = respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        response = start(client)

    assert response.status_code == 302
    assert init.call_count == 1
    location = response.headers["location"]
    assert location.startswith(f"{PUBLIC_URL}{ui_consent.CONSENT_PATH}?")
    assert response.headers["cache-control"] == "no-store"


def test_the_flow_carries_every_field_of_the_request_and_twenty_minutes(
    store: OAuthStore,
) -> None:
    """Everything plan 03-06 needs to build a code out of it, and nothing more."""
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))

    with respx.mock:
        respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        response = start(client)

    row = asyncio.run(store.load_flow(flow_of(response)))
    assert row is not None
    assert row.client_id == CLIENT_ID
    assert row.redirect_uri == REDIRECT
    assert row.redirect_uri_explicit is True
    assert row.code_challenge == CHALLENGE
    assert row.state == STATE
    assert row.scopes == "nextcloud"
    assert row.resource == RESOURCE
    assert row.poll_token == POLL_TOKEN
    assert 0 < row.expires_at - int(time.time()) <= FLOW_TTL


def test_the_client_name_reaches_nextcloud_cleaned_and_prefixed(store: OAuthStore) -> None:
    """T-03-43: the name is attacker input and becomes a header at Nextcloud (pitfall 8)."""
    provider = make(store)
    register(provider, client_name="Evil\r\nX-Injected: 1")
    client = TestClient(application(provider))

    with respx.mock:
        init = respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        start(client)

    agent = init.calls[0].request.headers["user-agent"]
    assert agent.startswith(loginflow.AGENT_PREFIX)
    assert "\r" not in agent
    assert "\n" not in agent


def test_a_request_without_the_resource_parameter_is_refused(store: OAuthStore) -> None:
    """T-03-46: a token without an audience would be valid at every other MCP server."""
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))

    with respx.mock:
        init = respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        response = start(client, resource="")

    assert init.call_count == 0, "no sign in is opened for a request that cannot be granted"
    assert response.status_code == 302
    assert "error=invalid_target" in response.headers["location"]


def test_a_request_for_another_resource_is_refused(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))

    with respx.mock:
        respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        response = start(client, resource="https://other.example.com/mcp")

    assert "error=invalid_target" in response.headers["location"]


def test_a_return_address_that_is_not_registered_never_becomes_a_redirect(
    store: OAuthStore,
) -> None:
    """T-03-41: the answer is a page, and above all it is not a redirect anywhere."""
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))

    response = start(client, redirect_uri="https://attacker.example/callback")

    assert response.status_code == 400
    assert "location" not in response.headers
    assert strings.ERROR_REDIRECT_TITLE in response.text


def test_a_client_that_is_not_on_the_allowlist_reaches_the_administrator_page(
    store: OAuthStore,
) -> None:
    provider = make(store, **{registry.ENV_ALLOWLIST_ONLY: "1"})
    register(provider)
    client = TestClient(application(provider, **{registry.ENV_ALLOWLIST_ONLY: "1"}))

    response = start(client)

    assert response.status_code == 403
    assert strings.ERROR_ALLOWLIST_TITLE in response.text


def test_an_unknown_client_with_registration_switched_off_reads_the_reason(
    store: OAuthStore,
) -> None:
    provider = make(store, **{registry.ENV_DCR: "off"})
    client = TestClient(application(provider, **{registry.ENV_DCR: "off"}))

    response = start(client)

    assert response.status_code == 400
    assert strings.ERROR_REGISTRATION_OFF_TITLE in response.text


def test_an_unknown_client_while_registration_is_open_is_sent_back_to_its_app(
    store: OAuthStore,
) -> None:
    """T-03-47: the same answer an expired registration gets, and no other information."""
    provider = make(store)
    client = TestClient(application(provider))

    response = start(client)

    assert response.status_code == 400
    assert strings.ERROR_EXPIRED_TITLE in response.text


def test_the_bare_address_is_the_empty_state_and_not_a_protocol_error(
    store: OAuthStore,
) -> None:
    """Where "Start over" of the timeout page leads, so it has to read as a sentence."""
    provider = make(store)
    client = TestClient(application(provider))

    response = client.get("/authorize")

    assert response.status_code == 400
    assert strings.EMPTY_TITLE in response.text
    assert strings.EMPTY_BODY in response.text


# --- the consent surface ------------------------------------------------------------------


def opened(
    provider: provider_module.NextcloudOAuthProvider,
) -> tuple[TestClient, str, str]:
    """Run one authorization request and return what the browser would follow.

    The third value is the address of the redirect with the public prefix removed, which
    is exactly the path this application sees behind HaRP.
    """
    client = TestClient(application(provider))
    with respx.mock:
        respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        response = start(client)
    target = response.headers["location"].removeprefix(PUBLIC_URL)
    return client, flow_of(response), target


def test_the_first_page_hands_the_user_over_to_nextcloud(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client, _flow_id, target = opened(provider)

    with respx.mock:
        poll = respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        response = client.get(target)

    assert response.status_code == 200
    assert poll.call_count == 0, "the handoff page polls nothing, it only hands over"
    assert f'href="{LOGIN_URL}"' in response.text
    assert 'rel="noopener noreferrer"' in response.text
    assert strings.SIGNIN_CTA in response.text
    assert CLIENT_NAME in response.text


def test_the_waiting_page_polls_exactly_once_per_load(store: OAuthStore) -> None:
    """T-03-34: the refresh is the throttle, so one load has to be one poll."""
    provider = make(store)
    register(provider)
    client, _flow_id, target = opened(provider)

    wait_target = f"{target}&{ui_consent.STEP_PARAM}={ui_consent.STEP_WAIT}"
    with respx.mock:
        poll = respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        client.get(wait_target)
        client.get(wait_target)
        response = client.get(wait_target)

    assert poll.call_count == 3
    assert response.status_code == 200
    assert '<meta http-equiv="refresh"' in response.text
    assert strings.WAIT_STATUS.format(host=HOST) in response.text


def test_a_finished_sign_in_turns_into_the_consent_screen(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert response.status_code == 200
    assert strings.CONSENT_TITLE.format(client=CLIENT_NAME) in response.text
    assert strings.CONSENT_IDENTITY.format(user=LOGIN_NAME, host=HOST) in response.text
    assert REDIRECT in response.text
    assert CLIENT_ID in response.text
    assert strings.CONSENT_GRANT_READ in response.text


def test_the_credential_of_the_sign_in_is_stored_and_never_rendered(
    store: OAuthStore, tmp_path: Path
) -> None:
    """The app password belongs to the connection, not to the page (D-34, T-03-33)."""
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert APP_PASSWORD not in response.text
    row = asyncio.run(store.load_authorization(flow_id))
    assert row is not None
    assert row.nc_user == LOGIN_NAME
    assert row.resource == RESOURCE
    assert asyncio.run(store.app_password(flow_id)) == APP_PASSWORD
    assert APP_PASSWORD.encode() not in _store_bytes(tmp_path)


def _store_bytes(directory: Path) -> bytes:
    return b"".join(path.read_bytes() for path in sorted(directory.iterdir()) if path.is_file())


def test_a_second_load_after_the_sign_in_does_not_poll_again(store: OAuthStore) -> None:
    """The 200 of a poll arrives exactly once, so the screen has to survive a refresh."""
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)

    with respx.mock:
        poll = respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))
        second = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert poll.call_count == 1
    assert second.status_code == 200
    assert strings.CONSENT_TITLE.format(client=CLIENT_NAME) in second.text


def test_the_unverified_callout_is_there_for_a_self_registered_client(
    store: OAuthStore,
) -> None:
    """T-03-42: a name from a registration is not a name Nextcloud vouched for."""
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert strings.CONSENT_WARNING_TITLE in response.text
    assert strings.CONSENT_WARNING_BODY in response.text


def test_the_unverified_callout_is_absent_for_a_listed_client(store: OAuthStore) -> None:
    listed = {registry.ENV_ALLOWED_CLIENTS: REDIRECT}
    provider = make(store, **listed)
    register(provider)
    client = TestClient(application(provider, **listed))
    with respx.mock:
        respx.post(INIT_URL).mock(return_value=httpx.Response(200, json=start_body()))
        flow_id = flow_of(start(client))
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert strings.CONSENT_WARNING_TITLE not in response.text


def test_an_expired_flow_shows_the_timeout_page_and_stops_polling(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)
    _age_flow(store, flow_id)

    with respx.mock:
        poll = respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))
        again = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert poll.call_count == 0
    assert response.status_code == 408
    assert strings.ERROR_TIMEOUT_TITLE in response.text
    assert again.status_code == 400, "the record is gone, so the next load is the expired page"


def _age_flow(store: OAuthStore, flow_id: str) -> None:
    """Move the deadline of one flow into the past, without touching the clock."""
    conn = sqlite3.connect(store.path)
    try:
        conn.execute(
            "UPDATE flows SET expires_at = ? WHERE flow_id = ?", (int(time.time()) - 1, flow_id)
        )
        conn.commit()
    finally:
        conn.close()


def test_an_unknown_flow_is_the_expired_page(store: OAuthStore) -> None:
    provider = make(store)
    client = TestClient(application(provider))

    response = client.get(consent_url("not-a-flow-id"))

    assert response.status_code == 400
    assert strings.ERROR_EXPIRED_TITLE in response.text


def test_a_client_blocked_after_the_sign_in_does_not_reach_the_decision(
    store: OAuthStore,
) -> None:
    """T-03-40: the enforcement point is asked again on the way to the decision."""
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)
    asyncio.run(store.save_client(CLIENT_ID, metadata_json='{"client_id": "x"}', allowed=False))

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    assert response.status_code in (400, 403)
    assert strings.CONSENT_APPROVE not in response.text


# --- the decision -----------------------------------------------------------------------


def signed_in(provider: provider_module.NextcloudOAuthProvider) -> tuple[TestClient, str, str]:
    """One flow that reached the consent screen, plus the screen it rendered."""
    client, flow_id, _target = opened(provider)
    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(200, json=poll_body()))
        page = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))
    return client, flow_id, page.text


def appapi_headers(user: str) -> dict[str, str]:
    """The three headers HaRP attaches to a request on a ``USER`` route.

    These tests speak to the application directly, so they stand in for the proxy. The
    value of ``AUTHORIZATION-APP-API`` is base64 of ``<user>:<APP_SECRET>``, which is what
    HaRP builds out of the Nextcloud account it resolved and the registration secret of
    this app, and which is why no caller can write it: the secret is not theirs.
    """
    raw = f"{user}:{ENV[config.ENV_APP_SECRET]}".encode()
    return {
        "EX-APP-ID": ENV[config.ENV_APP_ID],
        "EX-APP-VERSION": ENV[config.ENV_APP_VERSION],
        "AUTHORIZATION-APP-API": base64.b64encode(raw).decode("ascii"),
    }


def decide(
    client: TestClient,
    flow_id: str,
    decision: str,
    *,
    store: OAuthStore | None = None,
    confirm: str | None = None,
    user: str | None = LOGIN_NAME,
) -> Any:
    """One press of one of the two buttons, exactly as the rendered form sends it.

    ``user`` is the Nextcloud account HaRP resolved for the browser that presses it, and
    ``None`` is the anonymous request: no headers at all, which is what an attacker without
    a Nextcloud session can send (CR-01).
    """
    token = confirm if confirm is not None else (store.form_token(flow_id) if store else "")
    return client.post(
        ui_consent.DECIDE_PATH,
        data={
            ui_consent.FLOW_PARAM: flow_id,
            ui_consent.DECISION_PARAM: decision,
            ui_consent.CONFIRM_PARAM: token,
        },
        headers=appapi_headers(user) if user is not None else {},
        follow_redirects=False,
    )


def rows(store: OAuthStore, table: str) -> list[tuple[Any, ...]]:
    """Every row of one table, read straight out of the file the store writes."""
    conn = sqlite3.connect(store.path)
    try:
        return conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()  # noqa: S608
    finally:
        conn.close()


def _columns(store: OAuthStore, table: str) -> list[str]:
    """The column names of one table, so a test reads a row by name and not by position."""
    conn = sqlite3.connect(store.path)
    try:
        return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")]
    finally:
        conn.close()


def snapshot(store: OAuthStore) -> dict[str, list[tuple[Any, ...]]]:
    """The three tables a decision may touch, so a test can prove none of them moved."""
    return {name: rows(store, name) for name in ("flows", "authorizations", "auth_codes")}


def query_of(response: Any) -> dict[str, list[str]]:
    return parse_qs(urlsplit(response.headers["location"]).query)


def test_an_approval_redirects_with_code_state_and_iss(store: OAuthStore) -> None:
    """The one moment of this phase that grants something, and the shape RFC 9207 wants."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    response = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)

    assert response.status_code == 302
    assert response.headers["location"].startswith(REDIRECT)
    assert response.headers["cache-control"] == "no-store"
    query = query_of(response)
    assert query["state"] == [STATE]
    assert query["iss"] == [PUBLIC_URL], "the issuer is the configured public URL (RFC 9207)"
    assert len(query["code"]) == 1
    assert len(rows(store, "authorizations")) == 1, "exactly one authorization, not a second"
    assert asyncio.run(store.load_flow(flow_id, now=0)) is None, "the flow is spent"


def test_the_code_lives_sixty_seconds_and_is_redeemable_exactly_once(
    store: OAuthStore,
) -> None:
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    response = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)
    code = query_of(response)["code"][0]

    stored = rows(store, "auth_codes")
    assert len(stored) == 1
    assert stored[0][0] == token_hash(code), "the code stands in the file as its digest only"
    assert code not in _store_bytes(store.path.parent).decode("utf-8", "ignore")
    first = asyncio.run(store.redeem_auth_code(code))
    second = asyncio.run(store.redeem_auth_code(code))
    assert first is not None
    assert second is None
    assert first.auth_id == flow_id
    assert first.code_challenge == CHALLENGE
    assert first.redirect_uri == REDIRECT
    assert first.resource == RESOURCE
    expires_at = dict(zip(_columns(store, "auth_codes"), stored[0], strict=True))["expires_at"]
    assert 0 < expires_at - int(time.time()) <= AUTH_CODE_TTL


def test_a_get_never_grants_anything_whatever_it_carries(store: OAuthStore) -> None:
    """T-03-50: a state change is a POST, so a GET with a decision in it changes nothing."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)
    before = snapshot(store)

    response = client.get(
        f"{consent_url(flow_id)}&{ui_consent.DECISION_PARAM}={ui_consent.DECISION_APPROVE}"
        f"&{ui_consent.CONFIRM_PARAM}={store.form_token(flow_id)}",
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "location" not in response.headers
    assert snapshot(store) == before, "not one row of the store moved"


def test_a_denial_answers_access_denied_and_hands_the_credential_back(
    store: OAuthStore,
) -> None:
    """A refused connection must not leave a usable Nextcloud credential behind (D-34)."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    with respx.mock:
        revoke = respx.delete(REVOKE_URL).mock(return_value=httpx.Response(200, json={}))
        response = decide(client, flow_id, ui_consent.DECISION_DENY, store=store)

    assert response.status_code == 302
    assert revoke.call_count == 1, "one attempt, no retry"
    query = query_of(response)
    assert query["error"] == ["access_denied"]
    assert query["state"] == [STATE]
    assert query["iss"] == [PUBLIC_URL]
    assert "code" not in query
    assert rows(store, "authorizations") == [], "no authorization survives a denial"
    assert rows(store, "auth_codes") == []
    assert asyncio.run(store.load_flow(flow_id, now=0)) is None


@pytest.mark.parametrize("confirm", ["", "not-the-token", "0" * 64])
def test_a_decision_without_the_anti_forgery_token_changes_nothing(
    store: OAuthStore, confirm: str
) -> None:
    """T-03-50: the value is bound to this flow and to this deployment, and nothing else."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)
    before = snapshot(store)

    response = decide(client, flow_id, ui_consent.DECISION_APPROVE, confirm=confirm)

    assert response.status_code == 400
    assert "location" not in response.headers
    assert snapshot(store) == before


def test_a_second_decision_on_the_same_flow_creates_nothing_more(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    first = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)
    second = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)

    assert first.status_code == 302
    assert second.status_code == 400
    assert len(rows(store, "auth_codes")) == 1
    assert len(rows(store, "authorizations")) == 1


# --- CR-01: the decision belongs to the account that signed in ----------------------------


@pytest.mark.parametrize(
    ("user", "case"),
    [(None, "no Nextcloud session at all"), ("mallory", "a different Nextcloud account")],
)
def test_the_relay_attack_never_reaches_a_code(
    store: OAuthStore, user: str | None, case: str
) -> None:
    """CR-01, the whole attack in one test.

    The attacker registers a client, starts the authorization and gets the flow id, which
    until this fix was the entire authorisation of the decision. They send the victim
    nothing but Nextcloud's own sign in link, the victim grants it, and the attacker
    presses "Allow access" with the flow id and the anti forgery value of that flow, both
    of which they hold. Every check before this one passes: the flow exists, it has not
    expired, the value fits the form, the client is allowed and the sign in is finished.
    Only the account behind the browser is somebody else's, and that is what has to end it.
    """
    provider = make(store)
    register(provider)
    client, flow_id, page = signed_in(provider)
    assert strings.CONSENT_APPROVE in page, "the sign in of the victim finished"
    before = snapshot(store)

    response = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store, user=user)

    assert response.status_code == 400, case
    assert "location" not in response.headers, "no code and no redirect to the client"
    assert rows(store, "auth_codes") == []
    assert snapshot(store) == before, "not one row of the store moved"
    assert strings.CONSENT_APPROVE not in response.text


def test_a_forged_identity_header_is_not_an_identity(store: OAuthStore) -> None:
    """The header is signed with APP_SECRET, which the caller does not have (T-02-02)."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)
    forged = base64.b64encode(f"{LOGIN_NAME}:not-the-app-secret".encode()).decode("ascii")

    response = client.post(
        ui_consent.DECIDE_PATH,
        data={
            ui_consent.FLOW_PARAM: flow_id,
            ui_consent.DECISION_PARAM: ui_consent.DECISION_APPROVE,
            ui_consent.CONFIRM_PARAM: store.form_token(flow_id),
        },
        headers={
            "EX-APP-ID": ENV[config.ENV_APP_ID],
            "EX-APP-VERSION": ENV[config.ENV_APP_VERSION],
            "AUTHORIZATION-APP-API": forged,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert rows(store, "auth_codes") == []


def test_a_denial_by_a_stranger_leaves_the_connection_alone(store: OAuthStore) -> None:
    """The refusal is the whole decision, not only the granting half of it: a stranger who
    could deny would end a connection somebody else is making and hand back their
    credential, which is the same authority in the other direction."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    with respx.mock:
        revoke = respx.delete(REVOKE_URL).mock(return_value=httpx.Response(200, json={}))
        response = decide(client, flow_id, ui_consent.DECISION_DENY, store=store, user="mallory")

    assert response.status_code == 400
    assert revoke.call_count == 0, "no app password of another account is handed back"
    assert len(rows(store, "authorizations")) == 1, "the connection of the victim is untouched"


def test_the_decision_is_a_route_of_its_own_and_the_screen_stays_public() -> None:
    """CR-01: the split is what makes one access level possible per half of the surface."""
    paths = [getattr(route, "path", "") for route in build_exapp_app(ENV).router.routes]

    assert paths.count(ui_consent.CONSENT_PATH) == 1
    assert paths.count(ui_consent.DECIDE_PATH) == 1

    served = {
        getattr(route, "path", ""): sorted(getattr(route, "methods", set()) or set())
        for route in build_exapp_app(ENV).router.routes
    }
    assert served[ui_consent.CONSENT_PATH] == ["GET", "HEAD"]
    assert served[ui_consent.DECIDE_PATH] == ["POST"]


def test_the_form_of_the_consent_screen_posts_to_the_decision_route(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    _client, _flow_id, page = signed_in(provider)

    assert f'action="{PREFIX}{ui_consent.DECIDE_PATH}"' in page


def test_the_form_is_a_post_with_two_named_buttons_and_deny_first(store: OAuthStore) -> None:
    """03-UI-SPEC.md S3: no GET grants anything, and the safe action is reachable first."""
    provider = make(store)
    register(provider)
    _client, flow_id, page = signed_in(provider)

    assert 'method="post"' in page
    assert f'name="{ui_consent.DECISION_PARAM}" value="{ui_consent.DECISION_DENY}"' in page
    assert f'name="{ui_consent.DECISION_PARAM}" value="{ui_consent.DECISION_APPROVE}"' in page
    assert page.index(strings.CONSENT_DENY) < page.index(strings.CONSENT_APPROVE)
    assert f'name="{ui_consent.CONFIRM_PARAM}" value="{store.form_token(flow_id)}"' in page, (
        "the form carries the value that binds it to this authorization request"
    )
    assert "<script" not in page


def test_the_page_lands_on_its_heading_and_not_on_the_granting_button(
    store: OAuthStore,
) -> None:
    """A page that opens with the granting action focused turns a stray Enter into a grant."""
    provider = make(store)
    register(provider)
    _client, _flow_id, page = signed_in(provider)

    heading = re.search(r"<h1[^>]*>", page)
    assert heading is not None
    assert 'tabindex="-1"' in heading.group(0)
    assert "autofocus" in heading.group(0)
    assert "autofocus" not in page[page.index("<button") :]


def out_of_band(store: OAuthStore, flow_id: str) -> None:
    """A finished sign in of a client this server cannot redirect anywhere (S4)."""
    asyncio.run(
        store.create_flow(
            flow_id,
            client_id=CLIENT_ID,
            redirect_uri="",
            redirect_uri_explicit=False,
            code_challenge=CHALLENGE,
            state=None,
            scopes="nextcloud",
            resource=RESOURCE,
            poll_token=POLL_TOKEN,
        )
    )
    asyncio.run(
        store.create_authorization(
            flow_id,
            client_id=CLIENT_ID,
            nc_user=LOGIN_NAME,
            app_password=APP_PASSWORD,
            scopes="nextcloud",
            resource=RESOURCE,
        )
    )


def test_without_a_return_address_the_result_is_a_page(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))
    out_of_band(store, "flow-approved-out-of-band")

    response = decide(client, "flow-approved-out-of-band", ui_consent.DECISION_APPROVE, store=store)

    assert response.status_code == 200
    assert "location" not in response.headers
    assert strings.RESULT_CONNECTED_TITLE in response.text
    assert (
        strings.RESULT_CONNECTED_BODY.format(client=CLIENT_NAME, user=LOGIN_NAME) in response.text
    )
    assert APP_PASSWORD not in response.text


def test_without_a_return_address_a_denial_is_a_page_too(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client = TestClient(application(provider))
    out_of_band(store, "flow-denied-out-of-band")

    with respx.mock:
        respx.delete(REVOKE_URL).mock(return_value=httpx.Response(200, json={}))
        response = decide(client, "flow-denied-out-of-band", ui_consent.DECISION_DENY, store=store)

    assert response.status_code == 200
    assert strings.RESULT_DENIED_TITLE in response.text
    assert strings.RESULT_DENIED_BODY.format(client=CLIENT_NAME) in response.text
    assert APP_PASSWORD not in response.text
    assert rows(store, "authorizations") == []


def test_a_decision_of_a_client_blocked_in_the_meantime_grants_nothing(
    store: OAuthStore,
) -> None:
    """T-03-40, pitfall 9: the enforcement point is asked again at the moment of the grant."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)
    asyncio.run(store.save_client(CLIENT_ID, metadata_json='{"client_id": "x"}', allowed=False))

    response = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)

    assert response.status_code in (400, 403)
    assert "location" not in response.headers
    assert rows(store, "auth_codes") == []


def test_no_decision_writes_a_credential_into_the_log(
    store: OAuthStore, caplog: pytest.LogCaptureFixture
) -> None:
    """T-03-54: not on DEBUG, not truncated, not in the successful case either."""
    provider = make(store)
    register(provider)
    client, flow_id, _page = signed_in(provider)

    with caplog.at_level(logging.DEBUG):
        response = decide(client, flow_id, ui_consent.DECISION_APPROVE, store=store)

    assert APP_PASSWORD not in caplog.text
    assert POLL_TOKEN not in caplog.text
    assert query_of(response)["code"][0] not in caplog.text


# --- the properties of every page of this route -------------------------------------------


def test_no_page_of_this_route_carries_a_script(store: OAuthStore) -> None:
    provider = make(store)
    register(provider)
    client, flow_id, target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        pages = [
            client.get(target),
            client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT)),
            client.get("/authorize"),
        ]

    for page in pages:
        assert "<script" not in page.text
        assert "onclick" not in page.text
        assert page.headers["cache-control"] == "no-store"
        assert page.headers["x-frame-options"] == "DENY"
        assert page.headers["referrer-policy"] == "no-referrer"
        assert "default-src 'none'" in page.headers["content-security-policy"]


def test_every_link_of_a_page_carries_the_public_prefix(store: OAuthStore) -> None:
    """HaRP strips the prefix before this app sees a request, so a link without it would
    point at the root of the Nextcloud domain instead of at this application."""
    provider = make(store)
    register(provider)
    client, flow_id, target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        response = client.get(consent_url(flow_id, step=ui_consent.STEP_WAIT))

    for target in re.findall(r'(?:href|action)="(/[^"]*)"', response.text):
        assert target.startswith(PREFIX), target


def test_a_sign_in_link_of_a_foreign_host_is_not_rendered(store: OAuthStore) -> None:
    """The link is the one place this surface sends a user away from here (T-03-42)."""
    provider = make(store)
    register(provider)
    client, flow_id, _target = opened(provider)

    with respx.mock:
        respx.post(POLL_URL).mock(return_value=httpx.Response(404))
        response = client.get(
            f"{consent_url(flow_id)}&{ui_consent.LOGIN_PARAM}=https://evil.example/login"
        )

    assert "evil.example" not in response.text


def test_the_routes_are_declared_in_the_manifest_and_served_by_the_application() -> None:
    paths = [getattr(route, "path", "") for route in build_exapp_app(ENV).router.routes]

    assert paths.count("/authorize") == 1
    assert paths.count(ui_consent.CONSENT_PATH) == 1
    assert paths.count(ui_consent.DECIDE_PATH) == 1
