---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 07
subsystem: exapp
tags: [audit-log, occ, registrierung, manifest, environment-variables, t-19-26, t-19-27, audit-04]

# Dependency graph
requires:
  - phase: 19
    plan: 06
    provides: "exapp/audit_read.py samt AUDIT_READ_PATH, USER_OPTION, SINCE_OPTION, LIMIT_OPTION, JSON_OPTION, MAX_SINCE_DAYS und INSTANCE_KEYWORD"
  - phase: 19
    plan: 03
    provides: "das Vier-Wörter-Gate, gegen das die drei neuen Variablenbeschreibungen geschrieben sind"
  - phase: 18
    plan: 08
    provides: "command_schemes mit zwei Einträgen, der fünfte abwesende Pfad im Manifest, die Registrierschleife mit einem try je Kommando"
provides:
  - "occ.py: OCC_AUDIT_READ_COMMAND_NAME = mcp_connector:audit:read, OCC_AUDIT_READ_HANDLER = audit-read, vier Optionen (user/since/limit optional mit default, json none)"
  - "entry_exapp.py: audit_read_routes(env, store_provider=audit_store) an der Anwendung, unabhängig vom Schalter D-14"
  - "appinfo/info.xml: /audit-read als sechster absichtlich abwesender Pfad, drei deklarierte Audit-Umgebungsvariablen ohne default"
  - "tests/unit/test_exapp_lifecycle.py: die Modus-Positivliste als Gate über alle Schemata"
