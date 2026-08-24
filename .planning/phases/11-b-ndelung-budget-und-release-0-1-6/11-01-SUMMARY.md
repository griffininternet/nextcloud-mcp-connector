---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 01
subsystem: api
tags: [ids, unified-search, provider-map, talk, tables, regex, urlsplit]

# Dependency graph
requires:
  - phase: 10-mail
    provides: "mail:<databaseId> als sechstes Id-Kind, der Ziffernwächter in ids.parse und das Muster Attribut zuerst, URL als Gegenprobe"
  - phase: 09-talk
    provides: "das Token-Alphabet [a-z0-9]{4,30} und _path_token im Talk-Client"
provides:
  - "ids.encode_message und ids.encode_table plus die zwei parse-Zweige: der Codec kennt acht Formen"
  - "message:<token>:<messageId> und table:<tableId> als endgültige Schreibweise der zwei neuen Kinds"
  - "PROVIDER_KINDS mit talk-message, talk-message-current und tables-search-tables (sechs Einträge)"
  - "provider_map._message_target und provider_map._tables_node als die zwei neuen Leser"
  - "der vollständige neue _HINT-Text mit acht Formen"
affects: [11-03 (die Leser für message und table in fetch), 11-04, 11-08 (READMEs: Hinweistext und Zahl der Id-Arten)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fragment-Leser: urlsplit(url).fragment plus fullmatch, wenn die Id nicht im Pfad steht"
    - "Node-Typ zusammen mit der Id lesen, damit #/view/<id> nicht als table:<id> durchgeht"
    - "Provider-Zeile nur mit belegtem Kommentar: Repository, Datei und Klasse der Provider-Id"

key-files:
  created: []
  modified:
    - src/mcp_connector/ids.py
    - src/mcp_connector/provider_map.py
    - tests/unit/test_ids.py
    - tests/unit/test_provider_map.py

key-decisions:
  - "Die Kinds heissen message und table, nicht talk und tables: eine Id adressiert ein Objekt, keine App (dieselbe Regel wie bei card)"
  - "talk-message-current kommt in die Tabelle, und zwar belegt: CurrentMessageSearch erbt von MessageSearch und baut seine Einträge über das geerbte performSearch, überschrieben sind nur getId, getName, getOrder, das Subline-Template und die Raumauswahl (Annahme A1 aufgelöst, nicht geraten)"
  - "talk-conversations bleibt url: eine Konversation ist kein Dokument, talk_browse ist der Weg zu ihr"
  - "Ein Tables-Treffer auf eine View bleibt url, weil der Client dieses Projekts nur Tabellen liest und eine View-Id als Tabellen-Id nicht laut scheitert, sondern die Tabelle mit derselben Nummer liest"
  - "Mail bleibt url mit benanntem Grund im Modul-Docstring: die Auflösung eines Deep-Links auf die databaseId ist ungemessen und Future Requirement"
  - "provider_map bekommt eigene kompilierte Ausdrücke (_TOKEN, _DIGITS) statt Zugriff auf die privaten Namen von ids.py; str.isdigit reicht nicht, weil es eine Hochzahl Zwei und eine arabisch-indische Ziffer annimmt"
  - "threadId wird in _message_target bewusst nie gelesen: es benennt einen Thread, nicht eine Nachricht"

patterns-established:
  - "Fragment-Leser mit Node-Typ: _tables_node liest (nodeType, nodeId) aus urlsplit(url).fragment und akzeptiert nur table"
  - "Zwei-Werte-Variante von 'Attribut zuerst, URL als Gegenprobe': _message_target gibt None zurück, statt eine Hälfte zu raten"

requirements-completed: []  # TOOL-16 bleibt offen: dieser Plan ist nur das Fundament, die Leser folgen in 11-03

# Metrics
duration: 25min
completed: 2026-08-24
---

# Phase 11 Plan 01: Zwei neue Id-Kinds und zwei neue Provider Summary

**Der Codec kennt jetzt `message:<token>:<messageId>` und `table:<tableId>` als siebtes und achtes Kind, und die Übersetzungstabelle macht aus einem Talk- und einem Tabellen-Suchtreffer eine Id, die ein Leser annehmen kann, während View, Mail und ein Talk-Treffer ohne verwertbare Angaben ehrlich `kind=url` bleiben.**

## Performance

- **Duration:** ca. 25 min (Task 1 im vorherigen, per API-Fehler abgebrochenen Lauf, Task 2 in diesem)
- **Started:** 2026-08-24T19:16:00Z (ungefähr, Startzeitpunkt des ersten Laufs)
- **Completed:** 2026-08-24T19:43:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `ids.py` kennt acht Formen: `encode_message`, `encode_table` und zwei `parse`-Zweige, beide mit Wächtern, die vor jedem Request greifen (Token-Alphabet plus ASCII-Ziffern).
- `PROVIDER_KINDS` ist von drei auf sechs Einträge gewachsen, jede neue Zeile mit dem Kommentar, in welchem Repository, welcher Datei und welcher Klasse die Provider-Id gelesen wurde.
- Annahme A1 ist aufgelöst: `talk-message-current` trägt dieselben Attribute wie `talk-message`, im Quellcode von `nextcloud/spreed` nachgelesen statt vermutet.
- Zwei neue Leser: `_message_target` (Attribute zuerst, `/call/<token>` und `#message_<id>` als Gegenprobe) und `_tables_node` (Fragment statt Pfad, Node-Typ inklusive).
- Der Modul-Docstring von `provider_map.py` begründet jetzt namentlich, warum eine View, ein Mail-Treffer und `talk-conversations` bewusst `url` bleiben.

## Task Commits

1. **Task 1: message und table als siebtes und achtes Id-Kind** - `9b0606e` (feat)
2. **Task 2: Zwei Provider in der Übersetzungstabelle, plus der Fragment-Leser** - `a2a9039` (feat)

## Files Created/Modified

- `src/mcp_connector/ids.py` - `encode_message`, `encode_table`, die zwei `parse`-Zweige mit Token- und Ziffernwächter, `_TOKEN` als eigener kompilierter Ausdruck (kein Import aus `nextcloud/`), Formatliste und `_HINT` auf acht Formen erweitert.
- `src/mcp_connector/provider_map.py` - drei neue `PROVIDER_KINDS`-Zeilen, `_TOKEN`, `_DIGITS`, `_MESSAGE_FRAGMENT`, `_TABLES_NODE`, die Leser `_message_target` und `_tables_node`, zwei `elif`-Zweige in `extract_id`, drei neue Docstring-Absätze (View, Mail, `talk-conversations`).
- `tests/unit/test_ids.py` - Roundtrip beider Kinds, die akzeptierte Null, siebzehn Ablehnungsformen, `_HINT`-Vertrag auf acht Formen.
- `tests/unit/test_provider_map.py` - 31 Tests: beide Talk-Provider, der Fragment-Rückfall bei `attributes: []`, die zwei Degradationsfälle, `#/table/7` gegen `#/view/3`, der leere und der nicht numerische Knoten, Mail, die fremde Herkunft, `talk-conversations` und die eingefrorene Provider-Menge.

## Die endgültigen Schreibweisen (für Plan 11-03 und 11-08)

**Die zwei neuen Kinds:**

```
message:<token>:<messageId>
table:<tableId>
```

`message` hat zwei Segmente (Form des `event`-Zweigs): der Token ist die Konversation, die Zahl die Nachrichten-Id **derselben** Konversation, also nicht `threadId` und nicht `referenceId`. `table` hat ein Segment (Form des `mail`-Zweigs) und ist nie eine View-Id.

**Die endgültige Menge von `PROVIDER_KINDS` (sechs Einträge):**

| Provider-Id | Kind | Belegt in |
|---|---|---|
| `files` | `file` | (Bestand) |
| `notes` | `note` | (Bestand) |
| `search-deck-card-board` | `card` | `nextcloud/deck lib/Search/DeckProvider.php` |
| `talk-message` | `message` | `nextcloud/spreed lib/Search/MessageSearch.php` |
| `talk-message-current` | `message` | `nextcloud/spreed lib/Search/CurrentMessageSearch.php` |
| `tables-search-tables` | `table` | `nextcloud/tables lib/Search/SearchTablesProvider.php` |

Nicht in der Tabelle und je mit Grund im Modul-Docstring: `talk-conversations` (eine Konversation ist kein Dokument), der Kalender-Provider (Tagesansicht statt DAV-Objektname), jeder Mail-Provider (Deep-Link-Auflösung ungemessen, Future Requirement).

**Die zwei neuen Leserfunktionen:**

- `provider_map._message_target(attributes, url) -> tuple[str, str] | None` gibt `(token, messageId)` oder `None`.
- `provider_map._tables_node(url) -> tuple[str, str] | None` gibt `(nodeType, nodeId)` aus `urlsplit(url).fragment`; nur `nodeType == "table"` wird zu einer Id.

**Der vollständige neue `_HINT`-Text (ein Satz, acht Formen):**

```
Use an id exactly as returned by a search tool: file:<fileid>, note:<id>, card:<board>:<stack>:<card>, event:<calendar>:<object>, mail:<databaseId>, message:<token>:<messageId>, table:<tableId> or url:<absolute-url>.
```

Für die READMEs in Plan 11-08: **acht** Id-Arten, nicht mehr sechs.

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die zwei Entscheidungen mit Folgen für spätere Pläne:

1. **`talk-message-current` ist drin, belegt.** `CurrentMessageSearch extends MessageSearch` und ruft für die Trefferbildung das geerbte `performSearch` auf; `commentToSearchResultEntry` setzt `conversation`, `messageId`, `threadId`, `actorType`, `actorId` und `timestamp` und verlinkt auf `spreed.Page.showCall` mit dem Fragment `message_<id>`. Überschrieben sind nur `getId`, `getName`, `getOrder`, das Subline-Template und die Raumauswahl. Damit ist Annahme A1 der Recherche geschlossen.
2. **`_tables_node` liest den Node-Typ mit.** `getInternalLink($nodeId, $nodeType)` baut `#/table/<id>` und `#/view/<id>` aus einer Vorlage; der Tables-Client dieses Projekts baut nur `tables/{id}`-Pfade. Eine View-Id als Tabellen-Id würde also nicht scheitern, sondern die Tabelle mit derselben Nummer lesen (T-11-01).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Verifikationsschnipsel des Plans riefen `extract_id` mit falscher Argument-Reihenfolge auf**
- **Found during:** Task 2
- **Issue:** Der `<interfaces>`-Block und beide `<automated>`-Schnipsel des Plans nennen `extract_id(base_url, provider_id, entry)`. Im Repo lautet die Signatur seit Phase 1 `extract_id(provider_id, entry, base_url)`, und `tools/search.py:180` ruft sie so auf.
- **Fix:** Die echte Signatur bleibt unverändert (eine Umstellung hätte den einzigen Aufrufer und alle bestehenden Tests gebrochen, ohne Nutzen). Der Verifikationsschnipsel wurde beim Ausführen auf die echte Reihenfolge umgestellt, alle dreizehn Behauptungen laufen darüber grün.
- **Files modified:** keine (nur der ad-hoc ausgeführte Verifikationsbefehl)
- **Verification:** `provider map ok ['files', 'notes', 'search-deck-card-board', 'tables-search-tables', 'talk-message', 'talk-message-current']`
- **Committed in:** kein Code-Commit nötig

**2. [Rule 2 - Missing Critical] Strenge ASCII-Ziffernprüfung im neuen Leser statt `str.isdigit`**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt für `attributes["messageId"]` eine Prüfung "gegen `isdigit`", wie es `_file_id` vormacht. `str.isdigit` nimmt aber auch `²` und `٤٢` an, und eine so gebaute Id (`message:abcd1234:٤٢`) müsste der Codec beim nächsten Aufruf ablehnen: die Suche hätte eine Id ausgeliefert, die kein Leser annimmt.
- **Fix:** `provider_map` bekommt einen eigenen kompilierten `_DIGITS`-Ausdruck (`[0-9]+`, `fullmatch`), derselbe Wächter, den `ids.py` und `tools/mail.py` schon benutzen. `_file_id` bleibt unangetastet (ausserhalb des Scope dieses Plans).
- **Files modified:** src/mcp_connector/provider_map.py
- **Verification:** `uv run pytest -q` grün, der Talk-Treffer mit `messageId: "abc"` fällt auf `url`
- **Committed in:** `a2a9039`

**3. [Rule 2 - Missing Critical] Drei Tests mehr als verlangt**
- **Found during:** Task 2
- **Issue:** Der Plan nennt keinen Test für `talk-message-current` (obwohl der Provider neu in die Tabelle kommt), keinen für `talk-conversations` (obwohl der Ausschluss eine bewusste Entscheidung ist) und keinen für einen nicht numerischen Tables-Knoten (`#/table/7a`).
- **Fix:** Drei Tests ergänzt; die drei Tables-Degradationsfälle sind als ein parametrisierter Test geschrieben.
- **Files modified:** tests/unit/test_provider_map.py
- **Verification:** 31 Tests in `test_provider_map.py`, alle grün
- **Committed in:** `a2a9039`

**4. [Rule 1 - Bug] `"spreed"` als Beispiel eines unbekannten Providers durchgängig ersetzt**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt den Austausch nur in `test_an_unknown_provider_becomes_a_url_and_is_never_guessed`. `"spreed"` stand aber an drei Stellen der Datei, und alle drei prüfen dieselbe Regel an einer Zeichenkette, die nie eine Provider-Id war.
- **Fix:** Alle drei Stellen benutzen jetzt `"forms"` als wirklich unbekannten Provider; die Talk-Regel wird stattdessen an der echten Provider-Id `talk-conversations` geprüft.
- **Files modified:** tests/unit/test_provider_map.py
- **Verification:** `uv run pytest -q` grün
- **Committed in:** `a2a9039`

---

**Total deviations:** 4 auto-fixed (1 blocking, 2 missing critical, 1 bug)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 betrifft nur den Verifikationsbefehl, 2 schliesst eine Lücke, die eine unbrauchbare Id ausgeliefert hätte, 3 und 4 härten die Testabdeckung genau an den Stellen, die dieser Plan neu einführt.

## Issues Encountered

- Der Plan schrieb vor, Annahme A1 durch einen Blick in `CurrentMessageSearch.php` zu klären. Die Datei liegt nicht im Repo, also wurde sie samt `MessageSearch.php` und `SearchTablesProvider.php` per `curl` aus den Upstream-Repositories gelesen. Alle drei Provider-Ids und die Trefferform sind damit im Quellcode belegt, nicht aus der Erinnerung.

## Verification Results

| Prüfung | Ergebnis |
|---|---|
| `uv run pytest -q` | grün (gesamte Default-Auswahl) |
| `uv run pytest tests/contract -q` | grün, kein Werkzeug und kein Schema geändert |
| `uv run ruff check .` / `format --check .` | grün, 196 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün, kein neuer Whitelist-Eintrag |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15736 Bytes, **21 Werkzeuge**, Budget 18500 |
| `git diff --stat` gegen `pyproject.toml`, `uv.lock`, `tools/`, `server/`, `nextcloud/` | leer, wie vom Plan gefordert |

## Known Stubs

Keine. Die einzige bewusst unvollständige Stelle ist der Plan-Scope selbst: `fetch` kann `message:` und `table:` noch nicht auflösen, weil die Leser erst in Plan 11-03 entstehen. Das ist die erzwungene Reihenfolge des Phasenplans, kein Stub im Code: eine Id dieser Art entsteht bis dahin nur aus einem echten Suchtreffer, und `fetch` antwortet auf ein unbekanntes Kind mit einem ToolError samt Hinweistext.

## Threat Flags

Keine neue Angriffsfläche ausserhalb des Threat-Models des Plans. Die vier `mitigate`-Dispositionen T-11-01 bis T-11-04 sind je durch Code und Test abgedeckt, T-11-05 (Mail) ist wie vorgesehen `accept` mit Begründung im Modul-Docstring, T-11-06 ist durch die eingefrorene Provider-Menge abgedeckt, T-11-SC ist trivial erfüllt: `pyproject.toml` und `uv.lock` sind unangetastet.

## User Setup Required

Keine. Keine neue Abhängigkeit, keine neue Umgebungsvariable, kein Werkzeug mehr.

## Next Phase Readiness

- **Bereit für Plan 11-03:** Die Kind-Namen stehen (`message`, `table`), die Segmentformen stehen, und `ids.parse` liefert die Segmente schon geprüft. Ein Leser in 11-03 muss weder Token noch Zahl noch einmal validieren.
- **Bereit für Plan 11-08:** `_HINT` und die Zahl **acht** stehen oben wörtlich für die drei READMEs.
- **Offen und bewusst offen:** TOOL-16 bleibt in `REQUIREMENTS.md` auf `Pending`. Die Anforderung verlangt auflösbare Treffer, nicht nur Ids: erfüllt ist sie erst, wenn `fetch` die zwei Kinds liest (11-03). Fünf Pläne der Phase tragen `TOOL-16` im Frontmatter; abgehakt wird sie im letzten davon.

## Self-Check: PASSED

Alle vier geänderten Dateien liegen auf der Platte, alle drei Commits (`9b0606e`, `a2a9039`, `7a86864`) sind im Log, und der Arbeitsbaum ist sauber.

---
*Phase: 11-b-ndelung-budget-und-release-0-1-6*
*Completed: 2026-08-24*
