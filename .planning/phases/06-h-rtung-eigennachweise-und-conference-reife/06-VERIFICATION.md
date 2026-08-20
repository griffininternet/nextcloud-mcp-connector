---
phase: 06-h-rtung-eigennachweise-und-conference-reife
verified: 2026-08-20T00:00:00Z
status: gaps_found
score: 5/6 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Cursor verbindet sich live nach der Teilregistrierung: Autorisierung und Tool-Aufruf laufen durch (Roadmap Success Criterion 3, Requirement CLIENT-04)"
    status: failed
    reason: "DCR mit Cursors Drei-URI-Rumpf wird 201 und die zwei zulässigen Adressen werden registriert (dieser Teil ist erfüllt und live belegt). Cursor liest die Antwort seiner eigenen Registrierung jedoch nicht zurück und schickt an /authorize weiterhin seine ursprüngliche cursor://-Adresse, also genau die verworfene. Der Server weist diese Anfrage regelkonform mit 400 (Seite E5) ab. Autorisierung und Tool-Aufruf laufen dadurch nicht durch. Ursache ist clientseitig (Cursor 3.2.16), gemessen und mit drei Gegenproben belegt (06-08-MEASUREMENTS.md Abschnitt 8)."
    artifacts:
      - path: ".planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-08-MEASUREMENTS.md"
        issue: "Belegt den Fehlschlag Feld für Feld (Abschnitte 6-8); kein Fix im Repository, da die Ursache beim Client liegt und keine der vier Auswege reine Reparaturen sind"
    missing:
      - "Eine Entscheidung aus BL-14 (Schema doch registrieren / Registrierung wieder ganz abweisen / verworfene Adresse für den Client sichtbar machen / so lassen und auf App-Passwort verweisen), oder ein explizites Akzeptieren dieses Zustands als Restrisiko mit Override-Eintrag"
---

# Phase 6: Härtung, Eigennachweise und Conference-Reife Verification Report

**Phase Goal:** Jeder offene v1.1-Punkt, der ohne fremden Zugang beweisbar ist, ist erledigt: ein CIMD-Client kommt unter denselben Kontrollen wie ein DCR-Client herein, der Abruf des Metadatendokuments hat eine belegte SSRF-Grenze, die lokalen Clients (Cursor, Loopback-Port) sind gemessen statt vermutet, die Ein-Klick-Story sagt wörtlich das, was auf 34.0.3 wahr ist, und das Conference-Material ist vorführbar.

**Verified:** 2026-08-20
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Quelle: ROADMAP.md Success Criteria 1-5 für Phase 6 (roadmap-Vertrag, SC3 aufgeteilt in seine zwei messbaren Teile, weil ein Teil erfüllt ist und der andere nicht).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ein CIMD-Client verbindet sich und ruft ein Werkzeug auf; DCR-Kontrollen (Redirect-URI-Prüfung, Allowlist, DCR-Kopplung) greifen unverändert | ✓ VERIFIED | 06-09-MEASUREMENTS.md: Claude Code 2.1.233 verbindet sich ohne Registrierung, `files_list` liefert echten Inhalt (Abschnitt 3.8); drei Kontrollproben live (Abschnitte 8-10): DCR aus → 0 ausgehende Sockets gegen 4 in der Positivkontrolle, CIMD aus lässt DCR unberührt, Allowlist wirkt in beide Richtungen mit derselben Fehlerseite wie bei DCR |
| 2 | CIMD-Dokumentabruf ist fail-closed und belegt: nur https, keine privaten/link-lokalen Ziele, Größen-/Zeitlimit, kontrolliertes Caching, je Grenze ein roter Negativtest | ✓ VERIFIED | `src/mcp_connector/oauth/cimd.py` (is_cimd_client_id, target_allowed, resolve_addresses, fetch_document, validate_document); `tests/unit/test_oauth_cimd.py` mit Rebinding-Test, Redirect-Verweigerung, 5120-Byte-Grenze, Nicht-Cachen von Fehlern; live in 06-09-MEASUREMENTS.md Abschnitt 3.5 bestätigt (317 Bytes, 300s Cache-Fenster, zwei öffentliche Adressen aufgelöst) |
| 3a | Cursor: DCR mit Drei-URI-Body wird 201, die zwei zulässigen Adressen werden registriert | ✓ VERIFIED | 06-08-MEASUREMENTS.md Abschnitt 3: `POST /register` → `201`, Store-Zeile trägt die zwei zulässigen Adressen, `cursor://...` fehlt nachweislich |
| 3b | Cursor: Autorisierung und Tool-Aufruf laufen durch | ✗ FAILED | 06-08-MEASUREMENTS.md Abschnitt 6-8: Cursor schickt an `/authorize` weiterhin seine `cursor://`-Adresse (liest die Registrierungsantwort nicht zurück), Server antwortet regelkonform `400`/Seite E5; kein Code, kein Token, kein Werkzeugaufruf. Drei Gegenproben belegen, dass die Ursache beim Client liegt, nicht am Server |
| 3c | Loopback-Portfrage beantwortet: Client mit wechselndem Port gemessen, Entscheid dokumentiert | ✓ VERIFIED | 06-09-MEASUREMENTS.md Abschnitt 4: drei Läufe mit den Ports 45157/47608/41977 plus ein Override-Lauf mit `MCP_OAUTH_CALLBACK_PORT=34567`; `docs/oauth-setup.md` dokumentiert die RFC-8252-7.3-Ausnahme samt akzeptiertem Restrisiko (Port-Squatting) |
| 4 | Store-UI-Install/Remove-Knopf auf 34.0.3 gemessen; Doku und Store-Text sagen genau das Gemessene | ✓ VERIFIED | 06-07-MEASUREMENTS.md Abschnitt 6: Install-Knopf "Deploy and enable", Remove-Knopf im Aktionsmenü nur bei abgeschalteter ExApp; `docs/exapp-install.md`, drei READMEs und Store-Text (appinfo/info.xml) gemeinsam nachgezogen, kein Ein-Klick-Versprechen ohne Deckung |
| 5 | Reproduzierbare Demo-Strecke (Verbindung, Werkzeugaufrufe, Per-User-Verwaltung, Widerruf) plus Lightning-Talk-Entwurf | ✓ VERIFIED | `docs/conference-demo.md` (Runbook, 7 Abschnitte), einmal vollständig durchgefahren in 06-10-MEASUREMENTS.md (82,2s gegen 82s behauptet), Per-User-Schalter und Widerruf je zweifach belegt (Client + Draht); `docs/conference-talk.md` (8 Folien, 280/300s, CfP-Stand korrekt benannt, nichts eingereicht) |

