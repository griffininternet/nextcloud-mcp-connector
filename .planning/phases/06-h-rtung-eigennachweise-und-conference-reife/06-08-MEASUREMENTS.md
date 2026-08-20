# 06-08 Messprotokoll: Cursor live gegen den Connector

Datum des Laufs: **2026-08-20, ab 15:02 UTC** (Abschnitt 1). Rechner: der
Entwicklungsrechner aus 06-RESEARCH.md, Abschnitt "Environment Availability"
(Windows-Host, Git Bash). Alles unten ist aus einem Lauf, nicht aus dem Quellcode
abgeleitet; wo eine Aussage aus dem Quellcode kommt, steht das dabei.

Drei Konventionen für dieses Protokoll, übernommen aus 06-07:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen `compose.exapp.yml` verlangt
  `HP_SHARED_KEY` in der Umgebung (WR-11), und der messende Prozess hat mit diesem
  Schlüssel nichts zu tun.
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39).
  Kein Token, kein Autorisierungscode, kein App-Passwort, kein Chiffrat und kein
  Hash-Wert aus der Store-Zeile.
* Die Version einer Instanz ist immer die Zeile aus `occ status`, nie ein Docker-Tag
  (Pitfall 6). Für diesen Plan gilt dasselbe für den Connector: die Pflichtangabe ist
  Version **und** Image-Digest, weil 0.1.1 die Teilregistrierung aus a80af0a noch
  nicht hat und eine Messung gegen 0.1.1 einen falschen Negativbefund ergäbe
  (Pitfall 8).

## Topologie des Laufs

| Was | Wert |
|-----|------|
| Compose-Datei, Projekt | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | **34.0.3 (34.0.3.2)** laut `occ status`; Image-Id `sha256:365baea128b5e0f45a8dc5111c9234b926f1e6082b4c14d75ae650324ce5d65c` |
| Connector | `mcp_connector` **0.1.2 [enabled]** laut `occ app_api:app:list`; Image `127.0.0.1:5000/mcp_connector:0.1.2`, Digest `sha256:3ba4a2ce1921d65bb55c769dde855d0ea6c53794fb5445dcdec673e2e93f74ed`, `RestartCount` 0 |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| **Cursor** | **3.2.16**, `C:\Users\Student\AppData\Local\Programs\cursor\Cursor.exe` (Abschnitt 1) |
| Demo-Substanz | Nutzer `jane` (Jane Fischer), Fixture aus 05-03 |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberührt (kein Kommando dieses Laufs nennt sie) |

Der Digest des Connectors ist derselbe wie am Ende von 06-07, und der Container hat
sich seither nicht neu gestartet. Es läuft also der Arbeitsbaum mit der
Teilregistrierung, nicht die Store-Fassung 0.1.1.

---

## 1. Ist Cursor auf diesem Rechner verfügbar? (15:02:18Z)

**Antwort: ja, Cursor 3.2.16 ist installiert und läuft.** Der Rohbeleg, in der
Reihenfolge der Suche:

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-08-20T15:02:18Z
$ for p in "C:/Program Files/Cursor/Cursor.exe" \
           "C:/Program Files (x86)/Cursor/Cursor.exe" \
           "C:/Users/Student/AppData/Local/Programs/cursor/Cursor.exe"; do test -f "$p" && echo "FOUND $p" || echo "MISSING $p"; done
MISSING C:/Program Files/Cursor/Cursor.exe
MISSING C:/Program Files (x86)/Cursor/Cursor.exe
FOUND   C:/Users/Student/AppData/Local/Programs/cursor/Cursor.exe
$ command -v cursor
(kein Treffer, rc=1)
```

Cursor liegt also nicht in einem Programmordner, sondern im Benutzerprofil unter
`%LOCALAPPDATA%\Programs\cursor`, und es gibt kein `cursor` auf dem `PATH`. Die
ausführbare Datei ist 211 042 088 Bytes groß und vom 28.04.2026.

Die Version wörtlich, aus den zwei Dateien, die sie tragen:

```
$ python -c "<resources/app/package.json lesen>"
Cursor 3.2.16
$ python -c "<resources/app/product.json lesen>"
Cursor 3.2.16 3e548838cf82 2026-04-28T21:07:47.682Z
```

Das ist genau die Version, gegen die der historische Lauf vom 16.08.2026 die
Abweisung gemessen hat (03-09-MEASUREMENTS, Run 4), und genau die Version, die
`docs/oauth-setup.md` heute als offenen Rest nennt. Der Vergleich ist damit nicht
durch einen Versionssprung des Clients verwässert: derselbe Client, anderer Server.

Cursor läuft während der Messung, es musste nicht gestartet werden:

```
$ powershell Get-Process Cursor | Select Id,StartTime,MainWindowTitle
   Id StartTime           MainWindowTitle
 8368 16.08.2026 10:00:59 Cursor Agents
 8404 16.08.2026 10:01:28
 ... (10 Prozesse, ein Fenster)
