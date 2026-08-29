---
phase: 18-audit-log-kern
plan: 09
subsystem: audit
tags: [audit-log, account-check, fail-safe, tombstone, D-12, A1, tdd]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "AuditStore, Entry, user_chain, CHAIN_INSTANCE, KIND_TOMBSTONE, ACTOR_UNKNOWN, USER_SILENCE_DAYS und should_check_accounts"
  - phase: 18
    plan: 04
    provides: "sweep, verify_chains und die Grabsteinform mit gap_chain und gap_hash"
  - phase: 18
    plan: 06
    provides: "Recorder mit dem Feld env, note() und der Aufräumzweig auf should_sweep"
  - phase: 18
    plan: 07
    provides: "entry_exapp.build_exapp_app baut den Recorder hinter dem Schalter und füllt env mit dem aufgelösten Mapping"
provides:
  - "audit/accounts.py: existing_users(env) und USERS_PATH, fail-safe in Löschrichtung, wirft nie"
  - "audit/store.py: silent_users(moment, silence_days) und drop_user_chain(nc_user, moment) samt Grabstein"
  - "audit/record.py: _drop_chains_without_an_account, angeschlossen im gebündelten Aufräumlauf hinter should_check_accounts"
  - "tests/integration/test_appapi_users_list.py: die Messung von A1 gegen die laufende HaRP-Topologie, im CI-Job exapp verdrahtet"
