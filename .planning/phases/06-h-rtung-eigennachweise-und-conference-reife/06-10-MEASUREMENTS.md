# 06-10 Messprotokoll: das Demo-Drehbuch einmal vollstaendig durchgefahren

Datum des Laufs: 2026-08-20, 16:51 bis 17:03 UTC. Rechner: der Entwicklungsrechner aus
06-RESEARCH.md "Environment Availability". Alles unten ist aus diesem einen Lauf; wo eine
Aussage aus dem Quelltext kommt, steht das dabei.

Konventionen dieses Protokolls, wie in 05-08 und den drei Messdateien dieser Phase:

- `occ` steht fuer `docker exec -u www-data nc-mcp-exapp-nc php occ`.
- Der Basispfad des Connectors ist `http://127.0.0.1:8081/exapps/mcp_connector`.
- **Kein Credential steht in diesem Dokument**, auch kein Wegwerf-Credential (T-05-39):
  kein Token, kein Code, kein `code_challenge`, kein `state`, kein Sitzungscookie und kein
  Kontopasswort.
- Gefahren wurde `docs/conference-demo.md` in der Fassung des Commits `5b9271a`, Schritt fuer
  Schritt und ohne Wissen aus dem Kopf. Was dabei nicht gestimmt hat, steht in Abschnitt 8
  und ist im Drehbuch behoben, nicht hier entschuldigt.

## Topologie des Laufs

| Was | Wert |
|-----|------|
| ExApp-Topologie | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, HaRP, erreichbar unter `http://127.0.0.1:8081` |
| Nextcloud | `version: 34.0.3.2`, `versionstring: 34.0.3`, `installed: true` (aus `occ status`, nicht aus dem Docker-Tag) |
| AppAPI | 34.0.0 (`occ app:list`) |
| Connector | `mcp_connector` 0.1.2, Image-Digest `sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed`, `occ app_api:app:list` meldet `mcp_connector (MCP Connector): 0.1.2 [enabled]` |
| Client | Claude Code 2.1.233 (`claude --version`) |
| Demo-Konto | `alice` aus `scripts/bootstrap_exapp.sh` |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud`, je "Up 5 days", unberuehrt (kein Kommando dieses Laufs nennt sie) |

## Vorzustand, vor dem ersten Schritt

| Was | Wert |
|-----|------|
| `clients` | 2 |
| `flows`, `auth_codes`, `access_tokens` | 0 / 0 / 0 |
| `refresh_tokens` | 2 |
| `authorizations` | 2, beide `jane`, beide `revoked_at` leer |
| `user_access` | 0 Zeilen, also kein Konto pausiert |
| Schalter | `occ app_api:app:config:list mcp_connector` nennt genau `oauth_data_key` und `public_url`; im Container keine `NC_MCP_OAUTH_*`-Variable |

## 1. Die Zeilen des Durchlaufs, je Drehbuch-Schritt

Gemessen wurde die Maschinenzeit, also das, was auf einer Buehne nicht schneller geredet
werden kann. Die Spalte "Drehbuch" ist die Angabe aus `docs/conference-demo.md` **nach** den
Korrekturen aus Abschnitt 8.

| Schritt | Zeit (UTC) | Gemessen | Drehbuch | Ergebnis |
|---------|-----------|----------|----------|----------|
| 0, der ganze Flow in gedruckten Schritten | 16:51:55 bis 16:52:00 | **5 s** | 5 s | `all steps answered as the specification and this deployment require`, sieben Schritte, `tools=16` |
| 1, ein Assistent verbindet sich | 16:52:48 bis 16:52:54 | **6,2 s** | 6 s | `claude mcp login` endet mit Rueckgabewert `0` und `Authenticated with "ncmcp"` |
| 2, der Assistent liest echten Inhalt | 16:53:04 bis 16:53:34 | **30 s** | 30 s | `files_list` auf `/` mit 12 Eintraegen aus `alice`s Files-Home, woertlich als JSON |
| 3, das Konto pausiert und gibt wieder frei | 16:57:48 bis 16:58:19 | **25 s** | 25 s | pausiert: `! Needs authentication` und `403`; freigegeben: `✔ Connected` und `200` |
| 4, das Konto beendet eine Verbindung | 17:01:20 bis 17:01:31 | **11 s** | 11 s | Zeilen 2 auf 1, Seite sagt `Disconnected`, Client `! Needs authentication`, Draht `401` |
| 5, der ganze Satz und was darin fehlt | 17:00:24 bis 17:00:29 | **5 s** | 5 s | fuenfzehn Werkzeuge `OK`, plus die bekannte Zaehlzeile (Abschnitt 8.3) |

**Gesamt gemessen: 82,2 s Maschinenzeit.** Das Drehbuch behauptet in der Summe seiner
Maschinen-Angaben 82 s, also eine Abweichung von 0,2 Prozent. Die Buehnenzeit des Drehbuchs
(4:40) enthaelt das Reden und ist nicht Teil dieses Vergleichs; sie steht je Schritt getrennt
in `docs/conference-demo.md`.

Die Schritte wurden in der Reihenfolge des Drehbuchs gefahren, mit einer Ausnahme: Schritt 5
lief vor Schritt 4, weil Schritt 4 die Verbindung des Clients beendet und Schritt 5 sie nicht
braucht (er laeuft ueber stdio mit App-Passwort). Die Reihenfolge im Drehbuch bleibt, weil sie
auf der Buehne die richtige Dramaturgie hat.

## 2. Schritt 0, der Flow in sieben gedruckten Schritten

```
[step 1] POST /mcp -> 401 | cache_control=no-store | www_authenticate=Bearer error="invalid_token",
         ... resource_metadata="http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"
