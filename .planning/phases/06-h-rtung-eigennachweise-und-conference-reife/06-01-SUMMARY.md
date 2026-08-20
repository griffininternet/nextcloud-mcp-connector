---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 01
subsystem: oauth
tags: [cimd, ssrf, fail-closed, pure-functions, size-limit, no-network]

# Dependency graph
requires: []
provides:
  - "bounded_response: das Groessenlimit dieses Projekts auf der Response-Seite, Zwilling von bounded_body in derselben Datei"
  - "oauth/cimd.py mit is_cimd_client_id (Formpruefung ohne Netzwerkverkehr), target_allowed (gemessene Konjunktion gegen die drei ipaddress-Luecken) und resolve_addresses (eine schlechte Adresse verwirft den ganzen Namen)"
  - "MAX_DOCUMENT_BYTES = 5120 und FETCH_TIMEOUT_SECONDS = 5.0 als Modulkonstanten ohne Env-Schalter"
  - "AddressLookup als injizierbarer Resolver-Typ, damit der Zwei-Antworten-Resolver von 06-02 ohne Patch testbar ist"
affects: [AUTH-09, AUTH-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Groessenlimit bleibt in exapp/responses.py, auch wenn der neue Aufrufer in oauth/ liegt: zwei Limits in zwei Modulen sind die Kopie, die dieses Modul einmal abgeschafft hat"
    - "Die gemessene Eigenschaft der Standardbibliothek wird selbst zur Zusicherung: ein Test behauptet, dass 100.64.0.1 nicht is_private und 224.0.0.1 is_global ist, damit ein spaeteres Python die Konjunktion nicht stillschweigend entwertet"
    - "Der Resolver ist ein Signaturparameter mit sichtbarem Default (resolver: AddressLookup = _system_addresses), nie ein Modulaufruf"
    - "Ein AST-Gate prueft jeden logger-Aufruf des Moduls auf Argumente, die Werte der Anfrage tragen, statt sich auf die Formulierung der Meldungen zu verlassen"

key-files:
  created:
    - src/mcp_connector/oauth/cimd.py
    - tests/unit/test_oauth_cimd.py
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/deferred-items.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-01-SUMMARY.md
  modified:
    - src/mcp_connector/exapp/responses.py
    - tests/unit/test_exapp_responses.py
    - .planning/STATE.md

key-decisions:
  - "Der Default-Resolver ruft loop.getaddrinfo (asyncio, Standardbibliothek) statt anyio.getaddrinfo: docs/dependency-audit.md verlangt, dass ein direkt importiertes Paket direkt deklariert wird, und anyio liegt nur transitiv im Lock; der Plan-Wortlaut haette pyproject.toml, einen Audit-Eintrag und eine Owner-Freigabe erzwungen, was die Verifikation dieses Plans (pyproject und uv.lock unveraendert, T-06-SC) ausgeschlossen hat"
  - "Der Typalias heisst AddressLookup und nicht Resolver: das Contract-Gate tests/contract/test_no_destructive_calls.py verbietet die Zeichenkette 'Resolve' in src, weil sie MCP-Reference-Resolution meint; der Parametername resolver (klein) bleibt, das Gate bleibt unangetastet"
  - "resolve_addresses lehnt auch eine Resolver-Antwort ab, die keine Adresse ist, und einen leeren Hostnamen, ohne den Resolver zu fragen: dieselbe fail-closed-Lesart wie bei einer gemischten Aufloesung"
  - "Kein CHANGELOG-Eintrag: die beiden Bausteine haengen an keiner Route, nach aussen aendert sich in diesem Plan nichts; der nutzerrelevante Eintrag gehoert zu dem Plan, der den Abruf verdrahtet"

patterns-established:
  - "Die reinen Grenzen einer Transportstrecke entstehen vor dem Transport, in einer Testdatei, die ausdruecklich nicht einmal mockt: der Negativkatalog laeuft dann so schnell wie ein Lint"

requirements-completed: []

# Metrics
duration: 30min
completed: 2026-08-20
---

# Phase 06 Plan 01: Die Grenz-Bausteine des CIMD-Abrufs Summary

Die zwei Grenzen, die der Dokumentabruf von AUTH-09 ohne ein einziges Paket haelt, stehen als
reine Funktionen: eine `client_id`, die keine zulaessige CIMD-URL ist, wird vor der ersten
Aufloesung abgelehnt, jede Adresse aus den drei gemessenen `ipaddress`-Luecken (NAT64, CGNAT,
Multicast) wird abgelehnt, ein Name, der auf eine oeffentliche und eine private Adresse
aufloest, wird ganz verworfen statt auf die oeffentliche gepinnt, und das Groessenlimit bricht
im Chunk-Loop ab, bevor der Rumpf zu Ende gelesen ist.

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/exapp/responses.py` | `bounded_response(response, max_bytes)` neben `bounded_body`, mit denselben zwei Exceptions (`BodyTooLarge`, `BodyUnreadable`); keine dritte Exception-Klasse, `httpx` neu importiert, `bounded_response` alphabetisch in `__all__` |
| `tests/unit/test_exapp_responses.py` | Neun Tests fuer die Response-Seite auf einer eigenen `httpx.AsyncByteStream`: ganz, genau die Grenze, ein Byte darueber mit dem Beleg, dass der Rest des Streams nie abgeholt wurde, Abbruch mitten im Stream, `BodyUnreadable` statt Original-Exception, und eine Absage ohne Inhalt des Dokuments |
| `src/mcp_connector/oauth/cimd.py` (NEU) | `is_cimd_client_id`, `target_allowed`, `resolve_addresses`, `_system_addresses` als Default-Resolver, `MAX_DOCUMENT_BYTES = 5120`, `FETCH_TIMEOUT_SECONDS = 5.0`, `AddressLookup` |
| `tests/unit/test_oauth_cimd.py` (NEU) | 48 Tests: drei Parametrize-Kataloge (Form positiv, Form negativ, Adressklasse), die drei gemessenen Luecken als eigene Zusicherung, sieben Faelle um `resolve_addresses`, das Log-AST-Gate und die Konstanten |
| `deferred-items.md` (NEU) | Ein Fund ausserhalb des Auftrags: die Selbstangabe der Version in `uv.lock` |

## Wie die Grenzen gebaut sind

**Die Form der `client_id`** folgt `registry.redirect_uri_allowed` in allem, was zaehlt:
`urlsplit`, `try/except ValueError` um `hostname`/`port`, Rueckgabe `bool`, kein Logging des
geprueften Werts. Sie ist strenger als `is_valid_client_metadata_url` der Client-Seite des
SDK, und der Docstring sagt, warum: dort validiert ein Client seine eigene Konfiguration,
hier entscheidet ein Server ueber einen Outbound-Request fuer einen Fremden. Query und Port
bleiben zulaessig (Draft: SHOULD NOT beziehungsweise MAY), Fragment, Userinfo, fehlender Pfad
und Dot-Segmente sind Absagen.

**Die Adressklasse** ist die Konjunktion aus 06-RESEARCH.md Pattern 3, wortgetreu uebernommen:
v4-mapped entpacken, `is_global` als Pflicht, dann Absage bei `is_private`, `is_loopback`,
`is_link_local`, `is_reserved`, `is_multicast`, `is_unspecified`. Dazu kommt etwas, das der
Plan nicht verlangte und was die Regel gegen die Zukunft haelt: ein Test behauptet die
Messung selbst. Er faellt, wenn ein spaeteres Python `100.64.0.1` als `is_private` oder
`224.0.0.1` als nicht `is_global` fuehrt, also genau dann, wenn die Begruendung der
Konjunktion nicht mehr stimmt. Wer sie kuerzen will, muss dann diesen Test anfassen und liest
dabei, warum sie so lang ist.

**Die Aufloesung** verwirft den ganzen Namen, sobald eine Adresse durchfaellt, und zwar in
beiden Reihenfolgen (`8.8.8.8` zuerst und `127.0.0.1` zuerst sind derselbe Fall). Leere
Antwort, werfender Resolver, Antwort, die keine Adresse ist, und leerer Hostname sind vier
Wege in dieselbe Absage `None`. Der Resolver ist ein Signaturparameter mit sichtbarem
Default; ein Test belegt, dass der Default tatsaechlich verdrahtet ist, indem er `localhost`
aufloest (der eine Name, der ohne Paket beantwortet wird) und die Absage bekommt.

**Das Groessenlimit** ist der Zwilling in derselben Datei, nicht ein zweiter Zaehler in
`cimd.py`. Der Test, der zaehlt, ist der wichtigste: von 512 angebotenen Kilobyte-Chunks
werden hoechstens fuenf abgeholt, und der Stream hat nachweislich mehr zu geben. Eine Pruefung
auf dem fertigen Rumpf haette erst alles gelesen und danach nein gesagt.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest` (Default-Auswahl) | 1983 passed, 92 deselected in 52,41 s |
| `uv run --no-sync pytest tests/unit/test_exapp_responses.py tests/unit/test_oauth_cimd.py -q` | gruen (17 + 48) |
| `uv run --no-sync pytest tests/unit/test_project_layout.py -q` | gruen (httpx-Pin unberuehrt, `httpx2` kommt in keiner der beiden Dateien vor) |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0; kein Whitelist-Eintrag noetig, weil `__all__` die neuen Namen traegt |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| Vokabular-Gate | "archiv" kommt in keiner der vier Dateien vor |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC: dieser Plan installiert nichts) |

