---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 07
subsystem: topology-and-docs
tags: [exapp-06, nextcloud-34.0.3, store-ui, measurement, docs, three-readmes, store-text]

# Dependency graph
requires:
  - phase: 06-04
    provides: "das Manifest mit fuenf deklarierten Variablen, das der Rebuild dieses Plans in die Registrierung traegt"
  - phase: 06-06
    provides: "den Repository-Stand, der jetzt laeuft (Zustimmungsseite, CIMD, Loopback-Portregel)"
provides:
  - "compose.exapp.yml auf nextcloud:34.0.3-apache gepinnt, mit dem Grund an der Zeile"
  - "die Messtopologie auf 34.0.3.2 mit dem Connector aus dem Arbeitsbaum (0.1.2, Digest sha256:3ba4a2ce1921), jane und zwei gueltigen Verbindungen erhalten"
  - "06-07-MEASUREMENTS.md: occ status als erste Behauptung, Volume-Sicherungspfad, Digest vor und nach dem Rebuild, Konto, Cache-Schritt, Netzwerkmitschnitt, md5-Gegenprobe"
  - "EXAPP-06 beantwortet: die Store-Oberflaeche zeigt diese ExApp, der Install-Knopf heisst 'Deploy and enable', 'Remove' steht im Aktionsmenue einer abgeschalteten ExApp"
  - "docs/exapp-install.md mit dem 34.0.3-Befund neben der datierten 34.0.2-Kette"
  - "die drei READMEs und die drei Store-Beschreibungen mit derselben Aussage zur Installation"
  - "docs/screenshots/exapp-remove-button.png"
