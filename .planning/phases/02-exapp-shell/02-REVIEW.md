---
phase: 02-exapp-shell
reviewed: 2026-08-15T18:30:00Z
depth: standard
files_reviewed: 45
files_reviewed_list:
  - .github/workflows/ci.yml
  - .dockerignore
  - .env.exapp.example
  - Dockerfile
  - appinfo/info.xml
  - compose.exapp.yml
  - deploy/Caddyfile
  - docs/client-setup.md
  - docs/exapp-install.md
  - docs/spike-dav.md
  - docs/spike-discovery.md
  - entrypoint.sh
  - healthcheck.sh
  - start.sh
  - scripts/bootstrap_exapp.sh
  - scripts/bootstrap_test_nc.sh
  - scripts/spike_discovery.sh
  - src/mcp_connector/config.py
  - src/mcp_connector/deps.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/entry_http.py
  - src/mcp_connector/exapp/__init__.py
  - src/mcp_connector/exapp/auth.py
  - src/mcp_connector/exapp/discovery.py
  - src/mcp_connector/exapp/lifecycle.py
  - src/mcp_connector/exapp/middleware.py
  - src/mcp_connector/exapp/status.py
  - src/mcp_connector/nextcloud/clients/caldav.py
  - src/mcp_connector/nextcloud/clients/carddav.py
  - src/mcp_connector/nextcloud/clients/dav.py
  - src/mcp_connector/nextcloud/clients/deck.py
  - src/mcp_connector/nextcloud/clients/notes.py
  - src/mcp_connector/nextcloud/clients/ocs.py
  - src/mcp_connector/nextcloud/credentials.py
  - tests/conftest.py
  - tests/integration/test_exapp_dav_matrix.py
  - tests/integration/test_permission_fidelity_exapp.py
  - tests/unit/test_appapi_credentials.py
  - tests/unit/test_config.py
  - tests/unit/test_exapp_auth.py
  - tests/unit/test_exapp_discovery.py
  - tests/unit/test_exapp_entry.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_exapp_lifecycle.py
  - tests/unit/test_http_modes.py
findings:
  critical: 0
  warning: 3
  info: 8
  total: 11
status: issues_found
---

# Phase 02: Code Review Report (Abschluss-Review nach 02-05 bis 02-07)

**Geprüft:** 2026-08-15
**Tiefe:** standard, Security-Schwerpunkt laut Auftrag
**Dateien:** 45 (`exapp/middleware.py` zusätzlich zur Liste, weil es der tragende
CR-01-Fix ist und ohne es die Vollständigkeit der Interim-Fixes nicht prüfbar wäre)
**Status:** issues_found

## Narrative Findings (AI reviewer)

### Zusammenfassung

Der Auftrag war zweigeteilt: (a) sind die Fixes aus dem Interim-Security-Review
(02-INTERIM-SECURITY-REVIEW.md, CR-01/02, WR-01 bis WR-13, IN-01 bis IN-04) vollständig,
und (b) was ist mit 02-05 bis 02-07 neu dazugekommen (Discovery-Route, DAV-Matrix,
Permission-Fidelity-Test, CI, Bootstrap-Skripte).

**Zu (a), Vollständigkeit der Interim-Fixes:** Die Fixes sind im Kern vollständig und
handwerklich gut umgesetzt, jeder mit eigenem Test verifiziert:

* **CR-01:** `RequireAppApi` sitzt als ASGI-Wrapper vor der `/mcp`-Route, mit
  `guarded != 1`-Abbruch als Konstruktionsfehler-Schutz (`entry_exapp.py:72-81`).
  Fehlerpfad 401 leer mit `no-store`, `ToolError` wird mitgefangen. Tests decken
  fünf ungültige Handshake-Varianten, den leeren User (App-Kontext, geht durch) und den
  Phase-1-Modus (kein Wrapper) ab. Keine Lücke gefunden.
