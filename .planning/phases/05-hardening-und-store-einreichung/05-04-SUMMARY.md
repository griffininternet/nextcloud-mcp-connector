---
phase: 05-hardening-und-store-einreichung
plan: 04
subsystem: infra
tags: [appapi, exapp-config, one-click-install, setup-state, oauth-discovery, admin-settings]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 01
    provides: "exapp/config_values.admin_overlay (Vorrangregel durch Auslassen), CONFIG_KEYS/KEY_TO_ENV und die Textkonstanten SETUP_PUBLIC_URL_*"
  - phase: 03-oauth-2-1
    provides: "config.public_url als synchrone, pure Funktion; oauth/registry.client_policy; die drei Discovery-Dokumente aus metadata.py"
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "die Connections-Seite mit ihren drei Zustaenden und exapp/ui/layout.callout"
provides:
  - "entry_exapp._resolved_env: die Admin-Werte werden einmal beim Prozessstart aufgeloest und als Umgebung an build_exapp_app gegeben"
  - "entry_exapp._startup_client: ein kurzlebiger httpx-Client mit den Eigenschaften von shared_client, fuer den einen Aufruf vor dem Server"
  - "Der Setup-Zustand statt Exit 2: eine Installation ohne oeffentliche Adresse laeuft weiter und sagt es"
  - "exapp/ui/connections._setup: der Hinweisblock in allen drei Zustaenden der Seite"
  - "config_values.read_values/admin_overlay mit optionalem client-Parameter"
  - "docs/oauth-setup.md Abschnitt 3: Administrator settings in Nextcloud"
affects: [05-05, 05-06, store-einreichung, appinfo/info.xml]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Startzeit-Aufloesung statt Lesen pro Request: ein Overlay wird einmal auf os.environ gelegt und als Mapping weitergegeben"
    - "Ein eigener kurzlebiger HTTP-Client fuer Aufrufe, die vor dem Server-Event-Loop laufen"
    - "Sichtbarer Setup-Zustand statt Startabbruch bei fehlender Pflichtkonfiguration"

key-files:
  created: []
  modified:
    - src/mcp_connector/entry_exapp.py
    - src/mcp_connector/exapp/config_values.py
    - src/mcp_connector/exapp/ui/connections.py
    - docs/oauth-setup.md
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_exapp_config_values.py
    - tests/unit/test_connections_page.py

key-decisions:
  - "Das Overlay wird genau einmal beim Prozessstart aufgeloest, nicht pro Request: config.public_url bleibt synchron und pur, ein Prozess-Cache waere verbotener Modulzustand (D-20), und ein Lesen pro Request waere ein zweiter Nextcloud-Roundtrip je Anfrage (SC 5 der Phase 3)"
  - "Der Preis dieser Wahl ist der Wiederaktivieren-Schritt, und er wird an drei Stellen benannt (Feldbeschreibung aus 05-01, Setup-Hinweis auf /connections, docs/oauth-setup.md Abschnitt 3) statt versteckt"
  - "Die fehlende oeffentliche Adresse ist kein Exit 2 mehr: mit Abbruch wird die App nie enabled, das Admin-Formular wird nie registriert, und der Admin hat keinen Ort fuer den Wert; die Zusicherung 'keine stille Fehlkonfiguration' haelt jetzt die Fehlerzeile plus der sichtbare Setup-Zustand"
  - "Die drei anderen Startabbrueche bleiben Exit 2 (zweiter Credential-Kanal, unvollstaendige AppAPI-Env, nicht beschreibbares Volume): sie sind keine Zustaende, die ein Admin im Browser reparieren kann"
  - "Keine Herleitung der Adresse aus NEXTCLOUD_URL (Assumption A2): ein hergeleiteter Wert waere ein stiller Default mit kaputter Discovery und sieht aus wie eine konfigurierte Installation"
  - "read_values/admin_overlay bekommen einen optionalen client, weil shared_client seinen Verbindungspool an den Event-Loop bindet, in dem er zuerst benutzt wird, und der Loop des Startzeit-Lesevorgangs sofort wieder geschlossen wird"
  - "Der Startzeit-Client wiederholt die vier Eigenschaften von shared_client, und ein Test haelt sie gleich, statt eine Konstante in nextcloud/http.py einzufuehren (Blast-Radius bleibt bei den vier geplanten Dateien)"
  - "Der Setup-Hinweis steht als erster Block ueber der Identitaetszeile, weil seine Ursache keiner der drei Seitenzustaende ist, und die Bedingung lebt in genau einer Hilfsfunktion, die alle drei teilen"
  - "Der Hinweis nennt weder den Default-Wert noch einen internen Host: auf 127.0.0.1:8765 kann niemand handeln, brauchbar ist nur der Ort der Einstellung"

