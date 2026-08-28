---
phase: 17-opendesk-spike
plan: 02
subsystem: measurement-environment
tags: [spike, opendesk, od-01, od-02, s0, ssrf, docker, appapi, harp]
requires:
  - "17-01: docs/spike-opendesk.md mit Kopfblock, Entscheidungskriterien und Abschnitt 1"
provides:
  - "compose.spike-opendesk.yml: Stufe A laufend, Stufe B (op) und Stufe C (oidc) als Profile, alle drei Bildmarken gepinnt, jede ports-Zeile auf 127.0.0.1"
  - "scripts/bootstrap_spike_opendesk.sh: idempotenter Bootstrap gegen die Spike-Topologie, --manual erhalten, --staging entfernt"
  - ".env.spike-opendesk.example: Variablennamen aller drei Stufen, kein einziger echter Wert"
  - "S0 gemessen: die Ein-Klick-Kette haelt auf Nextcloud 33.0.7, mit Gegenprobe 64 Nullen"
  - "Berichtskopf mit aus der laufenden Instanz gelesenen Fassungen (Nextcloud 33.0.7.1, app_api 33.0.0, ExApp 0.1.11, HaRP-Digest)"
  - "Abschnitt 2.3: SSRF-Grenze gegen interne Docker-Dienstnamen gemessen, mit Gegenprobe und Entwurfsbefund fuer OD-04"
  - "Annahme A5 gemessen bestaetigt: app_api 33.0.0, die Kubernetes-Aussage aus 1.2 steht unveraendert"
affects:
  - "17-03 startet Stufe B mit --profile op gegen dieselbe Topologie; SECRET_KEY_BASE muss exportiert sein, sonst schlaegt jedes compose-Kommando fehl"
  - "17-04 bis 17-07 laufen gegen dieselbe laufende Stufe A; die registrierte ExApp ist der Aufrufer"
  - "17-07 startet Stufe C mit --profile oidc und muss KC_BOOTSTRAP_ADMIN_USERNAME und KC_BOOTSTRAP_ADMIN_PASSWORD selbst mitgeben"
  - "17-09 fuellt 2.4, 2.5 und Abschnitt 3; S0 und 2.3 stehen als Eingangswerte bereit"
tech-stack:
  added:
    - "nextcloud:33.0.7-apache (Messumgebung, gepinnt auf den openDesk-Stand)"
    - "openproject/openproject:17.7.2 (Profil op, in diesem Plan nicht gestartet)"
    - "quay.io/keycloak/keycloak:26.7.0 (Profil oidc, in diesem Plan nicht gestartet)"
  patterns:
    - "Stufenschnitt als compose-Profile, damit der billige Teil der Phase protokolliert ist, bevor der teure Teil gezogen wird"
    - "Geheimnisse ohne Vorgabewert (WR-11) mit ${VAR:?...}; gemessen, dass compose die ganze Datei vor der Profilauswahl interpoliert, und im Dateikopf dokumentiert"
    - "Zwei Ursachen fuer denselben Rueckgabewert werden getrennt protokolliert: resolve_addresses antwortet None sowohl bei Regelverstoss als auch bei Resolver-Fehlschlag, und nur die Logzeile unterscheidet sie"
key-files:
  created:
    - "compose.spike-opendesk.yml"
    - "deploy/Caddyfile.spike-opendesk"
    - "scripts/bootstrap_spike_opendesk.sh"
    - ".env.spike-opendesk.example"
  modified:
    - ".gitignore"
    - "docs/spike-opendesk.md"
