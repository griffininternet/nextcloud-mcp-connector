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
# The one place that knows where this instance answers over HTTP. `occ` reaches Nextcloud from
# the inside, the Talk conversation lookup below reaches it from the outside, and the
# connection file publishes the same value.
BASE_URL="http://127.0.0.1:${HOST_PORT}"
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

# One authenticated request against this instance, the body as its only output. The password
# travels through a curl config file on stdin (WR-06): `-u user:password` would sit in the
# world readable argv of curl for the whole duration of the request. Same shape as `nc_body`
# in scripts/bootstrap_exapp.sh.
nc_body() {
  local user="$1" password="$2" method="$3" url="$4"
  shift 4
  printf 'user = "%s:%s"\n' "$user" "$password" |
    curl -sS --config - -X "$method" "$@" "$url" || true
}

# --- the Talk test conversations (plan 09-05) -----------------------------------------
#
# Two conversations of alice, both with real umlauts in the name: one writable and one write
# protected. The write protected one carries the negative case of TALK-03, because a refusal
# with a sentence and a next step needs an object to be refused on and not an assumption.
#
# The changelog conversation (type 4) is deliberately not created and never used as a target.
# Talk creates it for every account by itself, it is always write protected, and it is exactly
# the trap `tools.talk._may_send` catches.
#
# `occ talk:room:create` is **not** idempotent: a second call creates a second room with the
# same name. The room is therefore looked up by name first and only created when it is
# missing. The lookup goes over the conversation list of the account itself, because the app
# ships no listing command at all: measured against spreed 24.0.4 on 2026-08-21, the `talk:`
# namespace offers create, update, delete, add, remove, promote and demote, and nothing that
# lists rooms.
#
# The name is matched on its ASCII prefix and not on the whole string, and that is not
# laziness: PHP writes every umlaut of a JSON answer as a \uXXXX escape, so a grep for the
# literal name would never match the answer of the API. The prefix is unique per
# conversation, which is what keeps the match exact enough.
talk_room_token() {
  local uid="$1" password="$2" key="$3"
  nc_body "$uid" "$password" GET "${BASE_URL}/ocs/v2.php/apps/spreed/api/v4/room" \
    -H "OCS-APIRequest: true" -H "Accept: application/json" |
    tr '{' '\n' | grep "\"displayName\":\"${key}" |
    grep -o '"token":"[a-z0-9]\{4,30\}"' | head -n1 | sed 's/.*:"//; s/"$//' || true
}

ensure_talk_room() {
  local uid="$1" password="$2" key="$3" name="$4" readonly="$5" token output
  token="$(talk_room_token "$uid" "$password" "$key")"
  if [ -z "$token" ]; then
    if ! output="$(occ talk:room:create "$name" --user "$uid" --owner "$uid" 2>&1)"; then
      echo "ERROR: could not create the Talk conversation ${name}:" >&2
      echo "${output}" >&2
      return 1
    fi
    # The command prints "Room token: <token>" and the success line after it. The CR strip is
    # the Windows guard, the same one app_password needs.
    token="$(printf '%s\n' "$output" | tr -d '\r' | sed -n 's/^Room token: //p' | head -n1)"
    if [ -z "$token" ]; then
      echo "ERROR: talk:room:create printed no token for ${name}:" >&2
      echo "${output}" >&2
      return 1
    fi
    echo "talk conversation ${name}: created (${token})"
  else
    echo "talk conversation ${name}: exists (${token})"
  fi
  # The write protection is established on every run instead of only at the create. It is the
  # object the negative case is measured on, so a conversation somebody switched back to
  # read-write would turn that test green for the wrong reason. `--readonly 0` says the same
  # thing about the writable one, and both directions are idempotent.
  if ! output="$(occ talk:room:update "$token" --readonly "$readonly" 2>&1)"; then
    echo "ERROR: could not set readonly=${readonly} on the conversation ${name}:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "talk conversation ${name}: readonly=${readonly}"
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
# Tables joins them in this phase. No mail app and no mail account here on purpose: the app
# password layer this instance serves needs Tables only, and the mail reachability spike of
# MAIL-04 runs against the HaRP topology of scripts/bootstrap_exapp.sh.
ensure_app tables
# Talk is the tool family of phase 9, and it joins this instance too, so both topologies carry
# the same app set for it. Chat needs no signaling backend at all: the two routes this
# connector builds are plain OCS calls against the database, and the internal signaling server
# covers the rest, so this install step is as cheap as the ones above. The app id is `spreed`,
# not `talk`.
ensure_app spreed

# alice is the full test user, bob is the restricted one for the permission tests.
ensure_user alice "${ALICE_PASSWORD}"
ensure_user bob "${BOB_PASSWORD}"

ensure_calendar alice personal
ensure_addressbook alice contacts
ensure_calendar bob personal

# The two Talk test conversations (see the block above talk_room_token). They stand here and
# not next to the `ensure_app` lines above: on a fresh instance alice does not exist at that
# point, and `talk:room:create --user alice` for an unknown user is an error and not a no-op.
# The names live in these four lines only and reach
# tests/integration/test_talk_roundtrip.py through the connection file at the end of this
# script, so a rename is one edit. The ASCII prefix is what the lookup matches on; the umlauts
# behind it are there so a broken encoding shows up in the first run instead of never. The two
# spellings are identical to the ones in scripts/bootstrap_exapp.sh, so the same test measures
# the same objects on both topologies.
#
# No spaces in either name, and that is not cosmetic: the connection file below is read with
# `set -a && . ./.env.test`, and an unquoted value with a space in it makes the shell run its
# second word as a command. Hyphens carry the same reading and survive every consumer of that
# file, quoting rules included.
TALK_ROOM_OPEN_KEY="MCP-Talk-offen"
TALK_ROOM_LOCKED_KEY="MCP-Talk-nurlesen"
TALK_ROOM_OPEN="${TALK_ROOM_OPEN_KEY}-Grüße-aus-Hamburg"
TALK_ROOM_LOCKED="${TALK_ROOM_LOCKED_KEY}-Straße-ohne-Ausgang"
ensure_talk_room alice "${ALICE_PASSWORD}" "${TALK_ROOM_OPEN_KEY}" "${TALK_ROOM_OPEN}" 0
ensure_talk_room alice "${ALICE_PASSWORD}" "${TALK_ROOM_LOCKED_KEY}" "${TALK_ROOM_LOCKED}" 1

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
NC_MCP_URL=${BASE_URL}
NC_MCP_USER=alice
NC_MCP_APP_PASSWORD=${ALICE_APP_PASSWORD}
NC_MCP_TEST_USER2=bob
NC_MCP_TEST_APP_PASSWORD2=${BOB_APP_PASSWORD}
# The two Talk test conversations of plan 09-05, both owned by NC_MCP_USER: one writable and
# one write protected, and the write protected one carries the negative case of TALK-03. The
# names are defined once in this script and travel through this file, so
# tests/integration/test_talk_roundtrip.py never spells them a second time; without them it
# skips instead of failing.
NC_MCP_TEST_TALK_ROOM=${TALK_ROOM_OPEN}
NC_MCP_TEST_TALK_READONLY_ROOM=${TALK_ROOM_LOCKED}
EOF
echo "wrote ${ENV_FILE}"

echo
echo "== verification =="
occ dav:list-calendars alice
if ! occ dav:list-calendars alice | grep "personal" >/dev/null; then
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
