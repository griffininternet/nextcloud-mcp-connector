---
phase: 03-oauth-2-1
plan: 08
subsystem: auth
tags: [oauth2.1, integration, harp, appapi, exapp, discovery, sc3, sc5, measurement, docs]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "02-07: the HaRP topology of compose.exapp.yml, scripts/bootstrap_exapp.sh and the permission fidelity chain test"
  - phase: 03-oauth-2-1
    provides: "03-01: the three discovery documents and the 401 with its pointer"
  - phase: 03-oauth-2-1
    provides: "03-02: oauth/store.py and oauth/crypto.py with the data key in the ExApp configuration"
  - phase: 03-oauth-2-1
    provides: "03-04: the browser onboarding of AUTH-02"
  - phase: 03-oauth-2-1
    provides: "03-05 and 03-06: the authorization server, the consent screen and the token verifier"
  - phase: 03-oauth-2-1
    provides: "03-07: the rotation, the revocation and the throttle"
provides:
  - "scripts/oauth_flow_check.py: the whole client half of the flow as one repeatable run, with the seven measured steps and the two success criteria"
  - "tests/integration/test_oauth_flow_exapp.py: tool call, container restart, two accounts with the leak test, revocation and reconnection, throttle boundary"
  - "docs/oauth-setup.md: topology, install, the measured evidence, six pitfalls and the production notes"
  - "appinfo/info.xml: the four deploy variables an administrator can set"
  - "the measured answer to SC 5: one Nextcloud round trip per MCP request that carries an Authorization header"
affects: [03-09 the two connectors, 04 admin ui, 05 store submission]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a live proof is a script anybody can re-run, not a session somebody remembers"
    - "a round trip count is a difference of two access log readings, never a time window"
    - "the browser half of a flow is driven from scripts/ and never from src/"

key-files:
  created:
    - scripts/oauth_flow_check.py
    - tests/integration/test_oauth_flow_exapp.py
    - docs/oauth-setup.md
  modified:
    - appinfo/info.xml
    - scripts/bootstrap_exapp.sh
    - src/mcp_connector/oauth/crypto.py
    - src/mcp_connector/nextcloud/http.py
    - tests/unit/test_oauth_crypto.py
    - tests/unit/test_credentials_http.py
    - vulture_whitelist.py
    - docs/exapp-install.md
    - docs/client-setup.md
    - README.md

key-decisions:
  - "A deploy variable reaches an ExApp container only if the manifest declares it: appinfo/info.xml now declares NC_MCP_PUBLIC_URL and the three AUTH-07 switches, because without the declaration the env option of the registration is accepted and silently dropped"
  - "The ExApp configuration is read with POST .../ex-app/config/get-values and a configKeys body, and the answer names its fields in lower case; the shape this project carried was a GET with a query parameter, for which AppAPI has no route at all"
  - "The shared HTTP client keeps no cookie jar: on a process wide client, Nextcloud's session cookie of the first user became the identity of every later request of every other user"
  - "SC 5 is one Nextcloud round trip per MCP request that carries an Authorization header, accepted or refused, and it cannot be switched off from here"
  - "The literal five minute recovery after a throttle window is measured by hand and documented, not asserted in a suite that would then sleep five minutes"

patterns-established:
  - "The client half of the flow lives once, in scripts/, and the integration test imports it by path"
  - "Every number in a document names the command that produced it and the date it was produced on"
  - "A counter measurement is part of the evidence: the reverse proxy rules are removed and put back, so the document can say what they are worth"

requirements-completed: [AUTH-02, AUTH-03, AUTH-07]

# Metrics
duration: 80 min
completed: 2026-08-16
---

# Phase 3 Plan 08: The integration proof against the running topology Summary

**The whole OAuth flow now runs through Caddy, HaRP, the ExApp container and Nextcloud and back, and getting it there found three defects that no unit test could have found: a deploy variable that never reached the container, a data key read against a route AppAPI does not have, and a shared HTTP client that turned two users into one.**

## Performance

- **Duration:** 80 min
- **Started:** 2026-08-16T03:25:00Z
- **Completed:** 2026-08-16T04:45:00Z
- **Tasks:** 3 of 3
- **Files created:** 3, modified: 10

## Accomplishments

