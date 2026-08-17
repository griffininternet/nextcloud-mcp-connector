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

import ast
import base64
import hashlib
import inspect
import json
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
import pytest
import respx
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    IdentityAssertionParams,
    RefreshToken,
    RegistrationError,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_connector import config, entry_http
from mcp_connector.entry_exapp import MCP_PATH, build_exapp_app
from mcp_connector.exapp.middleware import RequireAppApi
from mcp_connector.oauth import loginflow, metadata, registry
from mcp_connector.oauth import provider as provider_module
from mcp_connector.oauth import throttle as throttle_module
from mcp_connector.oauth.store import (
    ACCESS_TOKEN_TTL,
    FLOW_TTL,
    IDLE_CLIENT_TTL,
    UNUSED_CLIENT_TTL,
    OAuthStore,
    token_hash,
)
from mcp_connector.oauth.verifier import StoreTokenVerifier

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


# --- the code exchange -------------------------------------------------------------------

AUTH_ID = "the-flow-this-authorization-was-born-in"
NC_USER = "alice"
APP_PASSWORD = "aaaaa-bbbbb-ccccc-ddddd-eeeee"
CODE = "the-authorization-code-of-this-consent"
RESOURCE = f"{PUBLIC_URL}/mcp"
VERIFIER = "a-code-verifier-of-the-client-that-is-long-enough"
CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip("=")
)


async def approved(
    tmp_path: Path,
    *,
    resource: str = RESOURCE,
    secret: str | None = None,
    **env: str,
) -> tuple[provider_module.NextcloudOAuthProvider, OAuthStore]:
    """A registered client, a consent that happened and the code it produced."""
    subject, store = build(tmp_path, **env)
    await subject.register_client(registration(secret=secret))
    await store.create_authorization(
        AUTH_ID,
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=resource,
    )
    await store.create_auth_code(
        CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT,
        code_challenge=CHALLENGE,
        resource=resource,
    )
    return subject, store


@pytest.mark.anyio
async def test_a_code_is_loaded_with_everything_the_token_endpoint_compares(
    tmp_path: Path,
) -> None:
    subject, _store = await approved(tmp_path)

    loaded = await subject.load_authorization_code(registration(), CODE)

    assert loaded is not None
    assert loaded.code == CODE
    assert loaded.client_id == CLIENT_ID
    assert loaded.subject == NC_USER, "the resource owner travels into the access token"
    assert loaded.code_challenge == CHALLENGE
    assert str(loaded.redirect_uri) == REDIRECT
    assert loaded.redirect_uri_provided_explicitly is True
    assert loaded.resource == RESOURCE
    assert loaded.scopes == [metadata.TOOL_SCOPE]
    assert 0 < loaded.expires_at - time.time() <= 60


@pytest.mark.anyio
async def test_a_code_that_is_unknown_used_or_expired_is_not_loaded(tmp_path: Path) -> None:
    subject, store = await approved(tmp_path)

    assert await subject.load_authorization_code(registration(), "never-issued") is None
    await store.redeem_auth_code(CODE)
    assert await subject.load_authorization_code(registration(), CODE) is None


@pytest.mark.anyio
async def test_the_exchange_issues_an_opaque_pair_and_stores_only_their_digests(
    tmp_path: Path,
) -> None:
    subject, store = await approved(tmp_path)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None

    issued = await subject.exchange_authorization_code(registration(), code)

    assert issued.token_type == "Bearer"
    assert issued.expires_in == ACCESS_TOKEN_TTL
    assert issued.refresh_token is not None
    assert issued.access_token != issued.refresh_token
    access = await store.load_access_token(issued.access_token)
    refresh = await store.load_refresh_token(issued.refresh_token)
    assert access is not None
    assert refresh is not None
    assert access.auth_id == AUTH_ID
    assert access.nc_user == NC_USER
    assert access.resource == RESOURCE
    assert access.family_id == refresh.family_id, "one connection, one family"
    file_bytes = (tmp_path / "oauth.sqlite3").read_bytes()
    assert issued.access_token.encode() not in file_bytes
    assert issued.refresh_token.encode() not in file_bytes


