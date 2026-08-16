---
phase: 03-oauth-2-1
plan: 05
subsystem: auth
tags: [oauth2.1, dcr, rfc7591, rfc8707, allowlist, consent, login-flow-v2, starlette, mcp-sdk]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-01: oauth/metadata.py with the dcr_enabled parameter, the scope names and the no-store JSON helper"
  - phase: 03-oauth-2-1
    provides: "03-02: oauth/store.py with the clients, flows and authorizations tables, the two expiry windows and the crypto behind them"
  - phase: 03-oauth-2-1
    provides: "03-03: exapp/ui/layout.py, strings.py and the seven error pages"
  - phase: 03-oauth-2-1
    provides: "03-04: oauth/loginflow.py with start, one poll per call and the app password revocation"
provides:
  - "oauth/registry.py: the three admin switches of AUTH-07 as one immutable policy, plus the https rule for redirect addresses"
  - "oauth/provider.py: the SDK provider protocol with get_client as the enforcement point, register_client under the switches, authorize as the bridge into the sign in, and no-store over every authorization server answer"
  - "oauth/consent.py: /authorize in front of the SDK handler, plus the consent screen and its three states"
  - "exapp/ui/consent.py: S1, S2, the shape of S3 and the empty state"
  - "layout.app_path: every link and form action of the phase now carries the public prefix HaRP strips"
  - "appinfo/info.xml and scripts/bootstrap_exapp.sh: five new anchored PUBLIC routes"
affects: [03-06 consent decision and token endpoint, 03-07 rotation and revocation, 03-08 live proof, 04 admin ui for the allowlist]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "one policy object, asked at every point a client could get in, instead of one condition at the door"
    - "the SDK route is kept, its refusals are not: our own handler answers a person with a page and hands everything else to the SDK unchanged"
    - "an ASGI wrapper that overwrites Cache-Control on every answer of a route family"
    - "a browser address of this app is the configured public URL plus the path, never the path alone"
    - "two ids that are the same value (flow id and authorization id) instead of a column that links them"

key-files:
  created:
    - src/mcp_connector/oauth/registry.py
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/consent.py
    - src/mcp_connector/exapp/ui/consent.py
    - tests/unit/test_oauth_registry.py
    - tests/unit/test_oauth_provider.py
    - tests/unit/test_oauth_consent.py
  modified:
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/entry_exapp.py
    - src/mcp_connector/exapp/ui/layout.py
    - src/mcp_connector/exapp/ui/errors.py
    - src/mcp_connector/exapp/ui/connect.py
    - src/mcp_connector/exapp/ui/strings.py
    - appinfo/info.xml
    - scripts/bootstrap_exapp.sh
    - vulture_whitelist.py
    - tests/unit/test_oauth_metadata.py
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "The allowlist mode with an empty list refuses everything, and a switch value that is neither on nor off keeps its default and says so in the log"
  - "get_client answers None for unknown, blocked, unlisted and expired alike; which error page a refused client sees is decided from the administrator's configuration only, never from the state of a client"
  - "The client secret is stored as a SHA-256 digest, so the token endpoint stays fail closed for confidential clients until plan 03-06 brings its own client authenticator"
  - "Two routes of create_auth_routes are dropped: the metadata document (03-01 serves the complete one) and /authorize (oauth/consent.py stands in front of the SDK handler)"
  - "The sign in address travels as a query parameter of the redirect and is only rendered when its host is the configured Nextcloud or our own public URL"
  - "One authorization carries the id of its own flow, which links the two without a schema change"
  - "Every link and form action now carries the prefix from config.public_url, because HaRP strips it before this app sees a request"

patterns-established:
  - "Policy first, store second: the page a refused client sees comes from configuration, so no page is an oracle"
  - "A route family gets its cache header from one ASGI wrapper instead of from every handler"
  - "One route with a step parameter instead of two routes, so the manifest grows by one line and not by two"

requirements-completed: []  # AUTH-03 and AUTH-07 both stay Pending, see the requirement note below
requirements-advanced: [AUTH-03, AUTH-07]

# Metrics
duration: 35 min
completed: 2026-08-16
---

# Phase 3 Plan 05: Client registry, DCR policy and the consent bridge Summary

**An OAuth client can now register itself, ask for authorization and take its user through Nextcloud's own sign in to a consent screen that names it: the administrator can switch registration off, restrict it to a list, and every one of those refusals is a page that says what to do next instead of a JSON error a browser shows raw.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-08-16T01:22:00Z
- **Completed:** 2026-08-16T02:00:00Z
- **Tasks:** 3 of 3 (all TDD, six commits)
- **Files created:** 7, modified: 11
- **New checks:** 53 in `test_oauth_registry.py`, 25 in `test_oauth_provider.py`, 24 in `test_oauth_consent.py`, plus 6 in the manifest gate and the metadata tests