* **CR-02:** `require_hex64` verweigert alles außer 64 Kleinbuchstaben-Hex, beide
  Secret-Zeilen in `.env.exapp.example` sind auskommentiert, echte bash-Läufe testen
  sechs schwache Formen. Vollständig.
* **WR-01 (Header-Desync):** `_single` verweigert Mehrfachvorkommen über `getlist` bzw.
  Dict-Scan, das Manifest strippt alle fünf proxy-eigenen Header auf beiden Routen, die
  json-info-Registrierung spiegelt die Liste, und der Manifest-Gate-Test feuert
  nachweislich auf eine Route ohne Stripping. Vollständig.
* **WR-02/04/05/07/08/11/12/13, IN-01/02/04:** stichprobenhaft gegen Code, Compose,
  Dockerfile, entrypoint.sh, healthcheck.sh und die jeweiligen Tests geprüft; alle
  wie im Interim-Bericht beschrieben umgesetzt. WR-10 (search_scope quotet
  `creds.user`) ist konsistent: `parse_entries`/`_home_path_of` vergleichen beidseitig
  ungequotet, `files_url` quotet. Kein Widerspruch gefunden.
* **Eine Ausnahme:** Die WR-06-Regel ("kein Secret durch die Prozessliste") ist im
  eigenen Skript nicht vollständig durchgezogen und in zwei Schwesterdateien gar nicht
  angekommen. Das sind die drei Warnings unten (WR-01 bis WR-03 dieses Berichts, nicht
  identisch mit den Interim-IDs).

**Zu (b), neue Oberfläche 02-05 bis 02-07:**

* Die Discovery-Routen (`exapp/discovery.py`) sind bewusst öffentlich, lesen keinen
  Request-Header für ihre Antwort, leaken laut Set-Equality-Test nur `resource`,
  `authorization_servers` und `bearer_methods_supported`, und tragen `no-store`. Der
  Live-Beleg in `docs/spike-discovery.md` deckt beide Proxy-Pfade. Sauber.
* Die DAV-Matrix und der Permission-Fidelity-Test sind methodisch stark: beide führen
  Kontrollproben (kein App-Passwort im Prozess, falsches Secret wird abgelehnt, zwei
  echte Accounts, positive Kontrolle vor jedem Leak-Test) und prüfen den Confused-Deputy-
  Fall mit einem gültigen konkurrierenden Basic-Header. Keine Befunde.
* CI: Der neue `exapp`-Job generiert `HP_SHARED_KEY` pro Lauf frisch; er landet in
  keinem Log-Schritt, ist aber unmaskiert im Job-Env (IN-01).
* Die absichtlich offenen Interim-Punkte IN-05 (Token-Akkumulation), IN-07
  (unverankertes `^/\.well-known/`-Präfix, jetzt von den Spike-Routen bedient, Verhalten
  unverändert von Starlette-Literal-Matching und Caddy-Normalisierung abhängig) und
  IN-08 werden hier nicht erneut gemeldet.

Kein Befund erreicht Critical. Die drei Warnings sind alle dieselbe Klasse: Secrets in
der argv von Host-Prozessen, also genau die Klasse, die Interim-WR-06 geschlossen hat.

---

## Warnings

### WR-01: `ensure_daemon_harp` reicht `HP_SHARED_KEY` als Kommandozeilen-Argument durch die Host-Prozessliste

**Datei:** `scripts/bootstrap_exapp.sh:305-311` (konkret Zeile 310), Testlücke in
`tests/unit/test_exapp_env_setup.py:645-655`

**Befund:** Der Kommentar in Zeile 96-99 legt die Regel fest: "Every secret this script
hands to the container travels through stdin, never through a command line (WR-06)."
Die Daemon-Registrierung bricht sie:

```bash
occ app_api:daemon:register ... --harp_shared_key "${HP_SHARED_KEY}" ...
```

