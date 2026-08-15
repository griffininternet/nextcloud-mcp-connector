#!/usr/bin/env bash
# Install this app as a real ExApp into the HaRP topology from compose.exapp.yml.
#
#   docker compose -f compose.exapp.yml up -d --wait   # 1. topology, waits for healthy
#   bash scripts/bootstrap_exapp.sh                    # 2. AppAPI, daemon, image, ExApp
#   docker compose -f compose.exapp.yml down           # 3. stop, keep the data volume
#
# Step 2 builds the image and pushes it into the local registry itself, so the three
# commands above are the whole installation.
#
# Idempotent by design: every step checks first and skips what already exists, so a second
# run is a no-op apart from a fresh app password in .env.exapp. That file is git-ignored;
# .env.exapp.example documents the variable names.
#
# The development loop without a container image:
#
#   bash scripts/bootstrap_exapp.sh --manual
#
# registers a manual-install daemon and the app with a fixed secret and a fixed port, so a
# locally started `nc-mcp-exapp` process serves the requests and no rebuild is needed per
# iteration. The fixed secret is the point: a re-registration hands out a new one, and a
# process that still holds the old one answers 401 to everything (research pitfall 11).
#
# This script only ever talks to the topology named above. It never stops a container of
# the other test topology in this repository and never destroys a volume, which is why
# neither that file name nor a "down" command appears anywhere below.
set -euo pipefail

cd "$(dirname "$0")/.."

# Git Bash rewrites arguments that look like Unix paths before the process sees them, and
# the route regexes and the container paths below are exactly such arguments. No effect on
# Linux, where the variable is simply unknown.
export MSYS_NO_PATHCONV=1

# Not overridable, and checked below (WR-07). This script creates users, hands out app
# passwords and switches `auth.bruteforce.protection.enabled` off. All three are fine on
# the throwaway topology of this one file and unacceptable on any other instance, so a
# forgotten `export COMPOSE_FILE=...` in the calling shell must not be able to aim it at
# the other topology of this repository, which is in daily use.
COMPOSE_FILE="compose.exapp.yml"
SERVICE="nextcloud"
HARP_CONTAINER="${HARP_CONTAINER:-nc-mcp-exapp-harp}"
HOST_PORT="${NC_EXAPP_PORT:-8081}"
# The name of the compose network, as written in compose.exapp.yml. The deploy daemon
# attaches the ExApp container to it, which is how HaRP and Nextcloud reach the app.
NETWORK_NAME="${NC_EXAPP_NETWORK:-nc-mcp-exapp-net}"
DAEMON_NAME="harp_proxy_docker"
MANUAL_DAEMON_NAME="manual_install"
APP_ID="mcp_connector"
APP_NAME="MCP Connector"
# Loopback registry from compose.exapp.yml. The Docker daemon of the host treats a
# 127.0.0.1 registry as an allowed insecure one without any extra configuration.
REGISTRY="${NC_EXAPP_REGISTRY:-127.0.0.1:5000}"
IMAGE_NAME="${APP_ID}"
# 23000 to 23999 is the port range the FRP server inside HaRP accepts (allowPorts in its
# frps.toml), and it is the same range AppAPI picks from when a registration carries no
# port. A port outside it is answered with "start error: port not allowed" by frpc, and
# then HAProxy has no backend and every heartbeat is a 503.
APP_PORT="${NC_EXAPP_APP_PORT:-23000}"
MANUAL_APP_PORT="${NC_EXAPP_MANUAL_PORT:-23001}"
# At least ten characters: Nextcloud's password policy rejects anything shorter with
# "Password needs to be at least 10 characters long." and occ exits 1.
ALICE_PASSWORD="${NC_EXAPP_ALICE_PASSWORD:-alice-test-pw-01}"
BOB_PASSWORD="${NC_EXAPP_BOB_PASSWORD:-bob-test-pw-01}"
TOKEN_NAME="mcp-exapp"
ENV_FILE="${ENV_FILE:-.env.exapp}"
# Filled by ensure_image and read by verify_image_digest right before the registration.
IMAGE_DIGEST=""

MANUAL_MODE=0
if [ "${1:-}" = "--manual" ]; then
  MANUAL_MODE=1
fi

