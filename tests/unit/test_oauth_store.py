"""The persistence of the phase: every row that survives a restart, and what it costs.

Threats covered here: T-03-10 (the store file leaves the volume), T-03-11 (a plaintext
token in the database), T-03-13 (two winners of one refresh rotation) and T-03-17 (tables
that grow without a bound).

Every check runs against a real SQLite file in ``tmp_path``, because the guarantees under
test are the guarantees of the file: atomicity across threads, and content that is useless
to whoever steals it.
"""

import asyncio
import inspect
import sqlite3
import time
from pathlib import Path

import pytest

from mcp_connector.oauth import crypto, store

KEY = bytes(range(32))
OTHER_KEY = bytes(range(32, 64))

CLIENT_ID = "client-4711"
AUTH_ID = "auth-0001"
FAMILY = "family-0001"
NC_USER = "alice"
OTHER_USER = "bob"
SCOPES = "nextcloud"
RESOURCE = "https://cloud.example.com/exapps/mcp_connector/mcp"
REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

APP_PASSWORD = "app-password-of-alice-xyz"
POLL_TOKEN = "poll-token-of-the-login-flow"
REFRESH_TOKEN = "refresh-token-plain-value"
SUCCESSOR_TOKEN = "successor-token-plain-value"
ACCESS_TOKEN = "access-token-plain-value"
AUTH_CODE = "authorization-code-plain-value"


def open_store(tmp_path: Path, key: bytes = KEY) -> store.OAuthStore:
    return store.OAuthStore(tmp_path / store.STORE_FILENAME, key)


async def with_client(subject: store.OAuthStore, *, now: int | None = None) -> None:
    await subject.save_client(CLIENT_ID, metadata_json='{"client_id": "client-4711"}', now=now)


async def with_authorization(subject: store.OAuthStore, *, now: int | None = None) -> None:
    await with_client(subject, now=now)
    await subject.create_authorization(
        AUTH_ID,
        client_id=CLIENT_ID,
        nc_user=NC_USER,
        app_password=APP_PASSWORD,
        scopes=SCOPES,
        resource=RESOURCE,
        now=now,
    )


async def with_three_connections(subject: store.OAuthStore) -> None:
    """Two connections of one account and one of another, with a known order in time."""
    await with_client(subject)
    for auth_id, nc_user, moment in (
        ("auth-older", NC_USER, 1_000),
        ("auth-newer", NC_USER, 2_000),
        ("auth-of-bob", OTHER_USER, 3_000),
    ):
        await subject.create_authorization(
            auth_id,
            client_id=CLIENT_ID,
            nc_user=nc_user,
            app_password=APP_PASSWORD,
            scopes=SCOPES,
            resource=RESOURCE,
            now=moment,
        )


#: Every table of the schema, in the order the wipe of plan 05-06 empties them: children
#: before parents, and ``user_access`` last because it hangs on no cascade.
SCHEMA_TABLES = (
    "access_tokens",
    "refresh_tokens",
    "auth_codes",
    "flows",
    "authorizations",
    "clients",
    "user_access",
)


async def with_every_table_filled(subject: store.OAuthStore) -> None:
    """One row in each of the seven tables, which is what the purge has to leave empty."""
    await with_authorization(subject)
    await subject.create_flow(
        "flow-0001",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        redirect_uri_explicit=True,
        code_challenge=CHALLENGE,
        state=None,
        scopes=SCOPES,
        resource=RESOURCE,
        poll_token=POLL_TOKEN,
    )
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
    )
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )
    await subject.set_access(NC_USER, disabled=True)


def counts(tmp_path: Path) -> dict[str, int]:
    """The row count of every table, read out of the file itself."""
    return {
        table: query(tmp_path, f"SELECT COUNT(*) FROM {table}")[0][0] for table in SCHEMA_TABLES
    }


def all_bytes(tmp_path: Path) -> bytes:
    """Every byte the store wrote, including the write ahead log beside the database."""
    return b"".join(path.read_bytes() for path in sorted(tmp_path.iterdir()) if path.is_file())


def query(tmp_path: Path, sql: str, params: tuple = ()) -> list[tuple]:
    """Read the file behind the store's back; the connection is closed, not just committed."""
    conn = sqlite3.connect(tmp_path / store.STORE_FILENAME)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def modify(tmp_path: Path, sql: str, params: tuple = ()) -> None:
    """Write behind the store's back, which is how a corrupted row gets into a test."""
    conn = sqlite3.connect(tmp_path / store.STORE_FILENAME)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# --- the file itself ----------------------------------------------------------------


