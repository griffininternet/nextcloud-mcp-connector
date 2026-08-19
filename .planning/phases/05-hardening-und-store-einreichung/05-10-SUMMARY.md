---
phase: 05-hardening-und-store-einreichung
plan: 10
subsystem: release
tags: [release, app-store, versioning, runbook, live-proof, update, cache]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 01
    provides: "die Administrator-Einstellungen fuer die oeffentliche Adresse und die drei OAuth-Schalter, der Inhalt dieses Releases"
  - phase: 05-hardening-und-store-einreichung
    plan: 04
    provides: "der sichtbare Setup-Zustand statt Exit 2, der Grund, warum 0.1.1 per Klick startet und 0.1.0 nicht"
  - phase: 05-hardening-und-store-einreichung
    plan: 06
    provides: "occ mcp_connector:purge, das im Changelog steht und im Beweislauf noch einmal lief"
  - phase: 05-hardening-und-store-einreichung
    plan: 08
    provides: "die Messung, dass die gelistete 0.1.0 per Ein-Klick-Installation mit Exit 2 crash-loopt, und die HaRP-Topologie des Beweislaufs"
  - phase: 05-hardening-und-store-einreichung
    plan: 09
    provides: "die dreisprachige Store-Beschreibung, die FAQ und die zwei Manifest-Gates, die beim Release gruen bleiben mussten"
provides:
  - "Release 0.1.1: im Store gelistet, Asset erreichbar, Image anonym ziehbar und multi-arch"
  - "docs/store-submission.md: das Release-Runbook fuer Folgereleases plus der belegte Live-Zustand mit Datum je Zeile"
  - "der Beweis, dass ein Update die bestehenden Verbindungen behaelt, gemessen an einem Token, das die Vorversion ausgestellt hat"
  - "der Beweis, dass die gelistete Fassung per Klick startet: 0 restarts statt Restarting (2)"
