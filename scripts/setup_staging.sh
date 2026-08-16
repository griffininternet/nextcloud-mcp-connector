#!/usr/bin/env bash
# One time bootstrap of the public staging instance for plan 03-09 (AUTH-04), on a fresh
# virtual machine, as root:
#
#   git clone https://github.com/street1983nk/nextcloud-mcp-connector.git
#   cd nextcloud-mcp-connector
#   export NC_STAGING_DOMAIN=nc-staging.example.com
#   bash scripts/setup_staging.sh
#
# docs/staging-setup.md is the runbook around this script: what to order, how the DNS
# record is set (scripts/staging_dns.sh), what to check afterwards, and how the instance is
# taken down again. Read that one first; this file is what it calls.
#
# Idempotent: every step checks first and skips what is already there. A second run does
# not generate a second set of secrets, does not reinstall Docker and does not reinstall
# Nextcloud. It ends, like the first run, with the three self checks that decide whether a
# hosted connector can do anything with this instance at all.
#
# What it deliberately does not do:
#
#   * open a firewall port. Adding rules to a firewall over ssh is how people lock
#     themselves out of a machine. It names the two commands and stops.
#   * install anything by piping a downloaded script into a shell. Docker is installed from
#     the packages of its own apt repository, with the repository key in
#     /etc/apt/keyrings, so what is installed can be checked afterwards.
#   * touch any other topology. It knows one compose file, and that file carries its own
#     project name, its own volumes and its own network.
set -euo pipefail

cd "$(dirname "$0")/.."

export DEBIAN_FRONTEND=noninteractive

# Not overridable (WR-07): this script starts a topology that publishes ports 80 and 443
# and generates the secrets that belong to it. A forgotten export in the calling shell must
# not be able to aim any of that at another file.
COMPOSE_FILE="compose.staging.yml"
PROJECT_NAME="nc-mcp-staging"
CADDY_CONTAINER="nc-mcp-staging-caddy"
APP_ID="mcp_connector"
# The secret file of the topology: the HaRP shared key, the administrator password and the
# two account passwords. It is read by `docker compose --env-file` and sourced into the
# environment of the bootstrap. Git ignores it, and it never leaves this machine.
ENV_STAGING=".env.staging"
# Written by scripts/bootstrap_exapp.sh --staging: the registration secret and the app
# passwords of the two throwaway accounts. Also git ignored.
ENV_APP=".env.staging.app"

DOMAIN="${NC_STAGING_DOMAIN:?set NC_STAGING_DOMAIN to the public host name of this instance, for example: export NC_STAGING_DOMAIN=nc-staging.example.com}"
ADMIN_USER="${NC_STAGING_ADMIN_USER:-admin}"

CHECKS_FAILED=0
HEADER_FILE=""

cleanup() {
  if [ -n "${HEADER_FILE}" ] && [ -f "${HEADER_FILE}" ]; then
    rm -f "${HEADER_FILE}"
  fi
}
trap cleanup EXIT

step() {
  echo
  echo "== $1 =="
}

# --- preconditions ----------------------------------------------------------------

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: this script installs packages and starts containers, so it needs root." >&2
    echo "Run it as root, or with sudo -E so NC_STAGING_DOMAIN survives." >&2
    return 1
  fi
}

require_repo_files() {
  local missing=0 path
  for path in "${COMPOSE_FILE}" deploy/Caddyfile.staging scripts/bootstrap_exapp.sh; do
    if [ ! -f "${path}" ]; then
      echo "ERROR: ${path} is not here." >&2
      missing=1
    fi
  done
  if [ "${missing}" -ne 0 ]; then
    echo "Run this script from a checkout of the repository: bash scripts/setup_staging.sh" >&2
    return 1
  fi
  if ! grep -q "^name: ${PROJECT_NAME}\$" "${COMPOSE_FILE}"; then
    echo "ERROR: ${COMPOSE_FILE} does not declare the ${PROJECT_NAME} project (WR-07)." >&2
    return 1
  fi
}

