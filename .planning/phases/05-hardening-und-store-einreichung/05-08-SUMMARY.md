---
phase: 05-hardening-und-store-einreichung
plan: 08
subsystem: exapp
tags: [uninstall, install, occ-command, appapi, app-passwords, evidence, aio, descope]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 06
    provides: "occ mcp_connector:purge mit der erzwungenen Reihenfolge, store.all_authorizations, store.wipe_all, crypto.delete_key, die Loeschzusage in docs/privacy.md"
  - phase: 05-hardening-und-store-einreichung
    plan: 04
    provides: "der sichtbare Setup-Zustand statt Exit 2 bei fehlender oeffentlicher Adresse, gegen den die veroeffentlichte 0.1.0 gemessen wurde"
  - phase: 05-hardening-und-store-einreichung
    plan: 03
    provides: "die Fixture des Bootstraps (read-only geteilter Ordner plus ungeteilte Datei), die mit demselben Suffix neu entstand"
  - phase: 02-exapp-shell
    plan: 07
    provides: "docs/exapp-install.md mit dem AIO-Abschnitt und den offenen Schritten aus D-31"
  - phase: 03-oauth-2-1
    provides: "scripts/oauth_flow_check.py, dessen Client-Haelfte die Zaehlbasis erzeugt hat"
provides:
  - "docs/uninstall.md: das Runbook mit erzwungener Reihenfolge, Versionstabelle 32/33/34, acht Pruefungen fuer Linie A und elf fuer Linie B"
  - "Assumption A5 geschlossen: Aufrufweg und Draht-Form der occ-Option live gemessen"
  - "exapp/purge.py: _forced_in kennt die occ-Huelle, die AppAPI wirklich sendet"
  - "oauth/crypto.py: delete_key sendet configKeys als Liste und liest 404 als Erfolg"
  - "docs/exapp-install.md: der Descope des AIO-Smokes (D-31) und die NC-34-Stolperstelle"
  - "05-08-MEASUREMENTS.md: Linie 0, Linie A und Linie B mit jeder Ausgabe und Datum"
