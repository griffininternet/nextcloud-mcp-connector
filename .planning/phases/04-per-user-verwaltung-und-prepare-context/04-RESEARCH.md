# Phase 4: Per-User-Verwaltung und prepare_context - Research

**Researched:** 2026-08-17
**Domain:** AppAPI Declarative Settings (NC 34 / AppAPI 34), Per-User-Zugriffsschalter, Multi-Source-Bündel-Tool auf MCP
**Confidence:** HIGH (Kernbefund am laufenden System gemessen, nicht nur gelesen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Wo die Verwaltung lebt

- **D-44:** Geteilt, nach der Fähigkeit des jeweiligen Werkzeugs. Die Nextcloud-Einstellungen
  tragen über Declarative Settings den Ein/Aus-Schalter und einen Link; die Tabelle der
  verbundenen Clients mit Widerruf je Zeile liegt auf einer eigenen Seite dieser ExApp.
  Grund: Declarative Settings sind ein Formular ohne eigene Logik, eine Zeile mit Knopf je
  Verbindung ist damit nicht zu bauen, und SC 2 verlangt den Widerruf einzelner Tokens.
  Der Nutzer findet den Einstieg trotzdem dort, wo Nextcloud seine App-Schalter zeigt.
- **D-45:** Die eigene Seite baut auf der Seiten-Infrastruktur aus Phase 3 auf
  (`exapp/ui/layout.py`, `strings.py`, `icons.py`), nicht auf einer zweiten Bauweise.
  Dieselbe Kopfzeile, dieselbe Fußzeile, dieselben Sicherheitshinweise: die Consent-Seite
  hat den Ton dieser App bereits festgelegt.

#### Was der Ausschalter tut

- **D-46:** Der Schalter sperrt, er widerruft nicht. Tokens überleben, Wiedereinschalten
  stellt jede Verbindung wieder her. Ein Widerruf bleibt die eigene, benannte Handlung
  (Zeile in der Tabelle, oder Nextclouds "Geräte und Sitzungen").
- **D-47:** Der Zustand des Schalters wird in unserem eigenen Store geführt, und die
  Bearer-Grenze liest ihn dort. Er darf **keinen** zweiten Nextcloud-Roundtrip je Anfrage
  kosten: Phase 3 hat einen Roundtrip je MCP-Aufruf gemessen (SC 5, `03-VERIFICATION.md`),
  und diese Zahl bleibt die Obergrenze. Wie die Änderung aus den Declarative Settings in
  den Store kommt, klärt die Recherche; ein Poll ist die schlechteste der denkbaren
  Antworten.
- **D-48:** "Sofort" heißt: der nächste Tool-Aufruf nach dem Umlegen scheitert, nicht der
  übernächste. Ein Zwischenspeicher, der das aufweicht, ist keine Lösung. Wenn eine
  Spiegelung ohne Verzögerung nicht möglich ist, wird das im Plan benannt und nicht
  weggerundet.
- **D-49:** Der Schalter sperrt **jeden** Zugriff auf `/mcp`, OAuth-Verbindungen und den
  App-Passwort-Pfad aus Phase 1 gleichermaßen. Ein Schalter, der sichtbar etwas sperrt und
  dabei einen zweiten Weg offen lässt, ist in einem Audit nicht zu verteidigen.
- **D-50:** Standard für einen Nutzer, der die App nie geöffnet hat: **an**. Wer einen
  Connector verbindet, hat den Zugriff bereits bewusst genehmigt (Consent-Seite,
  Nextcloud-Anmeldung, "Approve access"). Ein zweiter Schalter davor erzeugt die Sackgasse,
  in der die Verbindung gelingt und der erste Tool-Aufruf trotzdem scheitert. Der Schalter
  ist die Notbremse, nicht der Türsteher.
- **D-51:** Die Ablehnung bei ausgeschaltetem Zugriff sagt, was los ist, und nennt den Ort,
  an dem der Nutzer es ändern kann. Sie ist von der Ablehnung eines ungültigen Tokens
  unterscheidbar, denn hier ist der Client in Ordnung und die Entscheidung war eine
  bewusste. Wortlaut gehört ins UI-SPEC.

#### Wie prepare_context relevant findet

- **D-52:** Zwei Wege, nach der Art der Frage. Inhalte kommen über `unified_search`, Termine
  über einen direkten Aufruf mit Zeitfenster. Grund: "diese Woche" beantwortet keine
  Volltextsuche, und ein Bündel ohne die nächsten Termine verfehlt seinen Zweck.
- **D-53:** Kein Direktdraht zu einem Suchindex, auch nicht zu Findling. Alles läuft über
  die Unified Search, damit Nextcloud die einzige Berechtigungsgrenze bleibt. Nebeneffekt,
  der die Entscheidung trägt: Der Provider wird zur Laufzeit gelesen (D-08,
  `tools/search.py`), also liefert ein installiertes Findling automatisch Inhaltstreffer
  bis in gescannte PDFs, ohne eine Zeile Code hier. Siehe BL-01 bis BL-03.

#### Antwortform und Degradation

- **D-54:** Kurz liefert je Treffer Titel, Quelle und die Id, mit der ein Folgetool nachladen
  kann. Voll hängt einen begrenzten Textauszug an. Der Assistent entscheidet selbst, ob er
  nachlädt, und das Token-Budget bleibt vorhersagbar.
- **D-55:** Degradation in derselben Form wie `unified_search` heute: eine Liste der
  ausgefallenen oder abgeschnittenen Quellen mit Name und Grund. Keine neue Form für
  dasselbe Problem, und SC 4 verbietet stille Teil-Ergebnisse.
- **D-56:** Hartes Gesamtbudget, deutlich unter dem Timeout eines üblichen Clients. Was
  nicht rechtzeitig da ist, erscheint unter `degraded`. Kein Budget-Parameter im Schema:
  ein Feld mehr zählt gegen das CI-Token-Budget, und ein Assistent trifft diese Wahl selten
  sinnvoll.

### Claude's Discretion

- Die Zahl der Treffer je Quelle in Kurz und Voll, die konkreten Sekunden des Gesamtbudgets
  und die Aufteilung auf die Teilquellen. Größenordnungen gehören in den Plan, nicht in
  diese Diskussion.
- Ob die Client-Tabelle eine eigene Route bekommt oder unter den bestehenden `/connect`-Pfad
  wächst, und wie die Declarative Settings technisch registriert werden.
- Wortlaut aller Seitentexte, im Rahmen des Tons, den Phase 3 gesetzt hat.

### Deferred Ideas (OUT OF SCOPE)

- **Cursor und private-use URI schemes** (BL-04): zwei getrennte Entscheidungen, ob
  unzulässige `redirect_uris` verworfen statt die ganze Registrierung abgelehnt wird, und ob
  private-use Schemata zugelassen werden. Gehört zu Phase 5 SC 4.
- **Client ID Metadata Documents** (BL-05): der Nachfolger von DCR laut Spec. Zukunftssicherung,
  keine Voraussetzung.
- **WR-08, WR-10, WR-12** (AR-03-06 bis AR-03-08): bewusst zurückgestellt, in
  `03-SECURITY.md` als Restrisiken mit Datum verzeichnet. Vor der Store-Einreichung prüfen.
- **Admin-Sicht auf die Verbindungen aller Nutzer**: kam nicht auf, wäre aber die
  naheliegende Erweiterung. Admin-Belange sind AUTH-07 und gehören nicht hierher.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXAPP-02 | Nutzer kann in den Nextcloud-Settings den MCP-Zugriff aktivieren/deaktivieren, verbundene Clients einsehen und Tokens widerrufen (Per-User-Verwaltung, Declarative Settings) | Abschnitt "Der Declarative-Settings-Kontrakt": Registrierungs-Endpoint, Pull-only-Befund, gemessener Link-only-Fallback; Abschnitt "Architecture Patterns" 1 bis 3: Schalter-Gate in `exapp/middleware.py`, `/connections`-Seite auf `oauth/store.py`, geteilter Widerrufs-Pfad. **Achtung:** der Schalter selbst landet wegen des Pull-only-Befunds auf `/connections`, die Nextcloud-Settings tragen den deklarativen Einstieg (Link). Das ist der im UI-SPEC vorab entschiedene Fallback, siehe "Konsequenz für D-44" |
| TOOL-08 | Gamechanger prepare_context: ein Aufruf bündelt relevante Dateien, Termine, Notizen und Karten zu einer Anfrage token-effizient (mit Kurz/Voll-Parameter) | Abschnitt "Architecture Patterns" 4: Fan-out über `tools/search.py` (alle Provider, D-53) plus `tools/calendar.list_events` mit Zeitfenster, eigene Teil-Budgets unter hartem Gesamtbudget, `degraded` in exakt der Suchen-Form; Token-Budget-Messung: 1858 Bytes Headroom im CI-Gate |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Verbindliche Direktiven aus `./CLAUDE.md`, die der Planer prüfen muss:

| Direktive | Konsequenz für Phase 4 |
|-----------|------------------------|
| Python nur über `uv run --no-sync`, kein `uv sync` | Jede Task-Action, die Python startet, nutzt `uv run --no-sync`. Diese Phase braucht **keine** neue Dependency, also auch keinen Lock-Schritt. |
| Kein Session-State in Tools, multi-worker-fähig (SRV-05) | Der Schalter-Zustand liegt in der SQLite des Stores (WAL), nie im Prozess. Kein Prozess-Cache für den Schalter (D-48). |
| Der MCP darf nie mehr sehen als der angemeldete Nutzer (AUTH-05) | `prepare_context` läuft komplett über die bestehenden User-Credential-Pfade; kein eigener Index, kein Cache über Requests hinweg (T-01-70). |
| Keine destruktiven Writes in v1 | Der Seiten-Widerruf nutzt exakt den bestehenden `/revoke`-Pfad (eigene Store-Zeilen, eigenes App-Passwort). Keine neue Ausnahme nötig, die Permission-Tabelle bleibt wie sie ist. |
| Code und Doku Englisch, `.planning/*` Deutsch, keine Em-Dashes, echte Umlaute | Unverändert. Seitentexte Englisch v1 (UI-SPEC). |
| Gates vor jedem Commit: ruff, pyright, vulture, pytest, Tool-Budget | `scripts/check_tool_budget.py` ist in dieser Phase scharf: aktuell 10642 von 12500 Bytes, das 16. Tool muss in 1858 Bytes passen oder das Budget wird mit neuer Messzeile bewusst angehoben. |
| Konto-Trennung, Repo public | Keine Secrets in Fixtures; der Probe-Lauf dieser Recherche hat nur die Wegwerf-Topologie (Port 8081) angefasst, `nc-mcp-test` und `findling-nextcloud` blieben unberührt. |
| Nach jedem Edit sofort committen, keine Claude-Attribution | Unverändert. |
| Tests: alle Paths (Happy/Fehler/Edge/no_data) | Gilt besonders für den Schalter: ein Test, der ohne die Sperre grün bliebe, ist keiner (CONTEXT, Established Patterns). |

## Summary

Der eine Befund, der diese Phase formt, ist **gemessen und dreifach belegt: Declarative
Settings für ExApps sind pull-only.** AppAPI erzwingt bei der Registrierung
`storage_type: external` (überschreibt jeden anderen Wert), und "external" heißt hier: der
Wert liegt in **AppAPIs eigener Tabelle** (`preferences_ex` für personal,
`appconfig_ex` für admin), nicht in der ExApp. Legt ein Nutzer den Schalter um, läuft die
Kette Settings-UI → `DeclarativeSettingsSetValueEvent` → AppAPI-`SetValueListener` →
DB-Write. **Kein Aufruf erreicht die ExApp**, es gibt keinen Webhook, kein Event und keine
deklarierbare Push-Route. Die ExApp kann den Wert ausschließlich per OCS-Roundtrip abholen,
und genau diesen Roundtrip verbieten D-47 und D-48. Damit greift der im UI-SPEC vorab
entschiedene Fallback: **der echte Schalter zieht auf die `/connections`-Seite** (unser
Store, Wirkung beim nächsten Aufruf, null zusätzliche Roundtrips), und die
Nextcloud-Settings tragen einen **Link-only-Einstieg** als Declarative-Settings-Form ohne
Felder. Dass diese Form registrierbar ist und im persönlichen Security-Abschnitt ankommt,
wurde heute gegen die laufende Phase-3-Topologie gemessen (Kommandos im Abschnitt
"Messprotokoll").

Für die Seite selbst ist alles Nötige da: `oauth/store.py` kennt Authorizations samt
`nc_user` und `revoke_authorization`, der Widerruf inklusive Verifier-Cache-Invalidierung
existiert als erprobte Sequenz im Provider, und `exapp/ui/` liefert die Bauweise. Neu sind
eine Store-Query "Authorizations eines Nutzers", eine Schalter-Tabelle, die Route dreizehn
`^/connections/?$` und der Schalter-Check in `exapp/middleware.py` (beide Identitätszweige,
Reihenfolge: erst Credential, dann Schalter).

`prepare_context` ist Komposition, kein Neubau: `tools/search.py` liefert Fan-out,
Timeout je Provider und die `degraded`-Form wörtlich (D-55), `tools/calendar.list_events`
das Zeitfenster (D-52), `tools/chatgpt.py` das Routing Id → Reader für die Voll-Variante
(D-54). Entscheidend ist, die Providerliste **nicht** einzuschränken, sonst stirbt die
Findling-Synergie aus D-53. Das CI-Token-Budget hat 1858 Bytes Luft; ein Zwei-Parameter-Schema
(`query`, `detail`) passt hinein.

**Primary recommendation:** Schalter und Client-Tabelle auf `/connections` bauen (Route 13,
PUBLIC, Identität aus `AUTHORIZATION-APP-API`), die Declarative-Settings-Form als
Link-only-Wegweiser in `section_type=personal`/`section_id=security` bei `/enabled`
registrieren, und `prepare_context` als paralleles Bündel aus uneingeschränkter
`unified_search` plus Kalender-Zeitfenster unter einem harten 20-Sekunden-Gesamtbudget.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schalter-Zustand (an/aus je Nutzer) | Database/Storage (eigene SQLite, `oauth/store.py`) | — | D-47: unser Store, lokaler Read, kein Nextcloud-Roundtrip |
| Schalter-Durchsetzung (R1) | API/Backend (`exapp/middleware.py`) | — | D-49: die eine Grenze, die beide Anschlussarten passieren |
| Schalter-Bedienung + Client-Tabelle | API/Backend (server-rendered `/connections`, Starlette) | Browser (reines HTML, kein JS) | D-44/D-45: Seiten-Infrastruktur aus Phase 3, zero JavaScript |
| Einstieg in den Nextcloud-Settings | Nextcloud (Declarative Settings, von NC gerendert) | API/Backend (OCS-Registrierung bei `/enabled`) | D-44: auffindbar, wo NC seine App-Schalter zeigt; Pixel gehören NC |
| Widerruf je Zeile | API/Backend (Provider-Widerrufssequenz) | Database/Storage | SC 2; dieselbe Sequenz wie `/revoke`, ein Codepfad statt zwei |
| prepare_context Fan-out | API/Backend (`tools/context.py`) | Nextcloud (Unified Search, CalDAV) | D-52/D-53: Nextcloud bleibt die einzige Berechtigungsgrenze |
| prepare_context Voll-Auszüge | API/Backend (bestehende Reader via Id-Codec) | Nextcloud (WebDAV/Notes/Deck) | D-54: nachladen über dieselben Pfade wie `fetch` |

## Standard Stack

### Core

Diese Phase führt **keine neue Laufzeit-Abhängigkeit** ein. Alles Nötige ist im Projekt.

| Library | Version (installiert) | Purpose | Why Standard |
|---------|----------------------|---------|--------------|
| mcp | 2.0.x | Tool-Registrierung für `prepare_context` (`@mcp.tool`), In-Memory-`Client` für Budget-Messung | Bestehender Kern; `server/reg_*`-Muster ist etabliert [VERIFIED: src/mcp_connector/server/reg_search.py] |
| starlette (transitiv) | via mcp | Route dreizehn `/connections`, R1-Response in der Middleware | Bestehende Seiten-Infrastruktur (D-45) [VERIFIED: exapp/ui/connect.py, consent.py] |
| httpx | 0.28.1 | Ausgehende OCS-Registrierung der Settings-Form (`shared_client` + `appapi_auth_headers`) | Exakt das Muster von `exapp/status.py` (Init-Progress-Push) [VERIFIED: src/mcp_connector/exapp/status.py] |
| sqlite3 (stdlib) | 3.13 | Schalter-Tabelle und User-Query im bestehenden Store | `oauth/store.py` hat Schema, WAL, Migrationsmuster (`_add_missing_columns`) [VERIFIED: src/mcp_connector/oauth/store.py] |
| asyncio (stdlib) | 3.13 | Paralleles Bündel mit Timeout je Teilquelle | `tools/search.py` und `tools/calendar.py` machen es vor [VERIFIED: beide Dateien] |

### Supporting

Keine neuen Werkzeuge. Die Messwerkzeuge (`scripts/check_tool_budget.py`,
Wegwerf-Topologie `compose.exapp.yml`) existieren und liefen in dieser Recherche.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Eigene OCS-Registrierung (~40 Zeilen) | `nc_py_api[app]` (`nc.ui.settings.register`) | Bringt FastAPI/niquests/Session-Layer mit; per D-24 in Phase 2 abgelehnt und hier erst recht unnötig: der eine Call ist `POST .../ui/settings` mit `{"formScheme": ...}` [VERIFIED: nc_py_api ex_app/ui/settings.py macht exakt das]. **Nicht nehmen.** |
| Schalter auf `/connections` (unser Store) | Declarative-Checkbox + OCS-Read je Request | Verletzt D-47 (zweiter Nextcloud-Roundtrip je MCP-Aufruf). **Verboten.** |
| Schalter auf `/connections` | Declarative-Checkbox + Poll auf `preferences_ex` | Verletzt D-48 (Wirkung erst nach Poll-Intervall) und ist laut D-47 die schlechteste Antwort. **Verboten.** |
| Schalter auf `/connections` | Declarative-Checkbox + Webhook (`webhook_listeners`) | Geht nicht: `DeclarativeSettingsSetValueEvent extends Event` und implementiert `IWebhookCompatibleEvent` **nicht**; Zustellung liefe zudem über Background-Jobs (Cron), was D-48 bricht [VERIFIED: nextcloud/server stable34, lib/public/Settings/Events/DeclarativeSettingsSetValueEvent.php] |

**Installation:** keine. `uv.lock` unverändert.

## Package Legitimacy Audit

Diese Phase installiert **keine** neuen Pakete. slopcheck ist gegenstandslos.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| — | — | — | — | — | — | keine Installation in dieser Phase |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Der Declarative-Settings-Kontrakt (AppAPI 34, gemessen 2026-08-17)

Dieser Abschnitt beantwortet die vier Recherche-Fragen des Orchestrators und die Open
Questions 1 und 2 des UI-SPEC.

### Frage 1: Was ruft Nextcloud auf der ExApp auf, wenn der Nutzer den Wert umlegt?

**Nichts.** Die vollständige Kette, aus dem Quellcode:

1. Die Settings-UI postet an `POST /ocs/v2.php/settings/api/declarative/value`
   [VERIFIED: nextcloud/server stable34, apps/settings/appinfo/routes.php Zeile 57, `'root' => ''`].
2. `DeclarativeManager::setValue` sieht `storage_type: external` und dispatcht
   `DeclarativeSettingsSetValueEvent` [VERIFIED: lib/private/Settings/DeclarativeManager.php].
3. AppAPIs `SetValueListener` fängt das Event und schreibt den Wert für personal-Formulare
   via `ExAppPreferenceService::setUserConfigValue` in die Tabelle `preferences_ex`
   [VERIFIED: nextcloud/app_api v34.0.3, lib/Listener/DeclarativeSettings/SetValueListener.php,
   vollständig gelesen: die Methode endet mit dem DB-Write, kein HTTP-Call, kein Event].
4. Lesen läuft analog: `GetValueListener` liest `preferences_ex`, fällt auf den
   Schema-`default` zurück. Auch hier kein Kontakt zur ExApp.

Der offizielle Doku-Satz dazu: *"When an admin or user changes some ExApp settings, they
will be stored in the database and can be retrieved using Preferences or AppConfig API"*
[CITED: docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/settings.html].
Drittes Indiz: `nc_py_api` führt im `SettingsField` ein Attribut
`notify = False  # to be supported in future` [VERIFIED: cloud-py-api/nc_py_api,
nc_py_api/ex_app/ui/settings.py]. Eine Änderungs-Benachrichtigung an die ExApp ist ein
**zukünftiges** Feature, kein vorhandenes.

**Konsequenzen:**
- Es gibt **keine Route vierzehn**. Die ExApp deklariert für Declarative Settings keine
  einzige eingehende Route; die Registrierung ist ein ausgehender OCS-Call. (Antwort auf
  UI-SPEC Open Question 1.)
- Initial-Sync/aktuellen Wert lesen ginge nur per
  `POST /ocs/v2.php/apps/app_api/api/v1/ex-app/preference/get-values` mit User-Kontext
  [VERIFIED: app_api v34.0.3 appinfo/routes.php Zeile 97] und ist ein Roundtrip je Nutzer,
  also genau das, was D-47 an der Bearer-Grenze verbietet.
- Der UI-SPEC formuliert seinen Fallback als "falls `external` nicht unterstützt wird".
  Präziser Befund: `external` ist der **einzige** Modus (AppAPI überschreibt bei der
  Registrierung hart: `$formScheme['storage_type'] = 'external';`
  [VERIFIED: app_api v34.0.3, lib/Service/UI/SettingsService.php Zeile 40]), aber die
  Push-Semantik, die das UI-SPEC dahinter annahm, existiert nicht. Die
  Fallback-**Bedingung** ist damit dem Sinn nach erfüllt, und der Fallback greift.

### Frage 2: Wie wird die Form registriert, wann, und wie wieder entfernt?

| Aspekt | Antwort | Beleg |
|--------|---------|-------|
| Endpoint | `POST /ocs/v2.php/apps/app_api/api/v1/ui/settings`, JSON-Body `{"formScheme": {...}}`, AppAPI-Auth-Header im App-Kontext (leerer User) | [VERIFIED: app_api v34.0.3 routes.php Zeile 143, OCSSettingsController; gemessen: 200 OK, siehe Messprotokoll] |
| Entfernen | `DELETE` auf dieselbe URL mit `{"formId": "..."}` | [VERIFIED: routes.php Zeile 144; gemessen: 200 OK] |
| Nachschauen | `GET` mit `formId` | [VERIFIED: routes.php Zeile 145] |
| Idempotenz | Ja: `SettingsService::registerForm` macht `insertOrUpdate` auf `(appid, formid)` | [VERIFIED: SettingsService.php] |
| Wann registrieren | Im `/enabled`-Handler bei `enabled=1` (`exapp/lifecycle.py`). Kein Entregistrieren bei `enabled=0` nötig: `getRegisteredForms` liefert nur Formulare **enabled** ExApps (`findAllEnabled`), eine deaktivierte App verschwindet also von selbst aus den Settings | [VERIFIED: SettingsService.php `findAllEnabled`] |
| App-Entfernung | AppAPI räumt selbst auf: `ExAppService::unregisterExApp` ruft `settingsService->unregisterExAppForms($appId)` | [VERIFIED: app_api v34.0.3, lib/Service/ExAppService.php Zeile 120] |
| Schema-Validierung | Core validiert beim Laden der Settings-Seite (`registerSchema` → `validateSchema`): Pflicht sind `id`, `section_type` (admin/personal), `section_id`, `storage_type`, `title`, `fields` (Array). **Ein leeres `fields: []` besteht die Validierung** (nur fehlend/kein Array schlägt fehl). Felder brauchen `id`, `title`, `type` aus der festen Typliste | [VERIFIED: DeclarativeManager.php validateSchema, stable34] |

Der Phase-2-Befund ("eine reine OCS-Registrierung", `02-RESEARCH.md` ~Zeile 107) ist damit
bestätigt und konkretisiert.

### Frage 3: Ist `section_id: security` für eine ExApp-Form adressierbar?

**Ja, gemessen.** Die persönliche Security-Sektion hat die Id `security`
[VERIFIED: nextcloud/server stable34, apps/settings/lib/Sections/Personal/Security.php],
das Matching in `DeclarativeManager::getFormIDs` ist ein reiner String-Vergleich, und die
Settings-Navigation zeigt eine Sektion schon dann, wenn sie deklarative Formulare enthält
[VERIFIED: apps/settings/lib/Controller/CommonSettingsTrait.php Zeile 68 bis 72]. Der
Probe-Lauf (unten) hat die Form mit `section_id: security` registriert und im HTML von
`/settings/user/security` wiedergefunden. `SETTINGS_PLACE` = "Settings, Security,
MCP Connector" hält. (Antwort auf UI-SPEC Open Question 2.)

### Frage 4: Wird `external` für ExApp-Formen unterstützt, seit wann?

`external` ist seit der Einführung der ExApp-Declarative-Settings (AppAPI 2024, Listener
tragen den 2024er Copyright-Header) der erzwungene und einzige Modus. Die Frage "seit
welcher AppAPI-Version" ist damit gegenstandslos: auf NC 34 / AppAPI 34.0.3 (Zieltopologie)
ist es der Ist-Zustand, an v34.0.3-Tag und main identisch verifiziert.

### Messprotokoll (2026-08-17, laufende Phase-3-Topologie, Port 8081)

Alle Kommandos reproduzierbar; die Owner-Instanzen `nc-mcp-test` und `findling-nextcloud`
wurden nicht angefasst, der Probe-Eintrag wurde wieder entfernt.

```text
1. Registrierung aus dem ExApp-Container (docker exec nc_app_mcp_connector, python/urllib):
   POST http://caddy/ocs/v2.php/apps/app_api/api/v1/ui/settings
   Body: {"formScheme": {"id":"probe_link_only","priority":10,"section_type":"personal",
          "section_id":"security","title":"MCP Connector (probe)","description":"...",
          "doc_url":"http://127.0.0.1:8081/exapps/mcp_connector/connections","fields":[]}}
   Header: AA-VERSION/EX-APP-ID/EX-APP-VERSION/AUTHORIZATION-APP-API (App-Kontext, leerer User)
   -> 200, {"ocs":{"meta":{"status":"ok",...}}}

2. curl -u admin:... http://127.0.0.1:8081/ocs/v2.php/settings/api/declarative/forms
   -> Form erscheint mit "storage_type":"external" (von AppAPI erzwungen), "fields":[],
      "section_id":"security", "app":"mcp_connector"

3. curl -u admin:... http://127.0.0.1:8081/settings/user/security | grep probe_link_only
   -> Treffer: die Form wird in den Initial-State der persönlichen Security-Seite geliefert

4. DELETE mit {"formId":"probe_link_only"} -> 200; forms-Endpoint danach ohne Probe
```

Einzige Restunsicherheit: Schritt 3 belegt die Datenlieferung an die Seite, nicht den
gerenderten Pixel (kein Browser im Messlauf). Der Vue-Renderer zeichnet Titel, Beschreibung
und Doc-Icon unabhängig von den Feldern; das Risiko, dass eine feldlose Form unsichtbar
bleibt, ist klein, aber im Plan mit einem Browser-Blick zu schließen (Assumptions Log A1).

### Konsequenz für D-44: der entschiedene Fallback greift

| Variante | D-47 (kein 2. Roundtrip) | D-48 (nächster Aufruf) | Urteil |
|----------|--------------------------|------------------------|--------|
| Declarative-Checkbox, Wert je Request per OCS lesen | verletzt | erfüllt | verboten |
| Declarative-Checkbox plus Poll auf `preferences_ex` | erfüllt | verletzt | verboten (und laut D-47 die schlechteste Antwort) |
| Declarative-Checkbox plus Webhook | Push existiert nicht (Event nicht webhook-kompatibel, Zustellung via Cron) | verletzt | technisch unmöglich |
| **Schalter auf `/connections` (unser Store), Settings-Eintrag als Link-only-Form** | **erfüllt (lokaler SQLite-Read)** | **erfüllt (Read je Request, kein Cache)** | **die Empfehlung** |

Das UI-SPEC hat genau diesen Fallback als Design vorentschieden ("the on/off control moves
onto /connections next to the list, and Nextcloud's settings section keeps only the link";
D-44 ist die Präferenz, D-47/D-48 sind die gemessenen Constraints, der Constraint gewinnt).
Folgen für den Plan, alle im UI-SPEC bereits angelegt:

1. `/connections` bekommt zusätzlich zum Zeilen-Widerruf den Schalter (POST-Aktion, HMAC,
   dieselbe Anti-Forgery wie der Rest der Seite).
2. Die Declarative-Form wird als **Wegweiser** registriert: `title`, `description` (nennt
   die `/connections`-Adresse als Text), `doc_url` (der eine Link, den eine
   Declarative-Section rendern kann), `fields: []`. Gemessen registrierbar und ausgeliefert.
3. Jede Copy, die den Ort nennt (`SETTINGS_PLACE`, `CONNECTIONS_PAUSED_BODY`,
   `ACCESS_DISABLED_DESCRIPTION`), muss auf den neuen Ort zeigen: der Schalter liegt jetzt
   auf der Connections-Seite, der Settings-Eintrag ist der Wegweiser dorthin. Das UI-SPEC
   hat dafür die Ein-Konstanten-Regel (`SETTINGS_PLACE`) gebaut; der Plan passt den
   Wortlaut einmal dort an.
4. **EXAPP-02-Wortlaut:** Das Requirement sagt "in den Nextcloud-Settings ...
   aktivieren/deaktivieren". Mit dem Fallback ist der Schalter einen Klick hinter dem
   Settings-Eintrag. CONTEXT und UI-SPEC autorisieren das ausdrücklich; der Plan sollte den
   Punkt trotzdem im VERIFICATION-Dokument benennen, damit `verify-work` nicht über den
   Wortlaut stolpert (Open Question 2).

## Architecture Patterns

### System Architecture Diagram

```text
Schalter-Pfad (EXAPP-02)

  Nutzer-Browser
      |
      |  GET/POST /connections (Route 13, PUBLIC)         Nextcloud personal settings
      v                                                       "Security"-Sektion
  HaRP: signiert AUTHORIZATION-APP-API                              |
      |  (User-Id der Browser-Session, leer wenn anonym)            |  Link-only-Form
      v                                                             |  (title/descr./doc_url)
  exapp/ui/connections.py --------- doc_url / Beschreibung <--------+
      |  Identitaet = appapi_user(); leer -> E8 (403)
      |  action=pause|resume  -> store.set_access(nc_user, ...)
      |  action=confirm|disconnect -> Ownership-Check, dann
      |                              provider.end_connection(auth_id)
      v                                            (revoke_family + revoke_authorization
  oauth/store.py (SQLite, WAL)                      + note_cleanup + verifier.invalidate)
      user_access(nc_user, disabled_at)
      authorizations(nc_user, ...)
      ^
      |  lokaler Read je Request (kein NC-Roundtrip, kein Cache)
      |
  MCP-Client --> /mcp --> RequireAppApi (exapp/middleware.py)
      1. AppAPI-Handshake pruefen (unveraendert)
      2. Identitaet: User-Id aus Header ODER Bearer -> Token-Verifier -> Identity
      3. NEU: access_disabled(nc_user)? -> R1: 403 {"error":"access_disabled",...},
         kein WWW-Authenticate, no-store
      4. sonst: MCP-App

prepare_context (TOOL-08)

  MCP-Client --> tools/call prepare_context(query, detail)
      |
      v
  tools/context.py  (hartes Gesamtbudget ~20 s)
      |-- parallel --> tools/search.unified_search(query, ALLE Provider)   [<= 15 s je Provider]
      |                  -> Treffer nach kind gebuendelt (file/note/card/url)
      |-- parallel --> tools/calendar.list_events(jetzt .. jetzt+7d)       [eigener Cap ~10 s]
      |
      |-- detail=full: zweite Welle, Top-K aufloesbare Treffer
      |                ueber die fetch-Reader (files_read/notes/deck), Byte-Cap je Auszug
      v
  Antwort: {query, window, events[], results[], degraded[], note}
      degraded[] in EXAKT der Form von unified_search: {"provider"|"source", "reason"}
```

### Recommended Project Structure

```text
src/mcp_connector/
├── exapp/
│   ├── middleware.py        # + Schalter-Gate (R1), beide Identitätszweige
│   ├── lifecycle.py         # /enabled=1 registriert die Settings-Form (fire-and-forget wie /init)
│   ├── settings_form.py     # NEU: formScheme-Konstante + OCS-Register-Call (Muster: status.py)
│   └── ui/
│       ├── connections.py   # NEU: S5-S8, Schalter-Aktion, eigene Pfad-/Feld-Konstanten
│       ├── strings.py       # + Konstanten aus dem UI-SPEC (SETTINGS_PLACE angepasst)
│       ├── layout.py        # + row_list() Primitive, 3 neue CSS-Regeln
│       └── errors.py        # + E8
├── oauth/
│   ├── store.py             # + user_access-Tabelle, authorizations_of_user(), set_access(), access_disabled()
│   └── provider.py          # + end_connection(auth_id) als öffentlicher Wrapper der bestehenden Sequenz
├── tools/
│   └── context.py           # NEU: prepare_context-Logik
├── server/
│   └── reg_context.py       # NEU: Registrierung, Schema-Diät (2 Parameter)
└── entry_exapp.py           # verdrahtet connections_routes(store, end_connection) und Middleware-Gate
appinfo/info.xml             # Route 13: ^/connections/?$ GET,POST PUBLIC (+ Begründungskommentar)
```

### Pattern 1: Das Schalter-Gate in der Transportgrenze

**What:** `RequireAppApi` bekommt einen Store-Zugriff und prüft nach erfolgreicher
Identitätsfeststellung, ob der Zugriff des Nutzers gesperrt ist. Beide Zweige (AUTH-01:
User-Id im Header; OAuth: Identity aus dem Verifier) münden in denselben Check.
**When to use:** Genau einmal, in `exapp/middleware.py`. Kein zweiter Prüfpunkt in den
Tools (zwei Quellen für eine Entscheidung driften).
**Reihenfolge ist Sicherheit:** Erst Handshake, dann Credential/Token, **dann** Schalter.
Ein R1 vor der Credential-Prüfung würde einem anonymen Aufrufer verraten, ob ein Konto den
Zugriff pausiert hat (User-Enumeration). Ein ungültiger Token bleibt 401 (R2), auch wenn
der Zugriff pausiert ist.

```python
# Skizze; Quelle: eigene Ableitung aus exapp/middleware.py (Phase 3) + UI-SPEC R1
# In RequireAppApi.__call__, nach require_appapi und nach der Bearer-Prüfung:
nc_user = user or getattr(request.state, OAUTH_STATE_ATTR).nc_user
if nc_user and await self._access_disabled(nc_user):   # lokaler SQLite-Read, ~µs
    response = Response(
        content=ACCESS_DISABLED_BODY,        # konstanter JSON-String aus strings.py
        status_code=403,                     # kein WWW-Authenticate (UI-SPEC R1)
        media_type="application/json",
        headers=NO_STORE,
    )
    await response(scope, receive, send)
    return
```

D-47-Bilanz: der Read ist SQLite im eigenen Container, kein Nextcloud-Roundtrip. SC 5
(1 Roundtrip je MCP-Aufruf) bleibt exakt, und der Plan sollte das mit dem bestehenden
`--measure`-Weg von `scripts/oauth_flow_check.py` nachmessen.

### Pattern 2: Link-only-Form bei `/enabled` registrieren

**What:** Bei `enabled=1` schickt die ExApp die Form-Registrierung als Fire-and-forget-OCS-Call
(Fehler loggen, nie 500 aus `/enabled`, dasselbe Fehlermodell wie der Init-Progress-Push).
**Example (gemessen, siehe Messprotokoll):**

```python
# Quelle: gemessener Probe-Lauf 2026-08-17 + exapp/status.py (Header-Bauweise)
FORM_SCHEME = {
    "id": "mcp_connector_settings",
    "priority": 10,
    "section_type": "personal",
    "section_id": "security",
    "title": SETTINGS_TITLE,          # "MCP Connector"
    "description": SETTINGS_DESCRIPTION,  # nennt die /connections-URL als Text
    "doc_url": f"{public_url}/connections",
    "fields": [],                     # Link-only: besteht die Core-Validierung (gemessen)
}
# POST {base}/ocs/v2.php/apps/app_api/api/v1/ui/settings
# json={"formScheme": FORM_SCHEME}, Header: appapi_auth_headers("", ...) + OCS_HEADERS
```

Idempotent (insertOrUpdate), Deaktivierung blendet automatisch aus, Deinstallation räumt
AppAPI-seitig auf. `doc_url` braucht die **öffentliche** URL (`NC_MCP_PUBLIC_URL`), nie den
internen Hostnamen.

### Pattern 3: Die Connections-Seite als eine Route mit Aktionsfeld

**What:** `^/connections/?$` GET (Liste) und POST (confirm/disconnect/pause/resume über ein
Aktionsfeld), exakt wie `/connect` start/cancel handhabt. PUBLIC mit Identitäts-Check in
der App (`appapi_user`), Ownership-Check `is_user(row.nc_user, resolved)`, HMAC über den
Connection-Handle mit dem vorhandenen `form_token`-Primitive des Stores.
**When to use:** Der komplette EXAPP-02-Browser-Teil. Das UI-SPEC ist der bindende
Design-Vertrag (S5 bis S8, E8, R1); diese Recherche fügt nur die Schalter-Aktion hinzu,
die der Fallback auf die Seite holt, und deren Copy-Anpassung.
**Store-Ergänzungen:** `authorizations_of_user(nc_user)` (neu, Index auf `nc_user`
erwägen), `user_access`-Tabelle (`nc_user TEXT PRIMARY KEY, disabled_at INTEGER NOT NULL`;
kein Eintrag = an, D-50 kostenlos erfüllt).

### Pattern 4: prepare_context als Fan-out über zwei fertige Fan-outs

**What:** `tools/context.py` startet parallel (a) `unified_search` **ohne
Provider-Einschränkung** und (b) `calendar.list_events` mit berechnetem Fenster, jede
Teilquelle in einem eigenen `asyncio.timeout`. Ergebnisse werden gebündelt, Ausfälle in
**derselben** `degraded`-Form gemeldet, die `_reason()` in `tools/search.py` produziert.
**Warum keine Providerliste:** `providers="files,notes,search-deck-card-board"` würde ein
installiertes Findling (und jeden künftigen Provider) aussperren und D-53s tragenden
Nebeneffekt zerstören. Stattdessen alle Provider fragen und die Treffer nach `kind`
bündeln (`file`/`note`/`card` aus `provider_map.PROVIDER_KINDS`, alles andere unter
`other` mit `resolvable: false`).
**Größenordnungen (Claude's Discretion, als Empfehlung):**

| Stellgröße | Empfehlung | Grund |
|-----------|------------|-------|
| Gesamtbudget | 20 s Wall-Clock | Teilquellen laufen parallel, das Maximum der Teil-Budgets bestimmt die Wand; 20 s liegt deutlich unter den 30 bis 60 s, die übliche MCP-Clients einem Tool-Call geben [ASSUMED: Tool-Call-Timeouts der Clients sind nicht offiziell dokumentiert; Phase 3 hat nur die OAuth-Timeouts zitiert] |
| Suche | bestehende 15 s je Provider unverändert | erprobt, parallel, unter 20 s |
| Kalender | eigener Cap **10 s** innerhalb von prepare_context | `PER_CALENDAR_TIMEOUT` ist 20 s und würde allein das Gesamtbudget füllen; der engere Cap gehört in den prepare_context-Aufruf, nicht in `calendar.py` |
| Zeitfenster | jetzt bis jetzt+7 Tage, UTC | "diese Woche" ohne Schema-Feld; im Antwort-`window` benannt, damit das Modell das Fenster kennt |
| Treffer je Quelle (Kurz) | 5 je kind-Bucket, Events max. 10 | Token-Vorhersagbarkeit (D-54) |
| Voll-Auszüge | Top 3 auflösbare Treffer, je max. 2000 Bytes, parallel, je 5 s Cap, Rest-Budget respektieren | Nachladen über die vorhandenen Reader (`ids`-Codec + Routing wie `tools/chatgpt.fetch`); ein gescheiterter Auszug wird zum `degraded`-Eintrag, der Treffer bleibt in Kurzform |
| `detail`-Parameter | String-Enum `"short"`/`"full"`, Default `"short"` | zwei Parameter gesamt (query, detail); geschätzt 600 bis 800 Schema-Bytes, passt in die 1858 Bytes Headroom (Messung 2026-08-17: 10642 von 12500) |

**Kein globales `asyncio.timeout` um das ganze Bündel:** ein globaler Abbruch verwirft die
schon fertigen Teilantworten. Stattdessen je Teilquelle ein Timeout; das Gesamtbudget ist
dann das Maximum, nicht die Summe.

### Pattern 5: Ein Widerrufs-Pfad für Protokoll und Seite

**What:** Der Zeilen-Widerruf der Seite ruft dieselbe Sequenz wie `/revoke`:
`revoke_family` (alle Familien der Authorization), `revoke_authorization`, `note_cleanup`,
Held-Answers leeren, `verifier.invalidate()`. Der Provider hat diese Sequenz bereits als
private Methode [VERIFIED: oauth/provider.py ~Zeile 740]; der Plan hebt sie als
`end_connection(auth_id)` an die Oberfläche und verdrahtet sie in `entry_exapp` an die
Connections-Routen.
**Warum:** Ohne `verifier.invalidate()` lebt ein widerrufener Token bis zu 5 Sekunden im
Prozess-Cache weiter (T-03-62); die Seite darf diese Lücke nicht neu aufreißen. Zwei
Implementierungen desselben Widerrufs sind die Drift, die das Projekt überall sonst
verbietet.

### Anti-Patterns to Avoid

- **Poll auf `preferences_ex`:** verletzt D-48, von D-47 als schlechteste Antwort benannt.
- **Provider-Einschränkung in prepare_context:** zerstört die Findling-Synergie (D-53).
- **Prozess-Cache für den Schalter:** genau der Zwischenspeicher, den D-48 verbietet. Der
  SQLite-Read je Request ist billig genug.
- **Zweite Quelle für den R1-Satz:** die Ablehnung entsteht ausschließlich in
  `exapp/middleware.py`; kein Tool-Level-Duplikat (UI-SPEC).
- **`preferences_ex` als Wahrheit für den Schalter:** dann zeigte die NC-Checkbox einen
  Zustand, den die Grenze nicht durchsetzt. Eine sichtbare Checkbox, die nichts schaltet,
  ist schlimmer als keine; deshalb Link-only-Form ohne Feld.
- **`GET` mit Nebenwirkung auf `/connections`:** T-03-35 gilt; Widerruf und Schalter nur
  über POST mit HMAC.
- **`access_level USER` für Route 13:** die gemessene HaRP-Blacklist (10 Refusals in 300 s
  sperren die ganze ExApp mit 502) trifft eine Settings-Seite mit abgelaufenen Sessions im
  Normalbetrieb. PUBLIC mit In-App-Identitätsprüfung, wie `/authorize/decide` (CR-01).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anti-Forgery des Disconnect-Formulars | eigenes CSRF-Token-System | `store.form_token`-HMAC-Primitive (CONFIRM_PARAM-Muster, T-03-50) | überlebt Neustart und zweiten Worker, keine Migration |
| Degradations-Form | neues Fehlerformat | `degraded`-Liste + `_reason()` aus `tools/search.py` | D-55 verlangt wörtlich dieselbe Form |
| Auszug-Nachladen (Voll) | eigener Content-Reader | `ids`-Codec + Routing-Muster aus `tools/chatgpt.py` (files_read/notes/deck-Reader) | Prefix-Disziplin, SSRF-Grenze und Byte-Caps existieren dort geprüft (T-01-75, T-01-79) |
| OCS-Call zur Form-Registrierung | eigener HTTP-Stack oder nc_py_api | `shared_client()` + `appapi_auth_headers()` + `OCS_HEADERS` wie `exapp/status.py` | ein erprobtes Muster, null neue Dependency (D-24) |
| Widerruf je Zeile | eigene Revocation-Logik | Provider-Sequenz als `end_connection(auth_id)` | Verifier-Cache-Invalidierung und Reihenfolge der drei Writes sind dort schon richtig |
| Seiten-HTML | Template-Engine | `exapp/ui/layout.py` + neue `row_list`-Primitive | D-45; Escaping am einen Punkt |
| Recurrence im Kalenderfenster | RRULE-Expansion | bestehendes `calendar.list_events` | icalendar/recurring-ical-events stecken schon dahinter |

**Key insight:** Diese Phase ist fast vollständig Komposition vorhandener, geprüfter Teile.
Der einzige echte Neubau ist die Schalter-Tabelle plus Gate, und der ist bewusst winzig.

## Common Pitfalls

### Pitfall 1: Die Declarative-Checkbox "funktioniert" scheinbar trotzdem
**What goes wrong:** Ein Plan registriert doch eine Checkbox, sie rendert, speichert und
liest sauber, alle Settings-Tests grün. Nur die Bearer-Grenze erfährt nie davon.
**Why it happens:** AppAPI beantwortet Get/Set selbst aus `preferences_ex`; der Rundlauf im
Settings-UI beweist nichts über die ExApp.
**How to avoid:** Der Wächter-Test der Phase ist ein End-to-End: Wert umlegen (auf der
Seite), nächster `tools/call` muss R1 sein. Ein Test, der nur den Settings-Roundtrip
prüft, wäre ohne die Sperre grün und damit per Projektregel keiner.
**Warning signs:** Ein `fields`-Eintrag mit `type: checkbox` im formScheme dieser App.

### Pitfall 2: R1 vor der Credential-Prüfung
**What goes wrong:** Ein anonymer oder falsch authentifizierter Aufrufer bekommt 403
`access_disabled` und lernt damit, dass das Konto existiert und pausiert hat.
**How to avoid:** Reihenfolge im Gate: Handshake → Token/Identität → Schalter. R2/R3
bleiben exakt wie in Phase 3.
**Warning signs:** Ein Test "invalid token + pausierter Nutzer" erwartet 403 statt 401.

### Pitfall 3: Seiten-Widerruf ohne Verifier-Invalidierung
**What goes wrong:** Der widerrufene Token arbeitet bis zu 5 Sekunden weiter
(Prozess-Cache, T-03-62), und bei mehreren Workern je Prozess einmal.
**How to avoid:** `end_connection` als geteilter Pfad (Pattern 5), nie `revoke_authorization`
direkt aus dem UI-Code.
**Warning signs:** `store.revoke_authorization` wird aus `exapp/ui/connections.py` importiert.

### Pitfall 4: Globales Timeout verschluckt fertige Teilantworten
**What goes wrong:** `asyncio.timeout(20)` um das ganze Bündel bricht bei einer lahmen
Quelle alles ab; die Antwort ist leer statt degradiert, SC 4 verletzt.
**How to avoid:** Timeout je Teilquelle, `gather(return_exceptions=True)`, Ausfälle in
`degraded` (das Muster steht in `tools/search.py` Zeile 89 bis 106).

### Pitfall 5: Der Kalender-Cap frisst das Gesamtbudget
**What goes wrong:** `PER_CALENDAR_TIMEOUT = 20.0` in `calendar.py`: eine hängende
Kalender-Collection hält prepare_context genau bis zur Budgetgrenze.
**How to avoid:** prepare_context wickelt den `list_events`-Aufruf in einen eigenen,
engeren `asyncio.timeout` (~10 s) und meldet den Ausfall als `{"source": "calendar",
"reason": ...}`. `calendar.py` selbst bleibt unverändert (das Standalone-Tool darf weiter
20 s haben).

### Pitfall 6: Das Tool-Budget-Gate reißt unbemerkt
**What goes wrong:** Ein wohlmeinend ausführliches Schema (Beschreibungssätze, ein dritter
Parameter) schiebt `tools/list` über 12500 Bytes, CI rot.
**How to avoid:** Vor jedem Commit `uv run --no-sync python scripts/check_tool_budget.py`.
Messstand 2026-08-17: 10642 Bytes, 15 Tools, 1858 Bytes frei. Zwei Parameter, knappe
Description, `structured_output=False` wie `unified_search`. Muss das Budget doch steigen,
verlangt der Kommentar im Skript eine neue Messzeile als bewusste Entscheidung.

### Pitfall 7: Route 13 ohne Endanker oder mit falschen Verben
**What goes wrong:** HaRP matcht mit `re.match` (nur Startanker); `^/connections` ohne `$`
publiziert auch `/connections.evil`. Ein fehlendes POST macht den Widerruf toter Knopf,
ein zusätzliches DELETE wäre unbegründete Angriffsfläche.
**How to avoid:** `^/connections/?$`, `GET,POST`, PUBLIC, `headers_to_exclude` wie die
anderen zwölf, plus Begründungskommentar im Manifest (Pflichtmuster seit AR-02-06).

### Pitfall 8: PHP-Proxy cacht die Seite eines benannten Kontos
**What goes wrong:** Ohne `Cache-Control: no-store` hält der AppAPI-PHP-Proxy JSON und
Seiten 3600 s (Phase-2-Pitfall 4); die Client-Liste eines Nutzers erscheint einem anderen.
**How to avoid:** `layout.page` setzt die fünf Header zentral; R1 trägt `no-store` explizit.
Test darauf, nicht Hoffnung.

### Pitfall 9: Deck heißt im Provider-Katalog nicht "deck"
**What goes wrong:** Wer Treffer nach Provider-Id `deck` bündelt, bekommt nie eine Karte.
**How to avoid:** `provider_map.PROVIDER_KINDS` nutzen: die Deck-Provider-Id ist
`search-deck-card-board`, das `kind` ist `card` [VERIFIED: provider_map.py Zeile 40,
gegen nextcloud/deck verifiziert in Phase 1]. Bündeln nach `kind`, nicht nach Provider-Id.

### Pitfall 10: Der App-Kontext (leere User-Id) trifft das Schalter-Gate
**What goes wrong:** Interne Aufrufe ohne Nutzer (App-Kontext) dürfen nicht am Schalter
scheitern oder ihn umgehen; `is_user` akzeptiert leer nie, aber das Gate muss die leere
Identität sauber am OAuth-Zweig vorbeigeben (dort entscheidet weiter der Bearer).
**How to avoid:** Gate nur bei nicht-leerer, aufgelöster Nutzer-Identität prüfen; die
bestehenden Zweig-Tests von `RequireAppApi` um die vier Kombinationen (User/OAuth x an/aus)
erweitern.

### Pitfall 11: Die Form-Registrierung macht `/enabled` kaputt
**What goes wrong:** Ein 500 aus `/enabled` bricht das Aktivieren der App; ein synchroner
OCS-Call, der hängt, läuft in AppAPIs Timeout.
**How to avoid:** Dasselbe Fehlermodell wie `report_init_progress`: ein Versuch, Fehler
loggen, `/enabled` antwortet trotzdem `{"error": ""}`. Bei fehlgeschlagener Registrierung
fehlt nur der Settings-Wegweiser, die App funktioniert; ein Log-Eintrag reicht als Signal.

## Code Examples

### 1. Gemessene Form-Registrierung (OCS, App-Kontext)

```python
# Source: Messprotokoll 2026-08-17 gegen app_api v34.0.3 (Topologie compose.exapp.yml)
# Header-Bauweise: src/mcp_connector/nextcloud/credentials.py appapi_auth_headers
url = f"{settings.base_url}/ocs/v2.php/apps/app_api/api/v1/ui/settings"
headers = {**OCS_HEADERS, **appapi_auth_headers("", app_id=..., app_version=...,
                                                aa_version=..., app_secret=...)}
await client.post(url, json={"formScheme": FORM_SCHEME}, headers=headers)   # 200 = ok
# DELETE mit json={"formId": FORM_SCHEME["id"]} entfernt sie wieder (200/404)
```

### 2. R1, die Ablehnung bei pausiertem Zugriff (UI-SPEC-Vertrag)

```python
# Source: 04-UI-SPEC.md Refusal Contract; Konstante ohne Platzhalter (T-03-66)
# HTTP 403, KEIN WWW-Authenticate, Cache-Control: no-store
ACCESS_DISABLED_BODY = (
    '{"error":"access_disabled","error_description":"MCP access is switched off for '
    'this Nextcloud account. The owner of the account can switch it back on in '
    'Nextcloud under Settings, Security, MCP Connector."}'
)
# Achtung Fallback-Copy: "Settings, Security, MCP Connector" ist jetzt der Ort des
# WEGWEISERS; der Schalter selbst liegt auf der verlinkten Connections-Seite. Der Satz
# wird ueber die eine Konstante SETTINGS_PLACE angepasst, nirgendwo sonst.
```

### 3. prepare_context-Skelett

```python
# Source: eigene Ableitung aus tools/search.py (Fan-out + degraded) und tools/calendar.py
async def prepare_context(clients, query, detail="short"):
    window_start, window_end = _window()          # jetzt .. jetzt+7d, ISO, UTC
    search_task = _guarded(search_tools.unified_search(clients, query=query, limit=25))
    cal_task = _guarded(_events_capped(clients, window_start, window_end))  # timeout 10 s
    search_out, cal_out = await asyncio.gather(search_task, cal_task, return_exceptions=True)
    degraded, results, events = _merge(search_out, cal_out)   # degraded: EXAKT die Suchen-Form
    if detail == "full":
        excerpts = await _excerpts(clients, results, degraded)  # Top 3, je 2000 B, je 5 s
    return {"query": query, "window": {...}, "events": events,
            "results": results, **({"degraded": degraded} if degraded else {}),
            "note": search_tools.SEARCH_NOTE}
```

### 4. Schalter-Tabelle im bestehenden Schema

```sql
-- Source: Muster oauth/store.py (_SCHEMA, CREATE TABLE IF NOT EXISTS ist die Migration)
CREATE TABLE IF NOT EXISTS user_access (
  nc_user TEXT PRIMARY KEY,
  disabled_at INTEGER NOT NULL
);
-- kein Eintrag = Zugriff an (D-50 kostenlos); resume = DELETE der Zeile
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Architektur-Skizze: Flag in `preferences_ex`, je Request aus Nextcloud gelesen (`.planning/research/ARCHITECTURE.md` Zeile 63/174) | Schalter in unserem Store, lokaler Read an der Grenze | Phase 3, SC-5-Messung; UI-SPEC supersediert die Skizze ausdrücklich | Der Planner darf die ältere, billiger aussehende Skizze nicht bauen |
| UI-SPEC-Annahme: `storage_type: external` heißt "Wert wird zur App gepusht" | Gemessen: external heißt "AppAPI speichert selbst, App holt per OCS ab"; kein Push in AppAPI 34 | diese Recherche, 2026-08-17 | Der im UI-SPEC vorentschiedene Fallback greift: Schalter auf `/connections`, Settings-Eintrag Link-only |
| nc_py_api als Settings-Weg (STACK.md-Empfehlung von 2026-08-14) | Ein roher OCS-Call mit vorhandenen Helpern | Phase 2, D-24 | Keine neue Dependency; STACK.md ist in diesem Punkt veraltet |
| `FastMCP`-Namen in Altdokumenten | `MCPServer`, mcp 2.0.x | Phase 1 | betrifft nur Zitate |

**Deprecated/outdated:**
- `nc_py_api.SettingsField.notify`: als "to be supported in future" markiert; bis es
  existiert und AppAPI es zustellt, gibt es keinen Push. Bei AppAPI 35 neu prüfen (BL-Kandidat).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Eine Form mit `fields: []` wird im Browser sichtbar gerendert (Titel, Beschreibung, doc_url-Icon). Datenlieferung an die Seite ist gemessen, der Pixel nicht | Declarative-Settings-Kontrakt | Niedrig: schlimmstenfalls fehlt der Settings-Wegweiser, Funktion unberührt. Plan: ein Browser-Blick auf `/settings/user/security` in der Verifikation |
| A2 | Übliche MCP-Clients geben einem Tool-Call mindestens 30 s (Claude/ChatGPT eher 60 s); 20 s Gesamtbudget liegt sicher darunter | Pattern 4 | Zu knappes Budget kostet nur Vollständigkeit (mehr `degraded`), zu großes provoziert Client-Timeouts. Plan: gegen echten Client einmal messen, Zahl im Code kommentieren |
| A3 | Die Empfehlungswerte (5 Treffer je Bucket, 3 Voll-Auszüge à 2000 Bytes, Fenster 7 Tage) sind sinnvolle Größenordnungen | Pattern 4 | Explizit Claude's Discretion; der Plan darf sie mit Begründung ändern |
| A4 | `getUserConfigValues` des Preferences-OCS ist als Initial-Sync nutzbar, falls je gebraucht (nicht Teil der Empfehlung) | Declarative-Settings-Kontrakt | Ohne Belang für den empfohlenen Entwurf |

## Open Questions

1. **"Last used" je Authorization (UI-SPEC Open Question 3)**
   - What we know: `clients.last_used_at` gehört zur Registrierung, nicht zur Authorization;
     eine geteilte Registrierung würde einem Nutzer die Aktivität eines anderen zeigen.
   - What's unclear: ob eine neue Spalte `authorizations.last_used_at` den Store-Umbau wert ist.
   - Recommendation: in v1 weglassen (so steht es im UI-SPEC); wenn der Plan sie doch will,
     ist es eine Spalte plus ein Write im Verifier-Pfad und gehört als bewusste Entscheidung
     in den Plan, nicht als Beifang.
2. **EXAPP-02-Wortlaut vs. Fallback**
   - What we know: Requirement sagt "in den Nextcloud-Settings aktivieren/deaktivieren";
     der gemessene AppAPI-Kontrakt macht das ohne D-47/D-48-Bruch unmöglich; CONTEXT und
     UI-SPEC entscheiden den Konflikt zugunsten der Constraints.
   - What's unclear: ob der Owner den Wortlaut von EXAPP-02 anpassen oder nur die
     Verifikations-Notiz akzeptieren will.
   - Recommendation: im PLAN als Verifikations-Notiz führen; keine Blockade.
3. **Nachmessen von SC 5 mit aktivem Gate**
   - What we know: der Schalter-Read ist lokal; theoretisch bleibt SC 5 exakt.
   - Recommendation: `scripts/oauth_flow_check.py --measure` nach dem Gate-Einbau einmal
     laufen lassen und die Zahl mit Datum ins VERIFICATION-Dokument schreiben (Projektregel).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv + Python | alles | ✓ | Python 3.13.13 via `uv run --no-sync` | — |
| Docker + Wegwerf-Topologie (`compose.exapp.yml`) | Runtime-Verifikation Settings-Form, E2E-Schalter-Test | ✓ | Topologie läuft (nc-mcp-exapp-nc, -harp, -caddy, nc_app_mcp_connector, alle healthy, Port 8081) | — |
| gh CLI (GitHub-Quellen) | Recherche/Zitate | ✓ | funktionsfähig (alle Quellcode-Reads dieser Recherche) | — |
| ruff / pytest | Gates | ✓ | ruff 0.16.3; Suite zuletzt 1396 passed | — |
| AppAPI auf Ziel-NC | Settings-Form, Preferences-OCS | ✓ | v34.0.3 (Tag verifiziert; Testinstanz antwortet) | — |
| Owner-Instanzen `nc-mcp-test`, `findling-nextcloud` | dürfen NICHT angefasst werden | ✓ (laufen) | — | — |

**Missing dependencies with no fallback:** keine.
**Missing dependencies with fallback:** keine.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | unverändert Phase 3: AppAPI-Handshake + StoreTokenVerifier; diese Phase fügt keine neue Authentifizierung hinzu, nur eine Autorisierungsentscheidung dahinter |
| V3 Session Management | yes | Identität auf `/connections` ausschließlich aus dem HaRP-signierten `AUTHORIZATION-APP-API` (gemessenes CR-01-Muster), nie aus Request-Werten |
| V4 Access Control | yes | Schalter-Gate an der einen Transportgrenze (beide Anschlussarten, D-49); Ownership-Check `is_user(row.nc_user, resolved)` je Zeile; die drei Fälle "unbekannt/fremd/schon widerrufen" antworten identisch (keine Existenz-Orakel) |
| V5 Input Validation | yes | Aktionsfeld als geschlossene Enumeration; `auth_id` nur als HMAC-gebundenes Hidden Field; Client-Name durch `layout.client_name` (DCR-Input, T-03-20); Escaping am einen Punkt in `layout` |
| V6 Cryptography | yes | keine neue Kryptografie: HMAC über das vorhandene `form_token`-Primitive (Installations-Datenschlüssel), nichts selbst bauen |

### Known Threat Patterns for ExApp-Settings + Multi-Source-Tool

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF auf Disconnect/Schalter | Tampering | POST-only, HMAC-Hidden-Field, `form-action 'self'`, Confirm-Zwischenseite (T-03-35, T-03-50) |
| IDOR über geratene `auth_id` | Elevation | Ownership-Check gegen HaRP-Identität; identische Antwort für fremd/unbekannt/weg (UI-SPEC S8) |
| User-Enumeration über R1 | Information Disclosure | R1 erst nach gültigem Credential; anonyme/ungültige Aufrufer bekommen weiter R2/R3 (Pitfall 2) |
| Client-Rediscovery-Schleife nach Pause | DoS (auf Nextcloud) | 403 ohne `WWW-Authenticate` statt 401 (UI-SPEC R1, bewusste RFC-6750-Abweichung mit dokumentiertem Preis) |
| Proxy-Caching der Kontoseite | Information Disclosure | `Cache-Control: no-store` auf jeder Antwort inkl. R1 (Phase-2-Pitfall 4) |
| DoS über prepare_context-Fan-out | DoS | harte Teil-Budgets, Trefferzahl-Caps, Byte-Caps je Auszug; kein Retry; MCP-Route bleibt unthrottled wie in Phase 3 begründet |
| Bösartiger App-Name in der Zeilenliste | Tampering (UI) | `layout.client_name` (Steuerzeichen raus, 80 Zeichen), dann zentrales Escaping (UI-SPEC) |
| HaRP-Blacklist-Aussperrung | DoS | Route 13 PUBLIC statt USER, Identitätsprüfung in der App (gemessener CR-01-Grund) |

## Sources

### Primary (HIGH confidence)

- nextcloud/app_api **v34.0.3** (Tag der Zieltopologie): `lib/Service/UI/SettingsService.php`
  (erzwungenes `storage_type: external`, insertOrUpdate, findAllEnabled),
  `lib/Listener/DeclarativeSettings/{Get,Set,RegisterDeclarativeSettings}ValueListener.php`
  (kompletter Wert-Pfad, kein ExApp-Call), `lib/Controller/OCSSettingsController.php` und
  `lib/Controller/PreferencesController.php`, `appinfo/routes.php` (OCS-URLs),
  `lib/Service/ExAppService.php` (Cleanup bei Deinstallation)
- nextcloud/server **stable34**: `lib/private/Settings/DeclarativeManager.php`
  (Event-Dispatch nur bei external, validateSchema inkl. leeres fields-Array),
  `lib/public/Settings/Events/DeclarativeSettingsSetValueEvent.php` (extends Event, nicht
  webhook-kompatibel), `apps/settings/appinfo/routes.php`,
  `apps/settings/lib/Sections/Personal/Security.php` (Id `security`),
  `apps/settings/lib/Controller/CommonSettingsTrait.php` (Sektion zeigt deklarative Formen)
- **Eigene Messung 2026-08-17** gegen die laufende Topologie (Messprotokoll oben):
  Registrierung 200, Auslieferung in `/ocs/v2.php/settings/api/declarative/forms` und im
  HTML von `/settings/user/security`, Deregistrierung 200
- Lokaler Code: `exapp/middleware.py`, `exapp/lifecycle.py`, `exapp/status.py`,
  `exapp/auth.py`, `oauth/store.py`, `oauth/provider.py`, `tools/search.py`,
  `tools/calendar.py`, `tools/chatgpt.py`, `provider_map.py`, `appinfo/info.xml`,
  `scripts/check_tool_budget.py` (Budget-Messung 10642/12500 am 2026-08-17)
- `.planning/phases/04-*/04-CONTEXT.md`, `04-UI-SPEC.md` (bindender Design-Vertrag),
  `03-VERIFICATION.md` (SC 5), `02-RESEARCH.md`

### Secondary (MEDIUM confidence)

- Nextcloud Developer Manual, ExApp Declarative Settings
  [CITED: docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/settings.html]:
  bestätigt Speicherung in der DB und Abholung per Preferences/AppConfig-API
- cloud-py-api/nc_py_api `ex_app/ui/settings.py` (Referenz, bewusst keine Dependency):
  Payload-Form `{"formScheme": ...}`, `notify`-Attribut als Zukunftsfeature

### Tertiary (LOW confidence)

- Tool-Call-Timeouts der MCP-Clients (A2): keine offizielle Quelle gefunden; nur die
  OAuth-Timeouts aus Phase 3 sind zitierbar. Budget-Empfehlung entsprechend konservativ.

## Metadata

**Confidence breakdown:**
- Declarative-Settings-Kontrakt: HIGH — Quellcode an Tag v34.0.3 gelesen UND am laufenden
  System gemessen; der Negativ-Befund (kein Push) ist dreifach belegt
- Schalter-Architektur (Fallback): HIGH — vom UI-SPEC vorentschieden, alle Bausteine im Repo
- prepare_context: HIGH für die Bausteine (alles vorhanden und getestet), MEDIUM für die
  konkreten Budget-Zahlen (Discretion, A2/A3)
- Pitfalls: HIGH — überwiegend aus gemessenen Phase-2/3-Befunden fortgeschrieben

**Research date:** 2026-08-17
**Valid until:** ~30 Tage für den AppAPI-Kontrakt (NC-34-Zielversion ist eingefroren);
bei einem Wechsel auf AppAPI 35 den `notify`-Stand neu prüfen
