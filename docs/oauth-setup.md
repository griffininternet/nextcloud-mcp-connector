# OAuth 2.1 setup

**Status:** proven on a local HaRP topology
**Measured on:** 2026-08-16
**Scope:** turning on the OAuth 2.1 half of this app, so that an assistant such as Claude.ai
or ChatGPT connects through a browser sign in instead of a pasted app password. The
credential based ways stay as they are and are described in
[client-setup.md](./client-setup.md).

Everything in the Evidence section was executed against **Nextcloud 34.0.2** with
**AppAPI 34.0.0** and `ghcr.io/nextcloud/nextcloud-appapi-harp:release`, on the topology of
[exapp-install.md](./exapp-install.md). The outputs are copied verbatim from that run.

## Topology

An OAuth connection touches four components, and each of them answers a different part of
the flow. This is the way of one request, from the assistant to Nextcloud and back:

| Step | Who answers | What happens |
|------|-------------|--------------|
| 1. The first tool call | the ExApp | No token, so the MCP route answers `401` with `WWW-Authenticate` and a `resource_metadata` pointer. That answer is the whole discovery: everything after it is built from it. |
| 2. The protected resource document | the ExApp | `GET <public url>/.well-known/oauth-protected-resource/mcp`. It names the resource and the authorization server. |
| 3. The authorization server document | the ExApp | Three paths lead there, and only one of them works everywhere. See "The three discovery paths" below. |
| 4. Registration | the ExApp | `POST <public url>/register`. Claude.ai and ChatGPT register themselves; there is no client id an administrator has to create. |
| 5. The authorization request | the ExApp, then Nextcloud | `GET <public url>/authorize` opens a Nextcloud Login Flow v2 and sends the browser to the consent screen of this app. The user signs in **on Nextcloud's own pages**, second factor included. This app never sees a password. |
| 6. The consent screen | the ExApp | Who is asking, what they get, and two buttons. Approving produces a single use authorization code and sends the browser back to the client. |
| 7. The code exchange | the ExApp | `POST <public url>/token`. No Nextcloud call happens on this path, which is why it answers in milliseconds. |
| 8. Every later tool call | the ExApp, then Nextcloud | The bearer is checked against this app's own store, and the tool call runs against Nextcloud as the user who signed in. |
| 9. Ending the connection | the ExApp, then Nextcloud | `POST <public url>/revoke`, or the user removes the entry under Settings, Security, Devices and sessions. |

Two components sit in front of all of this and are not optional. The reverse proxy of the
installation routes `/exapps/*` to HaRP, and HaRP strips the `/exapps/mcp_connector` prefix
before the container sees a request. Both matter for the discovery paths below.

### The three discovery paths

A client that has read the protected resource document has to find the authorization server
document. There is no pointer for that step, only three constructed paths, and a client
tries them in this order:

| # | Path | Who owns it | Answers |
|---|------|-------------|---------|
| 1 | `<nextcloud>/.well-known/oauth-authorization-server/exapps/mcp_connector` | Nextcloud | `404`, unless a reverse proxy rule maps it back (Install, below) |
| 2 | `<nextcloud>/.well-known/openid-configuration/exapps/mcp_connector` | Nextcloud | `404`. There is no rule for this one, because a client that tries it also tries path 3. |
| 3 | `<nextcloud>/exapps/mcp_connector/.well-known/openid-configuration` | this app | `200`, always, with no administrator action |

Path 3 survives a stripped prefix, which is why it is the one that works out of the box.
Paths 1 and 2 land on the domain root, where Nextcloud's own well-known controller matches
a single path segment only. The two rules in the Install section exist for clients that try
the canonical path and stop.

## Install

### 1. The public URL, and it is not optional

`NC_MCP_PUBLIC_URL` is the address this app is reachable under from the outside, without a
trailing slash:

```
https://cloud.example.com/exapps/mcp_connector
```

The authorization server calls itself by this value. It is the `issuer` of the metadata
document, the `resource` of the protected resource document and the target of the
`resource_metadata` pointer in every `401`. Left unset, all three name the documented
default `http://127.0.0.1:8765`, no client can reach it, and the connection fails at the
first step with "could not discover authorization server".

