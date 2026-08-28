# Architecture Research

**Domain:** Zwei neue Fähigkeiten in einer ausgelieferten MCP-only-ExApp: ein System ausserhalb von Nextcloud (OpenProject) erreichen, und jeden Werkzeugaufruf protokollieren
**Researched:** 2026-08-28
**Confidence:** HIGH für die Codebasis-Nähte (gelesen, Datei und Zeile genannt), HIGH für die Token-Mechanik von `integration_openproject` und `user_oidc` (PHP-Quellcode gelesen), HIGH für die Middleware-Naht des MCP-SDK 2.x (installiertes Paket gelesen), MEDIUM für das Verhalten unter AppAPI-Impersonation (im Quellcode belegt, in dieser Topologie nicht gemessen, genau das ist der Spike), MEDIUM für openDesk-Betriebsdetails (Dokumentation, keine eigene Instanz)

**Kernaussage in vier Sätzen.** Die schwierige Frage bei OpenProject ist nicht "welches OAuth", sondern ob der Weg überhaupt an unserem Container vorbeiführt: es gibt in Nextcloud bereits einen per-Nutzer-Proxy nach OpenProject (`integration_openproject`, OCS-Routen unter `/ocs/v2.php/apps/integration_openproject/api/v1/...`), der mit dem Token des angemeldeten Nutzers spricht, und dieser Weg ist der einzige, bei dem das Sicherheitsversprechen wörtlich unangetastet bleibt und im Container kein einziges neues Geheimnis liegt. Alle direkten Wege (eigener OAuth-Client gegen OpenProject, Keycloak-Client, Service-Konto, per-Nutzer-API-Keys) verschieben Anmeldedaten in unseren Container und brechen die heute geltende Invariante "die Zieladresse ist die eine aus `NC_MCP_URL`", zwei davon brechen zusätzlich das Versprechen selbst. Der Spike ist billig und braucht kein openDesk: eine Docker-Nextcloud plus eine OpenProject-Community-Instanz plus `integration_openproject` im OAuth2-Modus, und er muss genau eine Sache beweisen, nämlich dass der Proxy auch dann antwortet, wenn die Anfrage nicht aus einer Browser-Sitzung kommt, sondern mit App-Passwort oder AppAPI-Impersonation, denn im OIDC-Modus von openDesk ist im Quellcode belegt, dass das nicht mehr gilt. Das Audit-Log ist von all dem unabhängig, hat mit `middleware=` am `MCPServer` genau eine richtige Naht, und seine eigentliche Architekturentscheidung ist nicht das Wo, sondern die Inhaltsminimierung: ein Satz ohne schützenswerten Wert braucht keinen Schlüssel, überlebt damit die Purge und die Löschung des Datenschlüssels, und genau das macht ihn revisionstauglich.

---

## Teil 0: Die Randbedingungen, die beide Features binden

Aus dem Code gelesen, nicht angenommen. Diese sieben Punkte entscheiden in beiden Teilen mit.

| # | Randbedingung | Beleg |
|---|---------------|-------|
| R1 | Der Dispatch ist heute ohne Zwischenschicht: `@mcp.tool(...)` plus `@graceful` je Funktion in `server/reg_*.py`, die Registrierungsmodule werden per `pkgutil` automatisch importiert. Zwischen Transport und Tool-Funktion sitzt nichts von uns. | `server/__init__.py:23-51`, `:68-99`, `:102-114`; `server/reg_deck.py:23-47` |
| R2 | Anmeldedaten entstehen **im Tool-Aufruf**, synchron, aus dem Kontext: `deps.resolve_clients(ctx)` als erste Zeile jedes Tools. Es gibt keinen Cache, kein Retry, kein Logging des Headers. | `deps.py:75-101`, `:153-186` |
| R3 | Die Zieladresse ist niemals ein Wert aus der Anfrage. In allen fünf Modi kommt `base_url` aus dem Deploy-Environment bzw. `NC_MCP_URL`, mit ausdrücklichem Kommentar. | `deps.py:177`, `:221`, `:284-286` |
| R4 | Die Identität wird **vor** jedem MCP-Code an der ASGI-Grenze aufgelöst und in `request.state` hinterlegt; der synchrone Credential-Layer liest sie nur noch. | `exapp/middleware.py:118-147`, `:214-235`; `deps.py:230-246` |
| R5 | Der Container hat einen persistenten Datenträger (`APP_PERSISTENT_STORAGE`) und darauf genau eine SQLite-Datei. Der Start bricht ab, wenn der Datenträger fehlt oder nicht schreibbar ist, weil ein Speicher im Container-Dateisystem "bis zum ersten Neustart alles richtig beantwortet". | `config.py:240-282`, `oauth/store.py:83`, `entry_exapp.py:332` |
| R6 | Der Container ist **kein PHP-Prozess**. Alles, was Nextcloud nur als PHP-Event oder OCP-Interface anbietet, ist für uns nicht erreichbar; erreichbar ist ausschliesslich, was eine HTTP-Route hat (OCS oder App-Route). Das ist die Randbedingung, an der der SSO-Weg in Teil A scheitert. | gesamte `nextcloud/clients/`-Schicht, `exapp/config_values.py:12-27` |
| R7 | Es gibt bereits einen Weg, eine Verwaltungshandlung ohne Web-Route anzubieten: eine occ-Kommando-Registrierung plus eine Route, die im Manifest **nicht** deklariert ist. Genau so ist die Purge gebaut, und die Nicht-Deklaration ist dort die Sicherheitskontrolle. | `exapp/occ.py:29-95`, `exapp/purge.py:13-22`, `:61` |

Zwei Zahlen als Rahmen: 21 Werkzeuge, Schema-Budget 15712 von 18000 Bytes. **Beide Features in diesem Meilenstein fassen das Budget nicht an**, weil weder der Spike noch das Audit-Log ein Werkzeug hinzufügt. Das ist ein Vorteil und sollte in der Roadmap stehen, weil er eine ganze Klasse von Nacharbeit (Toolzahl in drei READMEs, `info.xml`, `docs/`, Contract-Test) einspart.

---

# Teil A: OpenProject aus der ExApp erreichen

## A.1 Die Frage, präzise gestellt

Heute gilt: eine Anfrage bringt ihre Identität mit, der Server hält kein Geheimnis eines Nutzers länger als einen Aufruf (Ausnahme: das verschlüsselte App-Passwort einer OAuth-Verbindung im Speicher), und die Zieladresse ist eine Deployment-Entscheidung. OpenProject ist ein zweiter Host mit einer zweiten Identität. Die Frage lautet damit nicht "wie authentifiziere ich mich", sondern: **welcher Weg lässt R2 und R3 stehen, und was liegt danach im Container, das heute nicht darin liegt?**

## A.2 Systembild der Wege

```
                    MCP-Client (Claude, ChatGPT, MUCGPT)
                                  |
                   OAuth 2.1 / AppAPI-Impersonation
                                  |
+--------------------------------- v ------------------------------------+
|  ExApp-Container                                                        |
|                                                                         |
|  exapp/middleware.py  ->  deps.resolve_clients(ctx)  ->  NcClients       |
|                                  |                                      |
|                          tools/openproject.py [neu, frühestens v2.0]     |
|                                  |                                      |
|         +------------------------+---------------------------+          |
|         | Weg 0                  | Weg 1 / 2 / 3 / 4                    |
|         v                        v                                      |
|  nextcloud/clients/              nextcloud/clients/openproject.py        |
|  integration_openproject.py      (zweite Basis-URL, zweiter Credential)  |
+---------|--------------------------------------|-----------------------+
          |                                      |
          | OCS, base_url = NC_MCP_URL           | direkter Egress
          v                                      v
   +-------------------+                 +----------------------+
   |    Nextcloud      |  Nutzer-Token   |     OpenProject      |
   |  integration_     |---------------->|  /api/v3/...         |
   |  openproject      |  (in NC gehalten)|                     |
   +-------------------+                 +----------------------+
          ^                                      ^
          | OIDC-Sitzung                         | JWT aus Keycloak
          +-------------- Keycloak (openDesk) ---+
```

Weg 0 ist die einzige Linie, die den Container nicht verlässt, ausser über die Verbindung, die er ohnehin hat.

## A.3 Die fünf Wege im Vergleich

