---
phase: 09-talk
plan: 04
subsystem: api
tags: [mcp-registrierung, literal-enum, contract-test, destruktiv-gate, token-budget, store-beschreibung, i18n]

# Dependency graph
requires:
  - phase: 09-talk
    provides: "tools/talk.py mit browse(level=conversations|messages) und send, Konstanten LEVELS, DEFAULT_LIMIT, MAX_LIMIT (Plan 09-03)"
  - phase: 09-talk
    provides: "config.talk_send_enabled und der sechste Admin-Wert talk_send samt NC_MCP_TALK_SEND (Plan 09-02)"
  - phase: 09-talk
    provides: "clients/talk.py mit genau drei Pfadformen: ROOM_PREFIX, CHAT_PREFIX-Lesen, CHAT_PREFIX-Senden (Plan 09-01)"
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "server/reg_tables.py als Registrierungsvorbild, das dreiteilige Gate-Muster (Nadel, Gegenprobe, positive Liste), die datierte Messzeile im Budget-Gate"
provides:
  - "server/reg_talk.py: talk_browse (READ_ONLY) und talk_send (CREATE_ONLY), Level als Literal-Enum, leere Strings statt None, kein $defs, kein Output-Schema"
  - "Die Werkzeugzahl 20 identisch in Registry, Contract-Test, beiden Skripten, den drei READMEs und der Doku"
  - "Zehn Talk-Nadeln im Destruktiv-Gate, jede mit eigener Gegenprobe, plus ALLOWED_TALK_ROUTES als positive Behauptung ueber die genau drei Pfadformen"
  - "Gemessenes Token-Budget bei 20 Werkzeugen: 14312 Bytes, BUDGET_BYTES unveraendert 15000"
  - "Talk in allen drei Store-Beschreibungen von appinfo/info.xml, ohne das verbotene Wort und ohne SEC-01 vorwegzunehmen"
  - "docs/oauth-setup.md nennt sechs Formularfelder samt talk_send und NC_MCP_TALK_SEND"
affects: [09-05 Live-Nachweis, 10 SEC-01, 11 TOOL-15 Budget-Fortschreibung, 11 Release 0.1.4]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine neue Werkzeugfamilie sichern heisst: Nadel plus Gegenprobe plus positive Liste der erlaubten Pfadformen, weil ein fehlendes verbotenes Verb (PUT) sonst ein Loch laesst"
    - "Eine Messzeile ohne Anhebung: das Budget-Gate dokumentiert die neue Messung und laesst BUDGET_BYTES stehen, damit eine Anhebung immer gegen einen Bedarf und nie aus Gewohnheit erfolgt"
    - "Der README-Nachzug gehoert in denselben Commit wie die Registrierung, weil zwei Contract-Tests die Tabelle und die Zahl gegen die lebende Registry pruefen"

key-files:
  created:
    - src/mcp_connector/server/reg_talk.py
  modified:
    - tests/contract/test_tool_surface.py
    - tests/contract/test_no_destructive_calls.py
    - scripts/check_tool_budget.py
    - scripts/acceptance_all_tools.py
    - README.md
    - README.de.md
    - README.fr.md
    - docs/oauth-setup.md
    - docs/client-setup.md
    - docs/conference-demo.md
    - docs/conference-talk.md
    - appinfo/info.xml
    - CHANGELOG.md
    - vulture_whitelist.py

