---
phase: 05-hardening-und-store-einreichung
plan: 07
subsystem: docs
tags: [open-webui, mucgpt, oauth2.1, dcr, rfc8707, client-setup, streamable-http]

requires:
  - phase: 03-oauth-2-1
    provides: "der Authorization Server samt DCR, Consent-Seite, /token und der redirect_uri_allowed-Regel aus D-35, gegen die Open WebUI hier gelaufen ist"
  - phase: 05-hardening-und-store-einreichung
    provides: "05-03 die read-only-Share-Fixture (geteilte plus ungeteilte Datei), ohne die die Leak-Gegenprobe mit zwei Konten nichts beweisen wuerde; 05-04 der Ort in oauth-setup.md, auf den die Client-Doku verweist"
provides:
  - "docs/client-setup.md deckt jetzt alle sieben Zielclients ab: Claude Desktop, Claude Code, Claude.ai, ChatGPT, Cursor, Open WebUI, MUCGPT"
  - "Open WebUI 0.11.0 ist Ende zu Ende verprobt: Discovery, DCR, Consent im Browser, Token, Refresh-Token, Werkzeugaufruf, und die Leak-Gegenprobe mit zwei Konten gleichzeitig"
  - "Die Open-WebUI-Stolperstelle (http auf einer LAN-Adresse) steht mit dem gemessenen Fehlertext in der Doku, plus zwei im Browser gefundene Stolperstellen, die im Plan nicht vorkamen"
  - "MUCGPT ist mit den zwei funktionierenden Konfigurationsschluesseln beschrieben und mit dem Preis des Out-of-the-box-Pfads, und die fehlende Verprobung ist als Luecke benannt statt uebergangen"
  - "Keine veraltete Aussage mehr in docs/client-setup.md: Werkzeugzahl 16 statt 15, keine Phasenverweise, Client-Matrix nicht mehr angekuendigt"

affects: [05-09-store-text, 05-10-verifikation, outreach-it-at-m, README-tool-count]

tech-stack:
  added: []
  patterns:
    - "Ein fremder Mehrbenutzer-Client wird mit seinem EIGENEN Client-Code gemessen, nicht mit einem nachgebauten: Token aus Open WebUIs Sitzungsspeicher, Header aus seinem bearer_auth_header, Transport aus seinem MCPClient"
    - "Ein Loopback-Weiterleiter aus der Standardbibliothek im fremden Container, damit Browser und Client dieselbe Zeichenkette benutzen, weil resource und issuer zeichengenau verglichen werden"
    - "Jede Stolperstelle in der Client-Doku nennt den gemessenen Fehlertext oder ihre Quelle; eine unverprobte Anleitung sagt das an sichtbarer Stelle"

key-files:
  created:
    - .planning/phases/05-hardening-und-store-einreichung/05-07-MEASUREMENTS.md
    - .planning/phases/05-hardening-und-store-einreichung/deferred-items.md
  modified:
    - docs/client-setup.md
    - .planning/STATE.md

key-decisions:
  - "Der Open-WebUI-Container bleibt fuer den Checkpoint stehen statt nach Task 1 entfernt zu werden: Task 2 ist der Browserteil derselben Umgebung, und eine zweite Aufsetzung waere eine zweite Messung"
  - "Stolperstelle (b) wird gegen den gemessenen Befund korrigiert: WEBUI_SECRET_KEY ist in 0.11.0 harte Startbedingung, und start.sh legt den generierten Schluessel ausserhalb des Datenvolumes ab, woran OAUTH_CLIENT_INFO_ENCRYPTION_KEY und OAUTH_SESSION_TOKEN_ENCRYPTION_KEY haengen"
  - "Zwei Stolperstellen kommen aus dem Browser und standen in keinem Research: der Zugriff einer Verbindung ist per Default Privat, und eine offene Nextcloud-Sitzung im selben Browser entscheidet still ueber das verbundene Konto"
  - "Der MUCGPT-Abschnitt traegt seine Luecke im ersten Absatz und nicht in einer Fussnote, samt der drei Punkte, die ein Nachweis braucht"
  - "Die Werkzeugzahl im README bleibt unangetastet und wandert nach deferred-items.md: files_modified dieses Plans ist ausschliesslich docs/client-setup.md"

