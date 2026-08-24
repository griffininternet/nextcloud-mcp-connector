---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 06
subsystem: api
tags: [mail, registrierung, literal-enum, token-budget, contract-test, schreibverbot, gegenprobe]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-02: clients/mail.py mit den vier lesenden Pfadkonstanten und keinem Schreibpfad"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-04: tools/mail.browse mit drei Ebenen, DEFAULT_LIMIT 20, MAX_LIMIT 50, FILTER_TYPES"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-05: mail als sechstes Id-Kind, damit fetch(mail:<databaseId>) den Volltext liefert"
  - phase: 09-talk
    provides: "reg_talk.py als vollständige Formvorlage und der Talk-Block des Destruktiv-Gates"
provides:
  - "server/reg_mail.py: mail_browse als einundzwanzigstes Werkzeug, READ_ONLY, ohne Output-Schema, Literal-Enum mit drei Ebenen"
  - "BUDGET_BYTES 18500 auf der Messung 15736 vom 2026-08-24, als Zwischenstand für TOOL-15 markiert"
  - "Die Zahl 21 identisch in test_tool_surface.py, acceptance_all_tools.py und README.md"
  - "Neun Mail-Nadeln in FORBIDDEN, MAIL_ROUTES mit neun Gegenproben, ALLOWED_MAIL_ROUTES mit vier Formen"
  - "Der Nur-GET-Test über clients/mail.py und tools/mail.py"
