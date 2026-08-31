# Phase 19: Audit-Log Bedienung und Textnachzug - Pattern Map

**Mapped:** 2026-08-31
**Files analyzed:** 17 (2 neu, 15 geändert)
**Analogs found:** 16 / 17 (ein Textziel ohne Analog, siehe unten)

Alle Pfade sind repo-relativ zu `C:\Users\Student\nextcloud-mcp-connector`. Zeilennummern sind
am Stand vom 2026-08-31 gemessen und beim Planen zu prüfen, nicht blind zu übernehmen.

---

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächster Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `src/mcp_connector/exapp/audit_read.py` (NEU) | route/handler | request-response | `src/mcp_connector/exapp/audit_verify.py` | exakt |
| `src/mcp_connector/audit/store.py` (MOD: `read_entries`) | model/store | CRUD-read (batch) | dieselbe Datei: `last_entry` `:991-1004`, `verify_chains` `:1006-1031` | exakt (Selbstanalog) |
| `src/mcp_connector/exapp/occ.py` (MOD: dritter Eintrag) | config/registration | request-response | zweiter Eintrag in `command_schemes()` `:131-145` | exakt |
| `src/mcp_connector/entry_exapp.py` (MOD: eine Zeile) | provider/wiring | request-response | `:229` `*audit_verify_routes(...)` plus Kommentar `:193-202` | exakt |
| `src/mcp_connector/exapp/ui/strings.py` (MOD: 2 Konstanten) | UI-Textkatalog | keiner (Datenkonstante) | `ADMIN_FIELD_TALK_SEND_DESCRIPTION` `:627-638`, `ADMIN_FIELD_CIMD_DESCRIPTION` `:595-609` | exakt |
| `appinfo/info.xml` (MOD: Kommentar, Enterprise x3, evtl. env vars) | config/manifest | keiner | fünfter abwesender Pfad `:284-294`; `<environment-variables>` `:525-550` | exakt |
| `docs/privacy.md` (MOD) | Doku | keiner | eigener Speicherabschnitt `:27-49` + Purge `:168-191` | rollengleich |
| `docs/uninstall.md` (MOD) | Doku/Runbook | keiner | eigene Prüfliste `:95-150`, Purge-Feldtabelle `:162-167` | rollengleich |
| `docs/faq.md` (MOD, empfohlen) | Doku | keiner | eigener Eintrag `:115-123` | rollengleich |
| `README.md` / `README.de.md` / `README.fr.md` (MOD: Enterprise) | Doku | keiner | `README.md:512-516` (EN-Original), DE/FR daneben | exakt |
| `CHANGELOG.md` (MOD: `[Unreleased]` NEU anlegen) | Doku | keiner | Kopf `:1-11` + Eintragsform `:12-31` | exakt |
| `tests/unit/test_exapp_audit_read.py` (NEU) | test | request-response | `tests/unit/test_exapp_audit_verify.py` | exakt |
| `tests/unit/test_audit_store.py` (MOD) | test | CRUD-read | eigene Helfer `:47-95` | exakt |
| `tests/unit/test_exapp_env_setup.py` (MOD: Vier-Wörter-Gate) | test/gate | keiner | Vokabular-Gate `:1993-2084` | exakt |
| `tests/unit/test_exapp_admin_settings.py` (MOD) | test | request-response | `:313-336` | exakt |
| `tests/unit/test_exapp_lifecycle.py` (MOD: Kommandozahl) | test | request-response | `:425-466` (`route.call_count == 2`) | exakt |
| `tests/unit/test_exapp_purge.py` (MOD: Registrierungszählung) | test | request-response | `:1067-1097` | exakt |

Anmerkung zu den letzten zwei Zeilen: beide Dateien behaupten heute die Zahl **zwei** über die
registrierten Kommandos (`route.call_count == 2`, `len(occ.command_schemes())`). Ein drittes
Kommando macht mindestens `test_exapp_lifecycle.py:443` und `:464` rot. Das gehört als
erwartete Teständerung in den Plan, nicht als Überraschung in die Ausführung.

---

## Pattern Assignments

### `src/mcp_connector/exapp/audit_read.py` (NEU, route/handler, request-response)

**Analog:** `src/mcp_connector/exapp/audit_verify.py` (406 Zeilen, komplett gelesen)

Diese Datei ist Zeile für Zeile die Vorlage. Reihenfolge im Modul beibehalten: Docstring mit den
drei Begründungen, `__all__`, Pfadkonstante, Optionskonstanten, `OCC_ENVELOPE`,
`HEADER_ORIGIN_IP`, `MAX_BODY_BYTES`, Fabrikfunktion, dann die privaten Helfer.

**Modulkopf und Konstanten** (`audit_verify.py:44-96`):

```python
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..audit.store import (
    FINDING_MISSING,
    FINDING_MODIFIED,
    SIZE_LIMIT_BYTES,
    AuditStore,
    ChainFinding,
    StoreOverview,
)
from ..errors import ToolError
from .auth import AppApiRejected, require_appapi
from .responses import NO_STORE, BodyTooLarge, BodyUnreadable, bounded_body, json_response

__all__ = ["AUDIT_VERIFY_PATH", "JSON_OPTION", "audit_verify_routes"]

AUDIT_VERIFY_PATH = "/audit-verify"
JSON_OPTION = "json"
OCC_ENVELOPE = "occ"
HEADER_ORIGIN_IP = "x-origin-ip"
MAX_BODY_BYTES = 4096
```

Zu kopieren: `HEADER_ORIGIN_IP` wird bewusst ein **viertes** Mal buchstabiert statt importiert
(Begründung `audit_verify.py:88-91`: `lifecycle` importiert `occ`, `occ` importiert das
Handlermodul, ein Rückimport wäre ein Zyklus). Ein Test hält die Schreibweisen gleich, siehe
Shared Patterns.

**Fabrik statt Registrierung** (`audit_verify.py:139-178`):

