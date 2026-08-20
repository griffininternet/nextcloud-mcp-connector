# Phase 6: Härtung, Eigennachweise und Conference-Reife - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning
**Source:** Bestehende Owner-Entscheidungen (BACKLOG.md BL-04/BL-05, v1.0-MILESTONE-AUDIT, Milestone-Zuschnitt vom 20.08.), kein neues Interview nötig

<domain>
## Phase Boundary

Alles aus v1.1, was ohne fremden Zugang beweisbar ist: CIMD als DCR-Alternative mit belegter SSRF-Grenze (AUTH-08/09), Cursor-Live-Nachweis nach der Teilregistrierung und die Loopback-Portfrage (CLIENT-04/05), der NC-34.0.3-UI-Smoke (EXAPP-06) und das Conference-Material (CONF-01/02). NICHT in dieser Phase: MUCGPT/F13/BaerGPT (Phase 7, extern getaktet).

</domain>

<decisions>
## Implementation Decisions

### CIMD (AUTH-08, BL-05)
- CIMD ergänzt DCR, ersetzt es nicht: beide Wege koexistieren, DCR bleibt für Claude.ai/ChatGPT unangetastet
- Die DCR-Kontrollen gelten wortgleich für CIMD: Redirect-URI-Prüfung (D-35: nur https und Loopback), Allowlist-Modus aus AUTH-07 greift an denselben vier Punkten, ein abgeschaltetes DCR darf über CIMD NICHT umgehbar sein (eigener Admin-Schalter oder derselbe, Entscheid beim Planen anhand der AUTH-07-Policy-Struktur)
- Kandidat-Client für den Live-Nachweis: Claude Code (nutzt CIMD laut 03-RESEARCH)

### SSRF-Grenze des CIMD-Abrufs (AUTH-09)
- Fail-closed, hoechste Sicherheit (Owner-Leitplanke aus [[exapp-auth-hoechste-sicherheit]], gilt fort): nur https, keine privaten/link-lokalen/Loopback-Ziele (auch nach DNS-Aufloesung, Rebinding bedenken), Groessen- und Zeitlimit, kontrolliertes Caching, keine Redirect-Folge ohne erneute Zielpruefung
- Jede Grenze braucht einen Negativtest (Owner-Regel: nie nur Happy Path)

