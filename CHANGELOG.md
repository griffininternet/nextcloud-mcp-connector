<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Changelog

All notable changes to this app are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-17

First release, submitted to the Nextcloud App Store.

### Added

- MCP server for Nextcloud, deployed as an AppAPI External App behind HaRP.
- A curated, read first set of tools for files, calendar, notes, deck and
  contacts, plus `prepare_context`, which bundles a search and the coming week
  into a single call.
- OAuth 2.1 sign in, so a hosted assistant such as Claude.ai or ChatGPT connects
  through a Nextcloud browser sign in instead of a pasted app password. Dynamic
  client registration, PKCE, and an administrator allowlist for clients.
- App password sign in for clients that cannot do OAuth.
- A per account switch and a connections page: every user pauses or resumes their
  own access and disconnects any connected assistant, on the app's own
  `/connections` page.
- Every request runs under the identity of the signed in user, so an assistant
  never sees more than that user sees in the web interface.
- A privacy and data flow description, see [docs/privacy.md](docs/privacy.md).

[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/street1983nk/nextcloud-mcp-connector/releases/tag/v0.1.0
