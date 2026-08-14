---
phase: 01-server-kern
reviewed: 2026-08-14T00:00:00Z
depth: standard
files_reviewed: 45
files_reviewed_list:
  - src/mcp_connector/__init__.py
  - src/mcp_connector/config.py
  - src/mcp_connector/deps.py
  - src/mcp_connector/entry_http.py
  - src/mcp_connector/entry_stdio.py
  - src/mcp_connector/errors.py
  - src/mcp_connector/ids.py
  - src/mcp_connector/models.py
  - src/mcp_connector/paging.py
  - src/mcp_connector/provider_map.py
  - src/mcp_connector/nextcloud/__init__.py
  - src/mcp_connector/nextcloud/capabilities.py
  - src/mcp_connector/nextcloud/credentials.py
  - src/mcp_connector/nextcloud/http.py
  - src/mcp_connector/nextcloud/clients/__init__.py
  - src/mcp_connector/nextcloud/clients/caldav.py
  - src/mcp_connector/nextcloud/clients/carddav.py
  - src/mcp_connector/nextcloud/clients/dav.py
  - src/mcp_connector/nextcloud/clients/deck.py
  - src/mcp_connector/nextcloud/clients/notes.py
  - src/mcp_connector/nextcloud/clients/ocs.py
  - src/mcp_connector/nextcloud/clients/xml.py
  - src/mcp_connector/server/__init__.py
  - src/mcp_connector/server/reg_calendar.py
  - src/mcp_connector/server/reg_chatgpt.py
  - src/mcp_connector/server/reg_contacts.py
  - src/mcp_connector/server/reg_deck.py
  - src/mcp_connector/server/reg_files.py
  - src/mcp_connector/server/reg_notes.py
  - src/mcp_connector/server/reg_search.py
  - src/mcp_connector/tools/__init__.py
  - src/mcp_connector/tools/calendar.py
  - src/mcp_connector/tools/chatgpt.py
  - src/mcp_connector/tools/contacts.py
  - src/mcp_connector/tools/deck.py
  - src/mcp_connector/tools/files.py
  - src/mcp_connector/tools/notes.py
  - src/mcp_connector/tools/search.py
  - scripts/acceptance_all_tools.py
  - scripts/check_tool_budget.py
  - scripts/bootstrap_test_nc.sh
  - pyproject.toml
  - .github/workflows/ci.yml
  - compose.test.yml
  - vulture_whitelist.py
findings:
  critical: 0
  warning: 6
  info: 11
  total: 17
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-08-14
**Depth:** standard
**Files Reviewed:** 45
**Status:** issues_found

## Summary

Adversariales Review des Server-Kerns (38 Produktionsdateien, 3 Skripte, 4 Konfigurationsdateien) mit Fokus auf das Kernversprechen (kein Loeschen, kein Ueberschreiben, keine Freigabe-Aenderung), Credential-Sicherheit, Injection-Flaechen und echte Bugs.

**Das Kernversprechen haelt der Pruefung stand.** Die gesamte Schreibflaeche besteht aus exakt vier Create-Pfaden: zwei PUT mit `If-None-Match: *` (dav.py:464, caldav.py:346) und zwei POST auf Create-Routen (notes.py:93, deck.py:169). Es existiert kein DELETE, MOVE, COPY, PROPPATCH oder MKCOL im Quellcode; 200/204-Antworten auf Create-PUTs werden als gebrochenes Precondition-Verhalten laut gemeldet statt als Erfolg. Auch die uebrigen Verteidigungslinien sind belastbar: alle DAV-Bodies werden mit lxml gebaut (keine String-Interpolation), der XML-Parser ist gegen XXE/DTD gehaertet, `resourceUrl` aus der Unified Search wird nie gefetcht und immer auf die konfigurierte Base-URL zurueckgebaut (kein SSRF), Pfad- und Segment-Guards laufen vor jedem Request, Redirects werden nie gefolgt, Credentials tauchen in keiner Fehlermeldung und keinem Log auf, und der AUTH-01-Integrationstest beweist den Passthrough ohne Env-Credentials.

