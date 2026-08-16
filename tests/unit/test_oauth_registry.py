"""The three admin switches of AUTH-07 and the redirect rule of D-35.

This is the policy half of the enforcement point. It decides nothing about a concrete
client on its own: it reads three environment variables into one immutable object that the
provider asks at every point where a client could get in (registration, authorization,
token issuance, token verification). Pitfall 9 of 03-RESEARCH.md is the reason for that
shape: a check that only runs at registration lets a client that was blocked afterwards
keep working until its token expires.

Every test here is a pure function call. No environment is read, no file is touched, no
Nextcloud is needed.
"""

import inspect
import logging

import pytest

from mcp_connector.oauth import registry, store

CLIENT_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000001"
OTHER_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000002"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"


def policy(**env: str) -> registry.ClientPolicy:
    """A policy from an environment a test writes out in full, never from os.environ."""
    return registry.client_policy(env)


# --- the delivery state --------------------------------------------------------------


def test_without_any_variable_registration_is_on_and_the_allowlist_is_off() -> None:
    """D-35: plug and play is the shipped state, the switches are what an admin adds."""
    result = policy()

    assert result.dcr_enabled is True
    assert result.allowlist_only is False
    assert result.allowed == ()


@pytest.mark.parametrize("blank", ["", " ", "\t", "\n  "])
def test_a_blank_value_counts_as_unset_for_every_switch(blank: str) -> None:
    """An empty value in a compose file is a typo, not an instruction (config.py rule)."""
    result = policy(
        **{
            registry.ENV_DCR: blank,
            registry.ENV_ALLOWLIST_ONLY: blank,
            registry.ENV_ALLOWED_CLIENTS: blank,
        }
    )

    assert result.dcr_enabled is True
    assert result.allowlist_only is False
    assert result.allowed == ()


# --- the boolean switches --------------------------------------------------------------


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", " Off "])
def test_an_explicit_off_value_switches_registration_off(value: str) -> None:
    result = policy(**{registry.ENV_DCR: value})

    assert result.dcr_enabled is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " On "])
def test_an_explicit_on_value_keeps_registration_on(value: str) -> None:
    result = policy(**{registry.ENV_DCR: value})

    assert result.dcr_enabled is True


