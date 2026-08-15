"""The fourth credential mode, from the header down to the outgoing request (AUTH-05).

Three layers are covered here and nothing else:

* :class:`Credentials` knows its own mode and hands out the matching ``httpx.Auth``
* ``deps.resolve_credentials`` builds those credentials from the AppAPI headers alone
* every client module asks the credentials instead of hard wiring Basic auth

Threats covered here: T-02-10 (the client must not be able to pick the user), T-02-11
(a second accepted auth channel), T-02-12 (data access without a user), T-02-13
(``APP_SECRET`` or the base64 token in a repr) and T-02-15 (a module falling back to
hard wired Basic auth).

No server, no Nextcloud and no network: ``auth_flow`` is a generator over a request
object, and respx answers the one call that leaves the process.
"""

import base64
import inspect
import logging

import httpx
import pytest

from mcp_connector import config, deps
from mcp_connector.nextcloud.credentials import AppApiAuth, Credentials

BASE_URL = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
AA_VERSION = "34.0.3"


def appapi_credentials(user: str = USER, secret: str = APP_SECRET) -> Credentials:
    """Credentials as the ExApp mode builds them: the app secret, not a user password."""
    return Credentials(
        base_url=BASE_URL,
        user=user,
        secret=secret,
        mode="appapi",
        app_id=APP_ID,
        app_version=APP_VERSION,
        aa_version=AA_VERSION,
    )


def token(user: str = USER, secret: str = APP_SECRET) -> str:
    """The AUTHORIZATION-APP-API value exactly as AppAPI builds it."""
    return base64.b64encode(f"{user}:{secret}".encode()).decode()


def appapi_headers(user: str = USER, secret: str = APP_SECRET) -> dict[str, str]:
    """The three headers HaRP puts in front of every request it forwards."""
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token(user, secret),
    }


def basic() -> str:
    """A Basic header of somebody else, offered as a second channel on purpose."""
    return "Basic " + base64.b64encode(b"mallory:another-password").decode()


class FakeContext:
    """Stand-in for the SDK context: ``headers`` is ``None`` on stdio and in-memory."""

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers


@pytest.fixture
def exapp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """The deploy environment AppAPI injects into the ExApp container."""
    monkeypatch.setenv(config.ENV_APP_ID, APP_ID)
    monkeypatch.setenv(config.ENV_APP_SECRET, APP_SECRET)
    monkeypatch.setenv(config.ENV_APP_VERSION, APP_VERSION)
    monkeypatch.setenv(config.ENV_AA_VERSION, AA_VERSION)
    monkeypatch.setenv(config.ENV_NEXTCLOUD_URL, BASE_URL)
    # An ExApp container has neither of these, and phase 1 must not leak into this mode.
    monkeypatch.delenv(config.ENV_STATIC_BEARER, raising=False)
    monkeypatch.delenv(config.ENV_APP_PASSWORD, raising=False)


def flow(auth: httpx.Auth, request: httpx.Request) -> list[httpx.Request]:
    """Run one auth flow to completion without any network or response."""
    return list(auth.auth_flow(request))


def request() -> httpx.Request:
    return httpx.Request("GET", f"{BASE_URL}/ocs/v2.php/cloud/user")


# --- the mode field ---------------------------------------------------------------


def test_credentials_without_a_mode_are_basic() -> None:
    """All existing construction sites keep working unchanged: three positional values."""
    creds = Credentials(BASE_URL, USER, SECRET)
    assert creds.mode == "basic"
    assert creds.app_id == ""
    assert creds.app_version == ""
    assert creds.aa_version == ""


def test_basic_mode_hands_out_basic_auth() -> None:
    creds = Credentials(BASE_URL, USER, SECRET)
    auth = creds.auth()
    assert isinstance(auth, httpx.BasicAuth)

    [sent] = flow(auth, request())
    expected = base64.b64encode(f"{USER}:{SECRET}".encode()).decode()
    assert sent.headers["authorization"] == f"Basic {expected}"


