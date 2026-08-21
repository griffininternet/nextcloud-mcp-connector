# Phase 9: Talk, Muster-Karte

**Kartiert:** 2026-08-21
**Analysierte Dateien:** 33 (7 neu, 26 geändert)
**Analoga gefunden:** 32 / 33 (eine Datei ohne Vorbild: der Schalter-Export in `entry_exapp.py`)

> Diese Datei beantwortet genau eine Frage: **Von welcher bestehenden Datei kopiert eine neue
> Datei ihr Muster, und welche Zeilen sind das konkret?** Sie wiederholt weder die
> Talk-API-Referenz noch die fünfzehn Korrekturen aus `09-RESEARCH.md`. Wo eine Korrektur das
> kopierte Muster ändert, steht die Kennung (T1 bis T15) am Muster.
>
> **Die Tables-Familie aus Phase 8 ist das frischeste vollständige Vorbild.** Sie deckt alle
> vier Schichten ab (Client, Tool, Registrierung, Tests) plus die Gate-Nachzüge, und sie ist
> zwölf Tage alt. Wo Tables und eine ältere Familie sich unterscheiden, gilt Tables.

## Datei-Klassifikation

### Produktionscode

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Passung |
|----------------------|-------|------------|-----------------|---------|
| `src/mcp_connector/nextcloud/clients/talk.py` | client (HTTP-Adapter) | request-response, lesend plus ein Create | `nextcloud/clients/tables.py` | exakt |
| `src/mcp_connector/tools/talk.py` | service (Fachlogik, Projektion) | CRUD-read plus create | `tools/tables.py` | exakt |
| `src/mcp_connector/server/reg_talk.py` | route (Tool-Registrierung) | request-response | `server/reg_tables.py` | exakt |
| `src/mcp_connector/nextcloud/clients/ocs.py` | client (gemeinsamer Parser) | transform | dieselbe Datei, Zeile 49-50 | Selbst-Analog |
| `src/mcp_connector/nextcloud/capabilities.py` | service (App-Erkennung, Cache) | request-response, gecacht | dieselbe Datei, `deck`- und `notes`-Zweig | Selbst-Analog |
| `src/mcp_connector/config.py` | config (Env-Leser) | transform | `config.dns_rebinding_protection` Zeile 314-318 | exakt |
| `src/mcp_connector/entry_exapp.py` | config (Startpfad) | batch, einmal beim Start | **keins** (T15, Weg A) | kein Analog |
| `src/mcp_connector/exapp/config_values.py` | config (Overlay-Lesepfad) | request-response | dieselbe Datei, `oauth_allowlist_only` | Selbst-Analog |
| `src/mcp_connector/exapp/admin_settings.py` | config (Declarative-Settings-Form) | request-response | dieselbe Datei, `allowlist_field` Zeile 139-145 | Selbst-Analog |
| `src/mcp_connector/exapp/ui/strings.py` | config (UI-Texte) | statisch | `ADMIN_FIELD_ALLOWLIST_*` Zeile 605-611 | Selbst-Analog |

### Tests

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Passung |
|----------------------|-------|------------|-----------------|---------|
| `tests/unit/test_talk_client.py` | test (unit, respx) | request-response | `tests/unit/test_tables_client.py` | exakt |
| `tests/unit/test_talk_tools.py` | test (unit) | CRUD | `tests/unit/test_tables_tools.py` | exakt |
| `tests/integration/test_talk_roundtrip.py` | test (integration, live) | CRUD plus Messung | `tests/integration/test_tables_roundtrip.py` | exakt |
| `tests/contract/test_tool_surface.py` | test (contract) | statische Behauptung | dieselbe Datei, Tables-Block Zeile 248-299 | Selbst-Analog |
| `tests/contract/test_no_destructive_calls.py` | test (contract, AST/Grep-Gate) | transform | dieselbe Datei, `TABLES_ROUTES` Zeile 70-100 | Selbst-Analog |
| `tests/unit/test_ocs_capabilities.py` | test (unit) | transform | dieselbe Datei, `tables`-Fälle | Selbst-Analog |
| `tests/unit/test_exapp_admin_settings.py` | test (unit) | statische Behauptung | dieselbe Datei, Zeile 114-145 | Selbst-Analog |
| `tests/unit/test_exapp_config_values.py` | test (unit) | request-response | dieselbe Datei, Switch-Tests Zeile 636-690 | Selbst-Analog |
| `tests/unit/test_exapp_entry.py` | test (unit) | batch | dieselbe Datei (Overlay-Weg) | Selbst-Analog |
| `tests/unit/test_config.py` | test (unit) | transform | dieselbe Datei, `test_exapp_configured_needs_both_id_and_secret` Zeile 133-145 | exakt |
| `tests/integration/test_permission_fidelity_exapp.py` | test (integration, zwei Konten) | CRUD | dieselbe Datei, Tables-Block Zeile 308-470 | Selbst-Analog |
| `tests/fixtures/talk_rooms.json` | fixture | statische Daten | `tests/fixtures/deck_boards.json`, `tables_tables.json` | exakt |
| `tests/fixtures/talk_messages.json` | fixture | statische Daten | `tests/fixtures/tables_rows_simple.json` | rollen-nah |

### Skripte und Doku

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Passung |
|----------------------|-------|------------|-----------------|---------|
| `scripts/bootstrap_exapp.sh` | config (Topologie) | batch | `ensure_app tables` Zeile 891, `ensure_app mail` Zeile 892 | exakt |
| `scripts/bootstrap_test_nc.sh` | config (Topologie) | batch | `ensure_app notes` Zeile 159 ff. | exakt |
| `scripts/acceptance_all_tools.py` | test (Abnahme über stdio) | request-response | dieselbe Datei, `EXPECTED_TOOLS = 18` Zeile 52 | Selbst-Analog |
| `scripts/check_tool_budget.py` | config (Gate) | batch | dieselbe Datei, Messzeilen-Kommentar Zeile 15-33 | Selbst-Analog |
| `README.md`, `README.de.md`, `README.fr.md` | doc | statisch | die zwei Tables-Zeilen der Tool-Tabelle | exakt |
| `docs/oauth-setup.md` | doc | statisch | Feldtabelle Zeile 113-119 | Selbst-Analog |
| `docs/client-setup.md`, `docs/conference-demo.md` | doc | statisch | dieselbe Datei (Zahlen) | Selbst-Analog |
| `appinfo/info.xml` | config (Store-Manifest) | statisch | die drei `<description>`-Blöcke, Tables-Erwähnung | Selbst-Analog |
| `CHANGELOG.md` | doc | statisch | der Tables-Eintrag aus Phase 8 | exakt |

**Nicht anfassen** (T13, gehört zu Phase 11): `src/mcp_connector/ids.py`,
`src/mcp_connector/provider_map.py`, `src/mcp_connector/tools/chatgpt.py`,
`src/mcp_connector/tools/context.py`, `pyproject.toml`, `uv.lock`.

## Muster-Zuordnungen

### `nextcloud/clients/talk.py` (client, request-response)

**Analog:** `src/mcp_connector/nextcloud/clients/tables.py`

**Modul-Docstring-Muster** (`tables.py` Zeile 1-42): Der Docstring des Analogs hat sechs
Absätze und jeder trägt genau eine Aussage: (1) welche API-Generationen die Familie
benutzt und warum die Trennlinie nicht beim Aufrufer landet, (2) die Pflichtheader nach
D-18, (3) die Falle der Familie, (4) dass die Routen eine zugesagte API sind (K10), (5) dass
eine Grenze erzwungen und nicht angeboten wird, (6) was bewusst fehlt plus (7) dass es kein
Retry gibt. Für Talk wird (1) zu "Räume sind v4, Chat ist v1", (3) zu den vier
Leseparametern (T6), (5) zu `MAX_MESSAGES`, (6) zu "kein Edit-, Delete-, Schedule- oder
Silent-Pfad".

```python
"""Tables client: two API generations of one app, reading plus one create path.
...
Two headers are mandatory on **every** request, a plain GET included: ``OCS-APIRequest:
true`` and ``Content-Type: application/json`` (D-18). Without the first one Nextcloud
answers a browser login page with status 200, which is why the headers are one constant
here instead of an argument anyone could forget.
...
There is deliberately no update, no remove, no column, no schema and no share path in this
module. The server promise is that it can neither overwrite nor remove nor re-share
anything, and the cheapest way to keep a promise is to never write the code that could
break it (threat T-08-11).

There is no retry on the POST, on any layer. ...
"""
```

**Import-Muster** (`tables.py` Zeile 44-51): genau diese Reihenfolge und Tiefe übernehmen,
`re` kommt für `_TOKEN` dazu.

```python
from collections.abc import Mapping
from typing import Any

import httpx

from ...errors import ToolError
from ..credentials import Credentials
from . import ocs
```

**Präfix- und Grenzkonstanten-Muster** (`tables.py` Zeile 53-84): jede Konstante trägt einen
`#:`-Kommentar, der die Begründung enthält, nicht die Wiederholung des Namens.

```python
#: Generation 2. It sits below ``/ocs/v2.php`` and is therefore built through
#: :func:`ocs.ocs_url`, never by string concatenation with the base URL.
V2_PREFIX = "/apps/tables/api/2"

#: Web route of a single table, used for the ``url`` field a human clicks. The fragment is
#: part of the route: the Tables frontend is a single page application.
TABLES_WEB_PREFIX = "/index.php/apps/tables/#/table"

#: Upper bound of one row read. Never build a rows URL without a limit: the parameter looks
#: optional and answers with the whole table when it is left out (pitfall 1).
MAX_ROWS = 200

#: The two mandatory headers of D-18, plus the ``Accept`` that keeps a proxy from
#: negotiating HTML. Copied per request, never mutated in place.
TABLES_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

Für Talk: `ROOM_PREFIX = "/apps/spreed/api/v4/room"`, `CHAT_PREFIX = "/apps/spreed/api/v1/chat"`,
`TALK_WEB_PREFIX = "/index.php/call"`, `MAX_MESSAGES = 50` und `READ_ONLY_PARAMS` (Muster 1
aus RESEARCH). **Entscheidung, die aus diesem Analog folgt:** Talk braucht **keine** eigene
Header-Konstante wie `TABLES_HEADERS`, weil beide Talk-Routen unter `/ocs/v2.php` liegen und
`ocs.ocs_get`/`ocs.ocs_post` die Header schon setzen (`ocs.py` Zeile 41-44, 79-84, 103-108).
Tables brauchte sie nur wegen der Generation-1-Route, die per `client.get` direkt gebaut wird.

**Pfad-Wächter-Muster** (`tables.py` Zeile 210-218): wortwörtlich die Vorlage für `_path_token`
(T9), nur mit `re.fullmatch(r"[a-z0-9]{4,30}", ...)` statt `.isdigit()`.

```python
def _path_id(value: str | int, what: str) -> str:
    """Ids are numeric in Tables; anything else is a bug or an attempt (threat T-08-06)."""
    text = str(value).strip()
    if not text.isdigit():
        raise ToolError(
            message=f"{value!r} is not a numeric {what}.",
            hint="Use an id from tables_browse; Tables addresses tables and columns by number.",
        )
    return text
