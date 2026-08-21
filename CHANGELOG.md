<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Changelog

All notable changes to this app are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

The Tables app and Talk are now part of what an assistant can reach: the tables of the
account can be looked through and a row can be added to one of them, and conversations can
be read and one message can be sent into one of them.

### Added

- An assistant can look through Tables on three levels: the tables the account may see,
  the columns of one table with their types and limits, and the rows themselves. A row read
  never returns a whole table. It answers with 25 rows unless a larger window is asked for,
  at most 200, and it says how many rows the table really holds, that the answer was cut
  and where the next page starts.

- A row can be added by naming the column titles, not the internal column numbers nobody
  sees in the app. A title the table does not have, a title that exists twice, a missing
  mandatory column and a table the account may read but not write to are all refused before
  anything is written, each with the next step to take. Existing rows are never changed and
  never removed, here as everywhere else in this app.

- An assistant can read the conversations of the account and the history of one of them, and
  that reading leaves no trace in the account: no read marker is moved, no notification is
  acknowledged and the online status stays as it was. The history answers the newest messages
  first, says when it was cut, and offers the way further into the past.

- An assistant can send one message into a conversation. It is addressed only by a token the
  read tool reported, so a made up address never reaches Nextcloud, and a conversation the
  account may not write in is refused before anything is sent. A sent message is never edited
  and never removed, and a message that mentions everybody at once is not sent at all.

- An administrator can switch the sending of Talk messages off for the whole instance, in the
  settings of this app, whatever an account is allowed to do in Talk itself. Reading
  conversations and their history is not affected by that switch.

### Fixed

- Asking for something that does not exist now says so. When Nextcloud answers such a
  request with a bare error page instead of a message, the assistant used to be told that
  its app password might be wrong, which sent it looking in the wrong place. It is now told
  that the id is unknown to this instance, so it can search for the right one.

## [0.1.3] - 2026-08-21

This release adds a second way for an assistant to identify itself: by a metadata
document it publishes, instead of registering with this app first. That is the way the
current specification prefers, it is the way Claude Code connects, and an administrator
can switch it off. Next to it, a locally running assistant may now come back on the
port it actually got, which is the other half of what kept Claude Code out, and the
page a refused desktop app lands on now names the way that works for it.

### Fixed

- The version this app names in the MCP handshake is now the version that is installed.
  It was a fixed string that stayed at the first release, so a connected assistant was
  told 0.1.0 whatever version answered. The handshake now derives it from the package
  version, the single string every release raises.

- The switch for the way an app identifies itself by its own published document can now be
  set in the administration settings of this app, next to the switch for self registration.
  It was only ever a deploy variable, and an installation from the app store never receives
  one, so on exactly that kind of installation the switch could not be reached at all. Both
  switch descriptions now say what they do to each other: with self registration off, both
  ways are closed whatever the second switch says, while switching the second one off leaves
  self registration exactly as it is.

### Changed

- The page a user sees when an assistant app asks to be returned to an address it did not
  register now names the way in that works for such apps: an app password from the Nextcloud
  security settings. Nothing is shared in that case, as before, and the page still says
  nothing about which check refused the request or which address was asked for. This closes
  what was left open for apps of that shape: the sign in stays refused, and the reader is no
  longer left with a refusal and no way forward. The documentation for Cursor and the OAuth
  setup carries the same way out and the reason behind it.

- The documentation now says what a real Claude Code does with this server, because it was
  measured against Claude Code 2.1.233: it connects without registering, by publishing its
  own metadata document, and it calls tools with the account that signed in. The port it
  comes back on was measured too, over four runs, and it was a different one every time,
  which is why this app no longer compares that port. What is not new: an administrator who
  switches client registration off closes this way with it, and an administrator who keeps a
  list of allowed clients keeps it for this way as well. Both were measured on a running
  instance, and with registration off the app makes no outbound request at all.

- The documentation now says what a real Cursor does with this server, because it was
  measured against Cursor 3.2.16: the registration goes through since 0.1.2, and the sign
  in is still refused, because Cursor asks to be returned to its `cursor://` address, which
  this app does not register. Nothing is shared in that case and no password page is shown.
  Cursor users are pointed at the app password path, and the earlier reading that a client
  of this shape is no longer kept out is corrected to what it really is: the attempt now
  fails at the sign in instead of at the registration.

- The documentation now says what Nextcloud 34.0.3 really does with an external app,
  because it was measured there: the apps management lists it with its deploy daemon, its
  install button reads "Deploy and enable", and "Remove" appears in the row actions once
  the app is disabled. On 34.0.2 and earlier the apps management lists no external app at
  all, and the occ commands stay the path that works on every version. No promise of a one
  click install without the version it was measured on.
- A locally running assistant may now come back on the port it actually got. A native
  client publishes a return address without a port and takes whatever free port the
  operating system hands it at the moment of the request, and the app used to refuse
  that as a mismatch. Scheme, host, path and query are still compared exactly and only
  loopback addresses are affected, so `localhost` still does not stand in for
  `127.0.0.1` and a hosted connector gains no freedom at all. This is what kept Claude
  Code out.

### Added

- An assistant can now connect by publishing its own metadata document instead of
  registering with this app first. The address of that document is the name the client
  goes by, the app reads it once and keeps the answer for as long as the answer asks for
  and at least five minutes. It reads the document again when that window is over, and it
  does so while a connection is being made and at no other moment: a running connection,
  a token exchange and every single tool call use the information as it was read, so an
  app you connected keeps working while the site that publishes its document is
  unreachable, and nothing your assistant does can make this app wait on that site. The
  other side of that trade, said plainly: a document that was withdrawn or changed does
  not reach a connection that already exists. Ending access is a disconnect on the
  connections page of this app, or an administrator who removes the app, and both take
  effect on the very next request. Everything that holds for a registration holds here
  too: only `https` return addresses and loopback ones, an inadmissible address is dropped
  and the rest kept, the client list of an administrator decides in exactly the same
  place, and a client of this kind never holds a shared secret. The app reads such a document from public addresses only, never
  from an address inside a network, never more than five kilobytes of it, never longer than
  five seconds, never after a redirect and never an image out of it, and a failed read is
  not remembered. This is the way the current specification prefers, and it is the way
  Claude Code identifies itself.
