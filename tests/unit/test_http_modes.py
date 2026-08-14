"""The three exclusive credential modes of the connector (D-12, AUTH-01).

One identity source per mode, chosen once and never mixed: environment (stdio), the
Basic credentials of the request (HTTP passthrough) or a static bearer that guards a
single-user deployment while the Nextcloud credentials still come from the environment.

Threats covered here: T-01-21 (credentials must never appear in an error message),
T-01-23 (a header is not an identity assertion, it is material we hand to Nextcloud)
and T-01-24 (the static bearer is compared in constant time).

No HTTP server and no Nextcloud are involved: a fake context with a headers attribute
is exactly what the SDK hands a tool.
"""

import base64
import inspect
import logging

import pytest

from mcp_connector import config, deps

BASE_URL = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
BEARER = "static-bearer-token"


class FakeContext:
    """Stand-in for the SDK context: ``headers`` is ``None`` on stdio and in-memory."""

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers


def basic(user: str = USER, secret: str = SECRET) -> str:
    raw = f"{user}:{secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


@pytest.fixture
def env_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nextcloud connection data in the environment, no static bearer."""
    monkeypatch.setenv(config.ENV_URL, BASE_URL)
    monkeypatch.setenv(config.ENV_USER, USER)
    monkeypatch.setenv(config.ENV_APP_PASSWORD, SECRET)
    monkeypatch.delenv(config.ENV_STATIC_BEARER, raising=False)


# --- mode selection --------------------------------------------------------------


def test_select_mode_without_headers_is_stdio() -> None:
    assert config.select_mode({}, headers=None) == "stdio"


def test_select_mode_with_headers_is_passthrough() -> None:
    assert config.select_mode({}, headers={"authorization": basic()}) == "http_passthrough"


def test_select_mode_with_static_bearer_is_static_bearer() -> None:
    env = {config.ENV_STATIC_BEARER: BEARER}
    assert config.select_mode(env, headers={}) == "http_static_bearer"


def test_select_mode_ignores_a_blank_static_bearer() -> None:
    env = {config.ENV_STATIC_BEARER: "   "}
    assert config.select_mode(env, headers={}) == "http_passthrough"


def test_static_bearer_wins_over_headers_but_never_over_stdio() -> None:
    """A stdio process has no headers, so it can never fall into an HTTP mode."""
    env = {config.ENV_STATIC_BEARER: BEARER}
    assert config.select_mode(env, headers=None) == "stdio"


# --- stdio mode ------------------------------------------------------------------


def test_stdio_mode_uses_the_environment(env_credentials: None) -> None:
    creds = deps.resolve_credentials(FakeContext(headers=None))
    assert (creds.base_url, creds.user, creds.secret) == (BASE_URL, USER, SECRET)


def test_a_missing_context_is_treated_as_stdio(env_credentials: None) -> None:
    creds = deps.resolve_credentials(None)
    assert creds.user == USER


# --- HTTP passthrough ------------------------------------------------------------


def test_passthrough_decodes_the_basic_credentials(env_credentials: None) -> None:
    ctx = FakeContext(headers={"authorization": basic("bob", "bobs-app-password")})
    creds = deps.resolve_credentials(ctx)
    assert creds.user == "bob"
    assert creds.secret == "bobs-app-password"
    assert creds.base_url == BASE_URL, "the target instance always comes from the environment"


def test_passthrough_accepts_a_lowercase_scheme(env_credentials: None) -> None:
    header = basic().replace("Basic ", "basic ")
    creds = deps.resolve_credentials(FakeContext(headers={"authorization": header}))
    assert creds.user == USER


def test_passthrough_keeps_a_colon_inside_the_password(env_credentials: None) -> None:
    ctx = FakeContext(headers={"authorization": basic(USER, "pass:with:colons")})
    assert deps.resolve_credentials(ctx).secret == "pass:with:colons"


def test_missing_authorization_raises_mcperror_not_valueerror(env_credentials: None) -> None:
    with pytest.raises(deps.MCPError) as excinfo:
        deps.resolve_credentials(FakeContext(headers={}))
    message = excinfo.value.message
    assert "Basic" in message
    assert "app password" in message.lower()


def test_a_bearer_header_in_passthrough_mode_explains_the_expected_scheme(
    env_credentials: None,
) -> None:
    ctx = FakeContext(headers={"authorization": "Bearer some-token"})
    with pytest.raises(deps.MCPError) as excinfo:
        deps.resolve_credentials(ctx)
    assert "Basic" in excinfo.value.message


def test_broken_base64_raises_mcperror(env_credentials: None) -> None:
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers={"authorization": "Basic not-base64!!"}))


def test_base64_without_a_colon_raises_mcperror(env_credentials: None) -> None:
    payload = base64.b64encode(b"no-colon-here").decode()
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers={"authorization": f"Basic {payload}"}))


def test_an_empty_user_is_rejected(env_credentials: None) -> None:
    payload = base64.b64encode(b":only-a-secret").decode()
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers={"authorization": f"Basic {payload}"}))


@pytest.mark.parametrize(
    "header",
    [
        "Bearer some-token",
        "Basic not-base64!!",
        "Basic " + base64.b64encode(b"no-colon-here").decode(),
        basic(USER, "should-never-be-echoed"),
    ],
)
def test_no_error_message_ever_repeats_the_header(env_credentials: None, header: str) -> None:
    """T-01-21: the header is material, not text we are allowed to quote back."""
    try:
        deps.resolve_credentials(FakeContext(headers={"authorization": header}))
    except deps.MCPError as exc:
        text = f"{exc.message} {exc}"
        assert header not in text
        assert header.split(" ", 1)[1] not in text
        assert "should-never-be-echoed" not in text


def test_resolution_writes_nothing_to_the_log(
    env_credentials: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        deps.resolve_credentials(FakeContext(headers={"authorization": basic()}))
    assert SECRET not in caplog.text
    assert caplog.text.strip() == ""


# --- static bearer ---------------------------------------------------------------


def test_static_bearer_mode_uses_the_environment_credentials(
    env_credentials: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bearer authenticates the caller; Nextcloud is still reached with env data."""
    monkeypatch.setenv(config.ENV_STATIC_BEARER, BEARER)
    ctx = FakeContext(headers={"authorization": f"Bearer {BEARER}"})
    creds = deps.resolve_credentials(ctx)
    assert (creds.user, creds.secret) == (USER, SECRET)


