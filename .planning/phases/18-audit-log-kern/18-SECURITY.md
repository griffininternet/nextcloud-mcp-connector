---
phase: 18
slug: audit-log-kern
status: verified
threats_open: 0
threats_total: 26
threats_closed: 21
threats_accepted: 5
asvs_level: 2
block_on: critical
created: 2026-08-31
reverified_after: [3376f63, fef59ff, a38d250]
---

# Phase 18: Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Audit-Trail.
> Grundlage sind die zehn `<threat_model>`-Bloecke der Plaene 18-01 bis 18-10 und die
> `## Threat Flags` der zehn SUMMARYs. Belegt wird ausschliesslich am Code, nicht an Absicht.

---

## Trust Boundaries

| Boundary | Beschreibung | Data Crossing |
|----------|--------------|---------------|
| Werkzeugaufruf zu Erfassung | `params["arguments"]` ist Eingabe von aussen, Schluessel wie Werte | Parameternamen (nie Werte), Werkzeugname |
| Werkzeugausnahme zu Ablage | `message` und `hint` tragen Pfade und Namen | nur `reason` aus sechs eingefrorenen Kennungen |
| Transportgrenze zu Werkzeugpfad | Identitaet wird einmal je Anfrage aufgeloest, danach nur gelesen | `nc_user`, `client_id`, `auth_id`, `client_name` |
| Client zu Protokoll | `client_name` kommt aus der dynamischen Registrierung | geklammerter, gekuerzter Name |
| Dateisystem zu Ablage | Wer das Volume schreibt, aendert Zeilen an der Ablage vorbei | Hash-Kette macht es sichtbar, verhindert es nicht |
| Ablage zu OAuth-Speicher | zwei Dateien, zwei Verbindungen, ein Volume | Obergrenze `used_bytes` schuetzt den Nachbarn |
| Nextcloud-Admin-Wert zu ExApp | Schalterwert kommt ueber OCS und ist Eingabe | `audit_log` (Checkbox, ohne `sensitive`) |
| Nextcloud-Kontoliste zu Loeschentscheid | unvollstaendige Liste wuerde eine ganze Kette loeschen | Liste von uids, fail-safe in Richtung Behalten |
| Internet zu occ-Pfad | PHP-Proxy haengt selbst gueltige AppAPI-Kopfzeilen an | Doppelpruefung `x-origin-ip` (404) + `require_appapi` (401) |
| Ablage zu Ausgabe | Ketten- und Kontonamen sind von aussen bestimmt | geklammerte Kennung, `--json` als Maschinenpfad |
| Administrator zu Daten | wer das Volume loescht, loescht das Log | Handlung, kein Angriff (D-18) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (Belegstelle im Code) | Status |
|-----------|----------|-----------|-------------|----------------------------------|--------|
| T-18-01 | Information Disclosure | `audit/store.py`, `audit/record.py`, `audit/allowlist.py`, `errors.py` | mitigate | Spalte `params` nimmt nur eine sortierte Namensliste: `store.py:246`, `store.py:543`. Nur gesetzte Schluessel, geschnitten mit der Erlaubnisliste: `record.py:97-103`. Nur `reason` aus der eingefrorenen Menge: `record.py:161-170`, `errors.py:25-34`. Nutzlastnamen auf der Sperrliste: `allowlist.py:22-32`. Kein Pfad liest `values()`. Faelle: `tests/unit/test_audit_record.py:200`, `tests/unit/test_audit_store.py:327`, `tests/unit/test_exapp_audit_verify.py:556` | CLOSED |
| T-18-02 | Tampering | `PARAM_ALLOWLIST` | mitigate | Der Rekorder schneidet die gesetzten Schluessel mit der Liste des Werkzeugs: `record.py:103` (`set(arguments.keys()) & PARAM_ALLOWLIST.get(tool, frozenset())`). Erfundener Schluesselname als eigener Fall: `tests/unit/test_audit_record.py:184` | CLOSED |
| T-18-03 | Tampering | Tabelle `entries` | mitigate | SHA-256 ueber `CANONICAL_FIELDS` plus `prev_hash`, `seq` als erstes Feld eingeschlossen: `store.py:268-286`, `store.py:601-614`. Pruefung trennt Inhalt und Verkettung und nennt die erste Stelle: `store.py:797-834`, `store.py:1006-1031`. Faelle an der Ablage vorbei: `tests/unit/test_audit_store.py:353,366,380,407`, `tests/unit/test_exapp_audit_verify.py:241,254,268 | CLOSED |
| T-18-04 | Repudiation | `entries`, Grabsteine | accept | Grenze ausgeschrieben im Modul-Docstring `store.py:26-30`, im Docstring von `verify_chains` `store.py:1013-1019` und als letzte Zeile **jeder** Antwort des Pruefkommandos: `exapp/audit_verify.py:117-121`, gesetzt in `audit_verify.py:204` und `audit_verify.py:273`. Siehe Accepted Risks Log R-18-01 | CLOSED (accepted) |
| T-18-05 | Denial of Service | Volume, `oauth.sqlite3` | mitigate | `auto_vacuum = INCREMENTAL` als erste Anweisung, vor `journal_mode`: `store.py:1129-1130`. `used_bytes` als einzige Messgroesse: `store.py:572-585`. Stapel von 5000: `store.py:116`, `store.py:654,690`. `incremental_vacuum` plus `wal_checkpoint(TRUNCATE)`: `store.py:772-781`. Rundengrenze: `store.py:124`, `store.py:686`. Aufraeumlauf beim Start auch bei abgeschaltetem Log: `entry_exapp.py:327-332`. Faelle: `tests/unit/test_audit_store.py:479` (Bound stoppt vor leerer Tabelle), `:716` (OAuth-Speicher bleibt nach dem Bound schreibbar und rotiert) | CLOSED |
| T-18-06 | Repudiation | `resolve_caller`, `note()` | mitigate | Fehlender Zwischenschritt ergibt `None` statt einer Ausnahme, an jedem Schritt defensiv: `deps.py:134-175`. Kein Aufrufer wird durch die Erfassung beendet: `record.py:222-229`. Die Luecke macht das Pruefkommando sichtbar: `audit_verify.py:150-176` | CLOSED |
| T-18-07 | Elevation of Privilege | `AUDIT_VERIFY_PATH` | mitigate | Keine `<url>` im Manifest (Pfad steht nur als bewusst abwesender im Kommentar `appinfo/info.xml:282-286`; die `<url>`-Liste `:416-488` enthaelt ihn nicht). Doppelpruefung: `x-origin-ip` -> 404, danach `require_appapi` -> 401, ohne Auskunft welche Pruefung ablehnte: `audit_verify.py:299-312`. Faelle: `tests/unit/test_exapp_audit_verify.py:148,162,174,186,203` | CLOSED |
| T-18-08 | Tampering | `client_name`, Kommandoausgabe | mitigate | Klammerung unmittelbar vor dem Schreiben, ohne Import aus `exapp/ui`: `record.py:106-120`, zweite Stufe in der Ablage selbst `store.py:506-520`, angewendet in `store.py:539`. Klammerung vor der occ-Ausgabe: `audit_verify.py:277-296`, angewendet in `:234` und `:265`. Faelle: `tests/unit/test_audit_record.py:319`, `tests/unit/test_exapp_audit_verify.py:531` (Zeilenzahl). Restrisiko siehe R-18-06 | CLOSED |
| T-18-09 | Denial of Service | `drop_user_chain`, `existing_users` | mitigate | Fail-safe in Loeschrichtung: `None` bei Netzfehler, bei jedem Status ausser 200, bei nicht lesbarem Rumpf **und bei leerer Liste** (`accounts.py:68-91`, `accounts.py:105-147`); der Aufrufer loescht bei `None` nichts (`record.py:190-199`). Schwelle 30 Tage: `store.py:111`, `store.py:912-937`. A1 als eigener Integrationstest: `tests/integration/test_appapi_users_list.py:177-230`. Einheitstests: `tests/unit/test_audit_accounts.py:228-281,395-429` | CLOSED |
| T-18-10 | Information Disclosure | Nextcloud-Log | mitigate | Nur `type(exc).__name__`, nie Meldung oder Pfad: `record.py:261-263`, `accounts.py:129,133,139,146` (nur Status oder Typ, keine Kopfzeile), `entry_exapp.py:345-349`, `audit_verify.py:161-166`. Faelle: `tests/unit/test_audit_record.py:279-301` (`caplog`, kein Pfad), `tests/unit/test_audit_accounts.py:287`, `tests/unit/test_exapp_audit_verify.py:479,506` | CLOSED |
| T-18-11 | Compliance und Mitbestimmung | Schalter `audit_log` | mitigate | Vorgabe im Code ist aus, als positive Zugehoerigkeitspruefung (Tippfehler bleibt aus): `config.py:384-418`. Formularfeld mit `"default": False`: `exapp/admin_settings.py:177-189`. Ohne Schalter kein Rekorder: `entry_exapp.py:127-135`; ohne Schalter und ohne bestehende Datei wird keine Datei angelegt: `entry_exapp.py:312-316`. Der 401 des ersten Starts ergibt ein leeres Overlay und faellt in dieselbe Richtung: `config.py:396-399` | CLOSED |
| T-18-12 | Information Disclosure | `audit/store.py`, `deps.Caller` | mitigate | `Caller` traegt vier Felder und kein Geheimnis: `deps.py:107-132`. Der Erfassungspfad ruft `resolve_credentials` nicht auf (nur `deps.resolve_caller`, `record.py:227`; grep ueber `audit/` findet keinen Aufruf). Kein `crypto`-Import in `audit/` (nur eine Erwaehnung im Docstring `store.py:13`), daher ueberlebt das Log `crypto.delete_key`: `tests/unit/test_exapp_purge.py:848-860` | CLOSED |
| T-18-13 | Spoofing | `params["_meta"]` | mitigate | Die selbstdeklarierte Client-Auskunft wird nicht gelesen: `"_meta"` kommt in `src/` nur als Begruendung im Docstring vor (`deps.py:146-149`). Werkzeugname aus `params["name"]`: `record.py:146-158`. Identitaet allein aus `request.state`: `deps.py:154-161`, `audit/__init__.py:48` | CLOSED |
| T-18-14 | Tampering | Contract-Test-Gate | mitigate | Der Gate registriert nichts am Modulsingleton `mcp`; der Gegenbeweis ist eine nie registrierte Funktion: `tests/contract/test_audit_surface.py:118-125`, geprueft in `:128-149`. `tests/contract/test_tool_surface.py` seit `9d9be78` unveraendert (leerer `git diff`) | CLOSED |
| T-18-15 | Tampering | ~223 unberuehrte Wurfstellen | accept | Vorgabe `reason=REASON_UNSPECIFIED` mit ausgeschriebener Begruendung: `errors.py:40-48`; Kennungsmenge eingefroren und per AST-Lauf gehalten: `errors.py:22-34`, `tests/unit/test_errors_reason.py` (gruen). Siehe R-18-02 | CLOSED (accepted) |
| T-18-16 | Denial of Service | Sweep und Kontopruefung im Schreibpfad | accept | Zeitplan haengt allein an der zurueckgegebenen Sequenznummer: `store.py:475-492` (jeder 500., Kontopruefung jeder 20. Sweep), aufgerufen in `record.py:248-260`. Belegt statt nur behauptet: `tests/unit/test_audit_accounts.py:450-465` (`route.call_count == 0` beim gewoehnlichen Aufraeumlauf). Siehe R-18-03 | CLOSED (accepted) |
| T-18-17 | Denial of Service | `finally`-Zweig in `graceful` | mitigate | `note()` fasst alles nach dem Rekorderfund in ein `except Exception` und protokolliert nur den Typ: `record.py:225-263`. Der `finally`-Zweig wartet den Schreibvorgang ab statt ihn abzuloesen: `server/__init__.py:132-133`. Doppelgaenger, der immer wirft, als Fall: `tests/unit/test_audit_record.py:279-301`. Restrisiko siehe R-18-07 | CLOSED |
| T-18-18 | Repudiation | Schaltung des Logs | mitigate | Jeder Zustandswechsel schreibt eine Zeile in die Instanzkette: `entry_exapp.py:319-326`. `actor` ist `unknown` mit Quelle im Docstring (AppAPI `SetValueListener`, app_api v34.0.3): `record.py:266-287`, `store.py:148-152`. Der Schalterwert wird in `outcome` geschrieben und dort wieder gelesen: `record.py:285`, `entry_exapp.py:323` | CLOSED |
| T-18-19 | Tampering | Admin-Formularfeld | mitigate | Kein `sensitive` in irgendeiner Schreibweise am Feld: `exapp/admin_settings.py:177-189`; geprueft ueber `json.dumps(...).lower()` in `tests/unit/test_exapp_admin_settings.py:310` und ueber den ganzen Formularrumpf in `:170-180`. Feldkennungen und Lesepfad gleichgesetzt: `tests/unit/test_exapp_admin_settings.py:141` gegen `exapp/config_values.py:114-144` | CLOSED |
| T-18-20 | Repudiation | Statuswahl des Handlers | mitigate | Immer 200, Urteil im Rumpf: `audit_verify.py:400-406` (Vorgabe 200, mit Messung von `ExAppOccService::buildCommand` im Modul-Docstring `:25-33`), JSON-Weg ueber `exapp/responses.py:52-54`. Auch der Fehlerfall antwortet 200: `audit_verify.py:161-166`. Faelle ueber alle Ausgaenge: `tests/unit/test_exapp_audit_verify.py:375,388,479,506` | CLOSED |
| T-18-21 | Repudiation | geloeschte Nutzerkette | mitigate | Genau ein Grabstein je gefallener Kette in der Instanzkette, mit `gap_chain`, `gap_hash` und `removed`, im selben `BEGIN IMMEDIATE` wie die Loeschung: `store.py:961-987`. Kein Grabstein fuer eine Kette, die es nicht gab: `store.py:963-966`. Faelle: `tests/unit/test_audit_accounts.py:345,366,378` (danach schweigt `verify_chains()`) | CLOSED |
| T-18-22 | Repudiation | Ueberleben beim Purge | mitigate | Vier Faelle halten die Behauptung: `tests/unit/test_exapp_purge.py:800,814,832,848`. `src/mcp_connector/exapp/purge.py` seit `9d9be78` unveraendert (leerer `git diff --stat`) | CLOSED |
| T-18-23 | Repudiation | `--rm-data` entfernt das Volume mit dem Log | accept | Grenze wortwoertlich und ohne Beschoenigung festgehalten: `.planning/phases/18-audit-log-kern/18-10-SUMMARY.md:217-235` mit vier Zeilenverweisen auf `docs/uninstall.md` (`:19`, `:47`, `:48`, `:229-235`). Siehe R-18-04, inklusive der offenen Nutzerdokumentation | CLOSED (accepted) |
| T-18-24 | Tampering | Werkzeugflaeche und Gate-Grenzwerte | mitigate | Budget-Stillstand in diesem Audit nachgemessen: `scripts/check_tool_budget.py` antwortet `15712 bytes, 21 tools, budget 18000`, identisch zur Zahl in `18-10-SUMMARY.md:63`. `scripts/check_tool_budget.py` und `tests/contract/test_tool_surface.py` seit `9d9be78` unveraendert (leerer `git diff --stat`) | CLOSED |
| T-18-25 | Repudiation | Trennen, Pausieren, Entfernen ueber die Oberflaeche | accept | Herleitung per grep plus `18-RESEARCH.md` §11, in der Nachweistabelle ausdruecklich als hergeleitet und nicht getestet ausgewiesen: `18-VERIFICATION.md:26` (Zeile 5b) und `:93`. Siehe R-18-05 | CLOSED (accepted) |
| T-18-SC | Tampering (Supply Chain) | `pyproject.toml`, `uv.lock` | mitigate | `git diff --stat 9d9be78 HEAD -- pyproject.toml uv.lock` ist leer; die Phase hat kein Paket installiert. Alle zehn SUMMARYs fuehren denselben Beleg | CLOSED |

*Status: open · closed*
*Disposition: mitigate (Umsetzung erforderlich) · accept (dokumentiertes Risiko) · transfer (Dritte)*

**Zaehlung:** 26 Bedrohungen, 21 `mitigate` CLOSED, 5 `accept` CLOSED via Accepted Risks Log, 0 OPEN.
Es gibt in diesem Register keine Bedrohung mit Disposition `transfer`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-18-01 | T-18-04 | Jeder Teil des Beweises liegt in derselben Datei: kein externer Anker, keine Signatur ausserhalb des Volumes. Wer die Datei schreiben kann, rechnet die Kette neu; ein gefaelschter Grabstein ist von einem echten nicht zu unterscheiden. Die Grenze steht nicht nur im Docstring, sondern als letzte Zeile jeder Antwort des Pruefkommandos, damit sie derjenige liest, der ein gruenes Ergebnis beurteilen muss (D-v1.5-02) | Owner (Plan 18-01/18-04/18-08, Entscheid D-v1.5-02) | 2026-08-31 |
| R-18-02 | T-18-15 | Rund 223 unberuehrte `raise`-Stellen tragen `unspecified`. Ein flaechendeckender Umbau der Fehlerbehandlung waere ein anderer Auftrag; `unspecified` ist honest und nicht geraten, und die Kennungsmenge ist per AST-Lauf auf sechs Werte eingefroren (D-17) | Owner (Plan 18-03, Entscheid D-17) | 2026-08-31 |
| R-18-03 | T-18-16 | Jeder 500. Aufruf traegt die Aufraeumkosten, jeder 20. Aufraeumlauf zusaetzlich einen Nextcloud-Aufruf. Bewusst getragen: die Alternative waere ein Dienst oder ein Cron, der auf einer Instanz ohne occ-Lauf nicht laeuft und einen Neustart nicht ueberlebt (D-11, D-12, D-20) | Owner (Plan 18-04/18-09, Entscheide D-11, D-12) | 2026-08-31 |
| R-18-04 | T-18-23 | `occ app_api:app:unregister mcp_connector --rm-data` entfernt das Volume und mit ihm die Log-Datei, weil sie nach D-01 daneben liegt; dasselbe gilt fuer "Delete data on remove" auf Nextcloud 32/33. Das ausdrueckliche Loeschen der Daten durch den Administrator ist kein Fall, gegen den diese Phase schuetzt. **Restpunkt:** `docs/uninstall.md` nennt das Audit-Log bisher nicht namentlich (grep `-i audit` ohne Treffer); der Textnachzug ist AUDIT-06 in Phase 19. Bis dahin steht die Grenze nur im Phasenartefakt, nicht in der Administratordokumentation | Owner (Plan 18-10, Entscheid D-18) | 2026-08-31 |
| R-18-05 | T-18-25 | Trennen, Pausieren und Entfernen ueber die Oberflaeche sind nicht getestet, sondern per grep ueber die drei Aufraeumpfade plus `18-RESEARCH.md` §11 hergeleitet. Die Nachweistabelle weist Zeile 5b ausdruecklich als hergeleitet aus, damit Phase 19 sie nicht als geprueft weiterschreibt | Owner (Plan 18-10) + Verifikation `18-VERIFICATION.md:26,93` | 2026-08-31 |
| R-18-06 | T-18-08 (Restrisiko) | Drei getrennte Reiniger fuer Namen von aussen (Review IN-02, nicht behoben): `record._clamped_client_name` filtert mit `str.isprintable()`, `store._clean_client_name` und `audit_verify._printable` nur C0 und DEL. Format-Zeichen wie U+202E koennen daher innerhalb einer Ausgabezeile die Leserichtung drehen. Die zugesagte Eigenschaft bleibt erfuellt: keine Zeile kann vorgetaeuscht werden (`tests/unit/test_exapp_audit_verify.py:531`), und `audit_verify.py:285-291` benennt die Grenze samt `--json` als Maschinenpfad | Auditor, offen zur Uebernahme durch Owner | 2026-08-31 |
| R-18-07 | T-18-17 (Restrisiko) | `note()` faengt `Exception`, nicht `BaseException` (Review IN-05, nicht behoben): eine `asyncio.CancelledError` waehrend des Schreibens kann aus dem `finally` von `graceful` entkommen und eine laufende Werkzeugausnahme ersetzen. Standard-asyncio-Semantik, geringe Wirkung; die zugesagte Massnahme (`note` faengt `Exception` selbst) ist vorhanden, die Docstring-Zusage "never raises" ist um diesen einen Fall weiter als der Code | Auditor, offen zur Uebernahme durch Owner | 2026-08-31 |
| R-18-08 | T-18-07/T-18-10 (Restrisiko) | `audit_verify._payload` prueft `announced.isdigit()` ohne `isascii()` (Review IN-03, nicht behoben): eine Unicode-Ziffer in `content-length` laesst `int()` werfen und wird zu einer 500. Nur fuer einen bereits authentifizierten AppAPI-Aufrufer erreichbar, konforme HTTP-Stacks weisen den Header vorher ab; die Antwort traegt weiterhin keinen Pfad und keine Meldung (`audit_verify.py:161-166`) | Auditor, offen zur Uebernahme durch Owner | 2026-08-31 |

*Akzeptierte Risiken tauchen in kuenftigen Audit-Laeufen nicht wieder als offen auf.*

---

## Threat Flags aus den SUMMARYs

| SUMMARY | Threat Flags vorhanden | Inhalt | Mapping |
|---------|------------------------|--------|---------|
| 18-01 | ja | keine neue Flaeche, keine Route, kein Netzzugang, keine Berechtigung | informational |
| 18-02 | ja | keine neue Flaeche, `pyproject.toml`/`uv.lock` unveraendert | T-18-SC |
| 18-03 | ja | keine neue Flaeche | T-18-SC |
| 18-04 | ja | T-18-03 und T-18-05 eingeloest, T-18-04 bleibt `accept` | T-18-03, T-18-04, T-18-05 |
| 18-05 | ja | fuenf Faeden eingeloest | T-18-06, T-18-08, T-18-12, T-18-13, T-18-SC |
| 18-06 | ja | sieben `mitigate`-Faeden mit Fundstellentabelle | T-18-01, 02, 06, 08, 10, 13, 17 |
| 18-07 | ja | fuenf `mitigate`-Faeden | T-18-05, 10, 11, 18, 19 |
| 18-08 | ja (Prozessnotiz geprueft, kein Gap) | eine Route, bewusst nicht im Manifest | T-18-03, 07, 08, 10, 20, 04 |
| 18-09 | ja (Prozessnotiz geprueft, kein Gap) | vier `mitigate`-Faeden, eine neue ausgehende Verbindung auf einen AppAPI-Pfad | T-18-09, 10, 16, 21 |
| 18-10 | ja | nur Testdateien, Budget-Stillstand | T-18-05, 22, 23, 24, 25, SC |

### Unregistered Flags

Keine. Jede in den zehn `## Threat Flags` genannte Flaeche bildet auf eine Kennung dieses
Registers ab. Die eine tatsaechlich neue Route (`/audit-verify`) ist als T-18-07 gefuehrt und
steht in keinem `<url>` des Manifests; die eine neue ausgehende Verbindung (AppAPI-Nutzerliste)
ist als T-18-09 und T-18-10 gefuehrt.

