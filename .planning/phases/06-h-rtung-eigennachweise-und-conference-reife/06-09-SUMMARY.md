---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 09
subsystem: oauth-cimd-and-loopback-port
tags: [auth-08, client-05, cimd, claude-code, loopback-port, rfc-8252, measurement, docs, control-probes]

# Dependency graph
requires:
  - phase: 06-07
    provides: "die Messtopologie auf 34.0.3.2 mit dem Connector aus dem Arbeitsbaum (0.1.2, Digest sha256:3ba4a2ce1921), jane und ihre zwei Verbindungen"
  - phase: 06-05
    provides: "den CIMD-Zweig in get_client und die Frische-Spalten der clients-Zeile, die hier live beschrieben werden"
  - phase: 06-03
    provides: "loopback_match und also_accepting, deren Notwendigkeit hier gemessen wird"
  - phase: 06-04
    provides: "das Advertising client_id_metadata_document_supported, das der Client als Weiche liest"
provides:
  - "06-09-MEASUREMENTS.md: Vorpruefung des AS-Dokuments, die tatsaechlich gesendete client_id, der vollstaendige Rundlauf mit clients-Zeile Feld fuer Feld, die Portspalte ueber vier Laeufe, drei Gegenproben zur Loopback-Regel, die drei Kontrollproben mit gezaehltem Ausgang, sechs unvorhergesagte Funde, der Nachzustand"
  - "AUTH-08 live belegt: Claude Code 2.1.233 weist sich per Metadatendokument aus, verbindet sich und ruft files_list mit Inhalt auf"
  - "CLIENT-05 beantwortet: 45157, 47608, 41977 in drei Laeufen plus 34567 aus MCP_OAUTH_CALLBACK_PORT; der Entscheid ist die umgesetzte RFC-8252-7.3-Ausnahme, das Restrisiko Port-Squatting steht in der Doku"
  - "der Nachweis, dass ein abgeschaltetes DCR keinen ausgehenden Request erzeugt: 0 Sockets auf Port 443 gegen 4 in der Positivkontrolle, mit demselben Zaehler"
  - "docs/client-setup.md mit einer datierten Claude-Code-Sektion statt des Absatzes, der den Client als nicht akzeptiert beschrieb"
  - "docs/oauth-setup.md mit dem CIMD-Live-Beleg, den drei Kontrollproben und dem CLIENT-05-Entscheid samt Restrisiko"
  - "eine wiederverwendbare Messform: Pseudo-Konsole fuer einen Client, der ein Terminal verlangt, und /proc-Zaehlung fuer einen ausgehenden Request, mit Positivkontrolle"
