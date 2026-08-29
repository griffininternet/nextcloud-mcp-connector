"""The three AppAPI lifecycle endpoints, in process and without Nextcloud (EXAPP-01).

Every check builds its own Starlette app from ``lifecycle_routes``, which is the whole
point of the factory: the routes are never registered on the shared MCP server object, so
the stdio server and the standalone HTTP server of phase 1 stay exactly as they were
(D-23). The outgoing progress push is replaced per test, so nothing here opens a socket.

Threats covered: T-02-04 (``/enabled`` as an off switch from the outside), T-02-05
(``/heartbeat`` must never authenticate), T-02-06 (``/heartbeat`` says that it lives and
nothing else) and T-02-07 (``no-store`` against the one hour cache of the PHP proxy).
"""

import base64
import json
import logging

import httpx
import pytest
import respx
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config
from mcp_connector.exapp import lifecycle, occ, settings_form, status
from mcp_connector.exapp.ui import strings

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
USER = "alice"
BASE_URL = "http://nc.test"
PUBLIC_URL = "https://cloud.example.test/exapps/mcp_connector"

ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
    config.ENV_PUBLIC_URL: PUBLIC_URL,
}

SETTINGS_URL = f"{BASE_URL}/ocs/v2.php/apps/app_api/api/v1/ui/settings"
OCC_URL = f"{BASE_URL}{occ.OCC_COMMAND_PATH}"


def appapi_headers(user: str = USER, secret: str = APP_SECRET) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token,
    }


def client() -> TestClient:
    """A fresh app per call: one Starlette instance is one lifespan."""
    return TestClient(Starlette(routes=lifecycle.lifecycle_routes(ENV)))


