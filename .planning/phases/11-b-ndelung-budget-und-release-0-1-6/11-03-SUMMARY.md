---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 03
subsystem: api
tags: [chatgpt, fetch, talk, tables, marks, respx, metadata, output-schema]

# Dependency graph
requires:
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 01
    provides: "ids.encode_message, ids.encode_table und die Kinds message/table in ids.parse"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 02
    provides: "talk.get_message_context als einziger Leseweg für genau eine Nachricht, Rückgabe [] im 304-Fall"
  - phase: 09-talk
    provides: "talk_tools._room (Token gegen die eigene Liste), _message, _resolve, _capped, KEPT_TYPES, MAX_MESSAGE_BYTES"
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "tables_client.get_table (title plus rowsCount in einem Request), get_rows_simple, web_url"
  - phase: 10-mail
    provides: "_fetch_mail als Vorlage: App-Gate erste Zeile, Filter-dann-Kappen-dann-Markieren, FINAL_TRUNCATION"
provides:
  - "chatgpt._fetch_message: fetch(\"message:<token>:<messageId>\") liefert den Text genau dieser Talk-Nachricht"
  - "chatgpt._fetch_table: fetch(\"table:<tableId>\") liefert Titel, Zeilenzahl und die ersten Zeilen"
  - "chatgpt.MESSAGE_CONTEXT_LIMIT = 1, chatgpt.TABLE_ROWS = 20, chatgpt.MAX_TABLE_BYTES = 4096"
  - "talk_tools.one_message(window, message_id): genau eine Nachricht aus einem Kontextfenster oder None"
  - "tables_tools.as_text(title, rows, total): eine Tabelle als Zeilenliste, jede Zelle marker-gefiltert"
  - "23 neue Unit-Testfälle in tests/unit/test_chatgpt_fetch.py (38 -> 61)"
affects:
  - "11-04/11-05 (Bündel): prepare_context weist dieselben Treffer noch als resolvable false aus, Pitfall 1 der Recherche"
  - "11-06 (Live-Messung): misst Nebenwirkungsfreiheit und die beiden neuen fetch-Zweige gegen eine echte Instanz"
  - "11-08 (Doku): die Zahl der auflösbaren Id-Arten steigt von sechs auf acht, in drei READMEs"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fenster statt Objekt: der Aufrufer filtert auf die Id und lehnt bei Fehlen ab, der Client bleibt dumm"
    - "Zwei Ablehnungsgründe, eine Rückgabe (None): den Satz wählt der Aufrufer, weil nur er weiß, was er dem Modell sagt"
    - "Setzung statt Messung: TABLE_ROWS und MAX_TABLE_BYTES tragen ihre Begründung im #:-Kommentar"
    - "Kein zweiter Kappungsmarker: eine bei MAX_MESSAGE_BYTES geschnittene Nachricht sagt es in metadata, nicht im Text"

key-files:
  created: []
  modified:
    - src/mcp_connector/tools/chatgpt.py
    - src/mcp_connector/tools/talk.py
    - src/mcp_connector/tools/tables.py
    - tests/unit/test_chatgpt_fetch.py
    - vulture_whitelist.py

