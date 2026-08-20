# 06-07 Messprotokoll: 34.0.3, Repository-Stand und der Blick in die Store-Oberfläche

Datum des Laufs: **2026-08-20, 14:15 bis 14:21 UTC** (Task 1), Fortsetzung im Abschnitt 6.
Rechner: der Entwicklungsrechner aus 06-RESEARCH.md, Abschnitt "Environment Availability"
(Windows-Host, Git Bash). Alles unten ist aus einem Lauf, nicht aus dem Quellcode
abgeleitet; wo eine Aussage aus dem Quellcode kommt, steht das dabei.

Drei Konventionen für dieses Protokoll:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen `compose.exapp.yml` verlangt
  `HP_SHARED_KEY` in der Umgebung (WR-11), und der messende Prozess hat mit diesem
  Schlüssel nichts zu tun (Lehre aus 05-05, fortgeschrieben in 05-08).
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39). Der
  Pfad der Volume-Sicherung steht hier, ihr Inhalt nicht.
* Die Version einer Instanz ist immer die Zeile aus `occ status`, nie ein Docker-Tag
  (Pitfall 6). Deshalb nennt die Tabelle unten Versionen und Digests.

## Topologie des Laufs (Nachzustand)

| Was | Wert |
|-----|------|
| Compose-Datei, Projekt | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | **34.0.3 (34.0.3.2)** laut `occ status`; Image-Id `sha256:365baea128b5e0f45a8dc5111c9234b926f1e6082b4c14d75ae650324ce5d65c` |
| AppAPI, appstore | `app_api` 34.0.0, `appstore` 1.0.0 (`occ app:list`), unverändert über das Upgrade |
| Deploy Daemon | HaRP, `harp_proxy_docker`, `ghcr.io/nextcloud/nextcloud-appapi-harp:release` |
| Connector | `mcp_connector` **0.1.2 [enabled]** laut `occ app_api:app:list`; Image `127.0.0.1:5000/mcp_connector:0.1.2`, Digest `sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed`, `RestartCount` 0 |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| Demo-Substanz | Nutzer `jane` (Jane Fischer), zwei nicht widerrufene OAuth-Verbindungen, Fixture aus 05-03 (Suffix unverändert) |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberührt (kein Kommando dieses Laufs nennt sie; `docker ps` belegt beide mit "Up 5 days") |

---

## 1. Vorzustand, vor jeder Änderung (14:15:17Z)

Die Instanz lief hinter dem gleitenden Tag `34-apache` und trug 34.0.2.1, der Connector war
die Store-Fassung 0.1.1 ohne die Teilregistrierung aus a80af0a und ohne alles aus 06-01 bis
06-06:

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-08-20T14:15:17Z
$ occ status
  - installed: true
  - version: 34.0.2.1
  - versionstring: 34.0.2
$ occ app:list | grep -E "app_api|appstore"
  - app_api: 34.0.0
  - appstore: 1.0.0
$ occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.1 [enabled]
$ docker inspect nc-mcp-exapp-nc --format '{{.Config.Image}} {{.Image}}'
nextcloud:34-apache sha256:3323e178371b1b0d03f9b3fdbe1831ff78335f07f25116d0d598048ce459e329
$ docker inspect nc_app_mcp_connector --format '{{.Config.Image}} {{.Image}}'
127.0.0.1:5000/mcp_connector:0.1.1 sha256:92602ca154a23a89b8ac15b3c5cf3268c458e50d5b169a9cd6af4fa40f792e4c
```

Die Demo-Substanz, die das Upgrade überleben musste, vorher gezählt:

```
$ occ user:list
  - admin: admin
  - alice: alice
  - bob: bob
  - jane: Jane Fischer
