---
phase: 02-exapp-shell
plan: 02
subsystem: auth
tags: [appapi, exapp, credentials, httpx, impersonation, nextcloud]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: verify_appapi_headers, AppApiRejected, config.exapp_settings, appapi_auth_headers
  - phase: 01-server-kern
    provides: Credentials (frozen, maskiert), deps.resolve_credentials, die 20 Aufrufstellen der Client-Schicht
provides:
  - "Credentials.mode plus Credentials.auth(): das Credential-Objekt entscheidet sein Verfahren selbst"
  - "AppApiAuth als httpx.Auth: die vier ausgehenden AppAPI-Header, zustandslos und ohne Retry-Zweig"
  - "deps._credentials_from_appapi: vierter Zweig in resolve_credentials, Signatur unveraendert"
  - "Quelltext-Gate ueber das clients-Paket: null BasicAuth, mindestens 20 creds.auth()"
affects: [02-03 Container und Manifest, 02-04 HaRP-Testtopologie, 02-05 Permission-Parity, 02-06 Live-Beweis, 03 OAuth]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Das Credential-Objekt kennt sein Verfahren; die Client-Schicht kennt keinen Modus mehr"
    - "httpx.Auth-Unterklasse mit einem einzigen yield: keine Antwort, kein Retry, kein Zustand"
    - "Quelltext-Gate ueber ein ganzes Paket statt ueber eine handgepflegte Dateiliste"

key-files:
  created:
    - tests/unit/test_appapi_credentials.py
  modified:
    - src/mcp_connector/nextcloud/credentials.py
    - src/mcp_connector/deps.py
    - src/mcp_connector/nextcloud/clients/dav.py
    - src/mcp_connector/nextcloud/clients/caldav.py
    - src/mcp_connector/nextcloud/clients/carddav.py
    - src/mcp_connector/nextcloud/clients/notes.py
    - src/mcp_connector/nextcloud/clients/deck.py
    - src/mcp_connector/nextcloud/clients/ocs.py
    - vulture_whitelist.py

key-decisions:
  - "mode bleibt ein str-Feld mit benannten Konstanten statt eines Literal-Typs, damit der Ablehnungszweig fuer einen dritten Wert erreichbar und testbar bleibt"
  - "auth() liefert pro Aufruf ein frisches Auth-Objekt; kein Caching am Credential, weil Credentials selbst pro Aufruf entstehen"
  - "AppApiAuth kapselt die Header privat und traegt ein eigenes repr; das base64-Token ist so sensibel wie APP_SECRET (T-02-13)"
  - "Der ExApp-Zweig steht vor dem Passthrough-Zweig und liest den Authorization-Header nie (D-27, T-02-11)"
  - "AUTH-05 bleibt Pending: der Weg ist verdrahtet und unit-belegt, der Berechtigungsnachweis mit zwei Konten gehoert zu 02-05"

patterns-established:
  - "Ein Verfahrenswechsel kostet eine Zeile pro Aufrufstelle, weil die Naht am Credential sitzt und nicht am Client"
  - "Gates gegen Rueckfaelle pruefen das Paket, nicht die im Plan genannten Dateien: eine siebte Datei faellt damit automatisch mit auf"

requirements-completed: []

# Metrics
duration: 15 min
completed: 2026-08-15
---

# Phase 2 Plan 02: Der vierte Credential-Modus bis in die Client-Schicht Summary

**Die Nutzeridentitaet aus AUTHORIZATION-APP-API erreicht jetzt jede der 20 Nextcloud-Aufrufstellen: Credentials kennt seinen Modus und liefert per auth() entweder httpx.BasicAuth oder AppApiAuth, resolve_credentials bekam genau einen Zweig, die Clients genau eine Zeile pro Aufruf, und Tool-Code wurde nicht angefasst.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-15T06:08:00Z
- **Completed:** 2026-08-15T06:23:00Z
- **Tasks:** 3 (davon 2 im TDD-Zyklus, also 5 Code-Commits)
- **Files modified:** 10 (1 neu, 9 geaendert)

## Accomplishments

