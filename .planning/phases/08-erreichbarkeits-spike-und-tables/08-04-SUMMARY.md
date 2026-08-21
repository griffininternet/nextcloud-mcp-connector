---
phase: 08-erreichbarkeits-spike-und-tables
plan: 04
subsystem: api
tags: [tables, mcp-tools, registry, contract-tests, token-budget, i18n]

# Dependency graph
requires:
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "tools/tables.py mit browse und create_row, LEVELS, DEFAULT_LIMIT, MAX_LIMIT (Plan 08-03)"
  - phase: 01-server-kern
    provides: "server/reg_deck.py als Vorbild, READ_ONLY und CREATE_ONLY, compact, graceful, _load_registrations, beide Contract-Test-Dateien, check_tool_budget.py, acceptance_all_tools.py"
provides:
  - "server/reg_tables.py: tables_browse mit Literal-Enum und tables_create_row als fuenfter Schreibpfad, beide ohne Output-Schema und ohne $defs"
  - "Werkzeugzahl 18 identisch in Registry, beiden Contract-Tests, beiden Skripten, den drei READMEs und der Doku"
  - "Fuenf FORBIDDEN-Nadeln fuer die Tables-Schreibrouten, jede mit eigener Gegenprobe plus dem Nachweis, dass die erlaubten Routen durchgehen"
  - "Budget-Gate auf einer datierten Messung verankert (12801 Bytes bei 18 Werkzeugen, Gate 15000) plus MAX_TOOL_BYTES = 1400 je Werkzeug"
  - "acceptance_all_tools.py ruft alle 18 Werkzeuge, die Altlast der Zahl 15 ist aufgeloest"
affects: [08-05-integration, 09-talk, 10-mail, 11-kontext-und-release]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Registrierungsmodul je Familie, ohne Eintrag in server/__init__.py (pkgutil-Autoimport)"
    - "Zwei Behauptungen statt einer im Budget-Gate: Summe mit Luft plus Pro-Werkzeug-Deckel"
    - "Gate-Nadeln auf die Anfuehrungszeichen-Form eines Pfadliterals verankert, damit erlaubte Nachbarroute nicht mitgetroffen wird"
    - "Jede neue Nadel hat eine Gegenprobe in beide Richtungen: sie loest aus und sie trifft den echten Quellcode nicht"

key-files:
  created:
    - src/mcp_connector/server/reg_tables.py
  modified:
    - tests/contract/test_tool_surface.py
    - tests/contract/test_no_destructive_calls.py
    - scripts/check_tool_budget.py
    - scripts/acceptance_all_tools.py
    - README.md
    - README.de.md
    - README.fr.md
    - docs/client-setup.md
    - docs/conference-demo.md
    - docs/conference-talk.md
    - docs/oauth-setup.md
    - docs/store-submission.md
    - CHANGELOG.md
    - vulture_whitelist.py
    - .github/workflows/ci.yml

key-decisions:
  - "Das Budget-Gate steht auf der Formel des bestehenden Eintrags (Messung 12801 plus 15 Prozent, aufgerundet auf 15000) und traegt zusaetzlich MAX_TOOL_BYTES = 1400, weil eine Aggregatzahl mit Luft keine Regression meldet"
  - "Die fuenf Tables-Nadeln sind auf die Anfuehrungszeichen-Form eines Pfadliterals verankert, weil tables/{id}/rows und rows/simple erlaubte Routen sind"
  - "ALLOWED_MODULE_STATE wird jetzt gezaehlt und nicht nur beschrieben: genau zwei Eintraege"
  - "acceptance_all_tools.py ruft die drei bisher ungerufenen Werkzeuge wirklich, statt nur die erwartete Zahl zu erhoehen"
  - "Die Zahl 16 bleibt in datierten Messwerten alter Laeufe stehen; store-submission.md bekommt dafuer den Zeiger auf den Contract-Test statt einer gefaelschten Zahl"
  - "Keine neue Prosa-Sektion je Sprache fuer Tables: die drei Tabellenzeilen tragen die Schreibgrenze, der Familienabschnitt ist ausdruecklich Sache der Release-Phase"

patterns-established:
  - "Registrierung und Nachzug aller eingefrorenen Zahlen liegen in einem Plan, damit die Registry kein rotes Fenster hat"
  - "Eine Zahl, die in einem Kommentar nur veralten kann, wird ersatzlos entfernt und auf den Contract-Test verwiesen"

