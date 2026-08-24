---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 04
subsystem: api
tags: [prepare-context, talk, digest, gather, budget, degradation, excerpts, tool-16]

# Dependency graph
requires:
  - phase: 11-01
    provides: "die Kind-Namen message und table, ohne die ein Treffer im Bündel nicht auflösbar wäre"
  - phase: 11-03
    provides: "fetch liest message: und table:, was die Reduktion in _short erst wahr macht"
  - phase: 09-talk
    provides: "talk_tools.browse(level='conversations') als ein Request mit unread, unread_mention, unread_mention_direct, last_activity und der gekappten Vorschau"
provides:
  - "TALK_BUDGET = 5.0, MAX_DIGEST = 3, DIGEST_PREVIEW_BYTES = 200 und EXCERPT_KINDS als Modul-Konstanten von tools/context.py"
  - "das dritte gather-Bein _talk plus die Auswertungskette _digest, _waiting, _urgency, _digest_entry, _preview, _count"
  - "der Top-Level-Schlüssel talk der Antwort, immer vorhanden und immer eine Liste"
  - "die drei wörtlichen degraded-Sätze des Talk-Beins"
  - "die auf resolvable reduzierte Zeile in _short, damit TOOL-16 auch im Bündel wirkt"
affects:
  - "11-05 (das Mail-Bein kopiert Bein, Auswertungsfunktion und Kappungssatz)"
  - "11-06 (prüft TALK_BUDGET, MAX_DIGEST und die Requestzahl live)"
  - "11-08 (drei READMEs beschreiben die Antwortform mit dem Schlüssel talk)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Bein je Quelle mit eigener asyncio.timeout-Decke, nie ein Timeout um das gather"
    - "Auswertungsfunktion in der Form von _schedule: isinstance-Zweig, fremde degraded-Einträge durchreichen, eigene Kappung mit Gesamtzahl benennen"
    - "Ein Top-Level-Schlüssel, der immer erscheint, plus zwei unterscheidbare Bedeutungen der leeren Liste"
    - "Eine eigene Konstante für die Reichweite der Auszüge, getrennt von der Gruppierung der Antwort"
    - "Fremde Marker vor der Messung entfernen, damit die Byte-Decke für das gilt, was herausgeht"

key-files:
  created: []
  modified:
    - src/mcp_connector/tools/context.py
    - tests/unit/test_tools_context.py

key-decisions:
  - "KIND_BUCKETS bleibt bei drei Kinds und _short liest die Auflösbarkeit nur noch aus dem Treffer: der Digest ist die einzige Talk-Aussage im Bündel, ein Talk-Bucket wäre eine zweite Wahrheit über dieselbe App in derselben Antwort"
  - "EXCERPT_KINDS existiert getrennt von KIND_BUCKETS, obwohl beide Tupel heute gleich sind: die Gruppierung der Antwort und die Frage, wessen Inhalt dieser Server ungefragt liest, dürfen nicht dieselbe Entscheidung sein (T-11-24)"
  - "DIGEST_PREVIEW_BYTES misst Bytes und nicht Zeichen, gegen den Wortlaut von CTX-01 und mit der Begründung im Kommentar: das Projekt budgetiert überall in Bytes, und talk_tools._capped ist der billigere Anschluss"
  - "TALK_BUDGET = 5.0 ist ausdrücklich als Setzung markiert; enger als CALENDAR_BUDGET, weil der Digest ein Request gegen eine Route ist und kein Fan-out"
  - "Die Doppelfehler-Regel bleibt wörtlich auf search_out und calendar_out, mit Kommentar an der Bedingung"
  - "Die Digest-Vorschau hängt keinen Marker an und läuft trotzdem noch einmal durch marks.without_marks: derselbe Schutz an der Grenze, an der der Text dieses Modul verlässt"
  - "Auch die Kappung der Konversationsliste in der Tool-Schicht (truncated/total) bekommt einen eigenen degraded-Satz"
  - "wire gibt weiter zwei Fakes zurück und nimmt den dritten als Parameter: kein bestehender Test musste seine Entpackung ändern"