```

### Der Vorzustand von `~/.cursor/mcp.json`

```
$ ls -la /c/Users/Student/.cursor
.gitignore  argv.json  ide_state.json
ai-tracking/  extensions/  plugins/  projects/  skills-cursor/
$ test -f /c/Users/Student/.cursor/mcp.json && echo EXISTS || echo ABSENT
ABSENT C:/Users/Student/.cursor/mcp.json
```

Der Vorzustand ist also **"die Datei existiert nicht"**, und damit ist die
Wiederherstellung nach dem Lauf ihre Löschung und nicht das Zurückschreiben einer
Sicherung. Es gibt keinen fremden Eintrag, der überschrieben werden könnte
(T-06-50). Sollte während des Laufs doch eine Sicherung nötig werden, liegt sie
unter `C:/Users/Student/.cursor/mcp.json.bak-20260820` und damit außerhalb des
Repositories; ihr Inhalt stünde nicht hier. Abschnitt 6 belegt den Nachzustand.

### Was nicht passiert ist

Es wurde **nichts installiert und nichts heruntergeladen**. Die Suche war
lesend: drei `test -f`, ein `command -v`, ein `ls`, zwei JSON-Dateien gelesen. Der
blockierende Halt aus Task 2 des Plans entfällt damit, weil sein Auslöser
("Cursor nicht vorhanden") nicht eingetreten ist; eine Entscheidung des Operators
über eine Installation war nicht nötig und wurde nicht eingeholt (T-06-52).

```
$ git status --short
(nur die Dateien dieses Plans)
```

**Folge für den Ablauf:** Task 2 wird übersprungen, Task 3 läuft.

---

## 2. Discovery: was Cursor abruft, mit Zeitstempeln (15:08:30Z bis 15:08:32Z)

Angefahren wurde durch das Schreiben von `~/.cursor/mcp.json`, und nichts weiter:

```json
{ "mcpServers": { "nextcloud-0608": {
    "url": "http://127.0.0.1:8081/exapps/mcp_connector/mcp" } } }
```

**Kein Klick war nötig.** Die laufende Cursor-Sitzung hat die Datei von sich aus
gelesen und binnen Sekunden zu verbinden begonnen. Der Rohbeleg ist das Log des
ExApp-Containers, mit den Zeitstempeln, die `docker logs -t` anschreibt:

```
$ docker logs -t nc_app_mcp_connector | grep -v heartbeat | tail -5
2026-08-20T15:08:30.460846970Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T15:08:31.413480848Z INFO: - "POST /mcp HTTP/1.1" 401 Unauthorized
2026-08-20T15:08:31.442792342Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T15:08:31.454638096Z INFO: - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
2026-08-20T15:08:32.454080517Z INFO: - "POST /register HTTP/1.1" 201 Created
```

Zwei Dinge daran sind neu gegenüber dem Lauf vom 16.08.2026 (03-09-MEASUREMENTS,
Run 4), und beide gehören hierher, weil sie sonst als "wie gehabt" durchgingen:

1. **Cursor liest das Ressourcen-Dokument, bevor es den 401 auslöst** (15:08:30, eine
   Sekunde vor dem `POST /mcp`), und danach ein zweites Mal, diesmal dem
   `resource_metadata`-Zeiger des 401 folgend. Der Zeiger selbst, wörtlich:

```
$ curl -s -i -X POST .../exapps/mcp_connector/mcp -d '<initialize>' | grep -i www-authenticate
Www-Authenticate: Bearer error="invalid_token", error_description="Authentication required",
  scope="nextcloud", resource_metadata="http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"
```

2. **Welchen der beiden zulässigen Wege zum AS-Dokument Cursor genommen hat, sagt
   dieses Log nicht**, und das wird hier nicht geraten. Der Container sieht
   `/.well-known/oauth-authorization-server`, weil HaRP das Präfix
   `/exapps/mcp_connector` abschneidet; von außen führen zwei Adressen genau
   dorthin, die kanonische mit Suffix (über die Rewrite-Regel in `deploy/Caddyfile`)
   und die OIDC-artige unter dem `issuer`. Caddy schreibt in dieser Topologie kein
   Zugriffslog, also ist die Frage aus dem vorhandenen Beleg nicht entscheidbar. Was
   sich entscheiden lässt, ist die dritte Möglichkeit, und sie ist ausgeschlossen:

```
$ curl -s -o /dev/null -w '%{http_code}\n' .../.well-known/oauth-protected-resource/exapps/mcp_connector/mcp
200
$ curl -s -o /dev/null -w '%{http_code}\n' .../.well-known/oauth-authorization-server/exapps/mcp_connector
200
$ curl -s -o /dev/null -w '%{http_code}\n' .../.well-known/oauth-authorization-server     # reine Wurzel, ohne Suffix
404
```

Die reine Wurzel ist 404 und erreicht den Container gar nicht, also kann die
200er-Zeile im Log nicht von ihr kommen. Das ist erwähnenswert, weil Cursor sich
den AS in seiner eigenen Ablage als `http://127.0.0.1:8081/` notiert (Abschnitt 4);
diese Zeichenkette ist nicht die Adresse, die es abgerufen hat.

## 3. Registrierung: 201, und zwei von drei Adressen (15:08:32Z)

**Die zentrale Behauptung dieses Protokolls.** Der Aufruf ist die Zeile
`POST /register ... 201 Created` oben, und die geschriebene Store-Zeile ist der
Beleg, dass die Teilregistrierung genau das getan hat, was a80af0a
vorsieht. Ausgelesen aus `oauth.sqlite3` im Volume `nc_app_mcp_connector_data`,
Feld für Feld:

```
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python < <Auslese-Skript>
cols: ['client_id', 'client_secret_hash', 'metadata_json', 'allowed',
       'registered_at', 'last_used_at', 'cimd_fetched_at', 'cimd_expires_at']
client_id           448414fe-8c43-463d-9b1b-14bc1bdb9f88
client_name         Cursor
redirect_uris       ['https://www.cursor.com/agents/mcp/oauth/callback',
                     'http://localhost:8787/callback']
grant_types         ['authorization_code', 'refresh_token']
response_types      ['code']
token_endpoint_auth_method  none
scope               nextcloud offline_access
client_secret_hash  None            <- öffentlicher Client, kein Geheimnis gesetzt
allowed             1
registered_at       1787238512      <- 2026-08-20T15:08:32Z
last_used_at        None            <- noch kein Token abgeholt
cimd_fetched_at     None            <- keine CIMD-Herkunft, das ist eine DCR-Zeile
```

`cursor://anysphere.cursor-mcp/oauth/callback` steht **nicht** in dieser Zeile. Die
Gegenprobe als Suche, damit das nicht nur eine Leseleistung ist:

```
$ <select ... where client_id='448414fe-...'>  | grep -c "cursor://"
0
```

`scope` ist `nextcloud offline_access`, obwohl Cursor keinen Scope gesendet hat: das
ist die Überschreibung aus `register_client`, die es seit dem ChatGPT-Befund von
AUTH-04 gibt, und keine Eigenheit dieses Laufs.

### 3.1 Der gesendete Rumpf, und die Antwort wörtlich

Der eigene Code echot eine verworfene Adresse absichtlich nicht, also sagt die
Antwort an Cursor nichts über den dritten Eintrag. Der gesendete Rumpf ist deshalb
aus **Cursors eigener Ablage** belegt (Abschnitt 4) und die Antwortform aus einer
**Wiederholung mit demselben Rumpf**, abgesetzt vom Messrechner um 15:11:10Z, mit
`client_name` als Kennzeichnung, damit die Wiederholung nicht mit dem echten Lauf
verwechselt wird:

```
$ curl -s -w '\nHTTP %{http_code}\n' -X POST -H "Content-Type: application/json" \
    --data-binary '{"redirect_uris":["cursor://anysphere.cursor-mcp/oauth/callback",
                                     "https://www.cursor.com/agents/mcp/oauth/callback",
                                     "http://localhost:8787/callback"],
                    "token_endpoint_auth_method":"none",
                    "grant_types":["authorization_code","refresh_token"],
                    "response_types":["code"],
                    "client_name":"Cursor (replay 06-08)",
                    "logo_uri":"https://.../cursorlogomcpv3.svg"}' \
    .../exapps/mcp_connector/register
HTTP 201
{
 "client_id": "7b310547-a467-4f7b-b520-fc9142ab33d4",
 "client_id_issued_at": 1787238670,
 "client_name": "Cursor (replay 06-08)",
 "redirect_uris": ["https://www.cursor.com/agents/mcp/oauth/callback",
                   "http://localhost:8787/callback"],
 "grant_types": ["authorization_code", "refresh_token"],
 "response_types": ["code"],
 "token_endpoint_auth_method": "none",
 "application_type": "native",
 "scope": "nextcloud offline_access",
 "logo_uri": "https://.../cursorlogomcpv3.svg"
}
```

Die Antwort trägt also die zwei registrierten Adressen und nicht die drei
gesendeten, was RFC 7591 §3.2.1 genau so verlangt. Die Zeile dieser Wiederholung
wurde danach wieder aus dem Store entfernt, damit der Nachzustand der Instanz der
Vorzustand plus die eine echte Cursor-Zeile ist (T-05-24):

```
$ <delete from clients where client_id='7b310547-...'>
clients now: 3
('c06831e2-36ee-48f9-a99c-d091b3013311', 'Claude Desktop')
('7256ad37-7670-4621-ba02-021e835fd372', 'Open WebUI')
('448414fe-8c43-463d-9b1b-14bc1bdb9f88', 'Cursor')
authorizations: 2
refresh_tokens: 2
```

Die zwei Verbindungen von `jane` stehen unverändert daneben, und sie sind nicht
Teil dieses Laufs.

## 4. Was Cursor sich merkt, und warum das für die Autorisierung zählt

Cursor legt den laufenden Versuch als Datei ab. Sie ist der Beleg für den
**gesendeten** Rumpf, weil die Antwort ihn nicht enthält:

```
$ <lesen von>
%APPDATA%\Cursor\User\globalStorage\anysphere.cursor-mcp\mcp-oauth-attempts\<attempt>.json
attemptId              5489ed61-3e8a-463f-8fa0-375792e4aa96
identifier             user-nextcloud-0608
createdAtMs            1787238513221
serverUrl              http://127.0.0.1:8081/exapps/mcp_connector/mcp
authorizationServerUrl http://127.0.0.1:8081/
codeVerifier           <vorhanden, Wert steht hier nicht>
clientInformation      {
  "redirect_uris": ["cursor://anysphere.cursor-mcp/oauth/callback",
                    "https://www.cursor.com/agents/mcp/oauth/callback",
                    "http://localhost:8787/callback"],
  "token_endpoint_auth_method": "none",
  "grant_types": ["authorization_code","refresh_token"],
  "response_types": ["code"],
  "client_name": "Cursor",
  "logo_uri": "https://.../cursorlogomcpv3.svg",
  "scope": "nextcloud offline_access",
  "client_id": "448414fe-8c43-463d-9b1b-14bc1bdb9f88",
  "client_id_issued_at": 1787238512 }
```

