# Client setup

Three ways to connect an assistant to your Nextcloud with this server:

| Transport | Who it is for | Credentials |
|-----------|---------------|-------------|
| **stdio** | One person, one machine. Claude Desktop, Claude Code, Cursor and every other client that starts a local process. | App password from the environment |
| **Streamable HTTP** | A shared or remote deployment. One process can serve several people. | App password per request, in the `Authorization` header |
| **ExApp (AppAPI)** | An administrator installs the server into Nextcloud itself, and every user connects with their own identity. | App password per request; HaRP resolves it to the user (OAuth in phase 3) |

All three speak the same 15 tools. The only difference is where the credentials come from and
where the identity is resolved.

The stdio and Streamable HTTP transports were verified in phase 1; the ExApp mode was added in
phase 2 and has its own installation guide in [exapp-install.md](exapp-install.md). The full
client matrix (ChatGPT, Cursor, Open WebUI, MUCGPT) follows in a later phase.

## Before you start: get an app password

Never use your login password. In Nextcloud, open **Settings, Security, Devices and
sessions**, enter a name such as `mcp`, and press **Create new app password**. Nextcloud
shows the value once. It looks like `xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`.

An app password can be revoked on that same page without touching your account, and it is
the only credential this server ever accepts. Two factor authentication stays intact,
because an app password bypasses the second factor by design and only for this one token.

## stdio

### Install

```bash
uv tool install nextcloud-mcp-connector
```

This puts the `nc-mcp` command on your PATH. Check it before you configure any client:

```bash
export NC_MCP_URL=https://cloud.example.com
export NC_MCP_USER=alice
export NC_MCP_APP_PASSWORD=xxxxx-xxxxx-xxxxx-xxxxx-xxxxx

nc-mcp
```

A working server prints nothing and waits on stdin. That silence is correct: stdio is a
pipe protocol, not a console application. Press Ctrl+C to stop it. If the command exits
immediately with an error instead, the message names the variable that is missing or the
URL that could not be reached.

### Claude Desktop

Edit `claude_desktop_config.json`:

* macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
* Windows: `%APPDATA%\Claude\claude_desktop_config.json`
* Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nextcloud": {
      "command": "nc-mcp",
      "env": {
        "NC_MCP_URL": "https://cloud.example.com",
        "NC_MCP_USER": "alice",
        "NC_MCP_APP_PASSWORD": "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"
      }
    }
  }
}
```

Restart Claude Desktop completely, not just the window. The 15 tools then appear in the
tools menu of a new conversation.

If `nc-mcp` is not found, the desktop app does not see your shell PATH. Use the absolute
path instead, for example `"command": "/home/alice/.local/bin/nc-mcp"`, or point at the
checkout with `"command": "uv"` and
`"args": ["run", "--directory", "/path/to/nextcloud-mcp-connector", "nc-mcp"]`.

### Claude Code

```bash
claude mcp add nextcloud \
  --env NC_MCP_URL=https://cloud.example.com \
  --env NC_MCP_USER=alice \
  --env NC_MCP_APP_PASSWORD=xxxxx-xxxxx-xxxxx-xxxxx-xxxxx \
  -- nc-mcp
```

Verify with `claude mcp list`. The entry has to say `connected`.

### What stdio does not do

stdio has no request headers, so it has no place to put an `Authorization` value. The
security boundary of this mode is the process that starts the server: whoever can start
`nc-mcp` can use the credentials in its environment. That is the right model for your own
laptop and the wrong one for a shared machine. Use HTTP there.

## Streamable HTTP

### Start the server

```bash
export NC_MCP_URL=https://cloud.example.com
export NC_MCP_ALLOWED_HOSTS=mcp.example.com
uv run uvicorn mcp_connector.entry_http:app --host 127.0.0.1 --port 8765
```

The MCP endpoint is `POST /mcp`. `GET /health` answers `{"status":"ok","version":"..."}`
without authentication and without the host check, which is what a reverse proxy or a
container health check should poll. It is a liveness probe and nothing else: a 200 there
does not mean a client can connect, see the 421 section below.

Note what is missing from that block: no `NC_MCP_USER` and no `NC_MCP_APP_PASSWORD`. In
this mode the server holds no Nextcloud account of its own. The target Nextcloud, however,
always comes from `NC_MCP_URL` and never from the request, because a client that could
choose the target could point this server and its credentials at a host of its choosing.

### Credentials per request (Basic passthrough)

Every request carries the user's own app password in an ordinary Basic header:

```
Authorization: Basic base64(alice:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx)
```

The server forwards it to Nextcloud unchanged and lets Nextcloud decide. It stores nothing,
caches no credential and never treats the header as an identity claim of its own, so one
deployment can serve several people without a token store. Every client that lets you add a
header to a remote MCP server works with this. In Claude Code:

```bash
claude mcp add --transport http nextcloud https://mcp.example.com/mcp \
  --header "Authorization: Basic $(printf 'alice:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx' | base64)"
