---
phase: 02-exapp-shell
plan: 07
subsystem: auth
tags: [permission-parity, auth-05, exapp, harp, impersonation, integration, phase-acceptance, aio, d-28, d-31]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "The fourth credential mode appapi behind the twenty client call sites, and the DAV impersonation matrix decided as case A (02-06)"
  - phase: 02-exapp-shell
    provides: "A running ExApp behind HaRP with the discovery routes and the RequireAppApi boundary in front of /mcp (02-04, 02-05)"
provides:
  - "tests/integration/test_permission_fidelity_exapp.py: the permission promise proven over the whole chain (MCP client, HaRP, ExApp, impersonation, Nextcloud ACLs), alice as the positive control and bob as the negative in one run, across files, notes and unified_search plus a direct files_read"
  - "scripts/bootstrap_exapp.sh: ensure_files_home, which initialises the test users' file homes so a fresh WebDAV SEARCH answers a clean empty instead of a 500"
  - "docs/client-setup.md: the ExApp operating mode beside stdio and standalone HTTP, with the endpoint, the phase 2 auth path and three mode specific pitfalls"
  - "docs/exapp-install.md: the Nextcloud AIO decision as a named handoff to phase 5 (D-31, case B)"
  - ".github/workflows/ci.yml: the exapp job runs both ExApp integration suites with a fresh HaRP key"
affects: [03 OAuth topology, 05 store submission and the Nextcloud AIO smoke]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The fidelity test drives a real MCP client over Streamable HTTP with a per user Basic header, so the identity is born in HaRP, not in our client layer; a green leak result can only be Nextcloud enforcing ACLs, not our code returning empty"
    - "Positive controls run in the same session as the leak tests, so an empty answer for bob can never pass for a boundary"
    - "A freshly occ-created user has an empty home with no searchable root; a neutral placeholder file plus a scan reproduces what a first login's skeleton does, and this is provisioning, not a test workaround"

key-files:
  created:
    - tests/integration/test_permission_fidelity_exapp.py
  modified:
    - .github/workflows/ci.yml
    - scripts/bootstrap_exapp.sh
    - docs/client-setup.md
    - docs/exapp-install.md
    - README.md

key-decisions:
  - "AUTH-05 is confirmed over the full chain, not only at the client library level: bob finds nothing of alice's through MCP, HaRP, the ExApp and impersonation, and alice finds her own content in the same run, across files, notes and unified_search"
  - "The Nextcloud AIO smoke is case B: it stops at AIO's domain validation, which requires a public domain and a valid public certificate, so it is handed to phase 5 as a named open item with the missing steps listed (D-31), never silently dropped"
  - "A fresh occ-created user's file home is unsearchable until it holds at least one file; the bootstrap now initialises both homes, so the parity proof answers a clean empty for bob instead of a 500"
  - "The middleware boundary is intact under the live topology: an anonymous /mcp is 403 and the lifecycle heartbeat is 502 from outside, so the phase 1 and interim security fixes were not weakened by this plan"

requirements-completed: [AUTH-05, EXAPP-01]

# Metrics
duration: 55 min
completed: 2026-08-15
---

# Phase 2 Plan 07: Permission Fidelity over the Full ExApp Chain and Phase Acceptance Summary

**The permission promise is proven over the whole chain a real user runs: an MCP client authenticates as bob with an ordinary app password, HaRP resolves the identity, the ExApp impersonates bob against Nextcloud, and bob finds nothing of alice's across files, notes and unified search, while alice finds her own file and note in the same run; the ExApp operating mode is documented beside stdio and HTTP, the Nextcloud AIO smoke is handed to phase 5 with a named reason, and the four Success Criteria of the phase are accepted with checkable evidence.**

## Performance

- **Duration:** 55 min
- **Completed:** 2026-08-15
- **Tasks:** 3 (2 auto, 1 checkpoint auto-approved under AUTO_MODE)
- **Files modified:** 6 (1 new, 5 changed)

## Accomplishments

