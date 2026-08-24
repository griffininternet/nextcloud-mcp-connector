---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 04
subsystem: backend
tags: [mail, tools, browse, filtergrammatik, paging, projektion, read-only, respx]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-01: die zwölf gemessenen Filterläufe, specialRole als String, previewText nie null, die Selbstkappung der Vorschau bei rund 250 Zeichen"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-02: clients/mail.py mit vier Lesern und capabilities.load_mail plus _MISSING[\"mail\"]"
  - phase: 09-talk
    provides: "Das Baumuster: browse mit level-Enum, Byte-Kappe, Cursor mit Scope, Fremdtext durch marks.without_marks, Antwort-Umschlag"
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "Das Vorbild für drei Ebenen mit Pflicht-Id auf den tieferen zwei"
provides:
  - "tools/mail.py mit mail_browse über die drei Ebenen accounts, mailboxes und messages"
  - "FILTER_TYPES als Positivliste plus FLAG_VALUES, geprüft vor dem ersten Request"
  - "Die drei Projektionen (Konto, Postfach, Envelope) mit ihren endgültigen Feldnamen"
  - "Cursor-Scope-Schlüssel m mit der mailbox_id, Position o als dateInt der ältesten Nachricht"
  - "MAX_PREVIEW_BYTES = 400 als Byte-Kappe der Vorschau"