patterns-established:
  - "Eine Pflichtkonfiguration, die der Admin nur im laufenden Zustand setzen kann, darf den Start nicht abbrechen: Fehlerzeile plus sichtbarer Zustand"
  - "Vorrangregel anwenden heisst Umgebung zusammenlegen, nicht Signaturen aendern"
  - "Ein Aufruf vor dem Server bringt seinen eigenen Client mit"

requirements-completed: []  # EXAPP-04 bleibt Pending, siehe Abschnitt "Requirements"

# Metrics
duration: 18min
completed: 2026-08-19
---

# Phase 05 Plan 04: Admin-Werte wirksam machen Summary

**Die in Nextcloud gesetzten Werte wirken jetzt: `main` legt sie einmal beim Start als Overlay auf die Umgebung und gibt sie an jede Route-Fabrik, und eine Installation ohne oeffentliche Adresse stirbt nicht mehr beim Start, sondern erklaert sich auf der Connections-Seite.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-08-19T16:35:41Z
- **Completed:** 2026-08-19T16:53:15Z
- **Tasks:** 2 von 2
- **Files modified:** 7 (0 neu, 7 geaendert)

## Accomplishments

- Die Verklemmung der Ein-Klick-Installation ist aufgeloest: eine Store-Installation ohne jede Umgebungsvariable startet, wird `enabled`, registriert das Admin-Formular, und der Admin kann die fehlende Adresse eintragen. Vorher beendete sich der Prozess mit Exit 2, wurde nie `enabled`, registrierte das Formular nie und liess den Admin ohne Ort fuer den Wert.
- Ein in Nextcloud gesetzter Wert wirkt auf `issuer`, `resource`, Formular-Praefix und Consent-Weiterleitung, ohne dass eine Signatur im bestehenden Code sich geaendert hat: die Vorrangregel aus 05-01 wird durch ein Zusammenlegen von `os.environ` und Overlay angewendet.
- Bestehende Installationen laufen unveraendert: ein gesetztes `NC_MCP_PUBLIC_URL` bleibt in Kraft, solange kein brauchbarer Admin-Wert existiert, und ein unbrauchbarer Admin-Wert aendert nichts (drei Negativfaelle als Test).
- Die drei AUTH-07-Schalter kommen aus derselben aufgeloesten Umgebung: mit `oauth_dcr` aus verschwindet der Registrierungsendpunkt aus dem AS-Metadatendokument der gebauten App, belegt samt Gegenprobe.
- Der Lesevorgang kann den Start nicht verhindern und keinen Container blockieren: ein Versuch, eigener kurzlebiger Client mit den Timeouts von `shared_client`, Transportfehler ergibt ein leeres Overlay.
- Die Connections-Seite sagt in allen drei Zustaenden, was fehlt und wo es hingehoert, und die Doku hat genau einen Ort mit der ganzen Wahrheit (Vorrangregel, beide occ-Kommandos, Sicherheitshinweis fuer oeffentliche Instanzen).
- 64 neue Tests (Datei-Summen: 74 + 60 + 68 = 202 in den drei beteiligten Dateien), volle Suite 1697 gruen, alle Gates gruen, `uv.lock` unberuehrt.

