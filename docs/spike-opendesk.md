# openDesk-Spike (OD-01, OD-02, OD-03)

**Status:** in Arbeit
**Entscheidungsdatum:** offen, wird gesetzt, sobald der Status auf abgeschlossen wechselt
**Nextcloud:** 33.0.7 (Build 33.0.7.1), gelesen mit `occ status` am 2026-08-28 aus der Messumgebung dieser Phase
**AppAPI:** `app_api` 33.0.0, gelesen mit `occ app:list` derselben Instanz (mitgelieferte Serverapp, nicht aus dem App Store)
**Diese ExApp:** 0.1.11, gelesen mit `occ app_api:app:list`, gleich der Fassung in `appinfo/info.xml`
**`integration_openproject`:** 3.1.1, gelesen mit `occ app:list` derselben Instanz nach `occ app:install integration_openproject` am 2026-08-28. Das ist genau die Fassung, für die alle Zeilennummern und Quellenzitate dieses Berichts zu Weg 0 gelesen wurden (Plattformspanne `>=33.0.0 <35.0.0`); die Fassung nennt sich auch selbst so, im Capability-Abschnitt `integration_openproject.app_version` (siehe 2.1)
**`user_oidc`:** noch nicht gemessen (Plan 17-07)
**OpenProject:** 17.7.2 (Community-Bildmarke `openproject/openproject:17.7.2`, Digest `sha256:19a828d6`, Image erstellt am 2026-08-13, gelesen mit `docker image inspect`). Die Instanz nennt dieselbe Fassung selbst: `MAJOR = 17`, `MINOR = 7`, `PATCH = 2` in `/app/lib/open_project/version.rb` des laufenden Containers. Die `coreVersion` aus `GET /api/v3` ist nachgetragen und lautet `17.7.2`, gelesen mit dem API-Schlüssel des Kontos `admin` am 2026-08-28; unauthentifiziert antwortet derselbe Aufruf mit 401, `instanceName` ist `OpenProject`. Damit nennen drei voneinander unabhängige Stellen dieselbe Fassung: der Digest der Bildmarke, die Quelldatei im Container und die API der laufenden Instanz
**Keycloak:** noch nicht gemessen (Plan 17-07)
**Deploy-Daemon:** HaRP, gemessen als `harp_proxy_docker` mit Deploy-ID `docker-install` und `NC Url http://caddy`. Die Bildmarke `ghcr.io/nextcloud/nextcloud-appapi-harp:release` ist gleitend, deshalb steht hier die gelaufene Fassung als Digest und nicht als Tag: `sha256:3b335650`, Image erstellt am 2026-08-14, gelesen mit `docker image inspect`
**Scope:** gemessen wird zweierlei: erstens die Installierbarkeit dieser App in einer openDesk-Umgebung, ausschließlich aus öffentlich ladbaren Quellen an festen Tags, zweitens die beiden Zugriffswege auf die Nutzeridentität gegen OpenProject, lokal in Docker mit gepinnten Fassungen. Ausdrücklich nicht gemessen wird: kein Kubernetes-Cluster wird beschafft, keine openDesk-Installation wird versucht, und es entsteht kein Produktionscode. Die Werkzeugoberfläche und das Budget-Gate der ausgelieferten App stehen in dieser Phase still.

Die Fassungen im Kopfblock werden vor dem Schreiben aus der laufenden Instanz gelesen (`occ status` für den Server, `occ app:list` für `app_api`, `integration_openproject` und `user_oidc`) und nicht aus der Recherche übernommen. Solange eine Zeile `noch nicht gemessen` trägt, steht dort kein Wert aus der Recherche, sondern gar keiner; die Planangabe dahinter nennt den Plan, der die Zeile füllt. Die Messumgebung ist die lokale Docker-Topologie `compose.spike-opendesk.yml`, gepinnt auf die Fassungen aus 1.3 und ausschließlich auf 127.0.0.1 erreichbar (D-02, D-03).

## Entscheidungskriterien, vorab festgelegt

Die Kriterien stehen hier, bevor der erste Messwert entsteht, damit die Zahlen sie nicht nachträglich verschieben können. Sie gelten für alle Abschnitte dieses Berichts.

**Erstens, die Antwortform für Weg 0.** Beurteilt wird die Form der Antwort, nicht ihr Statuscode. Das Kriterium ist von `docs/spike-mail.md` übernommen, wo es einmal durchdacht wurde.

| Beobachtung | Bedeutung |
|-------------|-----------|
| OCS-Umschlag als JSON, mit beliebigem `statuscode` (200, 400, 401, 404, 500) | erreicht: diesen Körper erzeugt nur App-Code, die CSRF- und Impersonationskette hat gehalten |
| HTML-Körper, der Körper beginnt mit `<` | nicht erreicht: das ist die Loginseite, die `ocs._json_payload` heute schon namentlich benennt |
| 3xx mit `Location`, die `/login` enthält | nicht erreicht: die Authentifizierung ist gescheitert |
| eine andere Antwortform | nicht eindeutig: der Punkt bleibt `ungemessen`, die Rohantwort steht in Abschnitt 5 |

Kein Schritt dieses Berichts prüft auf Statuscode 200. Eine 401, die aus `validatePreRequestConditions()` von `integration_openproject` kommt, ist antwortender App-Code und damit ein Erreichbarkeitsbeleg, kein Fehlschlag. Ein Bericht, der hier auf 200 prüft, meldet Weg 0 als unerreichbar und entscheidet OD-02 falsch.

**Zweitens, was `gemessen` heißt.** Ein Messwert gilt nur, wenn vier Bestandteile beisammen sind: ein benannter Aufruf, ein Messwert aus genau diesem Aufruf, mindestens eine Gegenprobe, die zeigt, dass der Messwert nicht auch anders zustande gekommen sein kann, und der Nutzername, unter dem der Aufruf lief. Kein Nutzername, kein Messwert: auf einer Einnutzer-Instanz ist der Unterschied zwischen "die API antwortet" und "die API antwortet als der richtige Mensch" sonst unsichtbar.

**Drittens, was `ungemessen` heißt.** `ungemessen` bedeutet: die Messung war nicht möglich, und der Grund steht an derselben Stelle dabei, samt Datum des Versuchs und, wo es einen gab, dem HTTP-Status oder der Logzeile. `ungemessen` ist in diesem Bericht ein zulässiges Ergebnis und kein Mangel. `verworfen` ist dagegen kein zulässiges Urteil: dieser Bericht spricht es über keinen Weg und über keine Frage aus, weil eine nicht durchgeführte Messung nichts widerlegt (D-03, ROADMAP-Erfolgskriterium 3).

## 1. Installierbarkeit (OD-01)

Dieser Abschnitt steht vor jeder API-Frage, weil ein Zugriffsweg, den niemand installieren kann, keine Frage mehr wert ist. Er ist ausschließlich aus openDesk-Quellen belegt und enthält keinen lokalen Messwert: kein Kubernetes-Cluster wurde beschafft und keine openDesk-Installation versucht (D-01, D-03). Jeder Beleg wurde am 2026-08-28 selbst abgerufen, ohne Anmeldung, an einem festen Tag, und nur das Abgerufene steht hier. Was aus Quellen nicht entscheidbar ist, steht namentlich in Abschnitt 1.4 und nicht als Vermutung im Text.

### 1.1 App Store

**Belegt, nicht offen.** Der Nextcloud App Store ist in openDesk abgeschaltet.

Quelle: Repository `bmi/opendesk/deployment/opendesk` auf `gitlab.opencode.de`, Tag `v1.18.0`, Datei `helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl`. Abgerufen über den Rohpfad `/-/raw/v1.18.0/...` am 2026-08-28, HTTP 200, 11288 Bytes.

```yaml
# helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl, Tag v1.18.0
    appstore:                    # Zeile 79
      enabled: false             # Zeile 80
```

Folge für dieses Produkt: die Ein-Klick-Erzählung, die der Kern dieser App ist, existiert in einer openDesk-Installation nicht. Eine Installation dort ist keine Nutzerhandlung im App Store, sondern eine Betreiberhandlung im Helmfile.

Vier Nebenbefunde aus demselben Block, alle in derselben Datei am selben Tag gezählt:

| Schalter | Zeile | Wert | Bedeutung für dieses Produkt |
|----------|-------|------|------------------------------|
| `contacts` | 61 bis 62 | `enabled: false` | die Werkzeugfamilie Kontakte liegt in openDesk dunkel |
| `spreed` | 75 bis 76 | `enabled: false` | die Werkzeugfamilie Talk liegt in openDesk dunkel |
| `comments` | 81 bis 82 | `enabled: false` | betrifft heute kein Werkzeug, wohl aber jede künftige Kommentarfunktion (OD-04 sieht Kommentare im Entwurf vor) |
| `circles` | 83 bis 84 | `enabled: false` | betrifft heute kein Werkzeug, genannt zur Vollständigkeit |

Zwei der neun Werkzeugfamilien dieser App liegen in openDesk dunkel. Dieser Befund trifft unabhängig vom Ausgang des OpenProject-Teils zu und gehört als Pflichtfrage auf die Liste in Abschnitt 4, nicht nur in diesen Bericht.

Ein fünfter Befund derselben Datei, günstig und nicht gemessen: `adminAudit` trägt in Zeile 77 bis 78 `enabled: {{ .Values.functional.admin.logging.auditLogs.enabled }}`. openDesk hat also schon einen Schalter für Protokollierung. Für die Phasen 18 und 19 ist das ein Anhaltspunkt, gemessen wird er hier nicht.

### 1.2 Deploy-Daemon und Kubernetes

**Belegt, nicht offen, und die Aussage lautet anders als erwartet.** Nicht "AppAPI kann kein Kubernetes", sondern: auf dem Stand, auf den openDesk 1.18.0 gepinnt ist, existiert der Kubernetes-Weg noch nicht, eine Hauptversion darüber existiert er.

Quelle: Repository `nextcloud/app_api`, Zweige `stable33` und `stable34`, abgerufen über `raw.githubusercontent.com` am 2026-08-28. Der entscheidende Beleg ist die Hilfe des Registrierungskommandos, weil sie die zulässigen Werte aufzählt.

```
# app_api stable33, lib/Command/Daemon/RegisterDaemon.php, Zeile 37
'The deployment method that the daemon accepts. Can be "manual-install" or "docker-install".
 "docker-install" is for Docker Socket Proxy and HaRP.'

# app_api stable34, lib/Command/Daemon/RegisterDaemon.php, Zeile 37
'The deployment method that the daemon accepts. Can be "manual-install", "docker-install", or
 "kubernetes-install". "docker-install" is for HaRP (recommended) and the legacy Docker Socket
 Proxy (deprecated, scheduled for removal in Nextcloud 35).'
```