```

Put the deployment behind TLS. Basic is base64, not encryption, and a proxy on the way sees
the password in plain text otherwise.

### Single user alternative: a static bearer

If exactly one person uses the deployment, a fixed token is simpler than a Basic header per
request:

```bash
export NC_MCP_URL=https://cloud.example.com
export NC_MCP_USER=alice
export NC_MCP_APP_PASSWORD=xxxxx-xxxxx-xxxxx-xxxxx-xxxxx
export NC_MCP_STATIC_BEARER=a-long-random-string
export NC_MCP_PUBLIC_URL=https://mcp.example.com
export NC_MCP_ALLOWED_HOSTS=mcp.example.com
uv run uvicorn mcp_connector.entry_http:app --host 0.0.0.0 --port 8765
```

Clients then send `Authorization: Bearer a-long-random-string`. The bearer authenticates
the caller of this server; it does not select a Nextcloud user. The account comes from the
environment, exactly as in stdio mode. The two HTTP modes are mutually exclusive, and
starting the server with both configured is an error rather than a silent preference.

### Host allow list

`NC_MCP_ALLOWED_HOSTS` is a comma separated list of the `Host` headers this server accepts.
It is not the bind address. `--host 0.0.0.0` lets the socket listen everywhere and still
allows nobody in, because the allow list is checked separately.

Each bare name is expanded into two entries, `example.com` and `example.com:*`, because a
client that was given a port puts the port into the `Host` header. A name that already
carries a port or a wildcard is taken exactly as written.

Without the variable, only `127.0.0.1`, `localhost` and `[::1]` are accepted.

Behind a reverse proxy that rewrites `Host` itself, and only there, the check can be turned
off with `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=true`.

## ExApp mode (installed through AppAPI)

The third way to run this server is as a Nextcloud ExApp, installed by an administrator
through AppAPI. It sits beside stdio and the standalone HTTP mode above: same code, same 15
tools, a different place the identity comes from. Installing it is a separate document,
[exapp-install.md](exapp-install.md); this section is about connecting a client to an
instance where it is already installed.

The client endpoint is:

```
https://<nextcloud>/exapps/mcp_connector/mcp
```

That is the public Nextcloud URL with the ExApp prefix, not a port of its own. AppAPI reaches
every ExApp under `/exapps/<appid>`, and the reverse proxy in front of Nextcloud forwards it.

In phase 2 the authentication is a Nextcloud username and an app password, sent as an ordinary
Basic header, exactly as in the HTTP passthrough above:

```
Authorization: Basic base64(alice:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx)
```

The difference is where that header is read. It goes to HaRP, the AppAPI proxy, which resolves
it to a Nextcloud user and hands the ExApp the resolved identity as signed AppAPI headers. The
server never receives the app password as a Nextcloud credential of its own; it receives who
the user is, and every Nextcloud request then runs under that user's own permissions. This is
why the permission promise holds through the whole chain and not only in our client layer.

OAuth is the phase 3 way to authenticate here, so a client will later present a token instead
of a Basic header. Until then the app password is the supported credential, and the endpoint
is otherwise the same, so nothing about the client configuration changes when OAuth arrives
except the header.

In Claude Code, the same command as the HTTP mode points at the ExApp endpoint:

```bash
claude mcp add --transport http nextcloud https://cloud.example.com/exapps/mcp_connector/mcp \
  --header "Authorization: Basic $(printf 'alice:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx' | base64)"
