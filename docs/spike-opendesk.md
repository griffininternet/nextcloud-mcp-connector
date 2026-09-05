Warning: truncated output (original token count: 58470)
Total output lines: 2645

# openDesk-Spike (OD-01, OD-02, OD-03)

**Status:** done, mit dem Ergebnis: beide Zugriffswege sind gemessen, Weg 0 trägt im gemessenen Modus `oauth2` vollständig und ist der billigere, Weg 1 trägt unabhängig von der Betriebsart und kostet Zustimmung je Nutzer und einen zweiten Client
**Entscheidungsdatum:** 2026-08-29, das Datum des letzten Messlaufs (5.5.4 und 5.6)
**Nextcloud:** 33.0.7 (Build 33.0.7.1), gelesen mit `occ status` am 2026-08-28 aus der Messumgebung dieser Phase
**AppAPI:** `app_api` 33.0.0, gelesen mit `occ app:list` derselben Instanz (mitgelieferte Serverapp, nicht aus dem App Store)
**Diese ExApp:** 0.1.11, gelesen mit `occ app_api:app:list`, gleich der Fassung in `appinfo/info.xml`
**`integration_openproject`:** 3.1.1, gelesen mit `occ app:list` derselben Instanz nach `occ app:install integration_openproject` am 2026-08-28. Das ist genau die Fassung, für die alle Zeilennummern und Quellenzitate dieses Berichts zu Weg 0 gelesen wurden (Plattformspanne `>=33.0.0 <35.0.0`); die Fassung nennt sich auch selbst so, im Capability-Abschnitt `integration_openproject.app_version` (siehe 2.1)
**`user_oidc`:** 8.11.0, gelesen mit `occ app:list` derselben Instanz nach `occ app:install user_oidc` am 2026-08-29. Das ist genau die Fassung, für die die Zeilennummern zu `TokenService.php` und zu den drei Listenern gelesen wurden. `integration_openproject` 3.1.1 verlangt mindestens 7.2.0 (`Application.php:70`, `MIN_SUPPORTED_USER_OIDC_APP_VERSION`); die Installation wurde von Nextcloud 33.0.7 nicht abgewiesen
**OpenProject:** 17.7.2 (Community-Bildmarke `openproject/openproject:17.7.2`, Digest `sha256:19a828d6`, Image erstellt am 2026-08-13, gelesen mit `docker image inspect`). Die Instanz nennt dieselbe Fassung selbst: `MAJOR = 17`, `MINOR = 7`, `PATCH = 2` in `/app/lib/open_project/version.rb` des laufenden Containers. Die `coreVersion` aus `GET /api/v3` ist nachgetragen und lautet `17.7.2`, gelesen mit dem API-Schlüssel des Kontos `admin` am 2026-08-28; unauthentifiziert antwortet derselbe Aufruf mit 401, `instanceName` ist `OpenProject`. Damit nennen drei voneinander unabhängige Stellen dieselbe Fassung: der Digest der Bildmarke, die Quelldatei im Container und die API der laufenden Instanz
**Keycloak:** 26.7.0 (Bildmarke `quay.io/keycloak/keycloak:26.7.0`, Digest `sha256:0f198be2`, Image erstellt am 2026-07-23, gelesen mit `docker image inspect`). Die Instanz nennt dieselbe Fassung selbst, an zwei Stellen: `kc.sh --version` im laufenden Container antwortet `Keycloak 26.7.0`, und die Startzeile des Protokolls lautet `Keycloak 26.7.0 on JVM (powered by Quarkus 3.33.2.1)`. Gefahren als `start-dev` auf der Datenbank im Arbeitsspeicher, ausschließlich für die Messung von S5
**Deploy-Daemon:** HaRP, gemessen als `harp_proxy_docker` mit Deploy-ID `docker-install` und `NC Url http://caddy`. Die Bildmarke `ghcr.io/nextcloud/nextcloud-appapi-harp:release` ist gleitend, deshalb steht hier die gelaufene Fassung als Digest und nicht als Tag: `sha256:3b335650`, Image erstellt am 2026-08-14, gelesen mit `docker image inspect`
**Scope:** gemessen wird zweierlei: erstens die Installierbarkeit dieser App in einer openDesk-Umgebung, ausschließlich aus öffentlich ladbaren Quellen an festen Tags, zweitens die beiden Zugriffswege auf die Nutzeridentität gegen OpenProject, lokal in Docker mit gepinnten Fassungen. Ausdrücklich nicht gemessen wird: kein Kubernetes-Cluster wird beschafft, keine openDesk-Installation wird versucht, und es entsteht kein Produktionscode. Die Werkzeugoberfläche und das Budget-Gate der ausgelieferten App stehen in dieser Phase still.

Die Fassungen im Kopfblock sind vor dem Schreiben aus der laufenden Instanz gelesen worden (`occ status` für den Server, `occ app:list` für `app_api`, `integration_openproject` und `user_oidc`) und nicht aus der Recherche übernommen. Solange die Pläne liefen, stand an einer noch offenen Zeile kein Wert aus der Recherche, sondern gar keiner, samt der Angabe des Plans, der sie füllt; jede dieser Zeilen trägt jetzt entweder ihren Messwert oder eine Ungemessen-Zeile mit Grund in Abschnitt 2.5. Die Messumgebung ist die lokale Docker-Topologie `compose.spike-opendesk.yml`, gepinnt auf die Fassungen aus 1.3 und ausschließlich auf 127.0.0.1 erreichbar (D-02, D-03); sie ist nach dem letzten Messlauf abgeräumt worden, die Befehlsfolge zum Nachbauen steht in `## Reproduktion`.

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

**Vollständig gemessen, zuletzt am 2026-08-29.** Dieser Abschnitt ist über drei Pläne entstanden: die
Installation der App und der Capability-Befund sowie S1, S2 und die Egress-Kontrolle stehen hier
(17-05), S3, S4 und S6 sind dazugekommen (17-06), S5a bis S5c mit Stufe C der Messumgebung (17-07).
Damit trägt jede Behauptung von S0 bis S6 einen Messwert; keine Zeile trägt einen Wert aus der
Recherche.

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

Der Store-Zugriff im Container hat getragen, der Rückfall über ein von Hand geladenes Paket der App war
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

#### Der Einrichtungsweg: gelaufen ist Weg B, und Weg A ist gemessen nicht gangbar

Die Recherche nennt zwei Einrichtungswege, Weg A über den Ablagen-Assistenten von OpenProject (der Weg
des openDesk-Bootstrap-Jobs, deshalb der mit der höheren Übertragbarkeit) und Weg B über
`occ config:app:set` plus den persönlichen Durchlauf je Konto. **Gelaufen ist Weg B.** Der Satz steht
hier so deutlich, weil er die Übertragbarkeit der ganzen Weg-0-Messung auf openDesk begrenzt: gemessen
ist, dass die App im Modus `oauth2` gegen eine lokale Instanz **arbeitet**, nicht, dass der
openDesk-Bootstrap-Job durchläuft.

**Weg A ist in dieser Topologie gemessen nicht gangbar**, und der Grund liegt nicht bei Nextcloud und
nicht bei der Erreichbarkeit, sondern beim SSRF-Schutz von OpenProject: `safe_ip?` weist alle vier
Namen ab, unter denen Nextcloud hier zu erreichen wäre, die Erlaubnisliste ist leer, und der Schlüssel
dafür ist in der Oberfläche nicht setzbar, während die zwei Netzaufrufe danach beide gelingen. Die
vollständige Messung samt Gegenprobe steht in 5.4. Weg A bleibt damit **ungemessen** und ist nicht
verworfen: er wäre mit einem Neuerzeugen des OpenProject-Containers samt
`OPENPROJECT_SSRF__PROTECTION__IP__ALLOWLIST` und einem für beide Seiten gleichlautenden Namen zu
messen, und diese Phase erzeugt diesen Eingriff bewusst nicht (D-03).

