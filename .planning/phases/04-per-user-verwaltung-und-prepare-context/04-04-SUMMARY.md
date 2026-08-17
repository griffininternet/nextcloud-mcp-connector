---
phase: 04-per-user-verwaltung-und-prepare-context
plan: 04
subsystem: exapp-settings
tags: [exapp-02, declarative-settings, signpost, live-proof, sc-5, prepare-context]

# Dependency graph
requires:
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "04-01: das Schalter-Gate R1 an der Transportgrenze und der user_access-Zustand"
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "04-02: prepare_context als 16. Tool"
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "04-03: die Connections-Seite mit dem Schalter, CONNECTIONS_PATH, SETTINGS_TITLE und SETTINGS_DESCRIPTION"
  - phase: 02-exapp
    provides: "EXAPP-01: der /enabled-Handler und das Fehlermodell des Init-Progress-Push"
provides:
  - "exapp/settings_form.py: form_scheme und register_settings_form, die gemessene Link-only-Registrierung"
  - "exapp/lifecycle.py: die Registrierung als Fire-and-forget bei enabled=1"
  - "04-04-MEASUREMENTS.md: die fünf Live-Beweise mit Kommando, Antwort und Datum"
  - "die EXAPP-02-Wortlaut-Notiz für 04-VERIFICATION"
