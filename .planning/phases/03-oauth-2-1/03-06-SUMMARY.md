---
phase: 03-oauth-2-1
plan: 06
subsystem: auth
tags: [oauth2.1, consent, csrf, rfc8707, rfc9207, pkce, token-verifier, credentials, mcp-sdk]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-01: the transport boundary with its bearer branch and the resource_metadata pointer of the 401"
  - phase: 03-oauth-2-1
    provides: "03-02: oauth/store.py with auth_codes, access_tokens and refresh_tokens, and oauth/crypto.py with the data key"
  - phase: 03-oauth-2-1
    provides: "03-03: exapp/ui/layout.py, strings.py and the seven error pages"
  - phase: 03-oauth-2-1
    provides: "03-04: oauth/loginflow.py with the app password revocation"
  - phase: 03-oauth-2-1
    provides: "03-05: oauth/provider.py with get_client as the enforcement point, oauth/consent.py with the consent screen, and the authorization server routes"
provides:
  - "oauth/consent.py: the decision itself, an anti forgery value bound to the flow, the approval redirect with code, state and iss, and the denial that takes the app password back"
  - "oauth/provider.py: load_authorization_code and exchange_authorization_code with the audience check of RFC 8707 and the client policy in front of it, plus HashedClientAuthenticator for confidential clients"
  - "oauth/verifier.py: the TokenVerifier of this deployment, with a five second process cache, the audience check and the client policy"
  - "exapp/middleware.py: the transport boundary uses the verifier and leaves the resolved identity in the request state"
  - "deps.py: the fifth credential mode, an OAuth token becomes the Nextcloud user who consented"
  - "exapp/ui/consent.py: S3 with its two buttons and S4 with its two result pages"