Dieses Objekt ist eine **Mischung** aus dem, was Cursor gesendet hat, und dem, was
unsere Antwort brachte: `client_id`, `client_id_issued_at` und `scope` können nur
aus der Antwort kommen, `redirect_uris` kann nur aus dem eigenen Rumpf kommen, denn
die Antwort trug dort zwei Einträge und dieses Feld trägt drei. Damit ist der
gesendete Drei-URI-Rumpf belegt, ohne Sonde und ohne Mitschnitt.

Und damit ist auch die Frage benannt, die `docs/client-setup.md` heute offen lässt:
**Cursor merkt sich nach dem 201 weiter seine eigenen drei Adressen**, also weiß es
nicht, dass eine verworfen wurde. Welche davon es an `/authorize` mitschickt,
entscheidet, ob die Verbindung zustande kommt: die zwei registrierten passen auf die
exakte Prüfung, die private-use Adresse würde von ihr abgewiesen. Nur der Live-Lauf
beantwortet das, und deshalb ist Abschnitt 5 kein Beiwerk.

Der Zustand, in dem Cursor nach der Registrierung stehen bleibt, aus seinem eigenen
Log:

```
$ tail "%APPDATA%\Cursor\logs\<session>\window1_wb0\exthost\anysphere.cursor-mcp\MCP user-nextcloud-0608.log"
2026-08-20 17:08:32.462 [info] saveClientInformation() entered
2026-08-20 17:08:32.468 [info] Persisting new OAuth client registration
2026-08-20 17:08:33.176 [info] Saving PKCE code verifier
2026-08-20 17:08:33.236 [info] MCP OAuth redirect to authorization
2026-08-20 17:08:33.256 [info] Connect failed after auth_required; returning needsAuth (streamableHttp)
2026-08-20 17:08:33.921 [info] CreateClient completed, connected: false, statusType: needsAuth
$ tail "…\window1_wb0\workbench.mcp.oauth.log"
2026-08-20 17:08:33.919 [info] [MCPService] State transition: user-nextcloud-0608 initializing → needsAuth
```

Die Zeitstempel dieser Dateien sind Ortszeit (17:08), die des Containers UTC
(15:08); es ist derselbe Augenblick.

**`needsAuth` heißt: Cursor hat die Autorisierungsadresse gebaut und wartet auf einen
Klick.** Es hat von sich aus keinen Browser geöffnet, und der ExApp-Container hat
folgerichtig kein `GET /authorize` gesehen. Gegenprobe, dass hier nicht ein
stiller Fehlschlag als Warten gedeutet wird: Cursor hält in diesem Zustand keinen
Port offen, also läuft auch kein Rücknahme-Lauscher, der einen Code annehmen
könnte.

```
$ Get-NetTCPConnection -State Listen | ? OwningProcess -in (Get-Process Cursor).Id
(keine Zeile)
$ Get-NetTCPConnection -LocalPort 8787
(keine Zeile)
```

## 5. Stand dieses Protokolls (Halt um 15:15Z)

Abschnitte 1 bis 4 sind gemessen und abgeschlossen. Die Autorisierung und der
Werkzeugaufruf fehlen, und sie fehlen aus einem benannten Grund und nicht, weil ein
Schritt übersprungen wurde:

* Cursor steht auf `needsAuth` und öffnet den Browser erst auf einen Klick in seiner
  eigenen Oberfläche. Es gibt keinen Weg von außen dorthin, der gemessen und nicht
  vorgetäuscht wäre: die Installation hat kein `cursor-agent`-Kommando
  (`resources/app/bin` trägt `cursor`, `code-tunnel.exe` und `cursor-tunnel.exe`,
  kein Agentenkommando), die laufende Sitzung hält keinen Debug-Port offen
  (Gegenprobe in Abschnitt 4), und der Werkzeugaufruf verlangt ohnehin den Agenten
  im Fenster.
* Ein Neustart von Cursor mit `--remote-debugging-port` wäre der technische Ausweg
  und wird hier **nicht** genommen: das Fenster gehört dem Owner und läuft seit dem
  16.08. Fremde Software des Owners neu zu starten ist keine Entscheidung dieses
  Plans (dasselbe Prinzip wie T-06-52).
* Den Browser-Schenkel selbst mit Cursors gespeicherten Versuchsdaten zu fahren wäre
  möglich, wäre aber **nicht** die Behauptung, die CLIENT-04 verlangt: dann hätte
  der messende Prozess autorisiert und nicht Cursor.

Was noch fehlt, steht damit als offene Behauptung fest und nicht als Lücke:
welche der drei Adressen Cursor an `/authorize` mitschickt, ob der Tausch am
Token-Endpunkt gelingt, und ob ein Werkzeugaufruf Inhalt zurückbringt.
`~/.cursor/mcp.json` bleibt für den Rest des Laufs absichtlich liegen; ihre
Entfernung ist der letzte Schritt und wird in Abschnitt 9 belegt.

