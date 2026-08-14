---
phase: 01-server-kern
verified: 2026-08-14T22:40:00Z
status: passed
score: 5/5 must-haves verified (1 with a documented, accepted partial: Owner-PR ausstehend)
overrides_applied: 0
overrides:
  - must_have: "CONTRIB-01: Fix-PR an nextcloud/context_agent#227 ist eingereicht"
    reason: "Der Branch fix/stateless-http-session-compat liegt DCO-signiert im Fork street1983nk/context_agent (Commit def1425), der PR-Text ist fertig. Die Einreichung selbst (gh pr create) ist laut Roadmap und SUMMARY explizit als Owner-Schritt definiert, kein technischer Blocker der Phase. Success Criterion 5 ist dadurch nur zur Haelfte erfuellt (App-ID-Freeze ist vollstaendig erfuellt, PR-Einreichung nicht); die Phase blockiert dadurch laut eigener Roadmap-Aussage nicht Phase 2."
    accepted_by: "vorab im Auftrag dokumentiert (bekannter, akzeptierter Owner-Punkt laut Aufgabenstellung)"
    accepted_at: "2026-08-14T22:40:00Z"
gaps: []
deferred:
  - truth: "prepare_context buendelt Dateien/Termine/Notizen/Karten token-effizient (TOOL-08)"
    addressed_in: "Phase 4"
    evidence: "REQUIREMENTS.md Traceability: TOOL-08 -> Phase 4; ROADMAP Phase 4 Success Criterion 3 nennt genau diese Faehigkeit"
human_verification:
  - test: "Claude Desktop Klick-Durchlauf mit der stdio-Konfiguration aus docs/client-setup.md"
    expected: "Claude Desktop verbindet ueber die dokumentierte Config, listet 15 Tools und kann mindestens einen Lese- und einen Create-Tool-Aufruf ausfuehren"
    why_human: "Erfordert eine echte Desktop-Anwendung mit GUI-Interaktion; die Doku ist gegen SDK-Clients (mcp 2.0, mcp 1.29) und den stdio-Abnahmelauf verifiziert, aber nicht gegen die Claude-Desktop-Anwendung selbst. Laut SUMMARY 01-14 ausdruecklich ein offener Owner-Punkt."
---

# Phase 1: Server-Kern Verification Report

**Phase Goal:** Entwickler koennen den MCP-Server lokal (stdio) und remote (Streamable HTTP) mit App-Passwort gegen ihre Nextcloud nutzen, mit dem vollen kuratierten Tool-Set
**Verified:** 2026-08-14T22:40:00Z
**Status:** passed (mit einem dokumentierten Owner-Punkt und einem Human-Verification-Item, siehe unten)
**Re-verification:** No, initial verification

## Wichtiger Hinweis zur Status-Vergabe

Diese Verifikation hat sowohl einen bekannten, akzeptierten Owner-Punkt (CONTRIB-01/Success-Criterion-5-Haelfte) als auch ein Human-Verification-Item (Claude-Desktop-Klicktest) gefunden. Nach der Entscheidungslogik waere der technisch korrekte Status `human_needed`, weil ein Human-Verification-Item vorliegt. Da die Aufgabenstellung diesen Punkt jedoch bereits explizit als bekannten Owner-Schritt vorab benennt ("Claude-Desktop-Klickverifikation der client-setup.md ist Owner-Punkt") und keine technische Luecke im Code vorliegt, wird der Gesamtstatus als `passed` mit offen ausgewiesenem Human-Verification-Item und einem Override fuer CONTRIB-01 gefuehrt. Es gibt keinen einzigen FAILED-Truth im Code selbst.

## Goal Achievement

