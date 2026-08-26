# Phase 12: Konsistenz und Härtungs-Nachzieher - Pattern Map

**Mapped:** 2026-08-25
**Files analyzed:** 14 (8 Produktion/Doku, 4 Tests geändert, 2 Tests neu)
**Analogs found:** 14 / 14 (davon 11 exakt, 3 role-match)

Diese Phase erfindet nichts. Für jede der vier Arbeitspakete existiert im Repo ein
erfolgreicher Präzedenzfall, und dieses Dokument nennt für jede Datei genau ihn plus die
Zeilen, die kopiert werden. Der wichtigste Präzedenzfall ist Commit `53ba602`
(`preview_truncated` in Mail): er hat für TOOL-17 alle vier Ebenen gleichzeitig bedient
(Projektion, Refusal-Hint, Tool-Docstring, Tests) und ist die vollständige Vorlage.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/mcp_connector/tools/talk.py` (TOOL-17, TOOL-19) | tool/projection | transform | `src/mcp_connector/tools/mail.py:489-512` | exakt (gleiche Rolle, gleicher Fix) |
| `src/mcp_connector/server/reg_talk.py` (TOOL-17) | route/registration | request-response | `src/mcp_connector/server/reg_mail.py:31-81` | exakt |
| `src/mcp_connector/tools/chatgpt.py` (TOOL-17 Verbraucher, TOOL-19 Aufrufer) | tool/adapter | transform | `src/mcp_connector/tools/chatgpt.py:621` (`talk_tools.one_message`) | exakt (Selbst-Analog im selben `_fetch_message`) |
| `src/mcp_connector/tools/mail.py` (TOOL-18) | tool/projection | transform | `src/mcp_connector/tools/notes.py:83-90` | exakt |
| `src/mcp_connector/ids.py` (TOOL-18) | utility/codec | validation | `src/mcp_connector/ids.py:119-128` (`mail`-Zweig im selben `parse`) | exakt (Selbst-Analog) |
| `src/mcp_connector/provider_map.py` (SEC-02a) | config/data map | transform | `src/mcp_connector/provider_map.py:58-72` (vier vorhandene Einträge) | exakt (Selbst-Analog) |
| `README.md`, `README.de.md`, `README.fr.md` (TOOL-19) | doc | - | `tests/unit/test_provider_map.py:287-298` (die belegte Id) | role-match (Beleg statt Vorlage) |
| `CHANGELOG.md` (TOOL-17) | doc | - | `CHANGELOG.md:66-74` (0.1.8 `### Changed`) | exakt |
| `tests/unit/test_talk_tools.py` (TOOL-17) | test | assertion | `tests/unit/test_mail_tools.py:501-547` | exakt |
| `tests/unit/test_ids.py` (TOOL-18) | test | assertion | `tests/unit/test_ids.py:182-201` (Parametrize-Ablehnungsliste) | exakt (Selbst-Analog) |
| `tests/unit/test_tools_context.py` (SEC-02b) | test/source-gate | file-I/O | `tests/unit/test_tools_context.py:1815-1829` | exakt (direkter Nachbar) |
| `tests/unit/test_exapp_env_setup.py` (SEC-02c) | test/text-gate | file-I/O | `tests/unit/test_exapp_env_setup.py:1686/1787-1789/1942` + `tests/contract/test_tool_surface.py:766` | exakt + role-match für die Dateiliste |
| `tests/contract/test_module_boundaries.py` **(neu)** | test/AST-gate | file-I/O | `tests/contract/test_no_destructive_calls.py:287-353,378-392` | exakt |
| `tests/contract/test_public_vocabulary.py` **(neu, Option 2/3)** | test/text-gate | file-I/O | `tests/contract/test_no_destructive_calls.py` (Struktur) + `test_tool_surface.py:766` (Dateiliste) | role-match |

---

## Pattern Assignments

### `src/mcp_connector/tools/talk.py` (tool/projection, transform) - TOOL-17 + TOOL-19

**Analog:** `src/mcp_connector/tools/mail.py` (TOOL-17), `src/mcp_connector/tools/talk.py::one_message` (TOOL-19)

**Kernmuster: Projektionsstelle mit Begründungskommentar** (`tools/mail.py:498-509`, Commit `53ba602`):

```python
    preview, cut = _capped(_text(raw.get("previewText") or ""))
    if preview:
        entry["preview"] = preview
        if cut:
            # ``preview_truncated`` and not ``truncated``, and the difference is the whole
            # point: one level up, ``truncated`` means "this page was cut and there may be a
            # next", and :data:`_CURSOR_HINT` tells a model exactly that sentence. The same
            # word down here meant "this preview was cut at MAX_PREVIEW_BYTES", which is a
            # second meaning a model cannot resolve, because both readings are plausible in
            # the same answer: a cut page whose first entry carries a cut preview sets both
            # keys at once (review finding IN-01).
            entry["preview_truncated"] = True
```

Zielstelle heute (`tools/talk.py:517-528`), der Kommentar fehlt vollständig:

```python
    text, cut = _capped(_resolve(raw.get("message"), raw.get("messageParameters")))
    entry: dict[str, Any] = {
        "id": raw.get("id"),
        "timestamp": _number(raw.get("timestamp")),
        "actor": _text(raw.get("actorDisplayName") or ""),
        "message": text,
    }
    if cut:
        entry["truncated"] = True
```

