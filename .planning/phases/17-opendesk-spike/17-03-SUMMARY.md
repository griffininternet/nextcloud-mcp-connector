---
phase: 17-opendesk-spike
plan: 03
subsystem: measurement-environment
tags: [spike, opendesk, od-02, openproject, stufe-b, oauth, zwei-konten, aufbau]
requires:
  - "17-02: compose.spike-opendesk.yml mit dem Profil op, Caddy-Block :8082, laufende Stufe A, .env.spike-opendesk"
  - "17-01: docs/spike-opendesk.md mit Kopfblock und Abschnittsgerüst"
provides:
  - "OpenProject 17.7.2 laufend im Profil op, erreichbar ausschließlich über Caddy auf 127.0.0.1:8082"
  - "Berichtskopf mit OpenProject 17.7.2, Digest sha256:19a828d6 und coreVersion 17.7.2 aus der laufenden Instanz"
  - "Abschnitt 5.1: erster Start gemessen (95 Sekunden, 1,964 GiB) gegen die erwarteten 30 bis 90 Minuten und mindestens 4 GB"
  - "Abschnitt 5.2: Namensfalle in beide Richtungen gemessen, mit remote_ip als Gegenprobe"
  - "Abschnitt 5.3 'Aufbau, nicht Messung': zwei Konten (opa id 5, opb id 6), privates Projekt spike-privat-b (id 3), Arbeitspaket SPIKE-OD-8471 privat (id 38), Mitglied nur opb"
  - "OAuth-Anwendung nc-mcp-spike-weg1 als öffentlicher Client, Feld Client Credentials User ID leer, im Bericht als Satz festgehalten"
  - "OP_ADMIN_PASSWORD, OP_API_TOKEN, OP_OAUTH_CLIENT_ID, OP_OAUTH_CLIENT_SECRET, OP_USER_A_PASSWORD, OP_USER_B_PASSWORD, OP_WP_ID in der git-ignorierten .env.spike-opendesk"
  - "DI-17-01 in deferred-items.md: OpenProject 17.7.2 bringt einen eigenen MCP-Server mit, ungemessen"
affects:
  - "17-04 kann Weg 1 messen: die OAuth-Anwendung ist ein nicht vertraulicher Client, force_pkce steht in doorkeeper.rb:90, Redirect-URI http://127.0.0.1:8099/callback"
  - "17-05 richtet integration_openproject ein und muss op.localtest.me:8082 als openproject_instance_url benutzen; der AAAA-Eintrag von localtest.me auf ::1 ist die erste Fehlerquelle, nicht die Caddy-Regel"
  - "17-04 und 17-06 fahren den Zwei-Konten-Negativbeweis unter opa und opb gegen Arbeitspaket 38; der Grundzustand steht, der Beweis selbst ist in diesem Plan ausdrücklich nicht geführt"
  - "17-08 bekommt aus DI-17-01 eine Frage mit Grund für den ISV-Call am 14.09."
  - "17-09 füllt 2.1, 2.2, 2.4, 2.5 und Abschnitt 3; 5.1 bis 5.3 stehen als Eingangswerte bereit"
tech-stack:
  added:
    - "openproject/openproject:17.7.2 (Profil op, jetzt laufend, Digest sha256:19a828d6, erstellt 2026-08-13, 882512785 Bytes)"
  patterns:
    - "Fassung dreifach belegen: Digest der Bildmarke, Quelldatei im Container, API der laufenden Instanz. Fällt eine Belegstelle aus, tritt eine andere an ihre Stelle statt die Aussage abzuschwächen"
    - "Aufbau und Messung im Bericht namentlich trennen, und den Zugang, der den Aufbau erzeugt hat, ausdrücklich aus der gemessenen Kette herausnehmen"
    - "Erwartungswerte aus der Recherche als Behauptung führen und gegen den Messwert stellen, auch wenn der Messwert günstiger ist als die Erwartung"
key-files:
  created:
    - ".planning/phases/17-opendesk-spike/deferred-items.md"
  modified:
    - "docs/spike-opendesk.md"
    - ".env.spike-opendesk.example"
