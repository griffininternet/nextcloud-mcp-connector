"""``occ mcp_connector:audit:verify``: success criterion 3 of this phase as a command.

The check itself is tested in ``tests/unit/test_audit_store.py``. What is under test here is
everything between that check and the console of an administrator: who may reach it, which
status it answers with, and whether the sentence it prints really names the place instead of
only saying that something is wrong.

Threats covered here, in the order of the plan:

* **T-18-07** the handler reached from outside: ``x-origin-ip`` is 404, a request without the
  AppAPI headers is 401, neither says which of the two refused it, and the path appears in no
  route of ``appinfo/info.xml``.
* **T-18-03** a changed or removed entry staying unnoticed: three manipulations, each one
  made with a connection of its own past the store, and each one has to come back out of the
  answer with its chain and its number.
* **T-18-20** the verdict getting lost: ``ExAppOccService::buildCommand`` drops the body on
  any status other than 200, so every answer that got past the guard is asserted to be 200,
  the broken ones included.

The store is a real SQLite file in ``tmp_path`` for the reason the store tests give: a
manipulation is a property of the file, and a mock of the store would assert the mock.
"""

import asyncio
import base64
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from lxml import etree
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_connector import config
from mcp_connector.audit import store
from mcp_connector.exapp import audit_verify, purge
from mcp_connector.nextcloud.clients.xml import hardened_parser

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
BASE_URL = "http://nc.test"

ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
}

ALICE = store.user_chain("alice")
BOB = store.user_chain("bob")

MANIFEST = Path(__file__).resolve().parents[2] / "appinfo" / "info.xml"


def appapi_headers(user: str = "", secret: str = APP_SECRET) -> dict[str, str]:
    """What AppAPI puts on an internal call. The user is empty: this is the app context."""
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token,
    }


