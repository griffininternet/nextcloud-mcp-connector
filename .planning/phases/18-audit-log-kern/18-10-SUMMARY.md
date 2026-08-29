---
phase: 18-audit-log-kern
plan: 10
subsystem: audit
tags: [audit-log, abschluss, nachweistabelle, budget-stillstand, gates, D-18, T-18-22, T-18-25]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "AuditStore, AUDIT_FILENAME, Entry, user_chain, die Ablage neben dem OAuth-Speicher"
  - phase: 18
    plan: 04
    provides: "sweep, verify_chains, used_bytes und die Obergrenze"
  - phase: 18
    plan: 08
    provides: "das Prüfkommando und AuditStore.overview"
  - phase: 18
    plan: 09
    provides: "die Kontoprüfung, die Kettenlöschung samt Grabstein und den CI-Schritt im Job exapp"
provides:
  - "tests/unit/test_exapp_purge.py: vier Fälle, die das Überleben des Audit-Logs beim Purge halten, samt Deployment.note und Deployment.audit_rows"
  - "tests/unit/test_audit_store.py: der Fall, dass der OAuth-Speicher nach dem Greifen der Audit-Obergrenze eine Token-Rotation und eine neue Verbindung annimmt"
  - "18-10-SUMMARY.md: die Nachweistabelle je Erfolgskriterium, der Budget-Stillstand, sieben Gate-Zeilen und die Messung zu A2"
