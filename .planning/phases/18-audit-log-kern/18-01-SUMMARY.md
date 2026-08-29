---
phase: 18-audit-log-kern
plan: 01
subsystem: database
tags: [sqlite, hash-chain, sha256, audit-log, wal, auto-vacuum, asyncio]

# Dependency graph
requires:
  - phase: 03
    provides: "oauth/store.py als Muster für eine SQLite-Ablage (WAL, busy_timeout, asyncio.to_thread, Objekt statt Modulzustand) und config.persistent_storage als Pfadquelle"
provides:
  - "src/mcp_connector/audit/store.py: zweite SQLite-Datei mit eigenem Schema, eigenen Pragmas und Hash-Kette je Kettenkennung"
  - "AuditStore.append: Vorgängerhash lesen und Zeile schreiben in genau einer BEGIN-IMMEDIATE-Transaktion, Rückgabe der vergebenen seq"
  - "AuditStore.last_entry: jüngste Zeile einer Kette, wahlweise auf eine Art eingeschränkt"
  - "AuditStore.size / used_bytes: die einzige Größenmessung, die nach einem Löschen fällt"
  - "CANONICAL_FIELDS: die unveränderliche Feldreihenfolge der Kanonisierung (17 Namen)"
  - "audit_opener(env): ein Speicher je Anwendung als Closure, kein Modulzustand"
  - "AUDIT_STATE_ATTR: der Name, unter dem die Transportgrenze den Rekorder hinterlegt"
