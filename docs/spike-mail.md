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

Die drei Listen-Routen `/api/accounts`, `/api/mailboxes` und `/api/messages` tragen auf
Klassenebene `#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`. Sie sind damit keine zugesagte API,
sondern das Innenleben des Mail-Frontends: eine Mail-Fassung darf sie ohne Ankündigung ändern
oder entfernen. Was Phase 10 darauf baut, muss ersetzbar bleiben.

Der Ausweg ist benannt und nicht erst zu erfinden: Discovery über den Unified-Search-Provider
`mail` plus die OCS-Volltextroute `GET /ocs/v2.php/apps/mail/message/{id}`, die als einzige der
vier eine deklarierte Route ist und in dieser Messung 404 im OCS-Envelope geliefert hat, also
antwortenden App-Code.

Dieser Hinweis gehört ein zweites Mal in das künftige
`src/mcp_connector/nextcloud/clients/mail.py`, und zwar in dessen Modul-Docstring. Phase 10
übernimmt das ausdrücklich: in Phase 8 existiert kein Produktionscode, der Mail-Routen
aufruft, deshalb steht der Hinweis heute im Modul-Docstring von
`tests/integration/test_exapp_mail_reach.py`.

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

Alle vier Messzeilen sind eindeutig, deshalb bleibt `compose.exapp.yml` unverändert und der
GreenMail-Block oben ist eine Vorlage und kein eingebauter Dienst. Stufe 2 ist damit ein
benannter, ausgeklammerter Folgeschritt für Phase 10: sie liefert nicht die Erreichbarkeit,
die hier schon belegt ist, sondern die Envelope- und Volltextformen, die Phase 10 sonst
annehmen müsste.

## Reproduktion

```
docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh
set -a && . ./.env.exapp && set +a
uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q
```

Mit `-s` statt `-q` gibt der letzte Befehl die vier Messzeilen aus, aus denen die Tabelle oben
besteht. Ohne die Topologie wird die Datei übersprungen und nicht ausgeführt: `exapp_env`
skippt mit dem Namen der fehlenden Umgebungsvariable.

## Was diese Messung nicht beweist

- Sie lief gegen Nextcloud 34.0.3 mit SQLite in einer Wegwerf-Instanz und gegen Mail 5.11.1.
  Eine andere Mail-Fassung darf die drei `SCOPE_IGNORE`-Routen brechen, siehe
  "Replaceability".
- Sie sagt nichts über die Feldformen der Antworten. `mailboxes` und `messages` haben in
  dieser Messung keine echten Daten geliefert; wer Felder braucht, braucht Stufe 2.
- Sie sagt nichts über das Senden. `POST /ocs/v2.php/apps/mail/message/send` steht nicht in
  `routes.php`, sondern als `#[ApiRoute]` am Controller (Korrektur K2), wurde hier nicht
  angefasst, und ein Sendeweg ist ohnehin eine eigene Entscheidung und kein Nebenprodukt
  einer Lesemessung.
- Sie sagt nichts über eine Instanz mit aktivem Brute-Force-Schutz. Auf dieser Topologie ist
  er per Bootstrap abgeschaltet; die Regel, die OCS-Volltextroute nur einmal und nie in einer
  Schleife zu rufen, steht deshalb im Test und nicht in der Topologie, weil sie in Phase 10
  in Produktionscode wandert.