| | Weg 0: Proxy über Nextcloud | Weg 1: eigener OAuth-Client gegen OpenProject | Weg 2: Keycloak-Client, Autorisierungscode je Nutzer | Weg 3: Keycloak Token-Exchange / Service-Konto | Weg 4: per-Nutzer-API-Key, vom Nutzer eingefügt |
|---|---|---|---|---|---|
| **Wo liegt das Geheimnis** | in Nextcloud (`oc_preferences`, `integration_openproject`) | in unserem SQLite, AES-GCM, Datenschlüssel aus Nextcloud | wie Weg 1, plus Client-Secret im Deploy-Env | Client-Secret mit Impersonationsrecht im Container | wie Weg 1, aber ein Dauer-Key ohne Scopes |
| **Sieht der Assistent mehr als der Nutzer** | nein, unverändert | nein, aber zweite Einwilligung | nein | **ja**, der Container kann für beliebige Nutzer Token holen (Weg 3a) bzw. sieht alles des Dienstkontos (Weg 3b) | nein |
| **Container kompromittiert, was fällt** | nichts Neues: dieselben App-Passwörter wie heute | zusätzlich alle OpenProject-Refresh-Token aller verbundenen Nutzer | dito, plus ein IdP-Client | **die ganze Instanz**: wer das Secret hat, ist jeder Nutzer bzw. das Dienstkonto | zusätzlich alle API-Keys, und ein API-Key hat vollen Kontozugriff ohne Scope |
| **Bricht R3 (feste Zieladresse)** | nein | ja, zweite Basis-URL nötig (aus Admin-Settings, nie aus der Anfrage) | ja | ja | ja |
| **Braucht Egress aus dem Container** | nein | ja | ja | ja | ja |
| **Braucht Administration in OpenProject** | ja, aber sie existiert in openDesk bereits | ja, eine OAuth-Anwendung | ja, ein Keycloak-Client | ja, plus Impersonationsrecht | nein |
| **Funktionsumfang** | schmal: was die Integration proxyt (Arbeitspakete suchen und anlegen, Projekte, Zuweisbare, Status, Typen, Benachrichtigungen, Dateiverknüpfungen) | ganze API v3 | ganze API v3 | ganze API v3 | ganze API v3 |
| **Bricht bei openDesk-SSO** | **möglicherweise ja**, siehe A.4 | nein | nein | nein | nein |
| **Spike-Kosten** | niedrig, zwei Container | mittel, plus Browser-Flow | hoch, Keycloak nötig | hoch | niedrig |
| **Urteil** | **empfohlen für den Spike und für v2.0-Basis** | Rückfallweg, falls Weg 0 im SSO-Modus nachweislich bricht | nur mit openDesk-Betreiber, v2.0+ | **abgelehnt** | Notnagel, nicht empfohlen |

## A.4 Die Wege im Einzelnen

### Weg 0: über die Nextcloud-Integration, die es schon gibt

`nextcloud/integration_openproject` registriert einen Satz OCS-Routen, die Anfragen an OpenProject **mit dem Token des angemeldeten Nutzers** stellen. Aus `appinfo/routes.php` und `lib/Controller/OpenProjectAPIController.php` gelesen:

| Zweck | Route (Präfix `/ocs/v2.php/apps/integration_openproject`) | Verb |
|-------|----------------------------------------------------------|------|
| OpenProject-Adresse dieser Instanz | `/api/v1/url` | GET |
| Arbeitspakete suchen | `/api/v1/work-packages?searchQuery=...` | GET |
| Projekte | `/api/v1/projects` | GET |
| Zuweisbare eines Projekts | `/api/v1/projects/{projectId}/available-assignees` | GET |
| Status, Typ | `/api/v1/statuses/{id}`, `/api/v1/types/{id}` | GET |
| Benachrichtigungen | `/api/v1/notifications` | GET |
| Konfiguration | `/api/v1/configuration` | GET |
| Arbeitspaket anlegen | `/api/v1/create/work-packages` | POST |
| Datei verknüpfen, Verknüpfung lösen | `/api/v1/work-packages`, `/api/v1/file-links/{id}` | POST, DELETE |

Vier Befunde aus dem Quellcode, alle HIGH:

1. **Der Controller ist ein `OCSController`, die Methoden tragen `#[NoAdminRequired]`, aber überwiegend kein `#[NoCSRFRequired]`.** Das ist genau die Lage, die dieses Projekt bei Nextcloud Mail in v1.2 schon einmal gelöst und live bewiesen hat: `Request::passesCSRFCheck()` antwortet `true`, sobald der Header `OCS-APIRequest` gesetzt ist, und D-18 setzt ihn auf jedem Request. Der Weg ist also bereits einmal in dieser Topologie erprobt worden, nur nicht mit dieser App.
2. **`validatePreRequestConditions()` antwortet mit 401, wenn der Nutzer kein Token hat.** Das ist ein sauber unterscheidbares Signal "dieser Nutzer hat OpenProject nicht verbunden" und wird zum Fehlertext eines künftigen Werkzeugs, nicht zu einem 500.
3. **`getAccessToken($userId)` liest das Token aus den Nutzer-Einstellungen und erneuert es im OAuth2-Modus selbst** (`grant_type=refresh_token` gegen OpenProject, mit `openproject_client_id` und `-secret` aus der App-Konfiguration). Dafür ist **keine Browser-Sitzung nötig**. Das ist der Grund, warum Weg 0 im klassischen Zwei-Wege-OAuth2-Aufbau für uns funktionieren sollte.
4. **Im OIDC-Modus ist es anders, und das ist der kritische Befund.** `getOIDCToken()` löst das PHP-Event `OCA\UserOIDC\Event\ExchangedTokenRequestedEvent` aus. `user_oidc` beantwortet es in `TokenService::getExchangedToken()`, und diese Methode holt das Ausgangstoken **aus der PHP-Session** (`ISession`, `SESSION_TOKEN_KEY`) und wirft `TokenExchangeFailedException('Failed to exchange token, no login token found in the session')`, wenn dort keines liegt. Eine Anfrage, die mit App-Passwort oder AppAPI-Impersonation authentifiziert wurde, hat keine OIDC-Anmeldung und damit kein Ausgangstoken. Ergebnis: **im openDesk-Modus trägt Weg 0 nur so lange, wie das zwischengespeicherte Token (`token`, `token_expires_at` in den Nutzer-Einstellungen) noch gültig ist**, also typischerweise wenige Minuten nach der letzten Browsertätigkeit des Nutzers, danach 401.

Das ist keine Vermutung, das steht in beiden Quelldateien, und es ist genau die Art Befund, die einen Spike lohnt: er verwandelt "openDesk geht vermutlich" in "openDesk geht in dieser Betriebsart, in jener nicht, und hier ist die Zeile, die es entscheidet".

**Was Weg 0 architektonisch bedeutet.** Es entsteht ein neues Client-Modul `nextcloud/clients/integration_openproject.py` nach dem Muster von `clients/mail.py`, ein Eintrag in `capabilities.py` (die App veröffentlicht eine Capability, das ist im Spike zu prüfen; sonst zweiter Kanal `core/navigation/apps` wie bei Mail), und **nichts sonst**. Kein neuer Credential-Modus, kein zweiter Datenträger, keine zweite Basis-URL, kein Egress, kein Eintrag im Deploy-Environment. Das Sicherheitsversprechen bleibt wörtlich stehen, weil der Satz "der Assistent sieht nie mehr als der angemeldete Nutzer" von genau derselben Mechanik getragen wird wie heute: Nextcloud entscheidet, wer der Nutzer ist, und Nextcloud hält dessen Token.

### Weg 1: eigener OAuth-2.1-Client gegen OpenProject

OpenProject ist selbst ein OAuth-2.0-Autorisierungsserver: eine Anwendung wird in der Administration registriert (`client_id`, `client_secret`), unterstützt wird der Autorisierungscode-Fluss mit PKCE, Standard-Scope ist `api_v3`. Technisch ist das für dieses Projekt der bequemste Direktweg, weil die halbe Maschine schon steht: `oauth/connect.py`, `oauth/consent.py`, `oauth/store.py` mit verschlüsselten Geheimnissen, `oauth/crypto.py` mit dem Datenschlüssel aus Nextcloud, die Verbindungsseite unter `/connections`. Ein zweiter Verbindungstyp in derselben Tabelle wäre ein überschaubarer Bau.

Der Preis ist trotzdem hoch und er ist nicht technisch:

