"""The mail spike (MAIL-04): does an impersonated request reach Mail's own controllers.

This file measures one thing and asserts as little as possible about it. Phase 2 proved that
AppAPI impersonation carries six API families (``docs/spike-dav.md``), but Mail is the first
family whose listing routes carry no ``#[NoCSRFRequired]``, so whether a request that arrives
with ``AUTHORIZATION-APP-API`` alone reaches ``AccountsController``, ``MailboxesController``
and ``MessagesController`` at all is still open. A negative answer changes the cut of phases
10 and 11, which is why the answer is written down here and in ``docs/spike-mail.md`` before
either phase is planned.

Four things are load bearing in here.

*   **The measured question.** Not "does Mail work", but "did app code answer". A JSON body
    with any status code (200, 403, 404, 500) proves the controller was reached, because
    nothing but app code produces those bodies. Only an HTML body or a redirect to ``/login``
    disproves it. That is why no test below asserts ``status == 200``: the three listing ways
    touch IMAP, and an IMAP error is still app code answering.
*   **The replaceability risk.** All three listing controllers carry
    ``#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`` on class level, so ``/api/accounts``,
    ``/api/mailboxes`` and ``/api/messages`` are not a promised API: they are the internals of
    Mail's own frontend, and a Mail release may change or drop them without a deprecation.
    Whatever phase 10 builds on them has to stay replaceable, and the named way out is
    discovery through the unified search provider ``mail`` plus the OCS full text route below,
    which is the only one of the four that is a declared route. This paragraph belongs in the
    future ``src/mcp_connector/nextcloud/clients/mail.py`` too, and phase 10 owns putting it
    there.
*   **The OCS route has no ``api`` segment.** The ``ocs`` block of Mail's ``appinfo/routes.php``
    declares ``/message/{id}``, so the full URL is
    ``GET /ocs/v2.php/apps/mail/message/{id}`` and not ``.../apps/mail/api/message/{id}``
    (correction K1). Measuring the ``api`` spelling returns a 404 out of the routing layer and
    would make Mail look unreachable when it is not.
*   **Run it against the running HaRP topology.** The requests go straight to Nextcloud, never
    through the ExApp container: what is measured is Nextcloud's impersonation, not the proxy
    hop.

    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q

Add ``-s`` to the last command to see the four measured rows; they are what
``docs/spike-mail.md`` records verbatim.
"""

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.credentials import MODE_APPAPI, Credentials

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

#: Internal listing route, ``SCOPE_IGNORE``: ``AccountsController`` is the frontend's own
#: endpoint and reads nothing but the database, which makes it the cheapest of the four ways.
MAIL_ACCOUNTS_PATH = "/index.php/apps/mail/api/accounts"

#: Internal listing route, ``SCOPE_IGNORE``. The answer is an object with a ``mailboxes``
#: list, not a list (correction K7), and ``MailManager::getMailboxes`` forces an IMAP sync
#: unconditionally, so without a reachable IMAP server this way answers an error out of app
#: code. That is a measurement, not a failure.
MAIL_MAILBOXES_PATH = "/index.php/apps/mail/api/mailboxes"

#: Internal listing route, ``SCOPE_IGNORE``. ``limit`` is always sent: a missing ``limit`` is
#: not "everything" but exactly one message, because ``min(100, max(1, null))`` is 1 in PHP 8
#: (correction K6).
MAIL_MESSAGES_PATH = "/index.php/apps/mail/api/messages"

#: The one declared route of the four, and therefore the one phase 10 may rely on. It lives
#: in the ``ocs`` block of Mail's routes and has no ``api`` segment (correction K1).
MAIL_MESSAGE_OCS_PATH = "/apps/mail/message/{message_id}"

#: The four ways, in the order a reader walks them.
WAYS = ("accounts", "mailboxes", "messages", "ocs")

#: How many characters of a response body ever reach a log line or a protocol. A security
#: requirement and not cosmetics: the accounts answer carries IMAP and SMTP host names, user
#: names and the display name of a real account (T-08-01).
HEAD_LIMIT = 120

#: A message id that exists on no instance. One request, never a loop, see ``_row``.
MISSING_MESSAGE_ID = "999999"

#: Stage 1 of this spike runs without a reachable IMAP server, so the account has no mailbox
#: and there is no id to read. A mailbox that does not exist is answered by app code as well,
#: which is the whole question here; stage 2 with a real IMAP server is the named follow up in
#: ``docs/spike-mail.md``.
FALLBACK_MAILBOX_ID = "0"

#: The rows of one run. A memo and not a fixture, because the OCS way is asserted by its own
#: test and printed by the protocol table, and it may cost exactly one request in total:
#: ``messageApi#get`` carries ``#[BruteForceProtection('mailGetMessage')]`` and Nextcloud
#: counts per source IP, which for an ExApp is one address for every user of the instance.
_measured: dict[str, dict[str, str]] = {}