### Lokale Clients (CLIENT-04/05, BL-04-Rest)
- Teilregistrierung ist ENTSCHIEDEN und implementiert (Commit a80af0a): unzulaessige redirect_uris werden verworfen, zulaessige registriert; Cursor-Drei-URI-Body wird 201
- D-35 STEHT: private-use Schemes (cursor://...) bleiben unregistrierbar, wird nicht neu verhandelt
- CLIENT-04 ist reine Messarbeit: echter Cursor gegen die Instanz, DCR 201, Autorisierung, Tool-Aufruf; Messdatei neben den anderen Client-Nachweisen
- CLIENT-05: erst messen (Client mit wechselndem 127.0.0.1-Port, Kandidat Claude Code), dann entscheiden; die RFC-8252-7.3-Ausnahme (beliebiger Port auf 127.0.0.1 bei exaktem Rest-Match) ist die erwartbare Loesung, aber Umsetzung nur wenn die Messung das Problem bestaetigt; sonst als akzeptiertes Risiko dokumentieren

### NC-34.0.3-UI-Smoke (EXAPP-06)
- Hintergrund: NC 34.0.2 zeigte in der Store-UI GAR KEINE ExApps (Frontend-Bug, Ursachenkette in docs/exapp-install.md); Upstream-Fix in 34.0.3 (app_api#971, server#61709, PR 62276)
- Die Wegwerf-Topologie 127.0.0.1:8081 laeuft noch (Nutzer jane, 2 echte OAuth-Verbindungen) und ist das vorgesehene Testbett; Instanz auf 34.0.3 aktualisieren oder frisch aufsetzen ist Claude's Discretion
- Doku und Store-Text sagen danach GENAU das Gemessene, kein Ein-Klick-Versprechen ohne Deckung
- Bei README-/Store-Text-Aenderung: EN/DE/FR-Fassungen immer zusammen nachziehen (Owner-Regel, echte Umlaute/Accents, keine Em-Dashes)

### Conference-Material (CONF-01/02)
- Demo-Strecke: Verbindung, Tool-Aufrufe, Per-User-Verwaltung, Widerruf gegen eine laufende Instanz, mit Drehbuch; ein Dritter muss sie nachfahren koennen
- Lightning-Talk: Entwurf (Folien + Sprechzettel); ob eingereicht wird, entscheidet der OWNER, nicht wir
- Sprache Conference-Material: Englisch (internationales Nextcloud-Publikum, wie Code/README)
- Stil: keine Emojis, keine Em-Dashes; Kern-Narrativ = die vier Differenzierer (Store-Ein-Klick, Spec-OAuth, Per-User-Verwaltung, kann konstruktionsbedingt nichts zerstoeren)

### Betriebsregeln (gelten fort)
- Store-Release nur mit Owner-Freigabe; Milestone-Tags NIE als v* (release.yml triggert auf v*); ein etwaiges 0.1.3 traegt den F2-Fix (serverInfo.version aus __version__) bereits im Repo
- Vokabular-Gate: "archiv" in public Artefakten verboten (auch changelog.ts); Gate vor Push laufen lassen
- ruff check . + ruff format --check . uebers GANZE Repo vor Push; Code-Qualitaet wie v1.0 (pyright, vulture, Gates)
- Commits als street1983nk, keine Co-Authored-By-Trailer

### Claude's Discretion
- Aufbau/Update der Testtopologie fuer den UI-Smoke (Update vs. frisch)
- CIMD-Implementierungsdetails (Modul-Schnitt, Cache-Struktur), solange die Policy-Punkte oben gelten
- Demo-Drehbuch-Form (Markdown-Skript vs. Shell-Runbook) und Folien-Werkzeug
- Reihenfolge der Plaene und Wellen

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CIMD und lokale Clients
- `.planning/BACKLOG.md` — BL-04 (Teilregistrierung DONE, Loopback-Portfrage offen) und BL-05 (CIMD-Anforderungen, SSRF-Hinweis) im Wortlaut
- `docs/client-setup.md` — bestehende Client-Nachweise und deren Messdatei-Muster
- `docs/oauth-setup.md` — E2E-Belege Claude.ai/ChatGPT, well-known-Verhalten

### Store/UI-Smoke
- `docs/exapp-install.md` — Ursachenkette NC-34-Store-UI-Bug + Hinweis auf 34.0.3-Fix
- `docs/store-submission.md` — Store-Upload-Runbook (Schritt 7: Browser-Session reicht)

### Milestone-Rahmen
- `.planning/milestones/v1.0-MILESTONE-AUDIT.md` — F1/F2-Befunde (Cursor-Live-Nachweis offen, serverInfo.version)
- `.planning/REQUIREMENTS.md` — v1.1-Requirements im Wortlaut

</canonical_refs>

<specifics>
## Specific Ideas

- Cursors gemessener Drei-URI-Body (aus 03-09-MEASUREMENTS, historisch): `cursor://anysphere.cursor-mcp/oauth/callback`, `https://www.cursor.com/agents/mcp/oauth/callback`, `http://localhost:8787/callback` — Teilregistrierung muss die letzten beiden annehmen
- Wegwerf-Topologie: Projekt nc-mcp-exapp, Port 8081, Nutzer jane (Jane Fischer), 2 OAuth-Verbindungen (Claude Desktop, Open WebUI via DCR+PKCE) — nuetzlich fuer UI-Smoke und Demo
- Vorhandene Muster wiederverwenden: MEASUREMENTS-Dateien der Phase-5-Plaene als Vorlage fuer die Messdateien

</specifics>

<deferred>
## Deferred Ideas

- MUCGPT/F13/BaerGPT-Verprobung → Phase 7 (extern getaktet)
- Token Exchange fuer MUCGPT-Per-User-Identitaet → Future (haengt an it@M-Antwort)
- Store-Release 0.1.3 → nur falls diese Phase releasenotwendige Aenderungen produziert UND Owner freigibt

</deferred>

---

*Phase: 06-h-rtung-eigennachweise-und-conference-reife*
*Context gathered: 2026-08-20 aus bestehenden Owner-Entscheidungen*
