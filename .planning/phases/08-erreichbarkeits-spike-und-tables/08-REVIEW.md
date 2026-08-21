---
phase: 08-erreichbarkeits-spike-und-tables
reviewed: 2026-08-21T08:53:17Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - .github/workflows/ci.yml
  - CHANGELOG.md
  - README.de.md
  - README.fr.md
  - README.md
  - docs/client-setup.md
  - docs/conference-demo.md
  - docs/conference-talk.md
  - docs/oauth-setup.md
  - docs/spike-mail.md
  - docs/store-submission.md
  - scripts/acceptance_all_tools.py
  - scripts/bootstrap_exapp.sh
  - scripts/bootstrap_test_nc.sh
  - scripts/check_tool_budget.py
  - src/mcp_connector/nextcloud/capabilities.py
  - src/mcp_connector/nextcloud/clients/ocs.py
  - src/mcp_connector/nextcloud/clients/tables.py
  - src/mcp_connector/server/reg_tables.py
  - src/mcp_connector/tools/tables.py
  - tests/contract/test_no_destructive_calls.py
  - tests/contract/test_tool_surface.py
  - tests/fixtures/tables_columns.json
  - tests/fixtures/tables_rows_simple.json
  - tests/fixtures/tables_tables.json
  - tests/integration/test_exapp_mail_reach.py
  - tests/integration/test_permission_fidelity_exapp.py
  - tests/integration/test_tables_roundtrip.py
  - tests/unit/test_ocs_capabilities.py
  - tests/unit/test_tables_client.py
  - tests/unit/test_tables_tools.py
  - vulture_whitelist.py
findings:
  critical: 0
  warning: 7
  info: 9
  total: 16
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-08-21T08:53:17Z
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

Geprüft wurde die neue Tables-Familie (Client, Tool-Schicht, Registrierung, Capabilities-Erweiterung), die OCS-Statusbehandlung, der Mail-Erreichbarkeits-Spike samt Doku, die beiden Bootstrap-Skripte, die Gates (Destruktiv-Gate, Tool-Surface, Tool-Budget) sowie die dreisprachigen READMEs und die betroffenen Doku-Seiten.

Gesamtbild: Die Kernlogik der Tables-Familie ist sorgfältig gebaut. Die Berechtigungsvorprüfung (K5, Owner vs. Share), die Node-Type/Node-Collection-Trennung (K3), das erzwungene Limit, der Cursor-Scope-Check und das Fehlen jeglicher Update-/Delete-/Share-Pfade sind konstruktiv abgesichert und durch Unit-, Contract- und Integrationstests belegt. Keine Critical-Befunde.

Es bleiben sieben Warnungen: zwei Randfälle der Zeilen-Paginierung, die die eigene Zusage "Trunkierung wird benannt, nie still" bzw. die Cursor-Semantik brechen können, eine Lücke im Marker-Filter (T-08-14) für Nicht-String-Zellwerte und Auswahloptions-Labels, ein Blindfleck im Destruktiv-Gate, den die eigenen Testdateien vorführen, ein möglicher Fehlalarm im Abnahmeskript sowie in allen drei READMEs eine veraltete "Optionale Apps"-Aussage, die Tables nicht kennt. Dazu neun Info-Befunde, überwiegend Doku-Drift bei Toolzahlen und veraltete Docstrings.

## Warnings

### WR-01: Stille Trunkierung, wenn Tables kein `rowsCount` liefert

**File:** `src/mcp_connector/tools/tables.py:324-352`
**Issue:** `_rows` entscheidet über `truncated`/`next` ausschließlich per `rowsCount > offset + len(results)`. Fehlt `rowsCount` in der Antwort (oder ist es kein int), setzt `_row_count` den Fallback exakt auf `offset + len(results)`, die Bedingung ist damit nie wahr. Eine Tabelle mit 100 Zeilen und `limit=25` liefert dann 25 Zeilen, meldet `rowsCount: 25`, keine Trunkierung und kein `next`. Das widerspricht direkt der Modul-Zusage "Truncation is named here, never silent" und ist für das Modell unerkennbar falsch.
**Fix:** Wenn `rowsCount` fehlt, das Signal aus dem Lesefenster ableiten: bei `len(results) == limit` `truncated: true` plus `next`-Handle setzen und `rowsCount` weglassen statt zu erfinden:
```python
count = info.get("rowsCount")
known = isinstance(count, int) and not isinstance(count, bool) and count >= 0
if known:
    answer["rowsCount"] = count
if (known and count > offset + len(results)) or (not known and len(results) == limit):
    answer["truncated"] = True
    answer["next"] = paging.encode_cursor({"o": offset + len(results), "t": table})
```

### WR-02: `next`-Cursor kann identisch zum aktuellen Cursor sein (Endlosschleifen-Klasse)

