"""Guards for the ExApp package: container image, start scripts and appinfo/info.xml.

These are pure file assertions, no Docker and no network, so the default suite keeps
running on a host without a container engine (D-32). They hold the truths that would
otherwise only surface during a deploy, when the feedback loop is minutes long and the
audience is an administrator:

* a CR in a file the container reads turns the ENTRYPOINT into a "not found",
* a root container holds the shared secret and the data volume with far more authority
  than an MCP responder needs (T-02-22),
* a missing HEALTHCHECK makes AppAPI treat a broken container as healthy (T-02-25),
* an unverified frpc download is a supply chain hole (T-02-SC),
* and one route that is a shade too wide publishes the AppAPI lifecycle endpoints,
  including the one that disables the app, to anyone on the internet (T-02-20).

The manifest half is written as one function over a parsed root element rather than as a
chain of asserts, so the last test in this file can feed it a deliberately broken manifest
and prove that the gate actually fires.
"""

import ipaddress
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from lxml import etree

import mcp_connector
from mcp_connector import config
from mcp_connector.entry_exapp import build_exapp_app
from mcp_connector.nextcloud.clients.xml import hardened_parser

ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / ".env.exapp.example"
INSTALL_DOC = ROOT / "docs" / "exapp-install.md"
DOCKERFILE = ROOT / "Dockerfile"
ENTRYPOINT = ROOT / "entrypoint.sh"
START = ROOT / "start.sh"
HEALTHCHECK = ROOT / "healthcheck.sh"
DOCKERIGNORE = ROOT / ".dockerignore"
INFO_XML = ROOT / "appinfo" / "info.xml"
COMPOSE_EXAPP = ROOT / "compose.exapp.yml"
CADDYFILE = ROOT / "deploy" / "Caddyfile"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_exapp.sh"

CONTAINER_FILES = (DOCKERFILE, ENTRYPOINT, START, HEALTHCHECK)

#: The second half of this file guards the test topology of plan 02-04. Same reason as
#: above: docker compose exec breaks on a CR, a port that lost its 127.0.0.1 prefix
#: publishes a throwaway Nextcloud to the LAN (T-02-30), and a bootstrap script that grew a
#: reference to the other compose file could take down an instance somebody is using
#: (T-02-34).
TOPOLOGY_FILES = (COMPOSE_EXAPP, CADDYFILE, BOOTSTRAP)

#: Names that must never be baked into a layer: they are secrets, or they are the second
#: credential channel the ExApp mode refuses to have (T-02-23, D-27).
FORBIDDEN_ENV_NAMES = ("APP_SECRET", "NC_MCP_APP_PASSWORD", "NC_MCP_STATIC_BEARER")

#: Route patterns that match everything worth protecting. The literal blacklist catches the
#: obvious spellings, the probe below catches the creative ones.
WIDE_URLS = frozenset({".*", "^.*$", "/", ".+", "^.+$"})

#: The three paths AppAPI calls on the container. None of them may be reachable through a
#: declared route: an unmatched path is a 404, a matched one is served by the PHP proxy
#: with valid AppAPI headers attached.
LIFECYCLE_PATHS = ("/heartbeat", "/init", "/enabled")

#: Headers the proxy sets itself. A route that does not have them stripped lets a client
#: send its own copy next to the real one, and which of the two a reader sees depends on
#: whether the proxy prepends or appends (WR-01, IN-01).
PROXY_OWNED_HEADERS = (
    "AUTHORIZATION-APP-API",
    "EX-APP-ID",
    "EX-APP-VERSION",
    "AA-VERSION",
    "X-ORIGIN-IP",
)

#: What this phase opens: the MCP transport, the three discovery documents, the two pages
#: of the browser onboarding, the four endpoints of the authorization server, the consent
#: screen behind /authorize and the decision behind that screen (D-38, AUTH-02, AUTH-03).
DECLARED_ROUTES = 12

#: The routes that must not be PUBLIC, and the level they carry instead. One entry, and it
#: is the enforcement point of CR-01: the decision is the request that turns a finished
#: Nextcloud sign in into a grant, and only HaRP can say which account is behind the
#: browser that sends it. A PUBLIC decision route is the Login Flow v2 relay again, so the
#: gate below refuses the manifest instead of trusting a review to notice.
ACCESS_LEVELS = {"^/authorize/decide/?$": "USER"}

#: Every access level this app is allowed to declare at all. ADMIN is deliberately absent:
#: no route of this app is an administrative one, and a level nobody meant to use is a
#: level nobody checks.
ALLOWED_ACCESS_LEVELS = frozenset({"PUBLIC", "USER"})

#: The onboarding paths the application registers, compared with the manifest below. Set
#: equality for the same reason as the well-known documents: a page that is declared but not
#: served is a 404 nobody can explain, and one that is served but not declared is unreachable
#: through the proxy.
CONNECT_PATHS = ("/connect", "/connect/wait")

#: The four endpoints of the authorization server, compared with the manifest the same way.
#: A declared endpoint the application does not serve is a 404 during a first connection,
#: and a served one that is not declared is unreachable through HaRP (AUTH-03, D-38).
AS_PATHS = ("/authorize", "/token", "/register", "/revoke")

#: The consent screen of plan 03-05 and the decision behind it. Declared with the four
#: above and compared with them, because the screen is the page /authorize sends every
#: browser to and the decision is the request that grant hangs on (CR-01).
CONSENT_PATH = "/authorize/consent"
DECIDE_PATH = "/authorize/decide"

AUTHORIZATION_PATHS = (*AS_PATHS, CONSENT_PATH, DECIDE_PATH)

#: Enough of a deploy environment to build the application the manifest is compared against.
MANIFEST_ENV = {
    config.ENV_APP_ID: "mcp_connector",
    config.ENV_APP_SECRET: "app-secret-test",
    config.ENV_APP_VERSION: mcp_connector.__version__,
    config.ENV_NEXTCLOUD_URL: "http://nc.test",
}


def instruction_values(text: str, keyword: str) -> list[str]:
    """Every value of a Dockerfile instruction, in file order, comments removed."""
    values: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        head, _, rest = stripped.partition(" ")
        if head == keyword:
            values.append(rest.strip())
    return values


