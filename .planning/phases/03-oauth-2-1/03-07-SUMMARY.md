---
phase: 03-oauth-2-1
plan: 07
subsystem: auth
tags: [oauth2.1, refresh-rotation, reuse-detection, rfc7009, revocation, throttling, rfc8707, abuse-matrix]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-02: oauth/store.py with redeem_refresh_token, its three outcomes and revoke_family"
  - phase: 03-oauth-2-1
    provides: "03-03: exapp/ui/errors.py with E6, its 429 and its Retry-After header"
  - phase: 03-oauth-2-1
    provides: "03-04: oauth/loginflow.py with the app password revocation, one attempt and no retry"
  - phase: 03-oauth-2-1
    provides: "03-05: oauth/provider.py with get_client as the enforcement point and the AS routes"
  - phase: 03-oauth-2-1
    provides: "03-06: oauth/verifier.py with its process cache and the invalidate hook, and the code exchange"
provides:
  - "oauth/provider.py: exchange_refresh_token with rotation, reuse detection and the D-41 grace window"
  - "oauth/provider.py: revoke_token and revoke_presented_token, one connection ends in three steps"
  - "oauth/provider.py: FamilyRevocation, our own /revoke, because the SDK handler cannot see an access token"
  - "oauth/provider.py: sweep_abandoned, the credentials of the sign ins nobody finished"
  - "oauth/throttle.py: per source and per path class counters, 429 with Retry-After, no value stored"
  - "oauth/store.py: cleanup_at, note_cleanup, clear_cleanup and abandoned_authorizations"
  - "tests/unit/test_oauth_abuse.py: the complete D-40 matrix over the HTTP layer"
