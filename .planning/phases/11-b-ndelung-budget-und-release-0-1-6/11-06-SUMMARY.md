---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 06
subsystem: api
tags: [prepare-context, integration, measurement, budget, request-count, side-effect-freedom, ctx-01, ctx-02]

# Dependency graph
requires:
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 03
    provides: "fetch löst message: und table: auf, die zwei Zweige, die hier live belegt werden"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 04
    provides: "das Talk-Bein, TALK_BUDGET als Setzung, MAX_DIGEST, der Digest als Projektion einer Liste"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 05
    provides: "das Mail-Bein, MAIL_BUDGET und MAX_MAIL_ACCOUNTS als Setzungen, der Envelope {results,total}"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    plan: 08
    provides: "die Regel, dass die zu prüfende Operation nicht das Messwerkzeug sein darf, plus die GreenMail-Topologie"
  - phase: 04
    plan: 04
    provides: "die Referenzmessung 0,84 s kurz und 0,99 s voll, gegen die Erfolgskriterium 2 vergleicht"
provides:
  - "tests/integration/test_ctx_bundle.py: neun Messungen, neunzehn gedruckte Messzeilen, Marker integration"
  - "11-06-MEASUREMENTS.md: Topologie, Reproduktionsbefehl, 13-zeilige Nachweistabelle, Wanduhr, Requestkosten, Nebenwirkungsfreiheit, Offene Punkte"
  - "die Messzeilen an CALENDAR_BUDGET, TALK_BUDGET, MAIL_BUDGET und MAX_MAIL_ACCOUNTS"
  - "die korrigierte Kostenaussage: drei Erkennungsrequests je Bündel bei kaltem Cache, nicht zwei"
affects:
  - "11-09 (Changelog 0.1.8) schreibt seinen Block aus 11-06-MEASUREMENTS.md"
  - "11-08 (Doku) kann die Wanduhr- und Kostenzahlen wörtlich übernehmen"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein httpx-Request-Hook als Requestzähler, aufgeschlüsselt nach Pfadpräfix, kalt und warm"
    - "Wanduhr je Bein über die privaten Bein-Helfer, weil die Wanduhr des Bündels das Maximum ist und nicht sagt, von welchem Teil sie kommt"
    - "Beweis nur bei entscheidbarer Lage: eine Divergenz gilt, wenn ein Fenster sie entscheidet, und truncated ist kein Vollständigkeitssignal"
    - "Ein Suchwort als Messkonstante mit zwei begründeten Anforderungen (drei Auszüge, kein Mail-Treffer), plus eine Behauptung, dass die zweite hält"
    - "Fremder Providerfehler ist kein gescheitertes Bein: behauptet wird die Abwesenheit der Timeout-Wendung, nie eine leere degraded-Liste"

key-files:
  created:
    - tests/integration/test_ctx_bundle.py
    - .planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-06-MEASUREMENTS.md
  modified:
    - src/mcp_connector/tools/context.py

key-decisions:
  - "Keine der vier Zeitbudget-Konstanten wird geändert: jedes gedeckelte Bein liegt mehr als hundertfach unter seiner Decke, und eine Absenkung würde bei der ersten langsamen Instanz Degradation im Normalfall erzeugen"
  - "Die Obergrenze, die Messung 1 behauptet, ist CALENDAR_BUDGET (10 s) und nicht die Referenz selbst: eine Grenze bei 0,84 s würde den Entwicklungsrechner messen statt den Code, eine Grenze bei der grössten Einzeldecke fängt genau den sequenziellen Regress (T-11-40)"
  - "Die Wanduhr je Bein wird zusätzlich gemessen, weil die vier Konstantenkommentare je eine Zahl brauchen und die Bündel-Wanduhr als Maximum der Teile keine liefert"
  - "Der Beweis für 'unread ist kein Nachrichtenzähler' läuft über den umgekehrten Fall (sechs lesbare Nachrichten, unread 0), weil die Falle T12 auf dieser Instanz nicht vorhanden ist; der T12-Fall wird zusätzlich geprüft, wenn er da ist"
  - "truncated auf der Nachrichtenebene heisst 'die App hat eine Fortsetzungs-Id mitgegeben' und nicht 'es gibt mehr zu lesen': eine Divergenz gilt deshalb nur, wenn ein Fenster sie entscheidet"
  - "Die Nebenwirkungsmessung sucht sich eine Zielkonversation mit Ungelesenem: ein Zähler, der schon 0 ist, kann nicht fallen, und die gedruckte Zeile sagt immer, welcher der zwei Fälle gemessen wurde"
  - "Das Suchwort der Messung ist 'Abnahme': es erzeugt dieselben drei Auszüge wie die Referenz und erreicht den Mail-Suchprovider nicht, und die zweite Eigenschaft wird behauptet, damit das Betreff-Gate eine Aussage über das Zählerbein bleibt"
  - "Die Datei legt nichts an, also gibt es kein finally: ein finally ohne Inhalt ist ein Versprechen ohne Deckung; stattdessen liest der letzte Test den Endzustand"
  - "Die Kostenaussage im Docstring wird von zwei auf drei Erkennungsrequests je Bündel korrigiert: zwei gehören dem Mail-Bein, der dritte entsteht aus dem Rennen des Talk-Beins um denselben leeren Cache-Eintrag"