affects: [EXAPP-06, 06-08, 06-09, 06-10, CONF-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Browser-Schritt ohne Playwright-Werkzeug laeuft ueber das DevTools-Protokoll mit einem WebSocket-Client aus der Standardbibliothek gegen das installierte Chrome: kein Paket, kein Legitimacy-Gate (T-06-SC)"
    - "Eine Instanz wird auf eine Patch-Version gepinnt und die Version aus occ status gelesen, nie aus dem Tag"
    - "Ein Knopf-Befund wird in beiden Zustaenden gemessen, wenn die Sichtbarkeit an einem Zustand haengt: 'kein Remove-Knopf' war nur die Haelfte der Wahrheit"
    - "Eine erfolglose statische Gegenprobe wird nicht geloescht, wenn die Messung sie ueberholt, sondern erklaert: der Fix war ein Aufruf und kein neues Wort"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-07-MEASUREMENTS.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-07-SUMMARY.md
    - docs/screenshots/exapp-remove-button.png
  modified:
    - compose.exapp.yml
    - docs/exapp-install.md
    - README.md
    - README.de.md
    - README.fr.md
    - appinfo/info.xml
    - CHANGELOG.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Der Rebuild lief als Abmelden und Neuregistrieren, nicht nur als bootstrap_exapp.sh: ensure_exapp ueberspringt die Registrierung fuer eine bekannte App, also waere ein Image 0.1.2 gebaut worden, waehrend der Container weiter 0.1.1 fuhr (genau der Fehler von Pitfall 8, eine Ebene tiefer)"
  - "Abgemeldet wurde ohne --rm-data, und vorher wurde im Quelltext geprueft, was ein unregister mitnimmt: der Volume-Zweig haengt an --rm-data, und ExAppService::unregisterExApp loescht keine Zeile aus oc_appconfig_ex. Beides wurde danach gemessen, weil der Datenschluessel dort liegt und ohne ihn jede Autorisierung unlesbar waere"
  - "Der Remove-Knopf wurde in beiden Zustaenden gemessen: AppAPI rechnet canUnInstall = !active && removable (ExAppsPageController.php:213), also haette ein Blick auf die eingeschaltete App einen falschen Negativbefund ergeben"
  - "Der Install-Knopf wurde an einer nicht installierten ExApp derselben Ansicht gemessen (Context Chat Backend, 'Deploy and enable'), weil die eigene App installiert ist und darum 'Disable' traegt: eine Deinstallation der Demo-Substanz waere der Preis fuer eine Auskunft, die eine Nachbarzeile schon gibt"
  - "Der Browser-Schritt lief ohne Playwright: dieser Sitzung stand das Werkzeug nicht zur Verfuegung, und ein Paket zu installieren ist ausgeschlossen (T-06-SC). Gemessen wurde mit dem installierten Chrome ueber das DevTools-Protokoll, angesprochen von einem WebSocket-Client aus der Standardbibliothek"
  - "docs/contrib/app-api-971-comment.md entsteht NICHT: der Entwurf war fuer den negativen Ausgang vorgesehen, und der Ausgang ist positiv. Es gibt nichts zu melden, was upstream nicht schon geschlossen hat"
  - "Ein Bildschirmfoto geht ins Repository (docs/screenshots/exapp-remove-button.png): es traegt kein Credential und keine fremden Nutzerinhalte, sondern den Katalog abgeschalteter Kern-Apps dieser Wegwerf-Instanz plus die eigene Zeile mit dem geoeffneten Aktionsmenue"
  - "Die Version im Manifest bleibt 0.1.2 und es wurde kein v*-Tag erzeugt: ein Store-Release braucht Owner-Freigabe"

patterns-established:
  - "Der Cache-Schritt vor einer Store-UI-Messung nennt die Datei, das Vorher und das Nachher (timestamp=1787235500 -> 0) und belegt danach ein funktionierendes occ app_api:app:list, damit 'Ueberschreiben statt Loeschen' nicht nur eine Behauptung ist"

requirements-completed: [EXAPP-06]

# Metrics
duration: 45min
completed: 2026-08-20
---

# Phase 06 Plan 07: Die Messtopologie auf 34.0.3 und der Store-UI-Befund Summary

**Die Wegwerf-Instanz laeuft belegt auf 34.0.3.2 mit dem Connector aus dem Arbeitsbaum
(0.1.2, neuer Image-Digest), jane und ihre zwei gueltigen OAuth-Verbindungen haben Upgrade und
Neuregistrierung ueberlebt, und die Store-Oberflaeche zeigt diese ExApp jetzt wirklich: der
Installationsknopf einer ExApp heisst "Deploy and enable", "Remove" steht im Aktionsmenue der
Zeile und nur solange die App abgeschaltet ist.**

## Performance

- **Duration:** 45 min
- **Tasks:** 3 von 3
- **Files modified:** 1 Topologie-Datei, 5 Textdateien (Doku, drei READMEs, Manifest), CHANGELOG, 1 Bild, 1 Messdatei

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Volume-Sicherung, Upgrade auf 34.0.3, Rebuild auf Repo-Stand | `025a796` |
| 2 | Der UI-Smoke, mit Cache-Schritt und Gegenprobe | `918a9ad` |
| 3 | Doku, drei READMEs und Store-Text sagen das Gemessene | `6ebd0ae` |

## Der Befund, in einer Tabelle

| Frage | Antwort auf 34.0.3.2 | Sichtbarer Text |
|-------|----------------------|-----------------|
| Erscheint die ExApp in der Liste? | ja | Zeile "MCP Connector 0.1.2 Harp Proxy (Docker)" unter "Your apps" |
| Install-Knopf fuer eine ExApp? | ja | "Deploy and enable" (an einer nicht installierten ExApp derselben Ansicht) |
| Remove-Knopf fuer diese ExApp? | ja, im Aktionsmenue, nur abgeschaltet | "Remove" |
| Remove-Knopf an der eingeschalteten App? | nein | Menue ohne "Remove", `canUnInstall=false` |

Wo bei einer normalen App das Abzeichen "Featured" steht, steht bei einer ExApp der Name ihres
Deploy Daemon. Und der Grund fuer die zweistufige Entfernung liegt in AppAPI und nicht im
Frontend: `canUnInstall = !active && removable && ...`
(`apps/app_api/lib/Controller/ExAppsPageController.php:213`).

## Warum der Fix statisch nicht zu finden war

Die Recherche hatte den 34.0.3-Fix nicht belegen koennen, und dieser Plan erklaert die
Beobachtung statt sie zu ueberschreiben. Beide Images tragen `appstore` 1.0.0, und ausserhalb
von `l10n/` unterscheiden sich fuenf Dateien. Die interessante ist `dist/appstore-main.mjs`
(95762 -> 95841 Bytes):

```
34.0.2: kein Treffer fuer Promise.allSettled([ ... initialize ... ])
34.0.3: Promise.allSettled([V(),Y(),e.isEnabled?e.initialize():Promise.resolve()])
"isEnabled":  2 -> 3      "initialize": 1 -> 2
"app_api":   23 -> 23     "exAppsCount": 1 -> 1
"exapp" in AppstoreBrowse-*.chunk.mjs: 0 in beiden
```

`e` ist der minifizierte Name des `external-apps`-Stores. Der Merge-Titel
`fix(appstore): initialize the exApps store when enabled` ist damit woertlich das, was sich
geaendert hat, und wer nach dem Wort `exapp` sucht, findet nichts. Die zweite Haelfte des
Belegs ist der Netzwerkmitschnitt: die Seite fragt jetzt `/apps/app_api/apps/list`, was auf
34.0.2 nie geschah. Der `appstore` selbst kennt die ExApps weiter nicht (seine OCS-Antwort von
2 650 705 Bytes enthaelt `mcp_connector` null Mal, `ApiController.php` traegt unveraendert
`'app_api' => false`).

## Verifikation

| Kriterium | Beleg |
|-----------|-------|
| `occ status` meldet 34.0.3 | `version: 34.0.3.2`, `versionstring: 34.0.3`, `installed: true` |
| `occ app_api:app:list` | `mcp_connector (MCP Connector): 0.1.2 [enabled]` |
| Image-Digest geaendert | `sha256:92602ca154a2...` (0.1.1) -> `sha256:3ba4a2ce1921...` (0.1.2) |
| Demo-Substanz erhalten | `jane` in `occ user:list`; `authorizations` 2 vor und nach dem Lauf, beide `revoked_at` leer |
| Repo-Stand laeuft wirklich | AS-Metadaten liefern `client_id_metadata_document_supported: true` (erst seit 06-05) und den oeffentlichen `issuer` |
| Owner-Instanzen unberuehrt | `docker ps`: `nc-mcp-test` und `findling-nextcloud` je "Up 5 days" |
| Pin gesetzt | `grep -c "34.0.3-apache"` = 1, `grep -c "nextcloud:34-apache"` = 0 |
| Messdatei ohne Credential | Grep-Kriterium des Plans liefert 0 |
| Text-Gates | keine Em-Dashes und kein Vokabular-Treffer in den fuenf Textdateien; 121 Umlaut-Treffer in README.de.md |
| Ueberschriftenfolge der READMEs | 21 Ueberschriften in jeder der drei Dateien |
| Store-Beschreibungen | drei Bloecke, je 6 Absaetze, ohne Backtick, ohne `<`, ohne Tabelle, ohne Linie |
| Manifest | wohlgeformt, `<version>0.1.2</version>` unveraendert, kein neuer `v*`-Tag |
| Tests | `uv run --no-sync pytest tests/unit` 2155 gruen |
| Lint | `ruff check .` und `ruff format --check .` sauber (171 Dateien) |

## Abweichungen vom Plan

### 1. [Rule 3 - Blockierend] Der Rebuild brauchte eine Neuregistrierung

- **Gefunden in:** Task 1
- **Problem:** Der Plan sah `bash scripts/bootstrap_exapp.sh` als Weg zum Repository-Stand
  vor. `ensure_exapp` ueberspringt die Registrierung, sobald `occ app_api:app:list` die App
  kennt, also waere ein Image 0.1.2 gebaut und gepusht worden, waehrend der Container weiter
  `mcp_connector:0.1.1` fuhr, und die Messdatei haette einen unveraenderten Digest gezeigt.
- **Loesung:** `occ app_api:app:unregister mcp_connector` **ohne** `--rm-data`, danach der
  Bootstrap. Vor dem Abmelden wurde im AppAPI-Quelltext geprueft, was ein unregister mitnimmt
  (Volume-Zweig nur mit `--rm-data`, `unregisterExApp` laesst `oc_appconfig_ex` unberuehrt),
  und danach wurde beides gemessen: `oauth_data_key` und `public_url` standen noch da, das
  Volume auch. Zusaetzlich wurden die zwei Config-Zeilen vorher ausserhalb des Repositories
  gesichert, damit ein Fehlschlag nicht die zwei Verbindungen kostet.
- **Dateien:** keine Code-Aenderung, ein Schritt mehr im Ablauf und in der Messdatei
- **Commit:** `025a796`

### 2. [Rule 3 - Blockierend] Kein Playwright in dieser Sitzung

- **Gefunden in:** Task 2
- **Problem:** Der Plan nennt "das im Projekt vorhandene Playwright-Muster". Dieser
  Executor-Sitzung standen die Playwright-Werkzeuge nicht zur Verfuegung, und ein Paket zu
  installieren ist in dieser Phase ausgeschlossen (T-06-SC, und die Regel des Executors
  behandelt einen Paket-Install ohnehin nie als Auto-Fix).
- **Loesung:** Das auf dem Host installierte Chrome (`--headless=new`) ueber das
  DevTools-Protokoll, angesprochen von einem WebSocket-Client aus der Standardbibliothek. Die
  Treiber-Skripte liegen ausserhalb des Repositories (Scratchpad), weil sie Messwerkzeug sind
  und der Plan sie nicht als Liefergegenstand nennt. Die Eigenheit steht als eigener Absatz in
  der Messdatei, nach dem Muster von 05-07.
- **Dateien:** keine im Repository
- **Commit:** `918a9ad`

### 3. [Rule 2 - Vollstaendigkeit] Der Remove-Befund in beiden Zustaenden

- **Gefunden in:** Task 2
- **Problem:** Am eingeschalteten Eintrag gibt es keinen Remove-Knopf. Als Befund
  hingeschrieben waere das ein falscher Negativbefund gewesen, und die Doku haette gesagt, die
  Oberflaeche koenne eine ExApp nicht entfernen.
- **Loesung:** Der Quelltext von AppAPI nennt die Bedingung
  (`canUnInstall = !active && removable`), also wurde die zweite Haelfte gemessen:
  `occ app_api:app:disable`, Blick auf `/settings/apps/disabled`, Aktionsmenue mit "Remove",
  danach `occ app_api:app:enable` und Nachzaehlen der zwei Verbindungen. Ein Test, der
  Instanzzustand aendert, stellt ihn wieder her (T-05-24-Muster).
- **Dateien:** Messdatei, Doku
- **Commit:** `918a9ad`, `6ebd0ae`

### 4. [Rule 2 - Owner-Regel] CHANGELOG-Eintrag

- **Gefunden in:** Task 3
- **Problem:** Der Plan listet `CHANGELOG.md` nicht, die Owner-Regel verlangt fuer jede
  nutzerrelevante Aenderung einen Eintrag unter `## [Unreleased]`, und eine geaenderte Aussage
  zur Installation im Store-Text ist nutzerrelevant.
- **Loesung:** Ein Eintrag unter `### Changed`, der den Befund und seine Versionsbedingung
  nennt.
- **Dateien:** `CHANGELOG.md`
- **Commit:** `6ebd0ae`

## Was dieser Plan nicht tut

- **Kein `docs/contrib/app-api-971-comment.md`.** Der Entwurf war fuer den negativen Ausgang
  vorgesehen; der Ausgang ist positiv, der Upstream-Fix wirkt, und es gibt nichts zu melden.
  `app_api#971` und `server#61709` sind geschlossen, und die Messung bestaetigt das.
- **Keine Versionsanhebung und kein Release.** `<version>` bleibt 0.1.2, kein `v*`-Tag. Ein
  Store-Release braucht Owner-Freigabe, und der geaenderte Store-Text erreicht den Store erst
  mit dem naechsten Release.
- **Keine Deinstallation der eigenen App zur Messung.** Der Install-Knopf wurde an der
  Nachbarzeile einer nicht installierten ExApp gemessen; die Demo-Substanz fuer CONF-01 bleibt
  stehen.
- **Kein Blick auf 32 und 33.** Die Aussage der Doku ist auf 34.0.2 und 34.0.3 datiert, und
  fuer alles andere bleibt der Satz stehen, dass `occ` auf jeder Version funktioniert.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche: dieser Plan aendert keine Route, kein Schema und keinen
Auth-Pfad. Die Aenderungen sind eine Image-Zeile, Text und ein Bild.

## Requirements

- **EXAPP-06 abgehakt:** Es ist gemessen, **ob** die Store-Oberflaeche auf 34.0.3 Install- und
  Remove-Knopf fuer diese ExApp zeigt, getrennt beantwortet, unter benanntem Admin-Konto und
  nach dem Cache-Schritt. Antwort: beide vorhanden, der Remove-Knopf nur an einer
  abgeschalteten ExApp.

## Self-Check: PASSED

- `06-07-MEASUREMENTS.md`, `06-07-SUMMARY.md` und `docs/screenshots/exapp-remove-button.png`
  liegen auf der Platte.
- Die drei Task-Commits `025a796`, `918a9ad` und `6ebd0ae` sind in `git log`.