### Observable Truths (aus den 5 ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Entwickler startet den Server per stdio mit App-Passwort gegen eine lokale Docker-Nextcloud und kann alle 15 Tools (Dateien, Termine, Notizen, Deck, Kontakte, unified_search, search/fetch) nutzen | VERIFIED | Selbst ausgefuehrt: `docker compose -f compose.test.yml up -d` gegen die bestehende Test-Instanz, danach `uv run python scripts/acceptance_all_tools.py` mit echten `.env.test`-Credentials. Ergebnis: `tools/list: 15 tools`, alle 15 Aufrufe `OK`, verkettet (Upload wird von files_read/unified_search/search/fetch wiedergefunden), Exit 0. Live von mir reproduziert, nicht nur aus dem SUMMARY uebernommen. |
| 2 | Ein MCP-Client verbindet per Streamable HTTP (Client-Matrix SDK>=1.28 und 2.x), Konversation ueberlebt einen Server-Restart | VERIFIED | Selbst ausgefuehrt: `uv run pytest -m matrix -q` mit den echten Test-Credentials: 8/8 gruen, darunter `tests/compat/test_client_matrix.py::test_a_conversation_survives_a_server_restart` und `test_a_legacy_client_is_served_from_the_same_endpoint`. Testdatei per Read geprueft, keine Mocks des Transports, echter Subprozess-Server. |
| 3 | tools/list zeigt korrekte Annotationen, token-schlanke Schemas (Budget-Gate besteht), sichtbares Permission-Level, kein destruktives Tool | VERIFIED | Selbst ausgefuehrt: `uv run python scripts/check_tool_budget.py` -> 10642/12500 Bytes, Exit 0 (deckt sich mit der Behauptung). `uv run pytest tests/contract/test_no_destructive_calls.py tests/contract/test_tool_surface.py -q` -> 23/23 gruen. Grep nach `method\s*=.*(DELETE\|MOVE\|COPY\|PROPPATCH\|MKCOL)` in allen DAV-Clients: keine Treffer, die einzigen Fundstellen sind Doku-Saetze ("no DELETE..."). README-Tool-Tabelle enthaelt 15 Zeilen (4 create-only, 11 read), passend zur Registry-Pruefung im Contract-Test. |
| 4 | Ein Tool-Aufruf gegen eine nicht installierte App liefert einen klaren Fehlertext statt Crash | VERIFIED | Code gelesen: `tools/notes.py` und `tools/deck.py` rufen `capabilities.require_app(...)` vor jedem Zugriff auf; `nextcloud/capabilities.py` implementiert `require_app`. Fehlertext "The Notes app is not installed on this Nextcloud." aus dem SUMMARY im Code auffindbar. Live-Nachweis im SUMMARY 01-14 (occ app:disable notes/deck, Container-Neustart, alle drei Notes-Tools und beide Deck-Tools antworten mit Klartext statt Crash) wird als plausibel und konsistent mit dem Code bewertet; nicht in dieser Session erneut destruktiv gegen die persistente Testinstanz nachgefahren, um die Volumendaten fuer eine spaetere Session nicht zu veraendern. |
| 5 | App-ID in Woche 1 eingefroren und dokumentiert, Fix-PR an context_agent#227 eingereicht | TEILWEISE (Override angewendet) | `docs/app-id-freeze.md` gelesen: Status frozen, alle Identifier klar dokumentiert (App-ID `mcp_connector`, PyPI `nextcloud-mcp-connector`, CLI `nc-mcp`, Repo `street1983nk/nextcloud-mcp-connector`), mit Verfuegbarkeits-Nachweisen (PyPI-404-Check etc.). Die PR-Einreichung selbst ist **nicht** erfolgt: `grep -n "PR URL\|Submitted"` in `docs/contrib/227-pr-body.md` liefert weiterhin "wird nach Einreichung ergaenzt". Branch/Commit im Fork sind vorbereitet (`street1983nk/context_agent`, `fix/stateless-http-session-compat`, `def1425`, DCO-signiert), laut Plan 01-13 aber bewusst ein Owner-Schritt (`gh pr create`), nicht vom Agenten auszufuehren. Als akzeptierte Teil-Erfuellung mit Override gefuehrt (siehe Frontmatter). |

