# 13 Messprotokoll: der CIMD-Weg gegen den 0.1.9-Kandidaten

Datum des Laufs: **2026-08-25, 17:23 bis ... UTC**. Rechner: derselbe Entwicklungsrechner wie
in der Nachmessung vom 2026-08-20 (Windows-Host, Git Bash). Alles unten ist aus diesem Lauf,
nicht aus dem Quellcode abgeleitet; wo eine Aussage aus dem Programmtext des Clients oder aus
unserem Quellcode kommt, steht das dabei.

Gemessen wird der **0.1.9-Kandidat aus dem lokalen Registry**, also der Quellstand, der
getaggt wird, und **vor** dem Tag. Der Grund steht in der Roadmap: der Tag hängt an einer
Owner-Freigabe, die zeitlich offen ist, und ein Beweis hinter dieser Freigabe wäre von ihr
abhängig. Der Anlass ist der v1.1-Debt-Befund W-5: der letzte Live-Beleg der CIMD-Kette
stammt vom 2026-08-20 und lief gegen 0.1.2, also gegen eine Fassung vor den Review-Fixes
`a47bb57` (`may_fetch=False` weg von den heißen Pfaden) und `bd75cd8` (Allowlist VOR dem
Fetch). Diese Messung läuft gegen eine Fassung, die beide enthält.

Drei Konventionen für dieses Protokoll, übernommen aus dem Vorlauf 06-09:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen `compose.exapp.yml` verlangt
  `HP_SHARED_KEY` in der Umgebung (WR-11), und der messende Prozess hat mit diesem
  Schlüssel nichts zu tun. Wo compose unvermeidbar war, kam der Wert aus `.env.exapp` in die
  Umgebung des Aufrufs und ist nirgends aufgeschrieben.
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39). Kein
  Token, kein Autorisierungscode, keine `code_challenge`, kein `state`, kein App-Passwort.
  Wo eine Logzeile solche Werte trug, stehen sie als `<gekürzt>`.
* Die Version einer Instanz ist immer die Zeile aus `occ status`, nie ein Docker-Tag
  (Pitfall 6). Für den Connector ist die Pflichtangabe Version **und** Image-Digest.

Zur zweiten Konvention gehört eine Prüfung und eine Genauigkeit. Geprüft wurde mit einem
`grep -nE` über diese Datei, das die fünf verbotenen Namen jeweils **mit** einem folgenden Wert
sucht, also den Verifier, die Prüfsumme, einen Bearer-Kopf, einen `state` von mindestens acht
Zeichen und eine Passwort-Zuweisung: **kein Treffer**. Das Suchmuster steht hier absichtlich
nicht wörtlich, sonst fände es sich selbst.

Ein Grep nach den blossen Namen ohne Wert findet dagegen drei Zeilen: diese Konvention, die den
Namen nennen muss, um ihn zu verbieten, die gekürzte `/authorize`-Zeile in Abschnitt 2, und die
Tabellenzeile, die `code_challenge_method` als `S256` nennt. Ein Verfahrensname ist kein
Geheimnis. Verboten sind die Werte, und keiner steht hier.

## Topologie des Laufs

| Was | Wert |
|-----|------|
| Compose-Datei, Projekt | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | **34.0.3 (34.0.3.2)** laut `occ status`, `installed: true`, `maintenance: false` |
| Connector | `mcp_connector` **0.1.9 [enabled]** laut `occ app_api:app:list`; Image `127.0.0.1:5000/mcp_connector:0.1.9`, Digest `sha256:1183f8455c5f2ab420ee3d4b7eb8e0b2c207610c08dcd12b943ae78920759c47`, `RestartCount` 0, Health `healthy` |
| Beleg des Digests | `docker buildx imagetools inspect 127.0.0.1:5000/mcp_connector:0.1.9 --format '{{.Manifest.Digest}}'` und, unabhängig davon, die Zeile `image digest sha256:1183f845…: unchanged since the push` aus `scripts/bootstrap_exapp.sh` (`verify_image_digest` vergleicht das gerade Gepushte gegen das, was das Registry ausliefert) |
| `APP_VERSION` im Container | `APP_VERSION=0.1.9`, genau eine Zeile aus `docker inspect nc_app_mcp_connector --format '{{range .Config.Env}}{{println .}}{{end}}'` |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| **Gemessener Client** | **Claude Code 2.1.233** (`claude --version`), dieselbe Version wie im Vorlauf 06-09, also kein Client-Drift gegenüber dem letzten Beweis |
| Messkonto | `alice`, Fixture-Konto aus `scripts/bootstrap_exapp.sh`, nicht `jane` |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberührt (kein Kommando dieses Laufs nennt sie), `docker ps` meldet beide weiter "Up 10 days" |

