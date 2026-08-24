---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 02
subsystem: api
tags: [talk, spreed, ocs, client, respx, 304, path-guard]

# Dependency graph
requires:
  - phase: 09-talk
    provides: "CHAT_PREFIX, MAX_MESSAGES, _path_token, _as_list, _last_given und der lokale 304-Sonderfall in get_messages als wörtliche Vorlage"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 01
    provides: "message:<token>:<messageId> als Id-Form, die genau diese zwei Pfadsegmente liefert"
provides:
  - "talk.get_message_context(client, creds, token, message_id, *, limit) -> list[dict[str, Any]]: der einzige Leseweg für genau eine Talk-Nachricht"
  - "talk._path_message_id: ASCII-Ziffernwächter für das zweite Pfadsegment, vor dem Request"
  - "talk._MESSAGE_ID: das Ziffern-Muster [0-9]{1,19} als Konstante"
  - "die Rückgabeform im 304-Fall: [] (leere Liste, kein Tupel, kein Fehler)"
  - "CONTEXT_URL als drittes eingefrorenes URL-Literal in tests/unit/test_talk_client.py"
affects: [11-03 (fetch-Zweig für message:<token>:<messageId> setzt auf dieser Funktion auf), 11-06 (misst die Nebenwirkungsfreiheit über die Konversationsliste)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Pfadwächter für zwei Pfadsegmente, beide vor dem Request, beide mit Routen-Zählung 0 im Test"
    - "Begründete Auslassung: ein Name, der nicht im Code steht, steht im Docstring samt Beleg, und ein Test prüft seine Abwesenheit im Querystring"
    - "Geparkter Aufrufer: eine Client-Funktion eine Welle vor ihrem Aufrufer bekommt einen Whitelist-Eintrag mit Auflösungsplan (wie Tables 08-02, Talk 09-01, Mail 10-02)"

key-files:
  created: []
  modified:
    - src/mcp_connector/nextcloud/clients/talk.py
    - tests/unit/test_talk_client.py
    - vulture_whitelist.py

key-decisions:
  - "Die Kontextroute statt lastKnownMessageId-Arithmetik: GET /apps/spreed/api/v1/chat/{token}/{messageId}/context liefert die Zielnachricht mit (getHistory mit includeLastKnown=true in v24.0.4), die Arithmetik würde bei gelöschter oder gefilterter Zielnachricht eine Nachbarnachricht ausgeben, ohne dass es jemand sieht"
  - "READ_ONLY_PARAMS wird bewusst nicht gesetzt, weil die Route sie nicht annimmt; die Begründung mit drei Belegen aus spreed 24.0.4 (waitForNewMessages mit Timeout 0, markNotificationsAsRead false, kein updateLastReadMessage) steht im Docstring und ein Test prüft ihre Abwesenheit im Querystring"
  - "Der Modul-Docstring sagt jetzt ausdrücklich, dass der READ_ONLY_PARAMS-Absatz die Historien-Route beschreibt und nicht jede Route der Datei"
  - "message_id bekommt einen eigenen ASCII-Ziffernwächter im Client, obwohl ids.parse schon prüft: der Client ist die Stelle, an der eine Id zur URL wird, und ein künftiger Aufrufer ohne Codec erbt die Prüfung nicht"
  - "Die Auswahl der Zielnachricht aus dem Fenster ist ausdrücklich Aufgabe des Aufrufers (11-03) und nicht dieser Funktion: der Client bleibt dumm, die Entscheidung liegt an einer Stelle"
  - "limit=1 ist die richtige Wahl für einen Einzelabruf: spreed hebt den Historienteil auf max(1, limit) und gibt dem Zukunftsteil dasselbe limit, also Zielnachricht plus höchstens eine neuere"
  - "get_message_context wird für eine Welle im vulture_whitelist geparkt statt den Aufrufer aus 11-03 vorzuziehen (Abweichung zum Akzeptanzkriterium, siehe unten)"

patterns-established:
  - "Ziffernwächter im Talk-Client (_path_message_id) nach dem Muster von notes._path_id und deck, mit ASCII-Regex statt str.isdigit"
  - "Gegenprobe zur begründeten Auslassung: ein Test behauptet die Abwesenheit aller vier Leseparameter im Querystring der neuen Route"

requirements-completed: []  # TOOL-16 bleibt offen: dieser Plan liefert den Leseweg, der fetch-Zweig folgt in 11-03

# Metrics
duration: 22min
completed: 2026-08-24
---

# Phase 11 Plan 02: Die Kontextroute für genau eine Talk-Nachricht Summary

**Genau eine Talk-Nachricht ist jetzt adressierbar, ohne eine Nachbarnachricht zu raten: `get_message_context` liest `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}/{messageId}/context`, die einzige Route in spreed, die die gesuchte Nachricht selbst mitliefert, und 21 Testfälle nageln sie an jeder Stelle fest, an der sie falsch sein könnte.**

## Was gebaut wurde

### Die Funktion, vollständige Signatur

```python
async def get_message_context(
    client: httpx.AsyncClient,
    creds: Credentials,
    token: str,
    message_id: str | int,
    *,
    limit: int,
) -> list[dict[str, Any]]:
```

`limit` ist keyword-only und hat keinen Default, wie bei `get_messages` und `get_rooms`. `message_id` nimmt `str | int`, weil der Wächter ohnehin über `str(value).strip()` läuft und ein direkter Aufruf mit einer Zahl damit nicht künstlich scheitert; `ids.parse` liefert einen String.

Der Körper in fünf Zeilen: `_path_token(token)`, `_path_message_id(message_id)`, `ocs.ocs_get` auf `f"{CHAT_PREFIX}/{conversation}/{message}/context"` mit `params={"limit": min(max(int(limit), 1), MAX_MESSAGES)}`, der lokale 304-Sonderfall, dann `ocs.parse_ocs(response, what=f"the context of message {message}")` und `_as_list(payload, what="messages")`.

### Das gewählte `limit` für einen Einzelabruf, mit Begründung

**`limit=1`** ist der Wert, den Plan 11-03 setzen soll. spreed rechnet in v24.0.4 so: `$limit = min(100, max(0, $limit))`, `$historyLimit = max(1, $limit)` für die Historie, und derselbe `$limit` geht an `waitForNewMessages` für den Zukunftsteil. Bei `limit=1` kommt also die Zielnachricht (weil `getHistory` mit `includeLastKnown = true` läuft) plus höchstens **eine** neuere Nachricht zurück. Ein größeres `limit` kostet nur Payload und ändert nichts an der Sicherheit, mit der die Zielnachricht enthalten ist. Die Kappung nach oben liegt bei `MAX_MESSAGES = 50`, nach unten bei 1, gemessen im Test mit `limit=999` (erreicht die Route als `50`) und `limit=0` (als `1`).

Die **Auswahl** der Zielnachricht aus dem Fenster ist ausdrücklich nicht Aufgabe dieser Funktion. Der Leser in `tools/chatgpt.py` filtert auf die `id` und lehnt ab, wenn sie fehlt; das steht so im Docstring, damit die Entscheidung an einer Stelle bleibt.

### Die Rückgabeform im 304-Fall

`[]`, eine leere Liste, und ausdrücklich **kein** Tupel (anders als `get_messages`, das `([], None)` gibt, weil es einen Cursor führt) und **kein** Fehler. Der Sonderfall steht vor `ocs.parse_ocs`, weil der geteilte Parser jedes 3xx in "Nextcloud answered the request for ... with a redirect" plus `config.REDIRECT_HINT` verwandelt und den Leser damit hinter ein Konfigurationsproblem schickte, das es nicht gibt. Der Test hängt dafür einen `parse_ocs` ein, der beim Aufruf `AssertionError` wirft: den Parser überhaupt zu erreichen wäre schon der Fehler.

Für Plan 11-03 heißt das: eine leere Liste bedeutet "die Nachricht ist in diesem Fenster nicht (mehr) enthalten" und muss mit einem Satz abgelehnt werden, nicht als leerer Erfolg weitergegeben (dasselbe Muster wie `_fetch_event` bei einem Kalenderobjekt ohne Termin).

### Der Wortlaut der Ablehnungssätze

| Fall | `message` | `hint` |
|------|-----------|--------|
| Token nicht im Muster `[a-z0-9]{4,30}` (unverändert aus Phase 9) | `{value!r} is not a Talk conversation token.` | `Use a token exactly as talk_browse reports it; a Talk token is 4 to 30 lower case letters and digits.` |
| `message_id` nicht `[0-9]{1,19}` (neu) | `{value!r} is not a Talk message id.` | `Use an id exactly as a search tool reports it, for example message:abcd1234:4711; a Talk message id is a positive number.` |
| Antwortform passt nicht (geteilter Helfer) | `Nextcloud answered with something that is not a list of messages.` | `Check that the Talk app is enabled and up to date on that instance.` |
| 403 auf der Route (geteilter Parser) | `No permission for the context of message 5103.` | `Ask the owner in Nextcloud for the missing permission.` |
| 404 auf der Route (geteilter Parser) | `Nextcloud did not find the context of message 5103.` | `Search for it first; the id or the name is unknown to this instance.` |

Der 404-Satz ist der Fall, den `#[RequireParticipant]` in spreed aus der Middleware wirft, also auch der Fall "diese Konversation gehört mir nicht" (T-11-12, transferiert an den Leser in 11-03).

### Die Nebenwirkungsfreiheit, wie sie hier belegt ist

`READ_ONLY_PARAMS` steht **nicht** im ausführbaren Teil der Funktion, weil die Route die vier Parameter nicht annimmt. Der Docstring nennt die drei Belege aus dem Quellcode von spreed 24.0.4: `waitForNewMessages` mit Timeout 0 (kein Long-Poll), `markNotificationsAsRead: false`, und kein `updateLastReadMessage`, also kein Lesemarker. Der Modul-Docstring sagt jetzt zusätzlich, dass der `READ_ONLY_PARAMS`-Absatz eine Aussage über die Historien-Route ist und nicht über jede Route der Datei.

Die **Messung** dieser Eigenschaft gehört zu Plan 11-06 und läuft über die **Konversationsliste** (`unread`, `unread_mention`, `lastReadMessage`) vor und nach einem Aufruf, nie über die Kontextroute selbst: eine Route kann nicht über sich selbst aussagen.

### Die Testabdeckung

11 Testfunktionen, 21 Testfälle, alle in `tests/unit/test_talk_client.py`, Block am Dateiende:

| Fall | Behauptung |
|------|-----------|
| Volles Fenster | drei Nachrichten in Antwortreihenfolge, die Zielnachricht 5103 ist dabei (Beleg für `includeLastKnown`), Request beginnt mit `CONTEXT_URL` |
| 304 | leere Liste, und `parse_ocs` wird nie erreicht (monkeypatch wirft) |
| Form passt nicht | `data` als Objekt und `data` als String, beide `ToolError` mit "not a list of messages" |
| Eintrag passt nicht | ein String neben einer Nachricht: der String fällt weg, die Nachricht bleibt (dokumentiert, siehe Abweichung 1) |
| Token abgelehnt | `ABC`, `abc`, `ab cd`, `../../etc`, leer: je `route.call_count == 0` |
| Nachrichten-Id abgelehnt | `abc`, `-1`, leer, `4711abc`, `٤٧` (arabisch-indisch): je `route.call_count == 0` |
| Querystring | `limit` ist drin, `noStatusUpdate`, `lookIntoFuture`, `setReadMarker`, `markNotificationsAsRead` und `lastKnownMessageId` sind nicht drin |
| Kappung | `limit=999` erreicht die Route als `50`, `limit=0` als `1`, plus `MAX_MESSAGES == 50` |
| Ein Request | `route.call_count == 1` |
| 403 | `ToolError` mit "No permission", keine leere Liste |
| Signatur | `limit` ist keyword-only ohne Default |

Das eingefrorene URL-Literal `CONTEXT_URL = f"{CHAT_URL}/{MESSAGE_ID}/context"` ist von `CHAT_URL` abgeleitet, also von der v1-Chat-Route: ein Versionswechsel der Route ist damit eine bewusste Änderung an dieser Zeile.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-Annahme korrigiert] Eine Liste mit einem String darin ist kein `ToolError`**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt für Fall 3 zwei `ToolError`-Belege, davon einen für "`data` ist eine Liste mit einem String darin". Der geteilte Helfer `_as_list` **filtert** nicht-Objekte still heraus (`[item for item in payload if isinstance(item, dict)]`), und das ist in fünf Clients dieses Projekts identisch so (talk, mail, tables, deck, ocs). Ein strengerer `_as_list` in `talk.py` hätte gleichzeitig `get_rooms` und `get_messages` verändert und wäre von den vier Nachbarclients abgewichen.
- **Fix:** Die zwei geforderten `ToolError`-Belege sind zwei unpassende **Payload**-Formen (`data` als Objekt und `data` als String), beide mit "not a list of messages" im Satz, wie das Akzeptanzkriterium es verlangt. Zusätzlich ein eigener Test, der das Filterverhalten für einen unlesbaren Eintrag ausdrücklich dokumentiert, samt der Begründung, warum daraus kein leerer Erfolg beim Modell wird: der Leser in 11-03 filtert auf die `id` und lehnt ab, wenn sie fehlt.
- **Files modified:** tests/unit/test_talk_client.py
- **Commit:** d6a78cf

