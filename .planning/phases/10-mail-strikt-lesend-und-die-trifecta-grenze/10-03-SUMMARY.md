---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 03
subsystem: backend
tags: [mail, html, lxml, text-extraction, marks, prompt-injection, xxe, unit-tests]

# Dependency graph
requires:
  - phase: 01-server-kern
    provides: "tools/marks.py mit EXCERPT_TRUNCATION, TRUNCATION_NOTE, _PATTERNS und without_marks; lxml seit Phase 1 in pyproject.toml"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-01: die gemessene Byte-Kappe (Volltext 32 KiB, Newsletter nach Wandlung 25582 Bytes); Plan 10-02: clients/mail.py mit get_message und body_missing"
provides:
  - "src/mcp_connector/tools/html_text.py mit genau einer öffentlichen Funktion: to_text(html: str) -> str"
  - "to_text löst Entities auf, setzt Zeilenumbrüche an Blockgrenzen, wirft nie und kappt nie"
  - "marks.FINAL_TRUNCATION: die dritte Kappungsmarkierung, wahr für eine Mail (kein Werkzeug, kein Offset)"
  - "FINAL_TRUNCATION steht in _PATTERNS, also entfernt without_marks sie ohne Änderung am Filter"
  - "tests/unit/test_html_text.py: 13 Tests, jeder eine Messung an lxml 6.1.1"