affects: [03-07 rotation and revocation, 03-08 live proof, 04 admin ui and per user management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "an anti forgery value derived from the data key and the flow id instead of stored in a column"
    - "the transport boundary resolves the identity once per request and leaves it in the request state, because the credential layer of a tool call is synchronous"
    - "one route, two verbs: the GET renders the state, the POST is the decision"
    - "a cache keyed by the digest of a token, never by the token, holding positive answers only"

key-files:
  created:
    - src/mcp_connector/oauth/verifier.py
    - tests/unit/test_oauth_verifier.py
    - tests/unit/test_oauth_credentials.py
  modified:
    - src/mcp_connector/oauth/consent.py
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/oauth/crypto.py
    - src/mcp_connector/exapp/ui/consent.py
    - src/mcp_connector/exapp/ui/layout.py
    - src/mcp_connector/exapp/middleware.py
    - src/mcp_connector/entry_exapp.py
    - src/mcp_connector/deps.py
    - vulture_whitelist.py
    - tests/unit/test_oauth_consent.py
    - tests/unit/test_oauth_provider.py
    - tests/unit/test_exapp_entry.py

key-decisions:
  - "The anti forgery value of the consent form is an HMAC of the flow id under the data key, not a column: it needs no migration, survives a restart and a second worker, and cannot be produced by anybody who is not this deployment"
  - "A denial deletes the authorization instead of marking it revoked, and hands the app password back to Nextcloud in one attempt without a retry"
  - "The authorization code is read without being consumed and is spent inside the exchange, in the one atomic statement of the store, so a failed PKCE check does not burn a code"
  - "auth_codes carries the redirect_uri_explicit flag, which is a schema addition with an idempotent ALTER for a development store file"
  - "The transport boundary resolves the Nextcloud identity of a verified token and deposits it in the request state; deps.py reads it instead of doing asynchronous work inside a synchronous tool call"
  - "No third MODE_ value: towards Nextcloud an app password is Basic authentication, so the OAuth branch builds MODE_BASIC credentials"
  - "load_access_token of the provider stays a refusal, because the SDK's ProviderTokenVerifier would bypass the cache, the audience check and the client policy"
  - "/token and /revoke are rebuilt with our own client authenticator, because the SDK compares a plaintext client secret and this store keeps a digest"

patterns-established:
  - "Derive what would otherwise need a column, when the value is a pure function of a key and an id"
  - "The boundary resolves, the tool call reads: asynchronous work belongs in front of the synchronous credential layer"
  - "A cache holds positive answers only, is keyed by a digest, has a hard ceiling and can be emptied in one call"

requirements-completed: []  # AUTH-03 and AUTH-07 both stay Pending, see the requirement note below
requirements-advanced: [AUTH-03, AUTH-07]

# Metrics
duration: 40 min
completed: 2026-08-16
---

# Phase 3 Plan 06: Consent, code exchange, token verifier and the fifth credential mode Summary

**The durchstich of the phase stands: a user approves on a page of this app, the client trades its code for an opaque token that is bound to this one server, and a tool call runs under the Nextcloud identity of the person who consented, without a single Nextcloud round trip in the token path.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-08-16T02:00:00Z
- **Completed:** 2026-08-16T02:37:00Z
- **Tasks:** 3 of 3 (all TDD, six commits)
- **Files created:** 3, modified: 13
- **New checks:** 69 (suite grew from 1137 to 1206)

## Accomplishments

- **The consent is an act of a person, and it produces exactly one code.** The screen of plan 03-05 grew the two submit buttons of one POST form, deny before approve in the markup, the initial focus on the heading rather than on the granting button, and a hidden value that binds the form to one authorization request. An approval writes one authorization code with a sixty second life, deletes the flow and redirects to the registered address with `code`, `state` and `iss`; `iss` is the mix-up protection of RFC 9207 and is the same value the metadata document already announced.
- **A denial takes the credential back.** The sign in of plan 03-05 creates the app password before anybody consents, because the poll of Login Flow v2 answers 200 exactly once. The deny path now reads that password, hands it back to Nextcloud with one `DELETE` and no retry, deletes the authorization row and the flow, and redirects with `error=access_denied`. A refused connection leaves nothing behind that could be used.
- **The anti forgery value needed no schema change.** It is an HMAC-SHA256 of the flow id under the data key of this installation, so it is unguessable without being this deployment, useless for another flow, identical across workers and restarts, and free of a column, a cache and a migration. It is compared with `compare_digest`, and a decision that fails the comparison lands on the same page an expired link gets, so the refusal is not an oracle.
- **A code becomes an opaque pair, and the audience is checked before anything is spent.** `exchange_authorization_code` refuses a grant without a resource and a grant for another resource with `invalid_target`, asks the client policy again because a block that arrived during the consent must not be outrun, and only then spends the code in the single atomic statement of the store. What comes back are two `secrets.token_urlsafe(32)` values, both stored as SHA-256 digests, both in one family, and a registration that produced them is marked as used so it lives on the long expiry window.
- **The token endpoint works for both kinds of client.** Public clients (Claude.ai and ChatGPT) authenticate by PKCE alone, exactly as the SDK does it. Confidential clients now work as well: `HashedClientAuthenticator` reads the presented secret in the method the registration asked for and compares its digest against the stored one, which is what plan 03-05 owed. `/token` and `/revoke` are rebuilt with it; everything else about them stays the SDK's handler, its CORS wrapper and its error shapes.
- **The transport boundary verifies against our own store and nothing else.** `oauth/verifier.py` looks a bearer up by digest, refuses unknown, expired, revoked, foreign audience and blocked client with one indistinguishable answer, and caches only positive results for five seconds under a hard ceiling of 1024 entries. A store that raises is a refusal and never a pass. `invalidate()` exists for the revocation path of plan 03-07 and empties the cache in the same process.
- **A tool call runs as the user who consented, and no tool module was touched.** The boundary resolves the authorization and its decrypted app password once per request and leaves it in the request state; `deps.resolve_credentials` reads it and builds `Credentials(..., mode=MODE_BASIC)`, because towards Nextcloud an app password is Basic authentication. `nextcloud/credentials.py` is unchanged, the branch is decided by the AppAPI user id alone, and there is no fallback in either direction (D-27).

## Task Commits

1. **Task 1: the decision of the user and the authorization code** (TDD)
   - `7f43e14` test: the failing checks for the decision, the code and the two result pages
   - `02b68a6` feat: the POST branch of the consent route, the form, `crypto.form_token`, the store helpers
2. **Task 2: code against token, and the verification of that token** (TDD)
   - `ad8fba4` test: the failing checks for the exchange, the verifier and the wiring
   - `0da2210` feat: `oauth/verifier.py`, the exchange, the client authenticator, the boundary and `entry_exapp`
3. **Task 3: the fifth credential mode** (TDD)
   - `cca9ee8` test: the failing checks for the credential mode and the docstring it describes
   - `51849b2` feat: the OAuth branch of `deps.py` and the rewritten module docstring

## Files Created/Modified

- `src/mcp_connector/oauth/verifier.py` - `StoreTokenVerifier` with the cache, the audience check and the policy check, `OAuthIdentity` with a masked repr, the `IdentitySource` protocol and the state key both sides of the hand over use.
- `src/mcp_connector/oauth/consent.py` - `_decide` with its five refusals, `_approve`, `_deny`, `_confirmed` and the code constant.
- `src/mcp_connector/oauth/provider.py` - `load_authorization_code`, `exchange_authorization_code`, `client_secret_hash`, `HashedClientAuthenticator` and the two rebuilt routes.
- `src/mcp_connector/oauth/store.py` - `form_token`, `load_auth_code`, `delete_authorization`, the `redirect_uri_explicit` column with its idempotent migration and one shared row builder.
- `src/mcp_connector/oauth/crypto.py` - `form_token`, an HMAC under a versioned label.
- `src/mcp_connector/exapp/ui/consent.py` - the decision form of S3, `connected_page` and `denied_page` of S4, and the four new parameter names.
- `src/mcp_connector/exapp/ui/layout.py` - `focus_heading`, which renders the heading with `tabindex="-1"` and `autofocus`.
- `src/mcp_connector/exapp/middleware.py` - the verified token is turned into an identity and deposited; the plan 03-01 paragraph about a missing verifier is now the description of the final behaviour.
- `src/mcp_connector/entry_exapp.py` - one policy, one store, one provider and one verifier, built before the boundary that needs them.
- `src/mcp_connector/deps.py` - `_credentials_from_oauth`, `_oauth_identity` and the rewritten module docstring.
- `vulture_whitelist.py` - `authenticate_request` (the SDK calls it) and `invalidate` (plan 03-07 calls it).

## Decisions Made

Beyond the frontmatter list, three worth naming here:

- **A GET on the consent surface still writes one row, and that is the shipped design, not a hole.** The plan asked that a GET never create an authorization. What a GET does create, since plan 03-05, is the authorization of a finished sign in, because the Login Flow v2 poll answers 200 exactly once and the app password would otherwise be lost. What it must never create is a grant, and that is what the test asserts in the form the threat model cares about (T-03-50): a GET that carries `decision=approve` and a valid anti forgery value renders the page, redirects nowhere and leaves every row of `flows`, `authorizations` and `auth_codes` byte for byte as it was.
- **The identity is resolved at the boundary, not in the credential layer.** The plan's key link says `deps.py` reads the authorization out of the store. It cannot: `resolve_credentials` is synchronous and is called from inside a tool, while reading the row and decrypting the app password is asynchronous work. So the asynchronous half runs once per request in the middleware and the synchronous half reads its result. The revocation case stays in `deps.py`, where it becomes a sentence a user can act on, and it is reachable exactly in the window in which the five second cache still holds a positive answer.
- **The code is read without being spent and spent inside the exchange.** The SDK checks the client, the deadline, the return address and the PKCE verifier between the load and the exchange. Spending the code at load time would burn a valid grant on a client that merely sent a wrong verifier once; spending it in the exchange keeps the single use exact, because the store does it in one `UPDATE` under `BEGIN IMMEDIATE`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The authorization code had nowhere to keep what the token endpoint compares**

- **Found during:** Task 2 (`load_authorization_code`)
- **Issue:** The SDK compares `redirect_uri_provided_explicitly` of the code against the token request, and the `auth_codes` table of plan 03-02 has no column for it. The flow record that knew it is deleted at the moment of approval. Guessing the flag would break one of the two client shapes: always `True` breaks a client that omitted `redirect_uri` at `/authorize`, always `False` breaks the normal case of Claude.ai and ChatGPT.
- **Fix:** `auth_codes` carries `redirect_uri_explicit INTEGER NOT NULL DEFAULT 1`, and `_add_missing_columns` adds it with one idempotent `ALTER TABLE` for a store file written by an earlier development build. Nothing is shipped yet, so this is a schema addition and not a migration of user data.
- **Files modified:** `src/mcp_connector/oauth/store.py`
- **Verification:** `test_a_code_is_loaded_with_everything_the_token_endpoint_compares`, plus the live walk below, where the SDK's own comparison passes.
- **Committed in:** `0da2210` (the column itself in `02b68a6`)

**2. [Rule 3 - Blocking] The store had no way to hand out an anti forgery value, and no way to delete an authorization**

- **Found during:** Task 1
- **Issue:** The plan asks for a value that is bound to the flow and remembered in the flow record, and for a denial that leaves no authorization. The `flows` table has no column for the first, and the store had no delete for the second, only `revoke_authorization`.
- **Fix:** Three small additions: `crypto.form_token` (HMAC under the data key), `OAuthStore.form_token` (the key holder hands it out, no I/O) and `OAuthStore.delete_authorization` (the cascade takes codes and tokens with it). `load_auth_code` came with task 2 for the reason above.
- **Files modified:** `src/mcp_connector/oauth/crypto.py`, `src/mcp_connector/oauth/store.py`
- **Verification:** `test_a_decision_without_the_anti_forgery_token_changes_nothing` (three shapes), `test_a_denial_answers_access_denied_and_hands_the_credential_back`
- **Committed in:** `02b68a6`

**3. [Rule 2 - Missing critical] The SDK client authenticator cannot authenticate against a digest**

- **Found during:** Task 2 (handed over by plan 03-05 as an open item)
- **Issue:** `ClientAuthenticator` compares `client.client_secret` in plaintext. This store keeps only `client_secret_hash`, so every confidential client would have been refused at `/token` and `/revoke`, and the endpoints would have stayed fail closed for them.
- **Fix:** `HashedClientAuthenticator` reads the presented secret in the registered method (`client_secret_basic` or `client_secret_post`, never one the client picks), compares `token_hash(presented)` against the stored digest with `compare_digest`, and refuses when the store cannot answer. `auth_routes` drops the SDK's `/token` and `/revoke` and rebuilds them with the same handlers and the same CORS wrapper.
- **Files modified:** `src/mcp_connector/oauth/provider.py`
- **Verification:** `test_a_confidential_client_authenticates_against_the_stored_digest`, `test_a_wrong_client_secret_is_a_401_and_no_token`, `test_a_confidential_client_without_its_secret_is_refused`
- **Committed in:** `0da2210`

**4. [Rule 3 - Blocking] The heading could not hold the initial focus**

- **Found during:** Task 1
- **Issue:** 03-UI-SPEC.md requires that the consent page opens with the focus on the heading and never on the approve button, and `layout.page` is the only place an `h1` is written.
- **Fix:** `page(focus_heading=True)` renders `tabindex="-1" autofocus` on the heading, and only the consent screen asks for it.
- **Files modified:** `src/mcp_connector/exapp/ui/layout.py`, `src/mcp_connector/exapp/ui/consent.py`
- **Verification:** `test_the_page_lands_on_its_heading_and_not_on_the_granting_button`
- **Committed in:** `02b68a6`

**5. [Rule 1 - Deviation from the plan text] The identity is deposited by the boundary, not read from the store by deps.py**

- **Found during:** Task 3
- **Issue:** The plan's key link has `deps.py` reading the authorization and the app password out of the store. `resolve_credentials` is synchronous and runs inside a tool call, so it cannot await a store read or a decryption.
- **Fix:** `oauth/verifier.resolve_identity` does that work at the transport boundary, once per request, and `deps.py` reads the result out of the request state. The rule the link stands for is unchanged: the identity comes from the authorization and from nothing else in the request.
- **Files modified:** `src/mcp_connector/exapp/middleware.py`, `src/mcp_connector/deps.py`, `src/mcp_connector/oauth/verifier.py`
- **Verification:** `test_the_durchstich_from_a_stored_token_to_the_credentials`, `test_a_verified_bearer_leaves_its_identity_for_the_credential_layer`
- **Committed in:** `0da2210` and `51849b2`

**6. [Rule 1 - Deviation from the plan text] A GET creates no grant, which is what the test asserts**

- **Found during:** Task 1
- **Issue:** The plan's behaviour "a GET never creates an authorization" contradicts the shipped, deliberate behaviour of plan 03-05, where the poll of a finished sign in writes the authorization on a GET because the 200 arrives exactly once.
- **Fix:** The check was written against the property the threat model owns: a GET carrying a decision and a valid anti forgery value changes not one row of the three tables and redirects nowhere. The reasoning is in "Decisions Made" above.
- **Files modified:** `tests/unit/test_oauth_consent.py`
- **Verification:** `test_a_get_never_grants_anything_whatever_it_carries`
- **Committed in:** `7f43e14`

---

**Total deviations:** 6 auto-fixed (2 blocking schema or API gaps, 1 missing critical, 1 blocking UI capability, 2 deviations from the plan text)
**Impact on plan:** No scope creep and no new dependency. The one addition with production weight is the `redirect_uri_explicit` column, which is what makes the SDK's own redirect comparison work after the flow record is gone.

### Requirement Status

**AUTH-03 and AUTH-07 both stay Pending.** AUTH-03 is the statement that a client connects end to end against a real Nextcloud; every part of it now exists and is proven in process, but the live proof is plan 03-08 and the two connectors are plan 03-09. AUTH-07 names four enforcement points and this plan builds the last two (`exchange_authorization_code` and `verify_token`); what is still missing for the requirement as written is the revocation path of plan 03-07, without which "a blocked client stops working" has no way to be triggered by an administrator at runtime. `REQUIREMENTS.md` is unchanged.

## Issues Encountered

- **TDD gates versus the "all gates before every commit" rule.** The three RED commits contain tests that fail by construction and import a module that does not exist yet, so pyright cannot be green on them. Lint and format were run and passed on all three; every GREEN commit passes all six gates. Same documented tension as in 03-01, 03-03, 03-04 and 03-05.
- **One store method with a one commit lifetime.** `load_auth_code` was written in task 1 and had no production caller until task 2, where `load_authorization_code` uses it. It was moved into the task 2 commit rather than whitelisted, because a whitelist entry for a two hour gap is worse than one commit boundary in a different place.
- **The dead code gate cannot see two SDK call sites.** `authenticate_request` and `invalidate` are called by the SDK handlers and by plan 03-07 respectively, and both got a whitelist entry with that reason.

## Known Stubs

Two, both named in the plan and both owned by plan 03-07:

- **The refresh rotation refuses.** `load_refresh_token` and `exchange_refresh_token` still answer with the fail closed shape, although a refresh token is now issued with every exchange. A client that tries to refresh gets `invalid_grant` until 03-07.
- **`revoke_token` does nothing.** RFC 7009 requires a 200 for a token the server does not know, which is what the endpoint answers today. The real revocation, the family kill and the app password deletion behind it are 03-07, and `verifier.invalidate` is the hook waiting for it.

## Threat Flags

None. This plan added no route, no public surface and no outbound call; the manifest is unchanged.

## Verification Evidence

- Full suite: **1206 passed, 76 deselected** (from 1137), without Docker and without network. `test_oauth_consent.py` 38, `test_oauth_verifier.py` 25, `test_oauth_provider.py` 39, `test_oauth_credentials.py` 13, `test_exapp_entry.py` 42.
- Gates on the final tree, each on its own exit code: `ruff check .` 0, `ruff format --check .` 0, `pyright` 0 errors, `vulture src scripts vulture_whitelist.py` 0, `pytest` 0, `scripts/check_tool_budget.py` 0 (10642 of 12500 bytes, 15 tools).
- Acceptance greps: `compare_digest` in `oauth/verifier.py` 2, `"is not read"` in `deps.py` 0, `MODE_` in `nextcloud/credentials.py` 6 (unchanged against `48359fd`), `<script` in `exapp/ui/consent.py` 0.
- **The whole flow, live in one process, without a network** (registration, `/authorize`, a mocked Login Flow v2, the consent POST, `/token`, the verification and the credentials of a tool call):
  1. `/authorize` answers 302 to `https://cloud.example.com/exapps/mcp_connector/authorize/consent?flow=...`
  2. the consent screen renders with exactly two buttons
  3. approve answers 302 to `https://claude.ai/api/mcp/auth_callback?code=KOpS8_TM...&state=state-1&iss=https%3A%2F%2Fcloud.example.com%2Fexapps%2Fmcp_connector`
  4. `/token` answers 200 with `token_type=Bearer`, `expires_in=3600`, `scope=nextcloud` and a refresh token
  5. the verifier answers `subject=alice`, `resource=https://cloud.example.com/exapps/mcp_connector/mcp`, `client=claude-1`, and `None` for a token it never issued
  6. `deps.resolve_credentials` answers `Credentials(base_url='http://nc.test', user='alice', mode='basic', secret='***')`, and the secret is the app password of that connection

## Next Phase Readiness

- **Ready for 03-07:** the refresh token of every connection exists with its family, `store.redeem_refresh_token` and `store.revoke_family` are in place and covered, `verifier.invalidate` is the cache hook, and `deps.py` already answers a revoked authorization with a sentence a user can act on. The abandoned authorizations of a sign in nobody finished are still the sweep 03-07 owes.
- **For 03-08:** the live proof of this plan is one browser session against the staging instance: walk `/authorize`, sign in, press "Approve access", watch the client come back with a code, and read one tool answer as the signed in user. The second run is the same with "Deny access", where the entry in "Devices and sessions" has to disappear again.
- No blockers. Nothing in this plan needs a running Nextcloud, a container or a network.

---
*Phase: 03-oauth-2-1, Plan: 06*
*Completed: 2026-08-16*

## Self-Check: PASSED

All three created files exist on disk, all six commits are in the history (`7f43e14`,
`02b68a6`, `ad8fba4`, `0da2210`, `cca9ee8`, `51849b2`), every acceptance criterion of the
three tasks was executed as a command and passed, and the plan level verification was
re-run on the final tree: 1206 checks in the suite, all six gates clean, and the whole
flow walked live in one process from the authorization request to the credentials of a
tool call.
