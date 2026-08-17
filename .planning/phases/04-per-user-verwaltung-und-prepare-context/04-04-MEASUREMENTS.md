# Plan 04-04: Rohmessungen der Live-Abnahme

Arbeitsnotizen des Live-Laufs vom **2026-08-17**. Das SUMMARY ist aus dieser Datei
geschrieben; sie bleibt liegen, damit die Zahlen auch später ihren Befehl behalten.

Topologie: `compose.exapp.yml` (Docker), Nextcloud 34 (`nc-mcp-exapp-nc`), AppAPI 34.0.3,
HaRP `release`, Caddy 2, lokale Registry, Port 8081. Die Owner-Instanzen `nc-mcp-test` und
`findling-nextcloud` wurden nicht angefasst.

---

## Schritt 0: Neubau, sonst misst der Lauf Phase 3

Der laufende ExApp-Container stammte vom Image `2026-08-16T08:53:58Z`, also von vor
Plan 04-01. Prozedur wörtlich aus `.planning/STATE.md`:

```bash
export HP_SHARED_KEY=$(docker exec nc-mcp-exapp-harp printenv HP_SHARED_KEY)
docker compose -f compose.exapp.yml exec -T --user www-data nextcloud \
  php occ app_api:app:unregister mcp_connector --silent --force
docker compose -f compose.exapp.yml exec -T --user www-data nextcloud \
  php occ app_api:daemon:unregister harp_proxy_docker
bash scripts/bootstrap_exapp.sh
```

Antwort (gekürzt):

```text
daemon harp_proxy_docker: registered
image 127.0.0.1:5000/mcp_connector:0.1.0: built and pushed
  (sha256:de4b0865a187421fcf36493a8d49b92cd4a5042f5b660373b7eb3fae7499b564)
image digest sha256:de4b08...9b564: unchanged since the push
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
ExApps: mcp_connector (MCP Connector): 0.1.0 [enabled]
Ready. The app answers under: http://127.0.0.1:8081/exapps/mcp_connector/mcp
```

Das `enabled`-Ereignis dieser Zeile ist gleichzeitig der Auslöser für Beweis 1: die
Registrierung der Settings-Form läuft im `/enabled`-Handler.

---

## Beweis 1: der Settings-Wegweiser steht in Nextcloud

### 1a: die Form ist registriert und wird ausgeliefert

```bash
curl -s -u admin:admin-exapp-pw -H "OCS-APIRequest: true" -H "Accept: application/json" \
  "http://127.0.0.1:8081/ocs/v2.php/settings/api/declarative/forms"
```

Antwort (nur der eigene Eintrag; die Instanz liefert daneben
`dav-admin-system-address-book` und `mail-provider-support`):

```json
{
  "id": "mcp_connector_settings",
  "priority": 10,
  "section_type": "personal",
  "section_id": "security",
  "title": "MCP Connector",
  "description": "Assistant apps such as Claude or ChatGPT can reach your files, calendar, notes, contacts and Deck cards through this connector, exactly as far as your own account reaches. Your connected apps and the switch that pauses them are at http://127.0.0.1:8081/exapps/mcp_connector/connections.",
  "doc_url": "http://127.0.0.1:8081/exapps/mcp_connector/connections",
  "fields": [],
  "storage_type": "external",
  "app": "mcp_connector"
}
```

`fields` ist leer, `section_id` ist `security`, `storage_type` hat AppAPI wie gemessen auf
`external` gesetzt, und beide URLs tragen die öffentliche Adresse, nicht `http://caddy`.

### 1b: die persönliche Security-Seite liefert die Form aus

```bash
curl -s -u admin:admin-exapp-pw "http://127.0.0.1:8081/settings/user/security" -o sec.html
grep -c "mcp_connector_settings" sec.html
tr '>' '>\n' < sec.html | grep "mcp_connector_settings"
grep -o 'id="initial-state-settings-declarative-settings-forms" value="[^"]*"' sec.html \
  | sed 's/.*value="//; s/"$//' | base64 -d
```

