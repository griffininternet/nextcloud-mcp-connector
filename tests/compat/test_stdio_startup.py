"""Startup contract of the ``nc-mcp`` console script (SRV-02, pitfall 7).

The server is started as a real subprocess and answers a JSON-RPC ``initialize`` on stdin.
Two things are proven at once: the console script from ``pyproject.toml`` exists and works,
and the first stdout line is valid JSON-RPC, so nothing pollutes the wire. No Nextcloud is
needed because ``initialize`` triggers no Nextcloud request.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.matrix

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "gsd-compat-check", "version": "0.0.0"},
    },
}

DUMMY_ENV = {
    "NC_MCP_URL": "http://nc.test",
    "NC_MCP_USER": "alice",
    "NC_MCP_APP_PASSWORD": "dummy-app-password",
}


def _console_script() -> str:
    found = shutil.which("nc-mcp")
    if found:
        return found
    candidate = Path(sys.executable).parent / ("nc-mcp.exe" if os.name == "nt" else "nc-mcp")
    if candidate.exists():
        return str(candidate)
    pytest.skip("console script nc-mcp is not installed in this environment")


def _run(env_extra: dict[str, str], stdin_text: str) -> tuple[int, str, str]:
    env = {**os.environ, **env_extra}
    for name in ("NC_MCP_URL", "NC_MCP_USER", "NC_MCP_APP_PASSWORD"):
        if name not in env_extra:
            env.pop(name, None)
    process = subprocess.Popen(  # noqa: S603 - fixed command from our own package
        [_console_script()],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )
    try:
        stdout, stderr = process.communicate(stdin_text, timeout=120)
    except subprocess.TimeoutExpired:  # pragma: no cover - only on a hung server
        process.kill()
        stdout, stderr = process.communicate()
        pytest.fail(f"nc-mcp did not answer in time. stderr: {stderr[:2000]}")
    return process.returncode, stdout, stderr


def test_initialize_answers_with_json_on_the_first_stdout_line() -> None:
    returncode, stdout, stderr = _run(DUMMY_ENV, json.dumps(INITIALIZE) + "\n")

    assert stdout.strip(), f"no answer on stdout. stderr: {stderr[:2000]}"
    first_line = stdout.splitlines()[0]
    payload = json.loads(first_line)  # fails loudly if anything polluted stdout

    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == 1
    assert "error" not in payload, payload.get("error")
    assert payload["result"]["serverInfo"]["name"] == "MCP Connector"
    assert returncode == 0, f"unclean exit. stderr: {stderr[:2000]}"


def test_logs_go_to_stderr_not_to_stdout() -> None:
    _, stdout, stderr = _run(DUMMY_ENV, json.dumps(INITIALIZE) + "\n")

    for line in stdout.splitlines():
        if line.strip():
            json.loads(line)
    assert "stdio" in stderr, "the startup log line belongs on stderr"


def test_missing_environment_fails_with_a_named_variable() -> None:
    returncode, stdout, stderr = _run({}, "")

    assert returncode != 0
    assert stdout.strip() == "", "a configuration error must not write to the wire"
    assert "NC_MCP_URL" in stderr