affects: [19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Behauptung, die niemand prüft, bekommt ihren Test statt einer Sonderbehandlung im Handler: purge.py bleibt unverändert, der Beleg liegt im Test"
    - "Getestet und hergeleitet stehen in derselben Tabelle nebeneinander und sind als solche beschriftet, damit die nächste Phase das eine nicht für das andere hält"
    - "Eine Messung ist eine Beleg-Zeile in der SUMMARY, nie eine Zeitschwelle in einem Testfall"

key-files:
  created:
    - .planning/phases/18-audit-log-kern/18-10-SUMMARY.md
  modified:
    - tests/unit/test_exapp_purge.py
    - tests/unit/test_audit_store.py

key-decisions:
  - "Der Fall über die ungebrochene Kette liest die Zeilen zuerst an der Ablage vorbei: verify_chains legt eine fehlende Datei neu an und findet dann nichts zu melden, also wäre die leere Befundliste allein auch das Bild eines gelöschten Logs"
  - "Die Gegenprobe lief über eine Sicherungskopie von purge.py und nicht über git stash oder git clean; danach ist git diff --stat auf die Datei wieder leer"
  - "Die Schreibkosten stehen als gemessene Zahl in dieser SUMMARY und in keinem Testfall: eine Zeitschwelle wäre auf fremder Hardware eine Zufallszahl"
  - "Der grep über die drei Aufräumpfade trifft eine Zeile, und diese SUMMARY nennt sie, statt den Befund wegzulassen; die schärfere Fassung über die Namen der Ablage trifft keine"
  - "Die Grenze aus D-18 steht wörtlich und ohne Beschönigung: --rm-data entfernt das Volume und mit ihm das Log"

patterns-established:
  - "Ein Abschlussplan einer Phase belegt jedes Erfolgskriterium mit Datei plus Testname oder Kommandoausgabe, und ein Kriterium ohne Fundstelle gilt als offen"

requirements-completed: []
# AUDIT-01, AUDIT-02 und AUDIT-03 sind mit den Plänen 18-07 und 18-08 abgelegt worden.
# Dieser Plan legt keine neue Anforderung ab, er belegt die drei bestehenden.

# Metrics
duration: 45min
completed: 2026-08-29
---

# Phase 18 Plan 10: Der Abschluss auf Belegen Summary

**Jedes der fünf Erfolgskriterien der Roadmap hat jetzt eine Fundstelle statt einer Behauptung, das Werkzeugbudget steht mit 15712 Bytes über 21 Werkzeuge exakt dort, wo es vor der Phase stand, und die Grenze aus D-18 steht beim Namen darin: `--rm-data` entfernt das Volume und mit ihm das Log.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-08-29T12:40:00Z
- **Completed:** 2026-08-29T13:25:00Z
- **Tasks:** 3
- **Files modified:** 3 (1 neu, 2 geändert)

## Accomplishments

- **D-v1.5-01 ist nicht mehr nur wahr, sondern gehalten.** Vier Fälle in
  `tests/unit/test_exapp_purge.py` behaupten das Überleben des Audit-Logs beim Purge: die
  Zeilen sind danach dieselben (Vergleich der vollständigen Zeilen, nicht nur der Anzahl),
  die Ketten sind ungebrochen, alle sieben OAuth-Tabellen sind leer und der Datenschlüssel
  ist gelöscht, und die Datei ist danach weiterhin lesbar, weil sie nicht mit diesem
  Schlüssel verschlüsselt ist.
- **`src/mcp_connector/exapp/purge.py` ist unverändert.** `git diff --stat` auf die Datei
  ist leer. Das Überleben ist eine Eigenschaft des bestehenden Handlers und keine neue
  Sonderbehandlung: der Purge gibt App-Passwörter zurück, leert sieben Tabellen und löscht
  den Datenschlüssel, und keine dieser drei Handlungen kennt eine zweite Datei im selben
  Verzeichnis.
- **Die Gegenprobe ist geführt worden.** Über eine Sicherungskopie der Datei, nicht über
  `git stash` oder `git clean`: eine eingefügte Zeile, die die Audit-Datei nach dem Leeren
  der Tabellen löscht, macht **alle vier** Fälle rot. Danach wurde die Kopie zurückgespielt
  und `git diff --stat src/mcp_connector/exapp/purge.py` ist wieder leer.
- **Die zweite Hälfte von Erfolgskriterium 4 ist belegt.** Ein Fall in
  `tests/unit/test_audit_store.py` füllt die Audit-Ablage über ihre Obergrenze, lässt den
  Aufräumlauf greifen und behauptet danach beides: der OAuth-Speicher im selben Verzeichnis
  nimmt eine Token-Rotation und eine neue Verbindung an, und `used_bytes` der Audit-Ablage
  liegt unter der Grenze.
- **Sieben Gates grün**, in der Reihenfolge des CI-Jobs `unit`, jeder mit Kommando und
  Ergebnis unten.
- **Das Werkzeugbudget steht still:** `tools/list: 15712 bytes, 21 tools, budget 18000` vor
  und nach der Phase, und `scripts/check_tool_budget.py` sowie
  `tests/contract/test_tool_surface.py` sind seit dem ersten Commit der Phase unverändert.

## Task Commits

1. **Task 1: Das Audit-Log überlebt den Purge, und ein Test hält es** - `f358bec` (test)
2. **Task 2: Schreibkosten messen und den OAuth-Speicher bei vollem Volume prüfen** - `bb87187` (test)
3. **Task 3: Gate-Lauf, Budget-Stillstand und die Nachweistabelle** - diese SUMMARY

## Files Created/Modified

- `tests/unit/test_exapp_purge.py` - `T-18-22` im Threat-Katalog des Modul-Docstrings, die
  zweite Datei in der `Deployment`-Hülle (`audit_path`, `audit`), `Deployment.note` (Zeilen
  über `AuditStore.append`, also mit echter Kette), `Deployment.audit_rows` (Lesen an der
  Ablage vorbei wie `counts`), `Deployment.AUDIT_ROWS`, und die vier Fälle des neuen
  Abschnitts
- `tests/unit/test_audit_store.py` - der Nachbar im selben Volume: `oauth`-Import, sieben
  Konstanten für eine Verbindung und eine Rotation, und
  `test_the_oauth_store_still_rotates_and_connects_after_the_bound_bit`
- `.planning/phases/18-audit-log-kern/18-10-SUMMARY.md` (neu)

## Die sieben Gates

In der Reihenfolge des CI-Jobs `unit` aus `.github/workflows/ci.yml`, alle lokal gefahren:

| # | Kommando | Ergebnis |
|---|----------|----------|
| 1 | `uv run --no-sync ruff check .` | `All checks passed!` |
| 2 | `uv run --no-sync ruff format --check .` | `216 files already formatted` |
| 3 | `uv run --no-sync pyright` | `0 errors, 0 warnings, 0 informations` |
| 4 | `uv run --no-sync vulture src scripts vulture_whitelist.py` | ohne Befund (kein Ausgabetext, Rückgabewert 0) |
| 5 | `uv run --no-sync pytest tests/unit tests/contract` | `2987 passed in 80.32s` |
| 6 | `uv run --no-sync python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000` |
| 7 | `uv run --no-sync pytest -m matrix` | `8 passed, 3146 deselected in 19.01s` |

Der siebte Lauf gehört ausdrücklich dazu, weil diese Phase Werkzeugcode angefasst hat: der
Marker `matrix` ist im Vorgabelauf ausgeschlossen und läuft im CI als eigener Schritt
desselben Jobs.

**`-m integration` läuft hier nicht und soll hier nicht laufen.** Er gehört in den CI-Job
`exapp`, der die HaRP-Topologie hochfährt. Das Ergebnis aus Plan 18-09 wird damit
nachgetragen: die vier Fälle in `tests/integration/test_appapi_users_list.py` übersprangen
sich lokal mit dem genannten Grund (`NC_MCP_URL is not set: no test Nextcloud available`),
kein roter Fall, und der Schritt "The account list behind D-12 (AUDIT-03, assumption A1)"
steht im Job `exapp`. Die Messung von A1 findet dort statt, nicht auf diesem Rechner.

## Budget-Stillstand

| Zeitpunkt | Ausgabe von `scripts/check_tool_budget.py` |
|-----------|--------------------------------------------|
| vor der Phase (18-RESEARCH.md §10, gemessen 2026-08-29) | `tools/list: 15712 bytes, 21 tools, budget 18000` |
| nach der Phase (dieser Lauf) | `tools/list: 15712 bytes, 21 tools, budget 18000` |

Kein Grenzwert wurde angehoben, kein Werkzeug kam dazu: `BUDGET_BYTES = 18_000`
(`scripts/check_tool_budget.py:83`) und `MAX_TOOL_BYTES = 1400` (`:117`) sind unverändert.

```
git diff --stat 9d9be78 HEAD -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py
(leer)
```

`9d9be78` ist der Commit, mit dem die Phase begann. Beide Dateien haben über zehn Pläne
hinweg keine Zeile geändert. Ebenfalls leer über denselben Bereich:
`docs/privacy.md`, `docs/uninstall.md`, `CHANGELOG.md`, `pyproject.toml`, `uv.lock`
(T-18-SC: diese Phase hat kein Paket installiert). `appinfo/info.xml` trägt genau zwölf
eingefügte Kommentarzeilen aus Plan 18-08 und keine geänderte Zeile: keine Version, keine
`<url>`.

## Nachweistabelle: die fünf Erfolgskriterien

| # | Erfolgskriterium (Roadmap) | Art | Fundstelle |
|---|----------------------------|-----|------------|
| 1 | Eintrag je Aufruf mit Nutzer, Werkzeug, Zeitpunkt, Client und Status; ein abgelehnter Aufruf mit seinem Grund; kein Werkzeug kommt vorbei | getestet | `tests/unit/test_audit_record.py::test_a_call_that_worked_is_recorded_as_ok` (die fünf Felder), `::test_a_refusal_is_recorded_with_its_identifier_and_never_with_its_sentence` und `::test_a_refusal_without_an_identifier_stays_unspecified` (der Grund als feste Kennung, D-17), `tests/contract/test_audit_surface.py::test_every_registered_tool_carries_the_recording_marker` und `::test_the_two_ways_to_the_tool_name_cannot_drift_apart` (alle 21 tragen die Erfassung) |
| 2 | Kein Parameterwert und kein Ergebnisinhalt; Erlaubnisliste je Werkzeug; Vertragstest nach dem Muster des Budget-Gates | getestet | `tests/unit/test_audit_store.py::test_params_are_a_sorted_list_of_names_and_no_column_holds_a_value`, `tests/unit/test_audit_record.py::test_no_column_of_the_entry_carries_a_parameter_value` und `::test_an_invented_parameter_name_reaches_no_entry`; das Gate selbst: `tests/contract/test_audit_surface.py::test_every_registered_tool_has_an_allowlist_entry`, `::test_no_allowlisted_name_is_absent_from_its_own_schema`, `::test_no_allowlisted_name_is_on_the_block_list`, `::test_the_block_list_names_parameters_that_really_exist` |
| 3 | Prüfkommando bestätigt die ungebrochene Kette oder benennt die erste Stelle; eine veränderte Zeile wird gefunden | getestet | `tests/unit/test_audit_store.py::test_a_row_changed_after_the_fact_is_named_with_its_own_number`; über das Kommando: `tests/unit/test_exapp_audit_verify.py::test_an_untouched_store_answers_200_and_says_no_break`, `::test_a_changed_entry_is_named_with_its_chain_and_its_number`, `::test_a_removed_entry_is_named_as_the_pair_of_numbers_it_was_between`, `::test_a_head_of_a_chain_that_nothing_explains_is_named_as_such`. Jede Manipulation entsteht mit einer eigenen `sqlite3`-Verbindung an der Ablage vorbei |
| 4 | Eigene Ablage neben dem OAuth-Speicher, Obergrenze, Frist bis mindestens 180 Tage; bei vollem Volume bleiben Token-Rotation und neue Verbindungen funktionsfähig | getestet | Ablage: `AUDIT_FILENAME = "audit.sqlite3"` (`src/mcp_connector/audit/store.py:84`) neben `STORE_FILENAME = "oauth.sqlite3"` (`src/mcp_connector/oauth/store.py:83`), `tests/unit/test_audit_store.py::test_a_fresh_file_carries_wal_incremental_vacuum_and_the_nineteen_columns`. Obergrenze: `::test_the_upper_bound_stops_before_the_table_is_empty`. Frist: `::test_the_retention_window_takes_the_old_rows_and_leaves_the_young_ones` (behauptet `RETENTION_DAYS == 180` und beide Seiten des Randes). Nachbar: `::test_the_oauth_store_still_rotates_and_connects_after_the_bound_bit` (neu in diesem Plan) |
| 5a | `occ mcp_connector:purge` lässt das Audit-Log stehen | **getestet** | `tests/unit/test_exapp_purge.py::test_the_purge_leaves_every_row_of_the_audit_log_where_it_is`, `::test_the_chains_of_the_audit_log_are_unbroken_after_the_purge`, `::test_the_purge_empties_every_oauth_table_and_keeps_the_audit_rows`, `::test_the_audit_log_is_still_readable_after_the_data_key_was_deleted`. Gegenprobe geführt: alle vier werden rot, sobald der Handler die zweite Datei anfasst |
| 5b | Entfernen über die Oberfläche, Verbindung trennen und Pausieren lassen das Audit-Log stehen | **hergeleitet** (T-18-25, `accept`) | Kein Test, sondern ein grep über die drei Aufräumpfade plus die Tabelle in `18-RESEARCH.md` §11 (Zeilen 1126 bis 1136) und `docs/uninstall.md:47-48` für das Verhalten der Oberfläche. Die grep-Ausgabe steht wörtlich unten, samt dem einen Treffer und seiner Bedeutung |

Kein Vorgang steht in dieser Tabelle als getestet da, der es nicht ist.

### Der grep zu Zeile 5b, mit seinem Befund

Der Plan erwartet keine Zeile. Der Lauf liefert eine, und sie steht hier, statt
weggelassen zu werden:

```
$ grep -rniE "audit|AUDIT_FILENAME|audit\.sqlite3" \
    src/mcp_connector/oauth/connections.py \
    src/mcp_connector/exapp/purge.py \
    src/mcp_connector/exapp/lifecycle.py
src/mcp_connector/exapp/lifecycle.py:117:  "the occ command registration failed, the purge and the audit log check "
```

**Was der Treffer ist:** der Text einer Logzeile aus Plan 18-08. Sie steht im letzten
Auffangnetz der Kommandoregistrierung und sagt einem Administrator, dass **beide** occ-
Kommandos fehlen, wenn die ganze Registrierung fehlschlägt. Sie liegt im `enabled=1`-Zweig,
sie liest keine Datei, und sie schreibt keine.

**Was der Treffer nicht ist:** ein Zugriff auf die Audit-Ablage. Die schärfere Fassung
über die Namen, unter denen diese Ablage überhaupt erreichbar wäre, trifft keine Zeile:

```
$ grep -rniE "AUDIT_FILENAME|audit\.sqlite3|AuditStore|audit\.store|from mcp_connector.audit|audit import" \
    src/mcp_connector/oauth/connections.py \
    src/mcp_connector/exapp/purge.py \
    src/mcp_connector/exapp/lifecycle.py
(keine Zeile, Rückgabewert 1)
```

Das sind die drei Dateien, in denen Trennen und Pausieren (`oauth/connections.py`), der
Purge (`exapp/purge.py`) und der `enabled=0`-Haken der Oberfläche (`exapp/lifecycle.py`)
liegen. Keine von ihnen importiert das Audit-Modul, keine kennt den Dateinamen, keine
öffnet die Datei. Genau das ist die Herleitung, und sie bleibt eine Herleitung: sie sagt,
dass diese drei Pfade die Ablage nicht anfassen **können**, nicht dass ein Testlauf es
beobachtet hätte. Die Tabelle in `18-RESEARCH.md` §11 führt dieselbe Herleitung mit ihren
Fundstellen, und `docs/uninstall.md:48` hält fest, dass der Weg der Oberfläche auf
Nextcloud 34 `disableExApp` ist und dabei alles stehen bleibt.

## Die Grenze aus D-18, wörtlich

> `occ app_api:app:unregister mcp_connector --rm-data` entfernt das Volume und mit ihm die
> Log-Datei, weil sie nach D-01 neben dem OAuth-Speicher liegt. Dasselbe gilt für das
> Entfernen über die Oberfläche auf Nextcloud 32 und 33 mit gesetztem Haken "Delete data on
> remove". Das ausdrückliche Löschen der Daten durch den Administrator ist kein Fall, gegen
> den diese Phase schützt.

Belege, alle in `docs/uninstall.md`:

| Zeile | Aussage |
|-------|---------|
| `:19` | Der Runbook-Schritt selbst: `occ app_api:app:unregister mcp_connector --rm-data`, ausdrücklich als "remove the app, together with its volume" |
| `:47` | Nextcloud 32 und 33: das Kästchen "Delete data on remove" ruft den Deinstallationspfad mit `removeData=true`, das Volume geht |
| `:48` | Nextcloud 34: der Weg der Oberfläche ist `disableExApp`, der Container hält an, Volume, Schlüssel und App-Passwörter bleiben |
| `:229-235` | Der Hilfetext des Gegenstücks, zitiert: "Keep ExApp data (volume) [deprecated, data is kept by default]" - ohne das Flag bleibt das Volume; dazu die vier gemessenen Gegenproben nach dem Lauf mit Flag |

`docs/uninstall.md` ist in dieser Phase **nicht** geändert worden und wird es hier auch
nicht: der Textnachzug ist AUDIT-06 und gehört zu Phase 19.

## Messung zu A2: was ein Eintrag im Schreibpfad kostet

```
uv run --no-sync python -c "... 100 Einträge über AuditStore.append ..."
8,65 ms je Eintrag, 100 Einträge, Windows 11, Python 3.13.13 (NTFS)
```

Hundert Einträge über die öffentliche Schnittstelle, also je Eintrag eine frische
Verbindung, `BEGIN IMMEDIATE`, `COMMIT`, `close`, das Muster von `oauth/store.py::_call`.
Die Recherche misst für dieselbe Form 7,2 ms (18-RESEARCH.md §8); die 8,65 ms dieses Laufs
liegen in derselben Grössenordnung, der Unterschied ist die Kette (ein Lesevorgang mehr je
Zeile) und die Tageslast dieses Rechners.

**Im Container ungemessen.** A2 nennt die Windows-Zahl ausdrücklich eine Obergrenze und
keine Vorhersage für den Linux-Container auf einem Docker-Volume, wo das Öffnen einer
SQLite-Datei erfahrungsgemäss deutlich billiger ist. Die Nachmessung im Container ist damit
weiterhin offen, und das ist ein zulässiger Ausgang: selbst 8,65 ms je Werkzeugaufruf
laufen in `asyncio.to_thread`, also ohne Blockade der Ereignisschleife, gegen
Nextcloud-Antwortzeiten im zwei- bis dreistelligen Millisekundenbereich.

**Kein Testfall hängt an dieser Zahl.** `grep -nE "perf_counter|time\.time\(\)"
tests/unit/test_audit_store.py` liefert keine Zeile. Eine Zeitschwelle in einem Testfall
wäre auf fremder Hardware eine Zufallszahl; die Messung ist eine Beleg-Zeile, keine
Zusicherung.

## Was diese Phase nicht geliefert hat, und wer es liefert

| Offen | Anforderung | Wer |
|-------|-------------|-----|
| Lesen und Exportieren des Logs | AUDIT-04 | Phase 19 |
| Die sichtbare Beschriftung samt Mitbestimmungshinweis | AUDIT-05 | Phase 19 |
| Der Textnachzug in `docs/privacy.md` und `docs/uninstall.md` | AUDIT-06 | Phase 19 |
| Die Auslieferung als 0.1.12 | EXAPP-12 | ausserhalb des Meilensteins v1.5 |

Dazu die Nachmessung der Schreibkosten im Linux-Container (A2) und die Messung von A1 im
CI-Job `exapp`, beide angelegt und beide nicht auf diesem Rechner zu haben.

## Decisions Made

- **Der Kettenfall liest die Zeilen zuerst.** `verify_chains()` öffnet die Datei, legt das
  Schema an, wenn es fehlt, und findet dann nichts zu melden. Eine leere Befundliste allein
  ist also auch das Bild eines gelöschten Logs. Deshalb behauptet der Fall zuerst die
  Zeilenanzahl an der Ablage vorbei und erst dann die leere Liste. Gefunden wurde das in
  der Gegenprobe, nicht durch Nachdenken (siehe Abweichung 1).
- **Die Gegenprobe lief über eine Sicherungskopie.** Kein `git stash`, kein `git clean`:
  beide sind in diesem Projekt aus gutem Grund verboten. Kopie anlegen, Zeile einfügen,
  vier rote Fälle beobachten, Kopie zurückspielen, `git diff --stat` prüfen.
- **Der grep-Befund steht in der SUMMARY.** Der Plan erwartet keine Zeile und bekommt eine.
  Sie wegzulassen hiesse, die Prüfung an die Erwartung anzupassen. Stattdessen steht sie
  hier mit ihrer Bedeutung, und daneben die schärfere Fassung, die wirklich keine trifft.
- **Der Nachbar-Fall benutzt die echte Rotation.** `redeem_refresh_token` ist die eine
  Schreiboperation, die im laufenden Betrieb nicht scheitern darf, und sie schreibt in
  derselben Transaktion die Nachfolgerzeile. Ein blosses `save_client` hätte weniger
  gesagt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing coverage] Der Kettenfall wäre auch bei gelöschtem Log grün gewesen**