@pytest.mark.anyio
async def test_the_code_is_spent_and_a_second_exchange_fails(tmp_path: Path) -> None:
    """RFC 6749 §10.5: one code, one exchange, and the second one is invalid_grant."""
    subject, _store = await approved(tmp_path)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None

    await subject.exchange_authorization_code(registration(), code)
    with pytest.raises(TokenError) as raised:
        await subject.exchange_authorization_code(registration(), code)

    assert raised.value.error == "invalid_grant"


@pytest.mark.anyio
@pytest.mark.parametrize("resource", ["", "https://other.example.com/mcp"])
async def test_a_code_without_this_audience_never_becomes_a_token(
    tmp_path: Path, resource: str
) -> None:
    """T-03-51: a token without an audience is valid at every other MCP server."""
    subject, store = await approved(tmp_path, resource=resource)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None

    with pytest.raises(TokenError) as raised:
        await subject.exchange_authorization_code(registration(), code)

    assert raised.value.error == "invalid_target"
    assert await store.load_auth_code(CODE) is not None, "a refusal does not spend the code"


@pytest.mark.anyio
async def test_a_client_blocked_between_authorize_and_token_gets_nothing(
    tmp_path: Path,
) -> None:
    """T-03-55, pitfall 9: a block in the middle of a flow must not slip through."""
    subject, store = await approved(tmp_path)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None
    await store.save_client(CLIENT_ID, metadata_json='{"client_id": "x"}', allowed=False)

    with pytest.raises(TokenError) as raised:
        await subject.exchange_authorization_code(registration(), code)

    assert raised.value.error == "invalid_client"


@pytest.mark.anyio
async def test_the_exchange_asks_nextcloud_nothing_at_all(tmp_path: Path) -> None:
    """T-03-58, pitfall 13: the token endpoint of a connector has ten seconds."""
    subject, _store = await approved(tmp_path)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None

    with respx.mock:
        await subject.exchange_authorization_code(registration(), code)
        assert len(respx.calls) == 0


@pytest.mark.anyio
async def test_the_exchange_marks_the_registration_as_used(tmp_path: Path) -> None:
    """A registration that produced a token lives on the long window, not the short one."""
    subject, store = await approved(tmp_path)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None

    await subject.exchange_authorization_code(registration(), code)

    row = await store.load_client(CLIENT_ID)
    assert row is not None
    assert row.last_used_at is not None


# --- the client authenticator of this server ----------------------------------------------


def token_request(**fields: str) -> dict[str, str]:
    payload = {
        "grant_type": "authorization_code",
        "code": CODE,
        "code_verifier": VERIFIER,
        "redirect_uri": REDIRECT,
        "client_id": CLIENT_ID,
    }
    payload.update(fields)
    return payload


def serving(
    subject: provider_module.NextcloudOAuthProvider,
    *,
    throttle: throttle_module.Throttle | None = None,
    **env: str,
) -> TestClient:
    return TestClient(
        Starlette(
            routes=provider_module.auth_routes(ENV | env, provider=subject, throttle=throttle)
        )
    )


@pytest.mark.anyio
async def test_a_public_client_walks_the_whole_token_endpoint(tmp_path: Path) -> None:
    """The end to end shape: a real code, a real PKCE verifier, a real pair of tokens."""
    subject, _store = await approved(tmp_path)

    with serving(subject) as http:
        response = http.post("/token", data=token_request())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == ACCESS_TOKEN_TTL
    assert body["refresh_token"]
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_a_confidential_client_authenticates_against_the_stored_digest(
    tmp_path: Path,
) -> None:
    """The SDK compares a plaintext secret, and this store keeps none (plan 03-05)."""
    subject, _store = await approved(tmp_path, secret=SECRET)

    with serving(subject) as http:
        good = http.post("/token", data=token_request(client_secret=SECRET))

    assert good.status_code == 200, good.text


@pytest.mark.anyio
async def test_a_wrong_client_secret_is_a_401_and_no_token(tmp_path: Path) -> None:
    subject, store = await approved(tmp_path, secret=SECRET)

    with serving(subject) as http:
        response = http.post("/token", data=token_request(client_secret="not-the-secret"))

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"
    assert await store.load_auth_code(CODE) is not None, "the code was not spent"


@pytest.mark.anyio
async def test_a_confidential_client_without_its_secret_is_refused(tmp_path: Path) -> None:
    subject, _store = await approved(tmp_path, secret=SECRET)

    with serving(subject) as http:
        response = http.post("/token", data=token_request())

    assert response.status_code == 401