decisions:
  - "Stufe A steht mit vier Diensten auf Loopback; OpenProject und Keycloak stehen als Profile in derselben Datei, damit der Stufenschnitt sichtbar ist und ein blankes up keinen von beiden startet"
  - "Die Spike-Topologie bekommt ein eigenes Verzeichnis fuer die FRP-Zertifikate, weil zwei HaRP-Daemons auf einem gemeinsamen /certs eine geteilte CA untereinander neu erzeugen koennten und die Topologie, die dabei bricht, die taeglich benutzte waere"
  - "Der Deploy-Daemon benennt den ExApp-Container global nc_app_<appid>; zwei Topologien dieses Repositories koennen dieselbe ExApp deshalb nicht gleichzeitig betreiben. Die ExApp-Topologie ist fuer die Dauer der Phase mit stop angehalten, nie mit down -v"
  - "Der openproject-Dienstname loest ohne das Profil op nicht auf; die SSRF-Messung entscheidet den Fall stattdessen mit drei Adressliteralen desselben /24 und schreibt den Resolver-Fehlschlag als eigene Zeile in den Bericht, statt ihn als Sperrung zu lesen"
  - "Die drei vorbestehenden Vokabular-Gate-Treffer aus Plan 17-01 sind bereinigt, ohne Abschnitt 1 umzubauen; der eine unvermeidbare Treffer steckte in einer fremden URL und ist als ausgelassener Pfadteil mit Begruendung im Text geloest"
metrics:
  duration: 74 min
  completed: 2026-08-28
---

# Phase 17 Plan 02: Stufe A der Messumgebung und die ersten zwei Messwerte Summary

Stufe A steht gepinnt auf Nextcloud 33.0.7 und ausschließlich auf 127.0.0.1, und darauf fallen die zwei Messwerte, die dieser Plan schuldet: S0 hält (die Ein-Klick-Kette dieser App funktioniert auf dem openDesk-Stand, mit Gegenprobe), und die SSRF-Grenze aus D-06 ist gegen drei interne Docker-Dienstnamen gemessen statt hergeleitet.

## Erste Zeile des Protokolls: der Speicher der WSL2-VM (A3)

Der teuerste vermeidbare Fehlweg dieser Phase wurde vor dem ersten Container geprüft, und der Wert liegt **unter** der Schwelle von 8 GB:

| Messwert | Wie gelesen | Ergebnis |
|----------|-------------|----------|
| `C:\Users\Student\.wslconfig` | `cat` | existiert nicht, WSL2 läuft also auf seiner Vorgabe |
| Hauptspeicher des Rechners | `wmic computersystem get TotalPhysicalMemory` | 16852574208 Bytes, 15,7 GiB |
| Speicher der WSL2-VM | `free -m` in einem Container | total 7785 MiB, verfügbar 5752 MiB |
| Speicher, den Docker meldet | `docker info` | 8163373056 Bytes, 7,603 GiB |

WSL2 nimmt ohne `.wslconfig` die Hälfte des Hauptspeichers, hier 7,6 GiB, und damit knapp unter den 8 GB, die 17-RESEARCH.md als Schwelle nennt. Für Stufe A hat das nicht gestört: die fünf Container dieser Topologie belegen zusammen unter 400 MiB, und vor dem Start waren 5,7 GiB frei. **Für Plan 17-03 ist es ein Risiko und keine Fußnote:** die All-in-one-Bildmarke von OpenProject bringt ihr eigenes PostgreSQL mit und ist der speicherhungrigste Teil der Phase. Eine `.wslconfig` mit `memory=12GB` wurde bewusst **nicht** angelegt, weil sie erst nach `wsl --shutdown` greift und das jeden laufenden Container dieses Rechners beendet, auch die zwei fremden Projekte (`findling-nextcloud`, `nc-mcp-test`). Wer 17-03 fährt, entscheidet das mit dem Owner, nicht nebenbei.

## Was entstanden ist

**`compose.spike-opendesk.yml`**, 284 Zeilen. Eigenes Projekt `nc-mcp-spike-od`, eigenes Netz `nc-mcp-spike-od-net` auf `172.29.43.0/24` mit `ip_range` in der oberen Hälfte, feste Caddy-Adresse `172.29.43.10`, eigene Bände, eigene Ports. Die drei Bildmarken sind gepinnt (`nextcloud:33.0.7-apache`, `openproject/openproject:17.7.2`, `quay.io/keycloak/keycloak:26.7.0`), kein `latest`, kein Nightly. Jede der drei `ports`-Zeilen beginnt mit `127.0.0.1:`; keine Zeile bindet eine andere Adresse. `TRUSTED_PROXIES` und `HP_TRUSTED_PROXY_IPS` tragen genau eine Adresse und nie das Subnetz (WR-08). Der Dienst `greenmail` entfällt.

