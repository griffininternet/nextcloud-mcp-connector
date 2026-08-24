---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 07
subsystem: api
tags: [schema-diet, token-budget, tools-list, gate, measurement, tool-15]

# Dependency graph
requires:
  - phase: 11-05
    provides: "die Ausgangsmessung 15769 Bytes bei 21 Werkzeugen und die 33 Bytes der ehrlicheren prepare_context-Beschreibung, die gegenzurechnen waren"
  - phase: 10-mail
    provides: "mail_browse mit 1377 Bytes als grösstes Werkzeug, die Filtergrammatik in README.md und _FILTER_HINT in tools/mail.py"
  - phase: 01-server-kern
    provides: "das Gate scripts/check_tool_budget.py mit Messweg, Messzeilenform und den zwei Regelsätzen über Anheben und Obergrenze"
provides:
  - "BUDGET_BYTES = 18000, verankert auf der Messung 15612 dieser Phase (15612 * 1,15 = 17953, aufgerundet 18000)"
  - "MAX_TOOL_BYTES = 1400 als ausdrückliche Entscheidung mit eigener Messzeile, nicht als Gewohnheit"
  - "die fünf diäteten Registrierungen: mail_browse 1331, talk_browse 858, tables_create_row 746, tables_browse 751, talk_send 620"
  - "die gemessene Korrektur der Byte-Behauptung im Modul-Docstring von reg_mail.py (Docstring und Field sind derselbe tools/list-Payload)"
  - "test_the_byte_gate_counts_exactly_as_many_tools_as_this_file_freezes plus _load_budget_gate als Ladeweg für das Skript"
affects:
  - "11-08 (die drei READMEs beschreiben eine Oberfläche von 15612 Bytes und 21 Werkzeugen; die neuen Wortlaute der fünf Beschreibungen stehen unten)"
  - "11-09 (der Changelog-Block von 0.1.8 schreibt sich aus der Tabelle unten: 157 Bytes weniger, Gate von 18500 auf 18000)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kürzen heisst komprimieren, nicht verschieben: Tool-Docstring und Field-Beschreibung sind zwei Schlüssel desselben tools/list-Payloads"
    - "Ein Docstring-Zeilenumbruch kostet zwei Bytes (\\n im JSON), eine implizit verkettete Field-Beschreibung kostet für ihre Umbrüche nichts"
    - "Der abschliessende Zeilenumbruch eines mehrzeiligen Docstrings ist zwei Bytes ohne Information: schliessende Anführungszeichen direkt an den Text"
    - "Ein Verweis auf einen Aufzählungswert (only level=messages) ist kürzer und genauer als ein Verweis auf den Kontext (only that level)"
    - "Jede einzelne Kürzung wird als Bytepaar ausgerechnet, und die Summe der Einzelposten muss die gemessene Differenz je Werkzeug ergeben"
    - "Ein Gate wird auf eine Messung verankert, die im Skript nachlesbar ist; eine nicht erreichte Erwartung wird begründet statt gerundet"

key-files:
  created: []
  modified:
    - src/mcp_connector/server/reg_mail.py
    - src/mcp_connector/server/reg_talk.py
    - src/mcp_connector/server/reg_tables.py
    - scripts/check_tool_budget.py
    - tests/contract/test_tool_surface.py

key-decisions:
  - "Die Filtergrammatik wird an ihrem Platz komprimiert statt in den Tool-Docstring verschoben: die vom Plan verlangte Verschiebung ist gemessen +4 Bytes für dieselbe Information, weil Beschreibung und Docstring im selben tools/list-Payload liegen und ein Docstring-Umbruch zwei Bytes kostet"
  - "Die sieben Filtertypen bleiben im Schema, aber als Namen ohne Doppelpunkt (is/not/from/subject/tags/start/end): die Form type:value steht im selben Satz, die volle Grammatik in README.md, und eine falsche Bedingung kostet genau eine Runde, weil _FILTER_HINT alle sieben nennt"
  - "BUDGET_BYTES = 18000, die obere Kante der Erwartung von TOOL-15; 17500 hätte 395 Bytes mehr gebraucht, also 23 Prozent der gesamten Prosa dieser fünf Werkzeuge, und die verbliebene Prosa ist Grammatik, Timeout-Warnung und die Reads-only-Aussage"
  - "MAX_TOOL_BYTES bleibt 1400: nach der Diät ist nicht mehr mail_browse (1331) das grösste Werkzeug, sondern calendar_create_event (1351) aus Phase 1; die 15-Prozent-Regel ergäbe hier 1553 und damit eine verbotene Anhebung, und eine Senkung knapp über 1351 würde den Wortlaut eines Werkzeugs einfrieren, um das es in diesem Meilenstein nicht geht"
  - "Der title-Schlüssel jeder Schema-Property (rund 140 Bytes allein in mail_browse, über ein Kilobyte auf der ganzen Oberfläche) bleibt unangetastet: er ist reine Ableitung des Parameternamens, aber sein Wegfall ändert die Schema-Erzeugung aller 21 Werkzeuge und ist damit eine eigene Entscheidung und keine Diät von fünf Beschreibungen"
  - "Der neue Contract-Test lädt scripts/check_tool_budget.py per Pfad (Muster aus tests/integration/test_oauth_flow_exapp.py) und behauptet neben der Zahlengleichheit auch das Urteil des Gates, weil das Gate die Hälfte des Paars ist, die CI ausserhalb von pytest ausführt"

