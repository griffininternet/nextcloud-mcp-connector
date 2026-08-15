---
phase: 1
slug: 01-server-kern
status: verified
threats_total: 102
threats_closed: 101
threats_open: 0
threats_accepted: 9
threats_transferred: 16
asvs_level: 2
block_on: critical
blocking: false
register_authored_at_plan_time: true
audited: 2026-08-15
created: 2026-08-15
---

# Phase 1: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken, Audit-Trail.
> Register-Quelle: die `<threat_model>`-Bloecke der Plaene 01-01 bis 01-14 (zur Planzeit verfasst).
> Verifikationsregel dieses Audits: eine Mitigation gilt erst als geschlossen, wenn sie als
> Code-Stelle (Datei:Zeile) oder als laufender Test nachweisbar ist. Dokumentation und Absicht
> allein zaehlen nicht.

---

## Trust Boundaries

| Boundary | Beschreibung | Kreuzende Daten |
|----------|--------------|-----------------|
| PyPI zu lokalem Environment | Fremder Code wird installiert und ausgefuehrt (Supply Chain) | Paketinhalte, Lockfile |
| Repository zu Oeffentlichkeit | Alles Gepushte ist dauerhaft public (Plan 12) | Quellcode, Doku, Planung |
| MCP-Client zu Server (stdio) | Der startende Prozess ist die Grenze, keine Header, keine Authorization | Tool-Parameter, Env-Credentials |
| Internet zu HTTP-Endpoint | Unauthentifizierte Requests treffen /mcp und /health | Authorization-Header, JSON-RPC |
| Host-Header zu Transport-Layer | DNS-Rebinding-Vektor auf den lokalen Port | Host-Header |
| Tool-Parameter zu Nextcloud-Request | Modellgenerierte Strings werden zu Pfaden, XML- und ICS-Inhalten | Pfade, Suchbegriffe, Titel, Zeiten |
| Server zu Nextcloud | Credentials verlassen den Prozess, Nextcloud authentifiziert und erzwingt ACLs | App-Passwort (Basic) |
| Fremde Provider-Antwort zu unserer Antwort | resourceUrl und Inhalte beliebiger installierter Apps | URLs, Texte, IDs |
| Client-gelieferte ID/Cursor zu Ressourcenzugriff | Ein opaker String steuert Aufloesung und Fortsetzung | Resource-IDs, Cursor-Handles |
| Arbeitsplatz zu fremdem Repository | Ausgehende, oeffentlich sichtbare Beitraege unter dem Owner-Konto | PR-Text, Commit-Metadaten |

---

## Threat Register

Status: `CLOSED` (verifiziert) · `OPEN` (Mitigation nicht auffindbar).
Disposition: `mitigate` · `accept` (dokumentiertes Risiko, siehe Log) · `transfer` (Kontrolle in anderem Plan).

### Plan 01-01 (Projekt-Skelett, Supply Chain)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-SC (P01) | Tampering | uv add / uv sync (PyPI) | mitigate | `docs/dependency-audit.md:7-11` (slopcheck 0.6.1, Owner-Sign-off 2026-08-14), httpx2 als `[SUS]` nur transitiv: `pyproject.toml:11-20` enthaelt kein httpx2; `uv.lock` ist getrackt (`git ls-files`), `.github/workflows/ci.yml:16,55` nutzt `uv sync --frozen` | CLOSED |
| T-01-01 | Information Disclosure | Credential-Handling | mitigate | `.gitignore:4-5` (`.env`, `.env.test`), getrackt ist nur `.env.test.example` (Platzhalter `xxxxx-...`), `.github/workflows/ci.yml` verwendet keinen einzigen `secrets.`-Ausdruck | CLOSED |
| T-01-02 | Spoofing | SSRF ueber Basis-URL | transfer | Empfangende Kontrolle vorhanden: `config.py:76-79` (Basis-URL nur aus `NC_MCP_URL`), `nextcloud/http.py:33` (`follow_redirects=False`) | CLOSED |
| T-01-03 | Elevation of Privilege | Path Traversal in Datei-Tools | transfer | Empfangende Kontrolle vorhanden: `nextcloud/clients/dav.py:72` `safe_path()`, Aufruf vor jedem Request (`dav.py:104-107,124,168`) | CLOSED |
| T-01-04 | Tampering | Create-only-Schreibschutz | transfer | Empfangende Kontrolle vorhanden: `dav.py:476` `If-None-Match: *`, `dav.py:487` `_check_write` | CLOSED |
| T-01-05 | Tampering | Injection in WebDAV-XML | transfer | Empfangende Kontrolle vorhanden: `dav.py:110-119` lxml-Builder, `nextcloud/clients/xml.py:28-37` `hardened_parser` | CLOSED |
| T-01-06 | Denial of Service | Unbegrenzte tools/list-Antwort | mitigate | `scripts/check_tool_budget.py:27` `BUDGET_BYTES = 12_500`, blockierender CI-Schritt `.github/workflows/ci.yml:34-35`; gemessen 10642 Bytes (01-VERIFICATION.md) | CLOSED |

