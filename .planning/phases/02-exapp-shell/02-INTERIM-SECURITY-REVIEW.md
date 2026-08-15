---
phase: 02-exapp-shell
reviewed: 2026-08-15T12:45:00Z
depth: deep
scope: security-only (Interim vor Spike 02-05/02-06)
files_reviewed: 19
files_reviewed_list:
  - src/mcp_connector/exapp/__init__.py
  - src/mcp_connector/exapp/auth.py
  - src/mcp_connector/exapp/lifecycle.py
  - src/mcp_connector/exapp/status.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/config.py
  - src/mcp_connector/deps.py
  - src/mcp_connector/nextcloud/credentials.py
  - src/mcp_connector/nextcloud/clients/dav.py
  - Dockerfile
  - .dockerignore
  - start.sh
  - healthcheck.sh
  - appinfo/info.xml
  - compose.exapp.yml
  - deploy/Caddyfile
  - scripts/bootstrap_exapp.sh
  - .env.exapp.example
  - docs/exapp-install.md
findings:
  critical: 2
  warning: 13
  info: 8
  total: 23
status: issues_found
---

# Phase 02: Interim-Security-Review der ExApp-Oberfläche

**Geprüft:** 2026-08-15
**Tiefe:** deep (cross-file, inklusive SDK-Quellen und laufendem Image)
**Umfang:** ausschließlich Sicherheit, Plan 02-01 bis 02-04
**Status:** issues_found

## Zusammenfassung

Der Handshake selbst (`exapp/auth.py`) ist handwerklich gut: `secrets.compare_digest`
auf UTF-8-Bytes, keine Echo-Pfade, keine Secrets in Exceptions oder Logs, Rejection ohne
Detail. Die Prüfpunkte 1 und 3 des Auftrags haben in der reinen Header-Verifikation keine
verwertbare Lücke ergeben, und die Impersonation ist sauber gebunden: die Identität kommt
ausschließlich aus `AUTHORIZATION-APP-API`, ein zusätzlicher `Authorization`-Header wird
nachweislich ignoriert, `base_url` stammt nie aus dem Request.

Die Lücken liegen eine Ebene darüber und darunter:

1. Die Authentifizierung sitzt nicht an der Grenze, sondern im Tool-Handler. Der gesamte
   JSON-RPC-Vorbau (`initialize`, `tools/list`, Session-Allokation) wird im ExApp-Modus
   ohne jeden AppAPI-Header bedient. Das ist empirisch belegt, nicht vermutet.
2. Das Secret-Handling rundherum (Beispieldatei, Prozessliste, Compose-Default,
   TLS-Fallback in `start.sh`) hat mehrere Stellen, an denen ein vorhersagbares oder
   mitlesbares `APP_SECRET` beziehungsweise `HP_SHARED_KEY` entsteht.

Die Container- und Manifest-Arbeit ist überdurchschnittlich: keine Secrets in ENV oder
Layer-History (per `docker history` und `docker inspect` am lokalen Image
`127.0.0.1:5000/mcp_connector:0.1.0` verifiziert), non-root konsequent, frpc per
sha256 gepinnt, Routen eng deklariert, Lifecycle-Pfade nicht im Manifest.

**Empfehlung:** CR-01 und CR-02 vor den Spikes 02-05/02-06 schließen. Die Spikes bauen
auf `/mcp` auf und würden die offene Grenze sonst mit erben.

---

## Critical Issues

### CR-01: Im ExApp-Modus ist der MCP-Endpunkt an der Transportgrenze unauthentifiziert

**Datei:** `src/mcp_connector/entry_exapp.py:55-62`, `src/mcp_connector/server/__init__.py:38-49`, `src/mcp_connector/deps.py:64-86`

**Befund (empirisch belegt):** `deps.build_auth()` liefert im ExApp-Modus zwingend
`(None, None)`, weil `NC_MCP_STATIC_BEARER` nicht gesetzt sein darf (`entry_exapp.py:38`,
`main` bricht sonst mit Exit 2 ab). Das SDK baut daraufhin `Route("/mcp",
endpoint=streamable_http_app)` ganz ohne Auth-Wrapper und ohne Middleware
(`.venv/Lib/site-packages/mcp/server/lowlevel/server.py:806-813`). Die AppAPI-Prüfung
findet erst in `resolve_credentials` statt, also erst beim Tool-Aufruf.

Verifiziert gegen die reale Image-Umgebung (`NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=1`,
so wie `Dockerfile:112` es setzt):

```
ROUTES: [('/mcp', None), ('/heartbeat', {'GET','HEAD'}), ('/init', {'POST'}), ('/enabled', {'PUT'})]
MIDDLEWARE: []
INIT status: 200  session: 9f7e0044c0b54a83b1fcf3a26d1413f4
TOOLS status: 200
```

Kein `EX-APP-ID`, kein `AUTHORIZATION-APP-API`, kein `EX-APP-VERSION`. Antwort 200.