def test_appapi_mode_hands_out_the_appapi_auth() -> None:
    auth = appapi_credentials().auth()
    assert isinstance(auth, AppApiAuth)


def test_an_unknown_mode_is_refused_instead_of_falling_back_to_basic() -> None:
    """D-27: a silent fallback to Basic would authenticate with the app secret as a user."""
    creds = Credentials(BASE_URL, USER, SECRET, mode="bearer")
    with pytest.raises(ValueError, match="bearer"):
        creds.auth()


def test_the_error_of_an_unknown_mode_carries_no_secret() -> None:
    creds = Credentials(BASE_URL, USER, SECRET, mode="bearer")
    with pytest.raises(ValueError, match="credential mode") as excinfo:
        creds.auth()
    assert SECRET not in str(excinfo.value)


# --- the outgoing headers ---------------------------------------------------------


def test_the_appapi_auth_sets_exactly_the_four_headers() -> None:
    [sent] = flow(appapi_credentials().auth(), request())

    assert sent.headers["AA-VERSION"] == AA_VERSION
    assert sent.headers["EX-APP-ID"] == APP_ID
    assert sent.headers["EX-APP-VERSION"] == APP_VERSION
    assert sent.headers["AUTHORIZATION-APP-API"]


def test_the_token_decodes_to_user_and_app_secret() -> None:
    """The user id is the whole point: Nextcloud impersonates whoever stands in front."""
    [sent] = flow(appapi_credentials().auth(), request())

    decoded = base64.b64decode(sent.headers["AUTHORIZATION-APP-API"], validate=True).decode()
    assert decoded == f"{USER}:{APP_SECRET}"


def test_the_appapi_auth_sets_no_authorization_header() -> None:
    """T-02-11: the ExApp mode has exactly one auth channel, and Basic is not it."""
    [sent] = flow(appapi_credentials().auth(), request())
    assert "authorization" not in sent.headers


def test_the_appapi_auth_leaves_foreign_headers_alone() -> None:
    original = httpx.Request(
        "GET",
        f"{BASE_URL}/ocs/v2.php/cloud/user",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    )
    [sent] = flow(appapi_credentials().auth(), original)

    assert sent.headers["OCS-APIRequest"] == "true"
    assert sent.headers["Accept"] == "application/json"


def test_the_appapi_auth_is_stateless_and_has_no_retry_branch() -> None:
    """One yield, no response handling: a retry would replay the impersonation blindly."""
    auth = appapi_credentials().auth()

    first = flow(auth, request())
    second = flow(auth, request())

    assert len(first) == 1
    assert len(second) == 1
    assert dict(first[0].headers) == dict(second[0].headers)


def test_a_non_ascii_user_or_secret_still_produces_a_header() -> None:
    """A crash here would turn a German user id into a 500 instead of a request."""
    [sent] = flow(appapi_credentials(user="björn", secret="geheimnüss").auth(), request())

    decoded = base64.b64decode(sent.headers["AUTHORIZATION-APP-API"], validate=True).decode()
    assert decoded == "björn:geheimnüss"


# --- masking ----------------------------------------------------------------------


def test_the_repr_of_appapi_credentials_shows_the_mode_and_masks_the_secret() -> None:
    creds = appapi_credentials()
    text = repr(creds)

    assert BASE_URL in text
    assert USER in text
    assert "appapi" in text
    assert "***" in text
    assert APP_SECRET not in text


def test_the_repr_of_appapi_credentials_hides_the_base64_token() -> None:
    """T-02-13: base64 is an encoding, so the token is as sensitive as the secret."""
    creds = appapi_credentials()
    token = base64.b64encode(f"{USER}:{APP_SECRET}".encode()).decode()
    assert token not in repr(creds)


def test_the_repr_of_the_appapi_auth_hides_secret_and_token() -> None:
    auth = appapi_credentials().auth()
    text = repr(auth)

    assert APP_SECRET not in text
    assert token() not in text
    assert "AppApiAuth" in text
    assert APP_ID in text


