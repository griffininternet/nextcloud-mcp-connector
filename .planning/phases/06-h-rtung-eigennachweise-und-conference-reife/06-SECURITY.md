---
phase: 6
slug: h-rtung-eigennachweise-und-conference-reife
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-20
---

# Phase 6: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Restrisiken, Audit-Trail.
> Register-Quelle: die elf threat_model-Bloecke der Plaene 06-01 bis 06-11 (State B, zur
> Planzeit erstellt), 74 deduplizierte Positionen. Verifiziert am 2026-08-20 durch
> gsd-security-auditor (opus) gegen den Quelltext bei `f281458` (Arbeitsbaum sauber), gegen
> einen eigenen Testlauf (9 Unit-Dateien, 623 Tests, alle gruen) und gegen die Messdateien
> 06-07 bis 06-10.
>
> Dieses Audit sucht keine neuen Schwachstellen. Es prueft fuer jede der 74 Positionen, ob
> die in ihrer Zeile deklarierte Gegenmassnahme im ausgelieferten Stand wirklich existiert,
> Datei und Zeile beziehungsweise Testname als Beleg. Die drei Warnings des Code-Reviews
> (WR-01 bis WR-03, Commits `a47bb57` und `bd75cd8`) sind Teil dieser Pruefung und einzeln
> nachgewiesen.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| MCP-Client zu `/authorize` | Der einzige Ort im Projekt, an dem eine Anfrage das Ziel eines eigenen Requests waehlt: die `client_id` ist die Adresse des Dokuments | Kennung als URL, Redirect-Ziel, PKCE |
| ExApp-Prozess zu fremder HTTPS-Domaene | Erster ausgehender Request dieses Projekts in eine fremde Vertrauensdomaene; der Antwortrumpf ist Angreifereingabe | GET auf fremdes JSON, Antwortrumpf, Cache-Header |
| DNS-Resolver zu Prozess | Die Zuordnung Name zu Adresse ist von aussen beeinflussbar und kann sich zwischen Pruefung und Verbindung aendern | Adressliteral, Name fuer SNI und `Host` |
| Fremdes Dokument zu Store und Consent-Seite | Aus fremdem JSON entsteht eine Client-Zeile, an der Autorisierungen und App-Passwoerter haengen, und ein Text auf der Zustimmungsseite | `client_name`, `client_id`, `redirect_uris` |
| Store-Zeile zu Nextcloud-App-Passwort | `ON DELETE CASCADE` verbindet die Client-Zeile mit dem Chiffrat jedes App-Passworts darunter | Chiffretexte, Token-Hashes |
| Loopback-Interface zu Nutzerin | Auf einem Desktop kann jedes Programm einen Port belegen und eine fremde Kennung nennen | Authorization Code auf einem Port, den niemand zuordnen kann |
| Admin-Umgebung zu Prozess | Vier Schalter kommen aus der Umgebung, die AppAPI aus dem Manifest fuellt; eine undeklarierte Variable wird still verworfen | Policy-Werte |
| ExApp zu jedem MCP-Client (unauthentifiziert) | Das AS-Metadatendokument ist oeffentlich lesbar und steuert, welchen Registrierungsweg ein Client waehlt | Feld `client_id_metadata_document_supported` |
| Messlauf zu Owner-Instanzen und Owner-Konfiguration | Auf demselben Docker-Host laufen zwei taeglich genutzte Instanzen; `~/.cursor/mcp.json` und drei Schalter gehoeren dem Owner | Volumes, Client-Konfiguration, Schalterzustand |
| Messdatei und Conference-Material zu oeffentlichem Repository | `.planning/` und `docs/` sind oeffentlich (Phase-01-Entscheidung), also ist jede geschriebene Zeile veroeffentlicht | Logauszuege, Pfade, Zeitstempel, Behauptungen |
| Browser zur Absageseite E5 | Eine gerenderte Seite an einen Browser, der einer `/authorize`-Anfrage eines fremden Clients gefolgt ist | Fehlertext ohne Protokollwert |

---

## Threat Register

74 deduplizierte Positionen: 68 `mitigate`, 5 `accept`, 1 `transfer`. **74 closed, 0 open.**
Jede Zeile wurde einzeln gegen den Quelltext, gegen einen eigenen Testlauf oder gegen die
Messdatei geprueft, nicht gegen die SUMMARYs.

`T-06-SC` steht in allen elf Plaenen mit derselben Aussage und ist zu einer Zeile
zusammengefasst. Die Plaene 06-09, 06-10 und 06-11 haben die Nummern `T-06-60` bis `T-06-64`
doppelt vergeben; die Zeilen aus Plan 06-11 tragen hier den Zusatz `/11`. Siehe
"Register-Hygiene" weiter unten.

