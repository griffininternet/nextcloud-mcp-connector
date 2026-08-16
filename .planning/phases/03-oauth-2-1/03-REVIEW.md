---
phase: 03-oauth-2-1
reviewed: 2026-08-16T05:02:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - src/mcp_connector/oauth/metadata.py
  - src/mcp_connector/oauth/crypto.py
  - src/mcp_connector/oauth/store.py
  - src/mcp_connector/oauth/registry.py
  - src/mcp_connector/oauth/provider.py
  - src/mcp_connector/oauth/verifier.py
  - src/mcp_connector/oauth/loginflow.py
  - src/mcp_connector/oauth/connect.py
  - src/mcp_connector/oauth/consent.py
  - src/mcp_connector/oauth/throttle.py
  - src/mcp_connector/exapp/responses.py
  - src/mcp_connector/exapp/middleware.py
  - src/mcp_connector/exapp/auth.py
  - src/mcp_connector/exapp/ui/layout.py
  - src/mcp_connector/exapp/ui/strings.py
  - src/mcp_connector/exapp/ui/errors.py
  - src/mcp_connector/exapp/ui/connect.py
  - src/mcp_connector/exapp/ui/consent.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/config.py
  - src/mcp_connector/deps.py
  - src/mcp_connector/nextcloud/http.py
  - src/mcp_connector/nextcloud/credentials.py
  - appinfo/info.xml
  - deploy/Caddyfile
  - scripts/bootstrap_exapp.sh
  - docs/oauth-setup.md
  - tests/unit/test_oauth_abuse.py
  - tests/integration/test_oauth_flow_exapp.py
  - .github/workflows/ci.yml
findings:
  critical: 3
  warning: 12
  info: 6
  total: 21
resolved:
  at: 2026-08-16
  critical: 3
  warning: 8
  info: 0
  open: 10
  commits:
    - 563e330 CR-01
    - 6d7dc78 CR-01 amendment, live counter check
    - 24ebd35 CR-01 amendment, live counter check
    - fdaea5d CR-02, WR-03
    - f6d5ed1 CR-03
    - d3a5450 WR-01
    - b254e21 WR-02
    - 783854c WR-04
    - 91db412 WR-05
    - bac94d4 WR-06
    - ed829e3 WR-07
    - 1abbc90 WR-11
status: partially_resolved
---

# Phase 3: Code Review Report

**Reviewed:** 2026-08-16T05:02:00Z
**Depth:** standard (security focus, whole OAuth implementation 03-01 to 03-08)
**Files Reviewed:** 27 source files plus manifest, deploy, docs, tests, CI
**Status:** partially_resolved (three blockers and eight warnings fixed on 2026-08-16, ten findings open)

## What was fixed, and what is still open

Fixed on 2026-08-16, one commit per finding, each with a guard test that is red without it:
the three blockers (CR-01, CR-02, CR-03) and eight warnings (WR-01 to WR-07 and WR-11).
Every one of them carries a **Resolved** line with its commit below.

Still open, and deliberately: WR-08 (the refused client pages echo an attacker supplied
client id as page copy), WR-10 (_client_information takes a client_id it never compares),
WR-12 (POST /connect carries no anti forgery value) and five of the six Info findings.

Closed later the same day, after the phase gates named them again: **WR-09** (`main` now
refuses to start in the ExApp mode without `NC_MCP_PUBLIC_URL`, blank counts as missing) and
**IN-03** (`revocation_endpoint_auth_methods_supported` advertises `none`, so a public client
is no longer told it cannot end its own connection). Both with guard tests that are red
without the change.

One open point belongs to CR-03 rather than to the list above: the return page needs a cross
check in a real Chromium and a real WebKit. It is the shape that is correct without one,
because a navigation is not a form submission, and the measurement belongs to the staging
run of plan 03-09.

## Summary

The AS core is in good shape where the SDK carries it: PKCE with `S256` only, exact
`redirect_uri` matching, single use codes under `BEGIN IMMEDIATE`, RFC 8707 audience binding
at three points, reuse detection with a bounded grace window, digests instead of tokens on
disk, AES-GCM with the row id as `aad`, `no-store` on every answer, the AUTH-07 enforcement
point wired at all four places, and a genuinely careful set of guard tests
(`tests/unit/test_oauth_abuse.py`). The `NoCookieJar` fix is complete: both directions of
`http.cookiejar.CookieJar` are neutralised, and `httpx` reaches the jar and not a wrapper.