Beide Dateien antworteten mit HTTP 200. Der Unterschied ist der Wert `kubernetes-install`, den nur `stable34` aufzählt.

Die zweite Messung ist die Existenz der Datei, die diesen Wert umsetzt:

| Abruf | Erwartet | Gemessen |
|-------|----------|----------|
| `https://raw.githubusercontent.com/nextcloud/app_api/stable33/lib/DeployActions/KubernetesActions.php` | 404 | HTTP 404, Körper `404: Not Found` |
| `https://raw.githubusercontent.com/nextcloud/app_api/stable34/lib/DeployActions/KubernetesActions.php` | 200 | HTTP 200, 803 Zeilen |

Die Datei an `stable34` trägt in Zeile 37 `public const DEPLOY_ID = 'kubernetes-install';` und arbeitet über HaRP: Zeile 77 baut die Ziel-URL mit `buildHarpK8sUrl($daemonConfig)`, die Zeilen 88 und 91 geben sie an `deploySingleExApp()` und `deployMultiRoleExApp()` weiter.

**Sichtbarkeitsvorbehalt, ehrlich benannt.** In `src/constants/daemonTemplates.js` von `stable34` existiert keine Vorlage für `kubernetes-install`. Selbst ausgezählt am 2026-08-28: acht Vorlagen, davon sechs mit `acceptsDeployId: 'docker-install'` (Zeilen 10, 38, 66, 122, 147, 172) und zwei mit `acceptsDeployId: 'manual-install'` (`manual_install_harp`, Zeile 94, und `manual_install`, Zeile 197), keine einzige mit `kubernetes-install`. Ein Vergleich der Datei zwischen `stable33` und `stable34` ergibt genau drei geänderte Zeilen, alle drei ein hinzugefügtes `deprecated: true` an den Docker-Socket-Proxy-Vorlagen. Der Kubernetes-Weg ist in `stable34` also nur über `occ app_api:daemon:register --k8s` erreichbar, nicht über die Admin-Oberfläche. Die Option selbst steht in derselben Datei wie die Hilfe oben, `lib/Command/Daemon/RegisterDaemon.php` Zeile 54: `'Flag to indicate Kubernetes daemon (uses kubernetes-install deploy ID). Requires --harp flag.'`, gefolgt von sechs weiteren `k8s_`-Optionen in den Zeilen 55 bis 60. Die Gegenprobe: dieselbe Datei an `stable33` enthält die Zeichenkette `k8s` null Mal. Ob das Absicht oder Rückstand ist, ist ungemessen und gehört als Nebenfrage auf die Liste in Abschnitt 4.

**Und der Befund, der die Frage überhaupt stellt: openDesk richtet keinen AppAPI-Daemon ein.** Die projektweite Blob-Suche über die GitLab-API verlangt eine Anmeldung und antwortet ohne sie mit HTTP 401. Der Tarball-Download des Repositories verlangt keine. Gemessen am 2026-08-28:

```
GET https://gitlab.opencode.de/bmi/opendesk/deployment/opendesk/-/[…]/v1.18.0/opendesk-v1.18.0.tar.gz
-> HTTP 200, 2285825 Bytes, entpackt 349 Dateien (Verzeichnis außerhalb dieses Repositories)

grep -ril "app_api\|appapi\|external.app\|exapp" .
-> 0 Treffer

grep -ril "authorization_method\|integration_openproject\|integrationOpenproject" .
-> 3 Dateien: ./docs/architecture.md
              ./docs/debugging.md
              ./helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl
```

Der ausgelassene Pfadteil `[…]` ist der Standard-Download-Pfad, den GitLab für einen Tag anbietet. Er trägt ein Wort, das das Vokabular-Gate dieses Repositories in öffentlichen Seiten nicht zulässt (`tests/unit/test_exapp_env_setup.py`, `FORBIDDEN_VOCABULARY`); ausgelassen ist deshalb der Pfadteil und nicht der Messwert. Die Messwerte sind die Bytezahl und die Dateizahl, der Pfad selbst ist ein Standardpfad und in der GitLab-Dokumentation nachlesbar.

Die Aussage darf damit ohne Vorbehalt geführt werden: im Deployment-Projekt `bmi/opendesk/deployment/opendesk` auf Tag `v1.18.0` kommt AppAPI in keiner Datei vor. Der Gegenbefund im zweiten Griff zeigt, dass das Verfahren greift: dieselbe Suche findet `integration_openproject` in drei Dateien, sie sucht also nicht ins Leere.

**Der eine verbleibende Vorbehalt.** Das Nextcloud-Container-Image von openDesk (`bmi/opendesk/components/platform-development/images/opendesk-nextcloud`, siehe 1.3) wird aus einem anderen, hier nicht mitgelesenen Projekt gebaut. `app_api` ist seit Nextcloud 30 eine mitgelieferte Serverapp; ob das openDesk-Image sie enthält und ob sie eingeschaltet ist, ist aus dem Deployment-Projekt nicht entscheidbar. Das ist die eine echte Rest-Unbekannte von OD-01, sauber getrennt von der Kubernetes-Frage, und geht als Frage 1a in Abschnitt 1.4.

Was auf dem heutigen openDesk-Stand als Daemon-Typ bliebe, ist damit `manual-install`, und zwar in den zwei Varianten, die die Vorlagen oben nennen: `manual_install` und `manual_install_harp` mit dem Anzeigenamen `HaRP Manual Install`. Ob dieser Weg dort betrieblich zulässig ist, ist keine Quellenfrage: die heutige Admin-Dokumentation stellt `manual-install` neutral als Alternative dar, und die früher zitierte Einschränkung ließ sich auf der Seite nicht mehr wiederfinden. Dieser Bericht führt deshalb kein Urteil über die Produktionstauglichkeit von `manual-install`, sondern nur die aufgezählten Werte der `occ`-Hilfe, weil die im Quellcode stehen.

### 1.3 Versionspin 33.0.7 gegen die 34.0.3-Nachweise dieses Projekts

**Belegt, nicht offen.** Quelle: Repository `bmi/opendesk/deployment/opendesk`, Tag `v1.18.0`, Datei `helmfile/environments/default/images.yaml.gotmpl`, abgerufen über den Rohpfad am 2026-08-28, HTTP 200, 52487 Bytes.

```yaml
# helmfile/environments/default/images.yaml.gotmpl, Tag v1.18.0
  nextcloud:                                                          # Zeile 344
    registry: "registry.opencode.de"                                  # Zeile 349
    repository: "bmi/opendesk/components/platform-development/images/opendesk-nextcloud"
    tag: "33.0.7@sha256:16828dac..."                                  # Zeile 351

  nubusKeycloak:                                                      # Zeile 404
    repository: "bmi/opendesk/components/supplier/univention/images-mirror/keycloak"
    tag: "26.7.0@sha256:ba60a3a6..."                                  # Zeile 413

  openproject:                                                        # Zeile 716
    # upstreamRepository: "openproject/open_desk"                     # Zeile 720
    repository: "bmi/opendesk/components/supplier/openproject/images-mirror/open_desk"
    tag: "17.7.2@sha256:9c2181c8..."                                  # Zeile 725
```

Die Digest-Präfixe stehen gekürzt, die vollen Werte stehen in der Quelle an den genannten Zeilen. Nebenbefund mit praktischem Wert: das OpenProject-Image von openDesk ist ein Spiegel von `openproject/open_desk` (Zeile 720), nicht von `openproject/openproject`. Das Original ist öffentlich, die Messumgebung dieser Phase kann also dieselbe Bildmarke fahren wie openDesk.

**Die Aussage, die OD-01 verlangt, hat drei Teile, und alle drei sind belegt.**

Erstens: `appinfo/info.xml` dieser App deklariert in Zeile 235 `<nextcloud min-version="32" max-version="34"/>`. Nextcloud 33 liegt in der erklärten Spanne. Der Pin macht diese App also nicht unzulässig.

Zweitens: sämtliche Ein-Klick- und Erreichbarkeitsnachweise dieses Projekts stehen auf 34.0.x. `docs/spike-dav.md` nennt 34.0.2 (Build 34.0.2.1), `docs/spike-mail.md` nennt 34.0.3 (Build 34.0.3.2), und `compose.exapp.yml` pinnt in Zeile 53 `nextcloud:34.0.3-apache`. In einem Projekt, das seine Nachweise wörtlich nimmt, ist ein Nachweis auf der falschen Hauptversion kein Nachweis. Die Zielumgebung ist damit ungetestet, nicht unzulässig. Das ist ein Unterschied, den dieser Bericht nicht verwischt: ungetestet ist eine Aufgabe, unzulässig wäre eine Absage.

Drittens: der Unterschied ist nicht nur "älter als getestet". Auf 33 fehlt genau die Funktion, die den einzigen plausiblen Kubernetes-Installationsweg trägt (siehe 1.2). Der Versionspin und die Kubernetes-Hürde sind damit dieselbe Hürde, und die Lösung beider ist derselbe Schritt: openDesk auf Nextcloud 34 oder höher. Deshalb steht der Termin dieses Schritts als Frage 5 in Abschnitt 4.

Der Messteil dieser Hürde folgt als eigene Behauptung S0: hält die Ein-Klick-Installation samt AppAPI-Erreichbarkeitsweg auch auf 33.0.7, dem openDesk-Stand, statt nur auf 34.0.3. S0 ist die Zugabe daraus, dass die Messumgebung dieser Phase ohnehin auf 33.0.7 steht.

#### S0: hält die Kette auf 33.0.7

**Gemessen, und die Antwort ist ja.** Dies ist der erste lokal gemessene Wert dieses Berichts. Er sagt nichts über eine openDesk-Installation, sondern genau eines: die Kette aus Registrierung, Deploy-Daemon und Nutzerimpersonation, die dieses Projekt bisher nur auf 34.0.2 und 34.0.3 belegt hatte, hält auch auf der Hauptversion, auf die openDesk gepinnt ist.

**Messumgebung.** `compose.spike-opendesk.yml`, Projekt `nc-mcp-spike-od`, Netz `172.29.43.0/24`, Caddy als einzige Vordertür auf `127.0.0.1:8091`, Deploy-Daemon HaRP, ExApp-Image aus einer Registry auf `127.0.0.1:5001`. Vier Dienste, kein Dienst mit einem Port außerhalb von 127.0.0.1. Aufgebaut und gemessen am 2026-08-28.

**Erste Zeile, Zustand der ExApp.** `occ app_api:app:list`:

```
ExApps:
mcp_connector (MCP Connector): 0.1.11 [enabled]
```

