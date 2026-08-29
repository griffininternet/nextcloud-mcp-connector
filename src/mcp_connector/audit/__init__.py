"""The audit log package: one store per application, and the name its recorder is left under.

Three things live here and nothing else: the attribute name that ties the transport boundary
to the recording path, the factory that opens the file once per application, and the exports
the rest of the app reaches the store through. The recording path itself and the allowlist of
parameter names arrive in later plans of this phase; importing them here would only build a
ring, because the recorder imports this package.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping

from .. import config
from . import store
from .store import (
    ACTOR_UNKNOWN,
    CHAIN_INSTANCE,
    KIND_CALL,
    KIND_SWITCH,
    KIND_TOMBSTONE,
    OUTCOME_FAILED,
    OUTCOME_OK,
    OUTCOME_REJECTED,
    AuditStore,
    Entry,
    user_chain,
)

__all__ = [
    "ACTOR_UNKNOWN",
    "AUDIT_STATE_ATTR",
    "CHAIN_INSTANCE",
    "KIND_CALL",
    "KIND_SWITCH",
    "KIND_TOMBSTONE",
    "OUTCOME_FAILED",
    "OUTCOME_OK",
    "OUTCOME_REJECTED",
    "AuditStore",
    "Entry",
    "audit_opener",
    "user_chain",
]

#: The name the transport boundary deposits the recorder under, and the name the recording
#: path reads. One constant, so the two sides cannot drift apart. The same shape and the
#: same reason as ``OAUTH_STATE_ATTR`` in ``oauth/verifier.py``.
AUDIT_STATE_ATTR = "audit_recorder"


def audit_opener(env: Mapping[str, str] | None = None) -> Callable[[], Awaitable[AuditStore]]:
    """One audit store per application, opened at its first use.

    The store cannot be built when the routes are: the path comes from the volume AppAPI
    mounts, and a deployment that is not complete has to end in a page rather than in a
    failed import. So the callers get a function, and the first write that needs the file
    pays for opening it.

    The cache lives in this closure and not in a module global, which is the rule of this
    project (D-20) and a gate as well: ``tests/contract/test_no_destructive_calls.py`` counts
    the documented exceptions for module state and allows exactly two of them. This module
    does not register a third one. Two applications in one process, which is what every test
    builds, get one store each unless the caller hands the same opener to both.
    """
    opened: dict[str, AuditStore] = {}
    lock = asyncio.Lock()

    async def open_once() -> AuditStore:
        ready = opened.get("store")
        if ready is not None:
            return ready
        async with lock:
            ready = opened.get("store")
            if ready is None:
                ready = AuditStore(config.persistent_storage(env) / store.AUDIT_FILENAME)
                opened["store"] = ready
            return ready

    return open_once
