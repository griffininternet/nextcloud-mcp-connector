---
phase: 05-hardening-und-store-einreichung
plan: 11
subsystem: exapp
tags: [gap-closure, cr-01, issuer, rfc-8414, validation, startup, resilience]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 01
    provides: "das Administrator-Formular, ueber das der unbrauchbare Wert ueberhaupt in die Installation kommt"
  - phase: 05-hardening-und-store-einreichung
    plan: 04
    provides: "die Startzeit-Aufloesung der Admin-Werte und der sichtbare Setup-Zustand, der nach der Rettung greift"
  - phase: 03-oauth-2-1
    plan: 05
    provides: "provider.auth_routes, das das Issuer-Refusal des SDK in eine ToolError uebersetzt"
provides:
  - "config_values.LOOPBACK_HOSTS plus die https-Regel in _public_url: ein http-Wert auf einem Nicht-Loopback-Host erreicht das Overlay nie"
  - "der Rettungszweig in entry_exapp.main: ein Issuer-Refusal verwirft die Adresse und baut genau einmal neu, statt den Prozess zu beenden"
  - "Regressionstests fuer beide Haelften, inklusive Praefix-Trick (localhost.example.com) und Deploy-Umgebungs-Weg"
affects: [EXAPP-04, src/mcp_connector/exapp/config_values.py, src/mcp_connector/entry_exapp.py, docs/oauth-setup.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Bedingung gehoert dorthin, wo der Wert entsteht, und die Rettung dorthin, wo sie zuschlaegt: Praevention allein schuetzt nicht vor der Deploy-Umgebung, Rettung allein liesse einen falschen Wert bis zum Bau durchlaufen"
    - "Loopback wird als Mengenzugehoerigkeit des vollstaendigen Hostnamens geprueft, nie per Praefix oder Teilzeichenkette: localhost.example.com ist ein oeffentlicher Host"
    - "Ein Rettungszweig hat genau einen Versuch: ein zweiter Fehlschlag endet weiterhin sauber mit Exit 2 statt in einer Schleife"
    - "Ein Testwert, der nicht im Log stehen darf, bekommt einen Host, der in keiner Beispieladresse des Codes vorkommt, sonst prueft die Zusicherung den Hinweistext statt den Wert"

key-files:
  created: []
  modified:
    - src/mcp_connector/exapp/config_values.py
    - src/mcp_connector/entry_exapp.py
    - tests/unit/test_exapp_config_values.py
    - tests/unit/test_exapp_entry.py
    - docs/oauth-setup.md

key-decisions:
  - "config.normalize_base_url bleibt bewusst unveraendert: dieselbe Funktion prueft NC_MCP_URL, die Adresse der Nextcloud, und dort ist http auf einem internen Host ein legitimer Betriebsfall; eine gemeinsame Regel wuerde entweder diese Installationen brechen oder den Issuer-Wert ungeprueft lassen"
  - "LOOPBACK_HOSTS enthaelt ::1 ohne eckige Klammern, weil urlsplit(...).hostname sie entfernt und klein schreibt; ein zusaetzlicher Eintrag [::1] waere toter Code, den vulture melden wuerde"
  - "Der Rettungszweig loescht den gespeicherten Admin-Wert NICHT in Nextcloud (T-05-44 accept): die Administratorin findet ihn im Formular vor und korrigiert ihn, statt ihn stillschweigend zu verlieren"
  - "build_exapp_app bekommt ein eigenes try; exapp_settings, persistent_storage und die Setup-Fehlerzeile behalten ihr eigenes try mit SystemExit(2), damit die Rettung nur fuer den einen erholbaren Fehler gilt"
  - "Der End-to-End-Nachweis laeuft ohne Stub: das echte SDK lehnt http://... als Issuer ab (Issuer URL must be HTTPS), und das gestartete Programm antwortet danach mit dem Default in seinen Discovery-Dokumenten"

patterns-established:
  - "Ein Gap-Closure-Plan schliesst beide Haelften eines Fundes und belegt jede mit einem eigenen Test, der ohne den Fix rot ist"

requirements-completed: [EXAPP-04]

# Metrics
duration: 35min
completed: 2026-08-20
---

# Phase 05 Plan 11: Gap Closure CR-01 Summary

**Ein `http://`-Wert auf einem oeffentlichen Host kommt nicht mehr durch die Validierung, und selbst wenn er aus der Deploy-Umgebung stammt, beendet er den Prozess nicht mehr: die App verwirft die Adresse, laeuft mit dem Default weiter und sagt im Log und auf der Connections-Seite, wo sie zu korrigieren ist.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-08-20T04:05:00Z
- **Completed:** 2026-08-20T04:40:00Z
- **Tasks:** 2 von 2
- **Files modified:** 5

## CR-01

Der Fund aus 05-REVIEW.md (Critical) und Gap 1 aus 05-VERIFICATION.md (Truth 5 FAILED) ist in beiden Haelften geschlossen.

**Haelfte 1, Praevention (`exapp/config_values._public_url`).** Nach der Portbereichs-Pruefung steht jetzt die Issuer-Bedingung: ist das Scheme nicht `https` und der Host nicht in `LOOPBACK_HOSTS`, wird der Wert abgelehnt, mit der Begruendung "is http on a host that is not loopback; the issuer of the authorization server has to be https (RFC 8414)". Der Ablehnungspfad ist der bestehende `_rejected`, also nennt die Warnzeile das Feld und die Regel, nie den Wert und nie den Host. Die Pruefung ist eine Mengenzugehoerigkeit des vollstaendigen Hostnamens: `localhost.example.com` und `127.0.0.1.example.com` werden abgelehnt.

**Haelfte 2, Rettung (`entry_exapp.main`).** `build_exapp_app(resolved)` steht in einem eigenen `try`. Ein `ToolError` von dort fuehrt nicht mehr zu `SystemExit(2)`, sondern zu: `resolved.pop(NC_MCP_PUBLIC_URL)`, einer Fehlerzeile mit Meldung und Hint der gefangenen Ausnahme plus dem Ort der Einstellung und den zwei occ-Kommandos, und genau einem erneuten Bau. Der zweite Bau laeuft mit `config.DEFAULT_PUBLIC_URL`, also greift der Setup-Zustand aus Plan 05-04, und `/init` sowie `/enabled` bleiben bedienbar. Scheitert auch der zweite Bau, endet `main` weiterhin mit `SystemExit(2)`.

**Warum `config.normalize_base_url` bewusst unveraendert blieb:** dieselbe Funktion validiert `NC_MCP_URL`, die Adresse der Nextcloud-Instanz, mit der dieser Container spricht. Dort ist `http` auf einem internen Host ein legitimer Betriebsfall, und eine gemeinsame Verschaerfung wuerde bestehende Installationen brechen. Die schaerfere Regel gehoert an den Wert, der zum `issuer` wird, und steht deshalb in `_public_url`. Beide Docstrings sagen das jetzt ausdruecklich.

**Testnamen, mit denen der Verifier den Fund nachpruefen kann:**

| Test | Datei | Was er belegt |
|------|-------|---------------|
| `test_an_unusable_public_url_is_dropped_and_named_without_its_value[http://cloud.example.com/exapps/mcp_connector-...]` | `tests/unit/test_exapp_config_values.py` | Der Wert des Fundes erreicht das Overlay nicht mehr |
| `test_an_unusable_public_url_is_dropped_and_named_without_its_value[http://localhost.example.com/x-...]` | `tests/unit/test_exapp_config_values.py` | Praefix-Trick abgelehnt (Gleichheit statt `startswith`) |
| `test_an_unusable_public_url_is_dropped_and_named_without_its_value[HTTP://Cloud.Example.COM-...]` | `tests/unit/test_exapp_config_values.py` | Gross- und Kleinschreibung entscheidet nichts |
| `test_https_and_every_loopback_spelling_reach_the_overlay` | `tests/unit/test_exapp_config_values.py` | https und alle vier Loopback-Schreibweisen bleiben brauchbar |
| `test_the_default_in_code_survives_this_validation` | `tests/unit/test_exapp_config_values.py` | `config.DEFAULT_PUBLIC_URL` besteht die Validierung |
| `test_the_refused_http_value_leaves_neither_host_nor_value_in_the_log` | `tests/unit/test_exapp_config_values.py` | Genau eine Warnzeile, ohne Host und ohne Wert |
| `test_the_loopback_hosts_are_the_three_spellings_of_this_machine` | `tests/unit/test_exapp_config_values.py` | Die Menge ist genau `localhost`, `127.0.0.1`, `::1` |
| `test_one_issuer_refusal_drops_the_address_instead_of_the_process` | `tests/unit/test_exapp_entry.py` | Erster Bau wirft, `main` wirft kein `SystemExit`, `uvicorn.run` wird erreicht, der zweite Bau bekommt eine Umgebung ohne `NC_MCP_PUBLIC_URL` |
| `test_a_second_refusal_ends_the_start_with_exit_two` | `tests/unit/test_exapp_entry.py` | Zwei Fehlschlaege ergeben `SystemExit(2)` und genau zwei Aufrufe |
| `test_an_unusable_address_from_the_deploy_environment_takes_the_same_way` | `tests/unit/test_exapp_entry.py` | Derselbe Weg fuer einen Wert aus der Deploy-Umgebung, ohne Stub, gegen das echte SDK |
| `test_the_rescued_start_shows_the_setup_state_on_the_connections_page` | `tests/unit/test_exapp_entry.py` | Nach der Rettung zeigt `/connections` den Setup-Zustand aus 05-04 |
| `test_the_rescue_line_names_the_rule_and_the_place_but_never_the_value` | `tests/unit/test_exapp_entry.py` | Regel, Ort und beide occ-Kommandos in der Zeile, weder Wert noch Host |
| `test_a_missing_volume_stops_the_start_before_anything_is_built` | `tests/unit/test_exapp_entry.py` | Gegenprobe: `persistent_storage` bleibt `SystemExit(2)`, `build_exapp_app` wird nie aufgerufen |
| `test_a_second_credential_channel_is_still_exit_two_and_builds_nothing` | `tests/unit/test_exapp_entry.py` | Gegenprobe D-27: zweiter Credential-Kanal bleibt `SystemExit(2)` |
| `test_an_unusable_admin_value_changes_nothing[http on a host that is not loopback]` | `tests/unit/test_exapp_entry.py` | Der Wert des Fundes aendert am gestarteten Programm nichts |

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 (RED) | Failing Tests fuer die https-Regel | `4f9b747` | tests/unit/test_exapp_config_values.py |
| 1 (GREEN) | `LOOPBACK_HOSTS` plus Regel in `_public_url` | `bb32a62` | src/mcp_connector/exapp/config_values.py, tests/unit/test_exapp_config_values.py |
| 2 | Rettungszweig in `main` plus Doku | `791e6b9` | src/mcp_connector/entry_exapp.py, tests/unit/test_exapp_entry.py, docs/oauth-setup.md |

Task 2 lief ebenfalls test-first: die fuenf neuen `main`-Tests waren vor der Aenderung rot (`SystemExit: 2` in `entry_exapp.py:338`) und sind nach ihr gruen. Sie liegen mit dem Fix in einem Commit, weil derselbe Commit den Startpfad umbaut, an dem sie haengen.

## Verification

Alle Gates aus dem Plan gruen, im Arbeitsverzeichnis ausgefuehrt:

- `uv run --no-sync pytest -q`: vollstaendige Suite gruen (keine Fehlschlaege, keine Fehler)
- `uv run --no-sync ruff check .`: All checks passed
- `uv run --no-sync ruff format --check .`: 166 files already formatted
- `uv run --no-sync pyright`: 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py`: ohne Fund (`LOOPBACK_HOSTS` steht in `__all__`)
- `uv run --no-sync python scripts/check_tool_budget.py`: 11268 von 12500 Bytes, 16 Tools
- `git diff --stat uv.lock`: leer, keine Installation
- `grep -c "—\|–" docs/oauth-setup.md`: 0
- `grep -n "app_api:app:enable" src/mcp_connector/entry_exapp.py`: Zeilen 323 (bestehende Setup-Zeile) und 359 (neue Rettungszeile)
- `uv run --no-sync pytest tests/unit/test_project_layout.py -q`: gruen, kein neuer modul-globaler veraenderlicher Zustand

Zusaetzlicher Laufzeitnachweis vor dem Test-Schreiben: `provider.auth_routes` mit `NC_MCP_PUBLIC_URL=http://cloud.example.com/...` antwortet mit `ToolError: NC_MCP_PUBLIC_URL is not a usable issuer: Issuer URL must be HTTPS`. Das ist die Ausnahme, die vorher den Prozess beendete, und sie ist damit gemessen und nicht angenommen.

## Deviations from Plan

### 1. [Rule 3 - Blocking] Der Test `test_an_unusable_admin_value_changes_nothing` liegt in der anderen Datei

- **Gefunden bei:** Task 1
- **Sachlage:** Der Plan verlangt in Task 1, die Parametrisierung von `test_an_unusable_admin_value_changes_nothing` in `tests/unit/test_exapp_config_values.py` zu erweitern. Dieser Test steht aber in `tests/unit/test_exapp_entry.py`; die Datei der Validierung hat den entsprechenden Test unter dem Namen `test_an_unusable_public_url_is_dropped_and_named_without_its_value`.
- **Loesung:** Beide Parametrisierungen erweitert, in beiden Dateien. Damit sind alle Abnahmekriterien erfuellt (`cloud.example.com` erscheint im Validierungs-Test, und der Startpfad-Test kennt den Fall ebenfalls).
- **Commits:** `4f9b747`, `791e6b9`

### 2. [Rule 1 - Bug] Der Testwert der Log-Zusicherung musste einen anderen Host bekommen

- **Gefunden bei:** Task 2
- **Sachlage:** Die Zusicherung "der Host des Wertes steht nicht im Log" waere mit `cloud.example.com` falsch rot geworden: `provider._HINT_ISSUER` fuehrt genau diese Adresse als Beispiel, und der Hint wird bewusst mitgeloggt. Der Test haette dann den Hinweistext geprueft statt den Wert.
- **Loesung:** Der Testwert heisst `http://tls-is-missing.example.org/exapps/mcp_connector`, mit einem Kommentar, der den Grund nennt. Die Zusicherung prueft jetzt genau das, was sie prueft soll.
- **Commit:** `791e6b9`

### 3. [Rule 1 - Bug] Ein Vergleich musste umgeschrieben werden (ruff SIM300)

- **Gefunden bei:** Task 1
- **Sachlage:** `assert config_values.LOOPBACK_HOSTS == frozenset({...})` wurde von ruff als Yoda-Bedingung gemeldet.
- **Loesung:** `assert isinstance(..., frozenset)` plus `assert set(...) == {...}`. Die Zusicherung wurde dadurch sogar genauer: sie belegt jetzt auch den Typ.
- **Commit:** `bb32a62`

Ein zusaetzlicher Ablehnungsfall wurde ueber den Plan hinaus aufgenommen (`http://192.168.1.10:8080/x`): eine private Adresse ist ebenso wenig Loopback wie eine oeffentliche, und ohne diesen Fall waere die Regel nur an oeffentlichen Namen belegt.

## Known Stubs

Keine.

## Threat Flags

| Threat ID | Kategorie | Disposition | Stand nach diesem Plan |
|-----------|-----------|-------------|------------------------|
| T-05-40 | Spoofing, Information Disclosure | mitigate | Geschlossen: https-Pflicht mit Loopback-Ausnahme in `_public_url`, Mengenzugehoerigkeit des vollen Hostnamens, Regressionstests fuer Praefix-Tricks |
| T-05-41 | Denial of Service | mitigate | Geschlossen: die Adresse wird verworfen, genau einmal neu gebaut, der Prozess laeuft mit dem Default weiter; ein zweiter Fehlschlag endet sauber mit Exit 2 statt in einer Schleife |
| T-05-42 | Elevation of Privilege | mitigate | Geschlossen: der Setup-Zustand der Connections-Seite greift nach der Rettung (eigener Test), plus Fehlerzeile mit Ort der Einstellung; keine Adresse wird aus `NEXTCLOUD_URL` hergeleitet (A2) |
| T-05-43 | Information Disclosure | mitigate | Geschlossen: weder `_rejected` noch die neue Fehlerzeile geben Wert oder Host aus, zwei Tests pruefen das |
| T-05-44 | Tampering | accept | Bewusst kein Schreibvorgang gegen Nextcloud im Rettungszweig; der Wert bleibt im Formular sichtbar und korrigierbar, der Kommentar an der Stelle sagt warum |
| T-05-SC | Tampering | accept | Keine Installation, `uv.lock` unveraendert (`git diff --stat uv.lock` leer) |

Keine neue Angriffsflaeche ausserhalb des Registers: es entstand keine Route, kein Auth-Pfad, kein Dateizugriff und keine Schema-Aenderung.

## Success Criteria

- [x] CR-01 ist in beiden Haelften geschlossen: Validierung lehnt ab, Startpfad ueberlebt
- [x] Kein Weg ueber das Admin-Formular fuehrt mehr in eine Restart-Schleife ohne UI-Recovery
- [x] http auf Loopback und https bleiben unveraendert brauchbar, bestehende Installationen laufen weiter
- [x] Die Regressionstests decken Fehler-, Edge- und Negativfaelle ab, nicht nur den Happy Path

## Self-Check: PASSED

Alle fuenf genannten Dateien existieren, das SUMMARY liegt am angegebenen Pfad, und alle vier Commits (`4f9b747`, `bb32a62`, `791e6b9`, `9b681b4`) sind im Repository nachweisbar.