## Task Commits

Beide Tasks liefen als TDD-Zyklus:

1. **Task 1: Overlay beim Start aufloesen und den Startabbruch zum Setup-Zustand machen** - `84abaaa` (test), `1ebd05c` (feat), `201e2b4` (refactor: die lokale Variable in `main` heisst `resolved`, wie der Plan sie nennt)
2. **Task 2: Setup-Zustand auf der Connections-Seite und der Doku-Abschnitt** - `7edd193` (test), `62d0a13` (feat)

## Files Created/Modified

- `src/mcp_connector/entry_exapp.py` - `_startup_client()` (kurzlebiger Client mit den vier Eigenschaften von `shared_client`), `_admin_values()` (ein `async with` um `config_values.admin_overlay`), `_resolved_env()` (`{**os.environ, **overlay}`, nur im ExApp-Modus, INFO-Logzeile mit den Schluesselnamen). `main` liest die aufgeloeste Umgebung als `resolved` und gibt sie an `exapp_settings`, `persistent_storage`, `build_exapp_app`, `_warn_when_the_host_check_is_a_trap` und beide Serve-Zweige. Der `SystemExit(2)`-Zweig fuer die fehlende Adresse ist eine Fehlerzeile ohne Abbruch; der Kommentar daneben nennt die Verklemmung woertlich und den Verzicht auf die `NEXTCLOUD_URL`-Herleitung.
- `src/mcp_connector/exapp/config_values.py` - `read_values` und `admin_overlay` nehmen einen optionalen `client`; ohne ihn bleibt alles wie in 05-01 (`shared_client()` steht weiter genau einmal im Modul, der Waechter-Test dazu bleibt gruen).
- `src/mcp_connector/exapp/ui/connections.py` - `_setup(env)` vergleicht `config.public_url(env)` mit `config.DEFAULT_PUBLIC_URL` und liefert Callout plus Hinweiszeile; der Block steht als erster in `connections_page`, also in allen drei Zustaenden. Die Blockreihenfolge im Modul-Docstring ist nachgezogen.
- `docs/oauth-setup.md` - neuer Abschnitt "3. Administrator settings in Nextcloud" (Ort der Form, die vier Felder mit Feld-Id gleich Config-Schluessel, Vorrangregel, beide occ-Kommandos, der Satz zum ersten Speichern der Checkboxen, der Sicherheitshinweis fuer oeffentliche Instanzen, der Satz zum bewusst weiterlaufenden Start). Die drei folgenden Abschnitte sind auf 4 bis 6 umnummeriert, Abschnitt 1 verweist auf den neuen.
- `tests/unit/test_exapp_entry.py` - neue Sektion mit 14 Tests plus `AdminConfig`, einer autouse-respx-Fixture (kein Test dieser Datei oeffnet mehr einen Socket) und dem `start()`-Helfer, der `main` bis zum Serve laufen laesst und die gebaute App zurueckgibt.
- `tests/unit/test_exapp_config_values.py` - drei Tests zum uebergebenen Client (Draht, der geteilte Client wird nicht angefasst, Fail-soft bleibt).
- `tests/unit/test_connections_page.py` - sieben Tests zum Setup-Zustand (drei Zustaende, Abwesenheit bei gesetzter Adresse, Statuscode und `no-store`, Copy-Regeln, die Bedingung selbst) plus ein `env`-Parameter am `listing()`-Helfer.

## Verification

Alle Kommandos aus dem Plan, in derselben Reihenfolge:

