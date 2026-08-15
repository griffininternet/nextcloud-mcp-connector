---
phase: 02-exapp-shell
plan: 03
subsystem: infra
tags: [docker, buildx, uv, frpc, harp, appapi, exapp, manifest, ci]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: entry_exapp.main (uds gegen TCP, Startvalidierung), Console-Script nc-mcp-exapp, lifecycle_routes mit /heartbeat
provides:
  - "Dockerfile: zweistufiges, non-root ExApp-Image (python:3.13-slim, uv 0.11.7 gepinnt, uv sync --frozen --no-dev --no-editable) fuer amd64 und arm64"
  - "frpc 0.61.1 im Image, per SHA256 aus der HaRP-README verifiziert (sha256sum -c bricht den Bau ab)"
  - "start.sh woertlich aus HaRP exapps_dev/, mit Herkunftskopf; /frpc.toml als vorab angelegte Datei des unprivilegierten Nutzers"
  - "healthcheck.sh: /heartbeat ueber den Unix-Socket (HaRP) oder ueber APP_PORT, plus HEALTHCHECK-Instruktion"
  - "appinfo/info.xml: ExApp-Manifest mit docker-install und genau zwei engen Routen"
  - "tests/unit/test_exapp_env_setup.py: 23 Dateizusicherungen ohne Docker inklusive zweier Gegenproben fuer das Manifest-Gate"
  - "CI-Job image: docker buildx fuer amd64 und arm64, ohne Veroeffentlichung"
affects: [02-04 HaRP-Testtopologie und Installation, 02-05 Permission-Parity, 05 Store-Einreichung und Registry-Publishing]

# Tech tracking
tech-stack:
  added:
    - "Docker-Image-Bau (docker buildx, multi-arch amd64 und arm64)"
    - "frpc 0.61.1 als Binary im Image (kein Python-Paket, SHA256-Pin)"
    - "uv 0.11.7 als gepinntes Installer-Binary aus ghcr.io/astral-sh/uv"
  patterns:
    - "Manifest-Pruefung als Funktion ueber ein Wurzelelement statt als Assert-Kette, damit eine Gegenprobe das Gate rot faerben kann"
    - "Regex-Sonde statt Wortliste: jede deklarierte Route wird gegen /heartbeat, /init und /enabled gematcht"
    - "Non-root im Image durch vorab angelegte Zieldateien und -verzeichnisse statt durch gelockerte Rechte auf /"

key-files:
  created:
    - Dockerfile
    - .dockerignore
    - start.sh
    - healthcheck.sh
    - appinfo/info.xml
    - tests/unit/test_exapp_env_setup.py
  modified:
    - .gitattributes
    - .github/workflows/ci.yml

key-decisions:
  - "uv sync laeuft mit --no-editable, damit das Laufzeit-Image nur die virtuelle Umgebung traegt und keine Kopie von src"
  - "/frpc.toml wird im Image als leere Datei mit Eigentuemer 10001 angelegt: start.sh bleibt woertlich, und ein unprivilegierter Prozess darf eine eigene Datei kuerzen, aber keine in / anlegen"
  - "Das Volume-Ziel /nc_app_mcp_connector_data wird im Image mit Eigentuemer 10001 angelegt, weil ein frisches Docker-Volume Eigentuemer und Modus des ueberdeckten Verzeichnisses erbt"
  - "Der Manifest-Gate prueft nicht nur eine Wortliste weiter Regexe, sondern matcht jede Route gegen die drei Lifecycle-Pfade"
  - "Der CI-Job image bekommt zusaetzlich docker/setup-qemu-action, weil die arm64-Haelfte sonst auf einem amd64-Runner nicht laufen kann"
  - "EXAPP-01 bleibt Pending: das Paket ist gebaut, der Installationsnachweis durch den Deploy Daemon gehoert zu 02-04"

patterns-established:
  - "Container-Dateien tragen ihre Herkunft und ihr Abrufdatum im Kopf, wenn sie aus einem fremden Repo stammen"
  - "Jede Pruefdatei ohne Docker haelt genau die Wahrheit, die sonst erst beim Deploy auffaellt"
  - "Ein Sicherheits-Gate bekommt eine Gegenprobe, sonst ist unbewiesen, dass es ausloest"

requirements-completed: []

# Metrics
duration: 32 min
completed: 2026-08-15
---

# Phase 2 Plan 03: Container-Image und ExApp-Manifest Summary

