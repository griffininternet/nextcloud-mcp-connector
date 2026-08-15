---
phase: 03-oauth-2-1
plan: 01
subsystem: auth
tags: [oauth2.1, rfc9728, rfc8414, rfc9207, mcp-sdk, starlette, appapi, harp, discovery]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "the AppAPI transport boundary, the spike discovery routes, the manifest with its route gate, and the accepted risk AR-02-06"
  - phase: 01-server-kern
    provides: "config.public_url, the four credential modes and the standalone HTTP mode that must stay unchanged (D-23)"
provides:
  - "oauth/metadata.py: the RFC 9728 protected resource document and the RFC 8414 authorization server document at the three paths a client can actually reach"
  - "exapp/responses.py: the one no-store JSON helper of the ExApp package"
  - "the bearer branch of exapp/middleware.py, with an optional TokenVerifier and the 401 that carries the resource_metadata pointer"
  - "appinfo/info.xml with four fully anchored PUBLIC routes, which closes AR-02-06"
  - "two reverse proxy rules that map both canonical discovery root paths onto the ExApp"
affects: [03-05 authorization endpoints, 03-06 token verifier, 03-08 staging deploy, 03-09 client measurement, 04 admin ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "discovery documents built from configuration only, never from the incoming message"
    - "one no-store helper per package instead of one constant copy per module"
    - "route factories attached by build_exapp_app alone (D-23), now including the oauth package"
    - "manifest gate as a function over the parsed tree, with a counter probe per new rule"

key-files:
  created:
    - src/mcp_connector/oauth/__init__.py
    - src/mcp_connector/oauth/metadata.py
    - src/mcp_connector/exapp/responses.py
    - tests/unit/test_oauth_metadata.py
  modified:
    - src/mcp_connector/exapp/middleware.py
    - src/mcp_connector/exapp/lifecycle.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - scripts/bootstrap_exapp.sh
    - scripts/spike_discovery.sh
    - deploy/Caddyfile
    - docs/spike-discovery.md
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_exapp_env_setup.py
    - vulture_whitelist.py

key-decisions:
  - "The issuer of the authorization server document is pinned to the configured public URL as an exact string, because AnyHttpUrl appends a trailing slash to a path less URL and RFC 8414 compares the issuer byte for byte"
  - "One tool scope named nextcloud (D-42); offline_access appears in the authorization server document only, never in the protected resource metadata and never in the WWW-Authenticate challenge"
  - "token_endpoint_auth_methods_supported carries none in addition to the two SDK defaults, because Claude.ai and ChatGPT arrive as public clients"
  - "The bearer branch is fail-closed by construction: while no token verifier is configured, every bearer is invalid, so PUBLIC /mcp stays closed"
  - "The manifest declares one fully anchored route per document instead of a well-known prefix, and the gate now fails on any well-known route without an end anchor"

patterns-established:
  - "Set equality on the field names of every served metadata document, so an SDK upgrade cannot publish a new field unreviewed"
  - "Pointer and route share one path constant (PRM_SUFFIX), so the 401 cannot point somewhere the app does not serve"
  - "Manifest routes and registered Starlette paths are compared as sets, not as a subset"

requirements-completed: []  # AUTH-03 is carried by this plan but stays Pending, see the deviation below
requirements-advanced: [AUTH-03]

# Metrics
duration: 65 min
completed: 2026-08-15
---

# Phase 3 Plan 01: Discovery and route hardening Summary

**The OAuth discovery path is production code: /mcp answers an anonymous caller with a 401 that points at an RFC 9728 document, that document names one authorization server, and its RFC 8414 metadata is served at both reachable well-known paths, all from configuration and all with no-store.**

## Performance

- **Duration:** 65 min
- **Started:** 2026-08-15T20:32:00Z
- **Completed:** 2026-08-15T21:37:01Z
- **Tasks:** 3 (two of them TDD, five commits)
- **Files modified:** 15 (4 created, 10 modified, 1 deleted)

## Accomplishments

- `oauth/metadata.py` serves the three discovery documents below the stripped HaRP prefix: the protected resource document at `/.well-known/oauth-protected-resource/mcp` and the authorization server document at both `/.well-known/openid-configuration` and `/.well-known/oauth-authorization-server`, byte for byte identical.
- `/mcp` is `PUBLIC` in the manifest and still closed: the transport boundary now reads the AppAPI user id, and an empty one has to pass a token verifier that does not exist yet, which means every bearer is refused with the discovery 401 (fail-closed, T-03-01).
- AR-02-06 is closed: the broad `^/\.well-known/` route is gone, replaced by three fully anchored routes, and the manifest gate fails on any well-known route without an end anchor, with two counter probes proving it fires.
- The spike is fully retired: `exapp/discovery.py` and its probe route are deleted, `docs/spike-discovery.md` has no open item left that blocks phase 3, and `scripts/spike_discovery.sh` reads the 401 pointer off `/mcp` instead.
- Three copies of the `no-store` constant became one: `exapp/responses.py` is the single source for `lifecycle`, `middleware` and `oauth/metadata`.

## Task Commits

1. **Task 1: Metadata documents and the shared no-store helper** - `dc59582` (test, RED), `b51f96e` (feat, GREEN)
2. **Task 2: /mcp on PUBLIC, bearer boundary, four anchored routes** - `14ca945` (test, RED), `7b2d91b` (feat, GREEN)
3. **Task 3: Reverse proxy rules and the closed spike items** - `d13b89a` (feat)

## Files Created/Modified

- `src/mcp_connector/oauth/__init__.py` - package docstring, no re-exports and no import side effects
- `src/mcp_connector/oauth/metadata.py` - the route factory for the three documents, plus the path and scope constants the boundary imports
- `src/mcp_connector/exapp/responses.py` - `NO_STORE` and `json_response`, the merge order of the IN-06 fix included
- `src/mcp_connector/exapp/middleware.py` - second branch of the boundary: empty user id leads into the bearer check, 401 with the challenge
- `src/mcp_connector/exapp/lifecycle.py` - uses the shared helper, own copies removed
- `src/mcp_connector/entry_exapp.py` - attaches `metadata_routes` instead of `discovery_routes`
- `src/mcp_connector/exapp/discovery.py` - deleted (spike artifact, replaced not extended)
- `appinfo/info.xml` - four routes, all PUBLIC, every well-known pattern anchored at both ends, comment block extended with the reasoning
- `scripts/bootstrap_exapp.sh` - the json-info payload carries the same four routes with numeric access level 0
- `scripts/spike_discovery.sh` - measures the two authorization server documents and takes the pointer off `/mcp`
- `deploy/Caddyfile` - two exact path rewrites for the canonical RFC 9728 and RFC 8414 root paths, before the `/exapps/*` block
- `docs/spike-discovery.md` - both open items closed with a reference to this plan, the probe limitation resolved, new subsection with the three discovery ways and copyable Caddy and nginx snippets
- `tests/unit/test_oauth_metadata.py` - the rewritten spike test file, 25 checks
- `tests/unit/test_exapp_entry.py` - the bearer branch, the token echo test and a stub verifier for both outcomes
- `tests/unit/test_exapp_env_setup.py` - manifest gate for four anchored routes, two counter probes, set equality against the registered paths
- `vulture_whitelist.py` - two SDK model fields that are written and serialised but never read back

## Decisions Made

- **Issuer as an exact string.** `AnyHttpUrl` normalises `http://127.0.0.1:8765` to `http://127.0.0.1:8765/`. RFC 8414 compares the issuer byte for byte against the value the client built its discovery URL from, so a connector on its own host would have advertised an issuer no client accepts. The document is dumped from the SDK model and the issuer is then set to the configured value; every endpoint is built with the slash stripped anyway. A regression test covers the fallback URL, which is the case where it bites.
- **`ProtectedResourceMetadata.model_validate` with plain strings** instead of the constructor with `AnyHttpUrl` objects, for the same reason: the model preserves an empty URL path, an `AnyHttpUrl` built outside it does not.
- **`dcr_enabled` as a keyword parameter with default `True`.** Plan 03-05 hands the registry policy in; the default keeps this plan free of a policy it does not have yet and matches D-35.
- **The verifier stays `None` in this plan.** That is not a gap but the strictest state of the new branch, and the plan required the manifest change and the check in one commit (pitfall 6).
- **Two SDK model fields on the vulture whitelist** rather than patching the dumped dict: assigning them on the model keeps the field names checked by pydantic and pyright.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `scripts/spike_discovery.sh` still measured the deleted probe route**

- **Found during:** Task 1 (deleting the spike module)
- **Issue:** The plan's own acceptance criterion forbids any reference to the probe path outside `docs/spike-discovery.md`, and the script did not only mention it: its second hard expectation read the `WWW-Authenticate` header off that route, so the script would have failed against a deployed container.
- **Fix:** The two probe rows were replaced by the two authorization server documents, the hard expectation now reads the pointer off the unauthenticated `/mcp` row, and the comments name why (the route is PUBLIC since this plan).
- **Files modified:** `scripts/spike_discovery.sh`
- **Verification:** `grep -rn "mcp-discovery-probe" src tests appinfo scripts docs | grep -v docs/spike-discovery.md` is empty; the file keeps LF endings and passes the CRLF guard of `test_exapp_env_setup.py`.
- **Committed in:** `b51f96e` (Task 1 commit)

**2. [Rule 2 - Missing critical] Test coverage for the new verifier parameter**

- **Found during:** Task 2 (bearer boundary)
- **Issue:** The plan wires the verifier parameter but leaves it `None`, so the branch that hands a token to a verifier and the branch that accepts one would have shipped untested, against the owner directive that abuse and non happy paths are acceptance criteria.
- **Fix:** A `StubVerifier` implementing the one method of the SDK `TokenVerifier` protocol, plus three tests: a verified token reaches the route, a rejected token stops at the boundary, and a resolved Nextcloud user is never asked for a bearer at all.
- **Files modified:** `tests/unit/test_exapp_entry.py`
- **Verification:** `uv run --no-sync pytest tests/unit/test_exapp_entry.py -q` green, and the third test asserts the verifier saw nothing on the AUTH-01 path.
- **Committed in:** `14ca945` (Task 2 RED commit)

**3. [Rule 2 - Missing critical] A bootstrap guard for the four routes**

- **Found during:** Task 2 (manifest)
- **Issue:** The json-info registration overrides the manifest, so a route that only exists in `appinfo/info.xml` is not registered on the test instance. The plan asked for the payload change but for no guard against the two drifting apart again.
- **Fix:** `test_the_bootstrap_registration_declares_the_same_four_routes` checks the numeric access levels and every declared well-known path against the payload.
- **Files modified:** `tests/unit/test_exapp_env_setup.py`
- **Verification:** The expanded payload was parsed as JSON once by hand, which is how the doubled backslash escaping was confirmed to reach AppAPI as `^/\.well-known/...$`.
- **Committed in:** `14ca945` (Task 2 RED commit)

**4. [Rule 1 - Bug] AUTH-03 was not marked complete in REQUIREMENTS.md**

- **Found during:** Close out (state update)
- **Issue:** The plan frontmatter carries `requirements: [AUTH-03]`, and the close out step marks every listed requirement complete. AUTH-03 covers the whole OAuth 2.1 connect (protected resource metadata, dynamic client registration, PKCE S256, token revocation); this plan delivers the discovery half only, and the plan's own success criterion says exactly that. A checked box would have claimed DCR, PKCE and revocation exist.
- **Fix:** The automatic completion was reverted; AUTH-03 stays `Pending` in the traceability table and gets its check mark from the plan that closes the last part of it (03-07). The summary frontmatter records the requirement as advanced, not completed.
- **Files modified:** `.planning/REQUIREMENTS.md` (reverted to its previous state)
- **Verification:** `git diff .planning/REQUIREMENTS.md` is empty; AUTH-03 reads `Pending` for phase 3.
- **Committed in:** not committed, the file is unchanged on purpose

---

**Total deviations:** 4 auto-fixed (1 blocking, 2 missing critical, 1 bug)
**Impact on plan:** No scope creep. One was forced by an acceptance criterion of the plan itself, two close test gaps in code this plan introduced, and one keeps a requirement from being reported as delivered before it is.

## Issues Encountered

- **TDD gates versus the commit gate policy.** The two RED commits (`dc59582`, `14ca945`) contain failing tests by construction, so `pytest` and, for the first of them, `pyright` cannot be green at that commit; every other gate was run and passed. Both GREEN commits and every commit after them pass all six gates. This is the documented tension between the RED phase and "all gates before every commit", not a skipped gate.
- **`test_initialize_with_a_valid_handshake_is_served` changed meaning.** The empty user id used to pass the boundary on purpose (T-02-12, app context) and is now the anonymous case that gets the 401. The parametrised test was split rather than deleted, and the T-02-12 reasoning is recorded in the new test's docstring: refusing data access for the app context still belongs to the credential layer, but reaching MCP code no longer does.
- **A heredoc in the tooling collapsed backslash line continuations**, which silently changed shell snippets during editing. Both shell files were patched through Python scripts reading and writing bytes instead, and both were verified to keep LF endings.

## User Setup Required

None - no external service configuration required. The two reverse proxy rules in `deploy/Caddyfile` are optional for administrators and documented in `docs/spike-discovery.md`; the primary discovery way needs no configuration at all.

## Verification Evidence

- `uv run --no-sync pytest -q`: 767 passed (no Docker, no network).
- Gates on the final tree, each run on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest -q` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- The registered well-known paths of `build_exapp_app` are exactly `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource/mcp` and `/.well-known/openid-configuration`; `entry_http.build_app` registers none.
- The manifest declares four routes, zero of them `USER`, all three well-known patterns end with `$`.
- Live in process, with `NC_MCP_PUBLIC_URL=https://cloud.example.com/exapps/mcp_connector`: a POST to `/mcp` with a valid AppAPI header and an empty user answers `401`, empty body, `cache-control: no-store` and
  `WWW-Authenticate: Bearer error="invalid_token", error_description="Authentication required", scope="nextcloud", resource_metadata="https://cloud.example.com/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"`.
  Following that pointer yields `{"resource": "https://cloud.example.com/exapps/mcp_connector/mcp", "authorization_servers": ["https://cloud.example.com/exapps/mcp_connector"], "scopes_supported": ["nextcloud"], "bearer_methods_supported": ["header"], "resource_name": "Nextcloud MCP Connector"}`, and both authorization server paths answer the same document with `issuer` equal to the public URL, `code_challenge_methods_supported: ["S256"]`, `none` among the token endpoint auth methods and `authorization_response_iss_parameter_supported: true`.

## Known Stubs

- The four endpoints named in the authorization server document (`/authorize`, `/token`, `/register`, `/revoke`) do not exist yet; plan 03-05 builds them. This is intentional and spec correct: a discovery document describes addresses, not their implementation state, and a client reads it before it calls any of them.
- `RequireAppApi` takes a token verifier and is built with `None`. Plan 03-06 hands in the real one. Until then the parameter is exercised by tests only, and the production behaviour is the fail-closed 401.

## Next Phase Readiness

- Ready for 03-02 and the rest of wave 1: the metadata module, the shared response helper and the bearer branch are the seams the later plans plug into.
- Plan 03-05 needs `dcr_enabled` from the registry policy; plan 03-06 needs to pass its verifier into `RequireAppApi` at the one place in `entry_exapp.build_exapp_app`.
- Plan 03-09 owns the one open question left here: whether Claude.ai and ChatGPT walk the path appended OpenID way on their own, or need the reverse proxy rules.
- No blockers. The live proof over HaRP belongs to plan 03-08, and nothing in this plan required a running Nextcloud.

---
*Phase: 03-oauth-2-1*
*Completed: 2026-08-15*

## Self-Check: PASSED

All created files exist on disk (`oauth/__init__.py`, `oauth/metadata.py`, `exapp/responses.py`, `tests/unit/test_oauth_metadata.py`), all five task commits are in the history (`dc59582`, `b51f96e`, `14ca945`, `7b2d91b`, `d13b89a`), every acceptance criterion of the three tasks was executed as a command and passed, and the plan level verification (`pytest -q` green without Docker, three registered well-known paths, four anchored manifest routes, the 401 with the pointer, all six gates) was re-run on the final tree.
