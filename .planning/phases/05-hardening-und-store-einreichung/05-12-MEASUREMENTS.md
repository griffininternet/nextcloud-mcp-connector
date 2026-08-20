# 05-12 Rohmessungen: warum der Startzeit-Lesevorgang der Admin-Werte 401 bekommt

Alle Messungen am **20.08.2026** zwischen 03:44Z und 03:52Z auf diesem Windows-Host (Git
Bash), gegen die Wegwerf-Topologie `compose.exapp.yml` (Compose-Projekt `nc-mcp-exapp`).
Die vom Owner genutzten Instanzen `nc-mcp-test` und `findling-nextcloud` liefen die ganze
Zeit weiter, wurden in keinem Kommando dieses Laufs genannt und nicht angefasst (T-05-46).

Der gemessene Stand ist HEAD nach Plan 05-11, also App-Version 0.1.1 mit der
https-oder-Loopback-Regel und dem Rettungszweig in `entry_exapp`.

## 1. Gemessene Versionen und Aufbau

| Was | Wert | Kommando |
|-----|------|----------|
| Nextcloud | 34.0.2 (34.0.2.1) | `occ status` |
| AppAPI | 34.0.0 | `occ app:list` |
| Deploy Daemon | HaRP, `harp_proxy_docker`, `docker-install` | `occ app_api:daemon:list` |
| App | `mcp_connector (MCP Connector): 0.1.1 [enabled]` | `occ app_api:app:list` |

Zwei Konventionen fuer dieses Protokoll, wie in 05-08:

* `occ` steht fuer `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen diese Datei verlangt `HP_SHARED_KEY`
  in der Umgebung (WR-11), und der messende Prozess hat mit diesem Schluessel nichts zu tun.
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-45). Von
  jeder Anfrage stehen hier nur Zieladresse, Statuscode und Antwortkoerper; kein Header
  wird abgedruckt, und der Antwortkoerper der gemessenen Ressource traegt ausschliesslich
  die vier Admin-Schluessel dieser App, kein Geheimnis.

Frischer Aufbau vor der ersten Messung, wie 05-08 ihn beschreibt:

```
$ docker compose -f compose.exapp.yml down -v --remove-orphans
 Volume nc-mcp-exapp_nextcloud-exapp-data Removed
 Volume nc-mcp-exapp_registry-exapp-data Removed
$ docker volume rm nc_app_mcp_connector_data
Error response from daemon: get nc_app_mcp_connector_data: no such volume
$ docker compose -f compose.exapp.yml up -d --wait      # 03:44:34Z bis 03:45:09Z
$ bash scripts/bootstrap_exapp.sh                       # 03:45:14Z bis 03:46:36Z
image 127.0.0.1:5000/mcp_connector:0.1.1: built and pushed (sha256:3c504faa...)
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
ExApps:
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Der Zustand, gegen den gemessen wird:

```
$ occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.1 [enabled]
$ (oc_ex_apps, per PDO gelesen)
mcp_connector | enabled=1 | port=23000 | {"deploy":100,"init":100,"action":"","type":"","error":"",...}
$ docker inspect nc_app_mcp_connector
/nc_app_mcp_connector running unless-stopped 0 0 2026-08-20T03:46:24.540249364Z
  id 2d30cc5f3777a79e81270c454309c6d676db13819b2bf651a3e8764371eef92c
```

**Der Ausgangsbefund ist reproduziert.** Im Log des allerersten Starts dieses frisch
deployten Containers (03:46:24Z), also genau die Zeile aus `deferred-items.md`:

```
$ docker logs nc_app_mcp_connector | head -30
...
ERROR mcp_connector.exapp.config_values: Nextcloud answered 401 when the admin values were read, the environment stays
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
INFO:     Application startup complete.
```

## 2. M1: der Kanal bei aktivierter, laufender App (03:47:26Z und 03:48:07Z)

Der Lesevorgang genau einmal, aus dem App-Container heraus, mit dem Interpreter der
Container-venv (`/app/.venv/bin/python`) und mit den Headern des Produktionscodes
(`config_values._headers(config.exapp_settings(env))`, `env=dict(os.environ)`):

```
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python - < m1_probe.py
M1 url: http://caddy/ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values
M1 status: 200
M1 body: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":[]}}
M1 read_values keys: []
M1 read_values count: 0
```

200, aber mit leerer Liste, weil kein Admin-Wert gesetzt war. Ein leeres Ergebnis belegt
noch nicht, dass ein gesetzter Wert auch ankommt, deshalb ein Wert gesetzt und dieselbe
Messung wiederholt:

```
$ occ app_api:app:config:set mcp_connector oauth_dcr --value 1
ExApp mcp_connector config oauth_dcr set to 1
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python - < m1_probe.py
M1 status: 200
M1 body: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":[{"configkey":"oauth_dcr","configvalue":"1"}]}}
M1 read_values keys: ['oauth_dcr']
M1 read_values count: 1
```

`oauth_dcr` ist der harmloseste der vier Schluessel: `1` ist genau der Default aus
`registry.client_policy` (`dcr_enabled=True`), das Verhalten der laufenden App aendert sich
durch den Testwert also nicht. Der Wert wurde am Ende des Laufs wieder entfernt (Abschnitt
6).

**M1 = 200, und ein gesetzter Wert kommt vollstaendig zurueck.**

## 3. M2: blosser Container-Neustart bei aktivierter App (03:48:15Z bis 03:48:28Z)

```
$ docker restart nc_app_mcp_connector
nc_app_mcp_connector
$ docker inspect nc_app_mcp_connector
id=2d30cc5f3777... status=running started=2026-08-20T03:48:16.360289104Z restartcount=0
$ docker logs --since 60s nc_app_mcp_connector
INFO mcp_connector.entry_exapp: these values come from the administration settings of this app and win over the deploy environment: NC_MCP_OAUTH_DCR
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

**Keine 401-Zeile.** Stattdessen die INFO-Zeile ueber den gewonnenen Admin-Wert: der
Startzeit-Lesevorgang gelingt, und der Wert aus dem Formular wirkt nach einem einfachen
Container-Neustart.

## 4. M3: der Disable/Enable-Zyklus (03:48:47Z bis 03:49:14Z)

Vor und nach jedem Schritt `docker inspect` auf Id, Status, StartedAt und RestartCount:

```
T 03:48:47Z vor disable
id=2d30cc5f3777... status=running  started=2026-08-20T03:48:16.360289104Z restartcount=0 exit=0

$ occ app_api:app:disable mcp_connector
ExApp mcp_connector successfully disabled.

T 03:48:50Z nach disable
id=2d30cc5f3777... status=exited   started=2026-08-20T03:48:16.360289104Z
                 finished=2026-08-20T03:48:50.724945947Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [disabled]

T 03:48:58Z vor enable
id=2d30cc5f3777... status=exited   restartcount=0 exit=0

$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.

T 03:49:06Z nach enable
id=2d30cc5f3777... status=running  started=2026-08-20T03:49:00.660582396Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Der Zyklus schaltet also nicht nur Routen um: er **stoppt und startet denselben Container**
(gleiche Id, neues StartedAt, sauberer Exit 0). `RestartCount` bleibt dabei 0, weil das ein
Zaehler der Restart-Policy ist und nicht der Stopps und Starts von aussen.

Die Logpruefung dieses Starts:

```
$ docker logs --since 2026-08-20T03:48:55Z nc_app_mcp_connector
INFO mcp_connector.entry_exapp: these values come from the administration settings of this app and win over the deploy environment: NC_MCP_OAUTH_DCR
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

**Auch hier keine 401-Zeile.** Der erneute M1-Aufruf direkt nach der Rueckkehr von `enable`:

```
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python - < m1_probe.py   # 03:49:14Z
M1 status: 200
M1 body: {"ocs":...,"data":[{"configkey":"oauth_dcr","configvalue":"1"}]}
M1 read_values count: 1
```

### 4.1 M3b: derselbe Container, gestartet waehrend die App deaktiviert ist (03:49:37Z)

M2 und M3 zeigen die 401-Zeile nicht, der erste Start nach dem Deploy zeigt sie. Der einzige
Unterschied zwischen diesen Zeitpunkten ist der Aktivierungszustand, also wurde genau er
isoliert: die App bleibt `disabled`, und der Container wird von Hand gestartet.

```
$ occ app_api:app:disable mcp_connector
ExApp mcp_connector successfully disabled.
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [disabled]
$ docker start nc_app_mcp_connector          # 03:49:38Z, App bleibt disabled
nc_app_mcp_connector
$ docker inspect nc_app_mcp_connector
status=running started=2026-08-20T03:49:38.737226079Z restartcount=0
$ docker logs --since 2026-08-20T03:49:38Z nc_app_mcp_connector
ERROR mcp_connector.exapp.config_values: Nextcloud answered 401 when the admin values were read, the environment stays
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

**Die 401-Zeile ist zurueck**, bei sonst identischem Container, identischem Secret und
identischem Kanal.

### 4.2 M3c: derselbe Lesevorgang aus dem laufenden Container, App deaktiviert (03:50:01Z)

Damit der Unterschied nicht nur eine Logzeile ist, sondern ein Statuscode:

```
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python - < m1_probe.py
M1 url: http://caddy/ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values
M1 status: 401
M1 body: {"ocs":{"meta":{"status":"failure","statuscode":997,"message":"AppAPI authentication failed"},"data":[]}}
M1 read_values keys: []
M1 read_values count: 0
```

Gleiche Adresse, gleiche Header, gleicher Prozess, gleicher Zeitpunkt im Prozessleben wie
in M1. Einziger Unterschied: `enabled=0`. Danach wieder aktiviert:

```
$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

### 4.3 Die Gegenprobe im Quelltext der laufenden Instanz

Der Befund steht woertlich in AppAPI 34.0.0 auf dieser Instanz:

```
$ (nc-mcp-exapp-nc) apps/app_api/lib/Middleware/AppAPIAuthMiddleware.php:47-50
      if (!$this->request->getHeader('AUTHORIZATION-APP-API')) { throw ... STATUS_UNAUTHORIZED }
      if (!$this->service->validateExAppRequestToNC($this->request)) { throw ... STATUS_UNAUTHORIZED }

$ apps/app_api/lib/Service/AppAPIService.php:305-317  (validateExAppRequestToNC)
      $authValid = $authorizationSecret === $exApp->getSecret();
      if ($authValid) {
          ...
          if (!$exApp->getEnabled() && !$this->isExemptFromEnabledCheck($path, $exApp)) {
              $this->logger->error(sprintf('ExApp with appId %s is disabled (%s)', ...));
              return false;
          }

$ apps/app_api/lib/Service/AppAPIService.php:379-390  (isExemptFromEnabledCheck)
      if ($sanitizedPath === '/apps/app_api/ex-app/state') { return true; }
      $isInitializing = in_array($status['type'] ?? '', ['install', 'update'], true);
      if ($isInitializing && $sanitizedPath === '/apps/app_api/ex-app/status') { return true; }
      return false;
```

Das Secret ist gueltig (`$authValid` ist wahr), und trotzdem faellt die Anfrage durch, weil
`enabled` nicht gesetzt ist. Ausgenommen sind genau zwei Pfade, `ex-app/state` und, nur
waehrend `install` oder `update`, `ex-app/status`. Der Konfigurationspfad
`ex-app/config/get-values` ist **nicht** darunter und kann es auch nicht werden, ohne dass
AppAPI geaendert wird.

## 5. M4: das Neustartverhalten des Deploy-Daemon-Containers (03:51:20Z bis 03:51:36Z)

```
$ docker inspect -f '{{.HostConfig.RestartPolicy.Name}} {{.HostConfig.RestartPolicy.MaximumRetryCount}}' nc_app_mcp_connector
unless-stopped 0
```

**Die Restart-Policy heisst `unless-stopped`, mit MaximumRetryCount 0.** Was das praktisch
bedeutet, wurde nicht aus der Docker-Dokumentation abgeschrieben, sondern gemessen: das
Hauptprozessende von innen (`kill -TERM 1`), also die Form, die ein geordneter
Selbstneustart der App haette.

```
T 03:51:20Z vorher:  status=running restartcount=0 started=2026-08-20T03:49:38.737226079Z
$ docker exec nc_app_mcp_connector sh -c 'kill -TERM 1'
T 03:51:36Z nachher: status=running restartcount=1 started=2026-08-20T03:51:21.556587342Z exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Der Container kommt nach einem selbst herbeigefuehrten Prozessende **von allein zurueck**
(`RestartCount` 0 nach 1, neues StartedAt, App bleibt registriert und aktiviert), und der
Start danach liest die Admin-Werte sauber:

```
$ docker logs --since 2026-08-20T03:51:20Z nc_app_mcp_connector
INFO mcp_connector.entry_exapp: these values come from the administration settings of this app and win over the deploy environment: NC_MCP_OAUTH_DCR
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

Der Gegensatz zu M3 ist die zweite Haelfte der Aussage: ein `disable`, das den Container
ueber die Docker-API stoppt, laesst ihn liegen, denn genau das heisst `unless-stopped`.

## 6. Zustand der Topologie am Ende des Laufs

Der Testwert wurde wieder entfernt, damit spaetere Plaene eine neutrale Instanz vorfinden.
Der Loeschpfad braucht `configKeys` als Liste, das occ-Kommando erledigt das:

```
$ occ app_api:app:config:delete mcp_connector oauth_dcr
ExApp mcp_connector config oauth_dcr deleted.
$ occ app_api:app:config:list mcp_connector
ExApp mcp_connector configs:
[]
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
$ docker inspect -f '{{.Name}} {{.State.Status}} {{.HostConfig.RestartPolicy.Name}}' nc_app_mcp_connector
/nc_app_mcp_connector running unless-stopped
$ git status --porcelain src tests scripts
(leer)
```
