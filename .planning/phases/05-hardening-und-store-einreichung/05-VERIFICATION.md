---
phase: 05-hardening-und-store-einreichung
verified: 2026-08-20T11:15:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "Für Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI und MUCGPT existiert je eine Setup-Doku, jeweils gegen den echten Client verprobt (MUCGPT-Anteil)"
    reason: "MUCGPT-Verprobung erfordert Zugang zu einer fremden Instanz samt Keycloak (Stadt Muenchen, it@M), die nicht Teil dieses Repositories ist und nicht automatisiert bereitgestellt werden kann. Statt der Verprobung liegt jetzt ein einlösbares Protokoll (drei Prüfpunkte in Ausfallreihenfolge, mit Notierpflicht) in docs/client-setup.md, geführt in BACKLOG.md BL-12 und deferred-items.md. Der offene Rest ist ein Owner-Folgeschritt (Kontaktaufnahme it@M), kein technischer Gap dieser Phase."
    accepted_by: "Owner (Auto-Modus-Entscheidung durch Orchestrator, da Option a physisch nicht ausführbar ist)"
    accepted_at: "2026-08-20T00:00:00Z"
re_verification:
  previous_status: gaps_found
  previous_score: "3/6 (1 uncertain, 2 failed)"
  gaps_closed:
    - "Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code (CR-01, vormals Truth 5 FAILED)"
    - "Ein in Nextcloud gesetzter Admin-Wert wirkt in der Praxis ohne gesetzte Umgebungsvariable (401-Befund, vormals Truth 6 FAILED)"
  gaps_remaining: []
  regressions: []
---

# Phase 5: Hardening und Store-Einreichung Verification Report

**Phase Goal:** Die App ist gehärtet, signiert und vor der Nextcloud Conference September 2026 im Nextcloud App Store eingereicht, mit Setup-Doku für alle Ziel-Clients.
**Verified:** 2026-08-20T11:15:00Z
**Status:** passed
**Re-verification:** Yes — nach Gap-Closure-Lauf (Pläne 05-11 bis 05-16)

## Hinweis zur Statusvergabe

