---
phase: 3
slug: oauth-2-1
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-16
---

# Phase 3: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Restrisiken, Audit-Trail.
> Register-Quelle: die neun threat_model-Blöcke der Pläne 03-01 bis 03-09 (State B, zur
> Planzeit erstellt), 70 Positionen. Verifiziert am 2026-08-16 durch gsd-security-auditor
> (opus) gegen den Quelltext bei `e32a084` (Arbeitsbaum sauber), gegen eigene Testläufe
> (14 OAuth-Unit-Dateien, alle grün) und gegen die noch laufende öffentliche
> Staging-Instanz `https://nc-staging.infranode.dev` (nur lesende Messungen, 09:17 bis
> 09:20 UTC).
>
> Dieses Audit sucht keine neuen Schwachstellen. Es prüft für jede der 70 Positionen, ob
> die in ihrer Zeile deklarierte Gegenmaßnahme im ausgelieferten Stand wirklich existiert.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Internet zu PUBLIC-Routen | Zwölf verankerte Routen sind ohne Nextcloud-Sitzung erreichbar, `/mcp` eingeschlossen | Bearer-Token, OAuth-Parameter, Formularentscheidungen |
| HaRP zu ExApp | HaRP setzt `AUTHORIZATION-APP-API`; die Nutzer-Id darin ist leer, wenn der Aufrufer keine Nextcloud-Credentials sendet | Aufgelöste User-Id, APP_SECRET |
| Beliebiger Client zu /register und /authorize | Offene Registrierung im Auslieferungszustand (D-35); Name, Redirect-Ziel, Scope und Resource kommen aus fremder Hand | Client-Metadaten, Redirect-URI, PKCE |
| Browser des Nutzers zu Consent- und Onboarding-Seiten | Ein POST entscheidet über den Zugriff auf ein ganzes Konto; eine Seite zeigt einmalig ein App-Passwort | Flow-Id, Anti-Fälschungs-Merkmal, App-Passwort |
| ExApp zu Nextcloud (Login Flow v2, OCS) | Ausgehende Aufrufe erzeugen und löschen echte Zugänge | App-Passwörter, Poll-Token, Datenschlüssel |
| ExApp zu Volume und ExApp-Config | Der Store liegt im Docker-Volume, der Datenschlüssel in `oc_appconfig` (sensitive=1) | Chiffretexte, Token-Hashes, Datenschlüssel |
| Reverse Proxy des Admins zu HaRP | Zwei zusätzliche Rewrite-Regeln auf der Domain-Wurzel | Discovery-Anfragen |
| Fremder Anbieter zu unserem Authorization Server | Claude.ai und ChatGPT registrieren sich selbst und halten Tokens | Registrierungen, Refresh-Token |
| Dokumentation und Messartefakte zu Betreibern | Eine falsche Anleitung erzeugt eine unsichere Instanz; Logauszüge tragen Pfade und Zeitstempel | Konfigurationswissen, Zugangsdaten |

---

## Threat Register

70 Positionen: 68 `mitigate`, 2 `accept`. **70 closed, 0 open.** Belege verkürzt; jede
Zeile wurde einzeln gegen den Quelltext geprüft, nicht gegen die SUMMARYs.

Das Audit vom 16.08.2026 hatte drei Positionen offen gelassen (T-03-80, T-03-82, T-03-84).
Alle drei betrafen nicht den Code, sondern den zu diesem Zeitpunkt noch nicht ausgeführten
Rückbau der öffentlichen Staging-Instanz. Der Rückbau ist am selben Tag zwischen 09:25 und
09:29 UTC vollzogen worden; der Beleg steht im Abschnitt "Teardown der Staging-Instanz"
weiter unten und schließt die drei Positionen.

### Plan 03-01: Discovery und Bearer-Grenze

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-01 | Elevation | exapp/middleware.py, entry_exapp.py | mitigate | Bearer-Grenze vor `/mcp`; ohne Verifier ist jeder Bearer ungültig (`middleware.py:123-124`); Wächter `guarded != 1` wirft beim Start (`entry_exapp.py:99-107`) | closed |
| T-03-02 | Spoofing | oauth/metadata.py | mitigate | Alle drei Dokumente aus `config.public_url` (`metadata.py:149,170,201`); `request.` kommt in der Datei nicht vor (Grep leer); Fremdhost-Test `test_oauth_metadata.py:147` | closed |
| T-03-03 | Tampering | exapp/responses.py | mitigate | `json_response` merged `NO_STORE` statt zu ersetzen (`responses.py:41`, IN-06-Form); `NoStore`-Wrapper über allen AS-Routen (`provider.py:1090,1255`) | closed |
| T-03-04 | Info Disclosure | oauth/metadata.py | mitigate | Fester Feldsatz, `exclude_none`, `RESOURCE_NAME` ohne Version und Host (`metadata.py:99,137-158`); Mengengleichheits-Test | closed |
| T-03-05 | DoS | appinfo/info.xml | mitigate | Zwölf beidseitig verankerte Routen; Gate prüft Start- und Endanker (`test_exapp_env_setup.py:179,192`) mit Gegenproben (`:737,:768`) und Mengengleichheit Manifest/Starlette (`:882-888`); live 404 auf jedem undeklarierten Nachbarn | closed |
| T-03-06 | Info Disclosure | exapp/middleware.py | mitigate | 401 ohne Body, Challenge aus Konstanten (`middleware.py:67-72,104,159-167`); live gemessen: `Content-Length: 0`, kein Echo | closed |
| T-03-07 | Tampering | deploy/Caddyfile | mitigate | Zwei exakte Pfad-Matcher ohne Wildcard (`Caddyfile:25,30`), Kommentar nennt T-03-07 | closed |
| T-03-08 | DoS | Discovery-Routen | accept | Antworten statisch, klein, ohne DB-Zugriff; Drosselung der Auth-Pfade in 03-07 vorhanden. Restrisiko AR-03-01 | closed |