**Wie die Topologie auf den Kandidaten gehoben wurde (17:24:22Z).** Zwei Schritte, und der
erste ist Pflicht:

```
occ app_api:app:unregister mcp_connector      # OHNE --rm-data
  -> ExApp mcp_connector successfully disabled.
  -> ExApp mcp_connector successfully removed
  -> ExApp mcp_connector successfully unregistered.
bash scripts/bootstrap_exapp.sh
  -> image 127.0.0.1:5000/mcp_connector:0.1.9: built and pushed (sha256:1183f845…)
  -> image digest sha256:1183f845…: unchanged since the push
  -> exapp mcp_connector: registered and deployed
  -> exapp mcp_connector: enabled
  -> ExApps: mcp_connector (MCP Connector): 0.1.9 [enabled]
```

Ohne den Vorschritt hätte die Messung den heutigen Mischstand gemessen: `ensure_exapp()`
prüft nur, ob die App-Id in `occ app_api:app:list` vorkommt, und meldet dann `registered`,
ohne das neue Image zu deployen (Pitfall 3). Vor dem Lauf meldete AppAPI `0.1.7 [enabled]`,
der Container lief auf `ghcr.io/street1983nk/mcp_connector:0.1.6`.

`--rm-data` blieb weg, damit Volume und Autorisierungen überleben. Die zwei Konfigurationswerte
(`oauth_data_key`, `public_url`) wurden vor dem Abmelden außerhalb des Repositories gesichert
und haben Ab- und Anmeldung überlebt; `occ app_api:app:config:list mcp_connector` nennt sie
danach unverändert (occ selbst gibt sie nur als `***REMOVED SENSITIVE VALUE***` aus, was der
Credential-Regel dieses Protokolls entgegenkommt).

**Ein blockierender Fund, festgehalten statt weggelassen:** der erste Aufruf von
`scripts/bootstrap_exapp.sh` brach nach fünf Minuten mit
`ERROR: Nextcloud is still not installed after five minutes.` ab, obwohl `occ status`
`installed: true` meldete. Die Ursache ist die Konvention 1 dieses Protokolls von der anderen
Seite: das Skript ruft `occ` über `docker compose exec` (`dc()` in Zeile 200), und ohne
`HP_SHARED_KEY` in der Umgebung schlägt jeder compose-Aufruf gegen `compose.exapp.yml` fehl,
also auch die Installationsprüfung. Mit dem Wert aus `.env.exapp` in der Umgebung des Aufrufs
lief das Skript durch. Die Fehlermeldung nennt die Ursache nicht, und ein Leser dieses
Protokolls soll die zehn Minuten nicht ein zweites Mal ausgeben.

---

## 1. Trägt das AS-Dokument des Kandidaten beide Felder? (17:31:58Z)

**Antwort: ja, beide.** Ohne beide wählt der Client den CIMD-Weg nicht, und ein Ausbleiben
wäre sonst als Eigenschaft des Clients fehlgedeutet worden. Der Rohbeleg:

```
curl -sS http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-authorization-server \
  | jq '{issuer, client_id_metadata_document_supported, token_endpoint_auth_methods_supported}'
```

```json
{
  "issuer": "http://127.0.0.1:8081/exapps/mcp_connector",
  "client_id_metadata_document_supported": true,
  "token_endpoint_auth_methods_supported": [
    "client_secret_post",
    "client_secret_basic",
    "none"
  ]
}
```

Das ist zeichengleich mit der Antwort, die derselbe Aufruf am 2026-08-20 gegen 0.1.2 gab:
`issuer` ohne Schrägstrich am Ende, das CIMD-Feld als `true`, und `none` unter den
Authentisierungsmethoden, weil ein Client dieser Art nach dem Entwurf öffentlich ist und kein
gemeinsames Geheimnis hat.

**Dass der Client genau dieses Feld liest, ist am Client belegbar** und im Vorlauf 06-09 aus
dem Programmtext von `claude.exe` gelesen worden
(`client_id_metadata_document_supported === !0` und `clientMetadataUrl`). Die Client-Version
ist unverändert 2.1.233, die Stelle also dieselbe.

---

## 2. Gefahren wurde Messweg A: der echte Client (17:44:32Z)

