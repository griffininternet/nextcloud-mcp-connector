# Phase 17: openDesk-Spike - Recherche

**Recherchiert:** 2026-08-28
**Domain:** Messbarkeit einer ExApp-Installierbarkeit in einer Kubernetes-Distribution (openDesk) und
zweier Zugriffswege auf einen zweiten, fremden Host (OpenProject) im Namen des angemeldeten Nutzers
**Konfidenz:** HIGH für die Quellenlage (Quellcode an gepinnten Tags gelesen, Datei und Zeile genannt),
MEDIUM für die lokale Messbarkeit (die Topologie steht im Repo, die OpenProject-Hälfte ist neu),
LOW für den ZenDiS-Aufnahmeprozess (öffentlich nicht dokumentiert, das ist selbst der Befund)

## Summary

Diese Recherche hat sechs Befunde erbracht, die die Ausgangslage aus `research/SUMMARY.md`,
`research/STACK.md` und `research/PITFALLS.md` **korrigieren**, nicht nur bestätigen. Der wichtigste:
**AppAPI hat einen Kubernetes-Deploy-Daemon, aber erst ab Nextcloud 34.** In `app_api` auf dem Zweig
`stable33` existiert `lib/DeployActions/KubernetesActions.php` nicht (HTTP 404), auf `stable34` und
`stable35` existiert sie, mit `DEPLOY_ID = 'kubernetes-install'`, vier Service-Freigabearten und vier
eigenen CI-Workflows. Damit ist die zweite der drei OD-01-Hürden nicht "AppAPI kann kein Kubernetes",
sondern "AppAPI kann Kubernetes, aber nicht auf dem Stand, auf den openDesk gepinnt ist". Das dreht die
Frage für den ISV-Call von einer Absage in eine Terminfrage.