## Accomplishments

- **AUTH-07 has three switches and they are one object.** `NC_MCP_OAUTH_DCR`, `NC_MCP_OAUTH_ALLOWLIST_ONLY` and `NC_MCP_OAUTH_ALLOWED_CLIENTS` are read once into an immutable `ClientPolicy` whose repr counts its entries instead of printing them. The delivery state is registration on and allowlist off (D-35), a blank value counts as unset, and the allowlist mode with an empty list refuses everything: an administrator who switched it on and forgot the list meant to close the door.
- **The enforcement point exists where pitfall 9 says it has to.** `get_client` covers `/authorize`, `/token` and `/revoke` in one place because all three load their client through it. Unknown, blocked, not on the list and expired all answer `None`, and the expired registration is deleted on the way out, which is the whole cleanup of the registry in a project without a cron.
- **Registration is under the switch and under the redirect rule.** `register_client` refuses with `invalid_client_metadata` and a message that names the reason when registration is off, and with `invalid_redirect_uri` for any address that is not https or loopback, which the SDK does not check at all. The secret it was issued is stored as a digest, never as itself, and a byte level check proves the file does not contain it.
- **Four endpoints exist, and no answer of them can be cached.** `create_auth_routes` builds `/token`, `/register` and `/revoke`, one ASGI wrapper puts `Cache-Control: no-store` on every answer including the 201 the SDK sends without one, and the manifest and the bootstrap declare all of them fully anchored and PUBLIC with the five proxy headers stripped.
- **`/authorize` is ours, and the SDK still does the work.** Our handler decides who gets in and then hands the very same request to `AuthorizationHandler`, so PKCE, the `S256` literal, the exact redirect matching and the RFC error shapes are unchanged. What changed is the answer to a person: a client that is not allowed reads E1, an unknown client with registration off reads E2, an unknown one with registration on reads E3, a return address that does not match the registration reads E5 and is never redirected anywhere, and a bare `/authorize` is the empty state, which is where "Start over" of the timeout page leads.
- **The audience is required before anything else happens.** A request without the RFC 8707 `resource` parameter, or with one for another server, is refused with `invalid_target` before a sign in is even opened at Nextcloud, so a token that would be valid at every other MCP server cannot come into being (T-03-46).
- **The consent surface is three states on one route.** The handoff page carries the link into Nextcloud in a window of its own, the waiting state refreshes itself with one meta tag and polls exactly once per load, and a finished sign in turns into the consent screen with the identity line, the detail list, the grant list and the "Unverified client" callout for a client nobody put on the list. No JavaScript anywhere, and the credential of the sign in is stored encrypted rather than shown.
- **Every link of the phase now points at the right place.** `layout.app_path` prefixes each local target with the path of the configured public URL, because HaRP strips `/exapps/mcp_connector` before this app sees a request; without it every button of this surface, and of the `/connect` route of plan 03-04, would have pointed at the root of the Nextcloud domain.

## Task Commits

1. **Task 1: the three switches of AUTH-07** (TDD)
   - `28abbe3` test: the failing checks for the switches and the redirect rule
   - `9d8c67e` feat: `oauth/registry.py`
2. **Task 2: the provider, the routes and no-store** (TDD)
   - `344fd53` test: the failing checks for the registration half of the provider
   - `483090d` feat: `oauth/provider.py`, the store opener, the wiring, the manifest and the bootstrap
3. **Task 3: /authorize, the consent screen and the sign in** (TDD)
   - `4c32756` test: the failing checks for the consent bridge
   - `feeb262` feat: `oauth/consent.py`, `exapp/ui/consent.py`, `provider.authorize`, the prefix fix and the consent route

## Files Created/Modified