```python
def audit_verify_routes(
    env: Mapping[str, str] | None = None, *, store_provider: StoreProvider
) -> list[Route]:
    """The one route of the check, handed out rather than registered on the server object."""

    async def audit_verify(request: Request) -> Response:
        guarded = _guard(request, env)
        if isinstance(guarded, Response):
            return guarded

        as_json = await _wants_json(request)
        try:
            store = await store_provider()
            overview = await store.overview()
            findings = await store.verify_chains()
        except Exception as exc:
            # The type only, never the message: a store error can carry a path.
            logger.error("the audit log could not be checked: %s", type(exc).__name__)
            if as_json:
                return json_response({"checked": False, "error": type(exc).__name__})
            return _text(f"the audit log could not be checked: {type(exc).__name__}")
        ...
        return _text(_report(overview, findings))

    return [Route(AUDIT_VERIFY_PATH, audit_verify, methods=["POST"])]
```

Vier Dinge unverändert übernehmen: `type(exc).__name__` statt Fehlertext (ein Store-Fehler
trägt Pfade), `methods=["POST"]`, der Typalias `type StoreProvider = Callable[[], Awaitable[AuditStore]]`
(`:136`), und die Reihenfolge Guard zuerst, Optionslesen danach.

**Doppelprüfung, wörtlich zu übernehmen** (`audit_verify.py:299-312`):

```python
def _guard(request: Request, env: Mapping[str, str] | None) -> str | Response:
    if HEADER_ORIGIN_IP in request.headers:
        return _text("Not Found", status_code=404)
    try:
        return require_appapi(request, env=env)
    except (AppApiRejected, ToolError):
        return json_response({}, status_code=401)
```

**Antwortform, 200 auch im Fehlerfall** (`audit_verify.py:400-406`):

```python
def _text(body: str, status_code: int = 200) -> Response:
    return Response(body, status_code=status_code, media_type="text/plain", headers=NO_STORE)
```

**Rumpf lesen, begrenzt und nie geloggt** (`audit_verify.py:371-397`):

```python
async def _payload(request: Request) -> Any:
    announced = request.headers.get("content-length", "")
    if announced.isdigit() and int(announced) > MAX_BODY_BYTES:
        logger.warning("a check call announced a body this handler does not read")
        return None
    try:
        raw = await bounded_body(request, MAX_BODY_BYTES)
    except BodyTooLarge:
        logger.warning("a check call sent a body this handler does not read")
        return None
    except BodyUnreadable:
        logger.warning("the body of a check call could not be read")
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        logger.warning("the body of a check call is not JSON")
        return None
```

Hinweis für den Planer: `announced.isdigit()` ist hier genau die Stelle R-18-08 (kein
`isascii()`). Wenn der Restpunkt in dieser Phase mitgenommen wird, dann in **beiden** Modulen
gleich, sonst driften zwei Fassungen einer Regel.

**Flaggenleser (`none`-Modus), NICHT für Wert-Optionen verwenden** (`audit_verify.py:325-368`):

```python
def _set_in(payload: Any, *, inside_envelope: bool = False) -> bool:
    if not isinstance(payload, dict):
        return False
    if JSON_OPTION in payload and _is_set(payload[JSON_OPTION]):
        return True

    options = payload.get("options")
    if isinstance(options, dict) and JSON_OPTION in options and _is_set(options[JSON_OPTION]):
        return True
    if isinstance(options, list | tuple) and any(
        isinstance(item, str) and item.strip().lstrip("-") == JSON_OPTION for item in options
    ):
        return True

    if not inside_envelope:
        return _set_in(payload.get(OCC_ENVELOPE), inside_envelope=True)
    return False


def _is_set(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, int | float):
        return value == 1
    if not isinstance(value, str):
        return False
    return value.strip().lower() in TRUE_WORDS
```

Für `--user` und `--limit` braucht das neue Modul einen zweiten, kleinen Leser (Wert holen,
`None`/`False` als "nicht gesetzt"), Vorlage im Research-Codebeispiel 2. Die Zahlenprüfung
kopiert die Form aus `src/mcp_connector/config.py:433-465`:

```python
    raw = (source.get(name) or "").strip()
    if not raw:
        return default
    if not (raw.isascii() and raw.isdigit()):
        logger.warning(
            "%s is not a plain number, so the default of %s stays in force.", name, default
        )
        return default
    try:
        number = int(raw)
    except ValueError:
        ...
```

**Klammerung vor der Ausgabe** (`audit_verify.py:277-296`, identische Regel in
`audit/store.py:506-520`):

```python
def _printable(chain: str) -> str:
    printable = "".join(
        " " if character < " " or character == "\x7f" else character for character in chain
    )
    return " ".join(printable.split())[:CHAIN_LIMIT]
```

`nc_user` ist der eine Wert von aussen, den der Speicher beim Schreiben **nicht** reinigt
(`client_name` schon, `store.py:539`). Klammerung gehört unmittelbar vor die Textausgabe.

**JSON-Antwort und Grenzsatz** (`audit_verify.py:245-274`, `:117-121`):

Die maschinenlesbare Form trägt einen Schlüssel, den ein Skript beobachtet (dort `broken`),
weil der Rückgabewert immer 0 ist, und als letzten Schlüssel `"limit": LIMIT_SENTENCE`. Wenn
das Lesekommando eine JSON-Form bekommt, dieselbe Bauart: Daten neben dem Satz, nicht
stattdessen. `LIMIT_SENTENCE` (`:117-121`) ist der Grenzsatz, an dem sich die neue
Formularbeschriftung inhaltlich messen lassen muss (Pitfall 12).

---

### `src/mcp_connector/audit/store.py` (MOD: `read_entries`, model/store, CRUD-read)

**Analog:** dieselbe Datei. Es gibt keine Lesemethode für Zeileninhalte, also ist der Analog
die nächstliegende Leseform.

**Spaltenliste NIE handschreiben** (`store.py:288-301`):