Die Akzeptanzgrenzen des Plans wurden einzeln nachgezaehlt: `async def bounded_response`
einmal, `^class ` unveraendert zwei, `httpx2` null, `os.environ` in `cimd.py` null,
`MAX_DOCUMENT_BYTES = 5120` genau einmal (die Erwaehnung im Modul-Docstring wurde dafuer
umformuliert), `resolver` in der Signatur von `resolve_addresses`.

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 3 - Blocker] `anyio.getaddrinfo` durch `loop.getaddrinfo` ersetzt**

- **Gefunden bei:** Task 2, beim Schreiben des Default-Resolvers
- **Problem:** Der Plan schreibt `anyio.getaddrinfo` vor. `anyio` liegt nur transitiv im
  Lock, und die Politik in `docs/dependency-audit.md` lautet woertlich: was direkt importiert
  wird, wird direkt deklariert (das ist die Begruendung, mit der `cryptography` 2026-08-16
  vom transitiven zum direkten Paket wurde, mit Owner-Freigabe und Audit-Eintrag). Der
  Plan-Wortlaut haette also entweder die Politik gebrochen oder `pyproject.toml` und
  `uv.lock` geaendert, was die Verifikation dieses Plans ausdruecklich ausschliesst.
- **Fix:** `asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)`.
  Auf dem asyncio-Backend, das dieses Projekt fuehrt, ist das dieselbe Aufloesung, die
  `anyio.getaddrinfo` darunter aufruft. Die Begruendung steht im Docstring der Funktion.
