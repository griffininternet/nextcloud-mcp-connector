---
phase: 09-talk
verified: 2026-08-21T13:47:50Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 9: Talk Verifizierungsbericht

**Phasenziel:** Nutzer kann seine Konversationen und deren Verlauf lesen, ohne dass dieses Lesen irgendetwas an seinem Zustand verändert, und er kann eine Nachricht senden, ohne dass ein Modell dabei die Adressierung erfinden oder eine gesperrte Konversation treffen kann. Der Administrator behält den Ausgangskanal in der Hand.

**Verifiziert:** 2026-08-21T13:47:50Z
**Stand:** HEAD, Commit `0f2603d` (nach Code-Review und Fix-Pass, 09-REVIEW.md)
**Status:** passed
**Re-Verifizierung:** Nein, initiale Verifizierung

## Wichtiger Hinweis zur Prüfmethodik

Diese Verifizierung wurde bewusst nicht auf Basis der SUMMARY-Behauptungen durchgeführt, sondern:

1. Statischer Code wurde direkt gelesen (`tools/talk.py`, `clients/talk.py`, `reg_talk.py`, `config.py`, `capabilities.py`).
2. `uv run pytest -q` (Default-Auswahl) wurde selbst ausgeführt.
3. `uv run ruff check .`, `ruff format --check .`, `pyright`, `vulture` wurden selbst ausgeführt.
4. Die in den WICHTIGEN HINWEISEN explizit geforderten Live-Nachweise wurden **selbst gegen die laufenden Docker-Topologien nachgefahren**, nicht aus dem SUMMARY übernommen: `tests/integration/test_talk_roundtrip.py` und `tests/integration/test_permission_fidelity_exapp.py` mit `-m integration` gegen `.env.exapp`, dazu `scripts/acceptance_all_tools.py` gegen `.env.test` und `scripts/check_tool_budget.py`.
5. Der Fix-Pass aus 09-REVIEW.md (IN-01, Ablehnungspfad bei leerem Token in `tools/talk.py`) wurde im aktuellen Code direkt gegengeprüft, nicht nur über die Review-Notiz.

Alle Nachweise unten stammen aus diesen selbst durchgeführten Läufen.

## Goal Achievement

### Observable Truths

Quelle: ROADMAP.md Success Criteria Phase 9 (5 Kriterien), ergänzt um die PLAN-Frontmatter-`must_haves` aller fünf Pläne.