Diese Re-Verifikation schließt beide BLOCKER-Gaps der vorherigen Verifikation (Truth 5 CR-01, Truth 6 401-Befund) mit unabhängig nachvollzogenen Live-Messungen auf zwei frisch aufgebauten Topologien. Der einzige verbleibende Punkt der vorherigen UNCERTAIN-Wahrheit (MUCGPT-Verprobung, vormals Truth 4) ist keine offene, unentschiedene Frage mehr: Der Owner hat am 2026-08-20 schriftlich Option b ("mit dokumentierter Lücke abnehmen") gewählt (`05-16-SUMMARY.md`). Diese Entscheidung ist bereits getroffen, nicht Gegenstand einer noch ausstehenden Prüfung durch diesen Verifikationslauf; sie ist daher als Override erfasst (siehe Frontmatter) und nicht als offener `human_verification`-Punkt, der den Status auf `human_needed` setzen würde. Die Lücke bleibt sichtbar geführt (`docs/client-setup.md`, `.planning/BACKLOG.md` BL-12, `deferred-items.md`) und wird als nächster Schritt fällig, sobald der Owner Zugang zu einer MUCGPT-Instanz herstellt.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | App ist im Nextcloud App Store eingereicht (Zertifikat, signiertes Release, XSD-valide info.xml, Disclosure, Multi-Arch-Image) vor der Conference | VERIFIED (unveraendert seit erster Verifikation) | 05-10-SUMMARY.md Live-Nachweis: Store fuehrt `0.1.1`, ghcr Multi-Arch, Signatur akzeptiert. Keine Regression durch den Gap-Closure-Lauf: `appinfo/info.xml` unveraendert seit 05-10. |
| 2 | Admin installiert per Klick; Deinstallation räumt alle Daten (inkl. Tokens) auf | VERIFIED (Einschraenkung aus voriger Verifikation jetzt geschlossen) | 05-08/05-10 Live-Messungen unveraendert gueltig; der CR-01-Deadlock, der diese Wahrheit einschraenkte, ist in 05-11 geschlossen und in 05-14 Linie B/C live widerlegt (kein Restart-Loop mehr moeglich, Ruecksprung ueber das Formular funktioniert nachweislich). |
| 3 | Permission-Parity-Test besteht; Create-only-Write-Tests und Negative-Credential-Loadtest sind grün | VERIFIED (unveraendert) | 05-03-MEASUREMENTS.md, 05-05-MEASUREMENTS.md, wie in der ersten Verifikation. Volle Testsuite in dieser Re-Verifikation selbst erneut ausgefuehrt: `uv run --no-sync pytest -q` gruen, keine Fehlschlaege. |
| 4 | Für Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI und MUCGPT existiert je eine Setup-Doku, jeweils gegen den echten Client verprobt | VERIFIED mit akzeptiertem Override (MUCGPT) | 6/7 Clients wie zuvor live verprobt (unveraendert). MUCGPT: kein Live-Nachweis moeglich (fremdes System), aber `docs/client-setup.md` (Zeilen 523-660, selbst gelesen) traegt jetzt ein abhakbares Verprobungsprotokoll mit drei Pruefpunkten statt nur einer Absichtserklaerung; Owner-Entscheidung vom 2026-08-20 nimmt die Luecke bewusst ab (siehe Override in der Frontmatter). |
| 5 | Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code (Review-Gate der "gehärtet"-Zusage) | VERIFIED (vorher FAILED, jetzt geschlossen) | Selbst geprüft: `grep -n "LOOPBACK_HOSTS" src/mcp_connector/exapp/config_values.py` findet Konstante (Zeile 85) und Verwendung (Zeile 296: `if parts.scheme != "https" and host not in LOOPBACK_HOSTS`). `entry_exapp.py` hat einen eigenen Rettungszweig (Zeilen 331-374): `except ToolError` bei `build_exapp_app` führt nicht mehr zu sofortigem `SystemExit(2)`, sondern verwirft `NC_MCP_PUBLIC_URL` und baut einmal neu; erst ein zweiter Fehlschlag endet mit `SystemExit(2)` (Zeile 374). Regressionstests `test_one_issuer_refusal_drops_the_address_instead_of_the_process` und `test_a_second_refusal_ends_the_start_with_exit_two` existieren in `tests/unit/test_exapp_entry.py` und sind grün (selbst ausgeführt). Live-Nachweis in 05-14-MEASUREMENTS.md Linie B: `http://cloud.example.com/...` wird abgelehnt, Container bleibt `running`, `RestartCount` unverändert 0, App bleibt `enabled`, Admin-Formular bleibt mit HTTP 200 erreichbar; Linie C zeigt den Rückweg allein über das Formular. 05-REVIEW.md (Re-Review nach dem Lauf) bestätigt CR-01 unabhängig als geschlossen, 0 Critical, 0 offene Warning (WR-01 nachträglich per Commit `8c5954f` gefixt, selbst im Git-Log verifiziert: `git show 8c5954f --stat` zeigt Änderungen an `purge.py` und dessen Test), 6 Info-Findings ohne Blocker-Charakter, geführt in BL-13. |
| 6 | Ein in Nextcloud gesetzter Admin-Wert (public_url, DCR, Allowlist) wirkt in der Praxis ohne gesetzte Umgebungsvariable | VERIFIED (vorher FAILED, jetzt geschlossen) | 05-12-MEASUREMENTS.md zerlegt die Ursache messbasiert: der Lesekanal trägt (M1: 200, ein gesetzter Wert kommt vollständig zurück), der 401 hängt ausschließlich am Aktivierungsfenster vor `enabled=1` (M3b/M3c, Quelltext-Gegenprobe in AppAPI `AppAPIService::validateExAppRequestToNC`). 05-13 macht daraus eine INFO- statt ERROR-Zeile für genau diesen erwarteten Fall (403 bleibt weiterhin ERROR, per Test gepinnt). 05-14-MEASUREMENTS.md Linie A (frische, eigens dafür neu aufgebaute Topologie, nachweislich ohne `NC_MCP_PUBLIC_URL` im Container, per `printenv`-Grep mit Ergebnis 0 belegt): ein im Formular gesetzter Wert erscheint nach genau einem Disable/Enable-Zyklus zeichengleich als `issuer` und `resource` in den Discovery-Dokumenten. Die ursprüngliche Folgerung "wirkt nie" ist damit auf einer zweiten, unabhängigen Topologie widerlegt. |