decisions:
  - "Die dritte Belegstelle für die Fassung ist die Quelldatei /app/lib/open_project/version.rb im Container und nicht die Fußleiste der Anmeldeseite, weil 17.7.2 dort keine Fassung ausgibt"
  - "Der Zwei-Konten-Negativbeweis wird in diesem Plan NICHT vorweggenommen, obwohl die Passwörter beider Konten vorliegen: der Plan weist ihn 17-04 und 17-06 zu, und ein hier gefahrener Beweis hätte Aufbau und Messung im selben Plan vermischt"
  - "OD-02 bleibt Pending, weil dieser Plan nur den Grundzustand liefert und keinen der beiden Wege misst (Fortsetzung der Entscheidung aus 17-01 und 17-02)"
  - "Der nativen MCP-Server von OpenProject wird in dieser Phase nicht gemessen, sondern als zurückgestellter Fund geführt, damit der Stufenschnitt aus Pitfall 1 hält"
metrics:
  duration: 48 min
  completed: 2026-08-28
---

# Phase 17 Plan 03: Stufe A vollständig, OpenProject 17.7.2 und der Grundzustand des Negativbeweises Summary

Stufe A ist vollständig: OpenProject 17.7.2 läuft gepinnt hinter Caddy auf `127.0.0.1:8082`, dieselbe Adresse führt aus Browser und Nextcloud-Container an dieselbe Instanz, und der Grundzustand, ohne den der Zwei-Konten-Negativbeweis beider Wege leer wäre, existiert und ist im Bericht als Aufbau und nicht als Messung gekennzeichnet.

## Das teuerste erwartete Risiko ist nicht eingetreten

Aus 17-02 lief die Warnung mit, dass die WSL2-VM nur 7,6 GiB hat und OpenProject der speicherhungrigste Teil der Phase ist. Gemessen ist die Erwartung deutlich übertroffen worden, und beide Zahlen stehen mit Behauptung, Messweg, Messwert und Gegenprobe in Abschnitt 5.1:

| Behauptung aus 17-RESEARCH.md | Messwert am 2026-08-28 |
|-------------------------------|------------------------|
| erster Start 30 bis 90 Minuten, davon meist Warten | **95 Sekunden**, von 16:42:38 UTC bis zur ersten 200 auf `/login` um 16:44:14 UTC |
| OpenProject allein mindestens 4 GB RAM | **1,964 GiB**, 25,83 Prozent der VM, danach 4036 MiB verfügbar |
| 20 GB Platte | 925 GiB frei, keine Grenze |
| OOM beim Seeden als häufigstes Fehlerbild | `OOMKilled false`, `ExitCode 0`, kein zweiter Versuch |

**Damit war nichts von dem nötig, was die Randbedingungen verboten hatten:** kein `wsl --shutdown`, keine `.wslconfig`, kein Eingriff an den Containern der zwei fremden Projekte (`findling-nextcloud`, `nc-mcp-test`), die beide durchgelaufen sind. Der Ungemessen-Rückfall aus Task 1 wurde nicht gebraucht, und keiner der Pläne 17-04 bis 17-07 fiel unter seine Reichweite.

**Die Gegenprobe, ohne die die 95 Sekunden nichts wert wären:** eine 200 auf `/login` kann auch von einem Rails kommen, das die Seite schon ausliefert, während die Seed-Phase weiterläuft. Drei Belege aus demselben Lauf schließen das aus: die vier vorherigen Aufrufe antworteten 502, 502, 502 und 503; die Seed-Reihe steht namentlich und **vor** `=> Booting Puma` im Log; und das eingebaute PostgreSQL meldet um 16:43:38 UTC `listening on IPv4 address "0.0.0.0", port 5432`.

## Die Fassung, dreifach belegt

`17.7.2` steht jetzt im Kopfblock, und drei voneinander unabhängige Stellen nennen sie:

| Belegstelle | Wert |
|-------------|------|
| Digest der Bildmarke (`docker image inspect`) | `openproject/openproject@sha256:19a828d66e7c23322d1fbbaa974e7b712ef03c2badf1b10466ca45710e6bbbe5`, erstellt 2026-08-13 |
| Quelldatei im laufenden Container | `/app/lib/open_project/version.rb`: `MAJOR = 17`, `MINOR = 7`, `PATCH = 2` |
| API der laufenden Instanz | `GET /api/v3` mit dem Schlüssel: `coreVersion 17.7.2`, `instanceName OpenProject`; unauthentifiziert 401 |

## Die Namensfalle, in beide Richtungen gemessen (Abschnitt 5.2)