affects: [AUTH-08, CLIENT-05, BL-05, D-35, 06-10, CONF-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Client, der ein Terminal verlangt, wird ueber CreatePseudoConsole angesprochen (Windows-Bordmittel per ctypes), nicht ueber ein installiertes Paket: kein Paket-Install, kein Legitimacy-Gate (T-06-SC)"
    - "Der Beleg fuer ein AUSBLEIBEN braucht eine Positivkontrolle mit demselben Messwerkzeug: erst wenn derselbe Zaehler den Vorgang im Positivfall sieht, ist eine Null ein Befund"
    - "Ein Port, der wechselt, wird ueber mindestens drei Laeufe mit vollstaendig aufgegebener Verbindung belegt, und der Override-Lauf steht getrennt, weil ein fester Wert nichts ueber Wechselhaftigkeit sagt"
    - "Eine Regel, deren Frage am gemessenen Client nicht stellbar ist (hier: Host-Wechsel, weil das Dokument beide Loopback-Namen traegt), wird zusaetzlich an der Regel selbst im laufenden Container nachgelesen"
    - "Der Weg, auf dem ein Schalter umgelegt wurde, gehoert in die Messdatei: Admin-Wert plus disable/enable fuer die drei Werte aus CONFIG_KEYS, unregister plus register fuer eine reine Umgebungsvariable"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-09-MEASUREMENTS.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-09-SUMMARY.md
  modified:
    - docs/client-setup.md
    - docs/oauth-setup.md
    - CHANGELOG.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Der Kandidat-Client ist der echte `claude mcp login`, und der Autorisierungs-Schenkel wurde nicht gefaelscht: der Client baut seine Anfrage, haelt seinen Loopback-Port, tauscht den Code und ruft das Werkzeug. Automatisiert sind nur die zwei Knoepfe, die ein Mensch drueckt, ueber scripts/oauth_flow_check.py:sign_in, also die im Projekt dokumentierte Abkuerzung"
  - "Gemessen wurde mit `alice` und nicht mit `jane`: derselbe Grund wie in 06-08, jane's Passwort steht nirgends und occ user:resetpassword haette ihre zwei OAuth-Verbindungen entwertet, also die Demo-Substanz fuer CONF-01"
  - "Der Client wurde in einem eigenen Projektverzeichnis unter dem Scratchpad konfiguriert (-s local), nicht in der globalen Serverliste des Owners; der Vorzustand von .claude.json wurde gesichert und der Nachzustand verglichen (T-06-61)"
  - "Der Versuch, den Browser-Oeffner stumm zu stellen, ist gescheitert und steht als Fund in der Messdatei statt als Luecke: claude.exe startet mit veraendertem %SYSTEMROOT% nicht mehr (Rueckgabewert 127, zweimal gemessen). Der Ausweg war --no-browser in der Pseudo-Konsole, also kein Fenster des Owners"
  - "Die drei Schalter wurden auf zwei verschiedenen Wegen umgelegt, weil NC_MCP_OAUTH_CIMD kein Admin-Wert ist: die drei aus CONFIG_KEYS ueber occ app_api:app:config:set plus disable/enable, der CIMD-Schalter ueber unregister (ohne --rm-data) plus register mit der Variable im json-info"
  - "Der ausgehende Request wurde gezaehlt und nicht abgeschaltet, und die Zaehlung wurde vorher positiv kontrolliert: ohne die Positivkontrolle waere 'keine Sockets' auch die Antwort eines kaputten Zaehlers"
  - "Die Mess-Zeilen dieses Laufs wurden nach der Messung entfernt (sechs clients, vier Autorisierungen von alice mit Token, sechs flows), wie 06-08 es mit den Cursor-Zeilen gemacht hat; die letzte lebende Verbindung wurde vorher ueber claude mcp logout und damit ueber /revoke beendet, nicht per Datenbankeingriff"
  - "uv.lock wurde erneut zurueckgesetzt (git checkout --): die Selbstangabe 0.1.0 gegen 0.1.2 ist der in 06-01 dokumentierte Punkt in deferred-items.md und nicht Aufgabe dieses Plans"
  - "Die drei READMEs, der Store-Text und appinfo/info.xml bleiben unangetastet: die Aussage dieser Messung betrifft Client-Kompatibilitaet, nicht die Installationsgeschichte"

patterns-established:
  - "Eine Messung darf die Erwartung des Plans widerlegen und muss den Grund liefern: der Default-Port 3118 aus der Recherche erscheint wirklich, aber nur im abgebrochenen Weg, und der Plan haette ihn als Beweis akzeptiert. Die getrennte Zusatzbeobachtung sagt, wann er kommt und wann nicht"

requirements-completed: [AUTH-08, CLIENT-05]

# Metrics
duration: 50min
completed: 2026-08-20
---

# Phase 06 Plan 09: Claude Code per Metadatendokument, und die Loopback-Portfrage Summary

**Claude Code 2.1.233 verbindet sich live gegen 0.1.2, ohne sich zu registrieren: seine
`client_id` ist die Adresse seines eigenen Metadatendokuments, die geschriebene
`clients`-Zeile traegt ein leeres Secret und die zwei portlosen Rueckadressen, und
`files_list` antwortet mit dem echten Inhalt des angemeldeten Kontos. Der Port, auf dem der
Client zurueckkommt, war in drei aufeinanderfolgenden Laeufen dreimal ein anderer (45157,
47608, 41977), und mit abgeschaltetem DCR hat die Instanz kein einziges Paket nach claude.ai
geschickt, gezaehlt gegen eine Positivkontrolle mit demselben Zaehler.**

## Performance

- **Duration:** 50 min
- **Tasks:** 3 von 3
- **Files modified:** 1 Messdatei, 2 Doku-Dateien, CHANGELOG, REQUIREMENTS

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | CIMD-Rundlauf mit Claude Code und die Portspalte | `943c5a1` |
| 2 | Die drei Kontrollproben live, mit gezaehltem Ausgang und Rueckweg | `892b724` |
| 3 | Doku sagt das Gemessene, CLIENT-05-Entscheid mit Restrisiko | `fd3749a` |

## Der Befund, in einer Tabelle

| Frage | Antwort, gemessen am 2026-08-20 gegen 0.1.2 (Digest `sha256:3ba4a2ce1921`) auf Nextcloud 34.0.3.2 |
|-------|--------------------------------------------------------------------------------------------------|
| Traegt das AS-Dokument beide Weichen? | ja: `client_id_metadata_document_supported: true` und `none` in `token_endpoint_auth_methods_supported` |
| Welche `client_id` schickt der Client? | `https://claude.ai/oauth/claude-code-client-metadata`, woertlich aus dem Containerlog (Assumption A2 bestaetigt) |
| Entsteht eine `clients`-Zeile ohne Registrierung? | ja: `client_secret_hash` leer, `redirect_uris` die zwei portlosen, `cimd_fetched_at` 16:06:38Z, `cimd_expires_at` 16:11:38Z |
| Verbindet er sich? | ja, `POST /token 200`, `Authenticated with "ncmcp"`, Rueckgabewert 0, in vier Laeufen |
| Ruft er ein Werkzeug mit Inhalt auf? | ja, `files_list` auf `/` mit 11 Eintraegen aus `alice`s Files-Home |
| Wechselt der Loopback-Port? | ja: **45157, 47608, 41977** in drei Laeufen, plus **34567** mit `MCP_OAUTH_CALLBACK_PORT` |
| Ist DCR ueber CIMD umgehbar? | nein: `400`, `/register` `404`, und **0 Sockets auf Port 443** gegen 4 in der Positivkontrolle |
| Nimmt der CIMD-Schalter DCR mit? | nein: `/register` bleibt `201`, und der frische DCR-Client erreicht die Zustimmungsseite |
| Wirkt die Allowlist auf den CIMD-Client? | ja, in beide Richtungen, mit derselben Fehlerseite wie bei einem nicht gelisteten DCR-Client |

## Die Portspalte, der Kern von CLIENT-05

```
run 1  16:06:38Z   http://localhost:45157/callback   -> POST /token 200
run 2  16:08:44Z   http://localhost:47608/callback   -> POST /token 200
run 3  16:09:11Z   http://localhost:41977/callback   -> POST /token 200
run 4  16:09:27Z   http://localhost:34567/callback   -> POST /token 200   (MCP_OAUTH_CALLBACK_PORT=34567)
```

Jeder Lauf begann mit `claude mcp logout`, also mit einer vollstaendig aufgegebenen
Verbindung. Der Override-Lauf steht getrennt, weil ein einzelner fester Wert nur beweist,
dass eine Umgebungsvariable greift.

Zwei Zusatzbeobachtungen erklaeren, warum der in der Recherche genannte Default trotzdem
nicht die Antwort ist: ohne Terminal bricht `claude mcp login` ab und nennt dabei **3118**,
und derselbe Aufruf nennt **48014**, sobald ein fremder Socket 3118 haelt. Der Default
existiert also, und er ist trotzdem kein Wert, auf den ein Server sich festlegen darf. Die
Mechanik dahinter steht als Programmtext des Clients in der Messdatei (Zufallsport aus
39152 bis 49151 auf Windows, Default erst als Letztes), und die Messung sagt es zuerst.

**Der Entscheid:** die RFC-8252-7.3-Ausnahme ist umgesetzt (seit 06-03) und bleibt umgesetzt,
weil die Messung das Problem bestaetigt. Ein Server, der den Port mitvergleicht, haette
diesen Client in drei von vier Laeufen an einer Eigenschaft abgewiesen, die er nicht waehlt.
Das Restrisiko Port-Squatting steht in `docs/oauth-setup.md` und wird nicht weggelassen:
jedes Programm auf dem Rechner kann einen Loopback-Port halten, aber Schema, Host, Pfad und
Query bleiben zeichengenau, und ohne den PKCE-Verifier ist der Code nicht einloesbar.

## Der Nachweis, dass kein Paket die Instanz verlaesst

Ein Skript im Container liest `/proc/net/tcp` und `/proc/net/tcp6` etwa 90-mal pro Sekunde
und sammelt jeden Socket mit Gegenport 443. **Mit Positivkontrolle**, weil eine Null ohne sie
auch die Antwort eines kaputten Zaehlers waere:

| Lauf | Schalter | `/authorize` | Sockets auf 443 |
|------|----------|--------------|-----------------|
| Positivkontrolle 16:16:23Z | alles an | `302` in **0,935 s** | **4** Zustaende zu `160.79.104.10:443` |
| Kontrollprobe 1, 16:17:30Z | `NC_MCP_OAUTH_DCR=0` | `400` in **0,126 s** | **0** |
| Kontrollprobe 2, 16:21:56Z | `NC_MCP_OAUTH_CIMD=0` | `400` in **0,115 s** | **0** |

Die 0,8 Sekunden Unterschied in der Antwortzeit sagen dasselbe ein zweites Mal.

## Abweichungen vom Plan

### 1. [Rule 3 - Blockierend] Der Client verlangt ein Terminal

- **Gefunden in:** Task 1
- **Problem:** Der Plan beschreibt den Rundlauf als durchlaufenden Lauf. `claude mcp login`
  prueft `stdin.isTTY` und bricht ohne Terminal mit
  `Couldn't complete authentication ... stdin isn't a terminal` ab, auch im Browser-Modus.
  Gepruefte Auswege: `winpty` aus Git Bash lehnt ab, solange sein eigenes `stdin` kein
  Terminal ist; ein Paket zu installieren ist ausgeschlossen (T-06-SC).
- **Loesung:** Eine Pseudo-Konsole ueber `CreatePseudoConsole`, per `ctypes` angesprochen,
  also Windows-Bordmittel. Der Treiber liegt im Scratchpad, nicht im Repository. Die
  Eigenheit steht als eigener Absatz in der Messdatei (Muster von 05-07).
- **Dateien:** keine im Repository
- **Commit:** `943c5a1`

### 2. [Rule 3 - Blockierend] Der Browser-Oeffner liess sich nicht stumm stellen

- **Gefunden in:** Task 1
- **Problem:** Der Client oeffnet einen Browser, und das Fenster gehoert dem Owner (dasselbe
  Prinzip wie T-06-52 und 06-08). Das mitgelieferte `open`-Paket baut sein Windows-Kommando
  aus `%SYSTEMROOT%`.
- **Loesung:** Mit veraendertem `%SYSTEMROOT%` startet `claude.exe` ueberhaupt nicht mehr
  (Rueckgabewert 127, zweimal gemessen, einmal mit einem nicht existierenden und einmal mit
  einem existierenden Verzeichnis). Der Ausweg war `--no-browser` in der Pseudo-Konsole: in
  den vier gezaehlten Laeufen wurde kein Fenster geoeffnet. Der gescheiterte Versuch steht
  als Fund 6.3 in der Messdatei, statt als Luecke weggelassen zu werden.
- **Dateien:** Messdatei, Abschnitt 6.3
- **Commit:** `943c5a1`

### 3. [Rule 2 - Vollstaendigkeit] Die Gegenprobe zum Host-Wechsel war am Client nicht stellbar

- **Gefunden in:** Task 1
- **Problem:** Der Plan verlangt eine Ablehnung fuer `127.0.0.1` gegen ein registriertes
  `localhost`. Das Dokument dieses Clients registriert **beide** portlosen Namen, also trifft
  eine solche Anfrage den jeweils anderen Eintrag und wird zu Recht angenommen. Als
  "Ablehnung nicht reproduzierbar" hingeschrieben waere das ein falscher Negativbefund.
- **Loesung:** Zwei Belege statt einem. Live an `/authorize`: ein Loopback-Host, den das
  Dokument nicht traegt (`[::1]`), wird `400`, und ein Host, der nur aussieht wie Loopback
  (`localhost.example.com`), ebenfalls. Und an der Regel selbst im laufenden Container:
  `loopback_match('http://127.0.0.1:45157/callback', ['http://localhost/callback'])` ist
  `None`. Dazu die Pfad-Gegenprobe, die der Plan verlangt.
- **Dateien:** Messdatei, Abschnitt 5
- **Commit:** `943c5a1`

### 4. [Rule 2 - Vollstaendigkeit] Zwei Wege fuer die Schalter statt einem

- **Gefunden in:** Task 2
- **Problem:** Der Plan nennt `unregister` plus `register` als den Weg fuer alle drei
  Schalter. Drei von ihnen (`oauth_dcr`, `oauth_allowlist_only`, `oauth_allowed_clients`)
  stehen aber in `exapp/config_values.py:CONFIG_KEYS` und sind damit Admin-Werte, fuer die
  `occ app_api:app:config:set` plus ein `disable`/`enable`-Zyklus genuegt. Nur
  `NC_MCP_OAUTH_CIMD` ist kein Admin-Wert.
- **Loesung:** Der billigere Weg fuer die drei, der teure nur fuer den einen, und beide Wege
  samt Begruendung in Abschnitt 7 der Messdatei. Der Registrierungs-Rumpf fuer den teuren Weg
  wurde aus `scripts/bootstrap_exapp.sh` uebernommen und ausserhalb des Repositories gebaut;
  das App-Secret ging nur ueber stdin (WR-06). Vor dem Abmelden wurden `oauth_data_key` und
  `public_url` ausserhalb des Repositories gesichert, und beide haben beide Zyklen
  ueberlebt.
- **Dateien:** Messdatei, Abschnitt 7
- **Commit:** `892b724`

### 5. [Rule 2 - Ehrlichkeit] Zwei Funde, die eine Erwartung korrigieren

- **Gefunden in:** Task 2
- **Problem:** Zwei Beobachtungen widersprechen dem, was ein Leser der Doku erwartet.
  Erstens zeigt die Absage bei abgeschaltetem CIMD die Seite `This link has expired` und
  nicht die Seite `Automatic registration is off` aus Kontrollprobe 1. Zweitens antwortet
  `POST /register` mit bewaffneter Allowlist und leerer Liste weiter `201`.
- **Loesung:** Beide als eigene Funde festgehalten, mit dem Grund aus dem Quelltext:
  `_resolve_cimd` gibt bei ausgeschaltetem Schalter `None` zurueck, es entsteht also gar kein
  Client, und die Allowlist sitzt in `get_client` und damit an `/authorize`, `/token` und
  `/revoke`, nicht an `/register` (`docs/oauth-setup.md` sagt woertlich "may **authorize**").
  Keine Aenderung am Code und keine an einer Fehlerseite: das waere keine Messung.
- **Dateien:** Messdatei, Abschnitte 9 und 10
- **Commit:** `892b724`

### 6. [Rule 2 - Owner-Regel] CHANGELOG-Eintrag

- **Gefunden in:** Task 3
- **Problem:** Der Plan listet `CHANGELOG.md` nicht, und die Owner-Regel verlangt fuer jede
  nutzerrelevante Aenderung einen Eintrag unter `## [Unreleased]`. Eine belegte Aussage
  ueber einen namentlich genannten Client ist nutzerrelevant, und der Vorlauf hatte genau das
  fuer Cursor so gehandhabt.
- **Loesung:** Ein Eintrag unter `### Changed`, der den Messbefund und die Version des
  gemessenen Clients nennt.
- **Dateien:** `CHANGELOG.md`
- **Commit:** `fd3749a`

### 7. [Rule 3 - Blockierend] uv.lock erneut zurueckgesetzt

- **Gefunden in:** Task 3
- **Problem:** Ein `uv run` ohne `--no-sync` synchronisiert und schreibt dabei
  `version = "0.1.2"` in den eigenen Paketblock von `uv.lock`, was als ungefragte Aenderung
  im Arbeitsbaum erscheint. Derselbe Punkt wie in 06-01.
- **Loesung:** `git checkout -- uv.lock`. Der Punkt steht bereits in `deferred-items.md`
  dieser Phase, ein zweiter Eintrag waere Rauschen. Alle Testlaeufe dieses Plans liefen mit
  `uv run --no-sync`.
- **Dateien:** keine
- **Commit:** keiner (Ruecksetzung)

## Verifikation

| Kriterium | Beleg |
|-----------|-------|
| Abschnitt 1 zitiert beide Felder des AS-Dokuments | `client_id_metadata_document_supported: true` und `none` in `token_endpoint_auth_methods_supported` |
| Abschnitt 2 nennt die gesendete `client_id` woertlich aus dem Log | `client_id=https%3A%2F%2Fclaude.ai%2Foauth%2Fclaude-code-client-metadata` |
| `clients`-Zeile Feld fuer Feld, leeres Secret, zwei portlose Adressen | Tabelle in 3.5; `client_secret_hash = None`, `redirect_uris` `["http://localhost/callback","http://127.0.0.1/callback"]` |
| Werkzeugaufruf mit Inhalt | `files_list` auf `/`, 11 Eintraege, darunter die zwei Marker-Dateien des 05-03-Fixtures |
| Zustimmungsseite mit Host der `client_id` und Loopback-Warnung | `Client ID host: claude.ai` und `Comes back to this computer` |
| Portspalte, drei Laufzeilen plus Override-Zeile | 45157 / 47608 / 41977 / 34567, je mit Uhrzeit |
| Zwei Ablehnungen in der Gegenprobe, mit Fehlerbild | Pfad, fremder Loopback-Host und Nicht-Loopback-Host je `400` mit `This app cannot be sent back safely`; dazu die Regel im Container nachgelesen |
| Topologie-Tabelle mit Version, nicht Tag | `34.0.3.2` aus `occ status`, Connector `0.1.2`, Digest `sha256:3ba4a2ce1921…`, Client `Claude Code 2.1.233` |
| `nc-mcp-test` und `findling-nextcloud` als unberuehrt genannt | Topologie-Tabelle und Abschnitt 11, `docker ps` je "Up 5 days" |
| Kein Credential in der Messdatei | Grep-Kriterium des Plans liefert 0; kein Token, kein Code, kein `code_challenge`, kein `state`, kein `flow`-Wert |
| Client-Konfiguration im Vorzustand | globale `mcpServers` zeichengleich `['firecrawl-mcp','obsidian','stitch']`, Projekteintrag des Messverzeichnisses verschwunden |
| "DCR aus" belegt Absage und ausbleibenden Request, mit Zaehlmethode | `400` plus `/register 404`, 0 Sockets gegen 4 in der Positivkontrolle, Methode in Abschnitt 7 |
| "DCR aus" belegt das fehlende Feld im AS-Dokument | `client_id_metadata_document_supported present: False` |
| "CIMD aus" belegt beides | URL-`client_id` `400`, `/register` `201`, frischer DCR-Client `302` |
| "Allowlist" belegt beide Richtungen und dieselbe Fehlerseite | leere Liste: CIMD und DCR je `403` `This app is not allowed`; gelistete URL: CIMD `302`, DCR weiter `403` |
| Weg je Schalter genannt | Abschnitt 7, Tabelle |
| Ausgangszustand aller drei Schalter belegt | `config:list` mit genau den zwei alten Schluesseln, keine `NC_MCP_OAUTH_*`-Variable im Container, AS-Dokument wieder vollstaendig |
| `occ app_api:app:list` meldet die App weiter als enabled | `mcp_connector (MCP Connector): 0.1.2 [enabled]` |
| `grep -n "does not accept yet" docs/client-setup.md` | 0 |
| Neue Claude-Code-Sektion mit Datum, Version, Messdatei-Verweis, Ports im Code-Block | "Measured against Claude Code 2.1.233 on 2026-08-20", Link auf `06-09-MEASUREMENTS.md`, vier Portzeilen im Code-Block |
| `docs/oauth-setup.md` nennt Entscheid, Restrisiko und die drei Hosts | Pitfall 6, Absaetze "The decision, and the risk that is accepted with it" und "The rule is applied to the three hosts of `LOOPBACK_HOSTS`" |
| `docs/oauth-setup.md` nennt die drei Kontrollproben je in einem Satz | CIMD-Abschnitt, drei Aufzaehlungspunkte mit Verweis auf die Messdatei |
| Em-Dashes und Vokabular-Gate | 0 in Messdatei, beiden Doku-Dateien und CHANGELOG |
| READMEs und Manifest unangetastet | `git diff --stat README.md README.de.md README.fr.md appinfo/info.xml` leer |
| Tests | `uv run --no-sync pytest tests/unit` **2155 passed**, Rueckgabewert 0; `tests/unit/test_exapp_env_setup.py` gruen |
| Lint | `uv run --no-sync ruff check .` "All checks passed", `ruff format --check .` "171 files already formatted" |
| Store im Vorzustand | `clients 2`, `flows 0`, `auth_codes 0`, `access_tokens 0`, `refresh_tokens 2`, `authorizations 2` (beide `jane`, beide nicht widerrufen), `user_access 0` |

## Was dieser Plan nicht tut

- **Keine Codeaenderung.** Gemessen wurde der Arbeitsbaum, wie er aus 06-06 kam. Die zwei
  Funde, die eine Erwartung korrigieren (Fehlerseite bei CIMD aus, `/register` unter der
  Allowlist), sind festgehalten und nicht behoben: eine Aenderung an einer Fehlerseite waere
  keine Messung, und `/register` verhaelt sich so, wie D-35 es beschreibt.
- **Keine Aenderung an den drei READMEs, am Store-Text und am Manifest.** Die Aussage betrifft
  Client-Kompatibilitaet, nicht die Installationsgeschichte, und die drei READMEs wurden in
  06-07 gemeinsam nachgezogen.
- **Keine Versionsanhebung und kein Release.** `<version>` bleibt 0.1.2, kein `v*`-Tag.
- **Kein Neustart fremder Software und keine Installation.** Nichts wurde geladen, nichts
  installiert, kein Fenster des Owners geoeffnet, keine Instanzversion angefasst.
- **Kein Eingriff an `jane`.** Kein `resetpassword`, kein Widerruf, keine ihrer zwei
  Verbindungen angefasst.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche: dieser Plan aendert keine Route, kein Schema und keinen
Auth-Pfad. Die Aenderungen sind Text. Drei Beobachtungen aus dem Lauf, die in die Bewertung
gehoeren und keine neue Flaeche sind:

- **T-06-57 bleibt `accept`, jetzt mit Messung dahinter.** Port-Squatting auf Loopback ist
  das Restrisiko der umgesetzten RFC-8252-7.3-Ausnahme, und es steht ab jetzt in
  `docs/oauth-setup.md` mit den drei Gruenden, aus denen es das kleinere Risiko ist.
- **Jeder abgebrochene Anmeldeversuch legt eine `flows`-Zeile an**, die auf ihr Zeitfenster
  wartet. Sechs Zeilen aus diesem Lauf, alle ohne Nutzerbezug und ohne Geheimnis, nach der
  Messung entfernt. Dasselbe Muster wie die DCR-Zeilen aus 06-08.
- **Die Absage bei abgeschaltetem CIMD zeigt eine Seite, deren Wortlaut nicht zur Ursache
  passt** (`This link has expired`). Das ist mit T-03-47 vereinbar, weil die Seite ohnehin
  nie sagt, welche Pruefung gefallen ist, aber es ist ein Kandidat fuer eine spaetere
  Textkorrektur.

## Requirements

- **AUTH-08 abgehakt.** Ein Client, der sich per Client ID Metadata Document ausweist, hat
  sich live verbunden und ein Werkzeug mit Inhalt aufgerufen, und die drei DCR-Kontrollen
  greifen live: Redirect-URI-Pruefung (drei Ablehnungen), Allowlist in beide Richtungen mit
  derselben Fehlerseite, und ein abgeschaltetes DCR ist nicht umgehbar, belegt bis hinunter
  zum nicht gesendeten Paket.
- **CLIENT-05 abgehakt.** Die Portfrage ist gemessen (drei Laeufe, drei Ports, plus
  Override-Lauf), der Entscheid ist die umgesetzte RFC-8252-7.3-Ausnahme, und das Restrisiko
  ist benannt statt weggelassen.
- **AUTH-09 war bereits abgehakt** und bekommt hier seinen Live-Zusatz: der Abruf ging an eine
  oeffentliche Adresse, beide aufgeloesten Adressen von `claude.ai` sind oeffentlich, 317
  Bytes bei einem Limit von 5120, und das Fenster kam aus dem `Cache-Control` der Antwort.

## Self-Check: PASSED

- `06-09-MEASUREMENTS.md` und `06-09-SUMMARY.md` liegen auf der Platte.
- Die drei Task-Commits `943c5a1`, `892b724` und `fd3749a` sind in `git log`.