**Angriffspfad:** Jeder, der den Container-Port beziehungsweise den Unix-Socket erreicht,
also jeder andere Container im selben Docker-Netz, jeder Prozess auf dem Host, im
`--manual`-Entwicklungsmodus laut `docs/exapp-install.md:185` jeder im LAN, kann ohne
Anmeldung:

* eine MCP-Session anlegen (Speicher pro Session, unbegrenzt, kein Rate-Limit)
* `initialize` fahren und `serverInfo` plus `instructions` auslesen
* `tools/list` fahren und die vollständige Tool-Oberfläche samt Schemata abziehen

Datenzugriff bleibt korrekt gesperrt (`_credentials_from_appapi` verlangt Secret und
nicht-leere User-ID). Das ist aber ein Handler-Kontrollpunkt, keine Grenze: ein einziges
künftiges Tool oder eine Resource, die `resolve_clients(ctx)` vergisst, ist sofort
unauthentifiziert erreichbar. Genau das sollen die Spikes 02-05/02-06 ergänzen.

Zusätzlich wird der eigene Anspruch verletzt: `deps.py:21-25` sagt "die Identität kommt
aus `AUTHORIZATION-APP-API` und von nirgendwo sonst", und `info.xml` beschreibt die MCP-
Route als "the whole external attack surface". Für alle Nicht-Tool-Methoden gilt beides
heute nicht.

**Fix:** Handshake als ASGI-Middleware vor die `/mcp`-Route ziehen, nicht statt, sondern
zusätzlich zur Prüfung im Handler.

```python
# src/mcp_connector/exapp/middleware.py
class RequireAppApi:
    """Verify the AppAPI handshake before any MCP code runs."""

    def __init__(self, app: ASGIApp, env: Mapping[str, str] | None = None) -> None:
        self._app, self._env = app, env

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        try:
            require_appapi(Request(scope), env=self._env)
        except AppApiRejected:
            await Response(status_code=401, headers={"Cache-Control": "no-store"})(
                scope, receive, send
            )
            return
        await self._app(scope, receive, send)

# entry_exapp.build_exapp_app
for route in app.router.routes:
    if getattr(route, "path", None) == "/mcp":
        route.app = RequireAppApi(route.app, env)
```

Die leere User-ID darf hier durchgehen (App-Kontext); die Verweigerung für Datenzugriff
bleibt in `_credentials_from_appapi`. Ein Test, der `initialize` ohne Header gegen
`build_exapp_app()` fährt und 401 erwartet, gehört in `tests/unit/test_exapp_entry.py`.

---

### CR-02: Der Platzhalter aus `.env.exapp.example` wird ungeprüft zum echten `APP_SECRET`

**Datei:** `scripts/bootstrap_exapp.sh:194-204`, `.env.exapp.example:27,31`

**Befund:** `app_secret()` liest `APP_SECRET` per `sed` aus `.env.exapp` und gibt jeden
nicht-leeren Wert unverändert zurück. Nur wenn die Datei fehlt oder die Zeile leer ist,
wird `openssl rand -hex 32` verwendet. Es gibt keine Prüfung auf Länge, Zeichenvorrat oder
Platzhalter-Muster. `.env.exapp.example:27` liefert exakt den Wert
`replace-me-with-a-random-hex-string`.

**Angriffspfad:** Der naheliegende Einstieg `cp .env.exapp.example .env.exapp` (die
Beispieldatei nennt selbst `set -a && . ./.env.exapp` als Arbeitsschritt) führt dazu, dass
der Bootstrap die Registrierung mit einem in Git veröffentlichten, weltweit bekannten
Secret durchführt. `APP_SECRET` ist laut `config.py:88-90` bearer-äquivalent: wer es
kennt, kann über `AUTHORIZATION-APP-API` jeden beliebigen Nutzernamen setzen und damit
jeden Account der Instanz lesen. Der gleiche Pfad gilt für `HP_SHARED_KEY:31`, mit dem
sich ein fremder FRP-Proxy an HaRP hängen kann.

Verschärfend: Beide Werte werden anschließend von `app_secret()` als "vorhandener" Wert
gepinnt und über jeden weiteren Lauf hinweg festgehalten, genau damit sie stabil bleiben.

**Fix:** Platzhalter und schwache Werte hart ablehnen, statt sie zu übernehmen.

```bash
app_secret() {
  local existing=""
  if [ -f "${ENV_FILE}" ]; then
    existing="$(sed -n 's/^APP_SECRET=//p' "${ENV_FILE}" | head -n1 | tr -d '\r')"
  fi
  if [ -n "$existing" ]; then
    if ! printf '%s' "$existing" | grep -Eq '^[0-9a-f]{64}$'; then
      echo "ERROR: APP_SECRET in ${ENV_FILE} is not 64 hex characters." >&2
      echo "Delete the line and re-run; a fresh secret is generated then." >&2
      return 1
    fi
    printf '%s' "$existing"
    return 0
  fi
  openssl rand -hex 32
}
```