affects: [10-07, 10-08, phase-11-tool-15, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Registrierung durch die Existenz einer reg_*-Datei; die eingefrorenen Zahlen steigen im selben Commit"
    - "Eine Budget-Anhebung nur gegen eine datierte Messung, ältere Messzeilen bleiben lesbar"
    - "Zu grosses Werkzeug: die Beschreibung wird gekürzt, nie die Grenze angehoben (A5)"
    - "Ein Schreibverbot besteht aus Nadel plus Gegenprobe plus Positivliste plus Nur-GET-Aussage"

key-files:
  created:
    - "src/mcp_connector/server/reg_mail.py"
  modified:
    - "scripts/check_tool_budget.py"
    - "scripts/acceptance_all_tools.py"
    - "tests/contract/test_tool_surface.py"
    - "tests/contract/test_no_destructive_calls.py"
    - "vulture_whitelist.py"
    - "README.md"

key-decisions:
  - "mail_browse war zuerst 1585 Bytes und damit über MAX_TOOL_BYTES 1400; gekürzt wurde die Beschreibung, nicht die Grenze (A5). Endstand 1377 Bytes, 23 Bytes unter der Decke"
  - "BUDGET_BYTES 15000 -> 18500: Messung 15736 plus 15 Prozent = 18096, aufgerundet auf die nächsten 500; als Zwischenstand markiert, den TOOL-15 in Phase 11 neu verankert (Falle 14)"
  - "MAX_TOOL_BYTES bleibt 1400 und ist der eigentliche Wächter; die Anhebung betrifft nur die Summe"
  - "Die vollständige Filtergrammatik steht im Werkzeug-Docstring und in der README, nicht im Field(description): ein Schema-Byte wird in jeder Sitzung bezahlt, eine Grammatik einmal gelesen"
  - "ALLOWED_MAIL_ROUTES sind die vier Pfadkonstanten von clients/mail.py wörtlich, weil dieser Client seine Pfade als Konstanten schreibt und nicht als Inline-f-Strings"
  - "Der Nur-GET-Test liest den Rohtext der zwei Mail-Module statt der gefilterten Codezeilen: der Modul-Docstring nennt das Fehlende in Prosa, nie in Aufrufsyntax, also können die zwei Aussagen nicht auseinanderlaufen"
  - "CREATE_TOOLS unverändert bei sechs: dass Mail kein Schreibwerkzeug hinzufügt, ist eine geprüfte Aussage dieser Phase"
  - "mail_browse steht in der Vulture-Whitelist bei den anderen zwanzig Werkzeugfunktionen: der @mcp.tool-Dekorator ist der einzige Aufrufer"

patterns-established:
  - "Vierte Familien-Ausnahme im Abnahmelauf: Mail hat zwei eigene SKIP-Sätze (kein Konto, kein Postfach) plus einen dritten für den Volltext ohne Nachrichten-Id"
  - "Ein familienspezifischer Oberflächentest prüft nicht nur, was da ist, sondern auch die verbotene Namensmenge (mail_send, mail_create_draft und vier weitere)"

requirements-completed: [MAIL-01, MAIL-03]

# Metrics
duration: 15min
completed: 2026-08-24
---

# Phase 10 Plan 06: Registrierung, Budget und Schreibverbot Summary

**mail_browse ist als einundzwanzigstes Werkzeug registriert (1377 Bytes, Literal-Enum mit drei Ebenen, ohne Output-Schema), das Budget-Gate steht auf der neuen Messung 15736 Bytes plus 15 Prozent, und neun Mail-Nadeln mit je einer Gegenprobe belegen, dass es keinen Weg zum Senden gibt, obwohl die Mail-App eine Sende-Route direkt neben der Leseroute anbietet.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-24T14:27:30Z
- **Completed:** 2026-08-24T14:42:00Z
- **Tasks:** 3
- **Files modified:** 7 (1 neu, 6 geändert)

## Accomplishments

- `server/reg_mail.py` registriert genau ein Werkzeug: `mail_browse` mit `READ_ONLY`,
  `structured_output=False`, `Literal["accounts", "mailboxes", "messages"]` und leeren Strings
  als Defaults, damit kein `anyOf` aus String und Null ins Schema kommt.
- Das Budget-Gate hat wie vorgesehen ausgelöst und wurde einmal angehoben, gegen eine eigene
  datierte Messung und markiert als Zwischenstand für Phase 11.
- Die Zahl 21 steht identisch an allen fünf Pflegeorten plus README.
- Das Destruktiv-Gate kennt die Mail-Familie jetzt in beide Richtungen: neun Nadeln mit
  Gegenprobe, vier erlaubte Formen als Positivliste und die wörtliche Aussage, dass in den zwei
  Mail-Modulen kein einziger Schreibaufruf steht.

## Die gemessenen Zahlen (für Plan 10-07 und für TOOL-15 in Phase 11)

| Messung | Wert |
|---------|------|
| `tools/list` mit 21 Werkzeugen | **15736 Bytes** |
| `mail_browse` allein | **1377 Bytes** (grösstes Werkzeug der Oberfläche) |
| `mail_browse` vor der Kürzung | 1585 Bytes (über `MAX_TOOL_BYTES`) |
| `BUDGET_BYTES` alt / neu | 15000 / **18500** |
| Rechnung | 15736 + 15 Prozent = 18096, aufgerundet auf die nächsten 500 = 18500 |
| `MAX_TOOL_BYTES` | 1400, unverändert |
| Freier Kopfraum | 2764 Bytes, ausdrücklich als Zwischenstand markiert |

Die vier älteren Messzeilen (10643, 12801, 14312, 14358) stehen unverändert im Skript.

## Die endgültigen Feldbeschreibungen von `mail_browse`

Plan 10-07 baut daraus die README-Tabellenzeile und die Store-Beschreibung, deshalb wörtlich:

| Parameter | Typ / Default | `Field(description=...)` |
|-----------|---------------|--------------------------|
| `level` | `Literal["accounts", "mailboxes", "messages"]`, Default `"accounts"` | `What to list; mailboxes needs an account_id, messages a mailbox_id` |
| `account_id` | `str`, Default `""` | `Account id from level=accounts` |
| `mailbox_id` | `str`, Default `""` | `Mailbox id from level=mailboxes` |
| `filter` | `str`, Default `""` | `Only level=messages: type:value conditions, space separated; types is, not, from, subject, tags, start, end; start/end take Unix seconds` |
| `limit` | `int`, `ge=1`, `le=mail_tools.MAX_LIMIT` (50), Default `mail_tools.DEFAULT_LIMIT` (20) | `Maximum number of entries` |
| `cursor` | `str`, Default `""` | `Next page handle from a truncated messages answer; only that level` |

Der Docstring, also die Werkzeugbeschreibung, die ein Modell liest:

> List the mail accounts of this user, the mailboxes of one, or the messages of one.
>
> Envelopes newest first; the full text of one is a fetch("mail:\<id\>") away. A filter value
> with a space or a colon has to be percent encoded (subject:Rechnung%20Mai). Reads only:
> never sends, drafts, moves, flags or deletes.

## Die neun Mail-Nadeln (die Zahl ist in einem Test eingefroren)

| Nadel | Begründung im Test |
|-------|--------------------|
| `/message/send` | die eine deklarierte Sende-Route der Mail-App, direkt neben dem Volltext-Lesen auf demselben Segment |
| `/api/messages` | interne Resource-Route: POST legt einen Entwurf an, PUT ändert, DELETE löscht, alle auf dem Pfad eines Lesens |
| `/api/mailboxes` | Postfach anlegen, synchronisieren, leeren, reparieren oder als gelesen markieren |
| `/api/accounts` | Mail-Konto, Entwurfseinstellungen oder Signatur ändern |
| `/api/drafts` | Entwurf anlegen oder verschieben |
| `/api/outbox` | die zweite Sendemöglichkeit der App, ohne das Wort send im Pfad |
| `/api/thread` | ganzen Thread verschieben oder löschen |
| `/api/tags` | Tag anlegen, ändern, löschen oder auf eine Nachricht setzen |
| `/api/trustedsenders` | Absender-Vertrauen setzen und entziehen, eine Sicherheitsentscheidung des Kontoinhabers |

Zwei bestehende Nadeln greifen ohne Zutun in die Familie und bekommen bewusst keinen zweiten
Eintrag: `/attachment` (Mail-Anhangsroute) und `/read` (`/api/mailboxes/{id}/read`, von
`/api/mailboxes` ohnehin ein zweites Mal abgedeckt).

`ALLOWED_MAIL_ROUTES` hält die vier erlaubten Formen wörtlich, als die vier Pfadkonstanten des
Clients: `/apps/mail/account/list`, `/apps/mail/ocs/mailboxes`,
`/apps/mail/ocs/mailboxes/{mailbox}/messages` und `/apps/mail/message/{message}`. Die vierte ist
der Punkt: sie liegt ein Segment neben der verbotenen Sende-Route.

## Task Commits

1. **Task 1 + Task 2: reg_mail.py, Budget-Zwischenanhebung und die Zahl 21 an fünf Stellen** - `45b2b08` (feat)
2. **Task 3: Das erweiterte Schreibverbot mit Gegenprobe je Nadel und Positivliste** - `566a837` (test)

## Files Created/Modified

- `src/mcp_connector/server/reg_mail.py` (neu) - Registrierung von `mail_browse`, sechs Parameter plus `ctx`, Grenzen aus `tools/mail.py`
- `scripts/check_tool_budget.py` - neue Messzeile 2026-08-24 mit 21 Werkzeugen, `BUDGET_BYTES` 18500, Zwischenstand-Vermerk, zweite Messzeile am `MAX_TOOL_BYTES`-Block
- `tests/contract/test_tool_surface.py` - `EXPECTED_TOOLS` plus `mail_browse`, `len(tools) == 21`, drei Docstrings nachgezogen, familienspezifischer Mail-Test mit verbotener Namensmenge
- `tests/contract/test_no_destructive_calls.py` - neun Nadeln, `MAIL_ROUTES`, `ALLOWED_MAIL_ROUTES`, `MAIL_MODULES`/`WRITING_CALLS` und vier neue Tests
- `scripts/acceptance_all_tools.py` - `EXPECTED_TOOLS = 21`, Mail-Aufrufblock mit drei eigenen SKIP-Sätzen, `_preferred_mailbox`, `mail_browse` in der zweiten Namensliste
- `vulture_whitelist.py` - `mail_browse` in der Liste der Werkzeugfunktionen ohne sichtbaren Aufrufer
- `README.md` - zwei Zahlkorrekturen (20 auf 21) plus eine Werkzeugtabellenzeile

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei wichtigsten:

1. Die Beschreibung von `mail_browse` wurde gekürzt, bis sie unter `MAX_TOOL_BYTES` passte
   (1585 auf 1377 Bytes). Die Grenze blieb unangetastet, weil sie der eigentliche Wächter ist.
2. Die Budget-Anhebung ist ausdrücklich ein Zwischenstand. Der Vermerk steht im Skript, damit
   Phase 11 nicht eine bereits grosszügige Zahl noch einmal grosszügig anhebt.
3. Die Positivliste besteht aus den vier Pfadkonstanten des Clients und nicht aus
   Aufrufzeilen: dieser Client schreibt seine Pfade als Konstanten, und eine Positivliste, die
   die Datei nicht wörtlich zitiert, belegt nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] README-Werkzeugtabelle bekam die Zeile `mail_browse`**