### Plan 01-02 (HTTP-Basis, Credentials, Datei-Lesepfad)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-07 | Information Disclosure | Credentials in Logs und Tracebacks | mitigate | `nextcloud/credentials.py:20-21` (maskiertes `__repr__`), `server/__init__.py:85,90,95` (`raise ... from None`), `nextcloud/http.py:56-57` (httpx/httpcore auf WARNING), kein `print(` in `src/`; Tests `test_credentials_http.py:23,31,84` | CLOSED |
| T-01-08 | Spoofing | SSRF ueber Basis-URL | mitigate | `config.py:76-79`, `deps.py:166-168` (Basis-URL bleibt Deployment-Entscheidung), `nextcloud/http.py:33`, Redirect als Konfigurationsfehler `dav.py:552-556` mit `config.REDIRECT_HINT` | CLOSED |
| T-01-09 | Elevation of Privilege | Path Traversal in files_read | mitigate | `dav.py:72-101` (`..`, Backslash, Steuerzeichen), `dav.py:107` `quote(safe_path(path), safe='/')`; Tests `tests/unit/test_files_read.py:341` (kein HTTP-Call), `:349` | CLOSED |
| T-01-10 | Tampering | Create-only-Schreibschutz | transfer | Empfangende Kontrolle in Plan 03 vorhanden: `dav.py:473-476`, `dav.py:487-506` | CLOSED |
| T-01-11 | Tampering | Injection in WebDAV-XML | mitigate | `dav.py:110-119` (lxml, kein f-String), `xml.py:28-37` (`resolve_entities=False`, `no_network=True`, `huge_tree=False`), `xml.py:56-61` (DTD-Ablehnung); Tests `tests/unit/test_xml.py:129,136` | CLOSED |
| T-01-12 | Elevation of Privilege | Confused Deputy ueber Nutzer-Parameter | mitigate | `deps.py:57-74` (Identitaet nur aus `resolve_credentials`), Contract-Test `tests/contract/test_tool_surface.py:405` gegen `FORBIDDEN_PROPERTIES` (`:54`) | CLOSED |
| T-01-13 | Denial of Service | Unbegrenzte Datei-Antwort | mitigate | `tools/files.py:24-25` (512 KiB Default, 2 MiB hart), `:270-274` (`truncated` plus `next_offset`), `:234-239` mit `_is_text` (`:319-322`) lehnt Binaerinhalte ab; Test `test_files_read.py:125,249` | CLOSED |
| T-01-14 | Denial of Service | Brute-Force-Amplifikation | mitigate | `dav.py:549` `_check` ("No retry, ever"), 401 `dav.py:558-566`, 429 `dav.py:582-586`; Test `test_files_read.py:294` | CLOSED |

### Plan 01-03 (Upload, Bootstrap)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-15 | Tampering | Ueberschreiben via files_upload | mitigate | `dav.py:473-476` (PUT mit `If-None-Match: *`), `dav.py:487-506` (412 als `ConflictError`, 200/204 wird laut gemeldet); Integrationstest `tests/integration/test_files_roundtrip.py:78-97` | CLOSED |
| T-01-16 | Elevation of Privilege | Path Traversal im Upload-Ziel | mitigate | `tools/files.py:277ff` ueber `dav.files_url` mit `safe_path`+`quote` (`dav.py:104-107`); Test `tests/unit/test_files_upload.py:167` (kein HTTP-Call) | CLOSED |
| T-01-17 | Information Disclosure | App-Passwoerter aus dem Bootstrap im Repo | mitigate | `.gitignore:5`, getrackt nur `.env.test.example`; jeder Integrationstest erzwingt `user != "admin"` (9 Fundstellen, z.B. `tests/integration/test_files_roundtrip.py:45`) | CLOSED |
| T-01-18 | Spoofing | SSRF ueber Basis-URL | mitigate | `config.py:76-79`, `nextcloud/http.py:33`; kein Tool-Schema mit URL-Parameter (`test_tool_surface.py`) | CLOSED |
| T-01-19 | Tampering | Injection in WebDAV-XML | transfer | Empfangende Kontrollen vorhanden: `dav.py:110-119`, `dav.py:201-260`, `xml.py:28-37` | CLOSED |
| T-01-20 | Denial of Service | Grosse Uploads | accept | Siehe Accepted Risks Log AR-01; faktische Begrenzung durch den Client-Kontext, `dav.py:526-530` uebersetzt 413 in Klartext | CLOSED (accepted) |