* **Zweite Einwilligung je Nutzer.** Der Ein-Klick-Anspruch (BL-06) verträgt keinen zweiten Browser-Fluss, den der Nutzer nur versteht, wenn er weiss, was OpenProject ist.
* **Zweite Basis-URL.** R3 sagt heute "die Zieladresse ist Deployment und niemals Anfrage". Das bleibt haltbar, wenn die OpenProject-Adresse aus den Admin-Settings kommt und mit derselben Härte geprüft wird wie `public_url` in `config_values._public_url`. Es braucht dann aber einen Contract-Test, der behauptet, dass keine Zieladresse aus einem Request stammt, weil die heutige Selbstverständlichkeit dann keine mehr ist.
* **Neuer Inhalt im Container.** Nach einer Kompromittierung liegen zusätzlich zu den App-Passwörtern die OpenProject-Refresh-Token aller verbundenen Nutzer im Volumen. Die Purge müsste einen zweiten Rückgabepfad bekommen (Token bei OpenProject widerrufen), sonst ist die Zusage "Deinstallation entfernt alle Daten" wieder unwahr.
* **Egress.** Der Container braucht Netzzugang zu einem zweiten Host. In abgeschotteten Behördennetzen ist das eine Freigabe, kein Selbstverständnis.

Urteil: der richtige Rückfallweg, wenn der Spike zeigt, dass Weg 0 im SSO-Modus nicht trägt und der ISV-Kanal keine bessere Antwort liefert. Nicht in v1.5.

### Weg 2: Keycloak-Client mit Autorisierungscode je Nutzer

OpenProject akzeptiert JWT-Bearer-Token eines konfigurierten OIDC-Providers (`Authorization: Bearer <jwt>`), der Scope-Claim muss `api_v3` enthalten. In openDesk ist Keycloak zentral und beide Komponenten vertrauen ihm bereits. Ein eigener Keycloak-Client, der den Nutzer per Autorisierungscode anmeldet, ist deshalb sauber: das Token trägt die Identität des Nutzers, das Versprechen hält, und ein Token statt eines Refresh-Tokens im Speicher ist die kürzere Halbwertszeit.

Dagegen spricht nur die Beschaffung: ein Client in einer fremden Keycloak-Realm ist eine Handlung des openDesk-Betreibers, nicht des Nutzers und nicht des Store-Installateurs. Das ist eine v2.0-Entscheidung mit einem Gesprächspartner, kein Spike. Genau deshalb gehört sie auf die Fragenliste für den 14.09.

### Weg 3: Token-Exchange mit Impersonation oder Dienstkonto

Beide Varianten scheitern am Versprechen, nicht an der Technik.

* **3a Token-Exchange durch uns**: Der Container hielte einen Keycloak-Client, der sich Token für beliebige Subjekte ausstellen lässt. Das ist die Definition eines "confused deputy" mit Berechtigung. Nach einer Kompromittierung ist der Container jeder Nutzer der Instanz. Der Satz "der Assistent sieht nie mehr als der angemeldete Nutzer" wäre dann nur noch eine Aussage über unser Wohlverhalten, nicht über die Bauart.
* **3b Dienstkonto / Client-Credentials / OpenProject-API-Key eines Administrators**: eine Identität für alle Nutzer. Damit sieht der Assistent per Konstruktion mehr als der angemeldete Nutzer, und zwar in jeder einzelnen Antwort. Ausgeschlossen.

Ergänzend, weil es dieselbe Klasse ist: **das MCP-Token des Clients darf niemals an OpenProject weitergereicht werden.** Die Autorisierungsspezifikation ist dazu normativ: "MCP servers MUST only accept tokens that are valid for use with their own resources. MCP servers MUST NOT accept or transit any other tokens." Ein Durchreichen wäre ein Spezifikationsbruch und zugleich der klassische Weitergabefehler.

### Weg 4: per-Nutzer-API-Key, vom Nutzer eingefügt

Formal versprechenstreu: der Key gehört dem Nutzer, wir speichern ihn wie ein App-Passwort. Praktisch schlecht: ein OpenProject-API-Key ist ein Dauerzugang mit vollen Kontorechten ohne Scope-Begrenzung, er lässt sich von uns nicht widerrufen, und er ist exakt das Anmeldedaten-Gebastel, gegen das dieses Projekt seit v1.0 positioniert ist ("spec-konformes OAuth statt App-Passwort-Gebastel"). Nur als dokumentierter Notausgang denkbar, nicht als Weg.

## A.5 Empfehlung

1. **Weg 0 ist der Spike-Gegenstand und die vorgesehene Basis für v2.0.** Er ist der einzige Weg, der das Versprechen nicht anfasst, den Container nicht anreichert und kein zweites Vertrauensverhältnis begründet.
2. **Weg 2 ist die openDesk-spezifische Ausbaustufe**, sobald ein Betreiber am Tisch sitzt. Auf die ISV-Fragenliste.
3. **Weg 1 ist der Rückfallweg** für Installationen ohne `integration_openproject`.
4. **Weg 3 ist abgelehnt** und sollte in `PROJECT.md` unter "Out of Scope" mit Begründung stehen, damit die Frage nicht in sechs Monaten unbewertet wiederkommt.
5. **v1.5 baut kein Werkzeug.** Der Meilenstein liefert einen Messbericht und eine Fragenliste, keinen `openproject_browse`-Tool. Das hält das Budget bei 15712 und die Aussage im Store wahr.

## A.6 Der Spike: was er kostet und was er beweisen muss

**Aufbau, ohne openDesk.** Eine Docker-Nextcloud (`juliusknorr/nextcloud-docker-dev`, im Projekt bereits als lokale Wegwerf-Instanz gesetzt) mit AppAPI und unserer ExApp, dazu eine OpenProject-Community-Instanz im selben Docker-Netz, dazu die App `integration_openproject` im Modus `authorization_method = oauth2` (Zwei-Wege-OAuth2, die dokumentierte Standardeinrichtung). Zwei Nextcloud-Konten, weil der Negativbeweis zwei braucht. Geschätzter Aufwand: ein Tag Aufbau, ein halber Tag Messung. Kein Keycloak, kein XWiki, kein OX.

**Ort im Repo:** eine neue Datei `tests/integration/test_openproject_proxy_matrix.py` nach dem Muster von `tests/integration/test_exapp_app_route_matrix.py`. Kein Produktionscode. Das ist der Grund, warum der Spike neben dem Audit-Log laufen kann, ohne dass sich die beiden berühren.

**Die sechs Behauptungen, die der Spike als wahr oder falsch zurückgibt:**

| # | Behauptung | Warum sie zählt |
|---|-----------|-----------------|
| S1 | `GET /ocs/v2.php/apps/integration_openproject/api/v1/url` antwortet unter reiner AppAPI-Impersonation mit 200 und der OpenProject-Adresse | beweist Erreichbarkeit und den CSRF-Pfad ohne Sitzung, das ist die Mail-Frage von v1.2 für eine neue App |
| S2 | Dieselbe Route antwortet für ein Konto **ohne** verbundenes OpenProject mit 401 statt mit Daten | beweist, dass die Berechtigung am Nutzer hängt und nicht an der App |
| S3 | Konto A sieht in `/api/v1/work-packages?searchQuery=...` kein Arbeitspaket, das nur Konto B sehen darf | der Zwei-Konten-Negativbeweis, den dieses Projekt für jede Familie führt |
| S4 | Nach künstlichem Ablauf (`token_expires_at` in die Vergangenheit gesetzt) antwortet der nächste Aufruf **wieder** mit 200 | **die entscheidende Behauptung**: sie beweist, dass die serverseitige Token-Erneuerung ohne Browser-Sitzung greift, und damit, ob Weg 0 dauerhaft trägt |
| S5 | Im Modus `authorization_method = oidc` schlägt derselbe Aufruf nach Tokenablauf fehl, mit der Meldung "no login token found in the session" | verwandelt den Quellcode-Befund in eine Messung; falls Keycloak nicht verfügbar ist, wird S5 als Quellcodebeleg plus offene Frage geführt, nicht als Behauptung |
| S6 | Eine Antwort von `/api/v1/work-packages` ist in kompakter Form unter X Bytes und trägt die Felder, aus denen ein späteres Werkzeug seine Projektion baut | die Vorarbeit für die v2.0-Budgetplanung, kostenlos im selben Lauf |

**Kontrollmessung, zwei Minuten, eigener Erkenntniswert:** ein `curl` aus dem laufenden ExApp-Container gegen `https://<openproject>/api/v3/work_packages`. Antwortet er, ist Egress vorhanden und Weg 1 bleibt als Rückfall offen; antwortet er nicht, ist Weg 0 nicht nur der schönere, sondern der einzige.

**Was der Spike ausdrücklich nicht beweist:** dass openDesk unsere ExApp überhaupt ausrollen darf (AppAPI-Verfügbarkeit im openDesk-Nextcloud), und wie die openDesk-Betreiber Deploy-Daemons handhaben. Das ist eine Betriebsfrage und gehört auf die Fragenliste.

