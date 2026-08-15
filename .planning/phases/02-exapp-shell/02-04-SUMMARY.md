---
phase: 02-exapp-shell
plan: 04
subsystem: infra
tags: [docker-compose, caddy, harp, appapi, registry, occ, exapp, install, ci]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: "Dockerfile mit non-root-Image, start.sh, healthcheck.sh, appinfo/info.xml mit genau zwei Routen (02-03)"
  - phase: 02-exapp-shell
    provides: "entry_exapp mit Unix-Socket-Betrieb und lifecycle_routes (/heartbeat, /init, /enabled) aus 02-01"
provides:
  - "compose.exapp.yml: zweite, unabhaengige Topologie (Projektname nc-mcp-exapp) aus Caddy, Nextcloud, HaRP und lokaler Registry, ausschliesslich auf 127.0.0.1"
  - "deploy/Caddyfile: /exapps/* zu HaRP, Rest zu Nextcloud, mit 1800s read_timeout fuer Streamable HTTP"
  - "scripts/bootstrap_exapp.sh: idempotente Installation (Nutzer, AppAPI, HaRP-Daemon, Image-Bau und -Push, json-info-Registrierung, --manual-Dev-Loop)"
  - ".env.exapp.example plus git-ignoriertes .env.exapp mit APP_SECRET, HP_SHARED_KEY und NC_MCP_EXAPP_BASE"
  - "docs/exapp-install.md: belegte Installationsanleitung mit sechs gemessenen Nachweisen"
  - "tests/unit/test_exapp_env_setup.py: elf zusaetzliche Dateizusicherungen fuer die Topologie, ohne Docker"
  - "CI-Job exapp: installiert die App gegen einen echten Deploy Daemon und prueft app:list scharf"
affects: [02-05 Permission-Parity gegen die laufende ExApp, 02-06 Discovery-Spike, 02-07 AIO-Nachweis, 05 Store-Einreichung]

# Tech tracking
tech-stack:
  added:
    - "caddy:2 als Reverse-Proxy vor Nextcloud (bildet die AIO-Topologie nach)"
    - "ghcr.io/nextcloud/nextcloud-appapi-harp:release als Deploy Daemon"
    - "registry:2 als Loopback-Registry fuer das unveroeffentlichte ExApp-Image"
  patterns:
    - "Zweites compose-File mit eigenem `name:`, eigenem Volume, eigenem Netz und eigenem Port statt Erweiterung des bestehenden (D-31)"
    - "Der Bootstrap liest den HaRP-Shared-Key aus dem laufenden Container zurueck, statt ihn zu erzeugen: zwei Seiten koennen so nicht auseinanderlaufen"
    - "Die Registrierung ueberschreibt genau drei Felder des Manifests (registry, image, image-tag); info.xml bleibt auf dem Store-Stand"
    - "Compose-Zusicherungen ohne YAML-Abhaengigkeit: ein kleiner Indentation-Parser im Testmodul"

key-files:
  created:
    - compose.exapp.yml
    - deploy/Caddyfile
    - scripts/bootstrap_exapp.sh
    - .env.exapp.example
    - docs/exapp-install.md
  modified:
    - Dockerfile
    - .gitattributes
    - .gitignore
    - tests/unit/test_exapp_env_setup.py
    - .github/workflows/ci.yml

key-decisions:
  - "access_level wandert als Zahl in die json-info-Registrierung, nicht als String: AppAPI mappt PUBLIC/USER/ADMIN nur auf dem info.xml-Pfad, eine json-info-Registrierung schreibt den Wert roh in die Integer-Spalte"
  - "Der ExApp-Port ist 23000: der FRP-Server in HaRP akzeptiert nur 23000 bis 23999, alles andere endet in `port not allowed` und einem 503 ohne Backend"
  - "/certs wird im Image fuer uid 10001 angelegt, weil HaRP das FRP-Client-Zertifikat mit der Identitaet des Containers installiert"
  - "HP_SHARED_KEY hat einen sichtbaren Wegwerf-Default im compose-File (Muster von compose.test.yml), und der Bootstrap liest den effektiv laufenden Wert aus dem Container"
  - "EXAPP-01 wird abgehakt: Container-Backend, Heartbeat, Init auf 100, enabled-Handler und Deploy Daemon sind gegen eine echte Installation belegt"

