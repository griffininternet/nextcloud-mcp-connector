---
phase: 18-audit-log-kern
plan: 06
subsystem: audit
tags: [audit-log, decorator, fail-open, contract-gate, privacy, tdd]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "AuditStore, Entry, user_chain, should_sweep, sweep, CLIENT_NAME_LIMIT und AUDIT_STATE_ATTR"
  - phase: 18
    plan: 02
    provides: "PARAM_ALLOWLIST als der Schnitt, mit dem die gesetzten Argumentnamen beschnitten werden, und die Datei, in die der Dekorator-Nachweis gehört"
  - phase: 18
    plan: 03
    provides: "ToolError.reason, die sechs Kennungen und REASONS als eingefrorene Menge"
  - phase: 18
    plan: 04
    provides: "sweep(moment=..., retention_days=..., size_limit=...) und should_sweep auf der zurückgegebenen Nummer"
  - phase: 18
    plan: 05
    provides: "deps.resolve_caller, Caller mit vier Feldern ohne Geheimnis und die Ablage des Rekorders in der Anfrage"
provides:
  - "audit/record.py: Recorder (frozen, vier Felder), note(), note_switch(), set_parameter_names()"
  - "server.graceful setzt outcome und reason in vier Zweigen und schreibt eine Zeile im finally"
  - "__mcp_audited__: der ausdrückliche Marker, an dem der Vertragstest jedes Werkzeug misst"
  - "SWITCH_ON und SWITCH_OFF: die zwei Richtungen einer Schaltzeile (D-15)"
  - "tests/contract/test_audit_surface.py: zwei Gate-Fälle über alle 21 Werkzeuge"
