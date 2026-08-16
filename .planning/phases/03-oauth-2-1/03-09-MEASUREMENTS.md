# Plan 03-09: raw measurements from the hosted connector runs

Working notes taken during the live runs on 2026-08-16. The SUMMARY and the
documentation changes are written from this file; it is kept so the numbers stay
attributable after the fact.

Instance: https://nc-staging.infranode.dev
Nextcloud 34.0.2, AppAPI 34.0.0, ExApp 0.1.0, image built from main at 162d6f0.
Throwaway machine, Hetzner CX23 Nuernberg, 178.104.71.131, created 2026-08-16.

---

## Run 1: Claude.ai, 2026-08-16, RESULT: CONNECTED

Plan and account: personal Claude account, Chrome on Windows. The connector was
added with the URL alone, both OAuth fields left empty.

### Where the button is (for docs/client-setup.md)

Connectors moved out of Settings into "Customize". Two ways to the custom
connector dialog:

1. Customize, Connectors, "Add", "Add custom connector"
2. In the composer: the attachment menu, "Add connector"

Form fields: Name, "Remote MCP Server URL", OAuth Client ID (optional), OAuth
Client Secret (optional). Both OAuth fields stay empty, DCR does the rest.

### Blocker on organisation accounts

An account whose role is "user" inside a Team or Enterprise organisation does not
get the button at all; only owners may add custom connectors there. Measured with
a work account (role "user"): no button. Same browser, personal account: button
present. Source: support.claude.com/en/articles/11175166-about-custom-connectors-remote-mcp

### Request chain, from the access log

```
POST 401  /exapps/mcp_connector/mcp
GET  200  /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
GET  200  /.well-known/oauth-authorization-server/exapps/mcp_connector
POST 201  /exapps/mcp_connector/register
POST 200  /index.php/login/v2
GET  302  /exapps/mcp_connector/authorize?response_type=code&client_id=...
GET  200  /exapps/mcp_connector/authorize/consent?flow=...
POST 200  /login/v2/grant     (Nextcloud, access granted)
POST 200  /login/v2/poll      (exactly one poll)
POST 200  /exapps/mcp_connector/authorize/decide
POST 200  /exapps/mcp_connector/token
POST 200  /exapps/mcp_connector/mcp   (repeatedly: tools/list and follow ups)
```

### Assumption A2, answered

For the protected resource document Claude.ai follows the `resource_metadata`
pointer out of our 401, so it reads our own path under /exapps/. For the
authorization server metadata it uses the canonical path at the domain root,
`/.well-known/oauth-authorization-server/exapps/mcp_connector`, which exists only
because of the rewrite rule in deploy/Caddyfile.staging.

**Reading at the time:** the two rewrite rules looked required rather than
optional. The counter measurement below shows that this reading was wrong: with
the rules gone Claude.ai falls back to a third path and still connects. What run
1 measured is only which path Claude.ai *prefers* when both exist.

### Redirect URI

`https://claude.ai/api/mcp/auth_callback`, static.
Client id issued by our DCR: 67592959-8308-4ab4-bc66-a4af273eeb62.
Client name sent by Claude.ai: "Claude".

### CR-03 confirmed in a real browser

The consent decision is a POST to /authorize/decide that answers 200 with the
return page instead of a 302 to a foreign origin. Chrome returned to claude.ai
(`?step=success`). The strict CSP with `form-action 'self'` blocks nothing. This
was the one open browser check left by the code review.

### What the user sees

Nextcloud shows its own sign in page with its own security warning and names the
client as "MCP Connector: Claude". Our page in front of it says "This page never
asks for your password", the footer says "The password prompt is always Nextcloud
itself". The consent screen shows the "Unverified client" callout because the
client registered itself, and lists app name, redirect target and client id.

The connection appears in alice's Nextcloud sessions as "MCP Connector: Claude"
(`occ user:auth-tokens:list alice`, permanent, scope filesystem) and can be ended
there.

### Tools in the client

15 tools, grouped by Claude.ai itself: 11 read only (calendar_list_events,
contacts_search, deck_browse, fetch, files_list, files_read, files_search,
notes_read, notes_search, search, unified_search) and 4 write
(calendar_create_event, deck_create_card, files_upload, notes_create). Both
groups are set to ask for approval.