**Antwort: Messweg A, nicht der Fallback.** Das ist die stärkere Aussage, und sie ist die
einzige, die nicht nur die Serverseite belegt: der Client hat den CIMD-Weg selbst gewählt,
anhand des Feldes aus Abschnitt 1, und er hat seine `client_id` selbst gesetzt. Der HTTP-Treiber
des Fallbacks B hätte den Weg vorgegeben statt ihn wählen zu lassen; er wurde nicht gebaut.

Der Rohbeleg ist die `client_id` der Anfrage aus dem Containerlog, ohne die gekürzten Werte:

```
2026-08-25T17:44:34.758600969Z INFO:      - "GET /authorize?response_type=code&
  client_id=https%3A%2F%2Fclaude.ai%2Foauth%2Fclaude-code-client-metadata&
  code_challenge=<gekürzt>&code_challenge_method=S256&
  redirect_uri=http%3A%2F%2Flocalhost%3A41333%2Fcallback&state=<gekürzt>&
  scope=nextcloud+offline_access&
  resource=http%3A%2F%2F127.0.0.1%3A8081%2Fexapps%2Fmcp_connector%2Fmcp HTTP/1.1" 302 Found
```

Was an dieser Zeile die Behauptung trägt:

| Feld | Wert |
|------|------|
| `client_id` | `https://claude.ai/oauth/claude-code-client-metadata`, prozentkodiert, also eine Adresse und **kein Zufallsstring** und keine vergebene Id |
| `redirect_uri` | `http://localhost:41333/callback`, also **mit** Port |
| `code_challenge_method` | `S256` |
| `scope` | `nextcloud offline_access` |
| `resource` | `http://127.0.0.1:8081/exapps/mcp_connector/mcp` |
| Antwort | `302 Found` auf `/authorize/consent` |

Der Port wurde **gelesen und nicht angenommen** (Pitfall 4): `MCP_OAUTH_CALLBACK_PORT` war
nicht gesetzt, der Client wählte 41333 frei, und die zwei abgebrochenen Vorläufe dieses
Nachmittags wählten 42623 und 43988. Drei Läufe, drei Ports, alle im Windows-Fenster 39152
bis 49151. Der Treiber liest den Port aus der Adresse, die der Client ausgibt.

---

## 3. Der Rundlauf (17:33:43 bis 17:46:33Z)

### 3.1 Wie der Client angesprochen wurde, und was am Vorzustand geschützt wurde

Der MCP-Server wurde in einem **eigenen Projektverzeichnis** unter dem Scratchpad angelegt,
nicht in der globalen Serverliste des Owners:

```
claude mcp add --transport http ncmcp http://127.0.0.1:8081/exapps/mcp_connector/mcp -s local
-> Added HTTP MCP server ncmcp with URL: ... to local config
   File modified: C:\Users\Student\.claude.json [project: ...\scratchpad\cimd-run]
```

`-s local` schreibt unter `projects[<dieses Verzeichnis>].mcpServers` und lässt die drei
globalen Server des Owners (`firecrawl-mcp`, `obsidian`, `stitch`) und die
claude.ai-Connectoren unberührt. Vor der ersten Änderung wurde
`C:\Users\Student\.claude.json` außerhalb des Repositories gesichert. Nachzustand um
17:49:45Z, nach `claude mcp logout ncmcp` und `claude mcp remove ncmcp -s local`: die
globale Liste nennt weiter genau `firecrawl-mcp`, `obsidian`, `stitch`, und das
Scratchpad-Projekt hat keinen Server mehr.

**`claude mcp login` verlangt ein Terminal**, sonst endet es mit
`stdin isn't a terminal, so authentication can't be completed here`. Gemessen wurde deshalb
über eine **Pseudo-Konsole** (`CreatePseudoConsole`, Windows-Bordmittel, per `ctypes`
angesprochen), nicht über ein installiertes Paket: kein `uv add`, kein `pip install`, kein
`npm install`, und `uv.lock` und der Dependency-Block von `pyproject.toml` sind unangetastet.
Die zwei Treiberskripte liegen im Scratchpad und nicht im Repository, weil sie Messwerkzeug
sind.

**Ein Fund, den das Vorbild 06-09 nicht nennt und der eine halbe Stunde gekostet hat.** Eine
Pseudo-Konsole allein genügt nicht. Nach `CreatePseudoConsole` plus
`PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE` hing das Kind sichtbar an der Pseudo-Konsole (deren
Titel trug den Kindnamen), schrieb aber weiter auf die Standard-Handles des messenden
Prozesses und fragte diese nach einem Terminal, also wieder eine Pipe. Der Microsoft-Beispielcode
kommt ohne die fehlende Zeile aus, weil sein Elternprozess selbst eine Konsolenanwendung ist.
Die Zeile ist `STARTF_USESTDHANDLES` mit den drei alten Konsolen-Handle-Werten `0x3`, `0x7`
und `0xB`: dann liest das Kind seine eigene Konsole, und die ist ein Terminal. Danach kam die
Zeile `Or paste the redirect URL here:` aus dem Client, und das ist der Beleg, dass er den
Prozess für interaktiv hält.