### Plan 06-01: SSRF-Grenze und Limits

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-01 | Information Disclosure | `cimd.target_allowed` | mitigate | Konjunktion `not is_global` plus sechs Negativflags (`cimd.py:186-198`), v4-mapped vorher entpackt (`:186-188`); Negativkatalog `test_oauth_cimd.py:21` (NAT64, CGNAT, Multicast, v4-mapped, private, loopback, link local) | closed |
| T-06-02 | Information Disclosure | `cimd.resolve_addresses` | mitigate | Eine durchgefallene Adresse verwirft den ganzen Namen (`cimd.py:298-302`, `return None` statt Auswahl); Tests `test_oauth_cimd.py:237` und `:685` (gemischte Aufloesung, auch am Transport) | closed |
| T-06-03 | Information Disclosure | `cimd.is_cimd_client_id` | mitigate | https, Pfad Pflicht, kein Fragment/Userinfo, keine Dot-Segmente (`cimd.py:143-162`), aufgerufen als erster Schritt vor jeder Aufloesung (`cimd.py:428`); Tests `:167`, `:446`, `:639` (Absage kostet kein Paket). Restluecke IN-01 siehe AR-06-05 | closed |
| T-06-04 | Denial of Service | `responses.bounded_response` | mitigate | Zaehler mit Abbruch im Chunk-Loop (`responses.py:122-134`), `MAX_DOCUMENT_BYTES = 5120` (`cimd.py:70`), kein zweiter Zaehler in `cimd.py`; Tests `test_exapp_responses.py:208`, `test_oauth_cimd.py:408`, `:826` | closed |
| T-06-05 | Information Disclosure | Logging in `cimd.py` | mitigate | Alle acht Logzeilen nennen `type(exc).__name__` oder eine feste Art, nie einen Wert der Anfrage (`cimd.py:286,289,296,301,363,367,372,375,485-501`); Tests `test_oauth_cimd.py:300`, `test_exapp_responses.py:239` | closed |
| T-06-06 | Tampering | Konstanten als Env-Schalter | accept | 5120 Bytes, 5,0 s, 300/3600 s sind Modulkonstanten ohne Schalter (`cimd.py:70,75,84,85`); eigener Grep bestaetigt: kein `environ`/`getenv` in der Datei; Test `test_oauth_cimd.py:819`. Restrisiko AR-06-01 | closed |

### Plan 06-02: Der gepinnte Abruf

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-07 | Information Disclosure | `cimd._fetch_pinned` (TOCTOU) | mitigate | Request auf das gepruefte IP-Literal (`cimd.py:342-343`), `sni_hostname` auf dem Originalnamen (`:356`), `Host` auf dem Original-netloc (`:355`), genau eine Aufloesung je Aufruf (`:439`); Tests `test_oauth_cimd.py:328` und `:553` (Zwei-Antworten-Resolver, Aufrufzaehler) | closed |
| T-06-08 | Information Disclosure | Redirect-Folgen | mitigate | `follow_redirects=False` (`cimd.py:347`), jedes `!= 200` ist `_Refused` (`:366-368`); Test `a_redirect_is_a_refusal_and_its_target_is_never_asked` (`test_oauth_cimd.py:377`) | closed |
| T-06-09 | Denial of Service | Groesse und Zeit | mitigate | `bounded_response` mit 5120 (`cimd.py:369`), `Timeout(5.0, connect=5.0)` (`:346`), `Limits(max_connections=1, max_keepalive_connections=0)` (`:348`); Tests `test_oauth_cimd.py:31` und `:35` | closed |
| T-06-10 | Denial of Service | Fetch-Flooding mit unbekannten URL-`client_id` | transfer | Empfaenger der Uebergabe existiert und ist verdrahtet: `Throttled(..., CLASS_AUTHORIZE_START, count_all=True, limit=FLOW_LIMIT)` auf der `/authorize`-Route (`consent.py:212-219`, `throttle.py:124`); Uebergabe dokumentiert an der Quelle (`cimd.py:418-422`) und in 06-02-SUMMARY:108-109. Kein Negativ-Cache (Draft MUST NOT), Tests `test_oauth_cimd.py:585`, `:779`. Offene Anschlussfrage siehe "Beobachtungen" | closed |
| T-06-11 | Spoofing | Dokument mit fremder `client_id` | mitigate | Zeichengenauer Vergleich ohne Normalisierung (`cimd.py:493`); Tests `test_oauth_cimd.py:40`, `:540` | closed |
| T-06-12 | Elevation of Privilege | Shared-Secret-Auth im Dokument | mitigate | `_FORBIDDEN_AUTH` mit allen drei Verfahren (`cimd.py:95`), geprueft in `validate_document` (`:496`); drei Zeilen des Negativkatalogs (`test_oauth_cimd.py:44`) | closed |
| T-06-13 | Information Disclosure | `logo_uri` als Tracking-Kanal | mitigate | Eigener Grep ueber `src/`: `logo_uri` kommt ausschliesslich in zwei Kommentaren vor (`cimd.py:469`, `provider.py:1640`), in keiner Zuweisung und keinem Render-Pfad; `<img` existiert nirgends in `src/` | closed |
| T-06-14 | Spoofing | Geteilter Verbindungspool mit dem Credential-Pfad | mitigate | Eigener `AsyncClient` pro Aufruf (`cimd.py:345`), `NoCookieJar()` (`:350`), ein `USER_AGENT` (`:349`); eigener Grep: kein `shared_client` in der Datei; Test `test_oauth_cimd.py:46` | closed |