**2. [Rule 3 - Blockierendes Gate] `vulture` meldet `get_message_context` als tote Funktion**

- **Found during:** Task 2, Verifikation
- **Issue:** `uv run vulture src/mcp_connector vulture_whitelist.py` endete mit Exit-Code 3: `unused function 'get_message_context' (60% confidence)`. Vulture liest nur `src` und die Whitelist, nie die Tests, und der Produktions-Aufrufer (der `fetch`-Zweig) kommt planmäßig erst in 11-03. Das Akzeptanzkriterium des Plans lautete "grün, ohne neuen Whitelist-Eintrag"; beides gleichzeitig ist ohne Vorziehen von Plan 11-03 nicht erreichbar.
- **Fix:** Ein geparkter Whitelist-Eintrag im etablierten Muster dieses Projekts (Tables 08-02, Talk 09-01, Mail 10-02: Transport plus Tests in einem Stück, Aufrufer eine Welle später), mit Begründung, Testverweis und der ausdrücklichen Auflösung: "Plan 11-03 adds the fetch branch that calls it and takes this entry out again." Die Alternative, den `fetch`-Zweig hier vorzuziehen, hätte den Schnitt von 11-03 aufgelöst.
- **Files modified:** vulture_whitelist.py (12 Zeilen, eine davon der Name)
- **Commit:** d6a78cf
- **Folge für 11-03:** Der Eintrag muss dort wieder entfernt werden, sonst wird die Whitelist unwahr.