patterns-established:
  - "Ein Installationsnachweis besteht aus kopierten Kommandos samt Ausgabe und Datum, nicht aus einer Behauptung"
  - "Weicht eine Messung von der Planerwartung ab, steht die Messung in der Doku und die Abweichung wird benannt"

requirements-completed: [EXAPP-01]

# Metrics
duration: 1h 3min
completed: 2026-08-15
---

# Phase 2 Plan 04: HaRP-Testtopologie und echte ExApp-Installation Summary

**Eine zweite, vollstaendig getrennte Compose-Topologie aus Reverse-Proxy, Nextcloud, HaRP und Loopback-Registry, in der die App mit drei Kommandos als ExApp installiert wird: `occ app_api:app:list` meldet `mcp_connector (MCP Connector): 0.1.0 [enabled]`, Deploy und Init stehen beide auf 100, der MCP-Endpunkt wird mit dem App-Passwort eines Nutzers bedient und ohne Auth mit 403 abgewiesen.**

## Performance

- **Duration:** 1h 3min
- **Started:** 2026-08-15T09:17:00Z
- **Completed:** 2026-08-15T10:20:00Z
- **Tasks:** 3
- **Files modified:** 10 (5 neu, 5 geaendert)

## Accomplishments

- `compose.exapp.yml` mit `name: nc-mcp-exapp`: vier Services, eigenes Volume, eigenes Netz (`nc-mcp-exapp-net`, Subnetz 172.29.42.0/24), Caddy auf `127.0.0.1:8081`, Registry auf `127.0.0.1:5000`, HaRP ohne veroeffentlichten Port. Die Instanz aus `compose.test.yml` lief die ganze Zeit weiter und wurde am Ende erneut geprueft (healthy, `status.php` auf 8080 antwortet 200).
- `deploy/Caddyfile` bildet die AIO-Regel nach: `/exapps/*` zu `appapi-harp:8780` mit `read_timeout 1800s`, alles andere zu `nextcloud:80`. Ohne diese Regel scheitert die Installation am Heartbeat, das war im Verlauf mehrfach messbar.
- `scripts/bootstrap_exapp.sh` installiert die App in einem Kommando: Nutzer alice und bob samt Kalender und Adressbuch, Bruteforce-Guard aus, AppAPI, HaRP-Daemon, Image-Bau und Push in die Loopback-Registry, Registrierung per `--json-info` mit festem Secret, Enable-Schritt und ein scharfer Verifikationsblock. Drei Laeufe hintereinander, jeder mit Exit-Code 0.
- Der Installationsnachweis ist echt und steht woertlich in `docs/exapp-install.md`: `app_api:app:list` mit `[enabled]`, `app_api:daemon:list` mit dem HaRP-Daemon, der gesunde Container `nc_app_mcp_connector`, der Statusdatensatz mit `deploy:100` und `init:100`, ein 403 ohne Auth auf `/mcp`, eine bediente MCP-`initialize`-Antwort mit alices App-Passwort und der Nachweis, dass `/heartbeat` von aussen nicht erreichbar ist.
- `tests/unit/test_exapp_env_setup.py` waechst um elf Faelle ohne Docker: CRLF-Verbot fuer die drei neuen Dateien, Loopback-Zusicherung ueber einen kleinen Compose-Parser, eigener Projektname, kein Port auf HaRP, kein `down -v` und kein Verweis auf das andere compose-File im Skript, `/exapps/*`-Regel im Caddyfile.
- CI-Job `exapp` fuehrt genau den dokumentierten Weg aus (up mit `--wait`, Bootstrap, `app_api:app:list` mit `grep` auf `[enabled]`) und kippt bei Fehlschlag die Logs der Topologie und des ExApp-Containers aus. Kein Push nach aussen: `grep -c "docker push\|--push" .github/workflows/ci.yml` bleibt 0.

