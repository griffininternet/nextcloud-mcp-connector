---
phase: 03-oauth-2-1
plan: 04
subsystem: auth
tags: [login-flow-v2, app-password, onboarding, starlette, html, no-javascript, respx]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-02: oauth/store.py with the flows table, the encrypted poll token and purge_expired"
  - phase: 03-oauth-2-1
    provides: "03-03: exapp/ui/layout.py, strings.py, icons.py and the seven error pages"
  - phase: 02-exapp-shell
    provides: "exapp/status.py as the one shape of an outgoing Nextcloud call, and entry_exapp as the one place routes are attached"
provides:
  - "oauth/loginflow.py: start, poll once and revoke, each with exactly one attempt and no secret in a log record"
  - "oauth/connect.py: the three routes of the browser onboarding, plus the first production OAuthStore instance and the purge at its first use"
  - "exapp/ui/connect.py: the four screens of the onboarding, the meta refresh and the route paths they link to"
  - "layout.page(head_extra=...), layout.external_action and layout.form(method='get') as the three additions 03-03 named"
  - "appinfo/info.xml and scripts/bootstrap_exapp.sh: the two anchored /connect routes"
affects: [03-05 authorize and consent, 03-06 token endpoint and verifier, 03-07 revocation, 03-08 staging proof]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "one attempt per outgoing call, a named return value instead of an exception (exapp/status.py, now for three calls)"
    - "the deadline of a flow is ours, because the answer of Nextcloud cannot tell not yet from expired"
    - "attacker controlled text is reduced to printable ASCII before it becomes a header value"
    - "route paths live next to the links that write them, so a link and its route cannot drift apart"
    - "the process wide store lives in the closure of the route factory, not in a module global"

key-files:
  created:
    - src/mcp_connector/oauth/loginflow.py
    - src/mcp_connector/oauth/connect.py
    - src/mcp_connector/exapp/ui/connect.py
    - tests/unit/test_oauth_loginflow.py
    - tests/unit/test_oauth_connect.py
  modified:
    - src/mcp_connector/exapp/ui/layout.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - scripts/bootstrap_exapp.sh
    - docs/client-setup.md
    - tests/unit/test_exapp_env_setup.py
    - tests/contract/test_no_destructive_calls.py
    - vulture_whitelist.py

key-decisions:
  - "The poll goes to the configured base URL with a fixed path; the absolute address in the start answer is read by nothing and proved unused by a test that would fail if it were called"
  - "The sign in link is shown on the page that the start produced and never on the refreshing page, because a link that disappears three seconds after it appeared is worse than one reached again through Start over"
  - "The onboarding books its flows under one reserved client row that is marked as not allowed, because the flows table has a foreign key and this route has no registered client at all"
  - "The flow record is deleted before the credential is rendered, because the 200 of a poll arrives exactly once"
  - "A failed deletion of a finished flow revokes the app password again instead of leaving it behind in Nextcloud"
  - "page() takes one optional head fragment and refuses anything that is not the meta refresh, so the head stays as closed as the rest of the shell"

patterns-established:
  - "A GET never starts a flow: the state changing step of a browser surface is a POST with a named action"
  - "Byte level leak test for a rendered secret: the whole store directory is searched for the credential the page showed"
  - "Manifest gate by set equality for a second family of routes, plus a general end anchor rule for every declared route"

requirements-completed: []  # AUTH-02 stays Pending until the live proof of 03-08, see below
requirements-advanced: [AUTH-02]

# Metrics
duration: 25 min
completed: 2026-08-16
---

# Phase 3 Plan 04: Login Flow v2 and the /connect onboarding Summary

**A user without an OAuth capable client now opens one page, signs in on Nextcloud's own pages including the second factor, and reads one dedicated app password exactly once: no input field anywhere on the route, one poll per page load, twenty minutes of life per sign in, and nothing of the credential in any file or log.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-16T00:56:48Z
- **Completed:** 2026-08-16T01:22:00Z
- **Tasks:** 3 of 3 (two TDD, five commits)
- **Files created:** 5, modified: 9
- **New checks:** 66 in `test_oauth_loginflow.py`, 31 in `test_oauth_connect.py`, 5 in `test_exapp_env_setup.py` and `test_no_destructive_calls.py`

## Accomplishments

