---
phase: 18-audit-log-kern
plan: 07
subsystem: audit
tags: [audit-log, admin-settings, feature-switch, off-by-default, wiring, D-14, D-15]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "AuditStore, AUDIT_FILENAME, CHAIN_INSTANCE, KIND_SWITCH, ACTOR_UNKNOWN, RETENTION_DAYS, SIZE_LIMIT_BYTES und audit_opener"
  - phase: 18
    plan: 04
    provides: "sweep(moment=..., retention_days=..., size_limit=...) samt Grabstein"
  - phase: 18
    plan: 05
    provides: "der Konstruktorparameter audit_recorder an RequireAppApi und die Ablage in der Anfrage"
  - phase: 18
    plan: 06
    provides: "Recorder mit vier Feldern, note_switch, SWITCH_ON und SWITCH_OFF"
provides:
  - "config.ENV_AUDIT_LOG, ENV_AUDIT_RETENTION_DAYS, ENV_AUDIT_MAX_BYTES samt audit_log_enabled, audit_retention_days und audit_size_limit"
  - "audit_log als siebter Schlüssel in CONFIG_KEYS, KEY_TO_ENV und SWITCH_KEYS und als siebtes Formularfeld mit default False"
  - "entry_exapp.build_exapp_app baut den Audit-Opener und reicht einen Recorder nur hinter dem Schalter an RequireAppApi"
  - "entry_exapp._audit_startup: die Schaltzeile aus D-15/D-16 und der einmalige Aufräumlauf einer abgeschalteten Ablage"
