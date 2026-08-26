---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 03
subsystem: auth
tags: [oauth2.1, cimd, client-id-metadata-document, claude-code, conpty, appapi, harp, nextcloud, sqlite, e2e-measurement]

requires:
  - phase: 13-01
    provides: "Version 0.1.9 an sechs Stellen; der gemessene Kandidat wird aus diesem Quellstand gebaut"
  - phase: 13-02
    provides: "Enterprise-Texte in READMEs und Manifest; derselbe Quellstand"
  - phase: 06 (v1.1)
    provides: "CIMD-Implementierung, 06-09-Messprotokoll als Formvorbild, Loopback-Portregel"
provides:
  - "Live-Nachweis des CIMD-Pfades gegen den 0.1.9-Kandidaten (Messweg A, echter Client Claude Code 2.1.233), Digest sha256:1183f845"
  - "Rohprotokoll 13-MEASUREMENTS.md: Topologie mit Version UND Digest, Rundlauf, zwei Belege statt einem, Gegenprobe mit gezaehlten Sockets"
  - "Dauerhafte, selbsttragende Proof-Zeile in docs/oauth-setup.md (Datum, Befehl, Ergebnis, Digest)"
  - "Vier tote .planning-Verweise in docs/oauth-setup.md geschlossen"
  - "Pseudo-Konsolen-Treiber-Rezept: CreatePseudoConsole braucht STARTF_USESTDHANDLES mit 0x3/0x7/0xB"
affects: [13-04 Release 0.1.9, v1.3 Milestone-Audit, jede spaetere CIMD-Nachmessung]

tech-stack:
  added: []
  patterns:
    - "Messprotokoll mit drei Konventionen (occ-Kuerzel, Credential-Regel, Version plus Digest)"
    - "Zwei Belege fuer einen stillen Codepfad: geschriebene Zeile plus derselbe Abruf im Container"
    - "Gegenprobe durch Zaehlen statt Blocken, gleiches Skript im positiven und negativen Lauf"
    - "Selbsttragende Proof-Zeile ohne Verweis auf ein Nachbardokument"

key-files:
  created:
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-MEASUREMENTS.md
  modified:
    - docs/oauth-setup.md

key-decisions:
  - "Messweg A gefahren, nicht der Fallback B: der echte Client waehlte den CIMD-Weg selbst, damit belegt der Lauf die Client-Wahl und nicht nur die Serverseite"
  - "occ mcp_connector:purge --force bewusst NICHT gefahren: es beendet jede Verbindung der Instanz, und die Instanz haelt zwei lebende Verbindungen des Kontos jane (Demo-Substanz). claude mcp logout ruft /revoke, das erfuellt beide Haelften der Vorgabe"
  - "Die Positivkontrolle des Socket-Zaehlers wartet auf den Ablauf des Frischefensters: eine frische clients-Zeile loest keinen Abruf aus, und eine Null gegen eine Null belegt nichts"
  - "Alle vier .planning-Verweise in docs/oauth-setup.md geschlossen, nicht nur die zwei aus dem Plan: das Akzeptanzkriterium ist absolut und der Rest waere derselbe tote Link in einem Jahr"

patterns-established:
  - "ConPTY per ctypes: das Kind braucht STARTF_USESTDHANDLES mit den alten Konsolen-Handles 0x3, 0x7, 0xB, sonst haengt es an der Pseudo-Konsole und schreibt trotzdem auf die Pipes des Elternprozesses"
  - "Eine Adresse aus einer Terminalausgabe wird aus den Rohbytes gelesen und endet an der Escape-Folge, nie nach dem Entfernen der Escapes"

requirements-completed: [EXAPP-08]

duration: 40min
completed: 2026-08-25
---

# Phase 13 Plan 03: CIMD-Nachmessung gegen den 0.1.9-Kandidaten Summary

