# Phase 6: Härtung, Eigennachweise und Conference-Reife - Research

**Researched:** 2026-08-20
**Domain:** OAuth 2.1 Authorization Server (CIMD nach MCP-Spec 2026-07-28), SSRF-gehärteter Outbound-Abruf in Python/httpx, RFC-8252-Loopback-Matching, Nextcloud-34.0.3-Store-UI, Conference-Material
**Confidence:** HIGH (Spec, SDK-Lage, Codebasis, NC-Versionen alle in dieser Session gemessen); MEDIUM bei der Frage, ob der Upstream-Fix in 34.0.3 wirklich wirkt (statisch nicht belegbar, siehe Open Question 1)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CIMD (AUTH-08, BL-05)**
- CIMD ergänzt DCR, ersetzt es nicht: beide Wege koexistieren, DCR bleibt für Claude.ai/ChatGPT unangetastet
- Die DCR-Kontrollen gelten wortgleich für CIMD: Redirect-URI-Prüfung (D-35: nur https und Loopback), Allowlist-Modus aus AUTH-07 greift an denselben vier Punkten, ein abgeschaltetes DCR darf über CIMD NICHT umgehbar sein (eigener Admin-Schalter oder derselbe, Entscheid beim Planen anhand der AUTH-07-Policy-Struktur)
- Kandidat-Client für den Live-Nachweis: Claude Code (nutzt CIMD laut 03-RESEARCH)

**SSRF-Grenze des CIMD-Abrufs (AUTH-09)**
- Fail-closed, hoechste Sicherheit (Owner-Leitplanke aus [[exapp-auth-hoechste-sicherheit]], gilt fort): nur https, keine privaten/link-lokalen/Loopback-Ziele (auch nach DNS-Aufloesung, Rebinding bedenken), Groessen- und Zeitlimit, kontrolliertes Caching, keine Redirect-Folge ohne erneute Zielpruefung
- Jede Grenze braucht einen Negativtest (Owner-Regel: nie nur Happy Path)