Zusätzlich in `.env.exapp.example` beide Zeilen auskommentieren und über den Kommentar
klarstellen, dass die Datei nie kopiert, sondern nur gelesen wird.

---

## Warnings

### WR-01: Header-Desync: `verify_appapi_headers` nimmt den letzten, jeder andere Leser den ersten Wert

**Datei:** `src/mcp_connector/exapp/auth.py:51`, `appinfo/info.xml` (beide `<headers_to_exclude>[]</headers_to_exclude>`)

**Befund (empirisch):** `{key.lower(): value for key, value in headers.items()}` behält bei
doppelten Headern den **letzten** Wert, `starlette.datastructures.Headers.get()` liefert den
**ersten**. Gemessen:

```
get() -> YXR0YWNrZXI6d3JvbmdzZWNyZXQ=      (attacker:wrongsecret)
lookup wins -> b'alice:realsecret'
```

Beide Manifest-Routen setzen `headers_to_exclude` auf `[]`, verzichten also bewusst auf
jedes proxyseitige Strippen. Client-gesetzte `AUTHORIZATION-APP-API`, `EX-APP-ID`,
`EX-APP-VERSION` und `X-ORIGIN-IP` erreichen die App damit unverändert und stehen neben
den vom Proxy gesetzten Kopien.

**Angriffspfad:** Ob der Angreifer-Wert gewinnt, hängt allein davon ab, ob der jeweilige
Proxy seinen Header voranstellt oder anhängt, also von einer Komponente ausserhalb dieses
Repos. Ein voller Bypass ist heute nicht möglich, weil auch die manipulierte Kopie ein
gültiges `APP_SECRET` tragen muss. Was heute geht: gezielte Ablehnung fremder Requests
durch eine untergeschobene zweite Kopie. Was morgen geht, sobald ein Pfad die leere
User-ID akzeptiert oder die Auswertung sich verschiebt: freie User-Wahl.

**Fix:** Mehrfachvorkommen explizit ablehnen statt implizit aufzulösen, und die Header im
Manifest strippen lassen.

```python
def _single(headers: Mapping[str, str], name: str) -> str:
    getall = getattr(headers, "getlist", None)
    values = getall(name) if getall else [v for k, v in headers.items() if k.lower() == name]
    if len(values) > 1:
        raise AppApiRejected
    return values[0] if values else ""
```

```xml
<headers_to_exclude>["AUTHORIZATION-APP-API","EX-APP-ID","EX-APP-VERSION","AA-VERSION","X-ORIGIN-IP"]</headers_to_exclude>
```

### WR-02: `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=1` liegt fest im Image, für jeden Deploy-Modus

**Datei:** `Dockerfile:112`

**Befund:** Der Schalter schaltet in `TransportSecuritySettings` sowohl die Host- als auch
die Origin-Prüfung ab. Der Kommentar begründet ihn mit HaRP, gesetzt ist er aber
unbedingt, also auch für den `docker-install`-Daemon ohne HaRP und für jeden, der das
Image von Hand mit publiziertem Port startet.

**Angriffspfad:** Zusammen mit CR-01 ist der Endpunkt damit auch aus einem Browser heraus
per DNS-Rebinding erreichbar, ohne dass eine Origin-Prüfung eingreift. Der praktische
Schaden bleibt heute auf Metadaten begrenzt, weil das SDK `Content-Type: application/json`
erzwingt und ein solcher Request Preflight auslöst. Die Verteidigung, die das absichern
soll, ist aber genau die abgeschaltete.

**Fix:** Den Schalter nicht in den Layer schreiben, sondern in `start.sh` an `HP_SHARED_KEY`
koppeln, und `NC_MCP_ALLOWED_HOSTS` konfigurierbar lassen:

```bash
if [ -n "$HP_SHARED_KEY" ]; then
    export NC_MCP_DISABLE_DNS_REBINDING_PROTECTION=1
fi
```

### WR-03: `select_mode` lässt sich durch zwei generische, nicht praefixierte Umgebungsvariablen umschalten

**Datei:** `src/mcp_connector/config.py:157-158`, `src/mcp_connector/entry_exapp.py:38,69-77`

**Befund (empirisch):**

```
mode with ambient APP_ID/APP_SECRET + static bearer: exapp
mode passthrough case: exapp
```

`APP_ID` und `APP_SECRET` sind die einzigen Modus-Schalter ohne `NC_MCP_`-Praefix und
zugleich sehr verbreitete Namen (GitHub Apps, Sentry, diverse PaaS). `entry_exapp.main`
sichert nur die eine Richtung ab (`CONFLICTING_VARIABLES`, Exit 2). Die Gegenrichtung ist
ungesichert, und `entry_http` kann sie gar nicht absichern, weil dort kein `main`
existiert, sondern `app = build_app()` beim Import läuft.