| Gate | Ergebnis |
|------|----------|
| `pytest tests/unit/test_exapp_entry.py tests/unit/test_exapp_config_values.py -q` | 134 passed |
| `pytest tests/unit/test_connections_page.py -q` | 68 passed |
| `pytest -q` (volle Suite) | 1697 passed, 87 deselected |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 160 files already formatted |
| `pyright` | 0 errors, 0 warnings |
| `vulture src scripts vulture_whitelist.py` | leer |
| `python scripts/check_tool_budget.py` | gruen (kein neues Tool) |
| `pytest tests/unit/test_exapp_env_setup.py -q` | gruen (Manifest unberuehrt, keine neue Route) |
| `pytest tests/unit/test_project_layout.py -q` | gruen (kein neuer Modul-globaler Zustand) |
| `grep -n "Administrator settings" docs/oauth-setup.md` | Treffer in Zeile 94 |
| `grep -c "—\|–" docs/oauth-setup.md` | 0 |
| `git diff --stat uv.lock` | leer |

Namentlich belegte Akzeptanzkriterien: mit Admin-Wert und ohne `NC_MCP_PUBLIC_URL` traegt das Protected-Resource-Dokument der gebauten App die Admin-Adresse als `resource`; mit gesetzter Env und ohne Admin-Wert bleibt die Env-Adresse; ein Admin-Wert ohne Schema, mit Fragment oder mit `user:pass@` aendert nichts; ohne jede brauchbare Adresse wirft `main` kein `SystemExit`, schreibt aber eine Fehlerzeile mit `ADMIN_SETTINGS_PLACE` und dem Wiederaktivieren-Schritt und serviert die Dokumente weiter; `NC_MCP_STATIC_BEARER` fuehrt weiter zu `SystemExit(2)` (der bestehende parametrisierte Test); `oauth_dcr` gleich aus laesst `registration_endpoint` aus dem AS-Metadatendokument verschwinden (mit Gegenprobe); ein Transportfehler beim Lesen verhindert den Start nicht; drei aufeinanderfolgende Requests kosten genau einen Lesevorgang; ausserhalb des ExApp-Modus wird gar nicht gelesen; die INFO-Zeile nennt `NC_MCP_PUBLIC_URL` und `NC_MCP_OAUTH_ALLOWED_CLIENTS`, aber weder die Adresse noch die Client-Liste.

## Decisions Made

Vollstaendig im Frontmatter (`key-decisions`). Der Kern steht unten im Abschnitt "Entscheidung Startzeit-Overlay".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Die bestehenden Tests dieser Datei oeffneten nach der Aenderung Sockets**

- **Found during:** Task 1
- **Issue:** Sieben bestehende Tests rufen `entry_exapp.main()` mit vollstaendiger AppAPI-Env auf. Mit dem neuen Startzeit-Lesevorgang haetten sie jeder eine echte HTTP-Verbindung gegen `http://nc.test` versucht: langsam, umgebungsabhaengig und ein Bruch der Hausregel, dass ein Unit-Test kein Netz beruehrt.
- **Fix:** Eine autouse-respx-Fixture (`admin_config`) beantwortet die Leseroute fuer jeden Test der Datei; ein leeres Ergebnis ist genau der Zustand, unter dem die alten Tests geschrieben wurden. Die Fixture ist zugleich der Weg, Werte in `main` hineinzugeben, weil der Lesevorgang innerhalb von `main` passiert.
- **Files modified:** `tests/unit/test_exapp_entry.py`
- **Verification:** `admin_config.route.call_count`-Asserts in zwei Tests; die Datei laeuft ohne Netzzugriff
- **Committed in:** `84abaaa`

**2. [Rule 2 - Missing critical functionality] Zwei bestehende Tests behaupteten das alte Verhalten**

- **Found during:** Task 1
- **Issue:** `test_a_missing_public_url_stops_the_start` und `test_a_blank_public_url_counts_as_missing` verlangten woertlich `SystemExit(2)` fuer genau den Fall, den dieser Plan zum Setup-Zustand macht. Ein Loeschen haette die Aussage verloren, ein Behalten haette den Plan blockiert.
- **Fix:** Beide sind auf die neue Zusicherung umgeschrieben (Fehlerzeile mit Ort und Schritt, kein `SystemExit`, die App serviert), mit einem Docstring, der die Verklemmung als Grund nennt. Die Aussage "ein leerer Wert ist ein Tippfehler und kein Default" bleibt erhalten.
- **Files modified:** `tests/unit/test_exapp_entry.py`
- **Verification:** `test_an_installation_without_any_public_address_serves_and_says_where_to_set_it`, `test_a_blank_public_url_is_the_same_setup_state`
- **Committed in:** `84abaaa`, gruen mit `1ebd05c`