patterns-established:
  - "Ein Messdokument je Messplan mit der Nachweistabellenform von docs/store-submission.md (Datum mit Zeit in Z, Behauptung als ganzer Satz, Befehl)"
  - "Konstantenkommentar plus Messdokument als Paar: keine Zahl im Kommentar ohne Zeile im Dokument, kein Verweis auf ein Dokument, das nicht existiert"

requirements-completed: [CTX-01, CTX-02]

# Metrics
duration: 27min
completed: 2026-08-24
---

# Phase 11 Plan 06: Die Live-Messung der vier Beine Summary

**`prepare_context` mit vier Beinen ist gegen die Referenz aus Plan 04-04 gemessen statt geschätzt: Wanduhr 0,65 s bis 1,13 s kurz und 0,85 s bis 1,83 s voll bei leerer `degraded`-Liste, 22 Requests kalt und 19 warm, das Mail-Bein 1+1 auf dieser Instanz, und `fetch("message:...")` bewegt keinen der drei Zähler der Zielkonversation, gemessen über die Konversationsliste und nie über die geprüfte Route. Drei Setzungen sind jetzt Messungen, keine davon musste geändert werden, und der Kommentar, der auf eine verschwundene Datei zeigte, zeigt auf ein Dokument, das existiert.**

## Performance

- **Duration:** ca. 27 min
- **Started:** 2026-08-24T21:04Z
- **Completed:** 2026-08-24T21:31Z
- **Tasks:** 2
- **Files created/modified:** 3

## Task Commits

1. **Task 1: Das Messprotokoll als Integrationstest** - `746e9c3` (test)
2. **Task 2: Das Nachweisdokument und die vier Messzeilen** - `6a3bfa1` (docs)

## Die gemessenen Zahlen

### Wanduhr, drei Läufe mit je drei Aufrufen je Detailstufe

| Lauf | short min / median / max | full min / median / max |
|---|---|---|
| A, 21:12Z | 1,01 s / 1,13 s / 2,04 s | 1,40 s / 1,83 s / 2,07 s |
| B, 21:18Z | 0,77 s / 0,81 s / 1,85 s | 0,84 s / 0,85 s / 0,92 s |
| C, 21:25Z | 0,65 s / 0,65 s / 1,75 s | 0,84 s / 0,85 s / 1,27 s |

Referenz aus Plan 04-04 (zwei Beine): 0,84 s kurz, 0,99 s voll. `degraded` war in allen sechs
Zeilen leer. Der Maximalwert jeder Zeile ist immer der erste, kalte Aufruf. Lauf A liegt
insgesamt höher, das ist Last auf dem Entwicklungsrechner, und er steht im Dokument statt
weggelassen zu werden.

Die Zahl, die nicht streut, ist die je Bein: Suche 0,65 s bis 0,73 s, Kalender 0,07 s bis
0,08 s, Talk 0,04 s, Mail 0,06 s. Daran hängt die Antwort auf Erfolgskriterium 2: die Wanduhr
des Bündels hängt an der Suche, und die zwei neuen Beine addieren nichts, weil sie im selben
`gather` weit unter dem längsten Bein bleiben.

### Requestzahl je Bündelaufruf

| | kalt | warm |
|---|---|---|
| Summe | **22** | **19** |
| `/cloud/capabilities` | 2 | 0 |
| `/core/navigation/apps` | 1 | 0 |
| Providerliste plus 13 Provideranfragen | 14 | 14 |
| `/apps/mail/account/list` | 1 | 1 |
| `/apps/mail/ocs/mailboxes` | 1 | 1 |
| Talk-Konversationsliste | 1 | 1 |
| Kalender (PROPFIND plus REPORT) | 2 | 2 |