```

**Lese-Muster mit erzwungener Grenze** (`tables.py` Zeile 149-177): das Vorbild für
`get_messages`. Kappen im Client (`min(max(int(limit), 1), MAX_ROWS)`), `limit` als
Keyword **ohne Default**, und der Docstring erklärt, warum das Weglassen ein Fehler beim
Entwickler ist.

```python
async def get_rows_simple(
    client: httpx.AsyncClient,
    creds: Credentials,
    table_id: str | int,
    *,
    limit: int,
    offset: int = 0,
) -> list[list[Any]]:
    """...
    ``limit`` is a keyword without a default on purpose. The parameter is nullable in the
    API, and an omitted limit reads the entire table, so a missing limit has to be an error
    at the developer rather than a full table read at the user (pitfall 1). The value is
    capped at :data:`MAX_ROWS` and lifted to at least one, and a negative offset becomes
    zero, because the URL is built here and nowhere else.
    """
    table = _path_id(table_id, "table id")
    capped = min(max(int(limit), 1), MAX_ROWS)
    response = await client.get(...)
```

**Create-Muster** (`tables.py` Zeile 180-207): das Vorbild für `send_message`. Abweichungen:
`ocs.parse_ocs` bleibt, aber der Statuscode ist **201** (T1), und der Docstring sagt hier
"200, nicht 201", dort muss er "201, nicht 200" sagen. Das "kein Retry"-Absatz wird wörtlich
übernommen.

```python
async def create_row(
    client: httpx.AsyncClient, creds: Credentials, table_id: str | int, *,
    data: Mapping[str, Any] | str,
) -> dict[str, Any]:
    """...
    There is no retry. If this call times out, that does not mean nothing was written, and
    a second attempt would duplicate a row that no tool of this server can remove again.
    """
    table = _path_id(table_id, "table id")
    response = await ocs.ocs_post(
        client, creds, f"{V2_PREFIX}/{NODE_COLLECTION_TABLES}/{table}/rows", {"data": data},
    )
    return _as_dict(ocs.parse_ocs(response, what="the new row"), what="a row")
```

**Formprüfer-Muster** (`tables.py` Zeile 86, 221-236): `_SHAPE_HINT` als Modulkonstante plus
`_as_list` und `_as_dict`. Beide eins zu eins übernehmen, `_SHAPE_HINT` auf Talk umtexten.

```python
_SHAPE_HINT = "Check that the Tables app is enabled and up to date on that instance."