affects: [19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fail-safe in genau einer Richtung: jede Unsicherheit über die Eingabe fällt zugunsten des Behaltens, und die leere Antwort zählt als Unsicherheit"
    - "Der Zeitplan wird im Test nicht ersetzt, sondern erreicht: sqlite_sequence wird gesetzt, damit die nächste Zeile die zehntausendste ist, und das echte Prädikat entscheidet"
    - "Eine Löschung, die eine Spur hinterlässt: ein Grabstein je gefallener Kette, sonst wäre die Löschung spurlos"

key-files:
  created:
    - src/mcp_connector/audit/accounts.py
    - tests/unit/test_audit_accounts.py
    - tests/integration/test_appapi_users_list.py
  modified:
    - src/mcp_connector/audit/store.py
    - src/mcp_connector/audit/record.py
    - .github/workflows/ci.yml

key-decisions:
  - "Eine leere Liste ergibt None und nie ein leeres frozenset: das Log kann keine Kette haben, wenn die Instanz keine Nutzer hat, also ist die leere Liste immer ein Fehler"
  - "Eine Antwort, deren data kein JSON-Array ist, wird abgelehnt statt gedeutet: array_map behält die Schlüssel seiner Eingabe, und ein Objekt als Liste zu lesen hiesse, eine ungemessene Form in der einen Richtung zu deuten, die nicht zurückzunehmen ist"
  - "silent_users gruppiert über die Kettenkennung und nicht über nc_user, und _account_of ist die genaue Umkehrung von user_chain"
  - "drop_user_chain gibt die freien Seiten nach dem COMMIT zurück: eine ganze Kette ist das Grösste, was diese Ablage auf einmal hergibt"
  - "Der Integrationstest misst die Löschung wirklich, statt sie als ungemessen zu belegen: occ läuft im Container der Topologie, und wo das nicht geht, überspringt sich genau dieser Fall mit seinem Grund"
  - "Der CI-Job exapp führt die neue Datei aus; ohne diesen Schritt gäbe es die Messung, aber sie fände nie statt"

patterns-established:
  - "Eine Gegenprobe je Richtung der Asymmetrie: die None-Liste als leere Menge behandeln, den Zeitplan aushebeln, den Grabstein weglassen, und jedes Mal den roten Fall festhalten"

requirements-completed: []
# AUDIT-03 ist bereits mit Plan 18-07 erfüllt worden. Dieser Plan löst D-12 ein, das die
# Anforderung als Aufbewahrungsregel voraussetzt, und legt keine neue Anforderung ab.

# Metrics
duration: 62min
completed: 2026-08-29
---

# Phase 18 Plan 09: Kontoprüfung und die Messung von A1 Summary

**Wird ein Konto in Nextcloud gelöscht, fällt seine ganze Kette samt Grabstein beim nächsten gebündelten Lauf, und jede Unsicherheit über die Kontoliste, den Netzfehler und die leere Antwort eingeschlossen, lässt sie stehen.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-08-29T11:30:00Z
- **Completed:** 2026-08-29T12:32:00Z
- **Tasks:** 3
- **Files modified:** 6 (3 neu, 3 geändert)

## Accomplishments

- `existing_users` hat fünf Antwortformen und nur eine davon löscht: eine Liste mit
  mindestens einer Kennung ergibt ein `frozenset`, Netzfehler, jeder Status ungleich 200,
  eine unlesbare Hülle und die leere Liste ergeben `None`. Alle fünf sind eigene Fälle, die
  vier verschiedenen unlesbaren Formen davon parametrisiert.
- Der Weg kostet keine neue Berechtigung und keine neue Route:
  `GET /ocs/v2.php/apps/app_api/api/v1/users` mit den OCS-Kopfzeilen und den vier
  AppAPI-Kopfzeilen im App-Kontext, also mit leerer Nutzer-Id. Die drei Fundstellen in
  app_api v34.0.3 (`appinfo/routes.php:72`, `OCSApiController.php:81-86`,
  `ExAppService.php:199-203`) stehen im Modul-Docstring, damit die nächste Fassung dagegen
  nachgeprüft werden kann, und die Zahl aus dem Kostenabsatz (zehntausend Kennungen in einer
  Antwort) steht daneben, damit niemand die Funktion in eine Schleife stellt.
- `drop_user_chain` löscht in **einer** Transaktion und hängt genau einen Grabstein in die
  Instanzkette, mit `gap_chain`, `gap_hash` gleich dem Endhash der gefallenen Kette,
  `removed` und `actor = unknown`. Danach ist `verify_chains()` leer: die Löschung ist
  erklärt und nicht ein Bruch.
- Eine Kette, die es nicht gibt, bekommt keinen Grabstein. Ein Grabstein für eine Kette, die
  nie existiert hat, wäre eine Lücke im Protokoll, wo keine ist.
- Die Kontoprüfung läuft nur bei `should_check_accounts(seq)`, also bei jedem zwanzigsten
  Aufräumlauf. Der Fall dazu behauptet, dass ein gewöhnlicher Aufräumlauf die Liste **nicht**
  holt (`route.call_count == 0`), und die Gegenprobe unten zeigt ihn rot.
- Der Zeitplan wird in keinem Fall gepatcht. Wer die zehntausendste Zeile braucht, setzt
  `sqlite_sequence` auf 9999 und schreibt eine Zeile: damit reitet der Fall auf dem echten
  Prädikat von D-11 und D-12 statt auf einem ersetzten.
- Die Verdrahtung aus 18-07 ist vor der ersten Zeile geprüft worden, mit genau den zwei
  Griffen, die der Plan verlangt (siehe unten), und `entry_exapp.py` ist unverändert
  geblieben.
- A1 ist **gemessen angelegt und nicht als ungemessen abgelegt**: der Integrationstest führt
  die Löschung eines Wegwerf-Kontos über `occ user:delete` wirklich durch und behauptet
  danach die Abwesenheit in der Liste samt der Kontrolle, dass die anderen Konten noch da
  sind. Im lokalen Lauf steht keine Docker-Topologie zur Verfügung, deshalb siehe den
  eigenen Abschnitt "Messung von A1" weiter unten.

## Task Commits

1. **Task 1: audit/accounts.py, die Kontoliste mit fail-safe in Löschrichtung** - `4409de4` (feat)
2. **Task 2: Kettenlöschung samt Grabstein und die Anbindung an den Aufräumlauf** - `0b971f6` (test, RED) und `b90d25a` (feat, GREEN)
3. **Task 3: A1 messen, oder als ungemessen belegen** - `6aa78ad` (test)

## Files Created/Modified

- `src/mcp_connector/audit/accounts.py` (neu) - `USERS_PATH`, `existing_users`, `_identifiers`;
  der Modul-Docstring trägt die drei Fundstellen, den Kostenabsatz und den Satz, warum die
  Asymmetrie die Regel dieser Datei ist
- `src/mcp_connector/audit/store.py` - `USER_CHAIN_PREFIX` und `_account_of` als genaue
  Umkehrung von `user_chain`, die drei Anweisungen `_SILENT_CHAINS`, `_COUNT_OF_CHAIN` und
  `_DROP_CHAIN`, sowie die Methoden `silent_users` und `drop_user_chain`
- `src/mcp_connector/audit/record.py` - `_drop_chains_without_an_account` und der Aufruf im
  Aufräumzweig von `note`, hinter `should_check_accounts`; der Zeitpunkt des Laufs steht jetzt
  in einer Variablen, damit Frist, Grabstein und Schwelle über dieselbe Uhr sprechen
- `tests/unit/test_audit_accounts.py` (neu) - 18 Fälle (26 mit den Parametrisierungen) über
  eine echte Ablage in `tmp_path` und `respx` als Nextcloud
- `tests/integration/test_appapi_users_list.py` (neu) - vier Fälle mit Marker `integration`,
  Laufanweisung im Docstring, Wegwerf-Konto über `occ user:add` und `occ user:delete`
- `.github/workflows/ci.yml` - ein Schritt im Job `exapp`, der die neue Datei ausführt (siehe
  Abweichung 1)

## Belegte Verdrahtung (vor der ersten geschriebenen Zeile)

Der Plan verlangt zwei Griffe als Vorbedingung, beide geführt:

| Griff | Ergebnis |
|-------|----------|
| `grep -n "env=env" src/mcp_connector/entry_exapp.py` | `130:            env=env,` — die Zeile der `Recorder`-Konstruktion in `build_exapp_app` |
| `uv run --no-sync pytest tests/unit/test_exapp_entry.py -q` | grün, 113 Fälle; der Fall aus 18-07 heisst `test_the_recorder_carries_the_mapping_the_application_was_built_with` |
| `git diff --stat src/mcp_connector/entry_exapp.py` | leer, vor und nach diesem Plan |

## Gegenproben (Nachweis, dass die neuen Fälle wirklich halten)

Alle drei von Hand geführt und über eine Sicherungskopie der Datei zurückgenommen (kein
`git stash`, kein `git clean`):

| Eingriff | Roter Fall | Fehlertext |
|----------|-----------|------------|
| `known = frozenset()` statt der Rückkehr bei `None` | `test_an_unknown_account_list_drops_no_chain` | `assert 'u:alice' in {'i:instance', 'u:bob'}` |
| `if store.should_check_accounts(seq):` durch `if True:` ersetzt | `test_an_ordinary_sweep_never_asks_for_the_account_list` | `assert 1 == 0`, `route.call_count` |
| `_append_row(` in `drop_user_chain` übersprungen | zwei Fälle: der Grabstein und die gefallene Kette | `assert [] == ['u:alice']` |

Die erste ist die Gegenprobe, um die es in diesem Plan geht: sie zeigt, dass der Fall über
die `None`-Liste nicht zufällig grün ist, sondern die Löschung wirklich verhindert.

Ein vierter Eingriff ist ausdrücklich **nicht** als Beleg gezählt worden: `if known is None`
zu `if False` zu ändern liess alle Fälle grün, weil `nc_user not in None` einen `TypeError`
wirft, den das `except` von `note` fängt. Das ist die Fail-open-Regel bei der Arbeit, aber es
ist kein Nachweis über die Löschrichtung, und deshalb steht statt seiner die Fassung oben,
die wirklich löscht.

## Messung von A1

**Lokal ungemessen, im CI-Job `exapp` vorgesehen und dort verdrahtet.** Auf diesem Rechner
läuft die Linux-Docker-Engine nicht, was für dieses Projekt der Normalfall ist und der Grund,
aus dem `tests/conftest.py` den Marker `integration` ohne `NC_MCP_URL` in Übersprungen
verwandelt. Der Beleg, dass die Datei dabei nicht rot läuft:

```
uv run --no-sync pytest tests/integration/test_appapi_users_list.py -m integration -q -rs
ssss
SKIPPED [1] tests\integration\test_appapi_users_list.py:177:
  NC_MCP_URL is not set: no test Nextcloud available (Docker engine off)
```

Und im Vorgabelauf ohne `-m` wird die Datei über den Marker gar nicht erst gesammelt;
`uv run --no-sync pytest -q` bleibt grün.

Was der Test misst, sobald er im CI läuft, sind die vier Aussagen des Plans: Status und
Listenform, die bekannten Konten der Topologie, die schlichte Abwesenheit eines nie
existierenden Kontos ohne eigenen Status und ohne 404, und die Abwesenheit eines über
`occ user:delete` entfernten Kontos samt der Kontrolle, dass die übrigen Konten noch stehen.
Ob deaktivierte Konten enthalten sind, bleibt auch dann offen: die Topologie hat keinen
deaktivierten Nutzer, und einen anzulegen hiesse, die Fixtures der drei anderen
Integrationsdateien anzufassen. Die Zahl der Kennungen und die Fassung von `app_api` sind
Werte des CI-Laufs und stehen hier bewusst nicht als erfundene Zahlen.

**Der fail-safe aus Task 1 trägt die Absicherung unabhängig vom Ausgang dieser Messung.** Ein
roter Fall dort bedeutet "D-12 greift in dieser Topologie nicht", nie "eine Kette ist
versehentlich gefallen": jede Unsicherheit über die Liste antwortet mit `None`, und `None`
löscht nichts. Das ist der Satz, der diesen Plan auch dann trägt, wenn ein LDAP-Verzeichnis
eines Tages eine kurze Liste liefert.

## Decisions Made

- **Die leere Liste ist ein Fehler.** Sie ergibt `None` und nie ein leeres `frozenset`. Die
  Begründung steht im Docstring und ist eine Aussage über die Ablage, nicht über Nextcloud:
  eine Ablage mit einer schweigenden Kette gehört zu einer Instanz, die Nutzer hat, denn ohne
  Nutzer gäbe es die Kette nicht. Ein leeres `frozenset` liesse dagegen jede Kette der Instanz
  in einem einzigen Lauf fallen.
- **Eine Antwort, deren `data` kein JSON-Array ist, wird abgelehnt statt gedeutet.**
  `array_map` behält die Schlüssel seiner Eingabe, also könnte ein Backend die Liste als
  JSON-Objekt liefern. Das als Liste zu lesen hiesse, eine ungemessene Form in genau der
  Richtung zu deuten, die nicht zurückzunehmen ist. Der eigene Fall dazu heisst
  `data-is-an-object`, und der Docstring von `_identifiers` sagt, warum die Ablehnung hier die
  Entscheidung fürs Behalten ist.
- **`silent_users` gruppiert über die Kettenkennung.** Nicht über `nc_user`: die Kette ist,
  was fällt, und was ein Grabstein benennt, und eine Zeile mit leerem `nc_user` fiele bei der
  anderen Gruppierung ganz aus der Frage heraus. `_account_of` ist die genaue Umkehrung von
  `user_chain`, beide über dieselbe Präfixkonstante, damit sie nicht auseinanderlaufen können.
- **Die Schwelle ist am Rand einschliessend.** Ein Eintrag, der genau `silence_days` alt ist,
  gilt als schweigend, einer eine Sekunde jünger nicht. Das ist dieselbe Richtung, in der die
  Aufbewahrungsfrist derselben Datei schneidet (`at <= cutoff`), und ein eigener Fall hält
  beide Seiten des Randes fest.
- **Der freie Platz geht nach dem `COMMIT` zurück.** Eine ganze Kette ist das Grösste, was
  diese Ablage auf einmal hergibt, und kein `incremental_vacuum` läuft, solange eine
  Transaktion offen ist. Es ist derselbe Schritt, mit dem der Aufräumlauf endet.
- **Die Löschung wird wirklich gemessen, nicht nur beschrieben.** Der Plan erlaubt, den
  vierten Teil entfallen zu lassen. Er ist trotzdem geschrieben, weil der CI-Job die Topologie
  ohnehin hochfährt und `occ` dort erreichbar ist: der Fall legt ein Wegwerf-Konto an, prüft
  es in der Liste, löscht es und prüft es wieder. Wo `occ` nicht erreichbar ist, überspringt
  sich genau dieser Fall mit seinem Grund, und die drei anderen bleiben.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Der Messtest wäre in keinem Lauf gelaufen**

- **Found during:** Task 3
- **Issue:** Der Plan verlangt, dass der Test "im CI-Job `exapp` vorgesehen" ist, und die
  Akzeptanzkriterien lassen den Satz "im CI-Job `exapp` vorgesehen" in die SUMMARY schreiben.
  Der Job führt die Integrationsdateien aber einzeln auf (`test_exapp_dav_matrix.py`,
  `test_permission_fidelity_exapp.py`, `test_oauth_flow_exapp.py`) und sammelt nicht das
  Verzeichnis. Ohne einen eigenen Schritt existierte die Messung als Datei und fände nie
  statt, und der Satz in der SUMMARY wäre unwahr gewesen. `.github/workflows/ci.yml` steht
  nicht in der `files_modified`-Liste des Plans.
- **Fix:** Ein Schritt "The account list behind D-12 (AUDIT-03, assumption A1)" hinter dem
  OAuth-Schritt, im selben Zuschnitt wie seine drei Nachbarn, mit dem Kommentar, was ein roter
  Fall dort bedeutet und was er nicht bedeutet.
- **Files modified:** .github/workflows/ci.yml
- **Verification:** Die Datei parst als YAML und trägt zwölf Schritte im Job `exapp`, die
  Zeilenenden bleiben LF (`crlf 0`).
- **Committed in:** `6aa78ad` (Task-3-Commit)

**2. [Rule 1 - Bug] `--password-from-env` hätte nie ein Passwort gesehen**

- **Found during:** Task 3, beim Schreiben der Fixture des Wegwerf-Kontos
- **Issue:** Die erste Fassung setzte `OC_PASS` mit `monkeypatch.setenv` im Testkörper. Das ist
  gleich zweimal falsch: die Fixture läuft vor dem Testkörper, und die Umgebung dieses
  Prozesses reist ohnehin nicht durch `docker compose exec` in den Container. `occ user:add`
  wäre mit einem leeren Passwort abgebrochen, die Fixture hätte übersprungen, und der Fall
  hätte wie eine Topologie ohne `occ` ausgesehen statt wie ein Fehler im Test.
- **Fix:** `occ()` nimmt jetzt `passing=` und reicht die Variablen als `-eNAME=WERT` an
  `docker compose exec`; die Fixture setzt `OC_PASS` dort. Der Docstring sagt, warum ein
  `monkeypatch.setenv` an dieser Stelle nichts bewirkt.
- **Files modified:** tests/integration/test_appapi_users_list.py
- **Verification:** `ruff`, `pyright` und der Übersprung-Lauf grün; der Weg selbst wird im
  CI-Job gemessen.
- **Committed in:** `6aa78ad` (Task-3-Commit)

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1)
**Impact on plan:** Keine Erweiterung des Auftrags. Abweichung 1 macht eine Zusage des Plans
wahr, statt sie zu behaupten, Abweichung 2 korrigiert einen Fehler in einer Datei, die dieser
Plan selbst anlegt.