Der Kommentartext für Talk steht ausformuliert in `12-RESEARCH.md:372-379` (DF-11-01, gleiche
Struktur, `MAX_MESSAGE_BYTES` statt `MAX_PREVIEW_BYTES`). **Review-Nummer beachten:** in Talk
zitiert der Kommentar `DF-11-01`/`IN-01`, nicht die verschobene Requirement-Nummer.

**Docstring-Muster der Projektionsfunktion** (`tools/mail.py:475-484` nennt den Feldnamen
ausdrücklich; `tools/talk.py:513-515` nennt ihn heute noch nicht):

```python
    The truncation is a field beside the text and never a marker inside it. A marker inside
    foreign text is an attack path (ME-03), and a chat message is the cheapest place for it of
    all, because every participant of a conversation may write one.
```

**Antwortebene bleibt unverändert** (`tools/talk.py:494-496` und `:697-703`). Beide setzen
`answer["truncated"] = True` und sind die Wächter dafür, dass die Umbenennung nicht mitwandert:

```python
    if last_given is not None:
        answer["truncated"] = True
        answer["next"] = paging.encode_cursor({"o": last_given, "c": token})
```

**Refusal-Hint: Mail-Vorbild vs. Talk-Sinn.** Mail hat den Hint mitgezogen
(`tools/mail.py:89-93`):

```python
_CURSOR_HINT = (
    "Only level=messages hands out a cursor. Call mail_browse without cursor; the answer says "
    "with truncated that the page was cut (a cut preview of a single entry is a different key, "
    "preview_truncated)."
)
```

Talk heute (`tools/talk.py:107-110`) spricht über die **Konversationsliste**, nicht über die
Nachrichtenseite. Keine Pflichtänderung; falls präzisiert, den Talk-Sinn wahren (die
Konversationsliste hat kein `next`):

```python
_CURSOR_HINT = (
    "Only level=messages hands out a cursor. Call talk_browse without cursor; the conversation "
    "list says with truncated and total that it was cut."
)
```

**TOOL-19: öffentliche Funktion mit dem Aufrufer im Docstring.** Vorbild ist `one_message`
im selben Modul (`tools/talk.py:531-556`, Phase 11): öffentlich, weil `chatgpt.py` sie
braucht, Docstring nennt Rückgabe, Sicherheitsgrund und was er absichtlich nicht wiederholt:

```python
def one_message(window: list[dict[str, Any]], message_id: str) -> dict[str, Any] | None:
    """One named message out of a context window, or ``None`` if it cannot be read.
    ...
    **Never a neighbour.** The context route answers a window *around* the wanted message, so
    the entry with the closest id is a different message, and handing it over would be a wrong
    answer nobody can see (threat T-11-13). ...
    """
```

Der umzubenennende Docstring (`tools/talk.py:615-626`) trägt die halbe Mitigation von T-11-12
und T-11-14 und muss **wörtlich** mitwandern, weil `11-SECURITY.md` ihn zitiert:

```python
async def _room(clients: NcClients, token: str, *, include_last_message: bool) -> dict[str, Any]:
    """The conversation with this token out of this account's own list, or a refusal.

    Never ``GET /room/{token}`` with a token that came out of a model. That route answers an
    unknown token with a counted brute force attempt against the address of this container,
    which is one address for every user of the instance, so a model that invents tokens would
    slow Talk down for everybody and end in a 429 (threat T-09-21). The list costs the same
    single request, carries no token in its path and is the account's own data.
    """
```