Der Browser-Schenkel ist automatisiert, und zwar so, wie dieses Projekt ihn schon
automatisiert: `scripts/oauth_flow_check.py:sign_in` meldet `alice` über den Login Flow v2 an
und drückt "Grant access". Eine eigene Nextcloud-Login-Automatisierung wurde nicht gebaut, ein
Gate verbietet dasselbe unter `src/`. Der Client baut seine Anfrage selbst, hält seinen eigenen
Loopback-Port, tauscht den Code selbst ein und ruft das Werkzeug selbst auf.

Ein zweiter kleiner Fund derselben Art: die Adresse steht in der Ausgabe des Clients zweimal,
als Id und als sichtbarer Text eines OSC-8-Hyperlinks, und die Escape-Folge dahinter ist eine
Cursor-Bewegung. Wer die Escapes erst entfernt und dann die Adresse sucht, klebt das nächste
Wort an den letzten Query-Parameter: aus `resource=...%2Fmcp` wurde einmal
`resource=...%2FmcpWaiting`. Gelesen wird deshalb aus den Rohbytes, mit einem Muster, das an
der Escape-Folge endet.

### 3.2 Der 401 der MCP-Route und der Zeiger (17:33:53Z)

Diese drei Zeilen entstanden aus einem `claude mcp list`, also aus dem ersten Kontaktversuch
des Clients:

```
2026-08-25T17:33:53.339914669Z INFO:      - "POST /mcp HTTP/1.1" 401 Unauthorized
2026-08-25T17:33:53.347293984Z INFO:      - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-25T17:33:53.362944568Z INFO:      - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
```

`claude mcp list` meldete danach `ncmcp: http://127.0.0.1:8081/exapps/mcp_connector/mcp
(HTTP) - ! Needs authentication`.

### 3.3 Die Discovery-Kette des Rundlaufs (17:44:33Z)

```
2026-08-25T17:44:33.674316092Z INFO:      - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-25T17:44:33.683927792Z INFO:      - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
2026-08-25T17:44:33.699947816Z INFO:      - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-25T17:44:33.714192009Z INFO:      - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
```

Jedes der beiden Dokumente wird zweimal geholt, unverändert gegenüber dem Vorlauf. Das ist
kein Fehler unserer Seite.

### 3.4 Kein `POST /register` im Messfenster

**Antwort: keiner, und zwar keiner im ganzen Leben dieses Containers.** Ohne diesen Beleg wäre
"ohne Registrierung" behauptet und nicht gemessen (Pitfall 2). Gelesen wurde das Containerlog
mit Zeitstempeln:

```
docker logs nc_app_mcp_connector -t | grep -c 'POST /register'
-> 0
```

Das Zeitfenster dieses Zählers beginnt mit dem Start des 0.1.9-Containers um
2026-08-25T17:31:34Z und reicht bis zum Ende des Rundlaufs, umfasst also den ersten
Kontaktversuch um 17:33:53Z, den Rundlauf um 17:44:32 bis 17:44:39Z und den Werkzeugaufruf um
17:45:20 bis 17:45:32Z. Dieselbe Filterung über das Fenster ab 17:44:30Z zeigt zehn Zeilen,
und keine davon ist `/register`:

```
docker logs nc_app_mcp_connector -t | grep -v heartbeat | awk '$1 >= "2026-08-25T17:44:30"' | grep 'INFO: '
-> GET /.well-known/oauth-protected-resource/mcp 200
   GET /.well-known/oauth-authorization-server 200
   GET /.well-known/oauth-protected-resource/mcp 200
   GET /.well-known/oauth-authorization-server 200
   GET /authorize?...client_id=https%3A%2F%2Fclaude.ai%2F... 302 Found
   GET /authorize/consent?flow=<gekürzt>&step=wait 200 OK
   POST /authorize/decide 200 OK
   GET /.well-known/oauth-authorization-server 200
   GET /.well-known/oauth-protected-resource/mcp 200
   POST /token 200 OK
```

Der zweite Beleg derselben Aussage liegt in der Datenbank: von sechs Zeilen der Tabelle
`clients` trägt **keine einzige** einen `client_secret_hash`, und genau eine hat eine
`client_id`, die mit `https` beginnt. Eine Registrierungszeile hätte gesetzte Frischespalten
nicht, diese hat sie (Abschnitt 3.5).