- **The flow is measured end to end, and it is repeatable.** `scripts/oauth_flow_check.py` walks the seven steps of the plan's measurement list against a base URL it is given and prints one line per request with path, status and the headers that matter. The anonymous 401 with its `resource_metadata` pointer, the three discovery documents over both proxy paths byte for byte identical, the two canonical root paths, the registration with `201` and `no-store`, the authorization request with PKCE S256 and a resource parameter, the consent screen, the redirect with `code`, `state` and `iss`, the code exchange in **0.04 seconds**, and a tool call with the token that came out of it. The run ends by revoking what it created and deleting the one note it wrote.
- **Five integration checks that only exist at a running instance.** `tests/integration/test_oauth_flow_exapp.py` proves the four points the plan asks for plus the throttle boundary: a token from the flow serves a tool call over the chain; the same token still serves one after `docker restart` of the ExApp container; two accounts stay two accounts over four different read paths with the positive control in the same run; a revocation is a `401` whose `WWW-Authenticate` is byte for byte the one an anonymous request gets, followed by a complete reconnection; and a flood of unknown bearers throttles the token endpoint without touching a working connection.
- **SC 5 is a number now, and the number is one.** Every MCP request that carries an `Authorization` header costs exactly one Nextcloud round trip, `GET /index.php/apps/app_api/harp/user-info`, whether the bearer is accepted or refused. Six HTTP requests of one session produced six lookups; five refused ones produced five. The token verification itself costs nothing: it is one indexed lookup in the local store behind a five second cache. The counter check of the research holds: after eleven refused token requests and five refused MCP requests the test user signs in normally, because an unknown bearer produces no brute force entry in Nextcloud.
- **SC 3 is walked, station by station.** `/connect` 200, the start 200, the waiting page 200 with the user name and a 72 character credential, the second load of the same address 400 **without** the credential, and that credential accepted immediately as a Basic header on `/mcp` with `Server: uvicorn`, which is the proof that the answer came out of the container. The entry it creates carries the expected prefix: `MCP Connector: browser onboarding` under Devices and sessions.
- **The sweep of unfinished sign ins works at the instance.** Plan 03-07 built it and could only test it in process. Measured here by waiting out the twenty minute deadline and then driving ten authorization requests: `MCP Connector entries before the sweep: 25`, `after: 24`, `handed back by the sweep: [104]`. Entry 104 was the app password of a sign in that never became a connection; the running sign ins and the live connections in the same list were untouched.
- **The revocation really removes the Nextcloud credential.** Measured by ids, not by trust: the connection created one new entry under Devices and sessions, `POST /revoke` answered 200, and that exact entry was gone afterwards.
- **`docs/oauth-setup.md` is an installation manual, not a report.** Topology with the way of one request through nine steps, the three discovery paths and who owns each of them, the one variable an installation has to set, the three switches with their defaults, both reverse proxy rules as copyable Caddy and nginx blocks with an honest note on when they are needed, the whole evidence with commands and dates, the six pitfalls in the words of an operator, and the production notes about the data key, the volume, the allowlist, the throttle and the immediate revocation.

## Task Commits

1. **Task 1: the full flow against the running topology** - `edb2571` (feat)
2. **Task 2: SC 5 measured and SC 3 walked** - `ac4530f` (feat)
3. **Task 3: docs/oauth-setup.md and the documents around it** - `cf5c7ad` (docs)

## Files Created/Modified

- `scripts/oauth_flow_check.py` - the seven steps, the two measurements, the headless Nextcloud sign in for the test topology, and the cleanup. Also the module the integration test imports its client half from.
- `tests/integration/test_oauth_flow_exapp.py` - five checks, marker `integration`, skip with the missing variable named, docstring with the run instructions.
- `docs/oauth-setup.md` - the new document, in the shape of `exapp-install.md`.
- `appinfo/info.xml` - `environment-variables` with `NC_MCP_PUBLIC_URL` and the three AUTH-07 switches.
- `scripts/bootstrap_exapp.sh` - `PUBLIC_URL`, the already normalised `environment-variables` in the registration payload, and the two account passwords in `.env.exapp` for the headless sign in.
- `src/mcp_connector/oauth/crypto.py` - `CONFIG_READ_SUFFIX` and `CONFIG_READ_FIELD` replace `CONFIG_READ_PARAM`, the read is a POST, and `_config_value` accepts the lower case field names AppAPI answers with.
- `src/mcp_connector/nextcloud/http.py` - `NoCookieJar`, and the shared client uses it.
- `tests/unit/test_oauth_crypto.py` - the read is mocked as its own POST route, the stored shape is the measured one, and a new check drives all four answer shapes.
- `tests/unit/test_credentials_http.py` - two checks on the cookie jar that refuses to be one.
- `vulture_whitelist.py` - the two jar methods urllib calls and this repository does not.
- `docs/exapp-install.md` - the eleven routes of this phase and a pointer to the new document.
- `docs/client-setup.md` - the OAuth section: the exact URL, what happens after it, and what to do when the client cannot find the authorization server.
- `README.md` - a paragraph on OAuth 2.1 and the four deploy variables in the environment table.

