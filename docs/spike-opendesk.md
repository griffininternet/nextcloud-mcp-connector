# openDesk-Spike (OD-01, OD-02, OD-03)

**Status:** in Arbeit
**Entscheidungsdatum:** offen, wird gesetzt, sobald der Status auf abgeschlossen wechselt
**Nextcloud:** noch nicht gemessen (Plan 17-02)
**AppAPI:** noch nicht gemessen (Plan 17-02)
**`integration_openproject`:** noch nicht gemessen (Plan 17-02)
**`user_oidc`:** noch nicht gemessen (Plan 17-02)
**OpenProject:** noch nicht gemessen (Plan 17-02)
**Keycloak:** noch nicht gemessen (Plan 17-02)
**Deploy-Daemon:** HaRP, vorgesehen über die Topologie der Spike-Compose-Datei; die laufende Registrierung ist noch nicht gemessen (Plan 17-02)
**Scope:** gemessen wird zweierlei: erstens die Installierbarkeit dieser App in einer openDesk-Umgebung, ausschließlich aus öffentlich ladbaren Quellen an festen Tags, zweitens die beiden Zugriffswege auf die Nutzeridentität gegen OpenProject, lokal in Docker mit gepinnten Fassungen. Ausdrücklich nicht gemessen wird: kein Kubernetes-Cluster wird beschafft, keine openDesk-Installation wird versucht, und es entsteht kein Produktionscode. Die Werkzeugoberfläche und das Budget-Gate der ausgelieferten App stehen in dieser Phase still.

Die Fassungen im Kopfblock werden vor dem Schreiben aus der laufenden Instanz gelesen (`occ status` für den Server, `occ app:list` für `app_api`, `integration_openproject` und `user_oidc`) und nicht aus der Recherche übernommen. Solange eine Zeile `noch nicht gemessen (Plan 17-02)` trägt, steht dort kein Wert aus der Recherche, sondern gar keiner.

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

**Und der Befund, der die Frage überhaupt stellt: openDesk richtet keinen AppAPI-Daemon ein.** Die projektweite Blob-Suche über die GitLab-API verlangt eine Anmeldung und antwortet ohne sie mit HTTP 401. Das Repository-Archiv verlangt keine. Gemessen am 2026-08-28:

```
GET https://gitlab.opencode.de/bmi/opendesk/deployment/opendesk/-/archive/v1.18.0/opendesk-v1.18.0.tar.gz
-> HTTP 200, 2285825 Bytes, entpackt 349 Dateien (Verzeichnis außerhalb dieses Repositories)

grep -ril "app_api\|appapi\|external.app\|exapp" .
-> 0 Treffer

grep -ril "authorization_method\|integration_openproject\|integrationOpenproject" .
-> 3 Dateien: ./docs/architecture.md
              ./docs/debugging.md
              ./helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl
```

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

Messteil S0 (hält die Ein-Klick-Installation auf 33.0.7): noch nicht gemessen, Plan 17-02

### 1.4 Was offen bleibt

Vier Punkte sind aus Quellen nicht entscheidbar. Sie stehen hier namentlich, mit Grund, und jeder trägt den Verweis auf die Frage in Abschnitt 4, die ihn im ISV-Call am 14.09. abholt. Kein Punkt wird weggelassen, weil er unbequem ist, und keiner wird durch eine Vermutung ersetzt.

| Offener Punkt | Warum aus Quellen nicht entscheidbar | Verweis |
|---------------|---------------------------------------|---------|
| Ist `app_api` im openDesk-Nextcloud-Image enthalten und eingeschaltet? (in 1.2 als Punkt 1a benannt) | Das Image wird aus einem anderen, hier nicht mitgelesenen Projekt gebaut. Der Archivgriff über das Deployment-Projekt kann eine mitgelieferte Serverapp im Image grundsätzlich nicht sehen | Abschnitt 4, Frage 6 |
| In welchem Modus läuft `integration_openproject` in openDesk, `oauth2` oder `oidc`? | Die Einrichtung macht der Job `opendesk-openproject-bootstrap`, dessen Logik in einem eigenen Image liegt. Im Deployment-Projekt stehen nur seine Eingaben, ein OpenProject-API-Admin und ein Nextcloud-Admin samt Passwörtern. Das legt den Zwei-Wege-OAuth2-Weg nahe, ist aber Indiz und nicht Beleg; dieser Bericht behauptet deshalb keine Betriebsart | Abschnitt 4, Frage 7 |
| Würde ein Betreiber eine Dritt-ExApp neben der Suite aufnehmen, und wer entscheidet das? | Betriebs- und Verfahrensfrage, öffentlich nicht dokumentiert. Kein Quellcode und kein Helmfile kann sie beantworten | Abschnitt 4, Frage 1 |
| Wann geht openDesk auf Nextcloud 34 oder höher? | Terminfrage an ZenDiS. Sie ist erst durch den Befund aus 1.2 entstanden und in keiner öffentlichen Quelle beantwortet | Abschnitt 4, Frage 5 |