### Plan 01-04 (HTTP-Transport, Auth-Modi)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-21 | Information Disclosure | Credentials im Authorization-Header | mitigate | `deps.py` enthaelt keinen Logging-Aufruf, `deps.py:153-157` nennt den Wert nie in der Fehlermeldung; Tests `tests/unit/test_http_modes.py:155` (kein Header-Echo, parametrisiert), `:166` (kein Log-Record) | CLOSED |
| T-01-22 | Spoofing | DNS-Rebinding auf den MCP-Port | mitigate | `entry_http.py:57-63` (`TransportSecuritySettings` aus `config.allowed_hosts`/`dns_rebinding_protection`), `config.py:121-145`; Tests `tests/unit/test_transport_security.py:71,76,81,87` | CLOSED |
| T-01-23 | Elevation of Privilege | Header als Identitaetsbehauptung | mitigate | `deps.py:3-8` (Begruendung im Code), `deps.py:65-74` leitet keine Autorisierung aus dem Header ab; Basis-URL nie aus dem Request (`deps.py:166-168`) | CLOSED |
| T-01-24 | Spoofing | Static Bearer per Timing-Angriff | mitigate | `deps.py:95-100` (`secrets.compare_digest` auf UTF-8-Bytes, WR-01-Fix `d8044c4`), kein Logging des Tokens; Tests `test_http_modes.py:206,214,223,231` | CLOSED |
| T-01-25 | Denial of Service | Brute-Force-Amplifikation | mitigate | `dav.py:549-566,582-586` und `ocs.py:170-196` (401/429 als Endzustand, kein Retry) | CLOSED |
| T-01-26 | Tampering | Path Traversal und XML-Injection | transfer | Derselbe Tool-Code laeuft im HTTP-Modus; Kontrollen `dav.py:72`, `xml.py:28-37` verifiziert | CLOSED |
| T-01-27 | Tampering | Create-only-Schreibschutz | transfer | Transportunabhaengig: `dav.py:476`, `caldav.py:349` | CLOSED |
| T-01-28 | Spoofing | SSRF ueber nutzergelieferte URL | accept | Siehe AR-02; kein URL-holendes Tool, alle Requests laufen ueber `files_url`/`api_url`/`object_url` aus `creds.base_url` | CLOSED (accepted) |
| T-01-29 | Information Disclosure | /health gibt interne Details preis | mitigate | `entry_http.py:47-54` (nur `status` und `version`); Test `test_transport_security.py:44,54` | CLOSED |

### Plan 01-05 (Suche ueber WebDAV, Cursor)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-30 | Tampering | XML-Injection im basicsearch-Body | mitigate | `dav.py:201-260` (nur `etree.SubElement`, Term als Elementtext); Test `tests/unit/test_dav_search.py:46` | CLOSED |
| T-01-31 | Denial of Service | XXE und Billion Laughs | mitigate | `xml.py:28-37` `hardened_parser`, in `parse_root`/`parse_multistatus` (`xml.py:40-94`) fuer jede Antwort; Tests `test_xml.py:129,136` | CLOSED |
| T-01-32 | Elevation of Privilege | Path Traversal ueber folder/path | mitigate | `tools/files.py:105` (`dav.safe_path(folder)`), `dav.py:186-194` `search_scope` baut `/files/<user>` aus dem Auth-Kanal, nie aus einem Parameter | CLOSED |
| T-01-33 | Tampering | Manipuliertes Cursor-Handle | mitigate | `paging.py:6-15` (kein Secret, keine Autoritaet), `paging.py:44-68` (defensives Dekodieren, nur `ToolError`), `paging.py:79-91` `check_scope`; Credentials weiterhin aus `deps` | CLOSED |
| T-01-34 | Denial of Service | Unbegrenzte Trefferlisten | mitigate | `dav.py:258-260` (`d:limit`/`nresults`), `tools/files.py:106,117,128-136` (Deckelung, `truncated`, `next`, `SEARCH_CAP_NOTE` aus WR-02-Fix `c8aef12`) | CLOSED |
| T-01-35 | Information Disclosure | Credential-Leak ueber Logs | mitigate | Geerbt und verifiziert: `credentials.py:20`, `http.py:56-57`, `server/__init__.py:85-95` | CLOSED |
| T-01-36 | Tampering | Create-only-Schreibschutz | transfer | Kontrolle in Plan 03 vorhanden: `dav.py:473-506` | CLOSED |
| T-01-37 | Spoofing | SSRF | accept | Siehe AR-02 | CLOSED (accepted) |