**Lokale Clients (CLIENT-04/05, BL-04-Rest)**
- Teilregistrierung ist ENTSCHIEDEN und implementiert (Commit a80af0a): unzulaessige redirect_uris werden verworfen, zulaessige registriert; Cursor-Drei-URI-Body wird 201
- D-35 STEHT: private-use Schemes (cursor://...) bleiben unregistrierbar, wird nicht neu verhandelt
- CLIENT-04 ist reine Messarbeit: echter Cursor gegen die Instanz, DCR 201, Autorisierung, Tool-Aufruf; Messdatei neben den anderen Client-Nachweisen
- CLIENT-05: erst messen (Client mit wechselndem 127.0.0.1-Port, Kandidat Claude Code), dann entscheiden; die RFC-8252-7.3-Ausnahme (beliebiger Port auf 127.0.0.1 bei exaktem Rest-Match) ist die erwartbare Loesung, aber Umsetzung nur wenn die Messung das Problem bestaetigt; sonst als akzeptiertes Risiko dokumentieren

**NC-34.0.3-UI-Smoke (EXAPP-06)**
- Hintergrund: NC 34.0.2 zeigte in der Store-UI GAR KEINE ExApps (Frontend-Bug, Ursachenkette in docs/exapp-install.md); Upstream-Fix in 34.0.3 (app_api#971, server#61709, PR 62276)
- Die Wegwerf-Topologie 127.0.0.1:8081 laeuft noch (Nutzer jane, 2 echte OAuth-Verbindungen) und ist das vorgesehene Testbett; Instanz auf 34.0.3 aktualisieren oder frisch aufsetzen ist Claude's Discretion
- Doku und Store-Text sagen danach GENAU das Gemessene, kein Ein-Klick-Versprechen ohne Deckung
- Bei README-/Store-Text-Aenderung: EN/DE/FR-Fassungen immer zusammen nachziehen (Owner-Regel, echte Umlaute/Accents, keine Em-Dashes)

**Conference-Material (CONF-01/02)**
- Demo-Strecke: Verbindung, Tool-Aufrufe, Per-User-Verwaltung, Widerruf gegen eine laufende Instanz, mit Drehbuch; ein Dritter muss sie nachfahren koennen
- Lightning-Talk: Entwurf (Folien + Sprechzettel); ob eingereicht wird, entscheidet der OWNER, nicht wir
- Sprache Conference-Material: Englisch (internationales Nextcloud-Publikum, wie Code/README)
- Stil: keine Emojis, keine Em-Dashes; Kern-Narrativ = die vier Differenzierer (Store-Ein-Klick, Spec-OAuth, Per-User-Verwaltung, kann konstruktionsbedingt nichts zerstoeren)

**Betriebsregeln (gelten fort)**
- Store-Release nur mit Owner-Freigabe; Milestone-Tags NIE als v* (release.yml triggert auf v*); ein etwaiges 0.1.3 traegt den F2-Fix (serverInfo.version aus __version__) bereits im Repo
- Vokabular-Gate: "archiv" in public Artefakten verboten (auch changelog.ts); Gate vor Push laufen lassen
- ruff check . + ruff format --check . uebers GANZE Repo vor Push; Code-Qualitaet wie v1.0 (pyright, vulture, Gates)
- Commits als street1983nk, keine Co-Authored-By-Trailer

### Claude's Discretion
- Aufbau/Update der Testtopologie fuer den UI-Smoke (Update vs. frisch)
- CIMD-Implementierungsdetails (Modul-Schnitt, Cache-Struktur), solange die Policy-Punkte oben gelten
- Demo-Drehbuch-Form (Markdown-Skript vs. Shell-Runbook) und Folien-Werkzeug
- Reihenfolge der Plaene und Wellen

### Deferred Ideas (OUT OF SCOPE)
- MUCGPT/F13/BaerGPT-Verprobung -> Phase 7 (extern getaktet)
- Token Exchange fuer MUCGPT-Per-User-Identitaet -> Future (haengt an it@M-Antwort)
- Store-Release 0.1.3 -> nur falls diese Phase releasenotwendige Aenderungen produziert UND Owner freigibt
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-08 | Ein CIMD-Client kann sich verbinden; die DCR-Kontrollen gelten unveraendert (Redirect-URI-Pruefung, Allowlist AUTH-07, abgeschaltetes DCR nicht umgehbar) | Spec-Anforderungen vollstaendig extrahiert (Standard Stack, Architecture Pattern 1); `provider.get_client` als einziger Einhaengepunkt gemessen; `clients`-Tabelle-FK-Zwang identifiziert (Pitfall 3); Advertise-Feld `client_id_metadata_document_supported` im SDK-Modell vorhanden (Pattern 2) |
| AUTH-09 | Der CIMD-Dokumentabruf ist SSRF-geprueft und fail-closed; Negativtests belegen jede Grenze | Gemessene `ipaddress`-Flag-Tabelle mit drei Luecken (Pattern 3); `sni_hostname`-IP-Pinning in httpcore 1.0.9 verifiziert; 5-KB-Limit aus Draft §6.6; Negativtest-Katalog (Common Pitfalls, Code Examples) |
| CLIENT-04 | Cursor verbindet sich live nach der Teilregistrierung (DCR 201, Autorisierung, Tool-Aufruf) | Messdatei-Muster aus Git-Historie rekonstruiert (Pattern 6); Cursor-Drei-URI-Body und der bereits gebaute Teilregistrierungs-Pfad in `provider.register_client` gelesen |
| CLIENT-05 | Die Loopback-Portfrage ist beantwortet, Entscheid dokumentiert und umgesetzt oder als Risiko akzeptiert | **Vorab beantwortet:** Claude Codes CIMD-Dokument nennt portlose Loopback-URIs, Laufzeit nutzt Port 3118/variabel (Pattern 4); RFC 8252 §7.3 ist ein **MUST**, nicht eine Ausnahme; genau ein Enforcement-Punkt (`consent.py:236`), Token-Endpunkt braucht keine Aenderung (gemessen an SDK `token.py:164-183`) |
| EXAPP-06 | Auf 34.0.3 ist nachgewiesen, ob die Store-UI Install-/Remove-Knopf zeigt; Doku und Store-Text sagen danach das Gemessene | Docker-Tag `34.0.3-apache` verifiziert und lokal vorhanden; laufende Instanz auf 34.0.2.1 gemessen; Backport-PR #62881 mit Milestone 34.0.3 verifiziert; statische Gegenprobe ergebnislos -> Messung ist der einzige Beweis (Open Question 1) |
| CONF-01 | Reproduzierbare Demo-Strecke mit Drehbuch gegen eine laufende Instanz | Laufende Topologie inventarisiert (Runtime State Inventory); `scripts/oauth_flow_check.py` und `scripts/acceptance_all_tools.py` als vorhandene Bausteine identifiziert |
| CONF-02 | Lightning-Talk-Entwurf (Folien + Sprechzettel) liegt vor | Conference-Fakten verifiziert: 19.-20.09.2026, CIC Berlin, Lightning Talk = **5 Minuten**. **CfP ist seit 03.08.2026 GESCHLOSSEN** (Open Question 2) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Diese Direktiven sind fuer den Planer bindend, gleichrangig mit den Locked Decisions:

| Direktive | Quelle | Wirkung auf Phase 6 |
|-----------|--------|---------------------|
| Timeline: v1 vor der Nextcloud Conference September 2026, harte Deadline, notfalls Scope kuerzen, nie den Termin | PROJECT | Conference ist 19.-20.09.2026. Kalendarisch 30 Tage. Der Scope-Puffer liegt bei CONF-02 und CLIENT-05, nicht bei AUTH-09 |
| Tech stack: Python 3.13 + offizielles MCP-SDK (`mcp>=2.0,<3`), uv als Toolchain (System-Python defekt) | PROJECT | Jeder Befehl laeuft ueber `uv run`. Kein FastMCP, keine zweite Auth-Schicht |
| Lizenz AGPL-3.0, Repo public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab) | PROJECT | Commits als street1983nk. Alle Artefakte dieser Phase sind oeffentlich -> Vokabular-Gate |
| Solo-Betrieb: Wartungsaufwand pro Feature zaehlt, kuratiert schlank schlaegt breit | PROJECT | Kein generischer CIMD-Client-Store, keine Cache-Bibliothek. Ein Modul, eine Tabelle |
| Sprache: Code/README Englisch, Projektkommunikation Deutsch; keine Em-Dashes, echte Umlaute | PROJECT | Conference-Material Englisch. Messdateien Deutsch (Muster der Phase 5) |
| Security: Der MCP darf nie mehr sehen als der angemeldete Nutzer; keine destruktiven Writes in v1 | PROJECT | Unveraendert. CIMD aendert die Identitaetsbruecke nicht, nur wer als Client gilt |
| SDK-`auth_server_provider=` ist fuer neue Server explizit abgeraten; eigene AS-Routen + `token_verifier=` | STACK | Der CIMD-Pfad wird an `NextcloudOAuthProvider.get_client` gebaut, nicht an einer SDK-Erweiterung |
| Eigener Code nutzt `httpx`, nicht `httpx2` (das ist transitive mcp-Dependency) | STACK / Phase-01-Entscheidung | Der CIMD-Fetch nutzt `httpx` 0.28.1, damit `respx` ihn mocken kann |
| GSD-Workflow: keine direkten Repo-Edits ausserhalb eines GSD-Kommandos | WORKFLOW | Gilt fuer die Ausfuehrung, nicht fuer diese Recherche |

Weitere bindende Regeln aus den globalen Owner-Regeln, die in dieser Phase greifen:
- **Tests: alle Paths** (nicht nur Happy Path: Fehler/Edge/Negativ/no_data). Bei AUTH-09 ist das die Requirement-Formulierung selbst.
- **Copy-paste im Code-Block**: Kopier-Texte immer im Code-Block. Relevant fuer das Demo-Drehbuch.
- **Doku-Seite mitziehen**: nach API-/Verhaltensaenderung `docs/` und `openapi` anpassen. CIMD aendert das AS-Metadatendokument -> `docs/oauth-setup.md` muss mit.
- **Immer committen** nach jedem Edit, ohne Fragen.
- **CRLF-Dateien mit Python editieren**: `.gitattributes` existiert, vor Massen-Edits pruefen.

---

## Summary

Diese Phase hat **genau ein Stueck echtes Neuland** (CIMD als Authorization-Server-Haelfte) und vier Punkte, die vor allem Messarbeit und Textpflege sind. Die gute Nachricht zuerst: der Einhaengepunkt fuer CIMD ist in dieser Codebasis bereits gebaut, ohne dass jemand CIMD im Sinn hatte. `NextcloudOAuthProvider.get_client(client_id)` ist der eine Ort, durch den jeder Client jedes Endpunkts geht (SDK-`/authorize` an zwei Stellen, `HashedClientAuthenticator` fuer `/token` und `/revoke`, und die eigene Consent-Strecke in `oauth/consent.py`). Ein `client_id`, der eine https-URL ist und im Store fehlt, kann dort aufgeloest werden, und alle vier AUTH-07-Enforcement-Punkte greifen danach unveraendert weiter, weil sie hinter derselben Funktion liegen. Das ist die billigste denkbare Integration und sie erfuellt die Locked Decision "die DCR-Kontrollen gelten wortgleich" von selbst statt durch Wiederholung.

Die zweite Nachricht ist unangenehmer und aendert die Reihenfolge der Plaene: **CIMD und die Loopback-Portfrage sind nicht zwei Themen, sondern eines.** Claude Codes CIMD-Dokument (`https://claude.ai/oauth/claude-code-client-metadata`, in dieser Session abgerufen) nennt als `redirect_uris` genau zwei portlose Adressen, `http://localhost/callback` und `http://127.0.0.1/callback`. Zur Laufzeit bindet Claude Code aber auf Port 3118 (Default, ueberschreibbar per `MCP_OAUTH_CALLBACK_PORT`, mit Zufallsport als Rueckfall) und schickt `http://localhost:3118/callback`. Ein Server, der exakt vergleicht, lehnt das ab, und genau das ist bei anderen Anbietern als Regression aufgeschlagen (anthropics/claude-code#37747). Ein CIMD-Pfad ohne die RFC-8252-§7.3-Regel ist deshalb ein CIMD-Pfad, an dem der Kandidat-Client nicht ankommt. Und §7.3 ist kein Kann: der Wortlaut ist "The authorization server **MUST** allow any port to be specified at the time of the request for loopback IP redirect URIs". CLIENT-05 ist damit schon vor der Messung beantwortet; die Messung bestaetigt nur noch und liefert die Zahlen. Erfreulich klein ist der Eingriff: der Vergleich passiert an genau einer Stelle im eigenen Code (`oauth/consent.py:236`, `client.validate_redirect_uri`), weil der SDK-Token-Endpunkt die Rueckadresse gegen den **gespeicherten** Wert des Auth-Codes vergleicht und nicht gegen die Registrierung (gelesen in `mcp/server/auth/handlers/token.py:164-183`).

Die dritte Nachricht betrifft AUTH-09 und ist eine Messung, kein Zitat: Pythons `ipaddress`-Modul allein reicht nicht. Auf dem Python 3.13.13 dieses Projekts ist `is_private` **False** fuer `100.64.0.1` (CGNAT) und fuer `64:ff9b::7f00:1` (NAT64, das 127.0.0.1 einbettet), waehrend `is_global` **True** ist fuer `224.0.0.1` (Multicast). Kein einzelnes Flag traegt die Grenze. Die belastbare Regel ist eine Konjunktion, und sie steht unten als Code-Beispiel. Dazu kommt, dass eine einmalige Zielpruefung mit anschliessendem httpx-Aufruf ein TOCTOU-Loch ist (DNS-Rebinding, in 2026 mehrfach als CVE-Klasse aufgeschlagen, u.a. CVE-2026-55391); die verifizierte Loesung ist IP-Pinning ueber die `sni_hostname`-Extension, die das installierte httpcore 1.0.9 unterstuetzt.

Fuer EXAPP-06 ist die Infrastruktur besser als erwartet und der Beweis schwaecher: das Image `nextcloud:34.0.3-apache` liegt bereits lokal und traegt verifiziert 34.0.3.2, der Backport-PR nextcloud/server#62881 ist am 04.08. in `stable34` mit Milestone "Nextcloud 34.0.3" gemergt. Aber ein Datei-fuer-Datei-Vergleich der `appstore`-App zwischen dem 34.0.2- und dem 34.0.3-Image zeigt **ausserhalb der Uebersetzungen keinen einzigen Unterschied**, und die App-Version bleibt in beiden 1.0.0. Der Fix ist statisch nicht nachweisbar. Das entwertet EXAPP-06 nicht, es begruendet es: nur der Blick in die laufende UI entscheidet, und kein Doku-Satz darf vor dieser Messung geschrieben werden.

Und ein Fund, der eine Owner-Entscheidung braucht, bevor CONF-02 geplant wird: **der Call for Speakers der Nextcloud Community Conference 2026 ist seit dem 03.08.2026 geschlossen** ("The call for proposals closed on August 3"), 17 Tage vor dieser Recherche. Angenommene Sprecher liefern ihre Folien bis zum 09.09. Der Lightning-Talk-Entwurf bleibt sinnvoll (Contributor Week 21.-25.09., wiederverwendbares Pitch-Material, naechster Termin), aber die Formulierung "ob eingereicht wird, entscheidet der Owner" hat derzeit keinen offenen Einreichungsweg.

**Primary recommendation:** CIMD an `provider.get_client` einhaengen, nicht neben dem SDK; die RFC-8252-§7.3-Loopback-Regel als Voraussetzung von AUTH-08 planen und nicht als Folge von CLIENT-05; den SSRF-Fetch als eigenes Modul mit gepinnter IP (`sni_hostname`), 5-KB-Grenze und `follow_redirects=False` bauen; EXAPP-06 als reine Messung mit Doku-Nachlauf; und CONF-02 vor dem Planen mit dem Owner klaeren, weil der CfP zu ist.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CIMD-Client-Aufloesung (URL-`client_id` -> Client-Objekt) | API / Backend (`oauth/provider.py`, `get_client`) | Database / Storage (`clients`-Tabelle als FK-Anker) | `get_client` ist der eine Punkt, den SDK-`/authorize`, `/token`, `/revoke` und die eigene Consent-Strecke gemeinsam durchlaufen. Jede andere Stelle waere eine zweite Wahrheit |
| CIMD-Dokumentabruf (Outbound HTTPS) | API / Backend (neues Modul, z.B. `oauth/cimd.py`) | — | Ein Outbound-Request aus der Instanz heraus in eine fremde Vertrauensdomaene. Gehoert nicht in `nextcloud/http.py` (das ist der Weg zur eigenen Nextcloud) und nicht in `provider.py` (das ist Policy, nicht Transport) |
| SSRF-Zielvalidierung + IP-Pinning | API / Backend (eigener httpx-Transport im CIMD-Modul) | — | Muss auf der Connect-Ebene sitzen, sonst ist zwischen Pruefung und Verbindung ein Rebinding-Fenster |
| CIMD-Cache (positiv und negativ) | Database / Storage (Store-Tabelle) oder Prozess (Closure) | — | Modul-globaler veraenderlicher Zustand ist im Produktionscode verboten (Phase-01-Entscheidung, D-20). Also entweder Store-Tabelle oder Closure der Routen-Fabrik, wie `store_opener` |
| Redirect-URI-Regel D-35 (was registrierbar ist) | API / Backend (`oauth/registry.py`, `redirect_uri_allowed`) | — | Schon vorhanden und fuer CIMD unveraendert gueltig: Claude Codes portlose Loopback-Eintraege passieren die Funktion bereits |
| Loopback-Port-Matching RFC 8252 §7.3 (was im Request akzeptiert wird) | API / Backend (`oauth/consent.py`, die eine `validate_redirect_uri`-Stelle) | — | Der SDK-Token-Endpunkt vergleicht gegen den gespeicherten Auth-Code-Wert, nicht gegen die Registrierung. Also genau ein Ort |
| AUTH-07-Policy (DCR-Schalter, Allowlist) | API / Backend (`oauth/registry.py`, `ClientPolicy`) | — | Unveraendertes Policy-Objekt. CIMD braucht nur eine Frage mehr, keine zweite Policy |
| Consent-Anzeige fuer CIMD-Clients (Hostname, Loopback-Warnung) | Frontend Server (SSR) (`exapp/ui/consent.py`, `exapp/ui/layout.py`) | — | Spec-Pflicht: "MUST clearly display the redirect URI hostname", "SHOULD display additional warnings for localhost-only redirect URIs". Jede Seite entsteht in `layout.page()` (Phase-03-Entscheidung) |
| AS-Metadaten-Advertising (`client_id_metadata_document_supported`) | API / Backend (`oauth/metadata.py`) | — | Dort werden schon `authorization_response_iss_parameter_supported` und die Auth-Methoden nachgesetzt |
| NC-34.0.3-Store-UI | CDN / Static (Nextcloud-Frontend, fremd) | — | Nicht unser Code. Reine Messung plus Textpflege |
| Conference-Material | Docs (Repo) | — | Kein Laufzeitanteil |

---

## Standard Stack

### Der wichtigste Befund: diese Phase braucht kein neues Paket

Alle Bausteine sind vorhanden oder in der Standardbibliothek. Das ist keine Sparmassnahme, sondern das Ergebnis der Recherche:

| Aufgabe | Was benutzt wird | Warum kein Paket |
|---------|------------------|------------------|
| IP-Klassifikation | `ipaddress` (stdlib, Python 3.13.13) | Vollstaendig, aber mit drei gemessenen Luecken -> siehe Pattern 3. Ein Paket haette dieselben Luecken plus Update-Risiko |
| DNS-Aufloesung | `anyio.getaddrinfo` (anyio 4.14.2, bereits transitiv) | Async, gibt alle Adressen zurueck, kein `socket.gethostbyname` (nur die erste, nur IPv4) |
| Outbound-HTTPS mit IP-Pinning | `httpx` 0.28.1 + `httpcore` 1.0.9 `sni_hostname`-Extension | In dieser Session verifiziert: `httpcore/_async/connection.py:107` liest `request.extensions["sni_hostname"]` und gibt sie als `server_hostname` an den TLS-Handshake |
| Groessenbegrenztes Lesen | `response.aiter_bytes()` + Zaehler, Muster von `exapp/responses.bounded_body` | Das Haus-Muster steht schon (IN-01-Fix), nur die Response-Seite fehlt |
| JSON-Validierung der Metadaten | `mcp.shared.auth.OAuthClientInformationFull` (pydantic) | Genau das Modell, das `get_client` zurueckgeben muss. Ein zweites Modell waere eine zweite Wahrheit |
| Tests gegen den Fetch | `respx` 0.23.1 (mockt `httpx`, nicht `httpx2`) | Der Grund, warum eigener Code auf `httpx` bleibt (Phase-01-Entscheidung) |

### Core (unveraendert, zur Vollstaendigkeit)

| Library | Version (verifiziert) | Purpose | Why Standard |
|---------|----------------------|---------|--------------|
| mcp | 2.0.0 | MCP-Server + OAuth-RS-Haelfte + AS-Handler-Bausteine | [VERIFIED: `importlib.metadata.version('mcp')` == 2.0.0 in `.venv`] |
| httpx | 0.28.1 | Async-HTTP fuer alle eigenen Outbound-Calls | [VERIFIED: installiert] |
| httpcore | 1.0.9 | Transport unter httpx, traegt `sni_hostname` | [VERIFIED: installiert, Extension im Quelltext geprueft] |
| respx | 0.23.1 | httpx-Mocking in Tests | [VERIFIED: installiert] |
| anyio | 4.14.2 | Async-Primitiven, `getaddrinfo` | [VERIFIED: installiert] |
| httpx2 | 2.10.0 | **Nur transitiv** ueber mcp. Eigener Code beruehrt es nicht | [VERIFIED: installiert, Phase-01-Entscheidung dokumentiert] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Eigener SSRF-gehaerteter Transport | Ein SSRF-Guard-Paket von PyPI | Diese Klasse Pakete hatte 2026 selbst Rebinding-CVEs (crewai-tools, datamodel-code-generator, mlflow, prefect). Eine 40-Zeilen-Funktion, die man auditieren kann, ist hier ehrlicher als eine Abhaengigkeit, die man nicht liest [CITED: github.com/PrefectHQ/prefect/pull/21591, advisories.gitlab.com CVE-2026-55391] |
| CIMD-Cache in einer Store-Tabelle | `functools`-TTL-Cache im Prozess | Ein Prozess-Cache ist modul-globaler veraenderlicher Zustand und damit gegen die Phase-01-Regel; ein Cache in der Closure der Routen-Fabrik waere erlaubt (Muster `store_opener`), verliert aber beim Neustart und beim zweiten Worker. Die Store-Tabelle ist die konsistente Wahl, weil `clients` fuer den FK ohnehin eine Zeile braucht |
| `client_id_metadata_document_supported` als eigener Admin-Schalter | Denselben Schalter wie DCR (`NC_MCP_OAUTH_DCR`) benutzen | Locked Decision laesst beides offen. Empfehlung unten in Pattern 2, mit Begruendung |
| RFC-8252-§7.3-Regel nur fuer IP-Literale | Auch fuer `localhost` | RFC 8252 §7.3 spricht von "loopback IP redirect URIs" und §8.3 raet von `localhost` ab. Claude Code schickt zur Laufzeit aber `localhost`. Eine buchstabengetreue Umsetzung laesst den Kandidat-Client draussen -> siehe Pattern 4 |

**Installation:** keine. Kein `uv add`, kein `uv lock` in dieser Phase, wenn die Empfehlungen befolgt werden.

## Package Legitimacy Audit

**Diese Phase installiert keine externen Pakete.** Der Standard Stack besteht ausschliesslich aus der Python-Standardbibliothek und Paketen, die bereits in `uv.lock` stehen und in v1.0 auditiert wurden (`docs/dependency-audit.md`).

| Package | Registry | Status | Disposition |
|---------|----------|--------|-------------|
| *(keine neuen)* | — | — | — |

**Packages removed due to slopcheck [SLOP] verdict:** none (nichts zu pruefen)
**Packages flagged as suspicious [SUS]:** none

*Sollte ein Plan wider Erwarten ein Paket brauchen (z.B. eine Folien-Toolchain fuer CONF-02), gilt das Package-Legitimacy-Gate voll: slopcheck, PyPI-JSON-API statt HTML-Projektseite (Phase-01-Entscheidung: die HTML-Seite liefert wegen Bot-Challenge auch fuer freie Namen 200), und Owner-Freigabe wie bei `cryptography` in 03-02. Empfehlung: Folien als HTML/Markdown im Repo, damit die Frage nicht entsteht.*

---

## Architecture Patterns

### System Architecture Diagram

Der CIMD-Weg neben dem bestehenden DCR-Weg, aus Sicht eines eingehenden Requests:

```
                        MCP-Client (Claude Code)
                                 |
                    client_id = https://claude.ai/oauth/claude-code-client-metadata
                    redirect_uri = http://localhost:3118/callback
                                 |
                                 v
    +--------------------------------------------------------------+
    |  Eingangspunkte, alle vier fragen dieselbe Funktion           |
    |                                                              |
    |  /authorize (oauth/consent.py)   SDK /authorize (2 Stellen)   |
    |  /token (HashedClientAuthenticator)   /revoke (FamilyRevocation)|
    +--------------------------------+-----------------------------+
                                     |
                                     v
                 +-----------------------------------------+
                 |  provider.get_client(client_id)         |
                 |  DER EINE ENFORCEMENT-PUNKT (AUTH-07)   |
                 +--------+---------------------+----------+
                          |                     |
              Zeile im Store?                 nein, und client_id
              ja -> bisheriger Weg            sieht aus wie eine
                    (DCR / reservierte Zeile) https-URL?
                          |                     |
                          |                     v
                          |        +-------------------------------+
                          |        |  NEU: CIMD-Aufloesung         |
                          |        |                               |
                          |        |  1. Schalter an? (AUTH-07)    |
                          |        |     nein -> None (fail closed)|
                          |        |  2. Cache-Treffer?            |
                          |        |     ja -> Schritt 7           |
                          |        |  3. client_id-URL-Form pruefen|
                          |        |     (https, Pfad, kein Frag-  |
                          |        |      ment, kein Userinfo,     |
                          |        |      keine Dot-Segmente)      |
                          |        |  4. SSRF-Fetch (siehe unten)  |
                          |        |  5. Dokument validieren       |
                          |        |     (client_id == URL exakt,  |
                          |        |      Pflichtfelder, kein      |
                          |        |      Secret-Auth-Verfahren)   |
                          |        |  6. redirect_uris durch D-35  |
                          |        |     filtern (Teilregistrierung|
                          |        |      wie register_client)     |
                          |        |  7. clients-Zeile schreiben   |
                          |        |     (FK-Zwang!) + Cache       |
                          |        +---------------+---------------+
                          |                        |
                          v                        v
                 +-----------------------------------------+
                 |  Gemeinsamer Rest von get_client:       |
                 |  allowed-Flag, policy.allows(), TTL     |
                 |  -> OAuthClientInformationFull | None   |
                 +-----------------------------------------+
                                     |
                                     v
                 +-----------------------------------------+
                 |  consent.py: validate_redirect_uri      |
                 |  + NEU: RFC-8252-7.3-Loopback-Regel     |
                 |  + Consent-Seite zeigt client_id-Host   |
                 |    und redirect_uri-Host, Warnung bei   |
                 |    nur-Loopback                         |
                 +-----------------------------------------+

    SSRF-Fetch (Schritt 4), eigenes Modul, fail-closed an jeder Stufe:

    URL -> [https? Pfad? kein Fragment/Userinfo/Dot-Segmente?]
             |  nein -> Refusal (kein Netzwerkverkehr)
             v
           [DNS: alle A/AAAA aufloesen (anyio.getaddrinfo)]
             |  Fehler/leer -> Refusal
             v
           [JEDE Adresse pruefen: global UND nicht privat/loopback/
            link-local/reserved/multicast/unspecified; v4-mapped
            und 6to4/NAT64 entpacken]
             |  eine faellt durch -> Refusal (nicht "nimm eine andere")
             v
           [GET auf die GEPINNTE IP, Host-Header + sni_hostname =
            Originalhost, TLS-Verify an, follow_redirects=False,
            connect/read-Timeout, Accept: application/json]
             |  3xx -> Refusal (kein Folgen)
             |  Nicht-2xx -> Refusal, NICHT cachen
             v
           [aiter_bytes, Abbruch ueber 5 KB]
             |  ueber Grenze -> Refusal, NICHT cachen
             v
           [JSON parsen, Content-Type pruefen]
             |  ungueltig/malformed -> Refusal, NICHT cachen
             v
           Dokument
```

### Recommended Project Structure

```
src/mcp_connector/oauth/
├── cimd.py            # NEU: Fetch + SSRF-Grenze + Dokumentvalidierung
│                      #      keine Policy, keine Store-Kenntnis
├── provider.py        # get_client bekommt den CIMD-Zweig
├── registry.py        # ClientPolicy bekommt eine Frage (cimd_enabled)
│                      # redirect_uri_allowed unveraendert
│                      # NEU: loopback_match() fuer RFC 8252 7.3
├── consent.py         # die eine validate_redirect_uri-Stelle
├── metadata.py        # client_id_metadata_document_supported: true
└── store.py           # cimd_cache-Tabelle (oder Erweiterung von clients)

src/mcp_connector/exapp/
├── responses.py       # NEU: bounded_response (Zwilling zu bounded_body)
└── ui/consent.py      # Hostname-Anzeige + Loopback-Warnung

docs/
├── oauth-setup.md     # CIMD-Abschnitt, Pitfall 6 ersetzen
├── client-setup.md    # Claude-Code-Absatz ersetzen, Cursor-Absatz belegen
└── exapp-install.md   # 34.0.3-Messung

.planning/phases/06-.../
├── 06-XX-MEASUREMENTS.md   # je Messplan eine Datei, Muster siehe Pattern 6
```

### Pattern 1: CIMD an `get_client` einhaengen, nicht neben dem SDK

**What:** Die Aufloesung eines URL-`client_id` passiert innerhalb von `NextcloudOAuthProvider.get_client`, dort wo heute `row is None -> return None` steht.

**When to use:** Immer. Es gibt keinen zweiten sinnvollen Ort.

**Warum das die Locked Decisions von selbst erfuellt:** Die Locked Decision sagt, die AUTH-07-Kontrollen muessen "an denselben vier Punkten" greifen. Die vier Punkte sind im Docstring von `oauth/registry.py` namentlich aufgelistet, und drei von vier laufen bereits durch `get_client`:

```
1. register_client            -> DCR-Registrierung (fuer CIMD nicht relevant)
2. get_client                 -> deckt /authorize, /token, /revoke gemeinsam ab
3. exchange_authorization_code / exchange_refresh_token
4. verify_token
```

Wer den CIMD-Zweig **innerhalb** von `get_client` einbaut und danach in den gemeinsamen Rest der Funktion faellt (`row.allowed`, `self._policy.allows(...)`, `_has_expired(...)`), bekommt Punkt 2 gratis. Punkt 3 und 4 laufen ohnehin ueber den Store und finden dort die geschriebene Zeile. Das ist der Grund, warum die Zeile geschrieben werden **muss** und nicht nur gecacht werden darf.

**Verifiziert** (in dieser Session gelesen):
- `mcp/server/auth/handlers/authorize.py:103` und `:167` rufen `provider.get_client(...)`
- `mcp_connector/oauth/provider.py:1283` (`HashedClientAuthenticator.authenticate_request`) ruft `self._provider.get_client(client_id)`
- `mcp_connector/oauth/consent.py:229`, `:295`, `:468` rufen `provider.get_client(...)`

**Example:**
```python
# src/mcp_connector/oauth/provider.py, in get_client, nach der Store-Abfrage
# Source: eigene Codebasis, Zeilen 305-337, plus der neue Zweig

        if row is None:
            # NEU: ein client_id, der eine https-URL ist, kann ein Client sein, der
            # sich per Metadatendokument ausweist statt sich zu registrieren. Der
            # Schalter wird VOR jedem Netzwerkverkehr gefragt, sonst waere ein
            # abgeschaltetes CIMD ein SSRF-Werkzeug mit ausgeschalteter Funktion.
            if not self._policy.cimd_enabled:
                return None
            row = await self._resolve_cimd(client_id, store)
            if row is None:
                return None

        client = _client_information(row.metadata_json, client_id)
        ...
        # ab hier unveraendert: allowed, policy.allows, _has_expired
```

**Anti-Pattern:** Eine eigene `/cimd`-Route, eine Middleware vor `/authorize`, oder eine zweite Provider-Klasse. Jedes davon erzeugt einen Pfad, der die vier Enforcement-Punkte nicht durchlaeuft, und genau das verbietet die Locked Decision ("ein abgeschaltetes DCR darf ueber CIMD NICHT umgehbar sein").

### Pattern 2: Der Schalter, und wie DCR-off nicht umgehbar wird

**What:** `ClientPolicy` bekommt ein viertes Feld. Der Entscheid, ob es ein eigener Schalter oder derselbe ist, war Claude's Discretion; die Recherche gibt eine klare Empfehlung.

**Empfehlung: ein eigener Schalter `NC_MCP_OAUTH_CIMD`, Default AN, aber mit einer harten Kopplung an DCR.**

Begruendung aus drei Richtungen:

1. **Die Spec macht CIMD zum Vorzugsweg und DCR zum Altlastpfad.** Die MCP-Spec 2026-07-28 markiert DCR als deprecated und CIMD als das, was Clients zuerst versuchen sollen. Ein Server, der CIMD an denselben Schalter haengt wie DCR, koppelt den neuen Standardweg an den Zustand eines auslaufenden. In zwei Releases ist der DCR-Schalter der, den Admins ausschalten, und dann fiele der Standardweg mit.
2. **Aber die Locked Decision ist bindend und ihr Wortlaut ist eindeutig:** "ein abgeschaltetes DCR darf ueber CIMD NICHT umgehbar sein". Das ist mit einem eigenen Schalter nur einzuhalten, wenn die Ableitung fail-closed ist: `cimd_enabled = _switch(env, ENV_CIMD, default=True) and dcr_enabled`. Ein Admin, der DCR ausschaltet, hat "keine selbst anmeldenden Clients" gemeint, nicht "keine RFC-7591-Clients"; das ist die einzige Lesart, in der das Ausschalten das tut, was der Admin wollte.
3. **Der Preis ist ein Satz Doku und ein Test**, und der Gewinn ist, dass ein Admin CIMD getrennt abschalten kann (z.B. weil sein Netz keinen Outbound erlaubt), ohne DCR zu verlieren.

**Zweiter Pflichtteil: die Allowlist.** `policy.allows(client_id, redirect_uris)` funktioniert fuer CIMD **besser** als fuer DCR, und das ist ein Verkaufsargument fuer die Doku: bei DCR ist die `client_id` eine Zufalls-UUID, die ein Admin nicht vorab kennen kann (deshalb der `redirect_uris`-Zweig in `ClientPolicy.listed`). Bei CIMD **ist** die `client_id` eine stabile, veroeffentlichte URL. Ein Admin kann `NC_MCP_OAUTH_ALLOWED_CLIENTS=https://claude.ai/oauth/claude-code-client-metadata` schreiben, bevor je ein Client verbindet. Das ist genau die "domain-based trust policy", die der IETF-Draft in §6.4 und §6.8 als MAY nennt, und wir haben sie schon.

**Dritter Teil: das Advertising.** Das SDK-Modell traegt das Feld bereits:

```python
# .venv/Lib/site-packages/mcp/shared/auth.py:229 (verifiziert)
client_id_metadata_document_supported: bool | None = None
```

`build_metadata` setzt es **nicht** (in dieser Session gegen den SDK-Quelltext geprueft: keine Fundstelle in `mcp/server/`). Also wird es in `oauth/metadata.py:_authorization_server_document` nachgesetzt, genau wie `authorization_response_iss_parameter_supported = True` in Zeile 202. Und es muss vom Schalter abhaengen: ein Server, der `true` sagt und dann `invalid_client` antwortet, schickt Clients in eine Sackgasse, aus der sie laut Spec nicht mehr auf DCR zurueckfallen.

Zusaetzlich verifiziert: Claude waehlt CIMD nur, wenn die Metadaten **beides** tragen, `client_id_metadata_document_supported: true` **und** `"none"` in `token_endpoint_auth_methods_supported`. Letzteres steht hier schon (Phase-03-Entscheidung: "`token_endpoint_auth_methods_supported` traegt zusaetzlich `none`"). [CITED: sunpeak.ai Claude-Connector-Auth-Analyse; konsistent mit dem Draft, der Shared-Secret-Verfahren fuer CIMD verbietet]

### Pattern 3: Die SSRF-Grenze, gemessen statt zitiert

**What:** Eine Zielpruefung, die alle in dieser Session gemessenen Luecken von `ipaddress` schliesst, plus IP-Pinning gegen Rebinding.

**Die Messung** (`.venv/Scripts/python.exe`, Python 3.13.13, diese Session). Auszug auf die Faelle, die etwas beweisen:

| Adresse | `is_private` | `is_loopback` | `is_link_local` | `is_reserved` | `is_multicast` | `is_global` | Was das bedeutet |
|---------|-------------|---------------|-----------------|---------------|----------------|-------------|------------------|
| `127.0.0.1` | True | True | False | False | False | False | Trivialfall, jede Regel faengt ihn |
| `169.254.169.254` (Cloud-Metadaten) | True* | False | True | False | False | False | `169.254.1.1` gemessen: `is_private=True, is_link_local=True` |
| `::ffff:127.0.0.1` | **True** | **True** | False | False | False | False | v4-mapped wird korrekt entpackt, `ipv4_mapped` liefert `127.0.0.1` |
| `2002:7f00:1::1` (6to4 auf 127.0.0.1) | **True** | False | False | False | False | False | 6to4 faellt unter `is_private`. Gut |
| `64:ff9b::7f00:1` (NAT64 auf 127.0.0.1) | **False** | False | False | **True** | False | **True** | **LUECKE 1:** `is_private` reicht nicht. Nur `is_reserved` faengt es, und `is_global` ist hier True |
| `100.64.0.1` (CGNAT) | **False** | False | False | False | False | **False** | **LUECKE 2:** `is_private` reicht nicht. `is_global == False` faengt es |
| `224.0.0.1` (Multicast) | False | False | False | False | **True** | **True** | **LUECKE 3:** `is_global` reicht nicht. Nur `is_multicast` faengt es |
| `0.0.0.0` | True | False | False | False | False | False | `is_unspecified=True` |
| `8.8.8.8` | False | False | False | False | False | **True** | Der einzige der Liste, der durchgelassen werden darf |

**Die Regel, die alle drei Luecken schliesst:**

```python
# Source: eigene Messung dieser Session gegen Python 3.13.13
import ipaddress

def _target_allowed(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Whether an outbound request may go to this address. Fail closed.

    One flag is not enough, and this is measured rather than assumed:
    ``is_private`` is False for 100.64.0.1 (CGNAT) and for 64:ff9b::7f00:1
    (NAT64 embedding 127.0.0.1), while ``is_global`` is True for 224.0.0.1
    (multicast). Only the conjunction holds all three.
    """
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        # ::ffff:127.0.0.1 reads as a v6 address and is loopback. Python already
        # reports it as private, but unpacking makes the intent readable and covers
        # a future where it does not.
        addr = mapped
    if not addr.is_global:
        return False
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )
```

**When to use:** Bei jedem Outbound-Request, dessen Ziel aus einer Anfrage stammt. In diesem Projekt ist das ausschliesslich der CIMD-Fetch (die Nextcloud-Basis-URL kommt per Phase-01-Entscheidung immer aus `NC_MCP_URL` und nie aus dem Request).

**Die zweite Haelfte: IP-Pinning gegen Rebinding.** Eine Pruefung, die aufloest und danach httpx mit dem *Hostnamen* aufruft, laesst httpx erneut aufloesen. Das ist das TOCTOU-Fenster, das 2026 mehrfach als CVE aufgeschlagen ist [CITED: CVE-2026-55391 (datamodel-code-generator), github.com/mlflow/mlflow/issues/24179, github.com/crewAIInc/crewAI/issues/6520, github.com/PrefectHQ/prefect/pull/21591]. Der verifizierte Weg mit dem installierten Stack:

```python
# Source: httpcore 1.0.9, _async/connection.py:107 und :151 (in dieser Session gelesen);
# httpx 0.28.1 leitet request.extensions durch
async def _fetch_pinned(url: httpx.URL, ip: str, *, limit: int, timeout: float) -> bytes:
    """GET the document from a pinned address, with the original host in TLS and Host.

    The address is the one that was validated, not one httpx resolves again: that is the
    whole point. ``sni_hostname`` keeps the TLS handshake and the certificate check on the
    real host name, so pinning costs no certificate validation.
    """
    literal = f"[{ip}]" if ":" in ip else ip
    pinned = url.copy_with(host=literal)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout, connect=timeout),
        follow_redirects=False,          # the house rule of nextcloud/http.py, and a
                                         # redirect would be a second, unchecked target
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
    ) as client:
        request = client.build_request(
            "GET",
            pinned,
            headers={"Host": url.netloc.decode(), "Accept": "application/json"},
            extensions={"sni_hostname": url.host},
        )
        response = await client.send(request, stream=True)
        try:
            if response.status_code != 200:
                raise _Refused(f"status {response.status_code}")
            seen = bytearray()
            async for chunk in response.aiter_bytes():
                seen += chunk
                if len(seen) > limit:
                    raise _Refused("document exceeds the size limit")
            return bytes(seen)
        finally:
            await response.aclose()
```

**Konstanten mit Begruendung:**

| Konstante | Wert | Quelle |
|-----------|------|--------|
| Maximale Dokumentgroesse | **5120 Bytes** | Draft §6.6: "The recommended maximum response size for client metadata documents is 5 kilobytes" [CITED] |
| Timeout | **5 s** connect und read | Referenzimplementierung nutzt 10 s [CITED: giantswarm/mcp-oauth]; das Projekt fuehrt in `nextcloud/http.py` `connect=5.0` und ein CIMD-Fetch sitzt in einem Browser-Request (Consent-Seite), wo 10 s als haengend gelesen wird |
| Positiv-Cache | HTTP-Cache-Header respektieren, Untergrenze 300 s, Obergrenze 3600 s | Draft: "SHOULD respect HTTP cache headers ... MAY define its own upper and/or lower bounds"; die Referenzimplementierung nutzt 5 min Default und 1 h Cap [CITED] |
| Negativ-Cache | **darf nicht existieren fuer Fehlerantworten** | Draft, hart: "The authorization server MUST NOT cache error responses. The authorization server also MUST NOT cache documents which are invalid or malformed" [CITED]. Ein Negativ-Cache gegen Flooding ist nur als *Drosselung* zulaessig, nicht als gecachte Antwort -> `oauth/throttle.py` ist der vorhandene Ort dafuer |
| Redirects | **0** | Draft schweigt, aber jedes Folgen ist ein zweites Ziel ohne Pruefung; `follow_redirects=False` ist ohnehin die Hausregel |

### Pattern 4: RFC 8252 §7.3, an genau einer Stelle

**What:** Ein Loopback-Redirect-Request wird gegen die registrierten Adressen verglichen, wobei der Port ignoriert und der Rest exakt verglichen wird.

**Warum das eine Voraussetzung von AUTH-08 ist und nicht eine Folge von CLIENT-05:**

Claude Codes CIMD-Dokument, in dieser Session abgerufen von `https://claude.ai/oauth/claude-code-client-metadata`:

```json
{
  "client_id": "https://claude.ai/oauth/claude-code-client-metadata",
  "client_name": "Claude Code",
  "client_uri": "https://claude.ai",
  "redirect_uris": [
    "http://localhost/callback",
    "http://127.0.0.1/callback"
  ],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

Beide Adressen sind **portlos**. Zur Laufzeit schickt Claude Code `http://localhost:3118/callback` (Default 3118, ueberschreibbar per `MCP_OAUTH_CALLBACK_PORT`, mit Zufallsport-Rueckfall) [CITED: anthropics/claude-code#37747, geschlossen; die Regression traf mcp.granola.ai und mcp.slack.com]. Ohne §7.3 ist der Kandidat-Client fuer AUTH-08 also nicht erreichbar, und Success Criterion 1 ("verbindet sich und ruft ein Werkzeug auf") ist nicht erfuellbar.

**Der Normtext ist ein MUST, kein Kann:**

> "The authorization server **MUST** allow any port to be specified at the time of the request for loopback IP redirect URIs, to accommodate clients that obtain an available ephemeral port from the operating system at the time of the request." [CITED: RFC 8252 §7.3]

**Die Falle, die die Locked Decision nicht kennt:** §7.3 spricht von "loopback **IP** redirect URIs" und nennt `http://127.0.0.1:{port}/{path}` und `http://[::1]:{port}/{path}`. RFC 8252 §8.3 raet ausdruecklich von `localhost` ab, weil der Name von der Hosts-Datei abhaengt. Claude Code schickt zur Laufzeit aber `localhost`, nicht `127.0.0.1`. Eine buchstabengetreue Umsetzung (nur IP-Literale) laesst Claude Code weiter draussen. Die Locked Decision sagt "beliebiger Port auf 127.0.0.1 bei exaktem Rest-Match"; die Recherche empfiehlt, die Regel auf die drei Hosts anzuwenden, die `registry.LOOPBACK_HOSTS` schon nennt (`127.0.0.1`, `localhost`, `::1`), weil D-35 dieselben drei bereits als registrierbar zulaesst. Der Vergleich bleibt dabei streng: **Schema, Host, Pfad und Query exakt, nur der Port frei.** Ein Host-Wechsel ist kein Port-Wechsel.

**Warum genau eine Stelle:** In dieser Session gelesen:

```python
# .venv/Lib/site-packages/mcp/shared/auth.py:187-192
def validate_redirect_uri(self, redirect_uri: AnyUrl | None) -> AnyUrl:
    if redirect_uri is not None:
        if not self.redirect_uris or redirect_uri not in self.redirect_uris:
            raise InvalidRedirectUriError(...)
```

Diese Methode wird im eigenen Code an genau einer Stelle mit einem Request-Wert gerufen: `oauth/consent.py:236` (`address = client.validate_redirect_uri(requested)`). Der SDK-`/authorize`-Handler ruft sie auch, aber diese Route ist per Phase-03-Entscheidung verworfen ("Von den Routen aus `create_auth_routes` werden zwei verworfen: das AS-Metadatendokument und `/authorize`").

Und der Token-Endpunkt braucht **keine** Aenderung, weil er nicht gegen die Registrierung vergleicht:

```python
# .venv/Lib/site-packages/mcp/server/auth/handlers/token.py:164-183 (gelesen)
# verify redirect_uri doesn't change between /authorize and /tokens
if auth_code.redirect_uri_provided_explicitly:
    authorize_request_redirect_uri = auth_code.redirect_uri
...
if token_redirect_str != auth_redirect_str:
    return ... invalid_request
```

Der gespeicherte Wert traegt bereits den Port (die Spalte `auth_codes.redirect_uri` plus `redirect_uri_explicit` existiert seit Phase 3 genau dafuer), also stimmen beide Seiten von sich aus. Ein Plan, der zwei Stellen aendert, aendert eine zu viel.

**Example:**
```python
# src/mcp_connector/oauth/registry.py, neben redirect_uri_allowed
def loopback_match(requested: str, registered: Sequence[str]) -> str | None:
    """The registered address this loopback request matches, port aside (RFC 8252 7.3).

    The specification's word is MUST, not MAY: a native client takes whatever ephemeral
    port the operating system gives it, so a server that compares the port refuses the
    client for a property the client cannot control. Everything except the port is still
    compared exactly, and a request that is not loopback is not this function's business.

    Measured reason this exists: Claude Code publishes ``http://localhost/callback`` in its
    client id metadata document and arrives with ``http://localhost:3118/callback``.
    """
    ...
```

**Anti-Pattern:** Die angefragte Adresse beim Fund in die `redirect_uris` des Clients schreiben. Das macht aus einem Vergleich eine Registrierung, laesst die Zeile bei jedem Lauf wachsen und gibt einem Angreifer mit einem Loopback-Port eine dauerhafte Eintragung.

### Pattern 5: Die Consent-Seite traegt zwei neue Pflichten

**What:** Fuer CIMD-Clients schreibt die Spec Anzeigen vor, die heute nicht existieren.

Wortlaut, beide MCP-Spec, Security Considerations, Abschnitt "Client ID Metadata Document Security":

> Authorization servers:
> * **SHOULD** display additional warnings for `localhost`-only redirect URIs
> * **MAY** require additional attestation mechanisms for enhanced security
> * **MUST** clearly display the redirect URI hostname during authorization

Plus IETF-Draft §6.4: "The authorization server **SHOULD** display the hostname of the `client_id` on the authorization interface, in addition to displaying the fetched client information if any."

**Und die Falle:** Claude Codes Dokument ist genau der Fall, fuer den die Warnung gedacht ist: `redirect_uris` sind ausschliesslich Loopback. Der Grund steht im Spec-Satz darueber: "Client ID Metadata Documents cannot prevent `localhost` URL impersonation by themselves." Jede lokal laufende Anwendung kann behaupten, Claude Code zu sein, indem sie dieselbe `client_id`-URL nennt. Das Metadatendokument beweist nur, wer die URL kontrolliert, nicht wer den Port belegt.

**When to use:** Auf der Zustimmungsseite, wenn die Client-Identitaet aus einem Metadatendokument stammt.

**Passt in die bestehende Struktur:** `consent.py:402` uebergibt heute `unverified=not provider.policy.listed(...)` an die Seite. Ein zweites Flag (Herkunft = CIMD, plus `client_id`-Host und `redirect_uri`-Host) ist derselbe Mechanismus. Und jede Seite entsteht in `exapp/ui/layout.page()` (Phase-03-Entscheidung), Texte sind Modulkonstanten in `__all__` (fuer vulture und fuer eine spaetere Lokalisierung) - also gibt es genau einen Ort fuer den neuen Text.

### Pattern 6: Das Messdatei-Muster (fuer CLIENT-04, CLIENT-05, EXAPP-06)

**What:** Die MEASUREMENTS-Dateien der Phasen 3 bis 5 waren die Beweisform dieses Projekts. Sie sind mit Commit `d3eb627` ("chore: clear v1.0 phase directories for milestone v1.1") geloescht worden und liegen nur noch in der Git-Historie.

**Wie man das Muster holt:**
```bash
git show d3eb627^:.planning/phases/05-hardening-und-store-einreichung/05-07-MEASUREMENTS.md
git show d3eb627^:.planning/phases/03-oauth-2-1/03-09-MEASUREMENTS.md   # der Cursor-Lauf
```

**Das Muster, aus 05-07 rekonstruiert:**

1. Kopf: `# 05-07 Messprotokoll: <Was>`, dann Datum **mit Uhrzeit und Zeitzone**, Rechner, und der Satz "Alles unten ist aus einem Lauf, nicht aus dem Quellcode abgeleitet; wo eine Aussage aus dem Quellcode kommt, steht das dabei."
2. Abschnitt "Topologie des Laufs" als Tabelle: Compose-Datei, Projektname, Nextcloud-Image **mit Digest**, Connector-Version **mit Image-Digest**, `NC_MCP_PUBLIC_URL`, der gemessene Client mit Version und Digest, und eine Zeile "Owner-Instanzen ... liefen durch, unberuehrt (kein Kommando dieses Laufs nennt sie)".
3. Je Behauptung ein numerierter Abschnitt mit dem **Rohbeleg**: Container-Log mit Zeitstempeln, `occ`-Ausgabe, oder eine Tabelle aus `oauth.sqlite3` im Volume.
4. Eigenheiten der Messumgebung werden benannt, nicht versteckt (in 05-07 der Loopback-Weiterleiter im fremden Container).
5. Gegenproben stehen drin, nicht nur die Treffer.

**Fuer diese Phase:** Die Datei fuer CLIENT-05 hat eine Pflichtzeile mehr, weil die Portfrage die Frage ist: **welchen Port Claude Code in jedem der Laeufe genommen hat**, mindestens drei Laeufe, damit "wechselnd" belegt und nicht behauptet ist. Und den `MCP_OAUTH_CALLBACK_PORT`-Fall separat, weil der Default 3118 allein noch keinen wechselnden Port beweist.

### Anti-Patterns to Avoid

- **`is_valid_client_metadata_url` des SDK als AS-seitige Pruefung kopieren.** Sie steht in `mcp/client/auth/utils.py:317` und prueft nur `scheme == "https"` und `path not in ("", "/")`. Der Draft verlangt zusaetzlich: kein Fragment, kein Username/Passwort, keine Single- oder Double-Dot-Pfadsegmente. Die Client-Seite darf lax sein (sie prueft ihre eigene Konfiguration), die Server-Seite nicht.
- **Den Prozess-Client `nextcloud/http.shared_client()` fuer den CIMD-Fetch benutzen.** Er hat den Pool, die Timeouts und den Zweck des Weges zur eigenen Nextcloud. Ein Fetch in eine fremde Domaene teilt sich keinen Verbindungspool mit einem Credential-tragenden Pfad.
- **Beim SSRF-Check "eine gute Adresse genuegt" lesen.** Wenn ein Name auf `8.8.8.8` **und** `127.0.0.1` aufloest, ist er abzulehnen, nicht auf die gute Adresse zu pinnen. Sonst ist die Regel per DNS-Antwort umschaltbar.
- **Fehlerantworten cachen.** Der Draft verbietet es wortwoertlich (MUST NOT). Drosselung gegen Flooding gehoert in `oauth/throttle.py`, nicht in den Cache.
- **`logo_uri` aus dem Dokument anzeigen.** Das ist ein zweiter Outbound-Request und ein Cross-Domain-Tracking-Kanal; der Draft §6.7 verlangt bei Nutzung Prefetch und Caching. Empfehlung: `logo_uri` gar nicht rendern. Die Consent-Seite dieses Projekts zeigt heute keine Logos, und dabei sollte es bleiben.
- **Einen Doku- oder Store-Satz zu 34.0.3 schreiben, bevor die UI gesehen wurde.** Die Locked Decision sagt es, und die statische Gegenprobe unten sagt, warum es noetig ist.
- **Die Wegwerf-Topologie mit `down -v` neu aufsetzen.** Nutzer `jane` und zwei echte OAuth-Verbindungen sind die Demo-Substanz fuer CONF-01. Der Upgrade-Weg (Image-Pin aendern, `up -d`, `occ upgrade`) erhaelt sie.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IP-Klassifikation (privat, Loopback, link-local) | Eigene CIDR-Listen | `ipaddress` + die Konjunktion aus Pattern 3 | Eigene Listen vergessen NAT64, 6to4, CGNAT, v4-mapped. `ipaddress` kennt sie, man muss nur die richtigen Flags kombinieren, und die richtige Kombination ist oben gemessen |
| IP-Pinning mit korrektem TLS | Eigener Socket-Code oder eigener Resolver-Hook | `extensions={"sni_hostname": host}` + `Host`-Header | httpcore 1.0.9 gibt `sni_hostname` als `server_hostname` in den TLS-Handshake, also bleibt die Zertifikatspruefung auf dem echten Namen. Eigener Socket-Code verliert genau das |
| Groessenbegrenztes Lesen | `response.text` und danach `len` pruefen | `aiter_bytes()` mit Zaehler, Muster `exapp/responses.bounded_body` | Ein `.text` hat den Speicher schon verbraucht, wenn die Pruefung laeuft. Das ist genau der IN-01-Befund, nur auf der Response-Seite |
| Client-Modell fuer das Metadatendokument | Eigene Dataclass | `mcp.shared.auth.OAuthClientInformationFull` | Das ist der Rueckgabetyp von `get_client`. Ein zweites Modell muesste konvertiert werden und driftet |
| Redirect-URI-Zulaessigkeit | Eine zweite Regel fuer CIMD | `registry.redirect_uri_allowed` | Sie akzeptiert Claude Codes portlose Loopback-Eintraege bereits. Die Locked Decision verlangt Wortgleichheit, und Wortgleichheit heisst dieselbe Funktion |
| AUTH-07-Durchsetzung fuer CIMD | Eine zweite Policy-Abfrage | `ClientPolicy.allows` innerhalb von `get_client` | Vier Enforcement-Punkte, eine Funktion. Pitfall 9 der Phase 3 ist genau der Fehler, den eine zweite Abfrage wieder einbaut |
| Drosselung des CIMD-Fetch | Eigener Zaehler im CIMD-Modul | `oauth/throttle.py` | Existiert, hat zwei Grenzen (pro Quelle und pro Pfadklasse), speichert nur SHA-256-Digests und ist gemessen |
| Nextcloud-Versionsnachweis | Ein Blick auf den Docker-Tag | `occ status` im Container | In dieser Session belegt: der Tag `34-apache` zeigt heute auf 34.0.3, aber das **lokale Image** unter diesem Tag ist vom 05.08. und traegt 34.0.2 |

**Key insight:** Diese Phase ist zu 80 Prozent das Wiederverwenden von Strukturen, die v1.0 schon gebaut hat. Der einzige Ort, an dem echter neuer Code entsteht, ist das SSRF-gehaertete Holen eines Dokuments, und selbst dort sind Transport (httpx), Grenz-Muster (`bounded_body`), Redirect-Politik (`follow_redirects=False`) und Drosselung (`throttle.py`) vorhanden. Wer in dieser Phase eine Bibliothek einfuehrt, hat vermutlich einen bestehenden Baustein nicht gefunden.

---

## Runtime State Inventory

Diese Phase aendert Laufzeitzustand (Instanz-Upgrade, neue Store-Tabelle, neue AS-Metadaten). Jede Kategorie ist explizit beantwortet.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | `oauth.sqlite3` im Docker-Volume `nc_app_mcp_connector_data`: Nutzer `jane`, 2 echte OAuth-Verbindungen (Claude Desktop, Open WebUI). **Schema-Zwang:** `flows.client_id` und `authorizations.client_id` haben `REFERENCES clients(client_id) ON DELETE CASCADE` (`store.py:170`, `:183`). Ein CIMD-Client **muss** eine `clients`-Zeile bekommen, sonst schlaegt der erste Flow am Fremdschluessel fehl. | **Code-Edit + Schema-Erweiterung.** Neue Spalte oder Tabelle fuer die CIMD-Herkunft und die Cache-Frist, idempotentes `ALTER` wie bei `auth_codes.redirect_uri_explicit` in Phase 3. **Keine Datenmigration**: bestehende Zeilen bleiben DCR-Zeilen |
| **Live service config** | Compose-Projekt `nc-mcp-exapp` laeuft seit 5 Stunden: `nc-mcp-exapp-nc` (**nextcloud:34-apache = 34.0.2.1**), `nc-mcp-exapp-harp`, `nc-mcp-exapp-caddy`, `nc-mcp-exapp-registry`, `nc_app_mcp_connector` (**Image `127.0.0.1:5000/mcp_connector:0.1.1`**). `compose.exapp.yml:46` pinnt den **gleitenden** Tag `nextcloud:34-apache`. `app_api` 34.0.0, `appstore` 1.0.0. Zusaetzlich laufen `nc-mcp-test` (34-apache) und `findling-nextcloud` (**34.0.3-apache**), beide Owner-Instanzen, unbeteiligt. | **Manuell, in dieser Phase.** (a) `compose.exapp.yml:46` auf `nextcloud:34.0.3-apache` pinnen (Image liegt lokal, 2.21 GB, verifiziert 34.0.3.2), `up -d`, `occ upgrade`. (b) Der laufende Connector ist **0.1.1**, das Repo steht auf 0.1.2 und der Store hat 0.1.2: der Bootstrap muss das Image neu bauen, sonst messen CLIENT-04/05 eine veraltete Fassung ohne die Teilregistrierung aus a80af0a |
| **OS-registered state** | **Keine.** Verifiziert: kein Windows-Task-Scheduler-Eintrag, kein pm2, kein systemd im Spiel. Die Topologie ist reines Docker Compose, `docker ps` ist die vollstaendige Liste | keine |
| **Secrets / env vars** | `HP_SHARED_KEY` lebt nur in der Umgebung der laufenden Container. STATE.md nennt die Prozedur wortgetreu: gegen bereits laufende Container **zuruecklesen statt neu erzeugen** (`docker inspect nc-mcp-exapp-harp ...`), weil `require_hex64` einen abweichenden Schluessel ablehnt und jeder `docker compose`-Aufruf gegen `compose.exapp.yml` an der Interpolation scheitert. `.env.exapp` traegt `APP_SECRET` und den Fixture-Suffix zum Wiederverwenden. Neue Variablen dieser Phase (z.B. `NC_MCP_OAUTH_CIMD`) **muessen in `appinfo/info.xml` deklariert werden**, sonst reicht der Deploy-Daemon sie nicht durch (in Phase 3 gegen AppAPI 34.0.0 gemessen) | **Manifest-Edit Pflicht** fuer jede neue `NC_MCP_`-Variable. `.env.exapp.example` mitziehen. Kein Schluesselwechsel |
| **Build artifacts** | Laufendes ExApp-Image `mcp_connector:0.1.1` (Registry-Kopie und ghcr-Kopie); AppAPI loescht ein gezogenes Image nie. `appinfo/info.xml` sagt 0.1.2. Git-Baum ist sauber auf `63fbd17` | **Rebuild** ueber `scripts/bootstrap_exapp.sh` vor jeder Messung. Kein `pip`-Egg-Info-Problem (uv, `--no-editable` im Image) |

**Die kanonische Frage:** Nach jeder Code- und Doku-Aenderung tragen genau drei Dinge noch alten Zustand: das laufende ExApp-Image (0.1.1 statt HEAD), die Nextcloud-Instanz (34.0.2 statt 34.0.3), und das AS-Metadatendokument, das ein Client eine Stunde lang gecacht haben kann (`NoStore`-Middleware setzt `no-store` auf jede AS-Antwort, also faellt dieser Punkt weg - verifiziert in `provider.py:1356`).

---

## Common Pitfalls

### Pitfall 1: CIMD gebaut, Kandidat-Client kommt trotzdem nicht an

**What goes wrong:** Der CIMD-Pfad ist fertig, das Dokument von Claude Code wird korrekt geholt und validiert, `client_name` steht auf der Consent-Seite, und dann scheitert der Request an `invalid_redirect_uri`.
**Why it happens:** Das Dokument nennt `http://localhost/callback`, der Request bringt `http://localhost:3118/callback`. `validate_redirect_uri` vergleicht exakt.
**How to avoid:** Die RFC-8252-§7.3-Regel **vor oder mit** dem CIMD-Pfad planen, nicht danach. In der Plan-Reihenfolge heisst das: der Loopback-Plan ist keine Folge des CIMD-Plans, sondern seine Voraussetzung.
**Warning signs:** Ein Plan, in dem CLIENT-05 nach AUTH-08 kommt und AUTH-08 einen Live-Nachweis als Erfolgskriterium hat.

### Pitfall 2: Der SSRF-Check laeuft, das Rebinding-Loch bleibt

**What goes wrong:** `getaddrinfo` liefert eine oeffentliche Adresse, die Pruefung ist gruen, `httpx.get(url)` laeuft, httpx loest neu auf und bekommt `127.0.0.1`. Alle Negativtests sind gruen, weil sie mit statischen Namen arbeiten.
**Why it happens:** Zwischen Pruefung und Verbindung liegt eine zweite DNS-Abfrage. Das ist die Standard-Bypass-Klasse und war 2026 in mindestens vier Python-Projekten ein CVE.
**How to avoid:** Auf die validierte IP pinnen (Pattern 3). Und einen Test schreiben, der das **beweist**: ein Fake-Resolver, der beim ersten Aufruf eine oeffentliche und beim zweiten eine private Adresse liefert, muss dieselbe Ablehnung erzeugen. Ohne diesen Test ist die Grenze behauptet.
**Warning signs:** Der Fetch-Code ruft `client.get(url)` mit dem Originalhostnamen. Kein Test nennt das Wort Rebinding.

### Pitfall 3: Der erste CIMD-Flow stirbt am Fremdschluessel

**What goes wrong:** `get_client` liefert brav ein `OAuthClientInformationFull` aus dem Metadatendokument, die Consent-Seite rendert, und dann bricht das Anlegen des Flow-Datensatzes mit einem `IntegrityError` ab.
**Why it happens:** `flows.client_id` und `authorizations.client_id` referenzieren `clients(client_id)`. Ein CIMD-Client, der nur im Cache oder nur im Speicher existiert, hat keine Zeile. Genau dieses Problem hatte Phase 3 schon einmal und loeste es mit einer reservierten Client-Zeile fuer die Onboarding-Strecke (`allowed=false`).
**How to avoid:** Die Aufloesung schreibt eine echte `clients`-Zeile, mit `client_secret_hash = NULL` (CIMD-Clients sind per Draft public: Shared-Secret-Verfahren sind verboten) und `allowed = policy.allows(...)`. Damit funktioniert auch der Rest von `get_client` unveraendert.
**Warning signs:** Ein Design, in dem der CIMD-Cache die einzige Persistenz ist.

### Pitfall 4: Das TTL-Aufraeumen loescht CIMD-Clients samt Verbindungen

**What goes wrong:** Ein CIMD-Client wird nach `IDLE_CLIENT_TTL` von `_has_expired` verworfen. `delete_client` nimmt ueber `ON DELETE CASCADE` die `authorizations` mit, also verschwindet eine Nutzerverbindung, die der Nutzer nie beendet hat.
**Why it happens:** Die TTLs sind fuer DCR-Registrierungen gedacht ("eine Registrierung, die nie einen Token erzeugt hat"). Fuer CIMD ist "die Zeile ist alt" ein anderer Sachverhalt: die Identitaet ist jederzeit neu holbar.
**How to avoid:** `get_client` ruft vor dem Loeschen `_hand_back_client` (WR-04, steht schon so da), also ist der Schaden begrenzt. Aber die Frage muss beim Planen bewusst entschieden werden: entweder CIMD-Zeilen von `_has_expired` ausnehmen, oder die Frist so waehlen, dass sie nur den Cache und nicht die Identitaet betrifft. Empfehlung: die Cache-Frist und die Registrierungs-TTL sind zwei Werte, nicht einer.
**Warning signs:** Ein Plan, der `cimd`-Zeilen einfach in `clients` schreibt und die TTL-Frage nicht erwaehnt.

### Pitfall 5: `client_id_metadata_document_supported: true` ohne funktionierenden Pfad

**What goes wrong:** Die Metadaten sagen `true`, der Schalter steht aber auf aus (oder die Instanz hat keinen Outbound). Der Client waehlt CIMD, bekommt `invalid_client`, und faellt laut Spec **nicht** auf DCR zurueck, weil der Fallback nur greift, wenn die Faehigkeit nicht angekuendigt ist.
**Why it happens:** Das Advertising ist eine Konstante statt einer Funktion des Schalters.
**How to avoid:** `metadata_routes` bekommt den Schalter genauso durchgereicht, wie es heute `dcr_enabled` durchreicht (`metadata.py:107`, `dcr_enabled: bool = True`). Ein Test haelt zusammen: Schalter aus -> Feld fehlt oder ist `false` **und** `/authorize` mit URL-`client_id` ist eine Absage.
**Warning signs:** `client_id_metadata_document_supported = True` als Literal im Dokument.

### Pitfall 6: 34.0.3-Messung gegen den gleitenden Tag

**What goes wrong:** `docker compose up -d` mit `image: nextcloud:34-apache`, `occ status` sagt 34.0.2, und die Messung "die UI zeigt keinen Knopf" wird als 34.0.3-Befund notiert.
**Why it happens:** In dieser Session gemessen: der Tag `34-apache` auf Docker Hub wurde am 17.08. aktualisiert (zeigt jetzt auf 34.0.3), das **lokal** vorhandene Image unter diesem Tag ist aber vom 05.08. und traegt 34.0.2.1. Docker zieht ohne `pull` nicht nach.
**How to avoid:** Auf `nextcloud:34.0.3-apache` pinnen (liegt lokal, verifiziert 34.0.3.2) und `occ status` als **erste Zeile** der Messdatei festhalten, nicht den Tag.
**Warning signs:** Eine Messdatei, deren Topologie-Tabelle einen Tag statt einer Versionszeile nennt.

### Pitfall 7: Der UI-Smoke misst am falschen Nutzer oder am Cache

**What goes wrong:** Die Store-UI zeigt weiter keine ExApps, obwohl der Fix da ist.
**Why it happens:** Zwei bekannte Nebenwirkungen aus diesem Projekt. (a) Der AppAPI-Store-Cache: die Phase-05-Entscheidung sagt, er wird durch **Ueberschreiben mit timestamp 0** verworfen, nie durch Loeschen der Datei, sonst endet jedes folgende AppAPI-Kommando mit `GenericFileException`. (b) Der Store-Knopf ist eine Admin-Ansicht; nextcloud/server#60495 zeigt, dass der App-Store-Zugang fuer Normalnutzer in NC 34 bewusst weg ist. Die Messung muss als Admin laufen.
**How to avoid:** Reihenfolge in die Messdatei schreiben: `occ upgrade` -> Store-Cache mit timestamp 0 ueberschreiben -> Browser-Hard-Reload -> als Admin auf `/settings/apps` -> Screenshot. Und die Gegenprobe: `occ app_api:app:list` muss `mcp_connector [enabled]` sagen, waehrend die UI gemessen wird, sonst misst man eine leere Liste.
**Warning signs:** Ein Plan ohne Cache-Schritt und ohne Angabe, unter welchem Konto gemessen wird.

### Pitfall 8: Cursor-Messung gegen 0.1.1

**What goes wrong:** CLIENT-04 misst, dass Cursor mit `400 invalid_redirect_uri` abgewiesen wird, und schliesst, die Teilregistrierung funktioniere nicht.
**Why it happens:** Der laufende Container traegt Image `mcp_connector:0.1.1`. Die Teilregistrierung kam mit a80af0a und ist in 0.1.2.
**How to avoid:** Erste Zeile der Messdatei: die Version aus `occ app_api:app:list` **und** der Image-Digest. Das Muster verlangt es ohnehin.
**Warning signs:** Eine Messdatei ohne Image-Digest.

### Pitfall 9: Ein Doku-Satz laeuft dem Vokabular-Gate oder der Dreisprachigkeit davon

**What goes wrong:** Der Push scheitert am Vokabular-Gate, oder README.de.md und README.fr.md stehen inhaltlich neben README.md.
**Why it happens:** Zwei Owner-Regeln, die in dieser Phase beide greifen: "archiv" ist in oeffentlichen Artefakten verboten, und README-/Store-Text-Aenderungen ziehen EN/DE/FR zusammen nach.
**How to avoid:** Gate lokal vor dem Push laufen lassen (Locked Decision sagt es). Und: fuer `docs/*.md` gilt die Dreisprachigkeit **nicht** (Phase-05-Entscheidung: die FAQ ist einsprachig kanonisch plus dreisprachige Kurzform), fuer die drei READMEs und den Store-Text **schon**. Ein Plan sollte das explizit trennen, sonst entstehen sechs Textstellen fuer eine Aenderung.
**Warning signs:** Eine Aufgabe "Doku anpassen" ohne Liste der betroffenen Dateien.

### Pitfall 10: Der Consent-Text sagt "verifiziert", wo CIMD nur "domainbelegt" heisst

**What goes wrong:** Die Seite zeigt `client_name` aus dem Dokument, und ein Nutzer liest das als Bestaetigung, mit Claude Code zu sprechen.
**Why it happens:** CIMD beweist Kontrolle ueber eine URL, nicht Identitaet eines Prozesses. Bei nur-Loopback-Redirects kann jede lokale Anwendung die fremde `client_id`-URL nennen. Die Spec sagt es selbst: "Client ID Metadata Documents cannot prevent `localhost` URL impersonation by themselves."
**How to avoid:** Der Text nennt, was belegt ist (der Host der `client_id`), und was nicht (welches Programm den Port belegt). Das ist derselbe Ehrlichkeitsstandard wie die `marks.py`-Docstring-Grenze aus BL-09.
**Warning signs:** Das Wort "verified" oder "verifiziert" im neuen Consent-Text.

---

## Code Examples

### CIMD-URL-Form pruefen, vor jedem Netzwerkverkehr

```python
# Source: draft-ietf-oauth-client-id-metadata-document-00, Client Identifier URLs;
# strenger als mcp/client/auth/utils.py:is_valid_client_metadata_url, absichtlich
from urllib.parse import urlsplit

def is_cimd_client_id(value: str) -> bool:
    """Whether this string is a client identifier URL the draft admits.

    "Client identifier URLs MUST have an 'https' scheme, MUST contain a path component,
    MUST NOT contain single-dot or double-dot path segments, MUST NOT contain a fragment
    component and MUST NOT contain a username or password." A query string is a SHOULD NOT
    and a port is a MAY, so both are tolerated here and neither is invented.

    The SDK's client side check is two conditions (https, non-root path). That is enough
    for a client validating its own configuration and not enough for a server deciding
    whether to make an outbound request on a stranger's behalf.
    """
    parts = urlsplit((value or "").strip())
    if parts.scheme != "https":
        return False
    if parts.fragment or parts.username or parts.password:
        return False
    path = parts.path
    if not path or path == "/":
        return False
    if any(segment in (".", "..") for segment in path.split("/")):
        return False
    try:
        if parts.hostname is None or parts.port is not None and not 0 < parts.port <= 65535:
            return False
    except ValueError:
        return False
    return True
```

### Dokument validieren (die Reihenfolge ist die Spec-Reihenfolge)

```python
# Source: modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration
# plus draft-ietf-oauth-client-id-metadata-document-00
_REQUIRED = ("client_id", "client_name", "redirect_uris")
_FORBIDDEN_AUTH = frozenset(
    {"client_secret_post", "client_secret_basic", "client_secret_jwt"}
)

def validate_document(raw: bytes, client_id: str) -> dict | None:
    """The fetched document, or None. Never raises into a handler (D-37).

    The four MUSTs of the specification, in order:
      1. valid JSON,
      2. the required properties are present,
      3. the document's own ``client_id`` matches the URL it was fetched from, using
         simple string comparison per RFC 3986 section 6.2.1 (no normalisation, the same
         rule this project already applies to ``issuer``),
      4. the ``token_endpoint_auth_method`` is not one built on a shared symmetric secret,
         because there is no channel over which such a secret could ever be agreed.
    """
    try:
        document = json.loads(raw)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    if any(key not in document for key in _REQUIRED):
        return None
    if document["client_id"] != client_id:       # exact, no normalisation
        return None
    if document.get("token_endpoint_auth_method", "none") in _FORBIDDEN_AUTH:
        return None
    if not isinstance(document.get("redirect_uris"), list):
        return None
    return document
```

### Der Negativtest-Katalog fuer AUTH-09

Jede Zeile ist ein Test, der ohne die Grenze durchgeht und mit ihr rot ist. Das ist die Formulierung des Success Criterion 2.

```
Grenze                          | Negativtest
--------------------------------|-------------------------------------------------------
nur https                       | client_id = http://example.com/c.json  -> Absage, KEIN
                                | Netzwerkverkehr (respx: keine Route getroffen)
Pfadkomponente Pflicht          | https://example.com/  -> Absage
kein Fragment / Userinfo        | https://u:p@example.com/c.json, https://e.com/c#x
keine Dot-Segmente              | https://example.com/a/../../etc/c.json
kein privates Ziel              | Name loest auf 10.0.0.5 -> Absage
kein Loopback-Ziel              | Name loest auf 127.0.0.1 und auf ::1 -> je Absage
kein link-local (Metadaten)     | Name loest auf 169.254.169.254 -> Absage
v4-mapped nicht umgehbar        | Name loest auf ::ffff:127.0.0.1 -> Absage
NAT64 nicht umgehbar            | Name loest auf 64:ff9b::7f00:1 -> Absage (is_reserved)
CGNAT nicht umgehbar            | Name loest auf 100.64.0.1 -> Absage (is_global False)
Multicast nicht umgehbar        | Name loest auf 224.0.0.1 -> Absage (is_multicast)
gemischte Aufloesung            | Name loest auf 8.8.8.8 UND 127.0.0.1 -> Absage
                                | (nicht: "nimm die gute")
DNS-Rebinding                   | Resolver liefert Aufruf 1 oeffentlich, Aufruf 2 privat
                                | -> Absage; und ein Test, der belegt, dass nur EINE
                                | Aufloesung stattfindet (Pinning)
kein Redirect-Folgen            | 302 auf http://127.0.0.1/ -> Absage, Ziel nie geholt
Groessenlimit                   | 5121 Bytes -> Absage; und der Beleg, dass der Abbruch
                                | vor dem vollen Lesen kommt (Chunk-Zaehler)
Zeitlimit                       | Server antwortet nach Timeout+1 -> Absage
Nicht-2xx nicht gecacht         | 500, dann 200: der zweite Aufruf geht wirklich raus
Malformed nicht gecacht         | kaputtes JSON, dann gutes: zweiter Aufruf geht raus
client_id-Mismatch              | Dokument nennt eine andere client_id -> Absage
Pflichtfeld fehlt               | ohne client_name -> Absage
Secret-Auth-Verfahren           | token_endpoint_auth_method=client_secret_basic -> Absage
Schalter aus                    | CIMD-Schalter aus -> Absage, KEIN Netzwerkverkehr
DCR aus                         | DCR aus -> CIMD ebenfalls Absage (Locked Decision)
Allowlist an, nicht gelistet    | Absage, und zwar mit derselben Seite wie bei DCR
```

### Advertising an den Schalter haengen

```python
# src/mcp_connector/oauth/metadata.py, im Muster von Zeile 202
# Source: SDK setzt das Feld nicht (mcp/server/ enthaelt keine Fundstelle), das Modell
# traegt es (mcp/shared/auth.py:229)
    metadata.authorization_response_iss_parameter_supported = True
    # A server that announces the capability and then refuses sends clients into a dead
    # end: the specification's fallback to dynamic registration only applies when the
    # capability is absent, not when it is announced and broken.
    metadata.client_id_metadata_document_supported = cimd_enabled or None
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dynamic Client Registration (RFC 7591) als der MCP-Weg fuer Clients ohne Vorbeziehung | Client ID Metadata Documents (draft-ietf-oauth-client-id-metadata-document-00) als Vorzugsweg; DCR ausdruecklich **deprecated** und nur noch "retained for backwards compatibility" | MCP-Spec 2025-11-25 fuehrt CIMD ein (SEP-991), Spec 2026-07-28 markiert DCR als deprecated | Der DCR-Pfad dieses Servers bleibt richtig und noetig (Claude.ai und ChatGPT nutzen ihn), ist aber kein Zukunftspfad mehr. AUTH-08 holt den Standardweg nach |
| Client waehlt DCR, wenn ein `registration_endpoint` existiert | Prioritaetsreihenfolge: (1) Pre-Registration, (2) CIMD wenn `client_id_metadata_document_supported`, (3) DCR wenn `registration_endpoint`, (4) Nutzer fragen | Spec 2026-07-28, Abschnitt Client Registration | Sobald wir `true` ankuendigen, wechseln CIMD-faehige Clients **sofort** auf CIMD. Der Schalter ist damit ein Verhaltensschalter fuer bestehende Clients, nicht nur ein Feature-Flag |
| Client-Credentials sind an einen Authorization Server gebunden | CIMD-`client_id` sind "portable across authorization servers, since they are self-hosted HTTPS URLs resolved by the authorization server on demand. No re-registration is needed" | Spec 2026-07-28, Abschnitt Authorization Server Binding | Ein CIMD-Client braucht bei uns nie eine Re-Registrierung. Das ist der Grund, warum die TTL-Frage aus Pitfall 4 anders liegt als bei DCR |
| `is_private` als SSRF-Grenze | Konjunktion aus `is_global` und sechs Negativflags, mit Entpacken von v4-mapped | Kein Datum: das ist eine gemessene Eigenschaft von Pythons `ipaddress`, nicht eine Aenderung | Drei belegte Umgehungen (NAT64, CGNAT, Multicast) in jeder Implementierung, die ein Flag benutzt |
| SSRF-Check dann Request | Check und Request auf derselben gepinnten Adresse | 2026 als CVE-Klasse etabliert (u.a. CVE-2026-55391) | Ein Plan ohne Pinning baut eine dokumentierte Schwachstelle |

**Deprecated/outdated in unseren eigenen Artefakten:**
- `docs/oauth-setup.md`, Pitfall 6 ("Clients mit einem Loopback-Redirect und einem wechselnden Port passen nicht ... Das ist eine bewusste Grenze von v1, kein Fehler"): wird durch diese Phase falsch und muss ersetzt werden.
- `docs/client-setup.md`, Absatz "Claude Code is a separate case ... which this server does not accept yet": derselbe Fall.
- `docs/client-setup.md`, Absatz "Cursor's own behaviour after the registration is not measured yet": genau das schliesst CLIENT-04.
- `docs/exapp-install.md`, Ursachenkette zum 34.0.2-Store-UI-Bug: bleibt als historischer Befund richtig, braucht die 34.0.3-Zeile daneben.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker + Compose | Testtopologie, alle Messungen | ja | laeuft, 8 Container | keiner. Ohne Docker ist diese Phase nicht messbar |
| `nextcloud:34.0.3-apache` (Image lokal) | EXAPP-06 | **ja, lokal** | 2.21 GB, `occ status` = 34.0.3.2 (an `findling-nextcloud` verifiziert) | `docker pull` (Tag existiert auf Docker Hub, aktualisiert 2026-08-17) |
| `nextcloud:34-apache` (Image lokal) | laufende Topologie | ja | vom 2026-08-05, traegt **34.0.2.1** | — (ist genau die Falle aus Pitfall 6) |
| Laufende ExApp-Topologie `nc-mcp-exapp` | EXAPP-06, CLIENT-04/05, CONF-01 | **ja, seit 5 h** | NC 34.0.2.1, app_api 34.0.0, mcp_connector 0.1.1, Nutzer jane, 2 OAuth-Verbindungen | Neuaufbau per `scripts/bootstrap_exapp.sh` (verliert jane) |
| `HP_SHARED_KEY` | jeder `docker compose`-Aufruf gegen `compose.exapp.yml` | ja, in den laufenden Containern | zuruecklesen per `docker inspect nc-mcp-exapp-harp` | keiner: neu erzeugen bricht die Registrierung (`require_hex64`) |
| uv + Python 3.13 | alles | ja | Python 3.13.13 im `.venv` | keiner (System-Python defekt) |
| **Cursor (echte Installation)** | **CLIENT-04** | **ungeprueft** | — | Ohne Cursor ist CLIENT-04 nicht abschliessbar. **Muss vor dem Planen geklaert werden** (Open Question 3) |
| **Claude Code (echte Installation, gegen die eigene Instanz)** | **CLIENT-05, AUTH-08-Live-Nachweis** | **ja, diese Session laeuft in Claude Code** | — | Der Loopback-Port-Nachweis braucht Claude Code als **MCP-Client** gegen `127.0.0.1:8081`, was eine `.mcp.json`-Konfiguration und einen Browser-Login ist. Machbar, aber nicht dasselbe wie "Claude Code ist installiert" |
| Browser auf dem Host | EXAPP-06 (UI-Knopf), Consent-Seiten, Demo | ja (Playwright-Muster im Projekt vorhanden) | — | `occ` allein kann den UI-Knopf nicht beantworten; genau das war der 05-08-Befund |
| Netzwerk-Outbound nach `claude.ai` | CIMD-Live-Nachweis | ja (in dieser Session abgerufen) | — | Fuer Unit-Tests keiner noetig (respx); fuer den Live-Lauf schon |
| Nextcloud-Conference-Einreichungsweg | CONF-02 | **nein, CfP geschlossen seit 03.08.2026** | — | Entwurf trotzdem bauen; Einreichung ist Owner-Entscheid ohne offenen Weg (Open Question 2) |

**Missing dependencies with no fallback:**
- Nichts, was AUTH-08 oder AUTH-09 blockiert. Beide sind vollstaendig unit-testbar plus ein Live-Lauf gegen die vorhandene Topologie.

**Missing dependencies with fallback:**
- Cursor: falls nicht installierbar, ist CLIENT-04 als "Zugang fehlt" zu fuehren, analog zu CLIENT-01 in Phase 7. Es ist aber ein freier Download und damit anders gelagert als eine fremde Verwaltungsinstanz.
- CONF-02-Einreichung: der Entwurf ist der Liefergegenstand, die Einreichung war nie einer.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | CIMD-Clients sind public clients; PKCE S256 authentifiziert den Tausch (OAuth 2.1, SDK erzwingt es). Shared-Secret-Verfahren sind fuer CIMD verboten und werden abgelehnt |
| V3 Session Management | ja (unveraendert) | Token-Rotation und Familienwiderruf aus Phase 3 gelten fuer CIMD-Clients identisch, weil sie ueber dieselben Store-Zeilen laufen |
| V4 Access Control | ja | `ClientPolicy.allows` an vier Punkten; CIMD-Zeile traegt `allowed`; Per-User-Schalter (Phase 4) unveraendert davor |
| V5 Input Validation | ja, Kern der Phase | `client_id`-URL-Form, Dokumentstruktur, `redirect_uris`, Groessengrenze. Kein Feld des Dokuments wird ungeprueft in eine Seite oder eine URL gegeben (der Client-Name wird schon heute vor dem Escaping gesaeubert, `provider`/`consent`) |
| V6 Cryptography | nein (nichts neu) | Kein neues Schluesselmaterial. `private_key_jwt`/`jwks_uri` waere der einzige Krypto-Anteil von CIMD und ist bewusst **nicht** im Scope: Claude Code nutzt `token_endpoint_auth_method: "none"` |
| V10 Malicious Code / Business Logic | ja | Ein abgeschaltetes DCR darf nicht ueber CIMD umgehbar sein: das ist eine Business-Logic-Grenze, kein Auth-Fehler, und braucht einen eigenen Test |
| V12 Files and Resources | ja | Das Metadatendokument ist eine fremde Ressource mit Groessen- und Zeitgrenze |
| V13 API / Web Service | ja | RFC-8414-Metadaten bleiben zeichengenau; `no-store` auf jeder AS-Antwort |
| V14 Configuration | ja | Neue `NC_MCP_`-Variable muss in `appinfo/info.xml` deklariert werden, sonst wird sie stillschweigend verworfen (Phase-3-Messung) |

### Known Threat Patterns for diesen Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SSRF ueber den CIMD-Fetch auf interne Dienste | Information Disclosure | Zielvalidierung mit der Konjunktion aus Pattern 3, fail-closed, nur https |
| DNS-Rebinding um die Zielvalidierung | Information Disclosure | IP-Pinning ueber `sni_hostname`; Test mit wechselndem Fake-Resolver |
| SSRF ueber Redirect-Folgen | Information Disclosure | `follow_redirects=False`; 3xx ist eine Absage |
| Cloud-Metadaten-Endpunkt (169.254.169.254) | Information Disclosure | `is_link_local`; expliziter Negativtest |
| DoS durch riesiges oder haengendes Dokument | Denial of Service | 5-KB-Grenze mit Chunk-Abbruch, Connect- und Read-Timeout, `max_connections=1` |
| DoS durch Fetch-Flooding (viele unbekannte URL-`client_id`) | Denial of Service | `oauth/throttle.py` (zwei Grenzen, gemessen); **kein** Negativ-Cache, weil der Draft das Cachen von Fehlern verbietet |
| Client-Impersonation ueber eine fremde `client_id`-URL bei Loopback-Redirect | Spoofing | Nicht verhinderbar (Spec sagt es); Mitigation ist Anzeige: `client_id`-Host + `redirect_uri`-Host + Warnung bei nur-Loopback, und ein Consent-Text, der nicht "verifiziert" behauptet |
| Umgehung eines abgeschalteten DCR ueber CIMD | Elevation of Privilege | `cimd_enabled = switch and dcr_enabled`; eigener Test |
| Umgehung der Allowlist ueber CIMD | Elevation of Privilege | `policy.allows` im gemeinsamen Rest von `get_client`, nicht im CIMD-Zweig |
| Open Redirect ueber ein `redirect_uris` aus fremdem Dokument | Tampering | `redirect_uri_allowed` (D-35) filtert vor dem Schreiben; `layout.link()`/`form()` lehnen ohnehin jedes nicht-lokale Ziel ab |
| Port-Squatting auf Loopback nach der §7.3-Lockerung | Spoofing | Bewusst akzeptiertes Restrisiko, benannt: RFC 8252 verlangt die Lockerung; die Grenze ist, dass Schema, Host, Pfad und Query exakt bleiben und ein Angreifer den Code ohne PKCE-Verifier nicht einloesen kann |
| XSS ueber `client_name`/`client_uri` aus dem Dokument | Tampering | Bestehender Pfad: Saeuberung vor dem Escaping, CSP mit Nonce in `layout.page()` |
| Cross-Domain-Tracking ueber `logo_uri` | Information Disclosure | `logo_uri` nicht rendern (Draft §6.7 verlangt sonst Prefetch und Cache) |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Der Upstream-Fix (server#62881, Milestone 34.0.3) ist in 34.0.3 wirksam und die Store-UI zeigt danach Install-/Remove-Knopf fuer ExApps | Pitfall 6/7, EXAPP-06 | **Mittel.** Die statische Gegenprobe war ergebnislos (siehe Open Question 1). Falls der Knopf fehlt, ist EXAPP-06 mit einem negativen Befund abzuschliessen und die Ein-Klick-Story bleibt so vorsichtig wie heute. Kein Code-Risiko, aber ein Story-Risiko fuer die Conference |
| A2 | Claude Code nutzt gegen einen fremden MCP-Server dasselbe CIMD-Dokument, das unter `https://claude.ai/oauth/claude-code-client-metadata` liegt, und keinen anderen `clientMetadataUrl` | Pattern 4, CLIENT-05 | Niedrig-mittel. Das Dokument ist abgerufen, die Default-URL ist aus zwei unabhaengigen Quellen belegt. Falls Claude Code eine andere URL nennt, aendert das nur den Messwert, nicht die Architektur |
| A3 | Claude Codes Laufzeitport ist im Default 3118 und variiert (Env-Override, Zufallsport-Rueckfall) | Pattern 4, CLIENT-05 | Niedrig fuer die Architektur (§7.3 ist ein MUST unabhaengig davon), **hoch fuer die Messdatei**: "wechselnd" muss ueber mindestens drei Laeufe belegt werden, nicht aus einem Issue zitiert |
| A4 | Der Draft-Stand ist `-00`; es gibt keine neuere Revision mit abweichenden Anforderungen | Standard Stack, Pattern 3 | Niedrig. Die MCP-Spec 2026-07-28 referenziert explizit `-00`. Vor dem Bauen einmal `datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/` auf eine `-01` pruefen |
| A5 | `nextcloud:34.0.3-apache` laesst sich als In-Place-Upgrade auf die laufende 34.0.2-Topologie legen (Image-Pin, `up -d`, `occ upgrade`), ohne jane und die zwei Verbindungen zu verlieren | Runtime State Inventory, Environment Availability | Mittel. Standard-Nextcloud-Upgradepfad innerhalb einer Minor-Linie, aber nicht auf dieser Topologie gemessen. **Empfehlung: Volume-Backup vor dem Upgrade**, damit ein Fehlschlag nicht die Demo-Substanz kostet |
| A6 | `app_api` 34.0.0 braucht kein eigenes Update fuer den UI-Fix | Pitfall 7 | Niedrig-mittel. Der Fix liegt in der `appstore`-App des Servers (PR-Titel `fix(appstore):`), nicht in app_api. Beide Instanzen tragen app_api 34.0.0. Falls die UI nach dem Upgrade leer bleibt, ist ein app_api-Update der erste zweite Versuch |
| A7 | Ein eigener Schalter `NC_MCP_OAUTH_CIMD` mit `and dcr_enabled` erfuellt die Locked Decision "DCR-off nicht umgehbar" im Sinne des Owners | Pattern 2 | Niedrig. Die Locked Decision gibt beides frei und nennt den Entscheid als Planungsaufgabe. Die Ableitung ist fail-closed, also strikter als noetig |
| A8 | Der Owner will den Lightning-Talk-Entwurf trotz geschlossenem CfP | CONF-02 | **Mittel-hoch.** Braucht eine Antwort, bevor CONF-02 geplant wird (Open Question 2) |
| A9 | Cursor ist auf diesem Rechner installierbar/installiert | Environment Availability | Mittel. Blockiert CLIENT-04, sonst nichts (Open Question 3) |

---

## Open Questions (RESOLVED)

Alle fuenf Fragen sind beim Planen operationalisiert worden (Vermerke je Frage):

1. **Ist der 34.0.3-Fix wirklich wirksam, und wenn nein, was ist dann der Befund?**
   RESOLVED: Plan 06-07 setzt EXAPP-06 als Zwei-Ausgaenge-Messung um (Knopf da / Knopf fehlt, mit md5-Gegenprobe und Upstream-Kommentar-Entwurf als Owner-Schritt).
   - Was wir wissen: `nextcloud/server#62881` `[stable34] fix(appstore): initialize the exApps store when enabled` ist am 04.08.2026 in `stable34` gemergt, Milestone "Nextcloud 34.0.3". 34.0.3 ist am 17.08. veroeffentlicht, das Image liegt lokal und traegt 34.0.3.2. Die Issues `app_api#971` und `server#61709` sind beide als `completed` geschlossen.
   - Was unklar ist: Ein Datei-fuer-Datei-Vergleich (md5) der `appstore`-App zwischen dem 34.0.2- und dem 34.0.3-Image zeigt **ausserhalb von `l10n/` keinen einzigen Unterschied**; die App-Version ist in beiden 1.0.0; der einzige geaenderte Frontend-Chunk (`dist/AppstoreBrowse-*.chunk.mjs`, 8721 -> 8707 Bytes) enthaelt in beiden Fassungen kein einziges `exapp`-Vorkommen; `dist/appstore-main.mjs` unterscheidet sich im Hash, nennt aber in beiden nur `exAppsCount`. Der Fix ist also nicht statisch belegbar.
   - Empfehlung: Genau so planen, wie EXAPP-06 formuliert ist, naemlich als Frage ("ist nachgewiesen, **ob** die Store-UI den Knopf zeigt"), nicht als Bestaetigung. Zwei Ausgaenge vorsehen: Knopf da -> Doku und Store-Text auf die woertlich wahre Ein-Klick-Story; Knopf fehlt -> negativer Befund mit md5-Gegenprobe in der Messdatei, Doku bleibt so vorsichtig wie heute, und ein Upstream-Kommentar an `app_api#971` ist der naechste Schritt (Owner).

2. **CONF-02: Wozu genau dient der Lightning-Talk-Entwurf, wenn der CfP zu ist?**
   - Was wir wissen: Conference 19.-20.09.2026, CIC Berlin, Lohmuehlenstrasse 65. Lightning Talk = **5 Minuten**. Der CfP hatte eine verlaengerte Frist bis **03.08.2026** und ist geschlossen ("A big thank you to everyone who shared their ideas with us! The call for proposals closed on August 3"). Angenommene Sprecher liefern Foliendraft bis 09.09. Contributor Week 21.-25.09.
   - Was unklar ist: Ob der Owner bereits eingereicht hat (dann ist der Entwurf ein Pflicht-Liefergegenstand mit Frist 09.09.), ob es um die Contributor Week geht (anderes Format, anderer Ton), oder ob es reines Pitch-Material fuer Gespraeche vor Ort und den Prototype-Fund-Antrag ist.
   - Empfehlung: **Vor dem Planen fragen.** Bis dahin auf 5 Minuten und die vier Differenzierer auslegen, weil das in allen drei Faellen brauchbar ist. Und nicht auf 10 Minuten planen: das ist das Format, das es nicht gibt.
   RESOLVED: Plan 06-10 liefert genau das in allen drei Faellen brauchbare Artefakt (5-Minuten-Entwurf, Englisch, vier Differenzierer); jede Einreichungs-/Kontaktaktion bleibt Owner-Entscheid und ist dem Owner als offene Frage vorgelegt.

3. **Ist Cursor auf diesem Rechner verfuegbar?**
   - Was wir wissen: CLIENT-04 ist reine Messarbeit gegen einen echten Cursor. Der Code-Pfad (Teilregistrierung) steht seit a80af0a und ist unit-getestet.
   - Was unklar ist: ob Cursor installiert ist. Nicht geprueft, weil eine Suche nach fremden Installationen ausserhalb des Recherche-Auftrags liegt.
   - Empfehlung: Erste Aufgabe des CLIENT-04-Plans ist ein Verfuegbarkeits-Check mit Verzweigung, nicht ein Messschritt, der stillschweigend scheitert.
   RESOLVED: Plan 06-08 beginnt mit genau diesem Verfuegbarkeits-Check und traegt einen Checkpoint (install/defer/skip) statt eines stillen Fehlschlags.

4. **Cache: Store-Tabelle oder Closure?**
   - Was wir wissen: Modul-globaler veraenderlicher Zustand ist verboten (D-20, zwei namentlich gelistete Ausnahmen). Die `clients`-Zeile muss ohnehin geschrieben werden (FK-Zwang). Der Draft verlangt HTTP-Cache-Header-Respekt und verbietet das Cachen von Fehlern.
   - Was unklar ist: ob die Cache-Frist eine Spalte auf `clients` sein soll (billig, aber vermischt Identitaet und Frische) oder eine eigene Tabelle (saubere Trennung, ein `ALTER` mehr).
   - Empfehlung: Spalte auf `clients` (z.B. `cimd_fetched_at`, `cimd_expires_at`), weil die Zeile ohnehin existiert und weil Pitfall 4 verlangt, die Registrierungs-TTL und die Cache-Frist als zwei Werte zu fuehren, was mit zwei Spalten am selben Datensatz am ehrlichsten sichtbar ist. Ist Claude's Discretion.
   RESOLVED: Plan 06-05 setzt die Empfehlung um (Spalten `cimd_fetched_at`/`cimd_expires_at` auf `clients`; `_has_expired` gilt nicht fuer CIMD-Zeilen).

5. **Braucht die 5-KB-Grenze eine Ausnahme?**
   - Was wir wissen: Der Draft empfiehlt 5 KB. Claude Codes Dokument ist rund 350 Bytes.
   - Was unklar ist: nichts Belastbares. Ein Dokument mit `jwks` inline koennte groesser werden, aber `private_key_jwt` ist bewusst ausserhalb des Scope.
   - Empfehlung: 5120 Bytes fest, ohne Konfigurationsschalter. Ein Schalter waere eine Grenze, die ein Admin versehentlich aufweichen kann.
   RESOLVED: Plan 06-01 setzt 5120 Bytes als feste Konstante ohne Schalter um.

---

## Sources

### Primary (HIGH confidence)

**Spec und Norm (in dieser Session abgerufen)**
- https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization - Overview (CIMD SHOULD, DCR deprecated), Client Registration Verweis, Resource-Parameter, Refresh-Token-Guidance
- https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration - CIMD-Anforderungen fuer Clients und Authorization Server im Wortlaut, Prioritaetsreihenfolge, Beispieldokument, Advertising-Feld, DCR-Deprecation-Warnung, Authorization Server Binding (CIMD-Portabilitaet)
- https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations - Abschnitt "Client ID Metadata Document Security": SSRF-Verweis, Localhost-Redirect-Risiken (3 normative Punkte), Trust Policies; plus Open Redirection (exaktes Matching als MUST)
- https://www.ietf.org/archive/id/draft-ietf-oauth-client-id-metadata-document-00.html - Client-Identifier-URL-Regeln, Retrieval, Caching-Verbote (MUST NOT cache errors/malformed), verbotene Auth-Verfahren, Section 6 vollstaendig (6.1 redirect_uris-Beziehung, 6.2 Client-Auth, 6.3 Key-Wechsel, 6.4 Phishing/Hostname-Anzeige, 6.5 SSRF, 6.6 **5 KB**, 6.7 logo_uri, 6.8 Domain-Trust)
- https://datatracker.ietf.org/doc/html/rfc8252#section-7.3 - Loopback Interface Redirection, "The authorization server **MUST** allow any port to be specified at the time of the request for loopback IP redirect URIs"

**SDK und Codebasis (in dieser Session gelesen/gemessen)**
- `.venv/Lib/site-packages/mcp/shared/auth.py:187-198` - `validate_redirect_uri`, exaktes Matching
- `.venv/Lib/site-packages/mcp/shared/auth.py:229` - `client_id_metadata_document_supported` existiert im Modell
- `.venv/Lib/site-packages/mcp/server/auth/handlers/authorize.py:103,167` - beide `get_client`-Aufrufe
- `.venv/Lib/site-packages/mcp/server/auth/handlers/token.py:164-183` - Redirect-Vergleich gegen den **gespeicherten** Auth-Code-Wert
- `.venv/Lib/site-packages/mcp/client/auth/utils.py:317-397` - `is_valid_client_metadata_url`, `should_use_client_metadata_url`, `create_client_info_from_metadata_url` (alles **Client**-Seite)
- Gegenprobe: `grep -rn -i "client_id_metadata|metadata_document|cimd" .venv/Lib/site-packages/mcp/server/` -> **kein Treffer**. mcp 2.0.0 hat serverseitig keine CIMD-Unterstuetzung
- `.venv/Lib/site-packages/httpcore/_async/connection.py:107,151` - `sni_hostname`-Extension geht als `server_hostname` in den TLS-Handshake
- `src/mcp_connector/oauth/registry.py` (vollstaendig) - `ClientPolicy`, `redirect_uri_allowed`, `LOOPBACK_HOSTS`, die vier Enforcement-Punkte im Docstring
- `src/mcp_connector/oauth/provider.py:296-428` (`get_client`, `client_secret_hash`, `register_client`), `:1252-1408` (`HashedClientAuthenticator`, `NoStore`, `_client_information`)
- `src/mcp_connector/oauth/consent.py:223-239,394-402,468-472` - die eine `validate_redirect_uri`-Stelle, `unverified`-Flag
- `src/mcp_connector/oauth/store.py:158-218` - Schema, die beiden `REFERENCES clients(client_id) ON DELETE CASCADE`
- `src/mcp_connector/oauth/metadata.py:106-209` - `dcr_enabled`-Durchreichung, Nachsetzen von Metadatenfeldern
- `src/mcp_connector/exapp/responses.py:67-89` - `bounded_body` als Grenz-Muster
- `src/mcp_connector/nextcloud/http.py:5,68-76` - `follow_redirects=False` als Hausregel, `shared_client`-Timeouts
- Eigene Messung: `ipaddress`-Flag-Matrix ueber 21 Adressen auf Python 3.13.13 (Tabelle in Pattern 3)
- `git show d3eb627^:.planning/phases/05-hardening-und-store-einreichung/05-07-MEASUREMENTS.md` - Messdatei-Muster

**Nextcloud (in dieser Session gemessen)**
- `docker exec -u www-data nc-mcp-exapp-nc php occ status` -> 34.0.2.1; `occ app:list` -> app_api 34.0.0, appstore 1.0.0; `occ app_api:app:list` -> mcp_connector 0.1.1 [enabled]
- `docker exec -u www-data findling-nextcloud php occ status` -> 34.0.3.2 (belegt, dass das lokale `34.0.3-apache`-Image 34.0.3 traegt)
- `docker image inspect nextcloud:34-apache` -> Created 2026-08-05 (= 34.0.2, obwohl der Tag auf Docker Hub am 17.08. aktualisiert wurde)
- Docker Hub Tags-API `library/nextcloud?name=34.0` -> `34.0.3` und `34.0.3-apache` vorhanden, last_updated 2026-08-17
- `gh api repos/nextcloud/server/pulls/62881` -> `[stable34] fix(appstore): initialize the exApps store when enabled`, merged 2026-08-04, **Milestone "Nextcloud 34.0.3"**, base `stable34`
- `gh api repos/nextcloud/server/pulls/62276` -> master, Milestone "Nextcloud 35" (der Original-PR)
- `gh api repos/nextcloud/app_api/issues/971` -> "ExApps not shown anymore in App mangement menu", closed completed 2026-08-17
- `gh api repos/nextcloud/server/issues/61709` -> "[Bug]: external Apps are not being shown inside the App Store anymore", closed completed 2026-08-04
- md5-Vergleich `apps/appstore` und `apps/app_api` zwischen beiden Images (Ergebnis in Open Question 1)

**Claude Code CIMD**
- https://claude.ai/oauth/claude-code-client-metadata - das echte Dokument, in dieser Session abgerufen (JSON in Pattern 4)

**Conference**
- https://nextcloud.com/conference-2026/ - CfP "closed on August 3", Conference 19.-20.09.2026, Contributor Week 21.-25.09., CIC Berlin
- https://nextcloud.com/blog/nextcloud-conference-2026-call-for-speakers/ - Lightning Talk = 5 Minuten, Workshop 30/60 Minuten, Foliendraft bis 09.09.

### Secondary (MEDIUM confidence)

- https://github.com/anthropics/claude-code/issues/37747 - "MCP OAuth regression: client metadata document redirect_uris missing port causes auth failure for providers supporting CIMD": Port 3118 als Default, `MCP_OAUTH_CALLBACK_PORT`, Zufallsport-Rueckfall, betroffene Anbieter, Regression ab 2.1.80, geschlossen. Direkt konsistent mit dem abgerufenen Dokument (portlose URIs) -> die Grundaussage ist doppelt belegt, die Portdetails nur hier
- https://github.com/giantswarm/mcp-oauth/blob/main/docs/cimd.md - AS-seitige Referenzimplementierung (Go): Timeout 10 s, Cache-TTL 5 min Default mit 1-h-Cap, Negativ-Cache mit Backoff, keine Redirects, LRU. Als Vergleichsmassstab fuer die Konstanten benutzt, nicht als Vorlage
- https://workos.com/blog/client-id-metadata-documents-cimd-oauth-client-registration-mcp, https://www.descope.com/learn/post/cimd, https://stytch.com/blog/oauth-client-id-metadata-mcp/ - CIMD-Ueberblick, SEP-991, Adoption ab Spec 2025-11-25. Nur zur Orientierung; jede normative Aussage stammt aus Spec oder Draft
- https://sunpeak.ai/blogs/claude-connector-oauth-authentication/ - Claude waehlt CIMD nur bei `client_id_metadata_document_supported: true` **und** `"none"` in `token_endpoint_auth_methods_supported`. Konsistent mit dem Draft-Verbot von Shared-Secret-Verfahren, aber selbst keine Primaerquelle
- https://github.com/PrefectHQ/prefect/pull/21591, https://advisories.gitlab.com/pypi/datamodel-code-generator/CVE-2026-55391/, https://github.com/mlflow/mlflow/issues/24179, https://github.com/crewAIInc/crewAI/issues/6520 - DNS-Rebinding-Bypass als Klasse, und IP-Pinning als der akzeptierte Fix
- https://github.com/nextcloud/server/issues/60495 - App-Store-Knopf fuer Normalnutzer in NC 34 entfernt (relevant fuer "unter welchem Konto messen")

### Tertiary (LOW confidence, markiert)

- https://client.dev/ - CIMD-Landingpage. Nennt eine Origin-Pruefung fuer `client_uri` als "must", die im Draft ein MAY ist (§6.1). **Nicht** als Anforderung uebernommen
- https://github.com/anthropics/claude-code/issues/36861 - "[DOCS] MCP docs missing CIMD (SEP-991) OAuth support": Hinweis darauf, dass Claude Codes CIMD-Verhalten offiziell unterdokumentiert ist. Stuetzt A2/A3 als Annahmen statt als Fakten

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| CIMD-Spec-Anforderungen | HIGH | Spec-Seiten und IETF-Draft im Wortlaut abgerufen, normative Saetze zitiert. Zwei unabhaengige Primaerquellen (MCP-Spec verweist auf Draft, Draft gelesen) |
| SDK-Lage (nichts serverseitig vorhanden) | HIGH | Positiv- und Negativ-Grep gegen das installierte mcp 2.0.0. Die Negativaussage ist mit einem Kommando belegt, nicht erschlossen |
| Einhaengepunkt `get_client` | HIGH | Alle Aufrufer in SDK und eigenem Code namentlich gelesen, mit Zeilennummern |
| Loopback-Portfrage | HIGH | RFC-Wortlaut + das echte CIMD-Dokument + der SDK-Token-Handler-Vergleich. Das Portdetail (3118, variabel) ist MEDIUM, siehe A3 |
| SSRF-Regel | HIGH | Selbst gemessene Flag-Matrix auf dem Ziel-Interpreter; drei Luecken reproduzierbar benannt |
| IP-Pinning mit httpx | HIGH | `sni_hostname`-Extension im installierten httpcore-Quelltext gelesen. Der konkrete Code ist noch nicht ausgefuehrt -> der erste Plan-Task sollte ihn gegen einen lokalen TLS-Server verifizieren |
| Konstanten (5 KB, Timeout, Cache) | MEDIUM-HIGH | 5 KB und das Cache-Verbot sind Draft-Wortlaut (HIGH); Timeout und Cache-Grenzen sind begruendete Wahlen mit einer Referenzimplementierung als Vergleich (MEDIUM) |
| NC-Versionen und Tags | HIGH | `occ status` in beiden Containern, Docker-Hub-API, GitHub-API auf Merge-Commit und Milestone |
| Wirksamkeit des 34.0.3-Fix | **MEDIUM** | Merge und Milestone sind verifiziert, der Code-Effekt ist statisch nicht nachweisbar. Open Question 1 |
| Laufender Zustand der Topologie | HIGH | `docker ps`, `docker volume ls`, `occ`-Ausgaben. Weicht von STATE.md ab (dort "vollstaendig entfernt"), die Messung gewinnt |
| Conference-Fakten | HIGH | Offizielle Conference-Seite und CfP-Blogpost. Der geschlossene CfP ist woertlich zitiert |
| Messdatei-Muster | HIGH | Originaldatei aus der Git-Historie gelesen |

**Was ich uebersehen haben koennte, nach eigener Durchsicht:**
- Ob eine `-01`-Revision des IETF-Drafts existiert (A4). Ein Aufruf von `datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/` vor dem Bauen kostet eine Minute.
- Ob es eine MCP-Auth-Extension (`modelcontextprotocol/ext-auth`) gibt, die CIMD praezisiert. Die Spec verweist auf das Repo, ich habe es nicht geoeffnet, weil Extensions per Definition optional und additiv sind.
- `private_key_jwt` + `jwks_uri` (Draft §6.2, §6.3) ist bewusst nicht recherchiert: Claude Code nutzt `"none"`, und ein Krypto-Pfad ohne Kandidat-Client waere ungetesteter Code in einem Sicherheitspfad.
- Die genaue Form, in der Claude Code seine `.mcp.json` fuer einen HTTP-MCP-Server auf `127.0.0.1:8081` erwartet. Ein Ausfuehrungsdetail des Messplans, kein Architekturrisiko.

**Research date:** 2026-08-20
**Valid until:** 2026-09-03 (14 Tage). Kurz, aus drei Gruenden: der IETF-Draft steht auf `-00`, Claude Codes CIMD-Verhalten hat innerhalb weniger Releases als Regression geschwankt, und die Conference-Deadline verschiebt in diesem Fenster die Prioritaeten.
</content>
</invoke>
