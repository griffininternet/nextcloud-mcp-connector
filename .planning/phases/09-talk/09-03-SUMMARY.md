---
phase: 09-talk
plan: 03
subsystem: tools
tags: [nextcloud-talk, spreed, projektion, paginierung, prompt-injection, admin-schalter]

# Dependency graph
requires:
  - phase: 09-talk
    provides: "clients/talk.py mit get_rooms, get_messages, send_message und web_url; 201 im Erfolgsraum von parse_ocs; capabilities.spreed_available, spreed_chat_max_length (Plan 09-01)"
  - phase: 09-talk
    provides: "config.talk_send_enabled und ENV_TALK_SEND, plus der aufgeloeste Schalterwert in der Prozessumgebung (Plan 09-02)"
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "tools/tables.py als Bauplan der Familie (Level-Enum, Envelope, Projektion, Berechtigungs-Vorpruefung), tests/unit/test_tables_tools.py als Testbauplan"
  - phase: 01-server-kern
    provides: "paging.encode_cursor/decode_cursor/check_scope/read_offset, tools/marks.without_marks, errors.ToolError, capabilities.require_app"
provides:
  - "tools/talk.py: browse(level=conversations|messages) und send, mit Projektion beider Ebenen, Platzhalter-Aufloesung, Positivliste, UTF-8-Byte-Kappe und Header-Cursor"
  - "Die drei Inhaltsfallen der Phase je mit einem Regressionstest belegt: Sortieren vor dem Kappen (T5), aufgeloestes permissions statt attendeePermissions (T3), Typ 4 immer schreibgeschuetzt (T4)"
  - "Schicht 3 von Erfolgskriterium 5: mit abgeschaltetem Schalter antwortet talk_send mit einem Fehlersatz samt naechstem Schritt und macht null HTTP-Aufrufe"
  - "vulture_whitelist.py ohne die Talk-Transport- und Schalter-Eintraege der Plaene 09-01 und 09-02"
affects: [09-04 reg_talk.py und Schemata, 09-05 Ende-zu-Ende-Nachweis, 10 SEC-01, 11 CTX-01, 11 TOOL-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kappung einer Liste ohne Server-Reihenfolge: sortieren, dann filtern, dann kappen, und die Reihenfolge im Docstring begruendet"
    - "truncated und next aus einem Antwort-Header statt aus der Ergebnislaenge (neu in dieser Codebasis)"
    - "Ein Feld neben dem Text statt einer Markierung im Text, wenn fremder Text gekappt wird (ME-03)"
    - "Der administrative Schalter als erste ausfuehrbare Zeile eines Schreibwegs, vor der App-Erkennung"

key-files:
  created:
    - src/mcp_connector/tools/talk.py
    - tests/unit/test_talk_tools.py
  modified:
    - vulture_whitelist.py

key-decisions:
  - "Die Nachrichtenebene liest zuerst die Konversationsliste: sie liefert den Anzeigenamen fuer den Envelope und macht ein erfundenes Token zu unserem eigenen Satz, ohne dass Nextcloud es je in einem Pfad sieht (T10 gilt damit auch auf dem Lesepfad)"
  - "Eine Erwaehnung wird an mention-id oder am Platzhalternamen erkannt, nicht am Typ allein: {actor} traegt ebenfalls type=user, und ein Praefix darauf haette jede Nachricht so aussehen lassen, als erwaehne sie ihren eigenen Autor"
  - "Kein Cursor auf der Konversationsebene, sondern truncated plus total; ein Offset-Handle wuerde bei jedem Aufruf dieselbe Liste erneut holen und nur anders schneiden"
  - "Auf der Konversationsebene entscheidet der kleinere der beiden Werte: MAX_CONVERSATIONS und das limit des Aufrufers; beide nennen die Gesamtzahl hinter sich"
  - "Die Byte-Kappe laeuft ueber encode/slice/decode mit errors=ignore, damit ein Umlaut am Schnittpunkt verschwindet statt als Ersatzzeichen anzukommen"
  - "Der Cursor wird vor der Konversationsliste geprueft: ein fremdes Handle beendet den Aufruf ohne einen einzigen Talk-Request"
  - "spreed_features bleibt in vulture_whitelist.py, weil tools/talk.py es nicht liest; es ist derselbe Fall wie tables_api_versions und deck_api_versions und kein geparkter Aufrufer mehr"
  - "TALK-01 bis TALK-04 bleiben Pending: der Wortlaut spricht von den Werkzeugen talk_browse und talk_send, und registriert werden sie erst mit Plan 09-04; TALK-02 verlangt zusaetzlich die Live-Messung und TALK-04 die ganze Kette"

patterns-established:
  - "Ein Gate, das eine Zeichenfolge ausserhalb von Kommentaren verbietet, verschiebt die Begruendung in einen Kommentarblock ueber der Funktion, und der Docstring sagt, warum sie dort steht"
  - "Der Envelope einer Unterebene traegt die Identitaet ihres Elternobjekts (token plus Anzeigename), damit ein Fehlgriff ohne zweiten Aufruf sichtbar ist"

requirements-completed: []

# Metrics
duration: 26 min
completed: 2026-08-21
---

# Phase 9 Plan 03: Die Fachlogik der Talk-Familie Summary

**`tools/talk.py` mit `browse(level="conversations"|"messages")` und `send`: die Konversationsliste wird sortiert, bevor sie gekappt wird, `truncated` und `next` des Verlaufs kommen allein aus dem Antwort-Header, jeder fremde Text laeuft durch `without_marks` und wird auf eine echte UTF-8-Byte-Grenze gekappt, und der Sendeweg liest den Admin-Schalter als erste ausfuehrbare Zeile, prueft die Rechte am aufgeloesten `permissions`-Feld und laesst ein erfundenes Token nie in einen Nextcloud-Pfad.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-08-21T11:31:00Z
- **Completed:** 2026-08-21T11:57:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 neu, 1 geaendert)
- **Tests:** 49 Testfunktionen, 65 Faelle mit Parametrisierung