# The host name lands in URLs, in the compose interpolation and in the certificate order.
# A typo here is a certificate order that fails, and five failed orders per week per name
# are a rate limit that lasts a week, so the shape is checked before anything starts.
require_domain_shape() {
  if ! printf '%s' "${DOMAIN}" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}$'; then
    echo "ERROR: NC_STAGING_DOMAIN is '${DOMAIN}', which is not a host name." >&2
    echo "Expected something like nc-staging.example.com, without scheme and without path." >&2
    return 1
  fi
}

# Debian and Ubuntu only, because the package installation below is apt. Anything else is
# named and refused rather than half supported: a machine where the Docker install silently
# does nothing produces its error three steps later, in the middle of a certificate order.
require_distribution() {
  if [ ! -r /etc/os-release ]; then
    echo "ERROR: /etc/os-release is missing, so the distribution cannot be determined." >&2
    return 1
  fi
  # shellcheck disable=SC1091
  . /etc/os-release
  DISTRO_ID="${ID:-unknown}"
  DISTRO_CODENAME="${VERSION_CODENAME:-}"
  case "${DISTRO_ID}" in
    debian | ubuntu) ;;
    *)
      echo "ERROR: this script installs packages with apt and knows Debian and Ubuntu." >&2
      echo "This machine reports ID=${DISTRO_ID}. Install Docker and the compose plugin" >&2
      echo "by hand, then start at the 'topology' step of docs/staging-setup.md." >&2
      return 1
      ;;
  esac
  if [ -z "${DISTRO_CODENAME}" ]; then
    echo "ERROR: /etc/os-release carries no VERSION_CODENAME, which the apt source needs." >&2
    return 1
  fi
  echo "distribution: ${DISTRO_ID} ${DISTRO_CODENAME} (${VERSION_ID:-unknown})"
}

# Every IPv4 address this machine holds, one per line.
local_addresses() {
  if command -v ip >/dev/null 2>&1; then
    ip -4 -o addr show scope global | awk '{split($4, a, "/"); print a[1]}'
    return 0
  fi
  if command -v hostname >/dev/null 2>&1; then
    hostname -I 2>/dev/null | tr ' ' '\n' | sed '/^$/d'
  fi
}

# Every IPv4 address the public DNS hands out for the staging name, one per line.
resolved_addresses() {
  getent ahostsv4 "${DOMAIN}" 2>/dev/null | awk '{print $1}' | sort -u
}

# The certificate is issued over HTTP-01 or TLS-ALPN, which means Let's Encrypt connects to
# whatever the name points at. If that is not this machine, the order fails, and a handful
# of failed orders is a rate limit that outlives the test. So this is checked before the
# topology starts, not after.
require_dns_points_here() {
  local resolved local_ips address
  resolved="$(resolved_addresses)"
  if [ -z "${resolved}" ]; then
    echo "ERROR: ${DOMAIN} does not resolve at all." >&2
    echo "Set the A record first (DNS-only, grey cloud): CF_DNS_TOKEN=... CF_ZONE_ID=... \\" >&2
    echo "  NC_STAGING_DOMAIN=${DOMAIN} bash scripts/staging_dns.sh" >&2
    return 1
  fi
  local_ips="$(local_addresses)"
  for address in ${resolved}; do
    if printf '%s\n' "${local_ips}" | grep -Fx "${address}" >/dev/null; then
      echo "dns: ${DOMAIN} points at ${address}, which is an address of this machine"
      return 0
    fi
  done
  echo "ERROR: ${DOMAIN} resolves to:" >&2
  printf '  %s\n' ${resolved} >&2
  echo "and this machine holds:" >&2
  printf '  %s\n' ${local_ips} >&2
  echo "None of them match, so the certificate order would go somewhere else." >&2
  echo "Fix the A record (DNS-only, grey cloud): CF_DNS_TOKEN=... CF_ZONE_ID=... \\" >&2
  echo "  NC_STAGING_DOMAIN=${DOMAIN} bash scripts/staging_dns.sh" >&2
  echo "If this machine is behind NAT and the record is correct, re-run with" >&2
  echo "NC_STAGING_SKIP_DNS_CHECK=1, which skips this check and nothing else." >&2
  return 1
}