key-decisions:
  - "MESSAGE_CONTEXT_LIMIT = 1 als benannte Modulkonstante statt einer nackten 1 am Aufruf: die Begründung (spreed hebt den Historienteil auf max(1, limit) und liefert die Zielnachricht mit) gehört an die Zahl"
  - "TABLE_ROWS = 20, ausdrücklich eine Setzung: unter dem DEFAULT_LIMIT 25 von tables_browse, weil dies ein Auszug neben einer Gesamtzahl ist und keine Seite eines Laufs"
  - "MAX_TABLE_BYTES = 4096, ein Achtel von MAX_MAIL_BYTES: ein Brief wird von vorn bis hinten gelesen, ein Tabellenauszug soll sagen, was in der Tabelle steht"
  - "Der Nachrichten-Zweig hängt keinen zweiten Marker an; die Kappung von talk_tools._capped erscheint als metadata[truncated] = true (Entscheidung Phase 9, ME-03)"
  - "Der Autor steht als erste Textzeile (From: <actor>) und zusätzlich in metadata: eine Chatnachricht ohne ihren Verfasser ist kaum lesbar, und anders als die Vertrauens-Signale einer Mail ist der Autor Inhalt der Konversation und kein Urteil dieses Servers"
  - "title ist der Anzeigename der Konversation beziehungsweise der Tabellentitel, nie der Nachrichten- oder Zelltext: ein Titel wird wie eine Zusammenfassung dieses Servers gelesen"
  - "_table_total fällt auf die gerade gelesene Zeilenzahl zurück, wenn die App keine brauchbare rowsCount liefert oder eine unter dem Fenster: tools/tables.py lässt das Feld weg, hier ist die Zahl Teil des Satzes und darf nicht fehlen"
  - "as_text rendert die Kopfzeile wie jede andere Zeile: die Spaltentitel kommen als erste Liste von get_rows_simple mit, ein zweiter Spaltenabruf wäre eine Runde für vorhandene Information"
  - "TOOL-16 bleibt Pending: die Auflösung steht, aber prepare_context weist dieselben Treffer noch als unauflösbar aus (Pitfall 1) und die Live-Messung gehört zu 11-06"

patterns-established:
  - "one_message: eine öffentliche Projektion für den Aufrufer, die die Filterschritte des Nachbarn erbt statt sie zu kopieren"
  - "Der Whitelist-Eintrag einer geparkten Client-Funktion wird von dem Plan entfernt, der sie aufruft (Tables 08-03, Talk 09-03, Mail 10-05, hier 11-03)"

requirements-completed: []  # TOOL-16 bleibt offen, Begründung unter Entscheidungen

# Metrics
duration: 34min
completed: 2026-08-24
---

# Phase 11 Plan 03: Die zwei neuen Leser Summary

**Ein Talk- und ein Tabellen-Treffer aus der Suche sind jetzt auflösbar statt `kind=url`: `fetch("message:abcd1234:5103")` liefert den Text genau dieser Nachricht (und lehnt eine fehlende Zielnachricht mit einem Satz ab, statt eine Nachbarnachricht auszugeben), `fetch("table:7")` liefert Titel, Zeilenzahl und die ersten 20 Zeilen. 23 neue Testfälle nageln beide Zweige an den Stellen fest, an denen sie unsichtbar falsch antworten könnten.**

## Was gebaut wurde

### Die drei neuen Funktionen

| Ort | Signatur | Aufgabe |
|-----|----------|---------|
| `tools/talk.py` | `one_message(window: list[dict[str, Any]], message_id: str) -> dict[str, Any] \| None` | genau eine Nachricht aus einem Kontextfenster, gefiltert auf die `id` und gegen `KEPT_TYPES` |
| `tools/tables.py` | `as_text(title: str, rows: list[list[Any]], total: int) -> list[str]` | eine Tabelle als Zeilenliste, jede Zelle durch `marks.without_marks` |
| `tools/chatgpt.py` | `async _fetch_message(clients, token, message_id)` und `async _fetch_table(clients, table_id)` | die zwei neuen `case`-Zweige des Dispatchs |

Der Dispatch hat jetzt acht Zweige plus den `_`-Zweig; `_UNFETCHABLE` ist unverändert.

Zwei Hilfsfunktionen kamen dazu, weil der Plan ihre Frage offen ließ: `tables._cell_text` (eine Zelle kann eine Liste oder ein Objekt sein, `str()` darauf wäre ein Python-Repr beim Modell) und `chatgpt._table_total` (die Gesamtzahl, wenn `rowsCount` fehlt oder unter dem Fenster liegt).

### Die drei Konstanten samt Begründung

