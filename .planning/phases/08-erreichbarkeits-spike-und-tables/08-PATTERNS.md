# Phase 8: Erreichbarkeits-Spike und Tables, Muster-Karte

**Kartiert:** 2026-08-21
**Analysierte Dateien:** 20 (5 Produktionscode, 8 Tests und Fixtures, 7 Skripte/Doku/Topologie)
**Analoga gefunden:** 20 / 20 (13 exakt, 6 Rollen-Treffer, 1 Teil-Treffer)

> Diese Datei sagt dem Planer, **von welcher bestehenden Datei jede neue Datei ihr Muster
> kopiert** und welche Zeilen dabei wörtlich als Vorbild dienen. Sie ersetzt nicht die
> Recherche (`08-RESEARCH.md`), sondern liefert die konkreten Code-Auszüge, auf die die
> Plan-Aktionen zeigen können.
>
> Grundbefund: Tables ist mechanisch ein zweiter Deck. Die Familie Deck existiert vollständig
> in allen sieben Schichten (Client, Tool, Registrierung, Capability, Unit-Tests,
> Integrationstest, Contract-Test), und jede neue Tables-Datei hat dort genau ein Gegenstück.
> Der Mail-Spike ist die einzige Datei mit einem nur teilweise passenden Vorbild.

## Datei-Klassifikation

### Produktionscode

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Treffergüte |
|----------------------|-------|------------|-----------------|-------------|
| `src/mcp_connector/nextcloud/clients/tables.py` (NEU) | client (HTTP-Adapter einer App-Familie) | request-response, lesend plus ein Create | `src/mcp_connector/nextcloud/clients/deck.py` | exakt |
| `src/mcp_connector/nextcloud/clients/ocs.py` (`ocs_post`) | transport-Naht | request-response, schreibend | `ocs_get` im selben Modul, Zeilen 64-83 | exakt (Selbst-Analog) |
| `src/mcp_connector/nextcloud/capabilities.py` (GEÄNDERT) | discovery/config-Service mit Cache | request-response, gecacht (TTL 60 s) | die `deck`-Zweige derselben Datei, Zeilen 41-56, 59-76, 119-135 | exakt (Selbst-Analog) |
| `src/mcp_connector/tools/tables.py` (NEU) | tool (Fachlogik, Projektion, Fehlersätze) | transform plus CRUD-Create | `src/mcp_connector/tools/deck.py` | exakt |
| `src/mcp_connector/server/reg_tables.py` (NEU) | registration (Schema, Annotationen) | request-response | `src/mcp_connector/server/reg_deck.py` | exakt |

### Tests und Fixtures

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Treffergüte |
|----------------------|-------|------------|-----------------|-------------|
| `tests/unit/test_tables_client.py` (NEU) | test (unit, respx) | request-response, gemockt | `tests/unit/test_deck_client.py` | exakt |
| `tests/unit/test_tables_tools.py` (NEU) | test (unit, respx) | transform | `tests/unit/test_deck_tools.py` | exakt |
| `tests/integration/test_tables_roundtrip.py` (NEU) | test (integration, echte Instanz) | CRUD-Roundtrip | `tests/integration/test_deck_roundtrip.py` | exakt |
| `tests/integration/test_exapp_mail_reach.py` (NEU) | test (integration, Spike-Messung) | request-response, protokollierend statt behauptend | `tests/integration/test_exapp_dav_matrix.py` | Rollen-Treffer (siehe Teil-Treffer-Hinweis unten) |
| `tests/contract/test_tool_surface.py` (GEÄNDERT) | test (contract) | statische Registry-Prüfung | die Deck-Tests derselben Datei, Zeilen 199-236 | exakt (Selbst-Analog) |
| `tests/contract/test_no_destructive_calls.py` (GEÄNDERT) | test (contract, AST-Gate) | statische Quellcode-Prüfung | `FORBIDDEN` plus Gegenproben derselben Datei, Zeilen 32-48, 187-232 | exakt (Selbst-Analog) |
| `tests/unit/test_ocs_capabilities.py` (GEÄNDERT) | test (unit) | request-response, gemockt | die Deck-Fälle derselben Datei, Zeilen 80-120, 220-231 | exakt (Selbst-Analog) |
| `tests/fixtures/tables_tables.json`, `tables_columns.json`, `tables_rows_simple.json` (NEU) | fixture | Daten | `tests/fixtures/deck_boards.json`, `deck_stacks.json` | exakt |

### Skripte, Doku, Topologie

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Treffergüte |
|----------------------|-------|------------|-----------------|-------------|
| `scripts/check_tool_budget.py` (GEÄNDERT) | gate/script | batch | Messkommentar plus `BUDGET_BYTES` derselben Datei, Zeilen 16-27 | exakt (Selbst-Analog) |
| `scripts/acceptance_all_tools.py` (GEÄNDERT) | script | batch | `EXPECTED_TOOLS` derselben Datei, Zeilen 1, 16, 44, 103-104 | exakt (Selbst-Analog) |
| `scripts/bootstrap_exapp.sh` (GEÄNDERT) | script (Topologie-Bootstrap) | batch, idempotent | `ensure_app`, Zeilen 251-265, Aufrufe 849-850 | exakt (Selbst-Analog) |
| `scripts/bootstrap_test_nc.sh` (GEÄNDERT) | script | batch, idempotent | `ensure_app`, Zeile 76, Aufrufe 159-160 | exakt (Selbst-Analog) |
| `docs/spike-mail.md` (NEU) | doku (Messprotokoll) | Bericht | `docs/spike-dav.md` | Rollen-Treffer |
| `README.md`, `README.de.md`, `README.fr.md` (GEÄNDERT) | doku | Tabelle | Deck-Zeile der Tool-Tabelle, `README.md` Zeile 196 | exakt |
| `CHANGELOG.md` (GEÄNDERT) | doku | Bericht | Block `## [0.1.3]`, Zeilen 12-40 | exakt |
| `compose.exapp.yml` (OPTIONAL, GreenMail) | config (Topologie) | Dienst | Dienst `registry`, Zeilen 124-137 | Rollen-Treffer |

**Unverändert laut Recherche und deshalb hier ohne Zuordnung:** `src/mcp_connector/ids.py`,
`src/mcp_connector/provider_map.py`, `src/mcp_connector/tools/context.py`,
`appinfo/info.xml`.

## Muster-Zuweisungen

### `src/mcp_connector/nextcloud/clients/tables.py` (client, request-response)

**Analog:** `src/mcp_connector/nextcloud/clients/deck.py` (236 Zeilen, komplett gelesen)

**Modul-Docstring-Muster** (deck.py Zeilen 1-28): der Docstring dieser Client-Module ist kein
Kommentar, sondern der Ort, an dem die Pflichtheader, die Parser-Wahl, die Generationswahl und
das ausdrückliche Fehlen von Update und Delete stehen. Für Tables kommen die zwei Generationen
(K9), die zwei Schreibweisen `nodeType`/`nodeCollection` (K3) und das erzwungene `limit` (Falle
1) an genau diese Stelle. Wörtliches Vorbild, gekürzt:

```python
"""Deck REST v1.0 client: boards, stacks including their cards, and one create path.

The API lives at ``/index.php/apps/deck/api/v1.0`` and it is the strictest of the JSON
APIs this project speaks. Two headers are mandatory on **every** request, a plain GET
included: ``OCS-APIRequest: true`` and ``Content-Type: application/json`` (D-18). ...

Three local guards keep doomed requests from ever leaving, because a refused request is
cheaper than a 400 and its message is better:

* ids that go into the URL path must be digits (threat T-01-63)
...
There is deliberately no update, no delete and no board or stack write in this module. The
server promise is that it can neither overwrite nor remove anything, and the cheapest way
to keep it is to never write the code that could break it (threat T-01-62).
"""
```

**Imports-Muster** (deck.py Zeilen 30-38):

```python
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import httpx

from ...errors import ToolError
from ..credentials import Credentials
from . import ocs
```

Relative Drei-Punkt-Imports für `errors`, Zwei-Punkt für `credentials`, `from . import ocs`
für die Parser. Keine Barrel-Imports, kein Pfad-Alias.

**Konstanten-Muster** (deck.py Zeilen 40-67): jede Konstante trägt einen `#:`-Kommentar, der
die Entscheidung begründet, nicht den Wert wiederholt.

