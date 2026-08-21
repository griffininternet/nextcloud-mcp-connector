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
status: resolved
fixed_at: 2026-08-21T15:52:00Z
fixed: 5
deferred: 4
resolution:
  WR-01: fixed 9d67b36
  WR-02: fixed 4e5eded
  WR-03: fixed 422c1a7
  IN-01: fixed 7ca35fc
  IN-02: deferred
  IN-03: deferred
  IN-04: deferred
  IN-05: fixed 31fbe9c
  IN-06: deferred
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
**Resolution:** BEHOBEN in `9d67b36`. Zeile 180 sagt jetzt "same 20 tools", damit steht die Seite auf allen drei Produktaussagen (Zeile 11, 74, 180) auf derselben Zahl. Zeile 431 bleibt unverändert: "the measured run Open WebUI listed all 16 tools" ist eine datierte Messzeile und genau der Fall, den das Gate offenhalten soll. Die optionale Gate-Verschärfung ist **zurückgestellt**: sie ist eine Änderung an der Testlogik mit Wirkung auf jede datierte Zeile in `docs/` und gehört nicht in einen Doku-Fix.

### WR-02: conference-demo.md Schritt 5 widerspricht sich selbst und dem Bootstrap

**File:** `docs/conference-demo.md:255-270`
**Issue:** Zwei Fehler in einem Demo-Schritt. Erstens lautet die Sprechzeile "Eighteen tools, and here is what is not among them", zwei Absätze über der Pflichtausgabe "OK on every one of the twenty tools" und der Erwartung `tools=20` in Schritt 0 (Zeile 140). Das ausgeschriebene "Eighteen" ist für das Zahlen-Gate unsichtbar (Regex matcht nur Ziffern). Zweitens verlangt die Sichtprüfung "SKIP on the writes that need an object this server cannot create: ... and a Talk conversation this account may write into". `scripts/bootstrap_exapp.sh` legt für alice aber genau so eine beschreibbare Konversation an (`MCP-Talk-offen-...`, readonly=0), also findet `_sendable_conversation` sie und `talk_send` antwortet `OK`, nicht `SKIP`. Auf der Bühne stimmt die Checkliste nicht mit dem Lauf überein.
**Fix:** Sprechzeile auf "Twenty tools" ändern und die SKIP-Erwartung korrigieren: auf der Bootstrap-Topologie skippen nur `deck_create_card` und `tables_create_row`; `talk_send` postet in die Bootstrap-Konversation und antwortet `OK` (dann auch benennen, dass der Lauf eine Nachricht hinterlässt).
**Resolution:** BEHOBEN in `4e5eded`. Beide Fehler: die Sprechzeile lautet "Twenty tools", und die Sichtprüfung nennt jetzt `OK` oder `SKIP` auf allen zwanzig Tools, davon genau zwei `SKIP` (`deck_create_card`, `tables_create_row`), und sagt ausdrücklich, dass `talk_send` nicht dazugehört, weil `scripts/bootstrap_exapp.sh` alice eine beschreibbare Konversation hinterlässt, sowie dass der Lauf eine Nachricht hinterlässt. Gegengeprüft am Code: `ensure_talk_room alice ... "${TALK_ROOM_OPEN_KEY}" ... 0` legt sie mit `readonly=0` an, und `_sendable_conversation` in `scripts/acceptance_all_tools.py` findet sie über `can_send`. Der alte Satz "`OK` on every one of the twenty tools ... and `SKIP` on ..." war zusätzlich in sich widersprüchlich und ist mit aufgelöst.

### WR-03: README-Familie zieht die Talk-Familie nicht nach (alle drei Sprachen)

