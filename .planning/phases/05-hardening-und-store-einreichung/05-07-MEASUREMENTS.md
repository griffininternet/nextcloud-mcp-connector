# 05-07 Messprotokoll: Open WebUI gegen den Connector

Datum des Laufs: 2026-08-19, 18:02 bis 18:20 UTC. Rechner: der Entwicklungsrechner aus
05-RESEARCH.md "Environment Availability". Alles unten ist aus einem Lauf, nicht aus dem
Quellcode abgeleitet; wo eine Aussage aus dem Quellcode kommt, steht das dabei.

## Topologie des Laufs

| Was | Wert |
|-----|------|
| ExApp-Topologie | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, neu angefahren nach der Prozedur aus STATE.md |
| Nextcloud | `nextcloud:34-apache`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Connector | `mcp_connector` 0.1.0, Image-Digest `sha256:dd28c591b139d2dbbf4193354231d6e3122b5020cee24d3dd7858d58e62a3b95`, `occ app_api:app:list` meldet `mcp_connector (MCP Connector): 0.1.0 [enabled]` |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| Open WebUI | `ghcr.io/open-webui/open-webui:main`, Version 0.11.0 (Startbanner), Digest `sha256:6a773e5c3a246b65cbe74ce942b294292c0e5f81c138f703d111bc162f7d7c3d`, Container `nc-mcp-owui-probe`, veroeffentlicht auf `127.0.0.1:3030` |
| `WEBUI_URL` | `http://localhost:3030` |
| `WEBUI_SECRET_KEY` | gesetzt, 64 Hex-Zeichen aus `openssl rand -hex 32` |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberuehrt (kein Kommando dieses Laufs nennt sie) |

Eine Eigenheit der Messumgebung, weil sie die Zahlen erklaert: der Connector veroeffentlicht
sich als `http://127.0.0.1:8081/...`, und ein Container hat sein eigenes Loopback. Damit der
Browser auf dem Host und Open WebUI im Container **dieselbe** Zeichenkette benutzen (der
`resource`-Wert nach RFC 8707 und der `issuer` nach RFC 8414 werden zeichengenau verglichen),
lief im Open-WebUI-Container ein Weiterleiter aus der Standardbibliothek, der dort
`127.0.0.1:8081` auf `caddy:80` im Compose-Netz legt. In das fremde Image wurde nichts
installiert. Gegenprobe: derselbe URL-Aufruf liefert vom Host und aus dem Container dasselbe
Dokument.

## 1. Discovery und Registrierung (serverseitig belegt)

Log des Containers `nc_app_mcp_connector`, in dieser Reihenfolge, 18:16:04 bis 18:16:07 UTC:

```
POST /mcp                                        401 Unauthorized
GET  /.well-known/oauth-protected-resource/mcp   200 OK
GET  /.well-known/oauth-authorization-server     200 OK
POST /register                                   201 Created
```

Der 401 ist Open WebUIs anonymes `initialize`; der `WWW-Authenticate`-Zeiger ist der Weg, auf
dem es die Metadaten findet (Weg 1 aus `oauth/metadata.py`, kein Admin-Eingriff noetig).

Die eingegangene Registrierung, gelesen aus `oauth.sqlite3` im Volume
`nc_app_mcp_connector_data`:

| Feld | Wert |
|------|------|
| `client_id` | `8c0fcffc-9225-4d6f-ad80-5f511a1e0df8` |
| `client_name` | `Open WebUI` |
| `redirect_uris` | `['http://localhost:3030/oauth/clients/mcp:nextcloud/callback']`, **count = 1** |
| `scope` | `nextcloud offline_access` |
| `grant_types` | `['authorization_code', 'refresh_token']` |
| `token_endpoint_auth_method` | `client_secret_post` |
| Client-Secret vorhanden | ja (nur als SHA-256-Hash gespeichert) |
| `registered_at` | 2026-08-19T18:16:07Z |

Scope-Quelle: Open WebUI setzt den Scope aus `scopes_supported` **unserer PRM** (`nextcloud`),
nicht aus dem groesseren Katalog der AS-Metadaten. Unsere Registrierung schreibt daraus
`nextcloud offline_access` (`REGISTERED_SCOPE`), und genau dieser Zusatz erzeugt spaeter das
Refresh-Token.

Nicht vorhergesagt und darum hier festgehalten: Open WebUI registriert sich als
**vertraulicher** Client mit `client_secret_post`, nicht als public client wie Claude.ai und
ChatGPT. Der Grund steht in seinem Quellcode (`utils/oauth.py`): es behaelt seinen Default
`client_secret_post`, weil unsere AS-Metadaten diese Methode auflisten. Der eigene
`ClientAuthenticator` aus Plan 03-06 ist damit nicht nur Theorie, er ist der Pfad, den dieser
Client nimmt.

