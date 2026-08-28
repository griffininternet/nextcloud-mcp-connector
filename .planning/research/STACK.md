# Stack Research

**Domain:** Nextcloud MCP-only ExApp, Milestone v1.5 "Vorlauf openDesk" (OpenProject-Spike, Audit-Log)
**Researched:** 2026-08-28
**Confidence:** HIGH für alles, was live gemessen oder gegen den Quelltext gelesen wurde
(OpenProject-OAuth-Metadaten, `/mcp`-401, HAL-Nutzlastgrößen, `select`-Verhalten,
openDesk-1.18.0-Komponentenstände, admin_audit-/Activity-/AppAPI-Routen, mcp-2.x-Middleware).
MEDIUM für die Rechts- und Normlage (BSI-Mindeststandard-Version, BSIG-Paragraf) und für die
openDesk-EE-Frage. LOW für nichts, was hier als Empfehlung steht.

**Diese Datei ersetzt die v1.2-Stack-Recherche vom 2026-08-21.** Der Kernstack (Python 3.13,
mcp>=2.0,<3, httpx, lxml, uv, AppAPI/HaRP, SQLite als Persistenz) wird nicht angetastet und
hier nicht erneut begründet. Es geht ausschließlich um die beiden neuen Bausteine.

---

## Antwort in zwei Sätzen

**Es kommt wieder keine einzige neue Laufzeit-Abhängigkeit dazu:** OpenProject ist HAL+JSON über
HTTP und wird mit dem vorhandenen `httpx` gesprochen, und das Audit-Log wird mit demselben
stdlib-`sqlite3` geschrieben, das `oauth/store.py` seit Phase 3 auf dem ExApp-Volume betreibt,
plus einem JSON-Formatter auf dem stdlib-`logging`. Die beiden Zukäufe, die dieser Milestone
wirklich macht, sind keine Bibliotheken, sondern zwei Entscheidungen: die OpenProject-Verbindung
ist ein **eigener OAuth-Autorisierungscode-Fluss je Nutzer gegen OpenProject selbst** (nicht
OIDC-Token-Exchange, der aus einer ExApp konstruktionsbedingt unerreichbar ist), und das
Audit-Log braucht **zwei Senken statt einer**, weil weder stdout allein noch SQLite allein bei
einer deutschen Behörde als Audit-Log durchgeht.

---

# Teil A: OpenProject

## A.1 Der API-Stand, live gemessen

**API v3 ist die einzige allgemeine API. Ein v4 gibt es nicht.** Die Doku ist OpenAPI 3.1,
das Format ist HAL+JSON, die Spezifikation liegt auf jeder Instanz unter `/api/v3/spec.json`.

OpenProject veröffentlicht insgesamt vier API-Flächen plus die well-known-Endpunkte:

| Fläche | Zweck | Für uns |
|--------|-------|---------|
| **API v3** | Projekte, Arbeitspakete, Nutzer, alles Allgemeine | **das Ziel des Spikes** |
| SCIM | Nutzer-/Gruppenprovisionierung (RFC 7643/7644) | irrelevant |
| BCF v2.1 | BIM-Sonderfall | irrelevant |
| **MCP** | eigener MCP-Server von OpenProject, `/mcp` | **strategisch entscheidend, siehe A.5** |
| `/.well-known/oauth-authorization-server` | RFC 8414 | AS-Discovery |
| `/.well-known/oauth-protected-resource` | RFC 9728 | RS-Discovery, exakt der MCP-Auth-Weg |
| `/.well-known/openproject-metadata` | `installation_uuid`, unauthentifiziert | Instanz-Erkennung |

**Aktueller Stand:** 17.7.2, veröffentlicht 2026-08-13 (GitHub-Release-Tag geprüft). 17.8.0 ist
im `dev`-Zweig als Release-Notes vorhanden, also unmittelbar bevorstehend, aber noch nicht
getaggt.

Live gegen `community.openproject.org` am 2026-08-28 gemessen:

```
GET /.well-known/oauth-authorization-server
{
  "issuer": "https://community.openproject.org",
  "authorization_endpoint": ".../oauth/authorize",
  "token_endpoint": ".../oauth/token",
  "introspection_endpoint": ".../oauth/introspect",
  "scopes_supported": ["api_v3", "scim_v2", "mcp", "bcf_v2_1"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"]
}

GET /.well-known/oauth-protected-resource
{
  "resource": "https://community.openproject.org",
  "authorization_servers": ["https://id.openproject.com/realms/master",
                            "https://community.openproject.org"],
  "scopes_supported": ["bcf_v2_1", "api_v3", "scim_v2", "mcp"],
  "bearer_methods_supported": ["header"]
}
```

Drei Befunde aus diesen zwanzig Zeilen, die die Planung bestimmen:

1. **Kein `registration_endpoint`.** OpenProject kann keine Dynamic Client Registration. Unser
   Client muss von einem OpenProject-Administrator von Hand angelegt werden. Das ist die
   Spiegelseite unserer eigenen DCR/CIMD-Arbeit und ändert die Ein-Klick-Erzählung an dieser
   Stelle: es gibt für OpenProject keinen Ein-Klick.
2. **Kein `code_challenge_methods_supported`.** Die Metadaten bewerben PKCE nicht. Doorkeeper,
   der darunterliegende Rails-OAuth-Server, kann PKCE, und die API-Einführung nennt
   "Authorization code flow with PKCE" ausdrücklich. Das ist genau die Art Widerspruch, die man
   nicht annimmt, sondern misst. **Erste Messung des Spikes.**
3. **Zwei Authorization Server in der Resource-Metadata.** Auf der Community-Instanz stehen das
   externe Keycloak *und* OpenProject selbst. Das ist wörtlich das openDesk-Muster, nur mit
   anderen Hostnamen, und es bedeutet: ein Client, der RFC 9728 sauber liest, muss sich
   entscheiden, welchen AS er nimmt.

Und der `/mcp`-Endpunkt antwortet unautorisiert genau so, wie die MCP-Authorization-Spec es
verlangt:

```
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer realm="OpenProject API",
                  resource_metadata="https://community.openproject.org/.well-known/oauth-protected-resource",
                  scope="mcp"
```

## A.2 Authentifizierung im Namen des angemeldeten Nutzers: fünf Wege, zwei bleiben übrig