## Decisions Made

Beyond the frontmatter list, three worth naming here:

- **The headless sign in lives in `scripts/` and is named as a shortcut.** Two steps of the flow are a person in a browser: the Nextcloud sign in and the "Approve access" button. `sign_in` performs the first one exactly as a browser would, with the account password of a throwaway user, and the module docstring says in the first paragraph that this exists for the test topology and nowhere else. The gate over `src/` from plan 03-07 still holds: no product module contains a login automation and none ever sees a user password.
- **The measurement counts requests, not seconds.** The plan is explicit that the round trip count is the statement, because it multiplies with the number of users while a response time does not. The implementation reads the access log before and after and takes the difference, because `docker logs --since` resolves to whole seconds and would inherit or lose the requests of the second it starts in.
- **The throttle measurement runs last.** It blocks the token path of this source for five minutes, so everything that needs `/token` has to have happened by then. That ordering is in the code with its reason, and the document says a second run of the script has to wait the window out.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The public URL never reached the container, so nothing about OAuth was reachable**

- **Found during:** Task 1, at the very first measurement
- **Issue:** With the topology rebuilt on the phase 3 image, the 401 of `/mcp` pointed at `http://127.0.0.1:8765/...`, the issuer of the metadata document was `http://127.0.0.1:8765` and the resource of the protected resource document was `http://127.0.0.1:8765/mcp`. `NC_MCP_PUBLIC_URL` was read by the code, documented in the README and used in every unit test, and it was set nowhere in the deployment. Setting it with the `env` option of `occ app_api:app:register` changed nothing: the container environment did not carry it.
- **Root cause, measured in the running AppAPI 34.0.0:** `ExAppService::getAppInfo` only turns `external-app/environment-variables` into the map the deploy daemon reads on the info.xml path, and it only lets the registration option override a variable the manifest declares. On the json-info path it hands the decoded object through untouched. So a variable that is not declared is accepted on the command line and dropped without a word.
- **Fix:** `appinfo/info.xml` declares four variables, `NC_MCP_PUBLIC_URL` and the three switches of AUTH-07, which is also what makes them settable in the AppAPI administration interface. `scripts/bootstrap_exapp.sh` carries the already normalised shape in its json-info payload and writes the same value into `.env.exapp`.
- **Verification:** `docker inspect nc_app_mcp_connector` shows `NC_MCP_PUBLIC_URL=http://127.0.0.1:8081/exapps/mcp_connector`; the 401 and all three documents name that address.
- **Committed in:** `edb2571`

**2. [Rule 1 - Bug] The data key could never be read, because the read used a route AppAPI does not have**

- **Found during:** Task 1, at the first `POST /register`, which answered 500
- **Issue:** `crypto._read_key` asked `GET /ocs/v2.php/apps/app_api/api/v1/ex-app/config?configKeys[]=oauth_data_key`. AppAPI declares three verbs on that resource and none of them is a `GET`: the read is `POST /ex-app/config/get-values` with a JSON body `{"configKeys": [...]}`. The unmatched route never reaches the AppAPI authentication, so Nextcloud answered `401` with "Current user is not logged in", the store could not open, and every authorization endpoint answered 500. This is exactly the open item plan 03-02 handed to this one, and the answer is worse than expected: not a wrong parameter name but a wrong verb and a wrong path.
- **Second half of the same defect:** the answer names its fields **lower case**, `configkey` and `configvalue`, because they are the column names of `ex_apps_config` serialised straight out of the entity. The parser accepted `configKey`/`configValue` only and would have refused the answer as unreadable even with the right route.
- **Fix:** `CONFIG_READ_SUFFIX = "/get-values"` and `CONFIG_READ_FIELD = "configKeys"` replace `CONFIG_READ_PARAM`, the read is a POST with that body, and `_config_value` accepts the measured lower case shape next to the camel case one and the mapping.
- **Verification:** measured against the running AppAPI before and after (`READ empty: 200 ... data: []`, `WRITE: 200`, `READ back: 200` with the value); `tests/unit/test_oauth_crypto.py` mocks the read as its own POST route and drives all four answer shapes; the restart check of the integration suite is the live proof, because a cold process has to fetch that key again before it can decrypt anything.
- **Committed in:** `edb2571`

**3. [Rule 1 - Bug, security] The shared HTTP client made two users one**