## A.7 Fragenliste für den ISV-Call am 14.09.

Direkt aus den Befunden abgeleitet, jede Frage mit einem Grund, damit sie nicht wie Neugier klingt:

1. Läuft `integration_openproject` in openDesk im Modus `oauth2` oder `oidc`? (Entscheidet, ob Weg 0 dauerhaft trägt oder nach Tokenablauf bricht.)
2. Falls `oidc`: ist bekannt, dass `user_oidc` das Ausgangstoken nur aus der PHP-Session holt, und gibt es eine vorgesehene Lösung für Hintergrund- und Maschinenzugriffe? (Das ist zugleich unser stärkster fachlicher Beitrag zum Gespräch.)
3. Ist AppAPI in openDesk aktiviert, und welcher Deploy-Daemon ist vorgesehen? Kann eine Drittanbieter-ExApp überhaupt installiert werden, oder nur ein kuratierter Satz?
4. Gäbe es die Bereitschaft, für einen MCP-Zugang einen eigenen Keycloak-Client mit Zielgruppe OpenProject einzurichten (Weg 2)? Wer entscheidet das, ZenDiS oder der jeweilige Betreiber?
5. Welche Protokollierungspflichten gelten für Werkzeugaufrufe eines KI-Assistenten in einer Behördeninstallation, und in welchem Format erwartet der Betrieb sie (Datei, syslog, zentrale Sammlung)?
6. Gibt es eine Erwartung an Gruppen-Policies (welche Gruppe darf welche Werkzeugfamilie), und ist das eine Bedingung oder ein Wunsch?
7. Wie ist der Umgang mit der Mitbestimmung, wenn ein Audit-Log Nutzerverhalten protokolliert? (Siehe B.8; die Antwort entscheidet über den Vorgabewert unseres Schalters.)

## A.8 Was v1.5 an OpenProject ausdrücklich nicht anfasst

Kein Werkzeug, kein Client-Modul im Produktionscode, kein Eintrag in `capabilities.py`, keine zweite Basis-URL, kein zweiter Credential-Modus, keine Änderung an `deps.py`. Der Meilenstein produziert eine Integrationsdatei, einen Messbericht und eine Fragenliste. Alles andere ist v2.0.

---

# Teil B: Audit-Log über jeden Werkzeugaufruf

## B.1 Wo der Schreibpunkt sitzt: vier Nähte, an der echten Codebasis geprüft

| Naht | Wie | Sieht sie | Verpassbar | Urteil |
|------|-----|-----------|------------|--------|
| **N1 ASGI, in `RequireAppApi`** | eine Zeile mehr in `exapp/middleware.py:118` | HTTP-Anfrage, Identität, Statuscode. **Nicht** den Werkzeugnamen: der steckt im JSON-RPC-Rumpf, den diese Schicht nicht liest und nicht lesen darf, weil sie den Body sonst konsumiert | nein | falsch: sie protokolliert Anfragen, nicht Werkzeugaufrufe. Ein Streamable-HTTP-POST kann mehrere Nachrichten tragen |
| **N2 Dekorator je Werkzeug, neben `graceful`** | 21 Zeilen in sieben `reg_*.py` | alles, inklusive der Argumente in getippter Form | **ja**, Werkzeug 22 vergisst ihn | zweite Wahl. Nur mit Contract-Test tragbar, der behauptet, dass jede registrierte Funktion den Dekorator trägt |
| **N3 SDK-Extension, `intercept_tool_call`** | `MCPServer(extensions=[...])` | `tools/call`-Parameter und Ergebnis | nein | technisch richtig, aber sie **wirbt sich selbst**: `_apply_extension` trägt die Kennung nach `ServerCapabilities.extensions`, jeder Client sieht sie. Eine Protokollierung, die sich dem protokollierten Client ankündigt, ist eine Designentscheidung, die niemand verlangt hat |
| **N4 `ServerMiddleware`, `MCPServer(middleware=[...])`** | eine Zeile in `server/__init__.py:42` | `ctx.method`, `ctx.params` (roh, vor der Validierung), `ctx.request` (die Starlette-Anfrage), das Ergebnis, und eine geworfene `MCPError` | nein | **empfohlen** |

**Warum N4 und nicht N2.** Die Middleware wird vom SDK um *jede* eingehende Nachricht gelegt (`server/context.py:146-194`), sie steht innerhalb der SDK-eigenen Schichten und ausserhalb der Validierung, und sie ist eine einzige Registrierung. Damit ist "jeder Werkzeugaufruf" eine Eigenschaft der Bauart und keine Sammlung von 21 Zusagen. Genau derselbe Grund hat in v1.0 dafür gesprochen, die AppAPI-Prüfung an die Transportgrenze zu ziehen, statt sie 21-mal in die Tools zu schreiben.

**Zwei Feinheiten, die aus dem SDK-Quellcode kommen und die Umsetzung bestimmen:**

* `_handle_call_tool` (`mcpserver/server.py:415-424`) fängt jede Ausnahme ausser `MCPError` und macht daraus `CallToolResult(is_error=True)`. **Die Middleware sieht einen Misserfolg also in zwei Formen**: als Ergebnisobjekt mit `is_error` (jeder Werkzeugfehler, den `graceful` in eine `ValueError` verwandelt hat) und als geworfene `MCPError` (fehlende Anmeldedaten, pausierter Zugang). Wer nur das eine behandelt, protokolliert die Hälfte der Fehlschläge nicht.
* `ctx.request` ist die Starlette-Anfrage, die der Streamable-HTTP-Transport angehängt hat (`server/runner.py:315-340`). Das ist dieselbe Anfrage, in deren `state` `exapp/middleware.py:234` bereits die OAuth-Identität hinterlegt. **Damit braucht die Middleware keinen eigenen veränderlichen Zustand**, und das ist wichtig, weil `mcp` ein Modul-Singleton ist, das beim Import gebaut wird (`server/__init__.py:42`), während der Speicher erst in `entry_exapp.build_exapp_app` entsteht. Die Auflösung: die Middleware ist zustandslos und liest ihre Senke pro Anfrage aus `request.state`; `RequireAppApi` legt sie dort ab, so wie es die Identität heute schon tut. Kein Modul-Zustand, `test_no_destructive_calls.py::ALLOWED_MODULE_STATE` bleibt bei seinen zwei Einträgen.

**Skizze der Naht (kein fertiger Code, die Form ist der Punkt):**

```python
# server/__init__.py, eine Zeile am Konstruktor
mcp = MCPServer(..., middleware=[audit.AuditMiddleware()])

# audit/middleware.py
async def __call__(self, ctx, call_next):
    if ctx.method != "tools/call":
        return await call_next(ctx)          # nur Werkzeugaufrufe, nichts sonst
    sink = _sink_of(ctx)                     # aus request.state, None ausserhalb der ExApp
    started = time.monotonic()
    try:
        result = await call_next(ctx)
    except MCPError as exc:
        await _record(sink, ctx, outcome="refused", code=exc.code, ...)
        raise
    await _record(sink, ctx, outcome="error" if _is_error(result) else "ok", ...)
    return result
```

Zwei Regeln, die in dieser Funktion nicht verhandelbar sind: **die Protokollierung darf den Aufruf niemals scheitern lassen** (eine volle Platte ist kein Grund, eine Nutzerin nicht zu bedienen, ausser die Administration hat ausdrücklich "fail closed" gewählt), und **sie darf ihn nicht messbar verlangsamen** (ein Insert in eine WAL-SQLite über `asyncio.to_thread` liegt in derselben Grössenordnung wie der Nextcloud-Rundlauf, den der Aufruf ohnehin macht; ein zweiter Netzweg wäre es nicht).

## B.2 Was in einen Satz gehört

Ein Audit-Satz muss zwei gegenläufige Prüfungen bestehen: er muss einer Revision die Frage "wer hat wann womit was getan" beantworten, und er darf nicht selbst zur Kopie der Daten werden, die er schützt. Das ist die eigentliche Architekturentscheidung dieses Features.