The deploy daemon injects a variable into the ExApp container only if the manifest declares
it. `appinfo/info.xml` declares this one and the three switches below; an installation sets
the value at registration time:

```
occ app_api:app:register mcp_connector \
  --env "NC_MCP_PUBLIC_URL=https://cloud.example.com/exapps/mcp_connector"
```

For the local topology of `scripts/bootstrap_exapp.sh` the value is set automatically and
can be overridden with `NC_EXAPP_PUBLIC_URL`.

### 2. The three switches of AUTH-07

All three are optional, and the shipped state is the plug and play one:

| Variable | Default | What it does |
|----------|---------|--------------|
| `NC_MCP_OAUTH_DCR` | on | Dynamic client registration (RFC 7591). Claude.ai and ChatGPT need it to connect without an administrator. Switched off, `/register` refuses and the discovery document stops advertising the endpoint. |
| `NC_MCP_OAUTH_ALLOWLIST_ONLY` | off | Only clients named below may authorize. **An empty list with this switch on closes the door for everyone**, which is deliberate: an administrator who armed the switch and named nobody meant to close it. |
| `NC_MCP_OAUTH_ALLOWED_CLIENTS` | empty | Comma separated client ids **or redirect URIs**. Only read when the allowlist is on. A redirect URI is the entry an administrator can write down in advance, because a self registered client's id is random. |

A value that is neither on nor off keeps the default and says so in the log, instead of
guessing.

### 3. The two reverse proxy rules for the canonical root paths

These are **optional**. A specification compliant client reads the `resource_metadata`
pointer out of the `401` and finds everything from there; path 3 of the discovery table
needs no rule at all. Add them if a client reports that it cannot find the authorization
server, and add them before a first public launch, because they cost nothing and remove a
whole class of support requests.

Caddy:

```caddyfile
route /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp {
	rewrite * /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
	reverse_proxy appapi-harp:8780
}

route /.well-known/oauth-authorization-server/exapps/mcp_connector {
	rewrite * /exapps/mcp_connector/.well-known/oauth-authorization-server
	reverse_proxy appapi-harp:8780
}
```

nginx:

```nginx
location = /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp {
    proxy_pass http://harp:8780/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp;
    proxy_read_timeout 1800s;
}

location = /.well-known/oauth-authorization-server/exapps/mcp_connector {
    proxy_pass http://harp:8780/exapps/mcp_connector/.well-known/oauth-authorization-server;
    proxy_read_timeout 1800s;
}
```

Both use an exact match, `route /path` in Caddy and `location =` in nginx, so they rewrite
these two strings and nothing else. No Nextcloud path outside them changes behaviour, and
both rules have to stand before the general `/exapps/*` rule, because the first match wins.

### 4. What the user enters

The URL of the connector, exactly, with `/mcp` and without a trailing slash:

```
https://cloud.example.com/exapps/mcp_connector/mcp
```

That string has to match the `resource` of the protected resource document character for
character. A trailing slash is a different resource and the connection fails before the
first tool call.

## Evidence

All commands were run on **2026-08-16** against Nextcloud 34.0.2 and AppAPI 34.0.0. The
runnable form of the whole table is:

```
set -a && . ./.env.exapp && set +a
uv run --no-sync python scripts/oauth_flow_check.py \
    http://127.0.0.1:8081/exapps/mcp_connector --measure
```

### 1. The flow, step by step