affects: [18-08, 18-09, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Schalter mit Vorgabe aus im Code, dessen Leser ausdrücklich die Gegenrichtung von talk_send_enabled fährt und den Unterschied als Kommentar trägt"
    - "Zwei Zahlen doppelt geschrieben statt importiert, weil der Import einen Ring schliessen würde, und ein Test hält beide Paare gleich"
    - "Ein Startlauf, der nie wirft und dessen Fehlschlag nur den Ausnahmetyp kostet, nach dem Muster von exapp/purge.py"

key-files:
  created: []
  modified:
    - src/mcp_connector/config.py
    - src/mcp_connector/exapp/config_values.py
    - src/mcp_connector/exapp/admin_settings.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/entry_exapp.py
    - tests/unit/test_config.py
    - tests/unit/test_exapp_config_values.py
    - tests/unit/test_exapp_admin_settings.py
    - tests/unit/test_exapp_entry.py
    - docs/oauth-setup.md

key-decisions:
  - "Die zwei Vorgabezahlen stehen doppelt in config.py statt importiert zu werden: der Import wäre ein Ring, der heute nur überlebt, weil audit/__init__ seinen config-Zugriff erst zur Aufrufzeit macht"
  - "audit_log_enabled ist die positive Richtung und trägt den Unterschied zu talk_send_enabled als Kommentar, damit niemand das falsche Vorbild kopiert"
  - "Beide Zahlenleser nehmen nur eine ASCII-Ziffernfolge und fangen zusätzlich ValueError, weil die Stellenbegrenzung von int() seit Python 3.11 auch eine reine Ziffernfolge ablehnen kann"
  - "Der Startlauf räumt genau dann auf, wenn die Datei schon vorher da war: eine frisch angelegte hat nichts zu verlieren, und eine abgeschaltete hat sonst keine Gelegenheit mehr"
  - "Die ausführliche Beschriftung samt Mitbestimmungshinweis bleibt AUDIT-05 und ist hier ausdrücklich nicht vorweggenommen"

patterns-established:
  - "Eine Gegenprobe je verdrahteter Stelle: das Argument entfernen, den Aufruf entfernen, den Wert auf None setzen, den Aufräumlauf abschalten, und jedes Mal den roten Fall festhalten"

requirements-completed: [AUDIT-01, AUDIT-03]

# Metrics
duration: 50min
completed: 2026-08-29
---

# Phase 18 Plan 07: Der Schalter aus D-14 Summary

**Das Log liegt hinter einem Kästchen, das ab Werk leer ist: ohne Admin-Wert und ohne Umgebungsvariable entsteht nicht einmal die Datei, und wer es einschaltet oder ausschaltet, hinterlässt damit selbst eine Zeile in der Instanzkette.**

## Performance

- **Duration:** 50 min
- **Started:** 2026-08-29T09:33:00Z
- **Completed:** 2026-08-29T10:23:00Z
- **Tasks:** 3
- **Files modified:** 10 (0 neu, 10 geändert)

## Accomplishments

- Die dritte Stufe der Kette steht und sagt "aus": `config.audit_log_enabled({})` ist `False`, und der bekannte 401 des ersten Starts nach einer Installation fällt in dieselbe Richtung, weil ein leeres Ergebnis genau diese Vorgabe gelten lässt.
- `audit_log_enabled` trägt den Unterschied zu `talk_send_enabled` als Kommentar und als Testfall: dort darf ein Tippfehler keine Fähigkeit wegnehmen, hier darf ein Tippfehler kein Protokoll über namentlich genannte Menschen starten. Die WARNING nennt das Feld und nie den Wert.
- Beide Zahlenleser sind gegen jede Zeichenkette gehärtet, mit einem Fall über `"²"`, `"١٢٣"` und eine Folge von 5000 Ziffern: die ersten beiden liesse `str.isdigit` allein durch, die dritte lehnt `int()` seit der Stellenbegrenzung von Python 3.11 ab. Keine der drei Funktionen wirft.
- Der siebte Schlüssel steht in `CONFIG_KEYS`, `KEY_TO_ENV` und `SWITCH_KEYS`, und das Formular hat ein siebtes Feld an derselben Stelle: `uv run --no-sync python -c "... len(c.CONFIG_KEYS) ... 'audit_log' in c.SWITCH_KEYS"` meldet `7 True`, und der Test aus `test_exapp_admin_settings.py`, der Feldkennungen und `CONFIG_KEYS` in derselben Reihenfolge gleichsetzt, bleibt grün.
- Das neue Feld trägt `"type": "checkbox"`, `"default": False` und kein `sensitive` in keiner Schreibweise (T-18-19): ein verschlüsselter Wert wäre bei diesem Feld der schlimmste der sieben Fälle, weil er auch nicht mehr als "aus" lesbar wäre.
- Der Recorder wird in der Produktion gebaut, und nur hinter dem Schalter. Damit ist AUDIT-01 keine Aussage über einen Testaufruf mehr, sondern über eine laufende Instanz: das war der ausdrückliche Vorbehalt, unter dem die Pläne 18-01 bis 18-06 ihre Anforderungen zurückgehalten haben.
- Der gebaute Recorder trägt `env` gleich dem aufgelösten Mapping, belegt durch einen eigenen Fall, der zusätzlich gegen `None` und gegen `os.environ` behauptet. Ohne ihn stünde die Kontoprüfung aus D-12 im Code und wäre in der laufenden Anwendung nicht angeschlossen.
- Der Startlauf schreibt die Schaltzeile nur, wenn der gelesene Zustand vom zuletzt protokollierten abweicht: ein Neustart ist keine Schaltung, und ohne diese Regel wüchse die Instanzkette um eine Zeile je Containerstart.
- Die Werkzeugfläche hat sich um kein Byte bewegt: `tools/list: 15712 bytes, 21 tools, budget 18000`, vor und nach der Änderung dieselbe Zeile.

## Task Commits

1. **Task 1: Drei Umgebungswerte und ihre Leser in config.py** - `b71d6a9` (feat)
2. **Task 2: Der siebte Schlüssel in den drei Aufzählungen und im Formular** - `d272e5f` (feat)
3. **Task 3: Verdrahtung in entry_exapp.py samt Schaltprotokoll** - `ecbfea9` (feat)

## Files Created/Modified

- `src/mcp_connector/config.py` - `ENV_AUDIT_LOG`, `ENV_AUDIT_RETENTION_DAYS`, `ENV_AUDIT_MAX_BYTES`, die vier Zahlenkonstanten mit ihrer Begründung, `audit_log_enabled`, `audit_retention_days`, `audit_size_limit` und der gemeinsame `_bounded_number`
- `src/mcp_connector/exapp/config_values.py` - `audit_log` in `CONFIG_KEYS`, `KEY_TO_ENV` und `SWITCH_KEYS`; Modul-Docstring und die Zählkommentare von sechs auf sieben
- `src/mcp_connector/exapp/admin_settings.py` - das siebte Formularfeld mit `"default": False` samt Begründung des Auslieferungszustands; drei Zählstellen mitgezogen
- `src/mcp_connector/exapp/ui/strings.py` - `ADMIN_FIELD_AUDIT_LOG_LABEL` und `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION`, beide in `__all__`, beide kurz, mit dem ausdrücklichen Vermerk, dass die ausführliche Fassung AUDIT-05 ist
- `src/mcp_connector/entry_exapp.py` - `audit_opener` an derselben Stelle wie der OAuth-Opener, der Recorder hinter dem Schalter, `audit_recorder=` an `RequireAppApi`, `_audit_startup` und `_record_the_switch` sowie der Aufruf direkt hinter der Volume-Prüfung
- `tests/unit/test_config.py` - 15 Fälle über die drei Leser, darunter die Gleichheit der zwei doppelt geschriebenen Zahlen mit `audit/store.py`
- `tests/unit/test_exapp_config_values.py` - der siebte Schlüssel in vier Gleichheitsfällen plus ein eigener Fall für `SWITCH_KEYS`
- `tests/unit/test_exapp_admin_settings.py` - die Reihenfolge und die Typen um das siebte Feld erweitert, zwei neue Fälle über Auslieferungszustand und Beschriftung, und der Talk-Fall greift sein Feld jetzt über die Kennung statt über die letzte Position
- `tests/unit/test_exapp_entry.py` - acht neue Fälle über Schalter, Schaltzeile und Aufräumlauf samt zwei Lesehilfen (`audit_rows`, `recorder_of`)
- `docs/oauth-setup.md` - eine Zahl, die durch diesen Plan falsch geworden wäre (siehe Abweichung 1)

## Gegenproben (Nachweis, dass die neuen Fälle wirklich halten)

Alle vier von Hand geführt und über eine Sicherungskopie der Datei zurückgenommen (kein
`git stash`, kein `git clean`):

| Eingriff | Roter Fall | Fehlertext |
|----------|-----------|------------|
| `audit_recorder=recorder` an `RequireAppApi` entfernt | `test_with_the_switch_on_the_boundary_gets_a_recorder` und der `env`-Fall | `assert False = isinstance(None, <class '...record.Recorder'>)` |
| `env=env` durch `env=None` ersetzt | `test_the_recorder_carries_the_mapping_the_application_was_built_with` | `assert None == {'APP_ID': ...}` |
| `_record_the_switch(resolved)` aus `main` entfernt | die drei Fälle über die Schaltzeile | drei rote Fälle, `len(rows) == 1` gegen `0` |
| `if existed:` vor dem Aufräumlauf abgeschaltet | `test_a_switched_off_store_still_loses_its_expired_rows_on_a_start` | die abgelaufene Zeile steht noch da |

Der zweite Eingriff ist der, den der Plan ausdrücklich verlangt: der Nachweis, dass die
Verdrahtung der Kontoprüfung aus D-12 nicht nur ein `grep` auf `env=env` ist.

## Decisions Made

- **Die zwei Vorgabezahlen stehen doppelt statt importiert.** Der Plan erlaubt beides und
  verlangt eine Prüfung der Richtung vor dem Schreiben. Sie wurde geführt: `audit/store.py`
  selbst importiert nur die Standardbibliothek, aber ein Untermodul ist ohne sein Paket nicht
  zu haben, und `audit/__init__.py` importiert `config`. Ein `from .audit import store` in
  `config.py` läuft in allen vier gemessenen Reihenfolgen durch, aber nur, weil
  `audit/__init__` seinen `config`-Zugriff erst zur Aufrufzeit macht und weil der
  Importmechanismus für ein halb geladenes Untermodul auf `sys.modules` zurückfällt. Das ist
  eine Eigenschaft zweier Dateien, die niemand bewusst pflegen würde. Also stehen die zwei
  Zahlen zweimal, die Begründung steht in `audit/store.py`, und ein Test hält beide Paare
  gleich, so dass die Kopie nicht wegdriften kann.
- **`_bounded_number` fängt zusätzlich `ValueError`.** Der Ziffern-Test allein reicht nicht:
  seit Python 3.11 lehnt `int()` eine reine Ziffernfolge ab, sobald sie länger als 4300
  Stellen ist. Die Funktion wird beim Start gelesen, und ein abgelehnter Wert darf einen
  Container niemals am Bedienen hindern.
- **Der Aufräumlauf hängt an der Existenz der Datei vor dem Lauf, nicht danach.** Eine Datei,
  die dieser Start gerade erst anlegt, hat nichts zu verlieren; eine, die vorher da war, hat
  keine andere Gelegenheit mehr, wenn der Schreibpfad abgeschaltet ist (T-18-05).
- **Die Beschriftung bleibt kurz.** Sie sagt, was in einer Zeile steht, was nie darin steht,
  und dass eine Änderung erst nach einem Deaktivieren-Aktivieren-Zyklus wirkt. Der
  Mitbestimmungshinweis und die Grenzbeschreibung sind AUDIT-05 und gehören zu der Seite, die
  das Protokoll auch lesbar macht; die Hälfte davon hier hinzuschreiben liesse zwei Stellen
  unterschiedlich viel über denselben Schalter sagen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Eine Zahl in `docs/oauth-setup.md` wurde durch diesen Plan falsch**
- **Found during:** Task 2 (Suche nach allen Stellen, die "six" sagen)
- **Issue:** Der Satz "the app reads the same six keys back over the ExApp configuration
  channel" war eine Aussage über die Länge von `CONFIG_KEYS`, und diese Länge ist jetzt
  sieben. Der Plan nennt für die Zählstellen nur `admin_settings.py` und den Kommentar über
  `CONFIG_KEYS`; diese dritte Stelle steht in einer Datei, die der Plan nicht auflistet, wäre
  aber ab diesem Commit schlicht falsch gewesen.
- **Fix:** Die Zahl ist aus dem Satz entfernt statt hochgezählt worden: "the same keys". Damit
  kann derselbe Satz beim achten Wert nicht wieder falsch werden.
- **Files modified:** docs/oauth-setup.md
- **Verification:** `grep -rniE "six (values|keys|fields|admin)" src/ tests/ docs/` ohne
  Treffer ausser den historischen Ordnungszahlen ("the sixth joined in phase 9"), die richtig
  bleiben.
- **Committed in:** `d272e5f` (Task-2-Commit)

**2. [Rule 2 - Missing coverage] Ein Testfall zum Aufräumlauf und einer zum Fehlschlag des Startlaufs**
- **Found during:** Task 3
- **Issue:** Der Plan zählt fünf Fälle für `test_exapp_entry.py` auf. Zwei Zusagen des
  Auftrags hätten damit keinen Nachweis gehabt: der Aufräumlauf einer abgeschalteten Ablage
  (T-18-05, ausdrücklich ein `mitigate`-Faden des Plans) und das Akzeptanzkriterium "Ein
  Fehlschlag des Startlaufs kostet den Start nichts".
- **Fix:** Drei zusätzliche Fälle: die Gegenrichtung der Schaltzeile (`on` dann `off`), der
  Aufräumlauf mit einer abgelaufenen Zeile und einem Grabstein als Ergebnis, und ein
  Startlauf, der `OSError` wirft, während die Anwendung trotzdem gebaut wird und die Logzeile
  nur den Ausnahmetyp nennt.
- **Files modified:** tests/unit/test_exapp_entry.py
- **Verification:** Beide Fälle sind mit einer Gegenprobe belegt (Tabelle oben, Zeile 4).
- **Committed in:** `ecbfea9` (Task-3-Commit)

**3. [Rule 2 - Missing coverage] Fünfzehn Fälle in `tests/unit/test_config.py`**
- **Found during:** Task 1
- **Issue:** Der Plan listet für Task 1 nur `src/mcp_connector/config.py` als geänderte Datei
  und verlangt in den Akzeptanzkriterien trotzdem sechs Aussagen über Verhalten, darunter
  "keine der drei Funktionen wirft bei einer beliebigen Zeichenkette". Ohne Fälle wäre keine
  davon gehalten, und der Kommentar über den zwei doppelt geschriebenen Zahlen verspricht
  ausdrücklich einen Test, der beide Paare gleich hält.
- **Fix:** Ein eigener Abschnitt am Ende der Datei, im Zuschnitt des vorhandenen
  TALK-04-Abschnitts.
- **Files modified:** tests/unit/test_config.py
- **Verification:** `uv run --no-sync pytest tests/unit/test_config.py -q` grün.
- **Committed in:** `b71d6a9` (Task-1-Commit)

---

**Total deviations:** 3 auto-fixed (1 Bug, 2 fehlende Nachweise)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 hält eine bestehende Aussage
wahr, Abweichungen 2 und 3 belegen Akzeptanzkriterien, die der Plan aufstellt, ohne die
Testdatei dazu zu nennen.

## Issues Encountered

- `tests/unit/test_oauth_consent.py::test_a_flood_of_accepted_authorization_requests_ends_in_429`
  ist in einem von drei Läufen der vollen Suite rot geworden und in den beiden anderen sowie
  einzeln grün. Der Fall zählt 23 Anfragen gegen ein Fenster von 60 Sekunden; er hat mit
  diesem Plan keine Berührung (er baut seine eigene `Throttle` und kennt weder `entry_exapp`
  noch das Audit-Modul) und ist als zeitabhängig einzustufen. Nicht gefixt, weil ausserhalb
  des Auftrags: notiert für `deferred-items.md`.
- Der Plan schneidet die Verifikation von Task 1 ohne Vulture, und das ist bei diesem Zuschnitt
  richtig herum: zwischen Task 1 und Task 3 haben die drei neuen Leser keinen Produktionsaufrufer
  und der Dead-Code-Gate meldet sie mit 60 %. Mit Task 3 ist er wieder ohne Befund; ein
  Whitelist-Eintrag wäre für die Dauer von zwei Commits gesetzt und danach falsch gewesen.

## Anforderungen

**AUDIT-01 ist erfüllt.** Der ausdrückliche Vorbehalt der Pläne 18-01 bis 18-06 war, dass in
einer Installation keine Zeile entsteht, weil niemand in der Produktion einen `Recorder` baut.
Genau das tut `build_exapp_app` jetzt, hinter dem Schalter aus D-14. Damit ist "Jeder
Werkzeugaufruf erzeugt einen Eintrag" eine Aussage über eine laufende Instanz.

**AUDIT-03 ist erfüllt.** Die eigene Ablage neben dem OAuth-Speicher steht seit 18-01, die
Obergrenze und die Aufbewahrungsfrist seit 18-04, das Fail-open gegen ein volles Volume seit
18-06. Was fehlte, war die Einstellbarkeit: die Frist erreicht 180 Tage und kann darüber
hinausgehen, die Obergrenze ist verschiebbar, und beide sind über die Umgebung erreichbar.

**AUDIT-02 bleibt Pending**, weil das Prüfkommando aus Plan 18-08 fehlt.

## Threat Flags

Keine neue Fläche. Dieser Plan legt keine Route an, öffnet keinen Netzzugang und verlangt
keine neue Berechtigung; `git status --short appinfo/ pyproject.toml uv.lock` ist leer
(T-18-SC). Die fünf übrigen `mitigate`-Fäden des Plans sind eingelöst:

| Faden | Wo eingelöst |
|-------|--------------|
| T-18-11 | `audit_log_enabled` mit Vorgabe False, der Kommentar über den 401 des ersten Starts, und der Fall, der die Abwesenheit der Datei behauptet |
| T-18-18 | `_audit_startup` schreibt die Zeile bei jedem Zustandswechsel, `actor` ist `unknown`, und der Grund steht mit seiner Quelle im Docstring |
| T-18-19 | kein `sensitive` am neuen Feld, geprüft über `json.dumps(field).lower()`, und der Test, der Feldkennungen und `CONFIG_KEYS` gleichsetzt |
| T-18-05 | der Aufräumlauf beim Start, mit einem eigenen Fall über eine abgelaufene Zeile in einer abgeschalteten Ablage |
| T-18-10 | `_record_the_switch` protokolliert `type(exc).__name__`; der Fall behauptet zusätzlich, dass weder die Meldung noch `audit.sqlite3` in der Zeile stehen |

## Known Stubs

Keine. Ein bewusst offener Punkt bleibt und gehört Phase 19 beziehungsweise einem späteren
Plan: die drei neuen Variablen haben keinen `<environment-variables>`-Eintrag in
`appinfo/info.xml`, anders als `NC_MCP_TALK_SEND`. Das ist kein Versehen, sondern die
Verifikation dieses Plans, die `appinfo/` ausdrücklich unberührt verlangt. Der Weg eines
Administrators zum Schalter ist damit das Admin-Formular, also genau der Weg, den BL-06
fordert; ein Deploy-Variablen-Eintrag wäre die zusätzliche Bequemlichkeit für eine
Docker-Installation von Hand. Der Testfall über die drei Namen sagt das ausdrücklich, damit
niemand die Abwesenheit für einen Fehler hält.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract -q` — grün
- `uv run --no-sync ruff check .` / `ruff format --check .` — grün (211 Dateien)
- `uv run --no-sync pyright` — 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`
- `git status --short appinfo/ pyproject.toml uv.lock` — leer
- `grep -rniE "revisionssicher|AI-Act|DSGVO|SIEM" src/mcp_connector/exapp/ui/strings.py` — ohne Treffer
- `python -c "... config.audit_log_enabled({}) ..."` — `False True 180 365`
- `python -c "... len(c.CONFIG_KEYS) ... 'audit_log' in c.SWITCH_KEYS"` — `7 True`

## User Setup Required

None - no external service configuration required. Wer das Protokoll einschalten will, setzt
in den Administrationseinstellungen unter Sicherheit das siebte Kästchen und deaktiviert und
aktiviert die App danach einmal, wie bei jedem anderen Wert dieses Formulars.

## Next Phase Readiness

- Plan 18-08 findet die laufende Erfassung vor und kann sein Prüfkommando gegen eine Ablage
  richten, die im Betrieb wirklich Zeilen bekommt. Der fünfte Absatz über der Routenaufzählung
  in `entry_exapp.py` ist weiterhin frei und gehört diesem Plan.
- Plan 18-09 findet `Recorder.env` gefüllt mit dem aufgelösten Mapping vor, und ein Testfall
  hält das fest, damit die Kontoprüfung aus D-12 nicht in einer Anwendung landet, in der sie
  nichts anrufen kann.
- Phase 19 findet einen Schalter mit kurzer Beschriftung vor. AUDIT-05 hängt seine
  ausführliche Fassung an dieselben zwei Namen in `strings.py` und muss dafür weder Feld noch
  Lesepfad anfassen.

## Self-Check: PASSED

Alle zehn geänderten Dateien liegen auf der Platte, und alle drei Task-Commits stehen im Log
(`b71d6a9`, `d272e5f`, `ecbfea9`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
