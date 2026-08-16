---
phase: 03-oauth-2-1
plan: 09
subsystem: auth
tags: [oauth2.1, e2e, staging, claude, chatgpt, cursor, discovery, dcr, auth-04, docs]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-01: the three discovery documents and the 401 with its pointer"
  - phase: 03-oauth-2-1
    provides: "03-05 and 03-06: the authorization server, dynamic client registration and the consent screen"
  - phase: 03-oauth-2-1
    provides: "03-08: the flow proven through the full chain, docs/oauth-setup.md and the two proxy rules"
provides:
  - "compose.staging.yml, deploy/Caddyfile.staging, scripts/setup_staging.sh, scripts/staging_dns.sh: a public instance that can be built and torn down from scratch"
  - "docs/staging-setup.md: the owner runbook for it"
  - "docs/oauth-setup.md, section 'End to end with hosted connectors': the measured runs of Claude.ai, ChatGPT and Cursor"
  - "docs/client-setup.md: per client walkthroughs with the traps of the real run"
  - "the measured answer to A1 (ChatGPT redirect URI), A2 (are the proxy rules required) and A3 (response times)"
  - "AUTH-04, closed with evidence"
affects: [04 admin ui, 05 store submission]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a claim about a foreign client is only worth what its access log says"
    - "a counter measurement has to prove that the thing it switched off is really off"
    - "what a client refuses to tell us is measured with a throwaway server that records the request"

key-files:
  created:
    - compose.staging.yml
    - deploy/Caddyfile.staging
    - scripts/setup_staging.sh
    - scripts/staging_dns.sh
    - docs/staging-setup.md
    - .planning/phases/03-oauth-2-1/03-09-MEASUREMENTS.md
  modified:
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/registry.py
    - docs/oauth-setup.md
    - docs/client-setup.md
    - .planning/BACKLOG.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "A registration is granted every scope the metadata advertises: the server refused ChatGPT with invalid_scope for asking for offline_access, which our own metadata advertises, and that was our defect and not the client's"
  - "The two reverse proxy rules stay optional, now measured: with both switched off Claude.ai falls back to the path below the issuer and connects"
  - "AUTH-04 is closed on two connected clients; Cursor was measured on top and its refusal is a backlog item, not a gap in AUTH-04"
  - "The refusal of a private-use URI scheme stays as it is, because no application owns a scheme exclusively on a desktop; what changes is that the price is now written down"

patterns-established:
  - "Every foreign client run is recorded raw in a MEASUREMENTS file first, and the documentation is written from it afterwards"
  - "A bind mounted single file is verified inside the container after an edit, because sed replaces the inode and the container keeps the old one"

requirements-completed: [AUTH-04]

# Metrics
duration: one working day, spread over the staging build and three client runs
completed: 2026-08-16
---

# Phase 3 Plan 09: The hosted connectors against a public instance Summary

**Claude.ai and ChatGPT both connect to a public Nextcloud with nothing but the resource URL, which closes AUTH-04, and getting there found one real defect of ours, corrected one assumption of the research, corrected one reading of our own measurement, and turned the deferred BL-04 question into a different question than the one that was written down.**

## Performance

- **Completed:** 2026-08-16
- **Tasks:** 3 of 3
- **Clients measured:** 3 (Claude.ai, ChatGPT, Cursor)

## Accomplishments

