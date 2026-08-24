# Phase 11: Bündelung, Budget und Release 0.1.8 - Research

**Researched:** 2026-08-24
**Domain:** Bestandscode dieses Repositories (prepare_context, provider_map/ids/fetch, Budget-Gate, Release-Runbook) plus zwei fremde App-APIs (spreed v24.0.4 Chat-Kontext-Route, tables Suchprovider)
**Confidence:** HIGH für den Ist-Zustand und die beiden fremden Routen (Quellcode und laufende Messung), MEDIUM für die Landepunkte der Budget-Diät (hängt an Formulierungsentscheidungen der Phase)

## Summary

Diese Phase fügt **keine neue Abhängigkeit, kein neues Werkzeug und keine neue Familie** hinzu. Sie erweitert vier Stellen im Bestand und stellt eine Fassung in den Store. Die Arbeit ist deshalb ungewöhnlich gut vorhersagbar, und der Ist-Zustand ist vollständig gelesen: `tools/context.py` (342 Zeilen, zwei `gather`-Beine, Budget je Quelle, `degraded`-Liste), `provider_map.py` (drei bekannte Provider, ehrliche Restkategorie `url`), `ids.py` (sechs Kinds), `tools/chatgpt.py` (fünf `fetch`-Zweige), `scripts/check_tool_budget.py` (zwei Gates: Gesamtsumme und Obergrenze je Werkzeug) und `docs/store-submission.md` (Runbook mit acht Schritten und Nachweistabelle).

Drei Befunde verdienen die Aufmerksamkeit des Planers vor allem anderen. **Erstens** verbietet ein bestehender Test (`tests/unit/test_tools_context.py::test_this_module_reads_no_content_of_its_own`) jeden direkten Client-Zugriff in `context.py`: die neuen Talk- und Mail-Beine müssen zwingend über die Tool-Schicht (`talk_tools.browse`, `mail_tools.browse`) laufen, nicht über `clients/`. Das ist kein Stilwunsch, das ist ein rotes Gate. **Zweitens** kollidiert TOOL-16 mit einer Zeile in `context.py`: `_short()` setzt `resolvable: False` für **jeden** Treffer im `other`-Bucket, also würde ein neu auflösbarer Talk- oder Tables-Treffer im Bündel weiter als unauflösbar ausgewiesen, obwohl `fetch` ihn dann liest. Diese Zeile ist der eigentliche Kern der Phase, nicht die `provider_map`-Tabelle. **Drittens** ist die Budget-Arithmetik gemessen und exakt: bei unveränderter Messung von **15736 Bytes** ergibt die Regel (plus 15 Prozent, aufgerundet auf 500) genau **18500**, also die schon gesetzte Zwischenanhebung. Die von TOOL-15 erwarteten 17500 bis 18000 sind nur erreichbar, wenn die Schema-Diät die Messung senkt: **mindestens 84 Bytes für 18000, mindestens 519 Bytes für 17500.**

Für TOOL-16 sind beide fremden APIs im Quellcode der auf dieser Instanz laufenden Versionen verifiziert. Talk hat **keine** Route "eine Nachricht lesen", aber `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}/{messageId}/context` (spreed v24.0.4) ist nebenwirkungsfrei per Konstruktion (`timeout: 0`, `markNotificationsAsRead: false`, kein Lesemarker) und liefert die Zielnachricht mit (`includeLastKnown: true`). Der Tables-Suchprovider `tables-search-tables` baut seinen Link als `#/{nodeType}/{nodeId}` mit `nodeType` **`table` oder `view`**: nur `table` ist mit dem bestehenden Client lesbar, `view` bleibt ehrlich `url`.

**Primary recommendation:** Zwei neue `gather`-Beine in `context.py` mit eigenem Budget und eigenem `degraded`-Eintrag, beide ausschließlich über die Tool-Schicht; `provider_map` um `talk-message` (Attribute) und `tables-search-tables` (Fragment, nur `table`) erweitern, zwei neue Kinds in `ids.py`, zwei neue `fetch`-Zweige; erst danach die Schema-Diät, dann messen, dann das Gate verankern; Release 0.1.8 als letzter Plan mit Tag erst nach Owner-Freigabe.

## Owner-Vorgaben (verbindlich, statt CONTEXT.md)

Es gibt **keine** `11-CONTEXT.md` (das Phasenverzeichnis ist leer, geprüft am 2026-08-24). Die folgenden Vorgaben kommen aus dem Auftrag an diese Recherche und aus `10-08-SUMMARY.md` und sind wie gesperrte Entscheidungen zu behandeln.

### Gesperrte Entscheidungen

1. **Die Release-Nummer ist 0.1.8, nicht 0.1.6.** 0.1.4 (21.08.), 0.1.5, 0.1.6 und 0.1.7 (22.08.) liegen im Store. Bestätigt im Repo: `pyproject.toml` und `src/mcp_connector/__init__.py` stehen auf `0.1.7`, `appinfo/info.xml` auf `<version>0.1.7</version>` und `<image-tag>0.1.7</image-tag>`. Mit 0.1.8 wird der Spendenlink `https://www.paypal.com/paypalme/KhaledCherifDev` sichtbar (steht schon in `info.xml:208`, Commit `d36356d`). **Tag erst nach Owner-Freigabe.**
2. **Die Mail-Ungelesen-Zähler stehen pro Postfach in der Postfachliste** (`mail_browse(level="mailboxes", account_id=...)`), ein Request je Konto. `prepare_context` muss entscheiden, ob es alle Konten sieht oder eines. Kosten: 1 Request Kontenliste plus N Requests (je Konto).
3. **Das `unread`-Feld des Navigationseintrags darf nicht als Ungelesen-Zähler benutzt werden.** Gemessen: `{"id":"mail", ..., "unread": 0}` bei sechs ungelesenen Nachrichten. Die Bedeutung bleibt ungeklärt, der Messwert steht fest.
4. **TOOL-15: Gate neu verankern** auf Messung plus 15 Prozent, aufgerundet auf die nächsten 500, mit neuer Messzeile im Skript. Erwartet 17500 bis 18000. Werkzeugzahl bleibt 21, Konsistenz in Registry, README-Tabelle EN/DE/FR und Contract-Tests.
5. **IN-01 bis IN-04 aus `10-REVIEW.md` dürfen in dieser Phase mit erledigt werden** (IN-02 gehört ohnehin zur Release-Pflege und damit zu EXAPP-07).
6. **Vokabular-Gate:** das Wort "archiv" ist in öffentlichen Artefakten verboten, Gate vor Push lokal laufen lassen (`FORBIDDEN_VOCABULARY` in `tests/unit/test_exapp_env_setup.py:1686`, geprüft gegen den Elementtext des Manifests ohne Kommentare).
7. **Milestone-Tags heißen `milestone-v*`, niemals `v*`:** `release.yml` triggert auf `v*` und baut dann ein echtes Release.
8. **Deutsche Umlaute echt, keine Em-Dashes, keine Emojis**, auch in READMEs, Changelog und Store-Texten.

### Claudes Ermessen (Empfehlung dieser Recherche, Entscheidung im Plan)

- Zahl und Zuschnitt der Pläne und Wellen.
- Höhe der beiden neuen Zeitbudgets (`TALK_BUDGET`, `MAIL_BUDGET`) und ob die Kontenzahl gekappt wird.
- Ob die Vorschau-Kappe des Talk-Digests in Bytes oder Zeichen gemessen wird (siehe Pitfall 6).
- Wie ein Tabellen-Treffer als Text aussieht (`fetch` liefert Inhalt) und wie viele Zeilen er trägt.
- Reihenfolge der Diät-Schnitte innerhalb von TOOL-15.

### Ausdrücklich außerhalb des Umfangs

- Mail-Deep-Link-Auflösung (RFC-Message-Id zu `databaseId`): Future Requirement, Trigger ist eine Messung an einer echten Instanz. **Mail-Treffer bleiben `kind=url`, mit benanntem Grund.**
- Views in Tables lesen, Talk-Threads, Mail-Entwürfe, CLIENT-01 bis 03.

## Phase Requirements

| ID | Beschreibung (gekürzt) | Research Support |
|----|------------------------|------------------|
| CTX-01 | Talk-Digest aus einem Request: max 3 Konversationen mit Erwähnung oder Ungelesenem, `lastMessage`-Vorschau hart auf ~200 Zeichen, eigenes Budget, eigener `degraded`-Eintrag; bestehendes Verhalten der anderen Quellen gemessen unverändert | Ist-Zustand `context.py` (unten), `talk_tools.browse(level="conversations")` liefert `unread`, `unread_mention`, `unread_mention_direct`, `last_message` aus **einem** Request `get_rooms(include_last_message=True)`; Messmethodik unten |
| CTX-02 | Mail-Ungelesen-Zähler pro Konto und Inbox, nur Zahlen, eigenes Budget und `degraded`-Eintrag, 1+N-Kosten gemessen und dokumentiert | `mail_tools._mailbox` trägt `unread` und `special_role`; Kostenrechnung inklusive der beiden Erkennungsrequests bei kaltem Cache (unten) |
| TOOL-15 | Budget-Gate neu verankert, fünf neue Werkzeuge schema-diätet, Annotationen ehrlich (drei lesend, zwei anlegend), Werkzeugzahl 21 in Registry, README EN/DE/FR und Contract-Tests | Gemessene Ist-Zahlen je Werkzeug und die exakte Gate-Arithmetik (unten), Annotations-Stand verifiziert, `test_the_readme_permission_table_matches_the_live_registry` und `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from` als Gates |
| TOOL-16 | `provider_map`-Einträge für `talk-message` (Attribute `conversation`/`messageId`) und `tables-search-tables` (Id im Fragment); Mail bleibt ehrlich `url` | Beide Provider im Quellcode verifiziert, `#/table/` gegen `#/view/` unterschieden, `GET .../chat/{token}/{messageId}/context` als nebenwirkungsfreier Leseweg verifiziert |
| EXAPP-07 | Release 0.1.8 im Store: Version an vier Stellen, Changelog, READMEs und Store-Texte, Gates grün, Runbook-Schritte 4 bis 8 mit Proof-Zeilen, Tag erst nach Freigabe | Runbook-Schritte einzeln aufgeschlüsselt (unten), Versionsgates benannt, Schlüssel und Zertifikat lokal vorhanden, laufende Topologie vorhanden |

## Project Constraints (from CLAUDE.md)

Aus `C:\Users\Student\nextcloud-mcp-connector\CLAUDE.md` und den globalen Regeln, alle für diese Phase bindend:

| Direktive | Konsequenz für den Plan |
|-----------|-------------------------|
| Code und README auf Englisch, Projektkommunikation Deutsch | Docstrings, Fehlersätze, Changelog: Englisch. Planungsdokumente: Deutsch |
| Echte Umlaute, keine Em-Dashes | Gilt für jedes Dokument dieser Phase |
| Keine destruktiven Writes in v1 | Beide neuen `fetch`-Zweige sind reine Lesewege; die Talk-Kontext-Route ist daraufhin verifiziert |
| Der MCP sieht nie mehr als der angemeldete Nutzer | Neue Beine laufen über die bestehenden Clients mit denselben Credentials, kein Cache über Nutzergrenzen |
| Solo-Betrieb, kuratiert schlank schlägt breit | Kein neues Werkzeug, kein neues Paket, Schema-Diät statt Budget-Anhebung aus Gewohnheit |
| `ruff check .` und `ruff format --check .` über das **ganze** Repo vor Push | Teil jeder Task-Verifikation |
| Nach jedem Edit sofort committen | Task-Commits wie in Phase 10 |
| Keine Claude-Attribution in Commits | `includeCoAuthoredBy=false` bleibt |
| Tests: alle Pfade, nicht nur Happy Path | Fehler-, Edge-, Negativ- und `no_data`-Fälle für jede neue Verzweigung |
| Doku-Seite mitziehen bei Verhaltensänderung | READMEs EN/DE/FR plus `docs/` bei neuen Id-Kinds und neuen Bündelfeldern |
| Changelog-Pflege: nutzerrelevante Änderungen in den Changelog | `## [0.1.8]`-Block, plus die fehlende `## [0.1.5]`-Sektion (IN-02) |
| GSD-Workflow: keine Direkt-Edits außerhalb eines GSD-Kommandos | Diese Recherche schreibt nur ihre eigene Datei |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Talk-Digest im Bündel | Tool-Komposition (`tools/context.py`) | Tool-Schicht (`tools/talk.py`) | `context.py` darf keinen eigenen Client haben (Gate), also komponiert es nur |
| Mail-Zähler im Bündel | Tool-Komposition (`tools/context.py`) | Tool-Schicht (`tools/mail.py`) | dito; die Projektion inklusive `marks`-Filterung liegt schon in der Tool-Schicht |
| Zeitbudget und Degradation je Quelle | Tool-Komposition | - | Der Vertrag von `context.py`: Wanduhr gleich Maximum der Teile, nie Summe |
| Provider-Id zu Kind | `provider_map.py` | - | Eine Übersetzungstabelle, kein Ort für Kind-Erfindung |
| Id-Codec (neue Kinds) | `ids.py` | - | Ein Codec plus Roundtrip-Test, sonst löst `fetch` eine Karte als Notiz auf |
| Auflösen eines Treffers | `tools/chatgpt.py` (`fetch`) | Client-Schicht (`clients/talk.py`, `clients/tables.py`) | `fetch` routet, die Clients sprechen HTTP; eine neue Talk-Route ist Client-Arbeit |
| Nebenwirkungsfreiheit der neuen Talk-Route | Client-Schicht (`READ_ONLY_PARAMS`-Muster) | Integrationstest | Die Route ist per Konstruktion nebenwirkungsfrei, der Beweis gehört live gemessen |
| Budget-Gate | `scripts/check_tool_budget.py` plus CI | Registrierungsschicht (`server/reg_*.py`) | Das Gate messt, die Diät passiert in den `Field`-Beschreibungen und Docstrings |
| Werkzeugzahl als Wahrheit | `tests/contract/test_tool_surface.py` | README, `docs/`, `scripts/acceptance_all_tools.py` | Die Zahl lebt in einem Test, nie in einem Dokument (bestehende Projektregel) |
| Version und Store-Metadaten | `pyproject.toml`, `__init__.py`, `appinfo/info.xml`, Git-Tag | `release.yml`, Store-Upload | Vier identische Strings plus Tag, zwei Gates halten das |

## Ist-Zustand, gelesen und gemessen

### 1. `tools/context.py` (342 Zeilen)

**Zwei Beine in einem `gather`** (`prepare_context`, Zeile 127): `search_tools.unified_search(limit=SEARCH_LIMIT=25)` und `_events()` unter `CALENDAR_BUDGET = 10.0`. `return_exceptions=True`, danach:

- `_hits()` schreibt bei Ausnahme `{"source": "search", "reason": ...}` und übernimmt die `degraded`-Einträge der Suche **unverändert**.
- `_bundle()` gruppiert nach `kind` in `BUCKETS = ("file", "note", "card", "other")`, kappt jeden Bucket bei `MAX_PER_BUCKET = 5` und schreibt je Kappung einen `degraded`-Eintrag.
- `_schedule()` kappt bei `MAX_EVENTS = 10`, ebenfalls mit `degraded`-Eintrag.
- **Die Doppelfehler-Regel** (Zeile 137): nur wenn **beide** Beine Ausnahmen sind, wird ein `ToolError` geworfen, damit ein leeres Bündel nie als "es gibt nichts" gelesen wird.
- `detail="full"` ergänzt bis `MAX_EXCERPTS = 3` Auszüge über `chatgpt_tools.fetch(max_bytes=EXCERPT_READ_BYTES=4000)`, je unter `EXCERPT_TIMEOUT = 5.0`, gekappt bei `EXCERPT_MAX_BYTES = 2000` mit Marker im Text.
- Antwortform: `{"query", "window": {"start","end"}, "events", "results", ["degraded"], "note"}`.
- `_reason()` kennt genau drei Fälle (ToolError, Timeout, RequestError) und **wirft alles andere weiter**: ein unbekannter Fehler bleibt laut.

**Die Zeile, die TOOL-16 blockiert** (`_short`, Zeile 221):

```python
if bucket == OTHER_BUCKET or hit.get("resolvable") is False:
    entry["resolvable"] = False
```

Ein Talk- oder Tables-Treffer landet heute im `other`-Bucket und bekommt damit `resolvable: False`, selbst wenn `provider_map` ihn nach TOOL-16 als auflösbar meldet. Entweder wachsen die `KIND_BUCKETS` um die neuen Kinds, oder diese Bedingung wird auf `hit.get("resolvable") is False` reduziert. Beides ist verteidigbar, eine Entscheidung ist Pflicht.

**Die Auszugsgrenze** (`_excerpts`, Zeile 268) zieht Ziele nur aus `KIND_BUCKETS`. Wenn die Buckets wachsen, wächst automatisch die Auszugsmenge auf Talk- und Mail-Inhalte, und genau davor warnt die Meilenstein-Recherche (`.planning/research/ARCHITECTURE.md:296`): ein Mail-Body ist der von außen am leichtesten beschreibbare Text im ganzen System. Empfehlung: eine eigene Konstante `EXCERPT_KINDS = ("file", "note", "card")` einführen und `_excerpts` darauf umstellen, unabhängig davon, wie die Bucket-Frage entschieden wird.

### 2. `provider_map.py` (140 Zeilen) und `ids.py` (122 Zeilen)

`PROVIDER_KINDS` kennt heute drei Einträge: `files` zu `file`, `notes` zu `note`, `search-deck-card-board` zu `card`. Alles andere wird `UNKNOWN_KIND = "url"`, `canonical=False`. `absolute_url()` erhält Pfad, Query **und Fragment** und verwirft die Herkunft; der Modul-Docstring nennt `#message_42` als Beispiel, warum das Fragment überlebt. `_last_numeric_segment()` liest ausschließlich `urlsplit(url).path`, also nie ein Fragment.

`ids.parse` kennt `file`, `note`, `card` (1 oder 3 Segmente), `event` (2 Segmente), `mail` (nur ASCII-Ziffern, `_DIGITS.fullmatch`) und `url`. `_join()` verbietet den Separator in Segmenten. Der Hinweistext `_HINT` listet alle Kinds und wird bei jeder Erweiterung mitgezogen.

`chatgpt.fetch` hat fünf Zweige plus `_UNFETCHABLE` für `url`. Jeder Zweig ist dünn: `require_app`, ein Client-Aufruf, `marks.without_marks` über den fremden Text, Projektion auf `{id, title, text, url, metadata}`. `metadata` ist **flach `dict[str, str]`**, weil `search` und `fetch` die einzigen Werkzeuge mit Output-Schema sind.

### 3. Die beiden fremden Provider (Quellcode verifiziert)

| Provider-Id | Quelle | Was mitkommt |
|-------------|--------|--------------|
| `talk-message` | `nextcloud/spreed`, `lib/Search/MessageSearch.php` (master), `getId()` gibt `'talk-message'` | `attributes`: `conversation`, `messageId`, `threadId`, `actorType`, `actorId`, `timestamp`; `resourceUrl` über `spreed.Page.showCall` mit `'_fragment' => 'message_' . $id` |
| `tables-search-tables` | `nextcloud/tables`, `lib/Search/SearchTablesProvider.php` (main) | **Keine** `attributes`. `getInternalLink()` baut `...page.index` plus `'#/' . $nodeType . '/' . $nodeId`, mit `$nodeType` gleich `table` **oder** `view` |

Konsequenzen:

- Talk braucht **keine** Fragment-Auswertung: `attributes.conversation` und `attributes.messageId` sind der direkte Weg, das Fragment ist die Gegenprobe (siehe Pitfall 7).
- Tables braucht die Fragment-Auswertung, und sie muss `table` von `view` unterscheiden. `view` bleibt `url`, weil der Tables-Client nur Tabellen liest (`get_table`, `get_columns`, `get_rows_simple` bauen alle `tables/{id}`-Pfade; die View-Routen `views/{id}` existieren im Client nicht).
- Ein zweiter Talk-Provider `talk-message-current` (Nachrichten der gerade offenen Konversation) und `talk-conversations` existieren laut Meilenstein-Recherche. TOOL-16 nennt nur `talk-message`. Empfehlung: `talk-message-current` mitnehmen, wenn er dieselben Attribute trägt (im Plan mit einer Zeile prüfen), `talk-conversations` bleibt `url`, weil eine Konversation kein Dokument ist.

### 4. Die Talk-Route für eine einzelne Nachricht (verifiziert gegen spreed v24.0.4, die Version auf dieser Instanz)

Es gibt **kein** `GET /chat/{token}/{messageId}`. Die Routen mit `{messageId}` sind: `GET .../context`, `GET|POST|DELETE .../reminder`, `DELETE .../{messageId}`, `PUT .../{messageId}`, `POST|DELETE .../pin`. Der einzige Leseweg ist der Kontext:

```
GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}/{messageId}/context?limit=<n>
```

Gemessen am Quellcode von **v24.0.4**:

- Signatur `getMessageContext(int $messageId, int $limit = 50, int $threadId = 0)`, `$limit = min(100, max(0, $limit))`, `$historyLimit = max(1, $limit)`.
- Historie: `getHistory($room, $messageId, $historyLimit, true, $threadId)`, das vierte Argument ist `includeLastKnown`, also **die Zielnachricht selbst kommt mit**.
- Zukunft: `waitForNewMessages($room, $messageId, $limit, 0, $currentUser, false, threadId: ...)`, also **Timeout 0** (kein Long-Poll) und `markNotificationsAsRead: false`.
- Kein `updateLastReadMessage`, kein Lesemarker.
- Attribute der Methode: `#[FederationSupported] #[PublicPage] #[RequireModeratorOrNoLobby] #[RequireParticipant]`. **Keine** `#[BruteForceProtection]`, **keine** `#[UserRateLimit]` (im Unterschied zu `RoomController::getSingleRoom`, dem Grund für das Listen-Muster aus Phase 9).
- Leere Antwort ist **304** ohne Body, genau wie bei `get_messages` schon behandelt.

Damit gilt: `limit=1` liefert die Zielnachricht plus höchstens eine neuere. Der Zielsatz ist über die `id` zu filtern, und ein Treffer, der nicht dabei ist, muss abgelehnt werden statt eine Nachbarnachricht auszugeben.

### 5. Budget-Gate, gemessen am 2026-08-24

`uv run --no-sync python scripts/check_tool_budget.py`: **15736 Bytes, 21 Tools, Budget 18500.** Zwei Gates im Skript: `BUDGET_BYTES = 18_500` (Gesamtsumme, ausdrücklich als Zwischenstand markiert, mit dem Verweis auf TOOL-15) und `MAX_TOOL_BYTES = 1400` (Obergrenze je Werkzeug, in Bytes seit 2026-08-21).

Vollständige Messung je Werkzeug (Bytes, kompaktes JSON, UTF-8):

| Bytes | Werkzeug | | Bytes | Werkzeug |
|------:|----------|-|------:|----------|
| 1377 | mail_browse | | 678 | unified_search |
| 1351 | calendar_create_event | | 648 | talk_send |
| 951 | calendar_list_events | | 644 | notes_create |
| 924 | search | | 625 | prepare_context |
| 886 | talk_browse | | 538 | files_list |
| 877 | deck_create_card | | 501 | files_upload |
| 780 | tables_create_row | | 501 | files_read |
| 772 | tables_browse | | 487 | contacts_search |
| 761 | fetch | | 478 | notes_search |
| 736 | deck_browse | | 339 | notes_read |
| 703 | files_search | | | |

Die fünf neuen Werkzeuge des Meilensteins zusammen: `mail_browse` 1377, `talk_browse` 886, `tables_create_row` 780, `tables_browse` 772, `talk_send` 648, also **4463 Bytes und 28,4 Prozent der ganzen Oberfläche**. `mail_browse` liegt 23 Bytes unter der Obergrenze je Werkzeug.

**Die Arithmetik der Verankerung, exakt gerechnet:**

| Messung nach der Diät | Regel (mal 1,15) | Aufgerundet auf 500 | Trifft die Erwartung von TOOL-15 |
|----------------------:|-----------------:|--------------------:|----------------------------------|
| 15736 (heute) | 18096,4 | **18500** | nein, das ist der Zwischenstand |
| 15652 | 17999,8 | **18000** | ja (obere Kante) |
| 15218 bis 15652 | 17500,7 bis 17999,8 | 18000 | ja |
| 14783 bis 15217 | 17000,5 bis 17499,6 | **17500** | ja (untere Kante) |
| 14782 oder weniger | 16999,3 | 17000 | nein, unter der Erwartung |

Daraus folgt der Auftrag in Zahlen: **mindestens 84 Bytes einsparen für 18000, mindestens 519 Bytes für 17500.** Jede Erweiterung der `prepare_context`-Beschreibung (die aus Ehrlichkeit nötig sein kann, sobald das Bündel Talk und Mail trägt) arbeitet gegen diese Zahl und muss gegengerechnet werden.

### 6. Annotations-Stand der fünf neuen Werkzeuge (verifiziert in `server/reg_*.py`)

| Werkzeug | Annotation | Datei |
|----------|------------|-------|
| `tables_browse` | `READ_ONLY` | `reg_tables.py` |
| `talk_browse` | `READ_ONLY` | `reg_talk.py:27` |
| `mail_browse` | `READ_ONLY` | `reg_mail.py:33` |
| `tables_create_row` | `CREATE_ONLY` | `reg_tables.py` |
| `talk_send` | `CREATE_ONLY` | `reg_talk.py:62` |

Drei lesend, zwei anlegend, wie TOOL-15 es verlangt. `READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)`, `CREATE_ONLY` setzt zusätzlich `destructive_hint=False` und `idempotent_hint=False` (`server/__init__.py:54`). Die Aussage ist also heute schon wahr; TOOL-15 verlangt den **Nachweis** in den Contract-Tests, und der steht dort bereits (`test_every_tool_carries_honest_annotations` vergleicht gegen die eingefrorene Menge `CREATE_TOOLS` mit sechs Einträgen).

### 7. Contract-Tests: wo die Zahl 21 steht und was bricht

`tests/contract/test_tool_surface.py`:

- `EXPECTED_TOOLS` (Zeile 37): eingefrorene Menge mit 21 Namen, Mengengleichheit statt Teilmenge.
- `CREATE_TOOLS` (Zeile 65): sechs Schreibwege.
- `STRUCTURED_TOOLS = {"search", "fetch"}`.
- `test_the_curated_set_is_complete...`: `assert len(tools) == 21`.
- `test_prepare_context_is_listed_as_a_bundling_read` (Zeile 456): prüft `set(properties) == {"query", "detail"}`, kein `$defs`, `detail` als `string`, die Werte `short`/`full` in der Beschreibung, und die Wendung **"third parties"** in der Beschreibung. **Eine neue Beschreibung darf diesen Satzteil nicht verlieren.**
- `test_the_readme_permission_table_matches_the_live_registry` (Zeile 666): liest `README.md`-Zeilen, die mit ``| ` `` beginnen, und vergleicht Name und Stufe mit der Registry. **Nur `README.md`, nicht die beiden Übersetzungen.**
- `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from` (Zeile 688): jede Seite in `docs/` und `README.md`, die eine Tool-Zahl nennt, muss entweder die aktuelle nennen oder auf `tests/contract/test_tool_surface.py` verweisen. Regex `tools=(\d+)|(\d+)\s+tools\b`.

`tests/unit/test_tools_context.py` (786 Zeilen) enthält zwei Gates, die den Entwurf der neuen Beine bestimmen:

- `test_this_module_reads_no_content_of_its_own` (Zeile 772): grept `context.py` nach `AsyncClient`, `clients.client`, `clients.creds`, `ocs.`, `dav.`, `caldav` und lässt `httpx` nur als `import httpx` oder in einer `isinstance`-Zeile zu. **Direkter Client-Zugriff in `context.py` ist damit verboten.**
- `test_no_sentence_of_this_module_frames_foreign_text_as_a_wish_of_the_user` (Zeile 764): verbietet die Formulierungen "the user wants", "the user asked for", "please do", "you must" im Modul.
- `test_short_stays_exactly_short` (Zeile 707) prüft die Schlüsselmenge **eines Treffers**, nicht der Antwort, bleibt also von neuen Top-Level-Feldern unberührt.
- `test_an_injected_instruction_arrives_as_data_and_moves_no_key_of_the_answer` (Zeile 721) vergleicht `set(result) == set(control)` **zwischen zwei Läufen derselben Fassung**, bricht also nicht an neuen Feldern, wohl aber an Feldern, die nur manchmal erscheinen und von fremdem Text abhängen.

`scripts/acceptance_all_tools.py` trägt eine **zweite Kopie** der 21 Namen (`expected`, Zeile 443) und die irreführende SKIP-Zeile aus IN-04 (Zeile 292 bis 303). Der Tech-Debt-Eintrag "acceptance_all_tools-Zählung" aus den Future Requirements gehört laut Requirements-Datei zu TOOL-15. Ehrlichster Fix: die Liste nicht doppelt pflegen, sondern gegen `client.list_tools()` prüfen.

### 8. Release-Runbook, Schritte 4 bis 8 (`docs/store-submission.md:159` bis 255)

| Schritt | Was er verlangt | Proof-Zeile in der Tabelle |
|---------|-----------------|----------------------------|
| 1 bis 3 (Vorlauf, in dieser Phase Teil der Code-Pläne) | Version an vier Stellen gleich (`pyproject.toml` `version`, `src/mcp_connector/__init__.py` `__version__`, `appinfo/info.xml` `<version>` und `<image-tag>`), Changelog-Block plus die zwei Link-Referenzen, alle Gates lokal grün (`pytest`, `ruff check`, `ruff format --check`, `pyright`, `vulture`, `check_tool_budget.py`) | keine eigene Zeile, aber der Grund für Schritt 4 |
| 4 | `git tag v<version>` und `git push origin v<version>`. **Irreversibel in der Öffentlichkeit.** Nur nach Owner-Freigabe | Workflow-Lauf ist grün, mit Run-Id (`gh run view <id>`) |
| 5 | Auf `release.yml` warten: Multi-Arch-Image nach `ghcr.io/street1983nk/mcp_connector:<version>`, Store-Archiv gebaut und an das GitHub-Release gehängt. Nicht weitermachen, solange rot | dieselbe Zeile wie Schritt 4 |
| 6 | Das **veröffentlichte** Asset herunterladen und genau diese Bytes signieren (`tar.gz` ist nicht byte-reproduzierbar), `openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key` plus Base64 | Downloadgröße mit 200, plus `Verified OK` der Signatur gegen das Zertifikat |
| 7 | Download-URL und Signatur an den Store: Formular oder `POST /api/v1/apps/releases` aus dem Seitenkontext der angemeldeten Store-Sitzung. **201 heißt akzeptiert.** Braucht die Store-Sitzung, nicht zwingend einen Menschen an der Tastatur | "Der Store hat das Release akzeptiert", HTTP 201 |
| 8 | Vier Nachweise laufen lassen und **jeden mit Datum in die Tabelle schreiben**: `appapi_apps.json` nennt die Release-Zeile mit demselben Platform-Span, `curl -I` auf das Asset (der Nachweis gegen ein gelöschtes Asset, nicht optional), GHCR-Manifest ist ein echter OCI-Index mit amd64 und arm64, GHCR-Tag-Liste enthält jeden Tag | vier Zeilen |

Nebenbedingungen aus derselben Datei, beide dauerhaft: **niemals ein Release-Asset löschen, niemals einen Tag umschreiben** (AppAPI installiert von unserer URL), und **eine Korrektur kostet eine neue Patch-Version**. Und die Cache-Notiz: eine Änderung, die eine Minute nach dem Upload nicht sichtbar ist, ist nicht verloren und darf nicht mit einem weiteren Release verfolgt werden. 0.1.5 und 0.1.6 wurden für genau diesen Fehler ausgegeben.

Vorhandene Voraussetzungen, geprüft: `~/.nextcloud/certificates/mcp_connector.key` und `.crt` liegen lokal, `gh` 2.92.0, `openssl` 3.5.6, `curl` 8.19.0, `tar` 1.35 sind installiert, `release.yml` erzwingt die Gleichheit von Tag und `<version>` (Zeile 48 bis 59) und triggert auf `tags: v*`.

### 9. Changelog-Zustand (IN-02 im Detail)

Sektionen: `[Unreleased]` (trägt heute den vollständigen Mail-Block der Phase 10), dann `[0.1.7]`, `[0.1.6]`, **`[0.1.4]`** und weiter. Link-Definitionen existieren für `[0.1.5]` und `[0.1.6]`, die Sektion `[0.1.5]` fehlt. Der Tag `v0.1.5` existiert nachweislich (Proof-Tabelle, 2026-08-22 10:59Z, Run `32569019469`), also ist die Nachtragung der Sektion der richtige Weg, nicht die Korrektur der Links.

## Standard Stack

### Core

**Keine neue Abhängigkeit.** Diese Phase benutzt ausschließlich, was `pyproject.toml` bereits pinnt.

| Baustein | Version im Repo | Verwendung in dieser Phase |
|----------|-----------------|----------------------------|
| mcp (offizielles SDK) | `>=2.0,<3` | `Client(mcp)` für Budgetmessung und Contract-Tests |
| httpx | 0.28.x | die beiden neuen Leseaufrufe über die bestehenden Client-Module |
| pytest, pytest-asyncio, respx | wie im Lock | Unit-Tests mit Request-Zählern |
| ruff, pyright, vulture | wie im Lock | Gates |

### Supporting

| Werkzeug | Verwendung |
|----------|------------|
| `uv run --no-sync` | jeder lokale Lauf; das globale System-Python ist unbrauchbar (Projekt-Constraint) |
| `docker compose -f compose.exapp.yml` | die laufende HaRP-Topologie für die Live-Messungen |
| `gh`, `openssl`, `curl`, `tar` | Release-Schritte 4 bis 8 |

### Alternatives Considered

| Statt | Möglich wäre | Preis |
|-------|--------------|-------|
| Zwei neue `gather`-Beine | Keine neuen Beine, nur neue Buckets (Empfehlung der Meilenstein-Recherche, `ARCHITECTURE.md:291`) | Erfüllt CTX-01 und CTX-02 **nicht**: "ungelesen" ist keine Volltextfrage und über die Suche nicht ausdrückbar. Die Requirements haben diese Empfehlung überstimmt, der dort genannte Preis (zwei bis drei zusätzliche Runden in **jedem** Aufruf) bleibt aber wahr und muss gemessen werden |
| Talk-Nachricht über `.../context` lesen | `get_messages` mit `lastKnownMessageId = messageId + 1` und `limit=1` | Rät: die Antwort ist die höchste Id unterhalb der Grenze, also bei einer gelöschten oder gefilterten Zielnachricht **eine andere Nachricht**, ohne dass es jemand sieht. Verstößt gegen die Projektregel "niemals ein Kind oder eine Id raten" |
| Tabellen-Treffer über `#/table/<id>` auflösen | Jeden Tables-Treffer auflösen | `#/view/<id>` existiert und ist mit dem heutigen Client nicht lesbar; ein geratener Tabellen-Id wäre eine falsche Tabelle |
| Mail-Treffer bleiben `url` | Deep-Link-Auflösung versuchen | Ungemessen, ausdrücklich Future Requirement |