- `nextcloud/credentials.py`: `Credentials` traegt vier neue Felder mit Defaults (`mode`, `app_id`, `app_version`, `aa_version`), die drei alten stehen unveraendert an erster Stelle, sodass alle bestehenden Konstruktoraufrufe unberuehrt blieben. `auth()` liefert `AppApiAuth` oder `httpx.BasicAuth` und wirft bei einem dritten Wert `ValueError` mit dem Modusnamen, nie mit dem Secret.
- `AppApiAuth(httpx.Auth)`: baut die vier Header genau einmal ueber das in 02-01 angelegte `appapi_auth_headers`, `auth_flow` yieldet genau einmal und liest die Antwort nicht. Kein Retry-Zweig, kein Zustand, eigenes `__repr__` mit nur der App-Id.
- `deps.py`: vierter Zweig vor dem Passthrough-Zweig plus `_credentials_from_appapi`. Zwei Ablehnungen und kein dritter Weg: eine nicht von AppAPI signierte Anfrage und ein gueltiger App-Kontext ohne Nutzer-Id enden beide in `MCPError`, ohne einen Headerwert zu wiederholen. `resolve_credentials(ctx)` hat weiterhin genau einen Parameter.
- 20 Aufrufstellen in sechs Client-Modulen ersetzt (dav 6, deck 5, caldav 4, carddav 2, notes 2, ocs 1), ohne eine weitere Logik-, Signatur- oder Reihenfolgeaenderung. `_HEADERS` mit `OCS-APIRequest: true` blieb in allen drei JSON-Clients stehen (Pitfall 12), gezaehlt vor und nach dem Task.
- 33 neue Testfaelle ohne Netz, ohne Docker und ohne Serverprozess. Die Suite waechst von 562 auf 595 gruene Tests.

## Task Commits

1. **Task 1: Credentials mit Modus und AppApiAuth als httpx.Auth** - `4000f09` (test, RED) und `359c4eb` (feat, GREEN)
2. **Task 2: Vierter Zweig in resolve_credentials** - `eef4cdb` (test, RED) und `911124f` (feat, GREEN)
3. **Task 3: Die 20 Aufrufstellen und das Gate gegen Rueckfaelle** - `4363b76` (feat)

Kein REFACTOR-Commit: beide GREEN-Staende waren bereits die Zielform.

## Files Created/Modified

- `src/mcp_connector/nextcloud/credentials.py` - `MODE_BASIC`, `MODE_APPAPI`, `MODES`, vier neue Felder, `auth()`, `AppApiAuth`, erweitertes `__repr__`
- `src/mcp_connector/deps.py` - Modul-Docstring um einen Absatz zum ungelesenen Authorization-Header ergaenzt, Import aus `.exapp.auth`, ExApp-Zweig, `_credentials_from_appapi`
- `src/mcp_connector/nextcloud/clients/dav.py` (6), `deck.py` (5), `caldav.py` (4), `carddav.py` (2), `notes.py` (2), `ocs.py` (1) - je Aufrufstelle `auth=creds.auth()`; in `ocs.py` zusaetzlich der Docstring von `ocs_get`, der woertlich "per request Basic auth" sagte
- `vulture_whitelist.py` - `_.auth_flow` mit Begruendung (httpx ruft die Methode, unser Code nie)
- `tests/unit/test_appapi_credentials.py` - 33 Faelle in vier Abschnitten: Modusfeld, ausgehende Header, Maskierung, vierter Zweig, Client-Schicht

## Decisions Made

