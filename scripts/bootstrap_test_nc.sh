#!/usr/bin/env bash
# Bootstrap the local test Nextcloud from compose.test.yml.
#
#   docker compose -f compose.test.yml up -d --wait
#   bash scripts/bootstrap_test_nc.sh
#   set -a && . ./.env.test && set +a && uv run pytest -m integration -q
#
# Idempotent by design: every step checks first and skips what already exists, so a second
# run is a no-op apart from a fresh app password in .env.test. That file is git-ignored;
# .env.test.example documents the variable names.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE_FILE="${COMPOSE_FILE:-compose.test.yml}"
SERVICE="nextcloud"
HOST_PORT="${NC_TEST_PORT:-8080}"
# At least ten characters: Nextcloud's password policy rejects anything shorter with
# "Password needs to be at least 10 characters long." and occ exits 1.
ALICE_PASSWORD="${NC_TEST_ALICE_PASSWORD:-alice-test-pw-01}"
BOB_PASSWORD="${NC_TEST_BOB_PASSWORD:-bob-test-pw-01}"
TOKEN_NAME="mcp-test"
ENV_FILE="${ENV_FILE:-.env.test}"

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
  local uid="$1" name="$2" attempt
  # The create races the DAV app warming up right after the install, and a create that
  # failed transiently must not pass as "already there": two CI runs died exactly like
  # that, with the rerun green. So the create is retried until the calendar is actually
  # listed, with a hard timeout instead of a single check.
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    occ dav:create-calendar "$uid" "$name" >/dev/null 2>&1 || true
    if occ dav:list-calendars "$uid" 2>/dev/null | grep -q "$name"; then
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

echo "== test Nextcloud bootstrap =="
wait_for_install

# Notes and Deck are optional apps; the later tool plans need both.
ensure_app notes
ensure_app deck

# alice is the full test user, bob is the restricted one for the permission tests.
ensure_user alice "${ALICE_PASSWORD}"
ensure_user bob "${BOB_PASSWORD}"

ensure_calendar alice personal
ensure_addressbook alice contacts
ensure_calendar bob personal

# Nextcloud counts failed logins per source IP, and a remote MCP server is one IP for many
# users. Our negative tests produce 401s on purpose, so the guard would throttle the whole
# CI run and hand us random 429s (research pitfall 8). Test instance only, never a
# recommendation for a real server.
occ config:system:set auth.bruteforce.protection.enabled --value=false --type=boolean >/dev/null
echo "bruteforce protection: disabled (test instance)"

ALICE_APP_PASSWORD="$(app_password alice "${ALICE_PASSWORD}")"
BOB_APP_PASSWORD="$(app_password bob "${BOB_PASSWORD}")"
echo "app passwords: created for alice and bob"

umask 077
cat >"${ENV_FILE}" <<EOF
# Written by scripts/bootstrap_test_nc.sh. Never commit this file.
NC_MCP_URL=http://127.0.0.1:${HOST_PORT}
NC_MCP_USER=alice
NC_MCP_APP_PASSWORD=${ALICE_APP_PASSWORD}
NC_MCP_TEST_USER2=bob
NC_MCP_TEST_APP_PASSWORD2=${BOB_APP_PASSWORD}
EOF
echo "wrote ${ENV_FILE}"

echo
echo "== verification =="
occ dav:list-calendars alice
if ! occ dav:list-calendars alice | grep -q "personal"; then
  echo "ERROR: alice has no calendar 'personal'." >&2
  exit 1
fi
if ! occ app:list | grep -E '^[[:space:]]*- (notes|deck):'; then
  echo "ERROR: notes and deck are not in the app list." >&2
  exit 1
fi

echo
echo "Ready. Run the integration tests with:"
echo "  set -a && . ./${ENV_FILE} && set +a && uv run pytest -m integration -q"

# ---------------------------------------------------------------------------
# FALLBACK: no app store access (assumption A7)
#
# `occ app:install` downloads from apps.nextcloud.com. In an offline runner or behind a
# proxy that blocks it, the command fails and this script stops at ensure_app.
#
# Then install the app by hand once and let the script enable it:
#
#   1. Download the release archive on a machine that has access, for example
#      https://github.com/nextcloud/notes/releases and
#      https://github.com/nextcloud-releases/deck/releases
#      (Notes 6.0.1 and Deck 1.18.3 are the releases marked compatible with Nextcloud 34).
#   2. Unpack it into the container so that the app directory keeps its plain name:
#        docker compose -f compose.test.yml cp notes nextcloud:/var/www/html/custom_apps/notes
#        docker compose -f compose.test.yml exec -T --user root nextcloud \
#          chown -R www-data:www-data /var/www/html/custom_apps/notes
#   3. Re-run this script: `occ app:install` still fails, `occ app:enable` now succeeds,
#      and the rest of the bootstrap continues unchanged.
#
# Alternative for a permanently offline CI: mount a prepared apps directory as a volume in
# compose.test.yml under /var/www/html/custom_apps and keep only the app:enable path.
# ---------------------------------------------------------------------------
