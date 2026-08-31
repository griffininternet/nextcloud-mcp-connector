---
phase: 18-audit-log-kern
reviewed: 2026-08-31T11:55:05Z
depth: standard
files_reviewed: 45
files_reviewed_list:
  - .github/workflows/ci.yml
  - appinfo/info.xml
  - docs/oauth-setup.md
  - src/mcp_connector/audit/__init__.py
  - src/mcp_connector/audit/accounts.py
  - src/mcp_connector/audit/allowlist.py
  - src/mcp_connector/audit/record.py
  - src/mcp_connector/audit/store.py
  - src/mcp_connector/config.py
  - src/mcp_connector/deps.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/errors.py
  - src/mcp_connector/exapp/admin_settings.py
  - src/mcp_connector/exapp/audit_verify.py
  - src/mcp_connector/exapp/config_values.py
  - src/mcp_connector/exapp/lifecycle.py
  - src/mcp_connector/exapp/middleware.py
  - src/mcp_connector/exapp/occ.py
  - src/mcp_connector/exapp/ui/strings.py
  - src/mcp_connector/ids.py
  - src/mcp_connector/nextcloud/clients/caldav.py
  - src/mcp_connector/nextcloud/clients/carddav.py
  - src/mcp_connector/nextcloud/clients/dav.py
  - src/mcp_connector/nextcloud/clients/ocs.py
  - src/mcp_connector/oauth/verifier.py
  - src/mcp_connector/paging.py
  - src/mcp_connector/server/__init__.py
  - src/mcp_connector/tools/talk.py
  - tests/contract/test_audit_surface.py
  - tests/contract/test_no_destructive_calls.py
  - tests/integration/test_appapi_users_list.py
  - tests/unit/test_audit_accounts.py
  - tests/unit/test_audit_caller.py
  - tests/unit/test_audit_record.py
  - tests/unit/test_audit_store.py
  - tests/unit/test_config.py
  - tests/unit/test_errors_reason.py
  - tests/unit/test_exapp_admin_settings.py
  - tests/unit/test_exapp_audit_verify.py
  - tests/unit/test_exapp_config_values.py
  - tests/unit/test_exapp_entry.py
  - tests/unit/test_exapp_lifecycle.py
  - tests/unit/test_exapp_purge.py
  - tests/unit/test_oauth_verifier.py
findings:
  critical: 0
  warning: 3
  info: 7
  total: 10
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-08-31T11:55:05Z
**Depth:** standard
**Files Reviewed:** 45
**Status:** issues_found

## Summary

Reviewed the complete audit-log core of phase 18: the SQLite store with per-user hash chains
(`audit/store.py`), the recording path behind `@graceful` (`audit/record.py`,
`server/__init__.py`), the caller resolution (`deps.resolve_caller`), the allowlist of
parameter names, the D-14 switch through config/admin form/`entry_exapp`, the account check
of D-12 (`audit/accounts.py`), the occ check command (`exapp/audit_verify.py`, `exapp/occ.py`)
and the `reason=` retrofit across the clients, `ids.py`, `paging.py` and `tools/talk.py`.

The privacy boundaries hold under adversarial reading: no path writes a parameter value,
`exc.message`/`exc.hint`, an IP or a user agent into a row; the allowlist is intersected with
the actually-sent argument names, and contract tests measure the surface instead of trusting
it. The switch is genuinely off by default (positive membership test, typo stays off), the
off state creates no file, `/audit-verify` is absent from the manifest and double-guarded,
the account check fails toward keeping (`None`/empty list never deletes), and `verify_token`
carries the client name in a claim without a second lookup. The chain construction
(seq-in-hash, `BEGIN IMMEDIATE` around read-predecessor-plus-insert, AUTOINCREMENT against
seq reuse) is correct; the 20-concurrent-writers fork test confirms it. The `_bounded_number`
parser correctly guards against the Unicode-digit and 4300-digit `int()` traps.

No critical finding. Three warnings concern the integrity check producing **false tamper
alarms** after a mid-sweep crash or a backwards clock step (the second one reproduced against
the real store during this review), and the unbounded growth of the never-trimmed instance
chain inside the fixed 100 MB budget.

## Narrative Findings (AI reviewer)

### Warnings

### WR-01: Crash between sweep deletion and tombstone write leaves an unexplained gap that reads as tampering