---

## Run 2: ChatGPT, 2026-08-16, RESULT: FAILED, fixed, then CONNECTED

Plan and account: personal ChatGPT account on the free plan.

### Where the button is

Custom MCP servers need developer mode: Settings, Security and sign in,
"Developer mode" (carries an "increased risk" badge). Only then does the plugins
page show a "Create app" button, which opens the connector form: Name,
Description, Server URL, Authentication (OAuth is the default), plus a mandatory
"I understand and want to continue" checkbox.

### Request chain, from the access log

```
POST 401  /exapps/mcp_connector/mcp
GET  200  /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
GET  200  /.well-known/oauth-authorization-server/exapps/mcp_connector
GET  200  /exapps/mcp_connector/.well-known/openid-configuration
(the three documents are read twice)
POST 201  /exapps/mcp_connector/register
GET  302  /exapps/mcp_connector/authorize?...  -> error=invalid_scope
```

### The bug this run found

The authorize request carried:

```
client_id              4c674ffa-e27c-4018-8d16-8c4b6092172a
redirect_uri           https://chatgpt.com/connector/oauth/GxdvJstdJeOS
scope                  offline_access nextcloud
resource               https://nc-staging.infranode.dev/exapps/mcp_connector/mcp
code_challenge_method  S256
response_type          code
```

and was refused with
`error=invalid_scope, error_description=Client was not registered with scope offline_access`.

Cause: our metadata advertises `scopes_supported: ["nextcloud", "offline_access"]`
and `grant_types_supported: ["authorization_code", "refresh_token"]`, but the
client registered through DCR only carries the scope `nextcloud`. A client that
reads the metadata and asks for what it advertises is refused by our own server.
Claude.ai never asked for `offline_access`, which is why run 1 passed.

### Assumption A1, answered

The ChatGPT redirect URI is **not static**. It is issued per connector and has the
shape `https://chatgpt.com/connector/oauth/<token>`; in this run
`https://chatgpt.com/connector/oauth/GxdvJstdJeOS`. This replaces the [ASSUMED]
value taken from community sources in 03-RESEARCH.md.

Also confirmed: ChatGPT sends the `resource` parameter of RFC 8707 correctly, uses
PKCE with S256, and additionally fetches `/.well-known/openid-configuration`,
which Claude.ai does not.

### Status: fixed and re-run, CONNECTED

Fix commits 5793fc3, eb5b6b9, 8724d57. After rebuilding the image on the staging
machine the same connector was told to connect again, without deleting it, and
the run completed:

```
GET  302  /exapps/mcp_connector/authorize?...      (no error this time)
GET  200  /exapps/mcp_connector/authorize/consent?...
POST 200  /exapps/mcp_connector/authorize/decide
POST 200  /exapps/mcp_connector/token
POST 200  /exapps/mcp_connector/mcp                (repeatedly)
```

Redirect back to `https://chatgpt.com/connector/oauth/GxdvJstdJeOS?code=...&state=...&iss=...`,
the `iss` parameter carried our issuer. ChatGPT now shows "connected on 16 Aug 2026",
authorization method OAuth. Nextcloud names the client "MCP Connector: ChatGPT" on
its own sign in page, the same passthrough as for Claude.

Verified against the live instance after the rebuild:
```
registered scope: nextcloud offline_access
authorize with scope=offline_access nextcloud -> 302 to the consent page, no error
```

### Deployment note learned here

Rebuilding the image alone does not reach the running container: the image tag is
the app version and does not change, so AppAPI keeps the old container. Disabling
and enabling the app is not enough either, and removing the container by hand left
the registration in a state where `app_api:app:enable` failed. What worked:
`occ app_api:app:unregister mcp_connector --silent --force` followed by
`scripts/bootstrap_exapp.sh --staging`. Note that the bootstrap needs the generated
secrets, so source `.env.staging` first. Unregistering drops the ExApp volume, so
the token store is emptied and existing client connections have to be made again.

---

## Run 3: the counter measurement for A2, 2026-08-16, RESULT: CONNECTS WITHOUT THE REWRITES

