---
phase: 17-opendesk-spike
plan: 05
subsystem: auth-measurement
tags: [spike, opendesk, od-02, weg-0, integration-openproject, ocs, capabilities, ssrf, d-12]
requires:
  - "17-02: Nextcloud 33.0.7 hinter Caddy auf 127.0.0.1:8091, ExApp mcp_connector 0.1.11 registriert, Konten alice und bob"
  - "17-03: OpenProject 17.7.2 auf 127.0.0.1:8082, Konten opa (id 5) und opb (id 6), privates Projekt spike-privat-b (id 3), Arbeitspaket 38"
  - "17-04: der Formularweg durch den Consent-Fluss von OpenProject, samt der 2FA- und der AAAA-Falle"
provides:
  - "integration_openproject 3.1.1 installiert und im Modus oauth2 gegen die lokale Instanz eingerichtet, alice mit opa und bob mit opb verbunden, carol bewusst unverbunden"
  - "K4 geschlossen: der Capability-Abschnitt integration_openproject steht unauthentifiziert in /ocs/v2.php/cloud/capabilities, mit app_version 3.1.1, IPublicCapability belegt, kein Navigations-Umweg noetig"
  - "S1 gemessen und nach Antwortform beurteilt: 200 mit OCS-Umschlag und der Instanzadresse als alice, Gegenprobe 64 Nullen 401 mit statuscode 997"
  - "S2 gemessen auf /api/v1/configuration: carol 401 mit leerer Meldung aus validatePreRequestConditions, alice und bob je 200 mit Daten"
  - "Zweite Gegenprobe zu S2: die zwei 401-Formen sind unterscheidbar (997 vom Kern gegen 401 der Vorpruefung), damit ist die 401 von carol nachweislich App-Code"
  - "Egress-Kontrolle gemessen und eingeordnet: aus dem ExApp-Container antwortet OpenProject unter dem Dienstnamen mit einer echten API-v3-Fehlerkennung, op.localtest.me dort aber nicht (::1)"
  - "17 OCS-Routen aus der installierten Fassung gezaehlt, die vier schreibenden und die eine freiwillig ausgeschlossene namentlich, kein Aufruf darauf"
  - "Der Einrichtungsweg ist belegt: Weg A gemessen nicht gangbar (SSRF-Schutz von OpenProject), gelaufen ist Weg B; Abschnitt 5.4 und DI-17-03"
  - "Vier Huerden des Einrichtungswegs als eigene Messwerte: nc_oauth_client_id, fresh_project_folder_setup, Origin-Pflicht der Nextcloud-Anmeldung, lokale Adresssperre von Nextcloud"
  - "NC_CAROL_PASSWORD in .env.spike-opendesk; allow_local_remote_servers=true als Zustand der Messumgebung"
affects:
  - "17-06 bekommt den vollstaendigen Ausgangszustand fuer S3, S4 und S6: zwei verbundene Konten mit refresh_token, Modus oauth2, und die Routentabelle samt Ausschlussliste"
  - "17-07 bekommt den unberuehrten OIDC-Zweig als Ausgangszustand (kein sso_provider_type, kein oidc_provider, kein token_exchange) und weiss, dass allow_local_remote_servers schon an ist"
  - "17-08 bekommt zwei Fragen mit Grund: setzt openDesk eine SSRF-Erlaubnisliste fuer den Bootstrap-Job, und laeuft integration_openproject dort im Modus oauth2 oder oidc"
  - "17-09 muss 2.5 ausformulieren; der Absatz zu Weg A ist dort vorgemerkt und darf nicht verloren gehen"
tech-stack:
  added: []
  patterns:
    - "Vor dem ersten Owner-Schritt die Vorbedingungen der Anweisung messen: eine Anweisung, die an der ersten Eingabe scheitert, kostet den Owner mehr als die Messung kostet"
    - "Einen Konfigurationsschalter nie von Hand setzen, wenn die App eine eigene Route dafuer hat: die Route liefert zusaetzlich das Urteil der App selbst (hier status true aus isAdminConfigOk)"
    - "Zwei gleiche Statuscodes an verschiedenen Stellen der Kette unterscheidbar machen (997 mit Meldung gegen 401 mit leerer Meldung), sonst beweist der Statuscode die Herkunft der Antwort nicht"
    - "Bei einer Erreichbarkeitsfrage immer auch den Namen messen, nicht nur die Adresse: dieselbe Zeichenkette bedeutet in drei Containern drei verschiedene Ziele"
    - "Eine erwartbar erfolgreiche Messung (Egress im Docker-Netz) im selben Absatz einordnen, in dem sie steht, nicht erst im Fazit"
