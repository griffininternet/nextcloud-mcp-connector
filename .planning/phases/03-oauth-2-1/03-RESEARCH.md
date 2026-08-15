<!--
SPDX-FileCopyrightText: 2026 street1983nk
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Phase 3: OAuth 2.1 - Research

**Researched:** 2026-08-15
**Domain:** OAuth 2.1 / MCP Authorization (RFC 9728, 8414, 7591, 7636, 8707, 9207), Nextcloud
Login Flow v2, AppAPI/HaRP Routing, verschlüsselter Token-Store im ExApp-Volume
**Confidence:** HIGH für die SDK-Faktenlage (Quellcode der installierten Version gelesen),
HIGH für Nextcloud- und HaRP-Verhalten (Quellcode der Upstream-Repos gelesen), MEDIUM für
das dokumentierte Verhalten der Claude.ai- und ChatGPT-Connectoren (Hersteller-Doku bzw.
Community-Quellen, nicht gegen die echten Clients gemessen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Owner-Vorgabe (15.08.2026, bindend für alle Pläne dieser Phase)

Höchste Sicherheit und Zuverlässigkeit haben Vorrang vor Feature-Umfang und Komfort.
Konkret: konservative Spec-Auslegung, fail-closed überall, kein implizites Vertrauen,
Negativ- und Missbrauchstests sind Akzeptanzkriterien (nicht nur Happy Path),
klare Fehlerpfade und sauberer Wiederanlauf ohne kaputte Sessions.

### Locked Decisions

- **D-33:** Ein minimaler eigener Authorization Server als Teil der ExApp (gleiche
  Codebasis, eigener Routen-Namespace: PRM unter /.well-known, dazu authorize/token/
  register/revoke). Die Nutzer-Authentifizierung delegiert der AS an Nextcloud per
  Login Flow v2; wir speichern und prüfen NIE selbst ein Nextcloud-Passwort.
  Die Nextcloud-oauth2-App wird NICHT verwendet (kein DCR, kein PKCE-Zwang, nicht
  OAuth-2.1-konform); kein externes IdP in v1. Researcher prüft zuerst, wie viel
  davon das MCP-Python-SDK (mcp.server.auth) fertig mitbringt, bevor etwas selbst
  gebaut wird.

- **D-34:** Opake Zufalls-Tokens, keine JWTs in v1 (nichts, was ein Client falsch
  validieren kann; Widerruf wirkt sofort serverseitig, SC 4). Access-Token kurzlebig
  (Größenordnung 1 h), Refresh-Token mit Rotation UND Reuse-Detection (bei
  Wiederverwendung wird die ganze Token-Familie widerrufen). Audience-Binding
  (RFC 8707 resource parameter) ist Pflicht, Tokens gelten nur für diese Resource.
  Je Authorization wird genau ein dediziertes Nextcloud-App-Passwort (via Login
  Flow v2) erzeugt und verschlüsselt at rest abgelegt; Widerruf löscht Token UND
  App-Passwort. Ablageort und Verschlüsselungsverfahren entscheidet der Researcher
  (Kandidaten: SQLite im ExApp-Volume mit Schlüssel aus APP_SECRET-Ableitung);
  Klartext-Ablage ist verboten.

- **D-35:** DCR ist im Auslieferungszustand AN (SC 1 und 2 verlangen plug-and-play
  für Claude.ai und ChatGPT), ABER: Client-Registry mit allowed-Flag ab dem ersten
  Commit, Enforcement bei JEDER Token-Ausgabe und jedem authorize (nicht nur bei der
  Registrierung); globaler Schalter, der DCR komplett abschaltet; Allowlist-Modus
  (nur gelistete Client-IDs/Redirect-URIs), in v1 per Config/occ/Env schaltbar,
  Admin-UI folgt in Phase 4. Redirect-URIs matchen exakt (kein Prefix-Match),
  https ist Pflicht mit der spec-üblichen localhost-Ausnahme für native Clients.
  Registrierungen unbenutzter Clients verfallen (Aufräumen, kein unbegrenztes
  Wachstum der Registry).

- **D-36:** Clients ohne OAuth onboarden über den Login Flow v2 der Nextcloud
  selbst (poll-Endpunkt-Muster): Wir zeigen dem Nutzer den Browser-Link, Nextcloud
  führt den Login samt 2FA, das Ergebnis ist ein App-Passwort, das der Nutzer als
  Bearer nutzt (bestehender AUTH-01-Pfad bleibt unverändert). Der Client und wir
  sehen NIE das echte Passwort; einen eigenen Passwort-Prompt gibt es unter keinen
  Umständen.

- **D-37:** Token-Validierung läuft gegen den eigenen Store (kein Nextcloud-
  Roundtrip pro MCP-Request); ein kurzlebiger Validierungs-Cache hält auch das
  eigene Backend aus dem heißen Pfad. KEINE automatischen Auth-Retries gegen
  Nextcloud (Brute-Force-Guard-Schonung, Lehre aus Phase 1/Pitfall 8). 401 trägt
  immer den korrekten WWW-Authenticate-Header mit resource_metadata-Pointer
  (Spike-Ergebnis: Priorität 1, SEP-985), 429 trägt Retry-After. Fail-closed:
  Wenn Store oder Cache nicht erreichbar sind, wird abgelehnt, nie durchgewunken.

- **D-38:** Das akzeptierte Restrisiko AR-02-06 aus 02-SECURITY.md wird in dieser
  Phase geschlossen: die Manifest-Route ^/\.well-known/ wird auf exakt die
  benötigten Pfade eng gefasst; die neuen AS-Routen werden einzeln und minimal
  deklariert (authorize als Browser-Route PUBLIC, token/register/revoke mit eigenen
  Kontrollen und ohne Nutzer-Session). Die Spike-Topologie gilt: resource_metadata-
  Pointer im WWW-Authenticate zuerst, Reverse-Proxy-Fallback-Regel aus
  docs/spike-discovery.md dokumentiert halten.

- **D-39:** Der plug-and-play-Beweis mit Claude.ai- und ChatGPT-Connector braucht
  eine ÖFFENTLICH erreichbare Staging-Instanz (Domain + TLS). Das ist eine
  OWNER-ACTION (Domain/Server bereitstellen; Vorschlag: Subdomain auf vorhandener
  Infrastruktur mit Caddy). Alle übrigen Pläne laufen vorher lokal gegen die
  compose-Topologien; der E2E-Beweis ist ein eigener SPÄTER Plan mit
  Owner-Checkpoint und blockiert den Rest der Phase nicht.

- **D-40:** Missbrauchstests sind Akzeptanzkriterien der Pläne, mindestens:
  Refresh-Token-Replay nach Rotation (Familie stirbt), widerrufener Client bekommt
  401 mit korrektem WWW-Authenticate und kann sich sauber neu verbinden (SC 4),
  falsche/abweichende redirect_uri wird abgelehnt, PKCE-Downgrade (fehlendes oder
  plain challenge) wird abgelehnt, Audience-Mismatch wird abgelehnt, bei DCR=aus
  scheitert die Registrierung mit benennender Meldung, Allowlist-Modus blockt
  nicht gelistete Clients an authorize UND token.

### Claude's Discretion

- Interne Modulstruktur des AS, Schema des Token-Stores, exakte Lebensdauern
  (innerhalb "kurz"), Wortlaut der Consent-Seite (ui-phase darf im plan-chain
  triggern, UI hint = yes), Reihenfolge der Pläne, solange der E2E-Beweis hinten
  liegt und die Härtung (D-38) früh kommt.

### Deferred Ideas (OUT OF SCOPE)

- Admin-UI für Client-Allowlist und DCR-Schalter: Phase 4 (Enforcement-Punkt
  entsteht in Phase 3, D-35).
- Datenfluss-Disclosure-Text: Phase 6 (Owner-Entscheid 14.08., Punkt 3).
- Findling-Synergie (README-Cross-Link, Content-Hit-Fidelity-Test): BACKLOG.md
  BL-01..03, Trigger Findling v1.0.
- AIO-Smoke, WR-12 socat-Loop, cosign: Phase 5 (Übergaben aus Phase 2).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-02 | Nutzer kann sich per Login Flow v2 onboarden (Browser-Login, Client sieht nie das echte Passwort) | Abschnitt "Login Flow v2": exakter Ablauf, Endpunkte, 20-Minuten-Lifetime, One-shot-Poll, User-Agent wird zum Client-Namen, Widerruf per `DELETE /ocs/v2.php/core/apppassword`. Code-Beispiel 3. |
| AUTH-03 | OAuth 2.1 nach MCP-Authorization-Spec: PRM (RFC 9728), DCR, PKCE S256, Token-Widerruf | Abschnitte "Was das SDK mitbringt / was fehlt", "Discovery-Topologie", Pitfalls 1 bis 4, Code-Beispiele 1, 2, 4, 5 |
| AUTH-04 | Claude.ai- und ChatGPT-Connector verbinden plug-and-play gegen öffentliche Staging-Instanz | Abschnitt "Client-Verhalten Claude.ai und ChatGPT" (Redirect-URIs, DCR-Payload, Timeouts, Refresh-Verhalten), Pitfall 2 (AS-Metadata unter gestripptem Präfix), Environment Availability |
| AUTH-07 | Admin kann steuern, welche OAuth-Clients sich verbinden dürfen (Registry mit allowed-Flag, DCR global abschaltbar) | Abschnitt "Client-Registry und Allowlist", Enforcement-Punkte in `get_client`, Pitfall 9, Code-Beispiel 5 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Verbindliche Direktiven aus `./CLAUDE.md`, die der Planer prüfen muss:

| Direktive | Konsequenz für Phase 3 |
|-----------|------------------------|
| Python nur über `uv run --no-sync`, kein `uv sync` | Jede Task-Action, die Python startet, nutzt `uv run --no-sync`. Ein neuer direkter Dependency-Eintrag erfordert einen bewussten Lock-Schritt und Owner-Freigabe (Dependency-Audit). |
| Tech-Stack: `mcp>=2.0,<3`, Fallback-Pin `>=1.29,<2` | Installiert und gelockt ist **mcp 2.0.0**. Alle SDK-Aussagen dieser Recherche stammen aus dem Quellcode dieser Version in `.venv`. |
| Kein Session-State in Tools, multi-worker-fähig (SRV-05) | Token-Store und Pending-Authorization-Store müssen prozessübergreifend konsistent sein (SQLite mit WAL), Validierungs-Cache bleibt prozesslokal mit kurzer TTL. |
| Der MCP darf nie mehr sehen als der angemeldete Nutzer (AUTH-05) | Das aus dem OAuth-Token abgeleitete Nextcloud-Credential ist immer das eines konkreten Nutzers, nie ein App-Kontext ohne Nutzer. |
| Keine destruktiven Writes in v1 | Ausnahme mit Ansage: der Widerruf löscht das eigene App-Passwort (`DELETE /ocs/v2.php/core/apppassword`) und eigene Store-Zeilen. Das ist kein Nutzerdaten-Write und gehört in die Permission-Tabelle als Ausnahme dokumentiert. |
| Code und Doku Englisch, Projektkommunikation Deutsch, keine Em-Dashes, echte Umlaute | Modul-Docstrings, `docs/*.md` und Fehlermeldungen Englisch; `.planning/*` Deutsch. |
| Gates vor jedem Commit (D-32): ruff, pyright, vulture, pytest, Tool-Budget | Unverändert gültig; `cryptography` und `sqlite3` brauchen keine Stubs, `pyright` läuft im `standard`-Modus. |
| Konto-Trennung, Repo public auf GitHub street1983nk | Kein Secret in Fixtures, keine echten Client-Secrets in Tests. |
| Nach jedem Edit sofort committen, keine Claude-Attribution | Unverändert. |

Zusätzlich aus der Umgebungsvorgabe dieser Phase: **die Instanzen `nc-mcp-test` (8080) und
`findling-nextcloud` werden nicht angefasst**; Messungen laufen ausschließlich gegen die
Wegwerf-Topologie aus `compose.exapp.yml` (Port 8081).

## Summary

Die zentrale Frage der Phase ("wie viel bringt das SDK mit") hat eine überraschend gute und
eine unangenehme Antwort. Die gute: **mcp 2.0.0 liefert einen vollständigen
Authorization-Server-Rahmen** mit `/authorize`, `/token`, `/register` (RFC 7591),
`/revoke` (RFC 7009), RFC-8414-Metadata und RFC-9728-PRM als fertige Starlette-Routen
(`mcp.server.auth.routes.create_auth_routes`). PKCE S256 wird erzwungen (`code_challenge`
ist Pflichtfeld, `code_challenge_method` ist ein `Literal["S256"]`), der Code-Verifier wird
geprüft, `redirect_uri` wird exakt gegen die Registrierung gematcht, der Authorization-Code
läuft ab, Client-Authentifizierung am Token-Endpunkt ist implementiert. Wir implementieren
nur das `OAuthAuthorizationServerProvider`-Protokoll (11 async-Methoden) plus den
Token-Verifier und bekommen die gesamte HTTP-Schicht geschenkt. Die frühere
STACK.md-Annahme "das SDK stellt keinen Authorization Server, vier Endpoints selbst bauen"
ist für 2.0.0 **falsch** und darf nicht in die Pläne übernommen werden.

Die unangenehme Antwort: das SDK registriert seine Metadaten-Routen an den kanonischen
RFC-Pfaden **relativ zum eigenen App-Root**, und unser App-Root liegt hinter dem von HaRP
gestrippten Präfix `/exapps/mcp_connector`. Genau darum ist der kanonische PRM-Pfad im
Spike ein 404 gewesen. Für die Authorization-Server-Metadaten gilt dasselbe Problem ein
zweites Mal, und dort rettet uns der `resource_metadata`-Pointer nicht, weil es für AS-
Metadaten keinen Pointer gibt. Es bleiben genau drei Wege: (1) der von der Spec verlangte
dritte Discovery-Versuch `<issuer>/.well-known/openid-configuration` mit angehängtem Pfad,
den wir **selbst ausliefern können**, weil er unter unserem Präfix liegt; (2) zwei
Reverse-Proxy-Regeln des Admins, die die beiden Wurzelpfade auf die ExApp mappen; (3) eine
eigene Subdomain. Die Empfehlung ist (1) als Primärweg **und** (2) als dokumentierte
Absicherung, weil unbekannt ist, ob Claude.ai und ChatGPT die dritte Variante wirklich
probieren. Die Staging-Instanz aus D-39 läuft ohnehin hinter Caddy, dort kosten die zwei
Regeln nichts.

Der zweite große Befund betrifft SC 5 und kommt aus dem HaRP-Quellcode: **HaRP fragt bei
JEDEM Request mit einem `Authorization`-Header Nextcloud nach dem Nutzer**
(`/index.php/apps/app_api/harp/user-info`), auch auf PUBLIC-Routen, und cacht das Ergebnis
nur für Cookie-Sessions, nicht für Bearer-Token. Jeder MCP-Request mit unserem
OAuth-Bearer kostet also einen kompletten Nextcloud-PHP-Roundtrip, den wir nicht abstellen
können. Die gute Nachricht: ein unbekannter Bearer registriert in Nextcloud **keinen**
Brute-Force-Versuch (`Session::tryTokenLogin` gibt bei `InvalidTokenException` einfach
`false` zurück, ohne `registerAttempt`), anders als Basic-Auth. SC 5 ist damit erreichbar,
aber die Messung muss die Roundtrips zählen, nicht nur die Throttler-Zähler.

**Primary recommendation:** Das `OAuthAuthorizationServerProvider`-Protokoll von mcp 2.0.0
implementieren statt eigener Endpunkte, die vier fehlenden Sicherheitskontrollen
(Audience-Prüfung nach RFC 8707, https-Zwang für redirect_uris, Refresh-Rotation mit
Reuse-Detection, Client-Allowlist) im Provider ergänzen, die Metadaten-Dokumente zusätzlich
an den unter dem gestrippten Präfix erreichbaren Pfaden ausliefern und die Nutzer-
Authentifizierung über eine eigene Consent-Seite führen, die den Login Flow v2 anstößt und
per Poll auf das App-Passwort wartet.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Discovery-Dokumente (PRM, AS-Metadata) ausliefern | ExApp (Starlette-Routen) | Reverse Proxy des Admins (Rewrite der Wurzelpfade) | Statische, konfigurationsabgeleitete Dokumente; der Proxy fügt nur einen zweiten Weg zu einem bewusst öffentlichen Endpunkt hinzu |
| Client-Registrierung (DCR) und Registry | ExApp (Provider `register_client`/`get_client`) | Store (SQLite) | Enforcement-Punkt für AUTH-07; muss Container-Neustart überleben |
| Nutzer-Authentifizierung (wer ist das?) | Nextcloud (Login Flow v2, inkl. 2FA) | Browser des Nutzers | Wir sehen niemals ein Passwort; Nextcloud ist die einzige Identitätsquelle (D-33, D-36) |
| Consent-Anzeige und Rückführung zum Client | ExApp (HTML-Seite plus Status-Endpunkt) | Browser (Polling per JS) | Der Login Flow v2 kennt keine Rückleitung zu einer Redirect-URI; die Brücke muss bei uns liegen |
| Token-Ausgabe, -Rotation, -Widerruf | ExApp (Provider) | Store (SQLite) | Opake Tokens ohne Introspection-Roundtrip (D-34, D-37) |
| Token-Validierung pro MCP-Request | ExApp (TokenVerifier plus Prozess-Cache) | Store (SQLite) | Kein Nextcloud-Roundtrip (D-37) |
| Nextcloud-Zugriff im Namen des Nutzers | Nextcloud (Basic-Auth mit App-Passwort) | ExApp (Credential-Resolver) | Berechtigungs-Durchgriff, AUTH-05; App-Passwort ist der Nachweis der Nutzer-Zustimmung |
| Zugriffsschutz der Routen (PUBLIC/USER) | AppAPI-Manifest plus HaRP | ExApp-Middleware | Policy gehört ins Manifest (Phase-2-Muster), die ExApp bleibt Responder |
| Verschlüsselungsschlüssel für den Store | Nextcloud (ExApp-Config, `sensitive=1`) | ExApp (Cache im Speicher) | Trennt Schlüssel und Daten; überlebt eine APP_SECRET-Rotation |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp[cli]` | 2.0.0 (gelockt, installiert) | AS-Routen, Provider-Protokoll, Token-Verifier, Bearer-Middleware, PRM | Bereits Projekt-Dependency; liefert die komplette OAuth-HTTP-Schicht spec-konform [VERIFIED: uv.lock Zeile 418f, Quellcode in `.venv/Lib/site-packages/mcp/server/auth/`] |
| `cryptography` | 50.0.0 (bereits im Lock, transitiv über `mcp` -> `pyjwt[crypto]`) | AEAD-Verschlüsselung der App-Passwörter at rest (AESGCM), HKDF für Teilschlüssel | De-facto-Standard für Python-Krypto, keine Eigenbau-Krypto [VERIFIED: PyPI-JSON, `github.com/pyca/cryptography`, 158 Releases, installiert 50.0.0] |
| `sqlite3` | Python 3.13 stdlib | Token-Store, Client-Registry, Pending-Authorizations | Keine neue Dependency, ACID, WAL-Modus, eine Datei im ExApp-Volume |
| `httpx` | 0.28.1 (Projekt-Dependency) | Login-Flow-v2-Calls und OCS-Calls gegen Nextcloud | Bereits der eine HTTP-Client des Projekts |
| `secrets` | stdlib | Token-Erzeugung (`token_urlsafe(32)`), `compare_digest` | Projektmuster aus Phase 1/2 |
| `hashlib` | stdlib | SHA-256-Hash der Tokens für die Ablage (nie Klartext-Token in der DB) | Standard |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic` | 2.13.x | Modelle des SDK (`OAuthClientInformationFull`, `AccessToken`, ...) | Wird vom SDK erzwungen, kein eigener Bedarf |
| `starlette` | via mcp | Routen, HTML-Response der Consent-Seite | Bereits im Einsatz |
| `pytest` + `respx` | dev | Unit-Tests des Providers, Mock-Transport für Login-Flow-v2-Calls | Testmuster aus Phase 1/2 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SDK-`create_auth_routes` mit eigenem Provider | Vier eigene Starlette-Routen (Annahme aus STACK.md) | Der Eigenbau müsste PKCE-Prüfung, redirect_uri-Matching, Code-Ablauf, Client-Auth und die RFC-konformen Fehlerformate nachbauen, die im SDK bereits mit Tests liegen. Nur sinnvoll, wenn das SDK eine Kontrolle aktiv verhindert; das tut es nicht, alle fehlenden Kontrollen sind im Provider ergänzbar |
| Opake Tokens (D-34) | JWT mit PyJWT | Von D-34 ausgeschlossen; JWT würde Sofort-Widerruf (SC 4) nur mit Denylist erreichen und dem Client eine falsch validierbare Struktur geben |
| SQLite | JSON-Datei im Volume | Keine Atomarität bei Refresh-Rotation, kein Index, Race bei parallelen Refreshes |
| `sqlite3` in `asyncio.to_thread` | `aiosqlite` | Neue direkte Dependency für ein 30-Zeilen-Wrapper-Problem; das Projekt hält die Dependency-Fläche bewusst klein (docs/dependency-audit.md) |
| AESGCM mit AAD | `cryptography.fernet.Fernet` | Fernet ist einfacher, bindet aber den Chiffretext nicht an die Zeilen-Identität; ein Angreifer mit Schreibzugriff auf die DB könnte Chiffretexte zwischen Zeilen tauschen. AESGCM mit `aad = authorization_id` schließt das |
| Schlüssel in der Nextcloud-ExApp-Config (`sensitive=1`) | Schlüsseldatei im selben Volume | Die Datei liegt neben der Datenbank: wer das Volume liest, hat beides. Die ExApp-Config liegt in Nextclouds `oc_appconfig`, verschlüsselt mit dem Server-Secret, also in einem anderen Vertrauensbereich |
| Schlüssel in der Nextcloud-ExApp-Config | Ableitung aus `APP_SECRET` (Kandidat aus D-34) | **Nicht empfehlenswert:** `APP_SECRET` wird bei jeder Registrierung neu erzeugt, wenn die Registrierung keinen mitbringt (`scripts/bootstrap_exapp.sh`, Zeile 602). Nach einem App-Update oder einer Neuregistrierung wären alle gespeicherten App-Passwörter unlesbar, alle Verbindungen tot. Das verletzt die Zuverlässigkeits-Vorgabe des Owners |

**Installation:** keine neue Installation nötig. Falls `cryptography` von einer transitiven
zu einer direkten Dependency befördert werden soll (empfohlen, weil wir es direkt
importieren, siehe Dependency-Policy in `docs/dependency-audit.md`):

```bash
# nur mit Owner-Freigabe und bewusstem Lock-Schritt, NICHT als Nebenwirkung eines Plans
uv add "cryptography>=50,<51"
```

**Version verification:** `mcp` 2.0.0 und `cryptography` 50.0.0 sind in `uv.lock` gepinnt
und in `.venv` installiert; beide wurden für diese Recherche direkt aus dem
Installationsverzeichnis bzw. der PyPI-JSON-API gelesen, nicht aus dem Gedächtnis.

## Package Legitimacy Audit

Diese Phase installiert **keine neuen Pakete**. Der einzige Kandidat für eine Beförderung
von transitiv zu direkt ist `cryptography`, das bereits im Lock steht.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| cryptography | PyPI | 158 Releases, aktuell 50.0.0 vom 2026-07-31 | sehr hoch (Top-20-PyPI-Paket) | github.com/pyca/cryptography | nicht ausführbar (siehe unten) | Approved, manuell verifiziert |
| mcp | PyPI | 2.0.0 seit 2026-07-28 | sehr hoch | github.com/modelcontextprotocol/python-sdk | [OK] (Phase-1-Audit) | Approved (bereits direkt) |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine neuen. `httpx2` bleibt der bekannte
[SUS]-Fall aus `docs/dependency-audit.md` und bleibt transitiv.

*slopcheck war in dieser Session nicht lauffähig: `uv tool run --from slopcheck slopcheck
install cryptography` bricht mit `FileNotFoundError` ab, weil das Tool intern `pip` aufruft
und in dieser uv-Umgebung kein `pip` auf dem PATH liegt. Verifikation daher manuell über
die PyPI-JSON-API (Projekt-URLs zeigen auf `github.com/pyca/cryptography`, 158 Releases,
Upload-Zeitpunkt 2026-07-31). Weil `cryptography` bereits über `mcp` -> `pyjwt[crypto]` im
gelockten Environment liegt, kommt durch die Beförderung kein neuer Code ins Image; die
Entscheidung ist rein deklarativ. Ein `checkpoint:human-verify` ist trotzdem angemessen,
wenn der Planer die Beförderung in einen Task gießt.*

## Architecture Patterns

### System Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
   MCP-Client           │  Browser des Nutzers                        │
   (Claude.ai,          │  (nur waehrend der Autorisierung)           │
    ChatGPT)            └───────────────┬─────────────────────────────┘
        │                               │
        │ 1. POST /mcp ohne Token       │ 4. GET /authorize (Consent-Seite)
        │ 2. GET  resource_metadata     │ 5. Fenster auf Nextcloud-Login
        │ 3. GET  AS-Metadata           │ 6. JS-Poll auf /authorize/status
        │ 8. POST /token (code+verifier)│ 7. Redirect auf redirect_uri?code=..&iss=..
        v                               v
┌──────────────────────────────────────────────────────────────────────────────┐
│  Reverse Proxy (Caddy/nginx des Admins)                                      │
│   /exapps/*                                    -> HaRP                       │
│   /.well-known/oauth-protected-resource/...    -> HaRP (Fallback-Regel)      │
│   /.well-known/oauth-authorization-server/...  -> HaRP (Fallback-Regel)      │
│   alles andere                                 -> Nextcloud                  │
└───────────────┬──────────────────────────────────────────────┬───────────────┘
                │                                              │
                v                                              v
┌───────────────────────────────────┐            ┌────────────────────────────┐
│  HaRP                             │            │  Nextcloud (PHP)           │
│  - prueft access_level je Route   │  user-info │  - Login Flow v2 UI + 2FA  │
│  - bei Authorization-Header:      │───────────>│  - erzeugt App-Passwort    │
│    Nutzer-Lookup bei Nextcloud    │            │  - OCS: ExApp-Config,      │
│  - setzt AUTHORIZATION-APP-API    │            │    apppassword loeschen    │
└───────────────┬───────────────────┘            └──────────▲─────────────────┘
                │ Praefix gestrippt                          │ httpx (Basic / AppAPI)
                v                                            │
┌──────────────────────────────────────────────────────────────────────────────┐
│  ExApp-Prozess (uvicorn, ein Container)                                      │
│                                                                              │
│  Transportgrenze:  RequireAppApi  ->  RequireMcpAuth (neu)                   │
│      AppAPI-Header mit Nutzer  ->  bestehender AUTH-01/AUTH-05-Pfad          │
│      AppAPI-Header ohne Nutzer ->  Bearer pruefen  ->  401 + WWW-Authenticate│
│                                                                              │
│  AS-Routen (SDK create_auth_routes + eigene Zusatzpfade)                     │
│      /authorize  /token  /register  /revoke                                  │
│      /.well-known/oauth-protected-resource/mcp                               │
│      /.well-known/openid-configuration      (AS-Metadata, Pfad-Anhaengung)   │
│      /.well-known/oauth-authorization-server(AS-Metadata, fuer Proxy-Regel)  │
│      /authorize/status  (Poll-Brücke fuer die Consent-Seite)                 │
│                                                                              │
│  NextcloudOAuthProvider (implementiert OAuthAuthorizationServerProvider)     │
│      get_client / register_client   -> Registry + Allowlist (AUTH-07)        │
│      authorize                      -> Login Flow v2 starten, Consent-Seite  │
│      exchange_authorization_code    -> Audience pruefen, Tokens ausgeben     │
│      exchange_refresh_token         -> Rotation + Reuse-Detection            │
│      revoke_token                   -> Familie toeten + App-Passwort loeschen│
│                                                                              │
│  TokenStore (SQLite, WAL, im ExApp-Volume)  +  Prozess-Cache (TTL, klein)    │
│      clients | authorizations | access_tokens | refresh_tokens | flows       │
│      App-Passwort AESGCM-verschluesselt, Schluessel aus der Nextcloud-Config │
└──────────────────────────────────────────────────────────────────────────────┘
```

Der Datenfluss des Hauptfalls, den ein Leser den Pfeilen entlang nachvollziehen kann:
Client fragt `/mcp` ohne Token an (1), bekommt 401 mit `WWW-Authenticate` inklusive
`resource_metadata`, holt PRM (2) und AS-Metadata (3), registriert sich per DCR, schickt
den Browser auf `/authorize` (4), der Browser meldet sich bei Nextcloud an (5), unsere
Seite pollt bis das App-Passwort vorliegt (6), leitet mit `code` und `iss` zurück (7), der
Client tauscht Code gegen Token (8) und spricht danach MCP mit `Authorization: Bearer`.

### Recommended Project Structure

```
src/mcp_connector/
├── oauth/
│   ├── __init__.py        # public surface: build_oauth_routes, NextcloudOAuthProvider
│   ├── provider.py        # OAuthAuthorizationServerProvider-Implementierung
│   ├── verifier.py        # TokenVerifier + Prozess-Cache, Audience-Pruefung
│   ├── store.py           # SQLite-Schema, Migration, alle Queries, WAL
│   ├── crypto.py          # AESGCM-Wrapper, Schluesselbezug, HKDF
│   ├── registry.py        # Client-Registry-Policy: DCR-Schalter, Allowlist (AUTH-07)
│   ├── loginflow.py       # Nextcloud Login Flow v2 (init, poll, App-Passwort loeschen)
│   ├── metadata.py        # Metadaten-Dokumente an den erreichbaren Pfaden
│   └── consent.py         # Consent-Seite (HTML) + /authorize/status
├── exapp/
│   ├── middleware.py      # RequireAppApi bleibt, bekommt den Bearer-Zweig
│   └── discovery.py       # Spike-Modul, wird ersetzt (nicht erweitert)
└── config.py              # neue Env-Schalter, public_url-Ableitung
```

### Pattern 1: Provider implementieren statt Endpoints bauen

**What:** Das SDK bietet mit `OAuthAuthorizationServerProvider` ein Protocol mit elf
async-Methoden. `create_auth_routes(provider, issuer_url, ...)` erzeugt daraus fertige
Starlette-Routen für `/authorize`, `/token`, `/register`, `/revoke` und die AS-Metadata.
**When to use:** Immer. Der Eigenbau lohnt nur, wenn eine benötigte Kontrolle im SDK
verhindert wird; keine der Kontrollen aus D-34/D-35/D-37 wird verhindert.
**Example:**

```python
# Source: .venv/Lib/site-packages/mcp/server/auth/routes.py (mcp 2.0.0)
from mcp.server.auth.routes import create_auth_routes
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions

routes = create_auth_routes(
    provider=NextcloudOAuthProvider(store, login_flow, policy),
    issuer_url=AnyHttpUrl(public_base),            # z.B. https://cloud.example.com/exapps/mcp_connector
    client_registration_options=ClientRegistrationOptions(
        enabled=policy.dcr_enabled,                 # AUTH-07: global abschaltbar
        client_secret_expiry_seconds=None,
        valid_scopes=["nextcloud:read", "nextcloud:write"],
        default_scopes=["nextcloud:read"],
    ),
    revocation_options=RevocationOptions(enabled=True),   # SC 4
)
```

### Pattern 2: Die vier Lücken im Provider schließen

**What:** Das SDK prüft PKCE, `redirect_uri`, Code-Ablauf und Client-Auth. Es prüft
**nicht**: den RFC-8707-`resource`-Parameter, das https-Gebot für Redirect-URIs,
Refresh-Rotation samt Reuse-Detection und eine Client-Allowlist. Alle vier gehören in den
Provider und sind damit Pflichtinhalt der Pläne.
**When to use:** Immer; jede der vier Lücken hat einen Missbrauchstest in D-40.
**Example:**

```python
# Audience-Binding, RFC 8707 und MCP-Spec ("MUST validate that access tokens were
# issued specifically for them as the intended audience").
from mcp.shared.auth_utils import check_resource_allowed, resource_url_from_server_url

async def exchange_authorization_code(self, client, authorization_code):
    requested = authorization_code.resource
    if requested is None:
        # Fail-closed (Owner-Vorgabe): ein Token ohne Audience waere ueberall gueltig.
        raise TokenError("invalid_target", "the resource parameter is required")
    if not check_resource_allowed(requested, self._canonical_resource):
        raise TokenError("invalid_target", "the resource does not match this server")
    ...
```

### Pattern 3: Consent-Seite als Brücke zum Login Flow v2

**What:** Der Login Flow v2 kennt keine Rückleitung zu einer Redirect-URI. Nextcloud zeigt
am Ende eine eigene "Account verbunden"-Seite. Die Brücke zurück zum OAuth-Client muss bei
uns liegen: `/authorize` antwortet mit einer eigenen HTML-Seite, die den Login in einem
neuen Fenster öffnet und per JS unseren Status-Endpunkt pollt.
**When to use:** Für jeden `authorize`-Request. Das ist der UI-Anteil der Phase (UI hint =
yes).
**Ablauf:**

1. `authorize()` des Providers legt einen Pending-Flow an (`flow_id`, `client_id`,
   `redirect_uri`, `code_challenge`, `state`, `resource`, `scopes`, Ablauf 20 Minuten) und
   ruft `POST <nc>/index.php/login/v2` mit einem sprechenden `User-Agent` auf.
2. Der Provider gibt die URL unserer eigenen Consent-Seite zurück
   (`/authorize/consent?flow=<flow_id>`); das SDK leitet den Browser dorthin (302).
3. Die Seite zeigt Client-Name, Instanzname, angeforderte Scopes, Redirect-Host und einen
   Button "Bei Nextcloud anmelden", der die `login`-URL in einem neuen Fenster öffnet.
4. Ein JS-Intervall (z.B. alle 2 s, mit Deckel) fragt `/authorize/status?flow=<flow_id>`;
   dieser Endpunkt macht **genau einen** Poll gegen `POST <nc>/login/v2/poll`.
5. Sobald der Poll 200 liefert: App-Passwort verschlüsselt ablegen, Authorization-Code
   erzeugen, Antwort `{"redirect": "<redirect_uri>?code=..&state=..&iss=.."}`; das JS
   navigiert dorthin.

**Warum kein `access_level=USER` auf `/authorize`:** Das wäre bequemer (HaRP löst den
Nutzer aus dem Session-Cookie auf), aber ein nicht angemeldeter Nutzer bekäme von HaRP ein
nacktes 403 statt einer Anmeldemaske, weil HaRP keine Login-Weiterleitung kennt. D-38
verlangt deshalb korrekt PUBLIC.

### Pattern 4: Zwei Identitätsquellen an einer Transportgrenze

**What:** `/mcp` wechselt von `access_level=USER` auf `PUBLIC` (Spike, "Open items for
phase 3"). Danach setzt HaRP weiterhin `AUTHORIZATION-APP-API`, aber der Nutzer darin ist
leer, wenn der Aufrufer kein Nextcloud-Credential mitgeschickt hat. Die Middleware bekommt
damit zwei Fälle statt einem.
**When to use:** Genau einmal, in `exapp/middleware.py`.
**Regel:**

- AppAPI-Header gültig **und** Nutzer nicht leer -> bestehender Pfad (AUTH-01 über
  App-Passwort/Basic, AUTH-05 über Impersonation). Kein Bearer wird gelesen.
- AppAPI-Header gültig **und** Nutzer leer -> unser OAuth-Pfad: `Authorization: Bearer`
  gegen den TokenVerifier prüfen, bei Misserfolg 401 mit `WWW-Authenticate`.
- AppAPI-Header ungültig -> 401 wie bisher, ohne Hinweis.

Ein Fallback von OAuth auf Basic oder umgekehrt gibt es nicht (D-27).

### Anti-Patterns to Avoid

- **`RequireAuthMiddleware` des SDK unverändert vor `/mcp` hängen:** Sie verlangt einen
  Bearer und würde den bestehenden AUTH-01-Pfad (Basic-App-Passwort über HaRP) mit 401
  abweisen. Die Middleware ist als Vorlage gut, als Wrapper falsch.
- **`auth_server_provider=` am `MCPServer`-Konstruktor setzen:** funktioniert zwar (das
  SDK baut daraus `ProviderTokenVerifier`), hängt die AS-Routen aber an die MCP-App und
  verwendet `load_access_token` als Verifier, wodurch der Prozess-Cache und die
  Audience-Prüfung umgangen werden. Besser: Routen mit `create_auth_routes` selbst
  einhängen, Verifier separat setzen.
- **Discovery-Dokumente aus dem Request ableiten** (Host-Header, `X-Forwarded-Host`):
  Phase 2 hat das bewusst ausgeschlossen (T-02-41); ein gefälschter Host darf die
  Metadaten nicht ändern. Die öffentliche Basis kommt aus der Konfiguration bzw. aus
  Nextclouds `overwrite.cli.url`.
- **Klartext-Token in der Datenbank:** In der DB steht der SHA-256-Hash, nie der Token.
  Sonst wird ein DB-Leak zum sofortigen Vollzugriff auf alle verbundenen Konten.
- **Automatischer Retry bei fehlgeschlagenem Login-Flow-Poll oder App-Passwort-Löschen:**
  verstößt gegen D-37 und gegen die Phase-1-Lehre (Pitfall 8).
- **Ein App-Passwort für mehrere Autorisierungen wiederverwenden:** Der Widerruf einer
  Verbindung würde die anderen mit killen (D-34: genau eines je Authorization).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| `/authorize`, `/token`, `/register`, `/revoke` | Eigene Starlette-Routen mit eigenem Fehlerformat | `mcp.server.auth.routes.create_auth_routes` | RFC-konforme Fehlerobjekte, Redirect-vs-JSON-Entscheidung bei Fehlern, `Cache-Control: no-store` auf Token/Revoke, Form-Parsing, alles getestet |
| PKCE-Prüfung | Eigener S256-Vergleich | SDK-`TokenHandler` | Base64url ohne Padding, `invalid_grant` statt `invalid_request`, korrekt nach RFC 7636 §4.6 |
| `redirect_uri`-Matching | Eigener String-Vergleich | `OAuthClientInformationFull.validate_redirect_uri` | Exakter Listenvergleich plus die Sonderregel "genau eine registrierte URI darf weggelassen werden" |
| Client-Authentifizierung am Token-Endpunkt | Eigener Secret-Vergleich | `mcp.server.auth.middleware.client_auth.ClientAuthenticator` | `hmac.compare_digest`, Basic- und Post-Variante, Ablauf des Client-Secrets |
| Nutzer-Login inklusive 2FA | Eigenes Login-Formular oder Passwort-Prompt | Nextcloud Login Flow v2 | D-36; wir dürfen ein Passwort nie sehen, 2FA und Passwort-Policy bleiben bei Nextcloud |
| App-Passwort erzeugen | Eigener Token-Provider-Aufruf | `POST /index.php/login/v2` plus Poll | Der einzige unterstützte Weg ohne Passwort |
| App-Passwort widerrufen | Eigene Session-Manipulation | `DELETE /ocs/v2.php/core/apppassword` mit genau diesem App-Passwort | Löscht exakt das eigene Token, kein Fremdzugriff nötig [VERIFIED: `core/Controller/AppPasswordController.php`] |
| Schlüsselspeicher | Eigene Keyfile-Logik mit Rechteprüfung | AppAPI-ExApp-Config mit `sensitive=1` | Nextcloud verschlüsselt den Wert mit dem Server-Secret; die Trennung Schlüssel/Daten entsteht dadurch von selbst |
| Öffentliche Basis-URL erraten | Host-Header, Env-Raten | `GET /ocs/v2.php/apps/app_api/api/v1/info/nextcloud_url/absolute?url=/exapps/<app_id>` | Liefert `overwrite.cli.url` plus Pfad, also genau die URL, die der Nutzer im Client eintippt [VERIFIED: `lib/Controller/OCSApiController.php`] |
| Nutzerauflösung aus App-Passwort/Basic | Eigene Session-Prüfung | `access_level` im Manifest, HaRP macht `user-info` | Phase-2-Muster, unverändert gültig |

**Key insight:** In dieser Phase ist fast alles, was nach "OAuth-Server bauen" klingt,
bereits im SDK oder in Nextcloud vorhanden. Der Eigenanteil ist klein und liegt genau dort,
wo Sicherheitsentscheidungen fallen: Audience, Allowlist, Rotation, Verschlüsselung,
Widerruf. Genau diese fünf sind auch die Stellen, an denen D-40 Missbrauchstests verlangt.

## Common Pitfalls

### Pitfall 1: Der kanonische PRM-Pfad liegt außerhalb der ExApp (bekannt aus Phase 2)

**What goes wrong:** `create_protected_resource_routes` registriert die Route unter dem aus
`resource_server_url` abgeleiteten Pfad. Für `https://cloud.example.com/exapps/mcp_connector/mcp`
ist das `/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp` **innerhalb** der
ExApp, wo nie ein Request ankommt (HaRP strippt das Präfix, es kommt
`/.well-known/oauth-protected-resource/mcp` an).
**Why it happens:** RFC 9728 §3.1 schiebt das Well-known-Segment zwischen Host und Pfad.
**How to avoid:** Das Dokument selbst mit `ProtectedResourceMetadata` bauen und an
`/.well-known/oauth-protected-resource/mcp` registrieren (so wie es der Spike-Code bereits
tut). Im `WWW-Authenticate` die **externe** URL nennen:
`https://cloud.example.com/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp`.
Claude erlaubt ausdrücklich, dass `resource_metadata` auf einen beliebigen HTTPS-Ort zeigt
[CITED: claude.com/docs/connectors/building/authentication].
**Warning signs:** Client meldet "could not discover authorization server", obwohl `/mcp`
einen 401 mit Header liefert.

### Pitfall 2: Für die AS-Metadaten gibt es keinen Pointer (die eigentliche neue Falle)

**What goes wrong:** Nachdem der Client das PRM gelesen hat, holt er die AS-Metadaten.
Dafür gibt es keinen Header-Pointer, nur die drei konstruierten Wege. Bei einem Issuer mit
Pfad (`https://cloud.example.com/exapps/mcp_connector`) sind das laut Spec, in dieser
Reihenfolge:

1. `https://cloud.example.com/.well-known/oauth-authorization-server/exapps/mcp_connector`
2. `https://cloud.example.com/.well-known/openid-configuration/exapps/mcp_connector`
3. `https://cloud.example.com/exapps/mcp_connector/.well-known/openid-configuration`

Die ersten beiden liegen auf der Domain-Wurzel und gehören Nextcloud. Nextclouds
`WellKnownController` matcht nur **ein** Pfadsegment
(`#[FrontpageRoute(url: '.well-known/{service}')]`), beide Varianten laufen also ins 404
[VERIFIED: `core/Controller/WellKnownController.php`]. Nur der dritte Weg liegt unter
unserem Präfix und ist von uns bedienbar.
**Why it happens:** RFC 8414 §3.1 nutzt Pfad-Einschub, OIDC Discovery §4 nutzt
Pfad-Anhängung; nur die Anhängung überlebt einen gestrippten Präfix.
**How to avoid:** Drei Maßnahmen zusammen:
(a) Das AS-Metadata-Dokument **zusätzlich** unter `/.well-known/openid-configuration`
ausliefern (Weg 3). Der `issuer` im Dokument muss exakt der Issuer sein, aus dem die URL
gebaut wurde, sonst verwirft ein spec-treuer Client das Dokument.
(b) Das Dokument auch unter `/.well-known/oauth-authorization-server` ausliefern, damit die
Reverse-Proxy-Regel des Admins etwas zum Weiterleiten hat.
(c) Zwei Rewrite-Regeln in `docs/` dokumentieren und auf der Staging-Instanz aktivieren.
**Warning signs:** Der MCP-Server sieht den ersten Request, der Authorization-Server sieht
gar nichts. Claude nennt genau dieses Symptom als typischen Discovery-Fehler
[CITED: claude.com/docs/connectors/building/authentication].

Caddy-Regeln für die Staging-Instanz (Ergänzung zu `deploy/Caddyfile`):

```caddyfile
@prm path /.well-known/oauth-protected-resource/exapps/mcp_connector/mcp
handle @prm {
    rewrite * /exapps/mcp_connector/.well-known/oauth-protected-resource/mcp
    reverse_proxy appapi-harp:8780
}

@asm path /.well-known/oauth-authorization-server/exapps/mcp_connector
handle @asm {
    rewrite * /exapps/mcp_connector/.well-known/oauth-authorization-server
    reverse_proxy appapi-harp:8780
}
```

### Pitfall 3: Das SDK prüft den `resource`-Parameter nicht

**What goes wrong:** `AuthorizationRequest` und beide Token-Requests nehmen `resource`
entgegen und reichen ihn an den Provider durch. Weder der Handler noch die
Bearer-Middleware vergleichen ihn jemals mit der eigenen Resource. Ein Token, das für einen
anderen MCP-Server ausgestellt wurde, würde von einer naiven `verify_token`-Implementierung
akzeptiert.
**Why it happens:** Das SDK überlässt die Policy bewusst dem Provider.
**How to avoid:** Zwei Prüfungen, beide fail-closed: beim Ausstellen
(`exchange_authorization_code`, `exchange_refresh_token`) mit `check_resource_allowed`, und
beim Verifizieren (`verify_token`) gegen `AccessToken.resource`. Fehlender `resource` wird
abgelehnt, nicht großzügig interpretiert (Owner-Vorgabe).
**Warning signs:** Der D-40-Test "Audience-Mismatch wird abgelehnt" ist grün, obwohl nichts
implementiert wurde, weil der Testfall am falschen Punkt ansetzt.

### Pitfall 4: PHP-Proxy cacht JSON eine Stunde, und das SDK setzt bei zwei Antworten das Falsche

**What goes wrong:** `createProxyResponse` des PHP-Proxys setzt `cacheFor(3600)`, wenn keine
`Cache-Control` gesetzt ist und der Content-Type exakt `application/json` lautet (Phase-2-
Pitfall 4). Die DCR-Antwort des SDK (`PydanticJSONResponse`, 201) trägt **keine**
`Cache-Control`. Die Metadaten-Handler des SDK setzen `Cache-Control: public, max-age=3600`,
was dem `no-store`-Muster des Projekts widerspricht und ein Dokument mit veralteter
öffentlicher URL eine Stunde festhält.
**Why it happens:** Das SDK optimiert für den Normalfall ohne Proxy.
**How to avoid:** Eine kleine ASGI-Middleware über alle AS-Routen, die `Cache-Control:
no-store` setzt, wenn die Antwort keine eigene trägt, und die `public, max-age=3600` der
Metadaten-Handler überschreibt. Alternativ die Metadaten-Dokumente ohnehin selbst
ausliefern (siehe Pitfall 2), dann bleibt nur `/register` übrig.
**Warning signs:** Ein zweiter Client bekommt über den PHP-Proxy-Pfad eine gecachte
Registrierungsantwort.

### Pitfall 5: HaRP fragt bei jedem Bearer-Request Nextcloud (SC 5)

**What goes wrong:** In `haproxy_agent.py` gilt: `if pass_cookie or "authorization" in
request_headers: nc_user = await get_session(pass_cookie) ... nc_get_user(...)`. Der
Session-Cache greift nur für Cookies (`HP_SESSION_LIFETIME`, Default 3 s, max 10 s), nicht
für Bearer-Token. Jeder MCP-Request mit unserem OAuth-Bearer erzeugt damit einen
Nextcloud-PHP-Request, den wir nicht abstellen können.
**Why it happens:** HaRP unterstützt App-Passwörter und Basic-Auth als Nutzerquelle und
kann einem Bearer nicht ansehen, dass er nicht für Nextcloud ist.
**How to avoid:** Nicht vermeidbar, aber messbar und einordbar:
(a) Ein unbekannter Bearer registriert in Nextcloud **keinen** Brute-Force-Versuch
(`Session::tryTokenLogin` gibt bei `InvalidTokenException` `false` zurück, ohne
`registerAttempt`; nur `logClientIn`, also Basic, ruft `handleLoginFailed`)
[VERIFIED: `lib/private/User/Session.php`]. SC 5 ist damit erfüllbar.
(b) `getUserInfo` antwortet für anonyme Requests mit 200 und `access_level=PUBLIC`, es
entsteht also auch kein HaRP-Blacklist-Eintrag (Blacklist: 10 Fehlversuche in 300 s)
[VERIFIED: `app_api/lib/Controller/HarpController.php`, `HaRP/haproxy_agent.py`].
(c) In der Abnahme von SC 5 die Nextcloud-Zugriffe zählen (Access-Log oder
`docker logs`), nicht nur die Antwortzeiten.
**Warning signs:** Lastprofil zeigt für jeden MCP-Call zwei Nextcloud-Requests statt einem.

### Pitfall 6: `/mcp` auf PUBLIC öffnet den Preamble, wenn der Verifier fehlt

**What goes wrong:** Sobald `access_level` auf PUBLIC steht, entscheidet HaRP nicht mehr
über Zugriff. Ohne eigene Prüfung würde die ExApp `initialize` und `tools/list`
unauthentifiziert beantworten. Der Spike nennt das ausdrücklich als offenen Punkt.
**Why it happens:** Die Umstellung ist für den 401-Discovery-Flow nötig, entfernt aber die
bisherige Schutzschicht.
**How to avoid:** Manifest-Änderung und Bearer-Prüfung **im selben Plan-Task**, nie
getrennt. Der bestehende Wächter-Test aus `entry_exapp.build_exapp_app` (genau eine
geschützte `/mcp`-Route, sonst `RuntimeError`) wird auf den neuen Wrapper erweitert.
**Warning signs:** Ein `curl` ohne Header bekommt eine JSON-RPC-Antwort statt 401.

### Pitfall 7: Login Flow v2 hat drei harte Eigenschaften, die man einmal falsch macht

**What goes wrong:** (a) Der Poll liefert 200 **genau einmal**; danach ist der Datensatz
gelöscht. Ein zweiter Poll und ein noch nicht fertiger Flow sind beide 404, also
ununterscheidbar. (b) Der Flow lebt 1200 Sekunden (`LoginFlowV2Mapper::lifetime = 1200`).
(c) Der `poll.endpoint` in der Antwort ist eine **öffentliche absolute URL**
(`linkToRouteAbsolute`, gebaut aus `overwrite.cli.url`), die der Container unter Umständen
gar nicht auflösen kann.
**Why it happens:** Der Flow ist für Desktop-Clients gebaut, nicht für Server.
**How to avoid:** Den Poll gegen die eigene konfigurierte Nextcloud-Basis mit festem Pfad
`/login/v2/poll` fahren, nicht gegen die zurückgegebene absolute URL. Den Flow-Datensatz
bei uns mit Ablauf 20 Minuten führen und die Consent-Seite nach Ablauf mit einer klaren
Meldung ("Anmeldung abgelaufen, bitte erneut verbinden") beenden. Das 200 sofort persistent
verarbeiten, bevor irgendetwas anderes passieren kann.
**Warning signs:** Sporadisch verlorene App-Passwörter; Poll-Timeouts, die im Log wie
Netzwerkfehler aussehen.

### Pitfall 8: Der Client-Name geht als `User-Agent` an Nextcloud

**What goes wrong:** `ClientFlowLoginV2Controller::init` liest den `user-agent`-Header und
macht daraus den Client-Namen, der dem Nutzer im Grant-Dialog und später in "Geräte und
Sitzungen" angezeigt wird. Der Name kommt bei uns aus `client_name` der DCR-Registrierung,
also aus Angreiferhand.
**Why it happens:** Kein Feld für einen Client-Namen im Login Flow v2, nur der User-Agent.
**How to avoid:** Den Namen strikt säubern: auf ASCII-druckbare Zeichen reduzieren, CR/LF
entfernen, auf etwa 64 Zeichen kürzen, mit festem Präfix versehen (z.B.
`MCP Connector: <name>`), damit der Nutzer im Nextcloud-Dialog sieht, wer fragt. Zusätzlich
bedenken: Admins können den Flow per `core.login_flow_v2.allowed_user_agents`
(Regex-Liste) einschränken; das Präfix macht eine Allowlist-Regel möglich.
**Warning signs:** Header-Injection-Test schlägt fehl; oder Nextcloud zeigt einen
irreführenden Namen im Grant-Dialog.

### Pitfall 9: Allowlist nur an `/register` prüfen

**What goes wrong:** D-35 verlangt Enforcement bei **jedem** `authorize` und **jeder**
Token-Ausgabe. Wer nur `register_client` prüft, lässt einen bereits registrierten, später
gesperrten Client weiterlaufen, bis dessen Token abläuft.
**Why it happens:** `get_client` sieht nach einem reinen Lookup aus.
**How to avoid:** `get_client` ist der Enforcement-Punkt. Ein gesperrter, abgelaufener oder
unbenutzt verfallener Client wird dort als `None` zurückgegeben; das SDK antwortet dann an
`/authorize` mit `invalid_request` und an `/token` mit 401 `invalid_client`. Zusätzlich in
`exchange_*` prüfen, damit ein Sperrvorgang mitten in einem Flow nicht durchrutscht, und im
Verifier, damit bestehende Access-Tokens sofort ungültig werden.
**Warning signs:** Der D-40-Test "Allowlist blockt an authorize UND token" prüft nur einen
der beiden.

### Pitfall 10: Zwei parallele Refreshes (Rotation-Race)

**What goes wrong:** Zwei gleichzeitige `refresh_token`-Requests mit demselben Token: ohne
Transaktion bekommen beide neue Familien, oder einer tötet die Familie des anderen als
vermeintlichen Replay. Claude refresht reaktiv auf 401 **und** proaktiv bis zu fünf Minuten
vor Ablauf, ein Parallelfall ist also realistisch
[CITED: claude.com/docs/connectors/building/authentication].
**Why it happens:** Reuse-Detection und Nebenläufigkeit vertragen sich nur mit einer
atomaren Zustandsänderung.
**How to avoid:** Die Einlösung ist ein einziges `UPDATE ... WHERE token_hash = ? AND
state = 'active'` in einer Transaktion (SQLite: `BEGIN IMMEDIATE`); wer null Zeilen ändert,
hat verloren und bekommt `invalid_grant`. Zusätzlich ein kurzes Gnadenfenster (ca. 10 s):
wird derselbe Token innerhalb des Fensters ein zweites Mal eingelöst, wird **derselbe**
neue Token nochmals herausgegeben statt die Familie zu töten. Das ist gängige Praxis gegen
Netzwerk-Wiederholungen; die Reuse-Detection bleibt danach scharf. Wenn das Gnadenfenster
nicht gewollt ist (konservativere Auslegung, Owner-Vorgabe), muss der D-40-Testfall
"Replay tötet die Familie" das Fenster respektieren, sonst wird er flaky.
**Warning signs:** Nutzer verlieren sporadisch die Verbindung und müssen neu autorisieren.

### Pitfall 11: `APP_SECRET` ist kein stabiler Schlüssel

**What goes wrong:** Als Ableitungsquelle für die Verschlüsselung wirkt `APP_SECRET`
naheliegend (steht so als Kandidat in D-34). Es wird aber bei jeder Registrierung neu
erzeugt, wenn die Registrierung keins mitgibt; `scripts/bootstrap_exapp.sh` pinnt es nur
deshalb, weil Phase 2 genau diese Falle schon getroffen hat (Pitfall 11 dort). Nach einem
App-Update mit Neuregistrierung wären alle gespeicherten App-Passwörter unentschlüsselbar.
**Why it happens:** `APP_SECRET` ist ein Transport-Secret, kein Datenschlüssel.
**How to avoid:** Einen eigenen 32-Byte-Schlüssel beim ersten Start erzeugen und über
`POST /ocs/v2.php/apps/app_api/api/v1/ex-app/config` mit `sensitive=1` in Nextcloud
ablegen, beim Start einmal lesen und im Speicher halten. Fehlt der Schlüssel und lässt er
sich nicht anlegen: Start mit klarer Meldung abbrechen (fail-closed), nicht mit einem
Zufallsschlüssel weiterlaufen.
**Warning signs:** Nach `occ app_api:app:unregister` plus Neuregistrierung sind alle
Verbindungen tot, ohne dass jemand etwas widerrufen hat.

### Pitfall 12: Das ExApp-Volume ist da, aber nicht selbstverständlich

**What goes wrong:** Der Store braucht einen Pfad, der einen Container-Neustart überlebt.
AppAPI legt `nc_app_<appid>_data` an und übergibt den Mountpunkt als
`APP_PERSISTENT_STORAGE`. Die Variable ist in `config.py` deklariert, wird aber bisher von
nichts gelesen (steht deshalb in `vulture_whitelist.py`). Das Dockerfile legt
`/nc_app_mcp_connector_data` mit `0700` und uid 10001 an, damit das frische Volume die
richtigen Rechte erbt.
**Why it happens:** Phase 2 hat die Variable vorbereitet, aber nicht genutzt.
**How to avoid:** Den Store-Pfad aus `APP_PERSISTENT_STORAGE` ableiten, mit einer klaren
Fehlermeldung abbrechen, wenn die Variable fehlt oder das Verzeichnis nicht schreibbar ist,
und den Eintrag aus `vulture_whitelist.py` entfernen, sobald es einen echten Leser gibt.
Für den `--manual`-Entwicklungsmodus einen Fallback-Pfad im Repo (git-ignoriert) vorsehen.
**Warning signs:** Nach `docker restart` müssen sich alle Clients neu verbinden.

### Pitfall 13: Claude-Timeouts sind knapp

**What goes wrong:** Claude wartet 10 s auf Discovery-, Registrierungs- und
Token-Antworten und 30 s auf Refresh-Antworten
[CITED: claude.com/docs/connectors/building/authentication]. Unser `/token` löst im
Erfolgsfall keine Nextcloud-Calls aus, wohl aber `/authorize` (Login-Flow-Init) und der
Widerruf (App-Passwort löschen).
**Why it happens:** Ein Nextcloud-Roundtrip über den PHP-Stack kann unter Last mehrere
Sekunden dauern.
**How to avoid:** Kein Nextcloud-Call im `/token`-Pfad. Der Login-Flow-Init passiert in
`/authorize` (Browser, großzügigeres Timeout), das Löschen des App-Passworts im
Revoke-Pfad wird mit kurzem Timeout gefahren und ist idempotent: schlägt es fehl, gilt der
Token trotzdem als widerrufen und der Löschversuch wird als Aufräumaufgabe vermerkt.
**Warning signs:** Sporadische "Couldn't reach the MCP server"-Meldungen bei ansonsten
funktionierender Verbindung.

### Pitfall 14: Reverse-Proxy-Pfadnormalisierung und die enge Well-known-Route

**What goes wrong:** D-38 verlangt, die Route `^/\.well-known/` eng zu fassen. Zu eng
gefasst (z.B. mit `$`-Anker an der falschen Stelle) verschwindet die Discovery; zu weit
gefasst bleibt AR-02-06 offen. Zusätzlich normalisieren Proxys Pfade unterschiedlich
(`//.well-known/...`, `/./well-known/...`, prozentkodierte Punkte), und HaRP matcht mit
`re.match` gegen den gestrippten Pfad, also ohne Anker am Ende.
**Why it happens:** `re.match` ankert nur am Anfang; ein Muster ohne `$` matcht auch
Präfixe.
**How to avoid:** Je Dokument eine eigene Route mit vollständigem Anker, zum Beispiel
`^/\.well-known/oauth-protected-resource/mcp$`,
`^/\.well-known/oauth-authorization-server$`, `^/\.well-known/openid-configuration$`. Dazu
ein Test, der die verbotenen Nachbarn prüft (`/.well-known/oauth-protected-resource/mcpx`,
`/.well-known/`, Doppel-Slash-Varianten) und ein Test, der die Manifest-Routen gegen die
tatsächlich registrierten Starlette-Pfade abgleicht (Wächter-Test-Kultur aus
`tests/unit/test_exapp_env_setup.py`).
**Warning signs:** Der Spike-Probe-Pfad ist noch erreichbar, obwohl das Modul entfernt
wurde.

### Pitfall 15: Claude Code und andere Loopback-Clients passen nicht ins exakte Matching

**What goes wrong:** D-35 verlangt exaktes Redirect-URI-Matching; das SDK macht genau das.
Claude Code nutzt aber einen Loopback-Redirect mit wechselndem Port und identifiziert sich
per Client-ID-Metadata-Document (CIMD), nicht per DCR
[CITED: claude.com/docs/connectors/building/authentication]. CIMD ist in v1 nicht geplant.
**Why it happens:** Die MCP-Spec (draft) stuft DCR als "deprecated, retained for backwards
compatibility" ein und bevorzugt CIMD; die Ökosystem-Bewegung geht dorthin.
**How to avoid:** Für Phase 3 bewusst außen vor lassen: SC 1 und SC 2 nennen den
Claude.ai- und den ChatGPT-Connector, beide fahren DCR bzw. CIMD über die gehosteten
Oberflächen. Claude Code bleibt auf dem AUTH-01-Pfad (App-Passwort). Als Backlog-Eintrag
festhalten, damit es nicht als Bug wiederkehrt.
**Warning signs:** Ein Tester probiert Claude Code gegen Staging und meldet
"invalid_redirect_uri".

## Code Examples

### 1. Metadaten an den erreichbaren Pfaden ausliefern

```python
# Source: eigene Ableitung aus .venv/.../mcp/server/auth/routes.py (build_metadata,
# create_protected_resource_routes) plus Messmatrix aus docs/spike-discovery.md
from mcp.server.auth.routes import build_metadata
from mcp.shared.auth import ProtectedResourceMetadata

def metadata_routes(public_base: str) -> list[Route]:
    """public_base ist die externe URL der ExApp, z.B.
    https://cloud.example.com/exapps/mcp_connector"""
    issuer = AnyHttpUrl(public_base)
    resource = AnyHttpUrl(f"{public_base}/mcp")

    as_doc = build_metadata(issuer, None, registration_options, revocation_options)
    # Ergaenzungen, die das SDK nicht setzt:
    as_doc.authorization_response_iss_parameter_supported = True   # RFC 9207
    as_doc.scopes_supported = ["nextcloud:read", "nextcloud:write"]

    prm_doc = ProtectedResourceMetadata(
        resource=resource,
        authorization_servers=[issuer],      # Pflichtfeld, min_length=1
        scopes_supported=["nextcloud:read"], # bewusst minimal, ohne offline_access
        resource_name="Nextcloud MCP Connector",
    )

    return [
        # unter dem gestrippten Praefix erreichbar, Pointer-Ziel des 401
        Route("/.well-known/oauth-protected-resource/mcp", _json(prm_doc), methods=["GET"]),
        # Weg 3 der Spec-Discovery, ohne Zutun des Admins erreichbar
        Route("/.well-known/openid-configuration", _json(as_doc), methods=["GET"]),
        # Ziel der Reverse-Proxy-Regel (Weg 1)
        Route("/.well-known/oauth-authorization-server", _json(as_doc), methods=["GET"]),
    ]
```

### 2. Der 401, den der Discovery-Flow braucht

```python
# Source: Muster aus .venv/.../mcp/server/auth/middleware/bearer_auth.py
# (RequireAuthMiddleware._send_auth_error), ergaenzt um no-store und scope.
WWW_AUTH = (
    'Bearer error="invalid_token", '
    'error_description="Authentication required", '
    f'scope="nextcloud:read", '
    f'resource_metadata="{public_base}/.well-known/oauth-protected-resource/mcp"'
)
# Cache-Control: no-store ist Pflicht: der PHP-Proxy cacht JSON sonst 3600 s.
```

### 3. Login Flow v2, die drei Aufrufe

```python
# Source: nextcloud/server core/Controller/ClientFlowLoginV2Controller.php und
# core/Controller/AppPasswordController.php (master, gelesen 2026-08-15)

# 1. Flow starten. Der User-Agent wird zum Client-Namen im Grant-Dialog.
r = await client.post(
    f"{base_url}/index.php/login/v2",
    headers={"User-Agent": safe_agent},        # gesaeubert, siehe Pitfall 8
)
data = r.json()      # {"poll": {"token": ..., "endpoint": ...}, "login": "https://.../login/v2/flow/<t>"}

# 2. Genau ein Poll je Status-Anfrage der Consent-Seite. 404 = noch nicht fertig
#    ODER unbekannt/abgelaufen; 200 kommt genau einmal.
r = await client.post(f"{base_url}/login/v2/poll", data={"token": poll_token})
if r.status_code == 200:
    creds = r.json()   # {"server": ..., "loginName": ..., "appPassword": ...}

# 3. Widerruf: mit genau diesem App-Passwort authentifizieren, dann loeschen.
#    Loescht das Token, mit dem der Request authentifiziert wurde.
r = await client.delete(
    f"{base_url}/ocs/v2.php/core/apppassword",
    headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    auth=httpx.BasicAuth(login_name, app_password),
)
# 200 = geloescht, 401 = schon weg (Nutzer war schneller) -> beides ist Erfolg.
# Kein Retry (D-37).
```

### 4. Rotation mit Reuse-Detection, atomar

```sql
-- Source: eigene Ableitung; SQLite-Muster fuer atomare Einloesung
BEGIN IMMEDIATE;
UPDATE refresh_tokens
   SET state = 'used', used_at = :now, successor = :new_hash
 WHERE token_hash = :hash AND state = 'active' AND expires_at > :now;
-- changes() = 0 bedeutet: unbekannt, abgelaufen, oder bereits benutzt.
-- Bereits benutzt und ausserhalb des Gnadenfensters -> ganze Familie widerrufen:
UPDATE refresh_tokens SET state = 'revoked' WHERE family_id = :family;
UPDATE access_tokens  SET state = 'revoked' WHERE family_id = :family;
COMMIT;
```

### 5. Der Enforcement-Punkt für AUTH-07

```python
# Source: eigene Ableitung aus .venv/.../mcp/server/auth/handlers/{authorize,token}.py
async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
    row = await self._store.load_client(client_id)
    if row is None:
        return None
    if not row.allowed:                       # Admin-Sperre (Phase-4-UI setzt das Flag)
        return None
    if self._policy.allowlist_only and client_id not in self._policy.allowed_ids:
        return None
    if row.last_used_at is None and row.registered_at < self._now - UNUSED_TTL:
        await self._store.delete_client(client_id)   # unbenutzte Registrierungen verfallen
        return None
    return row.to_client_info()

async def register_client(self, client_info: OAuthClientInformationFull) -> None:
    if not self._policy.dcr_enabled:
        # Das SDK haengt /register nur ein, wenn enabled=True. Diese Pruefung ist die
        # zweite Haelfte: sie benennt den Grund, wenn die Route doch erreichbar ist.
        raise RegistrationError("invalid_client_metadata",
                                "dynamic client registration is disabled on this instance")
    for uri in client_info.redirect_uris or []:
        if not _is_https_or_loopback(uri):    # das SDK prueft das NICHT
            raise RegistrationError("invalid_redirect_uri",
                                    "redirect_uris must use https, except loopback")
    await self._store.save_client(client_info, allowed=not self._policy.allowlist_only)
```

## Was das SDK mitbringt und was fehlt

Alle Aussagen aus dem Quellcode der installierten Version **mcp 2.0.0** gelesen
[VERIFIED: `.venv/Lib/site-packages/mcp/server/auth/`].

| Baustein | Im SDK enthalten | Bemerkung |
|----------|------------------|-----------|
| `/authorize` (GET und POST) | ja, `handlers/authorize.py` | `code_challenge` ist Pflichtfeld, `code_challenge_method` ist `Literal["S256"]` mit Default `S256`; `plain` fällt als Validierungsfehler durch (D-40-Fall "PKCE-Downgrade") |
| `redirect_uri`-Prüfung | ja, `OAuthClientInformationFull.validate_redirect_uri` | Exakter Listenvergleich; Weglassen nur erlaubt, wenn genau eine URI registriert ist |
| Fehlerformat an `/authorize` | ja | Redirect mit `error`/`state`, wenn Client und Redirect valide sind, sonst JSON 400; beides mit `Cache-Control: no-store` |
| `/token` mit `authorization_code` | ja, `handlers/token.py` | Prüft Code-Existenz, Client-Zugehörigkeit, Ablauf, `redirect_uri`-Gleichheit, PKCE-Verifier |
| `/token` mit `refresh_token` | ja | Prüft Existenz, Client, Ablauf, Scope-Teilmenge. **Rotation und Reuse-Detection sind Provider-Sache** |
| Client-Authentifizierung | ja, `middleware/client_auth.py` | `client_secret_basic`, `client_secret_post`, `none`; `hmac.compare_digest`; Ablauf des Secrets |
| `/register` (RFC 7591) | ja, `handlers/register.py` | Verlangt `authorization_code` in `grant_types` und `code` in `response_types`; lehnt `private_key_jwt` und den jwt-bearer-Grant ab; vergibt `client_id` (uuid4) und bei Nicht-`none`-Methode ein 32-Byte-Hex-Secret |
| `/revoke` (RFC 7009) | ja, `handlers/revoke.py` | Sucht Access- und Refresh-Token, prüft Client-Zugehörigkeit, antwortet immer 200 |
| AS-Metadata (RFC 8414) | ja, `build_metadata` | `code_challenge_methods_supported: ["S256"]`, `token_endpoint_auth_methods_supported: ["client_secret_post", "client_secret_basic"]` |
| PRM (RFC 9728) | ja, `create_protected_resource_routes` | Route liegt am kanonischen Pfad, siehe Pitfall 1 |
| Bearer-Prüfung und 401 | ja, `middleware/bearer_auth.py` | `BearerAuthBackend` + `RequireAuthMiddleware`, 401 mit `resource_metadata`, 403 bei fehlendem Scope |
| Ablaufprüfung des Access-Tokens | ja, im `BearerAuthBackend` | zusätzlich zur eigenen Prüfung im Verifier |
| **Audience/`resource`-Prüfung** | **nein** | `resource` wird nur durchgereicht; Prüfung mit `check_resource_allowed` ist Provider- und Verifier-Aufgabe |
| **https-Zwang für `redirect_uris`** | **nein** | `/register` akzeptiert jede `AnyUrl`; D-35 verlangt https plus Loopback-Ausnahme |
| **Refresh-Rotation und Reuse-Detection** | **nein** | Docstring sagt nur "SHOULD rotate"; Umsetzung ist Provider-Sache |
| **Client-Allowlist, DCR-Schalter zur Laufzeit** | teilweise | `ClientRegistrationOptions.enabled` entscheidet beim App-Bau, ob `/register` existiert; ein Laufzeit-Schalter und die Allowlist gehören in `get_client` |
| **Persistenz** | **nein** | Alles kommt aus dem Provider |
| **`iss` in der Authorization-Response (RFC 9207)** | **nein** | Wir bauen die Redirect-URL selbst (Provider gibt sie zurück) und können `iss` anhängen; das Metadatenfeld `authorization_response_iss_parameter_supported` existiert im Modell |
| **Consent-Anzeige** | **nein** | Bewusst offen gelassen; der Provider entscheidet, wohin `/authorize` weiterleitet |
| **`Cache-Control` auf `/register`** | **nein** | Siehe Pitfall 4 |

## Discovery-Topologie: welcher Pfad wo landet

Bei einer ExApp unter `https://cloud.example.com/exapps/mcp_connector` und
`resource = https://cloud.example.com/exapps/mcp_connector/mcp`:

| URL, die der Client baut | Wer antwortet | Ergebnis ohne Zusatzkonfiguration |
|--------------------------|---------------|-----------------------------------|
| `WWW-Authenticate: resource_metadata=<voll qualifiziert>` | ExApp über HaRP | **200** (im Spike gemessen, beide Proxy-Wege) |
| `/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp` | Nextcloud | 404 (Spike-Messung) |
| `/.well-known/oauth-protected-resource` | Nextcloud `WellKnownController` | 404 JSON, Header `X-NEXTCLOUD-WELL-KNOWN: 1` |
| `/.well-known/oauth-authorization-server/exapps/mcp_connector` | Nextcloud | 404 (zwei Pfadsegmente, Route matcht nur eines) |
| `/.well-known/openid-configuration/exapps/mcp_connector` | Nextcloud | 404 (dito) |
| `/exapps/mcp_connector/.well-known/openid-configuration` | **ExApp** | **200, wenn wir das Dokument dort ausliefern** |
| `/exapps/mcp_connector/.well-known/oauth-authorization-server` | **ExApp** | 200, aber kein Client fragt dort von sich aus (nur als Rewrite-Ziel) |

Der MCP-Python-SDK-Client probiert alle drei AS-Varianten in dieser Reihenfolge
[VERIFIED: `mcp/client/auth/utils.py`, `build_oauth_authorization_server_metadata_discovery_urls`],
er findet also den OIDC-Pfad-Anhängungs-Weg von selbst. Ob Claude.ai und ChatGPT das
ebenfalls tun, ist **nicht verifiziert** (Claude-Doku formuliert nur "RFC 8414 oder OpenID
Connect Discovery 1.0 an seinen `/.well-known/`-Pfaden"). Deshalb: OIDC-Weg ausliefern
**und** Proxy-Regeln dokumentieren, Staging mit Regeln fahren, und im E2E-Plan messen,
welchen Weg die beiden Clients tatsächlich gehen (Access-Log auswerten).

## Client-Verhalten: Claude.ai und ChatGPT

| Eigenschaft | Claude (Claude.ai, Desktop, Mobile, Cowork) | ChatGPT-Connector |
|-------------|---------------------------------------------|-------------------|
| Registrierung | `oauth_dcr` out of the box; `oauth_cimd`, wenn die AS-Metadaten `client_id_metadata_document_supported: true` **und** `none` in `token_endpoint_auth_methods_supported` melden [CITED: claude.com/docs/connectors/building/authentication] | DCR "remains supported when configured"; CIMD wird empfohlen [CITED: developers.openai.com/api/docs/mcp] |
| Redirect-URI | `https://claude.ai/api/mcp/auth_callback` [CITED: claude.com/docs/connectors/building/authentication] | `https://chatgpt.com/connector_platform_oauth_redirect` [ASSUMED: Community-Quellen, nicht Hersteller-Doku] |
| PKCE | immer `S256`, unabhängig vom Registrierungsweg | S256 (MCP-Spec-Pflicht) [ASSUMED] |
| Client-Typ | public (DCR und CIMD registrieren Claude als public client) | public bei CIMD (`none`) oder `private_key_jwt` [CITED] |
| Scope-Auswahl | `scope` aus dem `WWW-Authenticate` gewinnt, sonst `scopes_supported` aus dem PRM; `offline_access` wird angehängt, wenn die AS-Metadaten es listen | analog MCP-Spec [ASSUMED] |
| Refresh | reaktiv auf 401, proaktiv bis 5 Minuten vor Ablauf; verlangt `invalid_grant` als Fehlercode; erwartet Rotation für public clients | analog [ASSUMED] |
| Content-Type | `/token` muss `application/x-www-form-urlencoded` annehmen, `/register` ist `application/json` | dito |
| Timeouts | 10 s für Discovery, Registrierung, Token; 30 s für Refresh | unbekannt [ASSUMED: ähnlich] |
| Egress | `160.79.104.0/21` | unbekannt |
| PRM-Fundort | `resource_metadata` aus dem 401 zuerst, sonst Origin-Probing `/.well-known/oauth-protected-resource/<pfad>` dann `/.well-known/oauth-protected-resource`; `resource` im PRM muss exakt der vom Nutzer eingetragenen URL entsprechen; bei mehreren `authorization_servers` wird **nur der erste** genutzt | analog [ASSUMED] |

Konsequenzen für die Pläne:

- Genau **ein** Eintrag in `authorization_servers`.
- Der `resource`-Wert im PRM muss exakt die URL sein, die der Nutzer einträgt, inklusive
  `/mcp`. Ein Trailing-Slash-Unterschied bricht die Verbindung.
- `scopes_supported` im PRM klein halten und `offline_access` dort **nicht** listen
  (MCP-Spec: "MCP servers SHOULD NOT include `offline_access` in WWW-Authenticate scope or
  PRM `scopes_supported`"). In den AS-Metadaten darf `offline_access` stehen, wenn wir
  Refresh-Tokens wollen.
- `token_endpoint_auth_methods_supported` sollte `none` enthalten, weil beide Clients als
  public client kommen; das SDK listet per Default nur `client_secret_post` und
  `client_secret_basic`. Das ist ein konkreter Patch am Metadaten-Dokument.
- CIMD (`client_id` als HTTPS-URL) ist in v1 nicht implementiert. Solange
  `client_id_metadata_document_supported` fehlt, fällt Claude auf DCR zurück; das ist
  gewollt. Für v2 vormerken, weil die Spec DCR als deprecated markiert.

## Client-Registry und Allowlist (AUTH-07)

Drei Schalter, alle per Env bzw. ExApp-Config lesbar (Admin-UI folgt in Phase 4):

| Schalter | Bedeutung | Default |
|----------|-----------|---------|
| `NC_MCP_OAUTH_DCR` | Dynamic Client Registration global an/aus | an (SC 1 und 2 verlangen plug-and-play) |
| `NC_MCP_OAUTH_ALLOWLIST_ONLY` | nur explizit freigegebene Clients dürfen autorisieren | aus |
| `NC_MCP_OAUTH_ALLOWED_CLIENTS` | Liste erlaubter Client-IDs oder Redirect-URIs | leer |

Enforcement an vier Stellen: `register_client` (Registrierung ablehnen), `get_client`
(gilt für `/authorize`, `/token` und `/revoke`, weil alle drei darüber laufen),
`exchange_authorization_code`/`exchange_refresh_token` (Sperre mitten im Flow) und
`verify_token` (bestehende Access-Tokens sofort ungültig).

Verfall unbenutzter Registrierungen: `registered_at` und `last_used_at` in der Registry
führen; ein Client ohne erfolgreiche Token-Ausgabe verfällt nach einer kurzen Frist
(Vorschlag 24 h), ein benutzter Client nach längerer Inaktivität (Vorschlag 90 Tage, dann
mit allen Tokens). Aufräumen läuft opportunistisch beim Zugriff und zusätzlich beim Start,
kein Cron.

## Token-Store: Schema-Vorschlag

Eine SQLite-Datei unter `${APP_PERSISTENT_STORAGE}/oauth.sqlite3`, `PRAGMA journal_mode =
WAL`, `PRAGMA foreign_keys = ON`, Zugriff über `asyncio.to_thread` mit einer Verbindung pro
Thread. Alle Token stehen nur als `sha256`-Hex in der DB.

```sql
CREATE TABLE clients (
  client_id TEXT PRIMARY KEY,
  client_secret_hash TEXT,             -- NULL bei public clients
  metadata_json TEXT NOT NULL,         -- OAuthClientInformationFull, ohne Secret
  allowed INTEGER NOT NULL DEFAULT 1,  -- AUTH-07
  registered_at INTEGER NOT NULL,
  last_used_at INTEGER
);

CREATE TABLE flows (                   -- Pending Authorizations (Login Flow v2 laeuft)
  flow_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  redirect_uri TEXT NOT NULL,
  redirect_uri_explicit INTEGER NOT NULL,
  code_challenge TEXT NOT NULL,
  state TEXT,
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  poll_token_enc BLOB NOT NULL,        -- verschluesselt: erlaubt das Abholen des App-Passworts
  expires_at INTEGER NOT NULL          -- 20 Minuten, wie Nextcloud
);

CREATE TABLE authorizations (          -- eine Verbindung = ein App-Passwort
  auth_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  nc_user TEXT NOT NULL,               -- loginName aus dem Login Flow
  app_password_enc BLOB NOT NULL,      -- AESGCM, aad = auth_id
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  revoked_at INTEGER
);

CREATE TABLE auth_codes (
  code_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  redirect_uri TEXT NOT NULL,
  code_challenge TEXT NOT NULL,
  resource TEXT NOT NULL,
  expires_at INTEGER NOT NULL,         -- kurz, Groessenordnung 60 s
  used_at INTEGER
);

CREATE TABLE refresh_tokens (
  token_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  family_id TEXT NOT NULL,
  state TEXT NOT NULL,                 -- active | used | revoked
  successor TEXT,
  issued_at INTEGER NOT NULL,
  used_at INTEGER,
  expires_at INTEGER NOT NULL
);
CREATE INDEX refresh_family ON refresh_tokens(family_id);

CREATE TABLE access_tokens (
  token_hash TEXT PRIMARY KEY,
  auth_id TEXT NOT NULL REFERENCES authorizations(auth_id) ON DELETE CASCADE,
  family_id TEXT NOT NULL,
  scopes TEXT NOT NULL,
  resource TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  revoked_at INTEGER
);
CREATE INDEX access_family ON access_tokens(family_id);
```

Lebensdauern (Claude's Discretion, Vorschlag): Authorization-Code 60 s, Access-Token
3600 s, Refresh-Token 30 Tage mit Rotation bei jeder Nutzung, Flow 1200 s (Nextcloud-Takt),
Validierungs-Cache 5 s mit direkter Invalidierung beim Widerruf im selben Prozess.

Widerruf (SC 4) in dieser Reihenfolge: Store-Zeilen der Familie auf `revoked` setzen ->
Prozess-Cache leeren -> App-Passwort bei Nextcloud löschen (idempotent, ein Versuch, kein
Retry). Schritt 3 darf Schritt 1 und 2 nicht blockieren.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "Das SDK stellt keinen Authorization Server" (STACK.md, Recherche vor Phase 1) | mcp 2.0.0 liefert `create_auth_routes` mit allen fünf Endpunkten plus Provider-Protokoll | spätestens mit 2.0.0 (2026-07-28) | Der Eigenbau-Umfang schrumpft von "vier Endpoints" auf "ein Provider plus vier Kontrollen" |
| Selbst signierte JWTs mit PyJWT (STACK.md) | Opake Tokens im eigenen Store (D-34) | Owner-Entscheid 15.08.2026 | Sofort-Widerruf ohne Denylist; PyJWT bleibt ungenutzte transitive Dependency |
| DCR als Standardweg für unbekannte Clients | MCP-Spec (draft) markiert DCR als deprecated, bevorzugt Client ID Metadata Documents (CIMD) | Spec-Draft nach 2026-07-28 | Für v1 kein Handlungsbedarf (beide Zielclients können DCR), aber CIMD gehört auf die v2-Liste |
| Login Flow v1 (`/index.php/login/flow`) | Login Flow v2 mit Poll-Token | seit Nextcloud 16 | v2 ist der einzige Weg, den wir nutzen |
| Docker Socket Proxy als Deploy-Daemon | HaRP ab Nextcloud 32, DSP-Entfernung für 35 geplant | Phase-2-Entscheidung | Alle Routing-Befunde dieser Recherche gelten für HaRP; der PHP-Proxy-Pfad bleibt Zweitweg |

**Deprecated/outdated:**

- `auth_server_provider=` am `MCPServer`-Konstruktor: funktioniert, ist aber laut
  SDK-Kommentar der Rückwärtskompatibilitätspfad (`ProviderTokenVerifier` ist explizit
  "provided for backwards compatibility").
- `src/mcp_connector/exapp/discovery.py`: Spike-Artefakt, wird **ersetzt**, nicht
  erweitert; die Probe-Route `/.well-known/mcp-discovery-probe` verschwindet mit ihr
  (offener Punkt aus `docs/spike-discovery.md`).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| mcp (SDK, Server- und Client-Hälfte) | AS-Routen, Verifier, E2E-Testclient | ja | 2.0.0 (uv.lock, .venv) | keiner nötig |
| cryptography | AESGCM, HKDF | ja | 50.0.0 (transitiv im Lock) | keiner nötig |
| sqlite3 | Token-Store | ja | Python 3.13 stdlib | keiner nötig |
| Wegwerf-Nextcloud mit HaRP (`compose.exapp.yml`) | Integrationstests, Login-Flow-Messung | ja, Topologie vorhanden | NC 34.0.2, AppAPI 34.0.0 | keiner |
| Öffentliche Staging-Instanz mit Domain und TLS | SC 1 und SC 2 (Claude.ai, ChatGPT) | **nein** | - | **kein Fallback**: OWNER-ACTION aus D-39; der E2E-Plan blockiert bis dahin, der Rest der Phase nicht |
| Claude.ai-Konto mit Connector-Berechtigung | SC 1 | unbekannt | - | Ohne Konto kein SC-1-Beweis; Owner-Checkpoint |
| ChatGPT-Konto mit Connector-Berechtigung (Plus/Pro/Business) | SC 2 | unbekannt | - | dito |
| slopcheck | Package Legitimacy Gate | nein (kein `pip` auf dem PATH) | - | Manuelle PyPI-Verifikation, siehe Audit-Abschnitt |
| Docker unter WSL2 | ExApp-Topologie | ja (Phase 2 lief damit) | - | keiner |

**Missing dependencies with no fallback:**

- Öffentlich erreichbare Staging-Instanz (Domain, TLS, Reverse Proxy mit den beiden
  Well-known-Regeln) sowie Konten bei Claude.ai und ChatGPT. Alle drei sind Owner-Actions
  und gehören in einen eigenen, hinten liegenden Plan mit `checkpoint:human-verify`.

**Missing dependencies with fallback:**

- slopcheck: manuelle Verifikation über die PyPI-JSON-API (durchgeführt).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | Nextcloud Login Flow v2 (inkl. 2FA) als einzige Nutzer-Authentifizierung; kein eigener Passwort-Pfad; `secrets.token_urlsafe(32)` für alle Geheimnisse |
| V3 Session Management | ja | Opake Tokens mit kurzer Lebensdauer, Refresh-Rotation mit Reuse-Detection, serverseitiger Sofort-Widerruf; kein Session-State im Prozess |
| V4 Access Control | ja | `access_level` im Manifest plus eigene Transportgrenze; Client-Allowlist in `get_client`; Audience-Bindung je Token; Nextcloud entscheidet über jede Datenoperation (AUTH-05) |
| V5 Input Validation | ja | pydantic-Modelle des SDK für alle OAuth-Parameter; eigene Säuberung des `client_name` vor dem `User-Agent` (Header-Injection); Regex-Anker in den Manifest-Routen |
| V6 Cryptography | ja | `cryptography` AESGCM mit AAD, HKDF für Teilschlüssel, `hashlib.sha256` für Token-Hashes, `secrets.compare_digest`/`hmac.compare_digest` für Vergleiche; keine Eigenbau-Krypto |
| V7 Error Handling and Logging | ja | RFC-Fehlercodes ohne interne Details; niemals Token, App-Passwort oder `APP_SECRET` in Logs oder Exceptions (Muster aus Phase 1/2) |
| V8 Data Protection | ja | App-Passwörter nur verschlüsselt at rest, Schlüssel getrennt in Nextclouds ExApp-Config; `Cache-Control: no-store` auf allen Auth-Antworten |
| V13 API and Web Service | ja | Nur `Authorization`-Header, kein Token in der Query; CORS nur dort, wo das SDK es setzt |

### Known Threat Patterns for MCP-OAuth-Bridge auf Nextcloud

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Authorization-Code-Interception | Spoofing | PKCE S256 erzwungen (SDK), Code einmalig und kurzlebig |
| PKCE-Downgrade (`plain` oder fehlend) | Tampering | `Literal["S256"]` im Request-Modell, Pflichtfeld `code_challenge`; D-40-Test |
| Offene Weiterleitung über `redirect_uri` | Tampering | Exaktes Matching (SDK), https-Zwang plus Loopback-Ausnahme (Provider), Redirect-Host auf der Consent-Seite anzeigen |
| Confused Deputy / Token an falschem Server einlösen | Elevation of Privilege | RFC-8707-`resource` verpflichtend, Prüfung bei Ausgabe und bei Verifikation |
| Mix-up zwischen Authorization Servern | Spoofing | `iss` in der Authorization-Response (RFC 9207) und `authorization_response_iss_parameter_supported: true` in den Metadaten |
| Refresh-Token-Diebstahl | Spoofing | Rotation plus Reuse-Detection: Wiederverwendung tötet die Familie |
| Token-Leak über Logs oder Cache | Information Disclosure | Nur Hashes in der DB, `no-store` überall, kein Token in Log oder Exception |
| DB-Diebstahl aus dem Volume | Information Disclosure | App-Passwörter AESGCM-verschlüsselt, Schlüssel liegt in Nextcloud, nicht im Volume |
| Client-Registry-Flut über DCR | Denial of Service | Verfall unbenutzter Registrierungen, DCR abschaltbar, Allowlist-Modus |
| Brute Force gegen Nextcloud über unsere Auth-Pfade | Denial of Service | Keine Auth-Retries, keine Nextcloud-Roundtrips im Token-Pfad, unbekannter Bearer erzeugt keinen NC-Throttler-Eintrag (verifiziert) |
| Header-Injection über `client_name` | Tampering | Säuberung auf druckbares ASCII, Längenbegrenzung, festes Präfix |
| Consent-Seite als Phishing-Fläche | Spoofing | Client-Name als nicht vertrauenswürdig kennzeichnen, Redirect-Host prominent zeigen, keine Nutzereingaben entgegennehmen |
| Anonymer Zugriff nach PUBLIC-Umstellung | Elevation of Privilege | Manifest-Änderung und Bearer-Prüfung im selben Task; Wächter-Test |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ChatGPT nutzt `https://chatgpt.com/connector_platform_oauth_redirect` als Redirect-URI | Client-Verhalten | SC 2 scheitert an `invalid_redirect_uri`; der echte Wert ist im E2E-Lauf aus dem DCR-Request ablesbar, dann korrigieren |
| A2 | Claude.ai und ChatGPT probieren den dritten Discovery-Weg (`<issuer>/.well-known/openid-configuration`) | Discovery-Topologie | Ohne Reverse-Proxy-Regeln findet der Client den AS nicht; deshalb sind die Regeln Pflichtinhalt der Staging-Doku, nicht optional |
| A3 | ChatGPTs Timeouts liegen in derselben Größenordnung wie Claudes 10 s / 30 s | Client-Verhalten | Zu langsame Endpunkte brechen SC 2; Messung im E2E-Plan |
| A4 | Ein Gnadenfenster von etwa 10 s bei der Refresh-Rotation ist mit der Owner-Vorgabe vereinbar | Pitfall 10 | Ohne Fenster kann ein Netzwerk-Retry eine Familie töten (Nutzer verliert die Verbindung); mit Fenster ist die Reuse-Detection minimal weicher. Owner-Entscheid im discuss-Schritt einholen |
| A5 | `overwrite.cli.url` ist auf Zielinstanzen korrekt gesetzt, sodass die öffentliche Basis-URL ableitbar ist | Don't Hand-Roll | Falsche `resource`-Werte im PRM brechen die Verbindung; deshalb `NC_MCP_PUBLIC_URL` als Override behalten und beim Start loggen |
| A6 | Der PHP-Proxy-Pfad (`/apps/app_api/proxy/...`) leitet auch POST-Requests an die AS-Routen weiter | Architektur | Nur der Zweitweg wäre betroffen; HaRP bleibt der Primärweg. Im Integrationstest mitmessen |
| A7 | Vorgeschlagene Lebensdauern (Code 60 s, Access 1 h, Refresh 30 Tage) passen zum Nutzungsprofil | Token-Store | Zu kurz erzeugt unnötige Refreshes (jeder kostet einen NC-Roundtrip über HaRP), zu lang verlängert das Zeitfenster eines gestohlenen Tokens |
| A8 | `cryptography` als direkte Dependency ist für den Owner in Ordnung (bereits transitiv im Lock) | Standard Stack | Ohne Freigabe müsste der Import auf der transitiven Dependency stehen bleiben, was die Dependency-Policy des Projekts eigentlich verbietet |

## Open Questions

1. **(RESOLVED: Messung in 03-01/03-09) Findet Claude.ai den AS ohne Reverse-Proxy-Regeln?**
   - Was wir wissen: Der MCP-SDK-Client probiert alle drei Wege; Claude verlangt laut Doku
     nur "RFC 8414 oder OIDC Discovery an den `/.well-known/`-Pfaden".
   - Was unklar ist: Ob Claudes Implementierung die OIDC-Pfad-Anhängung enthält.
   - Empfehlung: Staging mit Regeln aufsetzen (dann ist SC 1 sicher), im selben Lauf ohne
     Regeln gegenmessen und das Ergebnis in `docs/` festhalten. Das ist die Aussage, die
     später jeder Selfhoster braucht.

2. **(RESOLVED: D-34, ein App-Passwort je Authorization) Ein App-Passwort je Authorization oder Impersonation?**
   - Was wir wissen: D-34 legt das App-Passwort fest. Technisch ginge auch reine
     AppAPI-Impersonation mit der aus dem Token bekannten Nutzer-ID, ganz ohne
     App-Passwort.
   - Was unklar ist: nichts Technisches; es ist eine bewusste Entscheidung. Das
     App-Passwort ist der überprüfbare Nachweis, dass der Nutzer zugestimmt hat, es taucht
     für ihn in "Geräte und Sitzungen" auf und ist dort einzeln löschbar.
   - Empfehlung: Bei D-34 bleiben. Zusätzlich prüfen, ob die DAV-Provider-Matrix aus
     `docs/spike-dav.md` (Fall A) mit Basic-App-Passwort dieselben Ergebnisse liefert wie
     mit Impersonation; falls nicht, ist das ein Plan-Task.

3. **(RESOLVED: D-36, /connect-Strecke; Admin-UI folgt Phase 4) Wie erfährt der Nutzer von einer Verbindung, bevor Phase 4 die UI liefert?**
   - Was wir wissen: Das App-Passwort erscheint in Nextcloud unter "Geräte und Sitzungen"
     mit dem Namen, den wir als User-Agent gesetzt haben.
   - Was unklar ist: ob das für Phase 3 als Sichtbarkeit reicht.
   - Empfehlung: Ja, mit einem sprechenden Präfix; die Verwaltungsoberfläche ist
     ausdrücklich Phase 4 (EXAPP-02).

4. **(RESOLVED: D-42, genau ein Scope) Scope-Modell: brauchen wir überhaupt zwei Scopes?**
   - Was wir wissen: v1 ist read-first, `TOOL-09` verbietet destruktive Operationen; die
     Spec empfiehlt Scope-Minimierung.
   - Was unklar ist: ob `nextcloud:write` (Upload, Termin anlegen, Notiz anlegen, Karte
     anlegen) als eigener Scope Mehrwert bringt oder nur eine zweite Consent-Zeile.
   - Empfehlung: Zwei Scopes einführen, `scopes_supported` im PRM auf `nextcloud:read`
     beschränken und `nextcloud:write` per `WWW-Authenticate`-`scope` nachfordern, wenn ein
     schreibendes Tool ohne Scope aufgerufen wird. Das ist der Step-up-Flow der Spec und
     kostet wenig. Falls das zu viel Mechanik für mvp ist: ein Scope, aber die Felder von
     Anfang an vorsehen.

5. **(RESOLVED: D-41, 10-s-Idempotenzfenster) Gnadenfenster bei der Refresh-Rotation (siehe A4).**
   - Empfehlung: Im discuss-Schritt vom Owner bestätigen lassen, weil es die einzige
     bewusste Aufweichung der konservativen Auslegung wäre.

## Sources

### Primary (HIGH confidence)

- Installierter SDK-Quellcode `mcp` 2.0.0 in `.venv/Lib/site-packages/mcp/`:
  `server/auth/routes.py`, `server/auth/provider.py`, `server/auth/settings.py`,
  `server/auth/handlers/{authorize,token,register,revoke,metadata}.py`,
  `server/auth/middleware/{bearer_auth,client_auth}.py`, `shared/auth.py`,
  `shared/auth_utils.py`, `server/lowlevel/server.py`, `server/mcpserver/server.py`,
  `client/auth/{oauth2,utils}.py`
- `uv.lock` (mcp 2.0.0, cryptography 50.0.0, pyjwt 2.13.0, httpx2 2.10.0)
- nextcloud/server (master, gelesen 2026-08-15):
  `core/Controller/ClientFlowLoginV2Controller.php`, `core/Service/LoginFlowV2Service.php`,
  `core/Db/LoginFlowV2Mapper.php` (lifetime 1200), `core/Controller/AppPasswordController.php`,
  `core/Controller/WellKnownController.php`, `lib/private/User/Session.php`
- nextcloud/HaRP (main): `haproxy_agent.py` (Routing, `nc_get_user`, Blacklist,
  Session-Cache), `README.md`
- nextcloud/app_api (main): `lib/Controller/HarpController.php`,
  `lib/Controller/AppConfigController.php`, `lib/Controller/OCSApiController.php`,
  `appinfo/routes.php`
- MCP-Spec 2026-07-28, "Authorization Server Discovery"
  (modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery)
- MCP-Spec draft, "Authorization" (modelcontextprotocol.io/specification/draft/basic/authorization)
- Projekt-Artefakte: `docs/spike-discovery.md` (Messmatrix vom 2026-08-15),
  `.planning/phases/02-exapp-shell/02-RESEARCH.md`, `02-SECURITY.md` (AR-02-06),
  `appinfo/info.xml`, `Dockerfile`, `compose.exapp.yml`, `deploy/Caddyfile`,
  `scripts/bootstrap_exapp.sh`, `src/mcp_connector/{config,deps}.py`,
  `src/mcp_connector/exapp/{auth,middleware,discovery}.py`
- PyPI-JSON für `cryptography` (50.0.0, 158 Releases, pyca/cryptography)

### Secondary (MEDIUM confidence)

- claude.com/docs/connectors/building/authentication (Hersteller-Doku: Auth-Typen,
  DCR/CIMD-Auswahl, Callback-URLs, Refresh-Verhalten, Timeouts, Egress-Range,
  Discovery-Fallbacks)
- developers.openai.com/api/docs/mcp (CIMD-Empfehlung, DCR weiterhin unterstützt)
- docs.nextcloud.com Developer Manual, Login Flow (Ablauf, 20-Minuten-Token,
  `DELETE /ocs/v2.php/core/apppassword`)
- docs.nextcloud.com Developer Manual, ExApp Routes (access_level PUBLIC/USER/ADMIN,
  `headers_to_exclude`, `bruteforce_protection`)

### Tertiary (LOW confidence)

- Community-Quellen zur ChatGPT-Redirect-URI
  (`https://chatgpt.com/connector_platform_oauth_redirect`) und zum
  DCR-Verhalten des ChatGPT-Connectors: Medium-Artikel, Qlik-Support-Artikel,
  OpenAI-Community-Thread. Im E2E-Lauf gegen den echten Connector verifizieren.

## Metadata

**Confidence breakdown:**

- Standard Stack: HIGH. Alle Versionen aus `uv.lock` und `.venv` gelesen, keine neuen
  Pakete nötig.
- SDK-Fähigkeiten und -Lücken: HIGH. Aus dem Quellcode der installierten Version 2.0.0
  gelesen, nicht aus Dokumentation abgeleitet.
- Nextcloud Login Flow v2 und App-Passwort-Widerruf: HIGH. Controller- und Service-Code
  von nextcloud/server master gelesen; Lebensdauer 1200 s aus dem Mapper.
- HaRP-Routing, Nutzerauflösung und Brute-Force-Verhalten: HIGH für den Code,
  MEDIUM für die Auswirkung im Betrieb (nicht unter Last gemessen).
- Discovery-Topologie: HIGH für "was Nextcloud beantwortet" (Spike-Messung plus
  Routen-Code), MEDIUM für "was Claude und ChatGPT probieren".
- Client-Verhalten Claude/ChatGPT: MEDIUM für Claude (Hersteller-Doku), LOW bis MEDIUM
  für ChatGPT (Community-Quellen).
- Pitfalls: HIGH für die aus Code abgeleiteten (1 bis 12, 14), MEDIUM für 13 und 15.

**Research date:** 2026-08-15
**Valid until:** 2026-09-15 für die SDK- und Nextcloud-Befunde; **2026-08-29** für die
Client-Befunde zu Claude.ai und ChatGPT, weil beide Connector-Plattformen sich schnell
bewegen (CIMD verdrängt gerade DCR).