- **The Login Flow v2 is a building block with three functions and one attempt each.** Start, poll and revoke all read the base URL from `config.exapp_settings`, all go through `shared_client()`, none of them retries, and none of them raises at the caller: a failure is a named return value, which is what lets the route answer a person instead of a stack trace (D-37).
- **The three hard properties of the flow are nailed down by tests, not by comments.** One poll per call is counted on the respx route; the absolute poll address of the start answer is registered as a second route and asserted to have zero calls; a 404 is "not finished yet" and the deadline comes from our own record, because Nextcloud cannot tell "not yet" from "expired" (pitfall 7).
- **The client name cannot become a header.** `safe_user_agent` reduces the name to printable ASCII, which removes CR and LF and with them every injection, collapses whitespace, caps the length at 64 and puts the fixed prefix "MCP Connector: " in front. Ten parametrised cases cover the line break, the null byte, umlauts, an emoji, a right to left override, three hundred characters and the empty name (T-03-31).
- **The onboarding is three routes and four screens, with no JavaScript at all.** The invitation offers one POST button, the handoff carries the Nextcloud link in a window of its own with `rel="noopener noreferrer"`, the waiting screen refreshes itself with one `meta http-equiv="refresh"` and polls exactly once per load, and the result shows user name and credential once.
- **Nothing of the credential survives the answer.** The flow record is removed before the page is built, a test reads the whole store directory including the write ahead log as bytes and does not find the app password, a second load of the same address is the expired page with status 400, and no log record carries the credential, the poll token or even the flow id.
- **The store got its first production caller.** `connect_routes` opens one `OAuthStore` per application, on first use, and runs `purge_expired` there: this project has no cron, so the sweep hangs on the first use of the store (T-03-17). The cache lives in the closure of the factory and not in a module global, so the contract gate on module level state keeps its meaning (D-20).
- **The manifest grew by exactly two anchored routes**, both PUBLIC with the same reasoning as `/mcp`, both mirrored in the json-info registration of the bootstrap, and the manifest gate now demands an end anchor for every route instead of only for the well-known ones.

## Task Commits

1. **Task 1: Login Flow v2 with one attempt per call** (TDD)
   - `dd51099` test: the failing checks for the building block
   - `2e8b02b` feat: `oauth/loginflow.py` plus the narrow exemption in the destructive call gate
2. **Task 2: the browser onboarding** (TDD)
   - `1e36896` test: the failing checks for the route
   - `156f80e` feat: `oauth/connect.py`, `exapp/ui/connect.py`, the three layout additions, the manifest and the bootstrap
3. **Task 3: the way in the documentation**
   - `3d42840` docs: the `/connect` section of `docs/client-setup.md`

## Files Created/Modified

- `src/mcp_connector/oauth/loginflow.py` - `start_flow`, `poll_once`, `revoke_app_password`, `safe_user_agent`, the two masked containers and the three paths of the research.
- `src/mcp_connector/oauth/connect.py` - `connect_routes` with the invitation, the start or cancel POST and the waiting route, the reserved client row, the store provider and the four ends of the flow.
- `src/mcp_connector/exapp/ui/connect.py` - the four screens, `meta_refresh`, and the paths and field names the routes are declared with.
- `src/mcp_connector/exapp/ui/layout.py` - `head_extra` with its pattern, `external_action`, `status_line`, `form(method=...)` and two style rules.
- `src/mcp_connector/exapp/ui/strings.py` - twelve constants for the onboarding, in the tone of the rest.
- `appinfo/info.xml`, `scripts/bootstrap_exapp.sh` - the two `/connect` routes and the paragraph that says what they accept.
- `docs/client-setup.md` - the onboarding section, the phishing sentence and the assignment of the two ways to the clients they are meant for.
- `tests/contract/test_no_destructive_calls.py` - the second narrow exemption plus its counter proof.
- `vulture_whitelist.py` - six store methods left the list because they have production callers now.

## Decisions Made

Beyond the frontmatter list, three worth naming here:

- **The waiting screen does not carry the sign in link.** 03-UI-SPEC S2 lists a status line, "Check now" and "Start over", and no primary call to action, and the reason is mechanical: the page refreshes every three seconds, so a link on it would vanish while the user is still reading. The handoff page that the start produced carries it instead, and a user whose sign in window is gone reaches a fresh one through "Start over". Documented as a deviation below, because the plan describes the start as showing the waiting page.
- **One POST route with a named action instead of two routes.** Starting and cancelling are the same resource and each declared route is a line of external attack surface (D-38). An unknown action answers the invitation page with status 400 rather than a page of its own.
- **`_generic` builds the page and writes the log line together.** The reference of E7 exists once, in one answer and in one record, so the sentence "an administrator can find the details under reference ..." is true instead of decorative. A test reads the reference out of the rendered page and finds exactly that value in the log.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The flows table has a foreign key and this route has no client**