# 80 and 443 have to be free, because Caddy binds both. A web server that came with the
# image is the usual reason they are not, and its error message would otherwise appear as
# "port is already allocated" in the middle of the compose output.
require_free_ports() {
  local occupied=0 port listeners
  if ! command -v ss >/dev/null 2>&1; then
    echo "ports: ss is not installed, skipping the check"
    return 0
  fi
  for port in 80 443; do
    listeners="$(ss -ltnH "sport = :${port}" 2>/dev/null || true)"
    if [ -n "${listeners}" ]; then
      echo "ERROR: something already listens on port ${port}:" >&2
      printf '%s\n' "${listeners}" >&2
      occupied=1
    fi
  done
  if [ "${occupied}" -ne 0 ]; then
    echo "Stop that service (a preinstalled nginx or apache is the usual one) and re-run." >&2
    return 1
  fi
  echo "ports: 80 and 443 are free"
}

# A hint, not an action. Opening ports in a firewall over an ssh connection is how a
# machine becomes unreachable, so this names the commands and refuses to continue instead
# of running them.
require_open_firewall() {
  local status
  if ! command -v ufw >/dev/null 2>&1; then
    echo "firewall: no ufw on this machine. If the provider filters in front of it, open"
    echo "          80/tcp and 443/tcp there before continuing."
    return 0
  fi
  status="$(ufw status 2>/dev/null || true)"
  case "${status}" in
    *"Status: active"*) ;;
    *)
      echo "firewall: ufw is installed but inactive, nothing to open"
      return 0
      ;;
  esac
  if printf '%s' "${status}" | grep -E '(^|[^0-9])(80|443)(/tcp)?( |$)' >/dev/null; then
    echo "firewall: ufw is active and carries rules for 80 or 443"
    return 0
  fi
  echo "ERROR: ufw is active and has no rule for 80 or 443." >&2
  echo "The certificate order arrives on port 80 and every client on 443. Open both:" >&2
  echo "  ufw allow 80/tcp" >&2
  echo "  ufw allow 443/tcp" >&2
  echo "Then re-run this script." >&2
  return 1
}

# --- installation -----------------------------------------------------------------

# curl is the only client this script has, and openssl is what generates the secrets. A
# minimal cloud image carries neither, and the point where that would surface otherwise is
# the certificate wait, twenty minutes into the run.
ensure_base_tools() {
  local missing=0 tool
  for tool in curl openssl; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      missing=1
    fi
  done
  if [ "${missing}" -eq 0 ]; then
    echo "tools: curl and openssl are installed"
    return 0
  fi
  apt-get update
  apt-get install -y ca-certificates curl openssl
  echo "tools: installed curl and openssl"
}

ensure_docker() {
  if docker compose version >/dev/null 2>&1 && docker buildx version >/dev/null 2>&1; then
    echo "docker: engine, compose and buildx are installed"
    return 0
  fi
  echo "docker: installing engine, compose plugin and buildx from download.docker.com"
  apt-get update
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  # The repository key, fetched once into the keyring directory. Everything installed
  # below is signed with it, and `apt-key`-style global trust is not used: the source line
  # names this one file, so the key can only vouch for this one repository.
  curl -fsSL "https://download.docker.com/linux/${DISTRO_ID}/gpg" -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/%s %s stable\n' \
    "$(dpkg --print-architecture)" "${DISTRO_ID}" "${DISTRO_CODENAME}" \
    >/etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  echo "docker: installed"
}

# --- secrets ----------------------------------------------------------------------

# One value out of the environment file, without a pipe: `sed | head` would give the sed
# side a closed pipe under pipefail, which is the SIGPIPE flake this repository already
# paid for once.
env_value() {
  local name="$1"
  if [ ! -f "${ENV_STAGING}" ]; then
    return 0
  fi
  awk -F= -v key="${name}" '$1 == key { print substr($0, length(key) + 2) }' "${ENV_STAGING}" |
    tail -n1 | tr -d '\r'
}

