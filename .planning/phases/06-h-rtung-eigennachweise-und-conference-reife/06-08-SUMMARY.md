---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 08
subsystem: oauth-clients-and-docs
tags: [client-04, cursor, dcr, redirect-uri, d-35, measurement, docs, negative-finding]

# Dependency graph
requires:
  - phase: 06-07
    provides: "die Messtopologie auf 34.0.3.2 mit dem Connector aus dem Arbeitsbaum (0.1.2, Digest sha256:3ba4a2ce1921), jane und ihre zwei Verbindungen"
  - phase: 06-03
    provides: "die Loopback-Portregel, deren Nichtgreifen hier gemessen und erklaert wird"
provides:
  - "06-08-MEASUREMENTS.md: Verfuegbarkeitsbefund, Discovery-Kette mit Zeitstempeln, DCR 201 mit Store-Zeile Feld fuer Feld, die Abweisung an /authorize mit Wortlaut, drei Gegenproben, sechs unvorhergesagte Funde, Nachzustand"
  - "der gemessene Befund zu CLIENT-04: Cursor 3.2.16 registriert sich mit 201, besteht danach auf cursor:// und wird mit 400 abgewiesen; kein Token, kein Werkzeugaufruf"
  - "der Grund auf Client-Seite, belegt: Cursor liest die registrierten Adressen nicht aus der Antwort zurueck, sondern behaelt seine drei"
  - "docs/oauth-setup.md und docs/client-setup.md ohne die zwei offenen Saetze, mit datiertem Live-Ergebnis und Verweis auf die Messdatei"
  - "BL-14 mit der offenen Entscheidung (Schema registrieren, wieder ganz abweisen, das Verworfene sichtbar machen, oder so lassen)"
