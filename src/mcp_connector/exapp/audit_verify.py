"""The handler behind ``occ mcp_connector:audit:verify``: is every chain still unbroken?

Success criterion 3 of this phase asks for a check that an administrator can run and that
says either "unbroken" or names the first broken place. The check itself lives in
``audit/store.py`` (:meth:`~mcp_connector.audit.store.AuditStore.verify_chains`, plan
18-04) and answers in data; this module is the half that turns that data into a sentence
and hands it to an occ command. AUDIT-02 is the requirement, and it is a requirement about
what an administrator gets to read, not about what a function returns.

Three decisions, each with its source, because each of them is one somebody will want to
undo.

**Why there is no route in the manifest.** The occ command reaches this handler over
AppAPI's ``PublicFunctions``, the same internal path ``/heartbeat``, ``/init``,
``/enabled`` and ``/purge`` arrive on, so it needs no declaration to work. Declaring one
would publish the state of the audit log of this instance to the internet, because the PHP
proxy attaches valid AppAPI headers itself and protects none of these paths (T-02-20,
pitfall 13 of 05-RESEARCH.md). This answer names chains, and a chain of a user is named
after that account, so the paragraph that protects ``/purge`` from a deletion protects this
one from a listing. The big comment in ``appinfo/info.xml`` names this path as the fifth
deliberately absent one, and :func:`audit_verify_routes` therefore runs the same double
check ``exapp/purge.py`` runs: ``x-origin-ip`` means the PHP proxy and is answered with
404, then ``require_appapi``, and neither rejection says which of the two spoke.

**Why the answer is always 200.** Measured against app_api v34.0.3,
``ExAppOccService::buildCommand`` (``lib/Service/ExAppOccService.php:159-213``) writes the
body of the answer to the console verbatim, but only after a status check: on any status
other than 200 it prints ``[<app>] command executeHandler failed`` and returns 1, and the
body is dropped unread. A broken chain reported with an error status would therefore lose
exactly the sentence that names the place. So the verdict travels in the body and the
status is 200 even then. The price is named rather than hidden: the exit code of the
command is always 0, so a monitoring script has to read the text (or ``--json``) and cannot
watch the return value. Both halves of that trade are one line apart here on purpose.

**What this check does not do.** It finds a row that was changed or removed unnoticed. It
does not find somebody who can write the file: whoever can do that can recompute the chain
behind the change, and a forged marker for a gap is indistinguishable from a real one
(D-v1.5-02). A whole user chain that vanished leaves no trace of its own either, because
every chain stands for itself (D-02). The answer says this in its last line rather than
only here, because the person who has to judge a green result is the one reading the
console and not the one reading this file.
"""

import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..audit.store import (
    FINDING_MISSING,
    FINDING_MODIFIED,
    AuditStore,
    ChainFinding,
    StoreOverview,
)
from ..errors import ToolError
from .auth import AppApiRejected, require_appapi
from .responses import NO_STORE, BodyTooLarge, BodyUnreadable, bounded_body, json_response

__all__ = ["AUDIT_VERIFY_PATH", "JSON_OPTION", "audit_verify_routes"]

#: The path of the one route of this module, and the name the occ command registration
#: hands to AppAPI as its ``execute_handler`` (``exapp/occ.py`` derives that from this
#: constant, so the two cannot drift apart). It appears in no ``<url>`` of the manifest,
#: on purpose; see the module docstring.
AUDIT_VERIFY_PATH = "/audit-verify"

#: The one option of the command, and unlike the option of the purge it is not a permission
#: but a shape: with it the same answer arrives as JSON. Declared on the AppAPI side in
#: ``exapp/occ.py`` and read here as well, because what AppAPI hands over is input.
JSON_OPTION = "json"

#: The envelope AppAPI wraps an occ invocation in. Measured against a running AppAPI 34.0.0
#: in plan 05-08 and unchanged since: ``ExAppOccService::buildCommand`` calls
#: ``PublicFunctions::exAppRequest`` with ``params: ['occ' => ['arguments' => ...,
#: 'options' => ...]]``, and ``AppAPIService::prepareRequestToExApp`` turns ``params`` into
#: the JSON body of a POST. So the body of a real invocation of this command is
#: ``{"occ": {"arguments": null, "options": {"json": true}}}`` and the flag sits one level
#: below the top.
OCC_ENVELOPE = "occ"

#: Set on the proxy path, never by HaRP and never on the internal AppAPI path. The same
#: header ``exapp/lifecycle.py`` and ``exapp/purge.py`` refuse, spelled a third time rather
#: than imported: ``lifecycle`` imports ``occ``, and ``occ`` imports this module, so an
#: import back would close a cycle. A test holds all three spellings equal.
HEADER_ORIGIN_IP = "x-origin-ip"

#: The largest body this handler reads before deciding it is not an occ invocation. The
#: real one is one option name; anything above this is not AppAPI and is not parsed (the
#: rule of ``exapp/purge.py`` and of ``oauth/connections.py``).
MAX_BODY_BYTES = 4096

