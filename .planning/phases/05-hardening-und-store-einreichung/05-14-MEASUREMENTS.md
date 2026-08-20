# 05-14 Rohmessungen: der Rundlauf vom Admin-Formular ins Discovery-Dokument

Alle Messungen am **20.08.2026** zwischen 04:37Z und 04:53Z auf diesem Windows-Host (Git
Bash), gegen eine **neu aufgebaute** Wegwerf-Topologie `compose.exapp.yml` (Compose-Projekt
`nc-mcp-exapp`). Die vom Owner genutzten Instanzen `nc-mcp-test` und `findling-nextcloud`
liefen die ganze Zeit weiter, wurden in keinem Kommando dieses Laufs genannt und nicht
angefasst (T-05-54).

Der gemessene Stand ist HEAD nach Plan 05-13, also App-Version 0.1.1 mit der
https-oder-Loopback-Regel (05-11), dem Rettungszweig in `entry_exapp` (05-11) und der
INFO-Zeile für den 401 des Fensters vor der Aktivierung (05-13).

Dieser Lauf ist bewusst **nicht** die Instanz, auf der 05-08 den 401 gefunden und 05-12 ihn
zerlegt hat: Volumes und Registrierung sind vor der ersten Messung weggeworfen worden. Damit
beantwortet er zugleich die Frage des Verifiers, ob der Befund ein Artefakt einer einzelnen
Topologie war.

## 1. Gemessene Versionen und Aufbau

| Was | Wert | Kommando |
|-----|------|----------|
| Nextcloud | 34.0.2 (34.0.2.1) | `occ status` |
| AppAPI | 34.0.0 | `occ app:list` |
| Deploy Daemon | HaRP, `harp_proxy_docker`, `docker-install`, FRP `appapi-harp:8782` | `occ app_api:daemon:list` |
| App | `mcp_connector (MCP Connector): 0.1.1 [enabled]` | `occ app_api:app:list` |
| Image | `127.0.0.1:5000/mcp_connector:0.1.1`, `sha256:92602ca154a23a...` | `scripts/bootstrap_exapp.sh` |

Zwei Konventionen für dieses Protokoll, wie in 05-08 und 05-12:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen diese Datei verlangt `HP_SHARED_KEY`
  in der Umgebung (WR-11).
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-53). Von
  jeder Anfrage stehen hier nur Zieladresse, Statuscode und Antwortfelder. Die
  Anmeldedaten des Wegwerf-Admins lagen in einer Datei außerhalb dieses Repositories und
  sind am Ende des Laufs gelöscht worden (Abschnitt 6).

Frischer Aufbau vor der ersten Messung:

```
$ docker compose -f compose.exapp.yml down -v --remove-orphans      # 04:37:38Z
 Volume nc-mcp-exapp_registry-exapp-data Removed
 Volume nc-mcp-exapp_nextcloud-exapp-data Removed
 Network nc-mcp-exapp-net Resource is still in use
$ docker volume rm nc_app_mcp_connector_data
Error response from daemon: remove nc_app_mcp_connector_data: volume is in use
  - [2d30cc5f3777...]                       # der ExApp-Container gehoert keinem compose-Projekt
$ docker rm -f nc_app_mcp_connector
nc_app_mcp_connector
$ docker volume rm nc_app_mcp_connector_data
nc_app_mcp_connector_data
$ docker volume ls --format '{{.Name}}'     # kein Volume der Wegwerf-Topologie mehr
findling-dev_nextcloud
nextcloud-mcp-connector_nextcloud-test-data
(plus drei anonyme Volumes fremder Projekte)
$ docker compose -f compose.exapp.yml up -d --wait                  # 04:37:56Z bis 04:38:30Z
$ bash scripts/bootstrap_exapp.sh                                   # 04:44:01Z bis 04:45:11Z
image 127.0.0.1:5000/mcp_connector:0.1.1: built and pushed (sha256:92602ca154a2...)
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
ExApps:
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Nebenbefund aus diesem Aufbau, und der erste Live-Beleg für den Fix aus 05-13: der
allererste Start nach dem Deploy zeigt an der Stelle, an der 05-08 eine `ERROR`-Zeile
protokolliert hat, jetzt die INFO-Zeile mit dem Ausweg.

```
$ docker logs nc_app_mcp_connector | grep -E "config_values|entry_exapp"
INFO mcp_connector.exapp.config_values: the admin values were not read on this start:
  Nextcloud answered 401, which is the expected answer while AppAPI does not have this app
  on enabled yet, [...] That is why a value entered in the administration settings takes
  effect after this app has been disabled and enabled once. [...]
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