patterns-established:
  - "Gleichzeitigkeit über drei Beine per asyncio.Barrier(3): eine sequenzielle Fassung verklemmt und fällt über das eigene wait_for"
  - "Parametrisierter Test über vier Lagen einer Quelle (Erfolg, Ausfall, fehlende App, leer) mit identischer Schlüsselmenge der Antwort ohne degraded"

requirements-completed: []  # CTX-01 braucht die Live-Messung aus 11-06, TOOL-16 die READMEs aus 11-08

# Metrics
duration: 20min
completed: 2026-08-24
---

# Phase 11 Plan 04: Das Talk-Bein, die eine Zeile von TOOL-16 und die Auszugsgrenze Summary

**`prepare_context` trägt jetzt ein drittes Bein: einen Talk-Digest aus einem Request mit eigener Zeitdecke und eigenem `degraded`-Eintrag, höchstens drei Konversationen mit Ungelesenem oder Erwähnung, Vorschau bei 200 Bytes ohne Marker; und die Auskunft über die Auflösbarkeit eines Treffers kommt nur noch aus dem Treffer selbst, während eine eigene Konstante verhindert, dass die Reichweite der Auszüge dabei still mitwächst.**

## Performance

- **Duration:** ca. 20 min
- **Started:** 2026-08-24T20:24:51Z
- **Completed:** 2026-08-24T20:41:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- `_short` entscheidet nicht mehr nach Bucket: ein Talk- und ein Tabellen-Treffer im `other`-Bucket tragen kein `resolvable`-Feld mehr, ein `url`-Treffer mit `resolvable=False` trägt es weiter. TOOL-16 wirkt damit auch im Bündel.
- `EXCERPT_KINDS` ist eine eigene, begründete Konstante; `_excerpts` liest seine Ziele daraus, und ein Test belegt bei `detail="full"` mit auflösbarem Talk- und Tabellen-Treffer die `fetch`-Zählung 0.
- Das dritte `gather`-Bein läuft ausschließlich über `talk_tools.browse(clients, level="conversations", limit=talk_tools.MAX_CONVERSATIONS)`, also über das ganze `clients`-Objekt: das Modul-Gate `test_this_module_reads_no_content_of_its_own` bleibt grün und die Marker-Hygiene der Tool-Schicht wird geerbt statt nachgebaut.
- Die Doppelfehler-Regel ist unangetastet und ihre Absicht steht als Kommentar an der Bedingung; zwei Tests belegen beide Richtungen.
- Die zwei Bedeutungen einer leeren `talk`-Liste sind auseinandergehalten: ohne `degraded`-Eintrag heißt sie "nichts Ungelesenes", mit Eintrag "konnte nicht gelesen werden".
- 51 Tests in `tests/unit/test_tools_context.py`, davon 14 neue Funktionen (eine parametrisiert über vier Lagen) rund um den Digest und vier rund um TOOL-16 und die Auszugsgrenze.

## Task Commits

1. **Task 1: Die eine Zeile von TOOL-16 und die Auszugsgrenze** - `7f2f8d3` (feat)
2. **Task 2: Das Talk-Bein: ein Request, eigenes Budget, eigene Degradation** - `49e7a1b` (feat)
3. **Task 3: Unit-Abdeckung des Talk-Beins, alle Pfade** - `de08c94` (test)

## Files Created/Modified

- `src/mcp_connector/tools/context.py` - drei neue Konstanten mit `#:`-Begründung, `EXCERPT_KINDS`, das Bein `_talk`, die Auswertungskette `_digest`/`_waiting`/`_urgency`/`_digest_entry`/`_preview`/`_count`, der neue Antwortschlüssel `talk`, die reduzierte Zeile in `_short`, drei neue Absätze im Modul-Docstring.
- `tests/unit/test_tools_context.py` - `TALK_HIT` als auflösbarer Message-Treffer, neu `TABLE_HIT` und `URL_HIT`, die Fake-Bausteine `conversation()` und `talk_answer()`, `wire` mit drittem Parameter, 18 neue Testfunktionen, die Gleichzeitigkeit auf drei Beine erweitert.

## Die endgültigen Werte und Namen (für 11-05, 11-06 und 11-08)