| Weg | Wie | Verdikt |
|-----|-----|---------|
| **OAuth 2.0 Authorization Code gegen OpenProject** | Admin legt unter *Administration → Authentifizierung → OAuth-Anwendungen* eine Anwendung an (Name, Redirect-URL, Scopes, Häkchen "Confidential"). Endpunkte `/oauth/authorize`, `/oauth/token`. Default-Scope `api_v3`. | **EMPFEHLUNG.** Funktioniert in Community und Enterprise, funktioniert innerhalb und außerhalb openDesk, ist per Nutzer, ist widerrufbar, und passt exakt auf die Verbindungsseite, die wir seit v1.0 haben |
| **Persönliches API-Token** | Nutzer legt es unter *Mein Konto → Zugriffstoken* an. Übergabe als Basic-Auth `apikey:<token>` oder seit 17.2 als `Authorization: Bearer <token>` (#71147). Voraussetzung: Instanz-Einstellung "API-Token aktivieren" | **DOKUMENTIERTER RÜCKFALL.** Braucht keinen Administrator, was in einer fremden Behörde Gold wert ist. Der Nutzer klebt ein Geheimnis in ein Feld, das ist hässlicher, aber es ist derselbe Ausweg, den wir bei Cursor schon fahren (E5-Seite) |
| **Externes OIDC-JWT (RFC 9068)** | OpenProject akzeptiert ein von Keycloak ausgestelltes JWT-Access-Token, wenn der Provider konfiguriert und die Audience richtig ist | **UNERREICHBAR, siehe A.3.** Nicht weil OpenProject es nicht kann, sondern weil wir an das Token nicht herankommen |
| Globale Basic-Auth | `OPENPROJECT_AUTHENTICATION_GLOBAL__BASIC__AUTH_USER/_PASSWORD`, ein instanzweites Geheimnis. openDesk setzt es. | **VERBOTEN.** Das ist nicht der angemeldete Nutzer. Es bricht das Kernversprechen in einer einzigen Zeile Code, und der AST-Gate-Gedanke gehört genau hierher: dieser Weg muss unmöglich sein, nicht bloß unbenutzt |
| Client Credentials mit "Client Credentials User" | OpenProject erlaubt, einer OAuth-Anwendung einen festen Nutzer zuzuordnen, in dessen Namen alle Anfragen laufen | **VERBOTEN**, aus demselben Grund. `client_credentials` steht in `grant_types_supported`; dass es dasteht, ist keine Einladung |

## A.3 Warum der OIDC-Weg ausfällt, mit der Belegkette

Das ist der Befund, der am meisten Planungszeit spart, deshalb hier die volle Kette:

1. **OpenProject-Seite ist bereit.** Die OIDC-SSO-Kopplung zwischen Nextcloud und OpenProject ist
   dokumentiert und verlangt vom IdP entweder OAuth 2.0 Token Exchange nach **RFC 8693** oder
   Tokens, die schon beim Login die nötige Audience tragen. Signaturverfahren RS256,
   Access-Token-Typ "JWT Access Token (RFC 9068)". Sie ist aber ein **Enterprise-Add-on**
   (Corporate-Plan).
2. **Keycloak-Seite ist seit über einem Jahr bereit.** Standard Token Exchange nach RFC 8693 ist
   seit **Keycloak 26.2** (Mai 2025) offiziell unterstützt statt Preview, umlegbar per Schalter
   am Client. Keycloak 26.5 (Januar 2026) hat zusätzlich JWT-Authorization-Grant und Identity
   Chaining gebracht.
3. **Die Nextcloud-Seite ist der Bruch.** `user_oidc` (8.12.0-dev, NC 29 bis 36) kann Token
   Exchange, aber ausschließlich als **PHP-Ereignis**:
   `OCA\UserOIDC\Event\ExchangedTokenRequestedEvent`, im Prozess dispatched, Token direkt im
   Ereignisobjekt zurück. Die `appinfo/routes.php` von `user_oidc` wurde gelesen: der `ocs`-Block
   enthält Provider-CRUD und Nutzer-CRUD, **keine Token-Route**. Eine ExApp im eigenen Container
   kann ein PHP-Ereignis nicht auslösen.
4. **Und selbst mit einer PHP-Begleit-App ginge es nicht.** Der Exchange braucht das
   **Login-Token in der Nextcloud-Session** des Nutzers (`occ config:app:set user_oidc
   store_login_token --value=1`, ab Werk aus). Unsere Anfragen kommen von einem KI-Client über
   unser eigenes OAuth, ohne Browser-Session und ohne Keycloak-Login. Es gibt in dem Moment
   keine Session, aus der ein Token zu tauschen wäre.

**Konsequenz für die Fragenliste zum ISV-Call:** Die Frage lautet nicht "unterstützt ihr OIDC",
sondern "gibt es einen Weg, wie eine AppAPI-ExApp ein audience-korrektes Token für eine
Schwesterkomponente bekommt, ohne Browser-Session". Heute gibt es ihn nicht, und das ist eine
Lücke im openDesk-Baukasten, nicht in unserem Entwurf.

## A.4 Python-Client: keiner. Belegt, nicht behauptet.

Über die PyPI-JSON-API am 2026-08-28 abgefragt:

| Paket | Version | Letzter Upload | Abhängigkeiten | Verdikt |
|-------|---------|----------------|----------------|---------|
| `pyopenproject` | 0.7.4 | **2021-03-26** | `requests~=2.25.1`, `PyYAML~=5.3.1` | tot, fünf Jahre alt, gepinnte Uralt-Deps |
| `openproject` | 0.6.0 | 2024-01-24 | **`httpx>=0.25,<0.26`** | **harter Konflikt** mit unserem `httpx>=0.28,<0.29`. Nicht installierbar, ohne den Kernstack zurückzudrehen |
| `openproject-api-client` | 0.4.0 | 2026-08-19 | `requests>=2.25.1` | frisch, aber **drei Releases insgesamt**, unbekannter Herausgeber, und es zöge `requests` in ein Projekt, das bewusst nur `httpx` spricht. Für einen Solo-Betrieb ist das eine Lieferketten-Fläche ohne Gegenwert |
| `openproject-mcp`, `mcp-openproject` | 1.0.2 / : | 2025-12-29 | `aiohttp`, `mcp>=1.0` | sind selbst MCP-Server, keine Clients. Wären Konkurrenz, keine Bibliothek |

**Also: `httpx`, wie bei jeder Nextcloud-API.** Die Entscheidung ist dieselbe wie gegen
`nc_py_api` in v1.0 und aus demselben Grund: der Spike braucht drei bis fünf HTTP-Aufrufe. Ein
Client, der 200 Endpunkte modelliert, ist für drei Aufrufe kein Gewinn, sondern eine zweite
Fehlerquelle, ein zweites Lizenzthema und eine zweite Zeile in `docs/dependency-audit.md`.

## A.5 Der Befund, der die Spike-Frage umstellt: OpenProject hat einen eigenen MCP-Server

Seit **OpenProject 17.2** gibt es `/mcp`, als **Enterprise-Add-on**, in der Admin-Oberfläche noch
mit "beta"-Etikett. Bis 17.7 ausschließlich lesend; **17.8** bringt `create_work_package`,
`update_work_package`, Kommentare und Relationen, entfernt die HTML-Darstellung formatierbarer
Felder und die Output-Schemata aus den Tool-Definitionen und beschneidet die Links in den
Antworten. Authentifizierung: Scope `mcp`, per OpenProject-OAuth-Anwendung, per persönlichem
API-Token oder per Token eines konformen OIDC-Providers. Der Administrator kann einzelne Tools
abschalten und umbenennen und das Antwortformat zwischen `full`, `structured content only` und
`content only` umstellen.

Das ist keine schlechte Nachricht, aber es verschiebt die Frage, die der Spike beantworten muss.
Sie lautet nicht mehr "können wir OpenProject anbinden", sondern:

> **Wozu soll unsere ExApp OpenProject-Tools anbieten, wenn OpenProject selbst welche hat?**

Die belastbare Antwort, die der Spike belegen oder verwerfen muss, ist der Zusammenschnitt, nicht
die Abdeckung:

- **Ein Endpunkt, eine Autorisierung.** Der Nutzer verbindet einen MCP-Server, nicht zwei. In
  einem Client mit Tool-Limit (Cursor: 80) und in jedem Client mit Token-Budget ist "ein
  Connector für den Arbeitsplatz" ein anderes Produkt als "ein Connector je Anwendung".
- **`prepare_context` über Komponentengrenzen.** Termine, Suche, Talk-Digest, Mail-Zähler *und*
  die fälligen Arbeitspakete in einem Aufruf ist etwas, das der OpenProject-MCP
  konstruktionsbedingt nicht kann.
- **Verfügbarkeit.** Der OpenProject-MCP ist Enterprise. Siehe A.6: in openDesk CE ist er nicht da.
- **Unsere Auth-Erzählung.** Wir haben das gebaut, was OpenProject für `/mcp` voraussetzt, aber
  nur einmal pro Instanz vom Admin bekommt.

Und die ehrliche Gegenrechnung, die genauso in den Spike-Bericht gehört: Wenn ein Kunde
openDesk EE fährt und ein Client zwei MCP-Server verträgt, ist der OpenProject-eigene Server
näher an der Quelle, wird von OpenProject gepflegt und kann schreiben. Das ist ein legitimes
Ergebnis eines Spikes.

## A.6 openDesk: was wirklich ausgeliefert wird, und was uns dort härter trifft als die Auth-Frage

Alles Folgende ist am Tag `v1.18.0` des Deployment-Repos `bmi/opendesk/deployment/opendesk` auf
gitlab.opencode.de gelesen (Tag vom 2026-08-19), nicht aus Blogtexten.

**Komponentenstände in openDesk 1.18.0:**

| Komponente | Version in 1.18.0 | Bemerkung |
|------------|-------------------|-----------|
| **Nextcloud** | **33.0.7** (von 32.0.9) | in unserer unterstützten Spanne |
| **OpenProject** | **17.7.2** (von 17.6.0) | exakt der aktuelle Stand, openDesk zieht schnell nach |
| OX App Suite | 8.51 | Groupware, nicht Nextcloud Mail |
| Element / Synapse | 1.12.8 / 1.157.2 | Matrix ist der Chat, nicht Talk |
| Collabora | 26.04.02 | |
| CryptPad | 2026.5.1 | |
| Jitsi | 2.0.11146 | |
| Nubus (Univention) | IAM, Keycloak darin | OIDC-Provider, OpenLDAP als Verzeichnis |

**Wie die Komponenten einander vertrauen:** Keycloak ist OIDC-Provider, Keycloak föderiert gegen
OpenLDAP, jede Anwendung bekommt einen eigenen Keycloak-Client mit eigenem Client-Scope, der an
eine Keycloak-Rolle gebunden ist (`opendesk-nextcloud` / `opendesk-nextcloud-scope`,
`opendesk-openproject` / `opendesk-openproject-scope` und so weiter). Backend-Dienste zueinander
laufen über geteilte Geheimnisse und komponentenspezifische LDAP-Suchkonten; die
Frontend-Verklammerung macht der Intercom Service und die zentrale Navigation
(`OPENPROJECT_SOUVAP__NAVIGATION__URL` gegen das Nubus-Portal).

**OpenProject ist in openDesk auf Keycloak festgenagelt:**
`OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER: "keycloak"` bedeutet kein lokales Anmeldeformular.
`OPENPROJECT_OPENID__CONNECT_KEYCLOAK_ISSUER` zeigt auf das Realm. Für einen
Autorisierungscode-Fluss heißt das: der Nutzer landet auf Keycloak, kommt mit einer
OpenProject-Session zurück, und OpenProject stellt uns danach seinen eigenen Code aus. Das
funktioniert, ist aber ein zusätzlicher Redirect-Hop, den der Spike einmal wirklich durchlaufen
muss.

**Die Enterprise-Klausel, wörtlich aus den Helm-Werten:**

```
{{- if and (eq (env "OPENDESK_ENTERPRISE") "true") .Values.enterpriseKeys.openproject.token }}
OPENPROJECT_SEED__ENTERPRISE__TOKEN: ...
```

**In openDesk CE läuft OpenProject ohne Enterprise-Token.** Damit sind dort weder der
OpenProject-MCP-Server (Enterprise seit 17.2) noch der OIDC-SSO-Speichermodus (Enterprise)
verfügbar. In openDesk EE sind sie es. Das ist die schärfste Trennlinie im ganzen Teil A und
gehört als erste Frage in den ISV-Call.

**Drei openDesk-Befunde, die uns härter treffen als alles bisher Genannte:**

1. **Es gibt in openDesk keinen Nextcloud App Store.** In den Nextcloud-Werten steht
   `appstore: enabled: false`. Unsere gesamte Ein-Klick-Erzählung, die Kern der Positionierung
   und der Store-Beschreibung ist, existiert in einer openDesk-Installation **nicht**. Installation
   dort ist eine Betreiber-Aufgabe im Helmfile.
2. **AppAPI ist in openDesk nicht dabei, und AppAPI kann kein Kubernetes.** Die Deploy-Daemons
   sind HaRP (empfohlen ab NC 32) und der Docker Socket Proxy (abgekündigt, Entfernung für
   NC 35 angekündigt). Beide sind Docker. openDesk ist Helm auf Kubernetes. Der einzige
   realistische Weg ist der Daemon-Typ **`manual_install`** (existiert, in
   `src/constants/daemonTemplates.js` und `lib/Command/Daemon/RegisterDaemon.php` belegt): unser
   Container läuft als gewöhnliches K8s-Deployment, und `occ app_api:daemon:register` plus
   `occ app_api:app:register` verdrahten ihn. Ungemessen.
3. **Zwei unserer neun Familien sind in openDesk dunkel.** `spreed: enabled: false` (Chat ist
   Element/Matrix), `contacts: enabled: false`, dazu `comments` und `circles` aus. Von 21 Tools
   bliebe in openDesk weniger übrig, als die Store-Beschreibung verspricht.

**Ändert openDesk die Antwort auf die Auth-Frage? Nein, aber es verschärft sie.** openDesk macht
den OIDC-Weg optisch zwingend und ist genau der Weg, den wir nicht erreichen (A.3). Die Empfehlung
bleibt: OAuth-Autorisierungscode je Nutzer direkt gegen OpenProject, API-Token als dokumentierter
Rückfall.

## A.7 Nutzlast: die Schema-Diät passiert diesmal serverseitig

Live gemessen gegen `community.openproject.org`, 2026-08-28, alle Werte minifiziert:

| Objekt | Bytes | Struktur |
|--------|-------|----------|
| Ein Arbeitspaket, `GET /api/v3/work_packages?pageSize=1` | **3691** | 32 Felder auf oberster Ebene, darunter sechs `customFieldNNN`; `_links` allein **2099 Bytes über 37 Relationen**, also 57 Prozent reiner Navigationsballast; `description` 855 Bytes |
| Ein Projekt, `GET /api/v3/projects?pageSize=1` | 2024 | 12 Felder, 16 Links |
| Dasselbe Arbeitspaket mit `select=` | **216** | siehe unten |

```
GET /api/v3/work_packages?pageSize=1&select=total,count,elements/id,elements/subject,
    elements/status,elements/project,elements/dueDate
-> {"id":24971,"_links":{"status":{"href":"/api/v3/statuses/1","title":"new"},
    "project":{"href":"/api/v3/projects/1534","title":"Stream agile"}},
    "dueDate":null,"subject":"Backlogs should include tasks from subprojects"}
```

**3691 auf 216 Bytes, 94 Prozent weniger, und die Diät macht der Server.** Das ist besser als
alles, was wir gegen Nextcloud tun können, wo wir jedes Feld selbst wegprojizieren müssen.

Die erlaubten `select`-Werte sind eine geschlossene Liste, und OpenProject sagt sie im
Fehlerfall selbst an, mit einem sauberen 400 statt einem stillen Ignorieren:

```
{"_type":"Error","errorIdentifier":"urn:openproject-org:api:v3:errors:InvalidSignal",
 "message":"The requested select of updatedAt is not supported. Supported selects are
  self, project, status, type, author, assignee, responsible, _type, id, displayId,
  subject, startDate, dueDate, date, *."}
```

Merke für die Planung: `updatedAt` ist **nicht** selektierbar. Wer eine "was hat sich geändert"-
Ansicht bauen will, braucht `filters` statt `select`, oder er zahlt die vollen 3691 Bytes.

## A.8 Konkreter Zuschnitt für den zeitboxierten Spike

Ziel: Projekte und Arbeitspakete im Namen des angemeldeten Nutzers lesen. Fünf Aufrufe reichen:

| Zweck | Aufruf |
|-------|--------|
| Instanz erkennen | `GET /.well-known/openproject-metadata` (unauthentifiziert, liefert `installation_uuid`) |
| AS/RS-Discovery | `GET /.well-known/oauth-protected-resource`, dann `/.well-known/oauth-authorization-server` |
| Projekte | `GET /api/v3/projects?pageSize=&offset=` |
| Arbeitspakete | `GET /api/v3/work_packages?pageSize=&offset=&select=...&filters=[...]` |
| Berechtigungsprobe | derselbe Aufruf mit dem Token eines zweiten Nutzers, Zwei-Konten-Negativbeweis wie in v1.0 |

**Messumgebung: ein blankes OpenProject 17.7.2 im Container, nicht ein openDesk-Cluster.**
`openproject/openproject:17` ist ein einzelner Compose-Dienst neben `compose.test.yml`, genau das
Muster, das GreenMail in v1.2 hatte. Ein openDesk-Cluster zu stellen ist ein eigener Milestone,
kein Spike-Vorlauf, und die vier Fragen, die wirklich offen sind, beantwortet die blanke Instanz
genauso:

1. Nimmt `/oauth/authorize` einen PKCE-`code_challenge` an, obwohl die Metadaten ihn nicht bewerben?
2. Wie teuer ist ein Arbeitspaket nach `select` wirklich, gegen unser Byte-Budget gerechnet?
3. Kommt der bestehende SSRF-Schutz aus v1.1 mit einem internen Dienstnamen als Ziel-URL klar,
   oder sperrt er die Nachbarkomponente konstruktionsbedingt aus? **Das ist der am meisten
   unterschätzte Punkt**: unsere SSRF-Grenze wurde gegen das offene Internet gehärtet, und eine
   Schwesterkomponente im selben Cluster sieht für sie aus wie ein Angriffsziel.
4. Trägt der API-Token-Weg ohne jede Admin-Handlung?

---

# Teil B: Audit-Log

## B.1 Der Aufhänger: SQLite ist hier keine neue Technologie

`src/mcp_connector/oauth/store.py` betreibt seit Phase 3 stdlib-`sqlite3` mit
`journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout` und je Aufruf einer eigenen Verbindung in
`asyncio.to_thread`, auf dem Volume hinter `APP_PERSISTENT_STORAGE`
(`nc_app_<appid>_data`, vom Deploy-Daemon angelegt, schreibbar für uid 10001, in
`config.persistent_storage()` fail-closed geprüft). Der Modul-Docstring begründet dort bereits
ausdrücklich, warum stdlib und nicht `aiosqlite`.

Ein Audit-Log ist damit **keine Architekturentscheidung mehr, sondern eine zweite Tabelle nach
demselben Muster**. Das ist der Grund, warum dieser Baustein für einen Solo-Betrieb tragbar ist.

## B.2 Die Senken, einzeln bewertet

### B.2.1 Strukturiertes JSON nach stdout

**Technik:** stdlib `logging` plus eine `logging.Formatter`-Ableitung mit `json.dumps`. Rund
40 Zeilen. Das Projekt nutzt bereits durchgängig `logging.getLogger("mcp_connector.<modul>")`,
es ändert sich also nur der Handler in den beiden Entry-Points.

**Wo es landet:**
- Docker: der `json-file`- oder `journald`-Treiber. AppAPI kann die Container-Logs in der
  Admin-Oberfläche herunterladen (`GET /apps/logs/{appId}`,
  `ExAppsPageController::getAppLogs`, ruft `dockerActions->getContainerLogs`, und die
  Fehlermeldung sagt selbst: funktioniert nur bei `json-file` oder `journald`).
- Kubernetes/openDesk: die Cluster-Log-Pipeline, also genau die zentrale Stelle, die eine
  Behörde ohnehin betreibt.

**Format:** an Nextclouds eigenes anlehnen. Nextcloud schreibt JSON-Zeilen mit `reqId`, `level`,
`time`, `remoteAddr`, `user`, `app`, `method`, `url`, `message`. Wer dieselben Feldnamen
verwendet, spart dem Administrator eine Parser-Regel.

**Verdikt einer Behörde:** **Ja, als Transportweg.** Das ist die Senke, die die zentrale
Protokollierungsinfrastruktur speist, und genau die verlangt OPS.1.1.5.A6. **Nein, als Speicher.**
Container-Logs sterben mit dem Container, Dockers Rotation ist größenbasiert und wirft ohne
Rückfrage weg, und manipulationserkennend ist daran nichts.

### B.2.2 SQLite im ExApp-Volume

**Technik:** zweite Datei neben dem OAuth-Store, gleiche Pragmas, gleiches Thread-Muster, reine
`INSERT`-Tabelle. Kein `UPDATE`, kein `DELETE` außer durch einen dokumentierten
Aufbewahrungs-Job.

**Das eine, was hinzukommen muss, damit das Wort "Audit" trägt: eine Hash-Kette.**
`prev_hash` und `entry_hash = sha256(prev_hash || canonical_json(eintrag))`, dazu ein
Prüfkommando, das die Kette einmal durchläuft. Rund 30 Zeilen, keine Abhängigkeit
(`hashlib` ist stdlib). Damit wird aus "jemand hat eine Zeile geändert" von unsichtbar zu
nachweisbar. Ohne diese 30 Zeilen ist die Datei eine Datenbank, keine Beweismittelkette, und
genau diesen Unterschied fragt ein Auditor ab.

**Verdikt einer Behörde:** **Ja, als anwendungseigener Nachweis**, wenn drei Dinge dokumentiert
sind: Aufbewahrungsfrist und Löschprozess, Aufnahme in die Sicherung, und ein Weg, die Integrität
zu prüfen. **Nein, als alleinige Ablage.** Ein Speicher, den die geprüfte Anwendung selbst besitzt
und beschreibt, genügt allein nicht. Deshalb zwei Senken, nicht eine.

### B.2.3 In Nextcloud hineinschreiben: drei Varianten, zwei davon unmöglich

**`admin_audit`: geht nicht. Punkt.** Gegen den Quelltext geprüft, `stable34` und `master`:
`apps/admin_audit/lib` enthält `AuditLogger.php`, `IAuditLogger.php`, `Listener/`, `Actions/`,
`BackgroundJobs/Rotate` und eine `.noopenapi`-Markierung. **Kein Controller, keine Route, keine
OCS-Fläche.** Es ist ein PHP-Ereignis-Zuhörer, der über `ILogFactory::getCustomPsrLogger` in eine
eigene Datei schreibt, gesteuert durch `log_type_audit` (Werte wie `log_type`: `file`, `syslog`,
`systemd`, `errorlog`; Vorgabe `file`) und `logfile_audit` (Vorgabe
`[datadirectory]/audit.log`). Versionen: **1.24.0** auf NC 34, **3.0.0-dev.0** auf master (NC 36),
Architektur unverändert. Ein externer Container kann dort nicht hineinschreiben. Eine
PHP-Begleit-App könnte es, würde aber die Positionierung "MCP-only-ExApp" zerstören, die der
ganze Wettbewerbsvorteil ist. **In v1.5 nicht anfassen.**

**Activity-App: falsches Instrument, und ohnehin keine Schreib-API.** `appinfo/routes.php`
geprüft (7.0.0 auf NC 34, 9.0.0-dev auf master): der einzige `POST` im `ocs`-Block ist
`RemoteActivity#receiveActivity` auf `/api/v2/remote/{token}`, der Empfänger für föderierte
Freigaben, an ein Remote-Share-Token gebunden. Alles andere ist `GET`. Selbst wenn es ginge:
Activity ist ein Nutzer-Feed, den der Nutzer sich wegkonfigurieren kann. Ein Audit-Log, das der
Auditierte abschalten kann, ist keins.

**AppAPI-OCS-Log-Endpunkt: der existiert, und der ist der interessante.**

```
POST /ocs/v1.php/apps/app_api/api/v1/log
Parameter: level (0 debug, 1 info, 2 warning, 3 error, 4 fatal), message (string)
Attribute: #[AppAPIAuth] #[PublicPage] #[NoAdminRequired] #[NoCSRFRequired] #[MaintenanceModeAvailable]
Wirkung: $this->logger->log($level, $message, ['app' => <ex-app-id-Header>])
```

Das schreibt in die **gewöhnliche nextcloud.log**, nicht in `audit.log`, unter unserer App-Id,
authentifiziert über das ExApp-Geheimnis (nicht nutzergebunden). `message` ist ein flacher String,
Struktur muss also als JSON *im* String stehen.

**Verdikt:** wertvoll, weil unsere Einträge damit in der Datei landen, die der Administrator
ohnehin an sein SIEM weitergibt, mit demselben Umschlag wie alles andere. Aber: **eine
HTTP-Runde pro Eintrag** in den Nextcloud-Anfragepfad, kein Bündeln, und ein überlastetes oder
wartendes Nextcloud verliert Einträge still. Deshalb: **optional, per Admin-Schalter, best effort,
niemals die Primärsenke und niemals im synchronen Pfad eines Tool-Aufrufs** (Warteschlange plus
Hintergrund-Flush).

## B.3 Die Empfehlung, klar gesagt

| Rang | Senke | Zustand | Begründung |
|------|-------|---------|------------|
| 1 | **SQLite im Volume, append-only, hash-verkettet** | immer an | anwendungseigener Nachweis, überlebt Neustarts, prüfbar, kostet keine neue Abhängigkeit |
| 2 | **Eine JSON-Zeile je Tool-Aufruf nach stdout** | immer an | der Weg in die zentrale Protokollierung, und das ist die Senke, an der die BSI-Systematik hängt |
| 3 | **AppAPI-OCS-Log** | ab Werk aus, Admin-Schalter | für Administratoren, die es in `nextcloud.log` wollen; best effort |
| : | admin_audit, Activity, eigene PostgreSQL/MariaDB, OpenTelemetry-Logs-Pipeline | **nicht** | siehe B.2.3 und "What NOT to Use" |

**Und die Frage, wie sie gestellt wurde: was hält ein Administrator einer deutschen Behörde für
ein echtes Audit-Log?**

- **Hält er dafür:** die stdout-Zeile, sobald sie in seiner zentralen
  Protokollierungsinfrastruktur liegt, zusammen mit der hash-verketteten SQLite als
  anwendungsseitigem Nachweis. Das Paar ist verteidigbar.
- **Hält er nicht dafür:** SQLite allein (die geprüfte Anwendung besitzt den Speicher, und ein
  `docker volume rm` löscht ihn spurlos), stdout allein ohne zentrale Senke (lebt so lange wie der
  Container), den AppAPI-Log-Endpunkt allein (keine Zustellgarantie, und `nextcloud.log` ist die
  Betriebsprotokolldatei, nicht die Auditdatei).
- **Wonach er tatsächlich fragt, ist keine Technik.** Er fragt: ist die Zeit synchronisiert, ist
  der Feldsatz festgelegt und dokumentiert, gibt es eine Aufbewahrungsfrist und einen definierten
  Löschprozess, wer darf lesen, und ist gegen unkontrolliertes Löschen oder Verändern technisch
  vorgesorgt. Der IT-Grundschutz-Baustein **OPS.1.1.5 Protokollierung** verlangt eine zentrale
  Protokollierungsinfrastruktur (A6), das Löschen nach einem festgelegten Prozess und die
  technische Verhinderung unkontrollierten Löschens oder Veränderns; er verweist außerdem
  ausdrücklich auf Datenschutzrecht und Mitbestimmungsrechte. Für Bundesbehörden kommt der
  **BSI-Mindeststandard zur Protokollierung und Detektion von Cyberangriffen** hinzu, aktuell
  gefundene Fassung **2.1 (November 2024)**, die gegenüber 2.0 gerade die Speicherfristen und die
  Löschung konkretisiert hat.
- **Die Falle, die in Technik-Diskussionen nie vorkommt:** ein nutzerbezogenes Protokoll jedes
  Tool-Aufrufs ist eine **Verhaltens- und Leistungskontrolle**. In einer deutschen Behörde löst
  das die **Mitbestimmung des Personalrats** aus (BPersVG; in Unternehmen BetrVG § 87 Abs. 1
  Nr. 6). Ein Produkt, das das ohne dokumentierten Feldsatz, ohne Frist und ohne Schalter
  ausliefert, wird nicht am Administrator scheitern, sondern am Personalrat. Deshalb: fester,
  dokumentierter, minimaler Feldsatz und ein Abschalter.

## B.4 Feldsatz: minimal und verteidigbar

**Drin:** `ts` (UTC, RFC 3339 mit Millisekunden), `seq`, `user` (Nextcloud-Nutzer-Id),
`client_id` (der autorisierte OAuth-Client), `tool`, `outcome` (`ok` / `error` / `denied`),
`error_code`, `duration_ms`, `bytes_out`, `request_id`, `prev_hash`, `entry_hash`.

**Bewusst draußen:** Argumente, Ergebnisse, Dateinamen, Mail-Betreffe, Talk-Nachrichtentext.

Begründung, und sie ist dieselbe wie beim Owner-Entscheid gegen PII-Maskierung vom 14.08.:
Argumente sind Nutzinhalt. Nutzinhalt im Audit-Log macht aus einem Kontrollinstrument eine
zweite Kopie der Daten, mit anderer Aufbewahrungsfrist und anderem Leserkreis. Wer später
Argumente braucht, führt einen zweiten Detailgrad hinter einem eigenen Schalter ein; die Vorgabe
bleibt der schmale Satz.

## B.5 Der Einhängepunkt existiert im SDK bereits

`mcp` 2.x nimmt im Konstruktor `MCPServer(..., middleware=[...])` eine Folge von
`ServerMiddleware` entgegen: eine `async (ctx, call_next)`-Aufrufbarkeit, die **jede** eingehende
Nachricht umschließt, `ctx.method`, die rohen `ctx.params` und `ctx.request_id` sieht und einen
gescheiterten Handler als geworfenen `MCPError` erhält, also auch Fehler protokollieren kann.
Das SDK hängt selbst zwei davor (`OpenTelemetryMiddleware`, dann `RequestStateBoundary`);
unsere kommt danach. Es gibt zusätzlich die Extension-Schnittstelle nach SEP-2133 mit einem
`intercept_tool_call`, die aber mehr Vertrag ist, als wir brauchen.

**Der Vorbehalt, wörtlich aus dem Quelltext von 2.1.1 und 2.0.0:**

> "Provisional - the signature may change in a 2.x minor release; see the middleware guide."

Das ist kein Argument gegen den Haken, sondern eines für einen **dünnen Adapter**: ein Modul, das
das SDK-Protokoll erfüllt und sofort an unsere eigene, stabil signierte Audit-Funktion delegiert.
Ändert sich die Signatur in einem 2.x-Minor, ist genau eine Datei betroffen.

**Nebenbefund:** `opentelemetry-api>=1.28.0` ist bereits transitive Abhängigkeit von `mcp` 2.x.
Wir ziehen trotzdem **nicht** `opentelemetry-sdk` (1.44.0) nach. Ein Audit-Log ist kein Tracing:
Traces werden gesampelt, ein Audit-Log darf nicht sampeln.

## B.6 Zwei harte Berührungen mit vorhandenem Code

1. **`exapp/purge.py`.** Purge beendet jede Verbindung und löscht den Datenschlüssel; sein
   Docstring begründet die nicht verhandelbare Reihenfolge. Das Audit-Log darf dabei **nicht**
   mitgehen, sonst verschwindet der Nachweis über eine Verbindung zusammen mit der Verbindung.
   Umgekehrt bricht ein Audit-Log, das eine Deinstallation überlebt, das Erfolgskriterium 2 aus
   v1.0 ("eine Deinstallation entfernt alle Daten") und die Aussage in `docs/privacy.md`. **Das
   ist eine Entscheidung, die der Milestone ausdrücklich treffen muss, kein Fehler, den man
   später findet.** Empfehlung: das Audit-Log überlebt Purge, `docs/privacy.md` und
   `docs/uninstall.md` sagen das, und der Aufbewahrungs-Job ist der einzige automatische Löscher.
2. **Der Enterprise-Text.** READMEs und Store-Beschreibungen in EN/DE/FR nennen Audit-Log,
   Gruppen-Policies und SSO ausdrücklich als geplant und heute nicht vorhanden. Sobald das
   Audit-Log existiert, müssen alle sechs Fassungen plus `changelog.ts`-Äquivalent
   (`CHANGELOG.md`) im **selben** Release mitziehen, sonst wird eine wahre Aussage falsch. Das
   steht in PROJECT.md und gehört in den Phasenplan, nicht in einen Nachzieher.

---

## Recommended Stack

### Core Technologies

Unverändert. Keine Zeile in `[project.dependencies]` ändert sich.

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| httpx | >=0.28,<0.29 (schon drin) | Einziger HTTP-Client, jetzt auch für OpenProject API v3 und den AppAPI-Log-Endpunkt | OpenProject ist HAL+JSON über HTTP. Der einzige PyPI-Client mit passender Frische pinnt `httpx<0.26` und ist damit nicht installierbar; die anderen sind tot oder `requests`-basiert (A.4). Der vorhandene `AppApiAuth` und der SSRF-Schutz aus v1.1 tragen unverändert (HIGH) |
| sqlite3 (stdlib) | Python 3.13 | Primärsenke des Audit-Logs, append-only, hash-verkettet | Ist in diesem Projekt keine neue Technologie, sondern das Muster aus `oauth/store.py`: WAL, `busy_timeout`, eine Verbindung je `asyncio.to_thread`. Zweite Datei auf demselben Volume (HIGH) |
| hashlib (stdlib) | Python 3.13 | `entry_hash`/`prev_hash` der Beweismittelkette | Die 30 Zeilen, die aus einer Tabelle ein Audit-Log machen. Kein Zukauf (HIGH) |
| logging (stdlib) + eigener JSON-Formatter | Python 3.13 | Zweitsenke stdout, eine JSON-Zeile je Tool-Aufruf | Das Projekt nutzt bereits `logging.getLogger` in jedem Modul; es ändert sich nur der Handler in den Entry-Points. Feldnamen an Nextclouds JSON-Zeilen anlehnen (`reqId`, `time`, `user`, `app`, `message`) spart dem Administrator eine Parser-Regel (HIGH) |
| mcp[cli] | >=2.0,<3 (schon drin; Lock steht auf 2.0.0, PyPI bei 2.1.1) | `MCPServer(middleware=[...])` als Einhängepunkt für jeden Tool-Aufruf | Der Haken existiert und sieht Methode, rohe Parameter, Request-Id und geworfene `MCPError`. Ausdrücklich als "Provisional" markiert, deshalb hinter einem dünnen Adapter (B.5) (HIGH) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (keine) | - | - | - |

Bewusst leer, zum dritten Mal in Folge. Die Kandidaten, die man in dieser Domäne reflexartig
zieht, stehen unten mit Begründung in "What NOT to Use".

Der einzige Kandidat, der eine ehrliche Diskussion verdient hat, ist `python-json-logger` 4.2.0
(veröffentlicht 2026-08-15, keine Abhängigkeiten, Python >=3.10). **Empfehlung trotzdem: nein.**
Der Feldsatz ist ohnehin fest und unser eigener (B.4), die Formatter-Ableitung ist rund 40 Zeilen,
und jede direkte Abhängigkeit kostet einen Eintrag in `docs/dependency-audit.md`, ein
Lock-Update, eine Lizenzprüfung und eine Zeile Angriffsfläche im Container-Image.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| respx (schon im dev-group) | Contract-Tests für die OpenProject-Endpunkte ohne Netz | Fünf Endpunkte, jeder mit Happy/401/403/404/HTML-Login. Dazu die beiden well-known-Dokumente als Fixtures, weil der Discovery-Pfad eigene Fehlerfälle hat |
| Compose-Dienst `openproject/openproject:17` | Der Spike-Messstand | Ein Dienst neben `compose.test.yml`, exakt das GreenMail-Muster aus v1.2. **Nicht** ein openDesk-Cluster (A.8) |
| Bestehendes AST-Grep-Gate | Hält die Write-Grenze und die Identitätsgrenze | Muss um zwei Nadelgruppen wachsen: jeden OpenProject-Schreibverb (`POST/PATCH/DELETE` auf `/api/v3/...`) und **jede Verwendung der globalen Basic-Auth und des Client-Credentials-Flusses**. Der zweite Teil ist neu in seiner Art: das Gate hat bisher Zerstörung verhindert, hier verhindert es Identitätsverlust |
| Prüfkommando für die Hash-Kette | Integritätsnachweis, den ein Auditor selbst fahren kann | Läuft die Kette einmal durch und meldet die erste Bruchstelle. Gehört in die Doku, nicht nur in die Tests |
| Zeitsynchronisation dokumentieren | Erste Frage jedes Auditors | Der Container erbt die Uhr des Hosts. Ein Satz in der Doku, kein Code |

---

## Installation

```bash
# Nichts. Zum dritten Mal in Folge.
uv sync
```

`pyproject.toml` bleibt unverändert. Kein `uv add`, kein Lock-Update, kein neuer Eintrag in
`docs/dependency-audit.md`.

Für die Spike-Stufe kommt ein Compose-Dienst dazu (kein Python-Paket):

```yaml
# compose.openproject.yml, nur fuer den Spike
openproject:
  image: openproject/openproject:17
  environment:
    OPENPROJECT_HOST__NAME: "localhost:8081"
    OPENPROJECT_HTTPS: "false"
    OPENPROJECT_DEFAULT__LANGUAGE: "en"
  ports: ["8081:80"]
```

**Was sich dagegen sehr wohl ändert: `appinfo/info.xml`.** Bis zu sieben neue
`<environment-variable>`-Einträge kommen zu den heutigen fünf hinzu:

| Variable | Zweck |
|----------|-------|
| `NC_MCP_AUDIT` | Audit-Log an/aus |
| `NC_MCP_AUDIT_RETENTION_DAYS` | Aufbewahrungsfrist, ohne die es kein Löschkonzept gibt |
| `NC_MCP_AUDIT_TO_NEXTCLOUD` | dritte Senke (AppAPI-OCS-Log), ab Werk aus |
| `NC_MCP_OPENPROJECT_URL` | Basis-URL der OpenProject-Instanz |
| `NC_MCP_OPENPROJECT_CLIENT_ID` | aus der vom OP-Admin angelegten OAuth-Anwendung |
| `NC_MCP_OPENPROJECT_CLIENT_SECRET` | dito |
| `NC_MCP_OPENPROJECT_ALLOW_APIKEY` | ob der persönliche API-Token als Rückfall zugelassen ist |

Das ist der teuerste Posten dieses Milestones, und er ist kein Code: jede Variable berührt das
Variablen-Gate in `tests/unit/test_exapp_env_setup.py`, das Admin-Settings-Formular, drei READMEs,
drei Store-Beschreibungen und den Store-Upload. **Empfehlung: auf drei zusammenstreichen**
(`NC_MCP_AUDIT`, `NC_MCP_AUDIT_RETENTION_DAYS`, `NC_MCP_OPENPROJECT_URL`) und den Rest im ersten
Wurf weglassen, indem der Spike den API-Token-Weg als Standard nimmt und der OAuth-Weg erst
kommt, wenn ein echter Kunde eine OpenProject-Administration hat.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Eigene OpenProject-Tools in unserer ExApp | Auf den OpenProject-eigenen MCP-Server verweisen und gar nichts bauen | Wenn der Spike zeigt, dass der Kunde openDesk **EE** fährt (also den Enterprise-Token hat) und sein Client zwei MCP-Server verträgt. Dann ist der OpenProject-Server näher an der Quelle, wird gepflegt und kann ab 17.8 schreiben. Das ist ein legitimes Spike-Ergebnis, kein Scheitern (A.5) |
| OAuth-Autorisierungscode gegen OpenProject | Persönlicher API-Token je Nutzer | Wenn kein OpenProject-Administrator erreichbar ist. Empfehlung: **im ersten Wurf sogar zuerst**, weil er ohne fremde Mitwirkung messbar ist |
| `select=` serverseitig | Volle HAL-Antwort holen und selbst projizieren | Nur für `updatedAt` und andere nicht selektierbare Felder. Dann `filters=` statt `select=` prüfen, bevor man 3691 Bytes bezahlt (A.7) |
| Hash-Kette in SQLite | Signierte Einträge (HMAC mit einem Schlüssel außerhalb des Containers) | Wenn ein Kunde ausdrücklich Manipulationssicherheit gegen den Betreiber verlangt. Braucht eine Schlüsselverwahrung außerhalb des Volumes und ist damit ein eigener Milestone, nicht v1.5 |
| Zwei Senken (SQLite + stdout) | Nur stdout, wenn der Kunde nachweislich eine zentrale Log-Infrastruktur betreibt | In einem gut geführten openDesk-Cluster ist die K8s-Log-Pipeline die bessere Ablage als unser Volume. Die SQLite bleibt trotzdem, weil sie die Instanz ist, die wir selbst prüfen können |
| AppAPI-OCS-Log als dritte Senke | Weglassen | Wenn die Messung zeigt, dass die Runde je Eintrag den Tool-Aufruf spürbar verlangsamt und der Puffer den Aufwand nicht wert ist. Dann ehrlich weglassen statt halb einbauen |
| Blankes OpenProject im Container als Messstand | Ein openDesk-Cluster stellen | Erst, wenn ein konkreter Kunde oder ZenDiS eine Instanz zur Verfügung stellt. Selbst aufbauen ist ein Milestone, kein Spike (A.8) |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `pyopenproject` | Letzter Upload 2021-03-26, `requests~=2.25.1` und `PyYAML~=5.3.1` hart gepinnt | httpx |
| `openproject` (PyPI) | Pinnt `httpx>=0.25,<0.26`. **Direkter Konflikt** mit unserem `httpx>=0.28,<0.29`; nicht auflösbar, ohne den Kernstack zurückzudrehen | httpx |
| `openproject-api-client` | Frisch (0.4.0 vom 2026-08-19), aber drei Releases insgesamt, unbekannter Herausgeber, und zieht `requests` in ein reines httpx-Projekt | httpx |
| `openproject-mcp` / `mcp-openproject` | Sind selbst MCP-Server, keine Client-Bibliotheken. Als Abhängigkeit sinnlos, als Vorbild allenfalls interessant | eigene Tools oder der offizielle OpenProject-MCP |
| **Globale Basic-Auth von OpenProject** (`OPENPROJECT_AUTHENTICATION_GLOBAL__BASIC__AUTH_*`) | Ein instanzweites Geheimnis, das nicht der angemeldete Nutzer ist. openDesk setzt es, das macht es verfügbar und damit gefährlich. Bricht das Kernversprechen in einer Zeile | OAuth je Nutzer oder persönlicher API-Token |
| **OpenProject Client-Credentials-Fluss / "Client Credentials User"** | Feste Identität für alle Nutzer. Steht in `grant_types_supported`, ist aber genau das, wogegen dieses Produkt antritt | dito |
| **AppAPI `TalkBotsService`-Denkmuster übertragen** (ein technischer Dienstnutzer in OpenProject) | Derselbe Fehler wie in v1.2 abgelehnt: eigene Identität statt Durchgriff | Impersonation beziehungsweise nutzergebundene Tokens |
| OIDC-Token-Exchange über `user_oidc` | Ist ein PHP-Ereignis ohne OCS-Route und braucht das Login-Token in einer Browser-Session, die es bei einem MCP-Aufruf nicht gibt (A.3) | OAuth gegen OpenProject |
| **In `admin_audit` hineinschreiben** | Es gibt keinen Weg. `apps/admin_audit` hat keinen Controller, keine Route und trägt `.noopenapi`; es ist ein PHP-Ereignis-Zuhörer. Der einzige Weg wäre eine PHP-Begleit-App, die die MCP-only-Positionierung zerstört | eigene SQLite + stdout, optional der AppAPI-Log-Endpunkt |
| **Activity-App als Audit-Senke** | Einziger POST ist der Föderations-Empfänger `RemoteActivity#receiveActivity` an ein Remote-Share-Token. Keine allgemeine Schreib-API. Außerdem ein Nutzer-Feed, den der Auditierte abschalten kann | dito |
| AppAPI-OCS-Log als **Primärsenke** | Eine HTTP-Runde je Eintrag in den Nextcloud-Anfragepfad, kein Bündeln, stiller Verlust bei Wartung oder Last. Schreibt außerdem in `nextcloud.log`, nicht in `audit.log` | SQLite als Primärsenke, OCS-Log als abschaltbare Drittsenke |
| `structlog` (26.1.0) | Für ein Team die richtige Wahl, für einen Solo-Betrieb mit **einem** Formatter ein neues Denkmodell in jedem Modul, dauerhaft | stdlib `logging` + eigener JSON-Formatter |
| `python-json-logger` (4.2.0) | Sauber und aktuell, aber ersetzt 40 Zeilen und kostet einen Eintrag in `docs/dependency-audit.md`, ein Lock-Update und eine Lizenzprüfung | dito |
| `loguru` (0.7.3, letzter Upload 2024-12-06) | Ersetzt das stdlib-Logging statt es zu ergänzen, und die Bibliothek ist seit über einem Jahr ohne Release | dito |
| `aiosqlite` (0.22.1) | Schon in `oauth/store.py` mit Begründung abgelehnt: jeder Aufruf läuft in `asyncio.to_thread` mit eigener Verbindung, was genau das ist, was der Wrapper hinzufügen würde | stdlib `sqlite3` |
| `opentelemetry-sdk` (1.44.0) | Traces werden gesampelt, ein Audit-Log darf nicht sampeln. Die `opentelemetry-api` ist ohnehin schon transitiv über `mcp` da; der SDK-Zukauf brächte einen Exporter, einen Collector und einen Betriebsaufwand, den ein Solo-Entwickler nicht trägt | zwei Senken, wie oben |
| Eigene PostgreSQL/MariaDB für die ExApp | Ein zweiter Zustandsspeicher, ein zweites Backup-Thema, ein zweiter Compose-Dienst und ein Ein-Klick-Versprechen weniger. Für einige tausend Zeilen am Tag völlig unverhältnismäßig | SQLite auf dem Volume |
| Tool-Argumente und Ergebnisse ins Audit-Log | Macht aus dem Kontrollinstrument eine zweite Kopie der Nutzdaten, mit anderer Frist und anderem Leserkreis. Gleiche Logik wie der Owner-Entscheid gegen PII-Maskierung | fester schmaler Feldsatz (B.4) |
| Ein openDesk-Cluster als Spike-Messstand aufsetzen | Helmfile, Kubernetes, Nubus, neun Komponenten. Das ist ein Milestone | `openproject/openproject:17` als Compose-Dienst |

---

## Stack Patterns by Variant

**Wenn OpenProject gar nicht konfiguriert ist (der Normalfall, und er bleibt es lange):**
- Kein Tool verschwindet, kein `tools/list` ändert sich. Dieselbe Regel wie bei Notes/Deck/Talk:
  statisch gelistet, mit einer Erklärung antworten. Eine credential-abhängige Tool-Liste
  zerschießt Caching, Budget-Gate und jeden Client, der Listen persistiert.
- `prepare_context` lässt das Bein weg und sagt es, wie bei jeder anderen fehlenden Familie.

**Wenn OpenProject da ist, der Nutzer aber keine Autorisierung hat:**
- Die Verbindungsseite in den Nextcloud-Settings bekommt eine zweite Zeile ("OpenProject
  verbinden"), genau das Muster, das seit v1.0 für Nextcloud-Verbindungen steht. Pause und
  Widerruf gelten dann an denselben Autorisierungspunkten.
- Tool-Antwort ist eine Erklärung mit dem Verbindungs-Link, kein Fehler.

**Wenn wir in einem openDesk-Cluster laufen:**
- Kein App Store, also kein Ein-Klick. `manual_install`-Daemon plus K8s-Deployment, per `occ`
  registriert. Die Doku muss diesen Weg als eigenen Abschnitt bekommen, sonst ist die
  Store-Beschreibung dort schlicht unzutreffend.
- Der AppAPI-Container-Log-Download funktioniert dort nicht (kein Docker). Dafür ist die
  K8s-Log-Pipeline die bessere Zweitsenke. Das ist ein Tausch, kein Verlust.
- Talk und Kontakte sind aus. Von 21 Tools bleiben weniger. Ehrlich benennen.
- openDesk **CE**: kein OpenProject-Enterprise-Token, also kein OpenProject-MCP und kein
  OIDC-SSO-Speichermodus. openDesk **EE**: beides da. Das ist die Verzweigung, die den Wert
  unseres Bausteins bestimmt.

**stdio- und Passthrough-Modus:**
- Audit-Log: identisch, nur ohne `client_id` (im stdio-Modus gibt es keinen OAuth-Client). Das
  Feld bleibt im Satz und ist `null`, statt den Satz zu variieren.
- OpenProject: identisch. Es wechselt nur, woher das Token kommt.

---

## Version Compatibility

| Komponente | Kompatibel mit / Stand | Notizen |
|------------|------------------------|---------|
| OpenProject | **17.7.2** (2026-08-13) aktuell, 17.8.0 unmittelbar bevorstehend | API v3 ist stabil und rückwärtskompatibel; OpenProject sagt das ausdrücklich zu |
| OpenProject API v3 | einzige allgemeine API, OpenAPI 3.1, HAL+JSON | kein v4 in Sicht |
| OpenProject `/mcp` | ab **17.2**, Enterprise-Add-on, "beta" in der Admin-UI; Schreiben ab **17.8** | Scope `mcp`; in openDesk CE nicht verfügbar |
| OpenProject `.well-known` (RFC 8414 / RFC 9728) | live auf 17.x vorhanden | **ohne** `registration_endpoint`, **ohne** `code_challenge_methods_supported` |
| OpenProject API-Token als Bearer | ab **17.2** (#71147) | davor nur Basic `apikey:<token>` |
| openDesk | **1.18.0** (2026-08-19) | Nextcloud 33.0.7, OpenProject 17.7.2, OX 8.51, Element 1.12.8/Synapse 1.157.2, Collabora 26.04.02, CryptPad 2026.5.1, Jitsi 2.0.11146, Nubus |
| openDesk Nextcloud-Werte | `appstore: false`, `spreed: false`, `contacts: false`, `adminAudit` schaltbar | Kein Store, kein Talk, keine Kontakte |
| Keycloak Standard Token Exchange (RFC 8693) | offiziell unterstützt ab **26.2** (Mai 2025), Schalter je Client | Nicht der Blocker; der Blocker sitzt in Nextcloud (A.3) |
| `user_oidc` | 8.12.0-dev, NC 29 bis 36 | Token Exchange nur als PHP-Ereignis, keine OCS-Route, braucht `store_login_token=1` und eine Session |
| `admin_audit` | **1.24.0** (NC 34), 3.0.0-dev.0 (master/NC 36) | Architektur in beiden identisch: Ereignis-Zuhörer, keine HTTP-Fläche |
| Nextcloud Audit-Konfiguration | `log_type_audit` (`file`/`syslog`/`systemd`/`errorlog`, Vorgabe `file`), `logfile_audit` (Vorgabe `[datadirectory]/audit.log`) | `admin_audit` bringt einen eigenen `Rotate`-Hintergrundjob mit |
| Activity-App | 7.0.0 (NC 34), 9.0.0-dev (master) | einziger POST ist der Föderations-Empfänger |
| AppAPI | 36.0.0-dev.0 (NC 36) | `POST /ocs/v1.php/apps/app_api/api/v1/log` mit `level`+`message`; Deploy-Daemons HaRP (empfohlen ab NC 32) und DSP (**Entfernung für NC 35 angekündigt**); `manual_install` existiert; Container-Log-Download nur bei `json-file`/`journald` |
| `mcp` | Lock 2.0.0, PyPI aktuell **2.1.1** (2026-08-25) | `MCPServer(middleware=...)` in beiden vorhanden, in beiden als "Provisional" markiert. Ein Bump auf 2.1.1 ist optional und gehört nicht in denselben Schritt wie das Audit-Log |
| `pyproject.toml` | **unverändert** | keine neue Abhängigkeit, kein Lock-Update |
| `appinfo/info.xml` | **geändert** | bis zu sieben neue Umgebungsvariablen; empfohlen auf drei kürzen |

---

## Offene Punkte, ehrlich benannt

1. **PKCE gegen OpenProject ist ungemessen (der wichtigste offene Punkt).** Die AS-Metadaten
   bewerben `code_challenge_methods_supported` nicht, die API-Einführung nennt PKCE trotzdem.
   Doorkeeper kann es. Unser gesamtes OAuth-Denkmodell setzt PKCE voraus. **Das muss die erste
   Messung des Spikes sein**, nicht die letzte.
2. **Token-Lebensdauer und Refresh gegen OpenProject ungemessen.** 17.2 nennt "Implement token
   refreshing and reduce token expiration time" (#68460). Ob ein Refresh-Token ohne
   `offline_access` ausgestellt wird und wie lange ein Access-Token lebt, weiß ich nicht.
3. **openDesk EE gegenüber CE: nur die Helm-Bedingung ist belegt, nicht die Praxis.** Ob ZenDiS im
   EE-Angebot tatsächlich einen OpenProject-Enterprise-Token ausliefert, konnte ich nicht
   verifizieren. **Frage 1 für den ISV-Call am 14.09.**
4. **`manual_install`-Daemon auf Kubernetes ungemessen.** Der Daemon-Typ existiert im Quelltext.
   Ob unsere ExApp damit sauber läuft, insbesondere ob `APP_PERSISTENT_STORAGE` und der
   Heartbeat-Pfad tragen, hat niemand geprüft. Für die openDesk-Erzählung ist das mindestens so
   wichtig wie die Auth-Frage.
5. **SSRF-Grenze gegenüber Nachbarkomponenten ungeprüft.** Unser Schutz aus v1.1 wurde gegen das
   offene Internet gehärtet. Eine Schwesterkomponente unter einem internen Dienstnamen könnte
   konstruktionsbedingt ausgesperrt sein. Billig zu messen, teuer zu übersehen.
6. **BSI-Mindeststandard-Version (MEDIUM).** 2.1 (November 2024) ist die neueste, die ich gefunden
   habe. Dass es zum Stand August 2026 keine 2.2 gibt, konnte ich nicht bestätigen.
7. **Die Paragrafenangabe (MEDIUM).** "§ 8 Abs. 1 Satz 1 BSIG" stammt aus dem Titel des
   BSI-Dokuments. Das BSIG wurde mit der NIS2-Umsetzung neu nummeriert. **Nicht ungeprüft in
   kundenseitigen Text übernehmen.**
8. **Wachstum der Audit-SQLite ungemessen.** Eine Obergrenze und ein Verhalten beim Erreichen
   (rotieren, ältestes verwerfen, oder verweigern) muss die Phase festlegen. Ein Volume, das
   volläuft, legt die ExApp still.
9. **Der Personalrats-Punkt ist keine Technikfrage und braucht eine Owner-Entscheidung.** Ob das
   Audit-Log ab Werk an oder aus ist, ist die Entscheidung, die über Anschlussfähigkeit in einer
   Behörde entscheidet. Meine Empfehlung wäre "ab Werk aus, mit einer Doku-Seite, die den
   Feldsatz und die Frist nennt", aber das ist eine Produktentscheidung, keine Stack-Entscheidung.

---

## Sources

**OpenProject, live gemessen am 2026-08-28 (HIGH)**
- `https://community.openproject.org/.well-known/oauth-authorization-server` : Scopes, Grant Types, kein `registration_endpoint`, kein `code_challenge_methods_supported`
- `https://community.openproject.org/.well-known/oauth-protected-resource` : zwei Authorization Server, `bearer_methods_supported`
- `POST https://community.openproject.org/mcp` unautorisiert : 401 mit `WWW-Authenticate: Bearer realm="OpenProject API", resource_metadata=..., scope="mcp"`
- `GET /api/v3`, `/api/v3/work_packages?pageSize=1`, `/api/v3/projects?pageSize=1`, dieselbe Abfrage mit `select=` : die Byte-Messungen in A.7 und die Fehlermeldung mit der `select`-Allowlist

**OpenProject, Quelltext und Doku (HIGH)**
- `opf/openproject` `docs/api/README.md` : vier API-Flächen, die drei well-known-Endpunkte
- `opf/openproject` `docs/api/apiv3/README.md` : OpenAPI 3.1, `/api/v3/spec.json`
- `opf/openproject` `docs/system-admin-guide/integrations/mcp-server/README.md` : `/mcp`, Scope `mcp`, API-Token- und OAuth-Weg, "confidential" als Pflicht, Antwortformate, Tool-Abschaltung
- `opf/openproject` `docs/system-admin-guide/authentication/oauth-applications/README.md` : Registrierungsdialog, `/oauth/authorize`, `/oauth/token`, Default-Scope `api_v3`, Client-Credentials-User
- `opf/openproject` `docs/release-notes/17-2-0/README.md` : MCP Server als Enterprise-Add-on eingeführt, #71147 API-Keys als Bearer, #68460 Token-Refresh
- `opf/openproject` `docs/release-notes/17-8-0/README.md` : `create_work_package`/`update_work_package`, Link-Pruning, Entfernung der Output-Schemata
- `opf/openproject` GitHub-Releases : 17.7.2 am 2026-08-13 als aktuellster Tag
- `https://www.openproject.org/docs/system-admin-guide/integrations/nextcloud/oidc-sso/` : Enterprise-Add-on, RFC 8693 oder Wide-Access-Tokens, RS256, RFC 9068, `offline_access`

**openDesk, Deployment-Repo `bmi/opendesk/deployment/opendesk` auf gitlab.opencode.de, Tag `v1.18.0` (HIGH)**
- `CHANGELOG.md` : Komponentenstände in 1.18.0 (Nextcloud 33.0.7, OpenProject 17.7.2, OX 8.51, Element 1.12.8/Synapse 1.157.2, Collabora 26.04.02, CryptPad 2026.5.1, Jitsi 2.0.11146), Hinweise auf CE/EE
- `helmfile/apps/openproject/values.yaml.gotmpl` : `OPENPROJECT_SEED__ENTERPRISE__TOKEN` nur bei `OPENDESK_ENTERPRISE=true`, `OMNIAUTH__DIRECT__LOGIN__PROVIDER: keycloak`, `OPENID__CONNECT_KEYCLOAK_ISSUER`, LDAP-Suchkonto, **globale Basic-Auth**, zentrale Navigation
- `helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl` : `appstore: enabled: false`, `spreed: false`, `contacts: false`, `integrationOpenproject` an, `adminAudit` schaltbar, `oidc`-Client `opendesk-nextcloud`
- `helmfile/apps/nubus/values-opendesk-keycloak-bootstrap.yaml.gotmpl` : deklarative Keycloak-Clients je Komponente mit rollengebundenen Client-Scopes; `functional.authentication.oidc.clients` als Betreiber-Erweiterungspunkt
- Tag-Liste des Repos : v1.18.0 vom 2026-08-19 als aktuellster Stand
- `https://docs.opendesk.eu/operations/architecture/` : Kubernetes/Helmfile, Nubus als IAM, Keycloak als OIDC-Provider, OpenLDAP, Intercom Service, geteilte Geheimnisse zwischen Backends

**Nextcloud- und AppAPI-Quelltext (HIGH)**
- `nextcloud/server` `apps/admin_audit/appinfo/info.xml` (stable34: 1.24.0; master: 3.0.0-dev.0) und `apps/admin_audit/lib/` : `AuditLogger`, `IAuditLogger`, `Listener/`, `Actions/`, `BackgroundJobs/Rotate`, `.noopenapi`; **kein Controller, keine Route**
- `nextcloud/server` `stable34/config/config.sample.php` : `log_type_audit`, `logfile_audit`, Vorgabewerte
- `nextcloud/activity` `appinfo/routes.php` und `appinfo/info.xml` (7.0.0 / 9.0.0-dev) : einziger POST ist `RemoteActivity#receiveActivity`
- `nextcloud/app_api` `appinfo/routes.php` und `lib/Controller/OCSApiController.php` : `POST /ocs/.../api/v1/log` mit `level`+`message`, `#[AppAPIAuth]`, schreibt mit `['app' => ex-app-id]`
- `nextcloud/app_api` `lib/Controller/ExAppsPageController.php::getAppLogs` : Container-Log-Download, nur `json-file`/`journald`
- `nextcloud/app_api` `README.md` : HaRP empfohlen ab NC 32, DSP abgekündigt mit Entfernung in NC 35; `manual_install` in `src/constants/daemonTemplates.js` und `lib/Command/Daemon/RegisterDaemon.php`
- `nextcloud/user_oidc` `appinfo/routes.php` (keine Token-Route im `ocs`-Block), `docs/token_exchange.md` (`ExchangedTokenRequestedEvent`, `store_login_token`, Session-Bindung), `appinfo/info.xml` (8.12.0-dev, NC 29 bis 36)

**Python-Ökosystem, PyPI-JSON-API am 2026-08-28 (HIGH)**
- `pyopenproject` 0.7.4 (2021-03-26), `openproject` 0.6.0 (2024-01-24, `httpx<0.26`), `openproject-api-client` 0.4.0 (2026-08-19, `requests`), `openproject-mcp` 1.0.2
- `structlog` 26.1.0 (2026-06-06), `python-json-logger` 4.2.0 (2026-08-15), `loguru` 0.7.3 (2024-12-06), `aiosqlite` 0.22.1, `opentelemetry-sdk` 1.44.0, `mcp` 2.1.1 (2026-08-25)
- Installiertes `mcp` 2.0.0 in `.venv` sowie `modelcontextprotocol/python-sdk` v2.1.1 : `ServerMiddleware` in `mcp/server/context.py`, `middleware`-Parameter in `MCPServer.__init__`, `OpenTelemetryMiddleware` in `mcp/server/_otel.py`, Extension-Schnittstelle SEP-2133 in `mcp/server/extension.py`, Wortlaut "Provisional - the signature may change in a 2.x minor release"

**Norm- und Rechtslage (MEDIUM)**
- BSI IT-Grundschutz-Kompendium, Baustein **OPS.1.1.5 Protokollierung**, Edition 2023 : A6 zentrale Protokollierungsinfrastruktur, Löschen nach festgelegtem Prozess, technische Verhinderung unkontrollierten Löschens oder Veränderns, Verweis auf Datenschutz- und Mitbestimmungsrecht
- BSI **Mindeststandard zur Protokollierung und Detektion von Cyberangriffen**, Version 2.1 (November 2024), verbindlich für Bundesbehörden; 2.1 konkretisiert Speicherfristen und Löschung gegenüber 2.0. Dass keine neuere Fassung existiert, ist **nicht** bestätigt
- Keycloak-Ankündigung "Standard Token Exchange is now officially supported in Keycloak 26.2" (Mai 2025) sowie "JWT Authorization Grant and Identity Chaining in Keycloak 26.5" (Januar 2026)

**Eigene Codebasis (HIGH)**
- `src/mcp_connector/oauth/store.py` : SQLite-Muster, WAL, `busy_timeout`, `asyncio.to_thread`, Begründung gegen `aiosqlite`
- `src/mcp_connector/config.py` : `APP_PERSISTENT_STORAGE`, `nc_app_<appid>_data`, uid 10001, fail-closed
- `src/mcp_connector/exapp/purge.py` : die nicht verhandelbare Löschreihenfolge und das Erfolgskriterium 2 aus v1.0
- `pyproject.toml`, `uv.lock` : heutiger Abhängigkeitsstand

---
*Stack research for: Nextcloud MCP-only ExApp, Milestone v1.5 (OpenProject-Spike, Audit-Log)*
*Researched: 2026-08-28*