**Claude Code 2.1.233 verbindet sich live mit dem 0.1.9-Kandidaten allein über die Adresse seines Metadatendokuments, ohne eine einzige `/register`-Zeile im ganzen Containerleben, und mit abgeschaltetem Schalter geht null statt fünf Sockets nach außen.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-08-25T17:23:56Z
- **Completed:** 2026-08-25T18:04:03Z
- **Tasks:** 3 von 3
- **Files modified:** 2 (1 neu, 1 geändert)

## Accomplishments

- **Die Topologie führt den 0.1.9-Kandidaten**, belegt durch Version UND Digest: `mcp_connector 0.1.9 [enabled]`, Image `127.0.0.1:5000/mcp_connector:0.1.9`, Manifest-Digest `sha256:1183f8455c5f2ab420ee3d4b7eb8e0b2c207610c08dcd12b943ae78920759c47`, `APP_VERSION=0.1.9`, `RestartCount 0`, healthy. Vorher lief ein Mischstand (AppAPI 0.1.7, Container auf dem ghcr-Image 0.1.6).
- **Messweg A ist gefahren, nicht der Fallback.** Der echte Client hat den CIMD-Weg selbst gewählt: die `/authorize`-Zeile trägt `client_id` als prozentkodierte `https://claude.ai/oauth/claude-code-client-metadata`, der Client hielt seinen eigenen Loopback-Port (41333, frei gewählt), tauschte den Code selbst ein (`POST /token 200`) und rief `files_list` selbst auf, mit `alice`s echtem Inhalt samt der zwei Fixture-Marker. Der Client meldete `Authenticated with "ncmcp"` und Rückgabewert 0.
- **"Ohne Registrierung" ist belegt und nicht behauptet, zweifach:** `docker logs nc_app_mcp_connector -t | grep -c 'POST /register'` gibt `0` über das ganze Leben des Containers, und die geschriebene `clients`-Zeile trägt `client_secret_hash` NULL plus `cimd_fetched_at`/`cimd_expires_at` mit einem 300-Sekunden-Fenster aus dem `Cache-Control`. Der zweite Beleg des stillen Abrufs: derselbe Abruf im Container, `HTTP 200, 317 bytes, lifetime 300s`.
- **Genau eine Gegenprobe, gezählt statt geblockt:** mit `NC_MCP_OAUTH_CIMD=0` antwortet `/authorize` mit `400` in 0,065 s und der Seite `This link has expired`, das AS-Dokument bewirbt die Fähigkeit nicht mehr, `registration_endpoint` bleibt, und der Zähler im Container sieht **0** Sockets mit Gegenport 443 gegen **5** in der Positivkontrolle mit demselben Skript. Danach ist der Schalter gelöscht und das AS-Dokument bewirbt die Fähigkeit wieder.
- **Die dauerhafte Proof-Zeile steht selbsttragend in `docs/oauth-setup.md`** und nennt alle fünf Behauptungen einzeln plus Digest und Gegenprobe. Vier tote `.planning`-Verweise sind geschlossen: `grep -n '\.planning' docs/oauth-setup.md` gibt keine Zeile mehr aus.

## Task Commits

1. **Task 1: Topologie auf den 0.1.9-Kandidaten heben und protokollieren** - `cc40647` (docs)
2. **Task 2: Der Rundlauf ohne Registrierung, mit zwei Belegen statt einem** - `e65e2c0` (docs), Nachzug `32164be` (fix: der Credential-Check trug sein eigenes Suchmuster)
3. **Task 3: Gegenprobe, Proof-Zeile und der tote Verweis** - `52f3679` (docs)

## Files Created/Modified

- `.planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-MEASUREMENTS.md` (neu, 566 Zeilen) - Rohprotokoll: Kopf mit den drei Konventionen aus 06-09, Topologie-Tabelle mit Version und Digest, Abschnitt je Frage mit Uhrzeit, Rundlauf, zwei Belege für den stillen Abruf, Gegenprobe mit beiden Socket-Zahlen, Wiederherstellung des Ausgangszustands
- `docs/oauth-setup.md` - neue datierte Proof-Zeile im Kapitel "Client ID Metadata Documents" neben dem Absatz von 2026-08-20, ein Aufzählungspunkt zur Gegenprobe, vier tote `.planning`-Verweise durch selbsttragende Aussagen ersetzt

