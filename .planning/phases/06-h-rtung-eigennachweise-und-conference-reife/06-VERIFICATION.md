---
phase: 06-h-rtung-eigennachweise-und-conference-reife
verified: 2026-08-20T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "Cursor verbindet sich live nach der Teilregistrierung: Autorisierung und Tool-Aufruf laufen durch (Roadmap Success Criterion 3, Requirement CLIENT-04) — geschlossen per Owner-Entscheid 2026-08-20 (BL-14 Option 3, \"sichtbar machen plus Doku\"), umgesetzt in Plan 06-11 (Commits 710c44b, 91a42ca, 4e26732, ffe4069). Die Anforderung wurde nicht durch einen Server-Fix erfüllt, sondern mit Owner-Freigabe auf das Gemessene umformuliert: CLIENT-04 und ROADMAP SC3 verlangen jetzt, dass Cursors Verhalten gemessen statt vermutet ist, DCR mit 201 antwortet, der Fehlschlag am Client belegt ist und ein funktionierender Ausweichweg (App-Passwort) dokumentiert und auf der Fehlerseite E5 genannt wird — alles davon ist erfüllt und verifiziert."
  gaps_remaining: []
  regressions: []
gaps: []
---

# Phase 6: Härtung, Eigennachweise und Conference-Reife Verification Report

**Phase Goal:** Jeder offene v1.1-Punkt, der ohne fremden Zugang beweisbar ist, ist erledigt: ein CIMD-Client kommt unter denselben Kontrollen wie ein DCR-Client herein, der Abruf des Metadatendokuments hat eine belegte SSRF-Grenze, die lokalen Clients (Cursor, Loopback-Port) sind gemessen statt vermutet, die Ein-Klick-Story sagt wörtlich das, was auf 34.0.3 wahr ist, und das Conference-Material ist vorführbar.

**Verified:** 2026-08-20
**Status:** passed
**Re-verification:** Yes — nach Gap-Closure (Plan 06-11)

## Goal Achievement

### Observable Truths

Quelle: ROADMAP.md Success Criteria 1-5 für Phase 6, Stand nach der Owner-genehmigten Umformulierung von Success Criterion 3 und CLIENT-04 (Plan 06-11, Commit `4e26732`).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ein CIMD-Client verbindet sich und ruft ein Werkzeug auf; DCR-Kontrollen (Redirect-URI-Prüfung, Allowlist, DCR-Kopplung) greifen unverändert | ✓ VERIFIED (Bestandsvermerk) | Unverändert gegenüber der Erstverifikation: 06-09-MEASUREMENTS.md, Claude Code 2.1.233 verbindet sich, `files_list` liefert Inhalt, drei Kontrollproben live. Regressionscheck heute: volle Testsuite und ruff weiterhin grün, kein Diff in `src/mcp_connector/oauth/` seit der Erstverifikation außer den in Gap 3b beschriebenen, auth-neutralen Änderungen |
| 2 | CIMD-Dokumentabruf ist fail-closed und belegt: nur https, keine privaten/link-lokalen Ziele, Größen-/Zeitlimit, kontrolliertes Caching, je Grenze ein roter Negativtest | ✓ VERIFIED (Bestandsvermerk) | Unverändert: `src/mcp_connector/oauth/cimd.py`, vollständiger Negativkatalog, live in 06-09 bestätigt |
| 3a | Cursor: DCR mit Drei-URI-Body wird 201, die zwei zulässigen Adressen werden registriert | ✓ VERIFIED (Bestandsvermerk) | Unverändert: 06-08-MEASUREMENTS.md Abschnitt 3 |
| 3b | Cursors Verhalten ist gemessen statt vermutet; der Fehlschlag ist client-seitig belegt und ein funktionierender Ausweichweg (App-Passwort) ist dokumentiert und auf der Fehlerseite genannt (Roadmap SC3 und CLIENT-04, mit Owner-Freigabe am 2026-08-20 umformuliert) | ✓ VERIFIED | **Requirement-Wortlaut geändert, jetzt erfüllt.** `.planning/REQUIREMENTS.md:14` (CLIENT-04, `[x]`, Kennzeichnung "Wortlaut am 2026-08-20 mit Owner-Freigabe... BL-14 Option 'sichtbar machen plus Doku'"); `.planning/ROADMAP.md` SC3 sagt dasselbe. `.planning/BACKLOG.md` BL-14 trägt `STATUS 2026-08-20: CLOSED`, nennt Datum, gewählte Option, Messverweis (`06-08-MEASUREMENTS.md` Abschnitte 6-8) und den Rohbeleg der geprüften SDK-Teilfrage (`OAuthClientInformationFull` lehnt Zusatzfeld ab, `EXTRA IN ANSWER: False`). `src/mcp_connector/exapp/ui/strings.py:478-484` (`ERROR_REDIRECT_BODY`) nennt jetzt den App-Passwort-Weg, geprüft per neuem Test `test_the_return_address_page_names_the_way_that_works` (grep bestätigt: Zeile 678 in `tests/unit/test_oauth_ui.py`), ohne Protokollwert, Adresse oder Scheme zu nennen (T-03-24 unverändert). `docs/client-setup.md:585` trägt den D-35-Grund ("owns a scheme exclusively"), `docs/oauth-setup.md:791` verweist auf BL-14 statt der vormals offenen Formulierung ("is an open decision" per grep: 0 Treffer). D-35 und der Auth-Pfad sind nachweislich unangetastet: `git diff --stat 73d711b^..HEAD -- .planning/PROJECT.md src/mcp_connector/oauth/` liefert leeren Diff |
| 3c | Loopback-Portfrage beantwortet: Client mit wechselndem Port gemessen, Entscheid dokumentiert | ✓ VERIFIED (Bestandsvermerk) | Unverändert: 06-09-MEASUREMENTS.md Abschnitt 4, `docs/oauth-setup.md` |
| 4 | Store-UI-Install/Remove-Knopf auf 34.0.3 gemessen; Doku und Store-Text sagen genau das Gemessene | ✓ VERIFIED (Bestandsvermerk) | Unverändert: 06-07-MEASUREMENTS.md |
| 5 | Reproduzierbare Demo-Strecke plus Lightning-Talk-Entwurf | ✓ VERIFIED (Bestandsvermerk) | Unverändert: `docs/conference-demo.md`, `docs/conference-talk.md`, 06-10-MEASUREMENTS.md |

