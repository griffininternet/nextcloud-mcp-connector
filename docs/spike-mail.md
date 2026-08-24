# Mail Reachability Spike (MAIL-04)

**Status:** done, Ergebnis: erreicht (alle vier Wege antworten aus App-Code)
**Decision date:** 2026-08-21
**Nextcloud version:** 34.0.3 (build 34.0.3.2)
**AppAPI version:** 34.0.0
**Mail app version:** 5.11.1
**Deploy daemon:** HaRP, über die Topologie aus `compose.exapp.yml` (Caddy auf `127.0.0.1:8081`)
**Scope:** erreicht eine Anfrage, deren einziges Credential `APP_SECRET` ist und deren Nutzer
im Header `AUTHORIZATION-APP-API` steht, die Controller der Nextcloud-Mail-App, oder endet sie
auf einer Loginseite. Nicht gemessen wird, ob Mail fachlich funktioniert: dafür bräuchte es
einen erreichbaren IMAP-Server, und die offene Frage von MAIL-04 hängt nicht daran.

Die Versionen oben sind vor dem Schreiben aus der laufenden Instanz gelesen (`occ status` für
den Server, `occ app:list` für `app_api` und `mail`), nicht aus der Recherche übernommen.

## Entscheidungskriterium, vorab festgelegt

Das Kriterium stand vor der ersten Messung fest, damit die Zahlen es nicht nachträglich
verschieben können. Es steht wörtlich in `_verdict` in
`tests/integration/test_exapp_mail_reach.py`.

| Beobachtung | Bedeutung |
|-------------|-----------|
| JSON-Körper mit beliebigem Status (200, 403, 404, 500) | erreicht: nur App-Code erzeugt diese Körper, die CSRF- und Impersonations-Kette hat gehalten |
| HTML-Körper (Körper beginnt mit `<`) | nicht erreicht: das ist die Loginseite, die `ocs._json_payload` schon heute namentlich benennt |
| 3xx mit `Location`, die `/login` enthält | nicht erreicht: die Authentifizierung ist gescheitert |
| Antwortform `other` | nicht eindeutig, Stufe 2 nötig (siehe Eskalationsregel unten) |

Deshalb prüft kein Test auf Statuscode 200. Die drei Listen-Wege berühren IMAP, und ein
IMAP-Fehler ist trotzdem antwortender App-Code. Ein Spike, der hier auf 200 prüft, meldet
"Mail unerreichbar" und kippt den Schnitt der Phasen 10 und 11 fälschlich.

## Messung

Vier Wege, ein Versuch je Weg, gemessen am 2026-08-21 gegen die laufende HaRP-Topologie. Die
Werte stehen wörtlich so in der Ausgabe von
`uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q -s`.

| Weg | URL | erwarteter Status | gemessener Status | Content-Type | Form | Urteil |
|-----|-----|-------------------|-------------------|--------------|------|--------|
| accounts | `GET /index.php/apps/mail/api/accounts` | 200 | 200 | `application/json; charset=utf-8` | json | erreicht |
| mailboxes | `GET /index.php/apps/mail/api/mailboxes?accountId=1` | 500 mit JSON oder 200 mit leerer Liste | 500 | `application/json; charset=utf-8` | json | erreicht |
| messages | `GET /index.php/apps/mail/api/messages?mailboxId=0&limit=5` | 403 mit JSON | 403 | `application/json; charset=utf-8` | json | erreicht |
| ocs | `GET /ocs/v2.php/apps/mail/message/999999` | 404 im OCS-Envelope | 404 | `application/json; charset=utf-8` | json | erreicht |

Die ersten 120 Zeichen je Antwort, mehr wird nicht protokolliert (siehe "The two controls"):

```
accounts   head: '[{"id":1,"accountId":1,"name":"Alice Spike","order":1,"emailAddress":"alice@example.test","authMethod":"password","imapH'
mailboxes  head: '{"status":"error","message":"Server error","data":[],"code":0}'
messages   head: '[]'
ocs        head: '{"ocs":{"meta":{"status":"failure","statuscode":404,"message":""},"data":"Account not found."}}'
```

