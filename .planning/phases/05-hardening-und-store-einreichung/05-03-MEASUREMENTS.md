# 05-03 Rohmessungen: Permission-Parity und Create-only ueber die volle Kette

Alle Messungen am **19.08.2026** auf diesem Windows-Host (Git Bash), gegen die Topologie
`compose.exapp.yml` (Compose-Projekt `nc-mcp-exapp`, Nextcloud 34, AppAPI/HaRP). Die vom Owner
genutzten Instanzen `nc-mcp-test` und `findling-nextcloud` liefen waehrend der ganzen Messung
weiter und wurden nicht angefasst (Nachweis unten, Schritt 9).

Aktive Fixture-Werte dieses Laufs (aus `.env.exapp`, git-ignoriert):

```
NC_MCP_TEST_SHARED_DIR=mcp-share-04d2eb7d6d
NC_MCP_TEST_SHARED_FILE=mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md
NC_MCP_TEST_PRIVATE_FILE=mcp-private-04d2eb7d6d.md
NC_MCP_TEST_SHARED_MARKER=mcp-shared-file-04d2eb7d6d
```

---

## 1. Skip ohne Topologie (15:51:56Z, vor dem Anfahren)

```
$ uv run --no-sync pytest tests/integration/test_permission_parity_share.py -q -m integration
sssss                                                                    [100%]
```

Fuenf Skips, Exit 0, kein Fehler: ohne `.env.exapp` im Environment (NC_MCP_URL leer) skippt die
Datei, wie es die uebrige Integrationsebene tut. Die Standardsuite bleibt davon unberuehrt
(Schritt 8).

## 2. Topologie anfahren (15:52:24Z bis 15:52:41Z)

```
$ export HP_SHARED_KEY=$(openssl rand -hex 32) && docker compose -f compose.exapp.yml up -d --wait
 Container nc-mcp-exapp-nc Healthy
 Container nc-mcp-exapp-caddy Healthy
 Container nc-mcp-exapp-registry Healthy
 Container nc-mcp-exapp-harp Healthy
UP-EXIT=0
```

Danach die Wiederanfahr-Prozedur aus STATE.md woertlich:

```
$ occ app_api:app:unregister mcp_connector --silent --force
$ occ app_api:daemon:unregister harp_proxy_docker
Daemon config unregistered.
$ docker rm -f nc_app_mcp_connector      -> No such container (war schon entfernt)
$ occ app_api:app:list
ExApps:                                   (leer, wie erwartet)
```

## 3. Bootstrap mit der neuen Fixture (15:53:06Z bis 15:53:54Z, 48 s)

```
$ bash scripts/bootstrap_exapp.sh
...
files home alice: initialised
files home bob: initialised
share folder /mcp-share-4c73cd4efd: created
file alice/mcp-share-4c73cd4efd/mcp-shared-file-4c73cd4efd.md: created
file alice/mcp-private-4c73cd4efd.md: created
share auto accept: on (test instance)
curl: (23) client returned ERROR on write of 598 bytes      <- Befund, siehe Schritt 4
read-only share /mcp-share-4c73cd4efd to bob: present (attempt 2)
...
image 127.0.0.1:5000/mcp_connector:0.1.0: built and pushed (sha256:4d80694b...)
image digest sha256:4d80694b...: unchanged since the push
exapp mcp_connector: registered and deployed
exapp mcp_connector: enabled
app passwords: created for alice and bob
wrote .env.exapp
ExApps:
mcp_connector (MCP Connector): 0.1.0 [enabled]
BOOTSTRAP-EXIT=0
```

Die Fixture stand also beim ersten Lauf, aber curl meldete einen Schreibfehler.

## 4. Befund A: `-o /dev/null` scheitert unter MSYS_NO_PATHCONV=1

Das Skript exportiert `MSYS_NO_PATHCONV=1` (fuer die Route-Regexe der Registrierung). Damit
uebergibt Git Bash den Pfad `/dev/null` unveraendert an das native `curl.exe`, und dort gibt es
diesen Pfad nicht. Gegenprobe, direkt gemessen:

```
$ MSYS_NO_PATHCONV=1 curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/status.php
curl: (23) client returned ERROR on write of 170 bytes
200
exit=23

$ curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/status.php
200
exit=0
```

Fix: `nc_status` liest den Rumpf in eine Variable und haengt den Status mit
`-w '\n%{http_code}'` an, statt ihn nach `/dev/null` zu schreiben. Danach (15:56:46Z):