### Plan 01-06 (Notes)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-38 | Information Disclosure | Credentials in OCS-Fehlermeldungen | mitigate | `errors.py:9-15` (nur message plus hint), `ocs.py:170-218` nennt keine Header und keine Credential-URL, `ocs.py:214` `from None` | CLOSED |
| T-01-39 | Spoofing | SSRF ueber resourceUrl | mitigate | `tools/notes.py:188` `_note_id_from_resource_url` parst nur; jeder Request laeuft ueber `notes.api_url(creds, ...)` (`clients/notes.py:72,93`) | CLOSED |
| T-01-40 | Tampering | Falsche ID-Aufloesung | mitigate | `ids.py` als zentraler Codec (`encode_note` `:29`, `parse` `:50-77`), `tools/notes.py:79-85` ueberspringt Treffer ohne verwertbares Format | CLOSED |
| T-01-41 | Tampering | Create-only bei notes_create | mitigate | `clients/notes.py:93` ist der einzige Schreibaufruf des Moduls, kein PUT/DELETE (Grep ueber `src/` findet genau vier Schreibpfade); Annotation `server/__init__.py:53-58` `CREATE_ONLY` | CLOSED |
| T-01-42 | Elevation of Privilege | Confused Deputy | mitigate | `test_tool_surface.py:405` prueft alle Input-Schemas; Identitaet aus `deps.py:57-74` | CLOSED |
| T-01-43 | Denial of Service | Grosse Notizinhalte | mitigate | `tools/notes.py:41-42,57-60` (limit 25/100), `tools/notes.py:100` `read` liefert genau eine Notiz. Hinweis: die geplante Variante `exclude=content` entfaellt, weil kein Listen-Tool gebaut wurde | CLOSED |
| T-01-44 | Tampering | XML-Injection und Path Traversal | transfer | Kontrollen in Plan 02/05 vorhanden: `dav.py:72`, `dav.py:201-260`, `xml.py:28-37` | CLOSED |

### Plan 01-07 (Kalender)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-45 | Tampering | Injection in CalDAV-XML | mitigate | `caldav.py:125-149` (`build_calendar_query` per lxml, Attribute nur aus konvertierten Datumswerten) | CLOSED |
| T-01-46 | Tampering | Injection in ICS | mitigate | `tools/calendar.py:400-427` (`icalendar`-Objekte, `add()` statt Konkatenation) | CLOSED |
| T-01-47 | Denial of Service | XXE und Billion Laughs | mitigate | `caldav.py:198` `xml.parse_root`, Parser `xml.py:28-37` | CLOSED |
| T-01-48 | Tampering | Ueberschreiben eines Kalenderobjekts | mitigate | `caldav.py:346-349` (PUT mit `If-None-Match: *`), `caldav.py:442-460` (412 als Konflikt); kein DELETE im Modul; Integrationstest `tests/integration/test_calendar_roundtrip.py:191` | CLOSED |
| T-01-49 | Information Disclosure | Credentials in Fehlermeldungen | mitigate | `caldav.py:380` `from None`, geerbte Kontrollen aus Plan 02 verifiziert | CLOSED |
| T-01-50 | Denial of Service | Zu grosse Zeitraeume | mitigate | `tools/calendar.py:44-45,71-77` (limit 100/500), `:52,230` (`asyncio.timeout(PER_CALENDAR_TIMEOUT)`), `:98-125` (`degraded` statt Haengen) | CLOSED |
| T-01-51 | Elevation of Privilege | Path Traversal ueber calendar-Parameter | mitigate | `caldav.py:102-120` `safe_segment` plus `quote(..., safe='')` (`caldav.py:91-99`); Ziel stammt aus der Discovery-Liste (`tools/calendar.py:161,198`, WR-04-Fix `62c8680`) | CLOSED |
| T-01-52 | Spoofing | SSRF | accept | Siehe AR-02 | CLOSED (accepted) |

### Plan 01-08 (Kontakte)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-53 | Tampering | Injection in CardDAV-XML | mitigate | `carddav.py:130-162` (lxml-Builder); Test `tests/unit/test_carddav_client.py:240` | CLOSED |
| T-01-54 | Denial of Service | XXE und Billion Laughs | mitigate | `carddav.py:211` `xml.parse_root`, Parser `xml.py:28-37` | CLOSED |
| T-01-55 | Tampering | Fehlerhaftes vCard-Parsing per Regex | mitigate | `carddav.py:32,302` (`vobject.readComponents`), defensiver Feldzugriff; Test `test_carddav_client.py:331` | CLOSED |
| T-01-56 | Information Disclosure | Kontaktdaten fremder Nutzer | mitigate | `carddav.py:53-56,231-232` schliesst `z-server-generated--` und `z-app-generated--` aus (Systemadressbuch/Accounts), kein Nutzer-Parameter im Tool (`test_tool_surface.py:405`), ACL bei Nextcloud | CLOSED |
| T-01-57 | Tampering | Create-only-Schreibschutz | mitigate | Grep-Gegenprobe: `carddav.py` enthaelt kein PUT/DELETE/MOVE/COPY/PROPPATCH/MKCOL; Contract-Gate `tests/contract/test_no_destructive_calls.py:97` | CLOSED |
| T-01-58 | Denial of Service | Sehr grosse Adressbuecher | mitigate | `carddav.py:160-162` (`card:limit`/`nresults`), `tools/contacts.py:38-39,59,85-86` (Deckelung), `:43,106` (20 s Timeout je Buch) | CLOSED |
| T-01-59 | Elevation of Privilege | Path Traversal ueber addressbook-URI | mitigate | `carddav.py:93-120` `safe_segment` plus `quote` (`carddav.py:84-90`); URI stammt aus `discover_addressbooks` (`tools/contacts.py:61`) | CLOSED |
| T-01-60 | Spoofing | SSRF | accept | Siehe AR-02 | CLOSED (accepted) |

