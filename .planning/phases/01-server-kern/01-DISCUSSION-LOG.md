# Phase 1: Server-Kern - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-08-14
**Phase:** 1-Server-Kern
**Areas discussed:** App-ID/Naming, Tool-Zuschnitt, Auth-Modell, Antwort-/Fehlerformat, Client-Schicht, SDK/Transport, Test-Umgebung, Contribution-Fix
**Mode:** --auto (empfohlene Optionen automatisch gewaehlt; Owner hatte im Grilling-Interview pauschal "alles wie empfohlen" freigegeben)

---

## App-ID und Naming

| Option | Description | Selected |
|--------|-------------|----------|
| mcp_connector | Beschreibend, suchbar, MCP-only-Positionierung sichtbar | ✓ |
| Eigener Markenname | Braucht Namensfindung + Markenpruefung, kostet Deadline-Zeit | |
| nc_assistant_bridge | Erklaerungsbeduerftig, verwechselbar mit Assistant/context_agent | |

**Auto-Auswahl:** mcp_connector (Arbeitstitel-Beschluss aus dem Grilling: Branding nach MVP)
**Notes:** Umbenennung nur bis zum CSR-PR billig; "nextcloud" darf nicht in die App-ID (Store-Regel).

## Tool-Zuschnitt

| Option | Description | Selected |
|--------|-------------|----------|
| 15 Tools, app_verb-Schema, Deck als deck_browse konsolidiert | Kuratiert, unter allen Client-Limits, search/fetch inklusive | ✓ |
| 19+ Tools mit getrennten Deck/Kalender-Lesetools | Mehr Granularitaet, mehr Schema-Tokens | |
| Nur Lesetools (kein Create) | Sicherster Schnitt, aber Assistenten wirken kastriert | |

**Auto-Auswahl:** 15 Tools inkl. search/fetch im OpenAI-Pflichtschema, Create-only-Writes

## Auth-Modell Phase 1

| Option | Description | Selected |
|--------|-------------|----------|
| Env (stdio) + Header-Passthrough (HTTP), kein Token-Store | Einfach, sicher, OAuth-kompatibel erweiterbar in Phase 3 | ✓ |
| Eigener Token-Store schon in Phase 1 | Vorgezogene Komplexitaet ohne Nutzen vor OAuth | |
| Nur Env-Single-User auch fuer HTTP | Blockiert Multi-User-Demos | |

**Auto-Auswahl:** Env + Passthrough

## Antwort-/Fehlerformat

| Option | Description | Selected |
|--------|-------------|----------|
| Kompaktes JSON, Schema-Diaet, message+hint-Fehler | InfraNode-erprobt, Token-Budget-CI | ✓ |
| Volle outputSchemas ueberall | 56% Token-Footprint-Anteil, gemessen kontraproduktiv | |
| Markdown-Text-Antworten | Schlecht fuer programmatische Clients | |

**Auto-Auswahl:** Kompaktes JSON mit Schema-Diaet

## Nextcloud-Client-Schicht

| Option | Description | Selected |
|--------|-------------|----------|
| httpx roh + lxml/icalendar/vobject | Async, volle Kontrolle, vom Platzhirsch praktisch validiert | ✓ |
| caldav-Library | Sync (blockiert Event-Loop), Umweg | |
| aiodav | Verwaist | |

**Auto-Auswahl:** httpx roh

## SDK und Transport

| Option | Description | Selected |
|--------|-------------|----------|
| mcp>=2.0,<3 mit Fallback-Pin >=1.29,<2 | GA seit 28.07., bedient alte und neue Clients | ✓ |
| Pin auf 1.27/1.29 | Maintenance-only, verpasst Stateless-Clients | |
| FastMCP standalone 4.x | Beta, Drittanbieter, schlechtere Upstream-Story | |

**Auto-Auswahl:** mcp 2.x (revidierte PROJECT.md-Entscheidung vom 14.08.)

## Test-Umgebung

| Option | Description | Selected |
|--------|-------------|----------|
| Offizielles nextcloud:apache-Image + occ-App-Install in compose | CI-freundlich, reproduzierbar, zweiter Testnutzer fuer Permission-Tests | ✓ |
| juliusknorr/nextcloud-docker-dev | Maechtiger (Versions-Matrix), aber schwerer in CI | |

**Auto-Auswahl:** Offizielles Image; docker-dev optional spaeter fuer Versions-Matrix

## Contribution-Fix (#227)

| Option | Description | Selected |
|--------|-------------|----------|
| Minimaler Fix (stateless_http konfigurierbar/False) + Repro | Kleinster PR, hoechste Merge-Chance, Tueroeffner-Zweck | ✓ |
| Groesserer Refactor des MCP-Teils von context_agent | Scope-Creep in fremdem Repo, Merge-Risiko | |

**Auto-Auswahl:** Minimaler Fix

## Claude's Discretion

Modulstruktur, Naming-Details, Logging, CI-Workflow-Details, Test-Layout.

## Deferred Ideas

prepare_context (Phase 4), Login Flow v2 (Phase 3), Tasks/Prompts/Format-Parameter (v1.x), Talk/Tables/Mail + openDesk (v2/Phase 3), Behoerden-Hosting mit AVV (OPS-02).