$ docker exec nc_app_mcp_connector /app/.venv/bin/python -c "<Zeilen zaehlen>"
clients 2
authorizations 2
refresh_tokens 2
[('jane', 'c06831e2-36ee-48f9-a99c-d091b3013311', None), ('jane', '7256ad37-7670-4621-ba02-021e835fd372', None)]
```

Die dritte Spalte ist `revoked_at`: beide Verbindungen waren gültig, nicht widerrufen.

## 2. Volume-Sicherung vor dem Upgrade (14:16 bis 14:17Z)

Assumption A5 (In-Place-Upgrade innerhalb der Minor-Linie ohne Verlust von `jane` und den
zwei Verbindungen) war plausibel, aber auf dieser Topologie nicht gemessen. Gesichert wurde
per Wegwerf-Container mit `tar`, in ein Verzeichnis **außerhalb des Repositories**:

```
$ docker run --rm -v "<volume>:/src:ro" -v "<backup-dir>:/backup" alpine:3 \
    tar czf "/backup/<volume>.tgz" -C /src .
backed up nc-mcp-exapp_nextcloud-exapp-data
backed up nc_app_mcp_connector_data
```

| Sicherung | Größe |
|-----------|-------|
| `C:/Users/Student/nc-mcp-exapp-backup-20260820/nc-mcp-exapp_nextcloud-exapp-data.tgz` | 591 309 590 Bytes |
| `C:/Users/Student/nc-mcp-exapp-backup-20260820/nc_app_mcp_connector_data.tgz` | 2 749 Bytes (trägt `oauth.sqlite3` mit den zwei Verbindungen) |
| `C:/Users/Student/nc-mcp-exapp-backup-20260820/appconfig_ex-mcp_connector.jsonl` | 2 Zeilen, die ExApp-Konfiguration dieser App |

Die dritte Datei ist nicht vom Plan verlangt, sondern aus Abschnitt 5 entstanden: der
Datenschlüssel der Verbindungen liegt nicht im ExApp-Volume, sondern in
`oc_appconfig_ex` der Instanz, und die Neuregistrierung berührt genau diese Tabelle. Ihr
Inhalt steht nirgends in diesem Dokument.

## 3. Der Image-Pin (`compose.exapp.yml`)

```
$ grep -c "34.0.3-apache" compose.exapp.yml
1
$ grep -c "nextcloud:34-apache" compose.exapp.yml
0
```

Der Kommentar an der Zeile sagt, warum hier eine Patch-Version steht: das lokal vorhandene
Image unter `34-apache` war vom 5. August und trug 34.0.2.1, während der Tag auf Docker Hub
am 17. August auf 34.0.3 weitergezogen war, und Docker holt einen weitergezogenen Tag ohne
`pull` nicht nach. Die Version dieser Instanz ist deshalb `occ status`, nicht diese Zeile.

## 4. Das Upgrade auf 34.0.3 (14:17 bis 14:18:35Z)

`HP_SHARED_KEY` wurde aus dem laufenden HaRP-Container zurückgelesen und in derselben
Shell-Zeile weiterverwendet (nicht neu erzeugt: `require_hex64` und die
Daemon-Registrierung hängen an genau diesem Wert):

```
$ export <der Schluessel>   # zurueckgelesen aus nc-mcp-exapp-harp per docker inspect,
                            # Kommando im interfaces-Block von 06-07-PLAN.md
key length: 64
$ docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
 Container nc-mcp-exapp-nc Recreate
 Container nc-mcp-exapp-nc Recreated
 Container nc-mcp-exapp-nc Healthy
 Container nc-mcp-exapp-caddy Healthy
 Container nc-mcp-exapp-registry Healthy
 Container nc-mcp-exapp-harp Healthy
```

Der explizite `occ upgrade` fand nichts mehr zu tun, weil der Einsprungpunkt des offiziellen
Images das Upgrade beim Start selbst ausführt. Beide Belege, in dieser Reihenfolge:

```
$ occ upgrade
No upgrade required.
$ docker logs nc-mcp-exapp-nc | head -20
Initializing nextcloud 34.0.3.2 ...
Upgrading nextcloud from 34.0.2.1 ...
Turned on maintenance mode
Updating database schema
Updated database
Updating <dav> ...
Updated <dav> to 1.40.0
Starting code integrity check...
Finished code integrity check
Update successful
Turned off maintenance mode
```

Der Nachzustand der Instanz, und das ist die **erste Behauptung dieses Protokolls**:

```
$ occ status
  - installed: true
  - version: 34.0.3.2
  - versionstring: 34.0.3
  - maintenance: false
  - needsDbUpgrade: false