@pytest.mark.anyio
async def test_a_row_that_asks_for_a_secret_and_has_none_is_refused(tmp_path: Path) -> None:
    """WR-01: the SDK authenticator refuses "registered for a secret and has none stored",
    and this override read the same state as "a public client, let it in". Any row written
    another way than through the shipped registration path would then have authenticated
    with no credential at all."""
    subject, store = await approved(tmp_path, secret=SECRET)
    row = await store.load_client(CLIENT_ID)
    assert row is not None
    await store.save_client(
        CLIENT_ID,
        metadata_json=row.metadata_json,
        allowed=True,
        secret_hash=None,
    )

    with serving(subject) as http:
        without = http.post("/token", data=token_request())
        with_one = http.post("/token", data=token_request(client_secret=SECRET))

    assert without.status_code == 401
    assert with_one.status_code == 401
    assert without.json()["error"] == "invalid_client"
    assert await store.load_auth_code(CODE) is not None, "the code was not spent"


@pytest.mark.anyio
async def test_a_client_secret_that_ran_out_stops_working(tmp_path: Path) -> None:
    """WR-01: nothing compared client_secret_expires_at against a clock, so an expired
    secret kept working. Not reachable with the shipped default (never), which is why it is
    a warning, and live the moment an administrator sets an expiry."""
    subject, store = await approved(tmp_path, secret=SECRET)
    registered = registration(secret=SECRET)
    registered.client_secret_expires_at = int(time.time()) - 1
    row = await store.load_client(CLIENT_ID)
    assert row is not None
    await store.save_client(
        CLIENT_ID,
        metadata_json=registered.model_dump_json(),
        allowed=True,
        secret_hash=row.client_secret_hash,
    )

    with serving(subject) as http:
        response = http.post("/token", data=token_request(client_secret=SECRET))

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"


@pytest.mark.anyio
async def test_a_wrong_pkce_verifier_is_refused_by_the_sdk(tmp_path: Path) -> None:
    """The checks the SDK owns stay the SDK's, and this proves they are still in the path."""
    subject, _store = await approved(tmp_path)

    with serving(subject) as http:
        response = http.post("/token", data=token_request(code_verifier="another-verifier"))

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_grant"


# --- what an empty store answers, and the one grant that refuses for good -----------------


@pytest.mark.anyio
async def test_every_token_path_refuses_what_this_server_never_issued(tmp_path: Path) -> None:
    """Fail closed: a value nothing in the store knows is never a grant and never a 500."""
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

    assert raised.value.error == "unsupported_grant_type", "and this one refuses for good"


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


# --- the revocation of a whole connection (SC 4) -------------------------------------------


async def issued(
    tmp_path: Path, **env: str
) -> tuple[provider_module.NextcloudOAuthProvider, OAuthStore, OAuthToken]:
    """A connection that exists: one access token, one refresh token, one app password."""
    subject, store = await approved(tmp_path, **env)
    code = await subject.load_authorization_code(registration(), CODE)
    assert code is not None
    return subject, store, await subject.exchange_authorization_code(registration(), code)


def deletion_route(status: int = 200) -> respx.Route:
    """The one Nextcloud call a revocation makes: the app password of this connection."""
    return respx.delete(f"{BASE_URL}{loginflow.APP_PASSWORD_PATH}").mock(
        return_value=httpx.Response(status)
    )


def guarded(checker: StoreTokenVerifier) -> TestClient:
    """The transport boundary alone, so a 401 can be read header by header."""

    async def endpoint(request: Request) -> Response:
        del request
        return Response("reached", status_code=200)

    route = Route(MCP_PATH, endpoint, methods=["GET"])
    route.app = RequireAppApi(route.app, ENV, token_verifier=checker)
    return TestClient(Starlette(routes=[route]))


def appapi_headers(user: str = "") -> dict[str, str]:
    """What HaRP puts on every request; an empty user id is the OAuth branch (03-01)."""
    return {
        "EX-APP-ID": "mcp_connector",
        "EX-APP-VERSION": "0.1.0",
        "AUTHORIZATION-APP-API": base64.b64encode(f"{user}:app-secret-test".encode()).decode(),
    }