Signaturform beibehalten (`include_last_message` keyword-only), damit die drei Aufrufstellen
unverändert lesbar bleiben: `tools/talk.py:291`, `tools/talk.py:481`, `tools/chatgpt.py:616`.
Eine Prosa-Nennung zieht mit: `tools/talk.py:234` ("goes through ``talk_client.get_rooms``
(in :func:`_room`)").

---

### `src/mcp_connector/server/reg_talk.py` (route/registration, request-response) - TOOL-17

**Analog:** `src/mcp_connector/server/reg_mail.py`

**Tool-Docstring-Muster** (`reg_mail.py:76-81`, der Satz, den TOOL-17 nach Talk trägt):

```python
    """List the mail accounts of this user, the mailboxes of one, or the messages of one.

    Envelopes newest first; the full text of one is a fetch("mail:<id>") away. Percent encode a
    filter value with a space or colon (subject:Rechnung%20Mai). truncated: page cut;
    preview_truncated: preview cut. Reads only: never sends, drafts, moves, flags or
    deletes."""
```

Zielstelle (`reg_talk.py:46-48`):

```python
    """List the conversations of this account, or the history of one.

    The messages level answers newest first; the next page runs further into the past."""
```

**Modul-Docstring-Absatz, der die Bytes rechtfertigt** (`reg_mail.py:31-36`). Dieser Absatz
kostet keine `tools/list`-Bytes und ist die Begründung, warum der Satz oben teuer sein darf:

```python
The docstring names both truncation keys, and that is the one sentence of it that buys itself
back: ``truncated`` is the cut **page**, ``preview_truncated`` the cut **preview** of a single
entry, and before plan 11-08 both were called ``truncated``. A model that reads the entry level
flag as a page flag pages in a circle, which costs more round trips than the fifty odd bytes
this sentence occupies; the filter line above it was compressed in the same edit so the tool
stays under its own ceiling (``MAX_TOOL_BYTES``, plan 11-07).
```

Für Talk entfällt der Nachsatz zur Gegenkompression: `talk_browse` steht bei 858 von 1400
Bytes (Messung `12-RESEARCH.md:271-277`), Mail hatte nur 24 Bytes Luft.

**Nicht anfassen:** die `cursor`-Field-Description (`reg_talk.py:40-43`) bleibt wörtlich, sie
spricht über die Antwortebene:

```python
    cursor: Annotated[
        str,
        Field(description="Next page handle from a truncated answer; only level=messages"),
    ] = "",
```

**Verifikation nach jedem Edit an dieser Datei:**
`uv run --no-sync python scripts/check_tool_budget.py` (Erwartung: `talk_browse` rund 911,
Oberfläche rund 15710, Gate 18000).

---

### `src/mcp_connector/tools/chatgpt.py` (tool/adapter, transform) - TOOL-17 + TOOL-19

**Analog:** dieselbe Funktion `_fetch_message`, zwei Zeilen weiter unten.

**TOOL-17, der Verbraucher** (`chatgpt.py:653-654`). Genau diese zwei Zeilen sind die
Pitfall-1-Stelle: `entry.get(...)` wirft nicht, der Verlust ist still:

```python
    if entry.get("truncated"):
        metadata["truncated"] = "true"
```

`metadata["truncated"]` in `:654` bleibt so, wie es ist: eine Ebene, eine Bedeutung. Nur die
gelesene Projektionsschlüssel-Seite wechselt.

**TOOL-19, der Aufrufer** (`chatgpt.py:616` heute, direkt über der bereits korrekten Zeile
`:621`, die das Zielmuster zeigt):

```python
    await capabilities.require_app(clients, talk_tools.APP)
    room = await talk_tools._room(clients, token, include_last_message=False)   # der Durchgriff
    ...
    entry = talk_tools.one_message(window, message_id)                         # das Zielmuster
```

**Importblock bleibt unverändert** (`chatgpt.py:58-74`), das Alias-Muster ist im ganzen Baum
einheitlich und ist die Grundlage der AST-Alias-Auflösung des neuen Gates:

```python
from .. import ids, provider_map
from ..nextcloud.clients import talk as talk_client
from . import mail as mail_tools
from . import talk as talk_tools
```

---

### `src/mcp_connector/tools/mail.py` (tool/projection, transform) - TOOL-18

**Analog:** `src/mcp_connector/tools/notes.py:83-90` (Projektion, deren `id` aus dem Codec kommt)

```python
        results.append(
            {
                "id": ids.encode_note(note_id),
                "title": str(entry.get("title") or ""),
                "excerpt": str(entry.get("subline") or ""),
                "url": notes_client.web_url(clients.creds, note_id),
            }
        )
```

Dasselbe Muster in `chatgpt.py:463` (`ids.encode_mail(message_id)`), `deck.py:120`,
`files.py:199`, `calendar.py:306`, `tables`/`talk` über `provider_map.py:132-156`. Der
`_ID_KIND`-Bau in `mail.py:490` ist der einzige verbliebene Handbau im ganzen Produktionsbaum.

**Zu entfernen** (`mail.py:67-70`, die einzige Stelle im Repo, die eine erledigte Planung als
Zukunft beschreibt):

```python
#: The id kind of a mail, in the spelling ``fetch`` expects. Plan 10-05 is the one that adds
#: ``ids.encode_mail`` and teaches ``ids.parse`` this kind; until then the prefix is built
#: from the separator of that module rather than from a second copy of the colon.
_ID_KIND = "mail"
```

**Zu ersetzen** (`mail.py:489-490`):

```python
    entry: dict[str, Any] = {
        "id": f"{_ID_KIND}{ids.SEPARATOR}{_number(raw.get('databaseId'))}",
```

**Import bleibt:** `mail.py:36` lautet `from .. import ids, paging`; `ids` war bisher nur für
`ids.SEPARATOR` da und wird nach dem Fix für `ids.encode_mail` gebraucht, also kein `F401`.

**Verhaltensgleichheit ist belegt** (`mail.py:440`, der Filter vor der Projektion):

```python
    entries = [_message(item) for item in raw if _number(item.get("databaseId")) > 0]
```

Kein Wert, der diesen Filter passiert, kann `_join` zum Refusal bringen, also ist die Ausgabe
byte-identisch mit heute und kein bestehender Test in `tests/unit/test_mail_tools.py` bricht.

**Erste Handlung des Tasks** (Pitfall 5, die Requirements nennen die falsche Datei):
`grep -rn "_ID_KIND" src/`

---

### `src/mcp_connector/ids.py` (utility/codec, validation) - TOOL-18

**Analog:** der `mail`-Zweig derselben `parse`-Funktion (`ids.py:119-128`). Er zeigt beide
Hälften des Musters: `fullmatch`-Refusal plus Kommentar, der sagt, warum die Prüfung **hier**
steht und nicht im Client.

```python
    elif kind == "mail":
        parts = (rest,)
        # The digit guard stands here and not only in the mail client, and that is the whole
        # difference to ``file`` and ``note``: ``mail:abc`` has to fail without a single
        # request. The full text route is the most expensive call of that family, because
        # every read of it opens an IMAP session inside the Mail app, and the app offers
        # nothing to lean on: PHP casts a non numeric id to 0 and answers 404, so there is no
        # routing error that would stop a wrong value on the way out (pitfall 11).
        if not _DIGITS.fullmatch(rest):
            raise ToolError(message=f"{raw!r} is not a valid mail id.", hint=_HINT)
```

**Zielstelle, der Frühausstieg** (`ids.py:115-116`), der den gemeinsamen Leersegment-Check in
`:161-162` überspringt:

```python
    if kind == "url":
        return "url", (rest,)
```

**Der Satz, den die Ablehnung wiederverwenden soll** (`ids.py:113`, bestehende Formulierung,
kein neuer Text):

```python
        raise ToolError(message=f"{raw!r} is not a valid resource id.", hint=_HINT)
```

**Die Spiegelseite, gegen die die Auslegung geprüft wird** (`ids.py:100-105`): `encode_url`
lehnt whitespace-only ab und akzeptiert inneres Whitespace. `parse` darf nicht strenger sein,
sonst baut der Codec einen Wert, den er selbst nicht liest (Pitfall 3):

```python
def encode_url(url: str) -> str:
    """The rest category: everything we cannot address by a stable Nextcloud id."""
    value = (url or "").strip()
    if not value:
        raise ToolError(message="Cannot build an id from an empty url.", hint=_HINT)
    return f"url{SEPARATOR}{value}"
```

Der neue Kommentar an der Stelle sagt, **warum inneres Whitespace erlaubt bleibt**, und
verweist auf `encode_url` als Spiegel.

---

### `src/mcp_connector/provider_map.py` (config/data map) - SEC-02(a)

**Analog:** die vier vorhandenen Einträge derselben Tabelle (`provider_map.py:58-72`). Format:
eine oder mehrere `#`-Zeilen direkt über dem Eintrag, Form "Verified against
nextcloud/<repo> <pfad>, class <Klasse>: <was der Code tut, das wir ausnutzen>".

```python
PROVIDER_KINDS: Mapping[str, str] = {
    "files": "file",
    "notes": "note",
    # Verified against nextcloud/deck lib/Search/DeckProvider.php. "deck" is wrong.
    "search-deck-card-board": "card",
    # Verified against nextcloud/spreed lib/Search/MessageSearch.php, class MessageSearch:
    # commentToSearchResultEntry adds conversation, messageId, threadId, actorType, actorId and
    # timestamp, and links to spreed.Page.showCall with the fragment "message_" . $id.
    "talk-message": "message",
    # Verified against nextcloud/spreed lib/Search/CurrentMessageSearch.php, class
    # CurrentMessageSearch: it extends MessageSearch and overrides getId, getName, getOrder, the
    # subline template and the room selection only. Its entries are built by the inherited
    # performSearch, so they carry exactly the same attributes. Not an assumption: read.
    "talk-message-current": "message",
    # Verified against nextcloud/tables lib/Search/SearchTablesProvider.php, class
    # SearchTablesProvider: it sets no attributes at all, and getInternalLink builds
    # "#/" . $nodeType . "/" . $nodeId with $nodeType being "table" or "view".
    "tables-search-tables": "table",
}
```

Die zwei fehlenden Kommentare gehören über `"files"` und `"notes"` (Zeilen 56-57). Die Belege
liegen fertig in `12-RESEARCH.md:172-186` und `:415-431` (beide am Release-Tag gelesen).
Wichtig ist der Anschluss an die Ableitung im eigenen Modul, denn das ist die Begründung, die
den Kommentar über eine Fußnote hinaushebt:

- `files` liefert `attributes.fileId` **und** `/f/<fileid>` in der URL, also die Doppelspur von
  `_file_id` (`provider_map.py:176-188`).
- `notes` setzt **keine** Attribute, daher liest `provider_map.py:135-138` die Id per
  `_last_numeric_segment(url)`.

Der eingefrorene Halter (`tests/unit/test_provider_map.py:287-298`) bleibt unverändert; er
begrenzt die Menge, der Kommentar trägt den Beweis.

---

### `README.md`, `README.de.md`, `README.fr.md` (doc) - TOOL-19

**Analog / Beleg:** `tests/unit/test_provider_map.py:287-298` (der Test, der die Ersatz-Id
"echt und nie registriert" belegt):

```python
def test_the_provider_table_is_not_a_list_of_installed_apps() -> None:
    """The runtime list comes from Nextcloud; this table only maps ids to kinds."""
    assert set(provider_map.PROVIDER_KINDS) == {
        "files", "notes", "search-deck-card-board",
        "talk-message", "talk-message-current", "tables-search-tables",
    }
    assert "talk-conversations" not in provider_map.PROVIDER_KINDS
```

**Zielzeile, drei Dateien, identischer Text** (`README.md:372`, `README.de.md:381`,
`README.fr.md:389`), zu ändern ist genau `"provider":"spreed"` zu
`"provider":"talk-conversations"`:

```json
{"query":"budget","count":2,"results":[{"id":"file:4711", ...},{"id":"url:https://cloud.example.org/index.php/call/abc123","title":"Khaled","url":"https://cloud.example.org/index.php/call/abc123","provider":"spreed","kind":"url","resolvable":false}], ...}
```

`"kind":"url"` und `"resolvable":false` bleiben stehen und werden mit der Änderung **wahr**
statt erfunden (belegt durch `test_a_talk_conversation_hit_stays_a_url_because_a_conversation_is_no_document`,
`tests/unit/test_provider_map.py:288`). Der URL-Teil `/index.php/call/abc123` bleibt, `abc123`
erfüllt das Token-Alphabet.

**Optionales Gate für diese Zeile** (Open Question 4, nicht von SC3 gefordert). Vorlage für den
repo-weiten Markdown-Lauf ist `tests/contract/test_tool_surface.py:752-776`:

```python
    for page in [*sorted(DOCS.glob("*.md")), README]:
        text = page.read_text(encoding="utf-8")
        ...
    assert unexplained == [], (
        "a page naming a tool count other than "
        f"{current} has to point at {holder}: " + "; ".join(unexplained)
    )
```

---

### `CHANGELOG.md` (doc) - TOOL-17

**Analog:** der 0.1.8-Eintrag zu `preview_truncated` (`CHANGELOG.md:66-74`), wörtlich die
Vorlage für den 0.1.9-Text:

```markdown
### Changed

- A change of the answer format, named here because a reader of the old key has to be
  updated: in an answer of `mail_browse` on the message level, the key `truncated` of a
  single entry is now called `preview_truncated`. The same word meant two things in the same
  answer, and only one of them was about the entry: on the answer level `truncated` says that
  the page of messages was cut and that there may be a next one, on a single entry it says
  that the preview text of that message was cut. The answer level keeps `truncated`
  unchanged, and no other tool is affected.
```

Kopfformat des Versionsblocks: `## [0.1.8] - 2026-08-25` (`CHANGELOG.md:12`), darunter ein
Absatz Prosa, dann `### Added` / `### Changed`. Kein `Unreleased`-Block im Repo, und kein Gate
hält den obersten Block gegen `mcp_connector.__version__`, ein 0.1.9-Block bricht also nichts.

---

### `tests/unit/test_talk_tools.py` (test, assertion) - TOOL-17

**Analog:** `tests/unit/test_mail_tools.py:501-547` (beide Tests des Vorbild-Commits, exakt
die zwei Tests, die Talk braucht)

**Test 1: bestehender Kappungstest wechselt den Schlüssel** (Vorbild `test_mail_tools.py:501-516`):

```python
@pytest.mark.anyio
async def test_a_preview_over_the_byte_cap_is_cut_and_says_so_beside_the_text(
    clients: NcClients,
) -> None:
    """ME-03: the cut is a field next to the text and never a marker inside it."""
    payload = [message(previewText="ü" * mail_tools.MAX_PREVIEW_BYTES)]
    ...
    entry = answer["results"][0]
    assert entry["preview_truncated"] is True
    assert "truncated" not in entry, "the entry level flag is the preview one, never the page one"
```

Zielstelle (`tests/unit/test_talk_tools.py:725-730`), Byte-Kappung bei 800 mit Umlaut an der
Grenze; `:730` (Marker-Hygiene, ME-03) bleibt unverändert:

```python
    entry = result["results"][0]
    assert entry["truncated"] is True
    assert entry["message"] == "a" * 799
    assert "�" not in entry["message"]
    assert MARKER not in entry["message"]
    assert "truncated" not in json.dumps(entry["message"])
```

**Test 2: der neue Test für den gemeinsamen Fall**, vier Behauptungen, Vorbild
`test_mail_tools.py:519-547` wörtlich in Struktur und Docstring-Stil:

```python
@pytest.mark.anyio
async def test_a_cut_page_and_a_cut_preview_are_two_keys_with_two_meanings(
    clients: NcClients,
) -> None:
    """IN-01: the case that made one word for two cuts a problem, in one single answer.
    ...
    """
    ...
    assert answer["truncated"] is True, "the page was cut"
    assert paging.decode_cursor(answer["next"]) == {"o": 1755180000, "m": str(MAILBOX_ID)}
    assert "preview_truncated" not in answer, "the page flag is never the preview one"

    cut, whole = answer["results"]
    assert cut["preview_truncated"] is True, "the preview of the first entry was cut"
    assert "next" not in cut, "a cut preview has no continuation, the full text is a fetch away"
    assert "truncated" not in cut
    assert "preview_truncated" not in whole, "an uncut preview says nothing at all"
```

Für Talk ist der Cursor-Scope `"c"` statt `"m"` (`tools/talk.py:496`:
`paging.encode_cursor({"o": last_given, "c": token})`), und `truncated`/`next` auf der
Antwortebene kommen aus der Continuation-Id des Clients, nicht aus der Anzahl.

**Wächter, die unverändert bleiben müssen** (Antwortebene wandert nicht mit):
`tests/unit/test_talk_tools.py:361`, `:530`, `:630` (`"truncated" not in result` bei 304),
`:655` (leeres Fenster mit Fortsetzung).

**Wächter in einer anderen Datei:** `tests/unit/test_chatgpt_fetch.py:1302`
(`result["metadata"]["truncated"] == "true"`) bleibt wörtlich und wird nur grün, wenn
`chatgpt.py:653` mitzieht. Rot dort bei einem Edit, der nur `talk.py` anfasst, ist das System,
das funktioniert.

---

### `tests/unit/test_ids.py` (test, assertion) - TOOL-18

**Analog:** die bestehende Parametrize-Ablehnungsliste derselben Datei (`test_ids.py:182-201`).
Der neue Negativtest gehört genau dort hinein, `"url:"` steht schon drin:

```python
@pytest.mark.parametrize(
    "raw",
    [
        "garbage", "", ":", "file:", "unknown:1", "note:", "card:",
        "card:1:2", "card:1:2:3:4", "event:personal", "url:",
    ],
)
def test_invalid_ids_raise_toolerror_with_hint(raw: str) -> None:
    with pytest.raises(ToolError) as excinfo:
        ids.parse(raw)
    assert excinfo.value.hint, "every rejection must carry an actionable hint"
```

**Der Roundtrip-Wächter der Toleranz** (`test_ids.py:176-179`), er belegt, dass inneres
Zeichenmaterial bewusst durchgelassen wird, und darf nicht rot werden:

```python
def test_url_keeps_colons_and_slashes() -> None:
    kind, parts = ids.parse("url:https://nc.test:8443/index.php/apps/deck/#/board/1")
    assert kind == "url"
    assert parts == ("https://nc.test:8443/index.php/apps/deck/#/board/1",)
```

**Muster für die Encode-Seite**, falls die strengere Lesart gewählt wird
(`test_ids.py:204-217`, `encode_url("")` steht schon in der Liste):

```python
def test_encode_rejects_empty_parts() -> None:
    for call in (
        ...
        lambda: ids.encode_url(""),
    ):
        with pytest.raises(ToolError):
            call()
```

---

### `tests/unit/test_tools_context.py` (test/source-gate, file-I/O) - SEC-02(b)

**Analog:** der direkte Nachbar `test_this_module_reads_no_content_of_its_own`
(`test_tools_context.py:1815-1829`). Gleicher Stil: Quelltext lesen, `#`-Zeilen filtern,
behaupten. Das neue Gate steht daneben.

```python
def test_this_module_reads_no_content_of_its_own() -> None:
    """Every byte of content comes through the readers that already exist and are tested."""
    source = Path(context_tools.__file__).read_text(encoding="utf-8")
    code = [line for line in source.splitlines() if not line.strip().startswith("#")]
    body = "\n".join(code)

    for own_reader in ("AsyncClient", "clients.client", "clients.creds", "ocs.", "dav.", "caldav"):
        assert own_reader not in body, f"{own_reader} would be a second content reader here"
```

Zweites Muster derselben Datei, noch schlanker (`:1807-1812`):

```python
def test_no_sentence_of_this_module_frames_foreign_text_as_a_wish_of_the_user() -> None:
    """D-57 in the source: an excerpt is a data field, never a rewritten request."""
    source = Path(context_tools.__file__).read_text(encoding="utf-8").lower()

    for framing in ("the user wants", "the user asked for", "please do", "you must"):
        assert framing not in source, f"{framing!r} would turn foreign text into an instruction"
```

**Der Verhaltenstest, dessen Quelltext-Partner das neue Gate ist** (`:1615-1645`, bleibt
unverändert):

```python
async def test_no_subject_and_no_sender_can_reach_the_bundle_through_this_leg(...) -> None:
    """T-11-29: the message level is never asked for, so foreign text has no way in here."""
    ...
    assert mail.of("messages") == [], "the level that reads messages is never called"
```

**Zuschnitt:** die gesuchte Zeichenkette ist `level="messages"`; sie kommt in `context.py`
heute nur als Prosa im Wortlaut "messages" vor (`:36`, `:43`, `:348`, `:355`, `:593`), als Code
stehen dort `level="accounts"` (`:352`) und `level="mailboxes"` (`:367`). Der einfache
`#`-Filter genügt deshalb. **Gegenprobe ist Pflicht:** Prüffunktion nimmt den Text als
Parameter, ein zweiter Test speist einen konstruierten String mit `level="messages"` und
erwartet einen Fund (Muster `_violations` unten).

---

### `tests/unit/test_exapp_env_setup.py` (test/text-gate, file-I/O) - SEC-02(c)

**Analog:** die eigene Wortliste und ihre Anwendung plus Gegenprobe, alles in derselben Datei.

**Die Konstante, die nicht dupliziert werden darf** (`:1683-1686`):

```python
#: Project vocabulary rule: this word must not appear in a public artefact of this repo,
#: and the manifest is the most public one there is. Matched case insensitively, and only
#: against element text, so the explanatory comments of the manifest cannot trip it.
FORBIDDEN_VOCABULARY = "archiv"
```

**Die Anwendungsstelle** (`:1787-1789`), heute ausschließlich auf den Element-Text von
`appinfo/info.xml`:

```python
    text = element_text_without_comments(root)
    if FORBIDDEN_VOCABULARY in text.casefold():
        problems.append(f"the manifest text carries the forbidden word {FORBIDDEN_VOCABULARY!r}")
```

**Die Gegenprobe, die als Vorlage für die neue dient** (`:1942-1950`):

```python
def test_the_text_gate_rejects_the_forbidden_vocabulary(manifest_root: etree._Element) -> None:
    """The project vocabulary rule, on the most public artefact of the repository."""
    for element in manifest_root.findall("description"):
        if element.get("lang") is None:
            element.text = "First paragraph.\n\nThe Archive of your data stays untouched.\n"

    problems = description_problems(manifest_root)

    assert any("forbidden word" in problem for problem in problems)
```

**Die Gegenproben-Regel des Hauses, wörtlich** (`:1667-1672`) - sie gilt für alle drei neuen
Gates dieser Phase:

```python
# The public text of the manifest (plan 05-09)
#
# Two gates, both written as a function over the parsed root for the reason the module
# docstring gives: a gate nobody has seen fail is not a gate, so each one has a counter
# probe below that feeds it a manipulated manifest.
```

**Die Dateiliste für die Ausweitung** kommt aus `tests/contract/test_tool_surface.py:766`:

```python
    for page in [*sorted(DOCS.glob("*.md")), README]:
```

Für SEC-02(c) sind mindestens die drei READMEs und `CHANGELOG.md` gefordert; alle vier sind
heute sauber, die einzige Datei mit dem Wort ist `docs/store-submission.md` (zehn Zeilen).
**Die Ausnahme wird prüfbar gemacht** über eine positive Behauptung darüber, was ins
Store-Archiv reist (`scripts/build_store_release.sh:44` kopiert `appinfo/info.xml`,
`CHANGELOG.md`, `LICENSE`, `README.md`), plus die Begründung im Docstring des Gates
(interne Release-Doku, datierte Protokollzeilen `:124`/`:125`, fremder Klassenname `:281`).

**Nicht-leer-Behauptung als zweite Gegenprobe** (Muster `_source_files`,
`test_no_destructive_calls.py:287-290`), sonst schützt ein Tippfehler im Pfad nichts:

```python
def _source_files() -> list[Path]:
    files = sorted(SRC.rglob("*.py"))
    assert files, f"no production sources found under {SRC}"
    return files
```

---

### `tests/contract/test_module_boundaries.py` (test/AST-gate, file-I/O) **NEU** - TOOL-19

**Analog:** `tests/contract/test_no_destructive_calls.py` (vollständig: Aufbau, Filter,
Fundformat, Gegenprobe). Neue Datei in `tests/contract/`, weil CI dort ohne neuen Schritt
läuft (`.github/workflows/ci.yml:36`: `uv run pytest tests/unit tests/contract`).

**Imports und Wurzelkonstante** (`test_no_destructive_calls.py:22-30`):

```python
import ast
import io
import tokenize
from collections.abc import Iterable
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "mcp_connector"
```

**Der Filter, der zwingend übernommen wird** (`:293-320`). Ohne ihn wird das Gate rot wegen
Prosa in `context.py` (`:340`, `:355`, `:394`, `:605`), und die naheliegende Reparatur wäre,
die erklärenden Sätze zu löschen:

```python
def _code_lines(path: Path) -> list[tuple[int, str]]:
    """Return the source lines with comments and docstrings blanked out.

    Only these two are removed. A string literal that is not a docstring stays, because a
    destructive call is written as a string: ``client.request("DELETE", url)``.
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    blanked = list(lines)

    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if ast.get_docstring(node, clean=False) is None:
            continue
        first = node.body[0]
        end = first.end_lineno or first.lineno
        for lineno in range(first.lineno, end + 1):
            blanked[lineno - 1] = ""

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        lineno, col = token.start
        blanked[lineno - 1] = blanked[lineno - 1][:col]

    return [(number, text) for number, text in enumerate(blanked, start=1) if text.strip()]
```

**Die geteilte Prüffunktion plus Gate** (`:323-353`). Entscheidend ist der Docstring-Satz: die
Gegenprobe benutzt dieselbe Funktion, sonst beweist sie etwas über sich selbst:

```python
def _violations(relative: str, lines: Iterable[tuple[int, str]]) -> list[str]:
    """Every finding in already filtered lines, in the form the failure message prints.

    Shared by the gate and by its counter proofs on purpose: a counter proof that
    reimplements the check proves something about the counter proof.
    """
    findings: list[str] = []
    for number, text in lines:
        ...
            findings.append(f"{relative}:{number}: {needle!r} ({why}): {text.strip()}")
    return findings


def test_the_production_code_contains_no_destructive_request() -> None:
    """TOOL-09: the promise holds in the code, not only in the README."""
    findings: list[str] = []
    for path in _source_files():
        relative = path.relative_to(SRC).as_posix()
        findings.extend(_violations(relative, _code_lines(path)))

    assert findings == [], "destructive call found:\n" + "\n".join(findings)
```

**Die Gegenprobe** (`:378-392`), Vorlage für die konstruierte Quelle mit `talk_tools._room(...)`:

```python
def test_the_gate_would_notice_a_destructive_call_in_real_code() -> None:
    """Counter proof: the filter removes prose, and only prose.

    Without this test the previous one could be green because the filter eats everything.
    ``clients/dav.py`` is the honest fixture for it: its module docstring names all four
    verbs, and it must still be reported when the same word appears in an actual request.
    """
    dav = SRC / "nextcloud" / "clients" / "dav.py"
    docstring_text = "\n".join(text for _, text in _code_lines(dav))
    assert "no DELETE, no MOVE, no COPY" not in docstring_text, (
        "the filter must remove the module docstring of dav.py"
    )
```

**Der Modul-Docstring-Stil** (`:1-20`), inklusive der Warnung, die für dieses Gate wörtlich gilt:

```python
"""The security promise of the README, enforced by a gate instead of by discipline.
...
*   **Comments and docstrings are removed before counting.** ``clients/dav.py`` explains in
    its module docstring that it implements no DELETE, no MOVE, no COPY and no PROPPATCH.
    A naive grep would fail on that sentence, and the usual repair is to delete the
    sentence, which trades documentation for a green check. ...
*   **Every finding names file and line**, so a violation is a one line fix and never a
    hunt through the tree.
"""
```

**Zuschnitt der Regel** (Research, Pattern 2): über `src/mcp_connector/tools/*.py` laufen,
`ast.Attribute`-Knoten sammeln, deren `attr` mit `_` beginnt und deren `value` ein `ast.Name`
ist, der über die `Import`/`ImportFrom`-Knoten derselben Datei auf ein anderes Modul aus
`tools/` zeigt. Das Alias-Muster ist im Baum einheitlich (`chatgpt.py:67-74`):
`from . import talk as talk_tools`, `mail as mail_tools`, `tables as tables_tools`.
`self._x` und modul-interne `_helper()` werden nicht getroffen, weil sie keine `Attribute` auf
einem Modul-Alias sind.

**Bestandsaufnahme statt Vermutung** (Don't Hand-Roll): `uv run --no-sync ruff check
--select SLF src/` liefert drei Treffer, davon zwei legitime im selben Modul
(`oauth/provider.py:554`, `:1544`) und den einen echten (`tools/chatgpt.py:616`). Diese
Messung gehört als Begründung in den Plan, die Lint-Regel selbst nicht (sie kostet zwei
`noqa` plus `per-file-ignores` für `tests/**` mit 53 legitimen Treffern).

---

### `tests/contract/test_public_vocabulary.py` (test/text-gate, file-I/O) **NEU, nur Option 2/3** - SEC-02(c)

**Analog:** Struktur von `tests/contract/test_no_destructive_calls.py` (Konstante oben,
geteilte Prüffunktion, Gate, Gegenprobe), Dateiliste von
`tests/contract/test_tool_surface.py:31-32` und `:766`:

```python
README = Path(__file__).resolve().parents[2] / "README.md"
DOCS = Path(__file__).resolve().parents[2] / "docs"
...
    for page in [*sorted(DOCS.glob("*.md")), README]:
```

**Bedingung, unter der diese Datei entsteht:** nur, wenn die Wortliste komplett hierher zieht
und `test_exapp_env_setup.py` sie per Docstring-Verweis abgibt (Option 3 der Recherche). Zwei
Stellen mit `"archiv"` sind zwei Wahrheiten und genau der IN-03-Fehler, den das Projekt
schriftlich benannt hat. Wenn die Wortliste in `test_exapp_env_setup.py` bleibt (Option 1),
entfällt diese Datei.

---

## Shared Patterns

### Kommentar als Beleg an der Änderungsstelle
**Source:** `src/mcp_connector/tools/mail.py:502-508`, `src/mcp_connector/ids.py:121-126`,
`src/mcp_connector/provider_map.py:60-72`, `src/mcp_connector/tools/talk.py:639-648`
**Apply to:** jede Produktionsänderung dieser Phase
Der Kommentar erklärt nicht, *was* geändert wurde, sondern *warum die alte Form nicht auflösbar
war*, und nennt die Befundnummer. `talk.py:639-648` zeigt zusätzlich den Fall, in dem der
Kommentar bewusst kein Docstring ist, weil ein Test das Modul greppt:

```python
# ... It is named here and not in the docstring because a test of this plan greps the
# module for the wrong name outside of comments.
```

### Gate plus Gegenprobe
**Source:** `tests/unit/test_exapp_env_setup.py:1667-1672` (die Regel),
`tests/contract/test_no_destructive_calls.py:323-328` (die geteilte Funktion),
`:378-392` (die Gegenprobe), `:287-290` (die Nicht-leer-Behauptung)
**Apply to:** alle drei neuen Gates (Privat-Durchgriff, T-11-29-Quelltext, Vokabular-Reichweite)
Prüffunktion nimmt Text oder Pfad als Parameter, damit ein Test sie mit manipuliertem Material
speisen kann. Ein Gate, das nie rot war, ist kein Gate.

### Refusal mit Satz und nächstem Schritt
**Source:** `src/mcp_connector/ids.py:35-39` (`_HINT`), `:113`,
`src/mcp_connector/tools/talk.py:633-636`
**Apply to:** `ids.parse`-Erweiterung (TOOL-18)
Bestehende Meldung und bestehenden `_HINT` wiederverwenden, keinen neuen Satz erfinden:

```python
    raise ToolError(
        message=f"The token {token!r} is not in the conversation list of this account.",
        hint=_CONVERSATION_HINT,
    )
```

### Eine Bedeutung je Schlüssel, eine Wahrheit je Regel
**Source:** `src/mcp_connector/server/reg_mail.py:31-36` (die Begründung),
`CHANGELOG.md:66-74` (die nutzersichtbare Seite)
**Apply to:** TOOL-17 komplett, und als Prüffrage auf jedes Artefakt dieser Phase
Nach dieser Phase existiert im Repo kein Modul, das dasselbe Wort auf zwei Ebenen benutzt
(belegt per `grep -rn '\["truncated"\]\|"truncated":' src/mcp_connector/`), und keine Regel,
deren Wortliste an zwei Stellen steht.

### Byte-Messung statt Schätzung
**Source:** `scripts/check_tool_budget.py`, Messung `12-RESEARCH.md:258-279`
**Apply to:** jeden Plan, der `server/reg_talk.py` anfasst
Nur der Tool-Docstring in `reg_*.py` und `Field(description=...)` reisen in `tools/list`.
Modul-Docstrings, Kommentare, `_CURSOR_HINT` und alles in `tests/` kosten null Bytes.
`BUDGET_BYTES` 18000 und `MAX_TOOL_BYTES` 1400 bleiben unangetastet (SC5).

---

## No Analog Found

Keine. Alle 14 Dateien haben im Repo einen Präzedenzfall; der schwächste Match ist die
README-Zeile, für die es keine Vorlage-Zeile, aber einen belegenden Test gibt.

Ein Grenzfall, den der Planner kennen sollte: die **Alias-Auflösung** im neuen AST-Gate hat
kein Vorbild im Repo (`test_no_destructive_calls.py` sucht Zeichenketten, nicht Knoten).
Das Filtermuster (`_code_lines`) ist übernehmbar, die Knotenanalyse darüber ist neu. Der
Zuschnitt steht in `12-RESEARCH.md:238`, die Gegenprobe mit einer konstruierten Quelle ist
deshalb hier nicht optional, sondern der einzige Beweis, dass die Auflösung greift.

---

## Metadata

**Analog search scope:** `src/mcp_connector/` (tools, server, oauth, nextcloud, Wurzelmodule),
`tests/unit/`, `tests/contract/`, `scripts/`, `README*.md`, `CHANGELOG.md`, `docs/`
**Files scanned:** 16 gelesen (targeted ranges), 4 per Grep über den ganzen Baum ausgewertet
**Pattern extraction date:** 2026-08-25
**Repo-Stand:** HEAD `4323e16`
