---
phase: 01-server-kern
plan: 14
subsystem: testing
tags: [mcp, contract-test, vulture, token-budget, docker, nextcloud, stdio, streamable-http]

requires:
  - phase: 01-server-kern
    provides: alle 15 Tools, stdio- und HTTP-Transport, Graceful Degradation, App-ID-Freeze
provides:
  - Automatisierter Beweis der Schreibgrenzen (AST-Gate gegen destruktive Aufrufe, mit Kommentarfilterung)
  - Contract-Test ueber die vollstaendige Registry (Annotationen, Beschreibungen, Output-Schemas, Confused Deputy)
  - Negativbeweis der Berechtigungstreue mit zwei echten Konten (alice und bob)
  - Scharf gestelltes Token-Budget-Gate (gemessen 10643 Bytes plus 15 Prozent gleich 12500)
  - Vulture bei voller Konfidenz mit begruendeter Whitelist statt --min-confidence 80
  - docs/client-setup.md fuer stdio und Streamable HTTP, gegen die Referenz-Clients verprobt
  - scripts/acceptance_all_tools.py, ein wiederholbarer Abnahmelauf ueber alle 15 Tools
affects: [02-exapp-shell, 03-oauth, 05-haertung-store]

tech-stack:
  added: []
  patterns:
    - "Grep-Gate mit AST-Filterung: Kommentare und Docstrings raus, String-Literale drin"
    - "Gates werden auf den gemessenen Wert scharf gestellt, nicht dekorativ hoch gehaengt"
    - "Registry ist die einzige Wahrheit: die README-Tabelle wird gegen tools/list geprueft"

key-files:
  created:
    - tests/contract/test_no_destructive_calls.py
    - tests/integration/test_permission_fidelity.py
    - scripts/acceptance_all_tools.py
    - docs/client-setup.md
    - vulture_whitelist.py
  modified:
    - tests/contract/test_tool_surface.py
    - scripts/check_tool_budget.py
    - .github/workflows/ci.yml
    - README.md
    - pyproject.toml
    - src/mcp_connector/nextcloud/clients/deck.py
    - src/mcp_connector/nextcloud/clients/notes.py
    - src/mcp_connector/tools/notes.py

key-decisions:
  - "BUDGET_BYTES 24000 auf 12500 gesenkt (gemessen 10643 plus 15 Prozent); ein Budget ueber dem Doppelten der Messung kann nicht ausloesen und schuetzt nichts"
  - "Das Destruktiv-Gate filtert Kommentare und Docstrings per AST, behaelt aber String-Literale; sonst waere die ehrliche Doku in dav.py der Grund, warum der Test rot wird"
  - "Vulture laeuft bei voller Konfidenz mit annotierter Whitelist statt --min-confidence 80; bei 80 meldete der Schritt gar nichts und konnte nie fehlschlagen"
  - "Modul-globaler veraenderlicher Zustand ist im Produktionscode verboten; genau zwei Ausnahmen sind namentlich gelistet (Client-Pool pro Event-Loop, Capabilities-Cache mit TTL)"
  - "Die README-Tool-Tabelle wird nicht mehr von Hand gepflegt, sondern im Contract-Test gegen die laufende Registry geprueft"
  - "notes.list_notes und die ungenutzte Deck-Konstante entfernt; SUPPORTED_API_VERSION baut jetzt DECK_API_PREFIX statt tot herumzuliegen"
  - "Der Abnahmelauf ist ein committetes Skript, kein einmaliges Kommando; die Aufrufe bauen aufeinander auf, damit eine leere Antwort auf ein gerade angelegtes Objekt als Fehler zaehlt"

patterns-established:
  - "Gegenprobe zu jedem Gate: ein temporaer registriertes 16. Tool mit DELETE und user-Parameter muss die Gates rot faerben"
  - "Negativbeweise brauchen eine Positivkontrolle im selben Lauf (alice findet, bob findet nicht)"

requirements-completed: [TOOL-06, TOOL-09, SRV-01, SRV-03, SRV-04, SRV-05]

duration: 71 min
completed: 2026-08-14
---

# Phase 1 Plan 14: Phasenabschluss Summary

**Das Sicherheitsversprechen ist jetzt ein Gate statt einer Behauptung: AST-Grep gegen destruktive Aufrufe, Confused-Deputy-Pruefung ueber alle 15 Input-Schemas, Zwei-Konten-Negativbeweis, ein auf 12500 Bytes scharf gestelltes Token-Budget und ein Abnahmelauf, der alle 15 Tools ueber echtes stdio gegen die Docker-Nextcloud aufruft.**