| Name | Wert | Begründung, wie sie im `#:`-Kommentar steht |
|------|------|--------------------------------------------|
| `MESSAGE_CONTEXT_LIMIT` | `1` | Das kleinste Fenster, das die Zielnachricht garantiert trägt: spreed 24.0.4 hebt den Historienteil auf `max(1, limit)` und holt ihn mit `includeLastKnown = true`, der Zukunftsteil bekommt dieselbe Zahl. Also Zielnachricht plus höchstens eine neuere. Ein größeres Fenster kostet Payload und ändert an der Sicherheit nichts, weil die Auswahl hier passiert (Messweg aus 11-02). |
| `TABLE_ROWS` | `20` | **Setzung, keine Messung.** Eine Tabelle hat keinen natürlichen Auszug, also muss jemand entscheiden, was "die ersten Zeilen" heißt. Zwanzig ist ein Bildschirm voll und liegt bewusst unter dem Default-Fenster von `tables_browse` (25), weil diese Antwort ein Auszug neben einer Gesamtzahl ist und keine Seite eines Laufs. `tables_browse` ist der Weg zum Rest, und der pagt. |
| `MAX_TABLE_BYTES` | `4096` (4 KiB) | Ebenfalls eine Setzung: `TABLE_ROWS` begrenzt die Zahl der Zeilen, diese Zahl begrenzt, was sie kosten dürfen, denn eine einzige Textzelle trägt bis zu 40.000 Zeichen und zwanzig davon wären ein Megabyte. 4 KiB sind etwa 20 Zeilen mal 8 Spalten mal 20 Zeichen, also kommt die gewöhnliche Tabelle ganz an und die pathologisch breite wird geschnitten. Ausdrücklich ein Achtel von `MAX_MAIL_BYTES`: ein Brief wird von vorn bis hinten gelesen, ein Tabellenauszug soll sagen, was in der Tabelle steht. |

Dazu zwei Titel-Ersatzwerte für den Fall einer deformierten Antwort: `_NO_CONVERSATION = "(conversation without a name)"` und `_NO_TABLE_TITLE = "(table without a title)"`.

### Die vollständigen `metadata`-Schlüssellisten

**`message:<token>:<messageId>`**, alle Werte sind `str`:

| Schlüssel | Wert | Immer da? |
|-----------|------|-----------|
| `kind` | `"message"` | ja |
| `conversation` | der Token, so wie er in der Id stand | ja |
| `message_id` | die Nachrichten-Id aus der Id, als Zeichenkette | ja |
| `actor` | Anzeigename des Verfassers, marker-gefiltert; leer, wenn die App keinen liefert | ja |
| `timestamp` | Unix-Sekunden der App als Zeichenkette (dieselbe Lesart wie `last_activity` in `talk_browse`) | nur wenn positiv; eine `0` heißt "die App hat keinen geschickt" und wird weggelassen |
| `truncated` | `"true"` | nur wenn `talk_tools._capped` bei `MAX_MESSAGE_BYTES` geschnitten hat |

**`table:<tableId>`**, alle Werte sind `str`:

| Schlüssel | Wert | Immer da? |
|-----------|------|-----------|
| `kind` | `"table"` | ja |
| `table_id` | die Id aus der Id | ja |
| `rows_total` | Zeilen der Tabelle (`rowsCount`), Rückfall auf die gelesene Zahl | ja |
| `rows_shown` | Zeilen in dieser Antwort (ohne Kopfzeile), höchstens `TABLE_ROWS` | ja |
| `truncated` | `"true"` | nur wenn die Byte-Kappe `MAX_TABLE_BYTES` gegriffen hat |

Beide Ergebnisse validieren durch `FetchResult`; je ein Test behauptet den `str`-Typ per Schleife.

### Die gewählten `url`-Formen

| Kind | Form | Gebaut von |
|------|------|-----------|
| `message` | `{base_url}/index.php/call/{token}` | `talk_client.web_url(clients.creds, token)` |
| `table` | `{base_url}/index.php/apps/tables/#/table/{table_id}` | `tables_client.web_url(clients.creds, table_id)` |

