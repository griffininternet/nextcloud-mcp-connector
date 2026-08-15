---
phase: 02-exapp-shell
plan: 06
subsystem: auth
tags: [dav-spike, impersonation, appapi, auth-05, webdav, caldav, carddav, ocs, notes, deck, integration]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "The fourth credential mode appapi (Credentials.auth -> AppApiAuth) behind the twenty client call sites (02-02)"
  - phase: 02-exapp-shell
    provides: "A running ExApp behind HaRP with alice and bob as impersonatable accounts and .env.exapp with APP_ID, APP_SECRET, APP_VERSION (02-04)"
provides:
  - "tests/integration/test_exapp_dav_matrix.py: the automated impersonation matrix, one test per API family, two controls, the cross user negative case and a confused deputy check, all built with mode=appapi and APP_SECRET alone"
  - "tests/conftest.py: the exapp_env fixture that reads the AppAPI deploy identity from the environment and skips by name when the topology is not configured"
  - "docs/spike-dav.md: the D-30 matrix with the server verified identity per family, decision case A (no provider split) and the honest limits of the measurement"
affects: [03 OAuth topology, 05 store submission, any later plan that adds a Nextcloud API family]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The spike measures through the real client functions and the real tools, so it exercises the same Credentials.auth seam as production, not a hand built request; the only two hand built requests are the cross user negative URL and the confused deputy header, each named at its call site"
    - "Two controls run before the matrix: no app password or static bearer in the process, and a wrong APP_SECRET is refused, so a green row can only be explained by impersonation"
    - "The identity is proven server side (GET /ocs/v2.php/cloud/user plus data/exapp_impersonation.log), never inferred from a 2xx alone (D-30)"

key-files:
  created:
    - tests/integration/test_exapp_dav_matrix.py
    - docs/spike-dav.md
  modified:
    - tests/conftest.py

key-decisions:
  - "Decision case A: all six API families run under AppAPI impersonation with a server verified identity, so there is no provider split and no app password fallback in this phase; assumption A1 of 02-RESEARCH.md is confirmed and AUTH-05 is met"
  - "App passwords stay reserved for the standalone HTTP passthrough and stdio modes of phase 1; they are never used inside the ExApp, and D-27 is satisfied without taking the fallback path"
  - "The negative case targets alices file path with bobs impersonation headers on purpose and asserts 403 or 404 (measured 404), which is the elevation of privilege proof T-02-50, stronger than an empty list"
  - "The confused deputy check sends a fully valid Basic Authorization for alice on top of bobs AppAPI headers and proves cloud/user still returns bob: a client set Authorization header cannot override the impersonated identity"

requirements-completed: [AUTH-05]

# Metrics
duration: 45 min
completed: 2026-08-15
---

# Phase 2 Plan 06: DAV Impersonation Spike (D-30, AUTH-05) Summary

**The DAV spike is decided as case A: every one of the six Nextcloud API families (WebDAV, CalDAV, CardDAV, OCS, Notes, Deck) runs under AppAPI impersonation against a real HaRP topology, the identity is proven server side for alice and for bob, a wrong APP_SECRET is refused, bob cannot reach alices file even by the exact path (404, never 200), and a valid client set Authorization header cannot override the impersonated identity. There is no provider split and no app password fallback; assumption A1 is confirmed and AUTH-05 is met.**

## Performance

- **Duration:** 45 min
- **Completed:** 2026-08-15
- **Tasks:** 2
- **Files modified:** 3 (2 new, 1 changed)

## The DAV impersonation matrix

| Family | Endpoint | Auth path | HTTP status | Server verified identity |
|--------|----------|-----------|-------------|--------------------------|
| WebDAV Files | `/remote.php/dav/files/<user>/` | AppAPI impersonation | PROPFIND 207, SEARCH 207, PUT 201 create / 412 refused | yes, `exapp_impersonation.log` records `user=alice` and `user=bob` for the `remote.php` requests |
| CalDAV | `/remote.php/dav/calendars/<user>/` | AppAPI impersonation | REPORT 207 | yes, same sabre server, logged under the impersonated user |
| CardDAV | `/remote.php/dav/addressbooks/users/<user>/` | AppAPI impersonation | REPORT 207 | yes, same sabre server |
| OCS | `/ocs/v2.php/cloud/user` | AppAPI impersonation | 200 | yes, `ocs.data.id = alice` and `= bob` respectively |
| Notes REST | `/index.php/apps/notes/api/v1/notes` | AppAPI impersonation | 200 list, 201 create | yes, via `OC::tryAppAPILogin`, cross checked by the OCS row for the same account |
| Deck REST | `/index.php/apps/deck/api/v1.0/boards` | AppAPI impersonation | 200 read, create ok | yes, via `OC::tryAppAPILogin`, cross checked by the OCS row |