Antwort:

```text
http=200, 33252 Bytes
1
<div id="mcp_connector_mcp_connector_settings"></div>
[{"id":"mcp_connector_settings","priority":10,"section_type":"personal",
  "section_id":"security","title":"MCP Connector","description":"Assistant apps such as
  Claude or ChatGPT ... are at http://127.0.0.1:8081/exapps/mcp_connector/connections.",
  "doc_url":"http://127.0.0.1:8081/exapps/mcp_connector/connections","fields":[],
  "storage_type":"external","app":"mcp_connector"}]
```

Die Seite trägt also beides: den Initial-State mit der Form **und** den Mount-Punkt
`<div id="mcp_connector_mcp_connector_settings">`, an den der Vue-Renderer den Abschnitt
zeichnet. Damit ist Assumption A1 auf Datenlieferungs- und Mount-Ebene geschlossen. Nicht
gemessen bleibt der gerenderte Pixel: im Lauf war kein Browser beteiligt.

---

## Beweis 2: die Schalter-Kette, live über die volle Kette

Alle Zeilen aus einem Lauf des Live-Skripts (Sitzungs-Technik und OAuth-Flow aus
`scripts/oauth_flow_check.py`: `connect`, `tool_call`, `revoke`, `request_token_of`):

```bash
set -a && . ./.env.exapp && set +a
uv run --no-sync python <live-proof-skript>   # Quelltext siehe Anhang unten
```

```text
[connect]   POST /register -> 201 | cache_control=no-store | client_id=e86c6c81-b5b...
[beweis 2]  connected: an OAuth access token for the test account is in hand
[beweis 2]  tools/list over the full chain: 16 tools
[beweis 2]  tools/call prepare_context before the pause -> 200 in 0.83s (3 hits)
[beweis 2]  raw POST /mcp before the pause -> 400 (transport, served)
[beweis 2]  the switch form of the page offers action=pause
[beweis 2]  POST /connections action=pause -> 200 | state=paused
[beweis 2]  POST /mcp after the pause -> 403 |
            body={"error": "access_disabled", "error_description": "MCP access is switched
            off for this Nextcloud account. The owner of the account can switch it back on
            on the connector's connections page, linked in Nextcloud under Settings,
            Security, MCP Connector."} |
            www_authenticate=False | cache-control=no-store
[beweis 2]  tools/call after the pause -> refused: ExceptionGroup
[beweis 2]  POST /connections action=resume -> 200 | state=on
[beweis 2]  tools/call prepare_context after the resume, same token -> 200 in 0.82s
```

Lesehilfe zu den zwei Sonden:

- `tools/call` ist die vollständige MCP-Sitzung des SDK. Vor dem Pausieren 200, nach dem
  Pausieren scheitert schon der Sitzungsaufbau (das SDK bündelt den Abbruch in eine
  `ExceptionGroup`), nach dem Freigeben wieder 200 **mit demselben Token**: pausieren
  trennt nichts (D-46).
- Der rohe `POST /mcp` ist die Sonde, die die Antwort auf dem Draht zeigt. Ohne Sitzung
  antwortet der Transport 400, das heißt die Grenze hat den Request durchgelassen; im
  pausierten Zustand kommt er über die Grenze nicht hinaus: 403, `access_disabled`, ohne
  `WWW-Authenticate`, mit `no-store`.

---

## Beweis 3: SC 5 unverschlechtert

```bash
set -a && . ./.env.exapp && set +a
uv run --no-sync python scripts/oauth_flow_check.py \
  http://127.0.0.1:8081/exapps/mcp_connector --measure
```

Exit-Code 0, `all steps answered as the specification and this deployment require`. Die
beiden Messzeilen:

```text
[sc 5] 5 accepted MCP calls -> 6 Nextcloud requests (1.2 per call):
       ['GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector']
[sc 5] 5 refused  MCP calls -> 5 Nextcloud requests (1.0 per call):
       ['GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector']
[sc 5] POST /token -> 429 | attempts=11 | retry_after=300
[sc 5] GET /ocs/v2.php/cloud/user -> 200 | as_user=alice
```

