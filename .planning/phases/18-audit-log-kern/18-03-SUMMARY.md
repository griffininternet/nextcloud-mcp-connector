---
phase: 18-audit-log-kern
plan: 03
subsystem: errors
tags: [audit-log, error-handling, reason-codes, ast-gate, tdd, privacy]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "die Spalte reason im entries-Schema, die diese Kennung später aufnimmt"
  - phase: 18
    plan: 02
    provides: "das Muster eines Gates, das Befunde sammelt und gemeinsam mit Datei und Zeile meldet"
provides:
  - "ToolError mit reinem Schlüsselwortargument reason und dem Vorgabewert REASON_UNSPECIFIED"
  - "die sechs Kennungen REASON_UNSPECIFIED, REASON_PERMISSION_DENIED, REASON_UNKNOWN_ID, REASON_TIMEOUT, REASON_UNREACHABLE, REASON_GUARD_TRIPPED"
  - "REASONS: die eingefrorene Menge dieser sechs Werte"
  - "reason= an zwölf Statuszweigen über ocs, dav, caldav und carddav"
  - "reason=REASON_GUARD_TRIPPED an den drei Sicherungsorten (Talk-Sendeschalter, paging.py, ids.py)"
  - "tests/unit/test_errors_reason.py: vier Verhaltensfälle plus ein AST-Lauf über src/"
