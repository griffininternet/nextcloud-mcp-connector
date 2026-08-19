# 05-08 Rohmessungen: Installation per Klick und Deinstallation mit Beweis

Alle Messungen am **19.08.2026** auf diesem Windows-Host (Git Bash), gegen die Topologie
`compose.exapp.yml` (Compose-Projekt `nc-mcp-exapp`). Die vom Owner genutzten Instanzen
`nc-mcp-test` und `findling-nextcloud` liefen die ganze Zeit weiter und wurden nicht
angefasst.

Gemessene Versionen dieses Laufs, nicht die angenommenen aus Assumption A1:

| Was | Wert | Kommando |
|-----|------|----------|
| Nextcloud | 34.0.2 (34.0.2.1) | `occ status` |
| AppAPI | 34.0.0 | `occ app:list` |
| Deploy Daemon | HaRP, `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | `occ app_api:daemon:list` |

Zwei Konventionen fuer dieses Protokoll:

* `occ` steht fuer `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen diese Datei verlangt `HP_SHARED_KEY`
  in der Umgebung (WR-11), und der messende Prozess hat mit diesem Schluessel nichts zu
  tun (dieselbe Lehre wie in 05-05).
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39).
  App-Passwoerter wurden in eine Datei ausserhalb des Repositories geschrieben und nur
  ueber Statuscodes ausgewertet.

---

## 1. Instanz ohne Vorgeschichte (19:29:27Z bis 19:29:50Z)

Vorher, auf dem Host:

```
$ docker volume ls --format '{{.Name}}'
5e8572fd9243a19864780cbce98a1091aa5e4dc90c4e1925e8936c835afdddac
503e06fb68d7796f3bc25e2c4da67394c308630109073f42613ed915edc500e6
2976177be82166d1e29cd64b5830e5d2d3e7babee2a0d28924eca173d2f7365a
findling-dev_nextcloud
nc-mcp-exapp_nextcloud-exapp-data
nc-mcp-exapp_registry-exapp-data
nc_app_mcp_connector_data
nextcloud-mcp-connector_nextcloud-test-data
```

Die drei Volumes der Wegwerf-Topologie sind weggeworfen worden, `nc_app_mcp_connector_data`
einzeln, weil es kein compose-Volume ist (der Deploy Daemon legt es an, `down -v` sieht es
nicht):

```
$ docker compose -f compose.exapp.yml down -v --remove-orphans
 Volume nc-mcp-exapp_registry-exapp-data Removed
 Volume nc-mcp-exapp_nextcloud-exapp-data Removed
$ docker volume rm nc_app_mcp_connector_data
nc_app_mcp_connector_data
$ docker volume ls --format '{{.Name}}'
5e8572fd9243a19864780cbce98a1091aa5e4dc90c4e1925e8936c835afdddac
503e06fb68d7796f3bc25e2c4da67394c308630109073f42613ed915edc500e6
2976177be82166d1e29cd64b5830e5d2d3e7babee2a0d28924eca173d2f7365a
findling-dev_nextcloud
nextcloud-mcp-connector_nextcloud-test-data
```

Danach `up -d --wait`: vier Container, alle healthy, Netz `nc-mcp-exapp-net` neu angelegt.
Das Volume aus den Phasen 3 und 4 mit seinen 84 Autorisierungen lebt in dieser Messung
nicht weiter; die Zahlen dieses Protokolls stammen ausschliesslich aus der frischen
Instanz.

```
$ occ status
  - installed: true
  - version: 34.0.2.1
  - versionstring: 34.0.2
$ occ app:list | grep app_api
  - app_api: 34.0.0
```

---

## 2. Kommt der Nextcloud-Container ausgehend ins Internet? (19:30:45Z)

Voraussetzung des echten Store-Weges, deshalb gemessen und nicht angenommen:

```
$ docker exec nc-mcp-exapp-nc curl -s -o /tmp/appapi_apps.json \
    -w '%{http_code} %{size_download}\n' https://apps.nextcloud.com/api/v1/appapi_apps.json
200 701820
$ grep -o 'mcp_connector' /tmp/appapi_apps.json | wc -l
4
```

