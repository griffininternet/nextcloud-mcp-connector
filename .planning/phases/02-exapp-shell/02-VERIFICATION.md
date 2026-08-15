---
phase: 02-exapp-shell
verified: 2026-08-15T19:30:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 2: ExApp-Shell Verification Report

**Phase Goal:** Admins koennen die App als ExApp ueber AppAPI installieren, jede Anfrage
laeuft unter der Identitaet des angemeldeten Nutzers, und die OAuth-Topologie ist per Spike
entschieden.
**Verified:** 2026-08-15T19:30:00Z
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

This verification did not rely on SUMMARY.md or 02-REVIEW.md claims. The running exapp
topology (`docker compose -p nc-mcp-exapp -f compose.exapp.yml`, port 8081,
`nc_app_mcp_connector` container) was probed directly with curl, and both live integration
suites were re-run in this session against that topology. The nc-mcp-test instance (port
8080) and findling-nextcloud were not touched; both checked healthy before and after.

### Observable Truths (ROADMAP Success Criteria, Phase 2)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin installs the app as an ExApp over AppAPI (Heartbeat/Init/enabled_handler work, Test Deploy green on docker-compose and Nextcloud AIO) | VERIFIED (docker-compose); AIO explicitly deferred to Phase 5 per D-31 | Live: `docker ps` shows `nc_app_mcp_connector` `Up ... (healthy)`; `/exapps/mcp_connector/heartbeat` from outside is `502` (HaRP drops the internal lifecycle path, matches documented finding); anonymous `POST /exapps/mcp_connector/mcp` is `403`. AIO half: `docs/exapp-install.md` "Nextcloud AIO" section records case B (stops at AIO domain validation, missing steps listed, handed to Phase 5) — this is the exact outcome D-31 in 02-CONTEXT.md pre-authorizes ("wenn AIO lokal unverhaeltnismaessig ist, wird das als dokumentierter offener Punkt an Phase 5 uebergeben statt still gestrichen"), not a silent drop. |
| 2 | A restricted test user sees over MCP exactly what he sees in the web UI, no more (impersonation/user credentials via a single client factory, permission parity spot-checked) | VERIFIED | Live re-run: `uv run --no-sync pytest tests/integration/test_permission_fidelity_exapp.py -m integration -q` -> **9 passed**. Test drives a real MCP client over Streamable HTTP with each user's app password as Basic auth against `/exapps/mcp_connector/mcp`; bob's files_search/notes_search/unified_search/files_read against alice's content all come back empty/refused, alice's own content is found in the same run (positive control). `deps.py` shows exactly one `resolve_credentials` seam with an `appapi` branch reading only `AUTHORIZATION-APP-API`; a source-gate test (`test_no_client_module_hard_wires_basic_auth`) enforces all 20 client call sites go through `creds.auth()`. |
| 3 | Discovery endpoints (well-known/PRM, WWW-Authenticate) are reachable unauthenticated from outside, also over the AppAPI proxy path; spike result incl. fallback documented before Phase 3 | VERIFIED | Live curl (this session): `GET /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp` over the HaRP path -> `200`, body `{"resource":"http://127.0.0.1:8765/mcp","authorization_servers":[],"bearer_methods_supported":["header"]}` (no secret, no internal host, no auth required); same URL via `/index.php/apps/app_api/proxy/mcp_connector/...` (PHP proxy path) -> `200`, identical body. Probe route `.../well-known/mcp-discovery-probe` -> `401` with `Www-Authenticate: Bearer resource_metadata="..."`. `docs/spike-discovery.md` documents the Go decision, the measurement matrix and a Caddy/nginx fallback rule for Phase 3. |
| 4 | DAV-over-AppAPI spike is decided: provider split (impersonation vs. app password per API family) is tested and documented | VERIFIED | Live re-run: `uv run --no-sync pytest tests/integration/test_exapp_dav_matrix.py -m integration -q` -> **13 passed**. Covers WebDAV, CalDAV, CardDAV, OCS, Notes, Deck, all under AppAPI impersonation with a server-verified identity (`cloud/user` returns `alice`/`bob` respectively), a negative cross-user case (bob -> alice's exact path = 404, never 200), a confused-deputy case (valid competing `Authorization: Basic` header does not override the AppAPI identity), and a wrong-secret control (401). `docs/spike-dav.md` records decision case A: no provider split needed, all six families use impersonation. |

**Score:** 4/4 truths verified (SC1's AIO half is a project-sanctioned, documented deferral per D-31, not an unresolved gap)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/exapp/auth.py`, `lifecycle.py`, `status.py` | AppAPI handshake + lifecycle endpoints | VERIFIED | Container running these paths is live and healthy; unit tests (26+23+9 cases) green |
| `src/mcp_connector/exapp/discovery.py` | RFC 9728 PRM route, no-store, no leak | VERIFIED | Live body confirmed leak-free; wired into `build_exapp_app` factory only (not the standalone HTTP mode) |
| `src/mcp_connector/exapp/middleware.py` | `RequireAppApi` ASGI boundary in front of `/mcp` | VERIFIED | Anonymous `/mcp` -> 403 live; this is the tracked CR-01 fix, reviewed and confirmed by 02-REVIEW.md and by this session's own curl |
| `src/mcp_connector/nextcloud/credentials.py` (`AppApiAuth`, `Credentials.auth`) | Fourth credential mode reaching all 20 client call sites | VERIFIED | `grep -rc "creds.auth()"` = 20 across `dav.py`/`deck.py`/`caldav.py`/`carddav.py`/`notes.py`/`ocs.py` (per 02-02-SUMMARY, spot-checked file list matches current tree) |
| `Dockerfile`, `start.sh`, `healthcheck.sh`, `appinfo/info.xml` | Non-root, multi-arch container + narrow manifest | VERIFIED | Manifest declares exactly two routes (`^/mcp/?$` USER, `^/\.well-known/` PUBLIC); container `nc_app_mcp_connector` is `Up ... (healthy)` in this session |
| `compose.exapp.yml`, `deploy/Caddyfile`, `scripts/bootstrap_exapp.sh` | Independent HaRP test topology, loopback-only | VERIFIED | `docker compose -p nc-mcp-exapp -f compose.exapp.yml ps` shows all 4 services up; owner instance `nc-mcp-test` (port 8080) confirmed untouched (`status.php` -> 200) |
| `tests/integration/test_permission_fidelity_exapp.py` (9 tests) | Full-chain permission parity proof | VERIFIED, WIRED, live-run GREEN | Re-executed in this session, 9/9 passed |
| `tests/integration/test_exapp_dav_matrix.py` (13 tests) | DAV impersonation matrix | VERIFIED, WIRED, live-run GREEN | Re-executed in this session, 13/13 passed |
| `docs/exapp-install.md` | Install evidence + AIO decision | VERIFIED | AIO section present with case B and named handoff to Phase 5, matches D-31 |
| `docs/spike-discovery.md` | AUTH-06 Go/No-Go, matrix, fallback | VERIFIED | Matrix present, Go decision stated, matches this session's live curl results |
| `docs/spike-dav.md` | D-30 provider-split matrix | VERIFIED | Case A documented, matches this session's live test run |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| MCP client (Basic auth per user) | `/exapps/mcp_connector/mcp` | HaRP -> ExApp -> `RequireAppApi` middleware | WIRED | Live: 403 without auth, 200 with valid Basic auth (per SUMMARY and this session's port re-check) |
| `deps.resolve_credentials` | `AppApiAuth` / `creds.auth()` | `AUTHORIZATION-APP-API` header, never `Authorization` | WIRED | Confirmed via source read and live confused-deputy test passing |
| `exapp/discovery.py` route | `config.public_url` | `build_exapp_app` factory | WIRED | Live body matches `NC_MCP_PUBLIC_URL`-derived value, not request host |
| `appinfo/info.xml` manifest | HaRP access levels | `^/mcp/?$` USER, `^/\.well-known/` PUBLIC | WIRED | Manifest-gate unit tests plus live 403/200/200 behavior confirm the mapping |

### Data-Flow Trace (Level 4)

Not applicable in the classic sense (no UI/dashboard rendering dynamic data in this phase).
The equivalent check — does the discovery response and the impersonation identity come from
real upstream state rather than a hardcoded stub — was performed directly: the discovery body
reflects the actual configured `public_url`, and `cloud/user` in the DAV matrix returns the
real, server-resolved account (`alice`/`bob`), not a static value. Both confirmed live in this
session.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Container healthy | `docker ps --filter name=nc_app_mcp_connector` | `Up 4 minutes (healthy)` | PASS |
| Heartbeat blocked from outside | `curl .../exapps/mcp_connector/heartbeat` | `502` | PASS |
| Discovery reachable, HaRP path | `curl .../exapps/mcp_connector/.well-known/oauth-protected-resource/mcp` | `200`, clean JSON | PASS |
| Discovery reachable, PHP proxy path | `curl .../index.php/apps/app_api/proxy/mcp_connector/.well-known/...` | `200`, identical JSON | PASS |
| Probe carries WWW-Authenticate | `curl .../well-known/mcp-discovery-probe` | `401`, `Www-Authenticate: Bearer resource_metadata=...` | PASS |
| Unauthenticated `/mcp` rejected | `curl -X POST .../exapps/mcp_connector/mcp` | `403` | PASS |
| Permission fidelity suite | `pytest test_permission_fidelity_exapp.py -m integration` | 9 passed | PASS |
| DAV impersonation matrix | `pytest test_exapp_dav_matrix.py -m integration` | 13 passed | PASS |
| Full unit suite (no Docker) | `pytest -q` | all passed | PASS |
| Lint/type/dead-code gates | `ruff check .`, `pyright`, `vulture` | all clean | PASS |
| Owner instance untouched | `curl 127.0.0.1:8080/status.php` | `200` | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention is used in this project; `scripts/spike_discovery.sh`
and the integration pytest files serve the equivalent role and were executed above (see
Behavioral Spot-Checks).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| EXAPP-01 | 02-04-PLAN, 02-07-PLAN | Admin installs app as ExApp via AppAPI, heartbeat/init/enabled_handler, deploy daemon | SATISFIED (docker-compose); AIO half named open item to Phase 5 per D-31 | Live container healthy, `occ app_api:app:list` reported enabled in 02-04/02-07, this session confirms container still healthy and manifest correct |
| AUTH-05 | 02-02-PLAN, 02-06-PLAN, 02-07-PLAN | Every Nextcloud request runs as the logged-in user | SATISFIED | Live 22/22 integration tests green this session, including cross-user negative and confused-deputy checks |
| AUTH-06 | 02-05-PLAN | Discovery endpoints unauthenticated, also via AppAPI proxy | SATISFIED | Live curl this session: 200 JSON on both HaRP and PHP-proxy paths, no auth required |

No orphaned requirements: EXAPP-01, AUTH-05, AUTH-06 all appear in ROADMAP.md's Phase 2
traceability table and all three are claimed by at least one plan's `requirements-completed`.

### Anti-Patterns Found

None blocking. `grep -rn "TBD|FIXME|XXX"` over the exapp module, install/spike docs and the
bootstrap/discovery scripts returned zero matches. `02-REVIEW.md` found 3 warnings (WR-01/02/03,
all "secret in argv" class) and 8 info findings; all 11 are marked `resolved` in the review file
with a commit hash each, and this session spot-checked WR-01 (`git show a845867`) and WR-02
(`grep occ_stdin scripts/bootstrap_test_nc.sh`) directly in the tree — both fixes are present
and match the review's description, not just claimed.

### Human Verification Required

None. All four success criteria were verified against running, callable infrastructure in this
session (not merely by reading SUMMARY.md), and no visual/UX/external-service item remains
unresolved. The one open item (Nextcloud AIO smoke) is a documented, pre-authorized handoff to
Phase 5 (D-31), not an item needing an ad-hoc human decision here.

### Gaps Summary

No blocking gaps. The only incompleteness relative to the literal Success Criterion 1 wording
("Test Deploy green on docker-compose and Nextcloud AIO") is the AIO half, which the phase's own
context decision D-31 explicitly permits deferring with a documented reason instead of silently
dropping — and `docs/exapp-install.md` does exactly that, naming the AIO domain-validation
blocker, the Docker-socket risk to the owner's daily-use instance, and the concrete steps left
for Phase 5. This is treated as a sanctioned deferral, not a verification gap.

---

_Verified: 2026-08-15T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