Drei Details, die die Prognose der Recherche bestätigen: `mailboxes` scheitert am IMAP-Sync,
den `MailManager::getMailboxes` unbedingt erzwingt (Korrektur K7), und `#[TrapError]` macht
daraus eine JSON-Antwort statt einer HTML-Fehlerseite. `messages` antwortet 403 mit `[]`, weil
das adressierte Postfach nicht existiert. Und die OCS-Route trägt kein `api`-Segment
(Korrektur K1): der Envelope in der letzten Zeile ist der Beweis, dass die Anfrage im
Controller und nicht in der Routing-Schicht gelandet ist.

Ein echter IMAP-Server war für diese Messung nicht nötig. Das Spike-Konto zeigt bewusst auf
`imap.invalid`, weil `occ mail:account:create-imap` die Verbindung nicht prüft
(`CreateImapAccount`) und die gemessene Frage keine erfolgreiche IMAP-Sitzung braucht.

## Decision

Mail ist unter reiner AppAPI-Impersonation erreichbar: alle vier Wege antworten mit JSON aus
App-Code, keiner mit einer HTML-Loginseite und keiner mit einem Redirect auf `/login`.

Für Phase 10 und 11 folgt daraus: MAIL-01 bis MAIL-03 bleiben wie geschnitten, CTX-02, SEC-01
und die Toolzahl in TOOL-15 bleiben unangetastet. Der Gegenfall wäre eingetreten, wenn eine
Messzeile die Form `html` oder einen Redirect auf `/login` getragen hätte; dann wären die drei
Listen-Routen weggefallen und Phase 10 hätte sich auf die OCS-Volltextroute plus den
Suchprovider `mail` reduziert. Diese Entscheidung ist damit getroffen und wird in der Planung
von Phase 10 nicht wieder aufgemacht.

## The two controls

Ohne die beiden Kontrollprüfungen beweist eine grüne Messtabelle nichts: eine antwortende
Route könnte von einem anderen Credential bedient worden sein, das im Prozess herumlag.

`test_the_measuring_process_holds_no_nextcloud_app_password` ist Kontrolle eins:
`NC_MCP_APP_PASSWORD` und `NC_MCP_STATIC_BEARER` werden aus dem Environment gelöscht und ihre
Abwesenheit behauptet, und das gebaute Credential trägt `mode="appapi"` mit
`secret=APP_SECRET`, nie ein Nutzerpasswort. Die Datei enthält kein Basic-Schema, auch nicht
als Zeichenkette.

`test_a_wrong_app_secret_is_refused` ist Kontrolle zwei: ein `APP_SECRET` aus 64 Nullen wird
mit einem Status ungleich 200 abgewiesen (gemessen: 401 auf `GET /ocs/v2.php/cloud/user`).
Damit ist belegt, dass ein echtes `APP_SECRET` jede andere Zeile dieser Tabelle getragen hat.

Headerwerte, die `APP_SECRET` tragen, werden nie gedruckt: der Wert von
`AUTHORIZATION-APP-API` ist base64 von `<user>:<APP_SECRET>` und genau so vertraulich wie das
Geheimnis selbst. Im Protokoll stehen deshalb nur Statuscodes, Content-Type, Antwortform, eine
`Location` und maximal 120 Zeichen Körper. Die Kappung auf 120 Zeichen ist eine
Sicherheitsanforderung und keine Kosmetik (T-08-01): die Kontoantwort trägt IMAP- und
SMTP-Hostnamen, Kontonamen und die Mailadresse eines echten Kontos.

## Replaceability

### Korrektur K1 (nachgetragen am 2026-08-24): die vier benutzten Wege sind deklariert

Der Rest dieses Abschnitts ist am 2026-08-21 unter einer Prämisse geschrieben worden, die
sich in der Recherche zu Phase 10 als zu eng erwiesen hat, und die Korrektur steht deshalb
vorne und nicht in einer Fussnote.

Die mit der App ausgelieferte `openapi.json` von Mail 5.11.1 (im App-Verzeichnis der
laufenden Instanz) deklariert **sieben** OCS-Routen, davon vier lesende, und diese vier decken
alle drei Leseebenen plus den Volltext ab. Sie sind die Wege, die Phase 10 benutzt:

```
GET /ocs/v2.php/apps/mail/account/list
GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=<int>
GET /ocs/v2.php/apps/mail/ocs/mailboxes/{mailboxId}/messages?limit=..&view=singleton[&filter=..][&cursor=..]
GET /ocs/v2.php/apps/mail/message/{id}
```

Die drei `SCOPE_IGNORE`-Routen aus der Stufe-1-Messung werden damit **nicht** benutzt, und ein
Rückfall auf sie wäre keine Notlösung, sondern eine Verschlechterung: `/api/messages` ist eine
Resource-Route, auf der POST anlegt, PUT ändert und DELETE löscht, alles auf demselben Pfad,
den ein Lesen benutzt. Ein pfadbasiertes Schreibverbot, wie es das Gate dieses Projekts
formuliert, ist dort nicht mehr aussprechbar. Auf den deklarierten Wegen dagegen ist der
Sendeweg ein eigener Pfad (`POST /ocs/v2.php/apps/mail/message/send`), gegen den sich ein
Verbot formulieren und gegenprüfen lässt.

Der Satz weiter unten, die OCS-Volltextroute sei "als einzige der vier eine deklarierte
Route", bleibt stehen und ist **für die vier in Stufe 1 gemessenen Wege richtig**: von diesen
vier war sie die einzige deklarierte. **Für die Familie ist er falsch**, weil Stufe 1 die drei
`ocs`-Listenrouten gar nicht angefasst hat. Er wird deshalb gekennzeichnet und nicht gelöscht:
das Protokoll eines Laufs bleibt, wie es aufgeschrieben wurde.

### Der Stand vom 2026-08-21

Die drei Listen-Routen `/api/accounts`, `/api/mailboxes` und `/api/messages` tragen auf
Klassenebene `#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`. Sie sind damit keine zugesagte API,
sondern das Innenleben des Mail-Frontends: eine Mail-Fassung darf sie ohne Ankündigung ändern
oder entfernen. Was Phase 10 darauf baut, muss ersetzbar bleiben.

Der Ausweg ist benannt und nicht erst zu erfinden: Discovery über den Unified-Search-Provider
`mail` plus die OCS-Volltextroute `GET /ocs/v2.php/apps/mail/message/{id}`, die als einzige der
vier eine deklarierte Route ist und in dieser Messung 404 im OCS-Envelope geliefert hat, also
antwortenden App-Code. (Genau dieser Halbsatz ist der oben gekennzeichnete: richtig für die
vier gemessenen Wege, falsch für die Familie.)

Dieser Hinweis gehört ein zweites Mal in das künftige
`src/mcp_connector/nextcloud/clients/mail.py`, und zwar in dessen Modul-Docstring. Phase 10
übernimmt das ausdrücklich: in Phase 8 existiert kein Produktionscode, der Mail-Routen
aufruft, deshalb steht der Hinweis heute im Modul-Docstring von
`tests/integration/test_exapp_mail_reach.py`. Der Hinweis ändert dabei seine Richtung: er sagt
nicht mehr "unser Rückgrat ist unsicher", sondern "die unsichere Variante ist bewusst nicht
genommen worden, und hier steht warum".

## Eskalationsregel und Stufe 2

Stufe 1 (die Messung oben, ohne erreichbaren IMAP-Server) ist genau dann nicht eindeutig, wenn
eine der vier Messzeilen die Form `other` trägt oder ein 3xx auf etwas anderes als `/login`
zeigt. Nur in diesem Fall kommt GreenMail als vierter Dienst in `compose.exapp.yml` dazu:

```yaml
  greenmail:
    image: greenmail/standalone:2.1.12
    container_name: nc-mcp-exapp-greenmail
    environment:
      GREENMAIL_OPTS: >-
        -Dgreenmail.setup.test.all
        -Dgreenmail.hostname=0.0.0.0
        -Dgreenmail.auth.disabled
        -Dgreenmail.users=alice:alice-spike-imap-pw@example.test
    networks: [nc-mcp-exapp-net]
```