**3. [Rule 2 - Missing critical functionality] Die Doku nennt das erste Speichern der Checkboxen**

- **Found during:** Task 2
- **Issue:** 05-01 gab diesen Punkt woertlich mit ("sobald ein Admin die Form einmal speichert, schreibt Nextcloud fuer beide Checkboxen einen konkreten Wert, der dann die Deploy-Env schlaegt"). Der Plan zaehlt ihn nicht unter den Doku-Inhalten auf, aber ohne ihn ueberrascht die Vorrangregel genau die Installationen, die ihre Schalter per `--env` setzen.
- **Fix:** Ein Absatz in Abschnitt 3 samt Ausweg (Felder leeren, dann gilt die Env wieder).
- **Files modified:** `docs/oauth-setup.md`
- **Verification:** Abschnitt gelesen, `grep -c "—\|–"` bleibt 0
- **Committed in:** `62d0a13`

### Bewusste Abweichungen ohne Verhaltensunterschied

- **Der Startzeit-Client wiederholt die Timeout-Werte statt sie zu importieren.** Der Plan verlangt "dieselben Eigenschaften wie `shared_client`". Der saubere Weg waere eine Konstante in `nextcloud/http.py`, die aber nicht in `files_modified` steht. Statt den Blast-Radius zu vergroessern, halten die Werte doppelt und ein Test haelt sie gleich (`test_the_client_of_the_start_time_read_is_hardened_like_the_shared_one` vergleicht `timeout`, `follow_redirects`, den Cookie-Jar-Typ und den User-Agent gegen `shared_client()`). Wenn `nextcloud/http.py` einmal aus einem anderen Grund angefasst wird, ist die Konstante der richtige naechste Schritt.
- **Die lokale Variable in `main` heisst `resolved`.** Der Plan nennt sie so, und der eigene Commit dafuer (`201e2b4`) macht den Umbenennungs-Diff vom Verhaltens-Diff trennbar.
- **`_setup` liefert zwei Bloecke, nicht einen.** Der Callout traegt Titel und Text, die dritte Textkonstante (`SETUP_PUBLIC_URL_HINT`, die Form der Adresse) steht als gedaempfter Absatz darunter, weil `layout.callout` genau zwei Textfelder kennt und ein zweiter Callout eine zweite Warnung waere.

---

**Total deviations:** 3 (alle Rule 2) plus drei Form-Praezisierungen
**Impact on plan:** Kein Scope-Zuwachs. Zwei der drei Korrekturen sind Testhygiene, die dritte ein Satz Doku, den 05-01 bestellt hat.

## Entscheidung Startzeit-Overlay

Fuer die Phasen-Verifikation festgehalten, weil sie die eine Architekturentscheidung dieses Plans ist.

**Die Wahl:** Die Admin-Werte werden **einmal beim Prozessstart** aufgeloest (`_resolved_env`) und als gewoehnliches Mapping an `build_exapp_app` und damit an jede Route-Fabrik gegeben. Sie werden **nicht pro Request** nachgelesen.

**Die drei Gruende:**

1. **Signaturen.** `config.public_url(env)` ist synchron und pur. Ein Nachlesen pro Request muesste sie asynchron machen, und das trifft `metadata.py`, `consent.py`, `settings_form.py`, `admin_settings.py`, `layout.app_path` und damit jede Formularaktion jeder Seite. Der Diff waere ein Vielfaches dieses Plans, in genau den Pfaden, die Autorisierungen entscheiden.
2. **D-20.** Ein prozessweiter Cache mit Ablauf waere veraenderlicher Modulzustand. Das Projekt verbietet ihn mit genau zwei namentlich gelisteten Ausnahmen, und ein Dictionary, das eine Anfrage ueberlebt, ist einen Refactor von einem Session-Store entfernt.
3. **SC 5 der Phase 3.** Gemessen ist genau ein Nextcloud-Roundtrip je MCP-Request. Ein Config-Lesevorgang pro Request waere ein zweiter, auf jedem Pfad, fuer eine Antwort, die sich fast nie aendert.

