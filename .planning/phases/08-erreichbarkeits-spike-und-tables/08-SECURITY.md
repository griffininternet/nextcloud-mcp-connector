---
phase: 08-erreichbarkeits-spike-und-tables
slug: erreichbarkeits-spike-und-tables
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-21
---

# Phase 8 , Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfprotokoll.
> Geprüfter Stand: HEAD (`dcaf7eb`), also nach den Review-Fixes bis `1e39e7a`.
> Grundhaltung dieser Prüfung: jede Minderung gilt als abwesend, bis eine Fundstelle im
> Implementierungsstand sie belegt. Doku und Absicht allein sind kein Beweis.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Messprozess zu Nextcloud (Plan 01) | Der Spike stellt Anfragen mit `APP_SECRET` als einzigem Credential; die Identität entsteht serverseitig aus `AUTHORIZATION-APP-API` | Impersonations-Header, Antwortkörper der Mail-App |
| Antwortkörper der Mail-App zu Testprotokoll (Plan 01) | Die Kontoantwort trägt IMAP- und SMTP-Hostnamen sowie Kontonamen | Bis zu 120 Zeichen Körper, Status, Content-Type, Location |
| Bootstrap-Skript zu Testinstanz (Plan 01) | Legt Apps und ein Mail-Konto per `occ` mit Administratorrechten an | App-Namen, Kontodaten, IMAP-Passwort eines nicht existierenden Hosts |
| Modell zu URL-Pfad (Plan 02) | `table_id` kommt aus einer Modellantwort und wandert in den Pfad einer Nextcloud-URL | Pfadsegmente, Query-Parameter |
| Client zu Nextcloud (Plan 02) | Alle URLs werden aus der konfigurierten Basis-URL gebaut; die Antwort ist fremde Eingabe | OCS-Envelope, App-JSON |
| Antwortkörper zu Tool-Schicht (Plan 02, 03) | Rohantworten der App werden nie unverarbeitet weitergegeben | Projizierte Felder, Zellwerte |
| Modell zu Tool-Parameter (Plan 03) | `level`, `table_id`, `values` und `cursor` stammen aus einer Modellantwort | Freitext-JSON, Cursor-Handle |
| Zellwerte zu Modellkontext (Plan 03) | Tabellenzellen und Auswahl-Labels enthalten fremden Text | Zeilen- und Spaltentexte |
| Tool zu Nextcloud-ACL (Plan 03) | Die Vorprüfung ist die bessere Fehlermeldung, nicht die Autorität | Berechtigungsfelder `isShared`, `onSharePermissions` |
| Registry zu MCP-Client (Plan 04) | `tools/list` ist die gecachte Zusage samt Annotationen und Schemata | Werkzeugnamen, Hints, Schemagrösse |
| Quellcode zu Destruktiv-Gate (Plan 04) | Einzige Instanz, die eine neue schreibende Route bemerkt | Quelltextzeilen |
| Konto A zu Konto B (Plan 05) | Zwei Identitäten auf derselben Instanz, gemessen über die Impersonation | Tabelleninhalte, Zeilenzahlen |
| Testgerüst zu Connector-Fähigkeit (Plan 05) | Setup-POSTs legen Tabelle und Spalten an, was der Connector absichtlich nicht kann | Gerüst-Requests, klar markiert |
| Testinstanz zu Entwicklungsrechner (Plan 05) | Tests laufen nur gegen lokale Wegwerf-Topologien | Erfundene Testzeichenketten |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-08-01 | Information Disclosure | `_probe` in `tests/integration/test_exapp_mail_reach.py` | mitigate | `HEAD_LIMIT = 120` (Z. 83), Körper nur gekappt zurückgegeben (Z. 198), zurückgegeben werden ausschliesslich Status, Content-Type, Shape, Location; kein Headerwert mit `APP_SECRET`. Ausgabe der Protokolltabelle nutzt denselben gekappten Wert (Z. 341). Regel wörtlich in `docs/spike-mail.md:47,94-97` | closed |
| T-08-02 | Denial of Service | OCS-Route `apps/mail/message/{id}` | mitigate | Genau ein Aufruf (`_walk`, Z. 249), Memo in `_row` (Z. 252-262) hält die Route bei höchstens einer Anfrage je Session, keine Schleife; `BruteForceProtection`-Begründung als Kommentar am Test (Z. 94-98), nicht in der Topologie | closed |
| T-08-03 | Spoofing | Credential-Bau im Spike | mitigate | `test_the_measuring_process_holds_no_nextcloud_app_password` löscht und prüft `NC_MCP_APP_PASSWORD` und `NC_MCP_STATIC_BEARER` (Z. 137-152); `grep -c BasicAuth` in der Datei ist 0; `test_a_wrong_app_secret_is_refused` weist ein `APP_SECRET` aus 64 Nullen ab (Z. 155-167) | closed |
| T-08-04 | Tampering | `ensure_mail_account` in `scripts/bootstrap_exapp.sh` | mitigate | Idempotent nach dem Muster von `ensure_user`: Prüfung per `mail:account:export` plus `grep` vor dem Anlegen (Z. 299-307); Kommandoausgabe in `output` gefangen und nur bei Fehlschlag auf stderr gezeigt (Z. 310-316) | closed |
| T-08-05 | Information Disclosure | GreenMail-Dienst (nur Eskalationsfall) | mitigate | Eskalation ist nicht eingetreten, deshalb existiert kein Dienst: `grep -ri greenmail` trifft ausschliesslich `docs/spike-mail.md`. Der dortige Vorlagenblock (Z. 125-135) hat keinen `ports:`-Eintrag und nur `networks: [nc-mcp-exapp-net]`; die Begründung steht in Z. 139-141. `compose.exapp.yml` unverändert | closed |
| T-08-06 | Spoofing, Information Disclosure | `_path_id` in `src/mcp_connector/nextcloud/clients/tables.py` | mitigate | `_path_id` erzwingt `isdigit()` und wirft sonst `ToolError` vor dem Request (Z. 210-218); aufgerufen an allen vier Id-tragenden Eingängen: `get_table` (Z. 126), `get_columns` (Z. 139), `get_rows_simple` (Z. 168), `create_row` (Z. 200). `get_tables` trägt keine Id. Negativbeweis ohne Anfrage: `tests/unit/test_tables_client.py:278` (`"7/../../tables"`). Restrisiko siehe Hinweis R-1 | closed |
| T-08-07 | Denial of Service | `get_rows_simple` | mitigate | `limit` ist Keyword ohne Default (Z. 149-155), Kappung `min(max(int(limit), 1), MAX_ROWS)` mit `MAX_ROWS = 200` (Z. 76, 169). Behauptung an der gebauten URL, nicht am Ergebnis: `tests/unit/test_tables_client.py:117` (`limit=25`) und `:132` (`limit=200` bei angefragten 5000) | closed |
| T-08-08 | Information Disclosure (SSRF) | `api_url`, `web_url`, `ocs.ocs_url` | mitigate | Alle URLs aus `creds.base_url`: `api_url` (Z. 89-93), `web_url` (Z. 96-98), `ocs.ocs_url` (`clients/ocs.py:58-62`). Keine URL entsteht aus einer Antwort. `follow_redirects=False` auf dem geteilten Client (`nextcloud/http.py:75`), im ExApp-Eingang (`entry_exapp.py:227`) und im Testclient (`tests/unit/test_tables_client.py:74`); 3xx wird als Fehler gemeldet (`clients/ocs.py:199-203`) | closed |
| T-08-09 | Tampering | `ocs_post` und alle Tables-GETs | mitigate | Kein `Origin` in `OCS_HEADERS` (`clients/ocs.py:41-44`), keiner in `TABLES_HEADERS` (`clients/tables.py:80-84`), keiner in `ocs_post` (`clients/ocs.py:103-108`); der geteilte Client setzt nur `User-Agent` (`http.py:77`). Behauptung der Abwesenheit auf dem Schreibpfad: `tests/unit/test_tables_client.py:188-201`. Hinweis: die Behauptung deckt den POST; die GETs sind durch die beiden Header-Konstanten gedeckt | closed |
| T-08-10 | Tampering | `create_row` | mitigate | Kein Retry auf irgendeiner Schicht: Kette `reg_tables.tables_create_row` (Z. 71) zu `tools.tables.create_row` (Z. 149) zu `clients.tables.create_row` (Z. 201) zu `ocs.ocs_post` , je genau ein `await`, keine Schleife. Repo-Grep ohne Treffer für `tenacity`, `backoff`, `for attempt`, `while True` in `src/mcp_connector`; keine Transport-Retries konfiguriert (`http.py:73-79`). Timeout-Satz im Docstring (`clients/tables.py:196-198`, `tools/tables.py:126-128`) | closed |
| T-08-11 | Elevation of Privilege | `clients/tables.py` als Ganzes | mitigate | Das Modul enthält ausschliesslich `get_tables`, `get_table`, `get_columns`, `get_rows_simple`, `create_row`; kein Update-, Delete-, Spalten-, Schema-, Transfer- und Share-Pfad. Festgefroren durch das Gate `tests/contract/test_no_destructive_calls.py:219` über alle Dateien unter `src` (`_source_files`, Z. 160) plus Gegenproben Z. 317, 340, 353 | closed |
| T-08-12 | Error Handling | `parse_ocs`, `parse_app_json`, `_status_error` | mitigate | 400 der App wird mit eigener Meldung durchgereicht (`clients/ocs.py:261-266`, Behauptung `tests/unit/test_tables_tools.py:797`: "Nextcloud says: Value is not a valid number"). Kein Stacktrace: `raise ... from None` (`clients/ocs.py:256`). Keine HTML-Loginseite als Erklärung eines 4xx ohne JSON-Körper (`clients/ocs.py:224-230`, Test `tests/unit/test_tables_client.py:227-239`). Siehe Warnung UF-2 zur Abweichung an dieser geteilten Datei | closed |
| T-08-13 | Elevation of Privilege | `_may_create` in `src/mcp_connector/tools/tables.py` | mitigate | Regel nach K5 in `_may_create` (Z. 401-420): erlaubt bei `isShared` falsch oder `create` oder `manage`. Angewandt vor dem POST (Z. 136-144) und in der Projektion als `can_create` (Z. 294). Zwei Unit-Tests in beide Richtungen: `tests/unit/test_tables_tools.py:705` (Eigentümer darf, obwohl das Share-Objekt nur `read` meldet) und `:737` (geteilte Tabelle ohne `create` wird vor dem POST abgelehnt) | closed |
| T-08-14 | Tampering (Prompt Injection) | Projektion der Zellwerte und Titel | mitigate | `marks.without_marks` über `_text` (Z. 423-429) und rekursiv über `_clean` (Z. 432-450); angewandt auf Zellwerte (`_row`, Z. 383), Titelzeile (Z. 341), Tabellentitel (Z. 290), Spaltentitel (Z. 305) und alle `_COLUMN_LIMITS` inklusive `selectionOptions`-Labels (Z. 311-317). Nach WR-03 auch für Listen und Objekte belegt: `tests/unit/test_tables_tools.py:405` und `:433`. `prepare_context` führt keinen Tabellenauszug: `grep tables src/mcp_connector/tools/context.py` ohne Treffer | closed |
| T-08-15 | Tampering | Titel-zu-Id-Abbildung | mitigate | `_by_column_id` (Z. 189-267) löst Titel nur gegen die Spaltenliste der Instanz auf, schreibt ausschliesslich numerische Spalten-Ids (Z. 233) und lehnt mehrdeutige Titel ab (Z. 236-245). Nach WR-04 zusätzlich Ablehnung eines Spaltenobjekts ohne echtes `int` als Id (Z. 227-232, `_COLUMN_ID_HINT` Z. 71-75). Tests: `tests/unit/test_tables_tools.py:586`, `:620`, `:643`, `:665`, `:685` | closed |
| T-08-16 | Denial of Service | `browse(level="rows")` | mitigate | Kappung im Tool `min(max(limit, 1), MAX_LIMIT)` (Z. 88) zusätzlich zur Kappung im Client (Z. 169), Default `DEFAULT_LIMIT = 25` (Z. 43, 82), `truncated` in der Antwort (Z. 368, 458). Tests: `tests/unit/test_tables_tools.py:299` (ohne Limit 25, nicht die Tabelle) und `:317` (Limit ausserhalb der Spanne wird gekappt) | closed |
| T-08-17 | Tampering | Cursor-Handle | mitigate | `paging.check_scope(state, "t", table, "table")` vor jedem Offset-Gebrauch (Z. 335), Offset erst danach (Z. 336). Test `tests/unit/test_tables_tools.py:365`. Verstärkung nach WR-02: eine Seite ohne Inhalt gibt kein Handle aus (Z. 364, Test `:466`) | closed |
| T-08-18 | Error Handling | `values`-Parsing | mitigate | `json.JSONDecodeError` wird mit `from None` in einen Satz plus Beispielobjekt übersetzt (`_parse_values`, Z. 165-172, `_VALUES_HINT` Z. 63-66); kein Traceback, keine Rohantwort. Weitere Formfehler ebenfalls als Satz (Z. 174-185). Test `tests/unit/test_tables_tools.py:539`, `:556`, `:570` | closed |
| T-08-19 | Information Disclosure | Fehlersätze der Ablehnungen | accept | Dokumentiert als AR-01; Vorprüfung läuft erst nach `get_table` und `get_columns` unter der Identität des Nutzers (`tools/tables.py:135,146`) | closed |
| T-08-20 | Tampering | Neue Tables-Schreibroute im Client | mitigate | Fünf `FORBIDDEN`-Nadeln `"/rows/"`, `"/columns/"`, `"/scheme"`, `"/transfer"`, `"/share"` (`tests/contract/test_no_destructive_calls.py:57-62`), nach WR-05 auf Pfadsegmente statt auf ein Anführungszeichen verankert. Gegenprobe je Nadel über `TABLES_ROUTES` (Z. 70-75) parametrisiert in Z. 316-337, Gegenrichtung Z. 340 (drei echte Routen bleiben erlaubt) und Z. 353 (die Leseausnahme deckt zwei exakte Literale in genau einer Datei, nie `DELETE`, `/transfer`, `/share`: `TABLES_READ_NEEDLES` Z. 100) | closed |
| T-08-21 | Repudiation | Annotationen von `tables_create_row` | mitigate | `CREATE_ONLY` mit `read_only_hint=False`, `destructive_hint=False`, `idempotent_hint=False`, `open_world_hint=False` (`src/mcp_connector/server/__init__.py:55-60`), gesetzt an `tables_create_row` (`server/reg_tables.py:50`). Behauptet über `tools/list`: `tests/contract/test_tool_surface.py:279-283` | closed |
| T-08-22 | Denial of Service | `tools/list`-Grösse | mitigate | Datierte Messzeile "2026-08-21, all 18 curated tools registered: 12801 bytes" plus Budgetrechnung (`scripts/check_tool_budget.py:22-23`), `BUDGET_BYTES = 15_000` (Z. 35) und zweite Behauptung `MAX_TOOL_BYTES = 1400` je Werkzeug (Z. 42, Prüfung Z. 68-73) | closed |
| T-08-23 | Tampering | Modulweiter veränderlicher Zustand | mitigate | `ALLOWED_MODULE_STATE` trägt genau zwei namentlich gelistete Einträge (`tests/contract/test_no_destructive_calls.py:145-148`); Gate über alle Quelldateien Z. 376-404, Anzahl explizit behauptet Z. 419 | closed |
| T-08-24 | Information Disclosure | Werkzeug-Beschreibungen und README-Zeilen | mitigate | Der Docstring von `tables_create_row` sagt es dem Modell direkt: "A timeout does not mean nothing was written. Read back with tables_browse(level=\"rows\") instead of calling this a second time." (`server/reg_tables.py:65-69`); gleicher Satz in `tools/tables.py:126-128` und `clients/tables.py:196-198`. READMEs EN/DE/FR nennen Tables als optionale App und sieben ignorierbare Werkzeuge (WR-07, Commit `6ddc4a8`) | closed |
| T-08-25 | Repudiation | Doku-Zahlen | accept | Dokumentiert als AR-02; der Doku-Wächter `tests/contract/test_tool_surface.py:557` erzwingt für jede Zahl entweder Aktualität oder den Zeiger auf den Contract-Test | closed |
| T-08-26 | Elevation of Privilege | Zugriff auf eine fremde Tabelle | mitigate | Zwei-Konten-Beweis in `tests/integration/test_permission_fidelity_exapp.py`: positiver Teil im selben Lauf (Z. 417-431), Leseverweigerung mit echter Id ohne Inhalt (Z. 430-455, Marker-Behauptung Z. 455), Schreibverweigerung mit Zeilenzahl vor und nach dem Versuch (Z. 456-482). Abschnittsmarkierung mit Bedrohungs-Id Z. 300 | closed |
| T-08-27 | Spoofing | Credential-Quelle im Fidelity-Test | mitigate | Beide Identitäten entstehen allein aus `MODE_APPAPI` mit `APP_SECRET` in einer gemeinsamen Fabrik `_appapi_clients` (Z. 308-327), genutzt von `alice_tables` (Z. 331) und `bob_tables` (Z. 338); bestehende Kontrollen der Datei unverändert (`test_alice_and_bob_are_two_different_accounts`, Z. 177-185) | closed |
| T-08-28 | Tampering | Setup-POSTs im Integrationstest | mitigate | `_scaffold` ist im Docstring ausdrücklich als Gerüst mit Verweis auf T-08-11 markiert und macht aus Status ab 400 ein `pytest.skip` statt eines Fehlschlags (Z. 344-357); dasselbe Muster in `tests/integration/test_tables_roundtrip.py:102-121`. Der Connector-Client hat für diese Routen keinen Code, gehalten vom Gate aus Plan 04 | closed |
| T-08-29 | Information Disclosure | Testinhalte | accept | Dokumentiert als AR-03; die geschriebenen Werte sind erfundene Zeichenketten (`TABLES_TITLE`, `TABLES_COLUMN` in `test_permission_fidelity_exapp.py:304-305`, `TABLE_TITLE` in `test_tables_roundtrip.py:48`) auf lokalen Wegwerf-Topologien | closed |
| T-08-30 | Denial of Service | Wiederholte Testläufe | mitigate | Idempotenz nach festem Titel in beiden Topologien: `test_tables_roundtrip.py:142-151` (Suche in `get_tables`, Anlegen nur beim Fehlen) und `test_permission_fidelity_exapp.py:371-377`; Absicht samt Bedrohungs-Id im Modul-Docstring `test_tables_roundtrip.py:15-16`. Auch die Bootstrap-Helfer sind idempotent (`scripts/bootstrap_exapp.sh:255,271`, `scripts/bootstrap_test_nc.sh:164`) | closed |
| T-08-SC | Tampering | Paketinstallation | accept | Dokumentiert als AR-04; faktisch geprüft: `git log --name-only` über die Phasen-8-Commits nennt weder `pyproject.toml` noch `uv.lock`. Keine neue Sprachabhängigkeit, kein `uv add` | closed |