**Prozessnotiz (WARNING-Kandidat, ausgeraeumt):** Die Vorpruefung liess offen, ob den SUMMARYs
18-08 und 18-09 der Abschnitt `## Threat Flags` fehlt. Beide haben ihn (18-08 mit Fundstellen-
tabelle zu fuenf Faeden plus dem `accept`-Faden T-18-04, 18-09 mit vier Faeden). Es liegt damit
keine Prozessluecke vor.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-31 | 26 | 26 (21 mitigate + 5 accepted) | 0 | gsd-security-auditor (Claude) |

**Re-Verifikation nach dem Review-Fix-Lauf.** Das Register wurde nicht gegen den Stand der
Planausfuehrung geprueft, sondern gegen den aktuellen Code inklusive der drei Korrekturen
`3376f63` (Sweep nimmt nur zusammenhaengende Kettenpraefixe), `fef59ff` (Marker in derselben
Transaktion wie der Loeschstapel) und `a38d250` (Markerregister beschraenkt,
`over_bound_unevictable` sichtbar). Die drei Aenderungen beruehren T-18-03, T-18-04 und T-18-05
und halten diese weiter:

* T-18-03 bleibt geschlossen: der Digest ist unveraendert (`store.py:601-614`), die
  Praefix-Bedingung `_EXPIRED_PREFIX` (`store.py:339-348`) macht den entnommenen Block je Kette
  zusammenhaengend, damit der vermerkte Endhash immer der Vorgaenger des ueberlebenden Kopfes
  ist. Regressionsfall zur Uhr-Rueckstellung: `tests/unit/test_audit_store.py:446`.