Measured against Nextcloud 34.0.2 (build 34.0.2.1), AppAPI 34.0.0, over the `compose.exapp.yml` HaRP topology on `127.0.0.1:8081`.

## The security proofs (owner directive: no gaps, clean)

- **Every threat position closed individually with evidence**, see the table below, not a blanket claim.
- **The negative case is the core of AUTH-05.** A file created as alice at `/remote.php/dav/files/alice/<marker>.md` was requested with bobs impersonation headers and answered `404`, never `200`. The path was already known, so nothing but Nextcloud's own permission check stood between bob and the file. The impersonation log records that request as `user=bob`, GET on alices file, and the answer was `404`.
- **The confused deputy check.** A request with bobs `AUTHORIZATION-APP-API` plus a fully valid `Authorization: Basic <alice:app-password>` on top returned `cloud/user id = bob`, `HTTP 200`. A client set Authorization header does not change who the request runs as: the identity comes from `AUTHORIZATION-APP-API` alone. This is the property phase 3 needs when `/mcp` becomes public.
- **The two controls make the matrix meaningful.** The measuring process holds no `NC_MCP_APP_PASSWORD` and no `NC_MCP_STATIC_BEARER`, and a wrong `APP_SECRET` (64 zeros) was refused with `401`. A green row can therefore only be explained by a real `APP_SECRET` plus the user id in the AppAPI header.
- **D-27 is satisfied without the fallback.** No family failed, so no provider split and no per family app password fallback is needed. For the record: such a fallback would have to be a deliberate, documented configuration, never a silent runtime behaviour, and an instance wide shared admin token stays out of scope.

## Threat Model Coverage

| Threat ID | Disposition | Implementation | Evidence |
|-----------|-------------|----------------|----------|
| T-02-50 | mitigate | Bob cannot reach alices file over impersonation; the negative test targets the exact path and fails on a 200 | `test_bob_cannot_reach_alices_home_even_with_the_exact_path` (404); impersonation log `user=bob` on alices file |
| T-02-51 | mitigate | Two controls before the matrix: no app password or static bearer in the process, and a wrong APP_SECRET is refused | `test_the_measuring_process_holds_no_nextcloud_app_password`, `test_a_wrong_app_secret_is_refused` (401) |
| T-02-52 | mitigate | The create only PUT boundary holds under impersonation: a second PUT to the same path is refused with 412 | `test_webdav_put_is_create_only_under_impersonation` (201 then ConflictError/412) |
| T-02-53 | mitigate | No secret and no base64 token in the test output or in docs/spike-dav.md; only status codes and the returned id are shown | grep for hex64 and AUTHORIZATION-APP-API in docs -> 0; non-ascii and dashes -> 0 |
| T-02-54 | mitigate | The server side impersonation log was collected and quoted in the doc, one line per request with the resolved user | docs/spike-dav.md "Server side impersonation log" |
| T-02-55 | mitigate | No fallback code in this plan; case A means no family failed, and the doc states that any fallback would be a documented configuration, never silent (D-27) | docs/spike-dav.md "Consequence"; no new runtime code added |

Beyond the threat model, the owner directive added the confused deputy proof, covered by `test_a_client_authorization_header_cannot_override_impersonation`.

## Task Commits

1. **Task 1: impersonation matrix over all six API families** - `b8a8b01` (test)
2. **Task 2: spike result, decision case A and the provider decision** - `81b6845` (docs)

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] The preserved exapp topology could not be brought up as is**
- **Found during:** setup before Task 1 (the plan assumes the topology is running)
- **Issue:** The exapp topology was down, and `docker compose up` refuses to start without a `HP_SHARED_KEY`, while the daemon registration stored in the preserved volume carried the old non hex key that the `require_hex64` gate (CR-02) rejects. The preserved volumes were unusable with the code as it stands, the same finding plan 02-05 already documented.
- **Fix:** Recreated the `nc-mcp-exapp` project only, with a fresh 64 hex `HP_SHARED_KEY`: `down -v` on that project, removed the orphan `nc_app_mcp_connector` container and its data volume, `up -d --wait`, then a full `bootstrap_exapp.sh` run. `APP_SECRET` stayed the valid 64 hex value already in `.env.exapp`, so it was pinned, not regenerated.
- **Files modified:** none (topology and volumes only)
- **Verification:** `occ app_api:app:list` reported `mcp_connector (MCP Connector): 0.1.0 [enabled]`; the integration suite ran green against it. The owner instance `nc-mcp-test` on port 8080 was checked and stayed healthy; no command ever touched that project.