- **Found during:** Task 1, in the two account check
- **Issue:** `files_search` for the second user answered 500 with "Search is only supported on directories" for `/files/bob`, while the Nextcloud log recorded the request under the user **alice**. `nextcloud/http.shared_client` is one `httpx.AsyncClient` per event loop and therefore per process, and an httpx client keeps cookies by default. Nextcloud answers *every* request with `oc<instanceid>` and `oc_sessionPassphrase`, including a WebDAV request that authenticated with an app password. The first user's session cookie was stored in that client and sent with every later request of every other user, and Nextcloud resolved the session before the credentials of the request.
- **Why it never showed before:** the AppAPI mode carries the identity in a header the proxy validates on every single request, so a stale session cookie changes nothing there. It only became visible when a token became the identity (plan 03-06) and the credential became an app password in a Basic header.
- **Impact:** this is a permission fidelity defect of the class AUTH-05 exists against. Here it surfaced as a 500 rather than a leak, because the search scope carries the user id and did not match the session; on a path where the scope is not part of the request it would have been one user reading another user's data.
- **Fix:** `NoCookieJar`, a `http.cookiejar.CookieJar` whose `set_cookie` and `add_cookie_header` do nothing, handed to the shared client. The guard sits in the jar and not in an `httpx.Cookies` subclass, because the client rebuilds that wrapper and a subclass of it would be dropped silently.
- **Verification:** two unit checks on both directions of the jar, and the integration check `test_two_tokens_stay_two_accounts_over_the_whole_chain`, which fails without the fix and passes with it. `test_permission_fidelity_exapp.py` stays green as well.
- **Committed in:** `edb2571`

**4. [Rule 3 - Blocking] The headless sign in needs the account passwords, and `.env.exapp` did not carry them**

- **Found during:** Task 1
- **Issue:** The plan asks the check to confirm the Nextcloud grant without a browser, over the Login Flow v2, with the credentials of the test user from the environment. `.env.exapp` carried app passwords only, and an app password cannot complete a login flow: `apptokenRedirect` accepts one but then hands that same credential back, which would have made the "Devices and sessions" proof meaningless.
- **Fix:** `scripts/bootstrap_exapp.sh` writes `NC_MCP_TEST_PASSWORD` and `NC_MCP_TEST_PASSWORD2` into the git ignored `.env.exapp`. Both values are the throwaway defaults the script itself sets, so nothing new is exposed.
- **Verification:** the sign in produces a fresh app password named `MCP Connector: <client>` for the right user, verified for both accounts.
- **Committed in:** `edb2571`

**5. [Rule 1 - Deviation from the plan text] The literal five minute recovery is measured by hand, not by the suite**

- **Found during:** Task 2
- **Issue:** The plan asks for an integration case in which a valid token works again "after the stated waiting time". The stated time is 300 seconds, and a suite that sleeps five minutes is a suite nobody runs.
- **Fix:** The check asserts what the window promises and what makes it safe: `429` with a positive `Retry-After` and `no-store`, and a working connection that is completely unaffected by the flood, because the throttle never sits on the MCP route. The window itself and its number are recorded in `docs/oauth-setup.md`, and the test docstring says why the wait is not in the suite.
- **Committed in:** `edb2571`

---

