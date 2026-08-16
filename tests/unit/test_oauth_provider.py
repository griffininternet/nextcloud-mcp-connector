"""The provider half of the authorization server: who may register, and who may come back.

The SDK owns the HTTP shape of ``/authorize``, ``/token``, ``/register`` and ``/revoke``;
what it deliberately does not own is the policy behind them. These checks cover the two
places this plan fills: ``register_client``, which is the door, and ``get_client``, which
is the enforcement point every later request passes through (pitfall 9, T-03-40).

Threats covered here: T-03-40 (a blocked client that keeps working), T-03-41 (an open
redirect through a registered address), T-03-44 (a registry that grows without a bound),
T-03-45 (a registration answer in a proxy cache) and T-03-47 (an error that tells the
caller which check fired).

Nothing here starts a container or opens a socket: the store is a SQLite file in
``tmp_path`` and no Nextcloud is called at all.
"""

import json
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    IdentityAssertionParams,
    RefreshToken,
    RegistrationError,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config, entry_http
from mcp_connector.entry_exapp import build_exapp_app
from mcp_connector.oauth import metadata, registry
from mcp_connector.oauth import provider as provider_module
from mcp_connector.oauth.store import IDLE_CLIENT_TTL, UNUSED_CLIENT_TTL, OAuthStore, token_hash

PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
BASE_URL = "http://nc.test"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"
CLIENT_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000001"
SECRET = "0123456789abcdef0123456789abcdef"

#: A key that is not secret, because it never leaves this file.
KEY = bytes(range(32))

ENV = {
    config.ENV_PUBLIC_URL: PUBLIC_URL,
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: "app-secret-test",
    config.ENV_APP_VERSION: "0.1.0",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
}

AS_PATHS = ("/authorize", "/token", "/register", "/revoke")


def opener(subject: OAuthStore) -> Callable[[], Awaitable[OAuthStore]]:
    async def open_it() -> OAuthStore:
        return subject

    return open_it


def build(tmp_path: Path, **env: str) -> tuple[provider_module.NextcloudOAuthProvider, OAuthStore]:
    """A provider on a real store file, with the policy of the given environment."""
    subject = OAuthStore(tmp_path / "oauth.sqlite3", KEY)
    policy = registry.client_policy(ENV | env)
    return (
        provider_module.NextcloudOAuthProvider(
            env=ENV | env, policy=policy, store_provider=opener(subject)
        ),
        subject,
    )


def registration(
    client_id: str = CLIENT_ID,
    *,
    redirect_uris: list[str] | None = None,
    secret: str | None = None,
) -> OAuthClientInformationFull:
    """What the SDK hands the provider after it validated and minted a registration."""
    return OAuthClientInformationFull.model_validate(
        {
            "client_id": client_id,
            "client_secret": secret,
            "client_name": "Claude",
            "redirect_uris": redirect_uris or [REDIRECT],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none" if secret is None else "client_secret_post",
            "scope": metadata.TOOL_SCOPE,
        }
    )


# --- register_client ---------------------------------------------------------------------


@pytest.mark.anyio
async def test_a_registration_is_stored_while_dynamic_registration_is_on(tmp_path: Path) -> None:
    subject, store = build(tmp_path)

    await subject.register_client(registration())

    row = await store.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is True
    assert json.loads(row.metadata_json)["client_name"] == "Claude"