`op.localtest.me:8082` ist der eine Name. `curl` vom Host antwortet 200, `curl` aus dem Nextcloud-Container antwortet 200. Die zwei gleichlautenden 200 allein beweisen aber nicht, dass der `extra_hosts`-Eintrag die Arbeit tut, deshalb zwei Gegenproben: derselbe Aufruf aus dem Container mit `%{remote_ip}` nennt `172.29.43.10`, also die feste Adresse von Caddy, und `http://127.0.0.1:8082/login` aus demselben Container scheitert mit `curl: (7)`, weil dort nichts hört. Der Dienst `openproject` hat keinen veröffentlichten Port (`docker port` antwortet leer), der Zugang liegt allein auf `127.0.0.1:8082` am Caddy-Dienst.

**Ein Fund, der Plan 17-05 einen halben Tag sparen kann:** `getent hosts op.localtest.me` antwortet im Nextcloud-Container mit `::1` und nicht mit `172.29.43.10`, weil `localtest.me` einen öffentlichen AAAA-Eintrag auf die IPv6-Loopbackadresse hat und der `extra_hosts`-Eintrag ein reiner IPv4-Eintrag ist. Ein Aufrufer, der IPv6 bevorzugt, landet also im Container selbst. Gemessen ist, dass der Aufrufer, auf den es ankommt, die IPv4-Adresse nimmt: die PHP-Erweiterung `curl` desselben Containers, also der Weg, den `integration_openproject` geht, meldet `php_remote_ip=172.29.43.10` und Code 200.

## Abschnitt 5.3: der Grundzustand, als Aufbau gekennzeichnet

Angelegt über die API v3 mit dem Schlüssel des Kontos `admin`, alles mit 201:

| Was | Ergebnis |
|-----|----------|
| Konto A | `opa`, Vorname Alice, id 5, `active`, kein Admin |
| Konto B | `opb`, Vorname Bob, id 6, `active`, kein Admin |
| privates Projekt | `Spike Privat B`, Identifier `spike-privat-b`, id 3, `public false` |
| Mitgliedschaft | **nur** `opb`, Rolle `Member` (Rollen-Id 3) |
| Arbeitspaket | Betreff `SPIKE-OD-8471 privat`, Typ `Task`, **id 38** |

**Die Asymmetrie ist belegt und nicht nur beabsichtigt:** `GET /api/v3/memberships` gefiltert auf Projekt 3 antwortet `total: 1` und nennt genau `Bob Spike`. Alice ist nicht Mitglied. Ohne diese Asymmetrie wäre der Negativbeweis beider Wege leer und sähe trotzdem grün aus (Pitfall 3).

**Gegenproben des Aufbaus:** `GET /api/v3/work_packages/38` antwortet 200 und der Betreff enthält `SPIKE-OD-8471`, das private Projekt ist also nicht bloß leer angelegt. Dazu zwei Gegenproben zum Schlüssel selbst, weil eine 200 auch von einer offenen Instanz kommen könnte: mit einem Schlüssel aus 70 Nullen antwortet derselbe Aufruf 401, ohne jede Anmeldung ebenfalls 401. Der Schlüssel gehört nachweislich zu `admin` (`GET /api/v3/users/me`: `login admin`, `id 4`, `admin true`, `status active`).

**Was der Bericht ausdrücklich sagt:** der Admin-Zugang, mit dem dieser Grundzustand entstanden ist, ist **nicht Teil der gemessenen Kette**, und das Feld `Client Credentials User ID` der OAuth-Anwendung ist leer geblieben. Beide Sätze stehen im Bericht, weil ein Prüfer genau danach fragt und weil ein Wert in diesem Feld den Satz "der Assistent sieht niemals mehr als der angemeldete Nutzer" unwahr gemacht hätte, ohne dass eine einzige Messung rot geworden wäre (Pitfall 2, T-17-03).

## Deviations from Plan

**1. [Rule 1 - Belegstelle liefert den Wert nicht] Die dritte Fassungsbelegstelle ist die Quelldatei im Container, nicht die Fußleiste der Anmeldeseite**
- **Gefunden bei:** Task 1
- **Problem:** Der Plan verlangt die Fassung dreifach, als dritte Stelle die Fußleiste der Anmeldeseite. `curl` auf `/login` und ein Griff nach `17.7` und nach `version` im ausgelieferten HTML finden keine Fassung: 17.7.2 gibt sie dort nicht aus. Eine Aussage "Fußleiste bestätigt 17.7.2" wäre frei erfunden gewesen.
- **Fix:** Statt die Aussage abzuschwächen, ist eine andere Belegstelle an ihre Stelle getreten, die stärker ist als die Fußleiste, weil sie aus der Instanz selbst kommt: `/app/lib/open_project/version.rb` im laufenden Container nennt `MAJOR = 17`, `MINOR = 7`, `PATCH = 2`. Der Bericht nennt diese Stelle und nicht die Fußleiste.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** bd3d3b7