Der Stufenschnitt steht in der Datei und nicht nur in den Plänen: `openproject` unter `profiles: ["op"]`, `keycloak` unter `profiles: ["oidc"]`. Gemessen, nicht angenommen: `docker compose -f compose.spike-opendesk.yml config --services` nennt vier Dienste, mit `--profile op` fünf.

**`deploy/Caddyfile.spike-opendesk`**, 76 Zeilen. Kopie von `deploy/Caddyfile` mit einem zweiten Zuhörblock `:8082` auf `openproject:80`. Zwei Dinge stehen dort begründet: warum `X-Forwarded-Proto` den Wortwert `http` trägt und nicht den Platzhalter `{scheme}` (die Topologie serviert kein TLS, ein falscher Wert erzeugt eine Umleitungsschleife), und warum der `Host`-Kopf ausdrücklich **nicht** umgeschrieben wird (Caddy reicht ihn durch, und Rails vergleicht ihn gegen `OPENPROJECT_HOST__NAME`; ein `header_up Host {upstream_hostport}` würde `openproject:80` liefern und jede Anfrage mit einem Host-Autorisierungsfehler beenden). `caddy validate` gegen die Datei: `Valid configuration`.

**`scripts/bootstrap_spike_opendesk.sh`**, 1421 Zeilen. Kopie von `scripts/bootstrap_exapp.sh`, erzeugt über ein Skript mit ausschließlich exakten Zeichenketten-Ersetzungen und einer Endprüfung, die bei einem einzigen verbliebenen Verweis auf die alte Topologie abbricht. Geändert sind die Topologie-Konstanten (`COMPOSE_FILE`, `PROJECT_NAME`, `HARP_CONTAINER`, `HOST_PORT`, `NETWORK_NAME`, `REGISTRY` auf `127.0.0.1:5001`, `ENV_FILE`) und die Variablennamen `NC_EXAPP_*` zu `NC_SPIKE_OD_*`. `COMPOSE_FILE` bleibt nicht überschreibbar (WR-07), `--manual` bleibt, `--staging` und sein Zweig sind weg. `bash -n`: fehlerfrei.

**`.env.spike-opendesk.example`**, 111 Zeilen: nur Variablennamen und Kommentare, jede Geheimniszeile auskommentiert, alle zehn von den Folgeplänen gebrauchten Namen benannt. **`.gitignore`** trägt `.env.spike-opendesk` und `.harp-certs-spike-od/`. Gegenprobe: `git check-ignore -v .env.spike-opendesk` trifft Zeile 17, und die Datei erscheint nach dem Bootstrap nicht als unverfolgt.

## S0: hält die Kette auf 33.0.7 (Abschnitt 1.3)

**Ja, gemessen, mit Gegenprobe.** Der Bootstrap lief einmal durch, ohne Fehler und ohne Rückfall.

| Schritt | Messwert |
|---------|----------|
| Zustand der ExApp | `occ app_api:app:list`: `mcp_connector (MCP Connector): 0.1.11 [enabled]`, gleiche Fassung wie `appinfo/info.xml` |
| Deploy-Daemon | `harp_proxy_docker`, Deploy-ID `docker-install`, `Is HaRP yes`, `NC Url http://caddy` |
| Werkzeugaufruf | `tests/integration/test_http_tool_call.py -m integration`: 3 Tests grün, darunter `notes_create` plus `notes_read` als `alice` |
| Impersonationskette | `GET /ocs/v2.php/cloud/user` mit `AUTHORIZATION-APP-API`, ohne App-Passwort: HTTP 200, `ocs.data.id = alice` |
| ExApp-Route durch HaRP | `POST /exapps/mcp_connector/mcp` ohne Token: HTTP 401 mit unserem eigenen `resource_metadata`-Zeiger, also antwortender App-Code |
| Gegenprobe | derselbe OCS-Aufruf mit `APP_SECRET` aus 64 Nullen: HTTP 401, `statuscode 997`, `Current user is not logged in` |

Der geerbte Nachweis auf 34.0.2 (`docs/spike-dav.md`) und 34.0.3 (`docs/spike-mail.md`) ist damit durch einen auf 33.0.7 ersetzt. Kein Wert des Headers `AUTHORIZATION-APP-API` und kein `APP_SECRET` steht im Bericht (Geheimnisregel, T-17-01).