**Score:** 5/6 truths verified (3a und 3b als Teile derselben Roadmap-SC3 gezählt, hier separiert für Ehrlichkeit; ohne Separierung wäre SC3 als Ganzes FAILED)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/oauth/cimd.py` | is_cimd_client_id, target_allowed, resolve_addresses, fetch_document, validate_document, cache_lifetime | ✓ VERIFIED | Alle Funktionen vorhanden, `__all__` gepflegt, keine `os.environ`, kein Modulzustand |
| `src/mcp_connector/oauth/registry.py` | ENV_CIMD, ClientPolicy.cimd_enabled (fail-closed an dcr gekoppelt), loopback_match | ✓ VERIFIED | `cimd_enabled = _switch(...) and dcr`; `loopback_match` lockert ausschließlich den Port |
| `src/mcp_connector/oauth/provider.py` | _resolve_cimd, CIMD-Zweig in get_client, may_fetch-Trennung (Review-Fix) | ✓ VERIFIED | Zweig zwischen `row is None` und `_client_information`; `may_fetch=False` auf allen Nicht-/authorize-Pfaden bestätigt per grep (Zeilen 787, 902, 1511) |
| `src/mcp_connector/oauth/verifier.py` | may_fetch=False im Hot-Path (WR-01/WR-03) | ✓ VERIFIED | `verifier.py:227` ruft `get_client(..., may_fetch=False)` |
| `src/mcp_connector/oauth/store.py` | clients.cimd_fetched_at, clients.cimd_expires_at, idempotentes ALTER | ✓ VERIFIED | Bestätigt in 06-05-SUMMARY und live in 06-09-MEASUREMENTS (Store-Zeile Feld für Feld) |
| `src/mcp_connector/exapp/ui/consent.py` + `strings.py` | Hostname-Anzeige, Loopback-Warnung, kein "verified"-Text, kein Logo | ✓ VERIFIED | Live bestätigt auf der Zustimmungsseite in 06-09-MEASUREMENTS Abschnitt 3.6 ("Client ID host: claude.ai", "Comes back to this computer") |
| `docs/oauth-setup.md`, `docs/client-setup.md`, `docs/exapp-install.md` | CIMD-Abschnitt, Loopback-Entscheid, Cursor-Befund, Store-UI-Befund | ✓ VERIFIED | Alle offenen Live-Nachweis-Sätze ersetzt, per grep bestätigt (`does not accept yet`, `a live run against Cursor`, `not measured yet` → 0 Treffer) |
| `docs/conference-demo.md`, `docs/conference-talk.md` | Runbook und Talk-Entwurf | ✓ VERIFIED | Beide existieren, inhaltlich geprüft, einmal durchgefahren |
| Alle 10 `06-XX-MEASUREMENTS.md`/-SUMMARY-Dateien | Live-Belege | ✓ VERIFIED | Gelesen, intern konsistent, keine Credentials, Owner-Instanzen durchgehend unberührt |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `cimd.py` | `exapp/responses.py` | `bounded_response` Import | ✓ WIRED | Bestätigt in 06-01/06-02-SUMMARY, Grenztest vorhanden |
| `provider.py` | `cimd.py` | `fetch_document_and_lifetime` im CIMD-Zweig | ✓ WIRED | Live bestätigt (06-09, Abschnitt 3.5) |
| `provider.py` | `registry.py` | `redirect_uri_allowed`, `loopback_match`, `policy.allows` | ✓ WIRED | Live bestätigt (06-09 Kontrollproben) |
| `entry_exapp.py` | `metadata.py` | `cimd_enabled=policy.cimd_enabled` | ✓ WIRED | grep bestätigt eine Policy-Instanz, kein zweiter Lesevorgang |
| `verifier.py`/`provider.py` (Token/Revoke-Pfade) | `may_fetch=False` | Review-Fix WR-01/03 | ✓ WIRED | Commit `a47bb57`, per grep an 6 Stellen bestätigt |
| `_resolve_cimd` | Allowlist-Prüfung vor Fetch | Review-Fix WR-02 | ✓ WIRED | Commit `bd75cd8`, Zeile `provider.py:474` bestätigt |
| `consent.py` | `cimd.is_cimd_client_id` | Herkunftsmerkmal ohne Store-Zugriff | ✓ WIRED | grep bestätigt unveränderte Zahl der Store-Aufrufe |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Vollständige Unit-Testsuite | `uv run --no-sync pytest tests/unit -q` | Exit 0, keine Failures | ✓ PASS |
| Lint/Formatierung | `uv run --no-sync ruff check .` | "All checks passed!" | ✓ PASS |
| Review-Fix WR-01/03 im Code vorhanden | `grep -n "may_fetch" src/mcp_connector/oauth/*.py` | 12 Fundstellen inkl. Verifier-Hot-Path und beiden Exchange-Methoden | ✓ PASS |
| Review-Fix WR-02 im Code vorhanden | `grep -n "allowlist_only" provider.py` | Prüfung vor Fetch bestätigt (Zeile 474) | ✓ PASS |
| Keine Debt-Marker in geänderten Kern-Dateien | `grep -rniE "TODO\|FIXME\|XXX\|TBD"` auf oauth/*.py und exapp/ui/*.py | keine Treffer | ✓ PASS |
| Git-Arbeitsbaum sauber (keine unverifizierten Änderungen) | `git status --short` | leer | ✓ PASS |

### Probe Execution

Keine `scripts/*/tests/probe-*.sh`-Dateien im Projekt gefunden; kein Probe-Mechanismus für diese Phase deklariert. SKIPPED (keine Probes vorhanden).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| AUTH-08 | 06-03, 06-04, 06-05, 06-06, 06-09 | CIMD-Client kommt unter DCR-Kontrollen herein | ✓ SATISFIED | Live verbunden, DCR-Kontrollen live bestätigt (06-09); Review-Fixes WR-01/02/03 angewandt |
| AUTH-09 | 06-01, 06-02, 06-05 | CIMD-Dokumentabruf SSRF-geprüft und fail-closed | ✓ SATISFIED | Vollständiger Negativkatalog inkl. Rebinding; live bestätigt in 06-09 |
| CLIENT-04 | 06-08 | Cursor verbindet sich live (201, Autorisierung, Tool-Aufruf) | ✗ BLOCKED | 201 erfüllt, Autorisierung/Tool-Aufruf schlagen fehl (Client-Bug bei Cursor 3.2.16, gemessen); REQUIREMENTS.md führt es korrekt als offen (Checkbox `[ ]`, Traceability "Pending"); Übergabe in BL-14 |
| CLIENT-05 | 06-03, 06-09 | Loopback-Portfrage beantwortet und Entscheid dokumentiert | ✓ SATISFIED | Drei Läufe + Override-Lauf, RFC-8252-7.3-Ausnahme umgesetzt, Restrisiko dokumentiert |
| EXAPP-06 | 06-07 | 34.0.3-UI-Smoke gemessen, Doku/Store-Text sagen das Gemessene | ✓ SATISFIED | Install-/Remove-Knopf gemessen, Doku gemeinsam mit drei READMEs und Store-Text nachgezogen |
| CONF-01 | 06-10 | Demo-Material für Conference | ✓ SATISFIED | Runbook + einmaliger vollständiger Durchlauf mit Rohbeleg |
| CONF-02 | 06-10 | Lightning-Talk-Entwurf | ✓ SATISFIED | 8 Folien, 280/300s, CfP korrekt als geschlossen benannt, nichts eingereicht |

Keine verwaisten (orphaned) Requirements: alle 7 der Phase zugeordneten IDs erscheinen in mindestens einem Plan-Frontmatter.

### Anti-Patterns Found

Keine Blocker-Debt-Marker (TBD/FIXME/XXX) in den geänderten Kerndateien. Die drei im Code-Review (06-REVIEW.md) gefundenen Warnings (WR-01, WR-02, WR-03) sind durch die Commits `a47bb57` und `bd75cd8` behoben und im Code bestätigt (siehe Key Link Verification). Die drei Info-Findings (IN-01 Prozentkodierte Dot-Segmente, IN-02 IDN/Unicode-Divergenz, IN-03 kein Limit auf redirect_uris-Anzahl) bleiben laut explizitem Fix-Scope (Critical+Warning, Owner-Vorgabe 2026-08-20) unbehoben und als Advisory dokumentiert; kein Sicherheitsrisiko laut Review-Begründung, keine Blocker.

### Human Verification Required

Keine offenen Punkte, die visuelle/interaktive menschliche Prüfung erfordern — die Phase hat bereits umfassend mit echten Clients (Claude Code, Cursor) gegen eine echte Instanz gemessen, inklusive Screenshot-Beleg für den Store-UI-Befund (`docs/screenshots/exapp-remove-button.png`).

Ein Punkt braucht eine **Produktentscheidung des Owners**, keine Verifikationsarbeit: welcher der vier in BL-14 genannten Wege für den Cursor-Fall gewählt wird (Schema registrieren / Registrierung ganz abweisen / verworfene Adresse sichtbar machen / so lassen). Das ist keine "human_needed"-Prüfung im Sinne dieses Workflows, sondern die im Gap-Eintrag oben bereits benannte offene Entscheidung.

### Gaps Summary

Neun von zehn Plänen liefern exakt das, was Roadmap und Requirements verlangen, mit außergewöhnlich gründlicher Live-Messarbeit (drei echte Clients: Claude Code, Cursor, plus die Store-UI unter echtem Nextcloud 34.0.3). Der Code-Review fand drei Warnings (CIMD-Refetch im Hot-Path, Allowlist-Bypass für den ausgehenden Fetch), die beide vor dieser Verifikation bereits durch Commits behoben und im laufenden Code bestätigt wurden.

Der eine echte Gap: **Roadmap Success Criterion 3 verlangt wörtlich, dass Cursor nach der Teilregistrierung Autorisierung und Tool-Aufruf durchläuft.** Die Messung in 06-08 zeigt das Gegenteil, mit einer klar belegten Ursache auf Client-Seite (Cursor 3.2.16 liest die Registrierungsantwort nicht zurück und schickt weiterhin seine ursprüngliche `cursor://`-Adresse). Die Serverseite verhält sich exakt wie spezifiziert (D-35), und der ausführende Agent hat den Fehlschlag ehrlich dokumentiert statt ihn zu beschönigen — inklusive Aktualisierung der Doku, damit kein falscher Erfolg behauptet wird, und einer Übergabe in `.planning/BACKLOG.md` (BL-14) mit vier bewerteten Optionen.

**Dies sieht nach einer beabsichtigten/akzeptierten Abweichung aus** — die Roadmap-Zeile selbst wurde bereits auf "Cursor ... gemessen" (statt "verbunden") umformuliert und die Phase als abgeschlossen markiert. Ein formaler Override fehlt jedoch in diesem Verifikationsdokument. Empfehlung: Der Owner entscheidet zwischen (a) einem Override-Eintrag, der diese Abweichung als akzeptiertes Restrisiko festhält, oder (b) einem gezielten Folge-Plan, der einen der vier BL-14-Wege umsetzt.

**This looks intentional.** To accept this deviation, add to VERIFICATION.md frontmatter:

```yaml
overrides:
  - must_have: "Cursor verbindet sich live nach der Teilregistrierung: Autorisierung und Tool-Aufruf laufen durch"
    reason: "Ursache liegt belegt beim Client (Cursor 3.2.16 liest die DCR-Antwort nicht zurück); Server verhält sich spezifikationskonform (D-35); Übergabe in BL-14 mit vier bewerteten Optionen"
    accepted_by: "<name>"
    accepted_at: "<ISO timestamp>"
```

---

_Verified: 2026-08-20_
_Verifier: Claude (gsd-verifier)_
_Depth: standard_
