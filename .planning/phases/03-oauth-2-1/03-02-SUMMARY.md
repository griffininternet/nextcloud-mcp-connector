---
phase: 03-oauth-2-1
plan: 02
subsystem: auth
tags: [sqlite, wal, aes-gcm, aead, cryptography, appapi-config, token-store, refresh-rotation]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "the AppAPI deploy environment, exapp/status.py as the one shape of an outgoing OCS call, and APP_PERSISTENT_STORAGE declared but unread"
  - phase: 01-server-kern
    provides: "config.py with its env constants and fail closed helpers, errors.ToolError, nextcloud/http.shared_client and the masked credential objects"
provides:
  - "oauth/crypto.py: AES-GCM with the row id as additional authenticated data, plus the data key of the installation from Nextcloud's ExApp configuration (sensitive=1, D-43)"
  - "oauth/store.py: the full schema of 03-RESEARCH.md in one SQLite file, with the atomic refresh rotation, the single use authorization code and opportunistic cleanup"
  - "config.persistent_storage: the store directory from APP_PERSISTENT_STORAGE, fail closed in the ExApp mode and a named development fallback otherwise"
  - "entry_exapp.main refuses to start without a writable volume (exit code 2)"
  - "cryptography as a declared direct dependency, with the owner decision written down"
affects: [03-04 login flow bridge, 03-05 authorize and consent, 03-06 token endpoint and verifier, 03-07 refresh rotation and revocation, 03-08 staging proof, 04 admin ui]

# Tech tracking
tech-stack:
  added: ["cryptography>=50,<51 (promoted from transitive to direct, owner approved 2026-08-16)"]
  patterns:
    - "one encryption entry point, bound to the id of the row the ciphertext is stored in"
    - "the data key lives in a different trust boundary than the data it protects"
    - "compare and set inside BEGIN IMMEDIATE for every state change two requests can race for"
    - "three named failure outcomes instead of one boolean, so the caller can react differently"
    - "an unreadable answer is never read as an empty one (fail closed on parse failures)"
    - "one connection per call in a worker thread, so two workers behave like two threads"

key-files:
  created:
    - src/mcp_connector/oauth/crypto.py
    - src/mcp_connector/oauth/store.py
    - tests/unit/test_oauth_crypto.py
    - tests/unit/test_oauth_store.py
  modified:
    - src/mcp_connector/config.py
    - src/mcp_connector/entry_exapp.py
    - pyproject.toml
    - uv.lock
    - vulture_whitelist.py
    - .gitignore
    - docs/dependency-audit.md
    - tests/unit/test_config.py
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_project_layout.py
    - tests/contract/test_no_destructive_calls.py

key-decisions:
  - "The data key is fetched, then written, then read back: two workers starting at once both continue with the one value that actually survived, instead of one of them encrypting with a key nobody will ever read"
  - "An ExApp configuration answer that cannot be parsed raises instead of counting as an absent key, because 'I could not read it' turning into 'there is none yet' is what would overwrite a live key"
  - "A stored key that is not exactly 32 bytes of hex is a named failure, not a shorter cipher"
  - "The refresh redemption inserts the successor inside the same transaction, so a crash between the two writes cannot leave a user without any valid token"
  - "The redemption returns unknown, expired and reused as three outcomes, because 03-07 kills the family only for the third"
  - "Access token validity is a join against the authorization, so revoking a connection takes effect at once instead of at the next sweep"
  - "The writability of the volume is checked by writing a file, because os.access reports permission bits and says nothing about a read only bind mount"
  - "Client expiry runs in purge_expired only, never in the write path, because deleting a client deletes its authorizations through the cascade"
  - "cryptography is declared directly (owner approved 2026-08-16); the lock step used uv lock, not uv add, to leave the virtual environment untouched"

patterns-established:
  - "Byte level leak test: the whole store directory including the write ahead log is read as bytes and searched for every plaintext secret"
  - "Concurrency proof by asyncio.gather over two real threads on one SQLite file, asserting exactly one winner"
  - "Source gates on a module: no second HTTP client, no retry loop, no derivation from the transport secret"
  - "A narrow, counter proved exemption instead of a disabled gate when a rule collides with a new context (SQL DELETE in our own store)"