- **Found during:** Task 2 (the start of a sign in)
- **Issue:** `flows.client_id` references `clients(client_id)` with `ON DELETE CASCADE`, because in the OAuth flow of 03-05 a flow always belongs to a registered client. The onboarding has no client at all: the user is on that page precisely because their app cannot register itself. Every insert failed with `FOREIGN KEY constraint failed`.
- **Fix:** One reserved row, `urn:mcp-connector:browser-onboarding`, written with `allowed=False` so the enforcement point of AUTH-07 refuses it as a client, and touched on every start so the idle cleanup of `purge_expired` cannot delete it under a running flow. The alternative, a schema change, would have needed a migration path for a store that already exists.
- **Files modified:** `src/mcp_connector/oauth/connect.py`
- **Verification:** `test_the_flow_record_is_unguessable_and_runs_out_after_twenty_minutes` and the expiry test, which both write and read a real row.
- **Committed in:** `156f80e`

**2. [Rule 3 - Blocking] The destructive call gate refused the revocation of our own app password**

- **Found during:** Task 1
- **Issue:** `tests/contract/test_no_destructive_calls.py` forbids the token `DELETE` anywhere in `src/`. The revocation of an app password is an HTTP DELETE, and it is the opposite of what TOOL-09 protects: without it a connection a user revoked would stay usable in Nextcloud.
- **Fix:** A second exemption as narrow as the SQL one of 03-02: one file, and only the verb on a line of its own, which is the shape the formatter gives the one call that is meant. A DELETE written inline against any other target in the same module is still a finding.
- **Files modified:** `tests/contract/test_no_destructive_calls.py`
- **Verification:** `test_the_app_password_exemption_covers_one_call_form_and_nothing_else`, which asserts the same line is not exempt in `tools/files.py` and that an inline DELETE in `loginflow.py` is still reported.
- **Committed in:** `2e8b02b`

**3. [Rule 2 - Missing critical] The login link of the start answer is checked before it is rendered**

- **Found during:** Task 1
- **Issue:** The plan describes reading `login` out of the start answer. That value is written into an `href` of a page a user clicks, and a `javascript:` or `data:` value there is the phishing step this whole surface exists against (T-03-30). Nothing in the plan checks it.
- **Fix:** `start_flow` refuses any login link whose scheme is not http or https, and `layout.external_action` refuses it a second time at the point where it writes the attribute. Both are covered: four parametrised cases at the boundary, one raising check in the renderer.
- **Files modified:** `src/mcp_connector/oauth/loginflow.py`, `src/mcp_connector/exapp/ui/layout.py`
- **Verification:** `test_a_login_url_that_is_not_http_is_refused`.
- **Committed in:** `2e8b02b`, `156f80e`

**4. [Rule 2 - Missing critical] A finished flow that cannot be deleted revokes its credential**

- **Found during:** Task 2 (the success path)
- **Issue:** The plan says: render the page, delete the record, store nothing. If the deletion fails, the order in the plan would have shown the credential and left a record that lets the next load poll again, and the order chosen here (delete first) would have left a fresh app password alive in Nextcloud that nobody ever received.
- **Fix:** The deletion runs first, and its failure path revokes the app password that was just created before answering the generic page (pitfall 13). That is also the production caller `revoke_app_password` needed to exist for.
- **Files modified:** `src/mcp_connector/oauth/connect.py`
- **Verification:** Reviewed against the revocation tests of task 1; the branch itself is a store failure that no unit test forces, which is stated here rather than claimed as covered.
- **Committed in:** `156f80e`

**5. [Rule 1 - Deviation from the plan text] The refreshing page is not the answer to the start**

- **Found during:** Task 2 (the screens)
- **Issue:** The plan says the start "shows the waiting page", and the waiting page refreshes every three seconds. The sign in link can only be shown once at that pace, and a user who reads the page for four seconds loses it.
- **Fix:** The start answers the handoff screen, which carries the link, the "Check now" button and "Start over" and does not refresh. The refreshing waiting screen is the GET route behind it, and that route is where the one poll per load happens, exactly as the plan requires.
- **Files modified:** `src/mcp_connector/exapp/ui/connect.py`
- **Verification:** `test_the_start_opens_one_flow_and_links_to_nextcloud_in_a_new_window` and `test_the_waiting_page_refreshes_itself_and_polls_exactly_once`.
- **Committed in:** `156f80e`

**6. [Rule 2 - Missing critical] The end anchor rule now covers every declared route**

- **Found during:** Task 2 (the manifest gate)
- **Issue:** The gate demanded an end anchor for well-known routes only. `^/connect` without the anchor would publish every path that begins with it, which is the same mistake AR-02-06 was about.
- **Fix:** The rule applies to every route of the manifest, and the two counter probes of phase 2 still fire.
- **Files modified:** `tests/unit/test_exapp_env_setup.py`
- **Verification:** `test_the_manifest_gate_rejects_a_well_known_route_without_an_end_anchor` and its sister, both unchanged and green.
- **Committed in:** `156f80e`

---