Beide Helfer bauen wörtlich aus `creds.base_url`; im Funktionskörper wird keine Adresse aus einer Antwort gelesen. Der Weg über die zwei `web_url`-Helfer statt über ein eigenes f-String ist derselbe, den `talk_browse` und `tables_browse` gehen, also gibt es je Familie genau eine Stelle, die die Web-Route kennt.

### Der Wortlaut der Ablehnungssätze

**1. Zielnachricht nicht lesbar** (fehlt im Fenster, gelöscht, Systemnachricht, oder leeres Fenster nach 304):

```
The message 5103 cannot be read in the conversation abcd1234: either it was deleted, or it
is a system message this server does not pass on as content.
```
Hinweis:
```
Call talk_browse with level="messages" and this token to see what the conversation carries
now; the ids in that answer can be fetched.
```

**2. Tabelle ohne Zeile** (leere Antwort und Antwort mit nur der Kopfzeile, derselbe Satz):

```
The table 7 exists, but it carries no row.
```
Hinweis:
```
Call tables_browse with level=columns to see what this table expects, and level=rows once
somebody has added a row to it.
```

**3. Token nicht in der eigenen Konversationsliste** (geerbt aus `talk_tools._room`, Phase 9, hier nicht neu formuliert):

```
The token 'zzzz9999' is not in the conversation list of this account.
```
Hinweis:
```
Call talk_browse with level=conversations first; it lists the token of every conversation of
this account.
```

Dazu die zwei Absagen aus dem Codec, die ohne einen einzigen Request greifen: `message:ABC:1` und `table:abc` scheitern in `ids.parse` (`is not a valid Talk message id` beziehungsweise `is not a valid table id`).

### Die Reihenfolge in beiden Zweigen

`message`: `capabilities.require_app("spreed")`, dann `talk_tools._room` (Token gegen die eigene Liste, T-11-14), dann **einmal** `get_message_context(..., limit=1)`, dann `one_message` und die Ablehnung bei `None`. Der Grund für die Auflösung über die Liste steht als Kommentar dabei und ist ausdrücklich **nicht** der Brute-Force-Zähler aus Phase 9 (die Kontextroute trägt kein `#[BruteForceProtection]`), sondern der eigene Satz statt eines fremden 404 plus der Anzeigename für Titel und Link. Der Preis, ein zusätzlicher Request je `fetch`, steht im Docstring.

`table`: `capabilities.require_app("tables")`, dann **einmal** `get_table` (Titel und `rowsCount` aus einer Antwort), dann **einmal** `get_rows_simple(limit=TABLE_ROWS)`, kein Paging. Dann Marker-Filter je Zelle in `as_text`, dann die Byte-Kappe, dann `FINAL_TRUNCATION`, genau in dieser Reihenfolge.

### Die Textform einer Tabelle

```
Übergaben Straßenbau
Rows: 342, and this excerpt carries the first 3
Aufgabe | Status | status  | Fällig am | Größe in m²
Baulos 3 übergeben | offen | Nachtrag geprüft | 2026-09-01 | 1240.50
...
```

Zeile 1 ist der Titel, Zeile 2 die Gesamtzahl (und, wenn der Auszug kleiner ist, zusätzlich seine Größe), danach die Kopfzeile und die Zeilen. Dass es mehr Zeilen gibt, sagt diese Zeile mit der Gesamtzahl und nicht der Kappungsmarker.

### Die Testabdeckung

`tests/unit/test_chatgpt_fetch.py`: 61 Testfälle, vorher 38. Der `message:`-Block hat 12 Testfunktionen, der `table:`-Block 11.

