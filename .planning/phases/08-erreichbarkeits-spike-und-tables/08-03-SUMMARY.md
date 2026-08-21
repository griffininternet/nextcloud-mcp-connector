---
phase: 08-erreichbarkeits-spike-und-tables
plan: 03
subsystem: tools
tags: [tables, mcp-tools, paging, permissions, projection, respx]

# Dependency graph
requires:
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "clients/tables.py mit get_tables, get_table, get_columns, get_rows_simple, create_row; ocs.ocs_post; Capabilities.tables_available (Plan 08-02)"
  - phase: 01-server-kern
    provides: "tools/deck.py als Vorbild (Browse-Kopf, Rechtevorprüfung, Envelope), paging.py, errors.ToolError, capabilities.require_app"
  - phase: 07-kontext-und-marken
    provides: "tools/marks.without_marks als Filter für fremden Text im Modellkontext"
provides:
  - "tools/tables.py: browse mit drei Ebenen (tables, columns, rows), Projektion je Ebene, ein Antwortformat für alle drei"
  - "Erzwungene Kappung im Tool: Default 25, Maximum 200, rowsCount, offset, truncated und next-Handle mit Tabellen-Scope"
  - "create_row mit Titel-zu-Id-Abbildung, vier Ablehnungen vor dem ersten Schreibbyte"
  - "_may_create nach K5: die Eigentümer-Regel, die ein wörtlicher Blick auf onSharePermissions.create falsch beantwortet"
  - "24 Testfunktionen (29 Fälle) über beide Werkzeuge, inklusive der zwei Fälle, die ein Happy-Path-Test nie sieht"
affects: [08-04-gates-und-registrierung, 08-05-integration, 09-talk, 10-mail, 11-kontext]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Browse-Werkzeug mit level-Enum statt eines Werkzeugs je Hierarchieebene (D-06, D-14)"
    - "Freiform-Parameter als kompakter JSON-String statt als Dict, damit kein $defs ins Input-Schema gerät"
    - "Rechtevorprüfung am Objekt mit der Begründung im Docstring, warum das naive Feld nicht allein befragt wird"
    - "Titel werden ausschließlich gegen die Spaltenliste der Instanz aufgelöst, Mehrdeutigkeit wird abgelehnt statt geraten"
    - "Cursor-Handle mit der Objekt-Id als Scope, geprüft über paging.check_scope"

key-files:
  created:
    - src/mcp_connector/tools/tables.py
    - tests/unit/test_tables_tools.py
  modified:
    - vulture_whitelist.py

key-decisions:
  - "_may_create steht in Task 1 und nicht erst in Task 2: die Projektion von level=tables meldet can_create, und zwei Fassungen derselben Regel wären zwei Wahrheiten"
  - "Die Zeilenantwort trägt zusätzlich table (den Titel aus get_table), weil derselbe Request ohnehin für rowsCount gestellt wird und ein Titel die Antwort lesbar macht"
  - "rowsCount wird defensiv gelesen: meldet die App keine brauchbare Zahl, tritt offset plus count an ihre Stelle, damit truncated nie auf einer Falschzahl beruht"
  - "Kein neuer Eintrag in vulture_whitelist.py, dafür fünf entfernte: das Gate ist ohne jeden Eintrag grün, und ein unnötiger Eintrag verletzt die Regel der Datei"
  - "TABLES-01 und TABLES-02 bleiben Pending: beide versprechen ein Werkzeug, und dieser Plan registriert keines (Fortsetzung der Entscheidung aus 08-02)"

requirements-completed: []  # TABLES-01 und TABLES-02 werden von Plan 08-04 abgehakt, der die Werkzeuge registriert

# Metrics
duration: 12 min
completed: 2026-08-21
---

# Phase 8 Plan 03: Fachlogik der Tables-Familie Summary

**Ein Browse-Werkzeug über drei Ebenen mit konstruktiv gekapptem Zeilenfenster und ein Zeilen-Anlegen über Spaltentitel, dessen vier Ablehnungen alle vor dem ersten Schreibbyte passieren, inklusive der Eigentümer-Regel, die `onSharePermissions.create` falsch beantwortet.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-21T07:40:00Z
- **Completed:** 2026-08-21T07:52:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 neu, 1 geändert)

## Accomplishments