Zahlen und Pfad sind **zeichengleich** mit dem in `03-VERIFICATION.md` dokumentierten
Phase-3-Ergebnis. Ein MCP-Request, der einen `Authorization`-Header trägt, kostet genau
einen Nextcloud-Roundtrip, und der gehört HaRP (`user-info`), nicht uns; die sechste
Anfrage der fünf akzeptierten Aufrufe ist der Sitzungsaufbau. Das Schalter-Gate aus 04-01
kostet null: es ist ein lokaler SQLite-Read.

Weitere Zeilen desselben Laufs, die zur Phase gehören:

```text
[step 7] POST /mcp -> 200 | tools=16 | transport=streamable-http
[step 7] tool notes_create -> 200 | note_id=note:391 | as_user=alice
[sc 3]   GET /connect/wait -> 200 | signed_in_as=alice | credential=72 characters, shown once
```

---

## Beweis 4: /connections von außen

```text
[beweis 4] GET /connections with a session    -> 200 | cache-control=no-store | state=on
[beweis 4] GET /connections without a session -> 403 |
           heading=Sign in to see your connections | cache-control=no-store
```

Die Antwort ohne Sitzung ist E8 mit 403 und ohne Link auf irgendeine Anmeldeseite; die
Antwort mit Sitzung ist die Liste, beide mit `no-store`.

---

## Beweis 5: prepare_context live, kurz und voll

Vor der Messung wurden über die Tool-Oberfläche selbst drei Objekte angelegt (Notiz,
Textdatei, Termin), damit die Antwort Treffer aus mehr als einer Quelle tragen kann; alle
drei wurden am Ende wieder entfernt.

```text
[seed] notes_create          -> note:394 in 0.24s
[seed] files_upload          -> {"path": "/budget-plan-0404.txt", "created": true} in 0.23s
[seed] calendar_create_event -> event:personal:a4cfb4f8-...ics in 0.21s

[beweis 5] prepare_context detail=short -> 200 in 0.84s |
           buckets={'file': 2, 'note': 1, 'card': 0, 'other': 0} |
           providers=['files', 'notes'] | events=2 | degraded=[] |
           keys=['events', 'note', 'query', 'results', 'window']
[beweis 5] prepare_context detail=full  -> 200 in 0.99s |
           buckets={'file': 2, 'note': 1, 'card': 0, 'other': 0} |
           providers=['files', 'notes'] | events=2 | degraded=[] |
           keys=['events', 'note', 'query', 'results', 'window']
```

Die volle Antwort der Voll-Form (gekürzt um die zweite Datei):

```json
{
  "query": "budget",
  "window": {"start": "2026-08-17T14:22:41+00:00", "end": "2026-08-24T14:22:41+00:00"},
  "events": [
    {"id": "event:personal:2b9e00c4-....ics", "summary": "Budget review",
     "start": "2026-08-18T14:21:11+00:00", "end": "2026-08-18T15:21:11+00:00",
     "all_day": false, "calendar": "personal"},
    {"id": "event:personal:a4cfb4f8-....ics", "summary": "Budget review",
     "start": "2026-08-18T14:22:37+00:00", "end": "2026-08-18T15:22:37+00:00",
     "all_day": false, "calendar": "personal"}
  ],
  "results": {
    "file": [
      {"id": "file:395", "title": "budget-plan-0404.txt", "provider": "files",
       "kind": "file", "excerpt": "Budget plan for the review: three lines about it."},
      {"id": "file:394", "title": "Budget meeting prep.md", "provider": "files",
       "kind": "file", "excerpt": "The budget for the connector phase, notes for the review."}
    ],
    "note": [
      {"id": "note:394", "title": "Budget meeting prep", "provider": "notes",
       "kind": "note", "excerpt": "The budget for the connector phase, notes for the review."}
    ],
    "card": [], "other": []
  },
  "note": "matched on names and metadata; file contents are not indexed"
}
```