key-files:
  created: []
  modified:
    - "docs/spike-opendesk.md"
    - ".planning/phases/17-opendesk-spike/deferred-items.md"
decisions:
  - "Der Owner hat am 28.08. Variante B mit skriptbarem Durchlauf gewaehlt; Weg A bleibt unausgefuehrt und steht als ungemessen mit Grund, nicht als verworfen (D-03)"
  - "Die zwei fehlenden Konfigurationswerte sind ueber die App-Routen POST /nc-oauth und PUT /admin-config gesetzt worden und nicht per occ von Hand, damit das gemessene Verhalten das echte ist und die App ihr eigenes isAdminConfigOk bestaetigt"
  - "allow_local_remote_servers=true ist als Eingriff in die Messumgebung dokumentiert und nicht stillschweigend gesetzt: ohne ihn ist Weg 0 lokal nicht messbar, und der Befund gehoert in den Bericht"
  - "Die Egress-Kontrolle wird nach Antwortform beurteilt und nicht nach Statuscode: die 400 der Host-Pruefung von Rails ist ein Erreichbarkeitsbeleg, die 401 mit der API-v3-Fehlerkennung der bessere"
  - "OD-02 bleibt Pending: dieser Plan misst von Weg 0 die drei ohne Tokenablauf beantwortbaren Fragen, S3 bis S6 fehlen. Fortsetzung der Entscheidung aus 17-01 bis 17-04"
metrics:
  duration: 78 min
  completed: 2026-08-28
---

# Phase 17 Plan 05: Weg 0 eingerichtet und in seiner ersten Hälfte gemessen Summary

Weg 0 arbeitet: `integration_openproject` 3.1.1 läuft auf Nextcloud 33.0.7 im Modus `oauth2` gegen die lokale OpenProject-Instanz, `alice` und `bob` sind mit `opa` und `opb` verbunden, `carol` bewusst nicht, und S1, S2, der Capability-Befund und die Egress-Kontrolle stehen mit je einer Gegenprobe im Bericht. Der teuerste Fund des Plans ist aber der Einrichtungsweg selbst: der dokumentierte Assistentenweg ist gemessen nicht gangbar, und beide Produkte sperren Loopback in der Vorgabe.

## Die drei Messwerte, die dieser Plan schuldig war

| Behauptung | Messweg | Messwert | Gegenprobe |
|-----------|---------|----------|------------|
| **Capability** (K4) | `GET /ocs/v2.php/cloud/capabilities`, **ohne** jede Anmeldung | **200**, 5 Abschnitte, 6440 Bytes, `integration_openproject` mit `app_version 3.1.1`, `groupfolder_version 0`, `groupfolders_enabled false` | derselbe Aufruf unter Impersonation von `alice`: 200, **23** Abschnitte, 11739 Bytes, dieselben drei Schlüssel. Der Unterschied 5 gegen 23 belegt, dass die erste Antwort wirklich die öffentliche Teilmenge ist |
| **S1**, Erreichbarkeit | `GET /api/v1/url` unter reiner AppAPI-Impersonation als `alice`, ohne App-Passwort im Prozess | **200**, OCS-Umschlag als JSON, `ocs.data = http://op.localtest.me:8082` | derselbe Aufruf mit 64 Nullen als `APP_SECRET`: **401**, `statuscode 997`, `Current user is not logged in` |
| **S2**, Berechtigung am Nutzer | `GET /api/v1/configuration` als `carol` (nie verbunden) | **401** im OCS-Umschlag, `statuscode 401`, **leere** Meldung, also `validatePreRequestConditions()` | derselbe Aufruf als `alice` **und** als `bob`: je **200** mit echten Werten der Instanz (`_type Configuration`, `hostName op.localtest.me:8082`, 1702 bzw. 1700 Bytes) |
| **Egress** | aus dem laufenden ExApp-Container `GET http://openproject/api/v3` | **400** `Invalid host_name configuration`, und mit `Host: op.localtest.me:8082` **401** mit `urn:openproject-org:api:v3:errors:Unauthenticated` | `GET http://op.localtest.me:8082/api/v3` aus demselben Container: `Connection refused`, Code `000`, weil der Name dort auf `::1` zeigt |

`IPublicCapability` ist damit nicht nur gelesen, sondern an einer Antwort ohne Zugangsdaten ablesbar: der Navigations-Umweg, den `capabilities.py` für Mail braucht, entfällt für diese App.

## Die Gegenprobe, die der Plan nicht verlangt hat und die S2 erst hart macht

Beide 401 dieses Plans hätten als "401, also abgewiesen" durchgehen können. Sie sind aber unterscheidbar, und genau das macht S2 zu einem Messwert über Berechtigungen statt über Erreichbarkeit:

| 401 | `statuscode` | Meldung | Herkunft |
|-----|--------------|---------|----------|
| S1-Gegenprobe, 64 Nullen | `997` | `Current user is not logged in` | Kern von Nextcloud, die Impersonation ist gescheitert |
| S2, `carol` | `401` | leer | `validatePreRequestConditions()` der App, die Anfrage ist angekommen |

Wer nur auf die Zahl 401 schaut, hält beide für dasselbe. Dann beweist S2 nichts, weil eine gescheiterte Impersonation dieselbe Zahl liefert.

## Der Einrichtungsweg war der eigentliche Aufwand, und er ist ein Befund

**Weg A, der dokumentierte Assistent, ist gemessen nicht gangbar.** Diese Messung ist vor dem ersten Klick entstanden, weil die Alternative gewesen wäre, dem Owner eine Anweisung vorzulegen, die an der ersten Eingabe scheitert.

- `NextcloudCompatibleHostValidator:48-53` der laufenden Fassung 17.7.2 prüft den Namen mit `OpenProject::SsrfProtection.safe_ip?`, **vor** jedem Netzaufruf. Per `rails runner` in derselben Instanz gemessen: `nil` für `127.0.0.1`, `caddy`, `nextcloud`, `op.localtest.me` und `localhost`, Erlaubnisliste leer. `127.0.0.0/8` und `172.16.0.0/12` sind beide gesperrt, und `Resolv::DNS` liefert für `caddy` genau `172.29.43.10`.
- **Gegenprobe:** die zwei Netzaufrufe danach gelingen beide gegen `http://caddy`: Capabilities **200** mit `version.major 33`, `check-config` **200** mit wörtlich zurückgegebenem `Bearer TESTBEARERTOKEN`. Es scheitert ausschließlich der Namenscheck, nicht die Erreichbarkeit und nicht die fachliche Bedingung.
- `ssrf_protection_ip_allowlist` trägt `writable: false`, ist also nur über die Umgebung des Containers setzbar. Weg A kostet damit ein Neuerzeugen des OpenProject-Containers plus einen für beide Seiten gleichlautenden Namen, den die Topologie heute nicht hergibt. Das liegt als DI-17-03 mit Kostenschätzung und benanntem ungemessenen Teil bereit.

**Weg B verlangt fünf Werte, nicht vier.** Der Plan nennt vier `occ`-Schlüssel. `GET /op-oauth-url` antwortete damit **500** mit `OpenProject admin config is not valid!`. Ursache, aus der Prüfkette der App gelesen: `isAdminConfigOkForOauth2:931-934` verlangt zusätzlich `nc_oauth_client_id`, und `isCommonAdminConfigOk:902-911` verlangt `fresh_project_folder_setup` **aus**, während die Installationsmigration es auf `1` setzt (gemessen direkt nach `app:install`).

Beides ist **nicht** von Hand gesetzt, sondern über die zwei Routen, die die App selbst dafür mitbringt:

| Schritt | Aufruf | Messwert |
|---------|--------|----------|
| Nextcloud-seitige OAuth-Anwendung | `POST /nc-oauth` als Admin | 200, `nc_oauth_client_id = 1`, dazu die Rückadresse, die Weg A auf der OpenProject-Seite eingetragen hätte |
| Setup-Schalter | `PUT /admin-config` mit beiden Setup-Schaltern `false` | 200, wörtlich `{"status":true,...,"oPUserAppPassword":null}`, danach `fresh_project_folder_setup = 0` |

Die `"status": true` ist `isAdminConfigOk()` aus der App selbst und nicht unsere Auslegung ihrer Bedingungen. `setup_app_password` und `setup_project_folder` bleiben leer und `oPUserAppPassword` ist `null`: es liegt kein App-Passwort im Prozess, S1 bleibt aussagekräftig (T-17-03).

## Der persönliche Durchlauf lief ohne Browser, mit zwei Fallen

Der Plan sah dafür einen Owner-Schritt in zwei Oberflächen vor. Gemessen ist er per Formular gelaufen, für beide Konten, in neun Schritten. Zwei Hürden darin sind eigene Messwerte:

1. **Ohne `Origin`-Kopf keine Anmeldung.** `POST /login` antwortete `303` auf `/login?direct=1&user=alice`, im Protokoll `Login failed: 'alice'`, was wie ein falsches Passwort aussieht. Es war keines: dieselben Zugangsdaten antworten per Basic-Auth auf `/ocs/v2.php/cloud/user` mit **200**, ein falsches Passwort dort mit **401**. Der Grund steht in `core/Controller/LoginController.php:307-314`: ein leerer `Origin` bricht ab, **bevor** das Passwort geprüft wird. Mit `Origin: http://127.0.0.1:8091` endet derselbe Aufruf `303` auf `/apps/dashboard/`.
2. **Auch Nextcloud verweigert Loopback.** Der Rückweg antwortete `303`, die Verbindung stand aber nicht: `oauth_connection_error_message` lautete wörtlich `Error getting OAuth access token. Host "127.0.0.1" (op.localtest.me:80) violates local access rules`. Die Meldung nennt die **öffentliche** Auflösung `127.0.0.1` und nicht die `172.29.43.10` aus `extra_hosts`, und Port `80` statt `8082`. Aufgelöst mit `occ config:system:set allow_local_remote_servers --value=true --type=boolean`, danach `oauth_connection_result = success`.

**Der Befund dahinter:** beide Produkte sperren Loopback- und private Adressen in der Vorgabe, jedes mit einem eigenen Mechanismus an einer anderen Stelle der Kette. Ein lokaler Weg-0-Spike braucht auf **jeder** Seite eine Lockerung; gefallen ist hier nur die Nextcloud-Seite, zur Laufzeit. Für openDesk sagt das nichts, weil dort beide Seiten routbare Adressen haben, und der Bericht sagt das ausdrücklich.

## Der Zustand nach der Einrichtung, je Konto gelesen

| Konto | `oauth_connection_result` | OpenProject-Identität | `token_expires_at` |
|-------|---------------------------|------------------------|--------------------|
| `alice` | `success` | `Alice Spike`, `user_id 5` | `1787949009`, Restlaufzeit 7181 s |
| `bob` | `success` | `Bob Spike`, `user_id 6` | `1787949020`, Restlaufzeit 7192 s |
| `carol` | Schlüssel existiert nicht | Schlüssel existiert nicht | Schlüssel existiert nicht |

Die Ids sind der Beleg, dass die Zuordnung die beabsichtigte ist: `5` ist `opa`, `6` ist `opb`, und `opb` ist das Mitglied des privaten Projekts aus 5.3. Der Negativbeweis von 17-06 steht damit auf derselben Asymmetrie wie der von 2.2. Die rund 7200 Sekunden sind derselbe Wert, den 2.2 als `expires_in` gemessen hat, hier über einen zweiten, unabhängigen Weg.

## Deviations from Plan

**1. [Rule 3 - Die Anweisung des Plans hätte an der ersten Eingabe gescheitert] Weg A vorab gemessen statt vorgelegt**
- **Gefunden bei:** Task 2, vor dem Checkpoint
- **Problem:** Schritt 1 der `how-to-verify` wollte den Owner `http://127.0.0.1:8091` in das Feld Host des Assistenten eintragen lassen. Aus dem OpenProject-Container ist das `code=000`, und der SSRF-Schutz weist ohnehin jeden hier möglichen Namen ab. Ein vorgelegter Checkpoint hätte den Owner in eine Sackgasse geschickt.
- **Fix:** Die Vorbedingungen der Anweisung gemessen (vier Erreichbarkeitswerte, `safe_ip?` für fünf Namen, leere Erlaubnisliste, zwei Validator-Aufrufe als Gegenprobe), Abschnitt 5.4 geschrieben und dem Owner eine Entscheidung mit exakten Werten und einer Empfehlung vorgelegt.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 6f435e1

**2. [Rule 3 - Der Plan nennt vier Pflichtwerte, gemessen sind fünf] `nc_oauth_client_id` und `fresh_project_folder_setup`**
- **Gefunden bei:** Task 2, nach dem Freigabesignal
- **Problem:** Mit den vier Schlüsseln des Plans antwortete `GET /op-oauth-url` mit 500 und `OpenProject admin config is not valid!`. Ohne diesen Fund wäre Weg B als "geht nicht" gescheitert, obwohl er trägt.
- **Fix:** Die Prüfkette gelesen, die zwei fehlenden Bedingungen über die App-Routen `POST /nc-oauth` und `PUT /admin-config` erfüllt, mit beiden Setup-Schaltern aus. Die App bestätigt selbst `"status": true`.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 863cf9e

**3. [Rule 1 - Ein Messwert, der wie ein falsches Passwort aussieht] Origin-Pflicht der Anmeldung**
- **Gefunden bei:** Task 2
- **Problem:** `POST /login` scheiterte mit `Login failed: 'alice'`. Ein Abbruch hier hätte in den Browser-Rückfall geführt, obwohl der Formularweg trägt, und der Bericht hätte eine falsche Ursache genannt.
- **Fix:** Mit Basic-Auth gegengeprobt (200, falsches Passwort 401), also kein Passwortproblem, dann `LoginController.php:307-314` gelesen und den `Origin`-Kopf gesetzt. Als Messwert im Bericht, damit ein Wiederholungslauf ihn nicht falsch liest.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 863cf9e

