---
phase: 05-hardening-und-store-einreichung
plan: 03
subsystem: testing
tags: [permission-parity, exapp-chain, webdav-share, ocs-shares, create-only, bootstrap-fixture]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "die HaRP-Testtopologie samt bootstrap_exapp.sh und test_permission_fidelity_exapp.py (Credential-Regel, _mcp_session, chain_env-Skip)"
  - phase: 01-server-kern
    provides: "files_search, files_list, files_read, files_upload (create-only per If-None-Match) und unified_search"
provides:
  - "scripts/bootstrap_exapp.sh: ensure_readonly_share als idempotente Fixture (Ordner read-only an bob, ungeteilte Zweitdatei), plus nc_status/nc_body/put_marked_file/create_readonly_share/share_is_readonly_for/share_suffix/dav_url"
  - "vier neue Zeilen in .env.exapp: NC_MCP_TEST_SHARED_DIR, NC_MCP_TEST_SHARED_FILE, NC_MCP_TEST_PRIVATE_FILE, NC_MCP_TEST_SHARED_MARKER (relativ zur Nutzerwurzel)"
  - "tests/integration/test_permission_parity_share.py: fuenf Aussagen von SC 3 ueber die volle Kette, jede mit Positivkontrolle, live gemessen"
  - "tests/unit/test_exapp_env_setup.py: share_fixture_problems als Gate ueber den Skripttext plus zehn Gegenproben und ein bash-Lauf ueber share_suffix"
