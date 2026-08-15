---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Phase 2 context gathered
last_updated: "2026-08-15T04:46:18.653Z"
last_activity: 2026-08-14
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 14
  completed_plans: 14
  percent: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-14)

**Core value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Current focus:** Phase 2 — exapp shell

## Current Position

Phase: 2
Plan: Not started
Status: Ready to plan
Last activity: 2026-08-14

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 14
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 14 | - | - |

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

### Pending Todos

- **Owner-Schritt 01-13:** PR an nextcloud/context_agent#227 einreichen. Branch und DCO-Commit liegen im Fork street1983nk/context_agent (fix/stateless-http-session-compat, def1425), der PR-Text in docs/contrib/227-pr-body.md. Kommando und Pruefpunkte stehen in .planning/phases/01-server-kern/01-13-SUMMARY.md. Vorher `git push origin main` im Connector-Repo, damit der verlinkte Regressionstest oeffentlich sichtbar ist. Danach PR-URL nachtragen, ROADMAP 01-13 abhaken, CONTRIB-01 auf Complete.
- **Owner-Schritt 01-14:** Ein Durchgang mit Claude Desktop selbst nach docs/client-setup.md. Die Anleitung ist gegen die Referenz-Clients der Testsuite verprobt (mcp 2.0 und mcp 1.29 gegen denselben laufenden Endpoint, plus scripts/acceptance_all_tools.py ueber alle 15 Tools per stdio); die Konfigurationspfade fuer Claude Desktop stammen aus der offiziellen Dokumentation und sind auf diesem Rechner nicht verifiziert.
- **Aufraeumen (optional):** Die Docker-Testinstanz traegt jetzt zusaetzlich die Calendar-App 6.5.3 und die Abnahme-Artefakte. Fuer einen sauberen Stand: `docker compose -f compose.test.yml down -v` und danach `bash scripts/bootstrap_test_nc.sh`.

### Blockers/Concerns

- Harte Deadline: Store-Einreichung vor der Nextcloud Conference September 2026 (Scope kürzen, nie den Termin)
- MEDIUM confidence: CalDAV/CardDAV mit AppAPI-Auth-Headern (Spike Phase 2), Consent-Bridge über AppAPI-Proxy (Spike früh in Phase 3)
- Vor Phase 1 verifizieren: nc_py_api-Support für NC 34 (vermutlich nur Badge-Lag)

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-08-15T04:46:18.638Z
Stopped at: Phase 2 context gathered
Resume file: .planning/phases/02-exapp-shell/02-CONTEXT.md