## 2. Autorisierungsanfrage (der `resource`-Parameter)

Die Weiterleitung, die Open WebUI baut (aus seiner eigenen `/oauth/clients/mcp:nextcloud/authorize`):

```
target                 http://127.0.0.1:8081/exapps/mcp_connector/authorize
client_id              8c0fcffc-9225-4d6f-ad80-5f511a1e0df8
redirect_uri           http://localhost:3030/oauth/clients/mcp:nextcloud/callback
scope                  nextcloud offline_access
resource               http://127.0.0.1:8081/exapps/mcp_connector/mcp
code_challenge_method  S256
response_type          code
```

`resource` traegt die Zeichenkette aus dem `resource`-Feld unserer PRM, zeichengenau (RFC 8707).

## 3. Zustimmung und Tokenausgabe

Log, 18:16:20 bis 18:16:24 UTC:

```
GET  /authorize?...                              302 Found
GET  /authorize/consent?flow=...&step=wait       200 OK
POST /authorize/decide                           200 OK
POST /token                                      200 OK
```

Die Zustimmungsseite nannte den Client `Open WebUI` und das angemeldete Konto `alice` (beides
im Seitentext geprueft). Die Nextcloud-Anmeldung und die Zustimmung liefen mit dem Helfer aus
`scripts/oauth_flow_check.py`, also ueber die Login-Flow-v2-Seiten von Nextcloud und mit der
Sitzung, die daraus entsteht, ohne Browser. Der Browser selbst ist Gegenstand des Checkpoints
(Task 2 dieses Plans) und ist **noch nicht** bestaetigt.

Die entstandene Autorisierung:

| Feld | Wert |
|------|------|
| `auth_id` | `hAWV5uPXQLGf_hV9LAtgjUlFlbpELppKnX9id-Bd-8w` |
| `nc_user` | `alice` |
| `scopes` | `nextcloud offline_access` |
| `resource` | `http://127.0.0.1:8081/exapps/mcp_connector/mcp` |

Das ausgegebene Refresh-Token, aus `refresh_tokens`:

| Feld | Wert |
|------|------|
| `token_hash` | `75c20feff705...` (gekuerzt) |
| `family_id` | `Tkmj8xxnZ3w9_jixNtv9mQ` |
| `state` | `active` |
| `issued_at` | 2026-08-19T18:16:24Z |
| `expires_at` | 2026-09-18T18:16:24Z |

Und dieselbe Tatsache von der Client-Seite, aus Open WebUIs eigenem Sitzungsspeicher
(`OAuthSessions`, Provider `mcp:nextcloud`):

```
token fields       ['access_token', 'expires_at', 'expires_in', 'issued_at',
                    'refresh_token', 'scope', 'token_type']
has refresh_token  True
token_type         Bearer
scope              nextcloud offline_access
```

## 4. Werkzeugaufruf aus Open WebUI (gueltiger Bearer)

Ausgefuehrt 18:19:17 UTC mit Open WebUIs **eigenem** MCP-Client
(`open_webui.utils.mcp.client.MCPClient`), dem Access-Token aus seinem eigenen
Sitzungsspeicher und dem Header, den `open_webui.utils.tools.bearer_auth_header` baut. Kein
handgeschriebener Client.

```
tools listed  16
tool names    calendar_create_event, calendar_list_events, contacts_search, deck_browse,
              deck_create_card, fetch, files_list, files_read, files_search, files_upload,
              notes_create, notes_read, notes_search, prepare_context, search, unified_search
call_tool     files_search {"query": "mcp-shared-file"} -> 3 Treffer, darunter
              /mcp-share-4c73cd4efd/mcp-shared-file-4c73cd4efd.md (alices Bestand)
```

Im Log des Connectors:

```
Created new transport with session ID: b756ac2643d442cd94595253c4f70a2f
POST /mcp    200 OK
GET  /mcp    200 OK
POST /mcp    202 Accepted
POST /mcp    200 OK
POST /mcp    200 OK
Terminating session: b756ac2643d442cd94595253c4f70a2f
DELETE /mcp  200 OK
```

Die Werkzeugzahl 16 stimmt mit der laufenden Registry und mit
`tests/contract/test_tool_surface.py` ueberein (`assert len(tools) == 16`).

## 5. Gegenprobe: `http` auf einer LAN-Adresse

Zwei Wege, dieselbe Ablehnung.