**2. [Rule 1 - Falscher Planverweis im Bericht] Kopfblockzeile für `integration_openproject` auf 17-05 berichtigt**
- **Gefunden bei:** Task 1
- **Problem:** Der Kopfblock führte `integration_openproject` als "noch nicht gemessen (Plan 17-03)". Dieser Plan installiert die App nicht und misst sie nicht; ein Griff nach der Installationszeile findet sie ausschließlich in `17-05-PLAN.md`. Nach Abschluss dieses Plans hätte der Bericht auf einen Plan verwiesen, der die Zeile nicht füllt.
- **Fix:** Verweis auf `Plan 17-05` geändert. Der Wert bleibt ungefüllt, weil er ungemessen ist.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** bd3d3b7

**3. [Rule 1 - Anweisung an den Owner zeigte auf eine 404] `/my/access_tokens` statt `/my/access_token`**
- **Gefunden bei:** Task 2, beim Vorbereiten des Checkpoints
- **Problem:** Der Plan nennt für Schritt 2 die Adresse `/my/access_token`. Sie antwortet in 17.7.2 mit **404**. Der Owner wäre in eine Sackgasse geschickt worden, und ein 404 an dieser Stelle sieht wie eine fehlende Berechtigung aus.
- **Fix:** Vor der Vorlage an den Owner alle vier Adressen geprüft und die richtige aus der Instanz belegt: `resources :access_tokens, only: %i[index]` mit `post :generate_api_key` in `/app/config/routes.rb:1183`, also `/my/access_tokens` im Plural. Die Korrektur steht im Checkpoint-Text und dauerhaft in `.env.spike-opendesk.example`.
- **Dateien:** `.env.spike-opendesk.example`
- **Commit:** 80983ca

**4. [Rule 1 - Feldname im Plan weicht von der Oberfläche ab] "Client Credentials User ID"**
- **Gefunden bei:** Task 2
- **Problem:** Der Plan nennt das Feld "Client Credentials User". Die Beschriftung dieser Fassung ist "Client Credentials User ID" (`/app/config/locales/en.yml:144`). Ein Owner, der nach der genauen Zeichenkette sucht, findet sie nicht und könnte das falsche Feld leer lassen.
- **Fix:** Der Checkpoint-Text nennt die tatsächliche Beschriftung. Zusätzlich vorab an der Instanz belegt, dass beide Formularfelder überhaupt existieren (`_form.html.erb:75` für `confidential`, Zeile 91 bis 113 für `client_credentials_user_id`) und dass `api_v3` neben den optionalen `scim_v2` und `mcp` steht, damit die Angabe "nur `api_v3` ankreuzen" präzise ist.
- **Dateien:** `docs/spike-opendesk.md` (der Satz über das leere Feld)
- **Commit:** 80983ca

**5. [Owner-Abweichung, Aufbau] Das Seed-Passwort `admin` wurde von der Instanz abgelehnt**
- **Gefunden bei:** Task 2, beim Owner
- **Problem:** Die dokumentierte Vorgabe `admin`/`admin` funktionierte nicht: `User.check_password?` falsch, `failed_login_count` auf 6, `force_password_change` true, Konto **nicht** gesperrt. Die Anmeldung, auf der die drei folgenden Oberflächenschritte aufsetzen, war damit blockiert.
- **Fix (durch den Owner):** Passwort des Benutzers `admin` per `rails runner` auf den Wert in `OP_ADMIN_PASSWORD` gesetzt, `force_password_change` auf false, `failed_login_count` auf 0. Der erzwungene Passwortwechsel hat damit nicht stattgefunden; für die Messungen dieser Phase ist das ohne Folge, weil keiner der beiden Wege am Passwort des Administrators hängt.
- **Ausdrücklich offen:** **warum** das Seed-Passwort abwich, ist nicht untersucht. Das steht im Bericht als offener Punkt und nicht als Vermutung.
- **Belegbarer Nebenbefund, im Bericht:** die Passwortregeln dieser Fassung verlangen alle vier Zeichenklassen. Die Fehlermeldung lautet wörtlich `Password Must include characters of the following types: lowercase, uppercase, numeric, special`. Deshalb sind die beiden Wegwerfpasswörter von `opa` und `opb` 20 Zeichen lang und enthalten alle vier Klassen, und nicht bloß die im Plan verlangten zwölf Zeichen.
- **Dateien:** `docs/spike-opendesk.md`, `.env.spike-opendesk.example` (die Aussage über den erzwungenen Wechsel dort war nach dieser Messung falsch und ist berichtigt)
- **Commit:** 80983ca