requirements-completed: []  # AUTH-03 is carried by this plan but stays Pending, see below
requirements-advanced: [AUTH-03]

# Metrics
duration: 95min
completed: 2026-08-16
---

# Phase 3 Plan 02: Encrypted token store Summary

**A SQLite store with the full OAuth schema, AES-GCM at rest with the row id as aad, a data key held in Nextcloud's ExApp configuration instead of beside the database, and a refresh rotation that produces exactly one winner under two parallel requests.**

## Performance

- **Duration:** about 95 min
- **Tasks:** 3 of 3 (two TDD tasks, one owner gate that was already resolved)
- **Files created:** 4
- **Files modified:** 11
- **New checks:** 47 in `test_oauth_crypto.py`, 34 in `test_oauth_store.py`, plus 12 in `test_config.py`, `test_exapp_entry.py` and `test_project_layout.py`

## Accomplishments

- Every secret this phase writes to disk now has exactly one way in and one way out, and it is bound to the row it lives in: a ciphertext moved to another authorization is refused instead of decrypted.
- The key that protects those secrets is not derived from the transport secret of the AppAPI registration (pitfall 11, T-03-14) and does not live in the volume it protects. A re-registration no longer has the power to silently kill every connection.
- The rotation of a refresh token is a compare and set inside `BEGIN IMMEDIATE`, proved with two redemptions running in parallel threads against one file: one `ok`, one `reused`, exactly one surviving successor.
- A missing or read only volume is now a startup failure with a named message and exit code 2, instead of a store that works perfectly until the first container restart.
- The last reserved name of phase 2 got a reader: `ENV_APP_PERSISTENT_STORAGE` left `vulture_whitelist.py` (pitfall 12).

## Task Commits

1. **Task 1: data key and AES-GCM with row binding** (TDD)
   - `760b4b0` test: the failing checks for the data key, the encryption and the volume
   - `828017d` feat: `oauth/crypto.py`, `config.persistent_storage`, the startup check
2. **Task 2: SQLite store with the full schema and atomic redemption** (TDD)
   - `7339589` test: the failing checks for the token store
   - `36b1d32` feat: `oauth/store.py` plus the narrowed destructive call gate
3. **Task 3: owner gate for cryptography as a direct dependency**
   - `99bf8c2` chore: the declaration in `pyproject.toml`, the lock line and the audit entry

## Files Created/Modified

- `src/mcp_connector/oauth/crypto.py` - `encrypt`/`decrypt` with a fresh 12 byte nonce and `aad` equal to the row id, `DecryptionRejected` without a message, and `data_key` against the ExApp configuration route.
- `src/mcp_connector/oauth/store.py` - the six tables of 03-RESEARCH.md, WAL, foreign keys and a busy timeout on every connection, the row objects with masked reprs, and the redemption logic.
- `src/mcp_connector/config.py` - `persistent_storage` with the four refusals and the named development fallback, plus `_probe_writable`.
- `src/mcp_connector/entry_exapp.py` - the volume check beside the existing `exapp_settings` check.
- `vulture_whitelist.py` - `ENV_APP_PERSISTENT_STORAGE` removed, the store API added with the plans that will call it.
- `.gitignore` - the development store directory, which holds encrypted app passwords.
- `docs/dependency-audit.md` - the `cryptography` row and the section on the promotion.
- `tests/contract/test_no_destructive_calls.py` - a narrow SQL exemption with its own counter proof.

## Decisions Made

Beyond the frontmatter list, three worth naming here:

- **Lifetimes are module constants in `store.py`,** not literals at call sites: 60 s for a code, 3600 s for an access token, 30 days for a refresh token, 1200 s for a flow, 5 s validation cache, 10 s rotation grace (D-41), 24 h for an unused registration and 90 days for an idle client. A test asserts every one of them, so a change is one line and a visible diff.
- **The asymmetry in `revoke_family` is intentional:** refresh tokens carry a `state`, access tokens carry a `revoked_at`. Code example 4 of the research writes `state` on both, but the schema, which is the binding artifact, gives only the refresh tokens a state machine. The code follows the schema and the docstring says why.
- **The read form of the ExApp configuration is one constant** (`CONFIG_READ_PARAM`) with a comment saying it is the one thing here not yet confirmed against a running AppAPI. Plan 03-08 confirms it; a correction is one line plus its test.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The destructive call gate refused every SQL `DELETE` of the store**

- **Found during:** Task 2 (the store implementation)
- **Issue:** `tests/contract/test_no_destructive_calls.py` forbids the token `DELETE` anywhere in `src/`, which is a promise about what this server does to data *in Nextcloud* (TOOL-09). The store has to delete expired codes, flows, tokens and unused registrations from its own file, and the schema itself carries `ON DELETE CASCADE`. Thirteen findings, none of them a request to Nextcloud.
- **Fix:** A deliberately narrow exemption: in `oauth/store.py` only, and only for the two exact forms `DELETE FROM ` and `ON DELETE CASCADE`. Everything else keeps firing, `.delete(` is never exempt, and an HTTP `DELETE` written inside the store is still a finding.
- **Files modified:** `tests/contract/test_no_destructive_calls.py`
- **Verification:** New counter proof `test_the_sql_exemption_covers_sql_and_nothing_else`, which asserts that `await client.request("DELETE", url)` in the store is still reported and that the same SQL in `tools/files.py` is not exempt.
- **Committed in:** `36b1d32`

**2. [Rule 2 - Missing safety] The startup test of the port would have passed for the wrong reason**

- **Found during:** Task 1 (the startup check)
- **Issue:** `test_a_missing_or_broken_port_stops_the_start` asserts exit code 2. With the new volume check in `main`, the process would exit before ever reaching the port parsing, so the test would stay green while testing nothing.
- **Fix:** The test sets `APP_PERSISTENT_STORAGE` to a `tmp_path`, and two new tests cover the volume check itself, one for the exit code and one for the log line that names the variable.
- **Files modified:** `tests/unit/test_exapp_entry.py`
- **Verification:** Both new tests fail without the check in `entry_exapp.main`.
- **Committed in:** `760b4b0` (test) and `828017d` (feat)

**3. [Rule 2 - Missing safety] A read back after the key was written**

- **Found during:** Task 1
- **Issue:** The plan describes create-then-use. Two workers starting at the same time would both find no key, both store one, and the loser would encrypt everything with a key that no longer exists in Nextcloud, which is exactly the silent data loss D-43 exists to prevent.
- **Fix:** `data_key` reads the value back after writing it and returns what actually survived; a key that is gone at that point is a named failure.
- **Files modified:** `src/mcp_connector/oauth/crypto.py`
- **Verification:** `test_the_first_start_creates_the_key_and_stores_it_as_sensitive` asserts two reads, and `test_a_key_that_disappears_between_write_and_read_back_is_a_named_failure` covers the loser.
- **Committed in:** `828017d`

**4. [Rule 2 - Missing safety] A vulture whitelist block for the store API**

- **Found during:** Task 2
- **Issue:** The store is built in one piece but consumed by plans 03-04 to 03-07, so nineteen methods and five row fields have no production caller yet and the dead code gate fails at full confidence.
- **Fix:** One whitelist block that names, per group, which plan will call it and that `tests/unit/test_oauth_store.py` exercises all of them. The alternative, lowering the confidence threshold, would have made the gate decorative for the whole repository.
- **Files modified:** `vulture_whitelist.py`
- **Committed in:** `36b1d32`

---

**Total deviations:** 4 auto-fixed (1x Rule 3, 3x Rule 2)
**Impact on plan:** No scope creep. One is a gate collision that had to be resolved to commit at all, the other three close reliability holes the owner directive names explicitly.

### Requirement Status

