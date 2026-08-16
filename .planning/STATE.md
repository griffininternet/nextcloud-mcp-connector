---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 03-08-PLAN.md
last_updated: "2026-08-16T04:45:00.000Z"
last_activity: 2026-08-16
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 30
  completed_plans: 29
  percent: 48
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-14)

**Core value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Current focus:** Phase 3, OAuth 2.1

## Current Position

Phase: 3
Plan: 9 of 9
Status: In progress
Last activity: 2026-08-16

Progress: [█████████░] 97%

## Performance Metrics

**Velocity:**

- Total plans completed: 29
- Average duration: 35 min
- Total execution time: 15.2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 14 | - | - |
| 2 | 7 | 254 min | 36 min |
| 3 | 8 | 400 min | 50 min |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01-server-kern P01 | 24 min | 3 tasks | 10 files |
| Phase 01-server-kern P02 | 18 min | 3 tasks | 21 files |
| Phase 01-server-kern P12 | 14 min | 3 tasks | 2 files |
| Phase 01-server-kern P03 | 25 min | 3 tasks | 10 files |
| Phase 01-server-kern P04 | 20 min | 3 tasks | 12 files |
| Phase 01-server-kern P06 | 27 min | 2 tasks | 13 files |
| Phase 01-server-kern PP07 | 34 min | 3 tasks | 13 files |
| Phase 01-server-kern P08 | 25 min | 2 tasks | 10 files |
| Phase 01-server-kern P05 | 16 min | 2 tasks | 13 files |
| Phase 01-server-kern P09 | 13 min | 2 tasks | 10 files |
| Phase 01-server-kern P10 | 15 min | 2 tasks | 12 files |
| Phase 01-server-kern P11 | 74 min | 2 tasks | 11 files |
| Phase 01-server-kern P14 | 71 min | 3 tasks | 13 files |
| Phase 02-exapp-shell P01 | 30 min | 3 tasks | 15 files |
| Phase 02-exapp-shell P02 | 15 min | 3 tasks | 10 files |
| Phase 02-exapp-shell P03 | 32 min | 3 tasks | 8 files |
| Phase 02-exapp-shell P04 | 63 min | 3 tasks | 10 files |
| Phase 02-exapp-shell P05 | 14 min | 3 tasks | 5 files |
| Phase 02-exapp-shell P06 | 45 min | 2 tasks | 3 files |
| Phase 02-exapp-shell P07 | 55 min | 3 tasks | 6 files |
| Phase 03 P01 | 65 min | 3 tasks | 15 files |
| Phase 03 P03 | 20 min | 2 tasks | 6 files |
| Phase 03 P02 | 95 min | 3 tasks | 15 files |
| Phase 03 P04 | 25 min | 3 tasks | 14 files |
| Phase 03 P05 | 35 min | 3 tasks | 14 files |
| Phase 03 P06 | 40 min | 3 tasks | 16 files |
| Phase 03 P07 | 40 min | 3 tasks | 11 files |
| Phase 03 P08 | 80 min | 3 tasks | 11 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 6 Research-Phasen auf 5 komprimiert (Kern + Streamable HTTP zusammengelegt); Settings/prepare_context und Hardening/Store getrennt gehalten
- Roadmap: App-ID-Freeze (EXAPP-03) und context_agent#227-Fix (CONTRIB-01) bewusst in Phase 1 (Long-Lead-Risiken früh)
- Roadmap: Discovery-durch-AppAPI-Proxy-Spike (AUTH-06) in Phase 2 als Go/No-Go, BEVOR die OAuth-Phase committet wird
- Roadmap: CSR-PR-Start ist von Phase 5 entkoppelt, startet sobald App-ID + Public Repo existieren
- [Phase 01-server-kern]: httpx2 bleibt ausschliesslich transitive Dependency von mcp: slopcheck [SUS]-Befund; Owner-Freigabe nach Verifikation (pydantic-Org, Tom Christie); eigener Code nutzt httpx, weil respx httpx mockt
- [Phase 01-server-kern]: ruff schliesst .planning/ aus: ruff formatiert Python-Bloecke in Markdown; Research-Dokumente muessen wortgetreu bleiben
- [Phase 01-server-kern]: files_read lehnt nur oberhalb von 2 MiB komplett ab; darunter liefert es eine markierte Teilantwort mit next_offset: Ein harter Abbruch bei 512 KiB wuerde grosse Textdateien unlesbar machen; die Truncation-Markierung schuetzt den Kontext genauso
- [Phase 01-server-kern]: reg_*-Module werden in server/__init__.py per pkgutil automatisch importiert: Jedes Tool-Bundle bekommt seine eigene Registrierungsdatei, damit parallel laufende Plaene keine gemeinsame Datei aendern
- [Phase 01-server-kern]: parse_multistatus lehnt jede DTD im Antwortkoerper ab, nicht nur die Entity-Aufloesung: Nextcloud sendet nie eine DTD; ein DOCTYPE ist damit ein Signal und keine Sonderform, die man tolerieren muesste (XXE, Billion Laughs)
- [Phase 01-server-kern]: Nur SRV-02 wird abgehakt; SRV-03, SRV-05, TOOL-01 und AUTH-01 bleiben Pending: Der Walking Skeleton liefert ein Tool und einen Transport; die vollen Nachweise gehoeren zu Plan 04 (HTTP) und Plan 14 (alle 15 Tools)
- [Phase 01-server-kern]: Repo-Sichtbarkeit option-a: alles oeffentlich inklusive .planning (Owner-Entscheidung, T-01-84 accept)
- [Phase 01-server-kern]: PyPI-Verfuegbarkeit nur ueber die JSON-API und den Simple-Index pruefen: die HTML-Projektseite liefert wegen einer Bot-Challenge auch fuer freie Namen 200
- [Phase 01-server-kern]: TOOL-09 bleibt Pending: der README-Nachweis reicht nicht, die Schreibgrenzen belegt erst der Grep- und Registry-Test in Plan 14
- [Phase 01-server-kern]: Annahme A1 bestaetigt: Nextcloud 34.0.2 antwortet auf PUT mit If-None-Match: * bei existierender Datei mit 412; Laufzeitbeweis gegen nextcloud:34-apache; der geplante PROPFIND-Fallback mit TOCTOU-Restrisiko entfaellt
- [Phase 01-server-kern]: occ-Kommandos mit Passwort laufen ueber 'docker compose exec -e OC_PASS=...', Testnutzer-Passwoerter mindestens 10 Zeichen; Grund: eine auf dem Host gesetzte Variable erreicht den Container nie, und Nextclouds Passwort-Policy lehnt kuerzere Passwoerter ab
- [Phase 01-server-kern]: select_mode nimmt die Header als Keyword dazu: aus dem Environment allein ist stdio nicht erkennbar, denn ein stdio-Prozess hat konstruktionsbedingt keine Header
- [Phase 01-server-kern]: Die Auth-Verdrahtung entsteht beim Bau des MCPServer in server/__init__.py: auth= und token_verifier= sind Konstruktorargumente, ein Moduswechsel ist ein Neustart
- [Phase 01-server-kern]: Im Static-Bearer-Modus bleibt der Nextcloud-Zugang aus dem Env: der Bearer authentifiziert den Aufrufer dieses Servers, er waehlt keinen Nextcloud-Nutzer
- [Phase 01-server-kern]: Die Nextcloud-Basis-URL kommt in jedem Modus aus NC_MCP_URL, nie aus dem Request: ein Client, der das Ziel waehlen koennte, koennte diesen Server samt Credentials auf einen fremden Host richten
- [Phase 01-server-kern]: Der Default-Testlauf deselektiert jetzt auch den matrix-Marker, damit 'uv run pytest' keinen Serverprozess startet
- [Phase 01-server-kern]: AUTH-01 bleibt Pending: Basic-Passthrough und Static Bearer sind unit-getestet, der Remote-Rundlauf mit echtem App-Passwort gegen eine laufende Nextcloud fehlt noch
- [Phase 01-server-kern]: OCS-Aufrufe tragen immer OCS-APIRequest: true und Accept: application/json; getrennte Parser parse_ocs und parse_app_json, weil Notes und Deck nicht im OCS-Envelope antworten
- [Phase 01-server-kern]: notes_search laeuft ueber den Unified-Search-Provider notes: die Notes-REST-API hat keine Search-Route; Titel und Excerpt kommen aus dem Search-Entry, also ein Request statt einem pro Treffer
- [Phase 01-server-kern]: Notiz-IDs werden aus resourceUrl geparst und Treffer ohne numerisches Endsegment uebersprungen; die zurueckgegebene url wird immer aus der konfigurierten Basis-URL gebaut (SSRF-Grenze)
- [Phase 01-server-kern]: Der Capabilities-Cache haelt 60 Sekunden pro (base_url, user), enthaelt keine Credentials und darf jederzeit leer sein; tools/list bleibt statisch
- [Phase 01-server-kern]: 507 behaelt eine eigene Meldung (Speicher voll) statt im generischen 5xx-Zweig zu verschwinden
- [Phase 01-server-kern]: AUTH-01 abgehakt: uvicorn ohne Nextcloud-Konto im Environment legt per HTTP mit dem App-Passwort aus dem Request eine Notiz an und liest sie zurueck
- [Phase 01-server-kern]: Eine per occ deaktivierte App bleibt in /cloud/capabilities sichtbar, bis die Nextcloud neu startet; Degradations-Tests brauchen den Neustart, unser eigener Cache ist nicht die Ursache
- [Phase 01-server-kern]: Recurrence-Expansion laeuft serverseitig per c:expand; das CalDAV-Modul enthaelt keine RRULE-Iteration und kein recurring-ical-events, ein Grep-Test haelt diese Grenze
- [Phase 01-server-kern]: Das halboffene Zeitfenster wird nie korrigiert: ein Termin exakt auf end liegt ausserhalb, ein Verschieben der Grenze wuerde zwei Aufrufer mit demselben Fenster unterschiedliche Ergebnisse sehen lassen
- [Phase 01-server-kern]: Ganztaegige Termine behalten das exklusive Enddatum aus RFC 5545; start gleich end wird auf start plus ein Tag korrigiert, damit kein Termin der Laenge null entsteht
- [Phase 01-server-kern]: calendar_create_event bekommt einen optionalen timezone-Parameter (Abweichung von der Plan-Signatur), weil ein ISO-Offset keine IANA-Zone ist und ohne Zonennamen kein IANA-VTIMEZONE erzeugbar waere
- [Phase 01-server-kern]: Nach dem Event-PUT wird einmal per GET nachgelesen; scheitert das Nachlesen, bleibt created true und confirmed false, damit das Modell den Termin nicht ein zweites Mal anlegt
- [Phase 01-server-kern]: Faellt ein einzelner Kalender aus, erscheint er als degraded-Eintrag; fallen alle aus, ist das ein Fehler und keine leere Terminliste
- [Phase 01-server-kern]: Generierte Adressbuecher (z-server-generated--, z-app-generated--) zaehlen nicht als Adressbuecher des Nutzers; sonst waere 'kein Adressbuch' auf jedem echten Server unerreichbar und eine Namenssuche wuerde das Kontenverzeichnis der Instanz mitliefern
- [Phase 01-server-kern]: contacts_search bleibt rein lesend, es gibt keinen CardDAV-Schreibpfad in Phase 1; D-07 plus T-01-57; ein Grep-Test haelt das Modul frei von schreibenden Methoden
- [Phase 01-server-kern]: Cursor-Handles sind unsigniert und tragen nur Offset, Suchbegriff und Ordner: sie enthalten kein Geheimnis und keine Autoritaet, die Credentials kommen pro Aufruf aus dem Auth-Kanal (T-01-33)
- [Phase 01-server-kern]: Ein Handle aus einer anderen Suche oder einem anderen Ordner wird abgelehnt statt still auf die falsche Seite angewendet
- [Phase 01-server-kern]: files_search behaelt die Serverreihenfolge (Folgeseiten entstehen aus groesserem d:limit plus Slice); files_list sortiert selbst, Ordner zuerst, dann Name
- [Phase 01-server-kern]: propfind_children erkennt den Ordner selbst am Pfad statt an der Position und gibt ihn mit zurueck, damit ein Dateipfad ohne zweiten Request erklaert werden kann
- [Phase 01-server-kern]: Das note-Feld 'matched on names only; contents are not indexed' steht in jeder Suchantwort, nicht nur bei null Treffern (Pitfall 5, gegen NC 34 verifiziert)
- [Phase 01-server-kern]: canCreateBoards false beendet deck_create_card nicht sofort, sondern loest eine Pruefung der Board-Rechte aus; canCreateBoards regelt in Deck nur neue Boards; ein Nutzer ohne dieses Recht kann Schreibrechte auf einem geteilten Board haben, eine woertliche Ablehnung waere falsch negativ
- [Phase 01-server-kern]: deck_browse ist ein Tool mit Literal-Enum level statt drei Tools; level=cards kostet genau einen Request; D-06 plus Token-Budget und Client-Slots; GET /boards/{id}/stacks liefert die Karten bereits mit, ein Request pro Stack waere N+1
- [Phase 01-server-kern]: Deck-API-Version 1.0 statt 1.1 und numerische Pflicht fuer alle Pfad-Ids; 1.1 bringt nur Attachment-Typen, 1.0 laeuft auf mehr Instanzen; nicht numerische Ids kaemen aus Modell-Eingaben direkt in den URL-Pfad (T-01-63)
- [Phase 01-server-kern]: unified_search liest die Provider-Liste bei jedem Aufruf frisch von der Instanz und cacht sie nicht: die Provider-Landschaft haengt an installierten Apps, eine hardgecodete Liste wuerde eine App verpassen oder eine erfinden
- [Phase 01-server-kern]: Unbekannte Provider und unbrauchbare resourceUrls ergeben kind url plus resolvable false statt einer geratenen Zuordnung; der Kalender-Provider bleibt bewusst draussen, weil seine resourceUrl keinen DAV-Objektnamen traegt
- [Phase 01-server-kern]: Ausgefallene, zu langsame und unbekannt angefragte Provider erscheinen namentlich im degraded-Feld; null Provider auf der Instanz ist dagegen ein Fehler mit Ausweg, weil eine leere Trefferliste dort eine Luege waere
- [Phase 01-server-kern]: providers ist ein kommaseparierter String statt einer Liste: ein Listen-Parameter erzeugt ein anyOf aus array und null im Input-Schema (Schema-Diaet)
- [Phase 01-server-kern]: pytest laeuft im Import-Modus importlib, weil Unit- und Integrationsebene denselben Testdateinamen tragen duerfen sollen
- [Phase 01-server-kern]: TOOL-06 bleibt Pending: der provider-parallele Fan-out ist live belegt, der Negativbeweis der Berechtigungstreue mit zwei Konten gehoert in Plan 01-14
- [Phase 01-server-kern]: Der #227-Fix macht stateless_http konfigurierbar statt hart False: der Default behebt den Bug, MCP_STATELESS_HTTP=1 erhaelt das alte Verhalten; minimaler Diff, hoechste Merge-Wahrscheinlichkeit
- [Phase 01-server-kern]: Der Regressionstest der #227-Klasse bleibt bei uns (tests/compat/legacy_client_check.py); im fremden CI braeuchte er ein zweites Client-Environment gegen einen laufenden ExApp-Container und erzeugte nur Rauschen
- [Phase 01-server-kern]: Upstream-Beitraege laufen im Fork ausserhalb unseres Repos, mit lokal gesetzter git-Identitaet street1983nk / k.cherif@outlook.de und git commit -s (DCO); die Einreichung loest immer der Owner aus
- [Phase 01-server-kern]: search und fetch sind die einzigen Tools MIT Output-Schema (kein structured_output=False); mcp 2.x erzeugt aus dem Pydantic-Rueckgabetyp structured_content und content gleichzeitig, genau die Doppelung, die OpenAI verlangt
- [Phase 01-server-kern]: graceful ist generisch (PEP 695), weil eine auf str festgenagelte Dekorator-Signatur genau die Return-Annotation geloescht haette, aus der das SDK das Output-Schema baut
- [Phase 01-server-kern]: file:<fileid> wird per WebDAV-SEARCH mit d:eq auf oc:fileid in einen Pfad aufgeloest, live gegen Nextcloud 34 verifiziert; die Unified Search liefert nur die fileid, nie den Pfad
- [Phase 01-server-kern]: Die Deck-Kurzform wird per Sweep aufgeloest (ein Request pro Board, Abbruch beim Fund, Cache nur innerhalb des Aufrufs); die interne Route aus A4 wird nicht benutzt und steht deshalb nirgends woertlich im Modul, weil ein Grep-Test sie fernhaelt
- [Phase 01-server-kern]: fetch beantwortet eine url-ID mit einem ToolError, dessen Hinweis die URL traegt: ein Erfolgsergebnis ohne Inhalt ist die Form, die zum Erfinden einlaedt (T-01-75)
- [Phase 01-server-kern]: SRV-03 bleibt Pending: Annotationen und Budget-Gate stimmen fuer alle 15 Tools, die Abnahme gehoert nach Plan 01-14
- [Phase 01-server-kern]: Das Token-Budget-Gate steht auf dem gemessenen Wert plus 15 Prozent (10643 -> 12500 Bytes): 24000 war mehr als das Doppelte der Messung; ein Gate, das nie ausloest, schuetzt nichts
- [Phase 01-server-kern]: Das Destruktiv-Gate filtert Kommentare und Docstrings per AST, behaelt aber String-Literale: Der ehrliche Satz in dav.py wuerde ein naives Grep rot faerben; method=DELETE ist das eigentliche Ziel
- [Phase 01-server-kern]: Vulture laeuft bei voller Konfidenz mit annotierter Whitelist statt --min-confidence 80: Bei 80 meldete der CI-Schritt gar nichts und konnte nie fehlschlagen
- [Phase 01-server-kern]: Die README-Tool-Tabelle wird im Contract-Test gegen die laufende Registry geprueft statt von Hand gepflegt: Eine handgepflegte Tabelle veraltet beim ersten neuen Tool; die Registry ist die einzige Wahrheit
- [Phase 01-server-kern]: Modul-globaler veraenderlicher Zustand ist im Produktionscode verboten, mit genau zwei namentlich gelisteten Ausnahmen: Ein Dictionary, das eine Anfrage ueberlebt, ist einen Refactor von einem Session-Store entfernt und bricht den Restart-Beweis
- [Phase 01-server-kern]: CONTRIB-01 bleibt Pending und Success Criterion 5 nur zur Haelfte erfuellt: Die App-ID ist eingefroren und dokumentiert, aber der PR an context_agent 227 ist ein Owner-Schritt und noch nicht eingereicht
- [Phase 02-exapp-shell]: Die Lifecycle-Routen werden von einer Fabrik geliefert und nur von entry_exapp angehaengt, nicht per Dekorator am geteilten Serverobjekt registriert: eine Registrierung am Singleton wuerde /heartbeat, /init und /enabled auch im eigenstaendigen HTTP-Modus erscheinen lassen, sobald irgendein Import das Modul beruehrt (D-23)
- [Phase 02-exapp-shell]: Der ExApp-Modus gewinnt in select_mode gegen den statischen Bearer, aber nie gegen stdio; ein Prozess mit beiden Kanaelen wird beim Start mit Exit-Code 2 abgelehnt statt pro Request still aufgeloest (D-27)
- [Phase 02-exapp-shell]: Die AppAPI-Variablen tragen bewusst kein NC_MCP_-Praefix (APP_ID, APP_SECRET, APP_VERSION, AA_VERSION, APP_HOST, APP_PORT, APP_PERSISTENT_STORAGE, HP_SHARED_KEY, HP_EXAPP_SOCK, NEXTCLOUD_URL): die Namen gibt der AppAPI-Deploy-Daemon vor
- [Phase 02-exapp-shell]: /init antwortet auch dann 200, wenn der OCS-Fortschritts-Push scheitert; ein 500 wuerde die Installation abbrechen, ein verpasster Push kostet nur eine Logzeile (Pitfall 3)
- [Phase 02-exapp-shell]: Jede Lifecycle-Antwort traegt Cache-Control: no-store aus einer einzigen Hilfsfunktion; der PHP-Proxy cacht JSON sonst 3600 Sekunden (Pitfall 4)
- [Phase 02-exapp-shell]: Ein anliegender x-origin-ip-Header beendet /init und /enabled mit 404: nur der PHP-Proxy setzt ihn, und der schuetzt diese Pfade nicht, haengt aber gueltige AppAPI-Header selbst an (Pitfall 2)
- [Phase 02-exapp-shell]: EXAPP-01 und AUTH-05 bleiben Pending: dieser Plan belegt den Kontrakt in-process, der Installationsnachweis braucht Dockerfile, info.xml und eine laufende Nextcloud (Plaene 02-03 bis 02-05)
- [Phase 02-exapp-shell]: mode bleibt ein str-Feld mit benannten Konstanten statt eines Literal-Typs; sonst waere der Ablehnungszweig fuer einen dritten Modus im Test nur mit type: ignore erreichbar, und ein untestbarer Zweig schuetzt nichts
- [Phase 02-exapp-shell]: Der ExApp-Zweig steht vor dem Passthrough-Zweig und liest den Authorization-Header nie; HaRP reicht einen mitgeschickten Basic-Header durch, ein zweiter akzeptierter Kanal waere genau der stille Fallback, den D-27 verbietet (T-02-11)
- [Phase 02-exapp-shell]: Das Quelltext-Gate gegen hart verdrahtetes BasicAuth liest das gesamte clients-Paket statt einer Dateiliste; ein siebtes Client-Modul faellt damit ohne Testaenderung unter dasselbe Verbot (T-02-15)
- [Phase 02-exapp-shell]: AUTH-05 bleibt Pending, obwohl der vierte Credential-Modus steht; der Weg von AUTHORIZATION-APP-API bis in jede Anfrage ist unit-belegt, der Negativbeweis mit zwei Konten gegen eine laufende Nextcloud gehoert zu Plan 02-05
- [Phase 02-exapp-shell]: uv sync laeuft im Image mit --no-editable, damit die Laufzeitstufe nur die virtuelle Umgebung traegt und keine zweite Kopie von src; nc-mcp-exapp liegt danach als fertiges Skript in /app/.venv/bin
- [Phase 02-exapp-shell]: /frpc.toml wird im Image als leere Datei mit Eigentuemer 10001 angelegt, statt Schreibrechte auf / zu vergeben: start.sh bleibt damit woertlich das HaRP-Original, und ein unprivilegierter Prozess darf eine eigene Datei kuerzen
- [Phase 02-exapp-shell]: Das Volume-Ziel /nc_app_mcp_connector_data entsteht im Image mit Eigentuemer 10001, weil ein frisches Docker-Volume Eigentuemer und Modus des ueberdeckten Verzeichnisses erbt (DockerActions::buildDefaultExAppVolume)
- [Phase 02-exapp-shell]: Der Manifest-Gate vergleicht nicht nur eine Wortliste weiter Regexe, sondern matcht jede deklarierte Route gegen /heartbeat, /init und /enabled; eine Gegenprobe im Test belegt, dass das Gate ausloest
- [Phase 02-exapp-shell]: Der CI-Job image bekommt docker/setup-qemu-action zusaetzlich zu setup-buildx-action, weil die arm64-Haelfte des Matrix-Baus auf einem amd64-Runner sonst nicht ausfuehrbar ist; veroeffentlicht wird nichts (D-25)
- [Phase 02-exapp-shell]: EXAPP-01 bleibt Pending: das installierbare Paket existiert (Image plus Manifest), der Nachweis der Installation durch den Deploy Daemon gehoert zu Plan 02-04
- [Phase 02-exapp-shell]: Die HaRP-Testtopologie ist ein zweites compose-File mit eigenem Projektnamen nc-mcp-exapp, eigenem Volume, eigenem Netz und Port 8081 (D-31); die vom Owner genutzte Instanz aus compose.test.yml bleibt dadurch unberuehrt, und ein Test haelt fest, dass das Bootstrap-Skript sie nicht einmal erwaehnt
- [Phase 02-exapp-shell]: access_level wandert als Zahl in die json-info-Registrierung: AppAPI mappt PUBLIC/USER/ADMIN nur auf dem info.xml-Pfad, eine json-info-Registrierung schreibt den Wert roh in die Integer-Spalte von ex_apps_routes
- [Phase 02-exapp-shell]: Der ExApp-Port liegt bei 23000, weil der FRP-Server in HaRP nur 23000 bis 23999 erlaubt; ausserhalb meldet frpc port not allowed und HAProxy antwortet ohne Backend mit 503
- [Phase 02-exapp-shell]: Das Image legt /certs fuer uid 10001 an, weil HaRP das FRP-Client-Zertifikat mit der Identitaet des Containers installiert; ohne das Verzeichnis scheitert die Zertifikatsinstallation mit 500 und der Tunnel bleibt ungesichert und damit tot
- [Phase 02-exapp-shell]: EXAPP-01 ist abgehakt: occ app_api:app:list meldet mcp_connector als enabled, deploy und init stehen auf 100, der MCP-Endpunkt wird mit dem App-Passwort eines Nutzers bedient; der AIO-Nachweis bleibt Sache von Plan 02-07
- [Phase 02-exapp-shell]: AUTH-06 ist GO und abgehakt: die RFC-9728-Metadaten sind unauthentifiziert von aussen ueber BEIDE Proxy-Wege erreichbar (HaRP und PHP-Proxy je 200 mit JSON), der WWW-Authenticate-resource_metadata-Zeiger passiert beide Proxys unveraendert; die Discovery-Route leckt nichts (nur oeffentliche URL plus Methodenliste, kein Secret, kein interner Host)
- [Phase 02-exapp-shell]: Der kanonische RFC-9728-Wurzelpfad ist 404 und gehoert Nextcloud, nicht der ExApp; Phase 3 setzt auf den resource_metadata-Zeiger (SEP-985 Prioritaet 1) plus eine Admin-Reverse-Proxy-Regel als getesteten Fallback (Caddy und nginx in docs/spike-discovery.md)
- [Phase 02-exapp-shell]: Die Discovery-Sonde ist bewusst ein Spike-Artefakt (T-02-44): der 401 stammt aus einer eigenen Sonde unter /.well-known/, nicht aus /mcp, weil /mcp in Phase 2 bewusst auf USER steht; Ersatz durch echte PRM aus AuthSettings plus /mcp auf PUBLIC ist Phase-3-Aufgabe
- [Phase 02-exapp-shell]: Ein unbekannter Bearer ueber HaRP auf der USER-Route /mcp wird 403 (sauberes 4xx, kein 5xx) beantwortet; damit kann ein spaeter PUBLIC gestelltes /mcp unbekannte Tokens an den eigenen Token-Verifier weiterreichen statt in einen 401 zu kippen (Open Question 4)
- [Phase 02-exapp-shell]: Die exapp-Topologie musste fuer die Messung neu aufgebaut werden (down -v, frischer Hex64-HP_SHARED_KEY): die in den Volumes von 02-04 gespeicherte HaRP-Daemon-Registrierung nutzte den alten Nicht-Hex-Schluessel, den der nach 02-04 eingezogene require_hex64-Gate (CR-02) ablehnt; nur das nc-mcp-exapp-Projekt betroffen, nc-mcp-test blieb unberuehrt
- [Phase 02-exapp-shell]: AUTH-05 ist abgehakt (DAV-Spike D-30, Fall A): alle sechs API-Familien (WebDAV, CalDAV, CardDAV, OCS, Notes, Deck) laufen unter AppAPI-Impersonation gegen NC 34.0.2 / AppAPI 34.0.0, die Identitaet ist serverseitig belegt (cloud/user liefert genau alice bzw. bob, exapp_impersonation.log protokolliert jeden Request); keine Provider-Aufteilung, kein App-Passwort-Rueckfall, Annahme A1 bestaetigt
- [Phase 02-exapp-shell]: Der Negativfall ist der Kern von AUTH-05: bob erreicht alices Datei auch bei bekanntem Pfad nicht (404, nie 200); der Confused-Deputy-Beweis zeigt, dass ein zusaetzlicher gueltiger Authorization-Basic-Header fuer alice die bob-Impersonation NICHT ueberschreibt (cloud/user bleibt bob), weil die Identitaet allein aus AUTHORIZATION-APP-API stammt
- [Phase 02-exapp-shell]: Zwei Kontrollpruefungen machen die Matrix beweiskraeftig: der messende Prozess traegt kein NC_MCP_APP_PASSWORD und keinen NC_MCP_STATIC_BEARER, und ein falsches APP_SECRET (64 Nullen) wird mit 401 abgewiesen; die Create-only-Grenze (If-None-Match: *) haelt unter Impersonation (zweites PUT 412)
- [Phase 02-exapp-shell]: AUTH-05 ist ueber die volle Kette bestaetigt (MCP-Client, HaRP, ExApp, Impersonation, Nextcloud-ACLs); bob findet nichts von alice ueber files_search, notes_search, unified_search und files_read, alice findet ihre eigenen Inhalte im selben Lauf (test_permission_fidelity_exapp.py, 9 gruen); die Middleware-Grenze haelt live (anonymes /mcp = 403, Heartbeat von aussen = 502)
- [Phase 02-exapp-shell]: Ein per occ user:add angelegter Nutzer hat ein leeres Files-Home ohne suchbaren Root; eine WebDAV-SEARCH antwortet dann 500 statt leer; ensure_files_home legt eine neutrale Datei an und scannt sie (wie ein Erst-Login-Skeleton), danach ist die SEARCH ein sauberes leeres Ergebnis
- [Phase 02-exapp-shell]: Der Nextcloud-AIO-Smoke ist Fall B; er scheitert an AIOs Domain-Validierung (oeffentliche Domain plus gueltiges TLS), ist mit fehlenden Schritten in docs/exapp-install.md dokumentiert und als benannter Punkt an Phase 5 uebergeben (D-31), nicht still gestrichen
- [Phase 03-oauth-2-1]: Der issuer der AS-Metadaten wird als exakter String auf die konfigurierte public_url gesetzt: AnyHttpUrl haengt einer pfadlosen URL einen Schraegstrich an, und RFC 8414 vergleicht den issuer zeichengenau
- [Phase 03-oauth-2-1]: Genau ein Tool-Scope nextcloud in der PRM; offline_access nur in den AS-Metadaten: D-42 plus MCP-Spec: offline_access gehoert weder in scopes_supported der PRM noch in den WWW-Authenticate-Scope
- [Phase 03-oauth-2-1]: token_endpoint_auth_methods_supported traegt zusaetzlich none: Claude.ai und ChatGPT kommen als public clients ohne Client-Secret; das SDK listet per Default nur die beiden Secret-Methoden
- [Phase 03-oauth-2-1]: Die Bearer-Grenze ist fail-closed: ohne konfigurierten Verifier ist jeder Bearer ungueltig: Manifest-Umstellung auf PUBLIC und eigene Pruefung entstanden in derselben Aenderung (Pitfall 6); der echte Verifier folgt in Plan 03-06
- [Phase 03-oauth-2-1]: Das Manifest deklariert je Dokument eine vollstaendig verankerte Route, das Gate faellt ohne Endanker: HaRP matcht mit re.match, ein Muster ohne Endanker trifft auch Nachbarn; damit ist AR-02-06 geschlossen
- [Phase 03-oauth-2-1]: Jede HTML-Seite der Phase entsteht in genau einer Funktion (exapp/ui/layout.py): CSP mit Nonce, X-Frame-Options, Referrer-Policy und no-store haben damit eine Quelle statt einer Kopie je Seite
- [Phase 03-oauth-2-1]: page() nimmt die Umgebung und nie den Request: die Absenderzeile (Wortmarke plus Host) kommt aus config.public_url, sonst koennte ein gefaelschter Host-Header umschreiben, wer nach Zugriff fragt
- [Phase 03-oauth-2-1]: Der Client-Name aus der DCR-Registrierung wird vor dem Escaping gesaeubert (Steuerzeichen weg, 80 Zeichen) und der Escaping-Test vergleicht Elementanzahlen statt Teilzeichenketten
- [Phase 03-oauth-2-1]: Nutzertexte stehen als Modulkonstanten in __all__: das ist der Katalog fuer eine spaetere Lokalisierung und zugleich der Grund, warum der vulture-Gate ohne Whitelist-Eintrag gruen bleibt
- [Phase 03-oauth-2-1]: link() und form() lehnen jedes Ziel ab, das kein lokaler Pfad ist: ein Open Redirect im Consent-Umfeld ist im Renderer billiger verboten als in fuenf Route-Handlern geprueft
- [Phase 03-oauth-2-1]: AUTH-02 und AUTH-03 bleiben Pending: Plan 03-03 haengt bewusst keine Route ein, die Bausteine allein sind weder Browser-Login noch OAuth-Verbindung
- [Phase 03-oauth-2-1]: Der Datenschluessel wird nach dem Schreiben zurueckgelesen: zwei gleichzeitig startende Worker finden beide keinen Schluessel und schreiben beide einen; ohne Rueckleseschritt verschluesselt der Verlierer alles mit einem Schluessel, den niemand mehr liest (D-43)
- [Phase 03-oauth-2-1]: Eine nicht lesbare ExApp-Config-Antwort wirft, statt als fehlender Schluessel zu gelten: sonst wuerde ein Parse-Fehler einen lebenden Schluessel ueberschreiben und alle Verbindungen toeten
- [Phase 03-oauth-2-1]: Die Refresh-Einloesung schreibt den Nachfolger in derselben Transaktion und unterscheidet drei Ausgaenge (unknown, expired, reused): nur der dritte toetet in 03-07 die Familie, und ein Absturz zwischen zwei Schreibvorgaengen darf keinen Nutzer ohne gueltigen Token zuruecklassen
- [Phase 03-oauth-2-1]: Die Gueltigkeit eines Access-Tokens ist ein Join auf die Autorisierung: ein Widerruf wirkt damit sofort und nicht erst beim naechsten Aufraeumen (SC 4)
- [Phase 03-oauth-2-1]: Die Schreibbarkeit des Volumes wird durch Schreiben geprueft, nicht durch os.access: Berechtigungsbits sagen nichts ueber einen read-only-Mount oder eine Windows-ACL
- [Phase 03-oauth-2-1]: Client-Verfall laeuft nur in purge_expired, nie im Schreibpfad: das Loeschen eines Clients nimmt ueber die Kaskade seine Autorisierungen mit
- [Phase 03-oauth-2-1]: cryptography ist ab 03-02 direkte Dependency (Owner-Freigabe 16.08.); der Lock-Schritt lief mit `uv lock` statt `uv add`, damit die .venv unberuehrt bleibt
- [Phase 03-oauth-2-1]: Das Destruktiv-Gate bekommt eine eng gefasste, gegengeprobte Ausnahme fuer SQL in oauth/store.py (DELETE FROM, ON DELETE CASCADE): TOOL-09 ist ein Versprechen ueber Daten in Nextcloud, nicht ueber die eigene SQLite-Datei
- [Phase 03-oauth-2-1]: Der Poll laeuft immer gegen die konfigurierte Basis-URL mit festem Pfad, nie gegen die absolute Adresse aus der Startantwort (Pitfall 7c); ein Test mit einer zweiten respx-Route belegt, dass diese Adresse nie aufgerufen wird
- [Phase 03-oauth-2-1]: 404 heisst bei Nextcloud gleichzeitig 'noch nicht fertig' und 'unbekannt oder abgelaufen'; die Unterscheidung kommt deshalb aus unserer eigenen Zwanzig-Minuten-Frist im Flow-Datensatz, nie aus der Antwort
- [Phase 03-oauth-2-1]: Der Client-Name wird vor dem Absenden auf druckbares ASCII reduziert, gekuerzt und mit festem Praefix versehen: er wird bei Nextcloud zum User-Agent und damit zum angezeigten Namen im Bestaetigungsdialog (Pitfall 8)
- [Phase 03-oauth-2-1]: Der Anmeldelink steht auf der Seite, die der Start erzeugt, und nicht auf der sich alle drei Sekunden neu ladenden Warteseite; ein Link, der drei Sekunden nach dem Erscheinen verschwindet, ist schlechter als einer, den 'Start over' neu holt
- [Phase 03-oauth-2-1]: Die Onboarding-Strecke bucht ihre Flows unter einer reservierten Client-Zeile mit allowed=false, weil die flows-Tabelle einen Fremdschluessel auf clients hat und dieser Weg gar keinen registrierten Client kennt
- [Phase 03-oauth-2-1]: Der Flow-Datensatz wird geloescht, bevor die Zugangsberechtigung gerendert wird (das 200 des Polls kommt genau einmal); schlaegt das Loeschen fehl, wird das gerade erzeugte App-Passwort widerrufen statt ungenutzt in Nextcloud zu bleiben
- [Phase 03-oauth-2-1]: Die prozessweite Store-Instanz und der purge_expired-Aufruf leben in der Closure der Routen-Fabrik, nicht als Modulglobale: ein Zustand, der Requests ueberlebt, ist sonst einen Refactor von einem Session-Store entfernt (D-20)
- [Phase 03-oauth-2-1]: Ein GET startet nie einen Anmeldevorgang; der zustandsaendernde Schritt der Browser-Strecke ist ein POST mit benannter Aktion (T-03-35)
- [Phase 03-oauth-2-1]: Die drei Schalter von AUTH-07 liegen in einem unveraenderlichen Policy-Objekt, das an vier Stellen befragt wird statt an einer: wer nur bei der Registrierung prueft, laesst einen spaeter gesperrten Client bis zum Token-Ablauf weiterlaufen (Pitfall 9)
- [Phase 03-oauth-2-1]: Der Allowlist-Modus mit leerer Liste sperrt alles: ein Admin, der den Modus einschaltet und die Liste vergisst, wollte schliessen und nicht oeffnen; ein unbekannter Wert eines Schalters behaelt dagegen den Default und wird geloggt, weil ein Tippfehler kein Sicherheitsschalter ist
- [Phase 03-oauth-2-1]: get_client liefert fuer unbekannt, gesperrt, nicht gelistet und verfallen dieselbe Antwort None und loescht dabei verfallene Registrierungen; die Fehlerseite waehlt danach allein die Admin-Konfiguration aus (E1/E2/E3), nie der Zustand eines Clients (T-03-47)
- [Phase 03-oauth-2-1]: Das Client-Secret wird nur als SHA-256-Hash gespeichert; der SDK-ClientAuthenticator vergleicht Klartext, deshalb bleibt der Token-Endpunkt fuer vertrauliche Clients bis zum eigenen Authenticator in 03-06 fail-closed
- [Phase 03-oauth-2-1]: Von den Routen aus create_auth_routes werden zwei verworfen: das AS-Metadatendokument (03-01 liefert das vollstaendige) und /authorize (oauth/consent.py steht davor, damit eine Ablehnung eine Seite ist und kein JSON im Browser)
- [Phase 03-oauth-2-1]: Der Anmeldelink des Login Flow v2 reist als Query-Parameter der Weiterleitung zur Consent-Seite, weil der flows-Tabelle die Spalte fehlt und eine Migration teurer waere; gerendert wird er nur, wenn sein Host die konfigurierte Nextcloud oder die eigene public_url ist (T-03-42)
- [Phase 03-oauth-2-1]: Die Autorisierung wird unter der Id ihres eigenen Flows angelegt; damit verbindet sie sich mit dem Flow-Datensatz ohne zusaetzliche Spalte, und das App-Passwort aus dem einmaligen 200 des Polls ist sofort verschluesselt abgelegt
- [Phase 03-oauth-2-1]: Jeder Link und jede Formular-Aktion traegt jetzt den Praefix aus config.public_url: HaRP strippt /exapps/<app> vor dem Request, ein absoluter Pfad ohne Praefix zeigte auf die Nextcloud-Wurzel (Fund und Fix in 03-05, betraf auch die /connect-Seiten aus 03-04)
- [Phase 03-oauth-2-1]: Das Anti-Faelschungs-Merkmal des Consent-Formulars ist ein HMAC der Flow-Id unter dem Datenschluessel, keine Spalte: es braucht keine Migration, ueberlebt Neustart und zweiten Worker und kann von niemandem erzeugt werden, der nicht diese Installation ist (T-03-50)
- [Phase 03-oauth-2-1]: Eine Ablehnung loescht die Autorisierung und gibt das App-Passwort in einem Versuch an Nextcloud zurueck; eine abgelehnte Verbindung darf keinen brauchbaren Zugang hinterlassen (D-34)
- [Phase 03-oauth-2-1]: Der Authorization-Code wird beim Laden nicht verbraucht, sondern erst im Tausch, in der einen atomaren Anweisung des Stores: sonst verbrennt ein falscher PKCE-Verifier einen gueltigen Code
- [Phase 03-oauth-2-1]: auth_codes bekommt die Spalte redirect_uri_explicit samt idempotentem ALTER; ohne sie kann der SDK-Vergleich der Rueckadresse nach dem Loeschen des Flow-Datensatzes nicht mehr stimmen
- [Phase 03-oauth-2-1]: Die Transportgrenze loest die Nextcloud-Identitaet eines geprueften Tokens einmal pro Request auf und legt sie in den Request-Zustand; deps.resolve_credentials ist synchron und darf im Tool-Aufruf weder lesen noch entschluesseln (D-26)
- [Phase 03-oauth-2-1]: Kein dritter MODE_-Wert: gegenueber Nextcloud ist ein App-Passwort Basic-Auth, der OAuth-Zweig baut MODE_BASIC-Credentials
- [Phase 03-oauth-2-1]: provider.load_access_token bleibt eine Absage, weil der ProviderTokenVerifier des SDK Prozess-Cache, Audience-Pruefung und Client-Policy umgehen wuerde; geprueft wird ausschliesslich ueber oauth/verifier.py
- [Phase 03-oauth-2-1]: /token und /revoke werden mit einem eigenen ClientAuthenticator neu gebaut, der gegen den gespeicherten Hash vergleicht; das SDK vergleicht ein Klartext-Secret, das dieser Store nicht haelt
- [Phase 03-oauth-2-1]: Das Gnadenfenster aus D-41 wiederholt genau die vorgehaltene Antwort und erzeugt nie einen zweiten Familienzweig; eine verlorene vorgehaltene Antwort ist invalid_grant und nie ein Familienwiderruf
- [Phase 03-oauth-2-1]: Eine Wiederverwendung ausserhalb des Fensters widerruft Familie UND Autorisierung, ausschliesslich im Store, und vermerkt das App-Passwort als Aufraeumaufgabe: der Token-Pfad ruft Nextcloud nie an (Pitfall 13)
- [Phase 03-oauth-2-1]: Der Widerruf laeuft in der Reihenfolge Store, Prozess-Caches, Nextcloud; der dritte Schritt darf fehlschlagen und haelt die ersten beiden nie auf (cleanup_at vermerkt den Fehlschlag)
- [Phase 03-oauth-2-1]: /revoke wird als FamilyRevocation neu gebaut, weil load_access_token bewusst absagt und der SDK-Handler sonst 200 antwortet, ohne irgendetwas zu widerrufen; das eigene Request-Modell macht client_secret optional, sonst bekaeme jeder oeffentliche Client 400
- [Phase 03-oauth-2-1]: Die Drosselung hat zwei Grenzen: eine je Quelle, die ein gefaelschter X-Forwarded-For aufteilen kann, und eine je Pfadklasse, die er nicht aufteilen kann; gezaehlt wird nach Antwortstatus, gespeichert wird nur ein SHA-256-Digest
- [Phase 03-oauth-2-1]: Der Sweep fuer nie entschiedene Anmeldungen haengt an der Autorisierungsanfrage, hart begrenzt auf drei je Aufruf: dieses Projekt hat keinen Cron, und wer neu verbindet, zahlt fuer die, die niemand zu Ende gebracht hat