**Annahme A5 ist mitgemessen und trifft zu:** `occ app:list` nennt `app_api: 33.0.0`, also die 33er-Linie, deren `RegisterDaemon.php` den Wert `kubernetes-install` nicht aufzählt. Die Kubernetes-Aussage aus 1.2 stand bisher nur auf Quellcode und hat jetzt einen Beleg aus der laufenden Instanz. Läge die Fassung darüber, hätte 1.2 neu bewertet werden müssen.

## Abschnitt 2.3: die SSRF-Grenze, gemessen statt hergeleitet (D-06)

Im laufenden ExApp-Container (`nc_app_mcp_connector`, `running`, Netz `nc-mcp-spike-od-net`), mit dem Resolver der Produktion, ohne eine Zeile in `src/`.

- `_system_addresses`: `nextcloud` auf `172.29.43.129`, `caddy` auf `172.29.43.10`, `appapi-harp` auf `172.29.43.131`. `openproject` wirft `gaierror`, weil das Profil `op` nicht läuft und Docker einem Dienst ohne Container keinen DNS-Eintrag gibt.
- `target_allowed`: `False` für alle drei, mit `is_private=True` und `is_global=False` dabei. Dazu drei Literale desselben `/24` (`.10`, `.128`, `.254`), ebenfalls `False`: damit ist der Fall für OpenProject entschieden, ohne Stufe B zu starten.
- `resolve_addresses`: `None` für alle vier, und die Logzeile trennt die zwei Ursachen. Dreimal `a document target was refused: an address of it is not public`, einmal `a document target did not resolve: gaierror`. Ohne diese Trennung hätte ein Resolver-Fehlschlag im Bericht wie eine Sperrung gelesen.
- Gegenprobe im selben Lauf: `one.one.one.one` und `example.com` liefern je vier Adressen. Das `None` oben ist damit die Regel und nicht die Umgebung.
- Der Negativkatalog ist der bestehende aus `tests/unit/test_oauth_cimd.py` (Zeilen 179 bis 202), im Container gefahren: 12 von 12 abgelehnt, 3 von 3 der Positivliste zugelassen, keine Abweichung.

Die Einordnung steht mit der verlangten Zeichenkette im Bericht: die Grenze sitzt auf dem Weg zum **Client-Id-Metadatendokument** eines fremden OAuth-Clients, und der in dieser Phase gemessene Zugriffsweg berührt sie nicht, weil es keine zweite Basis-URL gibt. Der Entwurfsbefund für OD-04 steht als eigener Absatz da und verlangt keine Codeänderung.

## Deviations from Plan

**1. [Rule 3 - Blockierende Umgebungseigenschaft] Eigenes Zertifikatsverzeichnis für den zweiten HaRP-Daemon**
- **Gefunden bei:** Task 1, beim Übernehmen des `./.harp-certs`-Bandes aus `compose.exapp.yml`
- **Problem:** HaRP erzeugt die FRP-CA und beide Blattzertifikate beim ersten Start in `/certs` und benutzt weiter, was es dort findet. Zwei Daemons mit zwei verschiedenen `HP_SHARED_KEY` auf demselben Verzeichnis teilen eine CA und können sie untereinander neu erzeugen. Die Topologie, die dabei bricht, wäre `compose.exapp.yml`, die in diesem Repository täglich benutzt wird.
- **Fix:** `./.harp-certs-spike-od:/certs`, mit der Begründung als Kommentar an der Zeile, plus eine Zeile in `.gitignore`. Das ist die einzige Stelle, an der die Datei über die Topologie-Konstanten hinaus von ihrer Vorlage abweicht, und sie ist als solche gekennzeichnet.
- **Dateien:** `compose.spike-opendesk.yml`, `.gitignore`
- **Commit:** 712a4ef