## Accomplishments

- Die drei Inhaltsfallen der Phase sind je mit einem Test belegt, der bei einem Rueckfall rot wird und die Ursache im Namen traegt. `test_the_conversation_list_is_sorted_before_it_is_cut` behauptet die Reihenfolge der Tokens gegen die absichtlich unsortierte Fixture (T5); `test_a_conversation_with_the_chat_permission_may_be_written_in` sendet mit `permissions` 128 bei `attendeePermissions` 0 (T3); `test_a_conversation_nobody_may_write_in_is_refused_before_the_post` deckt `readOnly` 1, Typ 4 und fehlendes Bit 128 in einem parametrisierten Fall ab (T4), und `test_a_note_to_self_is_not_locked_away_with_the_read_only_conversations` haelt fest, dass Typ 6 beschreibbar bleibt.
- Schicht 3 von Erfolgskriterium 5 steht: mit `NC_MCP_TALK_SEND=0` antwortet `send` mit einem Fehlersatz, dessen Hinweis den Administrator, `strings.ADMIN_SETTINGS_PLACE`, den Aktivierungszyklus und die Unberuehrtheit des Lesens nennt, und es gibt **keinen** HTTP-Aufruf: `test_a_switched_off_send_makes_not_a_single_http_call` mockt nichts ausser einer Catch-all-Route und behauptet `len(route.calls) == 0`, `test_the_switch_is_read_before_the_app_is_detected` behauptet zusaetzlich, dass nicht einmal die Capabilities gefragt werden.
- Die Paginierung des Verlaufs hoert nicht auf, solange die App aelteren Verlauf anbietet. `truncated` und `next` entstehen allein aus der Fortsetzungs-Id des Clients, und die Zeichenfolge `len(results)` kommt im Modul ausserhalb von Kommentaren nicht vor. Der Fall, der eine Ableitung aus der Ergebnislaenge stillschweigend beendet haette (Status 200, ausschliesslich Systemnachrichten, gesetzter Header), ist ein eigener Test mit `count: 0` **und** `next`; die 304 des leeren Verlaufs ist `count: 0` **ohne** `next` und ohne Fehler.
- Kein fremder Text erreicht den Modellkontext ohne `marks.without_marks`: Nachrichtentext, Anzeigename der Konversation, Anzeigename des Autors und jeder aufgeloeste Name aus `messageParameters` laufen durch `_text` beziehungsweise durch `_resolve`, das selbst mit `without_marks` endet. Vier Tests behaupten das, zwei davon per `json.dumps` ueber die ganze Antwort.
- Die Kappung steht nie im Text. `truncated: true` ist ein Feld neben der Nachricht, und `test_a_long_message_is_cut_on_a_character_boundary_and_says_so_beside_the_text` prueft mit 799 ASCII-Zeichen plus Umlaut, dass der Schnitt bei 800 Bytes das halbe Zeichen verwirft statt ein Ersatzzeichen zu liefern.
- Ein erfundenes Token erreicht Nextcloud nie in einem Pfad, auf beiden Wegen. Lesen und Senden suchen es in der eigenen Konversationsliste (`GET /room`, ohne Token im Pfad) und antworten sonst mit unserem eigenen Satz; zwei Tests belegen null Aufrufe auf einer Chat-Route.
- Alle Gates sind gruen und nichts Fremdes ist angefasst: `uv run pytest -q` ueber die ganze Default-Auswahl, `ruff check .`, `ruff format --check .`, `pyright` (0 errors) und `vulture src/mcp_connector vulture_whitelist.py` (Exit 0, **ohne** neuen Whitelist-Eintrag und mit fuenf entfernten), `check_tool_budget.py` unveraendert bei 12801 Bytes und 18 Werkzeugen, und `git diff --stat` nennt nur `tools/talk.py`, `test_talk_tools.py` und `vulture_whitelist.py`.