- [Phase 03-oauth-2-1]: NC_MCP_PUBLIC_URL ist die eine Variable, ohne die OAuth nicht funktioniert, und der Deploy-Daemon reicht eine Variable nur durch, wenn das Manifest sie deklariert: appinfo/info.xml deklariert sie und die drei AUTH-07-Schalter, sonst wird `--env` akzeptiert und verworfen (gemessen gegen AppAPI 34.0.0)
- [Phase 03-oauth-2-1]: Die ExApp-Config wird mit POST auf .../ex-app/config/get-values und dem Rumpf {"configKeys": [...]} gelesen, nicht mit GET und configKeys[]; die Antwort nennt ihre Felder klein (configkey/configvalue), und beides zusammen war der Grund, warum kein Datenschluessel je gelesen werden konnte
- [Phase 03-oauth-2-1]: Der geteilte httpx-Client fuehrt keinen Cookie-Jar mehr: Nextcloud setzt auf jede Antwort ein Session-Cookie, und auf einem prozessweiten Client wurde daraus eine Sitzung fuer alle Nutzer (gemessen: SEARCH mit dem Scope des einen und der Identitaet des anderen Nutzers)
- [Phase 03-oauth-2-1]: SC 5 ist gemessen statt geschaetzt: genau ein Nextcloud-Roundtrip je MCP-Request mit Authorization-Header, angenommen wie abgelehnt; die eigene Drosselung antwortet beim elften abgelehnten Token-Request mit 429 und Retry-After 300, und der Testnutzer meldet sich danach normal an