def test_static_bearer_mode_ignores_a_basic_header(
    env_credentials: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(config.ENV_STATIC_BEARER, BEARER)
    ctx = FakeContext(headers={"authorization": basic("mallory", "mallorys-password")})
    creds = deps.resolve_credentials(ctx)
    assert creds.user == USER, "a single-user deployment never switches user by header"


@pytest.mark.anyio
async def test_the_verifier_accepts_the_configured_token() -> None:
    verifier = deps.StaticBearerVerifier(BEARER)
    token = await verifier.verify_token(BEARER)
    assert token is not None
    assert token.token == BEARER


@pytest.mark.anyio
async def test_the_verifier_rejects_a_wrong_token() -> None:
    verifier = deps.StaticBearerVerifier(BEARER)
    assert await verifier.verify_token("wrong") is None
    assert await verifier.verify_token("") is None
    assert await verifier.verify_token(BEARER + "x") is None


@pytest.mark.anyio
async def test_a_non_ascii_bearer_is_rejected_and_never_crashes() -> None:
    """``compare_digest`` raises TypeError on non-ASCII str input; hostile header
    content must land on the 401 path, never on a 500 (WR-01)."""
    verifier = deps.StaticBearerVerifier(BEARER)
    assert await verifier.verify_token("töken-mit-ümlaut-ß") is None
    assert await verifier.verify_token(BEARER + "é") is None


@pytest.mark.anyio
async def test_a_non_ascii_configured_token_still_authenticates_its_own_value() -> None:
    """A non-ASCII NC_MCP_STATIC_BEARER must not break every request with a crash."""
    verifier = deps.StaticBearerVerifier("geheim-ü-token")
    token = await verifier.verify_token("geheim-ü-token")
    assert token is not None
    assert await verifier.verify_token("geheim-u-token") is None


def test_the_verifier_compares_in_constant_time() -> None:
    """T-01-24: a plain ``==`` would leak the token length by length of comparison."""
    source = inspect.getsource(deps.StaticBearerVerifier)
    assert "compare_digest" in source


def test_build_auth_configures_nothing_in_passthrough_mode() -> None:
    verifier, settings = deps.build_auth({config.ENV_URL: BASE_URL})
    assert verifier is None
    assert settings is None, "auth= and token_verifier= belong to the bearer mode only"


def test_build_auth_configures_both_in_static_bearer_mode() -> None:
    verifier, settings = deps.build_auth({config.ENV_STATIC_BEARER: BEARER})
    assert verifier is not None
    assert settings is not None, "the SDK raises ValueError unless both are set together"


# --- transport hardening inputs --------------------------------------------------


def test_allowed_hosts_defaults_to_localhost() -> None:
    hosts = config.allowed_hosts({})
    assert "127.0.0.1" in hosts
    assert "127.0.0.1:*" in hosts
    assert "localhost" in hosts
    assert not any(host.startswith("mcp.") for host in hosts)


def test_allowed_hosts_adds_a_port_wildcard_per_name() -> None:
    hosts = config.allowed_hosts({config.ENV_ALLOWED_HOSTS: "mcp.example.com, nc.example.com"})
    assert hosts == [
        "mcp.example.com",
        "mcp.example.com:*",
        "nc.example.com",
        "nc.example.com:*",
    ]


def test_an_explicit_port_is_kept_verbatim() -> None:
    hosts = config.allowed_hosts({config.ENV_ALLOWED_HOSTS: "mcp.example.com:8765"})
    assert hosts == ["mcp.example.com:8765"]


def test_dns_rebinding_protection_is_on_by_default() -> None:
    assert config.dns_rebinding_protection({}) is True


def test_dns_rebinding_protection_can_be_switched_off_for_a_proxy() -> None:
    env = {config.ENV_DISABLE_DNS_REBINDING: "true"}
    assert config.dns_rebinding_protection(env) is False