Der Key steht damit für die Dauer des Aufrufs in der argv des `docker`-Clients auf dem
Host (weltweit lesbar in `ps aux`) und zusätzlich in der argv des php-Prozesses im
Container. `HP_SHARED_KEY` ist laut eigener Einstufung (CR-02, WR-11) bearer-äquivalent:
wer ihn kennt und den FRP-Port erreicht, hängt einen fremden Tunnel an HaRP. Der
Wächter-Test `test_no_secret_travels_through_the_process_list` prüft nur die Muster
`-e "OC_PASS=` und `--json-info "$(`, sieht diese Stelle also nicht; die Fix-Behauptung
des Interim-Berichts ("Every secret ... travels through stdin") ist damit für genau ein
Secret nicht wahr.

**Fix:** Denselben `occ_stdin`-Weg nehmen wie bei der App-Registrierung. Das holt den
Key aus der Host-Prozessliste; das Rest-Risiko argv-im-Container ist dasselbe, das
WR-06 für die json-info-Payload bereits dokumentiert akzeptiert.

```bash
if ! output="$(printf '%s' "${HP_SHARED_KEY}" | occ_stdin \
  'KEY="$(cat)"; exec php occ app_api:daemon:register "$@" --harp_shared_key "$KEY"' \
  "${DAEMON_NAME}" "Harp Proxy (Docker)" docker-install http \
  "appapi-harp:8780" "http://caddy" \
  --net "${NETWORK_NAME}" --harp \
  --harp_frp_address "appapi-harp:8782" \
  --set-default 2>&1)"; then
```

Zusätzlich den Wächter-Test um das Muster `--harp_shared_key "${HP_SHARED_KEY}"`
erweitern, damit die Stelle nicht zurückkommt.

### WR-02: `bootstrap_test_nc.sh` verwendet weiterhin das `-e "OC_PASS=..."`-Muster, das Interim-WR-06 im Schwesterskript geschlossen hat

**Datei:** `scripts/bootstrap_test_nc.sh:35-40` (konkret Zeile 38)

**Befund:** `occ_pw` übergibt das Login-Passwort als `-e "OC_PASS=${password}"` an
`docker compose exec`. Das ist exakt der Angriffspfad aus Interim-WR-06: das Passwort
steht in der argv des docker-Clients auf dem Host und in der Container-Config des
exec-Aufrufs. Der Fix wurde nur in `bootstrap_exapp.sh` eingebaut (dort `occ_stdin` +
`occ_pw` über Pipe), das Schwesterskript blieb auf dem alten Stand. Die Default-Werte
(`alice-test-pw-01`) sind zwar im Repo veröffentlicht und damit ohnehin kein Geheimnis,
aber `NC_TEST_ALICE_PASSWORD`/`NC_TEST_BOB_PASSWORD` sind überschreibbar, und die mit
diesen Passwörtern erzeugten App-Tokens sind echte Zugänge auf der täglich genutzten
Testinstanz (compose.test.yml), nicht auf einer Wegwerf-Topologie.

**Fix:** `occ_stdin` und die stdin-Variante von `occ_pw` aus `bootstrap_exapp.sh:103-117`
unverändert übernehmen:

```bash
occ_stdin() {
  local snippet="$1"
  shift
  docker compose -f "${COMPOSE_FILE}" exec -T --user www-data "${SERVICE}" \
    sh -c "${snippet}" sh "$@"
}

occ_pw() {
  local password="$1"
  shift
  printf '%s' "$password" |
    occ_stdin 'OC_PASS="$(cat)"; export OC_PASS; exec php occ "$@"' "$@"
}
```

### WR-03: `spike_discovery.sh` legt Alices App-Passwort per `curl -u` in die argv

**Datei:** `scripts/spike_discovery.sh:63-65` (gesetzt), `:92-99` (verwendet)

**Befund:** `basic_auth=(-u "${ALICE_USER}:${ALICE_APP_PASSWORD}")` reicht das
App-Passwort als curl-Argument durch, sichtbar in `ps aux` für die Dauer jedes der
beiden authentifizierten Requests. Dieselbe Klasse wie WR-01/WR-02; das Passwort ist
ein voll gültiger Zugang zum alice-Konto der Topologie. Das Skript ist neu aus 02-05
und hat die WR-06-Regel nicht geerbt.