ensure_own_topology() {
  if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "ERROR: ${COMPOSE_FILE} is not here. Run this script from the repository root." >&2
    return 1
  fi
  if ! grep -q '^name: nc-mcp-exapp$' "${COMPOSE_FILE}"; then
    echo "ERROR: ${COMPOSE_FILE} does not declare the nc-mcp-exapp project." >&2
    echo "This script only ever runs against that throwaway topology (WR-07)." >&2
    return 1
  fi
}

OCC="docker compose -f ${COMPOSE_FILE} exec -T --user www-data ${SERVICE} php occ"

occ() {
  # Intentionally unquoted: OCC is a command line, not a single word.
  # shellcheck disable=SC2086
  $OCC "$@"
}

# Every secret this script hands to the container travels through stdin, never through a
# command line (WR-06). The argv of `docker` is world readable in `ps aux` for the whole
# duration of a call, and an inline -e assignment additionally lands in the container
# config of the exec. A pipe is private to the two processes at its ends.
#
# The `sh -c '<snippet>' sh "$@"` form is the portable way to give that snippet positional
# arguments: the word after the snippet becomes $0, everything after it becomes $1 and up.
occ_stdin() {
  local snippet="$1"
  shift
  docker compose -f "${COMPOSE_FILE}" exec -T --user www-data "${SERVICE}" \
    sh -c "${snippet}" sh "$@"
}

# A password for occ has to travel inside the container: an exported variable on the host
# never reaches the process that `docker compose exec` starts.
occ_pw() {
  local password="$1"
  shift
  printf '%s' "$password" |
    occ_stdin 'OC_PASS="$(cat)"; export OC_PASS; exec php occ "$@"' "$@"
}

# grep on an occ pipe never uses -q here: with pipefail, -q exits on the first match,
# the pipe closes early and the docker side of the pipe can die on SIGPIPE (exit 141),
# which turns a successful check into a flaky bootstrap failure (two CI runs died with
# the calendar visibly printed one line above the failing check). grep without -q reads
# its input to the end; the match result goes to /dev/null instead.
wait_for_install() {
  local attempt
  for attempt in $(seq 1 60); do
    if occ status 2>/dev/null | grep "installed: true" >/dev/null; then
      echo "nextcloud: installed"
      return 0
    fi
    echo "waiting for the Nextcloud installation to finish (${attempt}/60)"
    sleep 5
  done
  echo "ERROR: Nextcloud is still not installed after five minutes." >&2
  echo "Check: docker compose -f ${COMPOSE_FILE} logs --tail=100 ${SERVICE}" >&2
  return 1
}

ensure_app() {
  local app="$1" output
  if output="$(occ app:install "$app" 2>&1)"; then
    echo "app ${app}: installed"
    return 0
  fi
  if output="$(occ app:enable "$app" 2>&1)"; then
    echo "app ${app}: enabled"
    return 0
  fi
  echo "ERROR: could not install or enable ${app}:" >&2
  echo "${output}" >&2
  echo "See the FALLBACK block at the end of this script." >&2
  return 1
}

ensure_user() {
  local uid="$1" password="$2" output
  if occ user:info "$uid" >/dev/null 2>&1; then
    echo "user ${uid}: exists"
    return 0
  fi
  # occ reports a rejected password on stdout, so the output is captured and only shown
  # when it matters. Swallowing it would turn a policy violation into a silent exit 1.
  if ! output="$(occ_pw "$password" user:add --password-from-env "$uid" 2>&1)"; then
    echo "ERROR: could not create user ${uid}:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "user ${uid}: created"
}

# Mandatory, not cosmetic: Nextcloud creates the default calendar and the default address
# book in the listener for UserFirstTimeLoggedInEvent, and `occ user:add` never fires that
# event. Without the two commands below a freshly created test user has no calendar and no
# address book at all, and every CalDAV or CardDAV test fails with an empty result that
# looks like a bug in our own XML (research pitfall 3).
ensure_calendar() {
  local uid="$1" name="$2" attempt
  # The create races the DAV app warming up right after the install, and a create that
  # failed transiently must not pass as "already there": two CI runs died exactly like
  # that, with the rerun green. So the create is retried until the calendar is actually
  # listed, with a hard timeout instead of a single check.
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    occ dav:create-calendar "$uid" "$name" >/dev/null 2>&1 || true
    if occ dav:list-calendars "$uid" 2>/dev/null | grep "$name" >/dev/null; then
      echo "calendar ${uid}/${name}: present (attempt ${attempt})"
      return 0
    fi
    sleep 5
  done
  echo "ERROR: calendar ${uid}/${name} did not appear within 60s." >&2
  return 1
}