affects: [18-07, 18-08, 18-09, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Erfassung im vorhandenen Dekorator statt in einer Middleware (D-04), mit einem await im finally-Zweig, der nie wirft"
    - "Ausdrücklicher Marker auf dem Wrapper statt einer Namensprüfung auf der inneren Funktion"
    - "Die gesetzten Parameternamen kommen aus params['arguments'].keys(), nie aus kwargs (Falle 1)"
    - "Fail-open mit dem Ausnahmetyp allein im Log, nach dem Muster von exapp/purge.py (D-13)"

key-files:
  created:
    - src/mcp_connector/audit/record.py
    - tests/unit/test_audit_record.py
  modified:
    - src/mcp_connector/server/__init__.py
    - tests/contract/test_audit_surface.py
    - vulture_whitelist.py

key-decisions:
  - "Der Rekorder baut den defensiven Lesevorgang der Anfrage in drei Zeilen nach, statt deps._request_of zu importieren: ein Name mit führendem Unterstrich ist ein Versprechen, das sein Besitzer zurücknehmen darf"
  - "note() prüft die Kennung gegen errors.REASONS, bevor sie in eine Spalte geht; alles andere wird zum ehrlichen unspecified statt zu Freitext"
  - "note_switch() lässt einen Fehlschlag durch, anders als note(): eine Schaltung ist eine Verwaltungshandlung mit eigener Antwort und kein Werkzeugaufruf, der seine eigene Buchführung überleben muss"
  - "Der Marker heisst __mcp_audited__ und wird ausdrücklich gesetzt; fn.__code__.co_name == 'wrapper' liesse jeden Dekorator der Welt durch"
  - "FORBIDDEN_PARAMS bleibt dauerhaft in vulture_whitelist.py: der Rekorder liest die Erlaubnisliste, nicht die Sperrliste, und die Korrektur des Ausstiegsplans aus 18-02 steht dort"

patterns-established:
  - "Ein await im finally-Zweig ist nur zulässig, wenn die gerufene Funktion nachweislich nicht wirft; der Nachweis ist ein Testfall mit einem Doppelgänger, der immer wirft"
  - "Eine Wertsuche über alle Spalten der geschriebenen Zeile, nicht nur über die Spalte, in der der Wert erwartet würde"

requirements-completed: []
# AUDIT-01 bleibt Pending: der Eintrag entsteht, aber niemand baut in der Produktion einen
# Recorder und reicht ihn an RequireAppApi weiter; das ist der Schalter aus D-14 in Plan 18-07.
requirements-advanced: [AUDIT-01, AUDIT-02]

# Metrics
duration: 28min
completed: 2026-08-29
---

# Phase 18 Plan 06: Erfassungspunkt und Rekorder Summary

**`graceful` trägt jetzt einen Marker und einen `finally`-Zweig, und daneben steht ein Rekorder, der eine Zeile je Aufruf schreibt, nie einen Wert kennt und nie wirft; ein Vertragstest hält über alle 21 Werkzeuge fest, dass keines daran vorbeikommt.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-08-29T09:05:00Z
- **Completed:** 2026-08-29T09:33:00Z
- **Tasks:** 3
- **Files modified:** 5 (2 neu, 3 geändert)

## Accomplishments

- `audit/record.py` steht ohne einen einzigen Import aus `..server` oder `..exapp`: der Ringschluss und die Schichtverletzung sind beide durch die Verifikation belegt, und die Klammerung des Client-Namens ist in fünf Zeilen nachgebaut statt aus `exapp/ui/layout.py` geholt (Falle 8, T-18-08).
- `set_parameter_names` liest ausschliesslich `params["arguments"].keys()` und schneidet mit `PARAM_ALLOWLIST`. `grep -c "\.values()" src/mcp_connector/audit/record.py` meldet 0. Der Testfall mit gesetztem `path` und ungesetztem `limit` beweist, warum `kwargs` die falsche Quelle wäre: der Aufruf im Test übergibt `limit=25` genauso, wie das SDK es tut, und die Zeile trägt trotzdem nur `["path"]`.
- `note` hat genau einen `except Exception`-Zweig, der `type(exc).__name__` protokolliert. Der Fail-open-Fall behauptet drei Dinge auf einmal: die Antwort des Werkzeugs kommt an, es fliegt keine Ausnahme, und die eine Logzeile nennt `OSError` und weder die Meldung noch den Pfad darin.
- `graceful` setzt `outcome` und `reason` in vier Zweigen und schreibt im `finally` genau eine Zeile. Die drei bestehenden Fehlertexte sind Wort für Wort unverändert: `git diff -U0 src/mcp_connector/server/__init__.py | grep "^-" | grep -c "Hint:"` meldet 0, und `from None` ist unangetastet.
- Die Werkzeugfläche hat sich um kein Byte bewegt: vor der Änderung `tools/list: 15712 bytes, 21 tools, budget 18000`, nach der Änderung dieselbe Zeile.
- Alle 21 Werkzeuge tragen `__mcp_audited__ is True`, und `tool.name == tool.fn.__name__` gilt für alle 21, damit die zwei Wege zum Werkzeugnamen nicht auseinanderlaufen.
- Drei geparkte Namen haben `vulture_whitelist.py` mit dem Plan verlassen, der sie ruft: `_.sweep`, `PARAM_ALLOWLIST` und `REASONS`.

## Task Commits

1. **Task 1: audit/record.py, der Rekorder, der nie wirft** - `bebb522` (feat)
2. **Task 2: graceful bekommt den Marker und den finally-Zweig** - `6f5e033` (feat)
3. **Task 3: Rekorder-Tests und der Dekorator-Nachweis im Gate** - `84b0788` (test)

## Files Created/Modified

- `src/mcp_connector/audit/record.py` - `Recorder`, `note`, `note_switch`, `set_parameter_names`, `_clamped_client_name`, `_recorder_of`, `_tool_name`, `_known_reason`; Modul-Docstring mit der Aufzählung dessen, was nie in eine Zeile darf
- `src/mcp_connector/server/__init__.py` - `started`, `ctx`, `outcome`/`reason` in vier `except`-Zweigen, der `finally`-Zweig, der Marker und der Erfassungsabsatz im Docstring von `graceful`
- `tests/unit/test_audit_record.py` - zehn Fälle gegen eine echte Ablage in `tmp_path`, jeder Zeilenlesevorgang mit einer eigenen `sqlite3`-Verbindung an der Ablage vorbei
- `tests/contract/test_audit_surface.py` - zwei Gate-Fälle plus die Gegenprobe ohne Registrierung; der Docstring nennt jetzt den Marker statt ihn anzukündigen
- `vulture_whitelist.py` - drei Namen entfernt, ein Name (`__mcp_audited__`) dauerhaft ergänzt, der Ausstiegsplan von `FORBIDDEN_PARAMS` korrigiert

## Gegenproben (Nachweis, dass die Gates wirklich halten)

Alle drei von Hand geführt und mit `git checkout -- <datei>` zurückgenommen (kein `git stash`,
kein `git clean`):

| Eingriff | Roter Fall | Fehlertext |
|----------|-----------|------------|
| `@graceful` an `files_search` entfernt | `test_every_registered_tool_carries_the_recording_marker` | `... sees every call with its outcome (D-04): files_search` |
| `set_parameter_names` gibt Namen **und** Werte zurück | drei Fälle: die zwei Namensfälle und die Wertsuche | `assert '["/notes","path"]' == '["path"]'` und `a parameter value reached a column of the entry:` |
| `logger.error(..., exc)` statt `type(exc).__name__` | `test_a_store_that_cannot_write_costs_the_call_nothing` | `assert 'OSError' in '... no space left on device: /var/lib/mcp_connector/audit.sqlite3'` |

Der erste Eingriff ist die vom Plan verlangte Gegenprobe: ein Werkzeug vorübergehend ohne
`@graceful`, Test rot mit dem Namen des Werkzeugs, Änderung zurückgenommen. Danach meldete
`grep -c "@graceful" src/mcp_connector/server/reg_files.py` wieder 4.

## Decisions Made

- **Der Rekorder baut den defensiven Lesevorgang nach, statt `deps._request_of` zu importieren.** Plan 18-05 stellt diese Hilfe als gemeinsamen Lesevorgang bereit, aber ihre beiden heutigen Leser stehen beide in `deps.py`. Ein Modul mit führendem Unterstrich über eine Paketgrenze hinweg zu rufen wäre dieselbe Art Kopplung, die dieses Repository sich mit `tests/contract/test_module_boundaries.py` verboten hat, und der Gewinn wären drei Zeilen. Der Grund steht im Docstring von `_recorder_of`.
- **Die Kennung wird gegen `REASONS` geprüft.** Der Wert kommt über `getattr(exc, "reason", ...)` aus einer Ausnahme, und eine Ausnahme ist nichts, was dieses Modul kontrolliert. Alles, was nicht eine der sechs Kennungen ist, wird zu `unspecified`, damit in einer Spalte ohne Freitext auch kein Freitext landet. Das ist zugleich der Leser, der `REASONS` aus der Vulture-Liste holt, genau wie Plan 18-03 es angekündigt hat.
- **`note_switch` fängt nicht.** `note` darf einen Werkzeugaufruf nicht kosten und schweigt deshalb; eine Schaltung ist eine Verwaltungshandlung mit einer eigenen Antwort, und was ein nicht geschriebener Schalteintrag für diese Antwort bedeutet, entscheidet der Aufrufer in Plan 18-07. Der Unterschied steht in beiden Docstrings.
- **`Recorder.env` trägt seinen Kommentar und keinen Whitelist-Eintrag.** Vulture meldet das Feld nicht, weil der Name im Baum an anderer Stelle gelesen wird; der Kommentar am Feld nennt Plan 18-09 (Kontoprüfung aus D-12) trotzdem als seinen Leser, so wie der Plan es verlangt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Dead-Code-Gate wurde durch den Marker rot**
- **Found during:** Task 3 (Verifikation `vulture src scripts vulture_whitelist.py`)
- **Issue:** `__mcp_audited__` wird in `server/__init__.py` gesetzt und ausschliesslich in `tests/contract/test_audit_surface.py` gelesen. Vulture läuft in diesem Projekt über `src`, `scripts` und die Whitelist, nie über `tests`, und meldete das Attribut als unbenutzt (60 %), Exit-Code 3.
- **Fix:** Ein Eintrag `_.__mcp_audited__` in `vulture_whitelist.py`. Er ist ausdrücklich **kein** geparkter Aufrufer: ein Marker bekommt per Konstruktion nie einen Produktionsleser, und das steht als Begründung dort, damit niemand später auf einen Ausstiegsplan wartet.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `84b0788` (Task-3-Commit)

**2. [Rule 1 - Bug] Der Ausstiegsplan von `FORBIDDEN_PARAMS` war falsch**
- **Found during:** Task 1 (Abbau der geparkten Namen)
- **Issue:** Der Block, den Plan 18-02 in `vulture_whitelist.py` hinterlassen hat, sagt für **beide** Listen "beide bekommen ihren Produktionsaufrufer in Plan 18-06". Für `PARAM_ALLOWLIST` stimmt das; für `FORBIDDEN_PARAMS` nicht: der Rekorder liest die Erlaubnisliste, und die Sperrliste ist die Regel, die einen Nutzlastnamen gar nicht erst in diese Erlaubnisliste lässt. Ihr einziger Leser bleibt der Vertragstest, und Vulture sieht `tests/` nicht. Ein Entfernen des Eintrags hätte den Gate rot gemacht, ein stilles Stehenlassen hätte einen falschen Ausstiegsplan konserviert.
- **Fix:** Der Block ist geteilt: `PARAM_ALLOWLIST` ist mit seinem Aufrufer verschwunden, `FORBIDDEN_PARAMS` steht mit einer eigenen Begründung da, die ausdrücklich sagt, dass dieser Name die Liste nicht mehr verlassen wird und warum.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund; `tests/contract/test_audit_surface.py` grün.
- **Committed in:** `bebb522` (Task-1-Commit)

---

**Total deviations:** 2 auto-fixed (1 Blocking, 1 Bug)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 hält ein bestehendes Gate grün und ist die Folge einer vom Plan verlangten Änderung, Abweichung 2 korrigiert eine Aussage in einer Datei, deren einzige Regel lautet, dass jeder Eintrag eine tragfähige Begründung hat.

## Issues Encountered

- Der Plan schneidet Task 3 als `tdd="true"`, aber seine Aufgabe ist ausschliesslich das Schreiben von Tests gegen die in Task 1 und Task 2 entstandene Umsetzung. Ein RED-Lauf davor hätte nur einen Importfehler gezeigt. Die eigentliche RED-Prüfung sind deshalb die drei Gegenproben oben; sie stehen an der Stelle, an der sonst der `test(...)`-Commit vor dem `feat(...)`-Commit stünde, und sie sind dieselbe Form, die Plan 18-02 für denselben Zuschnitt gewählt hat.
- `ruff` verlangte drei Formalien, die im Plan nicht stehen und keine Aussage berühren: `__all__` alphabetisch (RUF022), keine `noqa: SLF001`-Kommentare, weil die Regel in diesem Projekt gar nicht aktiv ist (RUF100), und eine Behauptung je Zeile statt einer mit `and` (PT018). Alle drei sind ohne Verhaltensänderung erledigt; der Grund für den Zugriff auf `mcp._tool_manager` steht jetzt als gewöhnlicher Kommentar über der Zeile statt als Lint-Ausnahme.

## Anforderungen

AUDIT-01 bleibt in `REQUIREMENTS.md` ausdrücklich **Pending**, obwohl die Plan-Frontmatter sie
nennt und obwohl alle drei Satzteile der Anforderung jetzt Code haben. Der Grund ist derselbe,
aus dem die Pläne 18-01 bis 18-05 ihre Anforderungen zurückgehalten haben: in einer
Installation entsteht heute keine Zeile, weil niemand in der Produktion einen `Recorder` baut
und an `RequireAppApi(audit_recorder=...)` reicht. Das ist der Schalter aus D-14, und er
entsteht in Plan 18-07. Erst dann ist "Jeder Werkzeugaufruf erzeugt einen Eintrag" eine
Aussage über eine laufende Instanz und nicht über einen Testaufruf.

AUDIT-02 bleibt Pending, weil das Prüfkommando aus Plan 18-08 fehlt.

## TDD Gate Compliance

Kein `feat(...)`-Commit nach dem `test(...)`-Commit, und das ist bei diesem Zuschnitt richtig
herum: der Plan legt die Umsetzung in Task 1 und Task 2 und die Tests in Task 3. Die
RED-Belege stehen im Abschnitt "Gegenproben", jeder mit dem Fehlertext, den der Eingriff
erzeugt hat.

## Threat Flags

Keine neue Fläche. Dieser Plan legt keine Route an, öffnet keinen Netzzugang und verlangt
keine neue Berechtigung; `git status --short appinfo/ pyproject.toml uv.lock` ist leer
(T-18-SC). Die sieben `mitigate`-Fäden des Plans sind eingelöst:

| Faden | Wo eingelöst |
|-------|--------------|
| T-18-01 | nur `.keys()`, Schnitt mit `PARAM_ALLOWLIST`, nur `reason` statt `message`; die Wertsuche über alle Spalten und die zwei Sätze der Ablehnung als eigene Behauptungen |
| T-18-02 | der Schnitt mit der Erlaubnisliste, mit eigenem Fall für den erfundenen Schlüsselnamen |
| T-18-06 | Fail-open mit einer Logzeile; die Lücke macht das Prüfkommando aus Plan 18-08 sichtbar |
| T-18-08 | `_clamped_client_name` unmittelbar vor dem Schreiben, eigene Längenkonstante, kein Import aus `exapp/ui` |
| T-18-10 | `type(exc).__name__` und nie die Meldung, geprüft an `caplog` samt der Behauptung, dass der Pfad fehlt |
| T-18-13 | `params["_meta"]` bleibt ungelesen; der Werkzeugname kommt aus `params["name"]`, die Identität aus `request.state` |
| T-18-17 | `note` fängt `Exception` selbst; der Doppelgänger, der immer wirft, ist ein Fall |

## Known Stubs

Keine. Der einzige bewusst offene Punkt ist der Aufrufer: `note_switch` und `Recorder.env`
haben bis Plan 18-07 beziehungsweise 18-09 keinen Produktionsleser, beide stehen mit ihrem
Grund im Code, und beide brauchen keinen Whitelist-Eintrag.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract -q` — grün
- `uv run --no-sync pytest -m matrix -q` — grün (8 Fälle)
- `uv run --no-sync ruff check .` / `ruff format --check .` — grün (211 Dateien)
- `uv run --no-sync pyright` — 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`, vor und nach der Änderung dieselbe Zeile
- `git status --short appinfo/ pyproject.toml uv.lock` — leer

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-07 findet `Recorder`, `note_switch(store, enabled=..., moment=...)`, `SWITCH_ON`/`SWITCH_OFF` und den Konstruktorparameter `audit_recorder` vor: der Schalter aus D-14 baut den Rekorder oder übergibt `None`, und beides ist bereits durchgemessen.
- Plan 18-08 findet in jeder geschriebenen Zeile die Angaben, die es formulieren soll, und in `verify_chains` die Prüfung dahinter.
- Plan 18-09 findet `Recorder.env` vor, gefüllt mit demselben Mapping, mit dem die Anwendung gebaut wurde.
- Ein neues Werkzeug ohne `@graceful` ist ab jetzt nicht mehr mergefähig: der Gate wird rot und nennt seinen Namen.

## Self-Check: PASSED

Alle fünf Dateien liegen auf der Platte
(`src/mcp_connector/audit/record.py`, `src/mcp_connector/server/__init__.py`,
`tests/unit/test_audit_record.py`, `tests/contract/test_audit_surface.py`,
`vulture_whitelist.py`), und alle drei Task-Commits stehen im Log
(`bebb522`, `6f5e033`, `84b0788`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