**AUTH-03 stays Pending**, exactly as after 03-01 and 03-03. This plan builds the storage
half of the requirement and nothing a client can connect to: there is no `/authorize`, no
`/token` and no verifier yet. The requirement is claimed when a client actually completes
the flow, which is plan 03-06 for the mechanism and 03-08 for the running proof.
`REQUIREMENTS.md` is therefore unchanged.

## Owner Decision: cryptography as a direct dependency (Task 3)

**Date:** 2026-08-16. **Decision:** approved.

The question was put explicitly, with the evidence collected first: installed version 50.0.0 (matching the lock), project URLs pointing at `github.com/pyca/cryptography`, 158 releases, current version uploaded 2026-07-31, a top twenty package on PyPI, and already present in the lock through `mcp` to `pyjwt[crypto]`. `slopcheck` was not runnable in this environment because it shells out to `pip` and there is no `pip` on the PATH of this uv setup, so the verification was done by hand against the PyPI JSON API.

**Reason for approval:** `src/mcp_connector/oauth/crypto.py` imports the package directly, and the policy in `docs/dependency-audit.md` says an imported package is a declared one. Leaving it transitive would mean that the encryption of every stored app password depends on somebody else's dependency list: the day `mcp` drops `pyjwt[crypto]`, the next clean install fails at import time in production.

**Constraint respected:** no `uv sync`. The lock step used `uv lock`, which writes `uv.lock` only; the diff is two declaration lines and no version changed. The virtual environment was not touched.

## Issues Encountered

- **pyright and the generic worker functions.** The three thread wrappers of the store were typed with `Any`, which pyright rejected as an unresolvable type variable. Resolved with a named `type Work[T] = Callable[[sqlite3.Connection], T]` alias, which also made the wrappers readable.
- **`load_flow` decrypted outside the worker.** Typing the row as `tuple[object, ...]` produced ten errors at once. The construction of `FlowRow` moved into the worker function, where the sqlite row is untyped and the decryption happens on the same thread as the read.
- **Open connections on Windows.** The first version of the tests used `sqlite3.connect` as a context manager, which commits but does not close. The helpers `query` and `modify` now close in a `finally`, so no test can leave a lock behind for the next one.

## Known Stubs

None. Every function of this plan is fully implemented and exercised; what is missing is callers, which are the subject of plans 03-04 to 03-07.

## Threat Flags

None. The two new modules stay inside the threat model of the plan: `oauth/crypto.py` opens exactly one outgoing route that was already listed (the ExApp configuration route), and `oauth/store.py` opens no network surface at all.

## Next Phase Readiness

Ready for the plans that consume this:

- **03-04** gets `create_flow`, `load_flow`, `delete_flow` with an encrypted poll token, and `create_authorization` for the app password that comes out of the login flow.
- **03-05 and 03-06** get `save_client`, `load_client`, `touch_client`, `delete_client`, the single use `redeem_auth_code`, and `load_access_token` including the user id, so the verifier needs one query and no join of its own.
- **03-07** gets `redeem_refresh_token` with the three outcomes, `used_at` and `successor` for the grace window of D-41, and `revoke_family`.

Two things stay open and belong to later plans, both by design:

1. **The read form of the ExApp configuration** (`CONFIG_READ_PARAM = "configKeys[]"`) has not been confirmed against a running AppAPI. Plan 03-08 confirms it; the code carries the comment and the single constant that makes a correction a one line change.
2. **Nothing calls `data_key` or constructs an `OAuthStore` in production yet.** The wiring belongs to the plan that first needs a store instance (03-04), which is also where the process wide instance and the startup call to `purge_expired` will live.

## Self-Check: PASSED

All four created source files exist, the SUMMARY exists, and all five commits are in the
history (`760b4b0`, `828017d`, `7339589`, `36b1d32`, `99bf8c2`). All six gates of D-32 run
clean on the working tree: `ruff check .`, `ruff format --check .`, `pyright` (0 errors),
`vulture src scripts vulture_whitelist.py`, `pytest -q` (full suite green) and
`scripts/check_tool_budget.py`.

---
*Phase: 03-oauth-2-1, Plan: 02*
*Completed: 2026-08-16*
