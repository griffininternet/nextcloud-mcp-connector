---
phase: 09-talk
reviewed: 2026-08-21T13:17:20Z
depth: standard
files_reviewed: 40
files_reviewed_list:
  - .env.exapp.example
  - .env.test.example
  - CHANGELOG.md
  - README.de.md
  - README.fr.md
  - README.md
  - appinfo/info.xml
  - docs/client-setup.md
  - docs/conference-demo.md
  - docs/conference-talk.md
  - docs/oauth-setup.md
  - scripts/acceptance_all_tools.py
  - scripts/bootstrap_exapp.sh
  - scripts/bootstrap_test_nc.sh
  - scripts/check_tool_budget.py
  - src/mcp_connector/config.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/exapp/admin_settings.py
  - src/mcp_connector/exapp/config_values.py
  - src/mcp_connector/exapp/ui/strings.py
  - src/mcp_connector/nextcloud/capabilities.py
  - src/mcp_connector/nextcloud/clients/ocs.py
  - src/mcp_connector/nextcloud/clients/talk.py
  - src/mcp_connector/server/reg_talk.py
  - src/mcp_connector/tools/talk.py
  - tests/contract/test_no_destructive_calls.py
  - tests/contract/test_tool_surface.py
  - tests/fixtures/talk_messages.json
  - tests/fixtures/talk_rooms.json
  - tests/integration/test_permission_fidelity_exapp.py
  - tests/integration/test_talk_roundtrip.py
  - tests/unit/test_config.py
  - tests/unit/test_exapp_admin_settings.py
  - tests/unit/test_exapp_config_values.py
  - tests/unit/test_exapp_entry.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_ocs_capabilities.py
  - tests/unit/test_talk_client.py
  - tests/unit/test_talk_tools.py
  - vulture_whitelist.py
findings:
  critical: 0
  warning: 3
  info: 6
  total: 9
status: issues_found
---

# Phase 9: Code-Review-Bericht

**Geprüft:** 2026-08-21T13:17:20Z
**Tiefe:** standard
**Dateien geprüft:** 40
**Status:** issues_found

## Summary

Geprüft wurde die neue Talk-Familie (Client `nextcloud/clients/talk.py`, Tools `tools/talk.py`, Registrierung `server/reg_talk.py`), die OCS-Erweiterungen (201 im Erfolgs-Set, 304-Sonderfall), der Admin-Schalter `NC_MCP_TALK_SEND` über alle drei Schichten (config, config_values, admin_settings, entry_exapp), die Bootstrap-Skripte, die Gates und die Doku.

Der Sicherheitskern hält der Prüfung stand: der Send-Pfad liest den Admin-Schalter vor jedem Netzwerkzugriff, ein erfundenes Token erreicht Nextcloud nie in einem Pfad (Listen-Lookup statt Einzelroute), das Token-Muster wird vor dem Pfadbau erzwungen, `@all`/`@here` werden mit Wortgrenze abgewiesen, fremder Text läuft durch `marks.without_marks`, der Byte-Cut schneidet auf Zeichengrenze, es gibt keinen Retry auf dem Send, und die destruktiven Routen sind durch zehn Talk-Nadeln mit Gegenproben verriegelt. Die Precedence-Kette des Schalters (Admin-Wert, Deploy-Variable, Code-Default) ist konsistent und per Test gehalten; der Rückschrieb in `os.environ` ist auf genau einen Schlüssel begrenzt und durch `test_the_entry_point_writes_exactly_one_key_into_the_process_environment` fixiert.

Was nicht mitgezogen wurde, ist die Dokumentation: drei Stellen widersprechen dem 20-Tool-Stand bzw. lassen die neue Familie und ihren Admin-Schalter aus. Das sind die drei Warnings. Kein Blocker.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Veralteter Tool-Count "same 16 tools" in client-setup.md