ensure_addressbook() {
  local uid="$1" name="$2"
  if occ dav:create-addressbook "$uid" "$name" >/dev/null 2>&1; then
    echo "addressbook ${uid}/${name}: created"
  else
    echo "addressbook ${uid}/${name}: already there"
  fi
}

# Same class of issue as the calendar and address book above: `occ user:add` never fires the
# first login, so a fresh user gets none of the skeleton files a real first login lays down
# and its files home stays completely empty. An empty home has no searchable root node, so a
# WebDAV SEARCH against it raises OCP\Files\NotFoundException on /<uid>/files inside the
# FileSearchBackend and surfaces as HTTP 500, not a clean empty result. A CalDAV or CardDAV
# read still answers empty, which is why only the file search is affected. The permission
# tests search bob's home before bob ever writes to it, so without this a leak test would
# fail on a server error rather than prove the boundary.
#
# Placing one neutral file (exactly what a first login's skeleton would leave behind) and
# scanning it registers the root the search backend looks up, after which SEARCH answers an
# honest empty. The file is generic and never matches the unique markers the permission tests
# search for, so it does not weaken any positive control or leak test. A plain scan alone is
# not enough: an empty home stays unsearchable. Verified against a clean rebuild from wiped
# volumes.
ensure_files_home() {
  local uid="$1"
  docker compose -f "${COMPOSE_FILE}" exec -T --user www-data "${SERVICE}" sh -c \
    "mkdir -p 'data/${uid}/files' && printf 'Initialised by scripts/bootstrap_exapp.sh.\n' \
      > 'data/${uid}/files/Readme.md'"
  if occ files:scan "$uid" >/dev/null 2>&1; then
    echo "files home ${uid}: initialised"
  else
    echo "files home ${uid}: scan failed" >&2
    return 1
  fi
}

app_password() {
  local uid="$1" password="$2" raw token
  raw="$(occ_pw "$password" user:auth-tokens:add "$uid" --password-from-env --name "$TOKEN_NAME")"
  # The command prints a label line and the token on the next line. The CR strip is the
  # Windows guard: Git Bash keeps the CR from the container output otherwise.
  token="$(printf '%s\n' "$raw" | tr -d '\r' | sed '/^[[:space:]]*$/d' | tail -n1 |
    sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [ -z "$token" ] || [ "${#token}" -lt 20 ]; then
    echo "ERROR: no app password could be parsed for ${uid}. Raw output:" >&2
    printf '%s\n' "$raw" >&2
    return 1
  fi
  printf '%s' "$token"
}

# Both secrets this script handles are bearer equivalent, so both are checked against the
# one shape `openssl rand -hex 32` produces. Anything else is a hand written value or the
# placeholder from .env.exapp.example, and that file is published in git: whoever reads it
# could impersonate every account of the instance with APP_SECRET, or attach a foreign FRP
# client to HaRP with HP_SHARED_KEY (CR-02). A weak value is refused, never adopted.
require_hex64() {
  local name="$1" value="$2" origin="$3"
  if ! printf '%s' "$value" | grep -Eq '^[0-9a-f]{64}$'; then
    echo "ERROR: ${name} in ${origin} is not 64 lower case hex characters." >&2
    echo "It looks like a placeholder or a hand written value, and both are secrets that" >&2
    echo "grant full access. Generate one: openssl rand -hex 32" >&2
    return 1
  fi
}

# json_info interpolates the port unquoted and the registry into a string of the
# registration payload, and all three source variables are overridable from the calling
# shell (IN-07). A forgotten export in that shell (the same error class WR-07 pinned
# COMPOSE_FILE against) produces at best invalid JSON, at worst a payload with extra
# fields that AppAPI adopts silently. APP_SECRET is covered by require_hex64 (CR-02);
# these two shapes are pinned here, immediately before any of them is used.
require_port_number() {
  local name="$1" value="$2"
  if ! printf '%s' "$value" | grep -Eq '^[0-9]+$'; then
    echo "ERROR: ${name} is '${value}', not a plain port number." >&2
    echo "It is interpolated unquoted into the registration JSON (IN-07). Refusing." >&2
    return 1
  fi
}