## Performance

- **Duration:** 71 min
- **Started:** 2026-08-14T21:15:00Z
- **Completed:** 2026-08-14T22:26:00Z
- **Tasks:** 3 (2 Auto, 1 Checkpoint auto-approved)
- **Files modified:** 13 (5 neu, 8 geaendert)

## Accomplishments

- **TOOL-09 belegt statt behauptet.** `tests/contract/test_no_destructive_calls.py` liest jede Produktionsdatei per AST, entfernt Kommentare und Docstrings, behaelt String-Literale und meldet Datei und Zeile. Gegenprobe live gefahren: ein temporaeres `files_delete` mit `method = "DELETE"` und einem `user`-Parameter faerbt fuenf Gates gleichzeitig rot.
- **TOOL-06 mit zwei echten Konten belegt.** bob findet alices frisch hochgeladene Datei weder ueber `files_search` noch ueber `unified_search` noch ueber das ChatGPT-`search`, und er kann sie auch bei bekanntem Pfad nicht lesen. Die Positivkontrolle (alice findet sie sofort) laeuft im selben Test, sonst waere jedes leere Ergebnis wertlos.
- **SRV-03 abgenommen.** Ein Durchgang ueber die komplette Registry prueft Annotationen (4 Create-Tools, 11 Lesetools, alle `open_world_hint=False`), nicht leere Beschreibungen, Output-Schema genau bei `search` und `fetch`, und rekursiv (inklusive `$defs`) dass kein Input-Schema `user`, `username`, `uid`, `userid` oder `owner` kennt.
- **Beide Gates scharf gestellt.** Token-Budget von 24000 auf 12500 Bytes (gemessen 10643 am 2026-08-14, plus 15 Prozent, aufgerundet). Vulture laeuft bei voller Konfidenz mit begruendeter Whitelist; zwei echte Funde wurden entfernt.
- **Alle 15 Tools live ueber einen echten stdio-Client aufgerufen**, gegen Nextcloud 34 im Docker-Container, mit verketteten Aufrufen und Exit-Code 0.
- **Offener Punkt aus 01-11 geschlossen:** Calendar-App per `occ app:install calendar` (6.5.3) nachinstalliert, der Weblink aus `fetch` (`/index.php/apps/calendar/dayGridMonth/2026-08-15`) antwortet live mit 200 und `text/html`.

## Task Commits

1. **Task 1: Contract-Test und Beweis der Schreibgrenzen** - `0459eee` (test)
2. **Task 2a: Budget und Totcode-Gate scharf stellen** - `97b85eb` (chore)
3. **Task 2b: Client-Setup-Doku und Known limitations** - `00fe486` (docs)
4. **Task 3: Abnahmelauf ueber alle 15 Tools** - `05522af` (test)

## Files Created/Modified

- `tests/contract/test_no_destructive_calls.py` - AST-Gate: keine destruktiven Verben, kein Share-Endpoint, kein modul-globaler Zustand ausser den zwei dokumentierten Caches, keine Elicitation
- `tests/contract/test_tool_surface.py` - Erweitert um den Gesamtdurchgang: Annotationen, Beschreibungen, Output-Schemas, Confused Deputy, README-Tabelle gegen die Registry
- `tests/integration/test_permission_fidelity.py` - Zwei-Konten-Negativbeweis (TOOL-06) mit Positivkontrolle und Guard gegen zwei identische Fixtures
- `scripts/acceptance_all_tools.py` - Abnahmelauf: startet `nc-mcp` als Subprozess, ruft alle 15 Tools verkettet auf, druckt eine Matrix
- `scripts/check_tool_budget.py` - BUDGET_BYTES 12500 mit Messwert und Datum als Kommentar
- `vulture_whitelist.py` - 17 begruendete Eintraege, gruppiert nach Grund (Decorator-Registrierung, Framework-Einstieg, Nutzung ausserhalb des Produktions-Call-Graphs)
- `.github/workflows/ci.yml` - Vulture bei voller Konfidenz mit Whitelist, Kommentare warum jedes Gate so eingestellt ist
- `README.md` - Abschnitt "Known limitations" mit Ausweg je Eintrag, Verweis auf docs/client-setup.md, Status ehrlich formuliert
- `docs/client-setup.md` - stdio (Claude Desktop, Claude Code), Streamable HTTP mit Basic-Passthrough und Static Bearer, Host-Allowlist, drei Stolperstellen
- `pyproject.toml` - ruff-Ausnahmen fuer die Whitelist-Datei
- `src/mcp_connector/nextcloud/clients/deck.py` - `SUPPORTED_API_VERSION` baut jetzt `DECK_API_PREFIX`
- `src/mcp_connector/nextcloud/clients/notes.py` - tote `list_notes` entfernt
- `src/mcp_connector/tools/notes.py` - Docstring auf den entfernten Helfer angepasst