Three findings are blocking. The first is a design gap, not a slip: **nothing binds a login
flow to the browser or the account that signs in.** The flow id is created by, and only ever
known to, the party that started the flow, and it is the single capability that both fetches
the sign in result and casts the consent decision. The anti forgery token is derived from
that same flow id, so it is readable by exactly the party the consent screen is supposed to
protect the user against. The second is that the throttle counts refusals only, so the one
path it was introduced for (SC 5, anonymous creation of Nextcloud login flows) is unbounded.
The third is a CSP rule that very likely blocks the approval redirect in Chromium and WebKit
browsers, which no check in this repository would notice because the whole flow proof runs
over `httpx`.

The remaining findings are smaller but several of them undo a property the code claims in its
own docstring (a dropped SDK guard in the client authenticator, a first start race the read
back does not close, a `_write` that promises a transaction it does not open, an expiry
cascade that drops Nextcloud credentials it promised to hand back).

## Critical Issues

### CR-01: A login flow can be finished by a different person than the one who signs in; the consent screen is bypassable

**Resolved:** 563e330, 2026-08-16. The decision is a route of its own, /authorize/decide;
HaRP resolves the signed in Nextcloud account and the route grants nothing unless it is the
account whose sign in produced the authorization. The result page of the browser onboarding
applies the same rule and hands the credential back when it cannot be shown to that account.
Manifest gate pulled along (twelve routes, an access level table with counter probes in both
directions). Guard tests reproduce the relay on both surfaces.

**Amended:** 6d7dc78 and 24ebd35, 2026-08-16, after the live counter check below. The access
level of the decision route went back to PUBLIC; the identity check itself is unchanged and
is where it always was, in the app.

**Live counter check, 2026-08-16** (Nextcloud 34.0.2, AppAPI HaRP `release`, the topology of
`compose.exapp.yml`). The fix rested on an assumption nothing had measured: that HaRP names
the Nextcloud account of a request that carries only a browser session cookie. It does, and
it does so on a PUBLIC route as well, which is what made the amendment possible. Full tables
in `docs/oauth-setup.md`, section 9 of the evidence. The three actor walk, against the
running instance:

| Actor | `POST /authorize/decide` | `GET /connect/wait` |
|---|---|---|
| the caller that started the flow, no Nextcloud account | `400`, no code | `400`, no credential |
| `mallory`, a real browser session, the wrong account | `400`, no code | `400`, no credential |
| `alice`, the session whose sign in produced the row | `200`, code issued and exchanged | `200`, credential shown once |

So the attack of this finding is closed over the full chain, and the browser path of the
victim works, which the previous proof did not show: `scripts/oauth_flow_check.py` threw the
sign in session away and re-authenticated the decision with Basic auth, and its onboarding
walk asked for the result with the caller that started the flow, which has been refused since
this fix. Both are corrected in 24ebd35; the walker now yields the session of the sign in and
uses it, so every run exercises the production path.

**Why the access level was withdrawn.** `access_level` `USER` made HaRP refuse the anonymous
decision itself with `403`, and HaRP records every such refusal in a blacklist of its own
(`HP_BLACKLIST_COUNT` 10, `HP_BLACKLIST_WINDOW` 300s). Measured from a cold HaRP: refusals
one to nine leave the app reachable, the tenth answers **every route of this app** with `502`
for that caller, discovery documents and `/mcp` included, and it clears 300 seconds after the
last refusal. Refusals are this route's normal traffic (the relay attempt, an expired session
behind an open consent screen, a resubmitted form, the negative probe the flow check sends on
every run), so the level intended to harden one route was a remote off switch for the whole
connector; two runs of the integration suite pulled it by accident, which is how it was
found. With the route PUBLIC the same sequence stays inside this app's own per path class
throttle (`400` ten times, then `429` with `Retry-After`) and the discovery documents keep
answering. Nothing is given up: the comparison in `_decide` is the only check that can
separate the relay attacker from the victim anyway, because the attacker holds a valid
Nextcloud account too. Regression guard:
`tests/integration/test_oauth_flow_exapp.py::test_refused_decisions_do_not_take_the_whole_app_off_the_network`,
plus the manifest gate, whose counter probe now fails a `USER` decision route.

**File:** `src/mcp_connector/oauth/consent.py:191-345`, `src/mcp_connector/oauth/connect.py:222-261`, `src/mcp_connector/oauth/crypto.py:139-154`

**Issue:**
The flow id is the whole authorisation of both browser surfaces, and it is held by whoever
*started* the flow, which in the OAuth path is the client and not the user. Nothing in
`_screen`, `_decide` or `_wait` binds a request to the browser or to the Nextcloud account
that performed the sign in.

Attack on the OAuth path, with the shipped defaults (DCR on, allowlist off):