**File:** `docs/client-setup.md:180`
**Issue:** Der ExApp-Abschnitt sagt "same code, same 16 tools", während dieselbe Seite in Zeile 11 und 74 korrekt "20 tools" nennt. Das ist eine Produktaussage, keine datierte Messzeile, und sie ist seit Phase 8/9 falsch. Das Gate `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from` schlägt nur deshalb nicht an, weil die Seite an anderer Stelle (Zeile 715) den Holder `tests/contract/test_tool_surface.py` nennt, was jede weitere falsche Zahl auf der Seite freischaltet. Ein Leser des ExApp-Abschnitts hält 16 für den Stand.
**Fix:** Zeile 180 auf "same 20 tools" ändern (oder die Zahl ganz streichen: "same code, same tool set"). Optional das Gate verschärfen: die Holder-Erwähnung nur für Zeilen gelten lassen, die ein Datum tragen.

### WR-02: conference-demo.md Schritt 5 widerspricht sich selbst und dem Bootstrap

**File:** `docs/conference-demo.md:255-270`
**Issue:** Zwei Fehler in einem Demo-Schritt. Erstens lautet die Sprechzeile "Eighteen tools, and here is what is not among them", zwei Absätze über der Pflichtausgabe "OK on every one of the twenty tools" und der Erwartung `tools=20` in Schritt 0 (Zeile 140). Das ausgeschriebene "Eighteen" ist für das Zahlen-Gate unsichtbar (Regex matcht nur Ziffern). Zweitens verlangt die Sichtprüfung "SKIP on the writes that need an object this server cannot create: ... and a Talk conversation this account may write into". `scripts/bootstrap_exapp.sh` legt für alice aber genau so eine beschreibbare Konversation an (`MCP-Talk-offen-...`, readonly=0), also findet `_sendable_conversation` sie und `talk_send` antwortet `OK`, nicht `SKIP`. Auf der Bühne stimmt die Checkliste nicht mit dem Lauf überein.
**Fix:** Sprechzeile auf "Twenty tools" ändern und die SKIP-Erwartung korrigieren: auf der Bootstrap-Topologie skippen nur `deck_create_card` und `tables_create_row`; `talk_send` postet in die Bootstrap-Konversation und antwortet `OK` (dann auch benennen, dass der Lauf eine Nachricht hinterlässt).

### WR-03: README-Familie zieht die Talk-Familie nicht nach (alle drei Sprachen)

**File:** `README.md:5,164-177,349-354,381` (analog `README.de.md:7,358-360,392`, `README.fr.md:369-371,407`)
**Issue:** Drei Lücken in derselben Datei, in allen drei Sprachfassungen:
1. Die Tabelle "Environment variables" führt `NC_MCP_TALK_SEND` nicht auf, obwohl `appinfo/info.xml` sechs Variablen deklariert und die anderen fünf ExApp-Variablen gelistet sind. Der Admin-Schalter ist die Gegenmaßnahme TALK-04; ein Administrator, der nur die README liest, erfährt nicht, dass er existiert.
2. Der Abschnitt "Optional apps" und die Zeile in "Known limitations" nennen "Notes, Deck and Tables" und "ignore those seven tools". Talk (App-ID `spreed`) ist seit dieser Phase die vierte optionale App (`capabilities.require_app`), und mit `talk_browse`/`talk_send` sind es neun Tools.
3. Der Eröffnungssatz nennt "files, calendar, notes, deck, contacts" ohne Tables und Talk; die Store-Beschreibung in info.xml nennt beide bereits.
**Fix:** `NC_MCP_TALK_SEND` in die Variablen-Tabelle aufnehmen (Mode: ExApp und alle, Purpose: schaltet das Senden von Talk-Nachrichten instanzweit ab, an sofern nicht off), "Notes, Deck, Tables and Talk ... nine tools" schreiben, Eröffnungssatz um Tables und Talk ergänzen, und die deutsche und französische Fassung nachziehen (Projektregel: Doku-Sync über alle Sprachfassungen).

## Info

### IN-01: Leeres Token im Send-Pfad kostet einen Nextcloud-Request statt der billigen Ablehnung

