"""Unit tests for environment parsing (D-11).

A missing variable must name itself in the error text: the developer reads that message
in a client log where nothing else explains what went wrong.
"""

import logging
from pathlib import Path

import pytest

from mcp_connector import config
from mcp_connector.errors import ToolError

REPO_ROOT = Path(__file__).resolve().parents[2]


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


@pytest.mark.parametrize(
    "raw",
    [
        "https://admin:hunter2@cloud.test",
        "https://admin@cloud.test",
        "http://:hunter2@cloud.test/nextcloud",
    ],
    ids=["user and password", "user only", "password only"],
)
def test_credentials_in_the_base_url_are_rejected_without_repeating_them(raw: str) -> None:
    """IN-04: the value passed the scheme and netloc checks and landed in
    settings.base_url, which exapp/status.py writes into two logger.error lines in full."""
    with pytest.raises(ToolError) as excinfo:
        config.normalize_base_url(raw)

    assert "credentials" in excinfo.value.message
    assert "hunter2" not in excinfo.value.message
    assert "hunter2" not in excinfo.value.hint


def test_redirect_hint_is_available_for_client_errors() -> None:
    """The 3xx path in the client layer reuses one wording, defined here."""
    assert "redirect" in config.REDIRECT_HINT.lower()


def test_http_mode_variable_names_are_declared_but_unused() -> None:
    """Plan 04 evaluates these; plan 02 only reserves the names (no silent defaults)."""
    assert config.ENV_ALLOWED_HOSTS == "NC_MCP_ALLOWED_HOSTS"
    assert config.ENV_STATIC_BEARER == "NC_MCP_STATIC_BEARER"


# --- the ExApp mode (EXAPP-01) ----------------------------------------------------

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"


def _exapp_env() -> dict[str, str]:
    return {
        config.ENV_APP_ID: APP_ID,
        config.ENV_APP_SECRET: APP_SECRET,
        config.ENV_APP_VERSION: APP_VERSION,
        config.ENV_AA_VERSION: "34.0.3",
        config.ENV_NEXTCLOUD_URL: "http://nc.test/",
    }


def test_appapi_variable_names_keep_the_names_appapi_dictates() -> None:
    """These four carry no NC_MCP_ prefix on purpose: the deploy daemon sets them."""
    assert config.ENV_APP_ID == "APP_ID"
    assert config.ENV_APP_SECRET == "APP_SECRET"
    assert config.ENV_APP_VERSION == "APP_VERSION"
    assert config.ENV_NEXTCLOUD_URL == "NEXTCLOUD_URL"


def test_exapp_configured_needs_both_id_and_secret() -> None:
    assert config.exapp_configured(_exapp_env()) is True
    assert config.exapp_configured({config.ENV_APP_ID: APP_ID}) is False
    assert config.exapp_configured({config.ENV_APP_SECRET: APP_SECRET}) is False
    assert config.exapp_configured({}) is False


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_appapi_variable_is_treated_as_unset(blank: str) -> None:
    env = _exapp_env()
    env[config.ENV_APP_SECRET] = blank
    assert config.exapp_configured(env) is False


def test_exapp_settings_reads_the_deploy_environment() -> None:
    settings = config.exapp_settings(_exapp_env())
    assert settings.app_id == APP_ID
    assert settings.app_secret == APP_SECRET
    assert settings.app_version == APP_VERSION
    assert settings.aa_version == "34.0.3"
    assert settings.base_url == "http://nc.test", "the trailing slash is normalised away"


def test_exapp_settings_falls_back_to_the_phase_one_url_variable() -> None:
    env = _exapp_env()
    del env[config.ENV_NEXTCLOUD_URL]
    env[config.ENV_URL] = "https://cloud.test/nextcloud/"
    assert config.exapp_settings(env).base_url == "https://cloud.test/nextcloud"


def test_exapp_settings_treats_a_missing_aa_version_as_empty() -> None:
    """HaRP writes a placeholder into AA-VERSION anyway, so it is never required."""
    env = _exapp_env()
    del env[config.ENV_AA_VERSION]
    assert config.exapp_settings(env).aa_version == ""


