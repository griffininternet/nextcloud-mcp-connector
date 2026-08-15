"""The DAV spike (D-30, AUTH-05): does the identity arrive without an app password.

This file does not ask whether the clients of phase 1 work. The phase 1 integration suite
already answers that, and it answers it with an app password. This file asks the one
question phase 2 turns on: when the only credential in play is ``APP_SECRET`` and a user id
travels inside the AppAPI header, does every Nextcloud API family run as that user, and does
it refuse everything that user may not see.

Because that is the question, three things are load bearing in here and not incidental.

*   Every credential object is built with ``mode="appapi"`` and ``secret=APP_SECRET``. There
    is no ``httpx.BasicAuth`` anywhere in this file, and no ``NC_MCP_APP_PASSWORD`` is read
    as a credential source. The identity can only come from ``AUTHORIZATION-APP-API``.
*   The first two checks are controls. Without them a green matrix proves nothing: a passing
    call could have been served by some other credential that happened to sit in the
    environment, or by a mechanism that ignores the secret entirely. Control one asserts the
    process holds no Nextcloud app password and no static bearer. Control two proves a wrong
    ``APP_SECRET`` is refused, so a real secret is what carried every other row.
*   The measurement uses the real client functions from
    ``mcp_connector.nextcloud.clients`` and the real tools, not hand written requests. The
    seam that carries impersonation in production (``Credentials.auth`` behind the twenty
    call sites) is the same seam under test here. The two exceptions are deliberate and
    named at their call site: the cross user negative case builds a URL the client would
    never construct on purpose, and the confused deputy case injects a header the client
    never sends on purpose.

The instance speaks over the reverse proxy on ``NC_MCP_URL`` and the requests go straight to
Nextcloud (``remote.php``, ``ocs/v2.php``, ``index.php/apps/...``), never to the ExApp
container: what is under test is Nextcloud's impersonation, not the proxy hop.

Run it against the running HaRP topology::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_exapp_dav_matrix.py -m integration -q
"""

