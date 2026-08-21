---
phase: 08-erreichbarkeits-spike-und-tables
fixed_at: 2026-08-21T09:11:09Z
review_path: .planning/phases/08-erreichbarkeits-spike-und-tables/08-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
deferred: 5
status: all_fixed
---

# Phase 8: Code Review Fix Report

**Fixed at:** 2026-08-21T09:11:09Z
**Source review:** `.planning/phases/08-erreichbarkeits-spike-und-tables/08-REVIEW.md`
**Iteration:** 1

**Zusammenfassung:**
- Befunde im Auftragsumfang: 11 (WR-01 bis WR-07, IN-01 bis IN-04)
- Behoben: 11
- Übersprungen: 0
- Zurückgestellt (ausserhalb Auftragsumfang): 5 (IN-05 bis IN-09)

Alle Gates liefen nach dem letzten Fix grün: komplette Test-Suite (`uv run python -m pytest -q`),
`ruff check .`, `ruff format --check .` (181 Dateien), `pyright` (0 errors), `vulture src scripts
vulture_whitelist.py` und `scripts/check_tool_budget.py` (12801 Bytes, 18 Tools, Budget 15000).

## Behobene Befunde

### WR-01: Stille Trunkierung, wenn Tables kein `rowsCount` liefert

**Dateien:** `src/mcp_connector/tools/tables.py`, `tests/unit/test_tables_tools.py`
**Commit:** `48cfbce`
**Angewandter Fix:** `_row_count` liefert `int | None` statt eines Fallbacks, der das Lesefenster
als Tabellengrösse ausgibt. `rowsCount` fällt aus der Antwort, wenn die App keinen brauchbaren Wert
meldet, und die Trunkierungsprüfung nutzt dann das volle Lesefenster als Signal. Der Modul-Docstring
sagt das jetzt auch.
**Tests:** `test_a_full_window_is_named_as_truncated_even_without_a_row_count` (vier Formen: Feld
fehlt, String, bool, negativ) und `test_a_window_that_was_not_filled_is_the_end_of_the_table`.

### WR-02: `next`-Cursor kann identisch zum aktuellen Cursor sein

**Dateien:** `src/mcp_connector/tools/tables.py`, `tests/unit/test_tables_tools.py`
**Commit:** `5f3788d`
**Angewandter Fix:** `bool(results)` steht jetzt vor beiden Zweigen der Trunkierungsprüfung, also
gibt eine Seite, die nichts trug, kein Handle mehr aus. Der Kommentar nennt den Grund (driftender
Zeilenzähler der Tables-App) statt ihn zu verstecken.
**Test:** `test_a_page_that_carried_nothing_hands_out_no_handle_of_its_own_offset` (Offset 25,
`rowsCount` 342, null Zeilen).

### WR-03: Marker-Filter greift nicht bei Nicht-String-Zellwerten und `selectionOptions`

**Dateien:** `src/mcp_connector/tools/tables.py`, `tests/unit/test_tables_tools.py`
**Commit:** `2b60ac5`
**Angewandter Fix:** Neue Funktion `_clean` filtert rekursiv über Listen und Objekte bis zum letzten
Blatt-String und lässt Zahlen, bools und `None` unverändert. Angewandt in `_row` (statt der
`isinstance(value, str)`-Abfrage) und auf alle `_COLUMN_LIMITS`-Werte, also auch auf die Labels der
Auswahloptionen.
**Tests:** `test_a_marker_is_removed_from_a_cell_that_is_not_a_plain_string` (Liste mit
verschachteltem Objekt, Zahl bleibt Zahl) und
`test_a_marker_in_a_selection_option_label_is_removed_as_well`.

### WR-04: Fehlende Spalten-ID wird zu `"None"` und träfe Spalte 0

**Dateien:** `src/mcp_connector/tools/tables.py`, `tests/unit/test_tables_tools.py`
**Commit:** `c9a7abf`
**Angewandter Fix:** `_by_column_id` prüft die Spalten-ID auf echtes `int` (bool ausgeschlossen) und
lehnt sonst mit dem neuen `_COLUMN_ID_HINT` ab, bevor irgendetwas geschrieben wird. Die
Fehlermeldung nennt den betroffenen Titel. Der Docstring beschreibt den zweiten Eingang derselben
Falle (T-08-15 eine Ebene tiefer).
**Test:** `test_a_column_without_a_numeric_id_is_refused_instead_of_written` (drei Formen: Feld
fehlt, String-ID, bool), mit Nachweis, dass kein POST hinausgeht.

### WR-05: Destruktiv-Gate fängt die projektübliche f-String-Schreibweise nicht