**Fix:** Credentials über eine curl-Konfigurationsdatei mit `umask 077` reichen statt
über die Kommandozeile:

```bash
basic_auth=()
if [ -n "${ALICE_APP_PASSWORD}" ]; then
  curl_netrc="$(mktemp)"
  trap 'rm -f "${curl_netrc}"' EXIT
  chmod 600 "${curl_netrc}"
  printf 'user = "%s:%s"\n' "${ALICE_USER}" "${ALICE_APP_PASSWORD}" > "${curl_netrc}"
  basic_auth=(-K "${curl_netrc}")
fi
```

---

## Info

### IN-01: Der CI-Job schreibt `HP_SHARED_KEY` unmaskiert in `GITHUB_ENV`

**Datei:** `.github/workflows/ci.yml:65-69`

**Befund:** `echo "HP_SHARED_KEY=$(openssl rand -hex 32)" >> "$GITHUB_ENV"` ohne
vorheriges `::add-mask::`. Kein heutiger Schritt gibt den Wert aus (geprüft: bootstrap
echot ihn nie, der Log-Dump auf Failure zeigt nur Container-Logs), aber jeder künftige
Schritt, der `env` druckt oder in dessen Fehlerausgabe der Wert auftaucht, stellt ihn
unredigiert in ein öffentliches Log. Der Schaden ist begrenzt (Wegwerf-Key pro Lauf,
Loopback-Topologie auf ephemerem Runner), die Maskierung kostet eine Zeile.

**Fix:**

```yaml
run: |
  KEY="$(openssl rand -hex 32)"
  echo "::add-mask::${KEY}"
  echo "HP_SHARED_KEY=${KEY}" >> "$GITHUB_ENV"
```

### IN-02: Der Plaintext-Guard prüft nur das Verzeichnis, nicht die Zertifikatsdateien

**Datei:** `entrypoint.sh:27-40` gegen `start.sh:14,22-24`

**Befund:** Beide prüfen `-d /certs/frp`. HaRP legt das Verzeichnis (per `mkdir -p`)
vor den drei Dateien an; im Rennen zwischen mkdir und Datei-Kopie startet start.sh mit
einer TLS-Konfiguration, deren `certFile` noch fehlt. Kein Downgrade (die Konfiguration
sagt `tls.enable = true`, frpc scheitert und der Healthcheck aus WR-05 meldet den toten
Tunnel), aber ein vermeidbarer roter Container mit irreführender Fehlermeldung.

**Fix:** In der Warteschleife und im Abbruchkriterium zusätzlich auf
`/certs/frp/client.crt` und `/certs/frp/client.key` warten, nicht nur auf das
Verzeichnis.

### IN-03: Die feste Trusted-Proxy-IP liegt im dynamischen Vergabebereich des Compose-Subnetzes

**Datei:** `compose.exapp.yml:39,68,100,132-140`

**Befund:** `172.29.42.10` ist statisch an caddy vergeben und die einzige Adresse auf
beiden Trust-Listen (WR-08-Fix, korrekt). Die IPAM-Konfiguration reserviert aber keinen
dynamischen Bereich: fällt caddy weg, kann Docker die .10 dynamisch an einen anderen
Container vergeben, auch an den vom Daemon neu erzeugten ExApp-Container, der damit zum
vertrauten Proxy würde. Konstruiert (braucht caddy-Ausfall plus genügend Container),
aber billig auszuschließen.

**Fix:** Dynamische Vergabe vom statischen Bereich trennen:

```yaml
    ipam:
      config:
        - subnet: 172.29.42.0/24
          ip_range: 172.29.42.128/25   # dynamische Vergabe nie im statischen Bereich
```

### IN-04: Ein docker-install-Daemon ohne HaRP läuft auf `/mcp` in die 421-Falle