@pytest.mark.anyio
async def test_revoking_a_refresh_token_ends_the_whole_family(tmp_path: Path) -> None:
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion_route()
        await subject.revoke_token(_presented_refresh(tokens))

    assert await store.load_access_token(tokens.access_token) is None
    row = await store.load_authorization(AUTH_ID)
    assert row is not None
    assert row.revoked_at is not None


@pytest.mark.anyio
async def test_revoking_an_access_token_ends_the_whole_family(tmp_path: Path) -> None:
    """RFC 7009 lets a client hand in either kind, and several of them hand in this one."""
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion_route()
        await subject.revoke_token(_presented_access(tokens))

    assert await store.load_access_token(tokens.access_token) is None
    assert await subject.load_refresh_token(registration(), tokens.refresh_token or "") is None


@pytest.mark.anyio
async def test_a_revocation_takes_effect_inside_the_cache_window(tmp_path: Path) -> None:
    """T-03-62: five seconds of a connection the user just ended is five too many."""
    subject, store, tokens = await issued(tmp_path)
    checker = StoreTokenVerifier(
        store_provider=opener(store), get_client=subject.get_client, env=ENV, clock=lambda: 1000.0
    )
    subject.on_revocation(checker.invalidate)
    assert await checker.verify_token(tokens.access_token) is not None, "the cache is warm"

    with respx.mock:
        deletion_route()
        await subject.revoke_token(_presented_refresh(tokens))

    assert await checker.verify_token(tokens.access_token) is None


@pytest.mark.anyio
async def test_the_401_after_a_revocation_points_where_an_anonymous_one_points(
    tmp_path: Path,
) -> None:
    """A client that lost its connection has to be able to start discovery again (SC 4)."""
    subject, store, tokens = await issued(tmp_path)
    checker = StoreTokenVerifier(
        store_provider=opener(store), get_client=subject.get_client, env=ENV
    )
    subject.on_revocation(checker.invalidate)

    with guarded(checker) as http:
        allowed = http.get(MCP_PATH, headers=appapi_headers() | _bearer(tokens))
        anonymous = http.get(MCP_PATH, headers=appapi_headers())
        assert allowed.status_code == 200

        with respx.mock:
            deletion_route()
            await subject.revoke_token(_presented_refresh(tokens))

        refused = http.get(MCP_PATH, headers=appapi_headers() | _bearer(tokens))

    assert refused.status_code == 401
    assert refused.headers["www-authenticate"] == anonymous.headers["www-authenticate"]
    assert "resource_metadata=" in refused.headers["www-authenticate"]
    assert (tokens.access_token or "") not in refused.text


@pytest.mark.anyio
async def test_the_revocation_hands_the_app_password_back_to_nextcloud(tmp_path: Path) -> None:
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        await subject.revoke_token(_presented_refresh(tokens))
        assert deletion.call_count == 1, "one attempt, never a retry (D-37)"

    row = await store.load_authorization(AUTH_ID)
    assert row is not None
    assert row.cleanup_at is None, "the credential is gone, so nothing is left to clean up"


@pytest.mark.anyio
async def test_a_failed_deletion_does_not_hold_up_the_revocation(tmp_path: Path) -> None:
    """Pitfall 13: a revocation that hangs on a cleanup step keeps a user connected."""
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route(status=500)
        await subject.revoke_token(_presented_refresh(tokens))
        assert deletion.call_count == 1

    assert await store.load_access_token(tokens.access_token) is None
    row = await store.load_authorization(AUTH_ID)
    assert row is not None
    assert row.revoked_at is not None
    assert row.cleanup_at is not None, "the orphaned credential is noted, not forgotten"


@pytest.mark.anyio
async def test_ending_a_connection_by_its_handle_hands_the_app_password_back(
    tmp_path: Path,
) -> None:
    """BL-01: the handle path of the user's own page ends where the token path ends.

    ``end_connection`` wrote the three revocations and stopped, so the credential stayed
    valid at Nextcloud: the sweep named in its docstring reads
    ``abandoned_authorizations``, which filters ``revoked_at IS NULL`` and can therefore
    never see a row this method just revoked.
    """
    subject, store, _tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        assert await subject.end_connection(AUTH_ID) is True
        assert deletion.call_count == 1, "one attempt, never a retry (D-37)"

    row = await store.load_authorization(AUTH_ID)
    assert row is not None
    assert row.revoked_at is not None
    assert row.cleanup_at is None, "the credential is gone, so nothing is left to clean up"


