---
phase: 04-per-user-verwaltung-und-prepare-context
plan: 01
subsystem: auth
tags: [exapp-02, per-user, switch, middleware, store, r1, fail-closed]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "03-02: der Store mit Schema, WAL und der Regel eine Verbindung je Thread"
  - phase: 03-oauth-2-1
    provides: "03-06: die Transportgrenze RequireAppApi mit ihren zwei Identitätszweigen und der abgelegten OAuth-Identität"
  - phase: 02-exapp
    provides: "AUTH-01: die Identität aus AUTHORIZATION-APP-API"
provides:
  - "oauth/store.py: user_access-Tabelle plus set_access, access_disabled, authorizations_of_user (der Kontrakt, gegen den Plan 04-03 baut)"
  - "exapp/middleware.py: das Schalter-Gate R1 an der einen Transportgrenze, für beide Anschlussarten"
  - "exapp/ui/strings.py: SETTINGS_PLACE und ACCESS_DISABLED_DESCRIPTION als je eine Konstante"
  - "entry_exapp.py: der Schalter kommt aus demselben Store wie die Tokens"
  - "Index authorizations(nc_user) für die Kontoliste der Connections-Seite"
affects: [04-03 connections page, 04-04 live proof, 05 store submission]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die Reihenfolge der Prüfungen ist das Sicherheitsmerkmal: Handshake, Credential, dann Schalter"
    - "Freigeben löscht die Zeile, statt sie auf null zu setzen: Default-Zustand und Freigabe-Zustand sind dieselbe Wahrheit"
    - "Ein Wächter-Test legt den Schalter hinter der laufenden Anwendung um und verlangt die Ablehnung beim nächsten Aufruf"

key-files:
  created: []
  modified:
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/exapp/middleware.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/entry_exapp.py
    - tests/unit/test_oauth_store.py
    - tests/unit/test_exapp_entry.py
    - vulture_whitelist.py

key-decisions:
  - "Der Schalter-Read läuft je Request gegen die eigene SQLite-Datei, ohne Prozess-Cache: nur so wirkt das Umlegen beim nächsten Aufruf (D-48), und es kostet keinen zweiten Nextcloud-Roundtrip (D-47)"
  - "Freigeben ist ein DELETE der Zeile, kein Update auf null: 'nie pausiert' und 'wieder freigegeben' sind damit ununterscheidbar dieselbe Wahrheit, und 'an' kostet keine Zeile (D-50)"
  - "Ein Store-Ausfall am Gate ist 503 ohne Detail, nie ein Durchlass und nie ein behauptetes access_disabled (fail closed, D-37-Analogie)"
  - "Eine leere Konto-Id wird nie gegen den Schalter geprüft, und set_access weist sie als ValueError ab, bevor die Datei geöffnet wird"
  - "_authorization_row als eine Zeilenform für die nun drei Leser einer Verbindung, nach dem Vorbild von _auth_code_row"
  - "Der AUTH-01-Zweig braucht ab jetzt den Store; die Live-Messung von SC 5 geht an Plan 04-04, weil der laufende Container das Image von vor dieser Änderung trägt"

patterns-established:
  - "Ein neuer Schutzmechanismus wird erst als roter Test eingecheckt und dann implementiert (zwei Commits je Task)"
  - "Ein Wächter wird gegengeprüft, indem die Verdrahtung testweise entfernt wird: bleibt der Test grün, ist er keiner"

requirements-completed: []

# Metrics
duration: rund eine Stunde
completed: 2026-08-17
---

# Phase 4 Plan 01: Der Schalter wirkt Summary

**Wer sein Nextcloud-Konto pausiert, wird beim nächsten MCP-Aufruf abgewiesen, auf beiden Anschlussarten, mit einem 403 `access_disabled` ohne Challenge, und die Sperre kostet keinen einzigen zusätzlichen Nextcloud-Roundtrip, weil sie ein lokaler SQLite-Read an genau einer Transportgrenze ist.**