**File:** `src/mcp_connector/tools/tables.py:327-329`
**Issue:** Liefert `rows/simple` bei einem Offset null Zeilen, während das (in Tables nachweislich drift-anfällige) Zählerfeld `rowsCount` noch `> offset` meldet, gilt `rowsCount > offset + 0`, und `next` wird mit `o = offset + 0` ausgegeben, also exakt der eingereichte Cursor. Ein Client, der `next` folgt, solange es gesetzt ist (genau das Muster von `_row_with_task` und `_rows` in den eigenen Integrationstests, dort nur durch das harte `range(50)` begrenzt), dreht sich im Kreis.
**Fix:** `next` nur ausgeben, wenn die aktuelle Seite Ergebnisse trug:
```python
if results and answer["rowsCount"] > offset + len(results):
    answer["truncated"] = True
    answer["next"] = paging.encode_cursor({"o": offset + len(results), "t": table})
```

### WR-03: Marker-Filter (T-08-14) greift nicht bei Nicht-String-Zellwerten und `selectionOptions`-Labels

**File:** `src/mcp_connector/tools/tables.py:288-292, 341-343`
**Issue:** `_row` wendet `_text` (also `marks.without_marks`) nur auf `isinstance(value, str)` an; jeder andere Wert geht roh in den Modellkontext (`row[title] = value`). Ebenso reicht `_column` die `selectionOptions` samt Labels ungefiltert durch (`entry[key] = value`). Beide Stellen tragen fremden Text von Personen, die in die Tabelle schreiben bzw. sie verwalten dürfen, genau die Fläche, die das Modul selbst als T-08-14 benennt. Ein Marker-String in einem Auswahloptions-Label oder in einem Listen-/Objekt-Zellwert (z. B. Mehrfachauswahl) umgeht den Filter vollständig.
**Fix:** Rekursiv filtern statt typabhängig:
```python
def _clean(value: Any) -> Any:
    if isinstance(value, str):
        return marks.without_marks(value)
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    return value
```
und in `_row` sowie für `_COLUMN_LIMITS`-Werte (mindestens `selectionOptions`) anwenden.

### WR-04: Fehlende Spalten-ID wird zu `"None"` und träfe per PHP-`(int)`-Cast Spalte 0

**File:** `src/mcp_connector/tools/tables.py:210`
**Issue:** `data[str(column.get("id"))] = value` erzeugt bei einem Spaltenobjekt ohne `id` den Schlüssel `"None"`. Die Tables-App castet jeden Schlüssel mit `(int)`, `(int)"None"` ist `0`, der Wert landet still in Spalte 0. Das ist exakt die Falle, die der eigene Docstring als T-08-15 beschreibt ("a title would silently become the column 0"), nur eine Ebene tiefer. Der Fall setzt eine deformierte Serverantwort voraus, aber die restliche Schicht behandelt genau solche Antworten überall defensiv (`_as_list`, `_as_dict`, `_path_id`).
**Fix:** ID vor dem Eintragen prüfen und sonst ablehnen:
```python
column_id = column.get("id")
if not isinstance(column_id, int) or isinstance(column_id, bool):
    raise ToolError(
        message=f"Table {table} answered a column without a numeric id.",
        hint=_SHAPE_HINT,  # der Shape-Hint des Clients
    )
data[str(column_id)] = value
```

### WR-05: Destruktiv-Gate: zwei Tables-Needles fangen die projektübliche Schreibweise nicht

**File:** `tests/contract/test_no_destructive_calls.py:45-76`
**Issue:** Die Needles `'"/columns/'` und `"tables/scheme"` sind auf die öffnende Anführungszeichen-Schreibweise bzw. auf wörtliche Nachbarschaft angewiesen. Die projektübliche Schreibweise umgeht beide: ein Spalten-Write würde als `ocs.ocs_post(client, creds, f"{V2_PREFIX}/columns/{column_id}", ...)` geschrieben (genau so bauen `tests/integration/test_tables_roundtrip.py:170` und `test_permission_fidelity_exapp.py:383` heute ihre Scaffolding-Routen, dort legitim), und der Schema-Export je Tabelle als `f"{V2_PREFIX}/tables/{table}/scheme"` enthält den String `tables/scheme` nicht. Der Kommentar im Gate behauptet, eine solche Route könne "hardly be written" ohne die Needle zu treffen; die eigenen Testdateien sind das Gegenbeispiel. Damit ist die Zusage "no tool may create, change or delete a Tables column" und "no tool may import or export a table scheme" nur teilweise maschinell gedeckt.
**Fix:** Needles vom öffnenden Anführungszeichen lösen und auf Pfadsegmente ankern, z. B. `"/columns/"` als Needle mit expliziter Ausnahme für die eine erlaubte Lese-Route (`f"{V2_PREFIX}/columns/{NODE_TYPE_TABLE}/"`) nach dem Muster der bestehenden SQL-/DELETE-Ausnahmen, und `"/scheme"` als eigene Needle ergänzen. Die Counter-Proof-Tests um die evasive Schreibweise `f"{V2_PREFIX}/columns/{column}"` erweitern, damit die Lücke nicht zurückkehrt.