@pytest.mark.anyio
async def test_ending_a_connection_survives_a_nextcloud_that_refuses_the_deletion(
    tmp_path: Path,
) -> None:
    """Pitfall 13: "disconnected" has to mean disconnected when the request returns."""
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion_route(status=500)
        assert await subject.end_connection(AUTH_ID) is True

    assert await store.load_access_token(tokens.access_token) is None
    row = await store.load_authorization(AUTH_ID)
    assert row is not None
    assert row.revoked_at is not None
    assert row.cleanup_at is not None, "the orphaned credential is noted, not forgotten"


@pytest.mark.anyio
async def test_ending_an_unknown_connection_calls_nothing_at_all(tmp_path: Path) -> None:
    """The page answers the same sentence for unknown and revoked, and writes nothing."""
    subject, store, _tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        assert await subject.end_connection("a-handle-of-nobody") is False
        assert await subject.end_connection(AUTH_ID) is True
        assert await subject.end_connection(AUTH_ID) is False, "already revoked"
        assert deletion.call_count == 1, "the second attempt is not a second deletion"

    assert await store.load_authorization(AUTH_ID) is not None


@pytest.mark.anyio
async def test_a_token_this_server_never_issued_changes_nothing(tmp_path: Path) -> None:
    """RFC 7009 section 2.2: 200 for an unknown token, and no hint that it was unknown."""
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        await subject.revoke_presented_token(CLIENT_ID, "a-token-of-somebody-else")
        assert not deletion.called

    assert await store.load_access_token(tokens.access_token) is not None


@pytest.mark.anyio
async def test_a_client_cannot_revoke_the_connection_of_another_client(tmp_path: Path) -> None:
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        await subject.revoke_presented_token("some-other-client", tokens.refresh_token or "")
        assert not deletion.called

    assert await store.load_access_token(tokens.access_token) is not None


@pytest.mark.anyio
async def test_the_revocation_endpoint_answers_200_and_no_store(tmp_path: Path) -> None:
    subject, store, tokens = await issued(tmp_path)

    with respx.mock:
        deletion_route()
        with serving(subject) as http:
            response = http.post(
                "/revoke", data={"client_id": CLIENT_ID, "token": tokens.refresh_token or ""}
            )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert await store.load_access_token(tokens.access_token) is None


@pytest.mark.anyio
async def test_the_revocation_endpoint_refuses_a_client_it_cannot_authenticate(
    tmp_path: Path,
) -> None:
    subject, store, tokens = await issued(tmp_path, secret=SECRET)

    with serving(subject) as http:
        response = http.post(
            "/revoke",
            data={
                "client_id": CLIENT_ID,
                "client_secret": "not-the-secret",
                "token": tokens.refresh_token or "",
            },
        )

    assert response.status_code == 401
    assert await store.load_access_token(tokens.access_token) is not None


@pytest.mark.anyio
async def test_the_revocation_endpoint_refuses_a_body_without_a_token(tmp_path: Path) -> None:
    subject, _store, _tokens = await issued(tmp_path)

    with serving(subject) as http:
        response = http.post("/revoke", data={"client_id": CLIENT_ID})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


# --- the sweep of the sign ins nobody finished ---------------------------------------------


@pytest.mark.anyio
async def test_a_sign_in_nobody_finished_hands_its_credential_back(tmp_path: Path) -> None:
    """Plan 03-05 writes the app password before anybody consents, because the poll of the
    Login Flow v2 answers 200 exactly once. A browser that is closed at that moment would
    otherwise leave a working Nextcloud credential behind for good (pitfall 13, D-34)."""
    subject, store = build(tmp_path)
    await subject.register_client(registration())
    await store.create_authorization(
        "the-flow-nobody-came-back-to",
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=RESOURCE,
        now=int(time.time()) - FLOW_TTL - 1,
    )

    with respx.mock:
        deletion = deletion_route()
        swept = await subject.sweep_abandoned()

    assert swept == 1
    assert deletion.call_count == 1
    assert await store.load_authorization("the-flow-nobody-came-back-to") is None