**Total deviations:** 5 auto-fixed (3 bugs, of which one is a security defect and two are blockers of the plan's own first measurement, 1 blocking environment gap, 1 deviation from the plan text)
**Impact on plan:** No scope creep and no new dependency. Three of the five are defects that would have surfaced in plan 03-09 in front of Claude.ai and ChatGPT, which is the expensive place the plan named in its own purpose.

## Issues Encountered

- **The topology had to be rebuilt three times.** Every one of the three defects above is in the container image, so each fix meant unregistering the app, removing the stale container, rebuilding the image and registering again. The order in the plan's environment section is right and the bootstrap is idempotent; what is not obvious is that **every** `docker compose` call against `compose.exapp.yml` needs `HP_SHARED_KEY` in its environment, including the `occ` wrapper, and the first bootstrap run died at `wait_for_install` for exactly that reason.
- **The first `docker compose exec` calls take tens of seconds on this host.** `docker exec -u www-data nc-mcp-exapp-nc php occ ...` answers in under a second and is the form to use for repeated queries.
- **A raw `tools/list` over HTTP is a 400, not a 401 or a 200.** The transport wants a session id for anything but `initialize`, so the raw checks that read a status and a header send `initialize`; a `tools/list` would hide the difference between an accepted and a refused bearer behind a protocol error.

## Known Stubs

None.

## Threat Flags

None. This plan added no route and no public surface. `appinfo/info.xml` gained an
`environment-variables` block, which declares configuration and no endpoint; the route list
is unchanged and the manifest gate of `tests/unit/test_exapp_env_setup.py` is green.

## Verification Evidence

- Plan level verification, point by point:
  1. `uv run --no-sync python scripts/oauth_flow_check.py http://127.0.0.1:8081/exapps/mcp_connector` ends with exit code 0 and prints the seven steps; `--measure` adds the SC 5 and SC 3 blocks and also ends 0.
  2. `uv run --no-sync pytest -m integration tests/integration/test_oauth_flow_exapp.py -q`: **5 passed**.
  3. `uv run --no-sync pytest -q` without Docker: **1282 passed, 81 deselected** (from 1274 passed, 76 deselected).
  4. `docs/oauth-setup.md` carries all six sections, both proxy rules for Caddy and nginx, and only numbers from the runs of this plan.
  5. Secret gate over the four documents: no 64 character hex string, no bearer value, no password. The one `Bearer` match is the placeholder `Bearer a-long-random...` that `client-setup.md` already carried.
  6. All six gates of D-32 clean on the final tree, each on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest -q` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- Acceptance criteria of the three tasks, executed:
  - the 401 carries `WWW-Authenticate` with `resource_metadata` and `Cache-Control: no-store` (step 1 line);
  - the registration is `201` with `Cache-Control: no-store` (step 4 line, and the script fails otherwise);
  - the redirect carries `code`, `state` and `iss`, all three checked against the values sent (step 5 line);
  - the code exchange took `0.04` seconds, well under the five second limit the script enforces;
  - the restart, the two account and the revocation proofs are three of the five integration checks;
  - the sweep of unfinished sign ins is measured against the instance and recorded in the Evidence section of the document;
  - the measurement prints the three SC 5 numbers, the counter check answers 200, and the onboarding protocol carries the status of every station;
  - `docs/oauth-setup.md` passes the section check of the plan verbatim.
- The topology it ran against: Nextcloud **34.0.2**, AppAPI **34.0.0**, image `ghcr.io/nextcloud/nextcloud-appapi-harp:release`, app version 0.1.0, deployed from the loopback registry.

## Requirement Status

**AUTH-02, AUTH-03 and AUTH-07 are complete.**

- **AUTH-02** is walked live, station by station, with the credential shown once and used once, and the entry under Devices and sessions carrying the expected prefix.
- **AUTH-03** has all four named parts proven against a running instance: the RFC 9728 document behind the 401 pointer, dynamic client registration with `201` and `no-store`, PKCE S256 through a real authorization request, and a revocation that ends the connection before the next request returns and hands the Nextcloud credential back.
- **AUTH-07** has its three switches declared in the manifest, which is what makes them settable at all, with their defaults documented; all four enforcement points were already covered by plan 03-07.

**AUTH-04 stays Pending.** It names the two connectors against a publicly reachable staging
instance, which is plan 03-09 and needs a public domain.

## Next Phase Readiness

- **Ready for 03-09:** the server side is proven. What 03-09 owes is the staging instance and the two hosted clients. Two things from here will matter there: the public URL has to be set in the registration of that instance, and the two reverse proxy rules should be active before the first connector run, because a connector that only tries the canonical path is exactly the case they exist for.
- **Carried to 03-09 or the owner:** the throttle window of the token path is five minutes per source, so two connector attempts that both fail will make the third wait. That is intended, and it is worth knowing during a live demonstration.
- **No blockers.**

## Topology state at the end

The throwaway topology is shut down again, with the volumes intact:
`docker compose -p nc-mcp-exapp -f compose.exapp.yml down` (with a dummy `HP_SHARED_KEY`,
because the file requires the variable to be present), then
`docker stop nc_app_mcp_connector`, `docker rm nc_app_mcp_connector` and
`docker network rm nc-mcp-exapp-net`. The volumes
`nc-mcp-exapp_nextcloud-exapp-data` and `nc-mcp-exapp_registry-exapp-data` were not
touched. The two instances that are in daily use, `nc-mcp-test` and `findling-nextcloud`,
were not touched at any point.

---
*Phase: 03-oauth-2-1, Plan: 08*
*Completed: 2026-08-16*

## Self-Check: PASSED

All three created files exist on disk, all three task commits are in the history
(`edb2571`, `ac4530f`, `cf5c7ad`), every acceptance criterion of the three tasks was
executed as a command against the running topology and passed, and the plan level
verification was re-run on the final tree: the flow check ends 0 in both modes, the five
integration checks pass, the suite is 1282 passed and 81 deselected without Docker, all six
gates of D-32 are clean, `docs/oauth-setup.md` passes the section check of the plan
verbatim, and none of the four touched documents carries a secret shaped value.
