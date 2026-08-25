---
phase: 11-b-ndelung-budget-und-release-0-1-6
slug: buendelung-budget-und-release-0-1-8
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-25
updated: 2026-08-25
---

# Phase 11 , Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfprotokoll.
> Geprüfter Stand: HEAD `c449420`, also nach dem Review-Fix-Pass
> (`e0150af`, `5ab83e6`, `33cae32`, `5501b0a`) und nach dem Release-Tag `v0.1.8`.
> Grundhaltung dieser Prüfung: jede Minderung gilt als abwesend, bis eine Fundstelle im
> Implementierungsstand sie belegt. Doku und Absicht allein sind kein Beweis.
> Register aufgebaut aus den zehn `<threat_model>`-Blöcken von `11-01-PLAN.md` bis
> `11-10-PLAN.md` (`register_authored_at_plan_time: true`): 73 nummerierte Zeilen plus
> `T-11-SC` in jedem der zehn Pläne, zusammen 83 Registerzeilen in 74 Registereinträgen.
> Gate-Lauf des Audits: `uv run --no-sync pytest tests/contract
> tests/unit/test_{provider_map,ids,talk_client,chatgpt_fetch,tools_context,mail_tools,tables_tools,exapp_env_setup}.py`
> = 590 passed in 10,90 s; `uv run --no-sync python scripts/check_tool_budget.py`
> = 15657 Bytes bei 21 Werkzeugen gegen Budget 18000, grösstes Werkzeug `mail_browse`
> mit 1376 Bytes gegen 1400, Exit 0.
> Implementierungsdateien wurden von diesem Audit nicht angefasst.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Modelleingabe zu URL-Pfad | Konversationstoken, Nachrichten-Id und Tabellen-Id aus einer Modellantwort werden Pfadsegmente gegen spreed und tables | Pfadsegmente (`[a-z0-9]{4,30}` bzw. `[0-9]+`), Query-Parameter |
| Suchtreffer einer fremden App zu eigener Id | `resourceUrl` und `attributes` schreibt die fremde App; das Ergebnis ist eine Adresse, die dieser Server anschliessend liest | Provider-Id, Fragment, Attribute |
| Fremde Herkunft in `resourceUrl` | Eine `resourceUrl` kann eine vollständige URL mit fremdem Origin tragen | Schema, Host, Pfad, Fragment |
| Nachrichtentext und Zellwert zu Modellkontext | Beide sind von Dritten geschrieben und landen im `text`-Feld einer `fetch`-Antwort | Chattext, Zellwerte, Platzhalter, Kappungsmarker |
| Nachrichtenvorschau zu Standardbündel | `last_message` einer Konversation ist fremder Text und reist im Standardbündel mit | Vorschau, gekappt auf 200 Bytes ohne eigenen Marker |
| Mailinhalt zu Standardbündel | Ein Betreff wäre fremder Text von jemandem ohne jede Nextcloud-Berechtigung | Nur Zahlen: `account_id`, `email`, `inbox_unread` |
| Kontenzahl des Nutzers zu Wanduhr des Werkzeugs | N in 1+N bestimmt ein fremder Nutzer durch das Anlegen von Mailkonten | Kontenliste, Postfachlisten, `MAX_MAIL_ACCOUNTS` |
| Leseweg zu Zustandsänderung | Eine falsch gewählte Route könnte einen Lesemarker setzen oder eine Benachrichtigung quittieren | `unread`, `unread_mention`, Lesemarker |
| Werkzeugbeschreibung zu Modellverhalten | Die Beschreibung ist die einzige Warnung, die ein Modell vor fremdem Text im Ergebnis sieht, und zugleich Kontextkosten jeder Sitzung | Beschreibungstexte, Enums, Annotationen |
| Laufende Instanz zu Testlauf | Der Integrationslauf spricht mit einer echten Nextcloud, echten Mails und echten Konversationen | Echte Betreffs, Tokens, Tabellen-Ids, Zähler |
| Vier Versionsstellen zu Git-Tag | Weichen sie ab, installiert AppAPI einen Tag, der nicht existiert | `info.xml` version/image-tag, `pyproject.toml`, `uv.lock`, Tag |
| Lokales Archiv zu signiertem Artefakt | Ein lokal gebautes `tar.gz` ist nicht byte-identisch mit dem veröffentlichten | Asset-Bytes, SHA-512-Signatur |
| Store-Token zu Arbeitskopie | Der Token gehört dem Store-Konto und darf den Browser nicht verlassen | Bearer-Token der Store-API |

