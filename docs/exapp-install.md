# ExApp installation

**Status:** proven on a local HaRP topology
**Measured on:** 2026-08-15
**Scope:** installing this app as an AppAPI ExApp with the HaRP deploy daemon, on
`docker compose`, from a locally built image. Nextcloud All-in-One is the second smoke step
and is handled as a named handoff to phase 5 in the Nextcloud AIO section below.

Everything below was executed against Nextcloud 34.0.2 with AppAPI 34.0.0 and the image
`ghcr.io/nextcloud/nextcloud-appapi-harp:release`. The outputs in the Evidence section are
copied verbatim from that run.

## Topology

Four containers, described by `compose.exapp.yml` (project name `nc-mcp-exapp`):

| Service | Image | Why it is there |
|---------|-------|-----------------|
| `caddy` | `caddy:2` | Reverse proxy on `127.0.0.1:8081`. It routes `/exapps/*` to HaRP and everything else to Nextcloud. |
| `nextcloud` | `nextcloud:34-apache` | The server. It publishes no port of its own and is reachable through Caddy only. |
| `appapi-harp` | `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | The deploy daemon. It starts the ExApp container over the Docker socket and proxies every request to it. |
| `registry` | `registry:2` | A loopback registry on `127.0.0.1:5000` that holds the locally built ExApp image. |

**The reverse proxy is not optional.** AppAPI reaches an ExApp under
`<nextcloud_url>/exapps/<appid>`, which means through the public URL of the Nextcloud
instance and therefore through whatever sits in front of it. Without a `/exapps/*` rule the
installation fails at the very first step, the heartbeat, with "heartbeat check failed.
Make sure that Nextcloud instance and ExApp can reach it other." Nextcloud All-in-One ships
exactly this rule in its bundled Caddy, and `deploy/Caddyfile` rebuilds it.

Two more properties of the file are deliberate:

* Every published port binds to `127.0.0.1`. The instance carries throwaway credentials and
  runs with the bruteforce guard disabled, so a `0.0.0.0` binding would hand a trivially
  ownable Nextcloud to everyone on the same network.
* HaRP publishes no port at all. Caddy reaches it inside the compose network, which is the
  only place that needs to reach it.

## Install

```
export HP_SHARED_KEY="$(openssl rand -hex 32)"
docker compose -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh
docker compose -f compose.exapp.yml down        # when you are done, keeps the volume
```

The first line is not optional. The compose file used to carry a fixed default for
`HP_SHARED_KEY`, which meant the documented command produced the same key on every machine
that ever ran it, published in this repository, and the bootstrap then wrote it into
`.env.exapp` where it looked generated (WR-11). `up` now fails with a named variable until a
real one is exported, and the bootstrap refuses anything that is not 64 hex characters.

`down` stops the four services of the file. The ExApp container is not one of them: the
deploy daemon created it over the Docker socket, so it keeps running and has to be stopped
separately, which is also why the compose network stays in use until then.

```
docker stop nc_app_mcp_connector
```

The bootstrap script is idempotent: it creates the test users and their calendars, installs
or enables AppAPI, registers the HaRP daemon, builds the image, pushes it into the loopback
registry and registers the app. A second run is a no-op apart from a fresh app password in
`.env.exapp`.

The registration overrides exactly three fields of `appinfo/info.xml`: registry, image and
image tag. The manifest keeps pointing at `ghcr.io`, because that is the state the app store
will see, while the local test needs an image that exists today. Nothing is published; the
image never leaves the loopback registry.

## Evidence

All commands below were run on **2026-08-15** on the development host, in the order shown.

### 1. The app is registered and enabled

```
docker compose -f compose.exapp.yml exec -T --user www-data nextcloud php occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.0 [enabled]
```

The deploy daemon it belongs to:

```
docker compose -f compose.exapp.yml exec -T --user www-data nextcloud php occ app_api:daemon:list
Registered ExApp daemon configs:
+-----+-------------------+---------------------+----------------+----------+------------------+--------------+---------+------------------+-------------------------+
| Def | Name              | Display name        | Deploy ID      | Protocol | Host             | NC Url       | Is HaRP | HaRP FRP Address | HaRP Docker Socket Port |
+-----+-------------------+---------------------+----------------+----------+------------------+--------------+---------+------------------+-------------------------+
| *   | harp_proxy_docker | Harp Proxy (Docker) | docker-install | http     | appapi-harp:8780 | http://caddy | yes     | appapi-harp:8782 | 24000                   |
+-----+-------------------+---------------------+----------------+----------+------------------+--------------+---------+------------------+-------------------------+
```

### 2. The container the daemon started is healthy

```
docker ps --filter name=mcp_connector --format '{{.Names}} {{.Status}}'
nc_app_mcp_connector Up 3 minutes (healthy)
```

### 3. Deploy and init both reached 100

The lifecycle state AppAPI keeps for the app, read out of the `ex_apps` table:

```
docker compose -f compose.exapp.yml exec -T --user www-data nextcloud php -r '
require_once "/var/www/html/lib/base.php";
$db = \OCP\Server::get(\OCP\IDBConnection::class);
$q = $db->getQueryBuilder();
$q->select("appid","version","enabled","port","status")->from("ex_apps");
foreach ($q->executeQuery()->fetchAll() as $row) { echo $row["appid"], " | enabled=", $row["enabled"], " | port=", $row["port"], " | status=", $row["status"], PHP_EOL; }
'
mcp_connector | enabled=1 | port=23000 | status={"deploy":100,"init":100,"action":"","type":"","error":"","deploy_start_time":1786788523,"init_start_time":1786788531}
```

`init: 100` is the interesting number: `POST /init` was answered with 200 and the app then
reported progress 100 back to Nextcloud over OCS. An app that answers 200 and stays silent
hangs at 0 percent until the init timeout expires.

### 4. The MCP route rejects an anonymous request

```
curl -i -s -X POST -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  http://127.0.0.1:8081/exapps/mcp_connector/mcp
HTTP/1.1 403 Forbidden
Content-Length: 13
Content-Type: text/plain
Via: 1.1 Caddy
```

The 403 comes from HaRP, not from the app: the route is declared with `access_level` `USER`,
and HaRP could not resolve a user for the request. The request never reaches the container.

### 5. The MCP route serves a request with a user app password

```
curl -i -s -u "alice:<app password>" -X POST -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"evidence","version":"1.0"}}}' \
  http://127.0.0.1:8081/exapps/mcp_connector/mcp
HTTP/1.1 200 OK
Cache-Control: no-cache, no-transform
Content-Type: text/event-stream
Mcp-Session-Id: 1d92d8a13d114fafac3f6926ffa93489
Server: uvicorn
Via: 1.1 Caddy

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"capabilities":{...},"instructions":"Read and create content in the user's own Nextcloud. This server can never delete, overwrite or re-share anything.","protocolVersion":"2025-06-18","serverInfo":{"name":"MCP Connector","version":"0.1.0"}}}
```

`Server: uvicorn` is the proof that the answer came out of the ExApp container. HaRP resolved
the app password to the user `alice` and signed the request with the AppAPI headers.

### 6. The lifecycle paths are not reachable from outside

```
curl -i -s http://127.0.0.1:8081/exapps/mcp_connector/heartbeat
HTTP/1.1 502 Bad Gateway
Server: Caddy
Date: Sat, 15 Aug 2026 10:12:07 GMT
Content-Length: 0
```

Two controls hold here, and this measurement shows the outer one. `appinfo/info.xml`
declares no route that matches `/heartbeat`, `/init` or `/enabled`, and HaRP additionally
blocks those three paths for anything that does not carry a valid AppAPI signature: it logs
"Only requests from AppAPI allowed to the internal endpoints" and drops the connection
without an answer, which Caddy reports to the client as a `502` with an empty body. The
plan expected a `404` from the route mismatch; the measured behaviour is stricter, because
the request is dropped one layer earlier. Either way the container never sees the call, and
`/enabled` cannot be used from the outside to switch the app off.

## Development loop

Rebuilding an image per iteration is slow. AppAPI has a second deploy mode for that, and the
script knows it:

```
docker compose -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh --manual
```

This registers a `manual-install` daemon and the app on a fixed port with a fixed secret, so
a locally started process serves the requests:

```
set -a && . ./.env.exapp && set +a
APP_PORT=23001 nc-mcp-exapp
```

**Do not add `APP_HOST=0.0.0.0` here.** That is what this document used to print, and it
contradicts the loopback rule two sections above (WR-12). The default of `entry_exapp` is
already `127.0.0.1`, and it has to stay that way: in this mode there is no HaRP and no
manifest filter in front of the process, so `/init` and `/enabled` are reachable directly and
are guarded by `APP_SECRET` alone, which sits in `.env.exapp` in the same directory.
`/heartbeat` authenticates nothing at all by contract.

Docker Desktop reaches a service bound to the host's loopback through
`host.docker.internal`, which is the address the manual daemon is registered with, so
nothing else is needed on Windows or macOS. On a plain Linux Docker, where
`host.docker.internal` is not a loopback path, forward the port explicitly instead of
opening the process to the LAN:

```
socat TCP-LISTEN:23001,fork,bind=172.29.42.1 TCP:127.0.0.1:23001
```

`172.29.42.1` is the gateway of the compose network from `compose.exapp.yml`, so the
listener is reachable for the containers of this topology and for nothing else.

Restart that process after every re-registration. `APP_SECRET` is handed out at registration
time, and a process that still holds the previous one answers 401 to everything while
Nextcloud rejects everything it sends.

## Known pitfalls

These four were the ones that actually cost time in this setup.

**1. No reverse proxy in front of Nextcloud.** The heartbeat is fetched from
`<nextcloud_url>/exapps/<appid>/heartbeat`, so a container name in `nextcloud_url` is not
enough: that URL has to be served by something that knows the `/exapps/` prefix. Pass
`nextcloud_url` to `occ app_api:daemon:register` explicitly as well, because AppAPI silently
downgrades `https` to `http` when the field is missing.

**2. A non-root ExApp image needs a writable `/certs`.** HaRP installs the FRP client
certificate by running commands inside the running container, with the identity of that
container. As uid 10001 the `mkdir -p /certs/frp` fails with "Permission denied", the
certificate installation answers 500, the tunnel client falls back to a plaintext handshake,
the FRP server closes the connection and every heartbeat is answered with 503. The Dockerfile
therefore creates `/certs` owned by the unprivileged user. The same call also tries to run
`update-ca-certificates`, which stays impossible without root; that failure is logged by HaRP
and is harmless as long as the instance is not behind a private certificate authority.

Since WR-04 the container no longer accepts the fallback. `entrypoint.sh` waits up to
`FRP_CERT_WAIT_SECONDS` (60 by default) for `/certs/frp` and then refuses to start, because
the fallback writes `transport.tls.enable = false` and sends `HP_SHARED_KEY` over the wire in
the clear, which hands whoever reads that path the right to register their own tunnel. On a
trusted local network the downgrade can be taken deliberately with `ALLOW_PLAINTEXT_FRP=1`;
there is no way to take it by accident.

**3. The ExApp port has to be inside the FRP range.** The FRP server inside HaRP accepts
remote ports 23000 to 23999 only. A registration with any other port produces
`start error: port not allowed` in the container log and a 503 on every request, because
HAProxy then has no backend at all. AppAPI picks from the same range when the registration
carries no port.

**4. HaRP caches the app record.** After a failed registration the daemon keeps the old
host and port for a while, so a corrected re-registration can still fail with a 503 that
looks identical to the original error. Recreate the container to clear it:

```
docker compose -f compose.exapp.yml up -d --no-deps --force-recreate appapi-harp
```

`HP_LOG_LEVEL=info` in the environment makes the daemon log the line that says where a
request was actually routed, which is the fastest way to tell a cache problem from a
configuration problem.

## Security notes for production

**The Docker socket is mounted into HaRP, and that is root on the host.** A deploy daemon
that starts containers cannot work without it, so this is accepted for a local test topology
that listens on loopback only and is stopped afterwards (threat T-02-31). It is not a
recommendation for a server: there, run HaRP on a host that does nothing else, or use the
Kubernetes daemon, and never expose its port.

**The registry in this topology is unauthenticated and unencrypted** (threat T-02-32). It
exists because the image is not published before the store submission, it listens on
`127.0.0.1` only, and it holds exactly one image. Do not copy that part into anything that
is reachable from a network.

**`.env.exapp` carries working secrets** (app passwords, the HaRP shared key and the app
secret). It is git-ignored; `.env.exapp.example` documents the variable names and holds
placeholders only.

## Nextcloud AIO

Success Criterion 1 of phase 2 names two smoke targets: the `docker compose` HaRP topology
above, and Nextcloud All-in-One. This section records the decision on the second one, because
D-31 requires it to be handed over with a reason rather than dropped in silence.

**Decision: not run on this development host. Handed to phase 5 as a named open item.**

**Where it stops.** The AIO mastercontainer refuses to start the Nextcloud stack until its
setup step validates a domain: it wants a publicly resolvable domain name with a valid, public
TLS certificate and inbound reachability on ports 80 and 443, and it runs that check before it
will bring up any container the ExApp could be installed into. The abort boundary in D-31 names
exactly this, a step that demands a publicly resolvable domain, a public certificate or an
outward port forward, as disproportionate for a loopback development machine, so the smoke stops
at the domain validation and does not proceed to installing the app.

A second reason reinforces the same call on this specific host. The AIO mastercontainer drives
the Docker daemon through a mounted socket to create and manage its own containers. That daemon
also runs the owner's in-daily-use test instance (`nc-mcp-test` on `127.0.0.1:8080`), and the
standing instruction is to never touch it. Starting a socket-privileged mastercontainer next to
it is a risk not worth taking for a reachability smoke that is already blocked by the domain
requirement.

**What is still missing, for phase 5.** To run the AIO smoke, these steps remain, in order:

1. A host with a publicly resolvable domain and a valid TLS certificate, or the AIO Let's
   Encrypt path with inbound 80 and 443 open to that domain.
2. Start the AIO mastercontainer and complete its domain validation and initial setup.
3. Enable the optional AppAPI and HaRP container in the AIO interface. Research assumption A6
   is that this is the only AIO specific action needed, but it is unverified: it may also
   require registering the HaRP deploy daemon, which the compose bootstrap does explicitly.
4. Install this app as an ExApp through the AIO managed AppAPI, from a published image or the
   store, since the loopback registry of the compose topology is not present in AIO.
5. Repeat the permission fidelity smoke over the AIO topology: alice finds her own content and
   bob finds nothing of hers, over files, notes and unified search, the same proof
   `tests/integration/test_permission_fidelity_exapp.py` runs against the compose topology.
6. Record `occ app_api:app:list` from the AIO instance as the evidence for case A.

**Handoff.** This is an open item for phase 5 (store submission), not a closed one. It is also
reported in the plan summary as an owner and phase 5 item so it is tracked in the project state
rather than remembered only here.

## Related

- Manifest and routes: [../appinfo/info.xml](../appinfo/info.xml)
- Topology: [../compose.exapp.yml](../compose.exapp.yml), [../deploy/Caddyfile](../deploy/Caddyfile)
- Installation script: [../scripts/bootstrap_exapp.sh](../scripts/bootstrap_exapp.sh)
- Requirement `EXAPP-01`, decision D-31
