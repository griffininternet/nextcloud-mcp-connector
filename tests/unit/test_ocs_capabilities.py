"""Unit tests for the OCS layer and the app detection behind graceful degradation.

Covered on purpose, all paths: the two mandatory headers (D-18), the fixture of a real
capabilities answer, an instance without Notes and without Deck, an HTML login page
instead of JSON, the app-JSON error format of Notes and Deck (pitfall 9), the exact
wording of the missing-app error (D-15) and the cache behaviour, including the proof that
the cache only saves latency and never changes an answer (D-20).
"""

import json
from pathlib import Path

import httpx
import pytest
import respx

from mcp_connector.errors import AppMissingError, ToolError
from mcp_connector.nextcloud import NcClients, capabilities
from mcp_connector.nextcloud.clients import ocs
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

LOGIN_PAGE = (
    '<!DOCTYPE html>\n<html class="ng-csp" data-placeholder-focus="false">\n'
    "<head><title>Login - Nextcloud</title></head>\n"
    '<body><form method="post" name="login"><input name="user"></form></body></html>\n'
)


def capabilities_fixture() -> dict:
    return json.loads((FIXTURES / "ocs_capabilities.json").read_text(encoding="utf-8"))


def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    """Every test starts with an empty cache; leaking one would hide a real call."""
    capabilities.clear_cache()


@pytest.fixture
def clients() -> NcClients:
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False),
        creds=Credentials(BASE, USER, SECRET),
    )


@pytest.mark.anyio
async def test_every_ocs_request_carries_the_two_mandatory_headers(clients: NcClients) -> None:
    """D-18: without both headers Nextcloud answers with a login page, not with JSON."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        await capabilities.load(clients)

    request = route.calls[0].request
    assert request.headers["OCS-APIRequest"] == "true"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["Authorization"].startswith("Basic ")


@pytest.mark.anyio
async def test_the_capabilities_fixture_reports_notes_and_deck(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        caps = await capabilities.load(clients)

    assert caps.notes_available is True
    assert caps.notes_api_versions == ("0.2", "1.3")
    assert caps.deck_available is True
    assert caps.deck_api_versions == ("1.0", "1.1")
    assert caps.can_create_boards is True


@pytest.mark.anyio
async def test_missing_keys_switch_the_flags_off_without_an_exception(clients: NcClients) -> None:
    """An instance without the optional apps is a normal instance, not an error."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=envelope({"capabilities": {"core": {}}}))
        )
        caps = await capabilities.load(clients)

    assert caps.notes_available is False
    assert caps.notes_api_versions == ()
    assert caps.deck_available is False
    assert caps.can_create_boards is False


@pytest.mark.anyio
async def test_a_deck_without_board_permission_is_reported_honestly(clients: NcClients) -> None:
    payload = envelope({"capabilities": {"deck": {"version": "1.18.3", "canCreateBoards": False}}})
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(200, json=payload))
        caps = await capabilities.load(clients)

    assert caps.deck_available is True
    assert caps.can_create_boards is False


@pytest.mark.anyio
async def test_an_enabled_tables_app_reports_both_api_generations(clients: NcClients) -> None:
    payload = envelope(
        {
            "capabilities": {
                "tables": {
                    "enabled": True,
                    "version": "2.2.2",
                    "apiVersions": ["1.0", "2.0"],
                    "features": ["favorite", "archive"],
                }
            }
        }
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(200, json=payload))
        caps = await capabilities.load(clients)

    assert caps.tables_available is True
    assert caps.tables_api_versions == ("1.0", "2.0")
    assert caps.has("tables") is True


@pytest.mark.anyio
async def test_an_installed_but_disabled_tables_app_counts_as_absent(clients: NcClients) -> None:
    """The one difference to Deck, and the reason the flag is not the section presence.

    Tables publishes an explicit ``enabled``. A section with ``enabled: false`` means the app
    is installed and switched off, and an app that is switched off answers no request, so
    treating the section as proof of availability would produce a 404 on an HTML page where a
    sentence belongs.
    """
    payload = envelope(
        {"capabilities": {"tables": {"enabled": False, "apiVersions": ["1.0", "2.0"]}}}
    )
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(200, json=payload))
        caps = await capabilities.load(clients)

    assert caps.tables_available is False
    assert caps.has("tables") is False