- The approval page now names the host of the address a client goes by, and it carries a
  second warning when the app can only be reached on the computer you are using. The
  reason for the warning is worth reading once: an address of that kind says who publishes
  the information about an app, and it does not say which program on your own computer
  answers on that port. So the page says both of those things, and it does not claim that
  anybody confirmed the app.
- A new administrator switch, `NC_MCP_OAUTH_CIMD`, for the way a client identifies
  itself by the address of its own published metadata document instead of registering.
  It is on unless it is switched off, and switching off client registration switches
  this off with it: a closed door cannot be walked around through the other spelling.
- A runbook for showing this app to other people, `docs/conference-demo.md`: the one time
  setup, four stations with every command to copy and what has to be visible at each of
  them, a checklist for the ten minutes before, the things it deliberately does not show,
  and a recovery table. It was walked once end to end and it carries the measured time of
  every step, including the two answers a paused and a disconnected account really get.
  Next to it, `docs/conference-talk.md`, a five minute talk draft whose every claim names
  the measurement it comes from.

## [0.1.2] - 2026-08-20

A maintenance release with no new feature. It opens the app to clients that register a
return address of their own scheme, which is what kept Cursor out, and it tightens four
places where the app trusted what a request said about itself instead of what it sent.

### Changed

- A client that registers several return addresses at once is no longer refused
  because one of them is inadmissible. The inadmissible entries are dropped and the
  registration keeps the allowed ones, and the answer names the addresses that were
  actually registered. This is what kept Cursor out: it registers a `cursor://` scheme
  next to two acceptable addresses. The rule itself is unchanged, `https` on any host
  and `http` on loopback only, a dropped address is never a redirect target, and a
  registration whose every address is inadmissible is still refused.
- An excerpt of a document now reads only what it keeps. The bundling tool keeps two
  kilobytes per hit and used to fetch up to 512 kilobytes to do it, so one call with
  three excerpts could move one and a half megabytes through the instance. The answer
  is the same one as before, the transfer behind it is a fraction of it.
- A pause that has nothing behind it is cleaned up after 90 days. The switch a user
  sets for their own account was stored forever, also for accounts that no longer
  exist, and on setups that reuse account names a new account could inherit the pause
  of an old one and start switched off without anybody having done that. A pause with
  a connection behind it is untouched, whatever its age.
- The app's database does less work per request. The table setup ran on every single
  open of the file, including the account switch check that sits on every request of a
  connected assistant, and it now runs when a process opens the file for the first
  time. A store file that is removed while the app runs is still recreated.
- The public address is stored in one spelling. An address typed with capital letters
  in the administration settings became the name this app publishes about itself, and a
  client that was given the same address in lower case failed a comparison nothing
  explained. The scheme and the host name are levelled now, which changes nothing about
  the address itself; a path is left exactly as it was typed, because there capital
  letters do mean something.
- The administration form of a fresh installation links to the documentation instead of
  to a page that cannot exist. Before an address is set, the app does not know where it
  can be reached, and the link of the form pointed at the administrator's own machine.
- The log line an administrator gets when no usable public address is set now says
  which of the two cases it is: none is stored, or one is stored and was refused. The
  line that reports a refused address names both places it can be corrected, the deploy
  variable and the form, and which of the two wins. Neither line ever contains the
  address itself.

### Fixed

- A paused account no longer sees a consent screen it cannot use. If the access switch
  was pulled in another tab while a consent screen stood open, a reload still showed
  approve and deny. Nothing could be granted, the click was already refused, but the
  page said the opposite of the switch. It now shows the same note as everywhere else.

### Security

- The uninstall command reads only as much of a request as it is willing to read. Its
  size limit trusted the length a request announced, and a request that announces none
  was read into memory whole. The path is an internal one and needs the app's own
  credentials, so nothing was reachable from outside; the limit now counts what actually
  arrives, and the command behaves exactly as before.
- The connections page has the same limit on the same terms. Its size check also read the
  length a request announced, so a submission that announced none was read whole and
  carried out, although the page says it refuses a body larger than its four short fields
  unread. The check now counts what arrives, both places share one implementation, and an
  ordinary submission is answered exactly as before.
- The hidden value that protects the consent screen and the connections page against
  forged form submissions now expires. It used to be the same value for an account for
  the whole lifetime of the installation, and the only way to change it would have been
  to replace the data key, which makes every stored connection unreadable. It is bound
  to a one hour window now, and the previous window is accepted as well, so a page that
  was open across a full hour still submits. A page older than that is refused the way a
  forged one is: it shows itself again, and the action has to be repeated.
- A document can no longer imitate the note this app writes into a text. When a file is
  too large to be read at once, or when a document is shortened to a short excerpt, the
  answer says so in the text itself, so an assistant that reads only the text can tell a
  whole document from the beginning of one. A document that contained that exact
  sentence could pretend the excerpt of the server ended there and that what followed
  was a message of the system, or claim to be complete where it was cut. The sentence is
  now removed from the content of a document before the app writes its own, so it can
  only come from the app. What an assistant receives is otherwise unchanged.

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

[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/street1983nk/nextcloud-mcp-connector/releases/tag/v0.1.0
