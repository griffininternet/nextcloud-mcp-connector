# 06-09 Messprotokoll: Claude Code per Metadatendokument, und die Loopback-Portfrage

Datum des Laufs: **2026-08-20, 15:48 bis 16:12 UTC** (Abschnitte 1 bis 6). Rechner: der
Entwicklungsrechner aus 06-RESEARCH.md, Abschnitt "Environment Availability" (Windows-Host,
Git Bash). Alles unten ist aus einem Lauf, nicht aus dem Quellcode abgeleitet; wo eine
Aussage aus dem Programmtext des Clients oder aus unserem Quellcode kommt, steht das dabei.

Drei Konventionen für dieses Protokoll, übernommen aus 06-07 und 06-08:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen `compose.exapp.yml` verlangt
  `HP_SHARED_KEY` in der Umgebung (WR-11), und der messende Prozess hat mit diesem
  Schlüssel nichts zu tun.
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39). Kein
  Token, kein Autorisierungscode, kein `code_challenge`, kein `state`, kein App-Passwort.
  Wo eine Logzeile solche Werte trug, stehen sie als `<gekürzt>`.
* Die Version einer Instanz ist immer die Zeile aus `occ status`, nie ein Docker-Tag
  (Pitfall 6). Für den Connector ist die Pflichtangabe Version **und** Image-Digest.

## Topologie des Laufs

| Was | Wert |
|-----|------|
| Compose-Datei, Projekt | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | **34.0.3 (34.0.3.2)** laut `occ status`, `installed: true`, `maintenance: false` |
| Connector | `mcp_connector` **0.1.2 [enabled]** laut `occ app_api:app:list`; Image `127.0.0.1:5000/mcp_connector:0.1.2`, Digest `sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed`, `RestartCount` 0 |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| **Gemessener Client** | **Claude Code 2.1.233** (`claude --version`), `C:\Users\Student\.local\bin\claude.exe` |
| Messkonto | `alice`, Fixture-Konto aus `scripts/bootstrap_exapp.sh` |
| Demo-Substanz | Nutzer `jane` (Jane Fischer) und ihre zwei Verbindungen, **nicht angefasst** |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberührt (kein Kommando dieses Laufs nennt sie), `docker ps` meldet beide "Up 5 days" |

Der Digest ist derselbe wie am Ende von 06-07 und 06-08, und der Container hat sich seither
nicht neu gestartet. Es läuft also der Arbeitsbaum mit CIMD und der Loopback-Portregel.

**Warum `alice` und nicht `jane`.** Dieselbe Begründung wie in 06-08: `jane`s Passwort steht
nirgends, und `occ user:resetpassword` würde die App-Passwörter ihrer zwei OAuth-Verbindungen
entwerten, also genau die Demo-Substanz für CONF-01. Der Rundlauf braucht ein Konto, das sich
anmelden kann, und `alice` ist dafür da.

---

## 1. Trägt das AS-Dokument der laufenden Instanz beide Felder? (15:48Z)

**Antwort: ja, beide.** Ohne beide wählt der Client den CIMD-Weg nicht, und ein Ausbleiben
wäre sonst als Eigenschaft des Clients fehlgedeutet worden. `GET
http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-authorization-server`, die zwei
Zeilen, auf die es ankommt, aus der Antwort:

```json
  "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
  "client_id_metadata_document_supported": true
```

Der Rest der Antwort ist unverändert gegenüber 06-07: `issuer`
`http://127.0.0.1:8081/exapps/mcp_connector` (ohne Schrägstrich am Ende),
`code_challenge_methods_supported` nur `S256`, `scopes_supported` `nextcloud` und
`offline_access`, `authorization_response_iss_parameter_supported: true`.

**Dass der Client genau diese zwei Felder liest, ist am Client belegbar.** Aus dem
Programmtext von `claude.exe` (also aus dem Client und nicht aus einem Lauf; die Datei ist ein
kompiliertes Bündel, die Stellen sind mit `grep -a` gelesen):