@pytest.mark.anyio
async def test_a_registration_is_refused_with_its_reason_while_the_switch_is_off(
    tmp_path: Path,
) -> None:
    """D-40: with the switch off the registration fails with a message that names why."""
    subject, store = build(tmp_path, **{registry.ENV_DCR: "off"})

    with pytest.raises(RegistrationError) as raised:
        await subject.register_client(registration())

    assert raised.value.error == "invalid_client_metadata"
    assert "registration" in (raised.value.error_description or "").lower()
    assert await store.load_client(CLIENT_ID) is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "uri",
    ["http://claude.ai/callback", "http://192.168.1.10/cb", "myapp://cb", "https://a@b.example/cb"],
)
async def test_a_redirect_address_that_is_not_https_or_loopback_is_refused(
    tmp_path: Path, uri: str
) -> None:
    """T-03-41: the SDK matches the address exactly, but accepts any address at all."""
    subject, store = build(tmp_path)

    with pytest.raises(RegistrationError) as raised:
        await subject.register_client(registration(redirect_uris=[REDIRECT, uri]))

    assert raised.value.error == "invalid_redirect_uri"
    assert await store.load_client(CLIENT_ID) is None


@pytest.mark.anyio
async def test_a_loopback_address_stays_registrable(tmp_path: Path) -> None:
    subject, store = build(tmp_path)

    await subject.register_client(registration(redirect_uris=["http://127.0.0.1:41234/cb"]))

    assert await store.load_client(CLIENT_ID) is not None


@pytest.mark.anyio
async def test_in_the_allowlist_mode_an_unlisted_client_is_stored_as_not_allowed(
    tmp_path: Path,
) -> None:
    subject, store = build(tmp_path, **{registry.ENV_ALLOWLIST_ONLY: "1"})

    await subject.register_client(registration())

    row = await store.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is False


@pytest.mark.anyio
async def test_in_the_allowlist_mode_a_listed_return_address_is_stored_as_allowed(
    tmp_path: Path,
) -> None:
    """The only spelling an administrator can write down before a client ever registers."""
    subject, store = build(
        tmp_path, **{registry.ENV_ALLOWLIST_ONLY: "1", registry.ENV_ALLOWED_CLIENTS: REDIRECT}
    )

    await subject.register_client(registration())

    row = await store.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is True


@pytest.mark.anyio
async def test_the_client_secret_is_stored_as_a_hash_and_never_as_itself(
    tmp_path: Path,
) -> None:
    """T-03-11: the same rule the tokens follow. A stolen file must not authenticate."""
    subject, store = build(tmp_path)

    await subject.register_client(registration(secret=SECRET))

    row = await store.load_client(CLIENT_ID)
    assert row is not None
    assert row.client_secret_hash == token_hash(SECRET)
    assert SECRET not in row.metadata_json
    assert SECRET not in (tmp_path / "oauth.sqlite3").read_bytes().decode("latin-1")


# --- get_client, the enforcement point ---------------------------------------------------


@pytest.mark.anyio
async def test_a_registered_client_comes_back_as_the_sdk_model(tmp_path: Path) -> None:
    subject, _ = build(tmp_path)
    await subject.register_client(registration())

    client = await subject.get_client(CLIENT_ID)

    assert client is not None
    assert client.client_id == CLIENT_ID
    assert [str(uri) for uri in client.redirect_uris or []] == [REDIRECT]


@pytest.mark.anyio
async def test_unknown_blocked_unlisted_and_expired_are_one_answer(tmp_path: Path) -> None:
    """T-03-47: an answer that separates the four is an information service (pitfall 9)."""
    subject, store = build(tmp_path)
    await subject.register_client(registration("blocked-client"))
    await store.save_client(
        "blocked-client", metadata_json='{"client_id": "blocked-client"}', allowed=False
    )
    await store.save_client(
        "stale-client",
        metadata_json='{"client_id": "stale-client"}',
        now=int(time.time()) - UNUSED_CLIENT_TTL - 60,
    )
    listed, _unused = build(tmp_path, **{registry.ENV_ALLOWLIST_ONLY: "1"})
    await store.save_client("live-client", metadata_json='{"client_id": "live-client"}')

    assert await subject.get_client("never-registered") is None
    assert await subject.get_client("blocked-client") is None
    assert await subject.get_client("stale-client") is None
    assert await listed.get_client("live-client") is None