- **Dateien:** `src/mcp_connector/oauth/cimd.py`
- **Commit:** 35e75e8

**2. [Rule 3 - Blocker] Typalias `Resolver` heisst `AddressLookup`**

- **Gefunden bei:** Task 2, beim vollen Testlauf
- **Problem:** `tests/contract/test_no_destructive_calls.py::test_no_tool_stops_to_ask_the_user_or_resolves_a_reference`
  verbietet die Zeichenkette `Resolve` in jeder Quelldatei unter `src` (sie steht fuer
  MCP-Reference-Resolution, die ueber einen Aufruf hinaus Zustand haelt). Der Name `Resolver`
  loeste das Gate an drei Stellen aus. Das Gate ist nicht falsch, es ist nur namensblind.
- **Fix:** Alias umbenannt, Parametername `resolver` (klein) unveraendert, damit die
  Akzeptanzgrenze des Plans erfuellt bleibt. Das Gate wurde nicht angefasst.
- **Dateien:** `src/mcp_connector/oauth/cimd.py`, `tests/unit/test_oauth_cimd.py`
- **Commit:** 35e75e8

**3. [Rule 2 - fehlende kritische Pruefung] Zwei Absagen mehr in `resolve_addresses`**

- **Gefunden bei:** Task 2
- **Problem:** Der Plan nennt drei Absagegruende (leere Antwort, Aufloesungsfehler,
  durchgefallene Adresse). Eine Resolver-Antwort, die gar keine Adresse ist, und ein leerer
  Hostname waeren durch das Raster gefallen: der erste Fall haette eine `ValueError` aus
  `ipaddress.ip_address` in einen Handler geworfen, was D-37 verbietet.
- **Fix:** Beide sind jetzt Absagen mit eigenem Test; der leere Hostname erreicht den
  Resolver nicht einmal.
- **Dateien:** `src/mcp_connector/oauth/cimd.py`, `tests/unit/test_oauth_cimd.py`
- **Commit:** 35e75e8

### Ausserhalb des Auftrags, nicht angefasst

Die Selbstangabe `version = "0.1.0"` in `uv.lock` (das Repo steht auf 0.1.2) wird vom ersten
`uv run` einer Sitzung korrigiert und erschien dadurch als Arbeitsbaum-Aenderung. Bewusst
zurueckgenommen und in `deferred-items.md` protokolliert, statt sie in einen Commit dieses
Plans zu ziehen.

## Was dieser Plan nicht tut

Kein Netzwerkzugriff, kein `respx`, kein Mock. Kein neues Paket. Kein `os.environ` und kein
modul-globaler veraenderlicher Zustand. Keine Route, kein Schalter, kein Store-Feld: die
Formpruefung ist noch an keinen Endpunkt angeschlossen, `MAX_DOCUMENT_BYTES` und
`FETCH_TIMEOUT_SECONDS` haben noch keinen Aufrufer, und `bounded_response` wird noch von
keiner Produktionsdatei importiert. Das ist der Zuschnitt des Plans: 06-02 baut den gepinnten
Abruf gegen fertige Kontrakte statt gegen Vermutungen.

## Known Stubs

Keine. Die vier Funktionen tun vollstaendig, was ihre Docstrings sagen; was fehlt, ist ihr
Aufrufer, und der ist ausdruecklich Gegenstand von 06-02.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans: es entstehen kein
Endpunkt, kein Auth-Pfad, kein Dateizugriff und keine Schema-Aenderung. `_system_addresses`
ist der einzige neue Aussenkontakt und fragt ausschliesslich den Resolver des Hosts.

## Requirements

AUTH-09 bleibt offen und wird hier bewusst nicht abgehakt: die reinen Grenzen stehen, aber
der Nachweis "fail-closed mit einem Negativtest pro Grenze" umfasst Groessenabbruch am
Transport, Timeout, Redirect-Verweigerung und Rebinding, und die brauchen den Abruf aus 06-02.

## Self-Check: PASSED

Alle vier in dieser Zusammenfassung genannten neuen Dateien liegen auf der Platte, beide
Task-Commits sind im Log (ec46b1a, 35e75e8), und die Testdatei des zweiten Tasks laeuft
gruen nachgeprueft.
