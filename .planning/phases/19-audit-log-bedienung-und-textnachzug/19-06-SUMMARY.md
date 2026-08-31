---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 06
subsystem: exapp
tags: [audit-log, occ, handler, appapi, read, export, information-disclosure, t-19-20]

# Dependency graph
requires:
  - phase: 19
    plan: 01
    provides: "audit/text.printable als die eine Reinigungsregel und die korrigierte Längenprüfung im _payload-Muster"
  - phase: 19
    plan: 04
    provides: "AuditStore.read_entries samt READ_LIMIT_DEFAULT und READ_LIMIT_MAX"
  - phase: 18
    plan: 08
    provides: "exapp/audit_verify.py als Zeile-für-Zeile-Vorlage: Doppelprüfung, Status 200, Optionsleser, Grenzsatz"
provides:
  - "src/mcp_connector/exapp/audit_read.py: AUDIT_READ_PATH = /audit-read und audit_read_routes(env, *, store_provider)"
  - "Vier Optionsnamen in __all__: USER_OPTION=user, SINCE_OPTION=since, LIMIT_OPTION=limit, JSON_OPTION=json"
  - "Textform (neueste zuerst) und Maschinenform (Kettenreihenfolge) mit den Schlüsseln read, count, limit_applied, truncated, entries, note"
  - "tests/unit/test_exapp_audit_read.py: 39 Fälle, davon der url-Zähltest auf 13 und die Zeichengleichheit gegen audit_verify"
affects: [19-07, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Wert-Optionsleser neben dem Flaggenleser: None UND False heissen 'nicht gesetzt', nur eine nach strip() nicht leere Zeichenkette ist eine Eingabe"
    - "Jede Zahl aus einer Option wird an der Länge ihres Ziffernlaufs entschieden, bevor int() sie sieht"
    - "Die Ausgabeform wird im selben try gebaut wie die Abfrage, weil eine Zeile aus einer manipulierten Datei beim Rendern werfen kann und eine 500 die Antwort verschluckt"
    - "Eine Konstante, die zweimal buchstabiert steht, wird von einem Test gegen ihr Original gehalten (HEADER_ORIGIN_IP, JSON_OPTION, OCC_ENVELOPE, TRUE_WORDS, CHAIN_LIMIT, MAX_BODY_BYTES, MAX_ANNOUNCED_DIGITS)"

key-files:
  created:
    - src/mcp_connector/exapp/audit_read.py
    - tests/unit/test_exapp_audit_read.py
  modified:
    - vulture_whitelist.py

key-decisions:
  - "EIN Kommando mcp_connector:audit:read mit einer Maschinenform statt zweier Kommandos: der Namensraum ist im Code ausdrücklich für dieses zweite Kommando gebaut (occ.py:81-83)"
  - "Die Maschinenform ist EIN JSON-Dokument über json_response und nicht JSONL, gegen die Empfehlung der Recherche: json_response samt NO_STORE ist die etablierte Maschinenform dieses Projekts, und audit_verify trägt seine Daten in derselben Bauart. CSV oder JSONL können später Werte einer --format-Option werden"
  - "entries steht in KETTENREIHENFOLGE (reversed), die Textform zeigt die neuesten zuerst: der Speicher liefert immer jüngste zuerst, und die Umkehrung gehört laut 19-04 in den Handler"
  - "limit_applied wird hier gegen die importierte Konstante READ_LIMIT_MAX geklemmt und nicht nur im Speicher, weil truncated sonst falsch wäre: bei --limit 999999 kämen 5000 Zeilen zurück und truncated stünde auf falsch"
  - "MAX_OPTION_DIGITS ist eine eigene Zahl neben MAX_ANNOUNCED_DIGITS: die eine begrenzt eine Behauptung über einen Rumpf, die andere eine Behauptung über eine Anzahl"
  - "INSTANCE_KEYWORD = instance ist das eine Wort von --user, das kein Konto ist; der Preis (ein Konto namens instance ist über diese Option nicht adressierbar) steht im Docstring"
  - "--since nimmt ganze Tage und niemals ein Datum: eine Zahl ist mit isascii() und isdigit() prüfbar, ein Datum nicht"
  - "read_entries hat vulture_whitelist.py mit diesem Plan verlassen, so wie der Eintrag aus 19-04 es angekündigt hat"

patterns-established:
  - "Ein Handler ohne Manifesteintrag trägt die Begründung dafür als ersten Absatz seines Modul-Docstrings, und ein Test hält die Zahl der deklarierten Routen"
  - "Eine Ausgabefunktion für Werte aus fremder Hand ist total: ein Moment, den kein Kalender kennt, kostet seine Spalte und nie die ganze Antwort"

requirements-completed: []
# AUDIT-04 bleibt Pending: dieser Plan liefert den Handler, die Registrierung des Kommandos
# und die Verdrahtung der Route sind Plan 19-07. Vorher kann ein Administrator nichts tippen.
requirements-advanced: [AUDIT-04]

# Metrics
duration: 24min
completed: 2026-08-31
---

# Phase 19 Plan 06: Das Handlermodul des occ-Lesekommandos Summary

**`exapp/audit_read.py` ist der Zwilling von `audit_verify.py`: dieselbe Doppelprüfung (x-origin-ip 404, dann require_appapi 401, ohne zu sagen welche Prüfung sprach), Status 200 auf jeder anderen Antwort, drei Wert-Optionen deren Zahlen an der Länge ihres Ziffernlaufs entschieden werden, bevor `int()` sie sieht, eine Textform mit den neuesten Einträgen zuerst und eine Maschinenform in Kettenreihenfolge, und in keiner der beiden ein Parameterwert, eine Adresse, ein Pfad oder ein Meldungstext.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-08-31T15:07:00Z
- **Completed:** 2026-08-31T15:31:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 neu, 1 geändert)