**Weg B verlangt fünf Werte, nicht vier.** Die Recherche nennt vier Schlüssel; gemessen sind fünf, und
der fünfte ist der Grund, warum ein reiner `occ`-Weg nicht genügt. `GET /op-oauth-url` antwortete mit
`HTTP 500` und im Protokoll stand wörtlich `OpenProject admin config is not valid!`, ausgelöst in
`lib/Controller/OpenProjectController.php:199`. Die Ursache steht in der Prüfkette der App:

```php
// lib/Service/OpenProjectAPIService.php:931-934 (isAdminConfigOkForOauth2)
$opClientId = $config->getAppValue(Application::APP_ID, 'openproject_client_id');
$opClientSecret = $config->getAppValue(Application::APP_ID, 'openproject_client_secret');
$ncClientId = $config->getAppValue(Application::APP_ID, 'nc_oauth_client_id');
return !(empty($opClientId) || empty($opClientSecret) || empty($ncClientId));
```

```php
// lib/Service/OpenProjectAPIService.php:902-911 (isCommonAdminConfigOk)
$freshProjectFolderSetUp = (bool)$config->getAppValue(Application::APP_ID, 'fresh_project_folder_setup');
if ($freshProjectFolderSetUp === true || empty($oauthInstanceUrl) || !self::validateURL($oauthInstanceUrl)) {
    return false;
}
```

Also braucht Weg 0 zusätzlich `nc_oauth_client_id`, das ist die OAuth-Anwendung auf der
**Nextcloud**-Seite, und `fresh_project_folder_setup` muss aus sein. Der Wert steht nach der
Installation auf `1`, gesetzt von der Migration `Version2400Date20230504144300`, gemessen als
`fresh_project_folder_setup = 1` direkt nach `app:install`. Beides ist **nicht** von Hand gesetzt
worden, sondern über die zwei Routen, die die App dafür selbst mitbringt:

| Schritt | Aufruf | Messwert |
|---------|--------|----------|
| Nextcloud-seitige OAuth-Anwendung | `POST /index.php/apps/integration_openproject/nc-oauth` als Admin, mit `requesttoken` | **200**, Antwort nennt `nextcloud_oauth_client_name = OpenProject client`, `nextcloud_client_id` (64 Zeichen), `nextcloud_client_secret` (64 Zeichen) und die Rückadresse, die Weg A auf der OpenProject-Seite eingetragen hätte: `http://op.localtest.me:8082/oauth_clients/<64 Zeichen>/callback`. Danach `nc_oauth_client_id = 1` |
| Setup-Schalter | `PUT /index.php/apps/integration_openproject/admin-config` mit `{"values":{"setup_project_folder":false,"setup_app_password":false}}` | **200**, Antwort wörtlich `{"status":true,"oPOAuthTokenRevokeStatus":"","oPUserAppPassword":null}`. Danach `fresh_project_folder_setup = 0` |

Die `"status": true` in der zweiten Zeile ist der Messwert, auf den es ankommt: das ist
`isAdminConfigOk()` aus der App selbst, nicht unsere Auslegung ihrer Bedingungen
(`lib/Controller/ConfigController.php:398`). Die Route wurde mit beiden Setup-Schaltern **aus**
aufgerufen, weil genau das die Bedingung von T-17-03 ist; gemessen bleiben `setup_app_password` und
`setup_project_folder` danach leer, und `oPUserAppPassword` ist `null`. Es liegt also kein
App-Passwort im Prozess, und S1 bleibt aussagekräftig.

**Der Admin-Konfigstand, gelesen statt behauptet.** `occ config:list integration_openproject` nennt
danach genau diese Schlüssel: `authorization_method = oauth2`,
`openproject_instance_url = http://op.localtest.me:8082`, `openproject_client_id` (43 Zeichen),
`openproject_client_secret` (43 Zeichen), `nc_oauth_client_id = 1`, `fresh_project_folder_setup = 0`,
`installed_version = 3.1.1`. Kein `sso_provider_type`, kein `oidc_provider`, kein `token_exchange`:
der OIDC-Zweig ist unberührt, was für S5 in 17-07 der Ausgangszustand ist.

#### Der persönliche Durchlauf lief ohne Browser, und zwei Hürden dabei sind eigene Messwerte

Der Plan sah für den persönlichen Zustimmungsdurchlauf einen Owner-Schritt in zwei Oberflächen vor.
Gemessen ist er per Formular gelaufen, für beide Konten, in neun Schritten und ohne Browser. Die
Schritte 5 bis 8 sind das Muster aus 2.2, hier nur mit der anderen OAuth-Anwendung:

| Schritt | Aufruf | Messwert |
|---------|--------|----------|
| 1, 2 | `GET /login`, dann `POST /login` in Nextcloud | 200, `requesttoken` 89 Zeichen; die Anmeldung endet mit `303` auf `/apps/dashboard/` |
| 3 | `GET /index.php/csrftoken` | 200, Token 89 Zeichen, an die Sitzung gebunden |
| 4 | `GET /index.php/apps/integration_openproject/op-oauth-url` mit `requesttoken` | **200**, `application/json`. Die Adresse trägt `client_id` (43 Zeichen), `redirect_uri` (siehe unten), `response_type=code`, `state` (10 Zeichen), `code_challenge` (43 Zeichen) und `code_challenge_method=S256` |
| 5, 6 | `GET /login`, `POST /login` in OpenProject als `opa` bzw. `opb` | 200, `authenticity_token` 86 Zeichen; die Kette endet auf der Startseite |
| 7 | `GET /oauth/authorize` mit der Adresse aus Schritt 4 | **200**, Zustimmungsseite 13442 Zeichen (`opa`) bzw. 13440 (`opb`), wörtlich `Authorize nc-mcp-spike-weg0 to use your account opa?` bzw. `opb` |
| 8 | `POST /oauth/authorize` | **302**, `Location` trägt `code` (43 Zeichen) und das `state` Zeichen für Zeichen zurück |
| 9 | `GET /oauth-redirect` mit der Nextcloud-Sitzung des Nutzers | **303** auf `/apps/files/` |

Die `redirect_uri` aus Schritt 4 ist gemessen
`http://127.0.0.1:8091/index.php/apps/integration_openproject/oauth-redirect` und stimmt Zeichen für
Zeichen mit dem Wert überein, den `IURLGenerator::getAbsoluteURL` in derselben Instanz liefert und den
`getOauthRedirectUrl()` (`lib/Service/OpenProjectAPIService.php:697-701`) baut. Deshalb trägt die
OAuth-Anwendung auf der OpenProject-Seite genau diese Zeichenkette.

**Erste Hürde, ein eigener Messwert: ohne `Origin`-Kopf keine Anmeldung.** `POST /login` antwortete
zunächst mit `303` auf `/login?direct=1&user=alice`, im Protokoll `Login failed: 'alice'`, und das
sieht wie ein falsches Passwort aus. Es war keines: dieselben Zugangsdaten antworten per Basic-Auth auf
`/ocs/v2.php/cloud/user` mit **200** (Gegenprobe: ein falsches Passwort dort **401**). Der Grund steht
in dieser Nextcloud-Fassung:

```php
// core/Controller/LoginController.php:307-314
$origin = $this->request->getHeader('Origin');
$throttle = true;
if ($origin === '' || !$trustedDomainHelper->isTrustedUrl($origin)) {
    $error = self::LOGIN_MSG_INVALID_ORIGIN;
    $throttle = false;
}
```

Ein leerer `Origin` bricht die Anmeldung ab, **bevor** das Passwort geprüft wird. Mit
`Origin: http://127.0.0.1:8091` antwortet derselbe Aufruf `303` auf `/apps/dashboard/`. Wer diese Zeile
nicht kennt, liest den Zustand als falsches Passwort und geht in den Browser-Rückfall, obwohl der
Formularweg trägt. Das ist dieselbe Klasse von Falle wie der 2FA-Umweg aus 2.2.

**Zweite Hürde, und die ist der interessantere Befund: auch Nextcloud verweigert Loopback.** Der
Rückweg in Schritt 9 antwortete `303`, die Verbindung war aber **nicht** hergestellt:
`oauth_connection_result` stand auf `error`, und `oauth_connection_error_message` lautete wörtlich

```
Error getting OAuth access token. Host "127.0.0.1" (op.localtest.me:80) violates local access rules
```