key-decisions:
  - "Die drei READMEs sind im Commit von Task 1 mitgezogen und nicht erst in Task 3: test_the_readme_permission_table_matches_the_live_registry und der Doku-Zahlen-Waechter lesen die lebende Registry, also waere jeder Zwischenstand ein rotes Gate gewesen, genau das, was dieser Plan vermeiden soll"
  - "BUDGET_BYTES bleibt 15000: gemessen 14312 Bytes bei 20 Werkzeugen (talk_browse 861, talk_send 648), 688 Bytes Luft; die neue Messzeile steht trotzdem im Skript, damit TOOL-15 in Phase 11 auf einer lesbaren Zahl aufsetzt"
  - "Keine elfte Nadel neben /share: die Anhang-Route von Talk ist chat/{token}/share, das deckt die bestehende Tables-Nadel mit ab, und der Kommentar sagt es, damit niemand eine Dublette danebenlegt"
  - "Die zitierte Fehlermeldung in docs/conference-demo.md bleibt im Wortlaut ihres datierten Laufs (expected 15 tools, got 16); richtiggestellt ist der Satz darum herum, weil ein datierter Messwert nach der Regel des Waechters und nach T-09-37 nicht umgeschrieben wird"
  - "TALK-04 ist erfuellt und wird abgehakt: die drei vom Wortlaut verlangten Schichten stehen (Formular, Overlay-Lesepfad, Wirkung am Werkzeug) und das Werkzeug, an dem der Schalter wirkt, ist ab jetzt registriert. TALK-01 bis TALK-03 bleiben Pending, weil Plan 09-05 sie im Frontmatter fuehrt und den Live-Nachweis liefert"
  - "talk_browse und talk_send stehen in vulture_whitelist.py, im bestehenden Block der Werkzeugfunktionen ohne sichtbaren Aufrufer, genau wie tables_browse und tables_create_row"

patterns-established:
  - "Wenn eine Familie einen Schreibweg ohne verbotenes Verb anbietet, wird sie von beiden Seiten eingezaeunt: die verbotenen Segmente mit je einer Gegenprobe und die erlaubten Pfadformen als positive Behauptung"
  - "Eine Doku-Zahl wird nachgezogen, ein datierter Messwert nicht: die Unterscheidung steht im Waechter, und der Satz um den Messwert herum traegt die aktuelle Zahl"

requirements-completed: [TALK-04]

# Metrics
duration: 33 min
completed: 2026-08-21
---

# Phase 9 Plan 04: Registrierung und Nachzug der Talk-Familie Summary

**`reg_talk.py` mit `talk_browse` als Literal-Enum-Lesewerkzeug und `talk_send` als sechstem CREATE_ONLY-Schreibweg, dazu der vollstaendige Nachzug in einem Zug: 20 statt 18 an jeder eingefrorenen Stelle, zehn Talk-Nadeln im Destruktiv-Gate mit je einer Gegenprobe plus die positive Behauptung ueber genau drei Pfadformen, ein auf 14312 Bytes gemessenes Token-Budget ohne Anhebung, und Talk in allen drei Store-Beschreibungen.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-08-21T12:00:00Z
- **Completed:** 2026-08-21T12:33:00Z
- **Tasks:** 3
- **Files modified:** 15 (1 neu, 14 geaendert)

## Accomplishments

