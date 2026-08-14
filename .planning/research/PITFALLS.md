# Pitfalls Research

**Domain:** Nextcloud MCP-only ExApp (Python, MCP SDK ~1.27, OAuth 2.1, App Store distribution)
**Researched:** 2026-08-14
**Confidence:** HIGH for MCP/OAuth and certification-process findings (official docs, live GitHub data, own InfraNode measurements); MEDIUM for some Nextcloud API edge cases (community reports)

## Critical Pitfalls

### Pitfall 1: OAuth discovery misimplementation silently breaks Claude.ai / ChatGPT connectors

**What goes wrong:**
The server "works" in MCP Inspector and Claude Code but the Claude.ai / ChatGPT web connector fails with "Couldn't reach the MCP server" or "Authorization with the MCP server failed". The OAuth flow never starts or dies mid-flow. This is the single most reported failure class for custom connectors.

**Why it happens:**
The MCP Authorization spec chains several RFCs and clients probe them in a strict order. Any missing piece aborts the flow:
- 401 responses without a `WWW-Authenticate` header carrying a `resource_metadata` pointer
- `/.well-known/oauth-protected-resource` (RFC 9728) missing, or missing the path-suffixed variant (`/.well-known/oauth-protected-resource/mcp` when the endpoint is `/mcp`)
- No authorization server metadata (RFC 8414 or OIDC discovery), or no way to obtain a client identity: no RFC 7591 Dynamic Client Registration, no CIMD, no pre-registered client
- PKCE S256 not implemented or not advertised via `code_challenge_methods_supported: ["S256"]`
- RFC 8707 `resource` / audience mismatch: Claude sends the canonical MCP server URL (lowercase, no trailing slash, includes path) as `resource`; tokens must be audience-bound to exactly that and the server must accept the canonical form
- Token endpoint slower than 10 seconds (Claude's hard timeout)
- A 3xx redirect on the registered URL (apex to www, reverse-proxy canonicalization) drops the `Authorization` header, so the target sees an unauthenticated request

**How to avoid:**
Implement the full discovery chain as its own deliverable, not as a byproduct of "add OAuth". Test with the exact curl checklist from Claude's troubleshooting doc: protected-resource metadata (with and without path suffix), one of the two AS metadata endpoints, `registration_endpoint` present, PKCE S256 advertised. Register the final non-redirecting URL. Keep the token handler fast (no synchronous Nextcloud round trips inside `/token`). Test from a public network, not from inside the LAN (claude.ai resolves DNS itself and rejects private / CGNAT / IPv6-only hostnames before any request is sent).

**Warning signs:**
"Works in Inspector, fails on claude.ai"; server access logs show nothing during a Connect attempt (DNS/private-IP rejection); edge logs show 403/429 the app never generated (WAF); `curl -sI` on the MCP URL returns 3xx.

**Phase to address:**
OAuth/Auth phase. Make "Claude.ai connector connects end-to-end against a public test instance" an explicit success criterion, plus ChatGPT connector as a second client.

---

### Pitfall 2: Session-state assumptions in Streamable HTTP (the context_agent#227 failure, and its mirror image)

**What goes wrong:**
Two symmetric failure modes. (a) context_agent runs `stateless_http=True`, so the transport terminates the session after every request; MCP SDK >= 1.28 clients keep the session and their `tools/list` after `initialize` fails with "Session terminated" (issue #227, still open, no fix). (b) The opposite: a stateful server behind a load balancer or restarted container returns 404 "Session not found" for valid `Mcp-Session-Id` headers because the new instance has no session record.

**Why it happens:**
Session semantics changed across MCP spec revisions (2026-07-28 made stateless the core), SDK defaults differ per version, and developers pick a transport flag without deciding what state their tools actually need.

**How to avoid:**
Decide once, architecturally: no tool depends on session state. Pagination via opaque handles/cursors encoded in the tool response, per-user context derived from the OAuth token on every request, no in-memory per-session caches that affect correctness. Then the transport flag is a compatibility knob, not a correctness knob. Pin `mcp[cli] ~1.27` (project decision) and add an integration test with an SDK >= 1.28 client to catch exactly the #227 class of breakage before users do. On restart/redeploy, clients must be able to re-initialize transparently.

**Warning signs:**
Any tool implementation reading from a dict keyed by session ID; "Session terminated" or 404 errors in client logs after the first request; behavior differs between first and second call of the same tool.

**Phase to address:**
MCP core phase (architecture decision + client-matrix integration test). The context_agent#227 contribution fix doubles as forced learning here; do it early.

---

### Pitfall 3: Schema bloat eats the client's context window and hits tool limits

**What goes wrong:**
Tool count and JSON-schema verbosity consume tens of thousands of tokens before the first user message. Measured on InfraNode: 71 tools = ~27k tokens, with `outputSchema` alone responsible for 56% of the footprint. Cursor hard-caps at 80 tools across all servers; a fat server crowds out every other server the user has installed.

**Why it happens:**
FastMCP-style decorators make it trivial to expose everything; Pydantic models generate exhaustive schemas (descriptions, enums, nested objects) by default; nobody measures the token cost until users complain.

**How to avoid:**
Hold the ~15-20 tool budget (already a project decision). Apply the InfraNode schema diet playbook: trim or drop `outputSchema`, short one-line descriptions, flatten nested models, consolidate variants behind an enum parameter instead of N tools. Add a CI check that fails when the serialized `tools/list` response exceeds a token budget (e.g., 6-8k tokens).

**Warning signs:**
`tools/list` JSON larger than ~30 KB; more than one tool per data source per verb; reviewers unable to summarize a tool from its description alone.

**Phase to address:**
MCP core phase. Set the token budget before writing the first tool, not after.

---

### Pitfall 4: ExApp deploy/registration failures (Docker socket, network triangle, heartbeat)

**What goes wrong:**
The ExApp registers but never becomes healthy, or registration fails outright. Classic causes: Docker Socket Proxy / HaRP misconfigured so AppAPI cannot reach the Docker Engine API; the three-way network requirement broken (Nextcloud must reach the daemon host, the daemon must reach Nextcloud, and the ExApp container must reach Nextcloud); heartbeat not answered within the 90s timeout; `/init` or `/enabled` endpoints missing or erroring; HTTP 401 on ExApp-to-Nextcloud calls because `EX-APP-ID` / `AUTHORIZATION-APP-API` headers are wrong after a re-register.

**Why it happens:**
The deploy pipeline is a strict multi-stage validation (AppAPI "Test Deploy" checks six stages) and every stage has environment-specific failure modes (reverse proxies, AIO networking, WSL2 port mapping, self-signed certs). Developers test only on one topology.

**How to avoid:**
Build against the official Test Deploy feature from day one and keep it green. Implement heartbeat, `/init` (with progress reporting 0-100) and `/enabled` handlers as the very first ExApp code, before any MCP logic. Test on at least two topologies early: plain docker-compose and Nextcloud AIO (the most common self-hoster setup, with its own network quirks). Document `occ app_api` re-register as the standard recovery path. Note: local WSL2 dev + a test Nextcloud in Docker adds NAT layers; verify container-to-Nextcloud reachability explicitly.

**Warning signs:**
ExApp shows as registered but "not enabled"; `docker logs nc_app_<appid>` shows 401s; Test Deploy fails at a specific stage; works locally but not on AIO.

**Phase to address:**
Foundations/ExApp-skeleton phase. Deliverable: green Test Deploy on two topologies before writing tools.

---

### Pitfall 5: Underestimating (or over-fearing) the certification and store pipeline before the September deadline

**What goes wrong:**
Either the team assumes signing/review takes months and panics, or assumes it is instant and submits days before the conference, hitting a snag (info.xml schema rejection, CSR question round, key mishap) with no buffer.

**Why it happens:**
The process has three separately-failing gates: (1) CSR pull request in nextcloud/app-certificate-requests, (2) app registration + release upload on apps.nextcloud.com with info.xml XSD validation and signature check, (3) for ExApps, the Docker image must already be pulled/pullable from the declared registry+tag at install time. Timelines are undocumented, so people guess.

**How to avoid:**
Measured reality (GitHub data, Jul/Aug 2026): CSR PRs are currently merged in roughly 1-5 days (examples: created 2026-07-28, merged 2026-07-29; created 2026-07-30, merged 2026-08-03; created 2026-08-06, merged 2026-08-10). Plan for that plus a question round: submit the CSR 3-4 weeks before the conference, and the first store release 2 weeks before. Validate info.xml against the XSD locally before upload. Publish the Docker image (ideally multi-arch amd64+arm64, since many self-hosters run ARM) to ghcr.io before creating the store release, because the deploy daemon pulls the exact `registry/image:tag` from `<external-app>` at install time. Guard the signing private key like a production secret: the request repo shows real revocation PRs for exposed keys ("Revoke and replace certificate for sharepath (private key exposed)"), and a mid-deadline revocation cycle costs another PR round trip.

**Warning signs:**
No CSR merged by mid-August for a September launch; info.xml never validated against the schema; release image tag referenced in info.xml not yet pushed.

**Phase to address:**
Store-submission phase, but start the CSR PR during the hardening phase (it only needs the app ID and public repo, not the finished app).

---

### Pitfall 6: ExApp system credentials quietly bypass user permissions

**What goes wrong:**
AppAPI lets an ExApp perform Nextcloud requests as any user (impersonation) or with app-level authority. A single lazy code path that uses app-level/system credentials for a data read breaks the core security promise ("the assistant never sees more than the logged-in user") and would be a legitimate store-removal / security-audit finding.

**Why it happens:**
The impersonation capability is the convenient default in ExApp examples; during debugging it is tempting to "just fetch as admin". Once one helper function does it, every tool inherits it.

**How to avoid:**
One single Nextcloud client factory in the codebase that requires an authenticated user identity (derived from the validated OAuth token) and has no system-credential constructor exposed to tool code. Deny-by-default: tools receive a user-scoped client, never raw AppAPI credentials. Add a test that greps/imports for forbidden impersonation entry points. Note for docs: Nextcloud logs ExApp impersonation to `data/exapp_impersonation.log`; point admins at it as an audit trail (this is a selling point, use it).

**Warning signs:**
Any Nextcloud request path that does not carry a user ID; tools returning data for files the test user cannot see; admin-level results in tests run as a restricted user.

**Phase to address:**
Foundations phase (client factory design) + hardening phase (permission-parity test: same query as restricted user via UI vs. via MCP must match).

---

### Pitfall 7: Nextcloud brute-force protection throttles the whole MCP server

**What goes wrong:**
Nextcloud's brute-force protection keys on source IP. A remote MCP server is one IP serving many users. A few failed authentications (expired app password fallback, revoked token, user typo during Login Flow) accumulate: delays up to 25 seconds per request, then hard 429s after 10 failed attempts in 30 minutes. Every user of the server is now throttled, and it looks like "the MCP server is slow/broken". Community reports show exactly this pattern with DAVx5/FolderSync-class API clients.

**Why it happens:**
Developers test with one always-valid credential and never hit the accumulation. The protection also counts some non-auth "suspicious" actions, and misconfigured reverse proxies (missing X-Forwarded-For trust) collapse all clients into one IP on the Nextcloud side.

**How to avoid:**
Never retry failed auth automatically. Cache token-validation results briefly so one bad credential does not hammer the login path. Surface 401/429 with actionable messages ("token revoked, re-authorize") instead of retrying. In admin docs: recommend `occ security:bruteforce:reset` for recovery and IP allowlisting of the ExApp/MCP host via the brute-force settings app; for the ExApp topology ensure the container's requests to Nextcloud carry correct forwarded headers. Watch response latency creeping toward 25s as the early symptom.

**Warning signs:**
Sporadic multi-second latencies on otherwise fast endpoints; 429s in logs; everything fast again after a successful login from the same IP.

**Phase to address:**
Auth phase (no-retry policy, error surfacing) + hardening phase (load/negative-path tests with deliberately invalid credentials, admin runbook).

---

### Pitfall 8: Store listing rejected or de-listed over policy details that are trivial to get right early

**What goes wrong:**
Late rename or resubmission because of store rules: apps must not use "Nextcloud" in their name (working title "MCP Connector für Nextcloud" is fine as description, not as app name/ID); license must be AGPL-3.0-or-later or compatible; apps may only use public Nextcloud APIs; user data transmission must be explicitly disclosed and minimized; uninstall must clean up completely; compatibility may only declare latest release +1. Violations cost the "approved" state or the listing, and security-relevant ones can block the author from the store.

**Why it happens:**
The rules live in the publishing docs that people read last, after the app ID is baked into info.xml, container names, table names and the CSR (the certificate is bound to the app ID, so a rename invalidates it).

**How to avoid:**
Fix the final app ID and display name (without "Nextcloud") before the first commit. Because this app by design transmits user data to third-party AI clients, write the disclosure text early and make it prominent in the listing and README; this is the rule most likely to draw reviewer questions for an MCP app. Implement uninstall cleanup (tokens, tables, preferences) as a feature, not an afterthought.

**Warning signs:**
App ID contains "nextcloud"; no data-flow disclosure in the description; leftover tables after `occ app_api:app:unregister`.

**Phase to address:**
Foundations phase (naming/ID decision), store-submission phase (listing text, disclosure, cleanup verification).

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| App-password-only auth first, OAuth "later" | Ships a demo fast | OAuth is the core differentiator; retrofitting discovery/DCR/audience-binding touches every request path | Only as the documented fallback path, built alongside OAuth, never instead of it |
| Per-session in-memory caches for pagination | Easy pagination | Breaks stateless transport, breaks on restart, blocks horizontal scaling | Never (use opaque cursors in responses) |
| System/admin credentials for "read-only" convenience calls | Avoids per-user plumbing | Destroys the permission-parity promise; store/security risk | Never |
| Skipping `/init` progress + `/enabled` handlers ("it deploys anyway") | Less boilerplate | Random AIO/registration failures, 90s heartbeat timeouts in slow environments | Never for a store-distributed ExApp |
| Full Pydantic outputSchema on every tool | Nice typed clients | 50%+ of token footprint (InfraNode measurement) | Acceptable only for the 2-3 tools where structured output is load-bearing |
| amd64-only Docker image | Simpler CI | ARM self-hosters (Raspberry Pi, Hetzner ARM, Apple Silicon dev) cannot install; support noise | MVP dev builds only; store release must be multi-arch |
| Chasing MCP spec 2026-07-28 / SDK 2.0 beta | Newest features | Beta API churn against a hard September deadline | Never before v1; keep architecture upgradefähig instead |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| WebDAV SEARCH | Sending SEARCH without `Content-Type: text/xml`, wrong basicsearch XML, or scope outside `files/$username`; result: opaque 500s | POST to `remote.php/dav/` with `d:basicsearch` (select/from/where/orderby), scope always `/files/<uid>/...`, request needed props explicitly; keep a known-good XML template with tests |
| WebDAV SEARCH | Assuming server-side full-text/content search | SEARCH matches properties (name, size, mimetype, mtime, `d:like` on displayname); content search belongs to Unified Search OCS, not DAV |
| CalDAV | Writing floating times or deprecated TZIDs ("Eastern Standard Time"); reading recurring events without expansion | Always IANA TZIDs with matching VTIMEZONE (use icalendar/vobject libs, never string-build iCal); for reads use calendar-query REPORT with time-range and let the library expand recurrences; treat all-day (VALUE=DATE) as date, not midnight |
| OCS | Forgetting `OCS-APIRequest: true` header (returns HTML login page), or parsing XML default envelope | Always send `OCS-APIRequest: true` + `Accept: application/json`; parse the `ocs.meta`/`ocs.data` envelope; note OCS v1 uses statuscode 100 for success, v2 uses real HTTP codes; use `/ocs/v2.php/` routes |
| Nextcloud auth | Basic auth with the account password when 2FA is enabled (always 401, and it feeds brute-force protection) | App passwords or Login Flow v2 for the fallback path; document that 2FA users must use the generated app password; never retry a failed credential |
| AppAPI | Treating ExApp auth headers as static after re-register | Secret rotates on unregister/register; validate `AUTHORIZATION-APP-API` per request exactly like AppAPI does; on persistent 401s, re-enable AppAPI and re-register |
| Deploy daemon | Referencing an image tag in `<external-app>` that is not yet pushed, or single-arch | Push multi-arch image to ghcr.io before the store release; the daemon pulls exactly registry/image:tag at install |
| Claude.ai connector | Testing only from the dev LAN | claude.ai resolves DNS from Anthropic infra: public A record required (IPv4), no private/CGNAT IPs, no cross-host redirects, WAF must allow Anthropic egress range |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| prepare_context fan-out done sequentially | 20-60s tool latency, client timeouts | Parallelize the WebDAV/CalDAV/OCS sub-queries (Unified Search providers are parallelizable), hard per-source timeouts, degrade gracefully per source (InfraNode wrapper pattern) | Immediately on any instance with slow apps installed |
| Unbounded file reads via WebDAV | Huge tool responses blow the client context, memory spikes | Size cap + range reads; return excerpts with a handle for "read more"; reject binaries with a clear message | First multi-MB file |
| Brute-force delay accumulation from one bad credential | All requests from server IP delayed up to 25s, then 429 | See Pitfall 7: no auth retries, cached validation, admin allowlist runbook | ~10 failed attempts / 30 min from the server IP |
| Token validation hitting Nextcloud on every MCP request | Nextcloud becomes the latency floor; token endpoint may exceed Claude's 10s limit under load | Short-lived local validation cache; keep `/token` and validation paths free of slow Nextcloud round trips | Tens of concurrent users |
| One SEARCH over the whole files tree per query | Slow on large accounts, DB pressure on the instance | Scope searches (folder param, limits), prefer Unified Search OCS for discovery, SEARCH for targeted property queries | Accounts with 100k+ files |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Using ExApp impersonation/system authority for data access | Assistant sees other users' data; store security-audit failure; reputational kill for a privacy-positioned product | Single user-scoped client factory (Pitfall 6); permission-parity tests; document `exapp_impersonation.log` for admins |
| Storing Nextcloud app passwords / refresh tokens in plaintext in the ExApp container or SQLite | Container compromise = account takeover for all connected users | Encrypt at rest with a key held in Nextcloud (appconfig secret) or derived per install; never log tokens; revocation UI must actually invalidate server-side |
| SSRF via user-supplied URLs (file-from-URL, webcal subscribe, "fetch this link into context") | ExApp container sits inside the deployment network: can reach the Docker socket proxy, Nextcloud internal ports, other containers, cloud metadata endpoints | v1: no URL-fetching tools at all (fits the curated scope); if ever added: resolve-then-connect with private/link-local/CGNAT IP denylist, no redirects across hosts, egress allowlist |
| Audience-unbound tokens (accepting any valid Nextcloud token) | Token minted for another service replayed against the MCP server (confused deputy) | Enforce RFC 8707 resource/audience binding; accept only tokens minted for the canonical MCP URL |
| Signing private key committed, baked into an image layer, or shared | Certificate revocation (real precedent in app-certificate-requests), broken releases mid-deadline | Key lives outside the repo/CI images; sign in a controlled step; treat like a production secret |
| Letting "risk-free writes" drift into overwrite semantics | Upload-with-same-name silently replaces files, violating the "cannot destroy anything" promise | Writes create-only: fail on existing targets (If-None-Match/exists check), never PUT over existing content, no delete/share endpoints wired at all |
| OAuth consent screen that hides scope | Users authorize an AI client without understanding data flow; store disclosure rule violation | Human-readable consent listing exactly which apps (Files, Calendar, Notes, Deck, Contacts) become readable, matching the per-tool permission levels |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Cryptic auth failures ("401") surfaced raw in the AI client | User blames the AI or reinstalls everything | Map failures to actions: "token revoked in Nextcloud settings, reconnect via ..." inside tool error text |
| No visible per-user control in Nextcloud | Admins cannot answer "who has AI access to what" | Per-user settings page (enable/disable, token list, revoke) is a differentiator: build it, screenshot it for the listing |
| Tool responses formatted for humans, not models | Token waste, model misreads structure | Compact structured text, stable field order, sizes/dates normalized; no ASCII tables in tool output |
| Onboarding requiring occ commands or manual app passwords | Kills the "install per click" promise for the store audience | OAuth-first onboarding; Login Flow v2 browser flow as fallback so no user ever hand-copies an app password |
| Silent partial results from prepare_context | Model asserts "no meetings found" when CalDAV timed out | Always mark degraded sources explicitly in the response ("calendar unavailable, results exclude events") |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **OAuth:** Works with MCP Inspector but not verified against claude.ai from a public network. Verify: full connect + tool call from claude.ai AND ChatGPT connector UIs, including token refresh and revocation.
- [ ] **ExApp deploy:** Works with manual-install but never with docker-install via a real deploy daemon. Verify: Test Deploy green + install on Nextcloud AIO.
- [ ] **Permission parity:** Tools tested only as admin. Verify: restricted test user with limited group folders sees identical results via UI search and via MCP.
- [ ] **Statelessness:** Works with one client sequentially. Verify: two concurrent clients, server restart mid-conversation, SDK >= 1.28 client (context_agent#227 regression test).
- [ ] **Store release:** info.xml written but never XSD-validated; image tag not pushed; CSR not merged. Verify: local schema validation, `docker pull` of the exact tag from a clean machine, merged certificate PR.
- [ ] **Uninstall:** App unregisters but leaves tokens/tables. Verify: unregister then inspect DB and user preferences for leftovers.
- [ ] **Brute-force behavior:** Never tested with invalid credentials. Verify: 15 failed auths from the server IP, confirm graceful 429 handling and recovery runbook works.
- [ ] **2FA users:** Fallback path tested only without 2FA. Verify: Login Flow v2 onboarding with a 2FA-enabled account.
- [ ] **Timezones:** Calendar tools tested only in one timezone. Verify: recurring event across DST boundary, all-day event, event created in Europe/Berlin read from a UTC client.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Claude.ai connector rejects OAuth | MEDIUM | Run the official curl diagnostic checklist top-down (DNS, redirect, well-known, PKCE advert, audience); capture the `ofid_` reference ID for Anthropic support if server logs show a completed flow |
| ExApp stuck half-registered | LOW | `occ app_api:app:unregister <id>` then re-register; check `docker logs nc_app_<id>`; re-enable AppAPI if 401s persist |
| Brute-force lockout during demo/testing | LOW | `occ security:bruteforce:reset <ip>`; add server IP to allowlist; fix the failing credential source |
| Signing key exposed | HIGH | Immediate revocation PR to app-certificate-requests (precedent exists), new CSR, re-sign and re-upload release; budget ~1 week |
| App ID must change late (naming rule) | HIGH | New CSR (cert is bound to app ID), rename image, migration for any stored data; avoid entirely by fixing ID in week 1 |
| SDK 1.27 blocks a needed client feature | MEDIUM | Handles-based, stateless architecture keeps the upgrade localized to transport wiring; upgrade behind an integration-test matrix |
| Store reviewer questions data transmission | MEDIUM | Pre-written data-flow disclosure + architecture diagram (user-scoped tokens, no server-side storage of content) ready to paste into the review thread |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ExApp deploy/registration failures (P4) | Phase: ExApp foundations | Test Deploy green on docker-compose + AIO |
| App ID / naming / store rules (P8) | Phase: ExApp foundations | App ID frozen, contains no "nextcloud", disclosure text drafted |
| System-credential bypass (P6) | Phase: ExApp foundations + hardening | Permission-parity test with restricted user passes |
| Session-state assumptions (P2) | Phase: MCP core | Restart-mid-conversation test + SDK >= 1.28 client test pass |
| Schema bloat (P3) | Phase: MCP core | tools/list token budget check in CI (< ~8k tokens) |
| WebDAV/CalDAV/OCS gotchas | Phase: MCP core (tool implementation) | Timezone/DST test matrix, SEARCH template tests, OCS JSON envelope tests |
| OAuth discovery breakage (P1) | Phase: Auth/OAuth | Live connect from claude.ai and ChatGPT against public staging |
| Brute-force throttling (P7) | Phase: Auth + hardening | Negative-credential load test, admin runbook written |
| Token storage / SSRF / write-safety | Phase: Hardening | Encrypted-at-rest check, create-only write tests, no URL-fetch tools in v1 |
| Certification lead time (P5) | Phase: Store submission (CSR started during hardening) | CSR merged >= 3 weeks pre-conference; signed release installed from the store on a clean instance >= 1 week pre-conference |

## Sources

- AppAPI troubleshooting and deployment: [Nextcloud ExApp Troubleshooting](https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/faq/Troubleshooting.html), [Test Deploy Daemon](https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/TestDeploy.html), [ExApp Deployment](https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/Deployment.html), [AppAPI and External Apps](https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/AppAPIAndExternalApps.html), [app_api issue #446](https://github.com/nextcloud/app_api/issues/446)
- Certification pipeline: [nextcloud/app-certificate-requests](https://github.com/nextcloud/app-certificate-requests) (closed-PR turnaround measured 2026-07/08 via GitHub API: 1-5 days; revocation precedent PR "sharepath private key exposed"), [Code signing docs](https://docs.nextcloud.com/server/stable/developer_manual/app_publishing_maintenance/code_signing.html), [App Store Developer Guide](https://nextcloudappstore.readthedocs.io/en/latest/developer.html)
- Store rules and rejection/removal: [Nextcloud app store rules](https://docs.nextcloud.com/server/stable/developer_manual/app_publishing_maintenance/publishing.html)
- MCP connector auth failures: [Claude.ai connector troubleshooting](https://claude.com/docs/connectors/building/troubleshooting) (fetched 2026-08-14; DNS/private-IP rejection, redirect header-drop, RFC 9728/7591/8414/8707 chain, PKCE S256, 10s token timeout), [claude-ai-mcp issue #134](https://github.com/anthropics/claude-ai-mcp/issues/134), [claude-code issue #3273](https://github.com/anthropics/claude-code/issues/3273)
- Session/state: [context_agent issue #227](https://github.com/nextcloud/context_agent/issues/227) (fetched: stateless_http=True terminates sessions, breaks SDK >= 1.28 clients, open/unfixed), [MCP stateless 2026-07-28 spec analysis](https://dev.to/krlz/mcp-went-stateless-what-the-2026-07-28-spec-actually-changes-273k), [New Relic: MCP going stateless](https://newrelic.com/blog/ai/mcp-is-going-stateless), [MCP C# SDK stateless concepts](https://csharp.sdk.modelcontextprotocol.io/v1/concepts/stateless/stateless.html)
- Schema bloat: own InfraNode measurements (71 tools ~27k tokens, outputSchema 56%), Cursor 80-tool limit (verified in prior project research)
- Nextcloud APIs: [WebDAV Search docs](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/search.html), [WebDAV basics](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/basic.html), [Brute force protection admin manual](https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/bruteforce_configuration.html), [community report: brute-force triggered by API clients](https://help.nextcloud.com/t/bruteforce-protection-triggered-by-using-certain-apps-foldersync-davx5-floccus-etc/165368)
- CalDAV timezone pitfalls: [Cal.com CalDAV implementation post-mortem](https://cal.com/blog/the-intricacies-and-challenges-of-implementing-a-caldav-supporting-system-for-cal), [RFC 4791](https://datatracker.ietf.org/doc/html/rfc4791), [fluid-calendar issue #135](https://github.com/dotnetfactory/fluid-calendar/issues/135)
- ExApp security/impersonation: [AppAPI GitHub](https://github.com/nextcloud/app_api), [app_api logging/diagnostics (exapp_impersonation.log)](https://deepwiki.com/nextcloud/app_api/11.4-logging-and-diagnostics)

---
*Pitfalls research for: Nextcloud MCP-only ExApp*
*Researched: 2026-08-14*