#: The words that mean "yes" when the option arrives with a value. Written here rather than
#: imported from ``exapp/purge.py``: that list belongs to the one action of this app that
#: cannot be undone, and a change made for a deletion must not silently change how a reading
#: command reads its output format. A test in ``tests/unit/test_exapp_audit_verify.py`` holds
#: the two equal, so the two lists cannot drift apart without somebody deciding it.
TRUE_WORDS = frozenset({"1", "true", "yes", "on"})

#: What a chain identifier is cut to before it is printed. The identifier of a user chain
#: carries the account name (``u:<nc_user>``), which is written by whoever creates accounts
#: on this instance, so it is bracketed exactly like the client name in ``audit/store.py``:
#: control characters go, runs of whitespace become one space, and the rest is cut. A name
#: with a line break in it could otherwise fake a finding line of its own (T-18-08).
CHAIN_LIMIT = 80

#: The verdict of a whole store, and the only line of the answer that says nothing happened.
NO_BREAK = "chains verified, no break found"

#: The last line of every answer, in both shapes. It belongs in the answer and not only in
#: this docstring, because a green result is judged by whoever reads the console.
LIMIT_SENTENCE = (
    "This check finds an entry that was changed or removed unnoticed. It does not find "
    "somebody who can write this file, because whoever can write it can recompute the "
    "chain behind the change."
)

logger = logging.getLogger("mcp_connector.exapp.audit_verify")

#: How a caller hands in its own store, the shape ``exapp/purge.py`` uses for the OAuth one.
type StoreProvider = Callable[[], Awaitable[AuditStore]]


def audit_verify_routes(
    env: Mapping[str, str] | None = None, *, store_provider: StoreProvider
) -> list[Route]:
    """The one route of the check, handed out rather than registered on the server object.

    A factory for the reason D-23 gives and ``exapp/lifecycle.py`` states: a registration on
    the shared MCP server object would make this path appear in the standalone HTTP mode of
    phase 1 as soon as anything imports this module, and that mode has no AppAPI identity to
    check it against.
    """

    async def audit_verify(request: Request) -> Response:
        """Walk every chain, then say either "no break" or where the first one is."""
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        as_json = await _wants_json(request)
        try:
            store = await store_provider()
            overview = await store.overview()
            findings = await store.verify_chains()
        except Exception as exc:
            # The type only, never the message: a store error can carry a path.
            logger.error("the audit log could not be checked: %s", type(exc).__name__)
            if as_json:
                return json_response({"checked": False, "error": type(exc).__name__})
            return _text(f"the audit log could not be checked: {type(exc).__name__}")

        logger.info(
            "the audit log was checked: %s chains, %s entries, %s findings",
            overview.chains,
            overview.entries,
            len(findings),
        )
        if as_json:
            return json_response(_machine_readable(overview, findings))
        return _text(_report(overview, findings))

    return [Route(AUDIT_VERIFY_PATH, audit_verify, methods=["POST"])]


def _report(overview: StoreOverview, findings: list[ChainFinding]) -> str:
    """The answer an administrator reads, in the order the plan of 18-08 fixed.

    Head, verdict, the line about the markers for gaps, and the limit of the check. The
    third one is there so an explained hole can be told from an unexplained one: a store
    whose oldest rows gave way to the upper bound is whole, and it says so next to the
    number of rows that went (D-10).
    """
    chains = _count(overview.chains, "chain", "chains")
    entries = _count(overview.entries, "entry", "entries")
    lines = [f"checked {chains} with {entries}"]
    lines.extend([NO_BREAK] if not findings else [_sentence(finding) for finding in findings])
    lines.append(
        f"{_count(overview.tombstones, 'tombstone', 'tombstones')} in the instance chain, "
        f"explaining {_count(overview.explained_entries, 'entry', 'entries')} that were removed"
    )
    lines.append(LIMIT_SENTENCE)
    return "\n".join(lines) + "\n"


def _count(number: int, one: str, many: str) -> str:
    """A number with the word behind it in the right number.

    Both forms are handed in because the words of this answer are not all regular, and an
    answer that says "1 chains" is one an administrator has to read twice.
    """
    return f"{number} {one}" if number == 1 else f"{number} {many}"


def _sentence(finding: ChainFinding) -> str:
    """One finding, written out: which kind, which chain, and which number or pair of them.

    Three kinds and not one, because "somebody edited this row" and "something between these
    two rows is gone" are different events with different answers, and a check that only
    says "broken" leaves the whole file to look at.
    """
    chain = _printable(finding.chain)
    if finding.kind == FINDING_MODIFIED:
        return f"entry {finding.seq} in chain {chain} was changed after it was written"
    if finding.kind == FINDING_MISSING and finding.next_seq is not None:
        return f"an entry is missing between {finding.seq} and {finding.next_seq} in chain {chain}"
    return (
        f"the beginning of chain {chain} is missing and no tombstone explains it, "
        f"the oldest entry left is {finding.seq}"
    )