class Deployment:
    """One process of this application with its own audit file and the check route on it."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / store.AUDIT_FILENAME
        self.store = store.AuditStore(self.path)
        self.client = TestClient(
            Starlette(routes=audit_verify.audit_verify_routes(ENV, store_provider=self._open))
        )

    async def _open(self) -> store.AuditStore:
        return self.store

    def write_calls(self, chain: str, moments: list[int]) -> None:
        """Ordinary rows through the public interface, so the chain of the file is real."""
        asyncio.run(self._write_calls(chain, moments))

    async def _write_calls(self, chain: str, moments: list[int]) -> None:
        for at in moments:
            await self.store.append(
                store.Entry(
                    chain=chain,
                    tool="files_search",
                    nc_user=chain.removeprefix("u:"),
                    outcome=store.OUTCOME_OK,
                    params=["query"],
                    at=at,
                )
            )

    def sweep(self, *, moment: int) -> store.SweepReport:
        return asyncio.run(self.store.sweep(moment=moment))

    def past_the_store(self, statement: str, parameters: tuple[Any, ...]) -> None:
        """Change the file with a connection of its own, the way an attacker would.

        Never through a method of the module: a manipulation that went through the store
        would recompute the chain and prove nothing about the check.
        """
        conn = sqlite3.connect(self.path, isolation_level=None)
        try:
            conn.execute(statement, parameters)
        finally:
            conn.close()


@pytest.fixture
def live(tmp_path: Path) -> Deployment:
    """A deployment with two chains of four and three entries, all of them whole."""
    deployment = Deployment(tmp_path)
    deployment.write_calls(ALICE, [1000, 1001, 1002, 1003])
    deployment.write_calls(BOB, [1004, 1005, 1006])
    return deployment


def call(
    deployment: Deployment,
    *,
    as_json: bool = False,
    body: object | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """One occ invocation, as AppAPI delivers it: a POST with the options in the body.

    ``Any`` for the reason ``tests/unit/test_oauth_abuse.py`` gives: the test client of
    Starlette answers with the response type of ``httpx2``, the fork the MCP SDK brings, and
    the outgoing calls of this app use ``httpx``. Naming either type here is a false claim.
    """
    options = {audit_verify.JSON_OPTION: True} if as_json else {}
    payload = body if body is not None else {"occ": {"arguments": None, "options": options}}
    sent = appapi_headers() if headers is None else headers
    return deployment.client.post(audit_verify.AUDIT_VERIFY_PATH, json=payload, headers=sent)


# --- the boundary: T-18-07 ----------------------------------------------------------


def test_a_request_through_the_php_proxy_is_not_served(live: Deployment) -> None:
    """The PHP proxy attaches valid AppAPI headers itself, so its own marker is the only
    thing that tells this handler the request came through it (pitfall 13)."""
    headers = appapi_headers() | {"x-origin-ip": "203.0.113.7"}

    response = call(live, headers=headers)

    assert response.status_code == 404
    assert response.text == "Not Found"
    assert "chain" not in response.text
    assert "alice" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_a_request_without_appapi_headers_is_401_without_detail(live: Deployment) -> None:
    """T-18-07: no answer says which of the two checks refused, and none says what is in the
    file. A caller who learns "the chain of alice is whole" has learned that alice uses this
    app."""
    response = call(live, headers={})

    assert response.status_code == 401
    assert response.json() == {}
    assert "alice" not in response.text
    assert APP_SECRET not in response.text


def test_neither_rejection_tells_the_caller_which_check_refused(live: Deployment) -> None:
    """The two answers have to be distinguishable by status alone and by nothing else."""
    proxied = call(live, headers=appapi_headers() | {"x-origin-ip": "203.0.113.7"})
    anonymous = call(live, headers={})

    for answer in (proxied, anonymous):
        assert audit_verify.HEADER_ORIGIN_IP not in answer.text.lower()
        assert "appapi" not in answer.text.lower()
        assert "header" not in answer.text.lower()
        assert answer.headers["cache-control"] == "no-store"


def test_a_request_with_a_wrong_app_secret_is_401(live: Deployment) -> None:
    response = call(live, headers=appapi_headers(secret="wrong"))

    assert response.status_code == 401
    assert response.json() == {}


def test_the_positive_list_of_the_option_is_the_one_of_the_purge() -> None:
    """The second duplicate of this module, and it is a decision rather than an accident.

    A value that arms a switch of this app reads the same everywhere. The list is spelled
    here so a change made for the destructive command cannot silently change how a reading
    one is invoked, and this assertion is what makes such a change a decision.
    """
    assert audit_verify.TRUE_WORDS == purge.TRUE_WORDS


def test_the_handler_path_is_declared_in_no_route_of_the_manifest() -> None:
    """T-18-07: a declared route would publish the list of everybody who used this app.

    The manifest still carries exactly the thirteen routes of phase 5, and none of them
    matches this path in any spelling.
    """
    root = etree.parse(str(MANIFEST), hardened_parser()).getroot()
    urls = [(element.text or "").strip() for element in root.iter("url")]

    assert len(urls) == 13, urls
    bare = audit_verify.AUDIT_VERIFY_PATH.strip("/")
    for url in urls:
        assert bare not in url, f"{url} would make the check reachable from the internet"


# --- the verdict, and the status it may never carry: T-18-20 ------------------------


def test_an_untouched_store_answers_200_and_says_no_break(live: Deployment) -> None:
    response = call(live)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["cache-control"] == "no-store"
    assert audit_verify.NO_BREAK in response.text
    assert "checked 2 chains with 7 entries" in response.text
    assert audit_verify.LIMIT_SENTENCE in response.text


def test_an_empty_store_is_whole_and_says_so(tmp_path: Path) -> None:
    """The store of an installation that never switched the log on has nothing to report."""
    response = call(Deployment(tmp_path))

    assert response.status_code == 200
    assert audit_verify.NO_BREAK in response.text
    assert "checked 0 chains with 0 entries" in response.text


def test_a_changed_entry_is_named_with_its_chain_and_its_number(live: Deployment) -> None:
    """T-18-03, and the number is asserted literally: "something is broken" is not the
    criterion, "the first place with a name" is."""
    live.past_the_store("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 3))

    response = call(live)

    assert response.status_code == 200, "a broken chain reported with 4xx loses its own body"
    assert f"entry 3 in chain {ALICE} was changed after it was written" in response.text
    assert audit_verify.NO_BREAK not in response.text
    assert BOB not in response.text, "the whole chain is not a finding"


def test_a_removed_entry_is_named_as_the_pair_of_numbers_it_was_between(
    live: Deployment,
) -> None:
    """A deleted row leaves the hash of its neighbour intact and breaks only its link, so
    this case has to name two numbers where the one above names one."""
    live.past_the_store("DELETE FROM entries WHERE seq = ?", (3,))

    response = call(live)

    assert response.status_code == 200
    assert f"an entry is missing between 2 and 4 in chain {ALICE}" in response.text
    assert audit_verify.NO_BREAK not in response.text


def test_a_head_of_a_chain_that_nothing_explains_is_named_as_such(live: Deployment) -> None:
    """The third kind: the oldest entry of a chain is gone and no marker stands for it."""
    live.past_the_store("DELETE FROM entries WHERE seq = ?", (1,))

    response = call(live)

    assert response.status_code == 200
    assert f"the beginning of chain {ALICE} is missing" in response.text
    assert "no tombstone explains it" in response.text
    assert "the oldest entry left is 2" in response.text


def test_a_real_tombstone_leaves_no_finding_and_is_counted_in_its_own_line(
    tmp_path: Path,
) -> None:
    """The difference between an explained hole and an unexplained one, in one case.

    Both halves are the proof: no finding **and** a line that says how many entries the
    markers stand for. Without the second half the answer of a store that gave half its rows
    to the retention window would read like the answer of one that never lost a row.
    """
    deployment = Deployment(tmp_path)
    old = 1_000_000_000
    young = old + 400 * 86400
    deployment.write_calls(ALICE, [old, old + 1, old + 2, old + 3])
    deployment.write_calls(ALICE, [young, young + 1])

    report = deployment.sweep(moment=young + 2)
    response = call(deployment)

    assert report.tombstones == 1
    assert response.status_code == 200
    assert audit_verify.NO_BREAK in response.text
    assert "1 tombstone in the instance chain, explaining 4 entries that were removed" in (
        response.text
    )


def test_the_line_about_the_markers_is_there_even_when_there_is_none(live: Deployment) -> None:
    """A store without a gap says so with a number, because an absent line says nothing."""
    response = call(live)

    assert "0 tombstones in the instance chain, explaining 0 entries that were removed" in (
        response.text
    )


def test_every_answer_that_got_past_the_guard_carries_200(live: Deployment) -> None:
    """T-18-20 as one case over all four outcomes: the body is the answer, and a status
    other than 200 makes AppAPI print "command executeHandler failed" instead of it."""
    answers = [call(live), call(live, as_json=True)]
    live.past_the_store("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 2))
    answers += [call(live), call(live, as_json=True)]

    assert [answer.status_code for answer in answers] == [200, 200, 200, 200]


# --- the machine readable shape -----------------------------------------------------


def test_the_json_option_answers_the_same_findings_with_the_same_status(
    live: Deployment,
) -> None:
    live.past_the_store("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 3))

    response = call(live, as_json=True)

    assert response.status_code == 200
    body = response.json()
    assert body["checked"] is True
    assert body["broken"] is True
    assert body["chains"] == 2
    assert body["entries"] == 7
    assert body["findings"] == [
        {
            "chain": ALICE,
            "kind": store.FINDING_MODIFIED,
            "seq": 3,
            "next_seq": None,
            "message": f"entry 3 in chain {ALICE} was changed after it was written",
        }
    ]
    assert body["limit"] == audit_verify.LIMIT_SENTENCE
    assert response.headers["cache-control"] == "no-store"


def test_the_json_option_of_a_whole_store_says_not_broken(live: Deployment) -> None:
    body = call(live, as_json=True).json()

    assert body["broken"] is False
    assert body["findings"] == []
    assert body["tombstones"] == 0
    assert body["explained_entries"] == 0


@pytest.mark.parametrize(
    "body",
    [
        {"occ": {"arguments": None, "options": {"json": True}}},
        {"occ": {"arguments": None, "options": {"json": None}}},
        {"occ": {"arguments": None, "options": ["--json"]}},
        {"options": {"json": "yes"}},
        {"json": True},
    ],
)
def test_every_shape_of_the_option_appapi_may_send_is_understood(
    live: Deployment, body: object
) -> None:
    """The measured shape is the first one; the rest is the margin around that measurement."""
    response = call(live, body=body)

    assert response.status_code == 200
    assert response.json()["checked"] is True


@pytest.mark.parametrize(
    "body",
    [
        {"occ": {"arguments": None, "options": {}}},
        {"occ": {"arguments": None, "options": {"json": False}}},
        {"occ": {"arguments": None, "options": {"json": "maybe"}}},
        {},
        [],
        "not an envelope",
    ],
)
def test_anything_that_is_not_the_option_leaves_the_answer_as_text(
    live: Deployment, body: object
) -> None:
    """A value nobody understands is a typo, and a typo does not decide the output shape."""
    response = call(live, body=body)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert audit_verify.NO_BREAK in response.text


def test_a_body_above_the_limit_is_not_parsed_and_costs_no_answer(live: Deployment) -> None:
    """The rule of ``exapp/purge.py``: a body this handler will not read is the default,
    which is text, and never a rejection."""
    payload = {"occ": {"options": {"json": True}, "padding": "x" * audit_verify.MAX_BODY_BYTES}}

    response = call(live, body=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


# --- the store that cannot be read: T-18-10 -----------------------------------------


def test_a_store_that_cannot_be_opened_answers_200_with_the_type_and_no_path(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A check that could not read anything must not answer as if it had checked, and it
    must not repeat the message of the error: the message of a store error carries the path
    of the file (T-18-10)."""

    async def broken() -> store.AuditStore:
        raise OSError(f"unable to open database file {tmp_path / store.AUDIT_FILENAME}")

    client = TestClient(
        Starlette(routes=audit_verify.audit_verify_routes(ENV, store_provider=broken))
    )

    with caplog.at_level(logging.DEBUG):
        response = client.post(audit_verify.AUDIT_VERIFY_PATH, json={}, headers=appapi_headers())

    assert response.status_code == 200
    assert "OSError" in response.text
    assert audit_verify.NO_BREAK not in response.text
    assert store.AUDIT_FILENAME not in response.text
    assert str(tmp_path) not in response.text
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert store.AUDIT_FILENAME not in logged
    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