patterns-established:
  - "Bytepaar-Rechnung je Kürzung mit Abgleich gegen die gemessene Differenz je Werkzeug (alle fünf gehen exakt auf)"
  - "Eine Messzeile, die eine Grenze ausdrücklich unverändert lässt, nennt die Rechnung, die zur Anhebung geführt hätte, und warum sie hier nicht gilt"

requirements-completed: []  # TOOL-15 bleibt Pending, siehe "Offen und bewusst offen"

# Metrics
duration: 19min
completed: 2026-08-24
---

# Phase 11 Plan 07: Schema-Diät der fünf Werkzeuge und die Verankerung des Gates Summary

**Die fünf Werkzeuge des Meilensteins v1.2 sind um 157 Bytes kürzer, ohne dass eine einzige Angabe verloren ging, und das Budget-Gate steht damit zum ersten Mal auf einer Messung, die es senkt statt anhebt: `BUDGET_BYTES` fällt von 18500 auf 18000, gerechnet aus 15612 gemessenen Bytes bei 21 Werkzeugen.**

## Performance

- **Duration:** ca. 19 min
- **Started:** 2026-08-24T21:36:20Z
- **Completed:** 2026-08-24T21:55:00Z
- **Tasks:** 2
- **Files modified:** 5

## Die Messtabelle

Messweg wörtlich der aus `scripts/check_tool_budget.py`: `Client(mcp, raise_exceptions=True).list_tools()`, `model_dump(by_alias=True, exclude_none=True, mode="json")`, `json.dumps(..., separators=(",", ":"), ensure_ascii=False)`, `len(...encode("utf-8"))`.

| Werkzeug | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `mail_browse` | 1377 | **1331** | **-46** |
| `talk_browse` | 886 | **858** | **-28** |
| `tables_create_row` | 780 | **746** | **-34** |
| `tables_browse` | 772 | **751** | **-21** |
| `talk_send` | 648 | **620** | **-28** |
| die fünf zusammen | 4463 | **4306** | **-157** |
| **Gesamtoberfläche** | **15769** | **15612** | **-157** |

Die Gesamtdifferenz ist gleich der Summe der fünf, weil kein sechstes Werkzeug angefasst wurde. Die Ausgangszahl ist 15769 und nicht die 15736 des Plans: die 33 Bytes dazwischen sind die ehrlichere `prepare_context`-Beschreibung aus Plan 11-05, und sie sind hier gegengerechnet.

### Jede Kürzung als Bytepaar

Die Summe der Einzelposten ergibt je Werkzeug exakt die gemessene Differenz. Das ist die Prüfung, dass die Tabelle oben nicht geschätzt ist.

**`mail_browse`, -46**

| Kürzung | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `level`: zwei Artikel weg (`needs an account_id` → `needs account_id`) | 66 | 61 | -5 |
| `filter`: umgestellt, Typenliste mit Schrägstrichen, `take` → `in` | 136 | 116 | -20 |
| `limit`: `Maximum number of entries` → `Maximum entries` | 25 | 15 | -10 |
| `cursor`: `only that level` → `only level=messages`, `messages answer` → `answer` | 66 | 61 | -5 |
| Docstring: `has to be` → `must be`, `a space or a colon` → `a space or colon` | 64 | 60 | -4 |
| Docstring: abschliessender Zeilenumbruch entfällt | | | -2 |

**`talk_browse`, -28**