@pytest.mark.parametrize("missing", ["APP_ID", "APP_SECRET", "APP_VERSION", "NEXTCLOUD_URL"])
def test_a_missing_appapi_variable_names_itself(missing: str) -> None:
    env = _exapp_env()
    del env[missing]
    with pytest.raises(ToolError) as excinfo:
        config.exapp_settings(env)
    assert missing in excinfo.value.message
    assert excinfo.value.hint


def test_the_settings_repr_masks_the_app_secret() -> None:
    """T-02-03: the secret must not show up in a traceback or a container repr."""
    settings = config.exapp_settings(_exapp_env())
    assert APP_SECRET not in repr(settings)
    assert "***" in repr(settings)


# --- the persistent volume of the token store (AUTH-03, pitfall 12) ---------------


def test_the_store_directory_is_the_volume_appapi_mounted(tmp_path: Path) -> None:
    env = {**_exapp_env(), config.ENV_APP_PERSISTENT_STORAGE: str(tmp_path)}
    assert config.persistent_storage(env) == tmp_path


@pytest.mark.parametrize("value", [None, "", "   "])
def test_a_missing_volume_names_the_variable_in_the_exapp_mode(value: str | None) -> None:
    """T-03-15: without it every authorization dies at the next container restart."""
    env = _exapp_env()
    if value is not None:
        env[config.ENV_APP_PERSISTENT_STORAGE] = value

    with pytest.raises(ToolError) as excinfo:
        config.persistent_storage(env)
    assert config.ENV_APP_PERSISTENT_STORAGE in excinfo.value.message
    assert excinfo.value.hint


def test_a_volume_that_does_not_exist_is_never_created_silently(tmp_path: Path) -> None:
    """A missing mount point is a deployment error, not a directory we may invent."""
    missing = tmp_path / "not-mounted"
    env = {**_exapp_env(), config.ENV_APP_PERSISTENT_STORAGE: str(missing)}

    with pytest.raises(ToolError) as excinfo:
        config.persistent_storage(env)
    assert config.ENV_APP_PERSISTENT_STORAGE in excinfo.value.message
    assert not missing.exists()


def test_a_volume_that_is_a_file_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "oauth"
    target.write_text("not a directory", encoding="utf-8")
    env = {**_exapp_env(), config.ENV_APP_PERSISTENT_STORAGE: str(target)}

    with pytest.raises(ToolError) as excinfo:
        config.persistent_storage(env)
    assert config.ENV_APP_PERSISTENT_STORAGE in excinfo.value.message


def test_a_volume_that_cannot_be_written_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read only mount answers every question right until the first write."""
    monkeypatch.setattr(config, "_probe_writable", lambda path: False)
    env = {**_exapp_env(), config.ENV_APP_PERSISTENT_STORAGE: str(tmp_path)}

    with pytest.raises(ToolError) as excinfo:
        config.persistent_storage(env)
    assert config.ENV_APP_PERSISTENT_STORAGE in excinfo.value.message
    assert excinfo.value.hint


def test_the_probe_really_writes_and_leaves_nothing_behind(tmp_path: Path) -> None:
    """os.access lies on Windows and inside containers, so the check writes a file."""
    assert config._probe_writable(tmp_path) is True
    assert list(tmp_path.iterdir()) == []
    assert config._probe_writable(tmp_path / "missing") is False


def test_outside_the_exapp_mode_the_store_falls_back_into_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The --manual development mode has no volume; the fallback is named, not silent."""
    monkeypatch.chdir(tmp_path)
    with caplog.at_level(logging.WARNING, logger="mcp_connector.config"):
        path = config.persistent_storage({})

    assert path == tmp_path / config.DEV_STORAGE_DIR
    assert path.is_dir()
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert config.DEV_STORAGE_DIR in messages
    assert config.ENV_APP_PERSISTENT_STORAGE in messages


def test_the_development_fallback_directory_is_git_ignored() -> None:
    """A store full of encrypted app passwords must never become a commit."""
    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert f"{config.DEV_STORAGE_DIR}/" in [line.strip() for line in ignored]
