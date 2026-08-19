<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Phase 5: Hardening und Store-Einreichung, Recherche

**Recherchiert:** 2026-08-19
**Domain:** Nextcloud App Store Distribution, AppAPI-Lebenszyklus (Install/Update/Uninstall), MCP-Client-Kompatibilitaet, Berechtigungs- und Missbrauchstests
**Confidence:** HIGH fuer AppAPI/Store/Client-Mechanik (an Quellcode und Live-Endpunkten verifiziert), MEDIUM fuer die noch nicht gegen echte Clients gemessenen Teile von SC4

---

## Summary

Erfolgskriterium 1 ist am 19.08.2026 erledigt: `mcp_connector` 0.1.0 ist live im Store. Das ist an
zwei unabhaengigen Stellen live nachgeprueft, nicht angenommen: die App steht in
`https://apps.nextcloud.com/api/v1/appapi_apps.json` (26 ExApps gesamt, unsere Release-Zeile
`0.1.0`, `platformVersionSpec >=32.0.0 <35.0.0`, Download auf das GitHub-Release-Asset), und
`ghcr.io/street1983nk/mcp_connector:0.1.0` liefert anonym einen OCI-Image-Index mit `linux/amd64`
und `linux/arm64`. Der Store-Teil dieser Phase ist damit kein Rechercheobjekt mehr.

Der Rest der Phase ist unangenehmer, als die Roadmap unterstellt, und zwar an genau einer Stelle:
**Erfolgskriterium 2 ist mit dem Store-UI von Nextcloud 34 nicht erfuellbar, weil dieses UI keine
Deinstallation ausloest.** Der Remove-Knopf der neuen `appstore`-App ruft fuer eine ExApp
`disableExApp()` und damit `GET /apps/app_api/apps/disable/{appId}`. Der AppAPI-Endpunkt
`uninstallApp` wird in NC 34 aus dem Frontend nirgends aufgerufen, obwohl die Service-Funktion
`uninstallExApp(appId, removeData)` existiert. In NC 33 war das noch anders: dort gab es eine
Checkbox "Delete data on remove" und einen echten Aufruf von
`/apps/app_api/apps/uninstall/{appId}?removeData=<bool>`. Zusaetzlich ist `removeData` auf der
AppAPI-Seite per Signatur auf `false` vorbelegt, und `occ app_api:app:unregister` sagt im Hilfetext
ausdruecklich "data is kept by default". Dazu kommt, dass AppAPI beim Entfernen einer ExApp die
ExApp-Konfiguration in Nextcloud nie loescht, und dass die Nextcloud-App-Passwoerter, die dieser
Connector pro Verbindung anlegt, in `oc_authtoken` liegen und von keinem AppAPI-Pfad angefasst
werden. Das ist messbar und nicht theoretisch: das Volume `nc_app_mcp_connector_data` liegt auf
diesem Rechner noch da, zwei Tage nach dem letzten Lauf, mit 85 Clients, 84 Autorisierungen und 83
Refresh-Tokens in `oauth.sqlite3`.

Die zweite unangenehme Konsequenz derselben Recherche betrifft den Ein-Klick-Anspruch (BL-06): eine
Store-Installation in NC 34 setzt **keine** Umgebungsvariablen. Mit genau einem konfigurierten
Docker-Daemon fragt das UI nicht einmal nach, es installiert direkt; `deployOptions` bleibt leer.
`NC_MCP_PUBLIC_URL` ist damit auf jeder Store-Installation leer, und unser eigener info.xml-Kommentar
sagt korrekt, was das bedeutet: kein Client kann eine Verbindung abschliessen. Ein Ein-Klick-Install
ergibt heute eine funktionsunfaehige OAuth-Installation. Der Ausweg ist verifiziert und liegt
vollstaendig im eigenen Code: AppAPI speichert Werte einer **Admin**-Declarative-Settings-Form ueber
`ExAppConfigService::setAppConfigValue()` in dieselbe ExApp-Konfiguration, aus der `oauth/crypto.py`
heute schon den Data Key liest (`POST /ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values`).
Ausserdem setzt AppAPI `value` aus `<default>` in `info.xml`, sodass nicht instanzspezifische
Schalter ueber das Manifest vorbelegt werden koennen.

Bei den Clients ist die Nachricht gut. Open WebUI (ab 0.6.31, aktuell 0.11.0) ist ein vollwertiger
Streamable-HTTP-MCP-Client mit OAuth 2.1 und Dynamic Client Registration, pro Nutzer
authentifiziert, und registriert genau **eine** Redirect-URI. Damit faellt die Cursor-Falle (BL-04)
weg, und der Konnektor sollte plug-and-play passen. Der Scope kommt aus unserer PRM
(`scopes_supported`), `resource` wird nach RFC 8707 mitgeschickt, ein Refresh-Token vergeben wir
ohnehin unabhaengig vom Scope. MUCGPT bleibt bei dem, was BL-12 beschrieben hat, mit einer neuen,
im Quellcode verifizierten Praezisierung: der `headers`-Block von MUCGPT filtert `authorization`
aktiv heraus, ein Basic-Header ist also **nur** ueber `forward_token: true` plus
`forward_auth_override` moeglich.

**Primaere Empfehlung:** Phase 5 nicht als "Store-Einreichung" planen, sondern als drei getrennte
Schnitte: (1) Ein-Klick-Tauglichkeit herstellen (Admin-Settings-Form fuer Public URL und die drei
AUTH-07-Schalter, gelesen ueber den vorhandenen ExApp-Config-Kanal), (2) Deinstallation
selbst in die Hand nehmen (registrierte occ-Aktion, die alle Nextcloud-App-Passwoerter widerruft,
den Store leert und den Data Key entfernt, plus ein Runbook, das die AppAPI-Wahrheit je
NC-Version benennt), (3) Beweise fuehren (Store-Install auf frischer Instanz, Permission-Parity
mit einem echten Read-only-Share, Create-only-Writes, Negativ-Credential-Lasttest, fuenf
Client-Dokus). Erfolgskriterium 1 wird nicht neu geplant, sondern als erledigt dokumentiert.

---

## Phase Requirements

| ID | Beschreibung | Recherche-Stuetze |
|----|--------------|-------------------|
| EXAPP-04 | App ist im Nextcloud App Store eingereicht (Zertifikat via CSR-PR, Signatur, info.xml-Validierung, Datenweitergabe-Disclosure) vor der Conference September 2026 | **Bereits erfuellt und live verifiziert** (Abschnitt "Status Delta"). Offen bleibt nur die Pflege: Folgereleases 0.1.x (Abschnitt "Release-Mechanik"), Beschreibungstext inkl. FAQ (Abschnitt "Store-Beschreibung"), und die Frage, ob der Store-Eintrag ohne Ein-Klick-Tauglichkeit ehrlich ist (Abschnitt "Ein-Klick-Luecke"). |
| EXAPP-05 | Setup-Doku pro Client (Claude.ai/Desktop, ChatGPT, Cursor, Open WebUI, MUCGPT) mit den bekannten Stolperstellen | `docs/client-setup.md` deckt Claude Desktop, Claude Code, Claude.ai, ChatGPT und Cursor bereits in Messqualitaet ab. Fehlen: Open WebUI (vollstaendig aus dem Quellcode recherchiert, Abschnitt "Open WebUI") und MUCGPT (BL-12 plus neue Header-Praezisierung, Abschnitt "MUCGPT"). |

Zusaetzlich in dieser Phase erwartet (nicht als Requirement-ID gefuehrt, aber Erfolgskriterium):
SC2 (Install/Uninstall auf sauberer Instanz), SC3 (Permission-Parity, Create-only-Writes,
Negativ-Credential-Lasttest), SC4 (fuenf Client-Dokus gegen den echten Client).

**Kein CONTEXT.md vorhanden.** Diese Recherche traf also keine gesperrten Entscheidungen an; alle
Empfehlungen unten sind Vorschlaege und keine Wiedergabe bereits getroffener Beschluesse. Die
Owner-Entscheidungen aus dem Auftrag (FAQ-Abschnitt, BL-06 und BL-12 in Phase 5 ziehen) sind wie
Vorgaben behandelt.

---

## Project Constraints (from CLAUDE.md)

Direktiven aus `./CLAUDE.md` und den globalen Regeln, die der Planner einhalten muss:

| Direktive | Konsequenz fuer Phase 5 |
|-----------|-------------------------|
| Deadline Store-Einreichung vor der Conference September 2026, notfalls Scope kuerzen, nie den Termin | Die Deadline ist mit dem Live-Release am 19.08. bereits gehalten. Alles in dieser Phase ist damit Qualitaet, nicht Termin. Das erlaubt, SC2 richtig zu loesen statt schnell. |
| Tech-Stack: Python 3.13, `mcp>=2.0,<3`, `uv` als Toolchain (System-Python ist defekt), Docker/WSL2 fuer die Test-Nextcloud | Jeder Testbefehl der Phase laeuft ueber `uv run`. Kein globales `python`/`pip`. |
| Lizenz AGPL-3.0, Repo public auf GitHub `street1983nk` (privates Konto, nicht Akara-GitLab) | Store-Artefakte und Screenshots bleiben in diesem Repo. Kein GitLab. |
| Code und README Englisch, Projektkommunikation Deutsch, keine Em-Dashes, echte Umlaute | Die FAQ existiert dreisprachig (README.md/de/fr) plus Store-Beschreibung in drei Sprachen. Das ist der reale Preis, siehe "Store-Beschreibung". |
| Security: der MCP darf nie mehr sehen als der angemeldete Nutzer, keine destruktiven Writes in v1 | SC3 ist die Pruefung genau dieser zwei Saetze. Der Contract-Test `tests/contract/test_no_destructive_calls.py` ist das bestehende Gate. |
| Solo-Betrieb, Wartungsaufwand pro Feature zaehlt | Gegen eine eigene Admin-UI-Seite spricht die Wartung; fuer die Declarative-Settings-Form spricht, dass Nextcloud sie rendert und wir nur ein Schema liefern. |
| GSD-Workflow: keine direkten Repo-Edits ausserhalb eines GSD-Kommandos | Diese Recherche hat nichts am Code geaendert. |
| Nach jedem Edit sofort committen und pushen, ohne Fragen | Gilt fuer die Ausfuehrung der Plaene. |
| Commits ohne Claude-Attribution (`includeCoAuthoredBy=false`) | Gilt fuer die Ausfuehrung. |
| Doku-Seite mitziehen: nach API-/Verhaltensaenderung `docs-site` und `openapi` anpassen | In diesem Projekt gibt es keine docs-site; das Aequivalent sind `README.md`/`.de`/`.fr`, `docs/*` und die Store-Beschreibung in `info.xml`. Eine Verhaltensaenderung (z. B. Admin-Settings) muss alle vier treffen. |
| README dreisprachig halten (EN/DE/FR), Uebersetzungen automatisch nachziehen | Jeder neue README-Abschnitt (FAQ) kostet drei Fassungen. |
| Ruff ueber das ganze Repo vor Push (`ruff check .` und `ruff format --check .`) | Gilt fuer jeden Plan. |
| Vokabular-Gate: das Wort "archiv" in oeffentlichen Artefakten vermeiden | Betrifft CHANGELOG und Store-Beschreibung. Achtung: im Store-Kontext ist "release archive" ein Fachbegriff; in `docs/store-submission.md` steht er schon, das ist interne Doku. In `info.xml` und `CHANGELOG.md` vermeiden. |
| Keine Emojis, Icons als SVG | Betrifft die Screenshots und jede UI-Ergaenzung. |

**Projekt-Skills:** `.claude/skills/` existiert nicht; CLAUDE.md sagt das ebenfalls
("No project skills found"). Es gibt also keine zusaetzlichen Skill-Regeln zu beachten.

---

## Status Delta: was Erfolgskriterium 1 heute schon ist

Live geprueft am 2026-08-19, nicht aus der Roadmap uebernommen.

| Fakt | Beweis |
|------|--------|
| App ist im Store gelistet und fuer ExApp-Installationen sichtbar | `GET https://apps.nextcloud.com/api/v1/appapi_apps.json` enthaelt `mcp_connector` unter 26 ExApps [VERIFIED: apps.nextcloud.com API] |
| Release 0.1.0, Plattform `>=32.0.0 <35.0.0` | dieselbe Antwort, Feld `platformVersionSpec` [VERIFIED] |
| Download-URL ist das GitHub-Release-Asset | `https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.0/mcp_connector-0.1.0.tar.gz` [VERIFIED] |
| Image anonym ziehbar, echtes Multi-Arch | `ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.0` liefert `application/vnd.oci.image.index.v1+json` mit `linux/amd64` und `linux/arm64` (plus zwei Attestation-Eintraege); Token via anonymem `ghcr.io/token` [VERIFIED: ghcr.io Registry API] |
| Nur ein Tag existiert | `tags/list` = `["0.1.0"]` [VERIFIED] |
| Screenshot-URL erreichbar | `raw.githubusercontent.com/.../docs/screenshots/connections.png` antwortet 200 mit 39532 Bytes [VERIFIED] |