Die Kostenformel wörtlich: **1 Kontenliste plus N Postfachlisten** (N höchstens
`MAX_MAIL_ACCOUNTS` = 3, auf dieser Instanz 1), **plus die Erkennungsrequests**, und die
gemessene Zahl je Bündel ist **drei kalt und null warm** innerhalb von
`capabilities.TTL_SECONDS` (60 s).

### Nebenwirkungsfreiheit, vier Werte vorher und nachher

`fetch("message:6c3pifti:17")`, Id aus einem echten Suchtreffer (Suchwort "moderation"), Ziel
bewusst eine Konversation mit Ungelesenem:

| Feld | Vorher | Nachher |
|---|---|---|
| `unread` | 7 | 7 |
| `unread_mention` | `false` | `false` |
| `unread_mention_direct` | `false` | `false` |
| `unread` der übrigen vier Konversationen | 0, 0, 3, 0 | 0, 0, 3, 0 |

Gelesen über `talk_browse(level="conversations")`, nie über
`GET .../chat/{token}/{messageId}/context`, also nicht mit der Operation, die geprüft wird.

### Die endgültigen Werte der vier Zeitbudget-Konstanten

| Konstante | Wert | Änderung gegenüber 11-04 / 11-05 | Gemessener Wert des Beins | Abstand |
|---|---|---|---|---|
| `CALENDAR_BUDGET` | 10.0 | keine | 0,07 s bis 0,08 s | Faktor 114 bis 133 |
| `TALK_BUDGET` | 5.0 | **keine** (war Setzung, ist jetzt Messung) | 0,04 s | Faktor 129 bis 138 |
| `MAIL_BUDGET` | 10.0 | **keine** (war Setzung, ist jetzt Messung) | 0,06 s | Faktor 151 bis 152 |
| `MAX_MAIL_ACCOUNTS` | 3 | **keine** (war Setzung, jetzt mit unterer Schranke belegt) | 1 Konto, 1 Postfachliste | Kappe biss nicht |

Kein Wert wurde geändert. Die Begründung steht im Dokument: eine Decke, die im gesunden Fall
mehr als hundertfach entfernt ist, tut genau das, wofür sie da ist, und eine Absenkung würde bei
der ersten langsamen Instanz Degradation im Normalfall erzeugen.

### Der Pfad des Nachweisdokuments

`.planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-06-MEASUREMENTS.md`

Plan 11-09 schreibt den Changelog-Block von 0.1.8 daraus. Es trägt Topologie (sechs Container,
drei App-Versionen, Nextcloud 34.0.3), den vollständigen Reproduktionsbefehl, eine
Nachweistabelle mit 13 Zeilen in der Form von `docs/store-submission.md`, und die Abschnitte
Wanduhr, Requestkosten, Nebenwirkungsfreiheit und Offene Punkte.

## Was gebaut wurde

`tests/integration/test_ctx_bundle.py` (795 Zeilen), neun Tests, neunzehn gedruckte Messzeilen:

| Messung | Was sie behauptet |
|---|---|
| 1 Wanduhr | Minimum, Median, Maximum je Detailstufe, plus die vier Beine einzeln; Obergrenze `CALENDAR_BUDGET`, und kein `degraded`-Eintrag nennt eine verpasste Zeitdecke |
| 2 Requestzahl | 1 Kontenliste, N Postfachlisten, kein weiterer Mail-Request; kalt mindestens ein Erkennungsrequest, warm genau null |
| 3 Digest | Kappe `MAX_DIGEST` hält, im Digest steht nur, wo etwas wartet, und `unread` ist kein Nachrichtenzähler |
| 4 Mail-Zähler | `inbox_unread` gleich `mail_browse(level="mailboxes")`, kein GreenMail-Betreff im Bündel, und die Suche erreicht den Mail-Provider nicht |
| 5 Nebenwirkungsfreiheit | drei Zählerfelder gleich vor und nach `fetch("message:...")`, gelesen über die Konversationsliste |
| 6 Ein `fetch` je neuem Kind | `message` und `table` je aus einem echten Suchtreffer, mit `metadata.kind` und einer `url` aus der konfigurierten Basis-Adresse |
| Gate | keine Messzeile trägt `APP_SECRET`, kein Auth-Headername, kein App-Passwort |
| Endzustand | `unread` je Konversation nach dem Lauf, gemessen statt angenommen |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Falsche Annahme über die Instanz] Die Falle T12 ist nicht vorhanden, der Beweis läuft über den umgekehrten Fall**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt für Messung 3 den Beweis am Fall `unread == 1` bei leerer Historie. Gemessen am 2026-08-24: die Changelog-Konversation dieser Instanz (`q5s5xqp5`, Typ 4) meldet `unread` 3 bei drei lesbaren Nachrichten, und keine der fünf Konversationen trägt Ungelesenes bei leerer Historie. Ein Test, der diesen Fall behauptet, wäre rot geworden, ohne etwas über den Code zu sagen.
- **Fix:** Der Test behauptet die allgemeine Form derselben Aussage, eine Divergenz zwischen `unread` und der Zahl der lesbaren Nachrichten, und findet sie im umgekehrten und stärkeren Fall: `o4vwrd7g` trägt sechs lesbare Nachrichten und meldet `unread` 0. Der T12-Fall wird zusätzlich geprüft, wenn er da ist (aktuell null Vorkommen), und das Dokument nennt die Abweichung unter Offene Punkte.
- **Files modified:** tests/integration/test_ctx_bundle.py, 11-06-MEASUREMENTS.md
- **Commit:** 746e9c3, 6a3bfa1

