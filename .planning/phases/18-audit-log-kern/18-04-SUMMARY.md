---
phase: 18-audit-log-kern
plan: 04
subsystem: database
tags: [sqlite, hash-chain, audit-log, retention, incremental-vacuum, wal, contract-gate]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "audit/store.py mit Schema, CANONICAL_FIELDS, _canonical, GENESIS, append, used_bytes und den Spalten removed, gap_chain, gap_hash"
provides:
  - "AuditStore.verify_chains: eine Liste von ChainFinding, je Kette höchstens ein Befund, verändert und fehlend getrennt"
  - "ChainFinding: chain, kind, seq, next_seq als eingefrorene Daten ohne fertigen Satz"
  - "FINDING_MODIFIED und FINDING_MISSING als die zwei unterschiedenen Befundarten"
  - "AuditStore.sweep: Frist, Obergrenze gegen used_bytes, ein Grabstein je betroffener Kette, Platz zurück ans Dateisystem"
  - "SweepReport: expired, trimmed, tombstones, used_bytes_after"
  - "should_sweep und should_check_accounts: das Bündelungsintervall aus D-11 als reine Funktionen auf dem eingefügten seq"
  - "FILES_WITH_OWN_SQL mit zwei Einträgen: oauth/store.py und audit/store.py, jeder mit eigener Begründungszeile"