affects: [19-08, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Kommandoschema wird gegen eine Positivliste erlaubter Optionsmodi gehalten, weil ein abgelehnter Modus nicht das Kommando, sondern die occ-Kommandozeile der ganzen Instanz kostet"
    - "Kein Kommando dieser App registriert ein Argument: AppAPI liest den default eines Arguments ohne ?? null und schreibt sonst eine PHP-Warnung je occ-Aufruf"
    - "Harte Zählungen in Registrierungstests lesen die Zahl aus command_schemes statt sie zu behaupten"
    - "Eine deklarierte Umgebungsvariable trägt genau name, display-name und description und nie ein leeres default"

key-files:
  created: []
  modified:
    - src/mcp_connector/exapp/occ.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - tests/unit/test_exapp_lifecycle.py
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "OCC_AUDIT_READ_JSON_DESCRIPTION ist eine eigene Konstante und nicht die des Prüfkommandos: dort heisst es dasselbe Ergebnis, hier ist die Maschinenform zugleich die Übergabe, die AUDIT-04 verlangt, und sie trägt die Kettenreihenfolge statt der Konsolenreihenfolge"
  - "READ_LIMIT_DEFAULT, READ_LIMIT_MAX und MAX_SINCE_DAYS werden in die Optionsbeschreibungen hineinformatiert statt als Zahlen abgeschrieben, damit die Beschriftung im occ list nicht von der Grenze abdriften kann"
  - "Die drei harten Zählungen der Registrierungstests wurden schon in Task 1 nachgezogen, weil die Akzeptanz von Task 1 die Datei grün verlangt"
  - "Der Test test_both_commands_failing_... heisst jetzt test_every_command_failing_... und liest die Zahl aus command_schemes: eine Zahl im Testnamen ist eine Wartungslast, die dieser Plan gerade bezahlt hat"
  - "Der Kommentar über dem environment-variables-Block wurde um die drei Audit-Variablen erweitert, weil er die deklarierten Variablen aufzählt und sonst unvollständig wäre"

patterns-established:
  - "Ein Modus ausserhalb der Positivliste ist kein Stilfehler, sondern ein Ausfall der Instanz, und die Regel steht als Test im Repo statt als Satz in einem Rechercheartefakt"

requirements-completed: [AUDIT-04]
requirements-advanced: []

# Metrics
duration: 25min
completed: 2026-08-31
---

# Phase 19 Plan 07: Das Kommando bekannt machen und die Route anhängen Summary

**Das dritte occ-Kommando `mcp_connector:audit:read` ist registriert, seine Route hängt an der Anwendung und an keinem `<url>`-Eintrag, kein Optionsmodus verlässt die Positivliste `required`, `optional`, `none`, und die drei Audit-Umgebungsvariablen sind erstmals deklariert, jede mit Anzeigename und Beschreibung und keine mit `default`.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-31T15:33:00Z
- **Completed:** 2026-08-31T15:58:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Drei registrierte Kommandos statt zwei:

  | Kommando | Handler | Optionen |
  |----------|---------|----------|
  | `mcp_connector:purge` | `purge` | `force` (none) |
  | `mcp_connector:audit:verify` | `audit-verify` | `json` (none) |
  | `mcp_connector:audit:read` | `audit-read` | `user` (optional), `since` (optional), `limit` (optional), `json` (none) |

  Die drei Wert-Optionen tragen je einen `default`-Schlüssel mit `None`, die Flagge trägt keinen.
  Kein Schema führt ein Argument (`[[], [], []]`), jedes trägt `hidden` mit 0 und mindestens
  einen `usages`-Eintrag.
- `OCC_AUDIT_READ_HANDLER = AUDIT_READ_PATH.removeprefix("/")`: der Handlername ist abgeleitet
  und nirgends zweitgeschrieben (`grep -c "AUDIT_READ_PATH.removeprefix"` ergibt 1). Der
  Kommandoname steht genau einmal als Literal im Modul (`grep -c "mcp_connector:audit:read"`
  ergibt 1), auch im Modul-Docstring nicht ein zweites Mal: AppAPIs `insertOrUpdate` keyed auf
  App-Id und Name, ein umbenanntes Kommando bliebe als 404-Eintrag in `occ list` stehen.
- Das Gate, das diese Phase am teuersten gemacht hätte, steht jetzt als Test im Repo:
  `test_no_command_scheme_leaves_the_positive_list_of_option_modes` läuft über alle Schemata
  und alle Optionen, hält die drei erlaubten Modi, die Abwesenheit von Argumenten, den
  `default`-Schlüssel jeder Wert-Option, `hidden == 0`, eine Beschreibung je Option und einen
  nicht leeren `execute_handler`. Die Fehlermeldung nennt Kommandoname und Optionsname.
  `grep -c '"array"' src/mcp_connector/exapp/occ.py` ergibt 0.
- Die Route hängt: `*audit_read_routes(env, store_provider=audit_store)` unter
  `audit_verify_routes`, mit dem AUDIT-Speicher und nicht dem OAuth-Speicher, und der
  Begründungskommentar sagt zum sechsten Mal dieselbe Regel plus den Grund, warum sie
  unabhängig vom Schalter D-14 hängt.
- Der sechste absichtlich abwesende Pfad steht im Manifestkommentar, in der Bauart der fünf
  darüber. Die Zahl der `<url>`-Einträge ist unverändert 13, keiner enthält `audit`, und die
  einleitende Zeile über genau dreizehn Routen ist nicht angefasst.
- Neun deklarierte Umgebungsvariablen: `NC_MCP_PUBLIC_URL`, `NC_MCP_OAUTH_DCR`,
  `NC_MCP_OAUTH_CIMD`, `NC_MCP_OAUTH_ALLOWLIST_ONLY`, `NC_MCP_OAUTH_ALLOWED_CLIENTS`,
  `NC_MCP_TALK_SEND`, `NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS`,
  `NC_MCP_AUDIT_MAX_BYTES`. Keine trägt ein `default`-Element. Damit ist der Punkt aus
  `.planning/phases/18-audit-log-kern/deferred-items.md` geschlossen.

## Task Commits

1. **Task 1: Dritter Eintrag in command_schemes samt Modus-Positivliste** - `3cc53e4` (feat)
2. **Task 2: Route anhängen, sechster abwesender Pfad, Zähltests** - `e11d0aa` (feat)
3. **Task 3: Die drei Audit-Umgebungsvariablen deklarieren** - `07131cf` (feat)

## Files Created/Modified

- `src/mcp_connector/exapp/occ.py` - fünf neue Konstanten, sechs neue Namen in `__all__`,
  dritter Eintrag in `command_schemes()`, Modul-Docstring auf drei Kommandos und auf die
  Modus-Regel erweitert; die Registrierschleife ist unverändert
- `src/mcp_connector/entry_exapp.py` - Import und eine Zeile in der Routenaufzählung, plus ein
  Absatz im Begründungskommentar
- `appinfo/info.xml` - sechster abwesender Pfad im Kommentar, drei `variable`-Blöcke, ein
  Absatz im Kommentar über dem Block; 34 Einfügungen, 0 Löschungen
- `tests/unit/test_exapp_lifecycle.py` - zwei neue Tests, drei nachgezogene Zählungen, ein
  umbenannter Test
- `tests/unit/test_exapp_env_setup.py` - Mengengleichheit von sechs auf neun Namen, zwei
  Docstrings nachgezogen

## Decisions Made

- **Eine eigene JSON-Beschreibung für das Lesekommando.** Der Plan stellt es frei, die
  bestehende `OCC_AUDIT_JSON_DESCRIPTION` wiederzuverwenden. Sie sagt "the same result as
  JSON", was für die Prüfung stimmt: dort ist die Maschinenform dieselbe Aussage in anderer
  Form. Beim Lesen ist sie mehr, nämlich die Übergabe, die AUDIT-04 verlangt, und sie trägt
  die Einträge in Kettenreihenfolge statt in der Reihenfolge, die die Konsole zeigt. Ein Satz
  für beide wäre in einem der beiden Kommandos falsch, also hat jedes seinen.
- **Die Zahlen der Optionsbeschreibungen kommen aus den Konstanten.** `READ_LIMIT_DEFAULT`,
  `READ_LIMIT_MAX` und `MAX_SINCE_DAYS` werden importiert und in die Beschreibungen
  hineinformatiert. Eine abgeschriebene 200 in einem Text, den `occ list` zeigt, wäre die
  nächste Stelle, an der eine Grenze und ihre Beschreibung auseinanderlaufen.
- **`INSTANCE_KEYWORD` steht ebenfalls in der Beschreibung von `--user`**, aus demselben
  Grund: das eine Wort, das kein Konto ist, ist ohne Beschriftung nicht auffindbar.
- **Der Test mit der Zahl im Namen wurde umbenannt.**
  `test_both_commands_failing_is_two_log_lines_and_no_exception` behauptete zweimal die Zahl
  zwei, einmal davon im Namen. Er heisst jetzt
  `test_every_command_failing_is_one_log_line_each_and_no_exception` und liest die Zahl aus
  `len(occ.command_schemes())`. Die Regel ist "eine Zeile je Kommando", nicht "zwei Zeilen".
  Der Grund steht als Docstring im Test.
- **Der Kommentar über den Umgebungsvariablen wurde erweitert.** Er zählt auf, welche Schalter
  dort deklariert sind ("die drei Schalter von AUTH-07, der eine von AUTH-08 und der eine von
  TALK-04"). Drei Variablen dazuzulegen und die Aufzählung stehen zu lassen, hätte einen
  Kommentar hinterlassen, der weniger sagt als die Datei enthält.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Zähltests mussten in Task 1 statt in Task 2 nachgezogen werden**

- **Found during:** Task 1
- **Issue:** Der Plan legt die harten Zahlen (`route.call_count == 2`, die zwei
  `side_effect`-Antworten) in Task 2. Die Akzeptanz von Task 1 verlangt aber
  `uv run pytest tests/unit/test_exapp_lifecycle.py -q` grün, und das dritte Schema macht
  genau diese drei Fälle rot (die Pattern Map hatte `:443` und `:464` vorhergesagt). Beides
  zugleich ist nicht erfüllbar.
- **Fix:** Die drei Zählungen sind im Commit von Task 1 nachgezogen. Task 2 hat an diesen
  Tests nichts mehr zu tun; sein Akzeptanzkriterium `grep -c "call_count == 2"` ergibt 0.
- **Files modified:** tests/unit/test_exapp_lifecycle.py
- **Committed in:** `3cc53e4`

**2. [Rule 2 - Wahrheit eines Kommentars] Der Kommentar über dem environment-variables-Block zählt die Variablen auf**

- **Found during:** Task 3
- **Issue:** Der Plan verlangt drei `variable`-Blöcke und nennt den Kommentar darüber nur als
  Fundstelle der Warnung zum leeren `default`. Dieser Kommentar zählt aber auf, welche
  Schalter deklariert sind. Drei neue Blöcke ohne einen Satz dazu hätten ihn falsch gemacht.
- **Fix:** Ein Absatz in derselben Form, der die drei Variablen nennt, den Hauptweg (BL-06,
  Admin-Formular) benennt und sagt, warum die Deklaration trotzdem nötig ist.
- **Files modified:** appinfo/info.xml
- **Committed in:** `07131cf`

### Klarstellungen im Wortlaut

- **Zwei neue Tests statt einem.** Der Plan verlangt den Positivlisten-Test. Daneben steht
  `test_the_read_command_is_the_one_plan_19_06_reserved_its_constants_for`, der den Namen, die
  Ableitung des Handlers aus `AUDIT_READ_PATH` und die vier Optionsmodi gegen das Handlermodul
  hält (T-19-28). Ohne ihn behauptet nichts, dass die Registrierung und der Handler dieselbe
  Option meinen.
- **`tests/unit/test_exapp_purge.py` brauchte keine Änderung.** Der Plan nennt die Datei unter
  den zu ändernden. Ihre Registrierungszählung liest bereits `len(occ.command_schemes())`, und
  ihre Schema-Behauptungen zeigen auf `command_schemes()[0]`. Sie ist mit dem dritten Kommando
  grün geblieben, also wurde nichts angefasst.
- **`OCC_AUDIT_READ_DESCRIPTION` steht nicht in `__all__`.** Die beiden bestehenden
  Kommandobeschreibungen (`OCC_DESCRIPTION`, `OCC_AUDIT_DESCRIPTION`) stehen dort auch nicht;
  in `__all__` stehen die Namen, die Handler und die Optionsbeschreibungen. Die neue
  Kommandobeschreibung folgt der bestehenden Trennung, die fünf anderen neuen Namen stehen
  alphabetisch in `__all__`.
- **Ein Satz im Kommentar bei `OCC_AUDIT_COMMAND_NAME` ist in die Vergangenheit gesetzt.** Er
  sagte "AUDIT-04 adds a second command in phase 19"; mit diesem Plan ist das geschehen.

---

**Total deviations:** 2 auto-fixed (Rule 3, Rule 2), 4 Klarstellungen
**Impact on plan:** Kein erweiterter Auftrag, keine Änderung an einer Zusage des Plans.

## Issues Encountered

- Keine. Die drei roten Fälle nach dem dritten Schema waren genau die drei, die die Pattern
  Map angekündigt hatte.
- `appinfo/info.xml` trägt CRLF und Tabulatoren; beide Einfügungen sind mit einem
  Python-Skript im `rb`/`wb`-Modus gemacht worden, damit kein Massen-Diff entsteht. Ergebnis:
  34 Einfügungen, 0 Löschungen.

## Anforderungen

**AUDIT-04 ist erfüllt und in `REQUIREMENTS.md` abgehakt** (Checkbox und Zeile der
Nachweistabelle). Ein Administrator kann `occ mcp_connector:audit:read` tippen, das Kommando
ist registriert, die Route hängt, und es ist keine neue Route im Manifest deklariert: die Zahl
der `<url>`-Einträge ist unverändert 13. Der echte Lauf gegen eine laufende Nextcloud bleibt
ein Release-Gate und ist unten als Owner-Schritt ausgeschrieben.

## Threat Flags

Keine neue Fläche ausserhalb des Registers dieses Plans. Die sechs Fäden sind eingelöst:

- **T-19-26** (Denial of Service, kritisch): drei Modi und kein vierter, kein Argument, ein
  `default` je Wert-Option, und ein Test hält alle Schemata gegen die Positivliste. Gegenprobe
  gelaufen: mit `"mode": "array"` an `--user` ist
  `test_no_command_scheme_leaves_the_positive_list_of_option_modes` rot und nennt Kommando und
  Option; danach zurückgesetzt.
- **T-19-27** (Information Disclosure, kritisch): kein neuer `url`-Eintrag, die Zahl bleibt 13,
  per `lxml` gemessen, und keiner der dreizehn enthält `audit`. Der Pfad ist als sechster
  absichtlich abwesender Pfad im Kommentar begründet.
- **T-19-28** (Spoofing): der Kommandoname steht genau einmal als Literal im Baum, der Handler
  ist abgeleitet, und ein Test hält beides gegen das Handlermodul.
- **T-19-29** (Information Disclosure, gering): kein Geheimnis unter den drei Variablennamen,
  kein `default`-Element, keine der drei Beschreibungen trägt einen Backtick, eine Tabelle,
  HTML, ein Bild, eine horizontale Linie, einen der vier verbotenen Ansprüche oder das
  verbotene Wort. Das Anspruchs-Gate und das Vokabular-Gate laufen über den Manifesttext und
  sind grün.
- **T-19-30** (Tampering): `git diff 4baacbd HEAD -- appinfo/info.xml` enthält keine Zeile mit
  `<version>` und keine mit `image-tag` (je 0 Treffer), 34 Einfügungen und 0 Löschungen;
  `git tag --points-at HEAD` ist leer, kein Store-Upload, kein Lauf von
  `scripts/build_store_release.sh`.
- **T-19-SC** (Supply Chain): `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock` ist
  leer.

Keine neue Netzfläche: das Kommando erreicht den Handler über AppAPI PublicFunctions, wie die
fünf Pfade davor.

## User Setup Required

Der Lauf gegen eine laufende Nextcloud ist **hergeleitet und nicht gemessen**: auf diesem
Rechner läuft keine Test-Instanz (Topologie nach 06-07 heruntergefahren). Hergeleitet ist
insbesondere, dass eine bestehende Installation das dritte Kommando erst nach einem
Deaktivieren-Aktivieren-Zyklus sieht: die Registrierung läuft im `enabled=1`-Zweig, und
`getOccCommands()` liest einen verteilten Cache, den nur eine erfolgreiche Registrierung leert.

Owner-Schritte, in dieser Reihenfolge:

1. `occ app_api:app:disable mcp_connector`
2. `occ app_api:app:enable mcp_connector`
3. `occ list | grep mcp_connector` , es müssen drei Zeilen erscheinen, darunter
   `mcp_connector:audit:read`
4. `occ list --help` , prüfen, dass keiner der vier Optionsnamen (`user`, `since`, `limit`,
   `json`) mit einer globalen Option von Symfony kollidiert (Assumption A2 der Recherche)
5. `occ mcp_connector:audit:read` , die Textform, neueste zuerst, mit dem angewandten Deckel
   in der Kopfzeile
6. `occ mcp_connector:audit:read --user alice --limit 5` und
   `occ mcp_connector:audit:read --since 7 --json` , die beiden Formen mit Optionen
7. `occ mcp_connector:audit:verify` , der Gegencheck, dass das zweite Kommando durch die
   dritte Registrierung nicht gelitten hat

Wenn Schritt 3 nur zwei Zeilen zeigt, ist die Registrierung fehlgeschlagen: der Grund steht
dann als eine Zeile im Log der App, mit dem Namen des Kommandos, und keine der beiden anderen
Registrierungen ist davon betroffen.

## Next Phase Readiness

- Plan 19-08 fasst `appinfo/info.xml` erneut an (Enterprise-Absatz in drei Sprachen). Der
  Stand nach diesem Plan: 34 eingefügte Zeilen, keine gelöschte, Version und `image-tag`
  unberührt, neun `variable`-Blöcke, dreizehn `url`-Einträge.
- Plan 19-09 schreibt den `[Unreleased]`-Block: das dritte occ-Kommando und die drei neu
  deklarierten Umgebungsvariablen sind zwei Punkte darin, und der
  Deaktivieren-Aktivieren-Zyklus gehört in denselben Text, weil Kommando und Beschriftung erst
  danach in der Instanz ankommen.
- Beobachtungsposten aus 19-06 bleibt offen: `used_bytes_after` steht in
  `vulture_whitelist.py` mit einer Begründung, die auf dieses Lesekommando zeigt, und dieses
  Kommando berichtet keinen Sweep.

## Verification

- `uv run pytest tests/unit tests/contract`: 3093 passed, exit 0.
- `uv run pytest tests/unit/test_exapp_lifecycle.py -q`: grün, 44 Fälle.
- `uv run pytest tests/unit/test_exapp_env_setup.py -q`: grün;
  `-k "vocabulary or forbidden_claim or description"`: 8 Fälle grün.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 221 files already
  formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget
  18000`, unverändert. Ein occ-Kommando ist kein MCP-Werkzeug.
- `command_schemes()`: `3 ['mcp_connector:purge', 'mcp_connector:audit:verify',
  'mcp_connector:audit:read']`; Modi `['none', 'optional']`; `arguments` `[[], [], []]`;
  `execute_handler` des dritten `audit-read`.
- `grep -c "AUDIT_READ_PATH.removeprefix" src/mcp_connector/exapp/occ.py`: 1.
  `grep -c "mcp_connector:audit:read"`: 1. `grep -c '"array"'`: 0.
- `grep -c "audit_read_routes" src/mcp_connector/entry_exapp.py`: 2.
  `grep -c "call_count == 2" tests/unit/test_exapp_lifecycle.py`: 0.
  `grep -c "audit-read" appinfo/info.xml`: 1, im Kommentarblock der abwesenden Pfade.
- Manifest über `lxml`: 13 `url`-Einträge, keiner mit `audit`; 9 `variable`-Einträge, keiner
  mit `default`; die drei Audit-Namen sind darunter.
- `git diff 4baacbd HEAD -- appinfo/info.xml`: 34 Einfügungen, 0 Löschungen, 0 Zeilen mit
  `<version>`, 0 mit `image-tag`, 0 mit `<url>`.
- `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock`: leer. `git tag --points-at HEAD`:
  leer.

## Self-Check: PASSED

Alle fünf geänderten Dateien liegen auf der Platte, die drei Task-Commits stehen im Log
(`3cc53e4`, `e11d0aa`, `07131cf`).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