require_registry_shape() {
  local value="$1"
  if ! printf '%s' "$value" | grep -Eq '^[0-9A-Za-z_.:-]+$'; then
    echo "ERROR: NC_EXAPP_REGISTRY is '${value}', which is not a host[:port] shape." >&2
    echo "It is interpolated into the registration JSON (IN-07). Refusing." >&2
    return 1
  fi
}

# The shared key is read back from the running HaRP container instead of being invented
# here. Both sides have to carry the same value, and a generated one would silently drift
# away from the container that was started before this script ran.
harp_shared_key() {
  local key
  key="$(docker inspect "${HARP_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null |
    tr -d '\r' | sed -n 's/^HP_SHARED_KEY=//p' | head -n1)"
  if [ -z "$key" ]; then
    echo "ERROR: container ${HARP_CONTAINER} is not running or carries no HP_SHARED_KEY." >&2
    echo "Start the topology first: docker compose -f ${COMPOSE_FILE} up -d --wait" >&2
    return 1
  fi
  require_hex64 HP_SHARED_KEY "$key" "container ${HARP_CONTAINER}" || return 1
  printf '%s' "$key"
}

# The version is the single source of truth for the image tag, so it is read from the
# manifest instead of being repeated here.
app_version() {
  sed -n 's:.*<version>\(.*\)</version>.*:\1:p' appinfo/info.xml | head -n1 | tr -d '\r'
}

# Fixed across runs: a new secret on every registration locks out a container or a
# development process that still holds the old one (research pitfall 11). Pinning an
# existing value is exactly why it has to be validated first: a bad one would be held on
# to across every further run, and .env.exapp.example ships a placeholder that the obvious
# `cp .env.exapp.example .env.exapp` would turn into the real registration secret (CR-02).
app_secret() {
  local existing=""
  if [ -f "${ENV_FILE}" ]; then
    existing="$(sed -n 's/^APP_SECRET=//p' "${ENV_FILE}" | head -n1 | tr -d '\r')"
  fi
  if [ -n "$existing" ]; then
    require_hex64 APP_SECRET "$existing" "${ENV_FILE}" || return 1
    printf '%s' "$existing"
    return 0
  fi
  openssl rand -hex 32
}

ensure_daemon_harp() {
  local output
  if occ app_api:daemon:list 2>/dev/null | grep "${DAEMON_NAME}" >/dev/null; then
    echo "daemon ${DAEMON_NAME}: exists"
    return 0
  fi
  # nextcloud_url is passed explicitly: without it AppAPI replaces https by http, and the
  # deploy daemon has to reach Nextcloud through the same reverse proxy that serves
  # /exapps/, otherwise the heartbeat fails (research pitfall 7).
  #
  # HP_SHARED_KEY is bearer equivalent (CR-02, WR-11), so it travels through stdin like
  # every other secret of this script (WR-06) and never through the argv of the docker
  # client on the host. The remaining argv inside the container is the same residual risk
  # WR-06 already documents and accepts for the json-info payload.
  if ! output="$(printf '%s' "${HP_SHARED_KEY}" | occ_stdin \
    'KEY="$(cat)"; exec php occ app_api:daemon:register "$@" --harp_shared_key "$KEY"' \
    "${DAEMON_NAME}" "Harp Proxy (Docker)" docker-install http \
    "appapi-harp:8780" "http://caddy" \
    --net "${NETWORK_NAME}" --harp \
    --harp_frp_address "appapi-harp:8782" \
    --set-default 2>&1)"; then
    echo "ERROR: could not register the deploy daemon ${DAEMON_NAME}:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "daemon ${DAEMON_NAME}: registered"
}

ensure_image() {
  local ref="${REGISTRY}/${IMAGE_NAME}:${APP_VERSION}" output
  if ! output="$(docker buildx build --platform linux/amd64 --load -t "${ref}" . 2>&1)"; then
    echo "ERROR: could not build ${ref}:" >&2
    echo "${output}" >&2
    return 1
  fi
  if ! output="$(docker push "${ref}" 2>&1)"; then
    echo "ERROR: could not push ${ref} into the local registry:" >&2
    echo "${output}" >&2
    echo "Is the registry service up? docker compose -f ${COMPOSE_FILE} ps registry" >&2
    return 1
  fi
  IMAGE_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "${ref}" 2>/dev/null |
    tr -d '\r' | cut -d@ -f2)"
  if [ -z "${IMAGE_DIGEST}" ]; then
    echo "ERROR: the push of ${ref} left no digest behind, so nothing can be verified." >&2
    return 1
  fi
  echo "image ${ref}: built and pushed (${IMAGE_DIGEST})"
}