Kein veröffentlichter Port, aus demselben Grund wie beim Dienst `registry`: Nextcloud erreicht
GreenMail über das Docker-Netz `nc-mcp-exapp-net`, und ein gebundener Port wäre zusätzliche
Reichweite ohne Gegenwert (T-08-05). Danach wird das Spike-Konto auf Host `greenmail`, Port
3143 und `imapSslMode none` umgestellt, ein Testmail über SMTP 3025 eingeliefert,
`occ mail:account:sync <id> -f` gerufen und die Messung wiederholt.

Alle vier Messzeilen sind eindeutig. Die Eskalationsregel hat Stufe 2 also **nicht**
ausgelöst.

### Stufe 2 ist trotzdem ausgeführt worden, am 2026-08-24

Der Auslöser war ein anderer als der oben beschriebene. Phase 10 baut Werkzeuge auf den
Feldformen dieser Antworten auf, und MAIL-03 verlangt wörtlich "dokumentiert wie getestet".
Vier Annahmen der Phasenrecherche (A1 bis A4 in
`.planning/phases/10-mail-strikt-lesend-und-die-trifecta-grenze/10-RESEARCH.md`) sind ohne
echte IMAP-Daten nicht entscheidbar: die Wertemenge von `specialRole`, das Füllverhalten von
`previewText`, die Länge einer gewandelten HTML-Mail und das Verhalten der Filtergrammatik.
Plan 10-01 hat Stufe 2 deshalb als ersten, blockierenden Schritt der Phase ausgeführt, damit
diese vier Zahlen vor dem Bau feststehen und nicht erst im Live-Lauf am Phasenende auffallen.

Der Dienst `greenmail` steht seitdem in `compose.exapp.yml`, das Konto von alice zeigt auf
`greenmail:3143`, und `scripts/bootstrap_exapp.sh` liefert sechs Testmails über SMTP 3025 ein
und ruft danach `occ mail:account:sync <id> -f`. Zwei Abweichungen von der Vorlage oben, beide
gemessen und nicht gewählt: das Passwort wird aus `NC_EXAPP_ALICE_IMAP_PASSWORD` interpoliert,
weil sonst zwei Dateien dieselbe Zeichenkette getrennt pflegen müssten, und der
`networks`-Schlüssel entfällt, weil `nc-mcp-exapp-net` in dieser Datei der Name des
`default`-Netzes ist und eine zweite Nennung als undefiniertes Netz abgelehnt würde.

**Warum hier Feldwerte stehen dürfen und in Stufe 1 nicht:** die Stufe-1-Kontoantwort trug die
Mailadresse, den Kontonamen und die IMAP- und SMTP-Hostnamen eines echten Kontos, deshalb die
Kappung auf 120 Zeichen (T-08-01). Alle Adressen unten liegen unter `example.test`, alle
Inhalte sind von `scripts/bootstrap_exapp.sh` erfunden, und die Postfächer leben in einem
Dienst, der alles im Arbeitsspeicher hält. Ein `APP_SECRET` und jeder Header, der es trägt,
erscheint auch hier nirgends.

Aufrufweg aller Zeilen unten: reine AppAPI-Impersonation gegen `http://127.0.0.1:8081`, also
`AUTHORIZATION-APP-API` mit base64 von `alice:<APP_SECRET>` plus `EX-APP-ID` und
`EX-APP-VERSION`, kein App-Passwort im Prozess. Nextcloud 34.0.3 (Build 34.0.3.2), Mail 5.11.1,
GreenMail 2.1.12.

#### A1: die Wertemenge von `specialRole`

`GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=4` antwortet 200 mit einem Postfach:

| Feld | gemessener Wert | Typ |
|------|-----------------|-----|
| `databaseId` | `3` | int |
| `name` | `INBOX` | str |
| `displayName` | `INBOX` | str |
| `specialRole` | `inbox` | **str**, nicht int |
| `specialUse` | `['inbox']` | Liste |
| `unread` | `6` | int |
| `delimiter` | `.` | str |

Vollständige Feldnamen der Antwort: `accountId, attributes, cacheBuster, databaseId,
delimiter, displayName, id, mailboxes, myAcls, name, shared, specialRole, specialUse,
syncInBackground, unread`.

