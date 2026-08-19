---
phase: 05-hardening-und-store-einreichung
verified: 2026-08-19T22:15:00Z
status: gaps_found
score: 3/6 must-haves verified (1 uncertain, 2 failed)
overrides_applied: 0
gaps:
  - truth: "Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code (CR-01 aus 05-REVIEW.md)"
    status: failed
    reason: >
      05-REVIEW.md dokumentiert einen Critical Finding (CR-01): ein Admin-Wert
      "http://cloud.example.com/..." (nicht-Loopback, ohne https) besteht die
      Validierung in config_values._public_url, gewinnt per Vorrangregel gegen
      NC_MCP_PUBLIC_URL, und fuehrt beim naechsten Disable/Enable dazu, dass
      build_exapp_app() eine ToolError wirft (SDK verweigert einen
      Nicht-https-Issuer ausser bei Loopback), die in entry_exapp.main mit
      SystemExit(2) beendet wird. Der Container geht in eine Restart-Schleife,
      die App wird nie wieder enabled, das Admin-Formular verschwindet damit
      (AppAPI liefert nur Formulare aktivierter Apps), und der fehlerhafte Wert
      ist ueber die Oberflaeche nicht mehr korrigierbar. Das ist exakt der
      Deadlock, den Plan 05-04 beseitigen sollte, jetzt erreichbar ueber das
      Formular selbst, das Plan 05-01 gebaut hat. Unabhaengig nachvollzogen:
      config_values.py _public_url (Zeilen ~205-234) hat keine
      https-ausser-Loopback-Pruefung; config.normalize_base_url akzeptiert
      http auf jedem Host; entry_exapp.main faengt ToolError aus
      build_exapp_app() weiterhin mit SystemExit(2) ab (Zeilen ~331-338,
      Kommentar bestaetigt das Risiko woertlich). Kein Test deckt
      "http auf Nicht-Loopback-Host" ab (grep nach diesem Testfall in
      tests/unit/test_exapp_config_values.py ergab keinen Treffer). Kein
      Folgeplan (05-11 o.ae.) hat den Fund behoben; git log endet mit dem
      Review-Commit selbst.
    artifacts:
      - path: "src/mcp_connector/exapp/config_values.py"
        issue: "_public_url akzeptiert http:// auf jedem Nicht-Loopback-Host; keine Issuer-taugliche https-Regel"
      - path: "src/mcp_connector/entry_exapp.py"
        issue: "Ein ToolError aus build_exapp_app() (Issuer-Refusal des SDK) fuehrt weiterhin zu SystemExit(2) statt zum Setup-Zustand, den Plan 05-04 fuer die fehlende Adresse bereits eingefuehrt hat"
    missing:
      - "https-Pflicht (mit Loopback-Ausnahme) in config_values._public_url ergaenzen, wie im Review-Fix vorgeschlagen"
      - "entry_exapp.main so aendern, dass ein Issuer-ToolError aus build_exapp_app() den fehlerhaften Admin-Wert verwirft und mit dem Setup-Zustand weiterlaeuft statt SystemExit(2) auszuloesen"
      - "Regressionstest fuer genau diesen Fall (http auf Nicht-Loopback-Host wird verworfen; ein Issuer-Refusal beendet den Prozess nicht)"
  - truth: "Ein in Nextcloud gesetzter Admin-Wert (BL-06: oeffentliche Adresse, DCR-Schalter, Allowlist) wirkt in der Praxis ohne gesetzte Umgebungsvariable"
    status: failed
    reason: >
      05-08-MEASUREMENTS.md und deferred-items.md dokumentieren einen live
      gemessenen 401-Fehler beim Startzeit-Lesevorgang der Admin-Werte auf der
      HaRP-Testtopologie ("Nextcloud answered 401 when the admin values were
      read, the environment stays", bei jedem Containerstart reproduziert).
      Der Lesepfad faellt zwar wie geplant weich aus (die App startet trotzdem
      mit den Deploy-Variablen), aber die Konsequenz ist, dass ein im
      Admin-Formular gesetzter Wert auf dieser Topologie NIE wirkt: exakt das
      Feature, das die Plaene 05-01 und 05-04 liefern sollten (Ein-Klick-
      Installation OHNE Umgebungsvariablen, Admin setzt die Adresse im UI).
      Die Unit-Tests fuer admin_overlay/read_values sind gruen (respx-Mocks),
      aber der End-zu-Ende-Beweis gegen eine echte Instanz schlaegt fehl. Die
      Ursache ist nicht behoben, nur als Vermutung notiert ("zur Startzeit ist
      die App noch nicht enabled"). Kein Folgeplan hat das aufgegriffen.
    artifacts:
      - path: "src/mcp_connector/exapp/config_values.py"
        issue: "read_values() erhaelt live gegen die getestete Topologie 401 von Nextcloud; die Ursache ist nicht ermittelt oder behoben"
      - path: "src/mcp_connector/entry_exapp.py"
        issue: "_resolved_env() liest das Overlay beim Prozessstart; auf der gemessenen Topologie liefert dieser Lesevorgang nie einen Admin-Wert (401)"
    missing:
      - "Ursachenanalyse des 401 (App-Identitaet zur Startzeit noch nicht enabled?) und ein Fix, z. B. ein zweiter Lesevorgang am enabled=1-Hook"
      - "Ein Live-Nachweis, dass ein im Admin-Formular gesetzter Wert nach Disable/Enable tatsaechlich im Discovery-Dokument ankommt (der in 05-04 vorgesehene, aber nie gefahrene Lauf)"
deferred: []
human_verification:
  - test: "MUCGPT gegen eine echte laufende Instanz verproben (Discovery, Werkzeugliste, ein Werkzeugaufruf mit Inhalten des konfigurierten Nextcloud-Kontos)"
    expected: "docs/client-setup.md, Abschnitt MUCGPT, kann seine Luecke ('nicht gegen eine laufende Instanz verprobt') schliessen"
    why_human: "Erfordert Zugang zu einer fremden MUCGPT-Instanz samt Keycloak (Stadt Muenchen, it@M); kein Teil davon liegt in diesem Repository oder ist automatisiert pruefbar"
  - test: "Den Live-Nachweis fuer den 401-Fehler (Admin-Werte wirken nach Disable/Enable) auf einer zweiten, frischen Topologie wiederholen"
    expected: "Klaeren, ob der 401 ein Artefakt der Wegwerf-Testtopologie ist oder jede Store-Installation betrifft"
    why_human: "Erfordert eine zweite laufende Nextcloud/AppAPI-Instanz und manuelle Beobachtung des Containerlogs nach Disable/Enable"
---

# Phase 5: Hardening und Store-Einreichung Verification Report

**Phase Goal:** Die App ist gehärtet, signiert und vor der Nextcloud Conference September 2026 im Nextcloud App Store eingereicht, mit Setup-Doku für alle Ziel-Clients
**Verified:** 2026-08-19T22:15:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | App ist im Nextcloud App Store eingereicht (Zertifikat via CSR-PR, signiertes Release, XSD-valide info.xml, Datenweitergabe-Disclosure, Multi-Arch-Image auf ghcr.io) vor der Conference | VERIFIED | 05-10-SUMMARY.md Live-Nachweis: Store fuehrt `0.1.1` (`appapi_apps.json`), Download-URL 200/29491 Bytes, ghcr-Manifest `application/vnd.oci.image.index.v1+json` mit `linux/amd64`+`linux/arm64`, Signatur akzeptiert (Store-Upload HTTP 201). `appinfo/info.xml` Version/`image-tag` = `0.1.1` unabhaengig gegengeprueft. |
| 2 | Admin installiert per Klick aus dem Store-Paket auf einer sauberen Instanz; Deinstallation räumt alle Daten (inkl. Tokens) auf | VERIFIED (mit Einschraenkung, siehe Gap 1) | 05-08/05-10 Live-Messungen: Ein-Klick-Installation ohne jede Env-Variable startet und bleibt oben (`0 restarts`, vorher bei 0.1.0 `Restarting(2)`); `occ mcp_connector:purge --force` + `occ app_api:app:unregister --rm-data` entfernt Volume, sieben Tabellen, Datenschluessel, Container, Registrierung, App-Passwoerter (401 danach). Aber: ein plausibler Admin-Klick (CR-01) kann denselben Deadlock wieder herstellen, siehe Gap 1. |
| 3 | Permission-Parity-Test besteht; Create-only-Write-Tests und Negative-Credential-Loadtest sind grün | VERIFIED | 05-03-MEASUREMENTS.md: 5/5 Tests live gruen gegen HaRP-Topologie (Leak-Test, Create-only, Positivkontrollen). 05-05-MEASUREMENTS.md: Negativ-Credential-Lasttest live gemessen (Quotient 1,00 Nextcloud-Runden/Angreifer-Request, Kontrolle 0,00, Bruteforce-Reset verifiziert). |
| 4 | Für Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI und MUCGPT existiert je eine Setup-Doku, jeweils gegen den echten Client verprobt | UNCERTAIN (6/7) | 05-07-MEASUREMENTS.md: Open WebUI vollstaendig End-zu-Ende verprobt (Discovery, DCR, Consent im Browser, Token, Refresh, 16 Werkzeuge, Zwei-Konten-Leak-Gegenprobe). Claude.ai/ChatGPT aus Phase 3 (03-09), Cursor ebenfalls verprobt. MUCGPT-Abschnitt selbst sagt woertlich: "nicht gegen eine laufende Instanz verprobt", nur aus Quellcode-Lektuere abgeleitet — kein Zugang zu einer echten Instanz. Transparent dokumentiert, aber die roadmap-woertliche Anforderung "verprobt" ist fuer diesen einen Client nicht erfuellt. |
| 5 | Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code (Review-Gate der "gehärtet"-Zusage) | FAILED | 05-REVIEW.md CR-01, unabhaengig nachvollzogen: `config_values.py` akzeptiert `http://` auf Nicht-Loopback-Hosts als Admin-Wert (kein https/Loopback-Check), `entry_exapp.main` beendet den Prozess weiterhin mit `SystemExit(2)`, wenn `build_exapp_app()` wegen eines ungueltigen Issuers eine `ToolError` wirft. Kein Test deckt diesen Fall ab, kein Folge-Commit behebt ihn (git log endet mit dem Review-Commit `c18bff6`). |
| 6 | Ein in Nextcloud gesetzter Admin-Wert (public_url, DCR, Allowlist) wirkt in der Praxis ohne gesetzte Umgebungsvariable | FAILED | `deferred-items.md` und 05-08-MEASUREMENTS.md: live gemessener 401-Fehler beim Startzeit-Lesevorgang auf der Testtopologie bei jedem Containerstart; Admin-Werte wirken auf dieser Topologie nie. Ursache nur vermutet, nicht behoben, kein Folgeplan behandelt es. |

**Score:** 3/6 Truths voll verifiziert, 1 unsicher (Human-Verify), 2 fehlgeschlagen

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/exapp/admin_settings.py` | Admin-Declarative-Settings-Form mit vier Feldern | VERIFIED | Existiert, getestet (33 Tests laut 05-01-SUMMARY), im Code gegengeprueft (kein `sensitive`, Feld-Ids = `CONFIG_KEYS`) |
| `src/mcp_connector/exapp/config_values.py` | Mehrschluessel-Lesepfad + Overlay mit Vorrangregel | STUB-artig fuer den Praxisfall | Vorhanden und unit-getestet, aber `_public_url` validiert die Issuer-Regel nicht vollstaendig (CR-01) und `read_values` liefert live 401 auf der Testtopologie (Gap 2) |
| `src/mcp_connector/exapp/purge.py` | occ-Purge-Kommando ohne Route, Doppelsicherung | VERIFIED | Existiert, 46 Unit-Tests, live gegen HaRP gemessen (05-08), zwei im Live-Lauf gefundene Fehler (occ-Huelle, configKeys-Form) wurden behoben |
| `docs/uninstall.md` | Runbook mit erzwungener Reihenfolge | VERIFIED | Datei existiert, live Kommandos/Antworten dokumentiert (05-08) |
| `docs/faq.md` | Kanonische FAQ zur Abschalt-Frage | VERIFIED | Datei existiert, gegen Gate getestet (05-09) |
| `docs/client-setup.md` | Setup-Doku fuer alle sieben Zielclients | PARTIAL | Sechs Abschnitte live verprobt, MUCGPT-Abschnitt bewusst als unverprobt gekennzeichnet |
| `appinfo/info.xml` | Version 0.1.1, dreisprachige Store-Beschreibung, 13 Routen | VERIFIED | `version`/`image-tag` = `0.1.1` gegengeprueft; Store fuehrt dieselbe Version live |
| `CHANGELOG.md` | 0.1.1-Eintrag | VERIFIED | `## [0.1.1] - 2026-08-19` vorhanden |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `admin_settings.py` | `config_values.py` | Feld-Id = Config-Schluessel (`CONFIG_KEYS`) | WIRED | Test haelt Gleichheit fest (05-01) |
| `entry_exapp.main` | `config_values.admin_overlay` | `_resolved_env()` beim Start | WIRED, aber DATENFLUSS GESTOERT | Verdrahtung korrekt, aber der Roundtrip scheitert live mit 401 auf der gemessenen Topologie (Gap 2) |
| `entry_exapp.main` | `build_exapp_app` (Issuer-Refusal) | `except ToolError: raise SystemExit(2)` | WIRED, aber FALSCH GEHAERTET | Ein durch die Admin-Form erreichbarer Issuer-Fehler fuehrt zum selben harten Abbruch, den Plan 05-04 fuer den einfacheren Fall (fehlende Adresse) bereits beseitigt hatte (CR-01) |
| `oauth/consent.py`/`oauth/connect.py` | `OAuthStore.access_disabled` | drei Enforcement-Punkte (BL-10) | WIRED | Live durch Unit-Tests belegt (05-02), kein Live-Lauf gegen echte Topologie noetig laut Plan |
| `exapp/purge.py` | `store.wipe_all` / `crypto.delete_key` | erzwungene Reihenfolge | WIRED | Live gemessen: Reihenfolge `["password","password","key"]`, 05-08 Linie B |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `entry_exapp._resolved_env()` | Admin-Overlay (`public_url`, `oauth_dcr`, ...) | `config_values.admin_overlay()` -> OCS `/ex-app/config/get-values` | NEIN (auf der gemessenen Topologie: 401) | DISCONNECTED (live gemessen in 05-08, siehe Gap 2) |
| `exapp/connections.py` `_setup()` | `config.public_url(env)` vs. `DEFAULT_PUBLIC_URL` | resolved env aus `main()` | JA (Fallback funktioniert, zeigt Setup-Hinweis korrekt) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Volle Test-Suite laeuft gruen | `uv run --no-sync pytest -q` | Exit 0, keine Fehler in der Ausgabe | PASS |
| CR-01 durch einen Regressionstest abgedeckt | `grep -n "test_an_unusable_admin_value_changes_nothing\|non-loopback\|is http on a host" tests/unit/test_exapp_config_values.py` | kein Treffer | FAIL (bestaetigt Gap 1) |
| `normalize_base_url` akzeptiert http auf Nicht-Loopback | Quelltextlektuere `config.py:121-147` | kein Scheme-Zwang auf https, kein Loopback-Check | FAIL (bestaetigt Gap 1) |
| Store-Version live | `appinfo/info.xml` `<version>`/`<image-tag>` | `0.1.1`/`0.1.1` | PASS |
| CHANGELOG traegt 0.1.1 | `grep "## \[0.1.1\]" CHANGELOG.md` | Treffer Zeile 14 | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh` in diesem Projekt gefunden (`find scripts -path '*/tests/probe-*.sh'` liefert nichts). Die Live-Beweise dieser Phase laufen als Integrationstests (`tests/integration/test_permission_parity_share.py`, `tests/integration/test_credential_flood.py`) und als manuelle, im SUMMARY protokollierte Laeufe gegen die HaRP-Topologie; beide Formen sind in den jeweiligen MEASUREMENTS.md-Dateien dokumentiert und wurden fuer diese Verifikation stichprobenartig durch Quelltext- und Testdatei-Abgleich nachvollzogen (siehe Behavioral Spot-Checks oben), nicht erneut gegen eine lebende Instanz ausgefuehrt.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| EXAPP-04 | 05-10 (mit Vorarbeit in 05-01/05-04/05-06/05-08) | App im Nextcloud App Store eingereicht | SATISFIED | Live-Nachweis Store-Listing, Signatur, ghcr Multi-Arch; REQUIREMENTS.md markiert Complete |
| EXAPP-05 | 05-07 | Setup-Doku pro Client mit Stolperstellen | SATISFIED (mit Einschraenkung) | 6/7 Clients live verprobt; MUCGPT-Abschnitt vorhanden, aber explizit unverprobt (siehe Truth 4/Human-Verify) |

Keine ORPHANED Requirements: `.planning/REQUIREMENTS.md` fuehrt fuer Phase 5 ausschliesslich EXAPP-04 und EXAPP-05, beide sind in Plan-Frontmatter referenziert (05-01, 05-02, 05-04, 05-05, 05-06, 05-08, 05-09, 05-10 tragen `EXAPP-04`; 05-07 traegt `EXAPP-05`).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/mcp_connector/exapp/config_values.py` | ~205-234 (`_public_url`) | Fehlende Issuer-taugliche https/Loopback-Regel trotz Docstring-Zusicherung "the extra conditions are the ones ... for the same reasons" | BLOCKER | CR-01: reproduzierbarer Crash-Loop ueber die Admin-Oberflaeche, kein UI-Recovery |
| `src/mcp_connector/entry_exapp.py` | ~331-338 | `except ToolError: raise SystemExit(2)` deckt auch den Issuer-Refusal-Fall ab, den Plan 05-04 fuer den einfacheren Fall (fehlende Adresse) bereits durch einen Setup-Zustand ersetzt hatte | BLOCKER | Dieselbe Symptomatik (Restart-Loop) kann durch einen Admin-Klick wiederhergestellt werden |
| `src/mcp_connector/exapp/purge.py` (Review WR-01, WR-02) | 140-153, 228-280 | Tabellen/Schluessel werden auch bei komplettem Revoke-Fehlschlag geleert; `_forced`/`_is_set` sind fuer eine irreversible Aktion permissiv | WARNING | Advisory laut Review, nicht durch diese Verifikation nachgebessert; siehe 05-REVIEW.md |
| `scripts/bootstrap_exapp.sh` (Review WR-03) | 145, 723-728 | `PUBLIC_URL` ungeprueft in JSON-Payload interpoliert (dieselbe Fehlerklasse wie IN-07) | WARNING | Nur Testskript der Wegwerf-Topologie, kein Produktionscode |

Kein TBD/FIXME/XXX-Marker in den Phase-5-Dateien gefunden (Debt-Marker-Gate ist sauber).

### Human Verification Required

#### 1. MUCGPT gegen eine echte laufende Instanz verproben

**Test:** Discovery, Werkzeugliste und ein Werkzeugaufruf mit Inhalten des konfigurierten Nextcloud-Kontos gegen eine echte MUCGPT-Instanz (Stadt Muenchen, it@M) durchfuehren.
**Expected:** `docs/client-setup.md`, MUCGPT-Abschnitt, kann seine im ersten Absatz benannte Luecke schliessen.
**Why human:** Erfordert Zugang zu einem fremden System samt Keycloak, das nicht Teil dieses Repositories ist und nicht automatisiert bereitgestellt werden kann.

#### 2. Ursachenanalyse und Fix des 401-Fehlers beim Admin-Werte-Lesevorgang

**Test:** Auf einer zweiten, frischen HaRP/AppAPI-Topologie den Startzeit-Lesevorgang der Admin-Werte beobachten (Containerlog nach Disable/Enable), um zu klaeren, ob der 401 spezifisch fuer die Wegwerf-Topologie ist oder jede Store-Installation betrifft.
**Expected:** Entweder eine bestaetigte, reproduzierbare Ursache mit Fix, oder der Nachweis, dass es sich um ein Artefakt der Testtopologie handelt.
**Why human:** Erfordert eine zusaetzliche laufende Nextcloud/AppAPI-Instanz und manuelle Beobachtung, die ueber Code-Lektuere hinausgeht.

### Gaps Summary

Die Phase hat einen aussergewoehnlich dichten Beweisapparat geliefert (Live-Messungen fuer Store-Submission, Install/Uninstall, Permission-Parity, Credential-Loadtest und Open-WebUI-Client), und der uebergrosse Teil des Phasenziels ist mit Belegen statt Behauptungen erfuellt. Zwei Punkte verhindern trotzdem ein uneingeschraenktes "passed":

1. **CR-01 (Blocker):** Der eigene Code-Review-Report der Phase hat einen kritischen, reproduzierbaren Fehler gefunden, der den zentralen Deadlock wieder herstellt, den diese Phase (Plan 05-04) explizit beseitigen sollte, erreichbar ueber genau das Formular, das dieselbe Phase (Plan 05-01) gebaut hat. Der Fund ist unabhaengig im aktuellen Code bestaetigt (kein Fix, kein Regressionstest, kein Folge-Commit). Das widerspricht der "gehärtet"-Zusage des Phasenziels direkt.
2. **Der 401-Fund (Blocker/Gap):** Das zentrale Ein-Klick-Feature dieser Phase, admin-gesetzte Werte ohne Umgebungsvariable wirksam zu machen, scheitert live auf der gemessenen Topologie bei jedem Start. Die Unit-Tests sind gruen, aber der End-zu-Ende-Beweis fehlt und die Ursache ist nur vermutet.

Zusaetzlich bleibt eine transparent dokumentierte, aber roadmap-woertlich ungeloeste Luecke: der MUCGPT-Client ist nicht gegen eine echte Instanz verprobt (externe Abhaengigkeit, Owner-Aktion noetig).

Alle anderen Wahrheiten der Phase (Store-Submission, Permission-Parity, Negativ-Credential-Loadtest, sechs von sieben Client-Doku-Abschnitte, Purge-Reihenfolge, Requirements-Traceability) sind mit Live-Messungen belegt und wurden unabhaengig nachvollzogen.

---

_Verified: 2026-08-19T22:15:00Z_
_Verifier: Claude (gsd-verifier)_