def _machine_readable(overview: StoreOverview, findings: list[ChainFinding]) -> dict[str, Any]:
    """The same answer for a monitoring script, with the same 200 under it.

    ``broken`` exists because the exit code cannot carry it: the command answers 0 whatever
    it found, for the reason the module docstring measures, so this key is what a script
    watches instead. Every finding keeps its data next to its sentence, so a reader does not
    have to parse the sentence back apart.
    """
    return {
        "checked": True,
        "chains": overview.chains,
        "entries": overview.entries,
        "tombstones": overview.tombstones,
        "explained_entries": overview.explained_entries,
        "broken": bool(findings),
        "findings": [
            {
                "chain": _printable(finding.chain),
                "kind": finding.kind,
                "seq": finding.seq,
                "next_seq": finding.next_seq,
                "message": _sentence(finding),
            }
            for finding in findings
        ],
        "limit": LIMIT_SENTENCE,
    }


def _printable(chain: str) -> str:
    """A chain identifier, made safe to print and bounded in length.

    A user chain is named ``u:<nc_user>`` and is handed out as it is: an account name is no
    secret, and an administrator who has to look at a broken chain needs to know whose it
    is. It is still bracketed the way ``audit/store.py`` brackets the client name, and for
    the same reason: the value comes from outside, and control characters in it could fake a
    line of this answer (T-18-08).
    """
    printable = "".join(
        " " if character < " " or character == "\x7f" else character for character in chain
    )
    return " ".join(printable.split())[:CHAIN_LIMIT]


def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    """Return the Nextcloud user id of this request, or the response that ends it.

    Verbatim the guard of ``exapp/purge.py`` and ``exapp/lifecycle.py``, including the reason
    for both halves: a response instead of an exception so no rejection escapes as a 500, and
    no detail in the rejection so nothing tells a caller which of the checks refused it
    (T-02-03, T-18-07).
    """
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        return json_response({}, status_code=401)


async def _wants_json(request: Request) -> bool:
    """Whether this invocation carries ``--json``, in any shape AppAPI may send it.

    The reading form of ``exapp/purge.py``, minus its severity: this option decides between
    two shapes of the same harmless answer, so a body this handler will not read is not a
    rejection but simply the default, which is text.
    """
    return _set_in(await _payload(request))


def _set_in(payload: Any, *, inside_envelope: bool = False) -> bool:
    """The option in a JSON body: in the occ envelope, at the top level, or in a list.

    ``inside_envelope`` keeps the descent one level deep. The envelope AppAPI builds carries
    no second one, and a body that nests them is not an occ invocation.
    """
    if not isinstance(payload, dict):
        return False
    if JSON_OPTION in payload and _is_set(payload[JSON_OPTION]):
        return True

    options = payload.get("options")
    if isinstance(options, dict) and JSON_OPTION in options and _is_set(options[JSON_OPTION]):
        return True
    if isinstance(options, list | tuple) and any(
        isinstance(item, str) and item.strip().lstrip("-") == JSON_OPTION for item in options
    ):
        return True

    if not inside_envelope:
        return _set_in(payload.get(OCC_ENVELOPE), inside_envelope=True)
    return False


def _is_set(value: object) -> bool:
    """Whether this value means the option is set. A positive list, and nothing beside it.

    The same rule ``registry._switch``, ``config_values._switch`` and ``purge._is_set``
    follow: a value nobody understands is a typo, and a typo does not decide anything. A yes
    is a JSON ``true``, the number one, an option that arrived with no value at all (a
    Symfony option in mode ``none`` is presence and nothing more), or one of
    :data:`TRUE_WORDS`. Nothing is logged for an unknown value here, unlike in the purge: the
    worst outcome of a misread is an answer in the other shape, and a warning per invocation
    would cost more than it says.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, int | float):
        return value == 1
    if not isinstance(value, str):
        return False
    return value.strip().lower() in TRUE_WORDS


async def _payload(request: Request) -> Any:
    """The JSON body, or ``None`` when there is none this handler is willing to read.

    Bounded and never logged, exactly as in ``exapp/purge.py``: the announced length is read
    first because refusing before a byte is on the wire is cheaper than counting, and
    ``responses.bounded_body`` is what actually holds, because a chunked request announces
    nothing at all (IN-01 of the re-review of phase 5).
    """
    announced = request.headers.get("content-length", "")
    if announced.isdigit() and int(announced) > MAX_BODY_BYTES:
        logger.warning("a check call announced a body this handler does not read")
        return None
    try:
        raw = await bounded_body(request, MAX_BODY_BYTES)
    except BodyTooLarge:
        logger.warning("a check call sent a body this handler does not read")
        return None
    except BodyUnreadable:
        logger.warning("the body of a check call could not be read")
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        logger.warning("the body of a check call is not JSON")
        return None


def _text(body: str, status_code: int = 200) -> Response:
    """Every answer of this module that is not JSON, and 200 unless a guard says otherwise.

    The default is the measurement of the module docstring rather than a habit: a status
    other than 200 makes AppAPI drop this body, and the body is the whole answer.
    """
    return Response(body, status_code=status_code, media_type="text/plain", headers=NO_STORE)