# The loopback registry has neither authentication nor TLS, so every local process, down to
# a package postinstall script, may `docker push` over this tag. The deploy daemon pulls by
# tag, and what it pulls is started with APP_SECRET in its environment (WR-09). A tag is a
# name, a digest is the content: this compares what the registry serves now against what we
# pushed, immediately before the registration that triggers the pull.
verify_image_digest() {
  local ref="${REGISTRY}/${IMAGE_NAME}:${APP_VERSION}" remote
  remote="$(docker buildx imagetools inspect "${ref}" --format '{{.Manifest.Digest}}' 2>/dev/null |
    tr -d '\r' | tr -d '[:space:]')"
  if [ -z "$remote" ]; then
    echo "ERROR: could not read the digest of ${ref} from the registry." >&2
    return 1
  fi
  if [ "$remote" != "${IMAGE_DIGEST}" ]; then
    echo "ERROR: ${ref} in the registry is not the image this run built." >&2
    echo "  pushed:  ${IMAGE_DIGEST}" >&2
    echo "  serving: ${remote}" >&2
    echo "Someone else pushed over this tag. Refusing to register it (WR-09)." >&2
    return 1
  fi
  echo "image digest ${remote}: unchanged since the push"
}

# The registration overrides exactly three fields of the manifest: registry, image and
# image tag. appinfo/info.xml keeps pointing at ghcr.io because that is the store state
# (D-25 publishes nothing before phase 5), while the local test needs an image that
# actually exists, and that one lives in the loopback registry.
#
# The four backslashes in each well-known route are two levels of escaping: the unquoted
# heredoc consumes one pair, and JSON needs the remaining one so the route regex reaches
# AppAPI as ^/\.well-known/... with an escaped dot. Two backslashes here produce the
# invalid JSON escape \. and AppAPI answers "Invalid app info provided in JSON format".
# Every well-known pattern ends with $, and /mcp is access level 0 (PUBLIC) like the other
# three: HaRP matches with re.match, and the 401 of the OAuth discovery flow has to come
# from the ExApp itself (appinfo/info.xml carries the full reasoning, plan 03-01).
#
# headers_to_exclude mirrors appinfo/info.xml: the proxy strips the headers it sets itself,
# so a client cannot send a second AUTHORIZATION-APP-API next to the real one (WR-01).
#
# Daemon and port are parameters, so the development loop builds its payload the same way
# instead of rewriting this one with sed.
EXCLUDED_HEADERS='["AUTHORIZATION-APP-API","EX-APP-ID","EX-APP-VERSION","AA-VERSION","X-ORIGIN-IP"]'
json_info() {
  local daemon="$1" port="$2"
  cat <<JSON
{"id":"${APP_ID}","name":"${APP_NAME}","daemon_config_name":"${daemon}","version":"${APP_VERSION}","secret":"${APP_SECRET}","port":${port},"docker-install":{"registry":"${REGISTRY}","image":"${IMAGE_NAME}","image-tag":"${APP_VERSION}"},"routes":[{"url":"^/mcp/?$","verb":"GET,POST,DELETE","access_level":0,"headers_to_exclude":${EXCLUDED_HEADERS}},{"url":"^/\\\\.well-known/oauth-protected-resource/mcp$","verb":"GET","access_level":0,"headers_to_exclude":${EXCLUDED_HEADERS}},{"url":"^/\\\\.well-known/openid-configuration$","verb":"GET","access_level":0,"headers_to_exclude":${EXCLUDED_HEADERS}},{"url":"^/\\\\.well-known/oauth-authorization-server$","verb":"GET","access_level":0,"headers_to_exclude":${EXCLUDED_HEADERS}}]}
JSON
}

# The payload carries "secret":"<APP_SECRET>", which is bearer equivalent, so it goes in
# through stdin and never as an argument of the docker client (WR-06).
register_exapp() {
  local daemon="$1" port="$2"
  local snippet
  snippet='JSON="$(cat)"; exec php occ app_api:app:register "$1" "$2"'
  snippet="${snippet} "'--json-info "$JSON" --force-scopes --wait-finish'
  json_info "$daemon" "$port" | occ_stdin "${snippet}" "${APP_ID}" "$daemon"
}