| `message:`-Fall | Behauptung |
|-----------------|-----------|
| Erfolg | Fenster mit drei Nachrichten, `text` ist der Text der Zielnachricht, **beide** Nachbarn werden namentlich ausgeschlossen; `title` ist "Baustelle Süd", nicht der Nachrichtentext |
| Platzhalter | `{actor}` und `{mention-user1}` sind aufgelöst ("Bob Beispiel hat die Maße an @Alice Beispiel übergeben"), keine geschweifte Klammer im Ergebnis |
| Zielnachricht fehlt | `ToolError`, Meldung nennt beide Gründe, kein Nachbartext in der Meldung, Hinweis trägt `talk_browse` und `level="messages"` |
| Systemnachricht | dieselbe Ablehnung für `messageType="system"` |
| Unbekannter Token | `ToolError` aus der Liste, Kontextroute `call_count == 0` |
| HTTP 304 | `ToolError` und nicht ein leerer Erfolg |
| Fremder Marker | `[truncated here` nicht im Text, die Worte der Nachricht bleiben, `truncated` fehlt in `metadata` |
| Kappung | `metadata["truncated"] == "true"`, **kein** zweiter Marker im Text (beide Formen geprüft) |
| `metadata` | jeder Wert ist `str`, `FetchResult` validiert, `timestamp` ist eine Zahl als Zeichenkette |
| Fehlende Talk-App | `AppMissingError` mit dem Satz aus `capabilities._MISSING["spreed"]`, Liste und Kontextroute je `call_count == 0` |
| `message:ABC:1` | `ToolError` aus `ids.parse`, Catch-all-Route `call_count == 0` |
| Zählung | Liste genau einmal, Kontextroute genau einmal, `limit` am Draht ist `MESSAGE_CONTEXT_LIMIT` |

| `table:`-Fall | Behauptung |
|---------------|-----------|
| Erfolg | Titel als erste Zeile, `Rows: 342`, Kopfzeile, Zellwerte, Zahl als Zelle; `id`, `url` aus der Instanz, `rows_total`/`rows_shown` |
| Leere Tabelle | `ToolError` "carries no row" mit `tables_browse` im Hinweis |
| Nur Kopfzeile | dieselbe Ablehnung |
| Marker in einer Zelle | im Ergebnis nicht mehr da, die Zellworte bleiben |
| Byte-Kappe | Text endet mit genau einem Marker, `truncated == "true"`, kein `files_read` im Text |
| Mehr Zeilen als `TABLE_ROWS` | `rows_total` 342, `rows_shown` 20, Text nennt beide, `limit` am Draht ist `TABLE_ROWS` |
| `metadata` | jeder Wert ist `str`, `FetchResult` validiert |
| Fehlende Tables-App | `AppMissingError` mit dem Satz aus `capabilities._MISSING["tables"]`, beide Tables-Präfixe `call_count == 0` |
| `table:abc` | `ToolError` aus `ids.parse`, Catch-all-Route `call_count == 0` |
| Zählung | `get_table` einmal, `get_rows_simple` einmal |
| Fremde URL in einer Zelle | Route auf diese Domain `call_count == 0`, die Adresse steht im Text und nicht im `url`-Feld |

Der Modul-Docstring der Testdatei nennt jetzt acht Id-Arten und beschreibt für beide Blöcke die eine falsche Antwort, gegen die sie geschrieben sind.

### Was noch nachgezogen wurde

- Der Modul-Docstring von `chatgpt.py`: sieben tragende Eigenschaften des Routings statt fünf (zwei neue Absätze für die zwei Kinds), und "sieben Leser, drei davon schreiben einen Marker zurück" statt "fünf Leser, zwei davon".
- `vulture_whitelist.py`: der Eintrag `get_message_context` aus Plan 11-02 ist entfernt, wie 11-02 es angekündigt hat, und an seiner Stelle steht der Absatz, der die Auflösung festhält (dasselbe Muster wie der leere Tables-Block aus 08-03).
- `capabilities_payload` in der Testdatei nimmt jetzt zusätzlich `spreed` und `tables`, damit die zwei neuen Blöcke die vorhandene Helfermechanik benutzen statt einer Kopie.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Commit-Zuschnitt] Task 1 und Task 2 ändern dieselbe Datei, also vier Commits statt drei**