@pytest.mark.anyio
async def test_the_sweep_leaves_a_running_sign_in_and_a_live_connection_alone(
    tmp_path: Path,
) -> None:
    subject, store, tokens = await issued(tmp_path)
    await store.create_authorization(
        "a-sign-in-that-is-still-running",
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=RESOURCE,
    )

    with respx.mock:
        deletion = deletion_route()
        swept = await subject.sweep_abandoned()
        assert not deletion.called

    assert swept == 0
    assert await store.load_authorization(AUTH_ID) is not None
    assert await store.load_access_token(tokens.access_token) is not None


@pytest.mark.anyio
async def test_the_sweep_takes_at_most_a_handful_per_call(tmp_path: Path) -> None:
    """A browser request pays for this, so the cost of one call is bounded by construction."""
    subject, store = build(tmp_path)
    await subject.register_client(registration())
    for index in range(provider_module.SWEEP_LIMIT + 3):
        await store.create_authorization(
            f"abandoned-{index}",
            client_id=CLIENT_ID,
            nc_user=NC_USER,
            app_password=APP_PASSWORD,
            scopes=metadata.TOOL_SCOPE,
            resource=RESOURCE,
            now=int(time.time()) - FLOW_TTL - 1,
        )

    with respx.mock:
        deletion_route()
        swept = await subject.sweep_abandoned()

    assert swept == provider_module.SWEEP_LIMIT


# --- WR-04: a client that runs out gives its app passwords back before its row goes --------


@pytest.mark.anyio
async def test_an_expired_client_hands_its_app_passwords_back_before_it_is_deleted(
    tmp_path: Path,
) -> None:
    """WR-04, the reachable case: a registration whose user signed in and approved while
    the client never exchanged the code has last_used_at IS NULL, so after a day the row
    went, and the cascade took the encrypted app password with it. The credential kept
    working at Nextcloud and no later sweep could find it, because the ciphertext was gone.
    """
    subject, store = build(tmp_path)
    await store.save_client(
        CLIENT_ID,
        metadata_json=registration().model_dump_json(),
        now=int(time.time()) - UNUSED_CLIENT_TTL - 1,
    )
    await store.create_authorization(
        AUTH_ID,
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=RESOURCE,
    )

    with respx.mock:
        deletion = deletion_route()
        swept = await subject.sweep_expired_clients()

    assert swept == 1
    assert deletion.call_count == 1, "the app password went back to Nextcloud"
    assert await store.load_client(CLIENT_ID) is None
    assert await store.load_authorization(AUTH_ID) is None


@pytest.mark.anyio
async def test_the_client_lookup_hands_the_credentials_back_when_it_expires_a_row(
    tmp_path: Path,
) -> None:
    """The second place a client row is deleted, and it is the one on the request path."""
    subject, store = build(tmp_path)
    await store.save_client(
        CLIENT_ID,
        metadata_json=registration().model_dump_json(),
        now=int(time.time()) - UNUSED_CLIENT_TTL - 1,
    )
    await store.create_authorization(
        AUTH_ID,
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=RESOURCE,
    )

    with respx.mock:
        deletion = deletion_route()
        assert await subject.get_client(CLIENT_ID) is None

    assert deletion.call_count == 1
    assert await store.load_authorization(AUTH_ID) is None


@pytest.mark.anyio
async def test_an_expired_client_hands_back_more_connections_than_the_sweep_limit(
    tmp_path: Path,
) -> None:
    """BL-01, point 4: ``delete_client`` cascades, so a capped read loses the rest silently.

    ``authorizations_of_client`` was read once with ``SWEEP_LIMIT`` and the delete of the
    client row took every further connection with it, ciphertext included. From the fourth
    connection of one registration on, the app password was neither handed back nor
    findable by any later sweep, which is exactly the failure mode WR-04 was built against.
    """
    subject, store = build(tmp_path)
    await store.save_client(
        CLIENT_ID,
        metadata_json=registration().model_dump_json(),
        now=int(time.time()) - UNUSED_CLIENT_TTL - 1,
    )
    handles = [f"connection-{index}" for index in range(provider_module.SWEEP_LIMIT + 2)]
    for handle in handles:
        await store.create_authorization(
            handle,
            client_id=CLIENT_ID,
            nc_user=NC_USER,
            app_password=APP_PASSWORD,
            scopes=metadata.TOOL_SCOPE,
            resource=RESOURCE,
        )

    with respx.mock:
        deletion = deletion_route()
        swept = await subject.sweep_expired_clients()

    assert swept == 1
    assert deletion.call_count == len(handles), "every credential of that client went back"
    for handle in handles:
        assert await store.load_authorization(handle) is None