* T-18-04 bleibt `accept` und unveraendert: die Konsolidierung ersetzt nur das Ende der
  Instanzkette innerhalb einer Transaktion (`store.py:704-769`), sie stellt keine Faelschung
  fest und behauptet das auch nicht.
* T-18-05 bleibt geschlossen: die Stapel, die Rundengrenze und `used_bytes` sind unveraendert;
  neu ist, dass der eine Zustand, den kein Sweep aufloest, benannt wird
  (`store.py:447-472`, `audit_verify.py:123-131,208-215`), belegt in
  `tests/unit/test_exapp_audit_verify.py:321,351,362`.
* Zusaetzliche Belege, die es vor dem Fix-Lauf nicht gab: `tests/unit/test_audit_store.py:527`
  (ein Stapel, dessen Marker nicht schreibbar ist, entfernt nichts), `:556` (Absturz zwischen
  zwei Stapeln laesst jeden festgeschriebenen Stapel erklaert), `:601,627,642` (Konsolidierung,
  zwei Ketten, Schalterzeile als Barriere).

**Lauf dieses Audits.** 234 Faelle aus `tests/unit/test_audit_store.py`,
`test_audit_record.py`, `test_audit_caller.py`, `test_audit_accounts.py`,
`test_exapp_audit_verify.py`, `test_exapp_purge.py`, `test_errors_reason.py`,
`test_exapp_admin_settings.py` und `tests/contract/test_audit_surface.py` sind gruen.
`scripts/check_tool_budget.py` antwortet `15712 bytes, 21 tools, budget 18000`.
`git diff --stat 9d9be78 HEAD` ist leer fuer `pyproject.toml`, `uv.lock`,
`src/mcp_connector/exapp/purge.py`, `scripts/check_tool_budget.py` und
`tests/contract/test_tool_surface.py`.

**Nicht Gegenstand dieses Audits.** Es wurde nicht blind nach neuen Schwachstellen gesucht.
Geprueft wurde jede Kennung des Registers nach ihrer Disposition. Keine Implementierungsdatei
wurde geaendert; die drei aus dem Code-Review uebrig gebliebenen Info-Befunde stehen als
R-18-06 bis R-18-08 im Accepted Risks Log statt als Patch im Code.

---

## Sign-Off

- [x] Alle Bedrohungen haben eine Disposition (mitigate / accept / transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (R-18-01 bis R-18-08)
- [x] `threats_open: 0` bestaetigt
- [x] `status: verified` im Frontmatter gesetzt
- [x] Register nach dem Review-Fix-Lauf (3376f63, fef59ff, a38d250) erneut am aktuellen Code geprueft

**Approval:** verified 2026-08-31