Kein Critical-Befund. Sechs Warnings betreffen einen unbehandelten Crash-Pfad im Bearer-Verifier auf feindlicher Eingabe, zwei Paging- bzw. Range-Randfaelle mit stillem Datenverlust, einen irrefuehrenden Tool-Hint, ein nichtdeterministisches Schreibziel beim Kalender-Create und eine zu breit gebundene Test-Nextcloud. Elf Infos dokumentieren kleinere Inkonsistenzen und Wartungsrisiken.

## Warnings

### WR-01: StaticBearerVerifier crasht auf nicht-ASCII-Token statt ihn abzulehnen

**File:** `src/mcp_connector/deps.py:94`
**Issue:** `secrets.compare_digest(token, self._token)` wirft `TypeError`, sobald eine der beiden Seiten nicht-ASCII-Zeichen enthaelt (verifiziert unter Python 3.13). Der `token`-Parameter ist Angreifer-kontrollierter Header-Inhalt: ein Bearer-Token mit nicht-ASCII-Zeichen produziert eine unbehandelte Exception in der SDK-Auth-Schicht (500) statt eines sauberen `None` (401). Umgekehrt bricht ein versehentlich nicht-ASCII konfigurierter `NC_MCP_STATIC_BEARER` jede Authentifizierung mit 500ern statt mit einer verstaendlichen Meldung. Kein Auth-Bypass, aber ein Crash-Pfad auf feindlicher Eingabe im Sicherheits-Layer.
**Fix:**
```python
async def verify_token(self, token: str) -> AccessToken | None:
    if not token:
        return None
    if not secrets.compare_digest(token.encode("utf-8"), self._token.encode("utf-8")):
        return None
    ...
```

### WR-02: files_search meldet am MAX_SEARCH_FETCH-Deckel stillschweigend Vollstaendigkeit

**File:** `src/mcp_connector/tools/files.py:111-125`
**Issue:** `fetch = min(offset + capped + 1, MAX_SEARCH_FETCH)` klemmt die SEARCH-Anfrage bei 500 Treffern. Sobald `offset + capped + 1 > 500` gilt (z.B. offset=480, limit=25), ist `len(hits) > offset + capped` strukturell falsch bzw. nie erfuellbar: Die Antwort traegt weder `truncated` noch `next`, obwohl auf dem Server weitere Treffer existieren koennen. Eine abgeschnittene Antwort ist damit von einer vollstaendigen nicht unterscheidbar, exakt die Verwechslung, die der eigene Docstring von `build_search_body` verhindern will.
**Fix:** Wenn `offset + capped + 1` den Deckel erreicht bzw. `len(hits) == MAX_SEARCH_FETCH` zurueckkommt, `truncated: true` plus einen Hinweis setzen (z.B. `"note": "result window capped at 500; narrow the folder or the term"`), statt Vollstaendigkeit zu implizieren.

### WR-03: files_read-Hint verweist auf einen Parameter, den das Tool nicht hat; fetch scheitert komplett an Dateien ueber 2 MB

**File:** `src/mcp_connector/tools/files.py:62-66,235-242` und `src/mcp_connector/server/reg_files.py:56-63`
**Issue:** `_SLICE_HINT` und der Fehler bei `size > HARD_MAX_BYTES` sagen dem Modell "pass offset and max_bytes (at most 2097152 bytes)". Das registrierte Tool `files_read` hat aber nur `path` und `offset`; ein `max_bytes`-Argument wird vom Schema abgelehnt. Das Modell wird also in einen garantierten Folgefehler geschickt. Verschaerfend nutzt `chatgpt._fetch_file` (tools/chatgpt.py:133) `files_tools.read` mit `offset=0`, sodass `fetch` fuer eine Textdatei ueber 2 MB gar keinen Inhalt liefern kann, obwohl ein markierter 512-KB-Anfang die nuetzliche Antwort waere.
**Fix:** Entweder `max_bytes` als Tool-Parameter registrieren oder den Hint auf die real existierenden Parameter umformulieren ("read again with offset ..."). In `_fetch_file` den Fall `size > HARD_MAX_BYTES` abfangen und den ersten Slice mit Truncation-Marker liefern statt den ToolError durchzureichen.

