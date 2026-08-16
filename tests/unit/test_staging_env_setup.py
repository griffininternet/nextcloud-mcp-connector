"""Guards for the public staging instance of plan 03-09 (compose.staging.yml and friends).

The local topology of ``compose.exapp.yml`` may be sloppy in ways this one may not: it
listens on loopback, so a weak password or a disabled bruteforce guard reaches nobody. The
staging instance is on the public internet from its first minute, and it exists to be
handed to two external companies. Every assertion in this file is one of the differences
that follow from that:

* the reverse proxy is the only service with a public port, and the registry keeps the
  loopback binding it needs to stay an unauthenticated write target nobody can reach,
* the certificates live in a named volume, because a fresh certificate on every restart
  runs into a rate limit that lasts a week and would end the measurement,
* the two secrets of the topology have no default at all, because a documented password on
  a public Nextcloud is a documented takeover,
* the host name is a variable, never a literal, so this public repository never carries the
  owner's infrastructure,
* the two rewrite rules for the canonical discovery paths are present, because whether the
  hosted connectors need them is the open question the whole plan measures (assumption A2),
* and the DNS token never touches an argv, because ``ps aux`` is world readable.

Pure file assertions plus a few functions cut out of the shell scripts and run on their
own. Nothing here starts Docker, resolves a name or talks to an API.
"""

import ipaddress
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_STAGING = ROOT / "compose.staging.yml"
COMPOSE_EXAPP = ROOT / "compose.exapp.yml"
CADDY_STAGING = ROOT / "deploy" / "Caddyfile.staging"
SETUP = ROOT / "scripts" / "setup_staging.sh"
DNS = ROOT / "scripts" / "staging_dns.sh"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_exapp.sh"
GITIGNORE = ROOT / ".gitignore"
DOC = ROOT / "docs" / "staging-setup.md"

STAGING_FILES = (COMPOSE_STAGING, CADDY_STAGING, SETUP, DNS, DOC)

#: Files that are published in this repository and must never carry the host name of a
#: real staging instance. The name is a variable everywhere, and this is what keeps it one.
NAME_FREE_FILES = (COMPOSE_STAGING, CADDY_STAGING, SETUP, DNS, DOC)

#: Last labels that make a match of the host name search a file of this repository rather
#: than a host name. compose.staging.yml and .env.staging.app are the two that matter.
FILE_SUFFIXES = frozenset({"yml", "yaml", "sh", "md", "py", "json", "app", "env", "txt"})

#: The two ports the reverse proxy publishes, and the only ones this topology may publish
#: on a public interface. 80 is not optional: the ACME HTTP-01 challenge arrives there.
PUBLIC_PORTS = frozenset({"80:80", "443:443"})

#: The two canonical discovery paths of RFC 9728 and RFC 8414 for an issuer with a path,
#: and the ExApp paths they are rewritten to. Both sit on the domain root, both belong to
#: Nextcloud, and both answer 404 without a rule (spike-discovery.md).
REWRITES = (
    (
        "/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp",
        "/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp",
    ),
    (
        "/.well-known/oauth-authorization-server/exapps/mcp_connector",
        "/exapps/mcp_connector/.well-known/oauth-authorization-server",
    ),
)


def compose_services(text: str) -> dict[str, str]:
    """Split the services mapping of a compose file into one text block per service.

    Hand written instead of parsed, for the same reason as in test_exapp_env_setup.py: the
    project has no YAML dependency, and the file this reads is written by hand and stays
    inside the two space indentation the rest of the repository uses.
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


def shell_function(name: str, path: Path) -> str:
    """Cut one function out of a shell script so a test can run it on its own."""
    text = path.read_text(encoding="utf-8")
    opening = f"\n{name}() {{\n"
    start = text.index(opening)
    end = text.index("\n}\n", start)
    return text[start + 1 : end + 3]


def find_bash() -> str | None:
    """A bash that can actually run this repository's scripts, or ``None``."""
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


@pytest.mark.parametrize("path", list(STAGING_FILES))
def test_the_staging_artefacts_are_checked_in(path: Path) -> None:
    assert path.is_file(), f"{path.name} is missing"


@pytest.mark.parametrize("path", [COMPOSE_STAGING, CADDY_STAGING, SETUP, DNS])
def test_no_crlf_in_the_staging_files(path: Path) -> None:
    """The staging host runs Linux and this repository is edited on Windows. A CR turns
    the shebang into a "not found" and the Caddyfile into a parse error, and both would
    surface on a machine that has no editor and no patience."""
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} has CRLF endings; bash and docker compose exec both break on the CR"
    )