| Feld | Beispiel | Warum |
|------|----------|-------|
| `ts` | `2026-08-28T09:14:02.318Z` | UTC, ISO 8601, sortierbar |
| `nc_user` | `k.cherif` | ohne den Nutzer ist der Satz wertlos. Pseudonymisierung wäre hier falsch: ein Audit-Log, das die handelnde Person nicht nennt, erfüllt seinen Zweck nicht |
| `channel` | `oauth` \| `appapi` | welcher der beiden Identitätskanäle. Trennt "ein Assistent hat gehandelt" von "die App hat für einen Nutzer gehandelt" |
| `client_id` | `mcp-client-4f2a...` bzw. die CIMD-Adresse | **der wichtigste Einzelwert nach dem Nutzer**: er sagt, welcher Assistent handelte. Kommt aus der Autorisierung, nicht aus einem Header |
| `auth_id` | Verbindungs-Id aus `authorizations` | verbindet den Satz mit der Verbindung, die die Nutzerin auf `/connections` sieht und beenden kann |
| `tool` | `talk_send_message` | der Werkzeugname aus `ctx.params["name"]` |
| `write` | `true` | aus der Annotation abgeleitet (`CREATE_ONLY` gegen `READ_ONLY`), nicht per Namensliste. Macht "zeig mir alle Schreibvorgänge" zu einer Spaltenabfrage |
| `outcome` | `ok` \| `error` \| `refused` | die drei Ausgänge aus B.1 |
| `error_class` | `tool_error` \| `upstream_timeout` \| `no_identity` \| `access_disabled` | eine kleine geschlossene Menge, niemals der Fehlertext, denn der kann fremde Prosa enthalten |
| `duration_ms` | `412` | Betriebswert und zugleich ein Missbrauchsindikator |
| `bytes_out` | `2841` | wie viel Inhalt den Assistenten erreicht hat. Der beste einzelne Abflussindikator, den es ohne Inhalt gibt |
| `args_digest` | `sha256:9f3c...` (gekürzt) | macht Wiederholungen und Schleifen sichtbar, ohne einen Argumentwert zu speichern |
| `args_safe` | `{"level":"messages","limit":25}` | **nur Schlüssel aus einer Erlaubnisliste je Werkzeug**, siehe unten |
| `session` | Transport-Sitzungs-Id, falls vorhanden | Aufrufe einer Sitzung zusammenbinden |
| `app_version` | `0.1.11` | ein Satz muss sagen können, welche Fassung ihn geschrieben hat |

**`args_safe` ist die Stelle, an der dieses Feature scheitern oder taugen kann.** Ein Audit-Log, das nur "notes_read wurde aufgerufen" sagt, beantwortet der Revision nichts. Eines, das die Argumente vollständig speichert, enthält Suchbegriffe, Nachrichtentexte, Notiztitel und Dateipfade und ist damit eine zweite, schlechter geschützte Kopie der Nutzerdaten. Die Auflösung ist eine **Erlaubnisliste je Werkzeug in der `reg_*`-Schicht**, dort wo das Schema ohnehin steht: Kennungen, Aufzählungswerte und Zahlen ja (`level`, `limit`, `board_id`, `conversation`, `message_id`, `table_id`), Freitext nein (`query`, `message`, `title`, `description`, `values`, `text`). Ein Contract-Test behauptet, dass jeder Parameter jedes registrierten Werkzeugs entweder auf der Erlaubnisliste steht oder ausdrücklich als Freitext markiert ist; ein neues Werkzeug ohne Entscheidung macht die Prüfung rot. Das ist dasselbe Muster wie das Budget-Gate: eine Zahl, die man anheben darf, aber nur bewusst.

Zwei Randfälle, die benannt gehören: eine Kennung kann selbst sprechen (ein Dateipfad in `files_read` ist eine Kennung **und** ein Inhalt), und `bytes_out` plus `args_digest` reichen für eine Missbrauchserkennung meistens aus. Empfehlung: Pfade und Dateinamen gehören **nicht** in `args_safe`, sondern nur ihre numerische Datei-Id, wo eine existiert.

## B.3 Was ausdrücklich nicht hinein darf

Anmeldedaten jeder Art (`Authorization`-Header, App-Passwörter, Token, auch gekürzt: T-01-21 gilt hier wortgleich), Antwortinhalte, Fehlertexte fremder Systeme, Nachrichtentexte, Suchbegriffe, IP-Adressen des Endnutzers (wir sehen ohnehin nur den Proxy), und der Inhalt von `ctx.params["arguments"]` in Rohform. Der Grund für die letzte Zeile ist nicht Sparsamkeit: `graceful` verwandelt Ausnahmen ausdrücklich in Sätze ohne URL, weil "eine URL ist eine unachtsame Änderung davon entfernt, Anmeldedaten zu tragen". Ein Audit-Schreiber, der Rohparameter mitschreibt, hebt diese Entscheidung an einer Stelle wieder auf, die niemand mehr liest.

## B.4 Wo es liegt

Der Container ist über eine Neuinstallation hinweg nicht dauerhaft, der Datenträger unter `APP_PERSISTENT_STORAGE` schon: die ganze OAuth-Persistenz dieses Projekts steht auf dieser Wette, und sie ist bei jedem Update seit v1.0 aufgegangen. Es braucht also keinen neuen Mechanismus, nur eine Entscheidung über die Datei.

**Empfehlung: zwei Senken, unterschiedliche Aufgaben.**

* **Senke 1, immer an: eine JSON-Zeile je Aufruf auf stderr.** `nextcloud/http.py:84-98` richtet das Logging bereits auf stderr ein (im stdio-Modus zwingend, weil stdout die Leitung ist). Eine Zeile pro Aufruf über einen eigenen Logger `mcp_connector.audit` mit einem Formatter, der nur `%(message)s` schreibt, ergibt maschinenlesbare JSON-Lines im Containerprotokoll. Der Vorteil ist gerade die Nicht-Dauerhaftigkeit des Containers: die Zeile verlässt ihn sofort und landet in dem Sammler, den der Betrieb ohnehin hat. Für eine Behördeninstallation ist das die revisionsfreundlichere Senke, weil sie ausserhalb der Reichweite des protokollierten Systems liegt.
* **Senke 2, abschaltbar: `audit.sqlite3` neben `oauth.sqlite3` im selben Datenträger.** Sie ist die abfragbare Senke für die occ-Leseroute und die einzige, mit der eine Administration ohne Log-Stack etwas anfangen kann.

**Warum eine zweite Datei und keine zweite Tabelle in `oauth.sqlite3`.** Drei Gründe, jeder für sich ausreichend:

1. **Die Purge darf das Audit nicht mitnehmen.** `exapp/purge.py` leert die Tabellen und löscht den Datenschlüssel, ausdrücklich in dieser Reihenfolge. Ein Audit-Log, das mit dem letzten Verbindungsabbau verschwindet, ist genau am Tag seiner Nützlichkeit weg.
2. **Der Datenschlüssel gehört nicht dazu.** Die Sätze aus B.2 enthalten nach der Inhaltsminimierung nichts, was einen Schlüssel braucht. Damit überleben sie auch die Löschung des Schlüssels, und die Kette "kein Geheimnis im Satz, also kein Schlüssel, also kein Verlust bei Purge" ist in sich schlüssig. Das ist ein Argument **für** die Minimierung, nicht nur ein Zugeständnis.
3. **Aufbewahrung und Kehren sind andere.** `store_opener` fegt beim ersten Öffnen abgelaufene Token weg. Ein Audit fegt nach einer eingestellten Frist in Tagen, und diese Frist ist eine Verwaltungsentscheidung, keine Protokolleigenschaft.

Schema, absichtlich klein: eine Tabelle, ein Index auf `(ts)`, ein Index auf `(nc_user, ts)`, dieselben drei Pragmas wie `oauth/store.py:1447-1466` (WAL, `busy_timeout`, `foreign_keys` hier ohne Wirkung, aber der Einheitlichkeit halber), `CREATE TABLE IF NOT EXISTS`, Spaltenmigration nach dem Muster von `_add_missing_columns`. Zwei Prozesse auf einer Datei sind ein unterstützter Fall (SRV-05), und ein Insert ohne Lesevorgang ist der billigste Schreiber, den SQLite kennt.

**Obergrenze statt unbegrenztem Wachstum.** Ein Satz kostet grob 250 bis 400 Bytes. Bei 50 Aufrufen je Nutzer und Tag und 200 Nutzern sind das rund 4 MB im Monat, also kein Problem, solange gefegt wird. Empfehlung: Vorgabe 90 Tage, einstellbar, plus eine harte Obergrenze in Sätzen, damit ein Amoklauf eines Clients den Datenträger nicht füllt, auf dem die OAuth-Datenbank liegt. **Diese Kopplung ist der einzige neue Betriebsrisikopfad, den das Feature einführt, und sie gehört benannt.**

## B.5 Wie eine Administration liest