affects: [05-04, 05-06, 05-10, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Asymmetrie in den Daten statt im Vergleich: eine Fixture-Datenlage, die Nextcloud durchsetzt, macht Permission-Parity messbar"
    - "Fixture-Namen ueber die Verbindungsdatei pinnen (wie APP_SECRET), damit ein zweiter Lauf keine zweite Freigabe stapelt"
    - "Gate als problems()-Funktion ueber den Skripttext, gegengeprobt an manipulierten Kopien im Speicher"
    - "Pfade in einer Env-Datei relativ zur Wurzel, weil Git Bash absolute POSIX-Pfade beim Prozessstart umschreibt"

key-files:
  created:
    - tests/integration/test_permission_parity_share.py
    - .planning/phases/05-hardening-und-store-einreichung/05-03-MEASUREMENTS.md
  modified:
    - scripts/bootstrap_exapp.sh
    - tests/unit/test_exapp_env_setup.py
    - .env.exapp.example

key-decisions:
  - "Die Fixture legt ihre Objekte ueber WebDAV und OCS mit alices Kontopasswort an, nicht per docker exec ins Datenverzeichnis: eine dort abgelegte Datei hat bis zum naechsten files:scan keine File-Id, und ein Ordner ohne File-Id ist nicht teilbar"
  - "Die Fixture laeuft vor dem App-Passwort-Block und benutzt deshalb das Kontopasswort statt eines App-Passworts; jedes Geheimnis reist als curl-Config durch stdin (WR-06), nie in der argv"
  - "permissions=1 ist der ganze Beweis: jeder hoehere Wert wuerde die Upload-Ablehnung ihrer Aussage berauben, deshalb pinnt das Unit-Gate diesen Literal und faellt bei jedem anderen Wert"
  - "Die Fixture-Namen tragen einen Suffix, der wie APP_SECRET aus der Verbindungsdatei zurueckgelesen wird: ein frischer Suffix pro Lauf haette die Instanz mit einer zweiten Freigabe hinterlassen"
  - "Die drei Pfade stehen relativ zur Nutzerwurzel in .env.exapp: Git Bash ersetzt beim Start eines nativen Prozesses den fuehrenden Schraegstrich eines exportierten Wertes durch sein Installationsverzeichnis (gemessen), der Test setzt ihn wieder davor"
  - "nc_status haengt den Statuscode an den Rumpf statt ihn nach -o /dev/null zu schreiben: mit dem exportierten MSYS_NO_PATHCONV=1 existiert /dev/null fuer curl.exe nicht, und jede Anfrage endete mit curl-Fehler 23 trotz vollstaendiger Antwort"
  - "Der Marker steht im Namen UND im Inhalt der geteilten Datei: derselbe String traegt die Suchaussage und die Leseaussage, also kann ein leerer Rumpf nicht als gelungener Lesezugriff durchgehen"
  - "Jede der fuenf Aussagen traegt ihre Positivkontrolle im selben Test, die Leak-Aussage zusaetzlich alices Fund derselben Datei: eine leere Antwort ist erst dann eine Grenze, wenn jemand gezeigt hat, dass das Objekt existiert"
  - "Der Test raeumt nichts auf, weil kein Werkzeug dieses Servers loeschen kann; die Wegwerf-Topologie ist der Aufraeummechanismus (down -v)"

patterns-established:
  - "Fixture-Nachweis statt Annahme auch fuer Freigaben: genau eine Freigabe an genau den Empfaenger mit genau permissions=1, plus ein 207 im Home des Empfaengers"
  - "Gegenprobe eines Skript-Gates an einer im Speicher manipulierten Kopie, ein Fall je Art, wie die Fixture aufhoeren wuerde etwas zu beweisen"
  - "Live-Gegenproben im Messprotokoll: ein falsch verdrahteter Aufbau muss rot werden, sonst ist der gruene Lauf keine Messung"

requirements-completed: []  # AUTH-05 und TOOL-09 waren schon Complete; dieser Plan liefert den zweiten, staerkeren Beweis

# Metrics
duration: 25min
completed: 2026-08-19
---

# Phase 05 Plan 03: Permission-Parity und Create-only ueber die volle Kette Summary

Permission-Parity ist von einem Leak-Test zu einer echten Paritaets-Messung geworden: eine
dritte Datenlage im Bootstrap (alice teilt einen Ordner read-only mit bob, eine zweite Datei
bleibt ungeteilt) und fuenf live gemessene Aussagen ueber MCP-Client, HaRP, ExApp,
Impersonation und Nextclouds ACLs.

## Was entstanden ist

**`ensure_readonly_share` im Bootstrap.** Zwischen `ensure_files_home` und dem
App-Passwort-Block legt die Fixture einen Ordner `mcp-share-<suffix>` im Home von alice an, eine
Datei darin, deren Marker im Namen und im Inhalt steht, und eine zweite Datei
`mcp-private-<suffix>.md` ausserhalb, die niemals geteilt wird. Alles ueber WebDAV (MKCOL, PUT
mit `If-None-Match: *`) mit alices Kontopasswort, das als curl-Config durch stdin reist. Danach
`shareapi_auto_accept_share=yes` und die Freigabe ueber die OCS-Share-API mit `shareType=0`,
`shareWith=bob`, `permissions=1`.

Nachweis statt Annahme, in der Bauform von `ensure_calendar`: die Fixture gilt erst als fertig,
wenn `GET .../shares?path=<ordner>` genau eine Freigabe an genau bob mit `permissions` gleich 1
listet **und** ein PROPFIND als bob auf sein `<ordner>` mit 207 antwortet. Der Suffix wird wie
`APP_SECRET` aus `.env.exapp` zurueckgelesen, also ist ein zweiter Lauf ein No-op (live
gemessen: dreimal hintereinander, "already there" und "present (attempt 1)").

**Vier neue Env-Zeilen** (`NC_MCP_TEST_SHARED_DIR`, `NC_MCP_TEST_SHARED_FILE`,
`NC_MCP_TEST_PRIVATE_FILE`, `NC_MCP_TEST_SHARED_MARKER`), relativ zur Nutzerwurzel, plus
dieselben Namen in `.env.exapp.example`.

**`tests/integration/test_permission_parity_share.py`** mit fuenf Tests, je einer pro Aussage:

| # | Aussage | Positivkontrolle im selben Test |
|---|---------|---------------------------------|
| 1 | bob findet die geteilte Datei ueber `files_search` UND `unified_search` | der Fund selbst (bob besitzt hier nichts) |
| 2 | bob findet die ungeteilte Datei ueber keinen der beiden Wege | alice findet dieselbe Datei, und bobs Suche antwortet fuer den geteilten Marker |
| 3 | bob liest die geteilte Datei und bekommt die Inhaltsmarkierung | der gelungene Lesezugriff mit geprueftem Inhalt |
| 4 | bob kann nicht in den read-only geteilten Ordner hochladen | derselbe `files_upload`-Aufruf in bobs eigene Wurzel gelingt |
| 5 | alices zweiter Upload auf denselben Pfad wird abgelehnt | der erste Upload gelingt, und der Inhalt ist danach unveraendert |

**Ein Unit-Gate ohne Docker** (`share_fixture_problems` in `tests/unit/test_exapp_env_setup.py`)
prueft die Fixture am Skripttext: Funktion vorhanden, im Hauptteil vor dem App-Passwort-Block
aufgerufen, `permissions=1` und nichts anderes, `shareType=0`, beide OCS-Header, Auto-Accept,
beide Nachweise im Funktionskoerper, die vier Env-Namen im Heredoc und keiner davon absolut.
Zehn Gegenproben an im Speicher manipulierten Kopien belegen, dass das Gate ausloest, und zwei
bash-Laeufe messen `share_suffix` in beiden Schreibweisen.

## Messprotokoll

Vollstaendige Rohmessungen mit allen Befehlen und Antworten:
`.planning/phases/05-hardening-und-store-einreichung/05-03-MEASUREMENTS.md`. Kurzfassung, alles
am **19.08.2026** gegen `compose.exapp.yml` (Nextcloud 34, AppAPI/HaRP):

| Zeit (UTC) | Befehl | Ergebnis |
|-----------|--------|----------|
| 15:51:56 | `pytest tests/integration/test_permission_parity_share.py -q -m integration` (ohne `.env.exapp`) | `sssss`, fuenf Skips, Exit 0 |
| 15:52:24 | `export HP_SHARED_KEY=$(openssl rand -hex 32) && docker compose -f compose.exapp.yml up -d --wait` | vier Container healthy, Exit 0 |
| 15:52:5x | `occ app_api:app:unregister mcp_connector --silent --force`, `occ app_api:daemon:unregister harp_proxy_docker` | Daemon abgemeldet, `ExApps:` leer |
| 15:53:06 | `bash scripts/bootstrap_exapp.sh` | Fixture angelegt und nachgewiesen, Image neu gebaut, `mcp_connector 0.1.0 [enabled]`, Exit 0 (48 s) |
| 15:56:46 | `bash scripts/bootstrap_exapp.sh` (nach dem curl-Fix, Suffix bewusst invalidiert) | `create answered 200`, `present (attempt 2)`, keine curl-Meldung mehr |
| 15:57:28 / 16:01:04 | `bash scripts/bootstrap_exapp.sh` (unveraendert) | "already there" dreimal, `present (attempt 1)`, gleicher Suffix: idempotent |
| 16:01:31 | `set -a && . ./.env.exapp && set +a` + `pytest tests/integration/test_permission_parity_share.py -m integration` | **5 collected, 5 passed in 2.50s, Exit 0, kein Skip** |
| 16:02:xx | Gegenprobe A: `NC_MCP_TEST_PRIVATE_FILE` auf die geteilte Datei | 5 errors: die Fixture-Wache lehnt den Aufbau ab |
| 16:02:xx | Gegenprobe B: `NC_MCP_TEST_SHARED_MARKER` auf ein Token ohne Objekt | 3 failed, 2 passed: die Greens haengen an den echten Objekten |
| 16:02:54 | zehn Rohaufrufe (A bis J) gegen dieselbe Topologie | siehe unten |

Die entscheidenden Rohantworten:

- **bob in die Freigabe:** `is_error=True ... No permission to write to /mcp-share-<sfx>/probe-...md. Hint: Check the share permissions of the target folder in Nextcloud.`
- **bob in seine eigene Wurzel:** `{"path":"/probe-own-....md","etag":"...","created":true}`
- **alice zweimal derselbe Pfad:** erst `"created":true`, dann `A file already exists at ... Hint: This server never overwrites files. Choose a different name.`
- **bob liest die geteilte Datei:** `"content":"# mcp-shared-file-<sfx> (fixture of scripts/bootstrap_exapp.sh, plan 05-03)"`
- **ungeteilte Datei:** bob `count=0` in `files_search` und `unified_search`, alice `count=1` im selben Lauf.

Nach der Messung wurde die Topologie mit `down` heruntergefahren (Volumes erhalten), der
ExApp-Container und das Netz entfernt. `nc-mcp-test` und `findling-nextcloud` liefen die ganze
Zeit unangetastet weiter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `-o /dev/null` scheitert, weil das Skript MSYS_NO_PATHCONV=1 exportiert**
- **Found during:** Task 2, erster Live-Lauf des Bootstraps
- **Issue:** Jede Anfrage von `nc_status` endete mit `curl: (23) client returned ERROR on write`, obwohl die Antwort vollstaendig ankam. Ursache gemessen: mit `MSYS_NO_PATHCONV=1` (das das Skript fuer die Route-Regexe braucht) reicht Git Bash den Pfad `/dev/null` unveraendert an `curl.exe` weiter, und den gibt es auf Windows nicht. Ein Fehler, der eine erfolgreiche Operation wie einen Fehlschlag aussehen laesst, versteckt beim naechsten Mal einen echten.
- **Fix:** `nc_status` haengt den Status per `-w '\n%{http_code}'` an den Rumpf und liest ihn mit `tail -n1`; kein `-o` mehr. Zusaetzlich meldet `create_readonly_share` jetzt den Statuscode ins Log statt den Rumpf zu verwerfen.
- **Files modified:** scripts/bootstrap_exapp.sh
- **Commit:** 5b9ce5a

**2. [Rule 1 - Bug] Git Bash schreibt absolute Pfade in exportierten Env-Werten um**
- **Found during:** Task 2, erster Live-Lauf der Testdatei (drei Tests rot)
- **Issue:** `set -a && . ./.env.exapp` exportierte `NC_MCP_TEST_SHARED_FILE=/mcp-share-.../...md`; beim Start des nativen pytest-Prozesses ersetzte MSYS den fuehrenden Schraegstrich durch das Git-Bash-Installationsverzeichnis, und `files_read` suchte `/C:/Program Files/Git/mcp-share-.../...md`.
- **Fix:** Die drei Pfade wandern relativ zur Nutzerwurzel in die Verbindungsdatei (`${SHARED_DIR#/}`), der Test setzt den Schraegstrich wieder davor und lehnt eine absolute Schreibweise mit Begruendung ab. Ein neuer Gate-Fall haelt die absolute Form aus dem Heredoc heraus, und `share_suffix` akzeptiert beide Schreibweisen, damit eine Verbindungsdatei aus einem frueheren Lauf ihre Objekte behaelt.
- **Files modified:** scripts/bootstrap_exapp.sh, tests/unit/test_exapp_env_setup.py, tests/integration/test_permission_parity_share.py, .env.exapp.example
- **Commit:** 5b9ce5a

### Zusaetzliche Datei

`.env.exapp.example` stand nicht in `files_modified` des Plans, nennt aber laut eigenem
Kopftext "nur die Variablen" der Verbindungsdatei. Ohne die vier neuen Namen (und ohne den
Hinweis auf die relative Schreibweise) waere die Referenz ab diesem Plan unvollstaendig.

### Bewusste Praezisierung gegenueber dem Plantext

Der Plan nannte die Formulierung "kein `Credentials`-Objekt, kein `httpx.BasicAuth`" fuer den
Modulkopf und gleichzeitig ein Akzeptanzkriterium `grep -c "BasicAuth\|Credentials(" == 0` fuer
dieselbe Datei. Beides zusammen ist nicht erfuellbar, wenn die Regel die verbotenen Namen
woertlich nennt. Der Modulkopf formuliert die Regel deshalb ohne die beiden Bezeichner und
verweist auf das grep-Gate; die Regel selbst ist unveraendert scharf (`grep` liefert 0).

## Requirements

- **AUTH-05** und **TOOL-09** stehen seit Phase 2 bzw. Phase 1 auf Complete. Dieser Plan haengt
  keinen Haken um, sondern liefert den zweiten, staerkeren Beweis: bis 02-06/02-07 war belegt,
  dass bob nichts von alice sieht; jetzt ist zusaetzlich gemessen, dass er genau das sieht, was
  Nextcloud ihm freigibt, und dort trotzdem nicht schreiben kann.
- **SC 3 der Phase** hat damit seinen ersten von zwei Beweisen (Paritaet plus Create-only ueber
  die Kette); der zweite Teil bleibt Sache der weiteren Plaene dieser Phase.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| T-05-12 (mitigate, erfuellt) | tests/integration/test_permission_parity_share.py | Aussage 2 als Leak-Test mit eindeutigem Marker (bob `count=0`, alice `count=1` im selben Lauf); Aussage 4 prueft, dass die Ablehnung den Marker der geteilten Datei nicht traegt |
| T-05-13 (mitigate, erfuellt) | tests/integration/test_permission_parity_share.py | Aussage 4 mit Positivkontrolle: Upload in bobs Wurzel gelingt, in die Freigabe wird er mit "No permission to write" abgelehnt, also entscheidet Nextcloud |
| T-05-14 (mitigate, erfuellt) | tests/integration/test_permission_parity_share.py | Aussage 5 misst die create-only-Grenze (If-None-Match) ueber die volle Kette und liest die Datei danach unveraendert zurueck |
| T-05-15 (mitigate, erfuellt) | tests/integration/test_permission_parity_share.py | Modulkopf-Regel des Analogs uebernommen, kein selbst gebauter Referenzweg; `grep -c "BasicAuth\|Credentials("` ist 0 |
| T-05-16 (mitigate, erfuellt) | scripts/bootstrap_exapp.sh | Nur Compose-Projekt `nc-mcp-exapp` (bestehendes Gate bleibt gruen), eindeutige Namenspraefixe, kein Loeschpfad, Topologie danach heruntergefahren; `nc-mcp-test` und `findling-nextcloud` blieben laufend und unberuehrt |
| T-05-SC (accept) | uv.lock | Keine Installation, `uv.lock` unveraendert |

Kein neues Angriffsflaeche-Flag: die Aenderungen liegen in einem Testskript der
Wegwerf-Topologie und in Testcode, `src/` ist unberuehrt.

## Known Stubs

Keine.

## Offene Punkte

- Auf der Wegwerf-Instanz liegen zwei ungenutzte Fixture-Staende (`mcp-share-4c73cd4efd`,
  `mcp-share-896e373b3f`) samt Freigaben, entstanden aus den beiden Laeufen mit bewusst
  invalidiertem Suffix. Sie tragen keinen aktiven Marker und stoeren keine Messung; kein
  Werkzeug dieses Servers kann loeschen. Wer einen sauberen Stand will:
  `docker compose -f compose.exapp.yml down -v` und danach neu bootstrappen.
- Die Fixture ist auf einem Linux-Host nicht durchgespielt (dieselbe Klasse offener Punkte wie
  WR-12). Die beiden Windows-Befunde oben (`-o /dev/null`, absolute Env-Pfade) sind dort
  wirkungslos, die relative Schreibweise und der angehaengte Statuscode funktionieren auf beiden
  Plattformen.

## Self-Check: PASSED
