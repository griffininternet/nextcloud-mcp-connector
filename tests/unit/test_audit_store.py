"""The store of the audit log: the file, the chain, and what one row may carry.

Threats covered here: T-18-03 (a row changed after the fact), T-18-05 (a store that grows
without a bound) and T-18-01 (a value in the log).

Every check runs against a real SQLite file in ``tmp_path``, because the properties under
test are properties of the file: two writers that meet on the same chain, pages that move to
the free list when rows go, and a digest that has to be reproducible from the row alone. A
mock of the connection would assert the mock.
"""

import asyncio
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from mcp_connector.audit import store

pytestmark = pytest.mark.anyio

ALICE = store.user_chain("alice")
BOB = store.user_chain("bob")

#: A file name of a user, the kind of value a parameter of ``files_read`` carries. It is
#: never handed to the store: no method here takes a parameter value, and the check below
#: looks for it in every column to say so out loud (D-06, AUDIT-01).
A_VALUE = "kuendigung-2026.md"


def open_store(tmp_path: Path) -> store.AuditStore:
    return store.AuditStore(tmp_path / store.AUDIT_FILENAME)


def rows(tmp_path: Path) -> list[tuple[Any, ...]]:
    """Every row of the table, read out of the file behind the store's back."""
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME)
    try:
        return list(conn.execute("SELECT * FROM entries ORDER BY seq"))
    finally:
        conn.close()


def pragma(tmp_path: Path, name: str) -> Any:
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME)
    try:
        return conn.execute(f"PRAGMA {name}").fetchone()[0]
    finally:
        conn.close()


def pages_times_size(tmp_path: Path) -> int:
    """The number that looks like the size of the store and is not (18-RESEARCH.md §8)."""
    return pragma(tmp_path, "page_count") * pragma(tmp_path, "page_size")


def fill(tmp_path: Path, count: int) -> None:
    """Write ``count`` rows with an own connection, in one transaction.

    The rows carry no chain worth checking: this helper exists for the size case only, and
    going through :meth:`AuditStore.append` for two thousand rows would open two thousand
    connections for a measurement that is about pages, not about hashes.
    """
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.executemany(
            "INSERT INTO entries (chain, kind, at, nc_user, tool, client_id, auth_id, "
            "client_name, outcome, params, prev_hash, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    f"u:user-{number % 7}",
                    store.KIND_CALL,
                    1_700_000_000 + number,
                    f"user-{number % 7}",
                    "files_search",
                    "client-4711",
                    f"auth-{number:06d}",
                    "A Client With A Name",
                    store.OUTCOME_OK,
                    '["query"]',
                    hashlib.sha256(f"prev-{number}".encode()).digest(),
                    hashlib.sha256(f"row-{number}".encode()).digest(),
                )
                for number in range(count)
            ],
        )
        conn.execute("COMMIT")
    finally:
        conn.close()


def drop_oldest(tmp_path: Path, count: int) -> None:
    """Remove rows with an own connection, the way a sweep of plan 18-04 will."""
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM entries WHERE seq <= ?", (count,))
        conn.execute("COMMIT")
    finally:
        conn.close()


def digest_of(row: tuple[Any, ...]) -> bytes:
    """Recompute the hash of a row from the row itself, as a check will have to."""
    canonical = row[: len(store.CANONICAL_FIELDS)]
    return hashlib.sha256(store._canonical(canonical) + row[-2]).digest()


# --- the file itself ------------------------------------------------------------------


async def test_a_fresh_file_carries_wal_incremental_vacuum_and_the_nineteen_columns(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.size()

    assert pragma(tmp_path, "journal_mode") == "wal"
    assert pragma(tmp_path, "auto_vacuum") == 2
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME)
    try:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(entries)")]
    finally:
        conn.close()
    assert columns == [
        "seq",
        "chain",
        "kind",
        "at",
        "actor",
        "nc_user",
        "tool",
        "client_id",
        "auth_id",
        "client_name",
        "outcome",
        "reason",
        "duration_ms",
        "params",
        "removed",
        "gap_chain",
        "gap_hash",
        "prev_hash",
        "hash",
    ]
    # The seventeen that are hashed are these nineteen without the two hashes themselves.
    assert list(store.CANONICAL_FIELDS) == columns[:-2]


# --- the chain ------------------------------------------------------------------------


