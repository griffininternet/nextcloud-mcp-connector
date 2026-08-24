# Messungen zu CTX-01 und CTX-02 (Plan 11-06)

**Datum:** 2026-08-24, drei Läufe zwischen 21:12Z und 21:25Z.

Dieses Dokument ist der Beleg für jede Zahl, die in `src/mcp_connector/tools/context.py` in
einem Konstantenkommentar steht. Es löst zugleich den Verweis ab, der dort auf
`04-04-MEASUREMENTS.md` zeigte: diese Datei existiert im Repository nicht mehr.

## Topologie

| Container | Rolle |
|---|---|
| `nc-mcp-exapp-nc` | Nextcloud 34.0.3 |
| `nc_app_mcp_connector` | die ExApp, dieses Projekt |
| `nc-mcp-exapp-harp` | HaRP, der Deploy-Daemon und Reverse Proxy |
| `nc-mcp-exapp-caddy` | der Proxy vor der Nextcloud |
| `nc-mcp-exapp-registry` | die lokale Image-Registry |
| `nc-mcp-exapp-greenmail` | IMAP und SMTP für die sechs Testmails aus Plan 10-01 |

Apps: `mail` 5.11.1, `spreed` 24.0.4, `tables` 2.2.2, alle aktiviert (gelesen mit
`docker exec -u www-data nc-mcp-exapp-nc php occ app:list --output=json`).

Instanzdaten, aus denen die Zahlen unten kommen: ein Mailkonto (`alice@example.test`, id 4) mit
einem Postfach (`INBOX`, `special_role="inbox"`, `unread` 6), fünf Talk-Konversationen, zwei
Tabellen.

## Reproduce

```bash
docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
bash scripts/bootstrap_exapp.sh
set -a && . ./.env.exapp && set +a
uv run pytest tests/integration/test_ctx_bundle.py -m integration -q -rA -s
```

Der Lauf druckt neunzehn Messzeilen. Sie sind das Lieferergebnis, und alles in diesem Dokument
ist aus ihnen abgeschrieben. Unter Windows braucht die Anzeige `PYTHONIOENCODING=utf-8`, sonst
scheitert das Drucken einer Konversation mit einem Zeichen ausserhalb von cp1252 an der Konsole
und nicht an der Messung.

## Nachweistabelle