**Empfohlen: ein occ-Kommando, kein Web-Endpunkt.** `exapp/occ.py` registriert heute genau ein Kommando, und `exapp/purge.py` beweist das Muster: die Route wird **nicht** im Manifest deklariert, weil ein deklarierter Pfad über den PHP-Proxy erreichbar wäre, der selbst gültige AppAPI-Header anhängt. Für einen Audit-Export gilt dasselbe eine Nummer schärfer: eine deklarierte Leseroute wäre eine öffentlich erreichbare Auskunft darüber, wer wann was getan hat.

```
occ mcp_connector:audit --since=2026-08-01 --user=<uid> --tool=<name> --limit=500 --format=jsonl
```

Drei Eigenschaften, die daran wichtig sind: der Aufrufer braucht Shell-Zugang zum Server, also ist die Berechtigungsfrage ohne eine einzige Zeile Code beantwortet (der Vergleich: eine Web-Seite müsste erst herausfinden, ob der angemeldete Nutzer Administrator ist, wofür es aus dem Container keinen sauberen, gecachten Weg gibt); die Ausgabe ist begrenzt, weil eine occ-Antwort über AppAPI durch einen JSON-Rumpf geht; und `hidden: 0` macht das Kommando in `occ list` auffindbar, was `exapp/occ.py:74` für die Purge ausdrücklich begründet.

Eine Seite unter `/connections` für die eigene Person ("welche Werkzeuge hat mein Assistent in den letzten sieben Tagen benutzt") ist eine gute spätere Ergänzung und ein starkes Transparenzargument, aber sie ist ein eigenes Stück Arbeit mit eigener Autorisierungsfrage. Nicht in v1.5.

## B.6 Manifest, Admin-Settings, Deployment: neu gegen geändert

### Neu

| Datei | Inhalt | Vorbild im Repo |
|-------|--------|-----------------|
| `src/mcp_connector/audit/__init__.py` | Satzform (`AuditRecord`), Ausgänge, Fehlerklassen | `oauth/store.py`-Zeilenobjekte |
| `src/mcp_connector/audit/middleware.py` | die `ServerMiddleware` aus B.1 | `exapp/middleware.py` |
| `src/mcp_connector/audit/store.py` | `audit.sqlite3`, Insert, Abfrage, Kehren | `oauth/store.py` |
| `src/mcp_connector/audit/sink.py` | stderr-JSON-Lines-Senke plus die Auswahl der Senken | `nextcloud/http.py::configure_logging` |
| `src/mcp_connector/audit/redaction.py` | Erlaubnisliste je Werkzeug, `args_digest` | neu, kein Vorbild |
| `src/mcp_connector/exapp/audit_read.py` | die undeklarierte Route hinter dem occ-Kommando | `exapp/purge.py` |
| `tests/contract/test_audit_coverage.py` | behauptet: jedes registrierte Werkzeug hat eine Argumentklassifikation, und die Middleware ist am Serverobjekt registriert | `tests/contract/test_tool_surface.py` |
| `tests/unit/test_audit_*.py` | Satzbildung, Schwärzung, Speicher, Kehren, beide Fehlerformen aus B.1 | die 60 vorhandenen Unit-Dateien |
| `docs/audit.md` | Felder, Aufbewahrung, Leseweg, Rechtslage | `docs/oauth-setup.md` |

### Geändert

| Datei | Änderung | Risiko |
|-------|----------|--------|
| `server/__init__.py:42` | `middleware=[...]` am Konstruktor | niedrig, aber es ist die eine Zeile, die alles trägt: ein Contract-Test muss ihre Anwesenheit behaupten |
| `exapp/middleware.py` | legt die Audit-Senke und die aufgelöste Identität (auch die des AppAPI-Zweigs, die heute nicht in `request.state` liegt) in `request.state` ab | mittel: der AppAPI-Zweig hinterlegt heute nichts, das ist eine echte Verhaltensänderung an der Sicherheitsgrenze und braucht einen eigenen Test |
| `entry_exapp.py:117-128` | baut die Audit-Senke wie den Store und reicht sie an `RequireAppApi` | niedrig, exakt das Muster von `access_check` |
| `exapp/config_values.py:110` | `CONFIG_KEYS` wächst von sechs auf sieben bis acht Einträge, `KEY_TO_ENV` mit | niedrig, aber das Feld-Id-gleich-Konfigurationsschlüssel-Gesetz gilt, und ein Test hält die Gleichheit |
| `exapp/admin_settings.py` | ein bis zwei Felder mehr; der Tupel-Auspack in `form_scheme` (`admin_settings.py:101-108`) muss mitwachsen | niedrig, mechanisch |
| `exapp/ui/strings.py` | Titel und Beschreibungen der neuen Felder, dreisprachig, mit dem Mitbestimmungshinweis aus B.8 | niedrig |
| `config.py` | ein bis zwei `ENV_`-Konstanten plus Leser, Muster `talk_send_enabled` | niedrig |
| `entry_exapp.py:322-323` | falls der Schalter im Tool-Pfad gelesen werden muss: er muss es **nicht**, die Middleware sieht das aufgelöste Environment über die Senke. Der Talk-Send-Sonderfall wiederholt sich hier also **nicht**, und das ist ausdrücklich festzuhalten | niedrig, aber leicht falsch zu machen |
| `exapp/occ.py` | `command_scheme()` wird zu einer Liste von Kommandos; `register_occ_commands` läuft über sie | niedrig; die Funktion heisst schon im Plural |
| `exapp/purge.py` | eine ausdrückliche Entscheidung plus Test: die Purge lässt `audit.sqlite3` in Ruhe, und der Kommandotext sagt das | mittel: hier steht heute eine Zusage "entfernt alle Daten", die präzisiert werden muss |
| `appinfo/info.xml` | **kein neuer `<route>`** (das ist die Kontrolle, siehe B.5), aber die Beschreibung in EN/DE/FR und der Enterprise-Absatz müssen mitziehen, sobald das Audit existiert; `<version>` | mittel: `PROJECT.md` nennt genau das, "sonst wird eine wahre Aussage falsch" |
| `README.md`, `README.de.md`, `README.fr.md` | Enterprise-Absatz: Audit-Log wechselt von "geplant" nach "vorhanden, optional"; Gruppen-Policies und SSO bleiben geplant | mittel: das ist die Stelle, an der v1.4 gelernt hat, dass Beweisdokumente dieselbe Prüfung brauchen wie Code |
| `CHANGELOG.md` | Eintrag im `[Unreleased]`-Block; Vokabular-Gate beachten (das Wort "Archiv" ist in öffentlichen Artefakten gesperrt, und ein Audit-Text lädt dazu ein) | niedrig, aber das Gate ist scharf |
| `docs/uninstall.md` | wohin das Audit gehört, wenn die App verschwindet, und wie man es bewusst löscht | niedrig |

### Ausdrücklich unverändert

`deps.py`, `nextcloud/credentials.py`, `nextcloud/http.py` (ausser einem zweiten Logger), `oauth/*` (der Speicher wird nicht angefasst), `server/reg_*.py` bis auf die Argumentklassifikation, jede Datei unter `tools/`, `Dockerfile`, `compose.*.yml`, das Schema-Budget.

## B.7 Vorgabewert des Schalters, und warum das eine Architekturfrage ist

Ein Log, das protokolliert, welcher Beschäftigte wann welches Werkzeug benutzt hat, ist eine Verhaltens- und Leistungserfassung. In Deutschland ist das in Betrieben und Behörden mitbestimmungspflichtig, und in der DSGVO braucht es Zweckbindung, Aufbewahrungsfrist und Löschung. Daraus folgen drei Bauentscheidungen, keine Meinungen:

1. **Vorgabewert aus.** Anders als der Talk-Sende-Schalter, der eine zugesagte Fähigkeit schützt und deshalb an ist, erzeugt dieser Schalter eine neue Datenerhebung. Eine Store-App, die bei Selbsthostern still anfängt, Nutzungsverhalten mitzuschreiben, tut das Falsche. Der Enterprise-Text muss dann "optional aktivierbar" sagen, nicht "aktiv".
2. **Die Aufbewahrungsfrist ist ein Feld, kein Literal.** Ohne Frist gibt es keine Löschung, ohne Löschung keine Zweckbindung.
3. **Die Feldbeschreibung nennt die Mitbestimmung.** Dasselbe Muster wie beim DCR-Schalter, dessen Sicherheitshinweis ausdrücklich im Feld steht und nicht nur in der Dokumentation: "eine Administration, die einen Schalter liest, ist die eine Person, die handeln kann".

Falls der ISV-Call ergibt, dass Behördenbetreiber eine erzwungene Protokollierung erwarten, ist der Weg dorthin ein zweiter Wert ("aus / metadaten / metadaten plus sichere Argumente") und nicht ein umgedrehter Vorgabewert.