affects: [10-05, 10-06, 10-07, 10-08, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Positivliste über Werten aus einer Modellantwort, geprüft vor der App-Erkennung, weil die stille Verwerfung der Fremd-App teurer ist als jeder Fehler"
    - "Ein Feld mit zwei deklarierten Typen (int ODER str) bekommt einen eigenen Leser statt _number oder _text"
    - "Ein Eintrag ohne adressierbare Id fällt aus der Liste, weil Adressierbarkeit der Zweck der Ebene ist"

key-files:
  created:
    - "src/mcp_connector/tools/mail.py"
    - "tests/unit/test_mail_tools.py"
  modified:
    - "vulture_whitelist.py"

key-decisions:
  - "MAX_PREVIEW_BYTES = 400: die App kappt previewText selbst bei rund 250 Zeichen (gemessen 10-01), 400 Bytes lassen eine deutsche Vorschau dieser Länge unangetastet und sind die Absicherung gegen eine Fassung, die nicht mehr kappt"
  - "Cursor-Scope-Schlüssel ist m (mailbox), Position o ist der dateInt der ältesten Nachricht der laufenden Seite"
  - "FLAG_VALUES = unread, read, starred, answered, important; die drei Sonderformen der Wichtigkeits-Klassifikation werden abgelehnt"
  - "tags: wird durchgereicht und nicht auf Ziffern geprüft; die Korrektur aus 10-01 (numerische Tag-Id statt IMAP-Label) steht als Dokumentation im Konstanten-Kommentar"
  - "Der Filter wird an beliebigem Leerraum zerlegt, nicht nur am Leerzeichen: eine Schattierung strenger als die App, und die sichere Richtung"
  - "Ein Envelope ohne numerische databaseId fällt aus der Liste, wie eine Talk-Konversation ohne Token"
  - "date ist ein ISO-Zeitstempel und nicht die Unix-Sekunde wie bei Talk: eine Mail hat genau einen Zeitstempel pro Envelope, und der wird von Menschen gelesen"
  - "MAIL-01 und MAIL-03 bleiben Pending: dieser Plan registriert kein Werkzeug (10-06) und führt keinen Live-Nachweis (10-08)"

patterns-established:
  - "Die teuerste Eigenschaft einer Werkzeugfamilie kann eine Ablehnung sein; dann hat die Testdatei mehr Ablehnungs- als Happy-Path-Tests"
  - "Ein honest limit steht im Docstring der Ebene, die es hat, und wird nicht heimlich repariert"

requirements-completed: []

# Metrics
duration: 22min
completed: 2026-08-24
---

# Phase 10 Plan 04: Das eine Werkzeug der Mail-Familie, Zusammenfassung

**`mail_browse` geht Konten, Postfächer und Envelopes über einen Aufruf mit drei Ebenen ab, prüft den Filter gegen eine Positivliste, bevor die App ihn stillschweigend verwerfen kann, und benennt jede Kappung als Feld statt als Marker in fremdem Text.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-24T13:42Z
- **Completed:** 2026-08-24T14:04Z
- **Tasks:** 3
- **Files created/modified:** 3

## Accomplishments

- `tools/mail.py` existiert mit 571 Zeilen, drei Ebenen, einer Filtergrammatik mit vier Ablehnungsarten und ohne einen einzigen schreibenden Aufruf. Die Formprüfung des Plans (`ocs_post`, `.post(`, `.put(`, `.patch(`, `.delete(` und ein `body:`-Filter im Code) ist grün.
- Die Prüfreihenfolge steht: Ebene, Cursor-Ablehnung, Filter-Ablehnung auf der falschen Ebene, Filter-Grammatik, Limit-Kappung, `require_app`, Dispatch, Pflicht-Id im Zweig. Die drei teuersten Ablehnungen kosten null Requests.
- `tests/unit/test_mail_tools.py` mit **38 Testfunktionen** (68 Fällen) ist grün, `uv run pytest -q` über die ganze Default-Auswahl ebenfalls, `ruff`, `pyright` und `vulture` sauber.
- Die zwei geparkten Whitelist-Einträge `get_accounts` und `get_mailboxes` sind aufgelöst; `get_message` bleibt mit dem Vermerk stehen, dass Plan 10-05 ihn löst.

## Die Schnittstelle, gegen die 10-06 und 10-07 bauen

### Die Signatur von `browse`

```python
async def browse(
    clients: NcClients,
    level: str = "accounts",
    account_id: str | None = None,
    mailbox_id: str | None = None,
    filter: str | None = None,  # noqa: A002 - the name of the parameter in the Mail app
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, Any]
```

Der Parameter heisst **`filter`** und trägt ein `# noqa: A002`, weil er einen eingebauten
Namen verdeckt. Das Vorbild ist `reg_chatgpt.fetch(id: str)`, das dasselbe für den
OpenAI-Kontrakt tut: der Name des Parameters gehört der fremden Schnittstelle und nicht uns.

### Konstanten

| Name | Wert |
|------|------|
| `APP` | `"mail"` |
| `LEVELS` | `("accounts", "mailboxes", "messages")` |
| `DEFAULT_LIMIT` / `MAX_LIMIT` | `20` / `50` |
| `MAX_PREVIEW_BYTES` | `400` |
| `FILTER_TYPES` | `{"is", "not", "from", "subject", "tags", "start", "end"}` |
| `FLAG_VALUES` | `{"unread", "read", "starred", "answered", "important"}` |
| `_SCOPE` (Cursor-Schlüssel) | `"m"` |
| `_ID_KIND` | `"mail"` |

**`MAX_PREVIEW_BYTES = 400`,** und die Zahl ist eine Einstellung, keine Messung. Plan 10-01
hat gemessen, dass die App `previewText` selbst bei rund 250 Zeichen kappt (beide Newsletter
trugen exakt 251 Zeichen bei 25 KB beziehungsweise 229 KB Text). 400 Bytes lassen eine
deutsche Vorschau dieser Länge unangetastet durch und sind die Absicherung gegen eine
Mail-Fassung, die nicht mehr selbst kappt. Im schlimmsten Fall kostet ein volles Fenster
50 mal 400 Bytes Vorschau.

### Die erlaubten Werte für `is:` und `not:`

`unread`, `read`, `starred`, `answered`, `important`.

`unread` und `read` sind gegen die Instanz gemessen (sechs Treffer und null Treffer auf
denselben sechs Nachrichten, Plan 10-01); `starred`, `answered` und `important` stammen aus
dem Parser der App. **Abgelehnt** werden `is:is_important`, `is:pi-important` und
`is:pi-other`: undokumentierte Interna der Wichtigkeits-Klassifikation.

### Die vier Ablehnungsarten der Grammatik

| Eingabe | Meldung nennt | Hinweis nennt |
|---------|---------------|---------------|
| Token ohne Doppelpunkt (`subject:Rechnung Mai`) | den Token, "carries no colon" | die sieben Typen plus die Prozentkodierung |
| unbekannter Typ (`foo:bar`, `body:x`, `match:x`, `mentions:true`) | den abgelehnten Typ | die sieben erlaubten Typen |
| leerer Wert (`subject:`) | "has no value" | dieselben sieben |
| ISO-Wert bei `start:`/`end:` | den Wert, "is not a Unix timestamp" | Unix-Sekunden und die Spalte `sent_at` |
| unbekannter Flag-Wert (`is:ungelesen`, `is:pi-other`) | den Wert | die fünf erlaubten Zustände |

Ein leerer Filter und ein Filter aus Leerraum werden zu `None` und erscheinen nicht in der
URL. Ein Filter auf `level="accounts"` oder `level="mailboxes"` wird abgelehnt, nicht
ignoriert, und zwar vor `require_app`.

`tags:` nimmt die **numerische Tag-Id** und nicht das IMAP-Label (Messkorrektur aus 10-01).
Der Wert wird durchgereicht und nicht auf Ziffern geprüft; die Aussage steht im
`#:`-Kommentar über `FILTER_TYPES` und gehört damit in die Grammatik-Dokumentation von
Plan 10-07.

### Die drei Projektionen, exakte Feldnamen

**Konto** (`level="accounts"`): `id` (Zahl), `email`, `delegated` (nur wenn wahr),
`aliases` (Anzahl, nur wenn mindestens eine). Kein Kontoname, kein IMAP-Host.

**Postfach** (`level="mailboxes"`): `id` (die `databaseId` als Zahl), `name`, `unread`,
`delimiter`, `special_role` (nur wenn vorhanden), `display_name` (nur wenn es von `name`
abweicht). Das base64-Feld `id` der App erscheint nicht.

**Envelope** (`level="messages"`): `id` (`mail:<databaseId>`), `subject`, `from`
(`label <email>`), `date` (ISO in UTC aus `dateInt`, fehlt bei unbrauchbarem Zeitstempel),
`preview` (fehlt, wenn es keinen Textkörper gibt), `unread` (aus `not flags.seen`),
`truncated` (nur wenn die Vorschau gekappt wurde), `has_attachments` (nur wenn wahr).

**Antwort-Umschlag:** `level`, `count`, `results`, dazu `truncated` bei einer Kappung; auf der
Nachrichtenebene zusätzlich `mailbox_id` und `next`.

### Der Cursor

`paging.encode_cursor({"o": <dateInt der ältesten Nachricht der Seite>, "m": <mailbox_id>})`.
Gelesen wird er mit `decode_cursor`, `check_scope(state, "m", mailbox, "mailbox")` und
`read_offset`. `truncated` steht, sobald das Fenster voll zurückkam; `next` nur, wenn die
Seite einen positiven Zeitstempel trägt, denn ein Cursor `0` würde die erste Seite noch
einmal ausgeben und wäre genau die Schleife, die IN-04 verbietet.

### Die zwei honest limits im Docstring der Ebene

1. Der Cursor der App filtert `sent_at <` **strikt**: zwei Mails in derselben Sekunde an einer
   Seitengrenze bedeuten, dass die zweite ausfällt. Benannt, nicht repariert, wie beim
   halboffenen Kalenderfenster.
2. Die App setzt zwei Filter selbst, unabhängig vom `filter`-Parameter: in einem
   Flagged-Postfach nur markierte Nachrichten, ausserhalb des Papierkorbs keine gelöschten.

## Task Commits

1. **Task 1: Konstanten, der Ebenen-Dispatch und die zwei flachen Ebenen** - `b114baa` (feat)
2. **Task 2: Die Ebene messages, die Filter-Positivliste und der Cursor** - `0b25205` (feat)
3. **Task 3: Unit-Abdeckung des Werkzeugs** - `972068d` (test)

## Files Created/Modified

- `src/mcp_connector/tools/mail.py` - neu, 571 Zeilen; Modul-Docstring mit den vier Fettblöcken, Konstanten mit Begründung, `browse`, `_accounts`/`_account`, `_mailboxes`/`_mailbox`, `_special_role`, `_messages`/`_message`, `_checked_filter`, `_sender`, `_date`, `_capped`, `_text`, `_number`, `_envelope`
- `tests/unit/test_mail_tools.py` - neu, 38 Testfunktionen über die drei Ebenen, die Grammatik, den Cursor und den Fremdtext
- `vulture_whitelist.py` - `get_accounts` und `get_mailboxes` aufgelöst, `get_message` bleibt mit Verweis auf Plan 10-05

## Decisions Made

- **`MAX_PREVIEW_BYTES = 400`.** Begründet durch die Messung: die App kappt selbst bei rund 250 Zeichen, also greift diese Kappe im Normalfall nie und ist die Absicherung gegen die Fassung, die es nicht mehr tut.
- **Der Cursor-Schlüssel ist `m`.** Ein Buchstabe im Stil der Familie (`c` bei Talk), und der Scope ist die `mailbox_id`, weil eine Seite genau zu einem Postfach gehört.
- **`date` ist ISO und nicht die Unix-Sekunde.** Talk reicht seine Zahlen durch, weil eine Konversation mehrere Zeitfelder hat; ein Envelope hat genau eines, und die 25 Bytes pro Nachricht kaufen einen Wert, den niemand mehr umrechnen muss.
- **Ein Envelope ohne numerische `databaseId` fällt aus der Liste.** Dieselbe Entscheidung wie bei einer Talk-Konversation ohne Token: adressierbar zu sein ist der Zweck dieser Ebene.
- **Der Filter wird an beliebigem Leerraum zerlegt.** Die App zerlegt am Leerzeichen; ein Tabulator im Wert wird hier als zwei Token gelesen und abgelehnt, wo die App ihn durchgereicht hätte. Das ist die strengere und damit sichere Richtung, und ein Wert mit Leerraum muss ohnehin prozentkodiert sein. Der Absatz steht im Docstring von `_checked_filter`.
- **`tags:` wird nicht auf Ziffern geprüft.** Die Messung aus 10-01 (numerische Tag-Id, nicht das IMAP-Label) steht als Dokumentation im Konstanten-Kommentar; eine Ablehnung wäre über die Vorgaben des Plans hinausgegangen und hätte die Grammatik enger gemacht als die drei Sätze, die Plan 10-07 dokumentieren soll.
- **MAIL-01 und MAIL-03 bleiben Pending.** Die Frontmatter des Plans nennt beide, aber `mail_browse` ist noch nicht registriert (Plan 10-06) und noch nicht gegen eine echte Instanz gelaufen (Plan 10-08). Ein Abhaken hier wäre eine unwahre Zeile in REQUIREMENTS.md, genau wie in 10-01 und 10-02.

## Deviations from Plan

### Bewusste Abweichungen von der Planvorgabe

**1. Die Envelope-Projektion und der Cursor entstanden in Task 1, nicht in Task 2**

Der Plan schneidet Task 1 auf "die zwei flachen Ebenen" und legt die Nachrichtenebene in
Task 2. Task 1 verlangt aber gleichzeitig, dass `LEVELS` alle drei Ebenen nennt und die
Signatur `filter` und `cursor` trägt (die Formprüfung von Task 1 prüft beides). Ein Zweig
`level="messages"`, der in Task 1 auf eine noch nicht existierende Funktion zeigt, wäre weder
typprüfbar noch ehrlich. Deshalb trägt der Commit von Task 1 die Nachrichtenebene samt
Projektion und Cursor bereits vollständig, und Task 2 ergänzt genau das, was der Plan als
Task-2-Gegenstand benennt: `FILTER_TYPES`, `FLAG_VALUES`, die Prüffunktion, die Ablehnung auf
der falschen Ebene und die zwei honest limits. Kein Scope-Zuwachs, nur eine andere
Commit-Grenze; das Endergebnis erfüllt beide Akzeptanzlisten.

**2. `# noqa: A002` am Parameter `filter`**

Nicht im Plan genannt, aber unvermeidbar: `ruff` prüft mit der Regelgruppe `A`
(flake8-builtins), und `filter` verdeckt einen eingebauten Namen. Der Name ist von der
Mail-App und vom Werkzeugschema vorgegeben, also steht die Ausnahme mit Begründung an der
Zeile, nach dem bestehenden Vorbild `reg_chatgpt.fetch(id: str)`.

**3. `vulture_whitelist.py` wurde in Task 1 statt in Task 3 angefasst**

Die Auflösung gehört an den Commit, der den Aufrufer bringt. `get_accounts` und
`get_mailboxes` bekommen ihren Aufrufer in Task 1, also verlassen sie die Liste dort. Die
Akzeptanz von Task 3 ("vulture grün, ohne neuen Whitelist-Eintrag") ist erfüllt: es kam kein
Eintrag dazu, es gingen zwei weg.

### Auto-fixed Issues

Keine. Es gab einen falsch gerechneten ISO-Zeitstempel in der ersten Fassung eines Tests
(`1755181000` ist `14:16:40Z`, nicht `13:36:40Z`); das war ein Fehler in der Erwartung des
Tests, kein Fehler im Produktionscode, und er wurde vor dem Commit korrigiert.

### Nicht abgewichen

Keine Rule-4-Frage. `pyproject.toml`, `uv.lock`, `ids.py`, `tools/chatgpt.py`, `server/` und
`appinfo/info.xml` sind unberührt (`git diff --stat` gegen `HEAD` leer), es gibt kein
`uv add` und keine neue Sprachabhängigkeit (T-10-SC). `ids.py` wird **gelesen** (für
`ids.SEPARATOR`) und nicht geändert: `ids.encode_mail` und der `mail`-Zweig von `ids.parse`
gehören zu Plan 10-05, und bis dahin baut `tools/mail.py` das Präfix aus dem Separator jenes
Moduls statt aus einer zweiten Kopie des Doppelpunkts.

## Known Stubs

Keine. `mail_browse` ist vollständig verdrahtet und gegen `respx` belegt; was fehlt, ist die
Registrierung als MCP-Werkzeug, und die ist der erklärte Gegenstand von Plan 10-06.

## Threat Flags

Keine neue Angriffsfläche ausserhalb des `<threat_model>` dieses Plans. Kein neuer Endpunkt,
kein Schreibpfad, kein Dateizugriff, keine Schemaänderung an einer Vertrauensgrenze. Die acht
`mitigate`-Dispositionen sind umgesetzt (T-10-19 bis T-10-25 und T-10-27), T-10-26 ist als
honest limit im Docstring benannt und damit wie geplant `accept`.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run pytest -q` (Default-Auswahl) | grün, inklusive `test_mail_tools.py` (68 Fälle aus 38 Funktionen) |
| `uv run ruff check .` / `ruff format --check .` | grün, 193 Dateien |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün, ohne neuen Eintrag |
| `uv run pytest tests/contract -q` | grün, die Werkzeugoberfläche ist unverändert |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 14358 Bytes, 20 Werkzeuge (unverändert, dieser Plan registriert nichts) |
| Formprüfung Task 1 (Konstanten, Signatur, Verbots-Grep) | `mail tools skeleton ok` |
| Formprüfung Task 2 (`FILTER_TYPES`, vier `paging`-Aufrufe, `sent_at`) | `filter and cursor wired` |
| Grep-Gate Task 3 (sieben Nadeln, `def test_` >= 25, `databaseId` plus `uid`) | grün, 38 Testfunktionen |
| `git diff --stat` gegen pyproject, uv.lock, ids.py, chatgpt.py, server/, info.xml | leer |

## Next Steps

- **Plan 10-05** löst den letzten Whitelist-Eintrag (`get_message`) auf, setzt die Volltext-Kappe auf 32768 Bytes und ergänzt `ids.encode_mail` plus den `mail`-Zweig von `ids.parse`; die Zeile in `tools/mail.py`, die das Präfix heute lokal baut, wandert dann dorthin.
- **Plan 10-06** baut die Feldbeschreibungen des Werkzeugschemas aus den drei Projektionen oben und hebt das Budget-Gate; der Name `mail_browse` ist seit 10-02 durch den Ziffernwächter festgelegt.
- **Plan 10-07** dokumentiert die Filtergrammatik in drei Sprachen; die Quelle dafür sind `FILTER_TYPES`, `FLAG_VALUES`, die drei Zerlegungsregeln im Konstanten-Kommentar und die zwei honest limits.
- **Plan 10-08** erwartet im Live-Lauf ein Postfach mit `special_role="inbox"` und `unread=6` sowie sechs Envelopes.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*

## Self-Check: PASSED

Alle drei behaupteten Dateien existieren (`src/mcp_connector/tools/mail.py`,
`tests/unit/test_mail_tools.py`, diese Zusammenfassung), alle drei Task-Commits stehen im Log
(`b114baa`, `0b25205`, `972068d`), und das Dokument enthält keine Em-Dashes.