Ein fünfter Punkt aus 1.2 wird nicht als eigene Zeile geführt, aber auch nicht unterschlagen: dass `stable34` keine Oberflächenvorlage für `kubernetes-install` mitbringt, ist ungemessen in der Absicht und geht als Nebenfrage zu Frage 5 in Abschnitt 4 mit.

**Antwort auf OD-01, in drei Sätzen.** Aus openDesk-Quellen belegt ist, dass die Ein-Klick-Erzählung dieses Produkts in einer openDesk-Installation nicht existiert: der App Store ist aus, und AppAPI kommt im Deployment-Projekt an keiner Stelle vor. Aus openDesk- und AppAPI-Quellen belegt ist außerdem, dass auf dem gepinnten Stand 33.0.7 kein Kubernetes-Deploy-Daemon existiert und eine Hauptversion darüber einer existiert. Offen bleibt der Installationsweg selbst, und weil beide Hürden dieselbe sind und mit demselben Schritt fallen, ist das eine Terminfrage an ZenDiS und keine Absage.

Die Trennung, die dieser Bericht durchhält: alles in Abschnitt 1 ist aus openDesk-Quellen belegt, nichts davon ist lokal gemessen. Der erste lokal gemessene Wert entsteht mit S0 in Plan 17-02 und wird dort auch so bezeichnet. Ein Satz, der "in openDesk" sagt und auf einen lokalen Messwert zeigt, ist in diesem Bericht ein Fehler und kein Befund.

## 2. Nutzeridentität gegen OpenProject (OD-02)

### 2.1 Weg 0: Behauptungen S1 bis S6, je Behauptung Messweg, Messwert, Gegenprobe

noch nicht gemessen, Plan 17-05 und 17-06

### 2.2 Weg 1: PKCE, `expires_in`, Erneuerung ohne Browsersitzung, Zwei-Konten-Negativbeweis

noch nicht gemessen, Plan 17-04

### 2.3 Die SSRF-Grenze und was sie wirklich abdeckt

noch nicht gemessen, Plan 17-02

### 2.4 Welcher Weg trägt, als Folge dieser Messungen

noch nicht gemessen, Plan 17-09

### 2.5 Was ungemessen blieb, und warum die Messung nicht möglich war

noch nicht gemessen, Plan 17-09

## 3. API-Form (Vorarbeit für OD-04, kein Requirement dieser Phase)

noch nicht gemessen, Plan 17-09

## 4. Fragenliste für den ISV-Call am 14.09. (OD-03)

noch nicht gemessen, Plan 17-08

## 5. Rohmesswerte

**Geheimnisregel, gültig für jede Zeile dieses Abschnitts.** Diese Datei liegt in einem öffentlichen Repository. Protokolliert werden ausschließlich Statuscodes, Feldnamen, Zahlen, Längen und Präfixe. Niemals protokolliert wird ein `access_token`, ein `refresh_token`, ein Autorisierungscode, ein `client_secret` oder ein Wert des Headers `AUTHORIZATION-APP-API`: dieser Wert ist Base64 von `<user>:<APP_SECRET>` und damit genau so heikel wie das Geheimnis selbst. Tokenwerte werden auf ihre Länge und ihr Präfix reduziert. `expires_in` ist eine Zahl und darf stehen. Vor jedem Commit an dieser Datei läuft ein Griff nach `eyJ`, `Bearer `, `refresh_token=` und `client_secret` über die geänderten Zeilen.

noch nicht gemessen, dieser Abschnitt wird von allen Plänen der Phase gefüllt

## Was diese Messung nicht beweist

noch nicht gemessen, Plan 17-09