**Installation:** keine.

## Package Legitimacy Audit

**Nicht anwendbar:** diese Phase installiert kein einziges externes Paket. `pyproject.toml` und `uv.lock` bleiben unberührt (dieselbe Aussage wie in Plan 10-08, dort per `git diff` nachgewiesen). Sollte im Plan doch ein Paket auftauchen, greift das Gate: `slopcheck install <pkg> --json`, danach `pip index versions <pkg>` gegen PyPI, und ohne verfügbares slopcheck gilt jedes Paket als `[ASSUMED]` mit `checkpoint:human-verify` vor der Installation.

## Architecture Patterns

### System Architecture Diagram

```
MCP-Client
   |
   v
prepare_context(query, detail)                     [tools/context.py, KEIN eigener Client]
   |
   +-- Bein 1: search_tools.unified_search(limit=25)          eigenes Timeout je Provider (15 s)
   |      -> provider_map.extract_id je Eintrag
   |         files->file  notes->note  deck->card
   |         talk-message->message [NEU, aus attributes]
   |         tables-search-tables + #/table/<id> ->table [NEU]
   |         tables ... #/view/<id>, mail, Rest -> url (ehrliche Restkategorie)
   |      -> _bundle: Buckets a MAX_PER_BUCKET=5, jede Kappung schreibt degraded
   |
   +-- Bein 2: _events()                                       CALENDAR_BUDGET = 10 s
   |
   +-- Bein 3 [NEU]: talk_tools.browse(level="conversations")   TALK_BUDGET, 1 Request
   |      -> filtern auf unread>0 oder unread_mention, max 3
   |      -> last_message erneut auf ~200 kappen
   |      -> ToolError (App fehlt, Timeout) => genau ein degraded-Eintrag
   |
   +-- Bein 4 [NEU]: mail_tools.browse(level="accounts")        MAIL_BUDGET, 1 + N Requests
   |      -> je Konto browse(level="mailboxes"), Inbox-Zaehler, nur Zahlen
   |      -> ToolError => genau ein degraded-Eintrag
   |
   +-- detail="full": _excerpts nur ueber EXCERPT_KINDS = (file, note, card)  [NEU begrenzt]
          -> chatgpt.fetch(max_bytes=4000), eigenes 5-s-Budget je Auszug

fetch(id)                                          [tools/chatgpt.py]
   |
   +-- file: / note: / card: / event: / mail:       (unveraendert)
   +-- message:<token>:<messageId>  [NEU] -> Token gegen die eigene Konversationsliste pruefen,
   |                                          dann GET .../chat/{token}/{messageId}/context?limit=1
   |                                          -> genau die Zielnachricht filtern, sonst ablehnen
   +-- table:<tableId>             [NEU] -> get_table (Titel, rowsCount) + get_rows_simple(limit)
   |                                          -> Zeilen als Text, gekappt und markiert
   +-- url:                                (ehrlich: "oeffne die URL")
```

Der Datenfluss der beiden neuen Beine geht **nie** direkt in die Client-Schicht: das ist die Bedingung, die `test_this_module_reads_no_content_of_its_own` erzwingt, und sie hat einen zweiten Nutzen. Die Projektion in der Tool-Schicht filtert fremden Text schon durch `marks.without_marks` (`talk_tools._text`, `_resolve`, `_preview`), also erbt der Digest die Marker-Hygiene, statt sie ein zweites Mal zu implementieren.

### Empfohlene Dateiaufteilung (keine neuen Module)

```
src/mcp_connector/
├── tools/context.py       # zwei neue Beine, zwei neue Budgets, EXCERPT_KINDS
├── tools/chatgpt.py       # zwei neue fetch-Zweige
├── tools/talk.py          # (evtl.) eine Projektion fuer eine einzelne Nachricht
├── provider_map.py        # zwei Provider, ein Fragment-Leser
├── ids.py                 # zwei Kinds, _HINT nachziehen
├── nextcloud/clients/talk.py    # get_message_context (die einzige neue Route)
├── server/reg_context.py  # Beschreibung ehrlich halten, Bytes gegenrechnen
└── server/reg_mail.py, reg_talk.py, reg_tables.py  # Schema-Diaet
scripts/check_tool_budget.py     # neue Messzeile, neues BUDGET_BYTES
```

### Pattern 1: Ein Bein je Quelle, Budget je Bein, Degradation mit Namen

**Was:** Jede neue Quelle bekommt eine eigene Konstante als Zeitbudget, läuft in `asyncio.gather(..., return_exceptions=True)` und wird bei Ausnahme über `_reason()` zu **einem** Satz unter `degraded`.
**Wann:** Für jede der beiden neuen Quellen.
**Beispiel (Muster aus dem Bestand, `tools/context.py:166`):**

```python
CALENDAR_BUDGET = 10.0

async def _events(clients: NcClients, start: str, end: str) -> dict[str, Any]:
    """Der Kalenderpfad, unter der Decke dieses Werkzeugs statt der des anderen."""
    async with asyncio.timeout(CALENDAR_BUDGET):
        return await calendar_tools.list_events(clients, start=start, end=end, limit=MAX_EVENTS)
```

Wichtig: `_reason(exc, subject, budget)` wirft alles, was nicht ToolError, Timeout oder RequestError ist, weiter. Ein neuer Fehlertyp wird also **laut**, und das soll so bleiben.

### Pattern 2: Die Doppelfehler-Regel nicht verwässern

`prepare_context` wirft heute nur dann einen Fehler, wenn **Suche und Kalender** beide ausgefallen sind. Die neuen Beine dürfen diese Bedingung nicht betreten: ein Bündel, in dem nur Talk geantwortet hat, ist kein Erfolg, und ein Bündel ohne Talk auf einer Instanz ohne Talk ist kein Fehler. Empfehlung: die Bedingung wörtlich auf die beiden bestehenden Beine beschränken und diese Absicht im Docstring benennen, weil sie sonst beim nächsten Bein wieder zur Frage wird.

### Pattern 3: Jede Kappung schreibt ihren eigenen `degraded`-Eintrag

Der Digest kappt zweimal (drei Konversationen von M, Vorschau bei ~200) und die Mail-Seite mindestens einmal (Kontenzahl, falls gekappt). Die bestehende Regel lautet: eine Liste, die still fünf Einträge lang ist, ist das eine Ergebnis, das ein Modell als "das ist alles" weitergibt. Also: Kappung der Konversationsliste mit Gesamtzahl benennen, wie `talk_tools._conversations` es mit `total` schon tut.

### Pattern 4: Neue Id-Kinds, drei Stellen und ein Roundtrip