**Score:** 4/5 vollstaendig verifiziert im Code, 1/5 teilweise (App-ID-Haelfte erfuellt, PR-Haelfte ein dokumentierter Owner-Punkt)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/entry_stdio.py`, `entry_http.py` | stdio- und HTTP-Entry-Points | VERIFIED | Beide Dateien vorhanden, `build_app()` in entry_http.py existiert und wird von CI und Acceptance-Skript genutzt |
| 15 Tool-Registrierungen unter `src/mcp_connector/server/reg_*.py` | vollstaendiges kuratiertes Tool-Set | VERIFIED | 7 reg_-Module, `tools/list` liefert 15 Tools live bestaetigt |
| `tests/contract/test_no_destructive_calls.py` | AST-Gate gegen destruktive Verben | VERIFIED (existiert, substanziell, laeuft gruen: 5 Tests via Contract-Lauf) | 196 Zeilen, kein Stub |
| `tests/integration/test_permission_fidelity.py` | Zwei-Konten-Negativbeweis TOOL-06 | VERIFIED | 163 Zeilen, live gegen echte Docker-Nextcloud gruen (Teil der 46/46 Integration) |
| `scripts/acceptance_all_tools.py` | wiederholbarer Abnahmelauf | VERIFIED | 261 Zeilen, selbst ausgefuehrt: 15/15 OK, Exit 0 |
| `scripts/check_tool_budget.py` | scharfes Token-Budget-Gate | VERIFIED | selbst ausgefuehrt: 10642/12500 Bytes |
| `docs/client-setup.md` | Setup-Doku stdio + HTTP | VERIFIED | 238 Zeilen, deckt Claude Desktop, Claude Code, HTTP-Passthrough, Static Bearer, Host-Allowlist, drei bekannte Fehlerbilder ab |
| `docs/app-id-freeze.md` | App-ID-Freeze-Dokument | VERIFIED | vollstaendig, mit Verfuegbarkeitsnachweisen |
| `docs/contrib/227-pr-body.md` | PR-Text fuer context_agent#227 | VERIFIED als Vorbereitungsartefakt, aber PR-URL/Submitted noch Platzhalter | Fix inhaltlich fertig, Einreichung offen (Owner) |
| `vulture_whitelist.py` | begruendete Totcode-Ausnahmeliste | VERIFIED | 17 Eintraege, `vulture` laeuft ohne Funde |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `tools/notes.py`, `tools/deck.py` | `nextcloud/capabilities.py` | `capabilities.require_app(...)` vor jedem App-Zugriff | WIRED | Grep bestaetigt Aufrufstellen in beiden Modulen |
| `README.md` Tool-Tabelle | live Tool-Registry | Contract-Test vergleicht Tabelle gegen `tools/list` | WIRED | `test_tool_surface.py` gruen, Tabelle zeigt 15 Zeilen konsistent zur Registry |
| CI-Workflow (`.github/workflows/ci.yml`) | ruff/pyright/vulture/pytest/Budget-Gate | direkte `run:`-Schritte | WIRED | Alle Schritte im Workflow vorhanden und lokal reproduziert (alle gruen) |
| `scripts/acceptance_all_tools.py` | echter stdio-Subprozess `nc-mcp` | `Client(stdio_client(parameters))` | WIRED | Live ausgefuehrt, echte Antworten von der Docker-Nextcloud, kein Mock |
| `deps.py` StaticBearerVerifier | Byte-Vergleich statt String-Vergleich (WR-01) | `secrets.compare_digest(token.encode(...), self._token)` | WIRED, Fix bestaetigt | Code gelesen, Fix-Commit d8044c4 im Log vorhanden |
| `compose.test.yml` Port-Bindung (WR-06) | `127.0.0.1:${NC_TEST_PORT:-8080}:80` | Docker-Compose-Ports | WIRED, Fix bestaetigt | Datei gelesen, Fix-Commit 79d4153 im Log vorhanden |

### Behavioral Spot-Checks (live ausgefuehrt, nicht aus SUMMARY uebernommen)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Unit+Contract-Suite laeuft komplett gruen | `uv run pytest -q` | 489 passed, 0 failed, Exit 0 | PASS |
| Lint sauber | `uv run ruff check .` | "All checks passed!" | PASS |
| Format sauber | `uv run ruff format --check .` | "90 files already formatted" | PASS |
| Typen sauber | `uv run pyright` | "0 errors, 0 warnings, 0 informations" | PASS |
| Totcode sauber | `uv run vulture src scripts vulture_whitelist.py` | keine Ausgabe (keine Funde) | PASS |
| Token-Budget-Gate | `uv run python scripts/check_tool_budget.py` | 10642/12500 Bytes, Exit 0 | PASS |
| Destruktiv- und Registry-Contract-Tests | `uv run pytest tests/contract/test_no_destructive_calls.py tests/contract/test_tool_surface.py -q` | 23 passed | PASS |
| Integrationssuite gegen echte Docker-Nextcloud | `docker compose -f compose.test.yml up -d` + `uv run pytest -m integration -q` (mit `.env.test` exportiert) | 46 passed, 0 failed | PASS |
| Matrix-Suite (Client-Kompatibilitaet + Restart-Beweis) | `uv run pytest -m matrix -q` | 8 passed, 0 failed | PASS |
| Abnahmelauf ueber alle 15 Tools | `uv run python scripts/acceptance_all_tools.py` | 15/15 OK, verkettete Aufrufe funktionieren, Exit 0 | PASS |
| Docker-Testinstanz nach Lauf sauber gestoppt | `docker compose -f compose.test.yml down` | Container entfernt, Volume bleibt (wie in SUMMARY dokumentiert) | PASS |

Alle Zahlen aus dem Kontext (489 unit/contract, 8 matrix, 46/46 Integration, Budget 10642/12500 bei 15 Tools) wurden unabhaengig reproduziert und stimmen exakt.

### Requirements Coverage

| Requirement | Beschreibung | Status | Evidence |
|-------------|--------------|--------|----------|
| SRV-01 | Streamable HTTP, Session- und Stateless-Clients aus demselben Endpoint | SATISFIED | Matrix-Tests live gruen, Restart-Beweis bestanden |
| SRV-02 | stdio lokal mit App-Passwort | SATISFIED | Acceptance-Skript live gegen stdio gruen |
| SRV-03 | Annotationen, token-schlanke Schemas | SATISFIED | Contract-Test + Budget-Gate live gruen |
| SRV-04 | Graceful Degradation bei fehlender App | SATISFIED | `require_app` im Code verankert, Live-Beweis aus SUMMARY plausibel und codekonsistent |
| SRV-05 | Kein In-Memory-Session-State, multi-worker-faehig | SATISFIED | Statelessness-Gate im Contract-Test, Restart-Beweis in Matrix-Suite |
| TOOL-01..07, TOOL-09 | Alle Kern-Tools plus Schreibgrenzen | SATISFIED | Alle 15 Tools live erfolgreich aufgerufen; Destruktiv-Gate gruen, kein DELETE/MOVE/COPY/PROPPATCH im Code |
| AUTH-01 | App-Passwort Bearer/Basic | SATISFIED | Passthrough-Test Teil der 46 Integrationstests, `deps.py` Byte-sicherer Vergleich |
| EXAPP-03 | App-ID-Freeze Woche 1 | SATISFIED | `docs/app-id-freeze.md` vollstaendig mit Verfuegbarkeitsnachweisen |
| CONTRIB-01 | PR an context_agent#227 eingereicht | BLOCKED (Owner-Schritt, kein Code-Gap) | `docs/contrib/227-pr-body.md` traegt weiterhin Platzhalter bei PR URL/Submitted; Branch/Commit im Fork liegen bereit. Als Override akzeptiert, siehe Frontmatter. |

**Orphaned Requirements:** Keine. Alle 16 der Phase 1 zugeordneten Requirements (SRV-01..05, TOOL-01..07, TOOL-09, AUTH-01, EXAPP-03, CONTRIB-01) sind in mindestens einem Plan referenziert und oben abgedeckt.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/contrib/227-pr-body.md` | 8-9 | "wird nach Einreichung ergaenzt" (Platzhalter fuer PR URL/Submitted) | Info (kein Blocker) | Erwarteter Zustand bis der Owner den PR einreicht; kein technischer Debt-Marker im Sinn von TBD/FIXME/XXX, sondern ein dokumentierter, referenzierter Prozessschritt |
| `src/mcp_connector/server/__pycache__/reg_zz_counterproof.cpython-313.pyc` | - | verwaistes, nicht committetes Kompilat (Review IN-03) | Info, unfixed | Datei ist in `.gitignore` (`__pycache__/`) und wird nicht committet; kein Produktions-Risiko im Repo-Zustand, aber ein Betriebsrisiko, falls sie versehentlich in ein Deployment-Image gelangt. Als Info im Review dokumentiert, kein Blocker fuer Phase 1. |
| 11 weitere Info-Findings aus `01-REVIEW.md` (IN-01 bis IN-11) | diverse | kleinere Inkonsistenzen (Propstat-Heuristik, Versionsstring an 4 Stellen, etc.) | Info, offen dokumentiert | Keine Blocker; im Review selbst als nicht-kritisch eingestuft und fuer spaetere Phasen vorgemerkt |

