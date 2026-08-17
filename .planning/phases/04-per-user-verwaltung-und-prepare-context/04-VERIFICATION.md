---
phase: 04-per-user-verwaltung-und-prepare-context
verified: 2026-08-17T18:05:00Z
status: passed with concerns
score: 5/5 success criteria verified
overrides_applied: 0
method: >
  1543 unit/contract tests re-run in this session (uv run --no-sync pytest),
  all six gates re-run (ruff check, ruff format --check, pyright 0/0/0,
  vulture, check_tool_budget, pytest), every BL/HI/ME/LO fix read against the
  code at HEAD 873b381, the three named blockers/highs traced to their guard
  tests and the guard tests run. No live re-deployment: the exapp topology was
  torn down at the end of plan 04-04 (STATE.md), so SC 5 and A1 rest on the
  recorded live run of 2026-08-17 plus the in-process structural guards.
concerns:  # not gaps: none blocks the phase goal, each is named for a human or a later plan
  - id: AR-04-01
    about: "A1, the rendered pixel of the settings signpost, was never seen in a browser"
    detail: >
      Measured: Nextcloud serves the form (/ocs/v2.php/settings/api/declarative/forms),
      it stands in the initial state of the personal Security page, and the page carries
      the mount div <div id="mcp_connector_mcp_connector_settings">. Not measured: the
      pixel itself, no browser was in the loop. Not a goal blocker. The switch and the
      revocation live on /connections, one click behind the signpost, and both are
      verified live and in-process; the Declarative-Settings renderer draws title,
      description and doc icon independent of the (empty) fields list, so the worst case
      is a missing wayfinding link, never a functional failure. Needs a human browser
      look at /settings/user/security before Phase 5.
  - id: AR-04-02
    about: "ME-04 / BL-10: the switch guards only /mcp, a paused account can still mint app passwords"
    detail: >
      A paused account can still complete /authorize, /authorize/decide and POST /connect,
      and Nextcloud mints a real app password on that path; only the later tool call hits
      R1. SC 1 as worded (the next tool call of the connected client fails) still holds.
      But the UI text "MCP access is switched off for your account" overstates the
      enforcement, and combined with a disconnect the set of valid Nextcloud credentials
      can still grow while the brake is pulled. Consciously deferred to BACKLOG BL-10.
      Defense-in-depth gap, not a phase-goal blocker.
  - id: AR-04-03
    about: "ME-02 / BL-08 and ME-03 / BL-09: two D-57 / anti-forgery defence-in-depth residuals"
    detail: >
      The anti-forgery values are a pure function of data key and handle, with no window,
      nonce or rotation (ME-02), and the excerpt truncation mark is in-band text a shared
      document can forge (ME-03, touches the D-57 structure argument). Both need the owner's
      HaRP identity to exploit and both are deferred with an id to BACKLOG BL-08 / BL-09.
      Named because crypto.py still describes the anti-forgery value as a full protection.
  - id: AR-04-04
    about: "SC 5 rests on a live run against a now torn-down topology, like Phase 3 C-01"
    detail: >
      The one-roundtrip measurement (1.2 per session call, 1 per authenticated request and
      that one is HaRP's own) is recorded in 04-04-MEASUREMENTS.md and is byte-identical to
      03-VERIFICATION.md. The topology is down, so it cannot be reproduced now. The
      structural property is proven in-process (one data-key fetch for three calls, the
      switch read never leaves the container) and re-run green in this session.
human_verification:
  - test: "Open Nextcloud, Settings, Security as a normal user on the exapp topology"
    expected: "A 'MCP Connector' entry with title, description and a help icon linking to {public_url}/connections is visibly rendered"
    why_human: "A1: no browser was in the live run; the DOM mount point and the served form are verified, the drawn pixel is not"
---

# Phase 4: Per-User-Verwaltung und prepare_context Verification Report

**Phase Goal:** Nutzer kontrollieren den MCP-Zugriff selbst in den Nextcloud-Settings, und
ein einziger `prepare_context`-Aufruf bündelt den relevanten Cloud-Kontext token-effizient.
**Verified:** 2026-08-17T18:05:00Z
**Status:** passed with concerns (four named concerns, none blocks the goal; one human browser look outstanding)
**Re-verification:** No, initial verification

## Goal Achievement

This verification did not rely on the four SUMMARY files, on 04-REVIEW.md or on the prose of
04-04-MEASUREMENTS.md. The tree at HEAD `873b381` was checked out, the full unit and contract
suite was re-run in this session (**1543 passed, 82 deselected**), all six gates were re-run
clean, and the three named review blockers/highs were traced from their fix commit to the
code and to a guard test that was executed here. What could not be reproduced is the live
chain: the exapp topology was deliberately torn down at the end of plan 04-04 (volumes kept,
`nc_app_mcp_connector` removed, per STATE.md), so SC 5 and A1 rest on the recorded run of
2026-08-17 plus in-process structural guards, the same shape of evidence Phase 3 carried
under C-01.

### Observable Truths (ROADMAP Success Criteria, Phase 4, plus the SC 5 round-trip contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nutzer aktiviert/deaktiviert den MCP-Zugriff in den Nextcloud-Settings; Deaktivierung wirkt sofort, der nächste Tool-Aufruf des verbundenen Clients schlägt mit klarer Meldung fehl, auf beiden Anschlussarten, ohne neue Anmeldung nach resume, ohne zusätzlichen Nextcloud-Roundtrip | VERIFIED | The gate is the third check of the one transport boundary (`middleware.py:139-191`): handshake (R3), bearer (R2), then the switch (R1). Both connection types resolve to the same call: `nc_user = user or (identity.nc_user ...)` covers the AUTH-01 app-password branch (`user` from the HaRP handshake) and the OAuth branch (identity the bearer resolved to). A paused account gets `403` with `_ACCESS_DISABLED_BODY`, `application/json`, `no-store`, **no** `WWW-Authenticate`; an invalid token still gets `401` before the switch is ever consulted; a store failure is `503` fail-closed. The read is local SQLite with no cache, so resume works with the same token and costs no second Nextcloud roundtrip (D-47, D-48). Guard tests re-run green here: `test_flipping_the_switch_takes_effect_on_the_very_next_request`, the wired end-to-end guard in `test_exapp_entry.py` (pause via POST /connections → next MCP request 403 → resume → 200 same token), and `test_an_invalid_bearer_of_a_paused_account_is_still_the_discovery_401` (asserts `switch.asked == []`). Live measurement 2 (04-04-MEASUREMENTS.md): before 200, `action=pause` → 403 `access_disabled` no `WWW-Authenticate` `no-store`, `action=resume` → 200 same token. The signpost lives one click behind in the Nextcloud Security settings (D-44, EXAPP-02 wording note accepted); see AR-04-01. |
| 2 | Nutzer sieht seine verbundenen Clients und widerruft einzelne Tokens, ohne andere Clients zu beeinflussen; die Seite ist funktionsfähig und ownership-sicher | VERIFIED | Route 13 `^/connections/?$`, PUBLIC with an in-app identity check, declared identically in `appinfo/info.xml` (13 routes) and `scripts/bootstrap_exapp.sh`. Ownership is `is_user` (`compare_digest`) per row; unknown, foreign and already-revoked handles answer the same page minus the nonce, so no existence oracle (`test_an_unknown_a_foreign_and_a_revoked_handle_answer_the_same_page`). Exactly one revocation path: a source guard keeps `revoke_authorization`/`revoke_family` out of both new modules and forces the route through `provider.end_connection`, which invalidates the verifier cache. `test_a_disconnect_leaves_every_other_connection_alone` and `test_a_disconnect_stops_the_token_of_that_connection_at_once` re-run green. |
| 3 | Ein `prepare_context`-Aufruf liefert Dateien, Termine, Notizen und Deck-Karten gebündelt und token-effizient, mit Kurz/Voll-Parameter und parallelem Fan-out | VERIFIED | `tools/context.py` composes `unified_search` (no provider restriction, so Findling is inherited, D-53) + `calendar.list_events` (computed window) + `chatgpt.fetch` (excerpts in full only). Grouped by `kind` into file/note/card/other buckets. Parallel is proven not asserted: `test_both_sources_run_at_the_same_time` deadlocks a sequential implementation. Registered as the 16th tool (`EXPECTED_TOOLS` count 16, `prepare_context` present; `read_only_hint`, no output schema, property set `{query, detail}`, third-party warning in the description). Tool budget 11268/12500 bytes, exit 0. Live measurement 5: 0.84 s short, 0.99 s full, hits from files, notes and calendar events, origin as structure. |
| 4 | Fällt eine Teilquelle aus oder überschreitet ihr Budget/Timeout, ist sie explizit als degradiert markiert, keine stillen Teil-Ergebnisse | VERIFIED | Each source has its own budget (15 s per search provider, `CALENDAR_BUDGET=10`, 5 s per excerpt), never one around the `gather`. Every cap writes its own `degraded` entry (`MAX_PER_BUCKET=5`, `MAX_EVENTS=10`); the search's and calendar's own `degraded` entries pass through unchanged; a stalled excerpt is degraded under the hit id and the hit stays in short form; both sources failing is a `ToolError`, never an empty bundle. Green here: `test_a_stalling_calendar_is_named_and_the_search_hits_still_arrive`, `test_short_caps_every_bucket_and_says_that_it_capped`, `test_a_reader_that_stalls_is_degraded_under_its_own_id`. |
| 5 | Der Schalter kostet keinen zusätzlichen Nextcloud-Roundtrip: SC 5 aus Phase 3 (ein Roundtrip je MCP-Aufruf) bleibt die Obergrenze (D-47) | VERIFIED (in-process; live-corroborated, not reproducible now, AR-04-04) | In-process guard re-run green: `test_the_switch_costs_no_nextcloud_round_trip_per_request` (one data-key fetch for three served MCP requests, the switch read never leaves the container). Live measurement 3 (04-04-MEASUREMENTS.md): `5 accepted MCP calls -> 6 Nextcloud requests (1.2 per call)`, `5 refused -> 5 (1.0)`, the single per-request path is HaRP's own `user-info`, byte-identical to 03-VERIFICATION.md. |

**Score:** 5/5 truths verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/exapp/middleware.py` | R1 switch gate at the one boundary, both branches, 403/401/503 contract | VERIFIED, WIRED | Order R3→R2→R1; both identity branches merge into `_switch_refusal`; 403 `access_disabled` no challenge, 401 for a bad bearer before the switch, 503 fail-closed on a store error |
| `src/mcp_connector/oauth/store.py` | `user_access` table, `set_access`, `access_disabled`, `authorizations_of_user`, `families_of_authorization` | VERIFIED, WIRED | Schema literal carries `user_access`; DELETE-on-release asymmetry; index on `authorizations(nc_user)`; UNION reader for a handle's families |
| `src/mcp_connector/tools/context.py` | prepare_context as composition, no own data source, kind grouping, caps, degraded, excerpts | VERIFIED, WIRED | `test_this_module_reads_no_content_of_its_own` holds; all knobs are named constants; 16th tool |
| `src/mcp_connector/server/reg_context.py` | registration, READ_ONLY, structured_output=False, two params, third-party warning | VERIFIED, WIRED | `@mcp.tool(annotations=READ_ONLY, structured_output=False)`, description warns of foreign content (D-57) |
| `src/mcp_connector/oauth/connections.py` | route 13, action field, ownership, HMAC, fail-closed, own throttle class, unparsable-body guard | VERIFIED, WIRED | `CLASS_CONNECTIONS` per account (HI-01), `form_or_none` → generic page not traceback (HI-02), both address spellings served (ME-05), form size bound (LO-08) |
| `src/mcp_connector/exapp/ui/connections.py` | S5-S8 templates, row_list primitive, E8, no visible handle | VERIFIED, WIRED | Handle only in hidden fields, client id shown in full, hostile client name stays text on every screen |
| `src/mcp_connector/oauth/provider.py` | `end_connection(nc_user, auth_id)`, shared revocation path, hands the app password back | VERIFIED, WIRED | BL-01: `_hand_back` called after `_end_connection`; LO-01: `nc_user` is a parameter and compared with `is_user` |
| `src/mcp_connector/exapp/settings_form.py` | link-only Declarative-Settings form, empty fields, doc_url from public_url | VERIFIED, WIRED | `fields: []`, `section_id security`, `doc_url = public_url + /connections`; registered on `enabled=1` in `lifecycle.py`, cannot break install |
| `appinfo/info.xml`, `scripts/bootstrap_exapp.sh` | 13 routes in both, route 13 with its CR-01 justification | VERIFIED | 13 `<route>` entries, connections route present with the reasoning paragraph |
| `tests/contract/test_tool_surface.py` | frozen `EXPECTED_TOOLS` of 16, own surface test, README parity | VERIFIED, GREEN | 16 tools, `prepare_context` present, surface test green |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| MCP request (both auth types) | switch decision | `middleware._switch_refusal` reading `store.access_disabled` | WIRED | `nc_user` from handshake or from the resolved bearer identity; 403/401/503 verified by guard tests |
| POST /connections (pause) | very next /mcp call | `set_access` → SQLite → `access_disabled` at the boundary | WIRED | End-to-end guard: pause → 403 → resume → 200, and a second account is untouched |
| /connections disconnect | Nextcloud app password | `provider.end_connection` → `_end_connection` → `_hand_back` → `loginflow.revoke_app_password` | WIRED | BL-01 fix: `test_a_disconnect_hands_the_app_password_back_to_nextcloud` asserts `nextcloud.deleted == [(NC_USER, APP_PASSWORD)]`, cleanup_at cleared |
| prepare_context | search + calendar + fetch | `context.prepare_context` composition, per-source budgets | WIRED | No own client; kind grouping; degraded on cap/failure |
| /enabled | Nextcloud Declarative Settings | `settings_form.register_settings_form` OCS POST, best effort | WIRED | Registered on enabled=1, failure is one log line, install cannot break |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full unit + contract suite | `uv run --no-sync pytest -q` | `1543 passed, 82 deselected` | PASS |
| Phase-4 files focused | `pytest test_connections_page test_tools_context test_exapp_entry test_exapp_lifecycle test_oauth_store test_tool_surface` | `251 passed` | PASS |
| BL-01 guard | `pytest test_a_disconnect_hands_the_app_password_back_to_nextcloud` (in focused run) | pass | PASS |
| HI-01 guards | `test_the_page_is_throttled_in_a_class_of_its_own`, `test_an_anonymous_flood_closes_neither_the_brake_nor_the_consent_surface`, `test_the_refusals_of_one_account_do_not_lock_out_another` | pass | PASS |
| HI-02 guard | `test_a_form_body_that_cannot_be_parsed_is_a_page_and_never_an_unhandled_500` | pass | PASS |
| SC 5 in-process | `pytest -k round_trip` in test_exapp_entry | `1 passed` | PASS |
| D-57 guard | `pytest ...::test_an_injected_instruction_arrives_as_data_and_moves_no_key_of_the_answer` | `1 passed` | PASS |
| Tool budget | `uv run --no-sync python scripts/check_tool_budget.py` | `11268 bytes, 16 tools, budget 12500`, exit 0 | PASS |
| Lint / format / types / dead code | `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` | clean, `150 files already formatted`, `0 errors, 0 warnings`, exit 0 | PASS |
| Debt markers in phase-4 source | grep TODO/FIXME/XXX/TBD/HACK/PLACEHOLDER over the seven modified src files | zero matches | PASS |

### Probe Execution

The project uses no `scripts/*/tests/probe-*.sh` convention; its equivalents are the unit and
contract suites and the live `scripts/oauth_flow_check.py --measure`. The suites and gates were
executed here. The live probe could not be run: the exapp topology is torn down (STATE.md),
which is the same limitation SC 5 carries under AR-04-04.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| EXAPP-02 | 04-01, 04-03, 04-04 | Nutzer aktiviert/deaktiviert MCP-Zugriff, sieht verbundene Clients, widerruft Tokens (Declarative Settings) | SATISFIED | SC 1 and SC 2 above. The switch is enforced at the boundary (04-01), the list, revocation and switch UI live on /connections (04-03), and the Declarative-Settings signpost points there (04-04). REQUIREMENTS.md marks it Complete; the wording note (switch one click behind the settings entry, D-44/D-47/D-48) is accepted |
| TOOL-08 | 04-02 | prepare_context bündelt Dateien, Termine, Notizen, Karten in einem Aufruf, Kurz/Voll | SATISFIED | SC 3 and SC 4 above; 16th tool, budget within limit, live measurement 5 |

No orphaned requirements: ROADMAP Phase 4 lists EXAPP-02 and TOOL-08, both claimed and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | TODO / TBD / FIXME / XXX / HACK / PLACEHOLDER / "not yet implemented" over the seven modified src files | none found | — |

Debt-marker gate: clean, zero matches. `vulture` over `src scripts` clean, `vulture_whitelist.py`
Phase-4 block empty (the two placeholders from 04-01 got their callers in 04-03).

### Review Findings, verified against the code and not against the report

The one BLOCKER and two HIGH of 04-REVIEW.md are genuinely closed in the tree at `873b381`,
each with a guard test that was run here:

| Finding | Fix commit | In the code now? | Guard test (run here) |
|---------|-----------|------------------|-----------------------|
| BL-01, disconnect leaves a valid Nextcloud app password behind | `700a935` | Yes: `end_connection` calls `_hand_back` after `_end_connection`; docstring and 04-03-SUMMARY corrected | `test_a_disconnect_hands_the_app_password_back_to_nextcloud` (asserts the delete happened once, cleanup_at cleared) and `test_a_failed_deletion_still_ends_the_connection_and_keeps_the_note` (pitfall 13) |
| HI-01, /connections in the shared `authorize` throttle class, brake lockable from outside | `7ada840` | Yes: `CLASS_CONNECTIONS`, `machine=False`, counter keyed by the signed account, anonymous E8 not counted | `test_the_page_is_throttled_in_a_class_of_its_own`, `test_an_anonymous_flood_closes_neither_the_brake_nor_the_consent_surface`, `test_the_refusals_of_one_account_do_not_lock_out_another` |
| HI-02, unparsable form body escapes as a bare 500 | `ac4015e`, `23df0a1` | Yes: `form_or_none` returns None → generic error page with `no-store`, html, a log reference and no traceback; the four older parse sites hardened the same way | `test_a_form_body_that_cannot_be_parsed_is_a_page_and_never_an_unhandled_500` |

The MEDIUM/LOW findings that were fixed (ME-01, ME-05, LO-01, LO-05, LO-07, LO-08) are in the
commit range and covered by the green suite; the deferred ones (ME-02→BL-08, ME-03→BL-09,
ME-04→BL-10, LO-02/03/06→BL-11, LO-04 doc corrected) are named residuals, carried as AR-04-02
and AR-04-03 above.

### Human Verification Required

One item, and it does not block the goal:

**1. The rendered settings signpost (A1 / AR-04-01)**
- **Test:** On the exapp topology, open Nextcloud, Settings, Security as a normal user.
- **Expected:** A "MCP Connector" entry with title, description and a help icon that links to `{public_url}/connections` is visibly drawn.
- **Why human:** No browser was in the live run. The served form, its presence in the personal Security page's initial state and the DOM mount point are all verified; the drawn pixel is not. The switch and revocation themselves are on /connections and are fully verified, so the worst case here is a missing wayfinding link, not a broken function.

### Gaps Summary

No gaps. All five success criteria hold: SC 1 through SC 4 and the SC 5 round-trip contract,
four of them re-verified from the code and the re-run suite in this session, SC 5 proven
in-process and corroborated by a live run that cannot be reproduced now (AR-04-04). The one
BLOCKER and two HIGH of the security review are closed in the code with guard tests, verified
here against the tree and not against the report.

**Is A1 a blocker? No.** A1 is a browser look at a link-only signpost whose renderer draws
its title, description and icon independent of the empty fields list. The capability the phase
owes, a user controlling their own MCP access with an immediate switch and per-client
revocation, lives entirely on /connections and is verified live and in-process. A1 is worth a
human glance before the store submission, not a hold on this phase.

The four concerns to carry forward: AR-04-01 (the settings pixel, human), AR-04-02 (the switch
guards only /mcp, BL-10), AR-04-03 (two D-57 / anti-forgery defence-in-depth residuals, BL-08 /
BL-09), AR-04-04 (SC 5 live evidence rests on a torn-down topology, as Phase 3 C-01 did).

---

_Verified: 2026-08-17T18:05:00Z_
_Verifier: Claude (gsd-verifier)_
_Method: checkout of `873b381`, 1543 unit/contract tests re-run, all six gates re-run, every BL/HI/ME/LO fix read against the code and the three named blockers/highs run against their guard tests; no live re-deployment (topology torn down)_