@pytest.mark.anyio
async def test_a_registration_nobody_used_is_removed_when_it_is_looked_up(
    tmp_path: Path,
) -> None:
    """T-03-44: the registry is swept where it is read, because this project has no cron."""
    subject, store = build(tmp_path)
    await store.save_client(
        CLIENT_ID,
        metadata_json='{"client_id": "x"}',
        now=int(time.time()) - UNUSED_CLIENT_TTL - 60,
    )

    assert await subject.get_client(CLIENT_ID) is None
    assert await store.load_client(CLIENT_ID) is None


@pytest.mark.anyio
async def test_a_client_that_was_used_and_then_forgotten_expires_later(tmp_path: Path) -> None:
    """A used registration lives on the longer window and takes its rows with it."""
    subject, store = build(tmp_path)
    moment = int(time.time())
    await store.save_client(CLIENT_ID, metadata_json='{"client_id": "x"}', now=moment - 10)
    await store.touch_client(CLIENT_ID, now=moment - IDLE_CLIENT_TTL - 60)

    assert await subject.get_client(CLIENT_ID) is None
    assert await store.load_client(CLIENT_ID) is None


@pytest.mark.anyio
async def test_a_stored_row_that_cannot_be_read_is_refused_and_not_raised(
    tmp_path: Path,
) -> None:
    """Fail closed (D-37): a row this code cannot parse is not a client, and not a 500."""
    subject, store = build(tmp_path)
    await store.save_client(CLIENT_ID, metadata_json="not json at all")

    assert await subject.get_client(CLIENT_ID) is None


# --- the methods the later plans fill ----------------------------------------------------


@pytest.mark.anyio
async def test_every_token_path_refuses_until_the_plan_that_builds_it(tmp_path: Path) -> None:
    """Fail closed: an unimplemented half of a protocol must refuse, never pass."""
    subject, _ = build(tmp_path)
    client = registration()

    assert await subject.load_authorization_code(client, "any-code") is None
    assert await subject.load_refresh_token(client, "any-token") is None
    assert await subject.load_access_token("any-token") is None
    assert await subject.revoke_token(_access_token()) is None

    with pytest.raises(TokenError):
        await subject.exchange_authorization_code(client, _authorization_code())
    with pytest.raises(TokenError):
        await subject.exchange_refresh_token(client, _refresh_token(), [])
    with pytest.raises(TokenError) as raised:
        await subject.exchange_identity_assertion(client, _identity_assertion())

    assert raised.value.error == "unsupported_grant_type"


# --- the routes --------------------------------------------------------------------------


def routes(**env: str) -> list[str]:
    policy = registry.client_policy(ENV | env)
    subject = provider_module.NextcloudOAuthProvider(env=ENV | env, policy=policy)
    return [route.path for route in provider_module.auth_routes(ENV | env, provider=subject)]


def test_the_authorization_server_routes_are_the_three_the_sdk_serves() -> None:
    """``/authorize`` is the fourth endpoint and is served by ``oauth/consent.py``: a
    refused authorization request has to end on a page a person can read, not in the JSON
    the SDK answers a machine with (plan 03-05, task 3)."""
    assert sorted(routes()) == ["/register", "/revoke", "/token"]


def test_the_application_serves_the_four_endpoints_exactly_once_each() -> None:
    """Set equality over the deployed application, which is where the two factories meet."""
    paths = [getattr(route, "path", "") for route in _exapp_routes()]

    for path in AS_PATHS:
        assert paths.count(path) == 1, path


def test_without_dynamic_registration_the_register_route_does_not_exist() -> None:
    """D-40: the switch removes the endpoint, it does not leave one that always refuses."""
    assert "/register" not in routes(**{registry.ENV_DCR: "off"})


def test_the_authorization_server_document_follows_the_switch() -> None:
    """A registration endpoint in the document that no route answers is a broken client."""
    on = metadata_document(dcr_enabled=True)
    off = metadata_document(dcr_enabled=False)

    assert on["registration_endpoint"] == f"{PUBLIC_URL}/register"
    assert "registration_endpoint" not in off