### Plan 06-03: Schalterkopplung und Loopback-Portregel

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-15 | Elevation of Privilege | Umgehung eines abgeschalteten DCR ueber CIMD | mitigate | `cimd_enabled=_switch(env, ENV_CIMD, default=True) and dcr` (`registry.py:171`); Test "DCR aus, CIMD explizit an" (`test_oauth_registry.py:123`), live bestaetigt (06-09-MEASUREMENTS.md:504-545) | closed |
| T-06-16 | Tampering | Open Redirect ueber die gelockerte Portregel | mitigate | Nur der Port ist frei, Schema, Pfad und Query exakt, Host case-insensitiv (`registry.py:255-259`); `redirect_uri_allowed` laeuft danach auf der angefragten Adresse (`consent.py:283-286`); Test `test_oauth_consent.py:328` | closed |
| T-06-17 | Spoofing | Port-Squatting auf Loopback nach der Lockerung | accept | Alles ausser dem Port bleibt exakt (`registry.py:255-259`), ohne PKCE-Verifier kein einloesbarer Code; sichtbar gemacht auf der Zustimmungsseite (`strings.py:268-273`, `ui/consent.py:245-247`). Restrisiko AR-06-02 | closed |
| T-06-18 | Information Disclosure | Fehlerbild verraet, welche Pruefung fiel | mitigate | Alle vier Redirect-Absagen in `_screen` liefern `E5` und keinen neuen Code (`consent.py:258,271,281,285`); bestehende Gates `FORBIDDEN_ON_ERROR_PAGES`/`FORBIDDEN_IN_ERROR_TEXT` laufen unveraendert ueber E5 | closed |
| T-06-19 | Tampering | Dauerhafte Eintragung einer angefragten Loopback-Adresse | mitigate | `loopback_match` gibt einen registrierten Kandidaten zurueck und schreibt nichts (`registry.py:248-260`); eigener Grep: in `consent.py` gibt es nur Lesezugriffe auf `client.redirect_uris` (`:270`, `:453`), keine Zuweisung; die Weitergabe ist eine Kopie fuer eine Anfrage (`provider.py:534-554`); Tests `test_oauth_consent.py:299`, `test_oauth_registry.py:321` | closed |
| T-06-20 | Tampering | Zweite Lockerung im Token-Pfad | mitigate | Eigener Grep ueber `src/`: genau eine `loopback_match`-Aufrufstelle im Produktionscode (`consent.py:271`), keine im Token-Pfad; der Token-Endpunkt vergleicht gegen den gespeicherten Auth-Code-Wert (Kommentar `consent.py:274-279`) | closed |

### Plan 06-04: Advertising und Manifest

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-21 | Denial of Service | Advertising ohne funktionierenden Pfad | mitigate | `client_id_metadata_document_supported = cimd_enabled or None` (`metadata.py:223`) plus `exclude_none` (`:225`); Tests `test_oauth_metadata.py:291-292` (`not in body` und `not in response.text`), `:354`, `test_exapp_entry.py:1201-1246` | closed |
| T-06-22 | Elevation of Privilege | Stiller Default durch fehlende Manifest-Deklaration | mitigate | Fuenfter `<variable>`-Eintrag `NC_MCP_OAUTH_CIMD` (`appinfo/info.xml:365-368`); Manifest-Gate `test_exapp_env_setup.py:1935-1965` schlaegt fehl, wenn die Deklaration fehlt | closed |
| T-06-23 | Information Disclosure | Metadatendokument leckt Konfiguration | accept | Fester Feldsatz, nur oeffentliche URLs, Scopes und Methodenlisten (`metadata.py:176-231`); Mengengleichheit auf die Feldnamen `test_oauth_metadata.py:76`. Restrisiko AR-06-03 | closed |
| T-06-24 | Tampering | Zweite Policy-Lesung im Prozess | mitigate | Genau ein `client_policy(env)` in der Anwendung (`entry_exapp.py:90`), derselbe Wert speist Provider (`:92`) und Advertising (`:170`); zweite Fundstelle ist nur der Default-Zweig des Providers (`provider.py:254`); Test `test_the_two_switches_are_read_from_one_policy_per_application` (`test_exapp_entry.py:1229-1248`) | closed |
| T-06-25 | Denial of Service | Leeres `<default>` im Manifest bricht den Store-Upload | mitigate | Eigener Grep: kein `<default></default>` und kein `<default/>` in `appinfo/info.xml`; das bestehende Variablen-Gate laeuft gruen (`test_exapp_env_setup.py`, eigener Lauf) | closed |

### Plan 06-05: Der Dokumentzweig im einen Pruefpunkt

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-26 | Elevation of Privilege | Umgehung des abgeschalteten DCR ueber CIMD | mitigate | `if not self._policy.cimd_enabled: return None` als erste Anweisung von `_resolve_cimd` (`provider.py:463-464`), fail-closed an `dcr` gekoppelt (`registry.py:171`); Tests `test_oauth_provider.py:540`, `:558`, `:823` (auch unter `may_fetch=False`), je ohne Paket | closed |
| T-06-27 | Elevation of Privilege | Umgehung der Allowlist ueber CIMD | mitigate | `policy.allows` im gemeinsamen Rest von `get_client` (`provider.py:371-373`) plus WR-02-Gate vor jedem Paket (`:472-478`); Tests `:577`, `:600`, `:622` und `:607` | closed |
| T-06-28 | Information Disclosure | SSRF als Nebenwirkung eines unbekannten `client_id` | mitigate | Schalter vor jedem Netzverkehr (`provider.py:463`), Zielpruefung vollstaendig in `cimd.py`; Test `:541` ("a switched off feature that still makes outbound requests is an SSRF tool"), live 0 Sockets zu Port 443 (06-09-MEASUREMENTS.md:533-537) | closed |
| T-06-29 | Tampering | Open Redirect ueber `redirect_uris` aus fremdem Dokument | mitigate | `registrable = [uri for uri in ... if redirect_uri_allowed(str(uri))]` (`provider.py:499`), leere Menge schreibt keine Zeile (`:500-504`); Tests `:637`, `:655` | closed |
| T-06-30 | Spoofing | Vertraulicher CIMD-Client mit geteiltem Secret | mitigate | `secret_hash=None` in jedem CIMD-Schreibpfad (`provider.py:518`), `validate_document` lehnt Shared-Secret-Verfahren vorher ab (`cimd.py:496`); Test `:669` | closed |
| T-06-31 | Denial of Service | TTL-Aufraeumen loescht CIMD-Clients samt Verbindungen | mitigate | `row.cimd_fetched_at is None and _has_expired(...)` im Pruefpunkt (`provider.py:378`), Sweep-Query mit `WHERE cimd_fetched_at IS NULL` (`store.py:907`); Tests `test_oauth_provider.py:977`, `:1014`, `test_oauth_store.py:781` | closed |
| T-06-32 | Tampering | Weiterlaufen mit veralteter Identitaet | mitigate | `_cimd_is_fresh` entscheidet (`provider.py:466`, `:1677-1684`), abgelaufene Frische erzwingt Abruf, fehlgeschlagener Abruf ist `None` (`:487-490`); Tests `:711`, `:731` (Zeile bleibt, Antwort ist Absage) | closed |
| T-06-33 | Information Disclosure | Fehlerbild verraet, ob ein Client existiert | mitigate | Jede Absage ist `None` (`provider.py:463,466,472,478,481,484,487,490,497,503,532`); Fehlerseitenwahl allein aus der Admin-Konfiguration (`consent.py:290-300`); parametrisierter Test ueber acht Absagearten (`test_oauth_provider.py:1031-1055`) | closed |
| T-06-34 | Denial of Service | Fehlerantworten als Cache-Zeilen | mitigate | Jeder Fehlerpfad kehrt vor `store.save_client` (`provider.py:515`) zurueck, kein Negativ-Cache im Modul; Test `:1055` "and none of them leaves a row behind" ueber 500, 404, 302 und vier kaputte 200er | closed |