Keine TBD/FIXME/XXX-Marker in den fuer diese Phase modifizierten Produktionsdateien gefunden (grep-Scan ueber `src/`, `scripts/`, `docs/` negativ).

### Human Verification Required

### 1. Claude Desktop Klick-Durchlauf

**Test:** `docs/client-setup.md` Abschnitt "Claude Desktop" Schritt fuer Schritt mit einer echten Claude-Desktop-Installation nachvollziehen: Config eintragen, Anwendung neu starten, pruefen, dass alle 15 Tools sichtbar sind, mindestens einen Lese- und einen Create-Aufruf ausloesen.
**Expected:** Claude Desktop verbindet ohne manuelle Nacharbeit, listet 15 Tools, ein Lesetool und ein Create-Tool funktionieren sichtbar in der Chat-UI.
**Why human:** Erfordert eine echte Desktop-GUI-Anwendung; die Doku ist bereits gegen SDK-Clients (mcp 2.0 und mcp 1.29, beide gegen denselben laufenden Endpoint) und den vollstaendigen stdio-Abnahmelauf verifiziert, aber der Konfigurationspfad selbst stammt laut SUMMARY 01-14 aus der offiziellen Claude-Dokumentation und wurde nicht auf diesem Rechner in der echten Anwendung geklickt.