$ docker inspect nc-mcp-exapp-nc --format '{{.Config.Image}} {{.Image}}'
nextcloud:34.0.3-apache sha256:365baea128b5e0f45a8dc5111c9234b926f1e6082b4c14d75ae650324ce5d65c
$ occ app:list | grep -E "app_api|appstore"
  - app_api: 34.0.0
  - appstore: 1.0.0
$ occ user:list
  - admin: admin
  - alice: alice
  - bob: bob
  - jane: Jane Fischer
```

`jane` hat das Upgrade also überlebt, und `app_api` sowie `appstore` sind über das Upgrade
unverändert. Der zweite Punkt ist für Abschnitt 6 wichtig: der Unterschied zwischen dem
34.0.2- und dem 34.0.3-Befund kann nicht an einer neuen App-Version liegen.

## 5. Der Repository-Stand des Connectors (14:19 bis 14:21:10Z)

`scripts/bootstrap_exapp.sh` allein hätte hier nicht genügt, und das ist ein Fund und keine
Formalität: `ensure_exapp` überspringt die Registrierung, sobald `occ app_api:app:list` die
App kennt, also hätte der Lauf ein Image 0.1.2 gebaut und gepusht und der Container wäre
weiter mit 0.1.1 gelaufen. Der Weg war deshalb Abmelden und neu registrieren, und die
Sicherheitsfrage davor war, was ein `unregister` mitnimmt:

* `occ app_api:app:unregister mcp_connector` **ohne** `--rm-data` lässt das Volume stehen
  (Quelltext: `apps/app_api/lib/Command/ExApp/Unregister.php`, der Volume-Zweig hängt an
  `--rm-data`), und `ExAppService::unregisterExApp` löscht Formulare, Routen und Menüs, aber
  keine Zeile aus `oc_appconfig_ex`. Beides ist Quelltext, also wurde beides gemessen.

```
$ occ app_api:app:unregister mcp_connector
ExApp mcp_connector successfully disabled.
ExApp mcp_connector successfully removed
ExApp mcp_connector successfully unregistered.
$ <select configkey, length(configvalue) from oc_appconfig_ex where appid="mcp_connector">
oauth_data_key len=324
public_url len=42
$ docker volume ls --format '{{.Name}}' | grep nc_app_mcp_connector_data
nc_app_mcp_connector_data
```

Der Datenschlüssel und das Volume haben das Abmelden überlebt, also auch die zwei
Verbindungen: ohne den Schlüssel wäre jede Autorisierung unlesbar geworden, obwohl ihre
Zeile noch dastünde.

Danach der Bootstrap, der das Image aus dem Arbeitsbaum baut, in die Loopback-Registry
pusht, den Digest gegenprüft und neu registriert:

```
$ bash scripts/bootstrap_exapp.sh
image 127.0.0.1:5000/mcp_connector:0.1.2: built and pushed (sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed)
image digest sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed: unchanged since the push
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
ExApps:
mcp_connector (MCP Connector): 0.1.2 [enabled]
```

Der Digest-Vergleich vorher und nachher, also der Beleg, dass der Rebuild wirklich
stattgefunden hat:

| Wann | Image des ExApp-Containers | Digest |
|------|----------------------------|--------|
| vorher | `127.0.0.1:5000/mcp_connector:0.1.1` | `sha256:92602ca154a23a89b8ac15b3c5cf3268c458e50d5b169a9cd6af4fa40f792e4c` |
| nachher | `127.0.0.1:5000/mcp_connector:0.1.2` | `sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed` |

Die Demo-Substanz nach dem Rebuild, mit demselben Kommando wie in Abschnitt 1 gezählt:

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-08-20T14:21:10Z
$ docker inspect nc_app_mcp_connector --format '... restarts={{.RestartCount}}'
127.0.0.1:5000/mcp_connector:0.1.2 sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed restarts=0
clients 2
authorizations 2
refresh_tokens 2
[('jane', 'c06831e2-36ee-48f9-a99c-d091b3013311', None), ('jane', '7256ad37-7670-4621-ba02-021e835fd372', None)]
```