- Die zwei Werkzeuge sind Teil des kuratierten Satzes, und die Registry beantwortet es selbst: ein In-Memory-Client listet 20 Werkzeuge, `talk_browse` und `talk_send` sind dabei, beide ohne Output-Schema, das Level-Enum ist genau `["conversations", "messages"]`, und in keinem der zwei Schemata kommt `$defs` vor. Kein Eintrag in `server/__init__.py` war noetig: `_load_registrations()` findet `reg_talk.py` per pkgutil.
- Die Annotationen sagen die Wahrheit und ein Test haelt jede einzelne fest: `talk_browse` mit `read_only_hint` True, `talk_send` mit `read_only_hint` False, `destructive_hint` False und `idempotent_hint` False, beide mit `open_world_hint` False. Die Ehrlichkeit von `destructive_hint` ist keine Behauptung, sondern die Folge des Gates darunter: im Client existiert kein Update- und kein Delete-Pfad.
- Das Destruktiv-Gate ist um die Talk-Schreibwege erweitert, die **kein verbotenes Verb brauchen**: zehn Nadeln (`/schedule`, `/summarize`, `/reminder`, `/pin`, `/attachment`, `/read`, `/favorite`, `/notify`, `/participants`, `/archive`), jede mit einem Begruendungssatz und jede mit einer Gegenprobe, die zweierlei behauptet: die angehaengte Zeile wird gemeldet, und der echte Quellcode von `clients/talk.py` ist vorher sauber. Dazu `ALLOWED_TALK_ROUTES` mit genau drei Pfadformen, von denen keine das Gate ausloest. Der Kommentarblock sagt, warum diese Familie beide Haelften braucht: **PUT ist in diesem Projekt kein verbotenes Verb**, weil `files_upload` es benutzt.
- Das Budget-Gate ist an einer Messung verankert statt an einer Gewohnheit: gemessen **14312 Bytes bei 20 Werkzeugen**, also **nicht** gerissen. `BUDGET_BYTES` bleibt bei 15000, `MAX_TOOL_BYTES` bleibt bei 1400, und die neue datierte Messzeile steht trotzdem im Skript, weil TOOL-15 in Phase 11 auf dieser Zahl fortschreibt. Die zwei neuen Schemata einzeln: `talk_browse` 861 Bytes, `talk_send` 648 Bytes; der Ausreisser bleibt `calendar_create_event` mit 1351.
- Alle drei Sprachfassungen sagen dasselbe wie die Registry: je eine Tabellenzeile `talk_browse | read` und `talk_send | create-only`, je zwei Produktaussagen auf 20 gezogen, und der README-Waechter parst die Zellen gegen die lebende Registry. Die deutschen und franzoesischen Zeilen tragen echte Umlaute, Akzente und Cedille.
- Die drei Store-Beschreibungen nennen Talk in der Familienliste und sagen in einem Satz, was der Ausgangskanal kann und was nicht: nur senden, kein Bearbeiten, kein Loeschen, kein Hinterlegen fuer spaeteren Versand, und eine Administratorin kann das Senden instanzweit abschalten. Das verbotene Wort kommt im gesamten Manifest-Elementtext nicht vor, SEC-01 ist nicht vorweggenommen, und `<version>` und `<image-tag>` sind unberuehrt (`git diff appinfo/info.xml` nennt keine der beiden Zeilen).
- Alle Gates gruen: `uv run pytest -q` ueber die ganze Default-Auswahl, `ruff check .`, `ruff format --check .`, `pyright` (0 errors), `vulture src/mcp_connector vulture_whitelist.py` (Exit 0), `scripts/check_tool_budget.py` (Exit 0, 20 Werkzeuge).

## Task Commits

Each task was committed atomically:

1. **Task 1: reg_talk.py und die eingefrorenen Stellen im Oberflaechen-Test** - `afe3b98` (feat)
2. **Task 2: Destruktiv-Gate, Budget-Gate und Abnahmeskript** - `d8e93ff` (test)
3. **Task 3: Store-Beschreibungen, Doku-Zahlen und Changelog** - `36120dd` (docs)

## Die Messung fuer TOOL-15 in Phase 11

Der Plan verlangt sie ausdruecklich in dieser Zusammenfassung:

| Groesse | Wert |
|---------|------|
| `tools/list` bei 18 Werkzeugen (Stand vor diesem Plan) | 12801 Bytes |
| `tools/list` bei 20 Werkzeugen (Stand nach diesem Plan) | 14312 Bytes |
| Schema von `talk_browse` einzeln | 861 Bytes |
| Schema von `talk_send` einzeln | 648 Bytes |
| `BUDGET_BYTES` | unveraendert 15000 |
| Verbleibende Luft | 688 Bytes |
| `MAX_TOOL_BYTES` | unveraendert 1400, groesstes Werkzeug bleibt `calendar_create_event` mit 1351 |

Die zwei neuen Schemata kosten zusammen 1509 Bytes, die Summe stimmt mit der Gesamtmessung
auf zwei Bytes Trennzeichen ueberein. Wer in Phase 11 ein weiteres Werkzeug registriert, hat
688 Bytes zur Verfuegung, bevor eine Anhebung faellig ist, und die Anhebung braucht dann eine
neue datierte Messzeile in derselben Schreibweise.

## Files Created/Modified