def test_the_staging_topology_carries_its_own_project_name() -> None:
    """Three topologies live in this repository now. Without a project name compose
    derives it from the directory, all three land in the same project, and a `down` on one
    stops the containers of the others (T-02-34)."""
    lines = COMPOSE_STAGING.read_text(encoding="utf-8").splitlines()
    names = [line for line in lines if line.startswith("name:")]
    assert names == ["name: nc-mcp-staging"]


def test_the_registry_is_not_published_publicly() -> None:
    """The registry has neither authentication nor TLS, and the deploy daemon runs what it
    serves with APP_SECRET in its environment (WR-09). On a public machine a 0.0.0.0
    binding here is an open write target for the image that becomes the ExApp."""
    services = compose_services(COMPOSE_STAGING.read_text(encoding="utf-8"))
    assert "registry" in services, f"services found: {sorted(services)}"
    ports = published_ports(services["registry"])
    assert ports, "the registry publishes nothing at all any more, check the parser"
    for port in ports:
        assert port.startswith("127.0.0.1:"), f"registry port {port!r} is not on loopback"


def test_the_reverse_proxy_is_the_only_service_with_a_public_port() -> None:
    """The one deliberate difference to the local topology, and it stays one service wide:
    everything else is reachable through Caddy or not at all."""
    text = COMPOSE_STAGING.read_text(encoding="utf-8")
    services = compose_services(text)
    public = {
        service: [port for port in published_ports(body) if not port.startswith("127.0.0.1:")]
        for service, body in services.items()
    }
    exposed = {service: ports for service, ports in public.items() if ports}
    assert set(exposed) == {"caddy"}, f"public ports outside the reverse proxy: {exposed}"
    assert set(exposed["caddy"]) == PUBLIC_PORTS, (
        f"the reverse proxy publishes {exposed['caddy']}, expected {sorted(PUBLIC_PORTS)}"
    )


def test_the_deploy_daemon_publishes_no_port() -> None:
    """Caddy reaches HaRP inside the compose network. A published port here would be the
    ExApp proxy on the public internet, without TLS in front of it."""
    services = compose_services(COMPOSE_STAGING.read_text(encoding="utf-8"))
    assert "ports:" not in services["appapi-harp"]


def test_the_certificates_survive_a_restart() -> None:
    """Let's Encrypt answers the sixth certificate for one name within a week with a rate
    limit that lasts a week. Without a named volume for /data every `up` is a new order,
    and the sixth restart of the instance ends the measurement."""
    text = COMPOSE_STAGING.read_text(encoding="utf-8")
    services = compose_services(text)
    mounts = [line.strip().lstrip("- ") for line in services["caddy"].splitlines()]
    data_mounts = [mount for mount in mounts if mount.endswith(":/data")]
    assert data_mounts, "the reverse proxy mounts nothing at /data, so certificates are lost"
    volume = data_mounts[0].split(":", 1)[0]
    assert not volume.startswith("."), f"{volume!r} is a bind mount, not a named volume"
    assert re.search(rf"^\s{{2}}{re.escape(volume)}:\s*$", text, flags=re.MULTILINE), (
        f"the volume {volume!r} is used but never declared"
    )


@pytest.mark.parametrize(
    ("service", "variable"),
    [("appapi-harp", "HP_SHARED_KEY"), ("nextcloud", "NEXTCLOUD_ADMIN_PASSWORD")],
)
def test_the_secrets_of_a_public_instance_have_no_default(service: str, variable: str) -> None:
    """WR-11, and here it is sharper than on the local topology: a default in a public
    repository is a published credential of a machine anyone can reach. Both variables
    abort the `up` instead, and scripts/setup_staging.sh generates them."""
    services = compose_services(COMPOSE_STAGING.read_text(encoding="utf-8"))
    lines = [
        line.strip()
        for line in services[service].splitlines()
        if line.strip().startswith(f"{variable}:")
    ]
    assert lines, f"{variable} is not set for {service} any more"
    assert ":?" in lines[0], f"{lines[0][:60]!r} carries a default"
    assert ":-" not in lines[0], f"{lines[0][:60]!r} carries a fallback value"


