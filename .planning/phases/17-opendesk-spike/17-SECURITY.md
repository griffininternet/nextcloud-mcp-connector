---
phase: 17
slug: opendesk-spike
status: verified
threats_open: 0
asvs_level: 2
created: 2026-08-29
---

# Phase 17: Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfspur.

Besonderheit dieser Phase: Phase 17 war ein Spike ohne Produktionscode. Geschrieben
wurden ausschließlich eine Messtopologie (`compose.spike-opendesk.yml`,
`deploy/Caddyfile.spike-opendesk`, `scripts/bootstrap_spike_opendesk.sh`,
`.env.spike-opendesk.example`), der Bericht `docs/spike-opendesk.md` und drei
unversendete Entwürfe unter `docs/contrib/`. Der Produktionsbaum (`src/`,
`appinfo/`, `pyproject.toml`, `uv.lock`) blieb unberührt; das ist als T-17-04
geführt und mit leerem Diff belegt.

---

## Trust Boundaries

| Grenze | Beschreibung | Was sie überquert |
|--------|--------------|-------------------|
| Messumgebung zu Host | Sieben Container (Nextcloud 33.0.7, HaRP, OpenProject 17.7.2, Keycloak 26.7.0, Caddy, Registry, DB) auf einem Entwicklerrechner | Nur Loopback-Ports 8082, 8083, 8091 und 5001 |
| Repository zu Öffentlichkeit | Bericht und Entwürfe liegen im später öffentlichen Repository | Messwerte, Zitate aus fremdem Code, Verhandlungspositionen |
| Repository zu fremdem Kanal | Drei Entwürfe für Nextcloud-Forum, OpenProject-Community und `user_oidc#925` | Technische Aussagen über fremden Code |
| Nextcloud zu OpenProject | Weg 0 (AppAPI-Impersonation über `integration_openproject`) gegen Weg 1 (eigener OAuth-Client mit PKCE) | Zugriffstoken, Nutzeridentität, Arbeitspaketdaten |
| Geheimnisse zu verfolgten Dateien | Zwanzig OAuth-Werte, App-Secrets und Wegwerf-Passwörter entstanden während der Messung | Nichts: alles nur in der git-ignorierten `.env.spike-opendesk` |

---

## Threat Register