**Angriffspfad:** Wer die Prozessumgebung beeinflusst (Compose-Datei, systemd-Drop-in,
CI-Variable, ein Base-Image mit gesetztem `ENV APP_SECRET`), kippt eine Phase-1-Instanz
still in den ExApp-Modus. Kein Auth-Bypass, denn `build_auth()` liest
`NC_MCP_STATIC_BEARER` direkt und lässt die Bearer-Schicht scharf, aber die Credential-
Quelle wechselt lautlos und jeder Tool-Aufruf endet in "no valid AppAPI authentication".
Für den Passthrough-Modus heisst das: alle Nutzer sind ausgesperrt, ohne dass eine
Konfiguration verändert wurde.

**Fix:** Modus explizit vom Entry-Point durchreichen statt aus der globalen Umgebung zu
schnüffeln, zum Beispiel ein von `entry_exapp` gesetztes `NC_MCP_MODE=exapp`, das
`select_mode` zusätzlich verlangt. Minimalvariante: Guard in `entry_http.build_app`, der
bei `exapp_configured(env)` mit einer klaren Meldung abbricht.

### WR-04: `start.sh` fällt still auf FRP ohne TLS zurück und schickt `HP_SHARED_KEY` im Klartext

**Datei:** `start.sh:37-52`

**Befund:** Fehlt `/certs/frp`, wird `transport.tls.enable = false` geschrieben und
`metadatas.token = "$HP_SHARED_KEY"` unverschlüsselt übertragen. `docs/exapp-install.md`
dokumentiert im gleichen Repo, dass genau diese Zertifikatsinstallation fehlschlagen kann
("answers 500"), Pitfall 2 der Doku beschreibt den Fall als real beobachtet.

**Angriffspfad:** Wer den Netzpfad zwischen ExApp-Container und HaRP mitlesen kann,
bekommt den Shared Key und kann sich anschliessend selbst als ExApp-Tunnel registrieren.
Der Downgrade ist genau die Art stillen Fallbacks, die D-27 an anderer Stelle verbietet.

**Fix:** Die Datei ist bewusst upstream-verbatim, also nicht editieren, sondern davor
prüfen. Im `ENTRYPOINT` einen Wrapper vorschalten, der bei gesetztem `HP_SHARED_KEY` und
fehlendem `/certs/frp` mit Exit ungleich 0 abbricht, oder mindestens eine
`logger.error`-taugliche Zeile plus dokumentierten Opt-in
(`ALLOW_PLAINTEXT_FRP=1`) verlangen.

### WR-05: Der Healthcheck bleibt grün, wenn frpc tot ist

**Datei:** `healthcheck.sh:20-26`, `start.sh:63-66`

**Befund:** Bei gesetztem `HP_SHARED_KEY` probt der Healthcheck den Unix-Socket
(`--unix-socket /tmp/exapp.sock`). frpc läuft als unbeaufsichtigtes Hintergrundkind von
PID 1 (`frpc -c /frpc.toml &`, danach `exec "$@"`), zusätzlich mit `loginFailExit = false`.
Stirbt frpc oder kommt der Login nie zustande, antwortet uvicorn auf dem Socket weiterhin,
der Container gilt als `healthy`, und HaRP hat trotzdem kein Backend.

**Angriffspfad:** Verfügbarkeit und Fehldiagnose, nicht Vertraulichkeit: der beschriebene
Zustand ist von aussen als 503 sichtbar, im Monitoring aber als "gesund". Genau die
Nebenwirkung, nach der Prüfschwerpunkt 5 fragt.

**Fix:** Im HaRP-Zweig zusätzlich prüfen, dass frpc lebt, zum Beispiel
`pgrep -x frpc >/dev/null || exit 1` vor dem `exec curl`. Sauberer wäre ein
Prozess-Supervisor, aber die eine Zeile schliesst die Lücke.

### WR-06: Bootstrap schiebt `APP_SECRET` und Nutzerpasswörter durch die Prozessliste

**Datei:** `scripts/bootstrap_exapp.sh:82-84,270-271,319-320`

**Befund:** `--json-info "$(json_info)"` enthält `"secret":"${APP_SECRET}"` als Argument
in der Kommandozeile, `occ_pw` übergibt Passwörter als `-e "OC_PASS=${password}"`. Beides
steht für die Dauer des Aufrufs in `ps aux` auf dem Host und in der Argv des
`docker`-Clients; die `-e`-Variante landet zusätzlich in der Container-Config des
`exec`-Aufrufs.

**Angriffspfad:** Jeder lokale Nutzer ohne besondere Rechte liest während des Bootstraps
das App-Secret mit und kann damit anschliessend jeden Account der Instanz impersonieren.

**Fix:** Secrets über stdin statt über Argumente reichen.