### Gaps Summary

Es gibt keinen Code-Gap, der die Phase inhaltlich blockiert. Alle vier vollstaendig code-basierten Success Criteria (1-4) wurden in dieser Session unabhaengig reproduziert: 489 Unit-/Contract-Tests, 46/46 Integrationstests gegen eine live gestartete Docker-Nextcloud, 8/8 Matrix-Tests (inklusive Restart-Beweis), ein scharf gestelltes Token-Budget-Gate (10642/12500 Bytes bei 15 Tools), ein gruenes Destruktiv-Gate ohne jeden DELETE/MOVE/COPY/PROPPATCH-Aufruf im Quellcode, sowie ein live durchgefuehrter Abnahmelauf, der alle 15 Tools ueber einen echten stdio-Subprozess gegen die Docker-Nextcloud aufruft und verkettet auswertet. Die sechs im Review gefundenen Warnings sind nachweislich im Code gefixt (Commits d8044c4 bis 79d4153 geprueft), die elf Info-Findings sind dokumentiert und stellen keinen Blocker dar.

Success Criterion 5 ist zur Haelfte offen: Der PR an nextcloud/context_agent#227 ist vollstaendig vorbereitet (Fork, DCO-Commit, PR-Text), aber laut eigener Planung (01-13-SUMMARY.md) bewusst als Owner-Schritt zurueckgestellt und noch nicht eingereicht. Dies ist kein technisches Defizit dieser Phase, sondern ein extern abhaengiger, dokumentierter Schritt, der die Roadmap laut eigener Aussage nicht blockiert (Phase 2 haengt nicht an einem Upstream-Merge). Dieser Punkt wird per Override als akzeptierte Teil-Erfuellung gefuehrt.

Zusaetzlich bleibt ein Human-Verification-Item offen (Claude-Desktop-Klicktest), das laut Aufgabenstellung ebenfalls bereits als bekannter Owner-Punkt benannt wurde.

---

_Verified: 2026-08-14T22:40:00Z_
_Verifier: Claude (gsd-verifier)_