*Status: open , closed*
*Disposition: mitigate (Implementierung nötig) , accept (dokumentiertes Risiko) , transfer (Dritte)*

Keine Bedrohung dieser Phase trägt die Disposition `transfer`, deshalb war keine Übertragungsdokumentation zu prüfen.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-08-19 | Ablehnungen nennen Titel und Ids der Spalten der angefragten Tabelle. Das ist genau der Inhalt, den der Nutzer ohnehin lesen darf, weil die Vorprüfung erst nach `get_table` und `get_columns` unter seiner eigenen Identität läuft (`src/mcp_connector/tools/tables.py:135,146`). Gegen fremde Tabellen greift vorher die Nextcloud-ACL, live belegt durch T-08-26 (Ablehnung ohne Inhalt) | Planner (Plan 08-03), bestätigt im Audit | 2026-08-21 |
| AR-02 | T-08-25 | Datierte Messwerte alter Läufe dürfen in `docs/` stehenbleiben, solange die Seite auf `tests/contract/test_tool_surface.py` als aktuelle Wahrheit zeigt. Das ist die bestehende Regel des Doku-Wächters (`tests/contract/test_tool_surface.py:557-567`) und wird hier nicht neu verhandelt | Planner (Plan 08-04), bestätigt im Audit | 2026-08-21 |
| AR-03 | T-08-29 | Die von den Integrationstests geschriebenen Inhalte sind erfundene Testzeichenketten mit Umlauten auf lokalen Wegwerf-Topologien; es entstehen keine echten personenbezogenen Daten. Ein Lauf gegen eine produktive Nextcloud ist nicht vorgesehen; ohne konfigurierte Testinstanz überspringen die Tests (`tests/integration/test_tables_roundtrip.py:86`) | Planner (Plan 08-05), bestätigt im Audit | 2026-08-21 |
| AR-04 | T-08-SC | Keine neuen Sprachpakete in dieser Phase, `pyproject.toml` und `uv.lock` unangetastet (im Audit per `git log --name-only` geprüft). Die verwendeten Nextcloud-Apps und das optionale Docker-Image sind in `08-RESEARCH.md` gegen ihre offiziellen Quellen verifiziert (tables 2.2.2, mail 5.11.1, greenmail/standalone 2.1.12); kein `[ASSUMED]`, kein `[SUS]`, also kein Legitimitäts-Checkpoint nötig | Planner (Pläne 08-01 bis 08-05), bestätigt im Audit | 2026-08-21 |