## Task Commits

Each task was committed atomically:

1. **Task 1: browse mit level conversations, sortiert vor dem Kappen** - `3388427` (feat)
2. **Task 2: browse mit level messages, Platzhalter, Positivliste und Header-Cursor** - `424b752` (feat)
3. **Task 3: send mit dem Schalter als erster Zeile und Vorpruefungen am Objekt** - `fd7a8d8` (feat)

## Die Signaturen fuer Plan 09-04

```python
async def browse(
    clients: NcClients,
    level: str = "conversations",          # LEVELS = ("conversations", "messages")
    token: str | None = None,              # Pflicht ab level="messages"
    limit: int = DEFAULT_LIMIT,            # 20, gekappt auf MAX_LIMIT = 50
    cursor: str | None = None,             # nur auf der Nachrichtenebene sinnvoll
) -> dict[str, Any]

async def send(clients: NcClients, token: str, message: str) -> dict[str, Any]
```

Es gibt **keinen** `include_system`-Parameter (Offene Frage 3) und **keinen** Cursor-Nutzen auf
der Konversationsebene (Offene Frage 2). Die Konstanten, aus denen die Schemagrenzen gebaut
werden: `DEFAULT_LIMIT = 20`, `MAX_LIMIT = 50`, `MAX_CONVERSATIONS = 50`,
`MAX_MESSAGE_BYTES = 800`, `KEPT_TYPES`, `PERMISSIONS_CHAT = 128`, `TYPE_CHANGELOG = 4`,
`READ_WRITE = 0`, `APP = "spreed"`.

## Die Feldnamen der drei Antworten

`browse(level="conversations")`, Envelope: `level`, `count`, `results`, dazu `truncated` und
`total` nur bei einer Kappung. Kein `next`.

Je Konversation, immer: `token`, `name` (aus `displayName`), `type`, `unread`,
`unread_mention`, `unread_mention_direct`, `last_activity` (Unix-Zahl), `read_only`,
`can_send`, `url`. Nur wenn gesetzt: `last_message` (gekappte Vorschau, ohne Markierung),
`mention_permissions`.

