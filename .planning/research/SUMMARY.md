# Projekt-Recherche-Zusammenfassung

**Projekt:** MCP Connector für Nextcloud (Arbeitstitel), Repository `nextcloud-mcp-connector`
**Meilenstein:** v1.5 "Vorlauf openDesk"
**Domain:** MCP-only-ExApp für Nextcloud; zwei neue Bausteine: ein zweiter, fremder Host (OpenProject in openDesk) und ein Audit-Log über jeden Werkzeugaufruf
**Recherchiert:** 2026-08-28
**Konfidenz:** MEDIUM in der Gesamtschau. Die Einzelbefunde sind überwiegend HIGH (Quellcode und live gemessen), aber die vier Berichte widersprechen sich in der wichtigsten Architekturfrage des Meilensteins, und diese Frage ist ungelöst. Eine Synthese, die das glattbügelt, wäre falsch.

## Executive Summary

Dieser Meilenstein hat zwei fast unabhängige Hälften. Die eine ist der Audit-Log: alle sechs Bauteile dafür existieren bereits im Repository (SQLite-Muster aus `oauth/store.py`, die `MCPServer(middleware=...)`-Naht im SDK, die Registry-Annotationen `READ_ONLY`/`CREATE_ONLY`, die `/connections`-Seite, der occ-Weg über `exapp/purge.py`), und alle vier Recherchen sind sich einig, dass dieser Baustein ohne openDesk trägt und zuerst fertig werden sollte. Die andere Hälfte ist der OpenProject-Zugriff, und hier widersprechen sich die Berichte an der einzigen Stelle, die wirklich zählt: wie der Connector im Namen des angemeldeten Nutzers auf OpenProject zugreift. ARCHITECTURE.md hat einen Weg gefunden, der drei der vier Berichte offenbar nicht bekannt war, nämlich die bereits existierende Nextcloud-App `integration_openproject` mit fünfzehn OCS-Routen, die mit dem Token des angemeldeten Nutzers spricht. STACK.md, FEATURES.md und PITFALLS.md bauen ihre gesamte Analyse dagegen auf einem eigenen OAuth-Autorisierungscode-Fluss direkt gegen OpenProject auf, ohne diesen Proxy-Weg überhaupt zu erwägen. Das ist kein Nuancenunterschied, sondern zwei verschiedene Architekturen mit verschiedenen Sicherheitseigenschaften, verschiedenen Spike-Kosten und verschiedenen Bruchstellen. Diese Zusammenfassung entscheidet die Frage nicht, sie legt sie offen: Sie gehört in den Spike, nicht in ein Meeting.

Darüber liegt eine noch wichtigere Frage, die drei der vier Berichte fast beiläufig behandeln, obwohl sie logisch vor jeder Auth-Frage steht: ob eine ExApp in openDesk überhaupt installierbar ist. openDesk ist eine Kubernetes-Distribution ohne Nextcloud App Store (`appstore: enabled: false`) und ohne AppAPI im produktionsfähigen Sinn (die unterstützten Deploy-Daemons sind Docker-basiert, openDesk ist Helm auf Kubernetes). Die gesamte Ein-Klick-Erzählung, der Kern der Positionierung dieses Produkts, existiert in einer openDesk-Installation schlicht nicht. Dazu kommt: openDesk 1.18.0 fährt Nextcloud 33.0.7, während sämtliche Ein-Klick- und Erreichbarkeitsnachweise dieses Projekts auf Nextcloud 34.0.3 stehen, openDesk schaltet Talk (`spreed`) und Kontakte ab, was zwei der neun bestehenden Werkzeugfamilien in dieser Umgebung dunkel schaltet, und openDesk Community Edition hat weder den OpenProject-eigenen MCP-Server noch den OIDC-SSO-Speichermodus, beide sind dort Enterprise-Add-ons.

Der Audit-Log-Baustein ist technisch der leichtere, aber er ist an fünf bis sechs Stellen eine Falle, die alle mit derselben Bewegung zu vermeiden sind: Metadaten statt Inhalte speichern, eine Obergrenze setzen, die Purge-Frage bewusst entscheiden, den Schalter per Default aus lassen (Mitbestimmung), und das Wort "Audit-Log" nicht mehr versprechen, als eine Hash-Kette plus zwei Senken tatsächlich halten. Mehrere Entscheidungen sind ausdrücklich als Owner-Entscheidung markiert, und keine Recherche kann sie stellvertretend treffen; sie gehören gesammelt in die Anforderungsdefinition.

## Der zentrale Widerspruch: Wie erreicht der Connector OpenProject im Namen des Nutzers?