**2. [Rule 1 - Falsches Vollständigkeitssignal] `truncated` auf der Nachrichtenebene taugt nicht als Vollständigkeitsprüfung**

- **Found during:** Task 1
- **Issue:** Der erste Zuschnitt von Messung 3 filterte Konversationen mit `truncated` heraus, um nur vollständig gelesene Historien zu vergleichen. Gemessen: **alle fünf** Konversationen tragen `truncated`, auch die mit null lesbaren Nachrichten, weil `talk._messages` das Feld an der Fortsetzungs-Id der App festmacht und nicht an der Zahl der Nachrichten. Der Filter löschte die gesamte Datenmenge und die Behauptung fiel über eine leere Liste.
- **Fix:** Eine Divergenz gilt nur als bewiesen, wenn ein Fenster sie entscheidet: `unread` unter dem Fenster ist Beweis für sich (weitere Seiten können nur dazuzählen), `unread` über dem Fenster nur ohne Fortsetzung. Als benannte Funktion `_settles_the_question` mit Begründung, plus ein Absatz im Docstring der Messung.
- **Files modified:** tests/integration/test_ctx_bundle.py
- **Commit:** 746e9c3

**3. [Rule 2 - Fehlende Notwendigkeit] Die vier Konstantenkommentare brauchen eine Zahl je Bein, die die Bündel-Wanduhr nicht liefert**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt in Task 2 je Konstante eine Messzeile mit "gemessener Wert und Abstand zum Budget". Messung 1 wie geplant liefert nur die Wanduhr des ganzen Bündels, und die ist per Vertrag das Maximum der Teile: sie sagt nicht, welcher Teil sie erzeugt hat. Damit hätten drei der vier Kommentare eine Zahl behauptet, die nirgends gemessen ist.
- **Fix:** Messung 1 misst die vier Beine zusätzlich einzeln, über genau die Helfer, die das Bündel aufruft (`_events`, `_talk`, `_mail`, `unified_search` mit `SEARCH_LIMIT`), je dreimal, und behauptet je Bein, dass sein Maximum unter seiner eigenen Decke bleibt. Daraus kommen die Zahlen in den Kommentaren und die Abstandstabelle im Dokument.
- **Files modified:** tests/integration/test_ctx_bundle.py, src/mcp_connector/tools/context.py
- **Commit:** 746e9c3, 6a3bfa1

**4. [Rule 1 - Unwahre Kostenaussage] Ein Bündel zahlt drei Erkennungsrequests bei kaltem Cache, nicht zwei**

- **Found during:** Task 1
- **Issue:** Der Modul-Docstring von `context.py`, der Docstring von `prepare_context` und der von `_mail` sagten alle drei "plus up to two detection requests on a cold cache". Gemessen: zweimal `/cloud/capabilities` plus einmal `/core/navigation/apps`, also drei. Zwei gehören dem Mail-Bein (`load_mail` liest beide Kanäle), der dritte entsteht, weil das Talk-Bein gleichzeitig startet und auf dem leeren Cache mit dem Mail-Bein um denselben Eintrag rennt.
- **Fix:** Alle drei Stellen präzisiert: zwei ist der Anteil des Mail-Beins, drei ist der Preis eines Bündels, null ist der Preis des zweiten Bündels innerhalb der TTL. Das Rennen selbst wird **nicht** behoben: eine Sperre im Capabilities-Cache wäre eine strukturelle Änderung (Rule 4) für einen doppelten GET auf einem leeren Cache, und der Befund steht stattdessen im Dokument.
- **Files modified:** src/mcp_connector/tools/context.py, 11-06-MEASUREMENTS.md
- **Commit:** 6a3bfa1