- **Found during:** Task 1, in der Gegenprobe
- **Issue:** Die erste Fassung von
  `test_the_chains_of_the_audit_log_are_unbroken_after_the_purge` behauptete nur
  `verify_chains() == []`. Mit der eingefügten Löschzeile in `purge.py` blieb dieser Fall
  **grün**, während die drei anderen rot wurden: `AuditStore.verify_chains` öffnet die
  Datei, legt bei einer fehlenden das Schema neu an und meldet über eine leere Tabelle
  völlig zu Recht nichts. Ein Fall, der bei gelöschter Datei grün bleibt, belegt das
  Gegenteil dessen, was er behauptet.
- **Fix:** Der Fall behauptet jetzt zuerst `len(live.audit_rows()) == Deployment.AUDIT_ROWS`
  (Lesen mit einer eigenen `sqlite3`-Verbindung, das an einer fehlenden Tabelle hart
  scheitert) und erst danach die leere Befundliste. Der Docstring sagt, warum diese
  Reihenfolge die Aussage trägt.
- **Files modified:** tests/unit/test_exapp_purge.py
- **Verification:** Mit der Löschzeile werden **alle vier** Fälle rot; ohne sie sind alle
  vier grün, und `git diff --stat src/mcp_connector/exapp/purge.py` ist leer.
