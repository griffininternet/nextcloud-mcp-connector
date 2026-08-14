---
phase: 01-server-kern
plan: 02
subsystem: api
tags: [mcp, stdio, webdav, httpx, lxml, respx, tdd, security]

# Dependency graph
requires:
  - phase: 01-01
    provides: "uv-Umgebung mit mcp 2.0.0, pytest-Harness (anyio_backend, nc_env), roter files_read-Contract-Test, Console-Script-Vertrag nc-mcp, Budget-Gate"
provides:
  - "Lauffaehiger stdio-Server nc-mcp: initialize wird beantwortet, erste stdout-Zeile ist valides JSON-RPC"
  - "mcp_connector.server: MCPServer-Objekt, READ_ONLY/CREATE_ONLY-Annotationen, compact(), graceful(), Auto-Import aller reg_*-Module"
  - "Fundament fuer alle 14 weiteren Tools: Credentials, shared_client(), configure_logging(), ToolError-Format, ID-Codec, gehaerteter XML-Parser"
  - "Read-only DAV-Client: safe_path(), PROPFIND Depth 0 (stat), GET mit Range (get_range)"
  - "files_read als erstes Tool, mit Groessen-Cap, Binaer-Ablehnung, Traversal-Guard und stateless Fortsetzung ueber next_offset"
  - "Gruener Contract-Test aus Plan 01-01 (GREEN-Gate der TDD-Kette) und gruenes Token-Budget-Gate (660 Bytes von 24000)"