**3. [Rule 3 - Verifikationsskript] `ROOM_PREFIX` darf im Funktionskörper nicht vorkommen, auch nicht im Docstring**

- **Found during:** Task 1, Verifikation
- **Issue:** Der Docstring benannte `:data:`ROOM_PREFIX`` als das, woran die Route **nicht** hängt. Das Prüfskript des Plans schneidet die Datei an `async def get_message_context` und verlangt `'ROOM_PREFIX' not in body`, also fiel die Prüfung über eine Formulierung, die inhaltlich richtig war.
- **Fix:** Umformuliert auf "and never on the version 4 conversation prefix above it", die Aussage bleibt, der Konstantenname verschwindet aus dem Körper.
- **Files modified:** src/mcp_connector/nextcloud/clients/talk.py
- **Commit:** 3ec998d

### Nicht abgewichen

- Kein `uv add`, kein `pip install`, kein `npm install`: `pyproject.toml` und `uv.lock` sind unangetastet (T-11-SC).
- Keine neue Route außer der einen, kein zweites Modul, keine Änderung an `get_messages`, `get_rooms` oder `send_message`.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün (196 Dateien) |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run pytest -q` | Exit 0 |
| `uv run pytest tests/unit/test_talk_client.py -q` | Exit 0, 46 Testfälle (vorher 25) |
| `uv run pytest tests/contract -q` | Exit 0, kein Werkzeug und kein Schema geändert |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | Exit 0 |
| `uv run vulture src scripts vulture_whitelist.py` (CI-Form) | Exit 0 |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15736 Bytes, **21 Tools**, Budget 18500 (unverändert) |
| Vertragsskript aus Task 1 | "context route wired" |
| Vertragsskript aus Task 2 | "context route tests present 11" |
| `git diff --stat` | `talk.py` (+87), `test_talk_client.py` (+250), `vulture_whitelist.py` (+12, Abweichung 2) |

## Für die Folgeplane

**11-03 (`fetch`-Zweig für `message:<token>:<messageId>`):**
- `await talk_client.get_message_context(clients.client, clients.creds, token, message_id, limit=1)`
- App-Gate zuerst (`capabilities.require_app(clients, talk_tools.APP)`), wie `_fetch_mail`.
- Rückgabe ist eine Liste. Auf `str(entry.get("id")) == message_id` filtern und bei Fehlen mit einem Satz ablehnen, nicht leer antworten. Eine leere Liste (304) ist derselbe Fall.
- Den Whitelist-Eintrag `get_message_context` wieder entfernen.

**11-06 (Messung):** Nebenwirkungsfreiheit vor und nach dem Aufruf über die Konversationsliste messen (`unread`, `unread_mention`, `lastReadMessage`), nicht über die Kontextroute.