| Threat ID | Kategorie | Komponente | Disposition | Mitigation und Beleg | Status |
|-----------|-----------|------------|-------------|----------------------|--------|
| T-17-01 | Information Disclosure (hoch) | `docs/spike-opendesk.md`, `docs/contrib/`, `.env.spike-opendesk` | mitigate | Geheimnisse ausschließlich in der git-ignorierten Verbindungsdatei; Token nur als Länge und Vier-Zeichen-Präfix. Gate-Griff nach `eyJ`, `Bearer `, `refresh_token=`, `client_secret`, `GLOBAL__BASIC__AUTH`, `apikey:` über alle neun Artefakte: kein Treffer trägt einen Wert, `eyJ` null Treffer. Geheimnisregel `docs/spike-opendesk.md:1864`; `.env.spike-opendesk` in `.gitignore:17` und nicht im Baum von e780ce7. Zusätzlicher Entropie-Griff `[0-9a-f]{32,}` über alle Nicht-Bericht-Artefakte: null Treffer | closed |
| T-17-02 | Spoofing, Tampering (mittel) | Caddy, Registry, Nextcloud, OpenProject, Keycloak | mitigate (in 17-04 und 17-06 je ein Teilaspekt accept, siehe A-17-1 und A-17-2) | Genau zwei `ports:`-Blöcke (`compose.spike-opendesk.yml:45,194`), alle vier veröffentlichten Ports auf `127.0.0.1`; kein `network_mode`, kein `expose:`, kein `0.0.0.0`. `HP_SHARED_KEY:161` und `SECRET_KEY_BASE:228` als `${VAR:?}`, also fail-closed. OpenProject-Vorgabepasswort ersetzt (`docs/spike-opendesk.md:2015`). Abräumung per `down -v` gegengeprobt (`:2617-2619`, `:2625-2630`) | closed |
| T-17-03 | Elevation of Privilege (mittel) | OAuth-Anwendung, `integration_openproject`, Keycloak-Client `openproject` | mitigate | Öffentlicher Client, "Confidential" aus, "Client Credentials User" leer, kein `client_credentials`-Lauf trotz beworbenem Grant; `GLOBAL__BASIC__AUTH` null Treffer; `setup_app_password:false` mit Antwort `oPUserAppPassword: null` (`docs/spike-opendesk.md:336`), Ausschlussabsatz `:341`; Admin-Zugang an allen sieben Stellen als Aufbau markiert und aus der gemessenen Kette genommen (`:2007`, `:2011`) | closed |
| T-17-04 | Tampering (mittel) | Produktionsbaum `src/`, `appinfo/`, `pyproject.toml`, `uv.lock`, Werkzeugbudget | mitigate | `git diff --stat c7ddcea..e780ce7 -- src appinfo pyproject.toml uv.lock` ist leer (vom Auditor selbst ausgeführt). Phasen-Diff: neun Dateien, alle neu, keine unter `src/` oder `appinfo/`. Budget unverändert 15712 von 18000 Bytes über 21 Werkzeuge (`docs/spike-opendesk.md:2608`), Suite 2813 passed (`:2609`), Lint grün (`:2610`) | closed |
| T-17-05 | Repudiation (mittel) | Messwerte, Zitate aus fremdem Code | mitigate | Messwertdefinition mit Pflicht-Gegenprobe und Pflicht-Nutzername (`docs/spike-opendesk.md:32`); 76 Vorkommen "Gegenprobe", Rohwerttabellen führen sie als eigene Spalte (`:1886`, `:1907`); Fremdaussagen stets mit Repository, Tag, Datei und Zeile (`:95`, `:2295`) | closed |
| T-17-06 | Information Disclosure (niedrig bis mittel) | `occ log:manage --level 0`, `allow_insecure_http` | mitigate | Beide Lockerungen gelten einer Wegwerf-Instanz auf Loopback (`:2271`, `:2295`, `:2585`, `:2587`); der Bericht sagt unter "Was diese Messung nicht beweist" ausdrücklich, dass daraus keine Produktionsempfehlung wird (`:2591-2592`); der Zustand fällt mit dem Nextcloud-Band (`:2495`) | closed |
| T-17-07 | Repudiation (mittel) | Versand durch einen Agenten | mitigate | Alle drei Entwürfe tragen in Zeile 4 `Status: Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner.`; `scripts/bootstrap_spike_opendesk.sh` enthält kein `gh`, kein Playwright, keinen Browser, keinen SMTP-Versand und kein curl-Ziel außerhalb der Compose-Topologie (Mail-Zweig abgeschaltet, `:101-105`); unabhängig bestätigt in `17-VERIFICATION.md:52`. Owner sendet (D-11) | closed |
| T-17-SC | Tampering, Supply Chain (niedrig bis mittel) | Container-Bildmarken, Paketstand | mitigate (in 17-01 accept, weil dort kein Paket gezogen wurde) | `nextcloud:33.0.7-apache` (`compose.spike-opendesk.yml:89`), `openproject/openproject:17.7.2` (`:218`), `quay.io/keycloak/keycloak:26.7.0` (`:252`) gepinnt, kein `:latest` in der Datei; HaRP `:release` als deklarierter gleitender Tag mit Digest `sha256:3b335650` im Berichtskopf (`docs/spike-opendesk.md:12`); keine Installation aus npm, PyPI oder crates; `pyproject.toml` und `uv.lock` unverändert | closed |