**Der Halt hat 11 Minuten gedauert.** Um 15:26:38Z hat der Operator in Cursor die
Anmeldung ausgelöst, und der Lauf ging weiter. Abschnitt 6 ist sein Ergebnis.

## 6. Autorisierung: abgewiesen, weil Cursor auf `cursor://` besteht (15:26:38Z bis 15:28:46Z)

**Der Befund in einem Satz: Cursor schickt an `/authorize` genau die Adresse mit,
die bei der Registrierung verworfen wurde, und wird dafür abgewiesen.** Die
Verbindung kommt also auch mit 0.1.2 nicht zustande; was sich gegenüber 0.1.1
verschoben hat, ist der Ort des Scheiterns, von `/register` nach `/authorize`.

Die Kette aus dem Containerlog, ungekürzt bis auf die Umbrüche in der langen Zeile:

```
$ docker logs -t nc_app_mcp_connector | grep -v heartbeat | tail -5
2026-08-20T15:26:38.183Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T15:26:38.784Z INFO: - "POST /mcp HTTP/1.1" 401 Unauthorized
2026-08-20T15:26:38.790Z INFO: - "GET /.well-known/oauth-protected-resource/mcp HTTP/1.1" 200 OK
2026-08-20T15:26:38.797Z INFO: - "GET /.well-known/oauth-authorization-server HTTP/1.1" 200 OK
2026-08-20T15:26:39.443Z INFO: - "POST /register HTTP/1.1" 201 Created
2026-08-20T15:26:40.852Z INFO: - "GET /authorize?response_type=code
    &client_id=d6ea6583-352c-4034-aec9-c286e7a9c611
    &code_challenge=2MdCI6Jn_cA0h8TiV_W2eJx6ZkM1eAkg1wjBplF_c6M&code_challenge_method=S256
    &redirect_uri=cursor%3A%2F%2Fanysphere.cursor-mcp%2Foauth%2Fcallback
    &state=eyJpZCI6InVzZXItbmV4dGNsb3VkLTA2MDgiLCJvd25lciI6...
    &scope=nextcloud
    &resource=http%3A%2F%2F127.0.0.1%3A8081%2Fexapps%2Fmcp_connector%2Fmcp HTTP/1.1" 400 Bad Request
2026-08-20T15:28:46.418Z INFO: - "GET /authorize?<derselbe Rumpf> HTTP/1.1" 400 Bad Request
```

Dekodiert sind die drei Felder, auf die es ankommt:

```
redirect_uri  cursor://anysphere.cursor-mcp/oauth/callback     <- die verworfene Adresse
scope         nextcloud
resource      http://127.0.0.1:8081/exapps/mcp_connector/mcp   <- RFC 8707, korrekt gesetzt
state         {"id":"user-nextcloud-0608",
               "owner":{"workspaceId":"empty-window"},
               "attemptId":"b5d24d1d-8297-41b8-a59f-669ce9082945"}
```

Der `state` ist base64-kodiertes JSON und trägt kein Geheimnis, sondern Cursors
eigene Buchführung; er steht hier, weil er die Anfrage dem Versuch zuordnet, den
Abschnitt 6.2 nachliest. `resource` ist gesetzt und richtig, also scheitert die
Anfrage nicht an der Zielgruppe, und `code_challenge_method` ist `S256`.

### 6.1 Was der Nutzer sieht, wörtlich

Die Antwort ist `400` und **keine Weiterleitung**, und das ist der Punkt: an eine
nicht registrierte Adresse wird nichts gesendet, auch kein Fehler. Der sichtbare
Text der Seite, aus einer Wiederholung derselben Adresse abgeholt und von den
Auszeichnungen befreit:

```
$ curl -s -o e5.html -w 'HTTP %{http_code}  bytes=%{size_download}\n' "<die Adresse von oben>"
HTTP 400  bytes=4179

MCP Connector for Nextcloud
127.0.0.1:8081
This app cannot be sent back safely
The address Cursor asked us to return to does not match its registration. For your
safety nothing was shared. Start the connection again in your assistant app, and tell
your administrator if it keeps happening.
The password prompt is always Nextcloud itself. If any other page asks you for your
Nextcloud password, close it.
```

Die Seite nennt den Client "Cursor", und dieser Name kommt aus der Registrierung und
nicht aus der Anfrage. Es ist die Seite `E5` aus `03-UI-SPEC.md`, und sie sagt
absichtlich nicht, welche Hälfte der Prüfung gefallen ist (T-03-47).

Der Codepfad ist damit eindeutig bestimmt, `src/mcp_connector/oauth/consent.py:262-272`:
die exakte Prüfung des SDK wirft `InvalidRedirectUriError`, danach wird die
Portregel gefragt, und weil auch die verneint, endet es auf `E5`. Gemessen im
laufenden Container, statt aus dem Quelltext geschlossen:

```
$ docker exec -i nc_app_mcp_connector /app/.venv/bin/python
>>> registry.loopback_match(<Kandidat>, ['https://www.cursor.com/agents/mcp/oauth/callback',
                                         'http://localhost:8787/callback'])
'cursor://anysphere.cursor-mcp/oauth/callback' -> None
'http://localhost:8787/callback'              -> http://localhost:8787/callback
'http://localhost:51234/callback'             -> http://localhost:8787/callback
```