# Generated once, then kept. A second run that generated new values would hand the
# topology an administrator password Nextcloud never saw (the image reads it at install
# time only) and account passwords the existing accounts do not have.
ensure_env_staging() {
  local shared_key admin_password alice_password bob_password
  shared_key="$(env_value HP_SHARED_KEY)"
  admin_password="$(env_value NC_STAGING_ADMIN_PASSWORD)"
  alice_password="$(env_value NC_EXAPP_ALICE_PASSWORD)"
  bob_password="$(env_value NC_EXAPP_BOB_PASSWORD)"

  if [ -z "${shared_key}" ]; then
    shared_key="$(openssl rand -hex 32)"
  fi
  if [ -z "${admin_password}" ]; then
    admin_password="$(openssl rand -hex 16)"
  fi
  if [ -z "${alice_password}" ]; then
    alice_password="$(openssl rand -hex 16)"
  fi
  if [ -z "${bob_password}" ]; then
    bob_password="$(openssl rand -hex 16)"
  fi

  # 077 before the file exists, not after: a chmod afterwards leaves a window in which the
  # secrets are world readable on a machine that is on the public internet.
  umask 077
  cat >"${ENV_STAGING}" <<EOF
# Written by scripts/setup_staging.sh. Never commit this file, never copy it off this
# machine. It is the environment file of compose.staging.yml and the environment of
# scripts/bootstrap_exapp.sh --staging.
NC_STAGING_DOMAIN=${DOMAIN}
NC_STAGING_ADMIN_USER=${ADMIN_USER}
NC_STAGING_ADMIN_PASSWORD=${admin_password}
HP_SHARED_KEY=${shared_key}
NC_EXAPP_ALICE_PASSWORD=${alice_password}
NC_EXAPP_BOB_PASSWORD=${bob_password}
EOF
  chmod 600 "${ENV_STAGING}"
  echo "secrets: ${ENV_STAGING} is in place (600, git ignored)"
}

# --- topology ---------------------------------------------------------------------

dc() {
  docker compose --env-file "${ENV_STAGING}" -f "${COMPOSE_FILE}" "$@"
}

start_topology() {
  dc up -d --wait
  echo "topology: up"
}

# The first request over https is also the proof that DNS, firewall and the certificate
# order worked. Caddy answers with the certificate as soon as the order finished, which
# takes a few seconds on a name that resolves correctly.
wait_for_tls() {
  local attempt code
  for attempt in $(seq 1 40); do
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "https://${DOMAIN}/status.php" 2>/dev/null || echo "000")"
    if [ "${code}" = "200" ]; then
      echo "tls: https://${DOMAIN} answers with a valid certificate"
      return 0
    fi
    echo "waiting for the certificate and the server (${attempt}/40, last status ${code})"
    sleep 10
  done
  echo "ERROR: https://${DOMAIN}/status.php never answered 200." >&2
  echo "Look at the certificate order: docker compose --env-file ${ENV_STAGING} \\" >&2
  echo "  -f ${COMPOSE_FILE} logs --tail=100 caddy" >&2
  echo "The three usual reasons are a proxied (orange cloud) A record, a closed port 80" >&2
  echo "and a name that points at another machine." >&2
  return 1
}

install_exapp() {
  # The bootstrap needs the generated passwords and the shared key in its environment, and
  # they live in exactly one place. Sourcing beats passing them as arguments: an argument
  # is world readable in `ps aux` for the whole call (WR-06).
  set -a
  # shellcheck disable=SC1090
  . "./${ENV_STAGING}"
  set +a
  bash scripts/bootstrap_exapp.sh --staging
}

# --- self checks ------------------------------------------------------------------