@pytest.fixture
def pushes(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Record every progress push instead of sending it to a Nextcloud that is not there."""
    recorded: list[int] = []

    async def fake(progress: int = 100, *, env: object = None) -> None:
        recorded.append(progress)

    monkeypatch.setattr(status, "report_init_progress", fake)
    return recorded


@pytest.fixture
def registrations(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Record every settings form registration instead of sending it anywhere."""
    recorded: list[object] = []

    async def fake(*, env: object = None) -> None:
        recorded.append(env)

    monkeypatch.setattr(settings_form, "register_settings_form", fake)
    return recorded


# --- heartbeat -------------------------------------------------------------------


def test_heartbeat_answers_200_without_any_header() -> None:
    """Pitfall 10: non HaRP daemons send no headers, and a 401 here costs ten minutes."""
    with client() as http:
        response = http.get("/heartbeat")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_heartbeat_answers_200_with_valid_headers_too() -> None:
    """AppAPI does send auth headers to the heartbeat of a HaRP daemon. They are ignored."""
    with client() as http:
        response = http.get("/heartbeat", headers=appapi_headers())
    assert response.status_code == 200


def test_heartbeat_answers_200_with_a_wrong_secret() -> None:
    """There is no authentication on this route, so there is nothing to fail."""
    with client() as http:
        response = http.get("/heartbeat", headers=appapi_headers(secret="wrong"))
    assert response.status_code == 200


def test_heartbeat_leaks_no_configuration() -> None:
    """T-02-06: no version, no host name, no mode. Set equality, not a subset check."""
    with client() as http:
        body = http.get("/heartbeat").text
    assert set(json.loads(body)) == {"status"}
    assert APP_ID not in body
    assert "nc.test" not in body


# --- init ------------------------------------------------------------------------


def test_init_without_headers_is_401_without_detail(pushes: list[int]) -> None:
    with client() as http:
        response = http.post("/init")
    assert response.status_code == 401
    assert response.json() == {}
    assert APP_SECRET not in response.text
    assert "www-authenticate" not in {key.lower() for key in response.headers}
    assert pushes == [], "a rejected init never touches Nextcloud"


def test_init_with_a_wrong_secret_is_401(pushes: list[int]) -> None:
    with client() as http:
        response = http.post("/init", headers=appapi_headers(secret="wrong"))
    assert response.status_code == 401
    assert pushes == []


@pytest.mark.parametrize("path", ["/init", "/enabled"])
def test_a_broken_deploy_environment_is_401_not_500(pushes: list[int], path: str) -> None:
    """IN-02: require_appapi reads the environment per call, and exapp_settings raises
    ToolError when a variable is missing. _guard used to let that escape as a 500, which
    the module docstring already claimed could not happen."""
    broken = {key: value for key, value in ENV.items() if key != config.ENV_APP_SECRET}
    with TestClient(Starlette(routes=lifecycle.lifecycle_routes(broken))) as http:
        response = http.request(
            "POST" if path == "/init" else "PUT", path, headers=appapi_headers()
        )

    assert response.status_code == 401
    assert response.json() == {}
    assert response.headers["cache-control"] == "no-store"
    assert pushes == []


def test_init_reports_progress_once_and_answers_200(pushes: list[int]) -> None:
    """Pitfall 3: a 200 without the status push leaves the installation at zero percent."""
    with client() as http:
        response = http.post("/init", headers=appapi_headers())
    assert response.status_code == 200
    assert pushes == [100]


def test_init_answers_200_when_the_progress_push_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 500 from /init aborts the installation; a missed push only costs a log line."""

    async def boom(progress: int = 100, *, env: object = None) -> None:
        raise httpx.ConnectError("nextcloud is not reachable")

    monkeypatch.setattr(status, "report_init_progress", boom)
    with client() as http:
        response = http.post("/init", headers=appapi_headers())
    assert response.status_code == 200


# --- enabled ---------------------------------------------------------------------


@pytest.mark.parametrize("value", ["1", "0"])
def test_enabled_answers_with_an_empty_error_field(registrations: list[object], value: str) -> None:
    """A non empty error field makes AppAPI disable the app again immediately."""
    with client() as http:
        response = http.put(f"/enabled?enabled={value}", headers=appapi_headers())
    assert response.status_code == 200
    assert response.json()["error"] == ""


def test_enabled_without_headers_is_401(registrations: list[object]) -> None:
    with client() as http:
        response = http.put("/enabled?enabled=1")
    assert response.status_code == 401
    assert registrations == [], "a rejected enable never touches Nextcloud"


@pytest.mark.parametrize("query", ["", "?enabled=", "?enabled=2", "?enabled=true"])
def test_enabled_accepts_nothing_but_zero_and_one(registrations: list[object], query: str) -> None:
    with client() as http:
        response = http.put(f"/enabled{query}", headers=appapi_headers())
    assert response.status_code == 400
    assert response.json()["error"]
    assert registrations == [], "an unusable value registers nothing"


# --- the settings entry ----------------------------------------------------------


def test_enabling_the_app_registers_the_settings_form(registrations: list[object]) -> None:
    """The signpost of EXAPP-02: enabling the app puts the entry into Nextcloud settings."""
    with client() as http:
        response = http.put("/enabled?enabled=1", headers=appapi_headers())
    assert response.status_code == 200
    assert registrations == [ENV], "the handler passes its own environment on"


def test_disabling_the_app_registers_and_unregisters_nothing(
    registrations: list[object],
) -> None:
    """AppAPI only hands out the forms of enabled apps, so a disable has nothing to undo."""
    with client() as http:
        response = http.put("/enabled?enabled=0", headers=appapi_headers())
    assert response.status_code == 200
    assert registrations == []


def test_enabled_answers_200_when_the_registration_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pitfall 11: a 500 out of /enabled makes AppAPI disable the app again at once.

    A missing signpost costs discoverability and one log line; a failing enable costs
    the installation.
    """

    async def boom(*, env: object = None) -> None:
        raise httpx.ConnectError("nextcloud is not reachable")

    monkeypatch.setattr(settings_form, "register_settings_form", boom)
    with client() as http:
        response = http.put("/enabled?enabled=1", headers=appapi_headers())
    assert response.status_code == 200
    assert response.json() == {"error": ""}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.anyio
@respx.mock
async def test_the_registered_form_is_the_scheme_of_the_ui_spec() -> None:
    """The schema table of 04-UI-SPEC, asserted key by key on the wire."""
    route = respx.post(SETTINGS_URL).mock(
        return_value=httpx.Response(200, json={"ocs": {"meta": {"status": "ok"}}})
    )

    await settings_form.register_settings_form(env=ENV)

    assert route.called
    scheme = json.loads(route.calls.last.request.content)["formScheme"]
    assert scheme["id"] == "mcp_connector_settings"
    assert scheme["priority"] == 10
    assert scheme["section_type"] == "personal"
    assert scheme["section_id"] == "security"
    assert scheme["title"] == strings.SETTINGS_TITLE
    assert scheme["doc_url"] == f"{PUBLIC_URL}/connections"
    assert "{connections_url}" not in scheme["description"]
    assert f"{PUBLIC_URL}/connections" in scheme["description"]


@pytest.mark.anyio
@respx.mock
async def test_the_registered_form_carries_no_field_at_all() -> None:
    """Pitfall 1: a checkbox here would be a switch the boundary never learns about.

    ``fields`` has to be a list for core validation, and it has to be empty for the
    design: the switch lives on the connections page, where flipping it is a local write
    this app can read on the very next request.
    """
    route = respx.post(SETTINGS_URL).mock(return_value=httpx.Response(200, json={}))

    await settings_form.register_settings_form(env=ENV)

    scheme = json.loads(route.calls.last.request.content)["formScheme"]
    assert scheme["fields"] == []
    assert "checkbox" not in route.calls.last.request.content.decode()


@pytest.mark.anyio
@respx.mock
async def test_the_form_never_carries_an_internal_host_name() -> None:
    """T-04-40: the description and the doc_url are read by a browser, not by us.

    An internal host in either of them is a dead link for every reader and a small leak
    about the deployment on top.
    """
    route = respx.post(SETTINGS_URL).mock(return_value=httpx.Response(200, json={}))

    await settings_form.register_settings_form(env=ENV)

    scheme = json.loads(route.calls.last.request.content)["formScheme"]
    assert scheme["doc_url"].startswith(PUBLIC_URL)
    assert scheme["doc_url"].endswith("/connections")
    assert BASE_URL not in scheme["doc_url"]
    assert BASE_URL not in scheme["description"]


@pytest.mark.anyio
@respx.mock
async def test_the_registration_runs_in_the_app_context() -> None:
    """The four AppAPI headers with an empty user: the app speaks about itself."""
    route = respx.post(SETTINGS_URL).mock(return_value=httpx.Response(200, json={}))

    await settings_form.register_settings_form(env=ENV)

    sent = route.calls.last.request
    expected = base64.b64encode(f":{APP_SECRET}".encode()).decode()
    assert sent.headers["AUTHORIZATION-APP-API"] == expected
    assert sent.headers["EX-APP-ID"] == APP_ID
    assert sent.headers["EX-APP-VERSION"] == APP_VERSION
    assert sent.headers["AA-VERSION"] == "34.0.3"
    assert sent.headers["OCS-APIRequest"] == "true"


@pytest.mark.anyio
@respx.mock
async def test_a_registration_that_cannot_be_delivered_is_one_log_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The same error model as the init progress push: one attempt, no retry, no raise."""
    respx.post(SETTINGS_URL).mock(side_effect=httpx.ConnectError("no route to nextcloud"))

    with caplog.at_level(logging.DEBUG):
        await settings_form.register_settings_form(env=ENV)

    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
@pytest.mark.parametrize("status_code", [400, 401, 500])
async def test_a_refused_registration_is_one_log_line(
    caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """Not raising is only half of it: a silent failure would be a signpost nobody misses."""
    respx.post(SETTINGS_URL).mock(return_value=httpx.Response(status_code, json={}))

    with caplog.at_level(logging.DEBUG):
        await settings_form.register_settings_form(env=ENV)

    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
@pytest.mark.parametrize("outcome", ["ok", "refused", "unreachable"])
async def test_the_app_secret_never_reaches_a_log_record(
    caplog: pytest.LogCaptureFixture, outcome: str
) -> None:
    """T-04-42: the headers carry the secret, so no code path may repeat the request."""
    route = respx.post(SETTINGS_URL)
    if outcome == "unreachable":
        route.mock(side_effect=httpx.ConnectError("no route to nextcloud"))
    else:
        route.mock(return_value=httpx.Response(200 if outcome == "ok" else 500, json={}))

    with caplog.at_level(logging.DEBUG):
        await settings_form.register_settings_form(env=ENV)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert APP_SECRET not in logged
    assert base64.b64encode(f":{APP_SECRET}".encode()).decode() not in logged


# --- the PHP proxy path ----------------------------------------------------------


@pytest.mark.parametrize(("method", "path"), [("post", "/init"), ("put", "/enabled?enabled=0")])
def test_a_request_through_the_php_proxy_is_not_served(
    pushes: list[int], method: str, path: str
) -> None:
    """Pitfall 2 and T-02-04: only the PHP proxy sets x-origin-ip, and it does not protect
    these three paths while attaching valid AppAPI headers itself."""
    headers = appapi_headers()
    headers["x-origin-ip"] = "203.0.113.7"
    with client() as http:
        response = getattr(http, method)(path, headers=headers)
    assert response.status_code == 404
    assert pushes == []


# --- cache control ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "extra"),
    [
        ("get", "/heartbeat", {}),
        ("post", "/init", {}),
        ("post", "/init", {"AUTHORIZATION-APP-API": "broken"}),
        ("put", "/enabled?enabled=1", {}),
        ("put", "/enabled?enabled=2", {}),
        ("put", "/enabled?enabled=0", {"x-origin-ip": "203.0.113.7"}),
    ],
)
def test_every_answer_carries_no_store(
    pushes: list[int], method: str, path: str, extra: dict[str, str]
) -> None:
    """T-02-07: createProxyResponse caches JSON for 3600 s unless Cache-Control is set.

    The success answers, the 400, the 401 and the 404 all carry it, which is why one
    helper builds every response of this module.
    """
    headers = appapi_headers() | extra
    with client() as http:
        response = getattr(http, method)(path, headers=headers)
    assert response.headers["cache-control"] == "no-store"


# --- the two occ commands, and their independence (plan 18-08) -------------------


def sent_names(route: respx.Route) -> list[str]:
    """The command name of every registration that went out, in the order it went."""
    return [json.loads(call.request.content)["name"] for call in route.calls]


@pytest.mark.anyio
@respx.mock
async def test_a_refused_first_command_does_not_cost_the_second(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One ``try`` per command, and this is the case that makes it worth having.

    ``OccCommandController::registerCommand`` takes exactly one command per POST, so two
    commands are two requests. Without the block per command the first refusal would end the
    loop, and an instance whose purge command could not be registered would silently lose the
    check of its audit log as well.
    """
    route = respx.post(OCC_URL).mock(
        side_effect=[httpx.Response(500, json={}), httpx.Response(200, json={})]
    )

    with caplog.at_level(logging.DEBUG):
        await occ.register_occ_commands(env=ENV)

    assert route.call_count == 2
    assert sent_names(route) == [scheme["name"] for scheme in occ.command_schemes()]
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert occ.OCC_COMMAND_NAME in logged, "the failure names the command it happened to"
    assert occ.OCC_AUDIT_COMMAND_NAME not in logged, "the one that worked stays quiet"
    assert APP_SECRET not in logged


@pytest.mark.anyio
@respx.mock
async def test_a_first_command_that_never_arrives_does_not_cost_the_second(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The other half of the same rule: a transport failure is caught per command too."""
    route = respx.post(OCC_URL).mock(
        side_effect=[httpx.ConnectError("no route to nextcloud"), httpx.Response(200, json={})]
    )

    with caplog.at_level(logging.DEBUG):
        await occ.register_occ_commands(env=ENV)

    assert route.call_count == 2
    assert sent_names(route) == [scheme["name"] for scheme in occ.command_schemes()]
    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
async def test_both_commands_failing_is_two_log_lines_and_no_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pitfall 11: a non empty error field out of ``/enabled`` disables the app again."""
    route = respx.post(OCC_URL).mock(return_value=httpx.Response(500, json={}))

    with caplog.at_level(logging.DEBUG):
        await occ.register_occ_commands(env=ENV)

    assert route.call_count == 2
    errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(errors) == 2
    assert any(occ.OCC_COMMAND_NAME in line for line in errors)
    assert any(occ.OCC_AUDIT_COMMAND_NAME in line for line in errors)
