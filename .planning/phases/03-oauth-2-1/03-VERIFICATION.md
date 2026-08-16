---
phase: 03-oauth-2-1
verified: 2026-08-16T09:10:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
concerns:  # not gaps: none of these blocks the phase goal, all are named for phase 4/5
  - id: C-01
    about: "AUTH-04 (SC 1 and SC 2) rests on an owner run that cannot be repeated after the staging teardown"
    detail: "The only record is prose in 03-09-MEASUREMENTS.md and docs/oauth-setup.md. No access log excerpt, HAR or screenshot was archived. Corroborated server side by this verification, not reproduced."
  - id: C-02
    about: "WR-09 stays open and is the one open finding that touches the goal"
    detail: "entry_exapp.main has no guard for a missing NC_MCP_PUBLIC_URL; an ExApp installed without it starts green and sends every client to http://127.0.0.1:8765. Close before Phase 5 SC 2 (install per click on a clean instance)."
  - id: C-03
    about: "The Phase 2 risk register was not updated by this phase"
    detail: "02-SECURITY.md still carries AR-02-06 as an open work order (it is closed, verified live) and AR-02-04 still justifies itself with '/mcp bleibt USER', which stopped being true in plan 03-01."
  - id: C-04
    about: "ROADMAP bookkeeping lags the work"
    detail: "03-09-PLAN.md is still unchecked in ROADMAP.md while its SUMMARY exists and AUTH-04 is checked off in REQUIREMENTS.md."
---

# Phase 3: OAuth 2.1 Verification Report

**Phase Goal:** MCP-Clients verbinden plug-and-play per spec-konformem OAuth 2.1, mit Login
Flow v2 als Fallback für Clients ohne OAuth.
**Verified:** 2026-08-16T09:10:00Z
**Status:** passed (with the four concerns above; none of them blocks the goal)
**Re-verification:** No, initial verification

## Goal Achievement

This verification did not rely on the nine SUMMARY files, on 03-REVIEW.md or on
03-09-MEASUREMENTS.md. The HaRP topology of `compose.exapp.yml` was brought back up in this
session, the app was rebuilt from the tree at `f8a516d` and deployed through AppAPI
(`nc_app_mcp_connector`, healthy), and the whole OAuth flow, the browser onboarding, the
revocation and the throttle were driven against that running chain. The public staging
instance was used read only for discovery and 401 checks. The owner instance `nc-mcp-test`
(port 8080) and `findling-nextcloud` (8090) were not touched and are both still up.

One class of evidence could not be reproduced by this gate and is not reproducible by
anyone after today: the two hosted connector runs of AUTH-04 (Claude.ai, ChatGPT) against
`https://nc-staging.infranode.dev`. What could be checked about them from the outside was
checked, and it all lines up (see SC 1/SC 2 below and C-01).

