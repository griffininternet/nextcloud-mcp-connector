# MCP Connector für Nextcloud (Arbeitstitel)

## What This Is

Ein schlankes MCP-only-ExApp für Nextcloud: Nutzer installieren es per Klick aus dem Nextcloud App Store und verbinden damit ihre Nextcloud (Dateien, Kalender, Notizen, Aufgaben, Kontakte) als Werkzeug mit KI-Assistenten wie Claude, MUCGPT, Cursor oder eigenen Agenten. Zielgruppe v1: Entwickler und Selfhoster; ab Phase 2 deutsche Behörden und Unternehmen mit Datenschutz-Anforderungen (souveräner Arbeitsplatz, openDesk).

## Core Value

Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Als ExApp per Klick aus dem Nextcloud App Store installierbar (AppAPI/Deploy Daemon)
- [ ] MCP-Spec-konformes OAuth 2.1 (Authorization-Spec: Protected Resource Metadata, Client-Registrierung), damit Claude.ai/ChatGPT-Connectoren plug-and-play funktionieren
- [ ] Per-User-Verwaltung in den Nextcloud-Settings (Zugriff aktivieren/deaktivieren, Tokens einsehen/widerrufen)
- [ ] Kuratierte Tool-Basis (~15-20 Tools): Dateien (WebDAV suchen/lesen/hochladen), Kalender (CalDAV), Notes (REST), Deck (REST), Kontakte (CardDAV), Unified Search (OCS, berechtigungstreu)
- [ ] Gamechanger-Tool prepare_context: bündelt zu einer Anfrage selbstständig relevante Dateien, Termine, Notizen und Karten in einer token-effizienten Antwort
- [ ] Risikoarme Writes (Notiz/Karte/Termin anlegen, Datei hochladen); destruktive Operationen konstruktionsbedingt ausgeschlossen; sichtbares Permission-Level pro Tool
- [ ] Transport: Streamable HTTP (remote, stateless-ready) und stdio (lokal); Auth-Fallback App-Passwort + Login Flow v2 (Browser-Onboarding)
- [ ] App-Store-Einreichung (Zertifikat, Signatur, Listing) vor der Nextcloud Conference im September 2026
- [ ] Flanke: gezielter Contribution-Fix an nextcloud/context_agent (Issue #227, MCP-SDK >= 1.28 Inkompatibilität) als Türöffner beim Nextcloud-Team

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

**MCP-Spec-Lage:** Spec 2026-07-28 (stateless core) ist frisch, SDKs dafür Beta. Entscheidung: stabiler SDK-Stand mcp[cli] ~1.27 (wie InfraNode), Architektur upgradefähig halten (Pagination über Handles, kein Session-State in Tools).

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
| MCP-only-ExApp statt Standalone-Server oder context_agent-Konkurrenz | Explizit nachgefragte, unbesetzte Nische (context_agent#203); Store-Distribution = Zugänglichkeits-Vorsprung | - Pending |
| OAuth 2.1 nach MCP-Authorization-Spec als Kern-Differenzierer | Meistgefordertes Feature im Ökosystem (context_agent#74); niemand hat es | - Pending |
| Kuratiert schlank (~15-20 Tools) statt Tool-Flut | Client-Tool-Limits real; Platzhirsch hat Breite schon; Schema-Diät-Patterns vorhanden | - Pending |
| Stabiler SDK-Stand 1.27 statt 2.0-Beta | Deadline September; Beta-APIs beweglich; Architektur bleibt upgradefähig | - Pending |
| Contribution-Fix an context_agent#227 als Flanke | Sichtbarkeit + Goodwill beim Nextcloud-Team vor der Conference | - Pending |
| AGPL-3.0 | Ökosystem-Kultur; Übernahme-Chance durch Nextcloud wichtiger als maximale Wiederverwendbarkeit | - Pending |
| Risikoarme Writes, destruktive Ops ausgeschlossen | "Kann nichts zerstören" ist Verkaufsargument, kein Mangel | - Pending |

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
*Last updated: 2026-08-14 after initialization*