## Accomplishments

- `src/mcp_connector/exapp/audit_read.py`, 611 Zeilen, in der Modulordnung der Vorlage:
  Docstring mit vier Begründungen, `__all__`, Pfadkonstante, Optionskonstanten, `OCC_ENVELOPE`,
  `HEADER_ORIGIN_IP`, `MAX_BODY_BYTES`, Fabrik, dann die privaten Helfer. Die endgültigen
  Konstanten, damit Plan 19-07 die Registrierung ohne Rückfrage bauen kann:

  ```python
  AUDIT_READ_PATH = "/audit-read"   # execute_handler: AUDIT_READ_PATH.removeprefix("/")
  USER_OPTION = "user"              # mode: optional, default None; Wert "instance" = Instanzkette
  SINCE_OPTION = "since"            # mode: optional, ganze Tage zurück, gedeckelt
  LIMIT_OPTION = "limit"            # mode: optional, Vorgabe READ_LIMIT_DEFAULT (200)
  JSON_OPTION = "json"              # mode: none, wie bei audit:verify
  MAX_SINCE_DAYS = 3650
  INSTANCE_KEYWORD = "instance"
  ```

  `audit_read_routes(env, *, store_provider)` gibt genau eine Route mit `methods=["POST"]`
  heraus, mit demselben Typalias `StoreProvider` wie die Vorlage.
- Die Doppelprüfung ist wortgleich übernommen: `grep -c "status_code=404"` und
  `grep -c "status_code=401"` je 1, `grep -c "status_code=5"` ohne Kommentarzeilen 0. Zwei
  Testfälle behaupten, dass keine der beiden Antworten einen Header, das Wort AppAPI oder einen
  Kontonamen nennt.
- Der Fehlerweg trägt allein `type(exc).__name__`: `grep -c "str(exc)"` ergibt 0. Drei Fälle
  behaupten Status 200, das Fehlen von `malformed` (dem Meldungstext), von `audit.sqlite3`, von
  `tmp_path` und von `Traceback`, und dass auch das Log der Instanz nur den Typnamen trägt.
- Jede Zahl geht durch `isascii()` und `isdigit()` **und** durch eine Längenprüfung ihres
  Ziffernlaufs, bevor `int()` sie sieht: `--limit ²` und `--limit 9*5000` fallen beide auf
  `READ_LIMIT_DEFAULT` zurück, ohne dass die Warnung den Wert nennt.
- Die Textform ist Kopfzeile, genau eine Zeile je Eintrag, `READ_NOTE`. Der Fall mit einem
  Kontonamen, der `\n - 99 - files_read` enthält, behauptet die Zeilenzahl der Antwort: ohne die
  Klammerung wäre er rot (Gegenprobe unten).