### Plan 06-06: Anzeigepflichten der Zustimmungsseite

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-35 | Spoofing | Client-Impersonation ueber eine fremde `client_id`-URL bei Loopback | mitigate | Alle drei Anzeigen vorhanden: `client_id`-Host als Detaileintrag (`ui/consent.py:254-255`, `strings.py:288`), `redirect_uri` vollstaendig und ungekuerzt (`layout.py:324-333`), zusaetzliche Warnung bei ausschliesslich Loopback (`ui/consent.py:245-247`, `strings.py:268-273`); Verdrahtung `consent.py:455-465`; Test `test_oauth_consent.py:657`. Restluecke IN-02 siehe AR-06-05 | closed |
| T-06-36 | Tampering | XSS ueber `client_name`, `client_id` oder Hostname | mitigate | Ein Escaping-Ort: `_escape(term)`/`_escape(value)` in `layout.detail_list` (`layout.py:331`), Name zusaetzlich ueber `layout.client_name` (`ui/consent.py:237`); Escaping-Test ueber Elementanzahlen (`test_oauth_ui.py:494`) | closed |
| T-06-37 | Information Disclosure | Cross-Domain-Tracking ueber `logo_uri` | mitigate | Grep-Test `assert "logo_uri" not in source` (`test_oauth_ui.py:507-514`); eigener Grep: kein `<img` in `src/` | closed |
| T-06-38 | Repudiation | Ein Text, der "verifiziert" behauptet | mitigate | `CONSENT_LOOPBACK_BODY` sagt "is known" und "is not" und nennt nichts als bestaetigt (`strings.py:270-273`), Begruendung mit Threat-Verweis im Docstring (`:259-267`); eigener Grep: das Wort kommt im neuen Text nicht vor, nur in der aelteren Negation `Unverified client` | closed |
| T-06-39 | Denial of Service | Zusaetzlicher Store- oder Nextcloud-Roundtrip pro Zustimmungsseite | mitigate | Herkunft aus der Form der `client_id`, nicht aus dem Store (`consent.py:467-479`, Begruendung `:442-446`); kein zusaetzlicher `load_client` auf dem Pfad; Test "exactly one Nextcloud round trip per request" (`test_oauth_consent.py:711`) | closed |
| T-06-40 | Tampering | Doku behauptet mehr als gemessen ist | mitigate | Eigene Diff-Pruefung der vier 06-06-Commits (`79b0d19`, `13f74b9`, `5bed3ee`, `fd88a83`): kein README und kein `appinfo/info.xml` beruehrt, nur `ui/`, `oauth/consent.py`, `docs/oauth-setup.md`, CHANGELOG und Planungsdateien | closed |

