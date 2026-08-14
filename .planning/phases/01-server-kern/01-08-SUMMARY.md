---
phase: 01-server-kern
plan: 08
subsystem: api
tags: [carddav, vobject, lxml, vcard, addressbook, graceful-degradation, respx, mcp]

# Dependency graph
requires:
  - phase: 01-02
    provides: httpx-Pool pro Event-Loop, Credentials, ToolError, xml.py mit hardened_parser und parse_multistatus, Server-Layer mit READ_ONLY/graceful/compact
  - phase: 01-03
    provides: compose.test.yml und bootstrap_test_nc.sh (occ dav:create-addressbook alice contacts, bob ohne Adressbuch)
  - phase: 01-07
    provides: xml.parse_root fuer Discovery-Baeume, Muster fuer DAV-Client plus Tool-Vertikale plus Fan-out mit degraded
provides:
  - CardDAV-Client mit Adressbuch-Discovery unter addressbooks/users/<uid>/ und serverseitig gefiltertem addressbook-query
  - contacts_search als rein lesendes Tool mit Fan-out ueber alle eigenen Adressbuecher
  - Filter gegen die generierten Adressbuecher (z-server-generated--, z-app-generated--)
  - Fixtures und Testnetz fuer vCard-Parsing inklusive Minimalkontakt und Umlauten
affects: [01-11-chatgpt-profil, 01-13-prepare-context, 01-14-tool-set]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "vCards ausschliesslich per vobject lesen, jeder Property-Zugriff defensiv, fehlende Felder sind der Normalfall (D-17)"
    - "Der Suchbegriff wird serverseitig gefiltert: ein c:filter mit test=anyof, je ein c:prop-filter fuer FN und EMAIL, plus c:limit/c:nresults"
    - "Generierte Adressbuecher gehoeren nicht zu den Adressbuechern des Nutzers und werden vor der Abfrage verworfen"
    - "Fan-out ueber Adressbuecher per asyncio.gather mit Timeout je Buch, Ausfall wird als degraded benannt"
    - "Limit wird gedeckelt statt abgelehnt und reist als c:nresults zum Server"
    - "Leere Felder erscheinen nicht in der Antwort: full_name und addressbook immer, der Rest nur wenn gefuellt"

key-files:
  created:
    - src/mcp_connector/nextcloud/clients/carddav.py
    - src/mcp_connector/tools/contacts.py
    - src/mcp_connector/server/reg_contacts.py
    - tests/fixtures/carddav_addressbooks_207.xml
    - tests/fixtures/carddav_report_207.xml
    - tests/unit/test_carddav_client.py
    - tests/unit/test_contacts_tools.py
    - tests/integration/test_contacts_search.py
  modified:
    - tests/contract/test_tool_surface.py
    - README.md

key-decisions:
  - "Die generierten Adressbuecher z-server-generated--system (Kontenverzeichnis der Instanz) und z-app-generated--contactsinteraction--recent werden verworfen: sonst waere der Fall 'kein Adressbuch' auf jedem echten Server unerreichbar und eine Namenssuche wuerde nebenbei das Kontenverzeichnis der ganzen Organisation ausliefern (T-01-56)"
  - "Kein capabilities.require_app fuer Kontakte: CardDAV steckt in der Core-App dav, die Contacts-App ist nur die Weboberflaeche; die ehrliche Vorbedingung ist 'existiert eine Collection'"
  - "Ein Konto ohne eigenes Adressbuch ist ein Fehler mit Loesungshinweis auf occ dav:create-addressbook, niemals eine leere Trefferliste"
  - "Ein zu grosses Limit wird gedeckelt statt abgelehnt: die Frage war legitim, nur die Zahl war unbrauchbar, und ein Fehler kostet nur eine zweite Runde"
  - "Faellt ein einzelnes Adressbuch aus, kommt es als degraded-Eintrag zurueck; fallen alle aus, ist das ein Fehler und keine leere Kontaktliste"
  - "Eine unlesbare vCard wird als Fehler mit Hinweis gemeldet, nicht halb geparst: eine falsche Mailadresse ist schlimmer als eine fehlende"
  - "Die Antwort enthaelt nie die rohe vCard, nur full_name, emails, phones, organization, addressbook und uid, leere Felder entfallen"
  - "Kein CardDAV-Schreibpfad in dieser Phase; das Modul enthaelt nachweisbar keine schreibende Methode und ein Test grept darauf"