`specialRole` ist also der Kleinschreibungs-Special-Use ohne Backslash, wie A1 vermutet hat.
Die Zahl 0 als Alternative ist an dieser Instanz nicht aufgetreten, weil GreenMail nur eine
INBOX anlegt; ein Postfach ohne Special-Use ist hier nicht gemessen und bleibt die aus
`getSpecialUseParsed()[0] ?? 0` gelesene Möglichkeit. Ein Werkzeug muss deshalb beide Typen
vertragen. Der Vorher-Zustand dieser Zeile war die Antwort 500 mit `meta.statuscode` 996
(Korrektur K6), solange das Konto auf einen Host zeigte, der nicht antwortet.

#### A2: `previewText`

`GET /ocs/v2.php/apps/mail/ocs/mailboxes/3/messages?limit=10&view=singleton` antwortet 200 mit
sechs Nachrichten. `previewText` ist bei **allen sechs gesetzt und nie `null`**, aber bei der
Mail ohne Textkörper ist es die leere Zeichenkette:

| Nachricht | `previewText` gesetzt | Länge in Zeichen | Länge in Bytes |
|-----------|-----------------------|------------------|----------------|
| Textmail mit Umlauten | ja | 229 | 236 |
| Newsletter, 45 KB HTML | ja | 251 | 255 |
| Grosser Newsletter, 400 KB HTML | ja | 251 | 255 |
| `Rechnung` | ja | 41 | 41 |
| `Rechnung Mai` | ja | 38 | 39 |
| Mail ohne Body, nur Anhang | ja, leer | 0 | 0 |

Die App kappt selbst bei ungefähr 250 Zeichen: die beiden Newsletter, deren Text 25 KB
beziehungsweise 229 KB lang ist, tragen beide genau 251 Zeichen Vorschau. Der Wert kommt ohne
HTML an, Absätze sind zu Leerzeichen geworden, Fettdruck ist zu Grossschreibung geworden.
`null` ist damit an echten Daten nicht aufgetreten; die leere Zeichenkette ist der Fall, den
ein Werkzeug abfangen muss, und "kein Text" heisst hier "die Mail hat keinen Textkörper" und
nicht "die Vorschau fehlt".

#### A3: die Länge des Volltexts und die gewählte Byte-Kappe

`GET /ocs/v2.php/apps/mail/message/{databaseId}`, alle sechs mit Status **200**. `body` ist der
Wert, den die Route liefert; `Text` ist derselbe Körper nach der Wandlung, die Plan 10-05 baut
(`lxml`, `script` und `style` entfernt, `text_content()`):

| Nachricht | Status | `hasHtmlBody` | `body` | Text nach der Wandlung |
|-----------|--------|---------------|--------|------------------------|
| Textmail mit Umlauten | 200 | `false` | 243 B | 236 B |
| Newsletter, 45 KB HTML | 200 | `true` | 48811 B | 25582 B |
| Grosser Newsletter, 400 KB HTML | 200 | `true` | 431379 B | 228894 B |
| `Rechnung` | 200 | `false` | 41 B | 41 B |
| `Rechnung Mai` | 200 | `false` | 39 B | 39 B |
| Mail ohne Body, nur Anhang | 200 | `false` | 0 B | 0 B |

Die vier Vertrauens-Signale, die MAIL-02 verlangt, sind in jeder der sechs Antworten vorhanden:
`isSenderTrusted` (`false`), `hasDkimSignature` (`false`), `phishingDetails` (Objekt mit
`warning: false` und drei bis vier `checks`) und `smime` (`isSigned`, `signatureIsValid: null`,
`isEncrypted`). `dkimValid` **fehlt in allen sechs Antworten**, wie die Recherche vorhergesagt
hat: der Wert kommt aus `dkimService->getCached`, und ohne gecachtes Prüfergebnis ist das Feld
gar nicht da. Ein Werkzeug muss "fehlt" als "nicht geprüft" lesen und nicht als "ungültig".

Korrektur K2 ist an der Textmail belegt. Ihr `body` bei `hasHtmlBody: false`:

```
Moin,\n\nGrüße aus Hamburg. Die Maße des Regals sind 80 x 200 cm.\nDer Preis liegt bei 30
Euro &amp; Versand, die Straße kennst du ja.\nDetails: https://example.test/regal?groesse=
80x200\nEin spitzes Zeichen: 5 &lt; 7.\n\nViele Grüße\nDas Büro\n
```