### Plan 06-07: 34.0.3-Messung und Store-Oberflaeche

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-41 | Information Disclosure | Messdatei mit Credential | mitigate | Eigener Credential-Grep ueber `06-07-MEASUREMENTS.md` (`APP_SECRET=`, `HP_SHARED_KEY=`, Bearer-, Code- und App-Passwort-Form): 0 Treffer; die zwei `HP_SHARED_KEY`-Zeilen (`:12`, `:116`) beschreiben die Herkunft, nicht den Wert; Sicherungspfad ohne Inhalt (`:15`, `:91-92`) | closed |
| T-06-42 | Denial of Service | Upgrade verliert jane und die zwei Verbindungen | mitigate | Volume-Sicherung vor dem Upgrade mit Pfad und Groesse (`06-07-MEASUREMENTS.md:76-92`), Vorzustand mit Nutzernamen und Zeilen (`:66-71`), Nachzaehlung danach (`:238`, `:427-430`) | closed |
| T-06-43 | Tampering | Falscher Befund durch gleitenden Tag | mitigate | Pin `nextcloud:34.0.3-apache` (`compose.exapp.yml:53`), `occ status` als Belegzeile an drei Stellen (`06-07-MEASUREMENTS.md:43`, `:156`, `:262`), Versionen statt Tags in der Topologie-Tabelle (`:24-29`), ausdrueckliche Regel `:16` | closed |
| T-06-44 | Tampering | Falscher Befund durch Store-Cache oder falsches Konto | mitigate | Cache verworfen durch Ueberschreiben mit `timestamp 0`, vorher/nachher belegt (`06-07-MEASUREMENTS.md:280-293`), Gegenprobe `occ app_api:app:list` vor dem Blick (`:303`), Messung als Admin | closed |
| T-06-45 | Tampering | Messung gegen 0.1.1 statt Repo-Stand | mitigate | Rebuild belegt, Image-Digest vor und nach dem Rebuild in einer Tabelle (`06-07-MEASUREMENTS.md:212-213`, `:225-226`) | closed |
| T-06-46 | Repudiation | Ein Ein-Klick-Versprechen ohne Deckung | mitigate | Ausgang positiv, Befund als Frage-Antwort-Tabelle mit sichtbarem Text (`06-07-MEASUREMENTS.md:413-419`), statische Gegenprobe trotz positivem Ausgang (`:499`); der Doku-Satz nennt beide Versionen und ihren Unterschied (Commit `6ebd0ae`, `appinfo/info.xml` EN/DE/FR) | closed |
| T-06-47 | Tampering | Ungewolltes Store-Release | mitigate | `<version>0.1.2</version>` unveraendert (`appinfo/info.xml:65`); eigener Vergleich `30bce28..baab076` auf `appinfo/info.xml`: keine Versionszeile im Diff; letzter `v*`-Tag ist `v0.1.2` an `30bce28` aus Phase 5 | closed |
| T-06-48 | Denial of Service | Leeres Manifest-Element bricht den Store-Upload | mitigate | Kein leeres `<default>` (eigener Grep), Manifest-Gates im eigenen Testlauf gruen (`test_exapp_env_setup.py`) | closed |

### Plan 06-08: Cursor-Livebeweis

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-49 | Information Disclosure | Messdatei mit Token, Code oder App-Passwort | mitigate | Eigener Credential-Grep ueber `06-08-MEASUREMENTS.md`: 0 Treffer; Store-Zeilen ohne Chiffrat und ohne Hash zitiert (`:530-534`) | closed |
| T-06-50 | Tampering | Bestehende Cursor-Konfiguration wird ueberschrieben | mitigate | Vorzustand gelesen und belegt (`06-08-MEASUREMENTS.md:87-101`, Ergebnis `ABSENT`), Sicherungspfad ausserhalb des Repositories benannt, Nachzustand wiederhergestellt (`:631-634`) | closed |
| T-06-51 | Repudiation | Falscher Negativbefund durch Messung gegen 0.1.1 | mitigate | Version und Image-Digest als Pflichtangabe der Topologie-Tabelle (`06-08-MEASUREMENTS.md:29`), erneut im Nachzustand (`:588`, `:679`) | closed |
| T-06-52 | Tampering | Stille Installation fremder Software auf dem Owner-Rechner | mitigate | Blockierender Halt statt Installation, Ausloeser nicht eingetreten und ausdruecklich festgehalten (`06-08-MEASUREMENTS.md:108-110`); der zweite Halt wurde vom Operator aufgeloest (`:345-372`) | closed |
| T-06-53 | Information Disclosure | Zitierter Werkzeuginhalt offenbart Fremddaten | mitigate | Nur `jane` aus der 05-03-Fixture (`06-08-MEASUREMENTS.md:32`, `:269`, `:530-534`); kein Abschnitt mit Werkzeuginhalt, weil es keinen Aufruf gab (`:520`) | closed |
| T-06-54 | Repudiation | Doku behauptet einen Lauf, der nicht stattfand | mitigate | Negativbefund im Titel statt in einer Fussnote (06-08-SUMMARY.md:28), die drei READMEs unangetastet (`:50`), Doku waehrend des Halts unangetastet (`:155-156`); Doku-Aenderung erst mit dem gemessenen Ergebnis (Commit `cfc98e5`) | closed |

### Plan 06-09: CIMD-Rundlauf und Loopback-Portfrage, live

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-55 | Elevation of Privilege | Umgehung des abgeschalteten DCR ueber CIMD, live | mitigate | Kontrollprobe 1 belegt beides: 400 `Automatic registration is off` in 0,126 s und `sockets to port 443 seen: 0` gegen die Positivkontrolle (`06-09-MEASUREMENTS.md:504-545`) | closed |
| T-06-56 | Elevation of Privilege | Umgehung der Allowlist ueber CIMD, live | mitigate | Kontrollprobe 3, beide Richtungen, zeichengleich dieselbe Seite `This app is not allowed` wie beim ungelisteten DCR-Client (`06-09-MEASUREMENTS.md:582-608`) | closed |
| T-06-57 | Spoofing | Port-Squatting auf Loopback nach der Lockerung | accept | Restrisiko benannt statt weggelassen, mit drei Gruenden (`docs/oauth-setup.md:864-905`), Anzeigepflichten der Consent-Seite daneben (`:360-373`). Restrisiko AR-06-02 | closed |
| T-06-58 | Tampering | Gegenprobe fehlt, der Lauf belegt nur Durchlass | mitigate | Abschnitt 5 mit abweichendem Pfad und Host-Wechsel, je mit Fehlerbild (`06-09-MEASUREMENTS.md:387-419`) | closed |
| T-06-59 | Information Disclosure | Messdatei mit Token, Code oder Schluessel | mitigate | Eigener Credential-Grep ueber `06-09-MEASUREMENTS.md`: 0 Treffer; die eine `HP_SHARED_KEY`-Zeile (`:12`) beschreibt die Herkunft | closed |
| T-06-60 | Denial of Service | Ein Schalter bleibt nach der Messung stehen | mitigate | Nachzustand Zeile fuer Zeile belegt: keine `NC_MCP_OAUTH_*`-Variable im Container, AS-Dokument traegt beide Felder wieder, `occ app_api:app:list` als Abschlusspruefung (`06-09-MEASUREMENTS.md:323-328`, `:637`) | closed |
| T-06-61 | Tampering | Client-Konfiguration des Owners wird ueberschrieben | mitigate | Vor jedem Lauf `claude mcp logout`, Vorzustand und Rueckweg belegt (`06-09-MEASUREMENTS.md:330-334`, Nachzustand Abschnitt 11) | closed |
| T-06-62 | Repudiation | "Der Port wechselt" als Behauptung statt als Messung | mitigate | Vier Laufzeilen mit Uhrzeit und Port, drei frei gewaehlt, Lauf 4 getrennt mit `MCP_OAUTH_CALLBACK_PORT=34567` (`06-09-MEASUREMENTS.md:336-347`); dieselben Zahlen in der Doku (`docs/oauth-setup.md:886-892`) | closed |