```python
_COLUMNS = ", ".join(CANONICAL_FIELDS)
_PLACEHOLDERS = ", ".join("?" * (len(CANONICAL_FIELDS) + 2))
_INSERT = f"INSERT INTO entries ({_COLUMNS}, prev_hash, hash) VALUES ({_PLACEHOLDERS})"  # noqa: S608 - column names of this module, values are placeholders
_LAST_ROW_OF_CHAIN = f"SELECT {_COLUMNS} FROM entries WHERE chain = ? ORDER BY seq DESC LIMIT 1"  # noqa: S608 - same column names, same placeholders
_ROWS_OF_CHAIN = f"SELECT {_COLUMNS}, prev_hash, hash FROM entries WHERE chain = ? ORDER BY seq"  # noqa: S608 - same column names, no value in the statement
```

Das neue Statement kommt neben diese, mit demselben `# noqa: S608`-Kommentar in derselben
Form ("column names of this module, values are placeholders"). `CANONICAL_FIELDS`
(`store.py:268-286`) darf nicht angefasst werden: der Hash rechnet darüber.

**Leseform: `work`-Closure plus `self._read`** (`store.py:991-1004`):

```python
    async def last_entry(self, chain: str, *, kind: str | None = None) -> Entry | None:
        def work(conn: sqlite3.Connection) -> Entry | None:
            statement = _LAST_ROW_OF_CHAIN if kind is None else _LAST_ROW_OF_KIND
            parameters: tuple[Any, ...] = (chain,) if kind is None else (chain, kind)
            row = conn.execute(statement, parameters).fetchone()
            return None if row is None else _entry_of_row(row)

        return await self._read(work)
```

`_read` ist `asyncio.to_thread(self._call, work, False)` (`store.py:1063-1065`), also kein
`BEGIN`. Nur Keyword-Argumente nach dem `*`, wie jede andere Methode der Klasse.

**Zeile zu Objekt** (`store.py:550-569`): `_entry_of_row` kennt die Spaltenordnung, der Handler
darf sie nicht kennen. `Entry` trägt `seq`, `prev_hash` und `hash` absichtlich **nicht**, also
braucht die Ausgabe entweder eine eigene kleine Rückgabeform oder das rohe Tupel plus
`_entry_of_row` (Research-Codebeispiel 4 geht den zweiten Weg mit `row[0]`, `row[-2]`, `row[-1]`).

**Kanonische JSON-Form** (`store.py:495-503`, `store.py:543`):

```python
    return json.dumps(list(fields), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
...
        json.dumps(sorted(entry.params), separators=(",", ":"), ensure_ascii=False),
```

Dieselben `separators` und `ensure_ascii=False` für die JSONL-Ausgabe, damit eine exportierte
Zeile byteweise wie die kanonische Form aussieht.

**Doc-Kommentarform:** jede öffentliche Methode dieser Datei begründet im Docstring, warum sie
so und nicht anders sortiert oder begrenzt (Beispiel `verify_chains`, `store.py:1006-1020`, mit
einem eigenen Abschnitt "**What this does not do.**"). `read_entries` schuldet dieselbe Form:
Vorgabelimit, Höchstlimit, und warum nach `seq` und nicht nach `at` sortiert wird (WR-02).

---

### `src/mcp_connector/exapp/occ.py` (MOD: dritter Eintrag, config/registration)

**Analog:** zweiter Eintrag derselben Funktion (`occ.py:131-145`).

**Konstanten und Handler-Ableitung** (`occ.py:80-97`):

```python
#: What an administrator types for the check of AUDIT-02. The namespace has two levels on
#: purpose: AUDIT-04 adds a second command in phase 19 that reads entries out and hands them
#: over, and ``mcp_connector:audit:`` carries both of them ...
OCC_AUDIT_COMMAND_NAME = "mcp_connector:audit:verify"

#: The route on us AppAPI calls when the check runs, derived exactly like :data:`OCC_HANDLER`.
OCC_AUDIT_HANDLER = AUDIT_VERIFY_PATH.removeprefix("/")

OCC_AUDIT_DESCRIPTION = (
    "Check every entry of the audit log against the chain it belongs to and report either "
    "that no break was found or the first place a chain is broken."
)

OCC_AUDIT_JSON_DESCRIPTION = (
    "Answer with the same result as JSON, for a script that watches this instead of the "
    "exit code, which is always 0."
)
```

Der Kommentar `:81-83` sagt ausdrücklich, dass `mcp_connector:audit:read` der vorgesehene
Name ist. Pitfall 5: Name einmal festlegen, `insertOrUpdate` keyed auf (appid, name).

**Schemaeintrag** (`occ.py:131-145`):

```python
        {
            "name": OCC_AUDIT_COMMAND_NAME,
            "description": OCC_AUDIT_DESCRIPTION,
            "hidden": 0,
            "arguments": [],
            # The same mode as the option above, and for once the handler reads it for a
            # shape and not for a permission: with it the answer arrives as JSON.
            "options": [
                {"name": JSON_OPTION, "mode": "none", "description": OCC_AUDIT_JSON_DESCRIPTION}
            ],
            # Both ways round, because the plain one is the one an administrator types and
            # the other is the one a monitoring script needs to find.
            "usages": [OCC_AUDIT_COMMAND_NAME, f"{OCC_AUDIT_COMMAND_NAME} --{JSON_OPTION}"],
            "execute_handler": OCC_AUDIT_HANDLER,
        },
```

Neu gegenüber diesem Analog ist nur `"mode": "optional"` plus `"default": None` für die
Wert-Optionen (Research-Codebeispiel 1). `"arguments": []` bleibt leer, `"array"` und
`"negatable"` kommen nicht vor: Pitfall 1 legt sonst die occ-Kommandozeile der ganzen Instanz
still. Jede neue Konstante gehört in `__all__` (`occ.py:47-57`), alphabetisch.

**Registrierschleife** (`occ.py:181-200`): unverändert. Sie iteriert über `command_schemes()`,
je Kommando ein `try`, ein Log pro Fehlschlag, nie eine Ausnahme aus dem Modul. Ein drittes
Kommando kostet dort keine Zeile.

---

### `src/mcp_connector/entry_exapp.py` (MOD: eine Zeile, provider/wiring)