def manifest_problems(root: etree._Element) -> list[str]:
    """Return every reason this manifest must not be shipped, empty list when it is fine.

    A function instead of a row of asserts, because a gate that was never seen failing is
    not a gate. ``test_the_manifest_gate_rejects_a_wide_public_route`` calls this with a
    manifest that carries the exact mistake 02-RESEARCH.md warns about first.
    """
    problems: list[str] = []

    if root.findtext("id") != "mcp_connector":
        problems.append("the app id is not the frozen mcp_connector")

    version = (root.findtext("version") or "").strip()
    if version != mcp_connector.__version__:
        problems.append(f"version {version!r} is not the package version")

    image_tag = (root.findtext(".//docker-install/image-tag") or "").strip()
    if image_tag != version:
        problems.append(f"image tag {image_tag!r} does not follow the version {version!r}")

    routes = root.findall(".//route")
    if len(routes) != DECLARED_ROUTES:
        problems.append(
            f"{len(routes)} routes declared, this phase opens exactly {DECLARED_ROUTES}"
        )

    for route in routes:
        url = (route.findtext("url") or "").strip()
        access_level = (route.findtext("access_level") or "").strip()
        bruteforce = (route.findtext("bruteforce_protection") or "").strip()
        excluded = (route.findtext("headers_to_exclude") or "").strip()

        if url in WIDE_URLS:
            problems.append(f"route {url!r} matches everything")
        for header in PROXY_OWNED_HEADERS:
            if f'"{header}"' not in excluded:
                problems.append(f"route {url!r} does not have {header} stripped by the proxy")
        if access_level == "PUBLIC" and not url.startswith("^/"):
            problems.append(f"public route {url!r} is not anchored at a path")
        if access_level not in ALLOWED_ACCESS_LEVELS:
            problems.append(f"route {url!r} declares the access level {access_level!r}")
        expected = ACCESS_LEVELS.get(url, "PUBLIC")
        if access_level != expected:
            # The access level table of CR-01. The decision behind the consent screen is
            # the one request whose caller HaRP has to resolve, and every other route is
            # PUBLIC for a reason written next to it in the manifest. A route that changes
            # level silently is a change of who may reach it, so it fails here.
            problems.append(f"route {url!r} is {access_level!r} and has to be {expected!r}")
        if not url.endswith("$"):
            # HaRP matches with re.match, which anchors at the start only, so a pattern
            # without an end anchor also matches every neighbour that starts the same way:
            # the old ^/\.well-known/ covered the whole tree, and even a per document
            # pattern without the $ would still cover /.well-known/openid-configuration.evil
            # (pitfall 14, AR-02-06). The rule holds for every route of this app since plan
            # 03-04, not only for the well-known ones: /connect without the anchor would
            # publish every path that begins with it.
            problems.append(f"route {url!r} has no end anchor")
        if "401" in bruteforce:
            problems.append(f"route {url!r} throttles on 401, which breaks OAuth discovery")
        for path in LIFECYCLE_PATHS:
            if _matches(url, path):
                problems.append(f"route {url!r} exposes the lifecycle path {path}")

    return problems


def declared_connect_paths(root: etree._Element) -> set[str]:
    """The literal path behind every onboarding route pattern of the manifest.

    Same reduction as for the well-known documents, plus the optional trailing slash that
    lets ``/connect/`` reach the same page as ``/connect``.
    """
    paths = set()
    for route in root.findall(".//route"):
        url = (route.findtext("url") or "").strip()
        if not url.startswith("^/connect"):
            continue
        paths.add(url.removeprefix("^").removesuffix("$").removesuffix("/?").replace("\\", ""))
    return paths


def declared_authorization_paths(root: etree._Element) -> set[str]:
    """The literal path behind every authorization server route of the manifest."""
    paths = set()
    for route in root.findall(".//route"):
        url = (route.findtext("url") or "").strip()
        literal = url.removeprefix("^").removesuffix("$").removesuffix("/?").replace("\\", "")
        if literal in AUTHORIZATION_PATHS:
            paths.add(literal)
    return paths


def declared_well_known_paths(root: etree._Element) -> set[str]:
    """The literal path behind every well-known route pattern of the manifest.

    The patterns are regular expressions for HaRP; reducing them to their literal form
    (anchors and escapes removed) is what makes them comparable with the Starlette paths
    the application actually registers.
    """
    paths = set()
    for route in root.findall(".//route"):
        url = (route.findtext("url") or "").strip()
        if "well-known" not in url:
            continue
        paths.add(url.removeprefix("^").removesuffix("$").replace("\\", ""))
    return paths


def _excluded_headers() -> str:
    """The headers_to_exclude value of the manifest, for a route a test builds itself."""
    return "[" + ",".join(f'"{header}"' for header in PROXY_OWNED_HEADERS) + "]"


def compose_services(text: str) -> dict[str, str]:
    """Split the services mapping of a compose file into one text block per service.

    Hand written instead of parsed: the project has no YAML dependency, and adding one for
    six assertions would be a runtime dependency for a test. The file it reads is written
    by hand and stays inside the two space indentation the rest of the repository uses.
    """
    blocks: dict[str, list[str]] = {}
    in_services = False
    current: str | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            in_services = line.startswith("services:")
            current = None
            continue
        if in_services and indent == 2 and line.strip().endswith(":"):
            current = line.strip().rstrip(":")
            blocks[current] = []
            continue
        if current is not None:
            blocks[current].append(line)
    return {name: "\n".join(body) for name, body in blocks.items()}


def published_ports(text: str) -> list[str]:
    """Every entry of every ``ports:`` list in the given compose text, comments removed."""
    ports: list[str] = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "ports:":
            collecting = True
            continue
        if collecting:
            if stripped.startswith("- "):
                ports.append(stripped[2:].strip().strip('"').strip("'"))
            else:
                collecting = False
    return ports


def shell_function(name: str, path: Path | None = None) -> str:
    """Cut one function out of a shell script so a test can run it on its own.

    The alternative would be sourcing the whole file, and the bootstrap talks to Docker
    from its first line. The cut is exact: every script here writes a function as
    ``name() {`` on its own line and closes it with a ``}`` in column one, and the
    assertions below fail loudly if that ever stops being true.
    """
    text = (path or BOOTSTRAP).read_text(encoding="utf-8")
    opening = f"\n{name}() {{\n"
    start = text.index(opening)
    end = text.index("\n}\n", start)
    return text[start + 1 : end + 3]