---

## Threat Register

Alle 74 Registereinträge CLOSED. Belege (Datei:Zeile bzw. Test) aus dem Audit-Lauf 2026-08-25:

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|-----------------------|--------|
| T-11-01 | Elevation of Privilege | View-Id als Tabellen-Id | mitigate | `_TABLES_NODE` liest den `nodeType` mit (`provider_map.py:94/221-232`), nur `node[0] == "table"` wird Id (`:147-152`); Tests `..._takes_its_id_from_the_fragment` und `..._view_hit_stays_a_url` (test_provider_map.py:222/229/248) | closed |
| T-11-02 | Spoofing | Geratener Token oder geratene Nachrichten-Id | mitigate | `_message_target` prüft Attribute, dann Fragment, sonst `None` (`provider_map.py:190-218`); Tests für fehlende Attribute und `messageId: "abc"` (test_provider_map.py:197/208) | closed |
| T-11-03 | Spoofing | Nicht konforme Ids aus einer Modellantwort | mitigate | `_TOKEN`/`_DIGITS.fullmatch` je Segment in `ids.py:45/51/127/139/145`; 17 Ablehnungsfälle (test_ids.py:114-162), inklusive `٤٢` und `²` | closed |
| T-11-04 | Tampering | SSRF über fremde Herkunft in `resourceUrl` | mitigate | `absolute_url` verwirft die Herkunft (`provider_map.py:97-109`); Tests 125 und `..._foreign_origin_in_a_tables_fragment_never_reaches_the_id` (test_provider_map.py:269) | closed |
| T-11-05 | Information Disclosure | Geratener Mail-Deep-Link liest fremde Mail | accept | Mail bleibt `kind=url` mit benanntem Grund im Modul-Docstring (`provider_map.py:36-40`); Test 258; siehe AR-11-1 | closed |
| T-11-06 | Tampering | `PROVIDER_KINDS` wächst zur App-Liste | mitigate | `test_the_provider_table_is_not_a_list_of_installed_apps` (test_provider_map.py:287) friert die Menge ein; Datei-und-Klasse-Kommentare an den vier verifizierten Provider-Ids (`provider_map.py:58-72`), Abweichung siehe UF-1 | closed |
| T-11-07 | Tampering | Nebenwirkung durch den neuen Leseweg | mitigate | Route gegen spreed 24.0.4 verifiziert und im Docstring belegt (`clients/talk.py:214-222`); Gegenprobe `..._carries_the_limit_and_none_of_the_read_parameters` (test_talk_client.py:606); Live-Messung in 11-06-MEASUREMENTS.md:54 | closed |
| T-11-08 | Spoofing | Nicht konformer Token oder Nachrichten-Id im Pfad | mitigate | `_path_token` und `_path_message_id` vor dem Request (`clients/talk.py:238-239/284-305`); 10 Parameterfälle mit `route.call_count == 0` (test_talk_client.py:567/587) | closed |
| T-11-09 | Denial of Service | Grosses `limit` zieht ein ganzes Fenster | mitigate | `min(max(int(limit), 1), MAX_MESSAGES)` (`clients/talk.py:244`, MAX_MESSAGES=50); Test `(999 -> "50", 0 -> "1")` (test_talk_client.py:633) | closed |
| T-11-10 | Denial of Service | Nachlese oder Loop über die Kontextroute | mitigate | Genau ein Request je Aufruf; `route.call_count == 1` (test_talk_client.py:648) | closed |
| T-11-11 | Information Disclosure | 304 als Weiterleitungsfehler oder Fehler als leere Liste | mitigate | Lokaler 304-Sonderfall vor `parse_ocs` (`clients/talk.py:246-248`); 403 bleibt ToolError (test_talk_client.py:662) | closed |
| T-11-12 | Elevation of Privilege | Zugriff auf fremde Konversation | transfer | Transferbeleg: `#[RequireParticipant]` in spreed, dokumentiert in 11-RESEARCH.md:149/369 und 11-02-SUMMARY.md:102; die eigene Hälfte des Transfers ist der Listen-Umweg in `chatgpt.py:616` (siehe T-11-14) | closed |
| T-11-13 | Spoofing | Nachbarnachricht als Zielnachricht | mitigate | `one_message` filtert auf `id` und `KEPT_TYPES` (`tools/talk.py:531-556`), Fehlen ist ToolError (`chatgpt.py:621-632`); Tests 1141/1198/1217 (test_chatgpt_fetch.py) | closed |
| T-11-14 | Elevation of Privilege | Token direkt an die Instanz gegeben | mitigate | Auflösung über die eigene Konversationsliste `talk_tools._room` (`chatgpt.py:616`), nie `GET /room/{token}`; Test `..._token_outside_the_conversation_list_never_reaches_the_context_route` (test_chatgpt_fetch.py:1239) | closed |
| T-11-15 | Spoofing | Gefälschter Kappungsmarker in Text oder Zelle | mitigate | `marks.without_marks` läuft vor jeder eigenen Kappung: Talk über `_resolve` (`tools/talk.py:589`), Tabelle über `as_text` (`tools/tables.py:521/537`, Reihenfolge begründet in `chatgpt.py:705-710`); Tests 1272 und 1469/1490 | closed |
| T-11-16 | Tampering | Unaufgelöste Nachrichtenparameter erreichen das Modell | mitigate | Text läuft über `talk_tools._message` und damit `_resolve` (`tools/talk.py:517`); Test `..._parameters_are_resolved_and_no_placeholder_reaches_the_model` (test_chatgpt_fetch.py:1164) | closed |
| T-11-17 | Information Disclosure | Leerer Erfolg bei fehlender Nachricht oder leerer Tabelle | mitigate | Beide Fälle sind ToolError mit nächstem Schritt (`chatgpt.py:621-632`, `:695-702`); Tests 1198/1258/1439/1453 | closed |
| T-11-18 | Tampering | SSRF über eine URL aus Zelle oder Nachrichtentext | mitigate | `url` kommt aus `talk_client.web_url`/`tables_client.web_url` (`chatgpt.py:663/733`); Test `..._url_inside_a_cell_is_text_and_is_never_requested` mit `foreign.call_count == 0` (test_chatgpt_fetch.py:1588-1602) | closed |
| T-11-19 | Denial of Service | Kontextflut über eine sehr grosse Tabelle | mitigate | `TABLE_ROWS = 20`, `MAX_TABLE_BYTES = 4 KiB` (`chatgpt.py:118/127/690-718`), kein Paging; Test `..._reads_the_table_once_and_the_rows_once` (test_chatgpt_fetch.py:1576) | closed |
| T-11-20 | Tampering | Verschachteltes Objekt in `metadata` | mitigate | Flache Projektion nur mit Strings (`chatgpt.py:642-654`, `:720-727`); Tests 1309/1527 validieren jeden Wert und `FetchResult` | closed |
| T-11-21 | Denial of Service | Requests gegen eine fehlende App | mitigate | `require_app` als erste Zeile beider Zweige (`chatgpt.py:615/688`); Tests 1328/1546 mit Routenzählung 0 | closed |
| T-11-22 | Tampering | Prompt Injection über die Talk-Vorschau im Bündel | mitigate | Digest läuft ausschliesslich über `talk_tools.browse` (`context.py:305-307`); Marker-Hygiene an der Bündelgrenze per Test 1287, Injektionstest 999; die Warnung "third parties" bleibt Vertrag (test_tool_surface.py:485) | closed |
| T-11-23 | Spoofing | Gefälschter Kappungsmarker in einer Vorschau | mitigate | Zweiter Schnitt auf `DIGEST_PREVIEW_BYTES` hängt keinen Marker an (`context.py:683-703`); Tests 1266 und 1287 (test_tools_context.py) | closed |
| T-11-24 | Information Disclosure | Auszüge wachsen als Nebeneffekt der Bucket-Entscheidung | mitigate | Eigene Konstante `EXCERPT_KINDS` mit `#:`-Begründung (`context.py:196-210`), `_excerpts` liest nur daraus (`:740`); Tests 947 und 962 belegen `fetch`-Zählung 0 für Talk und Tabellen | closed |
| T-11-25 | Denial of Service | Hängendes Talk-Bein blockiert das Bündel | mitigate | `asyncio.timeout(TALK_BUDGET)` je Bein, kein globales Timeout um `gather` (`context.py:248/305`); Test mit `TALK_BUDGET = 0.05` (test_tools_context.py:1060) | closed |
| T-11-26 | Tampering | Doppelfehler-Regel wird verwässert | mitigate | `isinstance`-Bedingung wörtlich auf `search_out`/`calendar_out` mit Kommentar (`context.py:265-266`); Tests 1106/1124/1783 | closed |
| T-11-27 | Information Disclosure | Leere Digest-Liste als "nichts Ungelesenes" | mitigate | Jeder Ausfall schreibt genau einen benannten `degraded`-Eintrag (`context.py:615/626/638`); Test 1241 trennt die zwei Bedeutungen von 1086/1106 | closed |
| T-11-28 | Spoofing | Zweiter Content-Reader in `context.py` | mitigate | Gate `test_this_module_reads_no_content_of_its_own` grün (test_tools_context.py:1815-1830); das Bein ruft `talk_tools.browse` mit dem ganzen `clients`-Objekt | closed |
| T-11-29 | Information Disclosure | Betreff oder Absender im Standardbündel | mitigate | Das Bein ruft nur `level="accounts"`/`"mailboxes"` (`context.py:352/365`); Test mit gesetztem Betreff, Absender und Anzeigename plus `mail.of("messages") == []` (test_tools_context.py:1616-1645); Anmerkung zum Quelltext-Gate siehe UF-2 | closed |
| T-11-30 | Denial of Service | Viele Mailkonten verlängern jeden Bündelaufruf | mitigate | `MAX_MAIL_ACCOUNTS = 3` mit `degraded`-Eintrag (`context.py:175/453-459`), inneres `gather` (`:361`), äussere Decke `MAIL_BUDGET` (`:351`); Tests 1409/1429/1458/1570 | closed |
| T-11-31 | Spoofing | `unread` des Navigationseintrags als Zähler | mitigate | Verbot samt Messung im Docstring (`context.py:35-37`, `:346-348`); Zähler ausschliesslich aus der Postfachliste (`:399-407`); Live-Beleg 11-06-MEASUREMENTS.md:50 | closed |
| T-11-32 | Tampering | Fehlende Inbox erscheint als `inbox_unread: 0` | mitigate | Kein `inbox_unread` ohne Postfach mit Rolle (`context.py:382/407`), benannter `degraded`-Eintrag (`:479`); Tests 1513/1541 | closed |
| T-11-33 | Tampering | Werkzeugbeschreibung verschweigt eine Quelle | mitigate | Contract-Test behauptet Talk und Mail in der Aufzählung und "third parties" (test_tool_surface.py:459-491) | closed |
| T-11-34 | Elevation of Privilege | Erstes Konto als "das gemeinte" gelesen | mitigate | Explizite `account_id` je Postfachaufruf (`context.py:366`); Test mit drei verschiedenen Werten (test_tools_context.py:1429) | closed |
| T-11-35 | Information Disclosure | Inbox hinter dem Umschlagschnitt, Antwort schweigt | mitigate | `limit=mail_tools.MAX_LIMIT` auf beiden Ebenen (`context.py:352/367`), eigene `degraded`-Sätze für beide Schnitte (`:444-476`, verschärft in `5ab83e6`); Tests 1597/1687/1724/1745 | closed |
| T-11-36 | Spoofing | Zweiter Content-Reader umgeht Marker-Hygiene | mitigate | Dasselbe Gate wie T-11-28, grün (test_tools_context.py:1815); das Mail-Bein ruft `mail_tools.browse` mit dem ganzen `clients`-Objekt | closed |
| T-11-37 | Tampering | Nebenwirkungsmessung über die geprüfte Route | mitigate | `unread`/`unread_mention` über `talk_browse(level="conversations")` vor und nach dem `fetch` (test_ctx_bundle.py:10-18/283/521/785); Regel im Docstring, Messzeile 11-06-MEASUREMENTS.md:54 | closed |
| T-11-38 | Information Disclosure | Echter Betreff landet unbemerkt im Bündel | mitigate | Sechs GreenMail-Betreffs dürfen im serialisierten Bündel nicht vorkommen (test_ctx_bundle.py:108-115/595) | closed |
| T-11-39 | Spoofing | `fetch`-Beweis mit geratener Id | mitigate | Jede Id stammt aus einem echten Suchtreffer, sonst SKIP mit wahrem Grund (test_ctx_bundle.py:20-24/727); Messzeile 11-06-MEASUREMENTS.md:55 | closed |
| T-11-40 | Denial of Service | Sequenzieller Regress der vier Beine | mitigate | Obergrenze `CALENDAR_BUDGET` mit begründeter Assertion (test_ctx_bundle.py:309-350); Messzeilen 11-06-MEASUREMENTS.md:45/47 | closed |
| T-11-41 | Repudiation | Kommentarzahl ohne Beleg | mitigate | Alle vier Budget-Kommentare zitieren Messzeilen und verweisen auf 11-06-MEASUREMENTS.md (`context.py:112-118/129-135/154-163/170-175`); die Datei existiert und trägt Datum, Aussage und Befehl je Zeile | closed |
| T-11-42 | Tampering | Testobjekte bleiben in der Instanz | mitigate | Der Lauf legt nichts an, und der Docstring sagt es ausdrücklich (test_ctx_bundle.py:26-31); der Endzustand wird gemessen statt angenommen (`test_the_measurement_protocol_of_this_run`, :775) | closed |
| T-11-43 | Denial of Service | Integrationslauf in der Default-Auswahl | mitigate | `pytestmark = [pytest.mark.integration, ...]` (test_ctx_bundle.py:75), `addopts = "-m 'not integration and not matrix' ..."` (pyproject.toml:44), Env-Skip in tests/conftest.py:66-86; Beleg 11-06-MEASUREMENTS.md:57 | closed |
| T-11-44 | Tampering | Kürzung entfernt eine Angabe ersatzlos | mitigate | Alle sieben Filtertypen bleiben lesbar: `FILTER_TYPES` und `_FILTER_HINT` (`tools/mail.py:120/137-140`) sowie die README-Tabelle (README.md:340-346) | closed |
| T-11-45 | Tampering | `Literal`-Enum wird zu freiem String | mitigate | `Literal["accounts", "mailboxes", "messages"]` steht in `server/reg_mail.py:53`; Contract-Test prüft die Enum-Listen wörtlich (test_tool_surface.py:394) | closed |
| T-11-46 | Repudiation | Gate ohne tragende Messung | mitigate | `BUDGET_BYTES = 18_000` = `ceil(15612 * 1,15 / 500) * 500` (scripts/check_tool_budget.py:38-41/83), sechs datierte Messzeilen ab :19; Audit-Gegenprobe 15657 Bytes, Exit 0 | closed |
| T-11-47 | Repudiation | Zahl erfunden, um TOOL-15 zu treffen | mitigate | Der ehrliche dritte Ausgang steht in der Datei: 17500 wurde nicht erreicht, es fehlen 395 Bytes, mit Rechnung (scripts/check_tool_budget.py:50-63) | closed |
| T-11-48 | Elevation of Privilege | Obergrenze je Werkzeug angehoben | mitigate | `MAX_TOOL_BYTES = 1400` unverändert, die Anhebung auf 1553 ausdrücklich abgelehnt (scripts/check_tool_budget.py:104-117); Audit-Gegenprobe: grösstes Werkzeug 1376 Bytes | closed |
| T-11-49 | Spoofing | Falsche Annotation lässt Schreiben als Lesen erscheinen | mitigate | `CREATE_TOOLS` eingefroren (test_tool_surface.py:68), `test_every_tool_carries_honest_annotations` grün (:661-690) | closed |
| T-11-50 | Tampering | Werkzeug registriert, aber nie eingefroren | mitigate | Neuer Contract-Test hält die vom Gate gezählte Zahl gegen `len(EXPECTED_TOOLS)` (test_tool_surface.py:563-566) | closed |
| T-11-51 | Tampering | Registriertes Werkzeug fehlt in der Skriptliste | mitigate | Erwartete Menge kommt aus `client.list_tools()` (scripts/acceptance_all_tools.py:139-144), keine literale Liste mehr; leere Antwort ist ein FAIL | closed |
| T-11-52 | Repudiation | SKIP behauptet "keine Daten" nach einem Fehler | mitigate | Die SKIP-Zweige prüfen den Rückgabewert von `call`; ein leerer Wert erzeugt keine SKIP-Zeile (scripts/acceptance_all_tools.py:429-470, IN-04 im Docstring benannt) | closed |
| T-11-53 | Spoofing | Abnahme ruft `fetch` mit geratener Id | mitigate | Jede Id stammt aus einem Lesevorgang desselben Laufs (`_mail_message_id`, `_table_id` und die Suchkette, scripts/acceptance_all_tools.py:410-470) | closed |
| T-11-54 | Tampering | `truncated` auf Eintragsebene als Seitenkappung gelesen | mitigate | Umbenennung auf `preview_truncated` (`tools/mail.py:502-509`, `server/reg_mail.py:32/80`); Test des gemeinsamen Falls (test_mail_tools.py:541-547) | closed |
| T-11-55 | Repudiation | Zahl im Docstring widerspricht dem Gate | mitigate | "four variables" kommt in `src/` und `scripts/` nicht mehr vor (einziger Repo-Treffer ist ein unbeteiligter Kommentar in tests/integration/test_permission_parity_share.py:168) | closed |
| T-11-56 | Information Disclosure | Übersetzungen versprechen etwas anderes | mitigate | Alle drei READMEs auf einem Stand: acht Id-Präfixe (README.de.md:423-425, README.fr.md:433-435), 21 Werkzeuge (README.md:19, README.de.md:21), null Em-Dashes in allen drei | closed |
| T-11-57 | Tampering | Eine Versionsstelle bleibt auf 0.1.7 | mitigate | `info.xml:171` und `:245`, `pyproject.toml:3`, `uv.lock:472` alle auf 0.1.8, dazu die drei README-Statuszeilen (`33cae32`); Manifest-Gate test_exapp_env_setup.py:173-179 und Tag-Gate release.yml:45-56 | closed |
| T-11-58 | Repudiation | Umbenennung fehlt im Changelog | mitigate | `preview_truncated` unter `### Changed` mit benannter Antwortformat-Änderung (CHANGELOG.md:66-75) | closed |
| T-11-59 | Information Disclosure | Verbotenes Wort erreicht ein öffentliches Artefakt | mitigate | Vokabular-Gate über den Manifest-Text, case-insensitiv (test_exapp_env_setup.py:1686/1788/1861-1878), im Audit grün; CHANGELOG.md, README.md, README.de.md, README.fr.md und `info.xml` tragen das Wort nicht. Reichweite des Gates siehe UF-3 | closed |
| T-11-60 | Spoofing | Store-Beschreibung verspricht mehr als die Fassung liefert | mitigate | Die neue Aussage stammt aus 11-04/11-05 und ist wahr ("Mail arrives as counts only", `info.xml:58/99/142`); die CR-01-Ketten-Formulierung steht unverändert in allen drei Sprachen (`info.xml:68/109/152`) | closed |
| T-11-61 | Tampering | Lokales Archiv für das signierte Artefakt gehalten | mitigate | Der Probelauf ist ausdrücklich als Strukturprüfung markiert, mit dem Beleg 31909 gegen 32168 Bytes (docs/store-submission.md:124) | closed |
| T-11-62 | Denial of Service | Tag ohne Owner-Freigabe (Plan 11-09) | mitigate | Plan 11-09 erzeugte keinen Tag: `git tag --list v0.1.8` leer, protokolliert in 11-09-SUMMARY.md:94-95/307/332; der Tag zeigt auf `bbe9753` und entstand erst im Lauf von 11-10 | closed |
| T-11-63 | Repudiation | Proof-Zeile vor ihrem Ereignis geschrieben | mitigate | 11-09 schrieb genau zwei Zeilen (docs/store-submission.md:123-124, 22:36Z und 22:39Z); die Zeilen 125-131 kamen erst mit den 11-10-Commits `dd9d137` und `08e960e` | closed |
| T-11-64 | Tampering | Spendenlink beim Manifest-Edit verändert | mitigate | `https://www.paypal.com/paypalme/KhaledCherifDev` unverändert (`info.xml:214`) | closed |
| T-11-65 | Denial of Service | Tag ohne Owner-Freigabe (Plan 11-10) | mitigate | Blockierender Checkpoint, Antwort des Owners wörtlich festgehalten: "freigegeben", ausdrücklich inklusive `git push origin main` (11-10-SUMMARY.md:75-82) | closed |
| T-11-66 | Tampering | Tag umgeschrieben oder Asset gelöscht | mitigate | Nachweis: alle neun Image-Tags 0.1.0 bis 0.1.8 existieren, keiner wurde umgeschrieben oder entfernt (docs/store-submission.md:131); das Release-Asset existiert weiter (:129) | closed |
| T-11-67 | Spoofing | Signatur gehört zu einem anderen Artefakt | mitigate | Signiert wurde ausschliesslich das heruntergeladene Asset: 45546 Bytes gegen 45710 lokal, `2769c587…` gegen `15fc8719…`, Gegenprobe `Verified OK` (docs/store-submission.md:126) | closed |
| T-11-68 | Information Disclosure | Store-Token in Datei, Zusammenfassung oder Env | mitigate | POST lief im Seitenkontext der Store-Session (docs/store-submission.md:127); im Repo steht nur der Platzhalter `$NC_STORE_TOKEN` samt der Aussage, dass der Token bewusst nicht in dieser Arbeitskopie liegt (:234/244-246) | closed |
| T-11-69 | Information Disclosure | Signatur wird aufgeschrieben statt neu berechnet | mitigate | Keine Signatur im Repo: im Runbook steht `<base64 signature>` als Platzhalter (docs/store-submission.md:237), und die Proof-Zeile nennt nur Bytegrösse und SHA-256-Präfixe | closed |
| T-11-70 | Denial of Service | Image ohne `arm64` | mitigate | Nachweis 3 belegt einen echten OCI-Index mit `linux/amd64` und `linux/arm64` (docs/store-submission.md:130) | closed |
| T-11-71 | Repudiation | Proof-Zeile behauptet einen Befehl, der nicht lief | mitigate | Neun 0.1.8-Zeilen, jede mit Datum und Zeit in Z und dem Befehl in der letzten Spalte (docs/store-submission.md:123-131) | closed |
| T-11-72 | Tampering | Store-Cache verleitet zu einem weiteren Release | mitigate | Die verzögerte Sichtbarkeit ist als Beobachtung mit Zeitstempel notiert, nicht als Fehler (docs/store-submission.md:128, 11-10-SUMMARY.md:43/118-121) | closed |
| T-11-73 | Elevation of Privilege | Meilenstein-Tag in `v*`-Form löst ein Release aus | mitigate | Der Tag heisst genau `v0.1.8`; `release.yml:45-56` vergleicht `${GITHUB_REF_NAME#v}` mit `info.xml <version>` und bricht bei Abweichung ab | closed |
| T-11-SC (10x) | Tampering | Paketinstallation | mitigate | Über die ganze Phase (`4cb8a38~1..HEAD`) ändern sich an `pyproject.toml` und `uv.lock` genau zwei Zeilen: die eigene `version` von 0.1.7 auf 0.1.8, beide im Release-Commit `8392680`. Keine neue Abhängigkeit, kein `uv add`, kein `pip install`, kein `npm install`. Abweichung zur Wortwahl von 11-09 siehe UF-4 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-11-1 | T-11-05 | Ein Mail-Suchtreffer bleibt bewusst `kind=url`: der Deep-Link trägt Postfach und Thread, nicht die `databaseId`, und eine geratene Id würde nicht mit einem Fehler antworten, sondern fremde Mail lesen. Auflösung ist ungemessen und ausdrücklich Future Requirement (`provider_map.py:36-40`, Test test_provider_map.py:258) | Audit-Lauf (Plan-Disposition 11-01) | 2026-08-25 |
| AR-11-2 | UF-3 (Review IN-07) | Die Vokabular-Regel ist repo-weit formuliert, aber nur über den Manifest-Text erzwungen; `docs/store-submission.md` nutzt das englische Wort in zehn Zeilen, davon zwei neu in 0.1.8. Das signierte Store-Archiv (`info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`) ist frei davon | Review-Fix-Pass (11-REVIEW.md:50, IN-07 deferred) | 2026-08-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags (WARNING, geprüft, kein Blocker)

