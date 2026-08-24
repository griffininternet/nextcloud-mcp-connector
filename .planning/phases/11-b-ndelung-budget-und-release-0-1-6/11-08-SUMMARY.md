---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 08
subsystem: api
tags: [acceptance, tool-surface, one-truth, truncation-keys, readme, i18n, tool-15, tool-16]

# Dependency graph
requires:
  - phase: 11-03
    provides: "fetch löst message:<token>:<messageId> und table:<tableId> auf, ohne die das Abnahmeskript die zwei neuen Id-Arten nicht rufen könnte"
  - phase: 11-07
    provides: "MAX_TOOL_BYTES = 1400 und BUDGET_BYTES = 18000, gegen die die erweiterte mail_browse-Beschreibung gemessen wurde"
  - phase: 10-mail
    provides: "die Mail-Kette des Abnahmeskripts, der Schlüssel truncated auf beiden Ebenen und die vier Info-Befunde aus 10-REVIEW.md"
provides:
  - "die erwartete Werkzeugmenge des Abnahmeskripts kommt aus client.list_tools(); die literale 21er-Namensliste existiert nicht mehr"
  - "_mail_message_id, _talk_message_id und _table_to_fetch: je (id, reason), genau eines von beiden gefüllt"
  - "fetch-Abnahme für vier Id-Arten (file:, mail:, message:, table:), jede mit einer Id aus einem Lesevorgang desselben Laufs"
  - "preview_truncated als Eintragsfeld der Mail-Antwort; truncated bleibt die Antwortebene"
  - "drei READMEs mit sieben Id-Arten, gleicher fetch-Zeile, gleicher prepare_context-Beschreibung"
affects:
  - "11-09 (Changelog 0.1.8: die Umbenennung truncated -> preview_truncated ist eine Antwortformat-Änderung und muss dort stehen; IN-02 ist der letzte offene Befund)"
  - "11-10 (die Abnahme läuft ab jetzt gegen die Registry, ein neu registriertes Werkzeug fällt dort auf)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die erwartete Menge kommt aus der laufenden Registry, nie aus einer zweiten Liste im Skript; die Zahl lebt in tests/contract/test_tool_surface.py"
    - "Ein Helfer gibt (id, reason) zurück, genau eines von beiden gefüllt: der Aufrufer muss keinen Grund erfinden"
    - "Ein leerer Rückgabewert von call heisst 'schon als FAIL verbucht' und erzeugt keine SKIP-Zeile"
    - "Ein Antwortschlüssel trägt je Ebene genau eine Bedeutung; die Ebene steht im Namen, wenn zwei Ebenen dasselbe Wort brauchen"
    - "Ein Docstring nennt keine Zahl, die ein Test derselben Datei pinnt, sondern verweist auf die Gate-Funktion"
    - "Eine Beschreibung, die wächst, wird im selben Edit an anderer Stelle komprimiert, damit das Byte-Gate nicht durch Prosa steigt"

key-files:
  created:
    - .planning/phases/11-b-ndelung-budget-und-release-0-1-6/deferred-items.md
  modified:
    - scripts/acceptance_all_tools.py
    - src/mcp_connector/tools/mail.py
    - src/mcp_connector/server/reg_mail.py
    - tests/unit/test_mail_tools.py
    - tests/unit/test_exapp_env_setup.py
    - README.md
    - README.de.md
    - README.fr.md