affects: [18-02, 18-03, 18-04, 18-05, 18-06, 18-07, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zweite SQLite-Datei neben oauth.sqlite3, eigene Verbindung, eigenes WAL (D-01)"
    - "Hash-Kette je Kettenkennung: SHA-256 über CANONICAL_FIELDS plus prev_hash, 32 rohe Bytes als BLOB"
    - "auto_vacuum = INCREMENTAL als allererste Anweisung auf einer frischen Verbindung"
    - "used_bytes = (page_count - freelist_count) * page_size als einzige Größenmessung"

key-files:
  created:
    - src/mcp_connector/audit/store.py
    - src/mcp_connector/audit/__init__.py
    - tests/unit/test_audit_store.py
  modified:
    - vulture_whitelist.py

key-decisions:
  - "auto_vacuum = INCREMENTAL muss vor PRAGMA journal_mode = WAL laufen, nicht nur vor executescript(SCHEMA): das Umschalten auf WAL schreibt den Dateikopf und friert den Modus auf 0 ein (eigene Messung, beide Reihenfolgen gegen eine frische Datei)"
  - "Der kanonische Rumpf wird aus genau den Spaltenwerten gebildet, die auch der INSERT schreibt (_row_values), damit ein Prüfkommando den Hash allein aus der Zeile nachrechnen kann"
  - "seq wird innerhalb der Transaktion aus sqlite_sequence gelesen und ausdrücklich geschrieben, weil die Nummer vor dem INSERT feststehen muss (sie wird mitgehasht)"
  - "Der Client-Name wird beim Schreiben entschärft und auf CLIENT_NAME_LIMIT gekürzt (Falle 8), statt ihn roh in die Zeile zu lassen"
  - "last_entry steht als geparkter Aufrufer in vulture_whitelist.py und verlässt die Liste mit Plan 18-07"

patterns-established:
  - "Entry als frozen/slots-Datenklasse ohne seq, prev_hash und hash: ein Aufrufer, der die Kettenteile setzen könnte, könnte sie gabeln"
  - "Zwei Kettenarten in einer Tabelle, unterschieden durch die Kennung (u:<nc_user> gegen i:instance)"
  - "Grenzbeschreibung im Modul-Docstring: die Kette zeigt eine unbemerkte Änderung, sie schützt nicht gegen jemanden, der die Datei schreiben und die Kette neu rechnen kann"

requirements-completed: [AUDIT-02, AUDIT-03]

# Metrics
duration: 20min
completed: 2026-08-29
---

# Phase 18 Plan 01: Ablage und Hash-Kette Summary

**Zweite SQLite-Datei mit 19-spaltigem entries-Schema, SHA-256-Kette je Nutzer- und Instanzkennung in einer BEGIN-IMMEDIATE-Transaktion, auto_vacuum INCREMENTAL und used_bytes als einzige Größenmessung.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-29T08:00:00Z
- **Completed:** 2026-08-29T08:20:00Z
- **Tasks:** 3
- **Files modified:** 4 (3 neu, 1 geändert)

## Accomplishments

- `audit/store.py` legt die Ablage aus D-01 an: eigene Datei, eigene Verbindung, eigenes WAL, kein Import aus `server/`, `exapp/` oder `oauth/crypto`, nur Standardbibliothek.
- Das Schema trägt die 19 Spalten von Anfang an, darunter `actor` (D-16) und die beiden Spalten, die ein Grabstein in Plan 18-04 braucht (`gap_chain`, `gap_hash`); eine spätere Migration entfällt.
- `append` liest den Vorgängerhash und schreibt die Zeile in genau einer Transaktion mit `BEGIN IMMEDIATE`; zwanzig gleichzeitige Schreiber derselben Kette ergeben zwanzig verschiedene `prev_hash`-Werte, also keine Gabelung.
- `used_bytes` misst `(page_count - freelist_count) * page_size` und fällt nach einem Löschen, während `page_count * page_size` stehen bleibt; beides ist im Test gegenübergestellt.
- `audit_opener(env)` liefert einen Speicher je Anwendung ohne einen einzigen veränderlichen Namen auf Modulebene; der Gate `tests/contract/test_no_destructive_calls.py` bleibt bei genau zwei erlaubten Ausnahmen.

## Task Commits

1. **Task 1: audit/store.py mit Schema, Pragmas und Kettenanhang** - `fa8159e` (feat)
2. **Task 2: audit/__init__.py mit Fabrik und Zustandsname** - `d92c41f` (feat)
3. **Task 3: Unit-Tests gegen eine echte Datei** - `704533a` (test), Gate-Nachzug `16c9a4f` (chore)

## Files Created/Modified

- `src/mcp_connector/audit/store.py` - Schema, Pragmas, Kanonisierung, Kettenanhang, `used_bytes`, Grenzbeschreibung im Modul-Docstring
- `src/mcp_connector/audit/__init__.py` - `AUDIT_STATE_ATTR`, `audit_opener` als Closure, Re-Exports
- `tests/unit/test_audit_store.py` - acht Fälle gegen eine echte Datei in `tmp_path`
- `vulture_whitelist.py` - ein geparkter Name (`last_entry`) mit Begründung und Ausstiegsplan

## Decisions Made

- **Pragma-Reihenfolge korrigiert:** Der Plan verlangte `journal_mode`, `busy_timeout`, dann `auto_vacuum` vor `executescript(SCHEMA)`. Gemessen meldet `PRAGMA auto_vacuum` in dieser Reihenfolge 0. `auto_vacuum` steht jetzt als erste Anweisung auf der Verbindung; die Messung beider Reihenfolgen steht als Absatz im Docstring von `_connect`.
- **Kanonisierung über die Spaltenwerte:** `_row_values` baut die Zeile einmal, der INSERT und der Digest nehmen dieselbe Reihenfolge. Ein Prüfkommando kann den Hash damit allein aus der gelesenen Zeile nachrechnen, was der Test bereits tut.
- **`seq` aus `sqlite_sequence`:** Die Nummer wird mitgehasht und muss deshalb vor dem INSERT feststehen. `AUTOINCREMENT` hält den Zähler auch über einen Grabstein-Lauf hinweg monoton.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] auto_vacuum blieb trotz Pragma vor dem Schema auf 0**
- **Found during:** Task 1 (audit/store.py)
- **Issue:** Die im Plan vorgegebene Reihenfolge (`journal_mode = WAL`, `busy_timeout`, `auto_vacuum = INCREMENTAL`, dann `executescript`) lässt `PRAGMA auto_vacuum` auf 0. Das Umschalten auf WAL schreibt bereits den Dateikopf, danach ist der Modus nur noch mit einem vollen `VACUUM` änderbar. Damit wäre das Akzeptanzkriterium (Wert 2) verfehlt und Plan 18-04 könnte keinen Platz an das Dateisystem zurückgeben.
- **Fix:** `PRAGMA auto_vacuum = INCREMENTAL` ist die erste Anweisung auf der Verbindung, davor steht nur `sqlite3.connect`. Die Gegenmessung beider Reihenfolgen steht als Absatz im Docstring von `_connect`.
- **Files modified:** src/mcp_connector/audit/store.py
- **Verification:** `PRAGMA auto_vacuum` meldet 2 und `PRAGMA journal_mode` weiterhin `wal` auf einer frisch angelegten Datei; als Testfall festgehalten.
- **Committed in:** `fa8159e` (Task-1-Commit)