### 3.5 Der ausgehende Abruf und die geschriebene `clients`-Zeile

Der Abruf selbst hinterlässt im Containerlog **keine** Zeile: `oauth/cimd.py` protokolliert
nur Absagen, ein geglückter Abruf ist still (Pitfall 1). Belegt ist er deshalb zweifach.

**Beleg (a): die geschriebene Zeile, Feld für Feld aus `/nc_app_mcp_connector_data/oauth.sqlite3`**,
gelesen per `docker exec nc_app_mcp_connector python` mit `sqlite3`:

| Feld | Wert |
|------|------|
| `client_id` | `https://claude.ai/oauth/claude-code-client-metadata` |
| `client_secret_hash` | `None`, also **leer** |
| `allowed` | `1` |
| `registered_at` | `1787679616` = 2026-08-25T17:40:16Z |
| `last_used_at` | `1787679879` = 2026-08-25T17:44:39Z |
| `cimd_fetched_at` | `1787679616` = 2026-08-25T17:40:16Z |
| `cimd_expires_at` | `1787679916` = 2026-08-25T17:45:16Z |
| Frischefenster | **300 Sekunden** |
| `metadata_json.redirect_uris` | `["http://localhost/callback", "http://127.0.0.1/callback"]`, also **die zwei portlosen** |
| `metadata_json.token_endpoint_auth_method` | `none` |
| `metadata_json.client_name` | `Claude Code` |
| `metadata_json.grant_types` | `["authorization_code", "refresh_token"]` |
| `metadata_json.logo_uri` | `None`, und das ist Absicht: `validate_document` liest das Feld nicht |

Das Fenster von 300 Sekunden kommt aus dem `Cache-Control` der Antwort (`max-age=300`) und
wird auf 300 bis 3600 Sekunden gekappt (`CACHE_MIN_SECONDS`, `CACHE_MAX_SECONDS`).

**Ein Detail, das nicht verschwiegen wird:** `cimd_fetched_at` steht auf 17:40:16Z und nicht
auf 17:44:34Z. Um 17:40 lief der erste, an der OSC-8-Falle gescheiterte Versuch dieses
Nachmittags, und der erste `/authorize` dieses Versuchs hat den Abruf ausgelöst. Um 17:44:34Z
war die Zeile noch frisch (Ablauf 17:45:16Z), und der Code hat sie benutzt statt neu
abzurufen: `/authorize` antwortete in 0,208 s statt in den 0,9 s eines Laufs mit Abruf. Das
ist genau der Zweck der zwei Frischespalten, und es ist der Grund, warum die Positivkontrolle
des Socket-Zählers in Abschnitt 4 mit einer abgelaufenen Zeile fahren muss.

**Beleg (b): derselbe Abruf, im laufenden Container aus dem Prozess selbst ausgeführt**
(`docker exec nc_app_mcp_connector python`, 17:48Z):

```
fetch_document_and_lifetime -> lifetime 300s, 0.205s
document           : {"client_id": "https://claude.ai/oauth/claude-code-client-metadata",
                      "client_name": "Claude Code", "client_uri": "https://claude.ai",
                      "grant_types": ["authorization_code", "refresh_token"],
                      "redirect_uris": ["http://localhost/callback", "http://127.0.0.1/callback"],
                      "response_types": ["code"], "token_endpoint_auth_method": "none"}
plain GET          -> HTTP 200, 317 bytes, 0.185s, cache-control 'public, max-age=300'
limits in force    : MAX_DOCUMENT_BYTES=5120, timeout=5.0s, cache 300..3600s
resolved addresses : ['160.79.104.10', '2607:6bc0::10']
```

317 Bytes, dieselbe Größe wie am 2026-08-20, und beide aufgelösten Adressen sind öffentlich,
sonst hätte `resolve_addresses` den ganzen Namen verworfen.

### 3.6 Die Zustimmungsseite (17:44:36Z)

`GET /authorize/consent?flow=<gekürzt>&step=wait` antwortete **200**. Aus der Definitionsliste
der Seite:

| Begriff | Wert |
|---------|------|
| App name | `Claude Code` |
| Sends you back to | `http://localhost:41333/callback` |
| Client ID | `https://claude.ai/oauth/claude-code-client-metadata` |
| **Client ID host** | **`claude.ai`** |