## Decisions Made

- **Messweg A statt B.** Der Pseudo-Konsolen-Treiber stand nach drei Anläufen (siehe Deviations), und damit belegt der Lauf die Client-Wahl und nicht nur die Serverseite. Der HTTP-Treiber des Fallbacks wurde nie gebaut, es gibt also keine schwächere Aussage, die man mit der starken verwechseln könnte.
- **`purge --force` nicht gefahren.** Der Plan verlangt "beende die Verbindung über `/revoke` oder `occ mcp_connector:purge --force`" UND "halte fremden Zustand unberührt". Auf dieser Instanz schließen sich die zwei aus: `purge` beendet jede Verbindung, und `authorizations` hält zwei lebende Zeilen des Kontos `jane` vom 2026-08-20 (die Demo-Substanz für CONF-01). `claude mcp logout ncmcp` ruft `POST /revoke` zweimal mit `200`, die Zeile des Laufs trägt danach `revoked_at`, und `jane`s zwei Zeilen sind unverändert. Nur dieser Weg erfüllt beide Hälften.
- **Die Positivkontrolle wartet auf den Ablauf des Frischefensters.** `cimd_fetched_at` stand auf 17:40:16Z (aus dem ersten, gescheiterten Anlauf), das Fenster reichte bis 17:45:16Z, und der Rundlauf um 17:44:34Z hat deshalb die gecachte Zeile benutzt (0,208 s statt 0,9 s). Für den Socket-Zähler wurde bis 17:59:27Z gewartet, damit die Positivkontrolle wirklich einen Abruf zählt. Sonst wäre die Null der Negativkontrolle gegen eine Null gemessen worden.
- **Alle vier `.planning`-Verweise geschlossen, nicht die zwei aus dem Plan.** Der Plan nannte die Zeilen 314-315; die Datei trug vier Stellen (drei Messprotokolle in mit `02dd6e1` gelöschten Verzeichnissen, plus `.planning/BACKLOG.md`). Das Akzeptanzkriterium ist absolut formuliert, und die übrigen wären in einem Jahr derselbe tote Link.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `bootstrap_exapp.sh` bricht ohne `HP_SHARED_KEY` mit einer irreführenden Meldung ab**
- **Found during:** Task 1
- **Issue:** Der erste Lauf endete nach fünf Minuten mit `ERROR: Nextcloud is still not installed after five minutes.`, obwohl `occ status` `installed: true` meldete. Das Skript ruft `occ` über `docker compose exec` (`dc()`, Zeile 200) und ohne `HP_SHARED_KEY` in der Umgebung schlägt jeder compose-Aufruf gegen `compose.exapp.yml` fehl, also auch die Installationsprüfung.
- **Fix:** Wert aus `.env.exapp` in die Umgebung des Aufrufs exportiert und nirgends aufgeschrieben, wie der Plan es für compose-Aufrufe vorgibt. Der Fund ist im Protokoll festgehalten, damit ein Leser die zehn Minuten nicht ein zweites Mal ausgibt.
- **Files modified:** keine (Aufrufumgebung), Protokolleintrag in `13-MEASUREMENTS.md`
- **Verification:** Skript lief durch bis `exapp mcp_connector: enabled` und `0.1.9 [enabled]`
- **Committed in:** `cc40647`