Die Fassung `0.1.11` ist dieselbe, die `appinfo/info.xml` deklariert. `occ app_api:daemon:list` nennt dazu `harp_proxy_docker`, Deploy-ID `docker-install`, `Is HaRP yes`, `NC Url http://caddy`. Die Registrierung selbst ist der eigentliche Messwert dieser Zeile: AppAPI registriert eine ExApp nur, wenn der Heartbeat über die öffentliche Nextcloud-URL zurückkommt, also wenn der Container läuft, das Bild aus der Registry gezogen wurde und die Route `/exapps/*` trägt. Der Lauf des Bootstrap-Skripts endete ohne Fehler und mit `exapp mcp_connector: registered and deployed`.

**Zweite Zeile, ein Werkzeugaufruf gegen die laufende Topologie.** `uv run pytest tests/integration/test_http_tool_call.py -m integration -q` gegen diese Instanz: drei Tests, alle grün. Der tragende darunter legt über das Werkzeug `notes_create` eine Notiz an und liest sie mit `notes_read` wieder, beides als `alice` und mit einem App-Passwort, das aus dem Anfrage-Header kommt und nicht aus dem Prozess. Die zwei Kontrollen derselben Datei liefen mit: ein falsches App-Passwort wird abgewiesen, und eine Anfrage ohne Zugangsdaten erreicht Nextcloud überhaupt nicht.

Daneben, weil der Test den Weg über den Prozess nimmt und nicht den über AppAPI, dieselbe Frage entlang der Impersonationskette. `GET /ocs/v2.php/cloud/user` durch Caddy, mit `OCS-APIRequest: true`, `EX-APP-ID`, `EX-APP-VERSION` und `AUTHORIZATION-APP-API`, ohne ein App-Passwort im Aufruf:

```
# GET /ocs/v2.php/cloud/user?format=json, Impersonation von alice über AUTHORIZATION-APP-API
HTTP 200
ocs.meta.status = ok, ocs.meta.statuscode = 200
ocs.data.id = alice, ocs.data.display-name = alice
```

Der Nutzername steht hier, weil ein Messwert ohne ihn nach dem Kriterium oben keiner ist: auf einer Instanz mit zwei Konten ist der Unterschied zwischen "die API antwortet" und "die API antwortet als der richtige Mensch" sonst unsichtbar.

Ein dritter, mitgemessener Wert zur Route selbst: ein `POST` auf `http://127.0.0.1:8091/exapps/mcp_connector/mcp` ohne Token antwortet mit `HTTP 401` und einem `WWW-Authenticate`-Kopf im Bearer-Schema, mit `error="invalid_token"`, `scope="nextcloud"` und dem Zeiger `resource_metadata="http://127.0.0.1:8091/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"`. Diese 401 ist nach dem Kriterium am Anfang dieses Berichts ein Erreichbarkeitsbeleg und kein Fehlschlag: sie kommt aus unserem eigenen Code hinter HaRP, kein anderer Bestandteil der Kette kennt diesen Zeiger.

**Dritte Zeile, die Gegenprobe.** Derselbe OCS-Aufruf, dieselben Kopfzeilen, `APP_SECRET` durch 64 Nullen ersetzt:

```
# GET /ocs/v2.php/cloud/user?format=json, AUTHORIZATION-APP-API mit 64 Nullen als APP_SECRET
HTTP 401
ocs.meta.status = failure, ocs.meta.statuscode = 997, message = "Current user is not logged in"
```

Ohne diese Zeile beweist die 200 darüber nichts: sie könnte auch von einer Instanz kommen, die jeden Aufruf durchlässt. Der Wert des Headers wird nicht protokolliert, weder der echte noch der aus Nullen, weil er Base64 von `<user>:<APP_SECRET>` ist und damit genau so heikel wie das Geheimnis selbst (Geheimnisregel, Abschnitt 5).

**Was S0 für OD-01 bedeutet.** Dieser Nachweis steht jetzt auf 33.0.7 und ersetzt den geerbten Nachweis auf 34.0.2 (`docs/spike-dav.md`) und 34.0.3 (`docs/spike-mail.md`). Der zweite Teil von Hürde 3 fällt damit weg: die Zielumgebung ist nicht mehr ungetestet, sondern auf der Hauptversion getestet, auf die openDesk gepinnt ist. Was offen bleibt, ist ausschließlich der Installationsweg aus 1.1 und 1.2, und der ist eine Frage an ZenDiS und keine Frage an diese App.

**Die `app_api`-Fassung, und warum sie hier ausdrücklich steht.** `occ app:list` nennt `app_api: 33.0.0`. Damit ist die Annahme A5 dieser Phase gemessen und trifft zu: die in Nextcloud 33.0.7 mitgelieferte AppAPI ist die 33er-Linie, also genau der Stand, dessen `RegisterDaemon.php` in 1.2 den Wert `kubernetes-install` nicht aufzählt. Läge die Fassung über 33.0.0, müsste die Kubernetes-Aussage aus 1.2 neu bewertet werden; sie liegt nicht darüber, und die Aussage steht deshalb unverändert. Das ist ein Beleg aus der laufenden Instanz für einen Befund, der in 1.2 nur aus dem Quellcode kam.

Ein Nebenbefund derselben Messung, der zu Hürde 1 gehört: die vier optionalen Apps, die diese App als Werkzeugfamilien bedient, waren auf 33.0.7 aus dem App Store installierbar und liefen (`notes 6.0.2`, `deck 1.17.5`, `tables 2.3.0`, `spreed 23.0.10`, dazu `mail 5.11.3`). In openDesk ist genau dieser App Store aus (1.1), was die Aussage dort nicht ändert, den Unterschied zwischen den beiden Umgebungen aber messbar macht.

### 1.4 Was offen bleibt

Vier Punkte sind aus Quellen nicht entscheidbar. Sie stehen hier namentlich, mit Grund, und jeder trägt den Verweis auf die Frage in Abschnitt 4, die ihn im ISV-Call am 14.09. abholt. Kein Punkt wird weggelassen, weil er unbequem ist, und keiner wird durch eine Vermutung ersetzt.

| Offener Punkt | Warum aus Quellen nicht entscheidbar | Verweis |
|---------------|---------------------------------------|---------|
| Ist `app_api` im openDesk-Nextcloud-Image enthalten und eingeschaltet? (in 1.2 als Punkt 1a benannt) | Das Image wird aus einem anderen, hier nicht mitgelesenen Projekt gebaut. Der Tarball-Griff über das Deployment-Projekt kann eine mitgelieferte Serverapp im Image grundsätzlich nicht sehen | Abschnitt 4, Frage 6 |
| In welchem Modus läuft `integration_openproject` in openDesk, `oauth2` oder `oidc`? | Die Einrichtung macht der Job `opendesk-openproject-bootstrap`, dessen Logik in einem eigenen Image liegt. Im Deployment-Projekt stehen nur seine Eingaben, ein OpenProject-API-Admin und ein Nextcloud-Admin samt Passwörtern. Das legt den Zwei-Wege-OAuth2-Weg nahe, ist aber Indiz und nicht Beleg; dieser Bericht behauptet deshalb keine Betriebsart | Abschnitt 4, Frage 7 |
| Würde ein Betreiber eine Dritt-ExApp neben der Suite aufnehmen, und wer entscheidet das? | Betriebs- und Verfahrensfrage, öffentlich nicht dokumentiert. Kein Quellcode und kein Helmfile kann sie beantworten | Abschnitt 4, Frage 1 |
| Wann geht openDesk auf Nextcloud 34 oder höher? | Terminfrage an ZenDiS. Sie ist erst durch den Befund aus 1.2 entstanden und in keiner öffentlichen Quelle beantwortet | Abschnitt 4, Frage 5 |

Ein fünfter Punkt aus 1.2 wird nicht als eigene Zeile geführt, aber auch nicht unterschlagen: dass `stable34` keine Oberflächenvorlage für `kubernetes-install` mitbringt, ist ungemessen in der Absicht und geht als Nebenfrage zu Frage 5 in Abschnitt 4 mit.

**Antwort auf OD-01, in drei Sätzen.** Aus openDesk-Quellen belegt ist, dass die Ein-Klick-Erzählung dieses Produkts in einer openDesk-Installation nicht existiert: der App Store ist aus, und AppAPI kommt im Deployment-Projekt an keiner Stelle vor. Aus openDesk- und AppAPI-Quellen belegt ist außerdem, dass auf dem gepinnten Stand 33.0.7 kein Kubernetes-Deploy-Daemon existiert und eine Hauptversion darüber einer existiert. Offen bleibt der Installationsweg selbst, und weil beide Hürden dieselbe sind und mit demselben Schritt fallen, ist das eine Terminfrage an ZenDiS und keine Absage.

Die Trennung, die dieser Bericht durchhält: alles in Abschnitt 1 ist aus openDesk-Quellen belegt, nichts davon ist lokal gemessen. Der erste lokal gemessene Wert entsteht mit S0 in Plan 17-02 und wird dort auch so bezeichnet. Ein Satz, der "in openDesk" sagt und auf einen lokalen Messwert zeigt, ist in diesem Bericht ein Fehler und kein Befund.

## 2. Nutzeridentität gegen OpenProject (OD-02)

### 2.1 Weg 0: Behauptungen S1 bis S6, je Behauptung Messweg, Messwert, Gegenprobe

**Teilweise gemessen am 2026-08-28.** Dieser Abschnitt füllt sich über drei Plänen: die Installation
der App und der Capability-Befund sowie S1, S2 und die Egress-Kontrolle stehen hier (17-05), S3 und S6
folgen in 17-06, S5 in 17-07. Jede Zeile, die noch keinen Wert trägt, sagt das mit `noch nicht
gemessen` und nennt den Plan; keine Zeile trägt einen Wert aus der Recherche.

#### Die installierte Fassung, und warum sie hier zuerst steht

`occ app:install integration_openproject` in der laufenden Nextcloud 33.0.7 endete mit den zwei Zeilen
`integration_openproject 3.1.1 installed` und `integration_openproject enabled`, und `occ app:list`
nennt danach `integration_openproject: 3.1.1` neben `app_api: 33.0.0`. Damit ist die Fassung, für die
die Zeilennummern dieses Berichts und der Recherche gelesen wurden, dieselbe, die hier antwortet.

Das ist keine Formalie: alle Belegstellen zu Weg 0 in diesem Bericht (die Routentabelle unten, die
Vorprüfung `validatePreRequestConditions()`, `Capabilities.php`, die per-Nutzer-Schlüssel) stammen aus
dem Tag `v3.1.1`. Wäre eine andere Fassung installiert worden, müssten sie neu geholt werden, bevor ein
Satz dieses Abschnitts stehen bleibt. Sie sind nicht neu geholt worden, weil sie nicht neu geholt werden
mussten.

Der Store-Zugriff im Container hat getragen, der Rückfall über ein von Hand geladenes App-Archiv war
nicht nötig, und die Plattformspanne `>=33.0.0 <35.0.0` aus der Versionsmatrix stimmt mit der Instanz
zusammen: die Installation wurde von Nextcloud 33.0.7 nicht abgewiesen.