**Ein 79-MB-ExApp-Image fuer amd64 und arm64, das als uid 10001 laeuft, frpc per SHA256 verifiziert mitbringt und seinen Gesundheitszustand in beiden Transportvarianten ehrlich meldet, dazu ein Manifest, das genau zwei Routen oeffnet und die drei Lifecycle-Pfade nachweislich nicht erreichbar macht.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-08-15T06:24:00Z
- **Completed:** 2026-08-15T06:56:00Z
- **Tasks:** 3
- **Files modified:** 8 (6 neu, 2 geaendert)

## Accomplishments

- `Dockerfile`: zwei Stufen auf `python:3.13-slim`. Die Baustufe zieht uv als gepinntes Binary aus `ghcr.io/astral-sh/uv:0.11.7` und loest die Umgebung mit `uv sync --frozen --no-dev --no-editable` auf; die Laufzeitstufe traegt nur die fertige virtuelle Umgebung, `curl`, `ca-certificates` und `frpc`. Ergebnis: 79 MB, `USER 10001:10001`, kein uv und kein Build-Werkzeug im Endimage.
- frpc 0.61.1 wird je Zielarchitektur (`TARGETARCH`) geladen und mit `sha256sum -c` gegen die beiden Pruefsummen aus der HaRP-README geprueft. Eine Abweichung beendet den Bau, statt ein fremdes Binary auszuliefern (T-02-SC).
- `start.sh` liegt woertlich so im Repo, wie HaRP es veroeffentlicht, mit Herkunftskopf (Repo, Pfad, Branch, Abrufdatum) ueber dem unveraenderten Original. Damit der non-root-Prozess die von ihm erzeugte `/frpc.toml` schreiben kann, legt das Image die Datei vorab mit Eigentuemer 10001 an.
- `healthcheck.sh` kennt beide Transportwege: liegt `HP_SHARED_KEY` an, probt es `/heartbeat` ueber den Unix-Socket, sonst ueber `127.0.0.1:${APP_PORT}`. Beide Wege wurden lokal gegen laufende Container belegt, der Container meldete jeweils nach rund 8 Sekunden `healthy`.
- `appinfo/info.xml`: Manifest mit den eingefrorenen Bezeichnern, `docker-install` auf `ghcr.io` mit `image-tag` gleich `version`, und genau zwei Routen (`^/mcp/?$` als USER, `^/\.well-known/` als PUBLIC). Kein `scopes`, kein `bruteforce_protection`, keine `401` in der Datei.
- `tests/unit/test_exapp_env_setup.py`: 23 Faelle ohne Docker und ohne Netz. Die Manifest-Pruefung ist eine eigene Funktion ueber das Wurzelelement, und zwei Gegenproben belegen, dass sie bei einer `.*`-PUBLIC-Route und bei einem Throttler auf 401 rot wird.
- CI-Job `image` baut amd64 und arm64 mit `docker buildx --output type=cacheonly`. Nichts wird veroeffentlicht (D-25), im ganzen Workflow steht kein Registry-Login und kein Push-Schritt.

## Task Commits

1. **Task 1: Container-Image, Startskript und Healthcheck** - `066b2dd` (feat)
2. **Task 2: ExApp-Manifest mit genau zwei engen Routen** - `e6adf93` (feat)
3. **Task 3: Dateizusicherungen ohne Docker und CI-Buildschritt** - `520019a` (test)

## Files Created/Modified

- `Dockerfile` - zweistufiger Bau, gepinntes uv, frpc mit SHA256, non-root uid 10001, OCI-Labels, HEALTHCHECK, `ENTRYPOINT ["/start.sh", "nc-mcp-exapp"]`, kein EXPOSE
- `.dockerignore` - haelt `.git`, `.planning`, `.venv`, `tests`, `docs`, `scripts`, `.env*`, `.harp-certs` und `compose*.yml` aus dem Bau-Kontext
- `start.sh` - HaRP-Original mit Herkunftskopf, ausfuehrbares Bit im Index (100755)
- `healthcheck.sh` - POSIX-sh, `exec curl`, beide Transportvarianten, ausfuehrbares Bit im Index (100755)
- `appinfo/info.xml` - ExApp-Manifest, zwei Routen, Kommentarblock mit der Begruendung fuer die nicht deklarierten Lifecycle-Pfade
- `tests/unit/test_exapp_env_setup.py` - CRLF-Verbot, HEALTHCHECK, non-root USER, ENTRYPOINT, frpc-Pruefsumme, ENV-Gate, `.dockerignore`, start.sh-Herkunft, healthcheck-Weiche, Manifest-Gate plus zwei Gegenproben
- `.gitattributes` - die bestehende LF-Begruendung erweitert, `Dockerfile text eol=lf` dazu
- `.github/workflows/ci.yml` - neuer Job `image` (QEMU, buildx, Bau ohne Veroeffentlichung); kein bestehender Schritt wurde ersetzt

