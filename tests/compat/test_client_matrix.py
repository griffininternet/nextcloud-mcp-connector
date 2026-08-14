"""Client matrix and restart proof against one real HTTP endpoint (SRV-01, SRV-05, D-19).

Three questions are answered here, all without Docker and without Nextcloud:

1. Does a modern client (mcp 2.x) get served on ``/mcp``?
2. Does a legacy client (mcp 1.29, its own environment) get served on the same ``/mcp``?
3. Does a conversation survive a server restart, because there is no session state?

Question 2 is the regression test for the failure class of nextcloud/context_agent#227:
a server that throws legacy sessions away answers "Session terminated" right after
initialize. Question 3 is the honest version of "stateless": not a claim in a document,
but a client that keeps working after the process it talked to was killed.

The server runs as a real subprocess with uvicorn, because in-process test clients cannot
prove any of this: they share the interpreter that would have to die for question 3.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.matrix

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPAT_DIR = Path(__file__).resolve().parent
MODERN_CHECK = COMPAT_DIR / "modern_client_check.py"
LEGACY_CHECK = COMPAT_DIR / "legacy_client_check.py"
LEGACY_SPEC = "mcp>=1.29,<2"

SERVER_ENV = {
    "NC_MCP_URL": "http://nc.invalid",
    "NC_MCP_USER": "matrix-dummy-user",
    "NC_MCP_APP_PASSWORD": "matrix-dummy-app-password",
    "NC_MCP_ALLOWED_HOSTS": "127.0.0.1",
}

# Signals that the isolated legacy environment could not be resolved from the network.
OFFLINE_MARKERS = (
    "failed to fetch",
    "error sending request",
    "network",
    "temporary failure in name resolution",
    "no such host",
    "connection refused",
    "proxy",
)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class Server:
    """A uvicorn subprocess serving ``mcp_connector.entry_http:app``."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.process: subprocess.Popen[str] | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/mcp"

    @property
    def health_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/health"

    def start(self) -> None:
        env = {**os.environ, **SERVER_ENV}
        self.process = subprocess.Popen(  # noqa: S603 - fixed command from our own package
            [
                sys.executable,
                "-m",
                "uvicorn",
                "mcp_connector.entry_http:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        self.wait_until_healthy()

    def wait_until_healthy(self, timeout: float = 60.0) -> dict[str, str]:
        deadline = time.monotonic() + timeout
        last_error = "no attempt made"
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                pytest.fail(f"uvicorn exited early: {self.read_output()[:2000]}")
            try:
                response = httpx.get(self.health_url, timeout=2.0)
                if response.status_code == 200:
                    return response.json()
                last_error = f"status {response.status_code}"
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.25)
        self.stop()
        pytest.fail(f"server did not become healthy: {last_error}")

    def stop(self) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:  # pragma: no cover - only on a hung server
            self.process.kill()
            self.process.wait(timeout=30)
        self.process = None

    def read_output(self) -> str:
        if self.process is None or self.process.stdout is None:
            return ""
        self.process.kill()
        return self.process.stdout.read() or ""


@pytest.fixture
def server() -> Iterator[Server]:
    instance = Server(free_port())
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def run_modern_check(url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed command from our own package
        [sys.executable, str(MODERN_CHECK), url],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )


def run_legacy_check(url: str) -> subprocess.CompletedProcess[str]:
    """Run the legacy check in its own environment with mcp 1.x, never in ours."""
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is not on PATH: the isolated legacy environment cannot be built")
    return subprocess.run(  # noqa: S603 - fixed command, spec is a constant
        [
            uv,
            "run",
            "--isolated",
            "--no-project",
            "--with",
            LEGACY_SPEC,
            "python",
            str(LEGACY_CHECK),
            url,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
        check=False,
    )


def test_health_reports_status_and_version(server: Server) -> None:
    payload = server.wait_until_healthy()
    assert payload["status"] == "ok"
    assert set(payload) == {"status", "version"}


def test_a_modern_client_is_served(server: Server) -> None:
    result = run_modern_check(server.url)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "tools/list returned" in result.stdout


def test_a_legacy_client_is_served_from_the_same_endpoint(server: Server) -> None:
    """D-19: SDK 1.29 and 2.x out of one endpoint, no "Session terminated" anywhere."""
    result = run_legacy_check(server.url)
    if result.returncode != 0:
        combined = f"{result.stdout}\n{result.stderr}".lower()
        if any(marker in combined for marker in OFFLINE_MARKERS) and "session" not in combined:
            pytest.skip(
                f"no network for the isolated {LEGACY_SPEC} environment: {result.stderr[:400]}"
            )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "Session terminated" not in f"{result.stdout}{result.stderr}"
    assert "answered initialize" in result.stdout


def test_a_conversation_survives_a_server_restart(server: Server) -> None:
    """SRV-05: nothing can be lost on restart, because no session exists to lose."""
    before = run_modern_check(server.url)
    assert before.returncode == 0, before.stderr

    server.stop()
    server.start()

    after = run_modern_check(server.url)
    assert after.returncode == 0, f"reconnect failed after restart: {after.stderr}"
    assert after.stdout.strip() == before.stdout.strip(), "the restarted server answers the same"


def test_a_foreign_host_header_is_rejected_by_the_running_server(server: Server) -> None:
    """The 421 of pitfall 6, this time through a real socket."""
    response = httpx.post(
        server.url,
        headers={
            "Host": "evil.example",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        timeout=10.0,
    )
    assert response.status_code == 421