### WR-06: Abnahmeskript kann bei Tables fälschlich FAIL melden

**File:** `scripts/acceptance_all_tools.py:194-214, 227-244`
**Issue:** Der Tables-Schritt nimmt per `_first_id` die erste Tabelle, ohne `can_create` zu prüfen, und per `_first_text_column` die erste Textspalte, ohne die Pflichtspalten der Tabelle abzudecken. Zwei realistische Konstellationen erzeugen dann ein `FAIL`, obwohl der Connector korrekt arbeitet: (a) die erste gelistete Tabelle ist eine ohne Schreibrecht geteilte, `tables_create_row` verweigert wie designt; (b) die erste Textspalte ist nicht die einzige Pflichtspalte, die Pflichtspalten-Verweigerung greift. Beides widerspricht der eigenen SKIP-Philosophie des Skripts ("no table with a text column ... by design").
**Fix:** Tabelle nach `can_create` filtern und die Pflichtspalten mitschreiben:
```python
entries = tables.get("results") or []
table = next((t for t in entries if t.get("can_create")), None)
```
und in `_first_text_column` bevorzugt eine Tabelle wählen, deren Pflichtspalten alle vom Typ `text` sind, sonst `SKIP` mit Begründung.

### WR-07: READMEs (EN/DE/FR): "Optionale Apps" kennt Tables nicht, "diese fünf Tools" ist falsch

**File:** `README.md:347-351, 378` (ebenso `README.de.md:356-362, 390` und `README.fr.md:367-369, 404`)
**Issue:** Der Abschnitt "Optional apps" sagt "Notes and Deck are optional Nextcloud apps", und die Zeile in "Known limitations" sagt "Notes and Deck are optional apps ... ignore those five tools". Seit dieser Phase ist Tables die dritte optionale App mit eigener Capabilities-Prüfung und eigener Fehlermeldung ("The Tables app is not enabled on this Nextcloud."), und die Zahl der betroffenen Tools ist sieben (3 Notes, 2 Deck, 2 Tables), nicht fünf. Die Tool-Tabelle derselben Seite listet beide Tables-Tools bereits, die Seite widerspricht sich also selbst. Der Fehler steht identisch in allen drei Sprachfassungen (Regel: Übersetzungen nachziehen).
**Fix:** In allen drei READMEs: "Notes, Deck and Tables are optional Nextcloud apps ..." und in der Limitations-Zeile "ignore those seven tools" (DE: "diese sieben Tools", FR: "ces sept outils"), plus die Tables-Fehlermeldung als zweites Beispiel nennen.

## Info

### IN-01: client-setup.md behauptet, der Contract-Test halte die Zahl 16

**File:** `docs/client-setup.md:713-715`
**Issue:** "Note the number of tools it lists, 16 at the time of writing, which is the number `tests/contract/test_tool_surface.py` holds" ist seit dieser Phase falsch: die Datei hält 18. Das Zahlen-Gate (`test_a_documented_tool_count_is_the_current_one_...`) wird hier durch den bloßen Verweis auf die Holder-Datei grün, obwohl die Aussage über die Holder-Datei selbst falsch ist.
**Fix:** Formulierung entkoppeln: "..., 16 at the time of that run; the current number is held by `tests/contract/test_tool_surface.py`."

### IN-02: oauth-setup.md nennt im selben Dokument "18 today" und "The set is 16"

**File:** `docs/oauth-setup.md:707-709` (vs. `459-461`)
**Issue:** Zeile 459 wurde auf "The set is 18 today" aktualisiert, Zeile 708 sagt weiter "The set is 16 since `prepare_context` arrived". Interner Widerspruch.
**Fix:** Zeile 708 analog zu 459 formulieren ("The set is 18 today; ...").

### IN-03: conference-talk.md paart "Eighteen tools" mit Version 0.1.2

**File:** `docs/conference-talk.md:31, 105-112, 185`
**Issue:** Der Talk beansprucht "Every product claim below is measured" und nennt Version 0.1.2 (Folie 1, sowie "No claim about a store release beyond 0.1.2"), gleichzeitig wurde Folie 6 auf "Eighteen tools" gehoben. Eine 0.1.2/0.1.3-Installation aus dem Store listet 16 Tools; 18 gibt es nur im unreleasten Stand. Für ein Dokument mit diesem Anspruch ist das eine messbare Inkonsistenz.
**Fix:** Entweder Folie 6 auf "Sixteen tools (eighteen in the development tree)" präzisieren oder das ganze Dokument auf den Stand eines Releases datieren.