affects: [CLIENT-04, BL-04, D-35, 06-09, 06-10, CONF-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Client-Nachweis beginnt mit einer Verfuegbarkeitspruefung mit Rohbeleg (gesuchte Pfade, gefundene Datei, Versionszeichenkette), nicht mit der Messung"
    - "Der gesendete DCR-Rumpf ist aus der Ablage des Clients belegbar, wenn der Server ihn nicht echot: was nur im gesendeten Rumpf stehen kann und nicht in der Antwort, ist damit bewiesen"
    - "Eine Abweisung wird mit drei Anfragen getrennt, die sich in genau einem Feld unterscheiden: erst dann ist 'es ist die Adresse' und nicht 'es ist die Instanz' eine Messung"
    - "Ein negativer Client-Befund wird in der Doku als Zustand im Titel gefuehrt und nicht als Fussnote; die frueher zu optimistische Lesart wird ausdruecklich korrigiert"
    - "Fremde GUI-Software des Owners wird fuer eine Messung nicht neu gestartet und nicht mit Debug-Port angefahren; der Halt ist der Ausweg, nicht die Umgehung"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-08-MEASUREMENTS.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-08-SUMMARY.md
  modified:
    - docs/oauth-setup.md
    - docs/client-setup.md
    - CHANGELOG.md
    - .planning/BACKLOG.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Task 2 (Operator-Entscheid) entfaellt: Cursor 3.2.16 ist installiert, der Auslöser des Halts ist nicht eingetreten. Nichts wurde installiert und nichts heruntergeladen"
  - "Der Lauf hat bei needsAuth gehalten und den Operator gefragt, statt Cursor mit --remote-debugging-port neu zu starten: das Fenster gehoert dem Owner. Den Browser-Schenkel mit Cursors gespeicherten Versuchsdaten selbst zu fahren waere moeglich gewesen und waere nicht die Behauptung von CLIENT-04 gewesen"
  - "Angemeldet wurde nicht als jane, weil ihr Passwort nirgends steht: occ user:resetpassword haette die App-Passwoerter ihrer zwei OAuth-Verbindungen entwertet und damit die Demo-Substanz fuer CONF-01. Die Frage wurde dadurch gegenstandslos, dass die Abweisung VOR jeder Anmeldeseite liegt"
  - "CLIENT-04 wird NICHT abgehakt: sein Wortlaut verlangt eine durchlaufende Autorisierung und einen Tool-Aufruf, und gemessen ist das Gegenteil. Der Plan ist abgeschlossen, das Requirement nicht"
  - "Kein Fix in diesem Plan. Die vier moeglichen Wege sind in BL-14 benannt; drei davon sind Entscheidungen gegen oder fuer D-35 und keine Reparaturen"
  - "Die zwei Cursor-Client-Zeilen wurden nach dem Lauf entfernt: last_used_at war bei beiden leer, sie sind Messrueckstand und eine Neuregistrierung kostet einen Dateischreibvorgang"
  - "Die drei READMEs bleiben unangetastet: ihre zwei Cursor-Zeilen nennen die stdio-Konfiguration mit App-Passwort, und genau das ist der Weg, der fuer Cursor funktioniert"

patterns-established:
  - "Der Nachweis eines Clients nennt beide Haelften getrennt: wo er ohne Klick weiterkommt (Discovery, Registrierung) und wo er einen Klick braucht (Autorisierung). 'No button involved' war nur fuer die erste Haelfte richtig"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-08-20
---

# Phase 06 Plan 08: Cursor live gegen die Instanz Summary

**Cursor 3.2.16 registriert sich gegen 0.1.2 mit `201` und genau den zwei zulaessigen
Adressen, und verbindet sich trotzdem nicht: es schickt an `/authorize` seine
`cursor://`-Adresse mit, also genau die, die bei der Registrierung verworfen wurde, und wird
mit `400` und der Seite "This app cannot be sent back safely" abgewiesen. Die
Teilregistrierung hat den Fehlschlag von `/register` nach `/authorize` verschoben, nicht
beseitigt, und die Ursache liegt messbar auf der Client-Seite: Cursor liest die
registrierten Adressen nicht aus der Antwort zurueck.**

## Performance

- **Duration:** 35 min Messzeit, davon 11 min Halt beim Operator
- **Tasks:** Task 1 und Task 3 gelaufen, Task 2 entfallen (Cursor war vorhanden)
- **Files modified:** 1 Messdatei, 2 Doku-Dateien, CHANGELOG, BACKLOG

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Verfuegbarkeit von Cursor pruefen, mit Rohbeleg | `b941707` |
| 3a | Discovery und Registrierung live gemessen | `5bebd8c` |
| 3b | Der Grund des Halts bei needsAuth, mit Gegenproben | `632e225` |
| 3c | Die abgewiesene Autorisierung, Gegenproben, Nachzustand | `5b19575` |
| 3d | Die zwei Doku-Abschnitte, BL-14, CHANGELOG | `cfc98e5` |

## Der Befund, in einer Tabelle

| Frage | Antwort, gemessen am 2026-08-20 gegen 0.1.2 (Digest `sha256:3ba4a2ce1921`) |
|-------|---------------------------------------------------------------------------|
| Ist Cursor verfuegbar? | ja, **3.2.16**, `%LOCALAPPDATA%\Programs\cursor\Cursor.exe`, kein `cursor` auf dem `PATH` |
| Verbindet Cursor ohne Klick? | ja, das Schreiben von `~/.cursor/mcp.json` genuegt fuer Discovery und Registrierung, Sekunden spaeter |
| Wird der Drei-URI-Rumpf `201`? | **ja**, Store-Zeile mit `www.cursor.com/agents/mcp/oauth/callback` und `localhost:8787/callback`, ohne die private-use Adresse |
| Durchlaeuft Cursor die Autorisierung? | **nein**, `GET /authorize` mit `redirect_uri=cursor://anysphere.cursor-mcp/oauth/callback` wird `400`, Seite `E5` |
| Ruft Cursor ein Werkzeug auf? | nein, und das ist ausgeschlossen und nicht offen: `auth_codes 0`, `access_tokens 0`, `last_used_at` leer |
| Liegt die Ursache auf unserer Seite? | nein bei der Portregel, nein bei der Teilregistrierung, nein bei der Instanz (drei Gegenproben) |

Die Kette, wie sie im Containerlog steht:

```
15:26:38  GET  200  /.well-known/oauth-protected-resource/mcp
15:26:38  POST 401  /mcp
15:26:38  GET  200  /.well-known/oauth-authorization-server
15:26:39  POST 201  /register
15:26:40  GET  400  /authorize   redirect_uri=cursor://anysphere.cursor-mcp/oauth/callback
15:28:46  GET  400  /authorize   dieselbe Anfrage, zweiter Versuch
```

## Warum das kein Serverfehler ist, in drei Anfragen

Gleiche `client_id`, gleicher `code_challenge`, gleicher `resource`, nur die Rueckadresse
getauscht:

```
http://localhost:8787/callback     (registriert)              -> 302 auf die Zustimmungsseite
http://localhost:51234/callback    (registriert, anderer Port) -> 302 auf die Zustimmungsseite
cursor://anysphere.cursor-mcp/...  (nicht registriert)         -> 400, Seite E5
```

Und die Regel, im laufenden Container statt aus dem Quelltext gelesen:

```
registry.loopback_match('cursor://anysphere.cursor-mcp/oauth/callback', <die zwei>) -> None
registry.loopback_match('http://localhost:51234/callback',             <die zwei>) -> http://localhost:8787/callback
```

Ein privates Schema hat keinen Port, den man lockern koennte. Die Lockerung aus 06-03 ist
also intakt und trifft diesen Fall nicht, und D-35 tut genau das, was es ankuendigt.

## Der Fund, der den Fall erklaert

Cursor behaelt nach dem `201` **seine eigenen drei Adressen**. Belegt aus seiner
Versuchsdatei, deren `clientInformation` eine Mischung ist: `client_id`,
`client_id_issued_at` und `scope` koennen nur aus unserer Antwort kommen, `redirect_uris`
kann nur aus dem gesendeten Rumpf kommen, denn die Antwort trug dort zwei Eintraege und
dieses Feld traegt drei. Fuer die Anfrage nimmt Cursor die erste, und das ist die
verworfene.

RFC 7591 3.2.1 verlangt vom Server, die registrierten Metadaten zu antworten, und der Server
tut das. Ein Client, der diese Antwort nicht zuruecklieset, kann von einem stillen Verwerfen
nicht profitieren. Genau darum hilft "verwerfen statt abweisen" hier nicht, und genau darum
ist die frueher gehoffte Wirkung der Teilregistrierung fuer diesen Client nicht eingetreten.

## Abweichungen vom Plan

### 1. [Rule 3 - Blockierend] Der Halt bei needsAuth war nicht vorgesehen

- **Gefunden in:** Task 3
- **Problem:** Der Plan beschreibt Task 3 als durchlaufenden Lauf. Cursor bleibt nach der
  Registrierung auf `needsAuth` stehen und oeffnet den Browser erst auf einen Klick in
  seinem eigenen Fenster. Gepruefte Auswege: kein `cursor-agent`-Kommando in der
  Installation (`resources/app/bin` traegt `cursor`, `code-tunnel.exe`,
  `cursor-tunnel.exe`), kein Debug-Port auf der laufenden Sitzung, kein Lauscher auf 8787.
- **Loesung:** Halt mit strukturiertem Checkpoint, Zwischenstand committet, Doku
  unangetastet gelassen. Ein Neustart von Cursor mit `--remote-debugging-port` waere der
  technische Ausweg gewesen und wurde nicht genommen: das Fenster gehoert dem Owner und
  laeuft seit dem 16.08. (dasselbe Prinzip wie T-06-52). Der Operator hat den Klick um
  15:26:38Z ausgeloest.
- **Dateien:** Messdatei, Abschnitt 5
- **Commit:** `632e225`

### 2. [Rule 3 - Blockierend] jane's Passwort steht nirgends

- **Gefunden in:** Task 3
- **Problem:** Der Plan verlangt Inhalt, der `jane` gehoert. Ihr Passwort steht in keiner
  Datei des Repositories, in keiner Messdatei und in keinem Commit der Historie.
- **Loesung:** `occ user:resetpassword` wurde NICHT benutzt: ohne das alte Passwort
  entwertet Nextcloud die in den Login-Token gespeicherten App-Passwoerter, also genau die
  zwei OAuth-Verbindungen von `jane`, die die Demo-Substanz fuer CONF-01 sind. Vorgesehen
  war `alice` mit dem Fixture-Passwort aus `scripts/bootstrap_exapp.sh`, gegen die Instanz
  gegengeprueft (`PROPFIND` antwortet `207`). Die Frage wurde dann gegenstandslos: die
  Abweisung liegt vor jeder Anmeldeseite, es wurde ueberhaupt kein Konto angemeldet.
- **Dateien:** keine
- **Commit:** `5b19575`

### 3. [Rule 2 - Vollstaendigkeit] Die zweite Client-Zeile

- **Gefunden in:** Task 3
- **Problem:** Die abgewiesene Anfrage trug eine andere `client_id` als die gemessene
  Registrierung. Als "seltsam" abgehakt waere das ein Loch im Protokoll gewesen.
- **Loesung:** Cursors Log erklaert es: der Knopf ist ein `LogoutServer` mit
  `ReloadClient`, es verwirft seine gespeicherte Registrierung ("No stored client
  information found") und registriert neu. Zwei Klicks, zwei Client-Zeilen, beide ohne
  Verwendung. Steht als eigener Fund in Abschnitt 6.2 und als Punkt 3 des
  Unvorhergesagten.
- **Dateien:** Messdatei
- **Commit:** `5b19575`

### 4. [Rule 2 - Ehrlichkeit] Eine bestehende Doku-Aussage war zu optimistisch

- **Gefunden in:** Task 3
- **Problem:** `docs/client-setup.md` sagte, seit 0.1.2 sei "a client of this shape no
  longer kept out by an address it does not have to use". Die Messung zeigt: dieser Client
  bleibt draussen, nur einen Endpunkt spaeter. Der Plan verlangt nur das Loeschen der zwei
  offenen Saetze, aber eine falsche Nachbarzeile stehenzulassen waere gegen die Locked
  Decision "Doku sagt GENAU das Gemessene".
- **Loesung:** Der Satz ist korrigiert und sagt jetzt, was sich wirklich geaendert hat: der
  Ort des Fehlschlags, nicht sein Ausgang. Dazu ein CHANGELOG-Eintrag, weil eine geaenderte
  Aussage ueber einen namentlich genannten Client nutzerrelevant ist.
- **Dateien:** `docs/client-setup.md`, `CHANGELOG.md`
- **Commit:** `cfc98e5`

### 5. [Rule 2 - Uebergabe] BL-14 statt eines Fixes

- **Gefunden in:** Task 3
- **Problem:** Aus dem Befund folgt eine Entscheidung, und der Plan sieht keinen Fix vor.
- **Loesung:** `.planning/BACKLOG.md`, BL-14: die vier Wege (Schema doch registrieren,
  wieder ganz abweisen, das Verworfene fuer den Client sichtbar machen, so lassen und auf
  das App-Passwort verweisen), jeder mit seinem Preis, plus die Begruendung, warum es nicht
  dringend ist.
- **Dateien:** `.planning/BACKLOG.md`
- **Commit:** `cfc98e5`

## Verifikation

| Kriterium | Beleg |
|-----------|-------|
| Verfuegbarkeit mit Rohbeleg beantwortet | Abschnitt 1: drei gesuchte Pfade, eine gefundene Datei, Version aus `package.json` und `product.json` |
| Cursor-Version, Connector-Version und Digest in der Topologie-Tabelle | 3.2.16, 0.1.2, `sha256:3ba4a2ce1921…`, `RestartCount` 0 |
| Antwortstatus der Registrierung als Rohbeleg | `POST /register ... 201 Created` im Log, Antwortkoerper woertlich aus einer Wiederholung |
| Store-Zeile Feld fuer Feld, ohne `cursor://` | Abschnitt 3, `grep -c "cursor://"` auf der Zeile liefert 0 |
| Werkzeugaufruf | fand nicht statt; `auth_codes 0`, `access_tokens 0`, `last_used_at` leer belegen, dass er ausgeschlossen und nicht uebersehen ist |
| Kein Credential in der Messdatei | kein Token, kein Code, kein `codeVerifier`-Wert, keine `flow`- und `login`-Werte, kein App-Passwort; Grep-Kriterium liefert 0 |
| `grep -c "a live run against Cursor" docs/oauth-setup.md` | 0 |
| `grep -c "not measured yet" docs/client-setup.md` | 0 |
| Neue Cursor-Sektion mit Datum, Version und Verweis | "Measured against Cursor 3.2.16 on 2026-08-20", Link auf `06-08-MEASUREMENTS.md` |
| Em-Dashes und Vokabular-Gate | 0 in beiden Doku-Dateien, in CHANGELOG und BACKLOG |
| READMEs unangetastet | `git diff --stat README.md README.de.md README.fr.md` leer |
| `~/.cursor/mcp.json` im Vorzustand | gelöscht, `test -f` sagt ABSENT; Cursor hat es selbst bemerkt (`cause=config_server_removed`) |
| Instanz im Vorzustand | `clients 2`, `flows 0`, `auth_codes 0`, `access_tokens 0`, `authorizations 2` (beide `jane`, nicht widerrufen), `refresh_tokens 2` |
| Owner-Instanzen unberuehrt | `docker ps`: `nc-mcp-test` und `findling-nextcloud` je "Up 5 days" |
| Tests | `uv run --no-sync pytest tests/unit` 2155 gesammelt, Rueckgabewert 0 |
| Lint | `ruff check .` und `ruff format --check .` sauber (171 Dateien) |

## Was dieser Plan nicht tut

- **Kein Fix.** Der Befund ist benannt, die Entscheidung liegt in BL-14 und gehoert in die
  Phasen-Verifikation oder einen eigenen Plan.
- **Kein Haken an CLIENT-04.** Sein Wortlaut verlangt "Autorisierung und Tool-Aufruf laufen
  durch", und gemessen ist das Gegenteil. Die Messarbeit ist erledigt, das Requirement ist
  beantwortet und nicht erfuellt.
- **Keine Aenderung an den drei READMEs.** Ihre Cursor-Zeilen nennen die
  stdio-Konfiguration mit App-Passwort, und das ist der Weg, der fuer Cursor funktioniert.
- **Kein Neustart fremder Software und keine Installation.** Nichts wurde geladen, nichts
  installiert, kein Container neu gestartet, keine Instanzversion angefasst.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche: dieser Plan aendert keine Route, kein Schema und keinen
Auth-Pfad. Die Aenderungen sind Text. Zwei Beobachtungen aus dem Lauf, die in die
Bewertung gehoeren und keine neue Flaeche sind:

- Jeder Anmeldeversuch von Cursor legt eine DCR-Zeile an, die nie benutzt wird. Die Zeilen
  tragen kein Geheimnis (`client_secret_hash` leer, `token_endpoint_auth_method: none`) und
  keinen Nutzerbezug, sie wachsen aber mit der Zahl der Klicks. Festgehalten als Punkt 3
  des Unvorhergesagten.
- Die Abweisung liefert keine Weiterleitung und keinen Hinweis darauf, welche Haelfte der
  Pruefung gefallen ist (T-03-47). Das ist so gewollt und wurde hier zum ersten Mal an
  einem fremden Client gesehen.

## Requirements

- **CLIENT-04 bleibt offen, mit beantworteter Frage.** DCR mit dem Drei-URI-Rumpf ist
  `201`, das ist der Teil, der zutrifft. Autorisierung und Tool-Aufruf laufen nicht durch,
  und das ist gemessen und nicht vermutet. Uebergabe in BL-14.

## Self-Check: PASSED

- `06-08-MEASUREMENTS.md` und `06-08-SUMMARY.md` liegen auf der Platte.
- Die fuenf Commits `b941707`, `5bebd8c`, `632e225`, `5b19575` und `cfc98e5` sind in
  `git log`.