**Nicht mehr recherchieren:** Zertifikatsprozess, Signaturverfahren, XSD-Struktur, `pre-info.xslt`,
Pflichtfelder, Multi-Arch-Pflicht. Das steht vollstaendig und korrekt in
`.planning/phases/05-store-research.md` und `docs/store-submission.md`, und der Live-Zustand
bestaetigt es. Ebenso erledigt: die Lehre zum leeren XML-Element in `<default>` (Fix b0ac128).
Nebenbefund, der diese Lehre erklaert und praezisiert: im Store-Datenmodell ist das Feld
`default = CharField(max_length=256, blank=True)` ohne `null=True`, ein `None` aus einem leeren
Element laeuft also zwangslaeufig in eine NOT-NULL-Verletzung [VERIFIED: nextcloud/appstore
`nextcloudappstore/core/models.py`].

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Store-Listung, Signaturpruefung, Metadaten-Validierung | App Store (apps.nextcloud.com) | Repo (`appinfo/info.xml`, GitHub Release) | Der Store validiert nur beim Upload; danach ist er nur noch Verzeichnis. |
| Sichtbarkeit der App in einer Instanz | Nextcloud-Instanz (AppAPI `ExAppFetcher`) | App Store | Die Instanz zieht `appapi_apps.json` und cacht 3600 s. |
| Download und Signaturpruefung des Release-Archivs bei der Installation | Nextcloud-Instanz (AppAPI `ExAppArchiveFetcher`) | GitHub Releases | Die Instanz laedt das tar.gz von **unserer** URL, nicht vom Store. |
| Image-Pull, Volume, Container, Env-Injektion | Deploy Daemon (HaRP) | AppAPI (`DockerActions`) | Nur der Daemon spricht mit Docker; AppAPI baut die Parameter. |
| Setzen der Deploy-Umgebungsvariablen | AppAPI (aus `info.xml` `<default>` und `deployOptions`) | Store-UI (setzt in NC 34 nichts) | Deshalb ist die Ein-Klick-Luecke eine AppAPI-Tier-Eigenschaft, kein Fehler unserer App. |
| Persistente Admin-Konfiguration zur Laufzeit | Nextcloud (`oc_appconfig` via AppAPI ExApp-Config) | ExApp (liest per OCS) | Verifizierter Kanal, denselben nutzt heute der Data Key. |
| Rendering der Admin-Einstellungen | Nextcloud (Declarative Settings) | ExApp (liefert nur das Schema) | Kein eigenes Frontend, kein Wartungsaufwand. |
| Widerruf eines Nextcloud-App-Passworts | Nextcloud (`oc_authtoken`) | ExApp (`DELETE /ocs/v2.php/core/apppassword` mit genau diesem Passwort) | Nur wir kennen die Zuordnung Verbindung zu Passwort; AppAPI raeumt hier nie auf. |
| Loeschen des ExApp-Datenvolumes | Deploy Daemon, ausgeloest von AppAPI mit `removeData: true` | Admin (`occ ... --rm-data`) | Default ist `false`, und das NC-34-UI loest es nie aus. |
| Berechtigungs-Durchgriff | Nextcloud ACLs | ExApp (Impersonation ueber AppAPI-Header) | Unveraendert seit Phase 2; SC3 prueft die Kette, nicht die Schicht. |
| Drosselung eines Credential-Floods | Reverse Proxy (Admin) | ExApp (`oauth/throttle.py`, nicht auf `/mcp`) | `/mcp` ist bewusst undrosselt (D-37); die Bremse gegen einen Flood liegt beim Admin. |
| Client-Registrierung und Browser-Login | Client (Claude.ai, ChatGPT, Open WebUI) | ExApp (AS-Haelfte) | Was ein Client schickt, entscheidet der Client; wir pruefen nur. |

---

## Standard Stack

### Core

Diese Phase fuehrt **keine neue Laufzeitabhaengigkeit** ein. Alles Benoetigte ist vorhanden.

| Library | Version (im Projekt) | Purpose | Why Standard |
|---------|----------------------|---------|--------------|
| pytest + pytest-asyncio | vorhanden (`pytest 9.1.1` im Cache sichtbar) | Alle Beweise der Phase | Bestehende Testpyramide, Marker `integration`/`matrix` bereits konfiguriert |
| httpx / httpx2 | 0.28.x / SDK-intern | Lasttest und Negativproben | Async, schon ueberall benutzt; `httpx2` ist der Client, den `mcp 2.x` nutzt und den die ExApp-Integrationstests bereits verwenden |
| `asyncio.gather` | stdlib | Parallelisierung des Negativ-Credential-Lasttests | Ein Lasttest mit 200 gleichzeitigen 401ern braucht kein Werkzeug von aussen |
| Docker + Compose | 29.5.2 / v5.1.4 (gemessen) | Frische Instanz fuer den Store-Install-Test | Bestehende Topologie `compose.exapp.yml` |
| occ (im Nextcloud-Container) | NC 34.0.3 | Registrierung, Deinstallation, Bruteforce-Inspektion | Der einzige Weg zu `app_api:app:unregister --rm-data` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sqlite3` (CLI, im Wegwerf-Container) | beliebig | Beweis, was im Volume liegt und was nach dem Purge nicht mehr | Fuer den Uninstall-Beweis; nicht im Produktionsimage noetig |
| `curl` | 8.19.0 (gemessen) | Store- und Registry-Pruefungen, Negativproben | Wie in `docs/exapp-install.md` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest + `asyncio.gather` fuer den Lasttest | `hey`, `vegeta`, `locust`, `k6` | Neue Abhaengigkeit, neues Reporting-Format, und der Messwert, auf den es ankommt, sind Nextcloud-PHP-Requests im Access-Log, nicht Latenzperzentile. Der Eigenbau ist hier kleiner und ehrlicher. |
| Declarative Settings (Admin-Sektion) fuer die Schalter | Eigene HTML-Seite unter einer `ADMIN`-Route in `info.xml` | Eine eigene Seite kann Knoepfe (Declarative Settings kennen keinen Button-Typ), kostet aber Frontend-Wartung und eine 14. Route. Empfehlung: Form fuer Werte, eine registrierte occ-Aktion fuer die destruktive Handlung. |
| Registrierte occ-Aktion fuer den Purge | Ein zusaetzlicher Knopf auf `/connections` (nur eigener Account) | `/connections` kann nur den eigenen Account raeumen. Fuer "Deinstallation raeumt alle Daten auf" braucht es eine instanzweite Aktion, und die gehoert einem Admin-Werkzeug. |
| `<default>` in `info.xml` fuer die Public URL | nichts, Wert ist instanzspezifisch | Eine Default-URL waere immer falsch. `<default>` taugt nur fuer die drei nicht instanzspezifischen Schalter. |

**Installation:** keine.

**Version verification:** Es wird kein Paket installiert, also gibt es keine Registry-Pruefung zu
dokumentieren. Die gemessenen Werkzeugversionen stehen unter "Environment Availability".

---

## Package Legitimacy Audit

Diese Phase installiert **keine** externen Pakete. Kein neuer npm-, PyPI- oder crates-Eintrag ist
empfohlen, kein `pyproject.toml`-Diff an den Dependencies vorgesehen.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| *(keines)* | | | | | | Nicht anwendbar |

**Wegen slopcheck-Verdikt `[SLOP]` entfernte Pakete:** keine.
**Als `[SUS]` markierte Pakete:** keine.

Sollte ein Plan spaeter doch ein Lasttest-Werkzeug wollen (`hey`, `vegeta`, `locust`, `k6`), gilt das
Gate von vorn: erst slopcheck und Registry-Pruefung im richtigen Ecosystem, dann ein
`checkpoint:human-verify` vor dem Install. Die Empfehlung dieser Recherche ist, es nicht zu
brauchen.

---

## Architecture Patterns

### System Architecture Diagram: Store-Installation bis erste Verbindung

```
[Admin im Browser]
      |
      | 1. Apps-Seite oeffnen
      v
[Nextcloud 34, App "appstore"] --2. GET appapi_apps.json (Cache 3600 s)--> [apps.nextcloud.com]
      |
      | 3. "Install" -> genau ein Docker-Daemon vorhanden?
      |      ja  -> kein Dialog, direkt weiter          (Ein Klick)
      |      nein -> DaemonSelectionDialog, Admin waehlt (Zwei Klicks)
      v
[AppAPI: enableApp(appId, daemonName), deployOptions = LEER]
      |
      | 4. Release-Archiv von UNSERER Download-URL laden
      v
[GitHub Releases] --tar.gz--> [AppAPI: Signatur gegen Zertifikat pruefen, entpacken, info.xml lesen]
      |
      | 5. Env bauen: APP_ID/SECRET/VERSION/HOST/PORT/APP_PERSISTENT_STORAGE/NEXTCLOUD_URL
      |    + je deklarierter Variable value = <default>, leere Werte werden VERWORFEN
      |    ==> NC_MCP_PUBLIC_URL fehlt, weil wir kein <default> haben und keiner es setzt
      v
[HaRP: createVolume nc_app_mcp_connector_data -> Image von ghcr.io ziehen -> Container starten]
      |
      | 6. Healthcheck -> GET /heartbeat -> POST /init -> PUT /enabled?enabled=1
      v
[ExApp: Data Key aus oc_appconfig lesen oder erzeugen, Settings-Form registrieren]
      |
      | 7. Nutzer traegt Connector-URL in seinen Assistenten ein
      v
[Client] --401 + resource_metadata--> [/.well-known/...] --DCR--> [/register] --Browser--> [NC-Login]
      |
      | 8. Consent -> Code -> Token
      v
[ExApp legt ein Nextcloud-App-Passwort an (Login Flow v2) und speichert es verschluesselt]
      |
      +--> Zustand danach liegt an DREI Orten: Volume (SQLite), oc_appconfig (Data Key),
           oc_authtoken (ein App-Passwort pro Verbindung)
```

Der Punkt der Zeichnung ist Schritt 5 und die letzte Zeile. Schritt 5 ist die Ein-Klick-Luecke,
die letzte Zeile ist die Uninstall-Luecke.

### System Architecture Diagram: was "Remove" in NC 34 wirklich tut

```
[Admin klickt "Remove"]
      |
      v
[actionRemove -> useAppsStore.uninstallApp(appId)]
      |
      | app.app_api === true?
      v
[exApps.uninstallApp(appId)] --> exAppApi.disableExApp(appId)
      |
      v
[GET /apps/app_api/apps/disable/{appId}]  (PasswordConfirmationRequired)
      |
      v
[AppAPI disableExApp: PUT /enabled?enabled=0 an die ExApp, dann Container STOPPEN]
      |
      +--> ExApp bleibt registriert
      +--> Container existiert weiter (nur gestoppt)
      +--> Volume bleibt, SQLite bleibt vollstaendig
      +--> oc_appconfig behaelt den Data Key
      +--> jedes angelegte App-Passwort bleibt in oc_authtoken gueltig