patterns-established:
  - "Client-Doku-Muster: gemessene Version plus Digest im ersten Absatz, dann Voraussetzungen, dann numerierte Schritte mit erwartetem Log, dann die Stolperstellen mit ihrem echten Text"
  - "Leak-Gegenprobe durch einen fremden Client: zwei Konten dieses Clients, zwei Nextcloud-Identitaeten, ein Marker der geteilt ist und einer der es nicht ist, beide Richtungen in einem Lauf"

requirements-completed: [EXAPP-05]

duration: 75min
completed: 2026-08-19
---

# Phase 05 Plan 07: Client-Doku fuer Open WebUI und MUCGPT Summary

**Open WebUI 0.11.0 ist von der Vermutung zum gelaufenen Fall geworden, inklusive der Ablehnung, die nach unserem Fehler aussieht und keiner ist, und MUCGPT ist mit dem einen funktionierenden Weg, seinem Preis und seiner unverprobten Stelle beschrieben.**

## Performance

- **Duration:** 75 min
- **Started:** 2026-08-19T17:58Z
- **Completed:** 2026-08-19T19:05Z
- **Tasks:** 3 von 3 (Task 2 war ein blockierender Checkpoint, vom Orchestrator per Playwright im Browser bestaetigt)
- **Files modified:** 4 (1 Doku, 3 Planungsartefakte)

## Accomplishments

- **Open WebUI Ende zu Ende verprobt, serverseitig belegt und im Browser bestaetigt.** Discovery ueber den `resource_metadata`-Zeiger, DCR mit genau einer Redirect-URI und dem Namen `Open WebUI`, Scope aus unserer PRM, `resource` nach RFC 8707 zeichengenau, Refresh-Token ausgegeben, 16 Werkzeuge gelistet, `files_search` mit Inhalten des angemeldeten Kontos. Alle Zahlen mit Log-Auszug und Zeitpunkt in `05-07-MEASUREMENTS.md`.
- **Die dokumentierte Stolperstelle ist belegt statt behauptet.** `http` auf einer LAN-Adresse und auf einem internen Hostnamen je `400 invalid_redirect_uri` mit dem woertlichen Text, Positivkontrolle mit `localhost` `201`, und derselbe Fehler ein zweites Mal durch Open WebUI hindurch mit dem Wortlaut, den ein Admin dort liest.
- **Das Berechtigungsversprechen haelt durch einen fremden Mehrbenutzer-Client.** Zwei Open-WebUI-Konten, zwei Nextcloud-Identitaeten, ein Lauf: `bob` findet den read-only geteilten Ordner und nie alices ungeteilte Datei, `alice` findet beide.
- **MUCGPT ist beschrieben, ohne einen Nachweis zu behaupten, den es nicht gibt.** Die zwei Schluessel, der stillschweigend verworfene `headers`-Eintrag, das gemeinsame Dienstkonto als Preis, und die Luecke im ersten Absatz des Abschnitts samt Liste dessen, was ein Nachweis braucht.
- **Drei Klassen veralteter Aussagen sind raus.** Die angekuendigte Client-Matrix, die Werkzeugzahl 15 an drei Stellen der Datei, und jeder Verweis auf eine Phase, die vorbei ist, insbesondere die ExApp-Passage, die OAuth noch als Zukunft beschrieb.

## Task Commits

1. **Task 1: Open WebUI lokal anbinden und die Anleitung aus dem Lauf schreiben** , `631dbfb` (docs)
2. **Nebenbefund ausserhalb des Scopes** , `34f71f8` (docs)
3. **Checkpoint und laufende Topologie im State** , `397e3a4` (docs)
4. **Task 2: Der Browserteil des Open-WebUI-Rundlaufs** , `9ba9842` (docs)
5. **Task 3: MUCGPT-Abschnitt und die veralteten Aussagen** , `85303ab` (docs)

## Files Created/Modified

- `docs/client-setup.md` , zwei neue Client-Abschnitte (`### Open WebUI, step by step` mit acht Stolperstellen, `### MUCGPT` mit benannter Luecke) plus Bereinigung der veralteten Aussagen im Kopf, im stdio-Abschnitt und im ExApp-Abschnitt.
- `.planning/phases/05-hardening-und-store-einreichung/05-07-MEASUREMENTS.md` , das Protokoll in neun Abschnitten: Topologie, Discovery und Registrierung, `resource`-Parameter, Zustimmung und Tokenausgabe, Werkzeugaufruf, Gegenproben, Browserteil, Zwei-Konten-Leak-Check, und was der Lauf nicht belegt.
- `.planning/phases/05-hardening-und-store-einreichung/deferred-items.md` , die Werkzeugzahl im README und die zwei datierten Messzeilen, die absichtlich stehen bleiben.
- `.planning/STATE.md` , der Checkpoint und die laufende Topologie, damit ein Nachfolger keiner veralteten Wiederanfahr-Prozedur folgt.