### Plan 01-09 (Deck)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-61 | Information Disclosure | Credentials in Deck-Fehlermeldungen | mitigate | `deck.py:206` `from None`, `ocs.py:217-218` erzeugt nur message plus hint, kein Header-Logging | CLOSED |
| T-01-62 | Tampering | Create-only bei deck_create_card | mitigate | `clients/deck.py:169` ist der einzige Schreibaufruf, kein PUT/DELETE im Modul; Annotation `CREATE_ONLY` (`server/reg_deck.py`), Gate `test_no_destructive_calls.py:97` | CLOSED |
| T-01-63 | Elevation of Privilege | Fremde Board- oder Stack-IDs | mitigate | `clients/deck.py:210-216` `_path_id` (nur numerisch), `tools/deck.py:195-215` `_require_write_permission` gegen die Board-Rechte, 403-Uebersetzung `ocs.py:217` | CLOSED |
| T-01-64 | Denial of Service | Grosse Boards | mitigate | `tools/deck.py:38,54,228-230` (limit 50/200, ein Request je Board, kompakte Felder) | CLOSED |
| T-01-65 | Spoofing | SSRF | accept | Siehe AR-02 | CLOSED (accepted) |
| T-01-66 | Tampering | Path Traversal und XML-Injection | transfer | Kontrollen in Plan 02/05 vorhanden und verifiziert | CLOSED |
| T-01-67 | Tampering | Ueberlanger Titel | mitigate | `clients/deck.py:178-195` `check_title` mit `MAX_TITLE_LENGTH` (`:50`), Pruefung vor dem Request | CLOSED |

### Plan 01-10 (Unified Search)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-68 | Spoofing | SSRF ueber fremde resourceUrl | mitigate | `provider_map.py:51-63` `absolute_url` baut auf `base_url` zurueck und ruft nichts ab; alle HTTP-Aufrufe in `src/` gehen ueber `creds.base_url`-Helper | CLOSED |
| T-01-69 | Tampering | Falsche ID-Aufloesung | mitigate | `provider_map.py:45` `UNKNOWN_KIND = "url"`, `:66-100` `extract_id` raet nicht, zentraler Codec `ids.py:50-77` | CLOSED |
| T-01-70 | Information Disclosure | Berechtigungsverletzung durch eigenen Index | mitigate | `tools/search.py:5,10` und Code ohne Ergebnis-Cache; einzige Caches sind HTTP-Client und Capabilities (`capabilities.py:78`), festgehalten durch `test_no_destructive_calls.py:127,168` | CLOSED |
| T-01-71 | Denial of Service | Haengender Provider | mitigate | `tools/search.py:89-91` (`asyncio.gather(..., return_exceptions=True)`), `:44,163` (`asyncio.timeout(PER_PROVIDER_TIMEOUT)`), `:99,114-115` (`degraded`) | CLOSED |
| T-01-72 | Denial of Service | Sehr viele Provider | mitigate | `tools/search.py:70` (Deckelung je Provider), `:95-117` (Cursors statt vollstaendiger Listen), kompakte Felder | CLOSED |
| T-01-73 | Information Disclosure | Credentials in Fehlermeldungen | mitigate | `tools/search.py:99,208` nennt nur Provider und Grund; geerbte Kontrollen aus Plan 02 verifiziert | CLOSED |
| T-01-74 | Tampering | Create-only, Path Traversal, XML-Injection | transfer | Kontrollen in Plan 02/03/05 vorhanden und verifiziert | CLOSED |

### Plan 01-11 (ChatGPT-Profil: search und fetch)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-75 | Spoofing | SSRF ueber url:-ID oder fremde resourceUrl | mitigate | `tools/chatgpt.py:21` (Regel im Code), `:103-116` (kind `url` wird beantwortet, nicht abgerufen); kein HTTP-Aufruf auf eine uebergebene URL in `src/` | CLOSED |
| T-01-76 | Elevation of Privilege | Path Traversal ueber file:-ID | mitigate | `chatgpt.py:118-131` (fileid zu Pfad via `find_by_fileid`), danach `files_tools.read` mit `dav.safe_path` (`tools/files.py:225`); `ids.parse` validiert das Format (`ids.py:50-77`) | CLOSED |
| T-01-77 | Tampering | Praefix-Verwechslung | mitigate | `ids.py:50-77` (unbekannter Praefix wird abgelehnt), Roundtrip-Tests `tests/unit/test_ids.py` | CLOSED |
| T-01-78 | Information Disclosure | Prompt Injection laesst das Modell schreiben | mitigate | Genau vier Create-Pfade im gesamten Quellcode (`dav.py:473`, `caldav.py:346`, `clients/notes.py:93`, `clients/deck.py:169`), kein DELETE/MOVE/COPY/PROPPATCH/MKCOL; Gate `test_no_destructive_calls.py:97` | CLOSED |
| T-01-79 | Denial of Service | Sehr grosse Inhalte im text-Feld | mitigate | `chatgpt.py:52` `TRUNCATION_NOTE`, `:133-142` (Cap aus `files.read`, Truncation in Text und Metadaten) | CLOSED |
| T-01-80 | Information Disclosure | Credentials in Fehlermeldungen | mitigate | Geerbte Kontrollen aus Plan 02 verifiziert (`server/__init__.py:85-95`, `credentials.py:20`) | CLOSED |
| T-01-81 | Tampering | Create-only-Schreibschutz | transfer | Kontrollen in Plan 03/07/09 vorhanden und verifiziert | CLOSED |
| T-01-82 | Tampering | XML-Injection | transfer | Kontrollen in Plan 02/05/07/08 vorhanden und verifiziert | CLOSED |