#### Der Capability-Befund: die Frage ist geschlossen, nicht mehr offen

`ARCHITECTURE.md` führte als offen, ob `integration_openproject` eine Capability veröffentlicht oder ob
es den Navigations-Umweg braucht, den `src/mcp_connector/nextcloud/capabilities.py` für Nextcloud Mail
gehen muss. **Gemessen, und die Antwort ist: eine echte Capability, sogar unauthentifiziert.**

```
# GET /ocs/v2.php/cloud/capabilities, ohne jede Anmeldung, nur OCS-APIRequest: true
HTTP 200, Content-Type application/json; charset=utf-8, 6440 Bytes
ocs.meta.status = ok, ocs.meta.statuscode = 200
Abschnitte (5): app_api, bruteforce, integration_openproject, spreed, theming
capabilities.integration_openproject = {
  "app_version": "3.1.1", "groupfolder_version": "0", "groupfolders_enabled": false }
```

Die drei gemessenen Schlüssel sind `app_version`, `groupfolder_version` und `groupfolders_enabled`, und
`app_version` trägt genau die Fassung, die `occ app:list` nennt. Damit hätte eine spätere
Fähigkeitsprüfung nicht nur die Antwort auf "ist die App da", sondern auch die auf "in welcher Fassung",
und das aus einem Aufruf, der ohnehin schon läuft.

**Der Navigations-Umweg ist hier nicht nötig, weil `Capabilities` das Interface `IPublicCapability`
implementiert.** Genau das ist an dem Messwert oben ablesbar und nicht nur aus dem Quelltext
hergeleitet: der Abschnitt steht in einer Antwort, die ohne ein einziges Zugangsdatum entstanden ist.
Nextcloud Mail veröffentlicht überhaupt keinen Abschnitt, weshalb `capabilities.py` dort auf
`/core/navigation/apps` ausweichen muss; für `integration_openproject` fällt dieser zweite Aufruf weg.

Gegenprobe im selben Lauf, damit der Wert nicht nur für den unauthentifizierten Sonderfall gilt:
derselbe Aufruf unter reiner AppAPI-Impersonation von `alice` antwortet ebenfalls 200, mit 11739 Bytes
und 23 Abschnitten statt 5, und `integration_openproject` trägt darin dieselben drei Schlüssel mit
denselben Werten. Der Unterschied 5 gegen 23 ist selbst der Beleg dafür, dass die unauthentifizierte
Antwort wirklich die öffentliche Teilmenge ist und nicht eine zufällig gleich aussehende.

#### Das dritte Konto, das absichtlich nichts verbindet

Für S2 braucht dieser Bericht ein Nextcloud-Konto, das OpenProject **nie** verbunden hat, denn ohne ein
solches Konto ist "die Berechtigung hängt am Nutzer" nicht messbar, sondern nur behauptbar.
`occ user:add --password-from-env carol` hat es angelegt, `occ user:list` nennt danach `admin`, `alice`,
`bob` und `carol`. Das Passwort steht in der git-ignorierten Verbindungsdatei und in keiner verfolgten
Datei.

`occ user:setting carol integration_openproject token` antwortet an dieser Stelle wörtlich
`The setting does not exist for user "carol".` mit Exit-Code 1. Dieser Grundzustand ist ein Messwert und
kein Nebensatz: er ist vor der Einrichtung von Weg 0 aufgenommen, damit die 401 aus S2 später nicht mit
"die Einrichtung war noch nicht fertig" verwechselt werden kann.

### 2.2 Weg 1: PKCE, `expires_in`, Erneuerung ohne Browsersitzung, Zwei-Konten-Negativbeweis

**Gemessen am 2026-08-28 (D-04, voller Consent-Fluss), lokal gegen die laufende Instanz OpenProject
17.7.2 aus dem Kopfblock, ausschließlich über `http://op.localtest.me:8082`.** Der Client ist die
OAuth-Anwendung `nc-mcp-spike-weg1` aus Abschnitt 5.3: **nicht vertraulich** (Häkchen "Confidential"
aus), Scope nur `api_v3`, Rückadresse `http://127.0.0.1:8099/callback`, Feld
`Client Credentials User ID` leer. Dass der Client nicht vertraulich ist, ist die Voraussetzung der
ersten Messung und keine Nachlässigkeit: `force_pkce` gilt wortwörtlich nur für nicht vertrauliche
Clients (K2 Punkt 1), ein vertraulicher Client hätte die falsche Frage beantwortet.

Kein Aufruf dieses Abschnitts benutzt den API-Schlüssel des Kontos `admin`, mit dem der Grundzustand
aus 5.3 entstanden ist. Jede Zeile nennt das Konto, unter dem sie lief.

**Nebenbefund vorweg: die Metadatenlücke ist auch lokal da, und sie ist ein Metadatenmangel und kein
Fähigkeitsmangel.** Beide Wohlbekannt-Dokumente der laufenden Instanz, mit `curl` vom Host geholt,
je Status 200:

```
GET /.well-known/oauth-authorization-server   -> 200
{"issuer":"http://op.localtest.me:8082",
 "authorization_endpoint":"http://op.localtest.me:8082/oauth/authorize",
 "token_endpoint":"http://op.localtest.me:8082/oauth/token",
 "introspection_endpoint":"http://op.localtest.me:8082/oauth/introspect",
 "scopes_supported":["api_v3","scim_v2","mcp","bcf_v2_1"],
 "response_types_supported":["code"],
 "grant_types_supported":["authorization_code","client_credentials","refresh_token"],
 "service_documentation":"https://www.openproject.org/docs/system-admin-guide/authentication/oauth-applications/?go_to_locale=en"}

GET /.well-known/oauth-protected-resource     -> 200
{"resource":"http://op.localtest.me:8082","resource_name":"OpenProject",
 "authorization_servers":["http://op.localtest.me:8082"],
 "scopes_supported":["scim_v2","mcp","bcf_v2_1","api_v3"],
 "bearer_methods_supported":["header"],
 "resource_documentation":"https://www.openproject.org/docs/api/?go_to_locale=en"}
```

Weder ein `registration_endpoint` noch ein `code_challenge_methods_supported` steht darin. Ein Client,
der sich allein nach diesen Dokumenten richtet, verzichtet also auf PKCE und wird abgewiesen: der
Messwert unten belegt beides in derselben Instanz. Der Grund liegt nicht in der Fähigkeit, sondern in
ihrer Bekanntmachung: `force_pkce` steht unbedingt in `config/initializers/doorkeeper.rb:90` am Tag
`v17.7.2` (K2). Diese Instanz ist dabei nicht der Sonderfall, die Dokumente der öffentlichen
Community-Instanz tragen dieselbe Lücke (17-RESEARCH.md, "Die Endpunkte und die Metadatenlücke").
Damit ist der Nebenbefund kein lokales Artefakt, und er geht als **Frage 9 in Abschnitt 4** auf die
ISV-Liste: das fehlende `code_challenge_methods_supported` ist der konkretere und dankbarere Beitrag
für den Community-Kanal als jede Beschwerde, weil die Fähigkeit vorhanden ist und nur die Ansage
fehlt.

**Zum Wort `client_credentials` im Dokument oben, und es ist der zweite Ort dieses Berichts, an den
der Griff aus Pitfall 2 gehört.** Der Grant steht in `grant_types_supported` der laufenden Instanz;
das ist ein wörtliches Zitat des Serverdokuments und keine Einladung. **Kein Aufruf dieses Abschnitts
hat diesen Grant benutzt**, und er könnte auch nichts liefern, was diese Phase braucht: das Feld
`Client Credentials User ID` der Anwendung ist leer geblieben (Abschnitt 5.3), und ohne einen Nutzer
darin gibt OpenProject auf diesem Grant kein Token im Namen eines Menschen aus. Ein Token aus
`client_credentials` wäre genau der Dienstkonto-Weg, der den Satz "der Assistent sieht niemals mehr
als der angemeldete Nutzer" unauffällig unwahr macht (Pitfall 1, T-17-03). Der Griff nach
`client_credentials` findet in diesem Bericht deshalb zwei Stellen, dieses Zitat samt diesem Absatz und
den Absatz in 5.3; jeder Treffer darüber hinaus ist ein Befund.

**Der Messweg des Hauptlaufs, in vier Schritten, alle mit `curl -4` vom Host und einem Cookie-Speicher
außerhalb des Repositoriums.** Verifier und Challenge kommen aus dem bestehenden Weg dieses Projekts
(`pkce()` in `scripts/oauth_flow_check.py:160-164`, per Import aufgerufen, keine Zeile geändert und
nichts neu erfunden); der Verifier ist 86 Zeichen lang, die Challenge nach S256 43 Zeichen.

| Schritt | Aufruf | Status | Was belegt ist |
|---------|--------|--------|----------------|
| 1 | `GET /login` | 200 | die Seite trägt zwei Formulare, beide mit `authenticity_token` (86 Zeichen); genommen wurde das des Formulars `user-login--form` |
| 2 | `POST /login` mit `username=opb`, Passwort aus `.env.spike-opendesk`, `authenticity_token` | 302 | Ziel ist **nicht** `/my/page`, sondern `/two_factor_authentication/request`; die Kette endet nach zwei weiteren 302 auf `/my/page`, und die Seite nennt oben rechts `Bob Spike` |
| 3 | `GET /oauth/authorize` mit `client_id`, `response_type=code`, `redirect_uri`, `scope=api_v3`, `state`, `code_challenge`, `code_challenge_method=S256` | 200 | die Zustimmungsseite, wortwörtlich `Authorize nc-mcp-spike-weg1 to use your account opb?` und `Full API v3 access`; das Formular trägt `code_challenge` und `code_challenge_method` als versteckte Felder weiter |
| 4 | `POST /oauth/authorize` mit denselben Parametern plus `authenticity_token` und `commit=Authorize`, ohne Weiterleitungen zu folgen | 302 | `Location: http://127.0.0.1:8099/callback?code=<43 Zeichen>&state=<der gesendete Wert>`; das `state` der Antwort ist Zeichen für Zeichen das gesendete |

Der Browser-Rückfall des Plans wurde **nicht** gebraucht: der Formularweg trug im ersten Versuch. Auf
dem Port 8099 hörte dabei nichts, und das musste es auch nicht, weil der Code aus dem
`Location`-Kopf gelesen wird und nicht aus einer Zustellung (T-17-02).

**Der Messwert, das Einlösen des Codes.** `POST /oauth/token`, mit `curl -d` und damit
`Content-Type: application/x-www-form-urlencoded` (Pflicht wegen `enforce_content_type`,
`doorkeeper.rb:55`), Parameter `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`,
`code_verifier`, und **ohne** `client_secret`, weil der Client öffentlich ist. Ebenfalls ohne jeden
Cookie-Speicher.

