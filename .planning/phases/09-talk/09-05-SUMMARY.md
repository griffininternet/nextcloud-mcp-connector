---
phase: 09-talk
plan: 05
subsystem: testing
tags: [integration, nebenwirkungsfreiheit, impersonation, bootstrap, spreed, idempotenz]

# Dependency graph
requires:
  - phase: 09-talk
    provides: "clients/talk.py mit READ_ONLY_PARAMS, get_rooms, get_messages, send_message, web_url (Plan 09-01)"
  - phase: 09-talk
    provides: "tools/talk.py mit browse(level=conversations|messages) und send samt Vorpruefungen (Plan 09-03)"
  - phase: 09-talk
    provides: "reg_talk.py, 20 Werkzeuge, das Destruktiv-Gate der Talk-Familie (Plan 09-04)"
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "test_tables_roundtrip.py als Testbauplan, der Tables-Zwei-Konten-Block als Bauplan der Impersonation-Naht, ensure_mail_account als Vorbild fuer Geruest hinter der Nutzeranlage"
provides:
  - "Erfolgskriterium 3 live gemessen: acht Werte, vier Felder vorher und nachher, in einem gruenen Lauf sichtbar"
  - "tests/integration/test_talk_roundtrip.py: neun Tests auf beiden Topologien gruen"
  - "Talk-Zwei-Konten-Beweis auf der Impersonation-Naht, mit den zwei Statuscodes der Instanz als Messwert"
  - "ensure_app spreed und ensure_talk_room in beiden Bootstrap-Skripten, idempotent nach Namen"
  - "Der Befund, dass spreed 24.0.4 kein listendes occ-Kommando mitbringt, und der Weg um ihn herum"