| Kürzung | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `limit` wie oben | 25 | 15 | -10 |
| `cursor` wie oben | 66 | 61 | -5 |
| Docstring Satz 1: `the history of one of them.` → `the history of one.` | 70 | 62 | -8 |
| Docstring Satz 2: `, and the` → `; the`, dazu `message level` → `messages level` (der echte Aufzählungswert, +1) | 85 | 82 | -3 |
| Docstring: abschliessender Zeilenumbruch entfällt | | | -2 |

**`tables_create_row`, -34**

| Kürzung | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `values`: Leerzeichen im JSON-Beispiel weg | 37 | 34 | -3 |
| `values`: `a text column takes a string, a number column a number` → `text columns take strings, number columns numbers` | 54 | 49 | -5 |
| Docstring: `never changes or deletes an existing row.` → `... deletes one.` | 75 | 63 | -12 |
| Docstring: `tables_browse(level="rows")` ohne Anführungszeichen (zwei JSON-Escapes) | 14 | 10 | -4 |
| Docstring: `instead of calling this a second time.` → `... twice.` | 38 | 30 | -8 |
| Docstring: abschliessender Zeilenumbruch entfällt | | | -2 |

**`tables_browse`, -21**

| Kürzung | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `limit` wie oben | 25 | 15 | -10 |
| `cursor`: `truncated rows answer` → `truncated answer` | 62 | 57 | -5 |
| Docstring: `the columns of one table` → `the columns of one` | 62 | 56 | -6 |

**`talk_send`, -28**

| Kürzung | vorher | nachher | Differenz |
|---|---:|---:|---:|
| `message`: `The message text to post` → `The text to post` (der Parameter heisst `message`) | 36 | 28 | -8 |
| Docstring: `never edits or deletes a message.` → `... deletes one.` | 71 | 65 | -6 |
| Docstring: `talk_browse(level=messages)` ohne Anführungszeichen | 14 | 10 | -4 |
| Docstring: `a second time` → `twice` | 38 | 30 | -8 |
| Docstring: abschliessender Zeilenumbruch entfällt | | | -2 |

## Das neue `BUDGET_BYTES`, ausgeschrieben

```
15612 * 1,15 = 17953,8   ->  aufgerundet auf die nächsten 500  =  18000
```

`BUDGET_BYTES = 18_000`, vorher 18500. Luft über der Messung: 2388 Bytes. Der `Zwischenstand`-Absatz mit dem Verweis "TOOL-15 in phase 11 re-anchors the gate" ist verschwunden; an seiner Stelle steht eine erledigte Aussage mit der Messung, der Rechnung, den fünf Einzeldifferenzen und den 33 gegengerechneten Bytes aus 11-05. Die fünf alten Messzeilen stehen unverändert darüber; die Datei enthält jetzt neun Zeilen mit `Measurement 20` (sieben im Budget-Block, zwei bei der Obergrenze).

**Warum nicht 17500.** 17500 verlangt eine Messung von höchstens 15217 Bytes, also 395 Bytes mehr als die Diät gefunden hat. Die fünf Werkzeuge bestehen nach der Diät aus 4306 Bytes, davon **1729 Bytes Prosa** (Tool-Beschreibung plus alle `Field`-Beschreibungen) und 2577 Bytes Struktur (Namen, Typen, Enums, Defaults, `required`, Annotationen und die `title`-Schlüssel). 395 Bytes sind 23 Prozent jedes Wortes, das diese fünf Werkzeuge noch sagen, und was übrig ist, ist die Filtergrammatik, die zwei Sätze "ein Timeout heisst nicht, dass nichts geschrieben wurde" und die Aussage, dass Mail nur liest. Jede davon ist Information, die ein Modell sonst nirgends im Schema findet. Der Satz steht so auch im Skript.

## Die Entscheidung über `MAX_TOOL_BYTES`

**Unverändert 1400, mit eigener Messzeile.** Die Begründung ist Arithmetik und nicht Gewohnheit:

- `mail_browse` ist mit 1331 nicht mehr das grösste Werkzeug. Das grösste ist jetzt **`calendar_create_event` mit 1351**, ein Werkzeug aus Phase 1, das dieser Meilenstein nie angefasst hat.
- Die Regel des Gesamtbudgets (Messung plus 15 Prozent) ergäbe hier 1351 * 1,15 = 1553 und damit eine **Anhebung**, die die Datei selbst verbietet ("a tool that reaches it gets a shorter description and never a higher limit"). Die Regel passt also nicht auf eine Grenze, die schon strenger ist als sie: 1400 lässt 49 Bytes über dem grössten Werkzeug, 3,6 Prozent, gegen die 15 Prozent, die die Gesamtsumme bekommt.
- Die einzige Senkung mit Bewegung darin läge knapp über 1351 und würde den Wortlaut von `calendar_create_event` einfrieren. Der nächste ehrliche Satz dort löste dann einen Alarm über Werkzeuggrösse aus, während die Gesamtsumme noch 2388 Bytes frei hat: ein Gate, das aus dem falschen Grund feuert.

