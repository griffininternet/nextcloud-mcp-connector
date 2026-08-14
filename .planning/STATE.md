---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 01-04-PLAN.md
last_updated: "2026-08-14T16:25:07.210Z"
last_activity: 2026-08-14
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 14
  completed_plans: 5
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-14)

**Core value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Current focus:** Phase 1: Server-Kern

## Current Position

Phase: 1 (Server-Kern): EXECUTING
Plan: 6 of 14
Status: Ready to execute
Last activity: 2026-08-14

Progress: [████░░░░░░] 36%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01-server-kern P01 | 24 min | 3 tasks | 10 files |
| Phase 01-server-kern P02 | 18 min | 3 tasks | 21 files |
| Phase 01-server-kern P12 | 14 min | 3 tasks | 2 files |
| Phase 01-server-kern P03 | 25 min | 3 tasks | 10 files |
| Phase 01-server-kern P04 | 20 min | 3 tasks | 12 files |

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

### Pending Todos

None yet.

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

Last session: 2026-08-14T16:24:51.120Z
Stopped at: Completed 01-04-PLAN.md
Resume file: None
