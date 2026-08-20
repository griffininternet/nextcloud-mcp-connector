"""The admin switches of AUTH-07 and the redirect rule of D-35.

This is the policy half of the enforcement point. It decides nothing about a concrete
client on its own: it reads environment variables into one immutable object that the
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
    assert result.cimd_enabled is True


@pytest.mark.parametrize("blank", ["", " ", "\t", "\n  "])
def test_a_blank_value_counts_as_unset_for_every_switch(blank: str) -> None:
    """An empty value in a compose file is a typo, not an instruction (config.py rule)."""
    result = policy(
        **{
            registry.ENV_DCR: blank,
            registry.ENV_ALLOWLIST_ONLY: blank,
            registry.ENV_ALLOWED_CLIENTS: blank,
            registry.ENV_CIMD: blank,
        }
    )

    assert result.dcr_enabled is True
    assert result.allowlist_only is False
    assert result.allowed == ()
    assert result.cimd_enabled is True


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


# --- the fourth switch and its coupling ------------------------------------------------


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", " Off "])
def test_cimd_can_be_switched_off_on_its_own_and_registration_stays_on(value: str) -> None:
    """An instance without outbound access closes the document fetch, not registration."""
    result = policy(**{registry.ENV_CIMD: value})

    assert result.cimd_enabled is False
    assert result.dcr_enabled is True


def test_switching_registration_off_switches_cimd_off_with_it() -> None:
    """A disabled dynamic registration must not be circumventable through CIMD."""
    result = policy(**{registry.ENV_DCR: "off"})

    assert result.dcr_enabled is False
    assert result.cimd_enabled is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_the_coupling_beats_an_explicitly_switched_on_cimd(value: str) -> None:
    """T-06-15: the newer switch is not a way around the older one, in any spelling.

    An administrator who switched registration off meant "no clients that sign themselves
    up", and CIMD is the other spelling of that, not an exception to it.
    """
    result = policy(**{registry.ENV_DCR: "off", registry.ENV_CIMD: value})

    assert result.cimd_enabled is False


def test_a_typo_in_the_cimd_switch_keeps_the_default_and_says_so(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The same reading as the three switches before it: a typo decides nothing."""
    with caplog.at_level(logging.WARNING):
        result = policy(**{registry.ENV_CIMD: "vielleicht"})

    assert result.cimd_enabled is True
    assert registry.ENV_CIMD in caplog.text


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


# --- the loopback port rule (RFC 8252 7.3, CLIENT-05) ------------------------------------

#: What Claude Code publishes in its client id metadata document, fetched on 2026-08-20
#: (06-RESEARCH.md, Pattern 4). Both entries are portless; at runtime the client arrives
#: with ``http://localhost:3118/callback``.
CLAUDE_CODE_URIS = ["http://localhost/callback", "http://127.0.0.1/callback"]


@pytest.mark.parametrize(
    ("requested", "registered", "expected"),
    [
        # The measured case this rule exists for.
        ("http://localhost:3118/callback", CLAUDE_CODE_URIS, "http://localhost/callback"),
        (
            "http://127.0.0.1:54321/callback",
            ["http://127.0.0.1/callback"],
            "http://127.0.0.1/callback",
        ),
        ("http://[::1]:9000/cb", ["http://[::1]/cb"], "http://[::1]/cb"),
        # A registration that already carries a port is matched with another one, which is
        # the ephemeral case: the client kept its published path and took a free port.
        (
            "http://localhost:41234/callback",
            ["http://localhost:8787/callback"],
            "http://localhost:8787/callback",
        ),
        # Same path and query, and the query is part of the exact half.
        (
            "http://127.0.0.1:7000/cb?state=keep",
            ["http://127.0.0.1/cb?state=keep"],
            "http://127.0.0.1/cb?state=keep",
        ),
        # The first entry that matches is the answer, and the other host is not touched.
        (
            "http://127.0.0.1:3118/callback",
            CLAUDE_CODE_URIS,
            "http://127.0.0.1/callback",
        ),
    ],
)
def test_a_loopback_request_matches_its_registration_with_another_port(
    requested: str, registered: list[str], expected: str
) -> None:
    """RFC 8252 7.3 is a MUST: the port is the one property the client cannot control."""
    assert registry.loopback_match(requested, registered) == expected