## Nicht ausgeführte Schnitte, mit Grund

Der Plan verlangt für jeden unterlassenen Schnitt den Grund, weil Plan 11-09 daraus den Changelog schreibt.

| Nicht geschnitten | Ersparnis gewesen | Grund |
|---|---:|---|
| Der `title`-Schlüssel jeder Schema-Property (`"title":"Mailbox Id"` und Genossen) | ~140 in `mail_browse`, über 1000 auf der Oberfläche | Reine Ableitung des Parameternamens, also der grösste verbleibende Hebel ohne Informationsverlust. Aber er liegt in der Schema-Erzeugung und betrifft alle 21 Werkzeuge, nicht die fünf dieses Meilensteins, und er steht in keiner der fünf Dateien dieses Plans. Eine eigene Entscheidung, kein Diätschnitt. Im Skript benannt. |
| `Reads only: never sends, drafts, moves, flags or deletes.` in `mail_browse` | 56 | Die Sicherheitsaussage der Familie. Die Annotation `readOnlyHint` sagt nur die Hälfte davon; die vier verneinten Verben stehen sonst nirgends im Schema. Dasselbe Muster wie `never overwrites` bei `files_upload`, das ein Contract-Test einfordert. |
| Die zwei Sätze `A timeout does not mean nothing was written/sent.` | je 43 | Sie verhindern den doppelten Schreibvorgang, den die Annotation `idempotentHint: false` nur ankündigt. Das ist der teuerste Fehler, den diese zwei Werkzeuge machen können. |
| `start/end in Unix seconds` in `mail_browse` | 25 | Genau die Regel, die still das Falsche tut: eine ISO-Angabe filtert alle Nachrichten weg statt zu scheitern. |
| Die sieben Typennamen ganz aus dem Schema entfernen (nur README) | ~40 | T-11-44. Ein Modell hätte die Typen erraten müssen. Sie bleiben als Namen im Schema. |
| Die Beispielwerte (`e.g. gzu8sw3d`, `e.g. 7`, `{"Task":"Call back",...}`) | ~90 zusammen | Ein Beispiel spart die Runde, die ein geratenes Format kostet (D-14). |
| `level` von `Literal` auf freien String | ~60 je Werkzeug | Ausdrücklich verboten (T-11-45, D-06, D-14). Alle vier `Literal`-Enums stehen unverändert. |
| Leere Strings gegen `None` tauschen | negativ | Ein `anyOf` aus String und Null kostet mehr, als jede Beschreibung einbringt. Alle Defaults sind unverändert leere Strings. |

## Wo die Information jetzt steht

Nachweis, dass keine Angabe verloren ging (T-11-44):

| Angabe | Im Schema | Im Docstring | In README.md | Zur Laufzeit |
|---|---|---|---|---|
| Die sieben Filtertypen | als Namen `is/not/from/subject/tags/start/end` | - | vollständige Tabelle mit `is:` bis `end:` ab Zeile 330 | `_FILTER_HINT` nennt alle sieben in der Ablehnung |
| Form `type:value`, Trennung durch Leerzeichen | ja | - | ja | `_FILTER_HINT` |
| Prozentkodierung bei Leerzeichen und Doppelpunkt | - | ja, mit Beispiel `subject:Rechnung%20Mai` | ja, plus die First-Colon-Regel | `_FILTER_HINT` |
| `start`/`end` in Unix-Sekunden | ja | - | ja, plus was eine ISO-Angabe anrichtet | `_SECONDS_HINT` |
| Nur `level=messages` nimmt einen Filter | ja | - | ja | Tool-Schicht lehnt ab |

Der geprüfte Satz: alle sieben Tokens `is:` bis `end:` sind in `README.md` lesbar, `subject:` zusätzlich im Tool-Docstring, und alle sieben Namen stehen im Schema und in `_FILTER_HINT`.

## Die neuen Wortlaute (für Plan 11-08)