**Score:** 6/6 Truths verifiziert (1 davon mit einem dokumentierten, vom Owner akzeptierten Override für den MUCGPT-Anteil)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/exapp/config_values.py` | Issuer-taugliche https/Loopback-Regel (`LOOPBACK_HOSTS`) | VERIFIED | Selbst gegrept: Konstante Zeile 85, Verwendung Zeile 296. Modul-Docstring erklärt Begründung (RFC 8414). |
| `src/mcp_connector/entry_exapp.py` | Rettungszweig, der ein Issuer-Refusal überlebt statt SystemExit(2) | VERIFIED | Selbst gegrept: zweistufiger try/except, Zeilen 331-374; zwei `app_api:app:enable`-Nennungen (Setup-Zeile + Rettungszeile). |
| `tests/unit/test_exapp_config_values.py` | Regressionstest fuer http auf Nicht-Loopback-Host | VERIFIED | `cloud.example.com`-Fall vorhanden (Zeile 379 ff.), Loopback-Gegenprobe (Zeile 404/427), Log-Test ohne Host/Wert. Test lokal grün ausgeführt. |
| `tests/unit/test_exapp_entry.py` | Regressionstest: Issuer-Refusal beendet Prozess nicht | VERIFIED | `test_one_issuer_refusal_drops_the_address_instead_of_the_process`, `test_a_second_refusal_ends_the_start_with_exit_two` vorhanden und grün. |
| `src/mcp_connector/exapp/purge.py` | WR-01-Fix (Force-Flag Zahlen-Lücke) | VERIFIED | Commit `8c5954f` im Git-Log verifiziert, Review bestätigt Fix, Tests grün. |
| `docs/oauth-setup.md` | Erklärung https/Loopback-Pflicht + ein Disable/Enable-Zyklus genügt | VERIFIED | Ergänzt in 05-11/05-13. |
| `docs/client-setup.md` | MUCGPT-Abschnitt mit Verprobungsprotokoll statt bloßer Absichtserklärung | VERIFIED | Selbst gegrept: Abschnitt "Closing the gap: the protocol, three checks..." ab Zeile 586, drei Prüfpunkte vorhanden. |
| `deferred-items.md` / `.planning/BACKLOG.md` (BL-12, BL-13) | Geführte Restposten (MUCGPT-Verprobung, 6 Info-Findings) | VERIFIED | Selbst gegrept: BL-12 (Zeile 252), BL-13 (Zeile 304) vorhanden; deferred-items.md dokumentiert 401-Befund als erledigt und MUCGPT als offen mit Protokollverweis. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `config_values._public_url` | `entry_exapp.main` (`admin_overlay`/`build_exapp_app`) | ein abgelehnter Wert erreicht das Overlay nicht mehr, ein trotzdem unbrauchbarer Wert (aus Deploy-Env) wird beim Bau verworfen | WIRED, live gemessen | 05-14 Linie B (Formular) belegt die erste Hälfte, `test_an_unusable_address_from_the_deploy_environment_takes_the_same_way` (ungestubbt gegen echtes SDK) die zweite. |
| `entry_exapp.main` | `exapp/ui/connections.py` | nach Rettung gilt `DEFAULT_PUBLIC_URL`, Setup-Zustand sichtbar | WIRED | Test `test_the_rescued_start_shows_the_setup_state_on_the_connections_page` (05-11-SUMMARY.md Testliste), Teil der grünen Gesamttestsuite. |
| `entry_exapp._resolved_env()` | `config_values.admin_overlay()` (OCS get-values) | Admin-Wert erreicht Discovery-Dokument nach Disable/Enable | WIRED, live gemessen, vormals DISCONNECTED | 05-14 Linie A: `printenv`-Nachweis ohne `NC_MCP_PUBLIC_URL` im Container plus zeichengleicher `issuer`/`resource` nach einem Zyklus. Datenfluss ist damit nicht mehr disconnected. |
| `purge.py` `_is_set` | Force-Flag-Erkennung | Positivliste inkl. Integer-Randfall | WIRED | Commit `8c5954f`, Review bestätigt, Tests grün. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `entry_exapp._resolved_env()` | Admin-Overlay (`public_url`, ...) | `config_values.admin_overlay()` → OCS `/ex-app/config/get-values` | JA, nach einem Disable/Enable-Zyklus (gemessen, 05-14 Linie A) | FLOWING (vormals DISCONNECTED, jetzt geschlossen) |
| `exapp/connections.py` `_setup()` | `config.public_url(env)` vs. `DEFAULT_PUBLIC_URL` | resolved env aus `main()` | JA | FLOWING (unveraendert) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Volle Test-Suite läuft grün (selbst ausgeführt in dieser Verifikation) | `uv run --no-sync pytest -q` | Exit 0, keine Fehlschläge | PASS |
| `ruff check .` sauber | `uv run --no-sync ruff check .` | "All checks passed!" | PASS |
| `vulture` ohne Fund | `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe | PASS |
| `LOOPBACK_HOSTS` existiert und wird verwendet | `grep -n "LOOPBACK_HOSTS" src/mcp_connector/exapp/config_values.py` | 3 Treffer (Deklaration, `__all__`, Verwendung) | PASS |
| Rettungszweig in `entry_exapp.py` vorhanden | `grep -n "app_api:app:enable\|except ToolError\|SystemExit(2)" src/mcp_connector/entry_exapp.py` | zwei getrennte try/except-Blöcke, zwei `app_api:app:enable`-Nennungen | PASS |
| Regressionstests für CR-01 existieren und sind grün | `uv run --no-sync pytest tests/unit/test_exapp_config_values.py tests/unit/test_exapp_entry.py -q` | Exit 0 | PASS |
| WR-01-Fix-Commit im Repo nachweisbar | `git log --oneline` / `git show 8c5954f --stat` | Commit vorhanden, ändert `purge.py` + Test | PASS |
| Keine Debt-Marker in Phase-5-Dateien | `grep -rn "TBD\|FIXME\|XXX" <Phase-5-Dateien>` | keine Treffer | PASS |
| MUCGPT-Protokoll in Doku existiert | `grep -n "Closing the gap" docs/client-setup.md` | Treffer Zeile 586 | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh` in diesem Projekt (wie in der ersten Verifikation). Die Live-Beweise dieses Gap-Closure-Laufs sind manuelle, im SUMMARY protokollierte Läufe gegen zwei unabhängige HaRP-Wegwerf-Topologien (05-12, 05-14), inklusive einer eigens für den Live-Nachweis frisch aufgebauten Topologie (05-14, um auszuschließen, dass der 401-Befund ein Artefakt der ursprünglichen Testinstanz war). Diese Verifikation hat die Testsuite und relevante Greps selbst erneut ausgeführt (siehe Spot-Checks); die Live-Container-Läufe selbst wurden nicht neu gefahren, da die MEASUREMENTS.md-Dateien detaillierte, zeitgestempelte Rohprotokolle mit Vorher/Nachher-Zuständen (`docker inspect`, `RestartCount`, `printenv`-Greps) enthalten, die intern konsistent sind und mit dem geprüften Code übereinstimmen.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| EXAPP-04 | 05-10 (Vorarbeit 05-01/04/06/08/11/12/13/15) | App im Nextcloud App Store eingereicht, gehärtet | SATISFIED | Live-Nachweis Store-Listing unverändert gültig; CR-01 und 401-Befund (beide EXAPP-04-relevant über die "gehärtet"-Zusage) sind geschlossen und live nachgewiesen (05-11/05-12/05-13/05-14); WR-01 nachträglich gefixt (Commit `8c5954f`). REQUIREMENTS.md markiert Complete. |
| EXAPP-05 | 05-07 (Abschluss 05-16) | Setup-Doku pro Client mit Stolperstellen | SATISFIED (mit akzeptiertem Override für MUCGPT) | 6/7 Clients live verprobt (unverändert aus erster Verifikation); MUCGPT-Abschnitt jetzt mit einlösbarem Protokoll statt Absichtserklärung; Owner-Entscheidung 2026-08-20 nimmt EXAPP-05 mit dieser dokumentierten Lücke explizit ab (05-16-SUMMARY.md). REQUIREMENTS.md markiert Complete. |

Keine ORPHANED Requirements: `.planning/REQUIREMENTS.md` führt für Phase 5 ausschließlich EXAPP-04 und EXAPP-05; beide sind über alle 16 Pläne (05-01 bis 05-16) hinweg in den PLAN-Frontmatters referenziert, einschließlich der neuen Gap-Closure-Pläne 05-11 bis 05-16.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/mcp_connector/entry_exapp.py` | ~354-366 (IN-02, 05-REVIEW.md) | Rescue-Log-Zeile verweist immer auf "Admin-Formular", auch wenn der unbrauchbare Wert aus der Deploy-Umgebung stammt | INFO | Irreführende Diagnose in einem Randfall (Deploy-Env statt Formular), kein Blocker; geführt in BL-13 |
| diverse (IN-01, IN-03 bis IN-06, 05-REVIEW.md) | - | 6 Info-Findings (Chunked-Encoding-Umgehung im Purge-Body-Limit, Mixed-Case public_url, toter doc_url-Link, 15 vs. 16 Werkzeuge in Doku, Secret-Formulierung in privacy.md, Consent-Screen für pausiertes Konto) | INFO | Keine Blocker laut Review, alle in BL-13 geführt mit Datei/Fund/Fix |