### Plan 03-02: Store und Krypto

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-10 | Info Disclosure | oauth/crypto.py, store.py | mitigate | AESGCM mit `aad=auth_id` (`store.py:531,581`), Schlüssel in der ExApp-Config mit `sensitive: 1` (`crypto.py:259`); Byte-Test über die Store-Dateien (`test_oauth_store.py:65`) | closed |
| T-03-11 | Info Disclosure | oauth/store.py | mitigate | Nur `token_hash` (sha256-hex) in allen Token-Spalten (`store.py:207-214,768,851,904,945`); Byte-Test sucht den Klartext | closed |
| T-03-12 | Tampering | oauth/crypto.py | mitigate | `encrypt/decrypt` mit `aad` gleich der Zeilen-Id (`crypto.py:112-136`), fremde `aad` liefert `DecryptionRejected`; Test vorhanden | closed |
| T-03-13 | Elevation | oauth/store.py | mitigate | `BEGIN IMMEDIATE` plus `UPDATE ... WHERE state`, Auswertung von `rowcount` (`store.py:812-818,949-955`); Nebenläufigkeitstest | closed |
| T-03-14 | DoS | oauth/crypto.py | mitigate | Eigener Datenschlüssel in der ExApp-Config (D-43); Quelltext-Gate `assert "APP_SECRET" not in code` (`test_oauth_crypto.py:447`) | closed |
| T-03-15 | DoS | entry_exapp.py | mitigate | `config.persistent_storage()` vor dem ersten Request, benannter Fehler und `SystemExit(2)` (`entry_exapp.py:184-199`) | closed |
| T-03-16 | Info Disclosure | crypto.py, loginflow.py | mitigate | `DecryptionRejected` ohne Argumente (`crypto.py:101-109`), maskierte reprs (`loginflow.py:115,126`), caplog-Tests auf DEBUG | closed |
| T-03-17 | DoS | oauth/store.py | mitigate | `_purge_expired_rows` an fünf Zugriffspfaden (`store.py:461,762,846,903,1032`), Fristen als benannte Konstanten (`store.py:90-112`) | closed |
| T-03-SC | Tampering | pyproject.toml | mitigate | Blockierender Owner-Checkpoint dokumentiert (03-02-SUMMARY "Owner Decision", `docs/dependency-audit.md`); Pin `cryptography>=50,<51`; slopcheck-Ausfall begründet | closed |

### Plan 03-03: Seiten und Fehlerseiten

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-20 | Tampering | exapp/ui/layout.py | mitigate | `_escape` an genau einer Stelle je Fragment (`layout.py:263-431`), Namenssäuberung mit Längenschnitt; Parser-Test | closed |
| T-03-21 | Spoofing | exapp/ui/layout.py | mitigate | `frame-ancestors 'none'` in der CSP und `X-Frame-Options: DENY` in derselben Funktion (`layout.py:68-69,493-495`); live auf Staging bestätigt | closed |
| T-03-22 | Elevation | exapp/ui/layout.py | mitigate | `default-src 'none'` ohne `script-src`, kein JavaScript im Projekt, Gate über `ui/*.py` (`test_oauth_connect.py:625`) | closed |
| T-03-23 | Spoofing | exapp/ui/strings.py, layout.py | mitigate | Eigene Wortmarke plus konfigurierter Host in der Leiste (`layout.py:506-511`), Fußzeile `FOOTER_PASSWORD_PROMPT` (`strings.py:102`), Test `test_oauth_ui.py:426` | closed |
| T-03-24 | Info Disclosure | exapp/ui/errors.py | mitigate | Sieben feste Texte aus einer Tabelle (`errors.py:66-79`), nur E7 trägt eine Zufallsreferenz (`errors.py:106,131`); Verbotsliste als Test. Restrisiko AR-03-06 (WR-08) | closed |
| T-03-25 | Tampering | exapp/ui/layout.py | mitigate | `no-store` aus derselben Quelle wie die JSON-Antworten, in `_headers` gesetzt (`layout.py:485-496`) | closed |
| T-03-26 | Info Disclosure | exapp/ui/layout.py | mitigate | `Referrer-Policy: no-referrer` auf jeder Seite (`layout.py:495`) | closed |