`ids.encode_*` plus `ids.parse` plus `_HINT`, dann `provider_map.PROVIDER_KINDS` und ein Zweig in `extract_id`, dann `case` in `chatgpt.fetch`. Der Test `test_ids.py` hält den Roundtrip, `test_provider_map.py` die Extraktion, `test_chatgpt_fetch.py` die Auflösung. Vorbild ist Plan 10-05 mit `mail:` und dem ASCII-Ziffern-Guard.

Namensvorschlag mit Begründung: `message:<token>:<messageId>` (die Meilenstein-Recherche nennt genau diese Form; der Token ist `[a-z0-9]{4,30}`, kollidiert also nie mit dem Separator) und `table:<tableId>`. Der Plan darf andere Namen wählen, muss dann aber `_HINT`, drei READMEs und die Doku in einem Zug mitziehen.

### Pattern 5: Ein Token aus einem Modell wird gegen die eigene Liste geprüft

`talk_tools._room()` (Zeile 587) holt die Konversationsliste und sucht den Token darin, statt `GET /room/{token}` zu rufen. Für die Kontext-Route ist der Grund von Phase 9 (Brute-Force-Zähler) **nicht** gegeben, `#[RequireParticipant]` antwortet mit 404 aus der Middleware. Der Nutzen bleibt: der eigene Satz statt eines fremden 404, und der Anzeigename der Konversation für Titel und Link. Preis: ein zusätzlicher Request je `fetch`. Empfehlung: den Preis zahlen und im Docstring benennen, weil es das Muster der Familie ist.

### Pattern 6: Vier Versionsstellen plus Tag, gehalten von zwei Gates

`tests/unit/test_exapp_env_setup.py` vergleicht `<version>` mit `mcp_connector.__version__` und `<image-tag>` mit `<version>`; `release.yml` verweigert einen Tag-Push, dessen Tag nicht `<version>` entspricht. Der Tag ist der dritte identische String, und `milestone-v*` ist für Meilensteine reserviert.

### Anti-Patterns

- **Ein eigener Client in `context.py`.** Gate `test_this_module_reads_no_content_of_its_own` wird rot, und die Marker-Filterung der Tool-Schicht ginge verloren.
- **Ein globales Timeout um das `gather`.** Wirft eine schon fertige Antwort weg. Der Modul-Docstring sagt es, das Gate ist die Messung.
- **Das Budget anheben, weil es nicht passt.** Die Datei sagt selbst: Anheben nur zusammen mit einer neuen Messzeile, und `MAX_TOOL_BYTES` ist das eigentliche Gate. `mail_browse` war 1585 Bytes und wurde gekürzt, nicht ausgenommen.
- **Ein Betreff im Standardbündel.** CTX-02 sagt "nur Zahlen". Ein Betreff ist fremder Text von jemandem, der keine Nextcloud-Berechtigung braucht.
- **`view` als `table` auflösen.** Ein geratener Tabellen-Id liest eine andere Tabelle.
- **Eine zweite Kopie der Werkzeugliste pflegen.** `scripts/acceptance_all_tools.py` hat sie heute; TOOL-15 ist die Gelegenheit, sie gegen die Registry zu ersetzen statt sie zu aktualisieren.

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Konversationen sortieren, filtern, projizieren | Eine zweite Projektion im Digest | `talk_tools.browse(level="conversations")` | Die Liste hat kein `ORDER BY` und 59 Pflichtfelder; die Regel "sortieren, filtern, kappen" steht dort begründet |
| Fremden Text von eigenen Markern befreien | Ein eigener Filter im Digest | `marks.without_marks` über die Tool-Schicht | Genau der Angriff, gegen den BL-09 und ME-03 stehen |
| Ungelesen-Zähler aus Nachrichten ableiten | Envelopes zählen | `unread` der Postfachliste | Gemessen: ein Request je Konto, und das Navigationsfeld lügt (steht auf 0 bei sechs ungelesenen) |
| Eine einzelne Talk-Nachricht adressieren | `lastKnownMessageId`-Arithmetik | `GET .../{messageId}/context?limit=1` | Die einzige Route, die genau diese Nachricht garantiert liefert, und sie ist nebenwirkungsfrei per Konstruktion |
| Fragment-Ids parsen | Eine eigene URL-Zerlegung | `urlsplit(...).fragment`, gebaut auf `provider_map.absolute_url`, die das Fragment schon erhält | Die Herkunft muss verworfen werden, das macht `absolute_url` bereits |
| Tabellenzeilen lesbar machen | Eigene Zeilenformatierung mit Spaltenauflösung | `get_rows_simple` (die erste Liste sind die Spaltentitel) | Spart die Spaltenrunde und ist die dokumentierte kompakte Form |
| Timeout-Klassifikation | Eigene `except`-Kette | `context._reason` | Drei Fälle, wörtlich gleich mit `tools/search.py`, alles andere bleibt laut |
| Paging-Handles | Eigene Cursor | `paging.encode_cursor` / `check_scope` | Ein Handle einer anderen Ebene wird abgelehnt statt still ignoriert |

**Key insight:** Diese Phase ist zu 90 Prozent Komposition. Jede Zeile, die eine bestehende Entscheidung neu trifft, ist eine zweite Wahrheit, die beim nächsten Nextcloud-Update auseinanderläuft.

## Runtime State Inventory

Diese Phase ist keine Umbenennung, aber sie **veröffentlicht**, und das erzeugt Zustand außerhalb des Repositories. Die Kategorien sind deshalb ausgefüllt.

| Kategorie | Gefunden | Erforderliche Handlung |
|-----------|----------|------------------------|
| Gespeicherte Daten | Keine Datenmigration. Der Store speichert Metadaten und eine URL, nicht das Archiv. Ein `occ app_api:app:update` behält das Volume (`removeData: false`), also überleben Autorisierungen und Tokens | keine |
| Live-Dienst-Konfiguration | Store-Eintrag `mcp_connector` auf apps.nextcloud.com: Beschreibung, Kategorien und Spendenlinks kommen **beim Upload** in die Seite, nicht auf einem Zeitplan. Der neue PayPal-Link wird erst mit 0.1.8 sichtbar | Release 0.1.8 hochladen, Sichtbarkeit in der Store-Seite prüfen (Cache-Notiz beachten) |
| OS- und Registry-Zustand | GHCR-Tags `0.1.0` bis `0.1.7` existieren, keiner wurde umgeschrieben; Git-Tags `v0.1.0` bis `v0.1.7`; die laufende Test-Topologie (`nc-mcp-exapp-nc`, `nc_app_mcp_connector`, `nc-mcp-exapp-harp`, `nc-mcp-exapp-caddy`, `nc-mcp-exapp-registry`, `nc-mcp-exapp-greenmail`) läuft gerade | Tag `v0.1.8` **nur nach Owner-Freigabe**, danach GHCR-Tag `0.1.8` als vierten Proof prüfen. Kein Tag umschreiben, kein Asset löschen |
| Secrets und Env-Variablen | `~/.nextcloud/certificates/mcp_connector.key` und `.crt` liegen lokal (geprüft); der Store-Token lebt nur in der Browser-Sitzung und ist ausdrücklich **kein** Repository-Secret; `.env.exapp` existiert für die Integrationsläufe | keine Änderung; Signatur wird bei Bedarf neu berechnet, nie aufgeschrieben |
| Build-Artefakte | `dist/mcp_connector-<version>.tar.gz` wird lokal beim optionalen Probelauf gebaut und ist **nicht** das Artefakt, das signiert wird (Nachweis 2026-08-20: 31909 gegen 32168 Bytes, unterschiedliche sha256) | Immer das heruntergeladene Release-Asset signieren |

## Common Pitfalls

### Pitfall 1: `resolvable: False` im `other`-Bucket macht TOOL-16 im Bündel unwirksam
**Was schiefgeht:** `provider_map` löst Talk und Tables auf, `fetch` liest sie, aber `prepare_context` weist dieselben Treffer weiter als unauflösbar aus, weil `_short()` das für den gesamten `other`-Bucket setzt.
**Warum:** Die Zeile wurde geschrieben, als "nicht in `KIND_BUCKETS`" gleichbedeutend mit "nicht auflösbar" war. TOOL-16 bricht diese Äquivalenz.
**Vermeidung:** Entweder `KIND_BUCKETS` um die neuen Kinds erweitern (dann `EXCERPT_KINDS` separat einführen, sonst wandern Talk- und Mail-Inhalte in die Auszüge) oder die Bedingung auf `hit.get("resolvable") is False` reduzieren.
**Warnzeichen:** Ein Testfall mit einem Talk-Treffer im Bündel, der `resolvable` trägt, obwohl `fetch` ihn auflöst.

### Pitfall 2: Die Budget-Regel liefert 18500, nicht 17500 bis 18000
**Was schiefgeht:** Der Plan verankert mechanisch auf die alte Messung und schreibt dieselbe Zahl noch einmal hin, obwohl TOOL-15 eine Neuverankerung meint.
**Warum:** 15736 mal 1,15 ist 18096, aufgerundet 18500, also exakt der Zwischenstand.
**Vermeidung:** Die Diät zuerst, die Messung danach, das Gate zuletzt. Zielmarken: 84 Bytes für 18000, 519 Bytes für 17500. Wenn die Diät die Marke nicht erreicht, ist das Ergebnis ehrlich als "Messung unverändert, Gate bleibt 18500" mit Begründung zu dokumentieren, statt eine Zahl zu erfinden.
**Warnzeichen:** Eine Messzeile ohne veränderte Messung.

### Pitfall 3: Die Beschreibung von `prepare_context` wird ehrlicher und kostet Bytes
**Was schiefgeht:** Das Bündel trägt Talk und Mail, die Beschreibung nennt sie nicht (heute: "files, notes, cards and the next week of events"), oder sie nennt sie in einem Absatz und frisst die Diät auf.
**Warum:** Jedes Byte einer Beschreibung wird in jeder Sitzung jedes Clients bezahlt; `prepare_context` liegt heute bei 625 Bytes.
**Vermeidung:** Eine kurze Aufzählung, und die Wendung **"third parties"** muss erhalten bleiben (Contract-Test). Änderung gegen die Budgetrechnung gegenprüfen.

### Pitfall 4: Ein direkter Client in `context.py` macht ein bestehendes Gate rot
**Was schiefgeht:** Der schnellste Weg zu einem Mail-Zähler wäre `mail_client.get_mailboxes(clients.client, clients.creds, ...)`. Das Modul-Gate grept genau darauf.
**Vermeidung:** Immer über `talk_tools.browse` und `mail_tools.browse`. Nebeneffekt: die Marker-Filterung und die `special_role`-Lesart kommen kostenlos mit.
**Warnzeichen:** `clients.client` oder `clients.creds` in `tools/context.py`.