### IN-04: Veraltete Docstrings: capabilities.py und ocs.py kennen Tables nicht

**File:** `src/mcp_connector/nextcloud/capabilities.py:3-11` und `src/mcp_connector/nextcloud/clients/ocs.py:14-17`
**Issue:** Der Modul-Docstring von capabilities.py sagt "Only Notes and Deck are checked here, on purpose", während das Modul Tables prüft (Dataclass-Felder, `_MISSING["tables"]`, `parse`). Der ocs.py-Docstring beschreibt `parse_app_json` als "for Notes and Deck", während die Tables-Generation-1-Route ihn ebenfalls nutzt.
**Fix:** Beide Docstrings um Tables ergänzen.

### IN-05: `_path_id` akzeptiert Unicode-Ziffern

**File:** `src/mcp_connector/nextcloud/clients/tables.py:210-218`
**Issue:** `str.isdigit()` ist wahr für Superscripts und fremde Ziffernsysteme ("²", "٧"). Solche Werte passieren die Prüfung, erzeugen aber nie eine gültige Route (harmloses 404). Kein Sicherheitsproblem, da keine Pfad-Metazeichen durchkommen, aber die Fehlermeldung würde den eigentlichen Fehler verdecken.
**Fix:** `text.isascii() and text.isdigit()` (oder `isdecimal()` plus ASCII-Check).

### IN-06: Abnahmeskript dupliziert die 18er-Toolmenge

**File:** `scripts/acceptance_all_tools.py:47, 271-290`
**Issue:** `EXPECTED_TOOLS = 18` und das wörtlich duplizierte `expected`-Set stehen neben der Quelle der Wahrheit in `tests/contract/test_tool_surface.py`. Genau diese Duplikatsklasse hat die 15/16-Drift produziert, die das Skript selbst im Kommentar dokumentiert.
**Fix:** `from tests.contract.test_tool_surface import EXPECTED_TOOLS` ist wegen des Skript-Kontexts unpraktisch; mindestens `EXPECTED_TOOLS = len(expected)` ableiten und das Set als einzige Liste im Skript führen.

### IN-07: `tables_browse` meldet Trunkierung ohne Fortsetzungs-Handle auf den Ebenen `tables` und `columns`

**File:** `src/mcp_connector/tools/tables.py:386-392`
**Issue:** `_envelope` setzt `truncated: true`, gibt aber kein `next` aus. Ein Konto mit mehr als 200 Tabellen (oder eine Tabelle mit mehr als 200 Spalten) kann den Rest über dieses Tool nie erreichen; das Antwortmuster der `rows`-Ebene (Handle) gilt hier nicht.
**Fix:** Entweder einen Offset-Cursor analog zu `rows` ausgeben oder die Grenze im `truncated`-Fall im Antworttext benennen ("raise limit up to 200"), damit der Sackgassen-Charakter zumindest erklärt ist.

### IN-08: Exakt gleichnamige Spaltentitel überschreiben sich still im Zeilenobjekt

**File:** `src/mcp_connector/tools/tables.py:333-344`
**Issue:** Der Schreibpfad verweigert mehrdeutige Titel, der Lesepfad nicht: `_row` benutzt Titel als Objektschlüssel; zwei Spalten mit byte-identischem Titel (Tables hat keine Unique-Constraint) kollabieren auf einen Schlüssel, der Wert der ersten Spalte verschwindet still. Die Fixture umgeht das nur, weil "Status" und "status " sich in einem Leerzeichen unterscheiden.
**Fix:** Bei Kollision die Schlüssel disambiguieren (z. B. `"Status (2)"`) oder die Kollision im Antwortobjekt benennen.

### IN-09: `tables_available` hängt am Feld `enabled`, verifiziert nur gegen Tables 2.2.2

**File:** `src/mcp_connector/nextcloud/capabilities.py:150-155`
**Issue:** `bool(tables.get("enabled")) if tables else False` behandelt eine Tables-Fassung, deren Capabilities-Sektion kein `enabled` publiziert, als abwesend, obwohl die App laufen kann. Die Entscheidung ist gegen 2.2.2 gemessen und begründet; für ältere oder künftige Fassungen ist sie eine fail-closed-Annahme, die sich nur als "Tables app is not enabled"-Fehlermeldung äußern würde.
**Fix:** Kein Codefix nötig; die Versionsabhängigkeit im Kommentar festhalten und, falls ein Nutzerbericht auftritt, auf `tables.get("enabled", True)` mit Sektion-Präsenz als Fallback wechseln.

---

_Reviewed: 2026-08-21T08:53:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