### Plan 03-04: Browser-Onboarding

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-30 | Spoofing | oauth/connect.py, ui/connect.py | mitigate | Kein Eingabefeld auf der Strecke (nur `type="hidden"`), Quelltext-Gate gegen `type="password"/"email"/"text"` (`test_oauth_connect.py:627`); Fußzeile mit Phishing-Hinweis | closed |
| T-03-31 | Tampering | oauth/loginflow.py | mitigate | `safe_user_agent`: druckbares ASCII, Whitespace-Kollaps, Schnitt auf 64, festes Präfix (`loginflow.py:137-155`); parametrisierter Test | closed |
| T-03-32 | Info Disclosure | oauth/connect.py | mitigate | Flow-Id aus `secrets.token_urlsafe(32)` (`connect.py:204`), Poll-Token verschlüsselt mit `aad=flow_id` (`store.py:458`), `FLOW_TTL = 1200`, Löschen nach der Anzeige (`connect.py:293,300`); zusätzlich CR-01-Identitätsvergleich (`connect.py:286`) | closed |
| T-03-33 | Info Disclosure | oauth/connect.py | mitigate | Credential wird nirgends gespeichert; Byte-Test über das Store-Verzeichnis (`test_oauth_connect.py:162`); `no-store` und `no-referrer` je Seite | closed |
| T-03-34 | DoS | ui/connect.py | mitigate | Genau ein Poll je Seitenaufruf (`connect.py:278`), `REFRESH_SECONDS = 3` als meta-refresh (`ui/connect.py:75-85`), harte Ablauffrist statt Schleife; Zählertest | closed |
| T-03-35 | DoS | oauth/throttle.py, connect.py | mitigate | `CLASS_CONNECT_START` mit `count_all=True` und `FLOW_LIMIT = 20` je Quelle und Fenster (CR-02-Fix, `throttle.py:106-118,319`); Flows verfallen nach 20 Minuten und werden opportunistisch aufgeräumt | closed |
| T-03-36 | Info Disclosure | oauth/loginflow.py | mitigate | Maskierte reprs für `FlowStart` und `AppCredentials` (`loginflow.py:114-126`), caplog-Test auf DEBUG | closed |
| T-03-37 | Repudiation | oauth/loginflow.py | mitigate | `AGENT_PREFIX = "MCP Connector: "` (`loginflow.py:78`); Widerrufsweg in `docs/oauth-setup.md` (Security notes, "Devices and sessions") | closed |

### Plan 03-05: Registrierung und Autorisierung

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-40 | Elevation | oauth/provider.py, registry.py | mitigate | `get_client` ist der Enforcement-Punkt für authorize, token und revoke (`provider.py:295-336`), vierter Punkt im Verifier (`verifier.py:215-218`); Test über alle vier Ablehnungsgründe | closed |
| T-03-41 | Tampering | oauth/registry.py, provider.py | mitigate | Exaktes Matching des SDK plus `redirect_uri_allowed` (https, Loopback-Ausnahme) bei Registrierung (`provider.py:389-390`) und erneut bei der Nutzung (`consent.py:220-223`) mit E5 statt Weiterleitung | closed |
| T-03-42 | Spoofing | exapp/ui/consent.py | mitigate | Callout `CONSENT_WARNING_TITLE = "Unverified client"` (`strings.py:204`), Redirect-Ziel prominent, Name escaped und gekürzt | closed |
| T-03-43 | Tampering | oauth/loginflow.py | mitigate | Säuberung plus festes Präfix vor dem `User-Agent` des Start-Requests (`loginflow.py:170`); CR/LF-Test (`test_oauth_abuse.py:609`) | closed |
| T-03-44 | DoS | oauth/registry.py, store.py | mitigate | DCR global abschaltbar und Allowlist-Modus (`registry.py:54-60,117-126`), `UNUSED_CLIENT_TTL = 24h` und `IDLE_CLIENT_TTL` (`store.py:109-112`), Ablauf in `get_client` mit Rückgabe der App-Passwörter (WR-04-Fix, `provider.py:326-333`) | closed |
| T-03-45 | Tampering | oauth/provider.py | mitigate | `NoStore`-ASGI-Wrapper über allen AS-Routen, überschreibt `public, max-age` der SDK-Handler (`provider.py:1090,1255-1283`) | closed |
| T-03-46 | Elevation | oauth/provider.py | mitigate | `resource` ist an `/authorize` Pflicht (`provider.py:428-432`), erneut geprüft bei Ausgabe (`:539-542`), Refresh (`:672-675`) und im Verifier (`verifier.py:211`) | closed |
| T-03-47 | Info Disclosure | oauth/provider.py, consent.py | mitigate | `get_client` liefert in allen vier Fällen `None` (`provider.py:295-336`); E1/E2/E3 werden aus der Admin-Konfiguration gewählt, nicht aus dem Client-Zustand (`consent.py:243-248`) | closed |
| T-03-48 | DoS | oauth/provider.py | accept | Ein Nextcloud-Roundtrip je Antrag, ausschließlich im Browserpfad (`provider.py:434`), nie im Token-Pfad; Drosselung `CLASS_AUTHORIZE_START`. Restrisiko AR-03-02 | closed |

