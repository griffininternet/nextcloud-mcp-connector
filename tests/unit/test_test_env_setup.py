"""Guards for the local test Nextcloud (compose.test.yml plus bootstrap script).

These checks are pure file assertions, so the default suite keeps running without Docker.
They pin the three mistakes that would cost the most time later: a CRLF in the shell
script (docker compose exec then fails on the CR), a missing dav:create-calendar (a user
created by occ has no calendar at all) and a committed .env.test with real app passwords.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.test.yml"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_test_nc.sh"
ENV_EXAMPLE = ROOT / ".env.test.example"
GITIGNORE = ROOT / ".gitignore"

ENV_VARS = (
    "NC_MCP_URL",
    "NC_MCP_USER",
    "NC_MCP_APP_PASSWORD",
    "NC_MCP_TEST_USER2",
    "NC_MCP_TEST_APP_PASSWORD2",
)


@pytest.mark.parametrize("path", [COMPOSE, BOOTSTRAP, ENV_EXAMPLE])
def test_the_test_environment_is_checked_in(path: Path) -> None:
    assert path.is_file(), f"{path.name} is missing"


@pytest.mark.parametrize("path", [COMPOSE, BOOTSTRAP])
def test_no_crlf_in_files_the_container_reads(path: Path) -> None:
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; docker compose exec fails on the CR"
    )


def test_compose_pins_the_nextcloud_image_and_a_healthcheck() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "nextcloud:34-apache" in text
    assert "SQLITE_DATABASE" in text, "no second database container for the test instance"
    assert "healthcheck" in text, "docker compose up --wait needs a healthcheck"


def test_compose_binds_the_test_instance_to_loopback_only() -> None:
    """WR-06: throwaway credentials are only defensible while nothing but localhost can
    reach the instance; a bare host port would publish it on every interface."""
    text = COMPOSE.read_text(encoding="utf-8")
    assert '"127.0.0.1:${NC_TEST_PORT:-8080}:80"' in text
    assert '"${NC_TEST_PORT:-8080}:80"' not in text.replace("127.0.0.1:${NC_TEST_PORT:-8080}", "")


def test_bootstrap_creates_calendar_addressbook_and_kills_the_bruteforce_guard() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "dav:create-calendar" in text
    assert "dav:create-addressbook" in text
    assert "auth.bruteforce.protection.enabled" in text
    assert "auth-tokens:add" in text
    assert "set -euo pipefail" in text


def test_env_example_documents_every_variable() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for name in ENV_VARS:
        assert f"{name}=" in text, f"{name} is missing from .env.test.example"


def test_env_example_holds_no_real_app_password() -> None:
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.startswith(("NC_MCP_APP_PASSWORD=", "NC_MCP_TEST_APP_PASSWORD2=")):
            assert set(line.split("=", 1)[1]) <= set("x-"), "placeholders only, never a token"


def test_real_env_test_stays_out_of_git() -> None:
    patterns = GITIGNORE.read_text(encoding="utf-8").split()
    assert ".env.test" in patterns, "the generated .env.test carries two app passwords"