```
mail_browse
  level   : What to list; mailboxes needs account_id, messages mailbox_id
  filter  : Only level=messages: space separated type:value; types
            is/not/from/subject/tags/start/end; start/end in Unix seconds
  limit   : Maximum entries
  cursor  : Next page handle from a truncated answer; only level=messages
  doc     : List the mail accounts of this user, the mailboxes of one, or the messages of
            one. / Envelopes newest first; the full text of one is a fetch("mail:<id>")
            away. A filter value with a space or colon must be percent encoded
            (subject:Rechnung%20Mai). Reads only: never sends, drafts, moves, flags or
            deletes.
talk_browse
  limit   : Maximum entries
  cursor  : Next page handle from a truncated answer; only level=messages
  doc     : List the conversations of this account, or the history of one. / The messages
            level answers newest first; the next page runs further into the past.
talk_send
  message : The text to post, plain text
  doc     : Send one message into a conversation; never edits or deletes one. / A timeout
            does not mean nothing was sent. Read back with talk_browse(level=messages)
            instead of calling this twice.
tables_browse
  limit   : Maximum entries
  cursor  : Next page handle from a truncated answer; only level=rows
  doc     : List the user's Tables, the columns of one, or its rows.
tables_create_row
  values  : One JSON object of column titles and values, e.g. {"Task":"Call back",
            "Amount":12.5}; text columns take strings, number columns numbers
  doc     : Add one row to an existing table; never changes or deletes one. / A timeout
            does not mean nothing was written. Read back with tables_browse(level=rows)
            instead of calling this twice.
```

Unverändert geblieben sind `account_id`, `mailbox_id`, `talk_browse.level`, `talk_browse.token`, `talk_send.token`, `tables_browse.level`, `tables_browse.table_id` und `tables_create_row.table_id`: sie waren schon die kürzeste Fassung ihrer Aussage.

## Task Commits

1. **Task 1: Schema-Diät der fünf Werkzeuge, jede Kürzung gemessen** - `47e9e56` (perf)
2. **Task 2: Das Gate neu verankern, mit Messzeile und einer Entscheidung über die Obergrenze** - `969cc1e` (chore)

## Files Created/Modified

- `src/mcp_connector/server/reg_mail.py` - vier gekürzte `Field`-Beschreibungen, gekürzter Tool-Docstring ohne abschliessenden Umbruch, und ein neu geschriebener Absatz im Modul-Docstring: die alte Behauptung, die Grammatik gehöre "in den Docstring statt ins Schema", war eine Byte-Aussage und ist gemessen falsch.
- `src/mcp_connector/server/reg_talk.py` - `limit`, `cursor` und `message` gekürzt, beide Tool-Docstrings gekürzt.
- `src/mcp_connector/server/reg_tables.py` - `limit`, `cursor` und `values` gekürzt, beide Tool-Docstrings gekürzt.
- `scripts/check_tool_budget.py` - neue Messzeile mit Rechnung und Herkunft der 157 Bytes, `BUDGET_BYTES` 18500 → 18000, der `Zwischenstand`-Absatz zur erledigten Aussage umgeschrieben, der Absatz über die nicht erreichten 17500 samt Prosa-Rechnung, ein fünfter Satz in der Chronik der Messzeilen, und eine neue Messzeile bei `MAX_TOOL_BYTES`, die die Grenze ausdrücklich stehen lässt.
- `tests/contract/test_tool_surface.py` - `_load_budget_gate` (Pfad-Ladeweg wie in `test_oauth_flow_exapp.py`) und `test_the_byte_gate_counts_exactly_as_many_tools_as_this_file_freezes`. `EXPECTED_TOOLS` (21) und `CREATE_TOOLS` (6) sind unangetastet.

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei mit Folgen für spätere Pläne:

1. **Verschieben ist keine Diät.** Ein Tool-Docstring und eine `Field`-Beschreibung sind zwei Schlüssel desselben `tools/list`-Payloads. Wer Text zwischen ihnen bewegt, spart nichts, und weil ein Docstring-Zeilenumbruch als `\n` zwei Bytes kostet, ist die Richtung "ins Docstring" sogar teurer. Der Modul-Docstring von `reg_mail.py` sagt das jetzt mit der Messung, damit die alte Formulierung nicht in sechs Monaten den nächsten Plan in dieselbe Richtung schickt.
2. **Das Gate steht auf 18000 und nicht auf 17500.** Die Erwartung von TOOL-15 ist an der oberen Kante getroffen, und der Grund für die Kante ist im Skript nachlesbar (395 Bytes fehlen, das sind 23 Prozent der verbliebenen Prosa). Eine Zahl zu erfinden war der einzige verbotene Ausgang, und er wurde nicht genommen.
3. **`MAX_TOOL_BYTES` ist jetzt eine Aussage über `calendar_create_event`, nicht über `mail_browse`.** Wer die Grenze das nächste Mal anfasst, hat es mit einem Werkzeug aus Phase 1 zu tun, und die Messzeile sagt das.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die vom Plan verlangte Verschiebung der Typenliste in den Tool-Docstring hätte die Messung erhöht**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, die `Field`-Beschreibung von `filter` auf einen Verweis zu reduzieren und "die Typenliste selbst" in den Tool-Docstring wandern zu lassen, mit dem Ziel, die Messung zu senken. Beides gleichzeitig ist nicht möglich: der Tool-Docstring wird als `description` im **selben** `tools/list`-Payload ausgeliefert wie die `Field`-Beschreibung. Nachgerechnet: die `Field`-Beschreibung verliert 75 Bytes, der Docstring gewinnt 85 (die neue Zeile plus ihr `\n`, das im JSON zwei Bytes kostet), abzüglich der zwei gesparten Escapes und des abschliessenden Umbruchs bleiben **+4 Bytes** für exakt dieselbe Information. Der Plan hätte damit sein eigenes Verifikationskriterium `total < 15736` gerissen, wäre die Diät auf diesen Schnitt beschränkt geblieben.
- **Fix:** Die Typenliste bleibt an ihrem Platz und wird komprimiert (Kommas zu Schrägstrichen, Umstellung, `take` → `in`): 136 → 116 Bytes, dieselben sieben Typen, dieselbe Form `type:value`, dieselbe Unix-Sekunden-Regel. Der Absatz im Modul-Docstring, der die falsche Byte-Behauptung aufgestellt hatte ("every byte of a `Field` description is paid for in every `tools/list` ... and a grammar is read once"), ist durch die gemessene Wahrheit ersetzt: die volle Grammatik steht in `README.md` und in `_FILTER_HINT`, die Kurzform im Schema, und nur Komprimieren spart.
- **Files modified:** src/mcp_connector/server/reg_mail.py
- **Verification:** `mail_browse` 1377 → 1331, alle sieben Typen im Schema, in `_FILTER_HINT` und in der README-Tabelle
- **Committed in:** `47e9e56`

**2. [Rule 3 - Blocking] Die Rechnung des Plans für `MAX_TOOL_BYTES` ergibt eine verbotene Anhebung**

- **Found during:** Task 2
- **Issue:** Der Plan schreibt: liegt `mail_browse` nach der Diät klar unter der Grenze, wird sie "auf den neuen grössten Wert plus dieselbe Logik wie beim Gesamtbudget" gesenkt. Der Plan nimmt dabei an, `mail_browse` sei das grösste Werkzeug (das war es mit 1377). Nach der Diät ist es `calendar_create_event` mit 1351, und 1351 plus 15 Prozent ergibt 1553: eine **Anhebung**, die derselbe Planabsatz und die Datei selbst ausdrücklich verbieten.
- **Fix:** Der zweite vom Plan vorgesehene Ausgang wurde genommen ("Bleibt sie, sagt eine Messzeile, dass sie bewusst bleibt, und warum"). Die Messzeile nennt die Rechnung, die zur Anhebung geführt hätte, die 49 Bytes (3,6 Prozent) Luft über dem grössten Werkzeug und den Grund, warum eine Senkung knapp über 1351 ein Gate wäre, das aus dem falschen Grund feuert.
- **Files modified:** scripts/check_tool_budget.py
- **Verification:** `MAX_TOOL_BYTES == 1400`, zwei Messzeilen im Obergrenzen-Block, Gate Exit 0
- **Committed in:** `969cc1e`

**3. [Rule 2 - Missing Critical] Der neue Contract-Test behauptet zusätzlich das Urteil des Gates**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt einen Test, der die vom Gate gezählte Werkzeugzahl gegen `len(EXPECTED_TOOLS)` hält. `main()` des Gates liefert aber einen Exit-Code und keine Zahl, die man abfragen könnte; eine Zählung, die der Test selbst nachbaut, kann vom Gate wegdriften, und dann behauptet der Test etwas über eine Kopie.
- **Fix:** Der Test lädt `scripts/check_tool_budget.py` per Pfad (Muster aus `tests/integration/test_oauth_flow_exapp.py`), zählt über **denselben** Ausdruck auf **derselben** Payload-Form wie das Gate, und behauptet zusätzlich `await gate.main() == 0`. Damit ist die einzige Hälfte des Paars, die CI ausserhalb von pytest ausführt, auch im Testlauf abgedeckt.
- **Files modified:** tests/contract/test_tool_surface.py
- **Verification:** `uv run pytest tests/contract` 66 statt 65 Tests, alle grün
- **Committed in:** `969cc1e`