Die Seite nennt den Hostnamen der `client_id` als eigene Zeile, und sie nennt das angemeldete
Konto (`alice` steht im Seitentext). `POST /authorize/decide` aus dem Browser, der die
Anmeldung gerade abgeschlossen hat: **200**. Die Rückseite navigiert auf
`http://localhost:41333/callback` mit einem `code`, mit dem `state` der Anfrage und mit
`iss=http://127.0.0.1:8081/exapps/mcp_connector`.

### 3.7 Der Code-Tausch (17:44:39Z)

Der Sprung auf die Rückadresse wurde ausgeführt, wie ein Browser ihn ausführt. **Der Client
hat auf seinem eigenen Port gelauscht und 200 geantwortet** (`callback_status: 200` im
Treiberprotokoll), der Einfüge-Weg wurde nicht gebraucht. Danach:

```
2026-08-25T17:44:36.904728622Z INFO:      - "GET /authorize/consent?flow=<gekürzt>&step=wait HTTP/1.1" 200 OK
2026-08-25T17:44:36.959138886Z INFO:      - "POST /authorize/decide HTTP/1.1" 200 OK
2026-08-25T17:44:39.124414890Z INFO:      - "POST /token HTTP/1.1" 200 OK
```

Der Client schrieb danach

```
Authenticated with "ncmcp". Its tools are now available in Claude Code.
```

und beendete sich mit Rückgabewert **0**. Vom `/authorize` bis zum beendeten
`claude mcp login`: 4,4 Sekunden.

### 3.8 Der Werkzeugaufruf, mit Inhalt (17:45:20 bis 17:45:32Z)

```
claude -p "Call the ncmcp tool files_list for the path / and then print, verbatim,
           the JSON the tool returned. Do nothing else."
  --strict-mcp-config --mcp-config mcp.json --allowedTools "mcp__ncmcp__files_list"
```

Die Antwort, gekürzt auf die Einträge, auf die es ankommt, aber wörtlich aus dem Werkzeug:

```json
{"path":"/","count":73,"items":[
 {"path":"/Documents","name":"Documents","kind":"folder","size":1108446,"modified":"Thu, 20 Aug 2026 04:44:24 GMT","id":"file:155"},
 {"path":"/mcp-share-04d2eb7d6d","name":"mcp-share-04d2eb7d6d","kind":"folder","size":80,"modified":"Thu, 20 Aug 2026 04:44:24 GMT","id":"file:161"},
 {"path":"/mcp-private-04d2eb7d6d.md","name":"mcp-private-04d2eb7d6d.md","kind":"file","size":76,"content_type":"text/markdown","modified":"Thu, 20 Aug 2026 04:44:25 GMT","id":"file:163"},
 {"path":"/Readme.md","name":"Readme.md","kind":"file","size":43,"content_type":"text/markdown","modified":"Tue, 25 Aug 2026 17:30:41 GMT","id":"file:88"}]}
```

Das ist `alice`s eigenes Files-Home, samt der zwei Marker-Dateien aus dem
Berechtigungs-Fixture (`mcp-private-…` und `mcp-share-…`), also **Inhalt** und keine
Werkzeugliste. Im Containerlog:

```
2026-08-25T17:45:20.528621407Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
2026-08-25T17:45:20.707596586Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
2026-08-25T17:45:21.026862712Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
2026-08-25T17:45:21.057457196Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
2026-08-25T17:45:21.064714542Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
2026-08-25T17:45:32.468347025Z INFO:      - "POST /mcp HTTP/1.1" 200 OK
```

**EXAPP-08 hat damit seinen Live-Beleg gegen den 0.1.9-Kandidaten:** ein Client, der sich
ausschließlich über die Adresse seines eigenen Metadatendokuments ausweist, verbindet sich
und ruft ein Werkzeug mit Inhalt auf. Gemessen wurde eine Fassung nach `a47bb57` und
`bd75cd8`, damit ist der v1.1-Debt-Befund W-5 geschlossen.

### 3.9 Die Verbindung dieses Laufs ist beendet (17:49:45Z)

`claude mcp logout ncmcp` ruft `/revoke`, und das ist der Weg, den der Plan verlangt:

```
2026-08-25T17:49:46.442741069Z INFO:      - "POST /revoke HTTP/1.1" 200 OK
2026-08-25T17:49:46.458865666Z INFO:      - "POST /revoke HTTP/1.1" 200 OK
```

Zweimal, einmal für das Zugriffs- und einmal für das Erneuerungs-Token. Die Zeile in
`authorizations` trägt danach `revoked_at` = 2026-08-25T17:49:46Z.