### 1.1 Der Schreibweg, am Controller der laufenden Instanz gegengeprüft

Der Plan nennt `/ocs/v2.php/apps/settings/api/declarative/value`. Die laufende Instanz sagt
etwas anderes, und die Route dieses Laufs ist die gemessene:

```
$ (nc-mcp-exapp-nc) apps/settings/appinfo/routes.php:57
['name' => 'DeclarativeSettings#setValue', 'url' => '/settings/api/declarative/value',
 'verb' => 'POST', 'root' => '']
$ (nc-mcp-exapp-nc) apps/settings/lib/Controller/DeclarativeSettingsController.php
public function setValue(string $app, string $formId, string $fieldId, mixed $value)
```

`'root' => ''` heißt: die Adresse ist `/ocs/v2.php/settings/api/declarative/value`, ohne das
`apps/`-Segment. Die vier Felder des Bodys heißen `app`, `formId`, `fieldId` und `value`.
Benutzt wurde genau dieser Weg, als Wegwerf-Admin mit den Headern `OCS-APIRequest: true` und
`Accept: application/json`; die Anmeldedaten gingen über eine curl-Konfiguration auf stdin
und nie über die Kommandozeile.

Dass dieses Formular das Formular dieser App ist, steht in derselben Messung
(`GET /ocs/v2.php/settings/api/declarative/forms`, HTTP 200):

```
Formular mcp_connector_admin im Ergebnis: 1
  app: mcp_connector section: admin security
  Feld-Ids: ['public_url', 'oauth_dcr', 'oauth_allowlist_only', 'oauth_allowed_clients']
```

### 1.2 Die Bedingung dieses Nachweises: keine Umgebungsvariable

`scripts/bootstrap_exapp.sh` registriert die App mit `NC_MCP_PUBLIC_URL` in der
Deploy-Umgebung (json-info, `external-app/environment-variables`). Genau diese Variable darf
für diesen Nachweis nicht existieren, sonst bewiese die Messung nur, dass ein Admin-Wert eine
Variable überschreibt, und nicht, dass er allein trägt. AppAPI 34.0.0 kennt kein occ-Kommando,
das eine Deploy-Variable entfernt (`occ list app_api`), also ist die App einmal ohne diesen
Block neu registriert worden, mit demselben Secret, demselben Image und denselben dreizehn
Routen:

```
$ occ app_api:app:unregister mcp_connector --rm-data                # 04:49:44Z
ExApp mcp_connector successfully disabled.
ExApp mcp_connector successfully removed
ExApp mcp_connector successfully unregistered.
$ occ app_api:app:register mcp_connector harp_proxy_docker \
    --json-info "$JSON" --force-scopes --wait-finish                # Payload ueber stdin
ExApp mcp_connector deployed successfully.
ExApp mcp_connector successfully registered.
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Die Umgebung des App-Containers danach, nur die Variablennamen, ohne Werte:

```
$ docker exec nc_app_mcp_connector printenv | cut -d= -f1 | grep -E '^(NC_MCP_|APP_|HP_|NEXTCLOUD_)' | sort
APP_DISPLAY_NAME
APP_HOST
APP_ID
APP_PERSISTENT_STORAGE
APP_PORT
APP_SECRET
APP_VERSION
HP_FRP_ADDRESS
HP_FRP_PORT
HP_SHARED_KEY
NEXTCLOUD_URL
$ docker exec nc_app_mcp_connector printenv | cut -d= -f1 | grep -c '^NC_MCP_PUBLIC_URL$'
0
```

**Keine `NC_MCP_PUBLIC_URL` in der Umgebung.** Der Start sagt dasselbe, und er sagt zugleich,
was eine Installation ohne Adresse ist, nämlich ein Setup-Zustand und kein toter Prozess:

```
$ docker logs nc_app_mcp_connector | grep -E "config_values|entry_exapp"
INFO  mcp_connector.exapp.config_values: the admin values were not read on this start:
  Nextcloud answered 401, [...]