**ARCHITECTURE.md** hat im Quellcode der Nextcloud-App `integration_openproject` einen Weg gefunden ("Weg 0"), der schon existiert: Diese App spricht mit OpenProject im Zwei-Wege-OAuth2-Modus mit dem Token des angemeldeten Nutzers, erneuert dieses Token serverseitig ohne Browser-Sitzung, und ist in openDesk bereits vorkonfiguriert. Der Connector müsste dafür nur ein neues Client-Modul bauen, das die bestehenden OCS-Routen dieser App über `NC_MCP_URL` anspricht, mit demselben App-Passwort-Mechanismus, den er heute schon für Nextcloud selbst benutzt. Kein neues Geheimnis im Container, keine zweite Basis-URL, kein Egress.

**STACK.md** (und mit ihm FEATURES.md und PITFALLS.md) erklärt dagegen den OIDC-Weg für strukturell unerreichbar (`user_oidc` kann Token-Exchange nur als PHP-Ereignis mit Browser-Session, das eine ExApp nicht auslösen kann) und empfiehlt als Konsequenz einen **eigenen OAuth-Autorisierungscode-Fluss je Nutzer direkt gegen OpenProject** ("Weg 1"), mit persönlichem API-Token als dokumentiertem Rückfall. Diese drei Dokumente erwähnen `integration_openproject` als Auth-Proxy an keiner Stelle. FEATURES.md kennt die App nur als Datenquelle für `file_links` (Dateiverknüpfungen), nicht als Zugriffsweg.

Das ist der Kern des Widerspruchs: **drei von vier Berichten haben den Weg, den der vierte für die einzig versprechenstreue Lösung hält, nicht in Betracht gezogen.**

| | Weg 0 (ARCHITECTURE): Proxy über `integration_openproject` | Weg 1 (STACK/FEATURES/PITFALLS): eigener OAuth-Client gegen OpenProject |
|---|---|---|
| **Wo liegt das Geheimnis** | in Nextcloud (`oc_preferences`, App-eigene Verwaltung) | im ExApp-Container, SQLite, AES-GCM, Datenschlüssel aus Nextcloud |
| **Übersteht "Assistent sieht nie mehr als der Nutzer"** | ja, unverändert, weil Nextcloud weiterhin entscheidet | ja, aber über eine zweite, eigene Einwilligung pro Nutzer |
| **Was fällt bei kompromittiertem Container** | nichts Neues gegenüber heute (dieselben App-Passwörter) | zusätzlich alle OpenProject-Refresh-Token aller verbundenen Nutzer |
| **Bricht die feste Zieladresse (heute: nur `NC_MCP_URL`)** | nein | ja, zweite Basis-URL nötig, Egress zu einem zweiten Host |
| **Was der Spike messen muss** | ob die OCS-Route auch ohne Browser-Sitzung antwortet (App-Passwort/AppAPI-Impersonation), und vor allem: übersteht die serverseitige Token-Erneuerung den Wechsel in openDesks OIDC-Modus, oder bricht sie nach Ablauf des zwischengespeicherten Tokens? | ob `/oauth/authorize` PKCE annimmt, obwohl die Metadaten es nicht bewerben; Token-Lebensdauer und Refresh-Verhalten; ob der bestehende SSRF-Schutz eine Nachbarkomponente im selben Cluster fälschlich aussperrt |
| **Spike-Kosten** | niedrig, zwei Container (Docker-Nextcloud + OpenProject-Community-Instanz), kein Keycloak nötig | mittel, zusätzlicher Browser-Consent-Flow zum Messen |
| **Funktionsumfang** | schmal, nur was die Integration proxyt (Arbeitspakete suchen/anlegen, Projekte, Zuweisbare, Status, Typen, Benachrichtigungen, Dateiverknüpfungen) | volle API v3 |
| **Bricht in openDesks OIDC-Modus** | möglicherweise ja: `getOIDCToken()` holt das Ausgangstoken aus der PHP-Session, die bei einem MCP-Aufruf ohne Browser-Login nicht existiert | nein, unabhängig vom Nextcloud-internen SSO-Modus |

**Bewertung:** Der von ARCHITECTURE.md gefundene Weg 0 ist die stärkere Architektur, wenn er trägt, weil er das Sicherheitsversprechen mit exakt derselben Mechanik hält wie heute und keinen neuen Vertrauensanker im Container schafft. Aber sein Tragen hängt an einer einzigen, ungemessenen Tatsache: ob die serverseitige Token-Erneuerung auch in openDesks OIDC-gebundenem Betrieb greift, oder ob sie nach Ablauf des zwischengespeicherten Tokens (typischerweise wenige Minuten nach der letzten Browsertätigkeit des Nutzers) auf 401 fällt. Genau das ist im Quellcode von `user_oidc` als Bruchstelle belegt (`TokenService::getExchangedToken()` liest aus der PHP-Session), aber nicht live gemessen.

