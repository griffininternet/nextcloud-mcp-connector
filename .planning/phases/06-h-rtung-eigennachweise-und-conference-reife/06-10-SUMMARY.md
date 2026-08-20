---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 10
subsystem: conference-material
tags: [conf-01, conf-02, runbook, demo, lightning-talk, measurement, per-user-switch, revocation]

# Dependency graph
requires:
  - phase: 06-07
    provides: "die Messtopologie auf 34.0.3.2 mit dem Connector aus dem Arbeitsbaum (0.1.2, Digest sha256:3ba4a2ce1921) und den Store-UI-Befund, den das Runbook als Ehrlichkeitsgrenze fuehrt"
  - phase: 06-08
    provides: "den Cursor-Befund, der im Runbook und im Talk als ehrliche Antwort auf die naheliegende Frage steht"
  - phase: 06-09
    provides: "den CIMD-Live-Beleg mit Claude Code 2.1.233 und die Portspalte, auf denen die Station 1 des Drehbuchs und die OAuth-Folie stehen"
provides:
  - "docs/conference-demo.md: Runbook in der Form von docs/store-submission.md, sieben Abschnitte, sechs Drehbuch-Schritte mit Kopier-Kommandos, Erwartung und Zeit je Schritt"
  - "docs/conference-talk.md: acht Folien mit je hoechstens drei Stichpunkten und ausformuliertem Sprechzettel, Summe 280 Sekunden, plus eine Tabelle, die jede Produktbehauptung an ihre Messdatei bindet"
  - "06-10-MEASUREMENTS.md: der belegte Durchlauf, 82,2 s Maschinenzeit gegen 82 s im Drehbuch, mit Rohbeleg je Station"
  - "der erste Beleg fuer die Wirkung des Per-User-Schalters am Draht: 403 mit access_disabled-Rumpf im pausierten Zustand, 200 mit Inhalt danach, ohne neues Token"
  - "der erste Beleg fuer die Wirkung des Widerrufs am Draht: 401 mit Zeiger, plus der mit 400 abgelehnte Auffrischversuch des Clients"
  - "eine wiederverwendbare Messform: ein Client, der ein Terminal verlangt, bekommt ein echtes Konsolen-Handle als stdin (AllocConsole plus CONIN$), billiger als die Pseudo-Konsole aus 06-09"