### Plan 03-06: Consent, Code-Tausch, Verifikation

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-50 | Tampering | oauth/consent.py, crypto.py | mitigate | Zustandswechsel nur per POST (`consent.py:178`), `form_token` = HMAC(data_key, flow_id) (`crypto.py:139-154`), Vergleich mit `compare_digest` (`consent.py:537`), `form-action 'self'` in der CSP (`layout.py:68`). Zusätzlich CR-01: Vergleich der HaRP-aufgelösten Identität mit `authorization.nc_user` | closed |
| T-03-51 | Elevation | provider.py, verifier.py | mitigate | `check_resource_allowed` an vier Stellen; fehlende Resource wird abgelehnt (`provider.py:429-431,540-542,673-675`, `verifier.py:211-214`) | closed |
| T-03-52 | Spoofing | provider.py, store.py | mitigate | `code_challenge_methods_supported: ["S256"]` (live gemessen), `AUTH_CODE_TTL = 60`, einmalige Einlösung per `UPDATE ... used_at IS NULL` unter `BEGIN IMMEDIATE` (`store.py:802-828`), Bindung an Client und Redirect-URI | closed |
| T-03-53 | Spoofing | oauth/consent.py, metadata.py | mitigate | `iss` auf beiden Rückwegen (`consent.py:472,511`), `authorization_response_iss_parameter_supported: true` in den AS-Metadaten (`metadata.py:194`, live bestätigt) | closed |
| T-03-54 | Info Disclosure | provider.py, verifier.py, store.py | mitigate | Hash statt Klartext im Store, maskierte Datensätze, Echo-Test über alle Ablehnungspfade (`test_oauth_abuse.py:826`), caplog-Test auf DEBUG (`:836`) | closed |
| T-03-55 | Elevation | verifier.py, provider.py | mitigate | Policy-Prüfung im Verifier (`verifier.py:215-218`) und beim Code-Tausch (`provider.py:545`), nicht nur bei der Registrierung | closed |
| T-03-56 | DoS | verifier.py, provider.py | mitigate | Fail-closed: jeder Store-Fehler wird zu `None` bzw. zu einer Ablehnung (`verifier.py:203-207,250-252`, `provider.py:304-311`); Test mit werfendem Store | closed |
| T-03-57 | Elevation | exapp/middleware.py | mitigate | Eine Verzweigung an der leeren Nutzer-Id (`middleware.py:108`); der ExApp-Zweig liest den `Authorization`-Header nicht; Test mit beiden Kanälen | closed |
| T-03-58 | DoS | oauth/provider.py | mitigate | `exchange_authorization_code` (`provider.py:512-575`) enthält keinen `loginflow`-Aufruf (Aufrufe nur bei 434, 897, 934, 996); Quelltext-Gate gegen `while`, `range(`, `sleep` (`test_oauth_abuse.py:855`) | closed |

### Plan 03-07: Rotation, Widerruf, Drosselung

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-60 | Spoofing | provider.py, store.py | mitigate | Rotation bei jeder Nutzung, Reuse-Detection tötet die Familie (`provider.py:697-712,754`, `store.py:986`); Missbrauchsmatrix `test_oauth_abuse.py:344` | closed |
| T-03-61 | DoS | oauth/provider.py | mitigate | `ROTATION_GRACE = 10` mit vorgehaltener Antwort und ohne zweiten Familienzweig (`provider.py:697-699,760-777`); Test für beide Seiten des Fensters (`test_oauth_abuse.py:377`) | closed |
| T-03-62 | Elevation | provider.py, verifier.py | mitigate | `provider.on_revocation(verifier.invalidate)` (`entry_exapp.py:92`), `_end_connection` leert den Cache (`provider.py:758`); Test unmittelbar nach dem Widerruf | closed |
| T-03-63 | Repudiation | provider.py, loginflow.py | mitigate | `note_cleanup` vor dem Versuch, dann `revoke_app_password` mit `REVOKE_TIMEOUT = 5` (`provider.py:878-903`, `loginflow.py:92`); live gemessen: Eintrag unter "Geräte und Sitzungen" verschwindet | closed |
| T-03-64 | DoS | oauth/throttle.py | mitigate | 429 mit `Retry-After` (`throttle.py:342-359`), `FAILURE_LIMIT = 10`, `WINDOW = 300`; keine Auth-Retries (Quelltext-Gate); kein Nextcloud-Aufruf im Token-Pfad | closed |
| T-03-65 | Info Disclosure | oauth/throttle.py | mitigate | Zähler speichert nur `sha256(path_class \0 source)` (`throttle.py:247`), prozesslokal, `WINDOW = 300`, harte Obergrenze `SOURCE_LIMIT = 4096` (`:254-258`) | closed |
| T-03-66 | Info Disclosure | provider.py, verifier.py | mitigate | RFC-Fehlercodes ohne interne Details; Echo-Test über alle Ablehnungspfade und caplog-Test auf DEBUG (`test_oauth_abuse.py:826,836`) | closed |
| T-03-67 | DoS | oauth/provider.py | mitigate | `HELD_ANSWER_LIMIT = 256` und Lebensdauer gleich `ROTATION_GRACE` (`provider.py:201,762-764`); Verlust führt nur zu `invalid_grant` | closed |