Der Pfad, der wirklich deinstalliert, wird vom NC-34-UI NICHT betreten:
[GET /apps/app_api/apps/uninstall/{appId}?removeData=true]  (im Frontend nie aufgerufen)
[occ app_api:app:unregister <appid> --rm-data]              (der einzige verlaessliche Weg)
```

### Pattern 1: Admin-Werte ueber Declarative Settings, gelesen ueber den ExApp-Config-Kanal

**What:** Eine zweite Declarative-Settings-Form registrieren, diesmal mit
`section_type: "admin"` und echten Feldern, und die Werte zur Laufzeit aus der
ExApp-Konfiguration lesen. Genau derselbe Kanal, den `oauth/crypto.py` fuer den Data Key benutzt.

**When to use:** Fuer `NC_MCP_PUBLIC_URL` (Feldtyp `url`), DCR ein/aus (`checkbox`),
Allowlist-Modus (`checkbox`), erlaubte Clients (`text`). Also genau BL-06.

**Warum das trägt, nachgewiesen im Quellcode:** `SetValueListener` schreibt fuer
`section_type === admin` ueber `ExAppConfigService::setAppConfigValue($app, $fieldId, $value)`,
und `getAppConfigValues` liest denselben Schluessel wieder plain zurueck. Der Schluessel ist die
**Field-Id**, ohne Praefix.

```python
# Quelle: nextcloud/app_api lib/Listener/DeclarativeSettings/{Set,Get}ValueListener.php (v34.0.3
# und main), plus der bereits im Repo erprobte Lesepfad in src/mcp_connector/oauth/crypto.py
#
# Schreiben tut Nextcloud. Wir lesen nur, mit genau dem Aufruf, den crypto._read_key schon macht:
#   POST /ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values
#   body: {"configKeys": ["public_url", "oauth_dcr", "oauth_allowlist_only", "oauth_allowed_clients"]}
#   headers: appapi_auth_headers("", ...) + OCS_HEADERS
#
# Vorrangregel, die der Planner festlegen muss (Vorschlag):
#   1. Admin-Wert aus der ExApp-Konfiguration, wenn gesetzt und nicht leer
#   2. sonst Deploy-Env (NC_MCP_*), damit bestehende Installationen unveraendert weiterlaufen
#   3. sonst der Default aus config.py / oauth/registry.py
```

**Zwei Fallen, beide verifiziert:**

1. **Niemals `sensitive: true`** an einem Feld, dessen Wert die ExApp zur Laufzeit braucht. Der
   `SetValueListener` verschluesselt sensible Feldwerte vorher zusaetzlich mit `ICrypto`
   (Server-Secret). Die ExApp bekommt dann einen Blob zurueck, den sie nicht aufmachen kann. Keines
   der vier Felder braucht `sensitive`.
2. **Declarative Settings kennen keinen Button-Typ.** Die Typenliste ist vollstaendig: `text`,
   `password`, `email`, `tel`, `url`, `number`, `checkbox`, `multi-checkbox`, `radio`, `select`,
   `multi-select` [VERIFIED: nextcloud/server stable34 `lib/public/Settings/DeclarativeSettingsTypes.php`].
   Eine destruktive Aktion gehoert also nicht in diese Form.

### Pattern 2: Nicht instanzspezifische Vorbelegung ueber `<default>` im Manifest

**What:** AppAPI setzt `value` einer deklarierten Variablen aus `<default>` und verwirft jede
Variable mit leerem Endwert. Ein `<default>` im Manifest wirkt also auf einer Store-Installation,
ohne dass ein Admin etwas tut.

**When to use:** Fuer Schalter mit sinnvollem Festwert. **Nicht** fuer `NC_MCP_PUBLIC_URL`.

**Warum, und wo die Bombe liegt:** In AppAPI 34.0.3 steht der Code inline in
`ExAppService::getAppInfo`: `'value' => $envVar['default'] ?? ''`, danach
`array_filter(... $envVar['value'] !== '')`. Ein **leeres** Element `<default></default>` kommt
durch den simplexml/json-Roundtrip als leeres Array an, ist damit nicht `''`, wird nicht
gefiltert und landet per `sprintf('%s=%s', ...)` als die Zeichenkette `Array` in der
Container-Umgebung. In AppAPI main ist das durch den neuen `ExAppEnvVarsHelper` mit einer
`toString()`-Normalisierung reparariert; auf unserer Zielversion 34.0.3 existiert diese Datei
nicht. Unsere vier Variablen fuehren gar kein `<default>`, wir sind also heute nicht betroffen,
und ein leeres `<default>` wurde ohnehin schon vom Store mit einem 500 bestraft. Wer ein
`<default>` ergaenzt, muss es befuellen oder das Element weglassen.

### Pattern 3: Deinstallation als registrierte occ-Aktion der ExApp

**What:** Eine ExApp kann bei Nextcloud ein occ-Kommando registrieren:
`POST /ocs/v2.php/apps/app_api/api/v1/occ_command` mit `name`, `description`, `hidden`,
`arguments`, `options`, `usages` und `execute_handler` (eine Route auf uns). Nextcloud baut daraus
ein echtes Symfony-Command und ruft beim Aufruf unseren Handler ueber den internen
AppAPI-Pfad (`PublicFunctions`) auf, nicht ueber den oeffentlichen Proxy.

**When to use:** Fuer `occ mcp_connector:purge` als der Aktion, die SC2 ueberhaupt erfuellbar
macht: alle gespeicherten Autorisierungen durchlaufen, je Autorisierung das Nextcloud-App-Passwort
per `DELETE /ocs/v2.php/core/apppassword` mit genau diesem Passwort widerrufen, danach die
Store-Tabellen leeren und den Data Key aus der ExApp-Konfiguration entfernen
(`DELETE /ocs/v2.php/apps/app_api/api/v1/ex-app/config`).

**Warum das der richtige Ort ist:** Ein Admin, der deinstallieren will, ist ohnehin auf der
Kommandozeile, weil `--rm-data` nur dort existiert. Das Runbook wird damit zu drei Zeilen in
einer Reihenfolge, die stimmen muss.

**Sicherheitsauflage, nicht optional:** Der Handler wird wie `/init` und `/enabled` ueber den
Daemon aufgerufen und darf deshalb **keinen** Eintrag in `<routes>` bekommen. Genau das ist die
Begruendung, die der grosse Kommentar in `appinfo/info.xml` fuer die drei Lifecycle-Pfade
gibt (T-02-20): der PHP-Proxy haengt selbst gueltige AppAPI-Header an, eine deklarierte Route
wuerde die Aktion fuer jeden im Internet erreichbar machen. Der Handler muss dieselbe
Doppelsicherung fahren wie `exapp/lifecycle.py`: `x-origin-ip` im Header bedeutet
PHP-Proxy und wird mit 404 beantwortet, danach `require_appapi`.

### Pattern 4: Reihenfolge im Uninstall-Runbook (die Reihenfolge ist der Inhalt)

Der Data Key liegt in Nextcloud (`oc_appconfig`), die verschluesselten App-Passwoerter liegen im
Volume. Wer erst `--rm-data` macht, hat danach keine Chance mehr, die Nextcloud-App-Passwoerter zu
widerrufen: das Wissen, welches Passwort zu welcher Verbindung gehoert, war im Volume.

```
# 1. Widerruf, solange beides noch da ist: Volume UND Data Key
occ mcp_connector:purge           # loescht App-Passwoerter, Store-Zeilen und den Data Key

# 2. Erst danach die App entfernen, inklusive Volume
occ app_api:app:unregister mcp_connector --rm-data

# 3. Beweis: es ist wirklich weg
docker volume ls | grep nc_app_mcp_connector_data      # keine Zeile
occ app_api:app:list | grep mcp_connector              # keine Zeile
occ user:setting alice                                  # kein "MCP Connector:"-Eintrag mehr
```

### Anti-Patterns to Avoid

- **Beim `enabled=0`-Hook aufraeumen.** Verlockend, weil der Remove-Knopf in NC 34 genau diesen
  Hook feuert. Aber `disableExApp()` wird auch beim **Update** aufgerufen
  (`lib/Command/ExApp/Update.php`, Zeile 169) und beim gewoehnlichen Deaktivieren. Ein Aufraeumen
  dort loescht bei jedem Update jede Verbindung jeder Nutzerin. Nicht tun.
- **SC2 als "das UI macht das schon" dokumentieren.** Es macht es nachweislich nicht. Eine Doku,
  die das behauptet, ist eine Zusicherung, die ein Audit sofort kippt.
- **Den Store-Text mit Codeblöcken schreiben.** Die In-Instanz-Ansicht filtert `code` und `pre`
  weg (siehe "Store-Beschreibung"). Die URL im Backtick verschwindet dort spurlos.
- **Eine breite `<route>` fuer den occ-Handler deklarieren.** Siehe Pattern 3.
- **Die Permission-Parity nur als Leak-Test fahren.** Der bestehende Test beweist, dass bob nicht
  sieht, was alice hat. SC3 fragt zusaetzlich, ob der MCP-Blick eines eingeschraenkten Nutzers dem
  Web-Blick gleicht, also auch nach dem, was er **sehen darf** (Read-only-Share) und dort **nicht
  darf** (Create hinein).
- **Auf `/mcp` eine Drosselung einbauen, weil der Lasttest weh tut.** D-37 hat das begruendet
  abgelehnt; die Bremse gehoert in den Reverse Proxy und in die Doku.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Admin-Oberflaeche fuer vier Werte | Eigene HTML-Seite, eigene Route, eigenes CSRF | Declarative Settings mit `section_type: admin` | Nextcloud rendert, validiert und speichert; wir liefern ein Schema. Der Wertepfad laeuft komplett in AppAPI ohne Aufruf bei uns. |
| Persistenz fuer Admin-Werte | Eigene Tabelle im SQLite-Store | ExApp-Konfiguration (`oc_appconfig` via AppAPI) | Ueberlebt `--rm-data` nicht als Datenmuell, ist ein anderes Backup, und der Lesecode existiert bereits (`crypto._read_key`). |
| Admin-Kommando | Eigenes Shell-Skript im Repo, das occ und curl kombiniert | Registriertes ExApp-occ-Kommando | Kommt ueber den internen AppAPI-Pfad, braucht keine Credentials im Klartext, taucht in `occ list` auf und wird bei `unregisterExApp` automatisch abgemeldet. |
| Widerruf eines Nextcloud-App-Passworts | Eigener Admin-Endpunkt oder DB-Zugriff | `DELETE /ocs/v2.php/core/apppassword`, authentifiziert mit genau diesem App-Passwort | Bereits implementiert (`oauth/loginflow.revoke_app_password`), braucht keine Admin-Rechte und keine Nutzersitzung. |
| Lasttest-Werkzeug | Neue Abhaengigkeit | `asyncio.gather` plus `httpx` im Test | Der Messwert ist die Anzahl der Nextcloud-PHP-Requests, nicht die Latenzverteilung. |
| Bruteforce-Beobachtung | Eigener Zaehler | `occ security:bruteforce:attempts` und `occ security:bruteforce:reset <ip>` | Nextcloud fuehrt die Liste schon, `docs/client-setup.md` nennt beide Kommandos bereits. |
| Store-Metadaten-Validierung | Eigener XSD-Check | Upload gegen den Store, plus `pre-info.xslt` vor dem lokalen Check | Der lokale Rohcheck meldet `routes` als Fehler, das ist ein bekannter falsch-positiver Befund (05-store-research.md, Frage 1). |
| Markdown-Rendering im Store pruefen | Raten | Die zwei belegten Allow-Listen abgleichen (Website: `bleach` mit Tabellen und `code`; In-Instanz: `dompurify` ohne beides) | Sonst schreibt man einen Text, der auf der Website gut aussieht und in Nextcloud loechrig ist. |

**Key insight:** Fast alles, was diese Phase braucht, existiert schon: der ExApp-Config-Lesepfad
(Data Key), der App-Passwort-Widerruf (Disconnect), die Settings-Form-Registrierung
(Wegweiser), die Permission-Fidelity-Testmaschinerie und der Destruktiv-Contract-Test. Phase 5
ist ueberwiegend Wiederverwendung an neuen Aufrufstellen, nicht Neubau.

---

## Runtime State Inventory

Diese Phase ist keine Umbenennung, aber sie hat dieselbe Frage im Kern: **welche Laufzeitzustaende
bleiben nach einer Deinstallation zurueck?** Alle fuenf Kategorien sind explizit beantwortet.

| Kategorie | Gefundene Eintraege | Erforderliche Aktion |
|-----------|---------------------|----------------------|
| **Gespeicherte Daten** | Docker-Volume `nc_app_mcp_connector_data` mit `oauth.sqlite3` (196608 Bytes, letzter Schreibzugriff 2026-08-17, existiert auf diesem Rechner heute noch). Gemessene Zeilen: `clients` 85, `authorizations` 84, `refresh_tokens` 83, `flows` 0, `auth_codes` 0, `access_tokens` 0, `user_access` 0. Jede `authorizations`-Zeile traegt ein AES-GCM-verschluesseltes Nextcloud-App-Passwort. | Datenmigration im Sinne von "Loeschen": nur `--rm-data` bzw. `?removeData=true` entfernt das Volume. Zusaetzlich Code-Aenderung: `occ mcp_connector:purge` muss die Zeilen und die zugehoerigen Nextcloud-Passwoerter vorher aufloesen. |
| **Live-Service-Konfiguration** | (a) Nextcloud `oc_appconfig` (vor AppAPI 35: `appconfig_ex`), App-Id `mcp_connector`, Schluessel `oauth_data_key`, als sensitiv gespeichert. `ExAppService::unregisterExApp()` loescht Talk-Bots, File-Actions, Menue-Eintraege, Initial-States, Skripte, Styles, Task-Processing-Provider, **Settings-Forms**, Setup-Checks, den ExApp-Ordner, occ-Kommandos, Deploy-Optionen, Webhooks, die `ex_apps`-Zeile und die Routen. Die ExApp-**Konfiguration** ist in dieser Liste nicht enthalten. (b) Der ExApp-Container `nc_app_mcp_connector` wird beim NC-34-Remove nur gestoppt, nicht entfernt. | Code-Aenderung: der Purge muss den Config-Schluessel selbst loeschen (`DELETE .../ex-app/config`). Runbook: `docker rm nc_app_mcp_connector` als Aufraeumschritt benennen, wenn nur der UI-Weg gegangen wurde. |
| **OS-registrierte Zustaende** | Kein Windows-Task-Scheduler-Eintrag, kein pm2, kein systemd-Unit. Der einzige OS-nahe Zustand sind Docker-Objekte: das genannte Volume, der Container, das gezogene ghcr.io-Image im Image-Store des Daemons (AppAPI entfernt das Image nie), und die Compose-Objekte der Testtopologie (`nc-mcp-exapp_nextcloud-exapp-data`, `nc-mcp-exapp_registry-exapp-data`, Netz `nc-mcp-exapp-net`). | Runbook fuer den Testlauf; im Produkt-Runbook nur das Image erwaehnen (Plattenplatz, kein Datenschutzthema). |
| **Secrets und Umgebungsvariablen** | (a) `oc_authtoken`: pro Verbindung ein Nextcloud-App-Passwort mit dem Namen `MCP Connector: <Client>` (Praefix `AGENT_PREFIX` in `oauth/loginflow.py`). Von **keinem** AppAPI-Pfad angetastet, bleibt nach jeder Form der Deinstallation gueltig. (b) `APP_SECRET` der AppAPI-Registrierung: wird bei `unregisterExApp` mit der `ex_apps`-Zeile entfernt, beim Update bewusst erhalten (`$appInfo['secret'] = $exApp->getSecret()`). (c) Lokale Entwicklungsdateien `.env.exapp` und `.env.test` mit Wegwerf-Credentials und `HP_SHARED_KEY`, git-ignoriert. (d) `NC_MCP_*` Deploy-Variablen leben nur im Container. | (a) ist der wichtigste Punkt der ganzen Phase und braucht Code (Purge). (b) und (d) erledigt AppAPI. (c) nur im Testrunbook. |
| **Build-Artefakte und installierte Pakete** | `dist/` mit dem gebauten Store-Archiv; `.venv/`; `__pycache__`-Baeume in `tests/` und `src/`; das ghcr.io-Image `0.1.0` als einziger Tag. Kein `egg-info` mit veraltetem Namen (App-Id ist seit Phase 1 eingefroren). | Nichts zu migrieren. Beim naechsten Release: `dist/` neu bauen, neuen Tag pushen, Tag und `<version>` und `<image-tag>` identisch halten. |

**Der kanonische Satz fuer diese Phase:** Nachdem der Admin im Store-UI auf "Remove" geklickt hat,
laufen 84 gueltige Nextcloud-App-Passwoerter weiter, das Volume mit ihren verschluesselten Kopien
liegt unveraendert da, der Data Key steht noch in `oc_appconfig`, und die App gilt in AppAPI
weiterhin als registriert. Das ist der Zustand, den Erfolgskriterium 2 verneint. Ohne eigene
Purge-Aktion und ohne ein Runbook, das den occ-Weg vorschreibt, ist SC2 nicht erreichbar.

---

## Common Pitfalls

### Pitfall 1: "Remove" im Store-UI von NC 34 deinstalliert nicht

**Was schiefgeht:** Der Test "Deinstallation raeumt alle Daten auf" wird ueber das UI gefahren, das
UI meldet Erfolg, die App verschwindet aus der Liste der installierten Apps, und niemand schaut ins
Volume.
**Warum:** `apps/appstore/src/actions/actionRemove.ts` ruft `useAppsStore.uninstallApp`, das fuer
`app.app_api === true` an `exApps.uninstallApp` weitergibt, und dort steht
`await exAppApi.disableExApp(appId)`. Die Funktion `uninstallExApp(appId, removeData = false)`
existiert in `apps/appstore/src/service/exAppApi.ts`, wird aber im ganzen `apps/appstore/src` von
niemandem aufgerufen. In NC 33 (33.0.8) war es korrekt: `AppManagement.js` rief
`appApiStore.uninstallApp(appId, removeData)`, und `AppDetailsTab.vue` hatte die Checkbox
"Delete data on remove".
**Vermeidung:** Den SC2-Beweis in zwei Zeilen fuehren. Zeile A: UI-Weg, und protokollieren, was
danach noch da ist (das ist der ehrliche Befund fuer die Doku). Zeile B: occ-Weg mit
`mcp_connector:purge` und `app_api:app:unregister --rm-data`, und protokollieren, dass danach
nichts mehr da ist. Die Client- und Admin-Doku muss den occ-Weg als den Weg nennen.
**Warnzeichen:** `docker volume ls` zeigt `nc_app_mcp_connector_data` nach dem Remove;
`occ app_api:app:list` zeigt die App weiter; `docker ps -a` zeigt einen gestoppten
`nc_app_mcp_connector`.

### Pitfall 2: Ein-Klick-Installation ohne `NC_MCP_PUBLIC_URL`

**Was schiefgeht:** Ein Admin installiert per Klick, alles wird gruen, der erste Nutzer traegt die
URL in Claude.ai ein und bekommt eine Discovery, die auf `http://127.0.0.1:8765` zeigt. Die
Verbindung scheitert, und das Fehlerbild sieht nach einem Client-Problem aus.
**Warum:** Mit genau einem Docker-Daemon ruft `exApps.enableApp` direkt
`exAppApi.enableExApp(app, dockerDaemons[0])` ohne `deployOptions`, es gibt keinen Dialog und kein
Env-Formular im NC-34-Store-UI. AppAPI verwirft jede deklarierte Variable mit leerem Endwert, also
kommt `NC_MCP_PUBLIC_URL` gar nicht im Container an, und `config.public_url()` faellt auf
`DEFAULT_PUBLIC_URL` zurueck. Unser eigener info.xml-Kommentar beschreibt genau diesen Fall.
**Vermeidung:** Drei Stufen, in dieser Reihenfolge planen. (1) Ein Admin-Feld (Typ `url`) in einer
Admin-Declarative-Settings-Form, gelesen ueber den ExApp-Config-Kanal. (2) Eine Herleitung als
Fallback: AppAPI setzt `NEXTCLOUD_URL` immer (aus `deployConfig['nextcloud_url']`, sonst aus
`getAbsoluteURL('')` mit `https` durch `http` ersetzt), daraus laesst sich
`<basis>/exapps/mcp_connector` bilden. Achtung, das Schema ist absichtlich heruntergesetzt und die
Adresse kann intern sein, eine Herleitung ist also nur ein Vorschlagswert und keine Wahrheit.
(3) Ein sichtbarer Setup-Zustand: solange keine belastbare Public URL vorliegt, soll die
Settings-Seite und `/connections` das sagen, statt dass ein Client an einer stillen Fehlkonfiguration
scheitert.
**Warnzeichen:** `/.well-known/oauth-protected-resource/mcp` liefert `resource` mit
`127.0.0.1:8765`; im Container-Log steht die Warnung aus `config.persistent_storage` nicht, aber
kein Client kommt durch.