`&amp;` und `&lt;` stehen dort, obwohl die Mail kein HTML enthält und `hasHtmlBody` falsch ist.
Eine Wandlung, die an `hasHtmlBody` hängt, liefert diese Entities also unverändert an das
Modell. Die Umlaute kommen dagegen roh an, und die URL ist nicht zu einem `a`-Element geworden.

**Die Byte-Kappe des Volltexts: 32 KiB, also 32768 Bytes.** Die Begründung ist die Zeile
darüber und nicht ein Gefühl. Der Startwert der Recherche war die Grössenordnung 16 KiB; der
gemessene Newsletter in realistischer Grösse ergibt nach der Wandlung 25582 Bytes und wäre bei
16 KiB gekappt worden, obwohl er der Normalfall ist, den die Familie tragen soll. 32 KiB lässt
ihn ungekappt durch und kappt den 400-KB-Fall auf gut ein Siebtel. Nach oben ist die Grenze
ebenso begründet: 512 KiB, die heutige Datei-Grenze `MAX_TEXT_BYTES`, wären 229 KB Fliesstext
in einem Modellkontext, also genau der Totalschaden, gegen den die Kappe existiert. Die Zahl
wird hier nur entschieden; gesetzt wird sie in Plan 10-05, als eigene Konstante und mit einer
Markierung, die nur bei echter Kappung erscheint.

Ein Nebenbefund zur Grössenordnung: der gemessene Newsletter ist textdicht (52 Prozent des
HTML sind Text). Ein echter Werbe-Newsletter mit Tabellenlayout und Inline-Styles liegt
deutlich darunter, seine gewandelte Länge also auch. 32 KiB ist damit eine obere Abschätzung
und keine knappe.

#### A4: die Filtergrammatik, zwölf Läufe an echten Nachrichten

Alle Läufe gegen `GET /ocs/v2.php/apps/mail/ocs/mailboxes/3/messages?limit=50&view=singleton`,
der Filterwert URL-kodiert im Parameter `filter`. Sechs Nachrichten liegen im Postfach, alle
ungelesen, zwei tragen `Rechnung` im Betreff, eine trägt den IMAP-Keyword `$label1`.

| Filter | Treffer | Bedeutung |
|--------|---------|-----------|
| (kein Filter) | 6 | die Grundlinie |
| `is:unread` | 6 | wirkt, alle sechs sind ungelesen |
| `is:read` | 0 | die Gegenprobe zu `is:unread` |
| `not:unread` | 0 | die Invertierung wirkt |
| `from:alice` | 0 | `from:` liest den Absender, nicht den Empfänger |
| `from:buchhaltung` | 2 | Teilstring des Absenders genügt |
| `subject:Rechnung` | 2 | Teilstring, `Rechnung` und `Rechnung Mai` |
| `subject:Rechnung%20Mai` | 1 | **der einzige Weg zu einem Wert mit Leerzeichen** |
| `subject:Rechnung Mai` | 2 | **stille Verwerfung**: `Mai` hat keinen Doppelpunkt und fällt weg |
| `start:1787575636` | 6 | Unix-Sekunden wirken |
| `end:1000000000` | 0 | Unix-Sekunden wirken auch in die andere Richtung |
| `start:2026-08-01` | **0** | der ISO-Wert filtert alles weg |
| `tags:1` | 1 | **`tags:` erwartet die Tag-Id, nicht das Label** |
| `tags:$label1` | 0 | das IMAP-Label als Wert trifft nichts |
| `is:ungelesen` | 6 | **stille Verwerfung**: der Tippfehler liefert die ungefilterte Liste |

Drei dieser Zeilen sind für die Werkzeug-Ebene entscheidend:

1. `is:ungelesen` liefert **dieselben sechs Treffer wie kein Filter**. Ein Tippfehler erzeugt
   also eine Antwort, die richtig aussieht und falsch ist, und das Modell kann diesen Fehler
   nicht erkennen. Das ist der Beleg für die Positivliste, die MAIL-03 verlangt.
