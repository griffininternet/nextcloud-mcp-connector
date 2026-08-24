---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 01
subsystem: infra
tags: [greenmail, imap, smtp, nextcloud-mail, docker-compose, bootstrap, messung]

# Dependency graph
requires:
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "Der Mail-Erreichbarkeits-Spike (MAIL-04) samt docs/spike-mail.md und der GreenMail-Vorlage, die dieser Plan eingelöst hat"
  - phase: 02-exapp-shell
    provides: "Die HaRP-Topologie compose.exapp.yml und scripts/bootstrap_exapp.sh, in die GreenMail als vierter Dienst eingehängt wurde"
provides:
  - "GreenMail 2.1.12 als Dienst der Wegwerf-Topologie, ohne veröffentlichten Port"
  - "Das Mail-Konto von alice auf greenmail:3143, mit sechs eingelieferten Testmails und Zwangssynchronisation"
  - "Vier Messwerte statt vier Annahmen: specialRole, previewText, Volltext-Byte-Längen, Filtergrammatik"
  - "Die entschiedene Byte-Kappe des Volltexts: 32 KiB (32768 Bytes)"
  - "Die Korrektur K1 in docs/spike-mail.md: die vier benutzten OCS-Leseformen sind deklariert"
affects: [10-02, 10-03, 10-04, 10-05, 10-06, 10-07, 10-08, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: ["greenmail/standalone:2.1.12 (nur Testtopologie)", "python:3.13-alpine (nur Wegwerf-Container der Einlieferung)"]
  patterns:
    - "Fixture-Idempotenz am Zustand des Fremdsystems statt an einer Markierungsdatei"
    - "Existenzprüfung einer Ressource vergleicht Identität UND Endpunkt, nie nur die Identität"
    - "Wegwerf-Container im Compose-Netz statt eines veröffentlichten Ports"

key-files:
  created: []
  modified:
    - "compose.exapp.yml"
    - "scripts/bootstrap_exapp.sh"
    - "docs/spike-mail.md"

key-decisions:
  - "Byte-Kappe des Volltexts: 32 KiB statt der 16 KiB des Startwerts, weil der gemessene Newsletter nach der Wandlung 25582 Bytes ergibt und bei 16 KiB gekappt wäre"
  - "Die Existenzprüfung des Mail-Kontos vergleicht Adresse und Endpunkt; ein Konto auf dem alten Host wird verworfen und neu angelegt (occ mail:account:delete existiert in Mail 5.11.1)"
  - "Reine Textmails liegen in einem multipart/mixed mit genau einem text/plain-Teil, weil GreenMail 2.1.12 nicht mehrteilige Nachrichten nicht ausliefern kann"
  - "Die Idempotenz der Einlieferung hängt an der Nachrichtenzahl im Postfach, nicht an einer Markierungsdatei: GreenMail hält alles im Arbeitsspeicher"
  - "MAIL-01 bis MAIL-03 bleiben Pending: dieser Plan misst die Grundlagen, die Werkzeuge bauen die Pläne 10-02 bis 10-08"
  - "tags: der Filtergrammatik nimmt die numerische Tag-Id, nicht das IMAP-Label (gemessen, korrigiert die Recherche)"

patterns-established:
  - "Messprotokoll mit erfundenen Daten darf Feldwerte drucken; ein Protokoll gegen echte Konten nicht (T-08-01 gegen T-10-02)"
  - "Ein Befund über das Testwerkzeug wird als solcher benannt und nicht dem geprüften System angelastet"

requirements-completed: []

# Metrics
duration: 42min
completed: 2026-08-24
---

# Phase 10 Plan 01: GreenMail und die vier Messwerte, Zusammenfassung

**Die Wegwerf-Topologie hat einen echten IMAP- und SMTP-Server bekommen, und aus den vier offenen Annahmen der Phase sind vier Zahlen geworden: `specialRole` ist der String `inbox`, `previewText` ist immer gesetzt und bei etwa 250 Zeichen von der App selbst gekappt, die Byte-Kappe des Volltexts steht auf 32 KiB, und zwölf Filterläufe zeigen, wo die Grammatik stillschweigend verwirft.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-08-24T12:31Z
- **Completed:** 2026-08-24T13:13Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- `compose.exapp.yml` trägt GreenMail 2.1.12 als fünften Dienst, ohne einen einzigen veröffentlichten Port dazuzugewinnen (die aufgelöste Konfiguration hat eine leere `ports`-Liste).
- `scripts/bootstrap_exapp.sh` legt das Mail-Konto von alice auf `greenmail:3143` an, verwirft ein Konto auf einem anderen Endpunkt, liefert sechs Testmails über SMTP 3025 ein und ruft `occ mail:account:sync <id> -f`. Zwei aufeinanderfolgende Läufe enden beide mit Exit-Code 0 und verdoppeln nichts.
- Die vier deklarierten OCS-Leseformen antworten unter reiner AppAPI-Impersonation mit 200 und echten Daten, wo die Postfachliste vorher 500 antwortete.
- `docs/spike-mail.md` behauptet nicht mehr, das Rückgrat der Familie seien die `SCOPE_IGNORE`-Routen, und trägt das Stufe-2-Protokoll mit Datum.

## Die Zahlen, auf die die nächsten Pläne bauen

### A1: `specialRole`

`GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=4` antwortet 200 mit einem Postfach:
`databaseId=3`, `name="INBOX"`, `displayName="INBOX"`, `specialRole="inbox"` (**Typ `str`**,
nicht `int`), `specialUse=["inbox"]`, `unread=6`, `delimiter="."`. Die Wertemenge aus A1 ist
damit bestätigt. Die Zahl `0` als Alternative ist an dieser Instanz nicht aufgetreten, weil
GreenMail nur eine INBOX anlegt; ein Werkzeug muss trotzdem beide Typen vertragen.

### A2: `previewText`

Bei allen sechs Testmails **gesetzt und nie `null`**. Längen in Zeichen: 229 (Textmail), 251
(Newsletter 45 KB), 251 (Newsletter 400 KB), 41 (`Rechnung`), 38 (`Rechnung Mai`), 0 (Mail
ohne Textkörper, nur Anhang). Die App kappt selbst bei etwa **250 Zeichen**: beide Newsletter
tragen genau 251 Zeichen, obwohl ihr Text 25 KB beziehungsweise 229 KB lang ist. Der Wert
kommt ohne HTML an. Die leere Zeichenkette ist der Fall, den ein Werkzeug abfangen muss, und
sie heisst "die Mail hat keinen Textkörper", nicht "die Vorschau fehlt".

### A3: Volltext-Längen und die gewählte Byte-Kappe

| Nachricht | Status | `hasHtmlBody` | `body` | Text nach der Wandlung |
|-----------|--------|---------------|--------|------------------------|
| Textmail mit Umlauten | 200 | `false` | 243 B | 236 B |
| Newsletter, 45 KB HTML | 200 | `true` | 48811 B | 25582 B |
| Grosser Newsletter, 400 KB HTML | 200 | `true` | 431379 B | 228894 B |
| `Rechnung` | 200 | `false` | 41 B | 41 B |
| `Rechnung Mai` | 200 | `false` | 39 B | 39 B |
| Mail ohne Body, nur Anhang | 200 | `false` | 0 B | 0 B |

**Gewählte Byte-Kappe des Volltexts: 32 KiB, also 32768 Bytes.** Der Startwert der Recherche
war die Grössenordnung 16 KiB; der Newsletter in realistischer Grösse ergibt nach der Wandlung
25582 Bytes und wäre bei 16 KiB gekappt worden, obwohl er der Normalfall ist. 32 KiB lässt ihn
ungekappt durch und kappt den 400-KB-Fall auf gut ein Siebtel. Die heutige Datei-Grenze
`MAX_TEXT_BYTES` von 512 KiB wäre 229 KB Fliesstext im Modellkontext, also genau der Schaden,
gegen den die Kappe existiert. **Gesetzt wird die Zahl in Plan 10-05**, als eigene Konstante.

Nebenbefund: der gemessene Newsletter ist textdicht (52 Prozent des HTML sind Text). Ein
echter Werbe-Newsletter liegt deutlich darunter, 32 KiB ist also eine obere Abschätzung.

Die vier Vertrauens-Signale von MAIL-02 sind in allen sechs Antworten vorhanden
(`isSenderTrusted`, `hasDkimSignature`, `phishingDetails`, `smime`). **`dkimValid` fehlt in
allen sechs Antworten**, wie vorhergesagt: ohne gecachtes Prüfergebnis ist das Feld gar nicht
da, und "fehlt" heisst "nicht geprüft", nicht "ungültig".

Korrektur K2 ist belegt: der `body` der reinen Textmail trägt bei `hasHtmlBody: false` die
Entities `&amp;` und `&lt;`. Eine Wandlung, die an `hasHtmlBody` hängt, liefert diese
unverändert an das Modell. Umlaute kommen dagegen roh an, und die URL ist nicht zu einem
`a`-Element geworden.

### A4: zwölf Filterläufe (plus drei Zugaben)

| Filter | Treffer | Bedeutung |
|--------|---------|-----------|
| (kein Filter) | 6 | die Grundlinie |
| `is:unread` | 6 | wirkt |
| `is:read` | 0 | Gegenprobe |
| `not:unread` | 0 | Invertierung wirkt |
| `from:alice` | 0 | `from:` liest den Absender, nicht den Empfänger |
| `from:buchhaltung` | 2 | Teilstring genügt |
| `subject:Rechnung` | 2 | Teilstring |
| `subject:Rechnung%20Mai` | 1 | der einzige Weg zu einem Wert mit Leerzeichen |
| `subject:Rechnung Mai` | 2 | **stille Verwerfung** des zweiten Worts |
| `start:1787575636` | 6 | Unix-Sekunden wirken |
| `end:1000000000` | 0 | Unix-Sekunden wirken in beide Richtungen |
| `start:2026-08-01` | **0** | der ISO-Wert filtert alles weg |
| `tags:1` | 1 | **`tags:` erwartet die Tag-Id** |
| `tags:$label1` | 0 | das IMAP-Label als Wert trifft nichts |
| `is:ungelesen` | 6 | **stille Verwerfung**: der Tippfehler liefert die ungefilterte Liste |

Drei Folgerungen für Plan 10-04: der Tippfehler `is:ungelesen` liefert dieselbe Antwort wie
kein Filter (Beleg für die Positivliste), ein Wert mit Leerzeichen muss kodiert oder abgelehnt
werden, und ein ISO-Datum in `start:` liefert **null** Treffer statt "praktisch alles", weil
der Wert als Zeichenkette gegen die Integer-Spalte `sent_at` verglichen wird. Die Recherche
hatte unter K4 "praktisch alles" vermutet; die Folge bleibt dieselbe, nur schärfer.

### K3, die Ansicht und der `\Seen`-Nachweis

- `...messages?view=singleton` **ohne** `limit`: **genau eine** Nachricht. K3 an echten Daten belegt.
- `...messages?limit=10&view=singleton`: 6 Nachrichten.
- `...messages?limit=10` ohne `view`: 6 Einträge, jeder mit gesetztem `threadRootId` auf seine eigene `messageId`. An dieser Instanz ist jede Testmail ihr eigener Thread, die Thread-Ansicht ist also nur am Feld erkennbar, nicht an der Anzahl.
- `flags.seen` der Nachricht 14: **`false` vor** dem Abruf von `GET /ocs/v2.php/apps/mail/message/14` (Status 200) und **`false` danach**. Der `unread`-Zähler der INBOX bleibt bei 6. Lesen setzt kein `\Seen`.

## Task Commits

1. **Task 1: GreenMail als vierter Dienst und das Mail-Konto darauf** - `b0e337a` (feat)
2. **Task 2: Fünf Testmails einliefern und die vier Annahmen messen** - `b0e337a` (Einlieferung und Sync) plus `02dbe2a` (fix, siehe Deviations)
3. **Task 3: Stufe-2-Protokoll und Korrektur K1** - `6148803` (docs)

## Files Created/Modified

- `compose.exapp.yml` - Dienst `greenmail` (2.1.12), ohne `ports`-Block, Passwort aus derselben Variable wie der Bootstrap
- `scripts/bootstrap_exapp.sh` - `mail_account_row`, `ensure_mail_account` mit Host und Port, `deliver_test_mail`, `sync_mail_account`
- `docs/spike-mail.md` - Korrektur K1, das Stufe-2-Protokoll vom 2026-08-24, K5 beim Brute-Force-Punkt, erweiterte Reproduktion

## Decisions Made

- **Byte-Kappe 32 KiB statt 16 KiB.** Begründet durch die Messung, nicht durch Geschmack: 16 KiB hätte den Normalfall gekappt.
- **`tags:` nimmt die Tag-Id.** `MessageMapper` verbindet `mail_message_tags` und vergleicht `tags.tag_id`. Die Recherche nannte "IMAP-Labels, komma-getrennt"; das ist gemessen falsch. Plan 10-04 muss das in der Dokumentation der Grammatik sagen.
- **MAIL-01 bis MAIL-03 bleiben Pending.** Die Frontmatter dieses Plans nennt sie, aber dieser Plan baut kein Werkzeug: er legt die Messwerte, gegen die 10-04, 10-05 und 10-08 bauen. Ein Abhaken hier wäre eine unwahre Aussage in REQUIREMENTS.md. Dieselben Requirement-Ids stehen in sechs weiteren Plänen dieser Phase.
- **Die Idempotenz hängt am Postfach.** Eine Markierungsdatei im Nextcloud-Volume würde etwas über einen Zustand behaupten, der in GreenMail lebt, und GreenMail hält alles im Arbeitsspeicher: ein Neustart des Containers leert das Postfach, während die Markierung liegen bliebe.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] GreenMail 2.1.12 kann nicht mehrteilige Nachrichten nicht ausliefern**
- **Found during:** Task 2 (Messung)
- **Issue:** Die drei reinen Textmails antworteten auf der Volltextroute mit 500 und `"Could not connect to IMAP server."`, deterministisch über mehrere Versuche. Ursache laut `docker logs nc-mcp-exapp-greenmail`: `FetchCommand.handleBodyFetch` castet den Inhalt jeder Nachricht auf `MimeMultipart`, und der Inhalt einer `text/plain`-Mail ist ein String, also `ClassCastException`. Ein Fehler des Testservers, keine Eigenschaft der Mail-App.
- **Fix:** Reine Textmails werden in ein `multipart/mixed` mit genau einem `text/plain`-Teil gelegt. Kein HTML im Inhalt, der K2-Nachweis bleibt also gültig.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** Alle sechs Volltextabrufe antworten danach mit 200.
- **Committed in:** `02dbe2a`