Anonymer Manifest-Abruf gegen ghcr.io, aus demselben Container:

```
token length: 68
manifest status 200
```

Beide Voraussetzungen sind erfuellt: die Instanz sieht den Store, und sie kann das Image
ohne Anmeldung ziehen.

## 3. Was der Store fuer diese App listet (19:31Z)

Aus dem Dokument, das die Instanz gerade selbst geholt hat:

```
version=0.1.0
download=https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.0/mcp_connector-0.1.0.tar.gz
signature_len=684
```

Das Archiv ist aus dem Container erreichbar (`curl -IL` folgt auf
`release-assets.githubusercontent.com` und antwortet 200), und das Image liegt als
Multi-Arch-Index bereit:

```
$ docker buildx imagetools inspect ghcr.io/street1983nk/mcp_connector:0.1.0
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:37a4aa7928264a74cf9440595478405d606fc085e6f409d9f382e9a603c6f61e
  Platform: linux/amd64
  Platform: linux/arm64
```

**Der Ausgangspunkt der Messung, belegt statt behauptet:** die gelistete Version traegt den
Purge nicht.

```
$ git log -1 --format='%h %ci' v0.1.0
b0ac128 2026-08-19 13:11:00 +0200
$ git cat-file -e v0.1.0:src/mcp_connector/exapp/purge.py
fatal: path 'src/mcp_connector/exapp/purge.py' exists on disk, but not in 'v0.1.0'
$ git log --oneline v0.1.0..HEAD | wc -l
49
```

Das Store-Archiv laesst sich aus dem heutigen Manifest reproduzieren (Signatur nicht
abgedruckt):

```
$ bash scripts/build_store_release.sh
built: dist/mcp_connector-0.1.0.tar.gz
$ ls -l dist/
-rw-r--r-- 1 Student 197121 28763 Aug 19 21:49 mcp_connector-0.1.0.tar.gz
```

---

## 4. Variante B: der heutige Stand, installiert (19:32Z bis 19:35Z)

`bash scripts/bootstrap_exapp.sh` auf der frischen Instanz, gekuerzt auf die Zeilen, die
etwas belegen:

```
share folder /mcp-share-04d2eb7d6d: created
read-only share /mcp-share-04d2eb7d6d to bob: present (attempt 2)
image 127.0.0.1:5000/mcp_connector:0.1.0: built and pushed (sha256:45090f9f...)
image digest sha256:45090f9f...: unchanged since the push
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
ExApps:
mcp_connector (MCP Connector): 0.1.0 [enabled]
```

Die Fixture aus 05-03 ist mit demselben in `.env.exapp` festgehaltenen Suffix neu
entstanden, also ohne eine zweite Freigabe daneben.

```
$ occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.0 [enabled]

$ ex_apps (Auszug, per PDO gelesen)
mcp_connector | enabled=1 | port=23000 | status={"deploy":100,"init":100,...}

$ docker ps -a --filter name=nc_app_mcp_connector --format '{{.Names}} | {{.Status}} | {{.Image}}'
nc_app_mcp_connector | Up 28 seconds (healthy) | 127.0.0.1:5000/mcp_connector:0.1.0
```

## 5. Assumption A5, Punkt 1: das occ-Kommando ist da (19:35:34Z)

```
$ occ list | grep mcp_connector
 mcp_connector
  mcp_connector:purge   End every MCP connection of this instance: hand every Nextcloud app
                        password this app created back to Nextcloud, empty its database and
                        delete its encryption key. Run this before removing the app, because
                        removing the app does not do it.

$ occ mcp_connector:purge --help
Usage:
  mcp_connector:purge [options]
  mcp_connector:purge --force
Options:
      --force           Required. This cannot be undone: every connected assistant has to be
                        authorized again.
```

Damit ist Punkt 1 geschlossen: das Kommando wird beim `enabled=1`-Hook registriert, es steht
in `occ list`, und die Pflichtoption ist auf der AppAPI-Seite so deklariert, wie
`exapp/occ.py` sie meint.

---

## 6. Assumption A5, Punkt 2: die Draht-Form der Option, und zwei Fehler (19:38Z bis 19:47Z)