def find_bash() -> str | None:
    """A bash that can actually run this repository's scripts, or ``None``.

    ``shutil.which('bash')`` is not enough on Windows: it finds the WSL relay in
    System32 first, which fails with "execvpe(/bin/bash)" on a host without a distro and
    cannot resolve a drive letter path even with one. So every candidate is probed with a
    Windows style path it has to see, and the first one that passes wins.
    """
    probe = f'test -f "{Path(__file__).as_posix()}"'
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        "/bin/bash",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run(  # noqa: S603 - a literal probe, no user input
                [candidate, "-c", probe],
                capture_output=True,
                check=False,
                timeout=60,
            )
        except OSError:
            continue
        if result.returncode == 0:
            return candidate
    return None


BASH = find_bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="no usable bash on this host")


def run_bash(script: str) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    return subprocess.run(  # noqa: S603 - a literal script from this test, no user input
        [BASH, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _matches(url: str, path: str) -> bool:
    """Whether the route regex would let ``path`` through, unparseable patterns included."""
    try:
        return re.search(url, path) is not None
    except re.error:
        return True


@pytest.fixture
def manifest_root() -> etree._Element:
    return etree.parse(str(INFO_XML), hardened_parser()).getroot()


@pytest.mark.parametrize(
    "path", [DOCKERFILE, ENTRYPOINT, START, HEALTHCHECK, DOCKERIGNORE, INFO_XML]
)
def test_the_exapp_package_is_checked_in(path: Path) -> None:
    assert path.is_file(), f"{path.name} is missing"


@pytest.mark.parametrize("path", list(CONTAINER_FILES))
def test_no_crlf_in_files_the_container_reads(path: Path) -> None:
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; docker compose exec fails on the CR"
    )


def test_the_image_declares_a_healthcheck() -> None:
    """T-02-25: AppAPI reads container health, and no healthcheck means always healthy."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "HEALTHCHECK" in text
    assert "/healthcheck.sh" in text


def test_the_image_runs_unprivileged() -> None:
    """T-02-22: the container holds APP_SECRET and the data volume, root is not needed."""
    users = instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "USER")
    assert users, "the Dockerfile never leaves root"
    final = users[-1]
    assert final not in {"root", "0", "root:root", "0:0"}, f"USER {final} is root"
    assert final.split(":")[0] not in {"root", "0"}, f"USER {final} is root"


def test_the_entrypoint_is_the_wrapper_that_execs_the_harp_start_script() -> None:
    """WR-02, WR-04: the guards run first, then the upstream script, with the same arg."""
    entrypoints = instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ENTRYPOINT")
    assert entrypoints, "the Dockerfile declares no ENTRYPOINT"
    assert "/entrypoint.sh" in entrypoints[-1]
    assert "nc-mcp-exapp" in entrypoints[-1]
    assert 'exec /start.sh "$@"' in ENTRYPOINT.read_text(encoding="utf-8")


def test_the_image_arms_no_transport_switch_in_a_layer() -> None:
    """WR-02: the switch disables the Host and the Origin check of the MCP transport, and
    in a layer it did so for every deployment mode, HaRP or not."""
    for value in instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ENV"):
        assert "NC_MCP_DISABLE_DNS_REBINDING_PROTECTION" not in value


def test_the_transport_switch_is_bound_to_the_harp_path() -> None:
    text = ENTRYPOINT.read_text(encoding="utf-8")
    switch = "export NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=1"
    assert switch in text
    before = text.split(switch, 1)[0]
    assert 'if [ -n "${HP_SHARED_KEY:-}" ]; then' in before, "the switch is not HaRP bound"
    code = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    assert not any("NC_MCP_ALLOWED_HOSTS=" in line for line in code), (
        "the host allowlist stays a deployment decision, the entrypoint never sets it"
    )


def test_the_entrypoint_refuses_a_plaintext_frp_tunnel() -> None:
    """WR-04: without /certs/frp start.sh writes transport.tls.enable = false and sends
    HP_SHARED_KEY in the clear. The downgrade is refused, with a documented opt-in."""
    text = ENTRYPOINT.read_text(encoding="utf-8")
    assert "/certs/frp" in text
    assert "exit 1" in text
    assert "ALLOW_PLAINTEXT_FRP" in text


@needs_bash
@pytest.mark.parametrize(
    ("env", "expected_code"),
    [
        ({"HP_SHARED_KEY": "x" * 64, "FRP_CERT_WAIT_SECONDS": "0"}, 1),
        (
            {
                "HP_SHARED_KEY": "x" * 64,
                "FRP_CERT_WAIT_SECONDS": "0",
                "ALLOW_PLAINTEXT_FRP": "1",
            },
            0,
        ),
        ({"FRP_CERT_WAIT_SECONDS": "0"}, 0),
    ],
    ids=["harp without a certificate", "explicit opt-in", "no harp at all"],
)
def test_the_plaintext_guard_decides_by_the_shared_key(
    tmp_path: Path, env: dict[str, str], expected_code: int
) -> None:
    """The guard runs for real, with /start.sh replaced by a stub that only records that
    it was reached. A container without HP_SHARED_KEY has no tunnel and must not be
    blocked by a certificate it does not need."""
    stub = tmp_path / "start.sh"
    stub.write_text('#!/bin/sh\necho REACHED_START "$@"\n', encoding="utf-8", newline="\n")
    absent = (tmp_path / "absent").as_posix()
    body = (
        ENTRYPOINT.read_text(encoding="utf-8")
        .replace('FRP_CERT_DIR="/certs/frp"', f'FRP_CERT_DIR="{absent}"')
        .replace('exec /start.sh "$@"', f'exec sh "{stub.as_posix()}" "$@"')
    )
    assert absent in body, "the certificate directory is not a single literal any more"
    exports = "".join(f'export {name}="{value}"\n' for name, value in env.items())
    script = f"{exports}{body}"

    result = run_bash(script)

    assert result.returncode == expected_code, result.stderr
    assert ("REACHED_START" in result.stdout) is (expected_code == 0)


@needs_bash
@pytest.mark.parametrize(
    ("files", "expected_code"),
    [
        ((), 1),
        (("client.crt", "client.key"), 1),
        (("client.crt", "client.key", "ca.crt"), 0),
    ],
    ids=["directory without files", "ca.crt still missing", "all three files"],
)
def test_the_plaintext_guard_waits_for_the_files_not_the_directory(
    tmp_path: Path, files: tuple[str, ...], expected_code: int
) -> None:
    """IN-02: HaRP creates /certs/frp with `mkdir -p` before it copies the three files
    start.sh reads. A guard that only checks the directory lets start.sh emit a TLS
    configuration whose certFile does not exist yet, so the guard has to wait for the
    files themselves."""
    stub = tmp_path / "start.sh"
    stub.write_text('#!/bin/sh\necho REACHED_START "$@"\n', encoding="utf-8", newline="\n")
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    for name in files:
        (cert_dir / name).write_text("not a real certificate\n", encoding="utf-8", newline="\n")
    body = (
        ENTRYPOINT.read_text(encoding="utf-8")
        .replace('FRP_CERT_DIR="/certs/frp"', f'FRP_CERT_DIR="{cert_dir.as_posix()}"')
        .replace('exec /start.sh "$@"', f'exec sh "{stub.as_posix()}" "$@"')
    )
    assert cert_dir.as_posix() in body, "the certificate directory is not a single literal"
    script = f'export HP_SHARED_KEY="{"x" * 64}"\nexport FRP_CERT_WAIT_SECONDS="0"\n{body}'

    result = run_bash(script)

    assert result.returncode == expected_code, result.stderr
    assert ("REACHED_START" in result.stdout) is (expected_code == 0)


def test_the_frpc_download_is_checksum_verified() -> None:
    """T-02-SC: frpc is a foreign binary, and a release asset can be replaced."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "sha256sum -c" in text, "the frpc archive is unpacked without a checksum check"
    assert "FRP_AMD64_SHA256" in text
    assert "FRP_ARM64_SHA256" in text


def test_the_frpc_checksums_cannot_be_replaced_from_the_command_line() -> None:
    """IN-03: as ARGs they were overridable with --build-arg, so the pin only held for a
    build nobody tampered with."""
    args = instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ARG")
    for name in ("FRP_AMD64_SHA256", "FRP_ARM64_SHA256", "FRP_VERSION"):
        assert not any(value.startswith(name) for value in args), f"{name} is still an ARG"


@pytest.mark.parametrize("name", FORBIDDEN_ENV_NAMES)
def test_no_secret_is_baked_into_the_image(name: str) -> None:
    """T-02-23: secrets come from the deploy environment, never from a layer."""
    for value in instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ENV"):
        assert name not in value, f"the image sets {name} in an ENV instruction"


def test_the_runtime_user_does_not_own_its_own_code() -> None:
    """WR-13: a writable site-packages turns any single file write into persistence, and
    AppAPI restarts this container rather than recreating it."""
    for value in instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "COPY"):
        if "/app/.venv" not in value:
            continue
        assert "--chown" not in value, f"the virtual environment is chowned: COPY {value}"