**File:** `README.md:5,164-177,349-354,381` (analog `README.de.md:7,358-360,392`, `README.fr.md:369-371,407`)
**Issue:** Drei Lücken in derselben Datei, in allen drei Sprachfassungen:
1. Die Tabelle "Environment variables" führt `NC_MCP_TALK_SEND` nicht auf, obwohl `appinfo/info.xml` sechs Variablen deklariert und die anderen fünf ExApp-Variablen gelistet sind. Der Admin-Schalter ist die Gegenmaßnahme TALK-04; ein Administrator, der nur die README liest, erfährt nicht, dass er existiert.
2. Der Abschnitt "Optional apps" und die Zeile in "Known limitations" nennen "Notes, Deck and Tables" und "ignore those seven tools". Talk (App-ID `spreed`) ist seit dieser Phase die vierte optionale App (`capabilities.require_app`), und mit `talk_browse`/`talk_send` sind es neun Tools.
3. Der Eröffnungssatz nennt "files, calendar, notes, deck, contacts" ohne Tables und Talk; die Store-Beschreibung in info.xml nennt beide bereits.
**Fix:** `NC_MCP_TALK_SEND` in die Variablen-Tabelle aufnehmen (Mode: ExApp und alle, Purpose: schaltet das Senden von Talk-Nachrichten instanzweit ab, an sofern nicht off), "Notes, Deck, Tables and Talk ... nine tools" schreiben, Eröffnungssatz um Tables und Talk ergänzen, und die deutsche und französische Fassung nachziehen (Projektregel: Doku-Sync über alle Sprachfassungen).
**Resolution:** BEHOBEN in `422c1a7`, alle drei Lücken in allen drei Sprachfassungen:
1. `NC_MCP_TALK_SEND` steht in jeder Variablen-Tabelle. Mode ist `all` und nicht `ExApp`, und das ist die genauere Angabe: `config.talk_send_enabled` liest `os.environ` in jedem Modus, das Administrationsformular ist nur der zweite Schreibweg und wird in der Purpose-Spalte als solcher benannt.
2. "Optionale Apps" und die Einschränkungs-Tabelle nennen "Notes, Deck, Tables und Talk" mit **neun** Tools (nachgezählt an `EXPECTED_TOOLS`: 3 Notes + 2 Deck + 2 Tables + 2 Talk), und der Beispielsatz für eine fehlende App ist um den echten Wortlaut "The Talk app is not available on this Nextcloud." aus `capabilities._MISSING["spreed"]` ergänzt.
3. Der Eröffnungssatz nennt Tables und Talk, im Wortlaut und in der Reihenfolge der Store-Beschreibung in `appinfo/info.xml` ("files, calendar, notes, deck, contacts, Tables and Talk").
Gegengeprüft: kein "seven tools" / "sieben Tools" / "sept outils" mehr übrig, kein Em-Dash in den neuen Zeilen, die einzigen Nicht-ASCII-Zeichen im Diff sind Umlaute und französische Akzente, und das vom Vokabular-Gate verbotene Wort kommt in keiner der drei Dateien vor.

## Info

### IN-01: Leeres Token im Send-Pfad kostet einen Nextcloud-Request statt der billigen Ablehnung

**File:** `src/mcp_connector/tools/talk.py:206-211`
**Issue:** `browse(level="messages")` weist ein fehlendes Token vor jedem Request ab (Zeile 134-135). `send` hat keinen symmetrischen Check: ein leerer `token` läuft durch Switch, Capabilities, Längen- und Mention-Prüfung und löst dann in `_room` einen `get_rooms`-Request aus, bevor die Ablehnung "The token '' is not in the conversation list" kommt. Bei einem hypothetischen Raum ohne Token im Listen-Payload würde der leere String sogar matchen (der Pfad-Guard in `send_message` fängt das zwar ab, aber erst nach dem Match).
**Fix:** Vor `_room` denselben Check wie in `browse` einbauen: `if not conversation: raise ToolError(..., hint=_CONVERSATION_HINT)`.
**Resolution:** BEHOBEN in `7ca35fc`. Der Check steht direkt vor `_room`, also vor jedem HTTP-Aufruf des Token-Pfads; die Meldung nennt den Token, der Hinweis ist `_CONVERSATION_HINT`. Der Docstring zählt jetzt sechs statt fünf Ablehnungen und benennt beide Gründe (kein Request für ein fehlendes Argument, und der leere String kann keine Konversation matchen, die im Listen-Payload ohne eigenen Token steht). Test: `test_a_send_without_a_token_never_asks_for_the_conversation_list`, parametrisiert über `""`, `"   "` und `None`, behauptet null Aufrufe auf beiden Talk-Routen. Integrationstests waren nicht nötig, weil ausschließlich ein Ablehnungspfad vor dem ersten HTTP-Aufruf betroffen ist. Alle Gates grün (pytest, ruff check, ruff format --check, pyright, vulture, check_tool_budget).