affects: [10-04, 10-05, 10-06, 10-07, 10-08, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein-Zweck-Helfer nach der Vierblock-Form von marks.py: was es tut, was es kostet, was es nicht ist, die honest limit"
    - "Fremdes Markup wird aus UTF-8-Bytes mit explizitem encoding geparst, nie aus dem String: das überlebt eine XML-Deklaration und ein widersprüchliches meta charset"
    - "Ein neuer Marker kommt zusammen mit seinem Muster, nie danach: ein Marker ohne Filter ist der Angriffsweg selbst (ME-03)"
    - "Unit-Tests als Regressionswächter über eine Bibliotheksfassung: der gemessene Wert wird festgeschrieben, auch wenn ein schönerer denkbar wäre"

key-files:
  created:
    - "src/mcp_connector/tools/html_text.py"
    - "tests/unit/test_html_text.py"
  modified:
    - "src/mcp_connector/tools/marks.py"
    - "tests/unit/test_truncation_marks.py"
    - "vulture_whitelist.py"

key-decisions:
  - "Die öffentliche Funktion heisst to_text und nimmt einen String und gibt einen String zurück; Plan 10-05 baut gegen html_text.to_text"
  - "Der dritte Marker heisst FINAL_TRUNCATION und lautet wörtlich: [truncated here; the rest was not returned and there is no way to continue]"
  - "Blockelemente, die einen Zeilenumbruch setzen: p, div, li, tr, h1, h2, h3, h4, h5, h6, blockquote, table (davor und dahinter) plus br (nur dahinter)"
  - "Geparst wird aus UTF-8-Bytes mit HTMLParser(no_network=True, encoding=utf-8) statt aus dem String: gemessen identisches Ergebnis, aber eine XML-Deklaration wirft dann nicht mehr und ein falsches meta charset lügt nicht mehr"
  - "script, style, noscript und template werden per drop_tree entfernt, obwohl HTMLPurifier in der App schon aufräumt: die Verteidigung gehört an die Stelle, die den Text verarbeitet (T-10-17)"
  - "Der Rest eines internen DTD-Subsets (die Zeichen ]>) bleibt im Text und wird benannt statt weggeputzt: eine zweite Reinigungsregel über fremdem Text wäre eine zweite Wahrheit"
  - "Ein Non-Breaking-Space bleibt einer; die Wandlung normalisiert fremden Text nicht"
  - "to_text kappt nicht: die Byte-Kappe gehört zur Aufrufstelle, wo der Schnitt markiert werden kann (Plan 10-05)"
  - "MAIL-02 bleibt Pending: dieser Plan baut die zwei Bausteine, das Volltext-Werkzeug entsteht in Plan 10-05"

patterns-established:
  - "Messwert als Kommentar: jede der vier Eigenschaften von to_text trägt die Messung, aus der sie folgt, im Quelltext"
  - "Ein geparkter Aufrufer bekommt einen begründeten Whitelist-Eintrag mit dem Plan, der ihn wieder entfernt (Muster der Mail-Transportschicht aus 10-02)"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-08-24
---

# Phase 10 Plan 03: Der HTML-zu-Text-Wandler und die dritte Kappungsmarkierung, Zusammenfassung

**`html_text.to_text(html: str) -> str` wandelt fremdes Mail-HTML mit lxml in Absätze statt in eine Wortkette, und `marks.FINAL_TRUNCATION` ist die erste Kappungsmarkierung, die für eine Mail wahr ist und von Anfang an gefiltert wird.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-24T13:16:00Z
- **Completed:** 2026-08-24T13:41:00Z
- **Tasks:** 3
- **Files modified:** 5 (2 neu, 3 geändert)

## Accomplishments

- `tools/html_text.py` mit genau einer öffentlichen Funktion. Alle vier Eigenschaften sind
  gemessene Werte und tragen ihre Messung als Kommentar: Leer-Schutz vor dem Parsen,
  `drop_tree()` auf `script`/`style`/`noscript`/`template`, Blockelemente als Zeilenumbrüche,
  `no_network=True`.
- Die teuerste Falle der Familie ist festgenagelt: eine reine Textmail in der Form nach
  `convertLinks` (Korrektur K2) ergibt `Grüße aus Hamburg` und `die Straße ist gesperrt`
  statt `Gr&uuml;&szlig;e` und `<a href=...>`.
- `marks.FINAL_TRUNCATION` sagt das Einzige, was für eine gekappte Mail wahr ist: hier ist
  Schluss, es gibt keine Fortsetzung. Sie nennt weder `files_read` noch `fetch` noch einen
  Offset, weil beide bestehenden Marker ein Modell in eine Schleife oder in eine nicht
  existierende API schicken würden (Falle 6, T-10-18).
- Der Marker steht ab der ersten Zeile in `_PATTERNS`, also entfernt `without_marks` ihn aus
  fremdem Mailtext, ohne dass der Filterrumpf angefasst wurde (ME-03, T-10-16).
- 13 neue Unit-Tests für den Wandler plus 5 neue für den Marker; die volle Default-Auswahl
  steht bei 2530 grünen Tests.

## Task Commits

1. **Task 1: tools/html_text.py, die vier gemessenen Anforderungen** - `bca12bf` (feat)
2. **Task 2: Der dritte Marker, für eine Kappung ohne Fortsetzung** - `054f586` (feat)
3. **Task 3: Unit-Abdeckung des Wandlers, an den gemessenen Fällen** - `650f184` (test)

## Files Created/Modified

- `src/mcp_connector/tools/html_text.py` (neu) - `to_text(html: str) -> str`, der Wandler.
  Modul-Docstring in der Vierblock-Form von `marks.py`, inklusive der Ansage, dass die
  Funktion kein Sanitizer und kein Renderer ist und `lxml_html_clean` nicht braucht.
- `src/mcp_connector/tools/marks.py` (geändert) - `FINAL_TRUNCATION` plus sein Muster in
  `_PATTERNS`; Modul-Docstring zählt jetzt drei Markierungen statt zwei. `without_marks`
  selbst ist unverändert.
- `tests/unit/test_html_text.py` (neu) - 13 Tests, jeder ein Satz über das Verhalten und
  jeder eine Messzeile aus `10-RESEARCH.md`, Abschnitt "HTML zu Text".
- `tests/unit/test_truncation_marks.py` (geändert) - fünf Tests für den dritten Marker:
  Entfernung aus fremdem Text, mehrfaches Vorkommen mitten im Text, alle drei Marker in
  einem Aufruf, kein Werkzeugname und kein Platzhalter, und die Zahl der Marker gegen die
  Zahl der Muster.
- `vulture_whitelist.py` (geändert) - `to_text` als geparkter Aufrufer bis Plan 10-05.

## Die Schnittstelle für Plan 10-05

```python
from mcp_connector.tools import marks
from mcp_connector.tools.html_text import to_text

text = to_text(body)                      # nie eine Exception, nie gekappt
text = marks.without_marks(text)          # erst fremde Marker weg
...                                       # dann kappen und markieren:
text = f"{cut}{marks.FINAL_TRUNCATION}"
```

- **Wandlungsfunktion:** `to_text(html: str) -> str` in
  `src/mcp_connector/tools/html_text.py`.
- **Dritter Marker:** `marks.FINAL_TRUNCATION`, wörtlich
  `[truncated here; the rest was not returned and there is no way to continue]`.
- **Blockelemente, die zu Zeilenumbrüchen werden:** `p`, `div`, `li`, `tr`, `h1`, `h2`, `h3`,
  `h4`, `h5`, `h6`, `blockquote`, `table` (je ein `\n` davor und dahinter) und `br` (nur ein
  `\n` dahinter, damit ein weicher Umbruch kein Absatz wird). Danach werden Zeilen getrimmt,
  Läufe von mehr als zwei Zeilenumbrüchen auf zwei gekürzt und der ganze Text getrimmt.
- **Gemessene Eigenarten, auf die 10-05 nicht hereinfallen sollte:** ein interner
  DTD-Subset-Rest hinterlässt `]>` am Textanfang, ein `&nbsp;` bleibt ein `\xa0`, und ein
  leerer oder unlesbarer Body ergibt `""` (nicht `None`, keine Exception).

## Decisions Made

- **`to_text` als Name, nicht `html_to_text`:** Am Aufrufort steht `html_text.to_text(...)`
  beziehungsweise `to_text(body)`; der Modulname trägt das `html` bereits.
- **Aus UTF-8-Bytes parsen statt aus dem String** (Abweichung nach Messung, siehe unten).
- **`noscript` und `template` zusätzlich zu `script` und `style`:** kosten im selben Aufruf
  nichts, und ihr Inhalt ist Markup für einen Browser, der nie läuft, also nicht das, was der
  Absender geschrieben hat.
- **`FINAL_TRUNCATION` statt eines Namens mit "mail":** der Marker beschreibt eine Kappung
  ohne Fortsetzung, nicht eine Familie; jede spätere Familie mit derselben Lage kann ihn
  benutzen.
- **`cast(HtmlMixin, ...)` für `drop_tree` und `text_content`:** `lxml-stubs` typisiert
  `document_fromstring` auf `_Element`, und beide Methoden leben auf `HtmlMixin`. Der Cast ist
  ein Cast und keine Umwandlung, weil der Parser oben HTML-Elemente baut.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fremdes HTML wird aus UTF-8-Bytes geparst statt aus dem String**

- **Found during:** Task 1 (tools/html_text.py)
- **Issue:** Der gemessene Weg der Recherche (`document_fromstring(str)`) wirft bei einem
  Body, der mit `<?xml version="1.0" encoding="utf-8"?>` beginnt, einen `ValueError`
  ("Unicode strings with encoding declaration are not supported"). Das ist für XHTML-Mails
  eine reale Form. Mit dem geplanten `except` hätte eine solche Mail leeren Text ergeben,
  also eine Erfolgsantwort ohne Inhalt, und genau das ist die Form, die zum Erfinden einlädt
  (T-01-75).
- **Fix:** `document_fromstring(html.encode("utf-8"), parser=HTMLParser(no_network=True,
  encoding="utf-8"))`. Am Arbeitsbaum gemessen: für alle Fälle der Messtabelle Zeichen für
  Zeichen dasselbe Ergebnis, zusätzlich überlebt der Weg die XML-Deklaration und ein
  `<meta charset>`, das dem schon dekodierten Text widerspricht.
- **Files modified:** `src/mcp_connector/tools/html_text.py`
- **Verification:** Messlauf über alle Fälle in beiden Varianten; das Verifikationsskript des
  Plans und `uv run pytest -q` sind grün.
- **Committed in:** `bca12bf` (Task-1-Commit)

**2. [Rule 3 - Blocking] `to_text` braucht einen begründeten Vulture-Eintrag bis Plan 10-05**

- **Found during:** Task 3 (Verifikationsschritt `uv run vulture`)
- **Issue:** Das Akzeptanzkriterium erwartet Vulture grün "ohne neuen Whitelist-Eintrag". Das
  ist in diesem Repo nicht erreichbar: das Gate läuft bei voller Konfidenz, und `to_text` hat
  bis Plan 10-05 keinen Produktionsaufrufer. `uv run vulture src scripts vulture_whitelist.py`
  (der CI-Schritt) wäre rot geblieben.
- **Fix:** Ein Eintrag nach dem etablierten Muster der geparkten Aufrufer (Tables 08-02, Talk
  09-01, Mail-Transport 10-02), mit Begründung und mit dem Plan, der ihn wieder entfernt.
  Der eigentliche Aufrufer kommt in 10-05; dann verlässt der Name die Liste.
- **Files modified:** `vulture_whitelist.py`
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` und
  `uv run vulture src scripts vulture_whitelist.py` sind grün.
- **Committed in:** `650f184` (Task-3-Commit)

**3. [Rule 1 - Bug] Das Marker-Verifikationsskript des Plans zählte zwei private Namen mit**

- **Found during:** Task 2 (Verifikationsschritt)
- **Issue:** Das Skript filtert Marker mit `n.isupper()`. `"_HEAD".isupper()` ist in Python
  `True`, also zählte es `_HEAD` und `_TAIL` als Marker mit und behauptete fünf statt drei.
  Der Fehler steckte im Skript, nicht im Modul: schon vor dieser Änderung hätte es vier
  gezählt.
- **Fix:** Beim Lauf `and not n.startswith("_")` ergänzt. Der Testfall
  `test_every_marker_the_module_defines_has_a_pattern` prüft dieselbe Aussage dauerhaft und
  vergleicht die Marker-Namen gegen die Zahl der Muster.
- **Files modified:** keine Produktionsdatei; die Aussage lebt jetzt in
  `tests/unit/test_truncation_marks.py`.
- **Verification:** Korrigiertes Skript grün, Testdatei grün.
- **Committed in:** `054f586` (Task-2-Commit)

---

**Total deviations:** 3 auto-fixed (1 missing critical, 1 blocking, 1 bug)
**Impact on plan:** Kein Scope-Zuwachs. Abweichung 1 macht den Volltextweg für eine reale
Mailform ehrlich, Abweichung 2 hält das Dead-Code-Gate grün, Abweichung 3 korrigiert ein
Prüfskript und ersetzt es durch einen dauerhaften Test.

## Issues Encountered

- `lxml-stubs` typisiert `document_fromstring` auf `_Element`, wo `drop_tree` und
  `text_content` nicht liegen. Gelöst mit zwei `cast(HtmlMixin, ...)` und einem Kommentar,
  der sagt, warum das ein Cast und keine Umwandlung ist.
- `ruff` PT018 verlangt aufgeteilte Assertions; drei Testzeilen wurden entsprechend zerlegt.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run pytest -q` (Default-Auswahl) | 2530 passed, 119 deselected |
| `uv run ruff check .` / `ruff format --check .` | grün, 191 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün |
| `uv run python scripts/check_tool_budget.py` | `tools/list: 14358 bytes, 20 tools, budget 15000`, Exit 0 |
| `git diff --stat -- pyproject.toml uv.lock` | leer, keine neue Abhängigkeit |
| `git diff --stat` gegen `tools/chatgpt.py`, `ids.py`, `nextcloud/` | leer |
| Verifikationsskript `html_text` aus dem Plan | `html_text ok: to_text` |
| Verifikationsskript Marker aus dem Plan (privat-Filter korrigiert) | `third marker ok: FINAL_TRUNCATION` |

## Known Stubs

Keine. `to_text` hat bis Plan 10-05 bewusst keinen Produktionsaufrufer, ist aber vollständig
implementiert und durch 13 Tests belegt; das ist ein geparkter Aufrufer und kein Stub.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 10-04 (`tools/mail.py`, die Listen-Werkzeuge) hängt nicht an diesem Plan und kann
  unabhängig laufen.
- Plan 10-05 (Volltext über `fetch` mit `mail:<databaseId>`) hat jetzt beide Bausteine:
  `html_text.to_text` und `marks.FINAL_TRUNCATION`. Die Reihenfolge dort ist die etablierte:
  erst wandeln, dann `without_marks`, dann kappen, dann den eigenen Marker anhängen.
- Offen und bewusst offen: Die Byte-Kappe selbst (10-01 hat 32 KiB gemessen) wird in 10-05
  gesetzt, nicht hier.

## Self-Check: PASSED

Alle fünf genannten Dateien existieren, die SUMMARY liegt am angegebenen Ort, und die drei
Task-Commits `bca12bf`, `054f586` und `650f184` sind im Log auffindbar.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*