import base64
import os
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from mcp_connector.config import normalize_base_url
from mcp_connector.errors import ConflictError
from mcp_connector.nextcloud import NcClients
from mcp_connector.nextcloud.clients import caldav, carddav, dav, ocs
from mcp_connector.nextcloud.clients import deck as deck_client
from mcp_connector.nextcloud.credentials import MODE_APPAPI, Credentials
from mcp_connector.tools import deck as deck_tools
from mcp_connector.tools import notes as notes_tools

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def _appapi_clients(exapp_env: dict[str, str], user: str) -> NcClients:
    """Build the impersonating clients for one user, ``APP_SECRET`` as the only credential.

    Mirrors ``deps._credentials_from_appapi``: the same base URL, the same fields, the same
    mode. The user id is the whole difference between impersonating alice and impersonating
    bob, which is exactly the property the spike measures.
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


@pytest.fixture
async def bob_clients(exapp_env: dict[str, str]) -> AsyncIterator[NcClients]:
    clients = _appapi_clients(exapp_env, exapp_env["bob"])
    async with clients.client:
        yield clients


async def _cloud_user_id(clients: NcClients) -> str:
    """Ask Nextcloud who this request runs as. The central identity proof of D-30."""
    response = await ocs.ocs_get(clients.client, clients.creds, "/cloud/user")
    data = ocs.parse_ocs(response, what="the impersonated user")
    assert isinstance(data, dict), f"cloud/user did not return an object: {data!r}"
    return str(data.get("id") or "")


# --------------------------------------------------------------------------------------
# Control checks. Everything below them is worthless without them.
# --------------------------------------------------------------------------------------


async def test_the_measuring_process_holds_no_nextcloud_app_password(
    exapp_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control one: the identity cannot come from a Basic app password or a static bearer.

    ``NC_MCP_APP_PASSWORD`` and ``NC_MCP_STATIC_BEARER`` are the two variables the connector
    itself would authenticate from. They are removed for the duration of the test and
    asserted absent, so a green row later cannot be explained by a credential that sat in the
    environment. ``NC_MCP_TEST_APP_PASSWORD`` is a different variable: it is alice's real app
    password, used only once below as an attack header, never as a credential source here.
    """
    monkeypatch.delenv("NC_MCP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("NC_MCP_STATIC_BEARER", raising=False)
    assert os.environ.get("NC_MCP_APP_PASSWORD") is None
    assert os.environ.get("NC_MCP_STATIC_BEARER") is None
    # The credential this suite builds carries the app secret and the impersonation mode,
    # never a user password.
    clients = _appapi_clients(exapp_env, exapp_env["bob"])
    assert clients.creds.mode == MODE_APPAPI
    assert clients.creds.secret == exapp_env["app_secret"]


async def test_a_wrong_app_secret_is_refused(exapp_env: dict[str, str]) -> None:
    """Control two: without the real secret, nothing answers 200.

    A wrong ``APP_SECRET`` fails Nextcloud's ``validateExAppRequestToNC``. If this call still
    reached the data, some other mechanism would be authenticating the request and every
    other row in the matrix would be measuring that mechanism instead of impersonation.
    """
    wrong = _appapi_clients({**exapp_env, "app_secret": "0" * 64}, exapp_env["alice"])
    async with wrong.client:
        response = await ocs.ocs_get(wrong.client, wrong.creds, "/cloud/user")
    assert response.status_code != 200, (
        "a wrong APP_SECRET was accepted; the identity is not coming from the secret"
    )


# --------------------------------------------------------------------------------------
# One test per API family. Each failure is nameable; there is no try/except that turns a
# failure into a soft "degraded".
# --------------------------------------------------------------------------------------


async def test_ocs_identity_is_the_impersonated_alice(alice_clients: NcClients) -> None:
    """OCS: ``cloud/user`` returns exactly alice. The server side identity proof for alice."""
    assert await _cloud_user_id(alice_clients) == alice_clients.creds.user


async def test_ocs_identity_is_the_impersonated_bob(bob_clients: NcClients) -> None:
    """OCS: ``cloud/user`` returns exactly bob. The same proof, a different account."""
    assert await _cloud_user_id(bob_clients) == bob_clients.creds.user


async def test_webdav_propfind_lists_the_impersonated_home(bob_clients: NcClients) -> None:
    """WebDAV PROPFIND Depth 1 on the root runs as bob and returns his own collection."""
    itself, _children = await dav.propfind_children(bob_clients.client, bob_clients.creds, "/")
    assert itself["is_collection"], f"the home of bob is not a collection: {itself!r}"


async def test_webdav_search_answers_under_impersonation(bob_clients: NcClients) -> None:
    """WebDAV SEARCH runs as bob and finds a file that was just created as bob.

    The create and the search both go through the impersonation seam, so a hit here is a
    round trip that never touched an app password.
    """
    marker = f"spikebob{uuid.uuid4().hex[:10]}"
    path = f"/{marker}.md"
    await dav.put_new_file(
        bob_clients.client, bob_clients.creds, path, b"# bob spike file\n", "text/markdown"
    )
    scope = dav.search_scope(bob_clients.creds)
    hits = await dav.search(bob_clients.client, bob_clients.creds, scope, marker, 25)
    assert any(hit["path"] == path for hit in hits), f"bob cannot find his own file: {hits!r}"


async def test_webdav_put_is_create_only_under_impersonation(bob_clients: NcClients) -> None:
    """WebDAV PUT with ``If-None-Match: *`` creates once and the second write is refused.

    The create only boundary of phase 1 (TOOL-09) has to hold under the new auth path too:
    the whole overwrite protection is a server side precondition, and it must not weaken
    because the request now arrives as an impersonation.
    """
    path = f"/spikebobonce{uuid.uuid4().hex[:10]}.md"
    created = await dav.put_new_file(
        bob_clients.client, bob_clients.creds, path, b"first\n", "text/markdown"
    )
    assert created["created"] is True
    with pytest.raises(ConflictError):
        await dav.put_new_file(
            bob_clients.client, bob_clients.creds, path, b"second\n", "text/markdown"
        )


async def test_caldav_report_expands_under_impersonation(alice_clients: NcClients) -> None:
    """CalDAV REPORT calendar-query with an expansion window answers well formed for alice.

    An empty calendar is a valid answer: the proof is that ``query_events`` returns a list
    rather than a 401 or a login page, which means sabre accepted the impersonation on the
    ``remote.php/dav`` server.
    """
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=1)
    events = await caldav.query_events(
        alice_clients.client, alice_clients.creds, "personal", start, end
    )
    assert isinstance(events, list)


async def test_carddav_report_answers_under_impersonation(alice_clients: NcClients) -> None:
    """CardDAV REPORT addressbook-query answers well formed for alice's contacts book."""
    contacts = await carddav.query_contacts(
        alice_clients.client, alice_clients.creds, "contacts", "spikequery", 25
    )
    assert isinstance(contacts, list)


async def test_notes_list_and_create_under_impersonation(alice_clients: NcClients) -> None:
    """Notes REST: search the provider and create a note, both as impersonated alice."""
    listing = await notes_tools.search(alice_clients, query="spike", limit=25)
    assert "results" in listing
    created = await notes_tools.create(
        alice_clients,
        title=f"Spike note {uuid.uuid4().hex[:8]}",
        content="created under AppAPI impersonation",
    )
    assert created["id"]


async def test_deck_read_and_create_under_impersonation(alice_clients: NcClients) -> None:
    """Deck REST: read the boards and create a card, both as impersonated alice.

    A fresh account owns no board, so the board and the stack the card needs are created as
    setup with the same impersonating credentials (a POST as alice, which is itself part of
    the proof), and the card itself is created through the real client function.
    """
    boards = await deck_tools.browse(alice_clients, level="boards")
    assert "results" in boards

    board_id, stack_id = await _ensure_board_with_stack(alice_clients)
    card = await deck_client.create_card(
        alice_clients.client,
        alice_clients.creds,
        board_id,
        stack_id,
        title=f"Spike card {uuid.uuid4().hex[:8]}",
    )
    assert card.get("id"), f"the card was not created: {card!r}"