**Datei:** `entrypoint.sh:57`, `src/mcp_connector/entry_exapp.py:120-133`,
`src/mcp_connector/config.py:216-233`

**Befund:** Der Rebinding-Schalter ist korrekt an `HP_SHARED_KEY` gekoppelt (WR-02-Fix).
Bei einem AppAPI-docker-install-Daemon ohne HaRP (PHP-Proxy-Pfad, bis NC 35 noch
verbreitet) bleibt die Host-Prüfung scharf, die Default-Allowlist ist localhost, und der
Host-Header des Proxys ist der Container-Name. Ergebnis: Lifecycle-Routen funktionieren
(sie liegen nicht hinter der Transport-Prüfung), die Installation wird grün, und jede
`/mcp`-Anfrage endet mit 421, sichtbar nur als eine Log-Zeile. Das Projekt hat sich
bewusst gegen DSP-Spezifisches entschieden; dann sollte der Fall aber benannt sein.

**Fix:** In `docs/exapp-install.md` einen Satz aufnehmen (ohne HaRP zwingend
`NC_MCP_ALLOWED_HOSTS` auf den vom Proxy verwendeten Namen setzen), oder in
`entry_exapp.main` beim Start ohne `HP_SHARED_KEY` und ohne `NC_MCP_ALLOWED_HOSTS`
eine Warnzeile loggen.

### IN-05: `notes.get_note` interpoliert die Note-Id ohne clientseitigen Guard in die URL

**Datei:** `src/mcp_connector/nextcloud/clients/notes.py:70-77`

**Befund:** Deck erzwingt an der Client-Schicht `_path_id` (nur Ziffern, T-01-63); Notes
verlässt sich allein auf die Tool-Schicht (`tools/notes.py:170-185`, dort korrekt
isdigit-geprüft). Heute nicht erreichbar, aber die einzige Stelle im Client-Paket, an
der ein Bezeichner ohne eigenen Guard in einen URL-Pfad geht; ein künftiger zweiter
Aufrufer erbt die Prüfung nicht.

**Fix:** Analog zu Deck einen Ziffern-Guard in `get_note` (und der Vollständigkeit
halber `web_url`) einziehen: `if not str(note_id).isdigit(): raise ToolError(...)`.

### IN-06: `discovery._json` garantiert das versprochene `no-store` nicht

**Datei:** `src/mcp_connector/exapp/discovery.py:94-100`

**Befund:** Der Docstring verspricht "so no-store cannot be forgotten on one branch",
der Code sagt `headers or dict(_NO_STORE)`: ein künftiger Aufrufer, der ein nicht-leeres
Header-Dict ohne `Cache-Control` übergibt, verliert `no-store` still, und der
PHP-Proxy cacht die Antwort 3600 Sekunden (genau das Pitfall-4-Szenario, gegen das die
Konstante existiert). Heute setzen beide Aufrufer den Header selbst, der Befund ist
eine geladene Falle, kein aktiver Fehler.

**Fix:** Mergen statt ersetzen: `JSONResponse(payload, status_code=status_code,
headers={**_NO_STORE, **(headers or {})})`.

### IN-07: `json_info` interpoliert `port` und `REGISTRY` unvalidiert in die Registrierungs-Payload

**Datei:** `scripts/bootstrap_exapp.sh:54,60-61,380-385`

**Befund:** `"port":${port}` steht unquotiert im JSON, und `port` kommt aus den
überschreibbaren `NC_EXAPP_APP_PORT`/`NC_EXAPP_MANUAL_PORT`; `REGISTRY`
(`NC_EXAPP_REGISTRY`) wird in einen String interpoliert. Ein vergessener Export in der
aufrufenden Shell (dieselbe Fehlerklasse, gegen die WR-07 `COMPOSE_FILE` festgenagelt
hat) erzeugt hier bestenfalls ungültiges, schlimmstenfalls um Felder erweitertes JSON,
das AppAPI kommentarlos übernimmt. `APP_SECRET` ist über CR-02 abgesichert, die beiden
hier nicht.