---

## Data Flow

### Werkzeugaufruf mit Audit, ExApp-Modus

```
POST /mcp  {"method":"tools/call","params":{"name":"deck_browse",...}}
   |
   v  exapp/middleware.py::RequireAppApi
   |    1. AppAPI-Handschlag       -> 401 ohne Hinweis
   |    2. Bearer -> Identität     -> request.state[oauth_identity]
   |    3. Konto-Schalter          -> 403 access_disabled
   |    4. [NEU] request.state[audit_sink], request.state[identity des AppAPI-Zweigs]
   v
 MCP-Transport -> ServerRunner -> Middleware-Kette
   |
   v  [NEU] audit/middleware.py
   |    method != tools/call -> durchreichen, nichts schreiben
   |    Uhr an, Senke aus request.state
   v
 _handle_call_tool -> reg_deck.deck_browse -> graceful -> deps.resolve_clients(ctx)
   |                                                          |
   |                                                    Nextcloud (OCS/DAV)
   v
 Ergebnis oder CallToolResult(is_error) oder MCPError
   |
   v  [NEU] audit/middleware.py
        Satz bilden (B.2), schwärzen (redaction), an beide Senken,
        Fehler beim Schreiben -> eine Logzeile, niemals in den Aufruf hinein
   v
 Antwort an den Client, unverändert
```

Der Aufruf bekommt keine zusätzliche Nextcloud-Runde und keinen zusätzlichen Netzweg. Genau das ist der Grund für SQLite statt eines Protokoll-Endpunkts in Nextcloud: es gäbe keine OCS-Route, in die ein ExApp schreiben könnte, und eine erfundene wäre ein zweiter Rundlauf pro Werkzeugaufruf.

### OpenProject über Weg 0 (Bild für v2.0, in v1.5 nur im Spike)

```
openproject_browse(level="work_packages", query="...")
   -> deps.resolve_clients(ctx)                    [unverändert]
   -> capabilities.require_app(clients, "integration_openproject")
   -> GET {NC_MCP_URL}/ocs/v2.php/apps/integration_openproject/api/v1/work-packages
        Header: OCS-APIRequest: true + AppAPI- bzw. Basic-Auth des Nutzers
   -> Nextcloud holt das OpenProject-Token DIESES Nutzers und fragt OpenProject
   -> parse_ocs -> Projektion -> compact -> graceful
```

Kein zweiter Credential, keine zweite Basis-URL, kein Egress. Der einzige neue Fehlerausgang ist der 401 aus `validatePreRequestConditions`, und der wird zu einem Satz: "Dieses Konto hat OpenProject in Nextcloud nicht verbunden."

---

## Anti-Patterns

### Das MCP-Token an OpenProject weiterreichen

**Was Leute tun:** den Bearer, mit dem der Client uns anspricht, an die nachgelagerte API schicken, weil er ja "schon ein Token ist".
**Warum falsch:** die Autorisierungsspezifikation ist normativ dagegen ("MCP servers MUST NOT accept or transit any other tokens"), und praktisch ist es der klassische Weitergabefehler: das Token wurde für uns ausgestellt, seine Zielgruppe ist unsere Ressource, und ein zweites System, das es akzeptiert, hat seine Zielgruppenprüfung nicht gemacht.
**Stattdessen:** ein eigener, für die Zielressource ausgestellter Credential, oder gar keiner, weil ein anderes System ihn hält (Weg 0).

### Ein Dienstkonto, weil es "nur für den Anfang" ist

**Was Leute tun:** einen OpenProject-API-Key eines Administrators ins Deploy-Environment legen, um im Spike schnell etwas zu sehen.
**Warum falsch:** ab diesem Moment liest die App Daten, die kein angemeldeter Nutzer sehen könnte, und der Satz, der auf jeder Store-Seite und in jedem LinkedIn-Beitrag dieses Projekts steht, ist unwahr. Selbst im Spike, weil ein Spike, der eine verbotene Bauart benutzt, keine Aussage über die erlaubte macht.
**Stattdessen:** der Spike benutzt zwei echte Konten mit echten Verbindungen, das ist der Punkt von S2 und S3.

### Das Audit als Dekorator an die Werkzeuge hängen

**Was Leute tun:** `@audited` neben `@graceful` in jede `reg_*`-Datei.
**Warum falsch:** "jeder Werkzeugaufruf" wird damit zu 21 Zusagen, von denen die 22. vergessen wird, und das Feature heisst "über jeden Tool-Aufruf". Dieselbe Argumentation hat in v1.0 die AppAPI-Prüfung an die Transportgrenze gezogen.
**Stattdessen:** `middleware=` am Serverobjekt, plus ein Contract-Test, der ihre Registrierung behauptet.

### Die Argumente vollständig protokollieren

**Was Leute tun:** `json.dumps(ctx.params)` in den Satz, weil man später ja nicht weiss, was man braucht.
**Warum falsch:** damit wandern Suchbegriffe, Nachrichten und Notiztexte in eine zweite Datei mit anderer Schutzhöhe. Ein Audit, das im Leck schlimmer ist als das System, das es prüft, ist ein Nettoverlust.
**Stattdessen:** Erlaubnisliste je Werkzeug plus `args_digest` plus `bytes_out`.

### Das Audit in `oauth.sqlite3` legen

**Was Leute tun:** eine Tabelle mehr, weil der Speicher schon da ist.
**Warum falsch:** die Purge leert diese Datei und löscht den Schlüssel. Das Audit verschwindet dann genau am Tag der Deinstallation, also an dem Tag, an dem eine Revision es sehen will.
**Stattdessen:** zweite Datei, kein Schlüssel, eigene Aufbewahrung, ausdrücklich von der Purge ausgenommen und mit einem Test dagegen abgesichert.

### Das Audit an der ASGI-Grenze schreiben

**Was Leute tun:** die vorhandene `RequireAppApi` um eine Protokollzeile erweitern, weil dort schon die Identität liegt.
**Warum falsch:** diese Schicht kennt den Werkzeugnamen nicht, und um ihn zu erfahren, müsste sie den Rumpf lesen, den der Transport danach noch braucht. Ein Streamable-HTTP-POST kann ausserdem mehrere Nachrichten tragen, eine Anfrage ist also nicht ein Aufruf.
**Stattdessen:** die ASGI-Schicht hinterlegt, die MCP-Middleware schreibt.

---

## Build Order

Zwei Stränge, die einander nicht berühren, plus der Textstrang, der beide einholt.

```
Strang S (Spike, kein Produktionscode)      Strang A (Audit-Log)         Strang R (Release-Text)
---------------------------------------     ----------------------       ----------------------
S0 Aufbau: NC + OpenProject + Integration    A1 Naht + Satz + stderr      R1 0.1.11: die drei
S1 Messungen S1..S6                          A2 Speicher + Kehren             wartenden Textstellen
S2 Bericht + ISV-Fragenliste                 A3 occ-Leseweg + Admin-Feld
                                             A4 Doku + Store-Text  <----------+ (Zusammenfluss)
```

### Phase A1: die Naht und der Satz (Anfang, blockierend für A2 und A3)

`audit/middleware.py`, `audit/redaction.py`, die stderr-Senke, die eine Zeile in `server/__init__.py`, die Hinterlegung in `exapp/middleware.py`, der Contract-Test über die Argumentklassifikation. **Danach ist das Feature fachlich fertig und beweisbar**: eine JSON-Zeile je Aufruf im Containerprotokoll, beide Fehlerformen abgedeckt, kein Freitext darin. Wenn der Meilenstein hier enden müsste, wäre er bereits wahr.

### Phase A2: Dauerhaftigkeit

`audit/store.py`, das Kehren nach Frist, die Obergrenze, die Purge-Ausnahme mit ihrem Test. Hängt an A1, weil der Satz feststehen muss, bevor er ein Schema bekommt.

### Phase A3: Lesen und Schalten

`exapp/audit_read.py`, das zweite occ-Kommando, die Erweiterung von `CONFIG_KEYS`, das Admin-Feld samt Zeichenketten, der Vorgabewert aus B.7. Hängt an A2, weil ein Leseweg etwas zu lesen braucht.

### Phase A4: Aussenwirkung

Enterprise-Absatz in drei READMEs und in `appinfo/info.xml`, `docs/audit.md`, `docs/uninstall.md`, Changelog, Versionsnummer. **Hängt an A3 und an R1**, denn beides fasst dieselben Textstellen an. Das ist die einzige echte Serialisierung des Meilensteins.