Die Portregel aus 06-03 ist also intakt und greift hier nur deshalb nicht, weil sie
ein Loopback-`http` verlangt: ein privates Schema hat keinen Port, den man lockern
könnte. **Das ist keine Lücke in `loopback_match`**, und die dritte Zeile belegt es:
dieselbe Adresse mit einem anderen Port wird angenommen.

### 6.2 Der Klick wirft die Registrierung weg und registriert neu

Die `client_id` der abgewiesenen Anfrage, `d6ea6583-352c-4034-aec9-c286e7a9c611`, ist
**nicht** die aus Abschnitt 3. Das war nicht vorhergesehen und hat einen belegten
Grund: der Knopf in Cursor ist ein Abmelden mit anschließendem Neuaufbau, und dabei
wirft Cursor seine gespeicherte Registrierung weg.

```
$ tail "…\exthost\anysphere.cursor-mcp\MCP user-nextcloud-0608.log"
2026-08-20 17:26:38.123 [info] [V2] Handling LogoutServer action
2026-08-20 17:26:38.123 [info] Clearing stored OAuth data
2026-08-20 17:26:38.169 [info] Successfully cleared OAuth tokens
2026-08-20 17:26:38.169 [info] [V2] Removing client, reason: logout_server
2026-08-20 17:26:38.172 [info] [V2] Handling ReloadClient action
2026-08-20 17:26:39.427 [info] Registration lock acquired, this provider will register
2026-08-20 17:26:39.427 [info] No stored client information found
2026-08-20 17:26:39.454 [info] Persisting new OAuth client registration
2026-08-20 17:26:40.083 [info] Saving PKCE code verifier
2026-08-20 17:26:40.094 [info] MCP OAuth redirect to authorization
2026-08-20 17:26:40.100 [info] Connect failed after auth_required; returning needsAuth
$ tail "…\workbench.mcp.oauth.log"
2026-08-20 17:26:38.122 [info] [MCPService] clearing OAuth state for server: user-nextcloud-0608 (cause=user_logout)
2026-08-20 17:26:40.679 [info] [MCPService] State transition: user-nextcloud-0608 initializing → needsAuth
```

Die Folge steht im Store: **zwei Cursor-Zeilen**, beide mit denselben zwei Adressen,
beide ohne die private-use Adresse, die erste ohne jede Verwendung:

```
$ <select client_id, client_name, registered_at, last_used_at, redirect_uris from clients>
c06831e2-…  Claude Desktop  reg 1787204156  last_used 1787204394  ['http://127.0.0.1:45001/callback']
7256ad37-…  Open WebUI      reg 1787204157  last_used 1787204515  ['http://127.0.0.1:45002/callback']
448414fe-…  Cursor          reg 1787238512  last_used None        ['https://www.cursor.com/agents/mcp/oauth/callback',
                                                                   'http://localhost:8787/callback']
d6ea6583-…  Cursor          reg 1787239599  last_used None        ['https://www.cursor.com/agents/mcp/oauth/callback',
                                                                   'http://localhost:8787/callback']
```

Und die zweite Versuchsdatei von Cursor, die zur abgewiesenen Anfrage gehört:

```
attemptId    b5d24d1d-8297-41b8-a59f-669ce9082945   (die aus dem state)
client_id    d6ea6583-352c-4034-aec9-c286e7a9c611
redirect_uris ['cursor://anysphere.cursor-mcp/oauth/callback',
               'https://www.cursor.com/agents/mcp/oauth/callback',
               'http://localhost:8787/callback']
```

Cursor führt also weiter alle drei Adressen und nimmt für die Anfrage die **erste**.
Der Befund aus Abschnitt 4 ist damit nicht nur eine Beobachtung an einer Ablage,
sondern die Ursache des Fehlschlags: Cursor liest die `redirect_uris` der Antwort
nicht zurück in seine eigene Liste, also kann es nicht wissen, dass es genau die
Adresse nimmt, die es nicht nehmen darf.

Jeder Anmeldeversuch hinterlässt damit eine unbenutzbare Client-Zeile. Zwei Versuche
in 18 Minuten haben zwei erzeugt.

## 7. Der Werkzeugaufruf: hat nicht stattgefunden, und warum

Es gibt keinen Abschnitt mit einem Werkzeugaufruf und Inhalt, weil es keinen
Werkzeugaufruf gab. Ohne Autorisierung gibt es keinen Code, ohne Code kein Token und
ohne Token bleibt `/mcp` bei `401`. Der Store sagt dasselbe ohne Auslegung:

```
$ <counts>
clients 4        <- 2 Fixture-Clients, 2 unbenutzbare Cursor-Zeilen
flows 0          <- kein offener Anmeldevorgang
auth_codes 0     <- kein Code ausgegeben
access_tokens 0  <- kein Token ausgegeben
authorizations 2 <- die zwei Verbindungen von jane, unverändert
refresh_tokens 2
$ <select nc_user, client_id, revoked_at from authorizations>
jane  c06831e2-…  revoked_at None
jane  7256ad37-…  revoked_at None
```

`last_used_at` ist bei beiden Cursor-Zeilen `None`, also hat keine von ihnen je ein
Token abgeholt. Der Werkzeugaufruf ist damit nicht "offen", sondern **durch den
Befund von Abschnitt 6 ausgeschlossen**, solange Cursor auf seiner privaten Adresse
besteht. Das Konto, mit dem angemeldet worden wäre, hat die Anmeldeseite nie
gesehen: die Abweisung liegt vor jedem Passwortdialog, was die Fehlerseite auch
selbst sagt ("nothing was shared").

