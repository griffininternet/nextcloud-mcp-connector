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

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from lxml import etree

import mcp_connector
from mcp_connector.nextcloud.clients.xml import hardened_parser

ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / ".env.exapp.example"
DOCKERFILE = ROOT / "Dockerfile"
START = ROOT / "start.sh"
HEALTHCHECK = ROOT / "healthcheck.sh"
DOCKERIGNORE = ROOT / ".dockerignore"
INFO_XML = ROOT / "appinfo" / "info.xml"
COMPOSE_EXAPP = ROOT / "compose.exapp.yml"
CADDYFILE = ROOT / "deploy" / "Caddyfile"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_exapp.sh"

CONTAINER_FILES = (DOCKERFILE, START, HEALTHCHECK)

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
    if len(routes) != 2:
        problems.append(f"{len(routes)} routes declared, this phase opens exactly two")

    for route in routes:
        url = (route.findtext("url") or "").strip()
        access_level = (route.findtext("access_level") or "").strip()
        bruteforce = (route.findtext("bruteforce_protection") or "").strip()

        if url in WIDE_URLS:
            problems.append(f"route {url!r} matches everything")
        if access_level == "PUBLIC" and not url.startswith("^/"):
            problems.append(f"public route {url!r} is not anchored at a path")
        if "401" in bruteforce:
            problems.append(f"route {url!r} throttles on 401, which breaks OAuth discovery")
        for path in LIFECYCLE_PATHS:
            if _matches(url, path):
                problems.append(f"route {url!r} exposes the lifecycle path {path}")

    return problems


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


def shell_function(name: str) -> str:
    """Cut one function out of the bootstrap script so a test can run it on its own.

    The alternative would be sourcing the whole file, and the whole file talks to Docker.
    The cut is exact: the script writes every function as ``name() {`` on its own line and
    closes it with a ``}`` in column one, and the assertions below fail loudly if that
    ever stops being true.
    """
    text = BOOTSTRAP.read_text(encoding="utf-8")
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


@pytest.mark.parametrize("path", [DOCKERFILE, START, HEALTHCHECK, DOCKERIGNORE, INFO_XML])
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


def test_the_entrypoint_is_the_harp_start_script() -> None:
    entrypoints = instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ENTRYPOINT")
    assert entrypoints, "the Dockerfile declares no ENTRYPOINT"
    assert "/start.sh" in entrypoints[-1]
    assert "nc-mcp-exapp" in entrypoints[-1]


def test_the_frpc_download_is_checksum_verified() -> None:
    """T-02-SC: frpc is a foreign binary, and a release asset can be replaced."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "sha256sum -c" in text, "the frpc archive is unpacked without a checksum check"
    assert "FRP_AMD64_SHA256" in text
    assert "FRP_ARM64_SHA256" in text


@pytest.mark.parametrize("name", FORBIDDEN_ENV_NAMES)
def test_no_secret_is_baked_into_the_image(name: str) -> None:
    """T-02-23: secrets come from the deploy environment, never from a layer."""
    for value in instruction_values(DOCKERFILE.read_text(encoding="utf-8"), "ENV"):
        assert name not in value, f"the image sets {name} in an ENV instruction"


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


def test_the_manifest_declares_exactly_the_two_routes_of_this_phase(
    manifest_root: etree._Element,
) -> None:
    routes = [
        ((route.findtext("url") or "").strip(), (route.findtext("access_level") or "").strip())
        for route in manifest_root.findall(".//route")
    ]
    assert routes == [("^/mcp/?$", "USER"), ("^/\\.well-known/", "PUBLIC")]


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


def test_the_deploy_daemon_publishes_no_port() -> None:
    """Caddy reaches HaRP inside the compose network; a published port only adds reach."""
    services = compose_services(COMPOSE_EXAPP.read_text(encoding="utf-8"))
    assert "appapi-harp" in services, f"services found: {sorted(services)}"
    assert "ports:" not in services["appapi-harp"]


def test_the_bootstrap_never_reaches_into_the_other_topology() -> None:
    """T-02-34: the other test instance is in daily use and must survive this script."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "compose.test.yml" not in text
    assert "down -v" not in text


# --- the secret handling around the registration (CR-02) --------------------------

needs_bash = pytest.mark.skipif(BASH is None, reason="no usable bash on this host")

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


def test_the_reverse_proxy_routes_the_exapps_prefix() -> None:
    """Without this rule the installation fails at the heartbeat (research pitfall 7)."""
    text = CADDYFILE.read_text(encoding="utf-8")
    assert "/exapps/*" in text
    assert "appapi-harp:8780" in text