**Die vier Konstanten:**

| Name | Wert | Einheit und Art |
|---|---|---|
| `TALK_BUDGET` | `5.0` | Sekunden, ausdrücklich eine **Setzung**; Plan 11-06 prüft sie gegen die Live-Messung und trägt dann die Messzeile nach |
| `MAX_DIGEST` | `3` | Konversationen, die Zahl aus CTX-01 |
| `DIGEST_PREVIEW_BYTES` | `200` | **Bytes**, nicht Zeichen (Pitfall 6); deshalb heißt die Konstante `..._BYTES` |
| `EXCERPT_KINDS` | `("file", "note", "card")` | Kinds, aus denen `detail="full"` ungefragt liest; `message`, `table` und `mail` stehen nicht darin |

`KIND_BUCKETS` ist unverändert `("file", "note", "card")`, `BUCKETS` unverändert vier Namen.

**Der neue Top-Level-Schlüssel der Antwort:**

```
{"query", "window": {"start", "end"}, "events", "results", "talk", ["degraded"], "note"}
```

`talk` steht hinter `results` und ist **immer** eine Liste, auch bei Ausfall, fehlender App und ohne Ungelesenes.

**Die vollständige Feldliste eines Digest-Eintrags:**

```
token, name, unread, unread_mention [, last_message]
```

`last_message` erscheint nur, wenn die Konversation eine Vorschau trägt. `unread_mention_direct` und `last_activity` sind Sortierkriterien und **keine** Felder der Antwort; `type`, `read_only`, `can_send`, `url` und `mention_permissions` der Tool-Schicht fallen weg.

**Die Sortierregel:** absteigend nach `(unread_mention_direct, unread_mention, last_activity)`. Eine direkte Erwähnung verschwindet damit nicht hinter einer lauten Gruppe.

**Der Filter:** `unread > 0` **oder** `unread_mention` **oder** `unread_mention_direct`. Eine Erwähnung ohne Ungelesenes zählt mit.

**Die drei `degraded`-Sätze des Talk-Beins** (alle mit `"source": "talk"`):

```
The talk did not answer within 5 seconds.          (Timeout, {budget:g} aus _reason)
The talk could not be reached.                     (RequestError)
<die Meldung des ToolError wörtlich>               (z. B. "The Talk app is not available on this Nextcloud.")
Only the first 3 of {found} conversations with something unread are listed.
Only the first {read} of {total} conversations of this account were read.
```

Die ersten drei sind der Ausfallzweig (`_reason(outcome, "talk", TALK_BUDGET)`), der vierte die eigene Kappung, der fünfte die durchgereichte Kappung der Tool-Schicht. Plan 11-05 kopiert für Mail dieselben fünf Formen mit `"source": "mail"`.

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei mit Folgen für spätere Pläne:

1. **`talk` ist immer da und immer eine Liste.** Ein Schlüssel, der nur manchmal erscheint, hängt an fremdem Text, und genau das prüft `test_an_injected_instruction_arrives_as_data_and_moves_no_key_of_the_answer` über zwei Läufe. Plan 11-05 muss `mail` genauso bauen, sonst hat das Bündel zwei Vertragsarten.
2. **Bytes statt Zeichen, mit Namen.** `DIGEST_PREVIEW_BYTES` weicht bewusst vom Wortlaut "~200 Zeichen" ab. Plan 11-08 sollte in den READMEs von einer Vorschau "von etwa 200 Bytes" sprechen und nicht von Zeichen.
3. **Das Bein ist keine Auszugsquelle.** `EXCERPT_KINDS` und der Digest sind zwei getrennte Reichweiten, und der Test mit `fetch`-Zählung 0 hält beide fest.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Antwortform von `talk_browse(level="conversations")` heißt `results`, nicht `conversations`**
- **Found during:** Task 2
- **Issue:** Der `<interfaces>`-Block des Plans nennt "Envelope mit `conversations`". Im Repo baut `talk._conversations` die Antwort über `_envelope("conversations", ...)`, und die ist `{"level", "count", "results"[, "truncated", "total"]}`. Ein Digest, der `conversations` liest, wäre still immer leer geblieben.
- **Fix:** `_digest` liest `results`; `talk_answer()` in den Tests baut genau diese Form, damit die Fakes nicht von der Wirklichkeit abweichen.
- **Files modified:** src/mcp_connector/tools/context.py, tests/unit/test_tools_context.py
- **Verification:** `test_the_digest_lists_what_is_waiting_in_the_order_of_the_sort_rule` liefert drei Einträge
- **Committed in:** `49e7a1b`