### Pitfall 3: Ein leeres `<default>` wird auf AppAPI 34.0.3 zur Zeichenkette `Array`

**Was schiefgeht:** Jemand ergaenzt `<default></default>` fuer Dokumentationszwecke. Der Store
antwortet mit 500 (bekannt, Fix b0ac128). Wer es lokal ohne Store-Upload testet, bekommt statt
dessen `NC_MCP_OAUTH_DCR=Array` in die Container-Umgebung.
**Warum:** simplexml/json macht aus dem leeren Element ein leeres Array; AppAPI 34.0.3 filtert nur
gegen `''`, nicht gegen "nicht-skalar". In AppAPI main behebt `ExAppEnvVarsHelper::toString()` das,
auf 34.0.3 existiert die Datei nicht.
**Vermeidung:** `<default>` entweder befuellen oder das Element weglassen. Unsere vier Variablen
fuehren heute keines, das ist der sichere Zustand.
**Warnzeichen:** `docker inspect nc_app_mcp_connector` zeigt eine Env-Zeile mit dem Wert `Array`;
`registry._switch` schreibt eine Warnung "neither on nor off".

### Pitfall 4: Der Store-Beschreibungstext verliert in Nextcloud die Haelfte

**Was schiefgeht:** Die FAQ wird mit Codeblöcken, einer Tabelle und einzeiligen Umbruechen
geschrieben. Auf apps.nextcloud.com sieht das gut aus. In der App-Detailansicht von Nextcloud 34
sind Tabelle und Codeblöcke weg, und die vier Saetze unserer heutigen Beschreibung stehen als ein
einziger Absatz.
**Warum:** Zwei verschiedene Pipelines. Website: Python-`markdown` plus `bleach` mit
`MARKDOWN_ALLOWED_TAGS`, das `table`, `code`, `pre`, `audio`, `video`, Definitionslisten und mehr
erlaubt. In der Instanz: `marked` mit `gfm: false, breaks: false`, danach `dompurify.sanitize` mit
`ALLOWED_TAGS: h1..h6, strong, p, a, ul, ol, li, em, del, blockquote`. Kein `code`, kein `pre`,
kein `table`, kein `br`, kein `img`, kein `hr`. `breaks: false` heisst, dass einzelne Zeilenumbrueche
keinen Umbruch erzeugen.
**Vermeidung:** Auf den kleineren gemeinsamen Nenner schreiben: Ueberschriften, fett, kursiv,
Links, Aufzaehlungen, Blockquote, und Absaetze durch **Leerzeilen** trennen. Keine Backticks,
keine Tabellen. Laengenbegrenzung gibt es nur bei `summary` (XSD `l10n-string`, `maxLength 128`);
`description` ist `l10n-text` ohne Obergrenze und im Store-Datenmodell ein `TextField` mit dem
Hilfetext "Will be rendered as Markdown".
**Warnzeichen:** Die vier Saetze der aktuellen `<description>` sind durch einfache Umbrueche
getrennt; in der Instanz-Ansicht ist das heute schon ein Klumpen.

### Pitfall 5: Der Negativ-Credential-Lasttest trifft Nextcloud, nicht uns

**Was schiefgeht:** Man misst die Antwortzeiten unseres Containers, findet sie gut, und uebersieht,
dass jeder einzelne ungueltige Bearer eine vollstaendige Nextcloud-PHP-Runde gekostet hat.
**Warum:** HaRP fragt Nextcloud fuer **jeden** Request mit `Authorization`-Header, wer der Aufrufer
ist, auch auf `PUBLIC`-Routen, und cacht diese Antwort nur fuer Cookie-Sessions. Das steht so im
Modulkopf von `oauth/throttle.py` und stammt aus der HaRP-Quelle. Unser Verifier cacht
**ausschliesslich positive** Ergebnisse, ein ungueltiger Bearer schlaegt also jedes Mal bis in den
SQLite-Store durch. Und `/mcp` ist bewusst nicht gedrosselt (D-37) und traegt bewusst kein
`bruteforce_protection` (T-02-21).
**Vermeidung:** Zwei Credential-Formen getrennt messen, weil sie sich gegensaetzlich verhalten.
Ungueltiger **Bearer**: erzeugt keinen Nextcloud-Bruteforce-Eintrag (`Session::tryTokenLogin`
liefert false ohne Versuch zu zaehlen) und keinen HaRP-Blacklist-Eintrag, kostet aber eine
PHP-Runde pro Request. Ungueltiges **Basic**: erzeugt Bruteforce-Eintraege pro Quell-IP, und weil
ein Remote-MCP-Server fuer alle seine Nutzer eine IP ist, drosselt das die Instanz fuer alle
(steht schon in `docs/client-setup.md`, Abschnitt 3). Gemessen wird in Nextcloud-Requests pro
Angreifer-Request, nicht in Millisekunden; Messquelle ist das Access-Log des
Nextcloud-Containers.
**Warnzeichen:** `occ security:bruteforce:attempts` fuellt sich beim Bearer-Lauf (dann stimmt die
Annahme nicht mehr und der Befund ist neu); die Nextcloud-Antwortzeiten fuer normale Nutzer steigen
waehrend des Laufs.

### Pitfall 6: Permission-Parity als Tautologie

**Was schiefgeht:** Man vergleicht den MCP-Blick mit einem "Web-Blick", der ueber genau dieselben
Aufrufe mit denselben Credentials erzeugt wird. Der Test ist immer gruen und beweist nichts.
**Warum:** Unsere Tools sprechen bereits WebDAV, OCS und DAV, also dieselben Schnittstellen wie
die Weboberflaeche.
**Vermeidung:** Die Asymmetrie in die Daten legen, nicht in den Vergleich. Der bestehende
Bootstrap erzeugt nur alice und bob ohne Gruppen und ohne Shares. Fuer SC3 braucht es eine dritte
Lage: alice teilt eine Datei **read-only** mit bob und eine zweite gar nicht. Dann sind vier
Aussagen pruefbar, und keine ist tautologisch: bob findet die geteilte Datei ueber MCP (positiv),
bob findet die ungeteilte nicht (Leak, existiert schon), bob kann die geteilte lesen, und bob
kann **nicht** in den read-only geteilten Ordner hochladen, obwohl unser `files_upload`
create-only ist. Der letzte Punkt verbindet Permission-Parity und Create-only-Writes an einer
Stelle, an der Nextcloud entscheidet und nicht wir.
**Warnzeichen:** Der Testcode baut fuer die Referenzseite ein `Credentials`-Objekt oder
`httpx.BasicAuth` selbst. Der bestehende ExApp-Test verbietet sich das im Modulkopf ausdruecklich,
und aus demselben Grund.