`browse(level="messages")`, Envelope: `level`, `token`, `conversation` (Anzeigename), `count`,
`results`, dazu `truncated` und `next` nur bei vorhandener Fortsetzung.

Je Nachricht, immer: `id`, `timestamp` (Unix-Zahl), `actor`, `message` (aufgeloest, bereinigt,
gekappt). Nur wenn zutreffend: `truncated`, `edited`.

`send`: `sent`, `id`, `token`, `conversation`, `timestamp`, `url`.

## Der Wortlaut des Schalter-Fehlersatzes

Damit Plan 09-04 die Beschreibung von `talk_send` im selben Ton schreibt und unter dem
Pro-Werkzeug-Deckel von 1400 Bytes bleibt:

```
message: Sending Talk messages is switched off for this Nextcloud.
hint:    This account cannot change it: an administrator switches it on under
         Administration settings, Security, MCP Connector, and the change takes effect after
         this app is disabled and enabled again. Reading conversations and their history with
         talk_browse is unaffected.
```

Der Ort ist `strings.ADMIN_SETTINGS_PLACE` und nicht buchstabiert; der Satz zum
Aktivierungszyklus ist derselbe wie an den vier anderen Stellen. Die fuenf uebrigen Absagen
des Sendewegs (zu lang, Sammel-Erwaehnung, Token nicht in der Liste, schreibgeschuetzt, Typ 4,
kein Chat-Recht) tragen jede einen eigenen Satz mit naechstem Schritt; drei davon nennen
`can_send`, damit die Antwort auf das Lesewerkzeug zeigt.

## Files Created/Modified

- `src/mcp_connector/tools/talk.py` (neu, 588 Zeilen) - Modul-Docstring mit vier
  Ueberschriftensaetzen und "Deliberately absent"; `browse`, `send`, `_refusal`,
  `_conversations`, `_conversation`, `_preview`, `_messages`, `_is_kept`, `_message`,
  `_resolve`, `_is_mention`, `_capped`, `_room`, `_may_send`, `_text`, `_number`, `_envelope`;
  Konstanten `APP`, `LEVELS`, `DEFAULT_LIMIT`, `MAX_LIMIT`, `MAX_CONVERSATIONS`,
  `MAX_MESSAGE_BYTES`, `KEPT_TYPES`, `READ_WRITE`, `TYPE_CHANGELOG`, `PERMISSIONS_CHAT`,
  `_LEVEL_HINT`, `_CONVERSATION_HINT`, `_PLACEHOLDER`, `_MENTION_ALL`.
- `tests/unit/test_talk_tools.py` (neu, 1123 Zeilen) - 49 Testfunktionen, 65 Faelle. Helfer
  `mock_capabilities`, `talk_routes`, `mock_rooms`, `room`, `mock_messages`, `message`,
  `mock_send`, plus die eingefrorenen URL-Literale beider API-Versionen.
- `vulture_whitelist.py` - `spreed_chat_max_length`, `get_rooms`, `get_messages`,
  `send_message` und `talk_send_enabled` entfernt, weil `tools/talk.py` sie jetzt aufruft;
  `spreed_features` bleibt mit neuer Begruendung (derselbe Fall wie `tables_api_versions`, kein
  geparkter Aufrufer).

## Decisions Made

- **Die Nachrichtenebene liest die Konversationsliste mit.** Der Plan verlangt `token` und den
  Anzeigenamen im Envelope, und die einzige Quelle des Namens ist die Liste. Der Preis ist ein
  zusaetzlicher Request je Verlaufsseite (mit `include_last_message=False`, also der kleinen
  Form der Antwort), der Gegenwert sind zwei Aussagen aus einem Request: der Name im Envelope
  und die Absage an ein Token, das nicht in der eigenen Liste steht. Damit gilt der Schutz aus
  T10 auch auf dem Lesepfad, nicht nur beim Senden. Vorbild ist `_rows` in `tools/tables.py`,
  das die Tabelle vor den Zeilen liest.
