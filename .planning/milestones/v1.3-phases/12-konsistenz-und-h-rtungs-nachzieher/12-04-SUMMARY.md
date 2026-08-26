---
phase: 12-konsistenz-und-h-rtungs-nachzieher
plan: 04
subsystem: tools
tags: [talk, chatgpt, module-boundary, ast-gate, provider-map, readme, pytest, ruff, pyright]

# Dependency graph
requires:
  - phase: 11-review-und-security
    provides: "one_message als Präzedenzfall für eine öffentliche Funktion mit dem Aufrufer im Docstring; die Mitigation von T-09-21 im Docstring von _room; IN-06 als Namensvorschlag"
  - phase: 12-konsistenz-und-h-rtungs-nachzieher
    provides: "12-01 hat tools/talk.py und tools/chatgpt.py bereits angefasst (message_truncated); 12-02 hat provider_map.py angefasst; 12-03 hat das Byte-Muster für Gegenproben auf echten Dateien etabliert"
provides:
  - "talk.one_room: öffentliche Schnittstelle mit dem Aufrufer und der T-09-21-Begründung im Docstring"
  - "tests/contract/test_module_boundaries.py: AST-Gate gegen Privat-Durchgriffe zwischen Tool-Modulen, mit drei Gegenproben und einer Dateilisten-Behauptung"
  - "Halter über die Provider-Ids der drei READMEs: PROVIDER_KINDS plus REAL_BUT_UNREGISTERED, mit Gegenprobe"
  - "README-Beispiel für einen unbekannten Suchprovider mit talk-conversations statt spreed"
affects: [13-release-und-store, changelog-0.1.9, neue-tool-module]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AST-Gate statt Text-Gate, wenn die Regel über Quelltext läuft und erklärende Prosa dieselben Namen nennt"
    - "Alias-Auflösung aus den Import-Knoten der geprüften Datei, statt einer Namensliste im Gate"
    - "Öffentliche Funktion trägt ihren Aufrufer und den Grund für die Sichtbarkeit im Docstring"
    - "Benannte Liste echter, absichtlich nicht registrierter Ids lebt im Test, nicht im Produktionsmodul"

key-files:
  created:
    - tests/contract/test_module_boundaries.py
  modified:
    - src/mcp_connector/tools/talk.py
    - src/mcp_connector/tools/chatgpt.py
    - tests/unit/test_provider_map.py
    - README.md
    - README.de.md
    - README.fr.md

key-decisions:
  - "Der öffentliche Name ist one_room und nicht room_of (IN-06): das Modul hat mit one_message schon eine Konvention für \"genau ein Objekt aus einer gelesenen Menge\", und ein zweiter Namensstil im gleichen Modul wäre eine Konvention mit zwei Formen. room_of ist vertretbar, aber nicht konsistent."
  - "AST-Gate in tests/contract/ statt ruff --select SLF, und die Messung dazu steht im Modul-Docstring des Gates: SLF findet drei Treffer in src/ (zwei legitime Klassen-Interna in oauth/provider.py) und 53 in tests/, kostet also zwei noqa-Zeilen plus per-file-ignores und prüft eine andere Aussage als das Requirement."
  - "Das Gate läuft über alle .py unter src/mcp_connector, nicht nur über tools/: ein Durchgriff aus server/ oder oauth/ auf ein Tool-Internum wäre derselbe Bruch."
  - "REAL_BUT_UNREGISTERED steht in tests/unit/test_provider_map.py und nicht in provider_map.py: das Produktionsmodul führt eine Übersetzungstabelle und keine Liste der Ids, die es nicht übersetzt, und sein Modul-Docstring erklärt die Abwesenheit von talk-conversations bereits in Prosa."
  - "Die Umbenennung ist eine rein interne Änderung und gehört NICHT in den Changelog von 0.1.9: kein Werkzeugname, kein Antwortschlüssel, keine Id-Form ändert sich, tools/list bleibt bei 15711 Bytes und 21 Werkzeugen. Die README-Korrektur gehört als Doku-Korrektur hinein."