| Feld der Antwort | Gemessener Wert |
|------------------|-----------------|
| HTTP-Status | **200** |
| `token_type` | `Bearer` |
| `scope` | `api_v3` |
| `expires_in` | **7200**, Einheit Sekunden, also zwei Stunden |
| `created_at` | `1787938654` (Unix-Sekunden, 2026-08-28) |
| `access_token` | Länge **43** Zeichen, Präfix `rN3W` |
| `refresh_token` | Länge **43** Zeichen, Präfix `xK-Z` |
| Konto, unter dem der Lauf lief | **`opb`** |

**`expires_in` stimmt mit der Erwartung aus der Quelle überein.** Erwartet waren 7200 aus
`access_token_expires_in 2.hours` (`doorkeeper.rb:61-64`), gemessen sind 7200. Die Admin-Dokumentation
sagt dasselbe ("expire after two hours (default)"). Code, Dokumentation und Messwert nennen denselben
Wert, damit ist er belastbar. Der Wert ist trotzdem gemessen und nicht zitiert worden, weil
`custom_access_token_expires_in` im Initializer auskommentiert vorliegt (Zeile 73-75) und ein
Betreiber ihn setzen kann; in dieser Instanz hat es niemand getan.

**Der Nutzername ist nicht nur behauptet, er ist aus dem Token gemessen.** `GET /api/v3/users/me` mit
`Authorization: Bearer <access_token>` und **ohne** Cookie antwortet 200 und nennt `login opb`, `id 6`,
`admin` nicht gesetzt, `status active`. Das ist genau die Id, die 5.3 für Konto B nennt. Zwei
Gegenproben dazu, weil eine 200 auch von einer offenen Instanz kommen könnte: ein Bearer-Wert aus 43
Nullen antwortet 401 mit `errorIdentifier urn:openproject-org:api:v3:errors:Unauthenticated`, und
ohne den Kopf `Authorization` antwortet derselbe Aufruf ebenfalls 401.

**Ein 415 an diesem Endpunkt ist kein PKCE-Befund, und das ist gemessen statt vermutet.** Derselbe
Endpunkt, mit `Content-Type: application/json` und einem JSON-Körper aufgerufen, antwortet **415**
mit leerem Körper `{}`. Wer `enforce_content_type` übersieht, liest diese 415 als Abweisung des
Flusses; sie ist eine Abweisung der Verpackung. Die Zeile steht hier, damit ein Wiederholungslauf den
Unterschied kennt, bevor er ihn falsch deutet.

#### Die Gegenprobe, ohne die der Hauptlauf nichts beweist: derselbe Client ohne PKCE

Dieselbe Sitzung, dasselbe Konto `opb`, derselbe öffentliche Client, dieselben Parameter, nur **ohne
code_challenge** und ohne `code_challenge_method`:

```
GET /oauth/authorize?client_id=<Client>&response_type=code
   &redirect_uri=http://127.0.0.1:8099/callback&scope=api_v3&state=<zufällig>
   -> HTTP 400
   Text der Seite, vollständig: "An authorization error has occurred. Code challenge is required."
```

**Die Abweisung sitzt an `/oauth/authorize` und nicht erst an `/oauth/token`.** Der Lauf sieht die
Zustimmungsseite nie, es entsteht kein Autorisierungscode, und der `Location`-Kopf fehlt. Damit ist
belegt, dass der Hauptlauf oben nicht auch ohne PKCE funktioniert hätte: derselbe Aufruf mit
`code_challenge` in derselben Sitzung antwortete 200 und lieferte einen Code, ohne
`code_challenge` antwortet er 400 und liefert keinen. Die Antwort ist eine gerenderte HTML-Fehlerseite
mit dem Text oben und kein JSON, ein `error`-Feld gibt es an dieser Stelle also nicht; der Fehlertext
ist der Befund.

Das ist die Zeile, die die Metadatenlücke von oben teuer macht: das Dokument bewirbt PKCE nicht, der
Server verlangt es unbedingt. Ein Client, der sich nach dem Dokument richtet, sieht die 400 und keinen
Hinweis darauf, was ihm fehlt, es sei denn er liest den Text der Seite.

#### Die Erneuerung ohne Browsersitzung, und was dabei wirklich passiert

**Kein Cookie im Spiel.** Der Aufruf lief mit `curl -d` und ausdrücklich **ohne** `-b` und ohne `-c`,
also ohne jeden Cookie-Speicher, in einem Prozess, der keine Sitzung dieser Instanz kennt und nie eine
gekannt hat. Ohne diese Angabe würde der Lauf nichts über "ohne Browsersitzung" beweisen, weil ein
mitgeschickter Sitzungs-Cookie das Ergebnis alleine erklären könnte.

```
POST /oauth/token   (Content-Type: application/x-www-form-urlencoded)
   grant_type=refresh_token
   refresh_token=<Wert aus dem Hauptlauf>
   client_id=<Client>
   -> HTTP 200
   token_type Bearer | expires_in 7200 | scope api_v3
   access_token   Länge 43, Präfix IwAN   (verschieden vom vorherigen)
   refresh_token  Länge 43, Präfix E7kb   (verschieden vom vorherigen)
```

Ein neues `access_token` **und** ein neues `refresh_token`, wie `use_refresh_token`
(`doorkeeper.rb:115`) es erwarten lässt. Dass das erneuerte Token dieselbe Person trägt, ist nicht
angenommen, sondern gemessen: `GET /api/v3/users/me` mit dem neuen Token und ohne Cookie antwortet 200
und nennt `login opb`, `id 6`. Und das alte `access_token` ist sofort tot: derselbe Aufruf mit dem
Token aus dem Hauptlauf antwortet nach der Erneuerung **401**.

**Die zweite Gegenprobe fiel anders aus als erwartet, und das ist der interessanteste Befund dieses
Abschnitts.** Erwartet war, dass der verbrauchte `refresh_token` fehlschlägt. Gemessen hat er beim
ersten Wiedergebrauch **200** geliefert, mit einem zweiten, vollständig gültigen Tokenpaar. Ein
Bericht, der das als "Gegenprobe bestanden" abgehakt hätte, hätte die Instanz falsch beschrieben, und
zwar in einer Richtung, die für einen künftigen Client wichtig ist. Also ist der Mechanismus
nachgemessen worden, mit zwei Ketten, die sich in genau einem Schritt unterscheiden, unmittelbar
hintereinander im selben Lauf, damit verstrichene Zeit als Erklärung ausfällt:

| Kette | Erneuerung | Wird das **neue** `access_token` einmal benutzt | Alter `refresh_token` danach erneut |
|-------|-----------|------------------------------------------------|-------------------------------------|
| A | 200, neues Paar | ja, `GET /api/v3/users/me` -> 200 | **400** `invalid_grant` |
| B | 200, neues Paar | nein, gar nicht | **200**, ein weiteres vollständiges Paar |

**Der Auslöser der Entwertung ist damit gemessen: nicht die Erneuerung selbst und nicht die Zeit,
sondern der erste Gebrauch des neu ausgegebenen `access_token`.** Der Beleg aus der Instanz, der dazu
passt, steht in der laufenden Datenbank: `/app/db/structure.sql:4383` führt die Spalte
`previous_refresh_token` auf `oauth_access_tokens`. Diese Spalte ist die Bedingung, unter der
Doorkeeper die Entwertung des vorherigen `refresh_token` aufschiebt statt sie sofort auszuführen.
Wortwörtlich behauptet dieser Bericht über den fremden Code nur, dass die Spalte existiert; die
Verknüpfung mit dem Verhalten ist die Messung oben und keine Lesart des Quelltexts.

**Praktische Folge, und sie gehört zu OD-04 und nicht in diese Phase:** ein Client, der erneuert und
das neue Token wegwirft, ohne es zu benutzen, kann mit demselben `refresh_token` beliebig viele Paare
ziehen. Wer den Fluss so baut, dass nach der Erneuerung sofort ein Aufruf mit dem neuen Token folgt,
schließt das von selbst.

**Die Gegenprobe mit einem erfundenen Wert und mit einem wirklich entwerteten Wert, beide mit Status
und Fehlerfeld:**

| Aufruf | Status | `error` | Bedeutung |
|--------|--------|---------|-----------|
| `grant_type=refresh_token` mit einem Wert aus 43 Nullen | **400** | `invalid_grant` | ein erfundener Wert wird abgewiesen, der 200 des Hauptlaufs kommt also nicht davon, dass der Endpunkt alles annimmt |
| derselbe Aufruf mit dem entwerteten `refresh_token` der Kette A | **400** | `invalid_grant` | der verbrauchte Wert ist nach dem ersten Gebrauch des Nachfolgetokens endgültig tot, dreimal nachgefahren, dreimal 400 |

Der `error_description`-Text ist beide Male der Doorkeeper-Sammeltext, wortwörtlich "The provided
authorization grant is invalid, expired, revoked, does not match the redirection URI used in the
authorization request, or was issued to another client." Er unterscheidet die Ursachen nicht. Ein
Nebenbefund dazu, den dieser Bericht nur festhält und nicht erklärt: derselbe Fehler kam in einem Lauf
auf Deutsch und in einem anderen auf Englisch zurück, bei identischem Aufruf ohne Kopf
`Accept-Language`. Warum die Sprache wechselt, ist **ungemessen**.

#### Die vier Messwerte, die D-04 wörtlich verlangt, in einer Tabelle

| Messwert | Wie gemessen | Erwartung aus der Quelle | Gemessener Wert | Gegenprobe |
|----------|--------------|--------------------------|-----------------|------------|
| Nimmt `/oauth/authorize` PKCE an | Schritte 1 bis 4 oben, Konto `opb`, `code_challenge_method=S256`, Code eingelöst | 200 und ein Token, aus `force_pkce` (`doorkeeper.rb:90`) | **ja**: 200 auf der Zustimmungsseite, 302 mit `code` (43 Zeichen), 200 am Token-Endpunkt | derselbe Client **ohne code_challenge**, dieselbe Sitzung: **400** an `/oauth/authorize`, "Code challenge is required.", kein Code |
| `expires_in` | Feld der Antwort von `POST /oauth/token` | `7200`, aus `access_token_expires_in 2.hours` (`doorkeeper.rb:61-64`) | **7200 Sekunden** | Code, Admin-Dokumentation und Messwert nennen denselben Wert; `custom_access_token_expires_in` ist in dieser Instanz nicht gesetzt |
| Trägt die Erneuerung ohne Browsersitzung | `grant_type=refresh_token` an `/oauth/token`, **kein Cookie-Speicher**, kein `-b`, kein `-c` | neues Paar, aus `use_refresh_token` (`doorkeeper.rb:115`) | **ja**: 200, neues `access_token` und neues `refresh_token`, `expires_in` wieder 7200, `login opb` aus dem neuen Token | erfundener Wert: 400 `invalid_grant`. Entwerteter Wert: 400 `invalid_grant`. Der Zeitpunkt der Entwertung ist mit zwei Ketten gemessen (Tabelle oben) |
| Zwei-Konten-Negativbeweis (D-05) | `GET /api/v3/work_packages/38` mit dem Token von `opb` und mit dem von `opa`, dazu eine erfundene Id | 404 mit `urn:openproject-org:api:v3:errors:NotFound`, nicht 403 | **404** für `opa`, **200** für `opb`, und die 404 ist von der auf eine nicht existierende Id nicht zu unterscheiden | der Lauf unter `opb` liefert 200 mit dem richtigen Betreff; ohne ihn wäre die 404 auch eine falsche Id. Dazu die erfundene Id 999999999 als zweite Gegenprobe |