ERROR mcp_connector.entry_exapp: NC_MCP_PUBLIC_URL is not set and no public address is
  stored in Nextcloud either. Until one is, every discovery document, the audience of every
  token and the consent redirect name http://127.0.0.1:8765, and no client can connect. Set
  it in "Administration settings, Security, MCP Connector", then disable and enable this app
  again [...]
INFO  mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
$ docker inspect nc_app_mcp_connector
id=164090d48d6a status=running started=2026-08-20T04:49:49.056116435Z restartcount=0
  policy=unless-stopped
```

Der Ausgangswert der Messung, von außen gelesen (04:50:17Z):

```
$ curl http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-authorization-server
HTTP 200   issuer: http://127.0.0.1:8765
$ curl http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
HTTP 200   resource: http://127.0.0.1:8765/mcp
```

Das ist der dokumentierte Default aus `config.DEFAULT_PUBLIC_URL`, und er ist der Kontrast,
gegen den Linie A misst.

## 2. Linie A: brauchbarer Wert, ein Zyklus, Discovery

Gesetzt wurde die Adresse, unter der diese Wegwerf-Instanz diese App tatsächlich ausliefert,
`http://127.0.0.1:8081/exapps/mcp_connector` (T-05-56: keine fremde Adresse). Sie ist http auf
einem Loopback-Host, also genau der Fall, den RFC 8414 als Ausnahme zulässt und den
`config_values._public_url` als einzige Nicht-https-Form durchlässt.

```
$ curl -X POST http://127.0.0.1:8081/ocs/v2.php/settings/api/declarative/value \
    -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    -d app=mcp_connector -d formId=mcp_connector_admin -d fieldId=public_url \
    --data-urlencode 'value=http://127.0.0.1:8081/exapps/mcp_connector'    # 04:50:40Z
{"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":null}}
HTTP 200
$ occ app_api:app:config:list mcp_connector
ExApp mcp_connector configs:
{ "mcp_connector": { "public_url": "***REMOVED SENSITIVE VALUE***" } }
```

Der Wert steht also in Nextcloud (occ maskiert Konfigurationswerte in der Ausgabe). Vor dem
Zyklus ändert sich am Dokument nichts, was den Preis aus `entry_exapp._resolved_env` sichtbar
macht:

```
T 04:50:51Z vor dem Zyklus
id=164090d48d6a status=running started=2026-08-20T04:49:49.056116435Z restartcount=0 exit=0
issuer vor dem Zyklus: http://127.0.0.1:8765

$ occ app_api:app:disable mcp_connector
ExApp mcp_connector successfully disabled.
T 04:50:52Z nach disable
id=164090d48d6a status=exited  started=2026-08-20T04:49:49.056116435Z
               finished=2026-08-20T04:50:52.687079343Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [disabled]

$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.
T 04:51:05Z nach enable
id=164090d48d6a status=running started=2026-08-20T04:50:53.937058226Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

**Genau ein Zyklus**, wie `docs/oauth-setup.md` es dokumentiert ("One cycle is enough, and it
is measured", Zeile 146). Derselbe Container (gleiche Id), neues StartedAt, `RestartCount`
unverändert 0.

Die Startzeile dieses Starts nennt, welcher Schlüssel aus der Administration kam:

```
$ docker logs --since 2026-08-20T04:50:53Z nc_app_mcp_connector
INFO mcp_connector.entry_exapp: these values come from the administration settings of this
  app and win over the deploy environment: NC_MCP_PUBLIC_URL
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