[step 2] beide Proxy-Wege liefern alle drei Dokumente byteweise gleich
[step 3] GET root:/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp -> 200 | rewrite=active
[step 4] POST /register -> 201 | cache_control=no-store
[step 5] GET /authorize -> 302 | GET /authorize/consent -> 200 | signed_in=True
[step 5] POST /authorize/decide -> 400 | identity=none
[step 5] POST /authorize/decide -> 200 | identity=the session cookie of the sign in | code=present
[step 6] POST /token -> 200 | seconds=0.04
[step 7] POST /mcp -> 200 | tools=16 | transport=streamable-http
[step 7] tool notes_create -> 200 | note_id=note:338 | as_user=alice
[cleanup] POST /revoke -> 200 | connection=ended
all steps answered as the specification and this deployment require
```

Der Schritt raeumt hinter sich auf: die Notiz wird geloescht und die Verbindung beendet. Das
ist der Grund, warum er als Opener taugt und den Vorzustand nicht verbraucht.

## 3. Schritt 1, die Verbindung des echten Clients

```
16:52:48Z claude mcp login started
16:52:49Z   client_id = https://claude.ai/oauth/claude-code-client-metadata
16:52:49Z   redirect_uri = http://localhost:46832/callback
16:52:49Z   code_challenge_method = S256
16:52:50Z GET /authorize -> 302
16:52:52Z GET /authorize/consent -> 200
16:52:52Z   consent page carries 'Client ID host': True
16:52:52Z   consent page carries 'Comes back to this computer': True
16:52:52Z POST /authorize/decide -> 200   (aus dem Browser, der sich angemeldet hat)
16:52:54Z GET the client's callback -> 200
16:52:54Z claude mcp login ended with 0 after 6.2s
16:52:54Z stdout tail: Authenticated with "ncmcp". Its tools are now available in Claude Code.
```

Keine Registrierung: die `client_id` ist die Adresse des Metadatendokuments des Clients, wie
in 06-09. Die Zustimmungsseite traegt beide Zeilen, die das Drehbuch verspricht.

### Zwei Eigenheiten der Messumgebung, benannt statt versteckt

Das Muster ist das von 05-07 und 06-09: eine Automatisierung, die nur der Messung dient, wird
genannt und nicht als Teil des Produkts ausgegeben.

* **`claude mcp login` verlangt ein Terminal.** Der Aufruf prueft, ob seine Eingabe eine ist,
  und endet sonst mit `stdin isn't a terminal`. Gemessen wurde deshalb mit einem echten
  Konsolen-Handle als Eingabe: der Treiber gibt seine eigene Konsole auf, legt eine neue an
  (`AllocConsole`, Windows-Bordmittel per `ctypes`) und uebergibt `CONIN$` als `stdin`,
  waehrend Ausgabe und Fehlerkanal in Dateien laufen. Kein Paket installiert (T-06-SC), und
  einfacher als die Pseudo-Konsole aus 06-09. Zwei Vorproben belegen den Unterschied: mit
  `CREATE_NEW_CONSOLE` allein bleibt `stdin` die Pipe des Elternprozesses und der Lauf endet
  nach 1,7 s mit derselben Meldung wie in 06-09; mit dem Konsolen-Handle lief derselbe Aufruf
  20 s lang mit `Waiting for authorization`.