`occ mcp_connector:purge --force` wurde **nicht** gefahren, und das ist eine Entscheidung und
kein Versäumnis: dieses Kommando beendet jede Verbindung der Instanz, und die Instanz hält
zwei lebende Verbindungen des Kontos `jane` vom 2026-08-20 (die Demo-Substanz für CONF-01).
Nach dem Lauf stehen sie unverändert da, `revoked_at` beider Zeilen ist weiterhin leer. Der
Plan verlangt beides, `/revoke` oder `purge` und fremden Zustand unberührt; auf dieser Instanz
erfüllt nur `/revoke` beide Hälften.

---

## 4. Die Gegenprobe: Schalter aus, und kein Paket geht nach außen

Ohne diese Gegenprobe würde Abschnitt 3 nur belegen, dass etwas durchgeht, nicht dass die
Grenze hält. Gefahren wurde genau eine, die des Schalters `NC_MCP_OAUTH_CIMD`, und sie ist
danach zurückgenommen.

**Wie ein ausgehender Request gezählt wurde.** Nicht abgeschaltet, sondern gezählt: ein Skript
im Container liest `/proc/net/tcp` und `/proc/net/tcp6` in einer Schleife (12 Sekunden lang)
und sammelt jeden Socket mit Gegenport 443, mit dem Zustand und der Zahl der Abfragen, in
denen er stand. **Dasselbe Skript im positiven und im negativen Lauf**, sonst vergleichen die
zwei Zahlen nichts. Der Zähler liegt im Scratchpad und wird per `docker cp` in den Container
gelegt; er ist Messwerkzeug und gehört nicht ins Repository.

### 4.1 Positivkontrolle, Schalter auf Werkseinstellung (17:59:29Z)

Zuerst wurde gewartet, bis das Frischefenster der `clients`-Zeile abgelaufen war (Ablauf
17:59:22Z), denn eine frische Zeile hätte den Abruf gar nicht ausgelöst und die
Positivkontrolle wäre eine Null gegen eine Null geworden. Dann derselbe `/authorize` wie im
Rundlauf, mit derselben Dokumentadresse als `client_id`:

```
{"label": "positive-control", "status": 302, "seconds": 0.344,
 "cache_control": "no-store", "location_path": "/exapps/mcp_connector/authorize/consent",
 "as_cimd_field_present": true, "as_cimd_field_value": true,
 "as_registration_endpoint_present": true}
```

Und der Zähler:

```
polls=20051 over 12.0s
sockets to port 443 seen: 5
  remote=0A684FA0:01BB state=01 seen_in_258_polls   (ESTABLISHED)
  remote=0A684FA0:01BB state=02 seen_in_21_polls    (SYN_SENT)
  remote=0A684FA0:01BB state=04 seen_in_2_polls     (FIN_WAIT1)
  remote=0A684FA0:01BB state=05 seen_in_22_polls    (FIN_WAIT2)
  remote=0A684FA0:01BB state=06 seen_in_16248_polls (TIME_WAIT)
```

`0A684FA0` ist `160.79.104.10`, also eine der zwei Adressen, zu denen `claude.ai` in diesem
Container auflöst (Abschnitt 3.5). Der Zähler sieht den Abruf also, wenn er stattfindet, und
das ist die Bedingung, unter der eine Null etwas bedeutet.

### 4.2 Der Schalter wird abgeschaltet, über die Admin-Form (17:59:52Z)

Nicht über eine Neuregistrierung, denn `oauth_cimd` ist seit 0.1.3 einer der sechs
Admin-Werte (`exapp/config_values.py`, `CONFIG_KEYS`); der Vorlauf 06-09 musste noch ab- und
neu anmelden, weil der Schalter damals keiner war.

```
occ app_api:app:config:set mcp_connector oauth_cimd --value 0
  -> ExApp mcp_connector config oauth_cimd set to 0
occ app_api:app:disable mcp_connector    -> successfully disabled
occ app_api:app:enable  mcp_connector    -> successfully enabled
occ app_api:app:list                     -> mcp_connector (MCP Connector): 0.1.9 [enabled]
occ app_api:app:config:list mcp_connector -> oauth_cimd, oauth_data_key, public_url
docker inspect nc_app_mcp_connector --format '{{.State.Health.Status}} {{.RestartCount}}'
  -> healthy 0
```

Ab- und Anmelden ist Pflicht: die sechs Felder werden beim Prozessstart einmal gelesen.
`docker exec nc_app_mcp_connector printenv NC_MCP_OAUTH_CIMD` findet den Wert **nicht**, und
das ist richtig und kein Widerspruch: ein Admin-Wert kommt nicht in die Container-Umgebung,
sondern wird beim Start aus Nextcloud gelesen und im Prozess über das Deploy-Environment
gelegt. Wer den Schalter am `printenv` prüft, prüft die falsche Stelle.