# access_level travels as a number on purpose. AppAPI maps the names PUBLIC, USER and
# ADMIN to 0, 1 and 2 only on the info.xml path (ExAppService::getAppInfo); a json-info
# registration writes the value straight into the integer column of ex_apps_routes, and a
# route whose access level reads "USER" is a route HaRP cannot evaluate.
ensure_exapp() {
  local output
  if occ app_api:app:list 2>/dev/null | grep "${APP_ID}" >/dev/null; then
    echo "exapp ${APP_ID}: registered"
    return 0
  fi
  verify_image_digest || return 1
  if ! output="$(register_exapp "${DAEMON_NAME}" "${APP_PORT}" 2>&1)"; then
    echo "ERROR: could not register the ExApp ${APP_ID}:" >&2
    echo "${output}" >&2
    echo "Logs: docker compose -f ${COMPOSE_FILE} logs --tail=100 appapi-harp" >&2
    echo "See the FALLBACK block at the end of this script." >&2
    return 1
  fi
  echo "exapp ${APP_ID}: registered and deployed"
}

# `occ app_api:app:list` prints one line per app: "<id> (<name>): <version> [enabled]".
# Enabling is not cosmetic: AppAPI sends PUT /enabled?enabled=1 to the container and only
# writes the flag when the app answers 200 with an empty error field.
ensure_exapp_enabled() {
  local output
  if occ app_api:app:list 2>/dev/null | tr -d '\r' | grep "^${APP_ID} .*\[enabled\]" >/dev/null; then
    echo "exapp ${APP_ID}: enabled"
    return 0
  fi
  if ! output="$(occ app_api:app:enable "${APP_ID}" 2>&1)"; then
    echo "ERROR: could not enable the ExApp ${APP_ID}:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "exapp ${APP_ID}: enabled"
}

# The development loop: no image, no container, a locally started process instead. Only
# reached with --manual, because it registers a second daemon and a second app entry.
register_manual_install() {
  local output
  if ! occ app_api:daemon:list 2>/dev/null | grep "${MANUAL_DAEMON_NAME}" >/dev/null; then
    if ! output="$(occ app_api:daemon:register \
      "${MANUAL_DAEMON_NAME}" "Manual Install" manual-install http \
      "host.docker.internal:${MANUAL_APP_PORT}" "http://caddy" 2>&1)"; then
      echo "ERROR: could not register the manual-install daemon:" >&2
      echo "${output}" >&2
      return 1
    fi
    echo "daemon ${MANUAL_DAEMON_NAME}: registered"
  fi
  if occ app_api:app:list 2>/dev/null | grep "${APP_ID}" >/dev/null; then
    echo "exapp ${APP_ID}: already registered, unregister it first to switch the daemon"
    return 0
  fi
  if ! output="$(register_exapp "${MANUAL_DAEMON_NAME}" "${MANUAL_APP_PORT}" 2>&1)"; then
    echo "ERROR: could not register the ExApp in manual-install mode:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "exapp ${APP_ID}: registered against the local process on port ${MANUAL_APP_PORT}"
}

echo "== ExApp topology bootstrap =="
ensure_own_topology
require_port_number NC_EXAPP_APP_PORT "${APP_PORT}"
require_port_number NC_EXAPP_MANUAL_PORT "${MANUAL_APP_PORT}"
require_registry_shape "${REGISTRY}"
wait_for_install

# Notes and Deck are optional apps; the tool plans of the later phases need both.
ensure_app notes
ensure_app deck

# alice is the full test user, bob is the restricted one for the permission tests.
ensure_user alice "${ALICE_PASSWORD}"
ensure_user bob "${BOB_PASSWORD}"

ensure_calendar alice personal
ensure_addressbook alice contacts
ensure_calendar bob personal

# Initialise both file homes so a WebDAV SEARCH answers an empty result, not a 500 (see
# ensure_files_home). bob is the one the leak tests search before he owns anything.
ensure_files_home alice
ensure_files_home bob

# Nextcloud counts failed logins per source IP, and a remote MCP server is one IP for many
# users. The negative tests produce 401s on purpose, so the guard would throttle the whole
# run and hand us random 429s (research pitfall 8). Test instance only, never a
# recommendation for a real server.
occ config:system:set auth.bruteforce.protection.enabled --value=false --type=boolean >/dev/null
echo "bruteforce protection: disabled (test instance)"