key-decisions:
  - "EXPECTED_TOOLS = 21 im Abnahmeskript fällt ersatzlos weg, nicht nur die Namensliste: eine Zahl im Skript ist dieselbe zweite Wahrheit wie eine Liste; an ihre Stelle tritt eine FAIL-Zeile für den einzigen Fall, den das Lesen der Registry nicht deuten kann (tools/list antwortet mit null Werkzeugen)"
  - "MAIL_BROWSE als Modulkonstante: die Mail-Kette nannte denselben Werkzeugnamen fünfmal wörtlich, und fünf Kopien eines Namens sind fünf Stellen zum Übersehen"
  - "Von den zwei Wegen aus IN-01 wird die Umbenennung gewählt statt der Doppelnutzung im Docstring: eine Erklärung im Docstring löst die Verwechslung nicht auf, wenn beide Lesarten in derselben Antwort plausibel bleiben"
  - "Die Filterzeile im mail_browse-Docstring wird im selben Edit um 9 Bytes komprimiert, damit die 54 Bytes der zwei Schlüsselnamen nicht die Kopffreiheit unter MAX_TOOL_BYTES aufbrauchen (1331 -> 1376 von 1400)"
  - "Der Docstring von variable_problems nennt gar keine Zahl mehr, statt vier durch sechs zu ersetzen: die nächste Umgebungsvariable macht jede Zahl im Prosatext wieder falsch"
  - "talk.py trägt dieselbe Doppelbedeutung von truncated wie mail.py vor IN-01, wird hier aber nicht angefasst: ausserhalb der files_modified dieses Plans und eine eigene Vertragsänderung (deferred-items.md, DF-11-01)"

patterns-established:
  - "(id, reason)-Paare für jede Id, die aus einem Lesevorgang stammen muss: der Grund einer SKIP-Zeile wird dort gebildet, wo er bekannt ist"
  - "Ein Prüfschritt behauptet die Abwesenheit der zweiten Kopie (code.count(name) <= 2), nicht nur die Anwesenheit der neuen Quelle"

requirements-completed: [TOOL-15, TOOL-16]

# Metrics
duration: 30min
completed: 2026-08-25
---

# Phase 11 Plan 08: Eine Wahrheit für die Abnahme, ein Schlüssel je Bedeutung, drei gleiche READMEs Summary

**Das Abnahmeskript liest seine Erwartung ab jetzt aus `client.list_tools()` statt aus einer
zweiten Namensliste, `truncated` bedeutet in einer Mail-Antwort je Ebene genau eine Sache, und
die drei READMEs nennen dieselben sieben Id-Arten.**

## Performance

- Dauer: rund 30 Minuten
- Tasks: 3, je ein Commit
- Dateien: 8 geändert, 1 angelegt

## Was sich am Abnahmeskript geändert hat

Drei Dinge, und das erste ist der Grund für den Plan:

1. **Eine Wahrheit.** `run()` gibt die Namen aus `tools/list` zurück, `main()` vergleicht
   `report.called()` gegen genau diese Menge, und die Abschlusszeile nennt die Zahl der
   Registry. Die literale Menge mit den 21 Namen und die Konstante `EXPECTED_TOOLS = 21` sind
   beide weg. Ein Werkzeug, das die Registry führt und die Abnahme nie angefasst hat, steht
   damit namentlich in der Fehlermeldung: genau der Fall, den eine handgepflegte Liste
   verpasst hätte.
2. **IN-04.** Die Mail-Kette liegt in `_mail_message_id`, die Talk-Kette in
   `_talk_message_id`. Beide prüfen den Rückgabewert von `call`: ein leerer String heisst
   "schon als FAIL verbucht", und dann entsteht **keine** SKIP-Zeile. Nur ein erfolgreicher
   Aufruf mit einer leeren Antwort schreibt eine, und ihr Grund ist dann wahr. Vor dieser
   Änderung erzeugte ein fehlgeschlagenes `mail_browse level=mailboxes` eine FAIL-Zeile **und**
   eine SKIP-Zeile mit dem Grund "that mail account lists no mailbox", der nicht stimmte und
   die Fehlerzeile daneben verdeckte.
3. **Zwei neue Id-Arten in der Abnahme.** `fetch("message:<token>:<id>")` mit einem Token aus
   `talk_browse(level="conversations")` und einer Nachrichten-Id aus
   `talk_browse(level="messages")`; `fetch("table:<id>")` mit einer Tabellen-Id aus dem
   `tables_browse`-Lauf, der ohnehin stattfindet (kein zusätzlicher Request). Jede Id kommt aus
   einem Lesevorgang desselben Laufs, nach der Regel, die schon in der Datei stand.

