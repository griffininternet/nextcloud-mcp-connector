"""Project invariants that must hold before any server code exists.

These assertions are cheap and catch the two mistakes that would be expensive later:
a direct ``httpx2`` pin (supply chain policy, see docs/dependency-audit.md) and a test
default that needs Docker.
"""

import tomllib
from pathlib import Path

import pytest

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


@pytest.fixture(scope="module")
def pyproject() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def test_httpx2_is_never_a_direct_dependency(pyproject: dict) -> None:
    declared = list(pyproject["project"]["dependencies"])
    for group in pyproject.get("dependency-groups", {}).values():
        declared.extend(entry for entry in group if isinstance(entry, str))
    offenders = [name for name in declared if name.lower().startswith("httpx2")]
    assert offenders == [], "httpx2 must stay a transitive dependency of mcp, never a direct pin"


def test_httpx_is_pinned_for_our_own_client_code(pyproject: dict) -> None:
    deps = pyproject["project"]["dependencies"]
    assert any(dep.startswith("httpx>=") for dep in deps), (
        "our own HTTP code uses httpx, because respx mocks httpx and not httpx2"
    )


def test_cryptography_is_declared_because_we_import_it(pyproject: dict) -> None:
    """Owner sign-off 2026-08-16: what encrypts the app passwords is not somebody else's
    dependency decision (docs/dependency-audit.md, "Promoting cryptography")."""
    deps = pyproject["project"]["dependencies"]
    assert any(dep.startswith("cryptography>=") for dep in deps)

    crypto = Path(__file__).resolve().parents[2] / "src" / "mcp_connector" / "oauth" / "crypto.py"
    assert "from cryptography" in crypto.read_text(encoding="utf-8"), (
        "the declaration exists because of this import; remove one and remove both"
    )


def test_default_test_run_excludes_integration(pyproject: dict) -> None:
    addopts = pyproject["tool"]["pytest"]["ini_options"]["addopts"]
    assert "not integration" in addopts, "the default suite must run without Docker"


def test_integration_and_matrix_markers_are_declared(pyproject: dict) -> None:
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]
    names = {marker.split(":", 1)[0].strip() for marker in markers}
    assert {"integration", "matrix"} <= names


def test_console_script_nc_mcp_is_declared(pyproject: dict) -> None:
    scripts = pyproject["project"]["scripts"]
    assert scripts["nc-mcp"] == "mcp_connector.entry_stdio:main"


def test_requires_python_is_3_13(pyproject: dict) -> None:
    assert pyproject["project"]["requires-python"] == ">=3.13"


def test_package_exposes_version_without_side_effects() -> None:
    import mcp_connector

    assert mcp_connector.__version__ == pyproject_version()


def pyproject_version() -> str:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_every_exapp_integration_suite_runs_in_the_exapp_job() -> None:
    """WR-11: a check that runs in no job is a check nobody runs.

    The suites that need the HaRP topology skip everywhere else for lack of the ExApp
    variables, so the ``exapp`` job of the workflow is the only place they can run at all.
    The OAuth flow suite, the five checks that prove phase 3 end to end, was not named
    there, so it was green only when somebody ran it by hand.
    """
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    suites = sorted(
        path.name
        for path in (Path(__file__).resolve().parents[2] / "tests" / "integration").glob(
            "*_exapp.py"
        )
    )

    assert suites, "no ExApp integration suite found, the guard would silently pass"
    for name in suites:
        assert name in workflow, f"{name} runs in no CI job"