Das ist die Prüfung auf lokale Adressen von Nextcloud selbst, nicht die von OpenProject aus 5.4. Zwei
Beobachtungen dazu, beide gemessen: die Meldung nennt `127.0.0.1`, also die **öffentliche** Auflösung
von `op.localtest.me`, und nicht die `172.29.43.10` aus d…38470 tokens truncated…lossen,
sondern an ihm ausgeführt. `safe_ip?` gibt die Adresse zurück, wenn sie zulässig ist, und `nil`, wenn
nicht:

```
allowlist = []
safe_ip?("127.0.0.1")       = nil
safe_ip?("caddy")           = nil
safe_ip?("nextcloud")       = nil
safe_ip?("op.localtest.me") = nil
safe_ip?("localhost")       = nil
Resolv::DNS "caddy"         = ["172.29.43.10"]
```

**Alle fünf Namen sind unzulässig, und die Erlaubnisliste ist leer.** Der Grund steht in der
Beschreibung des Schlüssels `ssrf_protection_ip_allowlist` in
`/app/config/constants/settings/definition.rb:1221-1266`, die die vom Gem `ssrf_filter` gesperrten
Bereiche wörtlich aufzählt: `127.0.0.0/8` sperrt die Loopback-Adresse und `172.16.0.0/12` das Netz
`172.29.43.0/24` dieser Topologie. Die letzte Zeile der Messung zeigt, dass auch der Dienstname nicht
hilft: er löst nach `172.29.43.10` auf, und diese Adresse liegt in genau dem gesperrten Bereich.

**Gegenprobe, ohne die der Befund auf Erreichbarkeit geschoben werden könnte.** Die zwei Netzaufrufe,
die der Validator **nach** dem Namenscheck führen würde, sind einzeln gefahren, aus dem
OpenProject-Container gegen `http://caddy`, und **beide gelingen**:

| Validator-Aufruf | Erwartung des Validators | Messwert |
|------------------|--------------------------|----------|
| `GET /ocs/v2.php/cloud/capabilities` (Zeile 73), `Ocs-Apirequest: true` | 2xx, `ocs.data.version.major` mindestens 22 (Zeile 31) | **200**, `version.major = 33`, und der Abschnitt `integration_openproject` steht darin |
| `GET /index.php/apps/integration_openproject/check-config` (Zeile 101), `Authorization: Bearer TESTBEARERTOKEN` (Zeile 32) | 2xx, und der Kopf muss unverändert zurückkommen | **200**, Körper wörtlich `{"user_id":"","authorization_header":"Bearer TESTBEARERTOKEN"}` |

Damit ist gemessen, dass diese Instanz die zwei fachlichen Bedingungen erfüllt: sie ist ein Nextcloud
33, die App ist installiert, und die Weiterleitungsfalle aus dem Kommentar des Validators
(`op_application_not_installed` bei einer 3xx, weil Apache den `Authorization`-Kopf ohne
`mod_rewrite` verschluckt) greift hier **nicht**. Der einzige Grund, an dem der Assistent scheitert,
ist der Namenscheck davor.

**Was daran gemessen ist und was nicht.** Gemessen ist die Antwort von `safe_ip?` für fünf Namen, die
leere Erlaubnisliste, die vier Erreichbarkeitswerte und die zwei Validator-Antworten. **Nicht
beobachtet** ist die Fehlermeldung des Assistenten in der Oberfläche: dass aus `:ssrf_filtered` eine
Abweisung des Formulars wird, ist an den Zeilen 48 bis 53 der installierten Fassung gelesen und nicht
im Browser gesehen. Der Bericht behauptet deshalb nicht, wie die Meldung lautet, sondern nur, welchen
Wert die Prüfung liefert, die zu ihr führt.

**Der Schlüssel ist nicht in der Oberfläche setzbar.** `ssrf_protection_ip_allowlist` trägt in
derselben Datei `writable: false`, `default: ""` und `env_alias: "SSRF_PROTECTION_IP_ALLOWLIST"`. Ein
Administrator kann ihn also nicht in OpenProject eintragen; er kommt aus der Umgebung des Prozesses,
und das heißt in dieser Topologie: der Container muss mit einer zusätzlichen Umgebungsvariablen neu
erzeugt werden.

**Was das über openDesk sagt, und was nicht.** Über openDesk sagt es nichts Gemessenes. Die
naheliegende Erklärung, warum der Bootstrap-Job dort denselben Weg gehen kann, ist, dass Nextcloud in
einem Cluster unter einem öffentlichen Namen mit einer routbaren Adresse steht und der Schutz dort
nicht greift; ob openDesk zusätzlich eine Erlaubnisliste setzt, ist in dieser Phase **ungemessen** und
steht nicht im Deployment-Projekt, das für Abschnitt 1 gelesen wurde. Dieser Absatz ist eine
Einordnung und kein Befund, und er ist als solcher gekennzeichnet, weil ein Satz ohne diese
Kennzeichnung wie eine Aussage über eine Behördeninstallation liest (Pitfall 3).

**Folge für die Einrichtung.** Weg A ist damit nicht ohne einen Eingriff in die Messumgebung gangbar,
und Weg B, der Handweg über `occ config:app:set` plus den persönlichen Durchlauf je Konto, ist der Weg
ohne Eingriff. Welcher der beiden genommen wurde, steht in 2.1; die Entscheidung liegt beim Owner, weil
sie die Übertragbarkeit der Weg-0-Messung auf openDesk verändert und nicht nur den Aufwand.

### 5.5 Rohwerte von S3, S4 und S6 auf Weg 0

#### 5.5.1 Die Suchmessung (S3)

Gemessen am 2026-08-28, alle Aufrufe durch Caddy gegen `http://127.0.0.1:8091`, alle unter reiner
AppAPI-Impersonation und ohne App-Passwort im Prozess. Der Pfad ist in jeder Zeile
`/ocs/v2.php/apps/integration_openproject/api/v1/work-packages`, die Werte in der Spalte Aufruf sind
die Abfrageparameter. Gekürzt wird nach der Geheimnisregel oben: der Wert des Kopfes
`AUTHORIZATION-APP-API` steht in keiner Zeile.

| # | Konto | Aufruf | Status | Content-Type | Bytes | `ocs.data` |
|---|-------|--------|--------|--------------|-------|------------|
| 1 | `alice` | `?searchQuery=SPIKE-OD-8471` | 200 | `application/json; charset=utf-8` | 74 | `[]`, 0 Treffer |
| 2 | `bob` | `?searchQuery=SPIKE-OD-8471` | 200 | `application/json; charset=utf-8` | 74 | `[]`, 0 Treffer |
| 3 | `alice` | `?searchQuery=SPIKE-OD-8471&isSmartPicker=true` | 200 | `application/json; charset=utf-8` | 74 | `[]`, 0 Treffer |
| 4 | `bob` | `?searchQuery=SPIKE-OD-8471&isSmartPicker=true` | 200 | `application/json; charset=utf-8` | **4746** | ein Objekt: `id 38`, `displayId "38"`, `subject "SPIKE-OD-8471 privat"`, `_type WorkPackage` |
| 5 | `alice` | `?searchQuery=Demo&isSmartPicker=true` | 200 | `application/json; charset=utf-8` | 35239 | 14 Objekte, `id 38` **nicht** darunter |
| 6 | `bob` | `?searchQuery=Demo&isSmartPicker=true` | 200 | `application/json; charset=utf-8` | 36308 | 14 Objekte, `id 38` **nicht** darunter |
| 7 | `bob`, `APP_SECRET` aus 64 Nullen | `?searchQuery=SPIKE-OD-8471&isSmartPicker=true` | 401 | `application/json; charset=utf-8` | 106 | `statuscode 997`, `Current user is not logged in` |
| 8 | `carol` | `?searchQuery=SPIKE-OD-8471&isSmartPicker=true` | 401 | `application/json; charset=utf-8` | 77 | `statuscode 401`, Meldung leer |