- `tests/integration/test_permission_fidelity_exapp.py`: nine checks over the full ExApp chain. A helper opens an MCP session over Streamable HTTP against `/exapps/mcp_connector/mcp` with each user's app password as a Basic header (the pattern from `tests/compat/modern_client_check.py`), so the credential goes to HaRP and the identity is resolved there. The order is deliberate: a guard that alice and bob differ, then `tools/list` for both to prove the chain carries, then a positive control and a leak for files, for notes and for unified search, then the direct `files_read` on a known path. Every positive control runs in the same session as the matching leak, so an empty answer for bob can never pass for a boundary.
- `scripts/bootstrap_exapp.sh`: `ensure_files_home` for alice and bob. A user created with `occ user:add` never fires a first login, so it gets no skeleton and its files home is empty, and an empty home has no searchable root, so a WebDAV SEARCH raises `OCP\Files\NotFoundException` and surfaces as HTTP 500. Placing one neutral file and scanning it registers the root the search backend looks up, after which SEARCH answers an honest empty. This is what a real first login's skeleton would leave behind.
- `docs/client-setup.md`: a new ExApp section beside stdio and standalone HTTP, with the endpoint URL, the phase 2 app-password-through-HaRP authentication and OAuth named for phase 3, and three mode specific pitfalls (the PHP proxy path is not the way in, no `/exapps/` reverse proxy rule means no connection, discovery lives at the pointer not the canonical path). The existing text was extended, not shortened.
- `docs/exapp-install.md`: a Nextcloud AIO section that records case B. The smoke stops at AIO's domain validation, which demands a public domain and a valid public certificate, exactly the abort boundary D-31 names, with a second reason specific to this host (the socket-privileged AIO mastercontainer would run next to the owner's in-daily-use instance). The remaining steps for phase 5 are listed and the item is handed over explicitly.
- `README.md`: the known limitations reach the phase 2 state, with a row on the app-password-not-OAuth-yet ExApp auth and links to `exapp-install.md`, `spike-discovery.md` and `spike-dav.md`.
- `.github/workflows/ci.yml`: the exapp job gains a fresh HaRP key (WR-11 removed the default), uv setup and the two ExApp integration suites, so both the DAV matrix and the fidelity proof run in CI.
- The proof was run against a real, freshly rebuilt HaRP topology (Nextcloud 34.0.2, AppAPI 34.0.0), reproducibly, from wiped volumes with a fresh `HP_SHARED_KEY` and a fresh `APP_SECRET`.

## Task Commits

1. **Bootstrap files-home provisioning (deviation, Rule 3)** - `11cfe6b` (fix)
2. **Task 1: permission fidelity over the full chain plus the CI steps** - `c731e34` (test)
3. **Task 2: ExApp operating mode and the Nextcloud AIO decision** - `dd2494b` (docs)

## Phase 2 Acceptance Matrix (the checkpoint, auto-approved under AUTO_MODE)

| # | Success Criterion | Evidence | Status |
|---|-------------------|----------|--------|
| 1 | Admin installs the app as an ExApp over AppAPI (heartbeat, init, enabled work; deploy green on docker-compose and Nextcloud AIO) | `occ app_api:app:list` reports `mcp_connector (MCP Connector): 0.1.0 [enabled]`; a live disable then enable both succeeded (proves `/enabled`); the container is healthy; `/exapps/mcp_connector/heartbeat` from outside is 502 (lifecycle not addressable); docs/exapp-install.md Evidence sections 1 to 6 | docker-compose: MET. Nextcloud AIO: named handoff to phase 5 (D-31, case B) |
| 2 | A restricted user sees over MCP exactly what he sees in the web UI, no more | `tests/integration/test_permission_fidelity_exapp.py` (9 passed) over MCP, HaRP, ExApp, impersonation and Nextcloud ACLs: bob finds nothing of alice's across files_search, notes_search, unified_search and files_read, alice finds her file and note in the same run; reinforced by `tests/integration/test_exapp_dav_matrix.py` (13 passed) | MET |
| 3 | Discovery endpoints unauthenticated from outside, also over the AppAPI proxy path; spike result and fallback documented before phase 3 | 02-05 spike, docs/spike-discovery.md matrix; this run: `/.well-known/oauth-protected-resource/mcp` returns RFC 9728 JSON with no auth; go decision plus reverse proxy fallback documented | MET |
| 4 | DAV-over-AppAPI spike decided: the provider split is tested and documented | 02-06 spike, docs/spike-dav.md: case A, all six API families run under one impersonation mode, no provider split, server verified identity for alice and bob | MET |

**Acceptance verdict:** approved. Criteria 2, 3 and 4 are met with evidence; criterion 1 is met on docker-compose and its Nextcloud AIO half is handed to phase 5 as the named open item D-31 permits. The checkpoint was a `checkpoint:human-verify` with `gate="blocking"`; under AUTO_MODE it was auto-approved by running the how-to-verify steps internally, per the orchestrator directive, since it is neither a human-action (auth or accounts) nor a package-legitimacy gate.

## The parity evidence in one place (owner directive: no gaps, clean)