```js
let S = c?.client_id_metadata_document_supported === !0, v = e.clientMetadataUrl;
if (v && !YuS(v)) throw new V3r(`clientMetadataUrl must be a valid HTTPS URL with a non-root pathname, got: ${v}`);
if (S && v) f = { client_id: v }, await e.saveClientInformation?.(f);
else { ... dynamische Registrierung ... }
```

Das Feld entscheidet also wörtlich zwischen CIMD und dynamischer Registrierung, und die
Prüfung auf https plus nicht-leeren Pfad ist dieselbe, die `cimd.is_cimd_client_id` auf
unserer Seite härter stellt.

---

## 2. Welches Metadatendokument nennt Claude Code wirklich? (16:06:38Z)

**Antwort: `https://claude.ai/oauth/claude-code-client-metadata`, wörtlich.** Assumption A2
ist damit bestätigt und nicht angenommen. Der Rohbeleg ist die `client_id` der Anfrage aus
dem Containerlog der ExApp, hier ohne die gekürzten Werte:

```
2026-08-20T16:06:38.979681581Z INFO:      - "GET /authorize?response_type=code&
  client_id=https%3A%2F%2Fclaude.ai%2Foauth%2Fclaude-code-client-metadata&
  code_challenge=<gekürzt>&code_challenge_method=S256&
  redirect_uri=http%3A%2F%2Flocalhost%3A45157%2Fcallback&state=<gekürzt>&
  scope=nextcloud+offline_access&prompt=consent&
  resource=http%3A%2F%2F127.0.0.1%3A8081%2Fexapps%2Fmcp_connector%2Fmcp HTTP/1.1" 302 Found
```

Der Wert ist im Client eine Konstante mit einer Umgebungs-Ausnahme, ebenfalls aus dem
Programmtext:

```js
get clientMetadataUrl(){ let e=process.env.MCP_OAUTH_CLIENT_METADATA_URL;
  if(e) return At(this.serverName,`Using CIMD URL from env: ${e}`), e; return bpn }
bpn = "https://claude.ai/oauth/claude-code-client-metadata"
```

Und das Dokument selbst, am 2026-08-20 um 15:48Z abgerufen, 317 Bytes, `HTTP/1.1 200`,
`Content-Type: application/json`, `Cache-Control: public, max-age=300`:

```json
{"client_id":"https://claude.ai/oauth/claude-code-client-metadata","client_name":"Claude Code",
 "client_uri":"https://claude.ai","redirect_uris":["http://localhost/callback","http://127.0.0.1/callback"],
 "grant_types":["authorization_code","refresh_token"],"response_types":["code"],
 "token_endpoint_auth_method":"none"}
```

Beide Rückadressen sind **portlos**. Das ist die Zange, aus der CLIENT-05 besteht: registriert
ist eine Adresse ohne Port, und angefragt wird eine mit Port.

---

## 3. Der Rundlauf (16:06:34 bis 16:10:25Z)

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
claude.ai-Connectoren unberührt. Vor der ersten Änderung wurde `C:\Users\Student\.claude.json`
außerhalb des Repositories gesichert; der Nachzustand steht in Abschnitt 10.

Zwei Eigenheiten der Messumgebung, benannt statt versteckt (das Muster von 05-07):

* **`claude mcp login` verlangt ein Terminal.** Ohne eines endet der Lauf mit
  `Couldn't complete authentication for "ncmcp": stdin isn't a terminal`. Gemessen wurde
  deshalb über eine **Pseudo-Konsole** (`CreatePseudoConsole`, Windows-Bordmittel, per
  `ctypes` angesprochen), nicht über ein installiertes Paket: ein Paket-Install ist in dieser
  Phase ausgeschlossen (T-06-SC), und `winpty` aus Git Bash lehnt ab, solange sein eigenes
  `stdin` kein Terminal ist ("stdin is not a tty"). Die Treiberskripte liegen im Scratchpad
  und nicht im Repository, weil sie Messwerkzeug sind.