def real_host_names(text: str) -> list[str]:
    """Every staging host name in ``text`` that is neither an example name nor a file name.

    A function rather than a chain of asserts, so the test below it can feed the gate a
    text that carries a real name and prove that it actually fires.
    """
    found = re.findall(
        r"\b[a-z0-9][a-z0-9-]*staging[a-z0-9-]*(?:\.[a-z0-9-]+)+", text, flags=re.IGNORECASE
    )
    return [
        name
        for name in found
        # The file names of this feature look like host names to a regular expression
        # (compose.staging.yml, .env.staging.app), so the last label decides: a file
        # extension is a file, anything else is a name that resolves somewhere.
        if name.rsplit(".", 1)[-1].lower() not in FILE_SUFFIXES
        and not name.endswith((".example.com", ".example.org", ".example.net"))
    ]


@pytest.mark.parametrize("path", list(NAME_FREE_FILES))
def test_the_public_host_name_is_never_written_into_the_repository(path: Path) -> None:
    """The instance is a throwaway with a different name every time, and this repository is
    public. Every file takes the name from NC_STAGING_DOMAIN; the only host names that may
    appear are the reserved example ones."""
    unexpected = real_host_names(path.read_text(encoding="utf-8"))
    assert not unexpected, f"{path.name} names a real host: {sorted(set(unexpected))}"


def test_the_host_name_gate_sees_a_real_name_between_the_file_names() -> None:
    """The counter probe: the filter that lets compose.staging.yml pass must not let the
    one line that matters pass with it."""
    text = (
        "docker compose -f compose.staging.yml up\n"
        "cat .env.staging.app\n"
        "export NC_STAGING_DOMAIN=nc-staging.example.com\n"
        "curl https://nc-staging.owner-domain.dev/exapps/mcp_connector/mcp\n"
    )

    assert real_host_names(text) == ["nc-staging.owner-domain.dev"]


def test_the_topology_reads_the_host_name_from_the_environment() -> None:
    text = COMPOSE_STAGING.read_text(encoding="utf-8")
    assert "${NC_STAGING_DOMAIN" in text
    assert "{$NC_STAGING_DOMAIN}" in CADDY_STAGING.read_text(encoding="utf-8"), (
        "the Caddyfile does not take the site address from the environment"
    )