## Decisions Made

Siehe `key-decisions` im Frontmatter. Zwei sind fuer spaeter wichtig:

- **Open WebUI registriert sich als vertraulicher Client mit `client_secret_post`**, nicht als public client wie Claude.ai und ChatGPT. Der eigene `ClientAuthenticator` aus Plan 03-06, der gegen den gespeicherten SHA-256-Hash vergleicht, ist damit nicht nur Vollstaendigkeit, sondern der real benutzte Pfad eines echten Clients. Grund liegt in Open WebUIs Quellcode: es behaelt seinen Default, weil unsere AS-Metadaten `client_secret_post` auflisten.
- **Unsere Registrierung hebt den Scope auf `nextcloud offline_access`**, obwohl Open WebUI nur `nextcloud` aus der PRM anfragt. Genau dieser Zusatz erzeugt das Refresh-Token. Das ist `REGISTERED_SCOPE` aus `oauth/metadata.py` und es ist jetzt an einem fremden Client bestaetigt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stolperstelle (b) des Plans war zu schwach formuliert**
- **Found during:** Task 1
- **Issue:** Der Plan liess `WEBUI_SECRET_KEY` als "sonst brechen die Tokens beim Neustart" dokumentieren. Gemessen an 0.11.0 ist die Lage anders und schaerfer: der Prozess startet ohne die Variable gar nicht, `start.sh` generiert stattdessen einen Schluessel in `.webui_secret_key` im Arbeitsverzeichnis, und das liegt nicht im Datenvolumen. Daran haengen `OAUTH_CLIENT_INFO_ENCRYPTION_KEY` und `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY`, also die gespeicherte Registrierung UND die gespeicherten Tokens.
- **Fix:** Stolperstelle 2 der Doku nennt den Mechanismus und die Folge (jede Verbindung jedes Nutzers muss neu autorisiert werden) statt der vagen Fassung.
- **Files modified:** `docs/client-setup.md`
- **Verification:** `env.py` Zeilen 714 bis 743 und `start.sh` Zeilen 32 bis 50 im laufenden Image gelesen.
- **Committed in:** `631dbfb`

**2. [Rule 2 - Missing critical information] Zwei Stolperstellen, die kein Research kannte**
- **Found during:** Task 2 (Browserteil)
- **Issue:** (a) Der Zugriff einer Tool-Server-Verbindung ist per Default "Privat", also sieht kein anderes Konto den Eintrag, und das sieht aus wie eine nie angelegte Verbindung. Das blockiert jede Mehrbenutzer-Installation, und der Plan kannte es nicht. (b) Eine im selben Browser offene Nextcloud-Sitzung ueberspringt die Anmeldeseite und geht direkt auf die Grant-Seite dieses Kontos, also kann man ohne Absicht das falsche Konto verbinden.
- **Fix:** Als Stolperstellen 7 und 8 aufgenommen, (a) zusaetzlich als eigener Schritt 6 der Anleitung, weil es kein Fehlerfall ist, sondern eine Einstellung, die man beim Anlegen setzt.
- **Files modified:** `docs/client-setup.md`, `05-07-MEASUREMENTS.md`
- **Verification:** Im Browser gemessen: mit dem Default sah ein Konto der Rolle `user` nichts, nach der Umstellung auf "Oeffentlich" sah dasselbe Konto den Eintrag und meldete sich selbst an.
- **Committed in:** `9ba9842`

**3. [Rule 3 - Blocking issue] Der Open-WebUI-Container kann `127.0.0.1:8081` nicht erreichen**
- **Found during:** Task 1
- **Issue:** Der Connector veroeffentlicht sich in dieser Topologie als `http://127.0.0.1:8081/exapps/mcp_connector`, und ein Container hat sein eigenes Loopback. Browser auf dem Host und Client im Container haetten damit zwei verschiedene Adressen gebraucht, und `resource` (RFC 8707) sowie `issuer` (RFC 8414) werden zeichengenau verglichen: mit zwei Adressen waere der Lauf nicht der Lauf gewesen, den ein Nutzer macht.
- **Fix:** Ein Weiterleiter aus der Standardbibliothek im Open-WebUI-Container legt dort `127.0.0.1:8081` auf `caddy:80`. In das fremde Image wurde nichts installiert (T-05-SC bleibt `accept`), und das Skript lebt im Scratchpad, nicht im Repo.
- **Files modified:** keine im Repo
- **Verification:** Derselbe URL-Aufruf liefert vom Host und aus dem Container dasselbe PRM-Dokument.
- **Committed in:** nicht committet, Messwerkzeug; dokumentiert in `05-07-MEASUREMENTS.md`, Abschnitt "Topologie des Laufs"