1. **UF-1, Kommentarabdeckung von `PROVIDER_KINDS`.** T-11-06 verlangt "jeder Eintrag trägt
   den Kommentar mit Datei und Klasse der verifizierten Provider-Id". Vier der sieben
   Einträge tragen ihn (`search-deck-card-board`, `talk-message`, `talk-message-current`,
   `tables-search-tables`); `files` und `notes` stammen aus Phase 1 und tragen ihn nicht.
   Der eingefrorene Halter (test_provider_map.py:287) deckt die ganze Menge ab, deshalb
   CLOSED mit benannter Abweichung.
2. **UF-2, Quelltext-Gate zu T-11-29.** Der dauerhafte Halter ist der Testfall
   (test_tools_context.py:1616-1645, `mail.of("messages") == []`). Das im Plan zusätzlich
   genannte Quelltext-Gate war ein einmaliger Prüfschritt der Ausführung
   (11-05-SUMMARY.md:257) und existiert nicht als Regressionstest. Die Sicherheitsaussage
   selbst ist gehalten, die zweite Absicherung nicht. Kandidat für einen `read_text`-Gate
   neben `test_this_module_reads_no_content_of_its_own`.
3. **UF-3, Reichweite des Vokabular-Gates.** Siehe AR-11-2. Das Gate prüft ausschliesslich
   den Manifest-Text, die Regel gilt laut Kommentar für jedes öffentliche Artefakt dieses
   Repos, und das Repo ist öffentlich. Kein Blocker, weil das Artefakt, das die Phase
   veröffentlicht hat, sauber ist.