### Pitfall 5: Die 1+N-Kosten sind in Wahrheit 1+N plus Erkennung
**Was schiefgeht:** Der Plan dokumentiert "1+N" und die Live-Messung zeigt mehr Requests.
**Warum:** `mail_tools.browse` ruft `capabilities.require_app("mail")`, und Mail wird über die Navigation erkannt (`GET /ocs/v2.php/core/navigation/apps`), zusätzlich zum allgemeinen Capabilities-Dokument. Beide Antworten liegen 60 Sekunden im Cache (`TTL_SECONDS = 60.0`), also fallen sie nur beim kalten Aufruf an.
**Vermeidung:** Die Messung als "1 Kontenliste plus N Postfachlisten, plus bis zu 2 Erkennungsrequests bei kaltem Cache" aufschreiben. Genau diese Ehrlichkeit ist der Unterschied zwischen gemessen und geschätzt.

### Pitfall 6: Bytes gegen Zeichen bei der ~200er-Kappe
**Was schiefgeht:** CTX-01 sagt "~200 Zeichen", das Projekt budgetiert überall in Bytes (`MAX_MESSAGE_BYTES = 800`, `MAX_PREVIEW_BYTES = 400`, `EXCERPT_MAX_BYTES = 2000`). Eine deutsche Vorschau mit Umlauten ist in Bytes kürzer als in Zeichen.
**Vermeidung:** Eine Entscheidung treffen, sie an einer Konstante festmachen und im Docstring sagen, welche Einheit gemessen wird und warum. `talk_tools._capped` schneidet auf Bytes und dekodiert tolerant, also ist der Byte-Weg der billigere Anschluss; dann heißt die Konstante `DIGEST_PREVIEW_BYTES` und nicht `..._CHARS`.

### Pitfall 7: Die Talk-Attribute können fehlen, das Fragment auch
**Was schiefgeht:** `extract_id` liest `attributes.conversation` und `attributes.messageId`, und ein Eintrag ohne beide wird zu `message:` mit leerem Segment oder zu einer geratenen Id.
**Warum:** Der Docstring von `provider_map` sagt es für die anderen Provider schon: `attributes` kommt als Objekt **oder** als leere Liste an, je nachdem, was die App setzt.
**Vermeidung:** Beide Wege prüfen (Attribute zuerst, Fragment `message_<id>` als Gegenprobe), und bei Zweifel `url` zurückgeben. Der `_join`-Guard in `ids.py` lehnt leere Segmente ohnehin ab, aber eine Ausnahme im Suchpfad wäre ein Fehler für einen einzelnen Treffer.

### Pitfall 8: Die Zielnachricht ist eine Systemnachricht oder gelöscht
**Was schiefgeht:** `fetch("message:<token>:<id>")` bekommt die Kontextantwort, die Zielnachricht ist aber vom Typ `system` und fällt durch `talk_tools.KEPT_TYPES`, oder sie existiert nicht mehr. Ein `text` aus der Nachbarnachricht wäre eine falsche Antwort.
**Vermeidung:** Genau auf die `id` filtern und bei Fehlen mit einem Satz plus nächstem Schritt ablehnen, wie `_fetch_event` es tut, wenn ein Kalenderobjekt kein Event trägt. Leere Antwort mit Erfolg ist die Form, die ein Modell zum Erfinden einlädt (Muster T-10-34).

### Pitfall 9: 304 auf der Kontext-Route
**Was schiefgeht:** Der geteilte OCS-Parser macht aus jedem 3xx "Nextcloud hat mit einer Weiterleitung geantwortet, prüfe die Basis-URL".
**Vermeidung:** Denselben lokalen Sonderfall wie in `get_messages` (`if response.status_code == httpx.codes.NOT_MODIFIED`). Verifiziert: `prepareCommentsAsDataResponse` antwortet 304 bei leerer Menge.

### Pitfall 10: `#/view/<id>` sieht aus wie eine Tabelle
**Was schiefgeht:** Der Fragment-Leser nimmt das letzte numerische Segment und baut `table:<viewId>`. Das liest eine fremde Tabelle oder antwortet 404.
**Vermeidung:** Den `nodeType` aus dem Fragment lesen und nur `table` akzeptieren; `view` bleibt `url`. Ein Testfall je Form.

### Pitfall 11: `MAX_TOOL_BYTES` hat 23 Bytes Luft
**Was schiefgeht:** Eine Formulierung in `mail_browse` wächst um zwei Wörter, das Gate wird rot, und die Reaktion ist eine Anhebung der Obergrenze.
**Vermeidung:** Die Datei sagt es selbst: ein Werkzeug, das die Decke erreicht, bekommt eine kürzere Beschreibung und nie eine höhere Grenze. Nach der Diät kann die Obergrenze sogar gesenkt werden, wenn `mail_browse` klar darunter landet, aber nur mit Messzeile.

### Pitfall 12: Die Tool-Zahl steht an vier Stellen
**Was schiefgeht:** 21 bleibt 21, aber Formulierungen wie "the 21 tools" in `README.md:19` und `:30` gelten nur, solange die Registry 21 sagt, und `docs/`-Seiten müssen entweder die aktuelle Zahl nennen oder auf den Contract-Test verweisen (Gate `test_a_documented_tool_count_...`).
**Vermeidung:** Wenn ohnehin an den READMEs gearbeitet wird (neue Id-Kinds), beide Zeilen mitlesen. Die Übersetzungen `README.de.md` und `README.fr.md` werden vom Tabellen-Gate **nicht** geprüft, sind also die Stelle, an der Drift unbemerkt bleibt (genau der Befund WR-05 aus Phase 10).

### Pitfall 13: Der Store-Cache verleitet zu einem zweiten Release
**Was schiefgeht:** Nach dem Upload ist die Änderung nicht sofort sichtbar, und die Reaktion ist 0.1.9.
**Vermeidung:** Die Cache-Notiz im Runbook: Detailseite, Katalog-Endpunkt und Suchindex aktualisieren Minuten auseinander. 0.1.5 und 0.1.6 wurden für diesen Fehler ausgegeben, das ist im Runbook dokumentiert.

### Pitfall 14: `v*` gegen `milestone-v*`
**Was schiefgeht:** Ein Meilenstein-Tag `v1.2` löst `release.yml` aus und versucht ein Release zu bauen, dessen Version nicht in `info.xml` steht.
**Vermeidung:** Meilensteine heißen `milestone-v1.2`. Steht in der Owner-Vorgabe und im Workflow-Trigger.

## Code Examples

### Ein Bein mit eigenem Budget, ausschließlich über die Tool-Schicht

```python
# Quelle: Muster aus src/mcp_connector/tools/context.py:166 (Kalenderbein)
TALK_BUDGET = 5.0          # Messung nachtragen, wie CALENDAR_BUDGET es tut
MAX_DIGEST = 3
DIGEST_PREVIEW_BYTES = 200

async def _talk(clients: NcClients) -> dict[str, Any]:
    """Die Konversationsliste, unter der Decke dieses Werkzeugs, ueber die Tool-Schicht."""
    async with asyncio.timeout(TALK_BUDGET):
        return await talk_tools.browse(clients, level="conversations", limit=talk_tools.MAX_CONVERSATIONS)
```

### Die Felder, die der Digest braucht, kommen aus einem Request

```python
# Quelle: src/mcp_connector/tools/talk.py:387 (_conversation), gelesen am 2026-08-24
entry = {
    "token": token,
    "name": _text(room.get("displayName") or ""),
    "unread": _number(room.get("unreadMessages")),
    "unread_mention": bool(room.get("unreadMention")),
    "unread_mention_direct": bool(room.get("unreadMentionDirect")),
    "last_activity": _number(room.get("lastActivity")),
    ...
}
preview = _preview(room.get("lastMessage"))   # bereits durch marks.without_marks gelaufen
```

Der Request dahinter: `get_rooms(..., include_last_message=True)` mit `params={"noStatusUpdate": 1, "includeLastMessage": True}` (`clients/talk.py:128`). **Ein** Request, wie CTX-01 es verlangt.

### Der Zähler, den CTX-02 braucht

```python
# Quelle: src/mcp_connector/tools/mail.py:328 (_mailbox)
entry = {
    "id": _number(raw.get("databaseId")),
    "name": name,
    "unread": _number(raw.get("unread")),
    "delimiter": _text(raw.get("delimiter") or ""),
}
role = _special_role(raw.get("specialRole"))   # "inbox", "sent", "drafts", "trash", "junk", ...
```

Also: Inbox ist `special_role == "inbox"`. Achtung auf die Kappung: `mail_tools.DEFAULT_LIMIT = 20`, `MAX_LIMIT = 50`, und die Postfachebene kappt in der Projektion. Ein Konto mit mehr als 50 Ordnern kann seine Inbox in der Antwort verlieren, wenn sie nicht vorne steht, deshalb mit `limit=mail_tools.MAX_LIMIT` fragen und die Grenze im Docstring benennen (Befund WR-03 aus Phase 10, dort als honest limit gelöst).

### Die neue Talk-Route im Muster der bestehenden Clients

```python
# Vorbild: src/mcp_connector/nextcloud/clients/talk.py:138 (get_messages)
async def get_message_context(
    client: httpx.AsyncClient, creds: Credentials, token: str, message_id: str, *, limit: int
) -> list[dict[str, Any]]:
    conversation = _path_token(token)
    response = await ocs.ocs_get(
        client, creds, f"{CHAT_PREFIX}/{conversation}/{int(message_id)}/context",
        params={"limit": min(max(int(limit), 1), MAX_MESSAGES)},
    )
    if response.status_code == httpx.codes.NOT_MODIFIED:
        return []
    payload = ocs.parse_ocs(response, what=f"the context of message {message_id}")
    return _as_list(payload, what="messages")
```

`READ_ONLY_PARAMS` gehören hier **nicht** hin: die Route nimmt sie nicht an, und sie ist per Konstruktion nebenwirkungsfrei (`timeout: 0`, `markNotificationsAsRead: false`, kein Lesemarker, verifiziert in v24.0.4). Diese Begründung gehört in den Docstring, sonst liest sie sich beim nächsten Review wie eine Auslassung.

### Der Fragment-Leser für Tables

```python
# provider_map.py: das Fragment ueberlebt schon, absolute_url baut es neu auf
from urllib.parse import urlsplit

_TABLES_NODE = re.compile(r"^/?(table|view)/([0-9]+)$")

def _tables_node(url: str) -> tuple[str, str] | None:
    """('table', '7') fuer #/table/7, ('view', '3') fuer #/view/3, sonst None."""
    match = _TABLES_NODE.match(urlsplit(url).fragment)
    return (match.group(1), match.group(2)) if match else None
```