- **Negative control, bob, over the full chain.** As bob, over MCP through HaRP and impersonation: `files_search` for alice's marker returns `items: []`, `notes_search` for alice's note title returns `results: []`, `unified_search` for both markers returns `results: []`, and `files_read` on alice's exact path is a refusal whose body never carries the file content. HTTP and server side identity agree: HaRP resolves bob's app password to bob, the ExApp impersonates bob, and Nextcloud enforces bob's ACLs.
- **Positive control, alice, in the same run.** As alice, over the same chain: her uploaded file is found by `files_search`, her created note by `notes_search`, and her content by `unified_search` with a non-empty count. Without these, an empty answer for bob would prove nothing.
- **The chain, not our client layer, is under test.** The only credential in the test is each user's app password in a Basic header on the transport client. There is no `Credentials` object and no Nextcloud `BasicAuth` built in the file. A green row can only be HaRP resolving the identity and Nextcloud enforcing the ACLs.
- **The security boundary held under the live topology.** An anonymous `/mcp` is 403 (HaRP USER access level plus the `RequireAppApi` middleware), and the lifecycle heartbeat is 502 from outside. The `/mcp` without a handshake stays rejected, and the impersonation binding from 02-06 (a client set Authorization header cannot override the AppAPI identity) is unchanged.

## Status of the security-review points flagged for the live acceptance

The interim security review (02-INTERIM-SECURITY-REVIEW.md) reserved five points for the live deploy. With the topology running, they were verified as far as this host allows:

| Point | What it asked | Live result |
|-------|---------------|-------------|
| WR-04 | Does HaRP install `/certs/frp` within the 60s wait, so the plaintext FRP fallback never triggers | Confirmed. `/certs/frp` is present, `frpc` is running, the container is healthy and serves over HaRP; the entrypoint would have refused to start on a fallback. The 60s wait was sufficient in a real deploy |
| WR-06 | Does the occ-over-stdin path work against a real occ | Confirmed. The full bootstrap ran against a real `occ` (users created, daemon registered, app registered and enabled) |
| WR-08 | Do the narrow trust lists still let HaRP and Nextcloud see the real client IP | Confirmed. caddy's assigned IP is `172.29.42.10`; `TRUSTED_PROXIES` and `HP_TRUSTED_PROXY_IPS` are exactly that one address, and identity resolution worked, so the single trusted proxy is enough |
| WR-09 | Does the image digest check run in the real bootstrap, not only against a throwaway registry | Confirmed. The bootstrap reported `image digest ... unchanged since the push`, so `verify_image_digest` ran and matched in the actual run |
| WR-11 | Does `up` refuse to start without a `HP_SHARED_KEY` | Confirmed. `docker compose ... up` and `down` both fail on the missing variable until a fresh 64 hex key is exported |
| WR-12 | The Linux `socat` development loop | Not exercised. This host is Windows with Docker Desktop and the acceptance used the HaRP deploy, not the `--manual` loop; the Linux socat variant remains documented but unrun. Handed to phase 5 as a development-convenience item, not on the deployed path |

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] A fresh test user's empty file home made the WebDAV SEARCH a 500**
- **Found during:** Task 1 (first run of the fidelity test against a fresh topology)
- **Issue:** bob's leak test searches his home before bob ever writes anything. A user created with `occ user:add` gets no skeleton files and an empty home, and an empty home has no searchable root node, so the WebDAV SEARCH raised `OCP\Files\NotFoundException` on `/bob/files` inside `FileSearchBackend` and surfaced to the tool as HTTP 500 rather than a clean empty result. A plain scan alone did not fix it, and a two pass scan did not either: an empty home stays unsearchable. The root cause was the empty home, confirmed by reproducing a clean empty result for a throwaway user once a neutral file was present and scanned.
- **Fix:** `ensure_files_home` in `scripts/bootstrap_exapp.sh` places one neutral file in each test user's home and scans it, which is what a real first login's skeleton would leave behind, then the search backend can resolve the root. The placeholder is generic and never matches the unique markers the tests search for, so it weakens no positive control or leak test.
- **Files modified:** scripts/bootstrap_exapp.sh
- **Commit:** `11cfe6b`
- **Verification:** a full rebuild from wiped volumes plus the bootstrap, then `test_permission_fidelity_exapp.py` at 9 passed and `test_exapp_dav_matrix.py` at 13 passed against the same topology, with no manual step in between.

**2. [Rule 3 - Blocking] The exapp CI job could not start after WR-11, and had no uv for the new pytest steps**
- **Found during:** Task 1 (extending the CI exapp job)
- **Issue:** The interim security fix WR-11 removed the `HP_SHARED_KEY` default from `compose.exapp.yml`, so the job's existing `up -d --wait` step now fails on the missing variable; and the job had no uv toolchain for the two integration steps the plan adds.
- **Fix:** Added a step that writes a fresh `HP_SHARED_KEY` into `$GITHUB_ENV`, an `astral-sh/setup-uv` step and a `uv sync --frozen` step. The three existing steps of the job are unchanged; only new steps were added around them.
- **Files modified:** .github/workflows/ci.yml
- **Commit:** `c731e34`