- Die Maschinenform trägt `read`, `count`, `limit_applied`, `truncated`, `entries`, `note` in
  dieser Reihenfolge, die Einträge aufsteigend nach `seq`, die Hashes als 64 Hex-Zeichen und
  `prev_hash` des ersten Eintrags als `GENESIS.hex()`.
- 39 Fälle in `tests/unit/test_exapp_audit_read.py` (der Plan verlangt 23), alle am echten
  SQLite-File in `tmp_path`; die einzige Ausnahme ist die Doppelgänger-Klasse `ExplodingStore`,
  weil eine kaputte Datei nichts ist, was diese Suite von Hand herstellen darf.
- `read_entries` hat `vulture_whitelist.py` verlassen, genau wie der Eintrag aus Plan 19-04 es
  angekündigt hatte; der Kommentar steht jetzt in der Form der Einträge von `sweep` und
  `verify_chains` ("gone from this list with plan 19-06").

## Task Commits

1. **Task 1: Das Handlermodul** - `a00dc09` (feat)
2. **Task 2: Grenzfälle, Optionsdraht und die Abwesenheit im Manifest** - `583d989` (test)
3. **Task 3: Ausgabeform, Klammerung und was nie in der Ausgabe steht** - `4500565` (test)

## Files Created/Modified

- `src/mcp_connector/exapp/audit_read.py` - neu: Handler, Pfad- und Optionskonstanten,
  Textform, Maschinenform, Wert-Optionsleser, Zahlenprüfung, Doppelprüfung
- `tests/unit/test_exapp_audit_read.py` - neu: 39 Fälle, `Deployment` mit echter Audit-Datei,
  `fill` für den Deckel, `raw_call` für rohe Header-Bytes, `ExplodingStore` für den Fehlerweg
- `vulture_whitelist.py` - `_.read_entries` entfernt, Begründung auf die Form "gone from this
  list with plan 19-06" umgeschrieben

## Decisions Made

- **Eine Maschinenform statt JSONL (Abweichung von der Recherche-Empfehlung).** Die Recherche
  hatte JSONL empfohlen, weil eine exportierte Zeile dann byteweise wie die kanonische Form
  aussieht. Dieser Plan tauscht den Vorteil gegen Einheitlichkeit: `json_response` samt
  `NO_STORE` ist die Maschinenform dieses Projekts, `audit_verify` trägt seine Daten in
  derselben Bauart neben dem Grenzsatz, und die Feldnamen bleiben die kanonischen. CSV oder
  JSONL können später Werte einer `--format`-Option werden, ohne dass sich etwas anderes ändert.
- **`limit_applied` wird hier geklemmt und nicht nur im Speicher.** Der Plan sagt, die harte
  Obergrenze liege in `store.read_entries` und werde hier nicht zweitgeschrieben. Der Handler
  klemmt trotzdem gegen die **importierte** Konstante `READ_LIMIT_MAX`, also gegen dieselbe
  Quelle: sonst stünde bei `--limit 999999` im Kopf und in `limit_applied` eine Zahl, die die
  Antwort gar nicht erreichen kann, und `truncated` (count == limit_applied) wäre falsch.
  Zweitgeschrieben ist damit nichts, die Zahl steht weiter genau einmal im Baum.
- **`CHAIN_LIMIT`, `TRUE_WORDS`, `OCC_ENVELOPE`, `MAX_BODY_BYTES` und `MAX_ANNOUNCED_DIGITS`
  stehen ein zweites Mal, statt aus `audit_verify` importiert zu werden.** Für
  `HEADER_ORIGIN_IP` und `JSON_OPTION` verlangt der Plan das ausdrücklich; die übrigen folgen
  derselben Regel aus demselben Grund, den `audit_verify` für `TRUE_WORDS` gibt: eine Breite
  oder eine Positivliste, die für die Prüfung geändert wird, darf nicht stillschweigend das
  Lesen ändern. Ein Test hält alle sieben Schreibweisen gegeneinander, damit eine Änderung eine
  Entscheidung ist und keine Drift.
- **Die Ausgabe wird im selben `try` gebaut wie die Abfrage.** Der Plan legt das `try` um die
  Abfrage. Eine Zeile aus einer Datei, die jemand an dieser App vorbei geschrieben hat, kann
  einen Moment tragen, den kein Kalender kennt, oder eine `params`-Spalte, die kein JSON ist;
  beides würfe beim Rendern, also außerhalb des `try`, und eine 500 ist die eine Antwort, die
  dieser Handler nie geben darf (T-18-20). `_moment` ist zusätzlich total, damit eine solche
  Zeile ihre Spalte kostet und nicht die ganze Antwort.