### Plan 03-08: Integrationsbeweis und Dokumentation

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-70 | Info Disclosure | docs/ | mitigate | Gate im Audit selbst nachgezogen: keine 64-stellige Hex-Kette, kein Bearer-Wert, kein Passwort in `docs/oauth-setup.md`, `docs/staging-setup.md`, `docs/client-setup.md` (einziger Treffer ist der Platzhalter `Bearer a-long-random-string`) | closed |
| T-03-71 | Repudiation | docs/oauth-setup.md | mitigate | Evidence-Abschnitt nennt Kommando und Datum (`:4,174,209`); der `invalid_scope`-Fehlschlag von ChatGPT ist als Fehlschlag dokumentiert (03-09-SUMMARY, MEASUREMENTS) | closed |
| T-03-72 | DoS | scripts/bootstrap_exapp.sh | mitigate | Eigener Port 8081, eigener Projektname mit Prüfung (`bootstrap_exapp.sh:77,155`); `compose.test.yml` wird nicht angefasst; Verifier bestätigt: `nc-mcp-test` und `findling-nextcloud` unberührt | closed |
| T-03-73 | Tampering | scripts/oauth_flow_check.py | mitigate | Der Lauf widerruft die erzeugte Verbindung und löscht die eine geschriebene Notiz (`oauth_flow_check.py:624-638,879-880`); Endzustand im SUMMARY | closed |
| T-03-74 | Info Disclosure | scripts/, src/ | mitigate | Der Abkürzungsweg (`sign_in`, `requesttoken`) liegt nur in `scripts/oauth_flow_check.py` mit Kommentar; im Audit per Grep über `src/` bestätigt: keine Login-Automatisierung mit Nutzerpasswort. Das im Audit fehlende automatische Gate wurde direkt danach gebaut (`test_no_module_under_src_automates_a_nextcloud_sign_in`), siehe AR-03-03 | closed |
| T-03-75 | DoS | tests, docs | mitigate | Serie läuft mit ungültigen Bearern statt falschen Passwörtern; Gegenprobe "Anmeldung danach normal" im Verifier reproduziert (`03-VERIFICATION.md`, SC 5) | closed |

### Plan 03-09: Hosted Connectors gegen die öffentliche Instanz

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-03-80 | Info Disclosure | Staging-Instanz | mitigate | Alle drei Teile belegt: Wegwerf-Topologie mit eigenen Testkonten (`compose.staging.yml`, `docs/staging-setup.md`), getrennt von produktiven Daten, und der Widerruf am 2026-08-16 um 09:26 UTC, gefolgt von der Zerstörung der Instanz um 09:28 UTC. Beleg unten | closed |
| T-03-81 | Info Disclosure | 03-09-Artefakte | mitigate | Gate im Audit nachgezogen über `03-09-MEASUREMENTS.md` und `03-09-access-log.txt`: keine 64-stellige Hex-Kette, kein Tokenwert; Query-Strings abgeschnitten, Flow-Token gekürzt | closed |
| T-03-82 | Elevation | Staging-Instanz, docs | mitigate | Die offene Registrierung endete mit der Instanz selbst (09:28 UTC, Beleg unten); der Weg über Allowlist oder DCR-Schalter wurde damit gegenstandslos. Der Dokumentationsteil ist nachgetragen: die Security notes von `docs/oauth-setup.md` verlangen jetzt für jede aus dem Internet erreichbare Instanz ausdrücklich einen der beiden Schalter | closed |
| T-03-83 | Repudiation | REQUIREMENTS.md, 03-09 | mitigate | AUTH-04 nur mit Beleg abgehakt: Request-Ketten, Client-Ids, Redirect-URIs, Zeiten (`03-09-MEASUREMENTS.md`) plus archivierter Access-Log (`03-09-access-log.txt`, Commit `e32a084`); der Teilfehlschlag von ChatGPT ist benannt, Cursor bleibt ausdrücklich offen (BL-04) | closed |
| T-03-84 | DoS | Registry, Staging | mitigate | Beide Teile belegt: unbenutzte Registrierungen verfallen nach 24 Stunden (`store.py:109`, `provider.py:326-333`), und die drei benutzten Verbindungen wurden am 2026-08-16 um 09:26 UTC in Nextcloud widerrufen, nicht nur im Client entfernt. Der Store selbst wurde mit seinem Volume zerstört | closed |
| T-03-85 | Spoofing | docs/oauth-setup.md | mitigate | Die Redirect-URI stammt aus dem echten Registrierungsrequest, nicht aus einer Community-Quelle; Annahme A1 wurde dadurch ersetzt (`docs/oauth-setup.md:158`, 03-09-SUMMARY) | closed |

*Status: open, closed*
*Disposition: mitigate (implementation required), accept (documented risk), transfer (third-party)*

---

## Open Threats (BLOCKER für den Phasenabschluss)

> **Nachtrag vom 2026-08-16, 09:29 UTC: alle drei sind geschlossen.** Der Befund des
> Audits stimmte, der Rückbau war zum Zeitpunkt der Messung wirklich nicht ausgeführt.
> Er wurde unmittelbar danach vollzogen; der Beleg steht im Abschnitt "Teardown der
> Staging-Instanz". Der Befund bleibt hier unverändert stehen, weil ein Audit-Bericht,
> der nachträglich umgeschrieben wird, seinen Zweck verliert.

Alle drei betreffen denselben Sachverhalt: der Rückbau beziehungsweise die Härtung der
öffentlichen Staging-Instanz ist deklariert, aber nicht belegt, und die Instanz läuft zum
Zeitpunkt dieses Audits offen weiter.