Die Zeilen 1 und 2 sind der Lauf nach dem Wortlaut des Auftrags, die Zeilen 3 und 4 derselbe Lauf mit
`isSmartPicker=true`. Der Unterschied zwischen Zeile 2 und Zeile 4 ist der Grund, warum der Parameter
in 2.1 einen eigenen Absatz hat: dasselbe Konto, dasselbe Suchwort, einmal 0 und einmal 1 Treffer.

Die zugehörige Zustandsmessung an der Ursache, **nicht** unter einem der Messkonten, sondern mit dem
Aufbauzugang `Basic apikey:<OP_API_TOKEN>` des Kontos `admin`:

```
GET http://op.localtest.me:8082/api/v3/storages
-> HTTP 200, 131 Bytes, total 0, count 0, _embedded.elements leer
```

Keine registrierte Ablage, also greift der Filter `linkable_to_storage_url` für kein Arbeitspaket. Die
Zeile steht ausdrücklich in Abschnitt 5 und nicht in der Messwerttabelle von S3: sie erklärt die
Vorgabe der Fläche und ist selbst kein Messwert über Berechtigungen, weil ein Administrator in
OpenProject alles sieht.

#### 5.5.2 Der künstliche Ablauf und die Erneuerung (S4)

Gemessen am 2026-08-28, ausschließlich am Konto `bob`. Die Zustandswerte kommen aus
`occ user:setting bob integration_openproject <schlüssel>`, ausgeführt als `www-data` im
Nextcloud-Container. Tokenwerte stehen nach der Geheimnisregel nur mit Länge und
Vier-Zeichen-Präfix.

| # | Zeitpunkt (Unix) | Schritt | Rohwert |
|---|------------------|---------|---------|
| 1 | 1787943289 | `token_expires_at` gelesen | `1787949020` |
| 2 | 1787943289 | `token` gelesen | Länge 43, Präfix `dbHz` |
| 3 | 1787943289 | `refresh_token` gelesen | Länge 43, Präfix `bHRR` |
| 4 | 1787943305 | `token_expires_at 0` gesetzt, zurückgelesen | `0` |
| 5 | 1787943305 | OCS-Aufruf als `bob`, `?searchQuery=SPIKE-OD-8471&isSmartPicker=true` | **200**, `application/json; charset=utf-8`, 4746 Bytes, ein Treffer `id 38` |
| 6 | 1787943305 | `token_expires_at` gelesen | `1787950505` (Differenz zu Zeile 5: **7200**) |
| 7 | 1787943305 | `token` gelesen | Länge 43, Präfix `7Gvk` (verschieden von Zeile 2) |
| 8 | 1787943305 | `refresh_token` gelesen | Länge 43, Präfix `eXhd` (verschieden von Zeile 3) |
| 9 | 1787943322 | `refresh_token` auf 43 Nullen gesetzt, `token_expires_at 0`, zurückgelesen | `0` |
| 10 | 1787943322 | derselbe OCS-Aufruf als `bob` | **401**, `application/json; charset=utf-8`, 77 Bytes, `statuscode 401`, Meldung leer |
| 11 | 1787943323 | `token_expires_at`, `token`, `refresh_token` gelesen | `0`, Präfix `7Gvk` unverändert, Präfix `0000` |
| 12 | nach Zeile 11 | `occ user:setting alice integration_openproject token_expires_at` | `1787949009`, unverändert gegenüber 17-05 |

Die Protokollzeilen im Zeitfenster der beiden Läufe, mit `grep` über
`/var/www/html/data/nextcloud.log` gezählt: **0** Zeilen zu `18:55:0x` (Hauptlauf, Zeile 5) und **2**
Zeilen zu `18:55:23` (Gegenprobe, Zeile 10). Die zweite davon steht wörtlich in 2.1; ihr Fehlerfeld
ist `invalid_grant`, dasselbe, das 2.2 auf Weg 1 für einen erfundenen `refresh_token` gemessen hat.
Die Zeile ist vor der Übernahme in diesen Bericht gegen jeden Wert der Verbindungsdatei geprüft
worden und trägt keinen davon.

#### 5.5.3 Die Byte-Messung und die Bezugsgröße (S6)

Gemessen am 2026-08-28. Die erste Zeile ist dieselbe Antwort wie Zeile 4 von 5.5.1, es ist kein
zweiter Aufruf dafür gefahren worden. Die Zählung selbst lief über die gespeicherte Antwortdatei
außerhalb des Repositoriums.

| Gegenstand | Rohwert |
|------------|---------|
| OCS-Antwort als `bob`, ein Treffer `id 38` | 4746 Bytes, 0 Zeilenumbrüche, 0 Tabulatoren, 0 doppelte Leerzeichen, 182 Vorkommen von `\/`, 0 Vorkommen von `\u` |
| dieselbe Antwort ohne Schrägstrich-Maskierung neu kodiert | 4564 Bytes |
| das Arbeitspaket-Objekt allein | 4490 Bytes, 25 Schlüssel oberster Ebene, kein `_embedded` |
| `_links` darin | 3895 Bytes, 49 Relationen |
| die 24 Felder darin | 585 Bytes |
| OCS-Antwort als `alice`, Suchwort `Upload presentations`, ein Treffer `id 12` | 2542 Bytes, 27 Relationen (1772 Bytes), 22 Felder (588 Bytes) |

Die Bezugsgrößen derselben Instanz, alle mit dem Aufbauzugang `Basic apikey:<OP_API_TOKEN>` des Kontos
`admin` und ausdrücklich ohne Beweiskraft über Berechtigungen:

```
GET /api/v3/work_packages/38                                            -> 200,  8115 Bytes
GET /api/v3/work_packages/38?select=id,subject                          -> 200,  8115 Bytes
GET /api/v3/work_packages?filters=[{"id":{"operator":"=","values":["38"]}}]
                                                                        -> 200, 15831 Bytes
   ... &select=total,elements/id,elements/subject                       -> 200,    88 Bytes
   ... &select=total,elements/id,elements/subject,elements/project,
              elements/status,elements/type,elements/self                -> 200,   361 Bytes
   ... &select=...,elements/updatedAt                                   -> 400,   310 Bytes,
       urn:openproject-org:api:v3:errors:InvalidSignal
```

Der Filterwert ist hier lesbar geschrieben, gefahren wurde er prozentkodiert. Die 88 und die 361 Bytes
sind die einzigen Antworten dieses Plans **mit** Leerraum: der `select`-Zweig serialisiert mit einem
Leerzeichen nach dem Doppelpunkt, der reguläre Zweig ohne. Für den Vergleich mit den 4746 Bytes ist das
ohne Bedeutung und steht hier nur der Vollständigkeit halber.

#### 5.5.4 Der natürlich verstrichene Ablauf an `alice` (Nachtrag zu S4)

Gemessen am 2026-08-29 beim Nachprüfen der Zahlen aus 5.5.3. Der Lauf war nicht als Messung geplant
und ist deshalb der sauberste, den dieser Plan hat: an `alice` ist zu keinem Zeitpunkt ein
`occ user:setting` gefahren worden, weder schreibend noch zur Vorbereitung. Der Ablauf ist von selbst
verstrichen, zwischen der Einrichtung in Plan 17-05 und diesem Aufruf.

| # | Zeitpunkt (Unix) | Schritt | Rohwert |
|---|------------------|---------|---------|
| 1 | 1787968632 | Systemzeit zum Zeitpunkt des Aufrufs | `1787968632` |
| 2 | vor 1 | `token_expires_at` von `alice`, gesetzt in 17-05, seither unangetastet | `1787949009`, Differenz zu Zeile 1: **-19623** |
| 3 | 1787968632 | OCS-Aufruf als `alice`, `?searchQuery=Upload%20presentations&isSmartPicker=true`, ohne Cookie, ohne App-Passwort | **200**, `application/json; charset=utf-8`, **2542 Bytes**, ein Treffer `id 12`, `subject "Upload presentations to website"` |
| 4 | nach 3 | `occ user:setting alice integration_openproject token_expires_at` | **`1787975808`**, Differenz zu Zeile 1: **+7176** |