```bash
json_info | docker compose -f "${COMPOSE_FILE}" exec -T --user www-data "${SERVICE}" \
  php occ app_api:app:register "${APP_ID}" "${DAEMON_NAME}" --json-info - --force-scopes --wait-finish
```

Falls `occ` kein `-` akzeptiert: die JSON-Datei mit `umask 077` in ein Container-Volume
schreiben und den Pfad übergeben, danach löschen.

### WR-07: `COMPOSE_FILE` ist überschreibbar, der Schutz der anderen Topologie ist damit nur nominal

**Datei:** `scripts/bootstrap_exapp.sh:36,347`, `tests/unit/test_exapp_env_setup.py:330-335`

**Befund:** `COMPOSE_FILE="${COMPOSE_FILE:-compose.exapp.yml}"`. Der Test
`test_the_bootstrap_never_reaches_into_the_other_topology` prüft nur, dass der String
`compose.test.yml` nicht im Skript vorkommt. Ein Aufruf
`COMPOSE_FILE=compose.test.yml bash scripts/bootstrap_exapp.sh` erfüllt den Test und legt
trotzdem Nutzer an, erzeugt App-Passwörter und setzt vor allem
`auth.bruteforce.protection.enabled=false` (Zeile 347) auf der dauerhaft laufenden
Instanz.

**Angriffspfad:** Kein Angreifer nötig, ein vergessenes `export COMPOSE_FILE` in der Shell
reicht. Ergebnis ist eine produktiv genutzte Testinstanz mit abgeschaltetem
Bruteforce-Schutz und zusätzlichen gültigen App-Passwörtern in einer git-ignorierten
Datei.

**Fix:** `COMPOSE_FILE` nicht überschreibbar machen und den Schutz aktiv prüfen:

```bash
COMPOSE_FILE="compose.exapp.yml"
if [ "$(docker compose -f "${COMPOSE_FILE}" config --format json | jq -r .name)" != "nc-mcp-exapp" ]; then
  echo "ERROR: this script only ever runs against the nc-mcp-exapp project." >&2
  exit 1
fi
```

Den Test entsprechend auf "kein `COMPOSE_FILE`-Override" umstellen.

### WR-08: `TRUSTED_PROXIES` und `HP_TRUSTED_PROXY_IPS` umfassen den ExApp-Container selbst

**Datei:** `compose.exapp.yml:58,86`

**Befund:** Beide Werte sind `172.29.42.0/24`, also das komplette Compose-Subnetz. Der
ExApp-Container wird vom Deploy-Daemon in genau dieses Netz gehängt (`--net
nc-mcp-exapp-net`, `bootstrap_exapp.sh:219`). Damit ist ausgerechnet die Komponente, die
nicht vertrauenswürdige Eingaben verarbeitet, für Nextcloud und für HaRP ein
vertrauenswürdiger Proxy.

**Angriffspfad:** Wer im ExApp-Container Codeausführung erlangt (siehe WR-13, die
`.venv` ist für den Laufzeit-Nutzer schreibbar), kann gegenüber Nextcloud beliebige
Client-IPs setzen: Bruteforce-Zähler umgehen, Audit-Logs fälschen, IP-basierte Regeln
aushebeln. Der Kommentar im File sagt "the proxy lives in this subnet", das Subnetz
enthält aber vier bis fünf Container.

**Fix:** Feste IPs vergeben und nur die des Reverse Proxy eintragen:

```yaml
  caddy:
    networks:
      default:
        ipv4_address: 172.29.42.10
# nextcloud:
      TRUSTED_PROXIES: "172.29.42.10"
# appapi-harp:
      HP_TRUSTED_PROXY_IPS: "172.29.42.10"
```

### WR-09: Unauthentifizierte Loopback-Registry plus Referenz per Tag statt Digest

**Datei:** `compose.exapp.yml:103-116`, `scripts/bootstrap_exapp.sh:229-243,256`

**Befund:** `registry:2` läuft ohne Auth und ohne TLS auf `127.0.0.1:5000`, die
Registrierung referenziert das Image über `"image-tag":"${APP_VERSION}"`, also über einen
verschiebbaren Tag. Die Doku bezeichnet die Registry als akzeptiert (T-02-32), begründet
das aber mit "listens on 127.0.0.1 only", was gegen lokale Schreibzugriffe nichts sagt.

**Angriffspfad:** Jeder lokale Prozess, auch ein npm- oder pip-Postinstall-Skript, kann
`docker push 127.0.0.1:5000/mcp_connector:0.1.0` ausführen. Beim nächsten Deploy zieht
der Daemon dieses Image und startet es mit `APP_SECRET` in der Umgebung und einem Volume.
Der Docker-Socket in HaRP (T-02-31) hebt den Schaden von "fremde ExApp" auf "root auf dem
Host".

**Fix:** Registry an einen Auth-Proxy hängen oder, einfacher und für einen Testaufbau
ausreichend, nach dem Push den Digest ermitteln und in der Registrierung verwenden:

```bash
DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "${ref}" | cut -d@ -f2)"
# ... "image-tag":"${APP_VERSION}@${DIGEST}" bzw. das von AppAPI unterstützte Digest-Feld
```

### WR-10: Die request-gelieferte User-ID fliesst ungequotet in den DAV-Search-Scope

**Datei:** `src/mcp_connector/nextcloud/clients/dav.py:198` gegen `:106,422`, `caldav.py:88`, `carddav.py:84`

**Befund:** `return f"/files/{creds.user}{suffix}"` ist die einzige Stelle, an der
`creds.user` ohne `quote(..., safe="")` in einen Pfad geschrieben wird. Alle anderen vier
Stellen quoten. In Phase 1 war das folgenlos, weil `creds.user` aus der Umgebung kam. Im
ExApp-Modus stammt der Wert aus `AUTHORIZATION-APP-API`, also aus dem Request.

**Angriffspfad:** Eine User-ID mit `/` oder `..` erzeugt einen Scope, der ausserhalb des
eigenen Home liegt (`/files/alice/../bob`). Nextcloud verbietet `/` in User-IDs, die
Kette hängt damit an einer Zusicherung einer fremden Komponente, und die Voraussetzung
(Kenntnis von `APP_SECRET`) ist ohnehin schwer. Reales Verhalten schon heute: User-IDs mit
Leerzeichen, die Nextcloud erlaubt, ergeben zwei unterschiedliche Pfadschreibweisen an
zwei Stellen desselben Requests.

**Fix:** `return f"/files/{quote(creds.user, safe='')}{suffix}"` und in
`parse_entries:422` dieselbe Schreibweise, damit `_home_path_of` weiter matcht (dort wird
`unquote` auf den href angewandt, also entweder beide Seiten quoten oder beide nicht,
aber konsistent).

### WR-11: Fest verdrahteter Default für `HP_SHARED_KEY` im eingecheckten Compose-File

**Datei:** `compose.exapp.yml:84`

**Befund:** `HP_SHARED_KEY: "${HP_SHARED_KEY:-nc-mcp-exapp-local-harp-key}"`. Der Default
steht im Repository und wird verwendet, wenn niemand die Variable exportiert, was der
dokumentierte Standardweg ist (`docker compose -f compose.exapp.yml up -d --wait`).
`bootstrap_exapp.sh:174-184` liest ihn danach aus dem Container zurück und schreibt ihn in
`.env.exapp`, wodurch die Schwäche unsichtbar wird.

**Angriffspfad:** Wer den FRP-Port von HaRP erreicht, kann sich mit diesem Key als ExApp
anmelden. Im vorliegenden Aufbau ist der Port nicht publiziert, das Risiko ist damit auf
Prozesse im Compose-Netz begrenzt. Der Punkt bleibt, weil der Kommentar
`export HP_SHARED_KEY="$(openssl rand -hex 32)"` optional ist und niemand ihn ausführt.

**Fix:** Default entfernen und `up` bewusst scheitern lassen
(`HP_SHARED_KEY: "${HP_SHARED_KEY:?export HP_SHARED_KEY=$(openssl rand -hex 32) first}"`)
oder den Key im Bootstrap vor dem `up` erzeugen.

### WR-12: Die Doku empfiehlt `APP_HOST=0.0.0.0` und widerspricht damit ihrer eigenen Loopback-Regel

**Datei:** `docs/exapp-install.md:185` gegen `docs/exapp-install.md:31-34`

**Befund:** Zeile 31 bis 34 begründet ausführlich, warum jeder Port an `127.0.0.1` gebunden
ist. Zeile 185 gibt dann `APP_PORT=23001 APP_HOST=0.0.0.0 nc-mcp-exapp` als
Entwicklungsschleife vor. `entry_exapp.py:93` würde ohne diese Vorgabe auf `127.0.0.1`
binden.

**Angriffspfad:** Zusammen mit CR-01 steht die unauthentifizierte MCP-Oberfläche damit dem
gesamten LAN des Entwicklungsrechners offen, `/heartbeat` ohnehin, und `/init` sowie
`/enabled` sind in diesem Modus ohne HaRP und ohne Manifest-Filter direkt erreichbar, also
nur noch durch `APP_SECRET` geschützt, das im selben Verzeichnis in `.env.exapp` liegt.

**Fix:** `APP_HOST` weglassen (Default ist bereits `127.0.0.1`) und, falls der Daemon aus
dem Container heraus zugreifen muss, entweder `host.docker.internal` mit einer expliziten
Bindung an die Docker-Bridge-IP dokumentieren oder einen SSH-/Socat-Tunnel.

### WR-13: Der Laufzeit-Nutzer darf seinen eigenen Code überschreiben

**Datei:** `Dockerfile:104`