### Plan 06-10: Conference-Material

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-63 | Information Disclosure | Credential in einem kopierbaren Kommando | mitigate | Eigener Credential-Grep ueber `docs/conference-demo.md`: 0 Treffer; die zwei `HP_SHARED_KEY`-Zeilen erzeugen (`:76`, `openssl rand`) beziehungsweise lesen zurueck (`:87`, `sed` aus `.env.exapp`), keine schreibt einen Wert hin | closed |
| T-06-64 | Information Disclosure | Bildschirminhalt der Demo zeigt fremde Daten | mitigate | Abschnitt "Where this stands" nennt Wegwerf-Instanz und Wegwerf-Konto `alice` (`docs/conference-demo.md:14-28`) und sagt, dass die zwei `jane`-Verbindungen nicht angefasst werden (`:43-45`) | closed |
| T-06-65 | Repudiation | Der Talk behauptet mehr als gemessen ist | mitigate | Tabelle "Where each claim on a slide comes from" bindet jede Produktbehauptung an ihre Fundstelle (`docs/conference-talk.md:158-174`), eigener Abschnitt "What this draft does not say, on purpose" (`:175-186`) | closed |
| T-06-66 | Tampering | Ungewollte Einreichung oder Kontaktaufnahme | mitigate | Status ohne Dekoration, Einreichung ist Owner-Entscheidung (`docs/conference-talk.md:12-20`), Einreichungstext als gekennzeichneter Entwurf (`:187-190`) | closed |
| T-06-67 | Denial of Service | Ein Drehbuch, das auf der Buehne nicht funktioniert | mitigate | Ein vollstaendiger Durchlauf, Zeiten je Schritt im Ueberschriftentext (`docs/conference-demo.md:125,144,169,185,232,253`), Pre-Demo-Checkliste (`:283`) und Rueckfallabschnitt "Recovery" (`:350-362`); vier Fehler im Drehbuch korrigiert (Commit `21bd973`) | closed |
| T-06-68 | Denial of Service | Instanzzustand bleibt nach der Demo verstellt | mitigate | Nachzustand belegt: App `enabled`, drei Schalter im Ausgangszustand mit Gegenprobe am AS-Dokument, Store zaehlgleich (`06-10-MEASUREMENTS.md:323-330`) | closed |

### Plan 06-11: Der Ausweg auf der Absageseite E5

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-60/11 | Information Disclosure | `ui/strings.py`, `ERROR_REDIRECT_BODY` | mitigate | Der neue Satz nennt keinen Protokollwert, keinen Parameternamen, keine Adresse und kein Scheme (`strings.py:478-484`) und ist fuer alle vier E5-Aufrufstellen gleich wahr (`consent.py:258,271,281,285`); bestehende Gates plus neuer Test `test_the_return_address_page_names_the_way_that_works` (`test_oauth_ui.py:678`) | closed |
| T-06-61/11 | Spoofing | dieselbe Seite | mitigate | Kein Link, keine URL, kein erfundener Klickpfad: der Ausweg steht in Worten (`strings.py:481-483`), nach dem E8-Muster derselben Datei (`:490-492`) | closed |
| T-06-62/11 | Tampering | `oauth/registry.py`, `provider.py`, `consent.py` | accept | Eigene Diff-Pruefung ueber die sechs 06-11-Commits: leerer Diff auf `src/mcp_connector/oauth/`; die eine Code-Aenderung liegt in `exapp/ui/strings.py` (Commit `91a42ca`). Restrisiko AR-06-04 | closed |
| T-06-63/11 | Repudiation | `.planning/BACKLOG.md`, `.planning/REQUIREMENTS.md` | mitigate | BL-14 mit Datum, Urheber, gewaehlter Option, dem Grund und den vier Optionen als Protokoll (`.planning/BACKLOG.md:401-426`); dieselbe Kennzeichnung in `REQUIREMENTS.md` (CLIENT-04) und `ROADMAP.md` (SC3), belegt in 06-VERIFICATION.md Punkt 3b | closed |
| T-06-64/11 | Information Disclosure | oeffentliche Planungsdateien | mitigate | Eigener Credential-Grep ueber die geschriebenen Planungsdateien: 0 Treffer; der einzige Bearer-Treffer im Phasenverzeichnis ist der Platzhalter `Bearer a-long-random-string` (06-11-SUMMARY.md:160) | closed |