@pytest.mark.anyio
async def test_the_schema_is_created_on_first_use_and_a_second_open_changes_nothing(
    tmp_path: Path,
) -> None:
    first = open_store(tmp_path)
    await with_authorization(first)

    second = open_store(tmp_path)
    await second.save_client("another-client", metadata_json="{}")

    tables = {
        row[0] for row in query(tmp_path, "SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert tables >= {
        "clients",
        "flows",
        "authorizations",
        "auth_codes",
        "refresh_tokens",
        "access_tokens",
        "user_access",
    }


@pytest.mark.anyio
async def test_the_connection_pragmas_are_the_ones_the_rotation_depends_on(tmp_path: Path) -> None:
    """WAL for a reader beside a writer, foreign keys for the cascade, a busy timeout so
    the second of two parallel redemptions waits instead of failing with 'database locked'."""
    subject = open_store(tmp_path)
    await with_client(subject)

    assert query(tmp_path, "PRAGMA journal_mode")[0][0].lower() == "wal"

    source = inspect.getsource(store)
    assert "foreign_keys" in source
    assert "busy_timeout" in source


@pytest.mark.anyio
async def test_the_data_survives_closing_and_reopening_the_file(tmp_path: Path) -> None:
    """The restart proof: a new store object on the same file reads what the old one wrote."""
    first = open_store(tmp_path)
    await with_authorization(first)
    await first.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)

    second = open_store(tmp_path)
    assert await second.app_password(AUTH_ID) == APP_PASSWORD
    row = await second.load_authorization(AUTH_ID)
    assert row is not None
    assert row.nc_user == NC_USER
    refresh = await second.load_refresh_token(REFRESH_TOKEN)
    assert refresh is not None
    assert refresh.state == store.STATE_ACTIVE


@pytest.mark.anyio
async def test_no_plaintext_secret_is_anywhere_in_the_files(tmp_path: Path) -> None:
    """T-03-10 and T-03-11: the whole point of the encryption and of the hashing."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_flow(
        "flow-0001",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        redirect_uri_explicit=True,
        code_challenge=CHALLENGE,
        state="opaque-client-state",
        scopes=SCOPES,
        resource=RESOURCE,
        poll_token=POLL_TOKEN,
    )
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
    )
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )

    written = all_bytes(tmp_path)
    for secret in (APP_PASSWORD, POLL_TOKEN, REFRESH_TOKEN, ACCESS_TOKEN, AUTH_CODE):
        assert secret.encode() not in written, f"{secret!r} is readable in the store files"


@pytest.mark.anyio
async def test_a_token_is_stored_as_its_hash_and_found_by_the_plain_value(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )

    (stored,) = query(tmp_path, "SELECT token_hash FROM access_tokens")[0]
    assert stored == store.token_hash(ACCESS_TOKEN)
    assert len(stored) == 64
    assert await subject.load_access_token(ACCESS_TOKEN) is not None


@pytest.mark.anyio
async def test_the_store_object_never_shows_its_key(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    assert KEY.hex() not in repr(subject)
    assert "***" in repr(subject)


# --- authorizations and the one app password --------------------------------------


@pytest.mark.anyio
async def test_the_app_password_comes_back_only_through_the_named_decryption(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)

    row = await subject.load_authorization(AUTH_ID)
    assert row is not None
    assert APP_PASSWORD not in repr(row)
    assert not [name for name in dir(row) if "password" in name]
    assert await subject.app_password(AUTH_ID) == APP_PASSWORD


@pytest.mark.anyio
async def test_the_app_password_is_bound_to_its_own_row(tmp_path: Path) -> None:
    """T-03-12: aad is the auth id, so a ciphertext copied into another row is refused."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_authorization(
        "auth-0002",
        client_id=CLIENT_ID,
        nc_user="bob",
        app_password="app-password-of-bob",
        scopes=SCOPES,
        resource=RESOURCE,
    )

    (blob,) = query(
        tmp_path, "SELECT app_password_enc FROM authorizations WHERE auth_id = ?", (AUTH_ID,)
    )[0]
    modify(
        tmp_path,
        "UPDATE authorizations SET app_password_enc = ? WHERE auth_id = ?",
        (blob, "auth-0002"),
    )

    with pytest.raises(crypto.DecryptionRejected):
        await subject.app_password("auth-0002")