## Messmethodik: wie CTX-01 und CTX-02 "gemessen statt geschätzt" werden

Die Topologie läuft gerade (`docker ps`: `nc-mcp-exapp-nc`, `nc_app_mcp_connector`, `nc-mcp-exapp-harp`, `nc-mcp-exapp-caddy`, `nc-mcp-exapp-registry`, `nc-mcp-exapp-greenmail`), inklusive GreenMail mit den sechs Testmails aus Plan 10-01 und `mail` 5.11.1, `spreed` 24.0.4, `tables` 2.2.2 alle aktiviert (Endzustand von Plan 10-08).

**Schicht 1, Unit mit Request-Zählern (respx).** Das Muster steht in `tests/unit/test_talk_tools.py`: Routen als `respx.Route` greifen und `route.call_count` behaupten. Damit werden die 1+N-Kosten deterministisch behauptet: "ein Konto, ein Postfachrequest", "drei Konten, drei Postfachrequests", "kein Request, wenn die App fehlt". Das ist die Zahl, die als Vertrag rot wird, wenn jemand ein Bein sequenziell doppelt aufruft.

**Schicht 2, Unit für die Gleichzeitigkeit.** `test_both_sources_run_at_the_same_time` (`test_tools_context.py:233`) lässt zwei Fakes aufeinander warten: eine sequenzielle Implementierung verklemmt und der Test fällt über sein eigenes Timeout. Dasselbe Muster für vier Beine.

**Schicht 3, Unit für Degradation je Quelle.** `test_a_stalling_calendar_is_named_and_the_search_hits_still_arrive` (Zeile 261) ist die Vorlage: ein stehendes Bein wird ein benannter `degraded`-Eintrag, die fertigen Treffer kommen an. Für Talk und Mail je eine Kopie, plus eine für "App fehlt" (der `ToolError` aus `capabilities.require_app`, dessen Satz in `capabilities._MISSING` steht und in `test_srv06_degradation.py` schon als Vertrag geprüft wird).

**Schicht 4, live gegen die Topologie.** Das Muster von `tests/integration/test_mail_read.py` und `test_srv06_degradation.py`: Marker `integration`, Skip mit dem Namen der fehlenden Umgebungsvariable, Messprotokoll über `-s`, Aufräumen im `finally`, Endzustand gemessen statt angenommen. Konkret zu messen:

1. **Wanduhr von `prepare_context`** mit `detail="short"` und `detail="full"`, mit allen vier Beinen, gegen die Referenz aus Plan 04-04 (0,84 s kurz, 0,99 s voll, `degraded` leer; die Zahlen stehen im Docstring von `context.py:60`). Die Aussage von CTX-01, "das bestehende Verhalten bleibt gemessen unverändert", ist genau dieser Vergleich.
2. **Requestzahl je Aufruf**, entweder über die Nextcloud-Zugriffslogs oder über einen httpx-Event-Hook im Testlauf.
3. **Der Digest an echten Daten:** die Instanz hat fünf Konversationen (Messung 10-08), die Changelog-Konversation ist oft die mit `unread == 1` bei leerer Historie (dokumentierte Falle T12 in `test_talk_roundtrip.py`), also ist sie der beste Testfall für "ein Zähler ist kein Nachrichtenzähler".
4. **Der Mail-Zähler an echten Daten:** ein Konto (`alice@example.test`, id 4), ein Postfach (`INBOX`, `special_role="inbox"`, `unread=6`). Also 1+1 Requests, und der Digest muss 6 sagen.
5. **Nebenwirkungsfreiheit des neuen Talk-Lesewegs:** `unreadMessages` und `unreadMention` der Zielkonversation vor und nach `fetch("message:...")`, gelesen über die **Konversationsliste** und nicht über die Kontext-Route. Die Regel aus Plan 10-08: die zu prüfende Operation darf nicht das Messwerkzeug sein.
6. **Ein `fetch` je neuem Kind** aus einem echten Suchtreffer, nie aus einer geratenen Id (dasselbe Prinzip wie beim sechsten Id-Kind in `scripts/acceptance_all_tools.py:325`).

Reproduktionsbefehle:

```bash
uv run --no-sync python scripts/check_tool_budget.py
uv run --no-sync pytest tests/unit tests/contract -q
set -a && . ./.env.exapp && set +a
uv run --no-sync pytest tests/integration/test_srv06_degradation.py -m integration -q -rA
```

## State of the Art

| Alt | Aktuell | Wann geändert | Wirkung auf diese Phase |
|-----|---------|---------------|-------------------------|
| Meilenstein-Empfehlung: kein neues `gather`-Bein, nur neue Buckets | CTX-01 und CTX-02 verlangen zwei Beine mit eigenem Budget und eigenem `degraded`-Eintrag | Roadmap v1.2, Erfolgskriterium 1 der Phase | Die Kostenwarnung der Recherche bleibt gültig und wird zur Messpflicht |
| `tables-search-tables` bleibt `url` (Empfehlung 08-RESEARCH) | TOOL-16 verlangt Auflösung über das Fragment | Requirements v1.2 | Nur `#/table/`, `#/view/` bleibt ehrlich `url` |
| Budget 15000 bei 20 Werkzeugen | 18500 bei 21, ausdrücklich Zwischenstand | Plan 10-06 | TOOL-15 verankert neu, mit Diät zuerst |
| `fetch` löst vier Id-Arten auf (READMEs vor Phase 10) | fünf Arten seit `mail:` (Commit `2c51cfc`) | Phase 10, Befund WR-05 | Nach dieser Phase sieben; alle drei READMEs plus der ChatGPT-Abschnitt sind die Driftstelle |
| Store-Beschreibung ohne Mail und ohne Ketten-Absatz | Beschreibung EN/DE/FR mit ehrlicher Ketten-Formulierung (Commit `6eb5d05`) | Phase 10, Befund CR-01 | Diese Texte werden erst mit 0.1.8 im Store sichtbar |
| PayPal-Spendenlink alt | `paypal.me/KhaledCherifDev` in `info.xml:208` (Commit `d36356d`) | 2026-08-24 | Wird mit 0.1.8 sichtbar, das ist der Anlass des Releases |

**Überholt und nicht mehr benutzbar:**

- Der Verweis "Reproduce with the command in 04-04-MEASUREMENTS.md" (`tools/context.py:65`) zeigt auf eine Datei, die im Repository nicht mehr existiert (die v1.0-Phasenverzeichnisse sind nicht mehr da; `find` findet keine `*MEASUREMENT*`-Datei). Wenn die Phase die Messung ohnehin wiederholt, ist das die Gelegenheit, den Verweis auf das neue Messdokument zu setzen.
- Die Tool-Zahl 16 in der Update-Tabelle des Runbooks ist ein Protokoll vom 2026-08-19 und darf so bleiben: die Seite verweist auf den Contract-Test als Wahrheit.

## Security Domain

`security_enforcement` ist in `.planning/config.json` nicht gesetzt, gilt also als aktiv.

### Anwendbare ASVS-Kategorien

| Kategorie | Trifft zu | Standard-Kontrolle in diesem Repo |
|-----------|-----------|-----------------------------------|
| V2 Authentication | nein (unverändert) | OAuth 2.1 und AppAPI-Impersonation stehen, diese Phase ändert nichts daran |
| V3 Session Management | nein | keine Sitzung in Werkzeugen, stateless |
| V4 Access Control | ja | Berechtigungs-Durchgriff: jeder neue Leseweg läuft mit den Credentials des Aufrufers; der Zwei-Konten-Beweis ist das Muster (`test_mail_read.py`) |
| V5 Input Validation | ja | `ids.parse` mit ASCII-Ziffern-Guard, `_path_token` gegen `[a-z0-9]{4,30}`, `paging.check_scope`, Fragment-Leser mit `fullmatch` |
| V6 Cryptography | ja, nur im Release | `openssl dgst -sha512 -sign` mit dem bestehenden Schlüssel; nichts selbst gebaut |
| V7 Error Handling | ja | `graceful` plus `ToolError` mit Satz und nächstem Schritt, kein Stacktrace, keine Loginseite |
| V12 Files and Resources | ja | keine URL aus einem Suchtreffer wird jemals abgerufen (`absolute_url` parst nur), das ist die SSRF-Tür und sie bleibt zu |

### Bekannte Bedrohungsmuster für diese Phase

| Muster | STRIDE | Standard-Gegenmaßnahme |
|--------|--------|------------------------|
| Prompt Injection über einen Talk-Vorschautext im Standardbündel | Tampering | `marks.without_marks` in der Tool-Schicht, fremder Text bleibt Datenfeld, D-57-Warnung in der Werkzeugbeschreibung ("third parties") bleibt erhalten |
| Gefälschter Marker in einer Nachricht oder einem Zellwert | Spoofing | Erst filtern, dann eigenen Marker anhängen, wie in `_capped` und `_fetch_mail`; die Reihenfolge ist tragend |
| Exfiltration über die erweiterte Reichweite (mehr fremder Inhalt im Bündel) | Information Disclosure | Kein Betreff und kein Body im Standardbündel (CTX-02), `EXCERPT_KINDS` bleibt bei den drei alten Kinds, Ketten-Formulierung aus CR-01 bleibt ehrlich |
| Eine geratene Id liest fremden Inhalt (falsche Tabelle, falsche Nachricht) | Elevation of Privilege | Niemals ein Kind oder eine Id raten; `view` bleibt `url`, eine fehlende Zielnachricht wird abgelehnt |
| Nebenwirkung durch einen neuen Leseweg (Lesemarker, Benachrichtigung) | Tampering | Route im Quellcode verifiziert, plus Vorher-Nachher-Messung über eine **andere** Route |
| Brute-Force-Zähler gegen fremde Container-Adressen | Denial of Service | Token gegen die eigene Konversationsliste prüfen, wie `talk_tools._room` |
| Ein gelöschtes Release-Asset macht jede spätere Installation kaputt | Denial of Service | Proof-Zeile `curl -I` in Schritt 8, ausdrücklich nicht optional |