**2. [Rule 3 - Blocking] Der Dead-Code-Gate wurde durch `last_entry` rot**
- **Found during:** Task 3 (Verifikation `vulture src scripts vulture_whitelist.py`)
- **Issue:** `last_entry` hat noch keinen Aufrufer im Produktionscode; sein Aufrufer ist der Schalter aus D-15 in Plan 18-07. Vulture läuft in diesem Projekt auf voller Vertrauensstufe und meldete die Methode als tot.
- **Fix:** Ein Eintrag `_.last_entry` in `vulture_whitelist.py` nach dem dort etablierten Muster der geparkten Aufrufer, mit Begründung, Testverweis und dem Plan, mit dem der Eintrag wieder verschwindet.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `16c9a4f` (eigener chore-Commit)

**3. [Rule 2 - Missing Critical] Client-Name wird beim Schreiben entschärft**
- **Found during:** Task 1 (audit/store.py)
- **Issue:** Der registrierte Client-Name kommt aus der dynamischen Registrierung, also von aussen (Falle 8 der Recherche). Roh in eine Zeile geschrieben könnte er mit Steuerzeichen und Zeilenumbrüchen die Ausgabe des Prüfkommandos unlesbar machen oder eine Zeile vortäuschen.
- **Fix:** `_clean_client_name` entfernt nicht druckbare Zeichen, fasst Leerraum zusammen und kürzt auf `CLIENT_NAME_LIMIT`; `append` schreibt nur die geklammerte Form.
- **Files modified:** src/mcp_connector/audit/store.py
- **Verification:** `pyright`, `ruff` und die Unit-Tests grün; die Konstante war im Plan bereits vorgesehen und hat damit einen Nutzer.
- **Committed in:** `fa8159e` (Task-1-Commit)

---

**Total deviations:** 3 auto-fixed (1 Bug, 1 Blocking, 1 Missing Critical)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 rettet ein Akzeptanzkriterium des Plans, Abweichung 2 hält ein bestehendes Gate grün, Abweichung 3 setzt eine Falle der Recherche um, deren Konstante der Plan schon nannte.

## Issues Encountered

- Der Plan nennt in `<behavior>` "siebzehn Spalten", das Akzeptanzkriterium von Task 1 nennt neunzehn. Die Tabelle hat neunzehn Spalten, davon gehen siebzehn in die Kanonisierung ein (alles ausser `prev_hash` und `hash`). Der Test behauptet beide Zahlen und ihren Zusammenhang, damit die Doppeldeutigkeit nicht wiederkommt.
- Zweitausend Zeilen für den Größenfall werden mit einer eigenen Verbindung in einer Transaktion geschrieben statt über `append`: zweitausend Verbindungen kosten rund vierzehn Sekunden für eine Messung, die von Seiten handelt und nicht von Hashes. Der Grund steht als Docstring an der Hilfe.

## Threat Flags

Keine. Die Ablage hat keine Route, keinen Netzzugang und keine neue Berechtigung; die einzige neue Datei liegt im bereits vorhandenen Volume.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-02 (Erfassungspfad) kann auf `Entry`, `append`, `user_chain` und `AUDIT_STATE_ATTR` aufsetzen; die Feldreihenfolge der Kanonisierung ist ab jetzt fest.
- Plan 18-04 (Frist, Obergrenze, Prüfkommando) findet `RETENTION_DAYS`, `SIZE_LIMIT_BYTES`, `SWEEP_EVERY`, `SWEEP_USER_CHECK_EVERY`, `USER_SILENCE_DAYS`, `SWEEP_BATCH_ROWS`, `used_bytes` sowie die Spalten `removed`, `gap_chain` und `gap_hash` vor.
- Noch niemand schreibt in die Datei: kein Werkzeug, kein Dekorator und keine Route berühren sie, und der Schalter aus D-14 entsteht in einem späteren Plan dieser Phase.

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