## Decisions Made

- **`--no-editable` beim `uv sync`.** Ein editierbarer Einbau haette `src` auch im Laufzeitimage gebraucht. So traegt die Laufzeitstufe nur `/app/.venv`, und `nc-mcp-exapp` liegt als fertiges Skript darin (`/app/.venv/bin/nc-mcp-exapp`, im Container belegt).
- **`/frpc.toml` vorab anlegen statt Rechte auf `/` lockern.** `start.sh` bleibt damit woertlich das Original. Ein unprivilegierter Prozess darf eine Datei, die ihm gehoert, per Umlenkung kuerzen und neu fuellen; ein Schreibrecht auf `/` waere die deutlich groessere Zugestaendnis gewesen.
- **Volume-Ziel im Image anlegen.** AppAPI mountet `nc_app_<appid>_data` nach `/nc_app_<appid>_data` (`DockerActions::buildDefaultExAppVolume`, am Quellcode geprueft). Ein frisches benanntes Volume erbt Eigentuemer und Modus des ueberdeckten Verzeichnisses, also entsteht es hier mit `10001:10001` und `0700`.
- **Der Manifest-Gate matcht Regexe, statt Zeichenketten zu vergleichen.** Die Wortliste aus dem Plan (`.*`, `^.*$`, `/`) faengt die naheliegenden Schreibweisen; die Sonde `re.search(url, "/enabled")` faengt jede kreative Variante, die dasselbe bewirkt. Genau das ist der Schaden aus T-02-20, und genau darauf prueft das Gate jetzt.
- **EXAPP-01 bleibt Pending.** Dieser Plan liefert das installierbare Paket, nicht die Installation. Der Nachweis "Admin kann die App als ExApp ueber AppAPI installieren" braucht den Deploy Daemon und eine laufende Nextcloud, also 02-04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Doppelter Bindestrich im XML-Kommentar**
- **Found during:** Task 2 (Manifest)
- **Issue:** Der Kommentar neben `docker-install` nannte die Registrierungsvariante woertlich `--json-info`. XML verbietet `--` innerhalb eines Kommentars, der Parser brach mit `Double hyphen within comment` ab; das Verifikationskommando des Plans scheiterte mit Exit-Code 1.
- **Fix:** Umformuliert auf "the json-info option of occ app_api:app:register". Inhalt unveraendert, Verweis auf 02-04 bleibt.
- **Files modified:** appinfo/info.xml
- **Verification:** Das Verifikationskommando des Plans laeuft mit Exit-Code 0 und gibt `[('^/mcp/?$', 'USER'), ('^/\\.well-known/', 'PUBLIC')]` aus.
- **Committed in:** `e6adf93`

**2. [Rule 2 - Missing Critical] QEMU im CI-Job `image`**
- **Found during:** Task 3 (CI)
- **Issue:** Der Plan nennt fuer den neuen Job nur `docker/setup-buildx-action`. Das Dockerfile fuehrt in der Zielarchitektur echte Befehle aus (apt, curl, tar, install), also laeuft die arm64-Haelfte auf einem amd64-Runner nur emuliert. Ohne binfmt-Registrierung waere der Job dort mit `exec format error` gescheitert, und der Multi-Arch-Anspruch aus den Akzeptanzkriterien waere in der CI unbelegt geblieben.
- **Fix:** `docker/setup-qemu-action@v3` vor `setup-buildx-action` eingefuegt, mit Begruendungskommentar.
- **Files modified:** .github/workflows/ci.yml
- **Verification:** Job-Struktur geparst (`jobs: ['unit', 'image', 'integration']`, Schritte `checkout`, `setup-qemu`, `setup-buildx`, `ExApp image build (no push)`); lokal ist derselbe Bau mit beiden Plattformen gruen (`multiarch_exit=0`).
- **Committed in:** `520019a`