#### Der Zwei-Konten-Negativbeweis auf Weg 1 (D-05)

Das zweite Token entstand auf demselben Weg wie das erste: eigener Cookie-Speicher, eigener Verifier,
eigene Zustimmungsseite, Schritte 1 bis 4 unverändert. Beide Läufe endeten mit 200 am Token-Endpunkt,
`expires_in` 7200, `scope api_v3`, `access_token` je 43 Zeichen. Ein Nebenbefund aus dem Lauf von
`opa`: die Anmeldung landete auf `/?first_time_user=true`, es war die erste Anmeldung dieses Kontos
überhaupt, und der Consent-Fluss trug trotzdem im ersten Versuch.

**Wer die Tokens tragen, ist aus den Tokens gemessen und nicht aus dem Skript geschlossen.**
`GET /api/v3/users/me` mit `Authorization: Bearer` und ohne Cookie: das eine Token nennt `login opb`,
`id 6`, das andere `login opa`, `id 5`. Beide `admin` nicht gesetzt. Das sind genau die zwei Ids, die
Abschnitt 5.3 für Konto B und Konto A nennt, und Mitglied des privaten Projekts `spike-privat-b`
(id 3) ist laut 5.3 **nur** `opb`.

| Aufruf | Konto | Status | `errorIdentifier` | Bedeutung |
|--------|-------|--------|-------------------|-----------|
| `GET /api/v3/work_packages/38` | `opb` (Mitglied) | **200** | keiner | die Id ist richtig und das Arbeitspaket existiert: `subject` ist `SPIKE-OD-8471 privat`, `project` ist `Spike Privat B`. Ohne diese Zeile wäre jede 404 unten auch mit einer falschen Id erklärbar |
| `GET /api/v3/work_packages/38` | `opa` (kein Mitglied) | **404** | `urn:openproject-org:api:v3:errors:NotFound` | die Berechtigungsgrenze hält auf Weg 1, unter dem Token des Kontos selbst und nicht unter einem Dienstkonto |
| `GET /api/v3/work_packages/999999999` | `opa` | **404** | `urn:openproject-org:api:v3:errors:NotFound` | dieselbe Antwort wie in der Zeile darüber, und zwar Byte für Byte: je 166 Bytes, gleicher SHA-256 (`96f26f0149c7be10...`), `cmp` meldet keinen Unterschied. OpenProject verrät die Existenz also nicht |

Die `message` ist in beiden 404 wortwörtlich "The work package you are looking for cannot be found or
has been deleted." Kein 403 an keiner Stelle, und kein Unterschied zwischen "gibt es nicht" und "darfst
du nicht".

**Dieselbe Grenze, zwei Ebenen höher gemessen, weil eine Einzelressource allein eine Ausnahme sein
könnte:**

| Aufruf | `opb` | `opa` |
|--------|-------|-------|
| `GET /api/v3/projects/3` | 200 | **404**, `urn:openproject-org:api:v3:errors:NotFound` |
| `GET /api/v3/projects/3/work_packages` | 200, `total 1`, Ids `[38]` | **404**, dieselbe Fehlerkennung |
| `GET /api/v3/work_packages?pageSize=100` | 200, `total 34`, enthält 38 | 200, `total 33`, enthält 38 **nicht** |

Die letzte Zeile ist die aussagekräftigste, weil sie nicht auf eine Id zielt, sondern die Liste
vergleicht: derselbe Endpunkt, dieselbe Seitengröße, ein Arbeitspaket Unterschied, und der Unterschied
ist genau das private. Ein Berechtigungsleck, das eine Einzelabfrage abweist und die Liste nicht,
wäre hier sichtbar geworden.

**Dieselbe Eigenschaft, dieselbe Sprache wie beim DAV-Nachweis dieses Projekts.**
`docs/spike-dav.md` belegt für Nextcloud-Dateien: bob kennt den genauen Pfad von alices Datei, nichts
als die Berechtigungsprüfung steht dazwischen, und die Antwort ist "`404`, never `200`". Für
OpenProject-Arbeitspakete gilt auf Weg 1 wortwörtlich dasselbe: `opa` kennt die genaue Id, und die
Antwort ist 404 und nie 200, ohne Unterschied zu einer Id, die es nicht gibt. Beide Negativbeweise
lassen sich damit in einem Satz führen, und beide gelten unter dem Konto selbst und nicht unter einem
Dienstkonto.

#### Abschluss von 2.2: Leistung, Kosten, und was der lokale Aufbau nicht reproduziert

**Was Weg 1 gemessen leistet.** Ein eigener Autorisierungscode je Nutzer trägt vollständig: PKCE ist
Pflicht und die Pflicht ist mit ihrer Gegenprobe belegt, das Token lebt gemessene 7200 Sekunden, die
Erneuerung trägt ohne jeden Cookie und ohne Browsersitzung, und die Berechtigungsgrenze des
angemeldeten Nutzers hält bis auf die Ebene der Liste, ohne dass irgendwo ein Dienstkonto oder ein
Administratorschlüssel im Spiel wäre.

**Was Weg 1 kostet.** Einen Zustimmungsschritt im Browser je Nutzer, der nicht wegzuautomatisieren ist,
weil `/oauth/authorize` eine OpenProject-Sitzung verlangt (`resource_owner_authenticator`,
`doorkeeper.rb:35-39`); einen zweiten OAuth-Client, den ein Betreiber in der OpenProject-Verwaltung
von Hand anlegen muss, weil sich zu 17.7.2 kein dokumentierter Weg zum Seeden einer OAuth-Anwendung
finden ließ und `registration_endpoint` in den Metadaten fehlt; und ein zweites Tokenlager neben dem
bestehenden, samt der Erneuerungsregel aus dem Befund oben.

**Was der lokale Aufbau ausdrücklich nicht reproduziert, und deshalb steht in diesem Abschnitt kein
Satz, der "in openDesk" sagt und auf einen der Messwerte oben zeigt.** In openDesk gibt es wegen
`OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"` kein lokales Anmeldeformular; genau dieses
Formular ist aber der zweite Schritt des gemessenen Messwegs oben. Der Zustimmungsfluss hat dort einen
zusätzlichen Umleitungsschritt über Keycloak, und dieser Schritt ist hier **ungemessen**. Ebenfalls
ungemessen ist die Scope-Pflicht für ein OIDC-JWT (`scope`-Anspruch mit `api_v3`, Breaking Change in
OpenProject 16.0.0): im lokalen OAuth-Modus, in dem alle Messwerte oben entstanden sind, ist sie
unsichtbar, weil OpenProject die Tokens selbst ausgibt. Beide Punkte gehören auf die ISV-Liste in
Abschnitt 4 und nicht in die Messwerttabelle.

**Aufräumen, und es ist gegengeprobt.** Alle in diesem Abschnitt entstandenen Tokens sind nach der
letzten Messung über `POST /oauth/revoke` widerrufen worden, zwanzig Werte, je Status 200. Die
Gegenprobe: `GET /api/v3/users/me` mit dem Token von `opb` und mit dem von `opa` antwortet danach je
**401**. Die Cookie-Speicher und die Zwischendateien lagen unter dem Temporärverzeichnis und niemals im
Repositorium; sie sind gelöscht. Kein Wert steht in diesem Bericht, nur Längen, Vier-Zeichen-Präfixe,
Statuscodes und Feldnamen (T-17-01).

### 2.3 Die SSRF-Grenze und was sie wirklich abdeckt

**Gemessen (D-06), im laufenden ExApp-Container, mit demselben Resolver, den die Produktion benutzt, und ohne eine Zeile Produktionscode zu ändern.** Der Container ist `nc_app_mcp_connector`, Zustand `running`, Bildmarke `127.0.0.1:5001/mcp_connector:0.1.11`, Netz `nc-mcp-spike-od-net`. Die Messung importiert `mcp_connector.oauth.cimd` und ruft es auf; sie legt keine Test-Datei an, ändert keinen Import und schreibt nichts in `src/`.

**Erste Zeile, die Auflösung der Nachbardienste.** `cimd._system_addresses(<name>, 80)`:

```
_system_addresses('nextcloud', 80)   -> ['172.29.43.129']
_system_addresses('caddy', 80)       -> ['172.29.43.10']
_system_addresses('appapi-harp', 80) -> ['172.29.43.131']
_system_addresses('openproject', 80) -> raised gaierror
```

Die drei laufenden Nachbardienste stehen unter ihrem Compose-Dienstnamen für private Adressen aus `172.29.43.0/24`, genau wie erwartet. Der Name `openproject` löst nicht auf, und das ist kein Fehlschlag der Messung, sondern der Zustand der Stufe: das Profil `op` ist in diesem Plan nicht gestartet, und Docker gibt einem Dienst ohne laufenden Container keinen DNS-Eintrag. Diese Zeile ist ausdrücklich mitgemessen und mitgeschrieben, weil sie sonst in der dritten Zeile als scheinbare Sperrung wiederkehrt.

**Zweite Zeile, dieselben Adressliterale durch `cimd.target_allowed()`.** Erwartung `False`, gemessen `False`, samt der beiden Flags, an denen es liegt:

```
target_allowed(172.29.43.129) -> False   [nextcloud,    is_private=True, is_global=False]
target_allowed(172.29.43.10)  -> False   [caddy,        is_private=True, is_global=False]
target_allowed(172.29.43.131) -> False   [appapi-harp,  is_private=True, is_global=False]
target_allowed(172.29.43.10)  -> False   [Literal desselben /24]
target_allowed(172.29.43.128) -> False   [Literal desselben /24]
target_allowed(172.29.43.254) -> False   [Literal desselben /24]
```

Die drei Literale am Ende sind der Ersatz für den Namen, der heute nicht auflöst: die Adresse, die `openproject` bekommen wird, liegt in demselben `/24`, und für dieses `/24` ist die Antwort an beiden Rändern und in der Mitte gemessen. Damit steht der Befund für OpenProject fest, ohne dass dieser Plan Stufe B hochfahren muss.