requirements-completed: [TABLES-01, TABLES-02]

# Metrics
duration: 18 min
completed: 2026-08-21
---

# Phase 8 Plan 04: Gates und Registrierung Summary

**Die Tables-Familie ist sichtbar: `tools/list` nennt 18 Werkzeuge zu 12801 Bytes, `level` ist ein Enum aus genau drei Werten, und alle elf eingefrorenen Stellen von den Contract-Tests bis zu den drei Sprachfassungen nennen dieselbe Zahl. Das Budget-Gate steht wieder auf einer Messung, und fuenf neue Nadeln mit Gegenprobe halten fest, dass keine Zeile, keine Spalte und kein Schema geaendert werden kann.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-08-21T07:55:00Z
- **Completed:** 2026-08-21T08:13:00Z
- **Tasks:** 3
- **Files modified:** 16 (1 neu, 15 geaendert)

## Accomplishments

- `reg_tables.py` registriert beide Werkzeuge ohne eine Zeile in `server/__init__.py`: `_load_registrations()` importiert jedes `reg_*`-Modul per pkgutil, und genau deshalb hat dieser Plan keine gemeinsame Datei mit einem parallel laufenden angefasst.
- `level` ist im Input-Schema ein `enum` mit genau `tables`, `columns`, `rows`. Beide Schemata sind frei von `$defs`, beide Werkzeuge haben `output_schema is None`, und `values` bleibt der JSON-String aus Plan 03, weil ein Dict-Parameter genau das `$defs` erzeugen wuerde, das an mehreren Stellen verboten ist.
- Die Annotationen sagen die Wahrheit und nicht nur eine Absicht: `tables_browse` ist `read_only`, `tables_create_row` schreibt, ist weder destruktiv noch idempotent, und der Client darunter hat fuer Update und Delete keinen Code.
- Die Beschreibung von `tables_create_row` traegt den Satz, der im Betrieb Geld wert ist: ein Timeout bedeutet nicht, dass nichts geschrieben wurde, also nachlesen mit `tables_browse(level="rows")` statt ein zweites Mal aufrufen.
- Das Destruktiv-Gate kennt jetzt fuenf Routen, die kein verbotenes Verb brauchen: Einzelzeile, Spalte, Schema, Eigentumsuebergabe und Share. Jede hat eine Gegenprobe, die belegt, dass sie ausloest, und dieselbe Pruefung belegt, dass die beiden erlaubten Formen `tables/{id}/rows` und `rows/simple` durchgehen.
- Das Budget-Gate ist wieder scharf: Messung 12801 Bytes vom 2026-08-21, Gate 15000, und zusaetzlich ein Deckel von 1400 Bytes je Werkzeug. Die Gegenprobe mit einem kuenstlich auf 700 gesenkten Deckel liefert Exit-Code 1 und nennt neun Werkzeuge samt Groesse.
- Die Altlast des Abnahmeskripts ist aufgeloest: es erwartet 18 Werkzeuge und ruft sie auch, inklusive der drei, die es bisher nie angefasst hat.

## Messwerte fuer Phase 11 (TOOL-15)

Phase 11 schreibt das Gate auf dieser Messung fort:

| Groesse | Wert |
|---------|------|
| `tools/list` mit 18 Werkzeugen | 12801 Bytes (vorher 11268 bei 16) |
| `BUDGET_BYTES` | 15000 (12801 plus 15 Prozent = 14721, aufgerundet auf 500) |
| `MAX_TOOL_BYTES` | 1400 |
| `tables_browse` | 751 Bytes |
| `tables_create_row` | 780 Bytes |
| Groesstes Werkzeug heute | `calendar_create_event`, 1351 Bytes |
| Freiraum zum Gate | 2199 Bytes |

Die Vorhersage der Recherche (rund 1310 Bytes fuer beide Schemata) lag 221 Bytes unter dem
gemessenen Zuwachs von 1531 Bytes. Das aendert nichts an der Anhebung, weil sie gegen die
Messung und nicht gegen die Schaetzung erfolgt.

## Task Commits

1. **Task 1: Registrierung und die fuenf eingefrorenen Stellen im Oberflaechen-Test** - `df1c941` (feat)
2. **Task 2: Destruktiv-Gate erweitern und Budget-Gate neu verankern** - `a71d479` (test)
3. **Task 3: Dreisprachige READMEs, Doku-Zahlen und Changelog** - `3077fea` (docs)

## Files Created/Modified