**2. [Rule 3 - Blocking] Die Pseudo-Konsole allein macht `claude mcp login` nicht interaktiv**
- **Found during:** Task 2
- **Issue:** Nach `CreatePseudoConsole` plus `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE` hing das Kind sichtbar an der Pseudo-Konsole (deren Titel trug den Kindnamen), schrieb aber weiter auf die Standard-Handles des messenden Prozesses und fragte diese nach einem Terminal. Ergebnis: weiter `stdin isn't a terminal`. Der Microsoft-Beispielcode kommt ohne die fehlende Zeile aus, weil sein Elternprozess selbst eine Konsolenanwendung ist.
- **Fix:** `STARTF_USESTDHANDLES` mit den drei alten Konsolen-Handle-Werten `0x3`, `0x7`, `0xB` im `STARTUPINFOEX`. Gegengeprobt mit `cmd.exe /c echo`: vorher landete die Ausgabe im Elternprozess, danach im Transkript der Pseudo-Konsole. Danach kam `Or paste the redirect URL here:` aus dem Client, und der Rundlauf lief durch.
- **Files modified:** nur Scratchpad-Treiber, ausdrücklich außerhalb des Repositories; kein `uv add`, kein `pip install`, kein `npm install`, `git diff --numstat uv.lock pyproject.toml` leer
- **Verification:** `claude mcp login` endete mit `Authenticated with "ncmcp"` und Rückgabewert 0
- **Committed in:** `e65e2c0` (als Fund im Protokoll)

**3. [Rule 1 - Bug] Die Adresse aus der Terminalausgabe war stillschweigend verfälscht**
- **Found during:** Task 2
- **Issue:** Der Client druckt die Adresse zweimal, als Id und als sichtbaren Text eines OSC-8-Hyperlinks, und dahinter steht eine Cursor-Bewegung. Wer die Escapes erst entfernt und dann sucht, klebt das nächste Wort an den letzten Query-Parameter: aus `resource=...%2Fmcp` wurde `resource=...%2FmcpWaiting`, und `/authorize` lieferte eine Antwort ohne Flow.
- **Fix:** Die Adresse wird aus den Rohbytes gelesen, mit einem Muster, das an der Escape-Folge endet.
- **Files modified:** nur Scratchpad-Treiber; Fund im Protokoll festgehalten
- **Verification:** `authorize_resource` im Treiberprotokoll ist `http://127.0.0.1:8081/exapps/mcp_connector/mcp`, `/authorize` antwortete 302
- **Committed in:** `e65e2c0` (als Fund im Protokoll)

**4. [Rule 1 - Bug] Der Credential-Check im Protokoll trug sein eigenes Suchmuster**
- **Found during:** Task 2, nach dem Commit bemerkt
- **Issue:** Das inline geschriebene Suchmuster fand sich selbst und machte aus einer bestandenen Prüfung einen Treffer.
- **Fix:** Die Prüfung ist in Prosa beschrieben, das Muster steht nicht wörtlich in der Datei.
- **Files modified:** `13-MEASUREMENTS.md`
- **Verification:** der Wert-Grep gibt keinen Treffer, Exit 1
- **Committed in:** `32164be`

### Weitere Abweichungen ohne Auto-Fix-Charakter

**5. Das Akzeptanzkriterium des Credential-Greps ist strenger als seine Absicht.**
Der Plan verlangt, dass `grep -nE '(code_verifier|code_challenge|Bearer [A-Za-z0-9]|state=[A-Za-z0-9]{8}|password)'` keinen Treffer gibt. Gleichzeitig verlangt Task 1, dass das Protokoll die Credential-Regel aus 06-09 wörtlich trägt, und diese Regel nennt `code_challenge`, um es zu verbieten. Die beiden Kriterien sind zusammen nicht erfüllbar. Erfüllt ist die Absicht (T-13-10: keine Werte): ein Grep, der die fünf Namen jeweils **mit** folgendem Wert sucht, gibt keinen Treffer. Der Namens-Grep findet drei Zeilen, alle drei nennen einen Parameter- oder Verfahrensnamen (`code_challenge=<gekürzt>`, `code_challenge_method` gleich `S256`) und keine davon einen Wert. Das Protokoll benennt diesen Unterschied selbst.

**6. Der Plan nennt zwei tote Verweiszeilen, die Datei trug vier.** Siehe Decisions.