## Abnahme-Matrix: die fuenf Success Criteria der Phase

| # | Kriterium | Status | Beweis |
|---|-----------|--------|--------|
| 1 | Alle Tools per stdio gegen eine lokale Docker-Nextcloud nutzbar | **erfuellt** | `uv run python scripts/acceptance_all_tools.py`: 15/15 OK ueber echten stdio-Client gegen Nextcloud 34, verkettet (Upload wird von `files_read`, `unified_search`, `search` und `fetch` wiedergefunden). Exit 0. |
| 2 | Streamable HTTP mit Client-Matrix und Restart-Ueberleben | **erfuellt** | `uv run pytest -m matrix`: 8/8, inkl. `test_a_conversation_survives_a_server_restart`. Zusaetzlich live gegen die Docker-Nextcloud: uvicorn im Passthrough-Modus (ohne NC-Konto im Environment), `files_list` per HTTP OK, Prozess hart beendet und neu gestartet, `files_list` erneut OK. Beide Referenz-Clients gegen denselben Endpoint: mcp 2.0 meldet 15 Tools, mcp 1.29 meldet 15 Tools. |
| 3 | Korrekte Annotationen, token-schlanke Schemas, sichtbares Permission-Level, keine destruktiven Tools | **erfuellt** | `uv run pytest tests/contract`: 23/23. Budget-Gate: 10643 von 12500 Bytes, Exit 0. Destruktiv-Gate gruen, Gegenprobe rot. README-Tabelle automatisiert gegen die Registry geprueft. |
| 4 | Klarer Fehlertext statt Crash bei fehlender App | **erfuellt** | `occ app:disable notes` plus Container-Neustart: `tools/list` bleibt bei 15 Tools, alle drei Notes-Tools antworten "The Notes app is not installed on this Nextcloud." plus Hinweis, `files_list` bleibt unbeeintraechtigt. Gleicher Lauf fuer Deck: beide Deck-Tools mit eigenem Text plus Hinweis, `unified_search` antwortet weiter. Apps danach wieder aktiviert, Integrationssuite erneut gruen. |
| 5 | App-ID eingefroren, context_agent-PR eingereicht | **teilweise** | `docs/app-id-freeze.md` ist vollstaendig (Status frozen, alle Bezeichner, Datum 2026-08-14). Der PR ist **nicht** eingereicht: `docs/contrib/227-pr-body.md` traegt bei "PR URL" und "Submitted" weiterhin "wird nach Einreichung ergaenzt". Der Branch liegt im Fork (`street1983nk:fix/stateless-http-session-compat`, `def1425`, DCO). Einreichen ist ein Owner-Schritt. |

## Testlaeufe des Abnahmelaufs

| Suite | Kommando | Ergebnis |
|-------|----------|----------|
| Unit und Contract | `uv run pytest -q` | 476 passed, 54 deselected |
| Integration | `uv run pytest -m integration -q` | 46 passed (gegen `compose.test.yml`, Nextcloud 34) |
| Matrix | `uv run pytest -m matrix -q` | 8 passed |
| Budget-Gate | `uv run python scripts/check_tool_budget.py` | 10643 / 12500 Bytes, Exit 0 |
| Lint und Format | `uv run ruff check . && uv run ruff format --check .` | sauber, 90 Dateien |
| Typen | `uv run pyright` | 0 errors, 0 warnings |
| Totcode | `uv run vulture src scripts vulture_whitelist.py` | keine Funde |
| Abnahme aller Tools | `uv run python scripts/acceptance_all_tools.py` | 15/15 OK, Exit 0 |

## Requirements-Stand nach diesem Plan

