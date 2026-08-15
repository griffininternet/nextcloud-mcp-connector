#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# The container entrypoint: two guards, then the verbatim HaRP start.sh (WR-02, WR-04).
#
# start.sh is copied from github.com/nextcloud/HaRP without a single change and stays that
# way, because it is the published contract between HaRP and an ExApp. Everything this
# deployment wants to decide before it runs therefore lives here.
#
# Guard 1 (WR-04): start.sh falls back to `transport.tls.enable = false` when /certs/frp
# is missing, and then sends HP_SHARED_KEY over the wire in the clear. Whoever can read
# the path between this container and HaRP gets the key and can register their own tunnel.
# The certificate arrives after the container starts, because HaRP installs it by running
# commands inside the running container, so this waits for it instead of deciding on the
# first millisecond of the first boot. When it never arrives, the container refuses to
# start rather than downgrading silently, which is what D-27 asks for everywhere else.
#
# Guard 2 (WR-02): the DNS rebinding protection of the MCP transport is switched off for
# the HaRP path only. Behind HaRP the Host header is the one of the reverse proxy, so the
# check would be a permanent 421 trap. Without HaRP, in a docker-install daemon or in a
# hand started container with a published port, the check is exactly the defence that
# belongs there, and baking the switch into an image layer disarmed it for every mode.
# NC_MCP_ALLOWED_HOSTS stays configurable either way; a value set in the environment is
# never overwritten here.
set -eu

FRP_CERT_DIR="/certs/frp"
FRP_CERT_WAIT_SECONDS="${FRP_CERT_WAIT_SECONDS:-60}"

# The directory alone is not the certificate (IN-02): HaRP creates it with `mkdir -p`
# before it copies the three files start.sh writes into the frpc configuration
# (client.crt, client.key and ca.crt). In the race between the mkdir and the copy a
# directory check lets start.sh emit a TLS configuration whose certFile does not exist
# yet, and frpc dies with a misleading error. So the wait is for the files themselves.
frp_certs_present() {
    [ -f "${FRP_CERT_DIR}/client.crt" ] &&
        [ -f "${FRP_CERT_DIR}/client.key" ] &&
        [ -f "${FRP_CERT_DIR}/ca.crt" ]
}

if [ -n "${HP_SHARED_KEY:-}" ]; then
    waited=0
    while ! frp_certs_present && [ "${waited}" -lt "${FRP_CERT_WAIT_SECONDS}" ]; do
        if [ "${waited}" -eq 0 ]; then
            echo "waiting for HaRP to install the FRP client certificate in ${FRP_CERT_DIR}"
        fi
        sleep 1
        waited=$((waited + 1))
    done

    if ! frp_certs_present; then
        if [ "${ALLOW_PLAINTEXT_FRP:-0}" = "1" ]; then
            echo "WARNING: the certificate files in ${FRP_CERT_DIR} are still incomplete" >&2
            echo "WARNING: after ${FRP_CERT_WAIT_SECONDS}s. ALLOW_PLAINTEXT_FRP=1 is set, so" >&2
            echo "WARNING: frpc will send HP_SHARED_KEY unencrypted. Only ever do this on" >&2
            echo "WARNING: a trusted local network." >&2
        else
            echo "ERROR: ${FRP_CERT_DIR} is still missing client.crt, client.key or ca.crt" >&2
            echo "ERROR: after ${FRP_CERT_WAIT_SECONDS}s." >&2
            echo "ERROR: frpc would send HP_SHARED_KEY in the clear, and whoever reads it" >&2
            echo "ERROR: can attach their own tunnel to HaRP. Refusing to start." >&2
            echo "ERROR: The usual cause is that /certs is not writable for uid 10001, so" >&2
            echo "ERROR: the certificate installation answered 500 (exapp-install.md," >&2
            echo "ERROR: pitfall 2). Set ALLOW_PLAINTEXT_FRP=1 to override on a trusted" >&2
            echo "ERROR: local network, or raise FRP_CERT_WAIT_SECONDS on a slow host." >&2
            exit 1
        fi
    fi

    export NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=1
fi

exec /start.sh "$@"