### Nicht abgewichen

- Kein `uv add`, kein `pip install`, kein `npm install`: `pyproject.toml` und `uv.lock` sind unangetastet (T-11-SC).
- `git diff --stat` zeigt keine Änderung an `src/mcp_connector/server/` und keine an `src/mcp_connector/tools/` ausser `context.py`.
- Keine `Field`-Beschreibung und kein Schema geändert: das Budget-Gate meldet dieselbe Messung wie nach 11-05 (15769 Bytes, 21 Werkzeuge, Budget 18500).
- Die Datei legt nichts an und räumt nichts ab; der Docstring sagt das ausdrücklich.

## Beobachtet und nicht behauptet

- **Ein einmaliger 404 auf `/apps/mail/account/list`** während der Vorerkundung um etwa 21:07Z: das Mail-Bein fiel mit genau einem `degraded`-Satz aus, das Bündel blieb im Übrigen vollständig, der nächste Aufruf war grün. In zwölf aufeinander folgenden Bündelaufrufen und drei vollen Testläufen nicht wieder aufgetreten, also ist die Ursache nicht gemessen und wird nicht behauptet. Das Verhalten im Fehlerfall war genau das entworfene.
- **Der Deck-Kommentar-Provider antwortet sporadisch 500.** Das Suchbein reicht das als eigenen `degraded`-Eintrag durch. Deshalb behauptet keine Messung eine leere `degraded`-Liste, sondern die Abwesenheit von Einträgen, die eine verpasste Zeitdecke nennen.
- **Die Referenz aus Plan 04-04 kommt aus einer MCP-Sitzung, diese Messung aus dem Testprozess.** Der Client- und Proxy-Sprung fehlt hier, also ist der Vergleich aussagekräftig und nicht auf die zweite Stelle belastbar. Beide Zahlen stehen im Dokument.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün (197 Dateien) |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run pytest -q` (Standardauswahl) | Exit 0, kein Container gestartet |
| `uv run pytest tests/integration/test_ctx_bundle.py --collect-only -q -m integration` | 9 Tests |
| `uv run pytest tests/integration/test_ctx_bundle.py -m integration -q -rA -s` | Exit 0, 9 passed, 19 Messzeilen gedruckt |
| `uv run pytest tests/contract -q` | Exit 0, 65 Tests |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 15769 Bytes, 21 Tools, Budget 18500 |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | Exit 0 |
| Gate-Skript aus Task 2 | "measurement document and constants aligned" |
| `git diff --stat` gegen die verbotenen Pfade | leer |

## Für die Folgeplane

- **11-08 (Doku):** Wanduhr und Requestkosten stehen abschreibfertig in `11-06-MEASUREMENTS.md`; die drei READMEs können die 1+N-Formel wörtlich übernehmen, inklusive der drei Erkennungsrequests.
- **11-09 (Changelog 0.1.8):** der Block über `prepare_context` kommt aus den Abschnitten Wanduhr und Requestkosten; die nutzerrelevante Aussage ist "vier Quellen in einem Aufruf, Wanduhr unverändert gegenüber zwei Quellen".
- **CTX-01 und CTX-02** dürfen als erfüllt gelten: das Verhalten der bestehenden Quellen ist gegen die Referenz gemessen, die Request-Kosten der Mail-Zähler sind gemessen und aufgeschrieben.
- **Ein offener Beobachtungspunkt** ohne Handlungsbedarf in dieser Phase: das Rennen zweier Beine um den leeren Capabilities-Cache kostet einen doppelten GET je kaltem Bündel. Eine Sperre im Cache wäre eine strukturelle Entscheidung und gehört nicht in einen Messplan.

## Known Stubs

Keine. Dieser Plan fügt keinen Produktionscode hinzu; die Änderung an `context.py` besteht aus
Kommentaren und Docstrings.

## Self-Check: PASSED

- `tests/integration/test_ctx_bundle.py`: FOUND
- `.planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-06-MEASUREMENTS.md`: FOUND
- `src/mcp_connector/tools/context.py`: FOUND (geändert)
- Commit `746e9c3`: FOUND
- Commit `6a3bfa1`: FOUND