Befund:

- Herkunft ist Struktur, nicht Prosa: jeder Treffer trägt `provider` und `kind`, die
  Buckets sind benannt, das Fenster steht als eigenes Objekt in der Antwort.
- Drei Quellen in einer Antwort: `files`, `notes` und der Kalender (`events`). Deck und
  Kontakte lieferten zu diesem Suchwort nichts, deshalb sind `card` und `other` leer.
- Die `degraded`-Liste ist leer und deshalb laut Kontrakt gar nicht erst im Objekt: der
  Schlüssel erscheint nur, wenn es etwas zu melden gibt. Kein Teil-Ausfall im Lauf.
- Nur die Voll-Form trägt `excerpt`; die Kurz-Form ist zeichengleich ohne die Auszüge.
- **Antwortzeiten: 0.84 s kurz, 0.99 s voll**, jeweils über die volle Kette. Das schließt
  Assumption A2 von der gesunden Seite: die Budgets (10 s Kalender, 5 s je Auszug, 15 s je
  Suchprovider) greifen nur, wenn wirklich etwas hängt. Die Zahl steht als Kommentar an
  `CALENDAR_BUDGET` in `src/mcp_connector/tools/context.py`.

---

## Aufräumen nach dem Lauf

```text
[cleanup] DELETE /apps/notes/api/v1/notes -> 200 | note=note:394
[cleanup] DELETE budget-plan-0404.txt -> 204
[cleanup] DELETE calendar a4cfb4f8-....ics -> 204   (der Termin des abgebrochenen ersten
                                                     Laufs, 2b9e00c4, danach ebenfalls 204)
[cleanup] POST /revoke -> 200
[cleanup] POST /connections action=disconnect -> 200   (x 42, alle Altverbindungen von alice
                                                        aus den Läufen der Phasen 3 und 4)
[cleanup] rows left on the page: 0
```

Kein Tool dieses Servers löscht etwas, deshalb geht das Aufräumen der drei Objekte direkt
an Nextcloud mit dem App-Passwort des Nutzers, genau wie in `scripts/oauth_flow_check.py`.
Die Verbindungen selbst wurden über die Seite getrennt, also über den Pfad, den dieser Plan
abnimmt.

---

## Anhang: das Live-Skript

Das Skript für die Beweise 2, 4 und 5 lag bewusst außerhalb des Repos (Wegwerf-Werkzeug,
kein Produktions- oder Testartefakt). Es besteht aus drei Bausteinen, alle aus
`scripts/oauth_flow_check.py` importiert:

```python
import sys; sys.path.insert(0, "scripts")
import oauth_flow_check as ofc

BASE = "http://127.0.0.1:8081/exapps/mcp_connector"
NC = "http://127.0.0.1:8081"

# 1. Eine echte OAuth-Verbindung inklusive Anmeldung und Zustimmung
connection = ofc.connect(BASE, NC, user, password, name="Live proof 04-04")

# 2. Eine Nextcloud-Sitzung für die Seite: GET /login, requesttoken, POST /login (303)
#    -> httpx.Client mit den Cookies, mit dem /connections aufgerufen und gepostet wird

# 3. Zwei Sonden gegen /mcp
payload = ofc.payload_of(asyncio.run(ofc.tool_call(BASE, connection.access_token,
                                                   "prepare_context", {"query": "budget"})))
raw = httpx.Client().post(f"{BASE}/mcp",
                          headers={"Authorization": f"Bearer {connection.access_token}",
                                   "Accept": "application/json, text/event-stream"},
                          json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
```

Die Formularwerte der Seite (`action`, `confirm`, `connection`) werden aus dem
ausgelieferten HTML gelesen, nicht selbst gebaut: der Anti-Fälschungs-Wert ist ein HMAC
unter dem Datenschlüssel der Installation und kann von außen nicht erzeugt werden.