def metadata_document(*, dcr_enabled: bool) -> dict[str, object]:
    app = Starlette(routes=metadata.metadata_routes(ENV, dcr_enabled=dcr_enabled))
    with TestClient(app) as http:
        return http.get(metadata.OPENID_CONFIGURATION_SUFFIX).json()


def test_the_document_route_is_served_once_and_by_us() -> None:
    """The SDK registers a document of its own at the same path, with a cache header."""
    paths = [
        path
        for path in (getattr(route, "path", "") for route in _exapp_routes())
        if path.endswith(metadata.AS_METADATA_SUFFIX)
    ]

    assert paths == [metadata.AS_METADATA_SUFFIX]


def test_the_registration_answer_carries_no_store(tmp_path: Path) -> None:
    """T-03-45: the PHP proxy caches a 201 without a cache header for an hour."""
    with client(tmp_path) as http:
        response = http.post(
            "/register",
            json={
                "redirect_uris": [REDIRECT],
                "client_name": "Claude",
                "token_endpoint_auth_method": "none",
            },
        )

    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"


def test_with_the_switch_off_a_registration_reaches_no_route_at_all(tmp_path: Path) -> None:
    with client(tmp_path, **{registry.ENV_DCR: "off"}) as http:
        response = http.post(
            "/register",
            json={"redirect_uris": [REDIRECT], "token_endpoint_auth_method": "none"},
        )

    assert response.status_code == 404, "the route does not exist while the switch is off"


def test_a_forbidden_return_address_is_refused_over_http(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = http.post(
            "/register",
            json={
                "redirect_uris": ["http://claude.ai/cb"],
                "token_endpoint_auth_method": "none",
            },
        )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_redirect_uri"
    assert response.headers["cache-control"] == "no-store"


def client(tmp_path: Path, **env: str) -> TestClient:
    subject = OAuthStore(tmp_path / "oauth.sqlite3", KEY)
    policy = registry.client_policy(ENV | env)
    instance = provider_module.NextcloudOAuthProvider(
        env=ENV | env, policy=policy, store_provider=opener(subject)
    )
    return TestClient(Starlette(routes=provider_module.auth_routes(ENV | env, provider=instance)))


def test_the_exapp_application_serves_the_four_routes_and_the_standalone_one_none() -> None:
    """D-23: the modes of phase 1 must not grow an authorization server by accident."""
    exapp = {getattr(route, "path", "") for route in _exapp_routes()}
    standalone = {getattr(route, "path", "") for route in entry_http.build_app({}).router.routes}

    assert set(AS_PATHS) <= exapp
    assert not set(AS_PATHS) & standalone


def _exapp_routes() -> list[object]:
    return list(build_exapp_app(ENV).router.routes)


# --- the SDK models these checks hand in -------------------------------------------------


def _authorization_code() -> AuthorizationCode:
    return AuthorizationCode.model_validate(
        {
            "code": "any-code",
            "scopes": [metadata.TOOL_SCOPE],
            "expires_at": time.time() + 60,
            "client_id": CLIENT_ID,
            "code_challenge": "challenge",
            "redirect_uri": REDIRECT,
            "redirect_uri_provided_explicitly": True,
            "resource": f"{PUBLIC_URL}/mcp",
        }
    )


def _refresh_token() -> RefreshToken:
    return RefreshToken(token="any-token", client_id=CLIENT_ID, scopes=[metadata.TOOL_SCOPE])


def _access_token() -> AccessToken:
    return AccessToken(token="any-token", client_id=CLIENT_ID, scopes=[metadata.TOOL_SCOPE])


def _identity_assertion() -> IdentityAssertionParams:
    return IdentityAssertionParams(assertion="not.a.jwt")