```
[step 1] POST /mcp -> 401 | cache_control=no-store | www_authenticate=Bearer error="invalid_token", error_description="Authentication required", scope="nextcloud", resource_metadata="http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"
[step 2] GET harp:/.well-known/oauth-protected-resource/mcp -> 200 | content_type=application/json | cache_control=no-store
[step 2] GET harp:/.well-known/openid-configuration -> 200 | content_type=application/json | cache_control=no-store
[step 2] GET harp:/.well-known/oauth-authorization-server -> 200 | content_type=application/json | cache_control=no-store
[step 2] GET php-proxy:/.well-known/oauth-protected-resource/mcp -> 200 | content_type=application/json | cache_control=no-store
[step 2] GET php-proxy:/.well-known/openid-configuration -> 200 | content_type=application/json | cache_control=no-store
[step 2] GET php-proxy:/.well-known/oauth-authorization-server -> 200 | content_type=application/json | cache_control=no-store
[step 2] both proxy paths serve all three documents byte for byte the same
[step 3] GET root:/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp -> 200 | content_type=application/json | rewrite=active
[step 3] GET root:/.well-known/oauth-authorization-server/exapps/mcp_connector -> 200 | content_type=application/json | rewrite=active
[step 4] POST /register -> 201 | cache_control=no-store | client_id=c98a2e57-314...
[step 5] GET /authorize -> 302
[step 5] GET /authorize/consent -> 200 | cache_control=no-store | signed_in=True
[step 5] POST /authorize/consent -> 302 | code=present | state=matches | iss=http://127.0.0.1:8081/exapps/mcp_connector
[step 6] POST /token -> 200 | cache_control=no-store | fields=access_token,expires_in,refresh_token,scope,token_type | seconds=0.04
[step 7] POST /mcp -> 200 | tools=15 | transport=streamable-http
[step 7] tool notes_create -> 200 | note_id=note:275 | as_user=alice
```

The code exchange took **0.04 seconds**. A connector allows ten, and this path makes no
Nextcloud call at all, which is the reason.

**One line of this run is older than the code it describes.** The decision was a `POST` on
`/authorize/consent` when this was measured. It is `POST /authorize/decide` since CR-01, it
is the one route of the app with `access_level` `USER`, and the walker now sends it twice:
once without a Nextcloud account, which has to be refused, and once with the account that
signed in, which is the redirect above. The numbers of every other step are unaffected; the
run is repeated against the staging instance in plan 03-09.

### 2. The canonical root paths, with and without the two rules

The rules of the Install section were removed from the running reverse proxy and put back:

```
docker exec nc-mcp-exapp-caddy caddy reload --config /tmp/Caddyfile.norewrite --adapter caddyfile

/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp        status=404
/.well-known/oauth-authorization-server/exapps/mcp_connector          status=404
/.well-known/openid-configuration/exapps/mcp_connector                status=404
/exapps/mcp_connector/.well-known/openid-configuration                status=200
/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp        status=200

docker exec nc-mcp-exapp-caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp        status=200
/.well-known/oauth-authorization-server/exapps/mcp_connector          status=200
```

Without the rules the two canonical root paths are answered by Nextcloud with 404, exactly
as the third discovery path predicted, and the path appended variant keeps working either
way. That is what makes the rules an improvement rather than a requirement.

### 3. Success Criterion 5: the number of Nextcloud round trips

```
[sc 5] 5 accepted MCP calls -> 6 Nextcloud requests (1.2 per call): ['GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector']
[sc 5] 5 refused MCP calls -> 5 Nextcloud requests (1.0 per call): ['GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector']
[sc 5] POST /token -> 429 | attempts=11 | retry_after=300
[sc 5] GET /ocs/v2.php/cloud/user -> 200 | as_user=alice
```

Three numbers, and they are the ones that multiply with the number of users:

| Measurement | Result |
|-------------|--------|
| Nextcloud requests per accepted MCP request | **1** (six HTTP requests, one session `initialize` plus five `tools/list`, produced six lookups) |
| Nextcloud requests per refused MCP request | **1** |
| Refused token requests before the throttle answers 429 | **11**, with `Retry-After: 300` |

**Every request that carries an `Authorization` header costs exactly one Nextcloud round
trip, and this application cannot switch it off.** HaRP resolves a user for any request
with that header, and its session cache only covers cookies, so an OAuth bearer is looked
up on every single call. The verification of the token itself costs nothing: it is one
indexed lookup in this app's own store, answered from a five second process cache.

The counter check the research asks for holds: after eleven refused token requests and five
MCP requests with bearers this server never issued, the test user signs in normally
(`GET /ocs/v2.php/cloud/user -> 200`). An unknown bearer produces no brute force entry in
Nextcloud, so nobody is locked out by a flood.

