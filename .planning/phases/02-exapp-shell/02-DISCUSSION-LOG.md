# Phase 2: ExApp-Shell - Discussion Log

**Date:** 2026-08-15
**Mode:** --auto (autonome Auswahl der jeweils empfohlenen Option, einmaliger Durchgang laut Auto-Modus-Regel)

## Auto-Auswahl-Protokoll

[--auto] Selected all gray areas: ExApp-Gerüst/Paketierung, Identitäts-Durchgriff, Spike-Reihenfolge/Go-No-Go, Test-Infrastruktur.

[auto] ExApp-Gerüst: Q: "Eigenes minimales AppAPI-Gerüst oder nc_py_api?" -> Selected: "Minimal selbst, nc_py_api nur bei nachgewiesener Handshake-Fragilität (dann Owner-Package-Gate)" (empfohlen; Begründung: 01-RESEARCH warnt vor FastAPI/niquests/caldav-Ballast, unsere ASGI-App existiert bereits)
[auto] ExApp-Gerüst: Q: "Neues Projekt oder dritter Betriebsmodus derselben Codebasis?" -> Selected: "Dritter Betriebsmodus, stdio+HTTP bleiben funktionsfähig" (empfohlen; Phase-1-Produkt bleibt nutzbar)
[auto] Identitäts-Durchgriff: Q: "Wo hängt die Impersonation ein?" -> Selected: "Vierter Credential-Modus in deps/NcClients, Tool-Code unangetastet" (empfohlen; designierte Naht aus Phase 1)
[auto] Identitäts-Durchgriff: Q: "Was passiert, wenn eine API-Familie keine Impersonation kann?" -> Selected: "Familie nutzt Nutzer-App-Passwort, dokumentiert; kein Shared-Admin-Token, keine stillen Fallbacks" (empfohlen; Out-of-Scope-Regel aus PROJECT.md)
[auto] Spikes: Q: "Welcher Spike zuerst?" -> Selected: "Discovery-Spike (AUTH-06) als früher eigener Plan" (empfohlen; Hauptrisiko, Go/No-Go für Phase 3)
[auto] Spikes: Q: "Was zählt als Go?" -> Selected: "PRM + WWW-Authenticate unauthentifiziert von außen durch den Proxy; No-Go nur mit getesteter, dokumentierter Fallback-Route" (empfohlen; Roadmap Success Criterion 3)
[auto] Test-Infrastruktur: Q: "compose oder AIO zuerst?" -> Selected: "compose primär, AIO als zweiter Smoke; falls AIO lokal unverhältnismäßig: dokumentierte Übergabe an Phase 5" (empfohlen)

## Deferred Ideas
- Keine neuen in dieser Discussion; Bestand siehe 02-CONTEXT.md <deferred>.

## Hinweis
Kein SPEC.md, keine Todos (todo.match-phase: 0 Treffer), keine Codebase-Maps (.planning/codebase leer; Scout stützte sich auf 01-RESEARCH.md und den Phase-1-Code).
