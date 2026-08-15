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

COMPOSE_FILE="${COMPOSE_FILE:-compose.exapp.yml}"
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

MANUAL_MODE=0
if [ "${1:-}" = "--manual" ]; then
  MANUAL_MODE=1
fi

OCC="docker compose -f ${COMPOSE_FILE} exec -T --user www-data ${SERVICE} php occ"

occ() {
  # Intentionally unquoted: OCC is a command line, not a single word.
  # shellcheck disable=SC2086
  $OCC "$@"
}

# A password for occ has to travel inside the container. An exported variable on the host
# never reaches the process that `docker compose exec` starts, so -e is not optional here.
occ_pw() {
  local password="$1"
  shift
  docker compose -f "${COMPOSE_FILE}" exec -T -e "OC_PASS=${password}" \
    --user www-data "${SERVICE}" php occ "$@"
}

wait_for_install() {
  local attempt
  for attempt in $(seq 1 60); do
    if occ status 2>/dev/null | grep -q "installed: true"; then
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
  local uid="$1" name="$2"
  if occ dav:create-calendar "$uid" "$name" >/dev/null 2>&1; then
    echo "calendar ${uid}/${name}: created"
  else
    echo "calendar ${uid}/${name}: already there"
  fi
}

ensure_addressbook() {
  local uid="$1" name="$2"
  if occ dav:create-addressbook "$uid" "$name" >/dev/null 2>&1; then
    echo "addressbook ${uid}/${name}: created"
  else
    echo "addressbook ${uid}/${name}: already there"
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
  if occ app_api:daemon:list 2>/dev/null | grep -q "${DAEMON_NAME}"; then
    echo "daemon ${DAEMON_NAME}: exists"
    return 0
  fi
  # nextcloud_url is passed explicitly: without it AppAPI replaces https by http, and the
  # deploy daemon has to reach Nextcloud through the same reverse proxy that serves
  # /exapps/, otherwise the heartbeat fails (research pitfall 7).
  if ! output="$(occ app_api:daemon:register \
    "${DAEMON_NAME}" "Harp Proxy (Docker)" docker-install http \
    "appapi-harp:8780" "http://caddy" \
    --net "${NETWORK_NAME}" --harp \
    --harp_frp_address "appapi-harp:8782" \
    --harp_shared_key "${HP_SHARED_KEY}" \
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
  echo "image ${ref}: built and pushed"
}

# The registration overrides exactly three fields of the manifest: registry, image and
# image tag. appinfo/info.xml keeps pointing at ghcr.io because that is the store state
# (D-25 publishes nothing before phase 5), while the local test needs an image that
# actually exists, and that one lives in the loopback registry.
#
# The four backslashes in the well-known route are two levels of escaping: the unquoted
# heredoc consumes one pair, and JSON needs the remaining one so the route regex reaches
# AppAPI as ^/\.well-known/ with an escaped dot. Two backslashes here produce the invalid
# JSON escape \. and AppAPI answers "Invalid app info provided in JSON format".
json_info() {
  cat <<JSON
{"id":"${APP_ID}","name":"${APP_NAME}","daemon_config_name":"${DAEMON_NAME}","version":"${APP_VERSION}","secret":"${APP_SECRET}","port":${APP_PORT},"docker-install":{"registry":"${REGISTRY}","image":"${IMAGE_NAME}","image-tag":"${APP_VERSION}"},"routes":[{"url":"^/mcp/?$","verb":"GET,POST,DELETE","access_level":1,"headers_to_exclude":[]},{"url":"^/\\\\.well-known/","verb":"GET","access_level":0,"headers_to_exclude":[]}]}
JSON
}

# access_level travels as a number on purpose. AppAPI maps the names PUBLIC, USER and
# ADMIN to 0, 1 and 2 only on the info.xml path (ExAppService::getAppInfo); a json-info
# registration writes the value straight into the integer column of ex_apps_routes, and a
# route whose access level reads "USER" is a route HaRP cannot evaluate.
ensure_exapp() {
  local output
  if occ app_api:app:list 2>/dev/null | grep -q "${APP_ID}"; then
    echo "exapp ${APP_ID}: registered"
    return 0
  fi
  if ! output="$(occ app_api:app:register "${APP_ID}" "${DAEMON_NAME}" \
    --json-info "$(json_info)" --force-scopes --wait-finish 2>&1)"; then
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
  if occ app_api:app:list 2>/dev/null | tr -d '\r' | grep -q "^${APP_ID} .*\[enabled\]"; then
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
  local output json
  if ! occ app_api:daemon:list 2>/dev/null | grep -q "${MANUAL_DAEMON_NAME}"; then
    if ! output="$(occ app_api:daemon:register \
      "${MANUAL_DAEMON_NAME}" "Manual Install" manual-install http \
      "host.docker.internal:${MANUAL_APP_PORT}" "http://caddy" 2>&1)"; then
      echo "ERROR: could not register the manual-install daemon:" >&2
      echo "${output}" >&2
      return 1
    fi
    echo "daemon ${MANUAL_DAEMON_NAME}: registered"
  fi
  json="$(json_info | sed \
    -e "s/\"daemon_config_name\":\"${DAEMON_NAME}\"/\"daemon_config_name\":\"${MANUAL_DAEMON_NAME}\"/" \
    -e "s/\"port\":${APP_PORT}/\"port\":${MANUAL_APP_PORT}/")"
  if occ app_api:app:list 2>/dev/null | grep -q "${APP_ID}"; then
    echo "exapp ${APP_ID}: already registered, unregister it first to switch the daemon"
    return 0
  fi
  if ! output="$(occ app_api:app:register "${APP_ID}" "${MANUAL_DAEMON_NAME}" \
    --json-info "${json}" --force-scopes --wait-finish 2>&1)"; then
    echo "ERROR: could not register the ExApp in manual-install mode:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "exapp ${APP_ID}: registered against the local process on port ${MANUAL_APP_PORT}"
}

echo "== ExApp topology bootstrap =="
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
if ! occ app_api:app:list | grep -q "${APP_ID}"; then
  echo "ERROR: ${APP_ID} is not in the ExApp list." >&2
  exit 1
fi
if ! occ app_api:app:list | tr -d '\r' | grep -q "^${APP_ID} .*\[enabled\]"; then
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
