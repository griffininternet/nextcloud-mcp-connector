# Phase 10: Mail strikt lesend und die Trifecta-Grenze, Muster-Karte

**Kartiert:** 2026-08-24
**Analysierte Dateien:** 31 (9 Produktionscode, 11 Tests, 11 Skripte/Doku/Topologie)
**Analoga gefunden:** 29 / 31 (2 ohne echtes Vorbild: `tools/html_text.py`, `tests/integration/test_srv06_degradation.py`)

Diese Phase ist die dritte Werkzeugfamilie in Folge nach demselben Bauplan, und der Bauplan
ist an einer Stelle wörtlich auf sie vorbereitet: `clients/talk.py` sagt in seinem
Modul-Docstring selbst, dass es **keine** Ersetzbarkeitswarnung braucht, "of the kind a Mail
integration would need" (`talk.py:18-20`), und `clients/tables.py` sagt denselben Satz
(`tables.py:23-26`). Die Warnung, die dort fehlt, ist genau der Absatz, den `clients/mail.py`
als erster Client dieses Projekts trägt. Das ist die einzige echte Neuheit der Familie; alles
andere ist Übertragung.

Zwei Vorbilder, und die Aufteilung ist nicht beliebig:

- **Talk (Phase 9)** ist das Vorbild für die Form: ein `browse` mit `level`-Enum, Byte-Kappe,
  Cursor mit Scope-Schlüssel, lokale Sonderstatus-Behandlung im Client, Positivliste im
  Gate, Nur-Lesen-Grep über die Client-Datei.
- **Tables (Phase 8)** ist das Vorbild für die Details: Ziffernwächter auf einer Id, `limit`
  als Keyword ohne Default, Pflicht-Id auf einer tieferen Ebene, gefrorene URL-Literale im
  Unit-Test.

---

## Datei-Klassifikation

### Produktionscode

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `nextcloud/clients/mail.py` (NEU) | client | request-response, nur lesend | `nextcloud/clients/talk.py` | exakt (Talk ist read-plus-one-write, Mail ist read-only) |
| `tools/mail.py` (NEU) | service (tool layer) | CRUD-read plus Paginierung | `tools/talk.py`, sekundär `tools/tables.py` | exakt |
| `tools/html_text.py` (NEU) | utility | transform | keins (nächstes Struktur-Vorbild: `tools/marks.py`) | nur Modulform |
| `tools/marks.py` (GEÄNDERT) | utility | transform | sich selbst (`marks.py:39-53`) | exakt |
| `tools/chatgpt.py` (GEÄNDERT) | service | request-response | `chatgpt.py::_fetch_note` und `::_fetch_file` | exakt |
| `ids.py` (GEÄNDERT) | utility | transform | `ids.py::encode_note` plus `tables.py::_path_id` | exakt (zwei Quellen) |
| `nextcloud/capabilities.py` (GEÄNDERT) | service | request-response mit Cache | sich selbst (`capabilities.py:84-153`) | exakt, mit einer echten Erweiterung |
| `server/reg_mail.py` (NEU) | route (registration) | request-response | `server/reg_talk.py` | exakt |
| `vulture_whitelist.py` (GEÄNDERT) | config | - | `vulture_whitelist.py` Tail-Blöcke | exakt |

### Tests

| Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `tests/unit/test_mail_client.py` (NEU) | test (unit, respx) | request-response | `tests/unit/test_talk_client.py` | exakt |
| `tests/unit/test_mail_tools.py` (NEU) | test (unit) | CRUD-read | `tests/unit/test_talk_tools.py` | exakt |
| `tests/unit/test_html_text.py` (NEU) | test (unit) | transform | `tests/unit/test_contacts_tools.py` (reine Funktionstests) | Rollen-Match |
| `tests/unit/test_ids.py` (GEÄNDERT) | test (unit) | transform | sich selbst (Roundtrip je Präfix) | exakt |
| `tests/unit/test_chatgpt_fetch.py` (GEÄNDERT) | test (unit) | request-response | sich selbst (`note`- und `card`-Zweig) | exakt |
| `tests/unit/test_ocs_capabilities.py` (GEÄNDERT) | test (unit) | request-response | sich selbst, `spreed`-Block (Zeilen 190-273) | exakt |
| `tests/unit/test_exapp_env_setup.py` (GEÄNDERT) | test (unit) | transform | `test_every_description_carries_the_answer_of_the_faq` (1817-1834) | exakt |
| `tests/contract/test_tool_surface.py` (GEÄNDERT) | test (contract) | request-response | Talk-Block (315-358) plus `EXPECTED_TOOLS` (36-57) | exakt |
| `tests/contract/test_no_destructive_calls.py` (GEÄNDERT) | test (contract) | Quelltextanalyse | Talk-Block (104-130, 407-450) | exakt |
| `tests/integration/test_mail_read.py` (NEU) | test (integration) | request-response, echte Instanz | `tests/integration/test_exapp_mail_reach.py` plus Talk-Roundtrip | Rollen-Match |
| `tests/integration/test_srv06_degradation.py` (NEU) | test (integration) | request-response mit Neustart | keins (kein Test startet heute Nextcloud neu) | keins |

### Skripte, Doku, Topologie

| Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `scripts/check_tool_budget.py` (GEÄNDERT) | config | batch | eigener Messzeilen-Block (16-46) | exakt |
| `scripts/acceptance_all_tools.py` (GEÄNDERT) | test (acceptance) | batch | Talk-Block (237-268) plus `EXPECTED_TOOLS` (54) | exakt |
| `scripts/bootstrap_exapp.sh` (GEÄNDERT) | config | batch | Vorlage in `docs/spike-mail.md:125-131` (wörtlich fertig) | exakt |
| `compose.exapp.yml` (GEÄNDERT) | config | - | die drei bestehenden Dienste ohne veröffentlichten Port | exakt |
| `docs/spike-mail.md` (GEÄNDERT) | doc | - | Abschnitt "Replaceability" (101-117) | exakt |
| `docs/privacy.md` (GEÄNDERT) | doc | - | Abschnitt "What leaves your control" | exakt |
| `docs/faq.md` (GEÄNDERT, optional) | doc | - | bestehende Frage-Antwort-Paare | exakt |
| `README.md` (GEÄNDERT) | doc | - | Werkzeugtabelle plus "Known limitations" | exakt |
| `appinfo/info.xml` (GEÄNDERT) | config | - | drei `<description>`-Varianten | exakt |
| `CHANGELOG.md` (GEÄNDERT) | doc | - | Einträge der Phasen 8 und 9 | exakt |

---

## Muster-Zuordnungen

### `nextcloud/clients/mail.py` (client, request-response, nur lesend)

**Analog:** `src/mcp_connector/nextcloud/clients/talk.py`, sekundär `clients/tables.py`

**Modul-Docstring, Absatz-Reihenfolge** (`talk.py:1-37`). Die Reihenfolge ist das Muster:
eine Zeile über die Familie, dann die Header-Frage, dann die Falle der Familie, dann die
Ersetzbarkeit, dann die Obergrenze, dann was absichtlich fehlt, dann die Retry-Regel.
Für Mail fallen die Retry-Regel weg (kein Schreibweg) und die Ersetzbarkeit wird der
längste Absatz.

```python
"""Talk client: two API versions of one app, reading plus one send path.
...
Both mandatory headers of D-18 are already set by :func:`ocs.ocs_get` and
:func:`ocs.ocs_post`, which is why this module deliberately has no header constant of its
own. Tables needs one because its row route belongs to a generation 1 path that is built
directly; every route here goes through the OCS helpers.

The trap of this family is the four read parameters. ...

Neither route carries ``#[OpenAPI(scope: SCOPE_IGNORE)]``, and both stand in the published
``openapi.json`` of the app. They are a promised API, not internal frontend plumbing, so
this module needs no replaceability warning of the kind a Mail integration would need.
...
There is deliberately no edit, no remove, no scheduled-send, no summary, no pinning, no
reminder, no file and no re-sharing path in this module, ... A unit test greps this file
for every one of those paths.
"""
```

Der letzte Satz ist wörtlich zu übertragen: für Mail heisst er "es gibt keinen Sendeweg,
keinen Entwurf, kein Verschieben, kein Markieren, kein Löschen, keinen Anhang, und ein
Unit-Test greppt diese Datei darauf".