Der Negativkatalog dazu ist der bestehende aus `tests/unit/test_oauth_cimd.py` (Zeilen 179 bis 202) und kein neu erfundener. Im selben Container gefahren: 12 von 12 Adressen des Katalogs abgelehnt, 3 von 3 Adressen der Positivliste zugelassen, keine unerwartete Abweichung. Der Katalog trägt die drei gemessenen Lücken, an denen ein einzelnes Flag nicht reicht (`100.64.0.1`, `64:ff9b::7f00:1`, `224.0.0.1`); die Prüfung ist deshalb eine Konjunktion aus sieben Fragen und nicht ein Flag.

**Dritte Zeile, `cimd.resolve_addresses()`, also die ganze Grenze.** Erwartung `None`, gemessen `None`, und die Logzeile sagt, welche der beiden Ursachen zutrifft:

```
resolve_addresses('nextcloud', 80)   -> None    LOG: a document target was refused: an address of it is not public
resolve_addresses('caddy', 80)       -> None    LOG: a document target was refused: an address of it is not public
resolve_addresses('appapi-harp', 80) -> None    LOG: a document target was refused: an address of it is not public
resolve_addresses('openproject', 80) -> None    LOG: a document target did not resolve: gaierror
```

Die vierte Zeile ist der Grund, warum die Unterscheidung im Protokoll steht: derselbe Rückgabewert `None`, aber eine andere Ursache. Drei Namen wurden von der Regel abgelehnt, einer war überhaupt nicht auflösbar. Ein Bericht, der nur `None` notiert, hätte einen Resolver-Fehlschlag als Sperrung gelesen.

Dazu die Regel, die den Befund über die Einzeladresse hinaus trägt: `resolve_addresses` verwirft den **ganzen Namen**, sobald **eine** seiner Adressen abgelehnt wird (`cimd.py`, Docstring: "Not 'take the good one'"). Ein Name, der auf eine öffentliche und eine private Adresse zeigt, ist damit vollständig gesperrt und nicht teilweise erlaubt.

**Gegenprobe, ohne die der Messwert nichts beweist.** Im selben Lauf, im selben Container, mit demselben Resolver, zwei öffentliche Namen:

```
resolve_addresses('one.one.one.one', 443) -> ['1.0.0.1', '1.1.1.1', '2606:4700:4700::1111', '2606:4700:4700::1001']
resolve_addresses('example.com', 443)     -> ['172.66.147.243', '104.20.23.154', '2606:4700:10::ac42:93f3', '2606:4700:10::6814:179a']
```

Beide liefern eine Adressliste. Damit ist das dreifache `None` oben nicht mit einem kaputten Resolver im Container erklärbar, und die Sperrung ist die Regel und nicht die Umgebung.

**Die Einordnung, und sie ist der eigentliche Wert dieser Messung.** Die Grenze sitzt nicht auf dem Weg zu einem fremden Host, sondern auf dem Weg zum Client-Id-Metadatendokument eines fremden OAuth-Clients. `cimd.py` sagt das im eigenen Modul-Docstring: es ist die erste und bislang einzige Stelle dieses Projekts, an der eine Anfrage das Ziel einer ausgehenden Anfrage von uns wählt; jeder andere Aufruf geht an die konfigurierte Nextcloud, weil die Basis-URL aus `NC_MCP_URL` kommt und nie aus einer Anfrage. Der in dieser Phase gemessene Zugriffsweg auf OpenProject berührt diese Grenze überhaupt nicht, weil es keine zweite Basis-URL gibt: Weg 0 läuft über Nextcloud, und Nextcloud ist die konfigurierte Basis. Wer aus dem Messwert oben liest, dieser Connector könne OpenProject im Cluster nicht erreichen, liest eine Aussage über einen Weg, den es heute nicht gibt.

**Der Entwurfsbefund für OD-04.** Er verlangt keine Codeänderung in dieser Phase und ist die Entscheidung, die v2.0 zu treffen hat. Wer `target_allowed` für eine zweite Basis-URL wiederverwendet, sperrt jede Cluster-Installation aus: die Messung oben ist genau der Fall, und sie fällt in einer openDesk-Installation nicht anders aus als hier, weil ein Dienst im selben Cluster immer eine private Adresse trägt. Wer sie nicht wiederverwendet, braucht eine eigene, ausdrücklich begründete Prüfung für eine URL, die aus den Admin-Einstellungen und niemals aus einer Anfrage kommt: die Begründung ist der Unterschied zwischen einer Adresse, die ein Angreifer wählt, und einer, die ein Administrator einträgt. Beide Wege sind vertretbar, ein stilles Wiederverwenden ist es nicht.

### 2.4 Welcher Weg trägt, als Folge dieser Messungen

noch nicht gemessen, Plan 17-09

### 2.5 Was ungemessen blieb, und warum die Messung nicht möglich war

noch nicht gemessen, Plan 17-09

## 3. API-Form (Vorarbeit für OD-04, kein Requirement dieser Phase)

noch nicht gemessen, Plan 17-09

## 4. Fragenliste für den ISV-Call am 14.09. (OD-03)

noch nicht gemessen, Plan 17-08

**Vorgemerkt aus Abschnitt 2.2, damit der Verweis dort nicht ins Leere zeigt.** Frage 9: OpenProject
17.7.2 erzwingt PKCE für nicht vertrauliche Clients (`force_pkce`, gemessen in 2.2), bewirbt in
`/.well-known/oauth-authorization-server` aber kein `code_challenge_methods_supported` und keinen
`registration_endpoint`. Die Frage lautet, ob die Lücke Absicht ist, und der Grund, sie zu stellen,
ist ein gemessener Fehlschlag: ein Client, der sich allein nach diesem Dokument richtet, lässt PKCE
weg und wird abgewiesen. Plan 17-08 formuliert die Frage aus und ordnet sie in die Liste ein.

## 5. Rohmesswerte

**Geheimnisregel, gültig für jede Zeile dieses Abschnitts.** Diese Datei liegt in einem öffentlichen Repository. Protokolliert werden ausschließlich Statuscodes, Feldnamen, Zahlen, Längen und Präfixe. Niemals protokolliert wird ein `access_token`, ein `refresh_token`, ein Autorisierungscode, ein `client_secret` oder ein Wert des Headers `AUTHORIZATION-APP-API`: dieser Wert ist Base64 von `<user>:<APP_SECRET>` und damit genau so heikel wie das Geheimnis selbst. Tokenwerte werden auf ihre Länge und ihr Präfix reduziert. `expires_in` ist eine Zahl und darf stehen. Vor jedem Commit an dieser Datei läuft ein Griff nach den vier Zeichenketten, die dieses Projekt als Geheimnisverdacht führt: das JWT-Präfix, das Bearer-Schema mit einem Wert dahinter, und `refresh_token` sowie `client_secret` je mit einem Gleichheitszeichen. Die vier Muster stehen hier bewusst umschrieben und nicht wörtlich: sonst findet der Griff diese Zeile selbst, und ein Gate, das an seiner eigenen Regel scheitert, wird beim nächsten Lauf ignoriert statt gelesen.

Die übrigen Unterabschnitte werden von den Plänen 17-04 bis 17-09 gefüllt.

### 5.1 Stufe B: der erste Start von OpenProject 17.7.2

Gemessen am 2026-08-28 in der Topologie `compose.spike-opendesk.yml`, Profil `op`.

**Behauptung, die geprüft wurde (aus der Recherche, nicht aus der Instanz):** der erste Start dauert 30 bis 90 Minuten, davon meist Warten, und OpenProject allein braucht mindestens 4 GB Hauptspeicher. Beide Zahlen sind in 17-RESEARCH.md als Erwartung geführt, die eine aus der Fehlerbildtabelle von Pitfall 1, die andere aus den Systemanforderungen von openproject.org.

**Messweg:** `docker compose -f compose.spike-opendesk.yml --profile op up -d openproject`, danach alle 20 Sekunden `curl` auf `http://op.localtest.me:8082/login` zusammen mit `docker inspect -f '{{.State.Status}}:{{.State.OOMKilled}}:{{.State.ExitCode}}'`, bis der erste Aufruf 200 antwortet oder der Container endet. Zeitmarken aus `docker logs -t`, Speicher aus `docker stats --no-stream`, freier Speicher der WSL2-VM aus `free -m` in einem Wegwerfcontainer.

| Messwert | Ergebnis |
|----------|----------|
| Container gestartet | 2026-08-28 16:42:37 UTC (`docker inspect -f '{{.State.StartedAt}}'`) |
| erste 200 auf `/login` | 16:44:14 UTC, also **95 Sekunden** nach der ersten Logzeile, nicht 30 bis 90 Minuten |
| Speicher des Containers nach dem Start | **1,964 GiB** von 7,603 GiB, 25,83 Prozent, nicht die erwarteten mindestens 4 GB |
| verfügbarer Speicher der WSL2-VM danach | 4036 MiB von 7785 MiB total |
| OOM-Killer | `OOMKilled: false`, `ExitCode: 0`, kein Neustart, kein zweiter Versuch |
| Platz | 925 GiB frei im Dateisystem der VM, die 20 GB der Systemanforderungen sind keine Grenze |
| Bildmarke | `openproject/openproject:17.7.2`, Digest `sha256:19a828d66e7c23322d1fbbaa974e7b712ef03c2badf1b10466ca45710e6bbbe5`, 882512785 Bytes, erstellt 2026-08-13 |

**Gegenprobe, ohne die die 95 Sekunden nichts wert wären:** eine 200 auf `/login` könnte auch von einem noch nicht fertig aufgesetzten Rails kommen, das die Seite schon ausliefert, während die Seed-Phase weiterläuft. Drei Belege dagegen, alle aus demselben Lauf:

* Die vier Aufrufe vor dem letzten antworteten 502, 502, 502 und 503. Die 200 ist also der Übergang und nicht der Anfangszustand.
* Die Seed-Phase steht namentlich und abgeschlossen im Log: die Reihe `*** Loading <modul> seed data` bis `*** Seeding data from environment variables`, und zwar **vor** der Zeile `=> Booting Puma`. Danach `Worker 0` und `Worker 1 ... booted`, beide um 16:44:13 UTC.
* Die eingebaute Datenbank der All-in-one-Bildmarke läuft im selben Container: `listening on IPv4 address "0.0.0.0", port 5432` um 16:43:38 UTC. Ein Rails mit halb gefüllter Datenbank hätte die Seed-Reihe nicht zu Ende geschrieben.