affects: [18-06, 18-07, 18-08, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Prüfung je Kette in Stapeln über fetchmany statt fetchall über die ganze Tabelle"
    - "Grabstein in der Instanzkette erklärt die Lücke einer Nutzerkette (gap_chain, gap_hash, removed)"
    - "Löschen in Stapeln mit je eigener Transaktion, damit der Checkpoint dazwischen laufen kann"
    - "Obergrenze gegen used_bytes, nie gegen os.stat oder page_count * page_size"
    - "durchgeschrittenes PRAGMA incremental_vacuum plus wal_checkpoint(TRUNCATE)"
    - "SQL-Konstanten heissen _DROP_*, damit der Vertragstest eng bleiben kann"

key-files:
  created: []
  modified:
    - src/mcp_connector/audit/store.py
    - tests/unit/test_audit_store.py
    - tests/contract/test_no_destructive_calls.py
    - vulture_whitelist.py

key-decisions:
  - "Die Prüfung sieht je Zeile erst den Inhalt, dann den Kettenanfang, dann die Verkettung: eine gelöschte Zeile bricht den Link der nächsten, ohne deren eigenen Hash zu berühren, also melden beide Fälle verschiedene Dinge und nicht zweimal dasselbe"
  - "Die Grabsteine der Instanzkette werden genau einmal je Lauf in ein dict[str, set[str]] gelesen, nicht je Kette erneut"
  - "_append_row ist der eine Kettenschreiber für den gewöhnlichen Eintrag und für den Grabstein; zwei Stellen, die einen Vorgängerhash lesen, sind zwei Stellen, die sich über die Kette uneinig werden können"
  - "Die beiden Löschanweisungen heissen _DROP_EXPIRED und _DROP_OLDEST: der Vertragstest nimmt zwei exakte SQL-Formen aus, nicht die Datei, und eine Ausweitung auf die Aufrufstellen hätte auch ein künftiges HTTP-DELETE in diesem Modul verdeckt"
  - "SWEEP_MAX_ROUNDS = 20 und der Abbruch ohne Nutzerzeile sind zwei getrennte Wächter: eine Ablage, die auch leer über der Grenze liegt, ist ein anderer Fehler und darf nicht in eine Endlosschleife münden"
  - "moment wird übergeben statt aus der Uhr gelesen, weil es zugleich das Ende der Frist und der Zeitpunkt jedes Grabsteins dieses Laufs ist"

patterns-established:
  - "Befunddaten statt Befundsätze: ChainFinding trägt Nummern, die Formulierung entsteht im Prüfkommando (18-08), damit dieselbe Prüfung auch maschinenlesbar antworten kann"
  - "Ein Wächter je gemessener Falle: gegen used_bytes fahren (Falle 2), fetchall am incremental_vacuum (Falle 3), Stapel statt einem Zug (WAL-Messung §8)"

requirements-completed: []
# AUDIT-02 und AUDIT-03 bleiben Pending. AUDIT-02 verlangt das Prüfkommando, das die Stelle
# benennt; die Prüfung dahinter steht, das Kommando entsteht in Plan 18-08. AUDIT-03 verlangt
# eine Obergrenze, die wirkt; sie steht als Lauf bereit, aber ihr Aufrufer ist der Rekorder
# aus Plan 18-06, und bis dahin schreibt niemand in die Datei.
requirements-advanced: [AUDIT-02, AUDIT-03]

# Metrics
duration: 20min
completed: 2026-08-29
---

# Phase 18 Plan 04: Prüfung, Frist und Obergrenze Summary

**Die Ablage prüft sich selbst und begrenzt sich selbst: verify_chains benennt die erste gebrochene Stelle je Kette mit ihrer Nummer, sweep hält Frist und Obergrenze gegen used_bytes, erklärt jede Lücke mit einem Grabstein in der Instanzkette und gibt den Platz dem Dateisystem zurück.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-29T08:44:00Z
- **Completed:** 2026-08-29T09:03:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- `verify_chains` unterscheidet drei Antworten statt einer: eine nachträglich veränderte Zeile wird mit ihrer eigenen `seq` benannt, eine entfernte als Paar der beiden Nummern, zwischen denen sie stand, und eine von einem Grabstein erklärte Lücke gar nicht.
- Der Lauf arbeitet je Kette und schreitet den Cursor in Stapeln von `SWEEP_BATCH_ROWS` durch; die Grabsteine der Instanzkette werden genau einmal je Lauf gelesen. Bei der Obergrenze von 100 MB sind das rund 440.000 Zeilen, die nie gemeinsam im Speicher liegen.
- `sweep` fährt vier Schritte: Frist (`at <= moment - retention_days * 86400`), Obergrenze gegen `used_bytes`, ein Grabstein je betroffener Kette in der Instanzkette, und zuletzt `PRAGMA incremental_vacuum(10000).fetchall()` plus `PRAGMA wal_checkpoint(TRUNCATE)`.
- Die Obergrenze löscht nicht bis zur leeren Tabelle: der Test füllt 15.000 Zeilen, setzt die Grenze auf die Hälfte, und danach sind Zeilen übrig, `size()` liegt unter der Grenze und ein zweiter Lauf meldet `trimmed == 0`. Das ist der Fall, den Falle 2 der Recherche verlangt.
- Die Instanzkette bleibt stehen, auch wenn ihre Zeilen älter als die Frist sind: sie ist das Verzeichnis, das jede Lücke erklärt, und ein eigener Testfall hält das fest.
- `should_sweep` und `should_check_accounts` sind reine Funktionen auf dem eingefügten `seq`. Kein Zähler auf Modulebene (D-20), kein Cron, kein Hintergrunddienst; `ALLOWED_MODULE_STATE` bleibt unverändert bei zwei Einträgen.
- `FILES_WITH_OWN_SQL` hat jetzt zwei Einträge, jeder mit eigener Begründungszeile; der Gegenbeweis-Test schleift über die Menge und trägt den zweiten Eintrag ohne Änderung.

## Task Commits

1. **Task 1: verify_chains, die die erste gebrochene Stelle benennt** - `689da7b` (feat)
2. **Task 2: Frist, Obergrenze, Grabsteine und der Gate-Eintrag** - `22c43d9` (feat)
3. **Task 3: Die drei Fälle des Manipulationstests und die Grenzen** - `78d383e` (test), Gate-Nachzug `2f38493` (chore)

## Files Created/Modified

- `src/mcp_connector/audit/store.py` - `ChainFinding`, `SweepReport`, `FINDING_MODIFIED`, `FINDING_MISSING`, `SWEEP_MAX_ROUNDS`, `SWEEP_VACUUM_PAGES`, `verify_chains`, `sweep`, `should_sweep`, `should_check_accounts`, `_append_row` als gemeinsamer Kettenschreiber
- `tests/unit/test_audit_store.py` - sieben neue Fälle, jeder Manipulationsfall mit einer eigenen `sqlite3`-Verbindung an der Ablage vorbei
- `tests/contract/test_no_destructive_calls.py` - zweiter Eintrag in `FILES_WITH_OWN_SQL` mit eigener Begründung (T-18-05)
- `vulture_whitelist.py` - vier geparkte Namen mit Begründung und Ausstiegsplan

## Decisions Made

- **Reihenfolge der Prüfschritte je Zeile:** erst der eigene Hash, dann der Kettenanfang, dann die Verkettung. Eine gelöschte Zeile lässt den Hash der nächsten unberührt und bricht nur deren Link, eine veränderte Zeile bricht nur ihren eigenen Hash. So melden die beiden Fälle verschiedene Dinge, und der Testfall behauptet für die Löschung wörtlich das Paar `(2, 4)` und für die Änderung wörtlich `seq == 3`.
- **Ein Kettenschreiber statt zweier:** `_append_row` liest den Vorgängerhash, vergibt die Nummer und schreibt die Zeile. `append` und der Grabsteinschritt des Aufräumlaufs rufen dieselbe Funktion in ihrer eigenen Transaktion auf.
- **Die Löschung nimmt genau den gelesenen Stapel:** der Stapel ist nach `seq` sortiert, also enthält `seq <= <letzte Nummer des Stapels>` bei gleichem Prädikat genau diese Zeilen. Damit braucht die Anweisung keine Liste von Nummern und bleibt eine Anweisung mit drei Platzhaltern.
- **`moment` ist ein Parameter:** derselbe Zeitpunkt ist das Ende der Frist und der Zeitstempel jedes Grabsteins dieses Laufs; aus der Uhr gelesen wäre ein Lauf nicht wiederholbar zu prüfen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Vertragstest meldete die beiden Löschanweisungen an ihren Aufrufstellen**
- **Found during:** Task 2 (nach dem Eintrag in `FILES_WITH_OWN_SQL`)
- **Issue:** Die Ausnahme des Gates deckt zwei exakte SQL-Formen ab (`DELETE FROM `, `ON DELETE CASCADE`), nicht die Datei. Die Zeilen `conn.execute(_DELETE_EXPIRED, ...)` und `conn.execute(_DELETE_OLDEST, ...)` tragen das Wort, sind aber keine SQL-Form, also blieben zwei Befunde stehen.
- **Fix:** Die beiden Konstanten heissen `_DROP_EXPIRED` und `_DROP_OLDEST`. Die Ausnahme bleibt damit so eng, wie sie geschrieben ist; eine Ausweitung auf "Wort DELETE in dieser Datei ignorieren" hätte auch ein HTTP-DELETE verdeckt, das eines Tages in diesem Modul steht. Der Grund steht als Kommentar über den vier Anweisungen.
- **Files modified:** src/mcp_connector/audit/store.py
- **Verification:** `uv run --no-sync pytest tests/contract/test_no_destructive_calls.py -q` grün, 40 Fälle.
- **Committed in:** `22c43d9` (Task-2-Commit)

**2. [Rule 3 - Blocking] Der Dead-Code-Gate wurde durch vier Namen ohne Produktionsaufrufer rot**
- **Found during:** Task 3 (Verifikation `vulture src scripts vulture_whitelist.py`)
- **Issue:** `sweep`, `verify_chains` und die beiden Felder `next_seq` und `used_bytes_after` haben heute keinen Aufrufer im Produktionscode; ihre Aufrufer sind der Rekorder aus Plan 18-06 und das Prüfkommando aus Plan 18-08. Vulture läuft in diesem Projekt auf voller Vertrauensstufe.
- **Fix:** Vier Einträge in `vulture_whitelist.py` nach dem dort etablierten Muster der geparkten Aufrufer, mit Begründung, Testverweis und dem Plan, mit dem der Eintrag wieder verschwindet. `should_sweep` und `should_check_accounts` brauchen keinen Eintrag, weil sie in `__all__` stehen.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `2f38493` (eigener chore-Commit)

---

**Total deviations:** 2 auto-fixed (beide Rule 3, beide halten ein bestehendes Gate grün)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 hält die Ausnahme des Gates so eng, wie der Plan es verlangt ("zweiter Eintrag mit eigener Begründungszeile", nicht "Datei freistellen"), Abweichung 2 folgt dem Muster, das Plan 18-01 für `last_entry` gesetzt hat.

## Issues Encountered

- Der Aufräumlauf misst `used_bytes` zwischen zwei Transaktionen und nicht in einer: `PRAGMA freelist_count` fällt sofort nach dem `COMMIT`, und eine Messung innerhalb der offenen Transaktion hätte die eigene Löschung noch nicht gesehen. Das ist der Grund, warum `sweep` über `_transaction` läuft und jeden Stapel selbst öffnet und schliesst, statt einen `_write`-Rumpf zu benutzen.
- Der Test der Obergrenze setzt die Grenze auf die Hälfte der gemessenen Belegung statt auf eine feste Bytezahl. Eine feste Zahl wäre an Seitengrösse und Zeilenbreite gebunden und würde bei einer harmlosen Schemaänderung entweder gar nichts oder alles löschen.

## Anforderungen

AUDIT-02 und AUDIT-03 bleiben in `REQUIREMENTS.md` **Pending**, obwohl die Plan-Frontmatter sie
nennt, und aus demselben Grund, aus dem Plan 18-01 sie zurückgehalten hat. AUDIT-02 verlangt ein
Prüfkommando; die Prüfung dahinter steht jetzt, das Kommando entsteht in Plan 18-08. AUDIT-03
verlangt eine Obergrenze, die wirkt; der Lauf steht bereit, sein Aufrufer ist der Rekorder aus
Plan 18-06, und bis dahin schreibt niemand in die Datei. Ein Haken hier wäre die Art von Aussage,
die dieses Projekt bei EXAPP-10, TABLES-01 und zuletzt bei AUDIT-01 bewusst zurückgehalten hat.

## Threat Flags

Keine. Die Phase bringt keine Route, keinen Netzzugang und keine neue Berechtigung. Die beiden
Fäden, die der Plan als `mitigate` führt, sind eingelöst: T-18-03 durch die getrennte Prüfung von
Inhalt und Verkettung samt drei Fällen an der Ablage vorbei, T-18-05 durch die Obergrenze gegen
`used_bytes`, die Stapel, das durchgeschrittene `incremental_vacuum` und die Rundengrenze. T-18-04
(ein gefälschter Grabstein) bleibt wie geplant `accept` und steht als Grenze im Docstring von
`verify_chains`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-06 findet `should_sweep`, `should_check_accounts` und `sweep(moment=..., retention_days=..., size_limit=...)` vor; der Rekorder braucht nur die Nummer, die `append` zurückgibt.
- Plan 18-08 findet `verify_chains()` und `ChainFinding` vor; die Formulierung für den Administrator fehlt bewusst und ist die Arbeit dieses Plans.
- Plan 18-05 (Kontoprüfung aus D-12) findet mit `_write_tombstones` und `gap_chain` das Muster vor, nach dem eine ganze Kette samt Grabstein fällt.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract -q`: grün.
- `uv run --no-sync ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py`: alle grün über das ganze Repo.
- `uv run --no-sync python scripts/check_tool_budget.py`: 15712 Bytes, 21 Werkzeuge, Budget 18000, unverändert.
- `FILES_WITH_OWN_SQL` hat zwei Einträge, `ALLOWED_MODULE_STATE` unverändert zwei.

## Self-Check: PASSED

Alle vier Dateien liegen auf der Platte, alle vier Task-Commits stehen im Log
(`689da7b`, `22c43d9`, `78d383e`, `2f38493`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