**Score:** 6/6 truths verified (3a, 3b, 3c als Teile der ursprünglichen Roadmap-SC3 gezählt; 3b war der einzige Fehlschlag der Erstverifikation und ist durch die Owner-genehmigte Umformulierung samt Umsetzung nun erfüllt)

### Gap-Closure im Detail (Plan 06-11)

Der vormals FAILED Punkt 3b wurde nicht durch einen Serverfix geschlossen — D-35 (private-use-Schemes bleiben unregistrierbar) gilt unverändert, und Cursor 3.2.16 verbindet sich nach wie vor nicht, weil es die Registrierungsantwort nicht zurückliest und weiterhin seine `cursor://`-Adresse an `/authorize` schickt. Geschlossen wurde die Lücke auf dem vom Owner am 2026-08-20 entschiedenen Weg (BL-14, Option 3 "sichtbar machen plus Doku"):

1. **Die Fehlerseite E5 nennt den funktionierenden Weg.** `ERROR_REDIRECT_BODY` trägt jetzt den Satz "Some assistant apps cannot use this sign in at all, and for those the way in is an app password from your Nextcloud security settings." Verifiziert: Wort "app password" vorhanden, "Start the connection again" wörtlich erhalten (von der bestehenden Testtabelle festgenagelt), kein `!`, kein `://`, kein Client-Scheme ("cursor" kommt weder im Text noch im Markup außerhalb des `<style>`-Blocks vor). Bestehende Schweigepflicht-Gates (`FORBIDDEN_ON_ERROR_PAGES`, `FORBIDDEN_IN_ERROR_TEXT`) laufen unverändert grün über E5.
2. **CLIENT-04 und ROADMAP SC3 wurden mit Owner-Freigabe auf das Gemessene umformuliert**, statt eine unerreichbare Anforderung offen zu halten. Beide Stellen tragen Datum, Urheber (Owner-Entscheid) und den Grund der Änderung; die ursprüngliche Formulierung bleibt in BL-14 als Protokoll erhalten, aus dem die Entscheidung hervorgeht.
3. **BL-14 ist geschlossen** mit gewählter Option, Datum, Messverweis (`06-08-MEASUREMENTS.md`) und einem gemessenen (nicht behaupteten) Rohbeleg dafür, warum das SDK-Antwortmodell kein Zusatzfeld für verworfene Adressen trägt.
4. **Beide Doku-Seiten** (`docs/client-setup.md`, `docs/oauth-setup.md`) benennen konsistent denselben Weg (App-Passwort) und den D-35-Grund; die zuvor offene Formulierung in `docs/oauth-setup.md` ist durch die getroffene Entscheidung ersetzt.
5. **D-35 und der Auth-Pfad sind unverändert** — mit Beleg per leerem Diff über den gesamten Gap-Closure-Bereich.