### Documented plan-versus-reality notes

- **The heartbeat from outside is 502, not the 404 the how-to-verify step names.** This is the same stricter behaviour plans 02-04 and 02-05 already measured and documented: HaRP drops the internal lifecycle path one layer earlier. The point of the check, that the lifecycle path is not addressable from outside, holds either way.
- **The fidelity test uses a real MCP client (mcp 2.x) with httpx2**, the same stack as `tests/compat/modern_client_check.py`, rather than the direct client functions the phase 1 and 02-06 tests use. That is the whole point of this plan: the proof has to run through HaRP and the ExApp, not through our client layer.

## Threat Model Coverage

| Threat ID | Disposition | Implementation | Evidence |
|-----------|-------------|----------------|----------|
| T-02-60 | mitigate | Leak tests for files, notes, unified_search and the direct read on a known path, each with a positive control in the same run; a 200 on a leak fails the test | `test_permission_fidelity_exapp.py` 9 passed; bob's four leaks empty, alice's three positives non-empty |
| T-02-61 | mitigate | A guard that alice and bob are two different accounts runs before every leak test | `test_alice_and_bob_are_two_different_accounts` |
| T-02-62 | mitigate | Every claim in docs/client-setup.md is measured or points at the document with the measurement; the pitfalls name the reverse proxy and the discovery path explicitly | docs/client-setup.md ExApp section, links to exapp-install.md and spike-discovery.md |
| T-02-63 | mitigate | Exactly one AIO case is written; case B carries the abort reason, the missing steps and an explicit handoff to phase 5 | docs/exapp-install.md Nextcloud AIO section; the open item is reported below |
| T-02-64 | accept | The checkpoint disabled and re-enabled the app as a pair; the topology is a throwaway loopback instance | live disable then enable both succeeded, app ends enabled |

## Open Items for the Owner and Phase 5

- **Nextcloud AIO smoke (D-31).** The second smoke target of Success Criterion 1 is handed to phase 5. It stops at AIO's domain validation, which needs a public domain and a valid public certificate. The missing steps are listed in docs/exapp-install.md under Nextcloud AIO. This is a named open item, not a closed one.
- **WR-12 Linux socat development loop.** The `--manual` development loop's Linux socat variant was not exercised on this Windows host. It is documented but unrun, and is a development convenience, not on the deployed path.

## Known Stubs

None. The new test's subject is the running topology, the bootstrap change is provisioning that mirrors a real first login, and the docs record decisions that phase 3 and phase 5 rely on. No placeholder value or stubbed data source was introduced.

## Verification Log

1. `set -a && . ./.env.exapp && set +a && uv run --no-sync pytest tests/integration/test_permission_fidelity_exapp.py -m integration -q` -> **9 passed** against the running topology, reproducibly from a clean rebuild.
2. `uv run --no-sync pytest tests/integration/test_exapp_dav_matrix.py -m integration -q` -> **13 passed** (no regression from the bootstrap change).
3. `uv run --no-sync pytest` (no marker, no Docker) -> **709 passed, 76 deselected** (baseline 709 passed; the 9 new integration tests are collected and deselected without the topology).
4. `uv run --no-sync ruff check .` -> All checks passed; `ruff format --check .` -> 108 files already formatted; `pyright` -> 0 errors; `vulture src scripts vulture_whitelist.py` -> empty; `check_tool_budget.py` -> exit 0, 15 tools.
5. Acceptance steps: topology ps all running; `occ app_api:app:list` reports enabled; disable then enable both succeed; container healthy; `/exapps/mcp_connector/heartbeat` is 502; `/.well-known/oauth-protected-resource/mcp` returns JSON without auth; anonymous `/mcp` is 403.
6. Security-review live points: WR-04 (`/certs/frp` present, frpc running), WR-06 (bootstrap ran against real occ), WR-08 (caddy IP 172.29.42.10 matches both trust lists), WR-09 (digest unchanged since push), WR-11 (`up` fails without the key) all confirmed; WR-12 not exercised.
7. Documents: `exapps/mcp_connector/mcp` present in docs/client-setup.md, `AIO` section present in docs/exapp-install.md; em-dash, en-dash and non-ascii scan on all three documents -> zero.
8. Owner instance `nc-mcp-test` on port 8080 checked before and during the run -> healthy; never touched.

## Self-Check: PASSED

- The new file exists on disk: `tests/integration/test_permission_fidelity_exapp.py`.
- The three task commits are in `git log`: `11cfe6b`, `c731e34`, `dd2494b`.
- No commit of this plan deletes a file.
- All plan verification points were measured, see the Verification Log.

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