affects: [05-10, store-einreichung, docs/privacy.md, docs/faq.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Assumption ueber eine Draht-Form wird gegen die laufende Gegenseite gemessen, nicht gegen ihren Quelltext: beide Fehler dieses Plans standen im Quelltext genau so, wie er gelesen wurde, und trugen trotzdem nicht"
    - "Wenn der Knopf fehlt, wird der Code-Pfad gemessen, den der Knopf aufrufen wuerde, und die Gleichheit mit Datei und Zeilennummer belegt"
    - "Ein Beweis, dass ein Credential wirklich zurueckgegeben wurde, braucht einen Aufruf mit genau diesem Credential; die Klartexte leben ausserhalb des Repositories und nur Statuscodes werden gedruckt"
    - "Eine Zaehlbasis vor dem Eingriff macht 'es ist weg' erst pruefbar: zwei Verbindungen, sieben Tabellenzahlen, zwei belegte Identitaeten"

key-files:
  created:
    - docs/uninstall.md
    - .planning/phases/05-hardening-und-store-einreichung/05-08-MEASUREMENTS.md
  modified:
    - src/mcp_connector/exapp/purge.py
    - src/mcp_connector/oauth/crypto.py
    - tests/unit/test_exapp_purge.py
    - tests/unit/test_oauth_crypto.py
    - docs/exapp-install.md
    - docs/privacy.md
    - .planning/phases/05-hardening-und-store-einreichung/deferred-items.md

key-decisions:
  - "Die Zaehlbasis entstand vor dem Install-Klick und ueberlebte ihn im Volume: ein unregister ohne --rm-data behaelt Volume und Datenschluessel, also konnte derselbe Datenstand erst der Store-Version und dann dem heutigen Stand untergeschoben werden, statt zwischen zwei Checkpoints eine zweite Zaehlbasis zu bauen"
  - "Assumption A5 wurde in Task 1 bis zum Ende gefahren, inklusive eines Purge-Laufs mit --force, statt sie fuer Linie B aufzusparen: ein Purge, der erst nach dem Remove-Klick als kaputt auffaellt, haette den Beweislauf mit einem Menschen im Wartezustand blockiert"
  - "Linie A wurde ueber occ app_api:app:disable gemessen, weil Nextcloud 34.0.2 keinen Remove-Knopf fuer ExApps hat; die Gleichheit ist aus dem Quelltext der Instanz belegt (ExAppsPageController.php:383 und Command/ExApp/Disable.php:46 rufen dieselbe Methode)"
  - "crypto.delete_key liest 404 dieser Route als Erfolg: die Route antwortet so, wenn sie null Zeilen geloescht hat, und das ist der Zustand, den der Aufrufer wollte; ein False haette den Admin nach einem Wert suchen lassen, den es nicht gibt"
  - "Der Fund zum 401 beim Lesen der Admin-Werte ging in deferred-items.md statt in einen Fix: er gehoert zum Feature von 05-01/05-04 und braucht eine eigene Ursachenanalyse, waehrend die zwei gefixten Fehler im Purge-Pfad und damit im Gegenstand dieses Plans lagen"
  - "Der AIO-Smoke bleibt descopte Zeile mit genannter Voraussetzung, nicht 'erledigt' und nicht stillschweigend weg: die Voraussetzung ist eine Host-Eigenschaft und keine Code-Eigenschaft"

patterns-established:
  - "Ein Runbook, dessen Reihenfolge Daten unwiderruflich unbrauchbar machen kann, nennt die Falschreihenfolge als Warnblock und belegt ihre Folge mit einem echten Nebenbefund"
  - "Ein Messprotokoll nennt bei jeder Zahl das Kommando, das sie ausgegeben hat, und bei jeder Aequivalenz die Datei und die Zeile"

requirements-completed: []  # EXAPP-04 bleibt Pending, siehe Abschnitt "Requirements"

# Metrics
duration: 60min
completed: 2026-08-19
---

# Phase 05 Plan 08: Installation per Klick und Deinstallation mit Beweis Summary

**Erfolgskriterium 2 ist in beiden Richtungen belegt: nach dem Entfernen ueber die Oberflaeche antworten zwei Nextcloud-Konten weiter mit 200 auf App-Passwoerter dieser App, waehrend Volume, Zeilen, Datenschluessel, Container und Registrierung unveraendert daliegen; nach `occ mcp_connector:purge --force` und `occ app_api:app:unregister --rm-data` antwortet jedes dieser Passwoerter mit 401 und keine der elf Gegenproben findet noch etwas.**

## Performance

- **Duration:** 60 min (inklusive Checkpoint-Runde im Browser)
- **Started:** 2026-08-19T19:29:27Z
- **Completed:** 2026-08-19T20:25:00Z
- **Tasks:** 3 von 3
- **Files modified:** 9 (2 neu, 7 geaendert)

## Accomplishments

- **Assumption A5 ist geschlossen, und das Schliessen hat zwei echte Fehler gefunden.** Das occ-Kommando steht in `occ list` einer laufenden Instanz und laeuft dort. Aber `occ mcp_connector:purge --force` antwortete live mit `purged: false`: AppAPI verpackt eine Option in `{"occ": {"arguments": ..., "options": {"force": true}}}`, und keine der acht akzeptierten Formen kannte diese Huelle. Danach lief der Purge, meldete aber `key_deleted: false`: der Loesch-Zweig der ExApp-Konfiguration nimmt `configKeys` als Liste, nicht `configKey`. Beide Fehler waren aus dem Quelltext nicht sichtbar, weil der Quelltext genau so gelesen worden war, wie er dasteht.
- **Beide Fehler waren fail-closed, und das war der einzige Grund, warum sie harmlos blieben.** Ein Purge, der nichts tut, schickt einen Admin mit falscher Sicherheit in die Deinstallation; die Doppelsicherung von 05-06 hat verhindert, dass er stattdessen ungefragt loescht.
- **Linie A hat acht Messungen, und die sechste ist der Kern.** Nach dem Remove-Pfad liegt das Volume da, sind alle sieben Tabellenzahlen unveraendert, ist die App weiter registriert (`[disabled]`), existiert der Container weiter (`Exited (0)`), steht der Datenschluessel weiter in `oc_appconfig_ex` (324 Bytes, sensitive=1), stehen beide Eintraege `MCP Connector: ...` in den Geraetelisten, und **beide App-Passwoerter antworten mit `HTTP 200, OCS 200` und der richtigen Identitaet**.
- **Ein Befund, den kein Plan vorhergesehen hat:** mit dem Deaktivieren verschwindet das Kommando, das aufraeumen koennte (`occ list | grep -c mcp_connector` gleich 0). Wer erst entfernt, muss die App wieder aktivieren, bevor er aufraeumen kann. Das ist jetzt Schritt 0 des Runbooks.
- **Linie B hat elf Gegenproben und keine offene.** `{"purged":true,"connections":2,"revoked":2,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}`, danach 401 je Passwort, sieben leere Tabellen, keine Config-Zeile, kein Geraeteeintrag; nach `--rm-data` kein Volume, keine Registrierung, kein Container, keine `oc_ex_apps`-Zeile, kein occ-Eintrag. Uebrig bleibt genau eine Zeile: das gezogene Image im Image-Store des Docker-Daemons, 330 MB, ohne Instanzdaten.
- **Nextcloud 34.0.2 hat gar keine Oberflaeche fuer ExApps.** Kein einziges ExApp erscheint in der Liste, auch `context_agent` und `visionatrix` nicht, waehrend das AppAPI-Backend korrekt `canInstall: true` antwortet. Die neue App `appstore` 1.0.0 fuellt ihre Liste allein aus dem Core-AppFetcher und setzt das Merkmal hart auf false; die `initialize`-Funktion ihres External-Apps-Stores kommt im Bundle genau einmal vor, in ihrer Definition. Die alte AppAPI-Seite antwortet 500, weil ihre Methode entfernt wurde und die Route blieb.
- **Die veroeffentlichte 0.1.0 ist per Klick nicht installierbar, gemessen statt vermutet.** Der Aufruf, den der Install-Knopf machen wuerde, endete nach 106,5 Sekunden mit 500, der Container lief mit `RestartCount=12`, `ExitCode=2` in einer Schleife, und im Log steht die Zeile, die 05-01 und 05-04 abgeschafft haben: `NC_MCP_PUBLIC_URL is not set`. Das ist Pitfall 2 der Recherche als Laufzeitbild und das staerkste Argument fuer Release 0.1.1 in 05-10.
- **Der AIO-Punkt aus D-31 ist entschieden und nicht vergessen:** descopte Zeile mit genannter Voraussetzung, die sechs offenen Schritte bleiben unveraendert stehen, kein beschoenigender Satz.
- **`docs/uninstall.md` existiert und schliesst drei offene Verweise:** zweimal aus `docs/faq.md`, einmal aus `docs/privacy.md`. Volle Suite 1776 gruen, alle Gates gruen, `uv.lock` unberuehrt.

## Task Commits

1. **Task 1: Frische Instanz, Installation, Zaehlbasis** - `505eaba` (fix: die occ-Huelle), `872cb0b` (fix: configKeys als Liste), `e90cfd2` (das Messprotokoll der Grundlage plus deferred-items)
2. **Task 2: Der Klick, der installiert, und der Klick, der entfernt** - Checkpoint, im Browser gefahren; das Ergebnis ist Abschnitt 9 des Messprotokolls, kein eigener Commit
3. **Task 3: Beide Linien messen und docs/uninstall.md daraus schreiben** - `2a51a9f`

## Files Created/Modified

- `docs/uninstall.md` (neu, 283 Zeilen) - Ueberblick mit dem einen Satz, der die Seite noetig macht; die erzwungene Reihenfolge mit Warnblock und Schritt 0; die Versionstabelle 32/33/34 samt dem NC-34-Befund im Detail; Linie A mit acht kopierbaren Pruefungen und ihren echten Ausgaben; Linie B mit der Feldtabelle der Purge-Antwort, vier Gegenproben und fuenf nach `--rm-data`; sechs Known pitfalls (Falschreihenfolge, deaktivierte App, Weiterarbeiten nach dem Purge, die falsche Tabelle fuer den Schluessel, die fehlende Oberflaeche, `HP_SHARED_KEY`); Security notes; Related auf `exapp-install.md`, `privacy.md`, `oauth-setup.md`, `faq.md`.
- `.planning/phases/05-hardening-und-store-einreichung/05-08-MEASUREMENTS.md` (neu, 11 Abschnitte) - jede Ausgabe dieses Laufs mit Kommando und Uhrzeit, inklusive der Fehlersuche in AppAPI und der Linie 0.
- `src/mcp_connector/exapp/purge.py` - `OCC_ENVELOPE` mit der gemessenen Herkunft im Kommentar; `_forced_in` steigt genau eine Ebene in die Huelle und behaelt jede bisherige Form; der Docstring von `_forced` nennt jetzt die Messung statt der Annahme.
- `src/mcp_connector/oauth/crypto.py` - `delete_key` sendet `{"configKeys": [CONFIG_KEY]}` und liest 404 als Erfolg mit einer Info-Zeile; der Docstring nennt die Signatur des Controllers und das Fehlbild, das ohne diese Zeile entstand.
- `tests/unit/test_exapp_purge.py` - zwei neue Positivformen (die gemessene Huelle mit und ohne `arguments`) und drei neue Negativformen (Huelle mit Flag false, ohne Optionen, Huelle die kein Objekt ist).
- `tests/unit/test_oauth_crypto.py` - die Form-Assertion auf `configKeys`, die Refusal-Parametrisierung ohne 404, und ein eigener Test fuer 404 gleich True ohne Error-Zeile.
- `docs/exapp-install.md` - der AIO-Abschnitt traegt die Descope-Entscheidung mit ihrer Voraussetzung; neuer Abschnitt "Nextcloud 34 has no interface for installing or removing an ExApp" mit der Ursachenkette und dem gemessenen Crash-Loop der Store-Version.
- `docs/privacy.md` - der Satz ueber den Remove-Knopf behauptet keinen Knopf mehr, den diese Version nicht hat (siehe Deviation 3).
- `.planning/phases/05-hardening-und-store-einreichung/deferred-items.md` - der 401 beim Lesen der Admin-Werte.

## Verification

| Gate | Ergebnis |
|------|----------|
| `pytest` (volle Suite) | 1776 passed, 92 deselected |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 166 files already formatted |
| `pyright` | 0 errors, 0 warnings |
| `vulture src scripts vulture_whitelist.py` | leer |
| `python scripts/check_tool_budget.py` | Exit 0 |
| `test -f docs/uninstall.md` | vorhanden |
| `grep -c 'mcp_connector:purge' docs/uninstall.md` | 3 |
| `grep -c 'app_api:app:unregister' docs/uninstall.md` | 3 |
| `grep -c '—' docs/uninstall.md` | 0 (en dash ebenfalls 0) |
| Emoji- und Nicht-ASCII-Scan `docs/uninstall.md` | keine Treffer |
| `grep -c 'AIO' docs/exapp-install.md` | 16 |
| Vokabular-Gate (`archiv`) in `docs/uninstall.md` | 0 |
| `git diff --stat uv.lock` | leer |

## Messprotokoll Linie A und Linie B

Vollstaendig in `05-08-MEASUREMENTS.md`, Abschnitte 9 bis 11. Die Kurzform, jede Zeile mit
ihrem Kommando im Protokoll:

**Zaehlbasis (19:47Z bis 19:49Z).** Zwei Verbindungen ueber die volle Kette, je eine fuer
`alice` und `bob`. `access_tokens 2, auth_codes 2, authorizations 2, clients 2, flows 0,
refresh_tokens 2, user_access 0`. Zwei App-Passwoerter `MCP Connector: Count base one/two`
(Ids 18 und 20), beide `HTTP 200, OCS 200` mit belegter Identitaet. Datenschluessel
`oauth_data_key`, 324 Bytes, `sensitive=1`. Container healthy, Registrierung `[enabled]`,
`deploy 100`, `init 100`.

**Linie 0 (20:00Z bis 20:12Z, Browser).** Kein ExApp in der Oberflaeche, `exappCount=0`;
der Install-Aufruf endete mit 500 nach 106,5 s; der Container der Store-Version lief in einer
Restart-Schleife mit `ExitCode=2` und der Log-Zeile `NC_MCP_PUBLIC_URL is not set`; keine
Zeile in `oc_ex_apps`. Die Zaehlbasis im Volume blieb unberuehrt.

**Linie A (20:14:16Z).** Ueber `occ app_api:app:disable`, weil kein Knopf existiert, und die
Gleichheit steht in `ExAppsPageController.php:383` gegen `Command/ExApp/Disable.php:46`.
Volume da; alle sieben Zahlen unveraendert; `[disabled]`, aber registriert; Container
`Exited (0)`; Datenschluessel da; **beide App-Passwoerter 200 mit richtiger Identitaet**;
beide Geraeteeintraege da; `occ list` kennt `mcp_connector` nicht mehr.

**Linie B (20:14:43Z bis 20:15:33Z).** Schritt 0 `app:enable` (Kommando ist wieder da,
Zaehlbasis unveraendert, Passwoerter weiter 200). Schritt 1
`{"purged":true,"connections":2,"revoked":2,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}`,
danach 401 je Passwort, sieben Nullen, keine Config-Zeile, null Geraeteeintraege. Schritt 2
`--rm-data`: kein Volume, keine Registrierung, kein Container, keine `oc_ex_apps`-Zeile,
`occ user:setting alice` ohne Praefix-Zeile, `occ list` ohne Eintrag. Uebrig: die zwei
Images (330 MB je), ohne Instanzdaten.

## Descope AIO (D-31)

**Entschieden: bewusst descopte Zeile der Phasen-Verifikation, nicht erledigt und nicht
stillschweigend weggelassen.**

Die fehlende Voraussetzung ist eine Host-Eigenschaft: eine oeffentlich aufloesbare Domain mit
gueltigem, oeffentlichem TLS-Zertifikat und eingehender Erreichbarkeit auf 80 und 443. Der
AIO-Mastercontainer prueft das, bevor er irgendeinen Container startet, in den eine ExApp
installiert werden koennte. Der zweite Grund aus Phase 2 gilt weiter: der Mastercontainer
steuert den Docker-Daemon, auf dem die taeglich genutzte Owner-Instanz laeuft.

Die sechs offenen Schritte stehen unveraendert in `docs/exapp-install.md`, Abschnitt
Nextcloud AIO, inklusive der unverifizierten Annahme A6 in Schritt 3. Der Abschnitt sagt
ausdruecklich, dass kein Teil dieses Projekts AIO-Abdeckung behauptet und keine Messung auf
AIO entstanden ist.

## Decisions Made

Vollstaendig im Frontmatter (`key-decisions`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `--force` erreichte den Handler nicht (Assumption A5, Punkt 2)**

- **Found during:** Task 1
- **Issue:** `occ mcp_connector:purge --force` antwortete auf der laufenden Instanz mit `{"purged":false,...}`. AppAPI schickt eine occ-Option als `{"occ": {"arguments": null, "options": {"force": true}}}` (`ExAppOccService::buildCommand` baut das Paar, `AppAPIService::prepareRequestToExApp` macht daraus `options['json']` eines POST). `_forced_in` kannte acht Formen, aber keine mit dieser Huelle. Genau das Fehlbild, das 05-06 als Risiko benannt hatte: der Admin deinstalliert im Glauben, die Credentials seien zurueckgegeben.
- **Fix:** `_forced_in` steigt genau eine Ebene in die Huelle `occ` hinab (`inside_envelope` begrenzt die Tiefe), alle bisherigen Formen bleiben; die Struktur der Funktion wurde von fruehen Returns auf "erst pruefen, dann weitersuchen" umgestellt, damit die Huelle auch neben anderen Feldern gefunden wird.
- **Files modified:** `src/mcp_connector/exapp/purge.py`, `tests/unit/test_exapp_purge.py` (beide nicht in `files_modified` des Plans)
- **Verification:** zwei neue Positivformen und drei neue Negativformen, vorher rot; live `{"purged":true,"connections":2,"revoked":2,...}`
- **Committed in:** `505eaba`

**2. [Rule 1 - Bug] Der Datenschluessel wurde nicht geloescht (`key_deleted: false`)**

- **Found during:** Task 1
- **Issue:** Nach dem ersten erfolgreichen Purge blieb `oauth_data_key` in `oc_appconfig_ex` stehen, im Container-Log ein 400. `AppConfigController::deleteAppConfigValues(array $configKeys)` hat genau einen Parameter, und der ist eine Liste; ein Rumpf mit `configKey` ist ein fehlendes Argument.
- **Fix:** `{"configKeys": [CONFIG_KEY]}`. Zusaetzlich gilt ein 404 dieser Route jetzt als Erfolg: sie antwortet so, wenn sie null Zeilen geloescht hat, und das ist der Zustand, den der Aufrufer wollte.
- **Files modified:** `src/mcp_connector/oauth/crypto.py`, `tests/unit/test_oauth_crypto.py` (beide nicht in `files_modified` des Plans)
- **Verification:** `test_delete_key_sends_one_delete_that_names_the_config_key`, `test_a_deletion_that_finds_no_key_is_true_and_no_error`; live `key_deleted: true` und `no config row of mcp_connector left`
- **Committed in:** `872cb0b`

**3. [Rule 1 - Bug] `docs/privacy.md` behauptete einen Knopf, den diese Version nicht hat**

- **Found during:** Task 3
- **Issue:** Der Abschnitt "Deletion and user control" sagte "On Nextcloud 34 the Remove button disables the app and stops its container". Auf 34.0.2 gibt es fuer eine ExApp keinen solchen Knopf, und das Akzeptanzkriterium des Plans verlangt ausdruecklich, dass `privacy.md` und `uninstall.md` sich nicht widersprechen.
- **Fix:** Der Satz nennt jetzt, dass die Oberflaeche die App gar nicht anbietet, und beschreibt den Pfad, den sie fuer eine ExApp benutzte, statt einen Knopf.
- **Files modified:** `docs/privacy.md` (nicht in `files_modified` des Plans)
- **Verification:** `grep -c '—\|–' docs/privacy.md` bleibt 0; der Verweis auf das Runbook zeigt jetzt auf eine existierende Datei mit genau diesen Abschnitten
- **Committed in:** `2a51a9f`

### Bewusste Abweichungen im Ablauf

- **Assumption A5 wurde in Task 1 bis zum Ende gefahren, inklusive eines Purge-Laufs mit `--force`.** Der Plan siedelt den Purge in Linie B an. Ein Purge, der erst nach dem Remove-Klick als kaputt aufgefallen waere, haette den Beweislauf mit einem Menschen im Wartezustand blockiert, und beide Fehler lagen genau dort. Preis: die Zaehlbasis musste danach neu gebaut werden, was zwei Wegwerf-App-Passwoerter als Waisen hinterliess (von Hand entfernt, im Protokoll benannt).
- **Die Zaehlbasis entstand vor dem Install-Klick, nicht danach.** Der Plan setzt sie in Task 1, der Remove-Klick in Task 2. Ein `unregister` ohne `--rm-data` behaelt Volume und Datenschluessel, also lag derselbe Datenstand vor dem Klick bereit und die Messung brauchte keine zweite Checkpoint-Runde fuer eine zweite Zaehlbasis.
- **Linie A wurde nicht ueber den Knopf gemessen, weil es keinen gibt.** Gemessen wurde `occ app_api:app:disable`, und die Gleichheit mit der Route des Knopfes ist aus dem Quelltext der Instanz mit Datei und Zeile belegt. Ohne diesen Schritt haette der Plan an einem Frontend-Fehler von Nextcloud 34 aufgehoert, statt seine Frage zu beantworten.
- **Die Volumes der Wegwerf-Topologie wurden bewusst weggeworfen**, obwohl STATE.md sie als aufbewahrt fuehrte: Task 1 verlangt eine Instanz ohne Vorgeschichte. Die Fixture aus 05-03 ist mit demselben in `.env.exapp` festgehaltenen Suffix neu entstanden, also ohne eine zweite Freigabe daneben.
- **`build_store_release.sh` lief, obwohl das Store-Archiv von 0.1.0 bereits veroeffentlicht ist:** der Plan nennt es als Schritt von Variante B, und der Lauf belegt, dass das Artefakt aus dem heutigen Manifest reproduzierbar ist (28763 Bytes, Signatur nicht abgedruckt).

### Nicht gefixt, bewusst

- **Der 401 beim Lesen der Admin-Werte** (`ERROR mcp_connector.exapp.config_values: Nextcloud answered 401 when the admin values were read, the environment stays`, in jedem Containerstart). Folge: ein im Admin-Formular gesetzter Wert wirkt auf dieser Topologie nie. Der Fund gehoert zum Feature von 05-01/05-04, braucht eine eigene Ursachenanalyse (Vermutung: die App ist zur Startzeit noch nicht `enabled`) und steht in `deferred-items.md`.

---

**Total deviations:** 3 (alle Rule 1) plus fuenf Ablauf-Abweichungen und ein zurueckgestellter Fund
**Impact on plan:** Scope-Zuwachs von zwei Quelldateien und ihren Tests, und beide Aenderungen sind der Grund, warum das Runbook dieses Plans ueberhaupt etwas Wahres beschreiben kann.

## Threat Flags

| Threat ID | Kategorie | Disposition | Ist-Zustand |
|-----------|-----------|-------------|-------------|
| T-05-36 | Elevation of Privilege | mitigate | **Umgesetzt und beidseitig belegt.** Vor dem Eingriff antworten beide App-Passwoerter mit `HTTP 200, OCS 200` und der Identitaet ihres Kontos; nach dem Remove-Pfad weiter 200 (das ist der Befund); nach dem Purge `HTTP 401, OCS 997` je Passwort, plus null Eintraege mit dem Praefix in beiden Geraetelisten. Das Runbook erzwingt die Reihenfolge, benennt die Falschreihenfolge als Warnblock und nennt zusaetzlich Schritt 0, ohne den das Kommando gar nicht existiert. |
| T-05-37 | Information Disclosure | mitigate | **Umgesetzt.** Linie A macht den zurueckbleibenden Zustand messbar (Volume da, sieben Zahlen unveraendert, `oauth_data_key` 324 Bytes `sensitive=1`) und `docs/uninstall.md` benennt ihn als Befund samt Pitfall 4 (der Schluessel liegt in `oc_appconfig_ex`, nicht in `oc_appconfig`, und ueberlebt auch `--rm-data`). Linie B belegt den Weg, der beides entfernt. |
| T-05-38 | Spoofing | accept | **Unveraendert, und die Kette ist jetzt gemessen.** Die Instanz laedt das Archiv von unserer Download-URL (200 ueber die Signed-URL von GitHub), der Store liefert die Signatur mit (684 Zeichen), AppAPI prueft sie zur Installationszeit. Der private Schluessel blieb lokal, `build_store_release.sh` hat die Signatur nur ausgegeben und dieses Protokoll druckt sie nicht. Kein weiteres Control in diesem Plan. |
| T-05-39 | Information Disclosure | mitigate | **Umgesetzt.** Kein Credential steht in Doku oder Protokoll. Die Klartexte der App-Passwoerter wurden im App-Container entschluesselt und in eine Datei ausserhalb des Repositories geschrieben, die nie ausgegeben wurde; ausgewertet wurden nur Konto, HTTP-Status, OCS-Status und die von Nextcloud gemeldete Identitaet. Der Datenschluessel erscheint nur als Laenge (324 Bytes), das App-Secret nie, die Store-Signatur nie. |
| T-05-40 | Denial of Service | mitigate | **Umgesetzt.** Alles lief im Compose-Projekt `nc-mcp-exapp`; `docker volume ls` vorher und nachher steht im Protokoll; die Owner-Instanzen `nc-mcp-test` und `findling-nextcloud` liefen die ganze Zeit weiter (`docker ps -a` am Anfang und am Ende) und wurden nicht angefasst. Jeder `occ`-Aufruf ging per `docker exec` an den festen Containernamen der Wegwerf-Instanz. |
| T-05-SC | Tampering | accept | **Unveraendert.** Kein Paket installiert, `git diff --stat uv.lock` leer. |

Zwei neue Flags ueber die Liste des Plans hinaus, beide ohne neue Angriffsflaeche in diesem
Repository, aber beide relevant fuer das Release:

| Flag | Datei | Beschreibung |
|------|-------|--------------|
| threat_flag: availability | `appinfo/info.xml` (Release 0.1.0) | Die veroeffentlichte Version beendet sich bei einer Ein-Klick-Installation mit Exit 2, weil `NC_MCP_PUBLIC_URL` auf diesem Pfad nie gesetzt wird. Sie ist damit fuer jeden Store-Installateur unbenutzbar, und der Fix liegt seit 05-01/05-04 im Code. Gegenstand von 05-10. |
| threat_flag: upstream | Nextcloud 34.0.2, App `appstore` 1.0.0 | Kein ExApp erscheint in der Verwaltungsoberflaeche, also gibt es fuer diese Klasse von Apps weder Install- noch Remove-Knopf. Kein Sicherheitsloch dieses Projekts, aber eine Aussage der Recherche ("der Remove-Knopf deaktiviert nur") gilt auf dieser Version nur noch fuer den Code-Pfad, nicht fuer einen Knopf. Kandidat fuer einen Upstream-Bericht. |

## Known Stubs

Keine. `docs/uninstall.md` enthaelt keine Platzhalterzahl und keinen unbelegten Abschnitt:
jede Zahl in Linie A und Linie B stammt aus dem Lauf vom 19.08.2026, und die zwei
Kommando-Bloecke sind kopierbar.

## Requirements

**EXAPP-04 bleibt Pending**, dieselbe Linie wie in 05-01, 05-04 und 05-06: EXAPP-04 ist die
Store-Einreichung selbst. Dieser Plan liefert zwei ihrer Voraussetzungen (ein Runbook, das
haelt, was es sagt, und einen Purge, der ueberhaupt laeuft) und einen harten Grund, warum die
naechste Einreichung nicht optional ist: die aktuell gelistete Version ist per Klick nicht
installierbar. `.planning/REQUIREMENTS.md` bleibt unveraendert.

## Issues Encountered

- **Der Quelltext las sich richtig und trug trotzdem nicht, zweimal.** Beide Fehler dieses Plans standen genau so im Quelltext von AppAPI, wie 05-06 ihn gelesen hatte, und beide fielen erst im Lauf auf: einmal, weil eine Huelle nicht Teil der gelesenen Stelle war, einmal, weil zwei Haelften derselben Ressource verschiedene Feldnamen nehmen. Das ist der Grund, warum A5 als Assumption markiert war, und die Markierung hat sich bezahlt.
- **Der Purge im laufenden Prozess loest den Schluessel vom Chiffrat.** Nach einem Purge ohne Neustart entstanden Verbindungen, die niemand mehr entschluesseln kann, weil der Prozess den geloeschten Schluessel weiter benutzte. Das ist jetzt Pitfall 3 des Runbooks und der Grund, warum der Purge dort der letzte Schritt vor dem Entfernen ist.
- **Zwei Waisen als Nebenprodukt.** Die verworfene Runde hinterliess zwei App-Passwoerter in Nextcloud, deren Datensaetze mit dem Volume verschwunden waren: genau der Zustand, gegen den das Runbook geschrieben ist, ungeplant hergestellt. Von Hand mit `occ user:auth-tokens:delete` entfernt.
- **Git Bash blieb der bekannte Stolperstein.** `MSYS_NO_PATHCONV=1` ist noetig und macht gleichzeitig `/dev/null` als curl-Ziel unbenutzbar; ein Skript im Scratchpad wird nur mit Windows-Pfad gefunden. Beides wie in 05-03 und 05-05 gelöst.

## User Setup Required

Keines fuer diesen Plan. Fuer den naechsten Lauf auf dieser Topologie gilt der Stand am Ende:
die App ist vollstaendig entfernt (`--rm-data`), die vier Container der Topologie sind
heruntergefahren, die Volumes `nc-mcp-exapp_*` behalten die Fixture aus 05-03. Wieder
anfahren wie in STATE.md beschrieben, `HP_SHARED_KEY` zuruecklesen statt neu erzeugen.

## Next Phase Readiness

- **Fuer 05-10 (Release und CHANGELOG):** dieser Plan liefert die Begruendung und die Belege. Die gelistete 0.1.0 ist per Klick nicht installierbar (Exit 2 ohne `NC_MCP_PUBLIC_URL`) und traegt weder den Purge noch die zwei hier gefundenen Korrekturen. Der CHANGELOG-Eintrag von 0.1.1 kann sich auf Abschnitt 9.2 des Messprotokolls stuetzen; die Installationsanleitung des Release-Textes muss den occ-Weg nennen, weil Nextcloud 34.0.2 keinen Knopf hat.
- **Fuer die Phasen-Verifikation:** SC 2 ist belegt, A5 ist geschlossen, D-31 ist descopte Zeile mit Voraussetzung. Offen bleibt der zurueckgestellte 401-Fund der Admin-Werte.
- **Fuer einen Upstream-Bericht:** die Kette aus Abschnitt 9.1 ist vollstaendig genug fuer ein Issue an Nextcloud (Cache ok, Backend ok, Frontend ruft `initialize` nie, alte Route 500).

## Self-Check: PASSED

- `docs/uninstall.md` (283 Zeilen), `05-08-MEASUREMENTS.md` und `05-08-SUMMARY.md` liegen auf der Platte; `purge.py` traegt `OCC_ENVELOPE` (3 Stellen), `crypto.py` traegt `configKeys` (6 Stellen).
- Alle fuenf Commits (`505eaba`, `872cb0b`, `e90cfd2`, `2a51a9f`, `bc0a6af`) sind im Log.
- Volle Suite 1776 gruen, alle Gates gruen, `uv.lock` unberuehrt, keine Datei geloescht.

---
*Phase: 05-hardening-und-store-einreichung*
*Completed: 2026-08-19*
