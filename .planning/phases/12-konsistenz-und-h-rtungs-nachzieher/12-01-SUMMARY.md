---
phase: 12-konsistenz-und-h-rtungs-nachzieher
plan: 01
subsystem: api
tags: [mcp, talk, spreed, answer-format, token-budget, pagination]

# Dependency graph
requires:
  - phase: 10-mail
    provides: "das Vorbild dieses Fixes (Review-Befund IN-01, Commit 53ba602): preview_truncated auf der Eintragsebene, truncated auf der Antwortebene, Begruendungskommentar plus Modul-Docstring-Absatz plus zwei Tests"
  - phase: 09-talk
    provides: "die Projektion _message mit der Byte-Kappung bei MAX_MESSAGE_BYTES und die Marker-Hygiene ME-03, die hier woertlich erhalten bleibt"
  - phase: 11
    provides: "talk_tools.one_message als oeffentliche Schnittstelle, ueber die chatgpt._fetch_message die Kappung liest"
provides:
  - "talk_browse(level=messages): die Eintragsebene meldet eine bei MAX_MESSAGE_BYTES gekappte Nachricht als message_truncated, die Antwortebene behaelt truncated samt next"
  - "chatgpt._fetch_message liest message_truncated und meldet die Kappung weiterhin als metadata['truncated'] (eine Ebene, ein Wort)"
  - "Tool-Docstring von talk_browse mit genau einer Bedeutung je Ebene ('truncated: page cut; message_truncated: message cut.')"
  - "Modul-Docstring-Absatz in reg_talk.py, der die Byte-Ausgabe mit der gemessenen Luft rechtfertigt"
  - "Test fuer den gemeinsamen Fall: gekappte Seite und gekappte Nachricht in einer Antwort, getrennte Behauptungen je Ebene"