def _as_list(payload: Any, what: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ToolError(
            message=f"Nextcloud answered with something that is not a list of {what}.",
            hint=_SHAPE_HINT,
        )
    return [item for item in payload if isinstance(item, dict)]
```

**Web-URL-Muster** (`tables.py` Zeile 96-98): die SSRF-Grenze. Immer aus `creds.base_url`,
nie aus einer Antwort.

```python
def web_url(creds: Credentials, table_id: str | int) -> str:
    """The link a human can open. Always built from the configured base URL."""
    return f"{creds.base_url}{TABLES_WEB_PREFIX}/{table_id}"
```

Für Talk: `f"{creds.base_url}{TALK_WEB_PREFIX}/{token}"`, und für eine einzelne Nachricht
`#message_{id}` als Fragment (T13 nennt den Deep-Link, aber das Auflösen ist Phase 11).

**Neu gegenüber dem Analog, ohne Vorbild in dieser Codebasis:** die Rückgabe von Körper
**und** Header als Tupel (T8) und die 304-Vorprüfung (T2). Beide stehen als Muster 3 in
`09-RESEARCH.md` und sind dort schon ausformuliert. `tables.py` hat kein Analog dafür, weil
keine seiner Routen einen Header als Nutzlast trägt.

---

### `tools/talk.py` (service, CRUD-read plus create)

**Analog:** `src/mcp_connector/tools/tables.py`

**Modul-Docstring-Muster** (`tables.py` Zeile 1-26): vier fette Überschriftensätze, jeder mit
einer Aussage plus Begründung, und ein Schlussabsatz "Deliberately absent".

```python
"""Tables tools: one browse tool with a level, and one create-only write (D-06, D-14).

**One tool, three levels.** ``tables_browse(level=...)`` walks the tables, ... Three
separate tools would cost three slots in every client that limits them ... The answer
envelope is the same on every level (``level``, ``count``, ``results``), so the model
learns one shape instead of three.

**The limit is enforced, not offered.** ... Truncation is named here, never silent.

**Two things are explained before they can fail.** A missing or disabled Tables app stops
both tools at the capabilities check, before the first Tables request (SRV-04). And a user
without a write permission ... The middleware stays the authority; the pre-check is only
the better error message.

Deliberately absent: update, delete, ... The client below has no code for any of it, which
is what makes the create-only annotation of ``tables_create_row`` honest rather than a
promise (T-08-11).
"""
```

**Konstanten- und Hint-Muster** (`tables.py` Zeile 37-47): `APP`, `LEVELS`, `DEFAULT_LIMIT`,
`MAX_LIMIT`, dann die Hint-Konstanten. Für Talk kommen `MAX_CONVERSATIONS = 50`,
`MAX_MESSAGE_BYTES` (A6, UTF-8-Byte-Kappe, benannte Konstante an genau einer Stelle) und `KEPT_TYPES`
(Positivliste, Muster 6) dazu.

```python
APP = "tables"

#: The three navigation levels of ``tables_browse``, in the order a model walks them.
LEVELS = ("tables", "columns", "rows")

#: TABLES-01: a row read without an explicit limit reads this many rows and not the table.
DEFAULT_LIMIT = 25
MAX_LIMIT = 200

_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."
_TABLE_HINT = "Call tables_browse with level=tables first; it lists the table ids."
```

**Browse-Einstiegs-Muster** (`tables.py` Zeile 78-103): die Reihenfolge ist das Muster.
Level-Validierung, Kappen, **dann** `require_app`, dann die Verzweigung. Für Talk gilt
dieselbe Reihenfolge, mit dem einen Unterschied, dass `talk_send` den Schalter **vor**
`require_app` liest (Falle 10).

```python
async def browse(
    clients: NcClients,
    level: str = "tables",
    table_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Walk the user's Tables: the tables, the columns of one table, or its rows."""
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Tables level.", hint=_LEVEL_HINT)
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "tables":
        return _envelope(level, await _tables(clients), capped)

    table = str(table_id or "").strip()
    if not table:
        raise ToolError(message=f"level={level!r} needs a table_id.", hint=_TABLE_HINT)
```

**Filter-vor-Projektion-Muster** (`tables.py` Zeile 275-278): der Ort, an dem Talk zusätzlich
**sortieren** muss (T5, Falle 5). Das Analog filtert nur, weil Tables eine Server-Reihenfolge
hat. Für Talk: sortieren nach `lastActivity` absteigend, **dann** `isArchived` filtern,
**dann** kappen.

```python
async def _tables(clients: NcClients) -> list[dict[str, Any]]:
    """Table ids and sizes, plus whether the user may add a row at all."""
    tables = await tables_client.get_tables(clients.client, clients.creds)
    return [_table(table) for table in tables if not table.get("archived")]
```

**Projektions-Muster** (`tables.py` Zeile 281-298): der Docstring nennt namentlich, was
wegfällt, und ein optionales Feld kommt nur dazu, wenn es einen Wert hat.

```python
def _table(table: dict[str, Any]) -> dict[str, Any]:
    """Project one table onto the fields a model reads, and drop the rest.

    ``GET /api/2/tables`` answers with the views of every table including their filters and
    sort orders, plus ``columnOrder``, ``sort``, ``ownerDisplayName``, ``createdBy`` and
    ``lastEditBy``. None of that survives here: every key is paid for in every answer.
    """
    entry: dict[str, Any] = {
        "id": table.get("id"),
        "title": _text(table.get("title") or ""),
        ...
        "can_create": _may_create(table),
    }
    if table.get("emoji"):
        entry["emoji"] = table["emoji"]
    return entry
```

Für Talk: 59 Pflichtfelder gehen rein, elf kommen raus (Feldauswahl in `09-RESEARCH.md`).
`truncated: true` an der einzelnen Nachricht folgt genau dieser "nur wenn gesetzt"-Regel
(Muster 7), und `edited: true` ebenso.

**Berechtigungs-Vorprüfungs-Muster** (`tables.py` Zeile 401-420): **das wichtigste Analog der
ganzen Phase.** Es ist dieselbe Fehlerklasse wie T3, und der Docstring ist die Vorlage für
den Docstring von `_may_send`: er benennt das falsche Feld, das naheliegt, sagt warum es
falsch ist, und nennt die Präzedenz.

```python
def _may_create(table: dict[str, Any]) -> bool:
    """Whether this account may add a row to this table (K5).

    The naive read of this question is wrong on the most common case of all. Tables reports
    the permissions of a *share* in ``onSharePermissions``, and ``TableService::
    setIsSharedState`` sets ``Permissions(read: true)`` together with ``isShared = false``
    for a table the caller owns, while Nextcloud's own ``PermissionsService::
    checkPermission`` short circuits on ``userIsElementOwner`` long before it looks at that
    object. A literal ``if not onSharePermissions.create: refuse`` would therefore refuse
    every user on their own table. That is the same trap as ``canCreateBoards`` in phase 1:
    a field that answers a different question than the one being asked.
    """
    permissions = table.get("onSharePermissions")
    permissions = permissions if isinstance(permissions, dict) else {}
    if not table.get("isShared"):
        return True
    return bool(permissions.get("create") or permissions.get("manage"))
```

**Verweigerungs-Muster mit nächstem Schritt** (`tables.py` Zeile 136-144): so sieht die
Absage von `talk_send` aus, viermal (readOnly, Typ 4, kein Bit 128, `@all`/`@here`, zu lang).

```python
    if not _may_create(info):
        raise ToolError(
            message=f"No permission to add a row to table {table} ({_text(info.get('title'))}).",
            hint=(
                "This table is shared with this account without a create permission. Ask its "
                "owner in Nextcloud for a write permission, or pick a table that tables_browse "
                "reports with can_create."
            ),
        )
```

**Cursor-Muster** (`tables.py` Zeile 330-336 plus 364-369): `paging.decode_cursor`,
`paging.check_scope` mit einem Ein-Buchstaben-Schlüssel, `paging.read_offset`, und der
Kommentar begründet, warum ein fremdes Handle abgelehnt wird statt still angewendet.

```python
    offset = 0
    if cursor:
        state = paging.decode_cursor(cursor)
        # A handle of another table would silently answer with the wrong page, and the model
        # has no way to notice. Saying so costs one round trip; guessing is a wrong answer.
        paging.check_scope(state, "t", table, "table")
        offset = paging.read_offset(state)
    ...
    if more:
        answer["truncated"] = True
        answer["next"] = paging.encode_cursor({"o": offset + len(results), "t": table})
```

Für Talk: Scope-Schlüssel `"c"` mit dem Token als Wert, `o` ist die Id aus
`X-Chat-Last-Given`. **Die Ableitung von `more` wird ausdrücklich nicht kopiert** (T8): das
Analog leitet sie aus `len(results)` und `rowsCount` ab, Talk leitet sie allein aus der
Anwesenheit des Headers ab. Der lange Kommentar an Zeile 354-363 des Analogs ist die
Begründung, warum dieser Punkt einen Kommentar braucht, und die Talk-Fassung braucht einen
eigenen mit dem umgekehrten Inhalt.

**Fremdtext-Muster** (`tables.py` Zeile 423-450): `_text` für eine Zeichenkette, `_clean`
rekursiv für jede Form. Für Talk gilt `_text` auf `actorDisplayName` und auf den aufgelösten
Nachrichtentext, plus auf jeden Namen aus `messageParameters` (Muster 5).

```python
def _text(value: Any) -> str:
    """Foreign text on its way into the model context, with our own markers removed.

    Cell values and titles are written by whoever may write to the table, so they are the
    place where a document could otherwise claim to be this server talking (T-08-14).
    """
    return marks.without_marks(str(value))
```

**Envelope-Muster** (`tables.py` Zeile 453-459): eine Antwortform für alle Ebenen, Kappung
benannt. Für Talk identisch, plus `token` und `conversation` auf der Nachrichtenebene.

```python
def _envelope(level: str, results: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for all three levels, truncation named instead of silent."""
    kept = results[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(results) > len(kept):
        answer["truncated"] = True
    return answer
```

**Freiform-Parameter-Muster** (`tables.py` Zeile 106-186): `values` ist ein **String** und
kein Mapping, damit kein `$defs` ins Schema gerät, plus `_parse_values` mit vier getrennten
Absagen. Für Talk ist die Nachricht ohnehin ein String, aber die Begründung im Docstring
("A ``dict`` parameter would pull ``additionalProperties`` or ``$defs`` into the input
schema") ist das Muster, das die Schema-Diät der Familie erklärt.

---

### `server/reg_talk.py` (route, request-response)

**Analog:** `src/mcp_connector/server/reg_tables.py` (die ganze Datei, 71 Zeilen, ist die
Vorlage)

**Modul-Docstring** (`reg_tables.py` Zeile 1-11):

```python
"""Registration of the tables tools. The logic lives in :mod:`mcp_connector.tools.tables`.

``level`` is a ``Literal`` and therefore an enum in the input schema, not a free string:
the model sees the three valid values instead of guessing "row" or "sheets" and paying a
round trip for the correction (D-06, D-14).

Both tools are listed unconditionally, even on an instance without the Tables app. A
credential dependent ``tools/list`` is not cacheable, breaks the token budget gate and
surprises clients that persist tool lists; the honest answer to a missing app is the
sentence the tool returns (SRV-04).
"""
```

**Imports und Registrierungs-Muster** (`reg_tables.py` Zeile 13-47): leere Strings statt
`None` als Default, `Literal` für das Level, `Field(ge=..., le=...)` aus den Tool-Konstanten,
`structured_output=False`, `@graceful`, `deps.resolve_clients(ctx)`, `compact(...)`.

```python
from typing import Annotated, Literal

from mcp.server.mcpserver import Context
from pydantic import Field

from .. import deps
from ..tools import tables as tables_tools
from . import CREATE_ONLY, READ_ONLY, compact, graceful, mcp


@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def tables_browse(
    level: Annotated[
        Literal["tables", "columns", "rows"],
        Field(description="What to list; columns and rows need a table_id"),
    ] = "tables",
    table_id: Annotated[str, Field(description="Table id from level=tables, e.g. 7")] = "",
    limit: Annotated[
        int, Field(ge=1, le=tables_tools.MAX_LIMIT, description="Maximum number of entries")
    ] = tables_tools.DEFAULT_LIMIT,
    cursor: Annotated[str, Field(description="Handle from a truncated answer, next page")] = "",
    ctx: Context | None = None,
) -> str:
    """List the user's Tables, the columns of one table, or its rows."""
    clients = deps.resolve_clients(ctx)
    return compact(
        await tables_tools.browse(
            clients,
            level=level,
            table_id=table_id or None,
            limit=limit,
            cursor=cursor or None,
        )
    )
```

**Create-Registrierungs-Muster** (`reg_tables.py` Zeile 50-71): `CREATE_ONLY`, und der
Docstring des Werkzeugs trägt den Retry-Satz. Genau hier reisst das Budget, wenn der
Docstring von `talk_send` zum Absatz wird (Falle 8, Pro-Tool-Deckel 1400 Bytes).

```python
@mcp.tool(annotations=CREATE_ONLY, structured_output=False)
@graceful
async def tables_create_row(
    table_id: Annotated[str, Field(description="Table id from tables_browse")],
    values: Annotated[str, Field(description=(...))],
    ctx: Context | None = None,
) -> str:
    """Add one row to an existing table; never changes or deletes an existing row.

    A timeout does not mean nothing was written. Read back with tables_browse(level="rows")
    instead of calling this a second time.
    """
    clients = deps.resolve_clients(ctx)
    return compact(await tables_tools.create_row(clients, table_id=table_id, values=values))
```

Die Annotationen kommen unverändert aus `server/__init__.py` Zeile 54-60:

```python
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATE_ONLY = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False,
)
```

`server/__init__.py` Zeile 102-114 lädt jedes `reg_*`-Modul automatisch: **keine Änderung an
`server/__init__.py` nötig**, eine neue Datei genügt.

---

### `nextcloud/clients/ocs.py` (client, geändert: `_OK_STATUS`)

**Analog:** dieselbe Datei, Zeile 49-50. Das Muster ist der `#:`-Kommentar, der die Zahlen
erklärt, statt sie nur zu nennen.

```python
#: ``100`` is the OCS v1 success code, ``200`` the v2 one. Instances answer with either.
_OK_STATUS = frozenset({100, 200})
```

Nachzuziehen (T1): `201` dazu, plus ein Satz, warum. Vorbild für die Art der Begründung ist
der Kommentar an Zeile 217-219 derselben Datei, der eine Ausnahme im Statuswald erklärt:

```python
    if status >= 500 and status != 507:
        # 507 is not a server fault but a full account, and its body carries the app's own
        # wording, so it belongs to the status mapping below and not into this branch.
```

**Nicht anfassen:** `_check_transport` Zeile 196-203. Die 3xx-Behandlung bleibt wie sie ist,
die 304 wird im Talk-Client **vor** `parse_ocs` abgefangen (T2). Der Grund gehört in den
Docstring von `get_messages`, nicht in diese Datei.

---

### `nextcloud/capabilities.py` (service, geändert: `spreed`)

**Analog:** dieselbe Datei. Talk verhält sich wie **Notes und Deck** (Präsenz der Sektion),
nicht wie Tables (`enabled`-Feld). Der Kommentar an Zeile 150-153 sagt genau das und ist die
Stelle, an der die Unterscheidung schon dokumentiert ist:

```python
        # The one place that differs from Notes and Deck: Tables publishes an explicit
        # ``enabled``, and an app that is installed but switched off is absent as far as this
        # server is concerned, so the flag is read from the field and not from the presence
        # of the section. No gate on ``version``: the API generations are what matter here.
        tables_available=bool(tables.get("enabled")) if tables else False,
        tables_api_versions=_versions(tables, "apiVersions"),
```

**Defensives Sektionslesen** (Zeile 137-142) plus **`_MISSING`-Muster** (Zeile 41-63): ein
Satz, was fehlt, plus eine Sache, die der Nutzer tun kann.

```python
    tables = section.get("tables")
    tables = tables if isinstance(tables, dict) else None
...
    "tables": (
        "The Tables app is not enabled on this Nextcloud.",
        (
            "Ask an administrator to enable the Tables app, or keep the list in a note "
            "created with notes_create."
        ),
    ),
```

**`has()`-Muster** (Zeile 78-88): der Schlüssel heisst `spreed`, nicht `talk`, weil das
Capabilities-Dokument ihn so nennt.

```python
    def has(self, app: str) -> bool:
        """Whether ``app`` is installed. Unknown names are a programming error."""
        flags = {"notes": ..., "deck": ..., "tables": self.tables_available}
        try:
            return flags[app]
        except KeyError:
            raise ValueError(f"{app!r} is not an optional app this server checks") from None
```

Ausserdem nachzuziehen, weil der Modul-Docstring die Zahl nennt (Zeile 3-11): "reports Notes,
Deck and Tables" und "Only these three optional apps are checked here".

**Neu gegenüber dem Analog:** `spreed_features: tuple[str, ...]` und
`spreed_chat_max_length: int`. `_versions` (Zeile 159-168) ist die Vorlage für den
Feature-Tupel-Leser, weil es dieselbe Aufgabe hat: eine Liste akzeptieren, einen einzelnen
String tolerieren, alles andere ignorieren.

---

### `config.py` (config, geändert: `ENV_TALK_SEND` und `talk_send_enabled`)

**Analog:** `config.dns_rebinding_protection` Zeile 314-318 (die Signatur, die
`os.environ`-oder-Mapping-Regel und die Wertmengen-Prüfung) plus `config.exapp_configured`
Zeile 195-204 (ein `bool`-Leser mit Docstring, der die Blank-Regel benennt).

```python
def dns_rebinding_protection(env: Mapping[str, str] | None = None) -> bool:
    """Whether the Host header check stays armed. Off only behind a trusted proxy."""
    source = os.environ if env is None else env
    value = (source.get(ENV_DISABLE_DNS_REBINDING) or "").strip().lower()
    return value not in _TRUE_VALUES
```

```python
def exapp_configured(env: Mapping[str, str] | None = None) -> bool:
    """True when this process was deployed as an ExApp, by the same rule as the bearer.

    A blank value counts as unset: an empty ``APP_SECRET`` in a compose file is a typo,
    not a request to authenticate everyone.
    """
    source = os.environ if env is None else env
```

**Env-Namens-Muster** (Zeile 39-46): die `NC_MCP_*`-Gruppe, alphabetisch nach Zweck
gruppiert, `ENV_TALK_SEND = "NC_MCP_TALK_SEND"` gehört zur ersten Gruppe.

**Wertmengen-Muster** (Zeile 70): `_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})`
existiert schon in `config.py`. T15 verlangt zusätzlich eine `_FALSE_VALUES`-Menge und einen
Test, der sie gegen `config_values.TRUE_VALUES`/`FALSE_VALUES` und
`oauth/registry._TRUE_VALUES` gleichsetzt. Das Muster für "held equal by a test" steht als
Kommentar in `config_values.py` Zeile 129-133:

```python
#: The spellings a switch may arrive in. Aligned with the two sets of ``oauth/registry.py``
#: on purpose and held equal by a test: a value that arms a switch in the environment has to
#: arm the same switch when it comes out of the admin form, or an administrator debugs a
#: difference nobody wrote down.
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
FALSE_VALUES = frozenset({"0", "false", "no", "off"})
```

**Wichtig, weil `dns_rebinding_protection` es umgekehrt macht:** dort ist der Default "an" und
die Variable schaltet **ab** (`value not in _TRUE_VALUES`). `talk_send_enabled` hat denselben
Default "an", aber der Wert schaltet **ein** (`NC_MCP_TALK_SEND=0` schaltet aus). Also
`return value not in _FALSE_VALUES` und nicht `value in _TRUE_VALUES`, sonst wäre ein
unverständlicher Wert ein stilles Aus. Diese eine Zeile ist der Ort, an dem das Analog nicht
wörtlich kopiert werden darf.

---

### `entry_exapp.py` (config, geändert: der Schalter erreicht den Tool-Lesepfad)

**Kein Analog.** Das ist der einzige Punkt der Phase ohne Vorbild (T15, A7). Was es gibt,
sind zwei Muster, die die neue Zeile umgeben:

**`_resolved_env`-Docstring** (`entry_exapp.py` Zeile 239-264) ist das Vorbild für die Art
der Begründung, die die neue Zeile braucht: er zählt die drei verworfenen Alternativen samt
Preis auf und benennt den Preis der gewählten Lösung ausdrücklich.

```python
def _resolved_env() -> tuple[dict[str, str], frozenset[str]]:
    """The deploy environment with the values an administrator set in Nextcloud on top.
    ...
    Resolved exactly once, here, and handed to every factory as a plain mapping. The
    alternative would be a read per request, and it is refused for three reasons.
    ``config.public_url`` is synchronous and pure, ... A process wide cache with an expiry
    would be mutable module state, which D-20 forbids with exactly two named exceptions.
    And a read per request would be a second Nextcloud round trip on every request ...

    The price is one step for the administrator: a changed value takes effect after the app is
    disabled and enabled again. That price is named in the description of the form field
    (plan 05-01), in the setup state of the connections page and in ``docs/oauth-setup.md``,
    and it is not hidden anywhere.
    """
```

**Der Ort der neuen Zeile** ist `main()`, direkt nach Zeile 299, und der Kommentarblock
darüber (Zeile 295-298) sagt schon, warum dort:

```python
    # Everything below reads this mapping and never os.environ again: the values an
    # administrator set in Nextcloud are part of the environment of this process from here on
    # (plan 05-04). The read happens after the refusal above, so a misconfigured process never
    # opens a socket, and before every check, so the checks judge the values that will be used.
    resolved, refused = _resolved_env()
```

Die neue Zeile widerspricht diesem Kommentar teilweise ("never os.environ again") und muss
das benennen: sie schreibt genau einen Schlüssel zurück nach `os.environ`, weil ein Werkzeug
kein `resolved`-Mapping in der Hand hat. **Die Kommentarzeile ist Pflicht, nicht Kür** (A7),
und `tests/unit/test_exapp_entry.py` hält sie fest.

**Was das Gate dazu sagt:** `tests/contract/test_no_destructive_calls.py` Zeile 145-148 führt
die zwei erlaubten Modulzustände wörtlich. `os.environ` ist keiner davon und muss auch keiner
werden, weil es die Prozessumgebung und kein Modul-Dictionary ist. Genau diese Abgrenzung
gehört in die Kommentarzeile.

```python
ALLOWED_MODULE_STATE: set[tuple[str, str]] = {
    ("nextcloud/http.py", "_clients"),  # one httpx client per event loop, weakly keyed
    ("nextcloud/capabilities.py", "_cache"),  # capabilities per (base_url, user), 60 s TTL
}
```

---

### `exapp/config_values.py` (config, geändert: sechster Schlüssel)

**Analog:** dieselbe Datei, der Eintrag `oauth_allowlist_only` (ein Schalter, der in allen
vier Listen auftaucht). Vier Stellen, alle in Zeile 96-135:

```python
CONFIG_KEYS: tuple[str, ...] = (
    PUBLIC_URL_KEY,
    "oauth_dcr",
    "oauth_cimd",
    "oauth_allowlist_only",
    "oauth_allowed_clients",
)

KEY_TO_ENV: Mapping[str, str] = {
    PUBLIC_URL_KEY: config.ENV_PUBLIC_URL,
    "oauth_dcr": registry.ENV_DCR,
    ...
}

SWITCH_KEYS: frozenset[str] = frozenset({"oauth_dcr", "oauth_cimd", "oauth_allowlist_only"})
```

`"talk_send"` kommt **hinten** in `CONFIG_KEYS` (T15: die drei OAuth-Schalter bleiben
beieinander, weil `registry.client_policy` zwei davon als eine Antwort liest, und der
`#:`-Kommentar an Zeile 101-105 sagt das schon), plus `KEY_TO_ENV[..] = config.ENV_TALK_SEND`,
plus in `SWITCH_KEYS`.

**Kein neuer Validierungscode nötig:** `_usable_value` Zeile 303-312 verzweigt schon auf
`SWITCH_KEYS`, und `_switch` Zeile 388-405 ist die fertige Prüfung.

```python
def _usable_value(key: str, raw: str) -> str | None:
    """The validated form of one admin value, or ``None`` when it is not usable."""
    if key == PUBLIC_URL_KEY:
        return _public_url(raw)
    if key in SWITCH_KEYS:
        return _switch(key, raw)
    return raw.strip()
```

**Log-Muster** (`_rejected`, Zeile 408-415): den Feldnamen nennen, nie den Wert.

```python
def _rejected(key: str, why: str) -> None:
    """Name the field and the reason, never the value: it came in over HTTP (T-05-03)."""
```

Nachzuziehen, weil die Zahl fünf im Text steht: Modul-Docstring Zeile 1 und 19, der
`#:`-Kommentar an Zeile 101, der Docstring von `_public_url` Zeile 318 ("the most dangerous of
the five values"), `_config_values` Zeile 434 ("Pull our five values out of the OCS envelope").

---

### `exapp/admin_settings.py` (config, geändert: sechstes Feld)

**Analog:** dieselbe Datei, das Feld `allowlist_field` (Zeile 139-145) ist die kürzeste
Checkbox der Form und damit die direkte Vorlage, bis auf den Default.

```python
            {
                "id": allowlist_field,
                "title": strings.ADMIN_FIELD_ALLOWLIST_LABEL,
                "description": strings.ADMIN_FIELD_ALLOWLIST_DESCRIPTION,
                "type": "checkbox",
                "default": False,
            },
```

Für `talk_send`: `"default": True` (TALK-04), und die Begründung im Kommentar folgt dem
Muster des `dcr_field` (Zeile 123-125):

```python
                "type": "checkbox",
                # The state this app ships with (D-35): success criteria 1 and 2 are about
                # connecting a hosted assistant without an administrator in the loop.
                "default": True,
```

**Die Entpackzeile** (Zeile 100) bricht absichtlich und ist der erwartete Compile-Fehler:

```python
    public_url_field, dcr_field, cimd_field, allowlist_field, allowed_field = CONFIG_KEYS
```

Wird zu sechs Namen, `talk_send_field` hinten. **Kein `sensitive`** in irgendeiner
Schreibweise: der Modul-Docstring Zeile 18-21 erklärt warum, und
`test_the_body_never_carries_the_word_sensitive` hält es fest.

Nachzuziehen: Modul-Docstring Zeile 1 ("five values"), Zeile 21 ("None of the five fields"),
`form_scheme`-Docstring Zeile 85 ("The five fields are built from"), der `#:`-Kommentar an
Zeile 63-64 ("the same subject as these five values"). Ausserdem empfiehlt T15 einen Satz in
`ADMIN_SETTINGS_DESCRIPTION`, damit die Seite nicht nur von OAuth spricht.

---

### `exapp/ui/strings.py` (config, geändert: zwei neue Konstanten)

**Analog:** `ADMIN_FIELD_ALLOWLIST_LABEL` und `ADMIN_FIELD_ALLOWLIST_DESCRIPTION`
(Zeile 605-611) für die Kürze, und `ADMIN_FIELD_CIMD_DESCRIPTION` (Zeile 589-603) für den
Fall, dass eine Beschreibung eine Kopplung oder eine Nebenbedingung erklären muss.

```python
ADMIN_FIELD_ALLOWLIST_LABEL = "Allow only the apps listed below"

ADMIN_FIELD_ALLOWLIST_DESCRIPTION = (
    "With this on, an app may connect only if it is in the list below. An empty list "
    "therefore allows nothing, which is deliberate: a list nobody filled in is not a "
    "permission to connect."
)
```

```python
#: The form half of ``NC_MCP_OAUTH_CIMD``, and the one field whose state is not its own: the
#: code derives the answer as "this switch AND the switch above" (``oauth/registry.py``), so
#: the description has to name that coupling in both directions.
ADMIN_FIELD_CIMD_DESCRIPTION = (...)
```

Der Aktivierungszyklus-Satz existiert wörtlich dreimal und wird für das neue Feld
wiederverwendet, zuletzt in `ADMIN_FIELD_PUBLIC_URL_DESCRIPTION` Zeile 575:

```python
    "trailing slash. A change takes effect after you disable and enable this app again."
```

`ADMIN_SETTINGS_PLACE` (Zeile 562) ist der Ort, den der Fehlersatz von `talk_send` nennt, und
er ist schon einmal buchstabiert:

```python
#: Where the administration form of this app sits, named once so a move is one edit.
ADMIN_SETTINGS_PLACE = "Administration settings, Security, MCP Connector"
```

**`__all__`-Regel** (Zeile 39-50): beide neuen Namen müssen sortiert in `__all__`, sonst
schlägt das vulture-Gate zu. Ausserdem prüft
`test_no_new_sentence_carries_an_em_dash_or_an_emoji` (Zeile 516) jeden neuen Text.

---

### `tests/unit/test_talk_client.py` (test, respx)

**Analog:** `tests/unit/test_tables_client.py` (die ganze Datei, 332 Zeilen)

**Docstring-Muster** (Zeile 1-23): der Docstring nennt die zwei Eigenschaften, die Vertrag
und nicht Implementierungsdetail sind, und **warum sie gegen die URL geprüft werden statt
gegen eine geparste Antwort**. Für Talk sind das die vier Leseparameter (T6) und die
Header-Paginierung (T8).

```python
"""Unit tests for the Tables client, all paths, asserted on the request that was built.

Two properties of this client are contract and not implementation detail, and neither of
them is visible in a parsed answer, which is why they are tested against the URL:

*   a rows URL always carries ``limit``. ...
*   the parser follows the generation. ...

The digits of the created-status appear nowhere in this file on purpose: the gate for this
plan greps for them, because a test that expects them is red against a correctly working
instance (pitfall 4).
"""
```

**Eingefrorene URL-Literale** (Zeile 41-48): das direkte Vorbild für die zwei API-Versionen
von Talk.

```python
# The frozen endpoint literals. They are the guard against swapping nodeType and
# nodeCollection: a route that changes spelling here has to be changed on purpose.
V2_BASE = f"{BASE}/ocs/v2.php/apps/tables/api/2"
TABLES_URL = f"{V2_BASE}/tables"
COLUMNS_URL = f"{V2_BASE}/columns/table/7"
CREATE_ROW_URL = f"{V2_BASE}/tables/7/rows"
ROWS_URL = f"{BASE}/index.php/apps/tables/api/1/tables/7/rows/simple"
```

Für Talk: `ROOM_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v4/room"` und
`CHAT_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v1/chat/abcd1234"`.

**Envelope-Helfer und Fixtures** (Zeile 50-86):

```python
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {"ocs": {"meta": {"status": "ok", "statuscode": statuscode, "message": message},
                    "data": data}}


@pytest.fixture
def creds() -> Credentials:
    return Credentials(BASE, USER, SECRET)


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False)
```

`envelope(..., statuscode=201)` ist damit der Test für T1, ohne dass eine neue Hilfsfunktion
nötig wäre.

**URL-Behauptungs-Muster** (Zeile 106-149): drei Tests, die alle nur die Query-Parameter
prüfen. Das ist der Bauplan für die vier Leseparameter und für `lookIntoFuture` (T7).

```python
@pytest.mark.anyio
async def test_the_rows_url_always_carries_a_limit(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """The property a parsed answer never shows: without a limit this reads everything."""
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(ROWS_URL).mock(
            return_value=httpx.Response(200, json=fixture("tables_rows_simple.json"))
        )
        rows = await tables_client.get_rows_simple(client, creds, 7, limit=25)

    assert "limit=25" in str(route.calls.last.request.url)
    assert route.calls.last.request.url.params["offset"] == "0"
```

```python
async def test_a_limit_above_the_maximum_is_capped_in_the_url(...) -> None:
    ...
    assert "limit=200" in str(route.calls.last.request.url)
    assert tables_client.MAX_ROWS == 200
```

**Kein-Request-Muster** (Zeile 270-282): das Vorbild für "der Token-Wächter lehnt ab, bevor
etwas rausgeht" (T9) **und** für "mit abgeschaltetem Schalter passiert kein HTTP-Aufruf"
(TALK-04, Schicht 3, Falle 10). `assert_all_called=False` plus `len(route.calls) == 0` ist die
gesamte Technik.

```python
@pytest.mark.anyio
async def test_a_table_id_that_is_not_numeric_never_reaches_nextcloud(
    client: httpx.AsyncClient, creds: Credentials
) -> None:
    """Ids go into the path; anything but digits is a bug or an attempt (threat T-08-06)."""
    with respx.mock(assert_all_called=False) as mock:
        route = mock.route(url__startswith=BASE)
        with pytest.raises(ToolError) as excinfo:
            await tables_client.get_rows_simple(client, creds, "7/../../tables", limit=25)

    assert len(route.calls) == 0
    assert excinfo.value.hint
```

**Origin-Verbots-Muster** (Zeile 187-201): eins zu eins für `send_message`.

```python
async def test_the_create_request_sends_json_and_never_an_origin_header(...) -> None:
    """With an Origin present Nextcloud demands a basic reauthentication (threat T-08-09)."""
    ...
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["OCS-APIRequest"] == "true"
    assert "origin" not in {key.lower() for key in request.headers}
```

**Quellcode-Behauptungs-Muster** (Zeile 319-332): zwei Tests, die die Datei als Text lesen
statt sie aufzurufen. Das erste ist die Vorlage für "kein Edit-, Delete-, Schedule-,
Summarize- oder Silent-Pfad", das zweite für "die Signatur erzwingt die Grenze".

```python
def test_the_module_has_no_update_remove_or_share_path() -> None:
    """The server promise of this family, kept by not writing the code (threat T-08-11)."""
    source = Path(tables_client.__file__).read_text(encoding="utf-8")
    for forbidden in (".put(", ".patch(", "/share", "/transfer", "/scheme"):
        assert forbidden not in source, f"{forbidden} has no place in a read plus create client"


def test_the_rows_reader_takes_its_limit_as_a_keyword_without_a_default() -> None:
    """Constructive rather than documented: an omitted limit does not compile away."""
    import inspect

    parameter = inspect.signature(tables_client.get_rows_simple).parameters["limit"]
    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
```

Für Talk wird die Verbotsliste `(".put(", ".patch(", "/schedule", "/summarize", "/reminder",
"/pin", "/attachment", "silent")` und deckt damit T14 auf Client-Ebene ab, zusätzlich zum
Gate.

**Umlaut-Regel im Testinhalt** (Zeile 84, 179, 196, 251): die Testdaten tragen absichtlich
`ü`, `ä`, `ß` (`"Baulos 4 übergeben"`, `"Maße geprüft"`, `"Fällig am"`). Talk-Fixtures und
gesendete Nachrichten machen es genauso.

---

### `tests/unit/test_talk_tools.py` (test, unit)

**Analog:** `tests/unit/test_tables_tools.py` (797 Zeilen, 30 Tests)

**Namensmuster:** jeder Testname ist ein vollständiger Satz über das Verhalten, nicht über
die Funktion. Die Zuordnung Talk zu Tables ist fast eins zu eins:

| Talk-Testfall (aus RESEARCH) | Vorbild in `test_tables_tools.py` |
|------------------------------|-----------------------------------|
| App fehlt, kein Request | `test_a_missing_tables_app_stops_both_tools_before_the_first_request` (Zeile 154) |
| App vorhanden, aber leere Sektion | `test_an_installed_but_disabled_app_behaves_like_a_missing_one` (Zeile 178) |
| Unbekanntes Level | `test_an_unknown_level_is_refused_and_names_all_three` (Zeile 198) |
| Nachrichtenebene ohne Token | `test_a_level_below_the_table_needs_a_table_id` (Zeile 215, parametrisiert) |
| Projektion der Konversation | `test_browse_tables_projects_the_fields_a_model_reads` (Zeile 230) |
| `isArchived` gefiltert | `test_a_table_that_was_put_aside_does_not_appear` (Zeile 257) |
| Default 20 statt alles | `test_rows_without_a_limit_read_twenty_five_and_not_the_table` (Zeile 299) |
| Limit über 50 gekappt | `test_a_limit_outside_the_range_is_capped_instead_of_refused` (Zeile 317) |
| `next`-Handle bei mehr Verlauf | `test_more_rows_than_the_window_are_named_with_a_next_handle` (Zeile 348) |
| Cursor einer anderen Konversation | `test_a_cursor_of_another_table_is_refused_instead_of_applied` (Zeile 365) |
| 304 wird `no_data` | `test_a_table_with_no_rows_is_an_empty_answer_and_not_an_error` (Zeile 384) |
| Marker im fremden Text weg | `test_a_marker_is_removed_from_a_cell_that_is_not_a_plain_string` (Zeile 405) |
| Leeres Fenster, aber Header (T8) | `test_a_page_that_carried_nothing_hands_out_no_handle_of_its_own_offset` (Zeile 466) |
| `permissions` statt `attendeePermissions` (T3) | `test_the_owner_may_write_although_the_share_object_reports_read_alone` (Zeile 705) |
| Kein Chat-Recht, keine Anfrage | `test_a_shared_table_without_create_is_refused_before_the_post` (Zeile 737) |
| Gesendet, aber keine Id zurück | `test_a_created_row_without_an_id_is_reported_instead_of_faked` (Zeile 756) |
| 400 der App durchgereicht | `test_a_four_hundred_of_the_app_is_passed_through_with_its_own_message` (Zeile 777) |

**Ohne Vorbild und neu zu schreiben:** Sortierung nach `lastActivity` bei absichtlich
unsortierter Fixture (T5, Falle 5), `@allan` ist **erlaubt** (T11), Platzhalter-Auflösung
inklusive unbekanntem Platzhalter (Muster 5), Byte-Kappe je Nachricht (Muster 7),
Systemnachrichten-Positivliste (Muster 6), Schalter aus (Muster: das
`len(route.calls) == 0`-Muster aus `test_tables_client.py` Zeile 270-282).

**Regressionsfall zu T3** in Fixture-Form: eine Konversation mit `permissions = 128` **und**
`attendeePermissions = 0`. Wer das falsche Feld liest, hat einen roten Test mit sichtbarer
Ursache. Das entspricht dem Aufbau von `test_the_owner_may_write_although_the_share_object_reports_read_alone`.

---

### `tests/integration/test_talk_roundtrip.py` (test, integration)

**Analog:** `tests/integration/test_tables_roundtrip.py` (336 Zeilen)

**Marker und Fixture-Muster** (Zeile 43, 82-99):

```python
pytestmark = [pytest.mark.integration, pytest.mark.anyio]


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
        creds=Credentials(...),
    )
```

**Messwert-Muster** (Zeile 72-79): der Weg, wie eine Messung in einem **grünen** Lauf sichtbar
wird. Genau das brauchen die Nebenwirkungs-Messwerte von Erfolgskriterium 3.

```python
def measured(what: str) -> None:
    """Make a measurement visible in the test report of a passing run.

    A print stays hidden while the test is green, and a green run is exactly when these
    numbers are wanted: the answer to assumption A2 belongs in the plan summary whether the
    instance accepted the value or refused it.
    """
    warnings.warn(f"measured: {what}", stacklevel=2)
```

**Gerüst-Muster mit Skip statt Failure** (Zeile 102-120): das Vorbild für das Anlegen einer
Testkonversation. Beachten: für Talk empfiehlt RESEARCH `occ talk:room:create` statt eines
API-Aufrufs, also wird `_post` durch einen `occ`-Aufruf ersetzt; die **Fehlerbehandlung**
bleibt aber genau diese (ein Konto, das kein Gerüst bauen darf, ist ein Skip und kein Fehler).

```python
async def _post(clients: NcClients, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Test scaffolding only: the connector itself never creates tables or columns.

    A status of 400 or above is a skip and not a failure: an account that may not prepare a
    table says nothing about the connector, and turning that into a red test would blame
    the wrong side. ``httpx.BasicAuth`` is written out here on purpose, so the setup is
    visibly not going through the credential seam the measurements use.
    """
```

**Idempotenz nach Namen** (Zeile 123-143, T-08-30): das Gerüst sucht zuerst, legt nur an, wenn
es fehlt. Für Talk zwingend, weil `occ talk:room:create` beim zweiten Aufruf einen zweiten
Raum anlegt (RESEARCH, Environment-Tabelle).

```python
async def _table_with_columns(clients: NcClients) -> str:
    """Return the test table, creating it and its four columns once if they are missing.
    ...
    """
    tables = await tables_client.get_tables(clients.client, clients.creds)
    table = next(...)
```

**Einmalige Nutzlast je Lauf** (Zeile 67-69): für `talk_send` genauso, damit ein zweiter Lauf
die eigene Nachricht wiederfindet und nicht die des vorigen.

```python
def unique_task() -> str:
    """One task text that no other run wrote, with umlauts a broken encoding would eat."""
    return f"Grüße aus Hamburg, Straße 1 ({time.strftime('%Y%m%d-%H%M%S')} {uuid.uuid4().hex[:8]})"
```

**Testabdeckung nach dem Analog** (Zeile 232-336): `test_capabilities_report_the_installed_tables_app`
wird `..._spreed_app`, `test_a_new_row_is_readable_back_under_its_column_titles` wird
"gesendete Nachricht ist im Verlauf wiederfindbar", `test_the_live_row_url_carries_a_limit`
wird die Live-Gegenprobe der vier Leseparameter, `test_browsing_an_unknown_table_reports_it_instead_of_guessing`
wird "ein Token, das nicht in der Liste steht, wird abgelehnt, ohne Nextcloud zu erreichen"
(T10).

**Der Test ohne Analog** ist die Nebenwirkungs-Messung. Er steht als Skizze in
`09-RESEARCH.md` und braucht nur das `measured()`-Muster von oben, damit die vier
Feldwerte im grünen Lauf sichtbar sind.

---

### `tests/fixtures/talk_rooms.json` und `talk_messages.json` (fixture)

**Analog:** `tests/fixtures/deck_boards.json` (echte Antwortform mit allen Beifeldern) und
`tests/fixtures/tables_tables.json`. Das Muster ist: **die Fixture ist so gross und so
unaufgeräumt wie die echte Antwort**, damit die Projektion etwas zu tun hat.

```json
[
  {
    "id": 2,
    "title": "Projekt MCP",
    "owner": { "primaryKey": "alice", "uid": "alice", "displayname": "Alice Beispiel", "type": 0 },
    "color": "0082c9",
    "archived": false,
    "labels": [ { "id": 7, "title": "Dringend", ... } ],
    "acl": [],
    "permissions": { "PERMISSION_READ": true, ... },
```

Vorgaben für `talk_rooms.json` aus RESEARCH, die über das Analog hinausgehen: die
Server-Reihenfolge widerspricht absichtlich der `lastActivity`-Reihenfolge (Falle 5), und die
Liste enthält je einen Eintrag mit `isArchived: true`, `readOnly: 1`, `type: 4` und
`permissions: 0` bei `attendeePermissions: 0` (T3-Regression).

---

### `tests/contract/test_tool_surface.py` (test, contract, geändert)

**Analog:** dieselbe Datei, der Tables-Block. Fünf eingefrorene Stellen plus drei
Textstellen (Falle 9).

**Mengen** (Zeile 35-63): `talk_browse` und `talk_send` in `EXPECTED_TOOLS`, `talk_send` in
`CREATE_TOOLS`. Der Kommentar an Zeile 56 nennt die Zahl ("The five write paths").

```python
EXPECTED_TOOLS = {
    ...
    "tables_browse",
    "tables_create_row",
    "search",
    "fetch",
}

# The five write paths. Everything else in EXPECTED_TOOLS only reads (D-16).
CREATE_TOOLS = {
    "files_upload", "calendar_create_event", "notes_create", "deck_create_card",
    "tables_create_row",
}
```

**Familien-Test-Muster** (Zeile 248-284): der direkte Bauplan für den Talk-Block, inklusive
der Enum-Behauptung und der vier Annotations-Behauptungen.

```python
@pytest.mark.anyio
async def test_the_two_tables_tools_are_listed_and_browse_takes_an_enum_level() -> None:
    """D-06 for the Tables family: one browse tool, one create-only write, no more.
    ...
    """
    async with Client(mcp, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    for name in ("tables_browse", "tables_create_row"):
        assert name in tools, f"{name} is part of the curated set (TABLES-01, TABLES-02)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    browse = tools["tables_browse"]
    annotations = browse.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "tables_browse only reads"
    assert annotations.open_world_hint is False

    schema = browse.input_schema
    assert schema["properties"]["level"]["enum"] == ["tables", "columns", "rows"], (
        "the level is an enum in the schema, not a free string the model has to guess"
    )
    assert "$defs" not in schema, "no nested models in the input schema (schema diet)"

    create = tools["tables_create_row"].annotations
    assert create is not None
    assert create.read_only_hint is False, "tables_create_row writes"
    assert create.destructive_hint is False, "it can only create, never replace or delete"
    assert create.idempotent_hint is False, "a second call creates a second row"
    assert create.open_world_hint is False
```

**Verbotslisten-Muster** (Zeile 287-299): eins zu eins für Talk, mit
`talk_list_conversations`, `talk_list_messages`, `talk_read_message`, `talk_send_message`.

```python
@pytest.mark.anyio
async def test_there_is_no_tool_per_tables_level() -> None:
    """The same anti-pattern one family later: three navigation tools buy nothing."""
    async with Client(mcp, raise_exceptions=True) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    forbidden = {
        "tables_list_tables", "tables_list_columns", "tables_list_rows", "tables_read_row",
    }
    assert not (names & forbidden), f"tables_browse covers these levels: {names & forbidden}"
```

**Die Zahl 18** an vier Stellen: Docstring Zeile 370, Assertion Zeile 375, Meldung Zeile 520,
Kommentar Zeile 560. Alle auf 20.

```python
async def test_the_curated_set_is_complete_and_only_the_chatgpt_profile_has_a_schema() -> None:
    """The whole surface in one assertion: 18 tools, and the diet holds for 16 of them."""
    ...
    assert set(tools) == EXPECTED_TOOLS
    assert len(tools) == 18, "the curated set is 18 tools, no more and no fewer"
```

---

### `tests/contract/test_no_destructive_calls.py` (test, contract, geändert)

**Analog:** dieselbe Datei, das dreiteilige Tables-Muster. **Jede Nadel braucht eine
Gegenprobe, und jede erlaubte Route braucht eine positive Behauptung.** Das ist die
tragfähige Absicherung für T14, weil PUT in diesem Projekt kein verbotenes Verb ist.

**Teil 1, die Nadeln** (Zeile 50-63): auf einem **Pfadsegment** verankert, nicht auf dem
öffnenden Anführungszeichen. Der Kommentar an Zeile 40-49 erklärt, warum, und dass die
frühere Fassung an der eigenen f-String-Schreibweise vorbeigelaufen ist.

```python
FORBIDDEN: dict[str, str] = {
    "DELETE": "no tool may delete anything",
    ...
    "/rows/": "no tool may address a single Tables row: reading, changing and deleting "
    "one all live on that route",
    "/columns/": "no tool may create, change or delete a Tables column",
    "/scheme": "no tool may import or export a table scheme",
    "/transfer": "no tool may hand a table to another owner",
    "/share": "no tool may create or change a Tables share",
}
```

Für Talk (T14): `/schedule`, `/summarize`, `/reminder`, `/pin`, `/attachment`, `/read`,
`/favorite`, `/notify`, `/participants`, `/archive`. **Kollisionsprüfung für `/read`:** heute
existiert kein Pfadliteral mit diesem Segment; `files_read` und `read_offset` sind Identifier
ohne Schrägstrich und werden von der Segment-Verankerung nicht getroffen.

**Teil 2, die Gegenprobe je Nadel** (Zeile 65-76 plus 316-337): jede Nadel bekommt eine Zeile,
die sie treffen **muss**, geschrieben in der f-String-Form, die dieses Projekt benutzt.

```python
#: The five needles above that name a Tables route, with a line that would carry them into
#: the code. ... Every line is written the way this project writes a path, an f-string with
#: the prefix constant in it, because that is the spelling the previous needles missed.
TABLES_ROUTES: dict[str, str] = {
    "/rows/": '    response = await client.get(api_url(creds, f"/tables/{table}/rows/{row_id}"))',
    "/columns/": '    await ocs.ocs_post(client, creds, f"{V2_PREFIX}/columns/{cid}", body)',
    ...
}
```

```python
@pytest.mark.parametrize(("needle", "line"), sorted(TABLES_ROUTES.items()))
def test_each_tables_needle_trips_on_its_route_and_leaves_the_real_module_alone(
    needle: str, line: str
) -> None:
    """Counter proof per Tables needle: it hits the route, and it misses today's code.

    A needle that never matches anything is the same as no needle at all, and a needle that
    matches the module as it stands would be repaired by rewriting the module rather than by
    narrowing the needle. Both failures are silent, so both are asserted here ...
    """
    relative = "nextcloud/clients/tables.py"
    real = _code_lines(SRC / relative)
    assert _violations(relative, real) == [], (
        f"{relative} must be clean before a needle can prove anything"
    )

    findings = _violations(relative, [*real, (len(real) + 1, line)])
    assert any(repr(needle) in finding for finding in findings), (
        f"the gate must report {needle!r} for: {line.strip()}"
    )
```

**Teil 3, die positive Behauptung** (Zeile 78-84 plus 340-350): `ALLOWED_TALK_ROUTES` mit
**genau drei** Pfadformen, im Wortlaut, den `clients/talk.py` schreibt. Das ist der Ersatz für
die fehlende Verb-Nadel bei PUT.

```python
#: The three forms :mod:`mcp_connector.nextcloud.clients.tables` really builds. They are the
#: reason the needles are shaped the way they are, so they are asserted, not assumed.
ALLOWED_TABLES_ROUTES = (
    '    api_url(creds, f"/tables/{table}/rows/simple"),',
    '    ocs.ocs_url(creds, f"{V2_PREFIX}/columns/{NODE_TYPE_TABLE}/{table}"),',
    '    ocs.ocs_url(creds, f"{V2_PREFIX}/{NODE_COLLECTION_TABLES}/{table}/rows"),',
)


def test_the_three_routes_the_tables_client_really_builds_stay_allowed() -> None:
    """The other half of the same proof: the create path and the two reads must pass. ..."""
    for line in ALLOWED_TABLES_ROUTES:
        assert _violations("nextcloud/clients/tables.py", [(1, line)]) == [], (
            f"the gate must not report the allowed route: {line.strip()}"
        )
```

**Ausnahme-Muster, falls eine Talk-Nadel eine erlaubte Route trifft** (Zeile 86-100 plus
353-373): eine Ausnahme ist **niemals** "ignoriere Talk-Routen in dieser Datei", sondern eine
Liste exakter Literale in genau einer Datei, mit einer Gegenprobe, die zeigt, dass eine
Variante daneben weiterhin gemeldet wird.

```python
FILES_WITH_THE_TABLES_READS = frozenset({"nextcloud/clients/tables.py"})
TABLES_READ_FORMS = (
    'f"/tables/{table}/rows/simple"',
    'f"{V2_PREFIX}/columns/{NODE_TYPE_TABLE}/{table}"',
)

#: The needles the read exemption may apply to. ``DELETE`` and the other verbs are never
#: exempt by it, and neither are ``/transfer`` and ``/share`` ...
TABLES_READ_NEEDLES = ("/rows/", "/columns/")
```

```python
def test_the_tables_read_exemption_covers_two_call_forms_and_nothing_else() -> None:
    """..."""
    tables = "nextcloud/clients/tables.py"
    assert _is_a_tables_read(tables, '        api_url(creds, f"/tables/{table}/rows/simple"),')
    assert not _is_a_tables_read(tables, '        api_url(creds, f"/tables/{table}/rows/{row}"),')
    assert not _is_a_tables_read(
        "tools/tables.py", '        api_url(creds, f"/tables/{table}/rows/simple"),'
    )
```

---

### `tests/unit/test_config.py`, `test_ocs_capabilities.py`, `test_exapp_*.py` (test, geändert)

**`test_config.py`, Analog** Zeile 133-145: das Muster für den neuen `talk_send_enabled`-Test,
inklusive der parametrisierten Blank-Variante.

```python
def test_exapp_configured_needs_both_id_and_secret() -> None:
    ...


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_appapi_variable_is_treated_as_unset(blank: str) -> None:
    ...
```

Für `talk_send_enabled`: alle Schreibweisen aus `_TRUE_VALUES` und `_FALSE_VALUES`
parametrisiert, Default `True` bei fehlender Variable, und ein unverständlicher Wert bleibt
**an** (siehe die Warnung im `config.py`-Abschnitt oben).

**`test_ocs_capabilities.py`, Analog:** die bestehenden `tables`-Fälle. Für `spreed` kommen
zwei Fälle dazu, die Tables nicht braucht: Sektion fehlt und Sektion ist ein **leeres Array**
(RESEARCH, Capabilities-Abschnitt).

**`test_exapp_admin_settings.py`, Analog** Zeile 114-145: die Behauptung, dass Formfelder und
`CONFIG_KEYS` in Reihenfolge übereinstimmen. Nur die Zahl und der Testname ziehen nach.

```python
async def test_the_five_fields_are_the_five_config_keys_in_order() -> None:
    ...
    assert tuple(field["id"] for field in fields) == config_values.CONFIG_KEYS
```

Diese vier bestehenden Tests decken das neue Feld automatisch mit ab und müssen grün bleiben:
`test_no_field_carries_a_type_outside_the_verified_list` (Zeile 146),
`test_the_body_never_carries_the_word_sensitive` (Zeile 161),
`test_every_field_carries_a_title_a_description_and_a_default` (Zeile 176),
`test_no_new_sentence_carries_an_em_dash_or_an_emoji` (Zeile 516).

**`test_exapp_config_values.py`, Analoga:** `test_the_five_keys_are_the_field_ids_of_the_admin_form`
(Zeile 76), `test_one_request_asks_for_all_five_keys` (Zeile 123),
`test_all_five_values_travel_together` (Zeile 690),
`test_every_understood_switch_spelling_becomes_on_or_off` (Zeile 636),
`test_an_unknown_switch_value_is_dropped_and_logged` (Zeile 652),
`test_the_switch_spellings_are_the_ones_the_registry_understands` (Zeile 105). Der letzte ist
zusätzlich das Vorbild für den neuen Gleichsetzungstest zwischen `config` und `config_values`
(T15).

**`test_exapp_entry.py`, Analog:** die bestehenden Overlay-Wege. Neu ist die Behauptung, dass
der aufgelöste Wert nach `os.environ` gelangt und dort in der Schreibweise steht, die
`talk_send_enabled` versteht (`"on"`/`"off"` aus `config_values.SWITCH_ON`/`SWITCH_OFF`).

**`test_permission_fidelity_exapp.py`, Analog** Zeile 308-470: der Tables-Zwei-Konten-Block
ist der Bauplan. `_appapi_clients`, zwei Fixtures (`alice_tables`, `bob_tables`), `_scaffold`,
und die drei Behauptungen: der Eigentümer findet, das zweite Konto findet nicht, das zweite
Konto kann nicht schreiben und **lässt nichts zurück**.

```python
async def test_bob_neither_lists_alices_table_nor_reads_it_by_its_real_id(...)
async def test_bob_cannot_write_into_alices_table_and_leaves_no_row_behind(...)
```

---

### Skripte (config und test, geändert)

**`scripts/bootstrap_exapp.sh`, Analog** Zeile 886-892: die Funktion `ensure_app` (Zeile 255)
existiert und ist idempotent; es kommt eine Zeile dazu.

```sh
ensure_app notes
ensure_app deck
...
ensure_app tables
ensure_app mail
```

Der Kommentar an Zeile 899 warnt, dass Alice zu diesem Zeitpunkt noch nicht existiert. Die
Testkonversationen müssen also **hinter** der Nutzeranlage stehen, nicht bei den
`ensure_app`-Zeilen. Idempotenz nach Namen ist Pflicht, weil `occ talk:room:create` beim
zweiten Aufruf einen zweiten Raum anlegt.

**`scripts/acceptance_all_tools.py`, Analog** Zeile 45-52: der Kommentar über `EXPECTED_TOOLS`
sagt selbst, dass die Zahl im gleichen Commit steigt wie jede andere eingefrorene Zahl.

```python
# The count the registry answers today. It stood at 15 while the registry already listed
# 16, which is the kind of drift only a number in two places produces, so it is raised in
# the same commit that raises every other frozen number of a phase.
EXPECTED_TOOLS = 18
```

Plus Modul-Docstring Zeile 1 ("call all 18 tools once") und Zeile 16 ("Exit code 0 only when
all 18 tools answered"). `docs/conference-demo.md` zitiert die Fehlermeldung dieses Skripts
wörtlich.

**`scripts/check_tool_budget.py`, Analog** Zeile 15-33: das Muster ist eine **datierte
Messzeile pro Anhebung**, und die alte bleibt stehen.

```python
# Armed value, not a decorative one. A budget far above the measurement never fails and
# therefore never protects anything, which was the state until the end of phase 1.
#
#   Measurement 2026-08-14, all 15 curated tools registered: 10643 bytes
#   Budget      10643 + 15 percent = 12239, rounded up to the next 500 = 12500 bytes
#
#   Measurement 2026-08-21, all 18 curated tools registered: 12801 bytes
#   Budget      12801 + 15 percent = 14721, rounded up to the next 500 = 15000 bytes
#
# The older line stays where it is: a regression is only attributable when the number it
# regressed from is still readable. ...
BUDGET_BYTES = 15_000
...
MAX_TOOL_BYTES = 1400
```

Anheben nur zusammen mit einer neuen Messzeile, und die Messung gehört in denselben Commit wie
die Werkzeuge (Falle 8). Der Pro-Tool-Deckel von 1400 ist die eigentliche Grenze für den
Docstring von `talk_send`.

---

## Querschneidende Muster

### Fehlermodell: ein Satz plus ein nächster Schritt

**Quelle:** `src/mcp_connector/errors.py` über `ToolError(message=..., hint=...)`, und
`src/mcp_connector/server/__init__.py` Zeile 68-99 (`graceful`).
**Gilt für:** `clients/talk.py`, `tools/talk.py`, jede Absage von `talk_send`.

```python
def graceful[T](fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Translate internal failures into an ordinary tool error the model can act on.

    ``from None`` is not cosmetic: an httpx traceback can contain the request URL, and a
    URL is one careless change away from carrying credentials (threat T-01-07). ...
    """
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
```

`ocs._status_error` (Zeile 259-303) ist die eine Stelle, die einen Nextcloud-Status in einen
Satz verwandelt. Der Talk-Client baut **keine** eigene Statuszuordnung (Don't Hand-Roll):
`_status_error` bekommt nur 201 im Erfolgsraum dazu (T1).

### Fremdtext-Behandlung

**Quelle:** `src/mcp_connector/tools/marks.py` Zeile 37-56, benutzt über `tools/tables.py`
Zeile 423-450 (`_text`, `_clean`).
**Gilt für:** jeden Nachrichtentext, jeden `actorDisplayName`, jeden Namen aus
`messageParameters`, jeden Konversations-`displayName`.

Regel aus `marks.py`: die Kappungsmarkierung steht **ausserhalb** des Textes
(`truncated: true` als Feld), nie im Text, weil ein Marker im fremden Text ein Angriffsweg
ist (ME-03). Talk-Nachrichten sind der billigste Ort für diesen Angriff, weil jeder
Konversationsteilnehmer schreiben darf.

### App-Erkennung als erste Zeile

**Quelle:** `nextcloud/capabilities.py` Zeile 114-129 (`require_app`, `app_missing`),
benutzt in `tools/tables.py` Zeile 90 und 130.
**Gilt für:** `tools.talk.browse` (erste Zeile) und `tools.talk.send` (zweite Zeile, nach dem
Schalter).

```python
async def require_app(clients: NcClients, app: str) -> Capabilities:
    """Return the capabilities, or raise :class:`AppMissingError` if ``app`` is absent.

    Called first by every tool of an optional app, which is what keeps a missing app from
    producing a request that could only fail with an HTML page or a 404.
    """
```

Die Reihenfolge in `talk_send` ist umgekehrt zu allen bestehenden Werkzeugen: **erst
`config.talk_send_enabled()`, dann `require_app`** (Falle 10). Das ist die eine Stelle, an der
dieses querschneidende Muster nicht wörtlich gilt, und sie braucht eine Kommentarzeile.

### OCS-Transport

**Quelle:** `nextcloud/clients/ocs.py` Zeile 41-44, 65-84, 87-108.
**Gilt für:** alle drei Talk-Aufrufe. Kein eigener Header-Bau, kein `Origin`, keine
Redirect-Verfolgung, Authentifizierung pro Request.

```python
#: The two mandatory headers of D-18. Copied per request, never mutated in place.
OCS_HEADERS: Mapping[str, str] = {"OCS-APIRequest": "true", "Accept": "application/json"}
```

```python
    """... No ``Origin`` header, ever. With one present Nextcloud's CORS middleware demands a
    basic reauthentication, and under AppAPI impersonation there is no password to
    reauthenticate with, so the request would fail for a reason that has nothing to do with
    the payload.
    """
    return await client.post(
        ocs_url(creds, path),
        json=dict(json_body),
        headers={**OCS_HEADERS, "Content-Type": "application/json"},
        auth=creds.auth(),
    )
```

### Paginierung über opake Handles

**Quelle:** `src/mcp_connector/paging.py` Zeile 35-88 (`encode_cursor`, `decode_cursor`,
`read_offset`, `check_scope`).
**Gilt für:** `talk_browse(level="messages")`. **Nicht** für die Konversationsebene
(RESEARCH, Offene Frage 2: kein Cursor dort, nur `truncated`).

Der Scope-Schlüssel ist ein einzelner Buchstabe (`"t"` bei Tables, `"c"` bei Talk), der
Offset-Schlüssel heisst überall `"o"` und muss ein nicht negativer Integer sein, worauf eine
Nachrichten-Id passt.

### Kein Retry auf einem Schreibweg

**Quelle:** `clients/tables.py` Zeile 38-41 und 196-199, `tools/tables.py` Zeile 126-128,
`reg_tables.py` Zeile 67-68.
**Gilt für:** `talk_send` auf allen drei Schichten. Die Formulierung steht dreimal, weil sie
an drei Stellen gelesen wird: im Client-Docstring, im Tool-Docstring und in der
Tool-Beschreibung, die das Modell sieht.

```python
    """Add one row to an existing table; never changes or deletes an existing row.

    A timeout does not mean nothing was written. Read back with tables_browse(level="rows")
    instead of calling this a second time.
    """
```

Für Talk ist es schärfer: eine doppelte Nachricht ist für Dritte sichtbar und durch kein
Werkzeug dieses Servers entfernbar, weil DELETE per Gate verboten ist.

### Automatische Registrierung, eine Datei je Familie

**Quelle:** `server/__init__.py` Zeile 102-114.
**Gilt für:** `reg_talk.py`. Keine Änderung an `server/__init__.py`.

```python
def _load_registrations() -> None:
    """Import every ``reg_*`` module so its tools register themselves.

    Each tool bundle owns its own registration file. That way plans that are written in
    parallel never have to change one shared file, and a new bundle is a new file plus
    nothing else.
    """
```

### Aktivierungszyklus als benannter Preis

**Quelle:** `exapp/ui/strings.py` Zeile 550, 557, 575; `entry_exapp.py` Zeile 256-259;
`docs/oauth-setup.md`.
**Gilt für:** die Beschreibung des neuen Feldes, `docs/oauth-setup.md` und den Fehlersatz von
`talk_send`. Der Satz existiert wörtlich und wird wiederverwendet, nicht neu formuliert.

## Kein Analog gefunden

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `src/mcp_connector/entry_exapp.py` (die neue Zeile) | config | batch | Kein Werkzeug dieses Servers liest heute Konfiguration, und das Overlay erreicht `os.environ` nie (T15). Weg A ist eine neue Art von Zeile in diesem Projekt (A7). Nächstes Verwandtes: der Docstring von `_resolved_env` als Vorbild für die Begründungstiefe, und `config.dns_rebinding_protection` als Vorbild für den Leser auf der anderen Seite. |

Zwei weitere Punkte haben ein Rollen-Analog, aber kein Muster-Analog, und der Planer muss
`09-RESEARCH.md` statt der Codebasis heranziehen:

| Baustein | Wo das Muster steht |
|----------|---------------------|
| 304-Vorprüfung vor `parse_ocs` plus Header-Rückgabe als Tupel | `09-RESEARCH.md`, Muster 3 (ausformuliert). Keine bestehende Route dieses Projekts trägt einen Header als Nutzlast oder einen 3xx-Erfolg. |
| Platzhalter-Auflösung aus `messageParameters` | `09-RESEARCH.md`, Muster 5 (ausformuliert). `tools/deck.py` und `tools/notes.py` haben keine Platzhalter-Semantik. |

## Metadaten

**Suchraum:** `src/mcp_connector/{nextcloud/clients,nextcloud,tools,server,exapp,exapp/ui}`,
`tests/{unit,contract,integration,fixtures}`, `scripts/`, `docs/`, `appinfo/`.
**Gelesene Analoga:** `nextcloud/clients/tables.py`, `nextcloud/clients/ocs.py`,
`nextcloud/capabilities.py`, `tools/tables.py`, `server/reg_tables.py`, `server/__init__.py`,
`config.py`, `entry_exapp.py`, `exapp/admin_settings.py`, `exapp/config_values.py`,
`exapp/ui/strings.py`, `tests/unit/test_tables_client.py`,
`tests/integration/test_tables_roundtrip.py`, `tests/contract/test_tool_surface.py`,
`tests/contract/test_no_destructive_calls.py`, `scripts/check_tool_budget.py`,
`scripts/acceptance_all_tools.py`, `tests/fixtures/deck_boards.json`.
**Strukturell erfasst (Testnamen und Konstanten):** `tests/unit/test_tables_tools.py`,
`tests/unit/test_exapp_admin_settings.py`, `tests/unit/test_exapp_config_values.py`,
`tests/unit/test_config.py`, `tests/integration/test_permission_fidelity_exapp.py`,
`src/mcp_connector/paging.py`, `src/mcp_connector/tools/marks.py`,
`scripts/bootstrap_exapp.sh`, `scripts/bootstrap_test_nc.sh`.
**Kartierungsdatum:** 2026-08-21
