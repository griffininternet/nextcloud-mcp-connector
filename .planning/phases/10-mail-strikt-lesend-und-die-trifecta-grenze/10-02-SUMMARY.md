---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 02
subsystem: backend
tags: [mail, ocs, client, app-detection, capabilities, read-only, respx]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-01: die gemessenen Feldwerte (specialRole als String, previewText immer gesetzt, die 500/996-Antwort der Postfachliste) und die Korrektur K1 in docs/spike-mail.md"
  - phase: 01-server-kern
    provides: "nextcloud/clients/ocs.py (ocs_get, parse_ocs, _check_transport) und nextcloud/capabilities.py mit Cache, require_app und _MISSING"
  - phase: 09-talk
    provides: "Das Baumuster der Familie: Sicherheitsparameter als Konstante, lokale Statusbehandlung, eingefrorene URL-Literale, Ziffernwächter"
provides:
  - "nextcloud/clients/mail.py mit genau vier lesenden Pfadformen, alle GET"
  - "get_message gibt (Nutzlast, body_missing) zurück; True heisst HTTP 206, also Erfolg ohne body"
  - "capabilities.load_mail als Nachfüllpfad über GET /ocs/v2.php/core/navigation/apps, in derselben Cache-Zeile"
  - "Capabilities.mail_available als dreiwertiges Feld (None heisst noch nicht gefragt) und has(\"mail\")"
  - "_MISSING[\"mail\"] mit dem Wortlaut, gegen den die Pläne 10-04 und 10-08 prüfen"
