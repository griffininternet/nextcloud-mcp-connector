<!--
Entwurf eines Kommentars an nextcloud/user_oidc Issue #925.

Status: Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner.

Kanal:        https://github.com/nextcloud/user_oidc/issues/925
Entstanden:   Phase 17, Plan 17-07 (D-08), 2026-08-29
Bedingung:    Nach D-08 und der Regel aus context_agent#230 geht dieser Text nur mit
              geglueckter Live-Reproduktion raus. Sie ist gelaufen; die Messwerte
              stehen in docs/spike-opendesk.md, Abschnitt 2.1 (S5a bis S5c) und 5.6.
Kein Agent hat diesen Text gesendet, gepostet oder eingereicht. Kein `gh issue comment`,
kein Browserversand, kein Playwright-Lauf.

Der Text unterhalb dieses Kommentars ist der Kommentar, wie er auf GitHub erscheinen
wuerde. Er ist englisch, weil der Kanal englisch ist.
-->

Adding a case that I think this issue does not yet cover: an AppAPI ExApp with no PHP part
at all. I have measured what happens today rather than only read the code, so the numbers
and log lines below come from a running instance.

First, so this comment is not misread as a bug report: as I understand it this issue is the
feature request the current implementation grew out of, and the event flow that ships today
is the one sketched here in the thread. The mechanism works. What I ran into is a case that
the resulting design does not reach, and I would like to check my reading before I plan
around it.

## What I ran

An MCP server that runs as an ExApp: a container next to Nextcloud, reached through AppAPI,
acting on behalf of the signed-in user. The neighbouring component it should reach is
OpenProject in an openDesk-style deployment, still strictly on behalf of that same user,
which is what `integration_openproject` and token exchange are for.

Versions, all read from the running instance and not from documentation:

| Component | Version | Read with |
|---|---|---|
| Nextcloud | 33.0.7 (build 33.0.7.1) | `occ status` |
| `user_oidc` | 8.11.0 | `occ app:list` |
| `integration_openproject` | 3.1.1 | `occ app:list` |
| Keycloak | 26.7.0 | `kc.sh --version` in the container |

## Reproduction

Everything is on loopback, all names resolve to 127.0.0.1.

1. Keycloak with a realm holding a confidential client for Nextcloud and a second client
   used only as the exchange audience.
2. `occ user_oidc:provider spike --clientid=... --clientsecret=... --discoveryuri=... --scope="openid email profile"`,
   then `occ config:app:set user_oidc store_login_token --value=1`.
3. `occ config:app:set integration_openproject authorization_method --value=oidc`, plus
   `sso_provider_type`, `oidc_provider`, `targeted_audience_client_id` and `token_exchange`.
4. `occ log:manage --level 0`. This step matters: the lines that tell the three paths apart
   are `logger->debug`, and the default level hides all of them.
5. Call an OCS route of `integration_openproject` under plain AppAPI impersonation, with the
   ExApp headers and no cookie and no app password, after expiring the cached token
   (`occ user:setting <uid> integration_openproject token_expires_at 0`).

## What the log says

With `sso_provider_type=external` and `token_exchange=0`:

```
user_oidc                [ExternalTokenRequestedListener] received request
user_oidc                [TokenService] Get token from the session
user_oidc                [TokenService] getToken: no session data
integration_openproject  Token event has not been caught by 'user_oidc'
```

With `token_exchange=1` and `store_login_token=1`:

```
user_oidc                [ExchangedTokenRequestedListener] received request for audience: ...
user_oidc                [TokenService] Starting token exchange
user_oidc                [TokenService] Get token from the session
user_oidc                [TokenService] getToken: no session data
user_oidc                [TokenService] Failed to exchange token, no login token found in the session
```

With `token_exchange=1` and `store_login_token=0`:

```
user_oidc                [ExchangedTokenRequestedListener] received request for audience: ...
integration_openproject  Failed to get token: Failed to exchange token, storing the login
                         token is disabled. It can be enabled in config.php
```

In every case the OCS call answers 401. The counter-probe, same account and same
configuration but with a real browser session from an OIDC login, logs
`[TokenService] getToken: token is still valid, ...` instead, so the only variable between
the two is the session.

## The one thing I got wrong before measuring, in case it helps

I had assumed the listeners bail out at their first check under AppAPI impersonation. They
do not. `if (!$this->userSession->isLoggedIn()) { return; }` is the first statement in all
three listeners (`ExternalTokenRequestedListener.php:39`,
`ExchangedTokenRequestedListener.php:35`, `InternalTokenRequestedListener.php:35` at
v8.11.0), and it passes: AppAPI impersonation goes through `OC::tryAppAPILogin`, which
resolves a user session that `IUserSession::isLoggedIn()` counts as logged in. The listener
is entered and its debug line appears.

So the blocker is not the login check. It is one step later: the session exists, but it
carries no login token, because it was never created by an OIDC login.

## The code I am reading, with lines at v8.11.0

- `lib/Service/TokenService.php:316` reads `store_login_token` through
  `appConfig->getValueString(..., 'store_login_token', '0', lazy: true)`, so it is an app
  config value. The exception message at 318 says "It can be enabled in config.php", which
  sent me looking in the wrong place for a while. `occ config:app:set user_oidc
  store_login_token --value=1` is what actually satisfies it.
- `lib/Service/TokenService.php:325-333`: `getExchangedToken()` calls `getToken()`, which
  reads `SESSION_TOKEN_KEY` (`:50`, `:93`), and a `null` there becomes
  `TokenExchangeFailedException`.
- `lib/Listener/ExternalTokenRequestedListener.php:47` throws
  `GetExternalTokenFailedException` when `store_login_token` is off.
- `lib/Service/TokenService.php:getTokenFromOidcProviderApp()` does take a `$userId` rather
  than a session, and the internal path really does not ask the session question. I could
  not measure it to the end, though: on my instance it stops at
  `[TokenService] Failed to get token from Oidc provider app, oidc app is not installed`,
  because that path needs Nextcloud itself to be the provider rather than the external one.
- `appinfo/routes.php` exposes no route, OCS or otherwise, that returns a token, so the
  exchange is reachable only from PHP running inside the same server process.

## The question

Is that reading correct, and is there an intended way for an ExApp without a PHP part to
obtain an exchanged token for the signed-in user? If there is one I have missed, I would
rather use it than ask for anything.

If there is not, two follow-up questions:

1. Would an OCS endpoint for the exchange be something you would consider? The permission
   model would be the same as for any other OCS call, and the caller is already
   authenticated as the user.
2. Could the session-free path be extended to the external provider case, or is holding the
   login token in the session fundamental to how it is refreshed?

I am not asking on my own behalf alone. As far as I can tell this affects any ExApp that
wants to act for the user against a second component of the same suite, which is a fair
share of what a sovereign workplace is meant to do.