**6. [Rule 2 - Fehlender Variablenname und zwei falsche Aussagen in einer verfolgten Datei]**
- **Gefunden bei:** Task 3
- **Problem:** `.env.spike-opendesk.example` nennt nach der Regel aus 17-02 alle Namen, die die Folgepläne brauchen. `OP_WP_ID` fehlte. Zwei Aussagen derselben Datei widersprachen dem, was dieser Plan gemessen hat: der erzwungene Passwortwechsel beim ersten Anmelden (siehe Abweichung 5) und die Angabe, `OP_API_TOKEN` sei "an OpenProject API token of user A", während der Plan den Schlüssel des Kontos `admin` erzeugen lässt, weil nur ein Administrator Konten und Projekte anlegen kann.
- **Fix:** `OP_WP_ID` mit Kommentar ergänzt, beide Aussagen berichtigt, jeweils mit dem Messdatum und dem Verweis auf Abschnitt 5.3. `files_modified` des Plans nennt nur `docs/spike-opendesk.md`; diese Datei liegt außerhalb von `src/` und die Ergänzung ist reine Dokumentation ohne einen einzigen echten Wert (geprüfte Gegenprobe: kein unkommentiertes Geheimnis in der Datei).
- **Dateien:** `.env.spike-opendesk.example`
- **Commit:** 80983ca

**7. [Rule 1 - Gate trifft seine eigene Ueberschrift nicht] "Aufbau, nicht Messung" muss auch im Fließtext stehen**
- **Gefunden bei:** Task 3, beim Lauf des Task-3-Gates
- **Problem:** Das Gate des Plans lautet `grep -v '^#' docs/spike-opendesk.md | grep -q "Aufbau, nicht Messung"`. Der erste Griff soll Kommentarzeilen ausschließen, entfernt aber jede Markdown-Ueberschrift, weil die ebenfalls mit `#` beginnt. Die Ueberschrift `### 5.3 Aufbau, nicht Messung` erfüllt damit die acceptance-Kriterien des Plans, lässt das Gate aber fallen.
- **Fix:** Die Ueberschrift bleibt wie verlangt, und der erste Satz des Abschnitts nimmt die Zeichenkette wörtlich auf ("was hier steht, ist **Aufbau, nicht Messung**"). Beides ist jetzt erfüllt, ohne das Gate umzuschreiben.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 80983ca

**8. [Rule 1 - Gate würde beim nächsten Lauf übergangen] Der Pitfall-2-Griff trifft den erklärenden Absatz, und der Bericht sagt das**
- **Gefunden bei:** Task 3
- **Problem:** Pitfall 2 verlangt, dass `git grep -i "client_credentials\|GLOBAL__BASIC__AUTH\|apikey:"` in den Dateien dieser Phase nichts findet außer in einem Absatz, der erklärt, warum diese Wege ausgeschlossen sind. Der Bericht nennt aber `apikey:<OP_API_TOKEN>` zweimal als benannten Messweg des Aufbaus. Ohne Einordnung wäre beim nächsten Lauf unklar, ob die Treffer erwartet sind, und ein unklares Gate wird übergangen statt gelesen (dieselbe Lehre wie 17-02, Abweichung 5).
- **Fix:** Der erklärende Absatz sagt jetzt selbst, dass der Griff in diesem Bericht ausschließlich die Schreibweise mit Platzhalter findet und niemals einen Schlüssel, und dass ein Treffer in diesem Absatz erwartet und jeder Treffer außerhalb ein Befund ist. `GLOBAL__BASIC__AUTH` kommt nicht vor; die Aussage steht als deutsche Prosa ("ein globaler Basic-Auth-Nutzer").
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 80983ca