def test_a_store_that_cannot_be_opened_stays_machine_readable_with_the_option(
    tmp_path: Path,
) -> None:
    """The option promises a shape, and a failure is exactly when a script needs it kept."""

    async def broken() -> store.AuditStore:
        raise OSError("unable to open database file")

    client = TestClient(
        Starlette(routes=audit_verify.audit_verify_routes(ENV, store_provider=broken))
    )

    response = client.post(
        audit_verify.AUDIT_VERIFY_PATH,
        json={"occ": {"arguments": None, "options": {"json": True}}},
        headers=appapi_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {"checked": False, "error": "OSError"}


# --- what the answer may say about a name ------------------------------------------


def test_a_chain_name_cannot_fake_a_line_of_the_answer(tmp_path: Path) -> None:
    """T-18-08: the identifier of a user chain carries an account name, and account names
    are written by whoever creates accounts on this instance.

    The criterion is the line and not the substring, and that is what the handler promises:
    a name that carries a line break cannot end the finding line and start a verdict of its
    own. Inside its line the name can still say anything, which is the second reason the
    machine readable shape exists, so this case asserts that shape as well.
    """
    deployment = Deployment(tmp_path)
    forged = store.user_chain("mallory\n" + audit_verify.NO_BREAK)
    deployment.write_calls(forged, [1000, 1001])
    deployment.past_the_store("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 2))

    response = call(deployment)
    machine = call(deployment, as_json=True).json()

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert len(lines) == 4, "head, finding, markers, limit: a name may not add a fifth"
    assert audit_verify.NO_BREAK not in lines, "and above all not a line that says it is whole"
    assert "mallory" in response.text, "and it is still readable enough to be found"
    assert machine["broken"] is True, "the key a script watches is untouched by a name"


def test_no_answer_carries_a_parameter_value_or_a_tool_argument(live: Deployment) -> None:
    """The log itself holds no value (D-06), and this answer holds even less: counts, chains
    and numbers."""
    live.past_the_store("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 3))

    text = call(live).text
    body = json.dumps(call(live, as_json=True).json())

    for answer in (text, body):
        assert "files_search" not in answer
        assert "files_read" not in answer
        assert "query" not in answer
