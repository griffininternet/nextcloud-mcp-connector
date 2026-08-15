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
from pathlib import Path

import pytest
from lxml import etree

import mcp_connector
from mcp_connector.nextcloud.clients.xml import hardened_parser

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"
START = ROOT / "start.sh"
HEALTHCHECK = ROOT / "healthcheck.sh"
DOCKERIGNORE = ROOT / ".dockerignore"
INFO_XML = ROOT / "appinfo" / "info.xml"

CONTAINER_FILES = (DOCKERFILE, START, HEALTHCHECK)

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