def test_a_value_that_is_neither_keeps_the_default_and_says_so(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A typo must not decide a security switch silently, in either direction."""
    with caplog.at_level(logging.WARNING):
        result = policy(**{registry.ENV_DCR: "flase"})

    assert result.dcr_enabled is True
    assert registry.ENV_DCR in caplog.text


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_the_allowlist_mode_is_off_until_it_is_switched_on(value: str) -> None:
    assert policy().allowlist_only is False
    assert policy(**{registry.ENV_ALLOWLIST_ONLY: value}).allowlist_only is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "perhaps"])
def test_anything_but_an_on_value_leaves_the_allowlist_mode_off(value: str) -> None:
    assert policy(**{registry.ENV_ALLOWLIST_ONLY: value}).allowlist_only is False


# --- the list ---------------------------------------------------------------------------


def test_the_list_splits_strips_drops_blanks_and_keeps_the_first_of_a_duplicate() -> None:
    raw = f" {CLIENT_ID} , {REDIRECT} ,, {CLIENT_ID} ,  "

    assert policy(**{registry.ENV_ALLOWED_CLIENTS: raw}).allowed == (CLIENT_ID, REDIRECT)


def test_an_entry_may_be_a_client_id_or_a_redirect_uri() -> None:
    """Both spellings of the same permission, because a dynamic client id is random."""
    by_id = policy(**{registry.ENV_ALLOWLIST_ONLY: "1", registry.ENV_ALLOWED_CLIENTS: CLIENT_ID})
    by_uri = policy(**{registry.ENV_ALLOWLIST_ONLY: "1", registry.ENV_ALLOWED_CLIENTS: REDIRECT})

    assert by_id.allows(CLIENT_ID) is True
    assert by_id.allows(OTHER_ID, [REDIRECT]) is False
    assert by_uri.allows(OTHER_ID, [REDIRECT]) is True
    assert by_uri.allows(OTHER_ID, ["https://elsewhere.example/callback"]) is False


def test_the_allowlist_mode_with_an_empty_list_refuses_everything() -> None:
    """Fail closed: an admin who switched the mode on and forgot the list meant to close."""
    result = policy(**{registry.ENV_ALLOWLIST_ONLY: "1"})

    assert result.allows(CLIENT_ID) is False
    assert result.allows(OTHER_ID, [REDIRECT]) is False


def test_without_the_allowlist_mode_every_client_passes_the_policy() -> None:
    result = policy(**{registry.ENV_ALLOWED_CLIENTS: CLIENT_ID})

    assert result.allows(OTHER_ID, [REDIRECT]) is True


def test_being_listed_is_asked_separately_from_being_allowed() -> None:
    """The consent screen needs the first question, the enforcement point the second.

    A client that registered itself and is on no list is shown as unverified even while
    the allowlist mode is off, which is the shipped state (03-UI-SPEC.md, S3).
    """
    result = policy(**{registry.ENV_ALLOWED_CLIENTS: CLIENT_ID})

    assert result.listed(CLIENT_ID) is True
    assert result.listed(OTHER_ID, [REDIRECT]) is False
    assert result.allows(OTHER_ID, [REDIRECT]) is True


# --- the redirect rule (D-35) -----------------------------------------------------------


@pytest.mark.parametrize(
    "uri",
    [
        "https://claude.ai/api/mcp/auth_callback",
        # Minted per connector rather than fixed, measured on the staging instance
        # (docs/oauth-setup.md, "What the hosted connectors actually send").
        "https://chatgpt.com/connector/oauth/GxdvJstdJeOS",
        "https://cloud.example.com/path?query=1",
        "http://127.0.0.1:41234/callback",
        "http://localhost:8080/oauth",
        "http://[::1]:5000/cb",
    ],
)
def test_https_and_loopback_http_are_accepted(uri: str) -> None:
    assert registry.redirect_uri_allowed(uri) is True


@pytest.mark.parametrize(
    "uri",
    [
        "http://claude.ai/api/mcp/auth_callback",
        "http://192.168.1.10/callback",
        "http://127.0.0.1.evil.example/callback",
        "https://user:secret@claude.ai/callback",
        "https://claude.ai/callback#fragment",
        "myapp://callback",
        "javascript:alert(1)",
        "data:text/html,hi",
        "https:///callback",
        "not a url",
        "",
    ],
)
def test_everything_else_is_refused(uri: str) -> None:
    """The spec exception is loopback for native clients, and nothing else (D-35)."""
    assert registry.redirect_uri_allowed(uri) is False


# --- the object itself -------------------------------------------------------------------


def test_the_policy_is_immutable() -> None:
    result = policy()

    with pytest.raises(Exception):  # noqa: B017, PT011 - frozen dataclass, any refusal counts
        result.dcr_enabled = False  # type: ignore[misc]


def test_the_repr_counts_the_entries_instead_of_printing_them() -> None:
    """The list is customer data: which apps an institution connects is not log material."""
    result = policy(**{registry.ENV_ALLOWED_CLIENTS: f"{CLIENT_ID},{REDIRECT}"})

    text = repr(result)

    assert CLIENT_ID not in text
    assert REDIRECT not in text
    assert "2" in text


def test_the_expiry_windows_are_the_ones_the_store_sweeps_with() -> None:
    """One number per rule, in one place: 03-07 must not invent a second 24 hours."""
    assert registry.UNUSED_REGISTRATION_TTL == store.UNUSED_CLIENT_TTL == 24 * 3600
    assert registry.IDLE_REGISTRATION_TTL == store.IDLE_CLIENT_TTL == 90 * 24 * 3600


def test_the_variable_names_live_in_the_constant_block_and_nowhere_else() -> None:
    """The rule of config.py: a name is a module constant, never a literal at a use site."""
    source = inspect.getsource(registry)
    body = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith(("#", "*"))
    )

    assert body.count('"NC_MCP_OAUTH') == 3