**Der Ersetzbarkeits-Absatz kommt aus zwei bestehenden Quellen und wird nicht neu
geschrieben:** `docs/spike-mail.md:101-117` (Original, plus der Satz "Dieser Hinweis gehört
ein zweites Mal in das künftige `clients/mail.py`") und
`tests/integration/test_exapp_mail_reach.py:19-26` (die englische Fassung, dort als
Zwischenlager markiert: "This paragraph belongs in the future
``src/mcp_connector/nextcloud/clients/mail.py`` too, and phase 10 owns putting it there").
Korrektur K1 der Recherche dreht die Aussage: der interne Satz wird bewusst **nicht**
genommen. Der Entwurf aus `10-RESEARCH.md:1112-1120` ist die Zielfassung.

**Pfadkonstanten mit Begründung je Konstante** (`talk.py:49-65`):

```python
#: API version 4, the conversation list. It sits below ``/ocs/v2.php`` and is therefore built
#: through :func:`ocs.ocs_url`, never by string concatenation with the base URL.
ROOM_PREFIX = "/apps/spreed/api/v4/room"

#: API version 1, the chat inside one conversation. The version differs from the one above
#: because the app versions its conversation API and its chat API separately, and mixing the
#: two yields a 404 out of the routing layer that reads like "conversation not found".
CHAT_PREFIX = "/apps/spreed/api/v1/chat"
...
#: Upper bound of one history window. The API caps at 200 and defaults to 100, and a single
#: message may carry 32.000 characters, so 50 is the number this project is willing to place
#: in one answer.
MAX_MESSAGES = 50
```

**Die "kein Parameter, eine Konstante"-Form** für `view=singleton` (`talk.py:67-89`,
Kurzfassung des Kopfes):

```python
#: The four parameters that keep a read a read. Not arguments: an argument is something a
#: caller can get wrong, and getting one of these wrong writes into the user's own account.
READ_ONLY_PARAMS: Mapping[str, int] = {
    "lookIntoFuture": 0,
    "setReadMarker": 0,
    "markNotificationsAsRead": 0,
    "noStatusUpdate": 1,
}
```

Für Mail ist die Begründung eine andere (Falle 12: Threads statt Nachrichten), die Form ist
dieselbe. Und Talk zeigt daneben die zweite Hälfte des Musters: `READ_ONLY_PARAMS` wird
beim Aufruf aufgeklappt (`talk.py:169-178`, `params={**READ_ONLY_PARAMS, "limit": capped, ...}`).

**`limit` als Keyword ohne Default, gekappt an einer Modul-Konstante** (`talk.py:163-182`):

```python
    ``limit`` is a keyword without a default, capped at :data:`MAX_MESSAGES` and lifted to at
    least one, and a negative cursor becomes zero, because the URL is built here and nowhere
    else.
    """
    conversation = _path_token(token)
    capped = min(max(int(limit), 1), MAX_MESSAGES)
    response = await ocs.ocs_get(
        client,
        creds,
        f"{CHAT_PREFIX}/{conversation}",
        params={
            **READ_ONLY_PARAMS,
            "limit": capped,
            "lastKnownMessageId": max(int(last_known_message_id), 0),
        },
    )
```

Die Begründung dafür steht in `tables.py:28-31` und ist für Mail wörtlich richtig (K3, "ein
`limit` ohne Wert bedeutet eine Nachricht"):

```python
``limit`` is enforced, not offered. Both ``limit`` and ``offset`` are nullable in the API,
and leaving the limit out returns *every* row of the table: a table with 20.000 rows becomes
one MCP answer. :func:`get_rows_simple` therefore takes ``limit`` as a keyword without a
default, so forgetting it is an error at the developer, not a full table read at the user.
```

**Lokale Sonderstatus-Behandlung, nicht global** (`talk.py:148-156` und `179-180`). Das ist
das Vorbild für **beide** Mail-Sonderfälle, den 206 (K7) und den 500 der Postfachliste (K6):

```python
    A conversation without messages, and a window past the oldest message, answer **304**
    with no body. That is a success and not a redirect, so it is handled here: the shared
    parser turns every 3xx into "Nextcloud answered with a redirect, check the base URL",
    which would send the reader of a fresh conversation after a configuration problem that
    does not exist. The check stays local because 304 has a meaning on this one route only;
    a second special case in the shared parser would cost more than this line does.
```

```python
    if response.status_code == httpx.codes.NOT_MODIFIED:
        return [], None
    payload = ocs.parse_ocs(response, what=f"the messages of conversation {conversation}")
```

Wichtig für den 500er: `ocs._check_transport` (`ocs.py:224-230`) greift **vor** dem
Envelope, also muss die Mail-Prüfung wie oben **vor** `parse_ocs` stehen und darf nicht auf
eine ausgelöste `ToolError` warten.

**Ziffernwächter auf einer Id** (`tables.py:210-218`), wörtlich für `message/{id}` und
`mailboxes/{mailboxId}` zu übertragen (Falle 11):

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

Die Talk-Variante daneben (`talk.py:217-235`) zeigt, wo der Hinweis-Satz hingehört: er nennt
das Werkzeug, das die richtige Id liefert. Für Mail also "Use an id exactly as mail_browse
reports it".

**Formprüfung der Antwort, zwei Helfer und eine Hint-Konstante** (`talk.py:99` und `254-269`):

```python
_SHAPE_HINT = "Check that the Talk app is enabled and up to date on that instance."
...
def _as_list(payload: Any, what: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ToolError(
            message=f"Nextcloud answered with something that is not a list of {what}.",
            hint=_SHAPE_HINT,
        )
    return [item for item in payload if isinstance(item, dict)]
```

**Nicht übernehmen:** `web_url` (`talk.py:102-104`). Mail hat keine stabile Web-Route für
eine einzelne Nachricht in dieser Recherche, und ein geratener Deep-Link ist schlechter als
keiner. Falls doch einer gebraucht wird, gilt die SSRF-Grenze aus
`test_talk_client.py:384-388`: der Link wird immer aus `creds.base_url` gebaut, nie aus einer
Antwort.

---

### `tools/mail.py` (service, CRUD-read plus Paginierung)

**Analog:** `src/mcp_connector/tools/talk.py`, sekundär `tools/tables.py`

**Modul-Docstring, vier Fettblöcke** (`talk.py:1-32`, gekürzt), und `tables.py:1-26` hat
dieselben vier in derselben Reihenfolge. Das ist die Form, die `tools/mail.py` übernimmt:

```python
"""Talk tools: one browse tool with two levels, and one write behind an administrative switch.

**One tool, two levels.** ``talk_browse(level=...)`` walks the conversations of the account
and the history of one of them. Two separate tools would cost two slots in every client that
limits them and two schemas in every ``tools/list``, for navigation the model can express in
one enum value (D-06). The answer envelope is the same on both levels (``level``, ``count``,
``results``), so the model learns one shape instead of two.

**The limits are enforced, not offered.** ... Every cut is named in the answer, never silent.

**Two things are explained before they can fail.** A missing or disabled Talk app stops both
tools at the capabilities check, before the first Talk request (SRV-04). ...

Deliberately absent: editing a message, removing one, ... The client below has no code for
any of it, which is what makes the create-only annotation of ``talk_send`` honest rather
than a promise (threat T-09-03).
"""
```

**Konstanten-Block** (`talk.py:45-91`, die vier, die Mail eins zu eins braucht):

```python
APP = "spreed"

#: The two navigation levels of ``talk_browse``, in the order a model walks them.
LEVELS = ("conversations", "messages")

#: TALK-02: a history read without an explicit limit reads this many messages and not the
#: window of 100 the API hands over when the parameter is left out.
DEFAULT_LIMIT = 20
MAX_LIMIT = 50

#: Upper bound of one message text, in **bytes**. TALK-02 says "byte cap" literally, and this
#: project budgets in bytes everywhere else too (``MAX_TOOL_BYTES``, ``BUDGET_BYTES``), so the
#: cut is measured on the UTF-8 encoding and not on characters. The number 800 is a setting
#: and not a measurement (A6): it makes 50 messages roughly 40 KB in the worst case, and it
#: stands at this one place so phase 11 can adjust it against ``prepare_context`` in one edit.
MAX_MESSAGE_BYTES = 800
```

Für Mail: `APP = "mail"`, `LEVELS = ("accounts", "mailboxes", "messages")`,
`DEFAULT_LIMIT = 20`, `MAX_LIMIT = 50`, `MAX_PREVIEW_BYTES` nach dem Vorbild von
`MAX_MESSAGE_BYTES` inklusive des Zusatzes "eine Einstellung, keine Messung" (A2/A3 der
Recherche).

**Die Positivliste als Konstante mit Begründung, warum keine Negativliste** (`talk.py:70-80`).
Das ist das Vorbild für `FILTER_TYPES` (MAIL-03) und die Begründung ist bei Mail sogar
stärker, weil der Parser der App still verwirft:

```python
#: The message types that belong in a history a model reads, as a positive list. TALK-02 asks
#: for "no system messages", and a negative list (``!= "system"``) would let the next new verb
#: of the app through by itself. ...
#:
#: There is deliberately no ``include_system`` parameter to switch this off. It would cost
#: schema bytes on every ``tools/list`` for a use nobody has shown, and if one ever turns up
#: it is one line.
KEPT_TYPES = frozenset({"comment", "object_shared", "voice-message", "private_reply"})
```

**`browse()`: Reihenfolge der Prüfungen** (`talk.py:150-183`). Diese Reihenfolge ist das
teuerste Muster der Familie und für Mail unverändert richtig: Level, dann Cursor-Ablehnung,
dann Kappung, **dann** `require_app`, dann Dispatch, und die Pflicht-Id erst im Zweig, der
sie braucht.

```python
async def browse(
    clients: NcClients,
    level: str = "conversations",
    token: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Walk the user's Talk: the conversations of the account, or the history of one of them.

    A ``cursor`` on the conversation level is refused rather than ignored, and it is refused
    here, before the capabilities request, so the cheapest mistake costs no request at all.
    ... a model has no way to notice that its paging went in a circle (review finding IN-04).
    """
    if level not in LEVELS:
        raise ToolError(message=f"{level!r} is not a Talk level.", hint=_LEVEL_HINT)
    if str(cursor or "").strip() and level != "messages":
        raise ToolError(
            message=f"level={level!r} has no next page, so a cursor cannot be applied here.",
            hint=_CURSOR_HINT,
        )
    capped = min(max(limit, 1), MAX_LIMIT)

    await capabilities.require_app(clients, APP)

    if level == "conversations":
        return await _conversations(clients, capped)

    conversation = str(token or "").strip()
    if not conversation:
        raise ToolError(message=f"level={level!r} needs a token.", hint=_CONVERSATION_HINT)
    return await _messages(clients, conversation, capped, cursor)
```

Die Drei-Ebenen-Variante steht in `tables.py:101-123` und ist strukturell die Vorlage für
Mail (drei Ebenen, mittlere und tiefe brauchen eine Id):

```python
    if level == "tables":
        return _envelope(level, await _tables(clients), capped)

    table = str(table_id or "").strip()
    if not table:
        raise ToolError(message=f"level={level!r} needs a table_id.", hint=_TABLE_HINT)

    if level == "columns":
        columns = await tables_client.get_columns(clients.client, clients.creds, table)
        return _envelope(level, [_column(column) for column in columns], capped)

    return await _rows(clients, table, capped, cursor)
```

Für Mail heisst das (A7 der Recherche): `level="mailboxes"` verlangt `account_id` mit einem
Fehler und nimmt **nicht** stillschweigend das erste Konto, `level="messages"` verlangt
`mailbox_id`. Die Hint-Konstanten dazu haben ihr Vorbild in `tables.py:46-54` und
`talk.py:93-110`:

```python
_LEVEL_HINT = f"Use one of: {', '.join(LEVELS)}."
_TABLE_HINT = "Call tables_browse with level=tables first; it lists the table ids."

#: The way out of a cursor on a level that has none. One sentence and the next step, like every
#: other refusal of this family.
_CURSOR_HINT = (
    "Only level=rows hands out a cursor. Call tables_browse without cursor; the answer says "
    "with truncated that it was cut."
)
```

**Der Cursor: dekodieren, Scope prüfen, kodieren** (`talk.py:472-497`). Für Mail ist der
Scope-Schlüssel die `mailbox_id` und der Offset der `dateInt` der ältesten Nachricht der
Seite:

```python
    last_known = 0
    if cursor:
        state = paging.decode_cursor(cursor)
        # A handle of another conversation would silently answer with a page of the wrong
        # chat, and the model has no way to notice. Saying so costs one round trip; guessing
        # is a wrong answer about somebody's conversation.
        paging.check_scope(state, "c", token, "conversation")
        last_known = paging.read_offset(state)
    ...
    if last_given is not None:
        answer["truncated"] = True
        answer["next"] = paging.encode_cursor({"o": last_given, "c": token})
```

`paging.read_offset` (`paging.py:72-77`) nimmt jede nicht negative Ganzzahl, ein
`sent_at`-Zeitstempel passt also ohne Änderung hinein. `check_scope` (`paging.py:80-91`) ist
zugleich das Vorbild für die Filter-Ablehnung: ein Satz plus der nächste Schritt statt einer
stillen Korrektur.

**Der Antwort-Umschlag** (`talk.py:669-675`), identisch in `tables.py`:

```python
def _envelope(level: str, entries: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One answer shape for both levels, truncation named instead of silent."""
    kept = entries[:limit]
    answer: dict[str, Any] = {"level": level, "count": len(kept), "results": kept}
    if len(entries) > len(kept):
        answer["truncated"] = True
    return answer
```

**Byte-Kappe, auf UTF-8 gemessen, mit tolerantem Dekodieren** (`talk.py:573-584`). Für
`previewText` wörtlich zu übernehmen:

```python
def _capped(text: str) -> tuple[str, bool]:
    """One text at :data:`MAX_MESSAGE_BYTES`, and whether it had to be cut.

    The cut is measured on the UTF-8 encoding, because TALK-02 asks for a byte cap and because
    a byte is what an answer actually costs. Slicing the encoded form can land in the middle of
    a multi byte character, so the decode drops what it cannot read: an umlaut at the cutting
    point disappears instead of arriving as a broken character.
    """
    blob = text.encode("utf-8")
    if len(blob) <= MAX_MESSAGE_BYTES:
        return text, False
    return blob[:MAX_MESSAGE_BYTES].decode("utf-8", errors="ignore"), True
```

**Kein Marker in einer Vorschau, aber ein Feld daneben** (`talk.py:430-444` und `505-528`).
Diese Unterscheidung ist für Mail zentral, weil `fetch` (Falle 6) einen Marker braucht und
`mail_browse` keinen:

```python
    A cut preview carries no marker of its own. A preview is a fragment by definition, and the
    full text is one call away on the message level.
```

```python
    The truncation is a field beside the text and never a marker inside it. A marker inside
    foreign text is an attack path (ME-03), and a chat message is the cheapest place for it of
    all, because every participant of a conversation may write one.
    """
    ...
    if cut:
        entry["truncated"] = True
```

**Fremdtext-Durchgang und Zahlen-Härtung** (`talk.py:648-666`):

```python
def _text(value: Any) -> str:
    """Foreign text on its way into the model context, with our own markers removed.
    ...
    """
    return marks.without_marks(str(value))


def _number(value: Any) -> int:
    """A counter or a flag of the app as a number, and 0 for anything that is not one.

    ``bool`` is excluded on purpose: it is an ``int`` in Python, and a ``True`` that arrives
    where a count belongs is a deformed answer and not the number one.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value
```

`_number` ist für Mail der Wächter über `unread`, `dateInt` und `specialRole` (das laut
Recherche `int` **oder** `str` sein kann, also braucht `specialRole` einen eigenen, tolerant
lesenden Helfer und nicht `_number`).

**Die Projektions-Entscheidung wird im Docstring begründet, mit Namensliste des
Weggelassenen** (`talk.py:387-408` und `505-516`). Für Mail betrifft das die elf Booleans in
`flags` und die Threading-Felder:

```python
    """Project one conversation onto the fields a model reads, and drop the other fifty.

    ``GET /api/v4/room`` answers with 59 mandatory fields per conversation: everything about
    calls, the lobby, signaling, SIP, breakout rooms, avatars, recording and live
    transcription. None of that survives here, and neither does the numeric room ``id``: it
    addresses none of the three routes this family builds, and a second identity field in an
    answer is an invitation to use the wrong one.
```

Der letzte Halbsatz ist die fertige Begründung für Falle 10 (`id` gegen `databaseId`).

---

### `tools/html_text.py` (utility, transform)

**Analog: keins.** Die Recherche hat es gemessen (`10-RESEARCH.md:758-761`): im ganzen
`src/`-Baum gibt es keine HTML-zu-Text-Funktion, `import html` in `exapp/ui/layout.py` ist
`html.escape` und damit die Gegenrichtung.

**Was trotzdem übertragbar ist:**

1. **Die Modulform eines Ein-Zweck-Helfers mit langem Docstring:** `tools/marks.py:1-33`.
   Vier Fettblöcke: was das Modul tut, was es kostet, was es nicht tut, die honest limit.
   `tools/html_text.py` braucht genau diese Struktur, mit dem Satz aus
   `10-RESEARCH.md:794-797`: "kein Sanitizer und kein Renderer".
2. **Die honest-limit-Form** (`marks.py:22-28`):

```python
**The honest limit.** Only the exact sequences below are removed. A document can still
write something that reads like a marker, and no filter over free text can prevent that.
```

3. **Die Fehlerbehandlung eines Parsers, der fremde Daten liest:** `ocs.py:248-263`
   (`_json_payload`) ist das nächste Vorbild für "leere Eingabe ist kein Absturz":

```python
    try:
        return json.loads(body) if body else None
    except json.JSONDecodeError:
        raise ToolError(...)
```

Für `html_text` heisst das: leer und nur-Leerraum **vor** dem Parsen abfangen und leeren Text
zurückgeben, nicht `ParserError` durchlassen (Falle 5).

**Planungshinweis:** Die vier gemessenen Anforderungen stehen in `10-RESEARCH.md:775-792`
(Leer-Schutz, `script`/`style` per `drop_tree`, Blockelemente zu Zeilenumbrüchen,
`no_network=True`). Sie sind Messwerte und keine Vorschläge.

---

### `tools/marks.py` (utility, GEÄNDERT: dritter Marker)

**Analog:** die Datei selbst, `marks.py:37-53`. Der dritte Marker und sein Muster werden nach
demselben Bauplan angelegt, und der Kommentar über `_PATTERNS` erklärt schon, warum ein
Muster und nicht ein Literal:

```python
#: Marked inside the text and not only beside it: a model that only reads the excerpt must
#: still be able to tell it from a whole document.
EXCERPT_TRUNCATION = "[excerpt truncated; call fetch with this id for the full text]"

#: The same idea one level down, for a file that was read as a slice. The offset is part of
#: the sentence, because it is what a caller needs to continue.
TRUNCATION_NOTE = "[truncated here; call files_read with offset {offset} to continue]"

_HEAD, _TAIL = TRUNCATION_NOTE.split("{offset}")

#: One pattern per marker. The note is matched by its shape and not by one value: a forged
#: copy carries whatever offset its author chose, so a filter that only knew the number this
#: server would have written would remove none of them.
_PATTERNS = (
    re.compile(re.escape(EXCERPT_TRUNCATION)),
    re.compile(re.escape(_HEAD) + r"\d+" + re.escape(_TAIL)),
)
```

Der neue Marker hat keinen Platzhalter, also ist sein Muster die einfache Form
(`re.escape(...)`) wie in der ersten Zeile von `_PATTERNS`. Falle 6 der Recherche sagt, was
er aussagen muss: hier ist Schluss, es gibt keine Fortsetzung.

**Der Filter selbst bleibt unangetastet** (`marks.py:56-64`) und wirkt automatisch auch auf
den neuen Marker, weil er über `_PATTERNS` läuft:

```python
def without_marks(text: str) -> str:
    """Foreign text with every marker sequence of this server removed.

    Called on the way in, before anything is appended, so the two are never confused: what
    the document wrote is gone by the time the server decides whether to mark a cut.
    """
    for pattern in _PATTERNS:
        text = pattern.sub("", text)
    return text
```

**Der Re-Export-Hinweis** (`marks.py:30-32`) gilt weiter: die nutzenden Module exportieren die
Konstante unter ihrem etablierten Namen, siehe `chatgpt.py:59-63`.

---

### `tools/chatgpt.py` (service, GEÄNDERT: Zweig `mail`)

**Analog:** dieselbe Datei, `_fetch_note` (186-202) für die schlanke Form und `_fetch_file`
(141-183) für Kappung plus Marker plus flache Metadaten.

**Der Dispatch** (`chatgpt.py:124-138`). Ein `case "mail":` kommt hinzu, der `_`-Zweig bleibt
unverändert:

```python
    kind, parts = ids.parse(resource_id)
    match kind:
        case "file":
            return await _fetch_file(clients, parts[0], max_bytes)
        case "note":
            return await _fetch_note(clients, parts[0])
        case "card":
            return await _fetch_card(clients, parts)
        case "event":
            return await _fetch_event(clients, parts[0], parts[1])
        case _:
            raise ToolError(
                message=_UNFETCHABLE,
                hint=f"Open the url in a browser to read it: {parts[0]}",
            )
```

**Die App-Prüfung im Zweig, nicht im Dispatch** (`chatgpt.py:205-207`):

```python
async def _fetch_card(clients: NcClients, parts: tuple[str, ...]) -> dict[str, Any]:
    """Read one Deck card, from the canonical triple or from the short search form."""
    await capabilities.require_app(clients, deck_tools.APP)
```

**Kappung, Marker und flache Metadaten in einem Block** (`chatgpt.py:160-183`). Das ist die
Vorlage für `_fetch_mail` inklusive der Reihenfolge "erst fremde Marker weg, dann eigenen
schreiben" und der Stringisierung jedes Metadatenwerts (Falle 7):

```python
    path = str(entry["path"])
    limit = MAX_TEXT_BYTES if max_bytes is None else max_bytes
    answer = await files_tools.read(clients, path=path, max_bytes=limit)

    # The document's own copy of either marker goes before this server writes one of its
    # own (BL-09, ME-03): a complete file that carries the note would claim to be cut, and
    # a cut one could point the model at an offset its author chose.
    text = marks.without_marks(str(answer["content"]))
    metadata = {"kind": "file", "path": path}
    if answer["content_type"]:
        metadata["content_type"] = str(answer["content_type"])
    if answer["truncated"]:
        offset = int(answer["next_offset"])
        text = f"{text}\n\n{TRUNCATION_NOTE.format(offset=offset)}"
        metadata["truncated"] = "true"
        metadata["next_offset"] = str(offset)

    return {
        "id": ids.encode_file(fileid),
        "title": path.rsplit("/", 1)[-1] or path,
        "text": text,
        "url": f"{clients.creds.base_url}{provider_map.FILE_WEB_PREFIX}/{fileid}",
        "metadata": metadata,
    }
```

Beachten: `"truncated": "true"` ist schon heute ein **String**, und `metadata` wird nur
gefüllt, wenn ein Wert da ist (`if answer["content_type"]:`). Beides ist genau das Muster,
das die Vertrauens-Signale aus MAIL-02 brauchen (`dkim` fehlt, wenn ungeprüft: dann
`"unchecked"` statt eines fehlenden Schlüssels, siehe Entwurf `10-RESEARCH.md:1173-1177`).

**Der Grund, warum die Signale nicht in `text` dürfen**, steht als Regel schon im
Modul-Docstring (`chatgpt.py:30-36`):

```python
**No text of an answer carries a marker this server did not write.** ``text`` is one field
for every kind, so the truncation note of a cut file and the content of a note or a card
land in the same place a model reads. Every one of the four readers therefore filters the
marker sequences out of the foreign text ...
```

**Die Schema-Grenze** (`models.py:40-47`), die Falle 7 auslöst:

```python
class FetchResult(BaseModel):
    """The full content of one hit, plus the little that is worth knowing about it."""

    id: str
    title: str
    text: str
    url: str
    metadata: dict[str, str] | None = None
```

**Der 206-Fall braucht einen eigenen Satz und keine leere Erfolgsantwort** (Falle 5). Das
nächste Vorbild ist `_fetch_event` (`chatgpt.py:265-269`), das genau diese Form hat: ein
Objekt ohne verwertbaren Inhalt wird abgelehnt statt leer beantwortet.

```python
    if not events:
        raise ToolError(
            message=f"The calendar object {object_name} holds no event.",
            hint="Call calendar_list_events for the window you are interested in.",
        )
```

---

### `ids.py` (utility, GEÄNDERT: `mail`)

**Analog:** dieselbe Datei. Mail ist einteilig wie `file` und `note`, also sind es drei
kleine Änderungen an drei Stellen.

**Das Format-Verzeichnis im Docstring** (`ids.py:7-13`) bekommt eine Zeile:

```python
Formats::

    file:<fileid>
    note:<id>
    card:<boardId>:<stackId>:<cardId>      (short form card:<cardId> is accepted)
    event:<calendarUri>:<objectName>
    url:<absolute-url>                     (honest rest category, see pitfall 10)
```

**Der Hinweistext ist Teil des Kontrakts** (`ids.py:20-23`) und wird ergänzt, nicht ersetzt:

```python
_HINT = (
    "Use an id exactly as returned by a search tool: file:<fileid>, note:<id>, "
    "card:<board>:<stack>:<card>, event:<calendar>:<object> or url:<absolute-url>."
)
```

**Encoder und Parse-Zweig** (`ids.py:26-31` und `59-60`):

```python
def encode_note(note_id: str | int) -> str:
    return _join("note", str(note_id))
...
    if kind in ("file", "note"):
        parts = (rest,)
```

Für Mail kommt der Ziffernwächter dazu, den `file` und `note` nicht haben. Vorbild ist der
`card`-Zweig, der eine eigene Formprüfung mit eigener Meldung führt (`ids.py:61-67`):

```python
    elif kind == "card":
        parts = tuple(rest.split(SEPARATOR))
        if len(parts) not in (1, 3):
            raise ToolError(
                message=f"{raw!r} is not a valid card id.",
                hint=_HINT,
            )
```

Der Prüfausdruck selbst ist `text.isdigit()` aus `tables.py:213`. Falle 11 begründet, warum
er hier und nicht nur im Client steht: `mail:abc` soll ohne einen einzigen Request scheitern.

**Die Leersegment-Prüfung am Ende gilt automatisch mit** (`ids.py:75-77`), also braucht
`mail:` keinen eigenen Zweig:

```python
    if any(not part.strip() for part in parts):
        raise ToolError(message=f"{raw!r} has an empty segment.", hint=_HINT)
    return kind, parts
```

---

### `nextcloud/capabilities.py` (service, GEÄNDERT: zweiter Erkennungskanal)

**Analog:** dieselbe Datei. Vier Stellen, und eine davon ist neu in ihrer Art.

**Die Dataclass und `has()`** (`capabilities.py:84-112`). Sie ist `frozen=True, slots=True`,
also funktioniert `dataclasses.replace` für den Nachfüllpfad (Weg A der Recherche):

```python
@dataclass(frozen=True, slots=True)
class Capabilities:
    """The optional-app snapshot of one Nextcloud, as far as this project cares."""

    notes_available: bool = False
    ...
    spreed_chat_max_length: int = DEFAULT_CHAT_MAX_LENGTH

    def has(self, app: str) -> bool:
        """Whether ``app`` is installed. Unknown names are a programming error."""
        flags = {
            "notes": self.notes_available,
            "deck": self.deck_available,
            "tables": self.tables_available,
            # ``spreed`` and not ``talk``: the capabilities document names the section that
            # way, and the key of this mapping is the key of the answer.
            "spreed": self.spreed_available,
        }
        try:
            return flags[app]
        except KeyError:
            raise ValueError(f"{app!r} is not an optional app this server checks") from None
```

`mail_available: bool | None = None` reiht sich in die Felder ein, und `has("mail")` wird
`bool(self.mail_available)`. Der `ValueError`-Zweig bleibt, und der Kommentar über `spreed`
ist das Vorbild für den Kommentar, der erklärt, warum `mail` **kein** Capabilities-Abschnitt
ist.

**`_MISSING`, ein Satz plus ein nächster Schritt** (`capabilities.py:53-81`). Der
Talk-Eintrag ist die kürzeste Form und damit die Vorlage:

```python
#: message plus hint per optional app (D-15). The wording is part of the contract: it is
#: what the user reads, so it names the app and one thing to do instead.
_MISSING: dict[str, tuple[str, str]] = {
    ...
    "spreed": (
        "The Talk app is not available on this Nextcloud.",
        "Ask an administrator to enable the Talk app for this account.",
    ),
}
```

Der Wortlaut für Mail steht in `10-RESEARCH.md:642-646` und ist im selben Stil gebaut.

**Cache-Lesen und -Schreiben in einer Zeile** (`capabilities.py:119-130`). Der Nachfüllpfad
muss denselben Schlüssel und den **ursprünglichen** Zeitstempel schreiben, damit die TTL
nicht durch eine zweite Frage verlängert wird:

```python
async def load(clients: NcClients) -> Capabilities:
    """Return the capabilities of this credential context, cached for ``TTL_SECONDS``."""
    key = (clients.creds.base_url, clients.creds.user)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached is not None and now - cached[0] < TTL_SECONDS:
        return cached[1]

    response = await ocs.ocs_get(clients.client, clients.creds, CAPABILITIES_PATH)
    result = parse(ocs.parse_ocs(response, what=_WHAT))
    _cache[key] = (now, result)
    return result
```

**`require_app` bleibt der einzige Eingang** (`capabilities.py:138-147`), und der
Mail-Nachfüllpfad hängt dort hinein, nicht in `load`:

```python
async def require_app(clients: NcClients, app: str) -> Capabilities:
    """Return the capabilities, or raise :class:`AppMissingError` if ``app`` is absent.

    Called first by every tool of an optional app, which is what keeps a missing app from
    producing a request that could only fail with an HTML page or a 404.
    """
    result = await load(clients)
    if not result.has(app):
        raise app_missing(app)
    return result
```

**Das defensive Lesen einer fremden Antwort** (`capabilities.py:156-171` und `217-226`) ist
das Vorbild für das Lesen der Navigationsliste. Wichtig ist die Gegenrichtung, die die
Recherche fordert: eine **leere** Liste ist ein Fehler und nicht "Mail fehlt"
(`10-RESEARCH.md:656-658`), also ist `parse` hier nicht wörtlich zu kopieren, sondern der
`_as_list`-Ansatz aus `talk.py:254-260`.

```python
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

**Die harte Grenze dieser Änderung:** `ALLOWED_MODULE_STATE` in
`tests/contract/test_no_destructive_calls.py:199-202` nennt genau zwei Einträge, und
`test_the_two_allowed_caches_still_exist_where_they_are_claimed_to_be` (517-522) prüft die
Zahl:

```python
    assert len(ALLOWED_MODULE_STATE) == 2, (
        "the exceptions are counted, not only described: a third cache is a decision, and a "
        "decision has to be made in a review and not in a diff (D-20, T-08-23)"
    )
```

Ein eigener Navigations-Cache ist damit kein Implementierungsdetail, sondern eine
Review-Entscheidung. Weg A der Recherche vermeidet sie.

---

### `server/reg_mail.py` (route, request-response)

**Analog:** `src/mcp_connector/server/reg_talk.py`, vollständig. Die Datei ist kurz genug,
dass sie als Ganzes die Vorlage ist.

**Der Modul-Docstring nennt die drei Entscheidungen der Registrierungsschicht**
(`reg_talk.py:1-15`):

```python
"""Registration of the talk tools. The logic lives in :mod:`mcp_connector.tools.talk`.

``level`` is a ``Literal`` and therefore an enum in the input schema, not a free string: the
model sees the two valid values instead of guessing "chats" or "history" and paying a round
trip for the correction (D-06, D-14).

Both tools are listed unconditionally, even on an instance without the Talk app. A credential
dependent ``tools/list`` is not cacheable, breaks the token budget gate and surprises clients
that persist tool lists; the honest answer to a missing app is the sentence the tool returns
(SRV-04). ...

Empty strings are the defaults instead of ``None``, so no ``anyOf`` of string and null reaches
the schema; the bodies below turn them back into ``None`` before the call.
"""
```

**Das Werkzeug selbst** (`reg_talk.py:27-59`). `mail_browse` ist dieselbe Form mit einem
Parameter mehr (`filter`), und `MAX_LIMIT`/`DEFAULT_LIMIT` kommen wie hier aus dem
Tools-Modul, damit die Zahl an einer Stelle steht:

```python
@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def talk_browse(
    level: Annotated[
        Literal["conversations", "messages"],
        Field(description="What to list; messages needs a token"),
    ] = "conversations",
    token: Annotated[
        str, Field(description="Conversation token from level=conversations, e.g. gzu8sw3d")
    ] = "",
    limit: Annotated[
        int, Field(ge=1, le=talk_tools.MAX_LIMIT, description="Maximum number of entries")
    ] = talk_tools.DEFAULT_LIMIT,
    cursor: Annotated[
        str,
        Field(description="Next page handle from a truncated messages answer; only that level"),
    ] = "",
    ctx: Context | None = None,
) -> str:
    """List the conversations of this account, or the history of one of them.

    The message level answers newest first, and the next page runs further into the past.
    """
    clients = deps.resolve_clients(ctx)
    return compact(
        await talk_tools.browse(
            clients,
            level=level,
            token=token or None,
            limit=limit,
            cursor=cursor or None,
        )
    )
```

**Registrierung geschieht durch die Existenz der Datei** (`server/__init__.py:101-110`), also
gibt es keine zentrale Liste zu pflegen:

```python
def _load_registrations() -> None:
    """Import every ``reg_*`` module so its tools register themselves.

    Each tool bundle owns its own registration file. ...
    """
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("reg_"):
            importlib.import_module(f"{__name__}.{module.name}")
```

`READ_ONLY`, `compact` und `graceful` kommen aus `server/__init__.py:54-99`.

**Die Budget-Grenze ist hier zu bezahlen:** `talk_browse` kostet 861 bis 886 Bytes
(`check_tool_budget.py:36-39`), und `mail_browse` hat einen Parameter mehr. Jedes Wort in
`Field(description=...)` ist ein Byte im `tools/list` jeder Sitzung.

---

### `tests/unit/test_mail_client.py` (test, unit, respx)

**Analog:** `tests/unit/test_talk_client.py`

**Der Docstring sagt, welche Eigenschaften Kontrakt sind und nicht Implementierung**
(`test_talk_client.py:1-25`, gekürzt):

```python
"""Unit tests for the Talk client, all paths, asserted on the request that was built.

Two properties of this client are contract and not implementation detail, and neither of
them is visible in a parsed answer, which is why they are tested against the URL:
...
The two API versions of the family stand below as frozen literals: conversations are v4 and
the chat is v1, and mixing the two yields a 404 out of the routing layer that reads like
"conversation not found".

The rest is the usual catalogue: the created status on the send, ... an empty conversation
without messages that answers 304, an instance without a single conversation, a token that
never reaches Nextcloud, an answer shape that does not fit, ...
"""
```

Für Mail sind die zwei Kontrakt-Eigenschaften: **jede** Nachrichten-URL trägt
`view=singleton` und ein explizites `limit`.

**Gefrorene URL-Literale** (`test_talk_client.py:41-49`). Für Mail sind es vier statt zwei,
und sie sind die Absicherung gegen die Verwechslung von OCS-Route und interner Route:

```python
BASE = "http://nc.test"
USER = "alice"
SECRET = "app-password-test"
TOKEN = "abcd1234"

# The frozen endpoint literals. They are the guard against mixing up the two API versions of
# one app: a route that changes its version here has to be changed on purpose.
ROOM_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v4/room"
CHAT_URL = f"{BASE}/ocs/v2.php/apps/spreed/api/v1/chat/{TOKEN}"
```

**Der OCS-Envelope-Helfer** (`test_talk_client.py:57-65`), für die 996er- und
998er-Antworten der Recherche direkt nutzbar:

```python
def envelope(data: object, statuscode: int = 200, message: str = "OK") -> dict[str, Any]:
    """An OCS v2 envelope around any payload."""
    return {
        "ocs": {
            "meta": {"status": "ok", "statuscode": statuscode, "message": message},
            "data": data,
        }
    }
```

**Der Nur-Lesen-Grep über die Client-Datei** (`test_talk_client.py:391-413`). Das ist der
Test, den MAIL-01 SC4 zusätzlich verlangt, und er wird für Mail länger:

```python
def test_the_module_has_no_edit_remove_or_scheduled_send_path() -> None:
    """The server promise of this family, kept by not writing the code (threat T-09-03).

    ``PUT`` is not a forbidden verb in this project, so editing a message would be caught by
    no verb check at all. The list below is therefore a positive statement about the three
    path forms this module builds, ...
    """
    source = Path(talk_client.__file__).read_text(encoding="utf-8")
    for forbidden in (
        ".put(",
        ".patch(",
        ".delete(",
        "/schedule",
        ...
    ):
        assert forbidden not in source, f"{forbidden} has no place in a read plus send client"
```

Für Mail zusätzlich `ocs_post`, `.post(`, `client.request` und `/message/send`. Die kürzere
Variante desselben Musters steht in `tests/unit/test_contacts_tools.py:244-248` (D-07) und
gilt für die Tool-Schicht:

```python
def test_the_tool_module_has_no_write_path(clients: NcClients) -> None:
    """D-07: contacts are read only, and that stays greppable in the tool layer too."""
    source = Path(contacts_tools.__file__).read_text(encoding="utf-8")
    for call in (".put(", ".delete(", ".patch("):
        assert call not in source
```

**Konstruktive Prüfung der Signatur statt einer Dokumentation** (`test_talk_client.py:416-425`).
Für `limit` in `get_messages` von Mail wörtlich zu übernehmen:

```python
def test_the_readers_take_their_limits_as_keywords_without_a_default() -> None:
    """Constructive rather than documented: an omitted decision does not compile away."""
    limit = inspect.signature(talk_client.get_messages).parameters["limit"]
    assert limit.default is inspect.Parameter.empty
    assert limit.kind is inspect.Parameter.KEYWORD_ONLY
```

**Der Wächter, der keinen Request auslöst** (`test_talk_client.py:378-381`): Die
Ziffernwächter-Tests behaupten `len(route.calls) == 0` und dass der Hinweis das richtige
Werkzeug nennt.

```python
    assert len(route.calls) == 0
    assert "talk_browse" in excinfo.value.hint
```

---

### `tests/contract/test_no_destructive_calls.py` (test, contract, GEÄNDERT)

**Analog:** dieselbe Datei, Talk-Block. Vier Bausteine, alle vier für Mail zu wiederholen.

**Die Nadeln mit Begründung im Wert** (`test_no_destructive_calls.py:64-89`, plus der
Kommentarblock 32-63, der erklärt, warum eine Nadel auf ein **Pfadsegment** zeigt und nicht
auf ein Anführungszeichen):

```python
FORBIDDEN: dict[str, str] = {
    "DELETE": "no tool may delete anything",
    ...
    "/schedule": "no tool may hand a message to the app for later delivery: the app would "
    "send it, which walks around the administrative switch of TALK-04",
    ...
    "/read": "no tool may move the read marker of this account or reset it to unread",
    ...
}
```

Zwei bestehende Nadeln greifen laut Recherche schon in die Mail-Familie: `/attachment`
verbietet die Anhangsroute, `/read` verbietet `/api/mailboxes/{id}/read`. Das gehört als
Satz in den Kommentarblock, nach dem Vorbild von Zeile 61-63:

```python
# ``/share`` already stands above and needs no second entry: the attachment route of Talk is
# ``chat/{token}/share``, so the Tables needle covers it. An eleventh needle beside it would
# only look like more security.
```

**Die Gegenprobe-Zeilen, eine je Nadel, in der f-String-Schreibweise des Projekts**
(`test_no_destructive_calls.py:104-119`):

```python
#: The ten needles above that name a Talk route, with a line that would carry them into the
#: code. Same job as :data:`TABLES_ROUTES` one family earlier: a needle nobody ever hit is
#: indistinguishable from no needle at all, so every one of them gets the line it has to
#: report, written in the f-string spelling this project uses for a path.
TALK_ROUTES: dict[str, str] = {
    "/schedule": '    await ocs.ocs_post(client, creds, f"{CHAT_PREFIX}/{room}/schedule", b)',
    ...
}
```

**Die Positivliste** (`test_no_destructive_calls.py:121-130`). Für Mail sind es vier Formen,
und die Recherche nennt sie als den wichtigeren Teil des Beweises, weil Lese- und Sendeweg
das Präfix `/message/` teilen:

```python
#: The three forms :mod:`mcp_connector.nextcloud.clients.talk` really builds: the conversation
#: list, one window of history, and the one send. This tuple is the half of the proof the
#: needles cannot deliver, because PUT is not a forbidden verb here (see the block above
#: :data:`FORBIDDEN`): the family says out loud which path forms exist instead of only saying
#: which ones must not.
ALLOWED_TALK_ROUTES = (
    '    await ocs.ocs_get(client, creds, ROOM_PREFIX, params={"noStatusUpdate": 1}),',
    '    await ocs.ocs_get(client, creds, f"{CHAT_PREFIX}/{conversation}", params=params),',
    '    await ocs.ocs_post(client, creds, f"{CHAT_PREFIX}/{conversation}", {"message": t}),',
)
```

**Die drei Tests dazu** (407-450). Der erste läuft über den **echten** Prüfpfad `_violations`
(250-270) und behauptet beide Richtungen; genau das verlangt MAIL-01 SC4 für
`/message/send`:

```python
@pytest.mark.parametrize(("needle", "line"), sorted(TALK_ROUTES.items()))
def test_each_talk_needle_trips_on_its_route_and_leaves_the_real_module_alone(
    needle: str, line: str
) -> None:
    """Counter proof per Talk needle: it hits the route, and it misses today's code.
    ...
    """
    relative = "nextcloud/clients/talk.py"
    real = _code_lines(SRC / relative)
    assert _violations(relative, real) == [], (
        f"{relative} must be clean before a needle can prove anything"
    )

    findings = _violations(relative, [*real, (len(real) + 1, line)])
    assert any(repr(needle) in finding for finding in findings), (
        f"the gate must report {needle!r} for: {line.strip()}"
    )


def test_every_talk_needle_of_this_phase_has_a_counter_proof() -> None:
    """A needle without a counter proof is a claim, and this file does not make claims."""
    assert len(TALK_ROUTES) == 10, (
        "ten Talk segments are named in FORBIDDEN, and each of them needs its own line here"
    )
    unbacked = sorted(needle for needle in TALK_ROUTES if needle not in FORBIDDEN)
    assert unbacked == [], f"a counter proof for a needle nobody armed: {unbacked}"


def test_the_three_routes_the_talk_client_really_builds_stay_allowed() -> None:
    """The other half of the same proof: the two reads and the one send must pass.
    ...
    """
    for line in ALLOWED_TALK_ROUTES:
        assert _violations("nextcloud/clients/talk.py", [(1, line)]) == [], (
            f"the gate must not report the allowed route: {line.strip()}"
        )
```

**Falls eine Mail-Nadel eine erlaubte Leseroute trifft**, ist die Ausnahmeform vorgegeben
(`test_no_destructive_calls.py:140-154` und `298-302`), mit der Regel: exakte Literale, eine
Datei, plus ein Gegenprobe-Test (453-473). Der Kommentar sagt, warum die Ausnahme so eng ist:

```python
# The two reads that live below a segment a needle names, and the file they live in. Both are
# GETs, both are what the Tables family exists for, and both are named as the exact literal
# the client writes: ...
# A second route below the same segment, in this file as much as in any other, is still a
# finding, which is what keeps the exemption from becoming "ignore Tables routes here".
FILES_WITH_THE_TABLES_READS = frozenset({"nextcloud/clients/tables.py"})
TABLES_READ_FORMS = (
    'f"/tables/{table}/rows/simple"',
    'f"{V2_PREFIX}/columns/{NODE_TYPE_TABLE}/{table}"',
)
```

---

### `tests/contract/test_tool_surface.py` (test, contract, GEÄNDERT)

**Analog:** dieselbe Datei, Talk-Block.

**Die gefrorene Menge und die gefrorene Zahl** (`test_tool_surface.py:36-57` und `429-434`):

```python
EXPECTED_TOOLS = {
    "files_search",
    ...
    "tables_browse",
    "tables_create_row",
    "talk_browse",
    "talk_send",
    "search",
    "fetch",
}
```

```python
    """The whole surface in one assertion: 20 tools, and the diet holds for 18 of them."""
    ...
    assert set(tools) == EXPECTED_TOOLS
    assert len(tools) == 20, "the curated set is 20 tools, no more and no fewer"
```

Beide Zahlen im Docstring **und** in der Assertion, und der Docstring von Zeile 429 ist
mitzuziehen: das ist die "eingefrorene Literale"-Falle aus Phase 9.

**Der familienspezifische Test** (`test_tool_surface.py:315-358`) ist die Vorlage für
`mail_browse`, inklusive der Enum-Prüfung und der Liste der Werkzeuge, die es **nicht** gibt:

```python
    for name in ("talk_browse", "talk_send"):
        assert name in tools, f"{name} is part of the curated set (TALK-01 to TALK-03)"
        assert tools[name].output_schema is None, "structured_output=False (schema diet)"

    browse = tools["talk_browse"]
    annotations = browse.annotations
    assert annotations is not None
    assert annotations.read_only_hint is True, "talk_browse only reads"
    assert annotations.open_world_hint is False

    schema = browse.input_schema
    assert schema["properties"]["level"]["enum"] == ["conversations", "messages"], ...
    ...
    forbidden = {
        "talk_list_messages",
        "talk_read_message",
        "talk_send_message",
    }
    assert not (names & forbidden), f"talk_browse and talk_send cover these: {names & forbidden}"
```

Für Mail heisst die verbotene Menge sinngemäss `mail_send`, `mail_list_messages`,
`mail_read_message`, `mail_search`.

**`CREATE_TOOLS` bleibt unverändert** (`test_tool_surface.py:59-60`), und das ist eine
prüfbare Aussage dieser Phase: Mail fügt kein Schreibwerkzeug hinzu.

```python
# The six write paths. Everything else in EXPECTED_TOOLS only reads (D-16).
CREATE_TOOLS = {
```

Der Kommentar sagt "six"; er bleibt sechs und die Zahl der reinen Leser wächst von vierzehn
auf fünfzehn. Auch `test_tool_surface.py:531` trägt die Zahl im Docstring ("six create-only
tools, fourteen pure reads") und muss mit.

**Die Doku-Zählwächter** (`test_tool_surface.py:620-631`): jede Zahl in `docs/` und `README`
wird gegen `len(EXPECTED_TOOLS)` geprüft, also ist die Werkzeugzahl in der Doku kein zweiter
Pflegeort, aber sie muss stimmen.

---

### `tests/unit/test_ocs_capabilities.py` (test, unit, GEÄNDERT)

**Analog:** dieselbe Datei, `spreed`-Block (190-273).

**Der Cache-Reset als autouse-Fixture** (`test_ocs_capabilities.py:56-59`) ist die
Voraussetzung für jeden Nachfüllpfad-Test:

```python
@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    """Every test starts with an empty cache; leaking one would hide a real call."""
    capabilities.clear_cache()
```

**Der Vorhanden-Test mit respx und `assert_all_called`** (`test_ocs_capabilities.py:195-212`).
Für Mail sind es zwei Mocks (Capabilities plus Navigation), und `assert_all_called=True` ist
zugleich der Beweis, dass der zweite Request wirklich stattfindet:

```python
    with respx.mock(assert_all_called=True) as mock:
        mock.get(CAPABILITIES_URL).mock(return_value=httpx.Response(200, json=payload))
        caps = await capabilities.load(clients)

    assert caps.spreed_available is True
    assert caps.has("spreed") is True
```

**Der Fehlt-Test ohne Netz** (`test_ocs_capabilities.py:215-222`) und der Fehlt-Test mit
Meldungsprüfung (`258-272`):

```python
def test_an_instance_without_a_talk_section_reports_it_as_absent() -> None:
    """A Nextcloud without Talk is a normal Nextcloud, and the fallback length still holds."""
    caps = capabilities.parse({"capabilities": {"core": {}}})

    assert caps.spreed_available is False
    assert caps.has("spreed") is False
```

```python
async def test_require_app_names_the_missing_talk_app_and_the_next_step(
    clients: NcClients,
) -> None:
    """The user cannot install an app, so the one action names who can (D-15)."""
    ...
    assert excinfo.value.message == "The Talk app is not available on this Nextcloud."
    assert "Talk app" in excinfo.value.hint
    assert excinfo.value.hint != excinfo.value.message
```

**Der Unbekannt-Name-Test** (`test_ocs_capabilities.py:298-303`) trägt einen Kommentar, der
diese Phase direkt betrifft: der dort benutzte Name musste zuletzt geändert werden, als Talk
die vierte geprüfte App wurde. Mit `mail` als fünfter ist erneut zu prüfen, dass der
Beispielname noch eine App ist, die dieses Projekt **nicht** kennt.

---

### `scripts/check_tool_budget.py` (config, GEÄNDERT: Zwischenanhebung)

**Analog:** der eigene Messzeilen-Block (`check_tool_budget.py:16-46`). Die Form einer
Anhebung ist dort dreimal vorgeführt, und die Regel steht im letzten Absatz:

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
#   Measurement 2026-08-21, all 20 curated tools registered: 14312 bytes
#   Budget      unchanged at 15000, because the measurement fits below it
#
#   Measurement 2026-08-21, same 20 tools, cursor description of tables_browse and
#               talk_browse says which level hands one out (review finding IN-04): 14358 bytes
#   Budget      unchanged at 15000, because the measurement fits below it
#
# The older lines stay where they are: a regression is only attributable when the number it
# regressed from is still readable. ...
#
# The headroom is for wording, not for a new tool: at ~4 bytes per token the whole surface
# costs roughly 3.6k tokens in every single session of every client. A twenty-first tool or a
# description that grows into a paragraph is supposed to trip this gate, so the decision
# gets made on purpose instead of by accident. Raising the number is allowed, but only
# together with a new measurement line above, so a regression stays attributable.
BUDGET_BYTES = 15_000
```

Der Satz "A twenty-first tool ... is supposed to trip this gate" ist wörtlich diese Phase.
Die neue Zeile trägt Datum, Werkzeugzahl 21, die Messung, die Rechnung (plus 15 Prozent,
aufgerundet auf 500) und den Vermerk "Zwischenstand, TOOL-15 verankert in Phase 11 neu".

**`MAX_TOOL_BYTES` bleibt bei 1400** (`check_tool_budget.py:48-63`) und ist der eigentliche
Wächter für `mail_browse` (A5 der Recherche).

---

### `scripts/acceptance_all_tools.py` (test/acceptance, GEÄNDERT)

**Analog:** der Talk-Block derselben Datei (237-268) und die zwei gefrorenen Zahlen.

```python
# The count the registry answers today. It stood at 15 while the registry already listed
# 16, which is the kind of drift only a number in two places produces, so it is raised in
# the same commit that raises every other frozen number of a phase.
EXPECTED_TOOLS = 20
```

**Der Aufruf-Block mit ehrlichem SKIP** (`acceptance_all_tools.py:237-253`). Für Mail ist der
SKIP-Fall der häufigere, weil ein Abnahmelauf ohne Mail-Konto normal ist:

```python
    conversations = loads(await call(client, report, "talk_browse", {"level": "conversations"}))
    entries = [entry for entry in (conversations.get("results") or []) if isinstance(entry, dict)]
    first = str(entries[0].get("token") or "") if entries else ""
    if first:
        await call(client, report, "talk_browse", {"level": "messages", "token": first})
    else:
        report.add(
            "talk_browse",
            "SKIP",
            "no conversation on this account, so there is no history to read back",
        )
```

Die zweite Namensliste am Dateiende (`acceptance_all_tools.py:385-395`) ist der dritte
Pflegeort und wird leicht übersehen.

---

### `tests/unit/test_exapp_env_setup.py` und `appinfo/info.xml` (SEC-01)

**Analog:** `test_every_description_carries_the_answer_of_the_faq`
(`test_exapp_env_setup.py:1817-1834`). Das ist die Form, in der ein Store-Satz prüfbar wird:

```python
def test_every_description_carries_the_answer_of_the_faq(manifest_root: etree._Element) -> None:
    """The store text is the only place a user reads without visiting the repository, so
    the answer has to stand there and not only be linked (05-RESEARCH open question 2).

    One marker per fact, in the language of the variant: nothing runs on its own, there is
    a switch per account, and a connection can be ended on its own.
    """
    markers = {
        None: ("background", "switch", "disconnect"),
        "de": ("Hintergrund", "Schalter", "trenn"),
        "fr": ("arrière-plan", "interrupteur", "déconnect"),
    }

    for lang, expected in markers.items():
        description = _localised(manifest_root, "description", lang)
        assert description is not None
        for marker in expected:
            assert marker in description, f"the {_lang_label(lang)} description misses {marker!r}"
```

Der Vorschlag der Recherche für das vierte Tripel: EN `read only`, DE `nur lesen`, FR
`lecture seule`.

**Das Textgate, das den Manifest-Text prüft** (`description_problems`,
`test_exapp_env_setup.py:1719-1780`) und die Falle, die genau bei Mail zuschlägt
(`test_exapp_env_setup.py:1672-1678` und `1776-1778`):

```python
#: Project vocabulary rule: this word must not appear in a public artefact of this repo,
#: and the manifest is the most public one there is. Matched case insensitively, and only
#: against element text, so the explanatory comments of the manifest cannot trip it.
FORBIDDEN_VOCABULARY = "archiv"
```

```python
    text = element_text_without_comments(root)
    if FORBIDDEN_VOCABULARY in text.casefold():
        problems.append(f"the manifest text carries the forbidden word {FORBIDDEN_VOCABULARY!r}")
```

Eine Aufzählung der Postfächer im Store-Text ist damit in allen drei Sprachen rot. Die
Beschreibung nennt Ebenen, keine Postfachnamen.

**Die Gegenprobe-Form für ein neues Gate-Verbot** (`test_exapp_env_setup.py:1899-1907`) bleibt
unverändert nutzbar und muss nicht angefasst werden:

```python
def test_the_text_gate_rejects_the_forbidden_vocabulary(manifest_root: etree._Element) -> None:
    """The project vocabulary rule, on the most public artefact of the repository."""
    for element in manifest_root.findall("description"):
        if element.get("lang") is None:
            element.text = "First paragraph.\n\nThe Archive of your data stays untouched.\n"

    problems = description_problems(manifest_root)

    assert any("forbidden word" in problem for problem in problems)
```

---

### `tests/integration/test_mail_read.py` (test, integration)

**Analog:** `tests/integration/test_exapp_mail_reach.py` für den Rahmen (Lauf gegen die
HaRP-Topologie, `-m integration`, Messprotokoll als Ausgabe), plus die Talk-Roundtrip-Datei
für die Fachprüfungen.

**Der Docstring nennt, was gemessen wird und was ausdrücklich nicht behauptet wird**
(`test_exapp_mail_reach.py:11-19`):

```python
Four things are load bearing in here.

*   **The measured question.** Not "does Mail work", but "did app code answer". A JSON body
    with any status code (200, 403, 404, 500) proves the controller was reached, because
    nothing but app code produces those bodies. Only an HTML body or a redirect to ``/login``
    disproves it. That is why no test below asserts ``status == 200``: the three listing ways
    touch IMAP, and an IMAP error is still app code answering.
```

**Der Lauf-Block als Kopiervorlage** (`test_exapp_mail_reach.py:32-41`):

```
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q
```

**Die Zwei-Konten-Naht** (Falle 15 der Recherche): das Vorbild ist
`tests/integration/test_permission_fidelity.py`, aber die Vorbedingung ist eine andere. Bob
hat kein Mail-Konto und bekommt 200 mit `[]`, also braucht der Negativbeweis ein Mail-Konto
für alice und die Erwartung 403 oder 404 bei bob, nicht die Erwartung "Fehler wegen
fehlenden Kontos".

**Die GreenMail-Vorlage steht wörtlich fertig** in `docs/spike-mail.md:119-131` und ist nach
`compose.exapp.yml` und `scripts/bootstrap_exapp.sh` zu übertragen, ohne veröffentlichten
Port (T-08-05).

---

## Querschneidende Muster

### Fehlermodell: ein Satz plus ein nächster Schritt

**Quelle:** `src/mcp_connector/errors.py:9-20`
**Gilt für:** jede neue Ablehnung in `clients/mail.py`, `tools/mail.py`, `ids.py`,
`capabilities.py`, `html_text.py`

```python
class ToolError(Exception):
    """A failure a caller can act on: what went wrong plus what to do about it."""

    def __init__(self, message: str, hint: str) -> None:
        super().__init__(f"{message} Hint: {hint}")
        self.message = message
        self.hint = hint


class AppMissingError(ToolError):
    """A Nextcloud app the tool needs (Notes, Deck, ...) is not installed."""
```

Der `hint` nennt immer ein Werkzeug oder eine Handlung, nie eine Diagnose. Und er ist nie
gleich der `message` (das prüft `test_ocs_capabilities.py:272`).

### Fremdtext-Behandlung: `without_marks` an jeder Eintrittsstelle

**Quelle:** `tools/marks.py:56-64`, angewandt in `talk.py:648-655`, `talk.py:561`,
`chatgpt.py:167`, `chatgpt.py:199`, `chatgpt.py:224`
**Gilt für:** jeden Mail-Text, der in eine Antwort geht: `subject`, `previewText`,
`from.label`, `body` nach der HTML-Wandlung, `displayName` eines Postfachs

Mail ist der Ort, an dem dieses Muster am meisten zählt: eine Mail schreibt jeder Fremde,
und zwar ohne im Adressbuch zu stehen. Die Reihenfolge ist fest: erst fremde Marker
entfernen, dann eigenen Marker anhängen (`chatgpt.py:163-175`).

### App-Erkennung als erste Zeile eines Werkzeugs

**Quelle:** `capabilities.py:138-147`, angewandt in `talk.py:175`, `tables.py:110`,
`chatgpt.py:207`
**Gilt für:** `tools/mail.py::browse` und `chatgpt.py::_fetch_mail`

Die einzige dokumentierte Umkehrung dieser Regel ist der Schreibweg von Talk
(`talk.py:22-25`: der Admin-Schalter steht vor der App-Erkennung). Mail hat keinen
Schreibweg, also gilt die Regel ohne Ausnahme.

### OCS-Transport: zwei Header, zwei Parser, kein Redirect

**Quelle:** `nextcloud/clients/ocs.py:37-57`, `72-91`, `158-179`
**Gilt für:** `clients/mail.py` vollständig

```python
#: OCS v2 lives under this prefix; v1 is not used anywhere in this project.
OCS_PREFIX = "/ocs/v2.php"

#: The two mandatory headers of D-18. Copied per request, never mutated in place.
OCS_HEADERS: Mapping[str, str] = {
    "OCS-APIRequest": "true",
    "Accept": "application/json",
}
...
_OK_STATUS = frozenset({100, 200, 201})
```

`clients/mail.py` baut jede URL über `ocs.ocs_get` und braucht deshalb **keine** eigene
Header-Konstante (`talk.py:8-11` erklärt genau diesen Unterschied zu Tables). `_OK_STATUS`
wird **nicht** um 206 erweitert (K7); der Statuscheck steht lokal, vor `parse_ocs`.

Die Statusmeldungen kommen aus `_status_error` (`ocs.py:266-310`), und die 404-Zeile ist für
Mail schon richtig formuliert:

```python
    if status in (404, 998):
        return ToolError(
            message=f"Nextcloud did not find {what}.{suffix}",
            hint="Search for it first; the id or the name is unknown to this instance.",
        )
```

Genau dieser Hinweis ist aber der Grund für die Vorprüfung: ohne `require_app` landet eine
fehlende Mail-App in diesem Zweig und das Modell wird zum Suchen in einer App geschickt, die
es nicht gibt (`10-RESEARCH.md:678-681`).

### Paginierung über opake Handles, ohne Serverzustand

**Quelle:** `paging.py:1-16`, `35-91`
**Gilt für:** `tools/mail.py`, Ebene `messages`

Ein Handle ist base64url von kompaktem JSON, nicht signiert, mit `o` für die Position und
einem Scope-Schlüssel daneben. `check_scope` ist die Ablehnung, `read_offset` der Wächter.
Die Sekundengrenze des Mail-Cursors (Falle 13) wird **benannt** und nicht repariert; das
Vorbild dafür ist die honest-limit-Form aus `marks.py:22-28` und die
Kalenderfenster-Entscheidung.

### Kein Retry, und bei Mail: kein Loop

**Quelle:** `talk.py:33-36`, `tables.py:38-41`
**Gilt für:** `clients/mail.py`

Mail hat keinen Schreibweg, also entfällt die Retry-Regel in ihrer bekannten Form. Sie
kehrt in einer anderen zurück (K5): jeder Volltextabruf öffnet eine IMAP-Sitzung, also ist
ein Loop über `message/{id}` teuer und nicht gefährlich. Der Satz gehört in den
Modul-Docstring, mit der Messung daneben (`throttle()` wird in Mail 5.11.1 nie aufgerufen,
der Brute-Force-Zähler zählt nicht).

### Automatische Registrierung, eine Datei je Familie

**Quelle:** `server/__init__.py:101-110`
**Gilt für:** `server/reg_mail.py`

Keine zentrale Liste, kein Import an anderer Stelle. Die Datei existiert, also ist das
Werkzeug registriert. Die gefrorenen Zahlen (`test_tool_surface.py`,
`acceptance_all_tools.py`, `check_tool_budget.py`) sind der Preis dafür und sind in
**demselben** Commit zu ziehen wie die Registrierung.

### Vulture-Whitelist als Durchgangsstation

**Quelle:** `vulture_whitelist.py` (Blockform am Dateiende: Kommentar, der erklärt, wer den
Namen aufruft, dann die Namen)
**Gilt für:** die neuen Namen aus `clients/mail.py` und `tools/mail.py`, solange
`reg_mail.py` noch nicht existiert

Phase-08-Muster: die Namen wandern hinein und mit der Registrierung wieder heraus. Am
Phasenende ist das Gate ohne Mail-Eintrag grün.

---

## Kein Analog gefunden

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `src/mcp_connector/tools/html_text.py` | utility | transform | Es gibt in `src/` keine HTML-zu-Text-Funktion (`10-RESEARCH.md:758-761`). Übertragbar ist nur die Modulform von `tools/marks.py` und die Fehlerhaltung von `ocs.py::_json_payload`. Die vier fachlichen Anforderungen stehen als Messwerte in `10-RESEARCH.md:775-792` und sind aus der Recherche zu übernehmen, nicht aus der Codebasis |
| `tests/integration/test_srv06_degradation.py` | test (integration) | request-response mit Neustart der Nextcloud | Kein bestehender Test schaltet eine App ab und startet die Instanz neu. `tests/integration/test_exapp_dav_matrix.py` und `test_exapp_mail_reach.py` liefern nur den Rahmen (Topologie, `-m integration`, Umgebungsvariablen). Die Neustart-Pflicht ist Falle 1 der Recherche und ohne Vorbild in diesem Repo |

Für den Store-Text gibt es zwar ein Analog für die **Form** (Marker-Tripel, Textgate), aber
keins für den **Inhalt**: die Benennung der Exfiltrationskette ist neuer Text. Die zitierbare
Quelle steht in `10-RESEARCH.md:845-852`.

---

## Metadaten

**Suchraum der Analog-Suche:** `src/mcp_connector/` (alle 80 Module), `tests/unit/`,
`tests/contract/`, `tests/integration/`, `scripts/`, `docs/spike-mail.md`,
`appinfo/`, `.planning/phases/09-talk/09-PATTERNS.md`
**Vollständig gelesene Dateien:** 13 (`clients/talk.py`, `clients/tables.py`, `clients/ocs.py`,
`tools/talk.py`, `tools/marks.py`, `tools/chatgpt.py`, `ids.py`, `paging.py`, `models.py`,
`capabilities.py`, `server/reg_talk.py`, `tests/contract/test_no_destructive_calls.py`,
`scripts/check_tool_budget.py`)
**Gezielt gelesene Abschnitte:** `tools/tables.py:1-180`, `server/__init__.py:1-120`,
`tests/unit/test_talk_client.py:1-80` und `380-430`, `tests/unit/test_contacts_tools.py:235-248`,
`tests/unit/test_ocs_capabilities.py` (spreed-Block), `tests/unit/test_exapp_env_setup.py`
(Textgate-Block), `tests/contract/test_tool_surface.py` (Talk- und Zählblöcke),
`scripts/acceptance_all_tools.py` (Talk-Block und Zahlen),
`tests/integration/test_exapp_mail_reach.py:1-45`, `docs/spike-mail.md:95-177`
**Projekt-Skills:** kein `.claude/skills/` und kein `.agents/skills/` vorhanden
**Datum der Musterextraktion:** 2026-08-24