**2. [Rule 2 - Missing critical] Die Textmail belegte K2 nicht**
- **Found during:** Task 2 (Messung)
- **Issue:** Der erste Entwurf der Textmail trug weder Link noch `&` noch `<`, also kam ihr `body` byte-identisch zurück und bewies nichts über die HTML-Wandlung. Die Mail existiert laut Plan aber genau für diesen Nachweis.
- **Fix:** Der Körper trägt jetzt eine URL, ein Ampersand und eine spitze Klammer.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** Der gemessene `body` trägt `&amp;` und `&lt;` bei `hasHtmlBody: false`.
- **Committed in:** `02dbe2a`

**3. [Rule 3 - Blocking] Die Einlieferung hätte die Staging-Topologie gebrochen**
- **Found during:** Task 2
- **Issue:** `scripts/bootstrap_exapp.sh` bedient mit `--staging` auch `compose.staging.yml`, und dort gibt es weder GreenMail noch das Netz `nc-mcp-exapp-net`. `deliver_test_mail` und `sync_mail_account` wären dort gescheitert.
- **Fix:** Beide Funktionen kehren im Staging-Modus mit einer Meldung zurück. Das Mail-Konto selbst wird dort weiter angelegt, es zeigt nur auf einen Host, den diese Topologie nicht hat, genau wie vor diesem Plan.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** `bash -n`, plus die Begründung als Kommentar an beiden Stellen.
- **Committed in:** `b0e337a`