**3. [Rule 2 - Missing Critical] Schreibbarkeit fuer den non-root-Nutzer explizit hergestellt**
- **Found during:** Task 1 (Image)
- **Issue:** Der Plan verlangt non-root und gleichzeitig ein woertlich uebernommenes `start.sh`, das `cat > /frpc.toml` ausfuehrt. Als uid 10001 waere das ein `Permission denied` in `/` gewesen, und der HaRP-Betrieb waere sofort gescheitert. Dasselbe gilt fuer `APP_PERSISTENT_STORAGE`, dessen Volume ohne vorbereitetes Verzeichnis als root-eigen entsteht.
- **Fix:** `install -o 10001 -g 10001 -m 0600 /dev/null /frpc.toml` und `install -d -o 10001 -g 10001 -m 0700 /nc_app_mcp_connector_data` in derselben RUN-Schicht, jeweils mit Begruendungskommentar und Quellenangabe fuer den Mount-Pfad.
- **Files modified:** Dockerfile
- **Verification:** Container mit `HP_SHARED_KEY` gestartet: `start.sh` schrieb `/frpc.toml`, frpc lief an (Verbindungsversuch zum nicht existierenden FRP-Server, `loginFailExit = false`), uvicorn lauschte auf `/tmp/exapp.sock`, Health nach 8 Sekunden `healthy`.
- **Committed in:** `066b2dd`

### Abweichungen ohne Rule-Zuordnung (Plan-Text gegen Realitaet)

- **SPDX-Header war schon da.** Der Plan verlangt, `start.sh` einen SPDX-Header zu ergaenzen. Das HaRP-Original traegt bereits `SPDX-FileCopyrightText` und `SPDX-License-Identifier: AGPL-3.0-or-later`. Ergaenzt wurden deshalb nur die geforderten Herkunftszeilen (Repo, Pfad, Branch, Abrufdatum); ein zweiter SPDX-Block waere eine Falschangabe zur Urheberschaft gewesen.
- **Schema-Attributsatz des Referenz-ExApps.** Der Plan verweist fuer den `info`-Wurzelknoten auf `nextcloud/context_agent`. Dessen `appinfo/info.xml` traegt gar keinen Schema-Attributsatz (nachgeprueft am Original). Verwendet wird deshalb der kanonische Nextcloud-Satz (`xmlns:xsi` plus `xsi:noNamespaceSchemaLocation` auf `apps.nextcloud.com/schema/apps/info.xsd`), weil die Store-Einreichung in Phase 5 genau daran validiert.
- **Lifecycle-Pfade nur im Kommentar.** Das Akzeptanzkriterium erlaubt die drei Pfadnamen innerhalb des Kommentarblocks. Sie stehen dort genau einmal; ausserhalb von Kommentaren kommen sie nicht vor (per Kommentar-Strippen geprueft: 0 Treffer ausserhalb, 3 innerhalb).
- **Testumfang.** Der Plan verlangt mindestens 8 Faelle, es sind 23 geworden, weil CRLF- und ENV-Gate parametrisiert sind und zwei Gegenproben dazukommen.
- **`uv run --no-sync` weiterhin noetig.** Zwei `nc-mcp.exe`-Prozesse des Owners sperren `.venv/Scripts/nc-mcp.exe`, ein `uv sync` wuerde mit `os error 32` scheitern. Alle Gates liefen deshalb mit `--no-sync`, wie schon in 02-01 dokumentiert. Auf den Container-Bau hat das keine Wirkung: der Bau loest die Umgebung im Image selbst auf.

---

**Total deviations:** 3 auto-fixed (2 Missing Critical, 1 Blocking) plus 5 dokumentierte Textabweichungen.
**Impact on plan:** Kein Scope-Zuwachs. Zwei Zeilen im Dockerfile und ein Action-Schritt in der CI kamen dazu, weil die Plan-Vorgaben "non-root" und "multi-arch in der CI" sonst nur auf dem Papier gestanden haetten. Eine Kommentar-Formulierung im Manifest wurde XML-tauglich gemacht.

## Checkpoints

Der Plan enthaelt keine Checkpoints. Im AUTO_MODE waren keine auto-approve-Entscheidungen noetig. Ein Package-Legitimacy-Fall trat nicht auf: es kam kein neues Python-Paket dazu (`pyproject.toml` und `uv.lock` sind unveraendert), und frpc ist das im Research gepruefte Binary aus dem offiziellen FRP-Release, im Dockerfile mit den beiden SHA256-Werten aus der HaRP-README gepinnt.

## Verification Log