## Issues Encountered

- Die erste Gegenprobe zur `None`-Liste (`if known is None` zu `if False`) blieb grün, weil
  `nc_user not in None` einen `TypeError` wirft, den das `except` von `note` fängt. Der
  Eingriff ist deshalb nicht als Beleg gezählt worden; an seiner Stelle steht die Fassung, die
  die unbekannte Liste als leere behandelt und damit wirklich löscht. Der Nebenbefund ist
  angenehm: selbst ein grober Fehler in diesem Zweig kostet den Werkzeugaufruf nichts.
- `tests/unit/test_audit_accounts.py` schreibt und liest eine echte SQLite-Ablage in
  `tmp_path`; die Fälle mit dem Aufräumlauf laufen deshalb über den echten `sweep` mit
  Vorgabefrist. Das ist gewollt: der Aufräumlauf und die Kontoprüfung stehen im selben Zweig,
  und ein Doppelgänger für den einen hätte den anderen mit weggenommen.

## Anforderungen

Dieser Plan legt **keine** neue Anforderung ab. AUDIT-01, AUDIT-02 und AUDIT-03 sind mit den
Plänen 18-07 und 18-08 vollständig. Was hier entsteht, ist die Aufbewahrungsregel D-12, die
AUDIT-03 voraussetzt: das Log darf nicht unbegrenzt wachsen, und eine Kette ohne Konto ist der
Teil dieses Wachstums, den weder die Frist noch die Obergrenze zuverlässig erwischen, weil
eine Kette, die nichts mehr schreibt, auch nichts mehr überschreitet.