### Pitfall 7: Das GitHub-Release-Asset ist eine Produktionsabhaengigkeit

**Was schiefgeht:** Nach dem naechsten Release wird das alte Asset aufgeraeumt oder ein
Release-Tag umgeschrieben, und plotzlich schlaegt die Installation bei fremden Admins fehl.
**Warum:** `ExAppArchiveFetcher::downloadInfoXml` nimmt `end($exAppAppstoreData['releases'])['download']`
und laedt das tar.gz zur **Installationszeit** von unserer URL, prueft die Signatur und liest
`info.xml` daraus. Der Store speichert nur die URL. Die Auswahl ist eindeutig, weil `ExAppFetcher`
die Releases vorher nach `min-version`/`max-version` filtert und auf die hoechste Version
reduziert.
**Vermeidung:** Release-Assets nie loeschen, Tags nie umschreiben, und im Release-Runbook nach dem
Upload einmal die URL mit `curl -I` gegenpruefen.
**Warnzeichen:** Ein 404 auf der Download-URL; AppAPI meldet "Failed to get app info for ... from
the Appstore".

### Pitfall 8: Neue Version erscheint nicht sofort in der Instanz

**Was schiefgeht:** Man laedt 0.1.1 hoch, sieht in der Testinstanz keinen Update-Hinweis und
sucht den Fehler im Release.
**Warum:** `AppAPIFetcher::INVALIDATE_AFTER_SECONDS = 3600` fuer den Stable-Kanal, 900 fuer
unstable, `RETRY_AFTER_FAILURE_SECONDS = 300`. `getExAppsWithUpdates()` vergleicht dann
`releases[0].version` mit der installierten Version per `version_compare`.
**Vermeidung:** Eine Stunde Geduld oder den Cache in der Testinstanz verwerfen. Im
Release-Runbook als erwartetes Verhalten notieren, damit es niemand als Fehler diagnostiziert.
**Warnzeichen:** `appapi_apps.json` auf apps.nextcloud.com zeigt die neue Version, die Instanz
nicht.

### Pitfall 9: Ein Update laeuft ueber `enabled=0` und liest die Routen neu

**Was schiefgeht:** Eine Routenaenderung wird als "wirkt erst nach Neuinstallation" angenommen,
oder umgekehrt wird beim `enabled=0`-Hook aufgeraeumt (siehe Anti-Patterns).
**Warum:** `occ app_api:app:update` macht: disable (also `PUT /enabled?enabled=0` plus Container
stoppen), `removeExAppRoutes` und `registerExAppRoutes` **aus dem neuen** `info.xml`,
Translations, `updateExAppInfo`, dann `deployExApp`. `deployExApp` entfernt den Container mit
`removeData: false` und legt das Volume per `createVolume` idempotent wieder an, das Volume und
damit jede Autorisierung ueberlebt. Das Secret wird bewusst uebernommen.
**Vermeidung:** Routenaenderungen als normalen Release-Inhalt planen. Und den `enabled=0`-Hook
weiterhin genau das tun lassen, was er heute tut.
**Warnzeichen:** Nach einem Update sind alle Verbindungen weg (dann wurde am Hook aufgeraeumt oder
der Data Key neu erzeugt).

### Pitfall 10: Open WebUI hinter http auf einer LAN-Adresse

**Was schiefgeht:** Ein selbstgehostetes Open WebUI unter `http://192.168.1.50:3000` oder
`http://openwebui.lan` bekommt bei der Registrierung 400 `invalid_redirect_uri`, und der Text
sieht aus wie ein Fehler bei uns.
**Warum:** Open WebUI registriert genau eine Redirect-URI:
`{webui.url oder request.base_url}/oauth/clients/{client_id}/callback`. Unser
`registry._redirect_allowed` erlaubt `https` beliebig und `http` nur fuer die Hostnamen
`127.0.0.1`, `localhost`, `::1`. Eine LAN-IP oder ein interner Hostname ueber http fallen durch,
und das ist beabsichtigt (D-35).
**Vermeidung:** In die Open-WebUI-Doku aufnehmen: Open WebUI hinter TLS betreiben oder auf
`localhost`/`127.0.0.1` erreichen, und `webui.url` korrekt setzen, weil daraus die Redirect-URI
gebildet wird. Der Unterschied zu Cursor ist wichtig fuer die Doku: Cursor scheitert an einem
`cursor://`-Schema in einem Drei-URI-Feld und ist damit heute ausgeschlossen; Open WebUI hat nur
eine URI und scheitert allenfalls am Schema der eigenen Installation, was der Admin aendern kann.
**Warnzeichen:** Unser Log zeigt eine abgelehnte Registrierung mit genau einer Redirect-URI und
`http` als Schema.

### Pitfall 11: MUCGPT nimmt keinen `Authorization`-Header aus `headers`

**Was schiefgeht:** Die Doku empfiehlt, in `config.yaml` unter `headers` einen
`Authorization: Basic ...` zu setzen. Es wird stillschweigend ignoriert, und die Verbindung
scheitert ohne brauchbare Meldung.
**Warum:** `McpLoader` kopiert `source_cfg.headers` mit dem Filter
`if header_name.lower() != "authorization"`. Der einzige Weg zu einem eigenen
`Authorization`-Header ist `forward_token: true` plus `forward_auth_override: "Basic base64(...)"`,
und ein Validator erzwingt genau diese Kombination
("forward_auth_override requires forward_token=true").
**Vermeidung:** Die MUCGPT-Doku auf genau diese zwei Schluessel schreiben, plus
`transport: streamable_http`.
**Warnzeichen:** Im MUCGPT-Log erscheint die Liste "Header names configured for source" ohne
`Authorization`.

### Pitfall 12: MUCGPT mit einem statischen App-Passwort bricht das Kernversprechen

**Was schiefgeht:** Der Out-of-the-box-Pfad wird als Loesung dokumentiert, ohne den Preis zu
nennen: `_auth_override` ist ein einzelner Wert pro MCP-Quelle, alle MUCGPT-Nutzer laufen unter
**einem** Nextcloud-Konto.
**Warum:** `McpBearerAuthProvider.auth_flow` setzt `request.headers["Authorization"] = self._auth_override`,
sobald ein Override existiert, und uebergeht die pro-Nutzer-Tokens im Klassen-Dict `_tokens`.
**Vermeidung:** Die MUCGPT-Doku muss den Pfad als Team- oder Dienstkonto kennzeichnen und die
Konsequenz benennen: das Berechtigungsversprechen gilt dann fuer das Dienstkonto, nicht fuer die
einzelne Person. Fuer echte Pro-Nutzer-Treue gibt es genau zwei Wege, und die architektonisch
interessante Nachricht ist, dass der zweite bei uns kleiner ist als BL-12 vermutet: ohne Override
schickt MUCGPT das **eigene Keycloak-OIDC-Token pro Nutzer** (`_tokens[uid]`, gesetzt in
`react_agent.py` aus `user_info.token`). Wenn wir dieses Token verifizieren koennten
(JWKS des Keycloak, Issuer und Audience gepruefft) und den Subject auf eine Nextcloud-Kennung
abbilden, brauchen wir **kein** Nextcloud-Credential dieser Person: als ExApp haben wir mit
`MODE_APPAPI` bereits die Impersonation. Die Bausteine (fuenfter Credential-Modus, `TokenVerifier`,
Client-Registry als Enforcement-Punkt) liegen alle. Was fehlt, sind ein Vertrauensanker (welcher
Issuer darf das) und die Identitaetsabbildung (setzt voraus, dass Nextcloud und MUCGPT dieselben
Konten kennen, also SSO oder LDAP). Das ist ein Feature, nicht ein Fix, und gehoert in die
Erstkontakt-Frage an it@M und nicht in Phase 5.
**Warnzeichen:** In der Doku steht "pro Nutzer" ueber einem Beispiel mit einem einzigen
`forward_auth_override`.

### Pitfall 13: Der Purge-Handler wird ueber den PHP-Proxy erreichbar

**Was schiefgeht:** Der `execute_handler` des occ-Kommandos bekommt einen Eintrag in `<routes>`,
damit "AppAPI ihn finden kann". Damit ist eine instanzweite Loeschaktion fuer jeden im Internet
aufrufbar, weil der PHP-Proxy selbst gueltige AppAPI-Header anhaengt.
**Warum:** Genau die Begruendung, die der Kommentar in `appinfo/info.xml` fuer `/heartbeat`,
`/init` und `/enabled` gibt (T-02-20). Der occ-Aufruf laeuft ueber `PublicFunctions` und damit
ueber denselben internen Pfad wie die Lifecycle-Endpunkte, braucht also keine Route.
**Vermeidung:** Keine Route deklarieren, und im Handler dieselbe Doppelsicherung wie in
`exapp/lifecycle.py._guard`: `x-origin-ip` vorhanden bedeutet 404, danach `require_appapi`.
**Warnzeichen:** Ein `curl` von aussen auf `/apps/app_api/proxy/mcp_connector/<handler>` bekommt
etwas anderes als 404.

### Pitfall 14: Zwei Nextcloud-Generationen, zwei Wahrheiten in einer Doku

**Was schiefgeht:** Die Admin-Doku beschreibt eine Deinstallation, die auf NC 33 richtig und auf
NC 34 falsch ist, oder umgekehrt. Unsere Dependency ist `min 32 max 34`, also sind beide im
Support.
**Warum:** Die ExApp-Verwaltung ist zwischen 33 und 34 umgezogen: in 33 in `apps/settings`
(mit `removeData`-Checkbox), in 34 in die neue App `apps/appstore` (ohne Uninstall-Aufruf).
`apps/appstore` existiert in stable32 und stable33 nicht.
**Vermeidung:** Im Runbook eine kleine Versionstabelle fuehren und den occ-Weg als den einen Weg
benennen, der auf allen drei Versionen gleich funktioniert.
**Warnzeichen:** Eine Anleitung, die einen UI-Klick als Deinstallation beschreibt, ohne die
Version zu nennen.

---

## Code Examples

Verifizierte Muster aus offiziellen Quellen und dem eigenen Repo.

### Deinstallation und Beweis (der einzige Weg, der auf NC 32 bis 34 gleich wirkt)

```bash
# Quelle: nextcloud/app_api v34.0.3, lib/Command/ExApp/Unregister.php (Optionen), plus
# lib/Controller/ExAppsPageController.php::uninstallApp (removeData default false)
#
# --rm-data ist notwendig. Der Hilfetext von --keep-data sagt es selbst:
#   "Keep ExApp data (volume) [deprecated, data is kept by default]."
occ app_api:app:unregister mcp_connector --rm-data

# Gegenprobe, alle drei muessen leer sein:
docker volume ls --format '{{.Name}}' | grep '^nc_app_mcp_connector_data$' || echo "volume weg"
occ app_api:app:list | grep mcp_connector || echo "nicht mehr registriert"
docker ps -a --format '{{.Names}}' | grep '^nc_app_mcp_connector$' || echo "kein container"
```

### Was nach dem UI-Weg zurueckbleibt (der SC2-Gegenbeweis, so gemessen)

```bash
# Quelle: eigene Messung 2026-08-19 auf diesem Rechner, Volume aus den Phase-3/4-Laeufen
docker run --rm -v nc_app_mcp_connector_data:/d:ro alpine:3 sh -c '
  apk add --no-cache sqlite >/dev/null 2>&1
  cp /d/oauth.sqlite3 /tmp/x.db
  for t in $(sqlite3 /tmp/x.db "select name from sqlite_master where type=%s table %s"); do
    printf "%s: " "$t"; sqlite3 /tmp/x.db "select count(*) from $t"
  done'
# Gemessen: clients 85, flows 0, authorizations 84, auth_codes 0,
#           refresh_tokens 83, access_tokens 0, user_access 0
# Die Kopie nach /tmp ist notwendig: sqlite3 kann eine read-only gemountete Datei nicht oeffnen.
```

### Admin-Werte lesen, mit dem Aufruf, den das Repo schon fuehrt