**2. [Rule 3 - Blockierende Umgebungseigenschaft] HAS_MAIL_SERVER=0 statt drei Mailaufrufe ins Leere**
- **Gefunden bei:** Task 1, beim Ableiten des Bootstrap-Skripts
- **Problem:** Der Plan verlangt, den Dienst `greenmail` weglassen zu lassen **und** im Skript ausschließlich Topologie-Konstanten zu ändern. Beides zusammen geht nicht: `ensure_mail_account`, `deliver_test_mail` und `sync_mail_account` laufen gegen `greenmail`, und `set -e` hätte den Bootstrap dort beendet, bevor die ExApp überhaupt registriert wird. Das hätte S0 auf `ungemessen` gesetzt, aus einem Grund, der mit 33.0.7 nichts zu tun hat.
- **Fix:** Eine neue Konstante `HAS_MAIL_SERVER=0` und die drei Aufrufe in genau der Form übersprungen, in der der entfernte Zweig für die öffentliche Instanz sie übersprungen hat. Kein Funktionskörper wurde umgebaut, die beiden bestehenden Wächter tragen nur eine andere Bedingung.
- **Dateien:** `scripts/bootstrap_spike_opendesk.sh`
- **Commit:** 712a4ef

**3. [Rule 1 - Fremde Topologie beschädigt] Die ExApp-Topologie ist angehalten, weil der Containername global ist**
- **Gefunden bei:** Task 1, nach dem Bootstrap
- **Problem:** Der Deploy-Daemon benennt den ExApp-Container `nc_app_<appid>`, und dieser Name ist global und nicht projektgebunden. Die Registrierung in der Spike-Topologie hat den laufenden `nc_app_mcp_connector` der Topologie aus `compose.exapp.yml` ersetzt: gemessen an `docker ps` steht danach genau ein Container dieses Namens, auf `nc-mcp-spike-od-net` und mit dem Bild aus der Registry auf `127.0.0.1:5001`. Die alte Topologie hätte ihre ExApp ab da nicht mehr erreicht, und ein Wettlauf um denselben Namen hätte jede Messung der Folgepläne verfälschen können.
- **Fix:** `docker compose -f compose.exapp.yml stop`, also ausdrücklich `stop` und niemals `down -v`; die Bände und damit alle fremden Messdaten sind unangetastet. Der Befund ist im Kopf von `compose.spike-opendesk.yml` nicht vermerkt, weil er keine Eigenschaft dieser Datei ist, sondern eine von AppAPI; er steht hier und in den Folgeplan-Hinweisen unten.
- **Wiederherstellung nach der Phase:** `export HP_SHARED_KEY="$(sed -n 's/^HP_SHARED_KEY=//p' .env.exapp)"`, dann `docker compose -f compose.exapp.yml up -d --wait` und `bash scripts/bootstrap_exapp.sh`. Der Bootstrap ist idempotent und holt den Containernamen zurück.
- **Dateien:** keine
- **Commit:** kein eigener, die Handlung ist eine Zustandsänderung an Containern

**4. [Rule 1 - Rotes Gate auf der Datei, die dieser Plan erweitert] Drei Vokabular-Treffer aus Plan 17-01 bereinigt**
- **Gefunden bei:** Task 1, beim Baseline-Lauf der Testsuite vor dem ersten Commit
- **Problem:** `uv run pytest -q` war vor jeder Änderung dieses Plans schon rot, mit genau einem Fehlschlag: `test_no_public_markdown_page_carries_the_forbidden_vocabulary` fand das verbotene Wort dreimal in `docs/spike-opendesk.md` (Zeilen 96, 99, 158 aus Plan 17-01). Die Verifikation dieses Plans verlangt eine grüne Suite, und Task 2 und 3 schreiben in genau diese Datei.
- **Fix:** Zwei Prosastellen umformuliert (`Repository-Archiv` zu `Tarball-Download`, `Archivgriff` zu `Tarball-Griff`). Die dritte steckte in einer fremden GitLab-URL und war nicht umformulierbar, ohne den Messweg zu verfälschen: dort ist der Pfadteil als `[…]` ausgelassen und der Grund im Text genannt, mit Verweis auf `tests/unit/test_exapp_env_setup.py` und `FORBIDDEN_VOCABULARY`. Bytezahl und Dateizahl, also die Messwerte selbst, stehen unverändert. Abschnitt 1 ist nicht umgebaut; es sind drei Zeilen und ein erklärender Satz.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** d9acfe8

