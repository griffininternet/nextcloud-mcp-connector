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

import httpx
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config
from mcp_connector.exapp import lifecycle, status

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
USER = "alice"

ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}


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
def test_enabled_answers_with_an_empty_error_field(value: str) -> None:
    """A non empty error field makes AppAPI disable the app again immediately."""
    with client() as http:
        response = http.put(f"/enabled?enabled={value}", headers=appapi_headers())
    assert response.status_code == 200
    assert response.json()["error"] == ""


def test_enabled_without_headers_is_401() -> None:
    with client() as http:
        response = http.put("/enabled?enabled=1")
    assert response.status_code == 401


@pytest.mark.parametrize("query", ["", "?enabled=", "?enabled=2", "?enabled=true"])
def test_enabled_accepts_nothing_but_zero_and_one(query: str) -> None:
    with client() as http:
        response = http.put(f"/enabled{query}", headers=appapi_headers())
    assert response.status_code == 400
    assert response.json()["error"]


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