# AppAPI is an app store app, not part of the server tarball (research pitfall 9). Recent
# server images ship it, in which case app:install reports it as already installed.
ensure_app app_api

HP_SHARED_KEY="$(harp_shared_key)"
APP_VERSION="$(app_version)"
APP_SECRET="$(app_secret)"

ensure_daemon_harp

if [ "${MANUAL_MODE}" -eq 1 ]; then
  register_manual_install
else
  ensure_image
  ensure_exapp
  ensure_exapp_enabled
fi

ALICE_APP_PASSWORD="$(app_password alice "${ALICE_PASSWORD}")"
BOB_APP_PASSWORD="$(app_password bob "${BOB_PASSWORD}")"
echo "app passwords: created for alice and bob"

umask 077
cat >"${ENV_FILE}" <<EOF
# Written by scripts/bootstrap_exapp.sh. Never commit this file.
NC_MCP_URL=http://127.0.0.1:${HOST_PORT}
NC_MCP_EXAPP_BASE=http://127.0.0.1:${HOST_PORT}/exapps/${APP_ID}
NC_MCP_TEST_USER=alice
NC_MCP_TEST_APP_PASSWORD=${ALICE_APP_PASSWORD}
NC_MCP_TEST_USER2=bob
NC_MCP_TEST_APP_PASSWORD2=${BOB_APP_PASSWORD}
APP_ID=${APP_ID}
APP_SECRET=${APP_SECRET}
APP_VERSION=${APP_VERSION}
HP_SHARED_KEY=${HP_SHARED_KEY}
EOF
echo "wrote ${ENV_FILE}"

echo
echo "== verification =="
occ app_api:daemon:list
occ app_api:app:list
if ! occ app_api:app:list | grep "${APP_ID}" >/dev/null; then
  echo "ERROR: ${APP_ID} is not in the ExApp list." >&2
  exit 1
fi
if ! occ app_api:app:list | tr -d '\r' | grep "^${APP_ID} .*\[enabled\]" >/dev/null; then
  echo "ERROR: ${APP_ID} is registered but not enabled." >&2
  exit 1
fi

echo
echo "Ready. The app answers under:"
echo "  http://127.0.0.1:${HOST_PORT}/exapps/${APP_ID}/mcp"

# ---------------------------------------------------------------------------
# FALLBACK 1: no app store access for app_api (research pitfall 9)
#
# `occ app:install app_api` downloads from apps.nextcloud.com. In an offline runner or
# behind a proxy that blocks it, the command fails, `app:enable` fails as well, and this
# script stops at ensure_app. Recent nextcloud images ship app_api, so the step then only
# prints "already installed".
#
# Then install it by hand once and let the script enable it:
#
#   1. Download the release archive on a machine that has access:
#      https://github.com/nextcloud/app_api/releases (pick the tag that matches the
#      server version, 34.x for nextcloud:34-apache).
#   2. Unpack it into the container so the app directory keeps its plain name:
#        docker compose -f compose.exapp.yml cp app_api nextcloud:/var/www/html/custom_apps/app_api
#        docker compose -f compose.exapp.yml exec -T --user root nextcloud \
#          chown -R www-data:www-data /var/www/html/custom_apps/app_api
#   3. Re-run this script: `occ app:install` still fails, `occ app:enable` now succeeds.
#
# FALLBACK 2: the app answers 401 after a re-registration (research pitfall 11)
#
# APP_SECRET is generated fresh on every registration unless the registration carries one.
# This script pins it: the value from .env.exapp is passed in the json-info payload, so a
# re-registration keeps the secret stable. If .env.exapp was deleted, a new secret is
# generated, and then everything that still holds the old one has to be restarted:
#
#   docker compose -f compose.exapp.yml exec -T --user www-data nextcloud \
#     php occ app_api:app:unregister mcp_connector
#   rm -f .env.exapp        # only if you want a new secret on purpose
#   bash scripts/bootstrap_exapp.sh
#
# In the --manual development loop the local process is the one that holds the old secret:
# restart `nc-mcp-exapp` after every registration, otherwise every incoming request is
# answered with 401 and every outgoing one is rejected by Nextcloud.
# ---------------------------------------------------------------------------