### 4.3 Negativkontrolle, Schalter aus (18:00:18Z)

Dieselbe Anfrage, dasselbe Skript, dieselbe Dauer:

```
{"label": "cimd-off", "status": 400, "seconds": 0.065,
 "cache_control": "no-store",
 "page_title": "This link has expired - MCP Connector for Nextcloud",
 "as_cimd_field_present": false, "as_cimd_field_value": null,
 "as_registration_endpoint_present": true}
```

```
2026-08-25T18:00:18.999072482Z INFO:      - "GET /authorize?response_type=code&
  client_id=https%3A%2F%2Fclaude.ai%2Foauth%2Fclaude-code-client-metadata&... HTTP/1.1" 400 Bad Request
```

Und der Zähler:

```
polls=20543 over 12.0s
sockets to port 443 seen: 0
```

Vier Aussagen stehen damit belegt:

| Behauptung | Beleg |
|------------|-------|
| Die Dokumentadresse wird abgelehnt | `400`, Seite `This link has expired`, dieselbe Seite, die eine unbekannte oder lange vergangene Registrierung sieht |
| Kein Paket geht nach außen | **0** Sockets mit Gegenport 443 gegen **5** in der Positivkontrolle, gleiches Skript, gleiche 12 Sekunden |
| Das AS-Dokument bewirbt die Fähigkeit nicht mehr | `client_id_metadata_document_supported` fehlt im Dokument |
| Der Schalter nimmt die Registrierung nicht mit | `registration_endpoint` steht weiter im Dokument |

Die Antwortzeiten sagen dasselbe noch einmal: 0,344 s mit Abruf, 0,065 s ohne. Die Absage
fällt, bevor irgendein Socket geöffnet wird, weil `provider._resolve_cimd` den Schalter fragt,
bevor die Form der Kennung geprüft wird.

### 4.4 Der Ausgangszustand ist wiederhergestellt (18:00:39 bis 18:00:48Z)

```
occ app_api:app:config:delete mcp_connector oauth_cimd -> config oauth_cimd deleted
occ app_api:app:disable mcp_connector                  -> successfully disabled
occ app_api:app:enable  mcp_connector                  -> successfully enabled
occ app_api:app:config:list mcp_connector              -> oauth_data_key, public_url
occ app_api:app:list                                   -> mcp_connector (MCP Connector): 0.1.9 [enabled]
curl -sS .../.well-known/oauth-authorization-server | jq -r .client_id_metadata_document_supported
  -> true
docker inspect nc_app_mcp_connector --format '{{.Config.Image}} {{.RestartCount}} {{.State.Health.Status}}'
  -> 127.0.0.1:5000/mcp_connector:0.1.9 0 healthy
```

`config:list` nennt genau die zwei Schlüssel, die vor dem Lauf dastanden, und das AS-Dokument
bewirbt die Fähigkeit wieder. Eine Messung, die den Schalter umgelegt liegen lässt, verändert
die Instanz hinter dem Rücken des nächsten Plans.

`docker ps` meldet `nc-mcp-test` und `findling-nextcloud` weiter als "Up 10 days"; kein
Kommando dieses Laufs nennt sie, und `compose.test.yml` wurde nicht angefasst.

---

## 5. Was in der Doku bleibt

Das Rohprotokoll hier verschwindet mit dem Phasenverzeichnis. Was bleiben muss, steht in
`docs/oauth-setup.md`, Kapitel "Client ID Metadata Documents": eine datierte Zeile mit
Client-Version, gemessener Fassung und Digest, die jede der fünf Behauptungen einzeln nennt
(Identifikation über die Dokumentadresse, kein `/register`, Consent nennt den Host, Token 200,
echter Werkzeuginhalt), plus ein Aufzählungspunkt zur Gegenprobe mit beiden Socket-Zahlen. Der
Absatz von 2026-08-20 bleibt daneben stehen, seine 0.1.3-Aussage ist weiter wahr.

Im selben Zug sind vier tote Verweise geschlossen. Die Datei nannte an vier Stellen Pfade unter
`.planning/`, drei davon auf Messprotokolle in Verzeichnissen, die Commit `02dd6e1` entfernt
hat. Jede dieser Stellen trägt jetzt die Aussage selbst, mit Datum und Ergebnis im Satz.
`grep -n '\.planning' docs/oauth-setup.md` gibt danach keine Zeile aus, und derselbe tote Link
kann beim Abschluss von v1.3 nicht ein zweites Mal entstehen.
