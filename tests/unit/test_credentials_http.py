"""Unit tests for the credential object, the HTTP pool and logging hardening.

Threats covered here: T-01-07 (credentials in logs and tracebacks) and the header leak
that ``follow_redirects=True`` would cause.
"""

import asyncio
import logging
import sys
from dataclasses import FrozenInstanceError

import httpx
import pytest

from mcp_connector import config, deps
from mcp_connector.errors import ToolError
from mcp_connector.nextcloud import http as nc_http
from mcp_connector.nextcloud.credentials import Credentials

SECRET = "s3cret"


def test_repr_masks_the_secret() -> None:
    creds = Credentials("http://nc.test", "alice", SECRET)
    text = repr(creds)
    assert "***" in text
    assert SECRET not in text
    assert "alice" in text


def test_str_and_format_do_not_leak_the_secret() -> None:
    creds = Credentials("http://nc.test", "alice", SECRET)
    assert SECRET not in str(creds)
    assert SECRET not in f"{creds}"
    assert SECRET not in f"{creds!r}"


def test_secret_stays_readable_for_the_http_layer() -> None:
    creds = Credentials("http://nc.test", "alice", SECRET)
    assert creds.secret == SECRET


def test_credentials_are_immutable() -> None:
    creds = Credentials("http://nc.test", "alice", SECRET)
    with pytest.raises(FrozenInstanceError):
        creds.secret = "other"  # type: ignore[misc]


@pytest.mark.anyio
async def test_shared_client_is_reused_within_one_event_loop() -> None:
    first = nc_http.shared_client()
    second = nc_http.shared_client()
    assert first is second


@pytest.mark.anyio
async def test_shared_client_is_hardened() -> None:
    client = nc_http.shared_client()
    assert client.follow_redirects is False, "a redirect would leak or drop the auth header"
    assert client.timeout.connect == 5.0
    assert client.timeout.read == 30.0
    assert client.headers["user-agent"].startswith("nextcloud-mcp-connector/")
    assert "authorization" not in client.headers, "auth is passed per request, never on the client"


@pytest.mark.anyio
async def test_shared_client_is_replaced_after_close() -> None:
    first = nc_http.shared_client()
    await first.aclose()
    second = nc_http.shared_client()
    assert second is not first
    assert second.is_closed is False


def test_each_event_loop_gets_its_own_client() -> None:
    async def grab() -> httpx.AsyncClient:
        return nc_http.shared_client()

    one = asyncio.run(grab())
    two = asyncio.run(grab())
    assert one is not two


def test_configure_logging_silences_httpx_and_writes_to_stderr() -> None:
    package_logger = logging.getLogger("mcp_connector")
    for handler in list(package_logger.handlers):
        package_logger.removeHandler(handler)

    nc_http.configure_logging()
    nc_http.configure_logging()  # idempotent: no duplicate handlers

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING

    handlers = package_logger.handlers
    assert len(handlers) == 1, "configure_logging must not stack handlers"
    stream = getattr(handlers[0], "stream", None)
    assert stream is sys.stderr, "stdout is the wire in stdio mode"
    assert package_logger.propagate is False, "records must not reach a root stdout handler"


def test_resolve_credentials_uses_the_environment(
    monkeypatch: pytest.MonkeyPatch, nc_env: dict[str, str]
) -> None:
    monkeypatch.setenv(config.ENV_URL, nc_env["base_url"] + "/")
    monkeypatch.setenv(config.ENV_USER, nc_env["user"])
    monkeypatch.setenv(config.ENV_APP_PASSWORD, nc_env["secret"])

    creds = deps.resolve_credentials(None)
    assert creds.base_url == nc_env["base_url"]
    assert creds.user == nc_env["user"]


def test_resolve_credentials_fails_loudly_without_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (config.ENV_URL, config.ENV_USER, config.ENV_APP_PASSWORD):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ToolError) as excinfo:
        deps.resolve_credentials(None)
    assert config.ENV_URL in excinfo.value.message


def test_no_tool_parameter_can_set_the_user() -> None:
    """Confused deputy guard: identity comes from the auth channel only."""
    import inspect

    params = list(inspect.signature(deps.resolve_credentials).parameters)
    assert params == ["ctx"], "resolve_credentials must not accept a user override"
