---
phase: 08-erreichbarkeits-spike-und-tables
verified: 2026-08-21T12:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 8: Erreichbarkeits-Spike und Tables Verification Report

**Phase Goal:** Die einzige offene Unbekannte des Meilensteins ist gemessen (erreicht der Connector Mail unter reiner AppAPI-Impersonation, oder nicht), und die Tables-Familie ist vollständig nutzbar: Tabellen, Spalten und Zeilen lesen, Zeile anlegen. Damit ist die mechanische Checkliste einer neuen Familie einmal an der Familie ohne Zusatzrisiko durchlaufen.
**Verified:** 2026-08-21T12:00:00Z
**Status:** passed
**Re-verification:** Nein, Erstverifikation. Hinweis des Auftrags beachtet: verifizierter Stand ist HEAD (`1e39e7a`), nicht der Stand der einzelnen Plan-SUMMARYs. Working Tree ist sauber und identisch mit `1e39e7a`.

## Wichtiger Hinweis zur Methodik

Diese Verifikation hat sich nicht auf die SUMMARY- und REVIEW-Behauptungen verlassen. Beide laufenden Docker-Topologien (`nc-mcp-test` für die App-Passwort-Schicht, `nc-mcp-exapp-*` für die HaRP/AppAPI-Schicht) waren bereits aktiv, deshalb wurden alle drei Integrationstestdateien der Phase in dieser Sitzung **live erneut ausgeführt**, nach den sieben Review-Fixes (Commits `48cfbce` … `1e39e7a`), nicht nur die Unit- und Contract-Tests. Das ist deshalb wichtig, weil `uv run pytest -q` (die im Fix-Report zitierte "komplette Test-Suite") laut `pyproject.toml` (`addopts = "-m 'not integration and not matrix' ..."`) die Integrationstests **ausschließt** — der Fix-Lauf hatte die Live-Pfade also nicht erneut geprüft. Diese Lücke wurde hier geschlossen:

- `tests/integration/test_tables_roundtrip.py -m integration -q` gegen `nc-mcp-test`: 5 passed, keine Regression durch WR-01/02/03/04.
- `tests/integration/test_exapp_mail_reach.py -m integration -q -s` gegen die HaRP-Topologie: 6 passed, Messzeilen identisch zur SUMMARY (accounts 200, mailboxes 500, messages 403, ocs 404, alle JSON).
- `tests/integration/test_permission_fidelity_exapp.py -m integration -q` gegen die HaRP-Topologie: 12 passed (9 bestehende + 3 neue Tables-Fälle).
- `uv run python scripts/acceptance_all_tools.py` gegen `nc-mcp-test`: `OK: all 18 tools answered over stdio`, inklusive `tables_browse` (beide Ebenen) und `tables_create_row`.
- `uv run python scripts/check_tool_budget.py`: 12801 Bytes, 18 Tools, Budget 15000, Exit 0.
- `uv run pyright`, `uv run ruff check .`, `uv run vulture src scripts vulture_whitelist.py`: alle grün.
- `uv run pytest -q` (Default-Auswahl, 2280 Tests laut Sammlung): grün, Exit 0.

## Goal Achievement