- `src/mcp_connector/oauth/registry.py` - the three environment names, `ClientPolicy` with `listed` and `allows`, `redirect_uri_allowed`, and the two expiry windows named next to the store's.
- `src/mcp_connector/oauth/provider.py` - `NextcloudOAuthProvider` with all eleven protocol methods, `auth_routes` and the `NoStore` wrapper.
- `src/mcp_connector/oauth/consent.py` - the authorization endpoint in front of the SDK handler and the four states of the consent screen.
- `src/mcp_connector/exapp/ui/consent.py` - S1, S2, S3 and the empty state, plus the path and parameter names the route is declared with.
- `src/mcp_connector/oauth/store.py` - `store_opener`, the one store per application with the sweep at its first use.
- `src/mcp_connector/entry_exapp.py` - one policy and one store opener feed the discovery document, the onboarding and the authorization server; `main` now turns a bad public URL into the same named exit as a missing volume.
- `src/mcp_connector/exapp/ui/layout.py`, `errors.py`, `connect.py` - `app_path` and the environment that reaches it.
- `src/mcp_connector/exapp/ui/strings.py` - three constants for the waiting state of the OAuth route.
- `appinfo/info.xml`, `scripts/bootstrap_exapp.sh` - five routes and the paragraph that says why each of them is public.
- `vulture_whitelist.py` - the nine protocol methods the SDK calls and nothing in this repository does.

## Decisions Made

Beyond the frontmatter list, four worth naming here:

- **Which error page a refused client sees is decided from the policy alone.** `get_client` cannot tell the caller why it refused, and that is deliberate (T-03-47). The page therefore comes from the administrator's own configuration: allowlist mode on and not listed reads E1, registration off reads E2, everything else reads E3. A blocked client while the allowlist mode is off therefore reads E3 and not E1, which is the price of not building an oracle; the honest reading of an unknown client id with registration open is a registration that expired, and E3 says exactly that.
- **The client secret stays a digest.** The SDK's `ClientAuthenticator` compares `client.client_secret` in plaintext, so returning only a digest means a confidential client cannot authenticate at `/token` yet. That endpoint refuses everything in this plan anyway, and the alternative, a plaintext secret in the store file, is the thing `client_secret_hash` was designed against in 03-02. Plan 03-06 owns the comparison.
- **The sign in address travels through the browser.** The `flows` table has no column for it and the schema is shipped, so a migration would have been the bigger change. The redirect carries the address and the page renders it only when its host is the configured Nextcloud or our own public URL, which in every supported topology is the same domain. A link that fails the check is dropped and the page still works, because the waiting state polls either way.
- **The authorization is written before the user consents.** The poll answers 200 exactly once and hands over an app password that exists from that moment, so it has to be stored right there. It is stored under the id of its own flow, nothing can be done with it until an authorization code exists, and the code is created only on approval in plan 03-06. The deny path of that plan owes the revocation; it is listed in the pending todos.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Every local link of the phase pointed at the Nextcloud root**

- **Found during:** Task 3 (the links of the consent screen)
- **Issue:** `layout.form`, `layout.link` and `layout.action` wrote the path this application sees (`/connect`, `/authorize`) into the document. HaRP strips `/exapps/mcp_connector` before the request arrives, so in a browser those absolute paths resolve against the domain root, where Nextcloud answers and this app is not. Every button of the browser onboarding of plan 03-04 and of the consent screen would have ended in a 404 in a real deployment; no test saw it because the test client serves the app at the root.
- **Fix:** `layout.app_path` puts the path of `config.public_url` in front of every local target, and the three functions take the environment. Without a configured public URL there is no prefix, which is exactly right for the local topology.
- **Files modified:** `src/mcp_connector/exapp/ui/layout.py`, `errors.py`, `connect.py`, `consent.py`
- **Verification:** `test_every_link_of_a_page_carries_the_public_prefix` in `test_oauth_consent.py`, plus the live render below.
- **Committed in:** `feeb262`

**2. [Rule 2 - Missing critical] The SDK registers a second document at a path this app already serves**

- **Found during:** Task 2 (wiring the routes)
- **Issue:** `create_auth_routes` registers `/.well-known/oauth-authorization-server` with `public, max-age=3600`. Plan 03-01 serves the same path with the complete document and `no-store`. Two routes on one path answer whichever was registered first.
- **Fix:** `auth_routes` drops that route, and a gate test asserts that no well-known path and no authorization path is served twice.
- **Files modified:** `src/mcp_connector/oauth/provider.py`, `tests/unit/test_exapp_env_setup.py`
- **Verification:** `test_no_authorization_route_is_declared_twice`, `test_the_document_route_is_served_once_and_by_us`
- **Committed in:** `483090d`

**3. [Rule 2 - Missing critical] A bad public URL would have surfaced as a traceback**

- **Found during:** Task 2 (the issuer)
- **Issue:** The SDK refuses an issuer that is neither https nor loopback with a bare `ValueError`, which `build_exapp_app` raised outside the block that turns configuration errors into a named exit.
- **Fix:** `auth_routes` turns it into a `ToolError` with a hint an administrator can act on, and `main` builds the application inside the same try block as the other environment checks, so the process exits with code 2 and one readable line.
- **Files modified:** `src/mcp_connector/oauth/provider.py`, `src/mcp_connector/entry_exapp.py`
- **Verification:** Reviewed against the existing exit path of `config.persistent_storage`; the branch is a deployment error no unit test forces, which is stated here rather than claimed as covered.
- **Committed in:** `483090d`