**5. [Rule 1 - Gate scheitert an seiner eigenen Regel] Geheimnisregel nennt ihre Suchmuster umschrieben**
- **Gefunden bei:** Task 2, beim Lauf des Geheimnis-Gates aus dem Plan
- **Problem:** Das Geheimnis-Gate des Plans (die vier Muster: JWT-Präfix, Bearer-Schema mit Wert, `refresh_token` und `client_secret` je mit Gleichheitszeichen, dazu der Headername mit Doppelpunkt) traf zwei Zeilen, beide falsch positiv: die Geheimnisregel aus Plan 17-01 zitiert ihre vier Suchmuster wörtlich, und mein neuer Satz über den `WWW-Authenticate`-Kopf nannte das Schema unmittelbar vor dem Fehlerwert. Ein Gate, das an seiner eigenen Regel scheitert, wird beim nächsten Lauf übergangen statt gelesen.
- **Fix:** Der Satz über den Kopf nennt jetzt Schema, Fehler, Scope und Zeiger getrennt; der load-bearing Teil, der `resource_metadata`-Zeiger, steht unverändert. Die Geheimnisregel beschreibt ihre vier Muster umschrieben und sagt in einem Halbsatz, warum. Danach ist das Gate über die ganze Datei sauber.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** d9acfe8

**6. [Rule 3 - Der genannte Dienst existiert in dieser Welle nicht] SSRF-Messung gegen drei laufende Nachbarn plus Literale**
- **Gefunden bei:** Task 3
- **Problem:** Der Plan nennt `cimd._system_addresses("openproject", 80)` als ersten Messschritt. Das Profil `op` läuft in diesem Plan aber nicht, und Docker gibt einem Dienst ohne laufenden Container keinen DNS-Eintrag. `resolve_addresses("openproject", 80)` antwortet dann `None` aus dem falschen Grund: Resolver-Fehlschlag statt Regelverstoß. Ein Bericht, der nur den Rückgabewert notiert, hätte daraus eine Sperrung gemacht, die nicht gemessen war.
- **Fix:** Gemessen wurde gegen die drei laufenden Nachbarn (`nextcloud`, `caddy`, `appapi-harp`), alle unter ihrem Compose-Dienstnamen und alle mit privaten Adressen aus `172.29.43.0/24`. Der Fall für OpenProject ist mit drei Adressliteralen desselben `/24` entschieden. Die `openproject`-Zeile steht trotzdem im Bericht, mit ihrer eigenen Logzeile (`did not resolve: gaierror`) und der ausdrücklichen Feststellung, dass das eine andere Ursache für denselben Rückgabewert ist. Damit ist die Messung vollständiger als der Plan sie beschreibt und an keiner Stelle behauptet, was sie nicht gesehen hat.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 16c6c6e

**7. [Rule 3 - Blockierende Wächter der eigenen App] Werkzeugaufruf mit den Variablennamen, die die Testdatei liest**
- **Gefunden bei:** Task 2
- **Problem:** Der Plan schreibt `set -a && . ./.env.spike-opendesk && set +a` und danach `uv run pytest tests/integration/test_http_tool_call.py -m integration -q`. So gefahren ergibt das dreimal `skipped`: die Datei liest `NC_MCP_USER` und `NC_MCP_APP_PASSWORD`, die Verbindungsdatei schreibt `NC_MCP_TEST_USER` und `NC_MCP_TEST_APP_PASSWORD`. Mit den zwei Namen zugeordnet bricht der Lauf trotzdem ab, und zwar an einem Wächter der eigenen App: `APP_ID` und `APP_SECRET` aus der Verbindungsdatei wählen den ExApp-Modus, und `entry_http` weigert sich, in einem Standalone-Prozess in diesem Modus zu starten.
- **Fix:** Der Lauf, den der Plan als Rückfall vorsieht, war nicht nötig. Gemessen wurde mit den zwei Namen zugeordnet und den drei ExApp-Variablen für diesen Prozess entfernt, also genau so, wie die Fehlermeldung des Wächters es dem Betreiber sagt (`env -u APP_ID -u APP_SECRET -u APP_VERSION`). Keine neue Datei, keine Änderung an der Testdatei, kein Eingriff in `src/`. Der `curl`-Rückfall des Plans lief zusätzlich, weil er die Impersonationskette prüft, die der Test nicht anfasst; beide Werte stehen im Bericht.
- **Dateien:** keine
- **Commit:** d9acfe8 (der Messwert)