| Requirement | Vorher | Nachher | Beweis |
|-------------|--------|---------|--------|
| TOOL-06 | Pending | **Complete** | `tests/integration/test_permission_fidelity.py`, 6 Tests live gegen zwei Konten |
| TOOL-09 | Pending | **Complete** | `tests/contract/test_no_destructive_calls.py` plus Registry-Beweis im Contract-Test, Gegenprobe gefahren |
| SRV-03 | Pending | **Complete** | Gesamtdurchgang ueber alle 15 Tools plus scharfes Budget-Gate |
| SRV-01 | Complete | Complete | Client-Matrix live gegen die laufende Nextcloud bestaetigt |
| SRV-04 | Complete | Complete | Notes- und Deck-Abschaltung live nachgefahren |
| SRV-05 | Complete | Complete | Restart-Beweis live plus Statelessness-Gate im Contract-Test |
| CONTRIB-01 | Pending | **Pending** | Owner-Schritt, siehe Kriterium 5 |

## Decisions Made

- **Budget auf den gemessenen Wert.** 24000 Bytes waren mehr als das Doppelte der Messung, das Gate konnte nie ausloesen. 12500 laesst Raum fuer Formulierungen, aber nicht fuer ein 16. Tool, und genau das soll es auch nicht.
- **Kommentarfilterung per AST, nicht per Regex.** Der ehrliche Satz in `clients/dav.py` ("no DELETE, no MOVE, no COPY and no PROPPATCH") wuerde ein naives Grep rot faerben, und die uebliche Reparatur waere, den Satz zu loeschen. Das Gate darf keine Doku kosten. String-Literale bleiben in Reichweite, denn `method="DELETE"` ist genau das Gesuchte.
- **Vulture ohne Konfidenzschwelle.** `--min-confidence 80` meldete auf diesem Repo nichts, der CI-Schritt war Dekoration. Volle Konfidenz plus eine Whitelist, in der jeder Eintrag eine Begruendungszeile hat, ist ein Gate mit Aussage.
- **Modul-globaler Zustand ist verboten, mit zwei namentlichen Ausnahmen.** Ein Dictionary, das eine Anfrage ueberlebt, ist einen Refactor von einem Session-Store entfernt, und ein Session-Store bricht den Restart-Beweis. Der Client-Pool pro Event-Loop und der Capabilities-Cache mit TTL duerfen jederzeit leer sein und tragen kein Geheimnis, deshalb stehen sie auf der Liste.
- **Die README-Tabelle wird geprueft, nicht gepflegt.** Ein Contract-Test liest die Tabelle und vergleicht Namen und Permission-Level mit `tools/list`. Eine Tabelle, die von Hand gepflegt wird, ist die erste Stelle, die bei einem neuen Tool veraltet.
- **Der Abnahmelauf ist ein Skript im Repo.** Ein einmaliges Kommando beweist einen Zeitpunkt, ein Skript beweist ihn wieder. Die Aufrufe bauen aufeinander auf, weil "null Treffer" fuer eine vor einer Sekunde angelegte Datei ein Fehler und kein leeres Ergebnis ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Negativbeweis der Berechtigungstreue nachgeruestet (TOOL-06)**
- **Found during:** Task 1
- **Issue:** Der Plan listet den Contract- und den Destruktiv-Test, aber keinen Nachweis, dass ein zweites Konto die Daten des ersten nicht sieht. TOOL-06 stand seit Plan 01-10 offen und war ohne diesen Test nicht abnehmbar. Ein Berechtigungsversprechen ohne Negativtest ist genau die Klasse Behauptung, die dieser Plan beseitigen soll.
- **Fix:** `tests/integration/test_permission_fidelity.py` mit sechs Tests: Guard gegen zwei identische Konten, Positivkontrolle fuer alice, drei Suchwege fuer bob, plus der Lesezugriff bei bekanntem Pfad.
- **Files modified:** tests/integration/test_permission_fidelity.py
- **Verification:** 6 passed gegen die laufende Docker-Nextcloud
- **Committed in:** `0459eee`

**2. [Rule 1 - Bug] `__all__` als modul-globaler Zustand gemeldet**
- **Found during:** Task 1
- **Issue:** Das Statelessness-Gate meldete sieben Treffer, alle `__all__`. Eine Exportliste ist keine Laufzeit-Zustandshaltung, das Gate haette so nie gruen werden koennen.
- **Fix:** Dunder-Namen von der Pruefung ausgenommen, mit Begruendung im Code.
- **Files modified:** tests/contract/test_no_destructive_calls.py
- **Verification:** 5 passed
- **Committed in:** `0459eee`