```

### Three things that are specific to this mode

1. **The PHP proxy path is not the way in.** AppAPI also exposes an ExApp under
   `/apps/app_api/proxy/mcp_connector/...`, and it answers. It is still not the recommended
   endpoint: its streaming and header behaviour differ from the direct `/exapps/` route, which
   is the one measured and relied on here. The measurement of both paths is in
   [spike-discovery.md](spike-discovery.md); use `/exapps/mcp_connector/mcp`.
2. **No `/exapps/` rule, no connection.** The reverse proxy in front of Nextcloud has to route
   `/exapps/*` to HaRP. Without that rule the installation never even completes its heartbeat,
   let alone serves `/mcp`, and the failure looks like a Nextcloud problem rather than a proxy
   one. The bundled Caddy of Nextcloud All-in-One ships this rule, and `deploy/Caddyfile`
   rebuilds it for the local topology.
3. **Discovery lives at a pointer, not at the canonical path.** The RFC 9728 metadata a phase 3
   OAuth client looks for is reachable unauthenticated over the ExApp, but the canonical
   `/.well-known/oauth-protected-resource/...` root path is answered by Nextcloud with a 404, so
   a client has to follow the `resource_metadata` pointer from the `WWW-Authenticate` header
   instead. The fallback, a reverse proxy rule that serves the metadata at the canonical path,
   is written out in [spike-discovery.md](spike-discovery.md).

## Browser onboarding (no app password to copy by hand)

An assistant app that cannot speak OAuth still needs a credential, and the section at the top
of this page asks you to create one in the Nextcloud settings yourself. The onboarding page
does that part for you. Open it in a browser:

```
https://<nextcloud>/exapps/mcp_connector/connect
```

What happens there, in four steps:

1. The page explains what it does and offers one button, "Continue to Nextcloud sign in".
2. Pressing it opens the Nextcloud sign in page in a new window. This is Nextcloud's own
   page on your own instance, with your own login and your own second factor. Approve the
   connection there, then come back to the connector page.
3. That page waits for the result. It refreshes itself every few seconds and carries a
   "Check now" button for browsers where automatic refresh is switched off.
4. When the sign in is complete, the page shows your user name and one credential for your
   assistant app.

Enter both into your client exactly like the app password in the sections above: user name
and credential as Basic credentials against `https://<nextcloud>/exapps/mcp_connector/mcp`.

**The credential is shown once.** Nothing of it is stored on this server, so there is no page
that can show it again. If you miss it, lose it, or close the window too early, open
`/connect` again and run the sign in a second time. The old attempt runs out on its own after
twenty minutes, and an unused credential can be removed in the Nextcloud settings.

### How to tell a real page from a fake one

This server never asks for your Nextcloud password. Not on the onboarding page, not on the
waiting page, not on the result page. None of them has an input field at all. A page that
looks like this one and asks you to type your Nextcloud password is not from this server:
close it, and tell your administrator.

The credential you get is an ordinary Nextcloud app password that belongs to you. It appears
in **Settings, Security, Devices and sessions** under the name of this connector, together
with every other connection of your account, and you can end it there at any time without
touching your password or your second factor.

### Which way is meant for which client

* **OAuth** is the way for Claude.ai and ChatGPT, which register themselves and run the whole
  authorization in the client. It arrives with plan 03-06 of this phase; nothing has to be
  copied by hand there.
* **Browser onboarding** is the way for every other client: it produces the credential the
  Basic header of the sections above needs, without you creating an app password by hand.
* **The app password sections above stay valid** for stdio, for the standalone HTTP mode and
  for the ExApp mode. The onboarding only replaces the manual step of creating one.

## Three things that will go wrong

### 1. `421 Misdirected Request`

Symptom: the client cannot connect at all, and the server answers `POST /mcp` with a 421
before any MCP message. `GET /health` keeps answering 200, which is the confusing part:
`/health` is a plain route and is deliberately not behind the host check, so a healthy
probe says nothing about whether a client can connect.

Cause: the `Host` header of the request is not in the allow list. This check runs in the
transport layer, before any code of this server, so there is no friendly error message.

Fix: set `NC_MCP_ALLOWED_HOSTS` to the name the client actually uses, including the port if
the client was given one. Reproduce and verify against the MCP endpoint, never against
`/health`:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H 'Host: mcp.example.com' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  http://127.0.0.1:8765/mcp
```

`421` means the name is missing from the allow list. `200` means it is accepted.

### 2. `Session terminated` or a client that reconnects in a loop

Symptom: an older client connects, works for one call and then reports a terminated
session, or reconnects on every message.

Cause: this server is stateless by design, and it keeps no session between requests. That
is what makes a restart survivable, and it is what some clients built against the 2025 spec
do not expect. It is also the exact bug behind `nextcloud/context_agent#227`.

Fix: update the client, or use stdio. Do not work around it by adding session state to the
server: a session store would break the restart guarantee for everyone. If the client is
based on the MCP SDK 1.x, note that both protocol generations are served from the same
endpoint, so an up to date SDK 1.x client works too.

### 3. `429 Too Many Requests` after a wrong app password

Symptom: you fixed the password, and the server still answers with an error. A minute later
it works again.

Cause: Nextcloud counts failed logins per source IP and throttles that IP with an
increasing delay. A remote MCP server is a single IP for all of its users, so a handful of
wrong attempts can slow down everybody behind it.

Fix: wait, then retry with the correct app password. Create a fresh one instead of guessing.
On a server you control, an administrator can list and clear the entries with
`occ security:bruteforce:attempts` and `occ security:bruteforce:reset <ip>`. Do not disable
the protection on a production instance.

## Checking that it works

Ask the assistant for something that needs exactly one tool, for example "list the files in
the root of my Nextcloud". A correct answer means credentials, transport and permissions are
all in place. If the assistant answers with a plausible but invented list, the tool was not
called at all: check the tool list in the client first.

Remember what the tools cannot do. Nothing here deletes, overwrites, moves or re-shares
anything, and `files_search` matches names, not the text inside documents. See the
"What this server cannot do" section of the [README](../README.md).
