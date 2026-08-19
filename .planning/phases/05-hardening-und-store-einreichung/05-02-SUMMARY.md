---
phase: 05-hardening-und-store-einreichung
plan: 02
subsystem: auth
tags: [oauth, login-flow-v2, per-user-switch, app-password, fail-closed, bl-10]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "consent.py und connect.py samt Login-Flow-v2-Poll, revoke_app_password und dem Seitenkatalog exapp/ui/errors.py"
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "OAuthStore.access_disabled als lokaler Lesevorgang (D-47, D-48), die Texte CONNECTIONS_PAUSED_TITLE / SWITCH_OFF_STATE / SETTINGS_PLACE und die 403-ohne-Challenge-Wahl von R1 (D-51)"
provides:
  - "errors.PAUSED (E9): die Seite eines Kontos, das seinen MCP-Zugriff pausiert hat, 403 ohne WWW-Authenticate, mit genau einem Link auf /connections"
  - "consent._screen: Schalter-Pruefung nach dem Poll und vor create_authorization"
  - "connect._wait: Schalter-Pruefung nach der Identitaetspruefung und vor result_page"
  - "consent._decide: Schalter-Pruefung vor der Verzweigung auf _approve, mit dem bestehenden Ablehnungspfad"
  - "consent._withdraw: der Widerrufs- und Loeschschritt aus _deny, jetzt fuer zwei Aufrufer"
  - "je Modul ein _access_disabled mit drei Zustaenden (pausiert, nicht pausiert, keine Antwort) fuer fail closed"