```python
#: The API generation this client speaks. 1.0 instead of 1.1 on purpose: 1.1 only adds
#: attachment types we do not use, and 1.0 is available on more instances.
SUPPORTED_API_VERSION = "1.0"

#: Base path of the Deck REST API. ``index.php`` is not optional on every instance.
DECK_API_PREFIX = f"/index.php/apps/deck/api/v{SUPPORTED_API_VERSION}"

#: Web route of a single card (``deck.page.redirectToCard``), used for the ``url`` field.
DECK_WEB_PREFIX = "/index.php/apps/deck/card"

#: The two mandatory headers of D-18, plus the ``Accept`` that keeps a proxy from
#: negotiating HTML. Copied per request, never mutated in place.
DECK_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

**URL-Bau-Muster** (deck.py Zeilen 70-79): ein `api_url`-Helfer mit Slash-Wächter plus ein
`web_url` für das Feld, das ein Mensch anklickt. Tables braucht davon zwei Varianten, weil
zwei Generationen im Spiel sind: die v1-Variante nach diesem Vorbild, die v2-Variante über
`ocs.ocs_url(creds, "/apps/tables/api/2/...")`.

```python
def api_url(creds: Credentials, path: str = "") -> str:
    """Build a Deck API URL; ``path`` is empty or starts with a slash."""
    if path and not path.startswith("/"):
        raise ValueError(f"a Deck path must start with a slash (got {path!r})")
    return f"{creds.base_url}{DECK_API_PREFIX}{path}"


def web_url(creds: Credentials, card_id: str | int) -> str:
    """The link a human can open. Always built from the configured base URL."""
    return f"{creds.base_url}{DECK_WEB_PREFIX}/{card_id}"
```

**Lesender Aufruf** (deck.py Zeilen 108-123): Signatur `(client, creds, id, *, ...)`, Wächter
zuerst, `headers=dict(...)`, `auth=creds.auth()` pro Aufruf, Parser danach, Formprüfung als
letzter Schritt.

```python
async def get_stacks(
    client: httpx.AsyncClient, creds: Credentials, board_id: str | int
) -> list[dict[str, Any]]:
    """List the stacks of a board; the answer already contains their cards.

    This is the single request behind ``deck_browse(level="cards")``. Asking every stack
    for its cards separately would be an N+1 over a payload Deck already sent.
    """
    board = _path_id(board_id, "board id")
    response = await client.get(
        api_url(creds, f"/boards/{board}/stacks"),
        headers=dict(DECK_HEADERS),
        auth=creds.auth(),
    )
    payload = ocs.parse_app_json(response, what=f"the stacks of board {board}")
    return _as_list(payload, what="stacks")
```

**Schreibender Aufruf** (deck.py Zeilen 145-175): Body wird lokal gebaut, optionale Felder nur
wenn gesetzt, kein Retry, Antwort durch denselben Parser.

```python
async def create_card(
    client: httpx.AsyncClient,
    creds: Credentials,
    board_id: str | int,
    stack_id: str | int,
    *,
    title: str,
    description: str | None = None,
    duedate: str | None = None,
    order: int = DEFAULT_CARD_ORDER,
) -> dict[str, Any]:
    """Create one card in an existing stack and return the object Deck stored."""
    board = _path_id(board_id, "board id")
    stack = _path_id(stack_id, "stack id")
    body: dict[str, Any] = {
        "title": check_title(title),
        "type": CARD_TYPE,
        "order": order,
    }
    if description:
        body["description"] = description
    ...
    response = await client.post(
        api_url(creds, f"/boards/{board}/stacks/{stack}/cards"),
        json=body,
        headers=dict(DECK_HEADERS),
        auth=creds.auth(),
    )
    return _as_dict(ocs.parse_app_json(response, what="the new card"), what="a card")
```

Für Tables geht der POST stattdessen durch die neue Naht `ocs.ocs_post` (K9), der Rest der
Form bleibt gleich.

**Pfad-Id-Wächter** (deck.py Zeilen 210-218): wörtlich übernehmbar, nur der Hinweistext wird
auf `tables_browse` umgeschrieben.

```python
def _path_id(value: str | int, what: str) -> str:
    """Ids are numeric in Deck; anything else is a bug or an attempt (threat T-01-63)."""
    text = str(value).strip()
    if not text.isdigit():
        raise ToolError(
            message=f"{value!r} is not a numeric {what}.",
            hint="Use an id from deck_browse; Deck addresses boards, stacks and cards by number.",
        )
    return text
```

**Formprüfer** (deck.py Zeilen 221-236): zwei kleine Helfer, damit eine unerwartete Antwortform
ein Satz und kein `TypeError` wird. Tables braucht zusätzlich `_as_rows` für die Liste von
Listen aus `rows/simple` (K8), gebaut nach derselben Form.

```python
def _as_list(payload: Any, what: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ToolError(
            message=f"Nextcloud answered with something that is not a list of {what}.",
            hint="Check that the Deck app is enabled and up to date on that instance.",
        )
    return [item for item in payload if isinstance(item, dict)]
```

**Lokale Vorprüfungen** (deck.py Zeilen 178-207): `check_title` und `check_duedate` sind
öffentlich, weil das Tool sie vor dem Rechte-Roundtrip aufruft. Tables hat kein Titel-Limit,
aber dasselbe Prinzip gilt für die Wertform-Prüfungen, die es bewusst **nicht** gibt
(Recherche, "Don't Hand-Roll"): dort steht stattdessen der durchgereichte 400.

---

### `src/mcp_connector/nextcloud/clients/ocs.py` (`ocs_post`, transport-Naht)

**Analog:** `ocs_get` im selben Modul, Zeilen 64-83. Wörtliches Vorbild inklusive der drei
Sätze, die die neue Funktion nur um `Content-Type` und den fehlenden `Origin` ergänzt:

```python
async def ocs_get(
    client: httpx.AsyncClient,
    creds: Credentials,
    path: str,
    params: Mapping[str, Any] | None = None,
) -> httpx.Response:
    """GET an OCS endpoint with both mandatory headers and per request authentication.

    Authentication is passed per request and not on the client, because the passthrough
    and the ExApp mode both change credentials from call to call. Which scheme it is, is
    the credential object's decision and not this module's (see ``Credentials.auth``).
    Redirects are not followed: the client is built that way, and a redirecting base URL
    is a configuration error.
    """
    return await client.get(
        ocs_url(creds, path),
        params=dict(params) if params else None,
        headers=dict(OCS_HEADERS),
        auth=creds.auth(),
    )
```

**Header-Konstante und URL-Bau, die `ocs_post` mitbenutzt** (Zeilen 36-61):

```python
#: OCS v2 lives under this prefix; v1 is not used anywhere in this project.
OCS_PREFIX = "/ocs/v2.php"

#: The two mandatory headers of D-18. Copied per request, never mutated in place.
OCS_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Accept": "application/json",
}


def ocs_url(creds: Credentials, path: str) -> str:
    """Build ``<base>/ocs/v2.php<path>``; ``path`` always starts with a slash."""
    if not path.startswith("/"):
        raise ValueError(f"an OCS path must start with a slash (got {path!r})")
    return f"{creds.base_url}{OCS_PREFIX}{path}"
```

**Nicht anfassen:** `parse_ocs` (Zeilen 126-147), `parse_app_json` (150-168), `_status_error`
(219-263). Tables benutzt beide Parser unverändert; `_status_error` hängt "Nextcloud says:
..." an und ist damit schon die Antwort auf die Wertform-400 der Tables-App.

---

### `src/mcp_connector/nextcloud/capabilities.py` (discovery-Service, gecacht)

**Analog:** die `deck`-Zweige derselben Datei. Vier Stellen, alle vier symmetrisch zu
erweitern.

**1. Fehlersatz je App** (Zeilen 41-56): message plus hint, und der hint nennt genau eine Sache,
die der Nutzer tun kann.

```python
#: message plus hint per optional app (D-15). The wording is part of the contract: it is
#: what the user reads, so it names the app and one thing to do instead.
_MISSING: dict[str, tuple[str, str]] = {
    "deck": (
        "The Deck app is not installed on this Nextcloud.",
        (
            "Ask an administrator to install the Deck app, or keep the task list in a note "
            "created with notes_create."
        ),
    ),
}
```

**2. Snapshot-Dataclass und `has()`** (Zeilen 59-76):

```python
@dataclass(frozen=True, slots=True)
class Capabilities:
    """The optional-app snapshot of one Nextcloud, as far as this project cares."""

    notes_available: bool = False
    notes_api_versions: tuple[str, ...] = ()
    deck_available: bool = False
    deck_api_versions: tuple[str, ...] = ()
    can_create_boards: bool = False

    def has(self, app: str) -> bool:
        """Whether ``app`` is installed. Unknown names are a programming error."""
        flags = {"notes": self.notes_available, "deck": self.deck_available}
        try:
            return flags[app]
        except KeyError:
            raise ValueError(f"{app!r} is not an optional app this server checks") from None