patterns-established:
  - "Geteilte Prüffunktion nimmt Text und Dateinamen als Parameter (_reaches(source, relative), provider_ids(text, name)); das Gate liest die echte Datei, die Gegenprobe füttert einen konstruierten String"
  - "Eine einzige Behauptung über \"genau ein Fund\" belegt beide Hälften: das Gate findet den Aufruf, und es findet die zwei Prosa-Nennungen daneben nicht"
  - "Eine echte Datei des Baums ist die ehrliche Fixture für einen Filter (tools/context.py nennt vier fremde Privatnamen in Prosa)"
  - "Gegenproben auf echten Dateien lesen und schreiben Bytes (read_bytes/write_bytes), sonst dreht der Python-Roundtrip auf diesem Windows-Host die Zeilenenden"

requirements-completed: [TOOL-19]

# Metrics
duration: 18min
completed: 2026-08-25
---

# Phase 12 Plan 04: Konsistenz und Härtungs-Nachzieher Summary

**Der letzte Privat-Durchgriff im Produktionsbaum ist eine öffentliche Schnittstelle mit ihrer Sicherheitsbegründung, die Modulgrenze zwischen den Tool-Familien ist ein AST-Gate mit drei Gegenproben statt einer Absprache, und das README-Beispiel für einen unbekannten Suchprovider nennt in allen drei Sprachen eine Id, die es wirklich gibt.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-08-25T13:05:03Z
- **Completed:** 2026-08-25T13:23:00Z
- **Tasks:** 3
- **Files modified:** 7 (344 Zugänge, 8 Abgänge, keine Datei gelöscht)

## Accomplishments

- `talk._room` heißt `talk.one_room`, ist öffentlich, und der T-09-21-Absatz steht wörtlich an seinem neuen Platz: derselbe Satz über `GET /room/{token}`, den gezählten Brute-Force-Versuch gegen die Adresse dieses Containers, die 429 und den einen Request, den die Liste kostet. Davor steht ein neuer Absatz, der den Aufrufer und den Grund für die Sichtbarkeit nennt.
- `tools/chatgpt.py` ruft die öffentliche Schnittstelle. Damit stehen die zwei Aufrufe in `_fetch_message` im gleichen Stil, und `talk_tools.one_message` zwei Zeilen weiter ist nicht mehr das Zielmuster, sondern der Nachbar.
- `uv run --no-sync ruff check --select SLF src/` meldet genau noch die zwei Treffer in `oauth/provider.py` (`view._also`, `self._provider._now()`), beide eigene Klassen-Interna. Kein Treffer in `tools/` mehr, also kein Durchgriff über eine Modulgrenze im ganzen Produktionsbaum.
- Das neue Gate war einmal rot: der Lauf gegen ein manipuliertes `tools/chatgpt.py` meldet `tools/chatgpt.py:616: talk_tools._room`, mit Datei, Zeile und Ausdruck.
- Das Gate bleibt grün, obwohl `tools/context.py` vier private Fremdfunktionen in Prosa nennt. Kein erklärender Satz musste gekürzt werden.
- Die drei READMEs nennen `talk-conversations`, und `"kind":"url"` sowie `"resolvable":false` daneben sind damit wahr statt erfunden, belegt durch `test_a_talk_conversation_hit_stays_a_url_because_a_conversation_is_no_document`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Aus `_room` wird `one_room`, die Sicherheitsbegründung wandert wörtlich mit** - `e4d0a28` (refactor)
2. **Task 2: AST-Gate über die Modulgrenze, einmal rot gesehen** - `7585756` (test)
3. **Task 3: README-Beispiel mit echter Provider-Id plus Halter mit Gegenprobe** - `bce640d` (docs)

## Der SLF-Messwert vor und nach der Umbenennung