@pytest.mark.anyio
async def test_a_client_that_did_not_run_out_keeps_its_connections(tmp_path: Path) -> None:
    """The counter probe: the sweep must not touch a registration that is in use."""
    subject, store = await approved(tmp_path)

    with respx.mock:
        deletion = deletion_route()
        swept = await subject.sweep_expired_clients()

    assert swept == 0
    assert not deletion.called
    assert await store.load_authorization(AUTH_ID) is not None
    assert await store.load_client(CLIENT_ID) is not None


@pytest.mark.anyio
async def test_a_revocation_that_fails_still_removes_the_expired_client(
    tmp_path: Path,
) -> None:
    """The rule of every cleanup path of this phase: the row goes even when the credential
    could not be handed back, and the failure is loud in the log rather than silent."""
    subject, store = build(tmp_path)
    await store.save_client(
        CLIENT_ID,
        metadata_json=registration().model_dump_json(),
        now=int(time.time()) - UNUSED_CLIENT_TTL - 1,
    )
    await store.create_authorization(
        AUTH_ID,
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=metadata.TOOL_SCOPE,
        resource=RESOURCE,
    )

    with respx.mock:
        deletion_route(500)
        swept = await subject.sweep_expired_clients()

    assert swept == 1
    assert await store.load_client(CLIENT_ID) is None
    assert await store.load_authorization(AUTH_ID) is None


# --- the throttle of our own authorization paths (SC 5, D-37) ------------------------------


def probe(
    *, machine: bool, limit: int = 3, ceiling: int = 100
) -> tuple[TestClient, throttle_module.Throttle]:
    """One route that answers whatever a caller asks for, behind the throttle wrapper."""
    box = throttle_module.Throttle(limit=limit, ceiling=ceiling, window=60)

    async def endpoint(request: Request) -> Response:
        return Response("body", status_code=int(request.query_params.get("status") or 400))

    route = Route("/probe", endpoint, methods=["GET"])
    route.app = throttle_module.Throttled(route.app, box, "probe", machine=machine, env=ENV)
    return TestClient(Starlette(routes=[route])), box


def test_a_flood_of_failures_ends_in_429_with_a_retry_after() -> None:
    http, _box = probe(machine=True)

    for _attempt in range(3):
        assert http.get("/probe").status_code == 400

    throttled = http.get("/probe")
    assert throttled.status_code == 429
    assert int(throttled.headers["retry-after"]) >= 1
    assert throttled.headers["cache-control"] == "no-store"


def test_the_json_answer_names_the_same_seconds_as_its_header() -> None:
    http, _box = probe(machine=True)
    for _attempt in range(3):
        http.get("/probe")

    throttled = http.get("/probe")

    body = throttled.json()
    assert body["error"] == "temporarily_unavailable"
    assert throttled.headers["retry-after"] in body["error_description"]


def test_the_html_answer_names_the_same_seconds_as_its_header() -> None:
    http, _box = probe(machine=False)
    for _attempt in range(3):
        http.get("/probe")

    throttled = http.get("/probe")
    seconds = throttled.headers["retry-after"]

    assert throttled.status_code == 429
    assert "text/html" in throttled.headers["content-type"]
    assert f"Wait {seconds} seconds" in throttled.text
    assert throttled.headers["cache-control"] == "no-store"


def test_a_successful_request_pays_back_one_failure_and_never_the_window() -> None:
    """WR-03: clearing the counter was an off switch. The path classes are shared surfaces,
    so a caller guessing flow ids only had to interleave one harmless successful request
    every ninth attempt to stay at zero forever. One success pays back exactly one failure:
    two failures, a success, two failures is three, and three is the limit here."""
    http, _box = probe(machine=True)

    for _attempt in range(2):
        assert http.get("/probe").status_code == 400
    assert http.get("/probe?status=200").status_code == 200
    for _attempt in range(2):
        assert http.get("/probe").status_code == 400

    assert http.get("/probe?status=200").status_code == 429