* **Die zwei Knoepfe, die ein Mensch drueckt, drueckt `scripts/oauth_flow_check.py:sign_in`,**
  also die im Projekt dokumentierte Abkuerzung: die Nextcloud-Anmeldung und "Approve access",
  plus den Sprung des Browsers auf die Rueckadresse des Clients. Der Client baut seine
  Anfrage selbst, haelt seinen eigenen Loopback-Port (46832), tauscht seinen Code selbst ein.
  `--no-browser` statt eines Fensters, aus demselben Grund wie in 06-08 und 06-09: das
  Browserfenster gehoert dem Owner.

Der Client wurde in einem eigenen Projektverzeichnis unter dem Scratchpad eingetragen
(`claude mcp add ... -s local`), nicht in der globalen Serverliste. `C:\Users\Student\.claude.json`
wurde vorher ausserhalb des Repositories gesichert; der Nachzustand steht in Abschnitt 9.

## 4. Schritt 2, der Werkzeugaufruf mit Inhalt

```
claude -p "Call the ncmcp tool files_list for the path / and then print, verbatim,
           the JSON the tool returned. Do nothing else."
  --strict-mcp-config --mcp-config mcp.json --allowedTools "mcp__ncmcp__files_list"
```

Die Antwort, gekuerzt, aber woertlich aus dem Werkzeug:

```json
{"path":"/","count":12,"items":[
 {"path":"/Documents","name":"Documents","kind":"folder","size":1108446,"id":"file:155"},
 {"path":"/mcp-share-04d2eb7d6d","name":"mcp-share-04d2eb7d6d","kind":"folder","size":80,"id":"file:161"},
 {"path":"/mcp-private-04d2eb7d6d.md","name":"mcp-private-04d2eb7d6d.md","kind":"file","size":76,"id":"file:163"},
 {"path":"/Readme.md","name":"Readme.md","kind":"file","size":43,"id":"file:88"}]}
```

Das ist `alice`s eigenes Files-Home samt der zwei Marker-Dateien des Berechtigungs-Fixtures
aus 05-03, also Inhalt und keine Werkzeugliste. Ein falsches Konto waere an diesen zwei
Namen sofort zu sehen, und genau das sagt das Drehbuch an dieser Stelle.

## 5. Schritt 3, Pausieren und Freigeben, in beiden Richtungen belegt

### 5.1 Am echten Client

| Zeit | Schalter | `claude mcp list` | Containerlog |
|------|----------|-------------------|--------------|
| 16:57:48Z | Zugang an | `ncmcp: ... (HTTP) - ✔ Connected` | `POST /mcp 200` (dreimal) |
| 16:58:00Z | `Pause access` gedrueckt, Seite sagt `MCP access is paused` | `ncmcp: ... (HTTP) - ! Needs authentication` | `POST /mcp 403 Forbidden` (zweimal) |
| 16:58:19Z | `Turn access back on` gedrueckt, Seite sagt `MCP access is on` | `ncmcp: ... (HTTP) - ✔ Connected` | `POST /mcp 200` (dreimal) |

Beide Schaltvorgaenge antworteten in **0,02 s**. Die Verbindung wurde dabei nicht neu
aufgebaut: es ist dieselbe `authorizations`-Zeile, dasselbe Token, und die Zeile blieb waehrend
der Pause auf der Seite stehen, weil nichts beendet wurde.

### 5.2 Am Draht, mit Token in der Hand

Der Client zeigt, dass ein Client die zwei Zustaende sieht. Was die Route antwortet und was
ein Werkzeug zurueckgibt, ist getrennt gemessen, mit einer eigenen Verbindung ueber
`scripts/oauth_flow_check.py:connect` und `tool_call`:

```
16:59:45Z connected as alice in 1.8s
16:59:45Z tool call, access on:        answered   {"path": "/", "count": 12, "items": [...]}
16:59:45Z POST /connections action=pause -> 200, the page states access paused
16:59:45Z tool call, access paused:    refused
16:59:45Z   POST /mcp -> 403, body: {"error": "access_disabled", "error_description":
            "MCP access is switched off for this Nextcloud account. The owner of the account
             can switch it back on on the connector's connections page, linked in ..."}
16:59:45Z POST /connections action=resume -> 200, the page states access on
16:59:45Z tool call, access on again:  answered   {"path": "/", "count": 12, "items": [...]}
```

Beide Richtungen mit Inhalt, und die Absage nennt ihren Grund. Der Werkzeugaufruf ist in allen
drei Faellen derselbe (`files_list` auf `/`), und die Antwort ist zweimal dieselbe
Zwoelferliste.

## 6. Schritt 4, der Widerruf und seine Wirkung

### 6.1 An der Zeile des echten Clients

```
17:01:20Z rows before: 2
17:01:20Z POST action=confirm -> 200 in 0.01s
17:01:20Z   names the app: True
17:01:20Z   says it loses access immediately: True
17:01:20Z POST action=disconnect -> 200 in 0.27s
17:01:20Z   page says 'Disconnected': True
17:01:20Z rows after: 1
17:01:31Z claude mcp list: ncmcp: ... (HTTP) - ! Needs authentication
```

Und der Draht in genau dieser einen Nachfrage des Clients:

```
INFO: - "POST /mcp HTTP/1.1" 401 Unauthorized
INFO: - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
INFO: - "POST /token HTTP/1.1" 400 Bad Request
```

Drei Dinge in einer Zeile Beleg: die Route weist ab, der Client liest die Discovery erneut,
und sein Auffrischversuch wird abgelehnt, weil das Refresh-Token mit der Verbindung gegangen
ist. Nicht vorhergesagt und darum hier festgehalten: der `POST /token 400` ist der schoenste
Teil des Belegs, weil er zeigt, dass der Widerruf nicht nur das Zugriffstoken trifft.

### 6.2 Am Draht, mit Token in der Hand

Dieselbe Strecke fuer die Verbindung, deren Token im Zugriff war:

```
16:59:45Z the page lists 3 connections of this account
16:59:45Z POST action=confirm -> 200
16:59:45Z   confirmation page carries 'loses access to your Nextcloud immediately': True
16:59:45Z   confirmation page carries 'Keep this connection': True
16:59:45Z POST action=disconnect -> 200, the page says 'Disconnected': True
16:59:45Z tool call, disconnected: refused
16:59:46Z   POST /mcp -> 401, WWW-Authenticate: Bearer error="invalid_token",
            error_description="Authentication required", scope="nextcloud",
            resource_metadata="http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"
```

Der Widerruf wirkt sofort und die Absage traegt den Zeiger, mit dem ein Client sich neu
verbinden kann. Der Unterschied zur Pause ist am Statuscode ablesbar: `403` mit Grund gegen
`401` mit Zeiger.

## 7. Schritt 5, der ganze Werkzeugsatz

Fuenfzehn Zeilen `OK` in der Abnahmematrix, darunter `files_upload`, `files_read`,
`calendar_create_event`, `notes_create`, `deck_create_card`, `unified_search`, `search`,
`fetch`. Kein Werkzeug loescht, keines verschiebt, keines teilt frei. Die Zaehlzeile des
Skripts steht in Abschnitt 8.3.

## 8. Was am Drehbuch nicht gestimmt hat

Vier Punkte. Alle vier sind in `docs/conference-demo.md` behoben; die Fassung des Commits
`5b9271a` ist die gefahrene, der Nachfolge-Commit ist die korrigierte.

### 8.1 Die Probe der Station 3 und 4 kann nicht die Frage aus Schritt 2 sein

Das Drehbuch verlangte "dasselbe Kommando wie in Schritt 2, unveraendert" nach dem Pausieren
und nach dem Freigeben. Gemessen:

| Zeit | Zustand | `claude -p` mit derselben Frage |
|------|---------|-------------------------------|
| 16:53:34Z | Zugang an | Inhalt, zwoelf Eintraege |
| 16:54:37Z | pausiert | Absage: "Der MCP-Server ncmcp ist in dieser Session nicht authentifiziert" |
| 16:55:10Z | freigegeben | **weiter Absage**, und im Containerlog kein einziger `POST /mcp` |
| 16:56:23Z | freigegeben, nach einem `claude mcp list` mit `200` | weiter Absage |
| 16:57:08Z | freigegeben, ohne `--strict-mcp-config --mcp-config` | weiter Absage |

Der Connector war zu diesem Zeitpunkt erreichbar: `claude mcp list` meldete um 16:55:30Z
`✔ Connected` und das Log traegt `POST /mcp 200`. Der Client haelt also nach einem `403` einen
eigenen Vermerk, und der nicht interaktive Weg fragt danach nicht mehr nach. Das ist eine
Eigenschaft des Clients und keine des Connectors, aber ein Drehbuch, das darauf baut, faellt
auf der Buehne aus.

**Korrektur im Drehbuch:** die Probe der Stationen 3 und 4 ist `claude mcp list`, weil sie den
Server neu anfragt und in beiden Richtungen sofort umschlaegt (`✔ Connected` gegen
`! Needs authentication`, `200` gegen `403`). Die Begruendung steht als eigener Absatz im
Schritt, damit niemand die scheinbar naheliegende Variante zurueckbaut, und die
Rueckfalltabelle hat eine Zeile dafuer bekommen. Der Beleg mit Inhalt in beiden Richtungen
steht in Abschnitt 5.2 und ist am Draht gefuehrt, nicht am Gedaechtnis eines Clients.

### 8.2 Die Zahl der Werkzeuge war im Drehbuch zweimal verschieden

Schritt 0 druckt `tools=16`, Schritt 5 behauptete "fuenfzehn". Beides stand im Drehbuch, ohne
ein Wort dazu, und auf einer Buehne ist das ein Widerspruch, den ein Zuhoerer findet.
Gemessen: der Server veroeffentlicht **16** Werkzeuge (`scripts/check_tool_budget.py`:
`tools/list: 11268 bytes, 16 tools, budget 12500`), und `scripts/acceptance_all_tools.py`
ruft **15** davon auf; das sechzehnte ist `prepare_context`, das das Skript nicht aufruft.

**Korrektur im Drehbuch:** Schritt 0 nennt `tools=16` und verweist auf Schritt 5, Schritt 5
sagt "sechzehn Werkzeuge" und dazu, dass fuenfzehn davon aufgerufen werden.

### 8.3 Die Erfolgszeile von Schritt 5 gibt es nicht

Das Drehbuch versprach als Abschluss `OK: all 15 tools answered over stdio.` Gemessen:

```
FAIL    tools/list             expected 15 tools, got 16
FAIL: 1 tools failed: tools/list
```

Rueckgabewert `1`, waehrend jede der fuenfzehn aufgerufenen Zeilen `OK` traegt. Die Ursache
ist die Konstante `EXPECTED_TOOLS = 15` aus Phase 1, nicht der Connector.

**Korrektur im Drehbuch:** Schritt 5 sagt, dass die Matrix die Station ist und nicht die
Schlusszeile, und nennt die Ursache in einem Satz, damit sie auf der Buehne kein Schreck ist.
Die Zeile selbst wird in diesem Plan nicht geaendert: ein Abnahmeskript aus Phase 1 verdient
keinen Nebenbei-Eingriff aus einem Doku-Plan. Sie steht in
`.planning/phases/06-h-rtung-eigennachweise-und-conference-reife/deferred-items.md`.

### 8.4 Die Zeitangaben waren geraten

Das Drehbuch behauptete zusammen 142 s Maschinenzeit, gemessen wurden 82 s. Vier der sechs
Angaben lagen daneben, Schritt 0 um den Faktor vier zu hoch und Schritt 2 um die Haelfte zu
niedrig.

**Korrektur im Drehbuch:** jede Angabe steht jetzt auf ihrer Messung, und die Summe der
Maschinen-Angaben (82 s) ist die aus Abschnitt 1. Nicht gekuerzt wurde das Drehbuch: die
Buehnenzeit von 4:40 fuer sechs Schritte bleibt im Rahmen eines Fuenf-Minuten-Formats.

### Was gestimmt hat