- **Found during:** Task 2
- **Issue:** Beide Tasks bearbeiten `src/mcp_connector/tools/chatgpt.py`. Zwei Task-Commits hätten entweder Task-2-Code in einem Task-1-Commit gehabt (falsche Beschriftung) oder eine Zwischenfassung, in der die Datei nicht importierbar ist.
- **Fix:** Vier dateiweise Commits in importierbarer Reihenfolge, jeder mit einer Nachricht, die genau seinen Inhalt nennt: `29c1883` (`tools/talk.py`, die Projektion), `b65df98` (`tools/tables.py`, die Textform), `363ca8e` (`tools/chatgpt.py` plus `vulture_whitelist.py`, beide `fetch`-Zweige), `c396e78` (die Tests). Kein Commit behauptet Arbeit, die er nicht enthält.
- **Files modified:** keine inhaltliche Änderung, nur der Zuschnitt

**2. [Rule 2 - Fehlende Notwendigkeit] Eine Zelle kann eine Liste oder ein Objekt sein, `str()` darauf ist ein Python-Repr**

- **Found during:** Task 2
- **Issue:** Der Plan beschreibt `as_text` mit "jede Zelle läuft durch `marks.without_marks`". `tables._text` ist `marks.without_marks(str(value))`, und Tables schreibt in eine Zelle auch Listen (Mehrfachauswahl) und Objekte (Auswahloption mit `label`). Ein Modell hätte `['offen', 'geprüft']` als Zelltext bekommen, und `_clean` löst das nur für die Datenform, nicht für eine Textzeile.
- **Fix:** `tables._cell_text` rendert eine Liste als kommagetrennte Werte, ein Objekt als kompaktes JSON und `None` als leere Zeichenkette (die App selbst sendet `""` für einen fehlenden Wert), und schickt beides danach durch `_text`, damit der Marker-Filter die gerenderte Form abdeckt und nicht nur ihre Blätter.
- **Files modified:** src/mcp_connector/tools/tables.py
- **Commit:** b65df98

**3. [Rule 2 - Fehlende Notwendigkeit] `rows_total` braucht eine Regel für eine fehlende `rowsCount`**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt `rows_total` in `metadata` und die Gesamtzahl im Text, sagt aber nicht, was gilt, wenn die App keine brauchbare `rowsCount` liefert. `tools/tables.py::_row_count` lässt das Feld in diesem Fall weg, was hier nicht geht: die Zahl ist Teil des Satzes, der den Auszug zum Auszug macht.
- **Fix:** `chatgpt._table_total` fällt auf die gerade gelesene Zeilenzahl zurück, und zwar auch dann, wenn die App eine Zahl **unter** dem Fenster meldet (der Zähler von Tables driftet, deshalb sichert `tables_browse` seinen `next`-Handle damit ab). Die Begründung steht im Docstring, und die Zeile im Text nennt die Auszugsgröße nur, wenn sie kleiner als die Gesamtzahl ist.
- **Files modified:** src/mcp_connector/tools/chatgpt.py
- **Commit:** 363ca8e

**4. [Rule 1 - Ehrlichkeit eines Feldes] `timestamp` wird weggelassen statt als `"0"` behauptet**

- **Found during:** Task 1
- **Issue:** Der Plan listet `timestamp` als `metadata`-Schlüssel. `talk_tools._message` liefert `0`, wenn die App keinen brauchbaren Zeitstempel geschickt hat (`_number` gibt für alles, was keine Zahl ist, `0`), und `"0"` beim Modell heißt "1. Januar 1970" und nicht "unbekannt".
- **Fix:** Der Schlüssel steht nur bei einem positiven Wert im `metadata`, wie `date` im Mail-Zweig (`_mail_date` antwortet mit nichts statt mit einer Vermutung). Die Schlüsselliste oben nennt es ausdrücklich.
- **Files modified:** src/mcp_connector/tools/chatgpt.py
- **Commit:** 363ca8e