- `tools/tables.py` beantwortet drei Fragen mit einem Werkzeug und einem Antwortformat: die Tabellen, die Spalten einer Tabelle, die Zeilen einer Tabelle. Das Modell lernt eine Form statt drei, und `tools/list` zahlt einen Slot statt drei.
- Ein Zeilenaufruf ohne Limit liest 25 Zeilen und nicht die Tabelle. Die Eigenschaft wird nicht am Ergebnis behauptet, sondern an der gebauten URL: der Test liest `limit=25` aus der Query, und `limit=5000` beziehungsweise `limit=0` erscheinen dort als 200 und 1.
- Die Kappung steht immer beim Namen: `rowsCount` neben `count` und `offset`, und bei mehr vorhandenen Zeilen `truncated: True` plus ein `next`-Handle, das die Tabellen-Id als Scope trägt. Ein Handle einer anderen Tabelle wird abgelehnt, statt still die falsche Seite zu liefern.
- Eine Zeile entsteht über Spaltentitel, aber nur über Titel, die die Instanz wirklich hat. Der Vergleich ist normalisiert, ein mehrdeutiger Titel wird mit beiden Spalten-Ids abgelehnt statt geraten, und der `data`-Dict, der den Client erreicht, trägt ausschließlich Spalten-Ids.
- Die gefährlichste Falle der Phase ist mit zwei Tests in beide Richtungen festgenagelt: der Eigentümer seiner eigenen Tabelle darf schreiben, obwohl das Share-Objekt nur `read` meldet, und eine geteilte Tabelle ohne `create` und ohne `manage` wird mit Titel und nächstem Schritt abgewiesen, bevor der POST entsteht.
- Die Registry ist unberührt: `tools/list` bleibt bei 16 Werkzeugen und 11268 Bytes gegen ein Gate von 12500, `uv run pytest -q` ist vollständig grün.

## Exportierte Schnittstelle für Plan 04

Plan 04 baut das Input-Schema wörtlich hieraus:

```python
# src/mcp_connector/tools/tables.py
APP = "tables"
LEVELS = ("tables", "columns", "rows")
DEFAULT_LIMIT = 25
MAX_LIMIT = 200

async def browse(
    clients: NcClients,
    level: str = "tables",
    table_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]

async def create_row(clients: NcClients, table_id: str, values: str) -> dict[str, Any]

def _may_create(table: dict[str, Any]) -> bool
```

Antwortformen:

```python
# browse(level="tables") und browse(level="columns")
{"level": "tables", "count": 2, "results": [...]}                       # plus truncated bei Kappung
# results je Tabelle: id, title, rowsCount, columnsCount, isShared, can_create, emoji (nur wenn gesetzt)
# results je Spalte:  id, title, type, mandatory, subtype und die gesetzten Grenzen
#                     (selectionOptions, textMaxLength, numberMin, numberMax, numberDecimals, datetimeDefault)

# browse(level="rows")
{"level": "rows", "table": "Übergaben Straßenbau", "count": 3, "results": [{"<Spaltentitel>": "<Wert>"}],
 "rowsCount": 342, "offset": 0, "truncated": True, "next": "<Handle>"}

# create_row
{"id": 4711, "table_id": "7", "url": "<base>/index.php/apps/tables/#/table/7",
 "values_written": {"Aufgabe": "Baulos 4 übergeben", "Größe in m²": 12.5}}
```

Hinweise für Plan 04: `level` gehört als `Literal["tables", "columns", "rows"]` ins
Registrierungsmodul, `values` ist ein **String** mit kompaktem JSON (ein Dict-Parameter zöge
`$defs` ins Schema), leere Strings statt `None` für `table_id` und `cursor`, und die
Tool-Beschreibung von `tables_create_row` muss die zwei verifizierten Wertformen nennen
(Textspalte nimmt einen JSON-String, Zahlenspalte eine JSON-Zahl) sowie den Satz, dass ein
Timeout nicht bedeutet, dass nichts geschrieben wurde. Das Budget-Gate reisst mit der
Registrierung und wird laut Recherche in demselben Commit angehoben.

## Task Commits

1. **Task 1: browse mit drei Ebenen, Kappung und Cursor** - `1a2f3d5` (feat)
2. **Task 2: create_row mit Titel-zu-Id-Abbildung und der Eigentümer-Regel** - `3281139` (feat)
3. **Task 3: Unit-Testkatalog beider Werkzeuge** - `33c42e2` (test)

## Files Created/Modified

- `src/mcp_connector/tools/tables.py` (neu, 392 Zeilen) - `browse` mit Ebenenprüfung, Kappung und Capabilities-Gate in dieser Reihenfolge; drei Projektionen; `_rows` mit Cursor-Scope und Titelzeile als Schlüssel; `create_row` mit Parsen, Rechtevorprüfung, Titel-Abbildung und Antwortprüfung; `_may_create` mit der K5-Begründung im Docstring
- `tests/unit/test_tables_tools.py` (neu, 623 Zeilen) - 24 Testfunktionen, 29 Fälle, `respx` gegen die eingefrorenen Literale beider Generationen
- `vulture_whitelist.py` - der Tables-Transportblock ist aufgelöst: die fünf Funktionen haben mit diesem Plan ihren Produktionsaufrufer

## Decisions Made