```python
# Quelle: src/mcp_connector/oauth/crypto.py (EXAPP_CONFIG_PATH, CONFIG_READ_SUFFIX) und
# nextcloud/app_api lib/Listener/DeclarativeSettings/{Set,Get}ValueListener.php
#
# EXAPP_CONFIG_PATH = "/ocs/v2.php/apps/app_api/api/v1/ex-app/config"
# Lesen ist POST auf .../config/get-values mit {"configKeys": [...]}; ein GET existiert nicht.
#
# Fuer eine Admin-Form gilt: der Config-Schluessel IST die Field-Id aus dem formScheme.
# Also z. B. fields = [{"id": "public_url", "type": "url", ...}] -> configKey "public_url".
#
# Zwei Auflagen:
#   - kein Feld mit "sensitive": true, dessen Wert die ExApp braucht (ICrypto-Blob, unlesbar)
#   - Vorrang: Admin-Wert > Deploy-Env (NC_MCP_*) > Code-Default, damit bestehende
#     Installationen mit gesetztem Env unveraendert weiterlaufen
```

### occ-Kommando registrieren (dieselbe Stelle wie die Settings-Form)

```python
# Quelle: nextcloud/app_api v34.0.3, appinfo/routes.php (OccCommand#registerCommand) und
# lib/Service/ExAppOccService.php (registerCommand, buildCommand)
#
# POST {base}/ocs/v2.php/apps/app_api/api/v1/occ_command
# json = {
#   "name": "mcp_connector:purge",
#   "description": "Revoke every MCP connection of this instance and delete all stored data.",
#   "hidden": 0,
#   "arguments": [],
#   "options": [{"name": "force", "mode": "none", "description": "Do not ask."}],
#   "usages": ["mcp_connector:purge --force"],
#   "execute_handler": "purge",      # eine Route auf UNS, absichtlich NICHT in <routes>
# }
# headers = appapi_auth_headers("", ...) + OCS_HEADERS
#
# Registrierung gehoert in denselben enabled=1-Zweig wie settings_form.register_settings_form,
# und mit derselben Fehlertoleranz: ein Fehlschlag darf das "error"-Feld nicht fuellen, sonst
# deaktiviert AppAPI die App sofort wieder (pitfall 11 der Phase 2).
# Abmelden muss niemand: unregisterExApp ruft occService->unregisterExAppOccCommands(appId).
```

### Der Store-Beschreibungstext auf dem kleineren gemeinsamen Nenner

```text
Quelle: nextcloud/server stable34 apps/appstore/src/composables/useMarkdown.ts (ALLOWED_TAGS)
und nextcloud/appstore nextcloudappstore/settings/base.py (MARKDOWN_ALLOWED_TAGS)

Erlaubt in BEIDEN Pipelines: h1..h6, strong, em, p, a, ul, ol, li, blockquote, del
Nur auf der Website:        table, code, pre, img, audio, video, dl/dt/dd, hr
Also verwenden:             Ueberschriften, Fettung, Links, Listen, Blockquote
Nicht verwenden:            Backticks, Codeblöcke, Tabellen, Bilder
Und:                        Absaetze mit LEERZEILE trennen (marked laeuft mit breaks: false)

Laengen: summary maxLength 128 (XSD l10n-string), description unbegrenzt (l10n-text / TextField)
```

### Negativ-Credential-Lasttest, Messgroesse Nextcloud-Requests

```python
# Quelle: src/mcp_connector/oauth/throttle.py (Modulkopf, HaRP-Befund) und
# src/mcp_connector/oauth/verifier.py ("Only positive results are cached")
#
# Zwei Laeufe, weil sich die beiden Credential-Formen gegensaetzlich verhalten:
#
# Lauf A, ungueltiger Bearer gegen /exapps/mcp_connector/mcp
#   erwartet: 401 je Request, KEIN Bruteforce-Eintrag, KEIN HaRP-Blacklist-Eintrag,
#             aber eine Nextcloud-PHP-Runde pro Request (HaRP fragt fuer jeden
#             Authorization-Header, auch auf PUBLIC-Routen)
#   gemessen wird: Zeilen im Access-Log des Nextcloud-Containers vor/nach dem Lauf
#
# Lauf B, ungueltiges Basic gegen dieselbe Route
#   erwartet: Bruteforce-Eintraege pro Quell-IP, danach Drosselung fuer ALLE hinter dieser IP
#   gemessen wird: occ security:bruteforce:attempts, danach occ security:bruteforce:reset <ip>
#
# Kein neues Werkzeug: asyncio.gather ueber N httpx-Requests, Marker "integration".
# /mcp bleibt undrosselt (D-37); das Ergebnis ist eine Zahl fuer die Doku und eine
# Empfehlung an den Admin (Rate Limit im Reverse Proxy), nicht ein Codefix bei uns.
```

---

## State of the Art

| Alter Stand | Aktueller Stand | Wann geaendert | Auswirkung |
|-------------|-----------------|----------------|------------|
| ExApp-Verwaltung im Settings-Frontend (`apps/settings`), Remove mit Checkbox "Delete data on remove" und echtem Uninstall-Aufruf | Eigene App `apps/appstore`; Remove ruft fuer ExApps nur `disable` | Nextcloud 34 (stable34 = 34.0.3); `apps/appstore` existiert in stable32/stable33 nicht | SC2 ist ueber das UI nicht erfuellbar; die Doku braucht den occ-Weg und eine Versionsnotiz |
| ExApp-Konfiguration in eigener Tabelle `appconfig_ex` | Migration nach `oc_appconfig` (`Version035000Date20260529120000`), Alt-Tabellen werden gedroppt (`...130000`) | AppAPI 35 (aktuell v35.0.0beta3, 18.08.2026) | Fuer uns transparent, weil wir ueber die OCS-Schnittstelle lesen. Beim Anheben der `max-version` auf 35 ist der Data-Key-Lesepfad der erste Test |
| Env-Var-Normalisierung inline in `ExAppService::getAppInfo` | Ausgelagert in `ExAppEnvVarsHelper` mit `toString()` fuer leere XML-Elemente | AppAPI 35 (Datei fehlt in v34.0.3) | Auf der Zielversion 34.0.3 ist ein leeres `<default>` weiter gefaehrlich |
| Docker Socket Proxy als Deploy-Daemon | HaRP ab NC 32 empfohlen, DSP-Entfernung fuer NC 35 geplant | seit NC 32 | unveraendert; unsere `min-version 32` ist damit begruendet |
| Open WebUI nur ueber `mcpo` (MCP-zu-OpenAPI-Proxy) | Nativer MCP-Client, Streamable HTTP, OAuth 2.1 mit DCR, pro Nutzer | ab Open WebUI 0.6.31 (aktuell 0.11.0) | Open WebUI wird von einem Sonderfall zum Standardfall; die Doku beschreibt eine OAuth-Verbindung, nicht einen Proxy |
| Dynamic Client Registration als der Weg | Client ID Metadata Documents (CIMD) in der MCP-Spec als Nachfolger, DCR als ueberholt markiert | MCP-Spec 2026-07-28 | BL-05, nicht v1. Betrifft heute nur Claude Code |

**Veraltet oder irrefuehrend im eigenen Repo:**

- `README.md` Abschnitt "Status" sagt "Version 0.1.0, phase 1 (server core)". Das ist nach vier
  Phasen und einem Live-Release falsch und steht ganz oben in der Datei, die ein Store-Besucher
  ueber den Repository-Link zuerst sieht. Gilt in drei Sprachen.
- `docs/client-setup.md` sagt "The full client matrix (ChatGPT, Cursor, Open WebUI, MUCGPT) follows
  in a later phase", enthaelt ChatGPT und Cursor aber inzwischen. Nur Open WebUI und MUCGPT fehlen
  wirklich. Ausserdem stehen dort "15 tools" und "twelve routes" (in `docs/exapp-install.md`),
  waehrend `info.xml` dreizehn Routen fuehrt.
- `docs/store-submission.md` beschreibt den CSR-PR als "the current blocker" und fuehrt die
  Vorab-Checkliste mit offenen Kaesten. Das ist der Stand vor dem 19.08.
- `docs/privacy.md` hat mit "Deletion and user control" bereits die inhaltliche Substanz der neuen
  FAQ. Die FAQ soll daraus zitieren und nicht daneben eine zweite Wahrheit aufbauen.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Die Zielinstanz fuer den SC2-Beweis ist Nextcloud 34.0.3 mit AppAPI 34.0.x, wie in `compose.exapp.yml`. Der Befund "Remove ruft nur disable" ist an `stable34` (34.0.3) verifiziert, nicht an jedem Patchlevel dazwischen. | Pitfall 1 | Falls ein 34.0.x-Patch das Frontend repariert, ist der Befund milder; der occ-Weg bleibt trotzdem der dokumentierte. Vor dem Beweis die tatsaechlich installierte Version festhalten. | 
| A2 | Aus `NEXTCLOUD_URL` laesst sich eine brauchbare Public URL herleiten. AppAPI setzt die Variable nachweislich immer, aber mit `https` durch `http` ersetzt und moeglicherweise mit einer internen Adresse. | Pitfall 2, Stufe 2 | Eine hergeleitete URL waere falsch und wuerde eine kaputte Discovery erzeugen, die aussieht wie eine konfigurierte. Deshalb nur als Vorschlagswert mit sichtbarem Setup-Zustand, nie als stiller Default. |
| A3 | Open WebUI verbindet sich mit unserem AS tatsaechlich Ende zu Ende. Registrierung, Scope-Quelle, `resource`-Parameter und Refresh-Verhalten sind aus dem Quellcode von 0.11.0 abgeleitet, aber kein Lauf gegen eine echte Instanz. | Open WebUI | SC4 fordert "gegen den echten Client verprobt". Ohne Lauf ist die Doku eine Vermutung. Der Lauf ist der Beweis. |
| A4 | MUCGPT verbindet sich mit `forward_token: true` plus `forward_auth_override`. Aus dem Quellcode vom 18.08.2026 abgeleitet, nicht gelaufen. | MUCGPT | Wie A3. Zusaetzlich haengt daran die Aussage im Outreach an it@M. |
| A5 | Ein registriertes ExApp-occ-Kommando funktioniert in unserer Topologie so, wie der AppAPI-Code es beschreibt. Die Schnittstelle ist verifiziert, ein Lauf gegen HaRP nicht. | Pattern 3 | Falls es scheitert, ist der Rueckfallweg eine Route mit `access_level: ADMIN` plus der Doppelsicherung gegen den PHP-Proxy, oder ein reines Runbook mit `occ app_api:app:unregister --rm-data` und einem ehrlichen Hinweis auf die zurueckbleibenden App-Passwoerter. |
| A6 | Nextcloud AIO als zweiter Smoke-Test (D-31, aus Phase 2 uebergeben) bleibt auf diesem Rechner unerreichbar, weil AIO eine oeffentliche Domain mit gueltigem TLS verlangt. | Environment Availability | Falls das Kriterium darauf besteht, braucht es eine Wegwerf-Domain und einen Host, also Owner-Aufwand ausserhalb dieses Rechners. Kandidat fuer bewusstes Descoping mit Begruendung. |
| A7 | Die 84 Autorisierungen im vorhandenen Volume gehoeren zu Testkonten (alice, bob) einer Wegwerf-Instanz und enthalten keine echten Nutzerdaten. | Runtime State Inventory | Falls doch, waere das Volume selbst ein Aufraeumauftrag mit Prioritaet, nicht nur ein Beweisstueck. |
| A8 | Der Store aktualisiert einen erneut hochgeladenen Release derselben Version, statt ihn abzulehnen. Der Kommentar im Upload-View sagt "create or update the models", ein Versuch wurde nicht gemacht. | Release-Mechanik | Falls er ablehnt, braucht ein Korrektur-Release eine neue Patchversion. Das ist ohnehin die saubere Praxis. |

---

## Open Questions

1. **Soll der Store-Eintrag warten, bis Ein-Klick wirklich funktioniert?**
   - Was wir wissen: Die App ist gelistet. Ein Admin, der jetzt per Klick installiert, bekommt eine
     Installation ohne `NC_MCP_PUBLIC_URL` und damit ohne funktionierende Client-Verbindung.
     Der stdio- und der Standalone-HTTP-Pfad sind davon nicht betroffen.
   - Was unklar ist: Wie sichtbar die App in den ersten Tagen ist und ob ein erster fremder Admin
     hineinlaeuft, bevor 0.1.1 da ist.
   - Empfehlung: Nicht zurueckziehen, sondern zuerst das Ein-Klick-Problem loesen und als 0.1.1
     nachschieben; bis dahin in der Store-Beschreibung und im README einen Satz fuehren, dass eine
     Angabe der oeffentlichen Adresse noetig ist und wo sie hingehoert. Owner-Entscheidung.