Die Zahl aus Zeile 2 ist dieselbe, die Zeile 12 von 5.5.2 als unverändert protokolliert hat. Zeile 12
bleibt für ihren Zeitpunkt richtig; wer den Wert heute liest, findet den aus Zeile 4. Die Antwort aus
Zeile 3 ist dieselbe, deren Byte- und Feldzahlen 5.5.3 unter `alice` führt: es ist **ein** Aufruf, der
zwei Fragen beantwortet, und kein zweiter dafür gefahren worden.

### 5.6 Stufe C: Keycloak, `user_oidc` und die Rohwerte von S5

Gemessen am 2026-08-29. Alle Aufrufe gingen durch Caddy an `http://127.0.0.1:8091` oder an
`http://kc.localtest.me:8083` (löst öffentlich auf `127.0.0.1` auf, im Nextcloud-Container über
`extra_hosts` auf `172.29.43.10`). Es gilt die Geheimnisregel vom Kopf dieses Abschnitts: kein Token,
kein Client-Secret, kein Cookie und kein Wert des Kopfes `AUTHORIZATION-APP-API` steht in einer Zeile.

#### 5.6.1 Aufbau, nicht Messung

Wie in 5.3 gilt auch hier: der folgende Aufbau ist **kein** Messwert. Er steht hier, damit ein
Wiederholungslauf ihn ohne Raten nachfährt.

| Schritt | Kommando oder Wert | Ergebnis |
|---|---|---|
| Keycloak gestartet | `docker compose -f compose.spike-opendesk.yml --profile op --profile oidc up -d` | `Keycloak 26.7.0 on JVM (powered by Quarkus 3.33.2.1) started in 15.852s` |
| Realm und Clients | `kcadm.sh` im Container, nicht `--import-realm` | Realm `spike` aktiv; Clients `nextcloud` (vertraulich, Rückadresse `http://127.0.0.1:8091/*`) und `openproject` (nur Zielgruppe) |
| Konten in der Realm | `kcadm.sh create users` plus `set-password` | `alice` und `bob`, beide aktiv, Passwörter in `.env.spike-opendesk` |
| Client-Secret | `kcadm.sh get clients/<id>/client-secret` | **86 Zeichen**; nach `.env.spike-opendesk` als `KC_CLIENT_SECRET` geschrieben und mit dem laufenden Wert verglichen |
| `user_oidc` installiert | `occ app:install user_oidc` | `user_oidc 8.11.0 installed`, `user_oidc enabled` |
| Anbieter eingerichtet | `occ user_oidc:provider spike --clientid=nextcloud --clientsecret=... --discoveryuri=http://kc.localtest.me:8083/realms/spike/.well-known/openid-configuration --scope="openid email profile"` | `occ user_oidc:providers`: `identifier spike`, `clientId nextcloud`, Scope `openid email profile`, `clientSecret` vom Werkzeug selbst als `********` ausgegeben |
| Sitzungstoken speichern | `occ config:app:set user_oidc store_login_token --value=1` | `1` |
| Loglevel **vor** dem ersten Lauf | `occ log:manage --level 0` | `Log level: Debug (0)` |
| Modus geschaltet | `occ config:app:set integration_openproject authorization_method --value=oidc`, dazu `sso_provider_type external`, `oidc_provider spike`, `targeted_audience_client_id openproject`, `token_exchange 0` | alle fünf zurückgelesen |

**Zwei Erreichbarkeitswerte, die den Namen und nicht nur die Adresse prüfen** (dieselbe Regel wie in
5.2):

```
GET http://kc.localtest.me:8083/realms/spike/.well-known/openid-configuration
  vom Host:                        HTTP 200
  aus dem Nextcloud-Container:     HTTP 200
issuer im Dokument:                http://kc.localtest.me:8083/realms/spike
```

Der `issuer` trägt denselben Namen und denselben Port wie beide Aufrufe. Genau das ist der Punkt der
Portabbildung 8083 innen wie außen.

#### 5.6.2 Zwei Aufbaufehler, die keine S5-Befunde sind

Beide sind hier protokolliert, weil sie beim Nachfahren je einen Anlauf kosten und beide wie ein
Fehler des Produkts aussehen, ohne einer zu sein.

| Fehlschlag | Wörtliche Meldung | Ursache und Auflösung |
|---|---|---|
| Keycloak startete nicht, Neustartschleife | `ERROR: Failed to start server in (development) mode` / `Provided hostname is neither a plain hostname nor a valid URL` | `KC_HOSTNAME` war als `kc.localtest.me:8083` gesetzt. 26.7.0 nimmt entweder einen Namen ohne Port oder eine vollständige URL. Aufgelöst mit `http://kc.localtest.me:8083` |
| `GET /apps/user_oidc/login/1` antwortete **404** mit einer Fehlerseite | `You must access Nextcloud with HTTPS to use OpenID Connect.` | `LoginController::isSecure()` (`LoginController.php:121-126`) verlangt https, den Debug-Modus **oder** den App-Konfigwert `allow_insecure_http`. Aufgelöst mit `occ config:app:set user_oidc allow_insecure_http --value=1 --lazy`; danach antwortet derselbe Aufruf **303** auf den Autorisierungsendpunkt der Realm |

Die zweite Zeile ist zugleich ein Befund über die Messumgebung und keiner über openDesk: dort trägt
Nextcloud https, und die Bedingung fällt gar nicht an.

#### 5.6.3 Die Nutzer-Id, unter der `user_oidc` das Konto führt

Nach einer Anmeldung des Keycloak-Kontos `alice` durch den Autorisierungscode-Fluss (Start
`GET /apps/user_oidc/login/1`, Anmeldeformular der Realm, Rückweg auf
`http://127.0.0.1:8091/apps/user_oidc/code`) endete der Rückweg mit **303** auf
`/apps/dashboard/`, und `GET /ocs/v2.php/cloud/user` mit demselben Cookie antwortete **200** mit
`"backend":"user_oidc"`.

```
occ user:list
  - admin: admin
  - alice: alice
  - 3855a8f7d81aae5de814f2a6d77bd149591983992337ec676fb84ebda333cfe3: Alice Spike
  - bob: bob
  - carol: carol
```

**Die Id weicht ab, und das ist der Grund, warum jede S5-Zeile ihren Nutzernamen nennt.** Das
Keycloak-Konto `alice` und das Nextcloud-Konto `alice` sind zwei verschiedene Konten; `user_oidc`
führt das erste unter dem Streuwert `3855a8f7d81aae5de814f2a6d77bd149591983992337ec676fb84ebda333cfe3`
mit dem Anzeigenamen `Alice Spike`.

#### 5.6.4 Die sechs Läufe von S5, Rohwerte

Jeder Lauf: `occ user:setting <konto> integration_openproject token_expires_at 0`, danach
`GET /ocs/v2.php/apps/integration_openproject/api/v1/work-packages?searchQuery=SPIKE-OD-8471&isSmartPicker=true`
unter reiner AppAPI-Impersonation, danach die Zustandswerte erneut gelesen und das Protokoll ab der
Zeilenzahl vor dem Aufruf frisch gelesen.

| # | Unix-Zeit | `sso_provider_type` / `token_exchange` / `store_login_token` | Konto | Antwort | `token` danach | `token_expires_at` danach |
|---|---|---|---|---|---|---|
| 1 | 1787970751 | `external` / `0` / `1` | `3855a8f7...` | **401**, `application/json; charset=utf-8`, **77 Bytes** | nicht vorhanden | `0` |
| 2 | 1787970764 | `external` / `0` / `0` | `3855a8f7...` | **401**, **77 Bytes** | nicht vorhanden | `0` |
| 3 | 1787970773 | `external` / `1` / `0` | `3855a8f7...` | **401**, **77 Bytes** | nicht vorhanden | `0` |
| 4 | 1787970781 | `external` / `1` / `1` | `3855a8f7...` | **401**, **77 Bytes** | nicht vorhanden | `0` |
| 5 | 1787970800 | `nextcloud_hub` / `0` / `1` | `3855a8f7...` | **401**, **77 Bytes** | nicht vorhanden | `0` |
| 6 | 1787970817 | `external` / `0` / `1` | `alice` | **401**, **77 Bytes** | Länge 43, Präfix `Jm2D`, unverändert | `0` |