**4. [Rule 1 - Bug] `talk_browse` sprach von einer Ebene, die es nicht gibt**

- **Found during:** Task 1
- **Issue:** Der Docstring sagte "The message level answers newest first". Der Aufzählungswert heisst `messages`, nicht `message`. Ein Modell, das den Docstring wörtlich nimmt, ruft eine Ebene, die das Schema ablehnt, und zahlt eine Runde für die Korrektur, also genau der Fehler, für den `level` überhaupt ein `Literal` ist.
- **Fix:** `The messages level answers newest first` (ein Byte teurer, im selben Satz durch `, and the` → `; the` mehr als gegengerechnet).
- **Files modified:** src/mcp_connector/server/reg_talk.py
- **Committed in:** `47e9e56`

---

**Total deviations:** 4 auto-fixed (1 blocking, 1 missing critical, 2 bugs)
**Impact on plan:** Kein Scope-Zuwachs, keine Datei ausserhalb der fünf geplanten. Deviation 1 und 2 sind beide Rechenfehler des Plans, die in dieselbe Richtung zeigen: die Zahlen, mit denen der Plan arbeitet, waren aus der Zeit vor 11-05 beziehungsweise vor der Diät. Beide sind gemessen korrigiert, kein Ergebnis wurde gerundet.

## Issues Encountered

- Die 15612 Bytes liegen nur 40 Bytes unter der Kante von 15652, ab der die Regel wieder 18500 ergäbe. Das ist für dieses Gate ohne Belang, weil `BUDGET_BYTES` eine feste Zahl ist und 2388 Bytes Luft hat. Für den **nächsten** Plan, der eine Beschreibung anfasst, heisst es aber: eine Verlängerung um 41 Bytes macht aus der Verankerung eine 18500-Verankerung, sobald jemand die Regel neu anwendet. Wer eine Beschreibung verlängert, verlängert also nicht nur die Oberfläche, sondern verschiebt die Rundungsstufe.
- Der grösste verbleibende Hebel liegt nicht mehr in Prosa, sondern in der Schema-Erzeugung (`title`-Schlüssel, über ein Kilobyte). Das ist notiert, nicht getan, und es ist eine Entscheidung für einen eigenen Plan, weil sie alle 21 Schemata gleichzeitig verändert.

## Verification Results