- **Found during:** Task 2 (die eingefrorenen Zahlen)
- **Issue:** Der Plan weist die README-Werkzeugtabelle Plan 10-07 zu und verlangt in
  Verifikation 5, dass `git diff -- README.md` nur aus den zwei Zahlkorrekturen besteht. Die
  Akzeptanzkriterien von Task 2 verlangen aber, dass
  `uv run pytest tests/contract/test_tool_surface.py -q` grün ist, **einschliesslich des
  README-Tabellentests**. Dieser Test vergleicht die Tabelle mit der laufenden Registry
  (`assert set(documented) == set(tools)`), also war er ab der Registrierung rot.
- **Fix:** Eine einzelne Tabellenzeile `| mail_browse | read | Browse Mail: ... |` ergänzt.
  Mail-Abschnitt, Grenzen, Trifecta-Absatz und die Formulierung bleiben Plan 10-07, das die
  Zeile ohnehin besitzt (10-07 Task 2) und sie dort ausformuliert.
- **Files modified:** `README.md`
- **Verification:** `uv run pytest tests/contract/test_tool_surface.py -q` grün, `git diff`
  über README zeigt genau drei Zeilen: zwei Zahlen und eine Tabellenzeile.
- **Committed in:** `45b2b08`

**2. [Rule 3 - Blocking] Task 1 und Task 2 liegen in einem Commit**

