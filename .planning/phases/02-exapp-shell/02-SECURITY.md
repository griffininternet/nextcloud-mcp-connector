---
phase: 2
slug: exapp-shell
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-15
---

# Phase 2: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Restrisiken, Audit-Trail.
> Register-Quelle: die sieben threat_model-Bloecke der Plaene 02-01 bis 02-07 (State B,
> zur Planzeit erstellt). Verifiziert am 2026-08-15 durch gsd-security-auditor (opus)
> gegen Quelltext, Testlaeufe (263 Unit, 22 Integration live) und die laufende
> Topologie auf 127.0.0.1:8081.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| MCP-Client zu HaRP | Beliebiger Client sendet Nutzer-Credentials an die oeffentliche Route | App-Passwoerter (Basic) |
| HaRP zu ExApp | HaRP entscheidet die Identitaet; die ExApp glaubt nur dem AppAPI-Header | Aufgeloeste User-Id + APP_SECRET |
| ExApp zu Nextcloud | Impersonation; ACLs bleiben serverseitig | Nutzerdaten unter fremder Identitaet |
| Container/Supply-Chain | Image-Build, frp-Binaries, Registry | Build-Artefakte, Secrets in Env |
| Dokumentation zu Betreibern | Eine falsche Anleitung erzeugt eine unsichere Instanz | Konfigurationswissen |

---

## Threat Register

Alle 48 Positionen CLOSED (43 mitigate, 5 accept; T-02-09 transfer). Belege verkuerzt;
die vollstaendige Beweiskette steht im Audit-Bericht vom 2026-08-15 (siehe Audit Trail).

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-02-01 | Spoofing | exapp/auth.py | mitigate | compare_digest auf UTF-8-Bytes (auth.py:57,69,114-116) | closed |
| T-02-02 | Info Disclosure | exapp/auth.py | mitigate | kein == im Verifier, Quelltext-Gate test_exapp_auth.py:246 | closed |
| T-02-03 | Info Disclosure | auth/config | mitigate | AppApiRejected ohne Wert; ExAppSettings.__repr__ maskiert | closed |
| T-02-04 | DoS | exapp/lifecycle.py | mitigate | x-origin-ip-Guard, 404; kein Lifecycle-Pfad im Manifest | closed |
| T-02-05 | DoS | exapp/lifecycle.py | mitigate | /heartbeat prueft nichts (lifecycle.py:60-62) | closed |
| T-02-06 | Info Disclosure | exapp/lifecycle.py | mitigate | Body exakt {"status":"ok"}, Mengengleichheits-Test | closed |
| T-02-07 | Tampering | exapp/lifecycle.py | mitigate | zentrales _NO_STORE, Test auch fuer 400/401/404 | closed |
| T-02-08 | Elevation | entry_exapp.py | mitigate | SystemExit(2) bei Static-Bearer/App-Passwort-Env | closed |
| T-02-09 | Info Disclosure | nextcloud/http.py | transfer | follow_redirects=False, base_url aus Deploy-Umgebung | closed |
| T-02-10 | Elevation | deps.py | mitigate | resolve_credentials(ctx) mit genau einem Parameter | closed |
| T-02-11 | Spoofing | deps.py | mitigate | ExApp-Zweig liest Authorization nicht; live nachgestellt | closed |
| T-02-12 | Elevation | deps.py | mitigate | leere User-Id wird zu MCPError (deps.py:162-169) | closed |
| T-02-13 | Info Disclosure | credentials.py | mitigate | private _headers, eigene reprs, httpx-Logs auf WARNING | closed |
| T-02-14 | Info Disclosure | http.py | mitigate | follow_redirects=False, Basis-URL aus exapp_settings | closed |
| T-02-15 | Tampering | clients/ | mitigate | BasicAuth im Client-Paket = 0, creds.auth() = 20 | closed |
| T-02-16 | Tampering | ocs/deck/notes | mitigate | Header nur aus creds.auth(); Zaehl-Gate | closed |
| T-02-SC | Tampering | Dockerfile/start.sh | mitigate | frp 0.61.1 mit SHA256-Konstanten, sha256sum -c | closed |
| T-02-20 | DoS | appinfo/info.xml | mitigate | genau zwei enge Routen; Lifecycle von aussen 502 (live) | closed |
| T-02-21 | DoS | appinfo/info.xml | mitigate | kein bruteforce_protection-Element, kein 401 | closed |
| T-02-22 | Elevation | Dockerfile | mitigate | USER 10001:10001 (im Image nachgeprueft) | closed |
| T-02-23 | Info Disclosure | Dockerfile | mitigate | .dockerignore; Image-ENV ohne Secrets | closed |
| T-02-24 | Tampering | Dockerfile | mitigate | uv 0.11.7 gepinnt, uv sync --frozen gegen uv.lock | closed |
| T-02-25 | DoS | healthcheck.sh | mitigate | HEALTHCHECK inkl. frpc-Lebendpruefung (WR-05) | closed |
| T-02-26 | Info Disclosure | Image-Signatur | accept | OCI-Labels gesetzt; cosign dokumentiert auf Phase 5 | closed |
| T-02-30 | Info Disclosure | compose.exapp.yml | mitigate | Ports nur auf 127.0.0.1; HaRP ohne ports-Block | closed |
| T-02-31 | Elevation | compose.exapp.yml | accept | Docker-Socket-Risiko am Volume + in Doku begruendet | closed |
| T-02-32 | Tampering/Info | compose.exapp.yml | accept | Begruendung im Compose + Security notes der Doku | closed |
| T-02-33 | Info Disclosure | .env.exapp | mitigate | git-ignoriert; Beispieldatei nur Platzhalter | closed |
| T-02-34 | DoS | bootstrap_exapp.sh | mitigate | eigener Projektname/Volumes/Netz; kein Zugriff auf compose.test | closed |
| T-02-35 | Spoofing | bootstrap_exapp.sh | mitigate | vorhandenes APP_SECRET gepinnt, require_hex64 | closed |
| T-02-36 | DoS | HaRP-Routing | mitigate | Lifecycle-Pfade von aussen 502 (live gemessen) | closed |
| T-02-40 | Info Disclosure | exapp/discovery.py | mitigate | PRM-Body nur drei Felder; live bestaetigt | closed |
| T-02-41 | Spoofing | exapp/discovery.py | mitigate | nur config.public_url(env); Host-Header wirkungslos (live) | closed |
| T-02-42 | Tampering | exapp/discovery.py | mitigate | no-store gemerged statt ersetzt (IN-06-Fix); live geprueft | closed |
| T-02-43 | DoS | spike_discovery.sh | mitigate | PUBLIC-Messungen ohne Authorization | closed |
| T-02-44 | Info Disclosure | exapp/discovery.py | mitigate | Spike-Artefakt markiert, Probe-Body leer, Abbau notiert | closed |
| T-02-45 | DoS | Discovery-Routen | accept | Limitations dokumentiert; /mcp bleibt USER, anonym 403 | closed |
| T-02-50 | Elevation | DAV-Matrix | mitigate | bob auf alices Pfad = 404 (Integration, live gruen) | closed |
| T-02-51 | Spoofing | DAV-Matrix | mitigate | falsches APP_SECRET = 401; kein App-Passwort im Prozess | closed |
| T-02-52 | Tampering | DAV-Matrix | mitigate | zweites PUT = ConflictError (live gruen) | closed |
| T-02-53 | Info Disclosure | docs/spike-dav.md | mitigate | keine Token/hex64 im Dokument (gemessen) | closed |
| T-02-54 | Repudiation | Impersonations-Log | mitigate | user=alice/user=bob je Request belegt | closed |
| T-02-55 | Elevation | credentials.py | mitigate | unbekannter Modus wirft, kein Basic-Fallback | closed |
| T-02-60 | Elevation | Permission-Fidelity | mitigate | vier Lecktests + drei Positivkontrollen, live gruen | closed |
| T-02-61 | Spoofing | Permission-Fidelity | mitigate | Guard alice != bob vor allen Lecktests | closed |
| T-02-62 | Info Disclosure | docs/client-setup.md | mitigate | Stolperstellen benennen Proxy + Discovery mit Messverweis | closed |
| T-02-63 | Repudiation | docs/exapp-install.md | mitigate | AIO Fall B mit Abbruchgrund und Phase-5-Uebergabe | closed |
| T-02-64 | DoS | Abnahme | accept | disable/enable als Paar; Endzustand [enabled] live geprueft | closed |