- **A public instance that exists on purpose and can be removed the same way.** `compose.staging.yml`, `deploy/Caddyfile.staging`, `scripts/setup_staging.sh` and `scripts/staging_dns.sh` build the whole topology on a throwaway VPS with a real certificate, and `docs/staging-setup.md` is the runbook. From the outside only 22, 80 and 443 answer. Guard tests cover the properties that make it safe to publish.
- **Claude.ai: connected, plug and play.** One connector, the URL alone, both OAuth fields empty. 15 tools, grouped by the client into 11 read only and 4 write, all set to ask for approval. `POST /token` in 23 ms, `POST /register` in 8 ms, `GET /authorize` in 143 ms. The connection shows up in Nextcloud under "MCP Connector: Claude" and can be ended there.
- **ChatGPT: connected, after we fixed our own server.** The first run was refused by us with `invalid_scope`, because our metadata advertises `offline_access` while our registration granted only `nextcloud`. A client that believes the published metadata was turned away by the server that published it. Fixed in `5793fc3`, `eb5b6b9` and `8724d57`, redeployed, and the same connector connected on a second attempt without being recreated. `POST /token` in 37 ms.
- **Assumption A1 replaced by a measurement.** The ChatGPT redirect URI is not the static value the research had taken from community sources. It is minted per connector, `https://chatgpt.com/connector/oauth/<token>`. Consequence for the allowlist mode: that address cannot be listed in advance, it has to be read out of the first refused attempt. Claude.ai keeps one fixed address and can be listed up front.
- **Assumption A2 answered, and the first answer was wrong.** The counter measurement was run twice. The first attempt reported that the canonical root paths answer 200 even with the rewrite rules removed, which would have been a sensational finding; it was an artifact. `deploy/Caddyfile.staging` is bind mounted as a single file, `sed -i` writes a new inode, the container kept reading the old file, and `caddy reload` dutifully reloaded the unchanged configuration. With the edit really in place the canonical paths answer 404, and the real question could be asked: a Claude.ai connection was forced from nothing, and **it connected anyway**. Claude.ai tries three locations for the authorization server metadata and settles on the OIDC style path below the issuer, which needs no rule at all. So the rules are a courtesy for clients that give up earlier, exactly as `deploy/Caddyfile` and `docs/spike-discovery.md` say.
- **Assumption A3 answered with numbers.** No response of this server came close to a time budget: registration 7 to 9 ms, token exchange 21 to 37 ms, the authorization redirect 94 to 191 ms, all measured through Caddy, HaRP and the container from the public internet.
- **BL-04 turned out to be about something else.** Cursor 3.2.16 was added the plain way, by writing `~/.cursor/mcp.json`, and it refuses to connect. Its own log carries our sentence verbatim. The cause is not the loopback address that BL-04 anticipated: a registration with `http://127.0.0.1:49731/callback` alone is accepted. Cursor registers three return addresses at once, one of which is the private-use scheme `cursor://anysphere.cursor-mcp/oauth/callback`, and our check reads the whole field, so one inadmissible entry sinks a registration that also carries two admissible ones. Measured three ways: Cursor's real payload refused, the same payload without the scheme accepted, loopback alone accepted. The payload itself had to be measured with a throwaway recording server, because this server deliberately never echoes a refused address.
- **A finding nobody asked for: removing a connector does not revoke it.** The Claude.ai connector was removed in the UI and added again with the same URL. The first request afterwards was a tool call answering 200: no 401, no discovery, no registration, and the entry even kept its old id. The stored authorization had survived on the provider side. This is now stated in both documents, because a user who removes a connector in the client believes they revoked something.

## Task Commits

1. **Task 1: the staging instance and its runbook** - `3728c4a`, `8ea0ce0`, `829f8eb`, `bda243b`, `b69e176`, `162d6f0`
2. **Task 2: the two connector runs, including the scope fix they forced** - `5793fc3`, `eb5b6b9`, `8724d57`, `6e6e8a2`, `dafd944`
3. **Task 3: evaluation, documentation, backlog, AUTH-04** - `9215501`, `39d766b`, `d7505d4`

## Files Created/Modified

- `.planning/phases/03-oauth-2-1/03-09-MEASUREMENTS.md` - the raw record of all four runs, kept so the numbers stay attributable.
- `docs/oauth-setup.md` - the new section "End to end with hosted connectors" with a table per client, the request chains, the counter measurement, the Cursor refusal and the note on revocation; section 3 of the install part now cites the measurement instead of leaving the question open.
- `docs/client-setup.md` - a walkthrough per client with the traps of the real run: where the button is, why an organisation account does not have one, that removing is not revoking, the ChatGPT developer mode, and why Cursor cannot connect.
- `.planning/BACKLOG.md` - BL-04 rewritten around what was measured, BL-05 added for client id metadata documents.
- `.planning/REQUIREMENTS.md` - AUTH-04 checked off with its evidence.

## Deviations From Plan

- The plan expected the counter measurement to possibly need a correction of `deploy/Caddyfile`. It did not: the measurement confirmed the wording that was already there. What needed correcting was the note in `03-09-MEASUREMENTS.md` from the first run, which had called the rules required.
- Cursor was not in the plan as a task, only as an open point. It was measured because the staging instance was the cheap moment for it, and the result changed a backlog entry.

## What the next phase inherits

- **Open from BL-04:** whether a client that picks a new loopback port per run breaks against exact matching. Cursor uses a fixed port, so this run says nothing about it.
- **Open from BL-05:** client id metadata documents, which the specification names as the successor of dynamic client registration.
- **Teardown:** the staging machine and its DNS record are to be removed by the owner now that the proof is recorded, per the instruction of 2026-08-16.