| Threat ID | Erwartete Gegenmaßnahme | Befund (gemessen 2026-08-16, 09:17 bis 09:20 UTC) |
|-----------|-------------------------|---------------------------------------------------|
| T-03-80 | "die Verbindung wird nach dem Lauf widerrufen" | Kein Widerrufsnachweis in `03-09-SUMMARY.md`, `03-09-MEASUREMENTS.md` oder `docs/oauth-setup.md`. `03-09-access-log.txt` behauptet "The instance was deleted right after this file was written"; die Instanz beantwortet PRM, AS-Dokument und `/mcp` weiterhin |
| T-03-82 | "Allowlist-Modus einschalten oder DCR abschalten" plus Empfehlung in den Security notes | `registration_endpoint` steht im live abgerufenen AS-Dokument (DCR an). `GET /authorize?client_id=audit-probe-does-not-exist` antwortet `400` mit E3 ("This link has expired"), nicht `403`/E1 und nicht E2, also Allowlist aus und DCR an (`consent.py:243-248`). In `docs/oauth-setup.md` "Security notes for production" steht keine Empfehlung für öffentlich erreichbare Instanzen |
| T-03-84 | "nach dem Lauf werden die erzeugten Verbindungen widerrufen" | Kein Nachweis. Die 24-Stunden-Frist greift nur für **unbenutzte** Registrierungen; die beiden Connector-Registrierungen wurden benutzt und fallen unter `IDLE_CLIENT_TTL` (90 Tage) |

**Was sie schließt, in dieser Reihenfolge und noch heute:**

1. Teardown nach `docs/staging-setup.md` Abschnitt 6, alle vier Schritte (Verbindungen in
   Claude.ai und ChatGPT trennen **und** in Nextcloud widerrufen, `docker compose ... down -v`,
   VM löschen, DNS-Eintrag entfernen). Das schließt T-03-80, T-03-82 und T-03-84 in einem Zug.
2. Solange die Instanz noch steht: `NC_MCP_OAUTH_ALLOWLIST_ONLY=1` setzen oder
   `NC_MCP_OAUTH_DCR=0`, damit die offene Registrierung nicht ungedeckt weiterläuft.
3. Ein Zweizeiler mit Datum und Uhrzeit als Beleg, angehängt an `03-09-MEASUREMENTS.md`
   oder an diese Datei, sowie die Korrektur des Satzes in `03-09-access-log.txt`, der den
   Rückbau bereits behauptet.
4. Für den Dokumentationsteil von T-03-82: ein Satz in "Security notes for production", der
   für eine aus dem Internet erreichbare Instanz den Allowlist-Modus empfiehlt oder DCR
   abzuschalten verlangt.

Einordnung der Schwere, damit die Zahl nicht größer gelesen wird als sie ist: die Instanz
trägt nur Wegwerf-Testkonten, und die offene Registrierung allein gibt niemandem Daten.
Eine Autorisierung braucht zusätzlich ein Nextcloud-Konto dieser Instanz, weil
`/authorize/decide` seit CR-01 die von HaRP aufgelöste Identität mit `authorization.nc_user`
vergleicht. Was offen steht, ist anonymes Anlegen von Registrierungen und Login-Flows,
gedrosselt auf 20 je Quelle und fünf Minuten.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-08 | Kein Rate-Limit auf den drei PUBLIC-Discovery-Routen; die Antworten sind statisch, klein und ohne Datenbankzugriff, die Auth-Pfade sind gedrosselt | Owner (Plan 03-01) | 2026-08-16 |
| AR-03-02 | T-03-48 | Ein Nextcloud-Roundtrip je Autorisierungsantrag; er liegt ausschließlich im Browserpfad mit großzügigem Zeitbudget, nie im Token-Pfad, und wird über `CLASS_AUTHORIZE_START` begrenzt | Owner (Plan 03-05) | 2026-08-16 |
| AR-03-03 | T-03-74 | ~~Das deklarierte Grep-Gate über `src/` existiert nicht~~ **ERLEDIGT am 2026-08-16, direkt nach dem Audit.** Der Befund stimmte. Das Gate ist jetzt gebaut: `test_no_module_under_src_automates_a_nextcloud_sign_in` prüft jede Datei unter `src/` gegen `requesttoken` und `/login/v2/grant` und lässt nur die drei Login-Flow-Pfade zu, die das Produkt wirklich kennt. Ohne die Eigenschaft ist der Test rot, gegengeprüft mit einer Probedatei. Der Docstring von `scripts/oauth_flow_check.py` nennt den Test jetzt beim Namen und beschreibt, was er leistet und was nicht | Audit 2026-08-16, geschlossen am selben Tag | 2026-08-16 |
| AR-03-04 | AR-02-04 (Phase 2) | `/mcp` ist seit Plan 03-01 PUBLIC und trägt bewusst keine Drosselung: das anonyme 401 mit `resource_metadata` muss aus der App kommen, und Tool-Aufrufe zu drosseln wäre die eigene Dienstverweigerung. Die Identitätsprüfung liegt dafür in `exapp/middleware.py`. Kosten je anonymem Request: ein HaRP-Lookup. Dokumentiert in `docs/oauth-setup.md`, Security notes | Phase 3 (Plan 03-01), Nachtrag in 02-SECURITY.md | 2026-08-16 |
| AR-03-05 | WR-09 (Review, ohne Threat-Id) | ~~Ein fehlendes `NC_MCP_PUBLIC_URL` degradiert im ExApp-Modus still auf `http://127.0.0.1:8765`~~ **ERLEDIGT am 2026-08-16.** `entry_exapp.main` schlägt jetzt auch für diesen Wert fehl, mit derselben Meldung und demselben Exit-Code wie für Volume und Issuer, und ein leerer Wert zählt als fehlend. Zwei Wächter, beide ohne den Fix rot (der zweite prüft die Logmeldung, weil der Exit-Code allein von einer späteren Prüfung stammen könnte) | geschlossen nach dem Audit | 2026-08-16 |
| AR-03-06 | WR-08 (Review), berührt T-03-24 | Die Ablehnungsseiten E1 und E2 geben bis zu 80 Zeichen eines vom Angreifer gewählten `client_id` als Fließtext wieder (escaped und gesäubert, keine Markup-Injektion). Erreichbar nur mit `allowlist_only=on` oder `dcr=off`. Für die Store-Einreichung vor Phase 5 prüfen | Owner (Review offen gelassen) | 2026-08-16 |
| AR-03-07 | WR-10 (Review) | `_client_information` nimmt einen `client_id` entgegen, den es nie vergleicht; heute nicht ausnutzbar, weil das SDK die Id vergibt und `register_client` Schlüssel und JSON aus einem Objekt schreibt. Latent | Owner (Review offen gelassen) | 2026-08-16 |
| AR-03-08 | WR-12 (Review), berührt T-03-35 | `POST /connect` trägt kein Anti-Fälschungs-Merkmal: eine fremde Seite kann einen Besucher einen Login-Flow anlegen lassen. Kein Credential-Leck, nur erzwungene Zustandserzeugung, seit CR-02 auf 20 je Quelle und fünf Minuten begrenzt | Owner (Review offen gelassen) | 2026-08-16 |
| AR-03-09 | IN-01 bis IN-06 (Review) | Sechs Info-Feststellungen: unerreichbare Cancel-Aktion, `_has_expired` ignoriert die injizierte Uhr, ~~`revocation_endpoint_auth_methods_supported` führt `none` nicht~~ (**IN-03 erledigt am 2026-08-16**: das Feld führt jetzt `none`, mit Wächter, der ohne den Fix rot ist; ein Public Client wurde vorher darüber belehrt, dass er seine eigene Verbindung nicht beenden kann), zwei Definitionen eines sicheren Client-Namens, Handoff-Link ohne die Hostprüfung der Consent-Seite, ein Kommentar der `compare_digest` überhöht. Keine der verbliebenen fünf liegt auf einem Verbindungspfad | Owner (Review offen gelassen), IN-03 geschlossen | 2026-08-16 |
| AR-03-10 | C-01 (Verifier), berührt T-03-83 | AUTH-04 ist ein Protokoll, kein Test: nach dem Teardown reproduziert es niemand mehr. Der Access-Log-Auszug ist seit `e32a084` archiviert, HAR und Screenshots gibt es nicht. Für die Client-Matrix in Phase 5 ist das der Beweisstand | Owner, Verifier-Concern C-01 | 2026-08-16 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Aus den Abschnitten `## Threat Flags` der neun SUMMARYs.

