---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 08
subsystem: testing
tags: [integration, greenmail, srv-06, degradation, berechtigungstreue, nebenwirkungsfreiheit]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-01: GreenMail in compose.exapp.yml, das Mail-Konto von alice und die sechs Testmails"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-06: mail_browse als registriertes Werkzeug, fetch mail:<id> als Volltextweg"
  - phase: 02-exapp-shell
    provides: "Die HaRP-Topologie und die AppAPI-Impersonation, unter der beide Läufe messen"
provides:
  - "tests/integration/test_mail_read.py: 24 grüne Behauptungen über drei Ebenen, Volltext, Filter, Nebenwirkungsfreiheit und die Zwei-Konten-Grenze"
  - "tests/integration/test_srv06_degradation.py: 11 grüne Behauptungen, sechs Nachweiszeilen, drei Neustart-Zyklen mit gemessenem Endzustand"
  - "Das Messprotokoll dieser Phase in Zahlen (unten), inklusive der zwei Übergaben an Phase 11"
affects: [phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Fehlt-Zweig einer App wird nur nach einem Neustart der Instanz gemessen, nie ohne"
    - "Eine Zustandsänderung an der Topologie wird memoisiert: eine Disable/Restore-Runde je Familie, mehrere Behauptungen darauf"
    - "Das Aufräumen steht im finally, der Endzustand wird gemessen und nicht angenommen"
    - "Nebenwirkungsfreiheit wird über eine andere Route gemessen als die, die geprüft wird"

key-files:
  created:
    - "tests/integration/test_mail_read.py"
    - "tests/integration/test_srv06_degradation.py"
  modified: []

key-decisions:
  - "flags.seen wird über die Envelope-Route gelesen und nicht über den Volltextweg: die zu prüfende Operation darf nicht das Messwerkzeug sein"
  - "Die Umlaut-Behauptung der Textmail steht auf ü und ß, nicht auf allen vieren: der Fixture-Körper trägt kein ä und kein ö, eine Behauptung darüber wäre aus einem anderen Grund rot geworden"
  - "Die spitze Klammer der Textmail (5 < 7) darf überleben; nur die HTML-Mail wird auf < und > geprüft, weil dort jede Klammer Markup wäre"
  - "Die drei Fehlersätze stehen als Literal im Test UND werden gegen capabilities.app_missing verglichen: das Literal ist der Vertrag, der Vergleich verhindert das Auseinanderlaufen"
  - "Kein MSYS_NO_PATHCONV nötig: die occ-Aufrufe laufen als festes argv über docker exec mit relativem occ, nicht über eine Shell; der Hinweis für die Handreproduktion steht trotzdem im Docstring"
  - "SRV-06 wird abgehakt; MAIL-01 bis MAIL-03 waren schon Complete und werden hier live bestätigt"

patterns-established:
  - "Eine Degradationsmessung memoisiert ihre Zustandsänderung, damit N Behauptungen nicht N Neustarts kosten"
  - "Ein Zwei-Konten-Beweis behauptet ausdrücklich, welche Ablehnung er NICHT ist"

requirements-completed: [SRV-06]

# Metrics
duration: 22min
completed: 2026-08-24
---

# Phase 10 Plan 08: Der Live-Nachweis und der SRV-06-Beweis, Zusammenfassung

**Die Aussagen dieser Phase sind jetzt gemessen statt behauptet: ein Nutzer liest an echten Daten sein Konto, sein Postfach und sechs Envelopes, liest drei Mails im Volltext, ohne dass ein einziges `\Seen` gesetzt wird, kommt mit einem zweiten Konto an nichts davon heran, und alle drei neuen Familien verschwinden sauber, gemessen in einem Zustand, in dem ihre App wirklich fehlt.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-24T15:02Z
- **Completed:** 2026-08-24T15:24Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments

- `tests/integration/test_mail_read.py` (769 Zeilen, 24 Tests) läuft grün gegen die Topologie und wird ohne sie mit dem Namen der fehlenden Umgebungsvariable übersprungen. Der Lauf geht durch `mail_tools.browse` und `chatgpt.fetch`, also durch die Werkzeugpfade, weil die Erfolgskriterien Aussagen über das sind, was ein Nutzer bekommt.
- `tests/integration/test_srv06_degradation.py` (549 Zeilen, 11 Tests) schaltet drei Apps ab, startet die Nextcloud dazwischen je einmal neu, misst, und stellt den Ausgangszustand wieder her. Der Endzustand wird gemessen: `occ app:list` nennt `mail`, `spreed` und `tables` danach wieder als aktiviert, und alle drei Werkzeuge liefern wieder fachliche Ergebnisse.
- Kein Produktionscode angefasst: `git diff` gegen `src/`, `pyproject.toml`, `uv.lock` und `appinfo/info.xml` ist leer. Dieser Plan misst.
- `test_mail_read.py` läuft nach dem Degradationslauf unverändert grün: die Wegwerf-Topologie ist nicht beschädigt.

## Das Messprotokoll in Zahlen

### Die drei Ebenen

| Ebene | Gemessen |
|-------|----------|
| Konten | **1** (`alice@example.test`, id 4); die Antwort trägt keinen IMAP-Host, keinen Port und kein Passwort |
| Postfächer | **1** (`INBOX`, `special_role="inbox"`, `unread=6`, `delimiter="."`) |
| Envelopes | **6**, davon **5 mit `preview`**; jede `id` in der Form `mail:<Zahl>`; kein Element trägt ein Feld aus `flags` |
| Fenster ohne `limit` | **6** Nachrichten (`DEFAULT_LIMIT=20`, `MAX_LIMIT=50`), also mehr als eine: Falle K3 schlägt nicht durch |

Vorschaulängen in Zeichen: Textmail 229, Newsletter 251, grosser Newsletter 251, `Rechnung` 41, `Rechnung Mai` 38, `Nur ein Anhang` 0. Das deckt sich mit der Messung von Plan 10-01 auf ein Zeichen genau (38 statt 39 bei `Rechnung Mai`, weil die Mail neu eingeliefert wurde).

### Der Volltext

| Nachricht | Text nach der Wandlung | Ergebnis |
|-----------|------------------------|----------|
| `Newsletter August` | **26684 Bytes** | ungekappt; kein `<`, kein `>`, keine Entity, kein `script`-Inhalt; `metadata` = `date, dkim, kind, sender_trusted, signature`, alle Werte `str` |
| `Gruesse aus Hamburg, die Masse stehen unten` | **235 Bytes** | echte `ü` und `ß`, kein `&uuml;`, kein `&szlig;`, kein `&amp;`, kein `<a `; die URL steht als Text da, und die spitze Klammer des Absenders (`5 < 7`) überlebt als Zeichen |
| `Grosser Newsletter August` | **32845 Bytes** | gekappt bei 32768, `metadata["truncated"] == "true"`, der dritte Marker (`FINAL_TRUNCATION`) genau einmal am Ende |
| `Nur ein Anhang` | - | abgelehnt mit einem Satz, der den Grund nennt (kein Textkörper, nur Anhang), statt mit einer leeren Erfolgsantwort |

Die zehn möglichen `metadata`-Schlüssel von Plan 10-05 sind an dieser Instanz nicht alle erreichbar: `mailbox` fehlt in allen gemessenen Antworten, weil die Volltextantwort dieser Fassung kein positives `mailboxId` trägt, und `encrypted`, `phishing_warning` und `phishing_checks` fehlen, weil keine Testmail sie auslöst. Der Test behauptet deshalb nur die vier immer vorhandenen (`kind`, `sender_trusted`, `dkim`, `signature`) plus "jeder Wert ist ein `str`"; ein bedingter Schlüssel als Pflicht wäre eine ehrliche Auslassung zu einem Fehler erklärt.

### Nebenwirkungsfreiheit

| Messpunkt | Vorher | Nachher |
|-----------|--------|---------|
| `flags.seen` von `mail:16` (`Rechnung`) | **`false`** | **`false`** |
| `unread` der INBOX | **6** | **6** (am Ende des gesamten Laufs, nach drei Volltextabrufen) |

Beide Zahlen werden über die **Envelope**-Route gelesen und nicht über den Volltextweg: die Operation, die nichts verändern soll, darf nicht das Messwerkzeug sein.

### Die Filter

| Filter | Treffer von 6 |
|--------|---------------|
| `is:unread` | 6 |
| `from:buchhaltung` | 2 |
| `subject:Rechnung` | 2 |
| `subject:Rechnung%20Mai` | 1 |
| `start:1000000000` | 6 |
| `tags:1` | 1 |
| `is:ungelesen` | **abgelehnt**: `'ungelesen' is not a message state this connector filters on.` |
| `subject:` | **abgelehnt**: `The filter condition 'subject:' has no value.` |
| `start:2026-08-01` | **abgelehnt**: `'2026-08-01' is not a Unix timestamp, so start: cannot use it.` |

Gegenprobe: die drei verengenden Filter (`from:`, `subject:` mit kodiertem Wortpaar, `tags:`) liefern 2, 1 und 1 gegen eine Grundlinie von 6. Ohne sie wäre die Zahl 6 bei `is:unread` und `start:` nicht von einem still verworfenen Filter zu unterscheiden.

### Die Zwei-Konten-Grenze (Falle 15)

| Aufruf als bob | Ergebnis |
|----------------|----------|
| `browse(level="accounts")` | **0 Konten, ein Erfolg** und kein Fehler |
| `browse(level="mailboxes", account_id=4)` | abgelehnt: `Nextcloud did not find the mailboxes of account 4.` |
| `browse(level="messages", mailbox_id=3)` | abgelehnt: `The Mail app could not read the messages of mailbox 3 from the mail server of this account.` |
| `fetch("mail:13")` | abgelehnt: `Nextcloud did not find the message 13.` |

Jede der drei Ablehnungen wird zusätzlich daraufhin behauptet, dass sie **nicht** unsere eigene "du hast die account_id vergessen"- oder "du hast die mailbox_id vergessen"-Meldung ist und nicht von bobs fehlendem Konto handelt, und dass sie weder alices Betreff noch ihren Vorschautext preisgibt. Insgesamt hat der Lauf **7 Ablehnungen** produziert, und über alle sieben gilt: kein `Traceback`, kein führendes `<`, kein `<html`, kein `/login`, ein Hinweis, der sich von der Meldung unterscheidet.

## Die sechs Degradationszeilen

| Familie | Zustand | Neustart dazwischen | Einstiegspunkt | Antwort |
|---------|---------|---------------------|----------------|---------|
| spreed | vorhanden | nein | `talk_browse` | 5 Unterhaltungen |
| spreed | fehlt | **ja** (2,0 s bis `installed: true`) | `talk_browse` | `The Talk app is not available on this Nextcloud.` |
| tables | vorhanden | nein | `tables_browse` | 2 Tabellen |
| tables | fehlt | **ja** (1,8 s) | `tables_browse` | `The Tables app is not enabled on this Nextcloud.` |
| mail | vorhanden | nein | `mail_browse` | 1 Konto, `navigation=True`, `providers=True` |
| mail | fehlt | **ja** (1,9 s) | `mail_browse` | `The Mail app is not available on this Nextcloud.` |
| mail | fehlt | **ja** (dieselbe Runde) | `fetch("mail:1")` | `The Mail app is not available on this Nextcloud.` |
| mail | fehlt | **ja** (dieselbe Runde) | beide Erkennungskanäle | `navigation=False`, `providers=False` |

Je Fehlt-Zeile wird behauptet: der Satz ist genau der aus `capabilities._MISSING`, der Hinweis unterscheidet sich von der Meldung und nennt eine Handlung, der Text trägt kein `Traceback`, beginnt nicht mit `<`, enthält kein `<html`, kein `/login` und **nicht** die Wendung `search for it first`, also nicht den 404-Zweig des gemeinsamen Parsers, in dem eine fehlende App ohne Vorprüfung landen würde.

Der Neustart ist die Zeile, die diesen Test überhaupt rechtfertigt: ohne ihn antworten Navigation und Mail-Routen nach `occ app:disable mail` weiter mit 200, und der Fehlt-Zweig wäre nie erreicht worden. Gemessen hat der Neustart nur **rund zwei Sekunden** gekostet, deutlich weniger als der Plan befürchtet hat; die drei Runden zusammen kosten den Lauf 18 Sekunden.

## Task Commits

1. **Task 1: Der Live-Nachweis, dass Mail lesbar ist und das Lesen nichts verändert** - `4b8643b` (test)
2. **Task 2: Der Degradationsnachweis für alle drei Familien, jeweils mit Neustart** - `2bbc310` (test)

## Files Created/Modified

- `tests/integration/test_mail_read.py` - NEU, 769 Zeilen, 24 Tests. Fixtures `alice`, `bob`, `account_id`, `mailbox_id`, `envelopes` mit Skip-Sätzen, die den Bootstrap-Schritt nennen; Messprotokoll über `-s`; `seen_state` liest über die Envelope-Route
- `tests/integration/test_srv06_degradation.py` - NEU, 549 Zeilen, 11 Tests. `app_disabled` als Kontextmanager mit `finally`, `restart_nextcloud` als Poll statt Sleep, `_missing` als Memo für eine Runde je Familie, `assert_named_and_nothing_else` mit den sechs Behauptungen je Zeile

## Decisions Made

- **`flags.seen` wird über die Envelope-Route gelesen.** Der Volltextweg ist die Operation, die nichts verändern soll; ihn als Messwerkzeug zu benutzen hiesse, die Prüfung mit dem Prüfling zu machen. Die Envelope-Route trägt das ganze `flags`-Objekt und öffnet keine IMAP-Sitzung für einen Körper.
- **Eine Disable/Restore-Runde je Familie, memoisiert.** Vier Behauptungen über den Mail-Fehlt-Zustand hätten sonst vier Neustarts gekostet. Das Muster ist das von `test_exapp_mail_reach.py` (`_measured` plus `_row`), und es hat hier einen zweiten Grund: eine fehlschlagende Behauptung darf nie die Wiederherstellung verhindern, und im Memo-Aufbau ist sie zum Zeitpunkt jeder Behauptung längst gelaufen.
- **Die drei Fehlersätze stehen doppelt.** Als Literal, weil das der Satz ist, den ein Nutzer liest, und als Vergleich gegen `capabilities.app_missing`, damit die Kopie nicht unbemerkt altert. Ein eigener Test hält genau diese Gleichheit.
- **Kein `MSYS_NO_PATHCONV`.** Der Plan verlangt es für Git-Bash-Aufrufe; dieser Prozess spricht mit festem argv über `docker exec ... php occ` mit relativem `occ`, also rewritet keine Shell irgendetwas. Der Hinweis steht trotzdem im Modul-Docstring, weil die Reproduktionszeile die ist, die kopiert wird.
- **SRV-06 wird abgehakt.** MAIL-01 bis MAIL-03 standen bereits auf Complete (Pläne 10-04 bis 10-06); dieser Lauf bestätigt sie live, ändert an ihrem Zustand aber nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Umlaut-Behauptung der Textmail war falsch geschrieben**
- **Found during:** Task 1, erster Lauf
- **Issue:** Der Test behauptete `ü`, `ö`, `ä` und `ß` im gewandelten Text der reinen Textmail. Der Körper dieser Testmail trägt nur `ü` und `ß` ("Grüße", "Maße", "Straße", "Büro"); ein `ä` und ein `ö` kommen darin nicht vor. Der Test war rot aus einem Grund, der nichts mit der Wandlung zu tun hat, also aus dem falschen Grund.
- **Fix:** Die Behauptung steht auf den zwei Zeichen, die die Fixture wirklich schreibt, mit einem Kommentar, warum ein drittes hier nichts belegen würde.
- **Files modified:** `tests/integration/test_mail_read.py`
- **Verification:** Der Lauf ist danach grün, und der Nachweis zu Korrektur K2 (keine Entities, kein `<a `) bleibt vollständig.
- **Committed in:** `4b8643b`

### Bewusste Abweichungen von der Planvorgabe

**2. Vier `metadata`-Schlüssel behauptet, nicht die zehn aus Plan 10-05**
- Der Plan sagt "`metadata` trägt die Schlüssel aus Plan 10-05, jeder mit einem `str` als Wert". Sechs der zehn sind bedingt (`mailbox`, `date`, `encrypted`, `phishing_warning`, `phishing_checks`, `truncated`), und `mailbox` ist an dieser Instanz in **keiner** Antwort vorhanden. Behauptet werden die vier immer vorhandenen plus "jeder Wert ist ein `str`"; `truncated` wird beim grossen Newsletter eigens behauptet. Ein bedingter Schlüssel als Pflicht hätte eine ehrliche Auslassung zu einem Fehler erklärt.

**3. Elf Tests statt der acht des Gates in `test_srv06_degradation.py`**
- Der Verifikationsschritt des Plans verlangt `>= 8`. Es sind elf, weil die Vertragsprüfung der drei Sätze, der Erkennungskanal-Vergleich und das Protokoll je einen eigenen Namen tragen. Kein Scope-Zuwachs: alle elf messen dieselben drei Disable-Runden.

**4. Der Zwei-Konten-Test von Task 1 ist auf zwei Tests aufgeteilt**
- Der Plan beschreibt einen Test 10. Umgesetzt sind zwei: einer für "bob sieht null Konten, und das ist ein Erfolg" und einer für die drei Ablehnungen an alices echten Ids. Die Vorbedingung und die Grenze sind zwei Aussagen, und ein gemeinsamer Test hätte im Protokoll nicht unterscheidbar gemacht, welche der beiden gerade rot ist. Das ist genau die Verwechslung, gegen die Falle 15 warnt.

---

**Total deviations:** 1 auto-fixed (Rule 1), 3 bewusste Abweichungen von der Formulierung des Plans.
**Impact on plan:** Kein Scope-Zuwachs, kein Produktionscode angefasst, keine Abhängigkeit installiert.

## Issues Encountered

- Keine. Beide Läufe waren nach einer einzigen Korrektur grün, die Topologie hat drei Neustart-Runden ohne Nebenwirkung überstanden, und die Testmails haben die Disable/Enable-Runde der Mail-App unbeschadet überlebt (`mail_browse` liefert danach wieder ein Konto, `test_mail_read.py` wieder 24 grüne Tests).

## Übergaben an Phase 11

**1. Die Ungelesen-Zähler für CTX-02 kosten einen Request pro Konto.**
Sie stehen pro Postfach in der Postfachliste (`browse(level="mailboxes", account_id=...)`), also in genau einer Antwort je Konto. An dieser Topologie sind das **1 Konto und 1 Postfach**, also ein Request für den vollständigen Zähler; auf einer echten Instanz mit mehreren Konten ist es ein Request je Konto, und die Zahl der Postfächer je Konto entscheidet nur die Grösse der Antwort, nicht die Zahl der Aufrufe. `prepare_context` muss also entscheiden, ob es alle Konten sehen will oder eines.

**2. Das `unread`-Feld des Navigationseintrags ist gemessen und bleibt ungeklärt.**
Der Eintrag `mail` in `GET /ocs/v2.php/core/navigation/apps` sieht bei aktivem Mail-Konto mit sechs ungelesenen Nachrichten so aus:

```json
{"id": "mail", "order": 3, "href": "/apps/mail/", "type": "link", "name": "Mail",
 "app": "mail", "active": false, "unread": 0, "classes": "", "default": false}
```

`unread` steht auf **0**, obwohl die INBOX sechs ungelesene Nachrichten hält. Die Recherche hat denselben Wert gesehen; dieser Lauf bestätigt ihn. Die Bedeutung ist damit weiter ungeklärt, aber der beobachtete Wert steht fest: **Phase 11 darf dieses Feld nicht als Ungelesen-Zähler benutzen** und muss dafür die Postfachliste aus Übergabe 1 lesen. Nachforschen lohnt nur, wenn ein anderer Zähler gebraucht wird als der, der bereits verfügbar ist.

## Next Phase Readiness

- Erfolgskriterien 1 bis 3 und 5 der Phase sind gemessen; SRV-06 ist abgehakt.
- Beide Dateien tragen den Marker `integration` und laufen nicht in der Default-Auswahl; `uv run pytest -q` bleibt ohne Docker grün.
- Die Topologie steht nach dem Lauf wie vorher: `mail` 5.11.1, `spreed` 24.0.4, `tables` 2.2.2, alle aktiviert.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*

## Self-Check: PASSED

Beide neuen Dateien existieren, beide Task-Commits (`4b8643b`, `2bbc310`) stehen im Log, das
Dokument enthält keine Em-Dashes, und `git diff` gegen `src/`, `pyproject.toml`, `uv.lock` und
`appinfo/info.xml` ist leer.