affects: [EXAPP-04, appinfo/info.xml, CHANGELOG.md, docs/store-submission.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Kommentar in einer Datei, die von einem grep gelesen wird, darf den gesuchten Ausdruck nicht enthalten: zwei Release-Werkzeuge lasen sonst den Kommentar statt der Version"
    - "Der Beweis, dass ein Update Daten behaelt, ist ein Credential aus der Zeit davor, das danach noch traegt, nicht eine Zeilenzahl, die gleich geblieben ist"
    - "Der irreversible Schritt eines Plans wird vorbereitet und dann abgegeben: der Ausfuehrende legt die Kommandos vor, der Owner loest sie mit seinen eigenen Zugangsdaten aus"

key-files:
  created: []
  modified:
    - appinfo/info.xml
    - CHANGELOG.md
    - docs/store-submission.md
    - pyproject.toml
    - src/mcp_connector/__init__.py
    - README.md
    - README.de.md
    - README.fr.md

key-decisions:
  - "Die Version wandert an vier Stellen statt an zwei: pyproject.toml, __version__, version und image-tag; das Manifest-Gate vergleicht version mit der Paketversion, ein Bump nur im Manifest waere rot"
  - "Der Kommentar im docker-install-Block nennt das Versionselement in Worten und nicht in spitzen Klammern, und sagt auch warum: build_store_release.sh und release.yml lesen die Version per grep auf genau dieses oeffnende Tag"
  - "Der Status-Abschnitt der drei READMEs sagt jetzt 'Version 0.1.1. Die App ist gelistet' statt 'Version 0.1.1, gelistet': die Trennung haelt den Satz auch in dem Fenster wahr, in dem der Tag steht und der Store-Upload noch nicht"
  - "Der Update-Nachweis lief gegen die veroeffentlichten Artefakte (ghcr-Image, Store-Listung, GitHub-Asset) statt gegen ein lokal gebautes Image; die Vorversion kam ueber das Manifest des Tags v0.1.0"
  - "Der Store-Cache wird durch Ueberschreiben verworfen, nie durch Loeschen: die geloeschte Datei laesst den Eintrag in Nextclouds Dateicache stehen, und jedes folgende AppAPI-Kommando endet mit GenericFileException"
  - "Die Verbindung des Beweislaufs entstand mit einem Wegwerf-Skript ausserhalb des Repositories, weil scripts/oauth_flow_check.py am Ende immer widerruft und genau das die Frage dieses Nachweises zerstoert haette"

patterns-established:
  - "Jede Zeile des Beweis-Abschnitts traegt Zeitpunkt, Kommando und Antwort; ein Fakt ohne Pruefweg wird nicht eingetragen"
  - "Ein Fund, der ein Runbook korrigiert, geht sofort in das Runbook und nicht nur in das Protokoll"

requirements-completed: [EXAPP-04]

# Metrics
duration: 30min
completed: 2026-08-19
---

# Phase 05 Plan 10: Release 0.1.1 und Store-Aktualisierung Summary

**Die im Store gelistete Fassung ist jetzt die, die diese Phase gebaut hat: 0.1.1 installiert sich per Klick ohne eine einzige Umgebungsvariable und bleibt oben (0 restarts, wo 0.1.0 mit Exit 2 crash-loopte), und ein Zugriffstoken, das die Vorversion ausgestellt hat, bediente nach dem Update weiter 16 Werkzeuge und einen echten Tool-Aufruf.**

## Performance

- **Duration:** 30 min Arbeitszeit (plus die Checkpoint-Runde beim Owner)
- **Started:** 2026-08-19T20:28:23Z
- **Completed:** 2026-08-19T20:56:00Z
- **Tasks:** 3 von 3 (Task 2 vom Owner ausgeloest)
- **Files modified:** 8

## Accomplishments

- **Die Version steht an vier Stellen auf demselben String, und der Git-Tag ist der fuenfte.** `pyproject.toml`, `__version__`, `<version>` und `<image-tag>` sind `0.1.1`; das Manifest-Gate vergleicht die ersten drei, der Release-Workflow vergleicht den Tag mit dem Manifest, und beide waren gruen.
- **`CHANGELOG.md` traegt einen `0.1.1`-Block mit den nutzerrelevanten Aenderungen dieser Phase**, getrennt nach Added, Changed und Fixed: die Administrator-Einstellungen an ihrem echten Ort ("Administration settings, Security, MCP Connector"), das Purge-Kommando, die Anleitungen fuer Open WebUI und MUCGPT, die FAQ, der Setup-Zustand statt des Startabbruchs, die Durchsetzung des Kontoschalters beim Entstehen einer Verbindung, die Store-Beschreibung mit der Abschalt-Antwort, die korrigierte Werkzeugzahl, und die zwei fail-closed Fehler aus 05-08. `grep -ci archiv CHANGELOG.md` ist 0, kein Em-Dash in keiner der geaenderten Dateien.
- **`docs/store-submission.md` ist vom Einreichungszettel zum Release-Runbook geworden.** Der CSR-PR steht nicht mehr als Blocker, sondern als erledigter Einmalschritt. Neu: ein Beweis-Abschnitt in Tabellenform mit Datum und Pruefweg je Zeile, ein Abschnitt `## Release runbook for a follow up release` mit acht numerierten Schritten von der Versionsanhebung bis zu den vier Nachweisen, der Warnblock zu den zwei Produktionsabhaengigkeiten (Assets nie loeschen, Tags nie umschreiben, Korrektur immer als neue Patchversion) und die Cache-Erwartung mit ihren Zahlen (3600 Sekunden stable, 900 unstable, 300 nach einem Fehlschlag).
- **Der Owner hat den irreversiblen Teil ausgeloest, und er lief durch.** Tag `v0.1.1` auf Commit `4d091e7`, Workflow-Lauf [32299836095](https://github.com/street1983nk/nextcloud-mcp-connector/actions/runs/32299836095) gruen in 1m56s, Signatur ueber das heruntergeladene Asset (29491 Bytes), Store-Antwort HTTP 201.
- **Alle vier Live-Nachweise stehen, jeder mit Kommando und Zeitpunkt** (Abschnitt unten und in `docs/store-submission.md`).
- **Das Update behaelt die Verbindungen, belegt statt behauptet.** Auf der HaRP-Topologie: 0.1.0 aus dem Manifest des Tags installiert, eine echte OAuth-Verbindung bis zum Tool-Listing gelaufen, dann `occ app_api:app:update` auf 0.1.1. Danach dieselben Zeilenzahlen und, was allein zaehlt, dasselbe Token: 16 Werkzeuge und ein `files_list`, das antwortete. Ein Token ueberlebt nur, wenn Volume, Zeilen und der Datenschluessel, der sie entschluesselt, den Redeploy ueberlebt haben.
- **Ein Fund, der sofort ins Runbook ging.** Der Store-Cache darf nicht durch Loeschen der Datei verworfen werden: der Eintrag bleibt in Nextclouds Dateicache stehen, und jedes folgende AppAPI-Kommando endet mit `OCP\Files\GenericFileException` ohne Erklaerung. Der Weg, der traegt, steht jetzt mit beiden Kommandos in der Doku.

## Task Commits

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Versionsanhebung, CHANGELOG und Release-Runbook | `4d091e7` | `pyproject.toml`, `src/mcp_connector/__init__.py`, `appinfo/info.xml`, `CHANGELOG.md`, `README.md`, `README.de.md`, `README.fr.md`, `docs/store-submission.md` |
| 2 | Tag, Signatur und Upload (Owner-Aktion) | Tag `v0.1.1` auf `4d091e7`, Workflow-Lauf 32299836095 | keine Quelldatei |
| 3 | Der Live-Nachweis nach dem Release | `f5122b4` | `docs/store-submission.md` |

## Live-Nachweis 0.1.1

Alles am 19.08.2026 gemessen, Zeiten in UTC. Dieselben Zeilen stehen in
`docs/store-submission.md`, damit sie ohne dieses Dokument auffindbar sind.

| Zeit | Nachweis | Kommando und Antwort |
|------|----------|----------------------|
| 20:45 | Store-Eintrag fuehrt `0.1.1` mit derselben Plattform-Spanne | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`: Releases `0.1.1` und `0.1.0`, beide `>=32.0.0 <35.0.0`, Download des neuen Releases zeigt auf `v0.1.1/mcp_connector-0.1.1.tar.gz`; der Store fuehrt jetzt 27 ExApps (vorher 26) |
| 20:45 | Download-URL antwortet 200 | `curl -sSIL .../releases/download/v0.1.1/mcp_connector-0.1.1.tar.gz`: 302, dann 200 mit `Content-Length: 29491`, genau die Groesse, die signiert wurde |
| 20:46 | Image-Manifest anonym und multi-arch | anonymes Token von `ghcr.io/token`, dann `ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.1`: HTTP 200, `application/vnd.oci.image.index.v1+json`, `linux/amd64`, `linux/arm64` plus die zwei Attestation-Eintraege |
| 20:46 | Tagliste enthaelt beide Tags | `ghcr.io/v2/street1983nk/mcp_connector/tags/list`: `["0.1.0","0.1.1"]`, kein Tag umgeschrieben |
| 20:49 | Vorversion installiert, aus dem veroeffentlichten Manifest des Tags | `occ app_api:app:register mcp_connector harp_proxy_docker --info-xml https://raw.githubusercontent.com/.../v0.1.0/appinfo/info.xml --env NC_MCP_PUBLIC_URL=... --wait-finish`: `0.1.0 [enabled]`, Container healthy auf `ghcr.io/street1983nk/mcp_connector:0.1.0` |
| 20:50 | Eine echte Verbindung als Zaehlbasis | Registrierung, Anmeldung, Consent, Code-Tausch, dann Tool-Listing mit dem entstandenen Token: 16 Werkzeuge; im Volume 1 client, 1 authorization, 1 access_token, 1 refresh_token |
| 20:51 | Der Cache ist real, 57 Minuten nach dem letzten Store-Abruf | `occ app_api:app:update --all --showonly`: leer, die Instanz kannte nur 0.1.0 (Pitfall 8, kein Fehler des Releases) |
| 20:51 | Nach dem Verwerfen des Caches sieht die Instanz das Update | `mcp_connector new version available: 0.1.1` |
| 20:52 | Das Update selbst, 20 Sekunden | `occ app_api:app:update mcp_connector --wait-finish`: disabled, deployed, updated; danach `0.1.1 [enabled]`, Container healthy auf dem 0.1.1-Image |
| 20:52 | **Die Verbindung hat es ueberlebt** | Zeilenzahlen unveraendert (1/1/1/1), und das von 0.1.0 ausgestellte Zugriffstoken bediente gegen 0.1.1 weiter 16 Werkzeuge und einen echten `files_list`-Aufruf |
| 20:53 | Ein-Klick-Installation ohne jede Variable startet und bleibt oben | `occ app_api:app:register mcp_connector harp_proxy_docker --wait-finish` ohne `--env`: `0.1.1 [enabled]`, `0 restarts`, state running, healthy; im Log der Setup-Zustand mit dem Ort, an dem die Adresse gesetzt wird. 05-08 mass an derselben Stelle fuer 0.1.0 `Restarting (2)` und Exit 2 |
| 20:53 | Purge auf der veroeffentlichten Fassung | `occ mcp_connector:purge --force`: `{"purged":true,"connections":1,"revoked":1,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}` |

Danach `occ app_api:app:unregister mcp_connector --rm-data` und `docker compose -f
compose.exapp.yml down`: der Host steht wieder so da wie vor dem Lauf, die Wegwerf-Skripte
und die Tokens ausserhalb des Repositories sind geloescht.

## Verification

```
uv run --no-sync pytest -q                                      1776 passed, 92 deselected
uv run --no-sync ruff check .                                   All checks passed!
uv run --no-sync ruff format --check .                          166 files already formatted
uv run --no-sync pyright                                        0 errors, 0 warnings, 0 informations
uv run --no-sync vulture src scripts vulture_whitelist.py       leer
uv run --no-sync python scripts/check_tool_budget.py            11268 bytes, 16 tools, budget 12500
git diff --stat uv.lock                                         leer
```

Zusaetzlich geprueft:

| Kriterium | Befund |
|-----------|--------|
| `version` gleich `image-tag` in `appinfo/info.xml` | `0.1.1` und `0.1.1` |
| Archiv lokal gebaut, Inhalt | `mcp_connector/`, darin `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`; Version darin `0.1.1` |
| `grep -ci archiv CHANGELOG.md` | 0 |
| Em-Dash oder En-Dash in den acht geaenderten Dateien | 0 |
| `curl -sS .../appapi_apps.json | grep -c 0.1.1` | 1 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der neue Manifest-Kommentar machte die Versionserkennung zweier Release-Werkzeuge unbrauchbar**

- **Found during:** Task 1
- **Issue:** Der ersetzte Kommentar im `docker-install`-Block erklaerte die Gleichheit der drei Strings und nannte das Versionselement dabei in spitzen Klammern. `scripts/build_store_release.sh` und `.github/workflows/release.yml` lesen die Version mit `grep -oP '(?<=<version>)[^<]+'`, also mit genau diesem Muster. Der erste Treffer war ab da der Kommentar: das lokal gebaute Archiv hiess `mcp_connector-0.1.1\n above, this tag and the git tag v\n have\n, ....tar.gz`. Auf dem Tag-Pfad haette der Workflow denselben Unsinn mit dem Manifestwert verglichen und den Release abgebrochen.
- **Fix:** Der Kommentar nennt das Element in Worten und traegt die Warnung selbst, damit der naechste Leser den Fehler nicht wiederholt.
- **Files modified:** `appinfo/info.xml`
- **Commit:** `4d091e7`

**2. [Rule 3 - Blockierend] Die Version musste auch in `pyproject.toml` und `__version__` wandern**

- **Found during:** Task 1
- **Issue:** `files_modified` des Plans nennt nur `appinfo/info.xml`, `CHANGELOG.md` und `docs/store-submission.md`. Das Manifest-Gate `test_the_manifest_passes_its_own_gate` vergleicht `<version>` aber mit `mcp_connector.__version__`; eine Anhebung nur im Manifest waere sofort rot gewesen, und das Image haette weiter die alte Version gemeldet.
- **Fix:** Beide Stellen mitgehoben, wie es 05-09 unter "Fuer 05-10" als Punkt 2 vorgezeichnet hat.
- **Files modified:** `pyproject.toml`, `src/mcp_connector/__init__.py`
- **Commit:** `4d091e7`

**3. [Rule 2 - Fehlende kritische Korrektheit] Der Versionssatz der drei READMEs**

- **Found during:** Task 1
- **Issue:** 05-09 hat den `## Status`-Abschnitt in drei Sprachen angelegt, und er nennt die Version woertlich. Nach einem Release ohne diese Aenderung haette die erste Zeile, die ein Besucher liest, eine Version genannt, die es nicht mehr gibt, und das Archiv haette diese Datei mit ausgeliefert (`build_store_release.sh` legt `README.md` hinein).
- **Fix:** Auf `0.1.1` gehoben und dabei umgestellt: "Version 0.1.1. Die App ist gelistet und installierbar" statt "Version 0.1.1, gelistet". Der Satz ist damit auch in dem Fenster wahr, in dem der Tag steht und der Store-Upload noch aussteht.
- **Files modified:** `README.md`, `README.de.md`, `README.fr.md`
- **Commit:** `4d091e7`

### Bewusste Auslegungen

- **Die Vorversion des Update-Nachweises kam ueber `--info-xml` des Tags `v0.1.0`, nicht ueber die Store-Auswahl.** Der Store liefert immer die hoechste passende Version, also 0.1.1; ohne diesen Weg gaebe es keine Instanz mit Vorversion, an der ein Update ueberhaupt messbar waere. Alles daran ist trotzdem veroeffentlicht: das Manifest ist das des Tags, das Image ist `ghcr.io/street1983nk/mcp_connector:0.1.0`, und das Update selbst lief ueber die Store-Listung.
- **Die Verbindung entstand mit einem Wegwerf-Skript ausserhalb des Repositories.** `scripts/oauth_flow_check.py` widerruft am Ende jedes Laufs, und genau das haette den Nachweis zerstoert. Das Skript importierte die vorhandenen Bausteine (`connect`, `list_tools`, `tool_call`, `revoke`), legte nichts Neues an, und die Tokens lagen ausserhalb des Repositories und sind geloescht.
- **Die Checkliste in `docs/store-submission.md` bleibt eine Vorlage.** Die zwei Release-Haken sind bewusst leer, weil sie fuer jeden Durchgang neu gelten; der Zustand von 0.1.1 steht in der Beweis-Tabelle darueber.

## Threat Flags

| Threat ID | Kategorie | Disposition | Zustand nach diesem Plan |
|-----------|-----------|-------------|--------------------------|
| T-05-45 | Tampering (version, Git-Tag und image-tag laufen auseinander) | mitigate | **Gehalten, und einmal live ausgeloest.** Das verify-Kommando vergleicht `version` und `image-tag`, das Manifest-Gate vergleicht zusaetzlich mit der Paketversion, und der Workflow vergleicht den Tag mit dem Manifest. Der Fund oben zeigt, dass die Kette auch den Weg schuetzt, auf dem die Version *gelesen* wird: ein Kommentar, der das Versions-Tag wiederholt, verschiebt genau diesen Wert, und die Warnung dazu steht jetzt in der Datei selbst. |
| T-05-46 | Denial of Service (geloeschtes Asset, umgeschriebener Tag) | mitigate | **Gehalten.** Warnblock im Runbook als eigener Abschnitt, `curl -I` als Pflichtschritt 8. Gemessen: die Download-URL antwortet 200 mit 29491 Bytes, die Tagliste enthaelt `0.1.0` und `0.1.1`, es wurde nichts geloescht und nichts umgeschrieben. |
| T-05-47 | Information Disclosure (Signaturschluessel oder Store-Zugang im Repo, Log oder Protokoll) | mitigate | **Gehalten.** Der Checkpoint verlangte Workflow-URL, die Aussage "Signatur erzeugt" und den Statuscode, und genau das kam zurueck. Weder Schluessel noch Signatur noch Store-Token stehen in einem Commit, einem Log oder diesem Dokument. Der einzige Ort, an dem waehrend des Beweislaufs Tokens lagen, war ein Wegwerf-Verzeichnis ausserhalb des Repositories, und die Datei ist geloescht. |
| T-05-48 | Tampering (ein Update loescht die bestehenden Verbindungen) | mitigate | **Gehalten und gemessen.** Ein Zugriffstoken der Vorversion bediente nach dem Update 16 Werkzeuge und einen echten Tool-Aufruf, und die Zeilenzahlen blieben 1/1/1/1. Zusaetzlich gemessen: auch ein `unregister` ohne `--rm-data` mit anschliessender Neuinstallation liess Client und Autorisierung stehen. |
| T-05-SC | Tampering (Paketinstallationen) | accept | **Nichts installiert.** `git diff --stat uv.lock` ist leer, `pyproject.toml` aenderte nur die Versionszeile. |

Keine neue Angriffsflaeche: dieser Plan hat keine Route, kein Schema und keinen Datenpfad
angefasst. Die einzige Aenderung an ausfuehrbarem Verhalten ist die Versionszeichenkette.

## Bewusst offen

Fuer die Phasen-Verifikation und die Backlog-Pflege gesammelt, hier bewusst nicht erledigt.

**Backlog-Eintraege, die diese Phase nicht angefasst hat:**

| ID | Gegenstand |
|----|------------|
| BL-04 | Lokale Clients (Loopback, private-use scheme) als OAuth-Clients; Claude Code passt nicht auf das exakte Redirect-Matching von v1 |
| BL-05 | Client ID Metadata Documents als Nachfolger der Dynamic Client Registration |
| BL-08 | Anti-Forgery-Werte mit Zeitfenster, oder als akzeptiertes Risiko fuehren (Review 04, ME-02) |
| BL-09 | Den Truncation-Marker aus dem Text ziehen (Review 04, ME-03, D-57) |
| BL-11 | Die drei kleineren Funde des Phase-4-Reviews (LO-02, LO-03, LO-06) |

**Die `max-version` bleibt 34, mit zwei benannten Testpunkten.** NC 35 ist in Entwicklung
(AppAPI v35.0.0beta3 vom 18.08.2026), unsere Spanne ist `>=32.0.0 <35.0.0`. Wer sie hebt,
prueft zuerst diese beiden: erstens den Data-Key-Lesepfad, weil die ExApp-Konfiguration in
AppAPI 35 nach `oc_appconfig` wandert (`Version035000Date20260529120000`, die Alt-Tabellen
werden gedroppt), und zweitens das Remove-Verhalten des Store-UI in 35, weil der NC-34-Befund
genau dort haengt.

**Der moegliche Upstream-PR zur NC-34-Uninstall-Verdrahtung.** In `nextcloud/app_api` gibt es
kein offenes Issue dazu, die Reparatur ist klein (`exApps.uninstallApp` muesste
`uninstallExApp` aufrufen, plus die fehlende Oberflaeche), und die Ursachenkette steht
belegt in `docs/exapp-install.md`. Einreichung waere wie jeder Upstream-Beitrag eine
Owner-Aktion.

**Der Startzeit-Lesevorgang der Admin-Werte antwortet 401** (`deferred-items.md`, gefunden in
05-08). Der Lesepfad faellt weich aus, die App laeuft mit den Deploy-Variablen weiter, aber
ein im Admin-Formular gesetzter Wert wirkt auf der gemessenen Topologie nie. Vermutung, nicht
gemessen: zur Startzeit ist die App noch nicht `enabled`, und AppAPI weist die eigene
App-Identitaet in diesem Fenster ab; dann waere der Fix ein zweiter Lesevorgang am
`enabled=1`-Hook. Das ist der wichtigste dieser Punkte, weil er das Feature betrifft, das
dieses Release ausliefert: das Formular existiert und ist erreichbar, sein Wert wird aber
erst nach einem Neustart der App gelesen, und der Setup-Text im Log sagt genau das
("disable und enable this app again"). Der Ein-Klick-Weg ist damit vollstaendig, der
Ein-Klick-Komfort noch nicht.

**AIO-Smoke (D-31)** bleibt descoped mit der in 05-08 genannten Voraussetzung (oeffentliche
Domain plus gueltiges TLS), also eine Host-Eigenschaft und keine Code-Eigenschaft.

## Files Changed

- `appinfo/info.xml`: `version` und `image-tag` auf `0.1.1`, der veraltete Kommentar zum
  unveroeffentlichten Image durch den heutigen Stand ersetzt, mit der Warnung, das
  Versionselement nicht in spitzen Klammern zu wiederholen.
- `CHANGELOG.md`: `0.1.1`-Block mit Added, Changed und Fixed, plus die zwei Link-Referenzen.
- `docs/store-submission.md`: `+47/-4` in Task 3 auf `+119/-40` gesamt; Statuskorrektur,
  Beweis-Abschnitt, Release-Runbook, Warnblock, Cache-Abschnitt, Update-Tabelle.
- `pyproject.toml`, `src/mcp_connector/__init__.py`: die Paketversion.
- `README.md`, `README.de.md`, `README.fr.md`: der Versionssatz des Status-Abschnitts.

## Known Stubs

Keine. Dieser Plan hat keinen Codepfad angelegt und keine Datenquelle offen gelassen.

## Requirements

- **EXAPP-04** ist **Complete**. Der Anforderungstext ist "App ist im Nextcloud App Store
  eingereicht (Zertifikat via CSR-PR, Signatur, `info.xml`-Validierung,
  Datenweitergabe-Disclosure) vor der Conference September 2026". Zertifikat und Registrierung
  liegen vor, die Signatur ueber das heruntergeladene Asset wurde akzeptiert (HTTP 201), die
  `info.xml`-Validierung des Stores lief beim Upload durch, und die Datenweitergabe steht als
  Prosa in allen drei Beschreibungen. Der Pflegeteil, den 05-RESEARCH offen liess, ist mit
  diesem Release und seinem Runbook ebenfalls erledigt.

## Self-Check: PASSED

Geprueft nach dem Schreiben dieses Dokuments:

- `appinfo/info.xml`, `CHANGELOG.md`, `docs/store-submission.md`, `pyproject.toml`,
  `src/mcp_connector/__init__.py`, `README.md`, `README.de.md`, `README.fr.md` vorhanden und
  geaendert.
- Commits `4d091e7` und `f5122b4` im Log gefunden.
- Der Store fuehrt `0.1.1`, live abgefragt.