## Threat Flags

Keine neue Fläche. Dieser Plan legt keine Route an und verlangt keine neue Berechtigung; die
einzige neue ausgehende Verbindung geht auf einen Pfad, den AppAPI für genau diese
Kopfzeilen bereitstellt. `git status --short appinfo/ pyproject.toml uv.lock` ist leer
(T-18-SC). Die vier `mitigate`-Fäden des Plans sind eingelöst:

| Faden | Wo eingelöst |
|-------|--------------|
| T-18-09 | `None` bei jedem Fehler und bei leerer Liste, Schwelle von 30 Tagen, und die Messung von A1 als eigener Integrationstest samt CI-Schritt |
| T-18-10 | nur Status oder `type(exc).__name__`; der Fall sucht den App-Schlüssel, einen Kontonamen und den Text der Ausnahme in allen Logzeilen und findet keinen |
| T-18-21 | genau ein Grabstein je gefallener Kette, mit `gap_chain`, `gap_hash` und `removed`, plus der Fall, dass `verify_chains()` danach schweigt |
| T-18-16 | bleibt `accept` und ist trotzdem belegt: der Fall über den gewöhnlichen Aufräumlauf behauptet `route.call_count == 0` |

## Known Stubs

Keine.

## Verification

- `uv run --no-sync pytest tests/unit/test_audit_accounts.py -q` — grün, 26 Fälle
- `uv run --no-sync pytest tests/unit tests/contract -q` — grün
- `uv run --no-sync pytest -q` — grün (Marker `integration` bleibt ausgeschlossen)
- `uv run --no-sync pytest tests/integration/test_appapi_users_list.py -m integration -q -rs` — vier Übersprünge mit der genannten Variablen, kein roter Fall
- `uv run --no-sync ruff check .` / `ruff format --check .` — grün (216 Dateien)
- `uv run --no-sync pyright` — 0 errors, 0 warnings, 0 informations
- `uv run --no-sync vulture src scripts vulture_whitelist.py` — ohne Befund
- `uv run --no-sync python scripts/check_tool_budget.py` — `tools/list: 15712 bytes, 21 tools, budget 18000`
- `git status --short appinfo/ pyproject.toml uv.lock` — leer
- `git diff --stat src/mcp_connector/entry_exapp.py` — leer
- `FILES_WITH_OWN_SQL` unverändert bei zwei Einträgen, `ALLOWED_MODULE_STATE` bei zwei
- `grep -rniE "\barchiv" ...` über die drei neuen Dateien — ohne Treffer

