"""The AppAPI handshake: three headers in, one Nextcloud user id out (EXAPP-01).

The incoming caller is AppAPI, not a model, so a rejected request gets a bare 401 and
never an explanation. That is the one place where this project deviates from its own
"message plus hint" error format on purpose.

Threats covered here: T-02-01 (a forged AUTHORIZATION-APP-API is rejected), T-02-02 (the
secret is compared in constant time) and T-02-03 (neither the exception nor a log record
ever repeats the received value).

No server and no Nextcloud are involved: a plain dict of headers is all the verifier
needs, which is also why it builds its own case insensitive lookup.
"""

import base64
import inspect
import logging

import pytest

from mcp_connector import config
from mcp_connector.exapp import auth
from mcp_connector.nextcloud.credentials import appapi_auth_headers

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
AA_VERSION = "34.0.3"
USER = "alice"
BASE_URL = "http://nc.test"


def token(user: str = USER, secret: str = APP_SECRET) -> str:
    """Build the AUTHORIZATION-APP-API value exactly like AppAPI does."""
    return base64.b64encode(f"{user}:{secret}".encode()).decode()


def appapi_headers(
    user: str = USER,
    secret: str = APP_SECRET,
    app_id: str = APP_ID,
    version: str = APP_VERSION,
) -> dict[str, str]:
    """The three headers every AppAPI request carries, in AppAPI's own spelling."""
    return {
        "EX-APP-ID": app_id,
        "EX-APP-VERSION": version,
        "AUTHORIZATION-APP-API": token(user, secret),
    }


def exapp_env() -> dict[str, str]:
    """A complete deploy environment as the AppAPI deploy daemon would set it."""
    return {
        config.ENV_APP_ID: APP_ID,
        config.ENV_APP_SECRET: APP_SECRET,
        config.ENV_APP_VERSION: APP_VERSION,
        config.ENV_AA_VERSION: AA_VERSION,
        config.ENV_NEXTCLOUD_URL: BASE_URL,
    }


# --- the happy paths -------------------------------------------------------------


def test_valid_headers_return_the_user_id() -> None:
    assert auth.verify_appapi_headers(appapi_headers(), APP_ID, APP_SECRET) == USER


def test_an_empty_user_is_the_app_context_and_no_error() -> None:
    """An empty user id means "app context, no user". Rejecting data access for it is
    the job of the credential layer, not of the parser."""
    headers = appapi_headers(user="")
    assert auth.verify_appapi_headers(headers, APP_ID, APP_SECRET) == ""


def test_the_lookup_ignores_the_header_case() -> None:
    """Starlette headers are case insensitive, a plain dict is not. The verifier is."""
    headers = {key.lower(): value for key, value in appapi_headers().items()}
    assert auth.verify_appapi_headers(headers, APP_ID, APP_SECRET) == USER


def test_a_colon_inside_the_user_id_stays_with_the_secret_boundary() -> None:
    """partition splits at the first colon, so the secret keeps every later one."""
    raw = base64.b64encode(f"{USER}:{APP_SECRET}".encode()).decode()
    headers = appapi_headers()
    headers["AUTHORIZATION-APP-API"] = raw
    assert auth.verify_appapi_headers(headers, APP_ID, APP_SECRET) == USER


# --- rejections ------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing",
    ["EX-APP-ID", "EX-APP-VERSION", "AUTHORIZATION-APP-API"],
)
def test_a_missing_header_is_rejected(missing: str) -> None:
    headers = appapi_headers()
    del headers[missing]
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


@pytest.mark.parametrize(
    "blank",
    ["EX-APP-ID", "EX-APP-VERSION", "AUTHORIZATION-APP-API"],
)
def test_a_blank_header_is_rejected(blank: str) -> None:
    headers = appapi_headers()
    headers[blank] = ""
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


def test_a_foreign_app_id_is_rejected() -> None:
    headers = appapi_headers(app_id="some_other_app")
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


def test_broken_base64_is_rejected() -> None:
    headers = appapi_headers()
    headers["AUTHORIZATION-APP-API"] = "not-base64!!"
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


def test_a_token_without_a_separator_is_rejected() -> None:
    headers = appapi_headers()
    headers["AUTHORIZATION-APP-API"] = base64.b64encode(b"no-colon-here").decode()
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


def test_a_wrong_secret_is_rejected() -> None:
    headers = appapi_headers(secret="the-wrong-secret")
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