**4. [Rule 2 - Missing critical functionality] Die Umgebung bleibt fuer den Checkpoint stehen**
- **Found during:** Task 1, Abschluss
- **Issue:** Task 1 forderte, den Open-WebUI-Container nach dem Lauf zu entfernen. Task 2 ist der Browserteil derselben Umgebung. Beides zusammen geht nicht, und ein zweites Aufsetzen waere eine zweite Messung mit anderen Ids.
- **Fix:** Container und Topologie liefen weiter, die gespeicherte OAuth-Sitzung des Admins wurde geloescht und die Selbstregistrierung freigeschaltet, damit der Browserteil ein echter Erstlauf ist und ein zweites Konto moeglich wird. Adressen, Konten und Aufraeumkommandos standen im Checkpoint-Bericht und in `05-07-MEASUREMENTS.md`. Nach Task 3 abgeraeumt.
- **Files modified:** `.planning/STATE.md` (damit ein Nachfolger nicht der veralteten Prozedur folgt)
- **Verification:** `docker ps` waehrend des Checkpoints, `docker ps -a` nach dem Abraeumen.
- **Committed in:** `397e3a4`

---

**Total deviations:** 4 auto-fixed (1x Rule 1, 2x Rule 2, 1x Rule 3)
**Impact on plan:** Kein Scope-Zuwachs. Drei der vier machen die Doku genauer, als der Plan sie verlangt hatte, und die vierte war die Voraussetzung dafuer, dass der Checkpoint ueberhaupt durchfuehrbar war.

## Issues Encountered

- **Der Werkzeugaufruf im Chatfenster ist nicht gelaufen**, weil im Wegwerf-Container kein Modell hinterlegt ist. Geloest, indem der Aufruf ueber Open WebUIs **eigenen** MCP-Client mit dem in Open WebUI gespeicherten Token gemessen wurde: damit ist alles ausser der Modellentscheidung belegt, und die ist keine Eigenschaft dieses Servers. Steht so in `05-07-MEASUREMENTS.md`, Abschnitt 9.
- **Open WebUI schliesst die Selbstregistrierung nach dem ersten Konto** (`403` auf `/api/v1/auths/signup`) und setzt neue Konten auf die Rolle `pending`. Fuer die Zwei-Konten-Gegenprobe wurden `ui.enable_signup` und `ui.default_user_role` gesetzt; Wegwerf-Instanz.
- **Der Erststart des Images dauert Minuten**, weil Open WebUI ein Embedding-Modell von Hugging Face zieht. Kein Befund ueber unseren Server, deshalb nicht in der Doku.

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche. Dieser Plan hat keine Zeile Produktionscode angefasst, nur Dokumentation und Planungsartefakte; das Threat Register unten ist der Stand des Plans.

## Threat Model, Stand nach dem Lauf

| Threat ID | Disposition | Ergebnis |
|-----------|-------------|----------|
| T-05-32 | mitigate, gehalten | Die Regel aus D-35 ist unveraendert. Die Doku nennt die Anforderung statt die Regel zu lockern, und die Gegenprobe ist gemessen: zweimal `400 invalid_redirect_uri` mit woertlichem Text, Positivkontrolle `201`. |
| T-05-33 | mitigate, gehalten | Der MUCGPT-Abschnitt kennzeichnet den Pfad als Team- oder Dienstkonto, nennt die Konsequenz fuer das Berechtigungsversprechen und gibt drei konkrete Auflagen fuer so ein Konto. |
| T-05-34 | mitigate, gehalten | Kein Wert aus dem Testbestand in der Doku. Geprueft: `grep -c "alice-test-pw-01\|bob-test-pw-01\|owui-probe-pw" docs/client-setup.md` ist 0; alle Beispiele tragen Platzhalter. |
| T-05-35 | mitigate, gehalten | Der MUCGPT-Abschnitt sagt im ersten Absatz, dass er nicht gegen eine laufende Instanz verprobt ist, und `05-07-MEASUREMENTS.md` Abschnitt 9 listet, was dieser Lauf nicht belegt, inklusive des Chat-Werkzeugaufrufs. |
| T-05-SC | accept, unveraendert | Keine Installation im Projekt. Open WebUI lief als fremdes Image in einer Wegwerf-Umgebung und ist entfernt; in das Image wurde nichts installiert, der Weiterleiter ist Standardbibliothek. |