```
share folder /mcp-share-896e373b3f: created            (frischer Suffix, weil der alte
file alice/mcp-share-896e373b3f/...md: created          bewusst auf "not-hex" gesetzt wurde)
file alice/mcp-private-896e373b3f.md: created
share auto accept: on (test instance)
share /mcp-share-896e373b3f to bob: create answered 200
read-only share /mcp-share-896e373b3f to bob: present (attempt 2)
```

Kein `curl: (23)` mehr, und der Create-Status steht jetzt im Log (200 = OCS v2 ok).

## 5. Idempotenz (15:57:28Z und 16:01:04Z)

Zweiter und dritter Lauf ohne Aenderung an `.env.exapp`:

```
share folder /mcp-share-04d2eb7d6d: already there
file alice/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md: already there
file alice/mcp-private-04d2eb7d6d.md: already there
share auto accept: on (test instance)
read-only share /mcp-share-04d2eb7d6d to bob: present (attempt 1)
EXIT=0
NC_MCP_TEST_SHARED_DIR=mcp-share-04d2eb7d6d
```

Kein Create, derselbe Suffix, Nachweis beim ersten Versuch: die Fixture ist ein No-op auf einer
Instanz, die sie schon hat.

## 6. Befund B: Git Bash schreibt exportierte absolute Pfade um

Der erste Live-Lauf der Testdatei (15:58:04Z) scheiterte an drei Tests mit:

```
AssertionError: the tool call ended in an error: ['Error executing tool files_read:
File not found: /C:/Program Files/Git/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md.
Hint: List the parent folder first to get the exact spelling of the path.']
```

`set -a && . ./.env.exapp && set +a` exportiert `NC_MCP_TEST_SHARED_FILE=/mcp-share-...`; beim
Start eines nativen Prozesses (uv/pytest) ersetzt MSYS den fuehrenden Schraegstrich durch das
Installationsverzeichnis von Git Bash. Fix an der Quelle: die drei Pfade wandern relativ zur
Nutzerwurzel in die Verbindungsdatei (`${SHARED_DIR#/}`), der Test setzt den Schraegstrich
wieder davor, und ein Gate in `tests/unit/test_exapp_env_setup.py` haelt die absolute
Schreibweise fern. `share_suffix` akzeptiert beide Schreibweisen, damit eine Datei aus einem
frueheren Lauf ihre Objekte behaelt (16:01:04Z gemessen: derselbe Suffix bleibt).

## 7. Der Live-Lauf (16:01:31Z bis 16:01:34Z)

```
$ set -a && . ./.env.exapp && set +a
$ uv run --no-sync pytest tests/integration/test_permission_parity_share.py -m integration
collected 5 items
tests\integration\test_permission_parity_share.py .....                  [100%]
5 passed in 2.50s
EXIT=0
```

Fuenf Tests, fuenf gruen, kein Skip. Die Rohantworten der zehn beteiligten Werkzeugaufrufe,
separat gemessen (16:02:54Z, gleiche Topologie, gleiche App-Passwoerter):

```
A bob laedt in die read-only-Freigabe:
  is_error=True Error executing tool files_upload: No permission to write to
  /mcp-share-04d2eb7d6d/probe-b26cc5da.md. Hint: Check the share permissions of the
  target folder in Nextcloud.
B bob laedt in seine eigene Wurzel:
  is_error=False {"path":"/probe-own-9cdf6a5c.md","etag":"\"927af81d...\"","created":true}
C alice legt eine neue Datei an:
  is_error=False {"path":"/probe-create-only-1fa8ce86.md","etag":"\"29f5f19d...\"","created":true}
D alice laedt denselben Pfad ein zweites Mal:
  is_error=True Error executing tool files_upload: A file already exists at
  /probe-create-only-1fa8ce86.md. Hint: This server never overwrites files.
  Choose a different name.
E bob liest die geteilte Datei:
  is_error=False {"path":"/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md",
  "content":"# mcp-shared-file-04d2eb7d6d (fixture of scripts/bootstrap_exapp.sh, plan 05-03)",
  "size":80,"content_type":"text/markdown","truncated":false}
F bob sucht die ungeteilte Datei (files_search):
  count=0, items=[]
G alice sucht dieselbe Datei (files_search):
  count=1, items=[{"path":"/mcp-private-04d2eb7d6d.md",...,"id":"file:418"}]
H bob sucht die geteilte Datei (files_search):
  count=1, items=[{"path":"/mcp-share-04d2eb7d6d/mcp-shared-file-04d2eb7d6d.md",...}]
I bob sucht die geteilte Datei (unified_search):
  count=1, results=[{"id":"file:417","title":"mcp-shared-file-04d2eb7d6d.md",
  "subline":"in mcp-share-04d2eb7d6d","provider":"files","kind":"file"}]
J bob sucht die ungeteilte Datei (unified_search):
  count=0, results=[]
```

