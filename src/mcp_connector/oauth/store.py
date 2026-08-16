"""Everything of this phase that has to survive a restart, in one SQLite file.

**Why SQLite and not a JSON file.** The refresh rotation is a compare and set: exactly one
of two simultaneous redemptions may win, and the loser has to learn that it lost rather
than to overwrite the winner. A file that is read, changed and written back cannot do
that; a transaction with ``BEGIN IMMEDIATE`` can, in one line of SQL, across threads and
across worker processes on the same volume (pitfall 10, T-03-13).

**Why the standard library module and not aiosqlite.** Every call here runs in
:func:`asyncio.to_thread` with its own connection, which is the whole of what an async
wrapper would add. The dependency surface of this project is a deliberate decision
(``docs/dependency-audit.md``), and a new direct dependency for a thirty line wrapper is
not one worth making.

**Pragmas, set on every connection because two of the three are per connection.**
``journal_mode = WAL`` so a reader does not block the writer of a parallel request,
``foreign_keys = ON`` so revoking a client actually takes its authorizations with it, and
``busy_timeout`` so the loser of a lock waits for the winner instead of failing with
"database is locked" while a user watches a spinner.

**What is stored and what is not.** Tokens exist here only as their SHA-256 hex digest, so
a stolen file cannot be replayed against the server (T-03-11). The two secrets that must
come back out, the Nextcloud app password of an authorization and the poll token of a
running login flow, are encrypted with :mod:`mcp_connector.oauth.crypto` and bound to the
id of their own row, so moving a ciphertext to another row makes it unreadable rather than
useful (T-03-12). Every row object that carries such a value masks its repr.

No module global mutable state: the store is an object that is given its path and its key,
which is the same rule the credential objects of phase 1 follow. Two processes on the same
file are a supported case, not an accident (SRV-05).
"""

import asyncio
import hashlib
import sqlite3
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import config
from . import crypto
from .crypto import decrypt, encrypt

#: What every method below hands to the worker thread: one function, one connection, one
#: result. Naming it keeps the three wrappers at the bottom readable and typed.
type Work[T] = Callable[[sqlite3.Connection], T]

__all__ = [
    "ACCESS_TOKEN_TTL",
    "AUTH_CODE_TTL",
    "FLOW_TTL",
    "IDLE_CLIENT_TTL",
    "REDEEM_EXPIRED",
    "REDEEM_OK",
    "REDEEM_REUSED",
    "REDEEM_UNKNOWN",
    "REFRESH_TOKEN_TTL",
    "ROTATION_GRACE",
    "STATES",
    "STATE_ACTIVE",
    "STATE_REVOKED",
    "STATE_USED",
    "STORE_FILENAME",
    "UNUSED_CLIENT_TTL",
    "VALIDATION_CACHE_TTL",
    "AccessTokenRow",
    "AuthCodeRow",
    "AuthorizationRow",
    "ClientRow",
    "FlowRow",
    "OAuthStore",
    "RefreshRedemption",
    "RefreshTokenRow",
    "store_opener",
    "token_hash",
]

#: The one file in the persistent volume of this app.
STORE_FILENAME = "oauth.sqlite3"

# --- lifetimes ---------------------------------------------------------------------
# Every number of seconds this phase uses is one of the names below. A literal at a call
# site is a value nobody finds again when a client turns out to need a different one.

#: An authorization code is a hand over between two requests of the same browser, so it is
#: short by an order of magnitude compared to everything else here.
AUTH_CODE_TTL = 60

#: One hour, which is what the connectors expect and what keeps a revocation cheap.
ACCESS_TOKEN_TTL = 3600

#: Thirty days. Longer than any session, short enough that an abandoned connection dies.
REFRESH_TOKEN_TTL = 30 * 24 * 3600

#: Twenty minutes, the pace Nextcloud sets for its own login flow.
FLOW_TTL = 1200

#: How long a validated access token may be answered from a process cache (03-06 uses it).
VALIDATION_CACHE_TTL = 5

#: The idempotent retry window of the rotation (D-41). Inside it the same refresh token is
#: answered with the same successor; outside it a second use is an attack on the family.
ROTATION_GRACE = 10

#: A registration that never produced a token is a fingerprint, not a client.
UNUSED_CLIENT_TTL = 24 * 3600

