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

noch nicht gemessen, Plan 17-01

### 1.1 App Store

noch nicht gemessen, Plan 17-01

### 1.2 Deploy-Daemon und Kubernetes

noch nicht gemessen, Plan 17-01

### 1.3 Versionspin 33.0.7 gegen die 34.0.3-Nachweise dieses Projekts

noch nicht gemessen, Plan 17-01

Messteil S0 (hält die Ein-Klick-Installation auf 33.0.7): noch nicht gemessen, Plan 17-02

### 1.4 Was offen bleibt

noch nicht gemessen, Plan 17-01

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