Der zweite wichtige Befund: **`force_pkce` steht unbedingt im Doorkeeper-Initializer von OpenProject
17.7.2**, also der Fassung, die openDesk 1.18.0 fährt. Die offene Frage aus `STACK.md` A.8 ("nimmt
`/oauth/authorize` PKCE an, obwohl die Metadaten es nicht bewerben") ist damit umgekehrt: ein
öffentlicher Client **muss** PKCE senden, sonst wird er abgewiesen. Die Messung wird also nicht prüfen,
ob PKCE geht, sondern belegen, dass PKCE Pflicht ist, mit der Gegenprobe eines Fluss ohne
`code_challenge`. Dazu kommen aus derselben Datei die harten Zahlen, die OD-02 verlangt:
`access_token_expires_in 2.hours`, `authorization_code_expires_in 10.minutes`, `use_refresh_token`,
`default_scopes :api_v3`.

Der dritte: **die S2-Behauptung aus `ARCHITECTURE.md` ist falsch formuliert.** `getOpenProjectUrl()`,
die Methode hinter `/api/v1/url`, ruft `validatePreRequestConditions()` **nicht** auf und antwortet
deshalb auch für ein Konto ohne verbundenes OpenProject mit 200 und der Instanzadresse. Der
Berechtigungsnachweis muss gegen eine Route laufen, die die Vorprüfung wirklich fährt. Die übrigen drei
Befunde: `integration_openproject` veröffentlicht eine echte Capability (kein Navigations-Umweg wie bei
Mail nötig), der Bruch im OIDC-Modus hat **drei** unterschiedliche Ereignispfade statt einem, und ein
repository-weiter Griff durch das openDesk-Deployment auf Tag `v1.18.0` findet **null** Treffer für
`app_api`, `appapi`, `exapp` oder `external app`.

**Primäre Empfehlung:** OD-01 ist zu rund 90 Prozent aus Quellen abschließend beantwortbar, und zwar
schärfer als die Meilenstein-Recherche vermutete. Diese Arbeit zuerst und ohne Docker erledigen, weil
sie billig ist und die Reihenfolge des Berichts vorgibt. Danach die Messumgebung in **zwei** Stufen
bauen: Stufe A (Nextcloud 33.0.7 plus OpenProject 17.7.2, `authorization_method = oauth2`) trägt S1
bis S4, S6, Weg 1 vollständig und den Zwei-Konten-Negativbeweis auf beiden Wegen. Stufe B (Keycloak
26.7.0 plus `user_oidc` 8.11.0 dazu) trägt S5 und die Live-Reproduktion für `user_oidc#925`. Stufe B ist
der teuerste Teil und hat einen dokumentierten Rückfall auf "ungemessen, Quellcodebeleg plus offene
Frage", Stufe A hat keinen.

---

<user_constraints>
## User Constraints (aus 17-CONTEXT.md)

### Locked Decisions

**Messumgebung und Kosten**
- **D-01:** OD-01 wird ausschließlich aus Quellen belegt, ohne Kubernetes-Cluster: openDesk-Helmfile
  (`helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl`), AppAPI-Dokumentation zu
  Deploy-Daemons, Nextcloud-Dokumentation zu `manual_install`. Jede der drei Hürden (abgeschalteter
  App Store, keine AppAPI auf Kubernetes, Pin auf Nextcloud 33.0.7 gegen unsere Nachweise auf
  34.0.3) bekommt ein Quellenzitat oder wird ausdrücklich als offene ISV-Call-Frage markiert.
- **D-02:** OD-02 wird lokal in Docker gemessen, mit gepinnten Versionen: Nextcloud **33.0.7**
  (der openDesk-Stand, nicht 34.0.3) plus `integration_openproject`, dazu OpenProject Community
  **17.7.x**. Kein `latest`.
- **D-03:** In dieser Phase entsteht **keine gemietete Box**. Was lokal nicht messbar ist, wird im
  Bericht als "ungemessen" geführt, nie als "verworfen".

**Messtiefe Weg 1 (eigener OAuth-Fluss gegen OpenProject)**
- **D-04:** Weg 1 wird mit vollem Consent-Flow gemessen, nicht nur angeklopft: OAuth-Anwendung in
  OpenProject anlegen, Autorisierungscode einmal durch den Browser holen, dann echte Werte
  festhalten: nimmt `/oauth/authorize` PKCE an, obwohl die Metadaten es nicht bewerben, welche
  `expires_in`, und trägt die Erneuerung ohne Browsersitzung.
- **D-05:** Der Negativbeweis mit **zwei Nutzerkonten** (Nutzer B sieht das Arbeitspaket von A
  nicht) ist auf **beiden** Wegen Pflicht, nicht nur auf dem gewinnenden.
- **D-06:** Die SSRF-Grenze aus v1.1 wird **gemessen**, nicht aus dem Code hergeleitet: lässt die
  Prüfung einen Nachbardienst unter internem Docker-Dienstnamen durch oder sperrt sie ihn
  fälschlich aus, mit den Fällen aus dem bestehenden Negativkatalog.

**OIDC-Bruchstelle S5 (die Stelle, an der Weg 0 kippt)**
- **D-07:** S5 wird gemessen, nicht behauptet: Keycloak plus `user_oidc` kommen lokal dazu, damit
  geprüft ist, ob die serverseitige Token-Erneuerung von `integration_openproject` auch im
  OIDC-gebundenen Betrieb hält oder nach Ablauf des zwischengespeicherten Tokens auf 401 fällt.
- **D-08:** Derselbe Aufbau liefert die Live-Reproduktion für `nextcloud/user_oidc#925`. Das Issue
  geht **nur** mit geglückter Repro raus; der Entwurf liegt im Repo und **der Owner sendet**.
  Ohne Repro bleibt der Entwurf liegen (Regel aus context_agent#230).

**Ablage von Bericht, Fragenliste und Kanälen**
- **D-09:** Der Spike-Bericht wird `docs/spike-opendesk.md`, nach dem Muster von `docs/spike-dav.md`,
  `docs/spike-discovery.md` und `docs/spike-mail.md`; die Rohmesswerte stehen als eigener Abschnitt
  darin. Reihenfolge im Bericht: erst Installierbarkeit, dann Auth, dann API-Form.
- **D-10:** Die ISV-Fragenliste (OD-03) wird in `Desktop/ISV-Call-Dossier-2026-09-14.md` ergänzt
  **und** als Abschnitt in den Spike-Bericht aufgenommen, damit sie versioniert ist.
- **D-11:** Zum Forumsbeitrag über die OCS-Routen: `christianlupus` hat am 28.08. geantwortet, im
  Community-Chat selbst keine Antwort erhalten und rät zu einem Konto in der OpenProject-Community.
  Die Phase erzeugt zwei **Entwürfe**: eine kurze Antwort an christianlupus im Nextcloud-Forum und
  eine Konto-Anfrage an die OpenProject-Community (Selbstregistrierung dort liefert HTTP 400
  "Registration not allowed"). Owner-Zusage 28.08.: "ich würde ein community account beantragen
  wenn es sein muss". **Gesendet wird ausschließlich vom Owner.**
- **D-12:** Auch wenn die Messung Weg 0 als tragend zeigt, entsteht in dieser Phase **kein Code**:
  kein Client-Modul, kein Werkzeug, kein Prototyp im Paketbaum. Der Weg-0-Client ist OD-04 und
  wartet auf v2.0 nach dem ISV-Call.

### Claude's Discretion

- Aufteilung der Messungen in Pläne und Wellen, Form der Docker-Compose-Dateien und wo sie liegen
  (außerhalb von `src/`), Aufbau der Messprotokolle, Reihenfolge innerhalb von OD-02, Wortwahl der
  Entwürfe.

### Deferred Ideas (AUSSERHALB DES UMFANGS)

- **Weg-0-Client als Code** (`nextcloud/clients/integration_openproject.py`) und das Werkzeug
  `openproject_browse` samt `wp:<id>` für `fetch`: OD-04, v2.0, nach dem ISV-Call.
- **Wegwerf-Prototyp außerhalb des Paketbaums**, der den gewinnenden Weg einmal echt durchspielt:
  vom Owner am 28.08. abgelehnt zugunsten "nur berichten".
- **k3s- oder Cloud-Installationsversuch für openDesk**: bewusst nicht in dieser Phase; wenn der
  ISV-Call einen Installationsweg nennt, wird er dort geprüft.
- **Antwort auf die OCS-Frage über die OpenProject-Community**: Konto-Anfrage entsteht als Entwurf,
  der Rückkanal läuft nach dieser Phase weiter.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Beschreibung (gekürzt aus REQUIREMENTS.md) | Was diese Recherche dafür bereitstellt |
|----|--------------------------------------------|-----------------------------------------|
| **OD-01** | Gemessen und schriftlich belegt, ob und auf welchem Weg diese ExApp in openDesk installierbar ist, gegen die drei Hürden abgeschalteter App Store, keine AppAPI in der Distribution, Kubernetes statt Docker; samt Aussage, was der Pin auf Nextcloud 33.0.7 für unsere 34.0.3-Nachweise bedeutet | Abschnitt "OD-01: Installierbarkeit aus Quellen". Alle drei Hürden mit Datei, Zeile und wörtlichem Zitat an gepinnten Tags belegt, plus der neue Versionsbefund `kubernetes-install` ab NC 34. Eine Rest-Unbekannte (`authorization_method` in openDesk) bleibt als ISV-Frage |
| **OD-02** | Weg 0 und Weg 1 mit Messwerten nebeneinander, mindestens PKCE, Token-Lebensdauer, Erneuerung ohne Browsersitzung, dazu die SSRF-Frage nach dem internen Dienstnamen. Entscheidung fällt auf der Messung | Abschnitte "OD-02 Weg 0" (17 OCS-Routen mit Zeilennummern, Konfigurationsschlüssel, S1 bis S6 als Messwege mit erwarteten Werten), "OD-02 Weg 1" (Endpunkte, `force_pkce`, `expires_in 7200`, Refresh-Messweg, Zwei-Konten-Negativbeweis mit dem gemessenen 404-Verhalten), "S5 und der OIDC-Bruch" (drei Ereignispfade, Bruchstelle mit Zeile), "SSRF-Messung" (Ort der Grenze, Negativkatalog, Messweg ohne Produktionscode-Änderung) |
| **OD-03** | Fragenliste für den ISV-Call am 14.09. mit ZenDiS-Aufnahmeverfahren, Installationsweg in openDesk, AGPL-Konsequenz, Folge der abgeschalteten Apps Talk und Kontakte | Abschnitt "OD-03: was auf die Fragenliste gehört und was nicht mehr". Vier Pflichtfragen plus fünf aus dieser Recherche neu abgeleitete; drei Fragen der Ausgangsrecherche sind durch diese Recherche beantwortet und gehören **nicht** mehr auf die Liste |
</phase_requirements>

---

## Project Constraints (aus CLAUDE.md)

| Direktive | Folge für diese Phase |
|-----------|------------------------|
| Core Value: "der Assistent sieht niemals mehr als der angemeldete Nutzer" | Jede Messung nennt den Nutzernamen, unter dem sie lief. Ein Messwert ohne Nutzernamen ist kein Messwert (Pitfall 1) |
| Security: "Der MCP darf nie mehr sehen als der angemeldete Nutzer; keine destruktiven Writes" | Die Messung fährt ausschließlich lesende Routen. `POST /api/v1/create/work-packages` und `DELETE /api/v1/file-links/{id}` werden **nicht** ausgelöst, auch nicht in der Messumgebung |
| Sprache: Code und README Englisch, Projektkommunikation Deutsch, echte Umlaute, keine Em-Dashes | `docs/spike-opendesk.md` folgt `docs/spike-mail.md`: deutscher Fließtext ist hier etabliert, die drei Vorgänger sind gemischt. Empfehlung: deutsch, wie `spike-mail.md` |
| Tech stack: Python 3.13, uv als Toolchain (lokales System-Python ist defekt), Docker/WSL2 | Jeder Python-Aufruf der Messung läuft über `uv run`. Das gilt auch für Wegwerf-Skripte |
| Lizenz AGPL-3.0 | Die AGPL-Konsequenz für die Enterprise-Positionierung bleibt ISV-Frage, sie ist keine Recherchefrage |
| Solo-Betrieb, Wartungsaufwand pro Feature zählt | Die Messumgebung darf keine Dauerlast werden. Compose-Datei plus Bootstrap-Skript, danach `down -v` |
| GSD-Workflow: keine direkten Repo-Edits außerhalb eines GSD-Kommandos | Gilt unverändert |

**Projekt-Skills:** `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/` und
`.codex/skills/` existieren in diesem Repository nicht. Keine Skill-Regeln zu beachten.
[VERIFIED: Verzeichnisprüfung im Repository, 2026-08-28]

---

## Architectural Responsibility Map

Diese Phase baut kein System, sie misst zwei. Die Karte ordnet deshalb nicht Bauteile, sondern
**Messfähigkeiten** der Schicht zu, die sie beantworten kann. Der Nutzen ist derselbe: sie verhindert,
dass eine Frage in der falschen Schicht gemessen wird, etwa der Nutzeridentitätsdurchgriff im Browser
statt am Server.

| Fähigkeit | Primäre Schicht | Sekundäre Schicht | Begründung |
|-----------|-----------------|-------------------|------------|
| Installierbarkeit in openDesk | Distributions-Konfiguration (Helmfile, openCode) | Nextcloud-Serverapp `app_api` | Die Distribution entscheidet, welche Apps aktiv sind; `app_api` entscheidet, welche Deploy-Verfahren überhaupt existieren. Keine der beiden Fragen ist im Container messbar |
| PKCE-Pflicht, Token-Lebensdauer, Refresh (Weg 1) | OpenProject Rails/Doorkeeper | Browser (nur für den einen Consent-Schritt) | Doorkeeper entscheidet; der Browser liefert nur die Sitzung, die `resource_owner_authenticator` verlangt |
| Nutzeridentität gegen OpenProject (Weg 0) | Nextcloud PHP (`integration_openproject`) | ExApp-Container (nur als Aufrufer) | Nextcloud hält das Token und erneuert es. Der Container ist Aufrufer, nicht Halter. Genau das ist der Grund, warum Weg 0 das Versprechen nicht anfasst |
| Token-Erneuerung im OIDC-Modus (S5) | Nextcloud PHP (`user_oidc`) | Keycloak | Die Bruchstelle ist eine PHP-Sitzungsbedingung in `user_oidc`, nicht ein Keycloak-Fehler. Keycloak ist Kulisse, nicht Messobjekt |
| Zwei-Konten-Negativbeweis | OpenProject Berechtigungsprüfung | Nextcloud Impersonation | Auf Weg 1 entscheidet OpenProject allein; auf Weg 0 entscheidet erst Nextcloud (wer ist der Nutzer), dann OpenProject (was darf er sehen). Beide Ketten brauchen ihren eigenen Beweis |
| SSRF-Grenze gegen internen Dienstnamen | ExApp-Container (`oauth/cimd.py`) | Docker-Netz (nur als Adressquelle) | Die Grenze ist eine reine Funktion über eine aufgelöste Adresse. Sie ist ohne HTTP messbar |
| Byte-Kosten einer Antwort (S6) | OpenProject API v3 (`select`) | ExApp (Projektion, erst v2.0) | Die Diät macht diesmal der Server. Das ist der Befund, nicht die Projektion |

---

## Die sechs Befunde, die die Ausgangslage korrigieren

Dieser Abschnitt steht vor allem anderen, weil die Planung sonst Fragen messen würde, die schon
beantwortet sind, und Fragen übersehen würde, die neu entstanden sind.

### K1: AppAPI hat einen Kubernetes-Deploy-Daemon, aber erst ab Nextcloud 34

`research/SUMMARY.md` und `research/STACK.md` A.6 sagen beide, AppAPI sei "für Kubernetes nicht gebaut"
und der einzige realistische Weg sei `manual_install`. Gemessen an den Zweigen des Repositories
`nextcloud/app_api` ist das für den openDesk-Stand richtig und für die nächste Hauptversion falsch:

| app_api-Zweig / Tag | `appinfo/info.xml` `<version>` | `lib/DeployActions/KubernetesActions.php` |
|---------------------|--------------------------------|--------------------------------------------|
| `stable33`, `v33.0.0` | `33.0.0` | **fehlt** (HTTP 404) |
| `stable34`, `v34.0.0` | `34.0.0` | **vorhanden** (HTTP 200, 803 Zeilen) |
| `stable35` | `35.0.0` | vorhanden |
| `main` | `36.0.0-dev.0` | vorhanden |

[VERIFIED: HTTP-Statusabfrage gegen raw.githubusercontent.com je Zweig, 2026-08-28]

Die Datei trägt `public const DEPLOY_ID = 'kubernetes-install';` (Zeile 37) und arbeitet durchgehend
über HaRP (`buildHarpK8sUrl()`, Zeile 765; `deployExApp(..., $harpUrl, ...)`, Zeile 69). Sie wurde am
**2026-02-22** mit einem einzigen Commit "feat: add Kubernetes deployment support" eingeführt.
[VERIFIED: GitHub-Commit-API für den Pfad, 2026-08-28]

Der Beleg, der es unstrittig macht, ist die Hilfe des Registrierungskommandos, weil sie die zulässigen
Werte aufzählt:

```
# app_api stable33, lib/Command/Daemon/RegisterDaemon.php:37
'The deployment method that the daemon accepts. Can be "manual-install" or "docker-install".
 "docker-install" is for Docker Socket Proxy and HaRP.'

# app_api stable34, lib/Command/Daemon/RegisterDaemon.php:37
'The deployment method that the daemon accepts. Can be "manual-install", "docker-install", or
 "kubernetes-install". "docker-install" is for HaRP (recommended) and the legacy Docker Socket
 Proxy (deprecated, scheduled for removal in Nextcloud 35).'
```

[VERIFIED: beide Dateien an ihrem Zweig gelesen, 2026-08-28]

`stable34` bringt dazu sieben eigene Optionen (`RegisterDaemon.php:54-60`): `--k8s`,
`--k8s_expose_type` (Werte `nodeport|clusterip|loadbalancer|manual`, Vorgabe `clusterip`),
`--k8s_node_port`, `--k8s_upstream_host`, `--k8s_external_traffic_policy`, `--k8s_load_balancer_ip`,
`--k8s_node_address_type`. `--k8s` ist ausdrücklich "Requires --harp flag". Vier CI-Workflows testen
den Weg (`tests-deploy-k8s.yml`, `-clusterip`, `-loadbalancer`, `-manual`), dazu
`tests/test_occ_commands_k8s.py`.
[VERIFIED: Verzeichnisbaum von `stable34` über die GitHub-Tree-API, 2026-08-28]

**Folge für OD-01:** Die dritte Hürde (Versionspin) und die zweite Hürde (Kubernetes) sind **dieselbe
Hürde**. Der Satz, den der Bericht führen muss, lautet nicht "AppAPI kann kein Kubernetes", sondern:
auf dem Stand, auf den openDesk 1.18.0 gepinnt ist, existiert der Kubernetes-Weg noch nicht, eine
Hauptversion darüber existiert er. Und damit wird aus einer Absage eine Terminfrage an ZenDiS. Das ist
zugleich die stärkste Frage, die diese Phase für den 14.09. produziert.

**Sichtbarkeitsvorbehalt, ehrlich benannt:** In `src/constants/daemonTemplates.js` von `stable34`
existiert **keine** Vorlage für `kubernetes-install`; die acht Vorlagen dort sind unverändert die von
`stable33` (sechs `docker-install`, zwei `manual-install`). Der Kubernetes-Weg ist also in `stable34`
nur über `occ app_api:daemon:register --k8s` erreichbar, nicht über die Admin-Oberfläche. Ob das
Absicht oder Rückstand ist, ist ungemessen und gehört als Nebenfrage auf die Liste.
[VERIFIED: `daemonTemplates.js` von `stable33`, `stable34` und `main` verglichen, 2026-08-28]

### K2: `force_pkce` steht unbedingt in OpenProject 17.7.2, PKCE ist Pflicht statt Frage

`research/STACK.md` A.1 Befund 2 und A.8 Frage 1 führen als "wichtigsten offenen Punkt", ob
`/oauth/authorize` PKCE annimmt. Aus `config/initializers/doorkeeper.rb` am Tag `v17.7.2` gelesen:

```ruby
# Zeile 57-59
authorization_code_expires_in 10.minutes
# Zeile 61-64
access_token_expires_in 2.hours
# Zeile 88-90
# Require non-confidential clients to use PKCE when using an authorization code
# to obtain an access_token (disabled by default)
force_pkce
# Zeile 92-94
hash_token_secrets
hash_application_secrets
# Zeile 115
use_refresh_token
# Zeile 134-136
default_scopes :api_v3
optional_scopes :scim_v2, :mcp
```

[VERIFIED: `https://raw.githubusercontent.com/opf/openproject/v17.7.2/config/initializers/doorkeeper.rb`, 2026-08-28]

Vier Konsequenzen, jede eine Planungsanweisung:

1. **PKCE ist für einen nicht vertraulichen Client Pflicht.** Die Doorkeeper-Semantik von `force_pkce`
   ist wörtlich "Require non-confidential clients to use PKCE". Ein Client mit gesetztem Häkchen
   "Confidential" darf PKCE weglassen, ein öffentlicher nicht. Die Messung von D-04 ist damit nicht
   mehr "nimmt er es an", sondern zwei Läufe: ein öffentlicher Client **mit** `code_challenge` (muss
   200 liefern) und derselbe Client **ohne** (muss abgewiesen werden). Der zweite Lauf ist die
   Gegenprobe, und ohne ihn ist der erste kein Beweis.
2. **`expires_in` ist 7200 und muss trotzdem gemessen werden.** Der Wert steht in der Quelle, aber
   `custom_access_token_expires_in` ist im Initializer nur auskommentiert vorhanden (Zeile 73-75); ein
   Betreiber kann ihn setzen. Der Messwert bleibt der Nachweis, die Quelle liefert den Erwartungswert.
3. **Das Client-Secret ist genau einmal sichtbar.** `hash_application_secrets` bedeutet, dass
   OpenProject das Secret gehasht ablegt. Wer es beim Anlegen der Anwendung nicht sofort kopiert, legt
   eine neue an. Das ist der wahrscheinlichste Zeitverlust in der ersten Stunde von Weg 1.
4. **`enforce_content_type` ist gesetzt (Zeile 55).** Die Token-Anfrage muss
   `Content-Type: application/x-www-form-urlencoded` tragen. Ein `curl -d` tut das von sich aus, ein
   `httpx.post(json=...)` nicht. Ein 4xx an dieser Stelle ist kein PKCE-Befund.

Dazu, aus derselben Datei, der Grund für den zusätzlichen Browserschritt:

```ruby
# Zeile 35-39
resource_owner_authenticator do
  logged_user = session[:user_id] && User.active.find_by(id: session[:user_id])
  logged_user.presence || redirect_to(signin_path(back_url: request.fullpath))
end
```

`/oauth/authorize` verlangt eine OpenProject-Browsersitzung. Lokal ist das das Anmeldeformular
(`admin`/`admin` beim ersten Start), in openDesk ist es wegen
`OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"` ein Umweg über Keycloak. Der Messaufbau
lokal reproduziert den Umweg **nicht** und darf ihn nicht behaupten.

### K3: `/api/v1/url` ist kein Berechtigungsnachweis, S2 muss umformuliert werden

`ARCHITECTURE.md` führt als Behauptung S2: "Dieselbe Route [`/api/v1/url`] antwortet für ein Konto
**ohne** verbundenes OpenProject mit 401 statt mit Daten". Aus
`lib/Controller/OpenProjectAPIController.php` am Tag `v3.1.1` gelesen:

```php
// Zeile 43-59
private function validatePreRequestConditions(): array {
    $token = $this->openprojectAPIService->getAccessToken($this->userId);
    if (!$token) {
        return ['status' => false, 'result' => new DataResponse('', Http::STATUS_UNAUTHORIZED)];
    } elseif (!OpenProjectAPIService::validateURL($this->openprojectUrl)) {
        return ['status' => false, 'result' => new DataResponse('', Http::STATUS_BAD_REQUEST)];
    }
    return ['status' => true, 'result' => null];
}

// Zeile 64-67
#[NoAdminRequired]
public function getOpenProjectUrl(): DataResponse {
    return new DataResponse($this->openprojectUrl);
}
```

`getOpenProjectUrl()` ruft `validatePreRequestConditions()` **nicht** auf. Sie gibt den App-Konfigwert
`openproject_instance_url` zurück, den der Konstruktor in Zeile 39 eingelesen hat, unabhängig davon, ob
der aufrufende Nutzer OpenProject verbunden hat. Ein Zähllauf über die Datei: 15 Methoden mit
`#[NoAdminRequired]`, davon 13 mit `validatePreRequestConditions()` in der ersten Zeile;
`getOpenProjectUrl()` und `getOpenProjectAvatar()` ohne.
[VERIFIED: Datei an `v3.1.1` gelesen und ausgezählt, 2026-08-28]

**Folge für die Planung:** S1 (Erreichbarkeit, CSRF-Pfad ohne Sitzung) bleibt richtig auf
`/api/v1/url`, weil eine Route, die nichts prüft, der klarste Erreichbarkeitstest ist: eine 200 dort
beweist, dass die Anfrage im Controller ankam und nicht in der Routing- oder Authentifizierungsschicht
starb. S2 (Berechtigung hängt am Nutzer) muss auf eine Route mit Vorprüfung wechseln. Empfehlung:
`GET /api/v1/configuration`, weil sie kein Argument braucht und nichts schreibt.

### K4: `integration_openproject` veröffentlicht eine echte Capability

`ARCHITECTURE.md` führt als offen: "Veröffentlicht `integration_openproject` eine Capability, oder
braucht es den Navigations-Kanal wie Mail". Aus `lib/Capabilities.php` an `v3.1.1`:

```php
class Capabilities implements IPublicCapability {
    public function getCapabilities(): array {
        return [
            Application::APP_ID => [       // 'integration_openproject'
                'app_version' => $appVersion,
                'groupfolder_version' => $groupfoldersVersion,
                'groupfolders_enabled' => $groupfoldersEnabled,
            ],
        ];
    }
}
```

`IPublicCapability` heißt: der Abschnitt steht auch in der unauthentifizierten Antwort von
`/ocs/v2.php/cloud/capabilities`. Der Navigations-Umweg, den `nextcloud/capabilities.py:56-58` für Mail
braucht (`NAVIGATION_PATH = "/core/navigation/apps"`), ist hier nicht nötig, und der Schlüssel trägt
sogar die App-Version, also die Information, die eine spätere Fähigkeitsprüfung wirklich braucht.
[VERIFIED: `lib/Capabilities.php` an `v3.1.1`, 2026-08-28]

**Folge:** Der Capability-Abruf gehört als Zusatzmessung in denselben Lauf wie S1 (kostet einen
Aufruf), und die Frage ist danach geschlossen, nicht offen.

### K5: Der OIDC-Bruch hat drei Pfade, nicht einen, und einer davon bricht nicht

`SUMMARY.md` und `ARCHITECTURE.md` A.4 Befund 4 beschreiben einen Pfad:
`getOIDCToken()` löst `ExchangedTokenRequestedEvent` aus, `user_oidc` liest aus der PHP-Sitzung, ohne
Sitzung 401. Aus `lib/TokenEventFactory.php` an `v3.1.1` gelesen sind es **drei** Pfade, und die
Fabrik entscheidet anhand von zwei App-Konfigwerten:

| `sso_provider_type` | `token_exchange` | Ereignis | Liest `user_oidc` daraus die Sitzung? |
|---------------------|------------------|----------|----------------------------------------|
| `nextcloud_hub` | (ignoriert) | `InternalTokenRequestedEvent` | **Nein.** `InternalTokenRequestedListener` holt `getUID()` und ruft `TokenService::getTokenFromOidcProviderApp($userId, ...)`, das eine Nutzer-Id nimmt statt einer Sitzung |
| `external` | falsch | `ExternalTokenRequestedEvent` | **Ja.** `ExternalTokenRequestedListener` wirft `GetExternalTokenFailedException`, wenn `store_login_token` aus ist, sonst `TokenService::getToken()` aus `SESSION_TOKEN_KEY` |
| `external` | wahr | `ExchangedTokenRequestedEvent` | **Ja.** `TokenService::getExchangedToken()` verlangt `store_login_token` und wirft sonst; danach `getToken()` aus der Sitzung |

[VERIFIED: `integration_openproject` `lib/TokenEventFactory.php` an `v3.1.1`; `user_oidc`
`lib/Listener/{Internal,External,Exchanged}TokenRequestedListener.php` und
`lib/Service/TokenService.php` an `v8.11.0`, 2026-08-28]

Die drei Bruchstellen wörtlich, mit Zeile:

```php
// user_oidc v8.11.0, lib/Service/TokenService.php:315-333
public function getExchangedToken(string $targetAudience, array $extraScopes = []): Token {
    $storeLoginTokenEnabled = $this->appConfig->getValueString(Application::APP_ID,
        'store_login_token', '0', lazy: true) === '1';
    if (!$storeLoginTokenEnabled) {
        throw new TokenExchangeFailedException(
            'Failed to exchange token, storing the login token is disabled. It can be enabled in config.php', 0);
    }
    ...
    $loginToken = $this->getToken();
    if ($loginToken === null) {
        $this->logger->debug('[TokenService] Failed to exchange token, no login token found in the session');
        throw new TokenExchangeFailedException('Failed to exchange token, no login token found in the session');
    }
```

```php
// user_oidc v8.11.0, lib/Service/TokenService.php:50 und 92-94
private const SESSION_TOKEN_KEY = Application::APP_ID . '-user-token';
public function getToken(...): ?Token {
    $sessionData = $this->session->get(self::SESSION_TOKEN_KEY);
```

Und die Vorbedingung, die **allen drei** Pfaden vorausgeht, in jedem der drei Listener als erste
Prüfung nach dem Typ-Test:

```php
if (!$this->userSession->isLoggedIn()) {
    return;
}
```

Das ist planungsrelevant, weil es eine zweite, bisher unbenannte Messung erzwingt: eine Anfrage unter
AppAPI-Impersonation läuft über `OC::tryAppAPILogin`, also mit einer aufgelösten Nutzersitzung. Ob
`IUserSession::isLoggedIn()` in dieser Lage `true` antwortet, ist **ungemessen**. Zwei Ausgänge, beide
verwertbar: antwortet sie `false`, bricht Weg 0 im OIDC-Modus schon vor der Sitzungsfrage, und die
Diagnose ist eine andere als die in `SUMMARY.md` vermutete; antwortet sie `true`, ist die
Sitzungs-Token-Frage die richtige, und die Fehlermeldung im Nextcloud-Log unterscheidet die beiden
Fälle namentlich. Der Bericht muss diese Unterscheidung treffen, sonst behauptet er eine Ursache, die
er nicht gemessen hat.

**Folge für D-08 (`user_oidc#925`):** Das Issue ist vom **2024-08-22**, offen, neun Kommentare, letzte
Aktivität 2024-10-24, und es ist die **Feature-Anfrage, aus der die heutige Implementierung entstanden
ist** (Maintainer `julien-nc` skizziert dort in Kommentar 5 genau den Ereignisweg, der jetzt im Code
steht). Es ist also nicht "das Issue zur Bruchstelle", sondern die Anfrage, deren Umsetzung eine neue,
darin nicht behandelte Lücke offenlässt: eine ExApp ohne PHP-Anteil. Genau so ist der Entwurf in
`Desktop/openDesk-Anfragen-2026-08-28.md` auch formuliert ("Adding a case that I think this issue does
not yet cover"). Der Bericht muss diese Einordnung mitführen, sonst liest der Kommentar wie eine
Fehlermeldung zu einem erledigten Feature.
[VERIFIED: GitHub-Issue-API `nextcloud/user_oidc#925` samt allen neun Kommentaren, 2026-08-28]

### K6: Das openDesk-Deployment nennt AppAPI an keiner Stelle, repository-weit gemessen

Der Belegtabelle in `Desktop/openDesk-Anfragen-2026-08-28.md` steht die Einschränkung "Vorsichtig
formuliert, weil nur diese Datei geprüft wurde und die projektweite Suche auf opencode.de eine
Anmeldung verlangt". Die Suche über die GitLab-API verlangt sie tatsächlich (`scope=blobs` antwortet
`401 Unauthorized`), das Repository-Archiv aber **nicht**:

```
GET https://gitlab.opencode.de/bmi/opendesk/deployment/opendesk/-/archive/v1.18.0/opendesk-v1.18.0.tar.gz
-> HTTP 200, 2285825 Bytes
```

Ein Griff durch den entpackten Baum:

```
grep -ril "app_api\|appapi\|external.app\|exapp" .    -> keine Treffer
grep -ril "authorization_method\|integration_openproject\|integrationOpenproject" .
  -> ./docs/architecture.md
     ./docs/debugging.md
     ./helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl
```

[VERIFIED: Archiv geladen, entpackt und durchsucht, 2026-08-28]

**Folge:** Die Aussage darf ohne Vorbehalt geführt werden: im Deployment-Projekt `bmi/opendesk/deployment/opendesk`
auf Tag `v1.18.0` kommt AppAPI in keiner Datei vor. Der einzige verbleibende Vorbehalt ist ein anderer
und muss genannt werden: das Nextcloud-**Container-Image** von openDesk
(`bmi/opendesk/components/platform-development/images/opendesk-nextcloud:33.0.7`) wird aus einem
anderen, nicht mitgelesenen Projekt gebaut. `app_api` ist seit Nextcloud 30 eine mitgelieferte
Serverapp; ob das openDesk-Image sie enthält und ob sie eingeschaltet ist, ist aus dem
Deployment-Projekt **nicht** entscheidbar. Das ist die eine echte Rest-Unbekannte von OD-01 und gehört
als Frage 1a auf die ISV-Liste, sauber getrennt von der Kubernetes-Frage.

---

## OD-01: Installierbarkeit aus Quellen

Reihenfolge des Berichts nach D-09 und Erfolgskriterium 1: dieser Abschnitt steht ganz vorn, vor jeder
API-Frage.

### Hürde 1: Der Nextcloud App Store ist in openDesk abgeschaltet

**Quelle:** `bmi/opendesk/deployment/opendesk`, Tag `v1.18.0`,
`helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl`, Zeilen 59 bis 85.
Öffentlich ohne Anmeldung ladbar über den Rohpfad `/-/raw/v1.18.0/...`.

```yaml
  feature:
    apps:
      contacts:
        enabled: false                                        # Zeile 61-62
      cryptpad:
        enabled: {{ .Values.apps.cryptpad.enabled }}
      filesZip:
        enabled: true
      groupfolders:
        enabled: true
      integrationOpenproject:
        enabled: {{ .Values.apps.openproject.enabled }}       # Zeile 69-70
      notifyPush:
        enabled: {{ gt .Values.replicas.nextcloudNotifyPush 0 }}
      sharereview:
        enabled: false
      spreed:
        enabled: false                                        # Zeile 75-76
    adminAudit:
      enabled: {{ .Values.functional.admin.logging.auditLogs.enabled }}   # Zeile 77-78
    appstore:
      enabled: false                                          # Zeile 79-80
    comments:
      enabled: false                                          # Zeile 81-82
    circles:
      enabled: false                                          # Zeile 83-84
    systemtags:
      enabled: true
```

[VERIFIED: Datei am Tag `v1.18.0` geladen und ausgezählt, 2026-08-28]

**Antwort:** belegt, nicht offen. Die Ein-Klick-Erzählung dieses Produkts existiert in einer
openDesk-Installation nicht. Installation dort ist eine Betreiberhandlung im Helmfile.

Drei Nebenbefunde aus demselben Block, die in den Bericht gehören:

- `spreed: enabled: false` und `contacts: enabled: false`: zwei der neun Werkzeugfamilien sind in
  openDesk dunkel. Das ist die Grundlage für die Pflichtfrage aus OD-03 und trifft unabhängig vom
  Ausgang des OpenProject-Teils zu.
- `comments: enabled: false` und `circles: enabled: false`: zwei weitere Kernfunktionen aus. Sie
  betreffen heute kein Werkzeug dieser App, wohl aber jede künftige Kommentarfunktion; der Bericht
  sollte sie beiläufig nennen, weil OD-04 im Entwurf Kommentare vorsieht.
- `adminAudit: enabled: {{ ... }}`: openDesk hat schon einen Schalter für Protokollierung. Für
  Phase 18 und 19 ist das ein günstiger Befund und gehört genannt, aber nicht gemessen.

### Hürde 2: Kein Kubernetes-Deploy-Daemon auf dem openDesk-Stand, einer eine Hauptversion darüber

Siehe K1. Zusammengefasst als Berichtszeile:

| Frage | Antwort | Quelle |
|-------|---------|--------|
| Existiert in openDesk ein AppAPI-Deploy-Daemon? | Nein, AppAPI kommt im Deployment-Projekt an keiner Stelle vor | Archivgriff, K6 |
| Kann AppAPI überhaupt Kubernetes? | Ab `app_api` 34 ja, mit `kubernetes-install` über HaRP und vier Freigabearten; auf `app_api` 33, dem openDesk-Stand, nein | `RegisterDaemon.php:37` beider Zweige, `KubernetesActions.php:37`, K1 |
| Welcher Daemon-Typ bliebe auf dem heutigen openDesk-Stand? | `manual-install`, und zwar in zwei Varianten: `manual_install` (Host `host.docker.internal`, kein HaRP) und `manual_install_harp` ("HaRP Manual Install", Host `appapi-harp:8780`) | `app_api` `src/constants/daemonTemplates.js`, Vorlagen an Zeile 92 und 195, in `stable33` und `stable34` identisch |
| Ist `manual-install` produktionstauglich? | Nicht entschieden. Die aktuelle Admin-Dokumentation stellt es neutral als Alternative dar und sagt **nicht** mehr, es sei nur für Entwicklung | `docs.nextcloud.com/server/stable/admin_manual/exapps_management/DeployConfigurations.html`, abgerufen 2026-08-28 |

Zur letzten Zeile ausdrücklich: die in `research/STACK.md` A.6 und `research/PITFALLS.md` Pitfall 2
zitierte Formulierung "`manual-install` ist laut Nextcloud-Doku ausdrücklich für Entwicklung oder
Spezialfälle" ließ sich auf der heutigen Seite **nicht** wiederfinden. Der Bericht darf diese
Formulierung deshalb nicht als Zitat führen. Was er führen darf: die aufgezählten Werte der
`occ`-Hilfe, weil die im Quellcode stehen. [CITED: docs.nextcloud.com Deploy Configurations, Abruf
2026-08-28; die frühere Aussage ist auf der Seite in dieser Form nicht mehr vorhanden]

Ein Zusatzbefund derselben Seite ist verwertbar und stützt K1: sie erwähnt "For the Kubernetes deploy
daemon, container log rotation is handled by the kubelet". Die Dokumentation kennt den Daemon also
schon.

### Hürde 3: Was der Pin auf Nextcloud 33.0.7 für unsere 34.0.3-Nachweise bedeutet

**Die Versionspins, wörtlich aus `helmfile/environments/default/images.yaml.gotmpl` an `v1.18.0`:**

```yaml
  nextcloud:                                                          # Zeile 344
    registry: "registry.opencode.de"
    repository: "bmi/opendesk/components/platform-development/images/opendesk-nextcloud"
    tag: "33.0.7@sha256:16828dac1e8467cadc0760d256a2d7e1686d3cd9e31f24b6529e9ede849f823c"   # Zeile 351

  nubusKeycloak:                                                      # Zeile 404
    repository: "bmi/opendesk/components/supplier/univention/images-mirror/keycloak"
    tag: "26.7.0@sha256:ba60a3a6c5e9833d9e94bb4e6c836d7efe07a5169dc82de89d863960ba22f8a5"   # Zeile 413

  openproject:                                                        # Zeile 716
    # upstreamRepository: "openproject/open_desk"
    repository: "bmi/opendesk/components/supplier/openproject/images-mirror/open_desk"
    tag: "17.7.2@sha256:9c2181c8fcf4de44e18aa502473d0034c2c8ce714db8a1d1d1ee8530244d66cc"   # Zeile 725
```

[VERIFIED: Datei am Tag `v1.18.0` geladen, 2026-08-28]

Nebenbefund mit praktischem Wert: das OpenProject-Image von openDesk ist ein Spiegel von
**`openproject/open_desk`**, nicht von `openproject/openproject`. Das Original liegt öffentlich auf
Docker Hub, `openproject/open_desk:17.7.2` existiert (419 MB, gepusht 2026-08-13).
[VERIFIED: Docker-Hub-Tag-API für `openproject/open_desk`, 2026-08-28]

**Die Aussage, die OD-01 wörtlich verlangt.** Sie hat drei Teile, und alle drei sind belegbar:

1. `appinfo/info.xml` dieser App deklariert `<nextcloud min-version="32" max-version="34"/>` (Zeile
   235). Nextcloud 33 liegt in der erklärten Spanne. Der Pin macht die App also nicht
   *unzulässig*.
   [VERIFIED: eigenes `appinfo/info.xml`, Release 0.1.11, 2026-08-28]
2. Sämtliche Ein-Klick- und Erreichbarkeitsnachweise dieses Projekts stehen auf 34.0.x
   (`docs/spike-dav.md`: 34.0.2 Build 34.0.2.1; `docs/spike-mail.md`: 34.0.3 Build 34.0.3.2;
   `compose.exapp.yml` pinnt `nextcloud:34.0.3-apache`). In einem Projekt, das seine Nachweise
   wörtlich nimmt, ist ein Nachweis auf der falschen Hauptversion kein Nachweis. Die Zielumgebung ist
   damit *ungetestet*, nicht *unzulässig*.
3. Der Unterschied ist nicht nur "älter als getestet". Auf 33 fehlt die Funktion, die den einzigen
   plausiblen Kubernetes-Installationsweg trägt (K1). Der Versionspin und die Kubernetes-Hürde sind
   dieselbe Hürde, und die Lösung beider ist derselbe Schritt: openDesk auf Nextcloud 34 oder höher.

**Das macht diese Phase daraus:** Nextcloud **33.0.7** ist die Messumgebung, nicht 34.0.3. Damit
liefert Stufe A der Messung als kostenlose Zugabe die Aussage, ob die Ein-Klick-Installation und der
AppAPI-Erreichbarkeitsweg auf 33.0.7 überhaupt halten. Das ist der Nachweis, der heute auf der falschen
Hauptversion steht, und er kostet in dieser Phase fast nichts extra, weil die Instanz ohnehin steht.
Empfehlung: als eigene Behauptung führen (Vorschlag: **S0**), damit sie im Bericht sichtbar ist und
nicht als Nebenprodukt untergeht.

### Was von OD-01 offen bleibt und in den Bericht als ISV-Frage gehört

| Offener Punkt | Warum aus Quellen nicht entscheidbar |
|---------------|---------------------------------------|
| Ist `app_api` im openDesk-Nextcloud-Image enthalten und eingeschaltet? | Das Image wird aus einem anderen, nicht öffentlich mitgelesenen Projekt gebaut (K6) |
| In welchem Modus (`oauth2` oder `oidc`) läuft `integration_openproject` in openDesk? | Die Einrichtung macht der Job `opendesk-openproject-bootstrap`, dessen Logik in einem eigenen Image liegt. Im Deployment-Projekt stehen nur seine Eingaben: OpenProject-API-Admin und Nextcloud-Admin samt Passwörtern (`helmfile/apps/opendesk-openproject-bootstrap/values.yaml.gotmpl`, Abschnitt `config`). Das legt den Zwei-Wege-OAuth2-Weg nahe, weil genau dafür die Routen `POST /nc-oauth` und `POST /setup` existieren, ist aber **Indiz und nicht Beleg** |
| Würde ein Betreiber eine Dritt-ExApp neben der Suite akzeptieren, und wer entscheidet | Betriebs- und Verfahrensfrage, öffentlich nicht dokumentiert |
| Wann geht openDesk auf Nextcloud 34 oder höher | Terminfrage an ZenDiS, aus K1 neu entstanden |

---

## OD-02 Weg 0: über `integration_openproject`

### Die OCS-Fläche, vollständig und mit Zeilennummern

Aus `appinfo/routes.php` am Tag `v3.1.1` (die neueste stabile Fassung für Nextcloud 33, siehe
Versionsmatrix unten). Präfix aller Zeilen: `/ocs/v2.php/apps/integration_openproject`. Der Block
`'ocs' => [` beginnt in Zeile 37 und endet in Zeile 56.

| Zeile | Verb | Pfad | Controller-Methode | Vorprüfung? | Für die Messung |
|-------|------|------|--------------------|-------------|------------------|
| 38 | GET | `/fileinfo/{fileId}` | `files#getFileInfo` | n/a | nicht Teil der API-v1-Fläche |
| 39 | POST | `/filesinfo` | `files#getFilesInfo` | n/a | nicht Teil der API-v1-Fläche |
| 41 | GET | `/api/v1/notifications` | `getNotifications` | ja | Kandidat für S2 und S3 |
| 42 | DELETE | `/api/v1/work-packages/{id}/notifications` | `markNotificationAsRead` | ja | **schreibend, nicht auslösen** |
| 43 | GET | `/api/v1/url` | `getOpenProjectUrl` | **nein** (K3) | **S1**, Erreichbarkeit und CSRF-Pfad |
| 44 | GET | `/api/v1/avatar` | `getOpenProjectAvatar` | nein | die einzige Methode mit `#[NoCsrfRequired]` |
| 45 | GET | `/api/v1/work-packages` | `getSearchedWorkPackages` | ja | **S3** und **S6** |
| 46 | POST | `/api/v1/work-packages` | `linkWorkPackageToFile` | ja | **schreibend, nicht auslösen** |
| 47 | GET | `/api/v1/work-packages/{id}/file-links` | `getWorkPackageFileLinks` | ja | in `ARCHITECTURE.md` nicht aufgeführt; für OD-04 der Kern des Unterscheidungsmerkmals |
| 48 | GET | `/api/v1/statuses/{id}` | `getOpenProjectWorkPackageStatus` | ja | |
| 49 | GET | `/api/v1/types/{id}` | `getOpenProjectWorkPackageType` | ja | |
| 50 | DELETE | `/api/v1/file-links/{id}` | `deleteFileLink` | ja | **destruktiv, nicht auslösen** |
| 51 | GET | `/api/v1/projects` | `getAvailableOpenProjectProjects` | ja | Kandidat für S2 und S3 |
| 52 | POST | `/api/v1/projects/{id}/work-packages/form` | `getOpenProjectWorkPackageForm` | ja | POST, aber fachlich lesend (Formular). Nicht auslösen, um die Regel nicht aufzuweichen |
| 53 | GET | `/api/v1/projects/{id}/available-assignees` | `getAvailableAssigneesOfAProject` | ja | |
| 54 | POST | `/api/v1/create/work-packages` | `createWorkPackage` | ja | **schreibend, nicht auslösen** |
| 55 | GET | `/api/v1/configuration` | `getOpenProjectConfiguration` | ja | **S2**, weil argumentfrei und lesend |

[VERIFIED: `appinfo/routes.php` an `v3.1.1` gelesen, Zeilen nachgezählt, 2026-08-28]

**15 Routen unter `/api/{apiVersion}` plus 2 Dateirouten, 17 OCS-Routen insgesamt.** Die Zahl 15 aus
`ARCHITECTURE.md` ist damit richtig, aber ihre Tabelle listet nur 11 davon und lässt
`markNotificationAsRead`, `avatar`, `work-packages/{id}/file-links` und `work-packages/form` weg. Die
in `ARCHITECTURE.md` und im Forumsentwurf genannten Lücken bleiben bestätigt: **keine Route für ein
einzelnes Arbeitspaket per Id, keine für Kommentare, keine für "meine Arbeit"**. Der Befund, der die
Lücken teilweise ausgleicht: `file-links` per Arbeitspaket **gibt es**, und das ist genau die Kette
Arbeitspaket zu Datei, die `research/FEATURES.md` als Unterscheidungsmerkmal führt.

### CSRF und Impersonation: was die Messung tatsächlich zu klären hat

`OpenProjectAPIController extends OCSController`, und exakt eine Methode trägt `#[NoCsrfRequired]`
(`getOpenProjectAvatar`, Zeile 79-80). Alle übrigen tragen nur `#[NoAdminRequired]`.
[VERIFIED: Attributzählung in der Datei an `v3.1.1`, 2026-08-28]

Der Weg dorthin ist in diesem Repository bereits gebaut und einmal live bewiesen: `OCS_HEADERS` in
`src/mcp_connector/nextcloud/clients/ocs.py:40-43` setzt `OCS-APIRequest: true` auf **jeder**
OCS-Anfrage (D-18), und `docs/spike-mail.md` hat mit demselben Mechanismus die OCS-Route von Nextcloud
Mail erreicht. Neu ist nur die App. Damit ist S1 keine offene Machbarkeitsfrage, sondern eine
Bestätigungsmessung, und das Entscheidungskriterium kann wie bei `spike-mail.md` **vor** der ersten
Messung festgeschrieben werden.

**Empfehlung, aus `docs/spike-mail.md` übernommen:** Das Kriterium ist die **Antwortform**, nicht der
Statuscode.

| Beobachtung | Bedeutung |
|-------------|-----------|
| OCS-Umschlag als JSON, beliebiger `statuscode` (200, 401, 400, 404) | erreicht: nur App-Code erzeugt diesen Umschlag, die CSRF- und Impersonationskette hat gehalten |
| HTML-Körper (beginnt mit `<`) | nicht erreicht: das ist die Anmeldeseite, die `ocs._json_payload` heute schon namentlich benennt |
| 3xx mit `Location`, die `/login` enthält | nicht erreicht: die Authentifizierung ist gescheitert |

Ein Spike, der hier auf 200 prüft, meldet bei einem Konto ohne verbundenes OpenProject fälschlich
"unerreichbar", denn 401 aus `validatePreRequestConditions()` ist antwortender App-Code. Genau dieser
Fehler ist in v1.2 bei Mail vermieden worden und muss hier wieder vermieden werden.

### Konfiguration von `integration_openproject`, skriptbar

Die App bringt **kein** eigenes `occ`-Kommando (`lib/Command/` existiert nicht).
[VERIFIED: Verzeichnisbaum an `v3.1.1` über die GitHub-Tree-API, 2026-08-28]

Die zulässigen Admin-Schlüssel stehen wörtlich in `lib/Service/SettingsService.php:19-38`:

```php
private const GENERAL_ADMIN_SETTINGS = [
    'openproject_instance_url' => 'string',
    'authorization_method' => ['oauth2', 'oidc'],        // Application::AUTH_METHOD_*
    'default_enable_navigation' => 'boolean',
    'default_enable_unified_search' => 'boolean',
    'setup_project_folder' => 'boolean',
    'setup_app_password' => 'boolean',
];
private const OAUTH_ADMIN_SETTINGS = [
    'openproject_client_id' => 'string',
    'openproject_client_secret' => 'string',
];
private const OIDC_ADMIN_SETTINGS = [
    'sso_provider_type' => ['nextcloud_hub', 'external'],
    'oidc_provider' => 'string',
    'targeted_audience_client_id' => 'string',
    'token_exchange' => 'boolean',
];
```

[VERIFIED: `lib/Service/SettingsService.php` an `v3.1.1`, 2026-08-28]

Daraus zwei gangbare Einrichtungswege für die Messumgebung, in dieser Reihenfolge zu versuchen:

**Weg A, der dokumentierte Zwei-Wege-Weg (empfohlen, weil er das echte Verhalten erzeugt).**
In OpenProject unter *Administration, Files, External file storages* eine Nextcloud-Ablage anlegen; die
Einrichtung tauscht beidseitig OAuth-Anwendungen aus und ruft dabei die App-Routen
`POST /nc-oauth` (`config#autoOauthCreation`, `appinfo/routes.php:18`) und
`POST /setup` (`config#setUpIntegration`, Zeile 30) auf. Das ist derselbe Weg, den der
openDesk-Bootstrap-Job geht (er hält genau die zwei Zugangsdatenpaare, die er dafür braucht), also der
Weg mit der höchsten Übertragbarkeit auf openDesk.

**Weg B, der Handweg für die reine Erreichbarkeitsmessung.**
`occ config:app:set integration_openproject openproject_instance_url --value=...`, dazu
`authorization_method`, `openproject_client_id`, `openproject_client_secret`. Danach muss jeder Nutzer
den persönlichen OAuth-Fluss der App einmal durchlaufen (Route
`GET /op-oauth-url` erzeugt die Adresse samt State und PKCE,
`GET /oauth-redirect` nimmt den Code an; Zeilen 35 und 15 in `appinfo/routes.php`). Ohne diesen
Durchlauf hat kein Nutzer ein `token`, und S1 wäre der einzige messbare Punkt.

Beachten: `POST /op-oauth-url` heißt im Quellcode `getOpenProjectOauthURLWithStateAndPKCE`. Die App
selbst benutzt also PKCE gegen OpenProject, was K2 unabhängig stützt.

### Die per-Nutzer-Zustandsschlüssel, die S4 braucht

`OpenProjectAPIService` schreibt und liest ausschließlich über `IConfig::{get,set}UserValue` mit der
App-Id `integration_openproject`. Die Schlüssel, mit Zeilen:

| Schlüssel | Wo geschrieben | Bedeutung |
|-----------|----------------|-----------|
| `token` | `svc.php:586`, `1715` | Access-Token des Nutzers |
| `refresh_token` | `svc.php:604` | Refresh-Token (nur im `oauth2`-Modus) |
| `token_expires_at` | `svc.php:601`, `1716` | Unix-Zeit des Ablaufs |
| `user_id`, `user_name` | `svc.php:1822-1823` | zwischengespeicherte OpenProject-Identität |

Und die Ablaufprüfung, die den Messweg von S4 bestimmt:

```php
// svc.php:1726-1733
public function isAccessTokenExpired(string $userId): bool {
    $expiresAt = $this->config->getUserValue($userId, Application::APP_ID, 'token_expires_at', 0);
    // Consider token expired 60 seconds early
    // to avoid race conditions caused by various factors
    $tokenExpirySafetyMargin = 60;
    $expiresAt = (int)$expiresAt - $tokenExpirySafetyMargin;
    return time() > $expiresAt;
}
```

**Planungsanweisung:** Der künstliche Ablauf für S4 muss `token_expires_at` auf einen Wert setzen, der
mehr als 60 Sekunden in der Vergangenheit liegt. `0` ist der sichere Wert und zugleich der Vorgabewert
der Methode, also unverdächtig. Der Befehl:

```bash
occ user:setting <user> integration_openproject token_expires_at 0
```

### Der entscheidende Quellcodebefund für S4, wörtlich

```php
// svc.php:1740-1789 (gekürzt, Kommentare original)
public function getAccessToken(?string $userId): string {
    ...
    $token = $this->config->getUserValue($userId, Application::APP_ID, 'token', '');
    $authMethod = $this->config->getAppValue(Application::APP_ID, 'authorization_method');

    if ($token && !$this->isAccessTokenExpired($userId)) { ... return $token; }

    // For OAuth2 setup, only try to refresh the expired token.        // Zeile 1764
    // Token exchange needs to be initiated from the UI.               // Zeile 1765
    if ($authMethod === Application::AUTH_METHOD_OAUTH && $token) {
        $refreshToken = $this->config->getUserValue($userId, Application::APP_ID, 'refresh_token');
        $clientID     = $this->config->getAppValue(Application::APP_ID, 'openproject_client_id');
        $clientSecret = $this->config->getAppValue(Application::APP_ID, 'openproject_client_secret');
        $result = $this->requestOAuthAccessToken($userId, $openprojectUrl, [
            'client_id' => $clientID, 'client_secret' => $clientSecret,
            'grant_type' => 'refresh_token', 'refresh_token' => $refreshToken,
        ]);
        if (isset($result['error'])) { ...; return ''; }
        return $result['access_token'];
    } elseif ($authMethod === Application::AUTH_METHOD_OIDC) {
        $token = $this->getOIDCToken($userId);
        ...
    }
    return '';
}
```

Die zwei Kommentarzeilen 1764 und 1765 sind der stärkste Quellenbeleg für die ganze Weg-0-Frage: im
`oauth2`-Modus erneuert die App serverseitig, im `oidc`-Modus sagt sie selbst, dass der Austausch von
der Oberfläche her angestoßen werden muss. Genau diese Asymmetrie ist der Unterschied zwischen S4 und
S5, und sie steht in einem Kommentar der Upstream-Entwickler.
[VERIFIED: `lib/Service/OpenProjectAPIService.php` an `v3.1.1`, Zeilen 1740 bis 1792, 2026-08-28]

### S0 bis S6: Messwege mit Erwartungswert und Gegenprobe

Die Behauptungen S1 bis S6 kommen aus `ARCHITECTURE.md` A.6; S0 ist aus OD-01 Hürde 3 neu, S2 ist nach
K3 umformuliert, S5 ist nach K5 aufgeteilt.

| # | Behauptung | Messweg (Aufruf und Vorbedingung) | Erwartung aus der Quelle | Gegenprobe, ohne die der Messwert nichts beweist |
|---|-----------|-----------------------------------|--------------------------|--------------------------------------------------|
| **S0** | Diese ExApp installiert und antwortet auf Nextcloud **33.0.7** genauso wie auf 34.0.3 | Stufe A hochfahren, `bootstrap_exapp.sh` unverändert laufen lassen, danach `occ app_api:app:list` und ein Werkzeugaufruf | offen, MEDIUM: `info.xml` erlaubt 32 bis 34 | ein Werkzeugaufruf mit falschem `APP_SECRET` antwortet 401 (Muster aus `spike-dav.md`) |
| **S1** | `GET /api/v1/url` antwortet unter reiner AppAPI-Impersonation mit OCS-JSON und der OpenProject-Adresse | ein Aufruf mit `OCS-APIRequest: true` und `AUTHORIZATION-APP-API`, ohne App-Passwort im Prozess | 200 mit der Adresse, weil die Methode nichts prüft (K3) | derselbe Aufruf mit 64 Null-Zeichen als `APP_SECRET` antwortet 401; und: HTML-Körper wäre die Anmeldeseite, also nicht erreicht |
| **S2** | Die Berechtigung hängt am Nutzer, nicht an der App | `GET /api/v1/configuration` als Konto **ohne** verbundenes OpenProject | OCS-Umschlag mit `statuscode` 401 aus `validatePreRequestConditions()` | derselbe Aufruf als verbundenes Konto liefert Daten. Ohne diesen zweiten Lauf ist die 401 auch mit einer kaputten Einrichtung erklärbar |
| **S3** | Konto A sieht in `/api/v1/work-packages?searchQuery=...` kein Arbeitspaket, das nur Konto B sehen darf | ein privates Projekt in OpenProject, Mitglied nur B, ein Arbeitspaket darin mit eindeutigem Suchwort; dieselbe Suche als A und als B | A findet nichts, B findet eines | dasselbe Suchwort als B **muss** treffen. Ein Suchwort, das keiner findet, beweist nur einen Tippfehler |
| **S4** | Nach künstlichem Ablauf antwortet der nächste Aufruf wieder mit Daten, ohne Browsersitzung | `occ user:setting <u> integration_openproject token_expires_at 0`, dann derselbe OCS-Aufruf; danach `occ user:setting <u> integration_openproject token_expires_at` erneut lesen | Daten, und ein **neuer** `token_expires_at` in der Zukunft. Quelle: `svc.php:1766-1782` | `refresh_token` vorher auf einen Unsinnswert setzen: derselbe Aufruf muss dann 401 liefern. Damit ist bewiesen, dass die Erneuerung wirklich lief und nicht ein zwischengespeichertes Token weiterhalf |
| **S5a** | Im Modus `oidc` mit externem Anbieter und `token_exchange = false` bricht derselbe Aufruf nach Ablauf | Stufe B, `sso_provider_type = external`, `token_exchange = false`, dann wie S4 | 401, und im Nextcloud-Log die Ausnahme `GetExternalTokenFailedException` bzw. `[TokenService] Get token from the session` ohne Treffer | Derselbe Aufruf **mit** einer echten Browsersitzung des Nutzers (Cookie mitschicken) muss Daten liefern. Ohne diese Gegenprobe ist die 401 auch eine kaputte Keycloak-Kopplung |
| **S5b** | Dasselbe mit `token_exchange = true` bricht mit einer **anderen** Meldung | `token_exchange = true`, `targeted_audience_client_id` gesetzt, `store_login_token` einmal aus und einmal an | aus: `'Failed to exchange token, storing the login token is disabled...'`; an, ohne Sitzung: `'Failed to exchange token, no login token found in the session'` (`TokenService.php:318` und `328`) | dieselbe Anfrage aus dem Browser des angemeldeten Nutzers |
| **S5c** | `IUserSession::isLoggedIn()` unter AppAPI-Impersonation | ergibt sich aus S5a: bricht es **vor** der Sitzungsprüfung, erscheint **keine** der beiden Meldungen im Log, weil alle drei Listener vorher `return` machen | ungemessen, beide Ausgänge verwertbar (K5) | die Log-Zeile `[ExternalTokenRequestedListener] received request` erscheint oder erscheint nicht. Das ist die trennscharfe Beobachtung |
| **S6** | Eine Antwort von `/api/v1/work-packages` trägt in kompakter Form die Felder, aus denen ein späteres Werkzeug projiziert, unter X Bytes | dieselbe Antwort wie S3, minifiziert, Bytes zählen und Felder auflisten | offen. Vergleichswert von `community.openproject.org`: ein Arbeitspaket über API v3 roh 3691 Bytes, mit `select` 216 Bytes | die rohe API-v3-Antwort derselben Instanz gegenrechnen, damit der Wert eine Bezugsgröße hat und nicht nur eine Zahl ist |

**Kontrollmessung aus `ARCHITECTURE.md`, zwei Minuten, eigener Erkenntniswert:** ein `curl` aus dem
laufenden ExApp-Container gegen `http://<openproject>/api/v3/work_packages`. Antwortet er, ist Egress
vorhanden und Weg 1 bleibt als Rückfall offen; antwortet er nicht, ist Weg 0 nicht nur der schönere,
sondern der einzige. Diese Messung ist im lokalen Docker-Netz **erwartbar erfolgreich** und beweist
damit über openDesk nichts. Der Bericht muss das sagen, sonst liest ein "Egress vorhanden" wie eine
Aussage über eine Behördeninstallation.

### Versionsmatrix für Stufe A

| Bauteil | Fassung | Belegt |
|---------|---------|--------|
| Nextcloud | **33.0.7** (`nextcloud:33.0.7-apache`) | Tag existiert auf Docker Hub, gemessen 2026-08-28 |
| `integration_openproject` | **3.1.1**, veröffentlicht 2026-07-13, Plattformspanne `>=33.0.0 <35.0.0` | App-Store-API für Plattform 33.0.0. Die einzige Alternative in der Spanne ist 3.1.0 (2026-06-18) und 3.0.0 (nur `<34.0.0`); `3.2.0-20260820-nightly` ist ein Nightly und fällt unter die Kein-`latest`-Regel |
| `app_api` | die im Server mitgelieferte Fassung, erwartet **33.0.0** | nicht im App Store für Plattform 33 gelistet, weil mitgeliefert. Die Fassung ist mit `occ app:list` aus der laufenden Instanz zu lesen und in den Berichtskopf zu schreiben |
| OpenProject | **17.7.2** (`openproject/openproject:17.7.2`, oder für maximale Nähe `openproject/open_desk:17.7.2`) | beide Tags auf Docker Hub gemessen 2026-08-28 |

[VERIFIED: `https://apps.nextcloud.com/api/v1/platform/33.0.0/apps.json`, Docker-Hub-Tag-APIs, 2026-08-28]

---

## OD-02 Weg 1: eigener OAuth-Autorisierungscode gegen OpenProject

### Die Endpunkte und die Metadatenlücke, live nachgemessen

Am 2026-08-28 gegen `community.openproject.org` gemessen, unabhängig von der Messung in
`research/STACK.md` A.1 und mit identischem Ergebnis:

```
GET /.well-known/oauth-authorization-server
{"issuer":"https://community.openproject.org",
 "authorization_endpoint":"https://community.openproject.org/oauth/authorize",
 "token_endpoint":"https://community.openproject.org/oauth/token",
 "introspection_endpoint":"https://community.openproject.org/oauth/introspect",
 "scopes_supported":["api_v3","scim_v2","mcp"," bcf_v2_1"],
 "response_types_supported":["code"],
 "grant_types_supported":["authorization_code","client_credentials","refresh_token"],
 "service_documentation":"https://www.openproject.org/docs/system-admin-guide/authentication/oauth-applications/?go_to_locale=en"}

GET /.well-known/oauth-protected-resource
{"resource":"https://community.openproject.org","resource_name":"OpenProject Community",
 "authorization_servers":["https://id.openproject.com/realms/master","https://community.openproject.org"],
 "scopes_supported":["bcf_v2_1","api_v3","scim_v2","mcp"],"bearer_methods_supported":["header"],
 "resource_documentation":"https://www.openproject.org/docs/api/?go_to_locale=en"}
```

[VERIFIED: eigene Abrufe, 2026-08-28. Die Reihenfolge der `scopes_supported` weicht zwischen den zwei
Dokumenten ab, das ist ohne Bedeutung]

Kein `registration_endpoint` (keine dynamische Client-Registrierung), kein
`code_challenge_methods_supported`. Nach K2 ist das Zweite ein **Metadatenmangel**, kein
Fähigkeitsmangel: `force_pkce` steht im Code. Das ist ein guter, konkreter Beitrag für den
Forums- oder Community-Kanal und gehört als Nebenbefund in den Bericht.

**Zusätzlicher Beleg gegen die Dokumentation:** Die API-Einführung nennt wörtlich
"Authorization code flow with PKCE, recommended for clients unable to keep the client_secret
confidential". Die Admin-Seite zu OAuth-Anwendungen nennt PKCE nicht und sagt zur Lebensdauer
"Please note that your Bearer token will expire after two hours (default)".
[CITED: openproject.org/docs/api/introduction/ und
openproject.org/docs/system-admin-guide/authentication/oauth-applications/, Abruf 2026-08-28]

### OAuth-Anwendung in OpenProject 17.7.x anlegen

**UI-Weg (der dokumentierte):** *Administration, Authentication, OAuth applications*. Felder: Name,
Redirect URL, Scopes, Häkchen "Confidential", optionales Feld "Client Credentials User".
[CITED: openproject.org/docs/system-admin-guide/authentication/oauth-applications/, Abruf 2026-08-28]

Drei Planungsanweisungen dazu:

1. **Häkchen "Confidential" nicht setzen.** Nur ein nicht vertraulicher Client fällt unter
   `force_pkce`, und genau dessen Verhalten soll gemessen werden. Ein vertraulicher Client könnte PKCE
   weglassen, und die Messung würde die falsche Frage beantworten.
2. **Feld "Client Credentials User" leer lassen.** Das ist Pitfall 1 in Feldform. `client_credentials`
   steht in `grant_types_supported`; dass es dasteht, ist keine Einladung. Der Bericht sollte in einem
   Satz festhalten, dass dieses Feld leer geblieben ist, weil ein Prüfer genau danach fragt.
3. **Client-Secret sofort kopieren** (`hash_application_secrets`, K2).

**Seeding-Weg:** In `opf/openproject` an `v17.7.2` existiert **kein** `app/models/doorkeeper/`
Verzeichnis; die OAuth-Client-Modelle der eigenen Fläche heißen `app/models/oauth_client.rb` und
`oauth_client_token.rb` und betreffen OpenProject **als Client** gegen fremde Dienste, nicht als
Server. Ein dokumentierter Umgebungsvariablen-Weg zum Seeden einer OAuth-**Anwendung** ließ sich nicht
finden. Der Handweg über die Oberfläche ist also der Weg; ein `rails runner` gegen
`Doorkeeper::Application` wäre möglich, ist aber ungeprüft und würde eine Behauptung über fremden Code
ohne Beleg bedeuten.
[VERIFIED: GitHub-Contents-API für `app/models` und `app/models/doorkeeper` an `v17.7.2`, 2026-08-28. Der
`rails runner`-Weg ist ASSUMED und in dieser Phase nicht zu benutzen]

### Die vier Messwerte, die D-04 wörtlich verlangt

| Messwert | Wie messen | Erwartung aus der Quelle | Gegenprobe |
|----------|-----------|--------------------------|------------|
| Nimmt `/oauth/authorize` PKCE an | Autorisierungsanfrage mit `code_challenge` und `code_challenge_method=S256`, Consent im Browser, Code einlösen | 200 und ein Token. `force_pkce` (`doorkeeper.rb:90`) | **derselbe öffentliche Client ohne `code_challenge`**: muss abgewiesen werden. Das ist der eigentliche Befund, und er ist der Gegenprobe-Lauf, nicht der Hauptlauf |
| `expires_in` | Feld der Token-Antwort | `7200`, aus `access_token_expires_in 2.hours` (`doorkeeper.rb:64`) | die Admin-Dokumentation sagt dasselbe ("expire after two hours (default)"): stimmen Code, Doku und Messwert überein, ist der Wert belastbar |
| Trägt die Erneuerung ohne Browsersitzung | `grant_type=refresh_token` an `/oauth/token`, mit `Content-Type: application/x-www-form-urlencoded`, **ohne** Cookie | neues Token samt neuem `refresh_token`, aus `use_refresh_token` (`doorkeeper.rb:115`) | derselbe Aufruf mit einem verbrauchten oder erfundenen `refresh_token` muss fehlschlagen. Und: der Lauf muss ohne jeden Cookie-Speicher stattfinden, sonst beweist er nichts über "ohne Browsersitzung" |
| Zwei-Konten-Negativbeweis (D-05) | `GET /api/v3/work_packages/<id>` mit dem Token von B auf ein Arbeitspaket, das nur A sehen darf | **404** mit `urn:openproject-org:api:v3:errors:NotFound`, nicht 403 | derselbe Aufruf mit dem Token von A muss 200 liefern. Ohne diesen Lauf ist die 404 auch eine falsche Id |

Zur letzten Zeile: das 404-Verhalten ist bereits gemessen, nicht angenommen. Am 2026-08-28 gegen
`community.openproject.org`, unauthentifiziert:

```
GET /api/v3/work_packages/24971      -> HTTP 200   (öffentlich sichtbar)
GET /api/v3/work_packages/999999999  -> HTTP 404   {"_type":"Error",
  "errorIdentifier":"urn:openproject-org:api:v3:errors:NotFound",
  "message":"The work package you are looking for cannot be found or has been deleted."}
GET /api/v3/work_packages/1          -> HTTP 404   dieselbe Antwort, Byte für Byte
```

Arbeitspaket 1 existiert, ist für den Anfragenden aber nicht sichtbar, und OpenProject antwortet
**identisch** zu einer nicht existierenden Id. OpenProject verrät die Existenz also nicht. Das ist
genau die Eigenschaft, die `docs/spike-dav.md` für Nextcloud-Dateien mit "404, never 200" belegt hat,
und der Bericht kann die beiden Negativbeweise damit in derselben Sprache führen.
[VERIFIED: eigene drei Abrufe, 2026-08-28]

### Nutzerkonten in OpenProject anlegen, für beide Wege

Der Zwei-Konten-Negativbeweis braucht auf beiden Wegen zwei OpenProject-Nutzer und ein privates
Projekt. Die API kann es: `POST /api/v3/users` ist vorhanden, "Only administrators and users with
`manage_user` global permission are allowed to do so", Status `active` verlangt ein Passwort, Antwort
201. `GET /api/v3/users` listet mit derselben Berechtigung.
[CITED: openproject.org/docs/api/endpoints/users/, Abruf 2026-08-28]

Wichtig für die Ehrlichkeit des Berichts: der Admin-Zugang, mit dem diese beiden Nutzer angelegt
werden, ist **Aufbau**, nicht Messung. Derselbe Satz steht in `docs/spike-dav.md` über die Deck-Boards.
Der Bericht muss ihn wiederholen, sonst liest ein Prüfer den Admin-Zugang als Teil der gemessenen
Kette.

---

## S5 und der OIDC-Bruch: der minimale lokale Aufbau

### Was Stufe B mindestens braucht

| Bauteil | Fassung | Warum genau diese |
|---------|---------|-------------------|
| Keycloak | `quay.io/keycloak/keycloak:26.7.0` | openDesk 1.18.0 spiegelt Nubus-Keycloak `26.7.0` (`images.yaml.gotmpl:413`). Tag existiert auf quay.io, gemessen 2026-08-28 |
| `user_oidc` | **8.11.0**, veröffentlicht 2026-08-24, Spanne `>=29.0.0 <36.0.0` | neueste stabile Fassung, deckt Nextcloud 33. `integration_openproject` verlangt mindestens `7.2.0` (`Application.php:70`, `MIN_SUPPORTED_USER_OIDC_APP_VERSION`) |
| Realm plus zwei Clients | selbst gebaut | einer für Nextcloud (Rolle von `opendesk-nextcloud`), einer als Zielgruppe für OpenProject (Rolle von `opendesk-openproject`) |

Anmerkung zur Recherchequelle: `research/STACK.md` A.3 nennt `user_oidc` "8.12.0-dev". Im App Store ist
für Plattform 33 die höchste Fassung **8.11.0**; ein Tag `v8.12.0` existiert im Repository nicht. Für
die Messumgebung ist 8.11.0 die richtige Wahl, und der Bericht sollte die Fassung aus `occ app:list`
lesen, nicht aus einer Recherche.
[VERIFIED: App-Store-API für Plattform 33.0.0 und GitHub-Tag-Liste `nextcloud/user_oidc`, 2026-08-28]

### Der Anbieter, skriptbar statt geklickt

`user_oidc` bringt drei `occ`-Kommandos: `user_oidc:provider` (Upsert), `user_oidc:provider:list`,
`user_oidc:provider:delete`. Die Signatur von `UpsertProvider`:

```
occ user_oidc:provider <identifier>
    --clientid=<id> --clientsecret=<secret>
    --discoveryuri=<https://keycloak/realms/<realm>/.well-known/openid-configuration>
    [--endsessionendpointuri=...] [--postlogouturi=...] [--scope="openid email profile"]
```

[VERIFIED: `lib/Command/UpsertProvider.php:180-190` an `v8.11.0`, 2026-08-28]

Dazu der Schalter, ohne den zwei der drei Ereignispfade sofort und mit einer **anderen** Meldung
scheitern:

```bash
occ config:app:set user_oidc store_login_token --value=1
```

Der Quellcode liest ihn als App-Konfigwert (`TokenService.php:316`, `appConfig->getValueString(..., 'store_login_token', '0', lazy: true)`),
die Fehlermeldung sagt allerdings "It can be enabled in config.php". Beide Wege führen zum Ziel; der
`occ`-Weg ist der skriptbare. Der Bericht sollte die Diskrepanz zwischen Meldung und Mechanik nennen,
weil sie beim Nachfahren Zeit kostet.

### Keycloak-Realm: Startform und Vorbehalt

Der Container liest Realm-JSON aus `/opt/keycloak/data/import`, wenn `--import-realm` gesetzt ist;
eine bereits vorhandene Realm wird **übersprungen**, nicht überschrieben. Die Dokumentation nennt die
Option zusammen mit `start`, nicht mit `start-dev`.
[CITED: keycloak.org/server/importExport, Abruf 2026-08-28]

**Planungsanweisung:** `start-dev --import-realm` ist der bequeme Weg und in der Praxis verbreitet,
aber laut dieser Seite nicht der dokumentierte. Er ist `[ASSUMED]`. Ein Fehlschlag hier ist ein
Aufbaufehler und kein S5-Befund: der Rückfall ist die Realm einmal von Hand in der Keycloak-Oberfläche
anzulegen und danach zu exportieren, damit der zweite Lauf reproduzierbar ist. Weil die Realm bei
vorhandenem Namen übersprungen wird, muss die Messumgebung zwischen zwei Läufen ihr Keycloak-Volume
verwerfen, sonst misst der zweite Lauf die Konfiguration des ersten.

### Was genau zu beobachten ist, damit S5 ein Messwert wird und keine Vermutung

Drei Beobachtungen, in dieser Reihenfolge, alle aus demselben Aufruf:

1. **Der HTTP-Ausgang.** Derselbe OCS-Aufruf wie in S4, nach `token_expires_at = 0`. Erwartung: OCS
   `statuscode` 401 aus `validatePreRequestConditions()`, weil `getAccessToken()` im `oidc`-Zweig `''`
   zurückgibt (`svc.php:1786-1792`).
2. **Die Log-Zeile, die die Ursache trennt.** Nextcloud-Loglevel vorher auf `debug` stellen
   (`occ log:manage --level 0`), weil alle drei Meldungen `logger->debug` sind und der Vorgabewert 2
   (Warning) sie verschluckt. Das ist derselbe Mechanismus, den `research/PITFALLS.md` Pitfall 4 für
   `admin_audit` beschreibt, und er würde hier eine geglückte Reproduktion unsichtbar machen.

   | Beobachtete Zeile | Bedeutung |
   |-------------------|-----------|
   | keine der Listener-Zeilen erscheint | `isLoggedIn()` war falsch: der Bruch liegt **vor** der Sitzungsfrage (S5c) |
   | `[ExternalTokenRequestedListener] received request`, dann `GetExternalTokenFailedException: ... login token is not stored` | `store_login_token` war aus |
   | `[TokenService] Failed to exchange token, no login token found in the session` | die in `SUMMARY.md` vermutete Bruchstelle, live reproduziert (S5b) |
   | `Token event has not been caught by 'user_oidc'` (`svc.php:1687`) | der Listener hat still `return` gemacht, also Variante 1 mit anderer Signatur |
3. **Der Zustand danach.** `occ user:setting <u> integration_openproject token` und `token_expires_at`
   erneut lesen. Bleiben sie unverändert, hat keine Erneuerung stattgefunden. Das ist die Gegenprobe zu
   S4 in derselben Sprache.

**Die Zuordnung zur Codestelle, die der Bericht nennen muss:** Die behauptete Bruchstelle ist
`user_oidc` `lib/Service/TokenService.php:325-329` (`getToken()` liest `SESSION_TOKEN_KEY`, `null`
führt zu `TokenExchangeFailedException`), und die vorgeschaltete Bedingung ist
`TokenService.php:316-322` (`store_login_token`). Die davorliegende, in der Ausgangsrecherche
unbenannte Bedingung ist `if (!$this->userSession->isLoggedIn()) { return; }` in allen drei Listenern.
Der Bericht führt alle drei, in dieser Reihenfolge, und markiert die eine, die die Messung getroffen
hat.

---

## SSRF-Messung (D-06)

### Wo die Grenze liegt, und wo sie ausdrücklich nicht liegt

Die Grenze aus v1.1 ist **eine** Funktion in **einer** Datei:
`src/mcp_connector/oauth/cimd.py`, `target_allowed()` (Zeilen 168 bis 201) und die Auflösung darüber,
`resolve_addresses()` (Zeilen 258 bis 307). Der Modul-Docstring sagt selbst, warum sie existiert:

> "This module is the first place in this project where a request chooses the target of an outbound
> request of ours. Every other call goes to the configured Nextcloud, because the base URL comes from
> `NC_MCP_URL` and never from a request (phase 01 decision, T-01-08)."

[VERIFIED: `src/mcp_connector/oauth/cimd.py:1-9`, Release 0.1.11]

Das ist der Befund, der die Frage aus `research/STACK.md` A.8 Nummer 3 präzisiert: die SSRF-Grenze
sitzt **nicht** auf dem Weg zu einem fremden Host, sondern auf dem Weg zum Client-Id-Metadatendokument
eines fremden OAuth-Clients. Ein hypothetischer OpenProject-Client von Weg 1 würde heute überhaupt
keine Prüfung passieren, weil es keine zweite Basis-URL gibt. Der Bericht muss diese Unterscheidung
führen, sonst behauptet er eine Grenze, die den gemessenen Weg nie berührt hat.

Die Prüfung selbst, wörtlich:

```python
# cimd.py:189-201
mapped = getattr(addr, "ipv4_mapped", None)
if mapped is not None:
    addr = mapped
if not addr.is_global:
    return False
return not (
    addr.is_private or addr.is_loopback or addr.is_link_local
    or addr.is_reserved or addr.is_multicast or addr.is_unspecified
)
```

Und die Regel darüber, die die eigentliche Antwort auf D-06 vorwegnimmt: `resolve_addresses()` verwirft
den **ganzen Namen**, sobald **eine** seiner Adressen abgelehnt wird (Zeile 301-305, mit Begründung im
Docstring: "Not 'take the good one'").

### Der Negativkatalog, der schon existiert

`tests/unit/test_oauth_cimd.py` fährt ihn zweimal, einmal gegen `target_allowed` (Zeilen 179 bis 198)
und einmal gegen den vollen Dokumentenabruf (Zeilen 669 bis 675). Der Katalog:

`127.0.0.1`, `::1`, `10.0.0.5`, `192.168.1.1`, `169.254.169.254`, `::ffff:127.0.0.1`,
`2002:7f00:1::1`, `64:ff9b::7f00:1`, `100.64.0.1`, `224.0.0.1`, `0.0.0.0`, `::`

Dazu die drei gemessenen Lücken, die begründen, warum die Prüfung eine Konjunktion aus sieben Fragen
ist und nicht ein Flag (`test_the_three_measured_gaps_would_each_pass_a_single_flag_check`, Zeilen 206
bis 222), und die Positivliste `8.8.8.8`, `2606:4700:4700::1111`, `93.184.216.34`.
[VERIFIED: `tests/unit/test_oauth_cimd.py`, Release 0.1.11]

### Der Messweg, ohne eine Zeile Produktionscode zu ändern

Das Docker-Netz der Messumgebung ist `172.29.42.0/24` (`compose.exapp.yml`, Abschnitt `networks`),
also `is_private`. Erwartung damit: **die Grenze sperrt den Nachbardienst aus**, nicht versehentlich,
sondern konstruktionsbedingt. Der Messweg in drei Schritten, alle lesend:

1. Aus dem laufenden ExApp-Container die Namen der Nachbardienste auflösen, mit demselben Resolver, den
   die Produktion benutzt: `cimd._system_addresses("openproject", 80)` und `("nextcloud", 80)`, beides
   über `uv run python -c ...` im Container oder in einer Wegwerf-Datei unter `tests/integration/`.
   Erwartung: private Adressen aus `172.29.42.0/24`.
2. Dieselben Literale durch `cimd.target_allowed()` schicken. Erwartung: `False`.
3. `cimd.resolve_addresses("openproject", 80)` mit dem echten Systemresolver. Erwartung: `None`, samt
   der Log-Zeile "a document target was refused: an address of it is not public".

**Gegenprobe, ohne die der Messwert nichts beweist:** derselbe Aufruf für einen öffentlichen Namen im
selben Lauf muss eine Adressliste liefern. Sonst ist das `None` auch mit einem kaputten Resolver im
Container erklärbar.

**Die Aussage, die daraus in den Bericht gehört.** Nicht "die SSRF-Grenze ist zu streng", sondern:
die Grenze ist für den Weg, auf dem sie sitzt (fremdes Client-Id-Dokument), richtig, und sie ist für
einen Nachbardienst im selben Cluster **konstruktionsbedingt undurchlässig**. Wer in OD-04 eine zweite
Basis-URL einführt und `target_allowed` dafür wiederverwendet, sperrt jede Cluster-Installation aus.
Wer sie nicht wiederverwendet, braucht eine eigene, ausdrücklich begründete Prüfung für eine URL, die
aus den Admin-Einstellungen und niemals aus einer Anfrage kommt. Das ist ein Entwurfsbefund für v2.0
und der eigentliche Wert dieser Messung.

---

## Messumgebung: Docker-Einzelheiten

### Bildmarken, alle gepinnt und geprüft

| Dienst | Bildmarke | Geprüft | Größe / Anmerkung |
|--------|-----------|---------|-------------------|
| Nextcloud (Stufe A und B) | `nextcloud:33.0.7-apache` | Tag vorhanden | Ersetzt `34.0.3-apache` nur in der Spike-Compose-Datei, nie in `compose.exapp.yml` |
| OpenProject (Stufe A und B) | `openproject/openproject:17.7.2` | Tag vorhanden, 2026-08-13 | ~800 MB amd64. Alles-in-einem: PostgreSQL und memcached im Container |
| OpenProject, Alternative | `openproject/open_desk:17.7.2` | Tag vorhanden, 419 MB | genau das Image, das openDesk spiegelt. Sein Startverhalten erwartet aber openDesk-Umgebungsvariablen und ist ungeprüft: `[ASSUMED]`, nur als Rückfall nennen |
| Keycloak (Stufe B) | `quay.io/keycloak/keycloak:26.7.0` | Tag vorhanden | die openDesk-Fassung |
| Caddy, HaRP, Registry | unverändert aus `compose.exapp.yml` | in Betrieb erprobt | `caddy:2`, `ghcr.io/nextcloud/nextcloud-appapi-harp:release`, `registry:2` |

[VERIFIED: Docker-Hub- und quay.io-Tag-APIs, 2026-08-28]

Anmerkung zu `ghcr.io/nextcloud/nextcloud-appapi-harp:release`: das ist ein gleitender Tag und
widerspricht der Kein-`latest`-Regel. Er steht heute so in `compose.exapp.yml` und ist damit bestehende
Lage, nicht neue Schuld. Der Berichtskopf muss die tatsächlich gelaufene HaRP-Fassung nennen, wie
`docs/spike-dav.md` es tut ("AppAPI version: 34.0.0").

### Die Namensfalle, die einen halben Tag kostet, und ihre Auflösung

OpenProject braucht **einen** Namen, der aus dem Browser des Entwicklers **und** aus dem
Nextcloud-Container gleich lautet. Drei Gründe:

1. `OPENPROJECT_HOST__NAME` erzeugt die Adressen in Formularen und Weiterleitungen. Passt sie nicht zu
   dem, was der Browser aufgerufen hat, bricht der Consent-Fluss von Weg 1 mitten drin ab.
2. Die Redirect-URI der OAuth-Anwendung muss aus dem Browser erreichbar sein.
3. `integration_openproject` ruft OpenProject aus dem Nextcloud-Container heraus unter
   `openproject_instance_url` auf. `127.0.0.1:8082` bedeutet dort der Container selbst.

`compose.exapp.yml` hat dasselbe Problem für Nextcloud schon gelöst, mit Caddy als einziger Vordertür
und `OVERWRITEHOST: "127.0.0.1:8081"`. Der Portunterschied bleibt: Caddy hört im Container auf 80 und
ist auf dem Host als `127.0.0.1:8081` veröffentlicht.

**Empfohlene Auflösung (bewusst so gewählt, dass keine Datei außerhalb des Repositories geändert werden
muss):** Caddy einen zweiten Zuhörblock auf dem Container-Port `8082` geben und ihn als
`127.0.0.1:8082:8082` veröffentlichen, also **gleiche Portnummer innen und außen**. Dann ist
`http://op.localtest.me:8082` von beiden Seiten dieselbe Adresse:

* aus dem Browser, weil `*.localtest.me` öffentlich auf `127.0.0.1` auflöst und dafür kein Eintrag in
  der Windows-`hosts`-Datei nötig ist;
* aus dem Nextcloud-Container, weil der Compose-Dienst `caddy` einen `extra_hosts`-Eintrag der Form
  `op.localtest.me:172.29.42.10` bekommt, also die feste Adresse, die Caddy in dieser Topologie schon
  hat.

`OPENPROJECT_HOST__NAME=op.localtest.me:8082`, `OPENPROJECT_HTTPS=false`, und die Redirect-URI der
OAuth-Anwendung zeigt auf denselben Namen.

Die elegantere Variante, `networks.default.aliases: [op.localtest.me]` am Caddy-Dienst, spart den
`extra_hosts`-Eintrag, setzt aber voraus, dass Dockers eingebauter DNS einen Alias mit Punkten
beantwortet. Das ist `[ASSUMED]`. `extra_hosts` gegen die feste Adresse ist deterministisch und
deshalb der empfohlene Weg; der Alias ist eine Verbesserung, die man messen darf, aber nicht braucht.

### Umgebungsvariablen von OpenProject beim ersten Start

```bash
SECRET_KEY_BASE=<openssl rand -hex 64>      # muss über Neustarts gleich bleiben,
                                            # sonst sind Sitzungen und verschlüsselte
                                            # DB-Inhalte unlesbar
OPENPROJECT_HOST__NAME=op.localtest.me:8082
OPENPROJECT_HTTPS=false                     # sonst verlangt OpenProject HTTPS
OPENPROJECT_DEFAULT__LANGUAGE=en            # steuert auch die Sprache der Seed-Daten
```

Erster Start: mehrere Minuten, weil Seed-Daten erzeugt werden. Vorgabe-Anmeldung `admin`/`admin`.
Datenhaltung über die Bände `/var/openproject/pgdata` und `/var/openproject/assets`.
[CITED: openproject.org/docs/installation-and-operations/installation/docker/, Abruf 2026-08-28]

### Speicher- und Platzerwartung

| Posten | Erwartung | Quelle |
|--------|-----------|--------|
| OpenProject allein | mindestens 4 GB RAM, 20 GB Platte, Vierkern-CPU ab 2 GHz | openproject.org Systemanforderungen, Abruf 2026-08-28 |
| Nextcloud 33 mit SQLite | wenige hundert MB | Erfahrung aus `compose.exapp.yml` in dieser Topologie |
| Keycloak 26.7 | 0,5 bis 1 GB | `[ASSUMED]`, nicht belegt |
| Caddy, HaRP, Registry, ExApp | zusammen unter 1 GB | Erfahrung aus dieser Topologie |
| **Stufe A gesamt** | realistisch 5 bis 6 GB für die WSL2-VM | Summe, `[ASSUMED]` |
| **Stufe B gesamt** | realistisch 6 bis 8 GB | Summe, `[ASSUMED]` |

**Planungsanweisung:** Vor dem ersten Hochfahren prüfen, wieviel Speicher die WSL2-VM bekommt
(`.wslconfig`, `memory=`). Ein OpenProject, das beim Seeden vom OOM-Killer beendet wird, hinterlässt
eine halb gefüllte Datenbank und sieht wie ein Konfigurationsfehler aus. Das ist der teuerste
vermeidbare Fehlweg der ganzen Phase.

### Zustand, der entsteht, und wie er wieder weggeht

Diese Phase ist kein Umbau, aber sie erzeugt Zustand außerhalb des Repositories. Er muss abräumbar
sein, sonst hängt er an der nächsten Phase.

| Kategorie | Was entsteht | Wie es wieder weggeht |
|-----------|--------------|------------------------|
| Docker-Bände | ein Band je Dienst: Nextcloud-Daten, OpenProject `pgdata` und `assets`, Keycloak-Daten, Registry | `docker compose -f <spike-datei> down -v`. Für Keycloak zwingend, weil `--import-realm` eine vorhandene Realm überspringt |
| Docker-Netz | ein eigenes Netz mit eigenem Subnetz, **nicht** `172.29.42.0/24`, wenn die Spike-Topologie neben `compose.exapp.yml` laufen soll | mit `down` weg. Bei gemeinsamer Nutzung von `compose.exapp.yml` bleibt das bestehende Netz |
| Geheimnisse in Dateien | `SECRET_KEY_BASE`, `HP_SHARED_KEY`, OpenProject-Client-Secret, Keycloak-Client-Secret, App-Passwörter | in eine git-ignorierte Datei nach dem Muster von `.env.exapp` schreiben, nie in eine Compose-Datei und **nie in den Bericht**. `docs/spike-dav.md` sagt dazu wörtlich: "Header values that carry `APP_SECRET` ... are never printed" |
| Nextcloud-App-Konfiguration | `integration_openproject`- und `user_oidc`-Schlüssel, `store_login_token`, Loglevel auf `debug` | verschwindet mit dem Nextcloud-Band |
| Windows-`hosts`-Datei | **nichts**, wenn der `localtest.me`-Weg gewählt wird | entfällt |
| Registrierte ExApp und Deploy-Daemon | Einträge in der Nextcloud-Datenbank | verschwinden mit dem Nextcloud-Band |
| Produktionsbaum | **nichts** (Erfolgskriterium 5) | mit `git status` nachweisen: `src/`, `appinfo/`, `pyproject.toml` unverändert |

---

## Standard Stack

Diese Phase zieht **kein** neues Paket. `pyproject.toml` und `uv.lock` bleiben unverändert.

### Kern

| Werkzeug | Fassung | Zweck | Warum das und nichts anderes |
|----------|---------|-------|------------------------------|
| `curl` | im System | jeder HTTP-Messwert | Der Messwert soll die Anfrage zeigen, die gestellt wurde. Eine Bibliothek dazwischen macht aus einem Messprotokoll eine Behauptung über Bibliotheksverhalten. `docs/oauth-setup.md` und `docs/spike-discovery.md` gehen denselben Weg |
| `httpx` | 0.28.x, vorhanden | die Aufrufe, die aus einer Test-Datei kommen | einziger HTTP-Client dieses Projekts, bereits im Lock |
| `pytest` mit dem Marker `integration` | vorhanden | Messungen, die wiederholbar sein sollen | `addopts = "-m 'not integration and not matrix' ..."` hält sie aus dem Vorgabelauf heraus. Muster: `tests/integration/test_exapp_mail_reach.py` |
| `docker compose` | Docker 29.5.2, vorhanden | die Topologie | schon in Betrieb für `compose.exapp.yml` und `compose.test.yml` |
| `occ` im Container | mit Nextcloud | Konfiguration und Zustandslesen | der einzige Weg zu App- und Nutzerwerten |

### Unterstützend

| Werkzeug | Zweck | Wann |
|----------|-------|------|
| `openssl rand -hex 64` | `SECRET_KEY_BASE`, `HP_SHARED_KEY` | einmal beim Aufbau |
| `uv run python -c ...` | die SSRF-Messung gegen `cimd.py` | Stufe A, drei Zeilen |
| Browser | genau zwei Schritte: der Consent von Weg 1, und der persönliche OAuth-Durchlauf von `integration_openproject` je Konto | unvermeidbar, `resource_owner_authenticator` verlangt eine Sitzung |
| `occ log:manage --level 0` | S5 sichtbar machen | Stufe B, sonst verschluckt Nextcloud die `debug`-Zeilen |

### Bewusst nicht benutzt

| Statt | Nicht | Grund |
|-------|-------|-------|
| `curl` und `httpx` | jeder PyPI-OpenProject-Client | `pyopenproject` seit 2021 tot, `openproject` pinnt `httpx>=0.25,<0.26` gegen unser `>=0.28,<0.29`, `openproject-api-client` hat drei Releases und zöge `requests` in ein Projekt, das bewusst nur `httpx` spricht. Aus `research/STACK.md` A.4, gegen die PyPI-JSON-API belegt |
| lokale Compose-Topologie | k3s, kind, Minikube | D-01 und D-03 schließen einen Cluster aus. Ein `kind`-Cluster würde die Kubernetes-Frage von K1 auch nicht beantworten, weil dafür `app_api` 34 nötig wäre und openDesk 33 fährt |
| `nextcloud:33.0.7-apache` | `juliusknorr/nextcloud-docker-dev` | die HaRP-Topologie dieses Repositories ist erprobt und liefert genau die Impersonationslage, die gemessen werden soll. Die Dev-Umgebung wäre ein zweiter, ungemessener Aufbau |
| `openproject/openproject:17.7.2` | `openproject/openproject:17` oder `:latest` | Kein-`latest` (D-02). `17` ist gleitend |

**Installation:** keine. Nur `docker compose pull` der fünf bis sechs Bildmarken.

---

## Package Legitimacy Audit

Diese Phase installiert **kein** Paket aus einem Sprachregister (npm, PyPI, crates). `pyproject.toml`
und `uv.lock` werden nicht angefasst (D-12, Erfolgskriterium 5). Ein `slopcheck`-Lauf hat damit kein
Ziel und wurde nicht durchgeführt.

Was diese Phase stattdessen von außen zieht, sind Container-Bildmarken. Für sie gilt dasselbe
Prüfprinzip, und die Prüfung ist gelaufen:

| Artefakt | Register | Tag geprüft | Herausgeber | Verdikt |
|----------|----------|-------------|-------------|---------|
| `nextcloud:33.0.7-apache` | Docker Hub, offizielles Bild | ja, 2026-08-28 | Docker Official Images | genehmigt |
| `openproject/openproject:17.7.2` | Docker Hub | ja, gepusht 2026-08-13 | `openprojectci`, Herstellerkonto | genehmigt |
| `openproject/open_desk:17.7.2` | Docker Hub | ja, gepusht 2026-08-13 | dasselbe Konto; von openDesk gespiegelt | genehmigt, aber Startverhalten ungeprüft: nur Rückfall |
| `quay.io/keycloak/keycloak:26.7.0` | quay.io | ja, 2026-08-28 | Keycloak-Projekt | genehmigt |
| `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | ghcr.io | Tag ist gleitend | Nextcloud | bestehende Lage aus `compose.exapp.yml`; die gelaufene Fassung gehört in den Berichtskopf |
| `caddy:2`, `registry:2` | Docker Hub, offizielle Bilder | bestehende Lage | Docker Official Images | genehmigt |

**Wegen `slopcheck` entfernte Pakete:** keine (kein Paket im Umfang).
**Als verdächtig markierte Pakete:** keine.

Nextcloud-Apps sind der zweite Bezugsweg. Beide kommen aus dem offiziellen App Store unter
`nextcloud/`-Eigentümerschaft, beide mit ihrer Plattformspanne geprüft:
`integration_openproject` 3.1.1 (`>=33.0.0 <35.0.0`) und `user_oidc` 8.11.0 (`>=29.0.0 <36.0.0`).
[VERIFIED: `https://apps.nextcloud.com/api/v1/platform/33.0.0/apps.json`, 2026-08-28]

---

## Nachweisform: was in diesem Projekt als Beleg gilt

Kein Nyquist-Abschnitt, weil `workflow.nyquist_validation` in `.planning/config.json` auf `false` steht.
Stattdessen dieser Abschnitt, weil OD-01 bis OD-03 nicht durch Tests, sondern durch Schriftstücke
erfüllt werden und die Form dieser Schriftstücke im Repository schon festliegt.

Die Form kommt aus `docs/spike-dav.md`, `docs/spike-mail.md` und `docs/spike-discovery.md` und hat
sechs Bestandteile. Ein Nachweis, dem einer fehlt, gilt in diesem Projekt nicht.

| Bestandteil | Woran man ihn erkennt | Vorbild |
|-------------|------------------------|---------|
| **Kopf mit gelesenen Fassungen** | Jede Fassung ist vor dem Schreiben aus der laufenden Instanz gelesen (`occ status`, `occ app:list`), nicht aus der Recherche übernommen | `spike-mail.md`, Zeile 3 bis 15 |
| **Vorab festgelegtes Entscheidungskriterium** | Steht **vor** der ersten Messung im Text, damit die Zahlen es nicht nachträglich verschieben | `spike-mail.md` §"Entscheidungskriterium, vorab festgelegt" |
| **Behauptung, Messweg, Messwert** | Eine Tabellenzeile je Behauptung, mit dem Aufruf und dem gemessenen Wert, nicht mit einer Bewertung | `spike-dav.md` §"Decision", `spike-mail.md` §"Messung" |
| **Gegenprobe** | Mindestens eine Beobachtung, die zeigt, dass der Messwert nicht auch anders zustande gekommen sein kann. In `spike-dav.md` sind es zwei: kein App-Passwort im Prozess, und ein falsches `APP_SECRET` liefert 401 | `spike-dav.md` §"The two controls" |
| **Negativfall mit bekanntem Pfad** | Der Zugriff scheitert, obwohl der Weg bekannt ist. Bei DAV: 404 statt 200 auf einen Pfad, den der Messende kennt | `spike-dav.md` §"The negative case" |
| **"Was diese Messung nicht beweist"** | Ein eigener Abschnitt mit den Rändern | alle drei Vorbilder |

Daraus die Zuordnung zu den drei Anforderungen dieser Phase:

| Anforderung | Was als hinreichender schriftlicher Beleg gilt |
|-------------|------------------------------------------------|
| **OD-01** | Drei Antworten (App Store, Kubernetes-Daemon, Versionspin), jede mit **Repository, Tag, Datei, Zeile und wörtlichem Zitat**, plus die Rest-Unbekannten namentlich als ISV-Frage. Ein Verweis auf eine Dokumentationsseite ohne Zitat gilt nicht, weil Dokumentationsseiten sich ändern (siehe die nicht mehr auffindbare `manual-install`-Formulierung). Dazu **S0**: eine gemessene Aussage über 33.0.7 statt einer geerbten über 34.0.3 |
| **OD-02** | Für **jeden** der beiden Wege: PKCE-Verhalten, Token-Lebensdauer, Erneuerung ohne Browsersitzung, Zwei-Konten-Negativbeweis, jeweils mit Gegenprobe. Dazu die SSRF-Antwort mit ihrer Einordnung (welcher Weg von der Grenze überhaupt berührt wird). Ein Weg, der nicht gemessen wurde, steht als **"ungemessen"** mit dem Grund, warum die Messung nicht möglich war, und niemals als "verworfen" (D-03, Erfolgskriterium 3) |
| **OD-03** | Eine Frageliste, in der jede Frage einen **Grund** trägt, damit sie nicht wie Neugier klingt (Muster: `ARCHITECTURE.md` A.7). Die vier Pflichtfragen aus OD-01 wörtlich enthalten. Fragen, die diese Recherche beantwortet hat, sind **entfernt**, nicht mitgeführt |

**Zwei Regeln, die aus context_agent#230 kommen und hier gelten:**

1. Keine Behauptung über fremden Code ohne Datei, Zeile und Tag. Diese Recherche liefert die Zeilen für
   `integration_openproject` 3.1.1, `user_oidc` 8.11.0, `app_api` `stable33`/`stable34` und
   OpenProject `v17.7.2`. Wer eine andere Fassung messen will, muss die Zeilen neu holen.
2. Das Issue `user_oidc#925` geht **nur** mit geglückter Live-Reproduktion raus (D-08). Bricht Stufe B
   ab, bleibt der Entwurf liegen, und der Bericht sagt "ungemessen" mit dem Grund.

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Nextcloud plus HaRP plus ExApp lokal hochziehen | eine neue Topologie von Null | `compose.exapp.yml` und `scripts/bootstrap_exapp.sh` kopieren, nur die Nextcloud-Bildmarke auf `33.0.7-apache` tauschen und die neuen Dienste anhängen | Die Datei löst sieben Einzelprobleme, die man sonst neu entdeckt: `/exapps/*`-Regel in Caddy, `OVERWRITEHOST`, `TRUSTED_PROXIES` auf **eine** Adresse statt das Subnetz, feste Caddy-Adresse, `NEXTCLOUD_TRUSTED_DOMAINS` samt `caddy`, HaRP-Shared-Key ohne Vorgabewert, lokale Registry. Das Bootstrap-Skript ist idempotent und kennt den `--manual`-Weg |
| Antwortform "erreicht oder nicht erreicht" beurteilen | eine neue Heuristik | das Kriterium aus `docs/spike-mail.md` samt `_verdict` in `tests/integration/test_exapp_mail_reach.py` | Es ist einmal durchgedacht und hat den Fehler "auf 200 prüfen" schon verhindert |
| Zwei-Konten-Negativbeweis strukturieren | eine neue Form | `docs/spike-dav.md` §"The negative case" und §"The confused deputy check" | Die Form ist erprobt und ein Prüfer erkennt sie wieder |
| Adressklassen für die SSRF-Messung aufzählen | eine neue Liste | den Negativkatalog aus `tests/unit/test_oauth_cimd.py:179-198` | Er enthält drei gemessene Lücken, die eine selbstgeschriebene Liste garantiert nicht enthält (NAT64, CGNAT, Multicast) |
| PKCE-Verifier und -Challenge erzeugen | eine neue Implementierung | den Weg, den `oauth/connect.py` und `scripts/oauth_flow_check.py` schon gehen | S256 richtig zu bauen ist einfach und trotzdem eine Stelle, an der ein Tippfehler wie ein Serverbefund aussieht |
| Ein OpenProject-Client | irgendetwas | nichts, D-12 verbietet Code | Der Weg-0-Client ist OD-04 |

**Kerngedanke:** Diese Phase hat kein Bauproblem, sie hat ein Beweisproblem. Jede Stunde, die in einen
neuen Aufbau geht, fehlt bei den Gegenproben, und eine Messung ohne Gegenprobe ist in diesem Projekt
kein Nachweis.

---

## Common Pitfalls

### Pitfall 1: Der Aufbau frisst den Tag und die Messung fällt aus

**Was schiefgeht:** OpenProject beim ersten Start braucht Minuten und mindestens 4 GB, die
Zwei-Wege-OAuth2-Einrichtung braucht beide Seiten konfiguriert, Keycloak braucht eine Realm mit zwei
Clients. Drei Aufbauschritte, jeder mit eigenen Fehlerbildern, und am Ende des Tages steht kein
einziger Messwert im Bericht.

**Warum es passiert:** Die Aufbauschritte fühlen sich wie Fortschritt an. Ein halb konfigurierter
Aufbau produziert Fehlermeldungen, die wie Befunde aussehen.

**Wie vermeiden:** Zwei Stufen, mit einem Schnitt dazwischen, und Stufe A muss **vollständig
protokolliert** sein, bevor Stufe B beginnt. Konkret, mit Zeitschätzung und Rückfall:

| Schritt | Erwarteter Aufwand | Häufigstes Fehlerbild | Rückfall, damit der Bericht "ungemessen" statt "hängt" sagt |
|---------|--------------------|-----------------------|--------------------------------------------------------------|
| Nextcloud 33.0.7 in der HaRP-Topologie, ExApp registriert (**S0**) | 1 bis 2 Stunden | Heartbeat scheitert, weil `OVERWRITEHOST` oder die Caddy-Regel nicht passt | keiner. Ohne S0 gibt es keine Stufe A. Wenn es hier bricht, ist **das** der OD-01-Befund und der wertvollste der Phase |
| OpenProject 17.7.2 erster Start | 30 bis 90 Minuten, davon meist Warten | OOM beim Seeden; `OPENPROJECT_HTTPS` nicht gesetzt und alles leitet auf HTTPS um | WSL2-Speicher erhöhen und einmal wiederholen. Bricht es zweimal, entfällt der **ganze** OpenProject-Teil und OD-02 wird "ungemessen, Aufbau nicht erreichbar" mit dem Log |
| Zwei-Wege-OAuth2 zwischen beiden (Weg 0 nutzbar) | 2 bis 4 Stunden | Namensfalle (siehe oben); die Einrichtung meldet Erfolg, aber kein Nutzer hat ein `token`, weil der persönliche Durchlauf fehlt | Rückfall auf Weg B der Einrichtung (`occ config:app:set` plus persönlicher Durchlauf je Konto). Bricht auch der: S1 bleibt messbar, S2 bis S6 werden "ungemessen" |
| Weg 1: OAuth-Anwendung plus Consent | 1 bis 2 Stunden | Client-Secret nicht kopiert; `Content-Type` bei `/oauth/token` falsch; Consent-Umleitung passt nicht zur Redirect-URI | Weg 1 ist der **unabhängigste** Teil und braucht Nextcloud nicht. Ihn zuerst messen, wenn Weg 0 hängt. Das ist die wichtigste Reihenfolgenoption dieser Phase |
| Stufe B: Keycloak plus `user_oidc` (**S5**) | 3 bis 6 Stunden, ehrlich geschätzt | Realm-Import übersprungen, weil die Realm schon existiert; `user_oidc` verweigert wegen Discovery-URI; `integration_openproject` erkennt den Anbieter nicht (`isUserOIDCAppSupported()` prüft fünf Klassen und die Mindestfassung) | **Vorgesehen und ausdrücklich zulässig:** S5 wird "ungemessen" mit Quellcodebeleg plus offener Frage. `ARCHITECTURE.md` A.6 hat diesen Rückfall selbst vorgesehen. Folge: `user_oidc#925` bleibt liegen (D-08) |

**Warnzeichen:** Ein Tag ohne einen einzigen Messwert im Protokoll. Ein Fehlerbild, das noch nicht in
der Tabelle steht und trotzdem als Befund notiert wird.

### Pitfall 2: Der Impersonationsnutzer, der sofort funktioniert

**Was schiefgeht:** Weg 1 ist zäh (Consent im Browser, zwei Konten, PKCE). `client_credentials` steht
in `grant_types_supported`, das Feld "Client Credentials User" steht direkt im Formular, und
`OPENPROJECT_AUTHENTICATION_GLOBAL__BASIC__AUTH_USER` liegt sogar in den openDesk-Werten
(`helmfile/apps/openproject/values.yaml.gotmpl:73-74`). Jeder dieser drei Wege liefert in fünf Minuten
eine grüne Antwort und macht den Satz "der Assistent sieht niemals mehr als der angemeldete Nutzer"
unwahr.

**Warum es passiert:** Der Unterschied zwischen "die API antwortet" und "die API antwortet als der
richtige Mensch" ist auf einer Einnutzer-Instanz unsichtbar. Genau wie bei den Talk-Read-Markern in
v1.2.

**Wie vermeiden:** Drei Regeln, alle prüfbar:

1. Jeder Messwert im Bericht nennt den Nutzernamen, unter dem er lief. Kein Nutzername, kein Messwert.
2. Das Feld "Client Credentials User" bleibt leer, und der Bericht sagt in einem Satz, dass es leer
   geblieben ist.
3. `git grep -i "client_credentials\|GLOBAL__BASIC__AUTH\|apikey:"` findet in den Dateien dieser Phase
   nichts außer in einem Absatz, der erklärt, warum diese Wege ausgeschlossen sind.

**Warnzeichen:** Ein `OPENPROJECT_API_KEY` oder `client_secret` in einer Compose-Datei. Ein Messwert,
der "funktioniert" sagt, ohne zu sagen, als wem.

### Pitfall 3: Der lokale Aufbau wird für openDesk gehalten

**Was schiefgeht:** Eine grüne Messung auf einer blanken Instanz wandert in den Bericht als Aussage
über openDesk. Was der lokale Aufbau **nicht** reproduziert, jedes einzeln zu nennen:

* Keycloak als Anmeldezwang. `OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"` bedeutet, dass
  es in openDesk kein lokales Anmeldeformular gibt. Der Consent-Fluss von Weg 1 hat dort einen
  zusätzlichen Umleitungsschritt, den Stufe A nicht misst und Stufe B nur nachbaut.
* Die Scope-Pflicht für ein OIDC-JWT (`scope`-Anspruch mit `api_v3`), Breaking Change in OpenProject
  16.0.0. Im lokalen OAuth-Modus unsichtbar.
* Die Datenlage. Seed-Daten haben ein Projekt und wenige Arbeitspakete. Das private Projekt für S3 und
  D-05 muss **von Hand** entstehen, sonst ist der Negativbeweis leer und sieht trotzdem grün aus.
* Kubernetes, Helm, gepinnte Charts, abgeschalteter App Store, `manual-install` als einziger Daemon.
* Der `integration_openproject`-Modus, den openDesk wirklich fährt.

**Wie vermeiden:** Zwei getrennte Ergebnisspalten im Bericht, und die Trennung bleibt sichtbar:
"lokal gemessen" gegen "aus openDesk-Quellen belegt". Ein Befund, der in keine der beiden Spalten
passt, gehört in "ungemessen".

**Warnzeichen:** Ein Satz im Bericht, der "in openDesk" sagt und auf einen lokalen Messwert verweist.

### Pitfall 4: Der Messwert ohne Gegenprobe

**Was schiefgeht:** S1 antwortet 200, das wandert als "Weg 0 trägt" in den Bericht. Aber eine 200 kann
auch von einem App-Passwort im Prozess kommen, von einem zwischengespeicherten Token, von einer
Anmeldeseite mit Status 200. `docs/spike-dav.md` fährt gegen genau das zwei Kontrollen, und
`docs/spike-mail.md` fährt sie in einem Test namentlich (`test_the_measuring_process_holds_no_nextcloud_app_password`).

**Wie vermeiden:** Die Gegenprobenspalte der S0-bis-S6-Tabelle ist Pflichtinhalt, nicht Kür. Die drei
wichtigsten: falsches `APP_SECRET` liefert 401; kein App-Passwort im Prozess; bei S4 ein kaputtes
`refresh_token` liefert 401.

**Warnzeichen:** Eine Behauptung im Bericht, unter der nur eine Zeile steht.

### Pitfall 5: Nextcloud verschluckt die Zeile, die S5 entscheidet

**Was schiefgeht:** Alle drei Meldungen, die die drei OIDC-Bruchstellen unterscheiden, sind
`logger->debug`. Der Vorgabe-Loglevel von Nextcloud ist 2 (Warning). S5 liefert dann eine 401 ohne
Ursache, und der Bericht schreibt die in `SUMMARY.md` vermutete Ursache hin, ohne sie gesehen zu haben.
Genau dieser Mechanismus macht `admin_audit` heute schon unsichtbar (`research/PITFALLS.md` Pitfall 4).

**Wie vermeiden:** `occ log:manage --level 0` **vor** dem ersten S5-Lauf, und das Log nach jedem Lauf
frisch lesen. Die Log-Zeile ist der Messwert, nicht die 401.

**Warnzeichen:** Ein S5-Abschnitt, der eine Ursache nennt, aber keine Log-Zeile zeigt.

### Pitfall 6: Der Produktionsbaum bewegt sich unbemerkt

**Was schiefgeht:** Eine Messung braucht "nur eine kleine Hilfsfunktion" in `src/`, und
Erfolgskriterium 5 ist verletzt. Oder eine Test-Datei importiert etwas, das es noch nicht gibt, und
jemand baut es.

**Wie vermeiden:** Am Ende der Phase `git status` und ein Diff gegen den Stand vor der Phase:
`src/`, `appinfo/`, `pyproject.toml` und `uv.lock` unverändert. Dazu
`uv run python scripts/check_tool_budget.py` mit demselben Ergebnis wie heute:
**15712 Bytes, 21 Werkzeuge, Budget 18000** (gemessen 2026-08-28). Und
`uv run pytest -q` grün, weil die Spike-Dateien den Marker `integration` tragen und im Vorgabelauf
übersprungen werden.

**Warnzeichen:** Ein Import in einer Spike-Datei, der auf ein Modul zeigt, das OD-04 erst bauen wird.

### Pitfall 7: Ein Geheimnis landet im Bericht

**Was schiefgeht:** `docs/spike-opendesk.md` liegt im öffentlichen Repository. Ein kopierter
Autorisierungscode, ein `refresh_token`, ein Client-Secret, ein `AUTHORIZATION-APP-API`-Wert (der ist
Base64 von `<user>:<APP_SECRET>` und damit genau so heikel wie das Geheimnis selbst).

**Wie vermeiden:** Die Regel, die `docs/spike-dav.md` wörtlich führt: nur Statuscodes und vom Server
zurückgegebene Ids werden gezeigt. Tokenwerte werden auf ihre Länge und ihr Präfix reduziert.
`expires_in` ist eine Zahl und darf stehen; ein `access_token` nie. Vor dem Commit ein Griff nach
`eyJ`, `Bearer `, `refresh_token=` und `client_secret` über die neuen Dateien.

**Warnzeichen:** Ein Codeblock im Bericht, der länger als drei Zeilen JSON aus einer Token-Antwort
zeigt.

---

## Environment Availability

| Abhängigkeit | Gebraucht für | Vorhanden | Fassung | Rückfall |
|--------------|---------------|-----------|---------|----------|
| Docker Engine | die gesamte Messumgebung | ja | 29.5.2, Build 79eb04c (gemessen 2026-08-28) | keiner. Ohne Docker ist OD-02 vollständig "ungemessen" |
| WSL2 | Docker unter Windows | ja | aus früheren Phasen erprobt | keiner |
| `git bash` | Bootstrap-Skripte | ja | die Skripte im Repository setzen `MSYS_NO_PATHCONV=1` und laufen damit | PowerShell würde die Skripte brechen |
| `uv` | jeder Python-Aufruf | ja | das System-Python ist defekt, `uv run` ist Pflicht (CLAUDE.md) | keiner |
| `curl` | HTTP-Messwerte | ja | in dieser Sitzung benutzt | `httpx` über `uv run` |
| Zugang zu gitlab.opencode.de (Rohdateien und Archiv) | OD-01 | ja, **ohne Anmeldung** | Rohpfad und `/-/archive/` antworten 200; die Blob-Suche über die API antwortet 401 | Archiv laden und lokal durchsuchen. Genau so ist K6 entstanden |
| Zugang zu Docker Hub, quay.io, ghcr.io | Bildmarken | ja | Tag-APIs in dieser Sitzung abgefragt | keiner |
| Browser | zwei Consent-Schritte | ja | | keiner. Ohne Browser ist Weg 1 "ungemessen" |
| Konto in der OpenProject-Community | Antwort auf die OCS-Frage | **nein** | Selbstregistrierung antwortet HTTP 400 "Registration not allowed" | Entwurf einer Konto-Anfrage, Owner sendet (D-11). Der Rückkanal läuft nach dieser Phase weiter |
| `ctx7` (Context7-CLI) | Bibliotheksdokumentation | **nein** | `command -v ctx7` findet nichts | Für diese Phase ohne Folge: alle Belege kommen aus Quellcode an gepinnten Tags und aus Herstellerdokumentation. Nicht per `npx --yes` nachinstallieren |
| Kubernetes-Cluster | ein echter openDesk-Installationsversuch | **nein, und ausdrücklich nicht beschafft** | D-01, D-03 | Quellenbeleg statt Messung. Die Frage bleibt offen und geht auf die ISV-Liste |

**Fehlende Abhängigkeiten ohne Rückfall:** keine, die OD-01 bis OD-03 blockiert.
**Fehlende Abhängigkeiten mit Rückfall:** OpenProject-Community-Konto (Entwurf), Kubernetes-Cluster
(Quellenbeleg), `ctx7` (nicht gebraucht).

---

## Vorschlag für den Aufbau von `docs/spike-opendesk.md`

Nach D-09 und Erfolgskriterium 1. Die Gliederung ist bewusst so gebaut, dass ein Leser die
Installierbarkeit erfährt, bevor er eine API-Frage sieht, und dass jeder Abschnitt eine der drei
Anforderungen abschließt.

```
# openDesk-Spike (OD-01, OD-02, OD-03)

**Status:** ...
**Entscheidungsdatum:** ...
**Nextcloud:** 33.0.7 (Build ..., aus `occ status`)
**AppAPI:** ... (aus `occ app:list`)
**integration_openproject:** 3.1.1 (aus `occ app:list`)
**user_oidc:** ... (aus `occ app:list`, oder "nicht installiert" wenn Stufe B ausfiel)
**OpenProject:** 17.7.2 (aus der Fussleiste der Instanz)
**Keycloak:** ... oder "nicht Teil dieser Messung"
**Deploy-Daemon:** HaRP, über die Topologie aus <spike-compose-datei>
**Scope:** ... und was ausdruecklich nicht gemessen wurde

## Entscheidungskriterien, vorab festgelegt
   (Antwortform statt Statuscode; was "erreicht" heisst; was "ungemessen" heisst)

## 1. Installierbarkeit (OD-01)
### 1.1 App Store            -> belegt, Zitat mit Datei und Zeile
### 1.2 Deploy-Daemon und Kubernetes -> belegt, Versionsgrenze NC 33 gegen NC 34
### 1.3 Versionspin 33.0.7 gegen unsere 34.0.3-Nachweise -> belegt plus gemessen (S0)
### 1.4 Was offen bleibt     -> namentlich, mit Verweis auf Abschnitt 4

## 2. Nutzeridentität gegen OpenProject (OD-02)
### 2.1 Weg 0: Behauptungen S1 bis S6, je Behauptung Messweg, Messwert, Gegenprobe
### 2.2 Weg 1: PKCE, expires_in, Refresh ohne Sitzung, Zwei-Konten-Negativbeweis
### 2.3 Die SSRF-Grenze und was sie wirklich abdeckt
### 2.4 Welcher Weg trägt, als Folge dieser Messungen
### 2.5 Was ungemessen blieb, und warum die Messung nicht möglich war

## 3. API-Form (Vorarbeit für OD-04, kein Requirement dieser Phase)
   Byte-Kosten, Feldsatz, die drei Lücken der OCS-Fläche

## 4. Fragenliste für den ISV-Call am 14.09. (OD-03)
   Jede Frage mit ihrem Grund

## 5. Rohmesswerte
   Aufrufe und Antworten, gekürzt nach der Geheimnisregel

## Was diese Messung nicht beweist
```

---

## OD-03: was auf die Fragenliste gehört, und was nicht mehr

### Die vier Pflichtfragen aus OD-01, wörtlich abzudecken

1. **ZenDiS-Aufnahmeverfahren.** Wie wird eine Drittanbieter-Komponente in openDesk aufgenommen: wer
   entscheidet, nach welchen Kriterien, in welchem Zeitrahmen? Grund: öffentlich nicht auffindbar, und
   wenn die Antwort "nur als Teil der Distribution" lautet, heißt die nächste Roadmap-Phase nicht
   "OpenProject-Werkzeuge", sondern "Aufnahmefähigkeit herstellen".
2. **Installationsweg in openDesk.** Ist die Installation einer External App vorgesehen, und wenn ja,
   auf welchem Weg? Grund: AppAPI kommt im Deployment-Projekt an keiner Stelle vor (K6), und der App
   Store ist aus.
3. **AGPL-Konsequenz für die Enterprise-Positionierung.** Grund: ein Audit-Log in einem
   AGPL-Repository kann kein exklusives kommerzielles Unterscheidungsmerkmal sein. Verhandlungsfrage,
   keine Recherchefrage.
4. **Talk und Kontakte sind in openDesk abgeschaltet.** `spreed: enabled: false`,
   `contacts: enabled: false`, dazu `comments` und `circles` aus. Zwei der neun Werkzeugfamilien
   liegen dort dunkel. Was heißt das für die Store-Beschreibung und für einen openDesk-Zuschnitt:
   eigene Fassung, Fähigkeitsprüfung zur Laufzeit, oder gar nicht bewerben?

### Fünf Fragen, die diese Recherche neu erzeugt hat

5. **Wann geht openDesk auf Nextcloud 34 oder höher?** Grund und Aufhänger in einem Satz: AppAPI hat
   ab `app_api` 34 einen Kubernetes-Deploy-Daemon (`kubernetes-install`, über HaRP, vier
   Service-Freigabearten, vier CI-Workflows), und auf dem gepinnten Stand 33.0.7 existiert er nicht.
   Das ist die stärkste Frage dieser Phase, weil sie aus einer Absage eine Terminfrage macht.
6. **Enthält das openDesk-Nextcloud-Image `app_api`, und ist die App eingeschaltet?** Grund: das Image
   wird aus einem nicht öffentlich mitgelesenen Projekt gebaut; die Frage ist aus Quellen nicht
   entscheidbar und entscheidet alles Weitere.
7. **In welchem Modus läuft `integration_openproject` in openDesk, `oauth2` oder `oidc`?** Grund: im
   `oauth2`-Modus erneuert die App das Nutzertoken serverseitig ohne Browsersitzung (Weg 0 trägt
   dauerhaft), im `oidc`-Modus sagt der Upstream-Kommentar selbst "Token exchange needs to be
   initiated from the UI" (Weg 0 bricht nach Tokenablauf). Der `opendesk-openproject-bootstrap`-Job
   hält beide Admin-Zugänge, die der Zwei-Wege-OAuth2-Weg braucht, aber seine Logik liegt in einem
   eigenen Image.
8. **Gibt es einen vorgesehenen Weg, wie eine AppAPI-ExApp ohne PHP-Anteil ein audience-korrektes
   Token für eine Schwesterkomponente bekommt, ohne Browsersitzung?** Grund: `user_oidc` bietet den
   Austausch nur als PHP-Ereignis an, es gibt keine Route dafür, und alle drei Listener beginnen mit
   `if (!$this->userSession->isLoggedIn()) return;`. Das ist eine Lücke im openDesk-Baukasten, nicht in
   unserem Entwurf, und zugleich unser stärkster fachlicher Beitrag zum Gespräch.
9. **Warum bewerben die AS-Metadaten von OpenProject `code_challenge_methods_supported` nicht, obwohl
   `force_pkce` im Doorkeeper-Initializer steht?** Grund: ein Client, der RFC 8414 sauber liest,
   schließt daraus, dass PKCE nicht unterstützt wird, und baut den Fluss ohne. Kleiner Befund,
   billiger Beitrag, gehört eher in den OpenProject-Kanal als in den ISV-Call, aber er zeigt Tiefe.

### Drei Fragen, die aus der Ausgangsrecherche stammen und **nicht mehr** auf die Liste gehören

| Frage aus `ARCHITECTURE.md` A.7 bzw. `STACK.md` A.8 | Warum sie entfällt |
|------------------------------------------------------|--------------------|
| "Ist AppAPI in openDesk aktiviert, und welcher Deploy-Daemon ist vorgesehen?" | Teilweise beantwortet (K6: AppAPI kommt im Deployment-Projekt nicht vor) und in Frage 6 präziser gefasst. Die alte Fassung würde eine Antwort einladen, die wir schon haben |
| "Nimmt `/oauth/authorize` PKCE an, obwohl die Metadaten es nicht bewerben?" | Aus der Quelle beantwortet (K2: `force_pkce`). Bleibt Messung, ist keine Frage mehr. Der Rest wird Frage 9 |
| "Veröffentlicht `integration_openproject` eine Capability, oder braucht es den Navigations-Kanal?" | Aus der Quelle beantwortet (K4: `IPublicCapability` mit `app_version`) |

Die drei nicht-technischen Fragen aus dem bestehenden Dossier (Verkaufsmechanik, Referenz-ISVs,
Kanal des Enterprise-Flags) bleiben unberührt: sie kommen aus dem Validierungsplan und nicht aus
dieser Phase.

---

## Security Domain

Diese Phase schreibt keinen Produktionscode und verändert die Angriffsfläche der ausgelieferten App
nicht. Der Sicherheitsanteil liegt vollständig in der Messumgebung und im Bericht.

### Zutreffende ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Standardmaßnahme in dieser Phase |
|----------------|-----------|----------------------------------|
| V2 Authentifizierung | ja | Gemessen wird ein Autorisierungscode-Fluss mit PKCE gegen einen fremden AS. Client Credentials, globale Basic-Auth und ein Impersonationsnutzer sind ausgeschlossen und der Ausschluss steht im Bericht (Pitfall 2) |
| V3 Sitzungsverwaltung | ja | Die zentrale Messung von S4 und S5 ist genau eine Sitzungsfrage: trägt die Tokenerneuerung ohne Browsersitzung. Die Messumgebung hält keine Sitzung im messenden Prozess |
| V4 Zugriffssteuerung | ja | Zwei Konten sind auf beiden Wegen Pflicht (D-05). Der Negativbeweis ist der Nachweis, dass die Zugriffssteuerung des Zielsystems und nicht unsere Filterung entscheidet |
| V5 Eingabevalidierung | nein | Kein neuer Eingabepfad. Kein Werkzeug, kein Endpunkt |
| V6 Kryptografie | teilweise | `SECRET_KEY_BASE` und die PKCE-Verifier werden mit `openssl rand` bzw. dem bestehenden Weg aus `oauth/connect.py` erzeugt, nie von Hand |
| V7 Fehlerbehandlung und Protokollierung | ja | Der Loglevel wird für S5 bewusst auf `debug` gesenkt. Das ist eine Messumgebung auf Loopback; in `docs/` darf daraus keine Empfehlung für Produktion werden |
| V14 Konfiguration | ja | Alle Bildmarken gepinnt (Ausnahme HaRP, bestehende Lage), alle Ports auf Loopback, keine Vorgabewerte für Geheimnisse (WR-11-Muster aus `compose.exapp.yml`) |

### Bekannte Bedrohungsmuster für diesen Aufbau

| Muster | STRIDE | Standardmaßnahme |
|--------|--------|------------------|
| Ein Impersonationskonto liefert allen Anfragenden dieselbe Sicht | Elevation of Privilege | Ausgeschlossen und der Ausschluss dokumentiert; jeder Messwert nennt den Nutzernamen (Pitfall 2) |
| Ein Geheimnis wandert in ein öffentliches Repository | Information Disclosure | Geheimnisse nur in git-ignorierte Dateien; Griff nach `eyJ`, `Bearer `, `client_secret` vor dem Commit (Pitfall 7) |
| Eine trivial übernehmbare Instanz hängt im LAN | Spoofing, Tampering | Alle Ports auf `127.0.0.1` binden, wie `compose.exapp.yml` und `compose.test.yml` es tun (WR-06) |
| Ein Container mit unvertrauter Eingabe fälscht Client-Adressen | Spoofing | `TRUSTED_PROXIES` bleibt auf **eine** Adresse, nicht auf das Subnetz (WR-08), und der dynamische Adressbereich bleibt aus der statischen Hälfte heraus (IN-03) |
| Der Docker-Socket im HaRP-Container | Elevation of Privilege | Bestehende, in `compose.exapp.yml` dokumentierte und akzeptierte Lage (T-02-31). Die Topologie hört nur auf Loopback und wird nach der Messung gestoppt |
| Eine SSRF-Grenze wird für einen Weg wiederverwendet, für den sie nicht gedacht ist | Tampering | Der Befund aus der SSRF-Messung sagt genau das, und er ist ein Entwurfsbefund für OD-04, nicht eine Änderung in dieser Phase |

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---------|-----------|---------------------|
| A1 | `start-dev --import-realm` importiert die Realm zuverlässig; die Dokumentation nennt `--import-realm` nur zusammen mit `start` | S5-Aufbau | Halbe Stunde Aufbauzeit. Rückfall: Realm von Hand anlegen und exportieren |
| A2 | Dockers eingebauter DNS beantwortet einen Netzwerk-Alias, der Punkte enthält (`op.localtest.me`) | Namensfalle | Keins, wenn der empfohlene `extra_hosts`-Weg gegen die feste Caddy-Adresse gewählt wird. Der Alias ist nur die elegantere Variante |
| A3 | Speicherbedarf: Stufe A 5 bis 6 GB, Stufe B 6 bis 8 GB | Messumgebung | OOM beim OpenProject-Seeding, halber Tag. Deshalb steht die WSL2-Speicherprüfung als erster Schritt in Pitfall 1 |
| A4 | Keycloak 26.7 braucht 0,5 bis 1 GB | Messumgebung | wie A3 |
| A5 | `app_api` in der laufenden Nextcloud 33.0.7 trägt die Fassung 33.0.0 (passend zu `stable33`) | Versionsmatrix, K1 | Wäre die Fassung höher, könnte der Kubernetes-Befund anders liegen. Deshalb ist "Fassung aus `occ app:list` in den Berichtskopf" Pflicht und keine Empfehlung |
| A6 | `openproject/open_desk:17.7.2` startet ohne die openDesk-Umgebungsvariablen | Bildmarken | Nur relevant, wenn dieser Rückfall gezogen wird. Deshalb ist `openproject/openproject:17.7.2` der empfohlene Weg |
| A7 | Ein `rails runner` gegen `Doorkeeper::Application` könnte die OAuth-Anwendung seeden | Weg 1, Einrichtung | Ausdrücklich **nicht** benutzen: eine Behauptung über fremden Code ohne Beleg. Der UI-Weg ist der dokumentierte |
| A8 | Der `opendesk-openproject-bootstrap`-Job richtet `integration_openproject` im Modus `oauth2` ein, weil er die zwei Zugangsdatenpaare des Zwei-Wege-Weges hält | OD-01, ISV-Frage 7 | Der Bericht würde eine Betriebsart behaupten, die er nicht kennt. Deshalb steht das als **Indiz** und als ISV-Frage, nicht als Befund |
| A9 | `IUserSession::isLoggedIn()` antwortet unter AppAPI-Impersonation `true` | S5c | Die Diagnose von S5 wäre eine andere als die in `SUMMARY.md` vermutete. Deshalb ist S5c eine eigene, benannte Messung mit einer trennscharfen Log-Zeile |

---

## Open Questions (RESOLVED via Plan-Routing)

1. **Welcher Nextcloud-Stand macht die Kubernetes-Frage praktisch lösbar?**
   Was wir wissen: `app_api` 34 bringt `kubernetes-install` über HaRP mit vier Freigabearten und
   CI-Abdeckung; `app_api` 33 hat die Datei nicht.
   Was unklar ist: ob der Weg in 34 schon betriebsreif ist (es gibt keine Vorlage in der
   Admin-Oberfläche) und wann openDesk nachzieht.
   Empfehlung: als Quellenbefund in den Bericht, als Frage 5 auf die ISV-Liste, kein Messversuch in
   dieser Phase (D-01 schließt einen Cluster aus).
   RESOLVED: geroutet an Plan 17-01 (Quellenbefund in Abschnitt 1.2 des Berichts) und an Plan 17-08
   als ISV-Frage 5. Kein Messversuch in dieser Phase.

2. **Antwortet die OCS-Fläche von `integration_openproject` unter reiner AppAPI-Impersonation?**
   Was wir wissen: der CSRF-Weg über `OCS-APIRequest: true` ist in v1.2 für Nextcloud Mail bewiesen,
   und `OCS_HEADERS` setzt den Header auf jeder Anfrage. Die Controller-Attribute passen.
   Was unklar ist: das Verhalten dieser App in dieser Topologie.
   Empfehlung: S1, erste Messung von Stufe A, mit dem Antwortform-Kriterium aus `spike-mail.md`.
   RESOLVED: geroutet an Plan 17-05 als Messung S1 in Abschnitt 2.1, samt Gegenprobe mit 64 Nullen.

3. **Sind die OCS-Routen eine öffentliche Schnittstelle für andere Apps?**
   Was wir wissen: `christianlupus` hat am 28.08. im Nextcloud-Forum geantwortet, ohne die Frage zu
   beantworten, und rät zu einem Konto in der OpenProject-Community. Die Selbstregistrierung dort
   antwortet HTTP 400 "Registration not allowed".
   Empfehlung: zwei Entwürfe (D-11), Owner sendet. Der Rückkanal läuft nach dieser Phase weiter. Für
   den Bericht heißt das: Weg 0 kann als tragend gemessen werden und trotzdem eine offene
   Stabilitätsfrage haben. Beides muss dastehen.
   RESOLVED: geroutet an Plan 17-08 (zwei Entwürfe unter `docs/contrib/`, Statuszeile
   `nicht gesendet`, Owner sendet) und an Plan 17-09, das die offene Stabilitätsfrage neben dem
   Messergebnis von Weg 0 im Bericht stehen lässt.

4. **Lässt sich der Zwei-Wege-OAuth2-Weg lokal ohne die OpenProject-Oberfläche einrichten?**
   Was wir wissen: die Routen `POST /nc-oauth` und `POST /setup` existieren, und der openDesk-Bootstrap
   benutzt genau die zwei Zugangsdatenpaare, die dafür nötig wären.
   Was unklar ist: ihr Aufrufvertrag (Rumpfform, Reihenfolge, Vorbedingungen). Der Quellcode von
   `ConfigController` wurde für diese Recherche **nicht** gelesen.
   Empfehlung: erst den dokumentierten UI-Weg fahren. Wenn der hängt, `ConfigController` lesen, bevor
   geraten wird.
   RESOLVED: geroutet an Plan 17-03 (dokumentierter UI-Weg als Owner-Checkpoint, mit dem Rückfall
   "erst `ConfigController` lesen") und an Plan 17-08 als ISV-Frage 7 für die Betriebsart, die der
   openDesk-Bootstrap wirklich fährt.

5. **Was bedeutet ein tragender Weg 0 für die Werkzeugbreite von OD-04?**
   Was wir wissen: keine Route für ein einzelnes Arbeitspaket per Id, keine für Kommentare, keine für
   "meine Arbeit". Dafür gibt es `work-packages/{id}/file-links`, also genau die Kette Arbeitspaket zu
   Datei, die `research/FEATURES.md` als Unterscheidungsmerkmal führt.
   Empfehlung: als Abschnitt 3 des Berichts (API-Form) festhalten, ohne Entscheidung. Die Entscheidung
   ist OD-04.
   RESOLVED: geroutet an Plan 17-06 Task 3, der Abschnitt 3 des Berichts ohne Entscheidung schreibt;
   die Entscheidung selbst bleibt OD-04 in v2.0.

---

## Sources

### Primär (HIGH, Quellcode an gepinnten Tags oder eigene Messung)

**`nextcloud/integration_openproject`, Tag `v3.1.1`, gelesen 2026-08-28**
- `appinfo/routes.php` Zeilen 37-56: 15 OCS-Routen unter `/api/{apiVersion}` plus 2 Dateirouten
- `lib/Controller/OpenProjectAPIController.php` Zeilen 43-59 (`validatePreRequestConditions`),
  64-67 (`getOpenProjectUrl` **ohne** Vorprüfung, Befund K3), 79-80 (die einzige
  `#[NoCsrfRequired]`-Methode)
- `lib/Service/OpenProjectAPIService.php` Zeilen 551 (`requestOAuthAccessToken`), 586-604
  (Schreiben von `token`, `token_expires_at`, `refresh_token`), 1664-1719 (`getOIDCToken`),
  1726-1733 (`isAccessTokenExpired`, 60-Sekunden-Marge), 1740-1792 (`getAccessToken` samt der
  Kommentarzeilen 1764-1765), 1844-1860 (`isUserOIDCAppInstalledAndEnabled`, `isUserOIDCAppSupported`)
- `lib/TokenEventFactory.php` vollständig: die drei Ereignispfade (Befund K5)
- `lib/Capabilities.php` vollständig: `IPublicCapability` mit `app_version` (Befund K4)
- `lib/Service/SettingsService.php` Zeilen 19-38: alle Admin-Schlüssel beider Betriebsarten
- `lib/AppInfo/Application.php` Zeilen 59-72: `AUTH_METHOD_*`, `NEXTCLOUD_HUB_OIDC_PROVIDER_TYPE`,
  `EXTERNAL_OIDC_PROVIDER_TYPE`, `MIN_SUPPORTED_USER_OIDC_APP_VERSION = '7.2.0'`

**`nextcloud/user_oidc`, Tag `v8.11.0`, gelesen 2026-08-28**
- `lib/Service/TokenService.php` Zeilen 50 (`SESSION_TOKEN_KEY`), 92-94 (`getToken` liest die Sitzung),
  315-333 (`getExchangedToken` mit beiden Ausnahmen), 424-462 (`getTokenFromOidcProviderApp`, der
  sitzungsfreie Pfad über die `oidc`-App)
- `lib/Listener/{Internal,External,Exchanged}TokenRequestedListener.php`: alle drei beginnen mit
  `if (!$this->userSession->isLoggedIn()) { return; }`
- `lib/Command/UpsertProvider.php` Zeilen 180-190: Signatur von `occ user_oidc:provider`

**`nextcloud/app_api`, Zweige `stable33`, `stable34`, `stable35`, `main`, gelesen 2026-08-28**
- `lib/DeployActions/KubernetesActions.php`: fehlt auf `stable33`/`v33.0.0` (404), vorhanden auf
  `stable34`/`v34.0.0`/`stable35`/`main`; `DEPLOY_ID = 'kubernetes-install'` (Zeile 37),
  `buildHarpK8sUrl()` (Zeile 765). Eingeführt am 2026-02-22 (Befund K1)
- `lib/Command/Daemon/RegisterDaemon.php` Zeile 37 beider Zweige: die Aufzählung der zulässigen
  Deploy-Ids, plus Zeilen 54-60 in `stable34` (die sieben `--k8s*`-Optionen)
- `src/constants/daemonTemplates.js`: acht Vorlagen, davon `manual_install` (Zeile 195) und
  `manual_install_harp` (Zeile 92); **keine** Kubernetes-Vorlage, auch nicht in `stable34`
- `appinfo/info.xml`: `<version>` je Zweig (33.0.0, 34.0.0, 35.0.0, 36.0.0-dev.0)
- vier CI-Workflows `tests-deploy-k8s*.yml` und `tests/test_occ_commands_k8s.py`, nur ab `stable34`

**`opf/openproject`, Tag `v17.7.2`, gelesen 2026-08-28**
- `config/initializers/doorkeeper.rb` Zeilen 35-39 (`resource_owner_authenticator` verlangt eine
  Sitzung), 55 (`enforce_content_type`), 59 (`authorization_code_expires_in 10.minutes`), 64
  (`access_token_expires_in 2.hours`), 88-90 (`force_pkce`), 92-94 (`hash_token_secrets`,
  `hash_application_secrets`), 115 (`use_refresh_token`), 134-136 (`default_scopes :api_v3`,
  `optional_scopes :scim_v2, :mcp`) (Befund K2)
- `app/models/`: `oauth_client.rb`, `oauth_client_token.rb`; **kein** `app/models/doorkeeper/`

**`bmi/opendesk/deployment/opendesk` auf gitlab.opencode.de, Tag `v1.18.0`, gelesen 2026-08-28**
- `helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl` Zeilen 59-85 (`appstore: false`,
  `spreed: false`, `contacts: false`, `comments: false`, `circles: false`, `integrationOpenproject`
  schaltbar, `adminAudit` schaltbar), Zeilen 150-157 (Nextcloud-OIDC-Client `opendesk-nextcloud`)
- `helmfile/environments/default/images.yaml.gotmpl` Zeilen 344-351 (Nextcloud `33.0.7` samt Digest),
  404-413 (Nubus-Keycloak `26.7.0`), 716-725 (OpenProject `17.7.2`, Upstream `openproject/open_desk`)
- `helmfile/apps/openproject/values.yaml.gotmpl` Zeilen 38-41 (die Enterprise-Bedingung), 48
  (`OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"`), 73-74 (globale Basic-Auth mit dem API-Admin), 88
  (Keycloak-Issuer)
- `helmfile/apps/opendesk-openproject-bootstrap/values.yaml.gotmpl`, Abschnitt `config`: die zwei
  Zugangsdatenpaare, aber keine Einrichtungslogik
- `docs/architecture.md` Zeile 348: "openDesk pre-configures the trust between the openDesk instance's
  OpenProject and Nextcloud during the `openproject-boostrap` deployment step"
- Repository-weiter Griff durch das Archiv: **null** Treffer für `app_api`, `appapi`, `exapp`,
  `external app` (Befund K6)

**Eigene Live-Messungen, 2026-08-28**
- `community.openproject.org`: `.well-known/oauth-authorization-server`,
  `.well-known/oauth-protected-resource`; `GET /api/v3/work_packages/{24971, 999999999, 1}` mit den
  Statuscodes 200, 404, 404 und identischem Fehlerkörper für die beiden 404
- Docker Hub: `library/nextcloud` (Tag `33.0.7-apache` vorhanden),
  `openproject/openproject` (`17.7.2`, `17.7.2-slim`), `openproject/open_desk` (`17.7.2`, 419 MB),
  `openproject/community` (existiert nicht)
- quay.io: `keycloak/keycloak` (`26.7.0`, `26.7.2`)
- `https://apps.nextcloud.com/api/v1/platform/33.0.0/apps.json`: `integration_openproject` 3.1.1
  (`>=33.0.0 <35.0.0`), `user_oidc` 8.11.0 (`>=29.0.0 <36.0.0`)
- GitHub-Issue-API `nextcloud/user_oidc#925`: offen seit 2024-08-22, neun Kommentare, letzte
  Aktivität 2024-10-24
- `docker --version` -> 29.5.2; `command -v ctx7` -> nicht vorhanden
- `uv run python scripts/check_tool_budget.py` -> 15712 Bytes, 21 Werkzeuge, Budget 18000

**Eigene Codebasis, Release 0.1.11, gelesen 2026-08-28**
- `src/mcp_connector/oauth/cimd.py` Zeilen 1-9 (der Grund für das Modul), 168-201 (`target_allowed`),
  258-307 (`resolve_addresses`, die "ein schlechtes Ergebnis verwirft den ganzen Namen"-Regel)
- `tests/unit/test_oauth_cimd.py` Zeilen 179-222 und 669-675: der Negativkatalog, zweimal gefahren
- `src/mcp_connector/nextcloud/clients/ocs.py` Zeilen 38-43: `OCS_PREFIX` und `OCS_HEADERS` (D-18)
- `src/mcp_connector/nextcloud/capabilities.py` Zeilen 46-58, 154-198: der Capability- und der
  Navigations-Kanal
- `compose.exapp.yml` vollständig, `deploy/Caddyfile`, `scripts/bootstrap_exapp.sh` Kopf,
  `compose.test.yml`, `pyproject.toml` Zeilen 36-48, `appinfo/info.xml` Zeilen 183, 235, 257-258,
  `scripts/build_store_release.sh` Zeilen 40-50
- `docs/spike-dav.md`, `docs/spike-mail.md`, `docs/spike-discovery.md`, `docs/oauth-setup.md`
  Abschnitte "What the fetch of a document is allowed to do" und "Evidence"

### Sekundär (MEDIUM, Herstellerdokumentation, Abruf 2026-08-28)

- `openproject.org/docs/system-admin-guide/authentication/oauth-applications/`: Admin-Pfad
  *Administration, Authentication, OAuth applications*; Felder Name, Redirect URL, Scopes,
  Confidential, Client Credentials User; "Please note that your Bearer token will expire after two
  hours (default)"; PKCE nicht erwähnt
- `openproject.org/docs/api/introduction/`: "Authorization code flow with PKCE, recommended for clients
  unable to keep the client_secret confidential"; API-Token über Basic-Auth als `apikey`; die
  `scope`-Pflicht für ein OIDC-JWT
- `openproject.org/docs/installation-and-operations/installation/docker/`: `SECRET_KEY_BASE`,
  `OPENPROJECT_HOST__NAME`, `OPENPROJECT_HTTPS=false`; Vorgabe-Anmeldung `admin`/`admin`; erster Start
  dauert Minuten; nicht gleitende Tags für Produktion empfohlen
- `openproject.org/docs/installation-and-operations/system-requirements/`: mindestens Vierkern ab
  2 GHz, 4096 MB RAM, 20 GB Platte
- `openproject.org/docs/api/endpoints/users/`: `POST /api/v3/users` (Admin oder `manage_user`),
  `GET /api/v3/users`
- `docs.nextcloud.com/server/stable/admin_manual/exapps_management/DeployConfigurations.html`:
  HaRP als empfohlener Weg, Docker Socket Proxy als veraltet, `manual-install` neutral dargestellt,
  Beiläufiges zur Kubernetes-Logrotation über das kubelet
- `keycloak.org/server/importExport`: `--import-realm`, Importverzeichnis
  `/opt/keycloak/data/import`, eine vorhandene Realm wird übersprungen

### Tertiär (LOW, zu validieren)

- ZenDiS-Aufnahmeverfahren: öffentlich nicht auffindbar. Das ist selbst der Befund
- Betriebsreife des `kubernetes-install`-Daemons: die Datei und die CI-Abdeckung sind belegt, die
  Praxis nicht. Keine Vorlage in der Admin-Oberfläche von `stable34`
- Der in `research/STACK.md` und `research/PITFALLS.md` zitierte Satz, `manual-install` sei
  "ausdrücklich für Entwicklung oder Spezialfälle", ließ sich auf der heutigen Dokumentationsseite
  nicht wiederfinden. Nicht als Zitat verwenden

---

## Metadata

**Konfidenz je Bereich:**

| Bereich | Stufe | Grund |
|---------|-------|-------|
| OD-01, App Store und abgeschaltete Apps | **HIGH** | Datei, Zeile, Zitat an einem Tag, öffentlich nachprüfbar |
| OD-01, Kubernetes-Daemon und Versionsgrenze | **HIGH** | vier Zweige verglichen, zwei `occ`-Hilfetexte wörtlich, Commit-Datum, CI-Workflows |
| OD-01, AppAPI im openDesk-Image | **LOW** | das Image wird aus einem nicht mitgelesenen Projekt gebaut. Ausdrücklich als ISV-Frage geführt |
| OD-02 Weg 0, Fläche und Mechanik | **HIGH** | vollständige Routenliste mit Zeilen, drei Codestellen zur Tokenmechanik, ein Upstream-Kommentar als Beleg |
| OD-02 Weg 0, Verhalten unter Impersonation | **MEDIUM** | der CSRF-Weg ist in v1.2 für eine andere App live bewiesen, für diese nicht. Genau das ist S1 |
| OD-02 Weg 1, PKCE, Lebensdauer, Refresh | **HIGH** für die Erwartungswerte (Initializer an `v17.7.2`), **MEDIUM** für den Messweg (der Consent-Fluss ist neu in diesem Projekt gegen einen fremden AS) |
| OD-02, Zwei-Konten-Negativbeweis | **HIGH** für die Antwortform (dreimal live gemessen, 404 verrät die Existenz nicht), MEDIUM für den Aufbau des privaten Projekts |
| S5, OIDC-Bruchstelle | **HIGH** im Quellcode (drei Pfade, drei Bruchstellen, Zeilen genannt), **ungemessen** live. Der Rückfall auf "Quellcodebeleg plus offene Frage" ist ausdrücklich vorgesehen |
| SSRF-Grenze | **HIGH** | die Funktion, der Negativkatalog und das Docker-Subnetz sind alle im Repository gelesen. Die Messung ist eine Bestätigung, kein Wagnis |
| Messumgebung, Aufwand und Speicher | **MEDIUM bis LOW** | die Nextcloud-Hälfte ist erprobt, die OpenProject- und Keycloak-Hälfte ist geschätzt. Vier Annahmen im Assumptions Log |
| OD-03, Fragenliste | **HIGH** | jede Frage hat einen belegten Grund; drei Fragen der Ausgangsrecherche sind begründet entfernt |

**Gesamtkonfidenz: HIGH für die Quellenlage, MEDIUM für die lokale Messbarkeit.** Der Grund für die
zweite Hälfte ist ehrlich benannt: OD-01 ist nach dieser Recherche fast vollständig belegt, ohne dass
ein Container gestartet werden muss, während OD-02 an einem Aufbau hängt, dessen OpenProject- und
Keycloak-Teil in diesem Projekt neu ist. Die Zweistufigkeit und die Rückfälle in Pitfall 1 sind genau
dafür gebaut.

**Recherchedatum:** 2026-08-28
**Gültig bis:** 2026-09-28 für die Quellcodebefunde an gepinnten Tags (sie sind unveränderlich; was
altert, ist ihre Bedeutung, sobald openDesk oder eine der Apps nachzieht). **2026-09-04** für die
Fassungsangaben: `integration_openproject` hat am 2026-08-20 ein Nightly veröffentlicht,
`user_oidc` 8.11.0 ist vier Tage alt, und openDesk zieht laut eigener Versionshistorie schnell nach.
Vor dem ISV-Call am 14.09. ist ein erneuter Blick auf den openDesk-Tag und auf die
`app_api`-Zweigstände sinnvoll, weil Frage 5 der ISV-Liste an genau diesen Ständen hängt.

---

*Recherche abgeschlossen: 2026-08-28*
*Bereit für die Planung: ja. Ausdrückliche Maßgabe: OD-01 zuerst und ohne Docker, weil es billig und
fast abschließend belegt ist; die Messumgebung danach in zwei Stufen mit dem Schnitt vor Keycloak; und
S5 darf "ungemessen" bleiben, ohne dass die Phase scheitert.*
