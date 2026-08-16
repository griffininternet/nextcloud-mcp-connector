#!/usr/bin/env bash
# Point the staging host name at the staging machine, over the Cloudflare API.
#
#   export CF_DNS_TOKEN=...            # never as an argument, see below
#   export CF_ZONE_ID=...              # the zone the name belongs to
#   export NC_STAGING_DOMAIN=nc-staging.example.com
#   bash scripts/staging_dns.sh                 # takes the public address of this machine
#   bash scripts/staging_dns.sh 203.0.113.10    # or an address given explicitly
#
# Idempotent: an existing A record for the name is updated, a missing one is created. It
# never creates a second record for the same name, because two A records for one name are
# a name that answers with a different address every other query, and half of those
# answers would be a certificate order that fails.
#
# The record is always DNS-only (proxied=false, the grey cloud), and that is not a
# preference:
#
#   * the certificate is issued over HTTP-01 or TLS-ALPN, and both challenges have to
#     arrive at the staging machine. Behind the Cloudflare proxy they never do, and a
#     handful of failed orders is a rate limit that lasts a week,
#   * the MCP transport holds a streaming response open for the lifetime of a session, and
#     a proxy in between is a second opinion on when that response is over.
#
# The token is read from the environment and never from an argument: the argv of a process
# is world readable in `ps aux` for the whole duration of the call, and this token can
# rewrite every record of the zone. For the same reason it is handed to curl through a
# configuration file on stdin rather than through -H (WR-06).
set -euo pipefail

API="https://api.cloudflare.com/client/v4"
TTL=120

if [ -z "${CF_DNS_TOKEN:-}" ]; then
  echo "ERROR: CF_DNS_TOKEN is not set." >&2
  echo "Export a Cloudflare API token with the permission Zone -> DNS -> Edit on the zone" >&2
  echo "this host name belongs to, in the shell that runs this script:" >&2
  echo "  export CF_DNS_TOKEN=...   # never pass it as an argument, it would be public" >&2
  echo "The token is not read from any file in this repository, and it is never written" >&2
  echo "into one." >&2
  exit 1
fi

ZONE_ID="${CF_ZONE_ID:?set CF_ZONE_ID to the id of the zone (Cloudflare dashboard, overview page of the zone)}"
DOMAIN="${NC_STAGING_DOMAIN:?set NC_STAGING_DOMAIN to the full host name, for example nc-staging.example.com}"
IP="${1:-${NC_STAGING_IP:-}}"

if ! printf '%s' "${DOMAIN}" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}$'; then
  echo "ERROR: NC_STAGING_DOMAIN is '${DOMAIN}', which is not a host name." >&2
  exit 1
fi

if ! printf '%s' "${ZONE_ID}" | grep -Eq '^[0-9a-f]{32}$'; then
  echo "ERROR: CF_ZONE_ID is not 32 hex characters. It is the 'Zone ID' from the overview" >&2
  echo "page of the zone in the Cloudflare dashboard." >&2
  exit 1
fi

# Every call to the API goes through here, so the token has exactly one way into curl: a
# configuration file on stdin, which is private to the two processes at its ends. The
# status code is appended to the body on its own line, because a Cloudflare error is a
# JSON body with a 200-shaped envelope often enough to be worth checking both.
cf_api() {
  local method="$1" url="$2" data="${3:-}"
  local args=(-sS --config - -X "${method}" -H "Content-Type: application/json" -w '\n%{http_code}')
  if [ -n "${data}" ]; then
    args+=(--data "${data}")
  fi
  printf 'header = "Authorization: Bearer %s"\n' "${CF_DNS_TOKEN}" | curl "${args[@]}" "${url}"
}

http_code() {
  printf '%s' "$1" | tail -n1
}

http_body() {
  printf '%s' "$1" | sed '$d'
}

require_success() {
  local what="$1" response="$2" code body
  code="$(http_code "${response}")"
  body="$(http_body "${response}")"
  if [ "${code}" = "200" ] && printf '%s' "${body}" | grep '"success":true' >/dev/null; then
    return 0
  fi
  echo "ERROR: ${what} failed (http ${code})." >&2
  echo "${body}" >&2
  echo "The two usual reasons are a token without Zone -> DNS -> Edit on this zone, and a" >&2
  echo "host name that belongs to a different zone than CF_ZONE_ID." >&2
  return 1
}

# The public address of this machine, as the internet sees it. Only used when no address
# was given: on a machine behind NAT the answer would be right and useless, which is why
# the argument exists.
detect_ip() {
  local trace
  trace="$(curl -sS --max-time 15 https://cloudflare.com/cdn-cgi/trace || true)"
  printf '%s' "${trace}" | sed -n 's/^ip=//p' | head -n1
}

if [ -z "${IP}" ]; then
  IP="$(detect_ip)"
  if [ -z "${IP}" ]; then
    echo "ERROR: could not determine the public address of this machine." >&2
    echo "Pass it explicitly: bash scripts/staging_dns.sh 203.0.113.10" >&2
    exit 1
  fi
  echo "address: detected ${IP} as the public address of this machine"
else
  echo "address: using ${IP}"
fi

if ! printf '%s' "${IP}" | grep -Eq '^[0-9]{1,3}(\.[0-9]{1,3}){3}$'; then
  echo "ERROR: '${IP}' is not an IPv4 address. This script sets an A record." >&2
  exit 1
fi

# proxied is written out on purpose rather than left to the account default: the default
# for a new record in a zone with the proxy enabled is the orange cloud, and that is
# exactly the state this record must never be in.
PAYLOAD="$(printf '{"type":"A","name":"%s","content":"%s","ttl":%s,"proxied":false}' \
  "${DOMAIN}" "${IP}" "${TTL}")"

echo "zone: looking for an existing A record for ${DOMAIN}"
LOOKUP="$(cf_api GET "${API}/zones/${ZONE_ID}/dns_records?type=A&name=${DOMAIN}")"
require_success "the record lookup" "${LOOKUP}"

# The record id out of the list response. Cloudflare ids are 32 hex characters and the
# record's own id is the first one in the object, so the first match is the record. This is
# a text extraction and not a JSON parse, because jq is not on a fresh machine; the shape
# it relies on is asserted by the update call right after, which fails loudly on a wrong id.
RECORD_ID="$(http_body "${LOOKUP}" | tr ',' '\n' | sed -n 's/.*"id":"\([0-9a-f]\{32\}\)".*/\1/p' | head -n1)"

if [ -z "${RECORD_ID}" ]; then
  echo "record: none yet, creating it"
  RESULT="$(cf_api POST "${API}/zones/${ZONE_ID}/dns_records" "${PAYLOAD}")"
  require_success "the record creation" "${RESULT}"
  echo "record: created"
else
  echo "record: ${RECORD_ID} exists, updating it"
  RESULT="$(cf_api PUT "${API}/zones/${ZONE_ID}/dns_records/${RECORD_ID}" "${PAYLOAD}")"
  require_success "the record update" "${RESULT}"
  echo "record: updated"
fi

if ! http_body "${RESULT}" | grep '"proxied":false' >/dev/null; then
  echo "ERROR: the record came back without proxied=false." >&2
  echo "Set the grey cloud by hand in the dashboard before continuing: behind the proxy" >&2
  echo "the certificate order never reaches the machine." >&2
  exit 1
fi

echo
echo "${DOMAIN} -> ${IP}, DNS-only (grey cloud), ttl ${TTL}s."
echo "Wait until it resolves everywhere, then continue with docs/staging-setup.md:"
echo "  getent hosts ${DOMAIN}"
