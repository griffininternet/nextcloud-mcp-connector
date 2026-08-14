# MCP Connector for Nextcloud

A curated MCP server that connects your Nextcloud (files, calendar, notes, deck, contacts) to AI
assistants such as Claude, Cursor, ChatGPT or your own agents.

**This server can never delete, overwrite or re-share anything.**

That sentence is the design constraint, not a promise of good behaviour. The server does not
implement a single destructive call: no DELETE, no MOVE, no overwrite, no share modification. Write
tools are create-only, and a name collision is answered with a clear refusal instead of a silent
overwrite.

Two more properties follow from the same idea:

- **The assistant never sees more than you do.** Every request runs with your own Nextcloud
  credentials, so Nextcloud permissions apply unchanged.
- **15 tools, not 150.** The tool set is curated so that this server fits next to your other MCP
  servers, even in clients with a hard tool limit.

License: AGPL-3.0-or-later. App id, package names and repository name are frozen, see
[docs/app-id-freeze.md](docs/app-id-freeze.md).

## Status

Version 0.1.0, phase 1 (server core) in progress. The tool table below is the v1 tool set. Tools
land one plan at a time and the table is verified against the live tool registry before release.

## Quickstart (stdio)

You need a Nextcloud app password, not your login password. Create one in Nextcloud under
Settings, Security, Devices and sessions.

```bash
uv tool install nextcloud-mcp-connector   # or: uv run nc-mcp inside a checkout

export NC_MCP_URL=https://cloud.example.com
export NC_MCP_USER=alice
export NC_MCP_APP_PASSWORD=xxxxx-xxxxx-xxxxx-xxxxx-xxxxx

nc-mcp
```

Client configuration, for example for Claude Desktop or Cursor:

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

## HTTP mode

The same server also speaks Streamable HTTP for remote clients:

```bash
export NC_MCP_URL=https://cloud.example.com
export NC_MCP_ALLOWED_HOSTS=mcp.example.com
uv run uvicorn mcp_connector.entry_http:app --host 127.0.0.1 --port 8765
```

The MCP endpoint is `POST /mcp`, and `GET /health` answers `{"status":"ok","version":"..."}`
without authentication. One endpoint serves both protocol generations: clients on the current
spec and clients built on MCP SDK 1.x are routed by the protocol version of their request, and a
restart cannot interrupt a conversation because the server keeps no session state.

Credentials are not read from the environment in this mode. They travel per request in the
`Authorization` header (Basic, user and app password) and are forwarded unchanged to Nextcloud,
which authenticates them. The server never treats the header as an identity claim of its own, and
it stores nothing, so one deployment can serve several users without a credential store.

For single user deployments a static bearer token is available instead: set
`NC_MCP_STATIC_BEARER`, and the Nextcloud account is taken from the environment like in stdio
mode. The two HTTP modes are mutually exclusive.

`NC_MCP_ALLOWED_HOSTS` is not optional in practice. Without it, the transport layer only accepts
`Host: localhost` and `Host: 127.0.0.1` and answers every other request with `421 Misdirected
Request` before any MCP code runs. Note that this is the `Host` header of incoming requests, not
the bind address: `--host 0.0.0.0` allows nobody in.

## Environment variables

| Variable | Mode | Required | Purpose |
|----------|------|----------|---------|
| `NC_MCP_URL` | all | yes | Base URL of your Nextcloud, including a subpath if you use one |
| `NC_MCP_USER` | stdio, static bearer | yes | Nextcloud user id |
| `NC_MCP_APP_PASSWORD` | stdio, static bearer | yes | App password from Settings, Security, Devices and sessions |
| `NC_MCP_ALLOWED_HOSTS` | HTTP | yes in practice | Comma separated `Host` header allow list of this server; a port wildcard is added per name |
| `NC_MCP_STATIC_BEARER` | HTTP | no | Static bearer token for single user deployments; without it, clients authenticate per request |
| `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION` | HTTP | no | Set to `true` only behind a proxy that controls the `Host` header |
| `NC_MCP_PUBLIC_URL` | static bearer | no | Public URL of this server for the bearer discovery document |

No credential is ever logged, in any mode.

## Tools

Permission levels: **read** means the tool only reads, **create-only** means the tool can create
new objects but can never modify or remove existing ones.

| Tool | Permission | What it does |
|------|------------|--------------|
| `files_search` | read | Search files by name and metadata via WebDAV search |
| `files_list` | read | List a directory with names, sizes and modification times |
| `files_read` | read | Read the content of a single file |
| `files_upload` | create-only | Upload a new file; an existing path is refused, never overwritten |
| `calendar_list_events` | read | List events in an explicit time range, with an explicit time zone |
| `calendar_create_event` | create-only | Create a new event; existing events are never changed |
| `notes_search` | read | Find notes by title and content via the Nextcloud notes search provider |
| `notes_read` | read | Read a single note |
| `notes_create` | create-only | Create a new note; existing notes are never changed |
| `deck_browse` | read | Browse Deck boards, stacks and cards |
| `deck_create_card` | create-only | Create a new card in a stack; existing cards are never changed |
| `contacts_search` | read | Search address book contacts |
| `unified_search` | read | Query the Nextcloud unified search across providers, permission aware |
| `search` | read | OpenAI compatible search entry point, delegates to unified search |
| `fetch` | read | OpenAI compatible fetch entry point, resolves an id to a file, note, card or event |

`search` and `fetch` exist because the ChatGPT connector profile requires exactly these two names
and schemas. They are thin wrappers over the tools above, not a second implementation.

### Optional apps

Notes and Deck are optional Nextcloud apps. The tool list is the same everywhere: it never depends
on which apps an instance has, so it stays cacheable and predictable for every client. If an app is
missing, the tool says so in one sentence and names an alternative, for example
"The Notes app is not installed on this Nextcloud." Calendars and contacts need no app at all:
CalDAV and CardDAV are part of the Nextcloud core.

## What this server cannot do

- **No deleting.** No tool issues a DELETE against files, events, notes, cards or contacts.
- **No overwriting.** Writes are create-only. `files_upload` refuses an existing target path with a
  clear error instead of replacing it, and the create tools never touch an existing object.
- **No moving or renaming.** MOVE and COPY are not implemented.
- **No share changes.** The server neither creates, modifies nor removes shares, and it never
  changes permissions.
- **No admin access.** The server acts as one user with an app password and inherits exactly that
  user's permissions.
- **No full text search inside file contents** unless the Nextcloud Full text search app is
  installed and configured. Without it, file search matches names and metadata.
- **No background jobs, no sync, no local copy of your data.** Every call goes to your Nextcloud
  and returns.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

`uv run pytest` starts nothing and needs nothing. The two heavier layers are opt-in:

- `uv run pytest -m matrix` starts the HTTP server as a subprocess and checks that a current
  client and a client on MCP SDK 1.29 are both served from the same endpoint, and that the
  conversation survives a restart. It needs no Nextcloud.
- `uv run pytest -m integration` needs the local test Nextcloud from `compose.test.yml`.

## License

AGPL-3.0-or-later, see [LICENSE](LICENSE).