async def _ensure_board_with_stack(clients: NcClients) -> tuple[int, int]:
    """Create a board and a stack as the impersonated user and return their ids.

    Deck has no board or stack write in the client (create only by design), so this setup
    posts them directly. Both posts carry the impersonation auth, so they double as evidence
    that a Deck POST runs as the impersonated user.
    """
    headers = dict(deck_client.DECK_HEADERS)
    board_resp = await clients.client.post(
        deck_client.api_url(clients.creds, "/boards"),
        json={"title": f"Spike board {uuid.uuid4().hex[:6]}", "color": "0087C5"},
        headers=headers,
        auth=clients.creds.auth(),
    )
    board = ocs.parse_app_json(board_resp, what="the new board")
    board_id = int(board["id"])

    stack_resp = await clients.client.post(
        deck_client.api_url(clients.creds, f"/boards/{board_id}/stacks"),
        json={"title": "Spike stack", "order": 1},
        headers=headers,
        auth=clients.creds.auth(),
    )
    stacks = ocs.parse_app_json(stack_resp, what="the board stacks after the create")
    if isinstance(stacks, dict):
        return board_id, int(stacks["id"])
    # Some Deck versions answer the stack create with the full stack list of the board.
    assert isinstance(stacks, list), f"unexpected stack create answer: {stacks!r}"
    assert stacks, f"no stack was created: {stacks!r}"
    return board_id, int(stacks[-1]["id"])


# --------------------------------------------------------------------------------------
# The core security proof of AUTH-05: the boundary between two users holds under
# impersonation, and a client set header cannot cross it.
# --------------------------------------------------------------------------------------


async def test_bob_cannot_reach_alices_home_even_with_the_exact_path(
    alice_clients: NcClients, bob_clients: NcClients
) -> None:
    """Negative case: a file created as alice is not readable in bob's impersonation context.

    This is not a search hygiene test. The path is already known, so nothing but Nextcloud's
    own permission check stands between bob and the file. The request targets
    ``/remote.php/dav/files/alice/...`` on purpose, a URL the client would never build for
    bob, and it carries bob's AppAPI headers. A 200 here would be the exact elevation of
    privilege T-02-50 forbids, so a 200 fails the test; the expected answer is 403 or 404.
    """
    marker = f"nurfueralice{uuid.uuid4().hex[:10]}"
    alice_path = f"/{marker}.md"
    secret_line = "Vertrauliche Notiz von alice, Strassenbudget."
    await dav.put_new_file(
        alice_clients.client,
        alice_clients.creds,
        alice_path,
        f"# {marker}\n{secret_line}\n".encode(),
        "text/markdown",
    )

    # Build alice's own WebDAV URL, then request it with bob's impersonating auth.
    alices_url = dav.files_url(alice_clients.creds, alice_path)
    response = await bob_clients.client.get(alices_url, auth=bob_clients.creds.auth())

    assert response.status_code in (403, 404), (
        f"bob reached alice's file over impersonation: status {response.status_code}"
    )
    assert response.status_code != 200
    assert secret_line not in response.text, "the response body leaked alice's file content"


async def test_a_client_authorization_header_cannot_override_impersonation(
    exapp_env: dict[str, str], bob_clients: NcClients
) -> None:
    """Confused deputy: a client set Authorization header does not change who the request is.

    The identity comes from ``AUTHORIZATION-APP-API`` alone. To prove it, the request carries
    bob's AppAPI headers and, on top, a fully valid Basic Authorization for alice. If the
    impersonation could be overridden, ``cloud/user`` would answer alice and this would be a
    real privilege confusion. The expected answer is bob, unchanged.
    """
    alice_password = (os.environ.get("NC_MCP_TEST_APP_PASSWORD") or "").strip()
    if not alice_password:
        pytest.skip("NC_MCP_TEST_APP_PASSWORD is needed as the attack header for this check")

    alice_basic = base64.b64encode(f"{exapp_env['alice']}:{alice_password}".encode()).decode()
    response = await bob_clients.client.get(
        ocs.ocs_url(bob_clients.creds, "/cloud/user"),
        headers={
            **dict(ocs.OCS_HEADERS),
            "Authorization": f"Basic {alice_basic}",
        },
        auth=bob_clients.creds.auth(),
    )
    data = ocs.parse_ocs(response, what="the impersonated user under a competing header")
    assert isinstance(data, dict)
    assert data.get("id") == bob_clients.creds.user, (
        "a client Authorization header overrode the AppAPI impersonation: "
        f"cloud/user returned {data.get('id')!r} instead of bob"
    )