**Der Preis:** Eine Wertaenderung wirkt erst nach `occ app_api:app:disable mcp_connector` und `occ app_api:app:enable mcp_connector`. Der Preis ist an drei Stellen benannt: in der Beschreibung des Formularfeldes (05-01), im Setup-Hinweis auf `/connections` (`SETUP_PUBLIC_URL_BODY`) und in `docs/oauth-setup.md`, Abschnitt 3. Ein Test haelt die Einmaligkeit fest (`test_the_admin_values_are_read_once_per_start_and_never_per_request`), damit ein spaeterer "Komfort"-Refactor die Entscheidung nicht still umdreht.

## Threat Flags

Der Threat-Register des Plans, Ist-Zustand nach diesem Plan:

| Threat ID | Kategorie | Disposition | Ist-Zustand |
|-----------|-----------|-------------|-------------|
| T-05-17 | Spoofing, Tampering | mitigate | **Umgesetzt.** `main` uebernimmt ausschliesslich, was `admin_overlay` ausgeliefert hat; die Validierung aus 05-01 wird nicht umgangen und nicht wiederholt. Drei Negativfaelle (ohne Schema, mit Fragment, mit `user:pass@`) belegen, dass die Deploy-Env dann in Kraft bleibt. |
| T-05-18 | Tampering | mitigate | **Bewusst nicht implementiert, dokumentiert.** Keine Herleitung aus `NEXTCLOUD_URL` (Assumption A2). Der Verzicht steht als Kommentar an der Fehlerzeile in `entry_exapp.main`; `grep -n NEXTCLOUD_URL src/mcp_connector/entry_exapp.py` findet zwei Treffer, den Modul-Docstring und genau diesen Kommentar, also keine Verwendung des Wertes. |
| T-05-19 | Elevation of Privilege | mitigate | **Umgesetzt, wie geplant.** Die Schalter sind ohne Env erreichbar (Security Domain V14), der Sicherheitshinweis steht am Feld (05-01) und jetzt zusaetzlich in `docs/oauth-setup.md` Abschnitt 3, und die unfertige Installation ist auf `/connections` sichtbar. |
| T-05-20 | Denial of Service | mitigate | **Umgesetzt.** Eigener kurzlebiger Client mit den Timeouts von `shared_client`, ein Versuch, Fehler ergibt leeres Overlay; `test_an_unreachable_nextcloud_does_not_stop_the_start` belegt den Start bei Transportfehler. |
| T-05-21 | Information Disclosure | mitigate | **Umgesetzt.** Die INFO-Zeile nennt nur Schluesselnamen (Test prueft Adresse und Client-Liste als abwesend), der Setup-Hinweis nennt nur den Ort der Einstellung (Copy-Test prueft `DEFAULT_PUBLIC_URL` und `127.0.0.1` als abwesend). Der Kopfbereich der Seite zeigt weiterhin den konfigurierten Host, also im Setup-Zustand den dokumentierten Loopback-Default; das ist der bestehende, gewollte Absender-Hinweis aus T-03-02 und kein neuer Abfluss. |
| T-05-SC | Tampering | accept | **Unveraendert.** Kein Paket installiert, `git diff --stat uv.lock` leer. |

Kein neuer Threat-Flag: dieser Plan legt keine Route an, keinen Auth-Pfad, keinen Dateizugriff und keine Schema-Aenderung. Der Setup-Hinweis erscheint auf einer bereits vorhandenen PUBLIC-Route, und der Startzeit-Lesevorgang benutzt den Kanal, den 05-01 gebaut und getestet hat.