**Fix:** Vor `json_info` validieren:
`printf '%s' "${APP_PORT}" | grep -Eq '^[0-9]+$'` (für beide Ports) und für `REGISTRY`
ein Muster wie `^[0-9A-Za-z_.:-]+$`, sonst Abbruch.

### IN-08: `on: push` plus `on: pull_request` erzeugt Doppel-Läufe für jeden PR aus dem eigenen Repo

**Datei:** `.github/workflows/ci.yml:3-5`

**Befund:** Jeder Branch-Push mit offenem PR startet alle vier Jobs zweimal, darunter
zweimal den vollen ExApp-Topologie-Aufbau. Kein Sicherheitsproblem, nur doppelte
Laufzeit und doppeltes Rauschen bei Failures.

**Fix:**

```yaml
on:
  push:
    branches: [master]
  pull_request:
```

---

## Was geprüft wurde und sauber war

Damit Weglassungen nicht als Lücken gelesen werden:

* **Vertrauensgrenze (Prüfschwerpunkt 1):** Middleware vor der `/mcp`-Route, Verifikation
  im Handler als zweite Kontrolle, Mehrfach-Header abgelehnt, Manifest strippt die fünf
  proxy-eigenen Header auf beiden Routen, Lifecycle-Pfade fehlen im Manifest und HaRP
  droppt sie zusätzlich (Live-Beleg 502). Ein zusätzlicher `Authorization`-Header ändert
  die Identität nachweislich nicht (Unit- und Live-Test).
* **Secret-Handling (Prüfschwerpunkt 2):** Kein Secret in Dockerfile-ENV oder Layern
  (Tests erzwingen es), `.env.exapp` mit umask 077 geschrieben und git-ignoriert,
  Beispieldatei ohne setzbare Secret-Zeilen, `require_hex64` auf beiden Secrets, kein
  Repr/Log-Leak (Tests decken auth.py, deps.py, credentials.py, status.py). Ausnahmen:
  die drei argv-Stellen oben.
* **Impersonation (Prüfschwerpunkt 3):** Identität ausschließlich aus
  `AUTHORIZATION-APP-API`, leere User-Id nur im App-Kontext und beim Datenzugriff hart
  verweigert, `base_url` nie aus dem Request, `search_scope` quotet, Scope-Filter
  `_home_path_of` mit Präfix-plus-Slash-Prüfung gegen `alicexyz`-Verwechslung,
  Cross-User-Negativfall und Confused-Deputy über die echte Kette bewiesen.
* **Container/Topologie (Prüfschwerpunkt 4):** non-root mit nicht schreibbarem venv,
  frpc-Pin als RUN-Konstante, Rebinding-Schalter HaRP-gebunden, Healthcheck kennt beide
  Transporte und den toten Tunnel, Loopback-Bindungen und Ein-Proxy-Trust-Listen per
  Test festgenagelt, Digest-Verifikation vor der Registrierung in der richtigen
  Reihenfolge (Test prüft die Reihenfolge im Skript).
* **Neue Tests (02-06/02-07):** beide Integrationsdateien führen Kontrollproben, decken
  Negativ- und Edge-Pfade und skippen sauber mit benannten Variablen statt zu erröten;
  keine fehlenden Assertions, keine erkennbar flakigen Muster (der einzige Retry, die
  Kalender-Schleife im Bootstrap, ist begründet und begrenzt).

Bewusst nicht erneut gemeldet: die im Interim-Review als "bewusst offen" geführten
IN-05, IN-07 und IN-08 sowie die dort für die Live-Abnahme vorgemerkten Punkte, die
02-07 laut Doku-Belegen abgearbeitet hat (WR-04-Zertifikats-Timing, WR-08/11-Trust-
Listen im Lauf, 02-05-Streaming über HaRP).

---

_Geprüft: 2026-08-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Tiefe: standard_
