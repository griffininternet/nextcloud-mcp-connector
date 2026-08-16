"""The authorization server of this app: the SDK protocol, plus the four controls it lacks.

**Why a provider and not four endpoints of our own.** The stack research of phase 0 said
the SDK brings no authorization server; for mcp 2.0.0 that is wrong, and the difference is
the size of this plan. ``create_auth_routes`` serves ``/authorize``, ``/token``,
``/register`` and ``/revoke`` with PKCE as a required field, ``S256`` as the only method
the request model accepts, exact redirect matching, an expiring code, client
authentication with ``compare_digest`` and the RFC error shapes for all of them. Rebuilding
that would mean rewriting tested security code to arrive at the same behaviour. What the
SDK deliberately leaves to us is the policy, and that is what lives here: the audience
binding of RFC 8707, the https rule for redirect addresses, the refresh rotation with reuse
detection, and the client allowlist of AUTH-07.

**Why not ``auth_server_provider=`` on the MCPServer constructor.** It works, and it
attaches the same routes to the MCP application instead of to this deployment mode, which
would put them into the standalone HTTP server of phase 1 as well (D-23). It also installs
``ProviderTokenVerifier``, which verifies a bearer through ``load_access_token`` and
therefore bypasses both the process cache and the audience check that plan 03-06 builds.
The routes are handed out by :func:`auth_routes` and attached by ``entry_exapp`` alone,
exactly like every other route factory of this project.

**What is built here and what still refuses.** ``register_client``, ``get_client``,
``authorize``, ``load_authorization_code`` and ``exchange_authorization_code`` are complete:
a client can register, ask, be sent through the sign in and trade its code for a token. The
refresh rotation with its reuse detection and the revocation are plan 03-07 and refuse until
then, and ``exchange_identity_assertion`` refuses permanently (D-33). A half implemented
protocol has to refuse rather than pass, which is the owner directive of this phase in its
smallest form.

**Why ``load_access_token`` stays a refusal although the tokens exist.** It is the hook of
the SDK's ``ProviderTokenVerifier``, which this deployment does not install: the bearer of
every request is checked by ``oauth/verifier.py``, which adds the process cache, the
audience check of RFC 8707 and the client policy. A second, weaker path to the same
decision is not a convenience, it is the one that gets forgotten in a review.

**Why ``get_client`` is the enforcement point.** ``/authorize``, ``/token`` and ``/revoke``
all load their client through it, so one refusal here covers all three (pitfall 9). It
answers ``None`` for a client that is unknown, blocked by an administrator, missing from
the allowlist or expired, and those four are indistinguishable from outside on purpose: an
answer that separates them is an information service for whoever is guessing (T-03-47).
"""

import base64
import binascii
import json
import logging
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from urllib.parse import unquote

from mcp.server.auth.handlers.revoke import RevocationHandler
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import AuthenticationError, ClientAuthenticator
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    IdentityAssertionParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    RegistrationError,
    TokenError,
)
from mcp.server.auth.routes import (
    AUTHORIZATION_PATH,
    REVOCATION_PATH,
    TOKEN_PATH,
    cors_middleware,
    create_auth_routes,
)
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from mcp.shared.auth_utils import check_resource_allowed
from pydantic import AnyHttpUrl, AnyUrl, ValidationError
from starlette.datastructures import FormData, MutableHeaders
from starlette.requests import Request
from starlette.routing import Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .. import config
from ..errors import ToolError
from ..exapp.ui.consent import consent_url
from . import loginflow
from .metadata import AS_METADATA_SUFFIX, REFRESH_SCOPE, RESOURCE_SUFFIX, TOOL_SCOPE
from .registry import (
    IDLE_REGISTRATION_TTL,
    UNUSED_REGISTRATION_TTL,
    ClientPolicy,
    client_policy,
    redirect_uri_allowed,
)
from .store import ACCESS_TOKEN_TTL, OAuthStore, store_opener, token_hash

__all__ = [
    "FAMILY_BYTES",
    "TOKEN_BYTES",
    "HashedClientAuthenticator",
    "NextcloudOAuthProvider",
    "NoStore",
    "StoreProvider",
    "auth_routes",
]

#: The two client authentication methods of RFC 6749 §2.3.1. Named here so the literal
#: appears once and so the third method of the registry, ``none``, is the absence of both.
_AUTH_BASIC = "client_secret_basic"
_AUTH_POST = "client_secret_post"