**Analog:** `entry_exapp.py:216-231` plus Begründungskommentar `:187-202`.

```python
    for route in (
        *lifecycle_routes(env),
        *metadata_routes(env, dcr_enabled=policy.dcr_enabled, cimd_enabled=policy.cimd_enabled),
        ...
        *purge_routes(env, store_provider=store),
        *audit_verify_routes(env, store_provider=audit_store),
    ):
        app.router.routes.append(route)
    return app
```

Import daneben (`:35`): `from .exapp.audit_verify import audit_verify_routes`. Der neue Eintrag
bekommt `store_provider=audit_store` (der Audit-Speicher, nicht der OAuth-Speicher, `:114`) und
einen Kommentarblock in der Form von `:193-202` ("Die Prüfung von Plan 18-08 hängt hier für
dieselbe Regel ein fünftes Mal" wird zum sechsten Mal). Wichtig aus `:201-202`: die Route wird
angehängt **unabhängig** vom Schalter D-14, ein abgeschaltetes Log bleibt lesbar und prüfbar.

---

### `src/mcp_connector/exapp/ui/strings.py` (MOD: 2 Konstanten, UI-Textkatalog)

**Analog:** die längeren Beschreibungen desselben Formulars.

**Heutiger Stand, der ersetzt wird** (`strings.py:640-654`):

```python
ADMIN_FIELD_AUDIT_LOG_LABEL = "Keep a record of tool calls"

#: The form half of ``NC_MCP_AUDIT_LOG`` (D-14), and deliberately the short version. It says
#: three things: what a recorded call contains, what it never contains, and the activation
#: cycle this file already spells for every other value. The full wording an administrator
#: needs before switching this on, the works council sentence and the description of what the
#: record can and cannot prove, is AUDIT-05 and belongs to phase 19, which owns that copy
#: together with the page that reads the record. Writing half of it here would leave two
#: places saying different amounts about the same switch.
ADMIN_FIELD_AUDIT_LOG_DESCRIPTION = (
    "With this on, every tool call is written down: the account it ran for, the name of the "
    "tool, the time, the app that called and whether the call succeeded. No parameter value "
    "and no part of a result is stored. This is off unless you switch it on, and a change "
    "takes effect after you disable and enable this app again."
)
```

**Formvorlage für die längere Fassung** (`strings.py:627-638`, das Feld mit dem
Aktivierungssatz, und `:595-609`, das Feld mit einer Kopplung in beiden Richtungen):

```python
ADMIN_FIELD_TALK_SEND_LABEL = "Let assistant apps send Talk messages"

#: The form half of ``NC_MCP_TALK_SEND`` (TALK-04) ... Three things and nothing more: what off
#: means, that reading is untouched by it, and the activation cycle in the sentence this file
#: already spells three times.
ADMIN_FIELD_TALK_SEND_DESCRIPTION = (
    "With this off, no assistant can send a Talk message through this connector, whatever an "
    "account is allowed to do in Talk itself. Reading is not affected: conversations and their "
    "history stay readable. A change takes effect after you disable and enable this app again."
)
```

Zu kopieren: implizit verkettete Stringliterale in Klammern (kein Backslash, keine
f-String-Verkettung über mehrere Zeilen ohne Not), ein `#:`-Kommentar über der Konstante, der
aufzählt, was der Text schuldet und warum, und der wörtlich gleiche Aktivierungssatz "A change
takes effect after you disable and enable this app again."

Beide Namen stehen bereits in `__all__` (`strings.py:41-42`), eine weitere neue Konstante
müsste dort alphabetisch nachgetragen werden (`vulture`-Gate, Pitfall 9).

Der Grenzsatz, an dem sich die neue Beschreibung messen lässt, steht in
`exapp/audit_verify.py:117-121` (`LIMIT_SENTENCE`).

Die 17 Felder, die eine Zeile wirklich trägt, stehen als kommentiertes Schema in
`audit/store.py:220-263`; die drei heute verschwiegenen (`reason`, `duration_ms`, `params`) mit
ihrer Zusage dort: `reason` = "a fixed identifier of a refusal, never a message of an error"
(`:243-244`), `params` = "A sorted JSON list of parameter names, never a value" (`:246`).

---

### `appinfo/info.xml` (MOD: Kommentar + Enterprise x3 + optional env vars)

**Analog 1, sechster abwesender Pfad** (`info.xml:284-294`):

```
		  - The fifth deliberately absent path is /audit-verify, added in plan 18-08, and
		  - for it the rule is the control itself as well. It is the handler of the occ
		  - command mcp_connector:audit:verify, which walks the chain of the audit log and
		  - answers either that no break was found or where the first one is. That answer
		  - names chains, and a chain of a person is named after her account, so a declared
		  - route would hand the list of everybody who used this app to anyone who can reach
		  - the PHP proxy, for exactly the reason stated above: that proxy attaches valid
		  - AppAPI headers itself (T-18-07). AppAPI calls this path over PublicFunctions
		  - like the four above, so it needs no declaration to work, and the handler carries
		  - the same double check. It has no mandatory option, because it changes nothing.
		  - A test asserts that this path is declared in no route below either.
```

Der neue Absatz hängt darunter, gleiche Einrückung (Tabs plus `  - `), gleiche Bauart: was der
Pfad ist, welches Kommando ihn ruft, welcher Schaden aus einer Deklaration folgt, und der
Hinweis, dass ein Test die Abwesenheit hält. Der Zähltest steht auf 13 `<url>`-Einträgen
(`tests/unit/test_exapp_audit_verify.py:212`) und bleibt auf 13. Die einleitende Zeile
`:261` ("Exactly thirteen routes") wird nicht angefasst.

**Analog 2, Enterprise-Absatz, drei Sprachen** (`info.xml:79`, `:124`, `:171`):

```
Audit log, group policies and SSO through your identity provider are planned as a commercial add-on for organisations. Want to run this app in your organisation? Talk to us: admin@infranode.dev

Audit-Log, Gruppen-Policies und SSO über Ihren Identitätsanbieter sind als kommerzielles Add-on für Organisationen geplant. Sie möchten die App in Ihrer Organisation einsetzen? Sprechen Sie uns an: admin@infranode.dev

Journal d'audit, politiques de groupe et SSO via votre fournisseur d'identité sont prévus comme module commercial pour les organisations. Vous souhaitez déployer l'application dans votre organisation ? Contactez-nous : admin@infranode.dev
```

Form: eine Zeile, ein Absatz, kein Backtick, keine Tabelle, kein HTML (Gate
`tests/unit/test_exapp_env_setup.py:1730-1791`). Echte Umlaute und Accents, im Französischen
das schmale Leerzeichen vor `?` und `:` wie im Original. Die Version `<image-tag>0.1.11`
(`:258`) und jede andere Versionsangabe bleiben unangetastet.

**Analog 3, Env-Variablen, nur falls Discretion dafür entscheidet** (`info.xml:526-530`):

```
			<variable>
				<name>NC_MCP_PUBLIC_URL</name>
				<display-name>Public URL of this app</display-name>
				<description>The address this app is reachable under from the internet, without a trailing slash, for example https://cloud.example.com/exapps/mcp_connector. Required for OAuth.</description>			</variable>
```

Drei Elemente je Variable, **kein** `<default>`-Element (leeres `<default>` kommt als String
`Array` an und lässt den Store-Upload mit 500 scheitern, `info.xml:518-524`). Beim Nachtragen
wird `tests/unit/test_exapp_env_setup.py:2174-2181` von sechs auf neun Namen erweitert
(Mengengleichheit, kein Subset), und `test_every_declared_variable_carries_the_three_elements_an_admin_reads`
(`:2184`) prüft Label und Beschreibung.

---

### `docs/privacy.md` (MOD, Doku)

**Analog:** die eigene Tabelle und ihr Ton.

**Speichertabelle** (`privacy.md:27-41`), die um `audit.sqlite3` erweitert wird:

```markdown
## What the app stores

The app keeps one SQLite database inside its own container, for the OAuth 2.1 and
credential state it needs to answer a request without a fresh sign in every time.
It holds these personal data:

| Data | Where | Form |
|------|-------|------|
| Nextcloud user id | `authorizations.nc_user`, `user_access.nc_user` | plain, it is the account name the request runs as |
...
| Client registrations | `clients` | the assistant apps and their redirect targets; the secret issued to a client is stored as a hash only, never in the clear |
```

Zwei harte Randbedingungen: "keeps **one** SQLite database" (`:29`) wird zu zwei, und die Zeile
`| Client registrations` bleibt **wörtlich** stehen, weil
`tests/unit/test_oauth_store.py:1501-1505` auf ihren Anfang und auf "hash" plus "never in the
clear" prüft (Pitfall 18). Neue Zeilen daneben stellen, nicht dazwischen umformulieren.

**Purge- und Retention-Absatz** (`privacy.md:174-191`), die zu korrigierenden Sätze:

```markdown
  1. `occ mcp_connector:purge --force` hands every Nextcloud app password of this
     app back to Nextcloud, empties every table of its database and deletes its
     encryption key.
...
## Retention

Tokens and codes carry their own expiry and are swept after it. A revoked or ended
authorization returns its app password to Nextcloud and is cleared. There is no
long lived store of personal data beyond the active connections a user has chosen
to keep.
```

Der neue Text nennt die drei automatischen Löschwege mit ihren Belegstellen
(`audit/store.py:93` 180 Tage, `:98` 100 MB, `:111`/`:939-989` Kontolöschung) und schreibt
**nicht** "der einzige automatische Löscher". Ton der Datei: Aussagesätze, konkrete Tabellen-
und Spaltennamen in Backticks, keine Werbung, keine Beteuerung.

---

### `docs/uninstall.md` (MOD, Doku/Runbook)

**Analog:** die eigene Messform.

**Prüfliste** (`uninstall.md:95-135`): numerierte Shell-Blöcke mit echter Ausgabe darunter,
Check 2 liest `oauth.sqlite3` aus einem Wegwerf-Container. Ein neuer Check für
`audit.sqlite3` folgt genau dieser Form:

```
2 $ docker run --rm -v nc_app_mcp_connector_data:/d:ro alpine:3 sh -c '
      apk add --no-cache sqlite >/dev/null 2>&1
      cp /d/oauth.sqlite3 /tmp/x.db
      for t in $(sqlite3 /tmp/x.db "select name from sqlite_master where type = '"'"'table'"'"'"); do
        printf "%s: " "$t"; sqlite3 /tmp/x.db "select count(*) from $t"
      done'
  access_tokens: 2
```

**Feldtabelle der Purge-Antwort** (`uninstall.md:162-167`): dieselbe dreispaltige Form
`| Field | Meaning | What to do about it |`. Die Zeile zu `tables_cleared` sagt künftig, dass es
die sieben Tabellen des OAuth-Speichers sind und die Audit-Datei daneben liegen bleibt.

Weitere Fundstellen mit Bestandsaussagen: Titel `:1`, Abschnittstitel `:151` ("What the occ way
leaves behind: nothing"), Versionstabelle `:47`, Gegenprüfungen nach `--rm-data` `:229-241`.
`grep -ri audit docs/uninstall.md` findet heute keinen Treffer, das ist der Ausgangszustand
für R-18-04.

---

### `docs/faq.md` (MOD, empfohlen)

**Analog:** der Eintrag selbst (`faq.md:115-123`), Form `### Frage?` plus zwei bis drei
Absätze, Kommandos in Backticks, Verweis auf das Runbook am Ende:

```markdown
### How do I remove the app and its data completely?

Two commands, in this order: `occ mcp_connector:purge --force` first, which hands
every Nextcloud app password this app created back to Nextcloud, empties every table
of its database and deletes its encryption key, then
`occ app_api:app:unregister mcp_connector --rm-data`, which removes the app together
with its data volume. ... The runbook with the
verification steps is [uninstall.md](uninstall.md).
```

Das Wort "completely" in der Überschrift ist der Grund, diesen Eintrag mitzuziehen.

---

### `README.md`, `README.de.md`, `README.fr.md` (MOD: Enterprise)

**Analog:** `README.md:512-516`, die drei Dateien tragen denselben Absatz an derselben Stelle:

```markdown
## Enterprise

Audit log, group policies and SSO through the identity provider your organisation already
runs are planned as a commercial add-on. Happy to support your organisation with evaluation
and deployment: admin@infranode.dev
```

DE `:527-531`, FR `:545-549`. Hier ist der Zeilenumbruch anders als im Manifest (Markdown,
mehrere Zeilen erlaubt), der Inhalt aber derselbe. Alle sechs Stellen zusammen ziehen, der
0.1.10-Changelog belegt, dass sie immer gemeinsam gepflegt wurden (Pitfall 17).

---

### `CHANGELOG.md` (MOD: `[Unreleased]` neu anlegen)

**Analog:** Kopf und der jüngste Eintrag (`CHANGELOG.md:1-31`):

```markdown
# Changelog

All notable changes to this app are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.11] - 2026-08-28

A release without a code change. ...

### Changed

- The paragraph about reading text written by strangers, in all three store descriptions, is
  three short sentences instead of four nested ones. ...
```

Der neue Block `## [Unreleased]` kommt zwischen Zeile 11 und 12, mit `### Added` und
`### Changed`. Form der Punkte: ein Satz, der sagt was ein Nutzer merkt, dann die Begründung,
Zeilenlänge um 100 Zeichen, Aufzählungspunkte mit zwei Leerzeichen Fortsetzungseinrückung. Die
Einträge zu 0.1.10 (`:33-45`) und 0.1.11 werden nicht umgeschrieben: ein Release-Eintrag ist
ein Datum. Der Zyklus "Deaktivieren und Aktivieren" gehört in den Text, weil Kommando und
Beschriftung erst danach in der Instanz ankommen.

---

### `tests/unit/test_exapp_audit_read.py` (NEU, test)

**Analog:** `tests/unit/test_exapp_audit_verify.py` (567 Zeilen), eins zu eins übertragbar.

**Deployment-Helfer und echter SQLite-Speicher** (`test_exapp_audit_verify.py:61-123`):

```python
def appapi_headers(user: str = "", secret: str = APP_SECRET) -> dict[str, str]:
    """What AppAPI puts on an internal call. The user is empty: this is the app context."""
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {
        "EX-APP-ID": APP_ID,
        "EX-APP-VERSION": APP_VERSION,
        "AUTHORIZATION-APP-API": token,
    }


class Deployment:
    """One process of this application with its own audit file and the check route on it."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / store.AUDIT_FILENAME
        self.store = store.AuditStore(self.path)
        self.client = TestClient(
            Starlette(routes=audit_verify.audit_verify_routes(ENV, store_provider=self._open))
        )

    async def _open(self) -> store.AuditStore:
        return self.store
```

**Eine occ-Invokation, wie AppAPI sie liefert** (`:126-142`):

```python
    options = {audit_verify.JSON_OPTION: True} if as_json else {}
    payload = body if body is not None else {"occ": {"arguments": None, "options": options}}
    sent = appapi_headers() if headers is None else headers
    return deployment.client.post(audit_verify.AUDIT_VERIFY_PATH, json=payload, headers=sent)
```

**Grenztests, die im neuen Modul dieselben sind** (`:148-215`): Proxy-Marker ergibt 404 mit
Rumpf "Not Found" und `cache-control: no-store`; fehlende AppAPI-Kopfzeilen ergeben 401 mit
`{}`; keine der beiden Antworten nennt Header, AppAPI oder einen Kontonamen; und der
`<url>`-Zähltest:

```python
def test_the_handler_path_is_declared_in_no_route_of_the_manifest() -> None:
    root = etree.parse(str(MANIFEST), hardened_parser()).getroot()
    urls = [(element.text or "").strip() for element in root.iter("url")]

    assert len(urls) == 13, urls
    bare = audit_verify.AUDIT_VERIFY_PATH.strip("/")
    for url in urls:
        assert bare not in url, f"{url} would make the check reachable from the internet"
```

Ergänzend für die Leseausgabe: ein Test mit einem Kontonamen, der einen Zeilenumbruch enthält,
und einer Behauptung über die Zeilenzahl der Antwort (die Form, die `_printable` rechtfertigt,
`audit_verify.py:284-291`); ein Test, dass ein Parameterwert aus `test_audit_store.py:44`
(`A_VALUE = "kuendigung-2026.md"`) in keiner Ausgabe vorkommt.

---

### `tests/unit/test_audit_store.py` (MOD: `read_entries`)

**Analog:** die eigenen Helfer (`test_audit_store.py:47-95`):

```python
def open_store(tmp_path: Path) -> store.AuditStore:
    return store.AuditStore(tmp_path / store.AUDIT_FILENAME)


def rows(tmp_path: Path) -> list[tuple[Any, ...]]:
    """Every row of the table, read out of the file behind the store's back."""
    conn = sqlite3.connect(tmp_path / store.AUDIT_FILENAME)
    try:
        return list(conn.execute("SELECT * FROM entries ORDER BY seq"))
    finally:
        conn.close()
```

`pytestmark = pytest.mark.anyio` (`:24`), echte Datei in `tmp_path`, kein Mock der Verbindung
("a mock of the connection would assert the mock", `:9`). Für `read_entries` gehören alle Pfade
dazu (globale Regel "nicht nur Happy Path"): leerer Speicher, Filter ohne Treffer, Limit
kleiner als die Trefferzahl, Limit über dem Höchstwert, `since`/`until` an den Rändern,
nicht-monotones `at` (WR-02) und ein Kontoname mit Steuerzeichen.

---

### `tests/unit/test_exapp_env_setup.py` (MOD: Vier-Wörter-Gate)

**Analog:** das Vokabular-Gate in derselben Datei, mit Reichweite, Meldungsform, Ausnahme und
Gegenprobe.

**Wortliste und Meldungsform** (`:1686`, `:1993-2006`):

```python
FORBIDDEN_VOCABULARY = "archiv"
...
def vocabulary_findings(text: str, name: str) -> list[str]:
    """Return one entry per line of ``text`` carrying the forbidden word, name and line first.

    Text and name are parameters and nothing is read inside, so the gate can point this at a
    real page while its counter probe points the same function at a constructed one.
    """
    needle = FORBIDDEN_VOCABULARY.casefold()
    return [
        f"{name}:{number}: {line.strip()}"
        for number, line in enumerate(text.splitlines(), start=1)
        if needle in line.casefold()
    ]
```

**Reichweite** (`:1966-1978`, `:2009-2036`):

```python
PUBLIC_MARKDOWN = (
    ROOT / "README.md",
    ROOT / "README.de.md",
    ROOT / "README.fr.md",
    ROOT / "CHANGELOG.md",
)
VOCABULARY_EXCEPTION = ROOT / "docs" / "store-submission.md"
...
def public_markdown_pages() -> list[Path]:
    docs = sorted(page for page in (ROOT / "docs").rglob("*.md") if page != VOCABULARY_EXCEPTION)
    pages = [*PUBLIC_MARKDOWN, *docs]
    assert pages, f"no public markdown found under {ROOT}"
    return pages
```

**Gate plus Manifesttext** (`:2046-2064`, `:1713-1727`, `:1787-1789`):

```python
def test_no_public_markdown_page_carries_the_forbidden_vocabulary() -> None:
    findings = [
        finding
        for page in public_markdown_pages()
        for finding in vocabulary_findings(
            page.read_text(encoding="utf-8"), page.relative_to(ROOT).as_posix()
        )
    ]

    assert findings == [], (
        f"a public page carries the forbidden word {FORBIDDEN_VOCABULARY!r}: " + "; ".join(findings)
    )
```

`element_text_without_comments(root)` (`:1713-1727`) ist der Weg über das Manifest, damit die
erklärenden Kommentare des Manifests das Gate nicht rot machen.

**Gegenprobe, ohne die der grüne Lauf nichts beweist** (`:1942-1950`, `:2067-2084`):

```python
def test_the_text_gate_rejects_the_forbidden_vocabulary(manifest_root: etree._Element) -> None:
    for element in manifest_root.findall("description"):
        if element.get("lang") is None:
            element.text = "First paragraph.\n\nThe Archive of your data stays untouched.\n"

    problems = description_problems(manifest_root)

    assert any("forbidden word" in problem for problem in problems)
```

Das neue Gate erbt Reichweite, Meldungsform und Gegenprobe, führt aber Wortformen als Regex
statt nackte Substrings (Research Muster 5: `docs/spike-opendesk.md:1707` trägt "SIEM-Ausleitung",
`docs/oauth-setup.md:204` "specification compliant", `README.fr.md:68` "conforme à la
spécification"). Die Liste bleibt in dieser Datei, kein zweites Gate-Modul (Begründung
`:1953-1961`).

---

### `tests/unit/test_exapp_admin_settings.py` (MOD: Beschriftungszusagen)

**Analog:** `:313-336`, der Test, der genau diese Beschreibung heute prüft:

```python
@pytest.mark.anyio
@respx.mock
async def test_the_audit_log_description_says_what_is_kept_and_what_is_not() -> None:
    route = respx.post(SETTINGS_URL).mock(return_value=httpx.Response(200, json={}))

    await admin_settings.register_admin_form(env=ENV)

    fields = json.loads(route.calls.last.request.content)["formScheme"]["fields"]
    description = next(field for field in fields if field["id"] == "audit_log")["description"]
    lowered = description.lower()
    assert "no parameter value" in lowered
    assert "no part of a result" in lowered
    assert "disable and enable this app again" in lowered
    # The four words AUDIT-06 keeps out of every public text of this project, checked at the
    # place a new public sentence enters it.
    for forbidden in ("revisionssicher", "ai-act", "dsgvo", "siem"):
        assert forbidden not in lowered
```

Der Docstring dieses Tests (`:316-322`) sagt selbst, dass die lange Fassung Phase 19 gehört, er
ist also mitzuziehen und nicht neu zu erfinden. Zusätzlich zu prüfen: die drei bisher
verschwiegenen Felder, der Mitbestimmungssatz, und dass das Wort `full` in keinem Feldtext und
keinem Feldtyp vorkommt (Pitfall 11). Der Nachbartest `:290-310` hält `default is False`,
`type == "checkbox"` und `"sensitive" not in json.dumps(field).lower()`, das bleibt so.

---

## Shared Patterns

### Doppelprüfung für jeden PublicFunctions-Pfad
**Quelle:** `src/mcp_connector/exapp/audit_verify.py:299-312`
**Gilt für:** `exapp/audit_read.py`
`x-origin-ip` vorhanden ergibt 404 mit Text "Not Found", danach `require_appapi`, dessen
Ablehnung 401 mit leerem JSON ergibt. Keine der beiden Antworten sagt, welche Prüfung
gesprochen hat. Identisch in `exapp/purge.py` und `exapp/lifecycle.py`.

### Antwort immer mit Status 200
**Quelle:** `src/mcp_connector/exapp/audit_verify.py:400-406` plus Docstring `:25-33`
**Gilt für:** `exapp/audit_read.py`, jeder Fehlerpfad darin
`ExAppOccService::buildCommand` verwirft den Rumpf bei jedem Status ausser 200. Auch
"konnte nicht gelesen werden" reist als 200 mit dem Satz im Rumpf. Preis (Rückgabewert immer 0)
wird im Docstring benannt und über eine JSON-Form mit einem Zustandsschlüssel abgefedert.

### Header-Konstante viermal buchstabieren statt importieren
**Quelle:** `src/mcp_connector/exapp/audit_verify.py:88-91`
**Gilt für:** `exapp/audit_read.py`
`lifecycle` importiert `occ`, `occ` importiert die Handlermodule; ein Rückimport wäre ein
Zyklus. Ein Test hält die Schreibweisen gleich (Muster: `test_exapp_audit_verify.py:193-200`
für `TRUE_WORDS`, gleiche Bauart für `HEADER_ORIGIN_IP`).

### Handlerpfad einmal, `execute_handler` abgeleitet
**Quelle:** `src/mcp_connector/exapp/occ.py:68`, `:87`, Begründung `:28-30`
**Gilt für:** `exapp/occ.py`, `exapp/audit_read.py`
`OCC_..._HANDLER = <PATH>.removeprefix("/")`. Nie ein zweitgeschriebener String.

### Zahl aus einer Zeichenkette
**Quelle:** `src/mcp_connector/config.py:433-465`
**Gilt für:** `exapp/audit_read.py` (`--limit`, `--since`)
`raw.isascii() and raw.isdigit()`, dann `int()` in `try`, dann Untergrenze. `"²".isdigit()` ist
True und `int("²")` wirft. Eine Warnung nennt Feld und Grenze, nie den Wert.

### Klammerung von Werten aus fremder Hand
**Quelle:** `src/mcp_connector/exapp/audit_verify.py:277-296` und `src/mcp_connector/audit/store.py:506-520`
**Gilt für:** jede Ausgabe von `nc_user` und `chain`
Steuerzeichen zu Leerzeichen, Weissraumläufe zu einem Leerzeichen, dann auf 80 kürzen. Achtung
R-18-06: es gibt heute drei Fassungen dieser Regel mit zwei verschiedenen Zeichenmengen. Eine
vierte macht die Lage messbar schlechter, entweder eine bestehende verwenden oder die drei
zusammenziehen.

### SQL nur aus Modulnamen, Werte nur als Platzhalter
**Quelle:** `src/mcp_connector/audit/store.py:288-301`
**Gilt für:** `audit/store.py` (`read_entries`)
Spaltenliste aus `CANONICAL_FIELDS`, `# noqa: S608` mit Begründung im selben Kommentarstil,
jeder Filterwert als `?`.

### Textkatalog statt Literal
**Quelle:** `src/mcp_connector/exapp/ui/strings.py:1-28`
**Gilt für:** jede neue Zeile, die ein Mensch liest
Ein Satz, eine Konstante, Name in `__all__`, `#:`-Kommentar mit der Begründung darüber.
`vulture` meldet sonst toten Code.

### Doku-Aussage an ein Codefaktum binden
**Quelle:** `tests/unit/test_oauth_store.py:1490-1509`
**Gilt für:** die neuen Sätze in `docs/privacy.md` und `docs/uninstall.md`

```python
    privacy = (Path(__file__).resolve().parents[2] / "docs" / "privacy.md").read_text(
        encoding="utf-8"
    )
    rows = [line for line in privacy.splitlines() if line.startswith("| Client registrations")]

    assert len(rows) == 1, "one row about the clients table"
    assert "hash" in rows[0], "and it says the secret is a hash"

    source = inspect.getsource(store)
    assert "client_secret_hash TEXT" in source, "which is what the schema really holds"
```

Dieselbe Bauart für die drei Löschwege: der Satz im Dokument und die Konstante im Code
(`RETENTION_DAYS`, `SIZE_LIMIT_BYTES`, `USER_SILENCE_DAYS`) werden im selben Test gegeneinander
gehalten, damit die neue Wahrheit die nächste Phase übersteht.

### Registrierschleife und Zähltests
**Quelle:** `tests/unit/test_exapp_lifecycle.py:425-466`, `tests/unit/test_exapp_purge.py:1067-1097`
**Gilt für:** jede Änderung an `command_schemes()`

```python
    assert route.call_count == 2
    assert sent_names(route) == [scheme["name"] for scheme in occ.command_schemes()]
```

Die Behauptungen, die aus der Liste selbst lesen (`len(occ.command_schemes())`), bleiben grün.
Die harten Zahlen (`== 2`, `side_effect` mit zwei Antworten) müssen mit.

### Dreisprachigkeit und Schreibregeln
**Quelle:** `appinfo/info.xml:77-79` / `:122-124` / `:169-171`, `README*.md`
**Gilt für:** jede öffentliche Textänderung
EN/DE/FR immer gemeinsam, echte Umlaute und Accents, keine Em-Dashes, in
`<description>` kein Backtick, keine Tabelle, kein HTML, Absätze durch Leerzeile getrennt.

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| (keine neue Datei ohne Analog) | - | - | - |

Ein Teilaspekt hat keinen Analog im Repo: **eine Doku-Aussage über einen Speicher, der eine
Löschaktion absichtlich übersteht.** `docs/privacy.md` und `docs/uninstall.md` sind heute
durchgehend so gebaut, dass am Ende nichts bleibt ("proving that nothing is left",
`uninstall.md:1`). Es gibt keinen Absatz im Repo, der eine bewusste Ausnahme von einer
Löschung erklärt. Dafür ist der Textbaustein aus `19-RESEARCH.md` §Drei automatische Löscher
die Vorlage, nicht eine bestehende Passage. Der Ton bleibt der der Datei: Aussagesätze,
konkrete Zahlen, keine Beteuerung.

Ebenfalls ohne Analog, aber im Research gemessen: **Wert-Optionen an einem occ-Kommando.**
`command_schemes()` kennt heute nur `"mode": "none"`. Die Draht-Form von `optional` steht in
`19-RESEARCH.md` Muster 2 und Codebeispiel 1, gemessen an app_api v34.0.3, nicht im Repo.

---

## Metadata

**Analog search scope:** `src/mcp_connector/exapp/`, `src/mcp_connector/audit/`,
`src/mcp_connector/config.py`, `src/mcp_connector/entry_exapp.py`, `tests/unit/`, `docs/`,
`appinfo/info.xml`, `README*.md`, `CHANGELOG.md`
**Files scanned:** 20 (davon 13 gelesen, gezielt oder vollständig)
**Pattern extraction date:** 2026-08-31
