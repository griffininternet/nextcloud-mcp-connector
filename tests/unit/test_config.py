"""Unit tests for environment parsing (D-11).

A missing variable must name itself in the error text: the developer reads that message
in a client log where nothing else explains what went wrong.
"""

import pytest

from mcp_connector import config
from mcp_connector.errors import ToolError


def _env(nc_env: dict[str, str]) -> dict[str, str]:
    return {
        config.ENV_URL: nc_env["base_url"],
        config.ENV_USER: nc_env["user"],
        config.ENV_APP_PASSWORD: nc_env["secret"],
    }


def test_loads_credentials_from_env(nc_env: dict[str, str]) -> None:
    creds = config.load_stdio_credentials(_env(nc_env))
    assert creds.base_url == "http://nc.test"
    assert creds.user == "alice"
    assert creds.secret == "app-password-test"


@pytest.mark.parametrize(
    "missing",
    ["NC_MCP_URL", "NC_MCP_USER", "NC_MCP_APP_PASSWORD"],
)
def test_missing_variable_names_itself(nc_env: dict[str, str], missing: str) -> None:
    env = _env(nc_env)
    del env[missing]
    with pytest.raises(ToolError) as excinfo:
        config.load_stdio_credentials(env)
    assert missing in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.parametrize(
    "blank",
    ["", "   "],
)
def test_blank_variable_is_treated_as_missing(nc_env: dict[str, str], blank: str) -> None:
    env = _env(nc_env)
    env[config.ENV_APP_PASSWORD] = blank
    with pytest.raises(ToolError) as excinfo:
        config.load_stdio_credentials(env)
    assert config.ENV_APP_PASSWORD in excinfo.value.message


def test_trailing_slash_is_removed_and_subpath_is_kept() -> None:
    assert config.normalize_base_url("https://cloud.test/") == "https://cloud.test"
    assert config.normalize_base_url("https://cloud.test///") == "https://cloud.test"
    assert (
        config.normalize_base_url("https://host.test/nextcloud/") == "https://host.test/nextcloud"
    )
    assert config.normalize_base_url("  https://host.test/nc  ") == "https://host.test/nc"


@pytest.mark.parametrize(
    "raw",
    ["cloud.test", "ftp://cloud.test", "file:///etc/passwd", "", "   ", "https://"],
)
def test_invalid_base_url_is_rejected(raw: str) -> None:
    with pytest.raises(ToolError) as excinfo:
        config.normalize_base_url(raw)
    assert excinfo.value.hint


def test_redirect_hint_is_available_for_client_errors() -> None:
    """The 3xx path in the client layer reuses one wording, defined here."""
    assert "redirect" in config.REDIRECT_HINT.lower()


def test_http_mode_variable_names_are_declared_but_unused() -> None:
    """Plan 04 evaluates these; plan 02 only reserves the names (no silent defaults)."""
    assert config.ENV_ALLOWED_HOSTS == "NC_MCP_ALLOWED_HOSTS"
    assert config.ENV_STATIC_BEARER == "NC_MCP_STATIC_BEARER"