**9. [Rule 3 - Route des Plans braucht einen Projektbezug] Arbeitspaket über die projektbezogene Route angelegt**
- **Gefunden bei:** Task 3
- **Problem:** Der Plan nennt `POST /api/v3/work_packages`. Ein Arbeitspaket braucht ein Projekt, und die projektlose Route verlangt den Projektbezug im Körper.
- **Fix:** `POST /api/v3/projects/3/work_packages` mit dem Typ `Task` (Typ-Id aus `GET /api/v3/projects/3/types`), also die projektbezogene Route derselben API. Ergebnis 201, Projekt laut Antwort `Spike Privat B`. Der Bericht nennt die tatsächlich benutzte Route und nicht die des Plans.
- **Dateien:** keine
- **Commit:** 80983ca (der Messwert)

**10. [Rule 1 - Umgebungsvariable regiert nicht, was sie zu regieren scheint] Sprache des Seed-Kontos**
- **Gefunden bei:** Task 3
- **Problem:** Die Topologie setzt `OPENPROJECT_DEFAULT__LANGUAGE=en`, damit Feldnamen und Menüeinträge in der dokumentierten Sprache abgelesen werden können. Gemessen an `GET /api/v3/users` trägt `admin` aber `language de`; nur die beiden in diesem Plan angelegten Konten tragen `en`.
- **Fix:** Kein Eingriff, weil die Messungen unter `opa` und `opb` laufen und die Feldnamen der API v3 ohnehin englisch sind. Der Befund steht als Zeile in Abschnitt 5.3, damit ein Folgeplan, der eine Beschriftung aus der Oberfläche abliest, weiß, unter welchem Konto er sie abliest.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 80983ca

**11. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01 und 17-02] OD-02 bleibt Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter nennt `requirements: [OD-02]`, und `requirements mark-complete` hätte OD-02 abgehakt. Der Wortlaut trägt das nicht: OD-02 verlangt Weg 0 und Weg 1 mit Messwerten nebeneinander, und dieser Plan misst **keinen** der beiden. Er liefert den Grundzustand, ohne den beide Negativbeweise leer wären, und drei Messwerte über den Aufbau selbst.
- **Fix:** OD-02 bleibt `Pending` und wird von 17-09 abgehakt. Das folgt den Entscheidungen aus 17-01 und 17-02 und der Projektregel, Nachweise wörtlich zu nehmen.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

**12. [Außerhalb des Auftrags, festgehalten statt behandelt] OpenProject 17.7.2 bringt einen eigenen MCP-Server mit**
- **Gefunden bei:** Task 1, beim Prüfen der OAuth-Scopes für die Anweisungen an den Owner
- **Problem und Belege:** `/app/config/routes.rb:48` enthält `mount API::Mcp => "/mcp"`, Zeile 676 eine Verwaltungsseite `admin/mcp_configurations`, `doorkeeper.rb:136` einen optionalen Scope `mcp`, und der erste Start protokolliert `*** Seeding MCP configuration`. `GET /mcp` unauthentifiziert antwortet 500, also eine antwortende Route und keine 404.
- **Warum nicht behandelt:** über diesen Endpunkt ist **nichts** gemessen, nicht seine Werkzeugliste, nicht sein Authentifizierungsweg, nicht der Berechtigungsdurchgriff, und nicht ob openDesk ihn einschaltet. Eine Aussage daruber wäre eine Behauptung über fremden Code ohne Messung. Eine Messung hätte den Stufenschnitt aus Pitfall 1 aufgeweicht.
- **Fix:** als DI-17-01 in `.planning/phases/17-opendesk-spike/deferred-items.md` festgehalten, mit Behandlungsvorschlag für 17-08 (Frage mit Grund für den ISV-Call) und 17-09.
- **Dateien:** `.planning/phases/17-opendesk-spike/deferred-items.md`
- **Commit:** 21cdd6f

Sonst keine. Insbesondere wurde der Zwei-Konten-Negativbeweis **nicht** vorweggenommen, obwohl die Passwörter beider Konten vorliegen und der Aufruf zwei Minuten gekostet hätte: der Plan weist ihn 17-04 und 17-06 zu, und ein hier gefahrener Beweis hätte Aufbau und Messung im selben Plan vermischt. Der Bericht sagt diesen Verzicht ausdrücklich.

## Authentication Gates

**Einer, geplant und als Checkpoint gefahren (Task 2, `checkpoint:human-action`).** Vier Schritte, für die OpenProject 17.7.2 keinen dokumentierten Weg außer der Oberfläche anbietet. Ein `rails runner` gegen `Doorkeeper::Application` war nach Annahme A7 ausdrücklich untersagt und ist nicht benutzt worden.