@pytest.mark.anyio
async def test_a_store_with_the_wrong_key_reads_nothing(tmp_path: Path) -> None:
    await with_authorization(open_store(tmp_path))

    with pytest.raises(crypto.DecryptionRejected):
        await open_store(tmp_path, OTHER_KEY).app_password(AUTH_ID)


@pytest.mark.anyio
async def test_an_unknown_authorization_is_none_and_not_an_error(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    assert await subject.load_authorization("auth-does-not-exist") is None
    assert await subject.app_password("auth-does-not-exist") is None


@pytest.mark.anyio
async def test_revoking_an_authorization_is_visible_and_idempotent(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)

    await subject.revoke_authorization(AUTH_ID)
    await subject.revoke_authorization(AUTH_ID)

    row = await subject.load_authorization(AUTH_ID)
    assert row is not None
    assert row.revoked_at


# --- the connections of one account (EXAPP-02) -------------------------------------


@pytest.mark.anyio
async def test_the_connections_of_one_account_are_listed_newest_first(tmp_path: Path) -> None:
    """S5 lists an account's own connections, newest first, and nobody else's."""
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    rows = await subject.authorizations_of_user(NC_USER)

    assert [row.auth_id for row in rows] == ["auth-newer", "auth-older"]
    assert {row.nc_user for row in rows} == {NC_USER}


@pytest.mark.anyio
async def test_a_disconnected_connection_leaves_the_list_of_its_account(tmp_path: Path) -> None:
    """Revoked is gone as far as this page is concerned, and only for this account."""
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    await subject.revoke_authorization("auth-newer")

    assert [row.auth_id for row in await subject.authorizations_of_user(NC_USER)] == ["auth-older"]
    assert [row.auth_id for row in await subject.authorizations_of_user(OTHER_USER)] == [
        "auth-of-bob"
    ]


@pytest.mark.anyio
async def test_an_unknown_or_empty_account_has_an_empty_connection_list(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    assert await subject.authorizations_of_user("carol") == []
    assert await subject.authorizations_of_user("") == []


# --- the per account access switch (EXAPP-02, D-47 to D-50) ------------------------


@pytest.mark.anyio
async def test_an_account_without_a_row_has_access(tmp_path: Path) -> None:
    """D-50: on is the default, and being on costs no row, no write and no migration."""
    subject = open_store(tmp_path)

    assert await subject.access_disabled(NC_USER) is False


@pytest.mark.anyio
async def test_pausing_an_account_is_visible_and_keeps_the_first_moment(tmp_path: Path) -> None:
    """Idempotent in the pausing direction: the moment the user pulled the brake stands."""
    subject = open_store(tmp_path)

    await subject.set_access(NC_USER, disabled=True, now=1_000)
    await subject.set_access(NC_USER, disabled=True, now=2_000)

    assert await subject.access_disabled(NC_USER) is True
    assert query(tmp_path, "SELECT nc_user, disabled_at FROM user_access") == [(NC_USER, 1_000)]


@pytest.mark.anyio
async def test_resuming_an_account_removes_the_row_and_is_a_no_op_without_one(
    tmp_path: Path,
) -> None:
    """Resume deletes the row instead of writing a zero into it: the default state and the
    resumed state are then the same truth, and no reader can tell them apart wrongly."""
    subject = open_store(tmp_path)
    await subject.set_access(NC_USER, disabled=True)

    await subject.set_access(NC_USER, disabled=False)
    await subject.set_access(NC_USER, disabled=False)

    assert await subject.access_disabled(NC_USER) is False
    assert query(tmp_path, "SELECT nc_user FROM user_access") == []


@pytest.mark.anyio
async def test_the_switch_of_one_account_leaves_every_other_account_alone(tmp_path: Path) -> None:
    subject = open_store(tmp_path)

    await subject.set_access(NC_USER, disabled=True)

    assert await subject.access_disabled(NC_USER) is True
    assert await subject.access_disabled(OTHER_USER) is False


@pytest.mark.anyio
async def test_pausing_an_account_disconnects_nothing(tmp_path: Path) -> None:
    """D-46: the switch blocks, it does not revoke, so every row stays as it was."""
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    await subject.set_access(NC_USER, disabled=True)

    rows = await subject.authorizations_of_user(NC_USER)
    assert [row.auth_id for row in rows] == ["auth-newer", "auth-older"]
    assert all(row.revoked_at is None for row in rows)


@pytest.mark.anyio
async def test_an_empty_account_id_is_never_a_switch(tmp_path: Path) -> None:
    """The app context has no switch (pitfall 10). Reading it is False without touching the
    file, and writing it is a programming error refused before anything is opened."""
    subject = open_store(tmp_path)

    assert await subject.access_disabled("") is False
    assert await subject.access_disabled("   ") is False
    for blank in ("", "   "):
        with pytest.raises(ValueError, match="nc_user"):
            await subject.set_access(blank, disabled=True)
        with pytest.raises(ValueError, match="nc_user"):
            await subject.set_access(blank, disabled=False)

    assert not (tmp_path / store.STORE_FILENAME).exists()


# --- clients -----------------------------------------------------------------------


@pytest.mark.anyio
async def test_a_client_is_written_read_stamped_and_deleted(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_client(subject)

    row = await subject.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is True
    assert row.last_used_at is None
    assert row.registered_at

    await subject.touch_client(CLIENT_ID)
    stamped = await subject.load_client(CLIENT_ID)
    assert stamped is not None
    assert stamped.last_used_at is not None

    await subject.delete_client(CLIENT_ID)
    assert await subject.load_client(CLIENT_ID) is None


@pytest.mark.anyio
async def test_a_client_secret_is_stored_as_a_hash_and_masked(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await subject.save_client(
        CLIENT_ID, metadata_json="{}", secret_hash=store.token_hash("the-secret"), allowed=False
    )

    row = await subject.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is False
    assert row.client_secret_hash == store.token_hash("the-secret")
    assert store.token_hash("the-secret") not in repr(row)
    assert "***" in repr(row)


@pytest.mark.anyio
async def test_deleting_a_client_takes_its_authorizations_with_it(tmp_path: Path) -> None:
    """The cascade of the schema, which only works with foreign keys switched on."""
    subject = open_store(tmp_path)
    await with_authorization(subject)

    await subject.delete_client(CLIENT_ID)

    assert await subject.load_authorization(AUTH_ID) is None


# --- flows and authorization codes --------------------------------------------------


@pytest.mark.anyio
async def test_a_flow_round_trips_including_its_encrypted_poll_token(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_client(subject)
    await subject.create_flow(
        "flow-0001",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        redirect_uri_explicit=True,
        code_challenge=CHALLENGE,
        state="opaque-client-state",
        scopes=SCOPES,
        resource=RESOURCE,
        poll_token=POLL_TOKEN,
    )

    row = await subject.load_flow("flow-0001")
    assert row is not None
    assert row.client_id == CLIENT_ID
    assert row.redirect_uri == REDIRECT_URI
    assert row.redirect_uri_explicit is True
    assert row.code_challenge == CHALLENGE
    assert row.state == "opaque-client-state"
    assert row.poll_token == POLL_TOKEN
    assert POLL_TOKEN not in repr(row)

    await subject.delete_flow("flow-0001")
    assert await subject.load_flow("flow-0001") is None


@pytest.mark.anyio
async def test_an_expired_flow_is_gone_instead_of_usable(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_client(subject)
    await subject.create_flow(
        "flow-old",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        redirect_uri_explicit=True,
        code_challenge=CHALLENGE,
        state=None,
        scopes=SCOPES,
        resource=RESOURCE,
        poll_token=POLL_TOKEN,
        now=int(time.time()) - store.FLOW_TTL - 1,
    )

    assert await subject.load_flow("flow-old") is None


@pytest.mark.anyio
async def test_an_authorization_code_can_be_redeemed_exactly_once(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
    )

    first = await subject.redeem_auth_code(AUTH_CODE)
    assert first is not None
    assert first.auth_id == AUTH_ID
    assert first.redirect_uri == REDIRECT_URI
    assert first.code_challenge == CHALLENGE
    assert first.resource == RESOURCE

    assert await subject.redeem_auth_code(AUTH_CODE) is None


@pytest.mark.anyio
async def test_an_expired_or_unknown_authorization_code_is_never_redeemed(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
        now=int(time.time()) - store.AUTH_CODE_TTL - 1,
    )

    assert await subject.redeem_auth_code(AUTH_CODE) is None
    assert await subject.redeem_auth_code("a-code-nobody-issued") is None


@pytest.mark.anyio
async def test_two_parallel_redemptions_of_one_code_produce_one_winner(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
    )

    results = await asyncio.gather(
        subject.redeem_auth_code(AUTH_CODE), subject.redeem_auth_code(AUTH_CODE)
    )

    assert sum(1 for result in results if result is not None) == 1


# --- access tokens ------------------------------------------------------------------


@pytest.mark.anyio
async def test_an_access_token_is_found_until_it_expires_or_is_revoked(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )

    row = await subject.load_access_token(ACCESS_TOKEN)
    assert row is not None
    assert row.auth_id == AUTH_ID
    assert row.family_id == FAMILY
    assert row.scopes == SCOPES
    assert row.resource == RESOURCE
    assert row.nc_user == NC_USER, "the verifier needs the user without a second query"

    assert await subject.load_access_token(ACCESS_TOKEN, now=int(time.time()) + 2 * 3600) is None
    assert await subject.load_access_token("a-token-nobody-issued") is None


@pytest.mark.anyio
async def test_a_token_of_a_revoked_authorization_is_not_valid(tmp_path: Path) -> None:
    """Fail closed, D-37: revoking the connection must not need a second sweep."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )

    await subject.revoke_authorization(AUTH_ID)

    assert await subject.load_access_token(ACCESS_TOKEN) is None


# --- the refresh rotation, which is the reason this is SQLite ----------------------


@pytest.mark.anyio
async def test_a_refresh_token_is_redeemed_exactly_once(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)

    first = await subject.redeem_refresh_token(REFRESH_TOKEN, successor=SUCCESSOR_TOKEN)
    assert first.outcome == store.REDEEM_OK
    assert first.auth_id == AUTH_ID
    assert first.family_id == FAMILY

    successor = await subject.load_refresh_token(SUCCESSOR_TOKEN)
    assert successor is not None
    assert successor.state == store.STATE_ACTIVE
    assert successor.family_id == FAMILY


@pytest.mark.anyio
async def test_a_replayed_refresh_token_reports_the_reuse_with_the_data_to_decide(
    tmp_path: Path,
) -> None:
    """D-41: the grace window is decided by the caller, so the reuse carries used_at and
    the successor it already handed out."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)
    await subject.redeem_refresh_token(REFRESH_TOKEN, successor=SUCCESSOR_TOKEN)

    replay = await subject.redeem_refresh_token(REFRESH_TOKEN, successor="a-third-token")

    assert replay.outcome == store.REDEEM_REUSED
    assert replay.family_id == FAMILY
    assert replay.used_at
    assert replay.successor == store.token_hash(SUCCESSOR_TOKEN)
    assert await subject.load_refresh_token("a-third-token") is None, "no second branch"


@pytest.mark.anyio
async def test_an_unknown_or_expired_refresh_token_is_told_apart_from_a_replay(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(
        REFRESH_TOKEN,
        auth_id=AUTH_ID,
        family_id=FAMILY,
        now=int(time.time()) - store.REFRESH_TOKEN_TTL - 1,
    )

    expired = await subject.redeem_refresh_token(REFRESH_TOKEN, successor=SUCCESSOR_TOKEN)
    unknown = await subject.redeem_refresh_token("nobody-issued-this", successor=SUCCESSOR_TOKEN)

    assert expired.outcome == store.REDEEM_EXPIRED
    assert unknown.outcome == store.REDEEM_UNKNOWN


@pytest.mark.anyio
async def test_two_parallel_redemptions_produce_exactly_one_winner(tmp_path: Path) -> None:
    """T-03-13, pitfall 10: Claude refreshes reactively and proactively, so this happens."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)

    first, second = await asyncio.gather(
        subject.redeem_refresh_token(REFRESH_TOKEN, successor="successor-a"),
        subject.redeem_refresh_token(REFRESH_TOKEN, successor="successor-b"),
    )

    outcomes = sorted([first.outcome, second.outcome])
    assert outcomes == sorted([store.REDEEM_OK, store.REDEEM_REUSED])
    survivors = [
        name
        for name in ("successor-a", "successor-b")
        if await subject.load_refresh_token(name) is not None
    ]
    assert len(survivors) == 1, "two branches of one family is exactly what must not happen"


@pytest.mark.anyio
async def test_revoking_a_family_kills_every_token_of_it_in_one_step(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)
    await subject.create_access_token(
        ACCESS_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, scopes=SCOPES, resource=RESOURCE
    )
    await subject.create_refresh_token("other-family-token", auth_id=AUTH_ID, family_id="family-2")

    await subject.revoke_family(FAMILY)

    revoked = await subject.load_refresh_token(REFRESH_TOKEN)
    assert revoked is not None
    assert revoked.state == store.STATE_REVOKED
    assert await subject.load_access_token(ACCESS_TOKEN) is None
    assert (
        await subject.redeem_refresh_token(REFRESH_TOKEN, successor="x")
    ).outcome == store.REDEEM_REUSED
    other = await subject.load_refresh_token("other-family-token")
    assert other is not None
    assert other.state == store.STATE_ACTIVE, "the other family of the same user is untouched"


@pytest.mark.anyio
async def test_an_unknown_state_value_raises_instead_of_counting_as_active(
    tmp_path: Path,
) -> None:
    """The credentials.py rule: no default branch, because a typo must not authenticate."""
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.create_refresh_token(REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY)

    modify(
        tmp_path,
        "UPDATE refresh_tokens SET state = ? WHERE token_hash = ?",
        ("aktiv", store.token_hash(REFRESH_TOKEN)),
    )

    with pytest.raises(ValueError, match="aktiv"):
        await subject.load_refresh_token(REFRESH_TOKEN)
    with pytest.raises(ValueError, match="aktiv"):
        await subject.redeem_refresh_token(REFRESH_TOKEN, successor=SUCCESSOR_TOKEN)


# --- opportunistic cleanup, no cron -------------------------------------------------


@pytest.mark.anyio
async def test_expired_rows_are_removed_when_the_store_is_used(tmp_path: Path) -> None:
    """T-03-17: unbounded tables are the denial of service nobody notices for months."""
    subject = open_store(tmp_path)
    long_ago = int(time.time()) - store.REFRESH_TOKEN_TTL - 3600
    await with_authorization(subject, now=long_ago)
    await subject.create_flow(
        "flow-old",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        redirect_uri_explicit=False,
        code_challenge=CHALLENGE,
        state=None,
        scopes=SCOPES,
        resource=RESOURCE,
        poll_token=POLL_TOKEN,
        now=long_ago,
    )
    await subject.create_auth_code(
        AUTH_CODE,
        auth_id=AUTH_ID,
        redirect_uri=REDIRECT_URI,
        code_challenge=CHALLENGE,
        resource=RESOURCE,
        now=long_ago,
    )
    await subject.create_refresh_token(
        REFRESH_TOKEN, auth_id=AUTH_ID, family_id=FAMILY, now=long_ago
    )
    await subject.create_access_token(
        ACCESS_TOKEN,
        auth_id=AUTH_ID,
        family_id=FAMILY,
        scopes=SCOPES,
        resource=RESOURCE,
        now=long_ago,
    )

    await subject.purge_expired()

    counts = {
        table: query(tmp_path, f"SELECT count(*) FROM {table}")[0][0]  # noqa: S608
        for table in ("flows", "auth_codes", "refresh_tokens", "access_tokens")
    }
    assert counts == {"flows": 0, "auth_codes": 0, "refresh_tokens": 0, "access_tokens": 0}


@pytest.mark.anyio
async def test_a_registration_nobody_ever_used_expires(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await subject.save_client(
        CLIENT_ID, metadata_json="{}", now=int(time.time()) - store.UNUSED_CLIENT_TTL - 1
    )
    await subject.save_client("fresh-client", metadata_json="{}")

    await subject.purge_expired()

    assert await subject.load_client(CLIENT_ID) is None
    assert await subject.load_client("fresh-client") is not None


@pytest.mark.anyio
async def test_a_client_that_went_quiet_for_a_season_keeps_its_row_while_it_has_connections(
    tmp_path: Path,
) -> None:
    """WR-04: this purge cannot hand a credential back, and deleting the client row takes
    the encrypted app password of every connection under it along through the cascade. So
    the row stays until somebody who can talk to Nextcloud has handed them back, and the
    client is listed for exactly that caller."""
    subject = open_store(tmp_path)
    long_ago = int(time.time()) - store.IDLE_CLIENT_TTL - 1
    await with_authorization(subject, now=long_ago)
    await subject.touch_client(CLIENT_ID, now=long_ago)

    await subject.purge_expired()

    assert await subject.load_client(CLIENT_ID) is not None
    assert await subject.load_authorization(AUTH_ID) is not None
    assert await subject.expired_clients(10) == [CLIENT_ID]


@pytest.mark.anyio
async def test_a_client_without_connections_still_expires_with_its_tokens(
    tmp_path: Path,
) -> None:
    """The other half: once the connections are gone the row goes on its own, which is what
    keeps the table from growing forever (T-03-44)."""
    subject = open_store(tmp_path)
    long_ago = int(time.time()) - store.IDLE_CLIENT_TTL - 1
    await with_authorization(subject, now=long_ago)
    await subject.touch_client(CLIENT_ID, now=long_ago)
    await subject.delete_authorization(AUTH_ID)

    await subject.purge_expired()

    assert await subject.load_client(CLIENT_ID) is None


@pytest.mark.anyio
async def test_the_connections_of_a_client_are_readable_before_it_is_deleted(
    tmp_path: Path,
) -> None:
    """WR-04: what the caller needs to hand the credentials back is the nc_user and the
    auth_id of every connection, and it has to be readable while the row still exists."""
    subject = open_store(tmp_path)
    await with_authorization(subject)

    rows = await subject.authorizations_of_client(CLIENT_ID, 10)

    assert [row.auth_id for row in rows] == [AUTH_ID]
    assert rows[0].nc_user == NC_USER
    assert await subject.authorizations_of_client("no-such-client", 10) == []


@pytest.mark.anyio
async def test_the_connections_of_a_client_are_uncapped_unless_a_limit_is_given(
    tmp_path: Path,
) -> None:
    """BL-01: a capped read in front of a cascading delete loses the rest of them silently.

    ``None`` travels as ``LIMIT -1``, which is SQLite's "no upper bound". Asserted here and
    not only in the provider, because the whole property of the caller rests on this
    spelling behaving that way.
    """
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    every = await subject.authorizations_of_client(CLIENT_ID)
    capped = await subject.authorizations_of_client(CLIENT_ID, 2)

    assert [row.auth_id for row in every] == ["auth-older", "auth-newer", "auth-of-bob"]
    assert len(capped) == 2, "a caller that asks for a page still gets exactly that page"


@pytest.mark.anyio
async def test_a_used_client_that_is_merely_older_than_a_day_stays(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    two_days = int(time.time()) - 2 * 24 * 3600
    await subject.save_client(CLIENT_ID, metadata_json="{}", now=two_days)
    await subject.touch_client(CLIENT_ID, now=two_days)

    await subject.purge_expired()

    assert await subject.load_client(CLIENT_ID) is not None


# --- the transaction _write promises (WR-05) -------------------------------------------


@pytest.mark.anyio
async def test_a_write_that_fails_halfway_leaves_nothing_behind(tmp_path: Path) -> None:
    """WR-05: the connection is opened with isolation_level=None, which is autocommit, so
    every statement of a body used to commit on its own and the commit at the end was a
    statement about nothing. A body that groups two writes has to get both or neither."""
    subject = open_store(tmp_path)
    await with_client(subject)

    def half(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE clients SET allowed = 0 WHERE client_id = ?",
            (CLIENT_ID,),
        )
        raise RuntimeError("the second half of this body never ran")

    with pytest.raises(RuntimeError):
        await subject._write(half)

    row = await subject.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is True, "the first statement of a failed body was rolled back"


@pytest.mark.anyio
async def test_a_write_that_returns_commits_every_statement_of_its_body(
    tmp_path: Path,
) -> None:
    """The other half of the same contract: a body that returns has written all of it, and
    the rows are there for the next connection and not only for this one."""
    subject = open_store(tmp_path)
    await with_client(subject)

    def both(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE clients SET allowed = 0 WHERE client_id = ?", (CLIENT_ID,))
        conn.execute("UPDATE clients SET last_used_at = ? WHERE client_id = ?", (4711, CLIENT_ID))

    await subject._write(both)

    row = await subject.load_client(CLIENT_ID)
    assert row is not None
    assert row.allowed is False
    assert row.last_used_at == 4711


# --- what the purge of plan 05-06 reads and empties ----------------------------------


@pytest.mark.anyio
async def test_all_authorizations_returns_every_row_oldest_first(tmp_path: Path) -> None:
    """No account, no client, no limit: the purge of an instance sees the whole table."""
    subject = open_store(tmp_path)
    await with_three_connections(subject)

    rows = await subject.all_authorizations()

    assert [row.auth_id for row in rows] == ["auth-older", "auth-newer", "auth-of-bob"]
    assert {row.nc_user for row in rows} == {NC_USER, OTHER_USER}


@pytest.mark.anyio
async def test_all_authorizations_carries_a_revoked_connection_too(tmp_path: Path) -> None:
    """The question of the purge is not "which connection lives".

    It is "which Nextcloud app password of this instance may still exist", and a revoked
    row answers yes to it: revoking marks our own record, while the credential itself only
    goes when Nextcloud is asked to delete it. ``authorizations_of_user`` filters exactly
    that row out, which is why it is the wrong model here, and the second half of this
    check is that counter proof.
    """
    subject = open_store(tmp_path)
    await with_three_connections(subject)
    await subject.revoke_authorization("auth-older", now=4_000)

    rows = await subject.all_authorizations()

    assert [row.auth_id for row in rows] == ["auth-older", "auth-newer", "auth-of-bob"]
    assert [row.auth_id for row in rows if row.revoked_at is not None] == ["auth-older"]
    live = {row.auth_id for row in await subject.authorizations_of_user(NC_USER)}
    assert "auth-older" not in live, "the filtered read would leave that credential behind"


@pytest.mark.anyio
async def test_all_authorizations_of_an_empty_store_is_an_empty_list(tmp_path: Path) -> None:
    assert await open_store(tmp_path).all_authorizations() == []


@pytest.mark.anyio
async def test_wipe_all_empties_every_table_of_the_schema(tmp_path: Path) -> None:
    """All seven, counted in the file and not through a reader of the store."""
    subject = open_store(tmp_path)
    await with_every_table_filled(subject)
    assert all(count > 0 for count in counts(tmp_path).values()), counts(tmp_path)

    await subject.wipe_all()

    assert counts(tmp_path) == dict.fromkeys(SCHEMA_TABLES, 0)


@pytest.mark.anyio
async def test_wipe_all_takes_the_access_switch_with_it(tmp_path: Path) -> None:
    """``user_access`` hangs on no cascade at all, so it needs a statement of its own.

    The middle step is the reason: deleting the client takes every authorization with it
    through the cascade and leaves the switch of that account exactly where it was.
    """
    subject = open_store(tmp_path)
    await with_authorization(subject)
    await subject.set_access(NC_USER, disabled=True)

    await subject.delete_client(CLIENT_ID)
    assert await subject.access_disabled(NC_USER) is True, "the cascade does not reach it"

    await subject.wipe_all()
    assert await subject.access_disabled(NC_USER) is False


@pytest.mark.anyio
async def test_the_store_keeps_working_on_the_same_file_after_a_wipe(tmp_path: Path) -> None:
    """Not a replacement for ``--rm-data``: the file and the schema stay usable.

    A running process has to write its next row without creating the file again, because
    the purge happens inside that process and answers a request afterwards.
    """
    subject = open_store(tmp_path)
    await with_every_table_filled(subject)

    await subject.wipe_all()
    await with_authorization(subject)

    row = await subject.load_authorization(AUTH_ID)
    assert row is not None
    assert await subject.app_password(AUTH_ID) == APP_PASSWORD
    tables = {
        name[0] for name in query(tmp_path, "SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert tables >= set(SCHEMA_TABLES), "the schema survived the wipe"


def test_the_wipe_is_one_write_and_names_every_table() -> None:
    """One transaction, and one statement per table rather than a table name in an f-string.

    The gate of ``tests/contract/test_no_destructive_calls.py`` matches ``DELETE FROM``
    literally, so a loop over a tuple of names would move these statements out of sight of
    the exemption that covers them.
    """
    source = inspect.getsource(store.OAuthStore.wipe_all)
    assert "self._write" in source
    for table in SCHEMA_TABLES:
        assert f"DELETE FROM {table}" in source, f"{table} is not emptied by name"


# --- source gates --------------------------------------------------------------------


def test_the_rotation_is_one_immediate_transaction() -> None:
    """Pitfall 10: a deferred transaction upgrades its lock too late to be atomic."""
    source = inspect.getsource(store)
    assert "BEGIN IMMEDIATE" in source
    assert "changes()" in source or "rowcount" in source


def test_the_store_holds_no_module_global_mutable_state() -> None:
    """The phase 1 rule: state lives in an object with a path, never in the module."""
    source = inspect.getsource(store)
    offenders = [
        line
        for line in source.splitlines()
        if line and not line[0].isspace() and (line.endswith("= {}") or line.endswith("= []"))
    ]
    assert offenders == []


def test_every_lifetime_is_a_named_constant() -> None:
    """No number of seconds at a call site, so a change is one line and a review is one
    diff (03-RESEARCH.md lifetimes, made binding by the plan)."""
    assert store.AUTH_CODE_TTL == 60
    assert store.ACCESS_TOKEN_TTL == 3600
    assert store.REFRESH_TOKEN_TTL == 30 * 24 * 3600
    assert store.FLOW_TTL == 1200
    assert store.VALIDATION_CACHE_TTL == 5
    assert store.ROTATION_GRACE == 10
    assert store.UNUSED_CLIENT_TTL == 24 * 3600
    assert store.IDLE_CLIENT_TTL == 90 * 24 * 3600