Eine Quellenangabe "frisch gelesen oder aus dem Volume" steht nicht dabei, und das ist kein
Fehlbefund: mit Zweig N gibt es keine zweite Quelle. Jeder Start liest frisch, der Cache aus
dem ursprünglichen Plan 05-13 ist gemessen überflüssig und deshalb nie gebaut worden
(05-13-SUMMARY.md, Abweichung 1 bis 3).

Die Dokumente von außen, unmittelbar danach (04:51:16Z):

```
$ curl http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-authorization-server
HTTP 200
issuer:                 http://127.0.0.1:8081/exapps/mcp_connector
authorization_endpoint: http://127.0.0.1:8081/exapps/mcp_connector/authorize
registration_endpoint:  http://127.0.0.1:8081/exapps/mcp_connector/register
$ curl http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
HTTP 200
resource:              http://127.0.0.1:8081/exapps/mcp_connector/mcp
authorization_servers: ['http://127.0.0.1:8081/exapps/mcp_connector']
```

Der Zeichenvergleich, beide Seiten ausgeschrieben und programmatisch verglichen:

```
gesetzter Wert:                    'http://127.0.0.1:8081/exapps/mcp_connector'
as_linieA: issuer == gesetzter Wert                 -> True
prm_linieA: resource == gesetzter Wert + '/mcp'     -> True
```

**Linie A steht.** Ein im Formular gesetzter Wert erscheint nach einem Disable/Enable-Zyklus
zeichengleich als `issuer` im Autorisierungsserver-Dokument, auf einer frischen Topologie,
ohne jede gesetzte Umgebungsvariable.

## 3. Linie B: unbrauchbarer Wert, keine Neustartschleife

Derselbe Weg mit `http://cloud.example.com/exapps/mcp_connector`, also http auf einem Host,
der kein Loopback ist. Das ist der Klick, den CR-01 als Blocker beschrieben hat.

```
T 04:51:35Z unmittelbar vor Linie B
id=164090d48d6a status=running started=2026-08-20T04:50:53.937058226Z restartcount=0 exit=0

$ curl -X POST .../settings/api/declarative/value  ... fieldId=public_url \
    --data-urlencode 'value=http://cloud.example.com/exapps/mcp_connector'
{"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":null}}
HTTP 200
$ occ app_api:app:disable mcp_connector
ExApp mcp_connector successfully disabled.
T 04:51:36Z nach disable
id=164090d48d6a status=exited started=2026-08-20T04:50:53.937058226Z restartcount=0 exit=0
$ occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully enabled.
T 04:51:50Z nach enable
id=164090d48d6a status=running started=2026-08-20T04:51:37.053305179Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
```

Die Ablehnungszeile steht wörtlich im Containerlog, und sie nennt weder den Wert noch eine
Adresse (T-05-03):

```
$ docker logs --since 2026-08-20T04:51:37Z nc_app_mcp_connector
WARNING mcp_connector.exapp.config_values: the admin value for public_url is http on a host
  that is not loopback; the issuer of the authorization server has to be https (RFC 8414),
  so it is ignored and the deploy environment stays in force for it. Correct it in the
  Nextcloud administration settings of this app.
ERROR mcp_connector.entry_exapp: NC_MCP_PUBLIC_URL is not set and no public address is
  stored in Nextcloud either. [...] Set it in "Administration settings, Security, MCP
  Connector", then disable and enable this app again [...] This process keeps serving on
  purpose, so that form exists at all; the connections page says the same thing.
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock
```