affects: [10 SRV-06, 10 SEC-01, 11 CTX-01, 11 TOOL-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Geruest per occ, Namen ueber die Verbindungsdatei in den Test: eine Umbenennung ist eine Aenderung"
    - "Idempotenz nach Namen ohne listendes CLI-Kommando: Suche in der Konversationsliste des Kontos ueber die eigene API"
    - "Die gemessene Eigenschaft wird vorher hergestellt: ein Lesevorgang ueber einem leeren Fenster koennte den Lesemarker nirgendwohin bewegen und waere die schwaechere Messung"
    - "Ein Statuscode der Instanz wird gemessen und nicht erwartet, weil die eigene Absage vor dem Request steht und deshalb keinen Status hat"

key-files:
  created:
    - tests/integration/test_talk_roundtrip.py
  modified:
    - scripts/bootstrap_exapp.sh
    - scripts/bootstrap_test_nc.sh
    - tests/integration/test_permission_fidelity_exapp.py
    - .env.exapp.example
    - .env.test.example

key-decisions:
  - "spreed 24.0.4 bringt kein talk:room:list mit (gemessen: create, update, delete, add, remove, promote, demote und nichts, was listet); die Idempotenz nach Namen laeuft deshalb ueber GET /apps/spreed/api/v4/room mit dem Konto selbst, und das Verifikationskommando des Plans, das talk:room:list aufruft, ist durch eine Inventarabfrage ueber dieselbe Route ersetzt"
  - "Der Name wird auf seinem ASCII-Praefix gematcht: PHP schreibt jeden Umlaut einer JSON-Antwort als \\uXXXX-Escape, ein grep auf den Literalnamen haette nie getroffen"
  - "Die zwei Konversationsnamen tragen keine Leerzeichen: die Verbindungsdatei wird mit set -a und . gelesen, und ein unquotierter Wert mit Leerzeichen laesst die Shell sein zweites Wort als Kommando ausfuehren (im ersten Lauf gemessen)"
  - "Die Schreibsperre wird bei jedem Lauf per occ talk:room:update --readonly gesetzt statt nur beim Anlegen, weil sie das Objekt ist, an dem der Negativfall gemessen wird"
  - "Die clients-Fixture des Rundlauf-Tests nimmt beide Schreibweisen des Kontos an (NC_MCP_USER/NC_MCP_APP_PASSWORD und NC_MCP_TEST_USER/NC_MCP_TEST_APP_PASSWORD), weil das Geruest auf beiden Topologien steht und ein Test, der nur eine Schreibweise kennt, gegen die gemessene Topologie uebersprungen haette"
  - "Die Nebenwirkungs-Messung fuellt die Konversation vorher, wenn ihr Verlauf leer ist: setReadMarker kann nur einen Marker bewegen, der ein Ziel hat"
  - "Die zwei direkten Statusabfragen als bob sind Geruest und ausdruecklich nicht der Weg des Connectors; der Kommentar nennt den Brute-Force-Preis einer Einzelkonversations-Route und dass der Waechter auf dieser Wegwerf-Topologie abgeschaltet ist"
  - "TALK-01, TALK-02 und TALK-03 sind abgehakt: die Werkzeuge sind seit 09-04 registriert, und die Live-Messung dieses Plans ist der letzte Baustein, den ihr Wortlaut verlangt"

patterns-established:
  - "Eine Messung, die eine Zusage belegen soll, stellt ihre Voraussetzung her, statt sie abzuwarten"
  - "Zwei Beweisschichten, die sich gegenseitig tragen: die ausgehende URL (unsere Werte verlassen den Prozess) und der Kontozustand (nichts hat sich bewegt); jede allein waere gruen, auch wenn die andere falsch ist"

requirements-completed: [TALK-01, TALK-02, TALK-03]

# Metrics
duration: 29 min
completed: 2026-08-21
---

# Phase 9 Plan 05: Live-Nachweis auf zwei Topologien Summary

**Erfolgskriterium 3 ist gemessen und nicht behauptet: `lastReadMessage 23 -> 23`, `unreadMessages 0 -> 0`, `unreadMention False -> False`, `lastCommonReadMessage 23 -> 23` um einen Verlauf-Lesevorgang mit einer Nachricht im Fenster, dazu die Live-Gegenprobe, dass alle vier Leseparameter wirklich ausgehen, ein echter Sendevorgang samt Wiederfinden mit Umlauten, die Absage der schreibgeschuetzten Konversation und ein zweites Konto, das alices Konversation nicht sieht, ihren Verlauf mit dem echten Token nicht erreicht und nichts darin zuruecklaesst.**

## Performance

- **Duration:** 29 min
- **Started:** 2026-08-21T12:37:30Z
- **Completed:** 2026-08-21T13:06:00Z
- **Tasks:** 3
- **Files modified:** 6 (1 neu, 5 geaendert)
- **Tests:** 9 neue Integrationstests plus 3 im Zwei-Konten-Beweis, alle gruen gegen die laufende HaRP-Topologie; die neun auch gegen die App-Passwort-Instanz

## Die Messwerte, die dieser Plan schuldet

Der Plan verlangt sie ausdruecklich in dieser Zusammenfassung, weil Phase 10 (SRV-06, SEC-01)
und Phase 11 (CTX-01, TOOL-16) darauf aufbauen.

**Installierte Talk-Version:** `spreed 24.0.4` auf **beiden** Topologien, per `occ app:list`
und zusaetzlich aus der `spreed`-Sektion von `/cloud/capabilities` gelesen. Das ist genau die
Version, gegen die 09-RESEARCH.md den Quellcode gelesen hat; 104 Features, `config.chat.
max-length` 32000.

**Die acht Werte der Nebenwirkungs-Messung** (HaRP-Topologie, Konversation `o4vwrd7g`, ein
Nachrichtenfenster mit einer Nachricht):

| Feld | vorher | nachher |
|------|--------|---------|
| `lastReadMessage` | 23 | 23 |
| `unreadMessages` | 0 | 0 |
| `unreadMention` | False | False |
| `lastCommonReadMessage` | 23 | 23 |

Auf der App-Passwort-Instanz dasselbe Bild mit `lastReadMessage 26 -> 26` und
`lastCommonReadMessage 26 -> 26`.

**Die ausgehende URL des gemessenen Lesevorgangs**, also die Gegenprobe, dass die vier Werte
den Prozess wirklich verlassen:

```
/ocs/v2.php/apps/spreed/api/v1/chat/o4vwrd7g
  ?lookIntoFuture=0&setReadMarker=0&markNotificationsAsRead=0&noStatusUpdate=1
  &limit=20&lastKnownMessageId=0
```

**Der beobachtete Statuscode von bobs Zugriff:** `GET 404` und `POST 404`. Nextcloud gibt die
Existenz der Konversation also nicht preis, genau wie Phase 8 es fuer ein fremdes
Tables-Objekt gemessen hat, und **nicht** 403. Wichtig fuer die Lesart: diese zwei Zahlen
stammen aus einer Geruest-Abfrage des Tests. Der Connector selbst kommt nie so weit, seine
zwei Absagen an bob lauten beide `The token 'o4vwrd7g' is not in the conversation list of this
account.` und entstehen aus der eigenen Konversationsliste, bevor irgendein Talk-Pfad gebaut
wird. Alices Nachrichtenzahl war vor und nach bobs Versuchen gleich.

**Zustand des Admin-Schalters auf der Topologie:** `talk_send_enabled() == True`,
`NC_MCP_TALK_SEND` ist auf keiner der beiden Topologien gesetzt. Der Test stellt das fest und
nimmt es nicht an, und er behauptet zusaetzlich beide Enden des Schalters (`"0"` schliesst,
ein leerer Wert laesst offen).

## Task Commits

Each task was committed atomically:

1. **Task 1: spreed und zwei Testkonversationen in beide Bootstrap-Skripte** - `287640c` (chore)
2. **Task 2: Live-Nachweis der Nebenwirkungsfreiheit, des Sendens und der Absage** - `ad7d4f4` (test)
3. **Task 3: Zwei-Konten-Negativbeweis fuer Talk auf der Impersonation-Naht** - `82bce95` (test)

## Accomplishments

- Die Voraussetzung, die auf **keiner** Topologie existierte, ist reproduzierbar da: `ensure_app spreed` neben `tables` und `mail`, und zwei benannte Konversationen von alice, eine beschreibbar und eine schreibgeschuetzt. Beide Skripte zweimal gelaufen, beide Male mit demselben Ergebnis: `created` im ersten, `exists` im zweiten Lauf, und alice hat danach genau zwei `MCP-Talk-`Konversationen und nicht vier.
- Erfolgskriterium 3 ist auf zwei Schichten belegt, die sich gegenseitig tragen. Die ausgehende URL zeigt alle vier Leseparameter mit ihren Werten (`test_the_live_history_url_carries_the_four_read_only_parameters`), und die vier Felder des Kontos sind vorher und nachher gleich (`test_reading_the_history_changes_nothing_about_the_account`, jedes Feld einzeln behauptet mit einer Meldung, die es benennt). Jede Schicht allein waere gruen, auch wenn die andere falsch waere: eine Instanz, die unsere Parameter ignoriert, faellt in der zweiten auf, ein Client, der sie nicht sendet, in der ersten.
- Die Messung laeuft nicht ueber ein leeres Fenster. Ist der Verlauf leer, wird vorher eine Nachricht gesendet, weil `setReadMarker` nur einen Marker bewegen kann, der ein Ziel hat; der Messwert nennt die Anzahl der Nachrichten im Fenster mit, damit die Aussagekraft ablesbar bleibt.
- Falle 2 zusammen mit T12 ist als eigener Test festgehalten: die nie beschriebene Konversation antwortet mit `count: 0`, **ohne** den Satz ueber die Basis-URL, und ihr Fenster traegt trotzdem eine Fortsetzung (`next=yes`), weil die App die Fortsetzungs-Id aus der aeltesten gelesenen Systemnachricht nimmt. Genau der Fall, an dem eine Ableitung aus der Ergebnislaenge den aelteren Verlauf verschwiegen haette.
- Der Sendeweg ist ende-zu-ende belegt: die Nachricht kommt mit `id` zurueck, wird im Verlauf derselben Konversation unter ihrem eigenen Wortlaut wiedergefunden, `Grüße aus Hamburg, Straße 1` inklusive, und die Antwort nennt den Anzeigenamen der Konversation zurueck. Der Sendeversuch in die schreibgeschuetzte Konversation wird mit einem Satz samt naechstem Schritt abgelehnt, der Hinweis zeigt auf `can_send`, und die Nachrichtenzahl derselben Konversation ist davor und danach gleich.
- T10 ist live belegt und nicht nur unit-belegt: ein erfundenes Token wird von unserem eigenen Satz abgelehnt, und der Test behauptet, dass es in **keinem** ausgehenden Request vorkommt, weder im Pfad noch in der Query, sowie dass die Absage nach einem Blick in die eigene Konversationsliste entstand (`ROOM_PREFIX` in den beobachteten Requests). Die Regel steht damit im Code, nicht in der Topologie, wo der Brute-Force-Waechter ohnehin abgeschaltet ist.
- Die Kernzusage des Projekts gilt fuer die neue Familie, und die Positivkontrolle laeuft im selben Lauf: alice liest den Verlauf ihrer Konversation unter reiner AppAPI-Impersonation (damit ist zugleich beantwortet, dass Talks OCS-Routen ohne jedes Nutzerpasswort erreichbar sind), bob hat sie nicht in seiner Liste, erreicht sie mit dem echten Token nicht und kann nicht hineinsenden.
- Alle Gates gruen und nichts Fremdes angefasst: `uv run pytest -q` ueber die ganze Default-Auswahl, `tests/contract/` einzeln, `ruff check .`, `ruff format --check .`, `pyright` (0 errors), `vulture src/mcp_connector vulture_whitelist.py`, `scripts/check_tool_budget.py` (unveraendert 14312 Bytes bei 20 Werkzeugen). Kein Produktionscode dieses Plans: `git diff` gegen den Stand vor dem Plan nennt an `src/` keine einzige Datei.

## Files Created/Modified

- `tests/integration/test_talk_roundtrip.py` (neu, 546 Zeilen) - neun Tests. Modul-Docstring mit den drei Fragen, die nur eine laufende Instanz beantwortet, und dem Satz, warum die Changelog-Konversation nie Ziel ist. `STATE_FIELDS`, `unique_message`, `measured`, die Fixtures `talk_env`, `clients`, `writable`, `write_protected` (die letzten zwei mit dem Changelog-Wachposten beziehungsweise dem Skip bei fehlender Schreibsperre), die Helfer `_spreed_section`, `_rooms`, `_named_room`, `_state`, `_sending_is_switched_on`.
- `scripts/bootstrap_exapp.sh` - `ensure_app spreed` mit Begruendung; `talk_room_token` und `ensure_talk_room` samt dem Kommentarblock, der die fehlende Listen-Faehigkeit von `occ`, die `\uXXXX`-Kodierung und die Nicht-Idempotenz von `talk:room:create` erklaert; der Aufruf hinter der Nutzeranlage mit dem Grund von `ensure_mail_account`; die vier Namenszeilen; zwei Zeilen in der Verbindungsdatei.
- `scripts/bootstrap_test_nc.sh` - dasselbe, plus `BASE_URL` und ein `nc_body` nach dem Vorbild des Schwesterskripts, weil dieses Skript bisher keinen HTTP-Weg hatte. `NC_MCP_URL` in der Verbindungsdatei kommt jetzt aus `BASE_URL`.
- `tests/integration/test_permission_fidelity_exapp.py` - Absatz im Modul-Docstring; Talk-Block am Ende: `TALK_ROOM_ENV`, `TALK_INTRUSION`, `measured`, die Fixtures `alice_talk`, `bob_talk` und `alices_conversation`, die Helfer `_message_count` und `_talk_status`, drei Tests in der Reihenfolge Positivkontrolle, fehlende Liste, unerreichbarer Verlauf und unerreichbarer Sendeweg.
- `.env.exapp.example`, `.env.test.example` - die zwei neuen Variablen dokumentiert.

## Decisions Made

- **Die Idempotenz nach Namen laeuft ueber die API und nicht ueber `occ`.** spreed 24.0.4 hat kein listendes Room-Kommando: gemessen sind `talk:room:create`, `update`, `delete`, `add`, `remove`, `promote`, `demote` und `talk:monitor:room` (das ein Token braucht). Die Suche geht deshalb ueber `GET /apps/spreed/api/v4/room` mit dem Konto selbst, per `nc_body` und damit auf demselben Weg, den die Share-Fixture von Plan 05-03 schon benutzt.
- **Der Name wird auf seinem ASCII-Praefix gematcht.** PHP schreibt Umlaute in JSON als `\uXXXX`, also traf ein `grep` auf `MCP-Talk-offen-Grüße` nie. Die vier Namenszeilen bauen den vollen Namen aus einem eindeutigen ASCII-Praefix plus dem Umlaut-Teil; gematcht wird auf `"displayName":"<Praefix>`.
- **Die Schreibsperre wird bei jedem Lauf gesetzt.** `occ talk:room:create --readonly` gaebe es, aber `talk:room:update <token> --readonly 1` bei jedem Lauf ist die staerkere Aussage: sie stellt den Zustand fest her und reparlert eine Konversation, die jemand zurueckgestellt hat. Genau die Sorge, die die Recherche fuer den Admin-Wert formuliert hat, nur ein Objekt weiter.
- **`talk_env` nimmt beide Schreibweisen des Kontos an.** `.env.test` nennt es `NC_MCP_USER`/`NC_MCP_APP_PASSWORD`, `.env.exapp` nennt es `NC_MCP_TEST_USER`/`NC_MCP_TEST_APP_PASSWORD`, und das Geruest steht auf beiden Topologien. Eine Fixture nach dem Vorbild von `live_env` allein haette beim vom Plan selbst vorgegebenen Verifikationskommando (`. ./.env.exapp`) uebersprungen, also einen gruenen Lauf produziert, der nichts gemessen hat.
- **Der Zustand wird ueber den rohen Client gelesen, der gemessene Lesevorgang ueber das Werkzeug.** Die Projektion von `talk_browse` traegt die vier Felder bewusst nicht, und das ist richtig; die Messung braucht sie, also liest sie `talk_client.get_rooms`. Die Eigenschaft muss fuer das gelten, was der Connector zusagt, nicht fuer eine Anfrage, die der Test selbst gebaut hat.
- **Die zwei direkten Statusabfragen als bob bleiben Geruest.** Sie beantworten, was die Instanz selbst sagt (404/404), und der Docstring sagt ausdruecklich, dass der Connector diesen Weg nie geht und warum: eine Einzelkonversations-Route mit einem fremden Token ist genau der gezaehlte Brute-Force-Versuch, den T10 vermeidet. Ein Lauf pro Testlauf auf einer Wegwerf-Topologie mit abgeschaltetem Waechter ist der Preis fuer die Zahl.
- **`alice_talk` und `bob_talk` sind eigene Fixtures neben `alice_tables` und `bob_tables`.** Dieselbe Naht, andere Objekte: ein Talk-Test, der an den Tables-Fixtures haengt, zieht deren Tabellen-Geruest in seine Voraussetzungen, und ein Skip dort saehe dann wie eine Aussage ueber Talk aus.
- **TALK-01 bis TALK-03 werden abgehakt.** Alle drei sprechen von `talk_browse` und `talk_send` als Werkzeugen (seit 09-04 registriert); TALK-02 verlangt zusaetzlich den Nachweis "nachweislich ohne Nebenwirkung", und der steht mit diesem Plan auf beiden Schichten. TALK-04 war mit 09-04 erfuellt, damit ist die Anforderungsliste der Phase komplett.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Zwei Konversationsnamen mit Leerzeichen machten die Verbindungsdatei unlesbar**

- **Found during:** Task 1
- **Issue:** Der erste Entwurf schrieb `NC_MCP_TEST_TALK_ROOM=MCP-Talk offen Grüße aus Hamburg` in die Verbindungsdatei. Der dokumentierte Weg, diese Datei zu lesen, ist `set -a && . ./.env.test && set +a`, und ein unquotierter Wert mit Leerzeichen laesst die Shell sein zweites Wort als Kommando ausfuehren: `./.env.test: line 12: offen: command not found`. Der Fehler war im ersten Lauf sichtbar und haette jeden `set -a`-Aufruf gegen diese Datei getroffen, nicht nur den Talk-Test.
- **Fix:** Beide Namen ohne Leerzeichen, mit Bindestrichen statt Luecken (`MCP-Talk-offen-Grüße-aus-Hamburg`, `MCP-Talk-nurlesen-Straße-ohne-Ausgang`), und ein Kommentarblock ueber den Namenszeilen, der den Grund nennt. Quoten allein waere die schwaechere Loesung gewesen, weil nicht jeder Leser dieser Datei ein Shell-Parser ist.
- **Files modified:** scripts/bootstrap_exapp.sh, scripts/bootstrap_test_nc.sh, .env.exapp.example, .env.test.example
- **Verification:** `set -a && . ./.env.test && set +a` gibt beide Werte unveraendert zurueck, Umlaute inklusive; die zwei Raeume mit Leerzeichen im Namen sind per `occ talk:room:delete` entfernt und neu angelegt, das Inventar nennt genau zwei `MCP-Talk-`Konversationen.
- **Committed in:** `287640c` (Task 1)

**2. [Rule 3 - Blocking] Das dritte Verifikationskommando von Task 1 ruft ein Kommando auf, das die App nicht hat**

- **Found during:** Task 1
- **Issue:** Der Plan verifiziert das Geruest mit `occ talk:room:list`. spreed 24.0.4 bringt dieses Kommando nicht mit; der `talk:`-Namensraum kennt `room:create`, `room:update`, `room:delete`, `room:add`, `room:remove`, `room:promote`, `room:demote` und `monitor:room` (das ein Token verlangt), aber nichts, was Raeume listet. Beide Haelften des vorgesehenen Kommandos (auch der `||`-Rueckfall) waeren fehlgeschlagen. Dasselbe Kommando steht als Fundament der geforderten Idempotenz im Aktionstext.
- **Fix:** Die Idempotenz laeuft ueber `GET /apps/spreed/api/v4/room` mit dem Konto selbst (`talk_room_token`), auf demselben curl-Weg, den `share_is_readonly_for` seit Plan 05-03 benutzt. Das Verifikationskommando ist durch eine Inventarabfrage ueber dieselbe Route ersetzt, die die Anzeigenamen zaehlt; sie belegt die Akzeptanzkriterien woertlich (genau zwei benannte Raeume nach dem zweiten Lauf). Der Befund steht als Kommentarblock im Skript, damit ihn niemand ein zweites Mal messen muss.
- **Files modified:** scripts/bootstrap_exapp.sh, scripts/bootstrap_test_nc.sh
- **Verification:** `docker exec -u www-data nc-mcp-exapp-nc php occ list | grep "talk:"` nennt kein listendes Kommando; die Inventarabfrage nach zwei Laeufen je Topologie liefert genau `MCP-Talk-offen-Grüße-aus-Hamburg` und `MCP-Talk-nurlesen-Straße-ohne-Ausgang`, je einmal.
- **Committed in:** `287640c` (Task 1)

**3. [Rule 3 - Blocking] `bootstrap_test_nc.sh` hatte keinen HTTP-Weg**

- **Found during:** Task 1
- **Issue:** Die Namenssuche braucht einen authentifizierten Request gegen die Instanz. `bootstrap_exapp.sh` hat `nc_body` seit Plan 05-03, `bootstrap_test_nc.sh` hatte gar keinen curl-Aufruf und auch keine Basis-URL als Variable.
- **Fix:** `BASE_URL` als eine Stelle, die weiss, wo diese Instanz antwortet, und ein `nc_body` woertlich in der Form des Schwesterskripts, also mit dem Passwort im curl-Config-File auf stdin (WR-06) und nicht in `-u`. `NC_MCP_URL` in der Verbindungsdatei kommt jetzt aus derselben Variablen.
- **Files modified:** scripts/bootstrap_test_nc.sh
- **Verification:** `bash -n` fehlerfrei; `test_no_secret_travels_through_the_process_list` und `test_no_grep_q_on_a_pipe_in_the_shell_scripts` gruen, beide laufen ueber alle Shell-Skripte.
- **Committed in:** `287640c` (Task 1)

**4. [Rule 2 - Missing critical] Die Kernmessung waere ueber einem leeren Fenster gelaufen**

- **Found during:** Task 2
- **Issue:** Im ersten gruenen Lauf stand `count=0`: die beschreibbare Testkonversation war frisch, ihr Verlauf enthielt nur Systemnachrichten, und die fallen aus der Positivliste. Eine Messung, die `setReadMarker=0` belegen soll, laeuft dann leer: ein Marker, der kein Ziel hat, bewegt sich auch ohne den Parameter nicht. Der Test waere fuer die naechsten Jahre gruen gewesen und haette die Zusage nicht getragen.
- **Fix:** Die Messung fuellt vorher, wenn der Verlauf leer ist und der Schalter an ist, und behauptet danach, dass das Fenster mindestens eine Nachricht traegt (oder dass gesendet abgeschaltet ist). Der Messwert nennt die Zahl der Nachrichten im Fenster mit, damit die Aussagekraft der acht Werte ablesbar bleibt.
- **Files modified:** tests/integration/test_talk_roundtrip.py
- **Verification:** Der Messwert lautet jetzt `messages in the window: 1` auf beiden Topologien.
- **Committed in:** `ad7d4f4` (Task 2)

**5. [Rule 3 - Blocking] `PT018` auf der Umlaut-Behauptung**

- **Found during:** Task 2
- **Issue:** `assert "ü" in open_entry["name"] and "ß" in locked_entry["name"]` gilt ruff als zusammengesetzte Behauptung (`PT018`), und `ruff check .` war rot.
- **Fix:** Zwei getrennte Behauptungen, jede mit einer Meldung, die ihre Konversation nennt; die Fehlermeldung sagt damit auch, welcher der zwei Namen die Kodierung nicht ueberlebt hat.
- **Files modified:** tests/integration/test_talk_roundtrip.py
- **Verification:** `uv run ruff check .` gruen.
- **Committed in:** `ad7d4f4` (Task 2)

**6. [Rule 2 - Missing critical] Die zwei neuen Variablen fehlten in den Beispiel-Verbindungsdateien**

- **Found during:** Task 1
- **Issue:** `.env.exapp.example` und `.env.test.example` sind die Referenz fuer jede Variable, die ein Bootstrap schreibt, und ein Test haelt fuer die Testinstanz fest, dass die Beispielfassung jede Variable nennt. Zwei neue Variablen ohne Zeile dort waeren genau die Drift, die diese Dateien verhindern sollen. Der Plan nennt beide Dateien nicht.
- **Fix:** Je ein Absatz mit den zwei Variablen und dem Satz, wofuer sie stehen und dass der Talk-Test ohne sie ueberspringt.
- **Files modified:** .env.exapp.example, .env.test.example
- **Verification:** `uv run pytest tests/unit/test_test_env_setup.py tests/unit/test_exapp_env_setup.py -q` gruen; `.env.exapp.example` haelt weiterhin kein benutzbares Geheimnis.
- **Committed in:** `287640c` (Task 1)

---

**Total deviations:** 6 auto-fixed (3 blockierend, 1 Bug, 2 fehlende kritische Absicherungen)
**Impact on plan:** Kein Scope-Zuwachs, keine offene Absage. Ein Punkt ist ein echter Fehler
im ersten Entwurf (Leerzeichen in der Verbindungsdatei), einer ist eine Annahme des Plans
ueber ein `occ`-Kommando, das die App nicht hat, zwei sind Luecken in der bestehenden
Infrastruktur (kein HTTP-Weg im Testskript, fehlende Beispielzeilen), einer ist ein Gate
dieses Repos (`PT018`) und einer ist die Verstaerkung genau der Messung, um die dieser Plan
gebaut ist. Die einzige Abweichung von einem Verifikationskommando des Plans ist der Ersatz
von `occ talk:room:list`, und der ist unvermeidbar: das Kommando existiert nicht.

## Issues Encountered

- `unreadMessages` und `unreadMention` stehen auf dieser Topologie beide auf 0 und koennen es
  nicht anders: alice ist die einzige Teilnehmerin ihrer Testkonversationen, und ein Konto
  liest seine eigenen Nachrichten mit dem Senden. Die zwei Felder sind damit belegt, dass sie
  sich nicht **veraendern**, aber nicht daran, dass ein Zaehler ungleich null unangetastet
  bleibt. Ein zweites Konto in derselben Konversation waere der staerkere Aufbau; er kostet
  eine Teilnehmer-Zeile im Bootstrap und gehoert in die Phase, die einen Grund dafuer hat
  (`bob` ist heute bewusst kein Teilnehmer, weil der Zwei-Konten-Beweis genau davon lebt).
  `lastReadMessage` und `lastCommonReadMessage` tragen die Aussage voll, weil sie sich beim
  Lesen bewegen wuerden.
- Das leere Fenster der schreibgeschuetzten Konversation antwortet mit `count: 0` **und**
  einer Fortsetzung (`next=yes`), nicht mit einer 304. Grund: die Konversation traegt
  Systemnachrichten, die App setzt `X-Chat-Last-Given` aus der aeltesten gelesenen Nachricht
  und filtert erst danach. Der Test behauptet deshalb `count == 0` und nicht die Abwesenheit
  von `next`; das ist derselbe Fall, den Plan 09-03 als Falle 6 unit-getestet hat, nur diesmal
  auf einer echten Instanz.

## Known Stubs

Keine. Alle neun Tests des Rundlaufs und alle drei Tests des Talk-Blocks laufen gegen eine
echte Instanz und behaupten etwas. Was fehlt, ist ausdruecklich nicht Teil dieses Plans: der
Degradations-Nachweis fuer eine deaktivierte Talk-App (SRV-06, Phase 10, braucht den
Nextcloud-Neustart) und der SEC-01-Doku-Abschnitt zur Exfiltrationskette (Phase 10, weil
Mail-Lesen noch nicht existiert).

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche gegenueber dem `<threat_model>` des Plans: kein
neuer Netzwerkendpunkt, kein neuer Auth-Pfad, keine Schema-Aenderung an einer
Vertrauensgrenze, keine neue Abhaengigkeit und kein Produktionscode. Ein Punkt gehoert
trotzdem ins Protokoll, weil er das Register praezisiert: T-09-42 verlangt, dass ein
unbekanntes Token Nextcloud nie in einem Pfad erreicht, und der Test belegt das fuer den
Connector. Die zwei Geruest-Abfragen in `_talk_status` bauen genau so einen Pfad **absichtlich**
und mit einem echten fremden Token, um den Statuscode der Instanz zu messen. Sie laufen nur
auf der Wegwerf-Topologie mit abgeschaltetem Brute-Force-Waechter, einmal pro Lauf, und ihr
Docstring sagt beides.

## User Setup Required

None - no external service configuration required. Beide Topologien tragen die Talk-App und
das Geruest nach einem Lauf des jeweiligen Bootstrap-Skripts; `NC_MCP_TALK_SEND` bleibt
ungesetzt, der Sende-Schalter ist damit an.

## Next Phase Readiness

- **Phase 10 (SRV-06)** findet die Talk-Familie live nachgewiesen vor und kann sich auf die
  Degradation beschraenken. Der Weg dafuer steht in der Recherche und ist in dieser Phase
  bestaetigt worden: eine per `occ` deaktivierte App bleibt in `/cloud/capabilities` sichtbar,
  bis die Nextcloud neu startet, ein Degradations-Test fuer `spreed` braucht also den Neustart.
- **Phase 10 (SEC-01)** kann den Ausgangskanal beim Namen nennen und auf zwei gemessene Dinge
  verweisen: der Schalter ist an per Default und sein Zustand ist feststellbar, und ein
  zweites Konto erreicht eine fremde Konversation weder lesend noch schreibend (404/404 von
  der Instanz, davor die eigene Absage).
- **Phase 11 (CTX-01, TOOL-16)** hat die Zahlen: 20 Werkzeuge bei 14312 Bytes, `talk_browse`
  861 und `talk_send` 648 Bytes, 688 Bytes Luft. Fuer die Bucket-Frage von `prepare_context`
  liegt zusaetzlich vor, dass ein Verlauf-Fenster mit `limit=20` in dieser Testlage null bis
  eine Nachricht liefert und die Kappe pro Nachricht bei 800 Bytes steht.
- Die Testkonversationen wachsen mit jedem Lauf um eine Nachricht (der Rundlauf sendet eine,
  die Messung gelegentlich eine zweite). Das ist gewollt und harmlos: die Nutzlast traegt eine
  Laufkennung, der Verlauf ist gekappt, und keine Behauptung dieses Plans haengt an einer
  festen Nachrichtenzahl.
- **ExApp-Topologie, Stand nach 09-05:** laeuft. `nc-mcp-exapp-nc` auf NC 34.0.3, ExApp
  `mcp_connector` neu gebaut und registriert auf `127.0.0.1:5000/mcp_connector:0.1.3`
  (`sha256:03019e651bc5`), also den Arbeitsbaum-Stand nach 09-04. `.env.exapp` ist von diesem
  Lauf neu geschrieben (frische App-Passwoerter fuer alice und bob, `APP_SECRET` und
  Share-Suffix `04d2eb7d6d` wiederverwendet) und traegt jetzt die zwei Talk-Variablen.
  Beide Instanzen tragen `spreed 24.0.4` und alices zwei Konversationen.

## Self-Check

- `tests/integration/test_talk_roundtrip.py` FOUND (546 Zeilen, alle vier Feldnamen vorhanden, `measured(` vorhanden)
- `scripts/bootstrap_exapp.sh` FOUND (`ensure_app spreed` vorhanden, `talk:room:create` vorhanden, `bash -n` fehlerfrei)
- `scripts/bootstrap_test_nc.sh` FOUND (`ensure_app spreed` vorhanden, `talk:room:create` vorhanden, `bash -n` fehlerfrei)
- `tests/integration/test_permission_fidelity_exapp.py` FOUND (`talk` vorhanden, drei neue Tests)
- Commit `287640c` FOUND
- Commit `ad7d4f4` FOUND
- Commit `82bce95` FOUND
- `uv run pytest tests/integration/test_talk_roundtrip.py -m integration -q` gegen `.env.exapp` 9 passed, gegen `.env.test` 9 passed
- `uv run pytest tests/integration/test_permission_fidelity_exapp.py -m integration -q` gegen `.env.exapp` 15 passed
- Beide Dateien in einem Lauf: 24 passed
- `uv run pytest -q` gruen ueber die ganze Default-Auswahl; `tests/contract/` einzeln 51 passed
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors), `uv run vulture src/mcp_connector vulture_whitelist.py` (Exit 0) alle gruen
- `uv run python scripts/check_tool_budget.py` Exit-Code 0, unveraendert 14312 Bytes bei 20 Werkzeugen
- Zweiter Lauf beider Bootstrap-Skripte: `exists` statt `created`, Inventar je Topologie genau zwei `MCP-Talk-`Konversationen
- `occ app:list | grep spreed` auf beiden Topologien: `spreed: 24.0.4`, identisch mit der Recherche
- Kein Em-Dash, kein En-Dash und keine Emojis in den sechs geaenderten Dateien

## Self-Check: PASSED

---
*Phase: 09-talk*
*Completed: 2026-08-21*
