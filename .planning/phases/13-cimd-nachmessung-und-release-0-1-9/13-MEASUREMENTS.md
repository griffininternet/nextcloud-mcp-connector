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