affects: [01-03-files-write, 01-04-streamable-http, 01-05-bis-01-13-tools, 01-14-tool-contract, Phase-2-ExApp-Impersonation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Registrierungs-Konvention: server/reg_*.py registriert Tools beim Import, server/__init__.py laedt sie per pkgutil (keine gemeinsame Datei fuer parallele Plaene)"
    - "Tool-Logik ohne mcp-Import: freistehende async Funktionen mit einem Parameterobjekt NcClients (respx-testbar, Naht fuer AppAPI-Impersonation)"
    - "Ein httpx.AsyncClient pro Event-Loop (WeakKeyDictionary), Auth per Request via httpx.BasicAuth, follow_redirects=False"
    - "Fehlerformat message plus hint an einer Stelle, graceful() uebersetzt in ValueError mit 'from None' (keine Tracebacks mit URLs)"
    - "Stateless Fortsetzung: truncated plus next_offset als normale Antwortfelder statt Server-State"
    - "Gehaerteter XML-Parser (resolve_entities=False, no_network=True, huge_tree=False) plus DTD-Ablehnung fuer jeden DAV-Antwortkoerper"

key-files:
  created:
    - src/mcp_connector/errors.py
    - src/mcp_connector/ids.py
    - src/mcp_connector/config.py
    - src/mcp_connector/deps.py
    - src/mcp_connector/entry_stdio.py
    - src/mcp_connector/nextcloud/__init__.py
    - src/mcp_connector/nextcloud/credentials.py
    - src/mcp_connector/nextcloud/http.py
    - src/mcp_connector/nextcloud/clients/__init__.py
    - src/mcp_connector/nextcloud/clients/xml.py
    - src/mcp_connector/nextcloud/clients/dav.py
    - src/mcp_connector/tools/__init__.py
    - src/mcp_connector/tools/files.py
    - src/mcp_connector/server/__init__.py
    - src/mcp_connector/server/reg_files.py
    - tests/unit/test_ids.py
    - tests/unit/test_config.py
    - tests/unit/test_credentials_http.py
    - tests/unit/test_xml.py
    - tests/unit/test_files_read.py
    - tests/compat/test_stdio_startup.py
  modified: []

key-decisions:
  - "files_read lehnt nur oberhalb von 2 MiB komplett ab; zwischen max_bytes und 2 MiB liefert es eine markierte Teilantwort mit next_offset"
  - "reg_*-Module werden per pkgutil automatisch importiert, damit parallele Plaene keine gemeinsame Registry-Datei anfassen"
  - "parse_multistatus lehnt jede DTD im Antwortkoerper ab, nicht nur die Entity-Aufloesung"
  - "NcClients liegt in nextcloud/__init__.py, deps.resolve_clients(ctx) baut es; tools/ bleibt frei von Env- und Header-Zugriff"
  - "Nur SRV-02 wird abgehakt; SRV-03, SRV-05, TOOL-01 und AUTH-01 bleiben Pending bis Plan 04 bzw. 14"

patterns-established:
  - "TDD pro Task: test(01-02) mit rotem Lauf, danach feat(01-02) mit gruenem Lauf"
  - "Jede Guard-Ablehnung wird per respx belegt, dass kein HTTP-Request rausgeht"
  - "Kein print im Paket, Logger mcp_connector auf stderr, httpx und httpcore auf WARNING"

requirements-completed: [SRV-02]

# Metrics
duration: 18min
completed: 2026-08-14
---

# Phase 01 Plan 02: Walking Skeleton Summary

**Ende-zu-Ende-Strecke steht: nc-mcp antwortet per stdio auf initialize, files_read liest Textdateien ueber PROPFIND plus GET-Range aus der eigenen Nextcloud, und alle Guards (Traversal, Binaer, 2-MiB-Deckel, 401-ohne-Retry, XXE) sind mit 95 gruenen Tests belegt.**

## Performance

- **Duration:** ~18 min
- **Erster Task-Commit:** 2026-08-14T17:28:54+02:00
- **Letzter Task-Commit:** 2026-08-14T17:37:28+02:00
- **Tasks:** 3 von 3 (alle autonom, kein Checkpoint)
- **Files created:** 21 (15 Produktionsmodule, 6 Testdateien)

## Accomplishments

- **Der Contract-Test aus Plan 01-01 ist gruen.** Damit ist das GREEN-Gate der TDD-Kette geschlossen: `files_read` erscheint in `tools/list` mit `read_only_hint=True`, `open_world_hint=False` und `output_schema is None`. Verifiziert wurde zusaetzlich, dass `ctx` nicht im Input-Schema auftaucht und die Parameterliste genau `['path', 'offset']` ist, also kein `user`/`username`/`uid` (Confused-Deputy-Kriterium).
- **Der Server laeuft wirklich, nicht nur im Test.** `tests/compat/test_stdio_startup.py` startet das echte Console-Script `nc-mcp` als Subprozess, schickt ein JSON-RPC-`initialize` auf stdin und parst die erste stdout-Zeile. Antwort: `serverInfo.name = "MCP Connector"`, Protokoll 2025-06-18, Exit 0 beim Schliessen von stdin. Die Startmeldung landet auf stderr, die Leitung bleibt sauber (Pitfall 7).
- **Alle Pfade von files_read sind abgedeckt, nicht nur der Happy Path:** 29 Tests in `tests/unit/test_files_read.py` fuer Happy, Basic-Auth-pro-Request, Depth 0, fuenf Text-Mimetypes, Binaer-Ablehnung, Ordner-Ablehnung, Oversize, `offset` hinter dem Dateiende, `max_bytes`-Deckel, 401 (genau ein Call), 403, 404, 429, 500, Redirect, Range-Fortsetzung mit `next_offset` und sieben unsichere Pfade. Sieben Traversal-Varianten sind per respx-Call-Zaehler als "kein HTTP-Request" belegt.
- **Token-Budget ist gemessen statt behauptet:** `tools/list` ist mit einem Tool 660 Bytes gross (`files_read`: 501 Bytes) gegen ein Budget von 24000. Erste echte Datenbasis fuer die Fixierung des Budgets in Plan 01-14.
- **Sicherheitszusagen sind maschinell gepruefte Invarianten:** kein `print(` in `src/` (0 Treffer), keine destruktive DAV-Methode in `dav.py` (0 Treffer fuer delete/move/copy/proppatch ausserhalb von Kommentaren), kein `stateless_http` und kein `FastMCP` in `server/__init__.py` (0 Treffer, auch nicht im Text der Docstrings), `repr(Credentials)` ohne Secret.

## Task Commits

1. **Task 1: Fundamentmodule (RED)** - `80fd416` (test): 4 Testdateien, Lauf endet mit `ModuleNotFoundError: mcp_connector.errors`
2. **Task 1: Fundamentmodule (GREEN)** - `a0045bd` (feat): errors, credentials, http, config, deps, ids, xml; 62 Unit-Tests gruen
3. **Task 2: DAV-Client und files_read (RED)** - `877f8df` (test): `ImportError: cannot import name 'dav'`
4. **Task 2: DAV-Client und files_read (GREEN)** - `41469c8` (feat): `dav.py`, `tools/files.py`; 29 Tests gruen
5. **Task 3: Server-Registry und stdio-Entry** - `b8a27d6` (feat): `server/`, `reg_files.py`, `entry_stdio.py`, Compat-Test

**Plan metadata:** siehe letzter Commit dieses Plans (docs(01-02))

_TDD-Gate-Sequenz je Task eingehalten: `test(...)` vor `feat(...)`. Task 3 ist bewusst kein TDD-Task (der Plan markiert nur Task 1 und 2 mit `tdd="true"`), sein roter Test lag bereits als Contract-Test aus Plan 01-01 vor._

## Files Created/Modified

Produktionscode:

- `src/mcp_connector/errors.py` - `ToolError(message, hint)` plus `AppMissingError` und `ConflictError`; keine Exception traegt Credentials
- `src/mcp_connector/nextcloud/credentials.py` - `Credentials` frozen/slots mit maskiertem `__repr__` (`secret='***'`)
- `src/mcp_connector/nextcloud/http.py` - `shared_client()` (WeakKeyDictionary vom Event-Loop, Timeout 10/5/30, `follow_redirects=False`, Limits 20/10, eigener User-Agent) und `configure_logging()` (Paket-Logger auf stderr, `propagate=False`, httpx und httpcore auf WARNING)
- `src/mcp_connector/nextcloud/__init__.py` - `NcClients(client, creds)` als einziges Parameterobjekt der Tool-Funktionen
- `src/mcp_connector/config.py` - `NC_MCP_URL`/`NC_MCP_USER`/`NC_MCP_APP_PASSWORD`, `normalize_base_url()`, `REDIRECT_HINT`; `NC_MCP_ALLOWED_HOSTS` und `NC_MCP_STATIC_BEARER` nur als Namen reserviert
- `src/mcp_connector/deps.py` - `resolve_credentials(ctx)` und `resolve_clients(ctx)`; Signatur nimmt bereits `ctx`, damit Plan 04 die Header-Modi ohne Tool-Aenderung ergaenzt
- `src/mcp_connector/ids.py` - Praefix-Codec `file:`/`note:`/`card:`/`event:`/`url:` mit Kurzform `card:<cardId>` und `ToolError` bei jedem Fehlformat
- `src/mcp_connector/nextcloud/clients/xml.py` - Namespace-Konstanten, `hardened_parser()`, `parse_multistatus()` (nur 2xx-Propstats, Collection-Erkennung, DTD-Ablehnung)
- `src/mcp_connector/nextcloud/clients/dav.py` - `safe_path()`, `files_url()` (quote mit `safe="/"`), `stat()` (PROPFIND Depth 0, Body per lxml), `get_range()` (GET mit optionalem Range, akzeptiert 200 und 206), `_check()` als einzige Statusuebersetzung
- `src/mcp_connector/tools/files.py` - `read()` mit Guard-Reihenfolge Pfad, Ordner, Mimetype, Groesse, danach Range-Lesen; Antwortfelder `path`, `content`, `size`, `content_type`, `truncated` und `next_offset` nur bei `truncated`
- `src/mcp_connector/server/__init__.py` - `mcp = MCPServer(...)`, `READ_ONLY`, `CREATE_ONLY`, `compact()`, `graceful()`, `_load_registrations()`
- `src/mcp_connector/server/reg_files.py` - `files_read` als `@mcp.tool(annotations=READ_ONLY, structured_output=False)` plus `@graceful`
- `src/mcp_connector/entry_stdio.py` - `main()`: `configure_logging()`, frueher Credential-Check mit Exit-Code 2 und Meldung auf stderr, dann `mcp.run()` ohne Argument

Tests:

- `tests/unit/test_credentials_http.py` - Maskierung in repr/str/format, Client-Wiederverwendung pro Loop, Loop-Trennung, Ersatz nach `aclose()`, Logging-Haertung, `resolve_credentials` ohne Nutzer-Override
- `tests/unit/test_config.py` - fehlende und leere Variablen (Name im Text), Trailing-Slash, Subpath, sechs ungueltige URLs
- `tests/unit/test_ids.py` - Roundtrip fuer alle fuenf Arten, Kurzform, elf Fehlformate, Separator-Schutz
- `tests/unit/test_xml.py` - Parser-Flags, XXE-Probe, Billion Laughs, DTD, defektes XML, falsches Root-Element, Propstat-Filter
- `tests/unit/test_files_read.py` - 29 Tests ueber alle Pfade von `files_read` und den DAV-Helfern
- `tests/compat/test_stdio_startup.py` - drei `matrix`-Tests gegen das echte Console-Script

## Decisions Made

- **Groessen-Deckel: Ablehnung erst ab 2 MiB, darunter markierte Teilantwort.** Der Plan verlangt beides: eine Ablehnung fuer zu grosse Dateien mit Hinweis auf `offset` und eine Fortsetzung ueber `next_offset`. Umgesetzt als: `size > 2 MiB` bei `offset=0` wird abgelehnt (Hinweis nennt `offset` und `max_bytes`), `max_bytes < size <= 2 MiB` liefert eine als `truncated` markierte Teilantwort mit `next_offset`, `max_bytes > 2 MiB` ist ein Parameterfehler. Grund: eine harte Ablehnung bereits ab 512 KiB wuerde jede groessere Textdatei unlesbar machen, obwohl die Truncation-Markierung den Client-Kontext genauso wirksam schuetzt (T-01-13).
- **`parse_multistatus` lehnt jede DTD ab.** `resolve_entities=False` verhindert die Expansion, laesst den DOCTYPE aber durch. Da Nextcloud nie eine DTD sendet, ist ein DOCTYPE ein Signal und kein zu tolerierender Sonderfall; XXE- und Billion-Laughs-Proben schlagen dadurch mit `ToolError` und ohne Dateizugriff fehl.
- **`NcClients` liegt in `nextcloud/__init__.py`, nicht in `tools/`.** Der Plan liess beides zu. So zeigt die Abhaengigkeit nur in eine Richtung (`tools` nach `nextcloud`) und `deps.resolve_clients()` kann das Objekt bauen, ohne dass die Credential-Schicht `tools` importieren muss.
- **Der Status wird an genau einer Stelle uebersetzt (`dav._check`).** Alle Statuscodes inklusive 3xx, 416 und 429 werden dort zu `message` plus `hint`. Kein Aufrufer interpretiert HTTP-Codes selbst, und der 401-Pfad hat konstruktionsbedingt keinen Retry (Pitfall 8).
- **Nur SRV-02 wird als erfuellt markiert.** Siehe Abschnitt Requirements-Status.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Eigene Testdatei fuer die XML-Haertung**
- **Found during:** Task 1
- **Issue:** Der Plan fordert Unit-Tests "inklusive XXE-Probe", listet in `files_modified` aber keine Testdatei fuer `xml.py`. Die Probe in `test_credentials_http.py` zu verstecken haette die Datei ihrem Namen entzogen und die Sicherheitspruefung schwer findbar gemacht.
- **Fix:** `tests/unit/test_xml.py` neu angelegt (13 Tests: Parser-Flags, XXE, Billion Laughs, DTD, Syntaxfehler, falsches Root-Element, Propstat-Filter, Collection-Erkennung).
- **Files modified:** tests/unit/test_xml.py
- **Verification:** `uv run pytest tests/unit -q` Exit 0; XXE-Probe liefert `ToolError` und keinen Dateizugriff.
- **Committed in:** 80fd416 (RED), a0045bd (GREEN)

**2. [Rule 2 - Missing Critical] `graceful()` faengt zusaetzlich `httpx.RequestError`**
- **Found during:** Task 3
- **Issue:** Der Plan nennt nur `ToolError` und `httpx.TimeoutException`. Ein Verbindungsfehler (falsche Basis-URL, Nextcloud offline, DNS) waere als roher `httpx.ConnectError` mit vollem Traceback beim Client gelandet, und dieser Traceback enthaelt die Request-URL. Das ist genau der Leak-Pfad aus T-01-07 und zusaetzlich eine unbrauchbare Fehlermeldung.
- **Fix:** `except httpx.RequestError` nach dem Timeout-Zweig (Timeout ist eine Unterklasse, Reihenfolge ist bewusst), Meldung "Could not reach Nextcloud" plus Hinweis auf die konfigurierte URL, ebenfalls mit `from None`.
- **Files modified:** src/mcp_connector/server/__init__.py
- **Verification:** `uv run pytest -q` Exit 0; Reihenfolge der `except`-Zweige gegen die httpx-Klassenhierarchie geprueft.
- **Committed in:** b8a27d6

**3. [Rule 3 - Blocking] Parser-Flags sind ueber lxml nicht auslesbar**
- **Found during:** Task 1 (roter Lauf von `test_hardened_parser_settings`)
- **Issue:** Der erste Testentwurf prueft `parser.resolve_entities is False`. `lxml.etree.XMLParser` exponiert diese Flags nicht als Attribute (`AttributeError`), das Acceptance-Kriterium waere so nicht pruefbar.
- **Fix:** Zwei Pruefungen statt einer: eine Quellcode-Pruefung per `inspect.getsource(xml.hardened_parser)` auf die drei Flags (haelt das Kriterium wortgetreu) und eine Verhaltenspruefung mit einer definierten Entity, die nicht expandiert wird.
- **Files modified:** tests/unit/test_xml.py
- **Verification:** beide Tests gruen; `grep` auf `xml.py` zeigt `resolve_entities=False`, `no_network=True`, `huge_tree=False`.
- **Committed in:** a0045bd

**4. [Rule 3 - Blocking] Docstring-Wortwahl gegen die Grep-Gates**
- **Found during:** Task 2 und Task 3 (Acceptance-Pruefung)
- **Issue:** Zwei Kriterien pruefen per `grep` ohne Kommentar-Filter fuer Docstrings: `dav.py` darf ausserhalb von Kommentarzeilen kein delete/move/copy/proppatch enthalten, `server/__init__.py` kein `stateless_http` und kein `FastMCP`. Beide Dateien erklaerten in ihren Docstrings genau diese Nicht-Ziele und haetten die Gates rein textlich gerissen.
- **Fix:** Begruendungen umformuliert ("die v1-Server-Klasse", "die legacy-only Statelessness-Weiche"), inhaltlich unveraendert. Die Erklaerung bleibt im Code, das Gate bleibt scharf.
- **Files modified:** src/mcp_connector/nextcloud/clients/dav.py, src/mcp_connector/server/__init__.py
- **Verification:** `grep -v '^\s*#' dav.py | grep -ci "delete\|move\|copy\|proppatch"` = 0; `grep -c "stateless_http\|FastMCP" server/__init__.py` = 0.
- **Committed in:** 41469c8, b8a27d6

**5. [Rule 1 - Bug] Em-Dashes in STATE.md entfernt**
- **Found during:** State-Update
- **Issue:** `gsd-sdk query state.add-decision` trennt Zusammenfassung und Begruendung mit einem Em-Dash. Em-Dashes sind projektweit verboten.
- **Fix:** Alle Em- und En-Dashes in `.planning/STATE.md` durch `: ` ersetzt (gleiche Korrektur wie in Plan 01-01, weiterhin ein SDK-Verhalten und kein Eingabefehler).
- **Files modified:** .planning/STATE.md
- **Verification:** Zaehlung der Em-/En-Dash-Zeichen in STATE.md ergibt 0.
- **Committed in:** SUMMARY-Commit

---

**Total deviations:** 5 auto-fixed (2 missing critical, 2 blocking, 1 bug)
**Impact on plan:** Kein Scope-Creep, keine neue Dependency, keine Architekturaenderung. Zwei Fixes betreffen Sicherheit (XML-Testabdeckung, Leak-Pfad im Wrapper), zwei die Pruefbarkeit der Acceptance-Kriterien, einer eine Projektregel.

## Requirements-Status

| ID | Status | Begruendung |
|----|--------|-------------|
| SRV-02 | **Complete** | stdio-Betrieb mit App-Passwort aus Env ist gegen das echte Console-Script bewiesen (`initialize` beantwortet, stdout sauber, Fehlkonfiguration mit Exit 2). |
| SRV-03 | Pending | Annotationen und Schema-Diaet sind fuer 1 von 15 Tools bewiesen. Der Vollnachweis gehoert zu Plan 01-14. |
| SRV-05 | Pending | Kein Session-State vorhanden und `next_offset` als Handle etabliert, aber der Multi-Worker-Nachweis braucht den HTTP-Transport aus Plan 01-04. |
| TOOL-01 | Pending | Von vier Datei-Tools existiert `files_read`. `files_search`, `files_list` und `files_upload` folgen. |
| AUTH-01 | Pending | Basic mit App-Passwort laeuft im stdio-Modus; der Remote-Teil (Header-Passthrough, statischer Bearer) ist Plan 01-04. |

Die Trennung ist bewusst: ein abgehaktes Requirement soll eine erbrachte Faehigkeit bedeuten, nicht eine begonnene.

## Issues Encountered

Keine ungeplanten Probleme. Zwei Punkte, die Zeit gekostet haben, sind oben als Deviation 3 und 4 dokumentiert (lxml-Introspektion, Wortwahl gegen Grep-Gates).

Ein Hinweis fuer Folgeplaene: die `matrix`-Tests laufen in der Default-Suite mit (`addopts` schliesst nur `integration` aus). `uv run pytest -q` startet damit drei echte Subprozesse. Das ist gewollt (der Startup-Vertrag soll nicht optional sein) und kostet aktuell rund 3 der 4,7 Sekunden Laufzeit.

## Known Stubs

Keine. Jedes ausgelieferte Modul ist verdrahtet und getestet. Bewusst noch nicht existierende Ziele, die spaetere Plaene fuellen:

| Ziel | Referenziert von | Faellig in |
|------|------------------|-----------|
| `mcp_connector.entry_http` (ASGI-App, Header-Passthrough, statischer Bearer) | `NC_MCP_ALLOWED_HOSTS`, `NC_MCP_STATIC_BEARER` in `config.py` | Plan 01-04 |
| Schreibpfad `dav.put_new_file` (PUT mit `If-None-Match: *`) | Threat T-01-10 (transfer) | Plan 01-03 |
| `ids.encode_*`-Nutzung durch `search`/`fetch` | `ids.py` (heute nur per Unit-Test genutzt) | Plan 01-12/01-13 |
| `AppMissingError` und `ConflictError` | `errors.py` (definiert, noch kein Aufrufer) | Plan 01-03 (Conflict), Notes/Deck-Plaene (AppMissing) |

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Models des Plans. Alle als `mitigate` gefuehrten Positionen sind implementiert und getestet: T-01-07 (Maskierung, `from None`, Logger-Pinning, kein print), T-01-08 (Basis-URL nur aus Env, `follow_redirects=False`, Redirect als Konfigurationsfehler), T-01-09 (`safe_path` vor jedem Request, sieben Negativtests ohne HTTP-Call), T-01-11 (lxml-Builder, gehaerteter Parser, DTD-Ablehnung), T-01-12 (Identitaet nur aus `deps`, Schema-Pruefung auf user/username/uid), T-01-13 (Deckel, Truncation-Marker, Binaer-Ablehnung), T-01-14 (kein Auth-Retry, 401 und 429 als Endzustaende). T-01-10 bleibt wie geplant `transfer`: dieser Plan enthaelt keinen Schreibpfad.

## User Setup Required

Keine. Fuer den Betrieb per stdio setzt der Nutzer spaeter `NC_MCP_URL`, `NC_MCP_USER` und `NC_MCP_APP_PASSWORD`; fuer Tests und CI ist nichts einzurichten (keine Docker-Nextcloud noetig).

## Next Phase Readiness

- **Bereit fuer Plan 01-03 (Datei-Schreibpfad) und alle weiteren Tool-Plaene.** Ein neues Tool-Bundle besteht ab jetzt aus einer Datei in `tools/` und einer in `server/reg_*.py`; `server/__init__.py` muss dafuer nicht mehr angefasst werden. Das macht die parallelen Wave-Plaene konfliktfrei.
- **Bereit fuer Plan 01-04 (Streamable HTTP).** `deps.resolve_credentials(ctx)` ist die einzige Stelle, die um die Header-Modi erweitert werden muss; `config.py` haelt die Variablennamen bereit.
- **Offen, kein Blocker dieses Plans:** Docker-Engine laeuft auf dem Host nicht, Integrationstests bleiben CI-Sache; das GitHub-Remote existiert noch nicht, es gab also weiterhin keinen CI-Lauf und keinen Push. Der erste gruene CI-Lauf ist ab diesem Plan technisch moeglich (Contract-Test und Budget-Gate sind gruen).
- **Fuer Plan 01-14 vormerken:** aktueller Messwert des Budget-Gates ist 660 Bytes bei einem Tool; das Budget von 24000 Bytes muss dort auf "gemessen plus 15 Prozent" fixiert werden.

## Self-Check

Dateien (alle mit `[ -f ]` geprueft): errors.py FOUND, ids.py FOUND, config.py FOUND, deps.py FOUND, entry_stdio.py FOUND, nextcloud/__init__.py FOUND, nextcloud/credentials.py FOUND, nextcloud/http.py FOUND, nextcloud/clients/__init__.py FOUND, nextcloud/clients/xml.py FOUND, nextcloud/clients/dav.py FOUND, tools/__init__.py FOUND, tools/files.py FOUND, server/__init__.py FOUND, server/reg_files.py FOUND, tests/unit/test_ids.py FOUND, tests/unit/test_config.py FOUND, tests/unit/test_credentials_http.py FOUND, tests/unit/test_xml.py FOUND, tests/unit/test_files_read.py FOUND, tests/compat/test_stdio_startup.py FOUND.

Commits: 80fd416 FOUND, a0045bd FOUND, 877f8df FOUND, 41469c8 FOUND, b8a27d6 FOUND.

Plan-Verifikation:
1. `uv run pytest -q` Exit 0 (95 passed, ohne Docker), `uv run pytest -m matrix -q` Exit 0 (3 passed) - PASS
2. `uv run python scripts/check_tool_budget.py` Exit 0 (660 von 24000 Bytes) - PASS
3. `uv run ruff check .` Exit 0 und `uv run ruff format --check .` Exit 0 (28 Dateien) - PASS
4. Grep-Gegenprobe: kein `stateless_http`, kein `FastMCP`, kein `print(` in `src/`, keine destruktive DAV-Methode - PASS
5. Acceptance-Kriterien aller drei Tasks einzeln nachgefahren, inklusive Input-Schema-Pruefung auf `user`/`username`/`uid` (Parameter sind genau `path` und `offset`) - PASS

## Self-Check: PASSED

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