**4. [Rule 3 - Ohne Eingriff kein Weg 0 auf Loopback] `allow_local_remote_servers`**
- **Gefunden bei:** Task 2
- **Problem:** Der Token-Tausch scheiterte an Nextclouds Prüfung auf lokale Adressen, mit einer wörtlich protokollierten Meldung. Ohne diese Einstellung ist Weg 0 in dieser Topologie überhaupt nicht messbar.
- **Fix:** Die dafür vorgesehene Systemeinstellung gesetzt, den Vorher- und Nachher-Zustand gelesen, und den Eingriff samt der wörtlichen Meldung in den Bericht geschrieben statt ihn stillschweigend zu machen. Der Befund "beide Produkte sperren Loopback in der Vorgabe" ist dabei entstanden.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 863cf9e

**5. [Rule 2 - Der Plan verlangt eine Gegenprobe, die zwei erst hart machen] Die zwei 401-Formen unterschieden**
- **Gefunden bei:** Task 3
- **Problem:** S1-Gegenprobe und S2 liefern beide 401. In dieser Form wäre die 401 von `carol` auch mit einer gescheiterten Impersonation erklärbar, und S2 hätte über Berechtigungen nichts bewiesen.
- **Fix:** Beide Antworten vollständig protokolliert und die Unterscheidung als eigene Tabelle in den Bericht genommen: `997` mit Meldung vom Kern gegen `401` mit leerer Meldung aus der Vorprüfung.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** ab60f4b

**6. [Rule 2 - Ein Pfad im Auftrag war nicht der Pfad der Route] Kontrolle des OCS-Präfixes**
- **Gefunden bei:** Task 3
- **Problem:** Der Auftrag nennt für S2 einmal `/index.php/apps/integration_openproject/api/v1/configuration`. Die Route liegt im Block `'ocs' => [`, also unter `/ocs/v2.php/apps/...`. Eine Messung auf dem falschen Präfix hätte eine 404 geliefert und wie "Route fehlt" gelesen.
- **Fix:** S2 auf dem OCS-Präfix gemessen und den anderen Präfix als eigene Kontrollzeile mitgemessen: **404** mit leerem Körper. Damit ist die Ambiguität mit einem Messwert aufgelöst und nicht mit einer Auslegung.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** ab60f4b

**7. [Rule 2 - Die Egress-Messung des Plans wäre missverständlich geblieben] Vier Zeilen statt einer**
- **Gefunden bei:** Task 3
- **Problem:** Der Plan verlangt einen Aufruf. Die 400 der Host-Prüfung von Rails hätte allein wie "Egress fehlt" gelesen werden können, und ohne die Namensmessung wäre offen geblieben, warum der Dienstname zu nehmen ist.
- **Fix:** Vier Zeilen gemessen: ohne Host-Kopf 400, mit dem erwarteten Host 401 mit der API-v3-Fehlerkennung (der eigentliche Beleg), `op.localtest.me` `Connection refused`, dazu `getent` mit `::1`. Die AAAA-Falle ist damit im dritten Container belegt.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** ab60f4b

**8. [Rule 1 - Verstoß gegen eine Projektregel im eigenen Text] Vokabular-Gate**
- **Gefunden bei:** Task 3, beim Lauf von `uv run pytest -q`
- **Problem:** Der Text von Task 1 enthielt das verbotene Wort in `App-Archiv`. Der Test `test_no_public_markdown_page_carries_the_forbidden_vocabulary` war rot, und der Commit von Task 1 war schon gesetzt.
- **Fix:** Umformuliert zu `von Hand geladenes Paket der App`, Suite danach grün. Lehre für Folgepläne: dieses Gate hängt an `docs/` insgesamt und läuft nicht in den Gates der Pläne mit, deshalb `pytest` nach jedem Schreibschritt und nicht erst am Ende.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** ab60f4b

**9. [Rule 2 - Ein Stub eines Folgeplans hätte den Befund verschluckt] Weg A in 2.5 vorgemerkt**
- **Gefunden bei:** nach Task 3
- **Problem:** Dass Weg A ungemessen bleibt, gehört nach 2.5, und 2.5 gehört 17-09. Ohne Vormerkung hätte 17-09 den Punkt nur über diesen Plantext gefunden.
- **Fix:** Ein ausdrücklich als "vorgemerkt aus Abschnitt 2.1" gekennzeichneter Absatz in 2.5, die Zeile `noch nicht gemessen, Plan 17-09` bleibt stehen. Dazu DI-17-03 mit Kostenschätzung. Dasselbe Muster wie Abweichung 1 in 17-04.
- **Dateien:** `docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`
- **Commit:** 8182a58