### Plan 01-12 (Public Repo, App-ID-Freeze)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-83 | Information Disclosure | Credentials im veroeffentlichten Repo | mitigate | Gegenprobe in diesem Audit wiederholt: `git grep -nE "NC_MCP_APP_PASSWORD=.+"` liefert nur Platzhalter (`README.md:42`, `docs/client-setup.md:38,85,147`, `.env.test.example:12`); keine getrackte `.env`; erweiterte Muster-Gegenprobe dokumentiert in `01-12-SUMMARY.md:108-109` | CLOSED |
| T-01-84 | Information Disclosure | Strategiedokumente in der oeffentlichen Historie | accept | Siehe AR-03; Owner-Entscheidung option-a dokumentiert (`01-12-SUMMARY.md:31,81,145`) | CLOSED (accepted) |
| T-01-85 | Spoofing | Falsche App-ID blockiert Store-Zertifikat | mitigate | `docs/app-id-freeze.md:1-17` (Status frozen, alle Identifier, Verfuegbarkeitsbelege, Kostenanalyse) | CLOSED |
| T-01-86 | Tampering | Falsche Permission-Angaben im README | mitigate | Contract-Test `tests/contract/test_tool_surface.py:425` (`test_the_readme_permission_table_matches_the_live_registry`), laeuft im CI (`ci.yml:31`); README-Tabelle `README.md:112-127` | CLOSED |
| T-01-87 | Elevation of Privilege | Path Traversal, Create-only, XML-Injection, SSRF | transfer | Kontrollen in Plan 02/03/05/07/08 vorhanden und verifiziert | CLOSED |

### Plan 01-13 (Upstream-Beitrag context_agent#227)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-88 | Information Disclosure | Interne Planung oder Secrets im PR-Text | mitigate | `docs/contrib/227-pr-body.md` (131 Zeilen): Gegenprobe auf `roadmap|phase|.planning|NC_MCP_|password|secret|token` ohne Treffer; Einreichung bleibt Owner-Schritt (`:8-9` Platzhalter) | CLOSED |
| T-01-89 | Repudiation | Fehlender DCO-Nachweis | mitigate | Fork-Commit `def1425b89b3` traegt `Signed-off-by: street1983nk <k.cherif@outlook.de>` (verifiziert per `git log` im Fork `C:\Users\Student\context_agent-fork\context_agent`) | CLOSED |
| T-01-90 | Tampering | Scope-Kriechen im fremden Repo | mitigate | `git show --stat def1425`: genau eine Datei `ex_app/lib/main.py`, 4 Insertions, 1 Deletion, keine neuen Dateien | CLOSED |
| T-01-91 | Spoofing | Beitrag unter falschem Absender | mitigate | Commit-Autor `street1983nk <k.cherif@outlook.de>`; keine automatische Einreichung erfolgt (`docs/contrib/227-pr-body.md:8-9` PR-URL weiterhin Platzhalter, `01-13-SUMMARY.md:96-97`) | CLOSED |
| T-01-92 | Tampering | Fremder Code wird lokal ausgefuehrt | accept | Siehe AR-04; Fork liegt ausserhalb des Repos, keine Installation, kein Start | CLOSED (accepted) |
| T-01-93 | Elevation of Privilege | Fuenf Kernkontrollen | transfer | Kein Produktionscode geaendert; Kontrollen in Plan 02/03/05/07/08 vorhanden und verifiziert | CLOSED |

### Plan 01-14 (Abnahme der Phase)

