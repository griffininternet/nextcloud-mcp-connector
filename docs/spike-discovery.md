# Discovery spike (AUTH-06)

**Status:** go
**Measured on:** 2026-08-15
**Scope:** whether an OAuth capable MCP client can reach the discovery metadata of this
ExApp from the outside, unauthenticated, and over which proxy path. This is the go or no-go
that decides the OAuth topology of phase 3 (D-29). It does not implement OAuth; that is
phase 3.

Measured against Nextcloud 34.0.2 with AppAPI 34.0.0, on the local HaRP topology from
`compose.exapp.yml`, with the ExApp deployed under the HaRP daemon and carrying the
discovery routes of plan 02-05.

## Result

Yes: an unauthenticated discovery request reaches this ExApp from the outside, with 200 and
JSON, over both the HaRP path and the PHP proxy path, and the `WWW-Authenticate` pointer
that a 401 carries survives both proxies to the client unchanged. Phase 3 can therefore
rely on the `resource_metadata` pointer of the MCP authorization flow.

## Measurement matrix

Produced by `scripts/spike_discovery.sh` on **2026-08-15** against Nextcloud **34.0.2** and
AppAPI **34.0.0**. `HaRP` is `/exapps/mcp_connector/...`, `PHP-Proxy` is
`/apps/app_api/proxy/mcp_connector/...`, `root` is the domain root without any prefix.

| Path | Way | Auth | Status | Headers of interest |
|------|-----|------|--------|---------------------|
| `/.well-known/oauth-protected-resource/mcp` | HaRP | none | 200 | `content-type: application/json`, `cache-control: no-store` |
| `/.well-known/oauth-protected-resource/mcp` | PHP-Proxy | none | 200 | `content-type: application/json`, `cache-control: no-store` |
| `/.well-known/mcp-discovery-probe` | HaRP | none | 401 | `cache-control: no-store`, `www-authenticate: Bearer resource_metadata="http://127.0.0.1:8765/.well-known/oauth-protected-resource/mcp"` |
| `/.well-known/mcp-discovery-probe` | PHP-Proxy | none | 401 | `cache-control: no-store`, `www-authenticate: Bearer resource_metadata="http://127.0.0.1:8765/.well-known/oauth-protected-resource/mcp"` |
| `/mcp` | HaRP | none | 403 | `content-type: text/plain` (rejected by HaRP, access level USER) |
| `/mcp` | PHP-Proxy | none | 404 | the proxy access level check fails closed |
| `/mcp` | HaRP | basic:alice | 200 | `content-type: text/event-stream` (streaming, see below) |
| `/mcp` | PHP-Proxy | basic:alice | 200 | `content-type: text/event-stream` |
| `/heartbeat` | HaRP | none | 502 | connection dropped by HaRP (internal path) |
| `/heartbeat` | PHP-Proxy | none | 404 | no declared route matches |
| `/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp` | root | none | 404 | answered by Nextcloud, not the ExApp |

Two things the matrix settles. First, the metadata route and the probe are both reachable
unauthenticated over the PHP proxy path as well, not only over HaRP, so the AUTH-06 go
criterion (unauthenticated, from outside, through the AppAPI proxy) holds on both paths.
Second, the `resource_metadata` pointer in the `WWW-Authenticate` header is identical on
both proxy paths: neither proxy strips or rewrites it.

The `resource` value in the metadata document reads `http://127.0.0.1:8765/mcp`, the
documented default of `config.public_url`, because the deployed container carries no
`NC_MCP_PUBLIC_URL`. That is expected for the spike: it measures reachability and header
pass through, not the value of this field. Phase 3 builds the real Protected Resource
Metadata from the SDK `AuthSettings`, with the true public URL.

### The discovery route leaks nothing

The full metadata body, fetched unauthenticated over HaRP, is:

```
{"resource":"http://127.0.0.1:8765/mcp","authorization_servers":[],"bearer_methods_supported":["header"]}
```

The probe body is empty (`{}`). Neither carries the `APP_SECRET`, an internal Nextcloud
host or path, an `EX-APP-*` header value or any configuration beyond the public base URL and
the method list. The route reads no request header to build its answer, so a forged `Host`
does not change it. This is the property T-02-40 and T-02-41 require, and it is covered by
`tests/unit/test_exapp_discovery.py` in addition to this live measurement.