**8. [Rule 2 - Fehlende Betriebsangabe] Zwei Pflichtexporte statt einem, gemessen und dokumentiert**
- **Gefunden bei:** Task 1
- **Problem:** Der Plan lässt `SECRET_KEY_BASE` nach dem `HP_SHARED_KEY`-Muster ohne Vorgabewert setzen (WR-11) und gibt als Startbefehl nur `export HP_SHARED_KEY=...` an. Gemessen mit einer eigenen Sondendatei am 2026-08-28: compose interpoliert die ganze Datei, bevor es nach Profilen filtert, und ein `${VAR:?...}` in einem Dienst mit `profiles:` lässt **jedes** Kommando scheitern, `config --services` und `ps` eingeschlossen, mit und ohne das Profil. Die Startzeile des Plans hätte also nicht funktioniert, und der Fehler wäre in Plan 17-03 als kaputte Compose-Datei gelesen worden.
- **Fix:** WR-11 bleibt, weil ein Vorgabewert für ein Geheimnis in einem öffentlichen Repository das teurere Übel ist. Stattdessen steht der Messwert samt Begründung im Kopf von `compose.spike-opendesk.yml`, in `.env.spike-opendesk.example` und im Kopf des Bootstrap-Skripts, jeweils mit dem vollständigen Exportblock. Keycloak bekommt aus demselben Grund **kein** Pflichtgeheimnis: das wäre ein dritter Export für jedes Kommando der Stufe A. Plan 17-07 gibt die Bootstrap-Zugangsdaten beim Start des Profils mit; die Variablennamen stehen in der Beispieldatei.
- **Dateien:** `compose.spike-opendesk.yml`, `.env.spike-opendesk.example`, `scripts/bootstrap_spike_opendesk.sh`
- **Commit:** 712a4ef

**9. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01] OD-01 und OD-02 bleiben Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter dieses Plans nennt `requirements: [OD-01, OD-02]`, und `requirements mark-complete` hätte beide abgehakt. Der Wortlaut trägt das nicht: OD-01 verlangt den Installationsweg, der ausdrücklich offen ist und als Terminfrage an ZenDiS geht; OD-02 verlangt Weg 0 und Weg 1 mit Messwerten nebeneinander, und von den beiden ist in diesem Plan keiner gemessen. Dieser Plan liefert von OD-02 genau einen Teil, die SSRF-Frage.
- **Fix:** Beide bleiben auf `Pending`, abgehakt werden sie am Ende der Phase durch 17-09. Das folgt der Entscheidung aus 17-01 (dort Abweichung 2) und der Projektregel, Nachweise wörtlich zu nehmen.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

Sonst keine. Der Ungemessen-Rückfall aus Task 1 wurde **nicht** gebraucht: der Heartbeat hielt im ersten Lauf, S0 ist gemessen, und keiner der Folgepläne fällt unter die Ungemessen-Reichweite. Die zwei Bedingungen, die der Plan für 17-03 und 17-04 prüfen lässt, sind trotzdem geprüft: `caddy` steht auf `running`, und `docker network inspect nc-mcp-spike-od-net -f '{{.Name}}'` antwortet mit dem Netznamen.

## Authentication Gates

Keine. Alle Zugangsdaten dieses Plans sind Wegwerfwerte, die der Bootstrap selbst erzeugt und in die git-ignorierte Verbindungsdatei schreibt. Kein fremder Dienst, kein Login, kein API-Schlüssel.

## Verification