affects: [13-release-und-changelog, prepare_context, fetch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Wort, eine Bedeutung je Antwortebene: ein Eintragsschluessel, der dasselbe Wort wie der Antwortschluessel traegt, wird umbenannt statt erklaert"
    - "Der zweite Leser einer Projektion wird im gleichen Task geaendert wie die Projektion, weil entry.get() nicht wirft"
    - "Byte-Ausgabe im Tool-Docstring wird im Modul-Docstring mit der gemessenen Luft begruendet, nicht mit einer Schaetzung"

key-files:
  created: []
  modified:
    - src/mcp_connector/tools/talk.py
    - src/mcp_connector/tools/chatgpt.py
    - src/mcp_connector/server/reg_talk.py
    - tests/unit/test_talk_tools.py

key-decisions:
  - "Der Eintragsschluessel heisst message_truncated und die Antwortebene behaelt truncated; die Alternative (Antwortebene umbenennen) haette vier bestehende Waechter und die cursor-Field-Description gebrochen, ohne die Doppelbedeutung besser aufzuloesen"
  - "metadata['truncated'] in fetch bleibt woertlich: fetch antwortet genau eine Nachricht, hat also genau eine Ebene, und dort ist ein Wort eindeutig"
  - "Keine Gegenkompression an anderer Stelle in reg_talk.py: talk_browse stand bei 858 von 1400 Bytes, anders als mail_browse mit 24 Bytes Luft im Vorbild-Edit"
  - "Der gemeinsame Fall (Seite gekappt und Nachricht gekappt) steht in genau einem Test statt in zwei, weil genau diese Gleichzeitigkeit die Doppelbedeutung zum Problem gemacht hat"
  - "Der Changelog-Block 0.1.9 wird hier bewusst nicht angefasst; die Formataenderung ist eine Uebergabe an Phase 13 (EXAPP-09)"

patterns-established:
  - "Kappungsschluessel je Ebene: truncated = Seite/Fenster (mit next), <ding>_truncated = Inhalt eines Eintrags (ohne Fortsetzung); jetzt in mail und talk gleich"
  - "Quelltext-Pruefschritt trennt entry[...] von answer[...], damit eine Ruecknahme der Trennung sichtbar wird statt still zu passieren"

requirements-completed: [TOOL-17]

# Metrics
duration: 9min
completed: 2026-08-25
---

# Phase 12 Plan 01: Konsistenz und Härtungs-Nachzieher Summary

**Die Nachrichtenebene von `talk_browse(level="messages")` heißt jetzt `message_truncated`, die Antwortebene behält `truncated` samt `next`, `fetch` meldet die Kappung weiterhin, und die Messung belegt 912 statt 858 Bytes bei unangetasteten Gates.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-08-25T12:25:54Z
- **Completed:** 2026-08-25T12:35:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Talk ist nicht mehr die Werkzeugfamilie, die dasselbe Wort auf zwei Ebenen benutzt: `truncated` heißt ausschließlich "dieses Fenster wurde geschnitten, es gibt ein `next`", `message_truncated` heißt ausschließlich "dieser Text wurde bei `MAX_MESSAGE_BYTES` geschnitten, dafür gibt es kein `next`".
- Der zweite Leser der Projektion (`chatgpt._fetch_message`) zieht im gleichen Commit mit, deshalb hat `fetch("message:<token>/<id>")` die Kappung nicht still verloren; `tests/unit/test_chatgpt_fetch.py` ist ohne eine einzige Änderung grün und war der Wächter dafür.
- Der Tool-Docstring nennt für jede Ebene genau eine Bedeutung, in der Form des Mail-Vorbilds, und der Modul-Docstring begründet diese Bytes mit der gemessenen Luft statt mit einer Schätzung.
- Der Fall, der die Doppelbedeutung überhaupt erst zu einem Problem gemacht hat (Seite und Nachricht gleichzeitig gekappt), hat jetzt einen Test mit getrennten Behauptungen je Ebene, inklusive Cursor-Scope `"c"`.
- Kein Gate wurde angehoben: `scripts/check_tool_budget.py` ist unverändert, 21 Werkzeuge, `BUDGET_BYTES` 18000, `MAX_TOOL_BYTES` 1400.

## Task Commits

Jede Aufgabe wurde atomar committet:

1. **Task 1: Die Nachrichtenebene bekommt ihren eigenen Namen, und der zweite Leser zieht im gleichen Schritt mit** - `066d8ec` (fix)
2. **Task 2: Der Tool-Docstring sagt die eine Bedeutung je Ebene, und die Messung belegt, dass kein Gate angehoben werden muss** - `cc0037b` (docs)

## Files Created/Modified

- `src/mcp_connector/tools/talk.py` - Eintragsschlüssel `message_truncated` mit Begründungskommentar (nennt `MAX_MESSAGE_BYTES`, die Antwortebene, `DF-11-01` und `IN-01`); der Docstring von `_message` nennt den Feldnamen ausdrücklich und behält die ME-03-Begründung; der Modul-Docstring nennt beide Namen nebeneinander (kostet keine `tools/list`-Bytes)
- `src/mcp_connector/tools/chatgpt.py` - `_fetch_message` liest `entry.get("message_truncated")`; `metadata["truncated"] = "true"` bleibt wörtlich, mit einem Kommentar darüber, warum die zwei Namen hier auseinandergehen
- `src/mcp_connector/server/reg_talk.py` - Tool-Docstring plus `truncated: page cut; message_truncated: message cut.`; Modul-Docstring-Absatz mit der gemessenen Luft; die `cursor`-Field-Description ist unverändert
- `tests/unit/test_talk_tools.py` - Kappungstest behauptet `message_truncated is True` und `"truncated" not in entry`, die vier Marker-Hygiene-Behauptungen sind wörtlich erhalten; neu `test_a_cut_window_and_a_cut_message_are_two_keys_with_two_meanings`

## Antwortformat-Änderung (Übergabe an Phase 13)

**Betroffenes Werkzeug:** `talk_browse`
**Betroffene Ebene:** Eintragsebene von `level="messages"`, also jeder Eintrag in `results`
**Änderung:** der Schlüssel `truncated` eines Eintrags heißt `message_truncated`

Die Antwortebene derselben Antwort (`truncated` plus `next`) und die Konversationsebene (`truncated` plus `total`) sind unverändert, ebenso `metadata["truncated"]` in `fetch`. Das ist damit die einzige nutzersichtbare Änderung dieses Plans und deckt sich mit SC5 der Roadmap.

**Dieser Plan fasst `CHANGELOG.md` bewusst nicht an.** Der Block 0.1.9 gehört zu Phase 13 (EXAPP-09), und die Zeile, die dort entstehen muss, lautet inhaltlich: unter `### Changed` die Umbenennung des Eintragsschlüssels in `talk_browse(level="messages")` von `truncated` zu `message_truncated`, mit dem Hinweis, dass ein Client mit persistierter Tool-Liste den neuen Docstring erst nach seiner nächsten Auffrischung sieht (dieselbe Lage wie beim 0.1.8-Fix von `mail_browse`, dort in `11-05-SUMMARY.md` unter "User Setup Required" protokolliert). Vorlage für den Wortlaut: der 0.1.8-Eintrag zu `preview_truncated`.

## Byte-Messung

| Messpunkt | Vor dem Edit | Nach dem Edit | Gate |
|-----------|--------------|---------------|------|
| `talk_browse` | 858 Bytes | 912 Bytes | `MAX_TOOL_BYTES` 1400 (unverändert) |
| `tools/list` gesamt | 15657 Bytes | 15711 Bytes | `BUDGET_BYTES` 18000 (unverändert) |
| Werkzeuge | 21 | 21 | Contract-Test |

Der erklärende Satz kostet 54 Bytes, die Vorhersage der Recherche lautete "rund 911 und rund 15710". `scripts/check_tool_budget.py` ist im Diff nicht enthalten, weder `BUDGET_BYTES` noch `MAX_TOOL_BYTES` wurden angefasst. Alles, was Bytes gekostet hat, steht im Tool-Docstring; der Modul-Docstring-Absatz und die Kommentare kosten null.

## Decisions Made

- Umbenannt wurde die Eintragsebene, nicht die Antwortebene. Die Antwortebene ist in vier bestehenden Tests (`test_talk_tools.py:361, 530, 630, 655`), in der `cursor`-Field-Description und in `context._digest` verankert; eine Umbenennung dort hätte mehr Fläche bewegt, ohne die Doppelbedeutung besser aufzulösen.
- `metadata["truncated"]` in `fetch` bleibt wörtlich. `fetch` antwortet genau eine Nachricht und hat damit genau eine Ebene; die zwei Namen gehen dort auseinander, und ein Kommentar sagt warum.
- Keine Gegenkompression in `reg_talk.py`. Das Mail-Vorbild musste seine Filterzeile im gleichen Edit kürzen (24 Bytes Luft), Talk hatte 542.
- `_CURSOR_HINT` in `tools/talk.py` blieb unangetastet: er spricht über die Konversationsliste, die kein `next` hat, und ist damit wörtlich richtig.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Die Vorhersage der Recherche zur Byte-Ausgabe (rund 911 / rund 15710) traf auf ein Byte genau zu, und `tests/unit/test_chatgpt_fetch.py` wurde nie rot, weil der Verbraucher im gleichen Task mitgezogen wurde.

## Verification

- `uv run --no-sync pytest -q`: grün (gesamte Suite)
- `uv run --no-sync pytest tests/contract -q`: grün
- `uv run --no-sync pytest tests/unit/test_talk_tools.py tests/unit/test_chatgpt_fetch.py -q`: grün, `test_chatgpt_fetch.py` ohne eine Änderung
- `uv run --no-sync ruff check .`, `ruff format --check .`, `pyright` (0 errors), `vulture src scripts vulture_whitelist.py`: grün
- `uv run --no-sync python scripts/check_tool_budget.py`: Exit-Code 0, 15711 Bytes, 21 Werkzeuge
- Quelltext-Gate: jede `entry[...]`-Zuweisung mit `truncated` in `tools/talk.py` benutzt `message_truncated`, keine `answer[...]`-Zuweisung tut das; `["truncated"]` findet nur noch `talk.py:499` und `talk.py:713`, beide Antwortebene
- `git diff --stat`: keine Änderung an `scripts/check_tool_budget.py`, `CHANGELOG.md`, `appinfo/info.xml`, `pyproject.toml` oder `uv.lock`

## User Setup Required

None - no external service configuration required. Ein Client mit persistierter Tool-Liste sieht den neuen Docstring erst nach seiner nächsten Auffrischung; das ist eine Changelog-Zeile in Phase 13 und keine Handlung des Betreibers.

## Next Phase Readiness

- TOOL-17 ist geschlossen; die drei übrigen Code-Schulden dieser Phase (TOOL-18 Id-Codec-Hygiene, TOOL-19 README plus `_room`-Privatdurchgriff, SEC-02 Security-Nachzieher) sind unberührt und können unabhängig laufen. `tools/talk.py` und `tools/chatgpt.py` werden von TOOL-19 erneut angefasst, `reg_talk.py` nicht mehr.
- Übergabe an Phase 13: der Changelog-Block 0.1.9 braucht die Zeile zur Umbenennung (siehe Abschnitt "Antwortformat-Änderung").
- Byte-Reserve für den Rest des Milestones: 2289 Bytes in der Oberfläche, 488 Bytes bei `talk_browse`.

## Self-Check: PASSED

Alle vier geänderten Dateien existieren, beide Task-Commits (`066d8ec`, `cc0037b`) stehen in der Historie, und keine der in dieser Zusammenfassung genannten Messungen ist geschätzt.

---
*Phase: 12-konsistenz-und-h-rtungs-nachzieher*
*Completed: 2026-08-25*