**10. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01 bis 17-04] OD-02 bleibt Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter nennt `requirements: [OD-02]`, und `requirements mark-complete` hätte OD-02 abgehakt. OD-02 verlangt Weg 0 und Weg 1 mit Messwerten nebeneinander; von Weg 0 fehlen S3 bis S6.
- **Fix:** OD-02 bleibt `Pending` und wird von 17-09 abgehakt.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

**11. [Bekannte Gate-Eigenheit, nicht behoben, hier benannt] `grep -v '^#'` entfernt jede Überschrift**
- **Gefunden bei:** Task 1 und Task 3, beim Lauf der Gates
- **Problem:** Dieselbe Eigenheit, die 17-03 als Abweichung 7 und 17-04 als Abweichung 9 gemeldet haben: der Filter entfernt auch Markdown-Überschriften, und der `artifacts`-Eintrag verlangt `contains: "### 2.1"`.
- **Fix:** Nicht umgeschrieben. Beide Prüfungen gefahren und beide grün: der gefilterte Griff für die inhaltlichen Zeichenketten, ein ungefilterter `grep -q "### 2.1"` für die Überschrift.
- **Dateien:** keine
- **Commit:** keiner

Sonst keine. Insbesondere ist keine der fünf ausgeschlossenen Routen ausgelöst worden, kein `client_credentials`-Lauf gefahren, und der API-Schlüssel des Kontos `admin` kommt in keinem Messwert dieses Plans vor.

## Authentication Gates

**Einer, und er war echt.** Der Checkpoint aus Task 2 wurde vorgelegt und vom Owner am 28.08. mit `freigegeben, skriptbar` und der Wahl von Variante B beantwortet. Owner-Schritt war die Registrierung der zweiten OAuth-Anwendung `nc-mcp-spike-weg0` in OpenProject (vertraulich, Rückadresse aus `IURLGenerator::getAbsoluteURL` gemessen, `Client Credentials User ID` leer) und das Ablegen von `NC_OP_CLIENT_ID` und `NC_OP_CLIENT_SECRET` in der git-ignorierten Verbindungsdatei. Beide Werte sind mit 43 Zeichen vorhanden, wurden nur über ihre Länge geprüft und stehen in keiner verfolgten Datei, in keinem Protokoll und nicht in diesem SUMMARY.

Der zweite vom Plan vorgesehene Owner-Schritt, der persönliche Zustimmungsdurchlauf in zwei Oberflächen, war nach der Freigabe **nicht** nötig: der Formularweg trug für beide Konten.

## Verification