- **Erwaehnung an `mention-id`, nicht am Typ.** Muster 5 der Recherche schlaegt vor, ein `@`
  vor jeden Parameter zu setzen, dessen Typ mit `user` beginnt. Das ist genau ein Zeichen zu
  breit: `{actor}`, der Autor der Nachricht, traegt in Talk denselben Typ. `_is_mention` prueft
  deshalb `mention-id`, den Typ `call` und den Praefix des Platzhalternamens. Der Plan verlangt
  wortwoertlich "ein `{actor}` und eine Erwaehnung werden aufgeloest, eine Erwaehnung mit `@`
  davor", was ohne diese Unterscheidung nicht erfuellbar ist.
- **Der Cursor wird vor der Konversationsliste geprueft.** Der Plan nennt die Reihenfolge
  "ohne Token ablehnen, Cursor lesen, dann `get_messages`"; die Konversationsliste kam als
  neuer Schritt dazu und steht hinter dem Cursor, weil die billigere Absage vorne gehoert:
  ein fremdes Handle beendet den Aufruf ohne einen einzigen Talk-Request. Der Test behauptet
  beide Nullen.
- **`total` nur bei einer Kappung.** Die Zahl ist die Ehrlichkeit der Kappung und in der
  ungekappten Antwort identisch mit `count`, also Bytes ohne Aussage. Dieselbe "nur wenn
  gesetzt"-Regel wie bei `emoji` in Tables und `truncated` an der Nachricht.
- **Der kleinere der beiden Werte kappt die Konversationsliste.** `limit` gilt auch auf dieser
  Ebene, `MAX_CONVERSATIONS` ist die Decke darueber. Ein Aufrufer, der fuenf Konversationen
  will, bekommt fuenf und die Gesamtzahl dazu; ein Aufrufer ohne `limit` bekommt 20. Beide
  Faelle stehen im selben Test.
- **Eine Konversation ohne Token faellt aus der Liste.** Sie ist nicht adressierbar, und
  Adressierbarkeit ist der Zweck dieser Ebene; eine Antwort mit leerem `token` und einer
  `url`, die auf nichts zeigt, waere die Form, die zum Raten einlaedt.
- **Kein Verbot einer leeren Nachricht.** Talk antwortet darauf mit einem 400 samt eigenem
  Text, und `parse_ocs` reicht ihn durch. Eine zweite Pruefung hier waere eine zweite Wahrheit
  ueber die Regeln der App, genau wie die fehlende Typpruefung der Zellwerte in Phase 8.
- **TALK-01 bis TALK-04 bleiben Pending.** Der Wortlaut aller vier spricht von `talk_browse`
  und `talk_send` als Werkzeugen; registriert werden sie mit Plan 09-04. TALK-02 verlangt
  zusaetzlich den Live-Nachweis der Nebenwirkungsfreiheit (Plan 09-05), TALK-04 die ganze
  Kette. Gleiches Vorgehen wie in den Plaenen 09-01 und 09-02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Nachrichtenebene musste im Commit von Task 1 mitkommen**

- **Found during:** Task 1
- **Issue:** Task 1 verlangt `LEVELS == ("conversations", "messages")` (per Verifikations-
  kommando) und beschreibt nur die Konversationsebene; Task 2 ergaenzt die Nachrichtenebene.
  Ein `browse`, dessen Level-Enum einen Wert nennt, fuer den es keinen Zweig gibt, ist
  entweder ein `None`-Rueckgabepfad (pyright rot) oder ein Platzhalter-ToolError, also genau
  der Stub, den die Plan-Regeln verbieten.
- **Fix:** Der Commit von Task 1 traegt `_messages`, `_is_kept`, `_message`, `_resolve`,
  `_capped` und `_room` mit; der Commit von Task 2 traegt die Cursor-Reihenfolge und die
  21 Testfaelle der Nachrichtenebene. Beide Commits sind fuer sich gruen und die
  Akzeptanzkriterien beider Aufgaben sind einzeln geprueft.
- **Files modified:** src/mcp_connector/tools/talk.py
- **Verification:** `uv run pytest tests/unit/test_talk_tools.py -q` nach jedem der drei
  Commits gruen; die Verifikationskommandos beider Aufgaben einzeln gelaufen.
