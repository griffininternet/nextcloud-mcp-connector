<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Changelog

All notable changes to this app are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- A client that registers several return addresses at once is no longer refused
  because one of them is inadmissible. The inadmissible entries are dropped and the
  registration keeps the allowed ones, and the answer names the addresses that were
  actually registered. This is what kept Cursor out: it registers a `cursor://` scheme
  next to two acceptable addresses. The rule itself is unchanged, `https` on any host
  and `http` on loopback only, a dropped address is never a redirect target, and a
  registration whose every address is inadmissible is still refused.

## [0.1.1] - 2026-08-19

A maintenance release that makes the listed version installable with one click, and
removable without a leftover. Everything the store listed as 0.1.0 needed an
environment variable an administrator had no place to set.

### Added

- Administrator settings in Nextcloud for the public address of this app and for the
  three OAuth switches (client self registration, allowlist only, allowed clients).
  Administration settings, Security, MCP Connector, no environment variable and no
  shell.
- A new administrator command `occ mcp_connector:purge --force` ends every MCP
  connection of the instance: it hands every Nextcloud app password this app created
  back to Nextcloud, empties its database and deletes its data key. Run it before
  removing the app, see [docs/uninstall.md](docs/uninstall.md).
- Setup guides for Open WebUI and MUCGPT, in
  [docs/client-setup.md](docs/client-setup.md).
- Frequently asked questions, including how a user switches the app off for their own
  account and how an administrator removes it together with its data, in
  [docs/faq.md](docs/faq.md).

### Changed

- An installation whose public address is not set yet now starts and reports its setup
  state instead of stopping with an error. Before this release, a one click install
  from the store ended in a container that restarted forever, because that address can
  only be set after the install.
- The per account switch now also prevents new connections from being created. Before,
  it stopped requests of existing connections but a paused account could still connect
  another assistant.
- The store description now answers, in all three languages, the one question users
  ask: whether they can switch the app off for themselves without their administrator.
- The tool count in the readme is now correct: 16 tools, not 15, and a contract test
  reads it from the live tool registry instead of trusting the text.

### Fixed

- The `--force` option of the purge command is now accepted by the command wrapper, so
  the command can actually be run.
- Deleting the data key now passes its key name in the shape AppAPI expects, so a purge
  leaves no key behind.

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

[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/street1983nk/nextcloud-mcp-connector/releases/tag/v0.1.0