Punkt 2 war der eigentliche Zweck dieses Abschnitts, und er hat zwei Fehler aufgedeckt, die
kein Unit-Test finden konnte.

### 6.1 Ohne die Option passiert nichts (19:38:48Z)

```
$ occ mcp_connector:purge
{"purged":false,"hint":"Nothing was changed. This command ends every MCP connection of this
instance and cannot be undone, so it only runs with --force."}
```

Zeilen danach unveraendert (`authorizations: 2`, `clients: 2`, `refresh_tokens: 2`,
`access_tokens: 2`), beide App-Passwoerter weiter 200. Die Verweigerung wirkt.

### 6.2 Mit der Option passierte ebenfalls nichts, und das war der Fehler (19:39:06Z)

```
$ occ mcp_connector:purge --force
{"purged":false,"hint":"Nothing was changed. ..."}
```

Zeilen unveraendert, App-Passwoerter weiter 200, `MCP Connector:`-Eintraege weiter da. Genau
der Ausgang, den 05-06 als Risiko benannt hat: ein Admin haette danach deinstalliert und
geglaubt, die Credentials seien zurueckgegeben.

Die Ursache steht im Quelltext von AppAPI 34.0.0 auf der Instanz:

```
lib/Service/ExAppOccService.php  (buildCommand, execute)
  $this->service->exAppRequest($appid, $executeHandler,
      params: ['occ' => ['arguments' => $arguments, 'options' => $options]], ...)

lib/Service/AppAPIService.php  (prepareRequestToExApp)
  if ($method === 'GET') { $url .= '?' . http_build_query($params); }
  else { $options['json'] = $params; }
```

Der Rumpf eines echten Aufrufs ist also

```json
{"occ": {"arguments": null, "options": {"force": true}}}
```

und die Option liegt eine Ebene unter dem Kopf. `_forced` kannte acht Formen, aber keine
mit dieser Huelle. Fix in `exapp/purge.py`: `_forced_in` steigt genau eine Ebene in die
Huelle `occ` hinab, alle bisherigen Formen bleiben (Commit `505eaba`, fuenf neue
parametrisierte Faelle).

### 6.3 Der Purge lief, aber der Datenschluessel blieb (19:43:44Z)

Mit dem korrigierten Image, gegen die Zaehlbasis:

```
$ occ mcp_connector:purge --force
{"purged":true,"connections":2,"revoked":2,"revoke_failures":0,"tables_cleared":true,"key_deleted":false}
```

Gegenproben: alle sieben Tabellen 0, beide App-Passwoerter `HTTP 401, OCS 997`, kein
`MCP Connector:`-Eintrag mehr in beiden Geraetelisten. Aber `key_deleted: false`, und im
Container-Log:

```
ERROR mcp_connector.oauth.crypto: the deletion of the data key at
http://caddy/ocs/v2.php/apps/app_api/api/v1/ex-app/config answered 400
```

Ursache, wieder aus dem Quelltext der Instanz:

```
lib/Controller/AppConfigController.php
  public function deleteAppConfigValues(array $configKeys): DataResponse
```

Der Loesch-Zweig dieser Ressource nimmt eine **Liste** unter `configKeys`, nicht das
`configKey` der Schreibseite. Ein Rumpf mit `configKey` ist ein fehlendes Argument und wird
mit 400 beantwortet. Fix in `oauth/crypto.py`: `{"configKeys": [CONFIG_KEY]}`, und ein 404
dieser Route (`No appconfig_ex values deleted`, also null geloeschte Zeilen) gilt jetzt als
Erfolg statt als Fehler (Commit `872cb0b`).

### 6.4 Beide Korrekturen live nachgemessen (19:46:07Z)

```
$ occ mcp_connector:purge --force
{"purged":true,"connections":0,"revoked":0,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}
$ (oc_appconfig_ex fuer mcp_connector)
no config row of mcp_connector left
```

Damit ist Assumption A5 in beiden Punkten geschlossen: der Aufrufweg traegt, und die
Draht-Form ist gemessen statt geraten.

### 6.5 Nebenbefund: ein Purge im laufenden Prozess loest den Schluessel vom Chiffrat