### WR-04: calendar_create_event ohne calendar-Parameter schreibt in ein nichtdeterministisches Ziel

**File:** `src/mcp_connector/tools/calendar.py:242-243`
**Issue:** `target = _select(calendars, calendar)[0]` nimmt ohne `calendar`-Parameter schlicht den ersten Eintrag der PROPFIND-Discovery. Die Reihenfolge eines Multi-Status ist protokollseitig nicht garantiert, und die Discovery liefert auch Kalender, die in das Konto hineingeteilt wurden. Ein Event kann damit ohne Absicht in einem geteilten Kalender landen, den andere Personen sehen, und dieser Server kann es per Design nicht wieder loeschen. Auch bei mehrdeutigem Namens-Match (URI vs. Displayname zweier Kalender) waehlt `[0]` stillschweigend.
**Fix:** Ohne Parameter bevorzugt den Kalender mit URI `personal` waehlen, sonst deterministisch sortieren und die getroffene Wahl in der Antwort benennen; bei mehrdeutigem Match einen ToolError mit den Kandidaten werfen statt still zu waehlen.

### WR-05: get_range akzeptiert 200 auf einen Range-Request und verfaelscht damit die Slice-Buchfuehrung

**File:** `src/mcp_connector/nextcloud/clients/dav.py:154-174` (mit `_check` 540-546) und `src/mcp_connector/tools/files.py:244-266`
**Issue:** `_check` laesst fuer GET sowohl 206 als auch 200 passieren. Ein Server oder Proxy, der den Range-Header ignoriert, antwortet 200 mit dem kompletten Body. `files.read` liefert dann bei `offset > 0` die gesamte Datei (bis zur vollen Dateigroesse, die den 2-MB-Deckel weit ueberschreiten darf, da der Deckel nur bei `offset == 0` greift) in einer Antwort ins Kontextfenster, und `used = len(data)` macht `truncated`/`next_offset` inkonsistent zur angefragten Scheibe.
**Fix:** In `get_range` nach dem `_check` pruefen: Wenn ein Range-Header gesendet wurde und der Status 200 ist, den Body lokal auf `[offset, offset+limit)` schneiden oder mit einem ToolError ("this server ignores Range requests") ablehnen.

### WR-06: Test-Nextcloud bindet auf 0.0.0.0, der Kommentar behauptet localhost-only

**File:** `compose.test.yml:18-19`
**Issue:** `ports: - "${NC_TEST_PORT:-8080}:80"` published auf allen Interfaces. Der Kommentar im selben File begruendet die Wegwerf-Credentials damit, dass die Instanz "only ever listens on localhost". Zusammen mit dem Default-Admin-Passwort `admin-test-pw` und dem im Bootstrap deaktivierten Bruteforce-Schutz (bootstrap_test_nc.sh:146) ist die Instanz im LAN des Entwicklers bzw. Runners erreichbar und trivial uebernehmbar.
**Fix:**
```yaml
ports:
  - "127.0.0.1:${NC_TEST_PORT:-8080}:80"
```

## Info

### IN-01: Propstat-Status-Erkennung ist eine lose Heuristik

**File:** `src/mcp_connector/nextcloud/clients/xml.py:97-101` (gleiche Logik in caldav.py:229-239, carddav.py:240-250, dreifach dupliziert)
**Issue:** `" 2" in status.text` erkennt 2xx nur zufaellig korrekt und behandelt einen fehlenden oder leeren Status als Erfolg. Robuster und ehrlicher: die Statuszeile parsen (`HTTP/1.1 200 OK` splitten, int-Vergleich `200 <= code < 300`). Die Duplikation ueber drei Module laedt zu divergierenden Fixes ein.
**Fix:** Eine gemeinsame `_is_ok`-Funktion in xml.py mit echtem Statuscode-Parsing; caldav/carddav importieren sie.