affects: [CONF-01, CONF-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Client, der ein Terminal verlangt, bekommt ein echtes Konsolen-Handle als stdin: FreeConsole, AllocConsole, CreateFileW('CONIN$'), open_osfhandle. CREATE_NEW_CONSOLE allein genuegt nicht, weil subprocess bei umgeleiteter Ausgabe STARTF_USESTDHANDLES setzt und stdin die Pipe des Elternprozesses bleibt"
    - "Ein Runbook wird gegen sich selbst getestet: einmal strikt nachfahren, und jede Stelle, an der man nachdenken musste, ist ein Fehler im Runbook und nicht im Protokoll"
    - "Eine Zeitangabe in einem Runbook wird zweigeteilt: Buehnenzeit und Maschinenzeit. Nur die zweite ist gegen eine Messung pruefbar, und nur sie steht in der Vergleichssumme"
    - "Die Wirkung eines Schalters wird zweimal belegt: am echten Client, weil ein Client sie sehen muss, und am Draht mit Token in der Hand, weil ein Client sich auch selbst irren kann"
    - "Ein Formular-POST mit der Faelschungssicherung, die die Seite gerendert hat, ist der Knopf. Was ersetzt wird, ist der Mensch, nie ein Schenkel des Protokolls"

key-files:
  created:
    - docs/conference-demo.md
    - docs/conference-talk.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-10-MEASUREMENTS.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-10-SUMMARY.md
  modified:
    - CHANGELOG.md
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/deferred-items.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Der Assistent des Drehbuchs ist ein echter MCP-Client und kein Skript, weil die Stationen 3 und 4 einen Akteur brauchen, der seine Verbindung ueber einen menschlichen Klick hinweg haelt. Kein Repo-Skript kann das, und einen neuen Baustein dafuer zu bauen war nicht der Auftrag: die zwei vorhandenen Skripte tragen Opener und Closer, der Client traegt die vier Stationen"
  - "Die Probe der Stationen 3 und 4 ist claude mcp list und nicht die Frage aus Station 2: gemessen haelt dieser Client nach einem 403 einen eigenen Vermerk und der nicht interaktive Weg fragt danach nicht mehr nach, auch nicht nach dem Freigeben. Ein Drehbuch, das darauf baut, faellt auf der Buehne aus, also steht die Begruendung im Schritt und nicht in einer Fussnote"
  - "Der Werkzeugaufruf in allen vier Zustaenden wurde zusaetzlich am Draht mit Token in der Hand gemessen (oauth_flow_check:connect plus tool_call), weil ein Beleg, der am Gedaechtnis eines fremden Clients haengt, kein Beleg fuer unsere Route ist"
  - "Gemessen wurde mit alice und nicht mit jane, aus demselben Grund wie in 06-08 und 06-09: janes Passwort steht nirgends, und ihre zwei Verbindungen sind die Demo-Substanz. Ihre Seite wurde nie geoeffnet"
  - "Die stehengebliebene Erwartung in scripts/acceptance_all_tools.py (15 gegen 16 Werkzeuge) wurde NICHT behoben, sondern in deferred-items.md notiert und im Drehbuch woertlich erklaert: ein Abnahmeskript aus Phase 1 verdient keinen Nebenbei-Eingriff aus einem Doku-Plan"
  - "Das Haken-Zeichen aus der Ausgabe des Clients steht in der Messdatei woertlich und im oeffentlichen Runbook als Beschreibung: Rohbeleg bleibt Rohbeleg, und der oeffentliche Text bleibt bei der Owner-Regel ohne Zeichen dieser Art"
  - "Der Projekteintrag des Messverzeichnisses in der Client-Konfiguration des Owners wurde nicht herausgeschnitten: die Datei wird zur Laufzeit einer Sitzung geschrieben, und ein Eingriff von aussen koennte einen gleichzeitigen Schreibvorgang ueberschreiben. Der Rest ist benannt statt beseitigt"
  - "Nichts eingereicht, niemand kontaktiert. Der Einreichungstext liegt als gekennzeichneter Entwurf am Ende von docs/conference-talk.md, mit dem Satz, dass der Owner sendet"

patterns-established:
  - "Ein Durchlauf, der das eigene Drehbuch widerlegt, ist der Zweck des Durchlaufs. Vier Korrekturen kamen aus diesem Lauf, und die wichtigste (die Probe der Stationen 3 und 4) haette man am Schreibtisch nicht gefunden, weil sie an einer Eigenschaft des Clients haengt und nicht an unserer Route"

requirements-completed: [CONF-01, CONF-02]

# Metrics
duration: 30min
completed: 2026-08-20
---

# Phase 06 Plan 10: Das Conference-Material Summary

**Die Demo-Strecke steht als Runbook mit sechs Schritten, Kopier-Kommandos und einer Zeit je
Schritt, und sie ist einmal vollstaendig durchgefahren: 82,2 Sekunden Maschinenzeit gegen 82
Sekunden Behauptung, mit vier Fehlern im Drehbuch, die der Lauf gefunden und das Drehbuch
behoben hat. Der Per-User-Schalter und der Widerruf sind zum ersten Mal in ihrer Wirkung
belegt, in beiden Richtungen und zweifach: am echten Client (`Connected` gegen
`Needs authentication`, `200` gegen `403`) und am Draht mit Token in der Hand (Inhalt, dann
`403` mit `access_disabled`-Rumpf, dann wieder Inhalt, dann `401` mit Zeiger). Der
Lightning-Talk-Entwurf liegt als acht Folien mit Sprechzettel vor, 280 von 300 Sekunden, jede
Behauptung an ihre Messdatei gebunden. Eingereicht wurde nichts und kontaktiert wurde
niemand.**

## Performance

- **Duration:** 30 min
- **Tasks:** 3 von 3
- **Files modified:** 2 neue Doku-Dateien, 1 Messdatei, CHANGELOG, deferred-items

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Das Demo-Runbook fuer die Conference | `5b9271a` |
| 2 | Das Drehbuch einmal durchgefahren und die vier Fehler behoben | `21bd973` |
| 3 | Der Lightning-Talk-Entwurf auf fuenf Minuten | `a645e03` |
| 3b | CHANGELOG-Eintrag fuer die zwei Conference-Dateien | `a4bfc5a` |

## Der Durchlauf, in einer Tabelle

Gemessen am 2026-08-20 zwischen 16:51 und 17:03 UTC gegen 0.1.2
(Digest `sha256:3ba4a2ce1921`) auf Nextcloud 34.0.3.2, mit Claude Code 2.1.233 als Client.

| Schritt | Gemessen | Drehbuch | Ergebnis |
|---------|----------|----------|----------|
| 0, der Flow in gedruckten Schritten | 5 s | 5 s | sieben Schritte, `tools=16`, Schlusszeile da |
| 1, ein Assistent verbindet sich | 6,2 s | 6 s | `Authenticated with "ncmcp"`, Rueckgabewert 0 |
| 2, echter Inhalt | 30 s | 30 s | `files_list` mit 12 Eintraegen aus `alice`s Home |
| 3, pausieren und freigeben | 25 s | 25 s | `403` und `! Needs authentication`, dann `200` und `Connected` |
| 4, eine Verbindung beenden | 11 s | 11 s | Zeilen 2 auf 1, `401` plus `POST /token 400` |
| 5, der ganze Werkzeugsatz | 5 s | 5 s | fuenfzehn Werkzeuge `OK` |
| **Summe** | **82,2 s** | **82 s** | Abweichung 0,2 Prozent |

## Was der Lauf am Drehbuch widerlegt hat

Vier Punkte, alle im Drehbuch behoben und in `06-10-MEASUREMENTS.md` Abschnitt 8 mit ihrem
Rohbeleg.

1. **Die Probe der Stationen 3 und 4 konnte nicht die Frage aus Station 2 sein.** Nach einem
   `403` haelt dieser Client einen eigenen Vermerk, und ein nicht interaktiver `claude -p`
   fragt danach nicht mehr nach, auch nicht nach dem Freigeben, und auch nicht ohne
   `--strict-mcp-config`. Fuenf Laeufe belegen es, und `claude mcp list` mit `POST /mcp 200`
   im Log belegt gleichzeitig, dass der Connector erreichbar war. Die Probe ist jetzt
   `claude mcp list`, mit der Begruendung im Schritt und einer Zeile in der Rueckfalltabelle.
2. **Die Zahl der Werkzeuge stand zweimal verschieden im Drehbuch**, 16 in Schritt 0 und 15
   in Schritt 5. Der Server veroeffentlicht 16, das Abnahmeskript ruft 15 davon auf, das
   sechzehnte ist `prepare_context`.
3. **Die versprochene Erfolgszeile von Schritt 5 gibt es nicht.** Das Skript endet mit
   `FAIL tools/list expected 15 tools, got 16` und Rueckgabewert 1, waehrend jede der
   fuenfzehn Zeilen `OK` traegt.
4. **Die Zeitangaben waren geraten**, 142 s behauptet gegen 82 s gemessen. Jede steht jetzt
   auf ihrer Messung.

## Die zwei Belege, die CONF-01 tragen

**Der Per-User-Schalter**, am Draht mit Token in der Hand, derselbe Werkzeugaufruf dreimal:

```
tool call, access on:       answered   {"path": "/", "count": 12, "items": [...]}
POST /mcp -> 403, body: {"error": "access_disabled", "error_description":
  "MCP access is switched off for this Nextcloud account. ..."}
tool call, access on again: answered   {"path": "/", "count": 12, "items": [...]}
```

**Der Widerruf**, danach, mit demselben Token:

```
POST action=disconnect -> 200, the page says 'Disconnected'
POST /mcp -> 401, WWW-Authenticate: Bearer error="invalid_token",
  error_description="Authentication required", scope="nextcloud",
  resource_metadata=".../.well-known/oauth-protected-resource/mcp"
```

Und am echten Client, in derselben einen Nachfrage: `401`, dann die zwei Discovery-Dokumente,
dann `POST /token 400`, weil das Refresh-Token mit der Verbindung gegangen ist. Der
Unterschied zwischen Pause und Widerruf ist am Statuscode ablesbar, `403` mit Grund gegen
`401` mit Zeiger.

## Abweichungen vom Plan

### 1. [Rule 3 - Blockierend] Der Client verlangt ein Terminal, und die Pseudo-Konsole war nicht noetig

- **Gefunden in:** Task 2, Schritt 1
- **Problem:** `claude mcp login` prueft, ob seine Eingabe ein Terminal ist, und endet sonst
  mit `stdin isn't a terminal` (derselbe Punkt wie in 06-09).
- **Loesung:** Ein echtes Konsolen-Handle als `stdin`: `FreeConsole`, `AllocConsole`,
  `CreateFileW("CONIN$")`, `open_osfhandle`, waehrend Ausgabe und Fehlerkanal in Dateien
  laufen. Kein Paket (T-06-SC) und billiger als die Pseudo-Konsole aus 06-09. Zwei Vorproben
  stehen in der Messdatei, weil die erste (`CREATE_NEW_CONSOLE` allein) fehlschlug und der
  Grund lehrreich ist: `subprocess` setzt bei umgeleiteter Ausgabe `STARTF_USESTDHANDLES`,
  und dann bleibt `stdin` die Pipe des Elternprozesses.
- **Dateien:** keine im Repository, die Treiber liegen im Scratchpad
- **Commit:** `21bd973`

### 2. [Rule 2 - Vollstaendigkeit] Der Beleg am Draht neben dem Beleg am Client

- **Gefunden in:** Task 2, Stationen 3 und 4
- **Problem:** Der Plan verlangt Rohbeleg fuer beide Richtungen des Schalters und fuer die
  Wirkung des Widerrufs. Der echte Client liefert `! Needs authentication` gegen
  `Connected`, aber nach dem `403` haelt er einen eigenen Vermerk (Abweichung 3), und damit
  haengt ein Teil des Belegs an seinem Gedaechtnis statt an unserer Route.
- **Loesung:** Eine zweite Messung mit eigener Verbindung ueber
  `scripts/oauth_flow_check.py:connect` und `tool_call`, derselbe Werkzeugaufruf in allen
  vier Zustaenden, plus die rohe HTTP-Antwort der MCP-Route. Damit steht der Rumpf der
  Absage woertlich im Protokoll und im Drehbuch, statt aus dem Quelltext zitiert zu werden.
- **Dateien:** Messdatei, Abschnitte 5.2 und 6.2; Drehbuch, Schritt 3
- **Commit:** `21bd973`

### 3. [Rule 2 - Ehrlichkeit] Ein Fund, der das Drehbuch umbaut statt es zu ergaenzen

- **Gefunden in:** Task 2, Station 3
- **Problem:** Nach dem Freigeben antwortete der Assistent weiter mit einer Absage, obwohl
  der Connector erreichbar war. Als "Client-Eigenheit" in eine Fussnote geschrieben waere
  das ein Drehbuch, das auf der Buehne an genau der Station ausfaellt, die das
  Alleinstellungsmerkmal traegt.
- **Loesung:** Fuenf Laeufe zur Eingrenzung (pausiert, freigegeben, freigegeben nach einem
  erfolgreichen `claude mcp list`, freigegeben ohne die zwei Konfigurationsflaggen), dann die
  Probe im Drehbuch getauscht und die Begruendung in den Schritt geschrieben, damit niemand
  die naheliegende Variante zurueckbaut. Am Code wurde nichts geaendert: es ist kein Fehler
  unserer Seite.
- **Dateien:** Drehbuch, Schritte 3 und 4 und die Rueckfalltabelle; Messdatei, Abschnitt 8.1
- **Commit:** `21bd973`

### 4. [Rule 2 - Uebergabe] Die stehengebliebene Werkzeugzahl im Abnahmeskript

- **Gefunden in:** Task 2, Station 5
- **Problem:** `scripts/acceptance_all_tools.py` erwartet 15 Werkzeuge, der Server hat 16,
  also endet der Lauf rot, obwohl jedes aufgerufene Werkzeug `OK` antwortet.
- **Loesung:** Nicht behoben. Der Punkt liegt in einem Abnahmeskript aus Phase 1, dieser Plan
  aendert `docs/` und eine Messdatei, und die Scope-Regel des Executors sagt fuer genau
  diesen Fall: notieren, nicht nebenbei anfassen. Eintrag in `deferred-items.md` mit dem
  vorgeschlagenen Weg, und im Drehbuch ein Satz, der die Zeile auf der Buehne entschaerft.
- **Dateien:** `deferred-items.md`, Drehbuch Schritt 5
- **Commit:** `21bd973`

### 5. [Rule 2 - Owner-Regel] CHANGELOG-Eintrag

- **Gefunden in:** Task 3
- **Problem:** Der Plan listet `CHANGELOG.md` nicht, und die Owner-Regel verlangt fuer jede
  nutzerrelevante Aenderung einen Eintrag unter `## [Unreleased]`. Zwei neue Dateien, die
  Leser des Repositories benutzen, sind nutzerrelevant, und 06-07 und 06-09 haben es genauso
  gehalten.
- **Loesung:** Ein Eintrag unter `### Added`, der beide Dateien und ihren Beleg nennt.
- **Dateien:** `CHANGELOG.md`
- **Commit:** `a4bfc5a`

### 6. [Rule 2 - Owner-Regel] Das Haken-Zeichen aus dem oeffentlichen Text

- **Gefunden in:** Task 3
- **Problem:** Das Runbook zitierte die Ausgabe des Clients mit dem Zeichen U+2714. Die
  Owner-Regel laesst Zeichen dieser Art im eigenen Text nicht zu.
- **Loesung:** Im oeffentlichen Runbook als Beschreibung ("`Connected`, with a check mark in
  front of it"), in der Messdatei woertlich, weil Rohbeleg Rohbeleg bleibt.
- **Dateien:** `docs/conference-demo.md`
- **Commit:** `a645e03`

## Verifikation

| Kriterium | Beleg |
|-----------|-------|
| Sieben Abschnitte in der Reihenfolge von `docs/store-submission.md` | `grep -c '^## '` = 7, Titel: Where this stands, What is shown, One time setup, The script, Pre demo checklist, What is deliberately not shown, Recovery |
| Vier Stationen je mit Erwartung und Zeit | Schritte 1 bis 4, je mit **Say**, **Do**, **Must be visible** und zwei Zeitangaben |
| Kopier-Kommandos im Code-Block | `grep -c '^```'` = 20, also zehn Bloecke |
| Beide vorhandenen Skripte werden aufgerufen | `oauth_flow_check` 2 Treffer, `acceptance_all_tools` 2 Treffer |
| Ehrlichkeitsabschnitt nennt Store-UI-Befund, AIO und die CIMD-Grenze | Abschnitt "What is deliberately not shown", plus Cursor als vierten Punkt |
| Vorher-Checkliste nennt `occ status`, den Digest und die drei OAuth-Schalter | die ersten drei Punkte der Checkliste, je mit Kommando und erwarteter Antwort |
| Zeile je Drehbuch-Schritt mit Dauer und Ergebnis | Messdatei Abschnitt 1, sechs Zeilen plus Summe |
| Widerruf mit Wirkung belegt | Messdatei 6.1 (Client, `401` plus `POST /token 400`) und 6.2 (`401` mit Zeiger, Token in der Hand) |
| Per-User-Schalter in beiden Richtungen belegt | Messdatei 5.1 (Client, `403` gegen `200`) und 5.2 (Inhalt, `403` mit Rumpf, Inhalt) |
| "Was am Drehbuch nicht gestimmt hat" plus die Korrekturen im Drehbuch | Messdatei Abschnitt 8, vier Punkte; `git diff 5b9271a..21bd973 -- docs/conference-demo.md` zeigt sie |
| Gemessene und behauptete Dauer | 82,2 s gegen 82 s, Abweichung 0,2 Prozent |
| Topologie-Tabelle mit Versionen und Digests, keine Tags | `34.0.3.2` aus `occ status`, AppAPI 34.0.0, Connector 0.1.2, `sha256:3ba4a2ce1921...`, Client 2.1.233 |
| Kein Credential in Messdatei und Doku | Grep-Kriterium des Plans liefert 0 in beiden; kein Token, kein Code, kein Cookie, kein Kontopasswort |
| `occ app_api:app:list` nach dem Lauf | `mcp_connector (MCP Connector): 0.1.2 [enabled]` |
| Die drei OAuth-Schalter im Ausgangszustand | `config:list` nennt genau `oauth_data_key` und `public_url`; keine `NC_MCP_OAUTH_*`-Variable im Container; AS-Dokument traegt `registration_endpoint` und `client_id_metadata_document_supported: true` |
| Store im Vorzustand | `clients 2`, `flows 0`, `auth_codes 0`, `access_tokens 0`, `refresh_tokens 2`, `authorizations 2` (beide `jane`, nicht widerrufen), `user_access 0` |
| Talk nennt Format und geschlossenen CfP mit Datum | Kopfzeile "lightning talk, five minutes" und "closed on 2026-08-03" |
| Talk sagt, dass der Owner entscheidet und nichts gesendet wurde | "Whether and where anything is submitted is the owner's decision", plus der Satz, dass kein Formular und keine Mail entstanden ist |
| Vier Differenzierer je als Folie, hoechstens drei Stichpunkte, ausformulierter Sprechzettel | Folien 3 bis 6, je 3 Stichpunkte |
| Summe der Sekundenangaben | 280, kleiner als 300; Tabelle am Ende der Datei |
| `grep -in "10 minute\|ten minute"` | 0 |
| Ein-Klick-Aussage stimmt mit 06-07 ueberein | Folie 3 sagt `Deploy and enable`, nennt 34.0.3.2 und den 34.0.2-Befund, wie die SUMMARY von 06-07 |
| Em-Dashes, Emojis, Vokabular-Gate | 0 in beiden Doku-Dateien, in der Messdatei und im CHANGELOG; keine Symbolzeichen in den oeffentlichen Dateien |
| Kein neues Paket | `git diff --stat pyproject.toml uv.lock` leer |
| Tests | `uv run --no-sync pytest tests/unit` **2155 passed** in 58,65 s, Rueckgabewert 0 |
| Lint | `ruff check .` "All checks passed", `ruff format --check .` "173 files already formatted" |
| Owner-Instanzen unberuehrt | `docker ps`: `nc-mcp-test` und `findling-nextcloud` je "Up 5 days" |

## Was dieser Plan nicht tut

- **Nichts eingereicht, niemand kontaktiert.** Kein Formular, keine Mail, kein Post, kein
  Kontakt. Der Einreichungstext liegt als gekennzeichneter Entwurf am Ende von
  `docs/conference-talk.md`, mit dem Satz, dass der Owner sendet.
- **Keine Codeaenderung.** Gemessen wurde der Arbeitsbaum. Der Fund am Client
  (Vermerk nach einem `403`) ist festgehalten und nicht behoben: er liegt nicht bei uns.
- **Kein Eingriff in `scripts/acceptance_all_tools.py`.** Der Punkt steht in
  `deferred-items.md`.
- **Kein Praesentationswerkzeug und kein neues Paket.** Folien und Sprechzettel sind
  Markdown im Repository, `pyproject.toml` und `uv.lock` sind unberuehrt (T-06-SC).
- **Kein Eingriff an `jane`.** Kein `resetpassword`, kein Widerruf, ihre Seite nie geoeffnet,
  ihre zwei Verbindungen nach dem Lauf unveraendert.
- **Keine Versionsanhebung und kein Release.** `<version>` bleibt 0.1.2, kein `v*`-Tag.
- **Keine Aenderung an den drei READMEs, am Store-Text und am Manifest.** Die zwei neuen
  Dateien sind Material fuer einen Vortrag, nicht die Installationsgeschichte.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche: dieser Plan aendert keine Route, kein Schema und keinen
Auth-Pfad. Die Aenderungen sind Text. Die vier Mitigationen des Plans, die am Ergebnis
haengen:

- **T-06-63 (Credential in einem kopierbaren Kommando):** die zwei `HP_SHARED_KEY`-Faelle
  erzeugen den Wert beziehungsweise lesen ihn aus `.env.exapp` zurueck, keiner schreibt ihn
  hin. Grep-Kriterium in Runbook und Messdatei liefert 0.
- **T-06-64 (Bildschirminhalt der Demo):** das Runbook sagt im Abschnitt "Where this stands"
  ausdruecklich, dass eine Wegwerf-Instanz mit einem Wegwerf-Konto benutzt wird, und nennt
  den Grund.
- **T-06-65 (der Talk behauptet mehr als gemessen ist):** eine eigene Tabelle bindet jede
  Produktbehauptung an ihre Fundstelle, und ein eigener Abschnitt sagt, was der Entwurf
  bewusst nicht behauptet.
- **T-06-68 (Instanzzustand bleibt verstellt):** der Nachzustand ist Zeile fuer Zeile belegt,
  Schalter im Ausgangszustand, App `enabled`, Store zaehlgleich zum Vorzustand.

Eine Beobachtung, die in die Bewertung gehoert und keine neue Flaeche ist: der Widerruf
nimmt das Refresh-Token belegt mit, sichtbar als `POST /token 400` im Auffrischversuch des
Clients. Das ist so gewollt und wurde hier zum ersten Mal an einem fremden Client gesehen.

## Requirements

- **CONF-01 abgehakt.** Die Demo-Strecke ist reproduzierbar aufgeschrieben, deckt Verbindung,
  Werkzeugaufrufe, Per-User-Verwaltung und Widerruf als je eine Station ab, ruft die
  vorhandenen Skripte auf statt neue zu bauen, und ist einmal wie geschrieben durchgefahren.
  Die Wirkung von Schalter und Widerruf ist belegt, zweifach und in beiden Richtungen.
- **CONF-02 abgehakt.** Der Lightning-Talk-Entwurf liegt vor, Englisch, acht Folien mit
  Sprechzettel, 280 von 300 Sekunden, die vier Differenzierer als Kern, jede Behauptung an
  ihre Messung gebunden. Der CfP-Stand steht im Kopf, die Einreichung ist Owner-Entscheid,
  und mit diesem Plan wurde nichts eingereicht.

## Self-Check: PASSED

- `docs/conference-demo.md`, `docs/conference-talk.md`, `06-10-MEASUREMENTS.md` und
  `06-10-SUMMARY.md` liegen auf der Platte.
- Die vier Commits `5b9271a`, `21bd973`, `a645e03` und `a4bfc5a` sind in `git log`.
