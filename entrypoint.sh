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

if [ -n "${HP_SHARED_KEY:-}" ]; then
    waited=0
    while [ ! -d "${FRP_CERT_DIR}" ] && [ "${waited}" -lt "${FRP_CERT_WAIT_SECONDS}" ]; do
        if [ "${waited}" -eq 0 ]; then
            echo "waiting for HaRP to install the FRP client certificate in ${FRP_CERT_DIR}"
        fi
        sleep 1
        waited=$((waited + 1))
    done

    if [ ! -d "${FRP_CERT_DIR}" ]; then
        if [ "${ALLOW_PLAINTEXT_FRP:-0}" = "1" ]; then
            echo "WARNING: ${FRP_CERT_DIR} is still missing after ${FRP_CERT_WAIT_SECONDS}s." >&2
            echo "WARNING: ALLOW_PLAINTEXT_FRP=1 is set, so frpc will send HP_SHARED_KEY" >&2
            echo "WARNING: unencrypted. Only ever do this on a trusted local network." >&2
        else
            echo "ERROR: ${FRP_CERT_DIR} is still missing after ${FRP_CERT_WAIT_SECONDS}s." >&2
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