**3. [Rule 1 - Bug] Falsche 421-Verifikation in der neuen Doku**
- **Found during:** Task 3
- **Issue:** `docs/client-setup.md` empfahl, die Host-Allowlist mit `curl -H 'Host: ...' .../health` zu pruefen. Live-Gegenprobe: `/health` ist eine Custom-Route ohne Host-Pruefung und antwortet auch mit fremdem Host mit 200. Die Anleitung haette Betreiber in die falsche Richtung geschickt, genau bei dem Fehler, den sie erklaeren soll.
- **Fix:** Verifikation auf `POST /mcp` umgestellt und live geprueft (fremder Host 421, erlaubter Host mit Port 200). Zusaetzlich steht jetzt im HTTP-Abschnitt, dass `/health` bewusst nicht hinter der Host-Pruefung liegt.
- **Files modified:** docs/client-setup.md
- **Verification:** `curl -X POST -H 'Host: evil.example.com' .../mcp` liefert 421, mit erlaubtem Host 200
- **Committed in:** `05522af`

**4. [Rule 3 - Blocking] Vulture-Whitelist braucht ruff-Ausnahmen**
- **Found during:** Task 2
- **Issue:** Das dokumentierte Vulture-Whitelist-Format besteht aus nackten, undefinierten Namen. ruff meldet dafuer F821 und B018, das Format ist ohne Ausnahme nicht committebar.
- **Fix:** `per-file-ignores` fuer `vulture_whitelist.py` in pyproject.toml, mit Begruendung. pyright sieht die Datei ohnehin nicht (`include` listet nur src, scripts, tests).
- **Files modified:** pyproject.toml, vulture_whitelist.py
- **Verification:** `ruff check .` sauber, `pyright` 0 errors, `vulture` ohne Funde
- **Committed in:** `97b85eb`

**5. [Rule 1 - Bug] Zwei echte Totcode-Funde entfernt**
- **Found during:** Task 2
- **Issue:** `notes.list_notes` (20 Zeilen, kein Aufrufer, kein Test) und `deck.SUPPORTED_API_VERSION` (deklariert, nirgends gelesen), waehrend `DECK_API_PREFIX` die Version noch einmal als Literal enthielt.
- **Fix:** `list_notes` entfernt und der Verweis im Docstring von `tools/notes.py` auf den tatsaechlichen Stand gebracht. `DECK_API_PREFIX` wird aus `SUPPORTED_API_VERSION` gebaut, damit die Version nur an einer Stelle steht.
- **Files modified:** src/mcp_connector/nextcloud/clients/notes.py, src/mcp_connector/nextcloud/clients/deck.py, src/mcp_connector/tools/notes.py
- **Verification:** volle Suite gruen, Integrationssuite gruen, vulture ohne Funde
- **Committed in:** `97b85eb`

### Bewusste Ergaenzungen ueber den Planwortlaut hinaus

- **`scripts/acceptance_all_tools.py`** war im Plan als manueller Client-Durchgang beschrieben (Kriterium 1 des Checkpoints). Als Skript ist der Beweis wiederholbar und faellt bei einer Regression im CI-Stil auf, statt nur einen Zeitpunkt zu belegen.
- **Deck-Degradation zusaetzlich zu Notes.** Der Plan verlangt fuer Kriterium 4 nur Notes. SRV-04 ist ein Gesamtnachweis ueber die Vertikalen, also wurde der Deck-Zweig im selben Zyklus mitgefahren.
- **Calendar-App installiert**, um den in 01-11 offen gebliebenen Weblink aus `fetch` live zu verifizieren. Die Test-Nextcloud ist eine Wegwerf-Instanz, der Eingriff kostet nichts und schliesst einen offenen Nachweis.

---

**Total deviations:** 5 auto-fixed (2 Bugs, 1 fehlende kritische Funktionalitaet, 1 Blocker, 1 Totcode-Bug) plus 3 bewusste Ergaenzungen
**Impact on plan:** Keine Scope-Ausweitung. Vier der fuenf Auto-Fixes betreffen Gates, die sonst falsch gruen oder gar nicht committebar gewesen waeren; der fuenfte korrigiert eine Anleitung, die Betreiber in die Irre gefuehrt haette.

## Issues Encountered