## The canonical RFC 9728 path

The canonical metadata URL for the resource `https://<nc>/exapps/mcp_connector/mcp` is, per
RFC 9728 section 3.1, `https://<nc>/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp`.
That path sits on the domain root and belongs to Nextcloud, not to the ExApp: HaRP only
routes `/exapps/*`, so the root path never reaches the container.

Measured result: **404**, answered by Nextcloud. This is the actual finding of the spike.
The ExApp cannot serve its own canonical metadata path, because that path is not below its
prefix. Phase 3 therefore does not rely on the canonical path being reachable; it relies on
the `resource_metadata` pointer instead, and offers the reverse proxy rule below as a
fallback for clients that insist on the canonical path.

## Recommended topology for phase 3

Three ways, in this order.

**1. The `resource_metadata` pointer in the `WWW-Authenticate` header (priority 1).** The
MCP client SDK reads `resource_metadata` from the 401 first (SEP-985), before it tries the
canonical path. The measurement shows the header reaches the client unchanged over both
proxy paths, so a spec compliant client discovers the metadata without any extra
configuration. This is the primary path for phase 3.

**2. An admin reverse proxy rule that maps the canonical root path onto the ExApp.** For a
client that only tries the canonical path, the admin can map it to the ExApp metadata route.
This opens no new attack surface: the route it exposes is the same public, leak free metadata
document that the pointer already advertises, so the rule only adds a second way to reach an
endpoint that is public by design.

Caddy:

```
@prm path /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp
handle @prm {
    rewrite * /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
    reverse_proxy {$HARP_HOST}:8780 {
        transport http {
            read_timeout 1800s
        }
    }
}
```

nginx:

```
location = /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp {
    proxy_pass http://harp:8780/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp;
    proxy_read_timeout 1800s;
}
```

**3. An own subdomain, or the standalone HTTP mode of phase 1.** If neither of the above
fits an installation, the connector still runs as the standalone HTTP server of phase 1
behind an own hostname, where the canonical path is served by the app itself because there
is no stripped prefix. This is the escape hatch, not the recommendation.

### What plan 03-01 implemented, and in which order a client walks it

An OAuth capable client looks for the discovery documents in this order. Only the first and
the third work without any action by an administrator, and the connector serves both.

1. **The protected resource document, through the pointer in the 401.** The client calls
   `/mcp`, gets 401 with
   `WWW-Authenticate: Bearer error="invalid_token", ..., resource_metadata="<public url>/.well-known/oauth-protected-resource/mcp"`
   and follows that URL. The document is served below our own prefix, where the request
   arrives after HaRP stripped it. **Works out of the box.**
2. **The authorization server document at its canonical root paths.**
   `/.well-known/oauth-authorization-server/exapps/mcp_connector` and
   `/.well-known/openid-configuration/exapps/mcp_connector` both carry two path segments,
   Nextcloud's `WellKnownController` matches one, so both answer 404. **Needs the reverse
   proxy rules below.**
3. **The authorization server document at the path appended OpenID variant.**
   `<public url>/.well-known/openid-configuration` lies below our prefix and survives the
   stripping. The MCP Python SDK client tries this one on its own after the two canonical
   spellings. **Works out of the box.**

Not measured yet: whether the Claude.ai and the ChatGPT connector try way 3 themselves, or
stop after the canonical paths. That measurement belongs to plan 03-09, which reads the
access log of the staging instance during a real connect.

The rules for both canonical root paths, ready to copy. Caddy, as shipped in
[../deploy/Caddyfile](../deploy/Caddyfile):

```
route /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp {
	rewrite * /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
	reverse_proxy appapi-harp:8780
}

route /.well-known/oauth-authorization-server/exapps/mcp_connector {
	rewrite * /exapps/mcp_connector/.well-known/oauth-authorization-server
	reverse_proxy appapi-harp:8780
}
```

The equivalent for nginx, with the HaRP upstream named `harp`:

```
location = /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp {
    proxy_pass http://harp:8780/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp;
    proxy_read_timeout 1800s;
}

location = /.well-known/oauth-authorization-server/exapps/mcp_connector {
    proxy_pass http://harp:8780/exapps/mcp_connector/.well-known/oauth-authorization-server;
    proxy_read_timeout 1800s;
}
```