Vor dem Anhalten automatisiert und belegt, damit der Owner in keine Sackgasse läuft: die vier Adressen geprüft (und die falsche des Plans korrigiert, Abweichung 3), die Existenz beider Formularfelder und der drei Scopes aus der Instanz belegt (Abweichung 4), `force_pkce` und `hash_application_secrets` in `doorkeeper.rb` Zeile 90 und 96 als Begründung für "Confidential aus" und "Secret sofort kopieren" nachgewiesen, und ein kommentierter Block für die vier Namen in der git-ignorierten Verbindungsdatei vorbereitet. Ich habe mich **nicht** angemeldet, damit der erzwungene Passwortwechsel der Schritt des Owners bleibt.

Nach der Freigabe geprüft: alle vier Variablen gesetzt (Längen 22, 70, 43, 43 Zeichen; kein Wert steht in einer Datei des Repositories, in einem Protokoll oder in diesem SUMMARY), und `GET /api/v3/users/me` mit `Basic apikey:<OP_API_TOKEN>` antwortet **200** als `login admin`. Gegenproben: Schlüssel aus 70 Nullen 401, ohne Anmeldung 401.

Der Ungemessen-Rückfall des Checkpoints wurde nicht gebraucht: Weg 1 ist nicht als `ungemessen, OAuth-Anwendung nicht angelegt` zu führen, und 17-04 wird nicht übersprungen.

## Verification

- Task-1-Gate: `curl` vom Host 200, `curl` aus dem Nextcloud-Container 200, `17.7.2` im Bericht gefunden. `docker compose --profile op ps openproject`: `running`.
- Task-2-Gate: alle vier Variablen nicht leer, `GET /api/v3/users/me` 200.
- Task-3-Gate: Betreff enthält `SPIKE-OD-8471`, `Aufbau, nicht Messung` und `Client Credentials User` beide auch außerhalb von Ueberschriften gefunden, Ausgangswert 0.
- `GET /api/v3/projects/spike-privat-b`: `public False`. Mitgliederliste des Projekts: `total 1`, `Bob Spike`, kein `Alice`.
- `OP_USER_A_PASSWORD`, `OP_USER_B_PASSWORD` und `OP_WP_ID` stehen in `.env.spike-opendesk`.
- `git status --short` zeigt `.env.spike-opendesk` nicht an (`git check-ignore -v` trifft `.gitignore:17`). `git grep -n OP_OAUTH_CLIENT_SECRET` findet den Namen nur in `.env.spike-opendesk.example` (auskommentiert, mit Platzhalter) und in Plantext, nie mit einem Wert dahinter.
- Geheimnis-Gate über beide geänderten Dateien: kein Treffer. Pitfall-2-Griff: zwei Treffer, beide `apikey:<OP_API_TOKEN>` als Platzhalter, beide im dafür vorgesehenen Absatz.
- `uv run pytest -q`: grün, Ausgangswert 0, dreimal gefahren (nach Task 1, nach dem Berichtstext von Task 3 und nach der Aenderung an der Beispieldatei).
- Kein U+2014 und kein U+2013 in `docs/spike-opendesk.md` und in `.env.spike-opendesk.example`, kein Zeichen oberhalb U+2600, keine ASCII-Ersatzschreibung von Umlauten.
- `git status --short src/ appinfo/ pyproject.toml uv.lock`: leer. `files_modified` nennt keinen Pfad unter `src/` (D-12).
- Keiner der drei Commits löscht eine verfolgte Datei (`git diff --diff-filter=D` je leer), keine unverfolgte Datei bleibt liegen.
- Loopback-Nachweis: `docker port nc-mcp-spike-od-op` leer, `8082/tcp` am Caddy-Dienst auf `127.0.0.1`.

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: die Abschnitte 2.1, 2.2, 2.4, 2.5, 3, 4 und "Was diese Messung nicht beweist" tragen weiter je eine Zeile `noch nicht gemessen` mit Planzuordnung. Die Kopfzeilen `integration_openproject` (jetzt Plan 17-05) und `user_oidc` sowie Keycloak (Plan 17-07) ebenso. Der Dienst `keycloak` steht ungestartet in der Compose-Datei: das ist der von Pitfall 1 verlangte Schnitt zur Stufe C, kein unfertiger Zustand.

Kein Stub verhindert das Ziel dieses Plans: der Grundzustand, den 17-04 und 17-06 brauchen, ist vollständig und gegengeprüft.

## Threat Flags

Keine neue Fläche über das Bedrohungsmodell des Plans hinaus. Drei Anmerkungen zu Einträgen daraus:

- **T-17-01 (Information Disclosure), gehalten:** sieben neue Werte sind entstanden, alle sieben liegen ausschließlich in `.env.spike-opendesk`. Im Bericht steht von ihnen nichts außer der vom Server vergebenen Arbeitspaket-Id `38` und den Zeichenlängen in diesem SUMMARY.
- **T-17-03 (Elevation of Privilege), gehalten und im Bericht belegt:** "Confidential" aus, `Client Credentials User ID` leer, kein Dienstkonto, keine Umgebungsvariable für einen globalen Basic-Auth-Nutzer. Der Ausschluss steht als Absatz im Bericht.
- **T-17-02 (Spoofing, Tampering), eine Abweichung nach unten:** das Vorgabe-Passwort `admin` ist ersetzt, wie das Modell es verlangt, aber nicht über den erzwungenen Wechsel der Oberfläche, sondern per `rails runner` (Abweichung 5). Das Ergebnis ist dasselbe: kein Konto dieser Instanz trägt mehr ein dokumentiertes Vorgabe-Passwort. Die Instanz ist außerdem nur auf `127.0.0.1` erreichbar.

Ein möglicher **künftiger** Flächenzuwachs steht als DI-17-01 in `deferred-items.md`: der native MCP-Endpunkt von OpenProject unter `/mcp`. Er ist in dieser Phase nicht gemessen und wird von dieser ExApp nicht angesprochen.

## Hinweise für die Folgepläne

1. **Drei Exporte vor jedem compose-Kommando**, auch vor `ps`: `HP_SHARED_KEY` und `SECRET_KEY_BASE` sind Pflicht (compose interpoliert die ganze Datei vor der Profilauswahl). Beide stehen in `.env.spike-opendesk`; `set -a && . ./.env.spike-opendesk && set +a` genügt.
2. **`SECRET_KEY_BASE` darf sich nie ändern.** Rails leitet jedes Sitzungscookie und jeden verschlüsselten Datenbankinhalt daraus ab. Der Wert steht mit 128 Hexzeichen in der Verbindungsdatei.
3. **Wer `pytest` fährt, muss `APP_ID`, `APP_SECRET` und `APP_VERSION` für diesen Prozess entfernen** (`env -u APP_ID -u APP_SECRET -u APP_VERSION`), sonst wählt die Verbindungsdatei den ExApp-Modus und der Wächter der eigenen App bricht ab. Das gilt weiter aus 17-02.
4. **Der Zwei-Konten-Negativbeweis ist vorbereitet, aber nicht geführt.** Arbeitspaket `38` im privaten Projekt `spike-privat-b` (id 3), Mitglied nur `opb`. `opa` darf es nicht sehen, und genau das ist in 17-04 und 17-06 zu messen, unter den Konten selbst und nicht unter dem Admin-Schlüssel.
5. **Für 17-05:** `openproject_instance_url` ist `http://op.localtest.me:8082`. Läuft ein Aufruf von Nextcloud aus ins Leere, ist der AAAA-Eintrag von `localtest.me` auf `::1` die erste Stelle zum Schauen und nicht die Caddy-Regel (gemessen: PHP-curl nimmt IPv4 und antwortet 200).
6. **Passwortregel dieser Fassung:** alle vier Zeichenklassen, sonst lehnt die API mit einer Meldung ab, die wie ein Berechtigungsfehler aussieht.
7. **Die Adresse für API-Schlüssel ist `/my/access_tokens`** im Plural. Der Singular ist eine 404.
8. **Nur eine Topologie dieses Repositories kann die ExApp betreiben.** Die Topologie aus `compose.exapp.yml` ist weiter mit `stop` angehalten, nie mit `down -v`. Die Wiederherstellungsschritte stehen in 17-02-SUMMARY.md, Abweichung 3.

## Self-Check: PASSED

Die drei in diesem SUMMARY genannten Dateien existieren (`docs/spike-opendesk.md`, `.env.spike-opendesk.example`, `.planning/phases/17-opendesk-spike/deferred-items.md`), und alle drei Commit-Kennungen (bd3d3b7, 21cdd6f, 80983ca) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` ist grün, OpenProject und die vier Dienste der Stufe A laufen, und das Arbeitspaket `38` ist unter dem Suchwort `SPIKE-OD-8471` lesbar. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt; wo eine Messung fehlt (Ursache des abgelehnten Seed-Passworts, nativer MCP-Endpunkt von OpenProject), sagt der Text das ausdrücklich.