- **`READ_NOTE` nennt den Deckel nicht mit einer Zahl.** Der Plan verlangt einen Satz, der den
  angewandten Deckel nennt und auf `mcp_connector:audit:verify` verweist. Die Zahl steht in der
  Kopfzeile ("3 entries, newest first, at most 200 per read"), und `READ_NOTE` verweist auf sie
  ("stops at the number of entries the first line names"). So bleibt die Notiz eine Konstante,
  die ein Test wörtlich behaupten kann, und die Zahl steht einmal pro Antwort statt zweimal.
- **`--user instance` und der Preis dafür.** Die Instanzkette hat kein Konto (`nc_user` ist dort
  `NULL`, D-03), also wäre sie über eine Kontooption sonst nicht adressierbar. Der Preis steht
  im Docstring: ein Konto, das wirklich `instance` heißt, ist über diese Option nicht erreichbar
  und wird über einen Aufruf ohne `--user` mitgelesen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing robustness] Die Ausgabeform lag ausserhalb des `try` und konnte eine 500 erzeugen**

- **Found during:** Task 1
- **Issue:** Der Plan legt das `try` um `store_provider()` und `read_entries(...)`. `_entry_of_row`
  ruft `json.loads(row[13])`, `_moment` rechnet mit einem Unix-Moment und `_hex` liest ein
  BLOB: eine Zeile aus einer manipulierten Datei lässt jeden der drei Schritte werfen, und zwar
  nach dem `try`. Das Ergebnis wäre genau die 500, die AppAPI mit einem leeren Konsolenfenster
  beantwortet (T-18-20).
- **Fix:** Der Aufbau von Text- beziehungsweise Maschinenform steht im selben `try`, mit einem
  Kommentar, der den Grund nennt. Zusätzlich sind `_moment` und `_hex` total: ein Wert, der
  keiner ist, wird zu `-` beziehungsweise `null`.
- **Files modified:** src/mcp_connector/exapp/audit_read.py
- **Verification:** `grep -v "^\s*#" ... | grep -c "status_code=5"` ergibt 0; die drei Fälle um
  `ExplodingStore` sind grün.
- **Committed in:** `a00dc09`

**2. [Rule 3 - Blocking] `read_entries` wäre nach diesem Plan ein toter Whitelist-Eintrag geblieben**

- **Found during:** Task 1 (Gate `vulture`)
- **Issue:** Plan 19-04 hat `_.read_entries` in `vulture_whitelist.py` eingetragen mit dem Satz,
  dass der Eintrag "die Liste mit Plan 19-06" verlässt. Dieser Plan ist der Aufrufer; ein
  stehen gebliebener Eintrag wäre eine Behauptung, die nicht mehr stimmt, in einer Datei, deren
  erste Regel lautet, dass jeder Eintrag eine Begründung braucht.