- `src/mcp_connector/server/reg_talk.py` (neu, 72 Zeilen) - eins zu eins nach `reg_tables.py`. Modul-Docstring mit drei Aussagen: die Logik liegt in `mcp_connector.tools.talk`, das Level ist ein `Literal` und damit ein Enum, und beide Werkzeuge werden unbedingt gelistet (SRV-04), auch bei abgeschaltetem Sende-Schalter. Die Beschreibung von `talk_browse` sagt, dass die Nachrichtenebene neueste zuerst liefert und die Fortsetzung in die Vergangenheit laeuft; die von `talk_send` besteht aus genau zwei Saetzen (kein Bearbeiten, kein Loeschen; ein Timeout heisst nicht, dass nichts gesendet wurde, und der naechste Schritt ist Nachlesen).
- `tests/contract/test_tool_surface.py` - `EXPECTED_TOOLS` um beide Namen, `CREATE_TOOLS` um `talk_send` samt Kommentar auf sechs Schreibwege, `len(tools) == 20` samt Docstring und Meldung, "all 20 schemas", "six create-only tools, fourteen pure reads", plus zwei neue Tests: `test_the_two_talk_tools_are_listed_and_browse_takes_an_enum_level` und `test_there_is_no_tool_per_talk_level_and_no_second_send`.
- `tests/contract/test_no_destructive_calls.py` - zehn neue `FORBIDDEN`-Eintraege, `TALK_ROUTES` mit einer Gegenprobenzeile je Nadel, `ALLOWED_TALK_ROUTES` mit genau drei Pfadformen, drei neue Tests (parametrisierte Gegenprobe, "jede Nadel hat eine Gegenprobe", "die drei echten Routen bleiben erlaubt"). `ALLOWED_MODULE_STATE` unveraendert bei zwei Eintraegen.
- `scripts/check_tool_budget.py` - dritte datierte Messzeile (20 Werkzeuge, 14312 Bytes, keine Anhebung), Begruendung der Nicht-Anhebung, "nineteenth" auf "twenty-first" korrigiert. `BUDGET_BYTES` und `MAX_TOOL_BYTES` unveraendert.
- `scripts/acceptance_all_tools.py` - `EXPECTED_TOOLS = 20`, Zahl im Docstring an beiden Stellen, `CHANGELOG_TYPE = 4`, Talk-Abschnitt im Lauf (Konversationen, dann Verlauf der ersten, dann Senden in die erste mit `can_send` und nicht Typ 4, Markierung mit echten Umlauten), Helfer `_sendable_conversation`, beide Namen in der Erwartungsmenge, dritte SKIP-Ausnahme im Docstring dokumentiert.
- `README.md`, `README.de.md`, `README.fr.md` - je zwei Tabellenzeilen direkt unter den Tables-Zeilen und je zwei Produktaussagen auf 20.
- `docs/oauth-setup.md` - "carries six fields", sechste Tabellenzeile (`talk_send`, `NC_MCP_TALK_SEND`), ein Absatz, der sagt, dass nicht jedes Feld dieser Form OAuth betrifft und dass der Wert nach einem Deaktivieren und Aktivieren wirkt, "the same six keys", und zwei Stellen "The set is 18 today" auf 20.
- `docs/client-setup.md` - die zwei Produktaussagen auf 20; die datierten Messwerte alter Laeufe (16 Werkzeuge) bleiben, die Seite zeigt auf `tests/contract/test_tool_surface.py`.
- `docs/conference-demo.md` - `tools=20`, "twenty tools", dritter SKIP-Fall (Talk-Konversation) im Satz ueber die Abnahmematrix, und die aktuelle Erwartung neben dem unveraenderten datierten Zitat.
- `docs/conference-talk.md` - drei Stellen "eighteen in the development tree" auf "twenty" (Folienstichpunkt, Sprechnotiz, Belegtabelle).
- `appinfo/info.xml` - die drei `<description>`-Bloecke: Talk in der Familienliste und ein Satz zum Ausgangskanal samt Schalter, in EN, DE und FR.
- `CHANGELOG.md` - Einleitungssatz der unveroeffentlichten Fassung um Talk erweitert, drei `### Added`-Eintraege aus Nutzersicht (Lesen ohne Spur im Konto, ein Sendeweg mit Absagen und ohne Bearbeiten oder Loeschen, der instanzweite Schalter). Keine Versionsnummer geaendert, kein Tag gesetzt.
- `vulture_whitelist.py` - `talk_browse` und `talk_send` im bestehenden Block der Werkzeugfunktionen ohne sichtbaren Aufrufer.