# --- the fourth branch of resolve_credentials -------------------------------------


def test_the_exapp_mode_takes_the_user_from_the_appapi_header(exapp_env: None) -> None:
    creds = deps.resolve_credentials(FakeContext(headers=appapi_headers(user="bob")))

    assert creds.mode == "appapi"
    assert creds.user == "bob"
    assert creds.secret == APP_SECRET
    assert creds.base_url == BASE_URL
    assert creds.app_id == APP_ID
    assert creds.app_version == APP_VERSION
    assert creds.aa_version == AA_VERSION


def test_an_additional_basic_header_changes_nothing(exapp_env: None) -> None:
    """T-02-11, D-27: HaRP forwards whatever the client sent, and we read one channel."""
    without = deps.resolve_credentials(FakeContext(headers=appapi_headers(user="bob")))

    with_basic = dict(appapi_headers(user="bob"))
    with_basic["Authorization"] = basic()
    result = deps.resolve_credentials(FakeContext(headers=with_basic))

    assert result == without
    assert result.user == "bob"


def test_a_basic_header_alone_is_not_enough_in_the_exapp_mode(exapp_env: None) -> None:
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers={"Authorization": basic()}))


def test_an_empty_user_id_gets_no_data_access(exapp_env: None) -> None:
    """T-02-12: the app context is a valid token and still not a person."""
    with pytest.raises(deps.MCPError) as excinfo:
        deps.resolve_credentials(FakeContext(headers=appapi_headers(user="")))

    assert "user" in excinfo.value.message.lower()


def test_a_wrong_app_secret_is_refused(exapp_env: None) -> None:
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers=appapi_headers(secret="wrong-secret")))


def test_a_missing_appapi_header_is_refused(exapp_env: None) -> None:
    with pytest.raises(deps.MCPError):
        deps.resolve_credentials(FakeContext(headers={}))


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": basic()},
        {**appapi_headers(), "AUTHORIZATION-APP-API": "not base64 at all"},
        appapi_headers(secret="wrong-secret"),
        appapi_headers(user=""),
    ],
)
def test_no_refusal_ever_repeats_a_header_value(exapp_env: None, headers: dict[str, str]) -> None:
    """T-02-03: the header is credential material, not text we may quote back."""
    try:
        deps.resolve_credentials(FakeContext(headers=headers))
    except deps.MCPError as exc:
        text = f"{exc.message} {exc}"
        for value in headers.values():
            assert value not in text
        assert APP_SECRET not in text


def test_the_exapp_resolution_writes_nothing_to_the_log(
    exapp_env: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        deps.resolve_credentials(FakeContext(headers=appapi_headers(user="bob")))

    assert APP_SECRET not in caplog.text
    assert caplog.text.strip() == ""


def test_resolve_credentials_still_takes_exactly_one_parameter() -> None:
    """T-02-10: no tool and no caller may hand in a user id next to the context."""
    params = list(inspect.signature(deps.resolve_credentials).parameters)
    assert params == ["ctx"]


def test_the_stdio_mode_is_untouched_by_the_new_branch(
    monkeypatch: pytest.MonkeyPatch, nc_env: dict[str, str]
) -> None:
    """A stdio process has no headers, so no deploy variable can move it into ExApp."""
    monkeypatch.setenv(config.ENV_APP_ID, APP_ID)
    monkeypatch.setenv(config.ENV_APP_SECRET, APP_SECRET)
    monkeypatch.setenv(config.ENV_URL, nc_env["base_url"])
    monkeypatch.setenv(config.ENV_USER, nc_env["user"])
    monkeypatch.setenv(config.ENV_APP_PASSWORD, nc_env["secret"])

    creds = deps.resolve_credentials(FakeContext(headers=None))

    assert creds.mode == "basic"
    assert creds.user == nc_env["user"]