**File:** `src/mcp_connector/tools/talk.py:206-211`
**Issue:** `browse(level="messages")` weist ein fehlendes Token vor jedem Request ab (Zeile 134-135). `send` hat keinen symmetrischen Check: ein leerer `token` läuft durch Switch, Capabilities, Längen- und Mention-Prüfung und löst dann in `_room` einen `get_rooms`-Request aus, bevor die Ablehnung "The token '' is not in the conversation list" kommt. Bei einem hypothetischen Raum ohne Token im Listen-Payload würde der leere String sogar matchen (der Pfad-Guard in `send_message` fängt das zwar ab, aber erst nach dem Match).
**Fix:** Vor `_room` denselben Check wie in `browse` einbauen: `if not conversation: raise ToolError(..., hint=_CONVERSATION_HINT)`.

### IN-02: Gruppen- und Team-Mentions fallen nicht unter den Kollektiv-Mention-Schutz

**File:** `src/mcp_connector/tools/talk.py:113,195-204`
**Issue:** `_MENTION_ALL` weist nur `@all` und `@here` ab. Talk kennt auch `@"group/<id>"` und `@"team/<id>"`, die eine ganze Gruppe benachrichtigen; ein Tool-Aufruf kann damit weiterhin viele Menschen auf einmal anpingen (dieselbe Risikoklasse wie T-09-23, nur enger gefasst). Das ist möglicherweise eine bewusste Grenze, sie ist aber nirgends als solche dokumentiert.
**Fix:** Entweder das Muster um `@\"?(group|team)/` erweitern oder die bewusste Grenze im Docstring von `send` und im Threat-Kommentar festhalten.

### IN-03: check_tool_budget misst pro Tool Zeichen, insgesamt Bytes

**File:** `scripts/check_tool_budget.py:54-63`
**Issue:** Das Gesamtbudget wird auf `len(blob.encode("utf-8"))` gemessen, das Pro-Tool-Limit auf `len(json.dumps(tool, ..., ensure_ascii=False))`, also Zeichen. Ein Tool mit vielen Nicht-ASCII-Zeichen wird pro Tool unterzählt; die beiden Grenzen messen nicht dieselbe Einheit.
**Fix:** Auch pro Tool `.encode("utf-8")` zählen.

### IN-04: Cursor auf level=conversations wird stillschweigend ignoriert

**File:** `src/mcp_connector/tools/talk.py:116-136`
**Issue:** `browse` liest den `cursor`-Parameter nur im Messages-Zweig. Ein Modell, das auf der Konversationsebene ein Cursor-Handle übergibt (etwa eines aus einer Messages-Antwort), erhält kommentarlos wieder dieselbe erste Seite. Die Entscheidung "kein Cursor auf dieser Ebene" ist dokumentiert, ein übergebener Cursor wird aber weder abgelehnt noch benannt.
**Fix:** Auf der Konversationsebene einen nicht-leeren Cursor mit einem Satz abweisen ("Die Konversationsliste hat keine Seiten; truncated plus total nennen den Schnitt").

### IN-05: Veralteter Kommentar "declares the same four variables" im Bootstrap

**File:** `scripts/bootstrap_exapp.sh:843-844`
**Issue:** Der Kommentar über `json_info` sagt "appinfo/info.xml declares the same four variables for the installation that registers from the manifest". Das Manifest deklariert seit dieser Phase sechs Variablen (info.xml, Kommentar dort korrekt: "The six variables").
**Fix:** "four" durch "six" ersetzen.

### IN-06: Längen-Vorprüfung zählt Zeichen, Talk zählt womöglich anders

**File:** `src/mcp_connector/tools/talk.py:186-194`
**Issue:** Die Vorprüfung vergleicht `len(text)` (Python-Zeichen) mit `config.chat.max-length`. Talk 24 prüft die Länge serverseitig (PHP), je nach Implementierung in Bytes bzw. mit anderer Zählung; eine umlautreiche Nachricht knapp unter der Zeichen-Grenze kann die Vorprüfung passieren und trotzdem Talks eigene 400 kassieren. Der Fall ist abgefangen (400 wird mit Talks eigener Meldung durchgereicht, Test vorhanden), aber der Docstring-Anspruch "the limit is not maintained a second time here" ist nur näherungsweise wahr.
**Fix:** Einen Satz im Docstring ergänzen, dass die Vorprüfung eine Näherung ist und Talks eigene Ablehnung der Rückhalt bleibt; keine Codeänderung nötig.

---

_Reviewed: 2026-08-21T13:17:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