#: A client that has not been seen for a season goes, and takes its authorizations along.
IDLE_CLIENT_TTL = 90 * 24 * 3600

# --- refresh token states ------------------------------------------------------------

STATE_ACTIVE = "active"
STATE_USED = "used"
STATE_REVOKED = "revoked"

#: Plain strings and an explicit check instead of an enum on the column: the refusal of an
#: unknown value has to stay reachable, and a type that makes the bad case unwritable also
#: makes it untestable (the rule of ``nextcloud/credentials.py``).
STATES = (STATE_ACTIVE, STATE_USED, STATE_REVOKED)

# --- outcomes of a refresh redemption --------------------------------------------------
# Three failures, not one: plan 03-07 kills the family for a reuse and answers a plain
# invalid_grant for the other two, so the store has to tell them apart.

REDEEM_OK = "ok"
REDEEM_UNKNOWN = "unknown"
REDEEM_EXPIRED = "expired"
REDEEM_REUSED = "reused"

#: The schema of 03-RESEARCH.md, verbatim except for the ``IF NOT EXISTS`` that makes it
#: idempotent for a second process opening the same file.
SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  client_id TEXT PRIMARY KEY,
  client_secret_hash TEXT,
  metadata_json TEXT NOT NULL,
  allowed INTEGER NOT NULL DEFAULT 1,
  registered_at INTEGER NOT NULL,
  last_used_at INTEGER
);