@pytest.mark.anyio
async def test_an_instance_without_a_tables_section_reports_it_as_absent(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        caps = await capabilities.load(clients)

    assert caps.tables_available is False
    assert caps.tables_api_versions == ()


def test_a_single_api_version_string_is_tolerated_for_tables() -> None:
    """An instance that answers one version as a plain string is not a broken instance."""
    caps = capabilities.parse({"capabilities": {"tables": {"enabled": True, "apiVersions": "2.0"}}})
    assert caps.tables_available is True
    assert caps.tables_api_versions == ("2.0",)


def test_has_refuses_an_app_this_server_does_not_check() -> None:
    """An unknown name is a programming error, never a silent False."""
    caps = capabilities.parse({"capabilities": {"tables": {"enabled": True}}})
    assert caps.has("tables") is True
    with pytest.raises(ValueError, match="spreed"):
        caps.has("spreed")


@pytest.mark.anyio
async def test_require_app_names_the_missing_tables_app_and_an_alternative(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(
                200, json=envelope({"capabilities": {"tables": {"enabled": False}}})
            )
        )
        with pytest.raises(AppMissingError) as excinfo:
            await capabilities.require_app(clients, "tables")

    assert excinfo.value.message == "The Tables app is not enabled on this Nextcloud."
    assert "Tables app" in excinfo.value.hint
    assert excinfo.value.hint != excinfo.value.message


@pytest.mark.anyio
async def test_an_html_login_page_explains_itself_instead_of_raising_a_keyerror(
    clients: NcClients,
) -> None:
    """The classic symptom of a missing OCS-APIRequest header (pitfall 9)."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(
                200, text=LOGIN_PAGE, headers={"content-type": "text/html; charset=UTF-8"}
            )
        )
        with pytest.raises(ToolError) as excinfo:
            await capabilities.load(clients)

    assert "HTML" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_rejected_app_password_is_reported_and_never_retried(clients: NcClients) -> None:
    """Nextcloud counts failures per source IP; a retry would slow down every user."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(401, json={}))
        with pytest.raises(ToolError) as excinfo:
            await capabilities.load(clients)

    assert route.call_count == 1, "an authentication failure is never repeated"
    assert "app password" in excinfo.value.message.lower()


@pytest.mark.anyio
async def test_an_ocs_error_envelope_becomes_a_tool_error(clients: NcClients) -> None:
    payload = {
        "ocs": {
            "meta": {
                "status": "failure",
                "statuscode": 400,
                "message": "No valid filters provided",
            },
            "data": [],
        }
    }
    with respx.mock(assert_all_called=True) as mock:
        mock.get(f"{BASE}/ocs/v2.php/search/providers/notes/search").mock(
            return_value=httpx.Response(400, json=payload)
        )
        response = await ocs.ocs_get(
            clients.client, clients.creds, "/search/providers/notes/search", params={"term": ""}
        )
        with pytest.raises(ToolError) as excinfo:
            ocs.parse_ocs(response, what="the note search")

    assert "No valid filters provided" in f"{excinfo.value.message} {excinfo.value.hint}"


@pytest.mark.anyio
async def test_parse_app_json_reads_the_notes_and_deck_error_format(clients: NcClients) -> None:
    """Notes and Deck answer ``{"status": 4xx, "message": ...}``, not an OCS envelope."""
    url = f"{BASE}/index.php/apps/notes/api/v1/notes/999"
    with respx.mock(assert_all_called=True) as mock:
        mock.get(url).mock(
            return_value=httpx.Response(404, json={"status": 404, "message": "Note not found"})
        )
        response = await clients.client.get(url)
        with pytest.raises(ToolError) as excinfo:
            ocs.parse_app_json(response, what="the note")

    assert "Note not found" in f"{excinfo.value.message} {excinfo.value.hint}"


def test_parse_app_json_returns_the_payload_of_a_successful_answer() -> None:
    response = httpx.Response(200, json={"id": 12, "title": "Protokoll"})
    assert ocs.parse_app_json(response, what="the note") == {"id": 12, "title": "Protokoll"}


def test_parse_ocs_and_parse_app_json_are_separate_functions() -> None:
    """One envelope parser per API family; mixing them is exactly pitfall 9."""
    assert callable(ocs.parse_ocs)
    assert callable(ocs.parse_app_json)
    assert ocs.parse_ocs is not ocs.parse_app_json


@pytest.mark.anyio
async def test_require_app_names_the_missing_notes_app_and_an_alternative(
    clients: NcClients,
) -> None:
    """D-15, exact wording: the sentence a user can act on without reading our code."""
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=envelope({"capabilities": {}}))
        )
        with pytest.raises(AppMissingError) as excinfo:
            await capabilities.require_app(clients, "notes")

    assert excinfo.value.message == "The Notes app is not installed on this Nextcloud."
    assert "Notes app" in excinfo.value.hint
    assert excinfo.value.hint != excinfo.value.message


@pytest.mark.anyio
async def test_require_app_also_covers_deck(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=envelope({"capabilities": {"notes": {}}}))
        )
        with pytest.raises(AppMissingError) as excinfo:
            await capabilities.require_app(clients, "deck")

    assert excinfo.value.message == "The Deck app is not installed on this Nextcloud."


@pytest.mark.anyio
async def test_require_app_returns_the_capabilities_when_the_app_is_there(
    clients: NcClients,
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        caps = await capabilities.require_app(clients, "notes")

    assert caps.notes_available is True


@pytest.mark.anyio
async def test_two_calls_within_the_ttl_make_exactly_one_http_call(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        first = await capabilities.load(clients)
        second = await capabilities.load(clients)

    assert route.call_count == 1, "the second call inside the TTL is served from the cache"
    assert first == second


@pytest.mark.anyio
async def test_an_expired_entry_is_fetched_again(
    clients: NcClients, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cache is a latency optimisation and may be empty at any time (D-20)."""
    monkeypatch.setattr(capabilities, "TTL_SECONDS", 0.0)
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        first = await capabilities.load(clients)
        second = await capabilities.load(clients)

    assert route.call_count == 2
    assert first == second, "an empty cache never changes the answer, only the latency"


@pytest.mark.anyio
async def test_the_cache_is_kept_per_credential_context(clients: NcClients) -> None:
    """Two users on the same instance never share an entry (threat T-01-42)."""
    other = NcClients(client=clients.client, creds=Credentials(BASE, "bob", "another-app-password"))
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(200, json=capabilities_fixture())
        )
        await capabilities.load(clients)
        await capabilities.load(other)

    assert route.call_count == 2


@pytest.mark.anyio
async def test_a_server_error_is_reported_as_a_degraded_answer(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(503, text="service down"))
        with pytest.raises(ToolError) as excinfo:
            await capabilities.load(clients)

    assert "503" in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.anyio
async def test_a_redirect_is_never_followed(clients: NcClients) -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(
            return_value=httpx.Response(302, headers={"location": "https://elsewhere.test/"})
        )
        with pytest.raises(ToolError) as excinfo:
            await capabilities.load(clients)

    assert "redirect" in excinfo.value.message.lower()
