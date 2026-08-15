"""The ExApp entry point and the boundary against the two phase 1 modes (D-23, D-27).

Nothing here starts a server: ``build_exapp_app`` is a pure function of its environment,
and every ``main`` case below exits before uvicorn is reached. The regression that matters
most is the last one in this file: the standalone HTTP application of phase 1 must not
grow a lifecycle route just because the ExApp module exists.
"""

import pytest

from mcp_connector import config, entry_exapp, entry_http

EXAPP_ENV = {
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: "app-secret-test",
    config.ENV_APP_VERSION: "0.1.0",
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}
LIFECYCLE_PATHS = {"/heartbeat", "/init", "/enabled"}


def paths(app: object) -> set[str]:
    return {getattr(route, "path", "") for route in app.router.routes}  # type: ignore[attr-defined]


# --- the application -------------------------------------------------------------


def test_the_exapp_app_carries_the_three_lifecycle_routes() -> None:
    assert paths(entry_exapp.build_exapp_app(EXAPP_ENV)) >= LIFECYCLE_PATHS


def test_the_standalone_http_app_has_no_lifecycle_route() -> None:
    """D-23: phase 1 stays exactly as it was, whoever imported the ExApp package."""
    assert not LIFECYCLE_PATHS & paths(entry_http.build_app({}))


def test_the_exapp_app_still_serves_mcp() -> None:
    assert "/mcp" in paths(entry_exapp.build_exapp_app(EXAPP_ENV))


# --- the startup validation ------------------------------------------------------


@pytest.mark.parametrize("conflicting", [config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD])
def test_a_second_credential_channel_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, conflicting: str
) -> None:
    """T-02-08: an ExApp process with a second way to authenticate is a misconfiguration."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(config.ENV_STATIC_BEARER, raising=False)
    monkeypatch.delenv(config.ENV_APP_PASSWORD, raising=False)
    monkeypatch.setenv(conflicting, "something")

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


def test_a_missing_deploy_variable_stops_the_start(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*EXAPP_ENV, config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(config.ENV_APP_ID, "mcp_connector")

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2


@pytest.mark.parametrize("port", [None, "", "not-a-number"])
def test_a_missing_or_broken_port_stops_the_start(
    monkeypatch: pytest.MonkeyPatch, port: str | None
) -> None:
    """A ValueError traceback out of int() would tell an administrator nothing."""
    for name, value in EXAPP_ENV.items():
        monkeypatch.setenv(name, value)
    for name in (config.ENV_STATIC_BEARER, config.ENV_APP_PASSWORD, config.ENV_HP_SHARED_KEY):
        monkeypatch.delenv(name, raising=False)
    if port is None:
        monkeypatch.delenv(config.ENV_APP_PORT, raising=False)
    else:
        monkeypatch.setenv(config.ENV_APP_PORT, port)

    with pytest.raises(SystemExit) as excinfo:
        entry_exapp.main()
    assert excinfo.value.code == 2