## Decisions Made

- **Der README-Nachzug steht in Task 1.** Zwei Tests dieser Datei lesen die lebende Registry und vergleichen sie mit `README.md`: die Berechtigungstabelle und der Doku-Zahlen-Waechter. Sobald `reg_talk.py` existiert, sind beide rot, und das Akzeptanzkriterium von Task 1 verlangt ein gruenes `test_tool_surface.py`. Die drei Sprachfassungen sind zusammen gezogen worden, weil eine englische Tabelle mit zwei Zeilen mehr als die deutsche genau der Zwischenzustand ist, den die Dreisprachigkeitsregel verbietet.
- **Keine Anhebung des Budgets.** 14312 gegen 15000 ist keine Grenzverletzung, und die Regel dieses Skripts lautet, dass eine Anhebung eine Messung braucht, nicht dass jede Phase anhebt. Die Messzeile steht aber im Skript und nicht nur hier, weil eine Regression nur zuordenbar ist, solange die Zahl, von der sie abweicht, lesbar bleibt.
- **Der Deckel von 1400 hat nicht gewackelt.** Die Beschreibung von `talk_send` ist mit zwei Saetzen geplant und mit zwei Saetzen geschrieben; das ganze Werkzeug kostet 648 Bytes, also weniger als die Haelfte des Deckels und halb so viel wie `calendar_create_event`.
- **`/share` bleibt eine Nadel und bekommt keine Dublette.** Der Begruendungstext dieser Nadel nennt jetzt beide Familien, und der Kommentarblock sagt ausdruecklich, dass eine elfte Nadel daneben nur nach mehr Sicherheit aussehen wuerde.
- **Das datierte Zitat in `docs/conference-demo.md` bleibt woertlich.** Der Plan verlangt, die zitierte Fehlermeldung an die neue Zahl anzupassen; die Zeile ist aber ausdruecklich als Messung eines Laufs vom 2026-08-20 eingefuehrt, und T-09-37 desselben Plans sagt, dass datierte Messwerte stehenbleiben. Richtiggestellt ist deshalb der Satz darum herum ("twenty since plan 09-04"), und ein Halbsatz sagt jetzt, dass das Zitat mitsamt Datum so bleibt, wie es aufgezeichnet wurde.
- **TALK-04 wird abgehakt, TALK-01 bis TALK-03 nicht.** Der Wortlaut von TALK-04 verlangt den Schalter samt Wirkung am Werkzeug und die drei Schichten Formular, Overlay-Lesepfad, Wirkung; alle drei sind belegt, und mit dieser Registrierung existiert das Werkzeug, an dem die dritte Schicht wirkt. TALK-01 bis TALK-03 stehen im Frontmatter von Plan 09-05, der den Live-Nachweis der Nebenwirkungsfreiheit und des Sendevorgangs fuehrt; sie dort abzuhaken ist die Reihenfolge, die die Phase seit Plan 09-01 einhaelt.
- **Zwei Doku-Seiten mehr als geplant.** `docs/oauth-setup.md` sagte an zwei Stellen "The set is 18 today" und `docs/conference-talk.md` an drei Stellen "eighteen in the development tree". Keine dieser fuenf Stellen faellt in das Muster des Waechters (`tools=(\d+)` oder `(\d+) tools`), also waere die falsche Zahl gruen liegen geblieben. Der Auftrag dieses Plans ist die Zahl 20 an jeder Stelle, die sie behauptet, nicht nur an jeder Stelle, die ein Test findet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die drei READMEs mussten in den Commit von Task 1**