- `src/mcp_connector/server/reg_tables.py` (neu, 70 Zeilen) - beide Werkzeuge, `Literal`-Enum fuer `level`, leere Strings statt `None` fuer `table_id` und `cursor`, `ge=1`/`le=MAX_LIMIT` fuer `limit`, Modul-Docstring mit der Begruendung fuer das bedingungslose Listen (SRV-04)
- `tests/contract/test_tool_surface.py` - `EXPECTED_TOOLS` und `CREATE_TOOLS` erweitert, vier Zahlenstellen auf 18 beziehungsweise 16 gezogen, zwei neue Tests (Enum plus ehrliche Annotationen, Verbotsliste je Ebene)
- `tests/contract/test_no_destructive_calls.py` - fuenf neue Nadeln, die Scan-Logik in `_violations` gezogen, eine parametrisierte Gegenprobe je Nadel, ein Test fuer die zwei erlaubten Routen, `ALLOWED_MODULE_STATE` wird gezaehlt
- `scripts/check_tool_budget.py` - neue Messzeile, `BUDGET_BYTES = 15_000`, `MAX_TOOL_BYTES = 1400` und ein zweiter Fehlerzweig, der Name und Groesse des ueberschreitenden Werkzeugs nennt
- `scripts/acceptance_all_tools.py` - `EXPECTED_TOOLS = 18`, Docstring-Zahlen, ein Tables-Block nach dem Muster der Deck-Ausnahme und `prepare_context` im Lauf, `_first_text_column` als Helfer
- `README.md`, `README.de.md`, `README.fr.md` - je zwei Tabellenzeilen (`read` beziehungsweise `create-only`) und die Werkzeugzahl an je zwei Stellen
- `docs/client-setup.md`, `docs/conference-demo.md`, `docs/conference-talk.md`, `docs/oauth-setup.md` - Produktaussagen auf 18, datierte Messwerte unveraendert
- `docs/store-submission.md` - der Zeiger auf `tests/contract/test_tool_surface.py`, weil die Seite zwei datierte Zaehlungen enthaelt und ihn bisher nicht trug
- `CHANGELOG.md` - `## [Unreleased]` mit einem `### Added`-Abschnitt aus Nutzersicht, keine Version, kein Tag
- `vulture_whitelist.py` - beide Werkzeugnamen dazu, die Zahl im Abschnittstitel ersatzlos entfernt
- `.github/workflows/ci.yml` - der Kommentar am Budget-Schritt nennt jetzt den Pro-Werkzeug-Deckel und die richtige Ordnungszahl

## Decisions Made