**a) Direkt am Enforcement-Punkt**, mit der Nutzlast, die Open WebUI schickt (eine Redirect-URI,
`client_name` `Open WebUI`), 18:02:39 UTC:

```
POST /register  redirect_uris=["http://192.168.1.79:3030/oauth/clients/PLACEHOLDER/callback"]
-> HTTP 400
{"error":"invalid_redirect_uri","error_description":"redirect_uris must use https, except loopback addresses of native clients"}

POST /register  redirect_uris=["http://openwebui.lan/oauth/clients/PLACEHOLDER/callback"]
-> HTTP 400
{"error":"invalid_redirect_uri","error_description":"redirect_uris must use https, except loopback addresses of native clients"}
```

Positivkontrolle mit derselben Nutzlast und `http://localhost:3030/...`: **HTTP 201**. Die
Ablehnung liegt am Schema plus Host und an nichts anderem.

**b) Durch Open WebUI selbst**, mit `webui.url` auf `http://192.168.1.79:3030` gestellt,
18:20:22 UTC. Der Text, den ein Admin in Open WebUI sieht:

```
HTTP 400
{"detail":"Failed to register OAuth client: Dynamic client registration failed: {\"error\":\"invalid_redirect_uri\",\"error_description\":\"redirect_uris must use https, except loopback addresses of native clients\"}"}
```

Im Log des Connectors dazu genau das Warnzeichen aus 05-RESEARCH Pitfall 10:

```
POST /mcp                                        401 Unauthorized
GET  /.well-known/oauth-protected-resource/mcp   200 OK
GET  /.well-known/oauth-authorization-server     200 OK
POST /register                                   400 Bad Request
```

`webui.url` wurde danach auf `http://localhost:3030` zurueckgestellt (Vorzustand
wiederhergestellt, T-05-24-Regel).

## 6. Pro-Nutzer-Bindung, serverseitige Haelfte

Open WebUIs Sitzungsspeicher, gefragt nach dem Provider `mcp:nextcloud`:

```
sessions for mcp:nextcloud = 1
  bound to user_id bd500ab7-7c0c-423e-91e3-0969f50f6b22
lookup for the account that authorized: token
lookup for any other account:           none
```

Ein Konto ohne Sitzung bekommt keinen `Authorization`-Header
(`build_tool_server_headers`), und ein `/mcp` ohne Bearer ist bei uns 401 (im selben Lauf
gemessen, Abschnitt 1, erste Zeile). Die Gegenprobe mit einem **zweiten echten**
Open-WebUI-Konto lief danach im Browserteil, siehe Abschnitte 7 und 8. Nebenbefund dieses
Laufs: `POST /api/v1/auths/signup` antwortet nach dem ersten Konto mit 403, weil Open WebUI die
Selbstregistrierung dann selbst schliesst; fuer die Gegenprobe wurde sie wieder freigeschaltet
(`ui.enable_signup`, `ui.default_user_role`).

## 7. Browserteil (Task 2, bestaetigt 2026-08-19)

Vom Orchestrator per Playwright in einem echten Browser durchgefuehrt, nicht von diesem Lauf.
Bestaetigt sind die Punkte 1, 2, 3 und 5 des Checkpoints; Punkt 4 (Werkzeugaufruf im Chat) ist
im Browser nicht durchfuehrbar, weil im Wegwerf-Container kein Modell hinterlegt ist. Der
Werkzeugaufruf selbst ist serverseitig in Abschnitt 4 belegt.

Die gesehene Kette: Toggle im Chat unter Integrationen, Werkzeuge, `Nextcloud MCP Connector`
startet den Flow; Zwischenseite des Connectors "Sign in to continue"; Nextclouds eigene
Login-Flow-v2-Seite; Grant-Seite mit "Aktuell angemeldet als alice"; Consent-Seite des
Connectors mit "You are signed in as alice", App-Name `Open WebUI`, Rueckadresse
`http://localhost:3030/oauth/clients/mcp:nextcloud/callback`, Unverified-client-Warnung und der
Liste, was die Verbindung darf; nach "Approve access" Rueckkehr ohne Fehlermeldung, Status
"Verbunden" und "Available Tools 1" im Eingabefeld.

Zwei Befunde aus dem Browser, die aus dem Quellcode nicht sichtbar waren und beide in die Doku
gewandert sind:

* **Der Zugriff einer Verbindung ist per Default "Privat".** Ein zweites Konto mit der Rolle
  `user` sah den Tool-Server ueberhaupt nicht. Erst nachdem der Admin in der
  Verbindungskonfiguration unter "Zugriff" auf "Oeffentlich" gestellt hatte (Gruppen waeren die
  Alternative), erschien der Eintrag und das Konto konnte sich selbst anmelden. Das ist der
  wahrscheinlichste Grund, warum eine korrekt konfigurierte Verbindung fuer alle anderen
  unsichtbar aussieht. Steht als Stolperstelle 7 in der Doku.