**Befund:** `COPY --from=build --chown=10001:10001 /app/.venv /app/.venv`. Das gesamte
virtuelle Environment inklusive `site-packages` und der installierten
`mcp_connector`-Pakete gehört dem Prozessnutzer und ist für ihn schreibbar.

**Angriffspfad:** Jede Schwachstelle, die einen Dateischreibzugriff erlaubt, wird damit
von "einmalig" zu "persistent im Container": ein überschriebenes Modul läuft beim
nächsten Start mit `APP_SECRET` in der Umgebung. Der Container wird von AppAPI
neugestartet, nicht neu erzeugt.

**Fix:** Eigentum bei root lassen, Leserecht genügt:

```dockerfile
COPY --from=build /app/.venv /app/.venv
```

Schreibbar muss nur `/nc_app_mcp_connector_data`, `/certs` und `/frpc.toml` sein, und
genau diese drei sind bereits korrekt mit `0700` beziehungsweise `0600` angelegt.

---

## Info

### IN-01: `x-origin-ip` ist ein clientsetzbarer Header als Sicherheitskontrolle

**Datei:** `src/mcp_connector/exapp/lifecycle.py:44,101-102`

Mit `headers_to_exclude: []` (siehe WR-01) wird der Header nicht gestrippt. Die Richtung
des Missbrauchs ist heute harmlos (ein Angreifer kann sich damit nur selbst ein 404
verschaffen), aber eine Kontrolle, die der Gegenüber abschalten kann, ist keine Kontrolle.
Zweiter Effekt: setzt irgendein Intermediary in einer fremden Installation
`X-Origin-IP`, werden `/init` und `/enabled` von AppAPI mit 404 beantwortet und die App
lässt sich nicht mehr installieren. Vorschlag: den Header in `headers_to_exclude`
aufnehmen und die Prüfung als reine Defense-in-Depth beibehalten, mit Kommentar, dass sie
nicht tragend ist.

### IN-02: `_guard` fängt nur `AppApiRejected`, `exapp_settings` kann `ToolError` werfen

**Datei:** `src/mcp_connector/exapp/lifecycle.py:103-108`, `src/mcp_connector/exapp/auth.py:82`

`require_appapi` ruft `config.exapp_settings(env)`, das bei fehlendem `NEXTCLOUD_URL`,
`APP_ID`, `APP_SECRET` oder `APP_VERSION` `ToolError` wirft. `_guard` fängt das nicht, der
Fehler wird zu einem 500. `main` validiert die Umgebung beim Start, der Pfad ist also
praktisch tot, aber der Kommentar "no rejection can escape as a 500" stimmt nur für einen
der beiden Fehlertypen. Vorschlag: `except (AppApiRejected, ToolError)`.

### IN-03: Basis-Image nicht per Digest gepinnt, FRP-Checksummen als überschreibbare Build-Args

**Datei:** `Dockerfile:16,41,62-65`

`python:3.13-slim` ist ein bewegliches Tag, während uv per Version und frpc per sha256
gepinnt sind. Die Checksummen sind `ARG` und lassen sich mit
`--build-arg FRP_AMD64_SHA256=...` aushebeln, die Pinning-Aussage gilt also nur für
Builds, die niemand manipuliert. Vorschlag: Basis-Image per `@sha256:` pinnen, Checksummen
als Konstante im `RUN` statt als `ARG`.

### IN-04: `normalize_base_url` akzeptiert Userinfo in der URL, die dann geloggt wird

**Datei:** `src/mcp_connector/config.py:105-122`, `src/mcp_connector/exapp/status.py:60,64`

`https://admin:pw@cloud.example.com` besteht Schema- und Netloc-Prüfung. Der Wert landet
in `settings.base_url` und aus `status.py` in zwei `logger.error`-Zeilen mit voller URL.
Vorschlag: `if parts.username or parts.password: raise ToolError(...)`.

### IN-05: Jeder Bootstrap-Lauf legt neue App-Passwörter an und widerruft keine alten

**Datei:** `scripts/bootstrap_exapp.sh:156-169,368-370`

`user:auth-tokens:add` mit demselben Namen `mcp-exapp` erzeugt bei jedem Lauf ein weiteres
gültiges Token. Nach fünf Läufen existieren zehn gültige Zugänge, von denen nur zwei in
`.env.exapp` stehen. Vorschlag: vorhandene Tokens mit diesem Namen vorher per
`user:auth-tokens:delete` entfernen.

### IN-06: `json_info` baut JSON per String-Interpolation

**Datei:** `scripts/bootstrap_exapp.sh:254-258`

`"secret":"${APP_SECRET}"` und `"name":"${APP_NAME}"` werden ohne Escaping eingesetzt. Bei
einem generierten Hex-Secret unkritisch, bei einem handgepflegten `.env.exapp` mit
Anführungszeichen entsteht ungültiges oder manipuliertes JSON. Mit dem Fix aus CR-02
(Hex-Validierung) ist der Punkt für `APP_SECRET` erledigt.