### Observable Truths (ROADMAP Success Criteria, Phase 3)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Der Claude.ai-Connector verbindet plug-and-play gegen eine öffentlich erreichbare Staging-Instanz: URL eintragen, Browser-Login mit Consent, Tools nutzbar, ohne manuelle Client-Konfiguration | VERIFIED (owner run of 2026-08-16, corroborated server side in this session; not independently reproducible, see C-01) | The run itself is recorded with its access log chain, the issued client id, the redirect URI `https://claude.ai/api/mcp/auth_callback`, 15 tools and per endpoint timings (03-09-MEASUREMENTS.md run 1, docs/oauth-setup.md "End to end with hosted connectors"). What this session could verify from outside, read only: `https://nc-staging.infranode.dev/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp` -> `200` with `authorization_servers:["https://nc-staging.infranode.dev/exapps/mcp_connector"]`; the AS document at the canonical root path -> `200` (so the Caddy rewrite rules really were restored after run 3, as the record claims); the OIDC style fallback below the issuer -> `200` (the path run 3 says Claude settles on); anonymous `POST /mcp` -> `401` with `Www-Authenticate: Bearer ... resource_metadata="…/.well-known/oauth-protected-resource/mcp"`, which is step 1 of the recorded chain. DCR is on by default in code (`registry.client_policy`, `NC_MCP_OAUTH_DCR` default true), which is what "ohne manuelle Client-Konfiguration" needs. The same flow was walked end to end locally in this session (`scripts/oauth_flow_check.py`: register 201, authorize 302, consent 200, decide 200, token 200, `tools=15`, tool call as alice 200). |
| 2 | Der ChatGPT-Connector verbindet ebenso Ende-zu-Ende gegen dieselbe Staging-Instanz (PRM, Dynamic Client Registration, PKCE S256, Audience-Binding komplett) | VERIFIED (owner run, corroborated; see C-01) | Recorded in 03-09-MEASUREMENTS.md run 2 including the failure that preceded it (`invalid_scope`) and the three fix commits. Those commits are real code, not documentation: `git show 5793fc3` adds `REGISTERED_SCOPE` in `oauth/metadata.py`, overwrites the registration scope in `provider.register_client` and adds four HTTP level regression tests; `8724d57` normalises rows written before the fix in `_client_information`. The live staging metadata now advertises `scopes_supported:["nextcloud","offline_access"]` and `grant_types_supported:["authorization_code","refresh_token"]` (fetched read only in this session), i.e. the instance carries the fixed build. Spec surface verified in code and by the local run: `code_challenge_methods_supported:["S256"]` only, `resource` (RFC 8707) required at `/authorize`, re-checked at code exchange, at refresh and again in the token verifier (`provider.py:431,542,675`, `verifier.py:210`), `authorization_response_iss_parameter_supported: true` and `iss` present on the way back (local probe step 5). |
| 3 | Nutzer ohne OAuth-fähigen Client onboarden sich per Login Flow v2 im Browser; der Client sieht nie das echte Passwort | VERIFIED, reproduced live in this session | `scripts/oauth_flow_check.py --measure` against the running topology: `GET /connect -> 200`, `POST /connect -> 200`, `GET /connect/wait -> 400` for the caller that started the flow but holds no Nextcloud account (CR-01 relay refused, credential handed back), `GET /connect/wait -> 200 | signed_in_as=alice | credential=72 characters, shown once`, the same address again `-> 400 | credential_shown_again=False`, and `POST /mcp -> 200 | auth=the credential from the page | server=uvicorn`. The sign in itself happens on Nextcloud's own pages: `oauth/loginflow.py` drives the Login Flow v2 poll endpoint, no module under `src/` contains a password prompt or a login automation, and the app password is what comes back. The invitation page renders with `Content-Security-Policy: default-src 'none'; style-src 'nonce-…'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'`, `no-store`, `X-Frame-Options: DENY` (curl in this session). |
| 4 | Token-Widerruf wirkt sofort: Ein widerrufener Client erhält 401 mit korrektem WWW-Authenticate-Header und kann sich sauber neu verbinden | VERIFIED, reproduced live | `pytest tests/integration/test_oauth_flow_exapp.py -m integration` -> **6 passed** in this session, including `test_a_revocation_is_a_401_with_the_same_pointer_and_a_reconnection_works` (the 401 after the revocation is byte for byte the one an anonymous request gets, and a complete new connection is built right afterwards). Immediacy is structural, not swept: an access token's validity is a join on the authorization row (`verifier.py:208`), and the process cache is invalidated on revocation. The second half of D-34, that the revocation also hands the Nextcloud app password back, was measured independently here: the set of `MCP Connector` entries in `occ user:auth-tokens:list alice` was identical before and after a full probe run that creates one connection and revokes it (46 entries, no id added, none removed). Measured twice, in two separate runs, with the same result. |
| 5 | Wiederholte fehlgeschlagene Auth-Versuche drosseln die Nextcloud-Instanz nicht (keine Auth-Retries, Validierungs-Cache, handlungsfähige 401/429-Meldungen) | VERIFIED, reproduced live, with one honest residual | Measured in this session, identical to the documented numbers: `5 accepted MCP calls -> 6 Nextcloud requests (1.2 per call)`, `5 refused MCP calls -> 5 Nextcloud requests (1.0 per call)`, and the single request per call is HaRP's own `GET /index.php/apps/app_api/harp/user-info`, not ours. `POST /token -> 429 | attempts=11 | retry_after=300`, and immediately afterwards the throttled user still signs in normally (`GET /ocs/v2.php/cloud/user -> 200 | as_user=alice`), so no brute force lockout is produced. No retry loop exists in the two files that decide about a token: the source gate `test_the_comparisons_are_constant_time_and_no_loop_talks_to_nextcloud` parses `provider.py` and `verifier.py` and refuses `while`, `range(` and `sleep`. Validation cache: five second positive-only process cache in `verifier.py`. Residual, deliberate and documented: the `/mcp` route carries no throttle at all (throttling tool calls would be this server's own denial of service), so an anonymous flood there still costs one HaRP lookup per request. `docs/oauth-setup.md`, "Security notes for production", states exactly this. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/oauth/metadata.py` (202 lines) | PRM (RFC 9728), AS metadata (RFC 8414), openid-configuration variant, scope constants | VERIFIED, WIRED | All three documents answer `200` on the HaRP path, on the PHP proxy path and (with the optional rewrite) on the canonical root path; local probe step 2 reports they are byte for byte identical over both proxy paths |
| `src/mcp_connector/oauth/provider.py` (1333 lines) | The authorization server: authorize, code exchange, refresh rotation, revocation, DCR policy, audience binding | VERIFIED, WIRED | Live flow: register 201, authorize 302, decide 200, token 200. Audience checked at three points plus the verifier; `S256` only; exact redirect matching; `register_client` refuses non https / non loopback addresses (this is what refuses Cursor, by design) |
| `src/mcp_connector/oauth/store.py` (1223 lines), `crypto.py` (374) | SQLite in the persistent volume, AES-GCM with `aad` = row id, data key in the ExApp config marked sensitive (D-43) | VERIFIED, WIRED | `encrypt(..., aad=flow_id)` / `aad=auth_id` at the four call sites; `test_the_same_token_still_works_after_the_container_restarted` passed live, which is the proof that store and key survive a cold container |
| `src/mcp_connector/oauth/verifier.py` (288 lines) | Validation against the own store, five second cache, audience check, fourth AUTH-07 enforcement point, fail closed | VERIFIED, WIRED | Every failure path returns `None`, never an exception; identity resolution is read fresh per request and never cached, which is what makes a revocation land inside the cache window |
| `src/mcp_connector/oauth/throttle.py` (377 lines) | Path classes, per source limits, `429` with `Retry-After`, counting creations and not only refusals (CR-02) | VERIFIED, WIRED | `CLASS_CONNECT_START` and `CLASS_AUTHORIZE_START` exist and are the CR-02 fix; live `429 | retry_after=300` after 11 token attempts; a second probe run in this session was itself refused by the throttle, which is the strongest possible proof that it is armed |
| `src/mcp_connector/oauth/loginflow.py`, `connect.py`, `consent.py` | Login Flow v2 relay, onboarding pages, consent screen, decide route with the CR-01 identity check | VERIFIED, WIRED | Live: `/authorize/decide -> 400 | identity=none`, `-> 200 | identity=the session cookie of the sign in`; `/connect/wait` behaves the same way |
| `src/mcp_connector/exapp/middleware.py` (167 lines) | Bearer boundary in front of `/mcp`, fail closed without a verifier, 401 with the `resource_metadata` pointer | VERIFIED, WIRED | Anonymous and bogus bearer both `401` with the full challenge, on staging and locally |
| `src/mcp_connector/exapp/ui/*` (7 error pages, layout, strings) | One rendering function, CSP with nonce, no-store, no reflected secrets | VERIFIED, WIRED | Pages render live with the strict CSP; a bogus `flow` on the consent route renders error copy and `400`, not a traceback |
| `appinfo/info.xml` | Twelve narrow routes, `^/\.well-known/` gone (AR-02-06), four env variables declared | VERIFIED | Manifest read; live on staging: the three declared well-known documents answer `200`, while `/.well-known/`, `/.well-known/oauth-authorization-server.evil`, `/.well-known/openid-configuration/foo` and the Phase 2 probe path all answer **404**. In Phase 2 that probe path answered `401`, i.e. it was reachable; it is not any more. Lifecycle paths `heartbeat`/`init`/`enabled` -> `502`, still undeclared |
| `tests/unit/test_oauth_*.py` (~5300 lines over 10 files) | The D-40 abuse matrix and the unit surface | VERIFIED, GREEN | `pytest` -> **1396 passed, 82 deselected** in this session. The D-40 list is covered one to one: refresh replay kills the family, retry window keeps the connection, revoked client gets 401 and can reconnect, foreign `redirect_uri` refused, PKCE downgrade produces no code, audience mismatch refused at authorize and at the boundary, DCR off names the reason, allowlist blocks at authorize **and** at token |
| `tests/integration/test_oauth_flow_exapp.py` (480 lines) | The same questions over the real chain | VERIFIED, GREEN | Re-executed live: **6 passed** |
| `scripts/oauth_flow_check.py` (896 lines) | The repeatable full flow probe | VERIFIED, GREEN | Executed twice in this session, plain and `--measure`, exit 0 both times |
| `compose.staging.yml`, `deploy/Caddyfile.staging`, `scripts/setup_staging.sh`, `scripts/staging_dns.sh`, `docs/staging-setup.md` | A public instance that can be built and torn down | VERIFIED (present, and the instance they built is live) | Read only checks against `https://nc-staging.infranode.dev` all answer as the runbook describes |
| `docs/oauth-setup.md` (708 lines), `docs/client-setup.md` | Admin setup, the evidence sections, the hosted connector section, per client walkthroughs | VERIFIED | Every reproducible number in the evidence sections was re-measured in this session and matched exactly (round trips, throttle threshold, `Retry-After`, tool count, the `/connect` sequence) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| MCP client (bearer) | `/mcp` | HaRP -> `RequireAppApi` -> `StoreTokenVerifier` -> `deps._credentials_from_oauth` | WIRED | Live tool call as alice with a token that came out of the flow; permission fidelity re-run green |
| `/authorize` | Nextcloud Login Flow v2 | `oauth/loginflow.start_flow`, poll token encrypted in the store | WIRED | Live 302 to the consent screen, one poll, sign in on Nextcloud's pages |
| `/authorize/decide` | the signed in Nextcloud account | `AUTHORIZATION-APP-API` resolved by HaRP, compared with the account of the sign in | WIRED | Live 400 without identity, 200 with the session cookie of that sign in (CR-01) |
| `/token` | store + rotation | `exchange_authorization_code`, `exchange_refresh_token` under `BEGIN IMMEDIATE` | WIRED | Live 200 with `access_token, expires_in, refresh_token, scope, token_type` in 40 ms |
| `/revoke` | Nextcloud app password | `_end_connection` -> `store` -> OCS delete | WIRED | Measured: the connection's app password is gone from `occ user:auth-tokens:list` after the revoke |
| Client policy (AUTH-07) | authorize, token, register, live tokens | `ClientPolicy.allows` in `get_client` + `register_client`, plus `verifier` | WIRED | Four enforcement points present in code, covered by the abuse suite; the delivery path of the switches is proven live (`NC_MCP_PUBLIC_URL` is injected into the container exactly because the manifest declares it) |
| `appinfo/info.xml` routes | HaRP access levels | twelve anchored routes, all PUBLIC, own checks behind them | WIRED | 404 on every undeclared neighbour, 502 on the lifecycle paths, 401/200 on the declared ones |

### Data-Flow Trace (Level 4)

The dynamic values of this phase are the discovery documents, the tokens and the identity
behind a token. All three were traced to a real source rather than a constant:

- The PRM/AS documents on staging name `https://nc-staging.infranode.dev/...`, i.e. the
  configured `public_url` of that deployment, while the local instance names
  `http://127.0.0.1:8081/exapps/mcp_connector`. Same code, two deployments, two answers.
- A token issued by the running container serves a tool call, survives a `docker restart`
  of that container and stops working the moment it is revoked. That rules out a
  hardcoded or in-memory-only credential.
- The identity behind the token resolves to the real Nextcloud account: the probe's
  `notes_create` lands as `alice` and appears in her notes; bob's token reaches nothing of
  hers (`test_two_tokens_stay_two_accounts_over_the_whole_chain`).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full unit suite | `uv run --no-sync pytest` | `1396 passed, 82 deselected` | PASS |
| OAuth over the real chain | `pytest tests/integration/test_oauth_flow_exapp.py -m integration` | `6 passed` | PASS |
| Phase 2 regression (permission parity, DAV matrix) | `pytest tests/integration/test_permission_fidelity_exapp.py tests/integration/test_exapp_dav_matrix.py -m integration` | `22 passed` | PASS |
| Full flow probe | `python scripts/oauth_flow_check.py http://127.0.0.1:8081/exapps/mcp_connector` | exit 0, all seven steps | PASS |
| Flow probe with SC 3 and SC 5 | same, `--measure` | exit 0, numbers match the docs exactly | PASS |
| Revocation returns the app password | `occ user:auth-tokens:list alice` before/after a probe run, twice | 46 before, 46 after, no id added or removed, both runs | PASS |
| Staging PRM / AS / OIDC documents | `curl` (read only) | `200`, `200`, `200`, issuer and resource correct | PASS |
| Staging `/mcp` anonymous and with a bogus bearer | `curl -X POST` | `401` + full `WWW-Authenticate` with `resource_metadata`, `no-store` | PASS |
| AR-02-06 hardening on staging | `curl` on four undeclared well-known paths | `404` each (was `401` in Phase 2) | PASS |
| Lifecycle paths still unreachable | `curl heartbeat/init/enabled` on staging | `502` each | PASS |
| Lint / format / types / dead code | `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` | clean, `143 files already formatted`, `0 errors`, exit 0 | PASS |
| Owner instances untouched | `docker ps` | `nc-mcp-test` up 29 h, `findling-nextcloud` up 21 h | PASS |

### Probe Execution

The project uses no `scripts/*/tests/probe-*.sh` convention. Its equivalent is
`scripts/oauth_flow_check.py` plus the two integration suites, and all three were executed
by this gate in its own process rather than read from a SUMMARY (see the table above). The
one probe that could not be executed here is the hosted connector run of plan 03-09: it
needs a human at a Claude.ai and a ChatGPT account, and running it was explicitly out of
scope for this gate.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AUTH-02 | 03-04 | Onboarding per Login Flow v2, Client sieht nie das echte Passwort | SATISFIED | SC 3 above, reproduced live; no password prompt anywhere under `src/` |
| AUTH-03 | 03-01, 03-05, 03-06, 03-07 | OAuth 2.1 nach MCP-Spec: PRM (RFC 9728), DCR, PKCE S256, Widerruf | SATISFIED | SC 2 and SC 4 above; the full flow ran end to end in this session |
| AUTH-04 | 03-09 | Claude.ai und ChatGPT verbinden nachweislich gegen eine öffentliche Staging-Instanz | SATISFIED, with C-01 | Owner run of 2026-08-16, recorded with access log chains, client ids, redirect URIs and timings; corroborated from the outside in this session. The requirement is an owner action by D-39 and its evidence is a record, not a test |
| AUTH-07 | 03-05 | Admin steuert, welche OAuth-Clients sich verbinden dürfen; DCR global abschaltbar | SATISFIED | `ClientPolicy` with the three switches, enforced at four points, covered by the abuse suite (`allowlist` refuses at authorize and at token, `dcr=off` names the reason and removes the route). The switches are declared in `appinfo/info.xml`; the injection path of such a declaration is proven live for `NC_MCP_PUBLIC_URL` |

No orphaned requirements: ROADMAP Phase 3 lists AUTH-02, AUTH-03, AUTH-04 and AUTH-07, and
each is claimed by at least one plan. The staged bookkeeping in this phase was unusually
careful: plans 03-01, 03-02 and 03-03 deliberately reverted the automatic completion of
AUTH-02/AUTH-03 and left them `Pending` until the plan that actually closed them, which was
spot-checked against `.planning/REQUIREMENTS.md` and holds.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TODO`, `TBD`, `FIXME`, `XXX`, `HACK`, `PLACEHOLDER`, "not yet implemented" over `src/`, `scripts/`, `appinfo/`, `deploy/` and the three phase documents | none found | — |

Debt marker gate: clean, zero matches. The `vulture` run over `src scripts` is also clean,
so there is no dead OAuth code left behind, with one caveat the review itself names
(IN-01: the `cancel` branch of `/connect` is implemented and tested but no page renders a
button for it; it is reachable code with an unreachable trigger, not dead code by
`vulture`'s definition).

### Open findings from 03-REVIEW.md, and whether they touch the phase goal

Verified against the code rather than against the review's own status line. The three
blockers and eight warnings marked resolved are genuinely resolved: CR-01 by the
`/authorize/decide` route with the identity comparison (observed live, both branches),
CR-02 by the two creation path classes in `throttle.py`, CR-03 by the decision answering
200 with a navigating page (and the browser cross check that CR-03 left open was made in
run 1 on staging: Chrome returned to `claude.ai?step=success`, `form-action 'self'` blocked
nothing).

The ten open findings, each judged against the goal:

| Finding | Still open in the code? | Touches the phase goal? |
|---------|------------------------|-------------------------|
| WR-08, refused-client pages echo an attacker supplied `client_id` | yes | **No.** Reachable only with `allowlist_only=on` or `dcr=off`, i.e. configurations in which no connector connects anyway. It is a trust-surface issue for the store release, not a connection issue |
| WR-09, missing `NC_MCP_PUBLIC_URL` degrades to `http://127.0.0.1:8765` | yes, confirmed: `entry_exapp.main` fails closed for the volume and for an unusable issuer but not for this one, and there is not even a warning | **Closest of the ten.** It cannot break a correctly configured install, and every install path in this repo sets it, so SC 1/SC 2 are not affected. But an admin who forgets it gets a green start and a connector that can never connect, with no line naming the cause. Close it before Phase 5 SC 2 |
| WR-10, `_client_information` takes a `client_id` it never compares | yes, confirmed (the parameter is still unused for its comparison) | **No.** Not exploitable while the SDK mints the id and `register_client` writes key and JSON from one object. Latent |
| WR-12, `POST /connect` has no anti forgery value | yes | **No.** Forced state creation only, no credential leak, and CR-02 now bounds it at 20 per source per five minutes |
| IN-01 unreachable cancel action, IN-02 `_has_expired` ignores the injected clock, IN-04 two definitions of a safe client name, IN-05 handoff link without the host check, IN-06 a comment that overstates `compare_digest` | yes | **No.** Consistency and testability, none of them on a connect path |
| IN-03, `revocation_endpoint_auth_methods_supported` does not advertise `none` | yes, confirmed on the live staging document | **Edge of SC 4 only.** The endpoint does accept public clients; the document understates it, so a strict public client could conclude it cannot revoke. Revocation by the user in Nextcloud and by a confidential client both work, which is what SC 4 asks for |

None of the ten is a blocker for this phase. WR-09 and IN-03 are the two worth carrying
forward as named items rather than as background noise.

### Human Verification Required

None outstanding. The one human-only item of this phase, AUTH-04, was executed by the owner
on 2026-08-16 before this gate and its record is in the repository; asking for it again
would mean asking for a run against an instance that is being torn down today. Everything
else that a human would normally have to look at (the consent screen, the onboarding pages,
the browser behaviour of the decision under `form-action 'self'`) was either rendered and
checked here or measured in a real Chrome during run 1.

### Gaps Summary

No gaps. All five success criteria hold, three of them (SC 3, SC 4, SC 5) reproduced from
scratch in this session against a freshly deployed container, and two of them (SC 1, SC 2)
resting on an owner run whose every externally checkable consequence was verified.

What a reader of this phase could still be misled about, and should not be:

1. **AUTH-04 is a record, not a test.** Nothing in the repository re-runs it, and after the
   staging teardown nothing can. The record is unusually good (access log chains, client
   ids, per endpoint timings, a failure of our own that was found and fixed, a counter
   measurement that overturned the first reading of A2), and this gate could confirm every
   server side trace of it. But no raw log excerpt, HAR or screenshot was archived, so the
   evidence is ultimately testimony plus corroboration. If the store submission is ever
   questioned on this point, there is no artefact to hand over. Archiving fifteen lines of
   the access log would have closed that, and is worth doing for the Phase 5 client matrix.
2. **"Plug and play" is true for the two connectors that were measured, not for every
   client.** Cursor is refused today, and by our own rule (private-use URI schemes are not
   admitted, and one inadmissible entry sinks the whole registration). That is documented
   in `docs/oauth-setup.md`, `docs/client-setup.md` and BL-04, and it is correctly excluded
   from AUTH-04 — but Phase 5 SC 4 names Cursor explicitly, so the decision in BL-04 has to
   be taken there rather than inherited silently.
3. **The `/mcp` route is PUBLIC and unthrottled since plan 03-01.** That is a deliberate,
   well argued trade (the discovery 401 has to come from the app, and rate limiting tool
   calls would be self denial of service), and the app's own bearer boundary replaced what
   the access level used to provide. Two Phase 2 documents were not updated to match:
   `02-SECURITY.md` still justifies AR-02-04 with "/mcp bleibt USER", and AR-02-06 still
   reads as an open work order there although it is closed and was verified closed live
   here (404 on every undeclared well-known neighbour).
4. **ROADMAP.md still shows plan 03-09 as unchecked** while its SUMMARY exists and AUTH-04
   is checked off in REQUIREMENTS.md. Bookkeeping only, but the phase looks 8/9 done in the
   one file a reader opens first.

One operational finding from reproducing the topology, worth a line in the runbook: with
the HaRP container recreated, the shared key in `.env.exapp` no longer matched the one
stored with the registered deploy daemon, and every AppAPI docker call answered 401, which
surfaces as an ExApp that is `[enabled]` in `occ app_api:app:list` while no container
exists and every route answers 503. `occ app_api:daemon:unregister harp_proxy_docker`
followed by `bash scripts/bootstrap_exapp.sh` fixes it. Related: `scripts/bootstrap_exapp.sh`
must be run with `.env.exapp` sourced, otherwise `docker compose` refuses on the required
`HP_SHARED_KEY`, the error is swallowed by `2>/dev/null` in the wait loop and the script
reports "Nextcloud is still not installed after five minutes" against a perfectly installed
Nextcloud.

---

_Verified: 2026-08-16T09:10:00Z_
_Verifier: Claude (gsd-verifier)_
_Method: live re-deployment of the HaRP topology from `f8a516d`, 1396 unit tests, 28 integration tests, two full flow probe runs, read only checks against the public staging instance_