- **Found during:** Task 1
- **Issue:** Das Akzeptanzkriterium von Task 1 verlangt ein gruenes `uv run pytest tests/contract/test_tool_surface.py -q`. Zwei Tests dieser Datei lesen `README.md` gegen die lebende Registry (`test_the_readme_permission_table_matches_the_live_registry` und `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from`), und beide waren mit registrierten Werkzeugen und alter Tabelle rot. Der Plan hatte die READMEs Task 3 zugeordnet.
- **Fix:** Die zwei Tabellenzeilen und die zwei Produktaussagen aller drei Sprachfassungen sind Teil des Commits von Task 1. Task 3 hat die restlichen Textdateien getragen (Doku, Manifest, Changelog).
- **Files modified:** README.md, README.de.md, README.fr.md
- **Verification:** `uv run pytest tests/contract/test_tool_surface.py -q` nach dem Commit von Task 1 gruen; die Akzeptanzkriterien von Task 3 zu den READMEs sind unveraendert erfuellt und einzeln nachgeprueft.
- **Committed in:** `afe3b98` (Task 1)

**2. [Rule 3 - Blocking] Die zwei neuen Werkzeugfunktionen liessen das vulture-Gate reissen**

- **Found during:** Task 1
- **Issue:** `vulture` laeuft in diesem Projekt bei voller Konfidenz und meldete `talk_browse` und `talk_send` als unbenutzte Funktionen (60 Prozent). Sie werden vom `@mcp.tool`-Dekorator registriert und von der MCP-Laufzeit gerufen, nie aus eigenem Code. Verifikationsschritt 3 des Plans verlangt ein gruenes vulture.
- **Fix:** Beide Namen in den bestehenden Block "The tool functions without a visible caller" von `vulture_whitelist.py`, in Registry-Reihenfolge hinter `tables_create_row`. Der Block nennt seinen Grund und seine Absicherung (`test_tool_surface.py`) schon und braucht keine neue Begruendung; die Zahl steht dort bewusst nicht.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` Exit-Code 0; ohne die zwei Zeilen meldet es genau diese zwei Namen.
- **Committed in:** `afe3b98` (Task 1)

**3. [Rule 1 - Bug] Eine Beispielzahl im Docstring des Waechters wurde vom eigenen Grep-Gate getroffen**

- **Found during:** Task 1
- **Issue:** Das Verifikationskommando von Task 1 verlangt null Treffer fuer `all 18` ausserhalb von Kommentaren. Der Docstring von `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from` benutzte "all 18 tools" als Beispiel fuer eine Produktaussage, und ein Docstring ist fuer `grep -v "^\s*#"` kein Kommentar. Derselbe Fall wie der `attendeePermissions`-Docstring in Plan 09-03.
- **Fix:** Das Beispiel nennt jetzt "all 20 tools", also die aktuelle Zahl. Die Aussage des Docstrings bleibt, und das Beispiel bleibt ein gueltiges Beispiel.
- **Files modified:** tests/contract/test_tool_surface.py
- **Verification:** `grep -v "^\s*#" tests/contract/test_tool_surface.py | grep -c "== 18\|all 18\|18 tools"` ist 0.
- **Committed in:** `afe3b98` (Task 1)

**4. [Rule 1 - Bug] Fuenf Doku-Stellen mit der Zahl 18, die kein Gate findet**

- **Found during:** Task 3
- **Issue:** `docs/oauth-setup.md` sagt zweimal "The set is 18 today", `docs/conference-talk.md` dreimal "eighteen in the development tree". Das Muster des Waechters ist `tools=(\d+)` oder `(\d+) tools`; keine der fuenf Stellen passt darauf, alle fuenf waeren also mit falscher Zahl gruen geblieben. `docs/conference-talk.md` steht nicht in der Dateiliste des Plans.
- **Fix:** Alle fuenf auf 20 gezogen, mit der Aufzaehlung "prepare_context und die zwei Paare Tables und Talk" statt der alten "die zwei Tables-Werkzeuge". Die datierten Messwerte derselben Seiten (`tools=15`, "16 tools") bleiben unangetastet.
- **Files modified:** docs/oauth-setup.md, docs/conference-talk.md
- **Verification:** `grep -rn "18 tools\|tools=18\|all 18\|eighteen\|achtzehn\|dix-huit"` ueber READMEs, `docs/`, `src/`, `tests/`, `scripts/`, `appinfo/` und `CHANGELOG.md` liefert nur noch die datierte Messzeile in `scripts/check_tool_budget.py`.
- **Committed in:** `36120dd` (Task 3)

---

**Total deviations:** 4 auto-fixed (2 blockierend, 2 Fehler in bestehenden Aussagen)
**Impact on plan:** Kein Scope-Zuwachs, keine offene Absage. Zwei Punkte sind die Reihenfolge
innerhalb des Plans (der README-Nachzug muss dort stehen, wo die Registrierung steht) und ein
Gate dieses Repos, das der Plan nicht vorhergesehen hat (vulture bei voller Konfidenz, exakt
wie in den Plaenen 09-01 und 09-02). Zwei sind falsche Zahlen, die dieser Plan sichtbar
gemacht hat, eine davon in einer Datei ausserhalb seiner Liste. Die einzige inhaltliche
Abweichung von einer Plan-Anweisung ist das datierte Zitat in `docs/conference-demo.md`, das
nach der eigenen Regel des Plans (T-09-37) nicht umgeschrieben werden durfte.

## Issues Encountered

- Zwei Anweisungen des Plans widersprachen sich an einer Stelle: Task 3 verlangt, die woertlich
  zitierte Fehlermeldung des Abnahmeskripts an die neue Zahl anzupassen, und das
  `<threat_model>` desselben Plans fuehrt datierte Doku-Messwerte als "accept" mit der
  Begruendung, dass sie stehenbleiben duerfen. Aufgeloest zugunsten des Threat-Registers: das
  Zitat bleibt, der Satz darum herum traegt die aktuelle Zahl und sagt ausserdem, dass das
  Zitat mit Datum so bleibt.
- Der Plan nennt fuenf eingefrorene Stellen in `test_tool_surface.py`; es waren sieben. Neben
  den genannten trug der Kommentar ueber `EXPECTED_TOOLS` die Formulierung "a nineteenth tool"
  und der Docstring des Doku-Waechters das Beispiel "all 18 tools". Beide sind mitgezogen, der
  zweite zwingend, weil das eigene Grep-Gate des Plans darauf angeschlagen hat.

## Known Stubs

Keine. Beide Werkzeuge sind verdrahtet, gelistet, annotiert und mit Contract-Tests belegt. Was
fehlt, ist ausdruecklich nicht Teil dieses Plans: der Live-Nachweis gegen eine laufende
Nextcloud (Plan 09-05, Nebenwirkungsfreiheit gemessen vor und nach dem Lesen, ein echter
Sendevorgang, die Absage in einer schreibgeschuetzten Konversation, der Zwei-Konten-Beweis) und
der SEC-01-Doku-Abschnitt zur Exfiltrationskette (Phase 10, weil Mail-Lesen noch nicht
existiert).

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche gegenueber dem `<threat_model>` des Plans: kein
neuer Netzwerkendpunkt, kein neuer Auth-Pfad, kein Dateizugriff, keine Schema-Aenderung an
einer Vertrauensgrenze und keine neue Abhaengigkeit (`pyproject.toml` und `uv.lock` sind
unberuehrt). Die einzige neue Zusage an eine Vertrauensgrenze ist `tools/list`, und sie ist mit
Contract-Tests, Gate-Nadeln und der Budget-Messung genau dort abgesichert, wo das Register es
verlangt.

## User Setup Required

None - no external service configuration required. Der Sende-Schalter ist an per Default, eine
bestehende Installation aendert ihr Verhalten mit diesem Plan nur insofern, als zwei Werkzeuge
in `tools/list` dazukommen. Wer das Senden abschalten will, setzt das sechste Feld unter
`Administration settings, Security, MCP Connector` oder die Deploy-Variable
`NC_MCP_TALK_SEND=0` und deaktiviert und aktiviert die App einmal.

## Next Phase Readiness

- Plan 09-05 kann sich auf den Live-Teil beschraenken: die Werkzeuge sind aufrufbar, das
  Abnahmeskript hat seinen Talk-Abschnitt samt SKIP-Regel, und die Unit-Seite aller vier
  Aussagen steht aus Plan 09-03.
- Phase 10 (SEC-01) findet die Store-Beschreibungen so vor, dass der Satz zur
  Exfiltrationskette dort ergaenzt werden kann, ohne die Familienliste noch einmal anzufassen;
  der Satz zum Ausgangskanal und zum Schalter steht schon in allen drei Sprachen.
- Phase 11 (TOOL-15) schreibt das Budget-Gate auf 14312 Bytes bei 20 Werkzeugen fort. 688
  Bytes Luft bis zur Anhebung, und die Anhebung braucht eine neue datierte Messzeile.
- Phase 11 (Release 0.1.4) findet einen `### Added`-Abschnitt unter der unveroeffentlichten
  Fassung mit drei Eintraegen aus Nutzersicht vor. `<version>` und `<image-tag>` sind
  unberuehrt, es ist kein Tag gesetzt.