**5. [Rule 2 - Fehlende Notwendigkeit] Eine benannte Konstante für das Kontextfenster**

- **Found during:** Task 1
- **Issue:** Der Plan sagt "mit dem `limit` aus 11-02-SUMMARY", also `limit=1`. Eine nackte `1` am Aufruf hätte die Begründung (spreed hebt den Historienteil auf `max(1, limit)` und liefert die Zielnachricht mit) nirgends stehen lassen, und diese Datei trägt jede Zahl mit ihrem Grund.
- **Fix:** `chatgpt.MESSAGE_CONTEXT_LIMIT = 1` mit `#:`-Kommentar samt Quelle der Rechnung; ein Test behauptet die Zahl am Draht.
- **Files modified:** src/mcp_connector/tools/chatgpt.py
- **Commit:** 363ca8e

### Nicht abgewichen

- Kein `uv add`, kein `pip install`, kein `npm install`: `pyproject.toml` und `uv.lock` sind unangetastet (T-11-SC).
- `git diff --stat` zeigt keine Änderung an `src/mcp_connector/server/`, `src/mcp_connector/tools/context.py` und `src/mcp_connector/provider_map.py`.
- Kein neues Werkzeug, keine geänderte `Field`-Beschreibung: das Budget-Gate meldet dieselbe Messung wie nach 11-02 (15736 Bytes, 21 Werkzeuge, Budget 18500).
- `talk_tools._room` wird direkt aufgerufen, ohne einen zweiten Listenabruf in `chatgpt.py`; ein öffentlicher Zweitname war nicht nötig, weil ruff und pyright in dieser Konfiguration keinen privaten Modulzugriff innerhalb des Pakets beanstanden.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün (196 Dateien) |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run pytest -q` | Exit 0 |
| `uv run pytest tests/unit/test_chatgpt_fetch.py -q` | Exit 0, 61 Testfälle (vorher 38) |
| `uv run pytest tests/contract -q` | Exit 0, `search` und `fetch` behalten ihr Output-Schema, Oberfläche bleibt bei 21 Namen |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | Exit 0, **ohne** neuen Whitelist-Eintrag und mit einem entfernten |
| `uv run vulture src scripts vulture_whitelist.py` (CI-Form) | Exit 0 |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15736 Bytes, 21 Tools, Budget 18500 |
| Vertragsskript Task 1 | "message branch wired" |
| Vertragsskript Task 2 | "table branch wired" |
| Vertragsskript Task 3 | "fetch branch tests present" |
| `git diff --stat` gegen die vier verbotenen Pfade | leer |

## Für die Folgeplane

- **11-04/11-05 (Bündel):** `prepare_context` weist Talk- und Tables-Treffer über `_short()` weiterhin als `resolvable: False` aus, obwohl `fetch` sie jetzt liest (Pitfall 1 der Recherche). Das ist die Stelle, an der TOOL-16 im Bündel sonst unwirksam bleibt.
- **11-06 (Live-Messung):** beide Zweige gegen eine echte Instanz, und die Nebenwirkungsfreiheit der Kontextroute über die Konversationsliste (`unread`, `unread_mention`, `lastReadMessage`) vor und nach dem Aufruf, nie über die Route selbst.
- **11-08 (Doku):** die Zahl der auflösbaren Id-Arten steigt von sechs auf acht; drei READMEs plus die Doku-Seiten nennen sie. Die Konstanten für den Wortlaut sind `TABLE_ROWS` (20 Zeilen) und `MAX_TABLE_BYTES` (4 KiB).
- **TOOL-16** bleibt in `REQUIREMENTS.md` unangehakt: die Auflösung existiert, aber der Anforderungstext verspricht auflösbare Suchtreffer, und das Bündel behauptet heute noch das Gegenteil.

## Self-Check: PASSED

Alle fünf genannten Dateien liegen auf der Platte, alle vier Commit-Hashes (29c1883, b65df98, 363ca8e, c396e78) sind in `git log` auffindbar.
</content>