affects: [03-08 live proof against the running topology, 03-09 the two connectors, 04 admin ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "an answer held for the length of a grace window, keyed by a digest, with a hard ceiling"
    - "an ASGI wrapper that asks a counter before the handler and tells it the status afterwards"
    - "a state change is noted before the network step that may fail, and cleared when it succeeded"
    - "a chore with a hard per call limit, hung on the path that has a reason to pay for it"

key-files:
  created:
    - src/mcp_connector/oauth/throttle.py
    - tests/unit/test_oauth_rotation.py
    - tests/unit/test_oauth_abuse.py
  modified:
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/oauth/consent.py
    - src/mcp_connector/oauth/connect.py
    - src/mcp_connector/oauth/loginflow.py
    - src/mcp_connector/entry_exapp.py
    - vulture_whitelist.py
    - tests/unit/test_oauth_provider.py

key-decisions:
  - "The grace window of D-41 repeats a held answer and never creates a second branch of the family; a lost held answer is invalid_grant and never a family kill"
  - "A reuse outside the window revokes the family and the authorization, in the store only, and notes the app password as a cleanup task instead of calling Nextcloud on the token path"
  - "A revocation is store, then process caches, then Nextcloud; the third step may fail and never holds up the first two"
  - "/revoke is rebuilt as FamilyRevocation, because load_access_token refuses by design and the SDK handler would answer 200 without revoking anything"
  - "The revocation request model makes client_secret optional, which the SDK model does not: a public client would otherwise get a 400 from its own revocation"
  - "The throttle has two limits: one per source, which a forwarded header can split, and one per path class, which it cannot"
  - "The throttle counts refusals by response status, so it needs to know no endpoint, and it never touches the MCP route"
  - "The sweep of abandoned sign ins hangs on the authorization request, bounded to three per call, because this project has no cron"

patterns-established:
  - "Hold an answer, not a session: a cache with a lifetime of seconds whose loss costs a retry and nothing else"
  - "Note the cleanup before the step that may fail, clear it when the step succeeded"
  - "A source gate reads code, not prose: strip the docstrings with ast before asserting on the text"

requirements-completed: []  # AUTH-03 and AUTH-07 stay Pending, see the requirement note below
requirements-advanced: [AUTH-03, AUTH-07]

# Metrics
duration: 40 min
completed: 2026-08-16
---

# Phase 3 Plan 07: Rotation, revocation, throttling and the D-40 abuse matrix Summary

**A stolen refresh token now costs the attacker the whole connection, a retransmitted one costs the user nothing, "revoked" means revoked before the request returns, and every misuse case of D-40 is a green test instead of a sentence in a plan.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-08-16T02:42:00Z
- **Completed:** 2026-08-16T03:22:00Z
- **Tasks:** 3 of 3 (all TDD, five commits)
- **Files created:** 3, modified: 8
- **New checks:** 68 (suite grew from 1206 to 1274)

## Accomplishments

- **The rotation has two sides and both are exact.** `exchange_refresh_token` asks the client policy, checks the audience of the connection, and only then redeems, in the one `UPDATE` under `BEGIN IMMEDIATE` the store already had. A first redemption issues a new pair of the same family and holds the answer for ten seconds. A second use inside those ten seconds is answered with exactly that held answer, byte for byte, and creates no second branch: three retries in a row leave two refresh rows and two access tokens in the file. A second use after them revokes every refresh and every access token of the family, revokes the authorization behind it, empties the held answers and the verifier cache, and answers `invalid_grant`. Nothing on any of those paths talks to Nextcloud.
- **The concurrency case is the normal case, and it behaves.** Two simultaneous redemptions of the same token produce exactly one successor and never two families: the loser of the write lock gets the held answer if the winner already stored it and `invalid_grant` if it did not, and neither outcome touches the family. Claude refreshes reactively on a 401 and proactively five minutes before an expiry, so this is the shape of ordinary traffic and not an edge case.
- **A revocation is three steps in the order the user expects.** The family and the authorization are marked as gone, the held answers and the five second verifier cache are emptied in the same process, and only then is the Nextcloud app password handed back with one `DELETE` and no retry, under a five second timeout of its own. A failed deletion leaves the connection revoked and writes `cleanup_at` on the authorization, so the orphaned credential is a record instead of a rumour. The measured proof is in the tests: immediately after the revocation, with the cache warm and the clock unmoved, the next tool call is a 401 that carries the same `WWW-Authenticate` pointer as a request with no token at all, and the client walks the whole flow again and works.
- **`/revoke` had to be rebuilt, and finding out why was worth the plan.** The SDK handler resolves a presented value through `load_access_token` first, which this deployment refuses on purpose (the bearer is checked by `oauth/verifier.py` and by nothing else), and then through `load_refresh_token`. A client that hands in its access token, which RFC 7009 explicitly allows, would therefore have received a 200 and kept a working connection. `FamilyRevocation` looks both kinds up in the store, checks that the connection belongs to the authenticated client, and answers 200 for everything else. Its request model also makes `client_secret` optional, which the SDK model does not: a public client, which Claude.ai and ChatGPT both are, would otherwise get a 400 from its own revocation.
- **The throttle answers to the right measure.** `oauth/throttle.py` counts refusals per path class and per source in a five minute window, answers 429 with `Retry-After` and the same number in the body or on the E6 page, and clears a source's counter on the first success. It sits on `/token`, `/register`, `/revoke`, `/authorize` with the consent screen, and the browser onboarding of AUTH-02, and it never sits on `/mcp`. The number it really bounds is named in its own docstring: every request with an `Authorization` header costs a Nextcloud PHP round trip through HaRP that this application cannot switch off, and an unknown bearer produces no brute force entry in Nextcloud, so Nextcloud will not set that ceiling for us. Two limits, because the per source counter is split by anybody who can write `X-Forwarded-For` and the per path ceiling is not.
- **The sign ins nobody finished no longer leave a working credential behind.** The consent bridge has to write an authorization the moment the Login Flow v2 poll answers, because that answer arrives exactly once. A browser closed at that moment used to leave the row and its Nextcloud app password forever. `sweep_abandoned` now finds those rows (no flow record, no code, no token of either kind, older than the twenty minute deadline of a sign in), hands the credential back and deletes the row, at most three per authorization request, on the one path that has a reason to pay for it. This was the open item 03-06 handed over.
- **The D-40 matrix is one file, at the HTTP layer, and it bites.** `tests/unit/test_oauth_abuse.py` assembles a deployment the way `entry_exapp` does (authorization server, consent surface, token verifier, a route behind the transport boundary) and drives every case of D-40 as a request: the replay after the rotation, the revoked client with its reconnection walk, the foreign `redirect_uri`, both shapes of PKCE downgrade, the missing and the wrong `code_verifier`, the audience mismatch at both ends, the registration with the switch off, and the allowlist at `/authorize` **and** at `/token`. Three mutation probes confirm it is not decorative: removing the grace window boundary, the audience check of the verifier and the cache invalidation each turns a green case red.

## Task Commits

1. **Task 1: rotation with reuse detection and the grace window** (TDD)
   - `988ba40` test: the failing checks for both sides of the window, the family kill and the race
   - `7c7535f` feat: `exchange_refresh_token`, `load_refresh_token`, the held answers and `cleanup_at`
2. **Task 2: the immediate revocation and the throttle** (TDD)
   - `290ec6a` test: the failing checks for the revocation, the sweep and the throttle
   - `b795fc9` feat: `revoke_token`, `FamilyRevocation`, `sweep_abandoned` and `oauth/throttle.py`
3. **Task 3: the D-40 abuse matrix**
   - `3b3902b` test: the complete matrix over the HTTP layer plus the three gates

## Files Created/Modified

- `src/mcp_connector/oauth/throttle.py` - `Throttle` with its two limits, its digest keyed counters and its ceiling on counters, `Throttled` as the ASGI wrapper, `source_of`, and the five path class constants.
- `src/mcp_connector/oauth/provider.py` - `load_refresh_token`, `exchange_refresh_token`, `_issue`, `_end_connection`, the held answers with `_hold` and `_held_answer`, `revoke_token`, `revoke_presented_token`, `_connection_of`, `_hand_back`, `sweep_abandoned`, `on_revocation`, the injectable clock, `FamilyRevocation` and `_RevocationRequest`.
- `src/mcp_connector/oauth/store.py` - the `cleanup_at` column with its idempotent `ALTER`, `note_cleanup`, `clear_cleanup` and `abandoned_authorizations`.
- `src/mcp_connector/oauth/consent.py` - the two routes take the shared throttle, as browser paths.
- `src/mcp_connector/oauth/connect.py` - the three onboarding routes take it too, with a path class of their own (T-03-35).
- `src/mcp_connector/oauth/loginflow.py` - `REVOKE_TIMEOUT`, five seconds on the one call a revocation makes.
- `src/mcp_connector/entry_exapp.py` - `provider.on_revocation(verifier.invalidate)` and one `Throttle` for the whole application.
- `vulture_whitelist.py` - fourteen entries left the list because plan 03-07 gave them production callers; three remain with their reasons.
- `tests/unit/test_oauth_rotation.py` - 23 checks on the rotation, with a clock a test moves by hand.
- `tests/unit/test_oauth_abuse.py` - 22 checks, the D-40 matrix and the three gates.
- `tests/unit/test_oauth_provider.py` - 23 new checks on the revocation, the sweep and the throttle.

## Decisions Made

Beyond the frontmatter list, four worth naming here:

- **A lost held answer is a refusal, never a family kill.** The held answers are a dictionary with a ten second lifetime and a hard ceiling of 256, and losing it (a restart, a second worker, the ceiling) is explicitly not evidence of anything. A retry inside the window whose answer is gone gets `invalid_grant` and the client reconnects, which is the same path it walks when a refresh token finally expires. That is what keeps this from being session state in the sense of SRV-05, and it is stated as such in the code.
- **The reuse detection revokes the authorization, not only the family.** D-40 asks for the family. Revoking the authorization as well costs nothing on the token path (it is one more `UPDATE` in the same file), makes every token ever issued under that connection dead rather than only the ones of one family, and is the honest reading of a token that was presented twice: that connection is compromised. The app password behind it is noted as a cleanup task instead of being deleted, because the token path may not call Nextcloud.
- **The throttle decides on the response status and knows no endpoint.** Anything from 400 upwards is a failed attempt. That covers every refusal of every endpoint behind the wrapper without the throttle having to learn a single one of them, it counts nothing that worked (the 302 of a successful authorization included), and it means a new authorization route is throttled the moment it is wrapped.
- **The abuse matrix keeps its own throttle out of the way.** The deployment it builds uses a `Throttle` with limits in the ten thousands. A matrix that throttles itself stops testing the refusals it exists for, and the throttle has its own checks in `test_oauth_provider.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The SDK revocation handler cannot revoke an access token of this deployment**

- **Found during:** Task 2
- **Issue:** `RevocationHandler` resolves the presented value through `provider.load_access_token` and then through `provider.load_refresh_token`. `load_access_token` refuses by design here (plan 03-06, so that the process cache, the audience check and the client policy cannot be bypassed), so a client that revokes with its access token would have received a 200 while the connection kept working. RFC 7009 explicitly allows either kind.
- **Fix:** `/revoke` is rebuilt as `FamilyRevocation`, which resolves both kinds against the store, checks that the connection belongs to the authenticated client, and hands the result to `revoke_presented_token`. Everything else stays the SDK's shape: same client authentication, 401, 400 and 200 in the same places.
- **Files modified:** `src/mcp_connector/oauth/provider.py`
- **Verification:** `test_revoking_an_access_token_ends_the_whole_family`, `test_the_revocation_endpoint_answers_200_and_no_store`
- **Committed in:** `b795fc9`

**2. [Rule 1 - Bug] A public client would get a 400 from its own revocation**

- **Found during:** Task 2
- **Issue:** The SDK's `RevocationRequest` declares `client_secret: str | None` without a default, which makes the field required and merely nullable. A public client, which Claude.ai and ChatGPT both are, sends no such field, so the model rejects the body before anything is revoked.
- **Fix:** `_RevocationRequest` in `provider.py` declares it optional, which is what RFC 7009 says. `token_type_hint` is left out entirely, because this server looks both kinds up either way and pydantic drops the unknown field.
- **Files modified:** `src/mcp_connector/oauth/provider.py`
- **Verification:** `test_the_revocation_endpoint_answers_200_and_no_store` (a public client, no secret in the body)
- **Committed in:** `b795fc9`

**3. [Rule 2 - Missing critical] A sign in nobody finished left a working Nextcloud credential behind for good**

- **Found during:** Task 2 (handed over by plan 03-06 as an open item, and listed as a pending todo in STATE.md)
- **Issue:** The consent bridge writes the authorization the moment the Login Flow v2 poll answers, because that answer arrives exactly once and the app password exists from then on. The flow record expires after twenty minutes, the authorization does not, and nothing ever handed that credential back.
- **Fix:** `store.abandoned_authorizations` finds the rows (no flow record, no code, no token of either kind, not revoked, older than `FLOW_TTL`) and `provider.sweep_abandoned` hands each credential back with one attempt and deletes the row, at most `SWEEP_LIMIT` (three) per call. It hangs on `authorize`, guarded so that it can never break an authorization.
- **Files modified:** `src/mcp_connector/oauth/store.py`, `src/mcp_connector/oauth/provider.py`
- **Verification:** `test_a_sign_in_nobody_finished_hands_its_credential_back`, `test_the_sweep_leaves_a_running_sign_in_and_a_live_connection_alone`, `test_the_sweep_takes_at_most_a_handful_per_call`
- **Committed in:** `b795fc9`

**4. [Rule 2 - Missing critical] The one Nextcloud call of a revocation ran on the thirty second read timeout**

- **Found during:** Task 2
- **Issue:** `loginflow.revoke_app_password` used the shared client's default timeouts. Pitfall 13 requires a short one here: the call sits inside a revocation, and a client gives that request about ten seconds.
- **Fix:** `REVOKE_TIMEOUT = 5.0` on that one request.
- **Files modified:** `src/mcp_connector/oauth/loginflow.py`
- **Verification:** the existing loginflow checks stay green; the constant is named and exported.
- **Committed in:** `b795fc9`

**5. [Rule 3 - Blocking] The store had no way to remember that a credential is an orphan**

- **Found during:** Task 1
- **Issue:** Both the reuse detection and a failed deletion have to leave a record that a Nextcloud app password is still out there, and `authorizations` had no column for it.
- **Fix:** `cleanup_at INTEGER` with an idempotent `ALTER TABLE` for a development store file, plus `note_cleanup` (idempotent, the first note stands) and `clear_cleanup` (the deletion succeeded).
- **Files modified:** `src/mcp_connector/oauth/store.py`
- **Verification:** `test_a_failed_deletion_does_not_hold_up_the_revocation`, `test_the_revocation_hands_the_app_password_back_to_nextcloud`
- **Committed in:** `7c7535f` (the column) and `b795fc9` (`clear_cleanup`)

**6. [Rule 1 - Deviation from the plan text] The log of a rejection is not empty, it is free of values**

- **Found during:** Task 3
- **Issue:** The plan asks for a `caplog` test on DEBUG over all rejection paths "that stays empty". It cannot: this server logs named events without values, for instance that a refresh token was presented outside the grace window, and an administrator has to be able to see that one happened.
- **Fix:** The check asserts the property the threat model owns (T-03-66): across every rejection path, on DEBUG, no value of the request that produced the record appears in the log, and neither does the PKCE challenge. The reasoning is in the test's own docstring.
- **Files modified:** `tests/unit/test_oauth_abuse.py`
- **Verification:** `test_no_rejection_writes_a_received_value_to_the_log`
- **Committed in:** `3b3902b`

**7. [Rule 1 - Deviation from the plan text] The source gate reads code and not prose**

- **Found during:** Task 3
- **Issue:** The plan asks the gate to show that neither `provider.py` nor `verifier.py` contains a retry loop against Nextcloud. A plain text search fails on the word "while" inside an explanatory sentence, and both files explain themselves at length.
- **Fix:** The gate strips the docstrings with `ast` and unparses the rest, which also drops every comment, and then asserts on the executable text: no `while`, no `range(`, no `sleep`, and at least one `compare_digest` per file.
- **Files modified:** `tests/unit/test_oauth_abuse.py`
- **Verification:** `test_the_comparisons_are_constant_time_and_no_loop_talks_to_nextcloud`
- **Committed in:** `3b3902b`

---

**Total deviations:** 7 auto-fixed (2 bugs in the SDK surface this deployment inherits, 2 missing critical behaviours, 1 blocking schema gap, 2 deviations from the plan text)
**Impact on plan:** No scope creep and no new dependency. The two additions with production weight are our own `/revoke` handler and the sweep of abandoned sign ins; both close a hole that would otherwise have surfaced only against a real Nextcloud.

### Requirement Status

**AUTH-03 and AUTH-07 both stay Pending, and this is the last plan that can advance them without a live proof.** All four enforcement points of AUTH-07 now exist and are exercised (`register_client`, `get_client`, both `exchange_*`, `verify_token`), and the full scope of AUTH-03 (PRM, DCR, PKCE S256, audience binding, revocation) is implemented and tested in process. What is missing for either requirement as written is the proof against a running topology, which is plan 03-08, and the two connectors, which is plan 03-09. `REQUIREMENTS.md` is unchanged.

## Issues Encountered

- **TDD gates versus the "all gates before every commit" rule.** The two RED commits contain checks that fail by construction, and the second one imports a module that does not exist yet, so pyright cannot be green on it. Lint and format were run and passed on both; every GREEN commit passes all six gates. Same documented tension as in 03-01 and 03-03 through 03-06.
- **Task 3 has no RED phase, and cannot have one.** Its deliverable is the test file itself, against behaviour the first two tasks built. Instead of a red run, three mutation probes were used to prove the matrix is not vacuous: inverting `_inside_grace` breaks the replay case, removing the audience check of the verifier breaks the audience case, and removing the cache invalidation breaks the two revocation cases. All three were reverted immediately and the suite is green on the committed tree.
- **The concurrency case has two legal outcomes.** With two simultaneous redemptions, the loser gets the held answer if the winner stored it first and `invalid_grant` if it did not; the ordering of two worker threads is not something to assert on. The check therefore asserts what must hold either way: at least one success, exactly one successor, and no revoked row.

## Known Stubs

None. Both stubs 03-06 listed as owned by this plan are gone: the refresh rotation issues tokens and the revocation revokes.

## Threat Flags

None. This plan added no route, no public surface and no outbound call that did not exist before: the only Nextcloud request it introduces is the app password deletion of a revocation and of the sweep, which is the same call `oauth/loginflow.py` already made on the denial path. `appinfo/info.xml` is unchanged, so the manifest gate has nothing to pull along.

## Verification Evidence

- Full suite: **1274 passed, 76 deselected** (from 1206), without Docker and without network. `test_oauth_rotation.py` 23, `test_oauth_abuse.py` 22, `test_oauth_provider.py` 62 (from 39).
- Gates on the final tree, each on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- Plan level verification, point by point:
  1. `pytest -q` green without Docker: yes, 1274 checks.
  2. Replay outside the window kills the family, inside it repeats the answer: `test_a_replay_after_the_window_kills_the_whole_family`, `test_a_retry_inside_the_window_repeats_the_same_answer`, and both again over HTTP in the abuse matrix.
  3. After a revocation the next call is a 401 with the pointer, and the reconnection walk is a test: `test_a_revoked_client_gets_a_401_with_a_pointer_and_can_connect_again` walks authorize, sign in, approve, token and tool call a second time and ends on a 200.
  4. A flood ends in 429 with `Retry-After` and reaches no Nextcloud: `test_a_flood_against_the_token_endpoint_reaches_no_nextcloud` asserts `len(respx.calls) == 0` over five refused token requests.
  5. `test_oauth_abuse.py` covers every D-40 case and is green.
  6. All six gates clean.
- Acceptance greps: `Retry-After` in `oauth/throttle.py` 1 (plus the header of E6), `reuse` in `tests/unit/test_oauth_abuse.py` present, `exchange_refresh_token` in `oauth/provider.py` present, `family` between provider and store present, `invalidate` between provider and verifier present, `429` between throttle and `exapp/ui/errors.py` present.
- Mutation probes (reverted immediately): `_inside_grace` forced to `True` fails `test_a_refresh_replay_after_the_rotation_kills_the_family`; the audience check of the verifier disabled fails `test_a_token_for_another_resource_is_refused_at_the_boundary`; `self._invalidate()` removed from `_end_connection` fails `test_a_revocation_takes_effect_inside_the_cache_window` and `test_the_401_after_a_revocation_points_where_an_anonymous_one_points`.

## Next Phase Readiness

- **Ready for 03-08:** the authorization server is feature complete on the test level. The live proof owes three things this plan could not check in process: that the app password deletion really removes the entry under "Devices and sessions", that a refresh over HaRP stays inside the thirty seconds a connector allows, and the count of Nextcloud round trips under a flood, which is the measurement SC 5 is actually about (access log or `docker logs`, not response times).
- **For 03-09:** nothing outstanding from here. Both connectors need the staging instance of D-39.
- **One open item is now closed:** the sweep for authorizations of a sign in nobody finished, which 03-06 handed over and STATE.md listed as a pending todo, is built, bounded and tested. The throttling of the public authorization paths, the second pending todo from 03-04 (T-03-35), is built as well.
- **Carried to 03-08:** `oauth/crypto.CONFIG_READ_PARAM` is still the one constant of this phase that no running AppAPI has confirmed.
- No blockers. Nothing in this plan needs a running Nextcloud, a container or a network.

---
*Phase: 03-oauth-2-1, Plan: 07*
*Completed: 2026-08-16*

## Self-Check: PASSED

All three created files exist on disk, all five commits are in the history (`988ba40`,
`7c7535f`, `290ec6a`, `b795fc9`, `3b3902b`), every acceptance criterion of the three tasks
was executed as a command and passed, and the plan level verification was re-run on the
final tree: 1274 checks in the suite, all six gates clean, and three mutation probes that
show the D-40 matrix fails when the control it stands for is removed.