Die Begründung für die Bauform des Gates ist eine Messung und keine Vermutung, und sie ist jetzt zweimal genommen:

| Lauf | `src/` | davon Durchgriffe über eine Modulgrenze | `tests/` |
|------|--------|------------------------------------------|----------|
| vor der Umbenennung (12-RESEARCH, 2026-08-25) | 3 | 1 (`tools/chatgpt.py:616`) | 53 (alle legitime Quelltext-Gates) |
| nach der Umbenennung (dieser Plan) | 2 | 0 | unverändert |

Die zwei verbleibenden Treffer sind `oauth/provider.py:554` (`view._also` nach `copy.copy(self)`) und `oauth/provider.py:1544` (`self._provider._now()`), beide Zugriffe auf eigene Klassen-Interna. Damit ist die Vollständigkeit belegt: es gab genau einen Durchgriff über eine Modulgrenze, und es gibt keinen mehr. Die Messung steht im Modul-Docstring des Gates, damit die nächste Änderung ihren Grund lesen kann, statt `SLF` erneut vorzuschlagen.

## Warum die Umbenennung nicht in den Changelog gehört

Sie ist rein intern. Kein Werkzeugname ändert sich, kein Antwortschlüssel, keine Id-Form, kein Parameter. `scripts/check_tool_budget.py` liest nach dem Umbau exakt dieselben Zahlen wie nach 12-01: **15711 Bytes, 21 Werkzeuge, Budget 18000**, `talk_browse` bei 912 Bytes. Der Changelog von 0.1.9 beschreibt, was ein Nutzer merkt; hier merkt niemand etwas außer jemandem, der das Modul liest.

Die README-Korrektur gehört dagegen hinein, als Doku-Korrektur: das Beispiel für `unified_search` nannte drei Releases lang eine Provider-Id, die es nicht gibt. Übergabe an Phase 13 unten.

## Files Created/Modified

- `src/mcp_connector/tools/talk.py` — `_room` heißt `one_room`; ein neuer Absatz im Docstring nennt `tools/chatgpt.py`, `fetch`, TOOL-19 und das neue Gate als Halter der Grenze; die zwei modulinternen Aufrufstellen (in `send`, in `_messages`) und die Prosa-Nennung im Docstring von `send` (`in :func:`one_room``) ziehen mit. Signatur Zeichen für Zeichen unverändert, `include_last_message` weiter keyword-only.
- `src/mcp_connector/tools/chatgpt.py` — eine Zeile: `talk_tools.one_room(...)` statt `talk_tools._room(...)`. Importblock unverändert.
- `tests/contract/test_module_boundaries.py` — **neu**, 260 Zeilen. Modul-Docstring mit der `SLF`-Messung, `_source_files`, `_tool_modules`, `_dotted`, `_package_of`, `_base_of`, `_aliases`, `_is_private`, `_reaches(source, relative)` und fünf Tests.
- `tests/unit/test_provider_map.py` — `READMES`, `REAL_BUT_UNREGISTERED`, `_PROVIDER_IN_JSON`, `provider_ids(text, name)` und zwei Tests. Alle bestehenden Tests unverändert, insbesondere der eingefrorene Mengen-Halter `test_the_provider_table_is_not_a_list_of_installed_apps`.
- `README.md`, `README.de.md`, `README.fr.md` — je eine Zeichenkette in der Beispielzeile: `"provider":"spreed"` zu `"provider":"talk-conversations"`. `"kind":"url"`, `"resolvable":false`, der URL-Teil `/index.php/call/abc123` und die umgebende Prosa mit Umlauten und Akzenten sind unberührt.

## Decisions Made