**4. [Rule 3 - Blocking] The plan asks for one /authorize route, the behaviours ask for pages**

- **Found during:** Task 3
- **Issue:** The plan wires `/authorize` from `create_auth_routes`, but its behaviours require E1, E2, E3 and E5 pages and the empty state, and the SDK handler answers JSON for all of them.
- **Fix:** `oauth/consent.py` serves `/authorize` and delegates to the SDK's `AuthorizationHandler` for everything it does not refuse, and `auth_routes` drops the SDK's own route. The SDK still checks PKCE, the response type, the redirect match and the error format.
- **Files modified:** `src/mcp_connector/oauth/consent.py`, `src/mcp_connector/oauth/provider.py`, `tests/unit/test_oauth_provider.py`
- **Verification:** `test_the_application_serves_the_four_endpoints_exactly_once_each` and the four refusal checks of `test_oauth_consent.py`.
- **Committed in:** `feeb262`

**5. [Rule 1 - Deviation from the plan text] The expiry windows are named, not redefined**

- **Found during:** Task 1
- **Issue:** The plan asks for the two expiry windows as constants of `registry.py`; `store.py` already defines them and sweeps with them.
- **Fix:** `registry.py` re-exports them under names of its own with a comment. Two numbers for one rule is the failure the plan wanted to prevent, and one source with two names prevents it better than two sources.
- **Files modified:** `src/mcp_connector/oauth/registry.py`
- **Verification:** `test_the_expiry_windows_are_the_ones_the_store_sweeps_with`
- **Committed in:** `9d8c67e`

**6. [Rule 1 - Deviation from the plan text] The consent surface is one route with a step, not two routes**

- **Found during:** Task 3
- **Issue:** The plan describes a consent route and a waiting state. Two routes would have been two manifest declarations, which is two lines of external surface for one page.
- **Fix:** One route, `/authorize/consent`, with a `step` parameter. Without it the page is the handoff, with it the waiting state, which is the one state that polls. The meta refresh reloads the address it is on, so the state survives without a second path.
- **Files modified:** `src/mcp_connector/exapp/ui/consent.py`, `src/mcp_connector/oauth/consent.py`, `appinfo/info.xml`
- **Verification:** `test_the_waiting_page_polls_exactly_once_per_load`, `test_the_first_page_hands_the_user_over_to_nextcloud`
- **Committed in:** `feeb262`

**7. [Rule 3 - Blocking] The poll mechanics were not merged with the onboarding route**

- **Found during:** Task 3
- **Issue:** The plan asks to pull the shared parts of `/connect` and the consent route into one function, or to say why not.
- **Fix:** Not merged, and this is the reason: the two routes share the shape (load the flow, check the deadline, poll once) but not one branch afterwards. `/connect` deletes the flow and renders a credential, the consent route keeps the flow and creates an authorization; a merged function would need a callback per branch and would touch a shipped, covered route of another plan for no gain. The ten identical lines carry a comment naming their sibling.
- **Files modified:** `src/mcp_connector/oauth/consent.py`
- **Verification:** Both route test files are green side by side.
- **Committed in:** `feeb262`

---

**Total deviations:** 7 auto-fixed (1 bug, 2 missing critical, 2 blocking, 2 deviations from the plan text)
**Impact on plan:** No scope creep and no new dependency. The one finding with production weight is the missing public prefix on every link, which also repairs the onboarding route of plan 03-04.

### Requirement Status

**AUTH-03 and AUTH-07 both stay Pending.** AUTH-07 names four enforcement points and this plan builds two of them (`register_client` and `get_client`); the other two, `exchange_*` and `verify_token`, are plans 03-06 and 03-07, and the requirement is only true when a client blocked in the middle of a flow and a token issued before a block are both refused. AUTH-03 is a statement about a client that connects, and no token can be issued yet. `REQUIREMENTS.md` is unchanged.

## Issues Encountered

- **TDD gates versus the "all gates before every commit" rule.** The three RED commits contain tests that fail by construction and import modules that do not exist yet, so pyright cannot be green on them. Lint and format were run and passed on all three; every GREEN commit passes all six gates. Same documented tension as in 03-01, 03-03 and 03-04.
- **One whitelist entry with a two commit lifetime.** `ClientPolicy.allows` had no production caller between task 1 and task 2 and was whitelisted with that reason, then replaced by the block for the nine provider protocol methods, which the SDK calls and this repository never does.
- **The dead code gate reports unused parameters of a refusing method.** The placeholder methods of the protocol drop what they were given with `del`, which is both what the tool needs and an honest statement about a method that answers without looking at its arguments.