affects: [18-06, 18-07, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reines Schlüsselwortargument mit Vorgabewert statt Unterklassen je Ablehnungsart (D-17)"
    - "Kennung an der Statusabbildung, nicht an der Wurfstelle, wo ein HTTP-Status vorliegt"
    - "Kennung an der Wurfstelle, wo keine Antwort von aussen vorliegt (Sicherungen dieses Servers)"
    - "AST-Lauf über src/, der nur die reason=-Argumente an Fehlerkonstruktionen prüft und Befunde mit Datei und Zeile sammelt"

key-files:
  created:
    - tests/unit/test_errors_reason.py
  modified:
    - src/mcp_connector/errors.py
    - src/mcp_connector/nextcloud/clients/ocs.py
    - src/mcp_connector/nextcloud/clients/dav.py
    - src/mcp_connector/nextcloud/clients/caldav.py
    - src/mcp_connector/nextcloud/clients/carddav.py
    - src/mcp_connector/tools/talk.py
    - src/mcp_connector/paging.py
    - src/mcp_connector/ids.py
    - vulture_whitelist.py

key-decisions:
  - "Der AST-Lauf prüft nur reason=-Argumente an Fehlerkonstruktionen, nicht jedes Schlüsselwort namens reason: audit/store.py baut ein Entry mit reason=row[11], und dieser Wert kommt zur Laufzeit aus einer Datei und kann nie eine Modulkonstante sein"
  - "Zwölf statt der im Plan erwarteten sieben bis zehn Zeilen: dav, caldav und carddav führen je einen Schreib- und einen Lesepfad, und der Plan zählt Funktionen, der Test zählt Zweige"
  - "Alle vierzehn Wurfstellen von ids.py und alle sieben von paging.py bekommen die Kennung, nicht nur die im Test geprüften: die Aussage ist modulweit und ein einzelner ungesetzter Zweig wäre eine stille Ausnahme"
  - "REASONS steht als geparkter Name in vulture_whitelist.py und verlässt die Liste mit Plan 18-06"

requirements-completed: []
# AUDIT-01 bleibt Pending: der Satzteil "Jeder Werkzeugaufruf erzeugt einen Eintrag" wird erst
# vom Rekorder in Plan 18-06 wahr. Fertig ist hier der Grund, den D-07 zum Ablesen verlangt.
requirements-advanced: [AUDIT-01]

# Metrics
duration: 25min
completed: 2026-08-29
---

# Phase 18 Plan 03: Ablehnungskennungen an ToolError Summary

**`ToolError` trägt ein reines Schlüsselwortargument `reason` mit sechs eingefrorenen Kennungen, gesetzt an zwölf Statuszweigen der vier Client-Dateien und an den drei Sicherungsorten dieses Servers, gehalten von einem AST-Lauf, der eine Zeichenkette an dieser Stelle mit Datei und Zeile rot macht.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-29T09:00:00Z
- **Completed:** 2026-08-29T09:25:00Z
- **Tasks:** 3
- **Files modified:** 10 (1 neu, 9 geändert)

## Accomplishments

- `errors.py` trägt die sechs Kennungen mit je einer Zeile, die den auslösenden Fall nennt, dazu `REASONS` als eingefrorene Menge mit der Begründung, dass eine siebte Kennung ein Entscheid ist und in ein Review gehört, nicht in einen Diff.
- Der Modul-Docstring zieht die Grenze aus T-18-01 ausdrücklich: die Kennung ist das Einzige, was aus einem Fehler in ein Protokoll wandern darf; `message` und `hint` sind für das Modell geschrieben und nennen Pfade, Kalendernamen und Kennungen.
- Zwölf Statuszweige über `ocs.py`, `dav.py`, `caldav.py` und `carddav.py` setzen die Kennung: sechs mal `REASON_PERMISSION_DENIED` (403), sechs mal `REASON_UNKNOWN_ID` (404, 409, 998). Jeder andere Status bleibt ohne Kennung und liest sich damit als `unspecified`.
- Kein einziger Satz einer Werkzeugantwort hat sich geändert: `git diff -U0 src/mcp_connector/nextcloud/clients/ | grep '^[-+]' | grep -c 'message=\|hint='` meldet 0.
- Die drei Sicherungsorte sagen `guard_tripped`: der Talk-Sendeschalter, die sieben Wurfstellen der Handhabungsprüfung in `paging.py` und die vierzehn Wurfstellen der Kennungsprüfung in `ids.py`.
- Die rund 223 übrigen Wurfstellen sind unberührt (D-17) und tragen ehrlich `unspecified` statt eines geratenen Grundes.

## Task Commits

1. **Task 1: ToolError bekommt reason, die sechs Kennungen werden eingefroren** - `5d31b85` (feat)
2. **Task 2: Die Statusabbildungen setzen ihre Kennung** - `93be17a` (feat)
3. **Task 3: guard_tripped an den drei Sicherungsorten, Menge eingefroren** - `8e0d910` (test, RED) und `bb5dc72` (feat, GREEN)

## Files Created/Modified

- `src/mcp_connector/errors.py` - sechs `REASON_*`-Konstanten, `REASONS`, `reason` als reines Schlüsselwortargument, Absatz im Modul-Docstring zur Grenze
- `src/mcp_connector/nextcloud/clients/ocs.py` - `_status_error` mit dem zweiteiligen Begründungs-Docstring, auf den die drei DAV-Geschwister verweisen, plus zwei Zweige
- `src/mcp_connector/nextcloud/clients/dav.py` - vier Zweige (Schreibpfad und Lesepfad)
- `src/mcp_connector/nextcloud/clients/caldav.py` - vier Zweige (Schreibpfad und Lesepfad)
- `src/mcp_connector/nextcloud/clients/carddav.py` - zwei Zweige
- `src/mcp_connector/tools/talk.py` - der Sendeschalter mit `REASON_GUARD_TRIPPED`
- `src/mcp_connector/paging.py` - sieben Wurfstellen plus ein Kommentar, warum sie alle dieselbe Kennung tragen
- `src/mcp_connector/ids.py` - vierzehn Wurfstellen plus derselbe Kommentar auf Modulebene
- `tests/unit/test_errors_reason.py` - fünf Fälle: vier Verhaltensfälle und der AST-Lauf
- `vulture_whitelist.py` - `REASONS` als geparkter Name mit Begründung und Ausstiegsplan (Plan 18-06)

## Zählung der Treffer

```
grep -rn "reason=REASON_PERMISSION_DENIED" src/mcp_connector/nextcloud/clients/ | wc -l   ->  6
grep -rn "reason=REASON_UNKNOWN_ID"        src/mcp_connector/nextcloud/clients/ | wc -l   ->  6
grep -rn "reason=REASON_"                  src/mcp_connector/nextcloud/clients/ | wc -l   -> 12
```

Der Plan erwartete sieben bis zehn Zeilen. Zwölf ist keine übersehene und keine zu viel
angefasste Stelle, sondern der Unterschied zwischen Funktionen und Zweigen: `dav.py`,
`caldav.py` und `carddav.py` führen je einen Schreib- und einen Lesepfad, und jeder von ihnen
hat einen eigenen 403- und einen eigenen 404-Zweig. Die Aufstellung, jede Zeile einzeln
nachgelesen:

| Datei | 403 | 404 / 409 / 998 |
|-------|-----|-----------------|
| `ocs.py::_status_error` | 1 | 1 (404, 998) |
| `dav.py::_check_write` | 1 | 1 (404, 409) |
| `dav.py::_check` | 1 | 1 |
| `caldav.py::_check_write` | 1 | 1 (404, 409) |
| `caldav.py::_check` | 1 | 1 |
| `carddav.py::_check` | 1 | 1 |

Die Prüfung des Plans (`[4-9]` je Kennungsart) ist damit erfüllt: sechs und sechs.

## Gegenprobe (Nachweis, dass der AST-Lauf wirklich hält)

Von Hand geführt: in `src/mcp_connector/paging.py` wurde `reason=REASON_GUARD_TRIPPED` durch
`reason="tippfehler"` ersetzt.

```
FAILED tests/unit/test_errors_reason.py::test_every_reason_under_src_is_one_of_the_frozen_constants
E       AssertionError: a literal at reason= bypasses the frozen set of errors.REASONS, and a
        seventh reason is a decision that belongs into a review and not into a diff:
E         paging.py:51: reason= is not a REASON_* constant
```

Der Fehlertext nennt Datei und Zeile, nicht nur die Tatsache. Danach zurückgenommen (kein
`git stash`, kein `git clean`); `grep -n "tippfehler" src/mcp_connector/paging.py` findet
nichts mehr, und `git status --short` war vor dem Task-3-Commit sauber bis auf die geplanten
Dateien.

## Decisions Made

- **Der AST-Lauf prüft Fehlerkonstruktionen, nicht jedes Schlüsselwort namens `reason`:** Der erste Entwurf sammelte jedes `ast.keyword` mit `arg == "reason"` und wurde sofort rot bei `audit/store.py:351`, wo `_entry_of_row` ein `Entry(reason=row[11], ...)` baut. Das ist die Spalte des Logs, gefüllt aus einer gelesenen Zeile, und kann per Konstruktion nie eine Modulkonstante sein. `_is_an_error_construction` grenzt auf Aufrufe ein, deren Name auf `Error` endet, plus `IssuerRefused` als die eine Fehlerklasse dieses Pakets ohne diese Endung. Damit trifft der Lauf genau das, was die eingefrorene Menge regiert, und der Rekorder aus Plan 18-06 kann `getattr(exc, "reason", ...)` an ein `Entry` reichen, ohne dieses Gate zu brechen.
- **Modulweite statt punktueller Kennung in `paging.py` und `ids.py`:** Der Test prüft vier Wurfstellen, gesetzt sind alle einundzwanzig. Eine Sicherung, die je nach Zweig mal `guard_tripped` und mal `unspecified` meldete, wäre im Log nicht lesbar, und der ungesetzte Zweig wäre eine stille Ausnahme ohne Begründung. Der Grund steht als Kommentar in beiden Modulen.
- **`pytest.mark.anyio` statt `pytest.mark.asyncio`:** Dieses Projekt fährt seine asynchronen Fälle über den `anyio_backend`-Fixture aus `tests/conftest.py`. Der erste Entwurf nutzte die andere Marke und lief als Warnung stumm durch, statt den Talk-Schalter wirklich aufzurufen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der AST-Lauf traf die Spalte `reason` des Logs mit**

- **Found during:** Task 3 (RED-Lauf von `tests/unit/test_errors_reason.py`)
- **Issue:** Der im Plan beschriebene Lauf ("sammle jedes `ast.keyword` mit `arg == 'reason'`") meldete `audit/store.py:351` als Verstoss. Dort baut `_entry_of_row` ein `Entry` mit `reason=row[11]`: der Wert kommt aus einer SQLite-Zeile und ist ein `ast.Subscript`, also weder `Name` noch `Attribute`. Der Fall wäre dauerhaft rot gewesen, und schlimmer: er hätte den Rekorder aus Plan 18-06 blockiert, der genau so einen Laufzeitwert an ein `Entry` reicht.
- **Fix:** `_is_an_error_construction` grenzt den Lauf auf Aufrufe ein, deren Callee-Name auf `Error` endet oder in `_ERROR_CLASSES_WITHOUT_THE_SUFFIX` steht (`IssuerRefused`). Der Grund steht als Docstring an der Hilfe.
- **Files modified:** tests/unit/test_errors_reason.py
- **Verification:** Der Fall ist grün, und die Gegenprobe oben belegt, dass er trotzdem hält: eine Zeichenkette an einem `ToolError` macht ihn rot und nennt Datei und Zeile.
- **Committed in:** `8e0d910` (RED-Commit)

**2. [Rule 3 - Blocking] Der Dead-Code-Gate wurde durch `REASONS` rot**

- **Found during:** Task 3 (Verifikation `vulture src scripts vulture_whitelist.py`)
- **Issue:** `REASONS` hat noch keinen Leser im Produktionscode; sein Leser ist der Rekorder aus Plan 18-06, der eine unbekannte Kennung ablehnt. Vulture läuft in diesem Projekt auf voller Vertrauensstufe und meldete den Namen als unbenutzte Variable (60 %), Exit-Code 3.
- **Fix:** Ein Block in `vulture_whitelist.py` nach dem dort etablierten Muster der geparkten Namen, mit Begründung, dem heutigen Leser (`tests/unit/test_errors_reason.py`) und dem Plan, mit dem der Eintrag wieder verschwindet.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `bb5dc72` (Task-3-Commit)

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 Blocking)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 rettet den AST-Fall des Plans und hält den Weg für Plan 18-06 frei, Abweichung 2 hält ein bestehendes Gate grün und ist mit demselben Plan wieder abgebaut.