**2. [Rule 2 - Missing Critical] Die Kappung der Konversationsliste selbst war still**
- **Found during:** Task 3
- **Issue:** `talk_tools` liest höchstens `MAX_CONVERSATIONS = 50` Konversationen und meldet den Schnitt über `truncated` plus `total`. `_digest` hätte daraus "die ersten 3 von 50" gemacht, obwohl die Erwähnung in den 40 ungelesenen dahinter stehen kann. Pattern 3 der Recherche verlangt für jede Kappung einen eigenen Satz, und `_schedule` macht es für den Kalender genauso.
- **Fix:** Ein zweiter `degraded`-Satz im Erfolgszweig: `Only the first {read} of {total} conversations of this account were read.`
- **Files modified:** src/mcp_connector/tools/context.py
- **Verification:** `test_a_cut_of_the_conversation_list_itself_is_named_as_well`
- **Committed in:** `de08c94`

**3. [Rule 2 - Missing Critical] Die Digest-Vorschau filtert die Marker an ihrer eigenen Grenze**
- **Found during:** Task 3
- **Issue:** Der Plan verlangt einen Test, der an der Bündelgrenze festhält, dass kein fremder Marker weitergereicht wird (T-11-23). Die Filterung passiert heute in `talk_tools`, also wäre die Eigenschaft an dieser Grenze unbelegt und eine spätere zweite Quelle für den Digest könnte sie unbemerkt verlieren.
- **Fix:** `_preview` ruft `marks.without_marks` vor der Messung, genau wie `_capped` es für die Auszüge tut. Idempotent, kein zweiter Marker, und die Byte-Decke gilt für das, was wirklich herausgeht.
- **Files modified:** src/mcp_connector/tools/context.py
- **Verification:** `test_the_digest_passes_no_marker_of_this_server_on`
- **Committed in:** `de08c94`

**4. [Rule 1 - Bug] Die im Plan verlangte Behauptung "identische `set(result)` über alle vier Lagen" ist falsch**
- **Found during:** Task 3
- **Issue:** `degraded` erscheint nur, wenn etwas ausgefallen ist ("nothing failed, so the key costs no bytes", Vertrag seit Plan 04-02). Über Erfolg, Ausfall, fehlende App und leer ist `set(result)` also nicht identisch.
- **Fix:** Der parametrisierte Test behauptet `set(result) - {"degraded"} == ANSWER_KEYS` und zusätzlich, dass `talk` in allen vier Lagen vorhanden und eine Liste ist. Damit ist die eigentliche Aussage geprüft, ohne den älteren Vertrag zu brechen.
- **Files modified:** tests/unit/test_tools_context.py
- **Verification:** `test_the_talk_key_is_there_and_a_list_in_every_situation` mit vier Parametern
- **Committed in:** `de08c94`

**5. [Rule 3 - Blocking] `wire` gibt zwei Fakes zurück statt drei**
- **Found during:** Task 2
- **Issue:** Ein drittes Rückgabeelement hätte die Entpackung in acht bestehenden Tests geändert, ohne eine Aussage zu verbessern.
- **Fix:** `wire` nimmt den dritten Parameter mit gültigem Default und verdrahtet ihn, gibt aber weiter `(search, calendar)` zurück; Tests, die den Talk-Fake befragen, übergeben ihn selbst, wie es `wire_fetch` in derselben Datei schon vormacht. Der Grund steht im Docstring von `wire`.
- **Files modified:** tests/unit/test_tools_context.py
- **Verification:** kein bestehender Test inhaltlich geändert; `uv run pytest -q` grün
- **Committed in:** `49e7a1b`