- **Committed in:** `f358bec` (Task-1-Commit)

### Befunde ohne Änderung

**2. [Befund] Der grep aus dem Prüfblock des Plans trifft eine Zeile**

- **Found during:** Task 3
- **Erwartung des Plans:** `grep -rniE "audit|AUDIT_FILENAME|audit\.sqlite3"` über
  `oauth/connections.py`, `exapp/purge.py` und `exapp/lifecycle.py` "liefert keine Zeile".
- **Gemessen:** eine Zeile, `src/mcp_connector/exapp/lifecycle.py:117`. Es ist der Text
  einer Logzeile aus Plan 18-08 ("the purge and the audit log check are missing"), also
  eine Zeichenkette und kein Zugriff. Der Plan selbst sieht diesen Ausgang vor: "Trifft der
  grep doch, ist das ein Befund und gehört als solcher in die SUMMARY, nicht weggelassen."
- **Folge:** keine Codeänderung. Die Herleitung zu Zeile 5b der Nachweistabelle steht
  jetzt auf zwei Läufen: dem wörtlichen aus dem Plan samt seinem einen Treffer und der
  schärferen Fassung über `AUDIT_FILENAME`, `audit.sqlite3`, `AuditStore` und die
  Importformen, die keine Zeile trifft.
- **Files modified:** keine

