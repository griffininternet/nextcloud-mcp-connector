---
phase: 01-server-kern
plan: 03
subsystem: testing
tags: [docker, nextcloud, webdav, create-only, if-none-match, respx, integration, tdd]

# Dependency graph
requires:
  - phase: 01-02
    provides: "DAV-Client mit safe_path/files_url/_check, NcClients, ToolError-Format, graceful(), CREATE_ONLY-Annotationen, Integration-Skip-Guard in tests/conftest.py"
provides:
  - "Lokale Test-Nextcloud als Code: compose.test.yml (nextcloud:34-apache, SQLite, Healthcheck) plus idempotentes scripts/bootstrap_test_nc.sh"
  - "Zwei Testnutzer alice und bob mit Kalender, Adressbuch und App-Passwoertern; Notes 6.0.1 und Deck 1.18.3 installiert"
  - ".env.test (git-ignoriert) als einzige Quelle der Integrationstest-Credentials, dokumentiert in .env.test.example"
  - "files_upload: der einzige Schreibpfad der Phase, Create-only per If-None-Match: *"
  - "dav.put_new_file mit vollstaendigem Schreib-Status-Mapping (412, 403, 404/409, 405, 413, 423, 507, 204-Alarm)"
  - "Laufzeit-Beweis fuer Annahme A1: Nextcloud 34.0.2 antwortet auf den zweiten PUT mit 412, der Inhalt bleibt unveraendert"
affects: [01-04-streamable-http, 01-05-files-search-list, 01-06-notes, 01-07-kalender, 01-08-kontakte, 01-09-deck, 01-14-tool-contract]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Test-Infrastruktur als Code: ein Compose-File plus ein idempotentes Bootstrap-Skript, lokal und in CI identisch aufrufbar"
    - "Bootstrap prueft erst und handelt dann (user:info, app:install/app:enable, dav:create-*), statt Fehler mit '|| true' zu verstecken"
    - "Schreibpfad ohne Vorab-PROPFIND: die Ueberschreibsperre ist eine serverseitige Precondition, ein Existenzcheck waere nur ein Race-Fenster"
    - "Akzeptanzkriterien werden zu dauerhaften Unit-Guards (tests/unit/test_test_env_setup.py: CRLF, Pflicht-occ-Kommandos, gitignore)"
    - "Integrationstests laufen als alice, nie als admin; jeder Test schreibt auf einen eigenen Zeitstempel-Pfad"

key-files:
  created:
    - compose.test.yml
    - scripts/bootstrap_test_nc.sh
    - .env.test.example
    - tests/unit/test_test_env_setup.py
    - tests/unit/test_files_upload.py
    - tests/integration/test_files_roundtrip.py
  modified:
    - src/mcp_connector/nextcloud/clients/dav.py
    - src/mcp_connector/tools/files.py
    - src/mcp_connector/server/reg_files.py
    - tests/contract/test_tool_surface.py

key-decisions:
  - "occ-Kommandos mit Passwort laufen ueber 'docker compose exec -e OC_PASS=...': eine auf dem Host exportierte Variable erreicht den Container nie"
  - "Der Healthcheck bleibt auf status.php, das Warten auf die fertige Installation macht das Bootstrap-Skript per 'occ status'"
  - "Ein 204 auf den PUT wird als gebrochene Precondition gemeldet, nicht als erfolgreicher Create: sonst wuerde ein stiller Overwrite als Erfolg durchgehen"
  - "409 wird wie 404 auf 'Elternordner fehlt' gemappt: WebDAV antwortet auf ein fehlendes Collection-Ziel mit 409 Conflict"
  - "content_type wird gegen ein nacktes type/subtype-Muster geprueft, bevor es ein Header wird (modellgelieferter Wert, Header-Injection)"
  - "TOOL-01 und TOOL-09 bleiben Pending: files_search und files_list fehlen noch (Plan 01-05), und der Grep- plus Registry-Beweis fuer TOOL-09 gehoert zu Plan 01-14"