### Alle Plaene: Supply Chain

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-06-SC | Tampering | npm/pip/cargo installs (11 Plaene, eine Aussage) | mitigate | Eigene Diff-Pruefung: `git log 30bce28..f281458 -- pyproject.toml uv.lock` ist leer, also hat in der ganzen Phase kein Commit eine Abhaengigkeit oder die Lockdatei angefasst. `httpx`, `httpcore`, `respx`, `anyio` standen bereits in `uv.lock` und in `docs/dependency-audit.md`; `ipaddress`, `socket`, `json`, `asyncio` sind Standardbibliothek. `cimd._system_addresses` nutzt bewusst `loop.getaddrinfo` statt eines `anyio`-Direktimports, mit der Dependency-Policy als Grund (`cimd.py:236-248`) | closed |

---

## Register-Hygiene

Ein Befund am Register selbst, ohne Sicherheitswirkung, aber mit Wirkung auf jede spaetere
Nachverfolgung: **Plan 06-11 hat die Nummern `T-06-60` bis `T-06-64` erneut vergeben**,
obwohl `T-06-60`, `T-06-61` und `T-06-62` schon in Plan 06-09 und `T-06-63`, `T-06-64` schon
in Plan 06-10 belegt waren. Es sind zehn verschiedene Bedrohungen mit fuenf Nummern. Dieses
Dokument loest die Kollision mit dem Zusatz `/11` auf und zaehlt beide Saetze. Wer in einer
spaeteren Phase auf `T-06-62` verweist, muss den Plan mitnennen.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-01 | T-06-06 | Groessen-, Zeit- und Cache-Grenzen des Dokumentabrufs sind Modulkonstanten ohne Umgebungsschalter. Ein Schalter auf einer Grenze ist eine Grenze, die ein Admin versehentlich aufweichen kann; genau dagegen existiert `cimd.py`. Preis: eine Instanz mit einem langsamen oder groesseren Dokumentanbieter kann die Werte nicht anpassen und braucht eine neue Version (Open Question 5 der Recherche) | Owner (Planzeit 06-01) | 2026-08-20 |
| AR-06-02 | T-06-17, T-06-57 | Port-Squatting auf Loopback. RFC 8252 Abschnitt 7.3 verlangt die Lockerung als MUST, und die Messung (vier Laeufe, drei verschiedene Ports) bestaetigt den Anlass. Grenze: alles ausser dem Port bleibt zeichengenau, `localhost` steht nicht fuer `127.0.0.1`, ohne PKCE-Verifier ist der Code nicht einloesbar, und die Zustimmungsseite warnt ausdruecklich, wenn alle Rueckadressen auf dem eigenen Rechner liegen | Owner (Entscheid 2026-08-20, `docs/oauth-setup.md:900-905`) | 2026-08-20 |
| AR-06-03 | T-06-23 | Das AS-Metadatendokument ist oeffentlich lesbar und verraet damit den Konfigurationszustand zweier Schalter (Registrierung an/aus, CIMD an/aus). Das ist der Zweck des Dokuments: ein Client muss wissen, welchen Weg er nehmen kann. Es nennt nur oeffentliche URLs, Scopes und Methodenlisten, gemessen seit Phase 2 und durch Mengengleichheit auf die Feldnamen festgenagelt | Owner (Planzeit 06-04) | 2026-08-20 |
| AR-06-04 | T-06-62/11 | Plan 06-11 hat den Auth-Pfad bewusst nicht angefasst, obwohl der Anlass (Cursor wird an `/authorize` abgewiesen) dort liegt. D-35 bleibt: private-use-Schemes bleiben unregistrierbar, weil auf einem Desktop kein Programm ein Scheme exklusiv besitzt. Der Preis ist, dass Cursor 3.2.16 sich per OAuth nicht verbindet und den App-Passwort-Weg nehmen muss; belegt durch leeren Diff auf `src/mcp_connector/oauth/` und dokumentiert in BL-14 mit allen vier verworfenen Optionen | Owner (Entscheid 2026-08-20, BL-14 Option 3) | 2026-08-20 |
| AR-06-05 | T-06-03, T-06-35, T-06-29 | Die drei Info-Befunde des Code-Reviews bleiben nach Owner-Vorgabe (Fix-Scope Critical plus Warning) unbehoben und sind damit akzeptierte Restrisiken, nicht offene Punkte: **IN-01** `is_cimd_client_id` verwirft prozentkodierte Dot-Segmente (`%2e%2e`) nicht, eine Abweichung vom Draft-MUST-NOT ohne SSRF-Wirkung, weil die Kennung byte-fuer-byte als Identitaet gebunden und die Verbindung an die geprueften Adressen gepinnt wird (`cimd.py:151`). **IN-02** Anzeige und Formpruefung lesen den Host in Unicode, verbunden wird nach Punycode, was eine Homoglyph-Anzeige auf der Zustimmungsseite erlaubt; kein XSS, alles escaped (`cimd.py:344`, `consent.py:479`). **IN-03** kein Element-Limit auf `redirect_uris` eines Dokuments, gedeckelt allein durch das 5120-Byte-Limit (`cimd.py:499`, `provider.py:499`) | Owner (Fix-Scope-Vorgabe 2026-08-20, 06-REVIEW.md:225-226) | 2026-08-20 |

---

## Review-Fixes, einzeln nachgewiesen

Die drei Warnings des Code-Reviews sind Teil dieser Verifikation, weil sie die
Verdrahtung genau der Kontrollen betreffen, die das Register deklariert.