CREATE TABLE IF NOT EXISTS flows (
  flow_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  redirect_uri TEXT NOT NULL,
  redirect_uri_explicit INTEGER NOT NULL,
  code_challenge TEXT NOT NULL,
  state TEXT,
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  poll_token_enc BLOB NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS authorizations (
  auth_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  nc_user TEXT NOT NULL,
  app_password_enc BLOB NOT NULL,
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  revoked_at INTEGER,
  cleanup_at INTEGER
);

CREATE TABLE IF NOT EXISTS auth_codes (
  code_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  redirect_uri TEXT NOT NULL,
  redirect_uri_explicit INTEGER NOT NULL DEFAULT 1,
  code_challenge TEXT NOT NULL,
  resource TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at INTEGER
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
  token_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  family_id TEXT NOT NULL,
  state TEXT NOT NULL,
  successor TEXT,
  issued_at INTEGER NOT NULL,
  used_at INTEGER,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS refresh_family ON refresh_tokens(family_id);

CREATE TABLE IF NOT EXISTS access_tokens (
  token_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  family_id TEXT NOT NULL,
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  revoked_at INTEGER
);
CREATE INDEX IF NOT EXISTS access_family ON access_tokens(family_id);
"""


def token_hash(token: str) -> str:
    """The one form a token takes on disk. SHA-256 hex, never the token itself.

    No salt and no key stretching on purpose: these are 256 bit random values, not
    passwords, so there is nothing to brute force and a per row salt would only make the
    lookup by token impossible.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True, repr=False)
class ClientRow:
    """A registered client. The secret hash is masked like every other credential."""

    client_id: str
    client_secret_hash: str | None
    metadata_json: str
    allowed: bool
    registered_at: int
    last_used_at: int | None

    def __repr__(self) -> str:
        return (
            f"ClientRow(client_id={self.client_id!r}, allowed={self.allowed!r}, "
            f"registered_at={self.registered_at!r}, last_used_at={self.last_used_at!r}, "
            "client_secret_hash='***')"
        )


@dataclass(frozen=True, slots=True, repr=False)
class FlowRow:
    """A login flow that is still running. ``poll_token`` is the decrypted value."""

    flow_id: str
    client_id: str
    redirect_uri: str
    redirect_uri_explicit: bool
    code_challenge: str
    state: str | None
    scopes: str
    resource: str
    poll_token: str
    expires_at: int

    def __repr__(self) -> str:
        return (
            f"FlowRow(flow_id={self.flow_id!r}, client_id={self.client_id!r}, "
            f"redirect_uri={self.redirect_uri!r}, expires_at={self.expires_at!r}, "
            "poll_token='***')"
        )


@dataclass(frozen=True, slots=True)
class AuthorizationRow:
    """One connection of one user. The app password is deliberately not a field here.

    Reading it is an explicit act with its own method, so a caller cannot end up with a
    plaintext Nextcloud credential just because it wanted the user id.

    ``cleanup_at`` is the one field that is neither identity nor deadline: it is the moment
    at which somebody noticed that the Nextcloud app password of this connection still has
    to be handed back. It exists because the revocation must not hang on that deletion
    (pitfall 13, D-37), and something has to remember the attempt that failed.
    """

    auth_id: str
    client_id: str
    nc_user: str
    scopes: str
    resource: str
    created_at: int
    revoked_at: int | None
    cleanup_at: int | None = None


@dataclass(frozen=True, slots=True)
class AuthCodeRow:
    """What an authorization code is bound to: everything the token endpoint compares.

    ``redirect_uri_explicit`` is the one field that is neither a secret nor a deadline: the
    SDK compares the return address of the token request against the one of the
    authorization request, and a request that named none has to name none again. Carrying
    the flag is the only way that comparison can still be made after the flow record that
    knew it is gone.
    """

    auth_id: str
    redirect_uri: str
    redirect_uri_explicit: bool
    code_challenge: str
    resource: str
    expires_at: int


@dataclass(frozen=True, slots=True)
class AccessTokenRow:
    """A valid access token, with the user the request will act as."""

    auth_id: str
    family_id: str
    nc_user: str
    scopes: str
    resource: str
    expires_at: int


@dataclass(frozen=True, slots=True)
class RefreshTokenRow:
    """A refresh token as it stands in the file, with a state that was checked."""

    auth_id: str
    family_id: str
    state: str
    successor: str | None
    issued_at: int
    used_at: int | None
    expires_at: int


@dataclass(frozen=True, slots=True)
class RefreshRedemption:
    """The outcome of one redemption, plus what the caller needs to act on it.

    ``used_at`` and ``successor`` are filled for :data:`REDEEM_REUSED` only: they are what
    plan 03-07 needs to tell a network retry inside the grace window from a replay that
    has to kill the family (D-41).
    """

    outcome: str
    auth_id: str = ""
    family_id: str = ""
    used_at: int | None = None
    successor: str | None = None


class OAuthStore:
    """The persistence of the phase, bound to one file and one data key.

    Every method opens its own connection inside a worker thread and closes it again. That
    costs a fraction of a millisecond per call and buys the property this server needs
    most: no connection, no cursor and no transaction is shared between two requests, so
    two workers on the same volume behave exactly like two threads in one worker.
    """

    def __init__(self, path: Path, key: bytes) -> None:
        self._path = path
        self._key = key

    def __repr__(self) -> str:
        return f"OAuthStore(path={self._path!r}, key='***')"

    @property
    def path(self) -> Path:
        return self._path

    def form_token(self, flow_id: str) -> str:
        """The anti forgery value of the consent form of one flow (T-03-50).

        It lives on this object because the data key does, and nowhere else in the process
        holds that key. Nothing is read or written: the value is derived, which is why it
        is the same for every render of the same form and different for every deployment.
        """
        return crypto.form_token(self._key, flow_id)

    # --- clients --------------------------------------------------------------------

    async def save_client(
        self,
        client_id: str,
        *,
        metadata_json: str,
        secret_hash: str | None = None,
        allowed: bool = True,
        now: int | None = None,
    ) -> None:
        """Write a registration, keeping the original registration time on an update."""
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO clients (
                  client_id, client_secret_hash, metadata_json, allowed, registered_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(client_id) DO UPDATE SET
                  client_secret_hash = excluded.client_secret_hash,
                  metadata_json = excluded.metadata_json,
                  allowed = excluded.allowed
                """,
                (client_id, secret_hash, metadata_json, int(allowed), moment),
            )

        await self._write(work)

    async def load_client(self, client_id: str) -> ClientRow | None:
        def work(conn: sqlite3.Connection) -> ClientRow | None:
            row = conn.execute(
                "SELECT client_id, client_secret_hash, metadata_json, allowed, registered_at, "
                "last_used_at FROM clients WHERE client_id = ?",
                (client_id,),
            ).fetchone()
            if row is None:
                return None
            return ClientRow(
                client_id=row[0],
                client_secret_hash=row[1],
                metadata_json=row[2],
                allowed=bool(row[3]),
                registered_at=row[4],
                last_used_at=row[5],
            )

        return await self._read(work)

    async def touch_client(self, client_id: str, *, now: int | None = None) -> None:
        """Record that this client was actually used, which is what stops it expiring."""
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE clients SET last_used_at = ? WHERE client_id = ?", (moment, client_id)
            )

        await self._write(work)

    async def delete_client(self, client_id: str) -> None:
        """Remove a registration and, through the cascade, everything issued under it."""

        def work(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM clients WHERE client_id = ?", (client_id,))

        await self._write(work)

    # --- flows ----------------------------------------------------------------------

    async def create_flow(
        self,
        flow_id: str,
        *,
        client_id: str,
        redirect_uri: str,
        redirect_uri_explicit: bool,
        code_challenge: str,
        state: str | None,
        scopes: str,
        resource: str,
        poll_token: str,
        now: int | None = None,
    ) -> None:
        """Remember a pending authorization while Nextcloud runs the login."""
        moment = _moment(now)
        blob = encrypt(self._key, poll_token.encode("utf-8"), aad=flow_id)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            conn.execute(
                "INSERT INTO flows (flow_id, client_id, redirect_uri, redirect_uri_explicit, "
                "code_challenge, state, scopes, resource, poll_token_enc, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    flow_id,
                    client_id,
                    redirect_uri,
                    int(redirect_uri_explicit),
                    code_challenge,
                    state,
                    scopes,
                    resource,
                    blob,
                    moment + FLOW_TTL,
                ),
            )

        await self._write(work)

    async def load_flow(self, flow_id: str, *, now: int | None = None) -> FlowRow | None:
        """The flow, or ``None`` when it does not exist or ran out of time."""
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> FlowRow | None:
            row = conn.execute(
                "SELECT flow_id, client_id, redirect_uri, redirect_uri_explicit, code_challenge, "
                "state, scopes, resource, poll_token_enc, expires_at FROM flows "
                "WHERE flow_id = ? AND expires_at > ?",
                (flow_id, moment),
            ).fetchone()
            if row is None:
                return None
            return FlowRow(
                flow_id=row[0],
                client_id=row[1],
                redirect_uri=row[2],
                redirect_uri_explicit=bool(row[3]),
                code_challenge=row[4],
                state=row[5],
                scopes=row[6],
                resource=row[7],
                poll_token=decrypt(self._key, row[8], aad=row[0]).decode("utf-8"),
                expires_at=row[9],
            )

        return await self._read(work)

    async def delete_flow(self, flow_id: str) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM flows WHERE flow_id = ?", (flow_id,))

        await self._write(work)

    # --- authorizations -------------------------------------------------------------

    async def create_authorization(
        self,
        auth_id: str,
        *,
        client_id: str,
        nc_user: str,
        app_password: str,
        scopes: str,
        resource: str,
        now: int | None = None,
    ) -> None:
        """Store one connection: one user, one dedicated Nextcloud app password."""
        moment = _moment(now)
        blob = encrypt(self._key, app_password.encode("utf-8"), aad=auth_id)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT INTO authorizations (auth_id, client_id, nc_user, app_password_enc, "
                "scopes, resource, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (auth_id, client_id, nc_user, blob, scopes, resource, moment),
            )

        await self._write(work)

    async def load_authorization(self, auth_id: str) -> AuthorizationRow | None:
        def work(conn: sqlite3.Connection) -> AuthorizationRow | None:
            row = conn.execute(
                "SELECT auth_id, client_id, nc_user, scopes, resource, created_at, revoked_at, "
                "cleanup_at FROM authorizations WHERE auth_id = ?",
                (auth_id,),
            ).fetchone()
            if row is None:
                return None
            return AuthorizationRow(
                auth_id=row[0],
                client_id=row[1],
                nc_user=row[2],
                scopes=row[3],
                resource=row[4],
                created_at=row[5],
                revoked_at=row[6],
                cleanup_at=row[7],
            )

        return await self._read(work)

    async def app_password(self, auth_id: str) -> str | None:
        """Decrypt the Nextcloud app password of this authorization. An explicit act.

        Raises :class:`~mcp_connector.oauth.crypto.DecryptionRejected` when the ciphertext
        does not belong to this row or to this key, which is the case a moved ciphertext
        and a changed data key both produce.
        """

        def work(conn: sqlite3.Connection) -> bytes | None:
            row = conn.execute(
                "SELECT app_password_enc FROM authorizations WHERE auth_id = ?", (auth_id,)
            ).fetchone()
            return None if row is None else row[0]

        blob = await self._read(work)
        if blob is None:
            return None
        return decrypt(self._key, blob, aad=auth_id).decode("utf-8")

    async def delete_authorization(self, auth_id: str) -> None:
        """Remove a connection and, through the cascade, every code and token under it.

        The deliberate difference to :meth:`revoke_authorization`: a revoked authorization
        is a connection that existed and ended, and it is kept so a later revocation is
        idempotent and visible. A denied one never existed as far as the user is concerned,
        so the row goes and takes the ciphertext of an app password with it that nobody may
        ever use again.
        """

        def work(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM authorizations WHERE auth_id = ?", (auth_id,))

        await self._write(work)

    async def revoke_authorization(self, auth_id: str, *, now: int | None = None) -> None:
        """Mark the connection as gone. Idempotent: the first revocation time stands."""
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE authorizations SET revoked_at = ? WHERE auth_id = ? AND revoked_at IS NULL",
                (moment, auth_id),
            )

        await self._write(work)

    async def note_cleanup(self, auth_id: str, *, now: int | None = None) -> None:
        """Record that the Nextcloud app password of this connection is still out there.

        Written whenever a revocation could not hand the credential back, and whenever a
        revocation happened on a path that may not talk to Nextcloud at all, which is every
        path of the token endpoint (pitfall 13). Idempotent: the first note stands, because
        the interesting moment is the one at which the credential became an orphan.
        """
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE authorizations SET cleanup_at = ? WHERE auth_id = ? AND cleanup_at IS NULL",
                (moment, auth_id),
            )

        await self._write(work)

    # --- authorization codes --------------------------------------------------------

    async def create_auth_code(
        self,
        code: str,
        *,
        auth_id: str,
        redirect_uri: str,
        code_challenge: str,
        resource: str,
        redirect_uri_explicit: bool = True,
        now: int | None = None,
    ) -> None:
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            conn.execute(
                "INSERT INTO auth_codes (code_hash, auth_id, redirect_uri, "
                "redirect_uri_explicit, code_challenge, resource, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    token_hash(code),
                    auth_id,
                    redirect_uri,
                    int(redirect_uri_explicit),
                    code_challenge,
                    resource,
                    moment + AUTH_CODE_TTL,
                ),
            )

        await self._write(work)

    async def load_auth_code(self, code: str, *, now: int | None = None) -> AuthCodeRow | None:
        """A code that is still redeemable, or ``None``. Reads, never consumes.

        The token endpoint of the SDK loads a code, checks four things about it and only
        then asks the provider to exchange it, so the load has to leave the code alone.
        The single use is enforced where the tokens are issued, by
        :meth:`redeem_auth_code`, which is one atomic statement rather than this read
        followed by a write.
        """
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> AuthCodeRow | None:
            row = conn.execute(
                "SELECT auth_id, redirect_uri, redirect_uri_explicit, code_challenge, resource, "
                "expires_at FROM auth_codes "
                "WHERE code_hash = ? AND used_at IS NULL AND expires_at > ?",
                (token_hash(code), moment),
            ).fetchone()
            return None if row is None else _auth_code_row(row)

        return await self._read(work)

    async def redeem_auth_code(self, code: str, *, now: int | None = None) -> AuthCodeRow | None:
        """Consume the code, or return ``None``. The second caller always gets ``None``.

        The same compare and set the refresh rotation uses, for the same reason: two
        requests with one code must not both receive a token.
        """
        moment = _moment(now)
        digest = token_hash(code)

        def work(conn: sqlite3.Connection) -> AuthCodeRow | None:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "UPDATE auth_codes SET used_at = ? "
                "WHERE code_hash = ? AND used_at IS NULL AND expires_at > ?",
                (moment, digest, moment),
            )
            if cursor.rowcount != 1:
                conn.execute("COMMIT")
                return None
            row = conn.execute(
                "SELECT auth_id, redirect_uri, redirect_uri_explicit, code_challenge, resource, "
                "expires_at FROM auth_codes WHERE code_hash = ?",
                (digest,),
            ).fetchone()
            conn.execute("COMMIT")
            return _auth_code_row(row)

        return await self._transaction(work)

    # --- access tokens --------------------------------------------------------------

    async def create_access_token(
        self,
        token: str,
        *,
        auth_id: str,
        family_id: str,
        scopes: str,
        resource: str,
        now: int | None = None,
    ) -> None:
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            conn.execute(
                "INSERT INTO access_tokens (token_hash, auth_id, family_id, scopes, resource, "
                "expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    token_hash(token),
                    auth_id,
                    family_id,
                    scopes,
                    resource,
                    moment + ACCESS_TOKEN_TTL,
                ),
            )

        await self._write(work)

    async def load_access_token(
        self, token: str, *, now: int | None = None
    ) -> AccessTokenRow | None:
        """A token that is valid right now, or ``None``. There is no third answer.

        Expired, revoked and issued under a revoked authorization are one case for the
        verifier, and the join is what makes a revoked connection take effect immediately
        instead of at the next sweep (SC 4, D-37).
        """
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> AccessTokenRow | None:
            row = conn.execute(
                "SELECT t.auth_id, t.family_id, a.nc_user, t.scopes, t.resource, t.expires_at "
                "FROM access_tokens AS t JOIN authorizations AS a ON a.auth_id = t.auth_id "
                "WHERE t.token_hash = ? AND t.revoked_at IS NULL AND t.expires_at > ? "
                "AND a.revoked_at IS NULL",
                (token_hash(token), moment),
            ).fetchone()
            if row is None:
                return None
            return AccessTokenRow(
                auth_id=row[0],
                family_id=row[1],
                nc_user=row[2],
                scopes=row[3],
                resource=row[4],
                expires_at=row[5],
            )

        return await self._read(work)

    # --- refresh tokens -------------------------------------------------------------

    async def create_refresh_token(
        self, token: str, *, auth_id: str, family_id: str, now: int | None = None
    ) -> None:
        """Open a new family. Every later token of it comes out of a redemption."""
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            _insert_refresh_token(conn, token_hash(token), auth_id, family_id, moment)

        await self._write(work)

    async def load_refresh_token(self, token: str) -> RefreshTokenRow | None:
        def work(conn: sqlite3.Connection) -> RefreshTokenRow | None:
            row = conn.execute(
                "SELECT auth_id, family_id, state, successor, issued_at, used_at, expires_at "
                "FROM refresh_tokens WHERE token_hash = ?",
                (token_hash(token),),
            ).fetchone()
            if row is None:
                return None
            return RefreshTokenRow(
                auth_id=row[0],
                family_id=row[1],
                state=_checked_state(row[2]),
                successor=row[3],
                issued_at=row[4],
                used_at=row[5],
                expires_at=row[6],
            )

        return await self._read(work)

    async def redeem_refresh_token(
        self, token: str, *, successor: str, now: int | None = None
    ) -> RefreshRedemption:
        """Rotate this token, atomically, and say precisely what happened.

        One ``UPDATE`` inside ``BEGIN IMMEDIATE`` is the whole race protection: the write
        lock is taken before the row is read, so of two simultaneous callers exactly one
        changes a row. Zero changed rows is never a success; the row is then read to tell
        unknown, expired and already used apart, because plan 03-07 kills the family for
        the third case and answers a plain ``invalid_grant`` for the first two.

        The successor is inserted in the same transaction. A rotation that changed the old
        row but died before writing the new one would leave a user with no valid token at
        all, which is the reliability half of the owner directive.
        """
        moment = _moment(now)
        digest = token_hash(token)
        successor_digest = token_hash(successor)

        def work(conn: sqlite3.Connection) -> RefreshRedemption:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "UPDATE refresh_tokens SET state = ?, used_at = ?, successor = ? "
                "WHERE token_hash = ? AND state = ? AND expires_at > ?",
                (STATE_USED, moment, successor_digest, digest, STATE_ACTIVE, moment),
            )
            if cursor.rowcount == 1:
                row = conn.execute(
                    "SELECT auth_id, family_id FROM refresh_tokens WHERE token_hash = ?",
                    (digest,),
                ).fetchone()
                _insert_refresh_token(conn, successor_digest, row[0], row[1], moment)
                conn.execute("COMMIT")
                return RefreshRedemption(outcome=REDEEM_OK, auth_id=row[0], family_id=row[1])

            row = conn.execute(
                "SELECT auth_id, family_id, state, successor, used_at, expires_at "
                "FROM refresh_tokens WHERE token_hash = ?",
                (digest,),
            ).fetchone()
            conn.execute("COMMIT")
            if row is None:
                return RefreshRedemption(outcome=REDEEM_UNKNOWN)
            state = _checked_state(row[2])
            if state == STATE_ACTIVE:
                # The only way an active row does not match the update above.
                return RefreshRedemption(outcome=REDEEM_EXPIRED, auth_id=row[0], family_id=row[1])
            return RefreshRedemption(
                outcome=REDEEM_REUSED,
                auth_id=row[0],
                family_id=row[1],
                used_at=row[4],
                successor=row[3],
            )

        return await self._transaction(work)

    async def revoke_family(self, family_id: str, *, now: int | None = None) -> None:
        """End a whole token family in one transaction (reuse detection, SC 4).

        The refresh tokens carry a state and the access tokens carry a revocation time;
        that asymmetry is the schema of 03-RESEARCH.md and not an oversight, because only
        the refresh tokens have a state machine to be in.
        """
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE refresh_tokens SET state = ? WHERE family_id = ? AND state != ?",
                (STATE_REVOKED, family_id, STATE_REVOKED),
            )
            conn.execute(
                "UPDATE access_tokens SET revoked_at = ? WHERE family_id = ? "
                "AND revoked_at IS NULL",
                (moment, family_id),
            )
            conn.execute("COMMIT")

        await self._transaction(work)

    # --- housekeeping ---------------------------------------------------------------

    async def purge_expired(self, *, now: int | None = None) -> None:
        """Remove what has run out, including registrations nobody ever used.

        Called at startup and opportunistically from the client lookup of plan 03-06. The
        expired rows of the four short lived tables are already removed by every write, so
        what this adds is the client policy, which is kept out of the write path because
        deleting a client deletes its authorizations through the cascade.
        """
        moment = _moment(now)

        def work(conn: sqlite3.Connection) -> None:
            _purge_expired_rows(conn, moment)
            conn.execute(
                "DELETE FROM clients WHERE last_used_at IS NULL AND registered_at < ?",
                (moment - UNUSED_CLIENT_TTL,),
            )
            conn.execute(
                "DELETE FROM clients WHERE last_used_at IS NOT NULL AND last_used_at < ?",
                (moment - IDLE_CLIENT_TTL,),
            )

        await self._write(work)

    # --- the plumbing ---------------------------------------------------------------

    async def _read[T](self, work: Work[T]) -> T:
        """A statement without a transaction of its own, in a worker thread."""
        return await asyncio.to_thread(self._call, work, False)

    async def _write[T](self, work: Work[T]) -> T:
        """Statements that are committed together when ``work`` returns."""
        return await asyncio.to_thread(self._call, work, True)

    async def _transaction[T](self, work: Work[T]) -> T:
        """``work`` runs its own ``BEGIN IMMEDIATE`` and its own ``COMMIT``."""
        return await asyncio.to_thread(self._call, work, False)

    def _call[T](self, work: Work[T], commit: bool) -> T:
        conn = _connect(self._path)
        try:
            result = work(conn)
            if commit:
                conn.commit()
            return result
        finally:
            conn.close()


def store_opener(env: Mapping[str, str] | None = None) -> Callable[[], Awaitable["OAuthStore"]]:
    """One store per application, opened at its first use and swept when it opens.

    The store cannot be built when the routes are: the data key comes from Nextcloud over
    HTTP, which needs a running event loop, and a deployment that is not complete has to
    end in a page rather than in a failed import. So the callers get a function, and the
    first request that needs the store pays for opening it.

    The first open is also where :meth:`OAuthStore.purge_expired` runs. This project has no
    cron and no scheduler, so the sweep that removes what ran out hangs on the first use of
    the store and on every write after that (T-03-17).

    The cache lives in this closure and not in a module global, for the reason D-20 gives:
    a dictionary that outlives a request is one refactor away from being a session store.
    Two applications in one process, which is what every test builds, get one store each
    unless the caller passes the same opener to both.
    """
    opened: dict[str, OAuthStore] = {}
    lock = asyncio.Lock()

    async def open_once() -> OAuthStore:
        ready = opened.get("store")
        if ready is not None:
            return ready
        async with lock:
            ready = opened.get("store")
            if ready is None:
                # The key first: it is the one step that can fail with a named error, and
                # it fails before anything creates a directory.
                key = await crypto.data_key(env)
                ready = OAuthStore(config.persistent_storage(env) / STORE_FILENAME, key)
                await ready.purge_expired()
                opened["store"] = ready
            return ready

    return open_once


def _connect(path: Path) -> sqlite3.Connection:
    """One connection with the three pragmas, and the schema if the file is new.

    ``isolation_level=None`` turns off the implicit transaction handling of the standard
    library, which is what makes an explicit ``BEGIN IMMEDIATE`` mean what it says.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, timeout=_BUSY_TIMEOUT_SECONDS)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    conn.executescript(SCHEMA)
    _add_missing_columns(conn)
    return conn


def _add_missing_columns(conn: sqlite3.Connection) -> None:
    """Bring a file written by an earlier build up to the schema above.

    ``CREATE TABLE IF NOT EXISTS`` does nothing to a table that already exists, so a store
    file from a development build before plan 03-06 would keep an ``auth_codes`` table
    without ``redirect_uri_explicit`` and fail on the first insert. One ``ALTER TABLE`` with
    the same default as the schema is the whole migration, and it is idempotent because it
    asks first. Nothing here rewrites a row: a column that is added with a default is what
    every existing code carried anyway, an authorization request that named its return
    address.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(auth_codes)")}
    if "redirect_uri_explicit" not in columns:
        conn.execute(
            "ALTER TABLE auth_codes ADD COLUMN redirect_uri_explicit INTEGER NOT NULL DEFAULT 1"
        )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(authorizations)")}
    if "cleanup_at" not in columns:
        conn.execute("ALTER TABLE authorizations ADD COLUMN cleanup_at INTEGER")


def _auth_code_row(row: tuple[Any, ...]) -> AuthCodeRow:
    """One shape for the two places that read a code, so they cannot drift apart."""
    return AuthCodeRow(
        auth_id=row[0],
        redirect_uri=row[1],
        redirect_uri_explicit=bool(row[2]),
        code_challenge=row[3],
        resource=row[4],
        expires_at=row[5],
    )


#: How long the loser of a lock waits for the winner. Long enough for a transaction that
#: writes two rows, short enough that a wedged process answers instead of hanging.
_BUSY_TIMEOUT_MS = 5000
_BUSY_TIMEOUT_SECONDS = _BUSY_TIMEOUT_MS / 1000


def _insert_refresh_token(
    conn: sqlite3.Connection, digest: str, auth_id: str, family_id: str, moment: int
) -> None:
    conn.execute(
        "INSERT INTO refresh_tokens (token_hash, auth_id, family_id, state, issued_at, "
        "expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (digest, auth_id, family_id, STATE_ACTIVE, moment, moment + REFRESH_TOKEN_TTL),
    )


def _purge_expired_rows(conn: sqlite3.Connection, moment: int) -> None:
    """Drop what has run out. Opportunistic, so this project needs no cron (T-03-17)."""
    conn.execute("DELETE FROM flows WHERE expires_at <= ?", (moment,))
    conn.execute("DELETE FROM auth_codes WHERE expires_at <= ?", (moment,))
    conn.execute("DELETE FROM refresh_tokens WHERE expires_at <= ?", (moment,))
    conn.execute("DELETE FROM access_tokens WHERE expires_at <= ?", (moment,))


def _checked_state(value: str) -> str:
    """Return the state, or refuse to guess what an unknown one was supposed to mean.

    No default branch, the rule of ``nextcloud/credentials.py``: a value this code does not
    know must not quietly count as ``active``, because that is the one reading that hands
    out a token.
    """
    if value not in STATES:
        raise ValueError(f"unknown refresh token state {value!r}, expected one of {STATES}")
    return value


def _moment(now: int | None) -> int:
    """Whole seconds, and a parameter so a test can place a row in the past."""
    return int(time.time()) if now is None else int(now)