affects: [05-09, docs/oauth-setup, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Drei-Zustands-Lesevorgang eines Sicherheitsschalters (bool | None) statt eines bool mit geratenem Default"
    - "Durchsetzung am fruehesten Punkt, an dem die Identitaet existiert, plus Rueckgabe der bereits ausgegebenen Anmeldeinformation"
    - "Eine Ablehnung, die keine Nutzerentscheidung ist, bekommt keine access_denied-Weiterleitung, sondern eine Seite, die die Ursache nennt"

key-files:
  created: []
  modified:
    - src/mcp_connector/exapp/ui/errors.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/oauth/consent.py
    - src/mcp_connector/oauth/connect.py
    - tests/unit/test_oauth_ui.py
    - tests/unit/test_oauth_consent.py
    - tests/unit/test_oauth_connect.py
    - tests/unit/test_connections_page.py

key-decisions:
  - "Der Zeitpunkt der Pruefung ist der frueheste, an dem das Konto ueberhaupt existiert: nach dem Poll des Login Flow v2. Vorher ist kein Konto bekannt, also ist jede frueher gesetzte Pruefung entweder wirkungslos oder eine Pruefung des falschen Subjekts"
  - "Der Preis dieses Zeitpunkts ist das App-Passwort, das ab dem 200 des Polls existiert; deshalb gehoert zu jeder der drei Ablehnungen der Widerruf in einem Versuch, woertlich nach dem is_user-Zweig in connect._wait"
  - "E9 ist eine Zeile des bestehenden Katalogs und keine Kopie daneben; 403 ohne WWW-Authenticate, dieselbe Wahl wie R1 an der Transportgrenze und aus demselben Grund"
  - "E9 traegt den vorhandenen Titel CONNECTIONS_PAUSED_TITLE, aber einen eigenen Rumpf: CONNECTIONS_PAUSED_BODY zeigt bewusst nirgendwohin, weil es eine Zeile unter dem Schalter selbst steht, und diese Seite steht das nicht"
  - "Ein Store, der den Schalter nicht lesen kann, ist nie ein Nein: _access_disabled liefert None, und der Aufrufer antwortet mit der generischen Seite (fail closed, D-37)"
  - "Auch die Fehlerseite des unlesbaren Schalters gibt das App-Passwort zurueck: es existiert bei Nextcloud und wird nach dieser Ablehnung nie benutzt"
  - "Die Ablehnung in _decide bekommt keine access_denied-Weiterleitung: dieser Fehlercode heisst 'die Nutzerin hat abgelehnt', und hier hat sie nichts abgelehnt (T-05-09)"
  - "_deny wurde in _withdraw (Widerruf plus Loeschen) und das Rendern aufgeteilt, damit die neue Ablehnung dieselben drei Schritte laeuft und eine andere Seite antwortet"
  - "/authorize und connect._start bleiben ungeprueft, und der Grund steht als Docstring-Absatz an genau diesen beiden Stellen; zwei Quelltext-Tests halten ihn dort"
  - "Der Code E9 reist als benannte Konstante errors.PAUSED zwischen den Modulen, nicht als Zeichenkette"

patterns-established:
  - "Ein Sicherheitsschalter wird mit drei Zustaenden gelesen, weil ein bool fuer den Ausfall einen Default raten muesste und beide Defaults falsch sind"
  - "Eine Ablehnung, die eine Anmeldeinformation entstehen liess, gibt sie im selben Zweig zurueck"
  - "Eine bewusst nicht gepruefte Stelle traegt ihren Grund im Code und einen Test, der ihn dort haelt"

requirements-completed: []  # EXAPP-02 und EXAPP-04 bleiben Pending, siehe Abschnitt "Requirements"

# Metrics
duration: 20min
completed: 2026-08-19
---

# Phase 05 Plan 02: Der Schalter wirkt beim Verbinden Summary

**Der Per-User-Schalter wird jetzt an allen drei Punkten durchgesetzt, an denen eine Verbindung entsteht, und keine dieser Ablehnungen hinterlaesst ein benutzbares Nextcloud-App-Passwort.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-19T16:12:00Z
- **Completed:** 2026-08-19T16:32:00Z
- **Tasks:** 2 von 2
- **Files modified:** 8 (0 neu, 8 geaendert)

## Accomplishments

- Ein pausiertes Konto kann keine neue Verbindung mehr abschliessen: die OAuth-Strecke endet nach der Anmeldung auf der Seite, die den Schalter erklaert, ohne dass eine `authorizations`-Zeile entsteht.
- Die Onboarding-Strecke ohne OAuth zeigt einem pausierten Konto sein App-Passwort nie an; der Wert erscheint nicht im Antwortkoerper, und der Flow-Datensatz ist danach weg.
- Ein Konto, das erst waehrend der offenen Zustimmungsseite pausiert wurde, bekommt keinen Autorisierungscode: `auth_codes` bleibt leer, die Autorisierung ist geloescht, das App-Passwort widerrufen.
- Jede der drei Ablehnungen gibt das gerade entstandene App-Passwort in einem Versuch zurueck. Das ist per respx auf dem Draht belegt, nicht behauptet: die Menge gueltiger App-Passwoerter waechst bei gezogener Bremse nicht mehr.
- Der Text der Ablehnung nennt den Zustand (`SWITCH_OFF_STATE`), den Ort des Schalters (`SETTINGS_PLACE`) und traegt genau einen Link auf `/connections` mit dem Praefix aus `config.public_url`.
- Drei Positivkontrollen belegen, dass der normale Weg unveraendert funktioniert; ein Store-Ausfall am Pruefpunkt fuehrt zur generischen Seite und nie zum Durchlass.
- 26 neue Testfaelle, volle Suite 1674 gruen, alle Gates gruen, `uv.lock` unberuehrt, das Manifest fuehrt weiter dreizehn Routen.

## Task Commits

Beide Tasks liefen als TDD-Zyklus, also je ein RED- und ein GREEN-Commit:

1. **Task 1: Die Seite fuer den pausierten Zugriff im bestehenden Katalog** - `1cbd714` (test), `9d16fec` (feat)
2. **Task 2: Drei Pruefpunkte, jeder mit Rueckgabe des App-Passworts** - `e24673c` (test), `cf9f3db` (feat)

Ein REFACTOR-Commit war in keinem der beiden Zyklen faellig. Die Aufteilung von `_deny` in `_withdraw` plus Rendern ist Teil des GREEN-Schritts von Task 2, weil ohne sie der dritte Pruefpunkt eine Kopie des Ablehnungspfads gebraucht haette.

## Files Created/Modified

- `src/mcp_connector/exapp/ui/errors.py` - `PAUSED` (= `E9`) als benannter Code plus die Katalogzeile: 403, Titel `CONNECTIONS_PAUSED_TITLE`, Rumpf `ERROR_PAUSED_BODY`, Aktion `ACTION_OPEN_CONNECTIONS` auf `connections.CONNECTIONS_PATH`. Modul-Docstring und der Kommentar an `CODES` sagen jetzt neun statt acht.
- `src/mcp_connector/exapp/ui/strings.py` - zwei neue Konstanten (`ERROR_PAUSED_BODY`, `ACTION_OPEN_CONNECTIONS`), beide in `__all__`. Sie stehen am Dateiende und nicht im E-Block, weil der Rumpf `SETTINGS_PLACE` nennt und diese Konstante unter dem E-Block definiert ist; ein Kommentar sagt das an beiden Stellen.
- `src/mcp_connector/oauth/consent.py` - Pruefpunkt 1 in `_screen` (nach dem Poll, vor `create_authorization`) und Pruefpunkt 3 in `_decide` (vor der Verzweigung auf `_approve`); neu `_access_disabled`, `_refuse_paused` und `_withdraw`; `_deny` benutzt jetzt `_withdraw`; der `authorize`-Handler traegt den Grund, warum dort nicht geprueft wird.
- `src/mcp_connector/oauth/connect.py` - Pruefpunkt 2 in `_wait` (nach der `is_user`-Pruefung, vor `result_page`); neu `_access_disabled` und `_forget_flow`; `_start` traegt den Grund, warum dort nicht geprueft wird.
- `tests/unit/test_oauth_ui.py` - E9 in der Vertragstabelle plus vier eigene Tests (403 ohne `www-authenticate`, `no-store`, genau ein Link mit Praefix und `/connections`, kein Konto und kein Client-Name im Dokument).
- `tests/unit/test_oauth_consent.py` - Abschnitt `BL-10` mit elf Tests, ein Kommentar je BL-10-Aussage.
- `tests/unit/test_oauth_connect.py` - Abschnitt `BL-10` mit sechs Tests, gleicher Aufbau.
- `tests/unit/test_connections_page.py` - eine Positionsannahme ueber E8 gegen die Aussage getauscht, die sie meinte (siehe Deviations).

## Verification

Alle Kommandos aus dem Plan, in derselben Reihenfolge:

| Gate | Ergebnis |
|------|----------|
| `pytest tests/unit/test_oauth_ui.py -q` | 86 passed |
| `pytest tests/unit/test_oauth_consent.py tests/unit/test_oauth_connect.py -q` | 114 passed |
| `pytest -q` (volle Suite) | 1674 passed, 87 deselected |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 160 files already formatted |
| `pyright` | 0 errors, 0 warnings |
| `vulture src scripts vulture_whitelist.py` | leer |
| `python scripts/check_tool_budget.py` | gruen (11268 von 12500 Bytes, dieser Plan legt kein Tool an) |
| `pytest tests/unit/test_exapp_env_setup.py -q` | gruen (Manifest unberuehrt, keine neue Route) |
| `git diff --stat uv.lock` | leer |

Jedes Akzeptanzkriterium ist durch mindestens einen Test belegt, namentlich:

- **Je Pruefpunkt eine Ablehnung mit sichtbarem Widerruf:** `test_a_paused_account_never_reaches_the_consent_screen`, `test_a_paused_account_is_never_shown_its_app_password`, `test_an_account_paused_while_the_screen_was_open_gets_no_code`; jeder prueft `revoke.call_count == 1` gegen `/ocs/v2.php/core/apppassword`.
- **Leere Tabellen:** `authorizations == []` nach der Ablehnung in `_screen`, `auth_codes == []` nach der Ablehnung in `_decide`.
- **Kein gerendertes App-Passwort:** `APP_PASSWORD not in response.text` im Connect-Fall.
- **Drei Positivkontrollen:** `test_an_account_that_is_not_paused_reaches_the_consent_screen`, `test_an_account_that_is_not_paused_still_reads_its_credential`, `test_a_decision_of_an_account_that_is_not_paused_still_returns_a_code`; alle drei belegen zusaetzlich `revoke.call_count == 0`.
- **Fail closed:** `test_a_switch_that_cannot_be_read_creates_no_authorization`, `test_a_switch_that_cannot_be_read_shows_no_credential`, `test_a_switch_that_cannot_be_read_at_the_decision_grants_nothing`.
- **Gescheiterter Widerruf haelt nichts auf:** `test_a_revocation_that_fails_does_not_hold_up_the_refusal` (Nextcloud antwortet 500, die Ablehnung laeuft zu Ende).
- **Log-Hygiene auf DEBUG:** zwei `caplog`-Tests, je Modul einer, ohne Konto, ohne Passwortfragment, ohne Flow-Wert.
- **Die ungeprueften Stellen nennen ihren Grund:** `test_the_unchecked_places_say_why_they_are_unchecked` und `test_the_start_says_why_it_does_not_check_the_switch` lesen den Quelltext hinter `async def authorize(` bzw. `async def _start(`.

## Decisions Made

Vollstaendig im Frontmatter (`key-decisions`). Die drei tragenden:

1. **Der Zeitpunkt ist die eigentliche Entscheidung, nicht der Ort.** BL-10 nennt genau das. Vor dem Poll kennt kein Pfad das Konto: `/authorize` sieht eine Client-Id und eine Rueckadresse, `connect._start` sieht einen Button-Druck. Eine dort gesetzte Pruefung waere entweder wirkungslos oder wuerde das falsche Subjekt pruefen. Also faellt die Pruefung dorthin, wo die Anmeldung ein Konto hervorgebracht hat, und der Preis dieser Wahl ist ein App-Passwort, das schon existiert.
2. **Wer ablehnt, gibt zurueck.** Alle drei Zweige rufen `revoke_app_password` in einem Versuch, woertlich nach dem `is_user`-Zweig in `connect._wait`. Ohne diesen Schritt waere das Ergebnis dieses Plans schlechter als der Zustand vorher: die Verbindung entstuende nicht, das App-Passwort schon.
3. **Ein unlesbarer Schalter ist kein "nicht pausiert".** `_access_disabled` liefert drei Zustaende. Ein `bool` haette fuer den Ausfall einen Default raten muessen, und beide Defaults sind falsch: `True` sperrt eine gesunde Installation aus, deren Datei kurz belegt ist, `False` ist genau der Durchlass, gegen den dieser Plan gebaut ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Eine Positionsannahme ueber E8 in `test_connections_page.py`**

- **Found during:** Task 1 (sichtbar erst im Lauf der vollen Suite)
- **Issue:** `test_e8_is_a_row_of_the_existing_table_and_not_a_new_mechanism` prueft mit `errors.CODES.index("E8") == len(errors.CODES) - 2`, also "zweitletzte Zeile", meint aber laut eigener Fehlermeldung "steht vor der generischen Seite". Mit E9 zwischen den beiden war die Aussage weiter wahr und der Test rot.
- **Fix:** Die Behauptung gegen die gemeinte getauscht: `index("E8") < index(GENERIC)` plus `CODES[-1] == GENERIC`. Der Docstring nennt den Vorfall als Grund, damit die naechste Zeile im Katalog den Test nicht erneut umwirft.
- **Files modified:** `tests/unit/test_connections_page.py`
- **Verification:** volle Suite gruen
- **Commit:** `cf9f3db`

**2. [Rule 2 - Missing critical functionality] Auch der unlesbare Schalter gibt das App-Passwort zurueck**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt den Widerruf fuer die Ablehnung des pausierten Kontos und fuer den Store-Ausfall nur "kein Durchlass, sondern die generische Fehlerseite". Ohne Widerruf haette der Ausfallzweig genau den Zustand hinterlassen, gegen den T-05-08 gebaut ist: ein gueltiges App-Passwort ohne Verbindung dahinter.
- **Fix:** `_refuse_paused` (consent) und der Zweig in `connect._wait` widerrufen in beiden Faellen und unterscheiden nur die Antwortseite.
- **Files modified:** `src/mcp_connector/oauth/consent.py`, `src/mcp_connector/oauth/connect.py`
- **Verification:** `test_a_switch_that_cannot_be_read_creates_no_authorization` und `test_a_switch_that_cannot_be_read_shows_no_credential` pruefen beide `revoke.call_count == 1`
- **Commit:** `cf9f3db`

**3. [Rule 3 - Blocking issue] Das Loeschen des Flows im Ausfallzweig ist gekapselt**

- **Found during:** Task 2
- **Issue:** Der Ausfallzweig laeuft, weil der Store gerade nicht geantwortet hat. Ein ungeschuetztes `delete_flow` daneben waere in genau diesem Zweig ein 500 mit Traceback, also der Bruch der Zusage beider Modul-Docstrings ("no refusal escapes as a 500").
- **Fix:** `connect._forget_flow` und der `try` in `consent._refuse_paused` fangen den zweiten Fehlschlag mit einer Logzeile ab.
- **Files modified:** `src/mcp_connector/oauth/consent.py`, `src/mcp_connector/oauth/connect.py`
- **Verification:** die beiden Fail-closed-Tests antworten 500 mit der generischen Seite und nie mit einem Traceback
- **Commit:** `cf9f3db`

### Interpretationen

**Akzeptanzkriterium "Ziel beginnt mit der konfigurierten oeffentlichen URL".** Der Plan verlangt im selben Task, den Link ueber `layout.link()` zu bauen, damit der Praefix aus `config.public_url` kommt. Diese Hilfe erzeugt konstruktionsbedingt einen lokalen Pfad (`/exapps/mcp_connector/connections`) und keine absolute Adresse, und ein bestehender Test dieses Katalogs (`test_the_timeout_page_offers_the_way_back`) verbietet `://` in jedem `href`. Der Test prueft deshalb: das Ziel beginnt mit dem Pfad-Praefix der konfigurierten oeffentlichen URL, endet auf `/connections` und enthaelt kein `://`. Die Absicht des Kriteriums (der Praefix stammt aus `config.public_url`, HaRP-Strip beruecksichtigt) ist damit belegt, ohne eine zweite Linkform in diesen Katalog zu bringen.

## Threat Flags

Die fuenf Eintraege des Registers dieses Plans, jeder mit dem Nachweis:

| Threat ID | Kategorie | Disposition | Nachweis |
|-----------|-----------|-------------|----------|
| T-05-07 | Elevation of Privilege | mitigated | Drei Pruefpunkte an den drei Stellen, an denen das Konto bekannt ist: keine Autorisierung (`authorizations == []`), kein Code (`auth_codes == []`), keine gerenderte Anmeldeinformation (`APP_PASSWORD not in response.text`) |
| T-05-08 | Information Disclosure | mitigated | Jeder Ablehnungszweig ruft `revoke_app_password` in einem Versuch; drei respx-Tests belegen `revoke.call_count == 1`, die drei Positivkontrollen belegen `== 0` |
| T-05-09 | Spoofing | mitigated | Kein `access_denied`-Redirect fuer diesen Fall; `test_the_refusal_of_a_paused_account_is_not_reported_as_a_user_decision` prueft kein `location`, kein `access_denied` und keine Rueckadresse im Koerper; ein Kommentar an der Stelle nennt den Grund |
| T-05-10 | Denial of Service | mitigated | `_access_disabled` liefert bei jedem Fehler `None`, der Aufrufer antwortet mit der generischen Seite; drei Fail-closed-Tests, einer je Pruefpunkt |
| T-05-11 | Information Disclosure | mitigated | Die neuen Logzeilen nennen die Regel und keinen Wert; zwei `caplog`-Tests auf DEBUG ohne Konto, Passwortfragment und Flow-Wert |
| T-05-SC | Tampering | accepted | Keine Installation in diesem Plan, `git diff --stat uv.lock` leer |

Keine neue Angriffsflaeche ausserhalb des Registers: dieser Plan legt keine Route an, kein Schema aendert sich, und der einzige neue Netzwerkaufruf ist ein `DELETE` auf einen Pfad, den `loginflow` schon vorher benutzt hat.

## BL-10

**Status: geschlossen.** Der Befund ME-04 des Phase-4-Reviews ist behoben, und zwar auf dem ersten der beiden im Backlog genannten Wege (durchsetzen statt Texte abschwaechen).

**Gewaehlter Zeitpunkt der Pruefung und seine Begruendung.** Die Pruefung liegt an den drei Stellen, an denen die Anmeldung ein Nextcloud-Konto hervorgebracht hat:

1. `consent._screen`, nach dem Poll und vor `create_authorization`,
2. `connect._wait`, nach dem Poll und der `is_user`-Pruefung und vor `result_page`,
3. `consent._decide`, vor der Verzweigung auf `_approve`.

Sie liegt bewusst **nicht** an `/authorize` und nicht in `connect._start`, obwohl das Backlog `_start` als moeglichen Ort nennt: dort ist kein Konto bekannt, also waere die Pruefung dort entweder wirkungslos (kein Subjekt) oder wuerde das falsche Subjekt pruefen. Der Grund steht als Docstring-Absatz an beiden Stellen im Code, und zwei Quelltext-Tests halten ihn dort.

Der Preis dieses Zeitpunkts ist genau der, den BL-10 als Bedingung nennt: das App-Passwort existiert ab dem 200 des Polls. Deshalb gehoert zu jeder Ablehnung der Widerruf in einem Versuch, und deshalb ist die Antwort in Fall 3 nicht `denied_page` mit `access_denied`, sondern die Seite E9: die Ursache ist eine Kontoeinstellung und keine Entscheidung der Nutzerin.

**Fuer BACKLOG.md:** BL-10 kann als erledigt markiert werden, mit Verweis auf diesen Plan und die Commits `1cbd714`, `9d16fec`, `e24673c`, `cf9f3db`. Die Texte `SWITCH_OFF_STATE`, `CONNECTIONS_PAUSED_BODY` und `ACCESS_DISABLED_DESCRIPTION` bleiben unveraendert: sie sind jetzt wahr.

## Requirements

- **EXAPP-02 bleibt Pending.** Der Schalter wirkt jetzt ueberall, wo eine Verbindung entsteht, aber der Nachweis dieses Requirements ist der Live-Durchgang der Per-User-Verwaltung, und der gehoert zur Abnahme dieser Phase.
- **EXAPP-04 bleibt Pending.** Dieser Plan beruehrt das Store-Listing nicht.

## Known Stubs

Keine. Dieser Plan legt keine Ansicht ohne Datenquelle an und keinen Platzhalterwert.

## Notes for the Next Plan

- Die Seite E9 ist ab jetzt Teil des Katalogs und kostet nichts weiter: wer eine vierte Stelle findet, an der eine Verbindung entstehen kann, antwortet mit `errors.error_page(errors.PAUSED, env=env)` und ruft davor `_withdraw` bzw. `revoke_app_password`.
- Die FAQ aus Plan 05-09 kann den Satz "als Nutzer kann ich es abschalten" ohne Fussnote fuehren. Der Satz ist jetzt an der Transportgrenze (R1) und beim Verbinden (E9) gemessen wahr.
- Nicht gemessen ist der gerenderte Pixel: E9 ist wie jede Seite dieses Katalogs in-process geprueft, im Browser hat sie noch niemand gesehen. Schadensfall waere ein Layoutfehler, keine Funktionsstoerung.

## Self-Check: PASSED

- `src/mcp_connector/exapp/ui/errors.py` FOUND, enthaelt `PAUSED` und `access_disabled`-Antwortseite
- `src/mcp_connector/oauth/consent.py` FOUND, enthaelt `access_disabled` und `revoke_app_password`
- `src/mcp_connector/oauth/connect.py` FOUND, enthaelt `access_disabled` und `revoke_app_password`
- Commits `1cbd714`, `9d16fec`, `e24673c`, `cf9f3db` FOUND in `git log`