- **`mode` bleibt `str`, nicht `Literal`.** Der Plan liess die Wahl zwischen Literal-Typ und benannter Konstantenliste. Ein `Literal["basic", "appapi"]` auf dem Feld haette den Ablehnungszweig fuer einen dritten Wert unerreichbar gemacht: `Credentials(..., mode="bearer")` waere ein pyright-Fehler im Test gewesen, und der Test haette nur mit einem `type: ignore` existieren koennen. Ein Zweig, der nicht getestet werden kann, ist kein Schutz. Stattdessen `MODE_BASIC`, `MODE_APPAPI` und `MODES` als benannte Konstanten, die alle drei benutzt werden (Default, Vergleich, Fehlermeldung).
- **Kein Auth-Objekt-Cache am Credential.** `auth()` baut pro Aufruf ein frisches Objekt. Das kostet einen base64-Aufruf pro Request und haelt die Regel "kein Caching von Credentials" aus dem `deps.py`-Docstring unangetastet; ein am Credential haengendes Auth-Objekt waere Zustand, der eine Anfrage ueberleben koennte.
- **Das Quelltext-Gate liest das Paket, nicht die sechs Dateinamen.** `CLIENTS_DIR.glob("*.py")` statt einer Liste: ein siebtes Client-Modul faellt damit ohne Testaenderung unter dasselbe Verbot. Bei Fehlschlag nennt der Test Datei und Zeilennummer.
- **AUTH-05 bleibt Pending.** Dieser Plan belegt in-process, dass die Identitaet aus genau einem Header bis in jede Anfrage fliesst. Der Requirement-Text verlangt mehr ("der Assistent sieht nie mehr als der Nutzer in der Weboberflaeche"); das ist der Negativbeweis mit zwei Konten aus 02-05 gegen eine laufende Nextcloud. Das folgt der Phase-1-Praxis (AUTH-01 blieb bis zum Live-Beweis Pending) und der Entscheidung aus 02-01.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `pytest.raises(ValueError, match=...)` statt eines nackten Kontexts**
- **Found during:** Task 1
- **Issue:** Der Test auf das Fehlen des Secrets in der ValueError-Meldung nutzte zuerst `pytest.raises(ValueError)` ohne `match`. Ruff-Regel PT011 lehnt das ab (zu breit), und die globale Projektregel verlangt `match=` ohnehin.
- **Fix:** `match="credential mode"` ergaenzt; der Nachbartest prueft weiterhin `match="bearer"`, also den Modusnamen in der Meldung.
- **Files modified:** tests/unit/test_appapi_credentials.py
- **Verification:** `uv run --no-sync ruff check tests/unit/test_appapi_credentials.py` -> All checks passed
- **Committed in:** `4000f09`

**2. [Rule 3 - Blocking] Hilfsfunktion `basic()` ohne Default-Parameter**
- **Found during:** Task 2
- **Issue:** `def basic(user="mallory", secret="another-password")` loeste S107 aus (hardcodiertes Passwort als Default). Fuer Tests sind S101, S105 und S106 ignoriert, S107 nicht.
- **Fix:** Die Funktion nimmt keine Parameter mehr und baut den Fremd-Header aus einem Byte-Literal. Sie wird ohnehin nur in einer einzigen Auspraegung gebraucht: als zweiter, wirkungsloser Kanal.
- **Files modified:** tests/unit/test_appapi_credentials.py
- **Verification:** `uv run --no-sync ruff check .` -> All checks passed
- **Committed in:** `eef4cdb`

**3. [Rule 3 - Blocking] `Generator[..., ..., None]` auf zwei Parameter gekuerzt**
- **Found during:** Task 1
- **Issue:** Die Rueckgabeannotation von `auth_flow` war als `Generator[httpx.Request, httpx.Response, None]` geschrieben (so steht sie in der httpx-Dokumentation). Ruff-Regel UP043 meldet das dritte Argument als unnoetigen Default.
- **Fix:** `Generator[httpx.Request, httpx.Response]`. Pyright akzeptiert die Signatur als Ueberschreibung von `httpx.Auth.auth_flow` unveraendert.
- **Files modified:** src/mcp_connector/nextcloud/credentials.py
- **Verification:** `uv run --no-sync ruff check .` und `uv run --no-sync pyright` -> beide sauber
- **Committed in:** `359c4eb`