### IN-02: Gruppen- und Team-Mentions fallen nicht unter den Kollektiv-Mention-Schutz

**File:** `src/mcp_connector/tools/talk.py:113,195-204`
**Issue:** `_MENTION_ALL` weist nur `@all` und `@here` ab. Talk kennt auch `@"group/<id>"` und `@"team/<id>"`, die eine ganze Gruppe benachrichtigen; ein Tool-Aufruf kann damit weiterhin viele Menschen auf einmal anpingen (dieselbe Risikoklasse wie T-09-23, nur enger gefasst). Das ist möglicherweise eine bewusste Grenze, sie ist aber nirgends als solche dokumentiert.
**Fix:** Entweder das Muster um `@\"?(group|team)/` erweitern oder die bewusste Grenze im Docstring von `send` und im Threat-Kommentar festhalten.
**Resolution:** ZURÜCKGESTELLT. Keine der beiden Varianten ist risikofrei: eine Musteränderung verschiebt eine Sicherheitsgrenze und braucht eigene Positiv- und Negativtests gegen echte Talk-Mention-Syntax (auch die Form ohne Anführungszeichen), und die Doku-Variante ist eine bewusste Produktentscheidung darüber, wie weit der Kollektiv-Mention-Schutz reichen soll. Beides gehört in eine eigene Aufgabe mit Owner-Entscheid, nicht in einen Review-Fix.

### IN-03: check_tool_budget misst pro Tool Zeichen, insgesamt Bytes

**File:** `scripts/check_tool_budget.py:54-63`
**Issue:** Das Gesamtbudget wird auf `len(blob.encode("utf-8"))` gemessen, das Pro-Tool-Limit auf `len(json.dumps(tool, ..., ensure_ascii=False))`, also Zeichen. Ein Tool mit vielen Nicht-ASCII-Zeichen wird pro Tool unterzählt; die beiden Grenzen messen nicht dieselbe Einheit.
**Fix:** Auch pro Tool `.encode("utf-8")` zählen.
**Resolution:** ZURÜCKGESTELLT. Die Änderung ist klein, verschiebt aber eine Budget-Grenze: pro Tool würde ab dann mehr gezählt, und `check_tool_budget.py` ist ein Gate, das im Zweifel den Push blockiert. Das gehört mit einem Messlauf gegen das aktuelle Pro-Tool-Limit zusammen entschieden, nicht blind mitgenommen. Der Lauf steht bei 14312 von 15000 Bytes gesamt, es ist also kein akuter Druck.

### IN-04: Cursor auf level=conversations wird stillschweigend ignoriert

**File:** `src/mcp_connector/tools/talk.py:116-136`
**Issue:** `browse` liest den `cursor`-Parameter nur im Messages-Zweig. Ein Modell, das auf der Konversationsebene ein Cursor-Handle übergibt (etwa eines aus einer Messages-Antwort), erhält kommentarlos wieder dieselbe erste Seite. Die Entscheidung "kein Cursor auf dieser Ebene" ist dokumentiert, ein übergebener Cursor wird aber weder abgelehnt noch benannt.
**Fix:** Auf der Konversationsebene einen nicht-leeren Cursor mit einem Satz abweisen ("Die Konversationsliste hat keine Seiten; truncated plus total nennen den Schnitt").
**Resolution:** ZURÜCKGESTELLT. Eine neue Ablehnung im Lesepfad ist eine Verhaltensänderung an einer öffentlichen Tool-Signatur: ein Modell, das heute einen Cursor mitschickt und eine Antwort bekommt, bekäme dann einen Fehler. Das ist eine Design-Entscheidung (abweisen oder benennen und ignorieren) und braucht eigene Tests für beide Ebenen.