1. The attacker registers a client at `POST /register` with their own `redirect_uri`.
2. The attacker calls `GET /authorize` and receives `flow=F` plus the Nextcloud sign in link
   `L` in the redirect (`consent.py:108-114`, `provider.py:400-431`).
3. The attacker sends **only `L`** to a victim. `L` is Nextcloud's own Login Flow v2 grant
   page; it shows `MCP Connector: <attacker chosen name>` and a "Grant access" button.
4. The victim grants. The credential now exists at Nextcloud.
5. The attacker, not the victim, loads `GET /authorize/consent?flow=F&step=wait`. That call
   polls Nextcloud, writes the authorization with the victim's app password
   (`consent.py:233-260`) and renders the consent form, including the hidden
   `confirm` value, to the attacker.
6. The attacker POSTs `decision=approve` with `flow=F` and that `confirm` value, receives the
   code at their own `redirect_uri` and exchanges it. They now act as the victim.

The victim never sees the consent screen that names the client id, the return address and the
"Unverified client" warning. `_confirmed` (`consent.py:434-444`) cannot help: the token is
`HMAC(data_key, flow_id)`, deterministic for the flow, and the attacker holds the flow id.

The same shape is worse on the browser onboarding: an attacker starts `POST /connect`, sends
the victim the raw Nextcloud login link, and then loads `GET /connect/wait?flow=F`, which
renders the **victim's Nextcloud app password in clear text** on the attacker's screen
(`connect.py:240-261`, `ui/connect.py:137-168`).

This is the classic Login Flow v2 relay, and the phase treats the consent screen as the
control that answers it (03-UI-SPEC.md S3, T-03-50). It does not: it authenticates the form,
never the person.

**Fix:** Bind the deciding request to the signed in Nextcloud user, which this topology can
prove and the code already parses. Concretely (the `USER` half of this proposal was
implemented, measured and then withdrawn, see the amendment above; the binding itself is what
shipped):

```xml
<!-- appinfo/info.xml: split the surface. The entry pages stay PUBLIC because the user is
     not signed in yet; the two requests that hand out a grant or a credential are USER,
     so HaRP puts the signed in user id into AUTHORIZATION-APP-API for them. -->
<route><url>^/authorize/consent/?$</url><verb>GET</verb><access_level>PUBLIC</access_level>...</route>
<route><url>^/authorize/decide/?$</url><verb>POST</verb><access_level>USER</access_level>...</route>
<route><url>^/connect/result/?$</url><verb>GET</verb><access_level>USER</access_level>...</route>
```

```python
# oauth/consent.py, in _decide, before anything is granted:
user = require_appapi(request, env=env)          # exapp/auth.py, already imported elsewhere
authorization = await store.load_authorization(flow_id)
if not user or authorization is None or not secrets.compare_digest(
    user.encode("utf-8"), authorization.nc_user.encode("utf-8")
):
    # the browser that decides is not the account that signed in
    return _page(errors.error_page("E3", env=env))
```

Do the same for the page that renders the credential in `connect.py:_wait`. If the USER route
split is rejected for v1, this has to be written up as an accepted risk in
`docs/oauth-setup.md` and in the threat model, the claim that the consent screen is a security
control has to be removed from the docstrings, and the install guide must recommend
`core.login_flow_v2.allowed_user_agents`; shipping it silently is not an option under the
owner directive of this phase.

### CR-02: The throttle bounds nothing on the path it was built for; anonymous callers can create Nextcloud login flows without limit

**Resolved:** fdaea5d, 2026-08-16. The two routes that make this server open a Nextcloud login
flow, POST /connect and /authorize, count every request before the work, in path classes and
with a per source limit of their own; the screens behind them keep the refusal counter.
forget() is gone with it, which also resolves WR-03: a success pays back exactly one counted
failure now. SC 5 statements in docs/oauth-setup.md corrected.

**File:** `src/mcp_connector/oauth/throttle.py:216-268`, `src/mcp_connector/oauth/connect.py:100-169`

**Issue:**
`Throttled.__call__` records a failure only when the answer is `>= 400`
(`throttle.py:265-268`). Every *successful* request is not counted, and on top of that calls
`forget()`, which erases the per source counter.

The paths that cost a Nextcloud PHP round trip answer 200 on success:

* `POST /connect` (`action=start`) answers 200 with the handoff page and performs one
  `POST /index.php/login/v2` at Nextcloud, which creates a login flow record that lives for
  20 minutes, plus one row in our own `flows` table (`connect.py:172-207`).
