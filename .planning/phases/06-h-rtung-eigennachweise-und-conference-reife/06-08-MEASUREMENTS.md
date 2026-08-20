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