- TALK-01 bis TALK-03 bleiben Pending und gehoeren Plan 09-05. TALK-04 ist mit diesem Plan
  erfuellt.

## Self-Check

- `src/mcp_connector/server/reg_talk.py` FOUND (72 Zeilen, `Literal` vorhanden, `talk_tools.browse` und `talk_tools.send` aufgerufen)
- `tests/contract/test_tool_surface.py` FOUND (`talk_send` vorhanden, `len(tools) == 20`)
- `tests/contract/test_no_destructive_calls.py` FOUND (`ALLOWED_TALK_ROUTES` vorhanden, zehn Talk-Nadeln, `ALLOWED_MODULE_STATE` mit zwei Eintraegen)
- `scripts/acceptance_all_tools.py` FOUND (`EXPECTED_TOOLS = 20`, `talk_browse` und `talk_send` je zweimal)
- `appinfo/info.xml` FOUND (Talk in allen drei Beschreibungen, kein Backtick, keine Tabelle, mindestens zwei Absaetze je Sprache, kein verbotenes Wort im Elementtext)
- Commit `afe3b98` FOUND
- Commit `d8e93ff` FOUND
- Commit `36120dd` FOUND
- `uv run pytest -q` gruen ueber die ganze Default-Auswahl; `tests/contract/` einzeln gruen
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors), `uv run vulture src/mcp_connector vulture_whitelist.py` (Exit 0) alle gruen
- `uv run python scripts/check_tool_budget.py` Exit-Code 0, 14312 Bytes bei 20 Werkzeugen
- Die lebende Registry per In-Memory-Client: 20 Werkzeuge, Level-Enum `["conversations", "messages"]`, kein `$defs`, beide `output_schema is None`, alle sechs Annotations-Behauptungen wahr
- `grep -v "^\s*#" tests/contract/test_tool_surface.py | grep -c "== 18\|all 18\|18 tools"` ist 0
- Repo-weiter Grep auf veraltete Toolzahlen (`18 tools`, `tools=18`, `all 18`, `eighteen`, `achtzehn`, `dix-huit`) findet nur die datierte Messzeile in `scripts/check_tool_budget.py`
- `git diff appinfo/info.xml` ohne Zeile mit `<version>` oder `<image-tag>`
- Kein Em-Dash, kein En-Dash und kein Zeichen oberhalb U+2100 in einer der 15 geaenderten Dateien

## Self-Check: PASSED

---
*Phase: 09-talk*
*Completed: 2026-08-21*
