"""Unit tests for the provider table and the id extraction of unified search entries.

Pitfall 10 in one sentence: a unified search entry has no ``id`` field, so every id in
this project is either read out of ``attributes`` (only Files fills it), parsed out of
``resourceUrl``, or honestly marked as not resolvable. These tests pin all three outcomes,
including the two that are easy to get wrong: an unknown provider must never be guessed
into a known kind, and a ``resourceUrl`` from a foreign host must never survive into the
answer (threat T-01-68).
"""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_connector import provider_map

BASE = "http://nc.test"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def files_entries() -> list[dict[str, Any]]:
    return fixture("ocs_search_files.json")["ocs"]["data"]["entries"]


def test_a_files_hit_takes_its_id_from_the_attributes() -> None:
    """Only the files provider fills ``attributes.fileId``, and it is the cheapest source."""
    kind, identifier, canonical = provider_map.extract_id("files", files_entries()[0], BASE)

    assert kind == "file"
    assert identifier == "file:4711"
    assert canonical is True


def test_a_files_hit_without_attributes_falls_back_to_the_f_segment() -> None:
    """``attributes`` is an empty list on some instances; ``/f/<fileid>`` still resolves."""
    kind, identifier, canonical = provider_map.extract_id("files", files_entries()[1], BASE)

    assert kind == "file"
    assert identifier == "file:4712"
    assert canonical is True


def test_a_notes_hit_takes_its_id_from_the_last_url_segment() -> None:
    """The notes provider ships no ``attributes`` at all (verified in the notes app)."""
    entry = {"title": "Protokoll", "resourceUrl": f"{BASE}/index.php/apps/notes/note/12"}

    assert provider_map.extract_id("notes", entry, BASE) == ("note", "note:12", True)


def test_a_deck_hit_becomes_the_short_card_form_and_is_not_canonical() -> None:
    """``search-deck-card-board`` only ever delivers the cardId, never board and stack."""
    entry = {"title": "Karte", "resourceUrl": "/apps/deck/card/57"}

    kind, identifier, canonical = provider_map.extract_id("search-deck-card-board", entry, BASE)

    assert kind == "card"
    assert identifier == "card:57"
    assert canonical is False, "board and stack are missing, so this id needs a sweep"


def test_an_unknown_provider_becomes_a_url_and_is_never_guessed() -> None:
    """An honest boundary beats a wrong resolution (pitfall 10)."""
    entry = {"title": "Talk", "resourceUrl": "/call/abc123#message_42"}

    kind, identifier, canonical = provider_map.extract_id("spreed", entry, BASE)

    assert kind == "url"
    assert identifier == f"url:{BASE}/call/abc123#message_42"
    assert canonical is False


def test_an_entry_without_a_resource_url_and_without_attributes_is_skipped() -> None:
    assert provider_map.extract_id("files", {"title": "kaputt"}, BASE) is None
    assert provider_map.extract_id("spreed", {"title": "kaputt", "attributes": []}, BASE) is None


def test_a_known_provider_with_an_unusable_url_degrades_to_the_url_kind() -> None:
    """A wrong note id would read a different note; the url stays honest instead."""
    entry = {"title": "kaputt", "resourceUrl": "/index.php/apps/notes/"}

    kind, identifier, canonical = provider_map.extract_id("notes", entry, BASE)

    assert kind == "url"
    assert identifier == f"url:{BASE}/index.php/apps/notes/"
    assert canonical is False


def test_attributes_are_read_as_an_object_and_a_missing_key_is_no_error() -> None:
    """The server annotation says ``list<string>``; the wire format is an object."""
    entry = {"resourceUrl": f"{BASE}/index.php/f/8", "attributes": {"path": "Docs/x.md"}}

    assert provider_map.extract_id("files", entry, BASE) == ("file", "file:8", True)


def test_a_foreign_resource_url_is_rebuilt_on_the_configured_base_url() -> None:
    """The url is only ever parsed, never fetched, and never left pointing elsewhere."""
    entry = {"title": "geklaut", "resourceUrl": "http://evil.test/index.php/apps/notes/note/5"}

    _, identifier, _ = provider_map.extract_id("notes", entry, BASE)
    url = provider_map.hit_url(BASE, "note", identifier, entry)

    assert identifier == "note:5"
    assert url == f"{BASE}/index.php/apps/notes/note/5"
    assert "evil.test" not in url


@pytest.mark.parametrize(
    ("provider_id", "entry"),
    [
        ("files", {"resourceUrl": f"{BASE}/index.php/f/4711"}),
        ("files", {"attributes": {"fileId": "4711"}}),
        ("notes", {"resourceUrl": "/index.php/apps/notes/note/12"}),
        ("search-deck-card-board", {"resourceUrl": "/apps/deck/card/57"}),
        ("spreed", {"resourceUrl": "/call/abc123"}),
    ],
)
def test_every_hit_carries_an_absolute_non_empty_url(
    provider_id: str, entry: dict[str, Any]
) -> None:
    """ChatGPT only builds a citation when ``url`` is a non-empty, openable string."""
    resolved = provider_map.extract_id(provider_id, entry, BASE)
    assert resolved is not None

    kind, identifier, _ = resolved
    url = provider_map.hit_url(BASE, kind, identifier, entry)

    assert url.startswith(f"{BASE}/"), url
    assert url != BASE


def test_the_provider_table_knows_the_real_deck_provider_id() -> None:
    """It is ``search-deck-card-board``, not ``deck``, and that is worth a test."""
    assert provider_map.PROVIDER_KINDS["search-deck-card-board"] == "card"
    assert "deck" not in provider_map.PROVIDER_KINDS


def test_the_provider_table_is_not_a_list_of_installed_apps() -> None:
    """The runtime list comes from Nextcloud; this table only maps ids to kinds."""
    assert set(provider_map.PROVIDER_KINDS) == {"files", "notes", "search-deck-card-board"}