2. `subject:Rechnung Mai` liefert zwei Treffer statt einem: das zweite Wort wird stillschweigend
   verworfen. Ein Werkzeug muss den Wert kodieren oder die Eingabe ablehnen.
3. `start:2026-08-01` liefert **null** Treffer, nicht "praktisch alles", wie die Recherche unter
   K4 vermutet hatte. Der Wert wird als Zeichenkette gegen die Integer-Spalte `sent_at`
   verglichen, und `'1787575636' >= '2026-08-01'` ist im Zeichenkettenvergleich falsch. Die
   Folge ist dieselbe, nur schärfer: ein ISO-Datum gehört abgelehnt, nicht durchgereicht.

Und ein Befund, der in der Recherche noch anders stand: `tags:` nimmt die **numerische Id** des
Tags, nicht sein IMAP-Label. `MessageMapper` verbindet `mail_message_tags` und vergleicht
`tags.tag_id` mit den Werten des Filters. Die Nachricht mit dem Keyword `$label1` trägt in der
Antwort das Tag-Objekt `{"id": 1, "displayName": "Important", "imapLabel": "$label1",
"isDefaultTag": true}`, und nur `tags:1` findet sie.

#### K3 und die Ansicht

| Aufruf | Ergebnis |
|--------|----------|
| `...messages?view=singleton` (ohne `limit`) | **1 Nachricht**, K3 an echten Daten belegt |
| `...messages?limit=10&view=singleton` | 6 Nachrichten |
| `...messages?limit=10` (ohne `view`) | 6 Einträge, jeder mit gesetztem `threadRootId` |

Der Lauf ohne `view` ist an dieser Instanz zahlenmässig nicht vom Lauf mit `view=singleton` zu
unterscheiden, weil jede der sechs Testmails ihr eigener Thread ist. Erkennbar ist die
Thread-Ansicht trotzdem: jeder Eintrag trägt ein `threadRootId`, das auf seine eigene
`messageId` zeigt. Eine Antwortkette würde hier Einträge zusammenfassen, und genau deshalb
sendet der Client immer `view=singleton`.

#### Der `\Seen`-Nachweis in seiner Rohform

| Schritt | `flags.seen` der Nachricht 14 | `unread` der INBOX |
|---------|-------------------------------|--------------------|
| vor dem Volltextabruf | `false` | 6 |
| `GET /ocs/v2.php/apps/mail/message/14` | Status 200 | - |
| nach dem Volltextabruf | `false` | 6 |

Lesen setzt kein `\Seen`, wie der Quelltext (`'peek' => true` in jedem Fetch der App)
vorhergesagt hat. Das ist eine Eigenschaft dieser Fassung und nicht des Protokolls; der
ausgebaute Nachweis mit zwei Zuständen gehört zu Plan 10-08, hier steht die Zahl, die dort
erwartet wird.

#### Ein Befund über GreenMail, nicht über Nextcloud

GreenMail 2.1.12 castet in `FetchCommand.handleBodyFetch` den Inhalt jeder Nachricht auf
`MimeMultipart`. Eine nicht mehrteilige Nachricht, also eine reine `text/plain`-Mail, endet
dort mit einer `ClassCastException`, der IMAP-FETCH scheitert, und Nextcloud antwortet die
Volltextroute mit 500 und `"Could not connect to IMAP server."`. Das ist ein Fehler des
Testservers und keine Eigenschaft der Mail-App: die drei betroffenen Nachrichten antworten mit
200, sobald sie in einem `multipart/mixed` mit genau einem `text/plain`-Teil liegen.
`scripts/bootstrap_exapp.sh` baut sie deshalb so. Wer diese Messung wiederholt und einen 500er
sieht, prüft zuerst `docker logs nc-mcp-exapp-greenmail`.

## Reproduktion

```
export HP_SHARED_KEY="$(openssl rand -hex 32)"   # oder der Wert aus .env.exapp
docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh
set -a && . ./.env.exapp && set +a
uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q
```

Mit `-s` statt `-q` gibt der letzte Befehl die vier Messzeilen aus, aus denen die Tabelle oben
besteht. Ohne die Topologie wird die Datei übersprungen und nicht ausgeführt: `exapp_env`
skippt mit dem Namen der fehlenden Umgebungsvariable.

