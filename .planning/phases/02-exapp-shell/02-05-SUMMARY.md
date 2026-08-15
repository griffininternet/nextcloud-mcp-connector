---
phase: 02-exapp-shell
plan: 05
subsystem: auth
tags: [discovery, rfc-9728, oauth, harp, appapi, spike, well-known, streamable-http]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "Running ExApp behind HaRP with the PUBLIC .well-known route and the HaRP daemon topology (02-04)"
  - phase: 02-exapp-shell
    provides: "build_exapp_app factory pattern and the RequireAppApi boundary in front of /mcp (02-01, interim security review)"
provides:
  - "src/mcp_connector/exapp/discovery.py: the RFC 9728 metadata route and a 401 probe with a resource_metadata pointer, both public by contract and configuration only"
  - "scripts/spike_discovery.sh: repeatable path x auth x status matrix over the HaRP path, the PHP proxy path and the canonical root path, with three hard expectations"
  - "docs/spike-discovery.md: the go decision, the measurement matrix, the 404 finding for the canonical path, the streaming proof and the phase 3 topology with a copyable Caddy and nginx fallback"
  - "tests/unit/test_exapp_discovery.py: eleven checks including the leak guards T-02-40/T-02-41 and the wiring guard that keeps phase 1 modes free of a .well-known route"
