---
phase: 18-audit-log-kern
plan: 02
subsystem: audit
tags: [audit-log, allowlist, contract-test, gate, tool-surface, privacy]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "das Paket src/mcp_connector/audit/ als Ort für die Erlaubnisliste"
  - phase: 01
    provides: "die Werkzeugoberfläche über Client(mcp).list_tools() und das Muster des Budget-Gates (scripts/check_tool_budget.py, tests/contract/test_tool_surface.py)"
provides:
  - "src/mcp_connector/audit/allowlist.py: PARAM_ALLOWLIST mit genau 21 Einträgen, je Werkzeug ein frozenset erlaubter Parameternamen"
  - "FORBIDDEN_PARAMS: die sieben Nutzlastnamen, die niemals in einer Erlaubnisliste stehen dürfen"
  - "tests/contract/test_audit_surface.py: vier Fälle als Messung über alle registrierten Werkzeuge"
affects: [18-06, 18-07, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Erlaubnisliste als reine Daten ohne Funktion und ohne Projektimport (nur collections.abc)"
    - "Grossbuchstaben-Zwang für Modulkonstanten aus dem Modulzustands-Gate (target.id.isupper())"
    - "Gate-Form: Messung über alle Werkzeuge, Befunde sammeln, findings == [] mit benanntem Treffer"

key-files:
  created:
    - src/mcp_connector/audit/allowlist.py
    - tests/contract/test_audit_surface.py
  modified:
    - vulture_whitelist.py

key-decisions:
  - "Der Vergleich läuft gegen die Namen der obersten Schemaebene, nicht gegen den verschachtelten Durchlauf von test_tool_surface.py: nur die obersten properties können Schlüssel der Argumente eines Aufrufs sein, ein Feld unter $defs kann nie als Argumentname ankommen"
  - "Die Vollständigkeit prüft in beide Richtungen (Werkzeug ohne Eintrag und Eintrag ohne Werkzeug), weil ein Eintrag auf ein gelöschtes Werkzeug genauso still falsch wäre wie ein fehlender"
  - "Der vierte Fall ist die Gegenprobe zur Sperrliste: mindestens ein Name aus FORBIDDEN_PARAMS muss in der gemessenen Fläche vorkommen, sonst hielte die Sperrliste nichts und der dritte Fall bestünde aus dem falschen Grund"
  - "Der Dekorator-Nachweis aus D-04 bleibt bewusst aus dieser Datei; der Modul-Docstring sagt, dass der Marker mit Plan 18-06 kommt und seinen Fall dann hier bekommt"

requirements-completed: []
# AUDIT-01 bleibt Pending: der Satzteil "Jeder Werkzeugaufruf erzeugt einen Eintrag" wird erst
# vom Rekorder in Plan 18-06 wahr. Fertig ist hier die zweite Hälfte der Anforderung
# (Erlaubnisliste je Werkzeug plus Vertragstest nach dem Muster des Budget-Gates).
requirements-advanced: [AUDIT-01]

# Metrics
duration: 15min
completed: 2026-08-29
---

# Phase 18 Plan 02: Erlaubnisliste und Vertragstest Summary

**Eine Erlaubnisliste je Werkzeug (21 Einträge, nur Namen, nie Werte) und ein Vertragstest, der sie in vier Fällen gegen die gemessene Werkzeugfläche aller 21 Werkzeuge hält, samt Gegenprobe zur Sperrliste.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-29T08:30:00Z
- **Completed:** 2026-08-29T08:45:00Z
- **Tasks:** 2
- **Files modified:** 3 (2 neu, 1 geändert)

## Accomplishments

- `audit/allowlist.py` steht als reine Daten da: kein Import ausser `collections.abc`, keine Funktion, kein Projektmodul. `PARAM_ALLOWLIST` trägt genau 21 Schlüssel, keiner mit einer leeren Menge.
- `FORBIDDEN_PARAMS` nennt die sieben Nutzlastnamen (`content`, `description`, `location`, `message`, `summary`, `title`, `values`) mit der Begründung, warum die Nennung eines solchen Namens keine Auskunft trägt und nur die Stelle wäre, an der eines Tages ein Wert danebenwächst.
- `tests/contract/test_audit_surface.py` misst über alle registrierten Werkzeuge, nicht über eine Stichprobe, und benennt jeden Treffer als `werkzeug.name` statt nur die Tatsache eines Treffers.
- Nichts wird am Modulsingleton `mcp` registriert (Falle 9): `tests/contract/test_tool_surface.py` mit seinem eingefrorenen Literal und `len(tools) == 21` bleibt unberührt.
- Die Werkzeugoberfläche ist unverändert: `scripts/check_tool_budget.py` meldet weiterhin 15712 Bytes über 21 Werkzeuge bei einem Budget von 18000.

## Task Commits

1. **Task 1: audit/allowlist.py mit Erlaubnisliste und Sperrliste** - `354f3fb` (feat), enthält den Nachzug in `vulture_whitelist.py`
2. **Task 2: Vertragstest über alle Werkzeuge** - `b792133` (test)

## Files Created/Modified

- `src/mcp_connector/audit/allowlist.py` - `PARAM_ALLOWLIST` (21 Werkzeuge) und `FORBIDDEN_PARAMS` (7 Namen), Modul-Docstring mit der Grenze: Namen ja, Werte nie
- `tests/contract/test_audit_surface.py` - vier Fälle plus zwei Hilfen (`_argument_names`, `_measured_surface`), Modul-Docstring mit T-18-01, T-18-02 und dem Verweis auf AUDIT-01
- `vulture_whitelist.py` - beide Listen als geparkte Namen mit Begründung und Ausstiegsplan (Plan 18-06)

## Gegenproben (Nachweis, dass der Gate wirklich hält)

Alle vier von Hand geführt, jeweils gegen eine geänderte Kopie der Erlaubnisliste, danach mit
`git checkout -- src/mcp_connector/audit/allowlist.py` zurückgenommen (kein `git stash`, kein
`git clean`):

| Eingriff | Roter Fall | Fehlertext |
|----------|-----------|------------|
| Zeile `"notes_read": ...` entfernt | `test_every_registered_tool_has_an_allowlist_entry` | `... nobody made: notes_read has no allowlist entry` |
| `"not_a_parameter"` zu `files_read` ergänzt | `test_no_allowlisted_name_is_absent_from_its_own_schema` | `... reads this list by hand: files_read.not_a_parameter` |
| `"content"` zu `files_upload` ergänzt | `test_no_allowlisted_name_is_on_the_block_list` | `... a value grows next to one day: files_upload.content` |
| `FORBIDDEN_PARAMS` auf leer gesetzt | `test_the_block_list_names_parameters_that_really_exist` | `no name of FORBIDDEN_PARAMS occurs in the measured tool surface ...` |

Jeder Fehlertext nennt den Treffer, nicht nur die Tatsache. Nach den Gegenproben meldete
`git status --short` nur die noch nicht eingecheckte Testdatei.

## Decisions Made

- **Oberste Schemaebene statt verschachteltem Durchlauf:** `_argument_names` liest nur `schema["properties"]`. Der verschachtelte Durchlauf `_properties` aus `test_tool_surface.py` sucht nach einem *verbotenen* Namen irgendwo im Schema, und dafür ist er richtig. Hier wird verglichen, was als Argumentschlüssel ankommen kann, und ein Feld unter `$defs` kann das nie. Der Grund steht als Docstring an der Hilfe.
- **Vollständigkeit in beide Richtungen:** Der erste Fall meldet auch einen Eintrag, zu dem kein Werkzeug mehr gehört. Ein Mengenvergleich in nur einer Richtung liesse eine Erlaubnisliste für ein entferntes Werkzeug still stehen.
- **Zwei Fälle asynchron, einer nicht:** `test_no_allowlisted_name_is_on_the_block_list` braucht die Werkzeugfläche nicht und läuft deshalb ohne `Client`. Das ist keine Sparsamkeit, sondern eine Aussage: die Behauptung "kein Verräter in der Liste" gilt unabhängig davon, was registriert ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Dead-Code-Gate wurde durch die beiden neuen Listen rot**
- **Found during:** Task 1 (Verifikation `vulture src scripts vulture_whitelist.py`)
- **Issue:** `PARAM_ALLOWLIST` und `FORBIDDEN_PARAMS` haben noch keinen Leser im Produktionscode; ihr Leser ist der Rekorder aus Plan 18-06. Vulture läuft in diesem Projekt auf voller Vertrauensstufe und meldete beide als unbenutzte Variablen (60 %), Exit-Code 3.
- **Fix:** Ein Block in `vulture_whitelist.py` nach dem dort etablierten Muster der geparkten Namen, mit Begründung, dem heutigen Leser (`tests/contract/test_audit_surface.py`) und dem Plan, mit dem der Eintrag wieder verschwindet.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `354f3fb` (Task-1-Commit)

---

**Total deviations:** 1 auto-fixed (1 Blocking)
**Impact on plan:** Keine Erweiterung des Auftrags. Die Abweichung hält ein bestehendes Gate grün und ist mit Plan 18-06 wieder abgebaut.

## Issues Encountered

- Die TDD-Reihenfolge dieses Plans ist eine andere als sonst: Task 1 legt die Daten an, Task 2 den Gate, der sie hält. Ein RED-Lauf vor Task 1 hätte nur einen Importfehler gezeigt, keine Behauptung. Die eigentliche RED-Prüfung sind deshalb die vier Gegenproben oben, die jede Behauptung einzeln rot gemacht haben; sie stehen an der Stelle, an der sonst der `test(...)`-Commit vor dem `feat(...)`-Commit stünde.
- `mail_browse` hat mit sechs Namen die längste Erlaubnisliste; `filter` ist dabei bewusst enthalten, weil der Wert nicht erscheint und die Auskunft "es wurde gefiltert" keinen Inhalt verrät.

## Anforderungen

AUDIT-01 bleibt in `REQUIREMENTS.md` ausdrücklich **Pending**, obwohl die Plan-Frontmatter sie
nennt. Der erste Satzteil der Anforderung ("Jeder Werkzeugaufruf erzeugt einen Eintrag mit
Nutzer, Werkzeugname, Zeitpunkt, aufrufendem Client und Ergebnisstatus") wird erst wahr, wenn
der Rekorder in Plan 18-06 schreibt. Fertig ist die zweite Hälfte: die Erlaubnisliste je
Werkzeug und der Vertragstest, der die Grenze nach dem Muster des Budget-Gates hält.

## TDD Gate Compliance

Kein `feat(...)`-Commit nach dem `test(...)`-Commit, und das ist hier richtig herum: der Plan
schneidet Task 1 (Daten) vor Task 2 (Gate). Die RED-Belege stehen im Abschnitt "Gegenproben".

## Threat Flags

Keine. Die Plan-Dateien erzeugen keine Route, keinen Netzzugang, kein Schema und keine neue
Berechtigung. `pyproject.toml` und `uv.lock` sind unverändert (T-18-SC).

## Known Stubs

Keine. Beide Dateien sind vollständig; der einzige bewusst offene Punkt ist der
Dekorator-Nachweis aus D-04, der laut Plan ausdrücklich nicht hierher gehört und in Plan 18-06
in dieselbe Datei kommt.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract` — 2825 passed
- `uv run --no-sync ruff check .` / `ruff format --check .` — grün (207 Dateien)
- `uv run --no-sync pyright` — 0 errors, 0 warnings
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-06 kann `PARAM_ALLOWLIST` beim Schneiden der gesetzten Argumentschlüssel verwenden und den Marker aus D-04 setzen; sein Fall gehört in `tests/contract/test_audit_surface.py`, der Docstring dort sagt das bereits.
- Beide Namen verlassen `vulture_whitelist.py` mit demselben Plan.
- Ein neues Werkzeug ist ab jetzt ohne Eintrag in der Erlaubnisliste nicht mehr mergefähig: der erste Fall wird rot und nennt seinen Namen.

## Self-Check: PASSED

Beide neuen Dateien liegen auf der Platte
(`src/mcp_connector/audit/allowlist.py`, `tests/contract/test_audit_surface.py`), beide
Task-Commits stehen im Log (`354f3fb`, `b792133`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