### 4. A restart is not a disconnection

```
uv run --no-sync pytest -m integration tests/integration/test_oauth_flow_exapp.py -q
5 passed
```

`test_the_same_token_still_works_after_the_container_restarted` restarts
`nc_app_mcp_connector` with `docker restart`, waits until the app answers again and calls
the same tool with the same token. Three things have to survive for it to pass: the store
file on the persistent volume, the data key in Nextcloud's ExApp configuration, and the
ability to read that key back from a cold process.

### 5. Two accounts stay two accounts

`test_two_tokens_stay_two_accounts_over_the_whole_chain` builds one connection for each of
two users, writes a file as the first one and then asks the second one for it four ways:
`files_search`, `unified_search`, and `files_read` with the exact path. All three answer
empty or refuse, and the refusal carries no content of the file. The positive control runs
in the same test: the owner finds her own file at the same moment, so an empty answer
cannot be an empty instance.

### 6. Revocation, and what it removes

```
new Devices-and-sessions entries after the connection: [108]
revoke -> 200
still there after the revocation: []
removed by the revocation: [108]
```

Read with `occ user:auth-tokens:list alice`, which is the command line form of Settings,
Security, Devices and sessions. The Nextcloud app password behind the connection is really
handed back, not only marked as gone in this app's store.
`test_a_revocation_is_a_401_with_the_same_pointer_and_a_reconnection_works` adds the other
half: immediately after the revocation the next tool call is a `401` whose
`WWW-Authenticate` is byte for byte the one an anonymous request gets, and a complete new
connection can be built right away.

### 7. Success Criterion 3: the onboarding without OAuth

```
[sc 3] GET /connect -> 200 | cache_control=no-store
[sc 3] POST /connect -> 200
[sc 3] GET /connect/wait -> 200 | signed_in_as=alice | credential=72 characters, shown once
[sc 3] GET /connect/wait -> 400 | credential_shown_again=False
[sc 3] POST /mcp -> 200 | auth=the credential from the page | server=uvicorn
```

The credential is shown exactly once: the second load of the same address answers 400 and
carries no credential, because the flow record is deleted the moment the result is
rendered. The credential works immediately as a Basic header against `/mcp`, and
`Server: uvicorn` is the proof that the answer came out of the ExApp container rather than
from the proxy in front of it.

The entry it creates carries the expected name prefix:

```
docker exec -u www-data nc-mcp-exapp-nc php occ user:auth-tokens:list alice
| 98  | MCP Connector: browser onboarding | 2026-08-16T04:08:10+00:00 | permanent | filesystem |
| 102 | MCP Connector: browser onboarding | 2026-08-16T04:09:07+00:00 | permanent | filesystem |
```

An OAuth connection appears in the same list under the name the client registered itself
with, prefixed the same way, for example `MCP Connector: OAuth flow check`.

### 8. The sign ins nobody finished are cleaned up

A sign in that Nextcloud completed but that nobody ever approved leaves a working app
password behind. This app has no cron, so the cleanup hangs on the authorization request:
each one hands back at most three of those credentials. Measured by waiting out the twenty
minute deadline and then driving ten authorization requests:

```
MCP Connector entries before the sweep: 25
MCP Connector entries after ten authorization requests: 24
handed back by the sweep: [104]
```

Entry 104 was the credential of a sign in that never became a connection. Nothing else in
that list was touched: a running sign in and a live connection are both left alone by
definition, which is why only one entry moved.

## Known pitfalls

The six things that made this phase expensive, in the words of somebody who runs the
instance.

**1. The canonical root path belongs to Nextcloud, not to this app.** Two of the three
discovery paths sit on the domain root and are answered there with 404. Only the path
appended variant lives below the app's own prefix. If a client reports "could not discover
authorization server" although `/mcp` answers a proper 401, add the two reverse proxy rules.

**2. The authorization server document has no pointer.** The protected resource document is
found through a header; the authorization server document is found by guessing three paths.
There is nothing to configure that would make a client look somewhere else, which is why
the issuer in the document has to be exactly the value the URL was built from.