| Datum | Behauptung | Befehl |
|---|---|---|
| 2026-08-24 21:25Z | Die Wanduhr von `prepare_context` mit vier Beinen liegt bei `detail="short"` im Median bei 0,65 s bis 1,13 s und bei `detail="full"` mit drei Auszügen bei 0,85 s bis 1,83 s, gemessen über drei Läufe mit je drei Aufrufen, und bleibt damit unter der grössten Einzeldecke `CALENDAR_BUDGET` von 10 s. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k wall_clock` |
| 2026-08-24 21:25Z | Kein einziger `degraded`-Eintrag eines Laufs sagt, dass ein Bein seine Zeitdecke verpasst hat: die Bedingung ist die Abwesenheit der Wendung "did not answer within". | derselbe Lauf, Behauptung `budget_misses` in `test_the_wall_clock_of_four_legs_stays_under_one_budget` |
| 2026-08-24 21:25Z | Die vier Beine einzeln, im Median über drei Aufrufe: Suche 0,65 s bis 0,73 s, Kalender 0,07 s bis 0,08 s, Talk 0,04 s, Mail 0,06 s. Jedes der drei gedeckelten Beine liegt mehr als hundertfach unter seiner Decke. | derselbe Lauf, Zeilen `leg search`, `leg calendar`, `leg talk`, `leg mail` |
| 2026-08-24 21:25Z | Ein Bündelaufruf kostet 22 Requests bei kaltem und 19 bei warmem Capabilities-Cache, in beiden Fällen genau eine Kontenliste und genau eine Postfachliste für das eine Konto dieser Instanz, und keinen weiteren Mail-Request. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k request_cost` |
| 2026-08-24 21:25Z | Die Erkennungsrequests kosten kalt drei und warm null: zweimal `/cloud/capabilities` und einmal `/core/navigation/apps`, und nach `capabilities.TTL_SECONDS` (60 s) Gültigkeit zahlt ein zweites Bündel keinen davon. | derselbe Lauf, Zeile `mail cost sentence measured` |
| 2026-08-24 21:25Z | `unread` ist der Zähler der App und kein Nachrichtenzähler: die Konversation `o4vwrd7g` trägt sechs lesbare Nachrichten in einem Fenster und meldet `unread` 0, und sie steht deshalb korrekt nicht im Digest. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k digest` |
| 2026-08-24 21:25Z | Der Digest hält seine Kappe (`MAX_DIGEST` 3) und enthält ausschliesslich Konversationen, bei denen etwas wartet: zwei von fünf. | derselbe Lauf, Zeilen `conversation ...` |
| 2026-08-24 21:25Z | `inbox_unread` des Bündels ist 6 und `mail_browse(level="mailboxes")` meldet für dasselbe Konto ebenfalls 6; die Gegenprobe läuft über das Werkzeug und nicht über eine zweite Rechnung im Test. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k mail_counter` |
| 2026-08-24 21:25Z | Keiner der sechs GreenMail-Betreffs kommt im serialisierten Bündel vor (1950 Zeichen), und die Suche dieses Bündels erreicht den Mail-Provider nicht, also ist das eine Aussage über das Zählerbein. | derselbe Lauf, Zeile `none of the 6 GreenMail subjects` |
| 2026-08-24 21:25Z | `fetch("message:6c3pifti:17")` lässt `unread` bei 7, `unread_mention` bei `false` und `unread_mention_direct` bei `false`, gemessen vor und nach dem Aufruf über `talk_browse(level="conversations")` und nie über die Kontextroute. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k moves_no_counter` |
| 2026-08-24 21:25Z | Je neues Id-Kind ein `fetch` aus einem echten Suchtreffer: `message:6c3pifti:17` (Suchwort "moderation", 292 Byte Text) und `table:2` (Suchwort "Test", 1161 Byte Text), beide mit `metadata.kind` und einer `url` aus der konfigurierten Basis-Adresse. | `uv run pytest tests/integration/test_ctx_bundle.py -m integration -s -k new_id_kind` |
| 2026-08-24 21:25Z | Der Endzustand der Instanz ist gemessen und nicht angenommen: `unread` je Konversation lautet nach dem Lauf `o4vwrd7g` 0, `gtaigumi` 0, `q5s5xqp5` 3, `b3yaiqpa` 0, `6c3pifti` 7, also unverändert. | derselbe Lauf, Zeile `end state, unread per conversation` |
| 2026-08-24 21:25Z | `uv run pytest -q` (Standardauswahl) bleibt grün und startet keinen Container: die Datei trägt `pytest.mark.integration` und wird nicht eingesammelt. | `uv run pytest -q` und `uv run pytest tests/integration/test_ctx_bundle.py --collect-only -q -m integration` (9 Tests) |

## Wanduhr

Referenz aus Plan 04-04 (live proof 5, zwei Beine, eine MCP-Sitzung über Client, Proxy, HaRP,
Container und Nextcloud): `detail="short"` 0,84 s, `detail="full"` mit drei Auszügen 0,99 s,
`degraded` leer.

Heute, vier Beine, drei Läufe mit je drei Aufrufen je Detailstufe, Suchwort "Abnahme", das
dieselben drei Auszüge erzeugt wie die Referenz:

| Lauf | short min / median / max | full min / median / max |
|---|---|---|
| A, 21:12Z | 1,01 s / 1,13 s / 2,04 s | 1,40 s / 1,83 s / 2,07 s |
| B, 21:18Z | 0,77 s / 0,81 s / 1,85 s | 0,84 s / 0,85 s / 0,92 s |
| C, 21:25Z | 0,65 s / 0,65 s / 1,75 s | 0,84 s / 0,85 s / 1,27 s |

`degraded` war in allen drei Läufen leer, in allen sechs Zeilen.

**Was die Streuung ist und was sie nicht ist.** Der Maximalwert jeder Zeile ist immer der erste
der drei Aufrufe, weil der Cache dort leer ist: der erste Aufruf zahlt die Erkennungsrequests
und den Verbindungsaufbau. Lauf A liegt insgesamt höher als B und C, und das ist Last auf dem
Entwicklungsrechner und keine Eigenschaft des Codes. Die Zahl, die nicht streut, ist die je
Bein:

| Bein | Median | Decke | Abstand |
|---|---|---|---|
| Suche | 0,65 s bis 0,73 s | keine eigene (`PER_PROVIDER_TIMEOUT` 15 s je Provider) | - |
| Kalender | 0,07 s bis 0,08 s | `CALENDAR_BUDGET` 10 s | Faktor 114 bis 133 |
| Talk | 0,04 s | `TALK_BUDGET` 5 s | Faktor 129 bis 138 |
| Mail | 0,06 s | `MAIL_BUDGET` 10 s | Faktor 151 bis 152 |

**Antwort auf die Frage, die Erfolgskriterium 2 stellt.** Die Wanduhr des Bündels hängt an der
Suche und nicht an den zwei neuen Beinen: das Suchbein allein braucht 0,65 s bis 0,73 s, das
Talk-Bein 0,04 s und das Mail-Bein 0,06 s. Die beiden neuen Beine addieren zur Wanduhr nichts,
weil sie im selben `gather` laufen und weit unter dem längsten Bein bleiben, und der Median in
den Läufen B und C liegt für beide Detailstufen auf oder unter der Referenz von 2026-08-17. Lauf
A liegt darüber, und deshalb steht er hier und wird nicht weggelassen; sein Median für
`detail="full"` ist 1,83 s gegen 0,99 s.

**Folgt daraus eine Budgetänderung? Nein.** Keine der vier Konstanten wird geändert. Die
Begründung ist der Abstand in der Tabelle oben: jedes gedeckelte Bein liegt mehr als hundertfach
unter seiner Decke, und selbst der schlechteste einzelne Bündelaufruf dieser drei Läufe (2,07 s)
bleibt um mehr als den Faktor zwei unter der kleinsten Decke (`TALK_BUDGET`, 5 s) und um den
Faktor 14 unter den etwa 30 s, die ein Client gewährt. Eine Decke, die im gesunden Fall nie
zubeisst, tut genau das, wofür sie da ist. Eine Absenkung wäre die Gegenrichtung und würde bei
der ersten langsamen Instanz Degradation im Normalfall erzeugen.

## Requestkosten

Gezählt mit einem `httpx`-Request-Hook im Testlauf, aufgeschlüsselt nach Pfadpräfix. Suchwort
"Abnahme", eine Instanz mit einem Mailkonto und dreizehn Suchprovidern.

| Präfix | kalt | warm |
|---|---|---|
| `/cloud/capabilities` | 2 | 0 |
| `/core/navigation/apps` | 1 | 0 |
| `/search/providers` (die Providerliste) | 1 | 1 |
| `/search/providers/<id>/search` | 13 | 13 |
| `/apps/mail/account/list` | 1 | 1 |
| `/apps/mail/ocs/mailboxes` | 1 | 1 |
| `/apps/spreed/...` (die Konversationsliste) | 1 | 1 |
| `/remote.php/dav` (Kalender) | 2 | 2 |
| **Summe** | **22** | **19** |

**Die Kostenformel, wörtlich, wie CTX-02 sie verlangt.** Das Mail-Bein kostet
`1 + N` Requests: eine Kontenliste plus eine Postfachliste je Konto, mit `N` höchstens
`MAX_MAIL_ACCOUNTS` (3). Auf dieser Instanz ist `N` gleich 1, also 2 Requests. Dazu kommen bei
kaltem Cache die Erkennungsrequests, und die gemessene Zahl ist **drei** und nicht zwei: zweimal
`/cloud/capabilities` und einmal `/core/navigation/apps`. Zwei davon gehören dem Mail-Bein
(`capabilities.load_mail` liest beide Kanäle, weil Mail als einzige optionale App über die
Navigation des angemeldeten Kontos erkannt wird), der dritte ist ein zweiter Abruf des
Capabilities-Dokuments, weil das Talk-Bein gleichzeitig startet und auf dem leeren Cache mit dem
Mail-Bein um denselben Eintrag rennt. Nach dem ersten Bündel liegen beide Antworten in einem
Cache-Eintrag, der `capabilities.TTL_SECONDS` (60 s) hält, und ein zweites Bündel innerhalb
einer Minute zahlt keinen davon: kalt 3, warm 0.

Die Aussage im Modul-Docstring lautete "bis zu zwei Erkennungsrequests bei kaltem Cache". Für
das Mail-Bein allein ist das richtig, für das Bündel als Ganzes nicht, und der Kommentar ist mit
dieser Messung entsprechend präzisiert worden.

Der Rest der Rechnung ist unverändert und stand nicht zur Debatte: die Suche kostet eine
Providerliste plus einen Request je Provider (hier 13), der Kalender zwei DAV-Requests
(PROPFIND über die Sammlungen, REPORT über das Fenster), das Talk-Bein genau einen.

## Nebenwirkungsfreiheit

Gemessen an `fetch("message:6c3pifti:17")`, einer Id aus einem echten Suchtreffer (Suchwort
"moderation"), in einer Konversation, die vor dem Aufruf etwas Ungelesenes trug. Das ist
Absicht: ein Zähler, der schon 0 ist, kann nicht fallen, und eine grüne Zeile auf einer
gelesenen Konversation wäre wahr und wertlos.

| Feld | Vorher | Nachher |
|---|---|---|
| `unread` | 7 | 7 |
| `unread_mention` | `false` | `false` |
| `unread_mention_direct` | `false` | `false` |
| `unread` der übrigen vier Konversationen | 0, 0, 3, 0 | 0, 0, 3, 0 |

**Die Messung lief über `talk_browse(level="conversations")` und nicht über die geprüfte
Route.** Die Regel stammt aus Plan 10-08: die zu prüfende Operation darf nicht das Messwerkzeug
sein. `fetch("message:...")` geht über
`GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}/{messageId}/context`, und genau diese Route
soll den Lesemarker nicht bewegen. Hätte man den Marker über dieselbe Route gelesen, wäre eine
Bewegung unsichtbar geblieben. `unread_mention_direct` steht mit in der Tabelle, weil eine
quittierte Benachrichtigung sich dort zuerst zeigen würde, und "soweit die Konversationsliste es
zeigt" ist der ehrliche Umfang dieser Aussage.

Damit ist belegt, was bisher nur aus dem Quelltext von spreed 24.0.4 gelesen war: der neuere
Teil des Fensters wird über `waitForNewMessages` mit Timeout 0 geholt, derselbe Aufruf übergibt
`markNotificationsAsRead: false`, und `updateLastReadMessage` wird nie erreicht.

## Offene Punkte

- **Die Falle T12 ist auf dieser Instanz nicht vorhanden.** Der Plan erwartete den Beweis "der
  Zähler ist kein Nachrichtenzähler" an einer Konversation mit `unread == 1` und leerer
  Historie. Die Changelog-Konversation dieser Instanz (`q5s5xqp5`, Typ 4) meldet stattdessen
  `unread` 3 bei drei lesbaren Nachrichten. Der Beweis läuft deshalb über den umgekehrten und
  stärkeren Fall: `o4vwrd7g` trägt sechs lesbare Nachrichten und meldet `unread` 0. Der Test
  behauptet die Divergenz und prüft den T12-Fall zusätzlich, wenn er da ist; er zählt aktuell
  null Vorkommen.
- **`truncated` auf der Nachrichtenebene heisst nicht "es gibt mehr zu lesen".** Es heisst, dass
  die App eine Fortsetzungs-Id mitgegeben hat, und das tut sie auch bei leerem Fenster (siehe
  `talk._messages`). Eine Divergenz gilt deshalb nur als bewiesen, wenn ein Fenster sie
  entscheidet: `unread` unter dem Fenster ist Beweis für sich, `unread` über dem Fenster nur
  ohne Fortsetzung. Diese Unterscheidung ist während der Messung entstanden und steht im
  Docstring der Messung.
- **Ein einmaliger 404 auf `/apps/mail/account/list`.** Während der Vorerkundung am 2026-08-24
  um etwa 21:07Z antwortete die Route einmal so, dass das Mail-Bein mit genau einem
  `degraded`-Satz ausfiel ("Nextcloud did not find the mail accounts.") und das Bündel im
  Übrigen vollständig blieb. Der nächste Aufruf war grün. In zwölf aufeinander folgenden
  Bündelaufrufen danach und in drei vollen Testläufen ist es nicht wieder aufgetreten, also ist
  die Ursache nicht gemessen und wird hier nicht behauptet. Das Verhalten im Fehlerfall ist
  genau das entworfene: ein Bein aus, ein benannter Satz, das Bündel benutzbar.
- **Der Deck-Kommentar-Provider antwortet sporadisch 500.** Das Suchbein reicht das als eigenen
  `degraded`-Eintrag durch, wie vorgesehen. Deshalb behauptet keine Messung dieses Laufs eine
  leere `degraded`-Liste; behauptet wird die Abwesenheit von Einträgen, die eine verpasste
  Zeitdecke nennen. Eine fremde App mit einem Wackler darf keine rote Messung von uns erzeugen.
- **Die Referenz aus Plan 04-04 kommt aus einer MCP-Sitzung, diese Messung aus dem Testprozess.**
  Der Vergleich ist deshalb aussagekräftig, aber nicht auf die zweite Stelle belastbar: der
  Client- und Proxy-Sprung der Referenz fehlt hier. Beide Zahlen stehen oben, damit niemand die
  Differenz für eine reine Codeänderung hält.