patterns-established:
  - "Pattern: DAV-Vertikale = clients/<protokoll>.py (Discovery, Body-Bau, Parsing) plus tools/<domaene>.py (Fan-out, Deckelung, Antwortform) plus server/reg_<domaene>.py (Annotationen, Schema-Diaet)"
  - "Pattern: Live-Befunde gegen die Test-Nextcloud korrigieren Fixture-Annahmen, der Integrationstest belegt danach den Rohbefund (hier: die generierten Adressbuecher kommen wirklich ueber die Leitung)"

requirements-completed: [TOOL-05]

# Metrics
duration: 25 min
completed: 2026-08-14
---

# Phase 1 Plan 08: Kontakte-Suche ueber CardDAV Summary

**contacts_search als rein lesende Vertikale: Adressbuch-Discovery unter addressbooks/users/, serverseitig gefilterter addressbook-query mit lxml und vCard-Parsing per vobject, inklusive Filter gegen die generierten Adressbuecher.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-14T16:57:00Z
- **Completed:** 2026-08-14T17:22:00Z
- **Tasks:** 2 (beide TDD, RED vor GREEN)
- **Files modified:** 10 (8 neu, 2 geaendert)

## Accomplishments

- CardDAV-Client mit Discovery unter `addressbooks/users/<uid>/` (das `users/`-Segment, das CalDAV nicht hat) und `addressbook-query` REPORT mit genau einem `c:filter test="anyof"`, `c:prop-filter` fuer FN und EMAIL, `c:text-match` mit `collation="i;unicode-casemap"` und `c:limit`/`c:nresults`
- `contacts_search`: Fan-out ueber alle eigenen Adressbuecher, hartes Timeout je Buch, `degraded`-Feld bei Teilausfall, gedeckeltes Limit, kompakte Antwort ohne Rohdaten
- Live gegen Nextcloud 34 verifiziert und dabei eine falsche Planannahme korrigiert: jedes je authentifizierte Konto besitzt zwei generierte Adressbuecher, die jetzt gefiltert werden
- 36 neue Unit-Tests, 1 Contract-Test, 5 Integrationstests; Tool-Budget bleibt bei 5419 von 24000 Bytes fuer 8 Tools

## Task Commits

1. **Task 1: CardDAV-Client mit Discovery und addressbook-query**
   - `a43092e` test(01-08): failing tests plus Fixtures (RED)
   - `9d9dfea` feat(01-08): CardDAV-Client (GREEN)