Es ist die Ablehnungszeile aus `config_values` und nicht die Rettungszeile aus `entry_exapp`,
und das ist die schärfere der beiden Hälften von CR-01: der Wert wird schon verworfen, bevor
er `build_exapp_app` erreichen kann. Die Rettungszeile bleibt als zweite Sicherung dahinter
stehen, für jeden Wert, den `_public_url` durchlässt und das SDK trotzdem ablehnt.

Der Rest der Gegenprobe:

```
$ curl .../.well-known/oauth-authorization-server
issuer: http://127.0.0.1:8765                        # NICHT der http-Wert
$ curl -u <wegwerf-admin> http://127.0.0.1:8081/settings/admin/security
GET /settings/admin/security -> HTTP 200
$ curl -u <wegwerf-admin> http://127.0.0.1:8081/ocs/v2.php/settings/api/declarative/forms
GET /ocs/v2.php/settings/api/declarative/forms -> HTTP 200
Formular mcp_connector_admin im Ergebnis: 1
```

**Linie B steht.** `RestartCount` ist gegenüber der Messung unmittelbar davor unverändert 0,
`.State.Status` ist `running`, die App bleibt `enabled`, der `issuer` trägt den http-Wert
nicht, und die Seite, auf der der Fehler zu korrigieren ist, antwortet weiter mit 200.

## 4. Linie C: der Rückweg allein über das Formular

Vor dem Rückweg steht der falsche Wert noch dort, wo die Administratorin ihn eingetippt hat
(T-05-44: nichts wird stillschweigend gelöscht):

```
T 04:52:21Z vor Linie C
id=164090d48d6a status=running started=2026-08-20T04:51:37.053305179Z restartcount=0 exit=0
public_url im Formular: 'http://cloud.example.com/exapps/mcp_connector'
```

Der Rückweg ist ein Schreibvorgang auf dasselbe Feld und ein Zyklus, sonst nichts. Kein
`occ app_api:app:config:*`, kein PDO, kein Eingriff in `oc_appconfig_ex`:

```
$ curl -X POST .../settings/api/declarative/value ... fieldId=public_url \
    --data-urlencode 'value=http://127.0.0.1:8081/exapps/mcp_connector'
{"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":null}}
HTTP 200
$ occ app_api:app:disable mcp_connector && occ app_api:app:enable mcp_connector
ExApp mcp_connector successfully disabled.
ExApp mcp_connector successfully enabled.
T 04:52:36Z nach Linie C
id=164090d48d6a status=running started=2026-08-20T04:52:23.341686876Z restartcount=0 exit=0
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
public_url im Formular: 'http://127.0.0.1:8081/exapps/mcp_connector'

$ docker logs --since 2026-08-20T04:52:23Z nc_app_mcp_connector
INFO mcp_connector.entry_exapp: these values come from the administration settings of this
  app and win over the deploy environment: NC_MCP_PUBLIC_URL
INFO mcp_connector.entry_exapp: MCP Connector is serving as an ExApp on /tmp/exapp.sock

$ curl .../.well-known/oauth-authorization-server     HTTP 200
issuer:   http://127.0.0.1:8081/exapps/mcp_connector
$ curl .../.well-known/oauth-protected-resource/mcp    HTTP 200
resource: http://127.0.0.1:8081/exapps/mcp_connector/mcp

as_linieC: issuer == gesetzter Wert                 -> True
prm_linieC: resource == gesetzter Wert + '/mcp'     -> True
```

**Linie C steht.** Die Installation kommt allein über das Formular aus dem Fehlzustand
zurück.

## 5. Ein Nebenbefund, nicht in diesem Plan gefixt

Die ERROR-Zeile aus `entry_exapp.main` sagt in Linie B "no public address is stored in
Nextcloud either", obwohl eine gespeichert ist, nur eine unbrauchbare. Die Zeile davor
(`config_values`) sagt das Richtige, und die Handlungsanweisung beider Zeilen ist dieselbe,
also ist es kein Fehlverhalten, sondern ein ungenauer Satz. Er liegt in `src/`, und
`files_modified` dieses Plans ist Planung; deshalb steht er in `deferred-items.md` und nicht
in einem Commit dieses Plans.