### Bewusste Abweichungen von der Planvorgabe

**4. Sechs Testmails statt "fünf"**
- Der Plan spricht von "fünf Nachrichten", listet aber fünf **Zwecke**, von denen der vierte zwei Mails verlangt (`Rechnung` und `Rechnung Mai`). Eingeliefert werden sechs. Das Abnahmekriterium lautet "mindestens fünf".

**5. Kein `networks`-Schlüssel am Dienst `greenmail`**
- Die Vorlage in `docs/spike-mail.md` nennt `networks: [nc-mcp-exapp-net]`. In `compose.exapp.yml` ist das der **Name** des `default`-Netzes; eine zweite Nennung wäre ein undefiniertes Netz und `config --quiet` würde ablehnen. Der Dienst hängt über `default` im richtigen Netz.

**6. Kein Healthcheck am Dienst `greenmail`**
- Der Plan erlaubt einen, verlangt ihn nicht. Stattdessen wartet die Einlieferungsfunktion selbst auf den IMAP-Port, weil ein falsch gebauter Healthcheck `up -d --wait` scheitern liesse.

**7. Das Skript reist durch stdin statt über `python -c`**
- Der Plan nennt `python -c ...`. Ein mehrzeiliges Skript und ein Passwort in der argv des Docker-Clients widersprechen WR-06; das Skript kommt deshalb über stdin, das Passwort über `-e MAIL_PW` als Name.