## Performance

- **Completed:** 2026-08-17
- **Tasks:** 2 von 2
- **Tests:** 1400 vor dem Plan, 1423 danach (23 neue), 82 deselektiert wie vorher
- **Gates:** ruff check, ruff format --check, pyright, vulture, pytest, check_tool_budget: alle sauber
- **Tool-Budget:** unverändert 10642 von 12500 Bytes (dieser Plan registriert kein Tool)
- **uv.lock:** unverändert, keine neue Dependency (T-04-SC)

## Accomplishments

- **Der Schalter ist eine Store-Wahrheit, nicht ein Nextcloud-Wert.** `user_access (nc_user TEXT PRIMARY KEY, disabled_at INTEGER NOT NULL)` steht im `SCHEMA`-Literal, also ist `CREATE TABLE IF NOT EXISTS` die ganze Migration: `_connect` führt das Skript bei jedem Open aus, eine Store-Datei aus einem älteren Build bekommt die Tabelle beim nächsten Gebrauch. `_add_missing_columns` blieb unberührt, weil keine bestehende Tabelle eine neue Spalte bekam.
- **Drei Methoden, die Plan 04-03 unverändert konsumieren kann.** `set_access(nc_user, disabled=...)` ist in beide Richtungen idempotent und dabei bewusst asymmetrisch: Sperren schreibt höchstens eine Zeile und behält den ersten `disabled_at` (`ON CONFLICT DO NOTHING`), Freigeben löscht die Zeile. `access_disabled(nc_user)` ist ein `SELECT 1` auf den Primärschlüssel. `authorizations_of_user(nc_user)` liefert `revoked_at IS NULL ORDER BY created_at DESC`, dazu kam ein Index auf `authorizations(nc_user)`.
- **Das Gate sitzt an dritter Stelle, und das ist der Sicherheitsgewinn.** Erst Handshake (R3), dann Credential (R2), dann Schalter (R1). Ein ungültiger Bearer eines pausierten Kontos bekommt weiterhin 401, und der Schalter wird dabei nie gefragt: der Test assertiert `switch.asked == []`, damit kein Aufrufer ohne Identität erfährt, ob ein Konto existiert oder pausiert hat (Pitfall 2, T-04-01).
- **Eine Entscheidung für beide Anschlussarten.** Die Identität ist `user` aus dem HaRP-Header oder `identity.nc_user` aus `request.state`, das `_deposit` gerade abgelegt hat. Beide Zweige münden in denselben Aufruf; kein Tool trägt eine zweite Kopie der Entscheidung (`grep -c access_disabled` über `src/mcp_connector/tools/*.py` ist 0, und ein Test hält das fest).
- **R1 ist wortgleich der UI-SPEC-Vertrag.** 403, `media_type="application/json"`, Body ein auf Modulebene aus zwei Konstanten gebauter JSON-String, `Cache-Control: no-store`, kein `WWW-Authenticate`. Der Satz nennt Regel und Ort und trägt keinen Wert aus der Anfrage: der Test assertiert zusätzlich, dass weder der Kontoname noch das App-Secret im Body stehen (T-03-66, T-04-05).
- **Fail closed am Gate.** Wirft der Schalter-Read, antwortet die Grenze 503 mit `no-store`, ohne Body und mit einer Logzeile, die keinen Kontonamen nennt. Weder Durchlass noch gelogenes `access_disabled`: ein Store-Ausfall ist keine Nutzerentscheidung (T-04-06).
- **Der Wächter ist nachweislich einer.** Zur Gegenprobe wurde die Verdrahtung testweise auf `access_check=None` gesetzt: `test_a_paused_account_is_refused_by_the_wired_application`, `test_the_switch_costs_no_nextcloud_round_trip_per_request` und `test_the_mcp_route_is_guarded_with_the_switch_of_this_deployment` fielen sofort um (403 wurde 200). Danach wurde die Verdrahtung zurückgesetzt und die Suite war wieder grün.
- **Zwei End-to-End-Wächter statt eines Store-Roundtrips.** Einer legt den Schalter mit dem echten `OAuthStore` hinter der laufenden `TestClient`-Anwendung um und verlangt beim nächsten Request 403 und beim dritten wieder 200 (D-48, D-46). Der andere führt dasselbe durch die vollständig verdrahtete `build_exapp_app` und prüft dabei zusätzlich, dass das Konto eines anderen Nutzers unberührt bleibt.
- **SC 5 in-Prozess belegt.** `test_the_switch_costs_no_nextcloud_round_trip_per_request` fährt drei bediente MCP-Requests und assertiert, dass der Datenschlüssel genau einmal geholt wurde: der Store-Opener zahlt einmal je Prozess, der Schalter-Read selbst verlässt den Container nie.