patterns-established:
  - "Create-only-Write: PUT mit If-None-Match: *, kein Auto-Mkcol, kein Force-Flag, Konflikt als handlungsfaehige Meldung"
  - "Jeder neue Schreibpfad bekommt einen Integrationstest, der den rohen Statuscode des echten Servers behauptet, nicht nur die eigene Fehlermeldung"

requirements-completed: []

# Metrics
duration: 25 min
completed: 2026-08-14
---

# Phase 1 Plan 03: Test-Nextcloud und Create-only-Upload Summary

**files_upload schreibt ausschliesslich neu (PUT mit If-None-Match: *), und eine per compose.test.yml startbare Nextcloud 34.0.2 belegt zur Laufzeit, dass der zweite PUT auf denselben Pfad mit 412 abgelehnt wird**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-14T15:51:00Z
- **Completed:** 2026-08-14T16:16:00Z
- **Tasks:** 3 (davon 1 Checkpoint, im Auto-Modus selbst ausgefuehrt)
- **Files modified:** 10 (6 neu, 4 geaendert)

## Accomplishments

- Test-Nextcloud mit zwei Kommandos: `docker compose -f compose.test.yml up -d --wait` plus `bash scripts/bootstrap_test_nc.sh`. Das Skript ist idempotent (dritter Lauf: Exit 0, alles "exists"/"already there") und legt Notes, Deck, alice, bob, Kalender, Adressbuch und beide App-Passwoerter an.
- `files_upload` ist implementiert, annotiert (read_only_hint=False, destructive_hint=False, idempotent_hint=False) und mit 20 Unit-Faellen plus 4 Integrationstests belegt.
- **Annahme A1 bestaetigt.** Gegen die echte Nextcloud 34.0.2: erster PUT 201, zweiter PUT auf denselben Pfad 412, Inhalt danach unveraendert `original`. Der dokumentierte Fallback (PROPFIND-Existenzcheck mit TOCTOU-Restrisiko) wird nicht gebraucht und bleibt ungebaut.
- Die Testsuite bleibt ohne Docker gruen: 129 Tests, Integrationstests werden per Marker und Env-Guard uebersprungen.

## Task Commits

1. **Task 1: Test-Nextcloud per compose und idempotentes Bootstrap** - `c426df7` (chore)
2. **Task 2 (RED): failing tests fuer den Create-only-Upload** - `74932b0` (test)
3. **Task 2 (GREEN): files_upload als Create-only-Schreibpfad** - `ec1005f` (feat)
4. **Task 3: Docker-Lauf, dabei gefundener Bootstrap-Fehler** - `28c30f3` (fix)

Ein REFACTOR-Commit war nicht noetig: die GREEN-Implementierung brauchte keine Nacharbeit.

**Plan metadata:** siehe docs-Commit unten.

## Files Created/Modified

- `compose.test.yml` - nextcloud:34-apache auf SQLite, Port ueber `NC_TEST_PORT` ueberschreibbar, Healthcheck fuer `up -d --wait`, benanntes Datenvolume
- `scripts/bootstrap_test_nc.sh` - idempotentes Setup: Warten auf die Installation, Notes und Deck, alice und bob, `dav:create-calendar`/`dav:create-addressbook`, Brute-Force-Schutz aus, App-Passwoerter, `.env.test`, Verifikationsausgabe, Offline-Fallback als Kommentarblock
- `.env.test.example` - die fuenf Variablennamen mit Platzhaltern, ohne Token
- `src/mcp_connector/nextcloud/clients/dav.py` - `put_new_file()` plus `_check_write()`; Modul-Docstring auf den neuen Schreibpfad umgestellt
- `src/mcp_connector/tools/files.py` - `upload()` mit Ordner-, Mimetype- und UTF-8-Guard
- `src/mcp_connector/server/reg_files.py` - `files_upload` mit `CREATE_ONLY` und `structured_output=False`
- `tests/unit/test_files_upload.py` - 20 Faelle inklusive expliziter `If-None-Match: *`-Pruefung
- `tests/integration/test_files_roundtrip.py` - 4 Tests gegen die echte Instanz, inklusive rohem 412-Statusbeweis
- `tests/unit/test_test_env_setup.py` - Dauer-Guards fuer CRLF, Pflicht-occ-Kommandos, `.env.test` im gitignore
- `tests/contract/test_tool_surface.py` - Annotations-Contract fuer `files_upload`