| # | Truth | Status | Evidenz |
|---|-------|--------|---------|
| 1 | Nutzer kann Konversationen listen (Token, Name, Typ, Ungelesen-/Erwähnungs-Zähler, letzte Aktivität), archivierte draußen, Kappe 50 | ✓ VERIFIED | `tools/talk.py::_conversations` sortiert nach `lastActivity` **vor** dem Kappen (`MAX_CONVERSATIONS = 50`), filtert `isArchived`; `_conversation()` projiziert exakt die genannten Felder. Live bestätigt: `test_the_conversation_level_lists_both_test_conversations_with_their_write_state` PASSED gegen laufende HaRP-Topologie (`count=5`, korrekte `read_only`-Werte). Unit-Tests in `test_talk_tools.py` decken Sortierung gegen absichtlich unsortierte Fixture ab. |
| 2 | Nutzer kann Verlauf lesen (Default 20, Max 50, Byte-Kappe/Nachricht, Paginierung über `lastKnownMessageId`), aufgelöste Platzhalter/Mentions, keine Systemnachrichten | ✓ VERIFIED | `tools/talk.py::_messages` und `_resolve()` lösen `{placeholder}` und Mentions auf; `KEPT_TYPES`-Positivliste entfernt Systemnachrichten; `_capped()` UTF-8-Byte-Kappe bei `MAX_MESSAGE_BYTES=800`; Cursor aus `X-Chat-Last-Given`-Header (`clients/talk.py::get_messages`), nie aus `len(results)`. Live bestätigt: `test_the_live_history_url_carries_the_four_read_only_parameters` und `test_an_empty_history_is_an_empty_answer_and_not_a_hint_about_the_base_url` PASSED. |
| 3 | Nach Lesevorgang nachweislich nichts verändert: kein Lesemarker, keine quittierte Benachrichtigung, kein Online-Status, kein Long-Polling; positiv behauptender Test hält jeden der vier Parameter fest | ✓ VERIFIED | `clients/talk.py::READ_ONLY_PARAMS` erzwingt `lookIntoFuture=0, setReadMarker=0, markNotificationsAsRead=0, noStatusUpdate=1` als Modulkonstante (kein Tool-Argument). **Live gegen laufende Instanz gemessen** (nicht nur unit-behauptet): `test_reading_the_history_changes_nothing_about_the_account` PASSED, Messwert `lastReadMessage 41 -> 41, unreadMessages 0 -> 0, unreadMention False -> False, lastCommonReadMessage 41 -> 41`. Die live gebaute URL zeigt exakt die vier Parameter (`test_the_live_history_url_carries_the_four_read_only_parameters`). |
| 4 | Nutzer kann Nachricht senden, nur adressiert per Token aus Lesewerkzeug; schreibgeschützte Konversation, fehlendes Chat-Recht, `@all`/`@here`, zu langer Text vorab abgelehnt; kein Edit/Delete/stilles Senden | ✓ VERIFIED | `tools/talk.py::send` prüft Token gegen `get_rooms()` (nie `GET /room/{token}` mit Modell-Token), `_may_send()` liest aufgelöstes `permissions`-Bit 128 (nicht `attendeePermissions`, T3-Regression getestet), Typ 4 (Changelog) gesperrt, Typ 6 erlaubt, `_MENTION_ALL`-Regex mit Wortgrenze lehnt `@all`/`@here` ab, erlaubt `@allan`/`@allison`. Kein `.put(`, `.patch(`, `.delete(`, `/schedule` etc. im Client (Gate-getestet). Live bestätigt: `test_a_sent_message_is_found_again_in_the_history_of_the_same_conversation` und `test_a_send_into_the_write_protected_conversation_is_refused_with_a_next_step` sowie `test_a_token_that_is_not_in_the_list_never_reaches_nextcloud_in_a_path` PASSED. **IN-01-Fix bestätigt:** leerer Token wird jetzt vor `_room()` abgewiesen (`if not conversation: raise ToolError`, Zeile 211-215 in `tools/talk.py`), Test `test_a_send_without_a_token_never_asks_for_the_conversation_list` grün. |
| 5 | Administrator kann Senden instanzweit abschalten; abgeschalteter Schalter -> Fehlersatz samt nächstem Schritt, gemessen über ganze Kette (Settings-Form, Overlay-Lesepfad, Wirkung am Werkzeug) | ✓ VERIFIED | Kette komplett: `appinfo/info.xml` deklariert `NC_MCP_TALK_SEND` (6. Variable), `admin_settings.py` liefert 6. Formularfeld (Checkbox, `default: True`, kein `sensitive`), `config_values.py` bildet `talk_send` auf `config.ENV_TALK_SEND` ab, `entry_exapp.py` schreibt genau einen Schlüssel nach `os.environ` vor dem ersten Socket, `config.talk_send_enabled()` liest `not in _FALSE_VALUES` (Default an). `tools/talk.py::send` prüft den Schalter als **erste** Zeile vor `require_app` und jedem Client-Aufruf; Test belegt 0 HTTP-Aufrufe bei ausgeschaltetem Schalter. Live bestätigt: `test_the_admin_switch_is_established_and_not_assumed` PASSED (`talk_send_enabled() == True`, `NC_MCP_TALK_SEND` ungesetzt auf beiden Topologien). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artefakt | Erwartet | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/nextcloud/clients/talk.py` | Talk-Client mit `READ_ONLY_PARAMS`, `get_rooms`, `get_messages`, `send_message`, `web_url`, `_path_token` | ✓ VERIFIED | Existiert, genutzt von `tools/talk.py`, alle Signaturen wie im Plan spezifiziert |
| `src/mcp_connector/nextcloud/capabilities.py` | `spreed_available`, `spreed_features`, `spreed_chat_max_length` | ✓ VERIFIED | Alle drei Felder vorhanden und aus `parse()` befüllt |
| `src/mcp_connector/tools/talk.py` | `browse` (zwei Ebenen), `send` mit Vorprüfungen, `KEPT_TYPES` | ✓ VERIFIED | 598 Zeilen, `KEPT_TYPES` vorhanden, Schalter als erste Zeile in `send` |
| `src/mcp_connector/server/reg_talk.py` | Registrierung beider Werkzeuge, `Literal`-Enum, `READ_ONLY`/`CREATE_ONLY` | ✓ VERIFIED | 73 Zeilen, `talk_browse` mit `READ_ONLY`, `talk_send` mit `CREATE_ONLY`, Level als `Literal["conversations", "messages"]` |
| `src/mcp_connector/config.py` | `ENV_TALK_SEND`, `talk_send_enabled` | ✓ VERIFIED | Zeile 47 und 329, `_FALSE_VALUES` deckungsgleich mit `config_values` |
| `tests/contract/test_no_destructive_calls.py` | Zehn Talk-Nadeln + `ALLOWED_TALK_ROUTES` | ✓ VERIFIED | Zehn Nadeln (`/schedule`, `/summarize`, `/reminder` etc.) mit Begründungssatz, `ALLOWED_TALK_ROUTES` mit drei erlaubten Pfadformen |
| `tests/contract/test_tool_surface.py` | 20 Werkzeuge, Enum-Test, Verbotsliste | ✓ VERIFIED | `assert len(tools) == 20` (Zeile 434), Enum `["conversations", "messages"]` bestätigt |
| `appinfo/info.xml` | Talk in allen drei Store-Beschreibungen, `NC_MCP_TALK_SEND` deklariert | ✓ VERIFIED | Alle drei `<description>` enthalten "Talk", kein verbotenes Vokabular |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/talk.py` | `nextcloud/clients/talk.py` | `get_rooms`, `get_messages`, `send_message` | ✓ WIRED | Bestätigt per Codelesen und Live-Lauf (URL-Messwert `/ocs/v2.php/apps/spreed/api/v1/chat/o4vwrd7g?lookIntoFuture=0&...`) |
| `tools/talk.py::send` | `config.py::talk_send_enabled` | Erste Zeile vor `require_app` | ✓ WIRED | Zeile 177 vs. Zeile 188 (Reihenfolge im Code bestätigt) |
| `entry_exapp.py` | `config.py` | `os.environ[config.ENV_TALK_SEND] = ...` | ✓ WIRED | Genau eine Schreibstelle, mit vierzeiligem Begründungskommentar (Task-Verifikation ergab dies bereits in Plan 09-02, im aktuellen Code weiterhin vorhanden) |
| `server/reg_talk.py` | `tools/talk.py` | `talk_tools.browse`, `talk_tools.send` | ✓ WIRED | Direkter Import und Aufruf bestätigt |