**Total deviations:** 6 auto-fixed (2 blocking, 3 missing critical, 1 deviation from the plan text)
**Impact on plan:** No scope creep and no new dependency. Two were gate collisions that had to be resolved to commit at all, three close holes on the path that hands a credential to a person, and one changes which of two screens carries the sign in link.

### Requirement Status

**AUTH-02 stays Pending.** The route is complete and covered, but the requirement says a user
onboards through the browser login, and that is a statement about a running Nextcloud. Every
Nextcloud answer in this plan comes from respx. Plan 03-08 runs the flow against the staging
instance; the check mark belongs there, exactly as 03-01 to 03-03 handled AUTH-03.
`REQUIREMENTS.md` is unchanged.

## Issues Encountered

- **TDD gates versus the "all gates before every commit" rule.** The two RED commits (`dd51099`, `1e36896`) contain tests that fail by construction and import modules that do not exist yet, so pyright cannot be green there. Lint and format were run and passed on both; both GREEN commits pass all six gates. Same documented tension as in 03-01 and 03-03.
- **One whitelist entry with a two commit lifetime.** `PollResult.credentials` had no production reader between the two tasks of this plan, which the dead code gate reports at full confidence. It was whitelisted with that reason in the first commit and removed again in the second, together with the six store methods that now have real callers.
- **Two test expectations were corrected against the implementation, not the other way round.** The cleaned user agent drops CR and LF rather than replacing them with a blank, and the flow id is read out of the hidden field of the rendered form rather than out of a query string. Neither is a security property; both were unspecified details the RED test had guessed.

## Known Stubs

None on this route. Two things are deliberately not here and belong to later plans: the
throttling of the PUBLIC authorization paths (03-07, SC 5), and the live proof against a
running Nextcloud (03-08). `errors.START_OVER_PATH` still points at `/authorize`, the route
that 03-05 creates, so the "Start over" link of the E4 page reaches a 404 until then; the E4
page of this route is reached through `/connect` links that do exist.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: new-public-route | appinfo/info.xml | Two PUBLIC routes, `/connect` and `/connect/wait`, are new external surface. They are in the threat model of this plan (T-03-30 to T-03-37); what is not yet in place is the throttling of anonymous flow creation, which T-03-35 assigns to plan 03-07 (SC 5). |

## Verification Evidence

- `uv run --no-sync pytest tests/unit/test_oauth_loginflow.py`: 66 passed. `tests/unit/test_oauth_connect.py`: 31 passed. `tests/unit/test_exapp_env_setup.py`: 95 passed. Full suite: **1030 passed, 76 deselected**, without Docker and without network.
- Gates on the final tree, each on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest -q` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- Acceptance greps: `grep -v '^\s*#' loginflow.py | grep -c "for attempt\|while True\|retries"` is 0, `grep -c "poll.*endpoint" loginflow.py` is 0, `grep -rc 'type="password"' src/mcp_connector/exapp/ui/` is 0 for every file.
- Route wiring, live: `build_exapp_app(...)` lists `['/connect', '/connect', '/connect/wait']`, and `entry_http.build_app({})` lists none of them.
- Live render with `NC_MCP_PUBLIC_URL=https://cloud.example.com/exapps/mcp_connector`: the invitation page answers 200 with `Content-Security-Policy: default-src 'none'; style-src 'nonce-...'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`; the waiting page carries `<meta http-equiv="refresh" content="3">` and `<p class="status" role="status" aria-live="polite">Waiting for your sign in at cloud.example.com.</p>`; the result page carries the credential and nothing else does.

## Next Phase Readiness

- **Ready for 03-05:** `loginflow.start_flow` and `poll_once` are exactly what `/authorize` needs, the flow record is already the one the OAuth flow uses (with the columns this route leaves empty), and the consent screen can be built out of the same components. The one thing 03-05 has to decide for itself is where it keeps the Nextcloud sign in link between two renders, because this plan solved it by showing the link on a page that does not refresh.
- **Ready for 03-06 and 03-07:** the store instance and the purge at first use exist and are wired; `revoke_app_password` is the second half of the revocation path of SC 4.
- **For 03-08:** the live proof of Success Criterion 3 is one browser session against the staging instance: open `/exapps/mcp_connector/connect`, sign in, read the credential, use it as a Basic header against `/mcp`, then check that it appears in "Devices and sessions" and can be revoked there.
- No blockers. Nothing in this plan needs a running Nextcloud, a container or a network.

---
*Phase: 03-oauth-2-1, Plan: 04*
*Completed: 2026-08-16*

## Self-Check: PASSED

All five created files exist on disk, all five commits are in the history (`dd51099`,
`2e8b02b`, `1e36896`, `156f80e`, `3d42840`), every acceptance criterion of the three tasks was
executed as a command and passed, and the plan level verification was re-run on the final
tree: 1030 checks in the suite, all six gates clean.