### IN-05: Veralteter Kommentar "declares the same four variables" im Bootstrap

**File:** `scripts/bootstrap_exapp.sh:843-844`
**Issue:** Der Kommentar über `json_info` sagt "appinfo/info.xml declares the same four variables for the installation that registers from the manifest". Das Manifest deklariert seit dieser Phase sechs Variablen (info.xml, Kommentar dort korrekt: "The six variables").
**Fix:** "four" durch "six" ersetzen.
**Resolution:** BEHOBEN in `31fbe9c`. Nachgezählt: `grep -c "<name>NC_MCP" appinfo/info.xml` ergibt 6, und `bash -n scripts/bootstrap_exapp.sh` ist sauber.

### IN-06: Längen-Vorprüfung zählt Zeichen, Talk zählt womöglich anders

**File:** `src/mcp_connector/tools/talk.py:186-194`
**Issue:** Die Vorprüfung vergleicht `len(text)` (Python-Zeichen) mit `config.chat.max-length`. Talk 24 prüft die Länge serverseitig (PHP), je nach Implementierung in Bytes bzw. mit anderer Zählung; eine umlautreiche Nachricht knapp unter der Zeichen-Grenze kann die Vorprüfung passieren und trotzdem Talks eigene 400 kassieren. Der Fall ist abgefangen (400 wird mit Talks eigener Meldung durchgereicht, Test vorhanden), aber der Docstring-Anspruch "the limit is not maintained a second time here" ist nur näherungsweise wahr.
**Fix:** Einen Satz im Docstring ergänzen, dass die Vorprüfung eine Näherung ist und Talks eigene Ablehnung der Rückhalt bleibt; keine Codeänderung nötig.
**Resolution:** ZURÜCKGESTELLT. Rein redaktionell und ohne Risiko, aber der Satz sollte sagen, *wie* Talk 24 tatsächlich zählt, und das ist im Review als "je nach Implementierung" offen geblieben. Ein Docstring, der eine Näherung durch eine zweite Vermutung erklärt, ist keine Verbesserung. Der Fall ist ohnehin abgefangen (400 wird mit Talks eigener Meldung durchgereicht, Test vorhanden); nachzuziehen, sobald die serverseitige Zählung einmal belegt ist.

---

## Fix-Lauf

Behoben: 5 von 9 (alle drei Warnings, dazu IN-01 und IN-05). Zurückgestellt: IN-02, IN-03, IN-04, IN-06.

| Finding | Ergebnis | Commit |
|---------|----------|--------|
| WR-01 | behoben | `9d67b36` |
| WR-02 | behoben | `4e5eded` |
| WR-03 | behoben | `422c1a7` |
| IN-01 | behoben | `7ca35fc` |
| IN-02 | zurückgestellt | |
| IN-03 | zurückgestellt | |
| IN-04 | zurückgestellt | |
| IN-05 | behoben | `31fbe9c` |
| IN-06 | zurückgestellt | |

Vier der sechs Infos sind zurückgestellt, weil sie keine reinen Doku-Korrekturen sind: IN-02 und IN-04 verschieben Grenzen einer öffentlichen Tool-Signatur, IN-03 verschiebt eine Gate-Grenze, und IN-06 bräuchte einen Befund zu Talks serverseitiger Zählung, den dieser Review offengelassen hat. Die Begründung steht bei jedem Finding.

Gates nach dem letzten Code-Fix, alle grün: `uv run python -m pytest -q` (2437 passed, 119 deselected), `ruff check .`, `ruff format --check .` (187 Dateien), `pyright` (0 errors), `vulture src scripts vulture_whitelist.py`, `scripts/check_tool_budget.py` (14312 von 15000 Bytes, 20 Tools).

---

_Reviewed: 2026-08-21T13:17:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Fixed: 2026-08-21T15:52:00Z_
_Fixer: Claude (gsd-code-fixer)_