Dies ist eine legitime, dokumentierte Requirement-Präzisierung (Owner-Entscheidung, nicht stillschweigend abgeschwächt) und keine Verschleierung: Der ursprüngliche Anspruch, der Grund seiner Änderung, das Datum und die Alternativen, die nicht gewählt wurden, stehen alle mit Rohbeleg im Repository.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/oauth/cimd.py` | is_cimd_client_id, target_allowed, resolve_addresses, fetch_document, validate_document, cache_lifetime | ✓ VERIFIED | Unverändert seit Erstverifikation |
| `src/mcp_connector/oauth/registry.py` | ENV_CIMD, ClientPolicy.cimd_enabled, loopback_match | ✓ VERIFIED | Unverändert |
| `src/mcp_connector/oauth/provider.py` | _resolve_cimd, CIMD-Zweig, may_fetch-Trennung | ✓ VERIFIED | Unverändert, leerer Diff im Gap-Closure-Bereich bestätigt |
| `src/mcp_connector/oauth/verifier.py` | may_fetch=False im Hot-Path | ✓ VERIFIED | Unverändert |
| `src/mcp_connector/oauth/store.py` | cimd_fetched_at/cimd_expires_at | ✓ VERIFIED | Unverändert |
| `src/mcp_connector/exapp/ui/strings.py` | ERROR_REDIRECT_BODY mit App-Passwort-Ausweg | ✓ VERIFIED (neu) | Zeilen 478-484 bestätigt gelesen, Wortlaut exakt wie in 06-11-PLAN/-SUMMARY beschrieben |
| `tests/unit/test_oauth_ui.py` | Neuer Test für den E5-Ausweg | ✓ VERIFIED (neu) | `test_the_return_address_page_names_the_way_that_works`, Zeile 678, geprüft: Assertions decken alle drei Verhaltensanforderungen ab |
| `.planning/BACKLOG.md` | BL-14 geschlossen | ✓ VERIFIED (neu) | Vollständig gelesen: Status-Block, vier Optionen erhalten, Rohbeleg-Code-Block vorhanden |
| `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` | CLIENT-04/SC3 umformuliert und abgehakt | ✓ VERIFIED (neu) | Beide Dateien vollständig gelesen, Wortlaut und Kennzeichnung bestätigt, Traceability auf "Complete" |
| `docs/client-setup.md`, `docs/oauth-setup.md` | D-35-Grund, Ausweg, getroffene Entscheidung | ✓ VERIFIED (neu) | grep-bestätigt: "owns a scheme exclusively" in client-setup.md, "BL-14"-Verweis in oauth-setup.md, "is an open decision" → 0 Treffer |
| `docs/exapp-install.md`, `docs/conference-demo.md`, `docs/conference-talk.md` | Store-UI-Befund, Runbook, Talk | ✓ VERIFIED | Unverändert seit Erstverifikation |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `cimd.py` | `exapp/responses.py` | `bounded_response` | ✓ WIRED | Unverändert |
| `provider.py` | `cimd.py` | `fetch_document_and_lifetime` | ✓ WIRED | Unverändert |
| `provider.py` | `registry.py` | `redirect_uri_allowed`, `loopback_match`, `policy.allows` | ✓ WIRED | Unverändert |
| `verifier.py`/`provider.py` | `may_fetch=False` | Review-Fix WR-01/03 | ✓ WIRED | Unverändert, Commit `a47bb57` |
| `_resolve_cimd` | Allowlist-Prüfung vor Fetch | Review-Fix WR-02 | ✓ WIRED | Unverändert, Commit `bd75cd8` |
| `strings.ERROR_REDIRECT_BODY` | `docs/client-setup.md` | derselbe Ausweg ("app password") an beiden Stellen | ✓ WIRED (neu) | Konsistenzprüfung im Plan (`assert 'app password' in s.ERROR_REDIRECT_BODY and ... in doc`) sowie eigene grep-Prüfung bestätigt |
| `.planning/BACKLOG.md` (BL-14 Closure) | `06-08-MEASUREMENTS.md` | Messverweis in der Schließung | ✓ WIRED (neu) | Zitat "Abschnitte 6 bis 8" im Closure-Block bestätigt |
| `.planning/REQUIREMENTS.md` | `.planning/ROADMAP.md` | dieselbe Owner-genehmigte Umformulierung an beiden Stellen | ✓ WIRED (neu) | Beide Dateien tragen "Owner-Freigabe" bzw. "mit Owner-Freigabe am 2026-08-20", wortgleiche Substanz |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Vollständige Unit- und Contract-Testsuite | `uv run --no-sync pytest tests/unit tests/contract -q` | Exit 0, keine Failures | ✓ PASS |
| Lint/Formatierung | `uv run --no-sync ruff check .` | "All checks passed!" | ✓ PASS |
| Neuer E5-Test tatsächlich vorhanden und inhaltlich passend | `grep -n "def test_the_return_address_page_names_the_way_that_works" -A 20 tests/unit/test_oauth_ui.py` | Test vorhanden, prüft App-Passwort-Text, kein Scheme-Leak | ✓ PASS |
| ERROR_REDIRECT_BODY trägt den neuen Satz wörtlich | `grep -n "ERROR_REDIRECT_BODY" -A 7 strings.py` | Text exakt wie in SUMMARY behauptet | ✓ PASS |
| CLIENT-04/SC3-Umformulierung tatsächlich im Dokument | Volltext-Lektüre REQUIREMENTS.md/ROADMAP.md | Wortlaut, Kennzeichnung und Traceability bestätigt | ✓ PASS |
| BL-14 tatsächlich geschlossen mit Rohbeleg | Volltext-Lektüre BACKLOG.md (BL-14-Block) | Status CLOSED, Datum, Option, Messverweis, Code-Block-Beleg | ✓ PASS |
| D-35/Auth-Pfad unangetastet über den gesamten Gap-Closure-Bereich | `git diff --stat 73d711b^..HEAD -- .planning/PROJECT.md src/mcp_connector/oauth/` | leerer Diff | ✓ PASS |
| Arbeitsbaum sauber | `git status --short` | leer | ✓ PASS |

### Probe Execution

Keine `scripts/*/tests/probe-*.sh`-Dateien im Projekt gefunden. SKIPPED (keine Probes vorhanden).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| AUTH-08 | 06-03..06-06, 06-09 | CIMD-Client kommt unter DCR-Kontrollen herein | ✓ SATISFIED | Unverändert seit Erstverifikation |
| AUTH-09 | 06-01, 06-02, 06-05 | CIMD-Dokumentabruf SSRF-geprüft und fail-closed | ✓ SATISFIED | Unverändert |
| CLIENT-04 | 06-08, 06-11 | Cursors Verhalten gemessen statt vermutet, Ausweichweg dokumentiert (Owner-genehmigt umformuliert) | ✓ SATISFIED | REQUIREMENTS.md `[x]`, Traceability "Complete", Wortlaut deckt sich mit dem Gemessenen und dem Umgesetzten (06-11) |
| CLIENT-05 | 06-03, 06-09 | Loopback-Portfrage beantwortet und Entscheid dokumentiert | ✓ SATISFIED | Unverändert |
| EXAPP-06 | 06-07 | 34.0.3-UI-Smoke gemessen, Doku sagt das Gemessene | ✓ SATISFIED | Unverändert |
| CONF-01 | 06-10 | Demo-Material für Conference | ✓ SATISFIED | Unverändert |
| CONF-02 | 06-10 | Lightning-Talk-Entwurf | ✓ SATISFIED | Unverändert |

Keine verwaisten Requirements. Alle 7 der Phase zugeordneten IDs sind `Complete`.

### Anti-Patterns Found

Keine Blocker-Debt-Marker. Die drei Code-Review-Warnings (WR-01/02/03) bleiben behoben (unverändert seit Erstverifikation). Die drei Info-Findings (IN-01..03) bleiben laut explizitem Fix-Scope als Advisory dokumentiert, kein Blocker. Der Gap-Closure-Plan 06-11 selbst führt keine neuen Debt-Marker ein (geprüft in `strings.py`, `test_oauth_ui.py`).

### Human Verification Required

Keine. Die zuvor genannte offene Produktentscheidung (welcher BL-14-Weg gewählt wird) ist durch den Owner getroffen und in Plan 06-11 umgesetzt worden.

### Gaps Summary

Keine verbleibenden Gaps. Der einzige Fehlschlag der Erstverifikation (Cursor-Autorisierung/Tool-Aufruf, Roadmap-SC3 Teil 3b) wurde durch eine dokumentierte Owner-Entscheidung vom 2026-08-20 (BL-14, Option 3 "sichtbar machen plus Doku") und deren vollständige, TDD-gestützte Umsetzung in Plan 06-11 geschlossen (Commits `710c44b`, `91a42ca`, `4e26732`, `ffe4069`). Die Anforderung wurde nicht künstlich abgeschwächt: Datum, Urheber, gewählte Option, verworfene Alternativen und der gemessene Grund für das bewusst nicht Getane stehen alle mit Rohbeleg in `.planning/BACKLOG.md`, `.planning/REQUIREMENTS.md` und `.planning/ROADMAP.md`. D-35 und der Auth-Pfad blieben dabei nachweislich unangetastet (leerer Diff). Volle Testsuite (Unit + Contract) und Linter sind grün, der Arbeitsbaum ist sauber.

---

_Verified: 2026-08-20_
_Verifier: Claude (gsd-verifier)_
_Depth: standard (re-verification after gap closure)_