- **Found during:** Task 1
- **Issue:** Der Plan schreibt in Task 2 wörtlich vor, dass jede der eingefrorenen Zahlen im
  **selben** Commit liegt wie `reg_mail.py`, weil eine Zahl an zwei Orten sonst driftet. Ein
  eigener Commit für Task 1 wäre also ein Commit mit rotem Contract-Test gewesen.
- **Fix:** `45b2b08` trägt Task 1 und Task 2 zusammen. Task 3 hat wie geplant seinen eigenen
  Commit, weil er keine Zahl teilt.
- **Files modified:** keine zusätzlichen
- **Verification:** `uv run pytest -q` ist auf jedem der zwei Commits grün.
- **Committed in:** `45b2b08`

**3. [Rule 2 - Missing Critical] Zwei Kommentar-Nachträge in `check_tool_budget.py`**

- **Found during:** Task 1
- **Issue:** Der Kommentar über `MAX_TOOL_BYTES` nannte `calendar_create_event` mit 1351 Bytes
  als grösstes Werkzeug. Nach der Registrierung ist das `mail_browse` mit 1377, der Satz war
  also unwahr, und der Absatz über den freien Kopfraum nannte 642 Bytes und ein
  einundzwanzigstes Werkzeug, das jetzt existiert.
- **Fix:** Eine datierte Messzeile am `MAX_TOOL_BYTES`-Block (neues grösstes Werkzeug, plus der
  Hinweis, dass `mail_browse` gekürzt und nicht ausgenommen wurde) und der Kopfraum-Absatz
  zeigt jetzt auf ein zweiundzwanzigstes Werkzeug.
- **Files modified:** `scripts/check_tool_budget.py`
- **Verification:** Das Prüfskript des Plans (ältere Messungen lesbar, Zwischenstand-Vermerk
  vorhanden) läuft grün.
- **Committed in:** `45b2b08`

**4. [Rule 2 - Missing Critical] `mail_browse` in die Vulture-Whitelist**

- **Found during:** Task 1
- **Issue:** Der Plan sah für `vulture_whitelist.py` nur den umgekehrten Fall vor (einen
  Mail-Eintrag herausnehmen). Es war keiner mehr da, aber jede Werkzeugfunktion braucht dort
  einen Eintrag, weil `@mcp.tool` der einzige Aufrufer ist.