### IN-07: `^/\.well-known/` ist ein unverankertes Praefix mit `access_level` PUBLIC

**Datei:** `appinfo/info.xml` (zweite Route), `scripts/bootstrap_exapp.sh:256`

Die Route ist heute unbedient: im ExApp-Modus baut das SDK ohne `auth` keine
`.well-known`-Routen, jeder Treffer endet in Starlettes 404. Zwei Anmerkungen. Erstens
wird damit vor Phase 3 unauthentifizierte Internet-Erreichbarkeit für einen Pfad
deklariert, den noch nichts verteidigt. Zweitens matcht das Praefix auch
`/.well-known/../mcp` auf PUBLIC-Niveau; heute rettet, dass Starlette Routen literal
vergleicht und Caddy Dot-Segments vorher entfernt, die Kontrolle hängt damit aber an der
Normalisierung fremder Komponenten. Vorschlag: bis Phase 3 die Route entfernen, danach eng
fassen, zum Beispiel `^/\.well-known/oauth-protected-resource$`.

### IN-08: Längenunterschied des Secrets bleibt über `compare_digest` beobachtbar

**Datei:** `src/mcp_connector/exapp/auth.py:86-88`

`secrets.compare_digest` auf Bytes unterschiedlicher Länge kehrt schnell zurück. Der
Inhalt leckt nicht, die Länge theoretisch schon. Für ein 64-Zeichen-Hex-Secret ohne
Bedeutung, hier nur zur Vollständigkeit des Prüfschwerpunkts 1 genannt. Keine Massnahme
empfohlen.

---

## Was geprüft wurde und sauber war

Damit der Bericht nicht mit Weglassungen missverstanden wird:

* **Timing und Echo im Handshake:** `_same` vergleicht ausschliesslich auf UTF-8-Bytes,
  kein `!=`, kein f-string mit Header-Werten, `AppApiRejected` trägt keine Nachricht,
  `raise ... from None` unterdrückt die Ursachenkette. Die Tests
  `test_no_rejection_ever_repeats_the_header` und
  `test_verification_writes_nothing_to_the_log` decken das ab.
* **Verwechslung `EX-APP-ID` gegen konfigurierte ID:** wird constant-time geprüft und
  führt zur selben leeren 401 wie ein falsches Secret.
* **Leere und fehlende Werte:** leere Header werden vor jeder Kryptografie abgelehnt, eine
  leere User-ID ist im Lifecycle erlaubt und beim Datenzugriff explizit verboten
  (`deps.py:162-169`).
* **Impersonation-Bindung:** kein Tool hat einen `user`-Parameter, `base_url` kommt nie aus
  dem Request, ein zusätzlicher `Authorization`-Header ändert nichts
  (`test_an_additional_basic_header_changes_nothing`).
* **Secrets in Repr und Logs:** `ExAppSettings.__repr__`, `Credentials.__repr__` und
  `AppApiAuth.__repr__` maskieren jeweils; der base64-Token taucht in keinem Repr auf.
* **Lifecycle-Erreichbarkeit:** `/init` und `/enabled` verlangen einen gültigen Handshake,
  `/heartbeat` ist vertragsgemäss offen und gibt nur `{"status":"ok"}` zurück, alle
  Antworten tragen `Cache-Control: no-store`. Die drei Pfade fehlen im Manifest, was der
  eigentlich tragende Schutz ist.
* **Replay von `/init`:** wiederholte Aufrufe pushen nur erneut `progress=100`, kein
  Zustandsschaden, kein 500 bei fehlgeschlagenem Push.
* **Secrets im Image:** `docker inspect` zeigt in `Config.Env` nur `PATH`, `GPG_KEY`,
  `PYTHON_VERSION`, `PYTHON_SHA256` und `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION`;
  `docker history --no-trunc` enthält keine Treffer für `APP_SECRET`, `HP_SHARED_KEY`,
  `password` oder `token`. `.dockerignore` schliesst `.git`, `.env*` und `.harp-certs` aus.
* **Non-root:** `USER=10001:10001` im Image bestätigt, `/certs`, das Datenverzeichnis und
  `/frpc.toml` sind mit `0700` beziehungsweise `0600` korrekt vorbereitet.
* **Ausgehende Verbindungen:** `shared_client()` nutzt `verify` im Default (also an) und
  `follow_redirects=False`, ein umleitender Nextcloud kann das Secret also nicht auf einen
  fremden Host ziehen.
* **Git-Hygiene:** `.env.exapp` und `.harp-certs/` sind ignoriert und nicht getrackt,
  `git status` ist sauber.
* **compose.test.yml:** nicht angefasst, die exapp-Topologie wurde nicht gestartet, alle
  Aussagen stammen aus statischer Prüfung plus dem bereits vorhandenen lokalen Image.

---

_Geprüft: 2026-08-15_
_Reviewer: Claude (gsd-code-reviewer), Modus deep, Security-only_