### Strang S: parallel ab Tag eins

S berührt keine Datei, die A berührt. Die einzige gemeinsame Ressource ist die Docker-Testumgebung, und selbst die nur, wenn A eine Integrationsmessung braucht (A1 und A2 kommen mit Unit-Tests aus). **Empfehlung: S läuft parallel zu A1 und A2 und ist vor A4 abgeschlossen**, damit der Bericht in die ISV-Vorbereitung eingeht und nicht in eine Nacharbeit.

### Strang R: zuerst oder mit A4 zusammen

Die drei wartenden Textänderungen aus dem `[Unreleased]`-Block sind unabhängig von allem. Zwei Möglichkeiten, beide vertretbar: **0.1.11 sofort ausliefern** (kleiner Release, schnelle Owner-Freigabe, danach hat A4 ein sauberes Feld) oder **0.1.11 und den Audit-Text in einem Release bündeln** (ein Store-Upload statt zwei, aber der Textrest wartet länger). Empfehlung: bündeln, wenn A3 sicher vor dem 14.09. fertig ist, sonst sofort ausliefern. Diese Entscheidung gehört dem Owner und sollte in der Roadmap als Entscheidungspunkt stehen, nicht als Annahme.

### Warum nicht Audit zuerst und Spike danach

Der naheliegende Einwand: erst fertig bauen, dann forschen. Dagegen spricht der Kalender. Der ISV-Call am 14.09. ist ein fester Termin, den nur der Spike bedient, und der Spike hat eine Aufbauzeit, die man nicht komprimieren kann (zwei Dienste, eine Integration, zwei Konten). Ein Audit-Log dagegen hat keinen externen Termin. Wer S nach A legt, riskiert genau den Fall, in dem der Termin mit einer Vermutung statt mit einer Messung bedient wird, und dieses Projekt hat in v1.4 gelernt, was ein als erledigt gebuchter Befund ohne Beleg kostet.

---

## Offene Punkte, die live zu prüfen sind

| Frage | Status | Prüfweg |
|-------|--------|---------|
| Antwortet die OCS-Fläche von `integration_openproject` unter reiner AppAPI-Impersonation | offen, MEDIUM (CSRF-Weg für Mail bewiesen, für diese App nicht) | S1 |
| Trägt die serverseitige Token-Erneuerung ohne Browser-Sitzung (OAuth2-Modus) | offen, MEDIUM (Quellcode sagt ja) | S4, die entscheidende Messung |
| Bricht der Weg im OIDC-Modus nach Tokenablauf | HIGH im Quellcode (`TokenService::getExchangedToken` liest aus `ISession`), live ungeprüft | S5 bzw. ISV-Frage 2 |
| Veröffentlicht `integration_openproject` eine Capability, oder braucht es den Navigations-Kanal wie Mail | offen | ein Abruf von `cloud/capabilities` im selben Lauf |
| Ist AppAPI in openDesk aktiviert und dürfen Drittanbieter-ExApps installiert werden | offen | ISV-Frage 3 |
| Hat der ExApp-Container in der Zieltopologie Egress zu Nicht-Nextcloud-Hosts | offen | Kontrollmessung in A.6 |
| Sieht die `ServerMiddleware` im stdio-Modus eine `ctx.request` (erwartet: nein) | HIGH im SDK-Quellcode (`request=None` ohne `ServerMessageMetadata`), ungeprüft | ein Unit-Test mit stdio-Kontext |
| Kostet ein SQLite-Insert je Aufruf messbar Wanduhrzeit | offen, erwartet: unterhalb der Nextcloud-Runde | eine Messung in A2, dieselbe Disziplin wie beim Budget-Gate |
| Überlebt der Datenträger ein AppAPI-Update des Containers (die Annahme, auf der schon `oauth.sqlite3` steht) | HIGH aus Betriebserfahrung seit v1.0, nie ausdrücklich gemessen | ein Update-Zyklus in der Testinstanz, kostenlos in A2 |

---

## Sources

**Eigene Codebasis, gelesen am 2026-08-28 (HIGH):** `src/mcp_connector/server/__init__.py`, `deps.py`, `entry_exapp.py`, `config.py`, `exapp/{middleware,admin_settings,config_values,lifecycle,occ,purge}.py`, `oauth/{store,crypto}.py`, `nextcloud/http.py`, `server/reg_deck.py`, `tests/contract/{test_no_destructive_calls,test_module_boundaries}.py`, `appinfo/info.xml`.

**MCP-SDK 2.x, installiertes Paket gelesen (HIGH):** `.venv/Lib/site-packages/mcp/server/context.py` (`ServerMiddleware`, `ServerRequestContext`, `CallNext`), `mcp/server/runner.py` (`_make_context`, Anhängen der HTTP-Anfrage), `mcp/server/mcpserver/server.py` (Konstruktor mit `middleware=` und `extensions=`, `_apply_extension`, `_install_extension_interceptor`, `_handle_call_tool` mit `MCPError`-Durchreichung und `is_error=True`), `mcp/server/extension.py` (SEP-2133, `intercept_tool_call`).

**Nextcloud `integration_openproject`, Quellcode gelesen (HIGH):**
- [`appinfo/routes.php`](https://github.com/nextcloud/integration_openproject/blob/master/appinfo/routes.php) - der `ocs`-Block mit fünfzehn Routen unter `/api/{apiVersion}/...`
- [`lib/Controller/OpenProjectAPIController.php`](https://github.com/nextcloud/integration_openproject/blob/master/lib/Controller/OpenProjectAPIController.php) - `extends OCSController`, `#[NoAdminRequired]`, `validatePreRequestConditions()` mit 401 bei fehlendem Token
- [`lib/Service/OpenProjectAPIService.php`](https://github.com/nextcloud/integration_openproject/blob/master/lib/Service/OpenProjectAPIService.php) - `getAccessToken()` mit serverseitiger Erneuerung im OAuth2-Modus, `getOIDCToken()` mit `ExchangedTokenRequestedEvent`, `isAccessTokenExpired()`

**Nextcloud `user_oidc`, Quellcode gelesen (HIGH):**
- [`lib/Service/TokenService.php`](https://github.com/nextcloud/user_oidc/blob/main/lib/Service/TokenService.php) - `getExchangedToken()` holt das Ausgangstoken aus `ISession` und wirft `TokenExchangeFailedException`, wenn keines da ist; `storeToken()` schreibt in die Sitzung

**Nextcloud-Dokumentation (HIGH):**
- [OpenID Connect (Oidc), Developer Manual 34](https://docs.nextcloud.com/server/stable/developer_manual/digging_deeper/oidc.html) - Token-Exchange ausschliesslich über das PHP-Event, keine HTTP-Route
- [Logging, Administration Manual 34](https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/logging_configuration.html) - `admin_audit` schreibt in eine eigene `audit.log`, `log_type_audit`, `logfile_audit`; die Konvention, die unsere zweite Senke nachahmt

**OpenProject (HIGH bis MEDIUM):**
- [API Introduction](https://www.openproject.org/docs/api/introduction/) - OAuth2, Session, Basic Auth mit `apikey`, JWT eines konfigurierten OIDC-Providers als Bearer, Tokenlaufzeit zwei Stunden
- [OAuth applications](https://www.openproject.org/docs/system-admin-guide/authentication/oauth-applications/) - Registrierung, Autorisierungscode mit PKCE, Scope `api_v3` als Vorgabe
- [Nextcloud integration setup](https://www.openproject.org/docs/system-admin-guide/integrations/nextcloud/) und [Two-way OAuth 2.0](https://www.openproject.org/docs/system-admin-guide/integrations/nextcloud/two-way-oauth2/) - der OAuth2-Modus der Integration
- [Single Sign-On through OIDC](https://www.openproject.org/docs/system-admin-guide/integrations/nextcloud/oidc-sso/) - der openDesk-Modus, Token-Exchange, `oidc_provider_bearer_validation`

**openDesk (MEDIUM, Dokumentation ohne eigene Instanz):**
- [openDesk Architecture](https://docs.opendesk.eu/operations/architecture/) - Keycloak als zentraler Provider, Nextcloud und OpenProject als Relying Parties, Gruppensynchronisation

**MCP-Spezifikation (HIGH):**
- [Authorization](https://modelcontextprotocol.io/specification/draft/basic/authorization) - "MCP servers MUST only accept tokens that are valid for use with their own resources. MCP servers MUST NOT accept or transit any other tokens."

---
*Architecture research für: v1.5 Vorlauf openDesk (OpenProject-Spike und Audit-Log)*
*Researched: 2026-08-28*
</content>
</invoke>