#: The two verbs the machine endpoints of the authorization server answer. ``OPTIONS`` is
#: the CORS preflight the SDK wrapper handles; the manifest declares ``POST`` alone,
#: because no browser calls these endpoints cross origin in this topology (D-38).
_MACHINE_VERBS = ["POST", "OPTIONS"]

#: How a caller hands in its own store, which is what the tests of this module do and what
#: ``entry_exapp`` uses to give the browser onboarding and the authorization server the same
#: one. Without it the provider opens its own on first use.
type StoreProvider = Callable[[], Awaitable[OAuthStore]]

#: What a refused registration says. It names the reason, because an administrator turned
#: the switch off and the developer on the other end has to learn that from the answer
#: rather than from a support ticket (D-40).
_DCR_OFF = "dynamic client registration is disabled on this instance"

#: What a refused redirect address says. It names the rule and not the address: the value
#: came from the request and is echoed nowhere.
_REDIRECT_RULE = "redirect_uris must use https, except loopback addresses of native clients"

#: The description of every method that is not built yet. One sentence, no internal detail:
#: a client cannot act on the plan number, and an attacker should not read one.
_NOT_YET = "this authorization server cannot complete the request"

#: What a refused exchange says. Each names the rule and never a value of the request: the
#: developer on the other end has to be able to fix the call, and nothing more is owed.
_NO_AUDIENCE = "the grant carries no resource, which this server requires (RFC 8707)"
_WRONG_AUDIENCE = "the grant was issued for another resource"
_CLIENT_GONE = "this client may not use this authorization server"
_CODE_SPENT = "the authorization code is not valid"

#: 32 bytes of entropy behind every token this server issues, which ``token_urlsafe``
#: renders as 43 characters. The token is the whole authorisation of a connection, and it
#: exists on disk only as its SHA-256 digest.
TOKEN_BYTES = 32

#: The id that ties an access token to the refresh token it was issued with. Not a secret,
#: never handed out, and the unit a reuse detection kills in plan 03-07.
FAMILY_BYTES = 16

_HINT_ISSUER = (
    f"{config.ENV_PUBLIC_URL} is the address clients reach this app under, for example "
    "https://cloud.example.com/exapps/mcp_connector. RFC 8414 requires https for an issuer, "
    "with the loopback exception for a local test."
)

#: 32 bytes of entropy behind a flow id, which ``token_urlsafe`` renders as 43 characters.
#: The value is the whole authorisation of the consent screen for the length of one sign
#: in, so it is drawn from the same generator as every other secret of this phase.
FLOW_ID_BYTES = 32

logger = logging.getLogger("mcp_connector.oauth.provider")


class NextcloudOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """The one provider of this deployment. Built once per application, never per request."""

    def __init__(
        self,
        *,
        env: Mapping[str, str] | None = None,
        policy: ClientPolicy | None = None,
        store_provider: StoreProvider | None = None,
    ) -> None:
        self._env = env
        self._policy = policy if policy is not None else client_policy(env)
        self._store = store_provider if store_provider is not None else store_opener(env)
        #: The canonical audience of every token this server issues (RFC 8707). Built from
        #: the configured public URL and never from a request, like every other identity
        #: statement of this app (T-03-02).
        self._resource = f"{config.public_url(env)}{RESOURCE_SUFFIX}"

    def __repr__(self) -> str:
        return f"NextcloudOAuthProvider(resource={self._resource!r}, policy={self._policy!r})"

    @property
    def policy(self) -> ClientPolicy:
        """What an administrator decided. Read by the consent screen and by the routes."""
        return self._policy

    async def store(self) -> OAuthStore:
        """The store of this application, opened at its first use."""
        return await self._store()

    # --- the two halves this plan builds ------------------------------------------------

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """The enforcement point of AUTH-07, on the way into three endpoints.

        Four refusals with one answer, and a fifth that is not a refusal but a sweep: a
        registration that never produced a token is deleted when somebody asks for it, and
        so is one that has not been used for a season. That is the whole cleanup of the
        registry (T-03-44), because this project has no cron and a table that only grows
        is a denial of service with a delay.
        """
        try:
            store = await self.store()
            row = await store.load_client(client_id)
        except Exception as exc:
            # A store that cannot be opened or read is not a reason to let a client in
            # (D-37). The kind of the failure is logged, no value of the request is.
            logger.error("the client lookup has no store: %s", type(exc).__name__)
            return None

        if row is None:
            return None

        client = _client_information(row.metadata_json, client_id)
        if client is None:
            return None

        if not row.allowed:
            return None

        addresses = [str(uri) for uri in client.redirect_uris or []]
        if not self._policy.allows(client_id, addresses):
            return None

        if _has_expired(row.registered_at, row.last_used_at):
            await store.delete_client(client_id)
            return None

        return client

    async def client_secret_hash(self, client_id: str) -> str | None:
        """The stored digest of this client's secret, or ``None`` for a public client.

        Deliberately not part of what :meth:`get_client` returns: the SDK model carries a
        plaintext secret field, and a digest in it would be compared against a presented
        secret as if it were one. Whoever needs the digest asks for it, which is exactly
        one caller, :class:`HashedClientAuthenticator`.

        A store that cannot answer raises out of here instead of answering ``None``: the
        caller turns that into a refused authentication, and ``None`` would mean "this
        client has no secret", which is the one reading that would let a caller in.
        """
        store = await self.store()
        row = await store.load_client(client_id)
        return None if row is None else row.client_secret_hash

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Store a self registered client, once the two checks of D-35 pass.

        The SDK only attaches ``/register`` when registration is enabled, so the first
        check looks redundant. It is not: it is the half that names the reason, and it is
        the one that holds if the route is ever reachable another way. The second check is
        the one the SDK does not do at all: it accepts any address a registration sends,
        including ``http://`` on a host somebody else controls (T-03-41).
        """
        if not self._policy.dcr_enabled:
            raise RegistrationError("invalid_client_metadata", _DCR_OFF)

        addresses = [str(uri) for uri in client_info.redirect_uris or []]
        for address in addresses:
            if not redirect_uri_allowed(address):
                raise RegistrationError("invalid_redirect_uri", _REDIRECT_RULE)

        secret = client_info.client_secret
        store = await self.store()
        await store.save_client(
            client_info.client_id,
            # The secret is dropped from the record and kept as a digest, like every other
            # credential of this phase (T-03-11). The client authenticator of plan 03-06
            # compares against that digest, which is what ``client_secret_hash`` exists for.
            metadata_json=client_info.model_dump_json(exclude={"client_secret"}),
            secret_hash=token_hash(secret) if secret else None,
            # In the allowlist mode a client that nobody listed is stored as not allowed,
            # so the block survives a restart and shows up in the admin view of phase 4.
            # A client whose return address is on the list is stored as allowed, because
            # that address is the only property an administrator can name in advance.
            allowed=self._policy.allows(client_info.client_id, addresses),
        )

    # --- what plan 03-06 and plan 03-07 fill in -----------------------------------------

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Open a Nextcloud sign in and send the browser to our own consent screen.

        The audience is decided here and not at the token endpoint, and it is required
        rather than defaulted: a token without an audience would be accepted by every other
        MCP server a user connects, which is the confused deputy this parameter exists
        against (RFC 8707, T-03-46). The second half of that check, at the moment the token
        is issued, is plan 03-06; refusing here means no sign in is even opened for a
        request that could never be granted.

        The Nextcloud round trip happens on this path and never on the token path. The
        browser has a generous timeout, the token endpoint of a connector has ten seconds
        (pitfall 13), and a Nextcloud call under load is exactly the sporadic timeout
        nobody can reproduce afterwards.
        """
        resource = (params.resource or "").strip()
        if not resource:
            raise AuthorizeError("invalid_target", "the resource parameter is required")
        if not check_resource_allowed(resource, self._resource):
            raise AuthorizeError("invalid_target", "the resource does not match this server")

        started = await loginflow.start_flow(client.client_name or "", env=self._env)
        if started is None:
            # loginflow logged what happened; nothing of the request is repeated here.
            raise AuthorizeError("temporarily_unavailable", "the sign in could not be started")

        flow_id = secrets.token_urlsafe(FLOW_ID_BYTES)
        try:
            store = await self.store()
            await store.create_flow(
                flow_id,
                client_id=client.client_id,
                redirect_uri=str(params.redirect_uri),
                redirect_uri_explicit=params.redirect_uri_provided_explicitly,
                code_challenge=params.code_challenge,
                state=params.state,
                scopes=" ".join(params.scopes or []),
                resource=resource,
                poll_token=started.poll_token,
            )
        except Exception:
            logger.exception("the authorization request could not be written to the store")
            raise AuthorizeError("server_error", "the request could not be remembered") from None

        return consent_url(config.public_url(self._env), flow_id, started.login_url)

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        """Read a code back, with everything the token endpoint compares against it.

        Reads and does not consume: the SDK loads a code, checks four things about it (it
        belongs to this client, it has not expired, the return address is the one of the
        authorization request, the PKCE verifier matches the challenge) and only then asks
        for the exchange. Spending the code inside this method would burn it on every
        failed check.

        Two of the fields come from the authorization rather than from the code: the client
        and the user. The code points at its authorization, and the authorization is the
        row that knows whose connection this is, which is also why a revoked one answers
        ``None`` here already.
        """
        del client
        try:
            store = await self.store()
            row = await store.load_auth_code(authorization_code)
            if row is None:
                return None
            authorization = await store.load_authorization(row.auth_id)
        except Exception as exc:
            # Fail closed (D-37): a store that cannot answer is not a code that exists.
            logger.error("an authorization code could not be read: %s", type(exc).__name__)
            return None

        if authorization is None or authorization.revoked_at is not None:
            return None

        return AuthorizationCode(
            code=authorization_code,
            scopes=authorization.scopes.split(),
            expires_at=float(row.expires_at),
            client_id=authorization.client_id,
            code_challenge=row.code_challenge,
            redirect_uri=AnyUrl(row.redirect_uri),
            redirect_uri_provided_explicitly=row.redirect_uri_explicit,
            resource=row.resource,
            subject=authorization.nc_user,
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """Turn one consent into one opaque access token and one refresh token.

        The order of this method is the order of its risks. The audience is checked first
        and fails closed on a missing value, because a token without one would be accepted
        by every other MCP server the user connects (RFC 8707, pitfall 3, T-03-51). The
        client policy is asked second, because a block that arrived while the user was on
        the consent screen must not be outrun by a code that was already issued (pitfall 9,
        T-03-55). Only then is the code spent, in the one atomic statement that makes a
        second exchange impossible, and only after that do the tokens exist.

        Nothing here talks to Nextcloud. The whole Nextcloud round trip of this phase
        happens in the browser path, where a person is waiting and a second costs nothing;
        a connector gives its token endpoint about ten seconds (pitfall 13, T-03-58).
        """
        resource = (authorization_code.resource or "").strip()
        if not resource:
            raise TokenError("invalid_target", _NO_AUDIENCE)
        if not check_resource_allowed(resource, self._resource):
            raise TokenError("invalid_target", _WRONG_AUDIENCE)

        if await self.get_client(client.client_id) is None:
            raise TokenError("invalid_client", _CLIENT_GONE)

        store = await self.store()
        spent = await store.redeem_auth_code(authorization_code.code)
        if spent is None:
            # Used, expired or never issued. One answer for all three, which is also the
            # answer a client expects for a grant it may not use again (RFC 6749 §5.2).
            raise TokenError("invalid_grant", _CODE_SPENT)

        access = secrets.token_urlsafe(TOKEN_BYTES)
        refresh = secrets.token_urlsafe(TOKEN_BYTES)
        family = secrets.token_urlsafe(FAMILY_BYTES)
        scopes = " ".join(authorization_code.scopes)
        await store.create_access_token(
            access, auth_id=spent.auth_id, family_id=family, scopes=scopes, resource=resource
        )
        await store.create_refresh_token(refresh, auth_id=spent.auth_id, family_id=family)
        # A registration that produced a token is a connection somebody made, and it lives
        # on the long expiry window from here on (AUTH-07, T-03-44).
        await store.touch_client(client.client_id)

        return OAuthToken(
            access_token=access,
            token_type="Bearer",  # noqa: S106 - the token type of RFC 6750, not a secret
            expires_in=ACCESS_TOKEN_TTL,
            scope=scopes,
            refresh_token=refresh,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """Plan 03-07 rotates refresh tokens and detects their reuse."""
        del client, refresh_token
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Plan 03-07 rotates, with the grace window of D-41 and the family kill after it."""
        del client, refresh_token, scopes
        raise TokenError("invalid_grant", _NOT_YET)

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Refused on purpose: the bearer of a request is checked by ``oauth/verifier.py``.

        This method exists because the protocol has it, and it answers ``None`` because the
        only caller it would ever have is the SDK's ``ProviderTokenVerifier``, which this
        application does not install. That verifier knows neither the process cache nor the
        audience check nor the client policy, so a token accepted through here would be one
        accepted by a weaker path than the one at the transport boundary (T-03-51).
        """
        del token
        return None

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Plan 03-07 revokes a family and deletes the app password behind it (SC 4).

        Doing nothing is the correct answer while no token exists: RFC 7009 requires a 200
        for a token the server does not know, and that is exactly the state of this plan.
        """
        del token
        return

    async def exchange_identity_assertion(
        self, client: OAuthClientInformationFull, params: IdentityAssertionParams
    ) -> OAuthToken:
        """Refused permanently, not until a later plan.

        The SEP-990 profile hands an enterprise identity provider the right to assert who
        a user is. This connector has exactly one identity source, Nextcloud itself, and
        adding a second one is a decision for a later version and not a side effect of a
        grant type (D-33).
        """
        del client, params
        raise TokenError("unsupported_grant_type", _NOT_YET)


def auth_routes(
    env: Mapping[str, str] | None = None, *, provider: NextcloudOAuthProvider
) -> list[Route]:
    """The routes of the authorization server, with ``no-store`` over all of them.

    Two of the routes the SDK builds are dropped here, and both because this app already
    serves the same path with more than the SDK can know. ``oauth/metadata.py`` publishes
    the authorization server document with the fields the SDK does not set and the issuer
    spelled exactly as it was configured (03-01), and ``oauth/consent.py`` serves
    ``/authorize`` in front of the SDK handler, so that a refused request ends on a page a
    person can read instead of in JSON a browser displays raw. Two routes on one path would
    answer whichever was registered first, which is not a property to leave to registration
    order.

    The issuer is the configured public URL. The SDK requires https for it, with the
    loopback exception that makes the local test topology work; a value that fails that
    rule is a deployment error and is named as one instead of surfacing as a traceback.
    """
    try:
        issuer = AnyHttpUrl(config.public_url(env))
        routes = create_auth_routes(
            provider=provider,
            issuer_url=issuer,
            client_registration_options=ClientRegistrationOptions(
                enabled=provider.policy.dcr_enabled,
                valid_scopes=[TOOL_SCOPE, REFRESH_SCOPE],
                default_scopes=[TOOL_SCOPE],
            ),
            revocation_options=RevocationOptions(enabled=True),
        )
    except ValueError as exc:
        raise ToolError(
            message=f"{config.ENV_PUBLIC_URL} is not a usable issuer: {exc}", hint=_HINT_ISSUER
        ) from None

    dropped = (AS_METADATA_SUFFIX, AUTHORIZATION_PATH, TOKEN_PATH, REVOCATION_PATH)
    kept = [route for route in routes if route.path not in dropped]
    # The two endpoints that authenticate a client are rebuilt with our own authenticator.
    # Everything else about them stays the SDK's: the same handler, the same CORS wrapper
    # and the same methods, because only the comparison of the secret is ours.
    authenticator = HashedClientAuthenticator(provider)
    kept.append(
        Route(
            TOKEN_PATH,
            endpoint=cors_middleware(TokenHandler(provider, authenticator).handle, _MACHINE_VERBS),
            methods=_MACHINE_VERBS,
        )
    )
    kept.append(
        Route(
            REVOCATION_PATH,
            endpoint=cors_middleware(
                RevocationHandler(provider, authenticator).handle, _MACHINE_VERBS
            ),
            methods=_MACHINE_VERBS,
        )
    )
    for route in kept:
        route.app = NoStore(route.app)
    return kept


class HashedClientAuthenticator(ClientAuthenticator):
    """Authenticate a client at ``/token`` and ``/revoke`` against the stored digest.

    The SDK compares ``client.client_secret`` with the presented secret in plaintext, which
    means the store would have to keep one. It does not: plan 03-02 stores a SHA-256 digest
    for the same reason every other credential of this phase is stored as one, so that a
    stolen store file cannot be replayed against this server (T-03-11). This class is the
    other half of that decision, and without it the token endpoint would refuse every
    confidential client.

    What it does not change: which clients exist and which of them may act. Both come from
    ``get_client``, which is the one enforcement point of AUTH-07 (pitfall 9). A public
    client, which is what Claude.ai and ChatGPT are, has no secret at all and is
    authenticated by PKCE alone, exactly as the SDK does it.
    """

    def __init__(self, provider: "NextcloudOAuthProvider") -> None:
        super().__init__(provider)
        self._provider = provider

    async def authenticate_request(self, request: Request) -> OAuthClientInformationFull:
        form = await request.form()
        client_id = str(form.get("client_id") or "")
        if not client_id:
            raise AuthenticationError("Missing client_id")

        client = await self._provider.get_client(client_id)
        if client is None:
            raise AuthenticationError("Invalid client_id")

        try:
            stored = await self._provider.client_secret_hash(client_id)
        except Exception as exc:
            # A store that cannot be read is a refused authentication, never an accepted
            # one (D-37). The kind of the failure is logged, no value of the request is.
            logger.error("a client could not be authenticated: %s", type(exc).__name__)
            raise AuthenticationError("The client could not be authenticated") from None
        if stored is None:
            # A public client. The SDK treats a registration without a secret the same way,
            # and PKCE is what authenticates the exchange (OAuth 2.1, S256 enforced).
            return client

        presented = _presented_secret(request, form, client_id, client)
        if not presented:
            raise AuthenticationError("Client secret is required")
        # The comparison runs on the digests and in constant time, for the same reason the
        # AppAPI handshake compares that way: the value comes from a request, and a
        # comparison that stops early leaks its prefix over enough attempts (T-01-24).
        if not secrets.compare_digest(token_hash(presented), stored):
            raise AuthenticationError("Invalid client_secret")
        return client


def _presented_secret(
    request: Request,
    form: FormData,
    client_id: str,
    client: OAuthClientInformationFull,
) -> str:
    """The secret this request carries, in the form the registration asked for.

    The two methods of RFC 6749 §2.3.1 and nothing else. A client that registered for
    ``none`` and then sends a secret is not authenticated by it: the method decides, not
    the request, because anything else would let a caller pick the weaker of two paths.
    """
    if client.token_endpoint_auth_method == _AUTH_BASIC:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            raise AuthenticationError("Missing or invalid Basic authentication")
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError):
            # The offending value is credential material and stays out of the message.
            raise AuthenticationError("Invalid Basic authentication header") from None
        name, separator, secret = decoded.partition(":")
        if not separator or unquote(name) != client_id:
            raise AuthenticationError("Client ID mismatch in Basic auth")
        return unquote(secret)
    if client.token_endpoint_auth_method == _AUTH_POST:
        value = form.get("client_secret")
        return value if isinstance(value, str) else ""
    return ""


class NoStore:
    """Put ``Cache-Control: no-store`` on every answer of the authorization server.

    Two answers make this necessary and one rule makes it simple. The registration answer
    of the SDK carries no cache header at all, and the AppAPI PHP proxy caches a JSON
    answer without one for 3600 seconds, which would hand a second client the credentials
    of the first (pitfall 4, T-03-45). The metadata handler of the SDK sets ``public,
    max-age=3600``, which would pin a document with a stale public URL for an hour.

    The rule: every answer of an authorization server is either a credential or a decision
    about one, so there is no branch on which a cache header may survive. Overwriting
    unconditionally is therefore both simpler and stricter than merging, and it is what the
    HTML pages of this phase do through their own shell as well.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover - these routes are HTTP only
            await self._app(scope, receive, send)
            return

        async def send_with_no_store(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["cache-control"] = "no-store"
            await send(message)

        await self._app(scope, receive, send_with_no_store)


def _client_information(metadata_json: str, client_id: str) -> OAuthClientInformationFull | None:
    """Read a stored registration back, or refuse it. Never raise into a handler.

    A row this code cannot parse is a row from a future or a broken write. Both are
    reasons to refuse the client, never to answer a 500 that tells the caller a client id
    exists (fail closed, D-37, T-03-47).
    """
    try:
        return OAuthClientInformationFull.model_validate_json(metadata_json)
    except (ValidationError, ValueError, json.JSONDecodeError):
        logger.error("the stored registration of a client cannot be read and is refused")
        return None


def _has_expired(registered_at: int, last_used_at: int | None, *, now: int | None = None) -> bool:
    """Whether this registration ran out, by the window that applies to it.

    Two windows, because the two states mean different things: a registration that never
    produced a token is a fingerprint somebody left behind and goes after a day, while one
    that was used is a connection somebody made and goes after a season without a sign of
    life (AUTH-07).
    """
    moment = int(time.time()) if now is None else now
    if last_used_at is None:
        return registered_at < moment - UNUSED_REGISTRATION_TTL
    return last_used_at < moment - IDLE_REGISTRATION_TTL