Der Rest lief wie geschrieben, ohne Nachdenken und ohne Nachschlagen: der Einmal-Aufbau, die
Kopier-Kommandos der Schritte 0, 1, 2 und 5, alle Klickwege der Seite, jede Erwartung ausser
den vier oben, die Vorher-Checkliste (alle drei kritischen Punkte waren pruefbar wie
beschrieben) und beide Adressen fuer den Browser.

## 9. Nachzustand, belegt

| Was | Wert | Beleg |
|-----|------|-------|
| App | `mcp_connector (MCP Connector): 0.1.2 [enabled]` | `occ app_api:app:list` |
| Die drei OAuth-Schalter | Ausgangszustand | `occ app_api:app:config:list mcp_connector` nennt genau `oauth_data_key` und `public_url`; im Container keine `NC_MCP_OAUTH_*`-Variable; das AS-Dokument traegt wieder `registration_endpoint` und `client_id_metadata_document_supported: true` |
| Zugangsschalter | nicht pausiert | `user_access` 0 Zeilen; die Seite des Demo-Kontos sagt `MCP access is on` |
| Die Verbindung der Demo | beendet, ueber die Seite und damit ueber den Widerruf-Weg des Produkts, nicht per Datenbankeingriff | Seite sagt `No connected apps`, `connection rows: 0` |
| Store | `clients 2`, `flows 0`, `auth_codes 0`, `access_tokens 0`, `refresh_tokens 2`, `authorizations 2` (beide `jane`, beide nicht widerrufen) | Zaehlung im Container, identisch zum Vorzustand |
| Messrueckstand entfernt | vier `clients`-Zeilen und vier `authorizations`-Zeilen von `alice`, dazu die zugehoerigen Token und zwei nicht eingeloeste Codes | wie 06-08 und 06-09 mit ihren Messzeilen; `jane`s zwei Zeilen sind unberuehrt |
| `jane` | unberuehrt | kein `resetpassword`, kein Widerruf, keine ihrer zwei Verbindungen angefasst; ihre Seite wurde nie geoeffnet |
| Client-Konfiguration | globale Serverliste zeichengleich `['firecrawl-mcp', 'obsidian', 'stitch']`, `ncmcp` aus der Projektliste entfernt | Vergleich gegen die Sicherung von 16:52Z |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud`, je "Up 5 days" | `docker ps` |

Ein Rest bleibt und wird genannt statt beseitigt: `C:\Users\Student\.claude.json` traegt
weiterhin einen Projekteintrag fuer das Messverzeichnis, mit leerer Serverliste. Er wurde
nicht herausgeschnitten, weil diese Datei zur Laufzeit einer Sitzung geschrieben wird und ein
Eingriff von aussen einen gleichzeitigen Schreibvorgang des Owners ueberschreiben koennte. Der
Eintrag nennt einen Pfad im Scratchpad, kein Geheimnis und keinen Server.

## 10. Die Treiber dieses Laufs

Vier Skripte, alle im Scratchpad und keines im Repository, weil sie Messwerkzeug sind und der
Plan sie nicht als Liefergegenstand nennt (das Muster von 06-07 und 06-09):

| Datei | Was sie tut |
|-------|-------------|
| `tty_probe.py`, `tty_probe2.py` | die zwei Vorproben zur Konsolenfrage aus Abschnitt 3 |
| `step1_login.py` | Schritt 1: `claude mcp login` mit Konsolen-Handle, plus die zwei Knoepfe ueber `oauth_flow_check:sign_in` |
| `page.py` | die Verbindungsseite: lesen, pausieren, freigeben, bestaetigen, beenden, je mit dem Formular, das der jeweilige Knopf abschickt, samt der Faelschungssicherung, die die Seite gerendert hat |
| `wire_control.py` | Abschnitt 5.2 und 6.2: eine eigene Verbindung ueber `oauth_flow_check:connect`, Werkzeugaufrufe in allen vier Zustaenden, plus die rohe HTTP-Antwort der MCP-Route |

Was diese Treiber ersetzen, ist in jedem Fall ein Mensch an einem Knopf, nie ein Schenkel des
Protokolls: der Client baut jede seiner Anfragen selbst, und die Seite bekommt genau das
Formular, das ihr Knopf abschickt.