2. **Wo lebt die FAQ, wenn sie in drei Sprachen gepflegt werden muss?**
   - Was wir wissen: Die `description` im Store hat keine Laengengrenze und wird als Markdown
     gerendert, in drei Sprachen (en/de/fr existieren bereits). Das README existiert dreisprachig
     und muss laut Projektregel synchron gehalten werden. `docs/privacy.md` traegt die Substanz
     schon. Der Store hat kein FAQ-Feld.
   - Was unklar ist: Ob die FAQ langfristig eine Frage bleibt oder fuenf werden. Bei fuenf kostet
     jede Aenderung sechs Textstellen (drei READMEs, drei Beschreibungen).
   - Empfehlung: Eine kanonische, ausfuehrliche Fassung in `docs/faq.md` (Englisch), ein kurzer
     `## FAQ` im README mit der einen Frage und einem Link (dreisprachig, drei kurze Absaetze), und
     drei bis vier Saetze in jeder Store-Beschreibung. Der Store-Text ist der einzige Ort, den ein
     Nutzer sieht, ohne das Repository zu betreten, deshalb muss die Antwort dort stehen und nicht
     nur verlinkt sein.

3. **Ist ein instanzweiter Purge ohne Admin-Bestaetigung im UI vertretbar?**
   - Was wir wissen: Declarative Settings kennen keinen Button, ein occ-Kommando ist von Natur aus
     admin-only und protokollierbar, und der UI-Weg braucht in AppAPI ohnehin
     `PasswordConfirmationRequired`.
   - Was unklar ist: Ob ein Admin die Aktion auch im Browser erwartet.
   - Empfehlung: occ-Kommando mit `--force`-Pflicht als der Weg, ein Satz in der Settings-Form, der
     darauf zeigt. Kein Loeschknopf im Browser in v1.

4. **Wird `max-version` in dieser Phase auf 35 gehoben?**
   - Was wir wissen: NC 35 ist in Entwicklung (AppAPI v35.0.0beta3 vom 18.08.2026), unsere Spec ist
     `>=32.0.0 <35.0.0`, und in AppAPI 35 wandert die ExApp-Konfiguration nach `oc_appconfig`. DSP
     verschwindet dort ebenfalls, was uns nicht betrifft.
   - Was unklar ist: Wann NC 35 stabil ist und ob es vor oder nach der Conference kommt.
   - Empfehlung: In dieser Phase nicht heben. Als Backlog-Eintrag fuehren mit den zwei Testpunkten
     (Data-Key-Lesepfad nach der Migration, Store-UI-Verhalten beim Remove in 35).

