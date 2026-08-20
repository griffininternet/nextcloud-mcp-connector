# MCP Connector für Nextcloud (Arbeitstitel)

## What This Is

Ein schlankes MCP-only-ExApp für Nextcloud: Nutzer installieren es per Klick aus dem Nextcloud App Store und verbinden damit ihre Nextcloud (Dateien, Kalender, Notizen, Aufgaben, Kontakte) als Werkzeug mit KI-Assistenten wie Claude, MUCGPT, Cursor oder eigenen Agenten. Zielgruppe v1: Entwickler und Selfhoster; ab Phase 2 deutsche Behörden und Unternehmen mit Datenschutz-Anforderungen (souveräner Arbeitsplatz, openDesk).

## Core Value

Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.

## Current State

**v1.1 Phase 6 complete 2026-08-20** (verified 6/6): CIMD als DCR-Alternative live bewiesen (Claude Code), SSRF-Grenze belegt, Loopback-Portregel eingebaut, Cursor-Befund gemessen und per BL-14 entschieden, Ein-Klick-Story auf 34.0.3 wörtlich wahr, Conference-Material vorführbar. Offen: Phase 7 (MUCGPT/F13/BaerGPT, extern getaktet).

**v1.0 shipped 2026-08-20.** Release 0.1.2 ist live im Nextcloud App Store
(apps.nextcloud.com/apps/mcp_connector), 16 Tools, OAuth 2.1 E2E gegen Claude.ai und
ChatGPT bewiesen, Per-User-Verwaltung live, Purge/Deinstallation live bewiesen, alle 27
v1-Requirements erfüllt (Audit passed). Codebasis: Python 3.13, mcp 2.0, ~1800 Unit-/
Contract-Tests grün, ruff/pyright/vulture sauber. Offene Posten im BACKLOG (BL-01..05,
BL-12 MUCGPT-Verprobung wartet auf it@M-Antwort).

## Current Milestone: v1.1 Verwaltungs-Clients und Härtungs-Reste

**Goal:** Die v1.0-Versprechen gegen echte Verwaltungs-Clients beweisen und die letzten Auth-Reste schließen, rechtzeitig zur Nextcloud Conference September 2026.

**Target features:**
- MUCGPT live verproben, sobald it@M antwortet (Protokoll in docs/client-setup.md), danach F13 und BaerGPT (beide MCP-fähig laut Dossier)
- Cursor-Live-Nachweis nach der Teilregistrierung plus Klärung der Loopback-Portfrage (BL-04-Rest, F1 aus dem v1.0-Audit)
- BL-05 Client ID Metadata Documents (DCR-Nachfolger der MCP-Spec) mit eigenem SSRF-Review, einziges größeres Technikstück
- NC-34.0.3-UI-Smoke: Upstream-Fix prüfen (Install-/Remove-Knopf), bei Erfolg Ein-Klick-Story in Doku und Store-Text wörtlich einlösen
- Conference-Vorbereitung: Demo-Material, ggf. Lightning-Talk

**Bewusst klein (1-2 Phasen).** Vorgemerkt, nicht in diesem Milestone: v1.2 "Kuratierte Breite" (Talk/Tables/Mail, prepare_context-Ausbau, Q4 nach Store-Feedback) und v2.0 "openDesk/Behörden" (OpenProject/XWiki/Matrix/OX, Gruppen-Policies, Audit-Log, ZenDiS). Querschnitt: Prototype Fund Frist 1.10. bis 30.11.2026 liegt zwischen v1.1 und v1.2.

## Requirements

### Validated

