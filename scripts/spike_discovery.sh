#!/usr/bin/env bash
# Measure the discovery spike (AUTH-06, D-29) against the running HaRP topology.
#
#   docker compose -f compose.exapp.yml up -d --wait   # 1. topology
#   bash scripts/bootstrap_exapp.sh                     # 2. register and deploy the ExApp
#   set -a && . ./.env.exapp && set +a                  # 3. NC_MCP_TEST_APP_PASSWORD
#   bash scripts/spike_discovery.sh                     # 4. this measurement
#
# Prerequisite: the ExApp is registered under the HaRP daemon and the running container
# carries the metadata routes of plan 03-01 (rebuild and redeploy after a code change).
# This script changes nothing on the instance: no occ, no registration, no restart. It only
# sends GET and POST requests and reads the answers.
#
# The output is one table row per measurement. Three rows are hard expectations and make the
# script exit 1 when they do not hold; every other row is a measured value that the spike
# document records rather than enforces.
set -euo pipefail

BASE="${NC_MCP_EXAPP_SPIKE_BASE:-http://127.0.0.1:8081}"
APP_ID="mcp_connector"
HARP_PREFIX="/exapps/${APP_ID}"
PHP_PREFIX="/apps/app_api/proxy/${APP_ID}"
ALICE_USER="${NC_MCP_TEST_USER:-alice}"
ALICE_APP_PASSWORD="${NC_MCP_TEST_APP_PASSWORD:-}"

# Filled by measure(), read by the verification block at the end.
STATUS_METADATA_HARP=""
WWWAUTH_MCP_HARP=""
STATUS_HEARTBEAT_HARP=""

printf '%s\n' "== discovery spike measurement =="
printf 'base: %s   date: %s\n\n' "${BASE}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%-52s | %-9s | %-11s | %-6s | %s\n' "PATH" "WAY" "AUTH" "STATUS" "HEADERS OF INTEREST"
printf '%s\n' "--------------------------------------------------------------------------------------------------------------------"

# measure <target-path> <way-label> <auth-label> <url> [extra curl args...]
# Prints the row and echoes "<status>\t<www-authenticate>" so callers can capture both.
measure() {
  local target="$1" way="$2" auth="$3" url="$4"
  shift 4
  local dump status ctype cache wwwauth headers
  # -D - dumps the response headers, the body is discarded, no cookie jar is used. On a
  # PUBLIC route no Authorization header is sent on purpose: HaRP would otherwise ask
  # Nextcloud about it on every request (pitfall 6, T-02-43). Only the /mcp-with-user row
  # passes credentials, and it does so through "$@".
  # --max-time keeps a streamed /mcp answer from holding the measurement open: the status
  # and headers arrive first, the SSE body then streams to /dev/null until the cap.
  dump="$(curl -sS --max-time 20 -o /dev/null -D - -w 'HTTP_STATUS:%{http_code}' "$@" "${url}" 2>/dev/null || true)"
  status="$(printf '%s' "${dump}" | sed -n 's/^HTTP_STATUS:\([0-9]*\).*/\1/p' | tail -n1)"
  status="${status:-000}"
  ctype="$(printf '%s\n' "${dump}" | tr -d '\r' | sed -n 's/^[Cc]ontent-[Tt]ype:[[:space:]]*//p' | head -n1)"
  cache="$(printf '%s\n' "${dump}" | tr -d '\r' | sed -n 's/^[Cc]ache-[Cc]ontrol:[[:space:]]*//p' | head -n1)"
  wwwauth="$(printf '%s\n' "${dump}" | tr -d '\r' | sed -n 's/^[Ww][Ww][Ww]-[Aa]uthenticate:[[:space:]]*//p' | head -n1)"
  headers=""
  [ -n "${ctype}" ] && headers="ct=${ctype}"
  [ -n "${cache}" ] && headers="${headers}${headers:+ }cc=${cache}"
  [ -n "${wwwauth}" ] && headers="${headers}${headers:+ }wa=${wwwauth}"
  printf '%-52s | %-9s | %-11s | %-6s | %s\n' "${target}" "${way}" "${auth}" "${status}" "${headers:--}"
  MEASURED_STATUS="${status}"
  MEASURED_WWWAUTH="${wwwauth}"
}

# The app password never goes on a command line (WR-06): `curl -u` would leave it world
# readable in `ps aux` for the duration of each authenticated request. A curl config file
# with owner-only permissions hands it over privately instead, and the trap removes the
# file on every exit, including a failed hard expectation.
basic_auth=()
if [ -n "${ALICE_APP_PASSWORD}" ]; then
  curl_config="$(mktemp)"
  trap 'rm -f "${curl_config}"' EXIT
  chmod 600 "${curl_config}"
  printf 'user = "%s:%s"\n' "${ALICE_USER}" "${ALICE_APP_PASSWORD}" > "${curl_config}"
  basic_auth=(-K "${curl_config}")
fi

# 1. the RFC 9728 metadata route, unauthenticated, over both ways
measure "/.well-known/oauth-protected-resource/mcp" "HaRP" "none" \
  "${BASE}${HARP_PREFIX}/.well-known/oauth-protected-resource/mcp"