### Live-Nachweise (selbst ausgeführt, nicht aus SUMMARY übernommen)

| Test-Datei | Kommando | Ergebnis |
|------------|----------|----------|
| `tests/integration/test_talk_roundtrip.py` | `pytest ... -m integration` gegen `.env.exapp` (laufende HaRP-Topologie) | 9/9 PASSED, inkl. Nebenwirkungsfreiheit-Messung |
| `tests/integration/test_permission_fidelity_exapp.py` | `pytest ... -m integration` gegen `.env.exapp` | 15/15 PASSED, inkl. 3 Talk-Zwei-Konten-Tests |
| `scripts/acceptance_all_tools.py` | gegen `.env.test` | `OK: all 20 tools answered over stdio`, inkl. `talk_browse` und `talk_send` |
| `scripts/check_tool_budget.py` | — | `14312 bytes, 20 tools, budget 15000`, `talk_browse: 861 bytes` |
| `uv run pytest -q` | Default-Auswahl (schließt `integration`/`matrix` aus) | Grün, alle Suiten |
| `uv run ruff check .` / `ruff format --check .` / `pyright` / `vulture` | — | Alle grün, 0 Fehler |
| `uv run pytest tests/contract/ -q` | — | Grün |

### Requirements Coverage

| Requirement | Quell-Plan | Beschreibung | Status | Evidenz |
|-------------|-----------|--------------|--------|---------|
| TALK-01 | 09-01, 09-03 | Konversationen listen | ✓ SATISFIED | Siehe Truth 1 |
| TALK-02 | 09-01, 09-03 | Verlauf lesen ohne Nebenwirkung | ✓ SATISFIED | Siehe Truth 2 und 3, live gemessen |
| TALK-03 | 09-01, 09-03 | Nachricht senden mit Vorprüfungen | ✓ SATISFIED | Siehe Truth 4, inkl. IN-01-Fix |
| TALK-04 | 09-02, 09-03 | Admin-Schalter | ✓ SATISFIED | Siehe Truth 5 |

