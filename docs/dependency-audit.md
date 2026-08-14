<!--
SPDX-FileCopyrightText: 2026 street1983nk
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Dependency audit

**Audited:** 2026-08-14 (slopcheck 0.6.1 against PyPI)
**Scope:** all direct dependencies of `nextcloud-mcp-connector` plus the notable transitive ones.
**Owner sign-off:** the package legitimacy gate for the first `uv sync` was approved by the
repository owner on 2026-08-14 after independent verification (see "The httpx2 finding").

## Audit table

| Package | Registry | Age | Downloads | Source repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| mcp | PyPI | 2.0.0 since 2026-07-28, project since 2024 | very high | github.com/modelcontextprotocol/python-sdk | [OK] | Approved (direct) |
| mcp-types | PyPI | 2.0.0, lock-step with mcp | via mcp | github.com/modelcontextprotocol/python-sdk | [OK] | Approved (transitive, never pinned directly) |
| httpx | PyPI | 0.28.1 since 2024-12-06 | very high | github.com/encode/httpx | [OK] | Approved (direct) |
| httpx2 | PyPI | first release 2026-05-11, 2.10.0 on 2026-08-09 | new | github.com/pydantic/httpx2 | [SUS] | Keep transitive, never a direct dependency |
| lxml | PyPI | 6.1.1 since 2026-05-18 | very high | github.com/lxml/lxml | [OK] | Approved (direct) |
| icalendar | PyPI | 7.2.2 since 2026-07-20 | high | github.com/collective/icalendar | [OK] | Approved (direct) |
| vobject | PyPI | 0.9.9 since 2024-12-16 | high | github.com/py-vobject/vobject | [OK] | Approved (direct) |
| pydantic | PyPI | 2.13.4 since 2026-05-06 | very high | github.com/pydantic/pydantic | [OK] | Approved (direct) |
| respx | PyPI | 0.23.1 since 2026-04-08 | high | github.com/lundberg/respx | [OK] | Approved (dev) |
| pytest | PyPI | 9.1.1 | very high | github.com/pytest-dev/pytest | [OK] | Approved (dev) |
| anyio | PyPI | 4.14.2 | very high | github.com/agronholm/anyio | [OK] | Approved (transitive, also the async test plugin) |
| ruff | PyPI | 0.16.3 | very high | github.com/astral-sh/ruff | [OK] | Approved (dev) |

Packages removed due to a `[SLOP]` verdict: none.
Packages flagged as suspicious: `httpx2`.

## The httpx2 finding

slopcheck flags `httpx2` with "Suspiciously close to 'httpx'. Could be a typosquat." That signal is
expected for this name. Counter-evidence, verified directly against PyPI and GitHub:

- `mcp` 2.0.0 `requires_dist` contains `httpx2>=2.5.0`, so the dependency is genuinely pulled in by
  the official MCP SDK, not by our own code.
- `httpx2` is published with `author_email: Tom Christie <tom@tomchristie.com>` (the author of
  `httpx`), maintainer `Pydantic Services Inc. <engineering@pydantic.dev>`, homepage and source
  `github.com/pydantic/httpx2` (the real pydantic organisation, 914 stars, not a fork, first
  release 2026-05-11), classifier `Development Status :: 5 - Production/Stable`.
- The official SDK release notes for v2.0.0b2 name the switch explicitly: "httpx is replaced by
  httpx2 (#2972) ... the next-generation httpx fork with SSE support built in".
- `encode/httpx` has been inactive since March 2026, which makes the successor story consistent.

**Consequence for this repository:** `httpx2` is legitimate but young. It stays a transitive
dependency of `mcp` and is never listed in `pyproject.toml`. Our own HTTP code uses `httpx`
(`>=0.28,<0.29`), because `respx` mocks `httpx` and not `httpx2`.

Secondary observation, no action needed in phase 1: `httpx2` verifies TLS against the operating
system trust store (via `truststore`) instead of `certifi`. That becomes relevant only when an
integration test talks to a self-signed Nextcloud certificate; the Docker test setup uses plain
HTTP.

## Resolved tree (`uv tree --depth 2`, 2026-08-14)

```
nextcloud-mcp-connector v0.1.0
├── httpx v0.28.1
│   ├── anyio v4.14.2
│   ├── certifi v2026.7.22
│   ├── httpcore v1.0.9
│   └── idna v3.18
├── icalendar v7.2.2
│   ├── python-dateutil v2.9.0.post0
│   └── tzdata v2026.3
├── lxml v6.1.1
├── mcp[cli] v2.0.0
│   ├── anyio v4.14.2
│   ├── httpx2 v2.10.0
│   ├── jsonschema v4.26.0
│   ├── mcp-types v2.0.0
│   ├── opentelemetry-api v1.44.0
│   ├── pydantic v2.13.4
│   ├── pyjwt[crypto] v2.13.0
│   ├── python-multipart v0.0.32
│   ├── pywin32 v312
│   ├── sse-starlette v3.4.8
│   ├── starlette v1.6.0
│   ├── typing-extensions v4.16.0
│   ├── typing-inspection v0.4.4
│   ├── uvicorn v0.52.3
│   ├── python-dotenv v1.2.2 (extra: cli)
│   └── typer v0.27.1 (extra: cli)
├── pydantic v2.13.4
│   ├── annotated-types v0.8.0
│   ├── pydantic-core v2.46.4
│   ├── typing-extensions v4.16.0
│   └── typing-inspection v0.4.4
├── vobject v0.9.9
│   ├── python-dateutil v2.9.0.post0
│   ├── pytz v2026.3.post1
│   └── six v1.17.0
├── pytest v9.1.1 (group: dev)
│   ├── colorama v0.4.6
│   ├── iniconfig v2.3.0
│   ├── packaging v26.3
│   ├── pluggy v1.6.0
│   └── pygments v2.20.0
├── respx v0.23.1 (group: dev)
│   └── httpx v0.28.1 (*)
└── ruff v0.16.3 (group: dev)
(*) Package tree already displayed
```

**Finding:** `httpx2 v2.10.0` appears exclusively as a child of `mcp[cli] v2.0.0`. It is not a
top-level entry, which is the machine-checkable form of the policy above. The unit test
`tests/unit/test_project_layout.py` asserts that no direct dependency starts with `httpx2`.

## Supply chain controls in force

- `uv.lock` is committed; CI installs with `uv sync --frozen` (no silent resolution drift).
- The SDK pin is `mcp[cli]>=2.0,<3`. Documented fallback pin if v2 turns out to be a blocker:
  `mcp>=1.29,<2` (1.x is in maintenance mode, security fixes only).
- No `npx --yes` and no auto-substitution of packages: a failing install is a human checkpoint,
  never a "try a similar name" retry.
- Re-run the audit whenever a direct dependency is added or a major version bumps.