## Task Commits

1. **Task 1: Compose-Topologie mit Reverse-Proxy, HaRP und lokaler Registry** - `5a5906d` (feat)
2. **Task 2: Idempotenter Bootstrap fuer AppAPI, Daemon und ExApp** - `cd0e520` (feat)
3. **Nachtrag zu Task 2: praeziser Enabled-Check** - `d5c7d38` (fix)
4. **Task 3: Installationsnachweis, Dokumentation und Dateizusicherungen** - `9500cef` (test)

## Files Created/Modified

- `compose.exapp.yml` - vier Services, Kopfkommentar mit den vier Kommandos, WR-06-Begruendung an beiden Portzeilen, `OVERWRITEHOST`/`OVERWRITECLIURL` auf die oeffentliche Adresse, `TRUSTED_PROXIES` und `HP_TRUSTED_PROXY_IPS` auf das eigene Subnetz, `HP_LOG_LEVEL` ueberschreibbar
- `deploy/Caddyfile` - Reverse-Proxy-Regeln mit Herkunftsbegruendung (AIO) und Timeout-Kommentar
- `scripts/bootstrap_exapp.sh` - ensure-Funktionen mit Fehlerausgabe erst im Fehlerfall, `--manual`-Dev-Loop, Verifikationsblock, zwei FALLBACK-Bloecke (App-Store-Zugang, Secret-Verlust)
- `.env.exapp.example` - Variablennamen mit sichtbaren Platzhaltern; `.env.exapp` ist git-ignoriert (`git check-ignore` endet mit 0)
- `docs/exapp-install.md` - Topology, Install, Evidence mit sechs Messungen, Development loop, vier Known pitfalls, Sicherheitsnotizen inklusive des akzeptierten Docker-Socket-Risikos T-02-31
- `Dockerfile` - `/certs` fuer uid 10001 vorab angelegt (siehe Abweichung 1)
- `.gitattributes` - `deploy/Caddyfile text eol=lf`
- `.gitignore` - `.env.exapp` und `.harp-certs/`
- `tests/unit/test_exapp_env_setup.py` - elf neue Faelle plus zwei Hilfsfunktionen (`compose_services`, `published_ports`)
- `.github/workflows/ci.yml` - Job `exapp`

## Decisions Made

