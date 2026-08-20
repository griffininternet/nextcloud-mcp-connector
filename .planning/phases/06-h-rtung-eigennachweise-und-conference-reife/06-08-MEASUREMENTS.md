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