Die drei Helfer geben `(id, reason)` zurück, von denen immer genau eines gefüllt ist. Dadurch
unterscheidet jeder Grund "die Instanz hat kein solches Objekt" von "der Aufruf davor ist
fehlgeschlagen", ohne dass die Aufrufstelle raten muss.

## Antwortformat-Änderung: `truncated` zu `preview_truncated` (für Plan 11-09)

**Betroffene Ebene: die Eintragsebene von `mail_browse(level="messages")`, also jeder Eintrag
in `results`.** Ein Eintrag, dessen Vorschau bei `MAX_PREVIEW_BYTES` (400) geschnitten wurde,
trägt ab 0.1.8 `preview_truncated: true` statt `truncated: true`.

**Nicht betroffen: die Antwortebene.** `answer["truncated"]` bleibt, wo es steht, und bedeutet
weiterhin "diese Seite wurde geschnitten"; daneben steht `next`, und `_CURSOR_HINT` beschreibt
genau diese Ebene (der Hinweistext nennt jetzt zusätzlich den Eintragsschlüssel beim Namen).
Das gilt für beide Antwortebenen des Moduls, die Fensterantwort in `_messages` und die
Projektion in `_envelope`.

Das ist eine sichtbare Vertragsänderung und gehört in den Changelog-Block von 0.1.8.

## Die vier Info-Befunde aus `10-REVIEW.md`

| Kennung | Zustand | Wo |
|---------|---------|----|
| IN-01 | geschlossen | `tools/mail.py` (`preview_truncated`), `reg_mail.py` (Docstring nennt beide Schlüssel), neuer Test für den gemeinsamen Fall |
| IN-02 | **offen, bewusst** | CHANGELOG-Sektion `[0.1.5]`; gehört zu Plan 11-09 und ist danach der letzte offene Befund der Phase-10-Review |
| IN-03 | geschlossen | `tests/unit/test_exapp_env_setup.py`, Docstring von `variable_problems` verweist auf die Gate-Funktion statt auf eine Zahl |
| IN-04 | geschlossen | `scripts/acceptance_all_tools.py`, SKIP-Zweige hinter einer Erfolgsprüfung |

Dazu der Tech-Debt-Eintrag "acceptance_all_tools-Zählung": erledigt, die Zählung kommt aus der
Registry.

## Die geänderten README-Stellen, je Sprache

Vier Stellen, dreimal, damit die zwei ungeprüften Übersetzungen nicht weiter driften (WR-05).
Der Contract-Test `test_the_readme_permission_table_matches_the_live_registry` liest
ausschliesslich `README.md`.

| Stelle | README.md | README.de.md | README.fr.md |
|--------|-----------|--------------|--------------|
| Id-Arten | "the seven id kinds" plus `message:<token>:<messageId>` und `table:<tableId>` | "die sieben ID-Arten", gleiche zwei Formen | "les sept types d'id", gleiche zwei Formen |
| Mail-Suchtreffer bleibt URL | neuer Aufzählungspunkt (RFC-Message-Id auf `databaseId` ungemessen) | neuer Aufzählungspunkt | neuer Aufzählungspunkt |
| `fetch`-Zeile der Werkzeugtabelle | "...file, note, card, event, mail, Talk message or table" | "...Termin, einer Mail, einer Talk-Nachricht oder einer Tabelle" | "...un courriel, un message Talk ou un tableau" |
| `prepare_context` (Statuszeile + Tabellenzeile) | Talk-Digest, Mail-Zähler, drei Kappungen, kein Betreff/Inhalt | dieselbe Aussage, echte Umlaute | dieselbe Aussage, mit Akzenten und Cedille |