@pytest.mark.parametrize(
    ("requested", "registered"),
    [
        # A host change is not a port change (RFC 8252 8.3: the name and the literal do not
        # resolve through the same mechanism).
        ("http://localhost:3118/callback", ["http://127.0.0.1/callback"]),
        ("http://127.0.0.1:3118/callback", ["http://localhost/callback"]),
        ("http://[::1]:3118/callback", ["http://127.0.0.1/callback"]),
        # Path exactly.
        ("http://localhost:3118/other", ["http://localhost/callback"]),
        ("http://localhost:3118/callback/sub", ["http://localhost/callback"]),
        # Query exactly.
        ("http://localhost:3118/callback?x=1", ["http://localhost/callback"]),
        ("http://localhost:3118/callback", ["http://localhost/callback?x=1"]),
        # Scheme exactly.
        ("https://localhost:3118/callback", ["http://localhost/callback"]),
        # Not loopback, so not this function's business: the exact comparison of the SDK
        # stands and a hosted connector gains nothing here.
        ("https://claude.ai/cb", ["https://claude.ai/cb"]),
        ("http://127.0.0.1.evil.example:80/cb", ["http://127.0.0.1/cb"]),
        # A fragment or user info is a refusal, on either side of the comparison.
        ("http://localhost:3118/callback#frag", CLAUDE_CODE_URIS),
        ("http://user:secret@localhost:3118/callback", CLAUDE_CODE_URIS),
        ("http://localhost:3118/callback", ["http://user:secret@localhost/callback"]),
        ("http://localhost:3118/callback", ["http://localhost/callback#frag"]),
        # An address this library cannot take apart, and a port outside the range.
        ("http://localhost:99999/cb", ["http://localhost/cb"]),
        ("http://localhost:0/cb", ["http://localhost/cb"]),
        ("http://localhost:notaport/cb", ["http://localhost/cb"]),
        ("not a url", CLAUDE_CODE_URIS),
        ("", []),
        # Nothing registered, and an entry that is not an address.
        ("http://localhost:3118/callback", []),
        ("http://localhost:3118/callback", ["", "myapp://callback"]),
    ],
)
def test_everything_but_the_port_is_compared_exactly(requested: str, registered: list[str]) -> None:
    """The one relaxation is the port, and a refusal never says which half fell."""
    assert registry.loopback_match(requested, registered) is None


def test_the_match_returns_the_registration_and_writes_nothing() -> None:
    """The anti pattern is to register the requested address on a match (T-06-19)."""
    registered = list(CLAUDE_CODE_URIS)

    result = registry.loopback_match("http://localhost:3118/callback", registered)

    assert result == "http://localhost/callback"
    assert registered == CLAUDE_CODE_URIS


# --- the object itself -------------------------------------------------------------------


def test_the_policy_is_immutable() -> None:
    result = policy()

    with pytest.raises(Exception):  # noqa: B017, PT011 - frozen dataclass, any refusal counts
        result.dcr_enabled = False  # type: ignore[misc]


def test_the_derived_field_is_immutable_too() -> None:
    """A policy a request handler could reopen is one bug away from being reopened."""
    result = policy(**{registry.ENV_DCR: "off"})

    with pytest.raises(Exception):  # noqa: B017, PT011 - frozen dataclass, any refusal counts
        result.cimd_enabled = True  # type: ignore[misc]
    assert result.cimd_enabled is False


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

    assert body.count('"NC_MCP_OAUTH') == 4


def test_the_public_names_are_exported_and_sorted() -> None:
    """``__all__`` is what vulture reads and what a reader scans, so it stays ordered.

    The order is the one ruff's RUF022 enforces on this repository: the constants first,
    then the class, then the functions, alphabetically within each group. Asserting a plain
    ``sorted()`` would demand the opposite of what the formatter writes, so the assertion
    is made per group.
    """
    assert "ENV_CIMD" in registry.__all__
    constants = [name for name in registry.__all__ if name.isupper()]
    others = [name for name in registry.__all__ if not name.isupper()]
    assert constants == sorted(constants)
    assert others == sorted(others)
    assert list(registry.__all__) == constants + others