## Decisions Made

- Die Konfliktmeldung wird auf message und hint aufgeteilt (`A file already exists at <path>.` plus `This server never overwrites files. Choose a different name.`), weil `graceful()` beides als eine Zeile an das Modell gibt. Der geforderte Wortlaut steht damit vollstaendig in der Tool-Antwort.
- `content_type` bleibt bewusst kein Tool-Parameter in `tools/list` (Schema-Diaet); die Tool-Funktion nimmt ihn fuer spaetere Aufrufer trotzdem entgegen und validiert ihn.
- Kein Upload-Limit: T-01-20 ist im Threat-Register als `accept` eingestuft, der Inhalt kommt ohnehin aus dem Client-Kontext.
- Wegwerf-Credentials im Compose-File sind ueber `${NC_TEST_ADMIN_PASSWORD:-...}` ueberschreibbar; echte Tokens entstehen erst zur Laufzeit und landen ausschliesslich in der git-ignorierten `.env.test`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] OC_PASS erreichte den Container nicht**
- **Found during:** Task 1 (Bootstrap-Skript)
- **Issue:** Das Research-Snippet setzt `OC_PASS='...' $OCC user:add --password-from-env`. Die Variable gilt damit nur fuer den `docker`-Client auf dem Host; der Prozess im Container sieht sie nie, und `--password-from-env` scheitert.
- **Fix:** Helper `occ_pw()`, der `docker compose exec -T -e "OC_PASS=..."` benutzt.
- **Files modified:** scripts/bootstrap_test_nc.sh
- **Verification:** `user alice: created` und `user bob: created` im Bootstrap-Lauf, App-Passwoerter werden erzeugt.
- **Committed in:** c426df7

**2. [Rule 1 - Bug] Testnutzer-Passwoerter zu kurz fuer die Passwort-Policy**
- **Found during:** Task 3 (erster echter Docker-Lauf)
- **Issue:** `alice-pw` und `bob-pw` haben acht Zeichen, Nextcloud verlangt zehn: "Password needs to be at least 10 characters long." occ schreibt das auf stdout, das Skript hatte stdout weggeworfen, also endete der Lauf mit einem nackten Exit 1 ohne Meldung.
- **Fix:** Defaults auf `alice-test-pw-01` und `bob-test-pw-01` (ueber `NC_TEST_ALICE_PASSWORD`/`NC_TEST_BOB_PASSWORD` ueberschreibbar), Ausgabe von `user:add` wird gefangen und im Fehlerfall gezeigt.
- **Files modified:** scripts/bootstrap_test_nc.sh
- **Verification:** Bootstrap laeuft mit Exit 0 durch, Wiederholungslauf ebenfalls.
- **Committed in:** 28c30f3

**3. [Rule 2 - Missing Critical] Warten auf die fertige Installation**
- **Found during:** Task 1
- **Issue:** `status.php` antwortet, sobald Apache steht. Der Healthcheck meldet damit "healthy", waehrend die Erstinstallation noch laeuft, und der erste occ-Aufruf trifft eine halb installierte Instanz.
- **Fix:** `wait_for_install()` pollt `occ status` auf `installed: true`, bis zu fuenf Minuten, mit Log-Hinweis im Fehlerfall.
- **Files modified:** scripts/bootstrap_test_nc.sh
- **Verification:** Erster Lauf auf einem frischen Volume gab `nextcloud: installed` aus und lief durch.
- **Committed in:** c426df7