*Akzeptierte Risiken tauchen in späteren Prüfläufen nicht erneut auf.*

---

## Unregistered Flags und Restrisiken

Warnungen, keine Blocker. Sie halten die Phase nicht auf (`block_on: high`), gehören aber ins Protokoll.

| ID | Art | Befund | Bewertung |
|----|-----|--------|-----------|
| UF-1 | unregistered_flag (Prozess) | `08-02-SUMMARY.md`, `08-03-SUMMARY.md` und `08-04-SUMMARY.md` haben keinen Abschnitt `## Threat Flags`. Nur 08-01 und 08-05 melden ausdrücklich "keine neue Sicherheitsfläche" | Die neue Fläche dieser drei Pläne ist im Audit direkt am Code geprüft (T-08-06 bis T-08-25 alle closed), es fehlt also die Meldung und nicht die Minderung. Für kommende Phasen: Abschnitt in jeder Zusammenfassung erzwingen |
| UF-2 | unregistered_flag (Fläche) | Abweichung 2 in `08-05-SUMMARY.md` änderte die geteilte Produktionsdatei `src/mcp_connector/nextcloud/clients/ocs.py`: `_check_transport` erklärt jetzt ein 4xx ohne JSON-Körper über `_status_error` (Z. 224-230). Das ist ein zusätzlicher Fehlerpfad in einem Parser, den sieben Client-Familien teilen, während T-08-12 wörtlich "kein neuer Fehlerpfad" plante. Keiner der fünf Threat Models nennt diese Änderung | Die drei geschützten Eigenschaften von T-08-12 bleiben nachweislich erhalten: 4xx **mit** JSON-Körper geht unverändert durch die App-eigene Meldung (`tests/unit/test_tables_tools.py:797`), der 5xx-Zweig liegt weiter davor (Z. 217), kein Stacktrace und keine falsche Loginseiten-Diagnose (Test `tests/unit/test_tables_client.py:227-239`). Deckung laut Zusammenfassung: 2268 grüne Tests plus zwei Live-Topologien. Restrisiko gering, keine Massnahme nötig |
| R-1 | Restrisiko zu T-08-06 | `_path_id` prüft mit `str.isdigit()`, das auch für Superscripts und fremde Ziffernsysteme wahr ist ("²", "٧"). Befund IN-05 aus `08-REVIEW.md:247` ist bewusst zurückgestellt | Die deklarierte Minderung ist wörtlich `isdigit()` und damit erfüllt. Pfad-Metazeichen kommen nicht durch (`tests/unit/test_tables_client.py:278`), die Folge ist ein harmloses 404 mit einer irreführenden Meldung. Kein Sicherheitsbefund, Kandidat für eine geplante Änderung |
| R-2 | Hinweis zu T-08-05 | Der GreenMail-Dienst existiert nur als Vorlage in `docs/spike-mail.md`, weil die Eskalationsbedingung nicht eingetreten ist | Die Vorlage erfüllt die Minderung (kein `ports:`, nur `networks:`). Wird Stufe 2 in Phase 10 gebaut, ist T-08-05 dort erneut zu prüfen, insbesondere die Bindung an `127.0.0.1`, falls doch ein Port gebunden wird |
| R-3 | Hinweis zu T-08-09 | Die Behauptung der `Origin`-Abwesenheit deckt den Schreibpfad (`tests/unit/test_tables_client.py:188-201`); für die GETs gibt es keinen eigenen Test | Die GETs sind konstruktiv gedeckt: `TABLES_HEADERS` und `OCS_HEADERS` enthalten keinen `Origin`, der geteilte Client setzt nur `User-Agent`. Kein Gate erzwingt das für künftige Header-Änderungen, daher als Hinweis vermerkt |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-21 | 31 | 31 (27 mitigate verifiziert, 4 akzeptiert) | 0 | gsd-security-auditor |