- **Fix:** `mail_browse` in den Block der Werkzeugfunktionen ohne sichtbaren Aufrufer, neben
  `talk_browse` und `talk_send`.
- **Files modified:** `vulture_whitelist.py`
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` grün.
- **Committed in:** `45b2b08`

**5. [Rule 1 - Bug] Gegenprobe-Zeilen mit Präfixkonstante trafen ihre Nadel nicht**

- **Found during:** Task 3
- **Issue:** Die ersten `MAIL_ROUTES`-Zeilen waren nach dem Vorbild von `TALK_ROUTES` mit einer
  Präfixkonstante geschrieben (`f"{API}/messages/{m}"`). Damit steht das Segment `/api/messages`
  nicht wörtlich in der Zeile, acht der neun Gegenproben waren rot. Der Talk-Block kann das,
  weil seine Nadeln unterhalb des Präfixes liegen; die Mail-Nadeln liegen darin.
- **Fix:** Alle neun Zeilen mit dem vollen Pfadliteral geschrieben
  (`f"/apps/mail/api/messages/{m}"`), was ausserdem der Schreibweise von `clients/mail.py`
  entspricht, wo die Pfade ebenfalls vollständig stehen.
- **Files modified:** `tests/contract/test_no_destructive_calls.py`
- **Verification:** Alle neun parametrisierten Gegenproben grün, `uv run pytest -q` grün.
- **Committed in:** `566a837`

---

**Total deviations:** 5 auto-fixed (2 blocking, 2 missing critical, 1 bug)
**Impact on plan:** Alle fünf waren nötig, damit die Akzeptanzkriterien des Plans selbst
erfüllbar sind. Kein Scope Creep: die README-Zeile ist eine Zeile, und die Prosa bleibt 10-07.

## Issues Encountered

- `mail_browse` lag mit der ersten, vollständigen Fassung der Feldbeschreibungen bei 1585
  Bytes und damit über `MAX_TOOL_BYTES`. Gelöst nach A5: die Filtergrammatik ist aus dem Schema
  in den Docstring gewandert und der Docstring wurde gestrafft. Der Endstand 1377 Bytes lässt
  23 Bytes Luft, das Werkzeug ist damit das grösste der Oberfläche. Wer die Beschreibung
  erweitert, zahlt zuerst an dieser Decke, und das ist beabsichtigt.

## Known Stubs

Keine. `mail_browse` ist an `tools/mail.browse` verdrahtet, und der Weg zur laufenden
Nextcloud steht seit Plan 10-02.

## User Setup Required

None - keine externe Konfiguration, keine neue Abhängigkeit. `pyproject.toml`, `uv.lock` und
`appinfo/info.xml` sind unangetastet (per `git diff --stat` geprüft).

## Next Phase Readiness

- **Plan 10-07** kann die drei READMEs, `docs/privacy.md`, `docs/faq.md` und die
  Store-Beschreibung bauen. Die Feldbeschreibungen und die Grenzen stehen oben wörtlich. Zu tun
  bleibt dort: die README-Tabellenzeile ausformulieren, `README.de.md` und `README.fr.md`
  nachziehen (Zahl 21 und Tabellenzeile, in diesem Plan bewusst nicht angefasst) und der
  Mail-Abschnitt mit Filtergrammatik.
- **Plan 10-08** kann den Abnahmelauf fahren: der Mail-Block überspringt ein Konto ohne Mail
  ehrlich, mit eigenen Sätzen für "kein Konto" und "kein Postfach".
- **Phase 11, TOOL-15:** `BUDGET_BYTES` steht auf 18500 mit 2764 Bytes Kopfraum und ist als
  Zwischenstand markiert. Die Neuverankerung gehört auf die Endmessung dieser Phase, nicht auf
  eine weitere Anhebung.

## Self-Check: PASSED

Alle sieben Quelldateien und die Zusammenfassung liegen auf der Platte, beide Commits
(`45b2b08`, `566a837`) stehen im Log. Gates am Planende: `uv run pytest -q`,
`uv run pytest tests/contract -q`, `uv run ruff check .`, `uv run ruff format --check .`,
`uv run pyright`, `uv run vulture src/mcp_connector vulture_whitelist.py` und
`uv run python scripts/check_tool_budget.py` alle grün.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*