---

**Total deviations:** 1 auto-fixed (Rule 2), 1 Befund ohne Änderung
**Impact on plan:** Keine Erweiterung des Auftrags. Die Abweichung macht einen Fall wahr,
der sonst das Gegenteil seiner Behauptung belegt hätte; der Befund präzisiert einen
Prüfschritt, ohne die Aussage zu ändern.

## Issues Encountered

- Die vier neuen Fälle in `test_exapp_purge.py` liefen beim ersten Lauf sofort grün. Das
  ist bei einem TDD-Zuschnitt normalerweise ein Warnsignal, hier aber die Aussage des Plans
  selbst: `purge.py` darf nicht geändert werden, das Überleben ist eine bestehende
  Eigenschaft, und der rote Beleg ist deshalb nicht ein fehlender Handler, sondern die
  Gegenprobe mit einem Handler, der die Datei anfassen würde. Siehe den Abschnitt zur
  TDD-Gate-Lage unten.
- `AuditStore.verify_chains` legt eine fehlende Datei stillschweigend neu an. Das ist für
  den Betrieb richtig (das Prüfkommando soll nicht an einer noch nie beschriebenen Ablage
  scheitern) und für einen Test über das Überleben eine Falle. Sie steht jetzt als Satz im
  Docstring des Falls.

