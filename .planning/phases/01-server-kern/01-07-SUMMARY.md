---
phase: 01-server-kern
plan: 07
subsystem: api
tags: [caldav, icalendar, lxml, timezone, dst, graceful-degradation, respx, mcp]

# Dependency graph
requires:
  - phase: 01-02
    provides: httpx-Pool pro Event-Loop, Credentials, ToolError/ConflictError, ids.encode_event, xml.py mit hardened_parser, Server-Layer mit READ_ONLY/CREATE_ONLY/graceful
  - phase: 01-03
    provides: compose.test.yml und bootstrap_test_nc.sh (occ dav:create-calendar alice personal)
  - phase: 01-06
    provides: Muster fuer Tool-Vertikalen, Feststellung dass Kalender kein require_app braucht
provides:
  - CalDAV-Client mit Kalender-Discovery, serverseitig expandierendem calendar-query und create-only ICS-PUT
  - calendar_list_events mit Pflicht-Zeitraum, expliziter Timezone und degraded-Markierung pro Kalender
  - calendar_create_event mit IANA-VTIMEZONE, If-None-Match und serverseitig bestaetigten Zeiten
  - Vier-Faelle-Zeitmatrix als Regressionsnetz gegen die Platzhirsch-Bugs (D-18)
  - xml.parse_root als gemeinsamer Einstieg fuer DAV-Antworten mit XXE- und DTD-Schutz
affects: [01-08-kontakte, 01-11-chatgpt-profil, 01-14-tool-set]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Recurrence-Expansion serverseitig per c:expand, niemals clientseitig (keine RRULE-Iteration, kein recurring-ical-events)"
    - "Genau eine Zeitkonvertierung to_caldav_utc, ValueError bei naiver datetime"
    - "Ganztaegige Termine bleiben datetime.date, niemals Mitternacht mit Zone"
    - "Fan-out ueber Kalender per asyncio.gather mit Timeout je Kalender, Ausfall wird als degraded benannt"
    - "Der calendar-Parameter wird gegen die Discovery-Liste aufgeloest, nie ungeprueft in einen Pfad gehaengt"
    - "ICS ausschliesslich per icalendar erzeugt, DAV-XML ausschliesslich per lxml"

key-files:
  created:
    - src/mcp_connector/nextcloud/clients/caldav.py
    - src/mcp_connector/tools/calendar.py
    - src/mcp_connector/server/reg_calendar.py
    - tests/fixtures/caldav_calendars_207.xml
    - tests/fixtures/caldav_report_207.xml
    - tests/fixtures/event_allday.ics
    - tests/fixtures/event_berlin_dst.ics
    - tests/unit/test_caldav_client.py
    - tests/unit/test_calendar_tools.py
    - tests/integration/test_calendar_roundtrip.py
  modified:
    - src/mcp_connector/nextcloud/clients/xml.py
    - tests/contract/test_tool_surface.py
    - README.md

key-decisions:
  - "Serverseitige Expansion per c:expand ist die einzige Recurrence-Logik; das Modul enthaelt keine RRULE-Iteration und kein recurring-ical-events (D-17, Don't Hand-Roll)"
  - "to_caldav_utc wirft ValueError statt ToolError: eine naive datetime in dieser Tiefe ist ein Programmierfehler, die Nutzereingabe wird eine Schicht hoeher abgelehnt"
  - "Das halboffene Zeitfenster wird nicht korrigiert: ein Termin exakt auf end liegt ausserhalb, ein stilles Verschieben der Grenze wuerde zwei Aufrufer mit demselben Fenster unterschiedliche Ergebnisse sehen lassen"
  - "Der Zeitraum kommt als ISO-8601 mit Zone; die Abfrage laeuft immer in UTC, der timezone-Parameter aendert nur die Darstellung"
  - "Ganztaegige Termine behalten das exklusive Enddatum aus RFC 5545; ein Eintagestermin am 24. endet am 25. und das steht in README und Tool-Beschreibung"
  - "Faellt ein einzelner Kalender aus, kommt er als degraded-Eintrag zurueck; fallen alle aus, ist das ein Fehler und keine leere Terminliste"
  - "create_event bekommt einen optionalen timezone-Parameter, weil ein ISO-Offset keine IANA-Zone ist und ohne Zonennamen kein IANA-VTIMEZONE erzeugt werden kann"
  - "Nach dem PUT wird einmal per GET nachgelesen; scheitert das Nachlesen, bleibt created=true und confirmed=false, damit das Modell den Termin nicht ein zweites Mal anlegt"
  - "Der Objektname ist eine frische UUID und die ID bleibt event:<calendarUri>:<objektname>; alle expandierten Instanzen einer Serie teilen sich diese ID, weil sie ein Objekt sind"
  - "Kalender brauchen kein require_app: CalDAV ist Core-dav, die richtige Pruefung ist die Discovery (Fortschreibung der Feststellung aus 01-06)"

