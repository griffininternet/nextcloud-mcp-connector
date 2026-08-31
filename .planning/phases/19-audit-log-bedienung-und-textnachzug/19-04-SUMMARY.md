---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 04
subsystem: audit
tags: [audit-log, store, read, limit, denial-of-service, sql-placeholder, wr-02]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "audit/store.py mit CANONICAL_FIELDS, _COLUMNS, _entry_of_row und _read"
  - phase: 19
    plan: 01
    provides: "audit/text.py als die eine Reinigungsregel, damit die Leseausgabe in 19-06 keine vierte erfindet"
provides:
  - "AuditStore.read_entries(*, chain, since, until, limit) -> list[tuple[Any, ...]]: rohe Zeilen, neueste zuerst, gedeckelt"
  - "READ_LIMIT_DEFAULT = 200 und READ_LIMIT_MAX = 5000 als Modulkonstanten in __all__"
  - "_READ_ROWS: ein Lesestatement mit Spaltenliste aus _COLUMNS und drei Filtern als Platzhalterpaare"
  - "tests/unit/test_audit_store.py: dreizehn Fälle unter 'reading rows out', jeder Name mit read_entries"
affects: [19-06, 19-07, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Filter, den niemand gesetzt hat, steht als (? IS NULL OR spalte = ?) im Statement: ein Text für acht Kombinationen statt acht Statements"
    - "Die Klemmung eines Limits hat zwei Enden, weil SQLite ein negatives LIMIT als kein Limit liest"
    - "Eine Leseform gibt rohe Tupel heraus, wenn die Ausgabe seq und die Hashes braucht, die Entry absichtlich nicht trägt"
    - "Ein Deckel wird gegen mehr Zeilen als der Deckel gemessen, sonst besteht ihn auch die Fassung ohne Deckel"

key-files:
  created: []
  modified:
    - src/mcp_connector/audit/store.py
    - tests/unit/test_audit_store.py
    - vulture_whitelist.py

key-decisions:
  - "Rückgabe sind rohe Tupel und keine Entry-Objekte: Entry trägt seq, prev_hash und hash absichtlich nicht, und eine Ausgabezeile ohne Nummer ist nicht nachvollziehbar; der Docstring nennt _entry_of_row, row[0], row[-2] und row[-1] als den Weg, damit die Spaltenordnung einmal geschrieben steht"
  - "ORDER BY seq DESC und nie ORDER BY at: at ist die Wanduhr beim Schreiben und nach einem Zeitsprung nicht monoton (WR-02); ein Fall belegt es am echten File"
  - "Die Richtung ist immer neueste zuerst, weil ORDER BY seq ASC LIMIT ? die ältesten Zeilen liefern würde; die Umkehrung gehört in den Handler von 19-06"
  - "READ_LIMIT_MAX = 5000 fällt mit SWEEP_BATCH_ROWS zusammen, ist aber eine eigene Konstante: die eine begrenzt eine Transaktion, die andere eine Antwort, und eine gemeinsame Zahl wäre eine Kopplung ohne Grund"
  - "Die Klemmung steht vor der Abfrage in der Methode und nicht im Statement, damit ein Aufrufer, der später etwas anderes übergibt, nicht am SQL vorbeikommt"
  - "read_entries steht in vulture_whitelist.py, mit dem Plan benannt, der sie aufruft (19-06), in der Form der Einträge von last_entry, sweep und verify_chains"

patterns-established:
  - "Ein Test, der einen Deckel behauptet, füllt mehr Zeilen als der Deckel: fill(READ_LIMIT_MAX + 3) statt drei Zeilen und einer Behauptung, die ohne Deckel auch gilt"
  - "Die Gegenprobe auf eine Klemmung wird ausgeführt und nicht behauptet: Klemmung von Hand entfernt, zwei Fälle rot, Klemmung zurückgenommen"

requirements-completed: []
# AUDIT-04 bleibt Pending: die Abfrage liegt jetzt im Speicher, das occ-Kommando entsteht in
# 19-06 (Handler) und 19-07 (Registrierung). Erst danach kann ein Administrator lesen.
requirements-advanced: [AUDIT-04]

# Metrics
duration: 16min
completed: 2026-08-31
---

# Phase 19 Plan 04: read_entries mit Vorgabe- und Höchstlimit Summary

**Der Speicher gibt jetzt Zeileninhalt heraus, gefiltert nach Kette und Zeitfenster, gedeckelt auf 200 Zeilen ohne Angabe und 5000 mit jeder Angabe, sortiert nach `seq` und nie nach `at`, und kein Filterwert eines Aufrufers steht im SQL-Text.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-08-31T14:44:00Z
- **Completed:** 2026-08-31T15:00:00Z
- **Tasks:** 2 (Task 1 nach RED/GREEN)
- **Files modified:** 3

## Accomplishments

- `AuditStore` hat die eine Methode, die ihm fehlte. Die endgültige Signatur samt der zwei
  Konstanten, damit Plan 19-06 sie nicht aus der Datei rekonstruieren muss:

  ```python
  READ_LIMIT_DEFAULT = 200
  READ_LIMIT_MAX = 5000

  async def read_entries(
      self,
      *,
      chain: str | None = None,
      since: int | None = None,
      until: int | None = None,
      limit: int = READ_LIMIT_DEFAULT,
  ) -> list[tuple[Any, ...]]: ...
  ```

  Aufrufform für den Handler: `_entry_of_row(row)` für die Felder, `row[0]` für die Nummer,
  `row[-2]` und `row[-1]` für die zwei Hashes als rohe `bytes`. Die Liste kommt neueste zuerst;
  wer die Kettenreihenfolge ausgibt, dreht sie beim Ausgeben.
- Das Lesestatement steht neben seinen Nachbarn und ist aus `_COLUMNS` abgeleitet:

  ```python
  _READ_ROWS = (
      f"SELECT {_COLUMNS}, prev_hash, hash FROM entries "  # noqa: S608 - column names of this module, values are placeholders
      "WHERE (? IS NULL OR chain = ?) AND (? IS NULL OR at >= ?) AND (? IS NULL OR at <= ?) "
      "ORDER BY seq DESC LIMIT ?"
  )
  ```

  Sieben Platzhalter, sieben Werte, kein f-String-Platzhalter ausser `{_COLUMNS}` (T-19-11).
- Der Docstring trägt vier eigene Absätze in der Form von `verify_chains`: warum das Limit
  geklemmt ist (100 MB sind rund 440.000 Zeilen, AppAPI wartet mit `timeout => 0`, also deckelt
  von aussen nichts), warum nach `seq` und nicht nach `at` sortiert wird (WR-02), warum die
  Richtung immer neueste zuerst ist, und warum die Rückgabe kein `Entry` ist.
- Dreizehn Fälle unter `# --- reading rows out: read_entries ---`, alle am echten SQLite-File in
  `tmp_path`, kein Mock: leerer Speicher, neueste zuerst, Kettenfilter, Kettenfilter ohne
  Treffer, `limit=2`, `limit=0`, `limit=-5`, `limit=10**9` gegen 5003 Zeilen, kein Limit gegen
  205 Zeilen, die Ränder von `since` und `until`, ein nicht-monotones `at` und ein Kontoname mit
  Zeilenumbruch, plus die Form einer Zeile (Nummer, siebzehn kanonische Felder, zwei Hashes als
  32 Bytes, nachrechenbarer Digest).
- Die Gegenprobe ist gelaufen und nicht behauptet: `bounded = limit` statt der Klemmung machte
  `test_read_entries_with_a_limit_of_zero_or_below_answers_with_exactly_one_row` und
  `test_read_entries_cuts_a_limit_above_the_maximum_down_to_the_maximum` rot; danach per
  `git checkout --` zurückgenommen, `grep -c` auf die Klemmung ergibt wieder 1.
- Schema, Kette und Pragmas unangetastet: `CANONICAL_FIELDS` unverändert, kein bestehendes
  Statement angefasst, keine bestehende Methode angefasst, keine Migration.

## Task Commits

1. **Task 1: read_entries mit Vorgabe- und Höchstlimit** - `5eaa204` (test, RED), `7e1bd17` (feat, GREEN)
2. **Task 2: Alle Pfade von read_entries als Test** - `7fa0c19` (test)

## Files Created/Modified

- `src/mcp_connector/audit/store.py` - `READ_LIMIT_DEFAULT`, `READ_LIMIT_MAX` (beide in
  `__all__`, alphabetisch zwischen `OUTCOME_REJECTED` und `RETENTION_DAYS`), `_READ_ROWS`,
  `read_entries` neben `last_entry`
- `tests/unit/test_audit_store.py` - der neue Abschnitt mit dreizehn Fällen plus der
  Hilfsfunktion `file_names(tmp_path)`
- `vulture_whitelist.py` - ein Eintrag `_.read_entries` mit Begründung und dem Plan, mit dem er
  die Liste wieder verlässt

## Decisions Made

- **Rohe Tupel statt `Entry`:** `Entry` ist eine Zeile auf dem Weg **hinein** und trägt `seq`,
  `prev_hash` und `hash` bewusst nicht. Eine Leseausgabe ohne Nummer kann niemand nachverfolgen
  und eine Kette ohne Hashes niemand nachrechnen, also gibt die Methode die rohen Tupel heraus
  und der Docstring nennt den einen Weg zu den Feldern (`_entry_of_row`). Die Spaltenordnung
  steht damit weiter genau einmal im Baum.
- **Zwei Enden der Klemmung, nicht eins:** Das obere Ende fängt die Option, die eine Milliarde
  sagt. Das untere Ende ist kein Kosmetikum: `LIMIT -5` liest SQLite als **kein** Limit, ein
  ungeprüftes `--limit=-1` wäre also genau die Antwort, die diese Methode nicht geben darf.
  Beide Enden haben einen Fall.
- **`READ_LIMIT_MAX` ist eine eigene Zahl:** Sie ist zufällig gleich `SWEEP_BATCH_ROWS`. Die
  eine begrenzt, wie viele Zeilen eine Transaktion nimmt, die andere, wie viele eine Antwort
  trägt; eine gemeinsame Konstante hätte zwei Gründe verschmolzen, die sich unabhängig ändern.
- **Der Deckel wird gegen mehr Zeilen gemessen, als er zulässt:** Ein Fall mit drei Zeilen und
  `limit=10**9` besteht auch ohne jede Klemmung. Der Fall füllt deshalb `READ_LIMIT_MAX + 3`
  Zeilen über den Bulk-Helfer `fill` und behauptet `len(read) == READ_LIMIT_MAX` **und**, dass
  die jüngste Zeile dabei ist (abgeschnitten wird am alten Ende).
- **Der Kontoname kommt unverändert heraus:** Die Klammerung gehört unmittelbar vor die Ausgabe
  (Plan 19-06). Ein Speicher, der hier reinigte, gäbe einen Namen heraus, der nicht zur Kette
  passt, in der er steht, und niemand könnte die Kette wieder nachschlagen. Der Fall behauptet
  genau das: `nc_user` unverändert, `client_name` gereinigt, weil das der eine Wert ist, den der
  Speicher selbst schreibt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `vulture` meldet `read_entries` als toten Code, weil der Aufrufer erst in 19-06 entsteht**

- **Found during:** Task 1 (Acceptance Criterion "`uv run vulture ...` still")
- **Issue:** `src/mcp_connector/audit/store.py:1035: unused method 'read_entries' (60% confidence)`.
  Das Gate läuft ohne `--min-confidence`, also ist die Meldung ein Fehlschlag. Der Plan verlangt
  im selben Atemzug, dass `vulture` still ist und dass die Methode in dieser Phase noch keinen
  Produktionsaufrufer bekommt; beides geht nur über die Whitelist.
- **Fix:** Ein Eintrag `_.read_entries` im Block "The store API of phase 18" von
  `vulture_whitelist.py`, in genau der Form, die `last_entry`, `sweep` und `verify_chains` dort
  vorgemacht haben: was die Methode ist, welcher Plan sie aufruft (19-06), welche Tests sie heute
  treiben, und dass sie die Liste mit diesem Plan verlässt. Die Datei verlangt für jeden Eintrag
  eine Begründung, und diese ist die vorgesehene.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src scripts vulture_whitelist.py` still.
- **Committed in:** `7e1bd17`

**2. [Rule 3 - Blocking] `ruff` verbietet einen Pfadaufruf in einer async-Testfunktion (ASYNC240)**

- **Found during:** Task 2
- **Issue:** Der Fall zum leeren Speicher behauptet, dass keine Datei entsteht, die es nicht
  schon gab, und las dafür `tmp_path.iterdir()` direkt in der async-Testfunktion. `ruff` lehnt
  das ab (ASYNC240: ein Pfadaufruf blockiert die Schleife).
- **Fix:** Eine synchrone Hilfsfunktion `file_names(tmp_path) -> set[str]` neben den bestehenden
  synchronen Helfern `rows`, `pragma` und `past_the_store`, die aus demselben Grund synchron
  sind. Der Docstring nennt den Grund.
- **Files modified:** tests/unit/test_audit_store.py
- **Verification:** `uv run ruff check tests/unit/test_audit_store.py` still.
- **Committed in:** `7fa0c19`

### Abweichungen im Wortlaut von Kriterien und Behavior-Block

- **Testnamen:** Das Acceptance Criterion verlangt, dass `pytest -k read_entries` mindestens elf
  Tests meldet. `-k` liest den Funktionsnamen, also tragen alle dreizehn Namen `read_entries`
  (`test_read_entries_since_takes_the_moment_itself_and_not_the_one_before_it` statt
  `test_since_...`). Ohne diese Umbenennung hätte `-k read_entries` zwei Tests gemeldet und das
  Kriterium wäre am Namen und nicht an der Abdeckung gescheitert.
- **`grep -c "READ_LIMIT_DEFAULT\|READ_LIMIT_MAX"` ergibt 8 statt der geforderten "mindestens 4":**
  Zwei Definitionen, zwei `__all__`-Einträge, zwei Verwendungen im Code, zwei Nennungen im
  Docstring beziehungsweise in den `#:`-Kommentaren. Die Untergrenze des Kriteriums ist erfüllt.
- **"legt keine Datei an, die es nicht schon gab" (Behavior-Block, leerer Speicher):** Wörtlich
  gelesen wäre das falsch behauptbar, weil `_call` das Schema beim ersten Öffnen niederlegt, also
  legt auch eine Leseanfrage `audit.sqlite3` an. Der Fall behauptet deshalb, was gemeint ist: in
  `tmp_path` entsteht nichts außer dieser Datei und ihren zwei WAL-Nachbarn.
- **Zeilennummern der `<interfaces>`-Angaben:** `_COLUMNS` steht auf `:294` (Plan sagt `:292`),
  `_entry_of_row` auf `:555-574` (Plan: `:550-569`), `_read` auf `:1068-1070` (Plan: `:1063-1065`),
  `last_entry` auf `:996-1009`. Die Verschiebung stammt aus Plan 19-01 (Import von
  `audit/text.py`); die Bezüge selbst sind alle da, wo der Plan sie beschreibt.

---

**Total deviations:** 2 auto-fixed (beide Rule 3, beide Gate-Vorschriften des Repos), 4 Klarstellungen im Wortlaut
**Impact on plan:** Kein erweiterter Auftrag. Beide Fixes betreffen Gates, nicht Verhalten; keine
Zeile der Fachlogik weicht von `<action>` ab.

## Issues Encountered

- Der Kettenfilter-Fall behauptete zunächst die Nummern `[3, 1]` für Alice. Falsch gerechnet:
  Bob wird zwischen die zwei Alice-Zeilen geschrieben, also sind es `[2, 1]`. Der rote Lauf hat
  das gezeigt, die Behauptung nennt jetzt zusätzlich die Momente, damit die Nummernfolge lesbar
  bleibt.
- `ruff` verlangte für fünf der neuen Testfunktionen die mehrzeilige Signaturform (E501) und für
  den Formfall zwei getrennte Behauptungen statt `isinstance(...) and len(...)` (PT018). Beides
  ist Repo-Stil, keine Abweichung.
- Der Arbeitsbaum trägt gemischte Zeilenenden (`core.autocrlf=true`); git normalisiert beim
  Anlegen, kein Massen-Diff entstanden.

## Anforderungen

AUDIT-04 bleibt in `REQUIREMENTS.md` **Pending** und wurde nicht abgehakt. Die Anforderung
verlangt ein `occ`-Lesekommando ohne neue Manifest-Route. Dieser Plan liefert die Abfrage im
Speicher, weil nur er Schema und Verkettung besitzt; der Handler entsteht in 19-06, die
Registrierung in 19-07. Erst danach kann ein Administrator etwas lesen, und erst dann ist der
Haken die Wahrheit.

## Threat Flags

Keine neue Fläche: keine Route, kein Manifesteintrag, kein Netzzugang, keine Berechtigung, kein
Paket. Die fünf Fäden des Bedrohungsmodells sind eingelöst:

- **T-19-11** (Injection, Information Disclosure) durch die Spaltenliste allein aus `_COLUMNS`
  und sieben Platzhalter für sieben Werte. Im Statementtext steht kein f-String-Platzhalter
  außer `{_COLUMNS}`, der `# noqa: S608`-Kommentar trägt die Wortwahl der Nachbarn.
- **T-19-12** (Denial of Service) durch `max(1, min(limit, READ_LIMIT_MAX))` vor der Abfrage,
  `READ_LIMIT_DEFAULT = 200` als Vorgabe, drei Fällen an den Enden der Klemmung und einer
  ausgeführten Gegenprobe. Der Docstring nennt `timeout => 0` als den Grund, dass von aussen
  nichts deckelt.
- **T-19-13** (Tampering) durch `git diff 4baacbd HEAD -- src/mcp_connector/audit/store.py | grep -c "^-.*CANONICAL_FIELDS"`
  gleich 0: keine Zeile des kanonischen Feldes entfernt, keine hinzugefügt, keine Migration.
- **T-19-14** (Repudiation) durch `ORDER BY seq DESC`, den eigenen Docstring-Absatz und den Fall
  mit dem rückwärts gesetzten `at` (WR-02).
- **T-19-SC** (Supply Chain) durch `git diff --stat 4baacbd HEAD -- appinfo/info.xml pyproject.toml uv.lock`: leer.

Ein Hinweis für Plan 19-06: die Methode gibt `nc_user` und `chain` unverändert heraus, weil die
Klammerung dort hingehört. Ohne `printable` aus `audit/text.py` vor der Ausgabe trägt eine
Antwortzeile ein Steuerzeichen aus fremder Hand; der Fall
`test_read_entries_hands_an_account_with_a_control_character_over_untouched` hält diese
Zuständigkeitsgrenze fest, damit sie nicht versehentlich verschoben wird.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 19-06 findet Signatur, Konstanten, Sortierrichtung und Rückgabeform oben zitiert vor und
  braucht die Datei dafür nicht zu lesen. Offen bleibt dort allein die Ausgabeform (JSONL,
  Textbericht) samt der Klammerung über `audit.text.printable`.
- Die Umkehrung der Liste für einen Export in Kettenreihenfolge ist eine Zeile im Handler
  (`reversed(rows)`); der Docstring sagt ausdrücklich, dass sie dort und nicht hier steht.
- Für `--limit` hat 19-06 die Vorlage aus 19-01 (`plain_number` plus die Längenprüfung des
  Ziffernlaufs); die Methode klemmt danach ein zweites Mal, also ist ein durchgerutschter Wert
  kein unbegrenztes Lesen.

## Verification

- `uv run pytest tests/unit tests/contract`: 3040 passed.
- `uv run pytest tests/unit/test_audit_store.py -k read_entries`: 13 passed, 23 deselected.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 218 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget 18000`,
  unverändert. `read_entries` ist kein MCP-Werkzeug und an keinem Serverobjekt registriert.
- `git diff --stat 4baacbd HEAD -- appinfo/info.xml pyproject.toml uv.lock`: leer.
- `grep -c "async def read_entries" src/mcp_connector/audit/store.py`: 1.
- `grep -c "READ_LIMIT_DEFAULT\|READ_LIMIT_MAX" src/mcp_connector/audit/store.py`: 8;
  `grep -c '"READ_LIMIT_DEFAULT",'`: 1; `grep -c '"READ_LIMIT_MAX",'`: 1.
- `grep -c "ORDER BY seq DESC LIMIT ?" src/mcp_connector/audit/store.py`: 1 (neben den zwei
  bestehenden `... LIMIT 1`-Statements).
- `git diff 4baacbd HEAD -- src/mcp_connector/audit/store.py | grep -c "^-.*CANONICAL_FIELDS"`: 0.
- Gegenprobe: mit `bounded = limit` zwei Fälle rot, danach `git checkout --` und
  `grep -c "bounded = max(1, min(limit, READ_LIMIT_MAX))"`: 1.

## Self-Check: PASSED

Alle drei geänderten Dateien liegen auf der Platte
(`src/mcp_connector/audit/store.py`, `tests/unit/test_audit_store.py`, `vulture_whitelist.py`),
alle drei Commits stehen im Log (`5eaa204`, `7e1bd17`, `7fa0c19`).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