## Task Commits

1. **Task 1: der Schalter-Zustand und die Nutzer-Query im Store** - `f0489f2` (rote Tests), `e5de2b5` (Implementierung)
2. **Task 2: das Schalter-Gate R1 an der Transportgrenze, beide Zweige** - `2430c53` (rote Tests), `c3baa5d` (Gate, Konstanten, Verdrahtung)

## Files Created/Modified

- `src/mcp_connector/oauth/store.py` - `user_access` im SCHEMA, Index `authorizations_nc_user`, die drei neuen Methoden, `_authorization_row` als eine Zeilenform für die nun drei Leser einer Verbindung.
- `src/mcp_connector/exapp/middleware.py` - `access_check` als Konstruktorargument (Default `None` = Verhalten von Phase 3), `_switch_refusal` als dritte Prüfung, `_ACCESS_DISABLED_BODY` einmal auf Modulebene, ein Logger für den 503-Fall.
- `src/mcp_connector/exapp/ui/strings.py` - `SETTINGS_PLACE` und `ACCESS_DISABLED_DESCRIPTION`, beide in `__all__`, der Ort genau einmal genannt.
- `src/mcp_connector/entry_exapp.py` - ein kleiner async Wrapper über denselben Store-Opener, den der Verifier benutzt, als `access_check` an die eine Wrap-Stelle.
- `tests/unit/test_oauth_store.py` - zehn Tests: alle sieben Verhaltenspunkte des Plans, dazu "Pausieren trennt nichts" (D-46) und `user_access` im Schema-Test.
- `tests/unit/test_exapp_entry.py` - dreizehn neue Tests plus `StubSwitch` und der Store-Helfer `with_a_local_store`; ein bestehender Test wurde angepasst (siehe Abweichungen).
- `vulture_whitelist.py` - `set_access` und `authorizations_of_user` mit Begründung eingetragen (die Aufrufer kommen in Plan 04-03); `access_disabled` wurde in Task 2 wieder entfernt, weil es einen Produktions-Aufrufer bekam. Genau die Regel, die die Datei selbst aufstellt.

## Deviations From Plan