| Flag | Quelle | Mapping | Bewertung |
|------|--------|---------|-----------|
| `new-public-route`: `/connect`, `/connect/wait` | 03-04-SUMMARY | T-03-30 bis T-03-37 | informativ, zugeordnet |
| `new-public-route`: `/authorize`, `/authorize/consent`, `/token`, `/register`, `/revoke` | 03-05-SUMMARY | T-03-40 bis T-03-48 | informativ, zugeordnet |
| `attacker-controlled-render`: Sign-in-Adresse erreicht die Consent-Seite über den Browser | 03-05-SUMMARY | keine Threat-Id | **unregistered_flag** (WARNING). Inzwischen durch WR-07 gehärtet: `_sign_in_link` prüft Host **und** Pfad gegen `_LOGIN_PATH_MARKER = "/login/v2/flow"` (`consent.py:123,447-469`). Der Gegenpart auf dem Onboarding-Pfad fehlt weiterhin (IN-05, AR-03-09) |
| kein `## Threat Flags`-Abschnitt | 03-01, 03-03, 03-09-SUMMARY | entfällt | **Prozesslücke** (WARNING). Gerade 03-01 öffnet die größte neue Angriffsfläche der Phase (drei Well-known-Routen plus `/mcp` auf PUBLIC) und meldet sie nicht als Flag. Die Fläche ist im threat_model des Plans erfasst und in diesem Audit geprüft; die Meldung fehlt trotzdem. Für Phase 4 den Abschnitt in jedem SUMMARY verlangen |
| "None" gemeldet | 03-02, 03-06, 03-07, 03-08-SUMMARY | entfällt | geprüft und plausibel: 03-06 und 03-07 ändern `appinfo/info.xml` nicht, 03-08 fügt nur einen `environment-variables`-Block hinzu |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-16 | 70 | 67 | 3 | gsd-security-auditor (opus), State B, ASVS 1, `block_on: high`. Belege: Quelltext bei `e32a084`, eigene Läufe von 14 OAuth-Unit-Dateien (alle grün), Doku-Gates gegen Hex64/Bearer/Passwort selbst nachgezogen, vier lesende Live-Messungen gegen `https://nc-staging.infranode.dev` |

Anmerkungen aus dem Audit:

- **Was dieses Audit nicht getan hat:** keine Suche nach neuen Schwachstellen. Grundlage
  sind die 70 Zeilen der neun threat_model-Blöcke, jede einzeln gegen den Quelltext
  gehalten. Feststellungen aus `03-REVIEW.md` und `03-VERIFICATION.md` erscheinen hier nur,
  wo sie eine deklarierte Gegenmaßnahme berühren.