1. `docker buildx build --platform linux/amd64 --load -t mcp-connector-exapp:local .` -> Exit-Code 0, Image 79.050.187 Bytes. Im Bau belegt: `sha256sum -c` meldet `/tmp/frp.tar.gz: OK`.
2. `docker image inspect` -> `User: 10001:10001`, `Entrypoint: [/start.sh nc-mcp-exapp]`, `Healthcheck: [CMD /healthcheck.sh]`.
3. `docker run --rm --entrypoint sh ... -c "command -v curl && command -v frpc"` -> `/usr/bin/curl`, `/usr/local/bin/frpc`; `id` -> `uid=10001(exapp) gid=10001(exapp)`; zusaetzlich `command -v nc-mcp-exapp` -> `/app/.venv/bin/nc-mcp-exapp`.
4. `docker run ... env | grep -c 'APP_SECRET\|NC_MCP_APP_PASSWORD\|NC_MCP_STATIC_BEARER'` -> `0`.
5. `docker buildx build --platform linux/amd64,linux/arm64 --output type=cacheonly .` -> Exit-Code 0 (beide Architekturen bis `runtime 8/8` durchgelaufen).
6. Laufzeitprobe TCP: Container mit `APP_PORT=9100` -> Log `Starting application: nc-mcp-exapp`, `Uvicorn running on http://0.0.0.0:9100`, `GET /heartbeat HTTP/1.1 200 OK`, Health nach 8 Sekunden `healthy`.
7. Laufzeitprobe HaRP: Container mit `HP_SHARED_KEY` -> `Uvicorn running on unix socket /tmp/exapp.sock`, frpc gestartet, `GET /heartbeat HTTP/1.1 200 OK`, Health nach 8 Sekunden `healthy`. Beide Testcontainer wurden danach entfernt; die laufende `nc-mcp-test`-Instanz aus `compose.test.yml` blieb unberuehrt.
8. CR-Pruefung: `Dockerfile`, `start.sh`, `healthcheck.sh` -> je "no CR".
9. Manifest per `hardened_parser`: genau zwei Routen `[('^/mcp/?$', 'GET,POST,DELETE', 'USER'), ('^/\\.well-known/', 'GET', 'PUBLIC')]`; `id` `mcp_connector`; `version` `0.1.0` gleich `mcp_connector.__version__`; `image-tag` `0.1.0` gleich `version`; keine deklarierte Route matcht `/heartbeat`, `/init` oder `/enabled`.
10. Grep-Gates: `grep -c "401" appinfo/info.xml` -> 0; `grep -c "<scopes>" appinfo/info.xml` -> 0; Lifecycle-Nennungen ausserhalb von Kommentaren -> 0; `grep -c buildx .github/workflows/ci.yml` -> 2; `grep -c "docker push\|--push" .github/workflows/ci.yml` -> 0.
11. `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py` -> 23 passed.
12. `uv run --no-sync pytest` -> **618 passed, 54 deselected** (Ausgangsstand 595, ohne Docker, ohne Netz).
13. `uv run --no-sync ruff check .` -> All checks passed; `ruff format --check .` -> 100 files already formatted.
14. `uv run --no-sync pyright` -> 0 errors, 0 warnings, 0 informations; `uv run --no-sync vulture src scripts vulture_whitelist.py` -> leer.
15. `uv run --no-sync python scripts/check_tool_budget.py` -> Exit-Code 0 (10642 Bytes, 15 Tools, Budget 12500; Tool-Oberflaeche unveraendert).

## Threat Model Coverage

| Threat ID | Umsetzung | Beleg |
|-----------|-----------|-------|
| T-02-SC | frpc 0.61.1 mit `sha256sum -c` je Architektur, Pruefsummen aus der HaRP-README mit Quelle und Abrufdatum im Kommentar; `start.sh` woertlich mit Herkunftskopf; kein neues PyPI-Paket | Bau-Log `/tmp/frp.tar.gz: OK`; `test_the_frpc_download_is_checksum_verified`, `test_the_start_script_is_the_upstream_one_with_its_origin_named` |
| T-02-20 | Genau zwei enge Routen; keine deklarierte Route matcht einen Lifecycle-Pfad; Gegenprobe belegt das Gate | `test_the_manifest_declares_exactly_the_two_routes_of_this_phase`, `test_the_manifest_gate_rejects_a_wide_public_route` |
| T-02-21 | Kein `bruteforce_protection` im Manifest, `grep -c "401"` -> 0, Gate mit Gegenprobe | `test_the_manifest_gate_rejects_a_throttler_on_401` |
| T-02-22 | `USER 10001:10001`, Nutzer ohne Login-Shell und ohne Home | `docker image inspect` -> `10001:10001`; `test_the_image_runs_unprivileged` |
| T-02-23 | `.dockerignore` schliesst `.git`, `.planning`, `.env*` und `tests` aus; im Image kein Secret als ENV | `docker run ... env | grep -c ...` -> 0; `test_no_secret_is_baked_into_the_image`, `test_the_build_context_excludes_the_history_and_any_env_file` |
| T-02-24 | `uv sync --frozen` gegen das getrackte `uv.lock`, uv als gepinntes Binary `ghcr.io/astral-sh/uv:0.11.7` | Dockerfile, Baustufe; Bau schlaegt fehl, sobald `pyproject.toml` vom Lock abweicht |
| T-02-25 | `HEALTHCHECK` auf `/heartbeat`, Skript kennt Unix-Socket und TCP | Laufzeitproben 6 und 7 (beide Varianten `healthy`); `test_the_image_declares_a_healthcheck`, `test_the_healthcheck_knows_both_transports` |
| T-02-26 | accept: OCI-Labels `source`, `licenses`, `title` gesetzt; eine Signatur (cosign) gehoert zur Store-Einreichung in Phase 5 | Dockerfile, LABEL-Block |