Both use an exact path match, `route /path` in Caddy and `location =` in nginx, so they
rewrite these two strings and change no other Nextcloud path.

## Streaming

A real MCP session over the HaRP path, with the modern SDK client, streaming included:

```
set -a && . ./.env.exapp && set +a
export NC_MCP_USER="$NC_MCP_TEST_USER" NC_MCP_APP_PASSWORD="$NC_MCP_TEST_APP_PASSWORD"
uv run --no-sync python tests/compat/modern_client_check.py \
  http://127.0.0.1:8081/exapps/mcp_connector/mcp
```

Output:

```
modern client: tools/list returned 15 tools
```

That number is the one this run listed and is left as recorded; the set is 16 since
`prepare_context` was added, and `tests/contract/test_tool_surface.py` is what holds it.

Exit code 0. The `/mcp` answer is `content-type: text/event-stream` (see the matrix), so the
Streamable HTTP transport streams through HaRP end to end, which confirms the maintainer
statement in app_api#825 against a running instance.

## Open items for phase 3

* **Done in plan 03-01: `/mcp` switched from `access_level` USER to PUBLIC, together with an
  own bearer check.** In phase 2 `/mcp` was USER on purpose: HaRP resolves the user from an
  app password and the 401 of the OAuth flow would never reach our code. The route is PUBLIC
  now, so the ExApp answers that 401 itself, and the protection was replaced in the same
  change rather than dropped: `exapp/middleware.py` reads the user id out of the AppAPI
  header, and an empty one has to pass a token verifier. While no verifier is configured
  (plan 03-06 builds it) every bearer is invalid, so the route stays closed by default.
* **Done in plan 03-01: the measurement probe is gone.** The three production documents of
  `oauth/metadata.py` replaced it, and `appinfo/info.xml` declares one fully anchored route
  per document instead of the broad `^/\.well-known/` prefix, which closes the accepted risk
  AR-02-06 of 02-SECURITY.md.
* **Unknown bearer token over HaRP (research Open Question 4).** Measured: a request to
  `/mcp` over HaRP with a bearer token Nextcloud does not know is answered **403**, a clean
  4xx, not a 5xx. HaRP turns the 4xx from `nc_get_user` into "no user" and the USER route
  then rejects with 403. This is the measurement the switch above rests on: with `/mcp` on
  PUBLIC that same 4xx lets HaRP forward the request to our own bearer check instead of
  turning into a 401. A 5xx would have become a 401 and broken it; it does not. The finding
  stands as measured, on the topology of phase 2.

## Limitations of this spike

The 401 with the `WWW-Authenticate` pointer comes from a purpose built probe route,
`/.well-known/mcp-discovery-probe`, not from `/mcp`. `/mcp` carries `access_level` USER in
phase 2, so HaRP answers there before our code does (403 in the matrix), and a realistic 401
out of `/mcp` is only possible once the route is PUBLIC in phase 3. The probe sits below
`/.well-known/`, which the single PUBLIC route in `appinfo/info.xml` already covers, so it
measures the proxy behaviour for a 401 and its header without opening `/mcp`. The probe is a
spike artifact: it is replaced, not extended, when phase 3 wires the real Protected Resource
Metadata, and its removal is one of the open items above.

That limitation is closed. Plan 03-01 removed the probe route with the module it lived in,
and the 401 with the `WWW-Authenticate` pointer now comes out of `/mcp` itself, where a
client meets it. The numbers in the matrix above stay as they were measured, on the phase 2
topology with `/mcp` still on `access_level` USER; `scripts/spike_discovery.sh` reads the
pointer off `/mcp` from now on, and the next measurement of the whole table happens against
the staging instance in plan 03-09.

## Related

- Discovery documents (the production path, plan 03-01): [../src/mcp_connector/oauth/metadata.py](../src/mcp_connector/oauth/metadata.py)
- The 401 with the pointer: [../src/mcp_connector/exapp/middleware.py](../src/mcp_connector/exapp/middleware.py)
- Reverse proxy rules for both canonical root paths: [../deploy/Caddyfile](../deploy/Caddyfile)
- Measurement script: [../scripts/spike_discovery.sh](../scripts/spike_discovery.sh)
- Manifest and routes: [../appinfo/info.xml](../appinfo/info.xml)
- Topology and install: [exapp-install.md](exapp-install.md)
- Requirement `AUTH-06`, decision `D-29`