| Threat ID | Kategorie | Komponente | Disp. | Evidence | Status |
|-----------|-----------|------------|-------|----------|--------|
| T-01-94 | Tampering | Spaeterer Commit fuehrt destruktive Operation ein | mitigate | `tests/contract/test_no_destructive_calls.py:33-36,97,110` (AST-Gate mit Kommentarfilterung und Gegenprobe-Test), im CI `ci.yml:31` | CLOSED |
| T-01-95 | Elevation of Privilege | Neuer Nutzer-Parameter | mitigate | `tests/contract/test_tool_surface.py:54,405` prueft rekursiv alle Input-Schemas auf `user, username, uid, userid, owner` | CLOSED |
| T-01-96 | Information Disclosure | Credentials in Logs oder Doku | mitigate | `docs/client-setup.md:38,85,147` und `README.md:42` nennen nur Variablennamen mit Platzhaltern; Maskierung `credentials.py:20`, Logger-Pinning `http.py:56-57` | CLOSED |
| T-01-97 | Denial of Service | Token-Budget-Regression | mitigate | `scripts/check_tool_budget.py:16,27` (scharf gestellt: gemessen 10642, Budget 12500), blockierend im CI (`ci.yml:34-35`) | CLOSED |
| T-01-98 | Spoofing | SSRF | accept | Siehe AR-02; als Nicht-Ziel dokumentiert (`README.md:263`, `tools/chatgpt.py:21`) | CLOSED (accepted) |
| T-01-99 | Tampering | Create-only haelt in der Praxis nicht | mitigate | Integrationstest `tests/integration/test_files_roundtrip.py:78-97` (echte 412), Kalender `test_calendar_roundtrip.py:191`, plus Abnahmelauf ueber echten stdio-Client `scripts/acceptance_all_tools.py` (15/15 OK laut 01-VERIFICATION.md) | CLOSED |
| T-01-100 | Tampering | Path Traversal und XML-Injection im Gesamtlauf | mitigate | Unit- und Contract-Suite komplett im CI (`ci.yml:31`), 489 Tests gruen (01-VERIFICATION.md); enthaelt `test_files_read.py:341`, `test_dav_search.py:46`, `test_carddav_client.py:240`, `test_xml.py:129,136` | CLOSED |
| T-01-SC (P14) | Tampering | Abhaengigkeits-Upgrade kurz vor Phasenabschluss | mitigate | `uv.lock` getrackt und `uv sync --frozen` im CI (`ci.yml:16,55`); Dry-Run am 2026-08-15 nachgeholt und dokumentiert in `docs/dependency-audit.md` Abschnitt "Upgrade check at phase 1 closing" (Ergebnis: "No lockfile changes detected", mcp 2.0.0 aktuell) | CLOSED |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Akzeptiert von | Datum |
|---------|------------|-----------|----------------|-------|
| AR-01 | T-01-20 | Grosse Uploads binden Server und Nextcloud. Der Upload-Inhalt stammt aus dem Client-Kontext und ist dadurch faktisch begrenzt; ein expliziter Upload-Cap ist v1.x. Restrisiko niedrig fuer Selfhoster, Nextcloud beantwortet Ueberschreitungen mit 413 (`dav.py:526-530`) | Planentscheidung 01-03 (zur Planzeit dokumentiert), bestaetigt in `01-03-SUMMARY.md` Threat Flags | 2026-08-14 |
| AR-02 | T-01-28, T-01-37, T-01-52, T-01-60, T-01-65, T-01-98 | SSRF ueber eine nutzergelieferte URL. In Phase 1 existiert kein URL-holendes Tool; die Basis-URL ist eine Deployment-Entscheidung aus der Umgebung. Als Nicht-Ziel dokumentiert (`README.md:263`, `tools/chatgpt.py:21`) und code-seitig gestuetzt: jeder HTTP-Aufruf in `src/` wird aus `creds.base_url` gebaut, `follow_redirects=False` | Planentscheidung 01-04/05/07/08/09/14, im Code als Nicht-Ziel festgehalten | 2026-08-14 |
| AR-03 | T-01-84 | Strategiedokumente in der oeffentlichen Historie. Owner-Entscheidung option-a: alles oeffentlich inklusive `.planning`, Konsequenz benannt (Strategie, Wettbewerbsvergleich und Terminplanung sind lesbar), dafuer keine Historie-Akrobatik und maximale Glaubwuerdigkeit im Open-Source-Umfeld | Owner (`.planning/PROJECT.md`, Checkpoint Task 2, `01-12-SUMMARY.md:31,81`) | 2026-08-14 |
| AR-04 | T-01-92 | Fremder Code im lokalen Fork. Der Fork wird nur editiert und gepusht, nicht installiert und nicht gestartet; das Arbeitsverzeichnis liegt ausserhalb dieses Repos (`C:\Users\Student\context_agent-fork\context_agent`) | Planentscheidung 01-13, Vorgehen in `01-13-SUMMARY.md:66-72` belegt | 2026-08-14 |

*Akzeptierte Risiken tauchen in kuenftigen Audit-Laeufen nicht erneut als offen auf.*

---

## Unregistered Flags (neue Angriffsflaeche ohne Threat-Mapping)

Warnungen, kein Blocker. Sie stammen aus dem Code-Review 01-REVIEW.md und aus diesem Audit und
haben keine Entsprechung im zur Planzeit verfassten Register.

