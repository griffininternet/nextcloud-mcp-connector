<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Privacy and data flow

**Scope:** what personal data this app stores, where it stores it, what it never
does, and the one data flow an operator has to account for before switching it on.
This is a technical description for administrators and data protection officers,
not a legal privacy statement for end users. The instance operator remains the
data controller and has to provide that statement themselves.

## The short version

This connector runs inside your own Nextcloud deployment. It sends no telemetry,
phones no home, and calls no third party of its own. Every tool call runs under
the identity of the signed in user, so an assistant never sees more than that user
sees in the web interface.

The one flow that leaves your control is the assistant itself: when a user connects
a hosted AI client such as Claude.ai or ChatGPT, the content the assistant reads
from Nextcloud is transmitted to that client's provider. The connector does not
send it on its own, but it is the door through which it leaves. See
[What leaves your control](#what-leaves-your-control).

## What the app stores

The app keeps one SQLite database inside its own container, for the OAuth 2.1 and
credential state it needs to answer a request without a fresh sign in every time.
It holds these personal data:

| Data | Where | Form |
|------|-------|------|
| Nextcloud user id | `authorizations.nc_user`, `user_access.nc_user` | plain, it is the account name the request runs as |
| Nextcloud app password | `authorizations.app_password_enc` | encrypted at rest, AES-GCM with a fresh nonce per record, bound to its authorization id as additional authenticated data |
| OAuth authorization codes, refresh and access tokens | `auth_codes`, `refresh_tokens`, `access_tokens` | stored only as a hash, never in the clear |
| Client registrations | `clients` | the assistant apps, their redirect targets and issued secrets |
| Access switch state | `user_access` | one row per paused account, a timestamp |
| Timestamps | across the tables | created, revoked, cleanup and expiry times |

The app does not store the content of your files, calendar, notes, deck cards or
contacts. It reads them per request, under the user's identity, and returns them in
the tool answer. Nothing of that content is written to the database.

The encryption key lives outside the database, in the app's environment, so a copy
of the database file alone does not reveal any app password.

## What the app never does

- No telemetry, no analytics, no usage tracking, no error reporting to a third party.
- No outbound request except to your own Nextcloud instance.
- No call to any AI provider, model host or external service from the connector
  itself. The assistant, not this app, talks to the model.
- No access beyond the signed in user's own permissions. A restricted user sees
  through the connector exactly what the web interface shows them, and no more.

## What leaves your control

The purpose of the connector is to let an AI assistant read from Nextcloud. Once a
user connects a hosted assistant, the data that assistant reads is transmitted to
the assistant's provider:

- Search results, file listings, calendar entries, notes, deck cards and contacts
  the assistant requests.
- With `prepare_context`, short excerpts of the top matching files, so the model
  has content and not only titles.

For hosted assistants such as Claude.ai or ChatGPT this is a transfer to a third
party, in most cases outside the EU. The connector transmits nothing on its own,
but an operator has to account for this flow:

- Have a legal basis for the transfer to the assistant's provider, for example a
  data processing agreement, and where applicable a transfer impact assessment for
  the third country.
- Tell your users that the content their assistant reads leaves Nextcloud for the
  assistant they chose, and let them decide which assistant to connect.
- A self hosted or EU based model (for example an assistant that speaks to a local
  or European LLM) keeps this flow inside your own control and is the way to avoid
  the third country transfer entirely.

## Deletion and user control

- A user pauses or resumes their own access, and disconnects any connected
  assistant, on the connector's own `/connections` page. Disconnecting hands the
  app password back to Nextcloud, so the entry also disappears from the user's
  Devices and sessions in Nextcloud.
- A user can revoke access from the Nextcloud side at any time, under Settings,
  Security, Devices and sessions.
- Uninstalling the app removes its container and its database, and with it every
  token and encrypted app password it held.

## Retention

Tokens and codes carry their own expiry and are swept after it. A revoked or ended
authorization returns its app password to Nextcloud and is cleared. There is no
long lived store of personal data beyond the active connections a user has chosen
to keep.