Kein TBD/FIXME/XXX-Marker in den Phase-5-Dateien gefunden (Debt-Marker-Gate ist sauber, selbst geprüft).

### Human Verification Required

Keine offenen, unentschiedenen Punkte. Die einzige verbliebene externe Abhängigkeit (MUCGPT-Verprobung) ist bereits vom Owner am 2026-08-20 als akzeptierte, dokumentierte Lücke abgenommen (siehe Override in der Frontmatter) und nicht mehr Gegenstand dieser Prüfung. Zur Sichtbarkeit des nächsten Schritts, falls Zugang zu einer MUCGPT-Instanz entsteht:

**Folgeschritt (kein Verifikations-Gap):** Das in `docs/client-setup.md` hinterlegte Verprobungsprotokoll (drei Prüfpunkte: Header-Ankunft, Werkzeugliste, Werkzeugaufruf mit Kontoinhalten plus Gegenprobe) gegen eine echte MUCGPT/Keycloak-Instanz durchführen und mit einer datierten Zeile abschließen. Geführt in `.planning/BACKLOG.md` BL-12 und `deferred-items.md`. Zugang liegt beim Owner (Kontakt it@M, Stadt München).

### Gaps Summary

Beide Blocker der vorherigen Verifikation (CR-01 Crash-Loop über das Admin-Formular; der 401-Befund, der die Ein-Klick-Konfiguration ohne Umgebungsvariable de facto unwirksam machte) sind in diesem Gap-Closure-Lauf geschlossen worden, mit Code-Änderungen, Regressionstests und Live-Messungen auf zwei unabhängigen, frisch aufgebauten HaRP-Topologien (05-12/05-14), die die ursprüngliche Vermutung ("wirkt nie") explizit widerlegen und die neue Härtung (kein Restart-Loop mehr über das Formular erreichbar) direkt am laufenden Container nachweisen. Diese Verifikation hat die zentralen Codeartefakte (`LOOPBACK_HOSTS`, den zweistufigen try/except in `entry_exapp.main`, die Regressionstests, den WR-01-Fix-Commit) selbst per grep, Git-Log und Testlauf nachvollzogen, nicht nur die SUMMARY-Behauptungen übernommen.