**4. [Rule 2 - Missing Critical] Statuscodes, die der Plan nicht nennt**
- **Found during:** Task 2
- **Issue:** Der Plan mappt 412, 403, 404 und 401. WebDAV antwortet auf ein fehlendes Elternverzeichnis aber mit 409, sabre schickt 204 wenn ein PUT tatsaechlich ersetzt hat, und 405/413/423/507 sind reale Antworten einer Nextcloud.
- **Fix:** `_check_write()` deckt 409 (wie 404), 405, 413, 423 und 507 ab. Ein 200 oder 204 wird als gebrochene Precondition gemeldet, nicht als Erfolg: das ist genau der Fall, in dem das Ueberschreibversprechen nicht mehr haelt (T-01-15).
- **Files modified:** src/mcp_connector/nextcloud/clients/dav.py
- **Verification:** Unit-Tests fuer 412/403/404/401/5xx/Redirect, Integrationstest fuer den echten 412.
- **Committed in:** ec1005f

**5. [Rule 2 - Missing Critical] Guards fuer Ordnerziel und Mimetype**
- **Found during:** Task 2
- **Issue:** `safe_path("/Docs/")` normalisiert den Schraegstrich weg, ein Upload nach `/Docs/` haette also stillschweigend die Datei `/Docs` gemeint. Und `content_type` ist ein modellgelieferter Wert, der ungeprueft in einen Header wandert (CRLF-Injection).
- **Fix:** Trailing Slash und Wurzelpfad werden vor dem Request abgelehnt; `content_type` muss ein nacktes `type/subtype` sein.
- **Files modified:** src/mcp_connector/tools/files.py
- **Verification:** `test_a_folder_target_is_refused_before_the_request`, `test_a_content_type_that_is_not_a_bare_mimetype_is_refused` (vier Faelle, inklusive `\r\nX-Injected: 1`).
- **Committed in:** ec1005f

**6. [Rule 2 - Missing Critical] Akzeptanzkriterien als Dauer-Guards**
- **Found during:** Task 1
- **Issue:** CRLF im Skript, ein fehlendes `dav:create-calendar` oder eine versehentlich eingecheckte `.env.test` waeren erst beim naechsten Docker-Lauf aufgefallen, also Stunden spaeter.
- **Fix:** `tests/unit/test_test_env_setup.py` prueft genau diese Punkte ohne Docker.
- **Files modified:** tests/unit/test_test_env_setup.py
- **Verification:** Teil der Default-Suite, gruen.
- **Committed in:** c426df7

---

**Total deviations:** 6 auto-fixed (2 Bugs, 4 fehlende kritische Funktionalitaet)
**Impact on plan:** Kein Scope-Zuwachs. Zwei der sechs Punkte waren echte Blocker des Docker-Laufs, die anderen vier schliessen Luecken im Schreibpfad, an denen das Kern-Sicherheitsversprechen der Phase haengt.

## Checkpoint: Task 3 (human-verify)

Im Auto-Modus selbst abgearbeitet, weil der Orchestrator Docker Desktop vorab gestartet hat (`docker info` war beim Start bereits erfolgreich). Ergebnis der vier Verifikationsschritte:

| Schritt | Ergebnis |
|---------|----------|
| `docker compose -f compose.test.yml up -d --wait` | Exit 0, Container `nc-mcp-test` healthy (Image nextcloud:34-apache frisch gezogen) |
| `bash scripts/bootstrap_test_nc.sh` | Exit 0 nach dem Passwort-Fix; Kalender `personal` fuer alice, `notes: 6.0.1`, `deck: 1.18.3`, `.env.test` geschrieben |
| `uv run pytest -m integration -q` | 4 passed |
| Roher Konfliktbeweis per curl | erster PUT `201`, zweiter PUT `412`, Inhalt danach `original` |

**Annahme A1: bestaetigt** auf Nextcloud 34.0.2 (`occ status`: version 34.0.2.1). Der Fallback-Pfad (PROPFIND-Existenzcheck vor dem PUT mit TOCTOU-Restrisiko) entfaellt und wird nicht als Folgeaufgabe notiert.

## Verification

