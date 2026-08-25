<!--
Prepared GitHub issue body for street1983nk/nextcloud-mcp-connector.

Target repo:   street1983nk/nextcloud-mcp-connector
Title:         Enterprise features: what would your org need before allowing MCP access?
Kind:          fake door, question only, no implementation behind it
Go criterion:  at least five qualified organisation signals, each from an organisation with
               more than 100 users, within six weeks of publication; or one anchor customer
               asking for a pilot. Anything short of that is a no-go and the add-on stays
               unbuilt.
Not published. Publishing this issue is an owner decision (D-07).

Everything below this comment is the issue body as it will be rendered on GitHub.
-->

## Why this issue exists

This app is installable today, and it reads a Nextcloud under the identity of the signed in
user. That answers the question whether an outside assistant can reach a Nextcloud safely at
all. It does not answer the question an IT lead has to answer instead: what does this
organisation need in place before it allows that access.

The README now names three things as planned, and none of the three exists in the app today,
in no version and behind no setting:

- **An audit log**: one structured event per tool call, naming the account, the client, the
  tool, the resource it touched and how the call ended, with a retention an administrator
  sets and an export that leaves the app.
- **Group policies**: which tools a group may call at all, read scopes narrowed to a folder,
  an allow list of clients, and a switch that closes access for one account or for everyone.
- **SSO**: sign in through the identity provider the organisation already runs, in front of
  the OAuth sign in of this app, with a central inventory of the tokens that were handed out.

## What would help

If you have looked at this app for an organisation rather than for yourself, the useful
answer is short:

1. Which of the three is the one that blocks a rollout, and which of the three you could do
   without for a while.
2. Roughly how many accounts would use it, and whether the decision sits with you, with a
   security officer or with a data protection officer.
3. What a report would have to show on the day somebody asks what the assistant has seen.
4. Whether an outside assistant is allowed in your organisation at all today, and if it is
   not, what the stated reason is.

One line per question is worth more than a wishlist. If the answer is that your organisation
would forbid this kind of access whatever gets built, that is a useful answer too, and it is
the one that keeps this from being built.

## What this issue is not

It is not an announcement. Nothing here is implemented, there is no branch behind it, and no
sentence in it promises a version or a day. If none of this is about you and you self host
for yourself, the app you already have is the whole app, and it stays that way.