Nach dem Purge aus 6.3 wurden zwei neue Verbindungen angelegt, ohne die App neu zu starten.
Sie liessen sich nicht mehr entschluesseln (`DecryptionRejected`): der Prozess hielt den
Schluessel, den er beim Start gelesen hatte, waehrend der Purge ihn in Nextcloud geloescht
hatte. Wer nach einem Purge weiterarbeitet, muss die App neu aktivieren, sonst haengt jede
danach entstandene Verbindung an einem Schluessel, den niemand mehr hat. Der Purge ist der
letzte Schritt vor dem Entfernen, und genau so steht er im Runbook.

Aufraeumen dieses Nebenbefundes: `unregister --rm-data`, danach neu installiert, danach die
Zaehlbasis neu erzeugt. Die zwei App-Passwoerter der verworfenen Runde blieben dabei als
Waisen in Nextcloud stehen (Ids 12 und 14), also genau der Zustand, den die falsche
Reihenfolge erzeugt: Credentials ohne jeden Datensatz, der sie erklaert. Sie wurden von Hand
mit `occ user:auth-tokens:delete <uid> <id>` entfernt.

---

## 7. Was ein `unregister` behaelt (19:42:30Z und 19:48:02Z)

Zwei Messungen derselben Frage, weil der Unterschied der ganze Punkt des Runbooks ist.

**Ohne `--rm-data`:**

```
$ occ app_api:app:unregister mcp_connector
ExApp mcp_connector successfully disabled.
ExApp mcp_connector successfully removed
ExApp mcp_connector successfully unregistered.
$ occ app_api:app:list
ExApps:
$ docker volume ls | grep nc_app_mcp_connector_data
nc_app_mcp_connector_data
$ docker ps -a | grep nc_app_mcp_connector
(kein Container)
$ (oc_appconfig_ex fuer mcp_connector)
still there: oauth_data_key
$ occ list | grep -c mcp_connector
0
```

Also: Registrierung weg, Container weg, occ-Kommando weg, **Volume und Datenschluessel
bleiben**. Eine Neuinstallation auf dasselbe Volume fand ihre zwei Verbindungen unveraendert
vor, und beide App-Passwoerter antworteten weiter mit 200.

**Mit `--rm-data`:**

```
$ occ app_api:app:unregister mcp_connector --rm-data
ExApp mcp_connector successfully unregistered.
$ docker volume ls | grep nc_app_mcp_connector_data
(Volume weg)
$ (oc_appconfig_ex fuer mcp_connector)
still there: oauth_data_key (324 bytes)
```

**Der Datenschluessel ueberlebt auch `--rm-data`.** Das ist keine Nebensache: ohne den Purge
bleibt ein sensitiv markierter Wert in `oc_appconfig_ex` stehen, und `occ config:app:get`
findet ihn nicht, weil er nicht in `oc_appconfig` liegt.

---

## 8. Die Zaehlbasis des echten Laufs (19:47:14Z bis 19:49:13Z)

Zwei Verbindungen ueber die vollstaendige Kette (Client, Caddy, HaRP, ExApp, Nextcloud), je
eine fuer `alice` und `bob`, mit dem Client-Halbteil von `scripts/oauth_flow_check.py` und
ohne dessen abschliessenden Widerruf:

```
[connect] POST /register -> 201 | cache_control=no-store | client_id=b3ebdfdf-a30...
connection established for alice: client id starts with b3ebdfdf
[connect] POST /register -> 201 | cache_control=no-store | client_id=cad1333c-d27...
connection established for bob: client id starts with cad1333c
count base: 2 connections, none of them ended
```

Zeilen je Tabelle, mit dem Einzeiler aus 05-RESEARCH (Wegwerf-Container, Volume read-only,
Kopie nach `/tmp`, weil sqlite3 eine read-only gemountete Datei nicht oeffnet):

```
$ docker run --rm -v nc_app_mcp_connector_data:/d:ro alpine:3 sh -c '...'
access_tokens: 2
auth_codes: 2
authorizations: 2
clients: 2
flows: 0
refresh_tokens: 2
user_access: 0
```

Die Nextcloud-App-Passwoerter, die diese App angelegt hat:

```
$ occ user:auth-tokens:list alice
| 18 | MCP Connector: Count base one | 2026-08-19T19:48:55+00:00 | permanent | filesystem |
$ occ user:auth-tokens:list bob
| 20 | MCP Connector: Count base two | 2026-08-19T19:48:56+00:00 | permanent | filesystem |
```

Beide sind gueltig, und die Instanz bestaetigt fuer jedes die richtige Identitaet:

```
count base: app password 1 of alice -> HTTP 200, OCS 200, identity 'alice'
count base: app password 2 of bob -> HTTP 200, OCS 200, identity 'bob'
```

Der Datenschluessel dieser Installation:

```
oauth_data_key | value length 324 | sensitive=1
```

Damit ist jede spaetere Aussage "es ist weg" pruefbar: zwei Autorisierungen, zwei gueltige
App-Passwoerter mit belegter Identitaet, sieben Tabellen mit bekannten Zahlen, ein
Datenschluessel, ein laufender Container, eine Registrierung.

---

## 9. Der Klick, den es nicht gibt (20:00Z bis 20:12Z, Browser)

Der Checkpoint-Lauf im Browser (Playwright, Konto `admin`) hat die zwei Klicks nicht
gefunden, und diese Abweichung ist selbst die Messung.

### 9.1 Kein ExApp erscheint in der Store-Oberflaeche von Nextcloud 34.0.2

Suche nach "MCP Connector" auf der Apps-Seite: null Treffer. Suche nach "mcp": nur eine
regulaere App. Kategorie "Einbindung" (174 Zeilen): kein `mcp_connector`. Und der Befund ist
nicht auf diese App beschraenkt: **kein einziges ExApp** erscheint, `context_agent`,
`visionatrix` und `stt_whisper2` fehlen genauso. `OCS /apps/appstore/api/v1/apps` liefert
694 Apps mit `exappCount=0`.

Die Kette, jeder Punkt geprueft:

1. **Der Cache ist in Ordnung.** `appapi_apps.json` in der Instanz enthaelt `mcp_connector`
   0.1.0 mit `platform >=32.0.0 <35.0.0`, insgesamt 24 ExApps.
2. **Das Backend ist in Ordnung.** `GET /index.php/apps/app_api/apps/list` liefert
   `{id: mcp_connector, version: 0.1.0, canInstall: true}`, die Initial-States melden
   `appApiEnabled=true` und `defaultDaemonConfigAccessible=true`.
3. **Das Frontend fragt nie.** Die neue App `appstore` 1.0.0 fuellt ihre Liste allein aus dem
   Core-AppFetcher und setzt das Merkmal hart auf false:

   ```
   $ grep -n 'AppFetcher\|app_api' apps/appstore/lib/Controller/ApiController.php
   14: use OC\App\AppStore\Fetcher\AppFetcher;
   52:   private readonly AppFetcher $appFetcher,
   383:  $apps = $this->appFetcher->get();
   459:  'app_api' => false,
   ```

   Im ausgelieferten Bundle exportiert der External-Apps-Store zwar ein `initialize`, aber
   das Wort kommt im ganzen Bundle genau einmal vor, naemlich in der Definition. Es wird nie
   aufgerufen, und das Netzwerk-Log bestaetigt es: `/apps/app_api/apps/list` wurde von der
   Oberflaeche nie geholt, nur vom manuellen Abruf der Messung.
4. **Die alte ExApps-Seite von AppAPI ist tot.** Die Route steht noch, die Methode ist weg:

   ```
   $ curl /index.php/apps/app_api/apps
   HTTP 500  "Method ExAppsPageController::viewApps() does not exist"
   $ grep -n viewApps apps/app_api/appinfo/routes.php
   45: ['name' => 'ExAppsPage#viewApps', 'url' => '/apps/{category}', ...]
   ```

**Und eine installierte ExApp erscheint genauso nicht.** Gegenprobe mit der laufenden,
aktivierten App:

```
$ occ app:list | grep -c mcp_connector
0
```

Der Core-App-Manager kennt eine ExApp nicht, und die Liste der Oberflaeche kommt aus ihm.
Damit gibt es auf dieser Version weder einen Install- noch einen Remove-Knopf fuer diese
Klasse von Apps. Kein passendes Upstream-Issue gefunden; Kandidat fuer einen eigenen
Bericht.