Keine verwaisten Requirements: `.planning/REQUIREMENTS.md` mappt TALK-01 bis TALK-04 ausschließlich auf Phase 9, alle vier sind dort als "Complete" markiert und durch obige Evidenz gedeckt.

### Anti-Patterns Found

Keine Debt-Marker (`TBD`, `FIXME`, `XXX`) in den von dieser Phase geänderten Dateien. Keine Platzhalter-Implementierungen, keine leeren Handler, keine hartcodierten leeren Rückgaben in Produktionscode. Die Treffer für "placeholder" in `tools/talk.py` sind Fachbegriffe der Talk-API (`{placeholder}`-Syntax) und keine Stub-Marker.

### Code-Review-Nachvollzug (09-REVIEW.md)

Der Code-Review lief nach Abschluss der fünf Pläne und fand 3 Warnings + 6 Infos (keine Blocker). Fix-Pass behob 5 davon (alle drei Warnings, IN-01, IN-05), 4 Infos wurden bewusst zurückgestellt mit dokumentierter Begründung (IN-02, IN-03, IN-04, IN-06 — alle drei betreffen Verhaltensänderungen an öffentlichen Signaturen oder Gate-Grenzen, keine davon berührt ein must-have dieser Phase). Alle Fix-Commits (`9d67b36`, `4e5eded`, `422c1a7`, `7ca35fc`, `31fbe9c`) sind im geprüften HEAD (`0f2603d`) enthalten, gegengeprüft per `git log`.

Der IN-01-Fix (billige Ablehnung bei leerem Token im Send-Pfad) wurde direkt im aktuellen Code verifiziert, nicht nur aus der Review-Notiz übernommen: die Zeilen 211-215 in `tools/talk.py` zeigen den Guard vor `_room()`, und der zugehörige Test ist grün.

### Bekannter, akzeptierter Punkt (kein Gap)

Der ROADMAP-Ziel-Satz der Phase erwähnt "neue Kinds" und "erster `ocs_post`" — beide Formulierungen sind laut Vorgabe veraltet (`ocs_post` existiert bereits seit Phase 8, das `message:`-Kind ist TOOL-16 in Phase 11 laut 09-RESEARCH.md T13). Dies wird hier nicht als Lücke gewertet, wie explizit angewiesen.

### Human Verification Required

Keine. Die Phase hat kein eigenes Frontend (ROADMAP: "UI hint: nein"), und alle fünf Erfolgskriterien wurden entweder durch Unit-Tests mit positiven Behauptungen an der gebauten Anfrage oder durch selbst ausgeführte Live-Läufe gegen laufende Docker-Topologien nachgewiesen. Keine PLAN-Datei enthält `<verify><human-check>`-Blöcke.

### Gaps Summary

Keine Lücken gefunden. Alle fünf Erfolgskriterien der Phase sind sowohl auf Unit- als auch auf Live-Integrationsebene nachgewiesen, der Code-Review-Fix-Pass ist im geprüften Commit enthalten, und alle Gates (`pytest`, `ruff`, `pyright`, `vulture`, `check_tool_budget`) sind grün gegen den aktuellen HEAD.

---

_Verifiziert: 2026-08-21T13:47:50Z_
_Verifier: Claude (gsd-verifier)_
