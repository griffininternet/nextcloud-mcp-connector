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
