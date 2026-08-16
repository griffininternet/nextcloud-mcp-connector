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
[step 4] POST /register -> 201 | cache_control=no-store | client_id=cf25d0ac-030...
[step 5] GET /authorize -> 302
[step 5] GET /authorize/consent -> 200 | cache_control=no-store | signed_in=True
[step 5] POST /authorize/decide -> 400 | identity=none
[step 5] POST /authorize/decide -> 200 | identity=the session cookie of the sign in | code=present | state=matches | iss=http://127.0.0.1:8081/exapps/mcp_connector
[step 6] POST /token -> 200 | cache_control=no-store | fields=access_token,expires_in,refresh_token,scope,token_type | seconds=0.04
[step 7] POST /mcp -> 200 | tools=15 | transport=streamable-http
[step 7] tool notes_create -> 200 | note_id=note:354 | as_user=alice
```

The code exchange took **0.04 seconds**. A connector allows ten, and this path makes no
Nextcloud call at all, which is the reason.

**Every line above is from one run against the current code** (2026-08-16, Nextcloud
34.0.2, AppAPI HaRP `release`). Two of them are worth reading twice.

The decision is `POST /authorize/decide` and it appears **twice**, which is the CR-01 relay
walked over the full chain. The first one is sent by the caller that started the flow: it
holds the flow id and the anti forgery value derived from it, which used to be the entire
authorisation of this request, and it has no Nextcloud account. It is refused with `400`
and no code exists. The second is sent by the browser that just signed in, carrying nothing
but its Nextcloud session cookies, and that one is granted. The walker refuses to continue
if the first is granted.

The answer is `200` with a page that carries the return address as a link and as a
`meta refresh`, not a `302`: Chromium and WebKit check `form-action` against the target of
a redirect that follows a form submission, and every page here carries `form-action 'self'`,
so a redirect never arrived in those browsers (CR-03). The address, the code, the state and
the `iss` are what the line shows. The run is repeated against the staging instance in plan
03-09.

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
| Login flows one source may open per five minutes | **20** per path class, refused or not (CR-02) |

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
6 passed
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
[sc 3] GET /connect/wait -> 400 | identity=none | credential_handed_over=False
[sc 3] GET /connect/wait -> 200 | identity=the session cookie of the sign in | signed_in_as=alice | credential=72 characters, shown once
[sc 3] GET /connect/wait -> 400 | credential_shown_again=False
[sc 3] POST /mcp -> 200 | auth=the credential from the page | server=uvicorn
```

The first of the three loads is the CR-01 relay on this surface: the caller that started
the flow asks for its result, holding the flow id and no Nextcloud account. It gets 400 and
no credential, and the app password the finished sign in produced is handed back to
Nextcloud in the same request (D-34), which is why the successful half below needs a flow
of its own rather than a second try on that one.

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

### 9. The CR-01 counter check: what HaRP resolves, and what a refusal costs

The CR-01 fix rests on one assumption, and this section is that assumption measured rather
than argued: **does HaRP name the Nextcloud account of a request that carries nothing but a
browser session cookie, and does it do so on a route that is PUBLIC?**

Two oracles were used, both of them routes this app already serves. On the PUBLIC `/mcp`
route the middleware takes the AUTH-01 path when the AppAPI header names a user and demands
a bearer when it does not, so `200` means "identity resolved" and `401` means "no identity".
On `/authorize/decide` a `400` carrying this app's own error page means the request reached
the app, and anything else means the proxy answered instead.

| Credential of the request | `/mcp` (PUBLIC) | `/authorize/decide` |
|---|---|---|
| none | `401`, no identity | `400`, the app's own page |
| Basic, app password | `200`, identity resolved | `400`, the app's own page |
| Basic, account password | `200`, identity resolved | `400`, the app's own page |
| **Nextcloud session cookie** | **`200`, identity resolved** | **`400`, the app's own page** |
| session cookie plus `requesttoken` | `200`, identity resolved | `400`, the app's own page |

So the answer is yes, and it holds for a PUBLIC route: HaRP signs every request it forwards
with `AUTHORIZATION-APP-API` and writes the account it resolved into it, empty when the
caller sent no credential. A browser session is resolved exactly like an app password. The
whole relay was then walked against the running instance with three actors, and the
identity check is what separates them:

| Actor | `POST /authorize/decide` | `GET /connect/wait` |
|---|---|---|
| the caller that started the flow, no account | `400`, no code | `400`, no credential |
| `mallory`, a real session, the wrong account | `400`, no code | `400`, no credential |
| `alice`, the session that signed in | `200`, code issued | `200`, credential shown once |

**The access level this route must not carry.** The first shape of the CR-01 fix declared
`/authorize/decide` as `access_level` `USER`, which made HaRP refuse the anonymous case
itself with `403`. That is a denial of service of the whole app, and it was measured from a
cold HaRP:

```
attempt  1: anonymous POST /authorize/decide -> 403 | GET /.well-known/oauth-authorization-server -> 200 | POST /mcp -> 401
...
attempt  9: anonymous POST /authorize/decide -> 403 | GET /.well-known/oauth-authorization-server -> 200 | POST /mcp -> 401
attempt 10: anonymous POST /authorize/decide -> 403 | GET /.well-known/oauth-authorization-server -> 502 | POST /mcp -> 502
attempt 11: anonymous POST /authorize/decide -> 502 | GET /.well-known/oauth-authorization-server -> 502 | POST /mcp -> 502
```