**3. The PHP proxy caches JSON.** A JSON answer without a `Cache-Control` header is cached
for an hour by AppAPI's PHP proxy. Every answer of the authorization server therefore
carries `no-store`, set by a wrapper over all of its routes rather than per handler. If you
put a cache in front of this app, exclude these routes.

**4. HaRP asks Nextcloud on every request with an `Authorization` header.** One MCP call is
one Nextcloud PHP request, measured above. Its session cache only covers cookies, so an
OAuth bearer never hits it. Plan for it in sizing; there is no setting that removes it.

**5. The Login Flow v2 answers its poll exactly once.** The moment Nextcloud says the sign
in is done, the credential exists and the record is gone. This app therefore stores the
authorization at that moment, before anybody has consented, and hands the credential back
when the user denies or never finishes. If you see an app password of this connector for a
connection that does not exist, it is either younger than twenty minutes or a failed
cleanup, and the app remembers the second case.

**6. Clients with a loopback redirect and a changing port do not fit.** Claude Code
identifies itself with a client id metadata document instead of registering, and its
callback port changes per run, which exact redirect URI matching cannot accept. That is a
deliberate limit of v1, not a bug. Those clients use the app password way of
[client-setup.md](./client-setup.md).

## Security notes for production

**The data key lives in Nextcloud, and the store lives in the volume.** Every app password
this app keeps is encrypted with AES-GCM, bound to the row it is stored in, with a key that
sits in Nextcloud's own ExApp configuration and is marked as sensitive. Two consequences an
operator has to know: a backup of the volume without the Nextcloud database is useless, and
replacing that configuration value by hand makes every stored authorization unreadable, so
every connected assistant has to connect again.

**The persistent volume is not optional.** `APP_PERSISTENT_STORAGE` is where the store file
lives. Without a real volume every restart of the container loses every connection, and the
failure looks like a working installation until the first restart.

**The allowlist mode is a closed door, not a filter.** With
`NC_MCP_OAUTH_ALLOWLIST_ONLY` on and an empty list, nobody can authorize. That is the
intended reading and it is checked in four places, so a client that is blocked after its
token was issued stops working immediately rather than at the next expiry.

**A connection is granted by the account that signed in, and by nobody else.** The consent
screen is reachable with a flow id alone, because a browser that has not signed in yet has
nothing else, but the decision behind it is not. `POST /authorize/decide` is declared
`USER`, so HaRP resolves the Nextcloud account of that request, and the app compares it
with the account whose sign in produced the authorization; a mismatch, and an absent
account, are refused without a code. The same rule guards the one page that shows an app
password in clear text, `GET /connect/wait`: a credential that cannot be handed to the
account that signed in is handed back to Nextcloud instead of being shown. Without those
two checks the flow id was the whole authorisation, and whoever started a flow could finish
a sign in somebody else performed (CR-01, the Login Flow v2 relay).

**The throttle protects the authorization endpoints and never the MCP route.** Ten refused
attempts per source and path class in five minutes end in `429` with `Retry-After`. Rate
limiting the tool calls themselves would be this server's own denial of service, so the
measured number above is the honest ceiling: an accepted MCP request is not throttled here
and costs one Nextcloud round trip.

**A revocation takes effect before the request returns.** The store, the process caches and
the Nextcloud app password are ended in that order, and the third step may fail without
holding up the first two. A user ends their own connection under Settings, Security,
Devices and sessions; a client ends it with `POST /revoke`. Both are immediate.

**Nothing of a token is written anywhere.** No log record, no error page and no answer of
this server carries a bearer, a code, a PKCE value or an app password. The one page that
shows a credential is the onboarding result page, once, with `no-store`.

## Related

- Installing the ExApp itself: [exapp-install.md](./exapp-install.md)
- What a user enters into a client: [client-setup.md](./client-setup.md)
- Where the discovery paths were measured first: [spike-discovery.md](./spike-discovery.md)
- Requirements `AUTH-02` (browser onboarding), `AUTH-03` (OAuth 2.1 to the MCP
  authorization specification) and `AUTH-07` (the three administrator switches)