### Observable Truths (Roadmap Success Criteria, wörtlich)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Integrationstest gegen echte Instanz zeigt für alle vier Mail-Wege (accounts, mailboxes, messages, OCS-Volltext) Statuscode und Antwortform, keine Vermutung | ✓ VERIFIED | `tests/integration/test_exapp_mail_reach.py` live erneut ausgeführt: accounts 200/json, mailboxes 500/json, messages 403/json, ocs 404/json, kein HTML, kein Redirect auf `/login`. `docs/spike-mail.md` trägt die Messtabelle, Entscheidungskriterium `_verdict`, beide Kontrollprüfungen (kein App-Passwort im Prozess, falsches `APP_SECRET` wird abgewiesen) |
| 2 | SCOPE_IGNORE-Risiko der drei internen Mail-Listen-Routen steht im Code an der aufrufenden Stelle und in der Doku als Ersetzbarkeits-Hinweis | ✓ VERIFIED | Modul-Docstring und `#:`-Kommentare in `tests/integration/test_exapp_mail_reach.py` (Zeilen 19, 59, 63, 69) nennen `SCOPE_IGNORE` je Route; `docs/spike-mail.md` Abschnitt "Replaceability" nennt Ausweg (Suchprovider `mail` + OCS-Volltextroute) und übergibt die zweite Nennung ausdrücklich an Phase 10, wo `clients/mail.py` erst entsteht — das ist korrekt außerhalb des Scopes von Phase 8 |
| 3 | Nutzer kann Tabellen, Spalten, Zeilen über einen Aufruf lesen; jede Antwort gekappt (Default 25, Max 200), nennt `rowsCount`, markiert Kappung, kein Aufruf ohne Limit liest ganze Tabelle | ✓ VERIFIED | `tools/tables.py::browse` erzwingt `capped = min(max(limit,1), MAX_LIMIT)`; `DEFAULT_LIMIT=25`, `MAX_LIMIT=200`; Client-Ebene erzwingt `limit` als Keyword ohne Default. Live bestätigt: `test_the_live_row_url_carries_a_limit` zeigt echte URLs mit `limit=25` und `limit=200` (aus `limit=5000` gekappt); `test_the_table_level_reports_a_row_count_and_the_owner_may_write` zeigt echtes `rowsCount=5`. WR-01/WR-02-Fixes (Commits `48cfbce`, `5f3788d`) beheben stille Trunkierung und Endlosschleifen-Klasse bei fehlendem `rowsCount`, mit je einem Unit-Test belegt und live nicht regressiv |
| 4 | Nutzer kann Zeile mit Spaltentiteln anlegen; unbekannter/mehrdeutiger/fehlender Pflichttitel wird mit Liste gültiger Titel abgelehnt, bevor geschrieben wird | ✓ VERIFIED | `tools/tables.py::_by_column_id` prüft in der Reihenfolge Recht → Mehrdeutigkeit → unbekannt → Pflichtspalte, alle vor `tables_client.create_row`; 29 Unit-Testfälle in `test_tables_tools.py`; live bestätigt: `test_a_new_row_is_readable_back_under_its_column_titles` schreibt Text, Zahl, Auswahl, Datum in einem Aufruf, Antwort 200 mit `id`, `table_id`, `url`, `values_written` |
| 5 | Nutzer ohne Schreibrecht bekommt vorab Fehlersatz mit nächstem Schritt statt 403; kein Pfad zum Ändern/Löschen einer Zeile oder eines Schemas (Gate + Gegenprobe) | ✓ VERIFIED | `_may_create` (K5-Regel, Eigentümer nie abgewiesen) mit Docstring-Begründung und Wahrheitstabellen-Tests; `tests/contract/test_no_destructive_calls.py` trägt 5 Nadeln (`/rows/`, `/columns/`, `/scheme`, `/transfer`, `/share`) je mit Gegenprobe, nach WR-05-Fix (Commit `48d5d5c`) auf Pfadsegmente statt Anführungszeichen verankert und per Grep gegen den echten Quellcode negativ getestet; live bestätigt durch `test_permission_fidelity_exapp.py`: zweites Konto sieht fremde Tabelle nicht, Schreibversuch scheitert, Zeilenzahl des Eigentümers bleibt unverändert |