```

**3. Defensives Parsen** (Zeilen 119-147): hier liegt der einzige Unterschied zu Deck. Deck
gilt als vorhanden, sobald die Sektion existiert; Tables muss `enabled` auswerten (Recherche,
Muster 2). Die Form bleibt dieselbe.

```python
def parse(data: Any) -> Capabilities:
    """Read the capabilities payload defensively; a missing key is a ``False``, not a crash."""
    section = data.get("capabilities") if isinstance(data, dict) else None
    section = section if isinstance(section, dict) else {}

    deck = section.get("deck")
    deck = deck if isinstance(deck, dict) else None

    return Capabilities(
        deck_available=deck is not None,
        deck_api_versions=_versions(deck, "apiVersions"),
        can_create_boards=bool(deck.get("canCreateBoards")) if deck else False,
    )


def _versions(section: dict[str, Any] | None, key: str) -> tuple[str, ...]:
    """Accept a list, tolerate a single string, ignore anything else."""
    if not section:
        return ()
    raw = section.get(key)
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list):
        return tuple(str(item) for item in raw if isinstance(item, str | int | float))
    return ()
```

**4. Nicht anfassen:** `load` (82-93), `require_app` (101-110), `app_missing` (113-116), der
Cache `_cache` (79). Der Cache steht in
`tests/contract/test_no_destructive_calls.py::ALLOWED_MODULE_STATE` (Zeilen 84-87) und darf
nicht um einen zweiten Eintrag wachsen.

---

### `src/mcp_connector/tools/tables.py` (tool, transform plus create)

**Analog:** `src/mcp_connector/tools/deck.py` (234 Zeilen, komplett gelesen)

**Modul-Docstring-Muster** (deck.py Zeilen 1-23): begründet, warum ein Tool mit `level` statt
drei Tools, was vor dem Fehlschlag erklärt wird, und was absichtlich fehlt. Für Tables tritt an
die Stelle des N+1-Absatzes das erzwungene `limit`, und an die Stelle von `canCreateBoards` die
K5-Eigentümerfalle.

```python
"""Deck tools: one browse tool with a level, and one create-only write (D-06, TOOL-04).

**One tool, three levels.** ``deck_browse(level=...)`` walks boards, stacks and cards.
Three separate tools would cost three slots in every client that limits them and three
schemas in every ``tools/list``, for navigation the model can express in one enum value.
The answer envelope is the same on every level (``level``, ``count``, ``results``), so the
model learns one shape instead of three.
...
**Two things are explained before they can fail.** A missing Deck app stops both tools at
the capabilities check, before the first Deck request (SRV-04). And a user whose Nextcloud
forbids board creation is checked against the board's own permissions instead of being
walked into a 403 ...

Deliberately absent: update, delete, board or stack creation. The client below has no code
for any of it, which is what makes the create-only annotation of ``deck_create_card``
honest rather than a promise (threat T-01-62).
"""
```

**Imports und Konstanten** (deck.py Zeilen 25-41):

```python
from typing import Any

from .. import ids
from ..errors import ToolError
from ..nextcloud import NcClients, capabilities
from ..nextcloud.clients import deck as deck_client

APP = "deck"

#: The three navigation levels of ``deck_browse``, in the order a model walks them.
LEVELS = ("boards", "stacks", "cards")

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."
_BOARD_HINT = "Call deck_browse with level=boards first; it lists the board ids."
```

Für Tables: `ids` fällt weg (K8), `LEVELS = ("tables", "columns", "rows")`,
`DEFAULT_LIMIT = 25`, `MAX_LIMIT = 200`.

**Browse-Kopf: Reihenfolge Validierung, Kappung, `require_app`** (deck.py Zeilen 44-71):

```python
async def browse(
    clients: NcClients,
    level: str = "boards",
    board_id: str | None = None,
    stack_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Walk the user's Deck: boards, the stacks of a board, or its cards."""
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Deck level.", hint=_LEVEL_HINT)
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "boards":
        return _envelope(level, await _boards(clients), capped)

    board = (board_id or "").strip()
    if not board:
        raise ToolError(
            message=f"level={level!r} needs a board_id.",
            hint=_BOARD_HINT,
        )
    ...
```

**Create-Kopf: Vorprüfungen vor dem Schreiben** (deck.py Zeilen 74-126): die Reihenfolge ist
das Muster. `require_app`, dann die billigen lokalen Prüfungen, dann die Rechte-Vorprüfung,
dann der Schreibaufruf, dann die Antwortprüfung mit einem Satz für den Fall, dass die App eine
Id verschweigt.

```python
async def create_card(...)-> dict[str, Any]:
    """Create one card in an existing stack and return its canonical long id."""
    caps = await capabilities.require_app(clients, APP)

    # Validated here and not only in the client: an unusable title or date must not cost
    # the permission round trip below either.
    wanted = deck_client.check_title(title)
    ...
    if not caps.can_create_boards:
        await _require_write_permission(clients, board)

    card = await deck_client.create_card(...)

    card_id = card.get("id")
    if card_id in (None, ""):
        raise ToolError(
            message="Nextcloud created the card but reported no id.",
            hint="Look for the card in the Deck app; it was probably created.",
        )

    result: dict[str, Any] = {
        "id": ids.encode_card(board, card.get("stackId") or stack, card_id),
        "title": str(card.get("title") or wanted),
        "url": deck_client.web_url(clients.creds, card_id),
    }
```

Für Tables tritt die Titel-zu-Id-Abbildung an die Stelle von `check_title`, und die
Rechte-Vorprüfung ist `_may_create(table)` aus K5.

**Rechte-Vorprüfung mit Begründung im Docstring** (deck.py Zeilen 195-225): das ist das
wichtigste zu kopierende Muster der Phase, weil K5 dieselbe Falle in neuem Gewand ist. Der
Docstring erklärt, warum das naive Feld nicht befragt wird.

```python
async def _require_write_permission(clients: NcClients, board: str) -> None:
    """Refuse a card the instance would refuse anyway, and say which board it was.

    ``canCreateBoards`` is false on instances that restrict board creation to a group.
    That says nothing about a board the user already has an edit permission on, so the
    board list decides, and only a board that really is read-only ends the call here.
    """
    boards = await deck_client.get_boards(clients.client, clients.creds)
    match = next((item for item in boards if str(item.get("id")) == board), None)
    if match is not None and _can_edit(match):
        return
    ...
    raise ToolError(
        message=f"No permission to add a card to board {board} ({match.get('title')}).",
        hint=(
            f"{known} and this board is read-only for it. Ask its owner in Nextcloud for "
            "an edit permission, or pick a board that deck_browse reports with can_edit."
        ),
    )


def _can_edit(board: dict[str, Any]) -> bool:
    permissions = board.get("permissions")
    permissions = permissions if isinstance(permissions, dict) else {}
    return bool(permissions.get("PERMISSION_EDIT"))
```

Tables-Fassung nach K5 (aus der Recherche, Muster 4): `_may_create(table)` liest zuerst
`isShared`, dann `create` oder `manage`. Die Defensivform
`permissions if isinstance(permissions, dict) else {}` bleibt wörtlich.

**Projektion statt Durchreichen** (deck.py Zeilen 129-150): nur die Felder, die jemand liest,
plus ein abgeleitetes Rechtefeld, plus der Filter gegen zur Seite gelegte Objekte.

```python
async def _boards(clients: NcClients) -> list[dict[str, Any]]:
    """Board ids and titles, plus whether the user may write to them at all."""
    boards = await deck_client.get_boards(clients.client, clients.creds)
    return [
        {
            "id": board.get("id"),
            "title": str(board.get("title") or ""),
            "can_edit": _can_edit(board),
        }
        for board in boards
        if not board.get("archived") and not board.get("deletedAt")
    ]
```

**Antwort-Envelope mit benannter Kappung** (deck.py Zeilen 228-234): eine Form für alle Level.
Tables erweitert sie um `rowsCount` und `offset` (Recherche, Muster 6), behält aber `level`,
`count`, `results`, `truncated`.

```python
def _envelope(level: str, results: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for all three levels, truncation named instead of silent."""
    kept = results[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(results) > len(kept):
        answer["truncated"] = True
    return answer
```

---

### `src/mcp_connector/server/reg_tables.py` (registration)

**Analog:** `src/mcp_connector/server/reg_deck.py` (73 Zeilen, komplett gelesen). Eins zu eins
übertragbar, inklusive Docstring-Aufbau.

```python
"""Registration of the deck tools. The logic lives in :mod:`mcp_connector.tools.deck`.

``level`` is a ``Literal`` and therefore an enum in the input schema, not a free string:
the model sees the three valid values instead of guessing "card" or "lists" and paying a
round trip for the correction (D-06, D-14).

Both tools are listed unconditionally, even on an instance without the Deck app. A
credential dependent ``tools/list`` is not cacheable, breaks the token budget gate and
surprises clients that persist tool lists; the honest answer to a missing app is the
sentence the tool returns (SRV-04).
"""

from typing import Annotated, Literal

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import deck as deck_tools
from . import CREATE_ONLY, READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def deck_browse(
    level: Annotated[
        Literal["boards", "stacks", "cards"],
        Field(description="What to list; stacks and cards need a board_id"),
    ] = "boards",
    board_id: Annotated[str, Field(description="Board id from level=boards, e.g. 2")] = "",
    stack_id: Annotated[str, Field(description="Optional: only cards of this stack")] = "",
    limit: Annotated[
        int, Field(ge=1, le=deck_tools.MAX_LIMIT, description="Maximum number of entries")
    ] = deck_tools.DEFAULT_LIMIT,
    ctx: Context | None = None,
) -> str:
    """List Deck boards, the stacks of a board, or its cards."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await deck_tools.browse(
            clients,
            level=level,
            board_id=board_id or None,
            stack_id=stack_id or None,
            limit=limit,
        )
    )


