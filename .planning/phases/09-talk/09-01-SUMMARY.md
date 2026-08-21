---
phase: 09-talk
plan: 01
subsystem: api
tags: [nextcloud-talk, spreed, ocs, httpx, respx, capabilities]

# Dependency graph
requires:
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "ocs_post als gemeinsamer OCS-Schreibweg, clients/tables.py als Bauplan der Familie, tests/unit/test_tables_client.py als Testbauplan"
  - phase: 01-server-kern
    provides: "parse_ocs, _check_transport, _status_error, capabilities.load/require_app mit 60-Sekunden-Cache"
provides:
  - "clients/talk.py: Konversationsliste (v4), Verlauf lesen und Nachricht senden (v1), Token-Wächter, 304-Behandlung, Header-Cursor, web_url"
  - "201 im Erfolgsraum von parse_ocs, damit eine gesendete Talk-Nachricht kein Fehler ist"
  - "capabilities: spreed_available, spreed_features, spreed_chat_max_length und der _MISSING-Satz für spreed"
  - "tests/fixtures/talk_rooms.json und talk_messages.json in echter Antwortform"
  - "Vollständige Unit-Abdeckung des Clients, behauptet an der gebauten Anfrage"
affects: [09-02 tools/talk.py, 09-03 reg_talk.py, 09-04 Admin-Schalter, 11 CTX-01, 11 TOOL-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rückgabe von Körper und Antwort-Header als Tupel (neu in dieser Codebasis)"
    - "Statuscode-Sonderfall lokal an der Route, an der er eine Bedeutung hat, statt im gemeinsamen Parser"
    - "Pfad-Wächter je Familie mit dem Muster, das die App selbst deklariert"

key-files:
  created:
    - src/mcp_connector/nextcloud/clients/talk.py
    - tests/unit/test_talk_client.py
    - tests/fixtures/talk_rooms.json
    - tests/fixtures/talk_messages.json
  modified:
    - src/mcp_connector/nextcloud/clients/ocs.py
    - src/mcp_connector/nextcloud/capabilities.py
    - tests/unit/test_ocs_capabilities.py
    - vulture_whitelist.py

key-decisions:
  - "get_messages gibt tuple[list[dict], int | None] zurück: Nachrichten plus Fortsetzung aus dem Antwort-Header X-Chat-Last-Given; ein fehlender oder nicht numerischer Header ergibt None, also kein Angebot einer nächsten Seite"
  - "Die 304 des leeren Verlaufs wird im Talk-Client vor parse_ocs abgefangen; _check_transport bleibt unverändert, weil 304 nur an dieser einen Route eine Bedeutung hat"
  - "_OK_STATUS trägt 201, weil OCS v2 den rohen Status in ocs.meta.statuscode schreibt und die Talk-Sende-Route 201 als einzigen Erfolg dokumentiert; heute liefert keine benutzte Route 201, die Erweiterung kann keine bestehende Pruefung umdrehen"
  - "Die spreed-Sektion gilt nur als vorhanden, wenn sie nicht leer ist: ein für den Nutzer abgeschaltetes Talk antwortet mit einem leeren Array"
  - "spreed_chat_max_length liest config.chat.max-length und fällt auf 32000 zurück, DEFAULT_CHAT_MAX_LENGTH als benannte Konstante; die Zahl gehört der Instanz"
  - "TALK-01 bis TALK-03 bleiben Pending: dieser Plan liefert den Transport, die Anforderungen sprechen von talk_browse und talk_send und sind erst mit Plan 09-02 und 09-03 wahr"
  - "Drei Namen des Talk-Transports und zwei Capabilities-Felder stehen vorübergehend in vulture_whitelist.py, nach dem Vorbild von Plan 08-02; sie verlassen die Liste mit Plan 09-02"

patterns-established:
  - "Antwort-Header als Nutzlast: der Client gibt Körper und Cursor zurück, das Tool erfährt nie, dass leer hier ein Statuscode ist"
  - "Verbotene Pfade werden als Quelltext-Behauptung gehalten, inklusive des Wortes für stilles Senden, das im Modul nicht buchstabiert wird"
  - "Leseparameter mit Nebenwirkung sind Modulkonstanten mit Begründung je Wert, nie Argumente"

requirements-completed: []

# Metrics
duration: 20 min
completed: 2026-08-21
---

# Phase 9 Plan 01: Transport-Befunde und Talk-Client Summary

**Talk-Client mit v4-Räumen und v1-Chat, der die vier Leseparameter an der gebauten URL festnagelt, 304 als leeres Fenster liest und den Verlaufs-Cursor aus dem Antwort-Header X-Chat-Last-Given nimmt; dazu 201 im Erfolgsraum von parse_ocs und die spreed-Erkennung samt Chat-Höchstlänge der Instanz.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-21T10:49:00Z
- **Completed:** 2026-08-21T11:09:29Z
- **Tasks:** 3
- **Files modified:** 8 (4 neu, 4 geändert)

## Accomplishments

- Die zwei blockierenden Transport-Befunde der Phase sind erledigt, bevor irgendein Werkzeug sie treffen kann: `parse_ocs` nimmt 201 an (eine gesendete Nachricht ist damit kein "unexpected status" mehr, der zum zweiten Senden einlädt), und ein leerer Verlauf mit HTTP 304 ist ein leeres Fenster und nicht der Hinweis auf eine falsche Basis-URL.
- `clients/talk.py` baut genau drei Pfadformen (`GET /apps/spreed/api/v4/room`, `GET` und `POST /apps/spreed/api/v1/chat/{token}`) und keine vierte; kein Edit-, Delete-, Schedule-, Summarize-, Pin-, Reminder-, Attachment- und Share-Pfad, und das Wort für stilles Senden steht nirgends in der Datei.
- `READ_ONLY_PARAMS` hält `lookIntoFuture=0`, `setReadMarker=0`, `markNotificationsAsRead=0` und `noStatusUpdate=1` als Modulkonstante mit einer Begründung je Wert; ein Unit-Test behauptet alle vier wörtlich an der gebauten URL, `lookIntoFuture=0` zusätzlich einzeln.
- Die Paginierung des Verlaufs kommt aus dem Antwort-Header. Ein Fenster mit Status 200, leerer Liste und gesetztem Header liefert `([], id)` und damit weiterhin eine nächste Seite; das ist der Fall, an dem eine Ableitung aus den Nachrichten-Ids stillschweigend älteren Verlauf verschwiegen hätte.
- Die App-Erkennung kennt `spreed`, liest die Sektion als "vorhanden und nicht leer" und liefert die Chat-Höchstlänge der Instanz mit, damit die Kappe von TALK-03 nicht doppelt gepflegt wird.
- Keine bestehende Familie ändert ihr Verhalten: `uv run pytest -q` ist über die ganze Default-Auswahl grün, `check_tool_budget.py` meldet unverändert 18 Werkzeuge, und `pyproject.toml`, `uv.lock`, `ids.py`, `provider_map.py`, `tools/chatgpt.py` und `tools/context.py` sind unberührt.

## Task Commits

Each task was committed atomically:

1. **Task 1: 201 im Erfolgsraum des OCS-Parsers und spreed in der App-Erkennung** - `7c7b7c8` (feat)
2. **Task 2: Der Talk-Client mit den vier Leseparametern, der 304 und dem Header-Cursor** - `7e08b9c` (feat)
3. **Task 3: Unit-Abdeckung des Clients, behauptet an der gebauten Anfrage** - `244f980` (test)

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/talk.py` (neu) - Talk-Transport: `get_rooms`, `get_messages`, `send_message`, `web_url`, `_path_token`, `READ_ONLY_PARAMS`, `MAX_MESSAGES`, `LAST_GIVEN_HEADER`.
- `src/mcp_connector/nextcloud/clients/ocs.py` - `_OK_STATUS` ist `frozenset({100, 200, 201})`, mit Begründung im `#:`-Kommentar. `_check_transport` unverändert.
- `src/mcp_connector/nextcloud/capabilities.py` - `spreed_available`, `spreed_features`, `spreed_chat_max_length`, `DEFAULT_CHAT_MAX_LENGTH`, `_chat_max_length`, `_MISSING["spreed"]`, `has("spreed")`; Modul-Docstring nennt vier optionale Apps.
- `tests/unit/test_talk_client.py` (neu) - 25 Tests mit `respx`, eingefrorene URL-Literale beider API-Versionen.
- `tests/fixtures/talk_rooms.json` (neu) - sechs Konversationen in echter Antwortform (Anruf, Lobby, Signaling, Avatar, Aufzeichnung), Server-Reihenfolge widerspricht `lastActivity`, je ein Eintrag mit `isArchived`, `readOnly` 1, `type` 4, `permissions` 0 bei `attendeePermissions` 0 und `permissions` 254 bei `attendeePermissions` 0.
- `tests/fixtures/talk_messages.json` (neu) - Verlaufsantwort mit zwei Systemnachrichten, `messageParameters` mit `{actor}`, Erwähnung und `{file}`, einer bearbeiteten Nachricht mit `lastEditTimestamp`, einer Nachricht mit 1013 Zeichen und den Pflichtfeldern `reactions`, `parent`, `markdown`, `isReplyable`.
- `tests/unit/test_ocs_capabilities.py` - sieben neue Fälle (spreed vorhanden, fehlend, leeres Array, einzelner Feature-String, unlesbare Chat-Länge, `require_app` für Talk, 201-Envelope plus 401-Gegenprobe); der Test für einen unbekannten App-Namen nutzt jetzt `mail` statt `spreed`.
- `vulture_whitelist.py` - zwei Blöcke mit Begründung für die Namen, die auf ihren Aufrufer aus Plan 09-02 warten.

## Decisions Made

- **Rückgabetyp von `get_messages`:** `tuple[list[dict[str, Any]], int | None]`. Erstes Element sind die Nachrichten in der Reihenfolge der App (neueste zuerst), zweites Element die Fortsetzung. Plan 09-03 baut gegen genau diese Signatur.
- **Fehlender `X-Chat-Last-Given`-Header:** ergibt `None`, genau wie ein Header, der keine Zahl ist. Beides heisst "keine nächste Seite anbieten"; ein geratener Cursor wäre schlimmer als ein fehlender. Die 304 liefert ebenfalls `None`.
- **Feldnamen der drei neuen Capabilities-Felder:** `spreed_available: bool`, `spreed_features: tuple[str, ...]`, `spreed_chat_max_length: int`, plus die Modulkonstante `DEFAULT_CHAT_MAX_LENGTH = 32000` als Rückfall. Der Schlüssel in `has()` und in `_MISSING` heisst `"spreed"`, nicht `"talk"`.
- **`include_last_message` ohne Vorgabewert:** die Entscheidung ist am Aufrufer sichtbar, weil die Vorschau der letzten Nachricht der grösste Einzelposten der Antwort ist und die Sende-Vorprüfung sie nicht braucht.
- **TALK-01 bis TALK-03 bleiben Pending** in REQUIREMENTS.md. Der Plan trägt sie im Frontmatter, aber ihr Wortlaut spricht von `talk_browse` und `talk_send`; die gibt es erst mit Plan 09-02 und 09-03. Dasselbe Vorgehen wie bei TOOL-09 und SRV-03 in Phase 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bestehender Test benutzte `spreed` als den unbekannten App-Namen**

- **Found during:** Task 1
- **Issue:** `tests/unit/test_ocs_capabilities.py::test_has_refuses_an_app_this_server_does_not_check` erwartete, dass `caps.has("spreed")` einen `ValueError` auslöst. Mit `spreed` als vierter geprüfter App war dieser Test rot, und das Akzeptanzkriterium verlangt ausdrücklich, dass `has("spreed")` ohne `ValueError` antwortet.
- **Fix:** Der Test prüft die Ablehnung jetzt mit `mail`, also mit einer App, die dieser Server nicht prüft; der Docstring sagt, warum der Name gewechselt hat und dass die Zuordnung in `has()` die Liste der Apps ist.
- **Files modified:** tests/unit/test_ocs_capabilities.py
- **Verification:** `uv run pytest tests/unit/test_ocs_capabilities.py -q` grün, `uv run pytest -q` grün.
- **Committed in:** `7c7b7c8` (Task 1)

**2. [Rule 3 - Blocking] Fünf neue Namen ohne Produktionsaufrufer liessen das vulture-Gate reissen**

- **Found during:** Task 1 und Task 2
- **Issue:** Das Akzeptanzkriterium von Task 3 verlangt ein grünes `uv run vulture src/mcp_connector vulture_whitelist.py` **ohne neuen Whitelist-Eintrag**. Das ist in diesem Plan konstruktiv unerreichbar: `spreed_features`, `spreed_chat_max_length`, `get_rooms`, `get_messages` und `send_message` bekommen ihren Aufrufer erst mit `tools/talk.py` in Plan 09-02, und vulture läuft in diesem Projekt bei voller Konfidenz.
- **Fix:** Zwei Blöcke in `vulture_whitelist.py` mit Begründung je Name, nach dem wörtlichen Vorbild des Blocks "The transport layer of the Tables family (plan 08-02, dissolved in plan 08-03)". Beide Blöcke nennen den Plan, mit dem die Namen die Liste wieder verlassen. `web_url` steht nicht darin, weil der Name in der Tables-Familie einen Produktionsaufrufer hat.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` mit Exit-Code 0; ohne die Blöcke meldet es fünf Namen.
- **Committed in:** `7c7b7c8` (zwei Capabilities-Felder) und `7e08b9c` (drei Transportfunktionen)

**3. [Rule 1 - Bug] Das Wort für stilles Senden stand zweimal in der Prosa des neuen Moduls**

- **Found during:** Task 2
- **Issue:** Der erste Entwurf von `clients/talk.py` benutzte "silent untruth" und "silently hide" in zwei Docstrings. Das Modul muss frei von dieser Zeichenfolge bleiben, damit Plan 09-04 sie per Gate fernhalten kann; die Quelltext-Behauptung aus Task 3 wäre rot gewesen.
- **Fix:** Beide Sätze umformuliert ("an untruth nobody can see", "hide ... without saying so"), Aussage unverändert.
- **Files modified:** src/mcp_connector/nextcloud/clients/talk.py
- **Verification:** `grep -E "silent" src/mcp_connector/nextcloud/clients/talk.py` ohne Treffer; `test_the_module_has_no_edit_remove_or_scheduled_send_path` grün.
- **Committed in:** `7e08b9c` (Task 2)

**4. [Rule 3 - Blocking] Emojis in den Fixtures**

- **Found during:** Task 2
- **Issue:** Der erste Entwurf von `talk_rooms.json` trug den echten Namen der Changelog-Konversation ("Talk updates" mit Häkchen-Emoji) und eine Reaktion als Emoji-Schlüssel. Die globale Projektregel verbietet Emojis.
- **Fix:** Name auf "Talk updates" gekürzt, `reactions` auf `{}`. Die Umlaute in den Anzeigenamen und Beschreibungen bleiben und sind der eigentliche Zweck dieser Testdaten.
- **Files modified:** tests/fixtures/talk_rooms.json
- **Verification:** Prüfung auf Zeichen oberhalb U+2000 in der Datei ohne Treffer.
- **Committed in:** `7e08b9c` (Task 2)

**5. [Rule 3 - Blocking] `SIM300` auf einer Behauptung über `_OK_STATUS`**

- **Found during:** Task 1
- **Issue:** `assert ocs._OK_STATUS == frozenset({100, 200, 201})` gilt ruff als Yoda-Bedingung, weil es die rechte Seite für ein Literal hält; `ruff check .` war rot.
- **Fix:** `assert sorted(ocs._OK_STATUS) == [100, 200, 201]`, dieselbe Aussage plus eine feste Reihenfolge in der Fehlermeldung.
- **Files modified:** tests/unit/test_ocs_capabilities.py
- **Verification:** `uv run ruff check .` grün.
- **Committed in:** `7c7b7c8` (Task 1)

---

**Total deviations:** 5 auto-fixed (3 blockierend, 1 Bug, 1 blockierend wegen Projektregel)
**Impact on plan:** Kein Scope-Zuwachs. Vier der fünf Punkte sind Gates dieses Repos, die der Plan nicht vorhergesehen hat (bestehender Test auf `spreed`, vulture bei voller Konfidenz, `SIM300`, Emoji-Regel); der fünfte war ein echter Fehler im ersten Entwurf des Moduls. Die einzige Abweichung von einem Akzeptanzkriterium ist der neue Whitelist-Eintrag, und er folgt dem dokumentierten Vorbild aus Plan 08-02.

## Issues Encountered

- Die Fortsetzung des Verlaufs war der einzige Punkt ohne Vorbild in dieser Codebasis: keine andere Route liefert einen Header als Nutzlast. Gelöst mit einer benannten Konstante `LAST_GIVEN_HEADER` und einem Tupel als Rückgabe, plus zwei Tests, die den leeren Erfolg (304) und das leere Fenster mit brauchbarem Cursor (200) auseinanderhalten.
- Für die Behauptung "die 304 erreicht `parse_ocs` nie" gibt es kein Muster im Analog. Gelöst mit einem `monkeypatch` auf `ocs.parse_ocs`, der bei einem Aufruf fehlschlägt; damit ist die Behauptung konstruktiv statt kommentiert.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 09-02 (`tools/talk.py`) kann gegen die drei Client-Funktionen bauen. Die Signaturen stehen: `get_rooms(client, creds, *, include_last_message)`, `get_messages(client, creds, token, *, limit, last_known_message_id=0) -> tuple[list[dict], int | None]`, `send_message(client, creds, token, *, message)`.
- Die Vorprüfung von TALK-03 liest `permissions` (nicht `attendeePermissions`), `readOnly` und `type` aus der Konversationsliste; `tests/fixtures/talk_rooms.json` enthält für jeden dieser Fälle einen Eintrag, inklusive des Regressionsfalls `permissions` mit Bit 128 bei `attendeePermissions` 0.
- Die Kappe von TALK-03 kommt aus `capabilities.spreed_chat_max_length`, der Rückfall aus `capabilities.DEFAULT_CHAT_MAX_LENGTH`.
- Offen für Plan 09-02: die fünf Namen in `vulture_whitelist.py` müssen mit dem Plan, der sie aufruft, wieder verschwinden. Das ist die Regel dieser Datei und steht in beiden Blöcken als Auftrag.
- Nicht Teil dieses Plans und weiterhin offen: `tools/talk.py`, `server/reg_talk.py`, der Admin-Schalter (TALK-04) und der Live-Nachweis der Nebenwirkungsfreiheit. TALK-01 bis TALK-03 bleiben deshalb Pending.

## Self-Check

- `src/mcp_connector/nextcloud/clients/talk.py` FOUND
- `tests/unit/test_talk_client.py` FOUND
- `tests/fixtures/talk_rooms.json` FOUND
- `tests/fixtures/talk_messages.json` FOUND
- Commit `7c7b7c8` FOUND
- Commit `7e08b9c` FOUND
- Commit `244f980` FOUND
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run vulture src/mcp_connector vulture_whitelist.py` alle grün
- `uv run pytest -q` grün (Default-Auswahl), `uv run pytest tests/unit/test_talk_client.py -q` 25 Tests grün
- `uv run python scripts/check_tool_budget.py` Exit-Code 0, 18 Werkzeuge
- `git diff --stat` ohne Änderung an `pyproject.toml`, `uv.lock`, `ids.py`, `provider_map.py`, `tools/chatgpt.py`, `tools/context.py`

## Self-Check: PASSED

---
*Phase: 09-talk*
*Completed: 2026-08-21*