- **`access_level` als Zahl.** Das Research nennt String oder Zahl als erlaubt. Am Quellcode geprueft gilt das nur fuer den `info.xml`-Pfad: `ExAppService::getAppInfo` mappt `PUBLIC`/`USER`/`ADMIN` ausschliesslich im XML-Zweig auf 0/1/2, und `ExAppMapper::registerExAppRoutes` schreibt den Wert danach roh in die Integer-Spalte. Die Registrierung traegt deshalb 1 und 0. Der HaRP-Agent hat die Routen im Debug-Log als `AccessLevel.USER: 1` und `AccessLevel.PUBLIC: 0` gemeldet, also ist der Weg belegt.
- **Port 23000 statt 9100.** Der FRP-Server in HaRP erlaubt nur `allowPorts = [{ start = 23000, end = 23999 }]`. Das ist derselbe Bereich, aus dem `ExAppService::getExAppFreePort` waehlt.
- **HP_SHARED_KEY mit sichtbarem Wegwerf-Default.** Der Plan wollte einen erzeugten Schluessel, aber `docker compose config` und `up` laufen vor dem Bootstrap. Ein Default im compose-File ist genau das Muster, das `compose.test.yml` fuer das Admin-Passwort schon verwendet, und der Bootstrap liest den tatsaechlich laufenden Wert per `docker inspect` zurueck, statt zu raten. Wer einen zufaelligen will, exportiert ihn vor dem `up`; der Kommentar im File nennt das Kommando.
- **Der ExApp-Container gehoert nicht zum compose-Projekt.** `down` laesst ihn laufen, weil der Deploy Daemon ihn ueber den Docker-Socket erzeugt hat. Das steht jetzt in der Doku und wurde am Ende von Hand nachgeholt (`docker stop nc_app_mcp_connector`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Non-root-Image ohne beschreibbares `/certs`**
- **Found during:** Task 2 (erste echte Registrierung)
- **Issue:** HaRP installiert das FRP-Client-Zertifikat, indem es Kommandos im laufenden ExApp-Container ausfuehrt, und zwar mit dessen Identitaet. Als uid 10001 scheiterte `mkdir -p /certs/frp` mit `Permission denied`, die Zertifikatsinstallation antwortete 500, `start.sh` fiel auf den Zweig ohne TLS zurueck, der FRP-Server schloss die Verbindung (`connect to server error: EOF`), HAProxy hatte kein Backend und jeder Heartbeat war ein 503. Ohne Fix ist eine Installation mit einem non-root-Image unmoeglich.
- **Fix:** `install -d -o 10001 -g 10001 -m 0700 /certs` im Dockerfile, mit Begruendung und Messdatum im Kommentar.
- **Files modified:** Dockerfile
- **Verification:** Nach dem Neubau meldete das Containerlog `login to server success` und `proxy added: [mcp_connector]`; im HaRP-Log verschwand die Zeile `Failed to create FRP cert dir`.
- **Committed in:** `cd0e520`

**2. [Rule 1 - Bug] Ungueltiges JSON durch doppelte Escape-Ebene**
- **Found during:** Task 2 (erster Bootstrap-Lauf)
- **Issue:** Der Routen-Regex `^/\.well-known/` wurde im unquoted Heredoc als `\.` ausgegeben, und `\.` ist keine gueltige JSON-Escape-Sequenz. AppAPI brach mit `Invalid app info provided in JSON format` ab.
- **Fix:** Vier Backslashes im Heredoc plus ein Kommentar, der beide Escape-Ebenen benennt.
- **Files modified:** scripts/bootstrap_exapp.sh
- **Verification:** `json.load` ueber die erzeugte Zeichenkette laeuft durch; die Registrierung wurde angenommen.
- **Committed in:** `cd0e520`

**3. [Rule 1 - Bug] ExApp-Port ausserhalb des FRP-Bereichs**
- **Found during:** Task 2 (zweiter Lauf)
- **Issue:** Mit dem Beispielport 9100 aus dem Research meldete frpc `start error: port not allowed`, HAProxy hatte kein Backend, und der Heartbeat lief in seinen Zehn-Minuten-Timeout.
- **Fix:** Default 23000 (Dev-Loop 23001) mit Kommentar auf `allowPorts` in der frps-Konfiguration.
- **Files modified:** scripts/bootstrap_exapp.sh
- **Verification:** `netstat` im HaRP-Container zeigt `127.0.0.1:23000 LISTEN 69/frps`; `curl http://127.0.0.1:23000/heartbeat` im Container antwortet 200.
- **Committed in:** `cd0e520`

**4. [Rule 2 - Missing Critical] `HP_LOG_LEVEL` durchreichbar gemacht**
- **Found during:** Task 2 (Fehlersuche am 503)
- **Issue:** Das HaRP-Image setzt `HP_LOG_LEVEL=warning`. Genau die eine Zeile, die sagt, wohin ein Request geroutet wurde (`Rerouting request to ...`), ist INFO und damit unsichtbar. Ohne sie war ein Cache-Problem nicht von einem Konfigurationsproblem zu unterscheiden.
- **Fix:** `HP_LOG_LEVEL: "${HP_LOG_LEVEL:-warning}"` im Service, mit Kommentar.
- **Files modified:** compose.exapp.yml
- **Verification:** `HP_LOG_LEVEL=debug docker compose ... up -d --force-recreate appapi-harp` liefert die Routing-Zeile; ohne die Variable bleibt das Verhalten unveraendert.
- **Committed in:** `cd0e520`

**5. [Rule 1 - Bug] Enabled-Pruefung traf das Ausgabeformat nicht**
- **Found during:** Abschlusspruefung von Task 3
- **Issue:** Das Muster `grep -A5 ... | grep -qi "enabled.*(true|yes|1)"` passt nie auf die tatsaechliche Zeile `mcp_connector (MCP Connector): 0.1.0 [enabled]`. Der Enable-Schritt lief dadurch bei jedem Lauf, statt nur bei fehlendem Flag; die Endpruefung war entsprechend unscharf.
- **Fix:** `grep -q "^mcp_connector .*\[enabled\]"` an beiden Stellen.
- **Files modified:** scripts/bootstrap_exapp.sh
- **Verification:** Dritter Bootstrap-Lauf, Exit-Code 0, Ausgabe `exapp mcp_connector: registered` und `exapp mcp_connector: enabled`.
- **Committed in:** `d5c7d38`

### Abweichungen ohne Rule-Zuordnung (Plan-Text gegen Realitaet)

- **`/heartbeat` von aussen antwortet 502, nicht 404.** Der Plan erwartet 404 aus der Routenlogik. Gemessen wurde ein 502 mit leerem Koerper: HaRP kennt `/heartbeat`, `/init` und `/enabled` als interne Pfade, protokolliert `Only requests from AppAPI allowed to the internal endpoints` und laesst HAProxy die Verbindung ohne Antwort fallen (`silent-drop`), was Caddy dem Client als 502 meldet. Das ist strenger als erwartet, nicht schwaecher: die Anfrage stirbt eine Schicht frueher. Beides ist in `docs/exapp-install.md` so dokumentiert, samt Quellzeile im Agenten.
- **`/mcp` ohne Auth antwortet 403, nicht 401.** Erwartet war eine Ablehnung durch HaRP, gemessen ist es ein 403 aus dem HAProxy-Frontend. Erwartung erfuellt, Statuscode praezisiert.
- **AppAPI liegt im Server-Image.** Pitfall 9 sagt, AppAPI sei nicht im Server-Tarball. `nextcloud:34-apache` bringt `app_api 34.0.0` mit, `occ app:install app_api` meldet `already installed`. Der Fallback-Weg bleibt trotzdem im Skript und in der Doku, weil er fuer aeltere Images und offline-Runner weiterhin gilt.
- **Acceptance-Kriterium `grep -c "127.0.0.1:" == Anzahl ports-Eintraege` ist nicht erfuellbar.** Derselbe Plan verlangt `OVERWRITEHOST` und `OVERWRITECLIURL` auf `127.0.0.1:8081`, und die stehen ebenfalls in der Datei (gemessen: 2 `ports:`-Bloecke, 2 Portzeilen, 5 Zeilen mit `127.0.0.1:`). Geprueft wurde deshalb die gemeinte Zusicherung: jede Portzeile beginnt mit `127.0.0.1:`. Genau das haelt der neue Test `test_the_topology_publishes_on_loopback_only` maschinell fest.
- **Ein Image-Bau-Schritt weniger in der CI.** Der Plan nennt Bau und Push als eigenen CI-Schritt. Das erledigt `bootstrap_exapp.sh` selbst, damit der dokumentierte Weg und der CI-Weg identisch sind. `grep -c "compose.exapp.yml" .github/workflows/ci.yml` ergibt 4, gefordert waren mindestens 3.
- **Elf statt sechs neue Zusicherungen.** Drei Dateien werden parametrisiert auf CRLF und auf Existenz geprueft, dazu die fuenf inhaltlichen Faelle.
- **`uv run --no-sync` weiterhin noetig.** Zwei `nc-mcp.exe`-Prozesse des Owners sperren `.venv/Scripts/nc-mcp.exe`; alle Gates liefen mit `--no-sync`, wie in 02-01 und 02-03 dokumentiert.

---

**Total deviations:** 5 auto-fixed (3 Bugs, 1 Blocking, 1 Missing Critical) plus 7 dokumentierte Textabweichungen.
**Impact on plan:** Kein Scope-Zuwachs. Drei der fuenf Korrekturen waren Voraussetzung dafuer, dass die Installation ueberhaupt gruen wird; eine Zeile im Dockerfile und eine im compose-File kamen dazu.

## Checkpoints

Der Plan enthaelt keine Checkpoints. Im AUTO_MODE waren keine auto-approve-Entscheidungen noetig. Package-Legitimacy: es kam kein neues Python-Paket dazu (`pyproject.toml` und `uv.lock` unveraendert). Die drei neuen Container-Images stammen aus offiziellen Quellen (`caddy:2` und `registry:2` von Docker Official Images, `ghcr.io/nextcloud/nextcloud-appapi-harp:release` aus der Nextcloud-Organisation, genau das Image, das die AppAPI-Doku nennt).

## Verification Log

1. `docker compose -f compose.exapp.yml config --quiet` -> Exit-Code 0.
2. `docker compose -f compose.exapp.yml up -d --wait` -> Exit-Code 0, `ps` meldet `caddy running`, `appapi-harp running`, `nextcloud running`, `registry running`.
3. `curl -sf -o /dev/null -w '%{http_code}' http://127.0.0.1:8081/status.php` -> `200`.
4. `docker compose -f compose.exapp.yml exec -T caddy caddy validate --config /etc/caddy/Caddyfile` -> `Valid configuration`, Exit-Code 0 (unter `MSYS_NO_PATHCONV=1`, sonst verbiegt Git Bash den Pfad).
5. Portzeilen: `- "127.0.0.1:${NC_EXAPP_PORT:-8081}:80"` und `- "127.0.0.1:5000:5000"`, sonst keine; `ports:` kommt zweimal vor.
6. `bash -n scripts/bootstrap_exapp.sh` -> Exit-Code 0. Drei vollstaendige Laeufe, jeder Exit-Code 0; der zweite und dritte sind No-ops bis auf frische App-Passwoerter.
7. `occ app_api:daemon:list` -> `harp_proxy_docker | Harp Proxy (Docker) | docker-install | http | appapi-harp:8780 | http://caddy | Is HaRP yes | appapi-harp:8782`.
8. `occ app_api:app:list` -> `mcp_connector (MCP Connector): 0.1.0 [enabled]`.
9. Statusdatensatz aus `ex_apps`: `enabled=1 | port=23000 | status={"deploy":100,"init":100,"action":"","type":"","error":"", ...}`. Das ist der Beleg fuer den `/init`-Fortschritt und fuer den fehlerfreien Deploy.
10. `docker ps --filter name=mcp_connector` -> `nc_app_mcp_connector Up 3 minutes (healthy)`.
11. `curl -i ... POST /exapps/mcp_connector/mcp` ohne Auth -> `403 Forbidden` (13 Bytes, `text/plain`, aus HaRP).
12. `curl -i -u alice:<app-passwort> ... POST /exapps/mcp_connector/mcp` mit `initialize` -> `200 OK`, `Server: uvicorn`, `Mcp-Session-Id`, `serverInfo {"name":"MCP Connector","version":"0.1.0"}`.
13. `curl -i http://127.0.0.1:8081/exapps/mcp_connector/heartbeat` -> `502 Bad Gateway`, Content-Length 0 (HaRP verwirft die Verbindung).
14. `git check-ignore .env.exapp` -> Exit-Code 0; die Datei traegt `APP_SECRET`, `HP_SHARED_KEY` und `NC_MCP_EXAPP_BASE`.
15. `grep -c "down -v\|compose\.test\.yml" scripts/bootstrap_exapp.sh` -> `0`.
16. `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py` -> 34 passed (23 aus 02-03 plus 11 neue).
17. `uv run --no-sync pytest -q` -> **629 passed** ohne Docker und ohne Netz (Ausgangsstand 618).
18. `ruff check .` -> All checks passed; `ruff format --check .` -> 101 files already formatted; `pyright` -> 0 errors; `vulture` -> leer; `check_tool_budget.py` -> 10642 Bytes, 15 Tools, Budget 12500.
19. CR-Pruefung: `compose.exapp.yml`, `deploy/Caddyfile`, `scripts/bootstrap_exapp.sh`, `docs/exapp-install.md`, `ci.yml`, Testmodul -> je "no CR". Em-Dash- und Emoji-Pruefung ueber alle neuen Dateien -> 0 Treffer.
20. Owner-Instanz nach dem Lauf: `docker compose -f compose.test.yml ps` -> `nextcloud running`; `nc-mcp-test Up 6 hours (healthy) 127.0.0.1:8080->80/tcp`; `status.php` auf 8080 -> 200. Zu keinem Zeitpunkt wurde ein Kommando gegen dieses Projekt abgesetzt.
21. Abbau: `docker compose -p nc-mcp-exapp -f compose.exapp.yml down` plus `docker stop nc_app_mcp_connector`; beide Volumes (`nc-mcp-exapp_nextcloud-exapp-data`, `nc-mcp-exapp_registry-exapp-data`) und `nc_app_mcp_connector_data` sind erhalten.

## Threat Model Coverage

| Threat ID | Umsetzung | Beleg |
|-----------|-----------|-------|
| T-02-30 | Beide veroeffentlichten Ports binden auf 127.0.0.1, HaRP veroeffentlicht keinen; Nextcloud ist nur ueber Caddy erreichbar | `test_the_topology_publishes_on_loopback_only`, `test_the_deploy_daemon_publishes_no_port`; Verification 5 |
| T-02-31 | accept: Docker-Socket bewusst gemountet, mit Begruendung im compose-File und einem Produktionshinweis in docs/exapp-install.md ("Security notes for production") | compose.exapp.yml, Kommentar am Volume; Doku-Abschnitt |
| T-02-32 | accept: Registry lauscht nur auf 127.0.0.1, enthaelt genau ein selbst gebautes Image, existiert nur wegen D-25 | compose.exapp.yml, Kommentar am Service; Doku-Abschnitt |
| T-02-33 | `.env.exapp` git-ignoriert, `.env.exapp.example` nur mit Platzhaltern | `git check-ignore .env.exapp` -> 0; Verification 14 |
| T-02-34 | Eigenes compose-File mit eigenem `name:`, eigenem Volume, eigenem Netz, eigenem Port; das Skript nennt weder `down -v` noch das andere File | `test_the_topology_carries_its_own_project_name`, `test_the_bootstrap_never_reaches_into_the_other_topology`; Verification 15 und 20 |
| T-02-35 | Festes `secret` in der Registrierung, aus `.env.exapp` wiederverwendet; FALLBACK-Block 2 beschreibt den Neustartschritt | scripts/bootstrap_exapp.sh, `app_secret()`; drei Laeufe mit demselben Secret |
| T-02-36 | `/heartbeat` von aussen: Verbindung wird von HaRP verworfen, der Client sieht 502; keine deklarierte Route trifft einen Lifecycle-Pfad | Verification 13; Doku-Abschnitt "Evidence 6" |

## Known Stubs

Keine. Jede neue Datei hat ihren Abnehmer: `compose.exapp.yml` und `deploy/Caddyfile` -> `docker compose up` lokal und im CI-Job `exapp`, `scripts/bootstrap_exapp.sh` -> derselbe Job und die Doku, `.env.exapp.example` -> die vom Skript geschriebene Datei, `docs/exapp-install.md` -> Leserinnen und Leser der Installation.

Bewusst offen: `appinfo/info.xml` zeigt weiter auf `ghcr.io`, weil dort bis Phase 5 nichts liegt (D-25). Die Testregistrierung ueberschreibt genau die drei Felder `registry`, `image` und `image-tag`; das steht als Kommentar im Skript und in der Doku.

## Issues Encountered

- **Vier Fehlschlaege bis zur gruenen Installation.** Zertifikatsverzeichnis, JSON-Escaping, Portbereich und ein zwischengespeicherter Datensatz in HaRP. Alle vier sind als Abweichung oder als Pitfall dokumentiert; der vierte ist der unangenehmste, weil er wie der dritte aussieht: nach einer fehlgeschlagenen Registrierung haelt der HaRP-Agent Host und Port der alten Registrierung im Cache, und eine korrigierte Registrierung scheitert weiter mit demselben 503. Ein `--force-recreate` des HaRP-Containers loest das; die Doku nennt das Kommando.
- **Der Registrierungslauf kann bis zu zehn Minuten haengen**, wenn der Heartbeat scheitert (AppAPI probiert 600 Sekunden lang). Das ist AppAPI-Verhalten, kein Fehler des Skripts, aber es macht jeden Fehlversuch teuer.
- **Gesperrte `.venv/Scripts/nc-mcp.exe`:** unveraendert; alle Gates liefen mit `uv run --no-sync`.

## User Setup Required

Keine. Die Topologie braucht Docker Desktop, das lief. Es wurde nichts veroeffentlicht und kein Account angelegt.

## Next Phase Readiness

- **Bereit fuer 02-05 (Permission-Parity):** Die App laeuft als echte ExApp hinter HaRP, `/mcp` wird mit dem App-Passwort eines Nutzers bedient und HaRP loest die Identitaet auf. `.env.exapp` liefert alice und bob mit frischen App-Passwoertern und `NC_MCP_EXAPP_BASE`.
- **Bereit fuer 02-06 (Discovery-Spike):** Die `.well-known`-Route ist als PUBLIC registriert und liegt unter derselben Basis-URL.
- **Offen fuer 02-07 (D-31):** Der AIO-Teil von EXAPP-01 ist nicht Gegenstand dieses Plans. Der Nachweis hier ist compose-basiert; ob und wie die App in einer All-in-One-Instanz installierbar ist, gehoert zu 02-07.
- **Zum Wiederanfahren:** `docker compose -f compose.exapp.yml up -d --wait`, danach `docker start nc_app_mcp_connector`. Der ExApp-Container gehoert nicht zum compose-Projekt, weil der Deploy Daemon ihn erzeugt hat.
- **Requirements:** EXAPP-01 ist erfuellt und abgehakt (Container-Backend, Heartbeat, Init auf 100, enabled-Handler, Deploy Daemon, HaRP-Smoke-Test).

## Self-Check: PASSED

- Alle fuenf neu angelegten Dateien liegen auf der Platte (`[ -f ]` je Datei): `compose.exapp.yml`, `deploy/Caddyfile`, `scripts/bootstrap_exapp.sh`, `.env.exapp.example`, `docs/exapp-install.md`.
- Alle vier Commits sind in `git log` auffindbar: `5a5906d`, `cd0e520`, `9500cef`, `d5c7d38`.
- Alle Akzeptanzkriterien der drei Aufgaben wurden ausgefuehrt; das eine nicht erfuellbare Kriterium ist oben als Abweichung benannt und durch eine maschinelle Zusicherung ersetzt.
- Alle sechs Punkte des Plan-Verification-Blocks wurden gemessen, siehe Verification Log.
- Kein Commit dieses Plans loescht eine Datei (`git diff --diff-filter=D` ueber alle vier Commits -> leer).

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