@mcp.tool(annotations=CREATE_ONLY, structured_output=False)
@graceful
async def deck_create_card(
    board_id: Annotated[str, Field(description="Board id from deck_browse")],
    ...
    ctx: Context | None = None,
) -> str:
    """Create a card in an existing stack; never changes or deletes an existing card."""
    clients = deps.resolve_clients(ctx)
    return compact(await deck_tools.create_card(clients, ...))
```

Die vier Regeln, die diese Datei trägt und die für `reg_tables.py` genauso gelten:

1. Leere Strings statt `None` als Default, damit kein `anyOf[string, null]` ins Schema kommt.
2. `Literal[...]` erzeugt das `enum`; der Contract-Test prüft die Werte wörtlich.
3. `structured_output=False` überall (Ausnahme nur `search`/`fetch`).
4. Kein Import in `server/__init__.py` nötig: `_load_registrations()` (Zeilen 102-114 dort)
   importiert jedes `reg_*`-Modul automatisch, damit parallele Pläne keine gemeinsame Datei
   anfassen.

---

### `tests/unit/test_tables_client.py` (test, unit, respx)

**Analog:** `tests/unit/test_deck_client.py` (339 Zeilen; Kopf und Header-Tests gelesen)

**Testgerüst** (Zeilen 14-49): Konstanten für Basis-URL und die vollen Endpunkt-URLs als
eingefrorene Literale, zwei Fixtures, ein `fixture()`-Leser.

```python
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mcp_connector.errors import ToolError
from mcp_connector.nextcloud.clients import deck as deck_client
from mcp_connector.nextcloud.credentials import Credentials

BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"