Name und Stufe jeder Tabellenzeile sind unverändert; nur die Beschreibungsspalte hat sich
bewegt. Die Werkzeugzahl bleibt in allen drei Dateien 21 (zweimal je Datei, geprüft).

Die Beispielzeile mit `truncated` (`{"items": ["..."], "truncated": true, "next": "..."}`,
README.md:243, README.de.md:251, README.fr.md:256) wurde **geprüft und nicht angenommen**: sie
beschreibt die Antwortebene einer Dateiliste, steht neben `next` und bleibt damit richtig. Eine
Beschreibung der Mail-Eintragsebene gibt es in keiner der drei Dateien und in keiner Seite
unter `docs/`.

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Das Abnahmeskript bekommt eine Wahrheit statt einer Kopie | `159501b` |
| 2 | IN-01 und IN-03: ein Schlüssel, eine Bedeutung, eine richtige Zahl | `53ba602` |
| 3 | Drei READMEs auf denselben Stand, sieben Id-Arten | `151aad9` |

## Files Created/Modified

- `scripts/acceptance_all_tools.py` - Modul-Docstring (Registry statt 21, neuer Absatz über die
  Id-Arten), `MAIL_BROWSE`, `run()` gibt die Registry-Namen zurück, `_mail_message_id`,
  `_talk_message_id`, `_table_to_fetch`, vier `fetch`-Aufrufe, `main()` ohne `expected`-Menge
- `src/mcp_connector/tools/mail.py` - `entry["preview_truncated"]` mit Begründungskommentar,
  `_CURSOR_HINT` benennt beide Schlüssel
- `src/mcp_connector/server/reg_mail.py` - Tool-Docstring nennt beide Schlüssel, Filterzeile
  komprimiert, Modul-Docstring begründet die Erweiterung gegen das Byte-Gate
- `tests/unit/test_mail_tools.py` - Eintragsbehauptung auf `preview_truncated` gezogen, neuer
  Test `test_a_cut_page_and_a_cut_preview_are_two_keys_with_two_meanings`
- `tests/unit/test_exapp_env_setup.py` - Docstring von `variable_problems` ohne Zahl
- `README.md`, `README.de.md`, `README.fr.md` - die vier Stellen oben
- `.planning/phases/11-.../deferred-items.md` - neu, DF-11-01

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die zwei, die über diesen Plan hinaus wirken:

- Die Werkzeugoberfläche hat ab jetzt eine einzige Wahrheit, und sie liegt in einem Test. Skript
  und Dokument lesen sie oder nennen sie gar nicht.
- Ein Antwortschlüssel, den zwei Ebenen brauchen, trägt die Ebene im Namen. Das ist die Regel,
  aus der DF-11-01 für Talk folgt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Abnahmelauf braucht andere Variablennamen, als der Plan nennt**

- **Gefunden bei:** Task 1, Verifikationsschritt 4
- **Problem:** Der Plan ruft `. ./.env.exapp` und danach `scripts/acceptance_all_tools.py`. Die
  Datei `.env.exapp` führt aber `NC_MCP_TEST_USER` und `NC_MCP_TEST_APP_PASSWORD`, während das
  Skript `NC_MCP_USER` und `NC_MCP_APP_PASSWORD` verlangt (die stehen in `.env.test`, das auf
  die andere Instanz zeigt). Der Lauf endete mit Exit-Code 2, bevor ein einziges Werkzeug
  gerufen wurde.
- **Fix:** Die zwei Namen im Lauf gesetzt
  (`NC_MCP_USER="$NC_MCP_TEST_USER"`, `NC_MCP_APP_PASSWORD="$NC_MCP_TEST_APP_PASSWORD"`), also
  gegen die ExApp-Topologie mit GreenMail statt gegen die Testinstanz. Das ist die Instanz, auf
  der Mail, Talk und Tables überhaupt Daten haben, also der Lauf, der die zwei neuen Id-Arten
  wirklich prüft. Keine Datei geändert, nur der Aufruf.