check_status() {
  local label="$1" url="$2" expected="$3" code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "${url}" 2>/dev/null || echo "000")"
  if [ "${code}" = "${expected}" ]; then
    printf 'PASS  %-34s %s\n' "${label}" "${code}"
    return 0
  fi
  printf 'FAIL  %-34s %s (expected %s)\n' "${label}" "${code}" "${expected}"
  CHECKS_FAILED=1
}

# The one check that is more than a status code: an MCP client learns where to authorize
# from this header, and a 401 without it is a dead end for every hosted connector.
check_challenge() {
  local url="$1" code
  HEADER_FILE="$(mktemp)"
  code="$(curl -sS -o /dev/null -D "${HEADER_FILE}" -w '%{http_code}' --max-time 20 \
    -X POST -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    --data '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' "${url}" 2>/dev/null || echo "000")"
  if [ "${code}" != "401" ]; then
    printf 'FAIL  %-34s %s (expected 401)\n' "/mcp without a token" "${code}"
    CHECKS_FAILED=1
    return 0
  fi
  if grep -i 'resource_metadata=' "${HEADER_FILE}" >/dev/null; then
    printf 'PASS  %-34s 401 with resource_metadata\n' "/mcp without a token"
    return 0
  fi
  printf 'FAIL  %-34s 401 without a resource_metadata pointer\n' "/mcp without a token"
  CHECKS_FAILED=1
}

self_checks() {
  local base="https://${DOMAIN}/exapps/${APP_ID}"
  check_status "protected resource document" "${base}/.well-known/oauth-protected-resource/mcp" 200
  check_status "authorization server document" "${base}/.well-known/oauth-authorization-server" 200
  check_challenge "${base}/mcp"
  echo
  echo "The two canonical root paths, the open question of plan 03-09 (assumption A2)."
  echo "They answer 200 while the two rewrite rules in deploy/Caddyfile.staging are active:"
  check_status "root: protected resource" \
    "https://${DOMAIN}/.well-known/oauth-protected-resource/exapps/${APP_ID}/mcp" 200
  check_status "root: authorization server" \
    "https://${DOMAIN}/.well-known/oauth-authorization-server/exapps/${APP_ID}" 200
}

# --- run --------------------------------------------------------------------------

echo "== staging bootstrap for ${DOMAIN} =="

step "preconditions"
require_root
require_repo_files
require_domain_shape
require_distribution
if [ "${NC_STAGING_SKIP_DNS_CHECK:-0}" = "1" ]; then
  echo "dns: check skipped on request (NC_STAGING_SKIP_DNS_CHECK=1)"
else
  require_dns_points_here
fi
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -Fx "${CADDY_CONTAINER}" >/dev/null; then
  echo "ports: ${CADDY_CONTAINER} is already running and holds 80 and 443"
else
  require_free_ports
fi
require_open_firewall

step "packages"
ensure_base_tools
ensure_docker

step "secrets"
ensure_env_staging

step "topology"
start_topology
wait_for_tls

step "exapp"
install_exapp

step "self checks"
self_checks

echo
if [ "${CHECKS_FAILED}" -ne 0 ]; then
  echo "At least one check failed. The instance is not ready for a connector yet." >&2
  echo "Logs: docker compose --env-file ${ENV_STAGING} -f ${COMPOSE_FILE} logs --tail=100" >&2
  exit 1
fi

echo "Ready. This is the URL that goes into Claude.ai and into ChatGPT, exactly, with"
echo "/mcp and without a trailing slash:"
echo
echo "  https://${DOMAIN}/exapps/${APP_ID}/mcp"
echo
echo "The sign in on the consent screen uses one of the two throwaway accounts (alice or"
echo "bob); their passwords are in ${ENV_STAGING}, the administrator password as well."
echo "The app passwords and the registration secret are in ${ENV_APP}."
echo
echo "When the measurement is done, throw the instance away, do not keep it running:"
echo "  docker compose --env-file ${ENV_STAGING} -f ${COMPOSE_FILE} down -v"
echo "and delete the machine and the DNS record (docs/staging-setup.md, 'Teardown')."
