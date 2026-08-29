---
phase: 18-audit-log-kern
plan: 08
subsystem: exapp
tags: [occ-command, audit-log, chain-check, appapi, no-manifest-route, AUDIT-02]

# Dependency graph
requires:
  - phase: 18
    plan: 04
    provides: "verify_chains, ChainFinding, FINDING_MODIFIED, FINDING_MISSING"
  - phase: 18
    plan: 07
    provides: "der Schalter aus D-14 und der Audit-Opener in build_exapp_app"
provides:
  - "exapp/audit_verify.py: AUDIT_VERIFY_PATH, audit_verify_routes, die Doppelprüfung, die Textausgabe und die maschinenlesbare Fassung, immer mit Status 200"
  - "audit/store.py: StoreOverview und AuditStore.overview, die vier Zählungen um die Befunde herum"
  - "occ.py: command_schemes() als Liste, OCC_AUDIT_COMMAND_NAME, OCC_AUDIT_HANDLER und eine Registrierungsschleife mit einem try je Kommando"
  - "appinfo/info.xml: der fünfte bewusst abwesende Pfad im Kommentar, ohne neue url"
affects: [18-09, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Immer Status 200, das Urteil im Rumpf, weil AppAPI den Rumpf bei jedem anderen Status verwirft"
    - "Ein try je occ-Kommando, weil registerCommand genau ein Kommando je POST nimmt"
    - "Zählungen neben der Prüfung statt in ihr: eine Prüfung darf nicht löschen, um zu erfahren, wie viel da ist"
    - "Kettenkennungen wie Client-Namen geklammert, und die Grenze dieser Klammerung steht im Docstring"

key-files:
  created:
    - src/mcp_connector/exapp/audit_verify.py
    - tests/unit/test_exapp_audit_verify.py
  modified:
    - src/mcp_connector/audit/store.py
    - src/mcp_connector/exapp/occ.py
    - src/mcp_connector/exapp/lifecycle.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - tests/unit/test_exapp_lifecycle.py
    - tests/unit/test_exapp_purge.py
    - vulture_whitelist.py

key-decisions:
  - "Der Handler antwortet auch bei gebrochener Kette mit 200, weil ExAppOccService::buildCommand den Rumpf bei jedem anderen Status verwirft; der Preis, dass der Rückgabewert immer 0 ist, steht als Abwägung im Docstring und ist der zweite Grund für --json"
  - "Die Zählungen kommen aus AuditStore.overview und nicht aus einem SweepReport: eine Prüfung, die löschen müsste, um zu erfahren, wie viel da ist, wäre keine Prüfung"
  - "Die Klammerung einer Kettenkennung hält die Zeile, nicht die Zeichenkette: ein Name kann keine eigene Zeile erfinden, innerhalb seiner Zeile aber jeden Text tragen, und genau deshalb liest ein Skript den Schlüssel broken der JSON-Fassung"
  - "TRUE_WORDS steht ein zweites Mal in audit_verify.py statt aus purge.py importiert zu werden, damit eine Änderung für das zerstörende Kommando nicht stillschweigend die Aufrufform des lesenden ändert; ein Test hält beide Listen gleich"
  - "Der Namensraum ist zweistufig (mcp_connector:audit:verify), weil AUDIT-04 in Phase 19 ein zweites Kommando unter demselben Präfix nachlegt"

patterns-established:
  - "Ein Kommando, das nichts ändert, hat keine Pflicht-Option: die einzige Option entscheidet über die Form der Antwort, nicht über eine Erlaubnis"
  - "Der fünfte Absatz im Manifest-Kommentar nennt den Pfad, ohne das Wort url zu schreiben, damit die Zählung der Routen dieselbe bleibt"

requirements-completed: [AUDIT-02]

# Metrics
duration: 55min
completed: 2026-08-29
---

# Phase 18 Plan 08: Das Prüfkommando aus AUDIT-02 Summary

**Ein Administrator tippt `occ mcp_connector:audit:verify` und liest entweder "chains verified, no break found" oder die erste gebrochene Stelle mit Kette und Nummer, und die äussere Angriffsfläche der App ist dabei um kein Byte gewachsen.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-08-29T10:30:00Z
- **Completed:** 2026-08-29T11:25:00Z
- **Tasks:** 3
- **Files modified:** 10 (2 neu, 8 geändert)

## Accomplishments

- Das Kommando steht und es ist lesend: keine Pflicht-Option, keine Änderung an der Datei, und seine einzige Option (`--json`) entscheidet über die Form der Antwort statt über eine Erlaubnis.
- Der Handler antwortet **immer** mit 200, sobald die Doppelprüfung bestanden ist. Der Grund ist gemessen und steht mit seiner Quelle im Modul-Docstring: `ExAppOccService::buildCommand` (app_api v34.0.3) verwirft den Rumpf bei jedem Status ungleich 200 und gibt stattdessen `command executeHandler failed` aus, also verlöre ein Fehlerstatus genau den Satz, der die Stelle benennt. Ein eigener Testfall behauptet die 200 über alle vier Ausgänge, die gebrochenen eingeschlossen.
- Die Ausgabe unterscheidet drei Befundarten und nennt in jeder Kette und Nummer: `entry 3 in chain u:alice was changed after it was written`, `an entry is missing between 2 and 4 in chain u:alice`, und für den Kopf einer Kette `the beginning of chain u:alice is missing and no tombstone explains it, the oldest entry left is 2`. Jeder der drei Fälle wird mit einer eigenen `sqlite3`-Verbindung an der Ablage vorbei erzeugt, denn erst der Weg des Angreifers belegt, dass die Prüfung ihn findet.
- Die Grabsteinzeile macht eine erklärte Lücke von einer unerklärten unterscheidbar: `1 tombstone in the instance chain, explaining 4 entries that were removed`. Ohne sie läse die Antwort einer Ablage, die die Hälfte ihrer Zeilen an die Frist verloren hat, wie die einer, die nie eine verloren hat.
- Die Doppelprüfung greift und schweigt: `x-origin-ip` ergibt 404, fehlende AppAPI-Kopfzeilen ergeben 401, und ein eigener Fall behauptet, dass in keiner der beiden Antworten das Wort für die Kopfzeile, "appapi" oder "header" steht.
- Zwei occ-Kommandos, zwei Registrierungen, ein `try` je Kommando: `OccCommandController::registerCommand` nimmt genau eines je `POST`, und drei Fälle in `test_exapp_lifecycle.py` belegen, dass ein abgelehntes erstes das zweite nicht kostet, dass ein Transportfehler dasselbe tut, und dass zwei Fehlschläge zwei Logzeilen sind und keine Ausnahme.
- Der Pfad steht in keiner `<url>` des Manifests: `grep -c "<url>" appinfo/info.xml` liefert **14 vorher und 14 nachher** (13 echte `<url>`-Elemente plus eine Erwähnung im Kommentar), und der neue Absatz im Kommentar nennt `/audit-verify`, ohne das Wort selbst noch einmal zu schreiben. Der Manifest-Fall des neuen Tests prüft das mit `lxml.etree` und dem gehärteten Parser gegen alle dreizehn Routen.
- Die Werkzeugfläche hat sich um kein Byte bewegt: `tools/list: 15712 bytes, 21 tools, budget 18000`, vor und nach der Änderung dieselbe Zeile.

## Task Commits

1. **Task 1: Der Handler des Prüfkommandos** - `3274138` (feat)
2. **Task 2: Zweites occ-Kommando, Route und der fünfte abwesende Pfad** - `277308c` (feat)
3. **Task 3: Tests des Kommandos, samt der gebrochenen Kette** - `87903b9` (test), Nachtrag zur Klammerungsgrenze `a7acdf0` (docs)

## Files Created/Modified

- `src/mcp_connector/exapp/audit_verify.py` (neu) - `AUDIT_VERIFY_PATH`, `JSON_OPTION`, `TRUE_WORDS`, `NO_BREAK`, `LIMIT_SENTENCE`, die Fabrik `audit_verify_routes`, die Doppelprüfung, `_report`, `_sentence`, `_machine_readable`, `_printable`, die Leseform des occ-Umschlags und `_text` mit 200 als Vorgabe
- `src/mcp_connector/audit/store.py` - `StoreOverview` und `AuditStore.overview` samt der zwei Zählanweisungen (siehe Abweichung 1)
- `src/mcp_connector/exapp/occ.py` - `command_schemes()` als Liste, `OCC_AUDIT_COMMAND_NAME`, `OCC_AUDIT_HANDLER`, `OCC_AUDIT_DESCRIPTION`, `OCC_AUDIT_JSON_DESCRIPTION`, die Registrierungsschleife mit einem `try` je Kommando und einer Logzeile, die das Kommando benennt
- `src/mcp_connector/exapp/lifecycle.py` - die Logzeile des letzten Auffangnetzes meint jetzt beide Kommandos, mit dem Vermerk, dass ein einzelner Fehlschlag sie gar nicht erreicht
- `src/mcp_connector/entry_exapp.py` - der fünfte Absatz über der Routenaufzählung und `audit_verify_routes(env, store_provider=audit_store)` an derselben Stelle wie `purge_routes`
- `appinfo/info.xml` - zwölf Zeilen Kommentar über den fünften bewusst abwesenden Pfad, binär geschrieben, damit die CRLF-Zeilenenden bleiben (`git diff --stat`: 12 insertions, kein Massen-Diff)
- `tests/unit/test_exapp_audit_verify.py` (neu) - 32 Fälle über 23 Funktionen
- `tests/unit/test_exapp_lifecycle.py` - drei Fälle über die Unabhängigkeit der beiden Registrierungen
- `tests/unit/test_exapp_purge.py` - die dritte Schreibweise des Proxy-Merkmals, und drei Stellen von `command_scheme()` auf `command_schemes()` gezogen (siehe Abweichung 2)
- `vulture_whitelist.py` - `verify_chains` und `next_seq` verlassen die Liste mit dem Plan, den ihr Eintrag genannt hat; `used_bytes_after` bleibt mit einer korrigierten Begründung

## Decisions Made

- **Immer 200, und der Preis steht daneben.** Die Messung ist die Begründung, nicht der Geschmack: bei jedem anderen Status druckt AppAPI `command executeHandler failed` und liest den Rumpf gar nicht. Der Preis, dass der Rückgabewert des Kommandos damit immer 0 ist, ist nicht versteckt, sondern der zweite Grund für `--json`: ein Überwachungsskript liest den Schlüssel `broken`, nicht den Rückgabewert und nicht eine Teilzeichenkette des Textes.
- **Die Zählungen kommen aus einem eigenen Lesevorgang.** `verify_chains` liefert Befunde und keine Summen, und der `SweepReport` hätte sie nur um den Preis eines Löschlaufs. Eine Prüfung, die aufräumen muss, um zu erfahren, wie viel da ist, wäre keine Prüfung; also `AuditStore.overview`, vier Aggregate, die keine Zeile eines Aufrufers anfassen.
- **Die Klammerung hält die Zeile, nicht die Zeichenkette.** Ein Nutzername kann keinen Zeilenumbruch mehr in die Antwort bringen, also keine eigene Zeile erfinden; innerhalb seiner Zeile kann er jeden Text tragen, den Satz "no break found" eingeschlossen. Das ist die ehrliche Grenze, sie steht im Docstring von `_printable`, und der Testfall behauptet genau sie: vier Zeilen, keine davon gleich dem Urteil, und `broken` in der JSON-Fassung unberührt.
- **`TRUE_WORDS` steht ein zweites Mal.** Die Liste gehört im `purge` zu der einen Handlung dieser App, die nicht rückgängig zu machen ist. Eine Änderung, die dort aus Sicherheitsgründen fällt, darf nicht stillschweigend ändern, wie ein lesendes Kommando seine Ausgabeform wählt. Ein Test hält beide Listen gleich, so dass ein Auseinanderdriften eine Entscheidung ist und kein Versehen.
- **Der Namensraum hat zwei Stufen.** `mcp_connector:audit:verify` statt `mcp_connector:audit-verify`, weil AUDIT-04 in Phase 19 ein zweites Kommando unter demselben Präfix nachlegt und der Name dann nicht zum zweiten Mal erfunden werden muss.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Kopfzeile und die Grabsteinzeile hatten keine Datenquelle**
- **Found during:** Task 1
- **Issue:** Der Auftrag verlangt eine Kopfzeile mit der Anzahl der geprüften Ketten und Einträge und eine Zeile mit der Anzahl der Grabsteine und der von ihnen erklärten Zeilen. `verify_chains` liefert Befunde, `SweepReport` entsteht nur bei einem Löschlauf, und `AuditStore` hatte für diese vier Zahlen keine lesende Methode. Ohne sie wäre entweder die Zeile ausgefallen (Akzeptanzkriterium verfehlt) oder das Prüfkommando hätte eine eigene `sqlite3`-Verbindung neben dem Store geöffnet, mit eigenen Pragmas und eigener Fehlerbehandlung.
- **Fix:** `StoreOverview` (vier Zahlen, kein Name einer Kette und keines Kontos) und `AuditStore.overview` in `audit/store.py`, mit zwei Aggregatanweisungen neben den bestehenden Leseanweisungen des Moduls. `src/mcp_connector/audit/store.py` steht nicht in der `files_modified`-Liste des Plans; die Alternative wäre eine zweite Verbindung zur selben Datei aus einem Modul gewesen, das keine kennt.
- **Files modified:** src/mcp_connector/audit/store.py
- **Verification:** `uv run --no-sync pytest tests/unit tests/contract -q` grün, `vulture` ohne Befund (die Methode hat mit `audit_verify.py` sofort einen Produktionsaufrufer), `pyright` 0 errors.
- **Committed in:** `3274138` (Task-1-Commit)

**2. [Rule 3 - Blocking] Drei Stellen in `test_exapp_purge.py` riefen `command_scheme()`**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt die Umbenennung von `command_scheme()` zu `command_schemes()`. Drei Fälle in `tests/unit/test_exapp_purge.py` (Ableitung des Handlers, das Schema des Runbooks, der eine POST im App-Kontext) riefen die alte Form und wären mit einem `AttributeError` rot geworden. Die Datei steht nicht in der `files_modified`-Liste des Plans.
- **Fix:** Die ersten beiden greifen jetzt `command_schemes()[0]`, der dritte behauptet die neue Wahrheit statt der alten: ein POST **je** Kommando, in der Reihenfolge der Liste, und die Rümpfe gleich den Schemata. Damit ist derselbe Fall die Gegenprobe zur Registrierungsschleife.
- **Files modified:** tests/unit/test_exapp_purge.py
- **Verification:** `uv run --no-sync pytest tests/unit/test_exapp_purge.py -q` grün.
- **Committed in:** `277308c` (Task-2-Commit) für die Änderung, `87903b9` für die dritte Schreibweise des Proxy-Merkmals

**3. [Rule 2 - Missing coverage] Die Grenze der Klammerung war behauptet, aber nicht wahr**
- **Found during:** Task 3
- **Issue:** Der erste Testfall zu T-18-08 behauptete, ein Kettenname könne das Urteil nicht fälschen, und fiel: ein Konto namens `mallory\nchains verified, no break found` bringt die Zeichenkette des Urteils in die Befundzeile, weil der Umbruch zu einem Leerzeichen wird. Die Zeile lässt sich nicht fälschen, die Teilzeichenkette schon.
- **Fix:** Nicht der Test wurde aufgeweicht, sondern die Zusage präzisiert und die Lücke geschlossen, wo sie zu schliessen ist: der Docstring von `_printable` sagt jetzt, was die Klammerung kauft (keine zusätzliche Zeile) und was nicht (beliebiger Text innerhalb der Zeile), und nennt das als zweiten Grund für `--json`. Der Testfall behauptet vier Zeilen, keine davon gleich dem Urteil, und zusätzlich `broken is True` in der maschinenlesbaren Fassung, also in genau dem Schlüssel, den ein Skript liest.
- **Files modified:** src/mcp_connector/exapp/audit_verify.py, tests/unit/test_exapp_audit_verify.py
- **Verification:** `uv run --no-sync pytest tests/unit/test_exapp_audit_verify.py -q` grün, 32 Fälle.
- **Committed in:** `87903b9` und `a7acdf0`

**4. [Rule 2 - Missing coverage] `vulture_whitelist.py` hätte zwei falsche Einträge behalten**
- **Found during:** Task 3
- **Issue:** Der Eintrag aus Plan 18-04 sagt ausdrücklich, `verify_chains` und `next_seq` verlassen die Liste mit Plan 18-08. Beide haben mit diesem Plan einen Produktionsaufrufer. Ein stehen gebliebener Eintrag wäre eine Ausnahme ohne Grund und würde einen späteren echten Fund verdecken.
- **Fix:** Beide entfernt, der Kommentar sagt, mit welchem Plan sie gegangen sind. `used_bytes_after` bleibt, und seine Begründung ist korrigiert: der Eintrag aus 18-04 hatte dieses Kommando als seinen Leser genannt, es liest aber `overview` und keinen `SweepReport`. Sein Ausstiegsplan ist jetzt AUDIT-04 in Phase 19.
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run --no-sync vulture src scripts vulture_whitelist.py` ohne Befund.
- **Committed in:** `87903b9`

---

**Total deviations:** 4 auto-fixed (2 Rule 3, 2 Rule 2)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 und 2 halten den Auftrag überhaupt ausführbar, Abweichung 3 macht eine Zusage wahr, statt sie zu behaupten, und Abweichung 4 löst einen Ausstiegsplan ein, den dieser Plan ausdrücklich geerbt hat.

## Issues Encountered

- Der Kommentar im Manifest darf das Wort `<url>` nicht ein zweites Mal schreiben: das Akzeptanzkriterium hält `grep -c "<url>" appinfo/info.xml` fest, und diese Zählung sieht die Erwähnung im Kommentar mit. Der neue Absatz sagt deshalb "declared in no route below" statt der Elementform. Die Zahl bleibt bei 14, die dreizehn echten Routen unverändert.
- `appinfo/info.xml` trägt CRLF. Der Absatz wurde mit einem Wegwerf-Skript binär eingefügt und das Skript danach gelöscht; `git diff --stat` zeigt zwölf eingefügte Zeilen und keine geänderte.

## Anforderungen

**AUDIT-02 ist erfüllt.** Der Vorbehalt von Plan 18-04 war, dass die Prüfung zwar steht, aber niemand sie aufrufen kann: "AUDIT-02 verlangt das Prüfkommando, das die Stelle benennt". Das Kommando existiert jetzt, ist bei AppAPI registriert, in `occ list` sichtbar, von aussen nicht erreichbar, und es benennt die Stelle mit Kette und Nummer statt nur mit der Tatsache. Damit sind die drei Anforderungen dieser Phase (AUDIT-01, AUDIT-02, AUDIT-03) vollständig.

## Threat Flags

Keine neue Fläche. Der Plan legt eine Route an, und sie ist der Grund, warum sie im Manifest nicht steht: `git status --short pyproject.toml uv.lock` ist leer (T-18-SC), `<url>` unverändert. Die fünf `mitigate`-Fäden des Plans sind eingelöst:

| Faden | Wo eingelöst |
|-------|--------------|
| T-18-07 | keine `<url>`, Doppelprüfung mit 404 und 401, und ein Fall, der behauptet, dass keine der beiden Antworten verrät, welche Prüfung ablehnte |
| T-18-03 | drei Manipulationsfälle mit einer eigenen `sqlite3`-Verbindung an der Ablage vorbei, jeder behauptet die Nummer wörtlich |
| T-18-08 | `_printable` klammert die Kennung, der Fall behauptet die Zeilenzahl und dass keine Zeile das Urteil ist |
| T-18-20 | immer 200, mit einem eigenen Fall über alle vier Ausgänge |
| T-18-10 | im Fehlerfall nur `type(exc).__name__`; der Fall behauptet, dass weder `audit.sqlite3` noch der Pfad in Antwort oder Log stehen |

T-18-04 bleibt wie geplant `accept` und steht als letzter Satz **in der Antwort selbst**, nicht nur im Docstring: wer diese Datei schreiben kann, kann die Kette dahinter neu rechnen.

## Known Stubs

Keine.

## User Setup Required

None - no external service configuration required. Nach dem nächsten Deaktivieren-Aktivieren-Zyklus steht `occ mcp_connector:audit:verify` in `occ list`; `--json` liefert dieselbe Auskunft maschinenlesbar.

## Next Phase Readiness

- Plan 18-09 fasst `entry_exapp.py` nicht mehr an; die Route hängt, der Recorder trägt `env`, und die Kontoprüfung aus D-12 findet beides vor.
- Phase 19 findet mit `mcp_connector:audit:` einen Namensraum vor, der ein zweites Kommando trägt, und mit `command_schemes()` eine Liste, an die ein drittes Schema angehängt wird, ohne die Registrierung anzufassen.
- `used_bytes_after` bleibt der einzige geparkte Name dieser Phase und wartet auf das lesende Kommando von AUDIT-04.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract -q` — grün (exit 0)
- `uv run --no-sync ruff check .` / `ruff format --check .` — grün (213 Dateien)
- `uv run --no-sync pyright` — 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`
- `grep -c "<url>" appinfo/info.xml` — 14 vorher, 14 nachher
- `git status --short pyproject.toml uv.lock` — leer
- `python -c "... occ.command_schemes() ..."` — `2`, `['mcp_connector:purge', 'mcp_connector:audit:verify']`, `['purge', 'audit-verify']`
- `grep -c "mcp.custom_route\|@mcp\." src/mcp_connector/exapp/audit_verify.py` — 0

## Self-Check: PASSED

Beide neuen Dateien und alle acht geänderten liegen auf der Platte, und alle vier Commits stehen im Log (`3274138`, `277308c`, `87903b9`, `a7acdf0`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