| Check | Ergebnis |
|-------|----------|
| `uv run pytest -q` (ohne Docker) | 129 passed |
| `uv run pytest tests/unit -q` | gruen, `test_files_upload.py` mit 20 Faellen (Plan verlangt mindestens 6) |
| `uv run pytest -m integration -q --collect-only` | `tests/integration/test_files_roundtrip.py: 4` |
| `uv run pytest -m integration -q` (mit `.env.test`) | 4 passed |
| `bash -n scripts/bootstrap_test_nc.sh` | Exit 0 |
| `docker compose -f compose.test.yml config` | Exit 0 |
| CRLF im Bootstrap-Skript | keine |
| `uv run ruff check .` / `ruff format --check .` | All checks passed / 33 files already formatted |
| `uv run python scripts/check_tool_budget.py` | 1162 Bytes, 2 Tools, Budget 24000 |
| Idempotenz (dritter Bootstrap-Lauf) | Exit 0, alles "exists" bzw. "already there" |

## Known Stubs

Keine. `files_upload` ist vollstaendig verdrahtet; `content_type` ist bewusst nicht im Tool-Schema, aber in der Tool-Funktion implementiert und getestet.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Models des Plans. T-01-15 bis T-01-18 sind umgesetzt (If-None-Match, safe_path plus quote, `.env.test` im gitignore und Tests als alice, Basis-URL nur aus Env bei `follow_redirects=False`); T-01-19 bleibt bei den Plaenen 02 und 05, T-01-20 bleibt `accept`.

## Requirements

Nichts neu abgehakt, bewusst:

- **TOOL-01** braucht zusaetzlich `files_search` und `files_list` (Plan 01-05) und bleibt Pending.
- **TOOL-09** bleibt Pending bis Plan 01-14: der Laufzeitbeweis fuer den Upload steht jetzt, der Grep- und Registry-Beweis ueber alle Tools fehlt noch.
- **SRV-02** war bereits mit Plan 01-02 abgehakt.

## Issues Encountered

- Nextclouds Passwort-Policy hat den ersten echten Bootstrap-Lauf abgebrochen, ohne eine Fehlermeldung zu zeigen (occ schreibt sie auf stdout, das Skript hatte stdout verworfen). Beides behoben, siehe Deviation 2. Lehre fuer kommende Skripte: Ausgabe von occ nie blind wegwerfen.
- Ein Test hat zunaechst `mock.calls` nach dem Verlassen des `respx.mock`-Kontexts gelesen; respx setzt die Liste beim Verlassen zurueck. Die Auswertung liegt jetzt innerhalb des Kontexts, Route-Objekte (`route.calls`) bleiben dagegen auch danach lesbar.

## User Setup Required

None - die Test-Nextcloud wird komplett per Skript eingerichtet. Voraussetzung ist nur ein laufendes Docker Desktop mit WSL2-Backend.

## Next Phase Readiness

- Der Weg fuer alle folgenden Tool-Plaene steht: Integrationstests koennen ab sofort gegen eine echte Nextcloud 34 laufen, inklusive Kalender, Adressbuch, Notes und Deck.
- Plan 01-04 (Streamable HTTP) kann die Instanz direkt fuer den Client-Matrix-Lauf nutzen; `.env.test` liefert auch die Credentials des zweiten Nutzers bob fuer die spaeteren Permission-Tests.
- Offener Punkt fuer Plan 01-14: der Grep-Test gegen DELETE, MOVE, COPY und PROPPATCH ist noch nicht geschrieben, obwohl der DAV-Client die Methoden schon per Konvention meidet.
- Der Testcontainer wurde nach dem Lauf gestoppt (`docker compose -f compose.test.yml down`), das Datenvolume `nextcloud-mcp-connector_nextcloud-test-data` bleibt erhalten und spart den naechsten Install-Durchlauf.

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*

## Self-Check: PASSED

Alle zehn in diesem Plan erstellten oder geaenderten Dateien liegen auf der Platte, und alle vier Task-Commits (c426df7, 74932b0, ec1005f, 28c30f3) sind im Git-Log auffindbar.