**File:** `src/mcp_connector/audit/store.py:589-672` (`_sweep_expired`, `_sweep_over_limit`, `_write_tombstones`, called from `sweep` at 798-811)
**Issue:** The sweep deletes rows in per-batch transactions that each **commit** (`_sweep_expired`/`_sweep_over_limit`), and only afterwards writes the explaining markers in a separate transaction (`_write_tombstones`). A process kill, OOM or power loss between a committed delete batch and the marker commit leaves chains whose heads point at removed rows with no `gap_hash` explaining them. The next `verify_chains` (and thus `occ mcp_connector:audit:verify`, AUDIT-02) then reports `FINDING_MISSING` — indistinguishable from real manipulation — after a perfectly ordinary crash. The same window exists across the whole multi-batch run: every batch commit before the final marker widens it.
**Fix:** Make the marker atomic with the deletion it explains. Simplest shape: inside each batch transaction, after the `DELETE`, upsert/append the tombstone for every chain touched by that batch before the `COMMIT` (the marker's `gap_hash` is already known from the batch that was just read). Alternatively write a provisional "sweep in progress" marker (chain + intended end hash) *before* the first delete and finalize it afterwards, so the verifier can classify the gap.
**Fixed:** fef59ff `_write_markers` now runs inside the same `BEGIN IMMEDIATE` transaction as each batch deletion (both sweep steps), so every committed state explains its own gaps and a failed batch rolls back whole; fault-injection tests cover the single-batch and the mid-run crash.

### WR-02: Retention sweep assumes `at` is monotonic per chain; a backwards clock step produces a false "missing" finding (reproduced)

**File:** `src/mcp_connector/audit/store.py:322-327` (`_EXPIRED_ROWS`/`_DROP_EXPIRED`), `574-586` (`_note_removed`), `700-737` (`_first_finding`)
**Issue:** `_sweep_expired` removes every user row with `at <= cutoff`, and `_note_removed` remembers only the **highest-seq** removed row per chain as the `gap_hash`. That is only correct when expired rows form a seq-prefix of each chain, i.e. when `at` never decreases within a chain. `at` comes from `int(time.time())` at write time (`record.note`, `store._now`), so an NTP step backwards, a VM resume or a host clock correction creates an inversion (younger `at` on a lower seq). When a later sweep's cutoff lands inside that inversion window, rows are removed from the **middle** of the chain; the surviving row after the hole points at a hash no tombstone names, and `verify_chains` reports a break. Reproduced against the real store during this review:

```python
# seq1 at=base, seq2 at=base+400d (clock jumped), seq3 at=base+1, seq4 at=base+400d+1
await subject.sweep(moment=base + 180 * 86400 + 10)   # cutoff removes seq1 and seq3 only
await subject.verify_chains()
# -> [ChainFinding(chain='u:alice', kind='missing', seq=2, next_seq=None)]
```

A false tamper alarm is the worst answer an integrity command can give an administrator (AUDIT-02).
**Fix:** Delete a seq-prefix per chain instead of an `at`-predicate: per chain, compute `max(seq)` among expired rows and delete `chain = ? AND seq <= that`, so the removed block is always contiguous and the recorded end hash is always the predecessor of the surviving head. (Equivalently: record the hash of *every* removed row's successor boundary, or record all removed hashes per chain in the marker.)
**Fixed:** 3376f63 `_EXPIRED_ROWS`/`_DROP_EXPIRED` now take only the expired seq-prefix of each chain (a row goes only when no younger-than-cutoff row stands at a lower seq), so the recorded end hash is always the predecessor of the surviving head; the review's non-monotonic-clock reproduction is the regression test.

### WR-03: The instance chain grows without bound inside the fixed size budget and can never be reclaimed

**File:** `src/mcp_connector/audit/store.py:641-672` (`_write_tombstones`), `322-327` (`chain <> ?` in every sweep statement), `611-638` (`_sweep_over_limit`)
**Issue:** Every sweep run appends one tombstone per affected chain to `i:instance`, switch rows are added on every state change, and no statement ever removes an instance row (by design — it is the register of gaps). In steady state past the retention window, every sweep (every 500 rows, D-11) writes up to one marker per active user chain: with e.g. 50 active users that is ~10 % of all rows ever written, accumulating **permanently**. Those rows count toward `used_bytes` against the 100 MB bound, but `_sweep_over_limit` may only delete user rows (`chain <> CHAIN_INSTANCE`) and stops when none are left. Over years on a busy instance the permanent markers squeeze the actual audit rows out of the budget, and in the limit the store sits permanently over its bound with nothing left to sweep (`SWEEP_MAX_ROUNDS` prevents the endless loop, but not the state). The module comments name this state "a different fault" without a path to it being reported or resolved.
**Fix:** Bound the register: e.g. when the sweep affects a chain that already has a tombstone as the newest instance row for the same `gap_chain`, write one consolidated marker (new row with summed `removed` and the new end hash) and let a later sweep drop the superseded markers of the same chain with their own explanation; or track cumulative gap state per chain in a second small table outside the hash chain. At minimum, have `overview`/`audit-verify` report when the store is over its bound with no sweepable row left, so the state is visible instead of silent.
**Fixed:** a38d250 `_write_markers` consolidates the trailing run of tombstones in the same transaction (summed `removed`, newest end hash, tail-only replacement keeps the instance chain verifiable; switch rows are barriers), so the register grows with switches and chains, never with sweeps; `StoreOverview` gained `used_bytes`/`sweepable_entries` and `audit-verify` names the over-bound-unevictable state in text and JSON.

### Info

### IN-01: Dead code: `AuditStore._write` and the `commit=True` path of `_call`

**File:** `src/mcp_connector/audit/store.py:966-968`, `974-1004`
**Issue:** `_write` has no caller (every writer uses `_transaction`), so the `commit=True` branch of `_call` — including its `BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK` machinery and its docstring about the busy-timeout rollback case — is unreachable.
**Fix:** Remove `_write` and the `commit` parameter, or add the caller the plumbing was written for.

### IN-02: Three divergent sanitizers for names from outside; Unicode format characters pass two of them

**File:** `src/mcp_connector/audit/record.py:106-120` (`_clamped_client_name`, `isprintable()`), `src/mcp_connector/audit/store.py:463-477` (`_clean_client_name`, `< " "` only), `src/mcp_connector/exapp/audit_verify.py:246-265` (`_printable`, `< " "` only)
**Issue:** The recorder filters with `str.isprintable()` (drops Cf characters such as U+202E RLO or U+200B ZWSP); the store and the check command only replace C0 controls and DEL. `store.py` claims "control characters never enter a row at all" (line 134), but a bidi override in a client name written through `Entry` directly, or in an account name printed by `_printable`, survives and can visually reorder the occ answer within its line (the documented in-line spoofing boundary, but wider than the docstrings state). Three hand-rolled copies with different rules are how this drifts further.
**Fix:** One shared cleaner (the `isprintable()` variant is the stricter of the two) used by all three sites; the layering argument against importing does not preclude a leaf `audit/text.py`.

### IN-03: `audit_verify._payload` can raise on a Unicode-digit `content-length`

**File:** `src/mcp_connector/exapp/audit_verify.py:348-349`
**Issue:** `announced.isdigit() and int(announced)` — `"²".isdigit()` is `True` and `int("²")` raises `ValueError`, which escapes the handler as a 500 (only reachable by an authenticated AppAPI caller, and conforming HTTP stacks reject such a header first). `config._bounded_number` guards the exact same trap with `isascii() and isdigit()`; this site does not.
**Fix:** `if announced.isascii() and announced.isdigit() and int(announced) > MAX_BODY_BYTES:`

### IN-04: Tombstone/switch rows can swallow a sweep trigger

**File:** `src/mcp_connector/audit/store.py:432-449` (`should_sweep`, `should_check_accounts`), `record.py:248-260`
**Issue:** Markers and switch rows consume sequence numbers via `_append_row`, but the triggers are evaluated only on the seq returned by a tool-call `append`. When a tombstone happens to occupy an exact multiple of `SWEEP_EVERY` (or of the 10 000-row account-check multiple), that trigger fires for nobody and the schedule slips one full interval. Harmless drift for the sweep; for the rare account check it doubles the wait.
**Fix:** Trigger on crossing (`seq % SWEEP_EVERY < rows_written_by_this_append`-style) or accept and document the slip with a test.

### IN-05: `record.note` is not exception-free under task cancellation

**File:** `src/mcp_connector/audit/record.py:202-263`; `src/mcp_connector/server/__init__.py:132-133`
**Issue:** `note`'s docstring and the `finally` contract in `graceful` (T-18-17) rest on "never raises", but the internal `await`s (`store_provider()`, `append`, `sweep`) raise `asyncio.CancelledError` in a cancelled task, which is a `BaseException` and escapes `except Exception`. A cancellation arriving while the row is being written propagates out of the `finally` and can replace the tool's own in-flight exception. Standard asyncio semantics and low impact, but the stated invariant is narrower than documented.
**Fix:** Either shield the single-row write (`asyncio.shield` around `append` only, never the sweep) or soften the docstring/D-13 wording to "never raises except cancellation".

### IN-06: The admin-form description understates what a row stores

**File:** `src/mcp_connector/exapp/ui/strings.py:648-653` (`ADMIN_FIELD_AUDIT_LOG_DESCRIPTION`)
**Issue:** The sentence lists account, tool, time, calling app and outcome, and says no parameter value and no result part is stored — all true — but omits that the **names** of the set parameters, the fixed rejection reason and the duration are recorded too. For the one switch an administrator has to justify to a works council, the short version currently says less than the row holds; the full wording is deferred to phase 19 by decision, but the short version should not undercount.
**Fix:** Extend the sentence by one clause, e.g. "..., the names (never the values) of the parameters that were set, and how long the call took."

### IN-07: Tests write the switch direction into `reason=`, production writes it into `outcome=`

**File:** `tests/unit/test_audit_store.py:259-293`, `tests/unit/test_audit_accounts.py:324,370,383`
**Issue:** Several store tests build switch rows as `Entry(..., kind=KIND_SWITCH, reason="on")` while `note_switch` (production) writes the direction into `outcome` and `entry_exapp._audit_startup` reads `last.outcome`. The tests exercise the store's kind filter correctly, but they document a row shape production never writes; a reader taking the tests as the schema of a switch row would read the wrong column.
**Fix:** Use `outcome=SWITCH_ON/SWITCH_OFF` in the test fixtures, matching `note_switch`.

---

_Reviewed: 2026-08-31T11:55:05Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