- **Das Budget-Gate folgt der Formel des bestehenden Eintrags.** 12801 plus 15 Prozent sind 14721, aufgerundet auf die naechsten 500 sind 15000. Das ist bewusst dieselbe Rechnung, die TOOL-15 fuer den Meilenstein-Endstand festschreibt, damit die Anhebung in Phase 11 keine neue Regel braucht. Die alte Messzeile vom 2026-08-14 bleibt stehen, weil eine Regression nur zuordenbar ist, solange die Zahl lesbar ist, von der sie abweicht.
- **Der Pro-Werkzeug-Deckel ist die eigentliche Behauptung.** 2199 Bytes Freiraum bedeuten, dass ein neues Werkzeug mit Absatzbeschreibung die Summe nicht reisst. Genau diese Regression meldet der Deckel von 1400, und die Zahl steht nicht willkuerlich da: der heutige Ausreisser liegt bei 1351.
- **Die Nadeln sind auf die Anfuehrungszeichen-Form verankert.** `clients/tables.py` baut `f"/tables/{table}/rows/simple"` und `f"{V2_PREFIX}/{NODE_COLLECTION_TABLES}/{table}/rows"`. Eine Nadel `/rows/` traefe die erste Form, eine Nadel `apps/tables/api/1/rows` traefe keine realistische Schreibzeile, weil das Prefix in diesem Projekt eine eigene Konstante ist. `"/rows/` und `"/columns/` treffen genau die Form, in der eine Einzelzeilen- oder Spaltenroute geschrieben werden muesste, und keine der beiden erlaubten. Beide Richtungen sind als Test formuliert, nicht als Kommentar.
- **`ALLOWED_MODULE_STATE` wird gezaehlt.** Der bestehende Test prueft, dass die zwei Eintraege existieren, nicht dass es nur zwei sind. Ein dritter Cache waere unbemerkt durchgegangen, obwohl er den Neustart-Beweis bricht (T-08-23).
- **Kein neuer Familienabschnitt in den READMEs.** Jede Familie hat dort einen Prosa-Abschnitt, Tables bekommt in diesem Plan keinen. Die Schreibgrenze steht in der Tabellenzeile ("existing rows are never changed") und in der Werkzeugbeschreibung, die der Contract-Test prueft. Ein Abschnitt in drei Sprachen ohne Review waere die typische Stelle, an der die Sprachfassungen auseinanderlaufen; er gehoert zur Release-Phase, die den Store-Text ohnehin schreibt.
- **TABLES-01 und TABLES-02 sind abgehakt.** Beide Anforderungstexte beginnen mit "Nutzer kann ... ueber `tables_browse`" beziehungsweise "`tables_create_row`". Mit der Registrierung ist beides aufrufbar, und 08-03 hat diesen Plan namentlich als die Stelle benannt, die sie abhakt. Der Live-Nachweis gegen eine echte Instanz bleibt Gegenstand von 08-05.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] `acceptance_all_tools.py` ruft die drei fehlenden Werkzeuge wirklich**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt nur `EXPECTED_TOOLS = 18` plus die zwei Docstring-Zahlen. Die Namensliste am Ende des Skripts stand aber bei 15 Eintraegen, `prepare_context`, `tables_browse` und `tables_create_row` fehlten darin. Das Skript haette also "OK: all 15 tools answered" gemeldet, obwohl sein eigener Docstring 18 verspricht, und Verifikationsschritt 5 von Plan 08-05 ("meldet 18 antwortende Werkzeuge") waere unerreichbar gewesen.
- **Fix:** Die drei Namen in die Erwartungsmenge und in den Lauf. `prepare_context` wird unbedingt gerufen, der Tables-Block folgt der bestehenden Deck-Ausnahme: eine Tabelle und ihre Spalten sind keine Connector-Faehigkeiten, also wird die vom Integrationslauf hinterlassene Tabelle benutzt und der Schreibfall als `SKIP` gemeldet, wenn keine existiert. Die Spalte wird nach `type == "text"` ausgewaehlt, weil ein Textwert in einer Zahlenspalte ein 400 der App ist und kein defektes Werkzeug.
- **Files modified:** `scripts/acceptance_all_tools.py`
- **Verification:** `grep -n "EXPECTED_TOOLS = 18"` trifft, `grep -c "15 tools"` ist 0, `uv run ruff check .` und `uv run pyright` gruen. Der volle Lauf braucht eine Instanz und gehoert zu 08-05.
- **Committed in:** `a71d479`

