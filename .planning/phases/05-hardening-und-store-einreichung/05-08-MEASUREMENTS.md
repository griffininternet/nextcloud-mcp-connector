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

## 9. Linie A: was der Remove-Knopf zurueckbehaelt

Offen. Der Install- und der Remove-Klick sind die zwei Schritte dieses Plans, die eine
Weboberflaeche brauchen (Task 2, Checkpoint).

## 10. Linie B: der occ-Weg, gegen die Zaehlbasis

Offen bis Linie A gemessen ist. Der Ablauf ist in 6.3 und 6.4 schon einmal gefahren und
belegt; die Zahlen des Beweislaufs gehoeren hierher.