---

**Total deviations:** 4 auto-fixed (3x Rule 3/Rule 1 an Messwerkzeug und Aufrufumgebung, 1x Rule 1 im Protokoll), 2 dokumentierte Abweichungen von Plan-Kriterien
**Impact on plan:** Kein Scope Creep. Kein Produktivcode angefasst, kein Paket installiert, `uv.lock` und `pyproject.toml` unberührt. Alle vier Auto-Fixes waren notwendig, um überhaupt Messweg A fahren zu können, und drei davon sind neues, aufgeschriebenes Wissen für die nächste Nachmessung.

## Issues Encountered

- **Der Mischstand der Topologie war real.** Vor dem Lauf meldete AppAPI `0.1.7 [enabled]`, der Container lief auf `ghcr.io/street1983nk/mcp_connector:0.1.6`. Ohne den Vorschritt `occ app_api:app:unregister mcp_connector` (ohne `--rm-data`) hätte `bootstrap_exapp.sh` nur `registered` gemeldet und dieser Mischstand wäre gemessen worden. Der Vorschritt hat Volume und Autorisierungen überlebt: die zwei Konfigurationswerte `oauth_data_key` und `public_url` standen danach unverändert da.
- **`printenv` ist die falsche Stelle für einen Admin-Wert.** `docker exec nc_app_mcp_connector printenv NC_MCP_OAUTH_CIMD` findet nichts, auch mit gesetztem Schalter: ein Admin-Wert kommt nicht in die Container-Umgebung, sondern wird beim Prozessstart aus Nextcloud gelesen. Geprüft wurde deshalb am AS-Dokument und am Verhalten von `/authorize`. Im Protokoll festgehalten.

## User Setup Required

None - keine externe Dienstkonfiguration nötig. Kein Tag, kein Push: der Tag `v0.1.9` bleibt der Owner-Freigabe des Release-Plans vorbehalten.

## Next Phase Readiness

- **EXAPP-08 ist erfüllt und der v1.1-Debt-Befund W-5 geschlossen:** gemessen wurde eine Fassung nach `a47bb57` und `bd75cd8`, gegen den Quellstand, der getaggt wird, und vor dem Tag. Der Beweis hängt an keiner Owner-Freigabe.
- **Die Instanz ist im Ausgangszustand:** `oauth_cimd` ist gelöscht, `config:list` nennt genau die zwei Schlüssel von vorher, das AS-Dokument bewirbt die Fähigkeit wieder, der Container ist healthy mit `RestartCount 0`. Die Verbindung des Laufs ist über `/revoke` beendet, `jane`s zwei Verbindungen sind unberührt, `nc-mcp-test` und `findling-nextcloud` liefen durch.
- **Für den Release-Plan:** die Topologie läuft jetzt auf `127.0.0.1:5000/mcp_connector:0.1.9` aus dem lokalen Registry, nicht auf einem ghcr-Image. Wer nach dem Release gegen das veröffentlichte Artefakt prüfen will, muss die Registrierung erneut lösen (ohne `--rm-data`), das ist keine Nebenwirkung dieses Plans, sondern die Eigenschaft aus Pitfall 3.
- **Offen und bewusst offen:** die Proof-Zeilen der Runbook-Schritte 4 bis 8 in `docs/store-submission.md`. Sie gehören hinter die Ereignisse und damit in den Release-Plan.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*

## Self-Check: PASSED

- `13-MEASUREMENTS.md` vorhanden (566 Zeilen, Mindestmass 80)
- `docs/oauth-setup.md` vorhanden und geändert, `grep -n '\.planning'` leer, `Measured live on 2026-08` vorhanden
- Alle vier Commits in `git log`: `cc40647`, `e65e2c0`, `32164be`, `52f3679`
- Beide Gates grün: `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py tests/contract/test_tool_surface.py -q`, Exit 0
- Kein Em-Dash in einer der beiden Dateien, kein `archiv` in `docs/oauth-setup.md`