## 6. Zustand der Topologie am Ende des Laufs

```
$ occ app_api:app:list
mcp_connector (MCP Connector): 0.1.1 [enabled]
$ docker inspect -f '{{.State.Status}} {{.RestartCount}}' nc_app_mcp_connector
running 0
$ occ user:auth-tokens:list admin
(leer, das Wegwerf-App-Passwort dieses Laufs ist geloescht)
$ git status --porcelain src tests scripts docs
(leer)
```

Die Instanz bleibt in dem Zustand stehen, den Linie C hergestellt hat: App aktiviert,
Container läuft, `public_url` trägt die eigene Adresse dieser Wegwerf-Instanz. Die
Anmeldedaten des Wegwerf-Admins lagen in einer Datei außerhalb des Repositories und sind
zusammen mit dem Registrierungs-Payload gelöscht worden; in diesem Dokument steht keiner.

## 7. Was damit belegt ist

Zwei Wahrheiten aus `05-VERIFICATION.md` sind mit FAILED bewertet worden. Beide werden hier
wörtlich zitiert, und hinter jede gehört ein Satz mit dem Beleg.

**Truth 6, wörtlich:** "Ein in Nextcloud gesetzter Admin-Wert (public_url, DCR, Allowlist)
wirkt in der Praxis ohne gesetzte Umgebungsvariable"

> Belegt durch Linie A: auf einer neu aufgebauten Topologie, deren App-Container nachweislich
> keine `NC_MCP_PUBLIC_URL` trägt (Abschnitt 1.2, `grep -c` gleich 0), erscheint der im
> Admin-Formular gesetzte Wert nach genau einem Disable/Enable-Zyklus zeichengleich als
> `issuer` im Autorisierungsserver-Dokument und als `resource` im Protected-Resource-Dokument,
> während der Ausgangswert derselben Instanz der dokumentierte Default `http://127.0.0.1:8765`
> war. Der 401 des ersten Starts ist dabei kein Fehlschlag mehr, sondern die INFO-Zeile aus
> 05-13, und die Ursache aus 05-12 (der 401 hängt allein am Aktivierungszustand) ist auf einer
> zweiten, unabhängigen Topologie reproduziert.

**Truth 5, wörtlich:** "Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code
(Review-Gate der 'gehärtet'-Zusage)"

> Belegt durch Linie B und Linie C, die beiden Hälften von CR-01: ein `http`-Wert auf einem
> Nicht-Loopback-Host wird in `config_values` abgelehnt (Warnzeile wörtlich im Log), der
> Container bleibt `running` mit unverändertem `RestartCount` 0, die App bleibt `enabled`, der
> `issuer` übernimmt den Wert nicht, und die Admin-Seite bleibt mit 200 erreichbar. Der
> Deadlock aus 05-REVIEW.md, in dem eine Installation über ein Formular unerreichbar gemacht
> wird, ist damit live widerlegt, und Linie C zeigt den Rückweg: derselbe Weg über dasselbe
> Feld, ohne Eingriff in die Datenbank.

Was dieser Lauf nicht belegt, damit niemand mehr hineinliest, als gemessen wurde: die beiden
Schalter `oauth_dcr` und `oauth_allowlist_only` und das Feld `oauth_allowed_clients` sind hier
nicht einzeln durchgemessen worden. Sie gehen durch denselben Lesevorgang und denselben
Overlay wie `public_url` (`config_values.admin_overlay`, ein Aufruf für alle vier Schlüssel,
05-12 M1 hat `oauth_dcr` auf demselben Weg zurückbekommen), und der Wert dieses Laufs ist der
gefährlichste der vier, weil er zum `issuer` wird.