**6. [Rule 3 - Blocking] Die Test-Bausteine mussten in den Commit von Task 2**
- **Found during:** Task 2
- **Issue:** Task 2 verlangt `uv run pytest -q` grün. Ohne verdrahteten Talk-Fake liefen zehn bestehende Tests gegen das Netz und bekamen einen `degraded`-Eintrag.
- **Fix:** `conversation()`, `talk_answer()` und der dritte `wire`-Parameter liegen im Commit von Task 2, die zwölf Testfälle wie geplant in Task 3.
- **Files modified:** tests/unit/test_tools_context.py
- **Verification:** `uv run pytest -q` nach Task 2 grün
- **Committed in:** `49e7a1b`

**7. [Rule 3 - Blocking] Zwei Verifikationsschnipsel des Plans passen nicht zum Formatierer**
- **Found during:** Task 3
- **Issue:** Der Schnipsel sucht `'talk'` in einfachen Anführungszeichen; `ruff format` schreibt String-Literale in doppelten. Zusätzlich verlangt er `body.count('TALK_BUDGET') >= 2`, und der geplante Testblock nannte die Konstante nur einmal.
- **Fix:** Der Schnipsel wurde beim Ausführen auf `"talk"` umgestellt, und es kam ein Test `test_the_three_numbers_of_the_digest_are_the_ones_ctx_01_asks_for` dazu, der die drei Zahlen und das Verhältnis zu `CALENDAR_BUDGET` behauptet. Der Testblock ist damit vollständiger als geplant, nicht angepasster.
- **Files modified:** tests/unit/test_tools_context.py
- **Verification:** der Schnipsel läuft grün, `talk leg tests present`
- **Committed in:** `de08c94`

**8. [Rule 3 - Blocking] Ein Satz von Task 1 nimmt den Digest von Task 2 vorweg**
- **Found during:** Task 1
- **Issue:** Die Begründung, warum `KIND_BUCKETS` bei drei Kinds bleibt, ist der Digest, und der entsteht erst in Task 2. Der Plan verlangt den Satz aber in Task 1.
- **Fix:** Der Absatz steht wie verlangt im Modul-Docstring von Task 1 und ist ab Commit `49e7a1b` in derselben Stunde wörtlich wahr. Aufteilen hätte die Begründung in zwei Hälften zerlegt, die einzeln nichts erklären.
- **Files modified:** src/mcp_connector/tools/context.py
- **Committed in:** `7f2f8d3`

**9. [Rule 1 - Bug] `test_both_sources_run_at_the_same_time` behauptete etwas Falsches**
- **Found during:** Task 3
- **Issue:** Der Name und der Docstring sprechen von zwei Quellen, und der Test hätte das dritte Bein ungeprüft gegen das Netz laufen lassen.
- **Fix:** Umbenannt in `test_all_three_sources_run_at_the_same_time`, Barrier über drei Beine, und die Antwort wird an allen drei Stellen behauptet, samt leerem `degraded`.
- **Files modified:** tests/unit/test_tools_context.py
- **Verification:** eine sequenzielle Fassung verklemmt am Barrier und fällt über das eigene `wait_for`
- **Committed in:** `de08c94`

---

**Total deviations:** 9 auto-fixed (5 blocking, 2 missing critical, 2 bugs)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 hätte einen immer leeren Digest ergeben, 2 und 3 schließen zwei stille Stellen, 4 und 9 korrigieren zwei Testbehauptungen, die nicht zutreffen konnten, 5 bis 8 sind Reihenfolge und Formulierung.

## Issues Encountered

- Der Plan nennt `_excerpts` mit `results[name]`. Da `EXCERPT_KINDS` jetzt eine eigene Liste ist, greift die Zeile auf `results.get(name, [])` zurück: ein Kind, das später in `EXCERPT_KINDS` steht, aber keinen Bucket hat, wäre sonst ein `KeyError` mitten in einer Antwort statt einer leeren Zielliste.

## Verification Results