Seit Plan 10-01 gehören zwei Schritte dazu, und beide macht `up -d --wait` zusammen mit dem
Bootstrap von selbst:

1. Der Dienst `greenmail` läuft in der Topologie mit, ohne veröffentlichten Port, erreichbar
   nur im Netz `nc-mcp-exapp-net`.
2. Das Mail-Konto von alice zeigt auf `greenmail:3143` (SMTP `greenmail:3025`, beides
   `imapSslMode none`), trägt sechs eingelieferte Testmails und ist mit
   `occ mail:account:sync <id> -f` synchronisiert.

Beides ist prüfbar, ohne irgendetwas zu lesen, was ein Geheimnis trägt:

```
docker compose -p nc-mcp-exapp -f compose.exapp.yml exec -T --user www-data nextcloud \
  php occ mail:account:export alice
```

Die Ausgabe nennt `IMAP host: greenmail:3143` und `SMTP host: greenmail:3025`. Steht dort ein
anderer Host, hat der Bootstrap das Konto nicht ersetzt und meldet das laut; ein stilles
"exists" auf dem alten Host ist seit Plan 10-01 ausgeschlossen, weil die Existenzprüfung die
Adresse **und** den Endpunkt vergleicht.

Ein zweiter Bootstrap-Lauf ist idempotent: er meldet `mail account alice: exists on
greenmail:3143`, `test mails alice: already there (6 in INBOX)` und synchronisiert erneut, ohne
etwas zu verdoppeln. Die Postfächer leben im Arbeitsspeicher von GreenMail, ein Neustart dieses
Containers leert sie, und der nächste Bootstrap-Lauf liefert sie wieder ein. Genau deshalb
hängt die Idempotenz an der Nachrichtenzahl im Postfach und nicht an einer Markierungsdatei.

## Was diese Messung nicht beweist

- Sie lief gegen Nextcloud 34.0.3 mit SQLite in einer Wegwerf-Instanz und gegen Mail 5.11.1.
  Eine andere Mail-Fassung darf die drei `SCOPE_IGNORE`-Routen brechen, siehe
  "Replaceability".
- Sie sagt nichts über die Feldformen der Antworten. `mailboxes` und `messages` haben in
  dieser Messung keine echten Daten geliefert; wer Felder braucht, braucht Stufe 2. Stufe 2 ist
  am 2026-08-24 ausgeführt worden, siehe den Abschnitt darüber: die Feldformen von
  `specialRole`, `previewText`, dem Volltext und der Filtergrammatik stehen dort als Messwerte.
- Sie sagt nichts über das Senden. `POST /ocs/v2.php/apps/mail/message/send` steht nicht in
  `routes.php`, sondern als `#[ApiRoute]` am Controller (Korrektur K2), wurde hier nicht
  angefasst, und ein Sendeweg ist ohnehin eine eigene Entscheidung und kein Nebenprodukt
  einer Lesemessung.
- Sie sagt nichts über eine Instanz mit aktivem Brute-Force-Schutz. Auf dieser Topologie ist
  er per Bootstrap abgeschaltet; die Regel, die OCS-Volltextroute nur einmal und nie in einer
  Schleife zu rufen, steht deshalb im Test und nicht in der Topologie, weil sie in Phase 10
  in Produktionscode wandert.

  Nachtrag vom 2026-08-24 (Korrektur K5): `MessageApiController::get` trägt zwar
  `#[BruteForceProtection('mailGetMessage')]`, aber im ganzen `lib/`-Baum von Mail 5.11.1 gibt
  es **keinen einzigen `throttle()`-Aufruf** (gemessen: `grep` über
  `/var/www/html/custom_apps/mail/lib`, null Treffer). Ohne diesen Aufruf registriert die
  Middleware keinen Versuch, der Zähler bleibt leer und die Verzögerung ist null. Der Satz
  oben bleibt trotzdem richtig, aber aus einem anderen Grund: jeder Volltextabruf öffnet eine
  eigene IMAP-Sitzung, ist also teuer und nicht gefährlich. Ein Memo-Muster, das einen Zähler
  schont, der nicht zählt, muss deshalb nicht in Produktionscode wandern.