DECK_BASE = f"{BASE}/index.php/apps/deck/api/v1.0"
BOARDS_URL = f"{DECK_BASE}/boards"
STACKS_URL = f"{DECK_BASE}/boards/2/stacks"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)
```

Diese URL-Konstanten sind gleichzeitig das eingefrorene Literal, das die Recherche für
`nodeType` (Singular) und `nodeCollection` (Plural) verlangt (K3, Falle 3).

**Header-Behauptung** (Zeilen 65-79): das Muster, um eine Eigenschaft der gebauten Anfrage zu
prüfen statt nur das Ergebnis. Genau diese Form braucht auch die `limit`-Behauptung aus
Muster 5 der Recherche.

```python
@pytest.mark.anyio
async def test_a_get_carries_both_mandatory_headers(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """D-18 and pitfall 9: Deck wants both headers even where there is no body."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(BOARDS_URL).mock(
            return_value=httpx.Response(200, json=fixture("deck_boards.json"))
        )
        await deck_client.get_boards(client, creds)

    request = route.calls[0].request
    assert request.headers["OCS-APIRequest"] == "true"
    assert request.headers["Content-Type"] == "application/json"
```

**Query-Parameter-Behauptung** (Zeilen 98-107): dieselbe Technik über `request.url.params`.

```python
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(BOARDS_URL).mock(return_value=httpx.Response(200, json=[]))
        boards = await deck_client.get_boards(client, creds, details=True)

    assert boards == []
    assert route.calls[0].request.url.params["details"] == "true"
```

**Docstring des Testmoduls** (Zeilen 1-12): nennt zuerst die zwei Eigenschaften, die Vertrag
sind, danach den Katalog. Für Tables: erzwungenes `limit`, Parser-Wahl je Generation, dann der
Katalog (403 mit `{"message": ...}`, Status 200 beim Create, leere Tabelle als `no_data`, nicht
numerische `table_id`).

---

### `tests/unit/test_tables_tools.py` (test, unit)

**Analog:** `tests/unit/test_deck_tools.py` (395 Zeilen; Kopf gelesen)

**Gerüst mit Capabilities-Mock und Cache-Reset** (Zeilen 27-60): das ist der Teil, den ein
Tables-Tool-Test wörtlich braucht, weil `require_app` in jedem Pfad die erste Zeile ist.

```python
CAPABILITIES_URL = f"{BASE}/ocs/v2.php/cloud/capabilities"
DECK_BASE = f"{BASE}/index.php/apps/deck/api/v1.0"

DECK_INSTALLED = {"version": "1.18.3", "canCreateBoards": True, "apiVersions": ["1.0", "1.1"]}
DECK_WITHOUT_BOARD_RIGHTS = {**DECK_INSTALLED, "canCreateBoards": False}


def envelope(data: Any) -> dict:
    return {"ocs": {"meta": {"status": "ok", "statuscode": 200, "message": "OK"}, "data": data}}


def capabilities_payload(*, deck: dict | None = None) -> dict:
    section: dict[str, Any] = {"core": {}}
    if deck is not None:
        section["deck"] = deck
    return envelope({"capabilities": section})


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    capabilities.clear_cache()
```

Der `envelope()`-Helfer ist auch für die Tables-v2-Antworten der richtige, weil diese im
OCS-Envelope kommen; die v1-Zeilenantwort dagegen ist bar und braucht keinen.

**Docstring-Muster** (Zeilen 1-12): nennt die zwei Eigenschaften, die das Ein-Tool-Design
rechtfertigen, dann den Katalog der Fehlerpfade (D-15, SRV-04).

---

### `tests/integration/test_tables_roundtrip.py` (test, integration)

**Analog:** `tests/integration/test_deck_roundtrip.py` (174 Zeilen, komplett gelesen)

**Docstring mit Laufanleitung** (Zeilen 1-17):

```python
"""Deck round trip against a real Nextcloud 34 with the Deck app (opt-in).

The unit tests pin the shapes; only a real instance answers the questions that matter
here: does Deck really accept the mandatory headers the way the documentation describes,
...
Board and stack are test scaffolding, not connector features: the client cannot create
either of them on purpose (create-only, threat T-01-62), so the two ``POST`` calls below
are made directly with httpx and are clearly marked as setup.

Run it with::

    docker compose -f compose.test.yml up -d --wait
    bash scripts/bootstrap_test_nc.sh
    set -a && . ./.env.test && set +a && uv run pytest -m integration -q
"""

pytestmark = [pytest.mark.integration, pytest.mark.anyio]
```

**Clients-Fixture mit Skip und Admin-Sperre** (Zeilen 43-60):

```python
@pytest.fixture
def clients(live_env: dict[str, str | None]) -> NcClients:
    missing = [name for name, value in live_env.items() if not value]
    if missing:
        pytest.skip(f"no test Nextcloud configured (missing: {', '.join(sorted(missing))})")

    user = live_env["user"]
    assert user != "admin", "integration tests run as a normal user, never as admin"

    capabilities.clear_cache()
    return NcClients(
        client=httpx.AsyncClient(follow_redirects=False, timeout=30.0),
        creds=Credentials(
            base_url=normalize_base_url(str(live_env["base_url"])),
            user=str(user),
            secret=str(live_env["secret"]),
        ),
    )
```

**Setup-Schreibaufrufe als ausdrücklich markiertes Gerüst** (Zeilen 63-95): genau das braucht
Tables, weil das Tool keine Tabelle und keine Spalte anlegen kann. Der Skip bei 4xx statt eines
Fehlschlags ist Teil des Musters.

```python
async def _post(clients: NcClients, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Test scaffolding only: the connector itself never creates boards or stacks."""
    response = await clients.client.post(
        deck_client.api_url(clients.creds, path),
        json=body,
        headers=dict(deck_client.DECK_HEADERS),
        auth=httpx.BasicAuth(clients.creds.user, clients.creds.secret),
    )
    if response.status_code >= 400:
        pytest.skip(f"this account may not prepare a deck board ({response.status_code})")
    ...


async def _board_and_stack(clients: NcClients) -> tuple[int, int]:
    """Return an existing writable board plus stack, creating them once if needed."""
    boards = await deck_client.get_boards(clients.client, clients.creds)
    board = next(
        (item for item in boards if item.get("title") == BOARD_TITLE and not item.get("archived")),
        None,
    )
    if board is None:
        board = await _post(clients, "/boards", {"title": BOARD_TITLE, "color": "0082c9"})
    ...
```

**Die vier Testarten, die Tables spiegeln sollte** (Zeilen 98-174):

1. `test_capabilities_report_the_installed_deck_app` (98-104): Capability plus API-Version.
   Tables-Fassung prüft `tables_available` und `"1.0"` sowie `"2.0"` in `apiVersions`.
2. `test_a_new_card_is_findable_under_its_canonical_id` (107-126): anlegen, dann über das
   Browse-Tool zurücklesen. Umlaute im Testinhalt sind Absicht
   (`"Grüße aus Hamburg, Straße 1"`).
3. `test_the_card_level_stays_one_request_against_a_real_instance` (128-151): zählt Requests
   durch Ersetzen von `clients.client.send`. Für Tables ist die interessante Messung nicht die
   Request-Zahl, sondern die gebaute URL; derselbe Hook eignet sich, um `limit=` in der
   Live-URL zu behaupten.
4. `test_browsing_an_unknown_board_reports_it_instead_of_guessing` (168-174): Negativfall mit
   `pytest.raises(ToolError)` und `assert excinfo.value.hint`.

---

### `tests/integration/test_exapp_mail_reach.py` (test, integration, Spike)

**Analog:** `tests/integration/test_exapp_dav_matrix.py` (357 Zeilen, komplett gelesen).
Rollen-Treffer: dieselbe Rolle (Beweis unter AppAPI-Impersonation über der HaRP-Topologie),
aber ein anderer Datenfluss. Der DAV-Spike behauptet Erfolg je Familie; der Mail-Spike
**protokolliert** Statuscode, Content-Type und Körperanfang und behauptet nur "App-Code hat
geantwortet". Der `_probe`-Helfer aus der Recherche hat in der Codebasis kein Gegenstück und
ist der einzige echt neue Baustein der Phase.

**Docstring-Muster mit den drei tragenden Punkten** (Zeilen 1-38): wörtlich übernehmen und auf
Mail umschreiben. Genau hier gehört laut Erfolgskriterium 2 der `SCOPE_IGNORE`-Hinweis hin.

```python
"""The DAV spike (D-30, AUTH-05): does the identity arrive without an app password.
...
Because that is the question, three things are load bearing in here and not incidental.

*   Every credential object is built with ``mode="appapi"`` and ``secret=APP_SECRET``. There
    is no ``httpx.BasicAuth`` anywhere in this file, and no ``NC_MCP_APP_PASSWORD`` is read
    as a credential source. The identity can only come from ``AUTHORIZATION-APP-API``.
*   The first two checks are controls. Without them a green matrix proves nothing ...
*   The measurement uses the real client functions ...

Run it against the running HaRP topology::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_exapp_dav_matrix.py -m integration -q
"""

pytestmark = [pytest.mark.integration, pytest.mark.anyio]
```

**Credential-Bau im AppAPI-Modus** (Zeilen 61-94): wörtlich übernehmbar, inklusive Fixture-Form.

```python
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
```

**Beide Kontrollprüfungen** (Zeilen 104-143): die Recherche verlangt sie ausdrücklich, sonst
beweist eine grüne Matrix nichts. Wörtlich übernehmbar.

```python
# --------------------------------------------------------------------------------------
# Control checks. Everything below them is worthless without them.
# --------------------------------------------------------------------------------------


async def test_the_measuring_process_holds_no_nextcloud_app_password(
    exapp_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control one: the identity cannot come from a Basic app password or a static bearer."""
    monkeypatch.delenv("NC_MCP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("NC_MCP_STATIC_BEARER", raising=False)
    assert os.environ.get("NC_MCP_APP_PASSWORD") is None
    assert os.environ.get("NC_MCP_STATIC_BEARER") is None
    clients = _appapi_clients(exapp_env, exapp_env["bob"])
    assert clients.creds.mode == MODE_APPAPI
    assert clients.creds.secret == exapp_env["app_secret"]


async def test_a_wrong_app_secret_is_refused(exapp_env: dict[str, str]) -> None:
    """Control two: without the real secret, nothing answers 200."""
    wrong = _appapi_clients({**exapp_env, "app_secret": "0" * 64}, exapp_env["alice"])
    async with wrong.client:
        response = await ocs.ocs_get(wrong.client, wrong.creds, "/cloud/user")
    assert response.status_code != 200, (
        "a wrong APP_SECRET was accepted; the identity is not coming from the secret"
    )
```

**Die `exapp_env`-Fixture** liegt in `tests/conftest.py` Zeilen 39-68 und skippt mit dem Namen
der fehlenden Variable. Nichts daran ist zu ändern; der Mail-Spike benutzt sie unverändert.

**Was der Mail-Spike anders macht als das Analog:** statt `assert response.status_code == 200`
je Familie steht ein `_probe`-Helfer, der ein Dict aus Status, Content-Type, Form und den
ersten 120 Zeichen zurückgibt (Skizze in `08-RESEARCH.md`, Abschnitt "Spike: eine Messzeile
statt einer Vermutung"), plus ein `assert shape == "json"` je Weg. Die 120-Zeichen-Grenze ist
Sicherheitsanforderung, nicht Kosmetik: die Kontoantwort enthält IMAP- und SMTP-Hostnamen.

---

### `tests/contract/test_tool_surface.py` (GEÄNDERT)

**Analog:** die Deck-Abschnitte derselben Datei. **Fünf Stellen**, alle im Blick zu halten
(Recherche, Falle 7):

**1. Eingefrorene Mengen** (Zeilen 28-54):

```python
EXPECTED_TOOLS = {
    "files_search",
    ...
    "deck_browse",
    "deck_create_card",
    ...
}

# The four write paths. Everything else in EXPECTED_TOOLS only reads (D-16).
CREATE_TOOLS = {"files_upload", "calendar_create_event", "notes_create", "deck_create_card"}
```

**2. Der Enum-Test je Familie** (Zeilen 199-227): Vorbild für den neuen Tables-Test.

```python
@pytest.mark.anyio
async def test_the_two_deck_tools_are_listed_and_browse_takes_an_enum_level() -> None:
    """D-06: one browse tool with a level parameter, never one tool per Deck level."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ("deck_browse", "deck_create_card"):
        assert name in tools, f"{name} is part of the curated set (D-06)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    browse = tools["deck_browse"]
    annotations = browse.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "deck_browse only reads"
    assert annotations.open_world_hint is False

    schema = browse.input_schema
    assert schema["properties"]["level"]["enum"] == ["boards", "stacks", "cards"], (
        "the level is an enum in the schema, not a free string the model has to guess"
    )
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"

    create = tools["deck_create_card"].annotations
    assert create is not None
    assert create.read_only_hint is False, "deck_create_card writes"
    assert create.destructive_hint is False, "it can only create, never replace or delete"
    assert create.idempotent_hint is False, "a second call creates a second card"
    assert create.open_world_hint is False
```

**3. Die Verbotsliste gegen ein Tool pro Ebene** (Zeilen 229-236): Vorbild für
`tables_list_tables`/`tables_list_columns`/`tables_list_rows`/`tables_read_row`.

```python
@pytest.mark.anyio
async def test_there_is_no_tool_per_deck_level() -> None:
    """The anti-pattern D-06 rules out: three tools would cost slots without any gain."""
    async with Client(mcp, raise_exceptions=True) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    forbidden = {"deck_list_boards", "deck_list_stacks", "deck_list_cards", "deck_read_card"}
    assert not (names & forbidden), f"deck_browse covers these levels: {names & forbidden}"
```

**4. Die drei Stellen mit der nackten Zahl 16:** Zeile 307 (Docstring "16 tools, and the diet
holds for 14 of them"), Zeile 312 (`assert len(tools) == 16`), Zeile 409 (Docstring "four
create-only tools, twelve pure reads"), Zeile 457 (Assertion-Meldung "all 16 schemas"). Alle
vier werden zu 18 beziehungsweise "fünf create-only, dreizehn pure reads".

**5. Der README- und Doku-Wächter** (Zeilen 471-527): keine Änderung im Test, aber er erzwingt
die README-Zeilen und die Zahlen in `docs/`.

```python
def test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from() -> None:
    """IN-04: a page may record a run with an old count, it may not leave it unexplained.
    ...
    """
    holder = "tests/contract/test_tool_surface.py"
    current = len(EXPECTED_TOOLS)
```

Damit ist die Regel für `docs/client-setup.md` Zeile 431 exakt die aus der Recherche: ein
datierter Messwert darf stehenbleiben, wenn die Seite auf diese Testdatei zeigt.

---

### `tests/contract/test_no_destructive_calls.py` (GEÄNDERT)

**Analog:** dieselbe Datei. Zwei Muster sind zu kopieren.

**1. Die Nadel-Tabelle** (Zeilen 29-39): Kommentar erklärt, warum Grossschreibung, und jede
Nadel trägt ihre Begründung als Wert.

```python
# Destructive HTTP verbs and the one OCS route that changes who may see an object. Upper
# case on purpose: httpx spells a custom method in upper case, and the lower case words
# "move" or "copy" occur in ordinary prose and identifiers.
FORBIDDEN: dict[str, str] = {
    "DELETE": "no tool may delete anything",
    "MOVE": "no tool may move or rename anything",
    "COPY": "no tool may duplicate anything server side",
    "PROPPATCH": "no tool may change properties of an existing object",
    "ocs/v2.php/apps/files_sharing": "no tool may create or change a share",
    ".delete(": "no client helper may expose a delete call",
}
```

Die neuen Tables-Nadeln (`apps/tables/api/1/rows`, `apps/tables/api/1/columns`,
`tables/scheme`, `/transfer`, die Share-Route) folgen der Form "Pfadfragment als Schlüssel,
Begründungssatz als Wert". Wichtig: sie brauchen kein verbotenes Verb, weil ein POST auf
`/rows/{id}` die Zeile ändert.

**2. Gegenprobe je Ausnahme** (Zeilen 187-232): das Muster, das die Recherche für die neuen
Nadeln verlangt. Jede Ausnahme hat einen eigenen Test, der zeigt, dass sie genau eine Form
deckt und nichts sonst.

```python
def test_the_sql_exemption_covers_sql_and_nothing_else() -> None:
    """Counter proof for the narrow exemption: an HTTP DELETE in the store still counts.
    ...
    """
    store = "oauth/store.py"
    assert _is_own_sql(store, 'conn.execute("DELETE FROM flows WHERE expires_at <= ?")')
    assert not _is_own_sql(store, 'await client.request("DELETE", url)')
    assert not _is_own_sql("tools/files.py", 'conn.execute("DELETE FROM flows")')

    for relative in FILES_WITH_OWN_SQL | FILES_WITH_OWN_APP_PASSWORD | FILES_WITH_OWN_CONFIG:
        assert (SRC / relative).is_file(), f"{relative} is exempt but does not exist"
```

Und die Gegenprobe für das Gate selbst (Zeilen 170-184), damit der Kommentar-Filter nicht
alles frisst:

```python
def test_the_gate_would_notice_a_destructive_call_in_real_code() -> None:
    """Counter proof: the filter removes prose, and only prose."""
    dav = SRC / "nextcloud" / "clients" / "dav.py"
    docstring_text = "\n".join(text for _, text in _code_lines(dav))
    assert "no DELETE, no MOVE, no COPY" not in docstring_text, (
        "the filter must remove the module docstring of dav.py"
    )
    with_a_violation = docstring_text + '\n    await client.request("DELETE", url)\n'
    assert "DELETE" in with_a_violation, "a real call is still visible after filtering"
```

**Achtung, harte Nebenbedingung:** derselbe Test verbietet neuen modulweiten mutablen Zustand
(Zeilen 79-87, `ALLOWED_MODULE_STATE` mit genau zwei Einträgen). `clients/tables.py` und
`tools/tables.py` dürfen also keinen eigenen Cache und keine modulweite Liste anlegen. Konstanten
in Grossschreibung sind ausgenommen (Zeile 256).

---

### `tests/fixtures/tables_*.json` (fixture)

**Analog:** `tests/fixtures/deck_boards.json` (Kopf gelesen). Das Muster ist eine realistische,
vollständige Rohantwort mit deutschen Titeln, nicht ein minimales Konstrukt: genau daran zeigt
sich, ob die Projektion die überflüssigen Felder wirklich wegwirft.

```json
[
  {
    "id": 2,
    "title": "Projekt MCP",
    "owner": { "primaryKey": "alice", "uid": "alice", "displayname": "Alice Beispiel", "type": 0 },
    "color": "0082c9",
    "archived": false,
    "labels": [ { "id": 7, "title": "Dringend", "color": "31CC7C", "boardId": 2 } ],
    "acl": [],
    "permissions": {
      "PERMISSION_READ": true,
      "PERMISSION_EDIT": true,
      "PERMISSION_MANAGE": true,
      "PERMISSION_SHARE": true
    }
  }
]
```

Für Tables also: `tables_tables.json` mit `views`, `columnOrder`, `sort`, `ownerDisplayName`
und den beiden Rechte-Varianten (eigene Tabelle mit `isShared: false` plus
`onSharePermissions: {read: true, ...}`, und eine geteilte Tabelle ohne `create`), damit K5 im
Unit-Test ohne Server prüfbar ist.

---

### `scripts/check_tool_budget.py` (GEÄNDERT)

**Analog:** der bestehende Messkommentar derselben Datei, Zeilen 16-27. Die Regel, wie eine
Anhebung aussehen darf, steht wörtlich im Kommentar und ist damit selbst das Muster.

```python
# Armed value, not a decorative one. A budget far above the measurement never fails and
# therefore never protects anything, which was the state until the end of phase 1.
#
#   Measurement 2026-08-14, all 15 curated tools registered: 10643 bytes
#   Budget      10643 + 15 percent = 12239, rounded up to the next 500 = 12500 bytes
#
# The headroom is for wording, not for a new tool: at ~4 bytes per token the whole surface
# costs roughly 2.7k tokens in every single session of every client. A sixteenth tool or a
# description that grows into a paragraph is supposed to trip this gate, so the decision
# gets made on purpose instead of by accident. Raising the number is allowed, but only
# together with a new measurement line above, so a regression stays attributable.
BUDGET_BYTES = 12_500
```

Die neue Zeile folgt derselben Schreibweise: `Measurement <Datum>, all 18 curated tools
registered: <gemessen> bytes` plus die Rechnung. Die von der Recherche empfohlene zweite
Behauptung (kein einzelnes Tool über 1400 Bytes) hat ihr Vorbild in der schon vorhandenen
Pro-Tool-Auswertung, Zeilen 37-47:

```python
    per_tool = sorted(
        (
            (len(json.dumps(tool, separators=(",", ":"), ensure_ascii=False)), tool["name"])
            for tool in payload["tools"]
        ),
        reverse=True,
    )

    print(f"tools/list: {size} bytes, {len(payload['tools'])} tools, budget {BUDGET_BYTES}")
    for tool_size, name in per_tool[:5]:
        print(f"  {name}: {tool_size} bytes")
```

Die Liste existiert also schon; es fehlt nur der Vergleich gegen eine zweite Konstante und ein
zweiter `return 1`-Zweig nach dem Vorbild der Zeilen 49-52.

---

### `scripts/acceptance_all_tools.py` (GEÄNDERT)

**Analog:** dieselbe Datei. Die Zahl steht an **drei** Stellen: Modul-Docstring Zeile 1
("call all 15 tools once"), Zeile 16 ("Exit code 0 only when all 15 tools answered"),
Konstante Zeile 44 (`EXPECTED_TOOLS = 15`). Die Fehlermeldung dazu (Zeilen 103-104) ist in
`docs/conference-demo.md` Zeile 271 wörtlich zitiert und muss mitwandern:

```python
    if len(names) != EXPECTED_TOOLS:
        report.add("tools/list", "FAIL", f"expected {EXPECTED_TOOLS} tools, got {len(names)}")
```

---

### `scripts/bootstrap_exapp.sh` und `scripts/bootstrap_test_nc.sh` (GEÄNDERT)

**Analog:** die `ensure_app`-Funktion, `bootstrap_exapp.sh` Zeilen 251-265. Idempotenz durch
"install, sonst enable, sonst Fehler mit Verweis auf den FALLBACK-Block":

```bash
ensure_app() {
  local app="$1" output
  if output="$(occ app:install "$app" 2>&1)"; then
    echo "app ${app}: installed"
    return 0
  fi
  if output="$(occ app:enable "$app" 2>&1)"; then
    echo "app ${app}: enabled"
    return 0
  fi
  echo "ERROR: could not install or enable ${app}:" >&2
  echo "${output}" >&2
  echo "See the FALLBACK block at the end of this script." >&2
  return 1
}
```

Aufrufstellen: `bootstrap_exapp.sh` Zeilen 849-850 (`ensure_app notes`, `ensure_app deck`),
`bootstrap_test_nc.sh` Zeilen 159-160. Die neuen Zeilen kommen direkt darunter.

Das Mail-Konto für den Spike folgt dem Idempotenz-Muster von `ensure_user` (Zeilen 267-283):
erst prüfen, ob es existiert, dann anlegen, Ausgabe nur bei Fehler zeigen.

```bash
ensure_user() {
  local uid="$1" password="$2" output
  if occ user:info "$uid" >/dev/null 2>&1; then
    echo "user ${uid}: exists"
    return 0
  fi
  # occ reports a rejected password on stdout, so the output is captured and only shown
  # when it matters. Swallowing it would turn a policy violation into a silent exit 1.
  if ! output="$(occ_pw "$password" user:add --password-from-env "$uid" 2>&1)"; then
    echo "ERROR: could not create user ${uid}:" >&2
    echo "${output}" >&2
    return 1
  fi
  echo "user ${uid}: created"
```

---

### `docs/spike-mail.md` (NEU)

**Analog:** `docs/spike-dav.md` (169 Zeilen; Kopf und Beweisabschnitt gelesen). Rollen-Treffer:
gleiche Rolle (Messprotokoll eines Spikes), aber das Ergebnis ist nicht "Familie läuft", sondern
"Controller erreicht oder nicht".

**Kopf-Muster** (Zeilen 1-16): Status und Entscheidungsfall zuerst, dann jede Version, die die
Messung gültig macht, dann der Scope-Satz.

```markdown
# DAV Impersonation Spike (D-30, AUTH-05)

**Status:** done, decision case A (every family runs under impersonation)
**Decision date:** 2026-08-15
**Nextcloud version:** 34.0.2 (build 34.0.2.1)
**AppAPI version:** 34.0.0
**Deploy daemon:** HaRP, over the `compose.exapp.yml` topology (Caddy on `127.0.0.1:8081`)
**Scope:** does the identity of the logged in user arrive in every Nextcloud API family when
the only credential in play is `APP_SECRET` ...
```

**Entscheidungstabelle** (Zeilen 25-32): eine Zeile je gemessener Weg, mit Endpunkt, Auth-Pfad,
Beweis (Testname plus Statuscode) und der Spalte, die die Frage der Phase beantwortet.

```markdown
| Family | Endpoint | Auth path | Evidence (test, HTTP status) | Identity verified |
|--------|----------|-----------|------------------------------|-------------------|
| OCS | `/ocs/v2.php/...` | AppAPI impersonation | `test_ocs_identity_is_the_impersonated_alice` (200) | yes, `GET /ocs/v2.php/cloud/user` returns `ocs.data.id = alice` |
```

Für Mail werden die Spalten: Weg, URL, erwarteter Status, gemessener Status, Content-Type, Form
(json/html/other), Urteil (erreicht / nicht erreicht).

**Beweisabschnitt** (Zeilen 38-75): der Satz über Geheimnisse gehört wörtlich mit, weil der
Mail-Spike Kontodaten anfasst.

```markdown
All commands were run on 2026-08-15 against the running HaRP topology. Header values that
carry `APP_SECRET` (the `AUTHORIZATION-APP-API` value is base64 of `<user>:<APP_SECRET>` and
is exactly as sensitive as the secret) are never printed. Only status codes and the server
returned `id` are shown.
```

Dazu der Abschnitt "The two controls" (Zeilen 61-75), der beide Kontrollprüfungen benennt und
das 401 der falschen Secrets als Beweis der Gültigkeit aller anderen Zeilen ausweist.

---

### `README.md`, `README.de.md`, `README.fr.md` (GEÄNDERT)

**Analog:** die Deck-Zeilen der Tool-Tabelle. `README.md` Zeilen 196-197:

```markdown
| `deck_browse` | read | Browse Deck boards, stacks and cards |
| `deck_create_card` | create-only | Create a new card in a stack; existing cards are never changed |
```

`README.de.md` Zeile 203 und `README.fr.md` Zeile 206 tragen dieselben Zeilen übersetzt. Das
Format ist bindend, weil
`test_tool_surface.py::test_the_readme_permission_table_matches_the_live_registry` (Zeilen
471-491) die Zellen parst: erste Zelle in Backticks, zweite Zelle exakt `read` oder
`create-only`.

Die Zahlen: `README.md` Zeilen 19 und 30, `README.de.md` Zeilen 21 und 32, `README.fr.md`
Zeilen 21 und 34. Für die deutschen und französischen Zeilen gilt das Vokabular-Gate: "zur
Seite gelegte Tabellen" statt des verbotenen Wortes.

---

### `CHANGELOG.md` (GEÄNDERT)

**Analog:** der Block `## [0.1.3] - 2026-08-21`, Zeilen 12-40. Muster: ein Absatz in ganzen
Sätzen aus Nutzersicht vor den Unterabschnitten, dann `### Fixed` / `### Changed` / `### Added`
mit Sätzen, die sagen was war und was jetzt ist. Keine Tickets, keine Dateinamen, keine
Emojis. Beispielzeile:

```markdown
- The version this app names in the MCP handshake is now the version that is installed.
  It was a fixed string that stayed at the first release, so a connected assistant was
  told 0.1.0 whatever version answered. The handshake now derives it from the package
  version, the single string every release raises.
```

Phase 8 schreibt in einen `### Added`-Abschnitt unter einer noch nicht veröffentlichten
Fassung; das Release selbst ist Phase 11 (EXAPP-07).

---

### `compose.exapp.yml` (OPTIONAL, Spike-Stufe 2)

**Analog:** der Dienst `registry`, Zeilen 124-137. Muster: Kommentar über dem Dienst begründet,
warum er existiert, und jeder Port-Eintrag trägt seine Sicherheitsbegründung.

```yaml
  registry:
    # The ExApp image is not published before phase 5 (D-25), but the deploy daemon can
    # only pull what a registry serves. ...
    image: registry:2
    container_name: nc-mcp-exapp-registry
    ports:
      # Loopback only (WR-06): an unauthenticated, unencrypted registry on 0.0.0.0 is an
      # open write target for everyone on the same network.
      - "127.0.0.1:5000:5000"
    volumes:
      - registry-exapp-data:/var/lib/registry
    restart: unless-stopped
```

Für GreenMail folgt daraus: `container_name: nc-mcp-exapp-greenmail`, kein
veröffentlichter Port (Nextcloud erreicht ihn über das Docker-Netz
`nc-mcp-exapp-net`, Zeilen 139-152), oder wenn doch, dann ausdrücklich auf `127.0.0.1`
gebunden mit derselben Begründung.

## Gemeinsame Muster (gelten für mehrere neue Dateien)

### Pflichtheader je Familie als eine Konstante (D-18)
**Quelle:** `src/mcp_connector/nextcloud/clients/deck.py` Zeilen 59-65 und
`clients/ocs.py` Zeilen 39-43
**Anwenden auf:** `clients/tables.py` (v1-Generation), `clients/ocs.py::ocs_post` (v2)

Die Header sind eine `Mapping[str, str]`-Konstante mit `#:`-Begründung und werden per Aufruf
mit `dict(...)` kopiert, nie in place mutiert. Grund im Kommentar: "Without the first one
Nextcloud answers a browser login page with status 200". Kein `Origin`-Header, nirgends
(Recherche, Anti-Muster).

### Fehlersatz plus nächster Schritt, niemals eine Rohantwort
**Quelle:** `src/mcp_connector/errors.py` über `ToolError(message=..., hint=...)`, zentrale
Abbildung in `clients/ocs.py::_status_error` Zeilen 219-263
**Anwenden auf:** jede neue Datei mit Produktionscode

Jeder Fehler ist ein Satz plus genau eine Sache, die der Nutzer oder das Modell tun kann.
`_status_error` hängt "Nextcloud says: ..." an und ist damit schon die Antwort auf die
Wertform-400 der Tables-App; es wird kein neuer Fehlerpfad im Tables-Client gebaut.

### `require_app` als erste Zeile jedes Tools (SRV-04)
**Quelle:** `src/mcp_connector/tools/deck.py` Zeilen 56 und 83, Implementierung
`nextcloud/capabilities.py` Zeilen 101-110
**Anwenden auf:** `tools/tables.py`, beide Einstiegsfunktionen

```python
await capabilities.require_app(clients, APP)          # browse
caps = await capabilities.require_app(clients, APP)   # create, wenn ein Feld gebraucht wird
```

### Kappung im Tool, Kappung im Client, Kappung benannt in der Antwort
**Quelle:** `tools/deck.py` Zeilen 54 und 228-234
**Anwenden auf:** `tools/tables.py`, `clients/tables.py`

`capped = min(max(limit, 1), MAX_LIMIT)` im Tool, ein zweites Mal im Client (dort ohne
Default, damit ein Weglassen ein `TypeError` beim Entwickler und nicht ein Volltabellenlesen
beim Nutzer ist), und `truncated: True` in der Antwort, sobald mehr da war.

### Cursor-Handles statt offener Offsets
**Quelle:** `src/mcp_connector/paging.py` (91 Zeilen) mit dem Benutzungsmuster in
`tools/files.py` Zeilen 108-137 und 155-179
**Anwenden auf:** `tools/tables.py::browse` (offene Frage 3 der Recherche empfiehlt "Cursor ja")

```python
    offset = 0
    if cursor:
        state = paging.decode_cursor(cursor)
        paging.check_scope(state, "q", term, "search")
        offset = paging.read_offset(state)
    ...
    if len(hits) > offset + capped:
        result["truncated"] = True
        result["next"] = paging.encode_cursor({"o": offset + capped, "q": term, "f": target_folder})
```

Für Tables wäre der Scope-Schlüssel die Tabellen-Id, damit ein Handle einer anderen Tabelle
abgewiesen wird statt still die falsche Seite zu liefern.

### Registrierungs-Schicht: Annotationen, `compact`, `graceful`
**Quelle:** `src/mcp_connector/server/__init__.py` Zeilen 53-99
**Anwenden auf:** `server/reg_tables.py`

```python
# Honest annotations (D-16). snake_case in Python, camelCase on the wire.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATE_ONLY = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)


def compact(payload: object) -> str:
    """Serialise a tool answer without a single wasted byte (schema diet, D-14)."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
```

`graceful` (Zeilen 68-99) übersetzt `ToolError`, `httpx.TimeoutException` und
`httpx.RequestError` in eine Modellnachricht und benutzt `from None`, damit kein
httpx-Traceback eine URL nach draussen trägt. Neue Tools brauchen dafür keinen eigenen
Code, nur den Dekorator in dieser Reihenfolge: `@mcp.tool(...)` aussen, `@graceful` darunter.

### Fremder Text bekommt `marks.without_marks`
**Quelle:** `src/mcp_connector/tools/marks.py` Zeile 56, Aufrufstellen `tools/chatgpt.py`
Zeilen 167, 199, 224, 295 und `tools/context.py` Zeile 313
**Anwenden auf:** jedes neue Freitextfeld, das Tables-Zellwerte in den Modellkontext hebt
(Recherche, Bedrohungstabelle: Prompt Injection)

### Testgerüst für Unit-Tests einer Familie
**Quelle:** `tests/unit/test_deck_client.py` Zeilen 26-49, `tests/unit/test_deck_tools.py`
Zeilen 27-60
**Anwenden auf:** `tests/unit/test_tables_client.py`, `tests/unit/test_tables_tools.py`

`BASE`/`USER`/`SECRET`-Konstanten, volle Endpunkt-URLs als eingefrorene Literale, `creds`- und
`client`-Fixture, `fixture()`-Leser auf `tests/fixtures`, `envelope()`-Helfer für OCS,
`@pytest.fixture(autouse=True) def _empty_cache()` mit `capabilities.clear_cache()`,
`@pytest.mark.anyio` je Test.

### Integrationstest-Skelett
**Quelle:** `tests/integration/test_deck_roundtrip.py` Zeilen 33-60 (App-Passwort-Schicht) und
`tests/integration/test_exapp_dav_matrix.py` Zeilen 58-94 (AppAPI-Schicht), Fixtures in
`tests/conftest.py` Zeilen 30-68
**Anwenden auf:** `tests/integration/test_tables_roundtrip.py` (nimmt `live_env`),
`tests/integration/test_exapp_mail_reach.py` (nimmt `exapp_env`)

`pytestmark = [pytest.mark.integration, pytest.mark.anyio]`, Skip mit dem Namen der fehlenden
Umgebungsvariable, Laufanleitung im Modul-Docstring, `follow_redirects=False, timeout=30.0`.

## Teil-Treffer und offene Muster-Lücken

| Datei | Rolle | Datenfluss | Was kein Vorbild hat |
|-------|-------|------------|----------------------|
| `tests/integration/test_exapp_mail_reach.py` | test (Spike) | protokollierende Messung | Der `_probe`-Helfer, der Status, Content-Type, Form und Körperanfang zurückgibt statt zu behaupten. Die Codebasis hat nur behauptende Integrationstests. Skizze in `08-RESEARCH.md`, Abschnitt "Spike: eine Messzeile statt einer Vermutung"; die 120-Zeichen-Grenze und das "nur HTML und Login-Redirect sind Fehlschlag"-Kriterium sind neu und gehören begründet in den Docstring |
| `scripts/check_tool_budget.py` (Pro-Tool-Grenze) | gate | batch | Die zweite Behauptung "kein einzelnes Tool über 1400 Bytes" existiert noch nicht. Die Datenquelle (`per_tool`, Zeilen 37-43) und die Fehlerausgabe (Zeilen 49-52) sind aber vorhanden, es fehlt nur der Vergleich |
| `compose.exapp.yml` (GreenMail) | config | Dienst | Kein bestehender Dienst nimmt `GREENMAIL_OPTS`-artige Umgebungskonfiguration; `nextcloud` (Zeilen 45-86) ist das nächstliegende Vorbild für einen Dienst mit `environment`-Block |

**Keine Datei der Phase steht ohne Analog da.** Der Planer kann für jede neue Datei eine
konkrete Vorbilddatei und Zeilenspanne in die Plan-Aktion schreiben.

## Metadaten

**Suchraum für Analoga:** `src/mcp_connector/` (alle Unterverzeichnisse), `tests/unit/`,
`tests/contract/`, `tests/integration/`, `tests/fixtures/`, `scripts/`, `docs/`,
Projektwurzel (`README*.md`, `CHANGELOG.md`, `compose.exapp.yml`)
**Vollständig gelesene Dateien:** `clients/deck.py`, `clients/ocs.py`, `nextcloud/capabilities.py`,
`tools/deck.py`, `server/reg_deck.py`, `server/__init__.py`, `paging.py`,
`tests/contract/test_tool_surface.py`, `tests/contract/test_no_destructive_calls.py`,
`tests/integration/test_deck_roundtrip.py`, `tests/integration/test_exapp_dav_matrix.py`,
`scripts/check_tool_budget.py`
**Gezielt gelesene Abschnitte:** `tools/files.py` 95-184, `tests/unit/test_deck_client.py` 1-120,
`tests/unit/test_deck_tools.py` 1-60, `tests/conftest.py` 30-68, `docs/spike-dav.md` 1-80,
`scripts/bootstrap_exapp.sh` 251-283, `README.md` 185-205, `CHANGELOG.md` 1-40,
`compose.exapp.yml` 124-157
**Kartierungsdatum:** 2026-08-21