- **Fix:** Eintrag entfernt, Kommentar auf die Form der erledigten Einträge (`sweep`,
  `verify_chains`) umgeschrieben.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src scripts vulture_whitelist.py` still.
- **Committed in:** `a00dc09`

### Abweichungen im Wortlaut von Kriterien und Behavior-Block

- **"mindestens dreiundzwanzig Tests" sind 39 geworden.** Der Behavior-Block nennt Fälle, die
  sich nicht sinnvoll in eine Funktion legen lassen (drei Umschlagsformen, vier Zahlenfallen,
  zwei Enden von `truncated` als Parametrisierung), und die Grenzen aus Task 2 und die
  Ausgabefälle aus Task 3 stehen in derselben Datei. Alle 39 sind grün.
- **`--since` mit einem Wort statt einer Zahl liefert nicht "alles".** Der Behavior-Block sagt
  für `--since 99999`, dass alles kommt; wörtlich gilt das nur bis `MAX_SINCE_DAYS` zurück. Der
  Fall zum nicht-numerischen Wert behauptet deshalb genau das Gemessene: der Rückfall ist das
  **weiteste Fenster dieser Option** und nicht "kein Fenster", eine Zeile aus dem Jahr 1970
  bleibt draußen. Der Fall zu `99999` steht daneben und behauptet, dass beide Zeilen einer
  realistischen Ablage kommen.
- **Kein `--until`.** Die Signatur von `read_entries` trägt es, der Plan nennt drei Filter
  (`--user`, `--since`, `--limit`) und keine vierte Option; `until` bleibt ungenutzt.
- **`used_bytes_after` bleibt in `vulture_whitelist.py`.** Der Eintrag aus Phase 18 sagt, sein
  Aufrufer sei "die Lesekommando von AUDIT-04, das berichtet, was ein Ablauf genommen hat".
  Dieses Kommando berichtet keinen Sweep: es liest Zeilen und zählt keine gelöschten. Der
  Eintrag bleibt deshalb stehen, seine Begründung ist ab jetzt aber ungenau. Das ist ein
  Beobachtungsposten für Plan 19-09, kein Befund dieses Plans.

---

**Total deviations:** 2 auto-fixed (Rule 2, Rule 3), 4 Klarstellungen im Wortlaut
**Impact on plan:** Kein erweiterter Auftrag. Beide Fixes halten Zusagen, die der Plan selbst
aufstellt (nie eine 500, `vulture` still).

## Issues Encountered

- Der erste Entwurf des Falls zu einem nicht-numerischen `--since` war rot, und zwar zu Recht:
  er behauptete "alles", während die Rückfallgrenze zehn Jahre ist und die Zeilen der Vorrichtung
  aus dem Jahr 1970 stammen. Der Fall behauptet jetzt das Gemessene und ist damit schärfer als
  der Entwurf.
- Der Arbeitsbaum trägt gemischte Zeilenenden (`core.autocrlf=true`); die zwei neuen Dateien
  sind mit LF geschrieben und werden von git normalisiert. Kein Massen-Diff entstanden.

## Anforderungen

AUDIT-04 bleibt in `REQUIREMENTS.md` **Pending** und wurde nicht abgehakt. Die Anforderung
verlangt, dass ein Administrator liest und exportiert; dieser Plan liefert den Handler, aber
das Kommando ist an keinem `occ` registriert und die Route an keiner Anwendung angehängt. Beides
ist Plan 19-07. Erst danach kann jemand etwas tippen, und erst dann ist der Haken die Wahrheit.

## Threat Flags

Keine neue Fläche: keine Route im Manifest, kein Netzzugang, keine Berechtigung, kein Paket,
keine Versionszeichenkette. Die sechs Fäden des Bedrohungsmodells sind eingelöst:

- **T-19-20** (Information Disclosure) durch die Doppelprüfung, die Abwesenheit im Manifest und
  `test_the_handler_path_is_declared_in_no_route_of_the_manifest`: `len(urls) == 13` und der
  nackte Pfad in keinem Eintrag. Die Gegenprobe ist gelaufen: ohne den `x-origin-ip`-Zweig sind
  zwei Fälle rot.
- **T-19-21** (Information Disclosure) durch die Feldliste der kanonischen Form, Parameternamen
  statt Parameterwerten, `type(exc).__name__` als einzigen Fehlerinhalt und die Behauptungen zu
  `A_VALUE`, `malformed`, `audit.sqlite3`, `tmp_path` und `Traceback`.
- **T-19-22** (Tampering) durch `audit/text.printable` unmittelbar vor der Ausgabe für Kette,
  Kontoname und Clientname, in beiden Formen; der Fall mit dem Zeilenumbruch behauptet die
  Zeilenzahl, der Fall mit U+202E die Abwesenheit des Zeichens. Gegenprobe gelaufen: ohne die
  Klammerung in der Textform sind beide rot.
- **T-19-23** (Denial of Service) durch `READ_LIMIT_DEFAULT` als Vorgabe, die Klemmung gegen
  `READ_LIMIT_MAX` hier und ein zweites Mal im Speicher, `MAX_SINCE_DAYS`, `bounded_body(4096)`
  und `isascii()`/`isdigit()` plus Ziffernlauflänge vor jedem `int()`. Der Deckel ist gegen
  `READ_LIMIT_MAX + 3` Zeilen gemessen und nicht gegen drei.
- **T-19-24** (Repudiation, accept) durch den Zustandsschlüssel `read` und den ausgeschriebenen
  Preis im Modul-Docstring: der Rückgabewert des Kommandos ist immer 0.
- **T-19-25** (Denial of Service) durch `NO_STORE` an jeder Antwort (`_text` und
  `json_response`); drei Fälle behaupten `cache-control: no-store`, auch an den zwei
  Ablehnungen.
- **T-19-SC** (Supply Chain) durch `git diff --stat 4baacbd HEAD -- appinfo/info.xml
  pyproject.toml uv.lock`: leer.

Keine neue Fläche ausserhalb des Registers: der Pfad ist in keinem `<url>` deklariert, und die
Route hängt an keiner Anwendung, bis Plan 19-07 sie anhängt.

## User Setup Required

None - no external service configuration required. Der echte `occ`-Lauf bleibt hergeleitet und
nicht gemessen: auf diesem Rechner läuft keine Test-Nextcloud (Topologie nach 06-07
heruntergefahren). Der Owner-Schritt nach Plan 19-07 lautet: `occ list | grep
mcp_connector:audit`, dann das Kommando einmal ohne Option, einmal mit `--user`, einmal mit
`--json`, plus `occ list --help` zur Prüfung, dass kein Optionsname mit einer globalen Option
kollidiert (Assumption A2 der Recherche).

## Next Phase Readiness

- Plan 19-07 findet oben alle Konstanten, die der Schemaeintrag braucht: den Pfad (für
  `OCC_AUDIT_READ_HANDLER = AUDIT_READ_PATH.removeprefix("/")`), die drei Wert-Optionen für
  `"mode": "optional"` mit `"default": None` und `JSON_OPTION` für `"mode": "none"`.
- Die Verdrahtung in `entry_exapp.py` ist eine Zeile neben `*audit_verify_routes(...)`, mit
  `store_provider=audit_store` und demselben Kommentarblock, und sie hängt unabhängig vom
  Schalter D-14 ein.
- Der sechste absichtlich abwesende Pfad gehört in den grossen Kommentar von `appinfo/info.xml`;
  die Zahl der `<url>`-Einträge bleibt 13, und zwei Tests (dieser und der von 18-08) halten sie.

## Verification

- `uv run pytest tests/unit tests/contract`: 3091 passed.
- `uv run pytest tests/unit/test_exapp_audit_read.py -q`: 39 passed.
- `uv run pytest tests/unit/test_exapp_audit_verify.py -q`: grün, die Vorlage ist unangetastet.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 221 files already
  formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget
  18000`, unverändert. Das Lesekommando ist kein MCP-Werkzeug.