**Diese Entscheidung ist OPEN und wird durch die Spike-Messung entschieden, nicht durch Argumentation.** Der Spike muss beide Wege im Bericht führen: Weg 0 zuerst und mit den Behauptungen S1-S6 aus ARCHITECTURE.md (insbesondere S4: Token-Erneuerung ohne Browser-Sitzung, und S5: Verhalten im OIDC-Modus nach Tokenablauf), Weg 1 als Rückfall mit den vier Fragen aus STACK.md A.8 (insbesondere PKCE-Unterstützung trotz fehlender Metadaten-Ankündigung). Falls Weg 0 im OIDC-Modus nachweislich bricht und der ISV-Call keine bessere Antwort liefert, ist Weg 1 der einzig vertretbare Rückfallweg, kein Ausweichen.

## Die Gating-Frage: Ist eine ExApp in openDesk überhaupt installierbar?

Diese Frage steht **über** jeder API-Frage, und alle vier Berichte, die sie berühren, stimmen darin überein. openDesk ist laut eigener Architekturdokumentation eine Kubernetes-Distribution, orchestriert per Helmfile. Drei Befunde entscheiden vor jedem Toolcode:

1. **Kein Nextcloud App Store.** `appstore: enabled: false` in den openDesk-Nextcloud-Werten. Die gesamte Ein-Klick-Erzählung dieses Produkts, der Kern der Store-Beschreibung und der Positionierung, existiert in einer openDesk-Installation nicht. Installation dort ist eine Betreiber-Aufgabe im Helmfile.
2. **AppAPI ist für Kubernetes nicht gebaut.** Die produktionsfähigen Deploy-Daemons (Docker Socket Proxy, HaRP) sind Docker-Mechanik; openDesk ist Helm auf Kubernetes. Der einzige theoretisch passende Daemon-Typ ist `manual_install`, der laut Nextcloud-Dokumentation ausdrücklich für Entwicklung oder Spezialfälle gedacht ist, nicht für den produktiven Regelbetrieb.
3. **Nextcloud in openDesk 1.18.0 steht auf 33.0.7, nicht auf 34.0.3.** Sämtliche Ein-Klick- und AppAPI-Erreichbarkeitsnachweise dieses Projekts sind auf 34.0.3 gemessen. Die Zielumgebung ist damit nicht neuer, sondern älter als getestet, und ein Nachweis auf der falschen Hauptversion ist in einem Projekt, das seine Nachweise wörtlich nimmt, kein Nachweis.

Zusätzlich, weil es dieselbe Kategorie ist und in den Requirements ankommen muss: **openDesk schaltet `spreed` (Talk) und `contacts` ab.** Von den 21 heute ausgelieferten Werkzeugen über neun Familien bleiben in einer openDesk-Installation weniger übrig, als die Store-Beschreibung verspricht, unabhängig vom Ausgang des OpenProject-Spikes. Und: **openDesk Community Edition liefert weder den OpenProject-eigenen MCP-Server (Enterprise-Add-on seit OpenProject 17.2) noch den OIDC-SSO-Speichermodus (ebenfalls Enterprise) aus.** Beides existiert nur in openDesk Enterprise Edition, und das ist die Trennlinie, die den Mehrwert dieses Bausteins in der Zielumgebung überhaupt erst bestimmt.

**Konsequenz für die Roadmap:** Der Spike muss in dieser Reihenfolge berichten: zuerst die Installierbarkeitsfrage (Ja/Nein/offen, mit Quelle oder ISV-Call-Vermerk), dann erst die Auth-Frage (siehe oben), dann erst die API-Form. Eine Roadmap-Phase "OpenProject-Werkzeuge" ohne vorausgehende Phase "Installierbarkeit" hätte die teure Frage nicht angefasst.

## Key Findings

### Empfohlener Stack

Kein neuer Runtime-Zukauf. OpenProject ist HAL+JSON über HTTP und wird mit dem vorhandenen `httpx` gesprochen (jeder PyPI-Client für OpenProject ist tot, `requests`-basiert oder pinnt ein inkompatibles `httpx`). Das Audit-Log braucht `sqlite3` (stdlib, gleiches Muster wie `oauth/store.py`), `hashlib` (stdlib, für die Hash-Kette) und `logging` mit einem eigenen JSON-Formatter. `pyproject.toml` bleibt unverändert.