## Known Stubs

Keine. Jede angelegte Datei hat ihren Abnehmer: `Dockerfile` -> `docker buildx` lokal und in der CI, `start.sh` und `healthcheck.sh` -> `ENTRYPOINT` und `HEALTHCHECK` desselben Images, `appinfo/info.xml` -> `occ app_api:app:register` in 02-04, `tests/unit/test_exapp_env_setup.py` -> Standardsuite.

Bewusst offen und laut D-25 so gewollt: das Image ist bis Phase 5 nicht veroeffentlicht. `docker-install` zeigt bereits auf `ghcr.io/street1983nk/nextcloud-mcp-connector:0.1.0`; solange dort nichts liegt, registriert der lokale Test die App ueber die json-info-Variante (02-04). Das steht als Kommentar in der Datei selbst, damit niemand den Eintrag fuer einen Live-Verweis haelt.

## Issues Encountered

- **XML-Kommentar mit `--`:** siehe Abweichung 1. Innerhalb von zwei Minuten erkannt, weil das Verifikationskommando des Plans direkt nach dem Schreiben lief.
- **Gesperrte `.venv/Scripts/nc-mcp.exe`:** unveraendert aus 02-01. Alle Gates liefen mit `uv run --no-sync`; die Prozesse des Owners wurden nicht angefasst.

## User Setup Required

Keine. Der Plan braucht Docker Desktop, das lief; er nimmt keine Dependency auf und veroeffentlicht nichts.

## Next Phase Readiness

- **Bereit fuer 02-04:** Das Image ist lokal unter `mcp-connector-exapp:local` baubar und lauffaehig, das Manifest liegt unter `appinfo/info.xml` und ist mit `occ app_api:app:register --info-xml` verwendbar. Beide Startvarianten (TCP und Unix-Socket hinter HaRP) sind gegen echte Container belegt, der Healthcheck wird gruen.
- **Zu beachten in 02-04:** Der lokale Test kann nicht aus `ghcr.io` ziehen, solange nichts veroeffentlicht ist (D-25). Weg ist die json-info-Registrierung oder eine lokale Registry; der Kommentar in `info.xml` nennt das.
- **Offener Punkt fuer Phase 5:** `image-tag` folgt `version`. Wer die Version anhebt, muss beide Werte gemeinsam bewegen; der Guard-Test `manifest_problems` faengt ein Auseinanderlaufen sofort.
- **Requirements:** EXAPP-01 bleibt Pending. Das Container-Backend existiert, der Installationsnachweis durch den Deploy Daemon fehlt noch.

## Self-Check: PASSED

- Alle sechs neu angelegten Dateien liegen auf der Platte (`[ -f ]` je Datei geprueft): `Dockerfile`, `.dockerignore`, `start.sh`, `healthcheck.sh`, `appinfo/info.xml`, `tests/unit/test_exapp_env_setup.py`.
- Alle drei Task-Commits sind in `git log` auffindbar: `066b2dd`, `e6adf93`, `520019a`.
- Alle Akzeptanzkriterien der drei Aufgaben und alle fuenf Punkte des Plan-Verification-Blocks wurden ausgefuehrt, siehe Verification Log.
- Kein Commit dieses Plans loescht eine Datei (`git diff --diff-filter=D` ueber alle drei Commits -> leer).

---
*Phase: 02-exapp-shell*
*Completed: 2026-08-15*