- `git diff --stat 4baacbd HEAD -- appinfo/info.xml pyproject.toml uv.lock`: leer.
- `uv run python -c "from mcp_connector.exapp import audit_read; print(audit_read.AUDIT_READ_PATH)"`:
  `/audit-read`.
- `grep -c "def audit_read_routes"`: 1. `grep -c "status_code=404"`: 1. `grep -c
  "status_code=401"`: 1. Ohne Kommentarzeilen `grep -c "status_code=5"`: 0.
- `grep -c "type(exc).__name__"`: 3, `grep -c "str(exc)"`: 0, `grep -c "isascii() and"`: 2,
  `grep -c "printable("`: 5, `grep -c "isprintable"`: 0, `grep -c "NO_STORE"`: 2.
- `grep -c "== 13" tests/unit/test_exapp_audit_read.py`: 1;
  `grep -c "audit_verify" tests/unit/test_exapp_audit_read.py`: 9.
- Gegenprobe 1 (Guard): ohne den `x-origin-ip`-Zweig sind
  `test_a_read_through_the_php_proxy_is_not_served` und
  `test_neither_rejection_tells_the_caller_which_check_refused` rot; danach
  `git checkout --`, `grep -c "status_code=404"` wieder 1.
- Gegenprobe 2 (Klammerung): mit `entry.chain` statt `printable(entry.chain, limit=CHAIN_LIMIT)`
  sind `test_an_account_with_a_line_break_adds_no_line_to_the_answer` und
  `test_an_account_with_a_right_to_left_override_loses_it` rot; danach `git checkout --`,
  `grep -c "printable("` wieder 5.

## Self-Check: PASSED

Beide neuen Dateien liegen auf der Platte (`src/mcp_connector/exapp/audit_read.py`,
`tests/unit/test_exapp_audit_read.py`), alle drei Commits stehen im Log (`a00dc09`, `583d989`,
`4500565`).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