## TDD Gate Compliance

Task 1 trägt `tdd="true"`, und die übliche Reihenfolge ist hier nicht erreichbar: der Plan
verbietet ausdrücklich jede Änderung an `src/mcp_connector/exapp/purge.py`, es gibt also
keine Implementierung, die von rot auf grün gebracht werden könnte. Der RED-Gate ist
stattdessen als **Gegenprobe** geführt worden, und er ist damit strenger als ein
gewöhnlicher roter Lauf: nicht "der Fall ist rot, weil noch nichts da ist", sondern "der
Fall wird rot, sobald der bestehende Handler die Datei anfasst". Beide Commits dieser Phase
tragen deshalb `test(...)` und keinen `feat(...)`-Gegenpart, und das ist die Wahrheit über
diesen Plan: er fügt keine Funktion hinzu, er hält eine bestehende fest.

## Anforderungen

Dieser Plan legt **keine** neue Anforderung ab. AUDIT-01, AUDIT-02 und AUDIT-03 sind mit
den Plänen 18-07 und 18-08 abgelegt worden; was hier entsteht, ist der Beleg, dass alle
drei mit ihren Erfolgskriterien wirklich eingelöst sind, und die Trennung von getestet und
hergeleitet, damit Phase 19 das eine nicht für das andere hält.