* **Der Browser-Schenkel ist automatisiert, und zwar so wie dieses Projekt ihn schon
  automatisiert:** `scripts/oauth_flow_check.py:sign_in` meldet `alice` über den Login Flow v2
  an und drückt "Approve access". Der Client baut seine Anfrage selbst, hält seinen eigenen
  Loopback-Port, tauscht den Code selbst ein und ruft das Werkzeug selbst auf. Was der Treiber
  tut, sind die zwei Knöpfe, die ein Mensch drückt, plus der Sprung des Browsers auf die
  Rückadresse. Nichts davon ist der Autorisierungs-Schenkel des Clients.

### 3.2 Der 401 der MCP-Route und der Zeiger

```
2026-08-20T15:50:56.016683666Z INFO:      - "POST /mcp HTTP/1.1" 401 Unauthorized
2026-08-20T15:50:56.033121056Z INFO:      - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T15:50:56.045937292Z INFO:      - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
```

Diese drei Zeilen entstanden aus einem `claude mcp list`, also aus dem ersten Kontaktversuch
des Clients. Der Zeiger im Kopf des 401, mit `curl` nachgelesen (16:12:10Z):

```
HTTP/1.1 401 Unauthorized
Cache-Control: no-store
Www-Authenticate: Bearer error="invalid_token", error_description="Authentication required",
  scope="nextcloud", resource_metadata="http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"
```

Und das Dokument, auf das er zeigt:

```json
{"resource":"http://127.0.0.1:8081/exapps/mcp_connector/mcp",
 "authorization_servers":["http://127.0.0.1:8081/exapps/mcp_connector"],
 "scopes_supported":["nextcloud"],"bearer_methods_supported":["header"],
 "resource_name":"Nextcloud MCP Connector"}
```

`claude mcp list` meldete danach `ncmcp: http://127.0.0.1:8081/exapps/mcp_connector/mcp
(HTTP) - ! Needs authentication`.

### 3.3 Die Discovery-Kette des Rundlaufs

```
2026-08-20T16:06:38.247683701Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T16:06:38.260801894Z INFO: - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
2026-08-20T16:06:38.280557995Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T16:06:38.303011893Z INFO: - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
```

Jedes der beiden Dokumente wird zweimal geholt. Das ist kein Fehler unserer Seite und steht
als Fund 6.4 unten.

### 3.4 Der `/authorize`-Request

Die Zeile steht wörtlich in Abschnitt 2. Was an ihr die Behauptung trägt:

| Feld | Wert |
|------|------|
| `client_id` | `https://claude.ai/oauth/claude-code-client-metadata`, also eine URL und keine vergebene Id |
| `redirect_uri` | `http://localhost:45157/callback`, also **mit** Port |
| `code_challenge_method` | `S256` |
| `scope` | `nextcloud offline_access` |
| `prompt` | `consent` |
| `resource` | `http://127.0.0.1:8081/exapps/mcp_connector/mcp` |
| Antwort | `302 Found` auf `/authorize/consent` |

### 3.5 Der ausgehende Abruf und die geschriebene `clients`-Zeile

Der Abruf selbst hinterlässt im Containerlog **keine** Zeile: `oauth/cimd.py` protokolliert
nur Absagen, ein geglückter Abruf ist still. Belegt ist er deshalb zweifach.

Erstens durch die Frische-Spalten der geschriebenen Zeile, die genau das Fenster tragen, das
der `Cache-Control`-Kopf der Antwort erlaubt (`max-age=300`, und `CACHE_MIN_SECONDS` ist
ebenfalls 300):

```
cimd_fetched_at : 1787241998  2026-08-20T16:06:38Z
cimd_expires_at : 1787242298  2026-08-20T16:11:38Z
```

Zweitens durch denselben Abruf, im laufenden Container aus dem Prozess selbst ausgeführt und
gemessen (`docker exec nc_app_mcp_connector python`, 16:11Z):