## Known Stubs

Three, all of them named in the plan itself and all of them owned by the next two plans:

- **The consent screen has no buttons yet.** S3 renders the identity, the warning, the details and the grant list; "Approve access", "Deny access" and the anti forgery token are plan 03-06, and the POST route is already declared and answers 400 until then.
- **Six provider methods refuse.** `load_authorization_code`, `exchange_authorization_code`, `load_refresh_token`, `exchange_refresh_token`, `load_access_token` and `revoke_token` exist with the signature of the protocol and refuse fail closed. `exchange_identity_assertion` refuses permanently, which is a decision and not a stub.
- **An authorization exists before anybody approved it.** It carries no code and no token, so nothing can be done with it, but the app password behind it lives at Nextcloud. The deny path of 03-06 has to revoke it and 03-07 should sweep the abandoned ones; both are in the pending todos of `STATE.md`.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: new-public-route | appinfo/info.xml | Five new PUBLIC routes: `/authorize`, `/authorize/consent`, `/token`, `/register` and `/revoke`. They are in the threat model of this plan (T-03-40 to T-03-48); what is not yet in place is the throttling of anonymous flow creation, which T-03-48 assigns to plan 03-07 (SC 5). |
| threat_flag: attacker-controlled-render | src/mcp_connector/oauth/consent.py | The sign in address reaches the consent page through the browser. It is only rendered when its host is the configured Nextcloud or the configured public URL; a deployment whose `overwrite.cli.url` names a third host would lose the link (and only the link) instead of rendering a foreign one. |

## Verification Evidence

- Full suite: **1137 passed, 76 deselected**, without Docker and without network. `test_oauth_registry.py` 53, `test_oauth_provider.py` 25, `test_oauth_consent.py` 24, `test_exapp_env_setup.py` 98, `test_oauth_metadata.py` 32.
- Gates on the final tree, each on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- Route wiring, live: `build_exapp_app(...)` lists `['/authorize', '/register', '/revoke', '/token']` and one `/authorize/consent`; `entry_http.build_app({})` lists none of them.
- Switch, live: with `NC_MCP_OAUTH_DCR=off` the application answers `/register` with 404 and its `openid-configuration` carries no `registration_endpoint`; in the delivery state both exist.
- Live render with `NC_MCP_PUBLIC_URL=https://cloud.example.com/exapps/mcp_connector`: the handoff page carries `<a class="btn-link" href="https://cloud.example.com/index.php/login/v2/flow/abc" target="_blank" rel="noopener noreferrer">Continue to Nextcloud sign in</a>` and a form action of `/exapps/mcp_connector/authorize/consent`; the consent screen carries "Allow Claude to use your Nextcloud?", "You are signed in as alice at cloud.example.com.", the "Unverified client" callout, the three details with the full return address and the four grant lines of the UI contract.
- Acceptance greps: `grep -rc "<script" src/mcp_connector/exapp/ui/consent.py` is 0, the three environment names appear in `registry.py` exactly three times and only in the constant block.

## Next Phase Readiness

- **Ready for 03-06:** the flow record carries every field a code needs, the authorization and its app password are stored under the flow id, `get_client` is the enforcement point the token endpoint inherits, and the consent screen only needs its two buttons and the anti forgery token. The one thing 03-06 has to bring of its own is the client authenticator that compares against `client_secret_hash`, because the SDK's compares plaintext.
- **Ready for 03-07:** the policy object is where the two remaining enforcement points ask their question, and the abandoned authorizations of a sign in nobody finished are the sweep it should add.
- **For 03-08:** the live proof of this plan is one browser session against the staging instance: register a client, walk `/authorize`, sign in, and read the consent screen, plus one run with `NC_MCP_OAUTH_ALLOWLIST_ONLY=1` that ends on E1.
- No blockers. Nothing in this plan needs a running Nextcloud, a container or a network.

---
*Phase: 03-oauth-2-1, Plan: 05*
*Completed: 2026-08-16*

## Self-Check: PASSED

All seven created files exist on disk, all six commits are in the history (`28abbe3`,
`9d8c67e`, `344fd53`, `483090d`, `4c32756`, `feeb262`), every acceptance criterion of the
three tasks was executed as a command and passed, and the plan level verification was
re-run on the final tree: 1137 checks in the suite, all six gates clean, the four
authorization routes present in the ExApp application and absent from the standalone one.