- `docker compose -f compose.spike-opendesk.yml ps`: `caddy`, `appapi-harp`, `nextcloud`, `registry` auf `running`. Kein `openproject`, kein `keycloak`.
- `occ status`: `installed: true`, `version: 33.0.7.1`, `versionstring: 33.0.7`. Der Berichtskopf nennt denselben Wert.
- Alle vier Zeichenketten des Task-1-Gates gefunden, `grep -c "127.0.0.1:"` ergibt 5, kein Treffer für eine andere Bindeadresse, `.gitignore` trägt die Zeile exakt.
- `caddy validate`: `Valid configuration`. `bash -n scripts/bootstrap_spike_opendesk.sh`: fehlerfrei.
- Task-2- und Task-3-Gate: alle Teilbedingungen erfüllt, Ausgangswert 0.
- `uv run pytest -q`: grün, 0 Fehlschläge. Vor diesem Plan war die Suite rot (siehe Abweichung 4).
- `git status --short src/ appinfo/ pyproject.toml uv.lock`: leer. `files_modified` nennt keinen Pfad unter `src/` (D-12).
- Kein U+2014 und kein U+2013 in `docs/spike-opendesk.md`, keine ASCII-Ersatzschreibung von Umlauten, kein Treffer des Geheimnis-Gates, kein Treffer des Vokabular-Gates.
- Keine der drei Commits löscht eine verfolgte Datei (`git diff --diff-filter=D` je leer).

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: die Abschnitte 2.1, 2.2, 2.4, 2.5, 3, 4 und "Was diese Messung nicht beweist" tragen weiter je eine Zeile `noch nicht gemessen` mit Planzuordnung. Vier Kopfzeilen (`integration_openproject`, `user_oidc`, OpenProject, Keycloak) tragen dasselbe, jetzt mit den richtigen Plannummern 17-03 und 17-07 statt 17-02. Die Dienste `openproject` und `keycloak` stehen in der Compose-Datei und sind ungestartet: das ist der von Pitfall 1 verlangte Schnitt, kein unfertiger Zustand.

## Threat Flags

Keine neue Fläche über das hinaus, was das Bedrohungsmodell des Plans schon führt. Zwei Anmerkungen zu Einträgen daraus:

- **T-17-02, verschärft statt abgeschwächt:** die unauthentifizierte Registry liegt auf `127.0.0.1:5001`, und die Portnummer ist ausdrücklich eine andere als die der ExApp-Topologie, damit kein Bild versehentlich in die falsche Registry geschoben wird.
- **T-17-SC, ergänzt:** die HaRP-Bildmarke bleibt der gleitende Tag der bestehenden Lage, wie das Modell es vorsieht. Die gelaufene Fassung steht als Digest `sha256:3b335650` mit Erstellungsdatum 2026-08-14 im Berichtskopf, damit die Aussage über diese Instanz nachprüfbar bleibt.

## Hinweise für die Folgepläne

1. **Zwei Exporte vor jedem compose-Kommando**, auch vor `ps`: `HP_SHARED_KEY` und `SECRET_KEY_BASE`. `HP_SHARED_KEY` steht in der git-ignorierten `.env.spike-opendesk` und muss derselbe Wert bleiben wie beim Start des HaRP-Containers.
2. **Nur eine Topologie dieses Repositories kann die ExApp betreiben.** Die ExApp-Topologie ist angehalten; wer sie startet, holt sich den Containernamen zurück und bricht die Messumgebung der Phase.
3. **Speicher prüfen, bevor Stufe B startet** (siehe die erste Tabelle oben).
4. **`op.localtest.me:8082` ist der eine Name**, unter dem OpenProject für Browser und für Nextcloud erreichbar ist; die Portnummer ist innen und außen gleich, und das ist Absicht.
5. **Keycloak braucht `KC_BOOTSTRAP_ADMIN_USERNAME` und `KC_BOOTSTRAP_ADMIN_PASSWORD` beim Start des Profils** und sein Band muss zwischen zwei Realm-Importen verworfen werden, weil `--import-realm` eine vorhandene Realm überspringt.

## Self-Check: PASSED

Alle sechs in diesem SUMMARY genannten Dateien existieren (`compose.spike-opendesk.yml`, `deploy/Caddyfile.spike-opendesk`, `scripts/bootstrap_spike_opendesk.sh`, `.env.spike-opendesk.example`, `docs/spike-opendesk.md`, dieses SUMMARY), und alle drei Commit-Kennungen (712a4ef, d9acfe8, 16c6c6e) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` ist grün, und die vier Dienste der Stufe A laufen. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt.