Zwei Gegenproben, dass hier wirklich der Arbeitsbaum läuft und nicht die Store-Fassung:

```
$ curl -s .../.well-known/oauth-authorization-server -o /dev/null -w '%{http_code}'
200
$ curl -s .../.well-known/oauth-authorization-server | tr ',' '\n' | grep -E "issuer|client_id_metadata"
{"issuer":"http://127.0.0.1:8081/exapps/mcp_connector"
"client_id_metadata_document_supported":true
```

Das zweite Feld gibt es erst seit 06-05; die Store-Fassung 0.1.1 kennt es nicht. Und der
`issuer` ist die öffentliche Adresse und nicht der dokumentierte Default, also hat die
Registrierung `NC_MCP_PUBLIC_URL` wieder gesetzt.

## 6. Der UI-Smoke: zeigt die Store-Oberfläche Install- und Remove-Knopf? (14:24 bis 14:45Z)

Die Reihenfolge dieses Abschnitts ist die Reihenfolge der Messung.

**6.0 Die Version, gegen die gemessen wurde**, als erste Zeile und nicht als Docker-Tag:

```
$ occ status
  - installed: true
  - version: 34.0.3.2
  - versionstring: 34.0.3
```

**6.1 Das Konto.** Gemessen wurde als `admin`, und das ist ein Konto der Gruppe `admin`.
Das ist Pflichtangabe, weil der App-Store-Zugang für Normalnutzer in NC 34 bewusst entfernt
ist (nextcloud/server#60495):

```
$ occ user:info admin
  - user_id: admin
  - groups:
    - admin
im Browser: OC.getCurrentUser().uid = "admin", OC.isUserAdmin() = true
```

**6.2 Der Cache-Schritt.** Der Store-Cache wurde durch **Überschreiben mit `timestamp 0`**
verworfen, nie durch Löschen der Datei (Phase-05-Entscheidung: eine gelöschte Datei lässt
jedes folgende AppAPI-Kommando mit `GenericFileException` enden):

```
$ php -r '<apps.json lesen, timestamp auf 0 setzen, zurueckschreiben>'
before: timestamp=1787235500 ncversion=34.0.3.2 entries=665
after:  timestamp=0 ncversion=34.0.3.2 entries=665
appapi_apps.json exists: 0
```

Zwei Dinge stehen in diesem Beleg. Erstens: die Datei heißt
`data/appdata_*/appstore/apps.json`, und das ist der Cache, den `AppAPIFetcher::get`
verwirft, sobald `timestamp` alt ist (Quelltext `apps/app_api/lib/Fetcher/AppAPIFetcher.php`,
Zeilen 130 bis 152). Zweitens: die zweite Datei desselben Verzeichnisses,
`appapi_apps.json`, existierte gar nicht, also gab es dort nichts zu überschreiben und es
wurde nichts angelegt.

**6.3 Die Gegenprobe vor dem Blick in die Oberfläche**, damit nicht eine leere Liste als
Frontend-Befund notiert wird, und zugleich der Beleg, dass der Cache-Schritt kein
AppAPI-Kommando zerstört hat:

```
$ occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.2 [enabled]
```

Keine `GenericFileException`, und die App ist `enabled`, während gemessen wird.

**6.4 Eigenheit der Messumgebung, benannt statt versteckt.** Dieser Sitzung stand kein
Playwright-Werkzeug zur Verfügung, und ein Paket zu installieren ist in dieser Phase
ausgeschlossen (T-06-SC). Gemessen wurde deshalb mit dem auf dem Host installierten Chrome
(`C:\Program Files\Google\Chrome\Application\chrome.exe`, `--headless=new`) über das
DevTools-Protokoll, angesprochen von einem WebSocket-Client aus der Standardbibliothek. Die
Anmeldung lief über das Formular, das die Seite selbst rendert; das Kennwort des
Wegwerf-Kontos steht in `compose.exapp.yml` und nicht hier.

**6.5 Was zu sehen ist.** `/settings/apps` leitet auf `/settings/apps/discover`; die Listen
der Oberfläche sind `installed`, `enabled`, `disabled`, `updates` und die Kategorien
(Routen aus `dist/appstore-main.mjs`). Auf **"Your apps"** (`/settings/apps/installed`)
erscheint die ExApp:

```
Zeile (innerText):   MCP Connector
                     (Show details)
                     	0.1.2	
                     Harp Proxy (Docker)
                     	
                     Disable
Zeilen-Element:      <tr class="_appTableRow_...">
Detail-Link:         /settings/apps/installed/mcp_connector
Knöpfe der Zeile:    "Disable" und ein Menü-Knopf mit aria-label "Actions"
```

Wo bei einer normalen App das Abzeichen "Featured" steht, steht bei dieser Zeile der Name
des Deploy Daemon, "Harp Proxy (Docker)". Und die Seite fragt jetzt genau die Route, die auf
34.0.2 nie angefragt wurde (Netzwerkmitschnitt derselben Navigation, 213 Anfragen, davon die
interessanten):

```
http://127.0.0.1:8081/ocs/v2.php/apps/appstore/api/v1/apps
http://127.0.0.1:8081/ocs/v2.php/apps/appstore/api/v1/apps/categories
http://127.0.0.1:8081/apps/app_api/daemons
http://127.0.0.1:8081/apps/app_api/apps/list
http://127.0.0.1:8081/apps/app_api/img/app-dark.svg
```

Der 34.0.2-Befund aus `docs/exapp-install.md` bleibt damit richtig und ist überholt: die
OCS-Route des `appstore` kennt diese App weiter nicht (`mcp_connector` kommt in ihrer
Antwort von 2 650 705 Bytes **null** mal vor, und `apps/appstore/lib/Controller/ApiController.php`
trägt in 34.0.3 unverändert `'app_api' => false`), aber die Oberfläche holt die ExApps
inzwischen selbst über `/apps/app_api/apps/list` dazu.

**6.6 Der Install-Knopf: vorhanden, und er heißt "Deploy and enable".** Für die eigene App
ist die Frage nicht am eigenen Eintrag zu beantworten, denn sie ist installiert und trägt
darum "Disable". Gemessen wurde deshalb an einer ExApp, die diese Instanz **nicht**
installiert hat, in derselben Ansicht (`/settings/apps/office`, 116 Zeilen):

```
Zeile:    Context Chat Backend
          (Show details)
          	5.4.1	
          	
          Deploy and enable
Knöpfe:   "Deploy and enable" und "Actions"
Alle Knopf-Beschriftungen dieser Tabelle:
          "Download and enable", "Deploy and enable", "Disable", "Actions"
```

`Download and enable` ist der Knopf einer normalen App, `Deploy and enable` der einer ExApp.
Die Store-Oberfläche hat auf 34.0.3 also einen Installationsknopf für ExApps, und sie
unterscheidet ihn im Wortlaut vom Knopf einer PHP-App.

**6.7 Der Remove-Knopf: vorhanden, aber nur an einer abgeschalteten ExApp.** Am eingeschalteten
eigenen Eintrag gibt es ihn nicht, und das ist keine Vermutung, sondern gemessen: das
Aktionsmenü der Zeile und die Detailspalte tragen ihn nicht, und die Route, die die Seite
liest, sagt es selbst.

```
Aktionsmenü der Zeile (eingeschaltet):
          "Limit to groups", "Rate the app", "Report a bug", "Show details"
Detailspalte /settings/apps/installed/mcp_connector (aside.app-sidebar):
          Knöpfe: "Close sidebar", "Disable", "Limit to groups"
          Reiter: Description, Details, Changelog, Daemon
          Text:   MCP Connector, Version 0.1.2, AGPL-licensed, Daemon: Harp Proxy (Docker)
          kein Knopf mit "remove", "uninstall" oder "delete" auf der ganzen Seite
/apps/app_api/apps/list, Eintrag mcp_connector (eingeschaltet):
          installed=true active=true canInstall=true canUnInstall=false
```

Der Grund steht im Quelltext von AppAPI, `lib/Controller/ExAppsPageController.php:213`:

```php
$appData['canUnInstall'] = !$appData['active'] && $appData['removable'] && ...
```

Also wurde die zweite Hälfte gemessen. Nach `occ app_api:app:disable mcp_connector`
(14:43:53Z), Blick auf `/settings/apps/disabled`:

```
Zeile:    MCP Connector
          (Show details)
          	0.1.2	
          Harp Proxy (Docker)
          	
          Enable
Aktionsmenü der Zeile:
          "Limit to groups", "Remove", "Rate the app", "Report a bug", "Show details"
/apps/app_api/apps/list, Eintrag mcp_connector (abgeschaltet):
          installed=true active=false canInstall=true canUnInstall=true removable=true
```

Der Befund, getrennt beantwortet:

| Frage | Antwort | Sichtbarer Text |
|-------|---------|-----------------|
| Zeigt die Oberfläche diese ExApp überhaupt? | **ja** | Zeile "MCP Connector 0.1.2 Harp Proxy (Docker)" unter "Your apps" |
| Gibt es einen Install-Knopf für eine ExApp? | **ja** | "Deploy and enable" (an einer nicht installierten ExApp derselben Ansicht) |
| Gibt es einen Remove-Knopf für diese ExApp? | **ja, im Aktionsmenü, und nur solange sie abgeschaltet ist** | "Remove" |
| Und am eingeschalteten Eintrag? | **nein** | Menü ohne "Remove", `canUnInstall=false` |

**6.8 Der Zustand danach wieder hergestellt**, und die Demo-Substanz nachgezählt:

```
$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.
$ occ app_api:app:list
ExApps:
mcp_connector (MCP Connector): 0.1.2 [enabled]
$ <Zeilen zaehlen>
authorizations 2
[('jane', None), ('jane', None)]
$ curl -s -o /dev/null -w '%{http_code}' .../.well-known/oauth-authorization-server
200
```

**6.9 Die statische Gegenprobe**, obwohl der Ausgang positiv ist: die Recherche hatte den
Fix nicht statisch finden können, und dieser Absatz sagt, warum, damit die Aussage der
Recherche nicht als widerlegt und unerklärt stehenbleibt. Verglichen wurden alle 122 Dateien
von `apps/appstore` und alle `*ppstore*`-Dateien aus `dist/` zwischen dem 34.0.2- und dem
34.0.3-Image, per md5:

```
$ docker run --rm <image> sh -c 'cd /usr/src/nextcloud && find apps/appstore -type f -exec md5sum {} \; | sort -k2 && find dist -name "*ppstore*" -type f -exec md5sum {} \; | sort -k2'
34.0.2: 122 Dateien
34.0.3: 122 Dateien
Unterschiede ausserhalb von l10n/, .map und .license:
  apps/appstore/appinfo/signature.json
  dist/AppstoreBrowse-BY9drF5z.chunk.mjs  ->  dist/AppstoreBrowse-C0Yoxgfp.chunk.mjs  (8721 -> 8707 Bytes)
  dist/AppstoreDiscover-DdlBIFps.chunk.mjs -> dist/AppstoreDiscover-DuQf5I8Z.chunk.mjs
  dist/appstore-main.css
  dist/appstore-main.mjs                   (95762 -> 95841 Bytes)
```

Die App-Version ist in beiden 1.0.0, und in `AppstoreBrowse` kommt `exapp` in beiden Fassungen
nicht vor. Der Fix liegt in `dist/appstore-main.mjs`, und er ist ein Aufruf und kein neues
Wort:

```
34.0.2: kein Treffer fuer Promise.allSettled([...initialize...])
34.0.3: Promise.allSettled([V(),Y(),e.isEnabled?e.initialize():Promise.resolve()])
Vorkommen von "isEnabled":  34.0.2: 2   34.0.3: 3
Vorkommen von "initialize": 34.0.2: 1   34.0.3: 2
Vorkommen von "app_api":    34.0.2: 23  34.0.3: 23
Vorkommen von "exAppsCount":34.0.2: 1   34.0.3: 1
```

Das ist wörtlich der Titel des Upstream-Merges (`fix(appstore): initialize the exApps store
when enabled`, `nextcloud/server#62881`, Milestone 34.0.3): der Store der externen Apps wird
jetzt initialisiert, wenn AppAPI aktiviert ist. Wer nach dem Wort `exapp` sucht, findet
nichts, weil der Aufruf `e.initialize()` heißt und `e` der minifizierte Name des
`external-apps`-Stores ist.

**6.10 Bildschirmfotos.** Die Aufnahmen des Laufs liegen unter
`C:/Users/Student/AppData/Local/Temp/claude/.../scratchpad/out/` (Listen `installed`,
`enabled`, `disabled`, `updates`, die Kategorieansicht mit "Deploy and enable", die
Detailspalte der eigenen App). Sie tragen kein Credential und keine fremden Nutzerinhalte,
sondern den App-Katalog dieser Wegwerf-Instanz. Eine davon geht ins Repository, weil sie den
Befund dieses Abschnitts in einem Bild trägt:
`docs/screenshots/exapp-remove-button.png` zeigt die Zeile "MCP Connector 0.1.2, Harp Proxy
(Docker), Enable" mit dem geöffneten Aktionsmenü und dem Eintrag "Remove".

## 7. Nicht vorhergesagt und darum hier festgehalten

1. **Der explizite `occ upgrade` hatte nichts zu tun.** Der Einsprungpunkt des offiziellen
   Images führt das Upgrade beim Start selbst aus, also war die Instanz schon auf 34.0.3.2,
   bevor das geplante Kommando lief. Der Plan-Schritt bleibt richtig, sein Ergebnis ist aber
   "No upgrade required" und nicht der Upgrade-Bericht; der Bericht steht im Containerlog.
2. **`bootstrap_exapp.sh` allein hätte den alten Connector weiterlaufen lassen.**
   `ensure_exapp` überspringt die Registrierung für eine bekannte App, also wäre ein Image
   0.1.2 gebaut und gepusht worden, während der Container weiter 0.1.1 fährt. Genau der
   Fehler, gegen den Pitfall 8 warnt, nur eine Ebene tiefer: nicht die Messdatei hätte den
   Digest verschwiegen, sondern das Werkzeug hätte ihn nicht geändert.
3. **Der Remove-Knopf hängt am Abschaltzustand.** Ein einziger Blick auf die eingeschaltete
   App hätte "kein Remove-Knopf" ergeben, und das wäre ein falscher Negativbefund gewesen.
   Die Regel steht in AppAPI und nicht im Frontend (`canUnInstall = !active && removable`).
4. **Die Gegenprobe der Recherche war nicht falsch, sondern suchte das falsche Wort.** Der
   Fix ist ein Aufruf in einem minifizierten Bundle, kein neues `exapp`-Vorkommen. Abschnitt
   6.9 hält das fest, damit die frühere Aussage nachvollziehbar bleibt.
5. **Kein Playwright in dieser Sitzung.** Der Browser-Schritt lief über das
   DevTools-Protokoll mit einem WebSocket-Client aus der Standardbibliothek gegen das
   installierte Chrome. Kein Paket wurde installiert (T-06-SC).

## 8. Anhang: die Instanzen des Owners

Und die Instanzen des Owners, die diesen Lauf nur ausgehalten haben:

```
$ docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
nc_app_mcp_connector    127.0.0.1:5000/mcp_connector:0.1.2   Up 42 seconds (healthy)
nc-mcp-exapp-nc         nextcloud:34.0.3-apache              Up 3 minutes (healthy)
nc-mcp-exapp-caddy      caddy:2                              Up 10 hours
nc-mcp-exapp-harp       ghcr.io/nextcloud/...harp:release    Up 10 hours (healthy)
nc-mcp-exapp-registry   registry:2                           Up 10 hours
findling-nextcloud      nextcloud:34.0.3-apache              Up 5 days
nc-mcp-test             nextcloud:34-apache                  Up 5 days (healthy)
```