@pytest.mark.parametrize(
    "headers",
    [
        {
            "EX-APP-ID": "mcp_connectör",
            "EX-APP-VERSION": APP_VERSION,
            "AUTHORIZATION-APP-API": token(),
        },
        {
            "EX-APP-ID": APP_ID,
            "EX-APP-VERSION": APP_VERSION,
            "AUTHORIZATION-APP-API": base64.b64encode("alice:gehäim".encode()).decode(),
        },
    ],
)
def test_a_non_ascii_value_is_rejected_and_never_crashes(headers: dict[str, str]) -> None:
    """compare_digest raises TypeError on non-ASCII str input; hostile header content
    must land on the 401 path, never on a 500 (WR-01, same rule as the static bearer)."""
    with pytest.raises(auth.AppApiRejected):
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)


# --- no echo, no log, constant time ----------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "not-base64!!",
        base64.b64encode(b"no-colon-here").decode(),
        token(USER, "should-never-be-echoed"),
    ],
)
def test_no_rejection_ever_repeats_the_header(raw: str) -> None:
    """T-02-03: the header is credential material, not text we may quote back."""
    headers = appapi_headers()
    headers["AUTHORIZATION-APP-API"] = raw
    try:
        auth.verify_appapi_headers(headers, APP_ID, APP_SECRET)
    except auth.AppApiRejected as exc:
        text = f"{exc} {exc.args!r}"
        assert raw not in text
        assert "should-never-be-echoed" not in text


def test_verification_writes_nothing_to_the_log(caplog: pytest.LogCaptureFixture) -> None:
    """T-02-03: not on DEBUG, not truncated, not the successful case either."""
    with caplog.at_level(logging.DEBUG):
        auth.verify_appapi_headers(appapi_headers(), APP_ID, APP_SECRET)
        with pytest.raises(auth.AppApiRejected):
            auth.verify_appapi_headers(appapi_headers(secret="wrong"), APP_ID, APP_SECRET)
    assert APP_SECRET not in caplog.text
    assert caplog.text.strip() == ""


def test_the_verifier_compares_in_constant_time() -> None:
    """T-02-02: a plain == leaks the shared prefix of the secret over enough requests."""
    source = inspect.getsource(auth)
    assert source.count("compare_digest") >= 2, "app id and secret are both compared"
    assert " == " not in source.split("def verify_appapi_headers", 1)[1].split("def ", 1)[0]


# --- the thin Starlette wrapper --------------------------------------------------


class FakeRequest:
    """Stand-in for a Starlette request: only ``headers`` is read."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def test_require_appapi_reads_the_settings_and_returns_the_user() -> None:
    request = FakeRequest(appapi_headers())
    assert auth.require_appapi(request, env=exapp_env()) == USER  # type: ignore[arg-type]


def test_require_appapi_passes_the_rejection_through() -> None:
    request = FakeRequest(appapi_headers(secret="wrong"))
    with pytest.raises(auth.AppApiRejected):
        auth.require_appapi(request, env=exapp_env())  # type: ignore[arg-type]


# --- the four outgoing headers ---------------------------------------------------


def test_appapi_auth_headers_are_exactly_four() -> None:
    headers = appapi_auth_headers(
        USER,
        app_id=APP_ID,
        app_version=APP_VERSION,
        aa_version=AA_VERSION,
        app_secret=APP_SECRET,
    )
    assert set(headers) == {
        "AA-VERSION",
        "EX-APP-ID",
        "EX-APP-VERSION",
        "AUTHORIZATION-APP-API",
    }
    assert headers["AUTHORIZATION-APP-API"] == token()
    assert headers["EX-APP-ID"] == APP_ID


def test_appapi_auth_headers_return_a_fresh_dict_per_call() -> None:
    """Header dicts are mutated by callers (httpx merges them), so sharing one would
    leak the mutation into the next request."""
    first = appapi_auth_headers(
        USER, app_id=APP_ID, app_version=APP_VERSION, aa_version=AA_VERSION, app_secret=APP_SECRET
    )
    second = appapi_auth_headers(
        USER, app_id=APP_ID, app_version=APP_VERSION, aa_version=AA_VERSION, app_secret=APP_SECRET
    )
    assert first == second
    assert first is not second
    first["EX-APP-ID"] = "mutated"
    assert second["EX-APP-ID"] == APP_ID


def test_the_app_context_gets_an_empty_user_in_the_token() -> None:
    headers = appapi_auth_headers(
        "", app_id=APP_ID, app_version=APP_VERSION, aa_version=AA_VERSION, app_secret=APP_SECRET
    )
    decoded = base64.b64decode(headers["AUTHORIZATION-APP-API"]).decode()
    assert decoded == f":{APP_SECRET}"