**2. [Rule 1 - Bug] Lint fixes on the new test file**
- **Found during:** the pre commit gates of Task 1
- **Issue:** ruff reported an unused `ToolError` import, an unsorted import block, one over long line (E501) and one compound assertion (PT018).
- **Fix:** removed the unused import, let ruff sort the imports, shortened the skip message, and split the compound assertion into two.
- **Files modified:** tests/integration/test_exapp_dav_matrix.py
- **Verification:** ruff check and ruff format both clean; committed in `b8a8b01`.

### Documented plan-versus-reality notes

- **Deck needed a board and a stack for the card create.** A fresh account owns no board, and the Deck client has no board or stack write by design (create only). Both were created as setup with the same impersonating credentials, so the card create is still proven under impersonation, only against a board this account owns. Named at the call site and in the doc.
- **The confused deputy check uses alices real app password as the attack header.** It is read from `NC_MCP_TEST_APP_PASSWORD` and used only to prove it is ignored, never as a credential source for impersonation. This is the strongest form of the check: even a valid competing credential does not override the AppAPI identity.
- **`uv run --no-sync` throughout.** The owner `nc-mcp.exe` processes keep `.venv/Scripts/nc-mcp.exe` locked, so every gate ran with `--no-sync`, as in 02-01, 02-03, 02-04 and 02-05.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 lint) plus 3 documented notes.
**Impact on plan:** No scope change. No runtime code was added or changed; this plan is a measurement plus its result document.

## Checkpoints

The plan contains no checkpoints. AUTO_MODE was active; no auto-approve decision was needed. Package legitimacy: no new Python package was added (`pyproject.toml` and `uv.lock` unchanged), and no new container image was introduced.

## Verification Log

1. `set -a && . ./.env.exapp && set +a && uv run --no-sync pytest tests/integration/test_exapp_dav_matrix.py -m integration -q` -> **13 passed in 2.61s** against the running topology.
2. Per family raw HTTP status, measured directly: WebDAV PROPFIND 207, WebDAV SEARCH 207, CalDAV REPORT 207, CardDAV REPORT 207, Notes index 200, Deck boards 200.
3. OCS identity: `cloud/user` returned `{"id":"alice"}` and `{"id":"bob"}`, both 200.
4. Control: wrong APP_SECRET on `cloud/user` -> 401.
5. Negative case: create as alice 201, read alices path as bob -> 404.
6. Confused deputy: bob AppAPI headers plus valid alice Basic Authorization -> `cloud/user id = bob`, 200.
7. Impersonation log tail shows one line per request with the resolved user; the negative and confused deputy requests are logged as `user=bob`.
8. `uv run --no-sync pytest` (no marker, no Docker) -> **709 passed, 67 deselected** (the spike file is collected and deselected without the topology; baseline 709 passed, 54 deselected).
9. `uv run --no-sync ruff check .` -> All checks passed; `ruff format --check .` -> 107 files already formatted; `pyright` -> 0 errors; `vulture src scripts vulture_whitelist.py` -> empty; `check_tool_budget.py` -> exit 0.
10. Line endings: `docs/spike-dav.md` is LF only; non-ascii and em or en dashes -> 0. No hex64 secret and no AUTHORIZATION-APP-API token in the doc.
11. Owner instance `nc-mcp-test` on port 8080 checked -> healthy; never touched.

## Known Stubs

None. The new test has the running topology as its subject, the fixture has the test as its consumer, and the doc records the decision that AUTH-05 and phase 3 rely on. No placeholder value and no stubbed data source was introduced.

## Next Phase Readiness

- **AUTH-05 is met, not pending.** Every family runs under impersonation with a server verified identity, so phase 3 and the tool phases can rely on the single appapi credential mode. No follow up plan for a provider split is needed.
- **Phase 3 inherits the confused deputy finding.** A client set Authorization header cannot override the AppAPI identity, which is exactly what a public `/mcp` with the own token verifier needs.
- **Topology after the run:** the `nc-mcp-exapp` project is down, both its volumes are kept, and `nc_app_mcp_connector` was stopped. To measure again: `export HP_SHARED_KEY=$(openssl rand -hex 32)`, `docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait`, `bash scripts/bootstrap_exapp.sh` (the daemon key from this run is gone with the wiped volume, so a fresh bootstrap is needed).

## Self-Check: PASSED

- All new files exist on disk: `tests/integration/test_exapp_dav_matrix.py`, `docs/spike-dav.md`; the modified file `tests/conftest.py` carries the `exapp_env` fixture.
- Both task commits are in `git log`: `b8a8b01`, `81b6845`.
- No commit of this plan deletes a file.
- All plan verification points were measured, see the Verification Log.

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