def _appapi_clients(exapp_env: dict[str, str], user: str) -> NcClients:
    """Build the impersonating clients for one user, ``APP_SECRET`` as the only credential.

    Mirrors ``deps._credentials_from_appapi``: the same base URL, the same fields, the same
    mode. No Basic scheme is built anywhere in this file, the literal spelling of that httpx
    class does not occur in it at all, and no ``NC_MCP_APP_PASSWORD`` is read as a credential
    source, so the identity can only come from ``AUTHORIZATION-APP-API``.
    """
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(exapp_env["base_url"]),
            user=user,
            secret=exapp_env["app_secret"],
            mode=MODE_APPAPI,
            app_id=exapp_env["app_id"],
            app_version=exapp_env["app_version"],
            aa_version=exapp_env["aa_version"],
        ),
    )


@pytest.fixture
async def alice_clients(exapp_env: dict[str, str]) -> AsyncIterator[NcClients]:
    clients = _appapi_clients(exapp_env, exapp_env["alice"])
    async with clients.client:
        yield clients


# --------------------------------------------------------------------------------------
# Control checks. Everything below them is worthless without them.
# --------------------------------------------------------------------------------------


async def test_the_measuring_process_holds_no_nextcloud_app_password(
    exapp_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control one: the identity cannot come from a Basic app password or a static bearer.

    ``NC_MCP_APP_PASSWORD`` and ``NC_MCP_STATIC_BEARER`` are the two variables the connector
    itself would authenticate from. They are removed for the duration of the test and
    asserted absent, so a measured row cannot be explained by a credential that happened to
    sit in the environment.
    """
    monkeypatch.delenv("NC_MCP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("NC_MCP_STATIC_BEARER", raising=False)
    assert os.environ.get("NC_MCP_APP_PASSWORD") is None
    assert os.environ.get("NC_MCP_STATIC_BEARER") is None
    clients = _appapi_clients(exapp_env, exapp_env["alice"])
    assert clients.creds.mode == MODE_APPAPI
    assert clients.creds.secret == exapp_env["app_secret"]


async def test_a_wrong_app_secret_is_refused(exapp_env: dict[str, str]) -> None:
    """Control two: without the real secret, nothing answers 200.

    A wrong ``APP_SECRET`` fails Nextcloud's ``validateExAppRequestToNC``. If this call still
    reached the data, some other mechanism would be authenticating the request and every
    measured row would be measuring that mechanism instead of impersonation.
    """
    wrong = _appapi_clients({**exapp_env, "app_secret": "0" * 64}, exapp_env["alice"])
    async with wrong.client:
        response = await ocs.ocs_get(wrong.client, wrong.creds, "/cloud/user")
    assert response.status_code != 200, (
        "a wrong APP_SECRET was accepted; the identity is not coming from the secret"
    )


# --------------------------------------------------------------------------------------
# The measurement. One request per way, recorded instead of asserted.
# --------------------------------------------------------------------------------------


async def _probe(clients: NcClients, method: str, url: str) -> dict[str, str]:
    """One measured way. Records what came back instead of asserting a status code.

    A JSON body with any status proves the controller was reached; an HTML body or a redirect
    to ``/login`` proves it was not. That distinction is the whole point of MAIL-04, and it is
    the reason this helper does not assert 200: the listing routes touch IMAP, and an IMAP
    error is still app code answering.

    ``head`` is capped at ``HEAD_LIMIT`` characters, and that cap is a security requirement
    rather than a nicety: the accounts answer carries IMAP and SMTP host names next to the
    account name, and everything returned here is written into a protocol that leaves the
    confidential zone (T-08-01). Header values are never returned except ``location``, because
    ``AUTHORIZATION-APP-API`` is as sensitive as ``APP_SECRET`` itself.
    """
    response = await clients.client.request(
        method, url, headers=dict(ocs.OCS_HEADERS), auth=clients.creds.auth()
    )
    body = response.text.lstrip()
    return {
        "status": str(response.status_code),
        "content_type": response.headers.get("content-type", ""),
        "shape": "html" if body.startswith("<") else "json" if body[:1] in "[{" else "other",
        "location": response.headers.get("location", ""),
        "head": body[:HEAD_LIMIT],
    }


def _app_url(clients: NcClients, path: str) -> str:
    """An ordinary app route, always built from the configured base URL."""
    return f"{clients.creds.base_url}{path}"


async def _account_id(clients: NcClients) -> str:
    """The id of the first mail account of the impersonated user, or an empty string.

    A second read of the accounts route on purpose: ``_probe`` keeps at most ``HEAD_LIMIT``
    characters of a body, so an id cannot be recovered from a measured row, and widening the
    cap for convenience would defeat exactly the property T-08-01 asks for. This route reads
    the database only and carries no brute force counter, so a second read costs nothing.
    """
    response = await clients.client.get(
        _app_url(clients, MAIL_ACCOUNTS_PATH),
        headers=dict(ocs.OCS_HEADERS),
        auth=clients.creds.auth(),
    )
    if response.status_code != 200:
        return ""
    try:
        payload: Any = response.json()
    except ValueError:
        return ""
    entries = payload if isinstance(payload, list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("accountId", "id"):
            value = entry.get(key)
            if value not in (None, ""):
                return str(value)
    return ""


async def _walk(clients: NcClients, way: str) -> dict[str, str]:
    """Walk one way exactly once. Called through ``_row``, never directly by a test."""
    if way == "accounts":
        return await _probe(clients, "GET", _app_url(clients, MAIL_ACCOUNTS_PATH))
    if way == "mailboxes":
        account = await _account_id(clients)
        url = f"{_app_url(clients, MAIL_MAILBOXES_PATH)}?accountId={account}"
        return await _probe(clients, "GET", url)
    if way == "messages":
        url = f"{_app_url(clients, MAIL_MESSAGES_PATH)}?mailboxId={FALLBACK_MAILBOX_ID}&limit=5"
        return await _probe(clients, "GET", url)
    if way == "ocs":
        path = MAIL_MESSAGE_OCS_PATH.format(message_id=MISSING_MESSAGE_ID)
        return await _probe(clients, "GET", ocs.ocs_url(clients.creds, path))
    raise AssertionError(f"{way!r} is not one of the four measured ways {WAYS}")


async def _row(clients: NcClients, way: str) -> dict[str, str]:
    """The measured row of one way, walked at most once per session.

    The memo is what keeps the OCS full text way at one single request: it is asserted by its
    own test and printed by the protocol table, and ``messageApi#get`` carries
    ``#[BruteForceProtection('mailGetMessage')]``. Nextcloud counts that per source IP, and an
    ExApp is one address for every user of the instance, so a second request would be a second
    strike against all of them. The guard belongs here and not in the topology, because it
    travels into production code in phase 10.
    """
    cached = _measured.get(way)
    if cached is not None:
        return cached
    row = await _walk(clients, way)
    _measured[way] = row
    return row


def _verdict(row: dict[str, str]) -> str:
    """The decision rule of MAIL-04, fixed before the first measurement was taken."""
    if row["shape"] == "html":
        return "nicht erreicht"
    if "/login" in row["location"]:
        return "nicht erreicht"
    if row["shape"] == "other":
        return "nicht eindeutig"
    return "erreicht"


def _assert_reached(row: dict[str, str], way: str) -> None:
    """App code answered. Nothing more is claimed, and nothing less is accepted."""
    assert row["shape"] == "json", (
        f"the {way} way answered with shape {row['shape']!r} "
        f"(status {row['status']}, content-type {row['content_type']!r}): "
        f"an HTML body is the login page, so the controller was not reached"
    )
    assert "/login" not in row["location"], (
        f"the {way} way redirected to {row['location']!r}: authentication failed"
    )


async def test_the_accounts_way_is_answered_by_app_code(alice_clients: NcClients) -> None:
    """Way one: the cheapest of the four, and the only one that never touches IMAP."""
    _assert_reached(await _row(alice_clients, "accounts"), "accounts")


async def test_the_mailboxes_way_is_answered_by_app_code(alice_clients: NcClients) -> None:
    """Way two, with the real account id of the impersonated user.

    An error status is expected here rather than feared: ``getMailboxes`` forces an IMAP sync
    (correction K7) and the spike account points at ``imap.invalid``. ``#[TrapError]`` turns
    that into a JSON answer, which is app code and therefore a reached controller.
    """
    _assert_reached(await _row(alice_clients, "mailboxes"), "mailboxes")


async def test_the_messages_way_is_answered_by_app_code(alice_clients: NcClients) -> None:
    """Way three. ``limit=5`` is sent explicitly, see ``MAIL_MESSAGES_PATH``."""
    _assert_reached(await _row(alice_clients, "messages"), "messages")


async def test_the_ocs_full_text_way_is_answered_by_app_code(alice_clients: NcClients) -> None:
    """Way four, the only declared route of the four, with one id that exists nowhere.

    Exactly one request in the whole file, never a loop: the route carries
    ``#[BruteForceProtection('mailGetMessage')]`` (see ``_row``).
    """
    _assert_reached(await _row(alice_clients, "ocs"), "ocs")


async def test_the_four_measured_rows_are_the_protocol_of_this_spike(
    alice_clients: NcClients,
) -> None:
    """Print the four rows and hold the two negative conditions over all of them.

    The table is the deliverable: its values go into ``docs/spike-mail.md`` verbatim, which is
    why they are printed rather than only asserted. Run the file with ``-s`` to see them.
    """
    rows = {way: await _row(alice_clients, way) for way in WAYS}

    print(f"\n{'way':<10} {'status':<7} {'content-type':<34} {'shape':<6} verdict")
    for way, row in rows.items():
        print(
            f"{way:<10} {row['status']:<7} {row['content_type'][:34]:<34} "
            f"{row['shape']:<6} {_verdict(row)}"
        )
    for way, row in rows.items():
        print(f"{way:<10} head: {row['head']!r}")

    for way, row in rows.items():
        assert row["shape"] != "html", f"the {way} way answered with the login page"
        assert "/login" not in row["location"], f"the {way} way redirected to a login"