```
fetch_document_and_lifetime -> lifetime 300s, 0.639s
plain GET   -> HTTP 200, 317 bytes, 0.279s, cache-control 'public, max-age=300'
limits in force: MAX_DOCUMENT_BYTES=5120, timeout=5.0s, cache 300..3600s
resolved addresses of claude.ai: ['160.79.104.10', '2607:6bc0::10']
```

Beide aufgelösten Adressen sind öffentlich, sonst hätte `resolve_addresses` den ganzen Namen
verworfen (eine schlechte Adresse verwirft den Namen, T-06-02).

Die Zeile, die daraus entstand, Feld für Feld aus `oauth.sqlite3`:

| Feld | Wert |
|------|------|
| `client_id` | `https://claude.ai/oauth/claude-code-client-metadata` |
| `client_secret_hash` | `None`, also **leer** |
| `allowed` | `1` |
| `registered_at` | `1787241537` = 2026-08-20T15:58:57Z (der erste `/authorize` dieses Laufs) |
| `last_used_at` | `1787242004` = 2026-08-20T16:06:44Z |
| `cimd_fetched_at` | `1787241998` = 2026-08-20T16:06:38Z |
| `cimd_expires_at` | `1787242298` = 2026-08-20T16:11:38Z |
| `metadata_json.redirect_uris` | `["http://localhost/callback", "http://127.0.0.1/callback"]`, also **die zwei portlosen** |
| `metadata_json.token_endpoint_auth_method` | `none` |
| `metadata_json.client_name` | `Claude Code` |
| `metadata_json.grant_types` | `["authorization_code", "refresh_token"]` |
| `metadata_json.logo_uri` | `null`, und das ist Absicht: `validate_document` liest das Feld nicht (T-06-13) |

### 3.6 Die Zustimmungsseite

`GET /authorize/consent?flow=<gekürzt>&step=wait` antwortete `200`. Aus der
Definitionsliste der Seite, wörtlich:

```
App name        Claude Code
Sends you back to   http://localhost:45157/callback
Client ID       https://claude.ai/oauth/claude-code-client-metadata
Client ID host  claude.ai
```

Die Seite nennt also den **Hostnamen der `client_id`** als eigene Zeile, und sie zeigt die
Loopback-Warnung aus 06-06: `Comes back to this computer`. Der angemeldete Nutzer (`alice`)
steht ebenfalls auf der Seite.

`POST /authorize/decide` aus dem Browser, der die Anmeldung gerade abgeschlossen hat: `200`.
Die Rückseite navigiert auf `http://localhost:45157/callback` mit `code`, mit dem `state` der
Anfrage und mit `iss=http://127.0.0.1:8081/exapps/mcp_connector`.

### 3.7 Der Code-Tausch

Der Sprung auf die Rückadresse wurde ausgeführt, wie ein Browser ihn ausführt. **Der Client
hat auf seinem eigenen Port gelauscht und `200` geantwortet** (`callback_status = 200` im
Lauf 2, 3 und 4; im Lauf 1 hat zusätzlich der Einfüge-Weg gegriffen, siehe 6.2). Danach:

```
2026-08-20T16:06:42.397342353Z INFO: - "GET /authorize/consent?flow=<gekürzt>&step=wait HTTP/1.1" 200 OK
2026-08-20T16:06:42.478827581Z INFO: - "POST /authorize/decide HTTP/1.1" 200 OK
2026-08-20T16:06:44.683562117Z INFO: - "POST /token HTTP/1.1" 200 OK
```

Vom Sprung auf die Rückadresse bis zum beendeten `claude mcp login`: **2,7 Sekunden** (Läufe
2 bis 4: 2,765 / 2,693 / 2,716 s), `POST /token` selbst 2,2 s nach dem `decide`. Der Client
schrieb danach:

```
Authenticated with "ncmcp". Its tools are now available in Claude Code.
```

und beendete sich mit Rückgabewert `0`.

### 3.8 Der Werkzeugaufruf, mit Inhalt (16:10:10 bis 16:10:25Z)

```
claude -p "Call the ncmcp tool files_list for the path / and then print, verbatim,
           the JSON the tool returned. Do nothing else."
  --strict-mcp-config --mcp-config mcp.json --allowedTools "mcp__ncmcp__files_list"
```