| Prüfung | Ergebnis |
|---|---|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün, 197 Dateien |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run pytest` | grün, **2765 passed**, 163 deselected (vorher 2764) |
| `uv run pytest tests/contract` | grün, **66 passed** (vorher 65) |
| `uv run vulture src scripts vulture_whitelist.py` | grün, kein neuer Whitelist-Eintrag |
| `uv run python scripts/check_tool_budget.py` | **Exit 0**, `tools/list: 15612 bytes, 21 tools, budget 18000` |
| Byte-Gate des Plans | `total 15612 < 15736`, 21 Werkzeuge, grösstes 1351 ≤ 1400, `mail_browse` 1331 < 1377 |
| Verankerungsrechnung | `BUDGET_BYTES == ceil(15612 * 1,15 / 500) * 500 == 18000`, `MAX_TOOL_BYTES == 1400 ≤ 1400`, 9 Zeilen mit `Measurement 20`, `15612` steht in der Datei, `TOOL-15 in phase 11 re-anchors` steht nicht mehr darin |
| Informationsverlust | alle sieben Tokens `is:` bis `end:` in `README.md`, `subject:` zusätzlich im Docstring, alle sieben Namen im Schema **und** in `_FILTER_HINT`, `Literal[` in `reg_mail.py` |
| `git diff --stat 750d220 HEAD` | genau fünf Dateien; `pyproject.toml`, `uv.lock`, `src/mcp_connector/tools/` und `appinfo/info.xml` unangetastet |
| Löschungen im Diff | keine (`git diff --diff-filter=D` leer) |

## Known Stubs

Keine. Der eine bewusst offene Punkt gehört dem Phasenplan: die READMEs beschreiben die Oberfläche und die Werkzeugzahl, und deren Gegenprüfung ist Plan 11-08.

## Threat Flags

Keine neue Angriffsfläche: kein neuer Endpunkt, keine neue Route, kein neues Schemafeld, keine geänderte Annotation, keine geänderte Logik. Der Diff besteht aus Beschreibungstexten, Kommentaren, einer Konstante und einem Test. Die acht `mitigate`-Dispositionen des Plans:

- **T-11-44** (Kürzung entfernt eine Angabe ersatzlos): die Tabelle "Wo die Information jetzt steht" ist der Nachweis; die sieben Typen stehen im Schema, in `_FILTER_HINT` und in der README-Tabelle.
- **T-11-45** (`Literal` wird zu freiem String): alle vier `Literal`-Enums unverändert, der Contract-Test prüft die drei `enum`-Listen weiter wörtlich, `Literal[` steht in `reg_mail.py`.
- **T-11-46** (Gate ohne tragende Messung): `BUDGET_BYTES` gegen `ceil(Messung * 1,15 / 500) * 500` nachgerechnet, neun Messzeilen, die Zahl 15612 steht in der Datei.
- **T-11-47** (Zahl erfunden, um die Erwartung zu treffen): 18000 ist gerechnet, und der Absatz, der sagt warum nicht 17500, nennt die fehlenden 395 Bytes und die Prosa-Rechnung.
- **T-11-48** (Obergrenze angehoben statt Beschreibung gekürzt): 1400 unverändert, eine Anhebung wäre die Rechnung 1553 gewesen und wurde ausdrücklich abgelehnt; der Test behauptet `<= 1400`.
- **T-11-49** (falsche Annotation): `CREATE_TOOLS` und `EXPECTED_TOOLS` unangetastet, `test_every_tool_carries_honest_annotations` grün, kein `annotations=`-Argument angefasst.
- **T-11-50** (registriert, aber nie eingefroren): der neue Contract-Test hält die vom Gate gezählte Zahl gegen `len(EXPECTED_TOOLS)`.
- **T-11-SC** (Paketinstallation): kein `uv add`, kein `pip install`; `pyproject.toml` und `uv.lock` stehen nicht im Diff.

## User Setup Required

Keine. Keine neue Abhängigkeit, keine Umgebungsvariable, kein Werkzeug mehr und keines weniger. Die gekürzten Beschreibungen liest ein Client beim nächsten `tools/list`; ein Client, der Werkzeuglisten persistiert, sieht die kürzeren Texte erst nach seiner nächsten Auffrischung, und die Bedeutung ist in beiden Fassungen dieselbe.

## Next Phase Readiness

- **Bereit für Plan 11-08:** Die neuen Wortlaute aller fünf Werkzeuge stehen oben zum Abgleichen. Die Zahlen für die READMEs: **21 Werkzeuge, 15612 Bytes, Budget 18000, Obergrenze je Werkzeug 1400.** Die zwei Contract-Tests, die die README-Tabelle und die dokumentierten Werkzeugzahlen halten (`test_the_readme_permission_table_matches_the_live_registry`, `test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from`), sind grün, es ist also nichts kaputt, sondern nachzuziehen.
- **Bereit für Plan 11-09:** Der Changelog-Block von 0.1.8 schreibt sich aus zwei Sätzen: die fünf Werkzeuge des Meilensteins sagen dasselbe in 157 Bytes weniger, und das Budget-Gate ist zum ersten Mal gesunken statt gestiegen, von 18500 auf 18000. Die Werkzeugzahl ändert sich **nicht** (21), und keine Funktion ändert sich, es ist eine Aussage über Tokenkosten pro Sitzung.
- **Offen und bewusst offen:** **TOOL-15 bleibt `Pending`.** Diese Hälfte ist erledigt (Diät gemessen, Gate verankert, Annotationen unverändert ehrlich, Werkzeugzahl 21 in Registry und Contract-Test identisch); die andere Hälfte der Anforderung nennt ausdrücklich die nachgezogene README-Tool-Tabelle, und dafür ist Plan 11-08 zuständig, der die Werkzeugzahl in drei READMEs gegenprüft. `scripts/acceptance_all_tools.py` steht bereits auf 21, dieser Teil der Tech-Debt-Notiz ist also nicht offen.
- **Für den nächsten, der eine Beschreibung anfasst:** 40 Bytes trennen die heutige Messung von der Rundungsstufe 18500. Das Gate hat 2388 Bytes Luft, die Rundung nicht.

## Self-Check: PASSED

Alle fünf geänderten Dateien liegen auf der Platte, beide Commits (`47e9e56`, `969cc1e`) stehen im Log, es gibt keine Löschung und keine unversionierte Datei im Arbeitsbaum.

---
*Phase: 11-b-ndelung-budget-und-release-0-1-6*
*Completed: 2026-08-24*