def test_only_the_reverse_proxy_is_a_trusted_proxy() -> None:
    """WR-08: the ExApp container is hung into the same network by the deploy daemon and it
    is the component that processes untrusted input. On a public instance the client
    address decides bruteforce counters and audit entries, so it must come from the proxy
    and from nothing else."""
    text = COMPOSE_STAGING.read_text(encoding="utf-8")
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
    """IN-03: without an ip_range Docker may hand the fixed proxy address to the next
    container that comes up, and the ExApp container is one of them."""
    text = COMPOSE_STAGING.read_text(encoding="utf-8")
    ranges = re.findall(r"^\s*ip_range:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    assert ranges, "the ipam configuration carries no ip_range for dynamic assignment"
    dynamic = ipaddress.ip_network(ranges[0])
    statics = re.findall(r"^\s*ipv4_address:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    assert statics, "no statically assigned address found, the trust anchor is gone"
    for address in statics:
        assert ipaddress.ip_address(address) not in dynamic, (
            f"static address {address} lies inside the dynamic range {dynamic}"
        )


def test_the_two_topologies_do_not_share_a_subnet() -> None:
    """They are never meant to run on the same host, and an overlap between them is the
    kind of failure that reads like a network bug for an afternoon."""
    subnets = []
    for path in (COMPOSE_EXAPP, COMPOSE_STAGING):
        found = re.findall(
            r"^\s*- subnet:\s*(\S+)\s*$", path.read_text(encoding="utf-8"), flags=re.MULTILINE
        )
        assert found, f"{path.name} declares no subnet"
        subnets.append(ipaddress.ip_network(found[0]))
    assert not subnets[0].overlaps(subnets[1]), f"{subnets[0]} overlaps {subnets[1]}"


@pytest.mark.parametrize(("source", "target"), list(REWRITES))
def test_the_reverse_proxy_carries_both_canonical_rewrites(source: str, target: str) -> None:
    """Whether the hosted connectors need these two is assumption A2, and the instance
    exists to answer it. It answers it with the rules on and then with them off, so both
    have to be there and both have to be one commented block away from gone."""
    text = CADDY_STAGING.read_text(encoding="utf-8")
    assert f"route {source} {{" in text, f"no exact route for {source}"
    assert f"rewrite * {target}" in text, f"{source} is not rewritten to {target}"


def test_the_canonical_rewrites_stand_before_the_general_exapps_route() -> None:
    """The first matching route wins. Behind /exapps/* both rules are dead code."""
    text = CADDY_STAGING.read_text(encoding="utf-8")
    general = text.index("route /exapps/*")
    for source, _ in REWRITES:
        assert text.index(f"route {source} {{") < general, f"{source} stands after /exapps/*"


def test_the_streaming_route_keeps_its_timeout() -> None:
    """Streamable HTTP holds a response open for the lifetime of a session. The default
    read timeout cuts it, and the client sees a truncated body instead of an error."""
    text = CADDY_STAGING.read_text(encoding="utf-8")
    assert "read_timeout 1800s" in text
    assert "appapi-harp:8780" in text


def test_the_staging_site_is_not_a_bare_port() -> None:
    """A site address of :80 would serve the instance over plaintext http and would never
    ask for a certificate. The whole point of this topology is that it is reachable over
    TLS by two external clients."""
    text = CADDY_STAGING.read_text(encoding="utf-8")
    assert not re.search(r"^:\d+ \{", text, flags=re.MULTILINE), "the site listens on a bare port"


def test_the_access_log_is_switched_on() -> None:
    """The access log is the measuring instrument of plan 03-09: which discovery path a
    connector tries, in which order, with which status. Caddy logs nothing without it."""
    text = CADDY_STAGING.read_text(encoding="utf-8")
    assert re.search(r"^\tlog \{", text, flags=re.MULTILINE), "no access log in the site block"


@pytest.mark.parametrize("path", [SETUP, DNS])
def test_the_staging_scripts_stop_on_the_first_error(path: Path) -> None:
    assert "set -euo pipefail" in path.read_text(encoding="utf-8")


def test_the_dns_token_never_reaches_a_command_line() -> None:
    """WR-06: argv is world readable in `ps aux` for the whole call, and this token can
    rewrite every record of the zone. It travels through a curl configuration file on
    stdin, which is private to the two processes at its ends."""
    text = DNS.read_text(encoding="utf-8")
    assert "--config -" in text, "the token does not travel through a curl config on stdin"
    assert '-H "Authorization' not in text, "an Authorization header sits in the argv"
    assert "-H 'Authorization" not in text
    assert "${CF_DNS_TOKEN" in text, "the token is not read from the environment"
    assert 'CF_DNS_TOKEN="$1"' not in text, "the token is read from an argument"


def test_the_dns_record_is_never_proxied() -> None:
    """Behind the Cloudflare proxy the ACME challenge never arrives, and the streaming
    response of the MCP transport gets a second opinion on when it is over."""
    text = DNS.read_text(encoding="utf-8")
    assert '"proxied":false' in text
    assert '"proxied":true' not in text


def test_the_dns_script_updates_instead_of_adding_a_second_record() -> None:
    """Two A records for one name are a name that answers with a different address every
    other query, and half of those answers are a certificate order that fails."""
    text = DNS.read_text(encoding="utf-8")
    assert "cf_api PUT" in text, "an existing record is never updated"
    assert "cf_api POST" in text, "a missing record is never created"
    assert "RECORD_ID" in text


def test_the_setup_script_writes_its_secrets_before_anyone_can_read_them() -> None:
    """A chmod after the write leaves a window in which the file is world readable, on a
    machine that is on the public internet."""
    text = SETUP.read_text(encoding="utf-8")
    umask = text.index("umask 077")
    write = text.index('cat >"${ENV_STAGING}"')
    assert umask < write, "the umask is set after the secret file was written"
    assert 'chmod 600 "${ENV_STAGING}"' in text


def test_the_setup_script_installs_nothing_by_piping_a_download_into_a_shell() -> None:
    """A `curl ... | sh` is an unverified script running as root, and this one runs on the
    machine that then holds the Docker socket."""
    text = SETUP.read_text(encoding="utf-8")
    for forbidden in ("| sh", "| bash", "|sh", "|bash"):
        assert forbidden not in text, f"{forbidden!r} pipes something into a shell"


def test_the_setup_script_checks_what_a_connector_needs() -> None:
    """The three self checks are the difference between "it started" and "a hosted
    connector can do something with it": the protected resource document, the authorization
    server document, and a 401 that points at the first of them."""
    text = SETUP.read_text(encoding="utf-8")
    assert ".well-known/oauth-protected-resource/mcp" in text
    assert ".well-known/oauth-authorization-server" in text
    assert "resource_metadata=" in text
    assert "401" in text


@pytest.mark.parametrize("name", [".env.staging", ".env.staging.app"])
def test_the_staging_secret_files_are_git_ignored(name: str) -> None:
    """One carries the shared key, the administrator password and two account passwords,
    the other the registration secret and two working app passwords."""
    lines = [line.strip() for line in GITIGNORE.read_text(encoding="utf-8").splitlines()]
    assert name in lines, f"{name} is not git ignored"


def test_the_bootstrap_publishes_the_public_url_on_the_staging_instance() -> None:
    """The 03-08 finding: the authorization server calls itself by NC_MCP_PUBLIC_URL, and
    an instance that names 127.0.0.1 there is one no client can connect to, no matter how
    correct everything else is."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert 'BASE_URL="https://${STAGING_DOMAIN}"' in text
    assert 'PUBLIC_URL="${NC_EXAPP_PUBLIC_URL:-${BASE_URL}/exapps/${APP_ID}}"' in text
    assert "NC_MCP_PUBLIC_URL" in text


def test_the_public_instance_keeps_its_bruteforce_guard() -> None:
    """The guard is switched off on the local topology because the negative tests produce
    401s on purpose and nobody can reach it. Neither reason holds for an instance on the
    public internet that carries two accounts with test data."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "DISABLE_BRUTEFORCE=0" in text, "the staging branch does not keep the guard on"
    disable = text.index("occ config:system:set auth.bruteforce.protection.enabled")
    guard = text.index('if [ "${DISABLE_BRUTEFORCE}" -eq 1 ]; then')
    assert guard < disable, "the guard is disabled unconditionally"


def test_the_staging_topology_is_chosen_by_a_flag_not_by_the_environment() -> None:
    """Same reason COMPOSE_FILE is not overridable (WR-07): a forgotten export in a shell
    must not be able to point a run at the public instance, or at the local one."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "--staging) STAGING_MODE=1 ;;" in text
    assert 'STAGING_MODE="${' not in text, "the mode can be set from the environment"


@needs_bash
@pytest.mark.parametrize(
    ("value", "expected_code"),
    [
        ("nc-staging.example.com", 0),
        ("example.org", 0),
        ("https://nc-staging.example.com", 1),
        ("nc-staging.example.com/exapps/mcp_connector", 1),
        ("localhost", 1),
        ("", 1),
        ('example.com","evil":"1', 1),
    ],
    ids=[
        "a host name",
        "a bare domain",
        "a URL",
        "a host name with a path",
        "a name without a dot",
        "nothing",
        "a JSON injection",
    ],
)
def test_the_host_name_gate_refuses_anything_that_is_not_a_host(
    value: str, expected_code: int
) -> None:
    """IN-07: the name is interpolated into every URL this app publishes about itself and
    into the registration payload. A scheme or a path in it produces a discovery document
    no client can use, and the last case produces a payload AppAPI would adopt."""
    script = (
        "set -euo pipefail\n"
        f"{shell_function('require_host_name', BOOTSTRAP)}\n"
        f"require_host_name '{value}'\n"
    )

    result = run_bash(script)

    assert result.returncode == expected_code, result.stdout + result.stderr


@needs_bash
@pytest.mark.parametrize(
    ("value", "expected_code"),
    [
        ("0123456789abcdef0123456789abcdef", 0),
        ("alice-test-pw-01", 1),
        ("", 1),
        ("short-one", 1),
    ],
    ids=[
        "a generated password",
        "the documented local test password",
        "nothing",
        "a hand written one",
    ],
)
def test_the_public_accounts_refuse_the_documented_test_passwords(
    value: str, expected_code: int
) -> None:
    """The local topology's account passwords are printed in this repository, and on a
    public instance they are the whole distance between the internet and two accounts."""
    script = (
        "set -euo pipefail\n"
        f"{shell_function('require_generated_password', BOOTSTRAP)}\n"
        f"require_generated_password NC_EXAPP_ALICE_PASSWORD '{value}'\n"
    )

    result = run_bash(script)

    assert result.returncode == expected_code, result.stdout + result.stderr


def test_the_runbook_says_what_the_instance_is_not() -> None:
    """A staging instance that stays up is a Nextcloud with the Docker socket mounted, a
    disabled-by-nobody registry and two throwaway accounts, on the public internet. The
    document has to say that in one place a reader cannot miss."""
    text = DOC.read_text(encoding="utf-8")
    assert "What this instance is not" in text
    assert "down -v" in text, "the runbook never says how the instance is thrown away"
    assert "scripts/setup_staging.sh" in text
    assert "scripts/staging_dns.sh" in text