## Issues Encountered

- Der Plan nennt "die sieben Statusabbildungen" (Funktionen aus der Recherche) und erwartet zugleich sieben bis zehn Zeilen. Gesetzt sind zwölf Zeilen in sechs Funktionen, weil jede Funktion einen 403- und einen 404-Zweig führt. Die Tabelle oben stellt beide Zählungen nebeneinander, damit die Doppeldeutigkeit nicht wiederkommt.
- `REASON_TIMEOUT` und `REASON_UNREACHABLE` werden in diesem Plan von keiner Wurfstelle gesetzt, und das ist so gedacht: `graceful` liest sie in Plan 18-06 direkt aus `httpx.TimeoutException` beziehungsweise `httpx.RequestError`, weil dort keine `ToolError`-Instanz entsteht. Beide stehen deshalb schon jetzt in der eingefrorenen Menge, damit der Rekorder sie nicht nachträglich hinzufügen muss.
- Der Talk-Fall ruft `talk.send(None, ...)` auf: der Schalter ist die erste Anweisung der Funktion, also erreicht der Aufruf keinen Client. Das ist der einzige Weg, den Schalter als Verhalten zu prüfen statt als Textfund im Quelltext.

## Anforderungen

AUDIT-01 bleibt in `REQUIREMENTS.md` ausdrücklich **Pending**. Dieser Plan liefert den Grund,
den D-07 zum Ablesen verlangt, aber der Satzteil "Jeder Werkzeugaufruf erzeugt einen Eintrag"
wird erst wahr, wenn der Rekorder in Plan 18-06 schreibt. Ein Haken hier wäre die Art von
Aussage, die dieses Projekt bei EXAPP-10 und TABLES-01 schon einmal bewusst zurückgehalten
hat.