A gegen B ist die Aussage von T-05-13: derselbe create-only-Aufruf, einmal abgelehnt und einmal
erfolgreich, also entscheidet Nextcloud und nicht das Werkzeug. C gegen D ist T-05-14 ueber die
volle Kette. F gegen G ist die Nicht-Tautologie: das Objekt existiert und ist indexiert (alice
findet es), bob findet es trotzdem nicht. H und I sind die positive Haelfte, die zwei Konten
ohne Freigabe gar nicht messen koennen.

## 8. Gegenproben zum Live-Lauf (16:02Z)

Ein gruener Lauf ist erst dann eine Messung, wenn ein falscher Aufbau rot wird:

```
Probe A: NC_MCP_TEST_PRIVATE_FILE auf die geteilte Datei gesetzt
  -> 5 errors in 0.73s   (die Fixture-Wache lehnt den Aufbau ab: eine Datei innerhalb der
                          Freigabe darf bob sehen, also waere die Leak-Aussage sinnlos)

Probe B: NC_MCP_TEST_SHARED_MARKER auf ein Token gesetzt, das kein Objekt benennt
  -> 3 failed, 2 passed in 2.53s
     assert 'mcp-shared-file-doesnotexist' in
            '# mcp-shared-file-04d2eb7d6d (fixture of scripts/bootstrap_exapp.sh, plan 05-03)'
```

Probe B zeigt zugleich, dass der Inhalt der geteilten Datei tatsaechlich ueber die Kette bei bob
ankommt (die Fehlermeldung enthaelt ihn woertlich), und dass die drei positiven Aussagen an den
echten Objekten haengen und nicht an der Form der Aufrufe.

## 9. Standardsuite, Werkzeuge und Zustand danach

```
$ uv run --no-sync pytest -q                        -> alle gruen (Integrationsebene deselektiert)
$ uv run --no-sync ruff check .                     -> All checks passed!
$ uv run --no-sync ruff format --check .            -> 160 files already formatted
$ uv run --no-sync pyright                          -> 0 errors, 0 warnings, 0 informations
$ uv run --no-sync vulture src scripts vulture_whitelist.py -> clean
$ bash -n scripts/bootstrap_exapp.sh                -> Exit 0
$ grep -c "BasicAuth\|Credentials(" tests/integration/test_permission_parity_share.py -> 0
$ grep -c "permissions=1" scripts/bootstrap_exapp.sh -> 2
$ grep -v '^#' scripts/bootstrap_exapp.sh | grep -c "shareType=0" -> 1
$ grep -v '^#' scripts/bootstrap_exapp.sh | grep -c "NC_MCP_TEST_SHARED_DIR\|...\|MARKER" -> 5
```

Topologie danach heruntergefahren, Volumes erhalten (Zustand wie in STATE.md beschrieben):

```
$ docker compose -f compose.exapp.yml down
 Container nc-mcp-exapp-harp Removed
 Container nc-mcp-exapp-caddy Removed
 Container nc-mcp-exapp-nc Removed
$ docker stop nc_app_mcp_connector && docker rm nc_app_mcp_connector
$ docker network rm nc-mcp-exapp-net
$ docker ps --format '{{.Names}}'
findling-nextcloud
nc-mcp-test
$ docker volume ls | grep nc-mcp-exapp
nc-mcp-exapp_nextcloud-exapp-data
nc-mcp-exapp_registry-exapp-data
nc_app_mcp_connector_data
```

Die beiden Owner-Instanzen laufen unveraendert weiter, die drei Volumes der Wegwerf-Topologie
sind erhalten, also findet ein naechster Lauf dieselbe Fixture wieder vor.

## 10. Offene Punkte aus dieser Messung

- Auf der Instanz liegen zwei ungenutzte Fixture-Staende (`mcp-share-4c73cd4efd` und
  `mcp-share-896e373b3f`) samt ihren Freigaben. Sie stammen aus den beiden Laeufen mit bewusst
  invalidiertem Suffix (Schritt 4), tragen keinen der aktiven Marker und stoeren keine Messung.
  Kein Werkzeug dieses Servers kann loeschen, und der Bootstrap tut es aus demselben Grund
  nicht; wer sie los werden will, faehrt die Topologie mit `down -v` neu auf.
- Der Nextcloud-AIO-Smoke (D-31) und der Linux-socat-Loop (WR-12) bleiben offen, wie in
  STATE.md vermerkt; beide gehoeren nicht zu diesem Plan.