*Status: open, closed*
*Disposition: mitigate (Umsetzung nötig), accept (dokumentiertes Risiko), transfer (Dritter)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Begründung | Angenommen von | Datum |
|---------|------------|------------|----------------|-------|
| A-17-1 | T-17-02 (Plan 17-04) | Der Loopback-Redirect `http://127.0.0.1:8099/callback` nimmt niemand an; der Code wird aus dem `Location`-Header gelesen. Kein Dienst hört auf dem Port, es gibt nichts zu übernehmen | Plan 17-04, bestätigt im Audit 29.08.2026 | 2026-08-28 |
| A-17-2 | T-17-02 (Plan 17-06) | Die Weg-0-Verbindung von `bob` bleibt nach der Gegenprobe absichtlich kaputt; der Zustand verschwand mit dem Nextcloud-Band beim `down -v`, `alice` blieb für Plan 17-07 unberührt | Plan 17-06, bestätigt im Audit 29.08.2026 | 2026-08-28 |
| A-17-3 | T-17-SC (Plan 17-01) | Phase 17 installierte kein Paket aus npm, PyPI oder crates; das openDesk-Archiv wurde nur gelesen und lag außerhalb des Repositories | Plan 17-01, bestätigt im Audit 29.08.2026 | 2026-08-28 |
| A-17-4 | T-17-02 (neu im Audit) | `NEXTCLOUD_ADMIN_PASSWORD` trägt in `compose.spike-opendesk.yml:118` einen fest eingetragenen Wegwerf-Wert. Getragen von der Loopback-Bindung und im Bericht begründet (`:46-48`); dieselbe Klasse wie die seit cd0e520 bestehenden Bootstrap-Vorgabewerte. Die Instanz existiert nach `down -v` nicht mehr | Audit 29.08.2026 | 2026-08-29 |
| A-17-5 | T-17-06 (neu im Audit) | `allow_local_remote_servers = true` als Lockerung der Messumgebung ist eine neue Fläche ohne eigene Register-Id, wurde aber in `17-05-SUMMARY.md` ausdrücklich als Eingriff offengelegt und fiel mit dem Band | Audit 29.08.2026 | 2026-08-29 |

---

## Warnungen ohne Blocker-Wirkung

Aus dem Audit 29.08.2026: keine offenen Bedrohungen, aber vor einer Wiederverwendung
der Messtopologie nachzuziehen.

| # | Fund | Ort | Einordnung |
|---|------|-----|------------|
| W-17-1 | `caddy:2` und `registry:2` sind gleitende Major-Tags ohne Digest, auch nicht im Berichtskopf | `compose.spike-opendesk.yml:43`, `:192` | Außerhalb des Registers, das nur drei Bildmarken plus HaRP nennt. Wegwerf-Topologie auf Loopback, inzwischen abgeräumt |
| W-17-2 | `KC_BOOTSTRAP_ADMIN_USERNAME` und `_PASSWORD` als schlichtes `${VAR}` statt `${VAR:?}` | `compose.spike-opendesk.yml:271-272` | Erfüllt die Formel "ohne Vorgabewert" wörtlich, ist aber nicht fail-closed wie die Geschwistervariablen in Zeile 161 und 228 |
| W-17-3 | `17-08-SUMMARY.md` und `17-09-SUMMARY.md` haben keinen Abschnitt `## Threat Flags` | beide Dateien | Prozesslücke in zwei von neun SUMMARYs. Die Threats dieser beiden Pläne wurden deshalb ausschließlich direkt gegen die Artefakte verifiziert, Ergebnis unverändert closed |

---

## Security Audit Trail

| Datum | Threats gesamt | Closed | Open | Ausgeführt von |
|-------|----------------|--------|------|----------------|
| 2026-08-29 | 8 | 8 | 0 | gsd-security-auditor (opus), State B aus PLAN- und SUMMARY-Artefakten |

Eigenständig ausgeführte Belege statt übernommener Behauptungen:
`git diff --stat c7ddcea..e780ce7 -- src appinfo pyproject.toml uv.lock` (leer),
`git ls-tree -r --name-only e780ce7` (nur `.env.spike-opendesk.example` im Baum),
`git check-ignore -v .env.spike-opendesk` (`.gitignore:17`), Geheimnis-Gate-Griff,
Entropie-Griff `[0-9a-f]{32,}`, Portanalyse und Bildmarken-Griff.

---

## Sign-Off

- [x] Alle Bedrohungen haben eine Disposition (mitigate, accept, transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (A-17-1 bis A-17-5)
- [x] `threats_open: 0` bestätigt
- [x] `status: verified` in der Frontmatter gesetzt

**Freigabe:** verified 2026-08-29