def test_the_build_context_excludes_the_history_and_any_env_file() -> None:
    entries = DOCKERIGNORE.read_text(encoding="utf-8").split()
    for pattern in (".git", ".planning", ".env*", "tests"):
        assert pattern in entries, f"{pattern} belongs into .dockerignore"


def test_the_start_script_is_the_upstream_one_with_its_origin_named() -> None:
    """It is copied verbatim from HaRP on purpose, so the header has to say so."""
    text = START.read_text(encoding="utf-8")
    assert "SPDX-License-Identifier: AGPL-3.0-or-later" in text
    assert "nextcloud/HaRP" in text
    assert "exapps_dev/start.sh" in text
    assert 'exec "$@"' in text, "without the exec the container would not run the app"


def test_the_healthcheck_knows_both_transports() -> None:
    """Behind HaRP there is no TCP port at all, so one probe would be permanently red."""
    text = HEALTHCHECK.read_text(encoding="utf-8")
    assert "HP_SHARED_KEY" in text
    assert "APP_PORT" in text
    assert "--unix-socket" in text
    assert "/heartbeat" in text


def test_the_healthcheck_notices_a_dead_tunnel_client() -> None:
    """WR-05: frpc is an unsupervised background child with loginFailExit = false, so the
    socket answers and the container reports healthy while HaRP has no backend."""
    text = HEALTHCHECK.read_text(encoding="utf-8")
    assert "frpc_is_running" in text
    harp_branch = text.split('if [ -n "${HP_SHARED_KEY:-}" ]; then', 1)[1]
    assert "if ! frpc_is_running; then" in harp_branch
    assert harp_branch.index("frpc_is_running") < harp_branch.index("exec curl"), (
        "the tunnel check has to run before the probe that would answer anyway"
    )


@needs_bash
@pytest.mark.parametrize(
    ("second_process", "expected_code"),
    [("uvicorn", 1), ("frpc", 0)],
    ids=["frpc is dead", "frpc is alive"],
)
def test_the_tunnel_probe_reads_the_process_table(
    tmp_path: Path, second_process: str, expected_code: int
) -> None:
    """The helper runs for real, against a process table built for this test: a container
    always has PID 1, and the question is whether frpc sits next to it."""
    fake_proc = tmp_path / "process-table"
    for pid, comm in (("1", "sh"), ("42", second_process)):
        entry = fake_proc / pid
        entry.mkdir(parents=True)
        (entry / "comm").write_text(f"{comm}\n", encoding="utf-8", newline="\n")

    body = shell_function("frpc_is_running", HEALTHCHECK).replace(
        "/proc/[0-9]*", f"{fake_proc.as_posix()}/[0-9]*"
    )
    assert fake_proc.as_posix() in body, "the process table path is not a single literal"
    result = run_bash(f"set -eu\n{body}\nfrpc_is_running\n")

    assert result.returncode == expected_code, result.stderr