- **Committed in:** `3388427` (Task 1) und `424b752` (Task 2)

**2. [Rule 3 - Blocking] `_TOKEN_HINT` liess das Lint-Gate reissen**

- **Found during:** Task 1
- **Issue:** Der Plan nennt die Hint-Konstante `_TOKEN_HINT`. `ruff` liest eine
  Zeichenketten-Konstante mit `TOKEN` im Namen als hartverdrahtetes Passwort (S105), und
  `ruff check .` war rot. Ein `noqa` haette auf der Zeile der Diagnose stehen muessen, also
  mitten in einer mehrzeiligen Zeichenkette.
- **Fix:** Umbenannt in `_CONVERSATION_HINT`, mit einem `#:`-Kommentar, der den Grund und die
  Abgrenzung nennt (ein Talk-Token ist eine Konversationsadresse und kein Geheimnis).
- **Files modified:** src/mcp_connector/tools/talk.py
- **Verification:** `uv run ruff check .` gruen.
- **Committed in:** `3388427` (Task 1)

**3. [Rule 1 - Bug] Muster 5 der Recherche haette jede Nachricht ihren eigenen Autor erwaehnen lassen**

- **Found during:** Task 2
- **Issue:** Die vorgeschlagene Erkennung "Typ beginnt mit `user` oder ist `call`" trifft auch
  `{actor}`, also den Autor jeder Nachricht: aus "Bob hat die Masse geprueft" waere "@Bob hat
  die Masse geprueft" geworden. Der Plan verlangt ausdruecklich, dass der Aktor ohne und die
  Erwaehnung mit `@` aufgeloest wird.
- **Fix:** `_is_mention(key, entry)` prueft `mention-id`, den Typ `call` und den Praefix des
  Platzhalternamens. Der Docstring von `_resolve` benennt die Falle.
- **Files modified:** src/mcp_connector/tools/talk.py
- **Verification:** `test_the_placeholders_of_a_message_are_resolved_and_a_mention_keeps_its_at_sign`
  behauptet beide Formen in einer Nachricht.
- **Committed in:** `3388427` (Task 1, wo `_resolve` entstand)

**4. [Rule 3 - Blocking] Der Docstring von `_may_send` durfte das falsche Feld nicht nennen**

- **Found during:** Task 1
- **Issue:** Task 1 verlangt per Verifikationskommando, dass `attendeePermissions` im Modul
  ausserhalb von Kommentaren nicht vorkommt (`grep -v "^\s*#"`), und ein Docstring ist kein
  Kommentar in diesem Sinne. Task 3 verlangt, dass die Begruendung das falsche Feld
  ausdruecklich benennt. Beides zugleich ist nur ausserhalb des Docstrings moeglich.
- **Fix:** Der zehnzeilige Kommentarblock direkt ueber `_may_send` traegt die volle Begruendung
  samt Feldnamen und der Fallback-Kette; der Docstring traegt die drei Absagen und sagt in
  seinem letzten Absatz, warum die Begruendung im Kommentar darueber steht.
- **Files modified:** src/mcp_connector/tools/talk.py
- **Verification:** `grep -v "^\s*#" src/mcp_connector/tools/talk.py | grep -c
  "attendeePermissions"` ist 0; die Zeichenfolge steht im Kommentarblock und in
  `test_talk_tools.py`.
- **Committed in:** `3388427` (Task 1)

**5. [Rule 3 - Blocking] `SIM300` auf der Behauptung ueber `KEPT_TYPES`**

- **Found during:** Task 2
- **Issue:** `assert talk_tools.KEPT_TYPES == {...}` gilt ruff als Yoda-Bedingung, weil es die
  rechte Seite fuer ein Literal haelt. Derselbe Fall wie bei `_OK_STATUS` in Plan 09-01.
- **Fix:** `assert sorted(talk_tools.KEPT_TYPES) == [...]`, dieselbe Aussage plus eine feste
  Reihenfolge in der Fehlermeldung, mit Kommentar.
