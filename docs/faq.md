<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Frequently asked questions

**Scope:** the questions users and administrators ask about this app once it is
installed, answered with what the code actually does. Every answer names the
document that carries the detail, so nothing is stated twice in two places and no
answer can quietly drift away from the one that is authoritative.

The canonical answers live here, in English. The three READMEs carry a short form
of the first question with a link back to this file, and the app store description
carries the same answer in English, German and French, because the store text is
the only place a user sees without visiting the repository.

## For users

### My administrator installed this app. Can I switch it off for myself?

Yes. You do not need your administrator for that, and you do not have to wait for
anything to be turned off before it stops doing something, because it does nothing
until you connect an assistant.

**It only ever acts on a request.** There is no background job, no cron, no
scheduled task, no indexing and no telemetry. The connector never fetches your
files, calendar entries, notes, deck cards or contacts on its own initiative. It
reads them when a connected assistant asks a question, under your own identity, and
returns the answer. Without a connected assistant that sends a request, nothing
happens at all. See [privacy.md](privacy.md), section "What the app never does".

**There is a switch for your own account.** The connector's own connections page
carries it, and Nextcloud links that page under Settings, Security, MCP Connector.
Pausing takes effect on the next call: a connected app is refused, and nothing is
disconnected, so resuming brings your connections back as they were. The same
switch also closes the door where a new connection would be created: an account
that has paused its access cannot complete a new authorization either, it is shown
the page that explains the switch instead, and no usable credential is left behind.

**Every connection can be ended on its own.** The same page lists the assistant
apps connected to your account and disconnects any single one of them. Disconnecting
hands the Nextcloud app password of that connection back to Nextcloud, so the entry
also disappears from your Devices and sessions in Nextcloud, under Settings,
Security. You can revoke it from that side as well.

**Where this app's control ends.** What an assistant does with the content after a
tool call is decided by the provider of that assistant, not by this app. If you
connect a hosted assistant such as Claude.ai or ChatGPT, the content it reads from
your Nextcloud is transmitted to that provider. The connector transmits nothing on
its own, but it is the door through which it leaves, so choose your assistant
accordingly. [privacy.md](privacy.md), section "What leaves your control", spells
out the flow and what an operator has to account for.

**And where the administrator's part begins.** Removing the app is their step, not
yours, and on Nextcloud 34 the Remove button in the app list disables the app and
stops its container without deleting its data. Emptying the instance is an explicit
act with its own order of commands, which the administration runbook
[uninstall.md](uninstall.md) spells out, and
[privacy.md](privacy.md), section "Deletion and user control", summarises. Your own
switch and your own disconnect do not depend on any of that: they act immediately
and they are yours.

## For administrators

### Does the app need any configuration before a user can connect?

Yes, one value: the public address this app is reachable under,
`NC_MCP_PUBLIC_URL`. The authorization server calls itself by it, so without it no
client can complete a connection. What to set, where, and the measurements behind
it: [oauth-setup.md](oauth-setup.md).

### A user says the app is switched off for them and nobody switched it off. Why?

Almost certainly a reused account id. The pause is stored under the account name, in
the app's own database and with no link to the Nextcloud user table, because the
switch has to survive an account that this app has never seen. On a directory setup
(LDAP, SAML, a provisioning script) an account can be deleted and a new one created
with the same id later, and the new account then inherits the pause of the old one:
its first tool call is refused with the sentence about the switch, and no
administrator ever touched it.

**The fix takes one click and belongs to the user.** They open Settings, Security,
MCP Connector, and resume their access on the connections page. Nothing else is
affected, no connection is lost, and the row disappears with the click.

**What the app does on its own.** A pause that has no connection behind it at all is
removed 90 days after it was set, together with the other rows that have run out.
That closes the case above without touching anybody who is actually paused: as long
as an account has one connection, its switch stays whatever its age. The one price of
the window is the opposite case, a user who pauses their access without ever
connecting an assistant: after 90 days that pause is forgotten, and the account counts
as switched on again. Nothing becomes readable through it, because a connection has to
be authorized in the browser before anything can be read at all.

### How do I remove the app and its data completely?

Two commands, in this order: `occ mcp_connector:purge --force` first, which hands
every Nextcloud app password this app created back to Nextcloud, empties every table
of its database and deletes its encryption key, then
`occ app_api:app:unregister mcp_connector --rm-data`, which removes the app together
with its data volume. The second must not run first, because it deletes the only
record of which app password belongs to which connection. The runbook with the
verification steps is [uninstall.md](uninstall.md).