STATUS_METADATA_HARP="${MEASURED_STATUS}"
measure "/.well-known/oauth-protected-resource/mcp" "PHP-Proxy" "none" \
  "${BASE}${PHP_PREFIX}/.well-known/oauth-protected-resource/mcp"

# 2. the two authorization server documents, unauthenticated, over both ways. Their
# canonical root paths belong to Nextcloud, which is what the two rewrite rules in
# deploy/Caddyfile are for; measured here below our own prefix, where they exist.
measure "/.well-known/openid-configuration" "HaRP" "none" \
  "${BASE}${HARP_PREFIX}/.well-known/openid-configuration"
measure "/.well-known/oauth-authorization-server" "PHP-Proxy" "none" \
  "${BASE}${PHP_PREFIX}/.well-known/oauth-authorization-server"

# 3. /mcp without auth: since plan 03-01 the route is PUBLIC, so HaRP forwards the call
# and the transport boundary of the ExApp answers the 401 of the discovery flow itself,
# with the resource_metadata pointer. Until then the spike measured that 401 on a purpose
# built probe route below /.well-known/, which plan 03-01 removed. The URL is the fourth
# argument of measure; the curl options follow it (curl accepts the URL anywhere).
measure "/mcp" "HaRP" "none" "${BASE}${HARP_PREFIX}/mcp" \
  -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
WWWAUTH_MCP_HARP="${MEASURED_WWWAUTH}"
measure "/mcp" "PHP-Proxy" "none" "${BASE}${PHP_PREFIX}/mcp" \
  -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 4. /mcp with alice's app password: HaRP resolves the user and signs the request
measure "/mcp" "HaRP" "basic:alice" "${BASE}${HARP_PREFIX}/mcp" \
  -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"spike","version":"1.0"}}}' \
  "${basic_auth[@]}"
measure "/mcp" "PHP-Proxy" "basic:alice" "${BASE}${PHP_PREFIX}/mcp" \
  -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"spike","version":"1.0"}}}' \
  "${basic_auth[@]}"

# 5. /heartbeat without auth: no declared route matches it, so it never reaches the app
measure "/heartbeat" "HaRP" "none" "${BASE}${HARP_PREFIX}/heartbeat"
STATUS_HEARTBEAT_HARP="${MEASURED_STATUS}"
measure "/heartbeat" "PHP-Proxy" "none" "${BASE}${PHP_PREFIX}/heartbeat"

# The canonical RFC 9728 root path, once, without any prefix. This one belongs to Nextcloud,
# not to the ExApp, and its result is the actual spike finding.
measure "/.well-known/oauth-protected-resource/exapps/${APP_ID}/mcp" "root" "none" \
  "${BASE}/.well-known/oauth-protected-resource/exapps/${APP_ID}/mcp"
STATUS_ROOT="${MEASURED_STATUS}"

printf '\n== verification ==\n'
fail=0

# HARD 1: the metadata route answers 200 over the HaRP path. This is the go criterion.
if [ "${STATUS_METADATA_HARP}" = "200" ]; then
  printf 'PASS  metadata over HaRP is 200\n'
else
  printf 'FAIL  metadata over HaRP is %s, expected 200\n' "${STATUS_METADATA_HARP}"
  fail=1
fi

# HARD 2: the unauthenticated /mcp over HaRP carries a WWW-Authenticate header with the
# resource_metadata pointer. That header is the first step of the OAuth discovery flow,
# and the reason the route is PUBLIC since plan 03-01.
case "${WWWAUTH_MCP_HARP}" in
  *resource_metadata=*)
    printf 'PASS  /mcp over HaRP carries WWW-Authenticate with resource_metadata\n'
    ;;
  *)
    printf 'FAIL  /mcp over HaRP has no resource_metadata pointer (got: %s)\n' "${WWWAUTH_MCP_HARP:-none}"
    fail=1
    ;;
esac

# HARD 3: /heartbeat over HaRP is rejected, never served to the outside. The plan expected a
# 404 from the route mismatch; 02-04 measured a 502, because HaRP drops the internal
# lifecycle paths one layer earlier (silent-drop, reported as 502 by Caddy). Both are a
# rejection, which is the property that has to hold: the lifecycle path is not reachable.
if [ "${STATUS_HEARTBEAT_HARP}" != "200" ] && [ "${STATUS_HEARTBEAT_HARP}" != "000" ]; then
  printf 'PASS  heartbeat over HaRP is rejected (%s, not served)\n' "${STATUS_HEARTBEAT_HARP}"
else
  printf 'FAIL  heartbeat over HaRP is %s, expected a rejection\n' "${STATUS_HEARTBEAT_HARP}"
  fail=1
fi

printf '\ncanonical root path status: %s (recorded, not enforced)\n' "${STATUS_ROOT}"

if [ "${fail}" -ne 0 ]; then
  printf '\nspike measurement: at least one hard expectation failed\n' >&2
  exit 1
fi
printf '\nspike measurement: all hard expectations hold\n'