Geprüfter Commit: `dcaf7eb` (nach Review-Fix `1e39e7a`). ASVS-Level 1, `block_on: high`.
Geprüfte Implementierungsdateien: `src/mcp_connector/tools/tables.py`,
`src/mcp_connector/nextcloud/clients/tables.py`, `src/mcp_connector/nextcloud/clients/ocs.py`,
`src/mcp_connector/nextcloud/http.py`, `src/mcp_connector/server/reg_tables.py`,
`src/mcp_connector/server/__init__.py`, `tests/integration/test_exapp_mail_reach.py`,
`tests/integration/test_tables_roundtrip.py`, `tests/integration/test_permission_fidelity_exapp.py`,
`tests/contract/test_no_destructive_calls.py`, `tests/contract/test_tool_surface.py`,
`tests/unit/test_tables_client.py`, `tests/unit/test_tables_tools.py`,
`scripts/bootstrap_exapp.sh`, `scripts/bootstrap_test_nc.sh`, `scripts/check_tool_budget.py`,
`scripts/acceptance_all_tools.py`, `docs/spike-mail.md`.
Keine Implementierungsdatei wurde in diesem Lauf verändert.

---

## Sign-Off

- [x] Alle Bedrohungen tragen eine Disposition (mitigate / accept / transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (AR-01 bis AR-04)
- [x] `threats_open: 0` bestätigt
- [x] `status: verified` in der Frontmatter gesetzt

**Approval:** verified 2026-08-21