5. **Bekommt der NC-34-Uninstall-Befund einen Upstream-PR?**
   - Was wir wissen: In `nextcloud/app_api` gibt es kein offenes Issue dazu (die Suche findet nur
     das geschlossene #297 "Add option to remove volume on ExApp removal"), und die Reparatur ist
     klein: `exApps.uninstallApp` muesste `uninstallExApp` aufrufen, und das UI braeuchte die
     Entsprechung der NC-33-Checkbox. CONTRIB-01 hat gezeigt, dass so ein PR dem Projekt nuetzt.
   - Was unklar ist: Ob das in den Zeitrahmen dieser Phase passt und ob es ein `server`- oder ein
     `app_api`-Thema ist (der Aufruf steht in `server`).
   - Empfehlung: Als eigener, kleiner Plan am Ende der Phase oder als Backlog-Eintrag. Der
     Erkenntniswert fuer uns ist schon eingesammelt; der PR ist Oekosystem-Flanke, kein Blocker.

---

## Environment Availability

Gemessen am 2026-08-19 auf dem Entwicklungsrechner.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Docker Engine | Store-Install-Test, ExApp-Topologie | ja | 29.5.2, `linux/x86_64` | keiner |
| Docker Compose | `compose.exapp.yml` | ja | v5.1.4 | keiner |
| docker buildx | Multi-Arch-Image fuer 0.1.1 | ja | v0.34.0-desktop.1 | amd64 allein wird vom Store akzeptiert |
| uv | jeder Testlauf (System-Python ist defekt) | ja | 0.11.7 | keiner, Projektvorgabe |
| Python (nur fuer Werkzeuge) | Hilfsskripte | ja | 3.13.1 | `uv run` |
| git | Release-Tag | ja | 2.54.0.windows.1 | keiner |
| gh | Release-Asset, Upstream-Recherche | ja | 2.92.0 | Web-UI |
| openssl | `HP_SHARED_KEY`, Signatur | ja | 3.5.6 | keiner |
| curl | Store-, Registry- und Negativproben | ja | 8.19.0 | keiner |
| tar | Store-Archiv | ja | GNU tar 1.35 | keiner |
| Laufende Test-Nextcloud `nc-mcp-test` | Unit- und Integrationstests Phase 1 | ja | `nextcloud:34-apache`, Up 4 Tage, healthy | Neu hochfahren per `scripts/bootstrap_test_nc.sh` |
| ExApp-Topologie (`caddy`, `nextcloud`, `appapi-harp`, `registry`) | SC2, SC3 ueber die volle Kette | nein, heruntergefahren | Volumes existieren noch (`nc-mcp-exapp_nextcloud-exapp-data`, `nc-mcp-exapp_registry-exapp-data`, `nc_app_mcp_connector_data`) | Wiederanfahren nach dem Rezept in STATE.md, Pending Todos: `HP_SHARED_KEY` exportieren, `up -d --wait`, App und Daemon abmelden, `bootstrap_exapp.sh` |
| Frische Nextcloud ohne Vorgeschichte | "per Klick auf einer sauberen Instanz" | herstellbar | neues Compose-Projekt oder `down -v` | Die vorhandene Instanz ist durch 84 Autorisierungen und Registrierungen vorbelastet und taugt nicht als "saubere Instanz" |
| Ausgehendes Internet aus dem Nextcloud-Container | `appapi_apps.json`, tar.gz von GitHub, Image von ghcr.io | wahrscheinlich, nicht gemessen | | Ohne das ist ein echter Store-Install nicht testbar; dann bleibt nur der bisherige `json-info`-Registrierungsweg, und SC2 waere nicht belegt |
| Oeffentliche Domain mit gueltigem TLS | Nextcloud-AIO-Smoke (D-31), Test von gehosteten Clients | nein | | AIO-Smoke descopen oder Owner-Aufwand; die gehosteten Clients sind fuer AUTH-04 bereits gegen `nc-staging.infranode.dev` belegt, das Staging ist aber am 16.08. abgebaut |
| Echte Client-Zugaenge (Claude Desktop, Claude.ai, ChatGPT, Cursor, Open WebUI, MUCGPT) | SC4 "gegen den echten Client verprobt" | teils | Claude.ai und ChatGPT am 16.08. belegt; Cursor als Ablehnung belegt | Open WebUI ist selbst hostbar (Docker) und damit machbar. MUCGPT ist ein Fremdsystem der Stadt Muenchen: entweder eine lokale Instanz aus dem Repo oder eine ehrliche Kennzeichnung "nicht gegen die Produktivinstanz verprobt" |

**Fehlende Abhaengigkeiten ohne Fallback:**

- Oeffentliche Domain mit TLS: blockiert den AIO-Smoke (A6) und einen erneuten Lauf gegen
  gehostete Clients gegen eine frische Instanz.
- Zugang zu einer echten MUCGPT-Instanz: blockiert die woertliche Lesart von SC4 fuer diesen
  Client.

**Fehlende Abhaengigkeiten mit Fallback:**

- ExApp-Topologie laeuft nicht: wieder anfahren, Rezept liegt vor.
- Saubere Instanz: neues Compose-Projekt statt Wiederverwendung.
- Open WebUI: lokal per Docker, `webui.url` auf `http://localhost:<port>` setzen, damit die
  Redirect-URI durch unsere Pruefung kommt (Pitfall 10).

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | ja | Unveraendert aus Phase 3: OAuth 2.1 mit PKCE S256, Login Flow v2, Nextcloud-App-Passwoerter. Neu in dieser Phase: die Admin-Ebene. Werte kommen aus den Declarative Settings, deren Schreibpfad Nextcloud selbst authentifiziert; die ExApp liest nur. |
| V3 Session Management | ja | Serverseitig zustandslos, keine eigene Session. Der neue occ-Handler darf keine Session annehmen und muss `require_appapi` fahren. |
| V4 Access Control | ja | Der kritische Punkt der Phase: eine instanzweite Loeschaktion. Kontrolle ist doppelt: keine `<route>` im Manifest (damit der PHP-Proxy sie nicht erreicht) und `x-origin-ip` gleich 404 im Handler, wie `exapp/lifecycle.py._guard`. Zusaetzlich `--force`-Pflicht. |
| V5 Input Validation | ja | Neu validiert werden vier Admin-Werte. Die Public URL ist die gefaehrlichste: sie wird zum `issuer` und zur `resource` und darf nicht beliebig sein. Vorhandene Bausteine: `config.normalize_base_url`, die Pruefung, dass eine Login-Adresse zu dieser Instanz gehoert (`/authorize/consent`), und `registry._redirect_allowed` als Muster fuer eine harte URL-Regel. |
| V6 Cryptography | ja | Nichts neu bauen. AES-GCM mit Row-AAD und der Data Key aus `oc_appconfig` bleiben unangetastet. Wichtig fuer den Purge: erst widerrufen, dann `--rm-data`, sonst ist der Schluessel weg, mit dem die App-Passwoerter noch loeschbar waeren. |
| V7 Error Handling und Logging | ja | Der Purge muss protokollieren, was er getan hat (Anzahl, nicht Werte). `oauth/throttle.py` und `verifier.py` zeigen das Muster: Digest, Zahl, Frist, nie ein Credential. |
| V13 API und Web Service | ja | Der Lasttest ist die Pruefung von genau dieser Kategorie unter Missbrauch: `/mcp` bleibt undrosselt (D-37), die Bremse ist der Reverse Proxy des Admins, und das muss dokumentiert und gemessen sein statt behauptet. |
| V14 Configuration | ja | Die Ein-Klick-Luecke ist ein Konfigurationsbefund: ein sicherheitsrelevanter Schalter (DCR) mit einem Default, der auf einer oeffentlichen Instanz zusammen mit einer fehlenden Allowlist die schwaechere Variante ist. Der Sicherheitshinweis aus BL-06 ("oeffentliche Instanz: Allowlist an oder DCR aus") muss ueber die UI erfuellbar sein und nicht nur ueber Env. |

### Known Threat Patterns fuer diesen Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Purge-Handler ueber den AppAPI-PHP-Proxy aufgerufen (der Proxy haengt gueltige AppAPI-Header selbst an) | Elevation of Privilege, Denial of Service | Keine `<route>` deklarieren; `x-origin-ip` gleich 404; `require_appapi`; `--force`. Dasselbe Muster wie T-02-20 fuer `/heartbeat`, `/init`, `/enabled` |
| Zuruecklassen gueltiger Nextcloud-App-Passwoerter nach der Deinstallation | Elevation of Privilege (spaeter), Information Disclosure | Purge vor `--rm-data`; Runbook mit erzwungener Reihenfolge; Gegenprobe in `occ user:setting <uid>` |
| Admin setzt eine fremde Public URL und lenkt damit Discovery und Redirects | Spoofing, Tampering | Harte Validierung des Admin-Werts (Schema, kein Userinfo, kein Fragment), und Konsistenzpruefung gegen die Instanz, wie sie `/authorize/consent` fuer Login-Adressen schon macht |
| Ein-Klick-Installation auf einer oeffentlichen Instanz mit DCR an und leerer Allowlist | Spoofing (fremde Clients registrieren sich) | Der AUTH-07-Schalter muss ohne Env erreichbar sein; Sicherheitshinweis in der Admin-Form direkt am Schalter, nicht nur in `docs/oauth-setup.md` |
| Credential-Flood auf `/mcp` als Verstaerker gegen Nextcloud (eine PHP-Runde pro ungueltigem Bearer) | Denial of Service | Gemessen statt geraten; Empfehlung Rate Limit im Reverse Proxy; `/mcp` bleibt undrosselt (D-37); positive-only Cache bleibt |
| Basic-Flood erzeugt Bruteforce-Eintraege und drosselt alle Nutzer hinter einer IP | Denial of Service | Bereits in `docs/client-setup.md` beschrieben; im Lasttest als eigener Lauf messen; `occ security:bruteforce:reset` im Runbook |
| Manipuliertes Release-Archiv unter unserer Download-URL | Tampering | Der Store prueft die Signatur beim Upload, und AppAPI prueft sie **erneut** beim Download zur Installationszeit; der private Key bleibt lokal |
| Prompt-Injection aus Nextcloud-Inhalten in den Assistenten | Tampering | Unveraendert aus v1: keine destruktiven Operationen (Contract-Test), Create-only-Writes; SC3 prueft, dass das ueber die volle Kette gilt |
| Datenabfluss an den vom Nutzer gewaehlten Assistenten (Drittland) | Information Disclosure | Kein technisches Control, sondern Transparenz: `docs/privacy.md`, die Prosa in `<description>` und die neue FAQ |

---

## Sources

### Primary (HIGH confidence)

- **nextcloud/server, `stable34` (34.0.3, HEAD e74c4d2 vom 19.08.2026), sparse clone:**
  `apps/appstore/src/actions/actionRemove.ts`, `apps/appstore/src/store/apps.ts` (`app.app_api`-Verzweigung),
  `apps/appstore/src/store/exApps.ts` (`uninstallApp` ruft `disableExApp`; `enableApp` ohne Dialog bei
  genau einem Daemon, `deployOptions` nie gesetzt), `apps/appstore/src/service/exAppApi.ts`
  (`uninstallExApp(appId, removeData = false)`, nirgends aufgerufen),
  `apps/appstore/src/composables/useMarkdown.ts` (`ALLOWED_TAGS`, `gfm: false`, `breaks: false`),
  `apps/appstore/src/components/MarkdownPreview.vue`,
  `lib/public/Settings/DeclarativeSettingsTypes.php` (vollstaendige Feldtypenliste, kein Button)
- **nextcloud/server, `stable33` (33.0.8), sparse clone:**
  `apps/settings/src/components/AppStoreSidebar/AppDetailsTab.vue` (Checkbox "Delete data on remove"),
  `apps/settings/src/mixins/AppManagement.js`, `apps/settings/src/store/app-api-store.ts`
  (`uninstall/{appId}?removeData=`)
- **nextcloud/app_api, Tag `v34.0.3` (Zielversion) und `main` (v35.0.0beta3, 18.08.2026):**
  `lib/Controller/ExAppsPageController.php` (`uninstallApp(..., removeData = false)`, `disableApp`,
  `getAppDeployOptions`), `lib/Command/ExApp/Unregister.php` (`--rm-data`, `--keep-data` deprecated,
  "data is kept by default"), `lib/Command/ExApp/Update.php` (disable, Routen neu, deploy),
  `lib/Service/AppAPIService.php` (`disableExApp` sendet `PUT /enabled?enabled=0` und stoppt den
  Container; `removeExAppsByDaemonConfigName`), `lib/Service/ExAppService.php`
  (`unregisterExApp`-Aufraeumliste ohne ExApp-Konfiguration; `getAppInfo`-Env-Parsing),
  `lib/Service/ExAppConfigService.php` (`setAppConfigValue`, `getAppConfigValues`),
  `lib/Service/ExAppOccService.php` (`registerCommand`, `buildCommand`), `appinfo/routes.php`
  (`occ_command`, `apps/uninstall/{appId}`), `lib/DeployActions/DockerActions.php`
  (`createVolume`, `removeVolume`, `removeExApp` mit `remove_data`, `buildDeployEnvs`,
  `buildDefaultExAppVolume`), `lib/Fetcher/AppAPIFetcher.php` (`INVALIDATE_AFTER_SECONDS 3600`,
  `900`, `RETRY_AFTER_FAILURE_SECONDS 300`, Store-URL), `lib/Fetcher/ExAppFetcher.php`
  (`appapi_apps.json`, Filter nach min/max und Reduktion auf die hoechste Version),
  `lib/Fetcher/ExAppArchiveFetcher.php` (Download von unserer URL, Signaturpruefung, info.xml),
  `lib/Listener/DeclarativeSettings/{Set,Get}ValueListener.php` (Admin-Werte gehen in die
  ExApp-Konfiguration; `sensitive` wird zusaetzlich mit `ICrypto` verschluesselt),
  `lib/Service/ExAppEnvVarsHelper.php` (nur in main; `toString`-Normalisierung),
  `lib/Migration/Version035000Date2026052912/130000.php` (Migration nach `oc_appconfig` und Drop)
- **nextcloud/appstore, `master`:** `nextcloudappstore/api/v1/release/info.xsd`
  (`summary` als `l10n-string` mit `maxLength 128`, `description` als `l10n-text` ohne Grenze),
  `nextcloudappstore/core/models.py` (`description = TextField(... "Will be rendered as Markdown")`,
  `default = CharField(max_length=256, blank=True)` ohne `null=True`),
  `nextcloudappstore/settings/base.py` (`MARKDOWN_ALLOWED_TAGS` inkl. `table`, `code`, `pre`),
  `nextcloudappstore/core/templatetags/markdown.py`, `nextcloudappstore/api/v1/serializers.py`
  (`AppReleaseDownloadSerializer`: download, signature, nightly), `nextcloudappstore/api/v1/views.py`
  (`AppReleaseView.post`, "create or update the models", Throttle-Scope `app_upload`)
- **Live-Endpunkte, geprueft 2026-08-19:** `https://apps.nextcloud.com/api/v1/appapi_apps.json`
  (26 ExApps, unser Eintrag mit Release 0.1.0 und `>=32.0.0 <35.0.0`),
  `ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.0` (OCI-Index amd64 und arm64),
  `ghcr.io/v2/street1983nk/mcp_connector/tags/list` (`["0.1.0"]`),
  `raw.githubusercontent.com/.../docs/screenshots/connections.png` (200, 39532 Bytes)
- **Eigene Messung 2026-08-19 auf dem Entwicklungsrechner:** Docker 29.5.2, Compose v5.1.4,
  buildx v0.34.0, uv 0.11.7, Python 3.13.1, git 2.54.0, gh 2.92.0, OpenSSL 3.5.6, curl 8.19.0,
  GNU tar 1.35; laufende Container `nc-mcp-test` und `findling-nextcloud`; Volume
  `nc_app_mcp_connector_data` mit `oauth.sqlite3` (196608 Bytes, mtime 2026-08-17) und den
  Zeilenzahlen clients 85, flows 0, authorizations 84, auth_codes 0, refresh_tokens 83,
  access_tokens 0, user_access 0
- **open-webui/open-webui, `main` (0.11.0), sparse clone:** `backend/open_webui/utils/oauth.py`
  (`get_oauth_client_info_with_dynamic_client_registration`: genau eine Redirect-URI
  `{webui.url oder request.base_url}/oauth/clients/{client_id}/callback`, `client_name` "Open WebUI",
  `grant_types` authorization_code und refresh_token; Scope-Vorrang aus der PRM;
  `should_send_oauth_resource` und `build_oauth_request_params` senden `resource` im Modus `auto`),
  `backend/open_webui/utils/mcp/client.py`
- **it-at-m/mucgpt, `main` (Stand 18.08.2026), sparse clone:**
  `mucgpt-core-service/app/agent/tools/mcp.py` (`headers` filtert `authorization` heraus;
  `McpBearerAuthProvider.auth_flow` bevorzugt `auth_override` vor den Pro-Nutzer-Tokens),
  `mucgpt-core-service/app/config/settings.py` (`MCPSourceConfig`, `MCPTransport` mit
  `streamable_http`, Validator "forward_auth_override requires forward_token=true"),
  `mucgpt-core-service/app/agent/react_agent.py` (`McpBearerAuthProvider.set_token(user_id, token)`)
- **Eigener Code (gelesen, nicht geaendert):** `appinfo/info.xml` (13 Routen, 4 Variablen, der
  Kommentar zu `NC_MCP_PUBLIC_URL`), `src/mcp_connector/exapp/lifecycle.py` (`_guard`,
  `x-origin-ip` gleich 404), `src/mcp_connector/oauth/crypto.py` (`EXAPP_CONFIG_PATH`,
  `CONFIG_KEY`, `data_key`), `src/mcp_connector/config.py` (`persistent_storage`, `public_url`,
  `exapp_settings`), `src/mcp_connector/oauth/registry.py` (`LOOPBACK_HOSTS`,
  `_redirect_allowed`, `_switch`), `src/mcp_connector/oauth/metadata.py` (`TOOL_SCOPE`,
  `REFRESH_SCOPE`, `scopes_supported`), `src/mcp_connector/oauth/provider.py` (Refresh-Token
  unabhaengig vom Scope), `src/mcp_connector/oauth/loginflow.py` (`APP_PASSWORD_PATH`,
  `AGENT_PREFIX`, `revoke_app_password`), `src/mcp_connector/oauth/throttle.py`,
  `src/mcp_connector/oauth/verifier.py` (nur positive Ergebnisse gecacht),
  `src/mcp_connector/nextcloud/credentials.py` (`MODE_BASIC`, `MODE_APPAPI`),
  `tests/integration/test_permission_fidelity_exapp.py`,
  `tests/contract/test_no_destructive_calls.py`, `tests/unit/test_oauth_abuse.py`, `Dockerfile`,
  `scripts/bootstrap_exapp.sh`, `docs/exapp-install.md`, `docs/client-setup.md`,
  `docs/store-submission.md`, `docs/privacy.md`, `.planning/phases/05-store-research.md`,
  `.planning/phases/04-*/04-RESEARCH.md`, `.planning/STATE.md`, `.planning/BACKLOG.md`

### Secondary (MEDIUM confidence)

- `https://docs.openwebui.com/features/extensibility/mcp/`: nativer MCP-Support ab 0.6.31,
  Transport Streamable HTTP, Auth-Optionen "None", "Bearer", "OAuth 2.1" (DCR) und
  "OAuth 2.1 (Static)", Auth pro Nutzer, MCP-Server nur von Admins anlegbar,
  `WEBUI_SECRET_KEY` sonst brechen die Tokens beim Neustart, OAuth-Tools nicht als Default-Tools,
  Typ muss "MCP (Streamable HTTP)" sein und nicht OpenAPI. Gegen den Quellcode von 0.11.0
  abgeglichen und dort in den nachprüfbaren Punkten bestaetigt.
- GitHub-Issue-Suche in `nextcloud/app_api` und `nextcloud/server` nach einem offenen Issue zur
  NC-34-Uninstall-Verdrahtung: kein Treffer, nur das geschlossene app_api#297
  "Add option to remove volume on ExApp removal". Eine Nicht-Fundstelle ist kein Beweis der
  Abwesenheit, deshalb MEDIUM.

### Tertiary (LOW confidence)

- Der Zeitpunkt der NC-35-Freigabe und damit die Frage, wann `max-version` gehoben werden muss.
  Belegt ist nur, dass AppAPI `v35.0.0beta3` am 18.08.2026 existiert.
- Ob ein Patchrelease innerhalb der 34.0.x-Reihe die Uninstall-Verdrahtung noch aendert. Geprueft
  ist `stable34` am 19.08.2026.

---

## Metadata

**Confidence breakdown:**

- AppAPI-Lebenszyklus (Install, Update, Disable, Uninstall, Volume, Env, ExApp-Konfiguration,
  occ-Kommandos): **HIGH**. An zwei AppAPI-Versionen und zwei Nextcloud-Release-Branches im
  Quellcode gelesen, und im Fall des zurueckgebliebenen Volumes auf diesem Rechner mit Zeilenzahlen
  gemessen.
- Store-Mechanik (Listung, Release-Upload, Download zur Installationszeit, Cache-Fristen,
  Markdown- und Laengengrenzen): **HIGH**. Store-Quellcode plus Live-Antworten der Store- und
  ghcr.io-APIs.
- Ein-Klick-Luecke und der Ausweg ueber Admin-Declarative-Settings: **HIGH** fuer den Befund und
  den Speicherpfad, **MEDIUM** fuer die Herleitung einer Public URL aus `NEXTCLOUD_URL` (A2).
- Open WebUI: **MEDIUM-HIGH**. Vollstaendig aus dem Quellcode von 0.11.0 abgeleitet und mit der
  offiziellen Doku abgeglichen, aber kein Lauf gegen eine echte Instanz (A3).
- MUCGPT: **MEDIUM-HIGH** fuer die Konfigurationsmechanik (Quellcode), **MEDIUM** fuer den
  Token-Exchange-Weg (Architektur schluessig, Vertrauensanker und Identitaetsabbildung offen).
- Testdesign fuer SC3 (Permission-Parity mit Read-only-Share, Create-only, Lasttest in
  Nextcloud-Requests): **MEDIUM**. Die Bausteine und die Messgroesse sind belegt, das Design ist
  ein Vorschlag dieser Recherche und noch nicht gelaufen.
- AIO-Smoke (D-31): **LOW** in der Machbarkeit auf diesem Rechner, **HIGH** in der Begruendung
  warum nicht.

**Research date:** 2026-08-19
**Valid until:** 2026-09-18 fuer die AppAPI- und Store-Befunde (stabile Release-Branches).
Kuerzer, etwa 7 Tage, fuer die Client-Befunde: Open WebUI liefert schnell (0.6.31 bis 0.11.0 in
wenigen Monaten), und der Uninstall-Befund kann durch einen 34.0.x-Patch oder einen fremden PR
jederzeit kippen. Vor der Ausfuehrung des ersten Plans noch einmal die tatsaechlich installierte
Nextcloud- und AppAPI-Version festhalten.