### 9.2 Linie 0: der Install-Aufruf des Knopfes, von Hand gefahren

Statt des Knopfes derselbe Aufruf, den das Bundle machen wuerde:

```
$ POST /index.php/apps/app_api/apps/enable/mcp_connector/harp_proxy_docker
  body: {"deployOptions": {}}
HTTP 500 nach 106,5 s
{"data":{"message":"Fehler beim Starten der Installation von ExApp"}}
```

Kein Dialog, keine Frage nach Umgebungsvariablen, wie die Recherche es fuer genau einen
konfigurierten Docker-Daemon vorhergesagt hat. Der Container wurde deployt und starb dann in
einer Schleife:

```
$ docker ps -a --filter name=nc_app_mcp_connector
nc_app_mcp_connector | Restarting (2) 47 seconds ago | ghcr.io/street1983nk/mcp_connector:0.1.0
$ docker inspect nc_app_mcp_connector
RestartCount=12 ExitCode=2 Restarting=true
NC_MCP_PUBLIC_URL rows in the container environment: 0
$ docker logs nc_app_mcp_connector | tail -1
ERROR mcp_connector.entry_exapp: NC_MCP_PUBLIC_URL is not set. The authorization server
calls itself by it: without it every discovery document, the audience of every token and the
consent redirect name http://127.0.0.1:8765, and no client can connect.
$ occ app_api:app:list
ExApps:
$ (oc_ex_apps)
no row in oc_ex_apps
```

Das ist Pitfall 2 der Recherche in einer Zeile: die Ein-Klick-Installation liefert keine
`NC_MCP_PUBLIC_URL`, und die veroeffentlichte Version 0.1.0 beendet sich in diesem Fall mit
Exit 2. Die Plaene 05-01 und 05-04 haben genau das behoben (Fehlerzeile plus sichtbarer
Setup-Zustand statt Abbruch), und der getaggte Release traegt den Fix nicht. Das ist das
staerkste Argument fuer 0.1.1 in Plan 05-10.

Die Zaehlbasis im Volume hat den Fehl-Deploy unberuehrt ueberlebt (`authorizations: 2`,
beide App-Passwoerter 200). Aufgeraeumt mit `docker rm -f nc_app_mcp_connector`, weil nie
eine Registrierung entstanden war, danach der heutige Stand per Bootstrap installiert.

---

## 10. Linie A: was der Remove-Weg zurueckbehaelt (20:14:16Z)

Weil kein Knopf existiert, wurde der Weg gefahren, den der Knopf laut Recherche nimmt, und
die Gleichheit ist aus dem Quelltext der Instanz belegt:

```
$ grep -n 'apps/disable' apps/app_api/appinfo/routes.php
42: ['name' => 'ExAppsPage#disableApp', 'url' => '/apps/disable/{appId}', 'verb' => 'GET']
$ apps/app_api/lib/Controller/ExAppsPageController.php:383
      if (!$this->service->disableExApp($exApp)) {
$ apps/app_api/lib/Command/ExApp/Disable.php:46
      if ($this->service->disableExApp($exApp)) {
```

Route und occ-Kommando rufen dieselbe Methode desselben Dienstes. Gemessen wurde also
`occ app_api:app:disable mcp_connector`, und das Ergebnis gilt fuer den Knopf genauso, weil
dazwischen kein Code liegt.

```
$ occ app_api:app:disable mcp_connector
ExApp mcp_connector successfully disabled.
```

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| A.1 | `docker volume ls \| grep '^nc_app_mcp_connector_data$'` | `nc_app_mcp_connector_data`, das Volume liegt da |
| A.2 | Zeilen je Tabelle | `access_tokens 2, auth_codes 2, authorizations 2, clients 2, flows 0, refresh_tokens 2, user_access 0`, unveraendert gegen die Zaehlbasis |
| A.3 | `occ app_api:app:list` | `mcp_connector (MCP Connector): 0.1.0 [disabled]`, weiter registriert; `oc_ex_apps` traegt `enabled=0` |
| A.4 | `docker ps -a` | `nc_app_mcp_connector \| Exited (0) 3 seconds ago`, der Container existiert weiter |
| A.5 | ExApp-Konfiguration | `oauth_data_key \| value length 324 \| sensitive=1`, der Datenschluessel steht noch da |
| A.6 | jedes vor dem Entfernen angelegte App-Passwort gegen `/ocs/v2.php/cloud/user` | `HTTP 200, OCS 200, identity 'alice'` und `HTTP 200, OCS 200, identity 'bob'` |
| A.7 | `occ user:auth-tokens:list` | `MCP Connector: Count base one` (Id 18) und `... two` (Id 20) weiter in den Geraetelisten |
| A.8 | `occ list \| grep -c mcp_connector` | **0** |

