#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Docker HEALTHCHECK of the ExApp container (T-02-25).
#
# AppAPI reads the container health before it sends the first heartbeat, and a container
# without a healthcheck counts as healthy, which hides a failed start until the fifteen
# minute deploy timeout expires. So the probe has to be honest about both transports.
#
# Behind HaRP the process listens on a unix socket and there is no TCP port at all;
# HP_SHARED_KEY is the switch, the very same one entry_exapp.main uses. A probe against
# 127.0.0.1:APP_PORT would be permanently red there, and AppAPI would sit out its timeout
# on a container that is in fact serving. Without HaRP the socket does not exist and the
# port is the only way in.
#
# The exit code of curl is the exit code of this script: exec, no wrapper, no retry. The
# retries belong to the HEALTHCHECK instruction, not here.
set -eu

if [ -n "${HP_SHARED_KEY:-}" ]; then
    exec curl -fsS -o /dev/null \
        --unix-socket "${HP_EXAPP_SOCK:-/tmp/exapp.sock}" \
        http://localhost/heartbeat
fi

exec curl -fsS -o /dev/null "http://127.0.0.1:${APP_PORT}/heartbeat"