patterns-established:
  - "Pattern: jede Vertikale mit Formatrisiko bekommt eine benannte Testmatrix statt verstreuter Einzelfaelle"
  - "Pattern: Grep-Tests als Architekturgrenze (kein XML-Literal, keine eigene Recurrence-Iteration)"
  - "Pattern: Schreibpfade beweisen ihre Schreibgrenze im Integrationstest, nicht nur im Mock"

requirements-completed: [TOOL-02]

# Metrics
duration: 34 min
completed: 2026-08-14
---

# Phase 1 Plan 07: Kalender-Vertikale Summary

**CalDAV-Client mit serverseitiger Recurrence-Expansion plus calendar_list_events und calendar_create_event, abgesichert durch die Vier-Faelle-Zeitmatrix und einen Live-Beweis ueber die DST-Grenze Ende Oktober**

## Performance

- **Duration:** 34 min
- **Started:** 2026-08-14T16:50:00Z
- **Completed:** 2026-08-14T17:24:00Z
- **Tasks:** 3 (TDD, je RED und GREEN)
- **Files modified:** 13 (10 neu, 3 geaendert)

## Accomplishments

- CalDAV-Client: Discovery per PROPFIND Depth 1, `calendar-query` mit `c:expand` per lxml gebaut, create-only PUT mit `If-None-Match: *`, GET fuer die Rueckleseprobe
- Vier-Faelle-Zeitmatrix aus 01-RESEARCH.md Pitfall 4 vollstaendig als benannte Tests: Berlin-Termin gegen UTC-Fenster, Serie ueber die DST-Grenze, Ganztages-Termin, Fenster exakt auf der Termingrenze
- `calendar_list_events`: Pflicht-Zeitraum mit Zone, Fan-out ueber alle VEVENT-Kalender mit 20-Sekunden-Timeout je Kalender, `degraded`-Feld statt stiller Teilergebnisse, leeres Fenster liefert `events: []`
- `calendar_create_event`: ICS per icalendar, VTIMEZONE aus zoneinfo mit IANA-TZID, UUID-Objektname, Rueckleseprobe mit `confirmed`-Flag
- Kein Kalender im Konto erzeugt einen Fehler mit `occ dav:create-calendar`-Hinweis statt einer leeren Terminliste (Pitfall 3)
- Live-Beweis gegen Nextcloud 34.0.2: derselbe Berliner 09:00-Termin steht vor der Zeitumstellung auf `07:00Z` und danach auf `08:00Z`, in der Berlin-Darstellung beide Male auf `09:00` mit korrektem Offset

## Task Commits

1. **Task 1: CalDAV-Client mit Discovery, calendar-query und Zeitkonvertierung** - `3cd9090` (test, RED), `0931b3c` (feat, GREEN)
2. **Task 2: Tool calendar_list_events** - `1441a54` (test, RED), `446ae20` (feat, GREEN)
3. **Task 3: Tool calendar_create_event** - `f8f600d` (test, RED), `a1c4746` (feat, GREEN)
4. **Doku** - `9637dd6` (docs, README)