## Messprotokoll Open WebUI

Vollstaendig in [05-07-MEASUREMENTS.md](./05-07-MEASUREMENTS.md). Die Kurzfassung mit Zeitpunkten:

| Zeitpunkt (UTC) | Was | Ergebnis |
|-----------------|-----|----------|
| 18:02:39 | Gegenprobe `http` LAN und interner Hostname am `/register` | je `400`, `{"error":"invalid_redirect_uri","error_description":"redirect_uris must use https, except loopback addresses of native clients"}`; Positivkontrolle `localhost` `201` |
| 18:16:04 bis 18:16:07 | Discovery und DCR aus Open WebUI | `POST /mcp 401`, `GET /.well-known/oauth-protected-resource/mcp 200`, `GET /.well-known/oauth-authorization-server 200`, `POST /register 201` |
| 18:16:07 | Die eingegangene Registrierung im Store | `client_name` `Open WebUI`, `redirect_uris` count **1**, `scope` `nextcloud offline_access`, `grant_types` `authorization_code` und `refresh_token`, `token_endpoint_auth_method` `client_secret_post` |
| 18:16:20 | Autorisierungsanfrage | `resource=http://127.0.0.1:8081/exapps/mcp_connector/mcp`, `code_challenge_method=S256`, Scope-Quelle unsere PRM |
| 18:16:20 bis 18:16:24 | Zustimmung und Tausch | `GET /authorize 302`, `GET /authorize/consent 200` (nennt `Open WebUI` und `alice`), `POST /authorize/decide 200`, `POST /token 200` |
| 18:16:24 | Refresh-Token | `family_id` `Tkmj8xxnZ3w9_jixNtv9mQ`, `state` `active`, gueltig bis 2026-09-18; in Open WebUIs Speicher `has refresh_token True` |
| 18:19:17 | Werkzeugaufruf mit Open WebUIs eigenem MCP-Client | 16 Werkzeuge, `files_search` liefert alices Bestand, Log `POST /mcp 200 OK` |
| 18:20:22 | Gegenprobe durch Open WebUI hindurch | `400`, `Failed to register OAuth client: Dynamic client registration failed: {...invalid_redirect_uri...}`, im Connector-Log `POST /register 400` |
| Browserteil | Consent im Browser, zwei Konten | Kette bestaetigt bis "Available Tools 1"; zwei neue Stolperstellen gefunden |
| 18:50:20 | Zwei-Konten-Leak-Check | `alice`: geteilte Datei 1 Treffer, private Datei 1 Treffer. `bob`: geteilte Datei 1 Treffer, private Datei **0** Treffer |

## Offen: MUCGPT

**Die Luecke, ihr Grund und der fehlende Zugang, damit die Phasen-Verifikation SC 4 woertlich bewerten kann:**