## 8. Gegenproben: was NICHT passiert ist

Drei Anfragen an `/authorize`, gleiche `client_id`, gleicher `code_challenge`,
gleicher `resource`, nur die Rückadresse getauscht. Das ist die Trennung zwischen
"Cursor scheitert an der Adresse" und "Cursor scheitert an dieser Instanz":

| Rückadresse | Antwort |
|-------------|---------|
| `http://localhost:8787/callback` (registriert) | **302** auf `…/authorize/consent?flow=…&login=…` |
| `http://localhost:51234/callback` (registriert, anderer Port) | **302** auf die Zustimmungsseite |
| `cursor://anysphere.cursor-mcp/oauth/callback` | **400**, Seite `E5` |

```
$ curl -s -o /dev/null -w 'HTTP %{http_code}  location=%{redirect_url}\n' "<A>"
HTTP 302  location=http://127.0.0.1:8081/exapps/mcp_connector/authorize/consent?flow=<…>&login=<…>
$ curl … "<B>"
HTTP 302  location=…/authorize/consent?flow=<…>&login=<…>
$ curl … "<C>"
HTTP 400
```

Die Werte von `flow` und `login` sind Anmeldegeheimnisse und stehen deshalb nicht
hier. Die zwei so entstandenen `flows`-Zeilen wurden danach wieder gelöscht, damit
der Nachzustand kein Nebenprodukt der Messung trägt (T-05-24):

```
$ <delete from flows where state='gegenprobe-06-08'>
flows vorher: 2
flows nachher: 0
```

Was diese Tabelle zusammen mit Abschnitt 6 belegt, Punkt für Punkt:

* **Es ist nicht die Instanz.** Zwei von drei Anfragen kommen bis zur
  Zustimmungsseite, mit derselben `client_id`, die abgewiesen wurde.
* **Es ist nicht der Port und nicht die Loopback-Regel.** Ein anderer Port auf
  derselben registrierten Adresse wird angenommen, also wirkt die Lockerung aus
  06-03 auch für diesen Client.
* **Es ist nicht die Teilregistrierung.** Sie hat getan, was sie soll: `201` statt
  `400`, zwei Adressen im Store, keine private-use Adresse darin.
* **D-35 steht unverändert.** Die private-use Adresse ist nicht registriert, also
  wird sie an der exakten Prüfung abgewiesen, und genau das war die Ansage. Die
  Abweisung ist kein Fehler des Servers, sondern seine Regel bei der Arbeit.
* **Kein falscher Negativbefund durch eine alte Fassung.** Gemessen wurde gegen
  `mcp_connector` 0.1.2, Image-Digest `sha256:3ba4a2ce1921…`, `RestartCount` 0
  (Topologie-Tabelle), also gegen die Fassung MIT der Teilregistrierung. Der Beleg
  dafür ist der `201` selbst: 0.1.1 hätte hier `400 invalid_redirect_uri`
  geantwortet, und genau das ist der historische Befund vom 16.08.
* **Kein Credential ist geflossen.** Kein Token, kein Code, keine Anmeldeseite. Die
  zwei Verbindungen von `jane` sind unangetastet und nicht widerrufen.

## 9. Nicht vorhergesagt und darum hier festgehalten

1. **Die Teilregistrierung allein reicht für Cursor nicht.** Der Plan erwartete
   `201` und danach eine Verbindung. Der `201` kam, die Verbindung nicht: Cursor
   nimmt die erste seiner drei Adressen, und das ist die verworfene. Der Fehlschlag
   ist von `/register` nach `/authorize` gewandert, nicht verschwunden. Für die Doku
   heißt das, dass der Satz "a client of this shape is no longer kept out" so nicht
   stehenbleiben kann.
2. **Cursor liest die Antwort der Registrierung nicht zurück.** RFC 7591 §3.2.1
   verlangt vom Server, die registrierten Metadaten zu antworten, und der Server tut
   das. Der Client verlässt sich trotzdem auf seine gesendete Liste. Genau diese
   Asymmetrie macht ein stilles Verwerfen für ihn unsichtbar, und sie ist der Grund,
   warum "verwerfen statt abweisen" hier nicht hilft.
3. **Der Anmeldeknopf ist ein Abmelden mit Neuregistrierung.** Er erzeugt eine neue
   `client_id` und lässt die alte Zeile unbenutzt zurück. Zwei Klicks, zwei
   Client-Zeilen. Ein Server, der oft angeklickt wird, sammelt also DCR-Zeilen ohne
   Verwendung ein; die Zeilen sind harmlos (kein Geheimnis, `last_used_at` leer),
   aber sie sind da.
4. **Cursor verbindet ohne Klick, aber es autorisiert nicht ohne Klick.** Das
   Schreiben von `~/.cursor/mcp.json` genügt für Discovery und Registrierung
   (Abschnitt 2, Sekunden nach dem Schreiben), für die Autorisierung nicht. Die
   Doku-Zeile "no button involved" ist damit nur für die erste Hälfte richtig.