* `GET /connect/wait?flow=<valid>` answers 200 with the waiting page and performs one
  `POST /login/v2/poll` per load (`connect.py:240`).
* `GET /authorize` with a valid registration answers 302 and also opens a login flow
  (`provider.py:400-404`); the SDK returns 302 for its error cases as well
  (`mcp/server/auth/handlers/authorize.py`), so even a PKCE downgrade is never counted.

None of these is authenticated, none needs a cookie or a token, and none is bounded. The
module docstring (`throttle.py:13-20`) and `connect_routes` (`connect.py:107-112`) both claim
this is exactly what is protected ("the one route on which an anonymous caller can make this
server start a Nextcloud login flow ... SC 5"). The measurement in `docs/oauth-setup.md`
§3 and `tests/integration/test_oauth_flow_exapp.py:382` only ever exercises *refused* token
requests, so the gap is not visible anywhere.

**Fix:** Count the requests that cost a Nextcloud round trip, not only the refusals. Smallest
correct change: give the throttle a second counter that is incremented before the work on the
flow creating paths.

```python
# oauth/throttle.py
class Throttled:
    def __init__(self, app, throttle, path_class, *, machine, env=None, count_all=False):
        ...
        self._count_all = count_all

    async def __call__(self, scope, receive, send):
        ...
        await self._app(scope, receive, watch)
        if status >= 400 or self._count_all:
            self._throttle.record_failure(self._path_class, source)
        elif not self._count_all:
            self._throttle.forget(self._path_class, source)
```

and build the `/connect` and `/authorize` routes with `count_all=True` (a separate, higher
limit is fine: the point is that the ceiling per path class becomes reachable at all). Add a
guard test that N successful `POST /connect` requests end in 429 and that the Nextcloud mock
saw at most N round trips.

### CR-03: `form-action 'self'` very likely blocks the approval redirect in Chromium and WebKit

**Resolved:** f6d5ed1, 2026-08-16. The decision answers 200 with a page that carries the return
address as a meta refresh and as a readable button, instead of a 302 a browser refuses under
form-action 'self'. The policy is untouched and names no foreign origin. The browser cross
check in a real Chromium is still open and belongs to the staging run of plan 03-09.

**File:** `src/mcp_connector/exapp/ui/layout.py:66-69`, `src/mcp_connector/oauth/consent.py:385-388`

**Issue:**
Every page of the phase is served with `form-action 'self'`. The consent decision is a POST
form to our own path whose answer is a `302` to the client's registered `redirect_uri`
(`consent.py:385-388`, and the same for the deny path at `:415-418`). Chromium and WebKit
enforce `form-action` against the target of a redirect that follows a form submission
(long standing, intentional behaviour; Firefox does not). On those engines the browser
refuses to follow the 302 and the user is left on a blank page with a console error, which is
the primary flow of success criteria 1 and 2 (Claude.ai, ChatGPT).

Nothing in this repository would catch it: `scripts/oauth_flow_check.py` and
`tests/integration/test_oauth_flow_exapp.py` walk the flow with `httpx`, which has no CSP.

**Fix:** Verify in a real Chromium browser first, then relax the directive on the consent page
only, to the origin the decision may return to (never `*`):

```python
# exapp/ui/layout.py
CSP_TEMPLATE = (
    "default-src 'none'; style-src 'nonce-{nonce}'; form-action {form_action}; "
    "frame-ancestors 'none'; base-uri 'none'"
)

def page(..., form_action: str = "'self'") -> Response: ...

# exapp/ui/consent.py, consent_page(): pass the origin of the registered redirect_uri
origin = urlsplit(redirect_uri)
layout.page(..., form_action=f"'self' {origin.scheme}://{origin.netloc}" if origin.netloc else "'self'")
```

The alternative, which keeps the policy untouched, is to answer the decision with a 200 page
carrying a plain link plus `<meta http-equiv="refresh">` to the redirect target; that is a
navigation and not a form submission, so `form-action` does not apply. Either way the fix
needs a browser check, not another `httpx` run.

## Warnings

### WR-01: `HashedClientAuthenticator` drops two fail-closed guards of the SDK authenticator

**Resolved:** d3a5450, 2026-08-16. A registration that asked for a secret and has none stored
is refused instead of read as a public client, and client_secret_expires_at is compared against
the clock of this provider.

**File:** `src/mcp_connector/oauth/provider.py:1071-1101`

**Issue:** The override reimplements `ClientAuthenticator.authenticate_request` and loses two
checks the SDK makes (`mcp/server/auth/middleware/client_auth.py`):

1. *"registered for secret based authentication but has no stored secret"* is a refusal in the
   SDK. Here `stored is None` is treated as "a public client" and the client is returned
   authenticated (`provider.py:1088-1091`), so any row whose
   `token_endpoint_auth_method` is `client_secret_post`/`_basic` while
   `client_secret_hash` is `NULL` authenticates with no credential at all.
2. `client_secret_expires_at` is never compared against the clock, so an expired client secret
   keeps working.

Neither is reachable through the shipped DCR path today (the SDK always mints a secret when
the method is not `none`, and the default expiry is "never"), which is why this is a warning
and not a blocker. Both become live the moment a row is written another way or
`client_secret_expiry_seconds` is set.

**Fix:**

```python
        stored = ...
        if stored is None:
            if client.token_endpoint_auth_method != "none":
                # registered for a secret and has none: nothing was verified above
                raise AuthenticationError("The client could not be authenticated")
            return client
        ...
        if not secrets.compare_digest(token_hash(presented), stored):
            raise AuthenticationError("Invalid client_secret")
        if client.client_secret_expires_at and client.client_secret_expires_at < self._provider._now():
            raise AuthenticationError("The client could not be authenticated")
        return client
```

### WR-02: The first start race of the data key is not closed by the read back

**Resolved:** b254e21, 2026-08-16. The read back is compared against what was written, a worker
that lost adopts the stored key and logs it, and the read is repeated once. The residual is
named instead of denied: the configuration API has no compare and set, the window is the first
start of a deployment, and docs/oauth-setup.md tells an administrator to start the first
container with one worker.

**File:** `src/mcp_connector/oauth/crypto.py:157-185`

**Issue:** The docstring claims the read back means two workers "both continue with the one
value that actually survived". It does not. Interleaving: A reads (none), B reads (none), A
writes K1, A reads back K1, B writes K2 (overwrites), B reads back K2. A now encrypts with K1
while the stored key is K2, so every row A writes is permanently undecryptable and the
Nextcloud app passwords behind them become orphans that no sweep can find. The window exists
only at the very first start of a deployment with more than one worker, but the consequence is
silent data loss and the code states the opposite.

**Fix:** Re-read after the write and adopt the stored value, and treat a mismatch as a reason
to re-read once more before use; or, better, make the key readable by construction: write it,
sleep zero, read, and compare against what was written:

```python
    written = secrets.token_bytes(KEY_BYTES).hex()
    await _write_key(settings, written)
    stored = await _read_key(settings)
    if stored is None:
        raise ToolError(...)
    if stored.hex() != written:
        # somebody else won the race; theirs is the key of this installation
        logger.warning("another worker stored the data key first; using the stored one")
    return stored
```

and additionally re-fetch the key (rebuild the store) when `DecryptionRejected` is seen on a
row that was just written, so a lost race is repaired instead of persisted.

### WR-03: One success clears the failure counter of a whole path class, which a guessing loop can drive

**Resolved:** fdaea5d, 2026-08-16. Resolved with CR-02: forget() no longer clears the window of
a source. A success pays back exactly one counted failure, so one harmless request every ninth
attempt no longer keeps a guessing loop at zero.

**File:** `src/mcp_connector/oauth/throttle.py:180-187`, `:265-268`

**Issue:** `forget()` deletes the per source counter of the path class on any answer below
400. The path classes are shared surfaces: `CLASS_CONNECT` covers `GET /connect` (always
200), `CLASS_AUTHORIZE` covers `GET /authorize/consent` with a flow the caller owns (200). An
attacker guessing flow ids on `/connect/wait` or `/authorize/consent` therefore interleaves
one harmless successful request every ninth attempt and never reaches the per source limit.
Only the class ceiling (200 per window, not cleared) still applies, and it is shared with
every legitimate user of the instance.

**Fix:** Clear the counter only for a success on the same *operation* that failed, or decay it
instead of deleting it:

```python
    def forget(self, path_class: str, source: str) -> None:
        key = self._key(path_class, source)
        counter = self._counters.get(key)
        if counter is not None and counter.seen > 0:
            counter.seen -= 1        # a success pays back one failure, never the whole window
```

### WR-04: Expiring a client cascade deletes its authorizations, so live Nextcloud app passwords are orphaned without being handed back

**Resolved:** 783854c, 2026-08-16. purge_expired leaves a client with connections alone and
lists it through expired_clients; the provider revokes the app passwords, deletes the
authorizations and only then the client, in a sweep next to sweep_abandoned and in the expiry
branch of get_client.

**File:** `src/mcp_connector/oauth/store.py:954-975`, `src/mcp_connector/oauth/provider.py:320-323`

**Issue:** `purge_expired` and `get_client` delete client rows, and `authorizations` has
`ON DELETE CASCADE` (`store.py:160`). The delete takes the encrypted app password with it,
and no code path calls `loginflow.revoke_app_password` or even `note_cleanup` first. Reachable
in the ordinary case: a registration whose user signed in and approved but whose client never
exchanged the code has `last_used_at IS NULL`, so after `UNUSED_CLIENT_TTL` (24 h) the client
row goes and the authorization with it, while the Nextcloud credential keeps existing.
Everywhere else in this phase (D-34, pitfall 13, `sweep_abandoned`, `_deny`, `_revoke`) the
rule is "the credential goes back or the attempt is remembered"; this path breaks it and, by
deleting the ciphertext, makes the credential unrecoverable for any later sweep.

**Fix:** Hand back before deleting. In `provider.get_client` and wherever `purge_expired`
removes clients, first collect the authorizations of those clients, revoke their app passwords
(bounded like `SWEEP_LIMIT`) and only then delete; or drop the cascade for `authorizations`
and let `sweep_abandoned` pick the rows up, which it already can once the client is gone.

### WR-05: `OAuthStore._write` promises a transaction it never opens

**Resolved:** 91db412, 2026-08-16. _call opens BEGIN IMMEDIATE for a write, commits when the
body returns and rolls back when it does not.

**File:** `src/mcp_connector/oauth/store.py:983-999`

**Issue:** The connection is created with `isolation_level=None` (`store.py:1047`), which is
autocommit: every `execute` commits on its own and the `conn.commit()` in `_call` is a no op.
`_write` is documented as "statements that are committed together when `work` returns" and no
`_write` body rolls back on an exception. Today no `_write` needs atomicity (the multi
statement bodies are purge plus insert), so this is a contract defect rather than a live bug,
but the next caller that groups two writes there will silently get none of the promised
behaviour.

**Fix:** Make the promise true or delete it.

```python
    def _call[T](self, work: Work[T], commit: bool) -> T:
        conn = _connect(self._path)
        try:
            if commit:
                conn.execute("BEGIN IMMEDIATE")
            result = work(conn)
            if commit:
                conn.execute("COMMIT")
            return result
        except BaseException:
            if commit:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
```

### WR-06: A ciphertext that cannot be read escapes as a 500 on the two browser surfaces

**Resolved:** bac94d4, 2026-08-16. Both call sites of load_flow, and the decision route with
them, answer the generic page with its log reference instead of letting DecryptionRejected
reach Starlette.

**File:** `src/mcp_connector/oauth/consent.py:207`, `src/mcp_connector/oauth/connect.py:233`

**Issue:** `store.load_flow` decrypts `poll_token_enc` inside the worker
(`store.py:503`) and raises `crypto.DecryptionRejected` for a changed data key or a damaged
blob. Both call sites are unguarded, so the exception reaches Starlette and the user gets a
bare 500, while both modules state in their docstring that "the guards return a response
instead of raising, so no refusal can escape as a 500". Every other read of a secret in this
phase (`consent._app_password`, `provider._hand_back`, `verifier.resolve_identity`) is
guarded; these two were missed.

**Fix:**

```python
    try:
        row = await store.load_flow(flow_id, now=0)
    except Exception:
        logger.exception("a flow record could not be read back")
        return _generic("the flow record could not be read", env)
```

### WR-07: The sign in link on the trust page is checked by host only, not by path

**Resolved:** ed829e3, 2026-08-16. The path of the address is checked against the one shape a
Login Flow v2 grant page has, so no other page of the configured host can stand behind the
button.

**File:** `src/mcp_connector/oauth/consent.py:447-469`

**Issue:** The value arrives in the `login` query parameter, i.e. from whoever builds the URL,
and `_sign_in_link` accepts any address whose `netloc` equals the configured Nextcloud or the
configured public URL. Any path on that host passes, so the primary button of a page whose
whole purpose is to be trustworthy can be pointed at an arbitrary Nextcloud URL, for example a
login page with an attacker chosen `redirect_url`, a public share, or any endpoint that
renders content on that origin. The docstring claims the check stops "anybody who can build a
URL putting their own page behind our button"; it stops only foreign hosts.

**Fix:** Nextcloud's Login Flow v2 address always has one shape. Pin it:

```python
_LOGIN_PATH_MARKER = "/login/v2/flow"
...
    if _LOGIN_PATH_MARKER not in parts.path:
        logger.warning("a sign in link with a foreign path was not rendered")
        return ""
```

Better still, stop carrying the link through the browser: add a `login_url` column to `flows`
(the schema is already migrated in `_add_missing_columns`, so a third `ALTER TABLE` is cheap)
and read it from the row.

### WR-08: The refused-client pages reflect an attacker supplied `client_id` as page copy

**File:** `src/mcp_connector/oauth/consent.py:167-188`, `src/mcp_connector/exapp/ui/strings.py:270-280`

**Issue:** `_no_client_page` passes the raw `client_id` from the query into `error_page(...,
client=client_id)`, and `ERROR_ALLOWLIST_BODY` / `ERROR_REGISTRATION_OFF_BODY` interpolate it
into a sentence. The value is escaped and cleaned, so there is no markup injection, but up to
80 characters of attacker text appear inside our card on a surface built to teach users what a
trustworthy page from this app looks like ("An administrator has not allowed <attacker text>
to connect ..."). Reachable unauthenticated with `allowlist_only=on` or `dcr=off`, i.e. the
two hardened configurations.

**Fix:** Do not echo a value that was never a known client. Either render the two pages
without the `{client}` placeholder, or show the id only when `policy.listed(client_id)` is
true, i.e. only for a value an administrator wrote down themselves.

### WR-09: A missing `NC_MCP_PUBLIC_URL` silently degrades to `http://127.0.0.1:8765` in the ExApp mode

**File:** `src/mcp_connector/config.py:226-229`, `src/mcp_connector/entry_exapp.py:184-196`

**Issue:** `public_url` falls back to `DEFAULT_PUBLIC_URL` for every mode. In the ExApp mode
that value becomes the issuer, the audience of every token, the `resource_metadata` pointer,
the prefix of every form action and the target of the consent redirect, so the deployment
starts green and every browser is sent to `127.0.0.1`. `main()` deliberately fails closed for
the persistent volume and for an unusable issuer, but not for this one, although
`appinfo/info.xml:196-201` and `docs/oauth-setup.md:54-67` both call it the one value that has
to be set.

**Fix:** In `entry_exapp.main`, refuse to start in the ExApp mode without it:

```python
    if config.exapp_configured() and not (os.environ.get(config.ENV_PUBLIC_URL) or "").strip():
        logger.error(
            "%s is not set. The authorization server calls itself by it: without it every "
            "discovery document, the audience of every token and the consent redirect name "
            "%s and no client can connect (docs/oauth-setup.md).",
            config.ENV_PUBLIC_URL, config.DEFAULT_PUBLIC_URL,
        )
        raise SystemExit(2)
```

### WR-10: `_client_information` takes a `client_id` it never uses, so the row key and the stored identity are never compared

**File:** `src/mcp_connector/oauth/provider.py:1166-1177`

**Issue:** The parameter reads like an identity check and is dead. The client returned by
`get_client(X)` carries whatever `client_id` the stored JSON says, and every downstream
comparison in the SDK (`auth_code.client_id != token_request.client_id`,
`refresh_token.client_id != ...`) is made against that value, not against the key that was
looked up. Not exploitable today because the SDK generates the id and `register_client` writes
key and JSON from the same object, but the guard the signature suggests does not exist.

**Fix:**

```python
    client = OAuthClientInformationFull.model_validate_json(metadata_json)
    if client.client_id != client_id:
        logger.error("a stored registration does not match its own key and is refused")
        return None
    return client
```

### WR-11: The OAuth flow integration test never runs in CI

**Resolved:** 1abbc90, 2026-08-16. The suite runs in the exapp job, and a guard test keeps
every tests/integration/*_exapp.py suite named in the workflow.

**File:** `.github/workflows/ci.yml:63-106`, `tests/integration/test_oauth_flow_exapp.py:99-125`

**Issue:** The `exapp` job builds the whole HaRP topology and writes `.env.exapp`, but runs
only `test_exapp_dav_matrix.py` and `test_permission_fidelity_exapp.py`. The `integration` job
runs `pytest -m integration` against `compose.test.yml`, where the fixture of the OAuth test
skips for lack of the ExApp variables. So the five checks that prove this whole phase (token
over the chain, survival of a restart, two accounts stay two, revocation, throttle) are green
only when somebody runs them by hand, and every regression in the flow ships unnoticed.

**Fix:** Add a step to the `exapp` job, right after the two that already exist:

```yaml
      - name: The OAuth connection over the full chain (AUTH-02, AUTH-03, SC 4, SC 5)
        run: |
          set -a && . ./.env.exapp && set +a
          uv run pytest tests/integration/test_oauth_flow_exapp.py -m integration
```

### WR-12: `POST /connect` carries no anti forgery value, so any site can make a visitor open a Nextcloud login flow

**File:** `src/mcp_connector/oauth/connect.py:144-155`, `src/mcp_connector/exapp/ui/connect.py:88-101`

**Issue:** The consent decision is bound to its form by `CONFIRM_PARAM`, the onboarding start
is not. A cross origin form that posts `action=start` to `<public url>/connect` makes the
visitor's browser create a Nextcloud login flow (one PHP round trip plus one 20 minute record
per submission). The attacker cannot read the answer, so this is not a credential leak; it is
forced state creation and it multiplies CR-02.

**Fix:** Render a hidden token on the invitation page and require it in `begin`. Since there
is no session, derive it the same way the consent form does, from the data key plus a short
lived, page bound nonce, or simply require an `Origin`/`Sec-Fetch-Site` check on this one
POST:

```python
    origin = request.headers.get("origin") or ""
    if origin and origin != urlsplit(config.public_url(env))._replace(path="").geturl():
        return _with_status(invitation_page(env=env), 400)
```

## Info

### IN-01: The cancel action is implemented, tested and unreachable

**File:** `src/mcp_connector/oauth/connect.py:148-149`, `:210-219`, `src/mcp_connector/exapp/ui/strings.py:132-134`

**Issue:** No page renders a button with `action=cancel`; `ACTION_CANCEL_CONNECTION` and
`ACTION_CANCEL_SIGN_IN` are exported and unused. The route branch and its test therefore cover
a path a user cannot reach.

**Fix:** Either render the cancel button on the handoff and waiting screens (the copy exists),
or delete the branch, the two strings and `tests/unit/test_oauth_connect.py:418`.

### IN-02: `_has_expired` ignores the provider's injected clock

**File:** `src/mcp_connector/oauth/provider.py:1192-1203`

**Issue:** Every other time decision in the provider goes through `self._now()`; this one
calls `time.time()` through a default argument that no caller fills, so a test that moves the
clock cannot move the registration windows.

**Fix:** Pass `now=self._now()` at the call site in `get_client`.

### IN-03: The metadata document does not advertise `none` for the revocation endpoint

**File:** `src/mcp_connector/oauth/metadata.py:172-178`

**Issue:** `token_endpoint_auth_methods_supported` gains `none`, but the SDK also emits
`revocation_endpoint_auth_methods_supported = ["client_secret_post", "client_secret_basic"]`
and that list is left untouched. `FamilyRevocation` explicitly supports public clients (that is
why `_RevocationRequest` makes `client_secret` optional), so the document understates what the
server does and a strict client concludes it cannot revoke.

**Fix:** Append `PUBLIC_CLIENT_AUTH_METHOD` to
`metadata.revocation_endpoint_auth_methods_supported` next to the token endpoint list.

### IN-04: Two different definitions of "a safe client name"

**File:** `src/mcp_connector/exapp/ui/layout.py:415-431`, `src/mcp_connector/oauth/loginflow.py:137-155`

**Issue:** `safe_user_agent` reduces the name to printable ASCII; `client_name` accepts every
`str.isprintable()` character, so the name Nextcloud shows and the name our consent screen
shows can differ (homoglyphs, right to left marks that are not `Cf`, emoji). On a page whose
job is recognition, the two should not disagree.

**Fix:** Route both through one helper, or restrict `client_name` to the same printable ASCII
range and note the deliberate loss for non Latin names.

### IN-05: The onboarding handoff renders the Nextcloud link without the host check the consent path applies

**File:** `src/mcp_connector/oauth/connect.py:207`, `src/mcp_connector/oauth/consent.py:447-469`

**Issue:** `_start` passes `started.login_url` straight into `handoff_page`, checked only for
its scheme in `loginflow.start_flow`. The value comes from the configured Nextcloud, so it is
not attacker input, but a misconfigured `overwrite.cli.url` puts a foreign host behind the
same button that `_sign_in_link` refuses to render on the other surface.

**Fix:** Call the same host check on both paths.

### IN-06: The `compare_digest` in the two caches guards nothing the lookup did not already leak

**File:** `src/mcp_connector/oauth/provider.py:720-735`, `src/mcp_connector/oauth/verifier.py:264-280`

**Issue:** Both docstrings claim "nothing about a lookup can be learned from its duration",
but the entry is found by `dict.get(digest)` first; the constant time comparison afterwards is
against the key the dictionary just matched and can never differ (both branches are marked
`pragma: no cover` for that reason). The timing property comes from hashing the token, not
from the comparison.

**Fix:** Keep the code, correct the comment: the digest is what makes the lookup safe; the
comparison is belt and braces.

---

_Reviewed: 2026-08-16T05:02:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard, security focus_