## User Setup Required

None - no external service configuration required. Wer die Messung von A1 selbst führen will,
folgt der Laufanweisung im Docstring von `tests/integration/test_appapi_users_list.py`.

## Next Phase Readiness

- Phase 19 findet die Kontoprüfung angeschlossen vor: eine Kette ohne Konto existiert nach
  spätestens einem gebündelten Lauf nicht mehr, und was von ihr bleibt, ist ein Grabstein, den
  das Prüfkommando aus 18-08 bereits mitzählt.
- `existing_users` ist die einzige Stelle, an der dieses Modul Nextcloud nach Konten fragt.
  Ein zweiter Leser bekommt dieselbe Asymmetrie geschenkt, muss sie aber auch aushalten: die
  Funktion antwortet mit `None`, sobald irgendetwas unklar ist.
- Die vier Aussagen über A1 stehen als Fälle da, nicht als Absatz. Wer die Annahme später
  gegen ein LDAP-Verzeichnis prüfen will, setzt die Topologie um und lässt dieselbe Datei
  laufen.

## Self-Check: PASSED

Alle sechs Dateien liegen auf der Platte
(`src/mcp_connector/audit/accounts.py`, `src/mcp_connector/audit/store.py`,
`src/mcp_connector/audit/record.py`, `tests/unit/test_audit_accounts.py`,
`tests/integration/test_appapi_users_list.py`, `.github/workflows/ci.yml`), und alle vier
Commits stehen im Log (`4409de4`, `0b971f6`, `b90d25a`, `6aa78ad`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