HaRP records every refusal of a `USER` route in a blacklist of its own
(`HP_BLACKLIST_COUNT`, ten by default, inside `HP_BLACKLIST_WINDOW`, 300 seconds), and a
banned address is answered before the access level of the requested route is even looked
at. The tenth refusal therefore takes **every route of this app** away from that caller,
discovery documents and `/mcp` included, and it comes back 300 seconds after the last one
(measured: reachable again after five minutes, no restart needed). Refusals are this route's
normal traffic, not an anomaly: the relay attempt itself, a browser whose session expired
behind an open consent screen, a resubmitted form, and the negative probe
`scripts/oauth_flow_check.py` sends on every run. Two runs of the integration suite were
enough to lock the runner out, which is how this was found.

With the route PUBLIC, the same sequence stays inside this app's own throttle, which is
bounded per path class instead of per app:

```
attempt  1..10: anonymous POST /authorize/decide -> 400 | GET /.well-known/oauth-authorization-server -> 200
attempt 11..14: anonymous POST /authorize/decide -> 429 | GET /.well-known/oauth-authorization-server -> 200
```

Nothing is given up for that. HaRP resolves the account either way, and the comparison in
the app is the only check that can separate the two accounts anyway: the relay attacker of
CR-01 holds a valid Nextcloud account too, so the question is never whether the caller is
signed in, it is who they are signed in as.

**What an administrator takes from this.** If a route of an ExApp produces refusals as part
of its normal operation, it must not be declared `USER`. `HP_BLACKLIST_COUNT` and
`HP_BLACKLIST_WINDOW` are environment variables of the HaRP container and can be raised,
but that is the deploy daemon's configuration and not something this app may assume.

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

**Start the very first container with one worker.** The data key of this installation is
created on the first start and stored in Nextcloud's ExApp configuration, and that API has
no compare and set. Two workers that start at the same moment on an installation without a
key can both write one; the second write wins, and the worker that lost encrypts with a key
nobody can read again. Every later start reads the stored key and this cannot happen, so it
is one moment per installation. A loser is loud rather than silent: it logs "another worker
stored the data key first", and rows written with the lost key answer as unreadable instead
of decrypting into something wrong (WR-02).

**The persistent volume is not optional.** `APP_PERSISTENT_STORAGE` is where the store file
lives. Without a real volume every restart of the container loses every connection, and the
failure looks like a working installation until the first restart.

**The allowlist mode is a closed door, not a filter.** With
`NC_MCP_OAUTH_ALLOWLIST_ONLY` on and an empty list, nobody can authorize. That is the
intended reading and it is checked in four places, so a client that is blocked after its
token was issued stops working immediately rather than at the next expiry.

**A connection is granted by the account that signed in, and by nobody else.** The consent
screen is reachable with a flow id alone, because a browser that has not signed in yet has
nothing else, but the decision behind it is not. HaRP resolves the Nextcloud account of
every request it forwards and writes it into the AppAPI header, empty when the caller sent
no credential, and `POST /authorize/decide` compares it with the account whose sign in
produced the authorization; a mismatch, and an absent account, are refused without a code.
The same rule guards the one page that shows an app password in clear text,
`GET /connect/wait`: a credential that cannot be handed to the account that signed in is
handed back to Nextcloud instead of being shown. Without those two checks the flow id was
the whole authorisation, and whoever started a flow could finish a sign in somebody else
performed (CR-01, the Login Flow v2 relay). Both routes are PUBLIC and both refusals are
this app's own, deliberately so: see section 9 of the evidence above for what the `USER`
access level costs and why it buys nothing here.

**The throttle protects the authorization endpoints and never the MCP route.** Ten refused
attempts per source and path class in five minutes end in `429` with `Retry-After`, and a
success pays back one of them rather than clearing the window. Rate limiting the tool calls
themselves would be this server's own denial of service, so the measured number above is the
honest ceiling: an accepted MCP request is not throttled here and costs one Nextcloud round
trip.

**On the two routes that open a Nextcloud login flow, every request is counted, not only
the refused ones.** `POST /connect` and `/authorize` answer 200 and 302 when they work, and
each of those answers costs one Nextcloud round trip plus one login flow record that lives
for twenty minutes there. Counting refusals bounded nothing at all on exactly the path
success criterion 5 is about, so those two carry a path class and a limit of their own:
twenty per source per five minutes, counted before the work. The screens behind them, the
consent surface and the waiting page, keep the refusal counter, because a waiting screen
reloads itself every three seconds and is doing nothing wrong (CR-02).

**A revocation takes effect before the request returns.** The store, the process caches and
the Nextcloud app password are ended in that order, and the third step may fail without
holding up the first two. A user ends their own connection under Settings, Security,
Devices and sessions; a client ends it with `POST /revoke`. Both are immediate.

**The end of a decision is a page that navigates, not a redirect.** The consent decision is
a form submission, and Chromium and WebKit check `form-action` against the target of a
redirect that follows one. Under the policy every page of this flow carries,
`form-action 'self'`, a `302` to the client would be refused by those browsers and the user
would be left on a blank page. So the decision answers `200` with a page that carries the
return address twice, as a `meta refresh` that fires immediately and as a button the reader
can see and press. Nothing about the OAuth response changes: the same address, the same
code, the same `state` and the same `iss` (CR-03).

**Nothing of a token is written anywhere.** No log record, no error page and no answer of
this server carries a bearer, a code, a PKCE value or an app password. The one page that
shows a credential is the onboarding result page, once, with `no-store`.

## Related

- Installing the ExApp itself: [exapp-install.md](./exapp-install.md)
- What a user enters into a client: [client-setup.md](./client-setup.md)
- The throwaway instance the hosted connectors are measured against:
  [staging-setup.md](./staging-setup.md)
- Where the discovery paths were measured first: [spike-discovery.md](./spike-discovery.md)
- Requirements `AUTH-02` (browser onboarding), `AUTH-03` (OAuth 2.1 to the MCP
  authorization specification) and `AUTH-07` (the three administrator switches)