### IN-02: encode_event verbietet Doppelpunkte, die parse akzeptiert

**File:** `src/mcp_connector/ids.py:80-89`
**Issue:** `parse` liest `event:` mit `split(":", 1)` und toleriert Doppelpunkte im Objektnamen, `_join` in `encode_event` lehnt sie ab. Ein von einem Fremd-Client angelegtes Kalenderobjekt `foo:bar.ics` laesst `parse_ics` mit "Report this as a bug" scheitern und degradiert den ganzen Kalender im Fenster.
**Fix:** Im letzten Segment eines event-Ids den Separator zulassen (Encode symmetrisch zum Parse) oder das Segment URL-encoden.

### IN-03: Verwaistes Kompilat eines nie committeten reg_-Moduls im Produktionspaket

**File:** `src/mcp_connector/server/__pycache__/reg_zz_counterproof.cpython-313.pyc`
**Issue:** Zu diesem Kompilat existiert weder Quelldatei noch Git-Historie. Es belegt, dass zur Entwicklungszeit ein `reg_*`-Modul direkt in das live Paketverzeichnis geschrieben wurde. Da `_load_registrations` (server/__init__.py:100-112) jede `reg_*.py` im Paketordner importiert, wird jede versehentlich liegengebliebene Datei beim naechsten Start Teil der Tool-Oberflaeche. Der Contract-Test faengt neue Tools zwar auf, aber nur wenn er laeuft.
**Fix:** Pycache aufraeumen; Tests, die Registrierung per Datei beweisen wollen, in ein tmp-Package unter `tests/` schreiben lassen, nie in `src/`.

### IN-04: vulture_whitelist-Kommentar behauptet fuenfzehn Tools, listet zwoelf

**File:** `vulture_whitelist.py:14-29`
**Issue:** Ueberschrift "The fifteen tool functions", darunter stehen zwoelf Namen; `search`, `fetch` und `unified_search` fehlen (vermutlich, weil vulture sie ueber die gleichnamigen Modul-Funktionen fuer benutzt haelt). Der Kommentar dokumentiert damit einen falschen Zustand.
**Fix:** Kommentar praezisieren: zwoelf Eintraege plus ein Satz, warum die drei uebrigen keinen Whitelist-Eintrag brauchen.

### IN-05: Versionsstring an vier Stellen gepflegt

**File:** `src/mcp_connector/__init__.py:7`, `src/mcp_connector/server/__init__.py:42`, `src/mcp_connector/nextcloud/http.py:19`, `pyproject.toml:4`
**Issue:** `0.1.0` steht in `__version__`, im `MCPServer(version=...)`, als `0.1` im User-Agent und in pyproject. Ein Release-Bump vergisst erfahrungsgemaess mindestens eine Stelle; `/health` und `tools/list` wuerden dann verschiedene Versionen melden.
**Fix:** `importlib.metadata.version("nextcloud-mcp-connector")` als Quelle oder mindestens `__version__` in Server und User-Agent importieren.

### IN-06: resolve_credentials haengt an einem duck-typed getattr auf SDK-Interna

**File:** `src/mcp_connector/deps.py:65`
**Issue:** `getattr(ctx, "headers", None)` koppelt die Modus-Wahl an ein nirgends typisiertes Attribut des SDK-Context. Benennt eine SDK-Minor-Version das Attribut um, degradiert der Server still in den stdio-Modus (Env-Credentials). Im Passthrough-Deployment ohne Env-Credentials faellt das laut auf; der AUTH-01-Integrationstest deckt es ab, aber nur im Integration-Lauf, nicht im Unit-Gate.
**Fix:** Einen schnellen Matrix- oder Contract-Test ergaenzen, der auf dem echten SDK-Context das Vorhandensein von `.headers` asserted, damit ein SDK-Upgrade im Unit-Job bricht statt im Feld.