def test_a_success_never_pays_back_more_than_it_spent() -> None:
    """The forgiving half of the same rule: a person who mistypes something twice and then
    succeeds does not carry the two around for the rest of the window."""
    http, _box = probe(machine=True)

    assert http.get("/probe").status_code == 400
    for _attempt in range(3):
        assert http.get("/probe?status=200").status_code == 200

    for _attempt in range(2):
        assert http.get("/probe").status_code == 400
    assert http.get("/probe?status=200").status_code == 200


def test_a_forged_forwarded_header_still_meets_the_global_ceiling() -> None:
    """The per source counter can be split by anybody who can write a header; the ceiling
    of the path class cannot, and that is what keeps the Nextcloud round trips bounded."""
    http, _box = probe(machine=True, limit=3, ceiling=5)

    for index in range(5):
        answer = http.get("/probe", headers={"X-Forwarded-For": f"10.0.0.{index}"})
        assert answer.status_code == 400

    assert http.get("/probe", headers={"X-Forwarded-For": "10.0.0.99"}).status_code == 429


def test_the_throttle_remembers_a_bounded_number_of_sources() -> None:
    box = throttle_module.Throttle(limit=3, ceiling=1000, window=60)

    for index in range(throttle_module.SOURCE_LIMIT + 50):
        box.record_attempt("probe", f"10.0.0.{index}")

    assert len(box._counters) <= throttle_module.SOURCE_LIMIT


def test_the_throttle_stores_neither_a_credential_nor_an_identity() -> None:
    """T-03-65: a counter that keeps what it counted is itself a source of data."""
    box = throttle_module.Throttle(limit=3, ceiling=100, window=60)

    box.record_attempt(throttle_module.CLASS_TOKEN, "10.0.0.7")

    kept = repr(sorted(box._counters))
    assert "10.0.0.7" not in kept, "the source is a digest, never the address"
    assert throttle_module.CLASS_TOKEN not in kept
    assert all(len(key) == 64 for key in box._counters), "SHA-256 hex and nothing else"

    tree = ast.parse(inspect.getsource(throttle_module))
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            first = node.body[0] if node.body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:] or [ast.Pass()]
    code = ast.unparse(ast.fix_missing_locations(tree)).lower()

    assert "sha256" in code, "the source of a request is remembered as a digest"
    assert "authorization" not in code, "the credential header is never read here"
    assert "nc_user" not in code
    assert "refresh" not in code


def test_the_authorization_paths_are_throttled_and_the_mcp_route_is_not() -> None:
    """SC 5: the throttle sits on our own authorization paths, never on the tool call."""
    throttled = {
        getattr(route, "path", "")
        for route in _exapp_routes()
        if _is_throttled(getattr(route, "app", None))
    }

    assert {"/token", "/register", "/revoke", "/authorize"} <= throttled
    assert MCP_PATH not in throttled


@pytest.mark.anyio
async def test_a_flood_against_the_token_endpoint_reaches_no_nextcloud(tmp_path: Path) -> None:
    """Pitfall 5: every request with an Authorization header costs a Nextcloud round trip,
    and the throttle is the only thing that bounds how many of them a flood can buy."""
    subject, _store = await approved(tmp_path, secret=SECRET)
    box = throttle_module.Throttle(limit=3, ceiling=100, window=60)

    with respx.mock, serving(subject, throttle=box) as http:
        answers = [
            http.post("/token", data=token_request(client_secret="wrong")).status_code
            for _attempt in range(5)
        ]
        assert len(respx.calls) == 0

    assert answers[:3] == [401, 401, 401]
    assert answers[-1] == 429


def _is_throttled(app: object) -> bool:
    """Whether this route carries the throttle, under the ``no-store`` wrapper or not."""
    while app is not None:
        if isinstance(app, throttle_module.Throttled):
            return True
        app = getattr(app, "_app", None)
    return False


def _bearer(tokens: OAuthToken) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens.access_token}"}


def _presented_refresh(tokens: OAuthToken) -> RefreshToken:
    return RefreshToken(
        token=tokens.refresh_token or "", client_id=CLIENT_ID, scopes=[metadata.TOOL_SCOPE]
    )


def _presented_access(tokens: OAuthToken) -> AccessToken:
    return AccessToken(token=tokens.access_token, client_id=CLIENT_ID, scopes=[metadata.TOOL_SCOPE])
