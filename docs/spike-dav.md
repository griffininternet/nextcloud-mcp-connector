# DAV Impersonation Spike (D-30, AUTH-05)

**Status:** done, decision case A (every family runs under impersonation)
**Decision date:** 2026-08-15
**Nextcloud version:** 34.0.2 (build 34.0.2.1)
**AppAPI version:** 34.0.0
**Deploy daemon:** HaRP, over the `compose.exapp.yml` topology (Caddy on `127.0.0.1:8081`)
**Scope:** does the identity of the logged in user arrive in every Nextcloud API family when
the only credential in play is `APP_SECRET`, with the user id carried inside
`AUTHORIZATION-APP-API`, and does the boundary between two users hold under that path.

This spike answers the empirical half of AUTH-05. `02-RESEARCH.md` proves the mechanism at
the source (`OC::tryAppAPILogin` plus `AppAPIAuthBackend` and `DavPlugin` for sabre) but
rates the per family coverage only MEDIUM and carries it as assumption A1. The measurement
below confirms A1: all six families run under AppAPI impersonation, so there is no provider
split and no app password fallback for any family in this phase.

## Decision

The matrix D-30 asks for: one row per API family, the auth path, the evidence, and whether
the identity was verified server side. The measuring process holds no Nextcloud app password
and no static bearer, so a `200` in this table can only come from `APP_SECRET` plus the user
id in the AppAPI header.

| Family | Endpoint | Auth path | Evidence (test, HTTP status) | Identity verified |
|--------|----------|-----------|------------------------------|-------------------|
| WebDAV Files | `/remote.php/dav/files/<user>/` | AppAPI impersonation | `test_webdav_propfind_lists_the_impersonated_home` (207), `test_webdav_search_answers_under_impersonation` (207), `test_webdav_put_is_create_only_under_impersonation` (201 create, 412 refused) | yes, `exapp_impersonation.log` records `user=alice`/`user=bob` for the `remote.php` PUT and GET |
| CalDAV | `/remote.php/dav/calendars/<user>/` | AppAPI impersonation | `test_caldav_report_expands_under_impersonation` (207) | yes, same sabre server as Files, `remote.php/dav` line in the log |
| CardDAV | `/remote.php/dav/addressbooks/users/<user>/` | AppAPI impersonation | `test_carddav_report_answers_under_impersonation` (207) | yes, same sabre server as Files |
| OCS | `/ocs/v2.php/...` | AppAPI impersonation | `test_ocs_identity_is_the_impersonated_alice` (200), `test_ocs_identity_is_the_impersonated_bob` (200) | yes, `GET /ocs/v2.php/cloud/user` returns `ocs.data.id = alice` and `= bob` respectively |
| Notes REST | `/index.php/apps/notes/api/v1/notes` | AppAPI impersonation | `test_notes_list_and_create_under_impersonation` (200 list, 201 create) | yes, runs through `OC::tryAppAPILogin`, verified for the same account by the OCS row |
| Deck REST | `/index.php/apps/deck/api/v1.0/boards` | AppAPI impersonation | `test_deck_read_and_create_under_impersonation` (200 read, board/stack/card create) | yes, runs through `OC::tryAppAPILogin`, verified for the same account by the OCS row |

App passwords remain reserved for the standalone HTTP passthrough mode and the stdio mode of
phase 1. They are never used inside the ExApp, and this spike introduces no per family
exception to that rule.

## Evidence

All commands were run on 2026-08-15 against the running HaRP topology. Header values that
carry `APP_SECRET` (the `AUTHORIZATION-APP-API` value is base64 of `<user>:<APP_SECRET>` and
is exactly as sensitive as the secret) are never printed. Only status codes and the server
returned `id` are shown.

### The integration suite over the running topology

```
set -a && . ./.env.exapp && set +a
uv run pytest tests/integration/test_exapp_dav_matrix.py -m integration -q

13 passed in 2.61s
```

The same file is skipped, not run, without the topology:

```
uv run pytest -q            # full suite, no NC_MCP_URL
709 passed, 54 deselected   # the spike file is collected and skipped
```

### The two controls

Control one (no app password in the process) is enforced by
`test_the_measuring_process_holds_no_nextcloud_app_password`: `NC_MCP_APP_PASSWORD` and
`NC_MCP_STATIC_BEARER` are absent, and the credential the suite builds carries
`mode="appapi"` with `secret=APP_SECRET`, never a user password.

Control two (a wrong secret is refused):