- **`/health` liegt nicht hinter der Host-Pruefung.** Erst durch die Live-Gegenprobe aufgefallen, siehe Abweichung 3. Kein Codefehler: Custom-Routen sind bewusst unauthentifiziert und ungeprueft, das ist fuer eine Liveness-Probe richtig. Die Doku sagt es jetzt.
- **Eine per `occ` deaktivierte App bleibt in `/cloud/capabilities` sichtbar, bis die Nextcloud neu startet.** Bereits aus Plan 01-06 bekannt und bestaetigt: die Degradations-Nachweise brauchen `docker compose restart nextcloud`, nicht nur das Leeren unseres eigenen Caches.
- **`Client(transport)` in mcp 2.x nimmt den Transport ununbetreten.** Der erste Entwurf des Abnahme-Skripts betrat `stdio_client(...)` selbst und uebergab das Tupel, was mit einem TypeError endet. Korrekt ist `Client(stdio_client(parameters))`.

## Known Stubs

Keine. Kein Tool liefert Platzhalterdaten, und der Abnahmelauf faengt genau diesen Fall ab: eine leere Antwort auf ein gerade angelegtes Objekt zaehlt als Fehler.

## User Setup Required

Keine Konfiguration externer Dienste. Ein Owner-Schritt bleibt offen, siehe unten.

## Offene Owner-Punkte

1. **CONTRIB-01, PR an nextcloud/context_agent#227 einreichen.** Branch und DCO-Commit liegen im Fork (`street1983nk:fix/stateless-http-session-compat`, `def1425`), der PR-Text in `docs/contrib/227-pr-body.md`. Vorher `git push origin main`, damit der verlinkte Regressionstest oeffentlich sichtbar ist. Danach PR-URL in `docs/contrib/227-pr-body.md` nachtragen, ROADMAP 01-13 abhaken, CONTRIB-01 auf Complete. Solange der PR fehlt, ist Success Criterion 5 nur zur Haelfte erfuellt.
2. **Ein Durchgang mit Claude Desktop selbst.** `docs/client-setup.md` ist gegen die Referenz-Clients der Testsuite verprobt (mcp 2.0 und mcp 1.29 gegen denselben laufenden Endpoint, stdio-Abnahmelauf ueber alle 15 Tools). Ein Klick-Durchgang durch die Claude-Desktop-Konfiguration ist ein Owner-Schritt und steht aus. Die Konfigurationspfade in der Doku sind aus der offiziellen Dokumentation uebernommen, nicht auf diesem Rechner verifiziert.
3. **Docker-Testinstanz aufraeumen.** `docker compose -f compose.test.yml down` wurde nach dem Abnahmelauf ausgefuehrt, das Volume bleibt bestehen. Die Instanz traegt jetzt zusaetzlich die Calendar-App 6.5.3 und die Abnahme-Artefakte (Testdateien, eine Notiz, eine Deck-Karte, einen Termin). Fuer einen sauberen Neustart: `docker compose -f compose.test.yml down -v` und danach `bash scripts/bootstrap_test_nc.sh`.

## Next Phase Readiness

- Phase 1 ist inhaltlich abgeschlossen: alle 15 Tools laufen live, beide Transporte sind belegt, alle Gates sind scharf, die Dokumentation deckt die verprobten Wege ab.
- Der einzige verbleibende Punkt der Phase ist der Owner-PR (CONTRIB-01). Er blockiert Phase 2 nicht, denn die ExApp-Shell haengt nicht an einem Upstream-Merge.
- Fuer Phase 2 relevant: die Client-Factory nimmt ihre Credentials bereits als Parameter-Objekt entgegen, der AppAPI-Impersonation-Weg kann als dritte Credential-Quelle daneben treten, ohne die Tools anzufassen. Die Gates aus diesem Plan (Destruktiv, Confused Deputy, Statelessness, Budget) gelten weiter und werden jeden Fehltritt in Phase 2 an der einfuehrenden Aenderung melden.

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*

## Self-Check: PASSED

- Alle als erstellt gemeldeten Dateien liegen auf der Platte (`test_no_destructive_calls.py`, `test_permission_fidelity.py`, `acceptance_all_tools.py`, `client-setup.md`, `vulture_whitelist.py`).
- Alle vier Task-Commits sind in `git log` auffindbar: `0459eee`, `97b85eb`, `00fe486`, `05522af`.
- Alle `<acceptance_criteria>` beider Auto-Tasks wurden nach Abschluss erneut ausgefuehrt und sind gruen (siehe Tabelle "Testlaeufe des Abnahmelaufs").
- Die Docker-Testinstanz wurde nach dem Abnahmelauf mit `docker compose -f compose.test.yml down` gestoppt; das Volume `nextcloud-mcp-connector_nextcloud-test-data` bleibt erhalten.