affects: [04-VERIFICATION, 05 store submission, docs/client-setup.md, docs/oauth-setup.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein ausgehender OCS-Call im Lifecycle-Handler, dessen Scheitern nur eine Logzeile kostet"
    - "Beide URLs eines Wegweisers entstehen aus der öffentlichen URL, nie aus dem internen Hostnamen"
    - "Eine Live-Abnahme fängt mit dem Neubau des Images an, sonst misst sie die vorige Phase"

key-files:
  created:
    - src/mcp_connector/exapp/settings_form.py
    - .planning/phases/04-per-user-verwaltung-und-prepare-context/04-04-MEASUREMENTS.md
  modified:
    - src/mcp_connector/exapp/lifecycle.py
    - src/mcp_connector/tools/context.py
    - tests/unit/test_exapp_lifecycle.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "fields bleibt leer, und das ist kein Verzicht, sondern der gemessene Kontrakt: eine Checkbox, deren Änderung die ExApp nie erfährt, wäre ein Schalter, den die Grenze nicht durchsetzt"
  - "Die Registrierung läuft nur bei enabled=1 und entregistriert bei enabled=0 nichts: AppAPI liefert nur die Formulare aktivierter Apps aus und räumt bei der Deinstallation selbst auf"
  - "form_scheme ist eine Funktion und keine importzeitige Konstante, weil beide URLs aus der öffentlichen URL des Deployments kommen"
  - "Die Live-Abnahme trennt zwei Sonden gegen /mcp: die SDK-Sitzung beweist das Durchkommen, der rohe POST zeigt die Ablehnung auf dem Draht"

patterns-established:
  - "Wächter-Gegenprobe: die Verdrahtung testweise entfernen, der Test muss umfallen"
  - "Jede Zahl im SUMMARY nennt ihren Befehl und ihr Datum, die Rohfassung liegt in einer MEASUREMENTS-Datei daneben"

requirements-completed: [EXAPP-02]

# Metrics
duration: rund 90 Minuten
completed: 2026-08-17
---

# Phase 4 Plan 04: Der Settings-Wegweiser und die Live-Abnahme Summary

**Der Nutzer findet den MCP Connector jetzt dort, wo Nextcloud seine eigenen Schalter zeigt: ein Link-only-Eintrag unter Einstellungen, Sicherheit, der auf die Connections-Seite führt, registriert bei jedem Aktivieren und unfähig, die Installation zu brechen. Auf der echten Topologie ist die ganze Kette nachgemessen: Wegweiser sichtbar ausgeliefert, Schalter umgelegt und der nächste Tool-Aufruf 403 `access_disabled`, SC 5 unverändert bei einem Nextcloud-Roundtrip je MCP-Aufruf, und `prepare_context` antwortet in 0,84 s kurz und 0,99 s voll.**

## Performance

- **Completed:** 2026-08-17
- **Tasks:** 2 von 2
- **Tests:** 1507 vor dem Plan, 1521 danach (14 neue), 82 deselektiert wie vorher
- **Gates:** ruff check, ruff format --check, pyright (0 errors), vulture, pytest, check_tool_budget: alle sauber
- **Tool-Budget:** unverändert 11268 von 12500 Bytes bei 16 Tools (dieser Plan registriert kein Tool)
- **uv.lock:** unverändert, keine neue Dependency (T-04-SC)

## Accomplishments

- **Der Wegweiser ist ein ausgehender Call und keine neue Route.** `register_settings_form` postet das `formScheme` auf `/ocs/v2.php/apps/app_api/api/v1/ui/settings`, im App-Kontext (leerer Nutzer im `AUTHORIZATION-APP-API`-Token), mit `OCS_HEADERS` und der Header-Bauweise von `exapp/status.py`. Es gibt keine vierzehnte Route: wenn ein Nutzer in Nextclouds Settings etwas ändert, erreicht die ExApp nichts, und genau deshalb ist der Schalter dort auch nicht.
- **`fields` ist leer, und der Test hält das fest.** Das Schema folgt der Tabelle des UI-SPEC Zeile für Zeile: `id` `mcp_connector_settings`, `priority` 10, `section_type` `personal`, `section_id` `security`, Titel und Beschreibung aus den Konstanten von 04-03, `doc_url` die absolute öffentliche `/connections`-Adresse. Ein eigener Test verlangt `fields == []` und zusätzlich, dass das Wort `checkbox` im gesendeten Body nicht vorkommt (Pitfall 1 nennt genau das als Warnsignal).
- **Die Registrierung kann die Installation nicht brechen.** Sie hängt im `/enabled`-Handler in demselben try/except wie der Init-Progress-Push, und der Handler antwortet auch dann `{"error": ""}` mit `no-store`, wenn der OCS-Call in einen Transportfehler läuft. Ein Test lässt die Registrierung werfen und verlangt genau diese Antwort (Pitfall 11, T-04-41).
- **`enabled=0` registriert nichts und entregistriert nichts.** AppAPIs `getRegisteredForms` liefert nur Formulare aktivierter Apps, eine deaktivierte App verschwindet also von selbst aus der Settings-Seite, und `unregisterExApp` räumt bei der Deinstallation auf. Beides ist gemessen (04-RESEARCH) und steht als Begründung im Code, nicht nur im Plan.
- **Beide URLs kommen aus `config.public_url`.** `form_scheme` ist deshalb eine Funktion und keine Modulkonstante. Ein Test assertiert, dass `doc_url` mit der öffentlichen URL beginnt, auf `/connections` endet und dass die interne Basis-URL weder im `doc_url` noch in der Beschreibung auftaucht (T-04-40).
- **Das App-Secret bleibt aus den Logs.** Drei Ausgänge (200, 500, Transportfehler) werden mit `caplog` auf DEBUG geprüft: weder das Secret noch sein base64-Token stehen in einer Logzeile. Die Fehlerzeilen nennen die URL und den Status, nie einen Wert aus dem Request (T-04-42).
- **Die Live-Abnahme fing mit dem Neubau an.** Der laufende Container trug das Image vom 2026-08-16T08:53Z, also den Stand vor 04-01. Erst `app:unregister`, `daemon:unregister`, dann `bash scripts/bootstrap_exapp.sh` mit `HP_SHARED_KEY` aus dem HaRP-Container: neues Image `sha256:de4b0865...`, registriert, deployt, aktiviert. Ohne diesen Schritt hätte der ganze Lauf Phase 3 gemessen.
- **Alle fünf Live-Beweise stehen** (Kommandos, Antworten und Datum in `04-04-MEASUREMENTS.md`, verdichtet unten in "Für 04-VERIFICATION").
- **EXAPP-02 ist abgehakt.** `REQUIREMENTS.md` trägt das Häkchen und die Traceability-Zeile steht auf Complete, mit der Wortlaut-Notiz unten als Beipackzettel.

## Task Commits

1. **Task 1: die Link-only-Form und ihr lifecycle-Haken** - `d34c9dd` (rote Tests), `20aa72e` (Implementierung)
2. **Task 2: Live-Abnahme und die Zahlen fürs VERIFICATION** - `850253f` (Messprotokoll plus der gemessene A2-Kommentar an der Budget-Konstante)

## Files Created/Modified

- `src/mcp_connector/exapp/settings_form.py` (neu) - `SETTINGS_PATH`, `FORM_ID`, `FORM_PRIORITY`, `SECTION_TYPE`, `SECTION_ID`, `form_scheme(env)` und `register_settings_form(*, env)`. Der Modul-Docstring trägt den gemessenen Kontrakt vom 2026-08-17 samt der Begründung, warum `fields` leer bleibt.
- `src/mcp_connector/exapp/lifecycle.py` - der `enabled`-Handler ruft die Registrierung bei `"1"` im init-Fehlermodell; ein Kommentar nennt den Grund, warum `"0"` nichts tut. Kein neuer Parameter an `lifecycle_routes`.
- `src/mcp_connector/tools/context.py` - die gemessenen Antwortzeiten (0,84 s kurz, 0,99 s voll, `degraded` leer) als Kommentar an `CALENDAR_BUDGET`, mit dem Verweis auf die MEASUREMENTS-Datei. Keine Verhaltens- und keine Wertänderung.
- `tests/unit/test_exapp_lifecycle.py` - vierzehn neue Tests: die `registrations`-Fixture, drei Tests am `/enabled`-Verhalten, sechs respx-Tests am Payload und an den Headern, ein Log-Test je Fehlerausgang und drei parametrisierte Secret-Tests. Die vorhandenen `/enabled`-Tests bekamen die Fixture, damit kein Test mehr ins Netz greift.
- `.planning/phases/.../04-04-MEASUREMENTS.md` (neu) - die Rohfassung der Live-Abnahme nach dem Muster von `03-09-MEASUREMENTS.md`.
- `.planning/REQUIREMENTS.md` - EXAPP-02 abgehakt, Traceability-Zeile auf Complete.

## Für 04-VERIFICATION

### Die EXAPP-02-Wortlaut-Notiz (Open Question 2 aus 04-RESEARCH), wörtlich

> EXAPP-02 sagt: "Nutzer kann **in den Nextcloud-Settings** den MCP-Zugriff
> aktivieren/deaktivieren, verbundene Clients einsehen und Tokens widerrufen". Der gemessene
> AppAPI-Kontrakt (04-RESEARCH, Frage 1, Quellcode von app_api v34.0.3 und Nextcloud
> stable34) macht die wörtliche Lesart unmöglich, ohne D-47 oder D-48 zu brechen: AppAPI
> speichert den Wert einer Declarative-Settings-Checkbox selbst in `preferences_ex` und
> benachrichtigt die ExApp **nicht**. Die ExApp könnte den Wert nur per OCS-Roundtrip je
> Request lesen (verletzt D-47: kein zweiter Nextcloud-Roundtrip) oder pollen (verletzt
> D-48: wirkt nicht beim nächsten Aufruf). Ein Schalter, den die Grenze nicht durchsetzt,
> wäre schlimmer als keiner.
>
> Deshalb liegt der Schalter **einen Klick hinter** dem Settings-Eintrag: Nextcloud,
> Einstellungen, Sicherheit, "MCP Connector" nennt die Adresse im Text und verlinkt sie als
> `doc_url`; auf `/connections` liegen der Schalter, die Liste der verbundenen Apps und der
> Widerruf. `CONTEXT.md` (D-47, D-48) und `04-UI-SPEC.md` ("The Nextcloud Settings Entry")
> autorisieren diesen Weg ausdrücklich und schlagen die Präferenz D-44. Alle drei Teile des
> Requirements sind erfüllt, der Einstieg ist in den Nextcloud-Settings, und die Prüfung
> sollte nicht über den Wortlaut "in den Settings aktivieren" stolpern.

### Die Messzahlen (2026-08-17, Topologie compose.exapp.yml, Port 8081)

| Beweis | Kommando | Ergebnis |
|--------|----------|----------|
| 1a Wegweiser registriert | `curl -s -u admin:… -H "OCS-APIRequest: true" http://127.0.0.1:8081/ocs/v2.php/settings/api/declarative/forms` | `mcp_connector_settings`, `section_id: security`, `fields: []`, `storage_type: external`, `app: mcp_connector`, beide URLs öffentlich |
| 1b Seite liefert die Form | `curl -s -u admin:… http://127.0.0.1:8081/settings/user/security` | 200, ein Treffer `mcp_connector_settings`, Mount-Punkt `<div id="mcp_connector_mcp_connector_settings">`, Initial-State mit `fields:[]` |
| 2 Schalter-Kette | Live-Skript über `scripts/oauth_flow_check.py` (`connect`, `tool_call`) plus Nextcloud-Sitzung auf `/connections` | vorher `tools/call prepare_context` 200 in 0,83 s; nach `action=pause` **403 `access_disabled`, ohne `WWW-Authenticate`, `no-store`**; nach `action=resume` **200 mit demselben Token** in 0,82 s |
| 3 SC 5 | `uv run --no-sync python scripts/oauth_flow_check.py http://127.0.0.1:8081/exapps/mcp_connector --measure` | Exit 0; `5 accepted MCP calls -> 6 Nextcloud requests (1.2 per call)`, `5 refused -> 5 (1.0 per call)`, der eine Pfad ist HaRPs `GET /index.php/apps/app_api/harp/user-info`. **Zeichengleich mit dem Phase-3-Ergebnis in `03-VERIFICATION.md`** |
| 4 Seite von außen | `GET /connections` mit und ohne Nextcloud-Sitzung | mit Sitzung 200 mit `no-store`; ohne Sitzung **403 E8 "Sign in to see your connections"**, `no-store` |
| 5 prepare_context | `tools/call prepare_context {"query":"budget"}` in `detail=short` und `detail=full` über die volle Kette | **0,84 s kurz, 0,99 s voll**; Treffer aus drei Quellen (`files`, `notes`, plus `events` aus dem Kalender), Herkunft als Struktur (`provider`, `kind`, benannte Buckets, `window`), `degraded` leer und deshalb laut Kontrakt nicht im Objekt; nur die Voll-Form trägt `excerpt` |

Zur SC-5-Zahl: "1.2 je Aufruf" ist dieselbe Zahl wie in Phase 3 und keine Verschlechterung.
Fünf Tool-Aufrufe einer Sitzung kosten sechs Nextcloud-Anfragen, weil der Sitzungsaufbau die
sechste ist; je Request mit `Authorization`-Header ist es genau einer, und der gehört HaRP.
Das Schalter-Gate aus 04-01 kostet null, weil es ein lokaler SQLite-Read ist.

## Deviations From Plan

- **[Rule 2 - Fehlende kritische Absicherung] Vier Tests mehr als der Plan verlangt.** Zusätzlich zu den sieben Verhaltenspunkten: die Header-Prüfung des App-Kontexts (leerer Nutzer im Token, die vier AppAPI-Header plus `OCS-APIRequest`), der Log-Nachweis für den 400/401/500-Ausgang, und zwei Tests, die belegen, dass ein abgelehntes oder unbrauchbares `/enabled` überhaupt nichts registriert. Commit `d34c9dd`.
- **[Rule 3 - Blockierend] Die bestehenden `/enabled`-Tests brauchten die neue Fixture.** Mit der Verdrahtung würde `test_enabled_answers_with_an_empty_error_field` bei `enabled=1` einen echten OCS-Call gegen `http://nc.test` versuchen. Sie bekommen jetzt dieselbe `registrations`-Fixture wie die neuen Tests; kein Test dieses Moduls öffnet ein Socket. Commit `d34c9dd`.
- **`config.ENV_PUBLIC_URL` kam ins Test-`ENV`.** Ohne den Wert fiele `public_url` auf `http://127.0.0.1:8765` zurück, und die Assertion "die öffentliche URL steht im `doc_url`" hätte gegen den Default geprüft statt gegen eine gesetzte Konfiguration.
- **Die Live-Sonde gegen `/mcp` ist zweigeteilt.** Der Plan schreibt "tools/call gegen /mcp geht durch" und danach "der nächste tools/call MUSS 403 sein". Ein roher JSON-RPC-POST ohne MCP-Sitzung bekommt vom Transport 400 (keine Sitzung), egal ob der Schalter an ist; eine SDK-Sitzung wiederum verpackt die 403 in eine `ExceptionGroup` und zeigt die Header nicht. Deshalb laufen beide Sonden: die SDK-Sitzung beweist 200 vor und nach dem Pausieren, der rohe POST zeigt die 403 mit Body und Headern auf dem Draht. Beide Zeilen stehen im Messprotokoll.
- **Der A2-Kommentar wurde an `CALENDAR_BUDGET` gehängt.** Der Plan sagt "an die Budget-Konstante in tools/context.py"; ein globales Gesamtbudget gibt es dort bewusst nicht (04-02, Pitfall 4), sondern drei Teil-Budgets. `CALENDAR_BUDGET` ist das engste eigene und damit der Ort, an dem die Zahl gelesen wird. Commit `850253f`.
- **Der erste Live-Lauf brach ab, der zweite lief vollständig.** Der erste Anlauf lief in die Drossel des `--measure`-Laufs (`POST /token -> 429, retry in 124 seconds`), der zweite in einen abgeschnittenen Ausgabepuffer. Der dritte Lauf ist der protokollierte; die Objekte des abgebrochenen Laufs (eine Notiz, eine Datei, ein Termin) wurden hinterher einzeln entfernt und nachgeprüft.
- **Die Alt-Verbindungen von alice wurden mit aufgeräumt.** Der Lauf trennte am Ende alle 42 Zeilen der Connections-Seite, also auch die Verbindungen früherer Testläufe aus Phase 3 und 4. Das ist eine Wegwerf-Instanz mit zwei Wegwerf-Konten; die Owner-Instanzen `nc-mcp-test` und `findling-nextcloud` wurden nicht angefasst.
- **Die Topologie ist wieder heruntergefahren**, mit erhaltenen Volumes, `nc_app_mcp_connector` gestoppt und entfernt, `nc-mcp-exapp-net` entfernt: der Zustand, den STATE.md beschreibt. Der Wiederanfahr-Weg steht dort und in `04-04-MEASUREMENTS.md`, Schritt 0.

## Known Stubs

Keine. Kein Platzhalter, kein TODO, kein hartkodierter Leerwert in den geänderten Dateien.

## Threat Flags

| Threat ID | Ist-Zustand | Belegt durch |
|-----------|-------------|--------------|
| T-04-40 (Spoofing, `doc_url` und Beschreibung) | Geschlossen. Beide Werte entstehen ausschließlich aus `config.public_url`; die interne Basis-URL taucht in keinem der beiden auf. Live gegengeprüft: die registrierte Form trägt `http://127.0.0.1:8081/exapps/mcp_connector/connections` und nicht `http://caddy`. | `test_the_form_never_carries_an_internal_host_name`, `test_the_registered_form_is_the_scheme_of_the_ui_spec`, Beweis 1a |
| T-04-41 (Denial of Service, `/enabled`) | Geschlossen. Ein Versuch, kein Retry, jeder Fehler wird zu einer Logzeile; `/enabled` antwortet `{"error": ""}` mit `no-store`, auch wenn die Registrierung wirft. | `test_enabled_answers_200_when_the_registration_fails`, `test_a_registration_that_cannot_be_delivered_is_one_log_line`, `test_a_refused_registration_is_one_log_line` |
| T-04-42 (Information Disclosure, App-Secret) | Geschlossen. Header-Bauweise wörtlich aus `status.py`/`credentials.py`, kein Wert aus dem Request in einer Logzeile; auf DEBUG geprüft für alle drei Ausgänge. | `test_the_app_secret_never_reaches_a_log_record` (dreifach parametrisiert), `test_the_registration_runs_in_the_app_context` |
| T-04-43 (Tampering, Checkbox ohne Wirkung) | Geschlossen. `fields` ist eine leere Liste, im Payload-Test und live in der `forms`-Antwort der laufenden Nextcloud; das Wort `checkbox` kommt im gesendeten Body nicht vor. | `test_the_registered_form_carries_no_field_at_all`, Beweis 1a und 1b |
| T-04-SC (Tampering, Paket-Installationen) | Nicht eingetreten. Kein Paket installiert, `git diff --stat uv.lock` ist leer. | Gate-Lauf am Planende |

Zwei Beobachtungen über das Register hinaus, beide bewusst so:

- **Neue ausgehende Verbindung im Lifecycle.** `/enabled` spricht ab jetzt mit Nextcloud, was es vorher nicht tat. Der Aufruf ist synchron im Handler (ein Request, Timeouts aus `shared_client`: 10 s gesamt, 5 s Connect); ein hängendes Nextcloud verzögert damit das Aktivieren, kann es aber nicht scheitern lassen. Ein `asyncio.create_task` wäre schneller und würde den Fehler in einen unbeobachteten Task schieben, also genau die Logzeile verlieren, die das einzige Signal ist.
- **Der Wegweiser ist sichtbar für jeden Nutzer der Instanz**, auch für einen, der nie eine Verbindung hatte. Das ist gewollt: der Eintrag ist ein Link und eine Beschreibung, er nennt keinen Kontostand und keine Verbindung, und wer der Adresse folgt, sieht die leere Liste seines eigenen Kontos.

## Restunsicherheit, ehrlich benannt

**Assumption A1 (der gerenderte Pixel) ist nicht vollständig geschlossen.** Gemessen ist, dass Nextcloud die Form ausliefert (`/ocs/v2.php/settings/api/declarative/forms`), dass sie im Initial-State der persönlichen Security-Seite steht und dass die Seite den Mount-Punkt `<div id="mcp_connector_mcp_connector_settings">` trägt, an den der Vue-Renderer zeichnet. Nicht gemessen ist der Pixel selbst: im Lauf war kein Browser beteiligt. Der Renderer zeichnet Titel, Beschreibung und Doc-Icon unabhängig von den Feldern, das Restrisiko ist also klein und der Schaden im schlimmsten Fall der fehlende Wegweiser, nie eine Funktionsstörung. Ein Browser-Blick auf `/settings/user/security` gehört in die Phasen-Verifikation.

## What the next plans inherit

- **04-VERIFICATION:** die Wortlaut-Notiz oben wörtlich übernehmen, die Messtabelle als Beleg für SC 1, SC 3, SC 4 und SC 5 benutzen, und den Browser-Blick auf `/settings/user/security` als letzten offenen Punkt von A1 führen.
- **Doku (offen aus 04-03, jetzt vollständig beschreibbar):** `docs/client-setup.md` (Zeile 339) und `docs/oauth-setup.md` (Zeile 572) versprechen "the app's own connections page". Beide Stellen können ab jetzt Adresse (`{public_url}/connections`), Schalter **und** den Weg über Nextcloud, Einstellungen, Sicherheit, MCP Connector nennen. Dazu gehört der Satz aus 04-01, dass eine ExApp ohne lesbaren Datenschlüssel auch den AUTH-01-Pfad nicht mehr bedient, nach `docs/exapp-install.md`.
- **Phase 5 (Store-Einreichung):** die Settings-Form ist Teil des sichtbaren Verhaltens der App und gehört in die Store-Beschreibung; sie braucht keine zusätzliche Berechtigung und keine vierzehnte Route.

## Self-Check: PASSED

- `src/mcp_connector/exapp/settings_form.py`, `.planning/phases/04-per-user-verwaltung-und-prepare-context/04-04-MEASUREMENTS.md`: vorhanden.
- `src/mcp_connector/exapp/lifecycle.py`, `src/mcp_connector/tools/context.py`, `tests/unit/test_exapp_lifecycle.py`, `.planning/REQUIREMENTS.md`: vorhanden und geändert.
- Commits `d34c9dd`, `20aa72e`, `850253f`: alle in `git log`.
- Keine Stubs, keine Platzhalter, keine TODO- oder FIXME-Marker in den geänderten Dateien.