- ✓ Als ExApp per Klick aus dem Nextcloud App Store installierbar (AppAPI/Deploy Daemon) — v1.0 (Store-Release 0.1.0..0.1.2; Ein-Klick-Lücke via Declarative Admin-Settings geschlossen)
- ✓ MCP-Spec-konformes OAuth 2.1 — v1.0 (Claude.ai und ChatGPT verbinden sich nur mit der Resource-URL; DCR, PKCE, Rotation mit Reuse-Detection)
- ✓ Per-User-Verwaltung in den Nextcloud-Settings — v1.0 (Verbindungsseite unter Settings/Security, Pause wirkt an allen 4 Autorisierungspunkten)
- ✓ Kuratierte Tool-Basis — v1.0 (16 Tools, Budget-Gate 12500 Bytes, Contract-Test gegen die aktive Registry)
- ✓ prepare_context — v1.0 (Suche + Terminwoche in einem Aufruf, Marker-Filter gegen Text-Fälschung)
- ✓ Risikoarme Writes, destruktive Ops konstruktionsbedingt ausgeschlossen — v1.0 (AST-Grep-Gate, Zwei-Konten-Negativbeweis)
- ✓ Transport stdio + Streamable HTTP, App-Passwort + Login Flow v2 — v1.0
- ✓ App-Store-Einreichung vor der Nextcloud Conference September 2026 — v1.0 (eingereicht 2026-08-19, fünf Wochen vor Termin)
- ✓ Contribution-Fix an nextcloud/context_agent#227 — v1.0 (Fork + DCO-signierter Fix, Disclosure in #203)
- ✓ Client ID Metadata Documents als DCR-Alternative, SSRF-geprüft — v1.1 Phase 6 (Claude Code verbindet sich live ohne Registrierung; DCR-Kontrollen greifen wortgleich, kein Fetch außerhalb von /authorize)
- ✓ Cursor-Verhalten gemessen statt vermutet, Loopback-Portfrage beantwortet — v1.1 Phase 6 (Teilregistrierung wirkt live mit 201; Cursor scheitert belegt an seiner eigenen cursor://-Adresse, Owner-Entscheid BL-14 "sichtbar machen plus Doku"; RFC-8252-7.3-Portregel eingebaut und mit wechselnden Ports live bestätigt)
- ✓ NC-34.0.3-UI-Smoke: Ein-Klick-Installation über die Store-UI nachgewiesen — v1.1 Phase 6 (Deploy-and-enable- und Remove-Knopf gemessen, Doku/Store-Text EN/DE/FR sagen das Gemessene)
- ✓ Conference-Demo-Material — v1.1 Phase 6 (Runbook einmal komplett durchgefahren, 82 s; Lightning-Talk-Entwurf, CfP-Schließung im Kopf vermerkt)

### Active

(Leer. MUCGPT/F13/BaerGPT-Verprobungen am 2026-08-20 per Owner-Entscheid deferred: extern getaktet, Trigger it@M-Antwort bzw. Owner-Kontakte; siehe Future Requirements in REQUIREMENTS.md und BL-12.)

### Out of Scope

- Talk-, Tables- und Mail-Tools - v2; v1 bleibt kuratiert schlank, Breite hat der Community-Platzhirsch schon
- openDesk-Suite-Breite (OpenProject, XWiki, Matrix, OX) - Phase 3 nach Oktober 2026, eigener Meilenstein
- Tool-Flut (100+ Tools) - bewusste Gegenposition zum Platzhirsch; Client-Tool-Limits (z.B. Cursor 80) machen Flut zum Nachteil
- Destruktive Operationen (Löschen, Überschreiben, Teilen/Freigaben ändern) - Sicherheitsversprechen der v1: "kann konstruktionsbedingt nichts zerstören"
- Eigener LLM/RAG-Index - der MCP liefert Daten, das Modell sitzt beim Client; semantische Suche hat der Platzhirsch (Qdrant+Ollama), wir differenzieren über Zugänglichkeit und Auth
- Konkurrenz zum Nextcloud Assistant/context_agent als Agent-Plattform - wir sind bewusst MCP-only (genau die in context_agent#203 gewünschte, unerfüllte Nische)

## Context

**Marktlage (recherchiert 14.08.2026):**
- Offizieller MCP-Server existiert versteckt in der ExApp context_agent: nur statische App-Passwort-Bearer (kein OAuth, Issue #74), skaliert laut eigener Doku nicht, aktuell inkompatibel mit MCP-SDK >= 1.28 (Issue #227), MCP-only-ExApp explizit gewünscht und abgelehnt/nicht gebaut (Issue #203)
- Community-Platzhirsch cbcoutinho/nextcloud-mcp-server: 324 Stars, sehr aktiv, 110+ Tools über 12 Apps, AGPL, Login Flow v2, semantische Suche; kein ExApp, kein spec-konformes OAuth, keine Per-User-Verwaltung in der NC-UI
- Unbesetzte Lücken = unsere Differenzierer: (1) MCP-Authorization-Spec-OAuth, (2) Per-User-Verwaltung in Nextcloud-Settings, (3) Remote-Skalierbarkeit, (4) MCP-only-ExApp im Store

**Wiederverwendbare Basis:** InfraNode-MCP (C:\Users\Student\infranode-api\src\infranode\mcp\, live auf mcp.infranode.dev): Tool-Annotationen, Schema-Diät (-27% Tokens), Graceful-Degradation-Wrapper, ASGI-Rate-Limiting, freistehende testbare Tool-Funktionen, Registry-Listing-Playbook.

**Nextcloud-API-Matrix (recherchiert):** WebDAV (Dateien + SEARCH), CalDAV, CardDAV, Notes-REST, Deck-REST, Unified Search OCS (berechtigungstreu, parallelisierbar über Provider). OCS immer mit OCS-APIRequest: true + Accept: application/json.

**MCP-Spec-Lage (korrigiert 14.08. nach Stack-Research):** mcp 2.0.0 ist seit 28.07.2026 GA (stabil), 1.x ist Maintenance-only. Entscheidung: mcp>=2.0,<3 (bedient 2025er- und 2026er-Stateless-Clients aus demselben Endpoint), dokumentierter Fallback-Pin >=1.29,<2. Kein Session-State in Tools (Pagination über Handles).

**Strategisches Umfeld:** Termin Dataport/Brandmann 21.08. (MCP-These), DFKI/Porta ab 25.08., MUCGPT 2.0 kann MCP (Abnehmer-Story München/Stuttgart), ZenDiS/openDesk als Phase-3-Ziel. Nextcloud Conference September 2026 = Launch-Anker.

## Constraints

- **Timeline**: v1 lauffähig + App-Store-Einreichung vor der Nextcloud Conference September 2026 - harte Deadline, notfalls Scope kürzen, nie den Termin
- **Tech stack**: Python 3.13 + offizielles MCP-SDK (mcp[cli] ~1.27), uv als Toolchain (lokales System-Python ist defekt), Docker/WSL2 für lokale Test-Nextcloud
- **Lizenz**: AGPL-3.0 - passt zur Nextcloud-Ökosystem-Kultur und maximiert die Chance offizieller Übernahme
- **Repo**: public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab) - Konto-Trennungs-Regel
- **Solo-Betrieb**: Ein Entwickler; Wartungsaufwand pro Feature zählt, kuratiert schlank schlägt breit
- **Sprache**: Code/README Englisch (internationales Nextcloud-Publikum), Projektkommunikation Deutsch; keine Em-Dashes, echte Umlaute in deutschen Texten
- **Security**: Der MCP darf nie mehr sehen als der angemeldete Nutzer (Berechtigungs-Durchgriff); keine destruktiven Writes in v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| MCP-only-ExApp statt Standalone-Server oder context_agent-Konkurrenz | Explizit nachgefragte, unbesetzte Nische (context_agent#203); Store-Distribution = Zugänglichkeits-Vorsprung | ✓ Good — im Store gelandet, Nische bestätigt (Release-Ankündigung in #203 positiv aufgenommen) |
| OAuth 2.1 nach MCP-Authorization-Spec als Kern-Differenzierer | Meistgefordertes Feature im Ökosystem (context_agent#74); niemand hat es | ✓ Good — Claude.ai und ChatGPT verbinden plug-and-play, E2E gemessen |
| Kuratiert schlank (~15-20 Tools) statt Tool-Flut | Client-Tool-Limits real; Platzhirsch hat Breite schon; Schema-Diät-Patterns vorhanden | ✓ Good — 16 Tools bei 11268/12500 Bytes Budget |
| mcp>=2.0,<3 statt 1.x (revidiert 14.08.) | 2.0.0 seit 28.07. GA; v2 bedient alte und neue Clients aus einem Endpoint | ✓ Good — Matrix-Test SDK 1.29 + 2.x gegen dieselbe URL grün |
| Contribution-Fix an context_agent#227 als Flanke | Sichtbarkeit + Goodwill beim Nextcloud-Team vor der Conference | ✓ Good — Fix eingereicht, Disclosure platziert |
| AGPL-3.0 | Ökosystem-Kultur; Übernahme-Chance wichtiger als maximale Wiederverwendbarkeit | ✓ Good |
| Risikoarme Writes, destruktive Ops ausgeschlossen | "Kann nichts zerstören" ist Verkaufsargument, kein Mangel | ✓ Good — als Gate implementiert (AST-Grep), Kern der Store-Beschreibung und des LinkedIn-Narrativs |
| Fail-closed bei DCR-redirect_uris revidiert zu Teilregistrierung (20.08.) | Cursor registriert 3 URIs auf einmal, eine unzulässige sperrte den ganzen Client aus | ✓ Good — wirkt live (201 mit den zwei zulässigen Adressen); Cursor scheitert danach an sich selbst (schickt die verworfene cursor://-Adresse an /authorize) |
| BL-14 "sichtbar machen plus Doku" statt cursor://-Registrierung (Owner, 20.08.) | D-35 steht (Desktop-Schemes kann jede App abfangen); E5-Seite nennt den App-Passwort-Ausweg, Doku den Grund | ✓ Good — Phase 6 verified 6/6, kein Sicherheitsversprechen aufgeweicht |
| MUCGPT-Verprobung als geführte Lücke abgenommen (Owner, 20.08.) | Braucht fremde Instanz (it@M); Protokoll einlösbar dokumentiert | — Pending (Mail gesendet, Antwort ausstehend) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-20 after phase 6 completion*