| Finding | Fix-Commit | Beleg im ausgelieferten Stand |
|---------|-----------|-------------------------------|
| WR-01: CIMD-Refetch auf dem Token-Verifikations-Hot-Path | `a47bb57` | `get_client(..., may_fetch=...)` (`provider.py:310`), `may_fetch=False` bei `verifier.py:227`, `provider.py:1511` (Client-Auth `/token` und `/revoke`); Kurzschluss `if not may_fetch: return row` (`provider.py:469-473`); Tests `test_oauth_provider.py:751`, `:776`, `:795`, `:836` (laufende Sitzung ueberlebt einen Ausfall des Dokument-Hosts) |
| WR-02: Allowlist verhindert den ausgehenden Fetch nicht | `bd75cd8` | `if self._policy.allowlist_only and not self._policy.listed(client_id): return None` vor jeder Aufloesung und vor jedem Paket (`provider.py:474-478`); Tests `:577` (ungelistet ohne Zeile), `:600` (ungelistet mit abgelaufener Zeile), `:622` (gelistet mit Fetch); die verbleibende Asymmetrie (Listung per Rueckadresse kann den Abruf nicht freischalten) ist fail-closed und im Docstring benannt (`:437-445`) |
| WR-03: Refetch im Token-Pfad widerspricht der Zusage der Exchange-Methoden | `a47bb57` | `get_client(client.client_id, may_fetch=False)` in beiden Exchanges (`provider.py:787`, `:902`); Tests `:877` (Rotation an der Frische-Grenze ohne Paket), `:915`, `:955` (unbekannter Dokument-Client = 401 ohne Paket) |

---

## Unregistered Flags

Aus den `## Threat Flags`-Abschnitten der elf SUMMARYs plus einem Fund der Messung. Keiner
davon ist ein Blocker; jeder ist eine Beobachtung ohne eigene Register-Zeile.

| Flag | Quelle | Bewertung |
|------|--------|-----------|
| Jeder Anmeldeversuch von Cursor legt eine nie benutzte DCR-Zeile an; die Zeilen tragen kein Geheimnis und keinen Nutzerbezug, wachsen aber mit der Zahl der Klicks | 06-08-SUMMARY, Threat Flags | Unregistriert. Gedeckelt durch die zwei Registrierungs-TTLs (`registry.UNUSED_REGISTRATION_TTL`, `IDLE_REGISTRATION_TTL`) und den Sweep in `store.expired_clients`, der genau solche Zeilen entfernt. Kein Blocker, Kandidat fuer eine Register-Zeile in einer spaeteren Phase |
| Jeder abgebrochene Anmeldeversuch legt eine `flows`-Zeile an, die auf ihr Zeitfenster wartet | 06-09-SUMMARY, Threat Flags | Unregistriert, dasselbe Muster. Gedeckelt durch `FLOW_TTL` plus opportunistisches Aufraeumen aus Phase 3 (T-03-32, T-03-35) |
| Die Absage bei abgeschaltetem CIMD zeigt `This link has expired`, ein Wortlaut, der nicht zur Ursache passt | 06-09-SUMMARY, Threat Flags | Unregistriert, mit T-03-47 vereinbar (die Seite sagt ohnehin nie, welche Pruefung fiel). Textkandidat, kein Sicherheitsbefund |
| Mit bewaffneter Allowlist und leerer Liste antwortet `POST /register` weiter 201 | 06-09-MEASUREMENTS.md:609-616 | Unregistriert und by design: D-35 nennt vier Pruefpunkte, die Allowlist sitzt in `get_client` und damit an `/authorize`, `/token`, `/revoke`. Eine Registrierung ist keine Autorisierung, und `docs/oauth-setup.md` sagt genau das. Notiert, damit niemand eine Luecke sieht, wo keine ist |
| Der Widerruf nimmt das Refresh-Token belegt mit (`POST /token 400` im Auffrischversuch) | 06-10-SUMMARY, Threat Flags | Gewuenschtes Verhalten aus Phase 3 (T-03-62), erstmals an einem fremden Client gesehen. Keine neue Flaeche |
| `also_accepting` als neue Form an einer Vertrauensgrenze | 06-03-SUMMARY, Threat Flags | Abgebildet auf T-06-16 und T-06-19: die Kopie lebt eine Anfrage lang, traegt genau die von `loopback_match` gematchte Adresse und schreibt nichts (`provider.py:534-554`). Informationell |
| Ausnahme in `store.expired_clients` fuer Zeilen mit `cimd_fetched_at` | 06-05-SUMMARY, Threat Flags | Abgebildet auf T-06-31, zweite Stelle derselben Absicht (`store.py:907`). Informationell |

---

## Beobachtungen ohne Blockerwirkung

- **T-06-10 (transfer):** Der Empfaenger der Uebergabe ist verifiziert vorhanden und
  verdrahtet. Die im Mitigation-Plan angekuendigte Anschlussfrage ("ob eine eigene Klasse
  noetig ist, wird erst nach der Live-Messung in 06-09 entschieden") ist in 06-09 weder
  beantwortet noch nach `deferred-items.md` uebernommen worden. Das aendert nichts an der
  Drosselung, die heute laeuft, sollte aber beim naechsten Anfassen der Throttle-Klassen
  nachgeholt werden.
- **Eigener Testlauf am 2026-08-20:** `tests/unit/test_oauth_cimd.py`,
  `test_oauth_provider.py`, `test_oauth_registry.py`, `test_oauth_consent.py`,
  `test_oauth_ui.py`, `test_exapp_responses.py`, `test_oauth_metadata.py`,
  `test_exapp_env_setup.py`, `test_exapp_entry.py`: alle gruen, Arbeitsbaum bei `f281458`
  sauber.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 74 | 74 | 0 | gsd-security-auditor (opus) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-20