- Task-1-Gate: `occ app:list` nennt `integration_openproject: 3.1.1`, die Capability-Antwort enthält `integration_openproject`, `IPublicCapability` steht im Bericht.
- Task-2-Gate: `authorization_method = oauth2`, `openproject_instance_url = http://op.localtest.me:8082`, `alice` und `bob` je ein `token_expires_at` in der Zukunft (7181 s und 7192 s Restlaufzeit), `carol` ohne `token`, `setup_app_password` nicht `1` (leer).
- Task-3-Gate: `api/v1/configuration`, `carol` und `file-links` im Bericht gefunden, 12 Vorkommen von `noch nicht gemessen`, kein `AUTHORIZATION-APP-API`-Wert und kein JWT-Muster.
- `artifacts`-Eintrag: `grep -q "### 2.1"` ungefiltert grün (siehe Abweichung 11). `key_links`-Muster `openproject_instance_url` steht in 2.1 und im Konfigstand.
- Routenzählung im Bericht maschinell nachgezählt: **17** Zeilen, so viele wie der Block `'ocs' => [` der installierten Fassung hat.
- Geheimnis-Gate: `git grep -F` über die Werte von `APP_SECRET`, `HP_SHARED_KEY`, `OP_API_TOKEN`, `OP_ADMIN_PASSWORD`, `OP_OAUTH_CLIENT_ID`, `OP_OAUTH_CLIENT_SECRET`, `OP_USER_A_PASSWORD`, `OP_USER_B_PASSWORD`, `NC_CAROL_PASSWORD`, `SECRET_KEY_BASE`, `NC_OP_CLIENT_ID`, `NC_OP_CLIENT_SECRET` und `NC_MCP_TEST_APP_PASSWORD`: kein Treffer. Muster-Gate über den Bericht ebenfalls ohne Treffer.
- Pitfall-2-Griff über den Bericht: sieben Treffer, alle an den zwei aus 17-04 bekannten und dort eingeordneten Stellen (Metadatenzitat samt Absatz in 2.2, Absatz in 5.3). Der neue Text dieses Plans fügt keinen hinzu.
- `uv run pytest -q` mit `env -u APP_ID -u APP_SECRET -u APP_VERSION`: grün, dreimal gefahren (einmal rot wegen Abweichung 8, danach zweimal grün).
- Kein U+2014 und kein U+2013, kein Zeichen oberhalb U+2600, keine ASCII-Ersatzschreibung von Umlauten, 0 CRLF in beiden geänderten Dateien.
- `git status --short src/ appinfo/ pyproject.toml uv.lock`: leer, nach jedem der fünf Commits geprüft. `files_modified` des Plans nennt keinen Pfad unter `src/` (D-12); `capabilities.py` und `ocs.py` wurden nur gelesen. Werkzeugoberfläche und Budget-Gate sind nicht angefasst.
- Keiner der fünf Commits löscht eine verfolgte Datei; `git status --short` ist nach dem letzten leer.
- Loopback: jeder Aufruf ging an `127.0.0.1:8091`, `op.localtest.me:8082` (löst auf `127.0.0.1` auf) oder an einen Compose-Dienstnamen aus dem Netz `172.29.43.0/24`. Kein Aufruf an eine fremde Adresse, nichts an einen Dritten gesendet, keine gemietete Infrastruktur, kein `wsl --shutdown`, keine `.wslconfig`, keine fremden Container angefasst (die zwei Container fremder Projekte laufen unverändert).
- Das Messskript für den persönlichen Durchlauf liegt im Temporärverzeichnis und **nicht** im Repository (D-12). Cookie-Speicher und Zwischendateien der Messung sind gelöscht.

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: 2.4 und 2.5 (17-09), 3 (17-09), 4 (17-08), "Was diese Messung nicht beweist" (17-09), sowie in 2.1 die Zeilen S3, S4 und S6 (17-06) und S5a/b/c (17-07). Die Kopfzeilen `user_oidc` und Keycloak bleiben `noch nicht gemessen (Plan 17-07)`.

Zwei Stubs, die ausdrücklich Stubs bleiben, aber jetzt einen vorgemerkten Absatz tragen: Abschnitt 4 (Frage 9, aus 17-04) und Abschnitt 2.5 (Weg A ungemessen, dieser Plan). Beide behalten ihre Zeile `noch nicht gemessen` mit Planzuordnung.

Kein Stub verhindert das Ziel dieses Plans: die App ist eingerichtet, und die drei ohne Tokenablauf beantwortbaren Fragen (Erreichbarkeit, Capability, Berechtigung am Nutzer) tragen Messwerte mit Gegenproben.

## Threat Flags

Keine neue Fläche über das Bedrohungsmodell des Plans hinaus. Fünf Anmerkungen zu Einträgen daraus, dazu eine neue Fläche der Messumgebung, die benannt sein muss:

- **T-17-01 (Information Disclosure), gehalten:** kein `AUTHORIZATION-APP-API`-Wert, kein Token, kein Client-Secret und kein Passwort steht in einer verfolgten Datei, in einem Protokoll oder in diesem SUMMARY. Genannt werden Längen, Statuscodes, Content-Types, Bytezahlen und Feldnamen. Der PKCE-Verifier, den `occ user:setting` beim Auslesen anzeigt, ist nicht in den Bericht übernommen.
- **T-17-03 (Elevation of Privilege), gehalten und belegt:** `setup_app_password` und `setup_project_folder` sind nach der Einrichtung leer, `oPUserAppPassword` ist `null`, es liegt kein App-Passwort im Prozess. Die OAuth-Anwendung hat `Client Credentials User ID` leer. Jede Messzeile nennt ihr Konto.
- **T-17-05 (Repudiation), gehalten und über den Plan hinaus:** jeder Messwert trägt seine Gegenprobe, und für S2 ist eine zweite dazugekommen, ohne die der Statuscode die Herkunft der Antwort nicht belegt (Abweichung 5).
- **T-17-02 (Tampering), gehalten:** keine der vier schreibenden oder destruktiven Routen und auch nicht die freiwillig ausgeschlossene Formularroute ist aufgerufen worden. Gefahren sind ausschließlich `GET /api/v1/url`, `GET /api/v1/configuration` und `/ocs/v2.php/cloud/capabilities`. Arbeitspaket 38 ist unverändert.
- **T-17-04 (Tampering), gehalten:** nur `docs/spike-opendesk.md` und `deferred-items.md` sind geschrieben; `ocs.py` und `capabilities.py` wurden gelesen.
- **Neu und benannt, kein Flag der ausgelieferten App:** `allow_local_remote_servers = true` ist eine Lockerung **der Messumgebung**. Sie erlaubt dieser Nextcloud-Instanz ausgehende Anfragen an lokale und private Adressen und ist der Grund, warum Weg 0 hier überhaupt messbar ist. Sie betrifft die Instanz, nicht diese ExApp, sie steht im Bericht und in diesem SUMMARY, und sie darf beim Nachbau nicht unbemerkt bleiben. Für eine openDesk-Installation ist sie ohne Bedeutung, weil dort beide Seiten routbare Adressen haben.