### Pending Todos

- **AUTH-04 (Plan 03-09, Owner):** Claude.ai und ChatGPT gegen eine oeffentlich erreichbare Staging-Instanz. Alles, was ohne oeffentliche Domain messbar war, ist mit 03-08 gemessen; offen bleibt genau der Teil, der eine erreichbare Instanz und die beiden gehosteten Oberflaechen braucht.

- **Owner-Schritt 01-13:** PR an nextcloud/context_agent#227 einreichen. Branch und DCO-Commit liegen im Fork street1983nk/context_agent (fix/stateless-http-session-compat, def1425), der PR-Text in docs/contrib/227-pr-body.md. Kommando und Pruefpunkte stehen in .planning/phases/01-server-kern/01-13-SUMMARY.md. Vorher `git push origin main` im Connector-Repo, damit der verlinkte Regressionstest oeffentlich sichtbar ist. Danach PR-URL nachtragen, ROADMAP 01-13 abhaken, CONTRIB-01 auf Complete.
- **Owner-Schritt 01-14:** Ein Durchgang mit Claude Desktop selbst nach docs/client-setup.md. Die Anleitung ist gegen die Referenz-Clients der Testsuite verprobt (mcp 2.0 und mcp 1.29 gegen denselben laufenden Endpoint, plus scripts/acceptance_all_tools.py ueber alle 15 Tools per stdio); die Konfigurationspfade fuer Claude Desktop stammen aus der offiziellen Dokumentation und sind auf diesem Rechner nicht verifiziert.
- **Nextcloud-AIO-Smoke (Phase 5, D-31):** Der zweite Smoke-Schritt aus Success Criterion 1 ist an Phase 5 uebergeben. Er scheitert auf diesem Rechner an AIOs Domain-Validierung (oeffentliche Domain plus gueltiges TLS). Die fehlenden Schritte stehen in docs/exapp-install.md, Abschnitt Nextcloud AIO: Host mit oeffentlicher Domain und Zertifikat, AIO-Mastercontainer starten, optionalen HaRP-Container aktivieren (Annahme A6 unverifiziert), App als ExApp installieren, den Permission-Fidelity-Smoke wiederholen und occ app_api:app:list festhalten.
- **WR-12 Linux-socat-Loop (Phase 5):** Die Linux-Variante des --manual-Entwicklungsloops (socat auf das Compose-Gateway) ist dokumentiert, aber auf diesem Windows-Host nicht durchgespielt; Entwicklungs-Komfort, nicht der ausgelieferte Pfad.
- **ExApp-Topologie:** Nach 03-08 wieder heruntergefahren (`down` mit erhaltenen Volumes, danach `docker stop`/`docker rm nc_app_mcp_connector` und `docker network rm nc-mcp-exapp-net`). Wieder anfahren: `export HP_SHARED_KEY=$(openssl rand -hex 32)` und in DERSELBEN Zeile weiterarbeiten (die Shell-Env ueberlebt einen Aufruf nicht, und jedes `docker compose` gegen diese Datei braucht die Variable), `up -d --wait`, `occ app_api:app:unregister mcp_connector --silent --force`, `occ app_api:daemon:unregister harp_proxy_docker`, dann `bash scripts/bootstrap_exapp.sh` (baut das Image neu und setzt NC_MCP_PUBLIC_URL). Ohne das Neubauen laeuft ein veraltetes Image.
- **Aufraeumen (optional):** Die Docker-Testinstanz traegt jetzt zusaetzlich die Calendar-App 6.5.3 und die Abnahme-Artefakte. Fuer einen sauberen Stand: `docker compose -f compose.test.yml down -v` und danach `bash scripts/bootstrap_test_nc.sh`.

### Blockers/Concerns

- Harte Deadline: Store-Einreichung vor der Nextcloud Conference September 2026 (Scope kürzen, nie den Termin)
- CalDAV/CardDAV mit AppAPI-Auth-Headern: AUFGELOEST in 02-06 (DAV-Spike, beide Familien REPORT 207 unter Impersonation, serverseitig belegt); offen bleibt die Consent-Bridge über AppAPI-Proxy (Spike früh in Phase 3)
- Vor Phase 1 verifizieren: nc_py_api-Support für NC 34 (vermutlich nur Badge-Lag)

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-08-16T04:45:00.000Z
Stopped at: Completed 03-08-PLAN.md
Resume file: None