### IN-07: check_duedate akzeptiert naive Zeitstempel und blanke Daten

**File:** `src/mcp_connector/nextcloud/clients/deck.py:197-207`
**Issue:** `datetime.fromisoformat` akzeptiert `2026-09-01` und `2026-09-01T10:00:00` ohne Offset, obwohl der Hint einen Offset verlangt. Deck interpretiert naive Werte serverseitig in einer Zone, die der Nutzer nicht gewaehlt hat; genau die Fehlklasse, die die Kalender-Tools mit `parse_instant` bewusst ablehnen.
**Fix:** Wie in `calendar.parse_instant` auf `tzinfo is not None` pruefen und sonst mit dem vorhandenen `_DATE_HINT` ablehnen.

### IN-08: Limit-Politik inkonsistent: mal cappen, mal ablehnen

**File:** `src/mcp_connector/tools/notes.py:57-61`, `src/mcp_connector/tools/calendar.py:70-74` vs. `tools/files.py:100`, `tools/contacts.py:59`, `tools/search.py:70`, `tools/deck.py:54`
**Issue:** files, contacts, search und deck cappen ein Limit ausserhalb des Bereichs mit derselben Begruendung im Kommentar ("an error would only cost a round trip"), notes und calendar werfen einen ToolError. Auf der Wire-Ebene fangen die Field-Constraints beides ab, aber fuer direkte Python-Aufrufer und fuer die Wartung sind es zwei Politiken fuer dieselbe Frage.
**Fix:** Eine Politik waehlen (cappen) und in notes/calendar nachziehen.

### IN-09: Capabilities-Cache waechst ohne Eviction

**File:** `src/mcp_connector/nextcloud/capabilities.py:79-93`
**Issue:** `_cache` behaelt abgelaufene Eintraege fuer immer; im Passthrough-Modus entsteht pro jemals erfolgreich authentifiziertem Nutzer ein Eintrag. Kein Leak (Schluessel ohne Secret, Werte quasi-oeffentlich) und durch echte Logins begrenzt, aber ein langlaufender Multi-User-Server sammelt tote Eintraege.
**Fix:** Beim Miss abgelaufene Eintraege entfernen (ein `for`-Sweep) oder ein simples Groessenlimit mit FIFO-Verdraengung.

### IN-10: Bootstrap verschluckt echte Fehler von dav:create-calendar/addressbook

**File:** `scripts/bootstrap_test_nc.sh:94-110`
**Issue:** `ensure_calendar`/`ensure_addressbook` deuten jeden non-zero Exit als "already there". Ein echter Fehler (Tippfehler im Nutzernamen, kaputte dav-App) wird als Erfolg gemeldet; die Verifikation am Ende prueft nur alices Kalender, nicht bobs und kein Adressbuch.
**Fix:** Output erfassen und nur die bekannte "already exists"-Meldung als Skip werten; alles andere mit Output nach stderr und Exit 1.

### IN-11: build_app(env) suggeriert vollstaendige Konfiguration aus env, wired aber kein Auth

**File:** `src/mcp_connector/entry_http.py:57-67` mit `src/mcp_connector/server/__init__.py:38-49`
**Issue:** Das Auth-Wiring (`build_auth`) laeuft einmalig beim Import von `server/__init__` gegen `os.environ`. `build_app(env)` wendet ein uebergebenes `env` nur auf die Transport-Security an; ein Static Bearer in diesem `env` wird still ignoriert. Fuer Tests und zukuenftige Embedder ist das eine Falle, die wie eine Sicherheitsluecke aussieht (Bearer gesetzt, Server unbewacht), tatsaechlich aber ein API-Asymmetrie-Problem ist.
**Fix:** Docstring von `build_app` explizit machen ("auth is decided at import time from the process environment") oder das Auth-Wiring in `build_app` verschieben.

---

_Reviewed: 2026-08-14_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