affects: [03 OAuth topology and Protected Resource Metadata, 02-07 AIO acceptance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The discovery probe is a factory of routes attached by build_exapp_app alone, never on the shared server object (D-23), the same rule the lifecycle routes follow"
    - "A spike route is marked as a spike in its own module docstring and its removal is an explicit open item in the result document (T-02-44), so a measurement artifact cannot silently become production"
    - "The measurement is a checked-in shell script with hard and soft expectations, so the matrix in the doc is reproducible output, not a claim"

key-files:
  created:
    - src/mcp_connector/exapp/discovery.py
    - tests/unit/test_exapp_discovery.py
    - scripts/spike_discovery.sh
    - docs/spike-discovery.md
  modified:
    - src/mcp_connector/entry_exapp.py

key-decisions:
  - "AUTH-06 is a go: the RFC 9728 metadata is reachable unauthenticated from outside over BOTH the HaRP path and the PHP proxy path (200 with JSON), and the WWW-Authenticate resource_metadata pointer survives both proxies unchanged"
  - "The canonical RFC 9728 root path is 404, answered by Nextcloud, not the ExApp; phase 3 relies on the resource_metadata pointer (SEP-985 priority 1) and offers a reverse proxy rule as fallback"
  - "The discovery route leaks nothing: the body carries only the configured public URL and the method list, no secret, no internal host, no ex-app header; proven by a live fetch and by a unit leak guard"
  - "The deployed container has no NC_MCP_PUBLIC_URL, so the measured resource is the documented default host; acceptable for a reachability spike, phase 3 wires the real value from AuthSettings"
  - "An unknown bearer over HaRP on the USER route is answered 403 (a clean 4xx, not a 5xx), which is what phase 3 needs so a PUBLIC /mcp can forward to the own token verifier (Open Question 4)"

requirements-completed: [AUTH-06]

# Metrics
duration: 14 min
completed: 2026-08-15
---

# Phase 2 Plan 05: Discovery Spike (AUTH-06) Summary

**The discovery spike is a go: an unauthenticated client reaches the RFC 9728 metadata of this ExApp from the outside over both the HaRP path and the PHP proxy path, the WWW-Authenticate resource_metadata pointer passes through both proxies unchanged, the canonical root path is 404 and belongs to Nextcloud, and a real MCP session with the SDK client streams 15 tools over HaRP end to end.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-15T11:29:36Z
- **Completed:** 2026-08-15T11:43:38Z
- **Tasks:** 3
- **Files modified:** 5 (4 new, 1 changed)

## Accomplishments

- `src/mcp_connector/exapp/discovery.py`: a `discovery_routes` factory with two routes below `/.well-known/`, both public by contract and both covered by the single PUBLIC route already in `appinfo/info.xml`, so the spike needed no manifest change. The metadata route answers 200 with an RFC 9728 document built from `config.public_url` and never from the request; the probe answers 401 with `WWW-Authenticate: Bearer resource_metadata="<url>"`. Both carry `Cache-Control: no-store`. The module docstring marks the routes as spike artifacts to be replaced in phase 3.
- `entry_exapp.build_exapp_app` attaches the discovery routes beside the lifecycle routes, from a factory and never on the shared server object (D-23). The standalone HTTP mode of phase 1 knows neither route, held by a test.
- `scripts/spike_discovery.sh`: eleven measured rows over the HaRP path, the PHP proxy path and the canonical root path, with a hard verification block that fails the script when the metadata over HaRP is not 200, when the probe carries no `resource_metadata` pointer, or when `/heartbeat` is served. It changes nothing on the instance.
- `docs/spike-discovery.md`: the go decision, the matrix with the Nextcloud and AppAPI versions, the 404 finding for the canonical path, the streaming proof, the phase 3 topology with a copyable Caddy and nginx fallback rule and its security assessment, the leak evidence, the unknown bearer finding and the honest limitation that the 401 comes from a purpose built probe rather than `/mcp`.
- The measurement was run against a real, freshly rebuilt HaRP topology (Nextcloud 34.0.2, AppAPI 34.0.0) with the deployed container carrying this plan's code.

## Task Commits

1. **Task 1: Metadata route and measurement probe in the ExApp** - `eb66356` (feat)
2. **Task 2: Measurement matrix over both proxy paths and the root path** - `f1f0936` (feat)
3. **Task 3: Streaming proof and docs/spike-discovery.md** - `ae1b8f0` (docs)

## The measurement matrix

| Path | Way | Auth | Status | Notes |
|------|-----|------|--------|-------|
| `/.well-known/oauth-protected-resource/mcp` | HaRP | none | 200 | json, no-store |
| `/.well-known/oauth-protected-resource/mcp` | PHP-Proxy | none | 200 | json, no-store |
| `/.well-known/mcp-discovery-probe` | HaRP | none | 401 | www-authenticate resource_metadata, no-store |
| `/.well-known/mcp-discovery-probe` | PHP-Proxy | none | 401 | www-authenticate resource_metadata, no-store |
| `/mcp` | HaRP | none | 403 | rejected by HaRP (USER) |
| `/mcp` | PHP-Proxy | none | 404 | proxy access check fails closed |
| `/mcp` | HaRP | basic:alice | 200 | text/event-stream (streaming) |
| `/mcp` | PHP-Proxy | basic:alice | 200 | text/event-stream |
| `/heartbeat` | HaRP | none | 502 | dropped by HaRP (internal path) |
| `/heartbeat` | PHP-Proxy | none | 404 | no declared route matches |
| `/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp` | root | none | 404 | answered by Nextcloud |

**Go or No-Go for phase 3: GO.** Unauthenticated discovery reaches the ExApp over both proxy paths; the phase 3 OAuth topology can rely on the `resource_metadata` pointer, with the documented reverse proxy rule as the fallback.

## Decisions Made

- **AUTH-06 is checked complete.** The plan condition was that the matrix truly proves unauthenticated access over the proxy path, not only over HaRP. Both the metadata route and the probe are reachable unauthenticated over `/apps/app_api/proxy/mcp_connector/...` as well, so the requirement is met, not pending.
- **The resource value is the default host in the live measurement.** The deployed container carries no `NC_MCP_PUBLIC_URL`, so `config.public_url` returns its documented default. The spike measures reachability and header pass through, not this field, and phase 3 builds the real PRM from `AuthSettings`. The unit test pins the value against a set `NC_MCP_PUBLIC_URL` and separately checks the default fallback.
- **The probe route, not `/mcp`, produces the measured 401.** `/mcp` is `access_level` USER in phase 2 by design, so HaRP answers before our code. Opening `/mcp` to PUBLIC belongs to phase 3 with the own token verifier. This limitation is stated in the doc (T-02-45).
- **The reverse proxy fallback opens no new attack surface.** It exposes the same public, leak free metadata document the pointer already advertises. This is assessed explicitly in the doc, as D-29 requires a fallback that is not only described but evaluated.

## Deviations from Plan

### Necessary deviation: clean rebuild of the exapp topology to measure

**1. [Rule 3 - Blocking] The preserved topology could not be brought up with the current bootstrap**
- **Found during:** Task 2 (preparing the running topology for the measurement)
- **Issue:** The plan expected `docker compose up` plus `bootstrap_exapp.sh` against the preserved volumes. The HaRP daemon registration stored in the preserved Nextcloud volume was written by plan 02-04, before the interim security review added the `require_hex64` gate (CR-02) and removed the `HP_SHARED_KEY` default (WR-11). The stored key was the old non-hex `nc-mcp-exapp-local-harp-key`, which the current `bootstrap_exapp.sh` rejects in `harp_shared_key` before it can register or deploy, and `docker compose up` now refuses to start without a `HP_SHARED_KEY` at all. The preserved volumes were therefore unusable with the code as it stands.
- **Fix:** Recreated the nc-mcp-exapp project only, with a fresh 64 hex `HP_SHARED_KEY`: `down -v` on that project, removed the orphan `nc_app_mcp_connector` container and its data volume, `up -d --wait`, then a full `bootstrap_exapp.sh` run. That rebuilt the image with this plan's discovery code, registered the app under the HaRP daemon and deployed it. `APP_SECRET` stayed the valid 64 hex value already in `.env.exapp`, so it was pinned, not regenerated.
- **Files modified:** none (topology and volumes only)
- **Verification:** `occ app_api:app:list` reported `mcp_connector (MCP Connector): 0.1.0 [enabled]`, the container came up healthy, and the metadata route answered 200 over HaRP. The owner instance `nc-mcp-test` on port 8080 was checked before and after and stayed healthy (status.php 200); no command ever touched that project.

### Auto-fixed issue while authoring the script

**2. [Rule 1 - Bug] measure() received the URL in the wrong position for the /mcp rows**
- **Found during:** Task 2 (first measurement run)
- **Issue:** `measure` takes the URL as its fourth argument; the four `/mcp` calls passed the curl options before the URL, so the fourth argument was `-X` and the real URL was shifted into the extra args. Every `/mcp` row measured `000` instead of a status.
- **Fix:** Reordered those calls to pass the URL as the fourth argument and the curl options after it, and added `--max-time 20` so a streamed `/mcp` answer cannot hold the measurement open.
- **Files modified:** scripts/spike_discovery.sh
- **Verification:** the rerun measured 403, 404, 200 and 200 for the four `/mcp` rows. Committed in `f1f0936`.

### Documented plan-versus-reality deviations

- **The `/heartbeat` hard expectation is a rejection, not a literal 404.** The plan wanted `/heartbeat` to be 404. Over the HaRP path it is 502, the same stricter behaviour plan 02-04 already measured and documented (HaRP drops the internal lifecycle paths one layer earlier). The script asserts a rejection (any non-200, non-000) on the HaRP path, and the PHP proxy row shows the expected 404. The point of the check, that the lifecycle path is never served to the outside, holds.
- **The discovery helper is local, not imported from lifecycle.py.** The plan suggested importing the response helper if one exists. `lifecycle._json` is private and does not take extra headers, and `middleware.py` already established a local `_NO_STORE` constant rather than a cross module private import. `discovery.py` follows the middleware precedent and keeps its own helper, with a comment, so the spike module can be deleted in one piece in phase 3.
- **`vulture_whitelist.py` was not touched.** The plan allowed adding to it only if vulture complained. It did not; the new names are reachable through the factory and the tests.

## Threat Model Coverage

| Threat ID | Disposition | Implementation | Evidence |
|-----------|-------------|----------------|----------|
| T-02-40 | mitigate | The metadata body carries only the public URL and the method list; no secret, no request host, no version, no configuration | `test_metadata_leaks_nothing_but_the_public_url_and_the_method_list`; live body in docs/spike-discovery.md |
| T-02-41 | mitigate | `resource` comes only from `config.public_url`; a forged Host does not change it | `test_metadata_resource_ignores_a_forged_host_header`; the module reads no request header |
| T-02-42 | mitigate | `Cache-Control: no-store` on both routes | matrix rows show `cc=no-store`; `test_both_routes_carry_no_store` |
| T-02-43 | mitigate | The PUBLIC measurement rows send no Authorization header (pitfall 6), with a comment at the measurement site | scripts/spike_discovery.sh, the comment in `measure` |
| T-02-44 | mitigate | The probe is marked as a spike artifact in its docstring, reads no data, answers with a header and an empty body, and its removal is an open item in the doc | discovery.py docstring; docs/spike-discovery.md "Open items" |
| T-02-45 | accept | `/mcp` stays USER; the 401 is measured on a dedicated probe. The reduced realism is named in the doc | docs/spike-discovery.md "Limitations" |

## Security Focus (owner directive: no gaps, clean)

- **Every threat position closed individually with evidence**, see the table above, not a blanket claim.
- **The discovery route leaks nothing.** Live body over HaRP: `{"resource":"http://127.0.0.1:8765/mcp","authorization_servers":[],"bearer_methods_supported":["header"]}`, probe body `{}`. No `APP_SECRET`, no internal Nextcloud host or path, no `EX-APP-*` header value, no HP config. A negative unit test (`test_metadata_leaks_nothing...`) enforces the exact field set and the absence of the secret, the request host, the version and the test host name.
- **The middleware boundary from the interim security fix was not weakened.** `/mcp` stays behind `RequireAppApi` and behind the HaRP USER access level: unauthenticated `/mcp` is 403 over HaRP and 404 over the PHP proxy in the matrix. Only the explicitly public discovery and well-known paths answer without a handshake. The counter check holds: `/mcp` without a handshake is still rejected.
- **The No-Go path is not the outcome, but the fallback is assessed anyway.** The reverse proxy rule exposes only the already public, leak free metadata document, so it opens no new attack surface. Stated in the doc.

## Known Stubs

The two discovery routes are deliberate spike artifacts, not stubs that block the plan goal. Their purpose is measurement, not phase 3 function, and this is intentional per the plan and T-02-44: the module docstring says so and `docs/spike-discovery.md` lists their replacement (the real Protected Resource Metadata from `AuthSettings`, and the switch of `/mcp` to PUBLIC with an own token verifier) as an explicit open item for phase 3. The plan goal, deciding AUTH-06 with evidence, is fully achieved.

## Next Phase Readiness

- **Phase 3 has its topology decision:** the `resource_metadata` pointer is the primary path, the reverse proxy rule (Caddy and nginx, in the doc) is the tested fallback, the standalone HTTP mode is the escape hatch.
- **Open for phase 3:** switch `/mcp` to `access_level` PUBLIC together with the own `TokenVerifier`, and build the real PRM from `AuthSettings` (replacing the spike probe). The unknown bearer 403 finding means a PUBLIC `/mcp` will forward unknown tokens to that verifier rather than turning them into a 401.
- **Topology after the run:** the nc-mcp-exapp project is down, both its volumes are kept. To measure again: `export HP_SHARED_KEY=$(openssl rand -hex 32)` (the stored daemon key from the previous run is gone with the wiped volume, so a fresh bootstrap is needed), `docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait`, `bash scripts/bootstrap_exapp.sh`.

## Verification Log

1. `uv run --no-sync pytest tests/unit/test_exapp_discovery.py -q` -> 11 passed.
2. `uv run --no-sync pytest` -> 709 passed, 54 deselected (baseline 698, plus 11 new).
3. `uv run --no-sync ruff check .` -> All checks passed; `ruff format --check .` -> 105 files already formatted; `pyright` -> 0 errors; `vulture` -> empty; `check_tool_budget.py` -> 10642 bytes, 15 tools, budget 12500.
4. `bash -n scripts/spike_discovery.sh` -> exit 0; `bash scripts/spike_discovery.sh` -> eleven rows, all three hard expectations PASS.
5. `uv run --no-sync python tests/compat/modern_client_check.py http://127.0.0.1:8081/exapps/mcp_connector/mcp` with alice's app password -> `tools/list returned 15 tools`, exit 0.
6. Unknown bearer over HaRP on `/mcp` -> 403 (Open Question 4).
7. NC and AppAPI versions read from the running instance: 34.0.2 and 34.0.0.
8. Line endings: `scripts/spike_discovery.sh` and `docs/spike-discovery.md` are LF only.
9. Em-dash and emoji check on `docs/spike-discovery.md` -> zero non-ASCII characters, zero em or en dashes.
10. Owner instance `nc-mcp-test` checked before and after the run -> healthy, status.php 200; never touched.

## Self-Check: PASSED

- All four new files exist on disk: `src/mcp_connector/exapp/discovery.py`, `tests/unit/test_exapp_discovery.py`, `scripts/spike_discovery.sh`, `docs/spike-discovery.md`.
- All three task commits are in `git log`: `eb66356`, `f1f0936`, `ae1b8f0`.
- No commit of this plan deletes a file (the single deletion in the diff of `eb66356` is the one replaced line in `entry_exapp.py`).
- All plan verification points were measured, see the Verification Log.

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