| Prüfung | Ergebnis |
|---|---|
| `uv run pytest -q` | grün (gesamte Default-Auswahl) |
| `uv run pytest tests/unit/test_tools_context.py -q` | grün, 51 Tests |
| `uv run pytest tests/contract -q` | grün, 65 Tests: `prepare_context` hat weiterhin genau `query` und `detail`, kein `$defs`, "third parties" steht in der Beschreibung |
| `uv run ruff check .` / `format --check .` | grün, 196 Dateien |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün, kein neuer Whitelist-Eintrag (der Parameter `bucket` ist entfernt, nicht unterstrichen) |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15736 Bytes, 21 Werkzeuge, Budget 18500 (unverändert: keine `Field`- und keine Werkzeugbeschreibung angefasst) |
| Quelltext-Gate `_short` | `OTHER_BUCKET` steht nicht mehr im ausführbaren Teil |
| Quelltext-Gate `context.py` | kein `AsyncClient`, `clients.client`, `clients.creds`, kein OCS- und kein DAV-Präfix; `asyncio.timeout(TALK_BUDGET)` vorhanden; `CHARS` kommt nicht vor |
| `git diff --stat 032e6e2..HEAD` | genau zwei Dateien: `tools/context.py` und `tests/unit/test_tools_context.py` |

## Known Stubs

Keine. Die zwei bewusst offenen Punkte gehören dem Phasenplan und nicht diesem Code: `TALK_BUDGET` ist eine Setzung, die Plan 11-06 gegen die Live-Messung prüft (der Kommentar sagt es selbst), und die Werkzeugbeschreibung von `prepare_context` nennt Talk noch nicht, weil sie in Plan 11-05 zusammen mit Mail und der Budget-Rechnung angefasst wird (Pitfall 3).

## Threat Flags

Keine neue Angriffsfläche außerhalb des Threat-Models des Plans. Die sieben `mitigate`-Dispositionen sind je durch Code und Test abgedeckt: T-11-22 (Digest ausschließlich über `talk_tools.browse`, plus die Filterung an der Bündelgrenze), T-11-23 (kein eigener Marker, fremder entfernt), T-11-24 (`EXCERPT_KINDS`, `fetch`-Zählung 0), T-11-25 (eigene Decke je Bein, Test mit herabgesetztem Budget), T-11-26 (Doppelfehler-Regel wörtlich, zwei Tests), T-11-27 (leere Liste mit und ohne Eintrag, zwei Tests), T-11-28 (Modul-Gate grün). T-11-SC ist trivial erfüllt: `pyproject.toml` und `uv.lock` sind unangetastet, es gab keinen Installationsbefehl.

## User Setup Required

Keine. Keine neue Abhängigkeit, keine neue Umgebungsvariable, kein Werkzeug mehr, keine geänderte Werkzeugbeschreibung.

## Next Phase Readiness

- **Bereit für Plan 11-05:** Bein, Auswertungsfunktion, Kappungssätze und der Vertrag "der Schlüssel ist immer da und immer eine Liste" stehen oben wörtlich zum Kopieren. Das `gather` hat drei Beine und braucht für Mail nur ein viertes; die Doppelfehler-Bedingung bleibt dabei unangetastet.
- **Bereit für Plan 11-06:** Die drei Zahlen und die Requestbehauptung ("genau ein `talk_tools.browse`-Aufruf pro Bündel, `level="conversations"`, `limit=MAX_CONVERSATIONS`") sind als Unit-Vertrag festgenagelt; die Live-Messung muss nur noch dagegenhalten.
- **Bereit für Plan 11-08:** Die Antwortform samt neuem Schlüssel und Feldliste steht oben; Vorschau in **Bytes** benennen, nicht in Zeichen.
- **Offen und bewusst offen:** `CTX-01` und `TOOL-16` bleiben `Pending`. CTX-01 verlangt "das bestehende Verhalten bleibt **gemessen** unverändert" (Plan 11-06), TOOL-16 verlangt die drei READMEs (Plan 11-08).

## Self-Check: PASSED

Beide geänderten Dateien liegen auf der Platte, alle drei Commits (`7f2f8d3`, `49e7a1b`, `de08c94`) stehen im Log, und der Arbeitsbaum war vor diesem Dokument sauber.

---
*Phase: 11-b-ndelung-budget-und-release-0-1-6*
*Completed: 2026-08-24*
</content>
</invoke>