- **Name: `one_room`.** Festgelegt im Plan, hier nur die Begründung fürs Protokoll: `one_message` steht im gleichen Modul und bedeutet "genau ein Objekt aus einer gelesenen Menge". `room_of` aus `11-REVIEW.md` IN-06 ist ein guter Name, aber er hätte im selben Modul einen zweiten Stil eingeführt, und eine Konvention mit zwei Formen ist keine.
- **Der neue Absatz steht vor dem alten, nicht dahinter.** Ein Docstring beginnt mit der Zusammenfassungszeile; direkt danach ist der Platz für die Frage, warum diese Funktion überhaupt öffentlich ist, und der T-09-21-Absatz bleibt als Block zusammen. Der zitierte Text ist damit wörtlich erhalten, nur nicht mehr der erste Absatz.
- **AST statt Grep, und AST statt `ruff --select SLF`.** Siehe Messtabelle oben. Der entscheidende Punkt gegen Grep ist nicht Eleganz: die vier Prosa-Nennungen in `tools/context.py` hätten ein Text-Gate sofort rot gemacht, und die naheliegende Reparatur wäre, die erklärenden Sätze zu löschen. Genau diese Datei ist deshalb die zweite Gegenprobe.
- **Fünf Tests statt drei.** Der Plan verlangt Gate, zwei Gegenproben und eine Dateilisten-Behauptung. Dazu kommt ein fünfter Test über die Import-Formen, siehe Deviations.
- **`REAL_BUT_UNREGISTERED` ist heute eine Menge mit einem Element**, und das ist kein Provisorium: die Liste soll klein bleiben, denn jeder Zugang ist die Behauptung "diese Id existiert wirklich und fehlt in der Tabelle mit Absicht". Für `talk-conversations` steht diese Behauptung schon in zwei bestehenden Tests und im Modul-Docstring von `provider_map.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Ein fünfter Test über die fünf Import-Formen**

- **Found during:** Task 2
- **Issue:** Das Gate löst Import-Aliase auf, und der Plan verlangt, dass alle im Baum vorkommenden Formen behandelt sind. Belegt hätte das nichts: die Gegenprobe mit konstruierter Quelle benutzt genau **eine** Form (`from . import talk as talk_tools`). Ein Gate, das nur diese eine Form kennt, wäre über alle fünf Tests grün und würde `from ..tools import talk as talk_tools` in `server/reg_talk.py` stillschweigend übersehen. Ohne Halter wäre die Auflösung Code ohne Beweis, und der einzige Durchgriff, den es je gab, stand ausgerechnet in der Form, die getestet ist.
- **Fix:** `test_every_import_form_in_the_tree_is_resolved` speist derselben Prüffunktion fünf konstruierte Quellen, eine pro Form (`from . import x as y`, `from . import x`, `from ..tools import x as y`, `from mcp_connector.tools import x as y`, `import mcp_connector.tools.x as y`), und verlangt je genau einen Fund mit Zeilennummer. Der gleiche Test hält die Gegenrichtung fest: dieselbe Zeile innerhalb von `tools/talk.py` selbst ergibt null Funde, denn ein Modul, das in seine eigenen Interna greift, ist der Normalfall und der Grund, aus dem der Unterstrich existiert.
- **Files modified:** `tests/contract/test_module_boundaries.py`
- **Verification:** `uv run --no-sync pytest tests/contract/test_module_boundaries.py -q` grün mit 5 Tests; der Gegenprobenlauf gegen das manipulierte `tools/chatgpt.py` bleibt rot.
- **Committed in:** `7585756` (Task-2-Commit)

**2. [Rule 3 - Blocking] Der Gegenprobenlauf des Plans schreibt Text, wo er Bytes schreiben muss**

- **Found during:** Task 2
- **Issue:** Der Verifikationsschritt des Plans manipuliert `src/mcp_connector/tools/chatgpt.py` per `read_text`/`write_text`. Auf diesem Windows-Host (`core.autocrlf=true`, `.gitattributes` mit `* text=auto`) dreht dieser Roundtrip die Zeilenenden der ganzen Datei. Die Zusage des Plans ("`git diff --exit-code` ist danach sauber") wäre damit von der Prüfung selbst verletzt worden. Dieselbe Falle wie in 12-03, dort schon als Muster festgehalten.
- **Fix:** Der Gegenprobenlauf nutzt `read_bytes`/`write_bytes` und einen Byte-Ersatz (`b'talk_tools.one_room(' -> b'talk_tools._room('`), mit Rückschreiben im `finally` und einem Byte-Vergleich danach. Die Prüflogik des Plans bleibt unverändert: Rückgabecode ungleich 0 und `chatgpt.py` in der Ausgabe.
- **Files modified:** keine (Werkzeugbedienung, nicht Repo-Inhalt)
- **Verification:** `git diff --exit-code -- src/mcp_connector/tools/chatgpt.py pyproject.toml` sauber, `git status --short` leer; der rote Lauf meldete `tools/chatgpt.py:616: talk_tools._room`.
- **Committed in:** nicht committet (keine Inhaltsänderung)

---

**Total deviations:** 2 auto-fixed (1 fehlende kritische Prüfung, 1 blockierende Werkzeugfalle)
**Impact on plan:** Keine Scope-Änderung, keine neue Datei außer der geplanten, keine Paketinstallation. Beide Abweichungen betreffen die Beweiskraft, nicht den Umfang.

## Issues Encountered

- **`11-SECURITY.md` liegt nicht mehr im Arbeitsbaum.** Der Plan verlangt, das Dokument nicht anzufassen und seine Zitate wahr zu halten. Es wurde mit `661c609` ("clear v1.2 phase directories for milestone v1.3") entfernt und lebt nur noch in der Historie. Zwei Folgen: der Verifikationsschritt `git diff --exit-code -- .planning/phases/11-b-ndelung-budget-und-release-0-1-6/` läuft gegen einen nicht existierenden Pfad und ist trivial sauber, und die Zitatstelle ist keine Docstring-Kopie, sondern eine **Namensnennung**: `T-11-14` nennt "Auflösung über die eigene Konversationsliste `talk_tools._room` (`chatgpt.py:616`)". Der Docstring wanderte trotzdem wörtlich mit, wie der Plan es fordert, und die Namensnennung im Protokoll einer abgeschlossenen Phase bleibt als historische Aussage stehen. Ein Nachziehen dort wäre eine Rückschreibung gewesen.
- **Zeilennummern des Plans sind um elf verschoben.** `_room` stand bei 626 statt 615, die Aufrufstellen bei 295 und 485 statt 291 und 481, die Prosa-Nennung bei 238 statt 234. Ursache ist 12-01, das im selben Modul den `message_truncated`-Kommentarblock eingefügt hat. Alle Fundstellen waren über den Namen eindeutig auffindbar.
- **`git status` zeigte `tools/chatgpt.py` nach dem ersten Edit mit einer LF-Warnung.** Der Arbeitsbaum trägt die Datei jetzt mit LF, `talk.py` weiter mit CRLF. Beides ist für git identisch, weil `* text=auto` beim Commit normalisiert; `git diff` ist sauber und `ruff format --check` grün.

## Verification Results

| Prüfung | Ergebnis |
|---------|----------|
| `uv run --no-sync pytest -q` | grün (voller Baum, nach jedem Task) |
| `uv run --no-sync pytest tests/contract -q` | grün |
| `uv run --no-sync pytest tests/contract/test_module_boundaries.py -q` | 5 Tests grün |
| `uv run --no-sync pytest tests/unit/test_provider_map.py -q` | 33 Tests grün |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 198 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | exit 0, ohne neuen Whitelist-Eintrag |
| `uv run --no-sync ruff check --select SLF src/` | genau 2 Treffer, beide `oauth/provider.py`, keiner in `tools/` |
| Signatur- und Docstring-Prüfung `one_room` | "one_room is public and carries its reason" (`T-09-21`, `brute force`, `429`, Aufrufer, keyword-only) |
| Aufrufer-Prüfung `chatgpt.py` | "the caller goes through the front door" |
| Gate-Bauform-Prüfung | "the gate is built the way the plan says" (`ast.Attribute`, `ImportFrom`, `SLF`, `context.py`, >=3 Tests) |
| Gegenprobe manipuliertes `tools/chatgpt.py` | rot mit `tools/chatgpt.py:616: talk_tools._room`, Baum danach byte-identisch |
| README-Provider-Prüfung | "three readmes name provider ids that exist", kein `spreed`, kein Em- oder En-Dash |
| Halter-Prüfung `test_provider_map.py` | "the holder and its counter probe exist" |
| `scripts/check_tool_budget.py` | 15711 Bytes, 21 Werkzeuge, Budget 18000; `talk_browse` 912 Bytes (unverändert gegenüber 12-01) |
| `git diff --name-only 7f9fe10..HEAD -- pyproject.toml uv.lock .github/workflows/ci.yml CHANGELOG.md appinfo/info.xml` | leer |
| `git diff --exit-code -- .planning/phases/11-b-ndelung-budget-und-release-0-1-6/` | sauber (Pfad existiert seit `661c609` nicht mehr, siehe Issues) |
| `git status --short` nach jedem Task | nur die jeweils bearbeiteten Dateien, keine Untracked-Reste |

## Known Stubs

Keine. Dieser Plan benennt eine Funktion um, fügt ein Gate hinzu und korrigiert drei Dokumentationszeilen; es entsteht kein Codepfad mit fehlender Datenquelle.

## Threat Flags

Keine neue Sicherheitsfläche: kein neuer Endpunkt, kein neuer Auth-Pfad, kein Dateizugriff, keine Schemaänderung an einer Vertrauensgrenze. Die drei Mitigationen des Threat Registers sind belegt (T-12-14 durch das rote Gate, T-12-15 durch die Docstring-Prüfung, T-12-16 durch die `context.py`-Gegenprobe, T-12-17 durch den README-Halter), und T-12-SC ist eingehalten: `pyproject.toml` und `uv.lock` sind unberührt, das Gate benutzt nur `ast` und `pathlib` aus der Standardbibliothek.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Für den Changelog von 0.1.9 (Phase 13):** genau **eine** Zeile aus diesem Plan gehört hinein, als Doku-Korrektur, etwa "the `unified_search` example in the READMEs named `spreed`, which was never a provider id; it now names `talk-conversations`". Die Umbenennung `_room` zu `one_room` gehört **nicht** hinein, Begründung im Abschnitt oben.
- Ein neues Modul unter `tools/` steht ab jetzt automatisch unter dem Gate: `_tool_modules()` liest das Verzeichnis und zählt nichts auf.
- Wer eine private Funktion eines Tool-Moduls von außen braucht, bekommt einen roten Testlauf mit Datei, Zeile und dem Hinweis, es wie `one_room` und `one_message` zu machen: öffentlich, mit dem Aufrufer und dem Grund im Docstring.
- Kommt eine echte Provider-Id in ein README, die absichtlich nicht in `PROVIDER_KINDS` steht, ist `REAL_BUT_UNREGISTERED` die eine Stelle, an der sie benannt wird. Die Fehlermeldung des Halters sagt das.
- Keine Blocker. Phase 12 ist mit diesem Plan vollständig: TOOL-17 (12-01), TOOL-18 (12-02), SEC-02 (12-03), TOOL-19 (12-04).

## Self-Check: PASSED

- `tests/contract/test_module_boundaries.py` existiert (neu).
- `src/mcp_connector/tools/talk.py`, `src/mcp_connector/tools/chatgpt.py`, `tests/unit/test_provider_map.py`, `README.md`, `README.de.md`, `README.fr.md` existieren und tragen die beschriebenen Änderungen.
- Die drei Task-Commits `e4d0a28`, `7585756` und `bce640d` sind in `git log` auffindbar.

---
*Phase: 12-konsistenz-und-h-rtungs-nachzieher*
*Completed: 2026-08-25*