- **Was fehlt:** Der MUCGPT-Abschnitt von `docs/client-setup.md` ist der einzige Client-Abschnitt der Datei ohne Messung. Er ist aus dem Quellcode von `it-at-m/mucgpt`, Stand 2026-08-18, abgeleitet: `mcp.py` (der `headers`-Filter auf `authorization`, `McpBearerAuthProvider.auth_flow` bevorzugt den Override vor den Pro-Nutzer-Tokens), `settings.py` (`MCPTransport.streamable_http`, Validator `forward_auth_override requires forward_token=true`), `react_agent.py` (`set_token(user_id, token)`).
- **Warum:** Es gibt keinen Zugang zu einer laufenden MUCGPT-Instanz. Das ist Assumption A4 aus `05-RESEARCH.md` und der Environment-Availability-Eintrag "Zugang zu einer echten MUCGPT-Instanz: blockiert die woertliche Lesart von SC4 fuer diesen Client". MUCGPT ist ein Fremdsystem der Stadt Muenchen; eine lokale Instanz aus dem Repo braucht ihren Keycloak und war in diesem Plan nicht vorgesehen.
- **Was ein Nachweis braucht**, so wie es auch in der Doku steht, damit der Owner es beim Erstkontakt mit it@M in einem Satz nachholen kann: eine Instanz mit ihrem Keycloak, ein Konto darauf, eine `config.yaml` mit der MCP-Quelle. Drei Pruefpunkte: kommt der `Authorization`-Header ueberhaupt an, kommt die Werkzeugliste zurueck, antwortet ein Werkzeugaufruf mit Inhalten des konfigurierten Nextcloud-Kontos.
- **Was das fuer SC 4 heisst:** "Beide fehlenden Clients haben einen Abschnitt" ist erfuellt. "Open WebUI gegen den echten Client verprobt" ist erfuellt und belegt. Fuer MUCGPT ist die Anforderung "verprobt" **nicht** erfuellt und auch nicht als erfuellt dargestellt: die Luecke ist im ersten Absatz des Abschnitts benannt, mit der Liste dessen, was ein Nachweis braucht. Das ist genau die Form, die `must_haves` dieses Plans verlangt.
- **Die Anschlussfrage an it@M** bleibt wie in BL-12 formuliert: reicht ein Team- oder Dienstkonto, oder braucht es Pro-Nutzer-Treue. Der zweite Weg ist bei uns kleiner als BL-12 vermutete, weil MUCGPT ohne Override das eigene Keycloak-Token pro Nutzer schickt und wir mit `MODE_APPAPI` die Impersonation schon haben; es fehlen ein Vertrauensanker und eine Identitaetsabbildung. Feature, kein Fix, nicht v1.

## User Setup Required

Keins. Diese Aenderung ist Dokumentation.

Zwei Owner-Schritte entstehen daraus, beide nicht blockierend:

1. **MUCGPT-Verprobung beim Erstkontakt mit it@M**, drei Pruefpunkte siehe oben.
2. **Werkzeugzahl im README** (`15 tools` an zwei Stellen), notiert in `deferred-items.md`, gehoert in den Store-Text-Plan.

## Next Phase Readiness

- Success Criterion 4 der Phase ist fuer sechs von sieben Clients erfuellt und fuer den siebten mit benannter Luecke; `05-10` kann es woertlich bewerten, die Abschnitte "Messprotokoll Open WebUI" und "Offen: MUCGPT" oben sind dafuer gebaut.
- `EXAPP-05` ist abgehakt.
- Die Wegwerf-Umgebung ist abgeraeumt: `nc-mcp-owui-probe` entfernt, ExApp-Topologie heruntergefahren, Volumes mit der 05-03-Fixture behalten. Die Wiederanfahr-Prozedur in `STATE.md` gilt wieder unveraendert.
- Kein neuer Blocker. Die offenen Punkte der Phase sind unveraendert Assumption A5 (Live-Lauf des occ-Kommandos, Plan 05-08) und der Nextcloud-AIO-Smoke.

## Self-Check: PASSED

- Alle vier genannten Dateien existieren.
- Alle sechs genannten Commits existieren: `631dbfb`, `34f71f8`, `397e3a4`, `9ba9842`, `85303ab`, `aa17a54`.
- Volle Verifikation des Plans gruen: `uv run --no-sync pytest -q` (alle Tests), `ruff check .` ("All checks passed!"), `ruff format --check .` ("164 files already formatted").
- Die Akzeptanz-Greps des Plans: `follows in a later phase` = 0, `Open WebUI, step by step` = 1, `invalid_redirect_uri` = 2, `forward_auth_override` = 4, `not verified against a running` = 1, `transport: streamable_http` = 1, Em-Dashes = 0, Tabellenzeilen im MUCGPT-Abschnitt = 0, Testbestand-Passwoerter in der Doku = 0.
- Aufraeumen verifiziert: `nc-mcp-owui-probe` und `nc_app_mcp_connector` entfernt, ExApp-Topologie herunter, Netz `nc-mcp-exapp-net` weg, die drei Volumes behalten, `nc-mcp-test` und `findling-nextcloud` unberuehrt mit 4 Tagen Laufzeit.
- Nicht entfernt und absichtlich: das Image `ghcr.io/open-webui/open-webui:main` (7,16 GB). Ein erneuter Pull dauert Minuten, und `05-10` koennte es fuer eine Nachpruefung brauchen. Entfernen mit `docker rmi ghcr.io/open-webui/open-webui:main`.

---
*Phase: 05-hardening-und-store-einreichung*
*Completed: 2026-08-19*