def test_the_manifest_declares_exactly_the_twelve_routes_of_this_phase(
    manifest_root: etree._Element,
) -> None:
    """D-38: /mcp is PUBLIC since plan 03-01, the one broad well-known route that carried the
    accepted risk AR-02-06 is three fully anchored ones now, plan 03-04 adds the two pages of
    the browser onboarding, and plan 03-05 adds the four endpoints of the authorization
    server plus the consent screen behind /authorize. Every one of them is anchored at both
    ends and PUBLIC for a reason of its own, except the decision behind the consent screen:
    that one is USER, because HaRP has to name the account that decides (CR-01)."""
    routes = [
        ((route.findtext("url") or "").strip(), (route.findtext("access_level") or "").strip())
        for route in manifest_root.findall(".//route")
    ]
    assert routes == [
        ("^/mcp/?$", "PUBLIC"),
        ("^/\\.well-known/oauth-protected-resource/mcp$", "PUBLIC"),
        ("^/\\.well-known/openid-configuration$", "PUBLIC"),
        ("^/\\.well-known/oauth-authorization-server$", "PUBLIC"),
        ("^/connect/wait/?$", "PUBLIC"),
        ("^/connect/?$", "PUBLIC"),
        ("^/authorize/?$", "PUBLIC"),
        ("^/authorize/consent/?$", "PUBLIC"),
        ("^/authorize/decide/?$", "USER"),
        ("^/token/?$", "PUBLIC"),
        ("^/register/?$", "PUBLIC"),
        ("^/revoke/?$", "PUBLIC"),
    ]


def test_the_declared_onboarding_routes_are_the_registered_ones(
    manifest_root: etree._Element,
) -> None:
    """Set equality again, for the second family of pages this app publishes (AUTH-02)."""
    registered = {
        path
        for path in (
            getattr(route, "path", "") for route in build_exapp_app(MANIFEST_ENV).router.routes
        )
        if path.startswith("/connect")
    }

    assert declared_connect_paths(manifest_root) == registered == set(CONNECT_PATHS)


def test_the_onboarding_route_declares_the_verb_that_starts_a_sign_in(
    manifest_root: etree._Element,
) -> None:
    """A GET only declaration would leave the start of a flow unreachable through HaRP, and
    a POST on the waiting page would let a proxy replay a page that polls (T-03-34)."""
    verbs = {
        (route.findtext("url") or "").strip(): (route.findtext("verb") or "").strip()
        for route in manifest_root.findall(".//route")
    }

    assert verbs["^/connect/?$"] == "GET,POST"
    assert verbs["^/connect/wait/?$"] == "GET"


def test_the_declared_authorization_routes_are_the_registered_ones(
    manifest_root: etree._Element,
) -> None:
    """Set equality for the third family of routes, and the one that hands out tokens."""
    registered = {
        path
        for path in (
            getattr(route, "path", "") for route in build_exapp_app(MANIFEST_ENV).router.routes
        )
        if path in AUTHORIZATION_PATHS
    }

    assert declared_authorization_paths(manifest_root) == registered == set(AUTHORIZATION_PATHS)


def test_the_authorization_routes_declare_exactly_the_verbs_they_answer(
    manifest_root: etree._Element,
) -> None:
    """A missing POST on /authorize breaks the form post of RFC 6749, and a GET on /token
    would publish a credential endpoint to every crawler that follows a link."""
    verbs = {
        (route.findtext("url") or "").strip(): (route.findtext("verb") or "").strip()
        for route in manifest_root.findall(".//route")
    }

    assert verbs["^/authorize/?$"] == "GET,POST"
    assert verbs["^/authorize/consent/?$"] == "GET"
    assert verbs["^/authorize/decide/?$"] == "POST"
    assert verbs["^/token/?$"] == "POST"
    assert verbs["^/register/?$"] == "POST"
    assert verbs["^/revoke/?$"] == "POST"


def test_no_authorization_route_is_declared_twice(manifest_root: etree._Element) -> None:
    """The SDK registers a metadata document of its own at a path this app already serves,
    and two routes on one path answer whichever was registered first (plan 03-05)."""
    paths = [getattr(route, "path", "") for route in build_exapp_app(MANIFEST_ENV).router.routes]
    served = [
        path for path in paths if path.startswith("/.well-known/") or path in AUTHORIZATION_PATHS
    ]

    assert len(served) == len(set(served)), f"a path is served twice: {sorted(served)}"


def test_the_declared_well_known_routes_are_the_registered_ones(
    manifest_root: etree._Element,
) -> None:
    """Set equality, not a subset: a document that is declared but not served is a 404 an
    administrator cannot explain, and one that is served but not declared is unreachable
    through the proxy. Both are silent until a client tries to connect."""
    registered = {
        path
        for path in (
            getattr(route, "path", "") for route in build_exapp_app(MANIFEST_ENV).router.routes
        )
        if "well-known" in path
    }

    assert declared_well_known_paths(manifest_root) == registered


def test_the_manifest_gate_rejects_a_well_known_route_without_an_end_anchor(
    manifest_root: etree._Element,
) -> None:
    """Pitfall 14: HaRP matches with re.match, so a missing $ opens the neighbours too."""
    routes = manifest_root.find(".//routes")
    assert routes is not None
    route = etree.SubElement(routes, "route")
    etree.SubElement(route, "url").text = "^/\\.well-known/openid-configuration"
    etree.SubElement(route, "verb").text = "GET"
    etree.SubElement(route, "access_level").text = "PUBLIC"
    etree.SubElement(route, "headers_to_exclude").text = _excluded_headers()

    problems = manifest_problems(manifest_root)

    assert any("has no end anchor" in problem for problem in problems)


def test_the_manifest_gate_rejects_the_broad_well_known_route_of_phase_two(
    manifest_root: etree._Element,
) -> None:
    """The exact pattern AR-02-06 was accepted for. It must never come back unnoticed."""
    routes = manifest_root.find(".//routes")
    assert routes is not None
    route = etree.SubElement(routes, "route")
    etree.SubElement(route, "url").text = "^/\\.well-known/"
    etree.SubElement(route, "verb").text = "GET"
    etree.SubElement(route, "access_level").text = "PUBLIC"
    etree.SubElement(route, "headers_to_exclude").text = _excluded_headers()

    problems = manifest_problems(manifest_root)

    assert any("has no end anchor" in problem for problem in problems)


def test_the_manifest_passes_its_own_gate(manifest_root: etree._Element) -> None:
    assert manifest_problems(manifest_root) == []


def test_the_manifest_carries_no_scopes_element(manifest_root: etree._Element) -> None:
    """AppAPI 3.2.0 removed scopes; a leftover element is noise the store reviews."""
    assert manifest_root.findall(".//scopes") == []