**Kerntechnologien:**
- `httpx` (bereits vorhanden): einziger HTTP-Client, jetzt auch für OpenProject API v3. Kein PyPI-Client ist installierbar oder gepflegt genug, um ihn zu ersetzen
- `sqlite3` (stdlib): Primärsenke des Audit-Logs, append-only, hash-verkettet, zweite Datei neben `oauth.sqlite3`. Kein neuer Mechanismus, dieselbe Wette wie seit v1.0
- `hashlib` (stdlib): Hash-Kette (`prev_hash`/`entry_hash`), rund 30 Zeilen. Macht aus einer Tabelle einen prüfbaren Nachweis
- `mcp[cli]` `MCPServer(middleware=[...])` (bereits vorhanden): die einzig richtige Naht für "jeder Werkzeugaufruf", als "Provisional" markiert, deshalb hinter einem dünnen Adapter

Bewusst **nicht** gezogen: jeder PyPI-OpenProject-Client (tot oder inkompatibel), `structlog`/`python-json-logger`/`loguru` (40 Zeilen Eigenbau reichen), `aiosqlite` (bereits gegen begründet), `opentelemetry-sdk` (Traces werden gesampelt, ein Audit-Log darf nicht sampeln).

### Erwartete Features

**Must have (v1.5, wenn der Spike den OpenProject-Zugang trägt):**
- Ein Auth-Weg live bewiesen: Nutzer verbindet, ein Werkzeug antwortet mit echten Daten, Trennen nimmt den Zugang mit
- `openproject_browse` mit `my_work` (Filter `assignee=me`, `status=o`) und `inbox` (ungelesene Benachrichtigungen mit `reason`)
- `openproject_browse` mit `projects`, `work_packages` (inkl. Volltext), `comments`
- `fetch("wp:<id>")`, inklusive bis zu 10 `file_links` als auflösbare `file:<id>`: der einzige Punkt, an dem dieses Produkt etwas kann, das kein Wettbewerber kann
- Drei unterscheidbare Fehlersätze, instanzweiter Aus-Schalter, kein Schreibpfad (AST-Gate)

**Must have (Audit-Log, trägt den Meilenstein auch ohne OpenProject):**
- Ein Aufrufpunkt für jeden Werkzeugaufruf (Middleware, nicht Dekorator)
- Metadatenschema ohne Argumentwerte im Default, abgelehnte Aufrufe mit Grund, Verbindungs-/Admin-Ereignisse im selben Protokoll
- Aufbewahrungsfrist als Admin-Wert (Default 90 Tage), automatische Löschung, Hash-Kette plus Prüfbefehl
- `occ mcp_connector:audit` für CSV/JSONL-Export, JSON-Zeilen nach stdout, Nutzeransicht auf `/connections`
- Store-Text und READMEs EN/DE/FR im **selben** Release nachgezogen

**Differenzierer:** Ein Endpunkt für Nextcloud und OpenProject statt zwei Server mit zwei Zustimmungen; die Kette Arbeitspaket zu Datei über `file_links`; Verfügbarkeit auf der Community Edition, wo der Hersteller-MCP-Server (Enterprise-Add-on) fehlt; Nutzeransicht "was hat der Assistent in meinem Namen getan" auf der bestehenden `/connections`-Seite (kein Wettbewerber hat das).

**Anti-Features, ausdrücklich nicht bauen:** volle CRUD-Abdeckung wie Community-MCP-Server (132 Werkzeuge), PATCH auf Arbeitspakete, Benachrichtigungen als gelesen markieren, den offiziellen OpenProject-MCP durchreichen, Argumente/Ergebnisse vollständig im Audit-Log speichern, Nutzungsstatistiken/Dashboards, ein `audit_search`-Werkzeug, "revisionssicher"/WORM/Blockchain-Wortwahl.

### Architekturansatz

Die Architektur bindet beide Bausteine an sieben bestehende Randbedingungen (Dispatch ohne Zwischenschicht, Anmeldedaten synchron im Tool-Aufruf, feste Zieladresse aus `NC_MCP_URL`, Identität an der ASGI-Grenze aufgelöst, persistenter Datenträger, kein PHP-Prozess, undeklarierte occ-Route als Verwaltungsmuster). Für OpenProject ist die architektonische Kernfrage nicht "welches OAuth", sondern welcher Weg diese Randbedingungen intakt lässt (siehe Widerspruch oben). Für das Audit-Log ist die Naht eindeutig: `MCPServer(middleware=[...])` am Serverobjekt, nicht ein Dekorator je Werkzeug, weil "jeder Werkzeugaufruf" eine Eigenschaft der Bauart sein muss und keine Sammlung von 21 (bald 22) Einzelzusagen.