## Threat Flags

Keine neue Fläche: diese Phase hat in diesem Plan nur Testdateien angefasst. Die
`mitigate`-Fäden des Plans sind eingelöst, die `accept`-Fäden stehen beim Namen:

| Faden | Disposition | Wo eingelöst |
|-------|-------------|--------------|
| T-18-22 | mitigate | Vier Fälle halten das Überleben beim Purge; `purge.py` unverändert; Gegenprobe geführt |
| T-18-25 | accept | Der grep über die drei Aufräumpfade plus `18-RESEARCH.md` §11; die Nachweistabelle weist Zeile 5b ausdrücklich als hergeleitet aus |
| T-18-05 | mitigate | `test_the_oauth_store_still_rotates_and_connects_after_the_bound_bit` |
| T-18-23 | accept | Die Grenze aus D-18 steht wörtlich in dieser SUMMARY, mit vier Zeilenverweisen auf `docs/uninstall.md` |
| T-18-24 | mitigate | Budget-Stillstand vor und nach der Phase; `check_tool_budget.py` und `test_tool_surface.py` über zehn Pläne unverändert |
| T-18-SC | mitigate | `git diff --stat 9d9be78 HEAD -- pyproject.toml uv.lock` leer; kein Paket installiert |

## Known Stubs

Keine.

