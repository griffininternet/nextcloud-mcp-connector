---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 01
subsystem: audit
tags: [audit-log, sanitizing, unicode, bidi, content-length, refactor, r-18-06, r-18-08]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "audit/store.py mit CLIENT_NAME_LIMIT und _clean_client_name"
  - phase: 18
    plan: 06
    provides: "audit/record.py mit _clamped_client_name im Erfassungspfad"
  - phase: 18
    plan: 08
    provides: "exapp/audit_verify.py mit CHAIN_LIMIT, _printable und _payload"
provides:
  - "audit/text.py: printable(raw, *, limit) als die eine Reinigungsregel des Projekts für Werte aus fremder Hand"
  - "Drei Aufrufstellen ohne eigene Zeichenmenge: record._clamped_client_name, store._clean_client_name, audit_verify._printable"
  - "audit_verify.MAX_ANNOUNCED_DIGITS und _above_the_body_bound: eine angekündigte Länge, die int() nie werfen lässt"
  - "tests/unit/test_exapp_audit_verify.raw_call: ein POST direkt in die Anwendung, mit unangetasteten Header-Bytes"
affects: [19-02, 19-03, 19-04, 19-05, 19-06, 19-07, 19-08, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Regel für Werte aus fremder Hand in einem Blattmodul unterhalb aller Aufrufer, statt einer Fassung je Aufrufer"
    - "isprintable() als Regel statt einer Liste aus C0 und DEL: die Kategorie Cf ist damit mit erfasst"
    - "Steuerzeichen werden ersetzt und nicht getilgt, damit zwei Namensteile nicht zu einem Wort verschmelzen"
    - "Zahl aus einem Header: isascii() vor isdigit(), und die Länge des Ziffernlaufs vor seinem Wert"
    - "Ein Testfall, der rohe Header-Bytes braucht, fährt an der TestClient-Schicht vorbei direkt in die ASGI-Anwendung"

key-files:
  created:
    - src/mcp_connector/audit/text.py
    - tests/unit/test_audit_text.py
  modified:
    - src/mcp_connector/audit/record.py
    - src/mcp_connector/audit/store.py
    - src/mcp_connector/exapp/audit_verify.py
    - tests/unit/test_audit_record.py
    - tests/unit/test_exapp_audit_verify.py

key-decisions:
  - "Das Blattmodul liegt in audit/ und nicht in exapp/ui/: audit/record.py:107-109 verbietet den Import nach oben, exapp/audit_verify.py importiert ohnehin schon nach unten"
  - "Die vierte Fassung in exapp/ui/layout.py bleibt unberührt, weil ein Import aus audit/ nach exapp/ui/ die Schichtung brechen würde"
  - "limit ist Keyword-only ohne Vorgabewert: das Modul nimmt eine Grenze und entscheidet keine"
  - "printable gibt immer str zurück, nie None; die None-Semantik gehört den beiden Aufrufern, die sie verschieden beantworten"
  - "Steuerzeichen werden zu einem Leerzeichen: record._clamped_client_name tilgte sie bisher, das war die eine gewollte Verhaltensänderung dieses Plans"
  - "Die Längenprüfung des Ziffernlaufs kommt zur isascii-Prüfung hinzu: isascii allein lässt einen Lauf von 5000 ASCII-Ziffern durch, den int() seit Python 3.11 ebenfalls ablehnt"
  - "Der Unicode-Ziffer-Fall fährt direkt in die ASGI-Anwendung, weil httpx den Wert latin-1 liest und der Starlette-TestClient ihn als UTF-8 wieder kodiert; über den Client wäre der Fall ein Test der Verstümmelung"

patterns-established:
  - "Ein Nachweis per inspect.getsource je Modul: der Aufruf der einen Regel ist da UND keine eigene Zeichenschleife blieb zurück"
  - "Eine Zusammenlegung dreier Fassungen wird durch zwei Behauptungen gehalten, nicht durch eine"

requirements-completed: []
# AUDIT-04 bleibt Pending: dieser Plan legt nur die Grundlage, damit das occ-Lesekommando
# aus Plan 19-06 keine vierte Reinigungsregel und keine zweite Kopie der Unicode-Falle
# erzeugt. Das Kommando selbst entsteht dort.
requirements-advanced: [AUDIT-04]

# Metrics
duration: 22min
completed: 2026-08-31
---

# Phase 19 Plan 01: Eine Reinigungsregel und eine geschlossene Unicode-Falle Summary

**Die drei divergenten Namensreiniger sind ein Blattmodul `audit/text.py` mit einer Funktion `printable`, deren Regel `isprintable()` heißt und damit die Kategorie Cf samt Leserichtungs-Umschaltern erfasst (R-18-06 geschlossen); die angekündigte Rumpflänge in `audit_verify._payload` lässt `int()` nicht mehr werfen, weder bei einer Unicode-Ziffer (R-18-08) noch bei einem Ziffernlauf, den keine Ganzzahl fassen kann.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-31T13:44:00Z
- **Completed:** 2026-08-31T14:06:00Z
- **Tasks:** 3 (Task 1 und Task 3 nach RED/GREEN)
- **Files modified:** 7 (2 neu, 5 geändert)

## Accomplishments

- `src/mcp_connector/audit/text.py` hat genau eine öffentliche Funktion, `printable(raw, *, limit) -> str`, und drei Absätze Begründung: warum das Modul in `audit/` liegt, warum die Regel `isprintable()` ist und nicht eine Liste aus C0 und DEL, und warum ein Zeichen ersetzt und nicht getilgt wird. Das Modul nennt kein einzelnes Zeichen und keinen Codepunkt: die Regel folgt aus der Zeichenklasse.
- `printable('a' + chr(0x202E) + 'b', limit=80)` ergibt `'a b'`. Damit ist R-18-06 an der Wurzel geschlossen und nicht an drei Stellen einzeln.
- Die drei Aufrufstellen heißen weiter `_clamped_client_name`, `_clean_client_name` und `_printable`, haben unveränderte Signaturen und je einen Rumpf aus einem Aufruf plus ihrer eigenen Grenze (`store.CLIENT_NAME_LIMIT` zweimal, `CHAIN_LIMIT` einmal) und ihrer eigenen `None`-Semantik.
- Keine zweite Zeichenmenge bleibt im Baum: `grep -v "^\s*#" ... | grep -c` meldet 0 für `isprintable` in `record.py` und 0 für `x7f` in `store.py` und `audit_verify.py`. Zwei Tests halten das je Modul, einer über den Aufruf und einer über die Abwesenheit der alten Schleife.
- `audit_verify._payload` liest die angekündigte Länge in der Form von `config.py:433-465`: `announced.isascii() and announced.isdigit()`, danach entscheidet `_above_the_body_bound` erst die Länge des Ziffernlaufs und dann seinen Wert. Ein `content-length` mit `²` und ein `content-length` aus 5000 Ziffern antworten beide mit 200 und dem gewöhnlichen Bericht; die Warnung nennt den Umstand und nie den Wert.
- Alle sieben Verifikationsschritte des Plans sind gelaufen: `ruff check .`, `ruff format --check .`, `pyright`, `vulture`, `pytest tests/unit tests/contract` (3011 Tests), `check_tool_budget.py` (15712 Bytes, 21 Werkzeuge, unverändert), und `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock appinfo/info.xml` ist leer.

## Task Commits

1. **Task 1: Die eine Reinigungsregel als Blattmodul** - `7bd383f` (test, RED), `21ca79d` (feat, GREEN)
2. **Task 2: Die drei Aufrufstellen auf die eine Regel umstellen** - `4782f9e` (refactor)
3. **Task 3: Unicode-Ziffer im content-length erzeugt keine 500 mehr** - `dce1533` (test, RED), `3e626ad` (fix, GREEN), `e7b7397` (test, Typangabe der Hilfsfunktion nach pyright)

## Files Created/Modified

- `src/mcp_connector/audit/text.py` - neu: `printable`, `__all__`, Modul-Docstring mit den drei Begründungen
- `tests/unit/test_audit_text.py` - neu: acht Fälle der Regel plus zwei Nachweise über die drei Aufrufer per `inspect.getsource`
- `src/mcp_connector/audit/record.py` - `_clamped_client_name` ruft `printable`; Import; der Absatz "What this module must not import" nennt jetzt das Blattmodul statt der fünf nachgebauten Zeilen
- `src/mcp_connector/audit/store.py` - `_clean_client_name` ruft `printable`; Import
- `src/mcp_connector/exapp/audit_verify.py` - `_printable` ruft `printable`; `MAX_ANNOUNCED_DIGITS`, `_above_the_body_bound`, die korrigierte Prüfung in `_payload`; der `#:`-Kommentar an `CHAIN_LIMIT` verweist auf `audit/text.py`
- `tests/unit/test_audit_record.py` - ein neuer Fall für die gewollte Verhaltensänderung; kein bestehender Fall gelöscht oder abgeschwächt
- `tests/unit/test_exapp_audit_verify.py` - `appapi_header_pairs`, `raw_call`, `Deployment.app`, drei neue Fälle um die angekündigte Länge

## Decisions Made

- **Die Regel heißt `isprintable()`, nicht "C0 und DEL":** Eine Liste ist eine Behauptung darüber, welche Zeichen gefährlich sind; die Klasse ist eine Behauptung darüber, welche Zeichen gedruckt werden können. Nur die zweite kann dieses Projekt halten, und sie erfasst die Kategorie Cf mit, um die es bei R-18-06 ging. Der Docstring sagt das so.
- **Ersetzen statt Tilgen, und der Preis dafür:** `record._clamped_client_name` filterte bisher; damit wurde `"Claude\nAssistant"` zu `"ClaudeAssistant"`, einem Namen, den niemand registriert hat. Jetzt wird daraus `"Claude Assistant"`. Siehe "Deviations".
- **Die vierte Fassung bleibt stehen:** `exapp/ui/layout.py` behält seine eigene Regel, weil `audit/` nicht aus `exapp/ui/` importieren darf und die andere Richtung diese Schicht von der Anwendungsschicht abhängig machen würde. Das steht im Docstring von `text.py`, damit die Fassung dort nicht als Versehen gelesen wird.
- **Die Längenprüfung neben `isascii`:** Der Plan verlangt `announced.isascii() and announced.isdigit()`. Das schließt die Unicode-Ziffer, aber nicht einen Lauf von 5000 ASCII-Ziffern, den `int()` seit Python 3.11 ebenfalls ablehnt. Beide Wege führten zu derselben 500, also schließt dieser Plan beide; `config.py:433-465` nennt beide Hälften aus demselben Grund.
- **`plain_number` als Zwischenname:** Die Prüfung steht als `plain_number = announced.isascii() and announced.isdigit()` und danach `if plain_number and _above_the_body_bound(announced)`. Das hält die vom Plan geforderte Wortgleichheit des Ausdrucks und lässt gleichzeitig die vom Plan geforderte Abwesenheit der Zeichenfolge `announced.isdigit() and` zu, die in einer einzeiligen Fassung unvermeidlich stehen bliebe.
- **`raw_call` statt eines Header-Werts über den TestClient:** httpx kodiert einen Header-Wert als ASCII, liest ihn bei Bedarf als latin-1 und der Starlette-TestClient kodiert ihn als UTF-8 wieder. Aus `b"\xb2"` wird dadurch `b"\xc2\xb2"`, und der Handler sieht zwei Zeichen, deren `isdigit()` falsch ist: der Fall hätte die Verstümmelung getestet und nicht den Handler. `raw_call` baut den ASGI-Scope selbst und übergibt die Bytes unangetastet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `isascii()` allein schließt die Falle nicht: ein Ziffernlauf über 4300 Zeichen lässt `int()` weiter werfen**

- **Found during:** Task 3 (beim Bauen des RED-Falls)
- **Issue:** Der Plan verlangt `announced.isascii() and announced.isdigit()`. Ein `content-length` aus 5000 ASCII-Ziffern besteht beide Prüfungen und lässt `int()` mit `ValueError: Exceeds the limit (4300 digits) for integer string conversion` werfen, also genau die 500, die R-18-08 beschreibt, nur über einen zweiten Weg. Der RED-Lauf hat das an genau dieser Zeile gezeigt.
- **Fix:** `MAX_ANNOUNCED_DIGITS = 10` und `_above_the_body_bound(announced)`, das die Länge vor dem Wert entscheidet: ein Lauf über zehn Ziffern liegt über der Grenze, was auch immer er sagt, und wird nie umgewandelt. `config.py:433-465` nennt dieselben zwei Hälften, dieser Plan zieht sie beide nach.
- **Files modified:** src/mcp_connector/exapp/audit_verify.py, tests/unit/test_exapp_audit_verify.py
- **Verification:** `test_a_digit_run_no_integer_can_hold_answers_like_any_other_call` war rot (ValueError), ist grün (Status 200); alle Gates grün.
- **Committed in:** `dce1533` (RED), `3e626ad` (GREEN)

**2. [Rule 3 - Blocking] Der Starlette-TestClient kann den Fall des Plans nicht übertragen**

- **Found during:** Task 3 (der erste RED-Lauf war grün, was der Fall nicht sein durfte)
- **Issue:** Der Plan schreibt den Fall "gebaut mit dem dortigen Invokationshelfer und mit `headers=`". Über httpx und den TestClient kommt aus dem Byte `b"\xb2"` beim Handler die Zeichenfolge `Â²` an (latin-1 gelesen, UTF-8 wieder kodiert), deren `isdigit()` falsch ist; der Fall wäre auch ohne den Fix grün gewesen und hätte nichts belegt.
- **Fix:** `raw_call(deployment, headers, body)` fährt mit einem selbst gebauten ASGI-Scope direkt in die Anwendung, die dafür in `Deployment.app` neben dem Client liegt. Der Docstring der Hilfsfunktion sagt, dass der Grund eine Eigenschaft des Clients ist und keine des Handlers. Der Invokationshelfer `call` bleibt unverändert und trägt weiter den dritten Fall (`content-length: 99999`).
- **Files modified:** tests/unit/test_exapp_audit_verify.py
- **Verification:** Mit `raw_call` war der Fall rot (`ValueError: invalid literal for int()`), nach dem Fix grün.
- **Committed in:** `dce1533` (RED), `e7b7397` (Typangabe nach pyright)

### Bewusste Verhaltensänderung (vom Plan gefordert, hier festgehalten)

`record._clamped_client_name` **tilgte** bisher jedes Zeichen, für das `isprintable()` falsch ist; jetzt **ersetzt** es sie durch ein Leerzeichen. Ein Client, der sich als `"Claude\nAssistant"` registriert, stand bisher als `"ClaudeAssistant"` in der Zeile, also als ein Wort, das ein anderer Client sein könnte; jetzt steht dort `"Claude Assistant"`.

**Welche bestehenden Testerwartungen dafür angepasst wurden: keine.** Der einzige bestehende Fall zu diesem Weg,
`test_a_hostile_client_name_is_cleaned_and_cut_before_it_is_written` (`tests/unit/test_audit_record.py:319`), arbeitet mit `"Claude\n\x00 Assistant"`. Dort steht hinter den Steuerzeichen bereits ein Leerzeichen, also ergeben beide Regeln nach dem Zusammenziehen der Weissraumläufe `"Claude Assistant"`; die Behauptung `stored.startswith("Claude Assistant")` gilt vorher und nachher. Statt eine Erwartung zu ändern, ist ein Fall dazugekommen, der die Änderung überhaupt erst sichtbar macht: `test_a_control_character_in_a_name_becomes_a_space_and_melts_no_two_words` prüft `"Claude\nAssistant"` am Erfassungspfad und wäre unter der alten Regel rot. Kein bestehender Fall wurde gelöscht oder abgeschwächt.

### Abweichung im Wortlaut eines Akzeptanzkriteriums

Task 2 fordert für `_clamped_client_name`, `_clean_client_name` und `_printable` je `grep -c` gleich 1. Gemessen sind 2, 2 und 3, weil `grep -c` Definition **und** Aufrufstellen zählt. Der Sinn des Kriteriums, dass die drei Namen weiter existieren und keine öffentliche oder interne Signatur verschwunden ist, ist erfüllt; die Zahl 1 wäre nur bei einer Definition ohne Aufruf zu erreichen.

---

**Total deviations:** 2 auto-fixed (Rule 1, Rule 3), 1 bewusste Verhaltensänderung des Plans dokumentiert, 1 Kriterienwortlaut korrigiert
**Impact on plan:** Kein erweiterter Auftrag. Abweichung 1 schließt denselben Fehlerweg, den der Task ohnehin schließen soll, über seinen zweiten Eingang; Abweichung 2 ist die Bauweise des Falls, nicht sein Inhalt.

## Issues Encountered

- Der erste RED-Lauf von Task 3 war grün, was ein Warnsignal und kein Erfolg war: der Fall hatte die Falle nicht erreicht. Die Ursache lag in der Kodierungskette httpx/TestClient und ist als Abweichung 2 samt Begründung im Testcode festgehalten.
- `pyright` liest die `send`-Rückrufe der ASGI-Schnittstelle als `MutableMapping[str, Any]`; die Hilfsfunktion nennt deshalb `starlette.types.Message` statt `dict[str, Any]` (Commit `e7b7397`).
- Der Arbeitsbaum trägt gemischte Zeilenenden (`core.autocrlf=true`, `* text=auto`); die zwei neuen Dateien sind mit LF geschrieben und werden von git normalisiert. Kein Massen-Diff entstanden, `git status --short` ist außer `.planning/` leer.

## Anforderungen

AUDIT-04 bleibt in `REQUIREMENTS.md` **Pending** und wurde nicht abgehakt. Die Anforderung
verlangt ein `occ`-Lesekommando ohne neue Manifest-Route; dieser Plan liefert allein die
Voraussetzung, dass dieses Kommando in Plan 19-06 keine vierte Reinigungsregel und keine zweite
Kopie der Zahlenprüfung erzeugt. Ein Haken hier wäre dieselbe Art von Aussage, die Phase 18 bei
AUDIT-01 bis AUDIT-03 bewusst zurückgehalten hat.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein
Manifesteintrag, keine Versionszeichenkette. Die vier Fäden des Bedrohungsmodells sind eingelöst:

- **T-19-01** (Tampering) durch eine Regel auf Basis von `isprintable()`, den Fall mit dem Leserichtungs-Umschalter in `tests/unit/test_audit_text.py` und die zwei `inspect.getsource`-Nachweise, dass keine zweite Zeichenmenge im Baum bleibt. **R-18-06 ist damit geschlossen** und kann in `18-SECURITY.md` als erledigt vermerkt werden, sobald der Owner das übernimmt.
- **T-19-02** (Denial of Service) durch `announced.isascii() and announced.isdigit()` plus die Längenprüfung des Ziffernlaufs vor jedem `int()`, mit zwei Fällen, die beide Wege abdecken. **R-18-08 ist damit geschlossen**, und zwar weiter als das Restrisiko beschrieben war.
- **T-19-03** (Information Disclosure) durch die Warnung, die nur den Umstand nennt, und die Behauptungen, dass die Antwort weder den Headerwert noch einen Pfad noch `Traceback` trägt, und dass auch das Log den Wert nicht trägt.
- **T-19-SC** (Supply Chain) durch `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock appinfo/info.xml`: leer.

Ein Hinweis für Plan 19-06 und für den Auditor der Phase: `exapp/ui/layout.py` trägt weiterhin
eine eigene Fassung derselben Regel. Sie ist keine Lücke im Sinne von R-18-06 (sie filtert
nach `isprintable()`), aber sie ist die letzte Stelle, an der ein zweiter Wortlaut derselben
Zusage steht.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 19-06 findet `from ..audit.text import printable` als bestehenden Weg vor und braucht für Kontonamen in der Leseausgabe keine eigene Regel; die Grenze (`CHAIN_LIMIT` oder eine eigene) ist die einzige Entscheidung, die dort noch offen ist.
- Die Zahlenprüfung für `--limit` und `--since` hat mit `plain_number` plus `_above_the_body_bound` eine Vorlage im Nachbarmodul, die beide Wurfwege von `int()` abdeckt und wortgleich übernommen werden kann.
- `raw_call` in `tests/unit/test_exapp_audit_verify.py` ist die Vorlage für jeden künftigen Fall, der rohe Header-Bytes braucht; `tests/unit/test_exapp_audit_read.py` kann sie übernehmen, ohne die Kodierungskette erneut zu vermessen.

## Verification

- `uv run pytest tests/unit tests/contract`: 3011 passed.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 218 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still, `printable` wird nicht als toter Code gemeldet.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget 18000`, unverändert.
- `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock appinfo/info.xml`: leer.
- `uv run python -c "from mcp_connector.audit.text import printable; print(repr(printable('a' + chr(0x202E) + 'b', limit=80)))"`: `'a b'`.
- `grep -c "def printable" src/mcp_connector/audit/text.py`: 1. `grep -v "^\s*#" src/mcp_connector/audit/text.py | grep -c "202e\|202E"`: 0.
- `grep -c "announced.isascii() and announced.isdigit()" src/mcp_connector/exapp/audit_verify.py`: 1. Dieselbe Datei ohne Kommentarzeilen und `grep -c "announced.isdigit() and"`: 0.

## Self-Check: PASSED

Beide neuen Dateien liegen auf der Platte (`src/mcp_connector/audit/text.py`,
`tests/unit/test_audit_text.py`), alle sechs Commits stehen im Log (`7bd383f`, `21ca79d`,
`4782f9e`, `dce1533`, `3e626ad`, `e7b7397`).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
