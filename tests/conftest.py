"""Shared test fixtures.

This module deliberately imports nothing from ``mcp_connector``: the contract tests
are red until the server layer exists, and a package import here would break
collection for the whole suite instead of only the red test file.
"""

import os

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run ``@pytest.mark.anyio`` tests on asyncio only (SDK documentation pattern)."""
    return "asyncio"


@pytest.fixture
def nc_env() -> dict[str, str]:
    """Fake Nextcloud connection values for unit tests. Plain strings on purpose."""
    return {
        "base_url": "http://nc.test",
        "user": "alice",
        "secret": "app-password-test",
    }


@pytest.fixture
def live_env() -> dict[str, str | None]:
    """Connection values of a real test Nextcloud, read from the environment."""
    return {
        "base_url": os.environ.get("NC_MCP_URL"),
        "user": os.environ.get("NC_MCP_USER"),
        "secret": os.environ.get("NC_MCP_APP_PASSWORD"),
    }


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests when no test Nextcloud is configured.

    The Linux Docker engine does not run on the development host, so the default
    suite must stay green without Docker. ``addopts`` already deselects the
    ``integration`` marker; this guard additionally turns an explicit
    ``-m integration`` run without ``NC_MCP_URL`` into skips instead of failures.
    """
    if os.environ.get("NC_MCP_URL"):
        return
    skip_integration = pytest.mark.skip(
        reason="NC_MCP_URL is not set: no test Nextcloud available (Docker engine off)"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