**Wichtigste Komponenten:**
1. **OpenProject-Client** (Ort und Form abhängig vom Spike-Ergebnis): entweder `nextcloud/clients/integration_openproject.py` (Weg 0, kein neuer Credential-Modus) oder ein zweites Client-Modul mit eigener Basis-URL und eigenem Credential-Speicher (Weg 1)
2. **`audit/middleware.py`**: `ServerMiddleware`, zustandslos, liest ihre Senke aus `request.state`, sieht beide Fehlerformen (`CallToolResult(is_error=True)` und geworfene `MCPError`)
3. **`audit/store.py`**: zweite SQLite-Datei, eigene Datei statt zweite Tabelle in `oauth.sqlite3`, damit Purge und Aufbewahrung getrennt bleiben
4. **`audit/redaction.py`**: Erlaubnisliste je Werkzeug, Kennungen ja, Freitext nein, durchgesetzt per Contract-Test (Kanarientest)
5. **`exapp/audit_read.py`**: undeklarierte occ-Route nach dem `purge`-Muster, kein Web-Endpunkt

Der Meilenstein fügt in v1.5 **kein einziges neues Werkzeug** hinzu, weder der Spike noch das Audit-Log rühren das Schema-Budget an. Das ist ein handfester Vorteil (kein Nacharbeiten in drei READMEs, `info.xml`, Contract-Tests) und gehört als Rahmenbedingung in die Roadmap.

### Kritische Pitfalls

1. **Client Credentials / Impersonationsnutzer gegen OpenProject**: funktioniert im Spike sofort, bricht aber das Kernversprechen unauffällig, weil jeder Anfragende die Sicht eines einzigen Kontos sieht. Muss explizit ausgeschlossen und die Begründung in PROJECT.md unter Key Decisions festgehalten werden, bevor jemand in Versuchung gerät, damit eine Demo zu bauen.
2. **Ein Audit-Log wird zur zweiten Kopie genau der Daten, die es schützen soll**: sobald Argumente oder Ergebnisse mitgeschrieben werden, widerspricht die Anwendung `docs/privacy.md` wörtlich ("Nichts davon wird in die Datenbank geschrieben"). Durchsetzung nur per Contract-/Kanarientest, nicht per Disziplin.
3. **Unbegrenztes Wachstum reißt den OAuth-Store mit**: Audit-Log und Autorisierungen liegen auf demselben Volume ohne Quote; ein volles Volume macht SQLite im WAL-Modus schreibunfähig, jede Token-Rotation und jede neue Verbindung scheitert. Obergrenze und Aufbewahrungsfrist sind Pflicht, nicht Kür.
4. **Ein Log, das der Administrator nie zu Gesicht bekommt**: Nextclouds Default-Loglevel (2, Warning) unterdrückt Info-Meldungen; derselbe Mechanismus, der `admin_audit` heute schon unsichtbar macht. Ohne einen dokumentierten Leseweg (occ) und ohne Bewusstsein für den Default-Loglevel ist das Feature Dekoration.
5. **"Audit-Log" nennen, was ein Anwendungslog ist**: der Administrator hat Shell-Zugriff auf die SQLite-Datei und könnte sie ändern oder löschen; ein Prüfer erwartet unter dem Wort "Audit-Log" genau die Eigenschaft, die in dieser Architektur am schwersten zu halten ist. Grenzbeschreibung ("was es nicht leistet") ist Pflichtbestandteil des Textes.

## Owner-Entscheidungen

Diese Punkte sind in den Recherchen ausdrücklich als **Owner-Entscheidung**, nicht als Rechercheergebnis markiert. Sie gehören gesammelt in die Anforderungsdefinition, nicht verteilt über vier Dokumente:

1. **Überlebt das Audit-Log `occ mcp_connector:purge` / die Deinstallation?** Kollidiert direkt mit dem v1.0-Erfolgskriterium "eine Deinstallation entfernt alle Daten" und mit der heutigen Aussage in `docs/privacy.md`. Empfehlung aus der Recherche (STACK/FEATURES/ARCHITECTURE übereinstimmend): das Audit-Log überlebt Purge, `docs/privacy.md` und `docs/uninstall.md` sagen das ausdrücklich, der Aufbewahrungs-Job ist der einzige automatische Löscher. Das ist trotzdem eine Entscheidung, die der Meilenstein bewusst treffen muss, kein Fehler, der später auffällt.
2. **Purge vs. Aufbewahrung im Detail:** Was passiert mit Audit-Einträgen bei (a) Nutzer trennt Verbindung, (b) Nutzer pausiert, (c) Aufbewahrungsfrist läuft ab, (d) Nutzer wird in Nextcloud gelöscht, (e) Administrator ruft Purge / App wird deinstalliert? FEATURES.md legt eine Entscheidungsvorlage vor (bleiben / bleiben / löschen / löschen / alles löschen), aber es ist ausdrücklich eine Owner-Entscheidung.
3. **Ships Release 0.1.11 sofort, oder gebündelt mit dem Audit-Log-Text?** Der `[Unreleased]`-Block enthält bereits Textänderungen (gekürzter Trifecta-Absatz, Autorenkontakt). Beide Wege sind vertretbar (ARCHITECTURE.md empfiehlt Bündelung, wenn der Audit-Log-Export sicher vor dem 14.09. fertig ist, sonst sofortiges Ausliefern), aber es ist eine Terminentscheidung des Owners, keine Bauentscheidung.
4. **Default-Stellung des Audit-Log-Schalters:** an oder aus. Die Recherche empfiehlt einstimmig **aus** (anders als `talk_send`, das eine zugesagte Fähigkeit schützt, erzeugt dieser Schalter eine neue Datenerhebung mit Mitbestimmungsrelevanz), aber der endgültige Wert ist eine Produktentscheidung.
5. **Bleibt das Wort "Audit-Log" in der Enterprise-Zeile stehen, oder wird es präzisiert/umbenannt?** Hängt an der Frage, ob eine Hash-Kette gebaut wird (macht den Anspruch teilweise haltbar) und an der Frage, ob "geplant" im Store-Text neben einem existierenden Audit-Modul stehen darf (darf es nicht, siehe Pitfall 10). Vier Teilfragen aus PITFALLS.md Pitfall 10 sind vor dem Fundament schriftlich zu beantworten.
6. **AGPL-Konsequenz für die Enterprise-Positionierung:** Ein Audit-Log, das in dieses (AGPL-lizenzierte) Repository kommt, kann kein exklusives kommerzielles Unterscheidungsmerkmal mehr sein. Das ist eine Positionsfrage für den ISV-Call am 14.09., die vorher geklärt sein sollte, nicht dort entdeckt werden sollte.
7. **Inhaltsstufe des Audit-Logs als Admin-Opt-in** (`arguments: none|keys|full`): Default `keys` empfohlen, aber ob `full` überhaupt angeboten wird, ist eine Abwägung zwischen Nachfrage und Datenschutzrisiko.
8. **Ob und wie der ISV-Call-Ausgang die OpenProject-Architekturentscheidung (Weg 0 vs. Weg 1) präjudiziert**, insbesondere ob openDesk-Betreiber bereit wären, für Weg 2 (Keycloak-Client) einen eigenen Client einzurichten: das ist keine Recherchefrage mehr, sondern eine Verhandlungsfrage.

## Implications for Roadmap

Basierend auf der kombinierten Recherche ist die Reihenfolge **entlang der Entscheidungen und zweier fast unabhängiger Stränge** zu schneiden, nicht entlang der Module. PITFALLS.md nennt das ausdrücklich: die Fremdintegration hat Querschnittscharakter über Persistenz, Purge, Admin-Einstellungen, Latenz, drei Sprachen und den Store-Text, und jede der zugehörigen Einzelentscheidungen kostet eine Stunde einzeln und eine Woche, wenn sie erst während der Implementierung auffällt.

### Phase 1: Meilenstein-Entscheidungen (vor jedem Code)
**Rationale:** Name, Umfang und Grenze des Audit-Logs, Default-Stellung des Schalters, Purge-vs-Aufbewahrung-Regel und die Store-Text-Strategie bestimmen Schema und Aufwand aller folgenden Phasen. Dieselbe Phase entscheidet auch, ob 0.1.11 sofort oder gebündelt ausgeliefert wird.
**Liefert:** eine schriftlich festgehaltene Antwort auf jede der acht Owner-Entscheidungen oben.
**Vermeidet:** Pitfall 9, 10, 14 (Wortanspruch, Store-Text-Kollision, falsche Reihenfolge).

### Phase 2 (Strang S, parallel ab Tag 1): openDesk-Spike Teil 1: Installierbarkeit
**Rationale:** Muss vor jeder API-Frage stehen, weil sie die gesamte Reihenfolge von v2.0 bestimmt.
**Liefert:** drei Ja/Nein-Antworten (Deploy-Daemon-Typ in openDesk vorhanden? App-Allowlist? Wäre ein eigenständiges Deployment neben der Suite akzeptiert?), jede mit Quelle oder als offene ISV-Call-Frage markiert.
**Vermeidet:** Pitfall 2.