Der Körper ist in allen sechs Zeilen identisch:
`{"ocs":{"meta":{"status":"failure","statuscode":401,"message":""},"data":""}}`.

**Die Protokollzeilen dieser sechs Läufe, wörtlich und mit Stufe, Zeit und Konto.** Übernommen sind
ausschließlich die Meldungen der Apps `user_oidc` und `integration_openproject`; die Kontextfelder mit
Kopfzeilen sind nicht übernommen (T-17-01), und jede Zeile ist vor der Übernahme gegen jeden Wert aus
`.env.spike-opendesk` geprüft worden.

```
# Lauf 1, external / token_exchange 0 / store_login_token 1, Konto 3855a8f7...
level 0, 2026-08-29T02:32:32+00:00, user_oidc  "[ExternalTokenRequestedListener] received request"
level 0, 2026-08-29T02:32:32+00:00, user_oidc  "[TokenService] Get token from the session"
level 0, 2026-08-29T02:32:32+00:00, user_oidc  "[TokenService] getToken: no session data"
level 3, 2026-08-29T02:32:32+00:00, integration_openproject
                                               "Token event has not been caught by 'user_oidc'"

# Lauf 2, external / 0 / 0
level 0, 2026-08-29T02:32:44+00:00, user_oidc  "[ExternalTokenRequestedListener] received request"
level 3, 2026-08-29T02:32:44+00:00, integration_openproject
   "Failed to get token: Failed to get external token, login token is not stored"

# Lauf 3, external / 1 / 0
level 0, 2026-08-29T02:32:53+00:00, user_oidc
   "[ExchangedTokenRequestedListener] received request for audience: openproject"
level 3, 2026-08-29T02:32:53+00:00, integration_openproject
   "Failed to get token: Failed to exchange token, storing the login token is disabled.
    It can be enabled in config.php"

# Lauf 4, external / 1 / 1
level 0, 2026-08-29T02:33:01+00:00, user_oidc
   "[ExchangedTokenRequestedListener] received request for audience: openproject"
level 0, 2026-08-29T02:33:01+00:00, user_oidc  "[TokenService] Starting token exchange"
level 0, 2026-08-29T02:33:01+00:00, user_oidc  "[TokenService] Get token from the session"
level 0, 2026-08-29T02:33:01+00:00, user_oidc  "[TokenService] getToken: no session data"
level 0, 2026-08-29T02:33:01+00:00, user_oidc
   "[TokenService] Failed to exchange token, no login token found in the session"
level 3, 2026-08-29T02:33:01+00:00, integration_openproject
   "Failed to get token: Failed to exchange token, no login token found in the session"

# Lauf 5, nextcloud_hub / 0 / 1
level 0, 2026-08-29T02:33:20+00:00, user_oidc
   "[InternalTokenRequestedListener] received request for audience: openproject"
level 2, 2026-08-29T02:33:20+00:00, user_oidc
   "[TokenService] Failed to get token from Oidc provider app, oidc app is not installed"
level 3, 2026-08-29T02:33:20+00:00, integration_openproject
                                               "Token event has not been caught by 'user_oidc'"

# Lauf 6, external / 0 / 1, Konto alice
level 0, 2026-08-29T02:33:37+00:00, integration_openproject  "Token has expired."
level 0, 2026-08-29T02:33:37+00:00, integration_openproject  "Refreshing access token."
level 0, 2026-08-29T02:33:37+00:00, user_oidc  "[ExternalTokenRequestedListener] received request"
level 0, 2026-08-29T02:33:37+00:00, user_oidc  "[TokenService] Get token from the session"
level 0, 2026-08-29T02:33:37+00:00, user_oidc  "[TokenService] getToken: no session data"
level 3, 2026-08-29T02:33:37+00:00, integration_openproject
                                               "Token event has not been caught by 'user_oidc'"
```

#### 5.6.5 Die Gegenprobe mit echter Sitzung und der Lauf gegen den gültigen Zwischenspeicher

```
# 1787970835, derselbe Aufruf, aber mit dem Sitzungscookie aus der Keycloak-Anmeldung,
# Konto 3855a8f7..., Konfiguration external / 0 / 1
HTTP 401, application/json; charset=utf-8, 341 Bytes
ocs.meta.statuscode 401, Meldung leer
ocs.data.error trägt "errorIdentifier":"urn:openproject-org:api:v3:errors:Unauthenticated"

level 0, user_oidc  "[TokenService] Get token from the session"
level 0, user_oidc  "[TokenService] getToken: token is expiring, proactively refreshing to keep
                     IdP session alive, expires in 80"
level 0, user_oidc  "[TokenService] Refreshing the token:
                     http://kc.localtest.me:8083/realms/spike/protocol/openid-connect/token"
level 0, user_oidc  "[TokenService] ---- Refresh token success"
level 0, user_oidc  "[TokenService] Store token in the session"
level 0, user_oidc  "[TokenService] checkLoginToken: all good"
level 0, user_oidc  "[ExternalTokenRequestedListener] received request"
level 0, user_oidc  "[TokenService] getToken: token is still valid, it expires in 300 and
                     refresh expires in 1800"
level 0, integration_openproject  "New token expires at 2026/08/29 02:38:56"
level 3, integration_openproject  "OpenProject error : Client error:
                     `GET http://op.localtest.me:8082/api/v3/users/me` resulted in a
                     `401 Unauthorized` response"
```

Zustand am Konto `3855a8f7...` unmittelbar danach: `token` mit **Länge 1387** in der Form eines JWT
(drei durch Punkte getrennte Base64url-Abschnitte, der Wert selbst steht hier nicht),
`token_expires_at` `1787971136`; `user_id` und `user_name` existieren **nicht**, weil `initUserInfo()`
an der Abweisung durch OpenProject scheitert.

```
# 1787970877, wieder ohne Cookie, reine Impersonation, Konto 3855a8f7...,
# token_expires_at 1787971136 und damit 259 s in der Zukunft
HTTP 401, application/json; charset=utf-8, 341 Bytes
ocs.data.error trägt "errorIdentifier":"urn:openproject-org:api:v3:errors:Unauthenticated"

Zeilen der App user_oidc in diesem Zeitfenster: KEINE
level 3, integration_openproject  "OpenProject error : Client error:
                     `GET http://op.localtest.me:8082/api/v3/users/me` resulted in a
                     `401 Unauthorized` response"