**2. [Rule 3 - Blocking] `vulture_whitelist.py` um beide Werkzeugnamen erweitert**
- **Found during:** Task 3 (Verifikationsschritt 3 des Plans)
- **Issue:** `uv run vulture src/mcp_connector vulture_whitelist.py` meldete `tables_browse` und `tables_create_row` als unbenutzte Funktionen (Exit 3). Registrierte Werkzeuge haben konstruktionsbedingt keinen Aufrufer im eigenen Code, deshalb stehen die anderen zwoelf Werkzeugnamen schon in der Whitelist. Der Plan nennt die Datei nicht.
- **Fix:** Beide Namen in den bestehenden Abschnitt. Zusaetzlich die Zahl aus dem Abschnittstitel entfernt ("The fifteen tool functions" bei zwoelf gelisteten Namen war schon vorher falsch): der Titel verweist jetzt auf den Contract-Test, der die Zahl als einziger wahr halten kann.
- **Files modified:** `vulture_whitelist.py`
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` und `uv run vulture src scripts vulture_whitelist.py` beide Exit 0
- **Committed in:** `3077fea`

**3. [Rule 1 - Bug] Zwei Doku-Seiten mehr als geplant, plus der CI-Kommentar**
- **Found during:** Task 3 (Vollstaendigkeitspruefung)
- **Issue:** Der Doku-Waechter meldet nur Seiten ohne Zeiger auf den Contract-Test. Damit blieben drei falsche Produktaussagen unentdeckt: `docs/conference-talk.md` sagt zweimal "Sixteen tools" (ausgeschrieben, also fuer den Waechter unsichtbar), `docs/oauth-setup.md` sagt "The set is 16 today", und der Kommentar am Budget-Schritt in `.github/workflows/ci.yml` beschreibt das Gate als Schutz gegen ein "sixteenth tool" ohne den neuen Pro-Werkzeug-Deckel.
- **Fix:** Alle drei aktualisiert (18 beziehungsweise "Eighteen", der CI-Kommentar nennt den Deckel und die richtige Ordnungszahl). `docs/store-submission.md` bekommt den fehlenden Zeiger, weil seine zwei Zaehlungen datierte Messwerte eines Laufs vom 2026-08-19 sind und nach der Regel des Waechters stehenbleiben duerfen. Die datierten Werte in `client-setup.md`, `oauth-setup.md`, `spike-discovery.md` und `conference-demo.md` bleiben unveraendert.
- **Files modified:** `docs/conference-talk.md`, `docs/oauth-setup.md`, `docs/store-submission.md`, `.github/workflows/ci.yml`
- **Verification:** Repo-weiter grep auf `16 tools`, `== 16`, `all 16`, `tools=16`, `The 16`, `Die 16`, `Les 16`, `sixteen`, `15 tools` ausserhalb von `.planning/`: die restlichen Treffer sind ausschliesslich datierte Laufprotokolle, ein historischer Changelog-Eintrag und die zwei Docstring-Stellen, die absichtlich von einem alten Lauf erzaehlen
- **Committed in:** `3077fea`

**4. [Rule 1 - Bug] Der zitierte Fehlersatz in `conference-demo.md` beschrieb einen Zustand, den es nicht mehr gibt**
- **Found during:** Task 3
- **Issue:** Der Plan verlangt, die woertlich zitierte Fehlermeldung des Abnahmeskripts "an die neue Zahl anzupassen". Nach Task 2 gibt es diese Meldung im Lauf aber gar nicht mehr, weil erwartete und gelistete Zahl uebereinstimmen. Eine Zahlenkorrektur haette einen Fehlschlag beschrieben, der nicht mehr eintritt.
- **Fix:** Der Absatz erzaehlt jetzt, was er ist: die Meldung `FAIL tools/list expected 15 tools, got 16` ist das Protokoll des Laufs vom 2026-08-20, die Drift ist mit diesem Plan geschlossen, und eine solche Zeile ist ab jetzt wieder ein echter Befund. Der Satz ueber die Abnahmematrix nennt zusaetzlich die zwei `SKIP`-Faelle, die das Skript nach Abweichung 1 melden kann.
- **Files modified:** `docs/conference-demo.md`
- **Verification:** `uv run pytest tests/contract/test_tool_surface.py -q` gruen, inklusive des Doku-Waechters
- **Committed in:** `3077fea`

---

**Total deviations:** 4 auto-fixed (1 fehlende kritische Funktion, 1 blockierendes Gate, 2 falsche Aussagen in mitgeltenden Dateien)
**Impact on plan:** Keine Umfangsaenderung an der Registry, keine neue Abhaengigkeit, kein neues oeffentliches Symbol ausser den zwei geplanten Werkzeugen. Vier Dateien mehr als die Plan-Liste (`vulture_whitelist.py`, `docs/conference-talk.md`, `docs/store-submission.md`, `.github/workflows/ci.yml`), alle vier aus Gates oder aus der vom Plan verlangten Vollstaendigkeitspruefung.

## Issues Encountered

- **Zwei Tests waren nach Task 1 und Task 2 absichtlich rot.** `test_the_readme_permission_table_matches_the_live_registry` und `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from` vergleichen die Registry mit `README.md` und den Doku-Seiten. Zwischen Registrierung (Task 1) und Doku-Nachzug (Task 3) kann keine der beiden gruen sein, weil beide Seiten des Vergleichs in verschiedenen Aufgaben liegen: eine Aenderung der Doku vor der Registrierung waere genauso rot, nur in der anderen Richtung. Das ist eine Eigenschaft des vom Plan gewaehlten Aufgabenschnitts und keine offene Frage. Ab `3077fea` ist die Datei gruen, und die drei Commits werden gemeinsam gepusht, sodass die CI keinen roten Stand sieht.
- Zwei Zwischenlaeufe von `ruff format` verlangten eine andere Umbruchstelle in der Nadel-Tabelle und im Fehlerzweig des Budget-Skripts; im selben Task behoben.

## Known Stubs

Keine. Beide Werkzeuge sind vollstaendig verdrahtet und liefern echte Daten der Instanz, die Fachlogik dahinter stammt vollstaendig aus Plan 08-03. Was fehlt, fehlt absichtlich und ist im Modul-Docstring benannt: kein Update, kein Delete, kein Anlegen von Spalten, Tabellen oder Schemata und kein Share-Pfad.

## User Setup Required

Keine, keine externe Dienstkonfiguration und keine neue Abhaengigkeit (`pyproject.toml` und `uv.lock` unangetastet, T-08-SC bleibt `accept`).

## Verification

| Pruefung | Ergebnis |
|----------|----------|
| `uv run pytest -q` (Default-Auswahl) | gruen, keine Regression |
| `uv run pytest tests/contract/ -q` | gruen, inklusive der fuenf neuen Gegenproben und der zwei neuen Oberflaechen-Tests |
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen, 180 Dateien |
| `uv run pyright` (ganzes Projekt) | 0 errors, 0 warnings |
| `uv run vulture src scripts vulture_whitelist.py` | Exit 0 |
| `uv run python scripts/check_tool_budget.py` | 12801 Bytes, 18 Werkzeuge, Gate 15000, Exit 0 |
| Gegenprobe Pro-Werkzeug-Deckel (kuenstlich 700) | Exit 1, neun Werkzeuge namentlich mit Groesse |
| `grep -v '^\s*#' tests/contract/test_tool_surface.py \| grep -c "== 16\|all 16\|16 tools"` | 0 |
| Level-Enum, `$defs`, `output_schema`, Annotationen beider Werkzeuge | live gegen die Registry geprueft, alle wie gefordert |
| Em-Dash und En-Dash in den neun geaenderten Textdateien | keine |
| Verbotenes Vokabular in `README.de.md`, `README.fr.md`, `CHANGELOG.md` | keine Treffer |
| Repo-weiter grep auf stehengebliebene Zahlen ausserhalb `.planning/` | nur datierte Laufprotokolle und ein historischer Changelog-Eintrag |
| `git diff --diff-filter=D` ueber die drei Commits | leer, keine Datei geloescht |

## Next Phase Readiness

- Plan 08-05 kann direkt starten: beide Werkzeuge sind gelistet, `uv run python scripts/acceptance_all_tools.py` erwartet und ruft 18 Werkzeuge, und der Tables-Block des Skripts meldet `SKIP` statt `FAIL`, solange keine Tabelle mit Textspalte existiert. Der Integrationslauf von 08-05 hinterlaesst genau diese Tabelle.
- Phase 11 (TOOL-15) schreibt das Gate auf der Messung oben fort. Der Freiraum von 2199 Bytes traegt Talk und Mail nicht: vier weitere Werkzeuge in der Groessenordnung der Tables-Paare (rund 3000 Bytes) reissen die Summe, was der Zweck des Gates ist.
- Offen und bewusst ausgeklammert: der Prosa-Abschnitt "Tables" in den drei READMEs (Vorbild der Deck-Abschnitt), der zur Release-Phase gehoert, weil dort der Store-Text ohnehin dreisprachig nachgezogen wird.
- Der Doku-Waechter sieht ausgeschriebene Zahlen ("Sixteen tools") nicht. Das ist beim naechsten Nachzug erneut von Hand zu pruefen, oder der Waechter bekommt in Phase 11 die ausgeschriebenen Formen dazu.

## Self-Check: PASSED

- `src/mcp_connector/server/reg_tables.py` FOUND (70 Zeilen, `min_lines` 60, enthaelt `Literal`)
- `tests/contract/test_tool_surface.py` FOUND, enthaelt `tables_create_row`
- `tests/contract/test_no_destructive_calls.py` FOUND, enthaelt kein `apps/tables/api/1/rows`, sondern die praeziseren Nadeln samt Begruendung (siehe Decisions)
- `scripts/check_tool_budget.py` FOUND, enthaelt `MAX_TOOL_BYTES`
- Commit `df1c941` FOUND, Commit `a71d479` FOUND, Commit `3077fea` FOUND
- `key_links` des Plans nachgewiesen: `tables_tools.browse` und `tables_tools.create_row` in `reg_tables.py`, `_load_registrations` in `server/__init__.py` unveraendert, der README-Waechter parst die drei neuen Zellen
- Alle Abnahmekriterien der drei Aufgaben nachgelaufen; die einzige Ausnahme ist in "Issues Encountered" begruendet und ab dem dritten Commit ebenfalls gruen

---
*Phase: 08-erreichbarkeits-spike-und-tables*
*Completed: 2026-08-21*