**Dateien:** `tests/contract/test_no_destructive_calls.py`
**Commit:** `48d5d5c`
**Angewandter Fix:** Alle Tables-Needles sind vom öffnenden Anführungszeichen gelöst und auf
Pfadsegmente verankert: `"/rows/"`, `"/columns/"` und neu `"/scheme"` statt `"tables/scheme"`. Das
dritte Needle `'"/rows/'` hatte dieselbe Lücke und ist mitgezogen worden, weil das Argument des
Reviews wörtlich auf es zutrifft. Der Preis ist eine schmale Ausnahme `TABLES_READ_FORMS`: zwei
exakte Literale (der Zeilen-Lesepfad der Generation 1 und die Spaltenliste einer Tabelle) in genau
einer Datei, gültig nur für die zwei Segment-Needles, nie für `DELETE`, `/transfer` oder `/share`.
Vorher per Grep verifiziert, dass `/rows/`, `/columns/` und `/scheme` in `src/` nirgends sonst
vorkommen.
**Tests:** `test_the_tables_read_exemption_covers_two_call_forms_and_nothing_else` (Gegenprobe: die
zwei erlaubten Literale ja, ein Nachbarpfad im selben Segment nein, dieselbe Zeile in einer anderen
Datei nein), `TABLES_ROUTES` auf die f-String-Schreibweise umgestellt (fünf Counter-Proofs), und
`test_the_three_routes_the_tables_client_really_builds_stay_allowed` deckt jetzt auch den
Spalten-Lesepfad ab.

### WR-06: Abnahmeskript kann bei Tables fälschlich FAIL melden

**Dateien:** `scripts/acceptance_all_tools.py`
**Commit:** `c316ac2`
**Angewandter Fix:** `_first_text_column` ist ersetzt durch `_writable_tables` (filtert auf
`can_create`, in Listenreihenfolge) und `_text_row_for` (alle Pflichtspalten müssen vom Typ `text`
sein, und die geschriebene Zeile deckt jede davon ab; ohne Pflichtspalte genügt eine Textspalte).
Der Tables-Schritt probiert die Kandidaten der Reihe nach und schreibt in den ersten, der passt.
Passt keiner, ist es ein `SKIP` mit Begründung, genau wie bei Deck. Der Modul-Docstring nennt
Tables jetzt als zweite Ausnahme samt beider Hälften der Prüfung.

### WR-07: READMEs (EN/DE/FR) kennen Tables nicht und zählen fünf Tools

**Dateien:** `README.md`, `README.de.md`, `README.fr.md`
**Commit:** `6ddc4a8`
**Angewandter Fix:** Alle drei Sprachfassungen synchron: "Notes, Deck and Tables are optional
Nextcloud apps" (DE "Notes, Deck und Tables sind optionale Nextcloud-Apps", FR "Notes, Deck et
Tables sont des applications Nextcloud optionnelles"), die Tables-Fehlermeldung "The Tables app is
not enabled on this Nextcloud." als zweites Beispiel, und in der Limitations-Tabelle "ignore those
seven tools" / "diese sieben Tools" / "ces sept outils".

### IN-01 bis IN-04: veraltete Toolzahlen und Docstrings

**Dateien:** `docs/client-setup.md`, `docs/oauth-setup.md`, `docs/conference-talk.md`,
`src/mcp_connector/nextcloud/capabilities.py`, `src/mcp_connector/nextcloud/clients/ocs.py`
**Commit:** `ba93d80`
**Angewandter Fix:**
- IN-01: `client-setup.md` sagt "16 at the time of that run" und verweist getrennt davon auf
  `tests/contract/test_tool_surface.py` als aktuelle Wahrheit.
- IN-02: `oauth-setup.md` Zeile 708 lautet jetzt "The set is 18 today" mit derselben Begründung wie
  Zeile 459 (`prepare_context` plus die zwei Tables-Tools).
- IN-03: `conference-talk.md` sagt auf Folie 6, in der Sprechernotiz und in der Belegtabelle
  "Sixteen tools in the released 0.1.2, eighteen in the development tree". Die Versionsangabe 0.1.2
  bleibt, damit das Dokument datierbar bleibt.
- IN-04: der Modul-Docstring von `capabilities.py` nennt Tables samt `enabled`-Prüfung, der
  Docstring von `parse_app_json` nennt die Generation-1-Zeilenroute von Tables.

## Zurückgestellte Befunde

Alle fünf liegen ausserhalb des Auftragsumfangs dieses Fix-Laufs (nur triviale, risikofreie
Info-Befunde waren mitzunehmen). Die Begründung steht zusätzlich am jeweiligen Befund in
`08-REVIEW.md`.

| Befund | Grund |
|--------|-------|
| IN-05 `_path_id` akzeptiert Unicode-Ziffern | Codeänderung im Client mit eigener Testpflicht über alle Pfade; kein Sicherheits- oder Korrektheitsproblem (harmloses 404) |
| IN-06 Abnahmeskript dupliziert die Toolmenge | Umbau der Wahrheitsquelle, Struktur-Entscheidung statt Zahlenkorrektur |
| IN-07 `truncated` ohne Handle auf `tables`/`columns` | Erweiterung des Antwortformats von `tables_browse`, gehört in eine geplante Änderung |
| IN-08 gleichnamige Spaltentitel kollidieren still | Verlangt eine Entscheidung über die Schlüsselbildung im Zeilenobjekt, also über das Antwortformat |
| IN-09 `tables_available` hängt an `enabled` | Der Befund nennt selbst keinen nötigen Codefix; die fail-closed-Annahme ist gegen 2.2.2 gemessen und begründet |

## Hinweis zur Nachprüfung

WR-01, WR-02 und WR-06 sind Logikänderungen: die Bedingungen sind je durch einen Test für den
Fehlerfall belegt, die Entscheidung selbst (voll gefülltes Fenster als Trunkierungssignal, kein
Handle auf einer leeren Seite, Pflichtspalten-Abdeckung als Auswahlkriterium) sollte ein Mensch
einmal gegenlesen.

---

_Fixed: 2026-08-21T09:11:09Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