**Score:** 5/5 Roadmap-Erfolgskriterien verifiziert.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/integration/test_exapp_mail_reach.py` | Messung der vier Mail-Wege, MODE_APPAPI, SCOPE_IGNORE | ✓ VERIFIED | 345 Zeilen, live 6 Tests grün, kein `httpx.BasicAuth` (0 Treffer) |
| `docs/spike-mail.md` | Messprotokoll, Entscheidung, Ersetzbarkeit | ✓ VERIFIED | 177 Zeilen, Messtabelle deckt sich wörtlich mit dem heutigen Live-Lauf |
| `scripts/bootstrap_exapp.sh`, `scripts/bootstrap_test_nc.sh` | `ensure_app tables`/`mail`, Spike-Mail-Konto | ✓ VERIFIED | beide Apps in beiden laufenden Topologien enabled (`tables 2.2.2`, `mail 5.11.1` bestätigt durch Live-Capabilities-Abfrage und Acceptance-Lauf) |
| `src/mcp_connector/nextcloud/clients/tables.py` | Transport beider Generationen, erzwungenes `limit` | ✓ VERIFIED | 252 Zeilen, `MAX_ROWS=200`, `NODE_TYPE_TABLE`/`NODE_COLLECTION_TABLES`, kein DELETE/PROPPATCH |
| `src/mcp_connector/nextcloud/clients/ocs.py` (`ocs_post`) | Erste OCS-Schreibnaht | ✓ VERIFIED | `ocs_post` vorhanden, `Content-Type` gesetzt, kein `Origin`-Header, live durch `create_row` (Status 200) bestätigt |
| `src/mcp_connector/nextcloud/capabilities.py` | `tables_available` aus `tables.enabled` | ✓ VERIFIED | Feld korrekt aus `enabled` statt Sektionspräsenz gelesen; live `tables_available=True`, `apiVersions=['1.0','2.0','2.1']` |
| `src/mcp_connector/tools/tables.py` | `browse` (3 Ebenen), `create_row`, K5-Vorprüfung | ✓ VERIFIED | 459 Zeilen (nach Review-Fixes gewachsen von 392), alle 4 Review-Fixes (`_clean`, `_row_count`, `_by_column_id`-ID-Prüfung) im Code nachgewiesen |
| `src/mcp_connector/server/reg_tables.py` | Registrierung, Literal-Enum, READ_ONLY/CREATE_ONLY | ✓ VERIFIED | 71 Zeilen, `Literal["tables","columns","rows"]`, korrekt über `_load_registrations()` geladen (kein Eintrag in `__init__.py` nötig, live bestätigt durch `tools/list`) |
| `tests/contract/test_tool_surface.py`, `test_no_destructive_calls.py` | 18 Tools, Enum-Test, 5 Nadeln + Gegenproben | ✓ VERIFIED | 37 Tests grün, `len(tools)==18`, keine Reste von "== 16"/"all 16"/"16 tools" außerhalb Kommentaren |
| `scripts/check_tool_budget.py` | Datierte Messung + `MAX_TOOL_BYTES` | ✓ VERIFIED | 12801 Bytes / 18 Tools / Budget 15000, `MAX_TOOL_BYTES=1400`, Exit 0 |
| `tests/integration/test_tables_roundtrip.py` | Live-Roundtrip | ✓ VERIFIED | 336 Zeilen, live 5/5 Tests grün nach Review-Fixes (keine Regression) |
| `tests/integration/test_permission_fidelity_exapp.py` | Zwei-Konten-Negativbeweis erweitert | ✓ VERIFIED | live 12/12 Tests grün, 3 neue Tables-Fälle plus 9 bestehende unverändert |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/tables.py` | `capabilities.require_app` | erste Zeile beider Einstiegsfunktionen | ✓ WIRED | im Code an erster Stelle von `browse` und `create_row` |
| `tools/tables.py` | `clients/tables.py` | `get_tables/get_table/get_columns/get_rows_simple/create_row` | ✓ WIRED | alle fünf Aufrufe im Code nachgewiesen, live durch Roundtrip getrieben |
| `tools/tables.py` | `paging.py` | `check_scope` mit Tabellen-Id als Scope | ✓ WIRED | verhindert fremdes Cursor-Handle, Unit- und Live-Test vorhanden |
| `tools/tables.py` | `tools/marks.py` | `without_marks`/`_clean` auf jeden Zellwert | ✓ WIRED | nach WR-03-Fix rekursiv auf Listen/Objekte erweitert (Commit `2b60ac5`) |
| `server/reg_tables.py` | `tools/tables.py` | `tables_tools.browse`/`create_row` hinter `compact`+`graceful` | ✓ WIRED | live durch `tools/list` und Acceptance-Lauf bestätigt |
| `server/__init__.py` | `server/reg_tables.py` | `_load_registrations()` pkgutil-Autoimport | ✓ WIRED | kein manueller Eintrag nötig, Tool live erreichbar |
| `test_tool_surface.py` | READMEs (3 Sprachen) | Tabellenzellen-Parser | ✓ WIRED | Test grün, Zellen inhaltlich mit Registry-Annotationen übereinstimmend |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `tables_browse(level="tables")` | `results` | `tables_client.get_tables` → echte OCS-Antwort | Ja, live 2 echte Tabellen inkl. Testartefakte | ✓ FLOWING |
| `tables_browse(level="rows")` | `results`, `rowsCount` | `tables_client.get_rows_simple` + `get_table` | Ja, live `rowsCount=5`, echte Zeileninhalte mit Umlauten | ✓ FLOWING |
| `tables_create_row` | `values_written` | `tables_client.create_row` POST → echte Serverantwort | Ja, live Status 200, Zeilen-Id 13/14 in zwei unabhängigen Läufen | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Mail unter AppAPI-Impersonation erreichbar (4 Wege) | `pytest tests/integration/test_exapp_mail_reach.py -m integration -q -s` gegen HaRP-Topologie | accounts 200, mailboxes 500, messages 403, ocs 404, alle JSON | ✓ PASS |
| Tables-Roundtrip gegen echte Instanz | `pytest tests/integration/test_tables_roundtrip.py -m integration -q` gegen App-Passwort-Topologie | 5 passed, kein Skip | ✓ PASS |
| Zwei-Konten-Negativbeweis inkl. Tables | `pytest tests/integration/test_permission_fidelity_exapp.py -m integration -q` gegen HaRP-Topologie | 12 passed, kein Skip | ✓ PASS |
| Alle 18 Werkzeuge antworten live | `python scripts/acceptance_all_tools.py` gegen App-Passwort-Topologie | `OK: all 18 tools answered over stdio` | ✓ PASS |
| Budget-Gate hält | `python scripts/check_tool_budget.py` | 12801/15000 Bytes, Exit 0 | ✓ PASS |
| Destruktiv-Gate + Contract-Tests | `pytest tests/contract/ -q` | 37 Tests grün (u.a. beide betroffenen Dateien) | ✓ PASS |
| Default-Testsuite ohne Regression | `pytest -q` | grün, Exit 0 | ✓ PASS |
| Statik (Typen, Lint, toter Code) | `pyright`, `ruff check .`, `vulture src scripts vulture_whitelist.py` | alle grün, 0 Fehler | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MAIL-04 | 08-01 | Mail-Zugang im AppAPI-Modus live bewiesen, SCOPE_IGNORE benannt | ✓ SATISFIED | Live-Messung heute reproduziert, identisch zur SUMMARY; `.planning/REQUIREMENTS.md` zeigt `[x]` und "Complete" |
| TABLES-01 | 08-02/03/04/05 | `tables_browse` über drei Ebenen, Kappung, `rowsCount`, benannte Truncation | ✓ SATISFIED | Live-Roundtrip + 29 Unit-Tests + Contract-Tests; korrekt erst mit 08-04 (Registrierung) abgehakt, nicht vorzeitig in 08-02/03 (von den SUMMARYs selbst korrigiert) |
| TABLES-02 | 08-02/03/04/05 | `tables_create_row` mit Titel-zu-Id-Abbildung, Vorprüfungen vor dem Schreiben | ✓ SATISFIED | Live bestätigt (Text/Zahl/Auswahl/Datum in einem Aufruf), vier Ablehnungspfade unit-getestet |