5. **Cursor notiert den Autorisierungsserver als `http://127.0.0.1:8081/`.** Diese
   Zeichenkette ist nicht die Adresse, die es abgerufen hat: die reine Wurzel
   antwortet `404` (Abschnitt 2). Es ist eine Notiz in Cursors Ablage, nicht ein
   Messwert über diesen Server, und sie steht hier, damit sie später niemand als
   Widerspruch liest.
6. **Was ein Fix wäre, gehört nicht in diesen Plan.** Der Befund ist benannt, nicht
   behoben. Drei Wege sind sichtbar und alle drei sind Entscheidungen und keine
   Reparaturen: die private-use Adresse doch registrieren (widerspricht D-35 und
   seiner Begründung, dass auf einem Desktop kein Programm ein Schema exklusiv
   besitzt), die Registrierung wieder ganz abweisen (das war 0.1.1 und hat Cursor
   ebenfalls draußen gelassen, nur früher), oder die Antwort so gestalten, dass ein
   Client das Verworfene bemerken muss. Ob und welcher davon, entscheidet die
   Phasen-Verifikation oder ein eigener Plan, nicht dieser.

## 10. Nachzustand: alles zurückgestellt (15:33:29Z)

`~/.cursor/mcp.json` ist wieder im Vorzustand, und der Vorzustand war "existiert
nicht" (Abschnitt 1). Es wurde also gelöscht und keine Sicherung zurückgeschrieben,
weil es keine gab und keine gebraucht wurde:

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-08-20T15:33:29Z
$ rm -f ~/.cursor/mcp.json
$ test -f ~/.cursor/mcp.json && echo EXISTS || echo ABSENT
ABSENT C:/Users/Student/.cursor/mcp.json
$ ls ~/.cursor
ai-tracking argv.json extensions ide_state.json plugins projects skills-cursor
$ ls ~/.cursor/mcp.json.bak-20260820
(nicht vorhanden: es wurde nie eine Sicherung angelegt, weil nichts zu sichern war)
```

Cursor hat die Entfernung von sich aus bemerkt, und das ist die Gegenprobe, dass die
Datei wirklich die Quelle des ganzen Laufs war:

```
$ tail "…\workbench.mcp.oauth.log"
2026-08-20 17:33:29.990 [info] [MCPService] OAuth clear candidate for server: user-nextcloud-0608 (cause=config_server_removed)
2026-08-20 17:33:30.013 [info] [MCPService] Cleared identifier-scoped OAuth state for server: user-nextcloud-0608 (cause=config_server_removed)
```

Im Store wurden die zwei unbenutzbaren Cursor-Zeilen entfernt. Sie sind Messrückstand
und keine Substanz: `last_used_at` war bei beiden leer, und eine Neuregistrierung
kostet einen Dateischreibvorgang. Der Nachzustand ist damit der Vorzustand:

```
$ <delete from clients where client_id in ('448414fe-…','d6ea6583-…')>
clients 2
('c06831e2-36ee-48f9-a99c-d091b3013311', 'Claude Desktop')
('7256ad37-7670-4621-ba02-021e835fd372', 'Open WebUI')
flows 0   auth_codes 0   access_tokens 0
authorizations 2   refresh_tokens 2
('jane', 'c06831e2-36ee-48f9-a99c-d091b3013311', revoked_at None)
('jane', '7256ad37-7670-4621-ba02-021e835fd372', revoked_at None)
```

Nichts wurde installiert, nichts heruntergeladen, kein Container neu gestartet, keine
Instanzversion angefasst. Und die Instanzen des Owners, die diesen Lauf nur
ausgehalten haben:

```
$ docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
nc_app_mcp_connector    127.0.0.1:5000/mcp_connector:0.1.2   Up 48 minutes (healthy)
nc-mcp-exapp-nc         nextcloud:34.0.3-apache              Up About an hour (healthy)
nc-mcp-exapp-caddy      caddy:2                              Up 11 hours
nc-mcp-exapp-harp       ghcr.io/nextcloud/...harp:release    Up 11 hours (healthy)
nc-mcp-exapp-registry   registry:2                           Up 11 hours
findling-nextcloud      nextcloud:34.0.3-apache              Up 5 days
nc-mcp-test             nextcloud:34-apache                  Up 5 days (healthy)
```

## 11. Die Antwort auf CLIENT-04, in einer Tabelle

| Frage | Antwort, gemessen am 2026-08-20 gegen 0.1.2 |
|-------|---------------------------------------------|
| Ist Cursor auf diesem Rechner verfügbar? | ja, 3.2.16 |
| Verbindet Cursor ohne Klick? | ja, das Schreiben von `~/.cursor/mcp.json` genügt für Discovery und Registrierung |
| Wird der Drei-URI-Rumpf `201`? | **ja**, und der Store trägt die zwei zulässigen Adressen, die private-use nicht |
| Durchläuft Cursor die Autorisierung? | **nein**: es schickt `cursor://anysphere.cursor-mcp/oauth/callback` an `/authorize` und wird mit `400` und der Seite `E5` abgewiesen |
| Ruft Cursor ein Werkzeug auf? | nein, und das ist durch die Zeile darüber ausgeschlossen, nicht offen |
| Liegt die Ursache auf unserer Seite? | nein bei der Portregel und nein bei der Teilregistrierung (Abschnitt 8); die Ursache ist eine Adresse, die D-35 bewusst nicht registriert, und ein Client, der die Antwort seiner Registrierung nicht zurückliest |