4. **UF-4, `uv.lock` in T-11-SC.** Der Threat-Text von 11-09 sagt "uv.lock bleibt
   unangetastet"; tatsächlich hat `8392680` dort die eigene `version`-Zeile mitgezogen
   (0.1.7 zu 0.1.8), was `uv lock` ohnehin regeneriert. Die geschützte Eigenschaft, keine
   neue Sprachabhängigkeit, ist unverletzt.
5. **Neue Fläche aus dem Review-Fix-Pass**, nicht im Plan-Register, geprüft und mit den
   bestehenden Threats vereinbar: das Whitespace-Filtergate in `tools/mail.py` (`e0150af`,
   verschärft T-10-19) und die Duplikat-Ablehnung in `tools/tables.py` (`5501b0a`, ein
   neuer Ablehnungsweg in `tables_create_row`, kein neuer Lese- oder Schreibpfad). Beide
   bringen eigene Tests mit und sind Härtungen, keine Erweiterungen der Angriffsfläche.
6. **Prozesshinweis:** fünf von zehn SUMMARYs tragen keinen `## Threat Flags`-Abschnitt
   (11-02, 11-03, 11-06, 11-09, 11-10). Die fünf Pläne wurden einzeln gegen das Register
   geprüft, es wurde keine ungemappte Fläche gefunden.
7. **Deferred Review-Findings mit Sicherheitsbezug, informativ:** IN-04 (`ids.parse`
   überspringt für die `url`-Art den Leersegment-Check) und IN-06 (`chatgpt.py` ruft
   `talk_tools._room` über die Modulgrenze). Beide sind in 11-REVIEW.md als Info geführt
   und berühren keine Registerzeile dieser Phase.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-25 | 74 (73 nummeriert + T-11-SC 10x) | 74 | 0 | gsd-security-auditor (opus) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-25