- **[Rule 3 - Blockierend] `test_initialize_with_a_valid_handshake_is_served` musste einen Store bekommen.** Der AUTH-01-Zweig erreichte den Store bisher nie; mit dem Gate braucht jeder bediente Request ihn. In der Unit-Umgebung gibt es kein erreichbares Nextcloud, also lief der Test in die fail-closed-503. Der Test bekommt jetzt über den neuen Helfer `with_a_local_store` eine Store-Datei in `tmp_path` und einen Datenschlüssel ohne Netz (`monkeypatch` auf `store.crypto.data_key`, Muster aus `tests/unit/test_oauth_connect.py:678`). Er beweist damit mehr als vorher: der AUTH-01-Pfad passiert das Gate eines nicht pausierten Kontos. Commit `c3baa5d`.
- **[Rule 2 - Fehlende kritische Absicherung] Zwei Tests mehr als der Plan verlangt.** `test_the_switch_costs_no_nextcloud_round_trip_per_request` (SC 5 in-Prozess, weil die Live-Messung übergeben wird) und `test_the_switch_is_decided_at_the_boundary_and_nowhere_else` (das Akzeptanzkriterium mit dem `grep` über `tools/*.py` als Test, damit es auch in einem Jahr noch geprüft wird).
- **Kleiner Aufräumschritt im Store.** `load_authorization` und `authorizations_of_client` schrieben die achtfeldige `AuthorizationRow` je selbst zusammen; mit `authorizations_of_user` wäre es die dritte Kopie geworden. Stattdessen `_authorization_row`, genau nach dem Vorbild des vorhandenen `_auth_code_row` ("one shape for the two places that read a code"). Verhalten unverändert, die bestehenden Tests beider Leser bleiben grün.
- **Commit-Sprache.** Die vier Commits dieses Plans sind englisch formuliert, wie die gesamte Historie des Repos (in den letzten 60 Commits kein einziger deutscher Betreff). Die erste Fassung war deutsch und wurde vor dem Push auf die Repo-Konvention gebracht; die Inhalte der vier Commits sind unverändert.
- **Offen an Plan 04-04: die Live-Messung von SC 5.** Die exapp-Topologie läuft (Port 8081, `nc_app_mcp_connector` healthy), aber der ExApp-Container wurde am 2026-08-16T08:56Z aus dem Image von vor dieser Änderung erzeugt. Ein `--measure`-Lauf hätte also den Stand von Phase 3 gemessen und nichts über diesen Plan gesagt; ein Neubau mit Neuregistrierung würde genau den Container ersetzen, den Plan 04-04 ohnehin neu baut und live messt. Das Kommando für dort, unverändert aus dem Plan: `uv run --no-sync python scripts/oauth_flow_check.py http://127.0.0.1:8081/exapps/mcp_connector --measure`; die Zahl je MCP-Aufruf muss exakt bei eins bleiben. In-Prozess ist die Eigenschaft belegt (ein Datenschlüssel-Fetch für drei Aufrufe, der Schalter-Read verlässt den Container nie).

## Threat Flags

| Threat ID | Ist-Zustand | Belegt durch |
|-----------|-------------|--------------|
| T-04-01 (Information Disclosure, Prüf-Reihenfolge) | Geschlossen. R1 sitzt hinter Handshake und Credential; ein ungültiger oder fehlender Bearer bekommt R2/R3, und der Schalter wird nicht einmal gefragt. | `test_an_invalid_bearer_of_a_paused_account_is_still_the_discovery_401` (inklusive `switch.asked == []`), `test_a_broken_handshake_of_a_paused_account_is_still_the_bare_401` |
| T-04-02 (Denial of Service, Antwortform) | Geschlossen. 403 ohne `WWW-Authenticate`; kein OAuth-Client wird in die Rediscovery-Schleife geschickt. Die bewusste RFC-6750-Abweichung steht im Docstring von `_switch_refusal` und im Test-Docstring. | `test_the_refusal_of_a_paused_account_is_the_wire_contract_of_the_ui_spec` |
| T-04-03 (Elevation of Privilege, Durchsetzung) | Geschlossen. Read je Request direkt aus SQLite, kein Prozess-Cache; das Umlegen zwischen zwei Aufrufen wirkt beim zweiten. | `test_flipping_the_switch_takes_effect_on_the_very_next_request`, `test_the_switch_of_the_real_store_reaches_the_boundary`, `test_a_paused_account_is_refused_by_the_wired_application` |
| T-04-04 (Elevation of Privilege, App-Kontext) | Geschlossen. Nur eine nicht-leere aufgelöste Identität wird geprüft; `access_disabled("")` ist False ohne Dateizugriff, `set_access("")` ist ein ValueError vor jedem Schreiben. | `test_the_app_context_is_never_asked_for_a_switch`, `test_an_empty_account_id_is_never_a_switch` |
| T-04-05 (Information Disclosure, R1-Body) | Geschlossen. Konstanter String ohne Platzhalter, einmal auf Modulebene gebaut; nennt Regel und Ort, nie einen Wert aus der Anfrage. `no-store` gegen den PHP-Proxy-Cache. | `test_the_refusal_of_a_paused_account_is_the_wire_contract_of_the_ui_spec` (assertiert zusätzlich, dass Kontoname und App-Secret nicht im Body stehen) |
| T-04-06 (Denial of Service, Store-Ausfall) | Geschlossen. 503 mit `no-store`, ohne Body, mit einer Logzeile ohne Kontonamen; kein Durchlass und kein behauptetes `access_disabled`. | `test_a_store_that_cannot_answer_the_switch_refuses_instead_of_letting_through` |
| T-04-SC (Tampering, Paket-Installationen) | Nicht eingetreten. Dieser Plan installiert kein Paket, `git diff --stat uv.lock` ist leer. | Gate-Lauf am Planende |