```
# GET /ocs/v2.php/cloud/user with a 64 zero APP_SECRET as alice
HTTP 401
```

A `401` for the wrong secret is the proof that a real `APP_SECRET` carried every `200` below.

### OCS identity, the central server side proof

```
# GET /ocs/v2.php/cloud/user, impersonating alice
{"id": "alice", "display-name": "alice"}
HTTP 200

# GET /ocs/v2.php/cloud/user, impersonating bob
{"id": "bob", "display-name": "bob"}
HTTP 200
```

The server returns exactly the impersonated account for both users.

### The negative case: bob cannot reach alice's file, even by the exact path

```
# PUT /remote.php/dav/files/alice/<marker>.md, impersonating alice
create as alice HTTP 201

# GET /remote.php/dav/files/alice/<marker>.md, impersonating bob
read alices path as bob HTTP 404
```

The path is already known, so nothing but Nextcloud's own permission check stands between
bob and the file. The answer is `404`, never `200`. This is the mitigation for T-02-50.

### The confused deputy check: a client header cannot override the impersonation

```
# GET /ocs/v2.php/cloud/user
#   AUTHORIZATION-APP-API impersonates bob
#   plus a fully valid "Authorization: Basic <alice:app-password>" on top
cloud/user id = "bob"
HTTP 200
```

Even a valid competing Basic credential for alice does not change who the request runs as:
the identity comes from `AUTHORIZATION-APP-API` alone. A client set `Authorization` header is
ignored, which is the property phase 3 needs when `/mcp` becomes public.

### Server side impersonation log

Every request above appears in `data/exapp_impersonation.log`, one line per request with the
resolved user. The negative case and the confused deputy case are the interesting rows: the
GET on alice's file is logged as `user=bob` and answered `404`, and the competing header
request is logged as `user=bob`.

```
{"time":"2026-08-15T11:55:26+00:00","remoteAddr":"172.29.42.1","user":"alice","app":"mcp_connector","method":"PUT","url":"/remote.php/dav/files/alice/nurfueralice-evidence-3459.md","message":"impersonation request","version":"34.0.2.1"}
{"time":"2026-08-15T11:55:27+00:00","remoteAddr":"172.29.42.1","user":"bob","app":"mcp_connector","method":"GET","url":"/remote.php/dav/files/alice/nurfueralice-evidence-3459.md","message":"impersonation request","version":"34.0.2.1"}
{"time":"2026-08-15T11:55:27+00:00","remoteAddr":"172.29.42.1","user":"bob","app":"mcp_connector","method":"GET","url":"/ocs/v2.php/cloud/user","message":"impersonation request","version":"34.0.2.1"}
```

The `remoteAddr` is the reverse proxy inside the compose network, not a public address.

## Consequence

Case A applies: every one of the six families runs under AppAPI impersonation with a server
verified identity, so there is no provider split. Each family reads and writes as the
impersonated user, the create only boundary of phase 1 holds under the new auth path (a
second PUT to the same file is refused with `412`), and the boundary between two users holds
even when the path is known (`404`, never `200`).

Concretely:

- The single client factory (`Credentials.auth` behind the twenty call sites) is the whole
  change. Tool code is untouched, as D-26 requires.
- App passwords stay reserved for the standalone HTTP mode and stdio of phase 1. They are
  never used inside the ExApp.
- Assumption A1 of `02-RESEARCH.md` is confirmed. AUTH-05 is met, not pending.

Because no family failed, the D-27 fallback path is not taken. For the record: a fallback to
per user app passwords for a single family would have to be a deliberate, documented
configuration, never a silent runtime behaviour, and an instance wide shared admin token
stays out of scope (PROJECT.md). None of that is needed here.

## What this does not prove

The measurement is honest about its edges.

- It ran against Nextcloud 34.0.2 with SQLite in a throwaway instance, with the Notes, Deck
  and Calendar apps in the versions the bootstrap installs.
- Group folders, external storage, server side encrypted instances and LDAP or SSO backed
  users are not part of the measurement. Impersonation resolves the account the same way, but
  the storage and ACL layers under it differ, and each is its own question.
- Shared resources (a calendar or a folder shared from another account into the impersonated
  user) were not exercised beyond the negative case. The negative case proves the default
  boundary holds; the behaviour of an explicit share is Nextcloud's own ACL and was not the
  subject of this spike.
- The Deck card create needed a board and a stack, which a fresh account does not have. Both
  were created with the same impersonating credentials as setup, so the create path is proven
  under impersonation, but only against a board this account owns.