*Status: open, closed*
*Disposition: mitigate (implementation required), accept (documented risk), transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-02-01 | T-02-26 | Image-Signierung (cosign) auf Phase 5 verschoben; OCI-Labels vorhanden | Owner (Plan 02-02) | 2026-08-15 |
| AR-02-02 | T-02-31 | Docker-Socket fuer HaRP-Deploy noetig; Wegwerf-Loopback-Topologie, Produktionshinweis in Doku | Owner (Plan 02-04) | 2026-08-15 |
| AR-02-03 | T-02-32 | Lokale Registry ohne TLS nur auf Loopback; Produktionshinweis in Doku | Owner (Plan 02-04) | 2026-08-15 |
| AR-02-04 | T-02-45 | Kein Rate-Limit auf den PUBLIC-Discovery-Routen; Antworten sind statisch und klein, /mcp bleibt USER | Owner (Plan 02-05) | 2026-08-15 |
| AR-02-05 | T-02-64 | Abnahme deaktiviert/aktiviert die App als Paar auf der Wegwerf-Instanz | Owner (Plan 02-07) | 2026-08-15 |
| AR-02-06 | (ohne Plan-ID, Audit) | Manifest-Route `^/\.well-known/` ist ein unverankertes PUBLIC-Praefix; haengt an Pfadnormalisierung von Caddy/Starlette. FUER PHASE 3 ENG FASSEN | Audit 2026-08-15 | 2026-08-15 |
| AR-02-07 | (ohne Plan-ID, Audit) | ALLOW_PLAINTEXT_FRP=1 als dokumentierter Opt-in sendet HP_SHARED_KEY im Klartext; Default ist Abbruch | Audit 2026-08-15 | 2026-08-15 |
| AR-02-08 | (ohne Plan-ID, Audit) | bootstrap_exapp.sh legt je Lauf ein neues App-Passwort an und widerruft keins; nur Wegwerf-Instanz | Audit 2026-08-15 | 2026-08-15 |
| AR-02-09 | (ohne Plan-ID, Audit) | Laengenunterschied der Secrets ueber compare_digest beobachtbar; 64-Zeichen-Hex, Inhalt leckt nicht | Audit 2026-08-15 | 2026-08-15 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-15 | 48 | 48 | 0 | gsd-security-auditor (opus), State B; Belege: Code-Zitate, 263 Unit- + 22 Integrationstests, Live-Checks gegen 127.0.0.1:8081 |

Hinweis aus dem Audit: Die SUMMARYs nutzen "## Threat Model Coverage" statt "## Threat
Flags"; neue Angriffsflaeche wurde deshalb aus Reviews und Code abgeleitet (AR-02-06 bis
AR-02-09). AR-02-06 ist als Arbeitsauftrag fuer Phase 3 markiert.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-15