## Environment Availability

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Fallback |
|--------------|---------------|-----------|---------|----------|
| uv | jeder Lauf (System-Python ist unbrauchbar) | ja | 0.11.7 | keiner |
| Docker Engine | Integrationsmessungen | ja | 29.5.2, Daemon antwortet | keiner |
| Laufende ExApp-Topologie | Live-Messung CTX-01/02, SRV-06-Muster | ja | `nc-mcp-exapp-*` und `nc_app_mcp_connector` laufen, GreenMail dabei | `bash scripts/bootstrap_exapp.sh` neu aufsetzen |
| `.env.exapp` | Skip-Bedingung der Integrationstests | ja | vorhanden | `bootstrap_exapp.sh` schreibt sie neu |
| gh | Release-Schritt 5 | ja | 2.92.0 | GitHub-Weboberfläche |
| openssl | Release-Schritt 6 | ja | 3.5.6 | keiner |
| Signaturschlüssel und Zertifikat | Release-Schritt 6 | ja | `~/.nextcloud/certificates/mcp_connector.{key,crt}` | keiner, der Schlüssel ist nicht ersetzbar |
| curl, tar | Schritte 6 und 8 | ja | 8.19.0, 1.35 | keiner |
| Angemeldete Store-Sitzung im Browser | Release-Schritt 7 | **nicht prüfbar aus dieser Session** | - | Formular `apps.nextcloud.com/developer/apps/releases/new`, oder `curl` mit Token aus der Kontoseite |
| Owner-Freigabe für den Tag | Release-Schritt 4 | offen | - | keiner, das ist ein Checkpoint |

**Fehlende Abhängigkeiten ohne Ausweg:** keine technische. Zwei menschliche Tore: die Owner-Freigabe vor Schritt 4 und die Store-Sitzung in Schritt 7. Beide gehören als `checkpoint` in den Plan, nicht als Task.

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|------------|-----------|---------------------|
| A1 | `talk-message-current` trägt dieselben Attribute wie `talk-message` | Ist-Zustand 3 | Ein Provider bleibt unnötig `url`; billig zu prüfen, teuer zu raten. Im Plan mit einem Blick in `CurrentMessageSearch.php` klären |
| A2 | Die von TOOL-15 erwarteten 17500 bis 18000 setzen voraus, dass die Diät die Messung senkt | Budget-Arithmetik | Der Plan verankert mechanisch auf 18500 und liest sich wie eine nicht erledigte Aufgabe. Erwartung und Rechnung im Plan gegenüberstellen |
| A3 | Ein Zeitbudget von etwa 5 s für Talk und etwa 10 s für Mail ist angemessen | Pattern 1 | Zu klein heißt Degradation im Normalfall, zu groß heißt eine Wanduhr, die ein Client abbricht. Erst messen, dann die Konstante setzen |
| A4 | `fetch` eines Tabellen-Treffers soll Titel, Zeilenzahl und die ersten Zeilen liefern | Diagramm, Pattern 4 | Eine andere Antwortform wäre auch verteidigbar; die Entscheidung gehört in den Plan und in den Docstring |
| A5 | Die `prepare_context`-Beschreibung muss Talk und Mail nennen | Pitfall 3 | Wenn nicht, spart es Bytes, kostet aber Ehrlichkeit; Owner-nahe Entscheidung |
| A6 | Die Kontenzahl im Mail-Bein sollte gekappt werden | Pattern 3 | Ohne Kappung ist die Wanduhr von der Kontenzahl des Nutzers abhängig; mit Kappung braucht es einen `degraded`-Eintrag |
| A7 | IN-01 (Doppelbedeutung von `truncated`) wird in dieser Phase mit erledigt | Owner-Vorgabe 5 | Es ist eine Antwortformat-Änderung; wenn sie kommt, gehört sie in den Changelog von 0.1.8 |

## Open Questions

1. **Wachsen `KIND_BUCKETS` oder wird `_short` geändert?**
   - Bekannt: Beide Wege lösen Pitfall 1. Wachsende Buckets verteilen die 25 Treffer um, blasen die Antwort also kaum auf (Rechnung in `ARCHITECTURE.md:300`).
   - Unklar: ob das Bündel überhaupt Talk- und Mail-Treffer als eigene Buckets ausweisen soll, wenn es daneben einen Talk-Digest und Mail-Zähler trägt. Zwei Wahrheiten über Talk in einer Antwort wären verwirrend.
   - Empfehlung: `_short` minimal ändern (nur `resolvable is False` durchreichen) und die Buckets **nicht** erweitern, dann bleibt der Digest die einzige Talk-Aussage im Bündel und die Auszugsfrage stellt sich nicht. Im Plan begründen.

2. **Wie viele Konten sieht das Mail-Bein?**
   - Bekannt: 1+N Requests, N ist die Kontenzahl des Nutzers, auf dieser Instanz 1.
   - Unklar: ob eine Instanz mit fünf Konten fünf Postfachrunden je Bündelaufruf wert ist.
   - Empfehlung: alle Konten, aber mit einer Kappe (Vorschlag 3, passend zu `MAX_DIGEST`) und einem `degraded`-Eintrag, wenn sie greift.

3. **Wird `MAX_TOOL_BYTES` nach der Diät gesenkt?**
   - Bekannt: Heute 1400 mit 23 Bytes Luft; das Skript nennt diese Grenze das eigentliche Gate.
   - Empfehlung: senken, wenn `mail_browse` nach der Diät klar darunter liegt, aber nur mit neuer Messzeile und in derselben Task wie die Verankerung der Gesamtsumme.

4. **Bekommt `scripts/acceptance_all_tools.py` die Liste aus der Registry?**
   - Bekannt: Die Namensliste ist eine zweite Kopie; der Tech-Debt-Eintrag ist TOOL-15 zugeschlagen.
   - Empfehlung: gegen `client.list_tools()` prüfen und IN-04 in derselben Task erledigen.

5. **Wann fällt die Owner-Freigabe für den Tag?**
   - Bekannt: Schritt 4 ist irreversibel in der Öffentlichkeit; alle Voraussetzungen (Schlüssel, Zertifikat, Workflow) sind vorhanden.
   - Empfehlung: der letzte Plan endet mit einem `checkpoint:human-approve` vor `git push origin v0.1.8`, und die vier Proof-Zeilen aus Schritt 8 sind Teil derselben Task.

## Sources

### Primär (HIGH)

- Repository-Quellcode, gelesen am 2026-08-24: `src/mcp_connector/tools/context.py`, `provider_map.py`, `ids.py`, `tools/chatgpt.py`, `tools/talk.py`, `tools/tables.py`, `tools/mail.py`, `tools/search.py`, `server/__init__.py`, `server/reg_context.py`, `reg_chatgpt.py`, `reg_mail.py`, `reg_talk.py`, `nextcloud/clients/talk.py`, `nextcloud/clients/tables.py`, `nextcloud/capabilities.py`
- Eigene Messung am 2026-08-24: `uv run --no-sync python scripts/check_tool_budget.py` (15736 Bytes, 21 Tools) und eine Einzelmessung aller 21 Werkzeuge über `Client(mcp).list_tools()`
- `tests/contract/test_tool_surface.py`, `tests/unit/test_tools_context.py`, `tests/unit/test_exapp_env_setup.py` (Vokabular- und Versionsgate), `tests/integration/test_talk_roundtrip.py`
- `docs/store-submission.md` (Runbook und Nachweistabelle), `CHANGELOG.md`, `appinfo/info.xml`, `pyproject.toml`, `.github/workflows/release.yml`, `.github/workflows/ci.yml`
- `.planning/phases/10-mail-strikt-lesend-und-die-trifecta-grenze/10-08-SUMMARY.md` (Messprotokoll und die zwei Übergaben), `10-REVIEW.md` (CR-01, WR-01 bis WR-05, IN-01 bis IN-04)
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json`
- https://raw.githubusercontent.com/nextcloud/spreed/v24.0.4/lib/Controller/ChatController.php - `getMessageContext`: Route, Signatur, `$historyLimit = max(1, $limit)`, `$limit = min(100, max(0, $limit))`, `getHistory(..., true, ...)`, `waitForNewMessages(..., 0, ..., false, ...)`, 304 bei leerer Menge, keine Brute-Force- und keine Rate-Limit-Attribute
- https://raw.githubusercontent.com/nextcloud/spreed/master/lib/Search/MessageSearch.php - Provider-Id `talk-message`, Attribute `conversation`, `messageId`, `threadId`, `actorType`, `actorId`, `timestamp`, Fragment `message_<id>`
- https://raw.githubusercontent.com/nextcloud/tables/main/lib/Search/SearchTablesProvider.php - Provider-Id `tables-search-tables`, Link `#/<nodeType>/<nodeId>` mit `table` oder `view`, keine Attribute
- Umgebungsprüfung am 2026-08-24: `uv 0.11.7`, `Docker 29.5.2`, `gh 2.92.0`, `OpenSSL 3.5.6`, `curl 8.19.0`, `tar 1.35`, laufende Container, Zertifikat und Schlüssel vorhanden

### Sekundär (MEDIUM)

- `.planning/research/ARCHITECTURE.md`, `FEATURES.md`, `PITFALLS.md`, `STACK.md` (Meilenstein-Recherche vom 2026-08-21): Kostenrechnung, Bucket-Empfehlung, Provider-Liste. Zwei ihrer Empfehlungen sind von den Requirements überstimmt, siehe "State of the Art"
- `.planning/phases/08-erreichbarkeits-spike-und-tables/08-RESEARCH.md:701` und `09-talk/09-RESEARCH.md:341` (Vorarbeiten zu TOOL-16)

### Tertiär (LOW, ausdrücklich als offen markiert)

- `talk-message-current` trägt vermutlich dieselben Attribute (A1, nicht gelesen)
- Die Bedeutung des `unread`-Feldes im Navigationseintrag bleibt ungeklärt (Übergabe 2 aus Phase 10); für diese Phase irrelevant, weil das Feld nicht benutzt wird

## Metadata

**Confidence-Aufschlüsselung:**

- Ist-Zustand des Codes: **HIGH** - jede genannte Zeile wurde in dieser Session gelesen, jede Zahl in dieser Session gemessen
- Fremde APIs (spreed-Kontextroute, beide Suchprovider): **HIGH** - Quellcode der auf dieser Instanz laufenden Version (v24.0.4) bzw. der aktuellen Hauptlinie, mit Zitat
- Budget-Arithmetik: **HIGH** für die Rechnung, **MEDIUM** für den Landepunkt (hängt an Formulierungsentscheidungen)
- Zeitbudgets der neuen Beine: **LOW** - reine Setzung, muss gemessen werden (A3)
- Release-Runbook: **HIGH** - acht Schritte mit Nachweistabelle, alle Voraussetzungen lokal geprüft
- Store-Schritt 7 (Sitzung im Browser): **MEDIUM** - dokumentiert und zweimal so ausgeführt, aus dieser Session nicht prüfbar

**Research date:** 2026-08-24
**Valid until:** 2026-09-23 für den Repo-Ist-Zustand (er ändert sich mit dem ersten Plan dieser Phase), 2026-09-07 für die fremden App-APIs (Nextcloud-Apps veröffentlichen Patch-Releases in Wochen)