- **Drei Positionen wurden nicht über ihre Threat-Id gefunden, sondern über ihren Inhalt:**
  T-03-05, T-03-52, T-03-53, T-03-64 und die Positionen der Pläne 03-08 und 03-09 tragen im
  Quelltext keine Id. Sie sind trotzdem geprüft, jeweils an der in der Zeile genannten
  Stelle.
- **CR-01 ist der Kern dieser Phase und ist geschlossen:** der Identitätsvergleich mit
  `secrets.compare_digest` gegen `authorization.nc_user` liegt auf einer bewusst PUBLIC
  deklarierten Route, weil `access_level USER` HaRPs Blacklist bei regulären Abweisungen
  auslöst und die ganze App für fünf Minuten unerreichbar macht (gemessen, 03-REVIEW.md).
  Das Manifest-Gate hat dafür eine Gegenprobe, die eine `USER`-Entscheidungsroute wieder
  durchfallen lässt.
- **AR-02-06 aus Phase 2 ist in dieser Phase erledigt** und in `02-SECURITY.md` nachgetragen
  (Commit `e32a084`), ebenso der Nachtrag zu AR-02-04. Verifier-Concern C-03 ist damit
  ausgeräumt.
- **AUTH-04 hat seit `e32a084` ein Artefakt:** `03-09-access-log.txt`, 103 Zeilen, gekürzt
  und ohne Credentials (im Audit geprüft). Concern C-01 des Verifiers bleibt insoweit
  bestehen, als es weder HAR noch Screenshot gibt (AR-03-10).

---

## Teardown der Staging-Instanz (Beleg für T-03-80, T-03-82, T-03-84)

Ausgeführt am **2026-08-16** nach `docs/staging-setup.md` Abschnitt 6, alle vier Schritte,
unmittelbar nach dem Audit. Zeiten in UTC, gemessen auf der Instanz beziehungsweise am
Client.

| Zeit | Schritt | Beleg |
|------|---------|-------|
| 09:25:12 | Ausgangszustand aufgenommen | drei Einträge unter Devices and sessions von alice (`MCP Connector: Claude` zweimal, `MCP Connector: ChatGPT`), im OAuth-Store 1 Client, 1 Autorisierung, 1 Access- und 1 Refresh-Token |
| 09:25:49 | Connector in Claude.ai entfernt | Liste danach ohne Eintrag |
| 09:26:33 | Plugin in ChatGPT gelöscht | Liste danach ohne Eintrag |
| 09:26:50 | **Widerruf in Nextcloud**, der Schritt, den das Entfernen im Client nicht leistet | `occ user:auth-tokens:delete alice {4,12,18}`, danach null Einträge mit `MCP Connector` |
| 09:27:05 | Topologie mit Daten zerstört | `docker compose --env-file .env.staging -f compose.staging.yml down -v`, alle vier Volumes entfernt, darunter der Zertifikatsspeicher |
| 09:27:17 | ExApp-Container und Token-Store entfernt | `docker rm -f nc_app_mcp_connector`, `docker volume rm nc_app_mcp_connector_data`; danach 0 Container, 0 Volumes; `/mcp` von außen ohne Antwort |
| 09:28:25 | Virtuelle Maschine gelöscht | Hetzner, Server 162335572 `nc-staging`, beide primären IP-Adressen mitgelöscht statt reserviert |
| 09:28:47 | DNS-Eintrag gelöscht | Cloudflare-API, A-Record `nc-staging.infranode.dev`, danach null Records für den Namen |
| 09:29 | Gegenprobe | Namensauflösung leer, HTTPS ohne Route, SSH auf 178.104.71.131 im Timeout. Die beiden InfraNode-Boxen laufen unverändert weiter, `https://infranode.dev/` antwortet 200 |

Die zwei Geheimnisdateien der Instanz (`.env.staging`, `.env.staging.app`) haben die
Maschine nie verlassen und sind mit ihr verschwunden. Der archivierte Access-Log-Auszug
`03-09-access-log.txt` ist das, was von der Instanz bleibt, und er enthält keine
Zugangsdaten.

Damit ist auch die Frage beantwortet, die `docs/staging-setup.md` an den Teardown geknüpft
hat: der Widerruf muss in Nextcloud geschehen. Das Entfernen des Connectors in Claude.ai
allein lässt die Autorisierung am Leben, gemessen in Lauf 3 des Plans 03-09.

---

## Sign-Off

- [x] Alle 70 Positionen tragen eine Disposition (68 mitigate, 2 accept, 0 transfer)
- [x] Jede Position wurde nach ihrer Disposition geprüft, keine übersprungen
- [x] Akzeptierte Restrisiken mit Id, Begründung, Owner und Datum eingetragen (AR-03-01 bis AR-03-10)
- [x] `threats_open: 0` erreicht, nach dem belegten Teardown vom 2026-08-16
- [x] `status: verified` gesetzt

**Freigabe:** erteilt. Die drei zunächst offenen Positionen betrafen ausschließlich den
Rückbau der öffentlichen Staging-Instanz und sind durch den Teardown geschlossen, nicht
durch eine Umdeutung. Im Audit selbst wurde keine Implementierungsdatei geändert; die
danach nachgetragene Empfehlung in `docs/oauth-setup.md` und das Gate zu AR-03-03 sind
gesondert committet.