## Verification

- `uv run --no-sync pytest tests/unit/test_exapp_purge.py -q` - grün, 78 Fälle
- `uv run --no-sync pytest tests/unit/test_audit_store.py -q` - grün, 16 Fälle
- `git diff --stat src/mcp_connector/exapp/purge.py` - leer
- Die sieben Gates - siehe Tabelle oben, alle grün
- `git diff --stat scripts/check_tool_budget.py tests/contract/test_tool_surface.py docs/uninstall.md docs/privacy.md` - leer
- `git status --short pyproject.toml uv.lock docs/ CHANGELOG.md appinfo/` - leer
- `grep -nE "perf_counter|time\.time\(\)" tests/unit/test_audit_store.py` - keine Zeile
- Der grep zu Zeile 5b - eine Zeile, oben genannt und eingeordnet; die schärfere Fassung
  ohne Treffer
- `grep -rniE "\barchiv" .planning/phases/18-audit-log-kern/18-10-SUMMARY.md` - ohne Treffer

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 19 findet fünf belegte Erfolgskriterien vor und eine Tabelle, die sagt, welcher
  Beleg ein Test ist und welcher eine Herleitung. Zeile 5b darf dort nicht zu "geprüft"
  werden, ohne dass ein Test dazukommt.
- Der Textnachzug (AUDIT-06) hat seine Vorlage: die wörtliche Grenze aus D-18 mit ihren
  vier Zeilenverweisen steht oben und muss für `docs/privacy.md` und `docs/uninstall.md`
  nicht neu formuliert werden.
- Das Werkzeugbudget ist die Rahmenbedingung des ganzen Meilensteins und steht bei 15712
  von 18000. Phase 19 legt kein Werkzeug an und erbt diese Zahl.

## Self-Check

- `tests/unit/test_exapp_purge.py` - FOUND
- `tests/unit/test_audit_store.py` - FOUND
- `.planning/phases/18-audit-log-kern/18-10-SUMMARY.md` - FOUND
- Commit `f358bec` - FOUND
- Commit `bb87187` - FOUND

## Self-Check: PASSED

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