Both rewrite blocks in `deploy/Caddyfile.staging` were commented out, Caddy was
restarted, and Claude.ai was made to run the whole flow again from nothing.

### How to switch the rules off, and the trap in doing it

`deploy/Caddyfile.staging` is bind mounted as a **single file** into the Caddy
container. `sed -i` writes a new inode, so the container keeps reading the old
one: the file on the host changes, the running proxy does not, and `caddy reload`
happily reloads the unchanged file. The first attempt measured 200 on both
canonical paths for exactly that reason and looked like a sensational finding.
Two ways out: write in place without replacing the inode (`… > /tmp/x && cat
/tmp/x > deploy/Caddyfile.staging`) and restart the container so the mount is
resolved again, or edit through the container. The check that the edit arrived is
`docker exec nc-mcp-staging-caddy grep -c COUNTERMEASURE /etc/caddy/Caddyfile`.

With the rules really gone:

```
404  /.well-known/oauth-authorization-server/exapps/mcp_connector
404  /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp
200  /exapps/mcp_connector/.well-known/oauth-authorization-server
200  /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
```

`scripts/oauth_flow_check.py` walked the full flow in this state and passed; only
its step 3 flipped to `rewrite=absent`. The rest of the chain does not touch the
canonical paths at all.

### Making Claude.ai start over, and a finding that came out of it

Removing the connector in the Claude.ai UI does **not** end the authorization. The
connector was removed, then added again under a new name with the same server URL,
and Claude.ai reused its stored connection: the very first request was a tool call
that answered 200, no 401, no discovery, no registration. The entry even kept its
old id (`0b092552-…`). So the UI "Remove" is a local bookkeeping action; what ends
access is a revoke on the Nextcloud side. This belongs in docs/client-setup.md and
is worth one line in the consent copy review: a user who removes a connector in
the client has not revoked anything.

To force a real start over, the OAuth store of the ExApp was emptied
(`clients`, `authorizations`, `auth_codes`, `flows`, `access_tokens`,
`refresh_tokens` in `/nc_app_mcp_connector_data/oauth.sqlite3`), after which
`POST /mcp` answered 401 again.

### The request chain without the rewrites

```
POST 401  /exapps/mcp_connector/mcp
GET  200  /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
GET  404  /.well-known/oauth-authorization-server/exapps/mcp_connector
GET  404  /.well-known/openid-configuration/exapps/mcp_connector
GET  200  /exapps/mcp_connector/.well-known/openid-configuration   <- the fallback
POST 201  /exapps/mcp_connector/register
POST 200  /index.php/login/v2        (client name "MCP Connector: Claude")
POST 200  /login/v2/poll
POST 200  /exapps/mcp_connector/token
POST 200  /exapps/mcp_connector/mcp  (repeatedly)
```

Claude.ai returned to `claude.ai/customize/connectors?…&step=success` and the
connector is connected. The client id issued this time was
`4572d09d-df53-41dc-9c51-0671d71dfa79`, the redirect target was again the static
`https://claude.ai/api/mcp/auth_callback`.

### What A2 actually says now

Claude.ai tries three locations for the authorization server metadata, in order:
the RFC 8414 canonical path at the domain root, the same path with
`openid-configuration`, and finally the OIDC style suffix below the issuer,
`<issuer>/.well-known/openid-configuration`. The third one is ours and needs no
proxy rule at all.

**Consequence for the documentation:** the two rewrite rules stay **optional**,
which is what deploy/Caddyfile and docs/spike-discovery.md already say. They are
worth keeping as a courtesy for clients that stop after the canonical path, and
the sentence that names them optional should now cite this measurement instead of
leaving the question open. The finding of the spike, that the canonical path is
404 without a proxy rule, is confirmed: it is the client that has a fallback, not
the server that serves the path.

After the measurement both rules were put back and the container restarted; the
canonical paths answer 200 again.

## Still open

- Cursor: not required by phase 3, but it is the only client class with a loopback
  redirect (`http://127.0.0.1:<port>`), the class that BACKLOG BL-04 defers. The
  staging instance is the cheap moment to learn whether exact redirect matching
  locks out local clients as a whole.