- **`_may_create` steht in Task 1.** Die Projektion von `level=tables` meldet `can_create`, und dieses Feld ist genau die Frage, die `create_row` später stellt. Zwei Fassungen derselben Regel wären zwei Wahrheiten, von denen eine irgendwann veraltet, also gibt es eine Funktion, die beide benutzen. Der Plan sieht das in Task 1 wörtlich vor ("`can_create` (aus `_may_create`)"), die Begründung im Docstring gehört fachlich zu Task 2.
- **Die Zeilenantwort trägt `table`.** `get_table` wird ohnehin für `rowsCount` gestellt (K11), also kostet der Titel keinen Request und macht die Antwort lesbar, ohne dass das Modell die Tabellenliste dazuholen muss.
- **`rowsCount` wird defensiv gelesen.** Meldet die App keine nutzbare Zahl, tritt `offset + count` an ihre Stelle. Sonst könnte eine fehlende Zahl zu einem `truncated`-Feld führen, das auf einem `None`-Vergleich beruht, oder umgekehrt eine echte Kappung verschweigen.
- **Keine clientseitige Typvalidierung der Zellwerte.** Die Wertform je `type` und `subtype` ist in der App nicht vollständig dokumentiert; ein eigener Validator wäre eine zweite Wahrheit, die bei jedem neuen Spaltentyp veraltet. Ein 400 der App wird mit ihrer eigenen Meldung durchgereicht, und ein Test belegt genau das ("Nextcloud says: Value is not a valid number").
- **Reihenfolge der vier Ablehnungen.** Recht, dann Mehrdeutigkeit, dann unbekannter Titel, dann fehlende Pflichtspalte. Das Recht steht vorn, weil es der einzige Fall ist, in dem sogar das Lesen der Spalten überflüssig ist; ein Test behauptet, dass die Spalten-URL dann nicht gerufen wird.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Kein neuer Eintrag in `vulture_whitelist.py`, dafür fünf entfernte**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt, die neuen öffentlichen Funktionen mit Begründung in `vulture_whitelist.py` einzutragen, weil Plan 04 sie erst registriert. Gemessen ist das Gate aber ohne jeden neuen Eintrag grün (`uv run vulture src scripts vulture_whitelist.py`, Exit 0): `vulture` arbeitet namensbasiert, und die Namen `browse` und `create_row` werden im Repository bereits als Attribut aufgerufen (`deck.browse` im Registrierungsmodul, `tables_client.create_row` im neuen Tool). Ein Eintrag, der nichts verhindert, verletzt die Regel der Datei ("ein Name, der nicht in einer Zeile begründet werden kann, ist toter Code").
- **Fix:** Kein neuer Eintrag. Stattdessen der Schritt, den 08-02 unter "Next Phase Readiness" verlangt: der Block der fünf Transportfunktionen (`get_tables`, `get_table`, `get_columns`, `get_rows_simple`, `create_row`) ist aufgelöst, mit einem Kommentar, der sagt, welcher Plan die Aufrufer gebracht hat. `tables_api_versions` bleibt, dieselbe Lage wie `deck_api_versions`.
- **Files modified:** `vulture_whitelist.py`
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` und `uv run vulture src scripts vulture_whitelist.py` beide Exit 0
- **Committed in:** `3281139`

**2. [Rule 1 - Bug] TABLES-01 und TABLES-02 bleiben Pending**
- **Found during:** Abschluss (Requirements-Schritt)
- **Issue:** Die Plan-Frontmatter nennt `requirements: [TABLES-01, TABLES-02]`. Beide Anforderungstexte beginnen mit "Nutzer kann ... über `tables_browse`" beziehungsweise "über `tables_create_row`". Dieser Plan registriert bewusst kein Werkzeug (`tools/list` bleibt bei 16), ein Nutzer kann also nichts davon aufrufen. Ein Häkchen wäre unwahr, und es ist dieselbe Lage, die 08-02 schon einmal korrigiert hat.
- **Fix:** `.planning/REQUIREMENTS.md` unverändert gelassen; beide Anforderungen werden von Plan 08-04 abgehakt, der die Registrierung und die Gates bringt. `requirements-completed` in dieser Zusammenfassung ist leer.
- **Files modified:** keine
- **Verification:** `grep TABLES-0 .planning/REQUIREMENTS.md` zeigt für beide `[ ]` und `Pending`
- **Committed in:** nicht committet, die Rücknahme ist die Abwesenheit der Änderung

**3. [Rule 2 - Missing critical] Drei Tests über den Plankatalog hinaus**
- **Found during:** Task 3
- **Issue:** Der Katalog des Plans nennt 21 Fälle. Drei Pfade fehlen darin, die alle Ablehnungen sind: die Projektion von `level=columns` (die interpretationsnötigen Grenzen sind der einzige Grund, warum diese Ebene existiert), `values` als leeres Objekt (der Plan verlangt die Ablehnung in Task 2, nennt aber keinen Test dafür) und die abgeschaltete App auch für `create_row`.
- **Fix:** Drei zusätzliche Testfunktionen beziehungsweise Parameterfälle. Gesammelt werden dadurch 29 Fälle statt 21.
- **Files modified:** `tests/unit/test_tables_tools.py`
- **Verification:** `uv run pytest tests/unit/test_tables_tools.py -q` sammelt 29 Tests, alle grün
- **Committed in:** `33c42e2`

---

**Total deviations:** 3 auto-fixed (1 blockierendes Gate anders gelöst als geplant, 1 verfrühte Anforderungs-Zusage, 1 Testlücke)
**Impact on plan:** Keine Umfangsänderung, keine neue Abhängigkeit, kein neuer öffentlicher Name über die zwei geplanten Funktionen hinaus. Die Abweichung bei `vulture` macht die Whitelist kürzer statt länger, was der Regel dieser Datei entspricht.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün, 179 Dateien |
| `uv run pyright` (ganzes Projekt) | 0 errors, 0 warnings |
| `uv run vulture src scripts vulture_whitelist.py` | grün (Exit 0), fünf Einträge weniger |
| `uv run pytest tests/unit/test_tables_tools.py -q` | 29 Tests grün (24 Testfunktionen, Minimum des Plans 21) |
| `uv run pytest -q` (Default-Auswahl) | grün, keine Regression |
| `uv run python scripts/check_tool_budget.py` | 11268 Bytes, 16 Tools, Gate 12500, unverändert |
| `_may_create` Wahrheitstabelle (eigene, geteilt ohne, geteilt mit `create`, geteilt mit `manage`, `onSharePermissions: null`) | wie im Plan gefordert |
| `git diff --name-only` für `ids.py`, `provider_map.py`, `tools/context.py` | leer, alle drei unverändert |
| Kein `ids`-Import in `tools/tables.py` (K8) | bestätigt |

## Issues Encountered

Keine. Die drei Aufgaben liefen in der geplanten Reihenfolge, ohne Checkpoint und ohne Auth-Gate. Zwei Zwischenläufe waren rot und wurden im selben Task behoben: `ruff format` wollte zwei Signaturen einzeilig, und `ruff check` verlangte sieben zusammengesetzte Assertions als Einzelbehauptungen (PT018).

## Known Stubs

Keine. Beide Funktionen sind vollständig und werden von 29 Testfällen getrieben; was fehlt, fehlt absichtlich und ist im Modul-Docstring benannt (kein Update, kein Delete, kein Spalten- oder Schema-Anlegen, kein Share-Pfad). Die Registrierung ist kein Stub, sondern der ausdrückliche Gegenstand von Plan 08-04.

## User Setup Required

Keine, keine externe Dienstkonfiguration und keine neue Abhängigkeit (`pyproject.toml` und `uv.lock` unangetastet, T-08-SC bleibt `accept`).

## Next Phase Readiness

- Plan 08-04 kann direkt auf die oben wörtlich dokumentierten Signaturen aufsetzen: `reg_tables.py` mit `Literal["tables","columns","rows"]`, `READ_ONLY` und `CREATE_ONLY`, `structured_output=False`, `@graceful`.
- Mit der Registrierung reissen fünf eingefrorene Zahlenstellen gleichzeitig (`EXPECTED_TOOLS`, `CREATE_TOOLS`, `len(tools) == 16`, README-Tabelle in drei Sprachen, Toolzahlen in `docs/`) plus `scripts/check_tool_budget.py` und `scripts/acceptance_all_tools.py`. Die vollständige Liste steht in der Recherche unter "Mechanische Checkliste".
- TABLES-01 und TABLES-02 sind auf Unit-Ebene erfüllt und warten auf die Registrierung, um wahr zu werden.
- Offen und bewusst ausgeklammert: der Integrationstest gegen eine echte Tables-App (Plan 08-05, dort kommt auch der Projektionsfall "gesetztes `emoji`", den die Fixtures wegen der Emoji-Regel nicht abdecken können).

## Self-Check: PASSED

- `src/mcp_connector/tools/tables.py` FOUND (392 Zeilen, min_lines 200)
- `tests/unit/test_tables_tools.py` FOUND (623 Zeilen, min_lines 220)
- Commit `1a2f3d5` FOUND, Commit `3281139` FOUND, Commit `33c42e2` FOUND
- `capabilities.require_app`, `tables_client.*`, `paging.check_scope`, `marks.without_marks`: alle vier `key_links` des Plans im Quelltext nachgewiesen
- Alle Abnahmekriterien der drei Aufgaben nachgelaufen und grün, inklusive der beiden Prüfskripte aus den `<verify>`-Blöcken

---
*Phase: 08-erreichbarkeits-spike-und-tables*
*Completed: 2026-08-21*