Keine Waisen: `.planning/REQUIREMENTS.md` nennt für Phase 8 ausschließlich MAIL-04, TABLES-01, TABLES-02, alle drei sind in den Plan-Frontmatters von 08-01 bis 08-05 referenziert und hier bestätigt.

### Anti-Patterns Found

Der Code-Review-Zyklus (08-REVIEW.md → 08-REVIEW-FIX.md) hat vor dieser Verifikation bereits 7 Warnings und 4 Info-Befunde behoben (Commits `48cfbce` … `ba93d80` … `1e39e7a`). Diese Verifikation hat die Fixes im Code bestätigt (nicht nur im Report gelesen) und zusätzlich die Live-Integrationstests nach den Fixes erneut ausgeführt, weil der Fix-Report das nicht abdeckte (`addopts` schließt `integration` aus).

Keine TBD/FIXME/XXX-Marker in den phasenrelevanten Dateien gefunden (grep negativ).

Fünf Info-Befunde sind mit nachvollziehbarer Begründung zurückgestellt (IN-05 bis IN-09, siehe `08-REVIEW.md`/`08-REVIEW-FIX.md`): Unicode-Ziffern in `_path_id` (harmloses 404, kein Sicherheitsproblem), Duplizierte Toolmenge im Abnahmeskript (Strukturentscheidung), fehlendes Fortsetzungs-Handle auf den Ebenen `tables`/`columns` (Schema-Erweiterung), stille Kollision gleichnamiger Spaltentitel im Lesepfad (Schema-Entscheidung), `tables_available` versionsabhängig an `enabled` (begründete fail-closed-Annahme). Keiner davon widerspricht einem der fünf Roadmap-Erfolgskriterien oder einem der drei Requirements dieser Phase; alle sind als Info und nicht als Warning/Critical eingestuft und tragen eine nachvollziehbare Begründung, warum sie außerhalb des Fix-Scopes liegen. Sie werden hier informativ vermerkt, nicht als Gap gewertet.

### Human Verification Required

Keine. Die Phase hat laut Roadmap `UI hint: nein` (keine Frontend-Komponente), und alle fünf Erfolgskriterien sind mechanisch/live geprüft worden (Statuscodes, Antwortformen, Gate-Zustände, Zeilenzahlen). Es gibt keinen Rest, der nur durch visuelle oder subjektive Prüfung zu beurteilen wäre.

### Gaps Summary

Keine Gaps. Alle fünf Roadmap-Erfolgskriterien und alle drei Requirements (MAIL-04, TABLES-01, TABLES-02) sind verifiziert, sowohl im Code (Level 1-3) als auch mit echten Daten gegen zwei laufende Nextcloud-Topologien (Level 4, in dieser Sitzung erneut ausgeführt, nicht nur aus SUMMARY übernommen). Der einzige methodische Fund dieser Verifikation ist, dass der Fix-Report von `08-REVIEW-FIX.md` die Integrationstests nicht erneut laufen ließ (weil `pytest -q` sie standardmäßig ausschließt) — das wurde hier nachgeholt, und alle drei Integrationstestdateien sind am aktuellen HEAD (`1e39e7a`) grün ohne Regression.

---

_Verified: 2026-08-21T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