## TDD Gate Compliance

Task 3 hat die volle Folge: `8e0d910` (`test`, drei Verhaltensfälle rot, der AST-Fall bereits
grün) vor `bb5dc72` (`feat`, alle fünf grün). Ein REFACTOR-Commit war nicht nötig. Die Tasks 1
und 2 sind im Plan nicht als `tdd="true"` geschnitten und tragen deshalb keinen `test`-Commit;
ihre Behauptungen sind in demselben `test`-Commit mit abgedeckt
(`test_any_other_raise_site_stays_honestly_unspecified` für Task 1,
`test_every_reason_under_src_is_one_of_the_frozen_constants` für Task 2).

## Threat Flags

Keine. Dieser Plan legt keine Route an, öffnet keinen Netzzugang, ändert kein Schema und
verlangt keine neue Berechtigung. `git status --short appinfo/ pyproject.toml uv.lock` ist
leer (T-18-SC).

## Known Stubs

Keine. Die Kennungen sind gesetzt, der Test hält sie, und der einzige bewusst offene Punkt ist
der Leser der Menge: er entsteht als Rekorder in Plan 18-06 und ist dort als geparkter Name in
`vulture_whitelist.py` festgehalten.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract` — 2830 passed
- `uv run --no-sync ruff check .` — All checks passed
- `uv run --no-sync ruff format --check .` — 208 files already formatted
- `uv run --no-sync pyright` — 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`
- `git status --short appinfo/ pyproject.toml uv.lock` — leer

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-06 kann `getattr(exc, "reason", REASON_UNSPECIFIED)` lesen und den Wert gegen `REASONS` prüfen, bevor er in die Spalte `reason` einer Zeile geht; der AST-Lauf lässt diesen Weg ausdrücklich zu.
- `REASON_TIMEOUT` und `REASON_UNREACHABLE` warten dort auf ihren Setzer in `graceful`, wo `httpx.TimeoutException` und `httpx.RequestError` ankommen und keine `ToolError` entsteht.
- `REASONS` verlässt `vulture_whitelist.py` mit demselben Plan.
- Eine siebte Kennung ist ab jetzt nicht mehr still einführbar: sie muss in `errors.REASONS`, und eine Zeichenkette an `reason=` macht den AST-Fall rot.

## Self-Check: PASSED

`tests/unit/test_errors_reason.py` liegt auf der Platte, alle acht geänderten Quelldateien
ebenfalls, und alle vier Task-Commits stehen im Log (`5d31b85`, `93be17a`, `8e0d910`,
`bb5dc72`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