| Flag | Fundstelle | Warum sicherheitsrelevant | Empfehlung |
|------|------------|---------------------------|------------|
| UF-01 | `src/mcp_connector/server/__init__.py:100-110` plus verwaistes `server/__pycache__/reg_zz_counterproof.cpython-313.pyc` (Review IN-03) | `_load_registrations` importiert jede `reg_*.py` im Paketverzeichnis. Eine versehentlich dort abgelegte Datei wird beim naechsten Start Teil der Tool-Oberflaeche. Der Contract-Test faengt das nur, wenn er laeuft | Threat-ID in Phase 2 vergeben, Registrierungstests nie nach `src/` schreiben lassen, Build-Image ohne `__pycache__` |
| UF-02 | `src/mcp_connector/nextcloud/capabilities.py:78-93` (Review IN-09) | `_cache` kennt keine Eviction. Im Passthrough-Modus entsteht ein Eintrag pro jemals authentifiziertem Nutzer; langlebiger Multi-User-Server sammelt tote Eintraege (Speicher-DoS-Tendenz). Kein Secret im Schluessel | Sweep beim Miss oder FIFO-Limit, Threat-ID in Phase 2 |
| UF-03 | `src/mcp_connector/entry_http.py:57-63` mit `server/__init__.py:38` (Review IN-11) | `build_app(env)` wirkt vollstaendig konfigurierbar, verdrahtet aber kein Auth: ein Static Bearer im uebergebenen `env` wird still ignoriert, weil `build_auth()` beim Import gegen `os.environ` laeuft. Sieht fuer Embedder wie "Bearer gesetzt, Server unbewacht" aus | Docstring explizit machen oder Auth-Wiring nach `build_app` verschieben |
| UF-04 | `scripts/bootstrap_test_nc.sh:146`, `compose.test.yml:22,25-27` | Die Test-Nextcloud deaktiviert den Bruteforce-Schutz und nutzt ein Default-Admin-Passwort. Das Expositionsrisiko ist durch den WR-06-Fix (Bindung an `127.0.0.1`) entschaerft, bleibt aber eine Konfiguration, die nie in eine andere Umgebung wandern darf | Als Nicht-Produktions-Artefakt kennzeichnen, Threat-ID falls die Instanz je in CI-Netzen mit anderen Jobs laeuft |
| UF-05 | `01-01`, `01-05` bis `01-11`, `01-13`, `01-14` SUMMARY | Zehn der vierzehn SUMMARY-Dateien enthalten keinen Abschnitt `## Threat Flags`. Die Aussage "keine neue Angriffsflaeche" ist fuer diese Plaene nicht explizit protokolliert; 01-08 fuehrt stattdessen `## Threat Model Coverage` | Prozess: Threat-Flags-Abschnitt in jeder SUMMARY erzwingen |

---

## Offene Punkte (Blocker-Bewertung)

Keine. Der einzige offene Punkt aus dem Audit-Lauf (T-01-SC Plan 14, dokumentierter
Dependency-Dry-Run) wurde am 2026-08-15 direkt nach dem Audit geschlossen: Dry-Run
ausgefuehrt ("No lockfile changes detected") und in `docs/dependency-audit.md`
dokumentiert. Implementierungsdateien wurden vom Audit nicht veraendert.

---

## Security Audit Trail

| Audit-Datum | Threats gesamt | Closed | Open | Accepted | Transferred | Run By |
|-------------|----------------|--------|------|----------|-------------|--------|
| 2026-08-15 | 102 | 101 | 1 | 9 | 16 | gsd-security-auditor (Claude) |
| 2026-08-15 (Nachtrag) | 102 | 102 | 0 | 9 | 16 | Orchestrator: T-01-SC (P14) per dokumentiertem Dry-Run geschlossen |

Methodik: Register aus den `<threat_model>`-Bloecken der 14 Plaene extrahiert (102 Zeilen,
101 eindeutige IDs; `T-01-SC` erscheint in Plan 01 und Plan 14 mit unterschiedlicher
Mitigation). Jede `mitigate`-Position wurde per Grep und Lesen der Zielstelle gegen den
Code geprueft, jede `transfer`-Position gegen die empfangende Kontrolle im Zielplan, jede
`accept`-Position gegen einen dokumentierten Beschluss. Nicht Gegenstand dieses Audits:
Suche nach neuen, nicht registrierten Schwachstellen ausserhalb der oben gelisteten Flags.

---

## Sign-Off

- [x] Alle Threats haben eine Disposition (mitigate / accept / transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (AR-01 bis AR-04)
- [x] Neue Angriffsflaeche ohne Mapping als Unregistered Flags erfasst (UF-01 bis UF-05)
- [x] `threats_open: 0` bestaetigt (T-01-SC P14 am 2026-08-15 geschlossen)
- [x] `status: verified` im Frontmatter gesetzt

**Approval:** verified 2026-08-15 (alle 102 Register-Zeilen CLOSED; Unregistered Flags UF-01 bis UF-05 als nicht-blockierende Beobachtungen erfasst)