2. **Task 2: Tool contacts_search**
   - `46050f0` test(01-08): failing unit, contract und integration tests (RED)
   - `0536156` feat(01-08): contacts_search (GREEN)
   - `89617fd` fix(01-08): generierte Adressbuecher aus der Discovery entfernen (Deviation, siehe unten)
   - `8152478` docs(01-08): Kontakte-Abschnitt im README

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/carddav.py` - Discovery, `build_addressbook_query`, `query_contacts`, `parse_contacts`, `parse_vcard`, Statusuebersetzung; ohne jede schreibende Methode
- `src/mcp_connector/tools/contacts.py` - `search()` mit Fan-out, Timeout je Adressbuch, `degraded`, Deckelung, Sortierung und Antwortprojektion
- `src/mcp_connector/server/reg_contacts.py` - Registrierung mit READ_ONLY, `structured_output=False`, `@graceful`
- `tests/fixtures/carddav_addressbooks_207.xml` - Discovery mit zwei eigenen Buechern, zwei generierten und einer normalen Collection
- `tests/fixtures/carddav_report_207.xml` - drei Kontakte: voll, minimal (nur FN), mit Umlauten und Ampersand
- `tests/unit/test_carddav_client.py` - 22 Faelle: Pfad, Query-Body, Escaping, Minimalkontakt, Statuscodes, Grep-Gates
- `tests/unit/test_contacts_tools.py` - 11 Faelle: Fan-out, degraded, Deckelung, leerer Begriff, Nulltreffer, keine Rohdaten
- `tests/integration/test_contacts_search.py` - 5 Faelle gegen die laufende Nextcloud 34
- `tests/contract/test_tool_surface.py` - `contacts_search` in `tools/list` mit read_only_hint, ohne output_schema
- `README.md` - Abschnitt "Contacts": Umfang, gefilterte generierte Buecher, Fehlerfall

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die wichtigste: generierte Adressbuecher zaehlen nicht als Adressbuecher des Nutzers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Generierte Adressbuecher machten die Discovery und den Fehlerfall falsch**

- **Found during:** Task 2 (Integrationslauf gegen die Test-Nextcloud)
- **Issue:** Der Plan nimmt an, bob habe kein Adressbuch. Der Integrationstest schlug fehl (`DID NOT RAISE ToolError`). Nachmessung an der laufenden NC 34: jedes Konto, das sich einmal authentifiziert hat, besitzt `z-server-generated--system` ("Accounts", das Kontenverzeichnis der Instanz) und `z-app-generated--contactsinteraction--recent` ("Recently contacted"). Beide sind fuer sabre vollwertige `card:addressbook`-Collections. Damit war der Fall "kein Adressbuch" auf keinem echten Server erreichbar, und jede Namenssuche haette nebenbei das Kontenverzeichnis der ganzen Instanz zurueckgegeben (T-01-56).
- **Fix:** `GENERATED_PREFIXES` in `carddav.py`, Filterung in `parse_addressbook_home`; Fixture um beide Collections erweitert; zwei neue Unit-Tests; Integrationstest belegt, dass der Server die beiden wirklich sendet und die Discovery sie trotzdem nicht fuehrt.
- **Files modified:** `src/mcp_connector/nextcloud/clients/carddav.py`, `tests/fixtures/carddav_addressbooks_207.xml`, `tests/unit/test_carddav_client.py`, `tests/integration/test_contacts_search.py`
- **Verification:** `uv run pytest -q` gruen, `uv run pytest -m integration -q` 23 Tests gruen (vorher 1 Fehlschlag)
- **Committed in:** `89617fd`

**2. [Rule 2 - Missing Critical] README-Abschnitt zu den Kontakten**

- **Found during:** Task 2 (Abschluss)
- **Issue:** Die README fuehrt `contacts_search` in der Tool-Tabelle, beschreibt aber weder den Suchumfang (nur FN und EMAIL werden gematcht, Telefonnummern werden ausgegeben und nicht durchsucht) noch die neu eingefuehrte Filterung der generierten Adressbuecher. Die globale Regel "Doku-Seite mitziehen" verlangt das, und 01-07 hat denselben Weg fuer den Kalender genommen.
- **Fix:** Abschnitt "Contacts" mit Suchumfang, Fan-out und degraded, Filterbegruendung und Fehlerfall.
- **Files modified:** `README.md`
- **Verification:** Sichtpruefung, keine Em-Dashes, echte Umlaute (englischer Text, daher keine Umlaute noetig)
- **Committed in:** `8152478`

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 fehlende kritische Dokumentation)
**Impact on plan:** Beide notwendig. Deviation 1 korrigiert eine Planannahme, die gegen die Realitaet des Servers nicht haltbar war, und schliesst nebenbei eine Informationsabfluss-Flaeche. Kein Scope Creep, kein Schreibpfad hinzugekommen.

## Verification Results

| Gate | Ergebnis |
|------|----------|
| `uv run pytest tests/unit/test_carddav_client.py -q` | 27 passed (Vorgabe: mindestens 7 Faelle) |
| `uv run pytest tests/unit/test_contacts_tools.py -q` | 11 passed (Vorgabe: mindestens 6 Faelle) |
| `uv run pytest -q` (Default-Suite) | 312 passed |
| `uv run pytest tests/contract -q` | 6 passed, darunter `contacts_search` read_only_hint=True, open_world_hint=False, output_schema=None |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 5419 Bytes fuer 8 Tools bei Budget 24000 |
| `uv run pytest -m integration -q --collect-only` | sammelt `tests/integration/test_contacts_search.py: 5` fehlerfrei |
| `uv run pytest -m integration -q` (Docker NC 34) | 23 passed |
| `uv run ruff check .` / `ruff format --check .` | All checks passed / 60 files already formatted |
| Grep-Gegenprobe Schreibpfad | `grep -E "PUT\|DELETE\|MOVE\|PROPPATCH" carddav.py` findet nichts (Exit 1) |
| Escaping und Minimalkontakt | `test_a_search_term_with_ampersand_and_angle_bracket_is_escaped`, `test_a_contact_without_email_phone_and_organization_never_crashes` |

## Threat Model Coverage

| Threat | Umsetzung |
|--------|-----------|
| T-01-53 Injection im Suchbegriff | Body ausschliesslich per lxml, Test mit `Meier & <Söhne> "AG"` |
| T-01-54 XXE und Billion Laughs | Alle Antworten ueber `xml.parse_root` / `parse_multistatus` mit `hardened_parser` |
| T-01-55 Regex-vCard-Parsing | vobject, Grep-Test gegen `import re` und `re.compile` |
| T-01-56 Fremde Kontaktdaten | Keine Nutzerparameter, Credentials aus dem Auth-Kanal, Kontenverzeichnis der Instanz zusaetzlich ausgeschlossen |
| T-01-57 Kein Schreibpfad | Modul kennt nur PROPFIND und REPORT, Grep-Test in Unit- und Tool-Ebene |
| T-01-58 Sehr grosse Adressbuecher | `c:limit`/`c:nresults` im Request, Deckelung im Tool, 20 Sekunden Timeout je Buch |
| T-01-59 Path Traversal ueber die URI | `safe_segment` plus `quote`, URI stammt immer aus der Discovery, sechs parametrisierte Testfaelle |
| T-01-60 SSRF | accept, kein URL-Parameter, Basis-URL aus der Umgebung |

## Known Stubs

Keine. Alle Felder der Antwort stammen aus echten Serverdaten.

## Issues Encountered

- Der Integrationslauf zeigte, dass bob entgegen der Planannahme Adressbuecher besitzt. Aufgeloest als Deviation 1, statt den Test abzuschwaechen.
- Offene Frage fuer eine spaetere Phase: In Organisationen leben Kolleginnen und Kollegen im Systemadressbuch "Accounts". Dieses bewusst auszulassen, ist die konservative Vorgabe. Ein spaeterer optionaler Parameter (etwa `include_directory`) koennte es explizit oeffnen, das ist eine Produkt- und Datenschutzentscheidung und keine Standardeinstellung.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Der letzte fehlende Lesekanal fuer das ChatGPT-Profil (01-11) und fuer `prepare_context` (01-13) steht.
- `tools/list` fuehrt jetzt 8 der 15 kuratierten Tools; das Budget-Gate hat viel Luft.
- Offen in Wave 4: 01-05 (files_search, files_list) und 01-09 (Deck).

## Self-Check: PASSED

- Alle unter `key-files.created` genannten Dateien existieren auf der Platte (geprueft mit `[ -f ]`).
- Alle sechs Commit-Hashes sind in `git log` auffindbar.
- Alle Akzeptanzkriterien beider Tasks wurden erneut ausgefuehrt und sind gruen (siehe Verification Results).

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