### Phase 3 (Strang S, Fortsetzung): openDesk-Spike Teil 2: Nutzeridentität gegen OpenProject
**Rationale:** Das ist der zentrale Widerspruch dieser Zusammenfassung. Diese Phase misst beide Wege gegeneinander, nicht nur einen.
**Liefert:** Weg 0 gegen ein Docker-Nextcloud plus `integration_openproject` im OAuth2-Modus gemessen (Behauptungen S1-S6 aus ARCHITECTURE.md, mit S4/S5 als entscheidende Messungen), Weg 1 als dokumentierter Rückfall mit PKCE-Test. Zwei Nutzerkonten Pflicht (Negativbeweis). Auf die openDesk-Version gepinnt (17.7.x), nicht `latest`.
**Vermeidet:** Pitfall 1, 3, 4, 13.

### Phase 4 (Strang A, parallel zu Phase 2/3): Audit-Log Fundament
**Rationale:** Unabhängig vom Spike-Ausgang, trägt den Meilenstein allein, wenn der Spike enttäuscht.
**Liefert:** `audit/middleware.py`, `audit/redaction.py`, Satzschema (Metadaten, keine Inhalte), stderr-JSON-Zeilen, Kanarientest.
**Vermeidet:** Pitfall 5, 7, 12.

### Phase 5 (Strang A): Audit-Log Dauerhaftigkeit
**Rationale:** Baut auf dem feststehenden Satzschema auf.
**Liefert:** `audit/store.py` (eigene Datei), Obergrenze, Aufbewahrungsfrist, Hash-Kette plus Prüfbefehl, Purge-Ausnahme mit Test.
**Vermeidet:** Pitfall 6, 9.

### Phase 6 (Strang A): Audit-Log Ausgabe
**Rationale:** Braucht einen feststehenden Speicher, um etwas zu lesen.
**Liefert:** `occ mcp_connector:audit` (CSV/JSONL), Admin-Schalter (Default aus), Nutzeransicht auf `/connections`.
**Vermeidet:** Pitfall 8, 11.

### Phase 7 (Konvergenzpunkt beider Stränge): Release- und Store-Text
**Rationale:** Fasst dieselben Textstellen an wie 0.1.11 und der Audit-Enterprise-Absatz; die einzige echte Serialisierung des Meilensteins.
**Liefert:** dreisprachige READMEs und `info.xml` konsistent mit dem tatsächlichen Funktionsstand, ISV-Fragenliste aus Phase 2/3, Spike-Bericht.
**Vermeidet:** Pitfall 10.

### Research Flags

- **Phase 3 (Identitätsspike)** braucht während der Umsetzung weitere gezielte Recherche/Messung, keine reine Planung: PKCE-Verhalten, Token-Lebensdauer, SSRF-Verhalten gegenüber einer Nachbarkomponente sind alle ausdrücklich als "ungemessen" markiert.
- **Phase 4/5/6 (Audit-Log)** folgen einem im Repository bereits etablierten Muster (`oauth/store.py`, `exapp/purge.py`, `exapp/occ.py`): Standardmuster, `--research-phase` kann hier entfallen.
- **Phase 2 (Installierbarkeit)** ist überwiegend Dokumentenrecherche (openDesk-Deployment-Repo) plus eine schriftlich vorbereitete Fragenliste für den ISV-Call; kein Code-Risiko, aber die Antwort bestimmt, ob Phase 3 überhaupt lohnt.
- **Phase 7** ist Standardarbeit (Text, Gate-Test wie beim Vokabular-Gate), aber zeitkritisch wegen des Owner-Tag-Gates und der Signaturprüfung über das heruntergeladene Asset.

## Confidence Assessment

| Bereich | Konfidenz | Anmerkung |
|---------|-----------|-----------|
| Stack | HIGH für Einzelbefunde (live gemessen, PyPI-JSON-API, Quellcode), aber die Empfehlung "eigener OAuth-Client" ignoriert den von ARCHITECTURE.md gefundenen Proxy-Weg. Als Gesamtempfehlung daher MEDIUM |
| Features | HIGH für API-Lage und Wettbewerbslage (offizielle Doku, drei Community-Server gelesen), MEDIUM für regulatorische Erwartungen (keine echte Behörden-Rückmeldung), LOW für Nutzerpriorisierung innerhalb OpenProject |
| Architektur | HIGH für Codebasis-Nähte und Token-Mechanik (Datei und Zeile belegt), MEDIUM für Verhalten unter AppAPI-Impersonation in dieser Topologie (genau das misst der Spike), MEDIUM für openDesk-Betriebsdetails |
| Pitfalls | HIGH für OpenProject-API-Form und Nextcloud-Logging-Defaults, HIGH für die openDesk-Versionsmatrix, MEDIUM für Workspaces-Abkündigung/pageSize-Obergrenze und für alles, was den ZenDiS-Aufnahmeprozess betrifft (öffentlich nicht dokumentiert, das ist selbst der Befund) |