A.6 ist der harte Teil und der Kern von T-05-36: die App ist entfernt, ihr Container ist aus,
und zwei Nextcloud-Konten sind ueber Credentials erreichbar, die diese App angelegt hat.

A.8 ist der Befund, den kein Plan vorhergesehen hat: **mit dem Deaktivieren verschwindet das
Kommando, das aufraeumen koennte.** Wer erst entfernt und dann aufraeumen will, muss die App
zuerst wieder aktivieren. Das gehoert als Schritt 0 ins Runbook.

---

## 11. Linie B: der occ-Weg, gegen dieselbe Zaehlbasis (20:14:43Z bis 20:15:33Z)

### Schritt 0, aus A.8 gelernt

```
$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.0 [enabled]
$ occ list | grep -c mcp_connector:purge
1
$ docker ps | grep nc_app_mcp_connector
nc_app_mcp_connector | Up 11 seconds (healthy)
```

Zaehlbasis vor dem Purge: sieben Tabellen wie oben, beide App-Passwoerter 200.

### Schritt 1: der Purge

```
$ occ mcp_connector:purge --force
{"purged":true,"connections":2,"revoked":2,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}
```

| Nr | Gegenprobe | Ergebnis |
|----|------------|----------|
| B.1 | jedes vorher gueltige App-Passwort gegen `/ocs/v2.php/cloud/user` | `HTTP 401, OCS 997` fuer beide, keine Identitaet mehr |
| B.2 | alle sieben Tabellen | je `0` |
| B.3 | ExApp-Konfiguration | `no config row of mcp_connector left` |
| B.4 | Geraetelisten | `alice: 0`, `bob: 0` Eintraege mit dem Praefix |

### Schritt 2: das Entfernen mit den Daten

```
$ occ app_api:app:unregister mcp_connector --rm-data
ExApp mcp_connector successfully disabled.
ExApp mcp_connector successfully removed
ExApp mcp_connector successfully unregistered.
```

| Nr | Gegenprobe | Ergebnis |
|----|------------|----------|
| B.5 | `docker volume ls \| grep '^nc_app_mcp_connector_data$'` | keine Zeile |
| B.6 | `occ app_api:app:list \| grep mcp_connector` | keine Zeile |
| B.7 | `docker ps -a \| grep '^nc_app_mcp_connector$'` | keine Zeile |
| B.8 | `oc_appconfig_ex` und `oc_ex_apps` | keine Zeile fuer diese App, keine Zeile in `oc_ex_apps` |
| B.9 | `occ user:setting alice`, beide Geraetelisten | keine Zeile mit dem Praefix |
| B.10 | `occ list \| grep -c mcp_connector` | 0 |
| B.11 | `docker images \| grep mcp_connector` | `127.0.0.1:5000/mcp_connector:0.1.0 330MB` und `ghcr.io/street1983nk/mcp_connector:0.1.0 330MB` bleiben liegen |

B.11 ist die einzige Zeile, die nach dem occ-Weg noch von dieser App erzaehlt: das gezogene
Image im Image-Store des Docker-Daemons. Es enthaelt keine Instanzdaten und ist ein Thema
von Plattenplatz, nicht von Datenschutz. Das Runbook nennt es trotzdem.

**Damit ist Erfolgskriterium 2 in beiden Richtungen belegt:** der UI-Weg behaelt Volume,
Zeilen, Datenschluessel, Container, Registrierung und jedes App-Passwort; der occ-Weg
behaelt nichts davon.