* **Eine im selben Browser offene Nextcloud-Sitzung entscheidet still ueber das Konto.** Der
  Playwright-Browser war noch als `admin` bei Nextcloud angemeldet, und der Login Flow sprang
  deshalb direkt auf die Grant-Seite fuer `admin`. Erst nach dem Abmelden kam die echte
  Anmeldeseite. Die Consent-Seite nennt das Konto ehrlich, aber man kann daran vorbeidruecken.
  Steht als Stolperstelle 8 in der Doku.

## 8. Gegenprobe: zwei Open-WebUI-Konten, zwei Nextcloud-Identitaeten

Nach dem Browserteil existierten zwei Open-WebUI-Konten mit je einer eigenen Autorisierung
(`admin@probe.invalid` als `alice`, `bob@probe.invalid` als `bob`). Gemessen 18:50:20 UTC, je
mit dem gespeicherten Token des Kontos, Open WebUIs eigenem MCP-Client und dem Header aus
`bearer_auth_header`:

```
stored sessions for mcp:nextcloud: 2
--- open webui account admin@probe.invalid (alice) ---
  shared marker  mcp-shared-file-04d2eb7d6d: 1 hit  ['/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md']
  private marker mcp-private-04d2eb7d6d:     1 hit  ['/mcp-private-04d2eb7d6d.md']
--- open webui account bob@probe.invalid (bob) ---
  shared marker  mcp-shared-file-04d2eb7d6d: 1 hit  ['/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md']
  private marker mcp-private-04d2eb7d6d:     0 hits []
```

Beide Richtungen stehen damit in einem Lauf: die Positivkontrolle (bob findet, was alice mit ihm
read-only geteilt hat) und der Negativbeweis (bob findet alices ungeteilte Datei nicht), obwohl
beide durch dieselbe Open-WebUI-Instanz und denselben Connector gehen. Das Berechtigungs-
versprechen haelt also nicht nur in unserer Schicht, sondern ueber einen fremden Mehrbenutzer-
Client hinweg. Die volle Kette ist zusaetzlich in
`tests/integration/test_permission_parity_share.py` (5/5 live, Plan 05-03) belegt.

## 9. Was dieser Lauf NICHT belegt

* Einen Werkzeugaufruf aus dem **Chatfenster** von Open WebUI. Dieser Wegwerf-Container hat kein
  Modell hinterlegt, und ohne Modell entscheidet niemand, ein Werkzeug zu rufen. Belegt ist der
  Aufruf ueber Open WebUIs eigenen MCP-Client mit dem gespeicherten Token des Kontos
  (Abschnitte 4 und 8), also alles ausser der Modellentscheidung. Fuer die Anleitung genuegt
  das: was ein Modell mit einem verbundenen Werkzeug tut, ist keine Eigenschaft dieses Servers.
* Feldnamen, die dieser Lauf nicht gesehen hat, stehen nicht in der Anleitung. Die verwendeten
  sind entweder im Browser gesehen (Integrationen, Werkzeuge, Zugriff, Privat, Oeffentlich,
  Verbunden, Approve access) oder als ausgelieferte Beschriftung im Image belegt
  (`Tool Servers`, `Add Connection`, `Connection Type`, `Streamable HTTP`, `OAuth 2.1`,
  `OAuth 2.1 (Static)`, `Bearer`, `Authenticate`, `Verify Connection`).
* Andere Open-WebUI-Versionen als 0.11.0. Der Abschnitt nennt die gemessene Version und ihren
  Digest, damit ein spaeterer Leser weiss, wogegen er vergleicht.

## Zustand der Umgebung

Waehrend Task 2 absichtlich stehen gelassen, danach abgeraeumt. Wegwerf-Zustand zum Zeitpunkt
des Abraeumens: zwei Open-WebUI-Konten (`admin@probe.invalid` als `alice`, `bob@probe.invalid`
als `bob`) und zwei Autorisierungen im Connector-Store.

```bash
docker rm -f nc-mcp-owui-probe
docker rmi ghcr.io/open-webui/open-webui:main     # 7,16 GB, optional
docker compose -f compose.exapp.yml down          # Volumes behalten
```

Die Volumes bleiben, weil sie die Fixture von 05-03 tragen. Die Prozedur zum Wiederanfahren
steht in STATE.md unter "ExApp-Topologie (Prozedur)".