Zwei neue Beobachtungen über das Register hinaus, beide bewusst so:

- **Neue Abhängigkeit des AUTH-01-Zweigs vom Store.** Ein per App-Passwort authentifizierter Tool-Aufruf öffnet ab jetzt den Store, also beim ersten Request eines Prozesses auch den OCS-Abruf des Datenschlüssels. Ist der nicht lesbar (App nicht registriert, Nextcloud nicht erreichbar), antwortet die Grenze 503 statt zu bedienen. Das ist die gewollte fail-closed-Richtung: ohne Store kann niemand wissen, ob das Konto pausiert hat. Betriebsfolge: eine ExApp ohne lesbaren Datenschlüssel bedient jetzt auch AUTH-01 nicht mehr, während sie den OAuth-Teil schon vorher nicht bedienen konnte. Kein Requirement berührt, aber ein Satz für `docs/exapp-install.md` in einem späteren Plan.
- **Kein Throttle am Gate, und das bleibt so.** R1 ist billig (ein lokaler Read), und die MCP-Route trägt bewusst keinen Zähler (Kommentar in `entry_exapp.py`). Ein pausierter Client, der weiter pollt, kostet uns SQLite-Reads und Nextcloud nichts.

## What the next plans inherit

- **Plan 04-03 (Connections-Seite):** der Store-Kontrakt steht und ist getestet: `set_access`, `access_disabled`, `authorizations_of_user`. `SETTINGS_PLACE` und `ACCESS_DISABLED_DESCRIPTION` existieren; die vier `SWITCH_*`-Konstanten sowie `CONNECTIONS_*` und `DISCONNECT_*` gehören dorthin. `set_access` erwartet eine nicht-leere Konto-Id, die Seite muss also ihre E8-Prüfung vor den Schreibpfad setzen. Die Whitelist-Einträge `_.set_access` und `_.authorizations_of_user` sind mit dem Plan wieder zu entfernen, der sie aufruft.
- **Plan 04-04 (Live-Beweis):** die SC-5-Messung ist offen übergeben, mit Kommando und Sollwert oben. Beim Neubau der Topologie fällt der Beweis für den Schalter mit ab: pausieren, ein `tools/call`, R1 im Log.
- **EXAPP-02 bleibt offen.** Dieser Plan liefert Zustand und Durchsetzung, die Hand ans Steuer kommt in 04-03, der Settings-Wegweiser und die Live-Abnahme in 04-04. `REQUIREMENTS.md` wurde deshalb nicht abgehakt.

## Self-Check: PASSED

- `src/mcp_connector/oauth/store.py`, `src/mcp_connector/exapp/middleware.py`, `src/mcp_connector/exapp/ui/strings.py`, `src/mcp_connector/entry_exapp.py`, `tests/unit/test_oauth_store.py`, `tests/unit/test_exapp_entry.py`, `vulture_whitelist.py`: alle vorhanden und geändert.
- Commits `f0489f2`, `e5de2b5`, `2430c53`, `c3baa5d`: alle in `git log` vorhanden.
- Keine Stubs, keine Platzhalter, keine TODO-Marker in den geänderten Dateien.
