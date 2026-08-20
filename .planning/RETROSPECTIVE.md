# Retrospective: MCP Connector für Nextcloud

Living document, appended at each milestone close.

## Milestone: v1.0 — MVP im Store

**Shipped:** 2026-08-20
**Phases:** 5 | **Plans:** 50 | **Tasks:** 111 | **Timeline:** 2026-08-14 bis 2026-08-20 (7 Tage)

### What Was Built

Ein MCP-only-ExApp für Nextcloud, live im App Store (0.1.0 am 19.08., 0.1.2 am 20.08.):
16 kuratierte, auf Lesen ausgelegte Tools (Dateien, Kalender, Notizen, Deck, Kontakte,
Unified Search, prepare_context), eigener OAuth-2.1-Autorisierungsserver nach
MCP-Authorization-Spec (E2E gegen Claude.ai und ChatGPT bewiesen), Per-User-Verwaltung
mit Pause/Disconnect, Purge-Kommando mit vollständiger Datenräumung, dreisprachige
Store-Texte und siebenteilige Client-Doku.

### What Worked

- Messen statt vermuten: Jede kritische Annahme wurde live gemessen (Discovery-Spike,
  DAV-Impersonation, 401-Ursache, Crash-Loop-Rundlauf). Zwei Vermutungen aus früheren
  Sessions wurden dadurch widerlegt statt fortgeschrieben (401 "wirkt nie", Loopback als
  Cursor-Blocker).
- Gap-Closure-Zyklus: Verifier fand 3 echte Lücken nach Phase 5; der --gaps-Lauf schloss
  sie in einem Tag mit Live-Nachweisen statt Behauptungen.
- Runbooks zahlen sich sofort aus: docs/store-submission.md machte das 0.1.2-Release
  ohne Recherche möglich; der Session-basierte Store-Upload ist jetzt dokumentiert.
- Design-Konstante "kann nichts zerstören" trug durch alles: Architektur-Gate, Tests,
  Store-Text, LinkedIn-Narrativ, FAQ.

### What Was Inefficient

- Worktree-Isolation funktioniert in dieser Umgebung nicht (CWD system32 ist kein Repo);
  alle Executor liefen sequenziell. Bei 16 Plänen in Phase 5 kostete das Wandzeit.
- Plan 05-13 wurde gegen eine ungeprüfte Annahme geplant (Overlay-Cache); die Messung in
  05-12 machte 2 von 3 Tasks obsolet. Messung vor Planung wäre billiger gewesen.
- Der Review-Fund-Backlog (BL-08..BL-13) sammelte sich über drei Phasen, bevor ein
  einziger Abarbeitungstag ihn leerte; kleinere, frühere Batches hätten Re-Reviews gespart.

### Patterns Established

- Executor-Umgebungsblock (cd-Falle, uv --no-sync, Commit-Regeln) als Standard-Prompt.
- Beweistabellen mit Datum+Kommando in Runbooks (store-submission, MEASUREMENTS-Dateien).
- Gemeinsame Härtungs-Helfer statt Duplikate (bounded_body, marks.py, store_opener).
- Owner-Entscheidungen als kompakte Batch-Frage einholen, dann autonom durcharbeiten.

### Key Lessons

- Auto-Modus-Checkpoints: erste Option nie blind wählen, wenn sie physisch unmöglich ist
  (MUCGPT ohne Instanz); Evidenz schlägt Regel.
- Upstream zuerst suchen: der NC-34-UI-Befund war bereits gemeldet UND gefixt (34.0.3);
  das ersparte ein Duplikat-Issue.
- Release-Tags und Milestone-Tags müssen kollisionsfrei sein: release.yml triggert auf
  v*, daher Milestone-Tag milestone-v1.0 statt v1.0.
- Der Store hotlinkt Screenshot-URLs: Bildtausch ohne Release möglich, solange die URL
  stabil bleibt.

### Cost Observations

- Modell-Mix: Executor/Planner opus, Checker/Verifier sonnet; Orchestrierung in einer
  Session mit Sub-Agents (größte Läufe ~200-300k Tokens je Executor).
- Sessions: im Kern 6 Arbeitstage (14.-20.08.), Abschlusstag mit ~20 Commits und Release.

## Cross-Milestone Trends

| Metrik | v1.0 |
|--------|------|
| Phasen / Pläne / Tasks | 5 / 50 / 111 |
| Kalenderzeit | 7 Tage |
| Verifier-Gap-Runden | 1 (Phase 5) |
| Live-Releases im Milestone | 3 (0.1.0, 0.1.1, 0.1.2) |