**Einordnung, damit die Zahl nicht überdehnt wird:** gemessen ist der erste Start dieser Bildmarke auf diesem Rechner, mit leeren Bänden und ohne Last. Die Zahl widerlegt die Systemanforderung von openproject.org nicht, denn die gilt für eine benutzte Instanz mit mehreren Nutzern; sie widerlegt nur die Annahme, dass dieser Aufbauschritt hier eine Stunde kostet und am Speicher dieser WSL2-VM scheitert. Das aus 17-02 mitgeführte Speicherrisiko ist damit für Stufe B **nicht eingetreten**: es war keine `.wslconfig` nötig, kein `wsl --shutdown`, und die Container der beiden fremden Projekte auf diesem Rechner liefen durch.

### 5.2 Die Namensfalle, in beide Richtungen gemessen

**Behauptung:** `op.localtest.me:8082` ist ein Name, der aus dem Browser des Entwicklers und aus dem Nextcloud-Container an dieselbe Instanz führt. Ohne das ist Weg 0 nicht einrichtbar, weil `integration_openproject` OpenProject aus dem Nextcloud-Container heraus unter genau der Adresse aufruft, die ein Mensch in `openproject_instance_url` eingetragen hat.

| Messweg | Messwert |
|---------|----------|
| `curl` vom Host auf `http://op.localtest.me:8082/login` | 200 |
| `curl` aus dem Nextcloud-Container auf denselben Namen | 200 |
| dieselbe Anfrage aus dem Container mit `%{remote_ip}` | `172.29.43.10`, die feste Adresse von Caddy in dieser Topologie |
| `curl` aus dem Container auf `http://127.0.0.1:8082/login` | scheitert, `curl: (7) Failed to connect`, Code `000` |
| veröffentlichte Ports des Dienstes `openproject` | keine, `docker port` antwortet leer |
| Bindung des Zugangs | `8082/tcp` auf `127.0.0.1:8082` am Caddy-Dienst, keine andere Adresse |

**Gegenprobe:** die zwei gleichlautenden 200 allein beweisen noch nicht, dass der `extra_hosts`-Eintrag die Arbeit tut; sie könnten auch von einer öffentlichen Auflösung von `localtest.me` kommen. Die vierte Zeile schließt das aus: `127.0.0.1:8082` bedeutet im Nextcloud-Container der Container selbst, und dort hört nichts. Die dritte Zeile nennt die Adresse, die tatsächlich benutzt wurde, und es ist die aus `extra_hosts`.

**Ein Fund, der für Plan 17-05 zählt.** `getent hosts op.localtest.me` antwortet im Nextcloud-Container mit `::1` und nicht mit `172.29.43.10`: `localtest.me` hat einen öffentlichen AAAA-Eintrag auf die IPv6-Loopbackadresse, und ein Aufruf, der IPv6 bevorzugt, landet damit im Container selbst statt bei Caddy. Der `extra_hosts`-Eintrag ist ein reiner IPv4-Eintrag, und `getent ahostsv4` liefert entsprechend `172.29.43.10`. Gemessen ist, dass der Aufrufer, auf den es ankommt, die IPv4-Adresse nimmt: derselbe Aufruf durch die PHP-Erweiterung `curl` desselben Containers, also durch den Weg, den `integration_openproject` geht, meldet `php_remote_ip=172.29.43.10` und Code 200. Sollte in 17-05 ein Aufruf von Nextcloud aus dennoch ins Leere laufen, ist dieser AAAA-Eintrag die erste Stelle, an der zu schauen ist, und nicht die Caddy-Regel.

### 5.3 Aufbau, nicht Messung

Die Überschrift dieses Unterabschnitts ist wörtlich zu nehmen: was hier steht, ist **Aufbau, nicht Messung**. Es steht hier, weil der Zwei-Konten-Negativbeweis beider Wege (D-05) Daten braucht, die die Seed-Daten von OpenProject nicht hergeben: die Seed-Instanz hat ein Projekt und wenige Arbeitspakete, und ein Negativbeweis auf einer Instanz ohne fremde, nicht zugängliche Daten ist leer und sieht trotzdem grün aus (Pitfall 3, Absatz "Die Datenlage"). Angelegt am 2026-08-28 über die API v3 von OpenProject mit `Basic apikey:<OP_API_TOKEN>` des Kontos `admin`.

| Was | Aufruf | Ergebnis |
|-----|--------|----------|
| Konto A | `POST /api/v3/users` | 201, `login opa`, Vorname Alice, `id 5`, `status active`, `admin false` |
| Konto B | `POST /api/v3/users` | 201, `login opb`, Vorname Bob, `id 6`, `status active`, `admin false` |
| privates Projekt | `POST /api/v3/projects` | 201, Name `Spike Privat B`, Identifier `spike-privat-b`, `id 3`, `public false` |
| Rolle | `GET /api/v3/roles` | `Member` ist Rollen-Id 3 |
| Mitgliedschaft, **nur** Konto B | `POST /api/v3/memberships` | 201, Prinzipal `Bob Spike`, Rolle `Member` |
| Arbeitspaket im privaten Projekt | `POST /api/v3/projects/3/work_packages` | 201, Betreff `SPIKE-OD-8471 privat`, Typ `Task`, **Id 38** |

Die Arbeitspaket-Id `38` ist eine vom Server vergebene Id und kein Geheimnis; sie steht als `OP_WP_ID` in der git-ignorierten Verbindungsdatei, damit die Folgepläne sie nicht erraten müssen. Das Suchwort `SPIKE-OD-8471` ist so gewählt, dass es an keiner anderen Stelle dieser Instanz vorkommt: ein Negativbeweis, dessen Suchwort auch in einem Seed-Datensatz steht, findet etwas und beweist das Gegenteil von dem, was er soll.

**Die Asymmetrie ist der ganze Punkt.** `GET /api/v3/memberships` gefiltert auf Projekt 3 antwortet mit `total: 1` und nennt genau `Bob Spike` mit der Rolle `Member`. Alice ist **nicht** Mitglied. Ohne diese Asymmetrie ist der Negativbeweis beider Wege leer.

**Gegenprobe des Aufbaus:** `GET /api/v3/work_packages/38` mit dem API-Schlüssel antwortet 200, und der Betreff enthält `SPIKE-OD-8471`. Damit ist belegt, dass das Arbeitspaket wirklich existiert und lesbar ist, das private Projekt also nicht bloß leer angelegt wurde. Zwei weitere Gegenproben gelten dem Schlüssel selbst, denn eine 200 könnte auch von einer offenen Instanz kommen: derselbe Aufruf mit einem Schlüssel aus 70 Nullen antwortet 401, und ohne jede Anmeldung antwortet er ebenfalls 401.

**Diese Zeilen sind ausdrücklich nicht der Negativbeweis.** Der Negativbeweis läuft in den Plänen 17-04 und 17-06 unter den Konten selbst, nicht unter dem Admin-Zugang. Der Admin-Zugang, mit dem dieser Grundzustand entstanden ist, ist **nicht Teil der gemessenen Kette**: er hat dieselbe Rolle, die in `docs/spike-dav.md` das Deck-Board hat, das eine Messung erst möglich macht und selbst nichts beweist. Ein Messwert, der unter `apikey:<OP_API_TOKEN>` des Kontos `admin` entsteht, sagt über die Berechtigungen von `opa` und `opb` nichts, weil ein Administrator in OpenProject alle Projekte sieht.

**Das Feld "Client Credentials User ID" der OAuth-Anwendung ist leer geblieben.** Der Satz steht hier, weil ein Prüfer genau danach fragt: ein Wert in diesem Feld hätte der Anwendung ein festes Konto hinterlegt, jede Antwort wäre die dieses einen Kontos gewesen, und der Satz "der Assistent sieht niemals mehr als der angemeldete Nutzer" wäre unwahr geworden, ohne dass eine einzige Messung rot geworden wäre (Pitfall 2). Ebenso ist das Häkchen "Confidential" ausgeblieben, weil `/app/config/initializers/doorkeeper.rb:90` dieser Fassung `force_pkce` setzt und der Kommentar dort PKCE ausdrücklich für nicht vertrauliche Clients verlangt; genau dieses Verhalten misst Plan 17-04. In dieser Phase wurde kein Dienstkonto angelegt und keine Umgebungsvariable gesetzt, die einen globalen Basic-Auth-Nutzer oder einen instanzweiten API-Schlüssel einführt.

Dieser Absatz ist zugleich die Stelle, an die der Griff aus Pitfall 2 gehört. Er sucht in den Dateien dieser Phase nach den drei Wegen, die den Berechtigungsdurchgriff unauffällig brechen, und er findet in diesem Bericht ausschließlich die Schreibweise `apikey:<OP_API_TOKEN>`, also den benannten Messweg des Aufbaus mit einem Platzhalter an der Stelle des Werts, und niemals einen Schlüssel selbst. Der Platzhalter steht so und nicht ausgeschrieben, damit der Griff beim nächsten Lauf gelesen und nicht übergangen wird: ein Treffer in diesem Absatz ist erwartet, jeder Treffer außerhalb ist ein Befund.

**Drei Abweichungen beim Aufbau, protokolliert statt geglättet:**

1. **Das Seed-Passwort `admin` wurde von der Instanz abgelehnt.** Der Owner konnte sich mit der dokumentierten Vorgabe `admin`/`admin` nicht anmelden: `User.check_password?` war falsch, `failed_login_count` stand auf 6, `force_password_change` auf true, das Konto war **nicht** gesperrt. Aufgelöst wurde es, indem das Passwort des Benutzers `admin` per `rails runner` auf den Wert in `OP_ADMIN_PASSWORD` gesetzt, `force_password_change` auf false und `failed_login_count` auf 0 gestellt wurde. **Warum das Seed-Passwort abwich, ist nicht untersucht** und steht hier als offener Punkt und nicht als Vermutung. Der erzwungene Passwortwechsel hat damit nicht stattgefunden; für die Messungen dieser Phase ist das ohne Folge, weil keiner der beiden Wege am Passwort des Administrators hängt.
2. **Nebenbefund aus derselben Stelle, belegbar:** die Passwortregeln dieser Fassung verlangen alle vier Zeichenklassen. Die Fehlermeldung lautet wörtlich `Password Must include characters of the following types: lowercase, uppercase, numeric, special`. Die beiden Wegwerfpasswörter der Konten `opa` und `opb` sind 20 Zeichen lang und enthalten alle vier Klassen; die Regel ist damit der Grund für ihre Form und keine Zierde.
3. **`OPENPROJECT_DEFAULT__LANGUAGE=en` regiert das Seed-Konto nicht.** Gemessen an `GET /api/v3/users`: `admin` trägt `language de`, die beiden in diesem Plan angelegten Konten tragen `language en`. Für die Messungen ist das ohne Folge, weil sie unter `opa` und `opb` laufen und die Feldnamen der API v3 ohnehin englisch sind. Wer in einem Folgeplan eine Beschriftung aus der Oberfläche abliest, muss aber wissen, unter welchem Konto er sie abliest.

## Was diese Messung nicht beweist

noch nicht gemessen, Plan 17-09