## Hinweise für die Folgepläne

1. **Der Ausgangszustand für 17-06 steht vollständig.** `alice` (mit `opa`, id 5) und `bob` (mit `opb`, id 6) tragen `token`, `refresh_token` und `token_expires_at` rund 7200 s in der Zukunft, Modus `oauth2`. Für S4 gilt die Anweisung aus der Recherche unverändert: `occ user:setting <u> integration_openproject token_expires_at 0`.
2. **Zwei Aufrufe je Messzeile, nicht einer.** Ein Statuscode allein sagt in dieser App nicht, woher die Antwort kommt. Die Unterscheidung `997` gegen `401` mit leerer Meldung ist der billigste Weg, das zu belegen.
3. **Für 17-07 (OIDC):** der OIDC-Zweig ist unberührt (kein `sso_provider_type`, kein `oidc_provider`, kein `token_exchange`), `allow_local_remote_servers` ist schon `true`, und `nc_oauth_client_id = 1` existiert. Ein Wechsel von `oauth2` auf `oidc` löst nach `ConfigController` einen Reset des jeweils anderen Zweigs aus: erst lesen, dann schalten, sonst sind die Tokens von `alice` und `bob` weg.
4. **Der Formularweg durch beide Oberflächen ist automatisierbar**, und die drei Fallen darin sind: `Origin`-Kopf bei der Nextcloud-Anmeldung (sonst `Login failed`), `curl -L` beim OpenProject-Login (2FA-Umweg aus 17-04), und auf der Zustimmungsseite trägt das Formular **kein** `authenticity_token`-Feld, sondern nur `<meta name="csrf-token">`, das als Kopf `X-CSRF-Token` zu senden ist (sonst 500).
5. **`curl -4` und Dienstnamen.** Die AAAA-Falle von `localtest.me` ist jetzt in drei Containern belegt. Aus dem ExApp-Container ist `openproject` der einzige tragende Name, aus dem Nextcloud-Container `op.localtest.me` (über `extra_hosts`), aus dem OpenProject-Container `caddy` oder `nextcloud`.
6. **Für 17-08 zwei Fragen mit Grund:** setzt openDesk eine SSRF-Erlaubnisliste, damit der Bootstrap-Job den Ablagen-Assistenten fahren kann (aus 5.4), und läuft `integration_openproject` dort im Modus `oauth2` oder `oidc` (schon als offener Punkt in 1.4, jetzt mit dem Zusatzargument, dass nur der `oauth2`-Zweig serverseitig erneuert).
7. **Für 17-09:** 2.5 muss den vorgemerkten Absatz zu Weg A ausformulieren, und 2.4 kann jetzt entscheiden, sobald 17-06 und 17-07 ihre Zeilen tragen. DI-17-03 nennt die Kosten einer Weg-A-Messung, falls der Vergleich sie verlangt.
8. **Die drei Exporte vor jedem compose-Kommando gelten weiter** (`set -a && . ./.env.spike-opendesk && set +a`), `pytest` braucht weiter `env -u APP_ID -u APP_SECRET -u APP_VERSION`, und das Vokabular-Gate hängt an ganz `docs/`: `pytest` nach jedem Schreibschritt laufen lassen, nicht erst am Ende (Abweichung 8).

## Self-Check: PASSED

Die zwei genannten Dateien existieren (`docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`), und alle fünf Commit-Kennungen (fa57350, 6f435e1, 863cf9e, ab60f4b, 8182a58) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` ist grün, und kein Wert aus `.env.spike-opendesk` steht im verfolgten Baum. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt; wo eine Messung fehlt (Weg A, die Fehlermeldung des Assistenten in der Oberfläche, das Auflösungsverhalten von `httpx` unter der Erlaubnisliste, S3 bis S6), sagt der Text das mit dem Wort `ungemessen` und nicht als Vermutung.