Die Antwort, gekürzt auf die ersten Einträge, aber wörtlich aus dem Werkzeug:

```json
{"path":"/","count":11,"items":[
 {"path":"/Documents","name":"Documents","kind":"folder","size":1108446,"modified":"Thu, 20 Aug 2026 04:44:24 GMT","id":"file:155"},
 {"path":"/mcp-share-04d2eb7d6d","name":"mcp-share-04d2eb7d6d","kind":"folder","size":80,"modified":"Thu, 20 Aug 2026 04:44:24 GMT","id":"file:161"},
 {"path":"/mcp-private-04d2eb7d6d.md","name":"mcp-private-04d2eb7d6d.md","kind":"file","size":76,"content_type":"text/markdown","modified":"Thu, 20 Aug 2026 04:44:25 GMT","id":"file:163"},
 {"path":"/Readme.md","name":"Readme.md","kind":"file","size":43,"content_type":"text/markdown","modified":"Thu, 20 Aug 2026 14:19:49 GMT","id":"file:88"}]}
```

Das ist `alice`s eigenes Files-Home, samt der zwei Marker-Dateien aus dem
Berechtigungs-Fixture von 05-03 (`mcp-private-…` und `mcp-share-…`), also **Inhalt** und keine
Werkzeugliste. Im Containerlog:

```
2026-08-20T16:10:10.781047189Z INFO: - "POST /mcp HTTP/1.1" 200 OK
2026-08-20T16:10:10.986600312Z INFO: - "POST /mcp HTTP/1.1" 200 OK
2026-08-20T16:10:11.314979514Z INFO: - "POST /mcp HTTP/1.1" 200 OK
2026-08-20T16:10:11.377367908Z INFO: - "POST /mcp HTTP/1.1" 200 OK
2026-08-20T16:10:11.390537887Z INFO: - "POST /mcp HTTP/1.1" 200 OK
2026-08-20T16:10:25.716463511Z INFO: - "POST /mcp HTTP/1.1" 200 OK
```

**AUTH-08 hat damit seinen Live-Beleg:** ein Client, der sich ausschließlich über die URL
seines eigenen Metadatendokuments ausweist, verbindet sich und ruft ein Werkzeug mit Inhalt
auf.

---

## 4. Die Portspalte

Jeder Lauf begann mit einer **vollständig aufgegebenen** Verbindung: `claude mcp logout
ncmcp` ("Signed out of \"ncmcp\"") vor jedem `claude mcp login`, sodass der Port neu gewählt
wird und nichts aus dem Vorlauf weiterlebt. Der Port ist der, den die `redirect_uri` des
`/authorize`-Requests trägt, gelesen aus dem Containerlog **und** aus der Ausgabe des
Clients.

| Lauf | Uhrzeit (UTC) | Port | Wie er zustande kam | Ergebnis |
|------|---------------|------|---------------------|----------|
| 1 | 16:06:38 | **45157** | frei gewählt | `POST /token 200`, `Authenticated`, Rückgabewert 0 |
| 2 | 16:08:44 | **47608** | frei gewählt | `POST /token 200`, `Authenticated`, Rückgabewert 0 |
| 3 | 16:09:11 | **41977** | frei gewählt | `POST /token 200`, `Authenticated`, Rückgabewert 0 |
| 4 | 16:09:27 | **34567** | `MCP_OAUTH_CALLBACK_PORT=34567` gesetzt | `POST /token 200`, `Authenticated`, Rückgabewert 0 |

Drei aufeinanderfolgende Läufe, drei verschiedene Ports, alle drei im selben Fenster von drei
Minuten. Lauf 4 steht getrennt, weil ein einzelner fester Wert nichts über die Wechselhaftigkeit
beweist: er beweist nur, dass die Umgebungsvariable greift.

**Zwei zusätzliche Beobachtungen zum Default 3118**, die zeigen, warum eine Doku-Zeile "der
Port ist 3118" falsch wäre:

| Beobachtung | Uhrzeit | Port | Umstand |
|-------------|---------|------|---------|
| `claude mcp login` ohne Terminal, 3118 frei | 15:51 und 15:58 | **3118** | Der Lauf bricht danach mit `stdin isn't a terminal` ab |
| `claude mcp login` ohne Terminal, 3118 von einem fremden Socket gehalten | 16:00 | **48014** | derselbe Aufruf, nur der Port 3118 war belegt |

Der Default erscheint also, und er ist trotzdem nicht der Port, auf den ein Server sich
festlegen dürfte: schon ein zweites Programm auf 3118 verschiebt ihn.

**Die Mechanik dahinter, aus dem Programmtext des Clients** (also aus dem Client gelesen, nicht
aus einem Lauf abgeleitet):

```js
function $3r(e = xGa) { return `http://localhost:${e}/callback` }        // xGa = 3118
function PcS() { let e = q.MCP_OAUTH_CALLBACK_PORT; return e !== void 0 && e <= 65535 ? e : void 0 }
async function fLt(e) {
  let t = PcS(); if (t) return t;                                        // 1. die Umgebungsvariable
  if (e && await kGa(e)) return e;                                       // 2. ein vorgemerkter Port, falls frei
  let { min: r, max: n } = IcS, o = n - r + 1, i = Math.min(o, 100);
  for (let s = 0; s < i; s++) { let a = r + Math.floor(Math.random() * o); if (await kGa(a)) return a }
  if (await kGa(xGa)) return xGa;                                        // 3. der Default, als Letztes
  throw Error("No available ports for OAuth redirect")
}
IcS = Kt() === "windows" ? { min: 39152, max: 49151 } : { min: 49152, max: 65535 }
```

Die drei gemessenen freien Ports 45157, 47608 und 41977 liegen alle im Windows-Fenster
39152 bis 49151, und 48014 aus der Zusatzbeobachtung ebenfalls. Die Messung und der
Programmtext sagen also dasselbe, und die Messung sagt es zuerst.

**Die Antwort auf CLIENT-05 ist damit: ja, das Problem existiert.** Ein Server, der den Port
mitvergleicht, hätte diesen Client dreimal von vier Läufen abgewiesen, an einer Eigenschaft,
die der Client nicht wählen kann. Die Lockerung aus 06-03 (RFC 8252 Abschnitt 7.3) ist damit
keine Vorsichtsmaßnahme, sondern die Bedingung, unter der dieser Client überhaupt verbindet.

---

## 5. Die Gegenprobe zur Loopback-Regel (16:11:07Z)

Ohne diese Gegenprobe würde Abschnitt 4 nur belegen, dass etwas durchgeht, nicht dass die
Grenze hält. Vier Anfragen an `/authorize`, alle mit derselben `client_id`, demselben
`code_challenge` und demselben `resource`; getauscht wurde **nur** die Rückadresse:

| Anfrage | `redirect_uri` | Antwort | Sichtbarer Text |
|---------|----------------|---------|-----------------|
| Kontrolle | `http://localhost:45157/callback` | **302** auf `/authorize/consent` | Zustimmungsseite |
| Pfad abweichend | `http://localhost:45157/other` | **400** | `This app cannot be sent back safely` |
| Loopback-Host, den das Dokument nicht trägt | `http://[::1]:45157/callback` | **400** | `This app cannot be sent back safely` |
| Host, der nur aussieht wie Loopback | `http://localhost.example.com:45157/callback` | **400** | `This app cannot be sent back safely` |

Die Fehlerseite trägt `Cache-Control: no-store` und sagt nicht, welche Hälfte der Prüfung
gefallen ist (T-03-47). Es ist dieselbe Seite, die 06-08 an Cursor gesehen hat.

**Der Host-Wechsel, an der Regel selbst nachgelesen**, weil das Dokument dieses Clients
zufällig *beide* Loopback-Namen registriert und die Frage sonst gar nicht stellbar wäre. Im
laufenden Container, `registry.loopback_match` gegen zwei verschiedene Registrierungslisten:

```
loopback_match('http://localhost:45157/callback', <die zwei des Dokuments>) -> 'http://localhost/callback'
loopback_match('http://127.0.0.1:45157/callback', <die zwei des Dokuments>) -> 'http://127.0.0.1/callback'
loopback_match('http://localhost:45157/callback', ['http://localhost/callback']) -> 'http://localhost/callback'
loopback_match('http://127.0.0.1:45157/callback', ['http://localhost/callback']) -> None
loopback_match('http://localhost:45157/other',    <die zwei des Dokuments>) -> None
loopback_match('http://[::1]:45157/callback',     <die zwei des Dokuments>) -> None
```

Der vierte Aufruf ist der Host-Wechsel: `127.0.0.1` gegen ein registriertes `localhost` ist
eine Absage. Nur der Port ist frei, alles andere wird zeichengenau verglichen.

---

## 6. Nicht vorhergesagt und darum hier festgehalten

**6.1 Der Client verlangt ein Terminal, und `--no-browser` ist nicht der Ausweg.** Der Plan
rechnete mit einem Client, der einen Browser öffnet und auf seinem Port wartet. Claude Code
tut beides, aber `claude mcp login` prüft vorher `stdin.isTTY` und bricht ohne Terminal ab,
auch im Browser-Modus. Der Ausweg war die Pseudo-Konsole (3.1), nicht das Fälschen des
Autorisierungs-Schenkels.

**6.2 Es gibt zwei Wege, den Code zurückzugeben, und beide sind offen.** Der Client lauscht
auf seinem Loopback-Port **und** bietet gleichzeitig `Or paste the redirect URL here:` an. Im
Lauf 1 wurden versehentlich beide benutzt; die Läufe 2 bis 4 haben nur den Loopback-Weg
benutzt, und `callback_status = 200` belegt, dass der Lauscher wirklich stand. Für die
Bewertung heißt das: der Port ist nicht Zierde, der Client bindet ihn.

**6.3 Der Versuch, den Browser stumm zu stellen, ist gescheitert, und das ist so
festgehalten.** Das mitgelieferte `open`-Paket baut sein Windows-Kommando aus `%SYSTEMROOT%`.
Mit einem anderen Wert dort startet `claude.exe` überhaupt nicht mehr (Rückgabewert 127,
zweimal gemessen, einmal mit einem nicht existierenden und einmal mit einem existierenden
Verzeichnis). Der Ausweg war `--no-browser` in der Pseudo-Konsole; ein Fenster des Owners
wurde in den vier gezählten Läufen nicht geöffnet.

**6.4 Jedes Discovery-Dokument wird zweimal geholt.** Vier Zeilen statt zwei, im Abstand von
Millisekunden (3.3). Es kostet vier statische Antworten und ändert nichts, gehört aber
notiert, weil eine spätere Drosselung darüber stolpern könnte.

**6.5 `claude mcp logout` widerruft wirklich.** Zwei `POST /revoke 200` pro Abmeldung, für
Access- und Refresh-Token:

```
2026-08-20T16:09:09.366365133Z INFO: - "POST /revoke HTTP/1.1" 200 OK
2026-08-20T16:09:09.376714372Z INFO: - "POST /revoke HTTP/1.1" 200 OK
```

Das ist die Widerrufsstrecke von 04-03, hier zum ersten Mal von einem fremden Client
ausgelöst und für CONF-01 verwertbar.

**6.6 Eine Zeile aus dem MCP-SDK des Clients, die nicht uns betrifft, aber im Protokoll
steht:** `[mcp-sdk] SEP-2352: stored OAuth credential has no 'issuer' stamp (pre-upgrade
storage or provider not round-tripping the value)`. Sie kommt aus der Ablage des Clients für
seine **anderen** Server (die Meldung erschien auch vor dem ersten Kontakt mit unserer
Instanz) und ist keine Aussage über unsere Antworten. Unser AS-Dokument trägt `issuer`, und
die Rückseite trägt `iss` (3.6).