async def test_the_first_row_of_a_chain_points_at_genesis_and_the_second_at_the_first(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.append(store.Entry(chain=ALICE, tool="files_search", nc_user="alice", at=1000))
    await subject.append(store.Entry(chain=ALICE, tool="notes_read", nc_user="alice", at=1001))

    first, second = rows(tmp_path)
    assert first[-2] == store.GENESIS
    assert len(store.GENESIS) == 32
    assert second[-2] == first[-1]


async def test_the_hash_of_a_row_can_be_recomputed_from_the_row(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await subject.append(
        store.Entry(
            chain=ALICE,
            tool="files_read",
            nc_user="alice",
            client_id="client-4711",
            outcome=store.OUTCOME_REJECTED,
            reason="no_permission",
            duration_ms=42,
            params=["path"],
            at=1000,
        )
    )
    await subject.append(store.Entry(chain=ALICE, tool="notes_read", nc_user="alice", at=1001))

    for row in rows(tmp_path):
        assert digest_of(row) == row[-1]


async def test_twenty_simultaneous_writers_of_one_chain_leave_no_fork(tmp_path: Path) -> None:
    subject = open_store(tmp_path)
    await subject.size()  # the schema, so twenty threads do not race to lay it down

    await asyncio.gather(
        *(
            subject.append(store.Entry(chain=ALICE, tool="files_search", nc_user="alice", at=at))
            for at in range(1000, 1020)
        )
    )

    written = rows(tmp_path)
    assert len(written) == 20
    assert len({row[-2] for row in written}) == 20, "two rows with the same predecessor is a fork"
    expected = store.GENESIS
    for row in written:
        assert row[-2] == expected
        assert digest_of(row) == row[-1]
        expected = row[-1]


async def test_the_instance_chain_and_a_user_chain_do_not_extend_each_other(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.append(store.Entry(chain=ALICE, tool="files_search", nc_user="alice", at=1000))
    await subject.append(
        store.Entry(
            chain=store.CHAIN_INSTANCE,
            kind=store.KIND_SWITCH,
            actor=store.ACTOR_UNKNOWN,
            reason="on",
            at=1001,
        )
    )
    await subject.append(store.Entry(chain=BOB, tool="notes_read", nc_user="bob", at=1002))

    alice, instance, bob = rows(tmp_path)
    assert instance[-2] == store.GENESIS
    assert bob[-2] == store.GENESIS
    assert alice[-2] == store.GENESIS
    assert instance[1] == store.CHAIN_INSTANCE
    assert instance[5] is None, "the instance chain has no account behind it"


async def test_last_entry_of_a_kind_skips_the_calls_between_two_switches(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.append(
        store.Entry(chain=store.CHAIN_INSTANCE, kind=store.KIND_SWITCH, reason="on", at=1000)
    )
    await subject.append(
        store.Entry(chain=store.CHAIN_INSTANCE, kind=store.KIND_SWITCH, reason="off", at=1001)
    )
    await subject.append(store.Entry(chain=store.CHAIN_INSTANCE, tool="files_search", at=1002))

    switch = await subject.last_entry(store.CHAIN_INSTANCE, kind=store.KIND_SWITCH)
    assert switch is not None
    assert switch.reason == "off"
    assert switch.at == 1001

    youngest = await subject.last_entry(store.CHAIN_INSTANCE)
    assert youngest is not None
    assert youngest.kind == store.KIND_CALL

    assert await subject.last_entry(ALICE) is None


# --- the size -------------------------------------------------------------------------


async def test_size_falls_after_rows_go_and_page_count_times_page_size_does_not(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.size()
    fill(tmp_path, 2000)

    before = await subject.size()
    pages_before = pages_times_size(tmp_path)
    assert before > 1  # more than one page in use, or the case measures nothing

    drop_oldest(tmp_path, 1000)

    after = await subject.size()
    pages_after = pages_times_size(tmp_path)
    assert after < before, "used_bytes has to fall, or the upper bound sweeps to an empty table"
    assert pages_after >= pages_before, "the pages stay: they moved to the free list"


# --- what a row may carry -------------------------------------------------------------


async def test_params_are_a_sorted_list_of_names_and_no_column_holds_a_value(
    tmp_path: Path,
) -> None:
    subject = open_store(tmp_path)
    await subject.append(
        store.Entry(
            chain=ALICE,
            tool="files_read",
            nc_user="alice",
            outcome=store.OUTCOME_OK,
            params=["path", "format", "max_bytes"],
            at=1000,
        )
    )

    (row,) = rows(tmp_path)
    assert row[13] == '["format","max_bytes","path"]'
    assert json.loads(row[13]) == ["format", "max_bytes", "path"]
    assert A_VALUE not in " ".join(str(column) for column in row)