def test_the_manifest_gate_rejects_a_wide_public_route(manifest_root: etree._Element) -> None:
    """The counter probe: without it, the green run above proves nothing about the gate."""
    routes = manifest_root.find(".//routes")
    assert routes is not None
    route = etree.SubElement(routes, "route")
    etree.SubElement(route, "url").text = ".*"
    etree.SubElement(route, "verb").text = "GET,POST,PUT,DELETE"
    etree.SubElement(route, "access_level").text = "PUBLIC"

    problems = manifest_problems(manifest_root)

    assert any("matches everything" in problem for problem in problems)
    assert any("/enabled" in problem for problem in problems)


def test_the_manifest_gate_rejects_a_public_decision_route(
    manifest_root: etree._Element,
) -> None:
    """CR-01: with the decision PUBLIC, HaRP forwards it without resolving an account, so
    the app has nothing to compare the deciding browser against and the Login Flow v2 relay
    is open again. The counter probe for the access level table."""
    routes = {
        (route.findtext("url") or "").strip(): route for route in manifest_root.findall(".//route")
    }
    element = routes["^/authorize/decide/?$"].find("access_level")
    assert element is not None
    element.text = "PUBLIC"

    problems = manifest_problems(manifest_root)

    assert any("has to be 'USER'" in problem for problem in problems)


def test_the_manifest_gate_rejects_an_unexpected_user_route(
    manifest_root: etree._Element,
) -> None:
    """The same table read the other way: a route that quietly becomes USER stops answering
    the anonymous request it exists for, and the discovery documents and /mcp are exactly
    those routes (pitfall 6). PUBLIC is the declared default and a deviation has to be
    written into the table, not into the manifest alone."""
    routes = {
        (route.findtext("url") or "").strip(): route for route in manifest_root.findall(".//route")
    }
    element = routes["^/mcp/?$"].find("access_level")
    assert element is not None
    element.text = "USER"

    problems = manifest_problems(manifest_root)

    assert any("has to be 'PUBLIC'" in problem for problem in problems)


def test_the_manifest_gate_rejects_a_route_that_keeps_the_client_headers(
    manifest_root: etree._Element,
) -> None:
    """WR-01: an empty headers_to_exclude is what made the desync reachable at all."""
    route = manifest_root.find(".//route")
    assert route is not None
    element = route.find("headers_to_exclude")
    assert element is not None
    element.text = "[]"

    problems = manifest_problems(manifest_root)

    assert any("AUTHORIZATION-APP-API stripped" in problem for problem in problems)


def test_the_bootstrap_registration_strips_the_same_headers() -> None:
    """The json-info registration overrides the manifest, so it has to carry the list."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert '"headers_to_exclude":[]' not in text
    for header in PROXY_OWNED_HEADERS:
        assert f'"{header}"' in text, f"{header} is not stripped by the registration"


def test_the_bootstrap_registration_declares_the_same_twelve_routes(
    manifest_root: etree._Element,
) -> None:
    """The json-info payload overrides the manifest, so a route that only lives in
    appinfo/info.xml is not registered on the test instance at all. access_level travels as
    a number there: 0 is PUBLIC and 1 is USER, and the one route that carries 1 is the one
    the manifest declares as USER (CR-01)."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert text.count('"access_level":0') == DECLARED_ROUTES - len(ACCESS_LEVELS)
    assert text.count('"access_level":1') == len(ACCESS_LEVELS)
    assert '"access_level":2' not in text
    for url in ACCESS_LEVELS:
        pattern = url.replace("\\", "\\\\")
        assert f'"url":"{pattern}","verb":"POST","access_level":1' in text, url
    for path in declared_well_known_paths(manifest_root):
        # The payload carries the pattern with a doubled backslash escape, so the literal
        # path is compared without the dot escape (see the comment above json_info).
        assert path.replace("/.well-known/", "well-known/") in text, path
    for path in declared_connect_paths(manifest_root):
        assert f'"^{path}/?$"' in text, path
    for path in declared_authorization_paths(manifest_root):
        assert f'"^{path}/?$"' in text, path


def test_the_manifest_gate_rejects_a_throttler_on_401(manifest_root: etree._Element) -> None:
    """T-02-21: the OAuth discovery flow of phase 3 begins with a 401 by specification."""
    route = manifest_root.find(".//route")
    assert route is not None
    etree.SubElement(route, "bruteforce_protection").text = "[401]"

    assert any("throttles on 401" in problem for problem in manifest_problems(manifest_root))


@pytest.mark.parametrize("path", list(TOPOLOGY_FILES))
def test_the_test_topology_is_checked_in(path: Path) -> None:
    assert path.is_file(), f"{path.name} is missing"


@pytest.mark.parametrize("path", list(TOPOLOGY_FILES))
def test_no_crlf_in_the_topology_files(path: Path) -> None:
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; docker compose exec and bash both break on the CR"
    )


def test_the_topology_publishes_on_loopback_only() -> None:
    """T-02-30: throwaway credentials plus a disabled bruteforce guard, so no LAN."""
    ports = published_ports(COMPOSE_EXAPP.read_text(encoding="utf-8"))
    assert ports, "no published port found, the parser or the file changed shape"
    for port in ports:
        assert port.startswith("127.0.0.1:"), f"port {port!r} is not bound to loopback"


def test_the_topology_carries_its_own_project_name() -> None:
    """Without it compose derives the project from the directory and both topologies land
    in the same project, where a `down` on one stops the containers of the other
    (T-02-34)."""
    lines = COMPOSE_EXAPP.read_text(encoding="utf-8").splitlines()
    names = [line for line in lines if line.startswith("name:")]
    assert names == ["name: nc-mcp-exapp"]


def test_the_shared_key_has_no_default_in_the_repository() -> None:
    """WR-11: a fixed default is a published secret, and the documented command used it,
    so nobody ever saw that their HaRP tunnel was open to whoever read this file."""
    services = compose_services(COMPOSE_EXAPP.read_text(encoding="utf-8"))
    lines = [
        line.strip()
        for line in services["appapi-harp"].splitlines()
        if line.strip().startswith("HP_SHARED_KEY:")
    ]
    assert lines, "HP_SHARED_KEY is not set for the deploy daemon any more"
    assert "${HP_SHARED_KEY:?" in lines[0], f"{lines[0]!r} still carries a default"
    assert ":-" not in lines[0]