**4. [Rule 2 - Missing Critical] `_.auth_flow` in die vulture-Whitelist**
- **Found during:** Task 3
- **Issue:** `auth_flow` wird ausschliesslich von httpx aufgerufen; vulture meldete die Methode als unbenutzt und liess das Gate rot.
- **Fix:** Eintrag `_.auth_flow` mit Ein-Zeilen-Begruendung nach dem Muster von `_.verify_token`. `auth` selbst brauchte keinen Eintrag: nach Task 3 hat es 20 sichtbare Aufrufer.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` -> leer, Exit-Code 0
- **Committed in:** `4363b76`

### Abweichungen ohne Rule-Zuordnung (Plan-Text gegen Realitaet)

- **Ausgangsstand der Testsuite:** Das Akzeptanzkriterium von Task 3 nennt 476 gruene Tests. Tatsaechlicher Ausgangswert war 562 (Stand `b571991`, wie im 02-01-SUMMARY dokumentiert). Nach diesem Plan: 595.
- **Grep-Gate und `__pycache__`:** Die Akzeptanz-Greps im Plan laufen ohne `--include=*.py` und zaehlen damit auch `.pyc`-Dateien mit. Direkt nach der Aenderung enthielten die alten Bytecode-Dateien noch `BasicAuth`; nach dem ersten Testlauf sind sie neu erzeugt. Beide Zaehlungen wurden am Ende in der Plan-Schreibweise ausgefuehrt und ergeben 0 und 20. Der Test im Repo liest ausdruecklich nur `*.py`, ist also nicht von der Bytecode-Frische abhaengig.
- **`uv run --no-sync` durchgehend:** Zwei laufende `nc-mcp.exe`-Prozesse des Owners sperren `.venv/Scripts/nc-mcp.exe`; ein von `uv run` ausgeloester Reinstall scheitert daran mit `os error 32`. Dieser Plan aendert `pyproject.toml` nicht, `--no-sync` war also nur Vorsicht und keine Einschraenkung.
- **Nur ein Docstring musste umgeschrieben werden:** Der Plan rechnete mit mehreren Stellen, die woertlich "Basic auth" sagen. Ein Grep ueber `src/mcp_connector/nextcloud/` fand genau eine (`ocs.ocs_get`); die anderen fuenf Module begruenden "pro Request" ohne das Verfahren zu nennen.

---

**Total deviations:** 4 auto-fixed (1 Missing Critical, 3 Blocking) plus 4 dokumentierte Textabweichungen.
**Impact on plan:** Kein Scope-Zuwachs, keine zusaetzliche Datei ausser der geplanten Testdatei, keine Signaturaenderung ausserhalb der geplanten.

## Checkpoints

Der Plan enthaelt keine Checkpoints. Im AUTO_MODE war keine auto-approve-Entscheidung noetig. Ein Package-Legitimacy-Fall kam nicht auf: dieser Plan nimmt laut D-24 keine neue Dependency auf, `pyproject.toml` wurde nicht angefasst und `respx` liegt seit Phase 1 in der dev-Gruppe.

## Verification Log

1. `uv run --no-sync pytest` -> **595 passed, 54 deselected** (Ausgangsstand 562), ohne Docker und ohne Netz
2. Grep-Gate in der Plan-Schreibweise: `grep -rc "BasicAuth" src/mcp_connector/nextcloud/clients/ | awk ...` -> **0**; dasselbe fuer `creds.auth()` -> **20**
3. `grep -rc "OCS-APIRequest" src/mcp_connector/nextcloud/clients/ | awk ...` -> **12**, unveraendert gegenueber dem Stand vor Task 3 (6 in `*.py`, 6 im Bytecode)
4. respx-Gegenprobe aus demselben Aufrufpfad (`ocs.ocs_get`): Basic-Modus sendet `Authorization: Basic ...` und keinen AppAPI-Header; appapi-Modus sendet `AA-VERSION`, `EX-APP-ID`, `EX-APP-VERSION`, `AUTHORIZATION-APP-API` und keinen `Authorization`-Header; `OCS-APIRequest: true` liegt in beiden Faellen an
5. Phase-1-Guard: `uv run --no-sync pytest tests/unit/test_credentials_http.py::test_no_tool_parameter_can_set_the_user` -> 1 passed
6. `uv run --no-sync ruff check .` -> All checks passed; `uv run --no-sync ruff format --check .` -> 99 files already formatted
7. `uv run --no-sync pyright` -> **0 errors, 0 warnings, 0 informations**; `uv run --no-sync vulture src scripts vulture_whitelist.py` -> leer
8. `uv run --no-sync python scripts/check_tool_budget.py` -> 10642 Bytes, 15 Tools, Budget 12500 (Tool-Oberflaeche unveraendert, kein Tool-Code angefasst)
9. Task-1-Akzeptanzkriterien einzeln: `repr(Credentials(..., mode='appapi', ...))` -> `Credentials(base_url='http://nc.test', user='bob', mode='appapi', secret='***')` (weder `s3cr3t` noch das base64-Token enthalten); `type(Credentials(...).auth()).__name__` -> `BasicAuth`
10. Task-2-Akzeptanzkriterium: `grep -v '^\s*#' src/mcp_connector/deps.py | grep -c "verify_appapi_headers"` -> 2; keine Fehlermeldung in `deps.py` bettet einen Headerwert per f-String ein (die drei vorhandenen f-Strings setzen ausschliesslich die Modulkonstante `_BASIC_HINT` ein)

## Threat Model Coverage

| Threat ID | Umsetzung | Beleg |
|-----------|-----------|-------|
| T-02-10 | Nutzer kommt nur aus dem Header; `resolve_credentials` behaelt genau einen Parameter | `test_resolve_credentials_still_takes_exactly_one_parameter`, `test_no_tool_parameter_can_set_the_user` (Phase 1, unveraendert gruen) |
| T-02-11 | Der Authorization-Header wird im ExApp-Modus nicht gelesen | `test_an_additional_basic_header_changes_nothing`, `test_a_basic_header_alone_is_not_enough_in_the_exapp_mode` |
| T-02-12 | Leere Nutzer-Id endet in `MCPError`, nicht in `Credentials` | `test_an_empty_user_id_gets_no_data_access` |
| T-02-13 | `Credentials.__repr__` maskiert, `AppApiAuth` haelt `_headers` privat und hat ein eigenes repr | drei repr-Tests, zusaetzlich `test_the_exapp_resolution_writes_nothing_to_the_log` |
| T-02-14 | `follow_redirects=False` im geteilten Client unveraendert; die Basis-URL kommt aus `exapp_settings`, nie aus dem Request | `test_shared_client_is_hardened` (Phase 1), `_credentials_from_appapi` nutzt `settings.base_url` |
| T-02-15 | Quelltext-Gate ueber das gesamte clients-Paket | `test_no_client_module_hard_wires_basic_auth`, `test_every_call_site_asks_the_credentials` |
| T-02-16 | `OCS-APIRequest` steht unveraendert in allen JSON-Clients | `test_the_json_clients_keep_the_ocs_api_request_header`, plus die Header-Pruefung in beiden respx-Tests |

## Known Stubs

Keine. Jede neue Funktion hat ihren produktiven Aufrufer: `Credentials.auth` <- 20 Aufrufstellen der Client-Schicht; `AppApiAuth.auth_flow` <- httpx bei jedem so signierten Request; `_credentials_from_appapi` <- `resolve_credentials` im Modus `exapp`.

## Issues Encountered

- Keine. Die gesperrte `.venv/Scripts/nc-mcp.exe` aus 02-01 blieb ohne Wirkung, weil dieser Plan `pyproject.toml` nicht aendert; alle Kommandos liefen vorsorglich mit `--no-sync`.

## User Setup Required

Keine. Dieser Plan braucht weder Docker noch eine laufende Nextcloud und nimmt keine neue Dependency auf.

## Next Phase Readiness

- **Bereit fuer 02-03/02-04:** Der Container kann ab jetzt tatsaechlich Nutzerdaten lesen. Was im Deploy-Environment vorhanden sein muss, damit `_credentials_from_appapi` durchlaeuft: `APP_ID`, `APP_SECRET`, `APP_VERSION` und `NEXTCLOUD_URL` (`AA_VERSION` ist optional und wird nur durchgereicht).
- **Bereit fuer 02-05:** Der Permission-Parity-Test kann `Credentials(..., mode="appapi", secret=APP_SECRET, user="bob", app_id=..., app_version=...)` bauen und den Rest von `tests/integration/test_permission_fidelity.py` unveraendert uebernehmen, so wie es 02-PATTERNS.md vorzeichnet.
- **Offener Punkt fuer 02-06:** Ob CalDAV- und CardDAV-REPORTs unter Impersonation dieselben Antworten liefern wie mit App-Passwort, ist weiterhin unbelegt (MEDIUM confidence aus der Research-Phase). Der Code-Pfad dafuer steht jetzt, der Beweis fehlt.
- **Requirements:** AUTH-05 bleibt Pending, siehe Decisions.

## Self-Check: PASSED

- Die neu angelegte Datei liegt auf der Platte: `tests/unit/test_appapi_credentials.py` (`[ -f ]` geprueft).
- Alle fuenf Task-Commits sind in `git log` auffindbar: `4000f09`, `359c4eb`, `eef4cdb`, `911124f`, `4363b76`.
- Alle Akzeptanzkriterien der drei Aufgaben und alle fuenf Punkte des Plan-Verification-Blocks wurden ausgefuehrt, siehe Verification Log.
- Kein Commit dieses Plans loescht eine Datei (`git diff --diff-filter=D --name-only` je Commit -> leer).

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