---

**Total deviations:** 3 auto-fixed (2x Rule 3, 1x Rule 2), 4 bewusste Abweichungen von der Formulierung des Plans.
**Impact on plan:** Kein Scope-Zuwachs. Die drei Auto-Fixes waren nötig, damit die Messung überhaupt Messwerte statt Fehlerpfade liefert. Kein Produktionscode, keine Abhängigkeit und keine Manifest-Zeile angefasst.

## Issues Encountered

- **Stale Datenbankzeilen nach einem GreenMail-Neustart.** GreenMail vergibt nach einem Neustart wieder die UIDs 1 bis 6, die alten Zeilen der Mail-App zeigen danach auf die neuen Nachrichten, und `previewText` bleibt der Wert aus dem ersten Sync. Aufgelöst durch `occ mail:account:delete <id>` plus einen Bootstrap-Lauf, der das Konto neu anlegt und frisch synchronisiert. Für Plan 10-08 relevant: wer GreenMail neu startet, legt auch das Konto neu an.
- **Der Nextcloud-Log war für die Diagnose unbrauchbar** (die Mail-App loggt nur "Could not connect to IMAP server"). Die Ursache stand in `docker logs nc-mcp-exapp-greenmail`.

## User Setup Required

None - keine externe Konfiguration nötig. `HP_SHARED_KEY` muss wie bisher vor `docker compose up` exportiert sein.

## Next Phase Readiness

- **Plan 10-02** (Client) kann gegen echte Antwortformen bauen: die Feldnamenlisten aller vier Leseformen stehen im Protokoll.
- **Plan 10-04** setzt die Vorschau-Kappe gegen die gemessenen 250 Zeichen und die Filter-Positivliste gegen die zwölf Läufe, inklusive der Korrektur, dass `tags:` die Tag-Id nimmt.
- **Plan 10-05** setzt die Volltext-Kappe auf 32768 Bytes, mit der Messung als Kommentar.
- **Plan 10-08** erwartet im Live-Lauf: 1 Postfach mit `specialRole="inbox"` und `unread=6`, 6 Nachrichten, `flags.seen` vor und nach dem Volltextabruf `false`.
- **Offener Punkt für Phase 11:** ein Postfach **ohne** Special-Use ist an dieser Topologie nicht messbar, weil GreenMail nur eine INBOX anlegt. Die Zahl `0` als `specialRole` bleibt aus dem Quelltext gelesen.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*

## Self-Check: PASSED

Alle drei geänderten Dateien existieren, alle drei Task-Commits (`b0e337a`, `02dbe2a`,
`6148803`) stehen im Log, und das Dokument enthält keine Em-Dashes.