**Plan metadata:** siehe letzter `docs(01-07)`-Commit

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/caldav.py` - `to_caldav_utc`, `build_calendar_query`, `build_discovery_body`, `discover_calendars`, `parse_calendar_home`, `query_events`, `parse_ics`, `put_event`, `get_event`, `safe_segment`, Status-Mapping
- `src/mcp_connector/tools/calendar.py` - `list_events`, `create_event`, `parse_instant`, `resolve_zone`, `build_ics`, Fan-out mit Timeout, Darstellung in der Anzeige-Zone
- `src/mcp_connector/server/reg_calendar.py` - Registrierung beider Tools mit READ_ONLY bzw. CREATE_ONLY, `structured_output=False`, `@graceful`, Beispielwerte in den Parameter-Beschreibungen
- `tests/fixtures/caldav_calendars_207.xml` - Discovery-Antwort mit Home-Collection, VEVENT-Kalender, VTODO-only-Collection, Subscription, Scheduling-Inbox und einem URI mit Leerzeichen
- `tests/fixtures/caldav_report_207.xml` - expandierte `calendar-query`-Antwort mit Einzeltermin, zwei Serieninstanzen ueber die DST-Grenze und Ganztages-Termin
- `tests/fixtures/event_allday.ics` - `DTSTART;VALUE=DATE`-Objekt
- `tests/fixtures/event_berlin_dst.ics` - unexpandierte Serie mit `RRULE` und VTIMEZONE Europe/Berlin
- `tests/unit/test_caldav_client.py` - 31 Faelle inklusive der vier Matrix-Faelle, naive datetime, `end <= start` ohne Request, Pfad-Guard, 401, 404, 503, Redirect
- `tests/unit/test_calendar_tools.py` - 34 Faelle: Fan-out, Degradation, Darstellungs-Zone, Ganztag, ID-Aufloesung, ICS-Injection, Konflikt, fehlgeschlagene Rueckleseprobe
- `tests/integration/test_calendar_roundtrip.py` - 7 Faelle gegen die Docker-Nextcloud, inklusive DST-Beweis, halboffenem Fenster und verweigertem zweiten Schreibversuch
- `src/mcp_connector/nextcloud/clients/xml.py` - `parse_root` extrahiert, `parse_multistatus` nutzt ihn (unveraendertes Verhalten)
- `tests/contract/test_tool_surface.py` - Annotationen und Pflichtfelder beider Kalender-Tools
- `README.md` - Abschnitt "Calendar times" mit dem Zeitvertrag

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die vier wichtigsten:

- Die Expansion macht sabre, nicht dieser Prozess. Das Modul hat keine Zeile Recurrence-Logik, und ein Grep-Test haelt das so.
- Der `timezone`-Parameter ist reine Darstellung. Die Abfrage laeuft immer in UTC, die Instants aendern sich nie, nur ihre Schreibweise.
- Ein einzelner ausgefallener Kalender wird benannt, alle ausgefallenen Kalender sind ein Fehler. Eine leere Terminliste ohne Hinweis waere die gefaehrlichste Antwort, die dieses Tool geben kann.
- Nach dem Schreiben wird gelesen. Der Platzhirsch-Bug #544 (still verlorene Felder) ist nur so sichtbar, und das Ergebnis traegt `confirmed`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] create_event bekommt einen optionalen timezone-Parameter**
- **Found during:** Task 3
- **Issue:** Die Plan-Signatur nennt `summary, start, end, calendar, location, description, all_day`. Ein ISO-String traegt aber nur einen Offset (`+02:00`), keinen Zonennamen. Aus einem Offset laesst sich kein IANA-`VTIMEZONE` erzeugen, und genau das verlangt der behavior-Block ("niemals eine Windows-TZID").
- **Fix:** Optionaler Parameter `timezone` (IANA-Name). Ist er gesetzt, werden die Zeiten in dieser Zone geschrieben und ein `VTIMEZONE` aus `zoneinfo` erzeugt; ohne ihn werden UTC-Zeiten mit `Z` geschrieben, was RFC-konform ist und kein VTIMEZONE braucht. Symmetrisch zum `timezone`-Parameter von `calendar_list_events`.
- **Files modified:** src/mcp_connector/tools/calendar.py, src/mcp_connector/server/reg_calendar.py
- **Verification:** `test_a_zoned_event_carries_an_iana_vtimezone` und `test_without_a_zone_parameter_the_times_are_written_in_utc` gruen
- **Committed in:** `a1c4746`

**2. [Rule 2 - Missing Critical] Exklusives Enddatum bei Eintages-Ganztagsterminen**
- **Found during:** Task 3
- **Issue:** RFC 5545 zaehlt `DTEND` bei `VALUE=DATE` exklusiv. Ein Aufruf mit `start == end` haette einen Termin der Laenge null erzeugt, den sabre je nach Version ablehnt oder verschluckt.
- **Fix:** `start == end` wird auf `end = start + 1 Tag` korrigiert, `end < start` ist ein Fehler. Das Verhalten steht in der Tool-Beschreibung und im README, damit es nicht als versteckte Magie wirkt.
- **Files modified:** src/mcp_connector/tools/calendar.py, README.md
- **Verification:** `test_a_single_day_all_day_event_gets_the_exclusive_next_day_as_end` sowie der Integrationstest `test_an_all_day_event_stays_a_date_on_the_server`
- **Committed in:** `a1c4746`, `9637dd6`

**3. [Rule 2 - Missing Critical] Rueckleseprobe darf den Schreibvorgang nicht entwerten**
- **Found during:** Task 3
- **Issue:** Der Plan verlangt die Rueckleseprobe per GET. Scheitert dieser GET (5xx, Timeout), waere ein Fehler die falsche Antwort: der Termin existiert bereits, und dieser Server kann nichts loeschen. Das Modell wuerde ihn ein zweites Mal anlegen.
- **Fix:** Ein fehlgeschlagener GET liefert `created: true` plus `confirmed: false` mit den eigenen Werten.
- **Files modified:** src/mcp_connector/tools/calendar.py
- **Verification:** `test_a_failed_read_back_still_reports_the_event_as_created`
- **Committed in:** `a1c4746`

**4. [Rule 3 - Blocker] xml.parse_root extrahiert**
- **Found during:** Task 1
- **Issue:** `parse_multistatus` liefert Property-Werte als Text. Das `supported-calendar-component-set` traegt seine Bedeutung in Attributen (`<comp name="VEVENT"/>`), die dabei verloren gehen; die Discovery braucht den Baum. Ein eigener Parser im CalDAV-Modul haette den XXE- und DTD-Schutz dupliziert.
- **Fix:** `parse_root` in `xml.py` extrahiert (Parsen, DTD-Ablehnung, gehaerteter Parser), `parse_multistatus` nutzt ihn unveraendert weiter.
- **Files modified:** src/mcp_connector/nextcloud/clients/xml.py
- **Verification:** `tests/unit/test_xml.py` unveraendert gruen
- **Committed in:** `0931b3c`

**5. [Rule 1 - Bug] Falsche Assertion im Injection-Test**
- **Found during:** Task 3, GREEN-Lauf
- **Issue:** Der Test verlangte, dass die Zeichenfolge `BEGIN:VEVENT` genau einmal im ICS vorkommt. icalendar escaped einen Zeilenumbruch aber korrekt als `\n` innerhalb des SUMMARY-Werts, sodass die Zeichenfolge als Text im gefalteten Feld auftaucht, ohne je am Zeilenanfang zu stehen. Die Assertion war falsch, nicht die Implementierung.
- **Fix:** Der Test prueft jetzt die richtige Eigenschaft: keine entfaltete Zeile ausser der echten beginnt mit `BEGIN:VEVENT`, `\n` und `\;` sind escaped, und das Reparsen liefert genau einen VEVENT mit unveraendertem Summary.
- **Files modified:** tests/unit/test_calendar_tools.py
- **Verification:** `test_a_summary_with_ics_syntax_cannot_break_the_object` gruen
- **Committed in:** `a1c4746`

**6. [Rule 2 - Missing Critical] Contract-Tests fuer beide Kalender-Tools**
- **Found during:** Task 2 und Task 3
- **Issue:** Die Akzeptanzkriterien verlangen Nachweise ueber `tools/list` (Annotationen, kein Output-Schema, `start`/`end` als required), die Dateilisten der Tasks nennen `tests/contract/test_tool_surface.py` aber nicht.
- **Fix:** Zwei Contract-Tests ergaenzt, inklusive der Pruefung, dass der Beispielwert `+02:00` in der Beschreibung von `start` steht.
- **Files modified:** tests/contract/test_tool_surface.py
- **Verification:** `uv run pytest tests/contract -q` gruen
- **Committed in:** `1441a54` (RED), `f8f600d` (RED), gruen mit `446ae20` und `a1c4746`

---

**Total deviations:** 6 auto-fixed (1 Bug im Test, 4 fehlende kritische Funktionalitaet, 1 Blocker)
**Impact on plan:** Kein Scope-Zuwachs. Die einzige Vertragsaenderung ist der optionale `timezone`-Parameter von `calendar_create_event`, ohne den das geforderte IANA-`VTIMEZONE` nicht erzeugbar waere.

## Issues Encountered

- **Zonendaten kommen transitiv.** `zoneinfo` findet unter Windows ohne `tzdata` keine einzige Zone; das Paket ist derzeit eine harte Abhaengigkeit von `icalendar` und damit vorhanden. Da dieses Projekt `zoneinfo` selbst aufruft, waere ein direkter Pin sauberer. Nicht eigenmaechtig ergaenzt, weil neue Direkt-Dependencies dem Owner-Gate und `docs/dependency-audit.md` unterliegen. Vermerkt in "Next Phase Readiness".
- **Eine Serie hat eine ID, nicht viele.** Alle expandierten Instanzen einer Serie stammen aus einem Kalenderobjekt und teilen sich deshalb `event:<calendarUri>:<objektname>`. Das ist korrekt (die Adresse ist dieselbe), aber `fetch` in Plan 01-11 kann eine einzelne Instanz damit nicht adressieren. Dokumentiert im Modul-Docstring.
- **respx-Guard-Routen und `assert_all_called=True`** vertragen sich weiterhin nicht; die betroffenen Tests laufen mit `assert_all_called=False` und pruefen Call-Counts explizit (bekannt aus 01-06).

## User Setup Required

None - no external service configuration required. Die Integrationstests brauchen die lokale Docker-Nextcloud (`compose.test.yml` plus `scripts/bootstrap_test_nc.sh`); der Bootstrap legt `alice/personal` per `occ dav:create-calendar` an, was Pitfall 3 abdeckt.

## Next Phase Readiness

- Plan 01-08 (Kontakte) kann `xml.parse_root`, `safe_segment` und das Status-Mapping-Muster direkt uebernehmen; der CardDAV-Pfad hat eine andere Form (`addressbooks/users/<uid>/`), das Modul bleibt getrennt.
- Plan 01-11 (`fetch`) loest `event:<calendarUri>:<objektname>` ueber `caldav.get_event` auf; die Funktion existiert und ist getestet. Einzelne Serieninstanzen sind ueber diese ID nicht adressierbar.
- Offener Punkt fuer 01-14 oder die Dependency-Audit-Runde: `tzdata` als direkte Dependency pinnen, weil dieses Projekt `zoneinfo` selbst nutzt.
- Token-Budget: `tools/list` liegt bei 4931 Bytes fuer 7 Tools (Budget 24000); `calendar_create_event` ist mit 1352 Bytes das groesste Tool und ein Kandidat fuer die Schema-Diaet-Runde in 01-14.

## Self-Check: PASSED

- Alle 10 in `key-files.created` genannten Dateien existieren auf der Platte
- Alle 7 Commit-Hashes sind in `git log` auffindbar
- `uv run pytest -q` gruen (273 Tests, ohne Docker), `uv run pytest -m integration -q` gruen (18 Tests gegen Nextcloud 34.0.2, davon 7 neue Kalender-Tests)
- `uv run ruff check .` und `uv run ruff format --check .` sauber
- `uv run python scripts/check_tool_budget.py` Exit-Code 0

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