affects: [10-03, 10-04, 10-05, 10-06, 10-07, 10-08, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zweiter Erkennungskanal ohne dritten Modulzustand: lazy gefülltes Feld derselben Cache-Zeile mit dem ursprünglichen Zeitstempel"
    - "Verbots-Grep über den Codeteil einer Datei (Docstrings und Kommentare ausgeblendet), damit die Erklärung die Routen nennen darf, die der Code nicht bauen darf"
    - "Sonderstatus dort behandeln, wo er eine Bedeutung hat: 206 und 500 lokal im Client statt global im Parser"

key-files:
  created:
    - "src/mcp_connector/nextcloud/clients/mail.py"
    - "tests/unit/test_mail_client.py"
  modified:
    - "src/mcp_connector/nextcloud/capabilities.py"
    - "tests/unit/test_ocs_capabilities.py"
    - "vulture_whitelist.py"

key-decisions:
  - "get_message gibt ein Tupel (dict, bool) zurück; der zweite Wert heisst body_missing und ist genau bei HTTP 206 True"
  - "Der Nachfüllpfad heisst load_mail und hängt in require_app, nie in load: nur Mail-Nutzer zahlen den zweiten Request"
  - "Die Cache-Zeile behält beim Nachfüllen ihren ursprünglichen Zeitstempel; eine zweite Frage verlängert die Haltbarkeit einer Momentaufnahme nicht"
  - "Eine leere oder deformierte Navigationsliste ist ein ToolError mit Ausweg und nie die Aussage \"Mail fehlt\""
  - "ocs._OK_STATUS bleibt frozenset({100, 200, 201}); 206 wird lokal behandelt (T-10-12 accept)"
  - "Der Unbekannt-Name-Test in test_ocs_capabilities.py benutzt jetzt cospend, weil mail die fünfte geprüfte App ist"
  - "MAIL-01, MAIL-02 und SRV-06 bleiben Pending: dieser Plan baut den Transport, die Werkzeuge kommen in 10-04 und 10-05"

patterns-established:
  - "Ein Client, der eine Route bewusst NICHT benutzt, trägt den Grund als längsten Docstring-Absatz mit dem Suchbegriff der Entscheidung"
  - "Ein Testfile spiegelt _code_lines lokal, statt den Helfer des Gates zu importieren: ein importierter Helfer würde mit sich selbst grün bleiben"

requirements-completed: []

# Metrics
duration: 17min
completed: 2026-08-24
---

# Phase 10 Plan 02: Der Mail-Transport und der zweite Erkennungskanal, Zusammenfassung

**Der Mail-Client baut genau vier lesende Pfadformen und kann konstruktionsbedingt keine URL ohne Grenze und ohne Einzelansicht erzeugen, beide Sonderstatus sind dort behandelt, wo sie eine Bedeutung haben, und eine fehlende Mail-App ist jetzt ein Satz mit nächstem Schritt statt der Aufforderung, eine Nachricht in einer App zu suchen, die es nicht gibt.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-08-24T13:02Z
- **Completed:** 2026-08-24T13:19Z
- **Tasks:** 3
- **Files created/modified:** 5

## Accomplishments

- `capabilities.py` erkennt Mail über `GET /ocs/v2.php/core/navigation/apps`, ohne einen dritten Modulzustand anzulegen: `ALLOWED_MODULE_STATE` steht weiter bei zwei Einträgen und der Zähltest ist grün.
- `clients/mail.py` existiert mit vier Pfadkonstanten, vier `async`-Lesern und ohne einen einzigen schreibenden Aufruf. Der Verbots-Grep läuft über den Codeteil, der Docstring darf deshalb `/api/messages` und `attachment` wörtlich nennen.
- Beide Sonderstatus sind belegt: 206 ist ein Erfolg ohne Body (ein Monkeypatch beweist, dass `parse_ocs` ihn nie sieht), und HTTP 500 mit `meta.statuscode` 996 zeigt auf das Mail-Konto des Nutzers statt auf das Nextcloud-Log.
- `uv run pytest -q` ist über die ganze Default-Auswahl grün, `ruff`, `pyright` und `vulture` sauber, `check_tool_budget.py` meldet unverändert 14358 Bytes bei 20 Werkzeugen: dieser Plan registriert nichts.

## Die Schnittstellen, gegen die 10-04 und 10-05 bauen

### Die vier Leser, wörtliche Signaturen

```python
async def get_accounts(client: httpx.AsyncClient, creds: Credentials) -> list[dict[str, Any]]

async def get_mailboxes(
    client: httpx.AsyncClient, creds: Credentials, account_id: str | int
) -> list[dict[str, Any]]

async def get_messages(
    client: httpx.AsyncClient,
    creds: Credentials,
    mailbox_id: str | int,
    *,
    limit: int,
    filter_string: str | None = None,
    cursor: int | None = None,
) -> list[dict[str, Any]]

async def get_message(
    client: httpx.AsyncClient, creds: Credentials, message_id: str | int
) -> tuple[dict[str, Any], bool]
```

Der Parameter heisst `filter_string` und nicht `filter`, weil `filter` ein eingebauter Name
ist; in der URL erscheint er als `filter`. `cursor=None` bedeutet erste Seite, ein negativer
Cursor erscheint als `0`. `limit` ist Keyword ohne Vorgabewert und wird auf 1 bis
`MAX_MESSAGES` (50) gekappt.

### Die gewählte Rückgabeform von `get_message` (für Plan 10-05)

**Ein Tupel `(message, body_missing)`.** Der zweite Wert ist genau dann `True`, wenn die App
mit `PARTIAL` (206) geantwortet hat: die Nachricht wurde gefunden und ist vollständig **ausser**
`body`, weil sie nicht entschlüsselt werden konnte. Bei 200 ist er `False`. Die Form spiegelt
`talk.get_messages`, das ebenfalls ein Tupel aus Nutzlast und Nebenaussage liefert, und sie ist
bewusst kein Sentinel im Dictionary: ein fehlendes `body`-Feld allein wäre von einer Mail ohne
Textkörper (gemessen: `body` ist dann `""`, nicht abwesend) nicht zu unterscheiden.

Plan 10-05 liest daraus: `body_missing is True` heisst "verschlüsselt, kein Text vorhanden" und
ist **kein** Fehler und **keine** Kappung. Der Kappungsmarker der 32-KiB-Grenze aus 10-01 ist
eine andere Aussage und darf mit dieser nicht zusammenfallen.

### Konstanten

| Name | Wert |
|------|------|
| `ACCOUNTS_PATH` | `/apps/mail/account/list` |
| `MAILBOXES_PATH` | `/apps/mail/ocs/mailboxes` |
| `MESSAGES_PATH` | `/apps/mail/ocs/mailboxes/{mailbox}/messages` |
| `MESSAGE_PATH` | `/apps/mail/message/{message}` |
| `VIEW` | `singleton` |
| `MAX_MESSAGES` | `50` |
| `PARTIAL` | `206` |

### Der Nachfüllpfad in `capabilities.py`

Die Funktion heisst **`load_mail(clients: NcClients) -> Capabilities`**. Sie ruft `load`, gibt
bei `mail_available is not None` unverändert zurück, holt sonst `NAVIGATION_PATH`
(`/core/navigation/apps`), setzt das Feld per `dataclasses.replace` und schreibt das Ergebnis
unter denselben Cache-Schlüssel mit dem **ursprünglichen** Zeitstempel zurück. Aufgerufen wird
sie nur aus `require_app(clients, "mail")`; jede andere Familie zahlt den zweiten Request nie.

Die Erkennungsregel: ein Eintrag zählt, wenn `entry.get("app")` **oder** `entry.get("id")`
gleich `mail` ist. Kein Filter auf `type`. Eine leere Liste, ein Objekt statt einer Liste und
`null` sind ein `ToolError` mit Ausweg und ergeben **nicht** `mail_available = False`.

### Der Wortlaut von `_MISSING["mail"]`

```
message: "The Mail app is not available on this Nextcloud."
hint:    "Ask an administrator to enable the Mail app for this account."
```

Keine der beiden Zeichenketten enthält das Wort "Navigation": der Weg ist ein
Implementierungsdetail, die Meldung sagt, was fehlt und was zu tun ist. Der Ziffernwächter
nennt dagegen ein Werkzeug: `"Use an id exactly as mail_browse reports it; Mail addresses by
number."` Plan 10-04 muss das Werkzeug also wirklich `mail_browse` nennen.

## Task Commits

1. **Task 1: Der zweite Erkennungskanal in derselben Cache-Zeile** - `f869d2e` (feat)
2. **Task 2: Der Mail-Client, vier Leseformen und die zwei Sonderstatus** - `2384bd9` (feat)
3. **Task 3: Unit-Abdeckung des Clients, behauptet an der gebauten Anfrage** - `0231d29` (test)

## Files Created/Modified

- `src/mcp_connector/nextcloud/clients/mail.py` - neu; Modul-Docstring mit dem Ersetzbarkeits-Absatz (Suchbegriff `SCOPE_IGNORE`), vier Pfadkonstanten, `VIEW`, `MAX_MESSAGES`, `PARTIAL`, vier Leser, `_path_id`, `_check_mail_server`, `_partial_message`, `_as_list`, `_as_dict`
- `src/mcp_connector/nextcloud/capabilities.py` - `NAVIGATION_PATH`, `mail_available`, `has("mail")`, `_MISSING["mail"]`, `load_mail`, Mail-Zweig in `require_app`, `_navigation_lists_mail`; Modul-Docstring auf fünf optionale Apps nachgezogen
- `tests/unit/test_mail_client.py` - neu; 35 Testfälle, vier eingefrorene URL-Literale, der Verbots-Grep über den Codeteil samt Gegenprobe auf den Docstring
- `tests/unit/test_ocs_capabilities.py` - Mail-Block (Navigation in vier Zuständen, TTL-Beweis, kein Navigations-Request für Talk), Unbekannt-Name-Test auf `cospend` umgestellt
- `vulture_whitelist.py` - drei geparkte Leser, siehe Deviations

## Decisions Made

- **`(payload, body_missing)` statt eines Sentinels.** Ein fehlendes `body`-Feld allein wäre nicht von einer Mail ohne Textkörper zu unterscheiden; 10-01 hat gemessen, dass eine Mail ohne Body `body: ""` liefert und nicht das Feld weglässt.
- **`_OK_STATUS` bleibt unverändert.** 206 hat diese Bedeutung auf genau einer Route. Eine globale Erweiterung wäre für jede andere Familie eine stillschweigende Lockerung, genau wie Phase 9 die 304 lokal gehalten hat (T-10-12, bewusst akzeptiert).
- **Der 500er-Zweig steht vor `parse_ocs`, nicht danach.** `ocs._check_transport` fängt jeden Status ab 500 vor dem Envelope ab; ein Zweig, der auf eine ausgelöste `ToolError` wartet, käme nie zum Zug.
- **`_partial_message` liest den Envelope lokal.** Für den 206er gibt es keinen Weg über `parse_ocs`, ohne dessen Statusprüfung für alle zu ändern. Die zehn Zeilen sind auf genau einen Status auf genau einer Route beschränkt und tragen den Grund im Docstring.
- **Der Ziffernwächter deckt auch `account_id` ab.** Der Plan nennt Postfach- und Nachrichten-Id; die Konto-Id kommt aus derselben Quelle (einer Modellantwort) und geht in eine Query. Ein dritter Test belegt sie mit null Requests (Rule 2).
- **`load_mail` schreibt nur zurück, wenn die Cache-Zeile noch existiert.** Wird der Cache zwischen `load` und dem Rückschreiben geleert, entsteht keine neue Zeile: der Cache darf jederzeit leer sein (D-20), und ein Nachfüllpfad, der ihn wiederbelebt, wäre das Gegenteil davon.
- **MAIL-01, MAIL-02 und SRV-06 bleiben Pending.** Die Frontmatter des Plans nennt sie, aber dieser Plan registriert kein Werkzeug und führt keinen Live-Nachweis: die Aussagen "Nutzer kann seine Mail lesen" und "alle drei Familien degradieren sauber" lösen 10-04, 10-05 und 10-08 ein. Ein Abhaken hier wäre eine unwahre Zeile in REQUIREMENTS.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Vulture meldet die drei Leser ohne Aufrufer**
- **Found during:** Task 2 (Verifikation `uv run vulture src/mcp_connector vulture_whitelist.py`)
- **Issue:** `get_accounts`, `get_mailboxes` und `get_message` haben bis Plan 10-04 keinen Produktionsaufrufer, also meldet vulture sie bei voller Konfidenz. Das Akzeptanzkriterium von Task 3 erwartete "ohne neuen Whitelist-Eintrag"; das ist für einen Plan, der den Transport vor seinem Aufrufer baut, konstruktionsbedingt nicht erreichbar. `get_messages` ist nicht betroffen, weil derselbe Name in der Talk-Familie einen Aufrufer hat.
- **Fix:** Drei Einträge in `vulture_whitelist.py`, in genau der Form, die die Datei für diesen Fall selbst vorschreibt und die schon zweimal benutzt wurde (Plan 08-02 für Tables, Plan 09-01 für Talk): mit Begründung, mit dem Plan, der sie auflöst (10-04), und mit dem Hinweis, warum `get_messages` bewusst fehlt.
- **Files modified:** `vulture_whitelist.py`
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` ist grün.
- **Committed in:** `2384bd9`

**2. [Rule 2 - Missing critical] Der Ziffernwächter fehlte auf der Konto-Id**
- **Found during:** Task 2
- **Issue:** Der Plan nennt `mailboxId` und die Nachrichten-Id. `accountId` kommt aus derselben Quelle (einer Modellantwort) und wird Teil der URL; ohne Wächter erreichte ein erfundener Wert Nextcloud, wenn auch nur als Query.
- **Fix:** `_path_id(account_id, "mail account id")` in `get_mailboxes`, plus ein eigener Test mit `len(route.calls) == 0`.
- **Files modified:** `src/mcp_connector/nextcloud/clients/mail.py`, `tests/unit/test_mail_client.py`
- **Committed in:** `2384bd9`, `0231d29`

**3. [Rule 1 - Bug] Der Unbekannt-Name-Test prüfte ab jetzt eine bekannte App**
- **Found during:** Task 1
- **Issue:** `test_has_refuses_an_app_this_server_does_not_check` benutzte wörtlich `mail` als Beispiel für einen unbekannten Namen. Mit Mail als fünfter geprüfter App wäre der Test rot geworden, und der Kommentar in der Datei sagt selbst, dass genau das schon einmal passiert ist (bei `spreed`).
- **Fix:** Beispielname auf `cospend` umgestellt, plus eine Zeile, die `has("mail")` positiv als "geprüft, und unbeantwortet heisst abwesend" behauptet.
- **Files modified:** `tests/unit/test_ocs_capabilities.py`
- **Committed in:** `f869d2e`

### Nicht abgewichen

Keine Rule-4-Frage. `pyproject.toml`, `uv.lock`, `ids.py`, `tools/chatgpt.py`, `tools/marks.py`
und `appinfo/info.xml` sind unberührt (`git diff --stat` gegen `HEAD` leer), es gibt kein
`uv add` und keine neue Sprachabhängigkeit (T-10-SC).

## Known Stubs

Keine. Die vier Leser sind vollständig verdrahtet und gegen `respx` belegt; was fehlt, ist ihr
Aufrufer, und der ist der erklärte Gegenstand von Plan 10-04 (`tools/mail.py`) und Plan 10-05
(`fetch`-Zweig `mail:`).

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run pytest -q` (Default-Auswahl) | grün, inklusive `test_mail_client.py` (35) und `test_ocs_capabilities.py` (44) |
| `uv run ruff check .` / `ruff format --check .` | grün, 189 Dateien |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün |
| `uv run pytest tests/contract/test_no_destructive_calls.py -q` | grün, weiterhin genau zwei erlaubte Modulzustände |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 14358 Bytes, 20 Werkzeuge (unverändert) |
| Formprüfung des Clients (vier Pfade, Signatur, Verbots-Grep über den Codeteil) | `mail client shape ok` |
| Formprüfung der Capabilities (Pfad, Feld, `_MISSING`, ValueError) | `capabilities ok` |

## Next Steps

- Plan 10-03 (Filter- und HTML-Schicht) und Plan 10-04 (`tools/mail.py`) bauen auf den oben
  wörtlich genannten Signaturen auf; `mail_browse` ist der Name, den der Ziffernwächter im
  Hinweis führt, und er ist damit festgelegt.
- Plan 10-04 löst die drei Einträge in `vulture_whitelist.py` auf, so wie 08-03 und 09-03 es
  für ihre Familien getan haben.
- Plan 10-06 zieht die Aussage "genau vier Pfadformen, alle GET" aus dem Unit-Test in das
  Contract-Gate und braucht dafür die Gegenprobe gegen `POST /ocs/v2.php/apps/mail/message/send`.

## Self-Check: PASSED

Alle behaupteten Dateien existieren (`clients/mail.py`, `tests/unit/test_mail_client.py`,
diese Zusammenfassung), alle drei Task-Commits sind im Log auffindbar (`f869d2e`, `2384bd9`,
`0231d29`), und die beiden Testdateien laufen zusammen mit 79 grünen Fällen.