```

**Der Unterschied zwischen diesem Lauf und den sechs aus 5.6.4 ist eine einzige Zahl**, der Ablauf des
zwischengespeicherten Tokens, und er entscheidet, ob `user_oidc` überhaupt gefragt wird
(`getAccessToken()`, Zeile 1748). Die 341 gegen 77 Bytes sind der maschinell prüfbare Ausdruck
desselben Unterschieds.

## Reproduktion

Die Messumgebung ist nach dem letzten Lauf abgeräumt worden. Was hier steht, ist die Befehlsfolge, mit
der sie wieder entsteht, samt der Schritte, die nur über eine Oberfläche gehen, und samt dem einen
Befehl, mit dem sie wieder verschwindet.

**Stufe A, Nextcloud 33.0.7 samt ExApp:**

```
export HP_SHARED_KEY="$(openssl rand -hex 32)"
export SECRET_KEY_BASE="$(openssl rand -hex 32)"
docker compose -f compose.spike-opendesk.yml up -d --wait
bash scripts/bootstrap_spike_opendesk.sh
set -a && . ./.env.spike-opendesk && set +a
```

Beide `export` sind auch dann Pflicht, wenn nur Stufe A laufen soll: Compose interpoliert die ganze
Datei, bevor es nach Profilen filtert, gemessen am 2026-08-28 gegen Docker 29.5.2 (Kopf von
`compose.spike-opendesk.yml`). Der Bootstrap schreibt die Verbindungsdatei `.env.spike-opendesk`; sie
ist **git-ignoriert** (`.gitignore` Zeile 17), weil sie zwei funktionierende App-Passwörter, den
HaRP-Schlüssel und das `APP_SECRET` der Registrierung trägt. `.env.spike-opendesk.example` führt
ausschließlich die Variablennamen und keinen einzigen Wert; jede Geheimniszeile darin ist auskommentiert.

**Stufe B, OpenProject 17.7.2, und Stufe C, Keycloak 26.7.0:**

```
docker compose -f compose.spike-opendesk.yml --profile op up -d --wait
docker compose -f compose.spike-opendesk.yml --profile op --profile oidc up -d
```

**Die Schritte, die nur über eine Oberfläche gehen.** Zwei Stellen dieses Berichts hat der Owner im
Browser gemacht, und sie stehen deshalb nicht in der Befehlsfolge oben:

* die OAuth-Anwendungen in OpenProject, `nc-mcp-spike-weg0` und `nc-mcp-spike-weg1`, unter
  Administration, Authentication, OAuth applications. Zu 17.7.2 ließ sich kein dokumentierter Weg zum
  Seeden einer OAuth-Anwendung finden, und `registration_endpoint` fehlt in den Metadaten (2.2). Die
  Anweisungen dazu stehen in den Plänen 17-03 (Weg 1) und 17-05 (Weg 0), samt dem Hinweis, dass
  "Confidential" und "Client Credentials User ID" leer bleiben (5.3).
* der persönliche Durchlauf je Konto für Weg 0. Er ist in 17-05 ohne Browser nachgefahren worden
  (Schritte 1 bis 9 in 2.1), die Anweisung an den Owner nennt trotzdem den Browserweg, weil der
  Formularweg an zwei Stellen kippen kann.

**Wie der Zustand wieder verschwindet:**

```
docker compose -f compose.spike-opendesk.yml --profile op --profile oidc down -v
```

Das `-v` ist keine Bequemlichkeit, sondern für Keycloak Pflicht: die Realm `spike` wird mit `kcadm.sh`
erzeugt und nicht mit `--import-realm`, und ein Import überspringt eine vorhandene Realm, statt sie zu
aktualisieren. Ein zweiter Lauf auf einem behaltenen Band misst also die Konfiguration des ersten. Mit
demselben Befehl verschwinden auch die zwei Eingriffe an der Nextcloud-Instanz, der auf `Debug (0)`
gesenkte Loglevel und `allow_insecure_http`, weil beide im Nextcloud-Band liegen.

Ein Ding bleibt nach `down -v` liegen und ist keins dieser Topologie: der Deploy-Daemon benennt den
ExApp-Container global `nc_app_<appid>`, nicht projektgebunden. Wer danach die Topologie aus
`compose.exapp.yml` wieder braucht, holt sich den Namen mit ihrem eigenen Bootstrap zurück:

```
export HP_SHARED_KEY="$(sed -n 's/^HP_SHARED_KEY=//p' .env.exapp)"
docker compose -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh
```

## Was diese Messung nicht beweist

Die Ränder stehen hier vollständig und nicht als Auswahl. Wer einen Messwert dieses Berichts über einen
dieser Ränder hinaus benutzt, benutzt ihn falsch, und zwar nachlesbar falsch.

**Sie lief gegen eine Wegwerf-Instanz und gegen genau die Fassungen aus dem Kopfblock.** Nextcloud
33.0.7 auf **SQLite** (`SQLITE_DATABASE: nextcloud` in `compose.spike-opendesk.yml`), leere Bände, ohne
Last, ohne zweiten Knoten, `integration_openproject` 3.1.1, `user_oidc` 8.11.0, OpenProject 17.7.2,
Keycloak 26.7.0. Eine andere Fassung darf sich anders verhalten: alle Zeilennummern und alle
Quellenzitate dieses Berichts gelten für diese Fassungen und für keine andere, und die OCS-Fläche ist
aus `appinfo/routes.php` **dieser** Fassung gezählt.

**Der lokale Aufbau reproduziert openDesk nicht, und zwar in fünf benannten Punkten.**

1. **Keycloak als Anmeldezwang ohne lokales Formular.** In openDesk setzt
   `OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"` das lokale Anmeldeformular außer Kraft.
   Genau dieses Formular ist Schritt 2 des gemessenen Weg-1-Messwegs (2.2). Der Zustimmungsfluss hat
   dort einen zusätzlichen Umleitungsschritt, und der ist hier ungemessen (2.5).
2. **Die Scope-Pflicht für ein OIDC-JWT.** Seit OpenProject 16.0.0 verlangt ein OIDC-Token den
   `scope`-Anspruch mit `api_v3`. Im lokalen OAuth-Modus, in dem alle Weg-1-Messwerte entstanden sind,
   ist diese Pflicht unsichtbar, weil OpenProject die Tokens selbst ausgibt (2.5).
3. **Die Datenlage.** Die Seed-Instanz hat ein Projekt und wenige Arbeitspakete; die Asymmetrie, auf
   der beide Negativbeweise stehen, ist in 5.3 von Hand angelegt worden. Eine Behördeninstanz hat
   andere Projekte, andere Rollen, andere Sichtbarkeiten, und die 14 Treffer auf das Suchwort `Demo`
   sind eine Eigenschaft der Seed-Daten und keine Aussage über eine echte Instanz.
4. **Kubernetes samt Helm und abgeschaltetem App Store.** openDesk läuft über ein Helmfile in einem
   Cluster und hat den App Store aus (1.1); diese Messung lief in vier bis sieben Docker-Containern auf
   127.0.0.1, und die vier optionalen Apps sind hier aus genau dem App Store installiert worden, den es
   dort nicht gibt (S0). Kein Kubernetes-Cluster ist beschafft und keine openDesk-Installation versucht
   worden (D-01, D-03).
5. **Die tatsächliche Betriebsart von `integration_openproject`.** Eingerichtet wurde hier Weg B über
   `occ config:app:set` plus persönlichen Durchlauf je Konto; der openDesk-Bootstrap-Job geht Weg A,
   und Weg A ist in dieser Topologie gemessen nicht gangbar und deshalb ungemessen (2.5, 5.4). Ob dort
   `oauth2` oder `oidc` läuft, ist Frage 7.

**Die Egress-Kontrollmessung beweist über eine Behördeninstallation nichts.** Sie lief im lokalen
Docker-Netz, in dem alle Container in einem Netz hängen und nichts sie trennt; eine Antwort ist dort
erwartbar. In einer Behördeninstallation entscheiden Netzrichtlinien, Egress-Filter und Proxy-Zwang, ob
eine ExApp einen zweiten Host erreicht, und keine dieser Bedingungen ist hier nachgebildet.

**Die Zahlen aus `community.openproject.org` sind Kontext und kein Messwert dieser Instanz.** Die 3691
und 216 Bytes aus 3.2 stammen aus der Recherche gegen eine fremde Instanz mit anderem Modulsatz; sie
stehen dort als Größenordnung neben den gemessenen 15831 und 88 Bytes und nirgends als Beleg.

**Drei Eingriffe halten diesen Aufbau am Laufen, und sie stehen hier, weil ein Nachbau sie sonst für
Vorgabe hält.**