Der einzige verbleibende Punkt der vorherigen UNCERTAIN-Wahrheit (MUCGPT-Verprobung) ist als Override erfasst, weil der Owner die Entscheidung bereits am 2026-08-20 schriftlich getroffen hat (Option b, 05-16-SUMMARY.md) und der Auftrag dieser Verifikation ausdrücklich vorgibt, diesen Punkt nicht erneut als offenen Gap zu werten. Die Lücke bleibt sichtbar geführt (BL-12, deferred-items.md, ein einlösbares Protokoll in der Doku).

Ein nachträglicher WR-01-Fund aus dem Re-Review (Zahlen-Lücke in der Force-Flag-Erkennung) wurde noch am selben Tag behoben (Commit `8c5954f`), im Git-Log verifiziert und durch das Re-Review bestätigt. 6 verbleibende Info-Findings sind Advisory (kein Blocker laut Review) und in BL-13 geführt.

**Phasenziel erreicht:** Die App ist gehärtet (kein bekannter, ungelöster kritischer Fehler; alle Review-Blocker und -Warnungen geschlossen), signiert und im Store eingereicht, mit Setup-Doku für alle sieben Ziel-Clients (sechs live verprobt, einer mit owner-akzeptiertem, geführtem und einlösbarem Protokoll statt Live-Verprobung).

---

_Verified: 2026-08-20T11:15:00Z_
_Verifier: Claude (gsd-verifier)_