- **Files modified:** tests/unit/test_talk_tools.py
- **Verification:** `uv run ruff check .` gruen.
- **Committed in:** `424b752` (Task 2)

**6. [Rule 2 - Missing critical] `spreed_features` durfte die Whitelist nicht verlassen**

- **Found during:** Task 3
- **Issue:** Der Auftrag aus Plan 09-01 und 09-02 lautet, alle sechs geparkten Namen mit
  diesem Plan zu entfernen. Fuenf von ihnen haben jetzt einen Produktionsaufrufer,
  `spreed_features` nicht: `tools/talk.py` liest die Feature-Liste nicht. Ein blindes
  Entfernen haette das vulture-Gate reissen lassen, und ein erfundener Aufrufer waere
  schlimmer als der Eintrag.
- **Fix:** Der Block ist umgeschrieben statt geloescht: er sagt, welche vier Namen mit diesem
  Plan gegangen sind und warum, und begruendet `spreed_features` neu als denselben Fall wie
  `tables_api_versions` und `deck_api_versions`, also nicht mehr als geparkten Aufrufer.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` Exit-Code 0;
  `grep -n "plan 09-0" vulture_whitelist.py` nennt keinen offenen Auftrag mehr.
- **Committed in:** `fd7a8d8` (Task 3)

---

**Total deviations:** 6 auto-fixed (4 blockierend, 1 Bug, 1 fehlende kritische Absicherung)
**Impact on plan:** Kein Scope-Zuwachs, keine offene Absage. Drei Punkte sind Gates dieses
Repos, die der Plan nicht vorhergesehen hat (`S105`, `SIM300`, das eigene
`attendeePermissions`-Gate gegen einen Docstring), einer ist die strukturelle Grenze der
Aufgabenteilung von Task 1 und 2, einer ist ein echter Fehler im vorgeschlagenen Muster, und
einer ist die Korrektur eines Auftrags aus zwei vorherigen Plaenen. Der einzige inhaltliche
Zusatz gegenueber dem Plan ist der Lesevorgang der Konversationsliste auf der
Nachrichtenebene, und er ist die Voraussetzung fuer den vom Plan verlangten Anzeigenamen im
Envelope.

## Issues Encountered

- Zwei Verifikationskommandos derselben Phase widersprachen sich an einer Stelle: Task 1
  verbietet `attendeePermissions` ausserhalb von Kommentaren, Task 3 verlangt die namentliche
  Benennung in der Begruendung von `_may_send`. Geloest ueber den Kommentarblock; der
  Docstring verweist darauf, damit der naechste Leser die ungewoehnliche Aufteilung nicht
  "aufraeumt".
- Der Anzeigename im Envelope der Nachrichtenebene hat keine Quelle in der Verlaufsantwort.
  Das Datenflussdiagramm der Recherche zeigt fuer diese Ebene nur `get_messages`, der Plan
  verlangt den Namen. Aufgeloest mit dem zusaetzlichen Listen-Lesevorgang, siehe
  Entscheidungen; die Alternative waere gewesen, den Plan an dieser Stelle nicht zu erfuellen.

## Known Stubs

Keine. Beide Ebenen von `browse` und der ganze Sendeweg sind verdrahtet und getestet. Was
fehlt, ist ausdruecklich nicht Teil dieses Plans: die Registrierung als MCP-Werkzeuge samt
Schemata und Annotationen (Plan 09-04), die Contract- und Gate-Nachzuege (Plan 09-04) und der
Live-Nachweis gegen eine laufende Nextcloud (Plan 09-05).

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche gegenueber dem `<threat_model>` des Plans: kein
neuer Netzwerkendpunkt, kein neuer Auth-Pfad, kein Dateizugriff und keine Schema-Aenderung an
einer Vertrauensgrenze. Der einzige Unterschied zum Plan liegt in der Richtung mehr Schutz:
die Vorpruefung ueber die eigene Konversationsliste (T-09-21) wirkt jetzt auch auf dem
Lesepfad und nicht nur beim Senden.

## User Setup Required

None - no external service configuration required. Der Schalter aus Plan 09-02 ist an per
Default; eine bestehende Installation aendert ihr Verhalten durch diesen Plan nicht, weil noch
kein Werkzeug registriert ist.

## Next Phase Readiness

- Plan 09-04 kann die Schemata direkt aus den Signaturen und Konstanten oben bauen:
  `Literal["conversations", "messages"]`, `Field(ge=1, le=talk_tools.MAX_LIMIT)` mit
  `talk_tools.DEFAULT_LIMIT` als Vorgabe, leere Strings statt `None` als Default, und
  `structured_output=False` wie bei `reg_tables.py`.
- Der Docstring von `talk_send` in `reg_talk.py` ist die Stelle, an der der Pro-Werkzeug-Deckel
  von 1400 Bytes reissen kann. Vier Aussagen reichen dafuer: ein Versuch ohne Retry, Token nur
  aus `talk_browse`, kein Bearbeiten und kein Loeschen, und der Verweis auf `can_send`. Der
  Schalter braucht dort keinen Satz, weil das Werkzeug ihn selbst beantwortet.
- Plan 09-04 zieht die eingefrorenen Zahlen nach (18 auf 20 Werkzeuge an allen in Falle 9
  gelisteten Stellen) und ergaenzt `tests/contract/test_no_destructive_calls.py` um die
  positive Liste der genau drei Talk-Pfadformen samt `/schedule`, `/summarize`, `/pin`,
  `/reminder` und `/attachment` als Nadeln (T14).
- Plan 09-05 kann sich auf den Live-Teil beschraenken: Nebenwirkungsfreiheit gemessen vor und
  nach dem Lesen (T6, Schicht 2), ein echter Sendevorgang, die Absage in einer
  schreibgeschuetzten Konversation und der Schalter aus einer laufenden Nextcloud. Die
  Unit-Seite aller vier Aussagen steht hier.
- `spreed_features` ist der einzige offene Punkt in `vulture_whitelist.py` und braucht keinen
  Plan mehr: der Eintrag ist als dauerhafter Fall derselben Klasse wie `tables_api_versions`
  begruendet.

## Self-Check

- `src/mcp_connector/tools/talk.py` FOUND (588 Zeilen, `KEPT_TYPES` vorhanden)
- `tests/unit/test_talk_tools.py` FOUND (1123 Zeilen, `attendeePermissions` vorhanden)
- Commit `3388427` FOUND
- Commit `424b752` FOUND
- Commit `fd7a8d8` FOUND
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors),
  `uv run vulture src/mcp_connector vulture_whitelist.py` (Exit 0) alle gruen
- `uv run pytest -q` gruen ueber die ganze Default-Auswahl; `tests/unit/test_talk_tools.py`
  einzeln 65 Faelle gruen
- `uv run python scripts/check_tool_budget.py` Exit-Code 0, unveraendert 12801 Bytes bei 18
  Werkzeugen (dieser Plan registriert nichts)
- Die drei Grep-Gates: `attendeePermissions` 0 Treffer ausserhalb von Kommentaren,
  `len(results)` 0 Treffer ausserhalb von Kommentaren, `encode_cursor` 1 Treffer;
  `len(route.calls) == 0` und `allan` im Testmodul vorhanden
- Das Reihenfolge-Gate von `send`: `talk_send_enabled` steht vor `require_app`, `get_rooms`
  steht in der Quelle von `send`, die Wortgrenze der Erwaehnungsabsage ist vorhanden
- `git diff --stat` gegen den Stand vor diesem Plan nennt an Produktionscode nur
  `src/mcp_connector/tools/talk.py` und `vulture_whitelist.py`; `ids.py`, `provider_map.py`,
  `tools/chatgpt.py`, `tools/context.py`, `pyproject.toml` und `uv.lock` sind unberuehrt
- Kein Em-Dash, kein En-Dash und keine Emojis in den drei geaenderten Dateien

## Self-Check: PASSED

---
*Phase: 09-talk*
*Completed: 2026-08-21*