* **`allow_local_remote_servers = true` in Nextcloud** (Abschnitt 2.1, "Der persönliche Durchlauf lief
  ohne Browser"): ohne diese Systemeinstellung antwortet der Rückweg von Weg 0 zwar `303`, die Verbindung steht
  aber nicht, wörtlich `Host "127.0.0.1" (op.localtest.me:80) violates local access rules`. Sie ist
  eine Lockerung **der Messumgebung** und betrifft die ausgelieferte ExApp an keiner Stelle; für eine
  openDesk-Installation ist sie ohne Bedeutung, weil dort beide Seiten routbare Adressen haben.
* **Das Passwort des OpenProject-Kontos `admin` ist per `rails runner` gesetzt worden** (5.3), weil die
  dokumentierte Vorgabe `admin`/`admin` von dieser Instanz abgewiesen wurde. **Warum das Seed-Passwort
  abwich, ist nicht untersucht**, steht als offener Punkt in 2.5 und nicht als Vermutung. Der erzwungene
  Passwortwechsel hat damit nicht stattgefunden.
* **Keycloak und `user_oidc` sind ausschließlich für S5 dazugekommen** (5.6), nicht als Teil des
  Aufbaus von Weg 0 oder Weg 1: Keycloak lief als `start-dev` auf einer Datenbank im Arbeitsspeicher,
  die Realm ist mit `kcadm.sh` erzeugt worden, und der `sso_provider_type` jedes Laufs ist von diesem
  Bericht selbst gesetzt. Keiner dieser Werte ist aus openDesk übernommen.

**Zwei Punkte, an denen der Bericht ausdrücklich weniger sagt, als ein Leser gern hätte.** Der einzige
sitzungsfreie OIDC-Pfad, `nextcloud_hub`, ist nicht widerlegt, sondern ungemessen; wer Weg 0 im
OIDC-Betrieb verwirft, verwirft ihn ohne diesen Messwert (2.5). Und die für OD-04 wertvollste Route,
`GET /api/v1/work-packages/{id}/file-links`, ist ohne registrierte Ablage nicht aufgerufen worden;
belegt sind ihre Existenz und ihre Signatur, nicht ihr Verhalten (2.5, 3.3).

**Über den nativen MCP-Endpunkt von OpenProject sagt diese Messung nichts.** OpenProject 17.7.2 bringt
ihn mit, belegt aus dem laufenden Container: `mount API::Mcp => "/mcp"` in `config/routes.rb:48`, eine
Verwaltungsseite in Zeile 676, der Scope `mcp` in `doorkeeper.rb:136` und ein Seed-Schritt beim ersten
Start. Ein unauthentifizierter Aufruf antwortet 500, ist also eine antwortende Route und keine 404.
Über seine Werkzeugliste, seinen Authentifizierungsweg, seinen Berechtigungsdurchgriff und darüber, ob
openDesk ihn einschaltet, ist **nichts** gemessen. Der Fund berührt OD-04 (es gäbe einen dritten Weg,
auf dem der Assistent beide Server nebeneinander spricht) und gehört als Frage in den ISV-Kanal, nicht
als Aussage in diesen Bericht (DI-17-01).

**Zwei weitere Eingriffe derselben Art, und sie sind Aussagen über die Messumgebung und nicht über ein
Ergebnis.** Für S5 ist der Nextcloud-Loglevel auf `Debug (0)` gesenkt worden
(`occ log:manage --level 0`), und zwar vor dem ersten Lauf: die drei Meldungen, die die Ereignispfade
unterscheiden, sind `logger->debug`, und der Vorgabewert `Warning (2)` verschluckt sie. Ebenso ist
`occ config:app:set user_oidc allow_insecure_http --value=1` gesetzt worden, weil `user_oidc` die
Anmeldung sonst mit `You must access Nextcloud with HTTPS to use OpenID Connect.` abbricht
(`LoginController.php:121-126`).

**Beides betrifft eine Wegwerf-Instanz auf 127.0.0.1 und ist ausdrücklich keine Empfehlung für
Produktion.** Ein auf `debug` gesenkter Nextcloud-Log kann Nutzerdaten und Tokenbruchstücke in eine
Datei schreiben, die für dieses Niveau nicht gedacht ist, und OpenID Connect über plain http gibt das
Sitzungstoken auf der Leitung preis. Beide Zustände verschwinden mit dem Nextcloud-Band beim
`down -v`, und die ausgelieferte ExApp ist von keinem der beiden berührt. Sie stehen hier, damit ein
Nachbau sie als Eingriff erkennt und nicht als Vorgabe übernimmt.

## Der Produktionsbaum nach dieser Phase

Erfolgskriterium 5 der Roadmap verlangt einen stillstehenden Produktionsbaum: kein neues Werkzeug, kein
neuer Client im Paket, Werkzeugoberfläche und Budget-Gate unverändert (D-12). Das ist keine Zusicherung,
sondern ein Nachweis, und er besteht aus vier Läufen am 2026-08-29, alle gegen den Stand dieses
Berichts.

| # | Nachweis | Kommando | Ergebnis |
|---|----------|----------|----------|
| 1 | Nichts liegt unverfolgt herum, und nichts hat sich seit dem Stand vor der Phase bewegt | `git status --short src/ appinfo/ pyproject.toml uv.lock` und `git diff --stat 90d2f68..HEAD -- src appinfo pyproject.toml uv.lock` | beide **leer**. `90d2f68` ist der letzte Commit vor `docs(17): research openDesk spike domain`, also der Stand vor der Phase. Die Phase hat 33 Dateien geändert, keine davon unter `src/` oder `appinfo/` |
| 2 | Die Werkzeugoberfläche ist unverändert | `uv run python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000`, Zeichen für Zeichen dieselbe Zeile wie am 2026-08-28. Keine Grenze ist angehoben worden |

The historical tool count above is from the recorded run; the current count is held by
`tests/contract/test_tool_surface.py`.
| 3 | Die Vorgabesuite ist grün | `uv run pytest -q` | **2813 passed, 163 deselected** in 72,69 s. Es ist keine Test-Datei entstanden: die Spike-Messungen laufen außerhalb der Suite |
| 4 | Lint und Format sind grün | `uv run ruff check .` und `uv run ruff format --check .` | `All checks passed!` und `202 files already formatted`. `.planning/` ist von ruff ausgenommen, und das bleibt so |

Der Nachweis 2 ist der scharfe von den vieren. Ein Werkzeug, das unbemerkt dazukommt, fällt in einem
Diff über 33 Dateien nicht auf, in dieser einen Zeile aber sofort, weil sie drei Zahlen gleichzeitig
nennt. Weicht eine davon ab, ist das ein Fehlschlag von Erfolgskriterium 5 und keine Kleinigkeit.

**Die Messumgebung ist abgeräumt.** `docker compose -f compose.spike-opendesk.yml --profile op
--profile oidc down -v` hat die sechs Container mit dem Präfix `nc-mcp-spike-od` und alle fünf Bände
der Topologie entfernt. `docker ps -a` nennt danach keinen Container mit diesem Präfix,
`docker volume ls` kein Band und `docker network ls` kein Netz. Die Wegwerf-Instanz mit ihren
Wegwerf-Passwörtern, dem abgeschalteten Bruteforce-Schutz, dem auf `debug` gesenkten Loglevel und
`allow_local_remote_servers = true` existiert damit nicht mehr.

**Ein siebter Container trägt den Präfix nicht und musste deshalb eigens abgeräumt werden, und das ist
derselbe Befund wie in 17-02, nur in der Gegenrichtung.** Der Deploy-Daemon benennt den ExApp-Container
global `nc_app_<appid>` und nicht projektgebunden. Nach dem `down -v` lief er weiter, hing als einziger
noch am Netz `nc-mcp-spike-od-net` (weshalb dessen Entfernung mit `Resource is still in use` scheiterte)
und trug das Bild aus der Registry auf `127.0.0.1:5001` der Spike-Topologie. Abgeräumt mit
`docker rm -f nc_app_mcp_connector` und `docker network rm nc-mcp-spike-od-net`.

**Die vorherige ExApp-Topologie ist wieder benutzbar.** `compose.exapp.yml`, die Plan 17-02
ausdrücklich nur mit `stop` angehalten und nie mit `down -v` entfernt hat, läuft wieder
(`up -d --wait`, fünf Container gesund). Weil die Registrierung in **ihrer** Nextcloud die Phase
überdauert hatte, während ihr Container zwischenzeitlich von der Spike-Topologie ersetzt worden war,
hat der idempotente Bootstrap ihn nicht neu ausgerollt, sondern die vorhandene Registrierung gemeldet.
Der Weg dafür steht im Skript selbst: `occ app_api:app:unregister mcp_connector --force`, danach
`bash scripts/bootstrap_exapp.sh`. Gegengeprobt ist der Endzustand und nicht die Absicht:
`occ app_api:app:list` nennt `mcp_connector (MCP Connector): 0.1.11 [enabled]`, der Container hängt
wieder am Netz `nc-mcp-exapp-net`, und ein `POST http://127.0.0.1:8081/exapps/mcp_connector/mcp` ohne
Token antwortet **401** statt der 503, die der stehengebliebene Spike-Container vorher lieferte.

Die Container fremder Projekte auf diesem Rechner sind nicht angefasst worden: `findling-nextcloud` und
`nc-mcp-test` laufen unverändert seit 13 Tagen beziehungsweise zwei Wochen.