## Known Stubs

Keine. Der Vertragspartner aus 05-01 ist verdrahtet: die gelesenen Werte wirken.

## Requirements

**EXAPP-04 bleibt Pending**, dieselbe Linie wie in 05-01 und aus demselben Grund: EXAPP-04 ist die Store-Einreichung selbst (Zertifikat via CSR-PR, Signatur, `info.xml`-Validierung, Datenweitergabe-Disclosure). Dieser Plan liefert die zweite Haelfte der Ein-Klick-Tauglichkeit, also eine Voraussetzung der Einreichung. `.planning/REQUIREMENTS.md` bleibt unveraendert; der Haken gehoert an den Plan, der einreicht.

## Issues Encountered

- Die Reihenfolge im `main`-Rumpf ist enger als sie aussieht: der Lesevorgang muss nach der Ablehnung eines zweiten Credential-Kanals stehen (ein misskonfigurierter Prozess darf keinen Socket oeffnen) und vor allen Pruefungen (die Pruefungen sollen die Werte beurteilen, die auch benutzt werden). Als Kommentar an der Stelle festgehalten.
- Der Test "eine gesetzte Adresse ergibt eine zeichengleiche Seite" laesst sich nicht als Snapshot fuehren, weil jede Antwort einen neuen CSP-Nonce traegt. Er ist deshalb als Aussage ueber Callouts formuliert: die Access-on-Seite ohne Pause hat null Callouts, die Setup-Seite genau einen mit `callout-warning`.

## User Setup Required

Keines fuer diesen Plan. Auf einer laufenden Instanz sind die Schritte: Wert im Admin-Formular setzen, App deaktivieren und aktivieren, `/connections` neu laden. Der Live-Blick auf den gerenderten Setup-Hinweis und auf das gerenderte Admin-Formular fehlt weiter (kein Browser war beteiligt, alle Aussagen sind in-process und auf dem Draht belegt); dieser Punkt gehoert zur Phase-5-Verifikation, zusammen mit dem offenen Punkt aus 05-01 und dem `/settings/user/security`-Blick aus Phase 4.

## Next Phase Readiness

- **BL-06 ist mit 05-01 und 05-04 geschlossen.** Die Werte entstehen in Nextcloud (05-01) und wirken im Prozess (05-04); ein Admin kann eine per Klick installierte App vollstaendig konfigurieren, und eine noch nicht konfigurierte Installation sagt sichtbar, was fehlt. Fuer die BACKLOG-Pflege: BL-06 auf geschlossen setzen, mit Verweis auf diese zwei Plaene.
- **Fuer 05-06 (Store-Einreichung):** `appinfo/info.xml` ist unberuehrt, es gibt keine neue Route und keine neue Variable. Der Satz fuer die Store-Beschreibung kann jetzt lauten, dass die oeffentliche Adresse in den Administrationseinstellungen gesetzt wird, nicht mehr per `--env`.
- **Offen fuer 05-05 oder die Phasen-Verifikation:** Ein Lauf gegen die HaRP-Topologie, der die drei Aussagen live zeigt (Start ohne `NC_MCP_PUBLIC_URL` bleibt `enabled`, Wert im Formular setzen, nach dem Wiederaktivieren traegt `/.well-known/oauth-protected-resource/mcp` die neue Adresse).

## Self-Check: PASSED

- `src/mcp_connector/entry_exapp.py`, `src/mcp_connector/exapp/config_values.py`, `src/mcp_connector/exapp/ui/connections.py`, `docs/oauth-setup.md` und die drei Testdateien liegen geaendert auf der Platte.
- Alle fuenf Commits (`84abaaa`, `1ebd05c`, `7edd193`, `62d0a13`, `201e2b4`) sind im Log.
- Volle Suite 1697 gruen, alle Gates gruen.

---
*Phase: 05-hardening-und-store-einreichung*
*Completed: 2026-08-19*