- **Commit:** kein eigener; Teil von `159501b`

**2. [Rule 2 - Fehlende Notwendigkeit] Die Filterzeile im `mail_browse`-Docstring komprimiert**

- **Gefunden bei:** Task 2
- **Problem:** Die vom Plan verlangte Nennung beider Schlüssel im Tool-Docstring kostet 54
  Bytes und hob `mail_browse` von 1331 auf 1385 Bytes, bei `MAX_TOOL_BYTES = 1400`. 15 Bytes
  Kopffreiheit unter einem Gate sind kein Zustand, in dem der nächste Satz noch passt.
- **Fix:** "A filter value with a space or colon must be percent encoded" zu "Percent encode a
  filter value with a space or colon" (9 Bytes), Endstand 1376. Keine `Field`-Beschreibung
  angefasst; der Grund steht im Modul-Docstring von `reg_mail.py`.
- **Commit:** `53ba602`

**3. [Ausserhalb des Scope, nicht repariert] `truncated` in `tools/talk.py`**

- Siehe `deferred-items.md`, DF-11-01. `talk.py` steht nicht in den `files_modified` dieses
  Plans, und die Umbenennung wäre eine zweite Vertragsänderung im selben Release.

## Issues Encountered

Keine. Kein Auth-Gate, kein Checkpoint, keine Paketinstallation.

## Verification Results

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | 197 Dateien, unverändert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src scripts vulture_whitelist.py` | grün, kein neuer Whitelist-Eintrag |
| `uv run pytest -q` | Exit 0 |
| `uv run pytest tests/contract -q` | Exit 0 |
| Prüfschritt Task 1 (eine Wahrheit, keine zweite Kopie) | "acceptance script has one truth" |
| Prüfschritt Task 2 (Eintrags- und Antwortebene, "four variables") | "IN-01 and IN-03 closed" |
| Prüfschritt Task 3 (acht Präfixe, keine Em-Dashes, Umlaute, Akzente) | "three readmes aligned" |
| Prüfschritt Task 3 (Werkzeugzahl in drei Sprachen) | "expected tools 21", konsistent |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15657 von 18000 Bytes, `mail_browse` 1376 von 1400 |
| `uv run python scripts/acceptance_all_tools.py` (ExApp-Topologie, live) | Exit 0, 30 OK-Zeilen, **keine** FAIL- und **keine** SKIP-Zeile; `fetch` löste `file:475`, `mail:13`, `message:o4vwrd7g:43` und `table:1` auf |
| `git diff --stat` gegen `pyproject.toml`, `uv.lock`, `appinfo/info.xml`, `CHANGELOG.md` | keine Änderung |

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. Die sechs `mitigate`-Dispositionen des Plans sind abgedeckt:
T-11-51 (Registry statt Skriptliste), T-11-52 (SKIP nur nach Erfolg), T-11-53 (jede Id aus
einem Lesevorgang), T-11-54 (`preview_truncated` plus Test des gemeinsamen Falls), T-11-55
(Docstring ohne Zahl), T-11-56 (drei READMEs in einer Task, Prüfschritt über alle drei).
T-11-SC ist trivial erfüllt: kein `uv add`, kein `pip install`, `pyproject.toml` und `uv.lock`
unangetastet.

## User Setup Required

Keins.

## Next Phase Readiness

Plan 11-09 (Changelog und Release 0.1.8) kann starten. Was er von hier übernimmt:

- die Antwortformat-Änderung `truncated` zu `preview_truncated` mit der Ebene, auf die sie
  wirkt (Abschnitt oben),
- IN-02 als letzten offenen Befund der Phase-10-Review (fehlende `[0.1.5]`-Sektion),
- die Aussage, dass die Abnahme gegen die Registry läuft, falls der Release-Text sie erwähnt.

## Self-Check: PASSED

Alle acht geänderten und zwei angelegten Dateien existieren auf der Platte, alle drei
Task-Commits sind in `git log`.