def test_only_the_reverse_proxy_is_a_trusted_proxy() -> None:
    """WR-08: the whole subnet also covered the ExApp container, which is the component
    that processes untrusted input. It must not be able to forge a client address."""
    text = COMPOSE_EXAPP.read_text(encoding="utf-8")
    services = compose_services(text)
    addresses = set()
    for service, key in (
        ("nextcloud", "TRUSTED_PROXIES"),
        ("appapi-harp", "HP_TRUSTED_PROXY_IPS"),
    ):
        values = [
            line.split(":", 1)[1].strip().strip('"')
            for line in services[service].splitlines()
            if line.strip().startswith(f"{key}:")
        ]
        assert values, f"{key} is not set for {service}"
        assert "/" not in values[0], f"{key} is a range, not one proxy: {values[0]!r}"
        addresses.add(values[0])

    assert len(addresses) == 1, f"the two trust lists disagree: {addresses}"
    assert f"ipv4_address: {addresses.pop()}" in services["caddy"], (
        "the trusted address is not the fixed one assigned to the reverse proxy"
    )


def test_dynamic_addresses_never_enter_the_static_half_of_the_subnet() -> None:
    """IN-03: without an ip_range Docker may reassign the fixed proxy address once caddy
    is down, and the next container holding 172.29.42.10 (possibly the ExApp container
    itself) would be a trusted proxy for Nextcloud and HaRP."""
    text = COMPOSE_EXAPP.read_text(encoding="utf-8")
    ranges = re.findall(r"^\s*ip_range:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    assert ranges, "the ipam configuration carries no ip_range for dynamic assignment"
    dynamic = ipaddress.ip_network(ranges[0])
    statics = re.findall(r"^\s*ipv4_address:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    assert statics, "no statically assigned address found, the trust anchor is gone"
    for address in statics:
        assert ipaddress.ip_address(address) not in dynamic, (
            f"static address {address} lies inside the dynamic range {dynamic}"
        )


def test_the_deploy_daemon_publishes_no_port() -> None:
    """Caddy reaches HaRP inside the compose network; a published port only adds reach."""
    services = compose_services(COMPOSE_EXAPP.read_text(encoding="utf-8"))
    assert "appapi-harp" in services, f"services found: {sorted(services)}"
    assert "ports:" not in services["appapi-harp"]


def test_the_bootstrap_never_reaches_into_the_other_topology() -> None:
    """T-02-34, WR-07: the other test instance is in daily use and must survive this
    script. Naming the file is not enough, because the name used to be overridable: a
    forgotten `export COMPOSE_FILE=compose.test.yml` passed this test and still disabled
    the bruteforce guard on the instance somebody was using."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "compose.test.yml" not in text
    assert "down -v" not in text
    assert 'COMPOSE_FILE="compose.exapp.yml"' in text
    assert "COMPOSE_FILE:-" not in text, "the compose file is overridable from the shell"
    assert "ensure_own_topology" in text


@needs_bash
@pytest.mark.parametrize(
    ("content", "expected_code"),
    [
        ("name: nc-mcp-exapp\nservices:\n", 0),
        ("name: some-other-project\nservices:\n", 1),
        ("services:\n", 1),
        (None, 1),
    ],
    ids=["the right project", "a foreign project", "no project name", "no file at all"],
)
def test_the_topology_guard_refuses_a_foreign_compose_file(
    tmp_path: Path, content: str | None, expected_code: int
) -> None:
    """WR-07: the guard is what makes the fixed file name more than a comment."""
    compose = tmp_path / "compose.exapp.yml"
    if content is not None:
        compose.write_text(content, encoding="utf-8", newline="\n")
    script = (
        "set -euo pipefail\n"
        f'COMPOSE_FILE="{compose.as_posix()}"\n'
        f"{shell_function('ensure_own_topology')}\n"
        "ensure_own_topology\n"
    )

    result = run_bash(script)

    assert result.returncode == expected_code, result.stderr


@needs_bash
@pytest.mark.parametrize(
    ("call", "expected_code"),
    [
        ("require_port_number NC_EXAPP_APP_PORT '23000'", 0),
        ("require_port_number NC_EXAPP_APP_PORT '23000,\"system\":true'", 1),
        ("require_port_number NC_EXAPP_APP_PORT ''", 1),
        ("require_port_number NC_EXAPP_APP_PORT '23000 '", 1),
        ("require_registry_shape '127.0.0.1:5000'", 0),
        ("require_registry_shape 'ghcr.io'", 0),
        ('require_registry_shape \'127.0.0.1:5000","image":"evil\'', 1),
        ("require_registry_shape ''", 1),
    ],
    ids=[
        "a plain port",
        "a port with a JSON injection",
        "an empty port",
        "a port with trailing whitespace",
        "a registry with a port",
        "a bare registry host",
        "a registry with a JSON injection",
        "an empty registry",
    ],
)
def test_the_registration_inputs_are_pinned_before_json_info(call: str, expected_code: int) -> None:
    """IN-07: json_info interpolates the port unquoted and the registry into a string,
    and both come from overridable variables. A value outside the pinned shape must stop
    the bootstrap instead of reaching AppAPI as extra JSON fields."""
    script = (
        "set -euo pipefail\n"
        f"{shell_function('require_port_number')}\n"
        f"{shell_function('require_registry_shape')}\n"
        f"{call}\n"
    )

    result = run_bash(script)

    assert result.returncode == expected_code, result.stderr


def test_the_bootstrap_calls_both_registration_validators() -> None:
    """The functions only protect anything if the main flow actually runs them."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for call in (
        'require_port_number NC_EXAPP_APP_PORT "${APP_PORT}"',
        'require_port_number NC_EXAPP_MANUAL_PORT "${MANUAL_APP_PORT}"',
        'require_registry_shape "${REGISTRY}"',
    ):
        assert call in text, f"the bootstrap never runs {call!r}"


@pytest.mark.parametrize(
    "forbidden",
    [
        '-e "OC_PASS=',
        '--json-info "$(',
        '--json-info "${json}"',
        '--harp_shared_key "${',
        '-u "${',
    ],
)
def test_no_secret_travels_through_the_process_list(forbidden: str) -> None:
    """WR-06: the argv of `docker` and `curl` is world readable in `ps aux` for the whole
    call, and every value these patterns carry is bearer equivalent: the registration
    payload holds "secret":"<APP_SECRET>", the daemon registration holds HP_SHARED_KEY,
    OC_PASS is a login password and `curl -u` an app password. All of them go through
    stdin or a private file now. Checked over every shell script, not only the bootstrap:
    the pattern crept back into two sister scripts once (02-REVIEW WR-01 to WR-03)."""
    scripts = sorted((ROOT / "scripts").glob("*.sh"))
    assert scripts, "no shell scripts found, the guard would silently pass"
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert forbidden not in text, (
            f"{forbidden!r} in {script.name} puts a secret on a command line"
        )


def test_the_secrets_reach_the_container_through_stdin() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "occ_stdin" in text
    assert 'OC_PASS="$(cat)"' in text
    assert 'JSON="$(cat)"' in text


def test_no_grep_q_on_a_pipe_in_the_shell_scripts() -> None:
    """The scripts run with pipefail, and `grep -q` exits on the first match, which closes
    the pipe while the docker side is still writing. That side then dies on SIGPIPE (exit
    141) and pipefail turns the successful check into a failure. Two CI runs failed exactly
    there, with the wanted calendar visibly printed one line above the failing check. A
    grep without -q reads its input to the end, so `grep pattern >/dev/null` is the shape
    every piped check uses; -q stays allowed where grep reads from a file, not a pipe."""
    scripts = sorted((ROOT / "scripts").glob("*.sh"))
    assert scripts, "no shell scripts found, the guard would silently pass"
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "| grep -q" not in text, (
            f"{script.name} pipes into grep -q; under pipefail that is the SIGPIPE flake"
        )


def test_the_registration_verifies_what_the_registry_serves() -> None:
    """WR-09: the loopback registry takes a push from every local process, and the deploy
    daemon pulls by tag. A digest is the content, a tag is only a name."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "verify_image_digest" in text
    body = shell_function("ensure_exapp")
    assert body.index("verify_image_digest") < body.index("register_exapp"), (
        "the digest is checked after the registration triggered the pull"
    )


# --- the secret handling around the registration (CR-02) --------------------------

#: What the example file used to hand over as a working APP_SECRET, plus the shapes a
#: hand written value takes. None of them may survive into a registration.
WEAK_SECRETS = (
    "replace-me-with-a-random-hex-string",
    "nc-mcp-exapp-local-harp-key",
    "short",
    "0123456789abcdef",  # 16 hex characters, a quarter of what openssl produces
    "A" * 64,  # upper case, and not hex at all
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcde",  # 63
)
GOOD_SECRET = "0123456789abcdef" * 4


@pytest.mark.parametrize("name", ["APP_SECRET", "HP_SHARED_KEY"])
def test_the_example_file_hands_out_no_usable_secret(name: str) -> None:
    """CR-02: `cp .env.exapp.example .env.exapp` used to publish the registration secret."""
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        assert not line.strip().startswith(f"{name}="), f"{name} is assignable in the example"


def test_the_example_file_says_that_it_is_read_and_not_copied() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "never copy it" in text


@needs_bash
@pytest.mark.parametrize("weak", WEAK_SECRETS)
def test_a_weak_app_secret_stops_the_bootstrap(tmp_path: Path, weak: str) -> None:
    """The attack path of CR-02, end to end: a placeholder must not become the secret."""
    env_file = tmp_path / ".env.exapp"
    env_file.write_text(f"APP_SECRET={weak}\n", encoding="utf-8")
    script = (
        "set -euo pipefail\n"
        f'ENV_FILE="{env_file.as_posix()}"\n'
        f"{shell_function('require_hex64')}\n"
        f"{shell_function('app_secret')}\n"
        "app_secret\n"
    )

    result = run_bash(script)

    assert result.returncode != 0, f"{weak!r} was accepted as APP_SECRET"
    assert weak not in result.stdout, "the weak value was printed as the secret to use"
    assert "64 lower case hex" in result.stderr


@needs_bash
def test_a_generated_app_secret_is_pinned_across_runs(tmp_path: Path) -> None:
    """The counter probe: the check must not break the reason the value is pinned at all
    (research pitfall 11, a fresh secret locks out whoever still holds the old one)."""
    env_file = tmp_path / ".env.exapp"
    env_file.write_text(f"APP_SECRET={GOOD_SECRET}\n", encoding="utf-8")
    script = (
        "set -euo pipefail\n"
        f'ENV_FILE="{env_file.as_posix()}"\n'
        f"{shell_function('require_hex64')}\n"
        f"{shell_function('app_secret')}\n"
        "app_secret\n"
    )

    result = run_bash(script)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == GOOD_SECRET


@needs_bash
def test_a_missing_env_file_still_generates_a_fresh_secret(tmp_path: Path) -> None:
    script = (
        "set -euo pipefail\n"
        f'ENV_FILE="{(tmp_path / "nothing-here").as_posix()}"\n'
        f"{shell_function('require_hex64')}\n"
        f"{shell_function('app_secret')}\n"
        "app_secret\n"
    )

    result = run_bash(script)

    assert result.returncode == 0, result.stderr
    assert re.fullmatch(r"[0-9a-f]{64}", result.stdout.strip()), result.stdout


def test_the_shared_key_is_validated_like_the_app_secret() -> None:
    """Same class of secret, same gate: a foreign FRP client can attach with it."""
    body = shell_function("harp_shared_key")
    assert "require_hex64 HP_SHARED_KEY" in body


def test_the_documented_development_loop_stays_on_loopback() -> None:
    """WR-12: the same document explains at length why every port binds to 127.0.0.1 and
    then handed out APP_HOST=0.0.0.0, which publishes /init and /enabled to the LAN with
    APP_SECRET as their only guard, and that file sits in the same directory."""
    text = INSTALL_DOC.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Do not"):
            continue
        assert "APP_HOST=0.0.0.0" not in stripped, f"the doc still prescribes {stripped!r}"


def test_the_reverse_proxy_routes_the_exapps_prefix() -> None:
    """Without this rule the installation fails at the heartbeat (research pitfall 7)."""
    text = CADDYFILE.read_text(encoding="utf-8")
    assert "/exapps/*" in text
    assert "appapi-harp:8780" in text