**Gesamtkonfidenz: MEDIUM.** Nicht wegen schwacher Einzelrecherche, sondern weil die vier Berichte in der wichtigsten Frage nicht konvergieren und diese Frage nur eine Messung, kein weiteres Lesen, klären kann.

### Gaps to Address

- **Der zentrale Widerspruch (Weg 0 vs. Weg 1)** ist der wichtigste Gap und wird durch Phase 3 der Roadmap geschlossen, nicht durch weitere Dokumentenrecherche.
- **PKCE gegen OpenProject** ist ungemessen (Metadaten bewerben es nicht, die API-Doku setzt es voraus): erste Messung des Spikes, nicht die letzte.
- **Token-Lebensdauer und Refresh-Verhalten gegen OpenProject** ungemessen.
- **Ob openDesk EE tatsächlich einen OpenProject-Enterprise-Token ausliefert**: nur die Helm-Bedingung ist belegt, nicht die Praxis. Frage 1 für den ISV-Call.
- **`manual_install`-Deploy-Daemon auf Kubernetes** ungemessen, insbesondere ob `APP_PERSISTENT_STORAGE` und der Heartbeat-Pfad dort tragen.
- **ZenDiS-Aufnahmeprozess für neue Komponenten** öffentlich nicht dokumentiert: Frage für den ISV-Call, kein Rechercheversäumnis.
- **BSI-Mindeststandard-Version und die Paragrafenangabe (Paragraf 8 BSIG)** sind MEDIUM-Konfidenz und sollten vor kundenseitiger Verwendung nicht ungeprüft übernommen werden.

## Sources

### Primär (HIGH)
- `community.openproject.org`: live gemessen 2026-08-28: `.well-known/oauth-authorization-server`, `.well-known/oauth-protected-resource`, `/mcp`-401, `/api/v3/work_packages` HAL-Größen vor/nach `select`
- `opf/openproject` Quellcode und Doku (Context7 `/websites/openproject`): API-Flächen, Filter-Syntax, Berechtigungskonzept, OAuth-Anwendungen, Release Notes 16.0.0/17.2.0/17.8.0
- `nextcloud/integration_openproject` Quellcode (`appinfo/routes.php`, `OpenProjectAPIController.php`, `OpenProjectAPIService.php`): der Proxy-Weg, serverseitige Token-Erneuerung
- `nextcloud/user_oidc` Quellcode (`TokenService.php`): Beleg für die Bruchstelle im OIDC-Modus
- `bmi/opendesk/deployment/opendesk` auf gitlab.opencode.de, Tag v1.18.0: Komponentenstände, Helm-Werte, Enterprise-Bedingung
- Eigene Codebasis: `server/__init__.py`, `deps.py`, `oauth/store.py`, `exapp/purge.py`, `exapp/occ.py`, `config.py`, `docs/privacy.md`, `PROJECT.md`
- MCP-SDK 2.x installiertes Paket (`mcp/server/context.py`, `mcpserver/server.py`): Middleware-Naht, "Provisional"-Hinweis
- PyPI-JSON-API 2026-08-28: Abhängigkeitslage aller OpenProject-Python-Clients

### Sekundär (MEDIUM)
- BSI IT-Grundschutz OPS.1.1.5 und BSI-Mindeststandard Protokollierung: Anforderungsebene, Versionsstand nicht abschließend bestätigt
- DSK-Orientierungshilfe "Protokollierung": Zweckbindung, Mitbestimmung
- `docs.opendesk.eu/operations/architecture`, `releases.opendesk.eu`: Betriebsdetails ohne eigene Instanz
- Microsoft Purview / Anthropic Compliance API als Vergleichsmaßstab für Audit-Log-Feldsätze

### Tertiär (LOW, zu validieren)
- Nutzerpriorisierung innerhalb OpenProject (Ableitung aus Wettbewerbs-Toolschnitten, keine eigenen Store-Rückmeldungen)
- ZenDiS-Aufnahmeverfahren (öffentlich nicht auffindbar)

---
*Recherche abgeschlossen: 2026-08-28*
*Bereit für Roadmap: ja, mit der ausdrücklichen Maßgabe, dass Phase 1 der Roadmap eine reine Entscheidungsphase ist und dass die OpenProject-Architekturfrage (Weg 0 vs. Weg 1) im Spike gemessen, nicht vorab festgelegt wird.*
